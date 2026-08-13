---
doc_type: issue
title: >-
  pipeline_e2e_check.py enumerate_mtds_shards() silently drops ALL CEFI/SPORTS shards from a combined --mvp-only sweep
  (same root cause as the documented TRADFI base_ccy gap, but with no compensating override)
summary: >-
  Confirmed live (2026-08-06, cefi_mtds_smoke_tester's first-ever run) via direct calls into
  market-tick-data-service/scripts/pipeline_e2e_check.py: enumerate_mtds_shards(asset_group_filter=None, ...,
  mvp_only=True) — i.e. the invocation the /data-pipeline-check-mtds skill documents for a full-matrix smoke sweep —
  returns 2967 shards covering DEFI/PREDICTION/TRADFI only; CEFI and SPORTS contribute ZERO despite both having real MVP
  surfaces (verified: is_mvp(asset_group='cefi', venue='DERIBIT', instrument_type='OPTION', data_type='options_chain')
  is False with no base_ccy, True with base_ccy='BTC' — the exact same class of gap the existing _TRADFI_MVP_SHARDS
  comment already documents for TRADFI, just never extended to CEFI/SPORTS). The function's own "last-resort fallback"
  to smoke_matrix.py (which enumerates correctly) only fires when the ENTIRE accumulated `shards` list is empty across
  all asset groups processed in that call — so when DEFI/PREDICTION/TRADFI contribute non-empty results, the combined
  list is truthy and the fallback never triggers for CEFI/SPORTS specifically, silently masking the gap. Calling
  enumerate_mtds_shards('CEFI', ...) or ('SPORTS', ...) ALONE correctly returns non-empty (225 / 110 shards
  respectively) because the fallback DOES trigger when that single asset_group's own list is empty. Net effect: any
  operator/skill invocation of pipeline_e2e_check.py WITHOUT an explicit --asset-group filter (the documented "sweep the
  whole MVP matrix under one day" mode that cefi_mtds_smoke_tester.md explicitly relies on) silently proves zero cefi
  and zero sports coverage while reporting apparently-clean results for the other 3 groups — a false-negative-shaped gap
  in the tool whose entire job is proving pipeline correctness. Workaround used this run: invoke pipeline_e2e_check.py
  once per --asset-group explicitly (which correctly engages the smoke_matrix.py fallback for CEFI/SPORTS) rather than a
  single unfiltered invocation.
status: resolved
nature: issue
asset_group: [cefi, sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [data-correctness, mvp-scope, is_mvp, pipeline-e2e-check, cefi, sports, false-negative, smoke-test]
related:
  [
    plans/active/issues/mtds_qg_red_combined_coverage_shortfall_2026_08_05.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: 2026-08-06
author: cefi_mtds_smoke_tester (agt-e76dc5, slot 6)
last_updated: 2026-08-06
source: cefi_mtds_smoke_tester
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data-pipeline
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    market-tick-data-service/scripts/pipeline_e2e_check.py,
    market-tick-data-service/scripts/smoke_matrix.py,
    unified-trading-pm/cursor-configs/skills/data-pipeline-check-mtds/SKILL.md,
    unified-trading-pm/agents/cefi_mtds_smoke_tester.md,
    /plans/archive/issues/mtds_qg_red_combined_coverage_shortfall_2026_08_05.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
---

# pipeline_e2e_check.py enumerate_mtds_shards() silently drops CEFI/SPORTS from a combined sweep

> **🗄️ ARCHIVED 2026-08-13** — the one todo is `[x]`, zero remaining, `locked_by:` empty. Per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`, a doc with every todo done archives
> immediately.

## What I found

Dispatched as the first-ever run of the `cefi_mtds_smoke_tester` role (day=2026-08-05), I read
`cursor-configs/skills/data-pipeline-check-mtds/SKILL.md` §3's documented full-matrix invocation and, before spending
real VM budget, sanity-checked `enumerate_mtds_shards()` (the shared enumeration `pipeline_e2e_check.py` calls whenever
`--asset-group` is omitted — exactly the mode this role's own boot contract requires, since the skill "sweeps the whole
MVP matrix under one day").

```python
from pipeline_e2e_check import enumerate_mtds_shards, VENUES_BY_ASSET_GROUP
print(list(VENUES_BY_ASSET_GROUP.keys()))          # ['cefi', 'tradfi', 'defi', 'sports', 'prediction']
shards = enumerate_mtds_shards(None, None, None, True, False)   # mvp_only=True, no filter
print(set(s.asset_group for s in shards), len(shards))
# -> {'PREDICTION', 'TRADFI', 'DEFI'} 2967        <-- CEFI, SPORTS: zero shards, zero mention
```

```python
# same is_mvp() call the enumerator makes internally, isolated:
is_mvp(asset_group='cefi', venue='DERIBIT', instrument_type='OPTION', data_type='options_chain')              # False
is_mvp(asset_group='cefi', venue='DERIBIT', instrument_type='OPTION', data_type='options_chain', base_ccy='BTC')  # True
is_mvp(asset_group='cefi', venue='BINANCE-FUTURES', instrument_type='PERPETUAL', data_type='derivative_ticker')             # False
is_mvp(asset_group='cefi', venue='BINANCE-FUTURES', instrument_type='PERPETUAL', data_type='derivative_ticker', base_ccy='BTC')  # True
```

```python
# filtered to ONE asset_group at a time, the fallback correctly engages:
enumerate_mtds_shards('CEFI', None, None, True, False)     # -> 225 shards (via smoke_matrix.py fallback)
enumerate_mtds_shards('SPORTS', None, None, True, False)   # -> 110 shards (via smoke_matrix.py fallback)
```

## Root cause

Two separate, compounding defects in `market-tick-data-service/scripts/pipeline_e2e_check.py`:

1. **`_venue_data_type_is_mvp()` (line ~494) has no CEFI/SPORTS override.** For TRADFI it already hand-lists
   `_TRADFI_MVP_SHARDS` (line ~308) specifically because the docstring-comment there explains `is_mvp()` needs a
   `base_ccy` this enumeration-time probe can't supply yet (sampling happens later, per-day). The exact same
   dependency-ordering problem applies to CEFI (needs `base_ccy` for OPTION/PERPETUAL cells — verified above) and almost
   certainly SPORTS (needs `league`, per `is_mvp()`'s own kwarg surface) — but neither group got the
   hand-listed-override treatment TRADFI did, so `_venue_data_type_is_mvp('CEFI'|'SPORTS', ...)` returns `False`
   unconditionally today.
2. **The "last-resort fallback" (line ~688, `if shards: return shards`) is gated on the AGGREGATE list across every
   asset_group processed in that call, not per-asset_group.** When `asset_group_filter=None` (sweep-everything mode),
   the loop processes cefi/tradfi/defi/sports/prediction in one pass; DEFI/PREDICTION/TRADFI's hand-listed/working paths
   contribute 2967 real entries, so `shards` is truthy overall and the function returns immediately — the
   `smoke_matrix.enumerate_cells()` fallback (which DOES correctly enumerate CEFI/SPORTS, as proven by the
   single-asset-group calls above) never runs. Defect 1 alone would be a same-shape-as-TRADFI gap that's at least
   self-evident when you filter to `--asset-group CEFI` (you'd see 0 and investigate); defect 2 is what makes it
   INVISIBLE in exactly the mode the skill documents as the default full sweep — the run "succeeds" with 2967
   apparently-real shards and simply never mentions cefi/sports at all.

## Why this matters

`cefi_mtds_smoke_tester.md` (this role) exists specifically because the operator asked for a **daily cefi smoke test**,
and the role file is explicit that it relies on the skill's own whole-matrix sweep to get that coverage ("the skill
itself has no `--asset-group` filter — it sweeps the whole MVP matrix under one day... this role's whole reason to
exist, even though the skill itself is asset-group-agnostic"). Per this defect, that reliance is currently **false**: a
literal follow of SKILL.md §3's documented command (omit `--asset-group`, rely on the matrix) proves **zero** cefi
shards while looking superficially complete (2967 total, spread across 3 other groups, no error/warning surfaced to the
operator or the written report — the `logger.warning` for the fallback path only fires on the PER-CALL empty case, which
never happens here). This is a false-negative-shaped gap in the one tool whose job is catching false negatives.

## Secondary, related observation (not this issue's primary subject — noted for completeness)

DEFI's `--mvp-only` enumeration returns 2958 raw candidate shards = 102 venues × 29 data_types, i.e. every DEFI
(protocol, chain) venue is matched against every DEFI data_type uniformly (e.g. `UNISWAP_V2-ETHEREUM` ×
`lending_indices` / `perp_funding` / `governance_events` — data_types that make no protocol-domain sense for a
spot-AMM). The `_instrument_type_candidates()` docstring-comment explicitly acknowledges this design ("MVP membership is
checked as 'MVP for ANY instrument_type'... a reporting dimension, not a shard key"), so this looks like a known,
accepted over-broad cross-product rather than a new defect — `--require-captured` is the documented mitigation
(unprovable cells are `skipped/no_captured_data_for_cell` before any VM launch). Flagging only so a future DEFI-focused
audit doesn't re-discover it as if new; not requesting action on it here.

## Suggested remediation (either sufficient alone; second is more robust)

- **(a) Minimal, mirrors the existing TRADFI fix shape**: add `_CEFI_MVP_SHARDS` / a SPORTS equivalent (hand-listed
  `(venue, data_type)` pairs, or thread a per-venue representative `base_ccy`/`league` into the enumeration-time probe)
  the same way `_TRADFI_MVP_SHARDS` already does, so `_venue_data_type_is_mvp` stops returning a blanket `False` for
  these two groups.
- **(b) More robust, fixes the masking mechanism itself**: change the fallback to fire **per asset_group** (track which
  groups contributed zero shards from the primary path and only fallback-enumerate THOSE via
  `smoke_matrix.enumerate_cells(asset_group_filter=<that group>)`) instead of gating on the combined list's aggregate
  truthiness. This is the fix that actually closes the "invisible in a combined sweep" failure mode — (a) alone still
  leaves the same masking risk for the NEXT asset_group that acquires an unsupported enumeration-time `is_mvp()`
  dependency.

## Workaround used this run (cefi_mtds_smoke_tester, day=2026-08-05)

Invoked `pipeline_e2e_check.py` once per `--asset-group` explicitly (CEFI, DEFI, TRADFI, SPORTS, PREDICTION) rather than
a single unfiltered call — this correctly engages the `smoke_matrix.py` fallback for CEFI/SPORTS since each single-group
call's own `shards` list is genuinely empty before fallback. This also sidesteps the separately-known report-filename
collision bug (`data_pipeline_e2e_check_mtds_<day>.md`/`.json` gets silently overwritten by each subsequent invocation —
see the 2026-08-02 report's provenance note) by giving each asset_group's invocation its own `--report-dir`, merged by
hand into one combined report afterward.

## Todos

- [x] ✅ [CODE] P1. **ADDED 2026-08-12 (/plan-reconcile, Section 2 zero-checkbox conversion)** — Add `_CEFI_MVP_SHARDS`
      / a SPORTS-equivalent hand-listed override to `market-tick-data-service/scripts/pipeline_e2e_check.py`'s
      `_venue_data_type_is_mvp()` (mirrors the existing `_TRADFI_MVP_SHARDS` shape) so it stops unconditionally
      returning `False` for CEFI/SPORTS venue×data_type cells that need a `base_ccy`/`league` the enumeration-time probe
      can't yet supply — this is the minimal fix (remediation option (a)). The more robust alternative (option (b), not
      required to close this todo but fixes the masking mechanism itself): change the "last-resort fallback" (line ~688)
      to fire per-asset_group instead of gating on the combined `shards` list's aggregate truthiness. Repo:
      market-tick-data-service. — market-tick-data-service@6105f0b0 (already shipped 2026-08-12: adds
      `_CEFI_MVP_SHARDS`/`_SPORTS_MVP_SHARDS` + regression test `tests/unit/test_pipeline_e2e_cefi_sports_mvp.py`).

## Progress Log

- **context-scout 2026-08-07**: populated/refreshed context_scope (6 entries).
- **slot 14, 2026-08-13**: verified live — `enumerate_mtds_shards(None, None, None, True, False)` now returns
  `{CEFI, DEFI, PREDICTION, SPORTS, TRADFI}` (3126 shards total), confirming the fix from
  market-tick-data-service@6105f0b0 closes this todo; that commit had shipped without flipping this checkbox. Flipping
  now; all todos in this doc are done and it carries no `locked_by`, so archiving in a follow-up commit per the
  plan-completion-and-archival HARD RULE.
