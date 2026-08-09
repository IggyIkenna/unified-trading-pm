#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""CI-status side store — Firestore, one document per repo (Phase 1 writer + CAS).

SSOT design: plans/active/ci_status_firestore_side_store_2026_06_10.md.

Today ``ci_status`` lives in ``workspace-manifest.json`` (one ``[skip ci]`` commit per repo per
CI transition — the dominant PM-LDR commit-noise class) AND all 25 repos write the SAME file in
the SAME repo → a git-ref write-contention race. This module is the side store:

  * **Layer 1 — cross-repo races eliminated by partitioning, not locking.** One Firestore document
    per repo (``ci_status/{repo}``); two repos updating concurrently touch DISJOINT documents, so
    there is no contention by construction (the per-VM-shard principle).
  * **Layer 2 — same-repo ordering** via a Firestore-transaction compare-and-set on the lifecycle
    RANK: highest-rank / newest wins, with ``FAILING`` written unconditionally. This preserves the
    existing no-downgrade semantics from ``.github/workflows/ci-status-update.yml`` (a green staging
    re-run cannot knock an on-main repo down from ``MAIN_GREEN``; a real failure always surfaces;
    a ``main``-branch update is authoritative).

Phase 1 is DUAL-WRITE: ``ci-status-update.yml`` keeps the git commit AND calls ``set_status`` here,
so Firestore can be validated against the manifest before any reader is cut over (Phase 2).

The cloud SDK is imported lazily inside the default factory (mirrors
``unified_trading_library.firestore_lifecycle``) so importing this module — for the pure
``resolve_status`` logic or in a unit test with an injected fake — never requires the SDK.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from collections.abc import Callable
from typing import Protocol, cast

# ── Lifecycle ranks — MUST match ci-status-update.yml `_GREEN_RANK` (the SSOT semantics) ──────────
# FAILING is rank 0 here but is handled by the unconditional carve-out in resolve_status, never by
# rank comparison (a regression must always surface, even from a higher-ranked green).
_GREEN_RANK: dict[str, int] = {
    "FAILING": 0,
    "LOCAL_PASS": 1,
    "FEATURE_GREEN": 1,
    # PENDING == GREEN here is deliberate: this rank governs ONLY the no-downgrade store logic
    # (both mean "reached the staging tier", so a stale lower write can't flap the repo back).
    # Promotion READINESS is a separate judgement — tier_c_promotion_gate.ON_STAGING_STATUSES
    # EXCLUDES STAGING_PENDING (a dep must be actually green to promote dependents on). Keep distinct.
    "STAGING_PENDING": 2,
    "STAGING_GREEN": 2,
    "SIT_VALIDATED": 3,
    "MAIN_GREEN": 4,
}

COLLECTION: str = "ci_status"
"""Canonical Firestore collection name — consumers import this, never hardcode the string."""


def rank(status: str) -> int:
    """Lifecycle rank of a status (unknown → 0)."""
    return _GREEN_RANK.get(status, 0)


def resolve_status(
    prev_status: str,
    new_status: str,
    branch: str,
    prev_branch: str = "",
    prev_sha: str = "",
    new_sha: str = "",
) -> str:
    """The no-downgrade compare-and-set DECISION (pure — the heart of Layer 2).

    Returns the status that SHOULD be persisted given the previously-stored status, the incoming
    status, and the branch that produced it. Identical semantics to the manifest writer:

      * ``FAILING`` is persisted (a real regression must surface, even over a green) — EXCEPT a
        non-``main`` FAILING may not clobber ``MAIN_GREEN`` (see below);
      * a same-commit ``SIT_VALIDATED`` may not clear a STORED ``FAILING`` for the IDENTICAL sha
        (see the ``prev_sha``/``new_sha`` guard below — SIT proves cross-repo contracts, not this
        repo's own tests);
      * a STORED ``main``-originated ``FAILING`` may be cleared ONLY by another ``main`` signal
        (the symmetric half of the carve-out above — see the ``prev_branch`` guard);
      * a ``main``-branch signal is authoritative (it is the on-main truth — never downgraded);
      * otherwise keep the previously-stored status if the incoming rank is LOWER (no-downgrade:
        a re-run of staging/ldr v2 on an already-promoted repo must not flap MAIN_GREEN→STAGING_GREEN
        and deadlock the dep-order promote gate);
      * an equal-or-higher rank advances.

    Args:
        prev_branch: the branch recorded on the STORED doc (``doc["branch"]``). Defaults to ``""``
            (unknown provenance) so the main-red guard fails OPEN — a doc written before this field
            was consulted keeps the pre-existing rank behaviour rather than jamming on an
            unattributable red.
        prev_sha: the sha recorded on the STORED doc (``doc["sha"]``). Defaults to ``""`` (unknown)
            so the same-commit SIT guard fails OPEN — a doc written before this field was consulted,
            or a caller that doesn't pass it, keeps the pre-existing rank behaviour.
        new_sha: the sha of the commit that produced ``new_status``. Defaults to ``""`` (unknown),
            same fail-open rationale as ``prev_sha``.
    """
    if new_status == "FAILING":
        # A non-main red must NOT clobber the on-main truth. This carve-out used to be branch-
        # agnostic, which made it a ONE-WAY RATCHET: a red from ANY branch could demote
        # MAIN_GREEN, but the recovery could never climb back — an LDR/promote green maps to
        # FEATURE_GREEN (rank 1) and the no-downgrade rule below correctly refuses it over
        # MAIN_GREEN (rank 4), so ONLY a fresh push to main could restore it. Measured
        # 2026-07-16: a 3.3% wall-clock flake on deployment-api's live-defi-rollout drove
        # MAIN_GREEN → FAILING → SIT_VALIDATED and paged "CI REGRESSION ... (was MAIN_GREEN)"
        # while main itself was never tested and was never red.
        #
        # MAIN_GREEN is not cosmetic: it is the dep-on-main promotion gate (staging-to-main
        # STAGE 1.8), so a non-main flake could stall dependents until an unrelated main push.
        # A non-main red is NOT lost — the QG slice failure pages directly (notify-qg-fail) and
        # LDR redness has its own dedicated axis (ldr_ci_status / ldr_ci_monitor.py). This axis
        # is the PROMOTION tier's truth, and only main can speak for main.
        if branch != "main" and prev_status == "MAIN_GREEN":
            return prev_status
        return new_status
    # SAME-COMMIT GUARD (2026-08-07): SIT_VALIDATED proves only cross-repo API-surface contracts
    # (full-workspace-sit.yml's own header disclaims it as proof of this repo's own tests) — it
    # must not silently clear a FAILING recorded for the IDENTICAL commit (this repo's own
    # quality-gates-v2 is still known-red for that sha). Measured 2026-08-07:
    # batch-live-reconciliation-service@9beb2f73 failed quality-gates-v2 at 06:25Z and 07:31Z;
    # full-workspace-sit's stamp step restamped SIT_VALIDATED for the SAME sha at 07:43Z, and the
    # rank-only store advanced FAILING -> SIT_VALIDATED, producing a misleading "SIT PASSED"
    # recovery message while the repo's own QG was still red. Scoped to the exact same commit only
    # -- a SIT stamp for a NEWER (already-fixed) sha is unaffected and still advances normally.
    if new_status == "SIT_VALIDATED" and prev_status == "FAILING" and new_sha and prev_sha and new_sha == prev_sha:
        return prev_status
    # The SYMMETRIC half of the carve-out above (2026-07-20). The block above stops a non-main red
    # from clobbering the on-main truth; this stops a non-main GREEN from clearing a main-originated
    # red. Without it, FAILING is rank 0 on the STORED side and therefore erasable by ANY higher-
    # ranked write — which is exactly the ratchet the header comment claims cannot happen.
    #
    # Measured 2026-07-20: UAC@a2beed46 removed `massive` from SOURCE_PRIORITY and broke 10 UTL
    # manifest-writer tests. UTL main went FAILING (branch=main) at 03:28Z. At 05:21Z the
    # full-workspace SIT stamped SIT_VALIDATED (rank 3, branch=live-defi-rollout) → rank comparison
    # erased main's red, ci-status-update posted an affirmative "SIT PASSED … clear to promote"
    # all-clear, and the promote gate (which treats SIT_VALIDATED as on-main-eligible) re-opened
    # promotion INTO a red main. Note the 2026-07-16 comment above describes this same
    # MAIN_GREEN → FAILING → SIT_VALIDATED shape; only the FIRST hop was fixed then.
    #
    # SIT's guarantee is content-scoped to the LDR tree (`sit_validated_tree`), so it cannot speak
    # for main's tree at all — only main can speak for main, in BOTH directions.
    if prev_status == "FAILING" and prev_branch == "main" and branch != "main":
        return prev_status
    if branch == "main":
        return new_status
    if rank(new_status) < rank(prev_status):
        return prev_status
    return new_status


def is_stale_write(prev_dict: dict[str, object], new_status: str, branch: str, new_commit_ts: str | None) -> bool:
    """True when this write is a STALE non-FAILING signal that must NOT override the stored doc.

    The race (WS-A Finding from the implementation discussion): a late-arriving GREEN for an
    OLDER commit can otherwise clear a fresher status — ``resolve_status`` is rank-based, so
    ``resolve_status("FAILING", "FEATURE_GREEN", ...)`` advances to green even when the green
    tests an older commit than the one that failed. The git ``ci-status-reconciler`` used to
    backstop that; the STORE now rejects it directly (the reconciler was retired in WS-A Phase-3).

    Rejection is conservative — it fires ONLY when ALL hold, so it can never mask a real
    regression or a legacy (no-timestamp) caller:

      * the incoming status is NOT ``FAILING`` (a regression must always surface);
      * the branch is NOT ``main`` (an on-main signal is always authoritative);
      * the incoming carries a ``commit_ts`` AND the stored doc has one (both known);
      * the incoming commit is STRICTLY OLDER than the stored one (ISO-8601 sorts as a string).

    A write with no ``commit_ts`` (the legacy 4-arg call, before the dispatcher passes it) is
    NEVER treated as stale → behaviour is identical to today until the timestamp is wired in.
    """
    if new_status == "FAILING" or branch == "main" or not new_commit_ts:
        return False
    prev_ts = prev_dict.get("commit_ts")
    if not isinstance(prev_ts, str) or not prev_ts:
        return False
    return new_commit_ts < prev_ts


# ── Firestore client resolution — lazy + injectable (mirrors UTL firestore_lifecycle) ────────────
# Structural protocols for the slice of ``google.cloud.firestore`` we use. The untyped SDK is
# bridged exactly ONCE (the cast in _default_firestore_module); everything downstream is typed.


class _SnapProto(Protocol):
    exists: bool

    def to_dict(self) -> dict[str, object] | None: ...


class _DocRefProto(Protocol):
    id: str

    def get(self, transaction: object | None = ...) -> _SnapProto: ...

    def to_dict(self) -> dict[str, object] | None: ...


class _CollectionProto(Protocol):
    def document(self, document_id: str) -> _DocRefProto: ...

    def stream(self) -> list[_DocRefProto]: ...


class _TxnProto(Protocol):
    def set(self, reference: _DocRefProto, document_data: dict[str, object]) -> object: ...


class _ClientProto(Protocol):
    def collection(self, collection_path: str) -> _CollectionProto: ...

    def transaction(self, max_attempts: int = ...) -> _TxnProto: ...


class _FirestoreModuleProto(Protocol):
    """The slice of ``google.cloud.firestore`` we use (Client, SERVER_TIMESTAMP, transactional)."""

    SERVER_TIMESTAMP: object

    def Client(self, project: str | None = ...) -> _ClientProto:  # noqa: N802 — mirrors the SDK API
        ...

    def transactional(self, fn: Callable[[_TxnProto], object]) -> Callable[[_TxnProto], object]: ...


FirestoreModuleFactory = Callable[[], _FirestoreModuleProto]
"""Returns the firestore MODULE (not just a client) — we need SERVER_TIMESTAMP + transactional too.
Production uses :func:`_default_firestore_module`; tests inject a fake module."""


def _default_firestore_module() -> _FirestoreModuleProto:
    """Lazily import ``google.cloud.firestore``. Lazy so importing this module for ``resolve_status``
    or a fake-injected test never needs the SDK installed (same rationale as UTL firestore_lifecycle).
    """
    # Deliberate lazy in-function import (docstring above) — sanctioned markers for both QG checks
    # live on the `from` line (the line both the rg and the AST checker match):
    from google.cloud import (  # noqa: imports-inside-functions # noqa: cloud-sdk-direct
        firestore,  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue, reportUnknownVariableType]
    )

    return cast(_FirestoreModuleProto, cast(object, firestore))


def set_status(
    repo: str,
    status: str,
    branch: str,
    sha: str,
    *,
    codebase_health: dict[str, object] | None = None,
    commit_ts: str | None = None,
    sit_validated_tree: str | None = None,
    sit_validated_workspace_digest: str | None = None,
    project_id: str | None = None,
    max_attempts: int = 10,
    firestore_module_factory: FirestoreModuleFactory = _default_firestore_module,
) -> tuple[str, str]:
    """CAS-write ``ci_status/{repo}`` in a Firestore transaction (Layer 2 ordering).

    The transaction makes the read→resolve→write atomic PER DOCUMENT, so two rapid transitions of
    the SAME repo serialize correctly (Firestore retries on contention); different repos never
    contend (Layer 1). Returns ``(prev_status, written_status)``.

    ``codebase_health`` (coverage_pct / qg_red_reason / large_file_count / warn_file_count) is the
    per-repo QG-metric blob the deployment-ui Repo-CI table reads (Cov% / QG-reason / File-debt).
    ``txn.set`` REPLACES the whole document, so when a status-only update arrives (codebase_health
    is None) we carry the EXISTING blob forward — a ci_status transition must never wipe the
    last-known metrics. Pass a fresh dict to overwrite it.

    ``commit_ts`` (ISO-8601 committer date of ``sha``) drives the stale-write guard
    (:func:`is_stale_write`): a non-FAILING write for an OLDER commit than the stored one is
    rejected as a no-op, so a late green can't clear a fresh fail. Defaults to ``None`` (no guard
    — identical to today) until the dispatcher passes it. It is merge-preserved like
    codebase_health so a status-only write never wipes the stored commit ordering key.

    ``sit_validated_workspace_digest`` (HIGH-combo, cicd_sit_full_coverage_handoff_2026_06_27.md
    Phase 2): the SHA-256 workspace digest (see ``workspace_digest.compute_workspace_digest``) of
    ALL ldr_main repos' LDR tree SHAs at the time SIT ran. Stored alongside ``sit_validated_tree``
    so the promote gate can detect when a DEPENDENCY changed after SIT validated a dependent —
    ``sit_validated_tree == LDR_tree`` proves the dependent's own content is unchanged, but only
    ``sit_validated_workspace_digest == current_workspace_digest`` proves the cross-repo COMBINATION
    is still the one SIT actually validated. Same carry-forward and stale-write semantics as tree.

    ``max_attempts`` is the Firestore transaction's Aborted-retry budget (Layer-2 contention);
    the call is ADDITIONALLY retried a few times on transient ``DeadlineExceeded`` /
    ``ServiceUnavailable`` (which the transactional decorator does not retry).
    """
    fs = firestore_module_factory()
    client = fs.Client(project=project_id)
    doc_ref = client.collection(COLLECTION).document(repo)
    outcome: dict[str, str] = {}

    @fs.transactional
    def _apply(txn: _TxnProto) -> object:
        snap = doc_ref.get(transaction=txn)
        prev_dict = (snap.to_dict() or {}) if snap.exists else {}
        prev = str(prev_dict.get("status", "NONE"))
        # Stale-write guard (WS-A): a late green for an older commit must not clear a fresher
        # status. Skip the status/rank txn.set → the stored doc's status is unchanged.
        if is_stale_write(prev_dict, status, branch, commit_ts):
            # EXCEPTION (WS-L, adversarial-verified 2026-06-27): a SIT_VALIDATED write carries a
            # content-addressed `sit_validated_tree` fingerprint that is SELF-guarding — the promote gate
            # requires it to equal the CURRENT LDR tree, so a stale tree can never validate a different
            # current tree. So a fresh SIT validation must STILL record its tree here, else a 2nd breaking
            # change whose LDR commit's committer-date predates the prior promote's main-merge ts would be
            # stale-rejected wholesale → the fingerprint never updates → permanent promote jam (same jam
            # CLASS as the no-downgrade rank bug). Advance ONLY the fingerprint; leave status / rank /
            # commit_ts untouched so the stale-ordering key does not regress for other writers.
            if (
                status == "SIT_VALIDATED"
                and prev_dict
                and (sit_validated_tree is not None or sit_validated_workspace_digest is not None)
            ):
                merged: dict[str, object] = dict(prev_dict)
                if sit_validated_tree is not None:
                    merged["sit_validated_tree"] = sit_validated_tree
                if sit_validated_workspace_digest is not None:
                    merged["sit_validated_workspace_digest"] = sit_validated_workspace_digest
                txn.set(doc_ref, merged)
            outcome["prev"] = prev
            outcome["written"] = prev
            return None
        # noqa: qg-empty-fallback — "" is the DELIBERATE unknown-provenance sentinel: a doc written
        # before `branch` was consulted has no attributable origin, and resolve_status's main-red
        # guard requires an explicit "main" to engage, so "" fails OPEN (pre-existing rank
        # behaviour) rather than jamming an unclearable red. Raising here would break every
        # legacy doc; None would just move the same defaulting to the callee.
        prev_branch = str(prev_dict.get("branch", ""))  # noqa: qg-empty-fallback
        prev_sha = str(prev_dict.get("sha", ""))  # noqa: qg-empty-fallback
        written = resolve_status(prev, status, branch, prev_branch, prev_sha=prev_sha, new_sha=sha)
        doc: dict[str, object] = {
            "status": written,
            "rank": rank(written),
            "branch": branch,
            "sha": sha,
            "updated_at": fs.SERVER_TIMESTAMP,
        }
        # Merge-preserve codebase_health: write the fresh blob when provided, else carry the
        # existing one forward (txn.set is a full-document replace).
        health = codebase_health if codebase_health is not None else prev_dict.get("codebase_health")
        if health is not None:
            doc["codebase_health"] = health
        # Merge-preserve the commit ordering key: stamp the new commit's ts when provided, else
        # carry the stored one forward so a no-ts status update doesn't drop the guard's key.
        ts = commit_ts if commit_ts else prev_dict.get("commit_ts")
        if ts is not None:
            doc["commit_ts"] = ts
        # SIT-validated tree fingerprint (WS-L SIT-rehome) — DECOUPLED from resolve_status's no-downgrade
        # rank (adversarial-verified 2026-06-27). The fact "this LDR tree passed cross-repo SIT" must be
        # recordable EVEN when the resolved status stays a HIGHER rank: a repo already MAIN_GREEN whose
        # NEXT breaking change is re-validated on LDR emits SIT_VALIDATED (rank 3) which resolve_status
        # keeps as MAIN_GREEN (rank 4) — keying the fingerprint off `written == SIT_VALIDATED` would then
        # NEVER store it → that repo's 2nd breaking change could never pass the promote gate (permanent
        # jam). So key off the INCOMING `status`: stamp the dispatched tree when this write IS a
        # SIT_VALIDATED signal; otherwise CARRY FORWARD the stored fingerprint. A carried-forward older
        # tree is harmless — the CONSUMER gates on `sit_validated_tree == the CURRENT LDR tree`, so a
        # lingering older tree can never validate a different current tree (tree equality == content
        # identity, and that content DID pass SIT). is_stale_write still rejects an older-commit SIT
        # write wholesale, so the fingerprint never regresses to an older tree.
        if status == "SIT_VALIDATED" and sit_validated_tree is not None:
            doc["sit_validated_tree"] = sit_validated_tree
        else:
            carried = prev_dict.get("sit_validated_tree")
            if carried is not None:
                doc["sit_validated_tree"] = carried
        # Cross-repo combination fingerprint (HIGH-combo, Phase 2): same carry-forward semantics as
        # sit_validated_tree. The consumer gates on digest equality (sit_validated_workspace_digest ==
        # current_workspace_digest); a legacy doc with no stored digest fails-OPEN (no combination
        # check), so the fingerprint applies progressively once SIT starts emitting it.
        if status == "SIT_VALIDATED" and sit_validated_workspace_digest is not None:
            doc["sit_validated_workspace_digest"] = sit_validated_workspace_digest
        else:
            carried_ws = prev_dict.get("sit_validated_workspace_digest")
            if carried_ws is not None:
                doc["sit_validated_workspace_digest"] = carried_ws
        txn.set(doc_ref, doc)
        outcome["prev"] = prev
        outcome["written"] = written
        return None

    # The transactional decorator retries Aborted (write contention) up to max_attempts. We ALSO
    # retry the whole call on transient DeadlineExceeded / ServiceUnavailable, which it does not —
    # matched by exception NAME so this module never has to import google.api_core (SDK-free import).
    _transient = {"DeadlineExceeded", "ServiceUnavailable", "RetryError", "_MultiThreadedRendezvous"}
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            _apply(client.transaction(max_attempts=max_attempts))
            return outcome.get("prev", "NONE"), outcome.get("written", status)
        except Exception as err:  # noqa: broad-except — re-raised below unless transient-by-name; matched
            # by exception class NAME (not isinstance) so this module stays google.api_core-import-free
            if type(err).__name__ not in _transient or attempt == 2:
                raise
            last_err = err
            time.sleep(0.5 * (attempt + 1))
    raise last_err if last_err is not None else RuntimeError("set_status: unreachable")


def get_all(
    *,
    project_id: str | None = None,
    firestore_module_factory: FirestoreModuleFactory = _default_firestore_module,
) -> dict[str, dict[str, object]]:
    """Read the whole-fleet ci_status aggregate — a single collection query (Phase 2 readers)."""
    fs = firestore_module_factory()
    client = fs.Client(project=project_id)
    out: dict[str, dict[str, object]] = {}
    for doc in client.collection(COLLECTION).stream():
        out[doc.id] = doc.to_dict() or {}
    return out


def get_doc(
    repo: str,
    *,
    project_id: str | None = None,
    firestore_module_factory: FirestoreModuleFactory = _default_firestore_module,
) -> dict[str, object]:
    """Read ONE repo's full ci_status doc from Firestore (the live SSOT) — or ``{}`` if absent.

    Returns the raw document (``status`` / ``sit_validated_tree`` / ``sha`` / ``commit_ts`` / …). Used by
    the LDR→main fleet promoter's SIT-gate part-2, which must gate a breaking promote on the LIVE status
    + ``sit_validated_tree`` (NOT the hourly manifest cache, which never carries the tree). Reuses
    ``get_all`` so it shares the (tested) Firestore read path + fake-client compatibility; the fleet
    collection is ~two dozen docs, so reading all to pick one is negligible.
    """
    return get_all(project_id=project_id, firestore_module_factory=firestore_module_factory).get(repo, {})


# ── READ side (Phase 2) — Firestore-authoritative per-repo, manifest as the fallback cache ────────


def manifest_ci_status_map(manifest: dict[str, object]) -> dict[str, str]:
    """Map repo-name → ci_status from ``workspace-manifest.json`` (the fallback cache).

    Tolerant of dict-keyed (`{repo: {...}}`) or list (`[{name, ci_status}, ...]`) ``repositories``.
    Repos with no/blank ci_status are omitted (a missing entry means "unset", not a status).
    """
    repos = manifest.get("repositories")
    items: list[tuple[str, object]] = []
    if isinstance(repos, dict):
        items = [(str(k), v) for k, v in cast("dict[str, object]", repos).items()]
    elif isinstance(repos, list):
        for r in cast("list[object]", repos):
            if isinstance(r, dict):
                r_d = cast("dict[str, object]", r)
                name = r_d.get("name")
                if isinstance(name, str) and name:
                    items.append((name, r_d))
    out: dict[str, str] = {}
    for name, value in items:
        if isinstance(value, dict):
            status = cast("dict[str, object]", value).get("ci_status")
            if isinstance(status, str) and status:
                out[name] = status
    return out


def resolve_ci_status_map(
    manifest: dict[str, object],
    *,
    project_id: str | None = None,
    firestore_module_factory: FirestoreModuleFactory = _default_firestore_module,
) -> dict[str, str]:
    """Repo → ci_status: **Firestore-authoritative per-repo, manifest as fallback cache**.

    The migration-safe read primitive (Phase 2). Firestore is the live SSOT, but during the
    dual-write ramp (or if a repo simply hasn't transitioned yet) a repo may be absent from
    Firestore — so we start from the manifest map and OVERLAY Firestore per-repo where present. This
    means a reader behaves identically to today while the dual-write flag is still off (Firestore
    empty → pure manifest), and shifts to Firestore-truth repo-by-repo as docs appear — never a
    flag-day, never a repo blanked by a partial Firestore.

    On any Firestore unavailability (SDK absent before cutover, transient API error) we **degrade
    LOUDLY to the manifest cache** (a warning, not a silent swallow) — the manifest is the designed
    offline fallback for exactly this, so a degrade is correct, not a failure to mask.
    """
    base = manifest_ci_status_map(manifest)
    try:
        fs = get_all(project_id=project_id, firestore_module_factory=firestore_module_factory)
    except Exception as err:  # noqa: broad-except — any Firestore unavailability (SDK absent
        # pre-cutover, transient API error) must degrade to the manifest fallback, never crash
        logging.getLogger(__name__).warning(
            "ci_status Firestore read unavailable (%s: %s) — using manifest fallback cache",
            type(err).__name__,
            err,
        )
        return base
    for repo, doc in fs.items():
        status = doc.get("status")
        if isinstance(status, str) and status:
            base[repo] = status
    return base


def _load_manifest(path: str) -> dict[str, object]:
    with open(path, encoding="utf-8") as fh:
        loaded = cast("object", json.load(fh))
    return cast("dict[str, object]", loaded) if isinstance(loaded, dict) else {}


if __name__ == "__main__":
    import sys

    _args = sys.argv[1:]
    # READ mode: `ci_status_store.py get-map [--manifest PATH] [--project-id ID]` → JSON {repo: status}
    # for shell / GHA readers (Firestore-first, manifest fallback).
    if _args and _args[0] == "get-map":
        import argparse

        _p = argparse.ArgumentParser(prog="ci_status_store.py get-map")
        _p.add_argument("--manifest", default="workspace-manifest.json")
        _p.add_argument("--project-id", default=None)
        _ns = _p.parse_args(_args[1:])
        _manifest_path = cast("str", _ns.manifest)
        _proj = cast("str | None", _ns.project_id)
        _map = resolve_ci_status_map(_load_manifest(_manifest_path), project_id=_proj)
        print(json.dumps(_map, sort_keys=True))
        raise SystemExit(0)

    # READ mode: `ci_status_store.py get-doc --repo R [--project-id ID]` → the repo's full Firestore
    # doc as JSON (status + sit_validated_tree + sha + …) for the LDR→main fleet promoter's SIT-gate.
    # Degrades LOUDLY to `{}` (empty doc) on Firestore unavailability — the consumer fail-CLOSES on an
    # empty doc, which for an ldr_main breaking change means BLOCK (never promote unvalidated content).
    if _args and _args[0] == "get-doc":
        import argparse

        _p = argparse.ArgumentParser(prog="ci_status_store.py get-doc")
        _p.add_argument("--repo", required=True)
        _p.add_argument("--project-id", default=None)
        _ns = _p.parse_args(_args[1:])
        _repo = cast("str", _ns.repo)
        _proj = cast("str | None", _ns.project_id)
        try:
            _doc = get_doc(_repo, project_id=_proj)
        except Exception as _err:  # noqa: broad-except — Firestore unavailability degrades to an
            # empty doc (the fail-CLOSED signal for the ldr_main SIT-gate), never crashes the CLI
            logging.getLogger(__name__).warning(
                "ci_status get-doc Firestore unavailable (%s: %s) — emitting empty doc",
                type(_err).__name__,
                _err,
            )
            _doc = {}
        print(json.dumps(_doc, sort_keys=True, default=str))
        raise SystemExit(0)

    # WRITE mode (legacy 4-positional, the GHA dual-write): ci_status_store.py <repo> <status> <branch> <sha>
    # (an explicit `set` verb is also accepted).
    if _args and _args[0] == "set":
        _args = _args[1:]
    # Optional --codebase-health-b64 <base64-json>: the per-repo QG metrics blob
    # (coverage_pct / qg_red_reason / large_file_count / warn_file_count) that the CI agg job
    # forwards. Extracted before the 4 positional args so the legacy call signature is unchanged.
    _health: dict[str, object] | None = None
    if "--codebase-health-b64" in _args:
        _i = _args.index("--codebase-health-b64")
        _b64 = _args[_i + 1] if _i + 1 < len(_args) else ""
        _args = _args[:_i] + _args[_i + 2 :]
        if _b64:
            try:
                _decoded = cast("object", json.loads(base64.b64decode(_b64).decode("utf-8")))
                _health = cast("dict[str, object]", _decoded) if isinstance(_decoded, dict) else None
            except ValueError:
                print("warning: --codebase-health-b64 not valid base64-JSON; ignoring", file=sys.stderr)
    # Optional --commit-ts <iso8601>: the committer date of <sha>, the stale-write ordering key.
    # Extracted (like the health blob) so the legacy 4-positional signature is unchanged.
    _commit_ts: str | None = None
    if "--commit-ts" in _args:
        _j = _args.index("--commit-ts")
        _commit_ts = _args[_j + 1] if _j + 1 < len(_args) else None
        _args = _args[:_j] + _args[_j + 2 :]
        if not _commit_ts:
            _commit_ts = None
    # Optional --sit-validated-tree <tree-sha>: the LDR tree SHA the cross-repo SIT validated (WS-L
    # SIT-rehome). Persisted ONLY when status==SIT_VALIDATED; cleared on any other status. Extracted
    # (like --commit-ts) so the legacy 4-positional signature is unchanged.
    _sit_tree: str | None = None
    if "--sit-validated-tree" in _args:
        _k = _args.index("--sit-validated-tree")
        _sit_tree = _args[_k + 1] if _k + 1 < len(_args) else None
        _args = _args[:_k] + _args[_k + 2 :]
        if not _sit_tree:
            _sit_tree = None
    # Optional --sit-validated-workspace-digest <hex>: the workspace combination fingerprint
    # (SHA-256 of all ldr_main repos' LDR tree SHAs) computed by the SIT producer
    # (workspace_digest.compute_workspace_digest). Persisted ONLY when status==SIT_VALIDATED;
    # carry-forward semantics same as --sit-validated-tree. The promote gate uses this to detect
    # when a dependency changed after SIT validated a dependent (HIGH-combo, Phase 2).
    _sit_ws_digest: str | None = None
    if "--sit-validated-workspace-digest" in _args:
        _kw = _args.index("--sit-validated-workspace-digest")
        _sit_ws_digest = _args[_kw + 1] if _kw + 1 < len(_args) else None
        _args = _args[:_kw] + _args[_kw + 2 :]
        if not _sit_ws_digest:
            _sit_ws_digest = None
    # Optional --emit-transition: print ONLY the machine-parseable "<prev>\t<written>" line (the
    # RESOLVED store transition) instead of the human line. ci-status-update.yml (the WS-A Phase-3
    # SSOT writer) captures it to derive the Slack notify gating from prev->written WITHOUT a second
    # Firestore read. Keeps this module GHA-agnostic (the workflow owns the $GITHUB_OUTPUT shape).
    _emit_transition = False
    if "--emit-transition" in _args:
        _args.remove("--emit-transition")
        _emit_transition = True
    if len(_args) != 4:
        print(
            "usage: ci_status_store.py <repo> <status> <branch> <sha> "
            "[--codebase-health-b64 <b64-json>] [--commit-ts <iso8601>] [--emit-transition]\n"
            "       ci_status_store.py get-map [--manifest PATH] [--project-id ID]",
            file=sys.stderr,
        )
        raise SystemExit(2)
    _repo, _status, _branch, _sha = _args
    _prev, _written = set_status(
        _repo,
        _status,
        _branch,
        _sha,
        codebase_health=_health,
        commit_ts=_commit_ts,
        sit_validated_tree=_sit_tree,
        sit_validated_workspace_digest=_sit_ws_digest,
    )
    if _emit_transition:
        print(f"{_prev}\t{_written}")
    else:
        print(f"ci_status/{_repo}: {_prev} -> {_written}")
