---
doc_type: issue
title: UTL assert_no_lookahead_for_feature_group silently no-ops — UAC dropped lst_staking_yields from the DAG SSOT
summary: >-
  unified-trading-library's assert_no_lookahead_for_feature_group() (point_in_time.py) silently skips its lookahead-bias
  check for feature_group="lst_staking_yields" — 5 unit tests in tests/unit/test_point_in_time.py fail ("DID NOT RAISE")
  because UAC's get_required_inputs("lst_staking_yields") now returns [] (the key is no longer registered anywhere in
  unified_api_contracts.canonical.domain.features). Pre-existing red, unrelated to the tradfi/cefi instrument_type
  casing work this was found alongside — filed per worker.md §4.5 findings-closure + the repo- blocker protocol so a
  genuinely unrelated task isn't blocked shipping behind it.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, unified-api-contracts]
scope: [engineer]
tags: [lookahead-bias, point-in-time, feature-dag, ssot-drift, quality-gates, pre-existing-red]
related: []
created: 2026-07-27
priority: P1
parent_epic: infrastructure_master
assigned_vm: planning
source: [tradfi_casing_100pct_redrift_2026_07_27.md]
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: correct-code
depends_on: []
---

## What I found

While running `bash scripts/quality-gates.sh` on `unified-trading-library` for an unrelated task (the tradfi/cefi
`instrument_type` UPPERCASE casing canon, `tradfi_casing_100pct_redrift_2026_07_27.md` item -004), the full pytest run
came back RED with 5 failures, all in `tests/unit/test_point_in_time.py::TestAssertNoLookaheadForFeatureGroup`:

- `test_violation_raises`
- `test_scenario_overlay_active_downgrades_violation_to_warning`
- `test_scenario_overlay_inactive_still_raises_strict`
- `test_label_appears_in_violation_message`
- `test_violation_count_in_message`

All fail with `Failed: DID NOT RAISE <class 'unified_trading_library.point_in_time.LookaheadBiasError'>` (or the
caplog-message variant of the same symptom) — the lookahead-bias check is silently not firing for a genuine violation.

**Verified pre-existing, unrelated to my change**: `git stash`-ed my full diff, confirmed byte-identical failures on a
clean tree at the current `origin/live-defi-rollout` HEAD (both running the full suite and
`tests/unit/test_point_in_time.py` in isolation — not a pytest-xdist test-pollution artifact), then restored my diff. A
prior commit (`9064dd2a`, 2026-07-21) already flagged this exact class as "unrelated pre-existing red" in its own commit
message, so this has been standing for at least several days.

**Root cause**: every failing test uses `feature_group="lst_staking_yields"`. `assert_no_lookahead_for_feature_group()`
(`unified_trading_library/point_in_time.py:283`) calls UAC's `get_required_inputs(feature_group)` and silently returns
(no-op, by design — "feature groups absent here are not unsupported; upstream not yet in AVAILABILITY_AT_SEMANTICS")
whenever the lookup comes back empty:

```python
>>> from unified_api_contracts import get_required_inputs
>>> get_required_inputs("lst_staking_yields")
[]
```

Grepping `unified_api_contracts/canonical/domain/features/required_inputs.py` and `.../registry.py` for `lst_staking` /
`staking_yield` finds **zero matches** — the key isn't registered anywhere in UAC's current DAG SSOT at all (not
renamed-and-findable under a sibling name in those two files; may have been dropped in a UAC refactor, or moved
somewhere neither file covers).

## Why it matters

`assert_no_lookahead_for_feature_group` is a **safety guard against lookahead bias** — exactly the kind of check whose
silent disablement is dangerous precisely because it fails quiet, not loud. Any live caller (if one exists) passing
`feature_group="lst_staking_yields"` today gets ZERO lookahead protection despite the call site looking identical to a
covered one. The `unified-trading-library` quality-gates.sh full suite has been standing RED because of this for at
least since 2026-07-21 (`9064dd2a`), which means every prior slot that ran full QG on this repo either didn't notice,
worked around it locally, or (per `--no-fix`/named-file staging discipline) legitimately never re-ran the FULL suite
once already on this branch.

## Recommended decision

1. Determine in UAC whether `lst_staking_yields` was intentionally dropped (in which case the UTL test file + its
   docstring `Example::` block — both reference this now-dead key — need updating to a currently-registered
   feature_group) or was an unintentional regression during a UAC DAG refactor (in which case UAC needs the entry
   restored, and downstream should audit for any REAL caller passing this feature_group that's currently running with
   zero lookahead protection).
2. Either way, fix `tests/unit/test_point_in_time.py` (repo: unified-trading-library) so the file is green again, and
   confirm no other `FEATURE_REQUIRED_INPUTS`/`get_required_inputs` keys used elsewhere in this test file or in real
   (non-test) UTL/service callers have silently gone the same way.

- [ ] [DATA] P1. Diagnose whether UAC's `lst_staking_yields` DAG-SSOT entry
      (`unified_api_contracts.canonical.domain.features`) was intentionally removed/renamed or is a regression; if
      renamed, identify the new key. (repo: unified-api-contracts)
- [ ] [DATA] P1. Fix `tests/unit/test_point_in_time.py`'s `TestAssertNoLookaheadForFeatureGroup` class (5 failing
      tests) + the `assert_no_lookahead_for_feature_group` docstring `Example::` block to use a currently-registered
      feature_group (or restore `lst_staking_yields` in UAC if todo #1 finds it was an unintentional drop), so
      `bash scripts/quality-gates.sh` is green again. (repo: unified-trading-library)
- [ ] [DATA] P2. Grep unified-trading-library + every service repo for real (non-test) callers of
      `assert_no_lookahead_for_feature_group(...,     feature_group="lst_staking_yields", ...)` — any live caller has
      been running with the lookahead-bias check silently disabled since whenever UAC dropped the key; confirm none
      exist or fix/re-point them. (repo: unified-trading-library and any service found)
