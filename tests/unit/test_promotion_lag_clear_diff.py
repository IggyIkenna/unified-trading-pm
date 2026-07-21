"""Unit tests for the per-pair clear-diff in scripts/cicd/promotion_lag_monitor.py.

The promotion-lag all-clear used to be a fleet-wide "any-lag → no-lag" edge: it fired only when
the WHOLE fleet went green and said only "all branch-pairs back in sync" — never naming which
repair cleared, and never announcing one repo clearing while another still lagged. These helpers
persist the lagging SET across runs and diff prev→current so each pair's clear is announced by name
as it lands.

Guards, most-important first:
  * A pair still lagging is NEVER announced as cleared (no false all-clears).
  * A pair whose compare probe FAILED this run (UNMEASURED — a transient gh 403/5xx) is NEVER
    announced cleared; it is carried forward and re-decided on the next successful probe. (This was
    a real regression the per-pair change first introduced — the old fleet-wide edge was immune
    because it required the WHOLE fleet green; adversarial review 2026-07-21, finding "logic/HIGH".)
  * A pair no longer monitored (its repo toggled main-direct / staging-dormant → the direction is
    skipped, absent from repo_lags) is DROPPED, not announced "back in sync".
  * OLD-SCHEMA / absent / corrupt prior state → no prior baseline → no false CLEAR on first run.
  * Each distinct cleared SET gets its own stable dedup key (notify-slack dedups on key alone, so a
    static key would let one clear swallow another within the cooldown).
"""

from __future__ import annotations

import importlib.util
import json
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "cicd" / "promotion_lag_monitor.py"
    spec = importlib.util.spec_from_file_location("promotion_lag_monitor", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PLM = _load_module()


def _lagging(n: int, age_s: float) -> dict[str, object]:
    return {"n_commits": n, "age_s": age_s, "oldest_msg": "x", "lag": True, "provenance_blocked": False}


_IN_SYNC: dict[str, object] = {"lag": False}
_UNMEASURED: dict[str, object] = {"lag": False, "unmeasured": True}


def _rl(pairs: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    """Build a repo_lags map from {"repo|label": <entry dict>} (entry = _lagging(...)/_IN_SYNC/_UNMEASURED)."""
    out: dict[str, dict[str, object]] = {}
    for compound, entry in pairs.items():
        repo, label = compound.split("|", 1)
        out.setdefault(repo, {})[label] = entry
    return out


# ── summaries / evaluated / unmeasured sets ───────────────────────────────────────────────


def test_summaries_only_include_lagging_pairs() -> None:
    rl = _rl({"market-tick-data-service|LDR→main": _lagging(2, 7560.0), "ml-service|LDR→main": _IN_SYNC})
    got = PLM._lagging_summaries(rl)
    assert "market-tick-data-service|LDR→main" in got
    assert "ml-service|LDR→main" not in got  # lag False → excluded
    assert "was 2 commit(s), oldest 126m" in got["market-tick-data-service|LDR→main"]


def test_non_pair_bookkeeping_entry_is_not_a_lagging_or_evaluated_pair() -> None:
    """`staging_backmerge_present` has no `lag` key — never a lagging pair, never 'evaluated'."""
    rl: dict[str, dict[str, object]] = {"instruments-service": {"staging_backmerge_present": {"present": False}}}
    assert PLM._lagging_summaries(rl) == {}
    assert PLM._evaluated_keys(rl) == set()


def test_evaluated_and_unmeasured_sets() -> None:
    rl = _rl(
        {
            "a|LDR→main": _lagging(1, 8000.0),
            "b|LDR→main": _IN_SYNC,
            "c|LDR→main": _UNMEASURED,
        }
    )
    assert PLM._evaluated_keys(rl) == {"a|LDR→main", "b|LDR→main", "c|LDR→main"}
    assert PLM._unmeasured_keys(rl) == {"c|LDR→main"}


# ── the clear decision ────────────────────────────────────────────────────────────────────


def test_clears_only_a_pair_measured_in_sync_this_run() -> None:
    prev = {"a|LDR→main": "a ...", "b|LDR→main": "b ..."}
    rl = _rl({"a|LDR→main": _IN_SYNC, "b|LDR→main": _lagging(1, 8000.0)})
    got = PLM._cleared_keys(prev, PLM._evaluated_keys(rl), set(PLM._lagging_summaries(rl)), PLM._unmeasured_keys(rl))
    assert got == ["a|LDR→main"]  # a measured in-sync → cleared; b still lagging → not


def test_still_lagging_pair_is_never_announced_cleared() -> None:
    """The single most important guard: a pair present in BOTH prev and current-lagging is not a clear."""
    prev = {"market-tick-data-service|LDR→main": "mtds ..."}
    rl = _rl({"market-tick-data-service|LDR→main": _lagging(2, 7560.0)})
    got = PLM._cleared_keys(prev, PLM._evaluated_keys(rl), set(PLM._lagging_summaries(rl)), PLM._unmeasured_keys(rl))
    assert got == []


def test_unmeasured_prev_lagging_pair_is_never_cleared() -> None:
    """A transient compare-API error must NOT read as 'back in sync' for a still-stuck pair (HIGH regression)."""
    prev = {"market-tick-data-service|main→LDR": "mtds main→LDR — was 5 commit(s), oldest 1100m"}
    rl = _rl({"market-tick-data-service|main→LDR": _UNMEASURED})  # probe failed this run
    got = PLM._cleared_keys(prev, PLM._evaluated_keys(rl), set(PLM._lagging_summaries(rl)), PLM._unmeasured_keys(rl))
    assert got == []


def test_unmonitored_pair_is_dropped_not_cleared() -> None:
    """A repo toggled main-direct/staging-dormant → its staging pair is absent → dropped, not 'cleared'."""
    prev = {"svc|LDR→staging": "svc LDR→staging — was 1 commit(s), oldest 200m"}
    rl = _rl({"svc|LDR→main": _IN_SYNC})  # LDR→staging no longer present at all
    got = PLM._cleared_keys(prev, PLM._evaluated_keys(rl), set(PLM._lagging_summaries(rl)), PLM._unmeasured_keys(rl))
    assert got == []


# ── state load / persist ──────────────────────────────────────────────────────────────────


def test_old_schema_prior_state_yields_no_baseline(tmp_path: Path) -> None:
    """A pre-per-pair `{"lag": true}` file must load as {} so the first new run never false-fires."""
    p = tmp_path / "old.json"
    p.write_text(json.dumps({"lag": True}), encoding="utf-8")
    assert PLM._load_lag_state(str(p)) == {}


def test_missing_and_corrupt_state_load_as_empty(tmp_path: Path) -> None:
    assert PLM._load_lag_state(str(tmp_path / "nope.json")) == {}
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert PLM._load_lag_state(str(bad)) == {}


def test_state_roundtrips_new_schema(tmp_path: Path) -> None:
    p = tmp_path / "s.json"
    curr = {"mtds|LDR→main": "mtds — was 2 commit(s), oldest 126m"}
    PLM._write_lag_state(str(p), curr)
    assert PLM._load_lag_state(str(p)) == curr


# ── dedup key + message format ──────────────────────────────────────────────────────────────


def test_dedup_key_is_stable_and_set_scoped() -> None:
    """Same cleared set → same key regardless of order; a different set → a different key."""
    k1 = PLM._cleared_dedup_key(["a|LDR→main", "b|LDR→main"])
    k2 = PLM._cleared_dedup_key(["b|LDR→main", "a|LDR→main"])
    assert k1 == k2 and k1.startswith("promotion-lag-cleared:")
    assert PLM._cleared_dedup_key(["a|LDR→main"]) != k1  # distinct set → distinct lane


def test_cleared_block_names_the_pair_and_carries_key_then_message() -> None:
    prev = {"market-tick-data-service|LDR→main": "market-tick-data-service LDR→main — was 2 commit(s), oldest 126m"}
    block = PLM._build_cleared_block(["market-tick-data-service|LDR→main"], prev, still_lagging=0)
    lines = block.splitlines()
    assert lines[0].startswith("promotion-lag-cleared:")  # line 1 = dedup key
    assert "PROMOTION LAG CLEARED" in lines[1]  # line 2 = the Slack message (one physical line)
    assert "market-tick-data-service LDR→main" in lines[1]
    assert "all branch-pairs now in sync" in lines[1]  # still_lagging == 0
    assert r"\n" in lines[1]  # literal backslash-n line breaks for Slack, not real newlines
    assert len(lines) == 2  # message is one physical line


def test_cleared_block_reports_remaining_when_others_still_lag() -> None:
    prev = {"a|LDR→main": "a — was 1 commit(s), oldest 130m"}
    block = PLM._build_cleared_block(["a|LDR→main"], prev, still_lagging=2)
    assert "2 pair(s) still lagging" in block
    assert "all branch-pairs now in sync" not in block


def test_empty_cleared_set_yields_empty_block() -> None:
    assert PLM._build_cleared_block([], {"a|LDR→main": "a ..."}, still_lagging=1) == ""


# ── end-to-end emit ─────────────────────────────────────────────────────────────────────────


def test_emit_clear_diff_writes_state_and_named_clear(tmp_path: Path) -> None:
    """prev had mtds lagging, now it's measured in-sync → named CLEARED written, state emptied."""
    state_in = tmp_path / "prev.json"
    summary = "market-tick-data-service LDR→main — was 2 commit(s), oldest 126m"
    PLM._write_lag_state(str(state_in), {"market-tick-data-service|LDR→main": summary})
    state_out = tmp_path / "next.json"
    cleared_out = tmp_path / "cleared.txt"
    now_lags = _rl({"market-tick-data-service|LDR→main": _IN_SYNC})
    PLM._emit_clear_diff(now_lags, str(state_in), str(state_out), str(cleared_out))
    assert "market-tick-data-service LDR→main" in cleared_out.read_text(encoding="utf-8")
    assert PLM._load_lag_state(str(state_out)) == {}  # nothing lagging now


def test_emit_clear_diff_carries_unmeasured_forward_without_clearing(tmp_path: Path) -> None:
    """A prev-lagging pair unmeasured this run → NO clear posted AND it stays in the persisted state."""
    state_in = tmp_path / "prev.json"
    summary = "market-tick-data-service main→LDR — was 5 commit(s), oldest 1100m"
    PLM._write_lag_state(str(state_in), {"market-tick-data-service|main→LDR": summary})
    state_out = tmp_path / "next.json"
    cleared_out = tmp_path / "cleared.txt"
    now_lags = _rl({"market-tick-data-service|main→LDR": _UNMEASURED})
    PLM._emit_clear_diff(now_lags, str(state_in), str(state_out), str(cleared_out))
    assert cleared_out.read_text(encoding="utf-8") == ""  # no false clear
    # carried forward with its prior summary so the next successful probe decides
    assert PLM._load_lag_state(str(state_out)) == {"market-tick-data-service|main→LDR": summary}


def test_emit_clear_diff_empty_file_when_pair_still_lagging(tmp_path: Path) -> None:
    state_in = tmp_path / "prev.json"
    PLM._write_lag_state(str(state_in), {"a|LDR→main": "a ..."})
    cleared_out = tmp_path / "cleared.txt"
    still = _rl({"a|LDR→main": _lagging(1, 8000.0)})
    PLM._emit_clear_diff(still, str(state_in), str(tmp_path / "n.json"), str(cleared_out))
    assert cleared_out.read_text(encoding="utf-8") == ""  # 0-byte → workflow cleared=false
