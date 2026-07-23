---
doc_type: issue
title: Paper-trade smoke runbook — carry_staked_basis Solana hedge (Tab 1 work-split 2026-05-08 Item 1 deliverable)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
author: ikenna-tab1-main
source:
  - plans/active/work_split_2026_05_08_ikenna.md § "TAB 1 — DeFi launch + Fork 1 completion" Item 1
  - plans/active/defi_master_2026_05_07.md § "Fork 1 paper-trade smoke" pre-flight items
  - /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md (archetype spec)
  - Tab 1 sub-agent design pass 2026-05-08 (Plan-mode sub-agent output)
  - { cursor-configs/CLAUDE.md § "DeFi Execution Architecture" + § "Batch = Live: Unified Pipeline Architecture" }
locked_by: live-defi-rollout
locked_since: 2026-05-08
execution:
  {
    owner: Tab 1 (DeFi launch) — execution depends on V1-RETIRE blocker fix,
    cadence: daily once V1-RETIRE blocker fixed,
    verifier:
      all 4 service event streams emit STARTED+progress+STOPPED + paper fills + position events + P&L attribution,
    last_executed: "2026-05-08 (FAILED on colocated_engine.py:306 ImportError)",
  }
---

# Paper-trade smoke runbook — `carry_staked_basis` Solana hedge

> **Severity**: P0 — May-23 lead-archetype gating step. Smoke must pass before live trading on real wallet **Blast
> radius**: 4 services + 4 GCS buckets + Solana mainnet RPC reads (read-only) **Suggested owner**: defi_master Fork 1 +
> operator (smoke run is operator-driven; this runbook is the deliverable)

## What this is

Step-by-step operator-runnable paper-trade smoke for the May-23 lead archetype `carry_staked_basis` Solana leg. Runbook
exercises the full unified service mesh in batch mode with execution-service "always fill" matching engine — verifying
the strategy-service round-trip wiring per CLAUDE.md "Batch = Live: Unified Pipeline Architecture" without execution
alpha (zero conflation between strategy P&L and execution quality).

## Pre-flight verification (must hold before smoke)

1. **MTDS DeFi VMs drained**:
   `gcloud compute instances list --zones=asia-northeast1-c --filter="name~mtds-(lending-indices|lst-rates|oracle-prices|vault-share-price|gas-fees)-" --format='value(name,status)'`
   — expect zero RUNNING. (Background: pre-flight backfills shipped 2026-05-08 morning; new VMs need refreshed tarball
   before relaunch.)
2. **Tarballs refreshed for DEFI asset_group post-UAC@6c873e4 (drift-fix bundle) + UAC@92eab58 (Stream A) + UAC
   oracle_coverage commit**: `gsutil stat gs://deployment-scripts-${PROJECT_ID}/code/defi-tarball.tar.gz` — `mtime` must
   post-date `2026-05-08 13:30 UTC`. Refresh:
   `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group DEFI`.
3. **features-onchain Docker `:latest` rebuilt** post-Phase 9 calculator catalog rerun:
   `gcloud artifacts docker images describe asia-northeast1-docker.pkg.dev/${PROJECT_ID}/features-onchain-service/features-onchain-service:latest --format='value(updateTime)'`
   — must post-date last features-onchain commit on `live-defi-rollout`.
4. **Pyth Hermes endpoint reachable (jitoSOL feed)**:
   `curl -sS -o /dev/null -w "%{http_code} %{time_total}s\n" https://hermes.pyth.network/api/latest_price_feeds?ids[]=0x67be9f519b95cf24338801051f9a808eff0a578ccb388db73b7f6fe1de019ffb`
   — expect `200 < 3s` (already shown 200 in 2.3s on 2026-05-08 morning).
5. **Solana RPC reachable**:
   `curl -sS -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' $(python3 -c "from unified_api_contracts.registry.capability_declarations import SOLANA_RPC_TEMPLATES; print(SOLANA_RPC_TEMPLATES['mainnet'])")`
   — expect `{"result":"ok"}`. The Solana RPC SSOT is `SOLANA_RPC_TEMPLATES` in
   `unified_api_contracts/registry/capability_declarations/_defi_chain_data.py` (verified 2026-05-08 — Tab 1 sub-agent
   confirmed it exists in the UAC facade).
6. **4-service QG passes** (`strategy-service`, `execution-service`, `risk-and-exposure-service`,
   `features-onchain-service`) — `cd <repo> && bash scripts/quality-gates.sh 2>&1 | tail -5` per repo.
7. **basedpyright clean** across the four — `cd <repo> && timeout 120 basedpyright <repo_python_pkg>/` exit 0 per repo.
8. **SSH key + ADC available** for VM launch — `gcloud auth application-default print-access-token > /dev/null` +
   `gcloud compute os-login ssh-keys list | head -3`.
9. **PBM wallet adapter healthy** —
   `curl -sS http://localhost:8013/health | jq '.checks.wallet_adapter, .checks.data_freshness'` (PBM
   `make_health_router` per CLAUDE.md § "Service Infrastructure Requirements" STEP 5.62).
10. **UAC `VENUE_COLLATERAL_MATRIX` rows for `(DRIFT, JitoSOL)` + `(DRIFT, mSOL)`** flagged `accepted=True`:
    `python3 -c "from unified_api_contracts.registry.venue_collateral import venue_accepts_collateral; print(venue_accepts_collateral('DRIFT','JitoSOL'), venue_accepts_collateral('DRIFT','mSOL'))"`
    — expect `(True, True)`. Stream A flips landed at UAC@92eab58.
11. **features-onchain `staking_apy_total` non-NaN for jitoSOL** for yesterday:
    `python -m features_onchain_service --operation backtest --mode batch --asset-group defi --feature-group lst_yields --instruments JITOSOL --start-date $(date -v-1d +%F) --end-date $(date -v-1d +%F) --dry-run`
    — expect non-empty `staking_apy_bps`.

**KNOWN BLOCKERS (audited 2026-05-08, defer post-smoke):**

- **Pacifica entry pending** in `VENUE_COLLATERAL_MATRIX` per `defi_master_2026_05_07.md:370-375` — DRIFT slots are
  sufficient for paper-smoke; Pacifica/Solana JitoSOL slot will not exist until that row lands.
- **Custody adapter health (Copper sandbox / CEFFU)** is a live-only prerequisite per
  `master_to_live_defi_2026_05_23.md` Group F — paper-smoke does NOT require live custody.

## Service mesh wiring

### Strategy-service archetype runner

**CLI shape** (`strategy-service/strategy_service/cli/service_entry.py:1-7, 433`):

```bash
cd strategy-service && python -m strategy_service \
  --operation backtest --mode batch --asset-group defi \
  --strategies CARRY_STAKED_BASIS --instruments JITOSOL,MSOL \
  --timeframes 1h --date $(date -v-1d +%F) \
  --output-mode report --load-execution-results --max-workers 1
```

**Config**: `strategy-service/strategy_service/configs/carry_staked_basis/jito-drift-f100-usdc-1h-usdc-v2-prod.yaml`
(catalog slot per `carry-staked-basis.md:140-146`). YAML schema per `carry-staked-basis.md:156-177` —
`staking_protocol: JITO`, `lst_asset: JitoSOL`, `perp_venue: DRIFT`, `perp_instrument: SOL-PERP`, `spot_venue: JUPITER`,
`stake_fraction: "1.0"`, `entry_bps: "200"`, `exit_bps: "50"`, `min_health_factor: "1.25"`, `hedge_deadline_ms: "5000"`.

**Engine**: `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py`. **Allocator**:
`CarryStakedBasisRankAllocator` in `strategy-service/strategy_service/portfolio_allocator/archetypes.py`.

**Expected events**: `STARTED`, `VALIDATION_COMPLETED`, `MODE_INITIALIZED`, `DATA_INGESTION_COMPLETED`,
`PROCESSING_STARTED`, `PREDICTION_LOADING_COMPLETED`, `STRATEGY_EXECUTION_STARTED`, `STRATEGY_SIGNAL_EMITTED`,
`STRATEGY_DECISION_LOGGED`, `STRATEGY_EXECUTION_COMPLETED`, `PROCESSING_COMPLETED`, `SIGNALS_READY`, `STOPPED`.

### Execution-service in always-fill matching-engine mode

**CLI shape** (per `execution-service/execution_service/cli/parser.py:60-97`):

```bash
cd execution-service && python -m execution_service \
  --operation backtest --mode batch \
  --start-date $(date -v-1d +%F) --end-date $(date -v-1d +%F)
```

`execution-service` has `add_asset_group_arg=False` per `parser.py:7`. Matching-engine path lives at
`execution-service/execution_service/matching_engine/engine.py` and `algo_library/dust_router_runner.py:25`. Per
CLAUDE.md "Batch = Live": `--mode batch` returns simulated fills at requested price (zero execution alpha) — this is the
canonical paper fill source.

**Expected events**: `STARTED`, `ORDER_RECEIVED` × 4 legs, `EXECUTION_FILL_EMITTED` × 4 legs (SWAP, STAKE, TRANSFER,
TRADE), `ATOMIC_INSTRUCTION_COMPLETED` with `legs_completed=4`, `STOPPED`.

### Position-balance-monitor consuming fills

**CLI shape** (per `position-balance-monitor-service/position_balance_monitor_service/cli/main.py:127-136`):

```bash
cd position-balance-monitor-service && python -m position_balance_monitor_service \
  --operation monitor --mode batch \
  --start-date $(date -v-1d +%F) --end-date $(date -v-1d +%F) \
  --skip-startup-recon
```

**Expected events**: `STARTED`, `POSITION_OPENED`, `POSITION_DELTA_RECONCILED`, `POSITION_SNAPSHOT_EMITTED`, `STOPPED`.

### Risk-and-exposure-service co-located check

**CLI shape** (per `risk-and-exposure-service/risk_and_exposure_service/cli/main.py:50, 117`):

```bash
cd risk-and-exposure-service && python -m risk_and_exposure_service \
  --operation monitor --mode batch \
  --start-date $(date -v-1d +%F) --end-date $(date -v-1d +%F)
```

**Gating role** (pre-fill): consumes `STRATEGY_SIGNAL_EMITTED`; emits `RISK_PASS` or `RISK_REJECT` BEFORE
execution-service picks up the order. **Post-fill role**: consumes `EXECUTION_FILL_EMITTED` +
`POSITION_SNAPSHOT_EMITTED`; emits `EXPOSURE_LIMIT_CHECK` and `HEALTH_FACTOR_CHECK`.

**Expected events**: `STARTED`, `RISK_PASS`, `HEALTH_FACTOR_CHECK` with `breach=false`, `STOPPED`.

## Round-trip happy path runbook

Run on a single GCE VM (`asia-northeast1-c`, region-co-located) so the four services share the same event bus + GCS
reads.

| Step | Command                                                                                                                                                                                                                                                                                                                                                                                                | Expected outcome                                                                                   |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| 1    | `PROJECT_ID=<pid>; SMOKE_DATE=$(date -v-1d +%F); CORRELATION_ID=carry-staked-basis-smoke-$(date +%Y%m%d-%H%M%S); export PROJECT_ID SMOKE_DATE CORRELATION_ID`                                                                                                                                                                                                                                          | env exported                                                                                       |
| 2    | Pre-flight checks 1-11 above all green                                                                                                                                                                                                                                                                                                                                                                 | all PASS                                                                                           |
| 3    | Start PBM in background: `cd position-balance-monitor-service && nohup python -m position_balance_monitor_service --operation monitor --mode batch --start-date $SMOKE_DATE --end-date $SMOKE_DATE --skip-startup-recon > pbm.log 2>&1 &`                                                                                                                                                              | `STARTED` event in `gs://${PROJECT_ID}-events/.../position-balance-monitor-service/...` within 60s |
| 4    | Start risk: `cd risk-and-exposure-service && nohup python -m risk_and_exposure_service --operation monitor --mode batch --start-date $SMOKE_DATE --end-date $SMOKE_DATE > risk.log 2>&1 &`                                                                                                                                                                                                             | `STARTED` event                                                                                    |
| 5    | Start execution: `cd execution-service && nohup python -m execution_service --operation backtest --mode batch --start-date $SMOKE_DATE --end-date $SMOKE_DATE > exec.log 2>&1 &`                                                                                                                                                                                                                       | `STARTED` event                                                                                    |
| 6    | Issue archetype start (drives the smoke): `cd strategy-service && python -m strategy_service --operation backtest --mode batch --asset-group defi --strategies CARRY_STAKED_BASIS --instruments JITOSOL --timeframes 1h --date $SMOKE_DATE --output-mode report --load-execution-results --config-gcs gs://${PROJECT_ID}-config/strategy/carry_staked_basis/jito-drift-f100-usdc-1h-usdc-v2-prod.yaml` | strategy iterates 1 date, allocator scores `jito-drift` slot, signal emitted                       |
| 7    | Risk gating fires on signal                                                                                                                                                                                                                                                                                                                                                                            | `RISK_PASS` event with `headroom_usdc>0`, `decision_ts < signal_ts + 200ms`                        |
| 8    | Execution drives 4-leg AtomicInstruction (SWAP USDC→SOL on JUPITER, STAKE SOL→JitoSOL on Jito, TRANSFER JitoSOL→DRIFT, TRADE SHORT SOL-PERP on DRIFT)                                                                                                                                                                                                                                                  | matching engine returns 4 fills at requested price                                                 |
| 9    | PBM consumes fills, opens position, snapshots wallet                                                                                                                                                                                                                                                                                                                                                   | `POSITION_OPENED` with `lst_balance>0`, `perp_short_qty>0`; `health_factor ≥ 1.25`                 |
| 10   | Risk post-fill check on snapshot                                                                                                                                                                                                                                                                                                                                                                       | `HEALTH_FACTOR_CHECK` with `breach=false`                                                          |
| 11   | Strategy emits batch end + persistence                                                                                                                                                                                                                                                                                                                                                                 | `gs://strategy-store-${PROJECT_ID}/by_strategy/CARRY_STAKED_BASIS/day=${SMOKE_DATE}/...`           |
| 12   | P&L attribution computed                                                                                                                                                                                                                                                                                                                                                                               | `gs://pnl-store-${PROJECT_ID}/by_strategy/CARRY_STAKED_BASIS/day=${SMOKE_DATE}/...` 1 row          |
| 13   | All four services emit `STOPPED`                                                                                                                                                                                                                                                                                                                                                                       | event stream confirms drain                                                                        |
| 14   | Wait 60s for event-stream propagation, then run verification queries below                                                                                                                                                                                                                                                                                                                             | all green                                                                                          |

## Verification queries (per CLAUDE.md "No fire-and-forget VM launches")

For each service ∈ `{strategy-service, execution-service, position-balance-monitor-service, risk-and-exposure-service}`:

```bash
SVC=<service>
PROJECT_ID=<pid>
SMOKE_DATE=$(date -v-1d +%F)
CID=carry-staked-basis-smoke-<RUN_TS>

# (1) Confirm partition exists
gcloud storage ls gs://${PROJECT_ID}-events/events/${SVC}/${SMOKE_DATE}/${CID}/

# (2) Confirm STARTED first event
gcloud storage cat gs://${PROJECT_ID}-events/events/${SVC}/${SMOKE_DATE}/${CID}/hour=*/000.jsonl \
  | head -1 | jq '.event'   # expect "STARTED"

# (3) Confirm progress events (no silent-success)
gcloud storage cat gs://${PROJECT_ID}-events/events/${SVC}/${SMOKE_DATE}/${CID}/hour=*/*.jsonl \
  | jq -r '.event' | sort | uniq -c

# (4) Confirm STOPPED final event
gcloud storage cat gs://${PROJECT_ID}-events/events/${SVC}/${SMOKE_DATE}/${CID}/hour=*/*.jsonl \
  | tail -1 | jq '.event, .metadata.details'   # expect "STOPPED" with non-empty details
```

**Per-service expected event presence in `uniq -c`**:

| Service                          | Required events                                                                                                                                                            |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| strategy-service                 | `STARTED`, `VALIDATION_COMPLETED`, `PROCESSING_STARTED`, `STRATEGY_SIGNAL_EMITTED`, `STRATEGY_DECISION_LOGGED`, `STRATEGY_EXECUTION_COMPLETED`, `SIGNALS_READY`, `STOPPED` |
| execution-service                | `STARTED`, `ORDER_RECEIVED`, `EXECUTION_FILL_EMITTED` (×4 legs), `ATOMIC_INSTRUCTION_COMPLETED`, `STOPPED`                                                                 |
| position-balance-monitor-service | `STARTED`, `POSITION_OPENED`, `POSITION_DELTA_RECONCILED`, `POSITION_SNAPSHOT_EMITTED`, `STOPPED`                                                                          |
| risk-and-exposure-service        | `STARTED`, `RISK_PASS`, `HEALTH_FACTOR_CHECK`, `STOPPED`                                                                                                                   |

**Bucket spot-checks**:

- `gcloud storage ls gs://strategy-store-${PROJECT_ID}/by_strategy/CARRY_STAKED_BASIS/day=${SMOKE_DATE}/` — non-empty.
- `gcloud storage ls gs://execution-store-${PROJECT_ID}/fills/strategy=CARRY_STAKED_BASIS/day=${SMOKE_DATE}/` — 4
  parquets.
- `gcloud storage ls gs://pnl-store-${PROJECT_ID}/by_strategy/CARRY_STAKED_BASIS/day=${SMOKE_DATE}/` — 1 row.

## Failure-mode triage

1. **Solana RPC rate-limit / 429** — symptom: `STAKE` leg never `EXECUTION_FILL_EMITTED`, exec.log shows
   `web3.exceptions.TooManyRequests`. Fix: switch to paid Helius/QuickNode tier in UAC `SOLANA_RPC_TEMPLATES`.
2. **Pyth jitoSOL price feed stale** — symptom: `STRATEGY_DECISION_LOGGED` shows `staking_apy_bps=NaN`. Fix: confirm
   Hermes endpoint reachable; check archive coverage start (UAC `ORACLE_COVERAGE_START["pyth_hermes"]` = 2023-10-01) —
   if smoke date is pre-2023-10, clip the date window.
3. **Aave flash-loan-receiver contract missing** — symptom: execution-service `connect()` fails with
   `ValueError: missing contract`. Note: `LST_AS_MARGIN`-only structure does NOT use Aave. If this fires, an upstream
   regression has re-enabled the borrow path. Fix: confirm archetype config has no `lending_protocol` / `borrow_asset`
   keys.
4. **Uniswap router approve failed** — Note: `spot_venue: JUPITER` for Solana, NOT Uniswap-V3. If misconfigured to
   Uniswap on Ethereum, USDC→SOL fails because SOL isn't an EVM ERC20. Fix: hard-set `spot_venue: JUPITER` in slot
   config.
5. **DRIFT does NOT accept JitoSOL as cross-margin** — symptom: catalog regenerator produces 0 slots; allocator returns
   all-zeros; no `STRATEGY_SIGNAL_EMITTED`. Fix: ensure `(DRIFT, JitoSOL, accepted=True, haircut=10%)` row is present in
   `VENUE_COLLATERAL_MATRIX` (Stream A landed UAC@92eab58).
6. **`min_health_factor` breach at snapshot** — symptom: `HEALTH_FACTOR_CHECK` emits `breach=true`. Fix: confirm PBM is
   reading DRIFT's haircut from venue spec; verify entry gate at `carry-staked-basis.md:175` works.

## Done definition (matches work-split TAB 1 Item 1)

- [ ] **Paper fill lands in execution-service**: 4 leg parquets in
      `gs://execution-store-${PROJECT_ID}/fills/strategy=CARRY_STAKED_BASIS/day=${SMOKE_DATE}/` AND 4
      `EXECUTION_FILL_EMITTED` events with `source="matching_engine"`.
- [ ] **PBM reflects open position**: `POSITION_OPENED` with `lst_balance>0` AND `perp_short_qty>0`,
      `POSITION_DELTA_RECONCILED` shows `delta_bps < tolerance`, `POSITION_SNAPSHOT_EMITTED` shows
      `health_factor ≥ 1.25`.
- [ ] **Strategy P&L attribution computed**: 1 row in
      `gs://pnl-store-${PROJECT_ID}/by_strategy/CARRY_STAKED_BASIS/day=${SMOKE_DATE}/` with non-NaN `net_apy_bps`
      decomposed to `staking_apy_bps + funding_apy_bps - fees_bps` per `carry-staked-basis.md:194-205`.
      `staking_apy_bps` matches features-onchain `lst_rates` rate-diff.
- [ ] **No execution-alpha conflation**: per CLAUDE.md "Batch = Live", every leg has `fill_price == requested_price`
      (within 1e-9). Verification command in sub-agent's output.
- [ ] **All four services emit STARTED + progress + STOPPED**: per § verification queries.
- [ ] **Risk gate observed pre-fill**: `RISK_PASS` `decision_ts < first_fill_ts`.
- [ ] **No `record_failed` events on the smoke day**: zero `FAILED`/`REJECTED` events.

## Why it matters

`carry_staked_basis` is the May-23 lead archetype per `master_to_live_defi_2026_05_23.md`. Without a green paper-trade
smoke, the May-23 LIVE-on-real-wallet milestone has no end-to-end proof that strategy → execution → PBM → risk wiring
works. Paper-smoke isolates strategy P&L from execution alpha (matching engine fills at requested price) so a regression
in the strategy P&L surface is detectable independently of fill-quality measurement.

## Recommended decision

**Operator runs the runbook on a region-co-located GCE VM**. This runbook is the deliverable; execution is
operator-driven (requires GCP creds + Solana RPC reads). Tab 1 (this main agent) cannot run the smoke on the operator's
behalf since the matching-engine writes to `gs://execution-store-${PROJECT_ID}/...` which is operator-permissioned.

When green, fold the verification evidence (commit shas + smoke run log + manifest spot-check) into the
`master_to_live_defi_2026_05_23.md` Group F item 17 status block.

## DONE-2026-05-08 — Tab 1 main (runbook deliverable)

This runbook is the Item 1 deliverable for the 2026-05-08 work-split. Sub-agent (Plan-mode) produced the design pass;
this issue doc captures the durable record. Next operator run produces the paper-fill round-trip.

Source design pass: Tab 1 sub-agent fan-out 2026-05-08 ~13:30 UTC, Plan-mode general-purpose agent. Cross-references:

- Pre-flight checklist (steps 1-11) — Tab 1 sub-agent + this doc.
- Service mesh wiring tables — Tab 1 sub-agent + verified in repo via direct file reads.
- Verification queries — CLAUDE.md § "No fire-and-forget VM launches" template.
- Failure-mode triage — Tab 1 sub-agent + Stream A audit.
