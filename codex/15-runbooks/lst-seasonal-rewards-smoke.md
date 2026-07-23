---
doc_type: codex-runbook
title: LST Seasonal Rewards — Production Smoke Runbook
summary:
  Production smoke runbook (Phase 6 leveraged-leg-controller) for the daily LST seasonal-rewards collector — Secret
  Manager key checklist per chain, ad-hoc Cloud Run Job run, parquet round-trip via ParquetDustLoader, SIT full-chain
  dry-run, then cron enable + 24h first-fire monitoring + rollback.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, features-service, strategy-service, system-integration-tests, unified-trading-pm]
scope: [engineer]
tags: [runbook, defi, features, smoke-test, backfill, strategy]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md,
    ../../plans/archive/leveraged_leg_controller_2026_05_01.plan.md,
  ]
created: 2026-05-01
authoritative_for: [LST seasonal-rewards production smoke-test procedure]
referenced_by:
owner: ikenna
last_reviewed:
code_refs:
cadence: on-demand
verifier: operator
last_executed: never
---

# LST Seasonal Rewards — Production Smoke Runbook

Phase 6 of the leveraged-leg-controller plan. This runbook walks through validating the daily LST seasonal-rewards
collector against real keys + real RPCs before flipping the Cloud Scheduler cron on.

## What this runbook validates

1. The collector can authenticate against Secret Manager via `ApiKeyReloader`.
2. Every chain in `LST_REWARD_STREAMS` has a usable scanner (Web3 or Solana).
3. The scanner can pull at least one Transfer / claim event for a known distributor on the smoke day.
4. `OnChainFeatureWriter.write_seasonal_rewards` lands a parquet at the canonical
   `lst_seasonal_rewards/by_date/day=YYYY-MM-DD/...` path.
5. Strategy-service's `ParquetDustLoader` reads the parquet back and projects into `DustToken` rows for the configured
   holding wallet.
6. The dust-router fan in `V2EngineOrchestrator._fan_dust_router` produces a `ConvertDustInstruction` envelope when an
   engine declares a non-empty basket.

The unit-test + SIT layers cover (4)–(6) credential-free. (1)–(3) need real keys, so they only run as a manual smoke
against staging or prod.

## Pre-flight: Secret Manager key checklist

The collector needs the following secrets resolvable through `ApiKeyReloader` in the target project. Confirm each one
resolves before scheduling:

| Secret name (Secret Manager) | Used by                              | Chains gated               |
| ---------------------------- | ------------------------------------ | -------------------------- |
| `ALCHEMY_API_KEY`            | Web3 RPC for `make_web3_scanner`     | ETHEREUM / ARB / OP / BASE |
| `HELIUS_API_KEY`             | Solana RPC for `make_solana_scanner` | SOLANA                     |
| `ETHERSCAN_API_KEY`          | Etherscan fallback scanner           | ETHEREUM                   |
| `ARBISCAN_API_KEY`           | Arbiscan fallback                    | ARBITRUM                   |
| `OPTIMISMSCAN_API_KEY`       | Optimism Etherscan                   | OPTIMISM                   |
| `BASESCAN_API_KEY`           | Basescan                             | BASE                       |
| `POLYGONSCAN_API_KEY`        | Polygonscan                          | POLYGON                    |
| `BSCSCAN_API_KEY`            | BSCScan                              | BNB                        |
| `SNOWTRACE_API_KEY`          | Snowtrace                            | AVALANCHE                  |

The chain → scanner mapping is in
`features_onchain_service/collectors/lst_rewards_bootstrap.py:_CHAINS_REQUIRING_ETHERSCAN_KEYS` (SSOT; do not duplicate
the list here in code — copy the keys directly).

Verification one-liner (run from a workstation with `gcloud auth`):

```bash
PROJECT_ID=central-element-323112
for SECRET in ALCHEMY_API_KEY HELIUS_API_KEY ETHERSCAN_API_KEY ARBISCAN_API_KEY \
              OPTIMISMSCAN_API_KEY BASESCAN_API_KEY POLYGONSCAN_API_KEY \
              BSCSCAN_API_KEY SNOWTRACE_API_KEY; do
  gcloud secrets versions access latest --secret="$SECRET" --project="$PROJECT_ID" \
    >/dev/null 2>&1 \
    && echo "ok    $SECRET" \
    || echo "MISS  $SECRET"
done
```

Any `MISS` row blocks the smoke — the collector falls back to skipping that chain (D10 shard isolation), but the parquet
for that day will be incomplete and `RewardAttributionRow` rows for affected LSTs will never get written.

## Pre-flight: per-archetype holding-wallet schema

Strategy-service consumes the daily parquet via `ParquetDustLoader`, which filters by
`recipient_address == engine.identity.holding_wallet`. Before flipping the cron on, audit every
`StrategyInstanceDefinition` whose archetype subscribes to a restaking layer:

```bash
# In strategy-service, list every restaking-aware live instance and check
# whether identity.holding_wallet is populated.
python -c "
from strategy_service.engine.strategies.v2.registry import StrategyInstanceRegistry
from unified_api_contracts.internal import RESTAKING_AWARE_ARCHETYPES

reg = StrategyInstanceRegistry.load_from_firestore()  # or your env loader
for d in reg.all():
    if d.archetype_id not in RESTAKING_AWARE_ARCHETYPES:
        continue
    if not d.holding_wallet:
        print(f'MISSING  {d.strategy_instance_id}  archetype={d.archetype_id.value}')
    else:
        print(f'ok       {d.strategy_instance_id}  wallet={d.holding_wallet[:10]}...')
"
```

Any `MISSING` row blocks rewards going to that engine — fix by setting the `holding_wallet` field on the persisted
definition. The orchestrator reads the value through `params.get('holding_wallet') or definition.holding_wallet` (see
`strategy-service/strategy_service/engine/strategies/v2/orchestrator.py` in `register_instance`), so a
`params['holding_wallet']` override is also acceptable for ad-hoc runs.

## Smoke step 1: ad-hoc Cloud Run Job execution

Fire the Cloud Run Job manually (don't wait for the 02:25 UTC cron) against yesterday's UTC date:

```bash
ENV_PREFIX=prod  # or staging
JOB_NAME="${ENV_PREFIX}-features-onchain-collect-lst-seasonal-rewards"
REGION=asia-northeast1
PROJECT_ID=central-element-323112

gcloud run jobs execute "$JOB_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --wait
```

Expected exit code: `0`. Expected stdout (last lines):

```
INFO ... seasonal_rewards: chains_wired=('ETHEREUM','ARBITRUM',...)
INFO ... seasonal_rewards: collected N events for day YYYY-MM-DD
INFO ... feature_writer: wrote gs://features-onchain-{project}/seasonal_rewards/by_date/day=YYYY-MM-DD/issuer=ETHERFI/chain=ETHEREUM/rewards.parquet
```

If the exit code is nonzero, pull logs:

```bash
gcloud logging read \
  "resource.labels.job_name=\"$JOB_NAME\" AND severity>=ERROR" \
  --project="$PROJECT_ID" --limit=50 --format=json | jq '.[].textPayload'
```

Common failures + diagnosis:

| Symptom                                              | Likely cause                                                        |
| ---------------------------------------------------- | ------------------------------------------------------------------- |
| `KeyError: 'ALCHEMY_API_KEY'` at startup             | Secret Manager key missing; see the pre-flight checklist            |
| `chains_wired=()` and 0 events                       | Every per-chain scanner failed; check `ADAPTER_FETCH_FAILED` events |
| `block_range_resolver: no block found for ...`       | Chain RPC is rate-limited or down; back off and retry               |
| Job times out at 2400s (`timeout` in Terraform)      | Increase `timeout` in `lst_seasonal_rewards_scheduler.tf`           |
| `recipient_address.lower()` doesn't match any wallet | `holding_wallet` casing drift; the loader lowercases both sides     |

## Smoke step 2: parquet round-trip

Confirm the parquet landed at the canonical path:

```bash
gsutil ls "gs://features-onchain-${PROJECT_ID}/seasonal_rewards/by_date/day=$(date -u -d 'yesterday' +%Y-%m-%d)/"
```

Then read one row back through the loader's expected schema:

```bash
python -c "
from features_onchain_service.collectors.parquet_dust_loader import ParquetDustLoader

class FakeEngine:
    class identity:
        holding_wallet = '0x...your wallet here...'
    params = {'native_asset': 'ETH'}

loader = ParquetDustLoader(
    project_id='${PROJECT_ID}',
    wallet_resolver=lambda e: e.identity.holding_wallet,
    target_denom_resolver=lambda e: e.params.get('native_asset', 'ETH'),
)
result = loader(FakeEngine(), '$(date -u -d 'yesterday' +%Y-%m-%d)')
print(f'tokens={len(result[0]) if result else 0}, target_denom={result[1] if result else None}')
"
```

Expected: `tokens=N, target_denom=ETH` for `N >= 1` if your wallet had any restaking rewards on the smoke day. If
`N == 0`, double-check the `recipient_address` field in the parquet matches the configured wallet (case-insensitive).

## Smoke step 3: full-chain dry-run via SIT

The credential-free SIT in `system-integration-tests` exercises the full chain (parquet → loader → engine → orchestrator
→ dust-router → matching engine → reward attribution row). Run it before flipping the cron:

```bash
cd system-integration-tests
bash scripts/quality-gates.sh -- \
  -k test_phase6_reward_realisation_e2e
```

Expected: 5 tests pass (full-chain happy path, unregistered fallback, multi-engine, persister-failure isolation,
real-parquet round-trip).

## Cron enable + first-fire monitoring

Once steps 1–3 pass, enable the cron in Terraform (it ships paused if you prefer to flip it manually). The cron name
follows the `${ENV_PREFIX}-features-onchain-collect-lst-seasonal-rewards-cron` pattern.

Watch the first scheduled fire (02:25 UTC) for 24h, then confirm:

- The Cloud Run Job exits 0 (Cloud Scheduler dashboard).
- A new parquet shows up under `gs://features-onchain-{project}/seasonal_rewards/by_date/day=YYYY-MM-DD/`.
- The features-onchain T+1 recon (02:30 UTC) reads the parquet without errors (its `ADAPTER_FETCH_FAILED` event count
  for `seasonal_rewards` data_type stays at 0).
- Strategy-service tick logs show `Phase6Driver: installed N dust tokens` for at least one engine on the next live tick.

## Rollback

The cron is independent of every other DAG node, so disabling it is safe:

```bash
gcloud scheduler jobs pause \
  "${ENV_PREFIX}-features-onchain-collect-lst-seasonal-rewards-cron" \
  --location="$REGION" --project="$PROJECT_ID"
```

Strategy-service degrades gracefully: `ParquetDustLoader` returns `None` when the day's parquet is missing, the
orchestrator's `_fan_dust_router` short- circuits on `basket is None`, and engines simply never realise rewards for that
day. No downstream `RewardAttributionRow` is emitted, so the `pnl-attribution-service` consumer skips reward-layer P&L
for the affected strategies on the affected day. No corruption, no cascading failure.

## Related

- Architecture SSOT: `/codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md`
- Plan: `unified-trading-pm/plans/archive/leveraged_leg_controller_2026_05_01.plan.md` (Phase 6)
- Terraform: `deployment-service/terraform/gcp/lst_seasonal_rewards_scheduler.tf`
- Daily script: `features-service (onchain family)/scripts/collect_lst_seasonal_rewards_daily.py`
- Bootstrap: `features-service (onchain family)/features_onchain_service/collectors/lst_rewards_bootstrap.py`
- Loader: `features-service (onchain family)/features_onchain_service/collectors/parquet_dust_loader.py`
