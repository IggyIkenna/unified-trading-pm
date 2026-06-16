---
scope: [engineer, admin]
title: VM Launcher Runbook
type: infrastructure
status: living
last_reviewed: 2026-05-17
execution:
  owner: "deployment-platform"
  cadence: "per VM-launcher add/change"
  verifier:
    "bash deployment-service/scripts/vm/launch-*.sh --help (per-launcher); reference existing examples in
    deployment-service/scripts/vm/launch-*.sh"
  last_executed: "2026-05-17 (slot-8 frontmatter codification)"
---

# VM Launcher Runbook

**Author**: slot-2 agent  
**Date**: 2026-05-15  
**Scope**: All `deployment-service/scripts/vm/launch-*.sh` (83 launchers)  
**Owner**: Harsh (infra/ops) / Ikenna (strategy/DeFi gate decisions)  
**Verifier**: QG STEP 5.69 (bucket naming) + shellcheck (security)  
**Last executed**: 2026-05-15 (slot-2 security audit sweep)

---

## How To Use This Runbook

Every section below: **When to use → Required args → Expected duration → Common failures**.

For VM naming rules see `codex/05-infrastructure/launcher-script-ssot.md`.  
For event emission see `codex/05-infrastructure/vm-event-emission-audit.md`.  
For tarball creation see `codex/05-infrastructure/vm-tarball-deployment.md`.  
For log backup, archival, and kill/teardown runbook see `codex/05-infrastructure/vm-log-archival.md`.

---

## 1. Infrastructure / Cron VMs

### `launch-vm-zombie-watchdog.sh`

- **When**: Re-deploy after editing `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py`. Run once; VM self-perpetuates.
- **Required**: none (uses defaults: `PROJECT_ID`, `ZONE`)
- **Duration**: ~2 min launch + permanent running
- **Failures**: `vm-zombie-watchdog-*` already RUNNING → delete old first. Watchdog has no singleton lock.

### `launch-qg-snapshot-vm.sh`

- **When**: Daily QG snapshot collection (cron). Manual trigger for ad-hoc baseline.
- **Required**: none (env via `DEPLOYMENT_ENV`)
- **Duration**: ~10-15 min
- **Failures**: VM prefix `qg-snapshot-` must be in `VM_PREFIX_TO_BUCKET`. GCS write fails → check bucket
  `deployment-scripts-${PROJECT}` exists.

### `launch-measure-honest-coverage-vm.sh`

- **When**: On-demand honest-coverage measurement. Cloud Scheduler triggers daily (pending IAM for
  `cloudscheduler.jobs.create`).
- **Required**: none
- **Duration**: ~10-15 min
- **Failures**: Coverage JSON not written → check `gs://central-element-323112-honest-coverage/` bucket exists (created
  2026-05-15). Bucket creation: `gsutil mb -l asia-northeast1 gs://central-element-323112-honest-coverage`.

### `launch-honest-coverage-vm.sh`

- **When**: B-018 cron pattern. Same as `launch-measure-honest-coverage-vm.sh` but uses `honest-coverage-` prefix
  (heartbeat-only watchdog registration).
- **Required**: none
- **Duration**: ~10-15 min
- **Failures**: Same as `launch-measure-honest-coverage-vm.sh`.

### `launch-disaster-drill-cron-vm.sh` / `launch-dr-drill-cutover-vm.sh`

- **When**: Disaster recovery drill (quarterly). Human-initiated with explicit operator confirmation.
- **Required**: `--confirm-dr-drill` flag
- **Duration**: ~30-60 min (full failover simulation)
- **Failures**: IAM insufficient → needs `compute.instances.create` + `storage.buckets.*` on DR project.

---

## 2. MTDS (Market Tick Data) Backfill VMs

All MTDS launchers follow the same pattern. `CODE_BUCKET` resolves to `deployment-scripts-${PROJECT}`.

### `launch-mtds-backfill-vm.sh`

- **When**: Backfill market tick data for a date range across all asset groups.
- **Required**: `--asset-group <CEFI|DEFI|TRADFI|SPORTS|PREDICTION>` `--start-date YYYY-MM-DD` `--end-date YYYY-MM-DD`
- **Duration**: 30 min – 4 hours depending on date range + asset group
- **Failures**: Tarballs stale → run `create-code-tarballs.sh --asset-group X` first. BQ quota exceeded → reduce date
  range.

### `launch-mtds-perp-funding-backfill-vm.sh`

- **When**: Backfill perp funding rates (CeFi venues).
- **Required**: `--start-date` `--end-date`
- **Duration**: ~30-60 min/week of data
- **Failures**: Venue API rate limit → reduce date range. Hyperliquid/Bybit credential expiry → Secret Manager check.

### `launch-mtds-dex-pools-backfill-vm.sh`

- **When**: Backfill DeFi DEX pool data (Uniswap, Curve, Balancer).
- **Required**: `--start-date` `--end-date`
- **Duration**: ~1-2 hours/week (on-chain RPC intensive)
- **Failures**: RPC rate limit → verify Alchemy API key via Secret Manager. Pool not found → check UAC DEX registry.

### `launch-mtds-eigenlayer-rewards-backfill-vm.sh`

- **When**: Backfill EigenLayer restaking rewards.
- **Required**: `--start-date` `--end-date`
- **Duration**: ~20-40 min
- **Failures**: EigenLayer API unavailable → check `EIGENLAYER_API_KEY` in Secret Manager.

### `launch-mtds-liquidations-backfill-vm.sh`

- **When**: Backfill on-chain liquidation events.
- **Required**: `--start-date` `--end-date`
- **Duration**: ~30-60 min
- **Failures**: RPC node timeout → retry with smaller date range.

### `launch-mtds-pyth-archive-backfill-vm.sh` / `launch-mtds-pyth-lst-backfill-vm.sh`

- **When**: Backfill Pyth price oracle data (Solana). Pyth UNBANNED 2026-05-06.
- **Required**: `--start-date` `--end-date`
- **Duration**: ~30-60 min
- **Failures**: Pyth archive endpoint rate limit → uses `PYTH_ARCHIVE_API_KEY` from Secret Manager.

### Other MTDS launchers (same pattern)

`launch-mtds-gas-fees-backfill-vm.sh`, `launch-mtds-gas-fees-fleet-vm.sh`, `launch-mtds-lending-indices-backfill-vm.sh`,
`launch-mtds-lst-rates-backfill-vm.sh`, `launch-mtds-prediction-backfill-vm.sh`,
`launch-mtds-solana-drift-backfill-vm.sh`, `launch-mtds-solana-gas-backfill-vm.sh`,
`launch-mtds-sports-odds-backfill-vm.sh`, `launch-mtds-vault-share-price-backfill-vm.sh`

All: `--start-date` `--end-date` required. Duration 20-90 min. Failure: see MTDS launcher SSOT.

---

## 3. Forward-Poll VMs (Live Mode)

Forward-poll VMs run continuously (no end date). Self-delete on shutdown.

### `launch-cefi-forward-poll.sh`

- **When**: Start live CeFi market data streaming (Binance, Bybit, OKX, etc.).
- **Required**: `--asset-group CEFI`
- **Duration**: Continuous until terminated or VM deleted
- **Failures**: Singleton lock — refuses if `cefi-fwd-*` already RUNNING. Use `--force` to bypass.

### `launch-defi-forward-poll.sh`

- **When**: Start live DeFi data streaming (DEX events, on-chain prices).
- **Required**: `--asset-group DEFI` + Alchemy key in Secret Manager
- **Duration**: Continuous
- **Failures**: RPC provider down → check `WEB3_PROVIDER_URI` derivation from Secret Manager.

### `launch-footystats-forward-poll.sh` / `launch-sfi-forward-poll.sh`

- **When**: Live sports data polling.
- **Required**: API credentials in Secret Manager
- **Duration**: Continuous (match-day driven — typically 4-6 hours/day of active data)
- **Failures**: API key expired → credential rotation required.

### `launch-prediction-forward-poll.sh` / `launch-tradfi-forward-poll.sh`

- **When**: Live prediction markets / TradFi data polling.
- **Required**: Venue credentials in Secret Manager
- **Duration**: Continuous
- **Failures**: Market hours affect data volume (TradFi: NYSE/LSE hours).

---

## 4. Features Backfill VMs

### `launch-features-backfill-vm.sh`

- **When**: Backfill computed features for any asset group.
- **Required**: `--asset-group <CEFI|DEFI|TRADFI|SPORTS|PREDICTION>` `--start-date` `--end-date`
- **Duration**: 1-3 hours/month of data
- **Failures**: Missing MTDS data → run MTDS backfill first. Schema drift → UAC contract check.

### `launch-features-onchain-backfill-vm.sh`

- **When**: Backfill on-chain DeFi features (EigenLayer, LST, DEX).
- **Required**: `--start-date` `--end-date` + Alchemy key
- **Duration**: 2-4 hours/month
- **Failures**: RPC rate limit → reduce parallelism via `--max-workers`.

### `launch-features-sports-backfill-vm.sh` / `launch-features-sports-parallel-backfill-vm.sh`

- **When**: Backfill sports features. Parallel variant fans out per fixture.
- **Required**: `--start-date` `--end-date`
- **Duration**: 1-2 hours for parallel, 4-8 hours for serial
- **Failures**: Footystats API gaps → check manifest `empty_confirmed` entries first.

### `launch-prediction-features-vm.sh`

- **When**: Backfill prediction market features.
- **Required**: `--start-date` `--end-date`
- **Duration**: ~30-60 min
- **Failures**: Polymarket/Kalshi API rate limit → check API key in Secret Manager.

---

## 5. Strategy VMs

### `launch-strategy-test-vm.sh`

- **When**: Full L1-L7 pipeline backtest for a strategy.
- **Required**: `--asset-group` `--strategy <ID>` `--start-date` `--end-date`
- **Optional**: `--mode batch|backtest|paper|live` `--dry-run` `--skip-tarballs`
- **Duration**: 30 min – 4 hours (date range + strategy complexity)
- **Failures**: No backfill-cluster.sh → falls back to e2e script. Coverage: DEPLOYMENT_STARTED/COMPLETED now emitted
  (fixed 2026-05-15 setup-data-pipeline-vm.sh restructure).

### `launch-strategy-live-vm.sh`

- **When**: Live DeFi strategy execution. **Requires `--dry-run-live-cutover-passed` OR `--force-live`**.
- **Required**: `--archetype <carry_staked_basis|arbitrage_price_dispersion>` `--dry-run-live-cutover-passed`
- **Duration**: Continuous until terminated
- **Failures**: Phase 8 dry-run gate not passed → use `--force-live` only with full operator awareness. Wallet key
  required (human-only hard-stop).

### `launch-strategy-paper-vm.sh`

- **When**: Paper trading — live signals, simulated fills.
- **Required**: `--archetype` `--start-date`
- **Duration**: Continuous
- **Failures**: Missing live data → ensure forward-poll VMs running.

### `launch-strategy-backtest-grid-vm.sh`

- **When**: Grid search over strategy parameters.
- **Required**: `--archetype` `--param-grid <json-file>` `--start-date` `--end-date`
- **Duration**: Hours to days depending on grid size
- **Failures**: Grid size exceeds VM memory → use `--shard-index` / `--shard-count` to split.

---

## 6. Validation / Recon VMs

### `launch-amm-golden-fixture-validation-vm.sh`

- **When**: Phase 2 AMM fixture validation. Validates DEX swap fixtures against real on-chain data.
- **Required**: `--shape <UNISWAP_V3|UNISWAP_V4|CURVE_STABLE|...>` OR `--all-shapes`
- **Optional**: `--capture` (fresh RPC capture) `--force` (bypass singleton lock) `--dry-run`
- **Duration**: ~5-15 min/shape; ~45 min for `--all-shapes`
- **Failures**: Alchemy key required for `--capture`. Results:
  `gs://{pid}-defi-validation/results/amm/{date}/{shape}/...`

### `launch-aave-lending-rate-validation-vm.sh`

- **When**: Validate Aave lending rate calculations against on-chain truth.
- **Required**: Alchemy key in Secret Manager
- **Duration**: ~10-20 min
- **Failures**: RPC timeout → retry. Results in `gs://{pid}-defi-validation/results/aave/...`

### `launch-manifest-recon-all-vm.sh` / `launch-manifest-recon-apply-vm.sh`

- **When**: Detect and optionally fix phantom manifest rows.
- **Required**: `--asset-group X` (recon-all) or `--asset-group X --apply` (recon-apply)
- **Duration**: 15-30 min (recon-all); 30-60 min (recon-apply)
- **Failures**: Do NOT apply without recon-all dry-run first. Phantom rows → see
  `reconcile_phantom_manifest_rows_all.py`.

### `launch-defi-phantom-recon-vm.sh`

- **When**: DeFi-specific manifest phantom reconciliation.
- **Required**: `--dry-run` first; then `--apply` once verified
- **Duration**: ~20-40 min
- **Failures**: Same as manifest-recon-apply.

### `launch-batch-live-recon-cron-vm.sh`

- **When**: Daily batch vs live consistency check (cron).
- **Required**: none
- **Duration**: ~15 min
- **Failures**: Mismatches → check batch/live pipeline parity per CLAUDE.md "Live = batch (CRITICAL)".

---

## 7. Instruments / Reference Data VMs

### `launch-instruments-backfill-vm.sh`

- **When**: Backfill instrument reference data (universe, metadata, OHLCV).
- **Required**: `--asset-group` `--start-date` `--end-date`
- **Duration**: 20-60 min
- **Failures**: instruments-service not deployed → deploy first.

### `launch-instruments-smoke-vm.sh`

- **When**: Post-deploy smoke test for instruments-service.
- **Required**: none
- **Duration**: ~10 min
- **Failures**: Schema drift → check UAC instrument contracts.

### `launch-cefi-instruments-backfill.sh`

- **When**: CeFi-specific instrument backfill (exchange listings, contract specs).
- **Required**: `--start-date` `--end-date`
- **Duration**: ~20 min
- **Failures**: Venue API changes → check venue SDK version.

---

## 8. Sports VMs

### `launch-footystats-backfill-vm.sh`

- **When**: Backfill Footystats historical fixture data.
- **Required**: `--start-date` `--end-date` + Footystats API key
- **Duration**: 1-3 hours/season
- **Failures**: API quota → check tier (free = 500 req/day; paid = unlimited). Gaps in known seasons →
  `is_in_known_gap()` check.

### `launch-sports-full-sweep-vm.sh` / `launch-sports-entity-sweep-vm.sh`

- **When**: Full sweep of sports entities (teams, leagues, fixtures).
- **Required**: `--asset-group SPORTS`
- **Duration**: 2-4 hours (full sweep)
- **Failures**: Entity ID drift → reconcile with Transfermarkt/Footystats source IDs.

### `launch-sports-manifest-rescan-vm.sh`

- **When**: Rescan sports manifest for coverage gaps.
- **Required**: `--start-date` `--end-date`
- **Duration**: ~15-30 min
- **Failures**: Phantom rows from old failed runs → run `launch-defi-phantom-recon-vm.sh` first.

### `launch-transfermarkt-backfill-vm.sh` / `launch-understat-backfill-vm.sh`

- **When**: Backfill additional sports data sources.
- **Required**: `--start-date` `--end-date`
- **Duration**: 30-90 min
- **Failures**: Rate limit → use `--delay-ms` parameter.

---

## 9. ML Training VMs

### `launch-ml-training-vm.sh`

- **When**: Train ML models (CatBoost, LightGBM) for signal generation.
- **Required**: `--asset-group` `--model-type <catboost|lightgbm>` `--start-date` `--end-date`
- **Optional**: `--n-trials <N>` for hyperparameter search
- **Duration**: 30 min – 4 hours (model complexity + date range)
- **Failures**: OOM → upgrade to `n2-highmem-8`. catboost_info artifacts → in .gitignore (do not commit).

---

## 10. Admin / Migration VMs

### `launch-canonical-migration-vm.sh`

- **When**: Schema migration across GCS parquet files.
- **Required**: `--asset-group` `--migration-version`
- **Duration**: 1-6 hours (data volume dependent)
- **Failures**: Schema drift detected mid-run → VM reports mismatch to GCS; inspect log before re-running.

### `launch-canonical-smoke-vm.sh`

- **When**: Smoke test canonical schema after migration.
- **Required**: none
- **Duration**: ~10 min
- **Failures**: Schema mismatch → run canonical-migration-vm first.

### `launch-cefi-sharded-backfill.sh`

- **When**: Large CeFi backfill split across multiple VMs (sharded by venue/date).
- **Required**: `--shard-index` `--shard-count` `--start-date` `--end-date`
- **Duration**: 1-3 hours/shard
- **Failures**: Shard count mismatch → all shards must use same `--shard-count`.

### `launch-execution-alpha-vm.sh`

- **When**: Execution alpha testing (latency, fill rate analysis).
- **Required**: `--archetype` `--start-date` `--end-date`
- **Duration**: ~30 min
- **Failures**: Requires execution-service tarball current.

---

## Common Failure Patterns (All Launchers)

| Failure                                   | Diagnosis                   | Fix                                                               |
| ----------------------------------------- | --------------------------- | ----------------------------------------------------------------- |
| `ERROR: No code tarball found`            | Tarballs not uploaded       | `bash create-code-tarballs.sh --asset-group X`                    |
| VM spins up then immediately exits        | Startup script error        | `gsutil cat gs://.../vm-logs/{VM_NAME}/run.log`                   |
| `PERMISSION_DENIED` on GCS write          | Missing IAM binding         | Check VM service account has `storage.objectCreator`              |
| DEPLOYMENT_STARTED not emitted within 60s | Heartbeat sidecar failed    | Check vm-exec-with-gcs-tee.sh download from GCS                   |
| `Unknown VM prefix` in watchdog           | New launcher not registered | Add prefix to `VM_PREFIX_TO_BUCKET` in vm_zombie_watchdog.py      |
| VM running >4h (zombie)                   | Pipeline hung               | `gcloud compute instances delete {VM_NAME} --zone={ZONE} --quiet` |
| Bucket name hardcoded (pre-B-011)         | Old launcher style          | Refactor to `${PROJECT}` pattern per `launcher-script-ssot.md`    |
| SC2046 shellcheck warning                 | Unquoted flag substitution  | Use `EXTRA_FLAGS=()` array pattern                                |

---

## References

- `codex/05-infrastructure/launcher-script-ssot.md` — naming, CODE_BUCKET, tarball patterns
- `codex/05-infrastructure/vm-tarball-deployment.md` — tarball creation + deployment
- `codex/05-infrastructure/vm-event-emission-audit.md` — event emission chain
- `codex/05-infrastructure/vm-security-audit.md` — shellcheck security audit
- `deployment-service/deployment_service/vm/vm_zombie_watchdog.py` — VM_PREFIX_TO_BUCKET registry
