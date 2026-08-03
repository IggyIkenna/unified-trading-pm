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
context_scope:
  [
    features-service/features_service/commodity/adapters/baker_hughes.py,
    features-service/features_service/commodity/adapters/open_meteo.py,
    features-service/features_service/commodity/config.py,
    features-service/features_service/calendar/engine/calculators/sentiment_calculator.py,
    /credentials-registry.yaml,
  ]
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
- [x] [SCRIPT] P2. ✅ **features-service** — decide + act on calendar's 4 dead-code adapters. **Split decision, resolved
      2026-08-03** (history check done; `corporate_actions_handler.py` wired, `SentimentCalculator` filed
      `[OPERATOR]`-gated — see reasoning below), `features-service@<pending>`.

      **History check performed** (`git log --follow` on all 4 adapters + both calculators/handlers): all 4 came in
                          wholesale via the 2026-05-08 `feat(calendar): import features-calendar-service into features-service via git
                          subtree` commit (a previously-standalone repo folded in whole) — they are inherited, not purpose-built dead code.
                          Since then, only mechanical repo-wide fixes touched them (lint/`type: ignore`/bucket-migration/basedpyright), no
                          one has done feature work on them specifically. Calendar's own (also-dead, never-consulted)
                          `feature_builder_registry.py` declares `sentiment` + `corporate_actions` as intended feature groups with real
                          column names — showing original design intent to serve both, though that registry itself is unwired so it isn't
                          strong evidence on its own. No downstream consumer (grepped UAC, strategy-service, ml-service) references any of
                          these column names — nothing today depends on their output. Real precedent exists (`4eb5d628`, 2026-07-30) for
                          wiring a similarly-dormant calendar calculator into the batch path when a plan authorizes it (yield_curve +
                          economic_results, converting the `macro_micro_econ_data_capture_audit` issue doc's recommendation into code) — but
                          that same commit shows `economic_results` got a STANDALONE `--operation economic_results` entry point distinct
                          from the per-day `CALENDAR_FEATURE_GROUPS` batch-loop wiring, not just an `_OPERATIONS`-map registration.

                          **Corporate actions (`corporate_actions_handler.py`: `yfinance_earnings_adapter.py` + `polygon_corporate_actions_adapter.py`) — WIRED, option (a).**
                          `run_corporate_actions()` was already a complete, already-tested (`tests/calendar/unit/test_corporate_actions_handler.py`,
                          46 tests, all passing pre- and post-change), standalone `--operation corporate_actions --mode batch` function —
                          it just had no entry in `cli/main.py`'s `operations={}` map, so nothing could ever invoke it (confirmed dead code
                          per the audit). Registered `CorporateActionsModeHandler` (mirrors `EconomicResultsModeHandler`'s wrapper pattern)
                          + a `--tickers` CLI flag, added to `operations={...}`. This is a standalone, separately-invoked operation (like
                          `economic_results`) — its success/failure does NOT affect `--operation compute --mode batch`'s exit code or the
                          family-level smoke check's pass/fail signal, so this was safe to wire regardless of the Polygon credential's live
                          status (unconfirmed — `polygon-api-key` is not tracked in `unified-trading-pm/credentials-registry.yaml` at all;
                          yfinance needs no credential). Verified end-to-end: `python -m features_service.calendar --operation
                          corporate_actions --mode batch --dry-run --tickers AAPL --start-date 2026-08-01 --end-date 2026-08-01` reaches
                          real `app()`/`GCSCalendarStorage` code (fails only on missing `GCP_PROJECT_ID` env in this dev shell — proves the
                          argparse→ServiceBootstrap→handler→app() wiring is genuinely live). **Caveat, not fully closing the masking gap**:
                          this makes `corporate_actions_handler.py` CLI-reachable (fixes "unreachable dead code"), but `smoke_matrix.py`
                          only invokes `--operation compute --mode batch`, which never calls `--operation corporate_actions` — so the
                          family-level smoke check STILL never exercises this code path. Closing that fully would need `corporate_actions`/
                          `earnings_results` genuinely integrated into `CALENDAR_FEATURE_GROUPS`/`process_day()` (ticker-keyed data doesn't
                          fit that per-date calling convention without real integration work) — a separate, larger follow-up, not done here
                          given this todo's scope + the credential uncertainty above.

                          **Sentiment (`sentiment_calculator.py`: `cryptopanic_adapter.py` + `lunarcrush_adapter.py`) — `[OPERATOR]`-gated,
                          NOT wired.** Two concrete, evidence-backed reasons this is a genuine judgment call, not a mechanical one:
                          1. **Confirmed real cost, not provisioned.** `unified-trading-pm/credentials-registry.yaml` lists BOTH
                             `cryptopanic-api-key` and `lunarcrush-api-key` as `status: needs_provisioning` — combined cost estimate
                             $50-250/mo (CryptoPanic's free dev tier referenced in `macro_micro_econ_data_capture_audit_2026_06_05.md`
                             ended 2026-04-01, so it's paid-only now). The registry's own `required_for` field names
                             `features-cross-instrument-service` (news/social sentiment), NOT calendar — grepped `cross_instrument`'s
                             calculators and confirmed no cryptopanic/lunarcrush usage exists there either, so these credentials (even if
                             provisioned) were earmarked for a different, also-unbuilt consumer, not calendar's `SentimentCalculator`
                             specifically. The operator's cost posture on adjacent asks is documented: declined Glassnode Pro (~$999/yr)
                             and CoinGlass (~$299/mo) on 2026-07-29 in the same macro-audit doc — a new $50-250/mo commitment for calendar
                             sentiment is exactly the kind of spend that ruling pattern says needs an explicit operator answer, not a
                             data_engineering worker's unilateral call.
                          2. **Concrete correctness risk if wired without live credentials, not just a budget nicety.** Unlike
                             `corporate_actions`, wiring `sentiment` the way the task originally suggested (`add sentiment to
                             CALENDAR_FEATURE_GROUPS`) ties it into `batch_handler.py`'s per-day loop, which (a) only catches
                             `(ConnectionError, TimeoutError, OSError, ValueError)` per feature-group — the adapters' `RuntimeError(f"Secret
                             '{secret_name}' not found in Secret Manager")` on a missing key is NOT in that tuple, so it would propagate
                             uncaught out of `_process_batch_day`, breaking the whole per-day loop instead of just marking one group
                             failed — and (b) `_log_batch_summary` does `sys.exit(1)` if `total_failed > 0` across ANY feature group, so
                             even a caught failure would make the WHOLE calendar family report failure for EVERY batch day. That is exactly
                             the "fail-closed guard permanently, silently unsatisfiable" bug class this very issue doc documents for Baker
                             Hughes and CL/`weather_delta` (findings 1 + 3 above) — wiring `sentiment` without live credentials would
                             create a THIRD instance of that same bug class, not just leave dead code dead.

                          Follow-up action item tracked as its own todo below (findings-triage: every follow-up is a checkbox, not prose).

- [x] [DATA] P2. ✅ **features-service** — decide calendar's `SentimentCalculator` fate (`cryptopanic_adapter.py` +
      `lunarcrush_adapter.py`). **Operator ruling (2026-08-03): delete** — declines the CryptoPanic + LunarCrush spend
      (~$50-250/mo combined); these are superseded by credentials-registry's stated real intended consumer
      (features-cross-instrument-service's still-unbuilt sentiment features, confirmed not built there either). — **Done
      2026-08-03**, `features-service@c0cbb9b9`. Deleted `sentiment_calculator.py` + `cryptopanic_adapter.py` +
      `lunarcrush_adapter.py` + their unit tests (no-shims rule); cleaned up the now-dangling imports/exports in
      `calendar/adapters/__init__.py` + `calendar/engine/calculators/__init__.py`. Verified (via repo-wide grep) no
      other reference to these modules remains outside the unrelated onchain/cross_instrument sentiment calculators.
      Local Pass-1 `quality-gates.sh` green on the commit; shipped via `quickmerge --agent`, verified on
      `origin/live-defi-rollout`.
- [x] [DATA] P2. ✅ **features-service** — root-cause + fix CL's permanent `weather_delta` factor-coverage failure (see
      finding 3 above). — **Done 2026-08-03**, `features-service@d387ba7f`. Root cause: `DegreeDayFactor.commodity`
      already declares `'NG'` (every other factor declares `'*'`) — `OpenMeteoDegreeDayAdapter.fetch()` is hardcoded to
      return `{}` for any commodity but NG — but `collect_factor_values`/`_has_full_factor_coverage` never consulted
      that per-factor `commodity` scope property, so CL was always counted as "missing" `weather_delta`. The
      `ConfigStore CommodityProfile` mechanism the config docstring referenced does not exist anywhere in the codebase
      (grepped — zero class definitions); it was aspirational documentation, not the actual fix surface. Fix: added
      `factor_applies_to_commodity()`/`applicable_factor_groups()` (reusing the existing per-factor `commodity`
      property) in `engine/factors/__init__.py`, and filter `enabled_factor_groups` through it BEFORE fetching/counting
      in `batch_handler.py._process_day`, `live_handler.py.run_commodity`, and
      `orchestrator.py.compute_commodity_features`. **Done-when verified**: a real
      `--mode batch --start-date 2026-08-01 --end-date 2026-08-01 --dry-run` run now succeeds 2/2 (NG and CL both), no
      "Partial factor coverage" warning for CL, and NG's own weather_delta requirement is unchanged (still 4/4 required,
      confirmed via a new regression test simulating an NG weather_delta outage → day still fails-closed). 5 new
      regression tests added (`test_factors.py::TestApplicableFactorGroups`,
      `test_boost_commodity_handlers.py::test_process_day_cl_weather_delta_not_counted_as_missing` +
      `test_process_day_ng_still_requires_weather_delta`). Local Pass-1 `quality-gates.sh` green (102/102 commodity unit
      tests passing); shipped via `quickmerge --agent`, verified on `origin/live-defi-rollout`. All 4 todos in this
      issue doc are now resolved — doc ready for archival.

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
- 2026-08-03 (slot-13, data_engineering): Closed todo 2 (calendar dead-code decision) as a SPLIT decision, per the
  todo's own "file as [OPERATOR]-gated if not obvious" escape hatch. History check (`git log --follow` on all 4
  adapters + both calculators) showed genuine heterogeneity across the 4, not a clean wire-all-or-delete-all call:
  `corporate_actions_handler.py` (yfinance, free + polygon, cost-unconfirmed) was a complete, already-tested standalone
  operation just missing `cli/main.py` registration — wired it (`CorporateActionsModeHandler`, mirrors
  `EconomicResultsModeHandler`), verified end-to-end via a real CLI invocation reaching `app()`. `SentimentCalculator`
  (cryptopanic + lunarcrush) was NOT wired: both credentials are confirmed `needs_provisioning` in
  `credentials-registry.yaml` (real $50-250/mo, earmarked in that registry for a different, also-unbuilt consumer —
  features-cross-instrument-service, not calendar), AND wiring it into `CALENDAR_FEATURE_GROUPS` without live
  credentials would crash/permanently-fail-close the whole calendar batch (RuntimeError isn't in `_process_batch_day`'s
  caught-exception tuple; `_log_batch_summary` exits 1 on any group failure) — a concrete third instance of this doc's
  own Baker Hughes/CL bug class, not just a budget question. Filed the sentiment decision as its own `[OPERATOR]` todo
  (new todo, findings-triage: checkbox not prose) rather than leaving it as unactioned prose. Explicitly noted the
  corporate_actions wiring does NOT by itself close the smoke-check masking gap (smoke_matrix.py only invokes
  `--operation compute --mode batch`, never `--operation corporate_actions`) — full closure needs
  `CALENDAR_FEATURE_GROUPS`/`process_day()` integration, a separate larger follow-up not attempted here.
- **context-scout 2026-08-03**: populated context_scope (5 entries).
- 2026-08-03 (slot-7, data_engineering): Applied the operator ruling on the `[OPERATOR]` sentiment todo — delete branch.
  `features-service@c0cbb9b9`: deleted `sentiment_calculator.py`, `cryptopanic_adapter.py`, `lunarcrush_adapter.py`, and
  their unit tests; cleaned up the resulting dangling imports/exports in `calendar/adapters/__init__.py` +
  `calendar/engine/calculators/__init__.py`. Left `feature_builder_registry.py`'s `sentiment` entry untouched — it's
  declarative metadata (string source names only, no import of the deleted modules) and already-dead/unwired per this
  doc's own todo-2 history check, outside the operator ruling's stated scope. Credentials-registry entries for
  `cryptopanic-api-key`/`lunarcrush-api-key` also left untouched — they're earmarked for
  features-cross-instrument-service, a different consumer, not calendar. Local `quality-gates.sh` green on the commit;
  shipped via `quickmerge --agent`, verified on `origin/live-defi-rollout`. All 3 substantive todos in this issue doc
  are now resolved (Baker Hughes fix, calendar dead-code split decision, this sentiment ruling); the 4th (CL
  `weather_delta` factor-coverage) remains open — doc stays active.
- 2026-08-03 (slot-13, data_engineering): Closed todo 4 (CL `weather_delta` factor-coverage),
  `features-service@d387ba7f` — see the todo's own entry above for the root-cause + fix detail. Root cause:
  `DegreeDayFactor` already declared its own `commodity` scope (`'NG'`, vs. every other factor's `'*'`) but nothing
  downstream ever read that property before fetching/counting — the fix reuses it rather than inventing a new
  per-commodity mechanism. All 4 todos in this issue doc are now resolved with no `locked_by` set — per this workspace's
  archival-authority boundary (a worker running the 6-step archival ritual outside `plan_reconciler`'s designated
  authority is out of scope, not this task's done_definition), leaving the actual archive move for the next
  `/plan-reconcile` pass rather than doing it here.
