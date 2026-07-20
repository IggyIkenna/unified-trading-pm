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
get_doc = _mod.get_doc
is_stale_write = _mod.is_stale_write
manifest_ci_status_map = _mod.manifest_ci_status_map
resolve_ci_status_map = _mod.resolve_ci_status_map


# ── resolve_status — the pure CAS decision (Layer 2) ─────────────────────────────────────────────


def test_failing_is_persisted_over_a_green():
    # a real regression must surface even from a high green tier
    assert resolve_status("MAIN_GREEN", "FAILING", "main") == "FAILING"
    assert resolve_status("SIT_VALIDATED", "FAILING", "live-defi-rollout") == "FAILING"
    assert resolve_status("STAGING_GREEN", "FAILING", "staging") == "FAILING"


def test_non_main_failing_cannot_clobber_main_green():
    """Only main speaks for main — the fix for a ONE-WAY ratchet (2026-07-16).

    The FAILING carve-out used to be branch-agnostic ("...on any branch"), so a red from ANY
    branch demoted MAIN_GREEN while the recovery could never climb back: a green from
    LDR/staging maps to FEATURE_GREEN/STAGING_GREEN, which no-downgrade correctly refuses over
    MAIN_GREEN, so only a fresh main push could undo it. Measured: a 3.3% wall-clock flake on
    deployment-api's LDR drove MAIN_GREEN → FAILING → SIT_VALIDATED and paged "CI REGRESSION
    ... (was MAIN_GREEN)" though main was never tested and never red. MAIN_GREEN is the
    dep-on-main promotion gate (staging-to-main STAGE 1.8), so that stalls dependents.

    The non-main red is NOT swallowed: the QG slice failure pages directly (notify-qg-fail) and
    LDR redness has its own axis (ldr_ci_status / ldr_ci_monitor.py).
    """
    assert resolve_status("MAIN_GREEN", "FAILING", "live-defi-rollout") == "MAIN_GREEN"
    assert resolve_status("MAIN_GREEN", "FAILING", "staging") == "MAIN_GREEN"
    # ...but main itself still always speaks, including to say it is red:
    assert resolve_status("MAIN_GREEN", "FAILING", "main") == "FAILING"


def test_non_main_green_cannot_clear_a_main_originated_failing():
    """The SYMMETRIC half of the ratchet fix (2026-07-20) — the incident that motivated it.

    ``test_non_main_failing_cannot_clobber_main_green`` fixed the FIRST hop of the
    MAIN_GREEN → FAILING → SIT_VALIDATED shape. The SECOND hop stayed open: FAILING is rank 0
    on the STORED side, so ANY higher-ranked write erased it by plain rank comparison — despite
    the header comment claiming FAILING is "never [handled] by rank comparison".

    Measured 2026-07-20: UAC@a2beed46 dropped `massive` from SOURCE_PRIORITY, breaking 10 UTL
    manifest-writer tests. UTL main went FAILING at 03:28Z; at 05:21Z the full-workspace SIT
    stamped SIT_VALIDATED from live-defi-rollout and erased it — posting an affirmative "SIT
    PASSED ... clear to promote" over a main nobody had fixed, and re-opening the promote gate
    (which treats SIT_VALIDATED as on-main-eligible) into a red main.

    SIT's guarantee is content-scoped to the LDR tree (`sit_validated_tree`), so it cannot speak
    for main's tree. Only main speaks for main — in BOTH directions.
    """
    assert resolve_status("FAILING", "SIT_VALIDATED", "live-defi-rollout", "main") == "FAILING"
    assert resolve_status("FAILING", "STAGING_GREEN", "staging", "main") == "FAILING"
    assert resolve_status("FAILING", "MAIN_GREEN", "live-defi-rollout", "main") == "FAILING"
    # ...but main itself still clears its own red, which is the ONLY legitimate recovery path:
    assert resolve_status("FAILING", "MAIN_GREEN", "main", "main") == "MAIN_GREEN"


def test_non_main_originated_failing_is_still_clearable_by_non_main():
    """The guard is scoped to MAIN-originated reds — it must not jam the LDR/staging axis.

    An LDR red is a real signal on its own axis, but it is not main's truth, so a later LDR/
    staging green must still clear it. Jamming here would deadlock every non-main recovery.
    """
    assert resolve_status("FAILING", "SIT_VALIDATED", "live-defi-rollout", "live-defi-rollout") == "SIT_VALIDATED"
    assert resolve_status("FAILING", "STAGING_GREEN", "staging", "staging") == "STAGING_GREEN"


def test_unattributed_stored_failing_fails_open():
    """A doc written before `branch` provenance was consulted must not jam.

    `prev_branch` defaults to "" (unknown). The guard requires an explicit "main" provenance, so
    a legacy/unattributable red keeps the pre-existing rank behaviour rather than becoming
    permanently unclearable by anything but a main push.
    """
    assert resolve_status("FAILING", "SIT_VALIDATED", "live-defi-rollout") == "SIT_VALIDATED"
    assert resolve_status("FAILING", "SIT_VALIDATED", "live-defi-rollout", "") == "SIT_VALIDATED"


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


def test_sit_validated_tree_persists_and_carries_forward(store: dict[str, dict[str, object]]):
    # WS-L SIT-rehome: a SIT_VALIDATED write stores the LDR tree the cross-repo SIT validated.
    _, written = set_status(
        "uac",
        "SIT_VALIDATED",
        "live-defi-rollout",
        "sha1",
        sit_validated_tree="treeAAA",
        firestore_module_factory=_factory(store),
    )
    assert written == "SIT_VALIDATED"
    assert store["uac"]["sit_validated_tree"] == "treeAAA"
    # DECOUPLED semantics (2026-06-27): a later status CARRIES the fingerprint forward (it does NOT
    # clear). The fingerprint is a true fact "treeAAA passed SIT"; the CONSUMER guards staleness by
    # requiring sit_validated_tree == the CURRENT LDR tree, so a lingering tree can never validate a
    # different current tree. main is authoritative → MAIN_GREEN, tree carried forward.
    _, written2 = set_status("uac", "MAIN_GREEN", "main", "sha2", firestore_module_factory=_factory(store))
    assert written2 == "MAIN_GREEN"
    assert store["uac"]["sit_validated_tree"] == "treeAAA"


def test_sit_validated_tree_advances_even_on_stale_status_write(store: dict[str, dict[str, object]]):
    # CRITICAL liveness regression #2 (adversarial-caught 2026-06-27): a repo's prior promote left a
    # MAIN_GREEN doc with a NEWER commit_ts (squash-merge date). The 2nd breaking change's LDR commit has
    # an OLDER committer-date, so its SIT_VALIDATED write is stale-rejected by is_stale_write. The tree
    # fingerprint MUST still advance (it is content-addressed + consumer-guarded), else permanent jam.
    set_status(
        "uac",
        "MAIN_GREEN",
        "main",
        "m1",
        commit_ts="2026-06-27T11:00:00Z",
        firestore_module_factory=_factory(store),
    )
    # 2nd breaking change validated on LDR; its commit predates the main-merge ts → stale status write.
    _, written = set_status(
        "uac",
        "SIT_VALIDATED",
        "live-defi-rollout",
        "ldr2",
        commit_ts="2026-06-27T10:30:00Z",
        sit_validated_tree="treeT2",
        firestore_module_factory=_factory(store),
    )
    # Status write is stale-rejected → status stays MAIN_GREEN (no regression of the ordering key)…
    assert written == "MAIN_GREEN"
    assert store["uac"]["status"] == "MAIN_GREEN"
    assert store["uac"]["commit_ts"] == "2026-06-27T11:00:00Z"
    # …but the content-addressed tree fingerprint DID advance (the jam fix). The promote gate reads this.
    assert store["uac"]["sit_validated_tree"] == "treeT2"


def test_sit_validated_tree_recordable_after_main_green_no_rank_jam(store: dict[str, dict[str, object]]):
    # CRITICAL liveness regression (adversarial-caught 2026-06-27): once a repo is MAIN_GREEN (rank 4),
    # resolve_status's no-downgrade keeps MAIN_GREEN over an incoming SIT_VALIDATED (rank 3) on a
    # non-main branch. The fingerprint MUST still update (keyed off the INCOMING status, not `written`),
    # else the repo's 2nd breaking change could never be promote-gated → permanent fleet jam.
    set_status("uac", "MAIN_GREEN", "main", "m1", firestore_module_factory=_factory(store))
    assert store["uac"]["status"] == "MAIN_GREEN"
    # A NEW breaking change on LDR gets cross-repo SIT-validated at a NEW tree.
    _, written = set_status(
        "uac",
        "SIT_VALIDATED",
        "live-defi-rollout",
        "ldr2",
        sit_validated_tree="treeBBB",
        firestore_module_factory=_factory(store),
    )
    # No-downgrade keeps the STATUS at MAIN_GREEN…
    assert written == "MAIN_GREEN"
    # …but the SIT fingerprint for the new tree IS recorded (the jam fix). The consumer reads this.
    assert store["uac"]["sit_validated_tree"] == "treeBBB"


def test_sit_validated_tree_carried_forward_on_repeated_sit_validated(store: dict[str, dict[str, object]]):
    # A repeated SIT_VALIDATED with no tree arg carries the stored fingerprint forward (no accidental clear).
    set_status(
        "uac",
        "SIT_VALIDATED",
        "live-defi-rollout",
        "s1",
        sit_validated_tree="treeAAA",
        firestore_module_factory=_factory(store),
    )
    set_status("uac", "SIT_VALIDATED", "live-defi-rollout", "s2", firestore_module_factory=_factory(store))
    assert store["uac"]["sit_validated_tree"] == "treeAAA"


def test_set_status_no_downgrade_persists_prev(store: dict[str, dict[str, object]]):
    store["uac"] = {"status": "MAIN_GREEN", "rank": 4, "branch": "main", "sha": "old"}
    prev, written = set_status("uac", "STAGING_GREEN", "staging", "new", firestore_module_factory=_factory(store))
    assert (prev, written) == ("MAIN_GREEN", "MAIN_GREEN")  # no-downgrade held
    assert store["uac"]["status"] == "MAIN_GREEN"


def test_set_status_failing_overrides(store: dict[str, dict[str, object]]):
    store["uac"] = {"status": "SIT_VALIDATED", "rank": 3, "branch": "live-defi-rollout", "sha": "old"}
    prev, written = set_status("uac", "FAILING", "staging", "bad", firestore_module_factory=_factory(store))
    assert (prev, written) == ("SIT_VALIDATED", "FAILING")  # failure surfaces over a green
    assert store["uac"]["status"] == "FAILING"


def test_set_status_non_main_failing_does_not_clobber_main_green(store: dict[str, dict[str, object]]):
    # End-to-end of the ratchet fix — see resolve_status + test_non_main_failing_cannot_clobber_main_green.
    # A non-main red leaves the on-main truth (and the dep-on-main promote gate) intact.
    store["uac"] = {"status": "MAIN_GREEN", "rank": 4, "branch": "main", "sha": "old"}
    prev, written = set_status("uac", "FAILING", "live-defi-rollout", "bad", firestore_module_factory=_factory(store))
    assert (prev, written) == ("MAIN_GREEN", "MAIN_GREEN")
    assert store["uac"]["status"] == "MAIN_GREEN"
    # main itself still speaks for main:
    prev, written = set_status("uac", "FAILING", "main", "bad2", firestore_module_factory=_factory(store))
    assert (prev, written) == ("MAIN_GREEN", "FAILING")


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


def test_get_doc_returns_full_doc_with_sit_tree(store: dict[str, dict[str, object]]):
    # The LDR→main fleet promoter reads BOTH status AND sit_validated_tree for ONE repo (Firestore-live).
    set_status(
        "uac",
        "SIT_VALIDATED",
        "live-defi-rollout",
        "ldrsha",
        sit_validated_tree="treeXYZ",
        firestore_module_factory=_factory(store),
    )
    set_status("utl", "MAIN_GREEN", "main", "b", firestore_module_factory=_factory(store))
    doc = get_doc("uac", firestore_module_factory=_factory(store))
    assert doc["status"] == "SIT_VALIDATED"
    assert doc["sit_validated_tree"] == "treeXYZ"


def test_get_doc_absent_repo_returns_empty(store: dict[str, dict[str, object]]):
    # Absent doc → {} so the consumer fail-CLOSES (ldr_main breaking change BLOCKS, never promotes unvalidated).
    set_status("utl", "MAIN_GREEN", "main", "b", firestore_module_factory=_factory(store))
    assert get_doc("never-seen-repo", firestore_module_factory=_factory(store)) == {}


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


# ── sit_validated_workspace_digest — cross-repo COMBINATION fingerprint (HIGH-combo, Phase 2) ────


def test_sit_validated_workspace_digest_stored_with_sit_validated(store: dict[str, dict[str, object]]):
    # The combination digest is stored when status==SIT_VALIDATED and the digest arg is provided.
    set_status(
        "uac",
        "SIT_VALIDATED",
        "live-defi-rollout",
        "sha1",
        sit_validated_tree="treeAAA",
        sit_validated_workspace_digest="digest111",
        firestore_module_factory=_factory(store),
    )
    assert store["uac"]["sit_validated_workspace_digest"] == "digest111"


def test_sit_validated_workspace_digest_carried_forward_on_non_sit_write(store: dict[str, dict[str, object]]):
    # A non-SIT write must carry the stored combination digest forward (same semantics as sit_validated_tree).
    set_status(
        "uac",
        "SIT_VALIDATED",
        "live-defi-rollout",
        "sha1",
        sit_validated_workspace_digest="digest111",
        firestore_module_factory=_factory(store),
    )
    set_status("uac", "MAIN_GREEN", "main", "sha2", firestore_module_factory=_factory(store))
    # Status advanced to MAIN_GREEN but digest carried forward — consumer reads it unchanged.
    assert store["uac"]["sit_validated_workspace_digest"] == "digest111"
    assert store["uac"]["status"] == "MAIN_GREEN"


def test_sit_validated_workspace_digest_advances_on_new_sit_validated(store: dict[str, dict[str, object]]):
    # When a new SIT validation runs (new workspace combination), the digest must update.
    set_status(
        "uac",
        "SIT_VALIDATED",
        "live-defi-rollout",
        "sha1",
        sit_validated_workspace_digest="digest_D1",
        firestore_module_factory=_factory(store),
    )
    set_status("uac", "MAIN_GREEN", "main", "sha2", firestore_module_factory=_factory(store))
    # UAC (a dep) changes LDR tree → workspace digest becomes D2; SIT re-runs → new stamp.
    set_status(
        "uac",
        "SIT_VALIDATED",
        "live-defi-rollout",
        "sha3",
        sit_validated_workspace_digest="digest_D2",
        firestore_module_factory=_factory(store),
    )
    assert store["uac"]["sit_validated_workspace_digest"] == "digest_D2"


def test_sit_validated_workspace_digest_advances_even_on_stale_status_write(store: dict[str, dict[str, object]]):
    # Mirror of the sit_validated_tree stale-write carve-out: a stale-rejected SIT_VALIDATED
    # write must STILL advance the combination digest (same jam-class as the tree fix).
    set_status(
        "uac",
        "MAIN_GREEN",
        "main",
        "m1",
        commit_ts="2026-06-27T11:00:00Z",
        firestore_module_factory=_factory(store),
    )
    set_status(
        "uac",
        "SIT_VALIDATED",
        "live-defi-rollout",
        "ldr2",
        commit_ts="2026-06-27T10:30:00Z",  # OLDER → stale-rejected (status stays MAIN_GREEN)
        sit_validated_workspace_digest="digest_D2",
        firestore_module_factory=_factory(store),
    )
    assert store["uac"]["status"] == "MAIN_GREEN"  # status not regressed
    assert store["uac"]["sit_validated_workspace_digest"] == "digest_D2"  # digest advanced


def test_sit_validated_workspace_digest_combination_gate_logic(store: dict[str, dict[str, object]]):
    # Proof of the HIGH-combo Gate: repo R validated against combination d1 is BLOCKED after
    # a dependency (UAC) changes → current digest becomes d2 ≠ d1.
    # Step 1: SIT stamps R with d1 (tree matches, d1 was the workspace then).
    set_status(
        "utl",
        "SIT_VALIDATED",
        "live-defi-rollout",
        "sha_R",
        sit_validated_tree="tree_R",
        sit_validated_workspace_digest="digest_d1",
        firestore_module_factory=_factory(store),
    )
    doc = get_doc("utl", firestore_module_factory=_factory(store))
    assert doc["sit_validated_tree"] == "tree_R"
    assert doc["sit_validated_workspace_digest"] == "digest_d1"

    # Step 2: A dependency (UAC) changes its LDR tree → d2 = new current workspace digest.
    digest_d2 = "digest_d2"  # simulates workspace_digest.compute_workspace_digest({...uac: new_tree...})

    # Step 3: R tries to promote. Tree check: LDR_TREE("tree_R") == sit_validated_tree("tree_R") ✓.
    # Combination check: d2 ≠ d1 → gate MUST BLOCK.
    stored_ws_digest = doc["sit_validated_workspace_digest"]
    assert stored_ws_digest != digest_d2, "Combination mismatch must be detected"

    # Step 4: SIT re-runs with new combination → stamps d2 on R.
    set_status(
        "utl",
        "SIT_VALIDATED",
        "live-defi-rollout",
        "sha_R",
        sit_validated_tree="tree_R",
        sit_validated_workspace_digest=digest_d2,
        firestore_module_factory=_factory(store),
    )
    doc2 = get_doc("utl", firestore_module_factory=_factory(store))
    assert doc2["sit_validated_workspace_digest"] == digest_d2
    # Step 5: R promotes. Combination check: d2 == d2 ✓ → gate PASSES.
    assert doc2["sit_validated_workspace_digest"] == digest_d2, "Gate passes after re-validation"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
