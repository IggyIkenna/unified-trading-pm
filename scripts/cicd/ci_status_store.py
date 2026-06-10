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

from collections.abc import Callable
from typing import Protocol, cast

# ── Lifecycle ranks — MUST match ci-status-update.yml `_GREEN_RANK` (the SSOT semantics) ──────────
# FAILING is rank 0 here but is handled by the unconditional carve-out in resolve_status, never by
# rank comparison (a regression must always surface, even from a higher-ranked green).
_GREEN_RANK: dict[str, int] = {
    "FAILING": 0,
    "LOCAL_PASS": 1,
    "FEATURE_GREEN": 1,
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
    from google.cloud import (
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


if __name__ == "__main__":  # tiny CLI for the GHA dual-write: ci_status_store.py REPO STATUS BRANCH SHA
    import sys

    if len(sys.argv) != 5:
        print("usage: ci_status_store.py <repo> <status> <branch> <sha>", file=sys.stderr)
        raise SystemExit(2)
    _repo, _status, _branch, _sha = sys.argv[1:5]
    _prev, _written = set_status(_repo, _status, _branch, _sha)
    print(f"ci_status/{_repo}: {_prev} -> {_written}")
