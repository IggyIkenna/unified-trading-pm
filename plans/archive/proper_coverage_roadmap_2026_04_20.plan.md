---
doc_type: plan
title: proper-coverage-roadmap
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    instruments-service,
    market-tick-data-service,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-20"
overview:
  How to reach ~100% honest coverage per category for instruments-service / MTDS / MDPS — the operational sequence that
  lights up every cell of the Data Status heatmap.
type: ops
epic: epic-data-platform-honest-coverage
locked_by: live-defi-rollout
locked_since: 2026-04-20
completion_gates: { code: C5, deployment: D3, business: B3 }
depends_on: [honest_coverage_metrics_2026_04_19]
todos:
  - {
      id: phase-1-instruments-deferred,
      content:
        "- [ ] [AGENT] P0. Finish instruments-service Phase B deferred items: Polymarket\n  per-market loop in
        engine/orchestrator.py:1660-1687, Kalshi inlined paths,\n  SFI per-fixture entities (fixture-stats / odds /
        lineups), patch_prediction_shards.py,\n  rescan_prediction_v4.py. Each must call writer.record_empty /
        record_failed\n  consistently; tests in tests/unit/test_orchestrator_*_capture_status.py.\n",
      status: todo,
    }
  - {
      id: phase-1-cross-cat-audit,
      content:
        "- [ ] [AGENT] P0. Cross-category audit of every ManifestWriter call site in\n  instruments-service / MTDS /
        MDPS / features-* — confirm record_empty vs\n  record_failed routing matches the underlying success/failure
        state per the\n  Bug B fix pattern in MTDS bc33700. Document any remaining mis-classifications\n  in this plan.
        Update MEMORY.md if a new pattern is discovered.\n",
      status: todo,
    }
  - {
      id: phase-2-prediction-backfill,
      content:
        "- [ ] [SCRIPT] P0. PREDICTION full-history backfill via launch-mtds-prediction-backfill-vm.sh.\n  Range:
        2025-03-14 (Polymarket CLOB cutover) → today. Single VM at a time\n  (singleton lock). Expected outcome: 14000+
        captured rows + ~10x empty_confirmed\n  rows for non-trading conditionIds. Triggers PREDICTION attempt_coverage
        23%→~99%.\n",
      status: todo,
      note: "Estimated wall time: 4-12 hours single VM, depending on conditionId universe size.",
    }
  - {
      id: phase-2-cefi-backfill,
      content:
        "- [ ] [SCRIPT] P1. CEFI sharded backfill via launch-cefi-sharded-backfill.sh.\n  Already partly executed (per
        MEMORY.md). Confirm all year × venue × heavy/light\n  shards have completed; manually re-fire any shard with
        VM_STATUS != COMPLETED.\n  Track via deployment-ui Data Status page (post Phase C).\n",
      status: todo,
    }
  - {
      id: phase-2-tradfi-backfill,
      content:
        "- [ ] [SCRIPT] P1. TRADFI backfill — CME ES + CBOE VIX 2024-2026, futures + options.\n  Same launcher as CEFI
        (launch-cefi-sharded-backfill.sh handles tradfi).\n  Smaller universe than CEFI; should complete in 1-2 days
        wall time.\n",
      status: todo,
    }
  - {
      id: phase-2-defi-backfill,
      content:
        "- [ ] [SCRIPT] P1. DEFI backfill per chain × protocol. Existing scripts:\n  scripts/full-defi-backfill.sh
        (MTDS) + features-onchain-service backfill via\n  launch-features-backfill-vm.sh DEFI. Validate against
        DEFI_REPOS in\n  create-code-tarballs.sh. Coverage target: every (chain × protocol × date) cell.\n",
      status: todo,
    }
  - {
      id: phase-2-sports-cron-stabilization,
      content:
        "- [ ] [AGENT] P0. Sports cron orchestration: replace whatever is launching\n  10× SFI VMs concurrently (root
        cause of yesterday's thundering herd) with\n  a singleton-respecting scheduler. Singleton lock in launcher
        (968b961) is\n  a bandaid; the orchestration layer needs to stop firing 10 at once. Find\n  the cron / Cloud
        Scheduler / GHA workflow that did this and fix it.\n",
      status: todo,
    }
  - {
      id: phase-2-sports-backfill,
      content:
        "- [ ] [SCRIPT] P1. SPORTS backfill: SFI + footystats + odds-api + Understat\n  + transfermarkt + open_meteo +
        api_football. Each provider has its own\n  launcher (launch-sfi-forward-poll.sh,
        launch-footystats-forward-poll.sh).\n  Backfill window: 2019-01-01 → today (per Phase 5b.3 scope in MDPS
        launcher).\n",
      status: todo,
    }
  - {
      id: phase-3-reconcile-manifests,
      content:
        "- [ ] [SCRIPT] P0. Per-bucket manifest reconciliation pass via UTL
        helper:\n  unified_trading_library.manifest_writer.rebuild_manifest_from_canonical_paths.\n  For each bucket
        (instruments-store-{cat}, market-data-tick-{cat},\n  instruments-store-prediction, etc.) — scan canonical paths
        and write missing\n  manifest rows as capture_status=captured. Honest-coverage rule: this pass\n  only fills
        CAPTURED gaps. EMPTY_CONFIRMED / ATTEMPTED_FAILED rows must come\n  from real adapter runs (no retroactive
        sentinel fill — Decision #1 of\n  honest_coverage_metrics_2026_04_19).\n",
      status: todo,
    }
  - {
      id: phase-3-coverage-audit-script,
      content:
        "- [ ] [AGENT] P1. Build deployment-service/scripts/audit-coverage.py — per-category\n  × per-service report.
        Inputs: bucket lists from create-code-tarballs.sh\n  category arrays. Outputs: a markdown table with
        attempt_coverage_pct,\n  capture_coverage_pct, empty_rate, failure_rate per (service × category)
        cell.\n  Integrate into a daily GHA workflow that posts to ops Slack.\n",
      status: todo,
    }
  - {
      id: phase-4-deployment-ui-dashboard,
      content:
        "- [ ] [AGENT] P0. Phase C of honest-coverage-metrics — deployment-api ingest\n  of v5 columns + deployment-ui
        4-state heatmap + filter toggle + retry\n  action + Playwright validation. Currently dispatched (this session).
        Plan\n  ref: honest_coverage_metrics_2026_04_19.md § phase-c-*.\n",
      status: todo,
    }
  - {
      id: phase-4-per-service-coverage-page,
      content:
        "- [ ] [AGENT] P1. New deployment-ui page: /data-status/coverage-roadmap.\n  Renders the matrix from the
        audit-coverage.py script as a per-(service × category)\n  heatmap with click-through to the underlying shards.
        Single source of truth\n  for coverage progress that the operator can refresh on demand.\n",
      status: todo,
    }
  - {
      id: phase-5-coverage-floor,
      content:
        "- [ ] [SCRIPT] P1. Add coverage_floor.yaml (per service × category) ratchet\n  gate. Blocks merges that would
        lower attempt_coverage below the historical\n  baseline. Pattern: same as the coverage_ratchet_policy_2026_04_19
        plan but\n  scoped to data coverage instead of test coverage.\n",
      status: todo,
    }
  - {
      id: phase-5-failure-triage-runbook,
      content:
        "- [ ] [DOC] P1. Write /codex/02-data/failure-triage-runbook.md describing\n  how to read attempted_failed rows
        in the manifest, classify by error_reason,\n  and route to the right owner (adapter team, infra, vendor
        support). Pair\n  with the deployment-ui Retry button workflow.\n",
      status: todo,
    }
isProject: true
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Context + motivation

Honest-coverage-metrics Phase A + Phase B + MTDS bug fix + MDPS extension landed 2026-04-19/20. The ManifestWriter v5
schema now lets every shard ingestion attempt be recorded as one of `captured` / `empty_confirmed` / `attempted_failed`
per the [plan](honest_coverage_metrics_2026_04_19.md). The remaining work is **operational**: actually exercise the new
write path across every (category × service × shard) cell so the Data Status heatmap lights up honestly.

**Definition of "proper coverage" for this plan**:

```
attempt_coverage_pct = (captured + empty_confirmed + attempted_failed) / total_expected_cells
capture_coverage_pct = captured / total_expected_cells
```

For dense categories (CEFI, TRADFI, DEFI tick/onchain), `attempt_coverage` should equal `capture_coverage` once Phase 2
backfills complete — every expected cell either has real data or is documented as failed. For event-driven categories
(SPORTS, PREDICTION), `attempt_coverage` reaches ~99% but `capture_coverage` is intentionally lower because many days
legitimately have no fixtures / no trades on a given conditionId.

**Non-goal**: 100% capture coverage on event-driven categories. That would mean writing synthetic empty rows, which
Decision #1 of the honest-coverage plan explicitly forbids.

## Per-service coverage matrix

### instruments-service (reference data)

Expected cells: per `(date × venue × data_type)` (and `entity` for sports).

| Category   | Shards (per day)                                                    | Backfill launcher                                                 | Phase B status                                                                                                                                          |
| ---------- | ------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI       | 9 venues × {instrument_listing, instrument_availability}            | n/a (lives in `instruments-service` cron)                         | dense, OK                                                                                                                                               |
| TRADFI     | 4 venues × {instrument_listing, instrument_availability}            | same                                                              | dense, OK                                                                                                                                               |
| DEFI       | per-chain × per-protocol × {instrument_listing}                     | same                                                              | dense, OK                                                                                                                                               |
| SPORTS     | 7 providers × {fixtures, odds, leagues, progressive_stats, lineups} | `launch-sfi-forward-poll.sh`, `launch-footystats-forward-poll.sh` | **Phase B partial** — FootyStats / Understat wrapped (commit `64dc3b3`); Kalshi / SFI per-fixture entities deferred (todo phase-1-instruments-deferred) |
| PREDICTION | POLYMARKET + KALSHI × {markets}                                     | `instruments-service/scripts/full_polymarket_dump.py` (CLOB)      | **Phase B partial** — Polymarket script wrapped; per-market loop in `orchestrator.py:1660-1687` deferred                                                |

### MTDS (market tick data)

Expected cells: per `(date × venue × instrument_type × data_type [× chain for DeFi])`.

| Category   | Shards (per day)                                                                                                    | Backfill launcher                                           | Phase B status                                                                                |
| ---------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| CEFI       | 9 venues × 9 instruments × {trades, book_snapshot_5, derivative_ticker, liquidations, futures_chain, options_chain} | `launch-cefi-sharded-backfill.sh`                           | **Phase B done** (commits `aa60dea` + `bc33700` — category-agnostic Bug B fix lifts CeFi too) |
| TRADFI     | CME-ES + CBOE-VIX × {futures, options} × {trades, book_snapshot_5, options_chain}                                   | same                                                        | **Phase B done**                                                                              |
| DEFI       | per-chain × per-protocol × {pools, lending, swaps, lst, gas, oracle}                                                | `scripts/full-defi-backfill.sh`                             | **Phase B done**                                                                              |
| SPORTS     | per-provider × {odds, fixtures, results} via odds-api                                                               | n/a (MTDS Phase B sentinel covers all categories uniformly) | **Phase B done**                                                                              |
| PREDICTION | POLYMARKET × per-conditionId × {trades}                                                                             | `launch-mtds-prediction-backfill-vm.sh` (shipped `8eadd3d`) | **Phase B done** + Bug A (instrument_id) + Bug B (failure classification) fixed `bc33700`     |

### MDPS (market data processing — candle aggregation + bucketing)

Expected cells: per `(date × category × venue × instrument_type × data_type × timeframe [× league_id for sports])`.

| Category   | Shards (per day)                                                                 | Backfill launcher                       | Phase B status                                                                                                                                                                                                  |
| ---------- | -------------------------------------------------------------------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI       | candles aggregated from MTDS trades × 7 timeframes (15s/1m/5m/15m/1h/4h/1d)      | `launch-mdps-backfill-vm.sh cefi`       | **Phase B done** (`08a8e48`)                                                                                                                                                                                    |
| TRADFI     | same pattern                                                                     | `launch-mdps-backfill-vm.sh tradfi`     | **Phase B done**                                                                                                                                                                                                |
| DEFI       | candles from DEX swaps + lending data                                            | `launch-mdps-backfill-vm.sh defi`       | **Phase B done**                                                                                                                                                                                                |
| SPORTS     | bm_time bucketing → odds_horizon_bucket per league × per fixture × per timeframe | `launch-mdps-backfill-vm.sh sports`     | **Dep-check + extension done** (`f18dd5c`); downstream `get_instruments_for_date` SPORTS dispatch + `list_files_in_bucket` bug pending (todo phase-1-instruments-deferred upstream + Phase C session sub-agent) |
| PREDICTION | Polymarket trade aggregation                                                     | `launch-mdps-backfill-vm.sh prediction` | **Dep-check + extension done** (`f18dd5c`); downstream same as SPORTS                                                                                                                                           |

## Operational sequence (the recipe)

### 1. Land Phase C dashboard (1 session, ~3-4 hours)

deployment-api `data_status_service.py` reads the v5 capture_status column. deployment-ui heatmap renders 4 cell states
(captured / empty_confirmed / attempted_failed / missing). Filter "Show only failures". Drill-down with retry button.
Playwright audit in `playwright-artifacts/phase-c-audit-2026-04-20/`.

**Currently dispatched (this session).** Confirm the report when complete.

### 2. Finish Phase B deferred items in instruments-service (1 session, ~2-3 hours)

Polymarket per-market loop, Kalshi inlined paths, SFI per-fixture entities, the two prediction-shards scripts. Each call
site → `record_empty` / `record_failed` / pre-flight `lookup` per the Bug B fix pattern. See todo
`phase-1-instruments-deferred`.

### 3. Cross-category ManifestWriter audit (1 session, ~1 hour)

Grep every `ManifestWriter`, `record_empty`, `record_failed` site across all 6 services that write the manifest
(instruments / MTDS / MDPS / features-sports / features-calendar / features-onchain). Confirm each correctly
distinguishes empty vs failed (the Bug B fix in MTDS may need analogous fixes elsewhere). See todo
`phase-1-cross-cat-audit`.

### 4. Run systematic backfills (~1-2 weeks of compute)

Order of priority:

1. **PREDICTION first** (smallest universe, biggest visibility win):

   ```
   bash deployment-service/scripts/vm/launch-mtds-prediction-backfill-vm.sh \
     2025-03-14 2026-04-20
   ```

   Singleton-locked. Will take ~12 hours wall time. Manifest gains thousands of `captured` + `empty_confirmed` +
   `attempted_failed` rows.

2. **DEFI** (medium universe, spans multiple chains):

   ```
   bash market-tick-data-service/scripts/full-defi-backfill.sh
   ```

3. **CEFI/TRADFI** (largest, longest backfill — already partly done per MEMORY.md):

   ```
   bash deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh
   ```

   ~95 VMs in parallel; verify all reach `DEPLOYMENT_COMPLETED` via `gcloud compute instances list`.

4. **SPORTS** — needs cron stabilization first (todo `phase-2-sports-cron-stabilization`), then single-VM-at-a-time
   backfill via `launch-sfi-forward-poll.sh` + the FootyStats / odds-api equivalents.

### 5. Manifest reconciliation (1 session, ~1 hour)

Per bucket, scan canonical paths and write missing `captured` rows for cells where data exists on GCS but the manifest
is missing. Honest-coverage rule: this pass ONLY fills `captured` gaps, never `empty_confirmed` (no fabrication of
attempt history).

```python
from unified_trading_library.manifest_writer import rebuild_manifest_from_canonical_paths
for bucket in [
    "market-data-tick-cefi-central-element-323112",
    "market-data-tick-tradfi-central-element-323112",
    "market-data-tick-defi-central-element-323112",
    "market-data-tick-sports-central-element-323112",
    "market-data-tick-prediction-central-element-323112",
    "instruments-store-cefi-central-element-323112",
    # ... etc
]:
    rebuild_manifest_from_canonical_paths(
        bucket,
        service_name="<the writing service>",
        prefix="<the canonical path prefix>",
    )
```

See todo `phase-3-reconcile-manifests`.

### 6. Build the daily coverage audit script + report (1 session, ~2 hours)

`deployment-service/scripts/audit-coverage.py` — emits a per-(service × category) table of attempt_coverage_pct,
capture_coverage_pct, empty_rate, failure_rate. Integrate into a daily GHA workflow that posts to Slack
#data-platform-ops.

See todo `phase-3-coverage-audit-script`.

### 7. Add the per-service coverage roadmap UI page (1 session, ~3 hours)

`deployment-ui/src/pages/CoverageRoadmapPage.tsx` — renders the matrix from audit-coverage.py as a heatmap with
click-through. Single SSOT page for coverage progress.

See todo `phase-4-per-service-coverage-page`.

## Success criteria

| Criterion                             | Target                                 | Verification                   |
| ------------------------------------- | -------------------------------------- | ------------------------------ |
| **Honest-coverage code**              | C5 in all 6 manifest-writing services  | `git log` per repo             |
| **Phase C dashboard**                 | Renders 4 cell states + filter + retry | Playwright audit report green  |
| **PREDICTION attempt coverage**       | ≥ 95%                                  | deployment-ui Data Status page |
| **CEFI/TRADFI/DEFI capture coverage** | ≥ 99% (dense)                          | same                           |
| **SPORTS attempt coverage**           | ≥ 95% (legitimate empties allowed)     | same                           |
| **Daily coverage audit**              | Runs automatically + posts to Slack    | GHA workflow passing           |
| **No silent gaps**                    | Zero "unknown" cells in heatmap        | Playwright assertion           |

## Estimated effort + cost

| Phase                            | Sessions          | Compute cost (GCE)                                      |
| -------------------------------- | ----------------- | ------------------------------------------------------- |
| Phase 1 (deferred items + audit) | 2 sessions        | $0                                                      |
| Phase 2 (backfills)              | 1-2 weeks elapsed | ~$100-300 (95 CeFi VMs × few days + smaller categories) |
| Phase 3 (reconciliation)         | 1 session         | $0                                                      |
| Phase 4 (dashboard)              | 1 session         | $0 (Phase C already dispatched)                         |
| Phase 5 (operational gates)      | 1 session         | $0                                                      |

Total: ~5-7 focused agent sessions over ~2 weeks elapsed time.

## Handover prompt for the next agent

```
Read this plan first: unified-trading-pm/plans/active/proper_coverage_roadmap_2026_04_20.md

Pick the next undone P0 todo (in order: phase-1-instruments-deferred, then
phase-1-cross-cat-audit, then phase-2-prediction-backfill, then phase-3-reconcile-manifests).
Each todo has self-contained scope. Sub-agent dispatch is fine for the larger items
(see SUB_AGENT_MANDATORY_RULES.md for context injection pattern).

After completing each todo, mark it done with a [x] in the frontmatter and add
a `note:` field with the commit SHA(s) so the next agent can verify.

Don't try to do all phases in one session — they have natural seams. Phase 2 in
particular requires real wall-clock time waiting for VMs to backfill.
```

## SSOT references

- Phase A/B plan: `unified-trading-pm/plans/active/honest_coverage_metrics_2026_04_19.md`
- Coverage matrix: `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md`
- Tarball flags: `deployment-service/scripts/vm/README.md`
- VM launchers: `deployment-service/scripts/vm/`
- Manifest reconciliation helper: `unified-trading-library/unified_trading_library/manifest_writer.py`
  `rebuild_manifest_from_canonical_paths`
