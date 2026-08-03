---
doc_type: issue
title:
  Follow-up fixes from the features-service catalogue completeness + smoke-check masking empirical test — a live Baker
  Hughes adapter regression, and 4 calendar vendor adapters entirely unreachable by the family-level smoke check
summary: >-
  `cross_cutting_satellite_ao_dispatch_batch2-002` ran the required per-module catalogue inventory + an empirical
  smoke-check-masking test (real runs, not code-read inference) for the commodity and calendar families. Two concrete,
  actionable findings came out of the empirical run that are follow-up fixes, not part of the audit's own done-when: (1)
  the Baker Hughes rig-count adapter — already fixed once for a URL-scraping issue on 2026-07-27
  (`features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md` Root Cause E) — is broken AGAIN with a
  DIFFERENT symptom (file-format parse failure, not URL resolution), currently causing commodity's fail-closed guard to
  correctly reject every batch day; (2) calendar's `SentimentCalculator` (cryptopanic_adapter, lunarcrush_adapter) and
  `corporate_actions_handler.py` (yfinance_earnings_adapter, polygon_corporate_actions_adapter) are dead code — never
  imported/invoked by `calendar_orchestrator.py`'s batch path or wired into `main.py`'s `_OPERATIONS` map — so these 4
  adapters are entirely outside the `--mode batch` code path the family-level smoke check exercises, meaning a break in
  any of them would NEVER be caught by the smoke check regardless of its pass/fail logic (masking confirmed, via a
  coverage gap rather than a partial-tolerance gap).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [features-service, catalogue, smoke-test, commodity, calendar, adapter-regression, dead-code, coverage-gap]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/archive/issues/features_service_catalogue_completeness_inventory_2026_07_24.md,
    /plans/active/issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md,
    /plans/active/issues/features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md,
    /codex/02-data/feature-formula-versioning.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: advance-code
source: "slot-13, data_engineering, cross_cutting_satellite_ao_dispatch_batch2-002, 2026-08-01"
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# Catalogue-completeness / smoke-masking follow-ups: Baker Hughes regression + calendar dead-code coverage gap

## What I found

### 1. Baker Hughes rig-count adapter — new regression (file-format parse failure)

A real
`python -m features_service.commodity --operation compute --mode batch --start-date 2026-08-01 --end-date 2026-08-01`
run (2026-08-01, this session) logged:

```
WARNING Baker Hughes: unexpected file format
WARNING Data source 'baker_hughes_rig_count' returned empty data for commodity=NG — skipping factor.
ERROR Partial factor coverage for commodity=NG date=2026-08-01: 3/4 factors produced values (1 missing).
```

This adapter (`features_service/commodity/adapters/baker_hughes.py`) was already fixed once
(`features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md` Root Cause E, `features-service` commit
referenced there) for a DIFFERENT symptom — the current-week report URL is resolved dynamically by scraping the
`na-rig-count` landing page instead of a hardcoded (404'd) filename. Manually re-verified the URL-resolution half still
works (landing-page fetch → 200, href correctly parsed: `/static-files/b2ddc731-be64-4b59-9346-f41aa107305f`). The
failure is downstream of that — `openpyxl` (or the format-sniffing before it) rejects the downloaded file's content,
i.e. Baker Hughes has again changed what it serves at that URL (or serves an inconsistent format intermittently). Not
root-caused further this session (scope: audit + masking test, not adapter repair).

### 2. Calendar: 4 vendor adapters are dead code, entirely outside the family-level smoke check's coverage

Per the task's part (a) module table (below), calendar's registry only covers 4 feature groups (`time_features`,
`economic_events`, `yield_curve`, `economic_results`), matching exactly the 4 calculators `calendar_orchestrator.py`
actually imports (`TemporalFeatures`, `EconomicCalendarLoader`, `YieldCurveCalculator`, `EconomicResultsCalculator`).
Grepping the full `calendar/` package for the OTHER declared calculator (`SentimentCalculator`, which wraps
`cryptopanic_adapter.py` + `lunarcrush_adapter.py`) and the OTHER CLI handler (`corporate_actions_handler.py`, which
wraps `yfinance_earnings_adapter.py` + `polygon_corporate_actions_adapter.py`) found:

- `SentimentCalculator` is exported from `engine/calculators/__init__.py` but `calendar_orchestrator.py` never imports
  or calls it (confirmed: zero matches for `Sentiment` in `calendar_orchestrator.py`).
- `corporate_actions_handler.py` (`CorporateActionsModeHandler` or similar) is not referenced ANYWHERE else in the
  `calendar/` package — not in `cli/main.py`'s `_OPERATIONS` map
  (`{"compute": CalendarBatchModeHandler, "economic_results": EconomicResultsModeHandler}`), not imported by any other
  module. It is unreachable dead code.

Since `e2e-testing/scripts/calendar/smoke_matrix.py` only ever invokes `--operation compute --mode batch` (confirmed:
grep of the file shows no other `--operation`/`--mode` value used), and `--mode batch` only reaches the 4 wired
calculators, these 4 adapters (cryptopanic, lunarcrush, yfinance_earnings, polygon_corporate_actions) can NEVER cause
the family-level smoke check to fail, no matter how broken they are — not because the check tolerates their failure, but
because the check's code path never touches them at all. This is a stronger, unconditional form of the "does the
family-level check mask an individual broken adapter" masking risk the parent task asked to test — confirmed for these
4, distinct from the (correctly fail-closed, refuted) case for the 6 adapters actually wired into calendar's +
commodity's batch paths.

### 3. NEW (found 2026-08-03 verifying the Baker Hughes fix): CL permanently fails factor coverage via `weather_delta`

Re-running
`python -m features_service.commodity --operation compute --mode batch --start-date 2026-08-01 --end-date 2026-08-01`
after the Baker Hughes fix (todo 1) landed: NG now gets full factor coverage, but CL still fails —
`WARNING Data source 'open_meteo_degree_days' returned empty data for commodity=CL — skipping factor.` then
`ERROR Partial factor coverage for commodity=CL date=2026-08-01: 3/4 factors produced values (1 missing)`.

This is NOT flaky/transient like the Baker Hughes bug was — `OpenMeteoDegreeDayAdapter.fetch()`
(`features_service/commodity/adapters/open_meteo.py`) is hardcoded: `if commodity.upper() not in {"NG"}: return {}` (its
own docstring: "Applies to NG; returns {} for unrecognised commodities"). `weather_delta` is in `DEFAULT_FACTOR_GROUPS`
(`features_service/commodity/config.py`), which applies to ALL `enabled_commodities` (`["NG", "CL"]`) with no
per-commodity override actually wired in for CL — the field's own docstring says overrides "live in ConfigStore
CommodityProfile", so either CL's ConfigStore profile was never given a `weather_delta` exclusion, or the per-commodity
override mechanism isn't consulted by `enabled_factor_groups`'s consumers (`batch_handler.py`, `orchestrator.py`,
`live_handler.py` all read the flat `config.enabled_factor_groups`, not a per-commodity resolved list — not fully traced
this session, scope: verification of todo 1, not a new root-cause investigation). Net effect: CL's commodity fail-closed
guard rejects EVERY batch day, permanently, by construction — not because of a live data outage, but because
`weather_delta` can never produce a value for CL. Exactly the same failure SHAPE as this doc's Baker Hughes finding (a
factor-coverage gate silently, permanently unsatisfiable for one commodity), but a different mechanism (structural
commodity-scope mismatch, not a vendor format change) and a different fix surface (ConfigStore data and/or
`enabled_factor_groups` resolution code, not an adapter parser).

## Why it matters

- Baker Hughes: `rig_count` is one of only 4 `DEFAULT_FACTOR_GROUPS` for commodity — its repeated breakage means the
  commodity family's fail-closed design (a genuine correctness feature, see companion masking-test writeup) is currently
  rejecting EVERY commodity batch day, not producing any signal at all, until this is fixed.
- Calendar dead code: either these 4 adapters/calculators are genuinely obsolete (in which case they should be deleted
  per the workspace's no-shims rule) or they represent real intended functionality (sentiment features,
  corporate-actions calendar) that's silently never run in production either — worth an explicit decision either way
  rather than leaving ambiguous half-wired code in the tree.
- CL/`weather_delta`: same class of finding as Baker Hughes (a fail-closed guard permanently, silently rejecting every
  batch day for one commodity) — but CL is BLOCKED on this in a way NG no longer is, so the commodity family is still
  not producing a full signal for CL even after todo 1's fix.

## Recommended decision

- [x] [DATA] P2. ✅ **features-service** — root-cause the Baker Hughes "unexpected file format" failure (fetch the
      current-week file directly, inspect actual bytes/content-type returned, compare against what `openpyxl` expects —
      Baker Hughes may have switched to a `.csv`/different `.xlsx` variant, or the landing-page scrape may now be
      resolving a stale/wrong link under some conditions). Fix + add a regression test pinning the new format (mirroring
      the 2026-07-27 fix's own regression-test pattern in `tests/commodity/unit/test_sources*.py`). **Done when**: a
      real `--mode batch` run for a recent date produces `rig_count` factor values (not "unexpected file format"/skip),
      and `_has_full_factor_coverage` passes for at least one commodity. — **Done 2026-08-03**,
      `features-service@31b66b81`. Root cause confirmed by fetching the live report file directly: Baker Hughes replaced
      the flat single-table report with a multi-sheet workbook (`NAM Summary`/`NAM Breakdown`/`NAM Weekly`/...) that has
      NO gas/oil COLUMN headers at all — gas/oil are now ROW labels inside a `DrillFor` section of the `NAM Breakdown`
      sheet, broken into one block per region (United States, Canada). `_parse_workbook` now tries the legacy flat-table
      shape first (existing tests unchanged), then falls back to summing the DrillFor blocks across regions to get the
      North America total this adapter has always declared as its scope (docstring + the `na-rig-count` source URL) —
      verified against the real fetched file (US gas=127/oil=451, Canada gas=63/oil=150 -> NA gas=190/oil=601) and a
      real `--mode batch --start-date 2026-08-01 --end-date 2026-08-01` run: NG now gets full factor coverage
      (`rig_count` value produced, no "unexpected file format" warning). 2 new regression tests added pinning the new
      shape (`test_parse_workbook_drillfor_breakdown_shape`,
      `test_find_drillfor_breakdown_no_drillfor_section_returns_none`).
- [ ] [SCRIPT] P2. **features-service** — decide + act on calendar's 4 dead-code adapters: EITHER (a) wire
      `SentimentCalculator` into `calendar_orchestrator.py`'s batch path (add `sentiment` to `CALENDAR_FEATURE_GROUPS` +
      the calculator dispatch) and wire `corporate_actions_handler.py`'s mode into `cli/main.py`'s `_OPERATIONS` map
      (mirroring how `economic_results` was wired) so the smoke check actually covers them, OR (b) if genuinely
      obsolete/superseded, delete `sentiment_calculator.py` + `corporate_actions_handler.py` + their 4 adapters entirely
      (no-shims rule) and note the removal in this doc. This is a judgment call the audit itself is not making — file as
      `[OPERATOR]`-gated if the answer isn't obvious from a quick history check (`git log` on
      `sentiment_calculator.py`/`corporate_actions_handler.py` for why they were added and whether anything downstream
      still expects their output).
- [ ] [DATA] P2. **features-service** — root-cause + fix CL's permanent `weather_delta` factor-coverage failure (see
      finding 3 above). Determine why `enabled_factor_groups` isn't narrowed for CL despite `config.py`'s own docstring
      claiming per-commodity overrides live in ConfigStore `CommodityProfile` (trace whether `batch_handler.py` /
      `orchestrator.py` / `live_handler.py` ever resolve a per-commodity list, or always read the flat global default).
      Fix EITHER by wiring a real per-commodity `enabled_factor_groups` override that excludes `weather_delta` for CL,
      OR by giving `DegreeDayFactor`/`weather_delta` a commodity-scoped policy so `_has_full_factor_coverage` doesn't
      count it as "missing" for a commodity the underlying adapter structurally never serves. **Done when**: a real
      `--mode batch` run for a recent date produces full factor coverage for CL (not "Partial factor coverage ... 1
      missing"), and NG's coverage is unaffected. (repo: features-service)

## Progress Log

- 2026-08-01 (slot-13, data_engineering): Filed as the FINDINGS CLOSURE follow-up for
  `cross_cutting_satellite_ao_dispatch_batch2-002`'s empirical smoke-check-masking test. Neither fix applied inline
  (adapter-format root-cause and the wire-vs-delete decision are both outside the audit todo's own done-when).
- 2026-08-03 (slot-6, data_engineering): Closed todo 1 (Baker Hughes), `features-service@31b66b81` — see the todo's own
  entry above for the root-cause + fix detail. While verifying the fix with a real `--mode batch` run, found a second,
  adjacent factor-coverage bug for CL/`weather_delta` (finding 3 + new todo above) — same failure class as Baker Hughes
  but a different mechanism (structural commodity-scope mismatch, not a vendor format change) and a different fix
  surface (ConfigStore data / `enabled_factor_groups` resolution, not an adapter parser); not fixed inline since
  root-causing which layer owns the per-commodity override is itself the open question. Todo 2 (calendar dead-code
  decision) untouched — outside this task's scope.
