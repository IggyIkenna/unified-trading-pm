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
    /plans/active/candle_canonical_path_migration_execution_2026_07_24.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
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
  (`issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`). The bug remains for trades/book/tbbo/defi.

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
