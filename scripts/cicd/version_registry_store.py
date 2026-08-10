#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Version-registry side store — Firestore, the release version↔SHA per repo (Phase-2 writer + CAS).

SSOT design: plans/active/cicd_phase2_foundation_2026_06_27.md (item B) + the D13 decision in
plans/active/cicd_consolidated_remaining_2026_06_24.md. Git tags are the version SSOT; Firestore is
the queryable read-mirror; the manifest ``versions{}`` becomes a derived offline-fallback cache.

This module is the EVENT-DRIVEN + CAS upgrade of the best-effort write that
``reconcile_release_tags.py::_write_firestore_release_tags`` has performed since 2026-06-11. Both
converge on the SAME document field ``repo_state/{repo}.release_tag`` so the */30 reconcile cron
(self-healing backstop) and the ``push: tags: v*`` event path (primary, ≤1-min latency) never
diverge. The only additions over the existing best-effort write are ``sha`` + ``commit_ts`` and the
compare-and-set ordering discipline.

It is a faithful sibling of ``ci_status_store.py`` (the proven WS-A 208 pattern), with two
deliberate differences:

  * **Shared document, field-scoped merge.** ``repo_state/{repo}`` is shared with
    ``ci_failure_watcher`` and ``promotion_lag_monitor`` (they write sibling fields). So the CAS
    transaction writes ONLY the ``release_tag`` field with ``merge=True`` — never a whole-document
    replace (that would clobber the siblings). ``ci_status_store`` owns its whole ``ci_status/{repo}``
    document, so it can full-replace; this one must not.
  * **Semver is the rank.** ``ci_status`` orders by a lifecycle rank; the version registry orders by
    the semver tuple itself — the registry is MONOTONIC (never records a lower version over a higher
    one), matching ``reconcile_release_tags``'s existing no-backfill guard. ``commit_ts`` is the
    secondary stale-write guard for same/lower-version re-pushes arriving out of order.

The cloud SDK is imported lazily inside the default factory (mirrors
``unified_trading_library.firestore_lifecycle``) so importing this module — for the pure
``resolve_version`` logic or in a unit test with an injected fake — never requires the SDK.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from collections.abc import Callable
from typing import Protocol, cast

COLLECTION: str = "repo_state"
"""Canonical Firestore collection — SHARED with ci_failure_watcher / promotion_lag_monitor.
Consumers import this, never hardcode the string."""

RELEASE_TAG_FIELD: str = "release_tag"
"""The field within ``repo_state/{repo}`` this store owns (a nested map: version/tag/sha/commit_ts)."""

# Plain 3-part semver ONLY (no dev/pre-release/local suffix) — matches reconcile_release_tags._VERSION_RE
# and the Phase-2 publish-only-plain-3-part guard. A non-matching version is treated as unset (0,0,0).
_PLAIN_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def semver_tuple(version: str) -> tuple[int, int, int]:
    """Parse a plain ``X.Y.Z`` into a sortable tuple. Non-plain/empty → ``(0, 0, 0)`` (treated unset)."""
    m = _PLAIN_SEMVER_RE.match(version.strip()) if version else None
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def is_plain_semver(version: str) -> bool:
    """True iff ``version`` is a plain 3-part ``X.Y.Z`` (the only shape the registry accepts)."""
    return bool(_PLAIN_SEMVER_RE.match(version.strip())) if version else False


def resolve_version(prev_version: str, new_version: str) -> str:
    """The no-downgrade compare-and-set DECISION (pure — the heart of the monotonic registry).

    Returns the version that SHOULD be persisted given the previously-stored version and the
    incoming one. The registry is MONOTONIC by semver: a strictly-higher incoming version advances
    it; an equal-or-lower one keeps the stored value (a release is never "un-released"; matches
    ``reconcile_release_tags``'s no-backfill guard). An empty/unset previous always advances.
    """
    if semver_tuple(new_version) > semver_tuple(prev_version):
        return new_version
    return prev_version if prev_version else new_version


def is_stale_write(prev_dict: dict[str, object], new_version: str) -> bool:
    """True when this write must NOT change the stored ``release_tag`` (a no-op CAS).

    The registry is monotonic by semver, so a write is stale iff it does not ADVANCE the stored
    version:

      * a strictly-higher incoming version is NEVER stale (it advances the registry);
      * a first write (no stored version) is NEVER stale (it seeds the registry);
      * an equal-or-lower incoming version over an existing one IS stale — a duplicate/late re-push
        or a backfill, which must not churn the stored sha/commit_ts/updated_at.

    Ordering is decided purely by semver (the version is the rank); ``commit_ts`` is recorded for
    observability but is not part of this decision.
    """
    prev_version = str(prev_dict.get("version") or "") if prev_dict else ""
    # A strictly-higher incoming version always advances — never stale.
    if semver_tuple(new_version) > semver_tuple(prev_version):
        return False
    # No advance possible. A first write (no stored version) seeds the registry; otherwise it's a
    # non-advancing re-push → stale (no-op), keeping the registry monotonic.
    return bool(prev_version)


# ── Firestore client resolution — lazy + injectable (mirrors ci_status_store / UTL firestore_lifecycle) ──
# Structural protocols for the slice of ``google.cloud.firestore`` we use. The untyped SDK is bridged
# exactly ONCE (the cast in _default_firestore_module); everything downstream is typed.


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
    def set(self, reference: _DocRefProto, document_data: dict[str, object], merge: bool = ...) -> object: ...


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


def _default_firestore_module() -> _FirestoreModuleProto:  # pragma: no cover — lazy SDK import (integration surface)
    """Lazily import ``google.cloud.firestore``. Lazy so importing this module for ``resolve_version``
    or a fake-injected test never needs the SDK installed (same rationale as ci_status_store).
    """
    # Deliberate lazy in-function import (docstring above) — sanctioned markers for ALL three QG
    # checks live on the `from` line: TID251 (ruff banned-import ratchet) + the two rg/AST markers
    # (imports-inside-functions, cloud-sdk-direct). Mirrors reconcile_release_tags.py's green pattern.
    from google.cloud import (  # noqa: TID251, RUF100  # noqa: imports-inside-functions  # noqa: cloud-sdk-direct
        firestore,  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue, reportUnknownVariableType]
    )

    return cast(_FirestoreModuleProto, cast(object, firestore))


def set_release_version(
    repo: str,
    version: str,
    sha: str,
    *,
    commit_ts: str | None = None,
    project_id: str | None = None,
    max_attempts: int = 10,
    firestore_module_factory: FirestoreModuleFactory = _default_firestore_module,
) -> tuple[str, str]:
    """CAS-write ``repo_state/{repo}.release_tag`` in a Firestore transaction (monotonic ordering).

    The transaction makes the read→resolve→write atomic PER DOCUMENT, so two rapid tag pushes for
    the SAME repo serialize correctly (Firestore retries on contention); different repos never
    contend (disjoint documents). Returns ``(prev_version, written_version)``.

    Writes ONLY the ``release_tag`` field with ``merge=True`` so the sibling ``repo_state/{repo}``
    fields owned by ci_failure_watcher / promotion_lag_monitor are preserved. The stored map is
    ``{version, tag: "v"+version, sha, commit_ts, updated_at}``.

    ``version`` MUST be a plain 3-part ``X.Y.Z`` (the publish-only-plain-3-part guard) — a
    non-plain version raises, so a ``.devN``/``+local`` string can never poison the registry.

    ``commit_ts`` (ISO-8601 committer date of ``sha``) is recorded for observability/ordering; the
    registry's monotonicity is decided by semver (:func:`resolve_version` / :func:`is_stale_write`).

    ``max_attempts`` is the Firestore transaction's Aborted-retry budget (contention); the call is
    ADDITIONALLY retried a few times on transient ``DeadlineExceeded`` / ``ServiceUnavailable``.
    """
    if not is_plain_semver(version):
        raise ValueError(f"version_registry: refusing to record non-plain-3-part version {version!r} for {repo!r}")

    fs = firestore_module_factory()
    client = fs.Client(project=project_id)
    doc_ref = client.collection(COLLECTION).document(repo)
    outcome: dict[str, str] = {}

    @fs.transactional
    def _apply(txn: _TxnProto) -> object:
        snap = doc_ref.get(transaction=txn)
        full = (snap.to_dict() or {}) if snap.exists else {}
        prev_rt_obj = full.get(RELEASE_TAG_FIELD)
        prev_rt = cast("dict[str, object]", prev_rt_obj) if isinstance(prev_rt_obj, dict) else {}
        prev = str(prev_rt.get("version") or "")
        # Stale-write guard: a non-advancing (equal/lower) re-push is a no-op → leave the stored
        # release_tag untouched so the registry stays monotonic and updated_at doesn't churn.
        if is_stale_write(prev_rt, version):
            outcome["prev"] = prev or "NONE"
            outcome["written"] = prev or "NONE"
            return None
        written = resolve_version(prev, version)
        release_tag: dict[str, object] = {
            "version": written,
            "tag": f"v{written}",
            "sha": sha,
            "updated_at": fs.SERVER_TIMESTAMP,
        }
        # Stamp the new commit's ts when provided, else carry the stored one forward so a no-ts
        # write doesn't drop the ordering key.
        ts = commit_ts if commit_ts else prev_rt.get("commit_ts")
        if ts is not None:
            release_tag["commit_ts"] = ts
        # FIELD-SCOPED merge: only release_tag is written; sibling repo_state fields are preserved.
        txn.set(doc_ref, {RELEASE_TAG_FIELD: release_tag}, merge=True)
        outcome["prev"] = prev or "NONE"
        outcome["written"] = written
        return None

    _transient = {"DeadlineExceeded", "ServiceUnavailable", "RetryError", "_MultiThreadedRendezvous"}
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            _apply(client.transaction(max_attempts=max_attempts))
            return outcome.get("prev", "NONE"), outcome.get("written", version)
        except Exception as err:  # noqa: broad-except  # pragma: no cover — transient-retry path
            # (needs a flaky real Firestore); matched by exception class NAME, SDK-free import
            if type(err).__name__ not in _transient or attempt == 2:
                raise
            last_err = err
            time.sleep(0.5 * (attempt + 1))
    raise last_err if last_err is not None else RuntimeError("set_release_version: unreachable")  # pragma: no cover


def get_all(
    *,
    project_id: str | None = None,
    firestore_module_factory: FirestoreModuleFactory = _default_firestore_module,
) -> dict[str, dict[str, object]]:
    """Read the whole-fleet ``release_tag`` aggregate — one collection query (Phase-2 readers).

    Returns ``{repo: release_tag_map}`` for every ``repo_state`` doc that carries a ``release_tag``
    field (docs with only ci_failure/promotion_lag are omitted).
    """
    fs = firestore_module_factory()
    client = fs.Client(project=project_id)
    out: dict[str, dict[str, object]] = {}
    for doc in client.collection(COLLECTION).stream():
        full = doc.to_dict() or {}
        rt = full.get(RELEASE_TAG_FIELD)
        if isinstance(rt, dict):
            out[doc.id] = cast("dict[str, object]", rt)
    return out


# ── READ side (Phase-2) — Firestore-authoritative per-repo, manifest as the fallback cache ────────


def manifest_version_map(manifest: dict[str, object]) -> dict[str, str]:
    """Map repo-name → released version from ``workspace-manifest.json`` top-level ``versions{}``.

    The manifest is the offline-fallback cache (the hourly consolidator projects Firestore into it).
    Repos with no/blank version are omitted.
    """
    versions = manifest.get("versions")
    out: dict[str, str] = {}
    if isinstance(versions, dict):
        for k, v in cast("dict[str, object]", versions).items():
            if isinstance(v, str) and v:
                out[str(k)] = v
    return out


def resolve_version_map(
    manifest: dict[str, object],
    *,
    project_id: str | None = None,
    firestore_module_factory: FirestoreModuleFactory = _default_firestore_module,
) -> dict[str, str]:
    """Repo → released version: **Firestore-authoritative per-repo, manifest as fallback cache**.

    The migration-safe read primitive (Phase-2). Starts from the manifest ``versions{}`` map and
    OVERLAYS the Firestore ``repo_state/{repo}.release_tag.version`` per-repo where present, so a
    reader behaves identically to today while the registry is still ramping (Firestore empty → pure
    manifest) and shifts to Firestore-truth repo-by-repo as docs appear. On any Firestore
    unavailability it **degrades LOUDLY to the manifest cache** (the designed offline fallback).
    """
    base = manifest_version_map(manifest)
    try:
        fs = get_all(project_id=project_id, firestore_module_factory=firestore_module_factory)
    except Exception as err:  # noqa: broad-except — any Firestore unavailability must degrade to
        # the manifest fallback cache (the designed offline fallback), never crash the caller
        logging.getLogger(__name__).warning(
            "version_registry Firestore read unavailable (%s: %s) — using manifest fallback cache",
            type(err).__name__,
            err,
        )
        return base
    for repo, rt in fs.items():
        version = rt.get("version")
        if isinstance(version, str) and version:
            base[repo] = version
    return base


def _load_manifest(path: str) -> dict[str, object]:
    with open(path, encoding="utf-8") as fh:
        loaded = cast("object", json.load(fh))
    return cast("dict[str, object]", loaded) if isinstance(loaded, dict) else {}


_USAGE = (
    "usage: version_registry_store.py set <repo> <version> <sha> "
    "[--commit-ts <iso8601>] [--project-id ID] [--emit-transition]\n"
    "       version_registry_store.py get-map [--manifest PATH] [--project-id ID]"
)


def _pop_opt(args: list[str], flag: str) -> tuple[list[str], str | None]:
    """Remove ``--flag VALUE`` from ``args`` (if present) → (remaining_args, value or None)."""
    if flag not in args:
        return args, None
    i = args.index(flag)
    value = args[i + 1] if i + 1 < len(args) else None
    return args[:i] + args[i + 2 :], (value or None)


def _main(
    argv: list[str],
    *,
    firestore_module_factory: FirestoreModuleFactory = _default_firestore_module,
) -> int:
    """CLI body — testable (the factory is injectable). Returns the process exit code.

    READ:  ``get-map [--manifest PATH] [--project-id ID]`` → JSON ``{repo: version}`` (Firestore-first,
           manifest fallback) for shell / GHA readers.
    WRITE: ``set <repo> <version> <sha> [--commit-ts <iso>] [--project-id ID] [--emit-transition]`` —
           the ``set`` verb disambiguates from ``get-map``. ``--emit-transition`` prints only
           ``<prev>\\t<written>`` so a workflow can gate notify without a second read.
    """
    if argv and argv[0] == "get-map":
        rest, manifest_path_opt = _pop_opt(list(argv[1:]), "--manifest")
        rest, project = _pop_opt(rest, "--project-id")
        manifest_path = manifest_path_opt or "workspace-manifest.json"
        version_map = resolve_version_map(
            _load_manifest(manifest_path), project_id=project, firestore_module_factory=firestore_module_factory
        )
        print(json.dumps(version_map, sort_keys=True))
        return 0

    if not argv or argv[0] != "set":
        print(_USAGE, file=sys.stderr)
        return 2
    rest, commit_ts = _pop_opt(list(argv[1:]), "--commit-ts")
    rest, project = _pop_opt(rest, "--project-id")
    emit_transition = "--emit-transition" in rest
    rest = [a for a in rest if a != "--emit-transition"]
    if len(rest) != 3:
        print(_USAGE, file=sys.stderr)
        return 2
    repo, version, sha = rest
    prev, written = set_release_version(
        repo, version, sha, commit_ts=commit_ts, project_id=project, firestore_module_factory=firestore_module_factory
    )
    if emit_transition:
        print(f"{prev}\t{written}")
    else:
        print(f"repo_state/{repo}.release_tag: {prev} -> {written}")
    return 0


if __name__ == "__main__":  # pragma: no cover — entrypoint (logic lives in _main, which IS tested)
    raise SystemExit(_main(sys.argv[1:]))
