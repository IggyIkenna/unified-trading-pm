---
plan_type: handoff
asset_group: defi
owner: ikenna
created: 2026-05-05
locked_by: live-defi-rollout
locked_since: 2026-05-05
name: carry-tracer-pipeline-handoff-2026-05-05
status: active
---

# NEXT-AGENT PROMPT — Carry tracer pipeline (Stages 1-4)

> You are picking up a multi-hour data-pipeline session that ended at 2026-05-05 ~21:30 UTC. The user's goal: get unified `scripts/trace_all_carry_archetypes.py` running over a 30-day window with all 7 carry/yield archetypes producing real ranked output. **READ THIS WHOLE FILE before any action**.

## CRITICAL CLAUDE.md RULES (active workspace-wide via symlinks)

1. **Honest-absence rule** (`PM@3d6a29b6`): three categories of "missing", different actions:
   - Expected source gap (venue not yet launched, source coverage start, etc.) → `record_empty` + NaN. Honest. Do not fabricate.
   - Unexpected pipeline gap (raw exists per manifest but reader can't find it) → `DependencyError(fail_fast=True)`. Run upstream backfill, NOT `--skip-dependency-check`.
   - Reader/schema-drift bug → RAISE LOUD with structured details. Never silent placeholders.
2. **No fire-and-forget VM rule** (`PM@82bdb4f9`): every VM launch MUST be paired with active event-stream verification. STARTED within 60s, progress events streaming, STOPPED/FAILED at exit with non-empty `details`. SSH-tailing is dev crutch; production runs through `unified-events-interface`. Events stream to `gs://{pid}-events/events/{service}/{YYYY-MM-DD}/{vm-name}/hour=*/*.jsonl`.
3. Never quickmerge in Claude Code; use `git push origin live-defi-rollout`. Never `--skip-dependency-check` to mask a bug — only when the narrow-scope feature genuinely doesn't read the missing upstream.

## SESSION STATE — what's in `origin/live-defi-rollout`

**Five fixes shipped today** (in commit order):

| Repo | Commit | What |
|---|---|---|
| market-data-processing-service | `d352c02` | MDPS reader: per-instrument `{instrument_id}.parquet` enumeration (was expecting legacy `ticks.parquet`) |
| market-tick-data-service | `64f66d1` | MTDS `AlchemyBaseClient.get_rpc_url("SOLANA")` falls through to `SOLANA_RPC_TEMPLATES["alchemy"]` (chain_id=0 sentinel was raising) |
| features-onchain-service | `f3db4ca` | features-onchain reader: `mtds_output_config.py` directory-pattern enumeration (was expecting fixed `data.parquet` filenames + fictional `{protocol}/{chain}/` levels for lst_rates) |
| market-data-processing-service | `ca4df75` | MDPS aggregator: new SSOT `aggregation_rules.py` preserves derivative-specific columns (`mark_price`, `funding_rate`, `open_interest`) through 1m→24h aggregation. Was dropping them because `COLUMN_AGG_RULES` only had `_last`-suffixed names. + `INSTRUMENT_PROCESSED` events with row counts. |
| features-onchain-service | `266f512` | features-onchain persist-events: `PERSISTENCE_COMPLETED` at actual upload site with `rows_written, parquet_path, parquets_written` in details. All 4 silent-fail paths emit `FEATURE_WRITE_REJECTED` with `reason` enum (empty_dataframe / write_gate_rejected / pit_alignment / exception). + `LST_DAY_PROCESSED` per-day events. |
| unified-trading-pm | `3d6a29b6` + `82bdb4f9` | The two CLAUDE.md rules above. |

**Two launcher overrides shipped earlier**:
- `deployment-service@2c4d65c`: `FEATURE_GROUP=` and `SKIP_DEPENDENCY_CHECK=` env overrides for `launch-features-backfill-vm.sh`.
- `deployment-service@489ec0e`: DeFi added to `launch-mdps-sharded-backfill.sh` + `vm_zombie_watchdog.py`.

**Tarball state**: refreshed at 20:59Z 2026-05-05 with CORE + market-data-processing-service + features-onchain-service. **DO NOT RE-LAUNCH VMs without confirming tarball is current** — `gcloud storage ls -L gs://deployment-scripts-central-element-323112/code/{repo}-code.tar.gz` shows `updateTime`. If you ship new commits, refresh first: `bash deployment-service/scripts/vm/create-code-tarballs.sh --include <repo>`.

## CONFIRMED WORKING

- **lst_yields single-day** (DEFI 2026-04-09): produced 15 tokens at `gs://features-onchain-central-element-323112/by_date/day=2026-04-09/feature_group=lst_yields/features.parquet`. Real APY values: sUSDe=352bps, cbETH=254bps, rETH=210bps, stETH=246bps, wstETH=246bps, ETHx, ankrETH, mETH, osETH, etc. mSOL/jitoSOL=0.0 (Tier 3 REST historical limitation, documented).
- **MDPS aggregator on 2026-04-09**: HYPERLIQUID/BTC-PERP 1m derivative_ticker has `mark_price 1440/1440 non-null`, `funding_rate 1440/1440`, `open_interest 1440/1440`. Real data, real values.

## THREE REMAINING BLOCKERS (each diagnosed, structured events name the cause)

### Blocker 1: `lst_yields` wider window → `LookaheadBiasError`

VM `features-onchain-defi-backfill-20260505-210820` (DEFI lst_yields 2026-03-01 → 2026-04-14) emitted:
```
FEATURE_WRITE_REJECTED  exc_type=LookaheadBiasError  feature_group=lst_yields  date=2026-03-01  rows=675
PERSISTENCE_COMPLETED   parquets_written=0
FAILED  message=handler returned False
```
Single-day works; multi-day fails on the FIRST day. The PIT (point-in-time) check fires `LookaheadBiasError`. Probably the orchestrator's prior-day query overlaps the next-day target when iterating days.

**To fix**: read the `LookaheadBiasError` raise site (grep `LookaheadBiasError` in features-onchain). Likely in `app/core/feature_writer.py` or a PIT-validation guard. Determine if the calculator is genuinely producing future-leaking data, or if the guard is over-strict for this feature group. The lst_yields rate-diff math `(rate[t] / rate[t-1])^365 - 1` uses the PRIOR day, which is honest backward-looking. If the guard flags this, it's a false positive.

### Blocker 2: `lending_rates` → `write_gate_rejected: 2 columns >95% NaN`

VM `features-onchain-defi-backfill-20260505-210803` emitted:
```
FEATURE_WRITE_REJECTED  reason=write_gate_rejected  failed_checks=["2 columns exceed 95% NaN: ['aave_supply_apy', 'r..."]
                        feature_group=lending_rates  date=2026-04-09  rows=7460
```
**rows=7460** — calculator produced REAL data, just sparse. Write gate rejected because two columns exceed 95% NaN. The full failed_checks message is truncated; need to fetch the full event to know the second column.

**To fix**: read full `FEATURE_WRITE_REJECTED` event (`gcloud storage cat ...`); confirm which columns are >95% NaN and WHY. Hypotheses:
1. Most Aave V3 reserves don't have APY data on this day (sparse upstream)
2. Calculator's reserve-filtering is too broad
3. WriteGate threshold is too strict for this feature group

Possible fixes: loosen WriteGate threshold per-feature-group OR pre-filter reserves to populated set OR run lending_rates on a different day with denser coverage.

### Blocker 3: `funding_oi` (features-delta-one) still has decorative-theatre persist events

VM `features-delta-one-cefi-backfill-20260505-210748` emitted same pattern as the OLD features-onchain bug:
```
PROCESSING_COMPLETED  details={}  (empty)
FAILED  error="Handler returned False"
STOPPED  details={}
```
The fix at `266f512` was features-onchain ONLY. **features-delta-one needs the SAME class of fix** — its `_ingest_and_process` + `feature_writer` lifecycle events need to be moved to actual upload site with structured details (`rows_written, parquet_path, FEATURE_WRITE_REJECTED reason enum`). Until then, funding_oi failures are SILENT.

**To fix**: dispatch a subagent to features-delta-one-service to apply the SAME fix as `features-onchain-service@266f512`. Reference the diff in that commit. Then re-launch funding_oi VM to see what reason enum surfaces.

## STAGE PLAN — FOUR STAGES

User explicitly approved all 4 stages but acknowledged they'd be overnight/multi-day work.

### STAGE 1 — single-day per feature group (~30-60 min total)

For each of `lst_yields`, `lending_rates`, `funding_oi`: launch one VM for 2026-04-09 only, sample output, verify real data. lst_yields is DONE. lending_rates + funding_oi blocked on Blockers 1+2+3.

### STAGE 2 — 30-day window per feature group (~hours)

Once each feature group works on a single day, expand to 2026-03-15 → 2026-04-14 (30 days). This validates the iteration loop doesn't stall, leak memory, or emit cumulative state corruption. The lst_yields wider-window VM proved this is where stalls/Lookahead errors surface.

### STAGE 3 — RUN THE UNIFIED TRACER

This is THE goal. Once all 3 feature groups produce real 30-day output:
```bash
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/strategy-service
python scripts/trace_all_carry_archetypes.py \
  --start-date 2026-03-15 --end-date 2026-04-14 \
  --capital-usdc 1000000 --capital-eth 100 \
  [--archetype YIELD_STAKING_SIMPLE,CARRY_BASIS_PERP,CARRY_STAKED_BASIS,CARRY_RECURSIVE_STAKED,CARRY_BASIS_DATED,YIELD_ROTATION_LENDING,ARBITRAGE_PRICE_DISPERSION]
```
The tracer at `strategy-service@24a40d5` reads from features-onchain (`lst_yields`, `lending_rates`) and features-delta-one (`funding_oi`), drives V2BatchHarness across all 7 archetypes, ranks via `BaseRankAllocator` family, emits per-archetype + cross-archetype comparison parquets to `gs://strategy-store-{pid}/tracer_runs/CROSS_ARCHETYPE/{run_date}/`. CARRY_BASIS_DATED is honestly-skipped (no dated_basis_apy calculator shipped). Solana LSTs are honestly-empty for historical (Tier 3 REST limitation).

**This is the day's payoff** — gives the user the cross-archetype comparison for the carry strategy. Validate output sanity (winning slot per archetype, plausible APYs).

### STAGE 4 — full-historical backfill (overnight, ~4-12 hrs)

Once tracer works on 30 days, fan out:
1. **Delete partial mixed-quality MDPS output**: `gcloud storage rm -r gs://market-data-tick-{cefi,tradfi,defi,prediction}-{pid}/processed_candles/` (most days have pre-`ca4df75` broken aggregator output).
2. **Launch sharded MDPS** for cefi+tradfi+defi+prediction: `bash deployment-service/scripts/vm/launch-mdps-sharded-backfill.sh cefi tradfi defi prediction` (21 VMs, year-shards).
3. **Launch features-onchain backfills** for full lst_rates / lending_indices coverage: 2022-01-01 → 2026-04-14 narrow scope per feature_group.
4. **Launch features-delta-one funding_oi** for cefi (2022-11-02 → 2026-04-14) + defi (2021-09-01 → 2026-04-14).
5. **Re-run tracer** over a wide window (e.g. 6 months or 1 year) to compare archetype performance over varied funding regimes.

Each VM launch must be paired with event-stream verification per the no-fire-and-forget rule. Periodic check (every 15-30min) on the longest VMs.

## KEY BUCKET PATHS (verified 2026-05-05)

```
gs://lst-rates-{pid}/lst_rates/date={date}/lst_rates_{ts}.parquet                                    (legacy single-file, all tokens inside)
gs://lst-rates-{pid}/raw_tick_data/by_date/day=*/asset_group=defi/venue=*/...                       (canonical hive)
gs://lending-indices-{pid}/lending_indices/{protocol}/{chain}/date={date}/{protocol}_{CHAIN}_{ts}.parquet   ({CHAIN} uppercase!)
gs://oracle-prices-{pid}/day={date}/category=defi/venue=*/...                                       (bare day at root)
gs://perp-funding-{pid}/perp_funding/{venue}/date={date}/...
gs://market-data-tick-{ag}-{pid}/processed_candles/by_date/day=*/timeframe=*/data_type=*/venue=*/{instr}.parquet
gs://features-onchain-{pid}/by_date/day=*/feature_group={fg}/features.parquet                      (NO -defi suffix!)
gs://features-delta-one-{cefi|defi}-{pid}/by_date/day=*/feature_group={fg}/...                     (HAS -cefi/-defi suffix)
gs://strategy-store-{pid}/tracer_runs/CROSS_ARCHETYPE/{run_date}/...                                (tracer output)
gs://central-element-323112-events/events/{service}/{YYYY-MM-DD}/{vm-name}/hour=*/*.jsonl           (events)
```

## EVENT VERIFICATION PROTOCOL (every VM launch — copy this pattern)

```bash
# 90s after launch:
events_path="gs://central-element-323112-events/events/{service}/2026-05-05/{vm-name}/"
hour=$(gcloud storage ls "$events_path" | sort | tail -1)
last_file=$(gcloud storage ls "$hour" | sort | tail -1)
gcloud storage cat "$last_file" | python3 -c "import json,sys;d=json.loads(sys.stdin.read());print(d['event'], d.get('metadata',{}).get('details',{}))"
# Expect 'STARTED' first; later expect FEATURE_GROUP_PROCESSING_STARTED → FEATURE_GROUP_PROCESSING_COMPLETED with details.status=success and details.rows>0.
# If FEATURE_WRITE_REJECTED: read the reason enum to identify guard.
# If 'STOPPED' with empty details: that's the OLD bug pattern, REJECT — should not occur post-266f512 in features-onchain.
```

## DO NOT

- Re-fix the 5 already-shipped bugs (verify commits are on origin first).
- Run quickmerge.
- Use `--skip-dependency-check` to mask a real bug — it's only acceptable when the narrow feature_group genuinely doesn't read the missing upstream.
- Trust gcloud `STATUS=RUNNING` as proof of progress — always check events.
- Synthesize fake placeholder data when reader finds nothing. NaN + record_empty for honest gaps; raise loud for unexpected gaps.
- Skip the event-verification step. Production runs through `unified-events-interface` — silent VMs == invisible failures in production.

## START HERE

1. Read this entire file.
2. Check current state: `gcloud compute instances list --zones=asia-northeast1-c | grep -E "mdps-|features-"`. There should be 0 in-flight from this session — all auto-shutdown by handoff time.
3. Pick your battle: Blocker 1 (LookaheadBiasError), Blocker 2 (lending write_gate threshold), or Blocker 3 (features-delta-one persist events fix).
4. For Blocker 3: dispatch a subagent (general-purpose) referencing `features-onchain-service@266f512` as the template. The features-delta-one fix is structurally identical.
5. For Blocker 1: read `grep -rn LookaheadBiasError features-onchain-service/`, identify the guard, decide if false-positive vs real-bias.
6. For Blocker 2: read full `FEATURE_WRITE_REJECTED` event, identify the second NaN column, decide guard threshold vs reserve-filtering vs day-selection.
7. After each fix: refresh tarball, single-day validate, then 30-day validate, then unified tracer.

Good luck.
