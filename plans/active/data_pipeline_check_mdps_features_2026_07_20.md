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

- [x] 1. ✅ [SCRIPT] P1. Launcher edits (deployment-service) — `deployment-service@f0b3f14`. `--vm-name` added to
      `launch-mdps-backfill-vm.sh` (VM_NAME_OVERRIDE; single-category only — the `all` fan-out must not set it) and to
      `launch-features-vm.sh`; features also gained `--sink-bucket`/`--source-bucket` which bake
      `IS_TEST_RUN=true PROTOCOL_DATA_SINK_BUCKET_{AG}=<b> [PROTOCOL_DATA_SOURCE_BUCKET=<b>]` into `VM_BACKFILL_CMD`
      (env contract verified against delta_one `FeatureWriter._get_sink_bucket` + `run_pipeline_e2e.py:338`). Chose
      `--sink-bucket` over `--test-run` so the canonical `resolve_bucket_name` stays in Python, not bash. **Evidence:
      deployment-service QG ✅ ALL QUALITY GATES PASSED (139s), incl. the backfill-disk gate (100 launchers on adequate
      disks); shipped via quickmerge --agent, landed on live-defi-rollout.**
- [x] 2. ✅ [SCRIPT] P1. UTL engine edit — `unified-trading-library@82c3c336`. `report.py::_SERVICE_REPOS` +=
      `data_pipeline_e2e_check_mdps`→[market-data-processing-service, deployment-service] and `_features`→
      [features-service, deployment-service], so emitted audit-result frontmatter carries the right `repos:`. No shared
      benchmark/projection helper was needed — the projection math lives in the two SKILL.md (the drivers only measure).
      **Evidence: UTL QG ✅ ALL QUALITY GATES PASSED (360s); shipped via quickmerge --agent, landed on
      live-defi-rollout. Shipped BEFORE deployment-service per dep-order (UTL is T0; the dirty-dep pre-flight gate
      correctly blocked the downstream quickmerge until UTL was clean).**
- [x] 3. ✅ [SCRIPT] P1. MDPS driver — `market-data-processing-service@75ebf8b` (2000 lines, QG green). Enumerates
      cefi/defi/tradfi via `mdps_mvp_universe` + sports/prediction via
      `DATA_TYPES_BY_ASSET_GROUP ∩     needs_candle_processing`; per-timeframe verify; SELF-CONTAINED skip (MDPS reads
      freshness from the bucket it writes, so `--output-bucket` routes both to `-test-`); live leg = honest
      `skipped/live_not_wired`. **TWO INDEPENDENT VERDICTS** (corrected mid-session): force/skip target the writer's
      REAL MEASURED template so the mechanism is provable today, while a separate canonical leg reports
      declared-template divergence as `content_check=non_canonical` with specific tokens + a greppable migration
      worklist. Single-walk discipline (one cached day listing per (bucket,day,root) + stale-listing invalidation
      between VMs). Driver smoke wired into `scripts/quality-gates.sh`. **Shipped under the dirty-deps carve-out** (UTL
      had another agent's LIVE uncommitted WIP, mtime <120s → PROTECT, which blocked the quickmerge pre-flight); commit
      touches only MDPS files.
- [ ] 4. [SCRIPT] P1. Build `features-service/scripts/pipeline_e2e_check.py` (feature-family MVP shards, per-family CLI
      divergence, multi-day lookback windows via resolve_lookback, self-contained skip, benchmark leg). QG features
      green.
- [x] 5. ✅ [SKILL] P1. Both SKILL.md written in the canonical `cursor-configs/skills/` (auto-registered; both now
      appear in the harness skill list). Mirror the MTDS Phase 0/1/2 + report shape and ADD: the canonical-paths
      principle (§3a/§3b — non-canonical is skipped/flagged, never legacy-passed, and IS the migration worklist),
      coverage-aware day selection (MDPS) / per-family multi-day lookback windows (features, via `resolve_lookback.py`),
      the benchmark leg + full-history projection (honest per-shard floor + flat-2019 upper bound) + SPOT cost +
      parallelization headroom (fleet-wide since MDPS/features are NOT Tardis-capped), the known orphan/structural
      cells, and the throughput-measurement traps. MDPS §3 carries the hard scoping warning: an unscoped run is 447
      cells all-AG → ~447 force + ~447 skip VMs, so `--require-captured` is mandatory.
- [ ] 6. [SCRIPT] P2. Wire both drivers into their consumer `quality-gates.sh` + lifecycle markers
      (`# Epic:`/`# Lifecycle:`/`# Delete-when:`).
- [x] 7. ✅ [DATA] P1. `-test-` buckets — **ALL EXIST, no provisioning needed** (object-level probe 2026-07-20; never
      `buckets describe`, which 403s without `storage.buckets.get`). MDPS candles are CO-LOCATED in the MTDS tick
      buckets: `market-data-tick-{cefi,defi,tradfi,sports}-test-*` + `market-data-tick-pred-test-*` (all have objects).
      features: `features-{cefi,defi,tradfi,pred,sports,calendar}-test-*` all exist (cefi has objects, rest empty — the
      legitimate state of an unwritten `-test-` sibling).
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

### 2026-07-20 — build phase kicked off

- **Todo 1 (launcher edits) code-complete (pending QG+quickmerge):** `launch-mdps-backfill-vm.sh` +`--vm-name`
  (VM_NAME_OVERRIDE, single-cat only); `launch-features-vm.sh` +`--vm-name` +`--sink-bucket`/`--source-bucket` (bakes
  `IS_TEST_RUN=true PROTOCOL_DATA_SINK_BUCKET_{AG}=<b> [PROTOCOL_DATA_SOURCE_BUCKET=<b>]` into VM_BACKFILL_CMD —
  verified env contract via delta_one feature_writer `_get_sink_bucket` + run_pipeline_e2e.py:338). Both additive;
  registered prefixes unchanged. **Engine env caveat**: MDPS 250GB boot disk + features 250GB already DEFAULT
  (operator's "250GB" ask already satisfied).
- **Todo 2 (engine edit) code-complete (pending QG+quickmerge):** `report.py::_SERVICE_REPOS` +=
  `data_pipeline_e2e_check_mdps`→[market-data-processing-service,deployment-service],
  `_features`→[features-service,deployment-service].
- **Todo 7 (test buckets) DONE:** object-probe — ALL exist. MDPS shares MTDS tick buckets `market-data-tick-{ag}-test-*`
  (cefi/defi/tradfi/sports/pred, have objects). features `features-{cefi,defi,tradfi,pred,sports,calendar}-test-*` all
  exist (cefi has objects, rest empty — normal). NO provisioning needed.
- **Todos 3+4 (drivers) IN FLIGHT:** workflow `wf_7ebc53e5-dd1` (build→adversarial-review pipeline, 2 drivers, opus).
  Each agent reads DESIGN blueprint + MTDS reference + engine + (edited) launcher, writes
  `scripts/pipeline_e2e_check.py`, QG-greens, does NOT ship. Live/benchmark legs: MDPS live=honest-gap
  (mdps-features-live not wired); benchmark leg opt-in default OFF.
- **Pass-2 audit IN FLIGHT:** workflow `wf_12a59c39-cf6` (benchmark tooling / historical floors / cross-repo lineage-
  orphan / cost model). Feeds todos 10-13 (benchmark/ETA/orphan-migration/optimization).
- Shipping plan: QG+quickmerge deployment(launchers)+UTL(engine)+MDPS+features in ONE controlled batch (≤2 QG at once)
  once the driver workflow completes, then flip todos 1-4. Reason to batch: avoid 4-way QG contention while build agents
  are QG-ing their repos.

### 2026-07-20 — operator clarification: CANONICAL-PATHS PRINCIPLE (HARD — affects todos 3,4,5,8,9,11)

- Operator: "ensure everything is built off expected canonical paths/names etc for all AGs even if some of the data
  doesn't follow that (in which case would be skipped)." Both drivers + both SKILL.md MUST:
  1. Enumerate the shard universe from canonical SSOT ONLY (mdps_mvp_universe/is_mvp/FeatureFamily × canonical
     TIMEFRAMES/data_types), for ALL 5 AGs.
  2. Verify OUTPUT against the CANONICAL path template ONLY — canonical hive key `asset_group=` (DROP the MTDS driver's
     legacy `category=` coarse-fallback), canonical `data_type={mdps_dt}`, canonical `timeframe` (24h→1d), canonical
     instrument_id shape. A parquet present only under a legacy/non-canonical prefix →
     `skipped: non_canonical_object_path` (NOT failed, NOT legacy-pass) = migration signal.
  3. INPUT coverage counts only canonically-shaped captured rows; non-canonical-only input →
     `skipped: non_canonical_input`.
  4. Add a CANONICAL-SHAPE CHECK leg (mirror MTDS `canonical`): assert derived candle/feature ids+paths are canonical
     per AG; non-canonical → `content_check=non_canonical` (distinct verdict). Safe alongside any AG.
  5. The set of `skipped/non_canonical_*` shards IS the migration worklist for todo 11 (migrate existing data →
     canonical, no orphans MVP-or-not).
- ENFORCEMENT: the running build workflow (`wf_7ebc53e5`) predates this note; enforce canonical-only verify +
  non_canonical→skip + the canonical-shape leg in the POST-BUILD review pass on both drivers before shipping, and encode
  it in both SKILL.md. Design blueprint updated (scratchpad `DESIGN_...md` § CANONICAL-PATHS PRINCIPLE).

### 2026-07-20 — PASS-2 AUDIT SYNTHESIS (benchmark/floors/lineage/orphan/cost) — feeds ETA + migration + optimization

**HISTORICAL FLOORS (live-measured raw ticks, B3):** cefi raw **2019-03-30→today** (~2670d), tradfi **2020-01-01→**
(~2392d), prediction raw **2021-06-30** (candles anchor 2025-03-14 — divergence flagged), defi ~**2020-01-01**
(documented; live blocked on stale consolidator). Flat-2019 window = **2757/2758 days**. **CRITICAL: derived CANDLES
barely exist** — cefi 6 rows, tradfi 139, prediction 168 (2026-04 only). So candle backfill is GREENFIELD across full
history; "migrate existing candle data" is nearly a no-op — the real work is the optimized backfill + ETA. Honest
per-shard floor = `min(date where capture_status=='captured')` per (venue,data_type,timeframe) via slim read (do NOT
trust declared constants — provably late). Per-cell floors clip (HYPERLIQUID 2023-05, NASDAQ/NYSE 2023-04-15, etc.).

**COST MODEL (B5):** e2-standard-8 on-demand **$0.268/hr** → SPOT **~$0.024–0.107/hr** (60-91% off; credits exhausted
2026-06-20 so on-demand = real cash). Intra-region GCS egress =
**$0** (all VMs pinned asia-northeast1). MDPS auto
workers = min(cpu,16)=8 on e2-standard-8; features intra-pool default 4 (176-way fan-out possible). **MDPS/features NOT
Tardis-capped → fleet-wide scaling is THE lever** (N date-shard VMs ≈ N×; MANIFEST_PER_VM_SHARDS already set). Disk
pd-balanced 250GB = 70MB/s (pd-ssd faster). Formula: VM_hours = serial_hours/(workers×fleet); cost = VM_hours×$/hr.
Codex perf-targets (LOW-conf, unmeasured): mdps_compute ≈**386 serial-days** (<6h on c2-standard-16/100-conc),
features_compute ≈**2700 serial-days** (<2h on c3-highcpu-176/176-way). → NEED real benchmark to firm up (todo 10/12).

**OPTIMIZATION TARGETS learning-from-cefi (B1/B2, for todo 14):** MDPS candle kernel = polars core groupby (fast) BUT
HFT/whale/carry-forward stay pandas Python loops (whale detect O(n_intervals×n_ticks) `for` loop; `_carry_forward_ohlc`
Python `for i in range`; HFT `grouped.apply`). `_read_tick_data` does `pl.read_parquet(BytesIO(download_all))` — full
blob to RAM (OOM driver), no scan_parquet pushdown. USE_POLARS toggles only the core groupby. → optimize: vectorize the
Python loops / Rust kernel (operator OK'd Rust), scan_parquet pushdown, scale workers to cpu, fleet-wide date-shard,
pd-ssd. Existing bench tool `scripts/benchmark_fullmonth_binance.py` (measures wall/RSS/bytes across current-vs-polars ×
mdps-vs-features) — REUSE for the steady-state benchmark; features `scripts/profile_compute_costs.py` similarly.

**ORPHANS (B4 lineage, verified):** feature families — **performance_features + strategy_pnl_archetype** = ORPHAN
(unwired StrategyPnlStreamEvent → always empty_confirmed EXPECTED_NO_PNL_STREAM; consumers NO-OP/post-cutover) → honest
by-design; skill records skipped/expected_no_upstream, NOT migrate. candle cells produced-but-unconsumed: TRADFI
`ohlcv_1s`, DEFI `book_snapshot_5/market_state/liquidity/fx_rates` (verify — lineage-doc drift), SPORTS
`arbitrage_opportunity` (verify); upstream trap TRADFI `mbp_10` (needs_candle_processing defaults True, no adapter/not
captured → pin False). CONSUMED-CANDLE SET (safe): trades, book_snapshot_5(cefi), derivative_ticker, liquidations,
options_chain, futures_chain, ohlcv_1m/15m/24h, tbbo, dex_pool_swaps.

**DEAD-CODE (B6) → issue doc `issues/mdps_features_deadcode_consolidation_2026_07_20.md` (filed):** BIG findings need
operator keep/delete decision (self-heal + registered-live-launcher blast radius) — S1-a broken
`launch-prediction-features-vm.sh` (bound to self-heal), S1-b non-runnable `launch-mdps-features-live.sh` (+5 registry
rows), S1-c `mdps-sports-` prefix unregistered (monitoring blind spot). Safe: S2-a features-backfill dead lower-half,
S2-b stale SERVICE_TARBALLS keys, S3-a MDPS one-offs past Delete-when (NOT benchmark_fullmonth — reusing it). Do NOT
autonomously delete registered launchers / rebind self-heal (operator returns to this fleet) — document + notify.

### 2026-07-20 — drivers finalized + a DESIGN CORRECTION (canonical verdict split) + verified canonical divergence

- **Both drivers finalized + QG-green.** MDPS `scripts/pipeline_e2e_check.py` (~1793 lines) + features (~997+). The
  finalize pass added canonical enforcement, the MDPS adversarial review that had been rate-limited, the features
  coverage-aware day/window selection (`--require-captured`/`--auto-day` over each family's full lookback window), and a
  real driver gate in each repo's `quality-gates.sh` (features: also FIXED three pre-existing broken `${REPO_ROOT}` path
  vars at lines 174/204/205 that made the e2e/resolve_lookback/run_backfill smoke steps silently take the "not found"
  branch — now proven executing).
- **DESIGN CORRECTION (mine, decided + documented per autonomous rule 2).** The finalize pass made canonical-ness a
  FORCE-leg pass predicate, which would skip essentially every cell (all existing candle data diverges) → the skills
  could never prove force/skip and could not "test all shards". That violates the operator's other explicit requirement.
  Split per the MTDS rule that "three different failure modes on the same cell must never collapse into one pass/fail
  bit": **force/skip verify against the writer's REAL measured shape** (mechanism provable, green achievable today);
  **the canonical leg reports divergence from the DECLARED SSOT template as its own `content_check=non_canonical`
  verdict + migration worklist** (nothing non-canonical silently passes). Correction workflow `wf_763e4b73-af0`.
- **VERIFIED canonical divergence (I ground-truthed with `gsutil ls`, not agent-reported)** → issue doc
  `issues/candle_feature_canonical_path_divergence_2026_07_20.md`:
  - cefi candle object:
    `…/timeframe=15m/data_type=derivative_ticker/venue=DERIBIT/DERIBIT:PERPETUAL:BTC-PERPETUAL.parquet` → `data_type=`
    is the **SOURCE** type (manifest carries aggregated `deriv_ohlcv_15m`), and **NO `instrument_type=` segment exists**
    though the declared template requires it. So path==manifest does NOT hold on data_type; the two SSOTs (PATH_REGISTRY
    vs `docs/GCS_PATHS.md:42`) themselves disagree.
  - tradfi leaves are non-canonical migration artifacts (`E1AF0_C3200_migrated_20260418T131054Z.parquet`) where cefi's
    ARE canonical; and a **zero-length-stem object** exists (`venue=CME/.parquet`) — a genuine defect.
  - sports has NO `processed_candles/` at all — it writes `processed/…/league_id=…/timeframe=T-10m/bucketed.parquet`
    (legitimately different, not a violation).
  - features: **volatility writer bypasses its own path SSOT** (`get_data_sink` built with no `prefix=` → writes at the
    BUCKET ROOT, missing `volatility/by_date/`); UTL paths-registry `delta_one` entry is stale vs the real writer.
  - **Operator ruling needed (A/B/C in the issue doc) BEFORE the full-history backfill** — ~386 serial-compute-days
    would otherwise bake the current shape into the whole corpus. Candles are greenfield today (cefi 6 rows), so
    migrating now is cheap; migrating after the backfill is not.

### 2026-07-20 — operator clarification: CHAIN-BUNDLE RULE (HARD, tradfi + cefi, both drivers)

- Operator: "bundles futures and options across tradfi and cefi need to be processed per files still output one bundled
  file processing per instrument." **Confirmed as the already-implemented SSOT contract** (read
  `market_data_processing_service/app/core/output_path_helpers.py` first-hand, 2026-07-20):
  - chain data_types = UAC `CEFI_CHAIN_INSTRUMENT_TYPES` = `{options_chain, futures_chain}`; its docstring states the
    tokens "apply identically to TradFi (CME ES options, ETFs)" → BOTH asset_groups, as the operator said.
  - OUTPUT = ONE bundled file per (date, root): `CHAIN_BUNDLE_FILENAME = "ticks.parquet"` →
    `…/venue={V}/underlying={U}/ticks.parquet`; non-chain stays `…/venue={V}/{instrument_id}.parquet`.
  - PROCESSING iterates PER-INSTRUMENT within the bundle: `_process_chain_timeframe` groups by `instrument_key`;
    `_iter_chain_symbol_dfs` "lazily reads ONE symbol at a time" — the memory-safe path (vs `_read_tick_data`'s eager
    whole-blob read, which is the OOM driver B1 flagged).
  - HISTORICAL BUG the rule fixed (P1.5 SP500 master plan 2026-05-05): output named `{instrument_id}.parquet` from the
    FIRST strike's id. **This gives the drivers a real regression check.**
- **ENFORCE in both drivers (post-correction pass):** (1) chain shard atom = one underlying-root, never per-strike; (2)
  force/skip verify must expect `underlying={U}/ticks.parquet` for chain data_types — looking for a per-instrument leaf
  on a chain cell is a guaranteed FALSE `no_candle`; (3) canonical leg treats the bundled leaf as CANONICAL and flags a
  per-strike leaf under a chain data_type as `content_check=non_canonical: chain_leaf_not_bundled` (the 2026-05-05
  regression re-firing); (4) benchmark/ETA must not extrapolate a chain rate from a spot/perp cell — DERIBIT options
  chains run ~2-3M rows/shard.

### 2026-07-20 13:53 — MDPS canonical-verdict split DONE; features correction BLOCKED on session limit

- **MDPS driver corrected + QG-green (2000 lines)** — the measured-vs-declared split landed cleanly:
  - **force predicate = the writer's REAL measured template**:
    `processed_candles/by_date/day={D}/pipeline_mode={pm}/ timeframe={tf_RAW}/data_type={SOURCE_dt}/venue={V}/[underlying={U}/]{leaf}.parquet`
    — SOURCE data_type (NOT `mdps_data_type_key`), NO `instrument_type=` segment, RAW tf token (`24h` stays `24h`;
    normalisation is the manifest's job). Sports routed to its own measured root
    `processed/by_date/…/league_id=…/timeframe=T-10m/ bucketed.parquet`. Manifest verify UNCHANGED (canonical
    `mdps_dt` + NORMALISED tf — the manifest genuinely carries those; only the OBJECT path diverges). Force can now
    legitimately go GREEN on today's real data.
  - **canonical leg = strict vs the DECLARED SSOT**, computed over real objects INDEPENDENTLY of force acceptance, so a
    force-green cell still reports `content_check=non_canonical` with specific tokens. Verified verdicts: cefi
    `missing_segment=instrument_type; data_type=derivative_ticker!=deriv_ohlcv_15m` (+ `timeframe=24h!=1d` at 24h);
    tradfi `missing_segment=instrument_type; leaf=E1AF0_C3200_migrated_*(not VENUE:TYPE:SYMBOL)`; empty-stem objects get
    a dedicated `empty_instrument_stem` token and are EXCLUDED from force evidence so they can never green a cell.
  - Sibling-collision guard: measured data_type pinned to the SOURCE type exactly (trades+15m→ohlcv_15m would otherwise
    collide with tradfi's SOURCE ohlcv_15m) and tf pinned to the raw token — verified a 5m object and a trades object
    both correctly REJECT against a 15m/ohlcv_15m shard.
- **⛔ features driver correction FAILED — "You've hit your session limit · resets 2pm (Europe/London)".** The features
  driver therefore STILL has canonical-ness as a FORCE-leg pass predicate (from the earlier finalize pass), which would
  skip essentially every cell. **THIS IS THE NEXT ACTION after 14:00 BST**: re-run the identical measured-vs-declared
  split for features (same spec as MDPS; per-family REAL writer templates — delta_one
  `delta_one/day={D}/…/ feature_group_version={N}/…` with NO by_date/, volatility currently writing at BUCKET ROOT per
  the writer bypass).
- Investigation workflow `wf_362e496d-a35` (5 read-only agents: P0 manifest disconnect, chain-bundle/empty-stem fix
  spec, DeFi-MVP ETA inputs, backfill optimization runbook, orphan/migration worklist) launched 13:48 and is running.
- **RESUME POINTER for a compressed future-me**: MDPS driver = corrected/green/uncommitted; features driver = needs the
  split; nothing driver-side is committed yet (deployment-service@f0b3f14 + unified-trading-library@82c3c336 ARE
  shipped). Both SKILL.md written + uncommitted.

### 2026-07-20 15:0x — REAL e2e RUNS on live VMs: the skill works, and it found a P0 on its first run

**Todo 8 (MDPS e2e) — EXECUTED on real infrastructure, PROD verified untouched.** Two scoped runs, both test-bucket
routed via the new `--output-bucket`, both using real VMs polled through the shared engine's GCS observability contract.

**Run 1 — CEFI:DERIBIT:derivative_ticker (force+skip+canonical), day auto-substituted 2026-07-15 → 2024-02-08:**

- Report: `plans/audit/results/data_pipeline_e2e_check_mdps_2026_07_15.md` — total=21 passed=7 failed=7 skipped=7.
- **FOUND A P0** (filed `issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md`, PM@9ef516eec): every
  parquet write failed
  `StreamingParquetWriter pre-write validation … [schema_violation] column 'funding_rate_mean' / 'mark_price_mean' / 'index_price_mean' missing`.
  ZERO objects; 140 manifest rows (7tf × 20 instruments) ALL `attempted_failed/SCHEMA_VALIDATION_FAILED` row_count=0.
  **Yet the VM exited rc=0 reporting "20 success, 0 failed, 152,300 candles"** — a backfill would burn full compute,
  write nothing, and look green.
- **The skill's `failed` verdict was CORRECT where the VM's own exit code lied.** That is the whole point of the check.

**Run 2 — CEFI:DERIBIT:trades (force), day auto-substituted → 2026-04-17: SCOPE RESULT — `trades` WORKS.**

- `POLARS AGGREGATED: 1440 1m / 288 5m / 96 15m / 24 1h / 6 4h / 1 24h` candles (counts arithmetically correct for one
  day), no schema violation, 7 new manifest rows, EXIT_STATUS=0.
- **14 real candle objects verified on disk** in the `-test-` bucket, on the measured template with CANONICAL leaf ids:
  `processed_candles/by_date/day=2026-04-17/pipeline_mode=batch_tardis/timeframe=15m/data_type=trades/venue=DERIBIT/DERIBIT:PERPETUAL:BTC-PERPETUAL.parquet`
- => **The candle pipeline is NOT globally broken. The breakage is data_type-SPECIFIC (`derivative_ticker`).** This is
  what makes a DeFi-MVP ETA computable: budget the working data_types now, treat `derivative_ticker` as blocked on the
  P0 fix. Todo 3 of the P0 issue (sweep the OTHER data_types) is the remaining scoping work.

**VALIDATED BY THESE RUNS (the skill's core contract):** `--auto-day` correctly substituted a captured day in BOTH runs
(the requested 2026-07-15 had no captured input); `--output-bucket` test-routing worked (parquet AND manifest both to
`-test-`, PROD confirmed unmodified for the target day); the new `--vm-name` gave the engine a deterministic
`vm-logs/<vm>/` to poll; force and skip legs used DISTINCT VM names (`-pipelinecheck-` vs `-pcskip-`) so they never
collide; honest-absence held (`attempted_failed`, never a phantom `captured`).

**FIRST REAL THROUGHPUT DATAPOINTS (for the ETA, per-instrument, e2-standard-8):** derivative_ticker 2105ms/instrument
(42.1s for 20) and 2255ms/instrument (45.1s for 20) — but those runs FAILED their writes, so treat as compute-only. The
trades run is the honest one to extrapolate from. NOTE: these are single-cell boot-dominated runs — a steady-state
benchmark VM is still required before quoting a backfill ETA.

**DRIVER IMPROVEMENTS FOUND BY RUNNING IT (todo-list, not blockers):**

1. force-leg manifest verify reads the CONSOLIDATED index and reported the uninformative `no_matching_row` when the leg
   VM's OWN per-VM shard held `attempted_failed/SCHEMA_VALIDATION_FAILED` (Phase-0 consolidated 13:05, VM wrote 13:12).
   Fix: read the leg VM's own per-VM shard first, like the MTDS twin's `_read_per_vm_batch_row`. (P0 issue todo 4.)
2. `--project` (or `GCP_PROJECT_ID`) is REQUIRED or `get_project_id()` raises a raw traceback — same in the MTDS twin.
   Document in both SKILL.md.
3. Per-cell wall-clock is ~35 min for 1 cell × 7 timeframes (2 VMs + verification); the post-VM verification alone ran
   ~19 min, likely an unfiltered availability-index read. Worth a slim/filtered read before any wide sweep.

**SSOT GAP FOUND (from another agent's concurrent work):** CLAUDE.md now mandates "canonical/non-canonical is the UAC
`canonical_path_violations()` MACHINE ORACLE, never a re-implemented rule" — but that oracle is scoped to
`RAW_TICK_DATA_PREFIX = "raw_tick_data/by_date/"` ONLY (partition_paths.py:66,681-683; ZERO mentions of
`processed_candles`/`features/`). It CANNOT be applied to the candle or features surfaces (it would flag every object
non-canonical). Correct fix: extend the oracle to those surfaces in UAC so my drivers and
`/data-pipeline-reconciliation` share ONE oracle. Until then the drivers' local logic is not a duplication violation but
WILL drift.

### 2026-07-20 — OPERATOR CONTRACT: "empty window" vs "not fetched yet" are TWO signals (durable rule)

Operator, verbatim: _"the key is knowing what is empty data because theres nothing to aggregate in the window vs not
fetched yet that's where the manifest needs to help and different consumers live and batch will have different ways of
handling depending on their needs"_

**The contract (durable — belongs in `codex/02-data/honest-absence-downstream-handling.md` at the post-phase codex
audit; journaled here so it is not lost first):**

| Question a consumer asks                   | Which surface answers it        | Representation                                                                                    |
| ------------------------------------------ | ------------------------------- | ------------------------------------------------------------------------------------------------- |
| "Was this WINDOW active?"                  | the **parquet**, per bin        | row EXISTS on the session grid with **NaN price-like + 0 volume** = covered, nothing to aggregate |
| "Was this SHARD-DAY ever fetched/derived?" | the **manifest**, per shard-day | 4-state `capture_status`                                                                          |

- `captured` — derived, ≥1 bin had a real observation.
- `empty_confirmed` + a **typed** `EmptyConfirmedReason` — derived, but the WHOLE shard-day legitimately had nothing.
- `attempted_failed` + `error_reason` — we tried and it broke.
- `expected_unattempted` / no row — **never attempted**. There is no parquet to be NaN.

**Why it matters:** NaN alone cannot carry both meanings. A consumer must never infer "was this fetched?" from NaN in a
parquet, nor "was this window active?" from the manifest alone. Live and batch consumers handle each case differently
per their own needs, so the pipeline's job is to PRESERVE the distinction faithfully, never to paper over it. This is
exactly why LOCF (carry-forward) is wrong for `derivative_ticker`: it fabricates an observation in a window that had
none, destroying signal (1) and making the gap invisible.

**Two failure modes this rule makes checkable (NEW checks for both skills):**

1. manifest `captured` but NO parquet object = **phantom capture** (already checked — this is the MTDS-documented
   `PHANTOM_CAPTURED_NO_OBJECT`).
2. parquet present but **100% NaN bins** while the manifest says `captured` = should have been `empty_confirmed` with a
   typed reason. An all-NaN "capture" is the INVERSE phantom and is equally misleading. **Add this assertion to the MDPS
   driver's content check** (todo below).

**Applied immediately to the in-flight P0 fix** (`issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md`):
the fix must (a) leave empty bins NaN/0 rather than LOCF-filling them, (b) record `empty_confirmed` + typed reason when
the ENTIRE shard-day is empty rather than writing an all-NaN parquet as `captured`, and (c) document the two-signal
contract in-code so nobody "helpfully" re-adds carry-forward.

- [ ] NEW todo. [SCRIPT] P1. Add the all-NaN-parquet-vs-`captured` assertion to `/data-pipeline-check-mdps` (and the
      features twin where a family can emit an all-null feature frame) as a distinct `content_check=` verdict, so the
      inverse-phantom is caught the same way the phantom is.
- [ ] NEW todo. [DOC] P2. Promote the two-signal table above into `codex/02-data/honest-absence-downstream-handling.md`
      at the post-phase codex audit (SSOT direction: codex, not this plan).
