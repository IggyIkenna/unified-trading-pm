"""Regression guard for the content-based breaking-change differ.

scripts/cicd/detect_breaking_change.py is the SSOT public-surface differ wired into
semver-agent.yml. It must classify docstring/reformat/reorder/additive changes as
NON-breaking (the false-positive class that caused spurious cascade locks) and real
public-API/schema-surface removals/incompatible-changes as breaking.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "detect_breaking_change.py"
_spec = importlib.util.spec_from_file_location("detect_breaking_change", _SCRIPT)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules["detect_breaking_change"] = _mod
_spec.loader.exec_module(_mod)

extract_surface = _mod.extract_surface
diff_surfaces = _mod.diff_surfaces
registry_value_changes = _mod.registry_value_changes
source_touched = _mod._source_touched


BASE = '''
__all__ = ["foo", "Bar", "keep"]
def foo(a, b, c=1):
    """original docstring"""
    return a
class Bar:
    x: int
    name: str
    def method(self, p): ...
def keep(): ...
'''


def _is_breaking(new_src: str) -> tuple[bool, list[str]]:
    old = extract_surface(BASE, "m")
    new = extract_surface(new_src, "m")
    reasons = diff_surfaces(old, new)
    return bool(reasons), reasons


def test_docstring_reformat_reorder_is_not_breaking():
    """The false-positive class the old `grep '^-'` heuristic flagged."""
    src = '''
__all__ = ["keep", "Bar", "foo"]
def foo(a, b, c=1):
    """COMPLETELY rewritten docstring with examples"""
    # added internal comment
    result = a
    return result
class Bar:
    x: int
    name: str
    def method(self, p):
        return p
def keep(): ...
'''
    breaking, reasons = _is_breaking(src)
    assert not breaking, reasons


def test_removed_export_is_breaking():
    src = """
__all__ = ["foo", "Bar"]
def foo(a, b, c=1): return a
class Bar:
    x: int
    name: str
    def method(self, p): ...
"""
    breaking, reasons = _is_breaking(src)
    assert breaking
    assert any("keep" in r for r in reasons)


def test_removed_underscore_name_from_all_is_not_breaking():
    """A by-convention-private (``_``-prefixed) name listed in __all__ is an internal-but-
    cross-module-shared constant, NOT public cross-repo API; removing it must NOT be flagged
    breaking. Regression: the instruments-service venue-producer consolidation removed
    ``_CEFI_VENUES``/``_TRADFI_VENUES`` (both in __all__), which the differ wrongly read as a
    removed public export → false 'breaking' → stuck on the LDR→main label-check + SIT gate.
    """
    old = extract_surface(
        '__all__ = ["foo", "_CEFI_VENUES", "_TRADFI_VENUES"]\ndef foo(): ...\n_CEFI_VENUES = []\n_TRADFI_VENUES = []\n',
        "m",
    )
    new = extract_surface('__all__ = ["foo"]\ndef foo(): ...\n', "m")
    reasons = diff_surfaces(old, new)
    assert not reasons, reasons


def test_added_required_param_is_breaking():
    src = """
__all__ = ["foo", "Bar", "keep"]
def foo(a, b, required_new, c=1): return a
class Bar:
    x: int
    name: str
    def method(self, p): ...
def keep(): ...
"""
    breaking, reasons = _is_breaking(src)
    assert breaking
    assert any("required" in r for r in reasons)


def test_added_optional_param_is_not_breaking():
    src = """
__all__ = ["foo", "Bar", "keep"]
def foo(a, b, c=1, d=2): return a
class Bar:
    x: int
    name: str
    def method(self, p): ...
def keep(): ...
"""
    breaking, reasons = _is_breaking(src)
    assert not breaking, reasons


def test_removed_schema_field_is_breaking():
    src = """
__all__ = ["foo", "Bar", "keep"]
def foo(a, b, c=1): return a
class Bar:
    x: int
    def method(self, p): ...
def keep(): ...
"""
    breaking, reasons = _is_breaking(src)
    assert breaking
    assert any("name" in r and "field" in r for r in reasons)


def test_changed_field_type_is_breaking():
    src = """
__all__ = ["foo", "Bar", "keep"]
def foo(a, b, c=1): return a
class Bar:
    x: str
    name: str
    def method(self, p): ...
def keep(): ...
"""
    breaking, reasons = _is_breaking(src)
    assert breaking
    assert any("field type" in r for r in reasons)


def test_added_export_and_field_is_not_breaking():
    src = """
__all__ = ["foo", "Bar", "keep", "NEW"]
def foo(a, b, c=1): return a
class Bar:
    x: int
    name: str
    added: float
    def method(self, p): ...
def keep(): ...
def NEW(): ...
"""
    breaking, reasons = _is_breaking(src)
    assert not breaking, reasons


def test_removed_http_route_is_breaking():
    base = """
class Api:
    @router.get("/health")
    def health(self): ...
    @router.post("/orders")
    def orders(self): ...
"""
    new = """
class Api:
    @router.get("/health")
    def health(self): ...
"""
    reasons = diff_surfaces(extract_surface(base, "m"), extract_surface(new, "m"))
    assert reasons
    assert any("route" in r for r in reasons)


def test_removed_enum_member_is_breaking():
    # Enum members are a contract surface (consumers match on them) — removing one is breaking,
    # even though it's a plain (non-annotated) assignment. (Phase 4, dependency_promotion plan.)
    base = """
class DefiErrorCode(StrEnum):
    AAVE_HEALTH_FACTOR = "aave_hf"
    ORACLE_STALE = "oracle_stale"
"""
    new = """
class DefiErrorCode(StrEnum):
    AAVE_HEALTH_FACTOR = "aave_hf"
"""
    reasons = diff_surfaces(extract_surface(base, "m"), extract_surface(new, "m"))
    assert reasons
    assert any("ORACLE_STALE" in r for r in reasons)


def test_changed_enum_member_value_is_breaking():
    # The serialized value IS the contract for a StrEnum — changing it breaks consumers.
    base = """
class Source(StrEnum):
    DATABENTO = "databento"
"""
    new = """
class Source(StrEnum):
    DATABENTO = "databento_v2"
"""
    reasons = diff_surfaces(extract_surface(base, "m"), extract_surface(new, "m"))
    assert reasons
    assert any("DATABENTO" in r for r in reasons)


def test_added_enum_member_is_not_breaking():
    # Adding a member is additive — consumers that don't know it are unaffected.
    base = """
class Source(StrEnum):
    DATABENTO = "databento"
"""
    new = """
class Source(StrEnum):
    DATABENTO = "databento"
    MASSIVE = "massive"
"""
    reasons = diff_surfaces(extract_surface(base, "m"), extract_surface(new, "m"))
    assert not reasons, reasons


def test_plain_class_constant_change_is_not_enum_tracked():
    # A non-Enum class's plain constant is NOT a contract surface — changing it must NOT flag
    # (only Enum members are tracked; otherwise every internal constant tweak would trip SIT).
    base = """
class Config:
    DEFAULT_TIMEOUT = 30
"""
    new = """
class Config:
    DEFAULT_TIMEOUT = 60
"""
    reasons = diff_surfaces(extract_surface(base, "m"), extract_surface(new, "m"))
    assert not reasons, reasons


def test_module_to_package_move_preserves_surface_is_not_breaking():
    """Incident 2026-06-09 (UAC 0.5.0 spurious breaking-cascade regression guard).

    Deleting a DEPRECATED re-export SHIM module (``from .real import *``) while a sibling
    package provides the same public names must classify NON-breaking. A star-import
    contributes no parseable exports, and the differ keys exports by BARE name across the
    MERGED surface, so a name still exported anywhere is never counted as "removed". (The
    actual root cause of that incident was the semver-agent's baseline-commit resolution, not
    the differ — but this locks in the differ's correct module->package behaviour so a future
    coarsening can't re-introduce the false positive.)
    """
    merge = _mod.merge
    # OLD: package __init__ exports {A, B}; a deprecated shim module star-imports (no exports).
    old = merge(
        extract_surface('__all__ = ["A", "B"]\nclass A: ...\nclass B: ...', "pkg"),
        extract_surface("from .real import *  # deprecated compat shim", "pkg.validation.instruction"),
    )
    # NEW: shim module deleted; __init__ unchanged; a new sub-package provides the same names.
    new = merge(
        extract_surface('__all__ = ["A", "B"]\nclass A: ...\nclass B: ...', "pkg"),
        extract_surface("class A: ...\nclass B: ...", "pkg.validation.instruction"),
    )
    reasons = diff_surfaces(old, new)
    assert not reasons, reasons


def test_untagged_registry_dict_member_removal_is_not_tracked():
    """A plain module-level dict WITHOUT the ``# @contract-surface`` marker is NOT
    diffed at the literal level — only opted-in constants get this treatment (the
    marker-gating itself, not just the diff mechanics)."""
    base = """
CONFIG: dict[str, set[str]] = {
    "OKX": {"SPOT_PAIR", "PERPETUAL"},
}
"""
    new = """
CONFIG: dict[str, set[str]] = {
    "OKX": {"PERPETUAL"},
}
"""
    reasons = diff_surfaces(extract_surface(base, "m"), extract_surface(new, "m"))
    assert not reasons, reasons


def test_contract_surface_removed_set_member_is_breaking_23fa3a99_regression():
    """Regression fixture for `unified-api-contracts@23fa3a99` (2026-07-07): removing
    "SPOT_PAIR" from the bare "OKX" key of `INSTRUMENT_TYPES_BY_VENUE` silently broke
    instruments-service's `build_expected('cefi')` (75->71 tuples) with the OLD differ
    reporting `is_breaking: false` (name stayed exported, annotation unchanged) — the
    exact gap this `# @contract-surface` marker + registry diff closes. See
    plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md.
    """
    base = """
OKX_SPOT = "OKX-SPOT"
OKX_FUTURES = "OKX-FUTURES"
# @contract-surface
INSTRUMENT_TYPES_BY_VENUE: dict[str, set[str]] = {
    OKX_SPOT: {"SPOT_PAIR"},
    OKX_FUTURES: {"PERPETUAL", "FUTURE", "OPTION"},
    "OKX": {"SPOT_PAIR", "PERPETUAL", "FUTURE", "OPTION"},
    "BYBIT": {"SPOT_PAIR", "PERPETUAL", "FUTURE"},
}
"""
    new = """
OKX_SPOT = "OKX-SPOT"
OKX_FUTURES = "OKX-FUTURES"
# @contract-surface
INSTRUMENT_TYPES_BY_VENUE: dict[str, set[str]] = {
    OKX_SPOT: {"SPOT_PAIR"},
    OKX_FUTURES: {"PERPETUAL", "FUTURE", "OPTION"},
    "OKX": {"PERPETUAL", "FUTURE", "OPTION"},
    "BYBIT": {"PERPETUAL", "FUTURE"},
}
"""
    reasons = diff_surfaces(extract_surface(base, "m"), extract_surface(new, "m"))
    assert reasons
    assert any("SPOT_PAIR" in r and "OKX" in r for r in reasons)
    assert any("SPOT_PAIR" in r and "BYBIT" in r for r in reasons)


def test_contract_surface_added_set_member_is_not_breaking():
    base = """
# @contract-surface
INSTRUMENT_TYPES_BY_VENUE: dict[str, set[str]] = {
    "OKX": {"PERPETUAL"},
}
"""
    new = """
# @contract-surface
INSTRUMENT_TYPES_BY_VENUE: dict[str, set[str]] = {
    "OKX": {"PERPETUAL", "FUTURE"},
    "NEWVENUE": {"SPOT_PAIR"},
}
"""
    reasons = diff_surfaces(extract_surface(base, "m"), extract_surface(new, "m"))
    assert not reasons, reasons


def test_contract_surface_removed_top_level_key_is_breaking():
    """VENUES_BY_ASSET_GROUP shape (dict[str, list[str]]) — an asset_group entirely
    disappearing, or a venue dropped from its list, is breaking."""
    base = """
# @contract-surface
VENUES_BY_ASSET_GROUP: dict[str, list[str]] = {
    "cefi": ["BINANCE-SPOT", "OKX"],
    "tradfi": ["NASDAQ"],
}
"""
    new = """
# @contract-surface
VENUES_BY_ASSET_GROUP: dict[str, list[str]] = {
    "cefi": ["BINANCE-SPOT"],
}
"""
    reasons = diff_surfaces(extract_surface(base, "m"), extract_surface(new, "m"))
    assert reasons
    assert any("tradfi" in r and "removed key" in r for r in reasons)
    assert any("OKX" in r and "removed member" in r for r in reasons)


def test_contract_surface_removed_capability_inner_key_is_breaking():
    """VENUE_DATA_TYPE_CAPABILITIES shape (dict[str, dict[str, str]]) — a venue losing
    a data_type capability entry is breaking; the start-date VALUE changing is not."""
    base = """
# @contract-surface
VENUE_DATA_TYPE_CAPABILITIES: dict[str, dict[str, str]] = {
    "DERIBIT": {"trades": "2019-03-30", "options_chain": "2019-03-30"},
}
"""
    new = """
# @contract-surface
VENUE_DATA_TYPE_CAPABILITIES: dict[str, dict[str, str]] = {
    "DERIBIT": {"trades": "2020-01-01"},
}
"""
    reasons = diff_surfaces(extract_surface(base, "m"), extract_surface(new, "m"))
    assert reasons
    assert any("options_chain" in r for r in reasons)
    # the start-date VALUE change (trades: 2019-03-30 -> 2020-01-01) is NOT itself
    # flagged — only structural key removal is tracked for this shape.
    assert not any("2019-03-30" in r or "2020-01-01" in r for r in reasons)


def test_contract_surface_unresolvable_value_is_dropped_not_crashed():
    """A per-key value the differ cannot statically resolve (a computed expression,
    e.g. `VENUES_BY_ASSET_GROUP["defi"]`'s `list(dict.fromkeys(...))`) is DROPPED from
    the tracked snapshot rather than aborting the whole constant or crashing — every
    other, literal key in the same dict stays diffable."""
    src = """
_LIVE = ["AAVE_V3"]
# @contract-surface
VENUES_BY_ASSET_GROUP: dict[str, list[str]] = {
    "cefi": ["BINANCE-SPOT"],
    "defi": list(dict.fromkeys(v for v in _LIVE)),
}
"""
    surf = extract_surface(src, "m")
    assert surf.registry["VENUES_BY_ASSET_GROUP"] == {"cefi": ["BINANCE-SPOT"]}


def test_registry_value_removal_is_decoupled_from_is_breaking():
    """uac_value_only_config_change_breaks_utl_untested_2026_07_20.md instance 1:
    `massive` removed from tradfi SOURCE_PRIORITY. The decoupled signal must catch it;
    `is_breaking` (`diff_surfaces`) must NOT — the export name + shape are unchanged."""
    base = """
SOURCE_PRIORITY: dict[tuple[str, str], list[str]] = {
    ("tradfi", "ohlcv_15m"): ["databento", "yahoo"],
    ("tradfi", "trades"): ["databento", "massive"],
}
"""
    new = """
SOURCE_PRIORITY: dict[tuple[str, str], list[str]] = {
    ("tradfi", "ohlcv_15m"): ["databento", "yahoo"],
    ("tradfi", "trades"): ["databento"],
}
"""
    old_surf = extract_surface(base, "m")
    new_surf = extract_surface(new, "m")
    assert not diff_surfaces(old_surf, new_surf)
    assert registry_value_changes(old_surf, new_surf) == ["SOURCE_PRIORITY"]


def test_registry_value_dict_key_reorder_is_not_flagged():
    """Order-normalizing canonicalizer: a pure dict-key reorder is not a value change."""
    base = """
VENUE_TO_ADAPTER_KEY: dict[str, str] = {
    "BINANCE-SPOT": "binance",
    "OKX-SPOT": "okx",
}
"""
    new = """
VENUE_TO_ADAPTER_KEY: dict[str, str] = {
    "OKX-SPOT": "okx",
    "BINANCE-SPOT": "binance",
}
"""
    old_surf = extract_surface(base, "m")
    new_surf = extract_surface(new, "m")
    assert registry_value_changes(old_surf, new_surf) == []


def test_registry_value_priority_list_reorder_is_flagged():
    """List order IS preserved: reordering a priority list is itself a behavior change,
    unlike a dict-key reorder above."""
    base = """
SOURCE_PRIORITY: dict[tuple[str, str], list[str]] = {
    ("tradfi", "trades"): ["databento", "yahoo"],
}
"""
    new = """
SOURCE_PRIORITY: dict[tuple[str, str], list[str]] = {
    ("tradfi", "trades"): ["yahoo", "databento"],
}
"""
    old_surf = extract_surface(base, "m")
    new_surf = extract_surface(new, "m")
    assert registry_value_changes(old_surf, new_surf) == ["SOURCE_PRIORITY"]


def test_registry_value_unchanged_is_not_flagged():
    src = """
VENUE_TO_ADAPTER_KEY: dict[str, str] = {
    "BINANCE-SPOT": "binance",
}
"""
    surf = extract_surface(src, "m")
    assert registry_value_changes(surf, surf) == []


def test_non_allowlisted_constant_value_change_is_not_tracked():
    """A plain constant NOT in CROSS_REPO_REGISTRY_ALLOWLIST (e.g. a benign
    recalibration like EMISSION_LATENCY_MS_BY_SOURCE) gets neither is_breaking NOR the
    decoupled signal — this differ only tracks the narrow, explicit allowlist."""
    base = "EMISSION_LATENCY_MS_BY_SOURCE: dict[str, int] = {'yahoo': 900_000}\n"
    new = "EMISSION_LATENCY_MS_BY_SOURCE: dict[str, int] = {'yahoo': 840_000}\n"
    old_surf = extract_surface(base, "m")
    new_surf = extract_surface(new, "m")
    assert not diff_surfaces(old_surf, new_surf)
    assert registry_value_changes(old_surf, new_surf) == []


# ── source_touched: the squash-promote patch-fallback signal ────────────────────────
# Regression coverage for semver_agent_squash_promote_loses_commit_type_never_bumps_2026_08_09
# (the live incident: unified-trading-library@609299ad squashed into e94be221 -- BASELINE..HEAD
# was a single `chore(promote): LDR -> main` commit, so semver-agent's message-based feat:/fix:
# scan matched nothing, and old_export_count==new_export_count so the AST differ's own
# net-new-export fallback didn't fire either -- BUMP="" silently skipped a real internal fix).
# `_source_touched` is the content-based signal semver-agent.yml's patch-level fallback now
# keys off of instead: any non-metadata file changed in the range -> patch, closing the gap
# without needing the squash commit's subject to carry a conventional-commit prefix.


def _init_git_repo(repo_dir: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True)


def _git_commit(repo_dir: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo_dir, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_dir, text=True).strip()


def test_source_touched_true_on_squash_only_commit_range_with_real_source_change(tmp_path, monkeypatch):
    """The live-incident shape: BASELINE..HEAD is a single squash-promote commit whose
    SUBJECT carries no feat:/fix: prefix, but its content touches real package source --
    source_touched must be True so the patch-level fallback fires instead of silently
    skipping the release."""
    _init_git_repo(tmp_path)
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "mod.py").write_text("def f():\n    return 1\n")
    baseline = _git_commit(tmp_path, "chore: baseline")

    (pkg / "mod.py").write_text("def f():\n    return 2  # retry-path fix\n")
    head = _git_commit(tmp_path, "chore(promote): LDR → main (Option-B direct)")

    monkeypatch.chdir(tmp_path)
    assert source_touched(baseline, head) is True


def test_source_touched_false_on_squash_commit_touching_only_metadata_noise(tmp_path, monkeypatch):
    """A squash commit whose ONLY changes are CI/docs/lockfile noise (the
    `_NON_FUNCTIONAL_PATH_RE` denylist) must stay source_touched=False -- matching the
    documented `chore:/docs: -> no bump` rule; the patch-fallback must not fire on pure
    metadata churn even when it is the sole commit in a squash-promote range."""
    _init_git_repo(tmp_path)
    (tmp_path / "README.md").write_text("v1\n")
    (tmp_path / "uv.lock").write_text("# lock v1\n")
    baseline = _git_commit(tmp_path, "chore: baseline")

    (tmp_path / "README.md").write_text("v2\n")
    (tmp_path / "uv.lock").write_text("# lock v2\n")
    head = _git_commit(tmp_path, "chore(promote): LDR → main (Option-B direct)")

    monkeypatch.chdir(tmp_path)
    assert source_touched(baseline, head) is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
