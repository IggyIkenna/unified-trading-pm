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
is_stale_write = _mod.is_stale_write
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

    def transaction(self, max_attempts: int = 5) -> _FakeTxn:
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


def test_sit_validated_tree_persists_then_clears_on_status_change(store: dict[str, dict[str, object]]):
    # WS-L SIT-rehome: a SIT_VALIDATED write stores the LDR tree the cross-repo SIT validated.
    _, written = set_status(
        "uac", "SIT_VALIDATED", "live-defi-rollout", "sha1",
        sit_validated_tree="treeAAA", firestore_module_factory=_factory(store),
    )
    assert written == "SIT_VALIDATED"
    assert store["uac"]["sit_validated_tree"] == "treeAAA"
    # LOAD-BEARING SAFETY: any later non-SIT_VALIDATED status CLEARS the fingerprint, so a stale tree
    # can never validate a later, different LDR tree. main is authoritative → MAIN_GREEN.
    _, written2 = set_status("uac", "MAIN_GREEN", "main", "sha2", firestore_module_factory=_factory(store))
    assert written2 == "MAIN_GREEN"
    assert "sit_validated_tree" not in store["uac"]


def test_sit_validated_tree_carried_forward_on_repeated_sit_validated(store: dict[str, dict[str, object]]):
    # A repeated SIT_VALIDATED with no tree arg carries the stored fingerprint forward (no accidental clear).
    set_status(
        "uac", "SIT_VALIDATED", "live-defi-rollout", "s1",
        sit_validated_tree="treeAAA", firestore_module_factory=_factory(store),
    )
    set_status("uac", "SIT_VALIDATED", "live-defi-rollout", "s2", firestore_module_factory=_factory(store))
    assert store["uac"]["sit_validated_tree"] == "treeAAA"


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


def test_set_status_writes_codebase_health(store: dict[str, dict[str, object]]):
    health = {"coverage_pct": 76.7, "qg_red_reason": None, "large_file_count": 2, "warn_file_count": 1}
    set_status(
        "uac", "STAGING_GREEN", "staging", "abc", codebase_health=health, firestore_module_factory=_factory(store)
    )
    assert store["uac"]["codebase_health"] == health


def test_set_status_preserves_codebase_health_on_status_only_update(store: dict[str, dict[str, object]]):
    # A ci_status transition with NO fresh metrics must carry the existing blob forward
    # (txn.set is a full-document replace) — not wipe it.
    prior = {"coverage_pct": 88.0, "qg_red_reason": None, "large_file_count": 0, "warn_file_count": 0}
    store["uac"] = {"status": "FEATURE_GREEN", "rank": 1, "branch": "ldr", "sha": "x", "codebase_health": prior}
    set_status("uac", "STAGING_GREEN", "staging", "y", firestore_module_factory=_factory(store))
    assert store["uac"]["status"] == "STAGING_GREEN"
    assert store["uac"]["codebase_health"] == prior  # preserved


def test_set_status_overwrites_codebase_health_when_provided(store: dict[str, dict[str, object]]):
    store["uac"] = {
        "status": "FEATURE_GREEN",
        "rank": 1,
        "branch": "ldr",
        "sha": "x",
        "codebase_health": {
            "coverage_pct": 10.0,
            "qg_red_reason": "pytest",
            "large_file_count": 9,
            "warn_file_count": 9,
        },
    }
    fresh = {"coverage_pct": 91.0, "qg_red_reason": None, "large_file_count": 0, "warn_file_count": 0}
    set_status("uac", "STAGING_GREEN", "staging", "y", codebase_health=fresh, firestore_module_factory=_factory(store))
    assert store["uac"]["codebase_health"] == fresh  # overwritten


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


# ── is_stale_write — the WS-A stale-write ordering guard (pure) ───────────────────────────────────


def test_stale_write_rejects_older_commit_green():
    prev = {"status": "FAILING", "commit_ts": "2026-06-25T10:00:00Z"}
    # An older commit's late green must be rejected (older ts than the stored fail).
    assert is_stale_write(prev, "FEATURE_GREEN", "live-defi-rollout", "2026-06-25T09:00:00Z") is True


def test_stale_write_allows_newer_commit_green():
    prev = {"status": "FAILING", "commit_ts": "2026-06-25T09:00:00Z"}
    assert is_stale_write(prev, "FEATURE_GREEN", "live-defi-rollout", "2026-06-25T10:00:00Z") is False


def test_stale_write_never_blocks_failing():
    prev = {"status": "MAIN_GREEN", "commit_ts": "2026-06-25T10:00:00Z"}
    # FAILING must ALWAYS surface, even for an older commit.
    assert is_stale_write(prev, "FAILING", "live-defi-rollout", "2026-06-25T01:00:00Z") is False


def test_stale_write_never_blocks_main():
    prev = {"status": "MAIN_GREEN", "commit_ts": "2026-06-25T10:00:00Z"}
    assert is_stale_write(prev, "STAGING_GREEN", "main", "2026-06-25T01:00:00Z") is False


def test_stale_write_no_guard_without_commit_ts():
    # Legacy caller (no incoming ts) or no stored ts → never stale (identical to today).
    assert (
        is_stale_write({"status": "FAILING", "commit_ts": "2026-06-25T10:00:00Z"}, "FEATURE_GREEN", "ldr", None)
        is False
    )
    assert is_stale_write({"status": "FAILING"}, "FEATURE_GREEN", "ldr", "2026-06-25T09:00:00Z") is False


# ── set_status — stale guard + commit_ts persistence through the fake transaction ─────────────────


def test_set_status_rejects_stale_green(store: dict[str, dict[str, object]]):
    # Stored: a FAILING from a NEWER commit. A late green from an OLDER commit must NOT clear it.
    store["uac"] = {"status": "FAILING", "rank": rank("FAILING"), "commit_ts": "2026-06-25T10:00:00Z"}
    prev, written = set_status(
        "uac",
        "FEATURE_GREEN",
        "live-defi-rollout",
        "old",
        commit_ts="2026-06-25T09:00:00Z",
        firestore_module_factory=_factory(store),
    )
    assert (prev, written) == ("FAILING", "FAILING")
    assert store["uac"]["status"] == "FAILING"  # unchanged — no-op


def test_set_status_accepts_newer_green_over_fail(store: dict[str, dict[str, object]]):
    store["uac"] = {"status": "FAILING", "rank": rank("FAILING"), "commit_ts": "2026-06-25T09:00:00Z"}
    prev, written = set_status(
        "uac",
        "STAGING_GREEN",
        "live-defi-rollout",
        "new",
        commit_ts="2026-06-25T10:00:00Z",
        firestore_module_factory=_factory(store),
    )
    assert (prev, written) == ("FAILING", "STAGING_GREEN")
    assert store["uac"]["commit_ts"] == "2026-06-25T10:00:00Z"


def test_set_status_carries_commit_ts_forward(store: dict[str, dict[str, object]]):
    store["uac"] = {"status": "STAGING_GREEN", "rank": rank("STAGING_GREEN"), "commit_ts": "2026-06-25T10:00:00Z"}
    # A status update with NO commit_ts must not wipe the stored ordering key.
    set_status("uac", "MAIN_GREEN", "main", "x", firestore_module_factory=_factory(store))
    assert store["uac"]["commit_ts"] == "2026-06-25T10:00:00Z"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
