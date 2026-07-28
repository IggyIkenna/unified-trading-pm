"""Unit tests for the generic verdict-store (Firestore, doc-per-key, latest-wins CAS).

SSOT: plans/active/monitoring_control_plane_master_2026_06_10.md (version-coherence + G5
change-freeze panels), operator decision 2026-07-27. Covers the ordering decision (the CAS heart)
and the transactional write path against an injected fake firestore module (no SDK needed) —
mirrors tests/unit/test_ci_status_store.py's structure for the generalized store.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

_STORE = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "verdict_store.py"
_spec = importlib.util.spec_from_file_location("verdict_store", _STORE)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules["verdict_store"] = _mod
_spec.loader.exec_module(_mod)

resolve_verdict = _mod.resolve_verdict
set_verdict = _mod.set_verdict
get_verdict = _mod.get_verdict
get_all_verdicts = _mod.get_all_verdicts
VERSION_COHERENCE_COLLECTION = _mod.VERSION_COHERENCE_COLLECTION
CHANGE_FREEZE_COLLECTION = _mod.CHANGE_FREEZE_COLLECTION


# ── resolve_verdict — the pure ordering decision ────────────────────────────────────────────────


def test_first_write_always_accepted_no_stored_ts():
    assert resolve_verdict(None, "2026-07-27T10:00:00Z") is True


def test_newer_checked_at_accepted():
    assert resolve_verdict("2026-07-27T09:00:00Z", "2026-07-27T10:00:00Z") is True


def test_equal_checked_at_accepted():
    assert resolve_verdict("2026-07-27T10:00:00Z", "2026-07-27T10:00:00Z") is True


def test_older_checked_at_rejected():
    """The stale-write guard — a late-arriving run for an older evaluation must not clobber a
    fresher stored verdict (the whole point of the CAS, generalized from ci_status.is_stale_write
    with no rank/FAILING carve-outs — a verdict has no lifecycle rank)."""
    assert resolve_verdict("2026-07-27T10:00:00Z", "2026-07-27T09:00:00Z") is False


def test_missing_incoming_checked_at_never_blocks():
    """A legacy/no-timestamp caller behaves as if the guard did not exist (matches
    ci_status_store.is_stale_write's conservative-only-when-both-known contract)."""
    assert resolve_verdict("2026-07-27T10:00:00Z", None) is True


def test_missing_stored_checked_at_never_blocks():
    assert resolve_verdict(None, None) is True


# ── Fake Firestore plumbing (mirrors test_ci_status_store.py) ──────────────────────────────────


class _FakeDocRef:
    def __init__(self, doc_id: str, store: dict[str, dict[str, object]]) -> None:
        self.id = doc_id
        self._store = store

    def get(self, transaction: object | None = None) -> _FakeSnap:
        return _FakeSnap(self._store.get(self.id))

    def to_dict(self) -> dict[str, object] | None:
        """Mirrors the real SDK: ``collection.stream()`` yields snapshot-like objects that carry
        BOTH ``.id`` and ``.to_dict()`` directly (unlike ``.document(id).get()``, which returns a
        separate snapshot object) — see ci_status_store.py's ``_DocRefProto``."""
        return self._store.get(self.id)


class _FakeSnap:
    def __init__(self, data: dict[str, object] | None) -> None:
        self._data = data
        self.exists = data is not None

    def to_dict(self) -> dict[str, object] | None:
        return self._data


class _FakeTxn:
    """The fake ``transactional`` body just calls the wrapped fn once — no real atomicity, same
    simplification test_ci_status_store.py's unit-fake makes (a real-Firestore emulator test would
    be the integration-level follow-up, out of scope for this unit suite)."""

    def set(self, reference: _FakeDocRef, document_data: dict[str, object]) -> None:
        reference._store[reference.id] = dict(document_data)


class _FakeCollection:
    def __init__(self, store: dict[str, dict[str, object]]) -> None:
        self._store = store

    def document(self, document_id: str) -> _FakeDocRef:
        return _FakeDocRef(document_id, self._store)

    def stream(self) -> list[_FakeDocRef]:
        return [_FakeDocRef(k, self._store) for k in self._store]


class _FakeClient:
    def __init__(self) -> None:
        self.collections: dict[str, dict[str, object]] = {}

    def collection(self, path: str) -> _FakeCollection:
        return _FakeCollection(self.collections.setdefault(path, {}))

    def transaction(self, max_attempts: int = 10) -> _FakeTxn:
        return _FakeTxn()


class _FakeFirestoreModule:
    SERVER_TIMESTAMP = "SERVER_TS"

    def __init__(self) -> None:
        self.client = _FakeClient()

    def Client(self, project: str | None = None) -> _FakeClient:  # noqa: N802 — mirrors SDK API
        return self.client

    def transactional(self, fn):  # type: ignore[no-untyped-def]
        def _wrapped(txn: object) -> object:
            return fn(txn)

        return _wrapped


def _make_factory() -> tuple[_FakeFirestoreModule, object]:
    module = _FakeFirestoreModule()

    def factory() -> _FakeFirestoreModule:
        return module

    return module, factory


# ── set_verdict / get_verdict / get_all_verdicts — the transactional write + read path ─────────


class TestSetVerdictFreshDoc:
    def test_first_write_creates_doc(self):
        _module, factory = _make_factory()
        fmf = cast("object", factory)
        prev, written = set_verdict(
            VERSION_COHERENCE_COLLECTION,
            "unified-trading-library",
            "OK",
            checked_at="2026-07-27T10:00:00Z",
            firestore_module_factory=fmf,
        )
        assert prev is None
        assert written == "OK"
        doc = get_verdict(VERSION_COHERENCE_COLLECTION, "unified-trading-library", firestore_module_factory=fmf)
        assert doc["verdict"] == "OK"
        assert doc["checked_at"] == "2026-07-27T10:00:00Z"

    def test_reasons_and_details_persisted(self):
        _module, factory = _make_factory()
        fmf = cast("object", factory)
        set_verdict(
            VERSION_COHERENCE_COLLECTION,
            "utl",
            "VERSION_SPLIT",
            reasons=["versions{}=1.2.3 != source=1.2.2"],
            details={"class": "VERSION_SPLIT"},
            checked_at="2026-07-27T10:00:00Z",
            firestore_module_factory=fmf,
        )
        doc = get_verdict(VERSION_COHERENCE_COLLECTION, "utl", firestore_module_factory=fmf)
        assert doc["reasons"] == ["versions{}=1.2.3 != source=1.2.2"]
        assert doc["details"] == {"class": "VERSION_SPLIT"}


class TestSetVerdictOrdering:
    def test_newer_write_overwrites(self):
        _module, factory = _make_factory()
        fmf = cast("object", factory)
        set_verdict(
            CHANGE_FREEZE_COLLECTION,
            "PROD_DEPLOY",
            "CLEAR",
            checked_at="2026-07-27T09:00:00Z",
            firestore_module_factory=fmf,
        )
        prev, written = set_verdict(
            CHANGE_FREEZE_COLLECTION,
            "PROD_DEPLOY",
            "BLOCKED",
            checked_at="2026-07-27T10:00:00Z",
            firestore_module_factory=fmf,
        )
        assert prev == "CLEAR"
        assert written == "BLOCKED"
        doc = get_verdict(CHANGE_FREEZE_COLLECTION, "PROD_DEPLOY", firestore_module_factory=fmf)
        assert doc["verdict"] == "BLOCKED"

    def test_stale_write_rejected_stored_doc_unchanged(self):
        """A late-arriving run for an older commit/evaluation must never clear a fresher verdict —
        the exact race class ci_status_store.is_stale_write was built to reject."""
        _module, factory = _make_factory()
        fmf = cast("object", factory)
        set_verdict(
            CHANGE_FREEZE_COLLECTION,
            "PROD_DEPLOY",
            "BLOCKED",
            checked_at="2026-07-27T10:00:00Z",
            firestore_module_factory=fmf,
        )
        prev, written = set_verdict(
            CHANGE_FREEZE_COLLECTION,
            "PROD_DEPLOY",
            "CLEAR",
            checked_at="2026-07-27T09:00:00Z",
            firestore_module_factory=fmf,
        )
        assert prev == "BLOCKED"
        assert written == "BLOCKED"  # rejected — stale write is a no-op
        doc = get_verdict(CHANGE_FREEZE_COLLECTION, "PROD_DEPLOY", firestore_module_factory=fmf)
        assert doc["verdict"] == "BLOCKED"  # stored doc unchanged

    def test_missing_checked_at_always_overwrites(self):
        """Legacy/no-timestamp writes behave as if the guard is absent (identical to the pre-guard
        contract) — never silently dropped."""
        _module, factory = _make_factory()
        fmf = cast("object", factory)
        set_verdict(
            CHANGE_FREEZE_COLLECTION,
            "AUTONOMOUS",
            "BLOCKED",
            checked_at="2026-07-27T10:00:00Z",
            firestore_module_factory=fmf,
        )
        prev, written = set_verdict(
            CHANGE_FREEZE_COLLECTION, "AUTONOMOUS", "CLEAR", checked_at=None, firestore_module_factory=fmf
        )
        assert prev == "BLOCKED"
        assert written == "CLEAR"


class TestPartitioning:
    def test_different_keys_never_contend(self):
        """Layer-1: two different repos/check_types write disjoint documents — no cross-key
        interference (the per-VM-shard / ci_status per-repo-doc principle)."""
        _module, factory = _make_factory()
        fmf = cast("object", factory)
        set_verdict(
            VERSION_COHERENCE_COLLECTION,
            "repo-a",
            "OK",
            checked_at="2026-07-27T10:00:00Z",
            firestore_module_factory=fmf,
        )
        set_verdict(
            VERSION_COHERENCE_COLLECTION,
            "repo-b",
            "VERSION_SPLIT",
            checked_at="2026-07-27T09:00:00Z",
            firestore_module_factory=fmf,
        )
        all_docs = get_all_verdicts(VERSION_COHERENCE_COLLECTION, firestore_module_factory=fmf)
        assert all_docs["repo-a"]["verdict"] == "OK"
        assert all_docs["repo-b"]["verdict"] == "VERSION_SPLIT"

    def test_different_collections_never_collide(self):
        """version_coherence_verdicts and change_freeze_verdicts share no state even when a key
        string happens to collide (e.g. a repo literally named 'PROD_DEPLOY' — pathological but
        the partitioning must hold regardless)."""
        _module, factory = _make_factory()
        fmf = cast("object", factory)
        set_verdict(
            VERSION_COHERENCE_COLLECTION,
            "PROD_DEPLOY",
            "OK",
            checked_at="2026-07-27T10:00:00Z",
            firestore_module_factory=fmf,
        )
        set_verdict(
            CHANGE_FREEZE_COLLECTION,
            "PROD_DEPLOY",
            "BLOCKED",
            checked_at="2026-07-27T10:00:00Z",
            firestore_module_factory=fmf,
        )
        vc = get_verdict(VERSION_COHERENCE_COLLECTION, "PROD_DEPLOY", firestore_module_factory=fmf)
        cf = get_verdict(CHANGE_FREEZE_COLLECTION, "PROD_DEPLOY", firestore_module_factory=fmf)
        assert vc["verdict"] == "OK"
        assert cf["verdict"] == "BLOCKED"


class TestGetAllVerdictsEmpty:
    def test_empty_collection_returns_empty_dict(self):
        _module, factory = _make_factory()
        assert get_all_verdicts(VERSION_COHERENCE_COLLECTION, firestore_module_factory=cast("object", factory)) == {}

    def test_missing_doc_returns_empty_dict(self):
        _module, factory = _make_factory()
        fmf = cast("object", factory)
        assert get_verdict(VERSION_COHERENCE_COLLECTION, "no-such-repo", firestore_module_factory=fmf) == {}


class TestProjectIdPassedToClient:
    def test_project_id_forwarded(self):
        module = MagicMock()
        client_mock = MagicMock()
        collection_mock = MagicMock()
        collection_mock.stream.return_value = []
        client_mock.collection.return_value = collection_mock
        module.Client.return_value = client_mock

        def factory():
            return module

        get_all_verdicts(VERSION_COHERENCE_COLLECTION, project_id="my-project", firestore_module_factory=factory)
        module.Client.assert_called_once_with(project="my-project")
