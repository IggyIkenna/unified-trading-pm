#!/usr/bin/env python3
# Epic: observability_master
# Lifecycle: permanent
# Delete-when: NA
"""Generic verdict-store — Firestore, one document per (collection, key), latest-wins CAS.

Generalizes the ``ci_status`` Firestore side-store (``ci_status_store.py``) for arbitrary
periodic/on-demand CHECK VERDICTS that are NOT CI-lifecycle-ranked. ``ci_status`` needed a
"no-downgrade" rank hierarchy (MAIN_GREEN must never be knocked down by a stale STAGING_GREEN)
because it tracks a monotonic promotion lifecycle. A verdict-store consumer here is different: each
run is a STATELESS point-in-time re-evaluation (is the fleet's version surface coherent right now?
is a change-freeze window active right now?) — there is no rank to preserve, so "the freshest
evaluation wins" is the WHOLE ordering rule.

SSOT design: plans/active/monitoring_control_plane_master_2026_06_10.md (version-coherence panel +
G5 change-freeze-check panel), operator decision 2026-07-27 ("no CI/CD billing wall anymore — build
the real Firestore verdict-store generalisation, not the faithful-port workaround").

Two writers use this module (kept in ONE store, not two, so the CAS/reader logic is written and
tested exactly once):

  * ``assert_version_coherence.py`` (via a scheduled workflow) — one doc per repo, collection
    ``version_coherence_verdicts``, key = repo name. Verdict one of
    ``OK`` / ``VERSION_SPLIT`` / ``VESTIGIAL_SCALAR_DRIFT`` / ``DEP_FLOOR_UNSATISFIABLE``.
  * ``.github/workflows/change-freeze-check.yml``'s bash recurrence/DST evaluator — one doc per
    check_type, collection ``change_freeze_verdicts``, key = ``PROD_DEPLOY`` / ``AUTONOMOUS``.
    Verdict one of ``CLEAR`` / ``BLOCKED``.

Race handling — ONE layer (simpler than ci_status's two, because there is no rank):

  * **Partitioning** (mirrors ci_status Layer 1): each ``(collection, key)`` is a disjoint
    Firestore document — two DIFFERENT keys (two repos, or PROD_DEPLOY vs AUTONOMOUS) never
    contend, no retries, no push wars.
  * **Ordering** (a simplified Layer 2): within one ``(collection, key)``, reject a write whose
    ``checked_at`` is OLDER than the currently-stored doc's ``checked_at`` — an in-flight slow run
    must never clobber a fresher verdict with stale data. This is :func:`is_stale_write` from
    ``ci_status_store.py``, generalized: no FAILING-unconditional / rank / main-authoritative
    carve-outs (those are CI-lifecycle-specific), just "newest wins".

The cloud SDK is imported lazily inside the default factory (mirrors ``ci_status_store.py`` /
``unified_trading_library.firestore_lifecycle``) so importing this module — for the pure
``resolve_verdict`` logic or in a unit test with an injected fake — never requires the SDK.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Protocol, cast

VERSION_COHERENCE_COLLECTION: str = "version_coherence_verdicts"
"""Collection for assert_version_coherence.py verdicts — one document per repo."""

CHANGE_FREEZE_COLLECTION: str = "change_freeze_verdicts"
"""Collection for change-freeze-check.yml verdicts — one document per check_type."""


def resolve_verdict(
    prev_checked_at: str | None,
    new_checked_at: str | None,
) -> bool:
    """The ordering DECISION (pure — the heart of the CAS). True = accept the incoming write.

    A write is REJECTED only when both timestamps are known AND the incoming one is strictly
    OLDER than the stored one (ISO-8601 sorts as a string, same trick ``is_stale_write`` uses).
    A missing ``checked_at`` on either side never blocks — legacy/no-timestamp callers behave
    exactly as if this guard did not exist, matching ``ci_status_store.is_stale_write``'s
    conservative-only-when-both-known contract.
    """
    if not new_checked_at or not prev_checked_at:
        return True
    return new_checked_at >= prev_checked_at


# ── Firestore client resolution — lazy + injectable (mirrors ci_status_store.py) ───────────────────


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
"""Returns the firestore MODULE (not just a client). Production uses
:func:`_default_firestore_module`; tests inject a fake module."""


def _default_firestore_module() -> _FirestoreModuleProto:
    """Lazily import ``google.cloud.firestore`` (same rationale as ci_status_store.py: importing
    this module for the pure ``resolve_verdict`` logic, or with an injected fake, never needs the
    SDK)."""
    # Deliberate lazy in-function import — sanctioned markers for both QG checks on the `from` line:
    from google.cloud import (  # noqa: imports-inside-functions # noqa: cloud-sdk-direct
        firestore,  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue, reportUnknownVariableType]
    )

    return cast(_FirestoreModuleProto, cast(object, firestore))


def set_verdict(
    collection: str,
    key: str,
    verdict: str,
    *,
    reasons: list[str] | None = None,
    details: dict[str, object] | None = None,
    checked_at: str | None = None,
    project_id: str | None = None,
    max_attempts: int = 10,
    firestore_module_factory: FirestoreModuleFactory = _default_firestore_module,
) -> tuple[str | None, str]:
    """CAS-write ``{collection}/{key}`` in a Firestore transaction (the ordering guard above).

    Returns ``(prev_verdict, written_verdict)`` — ``prev_verdict`` is ``None`` when no doc existed
    yet. ``checked_at`` (ISO-8601, the evaluation timestamp — NOT necessarily wall-clock "now": the
    caller should pass the time the check actually ran) drives :func:`resolve_verdict`: a write
    older than the stored doc's ``checked_at`` is a no-op (the stored doc is returned unchanged).
    ``reasons``/``details`` are stored verbatim on acceptance — the human-readable "why" the UI
    panel renders (mirrors ``ci_status``'s ``codebase_health`` free-form blob).
    """
    fs = firestore_module_factory()
    client = fs.Client(project=project_id)
    doc_ref = client.collection(collection).document(key)
    outcome: dict[str, object] = {}

    @fs.transactional
    def _apply(txn: _TxnProto) -> object:
        snap = doc_ref.get(transaction=txn)
        prev_dict = (snap.to_dict() or {}) if snap.exists else {}
        prev_verdict = prev_dict.get("verdict")
        prev_verdict_str = str(prev_verdict) if isinstance(prev_verdict, str) else None
        prev_checked_at = prev_dict.get("checked_at")
        prev_checked_at_str = str(prev_checked_at) if isinstance(prev_checked_at, str) else None
        if not resolve_verdict(prev_checked_at_str, checked_at):
            # Stale write — reject. The stored doc is left untouched.
            outcome["prev"] = prev_verdict_str
            outcome["written"] = prev_verdict_str or verdict
            return None
        doc: dict[str, object] = {
            "verdict": verdict,
            "reasons": reasons or [],
            "checked_at": checked_at or fs.SERVER_TIMESTAMP,
            "updated_at": fs.SERVER_TIMESTAMP,
        }
        if details is not None:
            doc["details"] = details
        txn.set(doc_ref, doc)
        outcome["prev"] = prev_verdict_str
        outcome["written"] = verdict
        return None

    # Same retry shape as ci_status_store.set_status: the transactional decorator retries Aborted
    # (write contention) up to max_attempts; we additionally retry the whole call a few times on
    # transient DeadlineExceeded/ServiceUnavailable, matched by exception NAME (SDK-free import).
    _transient = {"DeadlineExceeded", "ServiceUnavailable", "RetryError", "_MultiThreadedRendezvous"}
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            _apply(client.transaction(max_attempts=max_attempts))
            return cast("str | None", outcome.get("prev")), cast("str", outcome.get("written", verdict))
        except Exception as err:  # noqa: broad-except — re-raised below unless transient-by-name;
            # matched by exception class NAME (not isinstance) so this module stays google.api_core-import-free
            if type(err).__name__ not in _transient or attempt == 2:
                raise
            last_err = err
            time.sleep(0.5 * (attempt + 1))
    raise last_err if last_err is not None else RuntimeError("set_verdict: unreachable")


def get_all_verdicts(
    collection: str,
    *,
    project_id: str | None = None,
    firestore_module_factory: FirestoreModuleFactory = _default_firestore_module,
) -> dict[str, dict[str, object]]:
    """Read every doc in a collection — ``{key: doc_dict}``. A single collection query."""
    fs = firestore_module_factory()
    client = fs.Client(project=project_id)
    out: dict[str, dict[str, object]] = {}
    for doc in client.collection(collection).stream():
        out[doc.id] = doc.to_dict() or {}
    return out


def get_verdict(
    collection: str,
    key: str,
    *,
    project_id: str | None = None,
    firestore_module_factory: FirestoreModuleFactory = _default_firestore_module,
) -> dict[str, object]:
    """Read ONE ``{collection}/{key}`` doc — or ``{}`` if absent. Reuses ``get_all_verdicts`` (the
    collections this module manages are small — a couple dozen repos / check_types)."""
    return get_all_verdicts(collection, project_id=project_id, firestore_module_factory=firestore_module_factory).get(
        key, {}
    )


if __name__ == "__main__":
    import argparse
    import sys

    _parser = argparse.ArgumentParser(prog="verdict_store.py")
    _sub = _parser.add_subparsers(dest="cmd", required=True)

    _set_p = _sub.add_parser("set", help="CAS-write one {collection}/{key} verdict doc")
    _set_p.add_argument("--collection", required=True)
    _set_p.add_argument("--key", required=True)
    _set_p.add_argument("--verdict", required=True)
    _set_p.add_argument("--reasons-json", default=None, help='JSON list of strings, e.g. \'["a","b"]\'')
    _set_p.add_argument("--details-json", default=None, help='JSON object, e.g. \'{"k": "v"}\'')
    _set_p.add_argument("--checked-at", default=None, help="ISO-8601 evaluation timestamp")
    _set_p.add_argument("--project-id", default=None)

    _get_p = _sub.add_parser("get", help="Read one {collection}/{key} doc as JSON")
    _get_p.add_argument("--collection", required=True)
    _get_p.add_argument("--key", required=True)
    _get_p.add_argument("--project-id", default=None)

    _get_all_p = _sub.add_parser("get-all", help="Read every doc in a collection as JSON {key: doc}")
    _get_all_p.add_argument("--collection", required=True)
    _get_all_p.add_argument("--project-id", default=None)

    _ns = _parser.parse_args(sys.argv[1:])

    if _ns.cmd == "set":
        _reasons: list[str] | None = None
        if _ns.reasons_json:
            _decoded_reasons = cast("object", json.loads(_ns.reasons_json))
            _reasons = cast("list[str]", _decoded_reasons) if isinstance(_decoded_reasons, list) else None
        _details: dict[str, object] | None = None
        if _ns.details_json:
            _decoded_details = cast("object", json.loads(_ns.details_json))
            _details = cast("dict[str, object]", _decoded_details) if isinstance(_decoded_details, dict) else None
        _prev, _written = set_verdict(
            _ns.collection,
            _ns.key,
            _ns.verdict,
            reasons=_reasons,
            details=_details,
            checked_at=_ns.checked_at,
            project_id=_ns.project_id,
        )
        print(f"{_ns.collection}/{_ns.key}: {_prev} -> {_written}")
        raise SystemExit(0)

    if _ns.cmd == "get":
        _doc = get_verdict(_ns.collection, _ns.key, project_id=_ns.project_id)
        print(json.dumps(_doc, sort_keys=True, default=str))
        raise SystemExit(0)

    if _ns.cmd == "get-all":
        _all_docs = get_all_verdicts(_ns.collection, project_id=_ns.project_id)
        print(json.dumps(_all_docs, sort_keys=True, default=str))
        raise SystemExit(0)
