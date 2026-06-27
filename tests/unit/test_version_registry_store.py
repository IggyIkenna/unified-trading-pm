"""Unit tests for the version-registry Firestore side store (Phase-2 foundation, item B).

SSOT: plans/active/cicd_phase2_foundation_2026_06_27.md. Covers the semver-monotonic CAS decision,
the stale-write guard, and — critically — that the transactional write is FIELD-SCOPED (merge=True
on the shared ``repo_state/{repo}`` doc, so it never clobbers the sibling ci_failure / promotion_lag
fields), all against an injected fake firestore module (no SDK needed).
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

_STORE = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "version_registry_store.py"
_spec = importlib.util.spec_from_file_location("version_registry_store", _STORE)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules["version_registry_store"] = _mod
_spec.loader.exec_module(_mod)

semver_tuple = _mod.semver_tuple
is_plain_semver = _mod.is_plain_semver
resolve_version = _mod.resolve_version
is_stale_write = _mod.is_stale_write
set_release_version = _mod.set_release_version
get_all = _mod.get_all
manifest_version_map = _mod.manifest_version_map
resolve_version_map = _mod.resolve_version_map
_main = _mod._main
_pop_opt = _mod._pop_opt


# ── semver parsing ───────────────────────────────────────────────────────────────────────────────


def test_semver_tuple_plain():
    assert semver_tuple("1.2.569") == (1, 2, 569)
    assert semver_tuple("0.0.0") == (0, 0, 0)
    assert semver_tuple("10.9.8") == (10, 9, 8)


def test_semver_tuple_non_plain_is_unset():
    # dev/local/pre-release suffixes are not plain 3-part → treated as unset (0,0,0)
    assert semver_tuple("1.0.1.dev0") == (0, 0, 0)
    assert semver_tuple("1.0.0+local") == (0, 0, 0)
    assert semver_tuple("v1.2.3") == (0, 0, 0)  # leading v is not plain
    assert semver_tuple("") == (0, 0, 0)
    assert semver_tuple("garbage") == (0, 0, 0)


def test_is_plain_semver():
    assert is_plain_semver("1.2.3") is True
    assert is_plain_semver("1.0.1.dev0") is False
    assert is_plain_semver("1.0.0+abc") is False
    assert is_plain_semver("v1.2.3") is False
    assert is_plain_semver("") is False


# ── resolve_version — the pure no-downgrade decision ─────────────────────────────────────────────


def test_resolve_version_advances_on_higher():
    assert resolve_version("1.2.3", "1.2.4") == "1.2.4"
    assert resolve_version("1.2.3", "1.3.0") == "1.3.0"
    assert resolve_version("1.2.3", "2.0.0") == "2.0.0"


def test_resolve_version_no_downgrade():
    assert resolve_version("1.2.4", "1.2.3") == "1.2.4"  # lower kept
    assert resolve_version("1.2.3", "1.2.3") == "1.2.3"  # equal kept
    assert resolve_version("2.0.0", "1.9.9") == "2.0.0"


def test_resolve_version_first_write():
    assert resolve_version("", "1.0.0") == "1.0.0"
    assert resolve_version("", "0.0.0") == "0.0.0"


# ── is_stale_write — the monotonic stale-write guard (pure) ───────────────────────────────────────


def test_stale_write_advance_never_stale():
    prev = {"version": "1.2.3", "commit_ts": "2026-06-25T10:00:00Z"}
    # higher version always advances
    assert is_stale_write(prev, "1.2.4") is False


def test_stale_write_first_write_never_stale():
    assert is_stale_write({}, "1.0.0") is False
    assert is_stale_write({"version": ""}, "0.0.1") is False


def test_stale_write_equal_or_lower_is_stale():
    prev = {"version": "1.2.4", "commit_ts": "2026-06-25T10:00:00Z"}
    assert is_stale_write(prev, "1.2.4") is True  # equal re-push → no-op
    assert is_stale_write(prev, "1.2.3") is True  # lower (backfill) → no-op


# ── set_release_version / get_all — transactional write against a fake firestore module ──────────


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


def _deep_merge(dst: dict[str, object], src: dict[str, object]) -> None:
    """Mimic Firestore merge=True deep-merge of nested maps."""
    for k, v in src.items():
        existing = dst.get(k)
        if isinstance(v, dict) and isinstance(existing, dict):
            _deep_merge(existing, v)  # type: ignore[arg-type]  # both proven dicts
        else:
            dst[k] = v


class _FakeTxn:
    def __init__(self, store: dict[str, dict[str, object]]):
        self._store = store

    def set(self, doc_ref: _FakeDocRef, data: dict[str, object], merge: bool = False) -> None:
        if merge and doc_ref.id in self._store:
            _deep_merge(self._store[doc_ref.id], data)
        else:
            self._store[doc_ref.id] = dict(data)


class _FakeClient:
    def __init__(self, store: dict[str, dict[str, object]]):
        self._store = store

    def collection(self, name: str) -> _FakeCollection:
        assert name == "repo_state"
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
        def _wrapped(txn: object) -> object:
            return fn(txn)

        return _wrapped


@pytest.fixture()
def store() -> dict[str, dict[str, object]]:
    return {}


def _factory(store: dict[str, dict[str, object]]) -> Callable[[], _FakeFirestoreModule]:
    return lambda: _FakeFirestoreModule(store)


def test_set_writes_fresh_repo(store: dict[str, dict[str, object]]):
    prev, written = set_release_version(
        "uac", "0.10.0", "abc123", commit_ts="2026-06-25T10:00:00Z", firestore_module_factory=_factory(store)
    )
    assert (prev, written) == ("NONE", "0.10.0")
    rt = store["uac"]["release_tag"]
    assert rt == {
        "version": "0.10.0",
        "tag": "v0.10.0",
        "sha": "abc123",
        "updated_at": "<server-ts>",
        "commit_ts": "2026-06-25T10:00:00Z",
    }


def test_set_no_downgrade_keeps_prev(store: dict[str, dict[str, object]]):
    store["uac"] = {"release_tag": {"version": "1.2.4", "tag": "v1.2.4", "sha": "old"}}
    prev, written = set_release_version("uac", "1.2.3", "new", firestore_module_factory=_factory(store))
    assert (prev, written) == ("1.2.4", "1.2.4")  # no-downgrade held
    assert store["uac"]["release_tag"]["version"] == "1.2.4"
    assert store["uac"]["release_tag"]["sha"] == "old"  # untouched


def test_set_advances_on_higher(store: dict[str, dict[str, object]]):
    store["uac"] = {"release_tag": {"version": "1.2.3", "tag": "v1.2.3", "sha": "old"}}
    prev, written = set_release_version(
        "uac", "1.3.0", "new", commit_ts="2026-06-25T12:00:00Z", firestore_module_factory=_factory(store)
    )
    assert (prev, written) == ("1.2.3", "1.3.0")
    assert store["uac"]["release_tag"]["sha"] == "new"
    assert store["uac"]["release_tag"]["commit_ts"] == "2026-06-25T12:00:00Z"


def test_set_merge_preserves_sibling_repo_state_fields(store: dict[str, dict[str, object]]):
    # THE critical property: repo_state/{repo} is shared. Writing release_tag must NOT clobber the
    # ci_failure / promotion_lag fields owned by other writers.
    store["uac"] = {
        "ci_failure": {"reason": "pytest", "run_url": "http://x"},
        "promotion_lag": {"minutes": 42},
        "release_tag": {"version": "1.0.0", "tag": "v1.0.0", "sha": "old"},
    }
    set_release_version("uac", "1.0.1", "new", firestore_module_factory=_factory(store))
    assert store["uac"]["ci_failure"] == {"reason": "pytest", "run_url": "http://x"}  # preserved
    assert store["uac"]["promotion_lag"] == {"minutes": 42}  # preserved
    assert store["uac"]["release_tag"]["version"] == "1.0.1"  # advanced


def test_set_rejects_non_plain_version(store: dict[str, dict[str, object]]):
    with pytest.raises(ValueError, match="non-plain-3-part"):
        set_release_version("uac", "1.0.1.dev0", "abc", firestore_module_factory=_factory(store))
    assert "uac" not in store  # nothing written


def test_set_carries_commit_ts_forward(store: dict[str, dict[str, object]]):
    store["uac"] = {
        "release_tag": {"version": "1.2.3", "tag": "v1.2.3", "sha": "x", "commit_ts": "2026-06-25T10:00:00Z"}
    }
    # An advance with NO commit_ts must not wipe the stored ordering key.
    set_release_version("uac", "1.2.4", "y", firestore_module_factory=_factory(store))
    assert store["uac"]["release_tag"]["commit_ts"] == "2026-06-25T10:00:00Z"


def test_set_stale_re_push_is_noop(store: dict[str, dict[str, object]]):
    store["uac"] = {
        "release_tag": {"version": "1.2.4", "tag": "v1.2.4", "sha": "keep", "commit_ts": "2026-06-25T10:00:00Z"}
    }
    prev, written = set_release_version(
        "uac", "1.2.4", "dup", commit_ts="2026-06-25T11:00:00Z", firestore_module_factory=_factory(store)
    )
    assert (prev, written) == ("1.2.4", "1.2.4")
    assert store["uac"]["release_tag"]["sha"] == "keep"  # no churn


def test_get_all_returns_only_release_tag_docs(store: dict[str, dict[str, object]]):
    set_release_version("uac", "1.0.0", "a", firestore_module_factory=_factory(store))
    set_release_version("utl", "0.12.0", "b", firestore_module_factory=_factory(store))
    store["mtds"] = {"ci_failure": {"reason": "x"}}  # no release_tag → omitted
    alls = get_all(firestore_module_factory=_factory(store))
    assert set(alls) == {"uac", "utl"}
    assert alls["uac"]["version"] == "1.0.0" and alls["utl"]["version"] == "0.12.0"


# ── READ side: manifest_version_map + resolve_version_map ─────────────────────────────────────────


def test_manifest_version_map():
    m = {"versions": {"uac": "1.0.0", "utl": "0.12.0", "blank": ""}}
    assert manifest_version_map(m) == {"uac": "1.0.0", "utl": "0.12.0"}  # blank omitted


def test_manifest_version_map_empty():
    assert manifest_version_map({}) == {}
    assert manifest_version_map({"versions": "not-a-dict"}) == {}


def test_resolve_firestore_overlays_manifest_per_repo(store: dict[str, dict[str, object]]):
    set_release_version("uac", "1.1.0", "a", firestore_module_factory=_factory(store))  # newer than manifest
    set_release_version("mtds", "0.5.0", "b", firestore_module_factory=_factory(store))  # firestore-only
    manifest = {"versions": {"uac": "1.0.0", "utl": "0.12.0"}}
    out = resolve_version_map(manifest, firestore_module_factory=_factory(store))
    assert out == {
        "uac": "1.1.0",  # Firestore wins (authoritative per-repo)
        "utl": "0.12.0",  # manifest-only repo retained
        "mtds": "0.5.0",  # Firestore-only repo added
    }


def test_resolve_falls_back_to_manifest_on_firestore_error():
    class _RaisingModule:
        def Client(self, project: str | None = None) -> object:  # noqa: N802 — mirrors SDK
            raise RuntimeError("firestore unavailable (SDK absent / transient)")

    manifest = {"versions": {"uac": "1.0.0"}}
    out = resolve_version_map(manifest, firestore_module_factory=lambda: _RaisingModule())
    assert out == {"uac": "1.0.0"}  # loud degrade to the manifest cache, never an exception


# ── CLI (_main) — testable with the injected fake factory ────────────────────────────────────────


def test_pop_opt():
    assert _pop_opt(["set", "uac", "1.0.0"], "--project-id") == (["set", "uac", "1.0.0"], None)
    assert _pop_opt(["set", "uac", "--project-id", "p", "1.0.0"], "--project-id") == (["set", "uac", "1.0.0"], "p")
    assert _pop_opt(["set", "uac", "--project-id"], "--project-id") == (["set", "uac"], None)  # missing value → None


def test_cli_set_writes(store: dict[str, dict[str, object]], capsys: pytest.CaptureFixture[str]):
    rc = _main(
        ["set", "uac", "0.10.0", "abc123", "--commit-ts", "2026-06-25T10:00:00Z", "--project-id", "p"],
        firestore_module_factory=_factory(store),
    )
    assert rc == 0
    assert store["uac"]["release_tag"]["version"] == "0.10.0"
    assert "repo_state/uac.release_tag: NONE -> 0.10.0" in capsys.readouterr().out


def test_cli_set_emit_transition(store: dict[str, dict[str, object]], capsys: pytest.CaptureFixture[str]):
    rc = _main(["set", "uac", "1.0.0", "sha", "--emit-transition"], firestore_module_factory=_factory(store))
    assert rc == 0
    assert capsys.readouterr().out.strip() == "NONE\t1.0.0"


def test_cli_set_bad_version_raises(store: dict[str, dict[str, object]]):
    with pytest.raises(ValueError, match="non-plain-3-part"):
        _main(["set", "uac", "1.0.0.dev0", "sha"], firestore_module_factory=_factory(store))


def test_cli_set_wrong_arity_is_usage_error(store: dict[str, dict[str, object]], capsys: pytest.CaptureFixture[str]):
    rc = _main(["set", "uac", "1.0.0"], firestore_module_factory=_factory(store))  # missing sha
    assert rc == 2
    assert "usage:" in capsys.readouterr().err


def test_cli_no_verb_is_usage_error(capsys: pytest.CaptureFixture[str]):
    assert _main([]) == 2
    assert "usage:" in capsys.readouterr().err
    assert _main(["bogus"]) == 2


def test_cli_get_map(store: dict[str, dict[str, object]], tmp_path, capsys: pytest.CaptureFixture[str]):
    set_release_version("uac", "1.1.0", "a", firestore_module_factory=_factory(store))  # firestore overlay
    manifest = tmp_path / "workspace-manifest.json"
    manifest.write_text('{"versions": {"uac": "1.0.0", "utl": "0.12.0"}}', encoding="utf-8")
    rc = _main(["get-map", "--manifest", str(manifest)], firestore_module_factory=_factory(store))
    assert rc == 0
    import json as _json

    out = _json.loads(capsys.readouterr().out)
    assert out == {"uac": "1.1.0", "utl": "0.12.0"}  # firestore wins for uac, manifest-only utl retained


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
