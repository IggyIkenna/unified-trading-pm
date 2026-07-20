---
doc_type: plan
title:
  Data-pipeline e2e smoke check — MDPS (candles) + features skills, cross-repo orphan migration, optimized backfill
  readiness + remaining-DeFi-MVP ETA (`/data-pipeline-check-mdps` + `/data-pipeline-check-features`)
summary: |
  Extend the shared UTL `pipeline_e2e_check` engine to two new services — market-data-processing-service (candle
  derivation) and features-service (feature compute) — with thin per-service `scripts/pipeline_e2e_check.py` drivers +
  two Claude Code skills mirroring `/data-pipeline-check-mtds`. Each proves, on real infra (test-bucket writes only),
  force-recompute + skip-if-fresh for every MVP shard across ALL asset_groups; adds a steady-state benchmark leg that
  measures amortized per-shard-day throughput and projects full-history (honest per-shard floor + flat 2019) time +
  SPOT compute cost + parallelization/optimization headroom (box + fleet + Rust/faster-libs; MDPS/features are NOT
  Tardis-IP-capped). Then: run a cross-repo orphan/lineage audit (MTDS raw → MDPS candles → features → ml/strategy) and
  MIGRATE existing candle/feature data to zero orphans (MVP or not); make the backfill-processing path (download →
  process → upload) code-ready + optimized learning from cefi; and produce a concrete ETA to backfill all remaining
  DeFi MVP. Autonomous dispatch 2026-07-20 (operator away 6h) — journal every unit here against context loss.
status: active
nature: process
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos:
  [
    unified-trading-library,
    market-data-processing-service,
    features-service,
    deployment-service,
    unified-trading-pm,
    ml-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags:
  [
    data-pipeline,
    smoke-test,
    e2e,
    backfill,
    mdps,
    candles,
    features,
    force-skip,
    benchmark,
    cost-projection,
    orphan-migration,
    skill,
    autonomous,
  ]
related:
  [
    data_pipeline_e2e_check_2026_07_10.md,
    features_service_e2e_pipeline_test_2026_05_26.md,
    ../epics/infrastructure_master.md,
    ../../cursor-configs/skills/data-pipeline-check-mtds/SKILL.md,
    ../../cursor-configs/skills/data-pipeline-check-is/SKILL.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >
  operator autonomous dispatch 2026-07-20 — build /data-pipeline-check-mdps + /data-pipeline-check-features mirroring
  MTDS with all the tricks; benchmark per-shard + full 2019-2026 time/compute cost + parallelization/optimization
  (Rust/faster-libs/multiproc/250GB disk ok); all migrations done on existing data no orphans MVP-or-not; code ready to
  backfill remaining MVP optimized (download/process/upload) learning from cefi; ETA to backfill all remaining DeFi MVP;
  keep documenting in case of context loss. Operator decisions locked via structured question 2026-07-20 (benchmark=both
  smoke+steady-state VM per shard-type, window=honest-floor+flat-2019, orphan=cross-repo lineage).
---

# Data-pipeline e2e check — MDPS + features skills, orphan migration, backfill readiness + DeFi-MVP ETA

> **🟢 In-flight autonomous run (2026-07-20, operator away 6h).** This plan is the loop's handoff document (Progress Log
> below). A compressed-context future-you resumes from: this brief + the Todos + the Progress Log + the durable design
> blueprint at `/private/tmp/claude-501/.../scratchpad/DESIGN_mdps_features_skills.md` (session-local) — key facts also
> journaled below so they survive scratchpad loss.

## Context

Extends `data_pipeline_e2e_check_2026_07_10.md` (which built the shared `unified_trading_library.pipeline_e2e_check`
engine + the `/data-pipeline-check-is` and `/data-pipeline-check-mtds` skills and explicitly names "features-service
next"). Same architecture: shared engine (launch→poll→verify→report) + a thin per-service
`scripts/pipeline_e2e_check.py` that supplies only shard enumeration, launcher-argv building, the skip-signal log
pattern, and bucket/match/prefix resolution. Two audit passes (18 sub-agents, 2026-07-20) mapped the engine, both
reference drivers, both target services, their launchers, the coverage model, the MVP/bucket contracts, benchmark
tooling, historical floors, the cross-repo lineage, and dead-code — findings journaled below.

## Finish-line criteria (autonomous — all must be TRUE)

1. `/data-pipeline-check-mdps` + `/data-pipeline-check-features` built (SKILL.md + `scripts/pipeline_e2e_check.py`
   drivers), QG-green, wired into the consumer `quality-gates.sh`, lifecycle-marked, shipped via quickmerge.
2. Force-recompute + skip-if-fresh PROVED for every MVP shard across ALL asset_groups under both skills, on real infra
   (test-bucket writes only) — report(s) written + relayed.
3. Steady-state benchmark leg run per representative shard-type → full-history (honest per-shard floor + flat 2019→now)
   time + SPOT compute-cost + parallelization/optimization (box + fleet + Rust/faster-lib) projection in the report.
4. Cross-repo orphan/lineage audit done AND all existing candle/feature data migrated to zero orphans (MVP or not).
5. Backfill-processing path (download → process → upload) code-ready + optimized, learning from cefi.
6. Concrete ETA to backfill all remaining DeFi MVP.
7. Rule-9 final report; no `DEFERRED`/`BLOCKED-OPERATOR` leftovers (only genuine operator-gated credential blocks
   defer).

## Codex SSOTs (read + keep the plan aligned)

- `codex/02-data/availability-manifest-and-data-status.md`, `…/honest-coverage-model.md` (4-state capture_status, shard
  atom, coverage formula)
- `codex/05-infrastructure/vm-launcher-runbook.md` (§ Tardis cap — MDPS/features are EXEMPT: they read GCS, don't
  fetch), `…/spot-vms-for-backfill.md`, `…/bucket-isolation-model.md`
- `codex/06-coding-standards/` (QG bans), `codex/12-agent-workflow/async-wait-and-poll-discipline.md`
- Engine + reference drivers: `unified-trading-library/unified_trading_library/pipeline_e2e_check/`,
  `market-tick-data-service/scripts/pipeline_e2e_check.py`

## Todos

- [ ] 1. [SCRIPT] P1. Launcher edits (deployment-service): add `--vm-name` to `launch-mdps-backfill-vm.sh` +
      `launch-features-vm.sh`; add test-bucket routing (`--test-run` → IS_TEST_RUN + PROTOCOL_DATA_SINK_BUCKET_{AG}) to
      `launch-features-vm.sh`. Additive, mirror MTDS. QG deployment-service green.
- [ ] 2. [SCRIPT] P1. UTL engine edit: add `data_pipeline_e2e_check_mdps` + `_features` to `report.py::_SERVICE_REPOS`;
      add shared benchmark/projection helpers if reusable. QG unified-trading-library green.
- [ ] 3. [SCRIPT] P1. Build `market-data-processing-service/scripts/pipeline_e2e_check.py` (candle MVP shards:
      cefi/defi/ tradfi via `mdps_mvp_universe` + sports/prediction via candle-processed data_types; per-timeframe
      verify; self-contained skip; live=honest-gap; benchmark leg). QG MDPS green.
- [ ] 4. [SCRIPT] P1. Build `features-service/scripts/pipeline_e2e_check.py` (feature-family MVP shards, per-family CLI
      divergence, multi-day lookback windows via resolve_lookback, self-contained skip, benchmark leg). QG features
      green.
- [ ] 5. [SKILL] P1. Write `data-pipeline-check-mdps/SKILL.md` + `data-pipeline-check-features/SKILL.md` (canonical
      `cursor-configs/skills/`) — mirror MTDS Phase 0/1/2 + report shape + new
      benchmark/projection/cost/parallelization/ orphan-lineage sections + coverage-aware day/window selection.
- [ ] 6. [SCRIPT] P2. Wire both drivers into their consumer `quality-gates.sh` + lifecycle markers
      (`# Epic:`/`# Lifecycle:`/`# Delete-when:`).
- [ ] 7. [DATA] P1. Provision `-test-` buckets (object-probe, never `buckets describe`) — MDPS
      `market-data-tick-{ag}-     test-{pid}` (shared w/ MTDS), features `features-{ag}-test-{pid}` +
      `features-sports-test`/`features-calendar-test`.
- [ ] 8. [DATA] P0. RUN + VALIDATE `/data-pipeline-check-mdps` e2e: auto-select high-coverage day per AG, prove
      force+skip for every MVP candle shard (all AGs × venues × data_types × timeframes). Report written.
- [ ] 9. [DATA] P0. RUN + VALIDATE `/data-pipeline-check-features` e2e: multi-day input window per family, prove
      force+skip for every MVP feature shard (all families × valid AGs). Report written.
- [ ] 10. [DATA] P1. Steady-state benchmark VMs (250GB disk) per representative shard-type; measure amortized per-shard-
      day throughput (RX + rows/s + wall-clock); project full-history time (honest floor + flat 2019) + SPOT cost +
      parallelization/optimization headroom.
- [ ] 11. [DATA] P0. Cross-repo orphan/lineage audit (MTDS→MDPS→features→ml/strategy) + MIGRATE existing candle/feature
      data to zero orphans (MVP or not). Migrations run to real completion (data-correctness heartbeat).
- [ ] 12. [SCRIPT] P1. Backfill-processing path (download→process→upload) code-ready + OPTIMIZED learning from cefi
      (within-VM multiproc, faster-libs/Rust where it pays, 250GB disk, fleet-wide since not Tardis-capped).
- [ ] 13. [DATA] P0. Produce concrete ETA to backfill all remaining DeFi MVP (from benchmark + remaining-shard count +
      optimized throughput + fleet width + $ cost).
- [ ] 14. [SCRIPT] P2. Ship everything via quickmerge --agent per repo; flip these checkboxes same-turn; rule-9 final
      report. Post-phase codex audit (update contracts / stub patterns / CLAUDE.md one-liner for the two new skills).

## Progress Log

### 2026-07-20 — session start (autonomous dispatch, operator away 6h)

- Read `SUB_AGENT_MANDATORY_RULES.md` + `AUTONOMOUS_AGENT_RULES.md` (rules injection OK). Model tier = opus-4-8[1m]
  (correct for cross-repo autonomous loop). Invoked `/autonomous`.
- Read shared engine first-hand (launcher/log_grep/prod_precheck/report/shard_verify) + both template SKILL.md.
- Ran 2 audit workflows (18 sub-agents). **KEY FACTS (survive scratchpad loss):**
  - Engine contract: driver supplies shard-enum + launcher-argv + skip-signal + bucket/match/prefix; engine does
    launch→poll(`gs://deployment-scripts-{pid}/vm-logs/{vm}/{EXIT_STATUS,run.log}`)→verify(`read_availability_index` +
    `verify_write`)→report. `_SERVICE_REPOS` needs 2 new entries.
  - **MDPS**: entrypoint
    `python -m market_data_processing_service --operation process --mode batch --start-date D --end-date D --{CAT} --venues V --data-types dt [--force]`.
    Launcher
    `launch-mdps-backfill-vm.sh <ag> <start> <end> full --venues V --data-types dt --output-bucket <test> --force` (NO
    --vm-name/--timeframes/--test-run; test routing via `--output-bucket market-data-tick-{ag}-test-{pid}`; 250GB disk +
    e2-standard-8 + SPOT default). Skip signal: `"SKIP date=%s category=%s: already fresh in manifest (use --force)"`.
    Candles co-located `market-data-tick-{ag}-{env}-{pid}` under `processed_candles/`,
    `service_name=market-data-processing-service`, data_type=`mdps_data_type_key(src,tf)` (trades+1m→ohlcv_1m…), 24h→1d.
    Shard atom (ag,venue,itype[inferred], data_type,timeframe). Enumerate:
    cefi/defi/tradfi=`mdps_mvp_universe(ag)`×`needs_candle_processing`× `get_valid_timeframes_for_data_type`;
    sports/prediction=`DATA_TYPES_BY_ASSET_GROUP` candle subset. Skip=self- contained (freshness read=output=-test-).
    **LIVE leg NOT runnable** (`launch-mdps-features-live.sh` has no dispatch branch → ModuleNotFoundError) — honest
    gap.
  - **features**: entrypoint
    `python -m features_service.<family> --operation compute --mode batch --asset-group AG [--feature-group G] --start-date D --end-date D [--force]`
    (per-family CLI divergence). Launcher canonical
    `launch-features-vm.sh --feature-family fam --asset-group AG --start-date D --end-date D --launch-mode full` (NO
    --vm-name/--test-run; 250GB+SPOT default). Skip signal `"Skipping %s - already processed"` (DEBUG → rely on
    fingerprint-unchanged). Output `features-{ag}-{env}-{pid}` (kind="features"; sports/calendar/commodity special),
    per-family path drift. (family→ag): delta_one[CEFI,DEFI,TRADFI,PRED], volatility[CEFI,TRADFI], onchain[DEFI],
    sports[SPORTS], calendar[CEFI,TRADFI global], multi_timeframe[CEFI,DEFI,TRADFI], cross_instrument[CEFI,TRADFI,PRED],
    commodity[TRADFI]. Lookback: delta_one max 200 candles, cross_instrument 500 → multi-day window via
    `scripts/e2e/resolve_lookback.py`. Reuse `scripts/e2e/run_pipeline_e2e.py`. Skip=self-contained (check_exists probes
    sink=-test-).
  - **Coverage day-select**: replicate MTDS `_captured_days_by_cell`/`_resolve_shard_day` on the INPUT manifest (raw
    ticks for MDPS, candles for features), prefer newest non-1st-of-month.
    `read_availability_index(bucket, columns=[...], filters=[("date",">=",s),("date","<=",e)])` pushdown for windows.
  - **Not Tardis-capped**: MDPS/features read GCS (don't fetch) → parallelize fleet-wide, unlike MTDS N=1.
  - **Launcher edits needed**: --vm-name (both), --test-run (features).
- Design blueprint written to scratchpad `DESIGN_mdps_features_skills.md`. Pass-2 audit (benchmark/cost/lineage/orphan)
  in flight; findings to be journaled on completion.
- NEXT: launcher edits → engine edit → MDPS driver → features driver → skills → e2e → benchmark → orphan migration →
  ETA.
