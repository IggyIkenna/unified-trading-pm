"""Unit tests for the CI-status Firestore side store (Phase 1).

SSOT: plans/active/ci_status_firestore_side_store_2026_06_10.md. Covers the no-downgrade CAS
decision (the heart of Layer 2 same-repo ordering) and the transactional write path against an
injected fake firestore module (no SDK needed).
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

_STORE = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "ci_status_store.py"
_spec = importlib.util.spec_from_file_location("ci_status_store", _STORE)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules["ci_status_store"] = _mod
_spec.loader.exec_module(_mod)

resolve_status = _mod.resolve_status
rank = _mod.rank
set_status = _mod.set_status
get_all = _mod.get_all
manifest_ci_status_map = _mod.manifest_ci_status_map
resolve_ci_status_map = _mod.resolve_ci_status_map


# ── resolve_status — the pure CAS decision (Layer 2) ─────────────────────────────────────────────


def test_failing_is_always_persisted_even_over_main_green():
    # a real regression must surface even from the highest green tier, on any branch
    assert resolve_status("MAIN_GREEN", "FAILING", "staging") == "FAILING"
    assert resolve_status("MAIN_GREEN", "FAILING", "main") == "FAILING"
    assert resolve_status("SIT_VALIDATED", "FAILING", "live-defi-rollout") == "FAILING"


def test_no_downgrade_keeps_higher_green_on_non_main_rerun():
    # the bug class: a staging/ldr v2 re-run on an already-promoted repo must NOT flap MAIN_GREEN down
    assert resolve_status("MAIN_GREEN", "STAGING_GREEN", "staging") == "MAIN_GREEN"
    assert resolve_status("MAIN_GREEN", "FEATURE_GREEN", "live-defi-rollout") == "MAIN_GREEN"
    assert resolve_status("SIT_VALIDATED", "STAGING_GREEN", "staging") == "SIT_VALIDATED"


def test_main_branch_is_authoritative():
    # an on-main signal is the truth — it advances AND may legitimately set a lower state
    assert resolve_status("STAGING_GREEN", "MAIN_GREEN", "main") == "MAIN_GREEN"
    assert resolve_status("MAIN_GREEN", "STAGING_GREEN", "main") == "STAGING_GREEN"  # main says so


def test_equal_or_higher_rank_advances():
    assert resolve_status("FEATURE_GREEN", "STAGING_GREEN", "staging") == "STAGING_GREEN"
    assert resolve_status("STAGING_GREEN", "SIT_VALIDATED", "staging") == "SIT_VALIDATED"
    assert resolve_status("STAGING_GREEN", "STAGING_GREEN", "staging") == "STAGING_GREEN"  # same rank


def test_fresh_repo_advances_from_none():
    assert resolve_status("NONE", "STAGING_GREEN", "staging") == "STAGING_GREEN"
    assert resolve_status("NONE", "FAILING", "staging") == "FAILING"


def test_rank_map_matches_lifecycle():
    assert rank("MAIN_GREEN") > rank("SIT_VALIDATED") > rank("STAGING_GREEN") >= rank("FEATURE_GREEN")
    assert rank("UNKNOWN_STATE") == 0


# ── set_status / get_all — transactional write against a fake firestore module ───────────────────


class _FakeSnap:
    def __init__(self, data: dict[str, object] | None):
        self._data = data
        self.exists = data is not None

    def to_dict(self) -> dict[str, object] | None:
        return self._data


class _FakeDocRef:
    def __init__(self, store: dict[str, dict[str, object]], doc_id: str):
        self._store = store
        self._id = doc_id

    def get(self, transaction: object | None = None) -> _FakeSnap:
        return _FakeSnap(self._store.get(self._id))

    @property
    def id(self) -> str:
        return self._id

    def to_dict(self) -> dict[str, object]:
        return self._store.get(self._id, {})


class _FakeCollection:
    def __init__(self, store: dict[str, dict[str, object]]):
        self._store = store

    def document(self, document_id: str) -> _FakeDocRef:
        return _FakeDocRef(self._store, document_id)

    def stream(self) -> list[_FakeDocRef]:
        return [_FakeDocRef(self._store, k) for k in self._store]


class _FakeTxn:
    def __init__(self, store: dict[str, dict[str, object]]):
        self._store = store

    def set(self, doc_ref: _FakeDocRef, data: dict[str, object]) -> None:
        self._store[doc_ref.id] = data


class _FakeClient:
    def __init__(self, store: dict[str, dict[str, object]]):
        self._store = store

    def collection(self, name: str) -> _FakeCollection:
        assert name == "ci_status"
        return _FakeCollection(self._store)

    def transaction(self) -> _FakeTxn:
        return _FakeTxn(self._store)


class _FakeFirestoreModule:
    SERVER_TIMESTAMP = "<server-ts>"

    def __init__(self, store: dict[str, dict[str, object]]):
        self._store = store

    def Client(self, project: str | None = None) -> _FakeClient:  # noqa: N802 — mirrors SDK
        return _FakeClient(self._store)

    def transactional(self, fn: Callable[..., object]) -> Callable[..., object]:
        # production wraps with retry/atomicity; the fake just invokes with the txn
        def _wrapped(txn: object) -> object:
            return fn(txn)

        return _wrapped


@pytest.fixture()
def store() -> dict[str, dict[str, object]]:
    return {}


def _factory(store: dict[str, dict[str, object]]) -> Callable[[], _FakeFirestoreModule]:
    return lambda: _FakeFirestoreModule(store)


def test_set_status_writes_fresh_repo(store: dict[str, dict[str, object]]):
    prev, written = set_status("uac", "STAGING_GREEN", "staging", "abc123", firestore_module_factory=_factory(store))
    assert (prev, written) == ("NONE", "STAGING_GREEN")
    assert store["uac"]["status"] == "STAGING_GREEN"
    assert store["uac"]["rank"] == rank("STAGING_GREEN")
    assert store["uac"]["branch"] == "staging" and store["uac"]["sha"] == "abc123"
    assert store["uac"]["updated_at"] == "<server-ts>"


def test_set_status_no_downgrade_persists_prev(store: dict[str, dict[str, object]]):
    store["uac"] = {"status": "MAIN_GREEN", "rank": 4, "branch": "main", "sha": "old"}
    prev, written = set_status("uac", "STAGING_GREEN", "staging", "new", firestore_module_factory=_factory(store))
    assert (prev, written) == ("MAIN_GREEN", "MAIN_GREEN")  # no-downgrade held
    assert store["uac"]["status"] == "MAIN_GREEN"


def test_set_status_failing_overrides(store: dict[str, dict[str, object]]):
    store["uac"] = {"status": "MAIN_GREEN", "rank": 4, "branch": "main", "sha": "old"}
    prev, written = set_status("uac", "FAILING", "staging", "bad", firestore_module_factory=_factory(store))
    assert (prev, written) == ("MAIN_GREEN", "FAILING")  # failure always surfaces
    assert store["uac"]["status"] == "FAILING"


def test_get_all_aggregates(store: dict[str, dict[str, object]]):
    set_status("uac", "MAIN_GREEN", "main", "a", firestore_module_factory=_factory(store))
    set_status("utl", "STAGING_GREEN", "staging", "b", firestore_module_factory=_factory(store))
    alls = get_all(firestore_module_factory=_factory(store))
    assert set(alls) == {"uac", "utl"}
    assert alls["uac"]["status"] == "MAIN_GREEN" and alls["utl"]["status"] == "STAGING_GREEN"


# ── READ side (Phase 2): manifest_ci_status_map + resolve_ci_status_map ──────────────────────────


def test_manifest_map_dict_shaped():
    m = {"repositories": {"uac": {"ci_status": "MAIN_GREEN"}, "utl": {"ci_status": "STAGING_GREEN"}}}
    assert manifest_ci_status_map(m) == {"uac": "MAIN_GREEN", "utl": "STAGING_GREEN"}


def test_manifest_map_list_shaped():
    m = {"repositories": [{"name": "uac", "ci_status": "FAILING"}, {"name": "utl", "ci_status": "MAIN_GREEN"}]}
    assert manifest_ci_status_map(m) == {"uac": "FAILING", "utl": "MAIN_GREEN"}


def test_manifest_map_omits_blank_and_missing():
    m = {"repositories": {"uac": {"ci_status": ""}, "utl": {}, "mtds": {"ci_status": "MAIN_GREEN"}}}
    assert manifest_ci_status_map(m) == {"mtds": "MAIN_GREEN"}  # blank + absent omitted, not None-valued


def test_resolve_firestore_overlays_manifest_per_repo(store: dict[str, dict[str, object]]):
    # manifest says uac=STAGING_GREEN, utl=MAIN_GREEN; Firestore has the newer uac=MAIN_GREEN + a fresh mtds
    set_status("uac", "MAIN_GREEN", "main", "a", firestore_module_factory=_factory(store))
    set_status("mtds", "FAILING", "staging", "b", firestore_module_factory=_factory(store))
    manifest = {"repositories": {"uac": {"ci_status": "STAGING_GREEN"}, "utl": {"ci_status": "MAIN_GREEN"}}}
    out = resolve_ci_status_map(manifest, firestore_module_factory=_factory(store))
    assert out == {
        "uac": "MAIN_GREEN",  # Firestore wins (authoritative per-repo)
        "utl": "MAIN_GREEN",  # manifest-only repo retained (not yet in Firestore)
        "mtds": "FAILING",  # Firestore-only repo added
    }


def test_resolve_falls_back_to_manifest_on_firestore_error():
    class _RaisingModule:
        def Client(self, project: str | None = None) -> object:  # noqa: N802 — mirrors SDK
            raise RuntimeError("firestore unavailable (SDK absent / transient)")

    manifest = {"repositories": {"uac": {"ci_status": "MAIN_GREEN"}}}
    out = resolve_ci_status_map(manifest, firestore_module_factory=lambda: _RaisingModule())
    assert out == {"uac": "MAIN_GREEN"}  # loud degrade to the manifest cache, never an exception


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
