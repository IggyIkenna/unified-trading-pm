---
doc_type: plan
title:
  Data-pipeline check MDPS + features — extracted historical Progress Log (build/investigation record, no open work)
summary: |
  Archive-bound record extracted VERBATIM 2026-07-24 from `data_pipeline_check_mdps_features_2026_07_20.md`
  (plan-hygiene line-cap remediation — parent was ~1200 lines, hard cap is 1000). Contains only fully-closed
  Progress Log dated entries that carried ZERO open todo checkboxes: session-start audit notes, the build-phase
  journal, the canonical-paths / chain-bundle operator clarifications, the MDPS canonical-verdict-split narrative,
  the first real e2e VM runs, the write-bottleneck investigation-and-refutation chain (manifest-flush hypothesis,
  GIL measurement, per-unit latency work), the SPOT-preemption fleet-wide fix narrative, the DeFi-MVP ETA
  measurement writeup, and the derivative_ticker P0 loop-close chain ending in its real-VM resolution. Every open
  todo (`- [ ]`), every checked top-level todo in the parent's `## Todos` section, and every Progress Log entry that
  still carried an open `NEW todo` checkbox were LEFT IN THE PARENT — nothing open moved here. This file has zero
  todos and is not itself actionable; it exists so the history is not lost and the parent stays under the line cap.
status: complete
nature: record
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
tags: [data-pipeline, mdps, candles, features, history, archive-bound, record, plan-hygiene]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/archive/2026_07/candle_canonical_path_migration_execution_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: docs_reconciler
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >
  Extracted 2026-07-24 from data_pipeline_check_mdps_features_2026_07_20.md's Progress Log — plan-hygiene line-cap
  remediation (parent still ~1200 lines after the earlier candle-canonical-path-migration extraction). This file holds
  only the dated entries that had zero open todo checkboxes; entries carrying any `- [ ]` stayed in the parent verbatim,
  untouched.
---

# Data-pipeline check MDPS + features — extracted historical Progress Log

> **Archive-bound record.** No open work lives here. This is a verbatim extraction of closed Progress Log entries from
> `/plans/active/data_pipeline_check_mdps_features_2026_07_20.md` — read that file for the plan's live Todos,
> Finish-line criteria, and any Progress Log entry that still carries an open todo. Nothing below was summarized,
> reworded, or trimmed; it is a byte-for-byte move of complete dated sections.

## Progress Log (historical — extracted verbatim, no open todos)

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
- **FOUND A P0** (filed `/plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md`,
  PM@9ef516eec): every parquet write failed
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

### 2026-07-20 — CORRECTION: the candle write bottleneck is NOT the MTDS 50GB-disk issue (operator question)

Operator asked whether the write-bound finding is the same problem as the MTDS cefi one (50GB disk throttling write
speed, fixed by going to 250GB). **Measured answer: NO — different bottleneck, and the MTDS fix is already applied.**

|                | MTDS cefi disk issue                   | MDPS candle writes (measured today)                                                                                                         |
| -------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| volume         | GBs of `.csv.gz` + parquet, sustained  | **1.99 MB total across 14 objects** (avg 149 KB)                                                                                            |
| effective rate | 2.36 MB/s after burst-credit depletion | **0.038 MB/s** (2.0 MB / 51.9s)                                                                                                             |
| disk           | 50 GB **pd-standard**                  | **250 GB pd-balanced ALREADY** (`launch-mdps-backfill-vm.sh:125` `BOOT_DISK_GB:-250`, enforced by `check_backfill_vm_disk_provisioning.py`) |
| headroom used  | saturated                              | **~0.05%** of the ~70 MB/s that 250GB pd-balanced provides                                                                                  |

You cannot be disk-BANDWIDTH-bound writing 2 MB in ~52s. Raising disk size/type buys ~nothing for candles. **This
DEMOTES "disk type/size" from lever #2 to a non-lever for MDPS** (it remains correct and load-bearing for MTDS download
VMs, which move GBs — do not weaken that gate).

**Where the time actually goes (per instrument, from run.log timestamps):**

- aggregation of all 6 timeframes: `13:52:30.763 → 13:52:32.235` = **1.47s**
- silent gap to the next manifest update: `13:52:32.235 → 13:52:42.956` = **10.7s** for 7 shards ≈ **1.5s per shard**

So the cost is **per-object latency + per-shard manifest flush**, i.e. round-trips and serialization — NOT bytes.

**Leading suspect (to VERIFY, not assert):** `canonical_writer_manifest.py::_flush_manifest_with_backoff` force-flushes
the manifest after EVERY shard (deliberate — "so SIGKILL loses ≤1 shard"), each flush rewriting the growing per-VM shard
parquet. 14 shards => 14 read-modify-write cycles. Observed in-log: the per-VM shard goes `(1 total entries, 1 new)` →
`(8 total entries, 7 new)` → … i.e. rewritten repeatedly. If confirmed, this is a **durability-vs-throughput tradeoff**,
not a hardware limit, and the fix is to batch the flush (per instrument / per N shards) while preserving an acceptable
crash-loss bound — NOT to buy faster disks.

**Revised optimization ranking for MDPS candles (measurement-driven):**

1. **Verify + fix write parallelism** (`max_workers`=8 appears NOT to overlap: 25,948ms x 2 == 51.9s total).
2. **Batch the per-shard manifest flush** (if confirmed as ~1.5s/shard), with an explicit crash-loss bound.
3. **Fewer/larger objects** (7 small parquets per instrument-day) — interacts with the canonical ruling, so gated.
4. **Fleet width** — reliable multiplier, but multiplies a latency-bound unit; fix 1+2 first or you buy N x the same
   stall.
5. ~~Disk type/size~~ — **NOT a lever for candles** (0.05% utilised). Keep it for MTDS download VMs.
6. **Rust/faster libs** — lowest: polars aggregation is only ~1.5s of ~12.2s.

### 2026-07-20 — ✅ P0 derivative_ticker FIXED + shipped (`uac@…_candle_contracts` + `market-data-processing-service@beea161`)

The P0 the skill found on its first run is fixed to the operator's exact semantics and shipped.

- **Root cause (two-part):** the deriv candle contract `_DERIV_EXT` REQUIRED `funding_rate_mean`/`mark_price_mean`/
  `index_price_mean`, but the adapter emitted them UNSUFFIXED (`CandleOutput.to_dataframe()` drops `None` fields) →
  every write failed `StreamingParquetWriter` strict validation. Independently, LOCF + `_finalize_session_grid`
  fabricated a price for empty windows.
- **Fix (operator semantics):** value = LAST-observation-in-window; empty window → NaN price + 0 volume (LOCF removed;
  `supports_prior_day_seed=False`); all-NaN input → 0 rows → `empty_confirmed` + typed reason, NEVER an all-NaN
  `captured` parquet. Emit the `*_mean` names (documented as a MISNOMER — last-in-window, not a mean; a future
  `*_mean`→`*_last` cross-repo rename is the correct migration). Also caught+fixed a real ordering bug (`groupby.last()`
  was positional; now sorts by `processing_dt` — MTDS tick parquets aren't guaranteed timestamp-sorted).
- **Two-signal contract implemented** exactly as the operator specified: parquet per-bin NaN/0 = "covered window,
  nothing to aggregate"; manifest `empty_confirmed`+typed reason = "no ticks at all".
- **Runtime-proven** against the REAL `StreamingParquetWriter` for all 7 timeframes + a sparse frame; MDPS QG 251s /
  2058 passed, UAC QG 617s / 124 passed. `book_snapshot_5` checked — no equivalent defect (its "quote always exists" is
  true for book data; still LOCF by design, a separate operator decision if honest-absence is wanted there too).
- **Shipped dep-ordered**: UAC contract change (`nullable_ohlcv=True`) FIRST via quickmerge, then MDPS via direct-push
  under the dirty-deps carve-out (UAC concurrently mid-edit by the oracle agent). Staged exactly my 8 MDPS files by name
  after a full-index hygiene check.
- **NEXT (loop-closing proof):** re-run `/data-pipeline-check-mdps --data-types derivative_ticker` on a real VM once the
  tarball rebuilds, and confirm it now WRITES objects (was 0) where it failed before. Until then the fix is
  local-runtime-proven, not yet re-proven on the VM tarball path.
- **Bonus finding from the fix:** because deriv is now `supports_prior_day_seed=False`, it no longer reads the shared
  seed context → deriv is REMOVED from the set of adapters exposed to the P0 concurrency bug
  (`/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`). The bug remains for
  trades/book/tbbo/defi.

### 2026-07-20 — LOOP-CLOSE: derivative_ticker fix PROVEN CORRECT on a real VM; end-to-end blocked by a deployment gap (filed)

Rebuilt the MDPS tarball to `09da08c` (all fixes) — verified the latest pointer + SHA-pinned artifact both updated. A
cron had already kept UTL(`80d2497e`)/UAC(`ad317c32`)/deployment/features tarballs current. Re-ran
`/data-pipeline-check-mdps --data-types derivative_ticker` on a real VM (same cell that was 100% broken: CEFI DERIBIT,
auto-day 2024-02-08).

**RESULT — the fix is CORRECT, proven by the CHANGED error:**

- Pre-fix error: `column 'funding_rate_mean' missing` (old adapter didn't emit the columns).
- Post-fix error: `Column 'open' has 2737 NaN/null values but is NOT NULLABLE for data_type=derivative_ticker`.
- => the NEW adapter ran: it emits `funding_rate_mean`/`mark_price_mean`/`index_price_mean` (no more "missing") AND
  leaves empty-window OHLC as NaN EXACTLY per the operator's honest-absence semantics. The fix works.

**But the write still failed — NOT a code bug.** The VM validated against a STALE `deriv_ohlcv` contract (OHLC
non-nullable) even though LDR UAC AND the current `unified-api-contracts-code.tar.gz` (extracted + verified) both have
`nullable_ohlcv=True` at `_candle_contracts.py:318`. **Root cause = a deployment contract-propagation gap** (filed P0
`issues/mdps_vm_stale_uac_contract_propagation_2026_07_20.md`): (1) `launch-mdps-backfill-vm.sh` pins UTL/MDPS tarball
SHAs but NOT `UAC_TARBALL_SHA`; (2) the setup's GCS wheel cache serves a stale UAC wheel that shadows the "always fresh"
editable install, because internal packages keep a static `0.x.y` version across commits. **This is bigger than
derivative_ticker: any UAC schema change can be fully shipped + tarballed and STILL not reach a service VM** — a silent,
fleet-wide correctness gap. Dispatched a deployment-service fix agent (pin UAC_TARBALL_SHA + make the editable install
beat the wheel cache + a boot-time SHA assertion).

**Loop-close status (honest):** derivative_ticker fix = CORRECT + shipped + proven-on-VM-that-it-runs; end-to-end object
write = BLOCKED on the UAC-propagation deployment fix (in flight); re-run queued behind it (issue todo 4). The prod-rate
measurement for the ETA is deferred to that re-run (a VM that writes 0 objects can't measure a write rate). This is
exactly the kind of silent deployment gap the "test all shards on real infra" mandate exists to catch — and it did.

### 2026-07-20 — MIGRATION/ORPHAN ground-truth on EXISTING candle data (no-VM, read-only)

Per the operator's "all migrations done on existing data, no orphans" mandate — ground-truthed the EXISTING prod candle
estate (bounded `gsutil ls`, not a corpus walk) for canonical compliance. Verified full MDPS MVP breadth is well-defined
(CEFI 119 + DEFI 294 + TRADFI 49 = **462 shard cells**; TRADFI timeframe-cascade correct). Two NEW verified orphan facts
folded into `issues/candle_feature_canonical_path_divergence_2026_07_20.md` (addendum iii):

1. **Split-brain candle layout** — the SAME cefi day (`day=2026-05-23`) carries BOTH a `pipeline_mode=batch_tardis/…`
   shape AND a `pipeline_mode`-LESS `timeframe=…`-directly-under-day shape. A pipeline_mode-aware vs -blind reader see
   disjoint subsets of the same corpus. Distinct from the missing-`instrument_type=` finding (that one is id/segment,
   this is partition split-brain).
2. **Root cause of unchecked candle divergence** — the UAC machine oracle `canonical_path_violations()` hardcodes
   `RAW_TICK_DATA_PREFIX="raw_tick_data/by_date/"` and flags EVERY `processed_candles/` path as the SAME structural
   violation (verified by running it on both a canonical and an orphan object). So NO machine oracle governs candle
   canonical shape — which is exactly why the skill's canonical leg re-implements the check (justified) and why the
   durable fix is to EXTEND the oracle to the `processed_candles/`+features namespace (new todo 10 on the issue).

**Resolution is operator-gated** (A/B/C canonical-shape ruling — issue todo 1); autonomous migration of prod candle
objects is out of scope until that ruling lands (a prod-bucket layout change is human-gated). This turn's job was to
GROUND-TRUTH the orphans with machine-checked evidence and point at the durable fix, which is done. Full corpus-wide
counts of the split (issue todo 9) need a bounded per-day sweep, deferred with the ruling.

### 2026-07-20 — UAC contract-propagation P0 SHIPPED (deployment@e978f32d) + published; loop-close re-run launched

Verified the dispatched deployment fix (read all 5 diffs, ran QG myself = GREEN --no-fix 22s, confirmed editable
`__file__` resolution locally to de-risk the fleet-wide boot assertion) and SHIPPED it via quickmerge
(deployment-service@e978f32d, staging-routed). Three fixes closing the stale-UAC gap fleet-wide:

1. Launcher auto-pins `UAC_TARBALL_SHA` (`lc_resolve_tarball_sha`, floats-not-bricks) into VM metadata + pin record.
2. `setup-data-pipeline-vm.sh` purges internal-package wheels from the find-links cache (editable source wins).
3. Boot assertion: `unified_api_contracts.__file__` under `$WORKSPACE` else `exit 1`.

**Published to GCS** (VMs read scripts from GCS, not the tarball; my fix is shell-only so no tarball rebuild needed —
avoided `create-code-tarballs.sh` which would have entangled other agents' uncommitted WIP via the dirty-tree override):

- `gs://…/vm/setup-data-pipeline-vm.sh` = byte-identical to my committed version (md5 f242a3aa…) — Fix 2+3 LIVE on boot.
- `gs://…/code/deployment-service/scripts/vm/{lib/launcher_common.sh,launch-mdps-backfill-vm.sh,launch-features-vm.sh}`
  = my committed versions (Fix 1 live for cron-VM launcher consumers; my local loop-close uses the local launcher).

Flipped propagation-issue todos 1-3 ✅. Launching the derivative_ticker loop-close re-run now (issue todo 4): the setup
script the VM boots is my byte-verified version, and the local launcher auto-pins UAC, so the VM should install the
nullable_ohlcv=True contract and the force leg should WRITE objects (was 0).

### 2026-07-20 22:38Z — CHECKPOINT: two real VMs running, Fix 1 UAC auto-pin CONFIRMED on a live VM

Both loop-close VMs are RUNNING (GCE-verified, not fire-and-forget):

- `mdps-backfill-cefi-pipelinecheck-20260720-213641-a63425` — derivative_ticker re-run (CEFI DERIBIT, auto-day
  2024-02-08).
- `mdps-backfill-cefi-pipelinecheck-20260720-213744-a84603` — trades→candles green-write smoke (CEFI BINANCE-FUTURES).

**Fix 1 (launcher UAC auto-pin) CONFIRMED working on a real VM**: the re-run VM's metadata carries
`UAC_TARBALL_SHA=ad317c32e8db…`, and `git merge-base --is-ancestor 8e58b009 ad317c32` = TRUE — i.e. the launcher
auto-resolved and pinned a UAC that is a DESCENDANT of the `nullable_ohlcv=True` fix (8e58b009). So the VM will install
the contract that permits NaN OHLC on derivative_ticker; combined with Fix 2 (editable beats wheel cache) + Fix 3 (boot
assert), the force leg should now WRITE objects (was 0 due to the stale non-nullable contract). Awaiting the VM
EXIT_STATUS + report to close derivative_ticker end-to-end (issue todo 4) and measure the prod write rate.

### 2026-07-20 ~22:45Z — LOOP-CLOSE re-run OUTCOME: derivative_ticker STILL fails — a DEEPER, SEPARATE bug (enforcer key mismatch), NOT propagation

Honest result: the re-run VM (`…-213641-a63425`, force leg) STILL failed
`SCHEMA_VALIDATION_FAILED: Column 'open' has N NaN/null values but is NOT NULLABLE for data_type=derivative_ticker`
(open/high/low/close, "Skipping upload"), 0 objects written, EXIT_STATUS=0, "20/20 succeeded". So the derivative_ticker
P0 is **NOT closed**.

**But this is NOT a propagation failure — the propagation fix (deployment@e978f32d) is correct and independently
verified**: the VM's metadata pinned `UAC_TARBALL_SHA=ad317c32` (git-proven descendant of the nullable fix 8e58b009),
the boot assertion did NOT fire (workload ran → UAC resolved editable, Fix 3 passed), so the VM ran the CORRECT UAC that
DOES have `nullable_ohlcv=True`. The write still failed for a **different, deeper reason**:

**ROOT CAUSE (hypothesis under adversarial workflow verification — w6kkdobay):** the enforcer
(`unified_trading_library/core/parquet_schema_enforcer.py`) resolves OHLC nullability by
`SchemaDefinition.get_nullable_columns(dimensions)` keyed on `dimensions["data_type"]`, and the error is keyed
`data_type=derivative_ticker` (the SOURCE type). But `uac@8e58b009` set `nullable_ohlcv=True` on the registration keyed
`_deriv_key(_tf)` = `deriv_ohlcv_{tf}` (the AGGREGATED type, `_candle_contracts.py:186,318`). So the MDPS candle writer
hands the enforcer the SOURCE data_type, the aggregated-key nullable contract is never matched, OHLC stays non-nullable,
and the honest-absence NaN rows are rejected. **The UAC fix was applied to a key the writer never queries.** This is the
SAME path≠manifest divergence (canonical issue finding #2) biting the VALIDATION path.

Launched Workflow **w6kkdobay** (ultracode) to exhaustively trace: (A1) what data_type MDPS passes to the enforcer for
EVERY candle source type, (A2) the registered UAC candle keys + nullable status, (A3) how get_nullable_columns handles a
miss, (A4) rule propagation in/out definitively — then synthesize the minimal correct fix + blast radius (does
trades/book/liq/chain also mis-key?) + regression risk, with adversarial verification before any code change. Fix
direction (align MDPS to pass the aggregated key vs. register a source-key alias) is DELIBERATELY not yet chosen — the
workflow decides. Also RE-CONFIRMED the "EXIT_STATUS=0 while 0 objects written" P0 (sibling issue todo 2) on this run.

### 2026-07-20 ~22:50Z — TRADES green-write smoke: PIPELINE WORKS (objects written) + write-rate + a sharp blast-radius insight

The CEFI BINANCE-FUTURES trades→candles smoke (VM `…-213744-a84603`, auto-day 2026-07-05) **WROTE objects
successfully**: run.log `✅ trades complete: 1/1 succeeded in 16.9s (7,615 candles)`,
`cefi processing complete: 1/1 succeeded, 0 errors in 33.9s`, exit_code=0, and the driver report shows **Parquet=1** for
every force timeframe (vs Parquet=0 for derivative_ticker). Polars aggregation (`POLARS AGGREGATED: 1440 1m … 1 24h`).
So the **green writing path is PROVEN** — the MDPS candle pipeline works end-to-end on real data for the common case;
derivative_ticker's failure is SPECIFIC, not a general breakage.

**Write-rate data point (for the ETA):** ~16.9s per instrument-day for all 7 timeframes (33.9s incl. VM setup/manifest
overhead) on a light 1-file instrument-day (7,615 candles). Heavier instrument-days (multi-file, HFT venues) will be
higher; this is a floor, not the DeFi-MVP mean.

**Driver-artifact verdicts (NOT pipeline failures) — matters for skill accuracy:** the trades force legs report `failed`
with `manifest_status_invalid:no_matching_row` even though the object WROTE (Parquet=1). Root cause = the driver's
manifest verify reads the CONSOLIDATED index while the fresh row sits in the leg VM's per-VM shard (sibling issue
`mdps_derivative_ticker_candle_schema_violation` todo 4 — read the per-VM shard first, like the MTDS twin). The skip
legs `failed: skip_signal_not_found_in_run_log` follow from the same manifest-not-consolidated cause (freshness check
saw nothing to skip). Both are DRIVER limitations to fix, not writer bugs — the writer did its job.

**SHARP blast-radius insight for the key-mismatch workflow (w6kkdobay):** trades succeeding does NOT prove the enforcer
key is correct for trades. **trades OHLC is never NaN** (a trade always carries a price), so the non-nullable OHLC check
PASSES regardless of whether the writer queries the source or aggregated key. The key mismatch only BITES candle types
whose OHLC can be legitimately NaN in an empty window — the snapshot/event streams: `derivative_ticker` (proven), and
plausibly `book_snapshot_5`, `liquidations`, `funding_rate`. Note `_candle_contracts.py:293` sets `nullable_ohlcv=True`
on the TRADES contract too (under `_trades_key`), so a mis-key may exist for trades as well — it just never surfaces
because trades has no empty-window NaN. The fix + sweep must cover EVERY empty-window-capable snapshot/event candle
type, not just derivative_ticker.

### 2026-07-20 ~23:05Z — WORKFLOW w6kkdobay VERDICT: root cause CORRECTED (my key-mismatch hypothesis was a red herring)

The adversarial workflow (8 agents, 3 lenses) CORRECTED my hypothesis — exactly why it was run. VERIFIED root cause:

**The failing check is MDPS's OWN pre-upload validator, NOT the UTL StreamingParquetWriter and NOT the UAC key.**
`candle_write_mixin.py:604` (+ byte-identical copy `data_sink.py:118`) calls
`get_schema_for_data_type(data_type, category)` (`output_schemas.py:394`), which gates OHLC nullability on
`category == "prediction"/"sports"` ONLY (`output_schemas.py:420`) — every cefi/tradfi/defi candle falls through to the
NON-nullable `PROCESSED_CANDLE_SCHEMA`. After the LOCF removal, empty derivative_ticker windows genuinely yield NaN OHLC
→ the non-nullable check rejects them → `_validate_candle_schema_before_upload` returns False → upload SKIPPED (0
objects) with NO raise → **that is exactly why EXIT_STATUS=0 with 0 objects** (the pre-upload skip short-circuits BEFORE
the StreamingParquetWriter's strict=True raise is ever reached). The UAC write seam (`lookup_mdps_contract` → aggregated
key `deriv_ohlcv_{tf}`) is ALREADY correctly nullable per uac@8e58b009 — but it's never reached. **So uac@8e58b009 fixed
the wrong layer.** The source-vs-aggregated KEY distinction (my hypothesis) is a RED HERRING here — the pre-upload
seam's nullability is category-gated, so the key never mattered at that layer.

**Blast radius (verified):** the pre-upload validator mis-enforces non-nullable OHLC for EVERY nullable-OHLC candle type
across ALL asset_groups (category-gated, never data_type): cefi trades (`ohlcv_{tf}` nullable), cefi derivative_ticker
(observed), spot trades, tradfi ohlcv, defi `swaps_ohlcv`. Only derivative_ticker fails TODAY because LOCF removal made
its empty windows NaN + the smoke hit one; a genuinely empty trades window would fail identically. **Correctly NOT
affected (must STAY rejecting NaN):** book_snapshot_5 (`book5_ohlcv_{tf}` nullable=False — a NaN covered book window is
a real defect) + liquidations (no OHLC). Fix changes NO object paths / NO manifest keys.

**Verified fix (family A, survived 3 adversarial lenses):** make the pre-upload validator inherit the UAC per-type
nullability instead of re-deciding by category — so book5 stays non-nullable automatically (zero regression), trades/
deriv/swaps become nullable. Both copies fix via the single `get_schema_for_data_type` seam. **REJECTED** the coarse
"blanket-nullable for cefi" patch — it would relax book5 too (data-correctness regression). **Required refinements from
the verifiers:** (1) add a positive aggregation test — a bin with ≥1 observation MUST yield non-NaN OHLC (nullability is
a permission gate, not a per-window guarantee); (2) do NOT claim the fix aligns path==manifest — it only aligns the
VALIDATION key; the object path still uses source data_type, manifest the aggregated key (separate divergence). Also
this fix incidentally makes the EXIT_STATUS=0-while-0-written class less likely for the honest-absence case (the write
now succeeds), though the broader exit-code-lies P0 (sibling todo 2) is still open for genuine failures. Dispatching a
focused MDPS implementation agent with this exact spec.

### 2026-07-20 ~23:20Z — Nullability fix SHIPPED (mdps@d4052e20b) + tarball rebuilt + verified; loop-close re-run #2 launched

Verified the implementation agent's fix (read all 5 diffs, EXECUTED the resolver —
`mdps_ohlc_is_nullable(CEFI, perpetual, derivative_ticker, 15s, DERIBIT)` = **True**, trades = True, **book5 = False**,
uppercase PERPETUAL = True; QG green 15s) and SHIPPED via quickmerge (mdps@d4052e20b). Design: the pre-upload validator
now inherits OHLC nullability from the UAC per-type SSOT (`mdps_ohlc_is_nullable[_for_frame]` → `lookup_mdps_contract` →
`open.nullable`), NOT category — book5/state stay non-nullable automatically (zero regression), lookup-miss → category
fallback (never raises, shard isolation). 12 new tests incl. book5-stays-non-nullable + empty-window-passes.

Rebuilt the MDPS tarball via `refresh_code_tarballs.sh` (clones committed LDR → foreign-WIP-immune): MDPS tarball now
`d4052e20b456`, EXTRACTED + verified it contains the fix (output_schemas `ohlc_nullable`, canonical_writer_shaping
`mdps_ohlc_is_nullable`, both validators threaded). Setup script still byte-intact (md5 f242a3aa). Launched loop-close
re-run #2 (CEFI DERIBIT derivative_ticker, legs force,skip,canonical). EXPECTED: the force leg now WRITES objects
(was 0) because the pre-upload validator resolves nullable=True for derivative_ticker. Awaiting the VM report to close
the P0 end-to-end.

### 2026-07-20 ~23:50Z — ✅ derivative_ticker P0 CLOSED END-TO-END on a real VM (was 0 objects → now 140)

The loop-close re-run #2 (mdps@d4052e20b, UAC ad317c32) PROVED the fix end-to-end. Run.log: **NO schema failures**,
`✅ derivative_ticker complete: 20/20 succeeded, 0 errors, 152,300 candles`, exit 0. Ground-truth on the -test- bucket:

- **140 candle objects** written for day=2024-02-08 (7 timeframes × 20 instruments) — **was 0 pre-fix**.
- **140 fresh manifest rows, ALL `captured`** (0 attempted_failed), `data_type=deriv_ohlcv_15m` (correct aggregated
  key), `row_count=96` (real counts) — read directly from the leg VM's per-VM shard via pyarrow.

The full chain is proven: UAC propagation fix (deployment@e978f32d) → correct nullable UAC (ad317c32) on the VM → candle
nullability fix (mdps@d4052e20b) → the MDPS pre-upload validator inherits per-type nullability → derivative_ticker
honest-absence NaN OHLC is ACCEPTED → objects write. Three P0s found + fixed via this one loop-close, none of which a
green-tick smoke would have surfaced.

**The driver still reports the force leg "failed"** — but that is now a KNOWN DRIVER LIMITATION, not a writer bug: the
manifest verify reads the CONSOLIDATED index (which still holds the STALE `attempted_failed` rows from the pre-fix
failed runs 205051/213641) instead of the leg VM's OWN per-VM shard (which is all `captured`). This is exactly
`mdps_derivative_ticker_candle_schema_violation` todo 4 (read the per-VM shard first, like the MTDS twin's
`_read_per_vm_batch_row`). The `canonical` leg's `non_canonical` verdict (missing `instrument_type=`,
`derivative_ticker`≠`deriv_ohlcv_15s`) is the EXPECTED, already-documented path≠manifest divergence
(`candle_feature_canonical_path_divergence` finding #2), not a failure. Both are correctly SEPARATE verdicts by design.

---

> **History extracted 2026-07-27 (slot-3, plan-hygiene line-cap remediation — parent was 1021 lines, hard cap 1000).**
> The parent's Progress Log had grown two more fully-closed dated entries (zero open `- [ ]` todos each, all items
> either absent or checked `[x]`) since the 2026-07-24 extraction above: the manifest-flush-hypothesis refutation
> follow-through (all 3 of its `NEW todo` items subsequently verified/audited and checked off) and the DeFi-MVP backfill
> ETA measurement writeup (its 1 `NEW todo` item subsequently closed). Moved VERBATIM below; nothing summarized or lost.
> The parent's still-open-todo dated entries (SECOND hypothesis/concurrency bug, GIL, per-unit latency — each carrying
> live `- [ ]` items) were LEFT IN THE PARENT, same rule as before.

### 2026-07-20 — my manifest-flush hypothesis was REFUTED by measurement; the real cost is 1000x bigger

**I was wrong, and the correction is more valuable than the original hypothesis.** I suspected the per-shard manifest
flush was doing an O(n^2) read-modify-write. **Measurement refuted it:**

- `ManifestWriter.flush()` deliberately does NOT force the per-VM rewrite — it DEBOUNCES (50 entries OR 5.0s,
  `_writer_io.py:291` -> `_state.py:706`); only `close()`/atexit force it. Shipped 2026-06-21 as `utl@6b6d53bd`.
- The live log line `(8 total entries, 7 new)` **proves the debounce worked** — 7 rows coalesced into ONE rewrite,
  not 7.
- Measured on the actual shard the profiled run produced: **14 rows / 23,438 bytes**, `to_parquet` = **0.010s**, ~2
  rewrites for the whole run, **~47 KB total rewritten**. The manifest WRITE is ~**0.02s** of a 51.9s run.
- => "Batch the flush" (my Option E) was ALREADY SHIPPED; per-shard-object / WAL / async-flush (A/B/C) would optimise
  **0.02s** while adding durability-relevant moving parts. **All rejected on evidence.** The operator's instinct that
  there must be a better way was right — but the better way is not on the write path at all.

**The REAL cost is a READ amplification** (filed `issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`):
`_publish_emission_check` -> `compute_completeness_fraction` -> `_build_capture_status_map(index)` builds a
**full-corpus python dict over EVERY manifest row x 25 key columns** to serve a lookup whose `upstream_window` is a
literal **1-element list** — **3x per instrument** (ohlcv_1m/1h/1d are policy-gated from `trades`), **unmemoized**, and
each flush calls `_invalidate_index_cache` forcing the next check to re-merge.

Measured scaling: 22,719 rows 0.11s -> 1,454,016 rows **13.14s** (super-linear, 9.04 us/row).

**I VERIFIED the prod index sizes myself** (`gcloud storage ls -l`): **defi 1,579.3 MB**, cefi 159.1 MB, tradfi 77.4 MB,
sports 46.1 MB — against the **0.44 MB TEST index every timing was measured on**.

**⚠️ THIS INVALIDATES MY OWN ETA INPUT.** The 25.9s/instrument-day was measured against a **0.44 MB** index; defi-prd is
**3,614x** larger. On cefi-prd the same path projects to ~75-100s per policy-gated timeframe ~= **4-5 minutes per
instrument**. **Any backfill ETA built on the 25.9s number is optimistic by roughly 10x until this is fixed or the
projection is disproved.** Do not quote the 25.9s-derived ETA to anyone without this caveat.

**Fix is read-path ONLY** (so durability/honest-absence/layout are untouched): F1 filter-then-build instead of
full-corpus map; F2 memoize by index identity; F3 thread the ALREADY-EXISTING `manifest_index=` kwarg so 3 timeframes
share one read. Crash-loss bound identical to today.

**SECOND STANDALONE P0: the defi-prd availability index is 1.58 GB.** Any `read_availability_index` caller on defi
without a column/filter projection is one cache-miss from an OOM. Independent of the above.

- [x] ✅ NEW todo. **VERIFIED 2026-07-27 (slot-9), via code-trace + real-prod log sampling (not live instrumentation)**:
      distinct from slot-7's adjacent todo below (which verified the F1/F2/F3 IMPLEMENTATION is correct + tested) — this
      todo asks specifically whether the gate actually FIRES on a real prod write path, not whether the code is correct
      in isolation. Traced the full call chain: `candle_write_mixin.py` → `write_candle_parquet`
      (`canonical_writer.py:164`) → `mdps_dt = mdps_data_type_key(source_data_type, tf)`
      (`canonical_writer_shaping.py:229`, confirmed via its own docstring example
      `mdps_data_type_key("trades", "1m")     == "ohlcv_1m"`) →
      `_resolve_policy_output_data_type(mdps_dt=..., source_data_type=..., date_str=...)` — the naming genuinely matches
      the gate's exact string checks (`ohlcv_1h`/`ohlcv_1m`/`ohlcv_1d`→`ohlcv_24h`) for a `trades`-sourced candle, so no
      silent naming-mismatch short-circuit exists. Sampled 4 real, currently-active or recently-run PROD backfill VMs'
      `run.log` (`mdps-backfill-cefi-20260726-165959` writing exactly `trades` across `[15s,1m,5m,15m,1h,4h,24h]` — i.e.
      squarely inside the gated timeframe set — plus 3 tradfi backfill VMs): **zero**
      `MDPS emission policy skipped`/`EMISSION_POLICY_CHECK_FAILED` log lines across any of them. Absence of the SKIP
      log is expected+correct when `should_publish_row` stays `True` (the function only logs on a skip or a caught
      exception — a fully-silent happy path is BY DESIGN, not a red flag); absence of the FAILURE log rules out the one
      documented failure mode (`EmptyUpstreamWindowError`/`OSError`/`ValueError`). **Conclusion: no code-level
      short-circuit found; the gate is correctly wired into the real backfill write path and the observed silence across
      a real-prod sample is consistent with it firing successfully every time, not with it being bypassed.** Residual
      honesty note: this is code-trace + log-absence evidence, not a live-instrumented direct observation of the gate
      executing (e.g. a temporary debug log added to a real VM run) — if a future session wants airtight proof, that is
      the next step, but the code-level bypass risk this todo was worried about is not substantiated by anything found
      here.
- [x] ✅ NEW todo. **VERIFIED 2026-07-27 (slot-7)**: already shipped same-day as this todo was written — no new code
      needed. `unified-trading-library@80d2497e` ("perf(manifest): filter-then-build + memoize
      compute_completeness_fraction (16.7x, value-equivalent)", 2026-07-20) implements F1 (pre-filter the DataFrame to
      candidate rows via an exact superset key match, build `_build_capture_status_map` from that slice — unchanged,
      value-preserving) + F2 (memoize per-window keyed by `(id, len, frozenset(keys))`, weakref-guarded, bounded
      FIFO 64) — confirmed still an ancestor of current LDR tip via `git merge-base --is-ancestor`. F3 is
      `market-data-processing-service/app/core/canonical_writer_stamping.py:445` — `_publish_emission_check` accepts
      `manifest_index: object = None` and threads it straight to `publish_with_manifest_lookup` (line 492); its
      docstring documents the correctness nuance (a caller must NOT share a stale snapshot across writes that MUTATE the
      shard being read — MDPS's own `ohlcv_1m` write is the same shard `ohlcv_1h`/`ohlcv_24h` read for their upstream
      check) so a naive share-across-timeframes bug can't be reintroduced. Perf-guard regression test confirmed:
      `tests/unit/test_manifest_completeness.py:658` `test_one_million_rows_under_three_seconds` (1.2M-row corpus,
      comparable to the todo's 1.45M reference, elapsed asserted `< 3.0s`; the shipping commit's own message cites
      0.211s measured, well under the todo's 0.5s target — the 3.0s in the test is a CI-safe assertion budget, not the
      achieved figure). Memoization + value-equivalence also covered: `test_three_calls_one_build` /
      `test_all_four_states_and_absent_key` / `test_duplicate_key_last_write_wins` (same file).
      `bash scripts/quality-gates.sh --no-fix` GREEN (263s) on UTL's current tree, full test suite incl. this file. No
      code change needed — closing as verified-via-code-read + green regression suite.
- [x] ✅ NEW todo. **AUDITED 2026-07-27 (slot-7)** — full-corpus audit complete, ~35-40 bare + defi-reachable call sites
      found across 8 repos, filed as `issues/read_availability_index_bare_defi_callers_2026_07_27.md` with a per-caller
      fix todo list (P0-P3, concrete file:line + column-usage guidance) + a proposed new QG gate to close the "no
      enforcement" gap for good. Highest-risk findings: deployment-api `manifest_source.py:164` (single chokepoint
      feeding ~10 dashboard endpoints), ml-service `manifest_inference_guard.py:46` (live-inference hot path), MTDS
      `reader.py:839` + `orchestrator/__init__.py:509` (per-shard-read + per-backfill-VM-startup, same incident class as
      `mtds_backfill_vm_startup_oom_rc137_2026_07_14`). Confirmed via `codex/02-data/` grep: the projection pattern is
      prose-only guidance, no QG gate enforces it. Did NOT ship the ~15 individual fixes in this session (each needs its
      own direct-read column-usage verification — the audit's own first-pass proposal for `reader.py:839` initially
      omitted `pipeline_mode`, which IS read downstream for the CF-3 lift; a mechanical columns-list copy without
      independent verification risks silent behavior regressions across 8 repos in one sitting). Per the audit-scope
      convention, filed as tracked per-caller todos for individual dispatch rather than one oversized fix-everything
      session.

### 2026-07-20 — DeFi-MVP backfill ETA (MEASURED denominator) + the read-path-fix reframes the fleet size

**THE DELIVERABLE the operator asked for. Denominator MEASURED from UAC SSOT + PROD manifests; per-unit rate is the
measured input; caveats stated.**

**DeFi-MVP candle-backfill denominator ≈ 2.71M instrument-days** (unit = instrument × data_type × day; all 7 timeframes
in ONE pass, so NOT × timeframe). Of DeFi's 27 data_types only 3 produce candles (`needs_candle_processing`):

- `dex_pool_swaps` **2,703,497** (99.8% of the work; UNISWAP_V3 alone = 2.07M = **76%**, then PANCAKESWAP_V3 194k,
  BALANCER 132k, SUSHISWAP_V3 108k, CURVE 72k, AERODROME_V3 31k)
- `liquidations` **6,254**
- `derivative_ticker` **16** (P0-broken → excluded until the fix's tarball lands; only 16 for DeFi anyway)
- **Already-derived (MDPS manifest rows) = 0 → REMAINING = ALL.** (Physical candle objects exist under
  `processed_candles/` untracked by the manifest — the object↔manifest disconnect I filed; the in-flight
  canonical-migration-defi-rebuild may be reconciling it.)
- The naive "instruments × flat-days" (346M) OVERSTATES by ~128× — MDPS only derives days with captured raw ticks, so
  the measured captured-instrument-day count (2.71M) is the honest denominator. It is a GROWING lower bound (raw capture
  still in progress; measured off an immutable mid-migration snapshot, live index ~13% larger).

**CeFi reference ≈ 3.23M total / 2.06M workable** (excl. broken derivative_ticker's 1.17M), already-derived = **6**
(confirms my earlier figure).

**ETA (16 workers/VM = MDPS default; wall = N×rate/(16×fleet)):**

| rate/unit                                 | DeFi 1 VM×16w | DeFi 10 VMs | **DeFi: min VMs for 2 WEEKS** |
| ----------------------------------------- | ------------- | ----------- | ----------------------------- |
| 25.9s (test-measured)                     | 50.8 d        | 5.1 d       | **4 VMs**                     |
| ~260s (prod-projected, PRE read-path-fix) | 507 d         | 50.8 d      | **37 VMs**                    |
| 5s (operator target, needs de-pandas too) | 9.8 d         | ~1 d        | **1 VM**                      |

**🔑 CRITICAL REFRAME — the read-path fix I shipped today collapses this.** The ETA agent used ~260s as the "prod rate"
BECAUSE the `compute_completeness_fraction` full-corpus map-build added ~9-40s/instrument on the prod-sized index.
**That is exactly the term `utl@80d2497e` + `mdps@b4db0af` (16.7x, value-equivalent) removed.** So the realistic
post-fix prod rate is ~25.9s + prod-I/O residual, NOT ~260s → **the DeFi 2-week target now needs ~4-6 VMs, not 37.**
This MUST be confirmed by a real-VM re-measure against a prod-sized index (queued) before being quoted as final — the
16.7x was measured on the map-build in isolation, not yet end-to-end per-instrument on a prod VM.

**Practical backfill plan implied by the numbers:** shard by venue (UNISWAP_V3 is 76% → give it its own fleet lane);
DeFi is NOT Tardis-capped so scale fleet-wide freely; land the derivative_ticker tarball before counting its cefi 1.17M;
turn on R1 `MDPS_DATE_CONCURRENCY` per VM. At the post-fix ~25.9s rate, **all remaining DeFi MVP candles fit in ~2 weeks
on ~4-6 SPOT VMs**, or comfortably under 2 weeks with the de-pandas per-unit work toward 5s.

- [x] NEW todo. [DATA] P0. **DONE 2026-07-27 (slot-10)** — satisfied by
      `manifest_completeness_full_corpus_map_build-001`'s closure this session: a real `/data-pipeline-check-mdps` run
      against real prod raw ticks measured **19.4s** per-instrument-day end-to-end (cefi trades), confirming prod ≈
      19-26s, NOT 260s. See todo 13 above for the resulting fleet-size/ETA/cost delivery.

---

## Extracted 2026-07-27 (slot-3) — 2026-07-20 dated technical narrative (OPERATOR CONTRACT through per-unit latency)

### 2026-07-20 — OPERATOR CONTRACT: "empty window" vs "not fetched yet" are TWO signals (durable rule)

Operator, verbatim: _"the key is knowing what is empty data because theres nothing to aggregate in the window vs not
fetched yet that's where the manifest needs to help and different consumers live and batch will have different ways of
handling depending on their needs"_

**The contract (durable — belongs in `/codex/02-data/honest-absence-downstream-handling.md` at the post-phase codex
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

**Applied immediately to the in-flight P0 fix**
(`/plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md`): the fix must (a) leave empty
bins NaN/0 rather than LOCF-filling them, (b) record `empty_confirmed` + typed reason when the ENTIRE shard-day is empty
rather than writing an all-NaN parquet as `captured`, and (c) document the two-signal contract in-code so nobody
"helpfully" re-adds carry-forward.

- [ ] NEW todo. [SCRIPT] P1. Add the all-NaN-parquet-vs-`captured` assertion to `/data-pipeline-check-mdps` (and the
      features twin where a family can emit an all-null feature frame) as a distinct `content_check=` verdict, so the
      inverse-phantom is caught the same way the phantom is.
- [ ] NEW todo. [DOC] P2. Promote the two-signal table above into `/codex/02-data/honest-absence-downstream-handling.md`
      at the post-phase codex audit (SSOT direction: codex, not this plan).

### 2026-07-20 — MEASURED throughput overturns the codex's compute-bound assumption (ETA input)

Authoritative VM summaries (e2-standard-8, pd-balanced 250GB, cefi DERIBIT, one day, 7 timeframes each):

| run                                 | per-instrument-day | writes        | evidence                                       |
| ----------------------------------- | ------------------ | ------------- | ---------------------------------------------- |
| `trades` (writes SUCCEEDED)         | **25,948 ms**      | ✅ 14 objects | `cefi 51.9s 2 success 0 failed 15,230 candles` |
| `derivative_ticker` (writes FAILED) | 2,105 ms           | ❌ 0 objects  | 12x "faster" ONLY because it never wrote       |

**The candle pipeline is WRITE/IO-BOUND, not compute-bound.** Of the ~25.9s per instrument-day, the polars aggregation
is only **~1.5s** (measured: the `POLARS AGGREGATED: 1440 1m … 1 24h` cascade spans 13:52:30.763→13:52:32.235). The
other ~94% is GCS write + manifest. Per instrument-day the writer emits **7 separate small parquet objects** (one per
timeframe) — small-object overhead dominates.

**This CONTRADICTS `/codex/06-coding-standards/performance-targets.md`**, which classifies `mdps_compute` as
"compute-bound, sublinear-70%" and recommends `c2-standard-16` for the <6h target. On this measurement a bigger CPU SKU
buys almost nothing. **Correct optimization levers, re-ranked by the measurement:**

1. **Write parallelism** — MDPS `max_workers` auto-resolves to `min(cpu_count,16)` = 8 on e2-standard-8, but the
   observed instrument cascade ran effectively serial (`25,948ms/instrument x 2 = 51.9s total`, i.e. sum == total). **If
   the 8 workers are not actually overlapping the writes, that is the single biggest win available** — verify and fix
   before sizing any fleet. (Explains why the codex's serial-day estimate is so large.)
2. **Disk throughput** — pd-balanced 250GB gives ~70 MB/s; `BOOT_DISK_TYPE=pd-ssd` (0.48 MB/s per GB vs 0.28) or a
   larger pd-balanced buys proportionally more write bandwidth. Directly attacks the dominant cost.
3. **Fewer/larger objects** — 7 small parquets per instrument-day is small-object-overhead-heavy. Batching timeframes
   (or instruments) per object would cut write count materially. NOTE: any such change interacts with the chain-bundle
   rule and the canonical path shape — do not change layout without the operator's A/B/C canonical ruling.
4. **Fleet width** — still the reliable multiplier (MDPS is NOT Tardis-capped), but it multiplies a write-bound unit, so
   per-VM disk/write-parallelism must be fixed first or you just buy N x the same bottleneck.
5. **Rust / faster libs** — LOWEST priority for candles on this evidence: the compute is already polars and is only ~6%
   of wall-clock. (The Python-loop hot spots B1 found — whale-detection O(n_intervals x n_ticks), `_carry_forward_ohlc`
   — matter for the `trades` HFT-feature path specifically, not the write-bound aggregate.)

**ETA caveat (honest):** a defensible DeFi-MVP ETA needs (a) the P0 derivative_ticker fix landed (that data_type
currently writes nothing), (b) confirmation of whether the 8 workers actually overlap writes (item 1 — it changes the
answer by up to ~8x), and (c) the DeFi MVP instrument x data_type shard count. Items (a) and (b) are in flight; the
per-instrument-day unit cost above (25.9s serial, write-bound) is the measured input to plug in. Quoting an ETA before
(b) is resolved would be guessing at the dominant term.

- [x] NEW todo. [DATA] P0. **ALREADY ANSWERED 2026-07-20 (this plan's own later entry), RE-VERIFIED 2026-07-27
      (slot-10)**: the `25,948ms x 2 == 51.9s` "serial" reading was a false positive — `processing_stats.py`'s
      `avg_time = duration_seconds / total_instruments * 1000` is `total/N` BY CONSTRUCTION, true for any N regardless
      of parallelism (see the "my SECOND hypothesis refuted" entry below, same plan). Direct code read confirms
      `ThreadPoolExecutor(max_workers=max_workers)` (`batch_workers.py`) genuinely dispatches concurrent futures — the
      2-file smoke run was UNDER-FED (2 futures into 8 slots), not serialized. The real throughput ceiling is 7
      independent serialization points found by that same direct-code-read pass (S1 sequential per-instrument timeframe
      loop — dominant; S2 a process-global per-VM manifest lock; S3 fresh `ManifestWriter`+flush per
      instrument×timeframe; S4 full parquet read-back per write; S5 GIL at the pandas boundary; S6 a hard cap of 2 on
      venue-file listing regardless of `MAX_WORKERS`; S7 the emission-policy lookup on 3/7 timeframes), each already
      tracked as its own follow-up todo in this plan (R1 concurrent date-subprocesses; the shared-seed-context P0
      concurrency bug, `/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`, confirmed still
      `status: open` — NOT yet fixed, so raising in-process concurrency remains gated on that fix landing first). No new
      code change from this todo — it was a measurement-methodology question, now closed with the correct answer on
      record.
- [ ] NEW todo. [DOC] P2. Correct `/codex/06-coding-standards/performance-targets.md`: `mdps_compute` is WRITE/IO-bound
      (measured ~94% write, ~6% polars), not compute-bound; the c2-standard-16 recommendation does not follow.

> The "CORRECTION: the candle write bottleneck is NOT the MTDS 50GB-disk issue" entry (2026-07-20, no open todos) was
> extracted verbatim to `/plans/archive/2026_07/data_pipeline_check_mdps_features_history_2026_07_24.md`.

### 2026-07-20 — operator: manifest durability is a FALSE tradeoff + scope expansion

**(1) "must be a better way to do this right? without killing the data loss think hard"**

My earlier framing ("durability-vs-throughput tradeoff") was WRONG and I corrected it. The cost is not flush FREQUENCY —
it is that each flush does a **read-modify-write of a GROWING file** (`_index/per_vm/{vm}.parquet`), so total flush work
is **O(n^2) in shards-per-VM** while STILL only guaranteeing "SIGKILL loses <= 1 shard". **The current design is
strictly dominated: simultaneously slow AND lossy.** A better design is faster AND loses nothing. Dedicated design agent
dispatched to validate against the code and rank:

- **A. Per-shard immutable object** (`_index/per_vm/{vm}/shard-{seq}.parquet`) — O(1) per shard, O(n) total; durability
  IMPROVES to **zero shards lost**. Extends the EXISTING `_index/per_vm/` merge-on-read pattern one level down. Key
  check: does the consolidator/`read_availability_index` glob a PREFIX (nearly free) or expect exactly one file per VM?
- **B. Write-ahead receipt + single materialisation** — tiny O(1) receipt per shard; full parquet once; replay on crash.
- **C. Async flush off the critical path** — keeps per-shard durability, overlaps flush with the next shard's compute.
  ORTHOGONAL, combinable with A/B; changes the guarantee not at all.
- **D. Co-locate the manifest row with the candle write** (no extra round-trip) — biggest layout change, GATED on the
  pending canonical A/B/C ruling.
- **E. Batch per instrument** — FALLBACK only (this was my original, inferior suggestion); requires stating a new
  crash-loss bound.

HARD CONSTRAINT carried into the design: manifest COMPLETENESS is already a live problem (cefi day=2026-04-14 has 20,734
candle objects vs 6 MDPS manifest rows corpus-wide), so the design must cut flush COST without ever reducing row COUNT
or making rows easier to lose.

**(2) Scope expansion (operator):** _"keep going and improving mdps and dont forget to do all AG that are relevant (not
the ones already in candles) and do features service across all shards too"_

- MDPS must be exercised across **ALL relevant asset_groups**, prioritising the ones that do **NOT** already have
  candles (i.e. the REMAINING work) rather than re-proving the covered ones. Requires first enumerating the
  candle-coverage gap per (ag, venue, data_type, timeframe) from the manifest — that enumeration is also the ETA
  denominator, so it does double duty.
- features-service must be exercised across **ALL shards** (all 8 families x their valid asset_groups, ~29 viable cells
  per the launcher's `_is_viable_cell` matrix).
- Sequencing reality: the features sweep is partly gated on candles existing (candle-dependent families will honestly
  report `no_captured_input_for_window` until the candle backfill runs) — so MDPS coverage leads, features follows, and
  the honest-gap verdicts in between are themselves the signal, not a failure.

- [x] NEW todo. ✅ [DATA] P0. **DELIVERED 2026-07-27 (slot-15)** — Enumerate the candle-coverage GAP per (asset_group,
      venue, data_type, timeframe): which cells ALREADY have candles vs which do not. **Denominator**
      (`enumerate_mdps_shards` × `_valid_timeframes`, all 5 AGs): **3,125 candle-eligible cells** — CEFI 819, DEFI
      1,974, TRADFI 273, SPORTS 30, PREDICTION 29. **Real GCS ground truth** (bounded delimiter-descent under
      `processed_candles/by_date/` — NOT a full-corpus walk; used instead of a pure manifest census because the manifest
      is KNOWN to undercount — todo 3 above found 20,734 real cefi candle objects vs 6 manifest rows on one day),
      day-partitions / most-recent-day / MDPS-service manifest rows (axis-census) per AG: DEFI 1,148 days / 2026-07-26
      (producing daily) / 503 manifest-too-large-for-one-request (see below); SPORTS 1,941 days / 2026-07-26 (producing
      daily) / 120,792 rows; TRADFI 884 days / 2026-07-22 / 23,810 rows (CME 22,086/NYSE 1,651/FX 73); CEFI 342 days /
      2026-07-21 / 75 rows (HYPERLIQUID 73/BITGET-FUTURES 2); PREDICTION 247 days / **2026-01-14 — STALLED ~6mo, no new
      days since** / 15,558 rows (KALSHI/POLYMARKET, all historical). Per-day breadth is narrow vs. the denominator:
      DEFI's 2026-07-26 sample covers only `pipeline_mode=batch_onchain_subgraph` + `data_type=dex_pool_swaps` +
      `instrument_type=POOL`, for 2 venues (PANCAKESWAP_V3, UNISWAP_V3) across 7 timeframes (DEFI's other data_types
      show ~0 recent activity); CEFI's 75 manifest rows cover only 2 of many venues and 2 of 6 candle data_types.
      **Verdict**: DEFI (63% of all cells, narrow real coverage) and CEFI (819 cells, near-empty manifest) are the
      biggest genuine gaps — prioritize these for the next `/data-pipeline-check-mdps` run + todo 15's backfill.
      TRADFI/SPORTS are comparatively well-covered (daily production current through this week). PREDICTION's pipeline
      appears to have STOPPED producing new days since 2026-01-14 — an operational question, filed below. **Known
      limitation (honest, not swept)**: a full per-cell DEFI census could not be completed safely this session — an
      in-process `read_availability_index` attempt grew to 15.8 GB RSS and was SIGTERM'd by main-agent (shared-host load
      avg hit 50); the deployment-api `axis-value-census` Cloud Run endpoint also 503'd on DEFI's manifest size. Per
      `reconciliation-census-and-compute-tiers.md`, this belongs on a Tier-2 SPOT VM — filed below.

- [ ] NEW todo (surfaced 2026-07-27, slot-15). [DATA] P1. Run a DEFI-specific per-cell (venue,data_type,timeframe)
      candle-coverage census on a Tier-2 SPOT VM — both the in-process `read_availability_index` read and the
      deployment-api `axis-value-census` endpoint failed on DEFI's manifest size this session (see todo above).
- [ ] NEW todo (surfaced 2026-07-27, slot-15). [DATA] P2. Investigate why PREDICTION's MDPS candle pipeline stopped
      producing new `processed_candles/by_date/day=` partitions after 2026-01-14 (247 total days, none since) — an
      operational question, not a backfill-scope gap (only 29 cells total for this AG).
- **[DATA] P0. CANCELLED — 2026-07-27 (slot-9): consolidated into todo 8's post-split follow-up todo** (see the "SPLIT
  2026-07-27 (slot-9, operator-ruled Option B on BLK-243a969b)" entry higher in this Todos section). This todo's scope
  ("run `/data-pipeline-check-mdps` across all relevant AGs") is a strict SUBSET of that follow-up's scope ("all AGs ×
  venues × data_types × timeframes") — same skill, same underlying blocker
  (`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`, gated on prerequisite
  `mdps-e2e-shared-host-teardown-fixed`), same done-when. Tracking it as a separate todo risked two AO-dispatched
  workers independently re-attempting the identical blocked skill run without either being aware of the other's findings
  (the exact collision class flagged elsewhere in this plan's Progress Log). Cancelled here rather than duplicated; the
  live scope + gate condition live in the one post-split todo. NOT re-attempted this session — no value in a 6th
  reproduction of an already-diagnosed, still-open P1 blocker. Original text (was
  `- [ ] NEW todo.     [DATA] P0. Run /data-pipeline-check-mdps across all relevant AGs NOT already in candles.`).
- [ ] NEW todo. [DATA] P0. Run `/data-pipeline-check-features` across ALL shards (8 families x valid AGs). **`--day`
      RULED 2026-07-27 (BLK-f2039422, main)**: `--day 2026-07-05` — matches the sibling `/data-pipeline-check-mdps` run
      in this plan that auto-resolved to + direct-GCS-verified this exact day 4-5x (a settled, high-coverage day, no
      feature-computation-lag risk); NOT a synthesized default (honors the skill's own hard rule). If the shared-host
      session-teardown (`shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`, still open) hits mid-run,
      `/progress` it as the known P1 rather than blind-retrying.

### 2026-07-20 — ✅ SPOT preemption auto-recovery was NOT fleet-wide; now it is (`deployment-service@c79f984`)

Operator: _"vms are SPOT and need to recover themselves if they go down via auto recovery think we have that for some
vms already so propagate if not there."_ **They were right to doubt it — and the gap was much wider than "some".**

**MEASURED (I verified the headline myself, independently of the agent): 58 launchers pass `--provisioning-model=SPOT`;
only ~10 emitted the `vm-logs/{vm}/PREEMPTED` blob. ~48 SPOT launchers were preemption-BLIND.** The
`RelaunchPreemptedVm` machinery is well-built and correct — but its **trigger** was missing, so a preempted VM
classified as `EXIT_NONZERO`/`GONE_NO_CAPTURE` and **PAGED a human** instead of auto-recovering.
`/codex/05-infrastructure/spot-vms-for-backfill.md` asserts the signal is "wired fleet-wide via `launcher_common.sh`" —
**that claim is false and the codex is now stale** (todo below).

**The mechanism (verified end-to-end):** VM shutdown checks `instance/preempted` → writes `PREEMPTED` blob →
`_gcs.is_vm_preempted` + `read_launch_params` + `read_progress_checkpoint` → `classify_terminated_vm` checks `preempted`
BEFORE exit_code → `DP_VM_PREEMPTED` (AUTO_RECOVER, DP-VM-007) → `RelaunchPreemptedVm.relaunch()` replays
`LAUNCH_PARAMS.json`, re-resolves `*_TARBALL_SHA` pins, budget 48/day/prefix. Resume overrides `START_DATE` to
`last_completed_date` **only if `monotonic=true`**; a `--force` run with non-monotonic/absent checkpoint still **PAGEs**
`force_run_not_replayable` — never silent. `PROGRESS.json` emission was ALREADY fleet-wide (UTL `record_vm_progress` +
`vm-exec-with-gcs-tee.sh`), which is why only the trigger was missing.

**CORRECTION (2026-07-25):** "ALREADY fleet-wide" is not exceptionless —
`plans/active/lst_rate_honest_coverage_2026_07_21.md` (2026-07-21/22) documents a concrete production counter-example:
`launch-mtds-pyth-lst-backfill-vm.sh` does NOT write a `PROGRESS.json` checkpoint (that session's own correction:
"unlike the newer PROGRESS-checkpoint contract referenced in CLAUDE.md — that's a DIFFERENT, newer launcher family"),
and the VM preempted after ~10hrs requiring a manual manifest-derived resume rather than an auto-resume via checkpoint.
Root cause of why this specific launcher lacks coverage despite booting via the shared `setup-data-pipeline-vm.sh` seam
is not yet diagnosed anywhere in the corpus — flagged here rather than swept into
`issues/vm_fleet_preemption_autorecovery_gap_2026_07_23.md` (that doc tracks the separate early-shutdown-script
`PREEMPTED`-signal blind spot, not this checkpoint-emission gap).

**Fix:** `setup-data-pipeline-vm.sh` now installs `uts-preemption-signal.service`, a systemd unit mirroring Google's own
`google-shutdown-scripts.service`, writing the same blob with the same `preempted=true` gate. Chosen because gcloud
accepts only ONE metadata `shutdown-script`, so a unit **composes** with the ~10 launchers already emitting it inline
rather than colliding. Every blind launcher boots from this one seam — including **both launchers I extended for these
skills** (`launch-mdps-backfill-vm.sh`, `launch-features-vm.sh`) and `launch-mdps-sharded-backfill.sh`. Also registered
**`mdps-sports-`** in BOTH registries (previously emitted by the sharded launcher but registered in neither →
unmonitored AND unrecoverable; sports confirmed genuinely in scope via its dedicated `STALL_TIMEOUT_SEC` +
`STALL_PROGRESS_REGEX` against a live run.log). New guard test: **no SPOT launcher may be preemption-blind**. **Safety
is structural** — inert on live/forward/cron/paper VMs because they are on-demand and GCE never sets `preempted=true` on
them; no exclusion list needed. QG GREEN (339s, 2781 passed/5 skipped).

**Shipped by DIRECT PUSH under the closed dirty-deps carve-out** (UAC concurrently mid-edit by my own P0 agent, so
quickmerge's dep pre-flight could not pass). **Multi-agent hazard hit and handled**: a concurrent agent had staged 13
foreign files into the shared index (17 staged, 1,556 insertions); caught it via the mandatory no-path-arg
`git status`/`git diff --cached --stat`, `git reset`, re-staged ONLY my 4 by name. Foreign work never entered the
commit.

**RESIDUAL RISKS (carried forward, not swept):**

1. **Arg-required launchers still cannot actually recover** — `launch-features-vm.sh` exits 2 without
   `--feature-family`/`--asset-group`, and the relauncher passes ENV only. Result is a loud CRITICAL
   `DP_VM_PREEMPTED_NO_RELAUNCH`, not silence — but not recovery either. **This directly affects the features backfill**
   and is the next thing to close (needs `lc_write_launch_params` adoption or env-arg support).
2. **Manual delete ≈ preemption exposure now spans ~48 more launchers.** A prior incident (manual delete → relaunch →
   two VMs 469ms apart → Tardis 403 lockout, 1181 rejections) is the precedent. Mitigated by the `preempted=true`
   metadata gate (a manual delete does not set it), the Tardis guard, and the 48/day budget — but worth review before
   the next wide SPOT wave.
3. **Relaunch scope amplification**: `launch-mdps-sharded-backfill.sh` with no args defaults to all 5 AGs x all years —
   a preempted shard could relaunch dozens of VMs. Absorbed by presence-skip (cost, not corruption); real fix is the
   `lc_write_launch_params` rollout.
4. **Not runtime-proven**: `bash -n` clean + guard tests pass, but only a live SPOT reclaim proves the unit fires.
5. `launch-prediction-features-vm.sh` (broken: packages a deleted repo, no SPOT, 50GB disk) deliberately NOT touched —
   it is operator-gated A/B/C in `issues/mdps_features_deadcode_consolidation_2026_07_20.md`.

- [ ] NEW todo. [DOC] P1. Correct `/codex/05-infrastructure/spot-vms-for-backfill.md`: the preemption signal was NOT
      wired fleet-wide via `launcher_common.sh`; it is now installed by `setup-data-pipeline-vm.sh` as a systemd unit.
- [ ] NEW todo. [SCRIPT] P1. Close residual risk 1 — make arg-required launchers relaunchable (features especially).

### 2026-07-20 — my SECOND hypothesis refuted, and a P0 concurrency bug that BLOCKS the speed lever

**Refuted (again, by measurement — recording plainly):** I claimed `25,948ms x 2 == 51.9s` was a "smoking gun" for
serial execution. **It is an arithmetic identity.** `processing_stats.py:468`:
`avg_time = stats.duration_seconds / stats.total_instruments * 1000` — the log line is `total/N` by construction, true
for ANY N. It proves nothing about serial-vs-parallel. **Verified by direct read.** Two of my hypotheses have now been
killed by measurement (the O(n^2) flush, and this) — both times the corrected answer was more valuable.

**What is ACTUALLY true (measured from code):**

- The `ThreadPoolExecutor` IS used (`batch_workers.py:370`) and was **UNDER-FED, not serialised** — 2 futures into 8
  slots, 6 workers idle.
- Parallel axis is the instrument FILE only. **Dates, asset_groups, data_types and TIMEFRAMES are all serial loops.**
- **The 7 timeframe writes per instrument ARE strictly sequential** (`live_workers_chain.py:314`) — each iteration does
  encode -> finalize -> read-back -> upload -> manifest -> flush before the next starts. **That is the 10.7s gap.**
- Serialisation points found: S1 timeframe loop (dominant) · S2 a process-global per-VM manifest shard LOCK (one path
  per VM, so every worker thread contends on ONE lock; critical section = download+read_parquet+merge+to_parquet+upload)
  · S3 a fresh ManifestWriter + flush per (instrument x timeframe) · S4 a full parquet READ-BACK per write (14x on this
  run) · S5 the GIL at the pandas adapter boundary · S6 a hard cap of 2 on venue-file listing regardless of MAX_WORKERS
  (`cloud_data_provider.py:277`) · S7 the emission-policy manifest lookup on 3 of 7 timeframes — **independently
  corroborating the other agent's `compute_completeness_fraction` finding**.

**🔴 P0 CONCURRENCY BUG — filed `/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`. I VERIFIED
BOTH HALVES BY DIRECT READ.** `candle_write_mixin.py:406-411` `_set_prior_seed_context` writes
`self._seed_category / _seed_date_str / _seed_input_venue / _seed_underlying / _seed_pipeline_mode / _seed_frame_cache`
onto the **SHARED** orchestrator instance, while `batch_workers.py:332-335` submits `self._process_instrument_file` to
the pool. With `max_workers>1` over a HETEROGENEOUS file list (multiple venues/underlyings/pipeline_modes in one
data_type — the NORMAL backfill shape) a thread reads another thread's context and resolves the prior-day carry seed
from the **WRONG GCS path**. **SILENT** — wrong leading-bin prices, no crash, no `attempted_failed`, no manifest signal.

**Why this matters more than a normal bug: it BLOCKS the primary speed lever.** The pool being under-fed means the
obvious fix is "raise concurrency" — and raising concurrency is EXACTLY what triggers this corruption. So the
correctness fix is a hard PREREQUISITE for the throughput work, not a parallel task. It was invisible in my own smoke
run only because both files were DERIBIT/same-day/same-mode, so the clobbered values were identical — any homogeneous
single-venue test passes. The adapter itself is safe (`base_adapter.py:802` returns a fresh adapter per call).

**Biggest lever (R1, from the probe):** run K **date-subprocesses** concurrently (`process_handler.py:783-807` is a
serial `while` over dates). ~K x wall-clock, and **LOW risk precisely because separate processes sidestep the shared-
`self` bug entirely** while keeping the C-arena reclaim `--subprocess-per-date` exists for. That is the months->weeks
lever, and it does NOT require raising in-process `max_workers` first.

- [x] ✅ NEW todo. [SCRIPT] P0. **VERIFIED 2026-07-27 (slot-8): already shipped, duplicate of already-completed work.**
      `/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`'s own todos 1+2 are `[x]` SHIPPED
      `market-data-processing-service@b3376b8` ("fix(mdps): thread-safe per-call seed context (P0) + opt-in concurrent
      date-subprocesses (R1)"), confirmed still an ancestor of current LDR tip (`git merge-base --is-ancestor`). Direct
      code read of `market_data_processing_service/app/core/candle_write_mixin.py` confirms zero remaining
      `self._seed_*` writes — replaced by a frozen `SeedContext` value object threaded per-call through
      `_process_instrument_file` → `_seed_adapter_for_instrument`, exactly the fix direction that issue doc specified.
      `tests/unit/test_seed_context_thread_safety.py` exists (the regression test that fails-on-old/passes-on-new +
      meta-guard the issue doc's todo 2 describes). No code change needed. The issue doc's own todo 3 (blast-radius
      assessment on existing candle data) remains separately open — not this todo's scope, tracked at
      `/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md` directly, matching the "NEW todo.
      [DATA] P1. Blast radius..." item just below.
- [ ] NEW todo. [DATA] P1. Blast radius: did any PAST prod MDPS run use max_workers>1 over a heterogeneous list? If so
      those shards may carry wrong leading-bin seeds and need re-derivation.
- [x] ✅ NEW todo. [SCRIPT] P0. **WIRED 2026-07-27** — R1 shipped (mdps@b3376b8) but unused; wired opt-in
      `--date-concurrency` into both launchers, default=serial. deployment-service@96be4cf

> The "✅ P0 derivative_ticker FIXED + shipped" entry (2026-07-20, no open todos) was extracted verbatim to
> `/plans/archive/2026_07/data_pipeline_check_mdps_features_history_2026_07_24.md`.

### 2026-07-20 — GIL question ANSWERED with measurement: yes it's the GIL; the throughput fix is MULTIPROCESSING (R1)

Operator: _"check if could be GIL in which case code needs refactor to use multi processes rather than concurrency
within a single python process."_ **Measured, decisive: YES.**

**The decisive benchmark** (real UTL `_build_capture_status_map` — VERIFIED a pure-Python `for` loop over
`_ROW_KEY_COLUMNS`, `manifest_completeness.py:169 — on ThreadPool vs ProcessPool, K=1..8):**

- Case A (the pure-Python map-build, GIL-HELD): **threads get WORSE with more workers — per-worker speed 0.67 → 0.11x
  (~1/K), wall EXPLODES 6.4s→41.5s** for the same work. Processes stay near full speed (0.86→0.52x); K=4 processes 12.3s
  vs threads 21.2s (**1.7x**). Textbook GIL. The thread-side degradation is the proof and needs no process-pool (the
  process side just confirms the alternative works; I independently confirmed the thread-side result is unambiguous).
- Case B (polars `group_by_dynamic`) + Case C (pandas numeric `.agg`): on the SAME thread pool, walls stay FLAT — they
  RELEASE the GIL. **So threads help the GIL-released fraction (I/O, polars, numeric agg) and do NOTHING for the held
  fraction.** Correction to a prior assumption: vectorized pandas numeric `.agg` RELEASES the GIL; the genuinely
  GIL-held pandas cost is the Python-callback/loop code (`_scatter_series`, `_carry_forward_ohlc`, HFT helpers) + the
  **3 redundant `.to_pandas()` per write** (`candle_write_mixin.py:519/571/618` — confirmed).

**Architecture (recommended):**

- **R1 (PRIMARY) — date-level multiprocessing:** the machinery ALREADY exists (`_run_date_as_subprocess`,
  `process_handler.py:675`) but the date loop dispatches SERIALLY (`:785`, blocking `subprocess.run`). Change serial →
  bounded-concurrent dispatch (Popen/ProcessPool of size K over dates). Separate processes → no cross-date GIL
  contention; C-arena reclaimed per child; **dates (~2400 multi-year) >> cores so it saturates any VM/fleet**; LOW risk
  (reuses tested subprocess code, only the dispatch loop changes). This is the "2 weeks" throughput lever.
- Keep the in-date `ThreadPoolExecutor(8)` — it profitably overlaps the GIL-RELEASED work within a date (Case B proves
  it).
- **R2 (secondary) — instrument-level ProcessPool** at `batch_workers.py:370`, only for single-DATE-heavy latency
  (one-day recompute), where date fan-out = 1.

**⚠️ NUANCE I must correct in the GIL agent's report:** it said R1 "fixes the shared-`self` seed bug for free." That is
only PARTLY true. R1 fixes CROSS-date races (different dates = different processes), but WITHIN one date the in-date
thread pool still runs over the shared `self`, so a date with heterogeneous files (multi-venue/underlying) still races.
**The seed-context fix (per-call value object) is REQUIRED independently of R1** — do not rely on R1 to cover it. (R2
WOULD cover it, since each instrument gets its own process, but R2 isn't the backfill recommendation.)

**The two operator targets are DIFFERENT problems — stated explicitly:**

- **"5s PER instrument-day" (LATENCY): multiprocessing buys 0% of this.** It needs per-unit Python-cost cuts: (1) the
  emission-check read-path fix (removes ~9-40s of GIL-held Python per PROD instrument — measured ~3-13s x ~3 calls),
  then (2) de-pandas the adapter (collapse the 3 redundant `.to_pandas()`, vectorize `_scatter_series`/
  `_carry_forward_ohlc`/HFT callbacks). 5s is a per-unit optimization program, reachable via those fixes.
- **"everything in 2 weeks" (THROUGHPUT): exactly what multiprocessing buys.** R1 at K workers x M VMs → per-unit /
  (K.M). Even at the un-optimized ~25.9s TEST residual, 16 workers ≈ 1.6s amortized; add VMs linearly. Reachable — BUT
  the emission-check read-path fix is a PREREQUISITE, because under a process pool each of K processes rebuilds its own
  1.45M-row dict → K copies in RAM → RAM caps K and stalls the fan-out. Multiprocessing AMPLIFIES the read-path bug.

**Sequencing that follows from the measurement:** (1) emission-check read-path fix [IN FLIGHT] — prerequisite for both
targets; (2) seed-context per-call fix — correctness prerequisite for in-date concurrency; (3) R1 concurrent
date-subprocess dispatch — the 2-week throughput lever; (4) de-pandas the adapter — the remaining per-unit latency to
hit 5s; (5) re-measure on a real VM against a PROD-sized index to PROVE the numbers.

- [ ] NEW todo. [SCRIPT] P1. Implement R1: bounded-concurrent `_run_date_as_subprocess` dispatch (the 2-week throughput
      lever). Gated on the seed-context fix for in-date safety.
- [ ] NEW todo. [SCRIPT] P2. De-pandas the per-write path: collapse the 3 redundant `.to_pandas()`
      (`candle_write_mixin.py:519/571/618`) + vectorize `_scatter_series`/`_carry_forward_ohlc`/HFT callbacks — the
      remaining per-unit latency cut toward 5s.

### 2026-07-20 — per-unit latency: safe wins + HFT vectorization SHIPPED; vol_clock + write-I/O floor characterized

De-pandas / HFT vectorization work, all BYTE-IDENTICAL (these feed the batch=live ε=0 spine, so allclose is not enough):

- `mdps@0ba3a72`: collapse redundant `to_pandas` 3->2 (schema+write share one conversion) + vectorize `_scatter_series`
  (170x, 9 edge cases proven). Honest note: safe plumbing alone = ~0.12% — it does not move the needle.
- `mdps@09da08c`: vectorize `_detect_whale_trades` (148x at 15s; **removes an O(n_intervals x n_ticks) throughput
  CLIFF** — a liquid instrument's whale loop measured 1791ms and scales with ticks, a real backfill hazard, not just
  latency) + `_calculate_tick_direction_momentum` (3.4x). 87/87 byte-identical each. **The agent caught + corrected its
  own spec: the prescribed `np.add.at` momentum vectorization is NOT bit-exact (few-ULP drift vs np.average on nearly
  every multi-tick group); only a per-interval numpy `.sum()` on the contiguous slice is 0-ULP.** ~2-2.5s saved per
  liquid instrument-day.

**Honest per-unit accounting (measured):** ~25.9s -> ~20-22s after the HFT vectorizations. **The 5s per-unit target is
NOT reachable without also attacking the ~20s per-write GCS/manifest I/O floor** (batch the 7 timeframe writes into
fewer objects) — which interacts with the canonical A/B/C ruling and is a bigger architectural change.
`_carry_forward_ohlc` (1.9ms, coupled honest-absence logic) and `_calculate_volume_clock_features` (biggest single
callback ~2.5s but the most intricate milestone-crossing logic) are left as REVIEWED follow-ups — deliberately not
gambling the just-fixed working adapters for the last seconds. **The 2-week THROUGHPUT target is already met by R1 + the
read-path fix (4-6 VMs); the 5s LATENCY target is a separate, fully-characterized optimization program (HFT done,
write-batching + vol_clock remaining).**

- [ ] NEW todo. [SCRIPT] P2 (reviewed follow-up). Vectorize `_calculate_volume_clock_features` (~2.5s, the largest
      single HFT callback) WITH a dedicated byte-identity test for the milestone-crossing edge cases (single-tick
      groups, zero total volume, <2 milestones). Prototype/plan in `de-pandas` agent output.
- [ ] NEW todo. [SCRIPT] P2. Write-batching: collapse the 7 per-timeframe parquet writes per instrument-day into fewer
      objects to attack the ~20s I/O floor (the remaining bulk of the 5s-target gap). GATED on the canonical A/B/C
      ruling (it changes the object layout).

### 2026-07-27 — todo 8 PARTIAL: CEFI force-leg mechanism re-proven 4x; skip-proof + other AGs blocked by session teardown

Scoped `/data-pipeline-check-mdps` to CEFI:BINANCE-FUTURES:trades (day=2026-07-05, auto-day-resolved) as a
representative cell before attempting the full 448-cell all-AG matrix (unscoped run is explicitly warned against by the
skill itself). **Force leg independently re-proven correct on real infra 4 separate times** (VMs
`...pipelinecheck-20260727-022633`, `-023618`, `-031200`, `...manualskip-033855` — all `exit_code=0`, all derive the
identical 7,615 candles across the 7 timeframes). The automated skill driver (`pipeline_e2e_check.py --legs force,skip`)
could not be kept alive long enough by this interactive session to produce a clean automated skip-proof verdict — the
local process was killed mid-run 4 times across different backgrounding strategies (plain `run_in_background`,
`nohup&disown`, foreground-with-auto-background, `setsid`). Full findings + recommended fixes:
`/plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`. A secondary, minor
finding (byte-identical candle written to two different paths — with/without `instrument_type=` segment — across
consecutive force runs) is tracked separately:
`/plans/archive/issues/mdps_candle_path_instrument_type_segment_nondeterministic_2026_07_27.md`.

**Disposition:** todo 8 stays OPEN (not flipped) — the force-leg _mechanism_ is proven, but the todo's actual scope
("every MVP candle shard, all AGs") and even a single clean automated skip-proof are not yet met. Report written this
session: `plans/audit/results/data_pipeline_e2e_check_mdps_2026_07_05.md`.

### 2026-07-27 (slot-9) — one of todo 8's two identified blockers FIXED; todo 8 itself still OPEN

Dispatched to continue todo 8. Rather than re-attempt the exact same 4x-failed backgrounding strategies (harness
`run_in_background`, `nohup&disown`, foreground-auto-backgrounded, `setsid` — all already exhausted per the entry
above), root-caused and fixed the CONCRETE bug behind attempt 3's `launcher_script_timeout` false-failure:
`unified-trading-library@137e219c` — a `subprocess.TimeoutExpired` on the launcher-script client-side wait
(`_LAUNCHER_SCRIPT_TIMEOUT_SEC=120s`) previously aborted the whole shard immediately with ZERO retry, even though the
identical `_vm_is_present`-gated retry machinery already existed for ordinary nonzero launcher exits (added for the
exact same "gcloud create succeeded server-side after the client-side confirmation wait already gave up" failure mode).
Now a timeout is converted to a synthetic nonzero-exit result and flows through that same retry path. 3 new regression
tests, QG green (226s). Full detail + evidence:
`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` todo 3 (flipped).

**Disposition:** todo 8 stays OPEN — this fixes one of the two identified blockers (the launcher-timeout false-failure),
not the other (the session/container teardown killing the long-running driver process itself, still under P1
investigation, unresolved). A from-scratch automated run may now get further before hitting the teardown wall, but
re-attempting the full multi-hour/462-cell matrix was out of scope for this 1-hour task; the next attempt should happen
once the teardown root-cause (item 1 below) is resolved, or from a longer-lived host if the teardown proves to be this
interactive-session-class specific.

### 2026-07-27 (slot-12) — todo 11 PARTIAL: caught + fixed a P0 unsafe-rebuild bug blocking the candle-manifest orphan reconciliation; DEFI candle-manifest measurement corrected

Dispatched to todo 11 (cross-repo orphan/lineage audit + migrate to zero orphans). Scoping how to execute the
already-open `issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` (CEFI candle files orphaned by
pre-fix-era OOM crashes) surfaced a genuine, previously-uncaught **P0 data-loss risk in the recommended remediation
itself**: `unified_trading_library.manifest_writer.rebuild_manifest_from_canonical_paths()` builds its output purely
from a `prefix`-scoped GCS walk and uploads that as the bucket's WHOLE consolidated manifest index — on the
`market-data-tick-{ag}-prd` buckets, which co-locate MTDS's `raw_tick_data/` and MDPS's `processed_candles/` under ONE
index, a prefix-scoped call (exactly what the reconciliation doc recommended) would have silently deleted essentially
the entire raw-tick manifest for that asset_group to backfill a much smaller candle-orphan set. **Caught before any VM
launched — nothing was actually deleted.** Full analysis, evidence, and fix:
`issues/rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md` (new, P0). Shipped the fix:
`unified-trading-library@2352e7c8` — added `merge_manifest_from_canonical_paths()`, an additive sibling that only adds
genuinely-missing `(day, venue, chain, instrument_type, data_type)` rows and preserves every existing row (including
rows for other prefixes) verbatim; 2 new regression tests directly proving the safety property (a pre-existing
out-of-prefix row survives the merge, both in the returned frame AND in what actually lands in GCS) plus an idempotency
test. Corrected `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`'s recommended-fix section to route
through the new additive function instead of the unsafe call, and to re-verify the bucket's non-candle row count is
unchanged before trusting a future run.

**Also corrected a stale measurement feeding this same effort**:
`candle_feature_canonical_path_divergence_2026_07_20.md` todo 7's "candle manifest never systematically populated" claim
(cefi=6/defi=0/tradfi=73/prediction=168 rows, 2026-07-23) used the WRONG `data_type` vocabulary (the aggregated
`ohlcv_*` family) — the SAME mistake already root-caused for cefi in the archived
`mdps_cefi_candle_manifest_never_emitted_2026_07_26.md` (MDPS stamps `data_type=<SOURCE type>` + a real `timeframe`, not
the aggregated family, by deliberate operator ruling). Re-measured DEFI directly this session with the correct
vocabulary: **7,913 real `market-data-processing-service` candle-manifest rows exist today**
(`data_type=dex_pool_swaps`, real timeframes), not 0. Flagged in that todo; not fully re-verified for
cefi/tradfi/prediction this session — do not close it on the DEFI spot-check alone.

**Disposition:** todo 11 stays OPEN — this session did NOT run the actual candle/feature migration. The previously-
recommended reconciliation path was unsafe; the additive fix (`unified-trading-library@2352e7c8`) has now SHIPPED and is
QG/CI-green, so `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` is UNBLOCKED for its next session (only
the actual Tier-2 SPOT VM reconciliation run remains, deliberately not launched from this interactive session per the
heavy-I/O rule). The full cross-repo lineage audit (MTDS→MDPS→features→ml/strategy) beyond the candle-manifest slice was
not attempted this session. What shipped is a genuine, verifiable safety fix + a corrected measurement that a future
session's migration work depends on not repeating.

### 2026-07-27 (slot-10) — todo 9b: no new CEFI cell launchable without duplicating in-flight work; billing-waste finding filed

Dispatched to todo 9b (full-matrix features re-run). Fresh-checked live state before launching anything (per the
duplicate-VM lesson learned mid-session, see below): `gcloud compute instances list --filter="name~'features-e2e-cefi'"`
showed **5 delta_one:CEFI VMs already RUNNING** from prior sessions (oldest since 06:34 UTC, ~4.7h runtime at check
time), none complete — `run.log` tails confirm all 5 are genuinely still computing (live-advancing timestamps, not
stuck), so none qualify for deletion under the VM-delete guardrail. Two are exact-duplicate pairs of each other (same
family/AG/window, both `--force`) — real billing waste from repeated relaunches with no in-flight check, filed as a new
todo in `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`. Separately confirmed via
`gcloud compute instances list --filter="name~'features-'"` that slot-3 is concurrently running `--family volatility`
(all-AG, covers CEFI) since 10:44 UTC, and another slot is running `sports`/`TRADFI:volatility` re-verification (both
post their respective fixes landing at 10:17/unclear). **Near-miss**: launched a
`--family volatility --asset-group CEFI` driver myself before checking local processes — `ps aux` immediately after
caught slot-3's identical in-flight run; killed my own 5-second-old duplicate before it reached VM-launch (confirmed via
its log: enumeration only, no VM created). Net effect: **zero new VMs launched this session** — every remaining CEFI
cell (`delta_one`, `volatility`) is already covered by in-flight work, and the two derived cells (`multi_timeframe`,
`cross_instrument`) are blocked on `delta_one`'s test-bucket output, which none of the 5 in-flight runs have produced
yet (checked `gs://features-cefi-test-central-element-323112/delta_one/by_date/day=2026-07-19/` — no objects; only the
still-writing `day=2026-06-28` partition has partial output so far).

**Disposition:** todo 9b stays OPEN. **Next session**: check
`gcloud compute instances list --filter="name~'features-e2e-cefi'"` FIRST — if all 5 have terminated, check which (if
any) reached a real completion (non-empty `by_date/day=<window-end>/` output in the test bucket) before launching
`multi_timeframe`/`cross_instrument` for CEFI (they need `delta_one`'s test output as `--source-bucket`); do NOT launch
a 6th `delta_one` VM. If `volatility` has a written report from slot-3 by then, fold it into the combined
`data_pipeline_e2e_check_features_2026_07_05` report via `merge_pipeline_e2e_report.py`.

### 2026-07-27 (slot-6) — todo 9b: found slot-7 ALREADY driving the full matrix; shipped the duplicate-VM billing-waste fix instead of launching

Dispatched to todo 9b. Per the disposition above, checked live fleet state FIRST:
`gcloud compute instances list --filter="name~'features-e2e'"` showed **7** `features-e2e-cefi-*` VMs RUNNING (up from
the 5 slot-10 found) + 2 `features-e2e-tradfi-*`, all confirmed live-advancing via fresh `run.log` tails (none stalled).
`ps aux` found slot-7 actively running
`.venv/bin/python scripts/pipeline_e2e_check.py --day 2026-07-05 --legs force,skip --require-captured --auto-day` (no
`--family`/`--asset-group` — the genuine unrestricted full-matrix driver todo 9b calls for) since 11:21 UTC, whose own
`run.log` showed it had just launched one of the 7 CEFI VMs (`-112159`, shard 1/16 = `CEFI:delta_one`) — i.e. **slot-7
is already doing exactly this todo**, ~35 min in, correctly progressing. This is the same slot-6/slot-7 double-dispatch
pattern main already ruled on once this session for a different task (`sports_satellite_ao_dispatch_batch5-026` — "stand
down, the other slot already implemented it"); applying the same resolution here: did NOT start a competing full-matrix
run (would duplicate VM spend on top of an already-running one) and did NOT touch slot-7's VMs (all genuinely
progressing, none eligible for the delete guardrail).

Instead used the dispatch productively: slot-7's own `-112159` launch was itself a NEW duplicate of the
2026-06-28..2026-06-29 window `-101851`/`-102228` were already computing — live proof that the P1 duplicate-VM-launch
bug filed in `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` was still unfixed and
actively costing money on the very run meant to close todo 9b. Shipped the fix: `features-service@6981b2b8` adds
`_find_inflight_duplicate_vm` (labels-based `aggregated_list_instances` check, no raw gcloud/subprocess) to both the
force and skip leg launch paths — a hit skips the launch with `status=skipped, reason=duplicate_in_flight: ...` instead
of creating another billable VM. QG green, quickmerge shipped. Full detail + a follow-up MDPS-parity todo (not yet
confirmed vulnerable, not yet fixed) in the same issue doc.

**Disposition:** todo 9b remains OPEN, now owned by slot-7's in-flight run (started 11:21 UTC, shard 1/16 of 16, window
`--day 2026-07-05 --auto-day`). **Next session**: check `ps aux | grep pipeline_e2e_check` for slot-7's process FIRST —
if it completed, read its written report (`data_pipeline_e2e_check_features_2026_07_05*`) and fold in any still-separate
`volatility` report from slot-3 via `merge_pipeline_e2e_report.py`; if it died mid-matrix (no `--resume` support yet —
see the other open todo in the same issue doc), resume from whichever shard it reached (check `run.log`'s last
`Starting compute:` line) rather than restarting all 16 from shard 1 — the new duplicate-guard fix will now correctly
skip any of the 7 already-running CEFI VMs / 2 TRADFI VMs it encounters again instead of adding an 8th/9th/10th.

### 2026-07-27 (slot-2) — todo 9b: slot-7 still in-flight; closed the MDPS-parity duplicate-VM-guard followup instead

Dispatched to todo 9b. Re-checked live fleet state: slot-7's driver (PID 3665121, started 11:21 UTC) STILL RUNNING,
1h18m+ elapsed, alive not zombie. Per the slot-6/slot-10 resolution, did NOT launch anything.

Used the dispatch productively to close the MDPS-parity followup flagged in
`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` (full detail there — confirmed
vulnerable + the launcher-label insufficiency finding + both fixes): `market-data-processing-service@6cd96e8` (ports
`_find_inflight_duplicate_vm` into both force/skip legs, 6 new tests, QG green 118s) + `deployment-service@c8ee47e`
(extends `launch-mdps-backfill-vm.sh` labels with venue/data_type, 5 new tests).

**Disposition:** todo 9b remains OPEN, still owned by slot-7's in-flight run — this closed an ADJACENT gap, not 9b
itself. **Next session**: `ps aux | grep pipeline_e2e_check` for slot-7 first; if finished, read its report; if died
mid-matrix, resume from its last shard (both drivers now duplicate-guarded).

### 2026-07-21 — Option-A candle canonical-path migration EXTRACTED to its own plan

The full "OPTION-A MIGRATION SCOPED" record and the "RESUMPTION STATE 2026-07-21" record (scale correction, blast
radius, path transform, the 8-phase breakdown, the LOCKED canonical shape, the per-repo shipped/uncommitted-file table,
RESUME ORDER, and the 🔑 LESSONS) were extracted **verbatim** 2026-07-24 to
`/plans/archive/2026_07/candle_canonical_path_migration_execution_2026_07_24.md` (plan-hygiene line-cap remediation) —
that plan now owns the migration epic end-to-end (census → executor → per-AG SPOT migration → verify). See that file for
the full record; nothing here was summarized or lost, only moved. This plan's own remaining work (todo 15) is
`depends_on`-gated on that plan's completion.

## Deferred work after 2026-07-21

Every item below is already a tracked todo in the cited issue doc (nothing lost). None blocks the operator's DeFi-MVP
backfill decision — the derivative_ticker write path (the one hard blocker found this session) is PROVEN fixed.

| #   | Item                                                                                                                                                     | Priority | Where tracked                                                       | Gating                                                          |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------- | --------------------------------------------------------------- |
| 1   | Driver reads MERGED index not the leg VM's per-VM shard → reports "failed" on a successful write (EXACT fix spec'd)                                      | P2       | `mdps_derivative_ticker_candle_schema_violation` todo 4             | none — unit-testable, no VM                                     |
| 2   | Exit-code-lies: a run whose every write fails still exits rc=0 (shard-isolation-safe fix needed)                                                         | P1       | same issue, todo 2                                                  | none                                                            |
| 3   | Proof-sweep the other empty-window candle types (book5/liq exempt) — the fix already covers them via the shared seam                                     | P1       | same issue, todo 3                                                  | none                                                            |
| 4   | Candle object↔manifest disconnect: 6 degenerate MDPS rows vs 20k+ objects/day — candle manifest never systematically populated                           | P0       | `candle_feature_canonical_path_divergence` todo 7                   | none — root-cause needed before trusting skip-if-fresh at scale |
| 5   | Canonical A/B/C ruling for the candle object-path shape (instrument_type= presence + source vs aggregated data_type)                                     | P1       | same issue, todo 1                                                  | **OPERATOR-GATED**                                              |
| 6   | Split-brain candle layout (pipeline_mode present on some objects, absent on others) + extend the UAC canonical oracle to the processed_candles namespace | P1       | same issue, todos 9,10                                              | partly operator-gated (follows the A/B/C ruling)                |
| 7   | Real features-service writing smoke (proves the features skill's green path)                                                                             | P2       | this plan                                                           | candle input coverage (blocked by #4)                           |
| 8   | Full DeFi-MVP candle backfill on real infra                                                                                                              | —        | this plan / ETA                                                     | operator's run (SPOT fleet ready; per the delivered ETA)        |
| 9   | Defense-in-depth UAC pin on the other service launchers (mtds/instruments/mdps-sharded/mtds-dex-swaps)                                                   | P2       | `mdps_vm_stale_uac_contract_propagation` (resolved; follow-up note) | none — already covered fleet-wide by shared setup Fix 2/3       |

## Session close 2026-07-21 — what shipped + proven

**Delivered:** both skills (`/data-pipeline-check-mdps` + `/data-pipeline-check-features`) built, shipped,
harness-registered, and VALIDATED end-to-end on real infra — where they earned their keep by catching 3 silent P0s no
green-tick smoke would surface. **3 P0s fixed + PROVEN on live VMs:** (1) derivative_ticker candle write (0→140
objects + 140 `captured` rows, via adapter `mdps@beea161` + nullability `mdps@d4052e20b`); (2) UAC contract-propagation
(`deployment@e978f32d`, fleet-wide silent staleness); (3) read-path amplification 16.7x + seed-context thread-safety
(`utl@80d2497e`/`mdps@b4db0af`/`b3376b8`) shipped earlier. Root cause of (1) was CORRECTED mid-flight by an adversarial
8-agent workflow (my first "key mismatch" hypothesis was a red herring — the real cause was category-gated nullability
in the MDPS pre-upload validator). **Measured:** trades write-rate ~16.9s/instrument-day; full MDPS MVP breadth 462
shard cells. **Ground-truthed (operator-gated resolution):** the existing-candle estate's canonical orphans (split-brain
layout, no candle oracle, 6-row manifest vs 20k objects/day). Every finding is a tracked todo; the SPOT backfill fleet
is ready pending the operator's canonical ruling + the candle-manifest-population root-cause.

---

## Extracted 2026-07-31 (slot-4) — six 2026-07-27/28 dated entries with zero embedded open checkboxes (todo 14's own extraction, keeping the parent under its 1000-line hard cap after the codex-audit addition)

### 2026-07-27 — todo 8 PARTIAL: CEFI force-leg mechanism re-proven 4x; skip-proof + other AGs blocked by session teardown

Scoped `/data-pipeline-check-mdps` to CEFI:BINANCE-FUTURES:trades (day=2026-07-05, auto-day-resolved) as a
representative cell before attempting the full 448-cell all-AG matrix (unscoped run is explicitly warned against by the
skill itself). **Force leg independently re-proven correct on real infra 4 separate times** (VMs
`...pipelinecheck-20260727-022633`, `-023618`, `-031200`, `...manualskip-033855` — all `exit_code=0`, all derive the
identical 7,615 candles across the 7 timeframes). The automated skill driver (`pipeline_e2e_check.py --legs force,skip`)
could not be kept alive long enough by this interactive session to produce a clean automated skip-proof verdict — the
local process was killed mid-run 4 times across different backgrounding strategies (plain `run_in_background`,
`nohup&disown`, foreground-with-auto-background, `setsid`). Full findings + recommended fixes:
`/plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`. A secondary, minor
finding (byte-identical candle written to two different paths — with/without `instrument_type=` segment — across
consecutive force runs) is tracked separately:
`/plans/archive/issues/mdps_candle_path_instrument_type_segment_nondeterministic_2026_07_27.md`.

**Disposition:** todo 8 stays OPEN (not flipped) — the force-leg _mechanism_ is proven, but the todo's actual scope
("every MVP candle shard, all AGs") and even a single clean automated skip-proof are not yet met. Report written this
session: `plans/audit/results/data_pipeline_e2e_check_mdps_2026_07_05.md`.

### 2026-07-27 (slot-9) — one of todo 8's two identified blockers FIXED; todo 8 itself still OPEN

Dispatched to continue todo 8. Rather than re-attempt the exact same 4x-failed backgrounding strategies (harness
`run_in_background`, `nohup&disown`, foreground-auto-backgrounded, `setsid` — all already exhausted per the entry
above), root-caused and fixed the CONCRETE bug behind attempt 3's `launcher_script_timeout` false-failure:
`unified-trading-library@137e219c` — a `subprocess.TimeoutExpired` on the launcher-script client-side wait
(`_LAUNCHER_SCRIPT_TIMEOUT_SEC=120s`) previously aborted the whole shard immediately with ZERO retry, even though the
identical `_vm_is_present`-gated retry machinery already existed for ordinary nonzero launcher exits (added for the
exact same "gcloud create succeeded server-side after the client-side confirmation wait already gave up" failure mode).
Now a timeout is converted to a synthetic nonzero-exit result and flows through that same retry path. 3 new regression
tests, QG green (226s). Full detail + evidence:
`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` todo 3 (flipped).

**Disposition:** todo 8 stays OPEN — this fixes one of the two identified blockers (the launcher-timeout false-failure),
not the other (the session/container teardown killing the long-running driver process itself, still under P1
investigation, unresolved). A from-scratch automated run may now get further before hitting the teardown wall, but
re-attempting the full multi-hour/462-cell matrix was out of scope for this 1-hour task; the next attempt should happen
once the teardown root-cause (item 1 below) is resolved, or from a longer-lived host if the teardown proves to be this
interactive-session-class specific.

### 2026-07-27 (slot-12) — todo 11 PARTIAL: caught + fixed a P0 unsafe-rebuild bug blocking the candle-manifest orphan reconciliation; DEFI candle-manifest measurement corrected

Dispatched to todo 11 (cross-repo orphan/lineage audit + migrate to zero orphans). Scoping how to execute the
already-open `issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` (CEFI candle files orphaned by
pre-fix-era OOM crashes) surfaced a genuine, previously-uncaught **P0 data-loss risk in the recommended remediation
itself**: `unified_trading_library.manifest_writer.rebuild_manifest_from_canonical_paths()` builds its output purely
from a `prefix`-scoped GCS walk and uploads that as the bucket's WHOLE consolidated manifest index — on the
`market-data-tick-{ag}-prd` buckets, which co-locate MTDS's `raw_tick_data/` and MDPS's `processed_candles/` under ONE
index, a prefix-scoped call (exactly what the reconciliation doc recommended) would have silently deleted essentially
the entire raw-tick manifest for that asset_group to backfill a much smaller candle-orphan set. **Caught before any VM
launched — nothing was actually deleted.** Full analysis, evidence, and fix:
`issues/rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md` (new, P0). Shipped the fix:
`unified-trading-library@2352e7c8` — added `merge_manifest_from_canonical_paths()`, an additive sibling that only adds
genuinely-missing `(day, venue, chain, instrument_type, data_type)` rows and preserves every existing row (including
rows for other prefixes) verbatim; 2 new regression tests directly proving the safety property (a pre-existing
out-of-prefix row survives the merge, both in the returned frame AND in what actually lands in GCS) plus an idempotency
test. Corrected `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`'s recommended-fix section to route
through the new additive function instead of the unsafe call, and to re-verify the bucket's non-candle row count is
unchanged before trusting a future run.

**Also corrected a stale measurement feeding this same effort**:
`candle_feature_canonical_path_divergence_2026_07_20.md` todo 7's "candle manifest never systematically populated" claim
(cefi=6/defi=0/tradfi=73/prediction=168 rows, 2026-07-23) used the WRONG `data_type` vocabulary (the aggregated
`ohlcv_*` family) — the SAME mistake already root-caused for cefi in the archived
`mdps_cefi_candle_manifest_never_emitted_2026_07_26.md` (MDPS stamps `data_type=<SOURCE type>` + a real `timeframe`, not
the aggregated family, by deliberate operator ruling). Re-measured DEFI directly this session with the correct
vocabulary: **7,913 real `market-data-processing-service` candle-manifest rows exist today**
(`data_type=dex_pool_swaps`, real timeframes), not 0. Flagged in that todo; not fully re-verified for
cefi/tradfi/prediction this session — do not close it on the DEFI spot-check alone.

**Disposition:** todo 11 stays OPEN — this session did NOT run the actual candle/feature migration. The previously-
recommended reconciliation path was unsafe; the additive fix (`unified-trading-library@2352e7c8`) has now SHIPPED and is
QG/CI-green, so `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` is UNBLOCKED for its next session (only
the actual Tier-2 SPOT VM reconciliation run remains, deliberately not launched from this interactive session per the
heavy-I/O rule). The full cross-repo lineage audit (MTDS→MDPS→features→ml/strategy) beyond the candle-manifest slice was
not attempted this session. What shipped is a genuine, verifiable safety fix + a corrected measurement that a future
session's migration work depends on not repeating.

### 2026-07-27 (slot-10) — todo 9b: no new CEFI cell launchable without duplicating in-flight work; billing-waste finding filed

Dispatched to todo 9b (full-matrix features re-run). Fresh-checked live state before launching anything (per the
duplicate-VM lesson learned mid-session, see below): `gcloud compute instances list --filter="name~'features-e2e-cefi'"`
showed **5 delta_one:CEFI VMs already RUNNING** from prior sessions (oldest since 06:34 UTC, ~4.7h runtime at check
time), none complete — `run.log` tails confirm all 5 are genuinely still computing (live-advancing timestamps, not
stuck), so none qualify for deletion under the VM-delete guardrail. Two are exact-duplicate pairs of each other (same
family/AG/window, both `--force`) — real billing waste from repeated relaunches with no in-flight check, filed as a new
todo in `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`. Separately confirmed via
`gcloud compute instances list --filter="name~'features-'"` that slot-3 is concurrently running `--family volatility`
(all-AG, covers CEFI) since 10:44 UTC, and another slot is running `sports`/`TRADFI:volatility` re-verification (both
post their respective fixes landing at 10:17/unclear). **Near-miss**: launched a
`--family volatility --asset-group CEFI` driver myself before checking local processes — `ps aux` immediately after
caught slot-3's identical in-flight run; killed my own 5-second-old duplicate before it reached VM-launch (confirmed via
its log: enumeration only, no VM created). Net effect: **zero new VMs launched this session** — every remaining CEFI
cell (`delta_one`, `volatility`) is already covered by in-flight work, and the two derived cells (`multi_timeframe`,
`cross_instrument`) are blocked on `delta_one`'s test-bucket output, which none of the 5 in-flight runs have produced
yet (checked `gs://features-cefi-test-central-element-323112/delta_one/by_date/day=2026-07-19/` — no objects; only the
still-writing `day=2026-06-28` partition has partial output so far).

**Disposition:** todo 9b stays OPEN. **Next session**: check
`gcloud compute instances list --filter="name~'features-e2e-cefi'"` FIRST — if all 5 have terminated, check which (if
any) reached a real completion (non-empty `by_date/day=<window-end>/` output in the test bucket) before launching
`multi_timeframe`/`cross_instrument` for CEFI (they need `delta_one`'s test output as `--source-bucket`); do NOT launch
a 6th `delta_one` VM. If `volatility` has a written report from slot-3 by then, fold it into the combined
`data_pipeline_e2e_check_features_2026_07_05` report via `merge_pipeline_e2e_report.py`.

### 2026-07-27 (slot-6) — todo 9b: found slot-7 ALREADY driving the full matrix; shipped the duplicate-VM billing-waste fix instead of launching

Dispatched to todo 9b. Per the disposition above, checked live fleet state FIRST:
`gcloud compute instances list --filter="name~'features-e2e'"` showed **7** `features-e2e-cefi-*` VMs RUNNING (up from
the 5 slot-10 found) + 2 `features-e2e-tradfi-*`, all confirmed live-advancing via fresh `run.log` tails (none stalled).
`ps aux` found slot-7 actively running
`.venv/bin/python scripts/pipeline_e2e_check.py --day 2026-07-05 --legs force,skip --require-captured --auto-day` (no
`--family`/`--asset-group` — the genuine unrestricted full-matrix driver todo 9b calls for) since 11:21 UTC, whose own
`run.log` showed it had just launched one of the 7 CEFI VMs (`-112159`, shard 1/16 = `CEFI:delta_one`) — i.e. **slot-7
is already doing exactly this todo**, ~35 min in, correctly progressing. This is the same slot-6/slot-7 double-dispatch
pattern main already ruled on once this session for a different task (`sports_satellite_ao_dispatch_batch5-026` — "stand
down, the other slot already implemented it"); applying the same resolution here: did NOT start a competing full-matrix
run (would duplicate VM spend on top of an already-running one) and did NOT touch slot-7's VMs (all genuinely
progressing, none eligible for the delete guardrail).

Instead used the dispatch productively: slot-7's own `-112159` launch was itself a NEW duplicate of the
2026-06-28..2026-06-29 window `-101851`/`-102228` were already computing — live proof that the P1 duplicate-VM-launch
bug filed in `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` was still unfixed and
actively costing money on the very run meant to close todo 9b. Shipped the fix: `features-service@6981b2b8` adds
`_find_inflight_duplicate_vm` (labels-based `aggregated_list_instances` check, no raw gcloud/subprocess) to both the
force and skip leg launch paths — a hit skips the launch with `status=skipped, reason=duplicate_in_flight: ...` instead
of creating another billable VM. QG green, quickmerge shipped. Full detail + a follow-up MDPS-parity todo (not yet
confirmed vulnerable, not yet fixed) in the same issue doc.

**Disposition:** todo 9b remains OPEN, now owned by slot-7's in-flight run (started 11:21 UTC, shard 1/16 of 16, window
`--day 2026-07-05 --auto-day`). **Next session**: check `ps aux | grep pipeline_e2e_check` for slot-7's process FIRST —
if it completed, read its written report (`data_pipeline_e2e_check_features_2026_07_05*`) and fold in any still-separate
`volatility` report from slot-3 via `merge_pipeline_e2e_report.py`; if it died mid-matrix (no `--resume` support yet —
see the other open todo in the same issue doc), resume from whichever shard it reached (check `run.log`'s last
`Starting compute:` line) rather than restarting all 16 from shard 1 — the new duplicate-guard fix will now correctly
skip any of the 7 already-running CEFI VMs / 2 TRADFI VMs it encounters again instead of adding an 8th/9th/10th.

### 2026-07-27 (slot-2) — todo 9b: slot-7 still in-flight; closed the MDPS-parity duplicate-VM-guard followup instead

Dispatched to todo 9b. Re-checked live fleet state: slot-7's driver (PID 3665121, started 11:21 UTC) STILL RUNNING,
1h18m+ elapsed, alive not zombie. Per the slot-6/slot-10 resolution, did NOT launch anything.

Used the dispatch productively to close the MDPS-parity followup flagged in
`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` (full detail there — confirmed
vulnerable + the launcher-label insufficiency finding + both fixes): `market-data-processing-service@6cd96e8` (ports
`_find_inflight_duplicate_vm` into both force/skip legs, 6 new tests, QG green 118s) + `deployment-service@c8ee47e`
(extends `launch-mdps-backfill-vm.sh` labels with venue/data_type, 5 new tests).

**Disposition:** todo 9b remains OPEN, still owned by slot-7's in-flight run — this closed an ADJACENT gap, not 9b
itself. **Next session**: `ps aux | grep pipeline_e2e_check` for slot-7 first; if finished, read its report; if died
mid-matrix, resume from its last shard (both drivers now duplicate-guarded).

### 2026-07-28 (slot-13) — todo 10 DONE: steady-state benchmarks run for both representative shard-types; local driver died twice, numbers recovered from each VM's own GCS log

Dispatched to todo 10 (steady-state benchmark VMs + full-history/SPOT-cost/parallelization projection). Ran the opt-in
`--legs benchmark` leg for one representative MDPS shard and one representative features shard.

**MDPS** (`market-data-processing-service`, CEFI:BINANCE-FUTURES:trades, `--benchmark-days 14` → window
2026-06-21..2026-07-05, VM `mdps-backfill-cefi-pcbench-20260727-234527-a84603`): the local driver process was killed
mid-run by a worker-session teardown (same class as
`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`) before it could poll EXIT_STATUS and
write its report — but the VM itself completed independently on GCP (`exit_code=0`). Recovered the real measurement
directly from the VM's own `gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log` (same recovery
technique already proven for todo 8): 15 calendar days were attempted, but only **1/15 (6.7%)** had genuine captured
raw-tick input for this venue/data_type — a concrete, independently-confirmed instance of the plan's own documented "the
input corpus is sparse and uneven" caution. Per-day costs, computed from consecutive `subprocess-per-date: spawning`
timestamps:

- **Real-compute day** (2026-07-05, the one day with real input): **20.7s** pure compute (VM's own "Total Duration"
  line) → 7,615 candles across 7 timeframes (15s/1m/5m/15m/1h/4h/24h) — matches the identical candle count independently
  proven 4-5x already in todo 8. Full round-trip incl. subprocess spawn/shutdown: ~29.8s.
- **Empty/no-input day** (13 samples, consecutive spawn-to-spawn deltas): mean **14.0s/day** — subprocess bootstrap +
  GCS list-and-bail + shutdown, even though zero real work happens. This is a real, non-trivial fixed tax paid on EVERY
  calendar day attempted, filed as new todo 10-followup-b.

**Features** (`features-service`, CEFI:delta_one): first attempt (window 2026-06-21..2026-07-05, matching the MDPS
window) failed outright — the delta_one dependency check requires MDPS candles for the whole window in the PROD bucket,
and `2026-06-21` had none (the benchmark leg does NOT honor `--auto-day`, confirmed by reading `_run_benchmark_leg`'s
use of the raw `_window()` helper vs. `_resolve_window()` used by the other legs — a real gap, itself worth a follow-up
if the benchmark leg needs auto-day support). Manually located a genuinely-covered window instead by object-counting
`processed_candles/by_date/day=*` prefixes in `market-data-tick-cefi-prd-central-element-323112`
(2026-04-10..2026-04-14, 1485-5680 objects/day) and relaunched with `--day 2026-04-14 --benchmark-days 4`. This driver
ALSO died mid-run to the same teardown class as MDPS (2nd/3rd reproduction this session) — recovered from the VM's own
run.log (`features-e2e-cefi-20260727-235729-025349`, still `RUNNING` at write-time, self-manages its own 10-hour
timeout + `VM_SHUTDOWN_ON_COMPLETION=true`, non-blocking to this report). Observed, from two independent full-log
snapshots 120s apart (11166→20034 lines): a sustained **~73.9 log-lines/s** dependency-pre-check rate. The universe is
large — 1807 retained instruments (per `universe_filter`) across delta_one's 4 sub-families
(technical_indicators/moving_averages/oscillators/ volatility_realized) — and **each sub-family independently re-scans
the identical (instrument, date) MDPS-availability check**, directly confirmed by watching the log's per-instrument
alphabetical iteration restart from the top at the start of each family's pass. This pre-check phase dominates
wall-clock before any real feature compute begins on a large-universe AG like CEFI. Filed as new todo 10-followup-a (~4x
reduction available by caching the check once per run instead of once per family).

**Projection** (SKILL.md formula: `serial_hours = per_shard_day_seconds × shard_days / 3600`;
`VM_hours = serial_hours / (workers × fleet_width)`; `cost = VM_hours × $/hr`), using MDPS's real COMPLETE measurement
as the primary input (features' number is a real but partial in-progress observation, not used for the cost projection):

- `per_shard_day_seconds` = 20.7s (compute-only) / 29.8s (full round-trip incl. subprocess overhead)
- `shard_days` = flat 2019-01-01→today upper bound = 2757 days (per this plan's already-established measured floor); the
  HONEST per-shard floor is almost certainly far lower given the 6.7%-real-data sparsity measured in this exact
  benchmark, but that requires its own availability-census (same class of work as todo 13's DeFi ETA) — not re-derived
  here, flagged as a caveat rather than assumed.
- Serial (1 VM, compute-only): 20.7 × 2757 / 3600 = **15.9 hours**; full round-trip: 29.8 × 2757 / 3600 = **22.8 hours**
  — for ONE representative shard's entire flat-2019 history on a single VM.
- Fleet width (unbounded, MDPS is not Tardis-capped — shard by date range across N VMs for ~N×): 4 VMs → ~4-6 hours; 8
  VMs → ~2-3 hours.
- Cost: e2-standard-8 SPOT
  $0.024-0.107/hr × 15.9-22.8 VM-hours (1 VM, worst case no skip-optimization) ≈
  **$0.38-$2.44** for one representative
  shard type's full historical backfill — cheap in absolute terms because compute itself is fast; the REAL cost driver
  at scale is the empty-skip subprocess tax (13/15 = 86.7% of attempted days in this sample), which is exactly what todo
  10-followup-b targets.
- Disk: `pd-balanced 250GB` confirmed already the enforced default (unchanged from prior sessions' finding).

**Disposition:** todo 10 DONE — both representative shard-types benchmarked on real infra, real per-day costs measured
(MDPS complete, features partial-but-real with the VM continuing independently), full-history/SPOT-cost/ parallelization
projection written with honest caveats, and two concrete new optimization-headroom todos filed (10-followup-a,
10-followup-b) rather than absorbed as unplanned scope into this todo.

> **Extracted 2026-08-05 (slot-2, line-cap remediation).** The fully-closed 2026-07-31 (slot-4) "todo 14 DONE:
> ship-verification + post-phase codex audit" entry — zero open todos carried — was moved VERBATIM here from the active
> plan (which had grown back to 1001 lines over its 1000-line hard cap). Nothing summarized or lost.

### 2026-07-31 (slot-4) — todo 14 DONE: ship-verification + post-phase codex audit (scoped, NOT a whole-plan rule-9 close)

Dispatched to todo 14 ("Ship everything via quickmerge --agent per repo; flip these checkboxes same-turn; rule-9 final
report. Post-phase codex audit"). Read the full plan first (1000+ lines across the active file + its extracted history)
to confirm scope before acting — this plan is NOT finished (11b/11c orphan-migration, the gated per-family features
numbers, 10-followup-a/b all remain genuinely OPEN), so a whole-plan "rule-9 final report" declaring completion would
violate the plans-run-to-actual-completion HARD RULE. Todo 14 itself, however, is a scoped hygiene/wrap-up item
(ship-verify + flip + codex audit), which IS fully addressable now:

1. **Ship-verification**: checked `git status --porcelain=v1 --branch` across all 8 repos this plan touches
   (unified-trading-library, market-data-processing-service, features-service, deployment-service, unified-trading-pm,
   ml-service, strategy-service, market-tick-data-service) in this slot — every one reads clean, `HEAD` ==
   `origin/live-defi-rollout`, nothing ahead/behind/dirty. Every commit cited in this plan's own Todos (1-13, 15,
   9a/9b/11a/etc.) has already landed via the normal quickmerge flow across ~20 prior sessions; there was nothing left
   to ship.
2. **Post-phase codex audit**: re-read this plan's own "Codex SSOTs" section + grepped the archived history for anything
   explicitly deferred "to the post-phase codex audit." Found one concrete item: the 2026-07-20 operator-stated
   "window-active vs shard-fetched" two-signal contract (WINDOW activity → parquet NaN/0-volume bin; SHARD-DAY
   fetch-status → manifest 4-state `capture_status`) was journaled in the plan's history with an explicit note "belongs
   in `/codex/02-data/honest-absence-downstream-handling.md` at the post-phase codex audit." Promoted it now, as its own
   named section ("Window-active vs shard-fetched — the two-signal contract") placed directly after the existing "MDPS
   downstream consumption contract (4-state routing)" section, and cross-linked it to the already-existing Phase 3A CeFi
   adapter audit's "inverse phantom" (all-NaN-OHLC-but-`captured`) discussion so the two related concepts sit next to
   each other. While auditing that discussion, surfaced one genuine remaining code gap the archived note also flagged
   but was never turned into a tracked todo: no driver (`/data-pipeline-check-mdps` or `/data-pipeline-check-features`)
   currently asserts the inverse-phantom case for a FRESH write (the existing reconciler is a historical scan-only tool
   for pre-writegate rows) — filed as new todo `14-followup` ([SCRIPT] P1, above) rather than absorbed into this
   doc-only todo's scope, per findings-triage.
3. **CLAUDE.md one-liner for the two new skills**: checked `wc -c cursor-configs/CLAUDE.md` = 40,958 bytes against the
   documented 40KB / ~10k-tok QG-enforced hard cap (`check_agent_rules_size_cap.py`) — 2 bytes of headroom, no room to
   add anything without violating the cap (which the doc's own governing rule explicitly forbids raising). Also checked
   for precedent: neither sibling skill already shipped in this same family (`/data-pipeline-check-mtds`,
   `/data-pipeline-check-is`) has a CLAUDE.md one-liner either — the domain index's "Working on DATA / manifest /
   pipeline?" section covers the shared manifest/coverage contracts, not individual skill names. Concluded: NOT adding a
   CLAUDE.md line is the correct disposition (consistent with existing precedent + the hard cap), not a gap — codex is
   already the correct SSOT for this per the CLAUDE.md's own "SSOT direction" rule, and both skills are independently
   discoverable via the harness's own skill registry (both already appear in the live skill list).
4. No code changed this session (docs-only + one plan-hygiene edit); nothing to quickmerge for this specific todo beyond
   the PM-repo plan/codex doc edits themselves.

**Disposition**: todo 14 DONE — its own scope (ship-verify, flip, codex audit) is fully closed. The PLAN remains ACTIVE
(genuinely open work: 11b/11c, the gated features-numbers todo, 10-followup-a, 14-followup) — no rule-9 whole-plan
closing report follows from this todo, and the plan should NOT be archived.

### 2026-07-31 (slot-8, data_engineering) — todo 14-followup DONE: inverse-phantom content_check shipped to both drivers

Dispatched to `data_pipeline_check_mdps_features-058` (todo 14-followup). Added the shared `check_inverse_phantom()`
primitive to `unified_trading_library.pipeline_e2e_check.shard_verify` (bar: every sampled cell across the caller's
`value_columns` NaN, not merely most — a row with even one real value is never flagged) plus
`ShardCheckResult.content_check`/`content_check_nan_ratio` + a report "Content" column, all shipped in
`unified-trading-library@8b894105`. Wired into both drivers: MDPS's `_check_content_for_inverse_phantom`
(`market-data-processing-service@12a3f6b`) consults the SAME `mdps_ohlc_is_nullable` UAC oracle the write seam itself
uses (via `_type_token_from_canonical_id` for the instrument_type) before flagging, so a legitimate nullable-OHLC
honest-absence window (`trades`/`derivative_ticker`/etc) is never mislabeled; features-service's twin
(`features-service@6afdb414`) has no equivalent per-type oracle, so it checks every non-identity numeric column against
the same strict 100%-NaN bar.

**Deliberately scoped informational-only in both drivers** — the verdict is threaded into the report/reason string but
never flips a leg's `passed`/`failed` status. Rationale: this smoke-check is relied on by other slots/CI as a
currently-green signal, and there is no adversarial test coverage yet proving the nullable-detection heuristic never
false-positives on real prod-shaped data (a false positive here would silently fail a legitimate leg). Promoting either
to authoritative once validated against real data is natural, tracked follow-up — not claimed done here.

While QG-verifying the MDPS driver via a real `--dry-enumerate` smoke run (`quality-gates.sh` § "PIPELINE-E2E-CHECK
DRIVER SMOKE"), surfaced a genuine, PRE-EXISTING, unrelated break (confirmed via diff against the parent commit before
my change touched this file): `_candle_data_types_for_market_ag` still unpacks `mdps_mvp_universe()`'s return as a
2-tuple, but the function was extended to a 3-tuple `(venue, instrument_type, data_type)` in
`unified-api-contracts@724b6633` (see `/plans/archive/2026_08/uac_mdps_mvp_universe_data_type_axis_2026_07_30.md`, whose
own caller-update sweep only covered UAC-internal callers, not this cross-repo consumer) — every enumeration call raises
`ValueError: too many values to unpack`. `quality-gates.sh`'s own exit code is 0 (this smoke step is non-blocking), so
it did not block shipping, but it is a real correctness gap. Per findings triage (not small/clear enough to fix inline —
needs redesigning the function's data_type derivation, not a 1-line unpack fix) filed as a new todo on the existing,
still-open issue doc rather than a fresh one (same root cause, already active, `assigned_vm: planning`) — did NOT fix it
here, out of this todo's scope.

Repos shipped: `unified-trading-library@8b894105`, `market-data-processing-service@12a3f6b`,
`features-service@6afdb414`.
