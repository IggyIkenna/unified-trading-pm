#!/usr/bin/env python3
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

import json
import logging
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


def resolve_status(prev_status: str, new_status: str, branch: str) -> str:
    """The no-downgrade compare-and-set DECISION (pure — the heart of Layer 2).

    Returns the status that SHOULD be persisted given the previously-stored status, the incoming
    status, and the branch that produced it. Identical semantics to the manifest writer:

      * ``FAILING`` is ALWAYS persisted (a real regression must surface, even over MAIN_GREEN);
      * a ``main``-branch signal is authoritative (it is the on-main truth — never downgraded);
      * otherwise keep the previously-stored status if the incoming rank is LOWER (no-downgrade:
        a re-run of staging/ldr v2 on an already-promoted repo must not flap MAIN_GREEN→STAGING_GREEN
        and deadlock the dep-order promote gate);
      * an equal-or-higher rank advances.
    """
    if new_status == "FAILING":
        return new_status
    if branch == "main":
        return new_status
    if rank(new_status) < rank(prev_status):
        return prev_status
    return new_status


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

    def transaction(self) -> _TxnProto: ...


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
    project_id: str | None = None,
    firestore_module_factory: FirestoreModuleFactory = _default_firestore_module,
) -> tuple[str, str]:
    """CAS-write ``ci_status/{repo}`` in a Firestore transaction (Layer 2 ordering).

    The transaction makes the read→resolve→write atomic PER DOCUMENT, so two rapid transitions of
    the SAME repo serialize correctly (Firestore retries on contention); different repos never
    contend (Layer 1). Returns ``(prev_status, written_status)``.
    """
    fs = firestore_module_factory()
    client = fs.Client(project=project_id)
    doc_ref = client.collection(COLLECTION).document(repo)
    outcome: dict[str, str] = {}

    @fs.transactional
    def _apply(txn: _TxnProto) -> object:
        snap = doc_ref.get(transaction=txn)
        prev = "NONE"
        if snap.exists:
            prev = str((snap.to_dict() or {}).get("status", "NONE"))
        written = resolve_status(prev, status, branch)
        txn.set(
            doc_ref,
            {
                "status": written,
                "rank": rank(written),
                "branch": branch,
                "sha": sha,
                "updated_at": fs.SERVER_TIMESTAMP,
            },
        )
        outcome["prev"] = prev
        outcome["written"] = written
        return None

    _apply(client.transaction())
    return outcome.get("prev", "NONE"), outcome.get("written", status)


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
    except Exception as err:
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

    # WRITE mode (legacy 4-positional, the GHA dual-write): ci_status_store.py <repo> <status> <branch> <sha>
    # (an explicit `set` verb is also accepted).
    if _args and _args[0] == "set":
        _args = _args[1:]
    if len(_args) != 4:
        print(
            "usage: ci_status_store.py <repo> <status> <branch> <sha>\n"
            "       ci_status_store.py get-map [--manifest PATH] [--project-id ID]",
            file=sys.stderr,
        )
        raise SystemExit(2)
    _repo, _status, _branch, _sha = _args
    _prev, _written = set_status(_repo, _status, _branch, _sha)
    print(f"ci_status/{_repo}: {_prev} -> {_written}")
