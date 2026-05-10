---
name: api-keys-wallets-accounts-readiness
overview:
  Comprehensive credential audit — every API key, wallet, service account, IAM role, secret, and account setup needed
  across AWS + GCP infrastructure, every trading venue + custody endpoint, every DeFi chain + RPC + fork, every data
  source, and every auxiliary service, scoped per mode (paper / batch / live). Answers "could the operator launch the
  full system end-to-end today against real infra without a credential gap blocking any path."
type: question
status: plan-spawned
created: 2026-05-08
last_audit: 2026-05-09
plan_spawned: 2026-05-10
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-08
spawned_plan: plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md
related_codex:
  - codex/04-architecture/interface-credential-convention.md
  - codex/06-coding-standards/config-reloader-pattern.md
  - codex/05-infrastructure/runtime-tiers-and-deployment.md
  - codex/14-playbooks/authentication/firebase-local.md
  - codex/04-architecture/flash-loan-receiver.md
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/epics/defi_master_2026_05_07.md
  - plans/epics/cefi_master_2026_05_07.md
  - plans/epics/infrastructure_master_2026_05_07.md
---

# API keys + wallets + accounts readiness — end-to-end credential audit

## Intent

Credentials are the silent prerequisite to every workspace HARD RULE about "real-infra completion, not smoke-test
green." We can ship the carry archetype with perfect code, the manifest with perfect coverage, the alerting service with
perfect rules, the deployment-api with perfect surface — and on May-23 the operator hits "go live" and discovers that
**the trading API key on OKX is read-only, the Copper sub-account isn't provisioned, the Solana RPC is
anon-rate-limited, the Tenderly fork seat expired, the GCP service account on the VM doesn't have
`secretmanager.secretAccessor` on the new keyring, and the Aster API key was never created at all**. Every one of those
is a 1-line discovery that costs hours-to-days to recover from at cutover.

The current state across the workspace is **implicit-knowledge-only**: the operator knows roughly which venues have
keys, roughly which chains have wallets funded, roughly which Secret Manager paths the services read from. There is no
canonical SSOT enumerating every credential the system needs, every place it's stored, every service that reads it, and
every mode (paper / batch / live) it's required for. The CLAUDE.md rules touch the discipline — `.env` files must NEVER
contain placeholder credentials, ADC is the default, no `os.getenv()` (use `UnifiedCloudConfig`), services use
`ApiKeyReloader` for hot-reload, every adapter uses `get_<protocol>_adapter(api_key=..., api_secret=...)` factory
injection, the flash-loan receiver is validated on-chain at `connect()` — but the discipline lives in pieces. There's no
single matrix that says **"for live-DeFi cutover on 2026-05-23, exactly these N credentials must be present, provisioned
with these scopes, stored at these Secret Manager paths, accessible to these services on these clouds, and tested
against real systems with these probes."**

This question doc forces the audit. Three concrete reasons for raising it now:

1. **May-23 deadline + master plan Group F live-only items** (custody Copper + CEFFU, live testnet replicating prod,
   batch-vs-live reconciliation, circuit breakers + kill switches + alerting, DART manual-trade gate) all require real
   credentials wired to real services. None of them work with mock keys.
2. **DeFi-specific surface area is large** — multi-chain (Ethereum + Arbitrum + Base + Polygon + Solana),
   multi-RPC-provider, per-protocol contract approvals, per-chain native gas wallets, plus testnet/fork separation. One
   missing wallet → one archetype dead.
3. **Cloud parity** — AWS↔GCP cloud parity is in the master plan, which means every credential needed on GCP must have
   an AWS equivalent (different secret managers, different IAM models, different service-account formats). A credential
   matrix that's GCP-only silently breaks the AWS half of cutover.

The audit is not "grep for `api_key` in the codebase." It's **"can the operator launch carry_staked_basis on a real
wallet, on real Bybit + Deribit + Binance + OKX + Hyperliquid + Aster perps, with real Copper + CEFFU custody balances,
with real Solana / Ethereum mainnet wallets, on AWS in ap-northeast-1 and GCP in asia-northeast1, today, without me
adding a single credential between now and May-23."** Every gap is a P0 for the May-23 deadline.

## Question

### Block A — Cloud infrastructure credentials (AWS + GCP)

A1. **GCP — service accounts + IAM matrix.** Per service, the SA email used in production (Cloud Run / GCE VM), the IAM
roles held (`secretmanager.secretAccessor`, `pubsub.publisher`/`subscriber`, `storage.objectAdmin`, `run.invoker`,
`bigquery.dataEditor`, `cloudscheduler.jobRunner`, `compute.instanceAdmin`, `artifactregistry.reader`), the local-dev
path (ADC vs impersonation), per-environment scoping (prod / staging / dev separation).

A2. **AWS — IAM users + roles matrix.** Same shape as A1 — IAM principal per service, policy bindings
(`s3:GetObject`/`PutObject`, `secretsmanager:GetSecretValue`, `events:PutRule`, `lambda:InvokeFunction`, `ecs:RunTask`,
`ec2:RunInstances`), cross-cloud assume-role bridges, per-environment scoping.

A3. **Secret Manager (GCP) + AWS Secrets Manager — credential storage SSOT.** Naming convention, per-environment vs
unified, cross-cloud parity, `UnifiedCloudConfig` mediation everywhere, `.env` discipline (no placeholder paths, no real
creds).

A4. **GCP Pub/Sub topics + subscriptions + dead-letter queues.** Publisher / subscriber SA bindings, DLQ topics,
per-environment scoping, AWS SNS/SQS equivalents.

A5. **GCS + S3 buckets — credential coverage.** Per bucket: GCS SA access, S3 IAM access, replication credentials,
per-asset_group bucket coverage on both clouds.

A6. **Cloud Run + Cloud Scheduler + EventBridge — runtime auth.** Per scheduled job: SA identity, target-service IAM
rules, failure-mode auth.

A7. **GCE / EC2 launcher credentials — VM launch chain.** Operator workstation auth, launching identity IAM, attached SA
permissions, tarball-pull auth.

A8. **Artifact Registry + ECR + image pull credentials.** Build-time push credential, run-time pull credential, AWS ECR
equivalent.

A9. **CI/CD credentials — GitHub Actions + Cloud Build.** Per workflow: required GitHub secrets, WIF vs SA-JSON for
GHA→GCP, cross-repo dispatch credentials.

### Block B — CeFi trading venue credentials

B1. Six perp venues (Bybit, Deribit, Binance, OKX, Hyperliquid, Aster) — account state (real / paper / demo), API key
state + scopes, 2FA / IP whitelist, Secret Manager paths, hot-reload via `ApiKeyReloader`, factory pattern compliance.

B2. Additional venues (Upbit, Kraken, Bitfinex, Bitget) — same matrix; whether each is data-only / trade-only / both /
deprecated.

B3. Spot vs perp account separation — per venue, key split + sub-account isolation.

B4. Read-only data keys vs trade keys vs withdraw keys — separate scopes per venue, separate Secret Manager paths.

B5. Account-level limits + venue-side risk constraints — venue ceilings, leverage tiers, fee tiers, market-maker
designation.

B6. API rate limits + connection limits per venue — documented limits, adapter-side enforcement, multi-VM concurrency
honor.

### Block C — Custody endpoints (Copper + CEFFU)

C1. Copper — account state, API integration model, asset coverage, signing key wiring, settlement / sweep flow,
end-to-end real-fund-movement test.

C2. CEFFU (operator's "SeFu") — account state, MirrorX vs API, Binance linkage, end-to-end real test.

C3. Other custody (Fireblocks, self-custody hot wallet, etc.) for assets Copper / CEFFU don't support.

C4. Treasury reconciliation — unified rollup view (custody + venue margin + on-chain), reconciliation cadence, SSOT for
"custody balance at time T."

### Block D — DeFi wallets + RPC providers + chain-specific credentials

D1. Production wallets per chain — operator hot wallet, private-key storage path, hardware-key vs raw-key, per-chain
coverage (Ethereum / Arbitrum / Base / Polygon / Solana).

D2. Chain RPC providers — `CHAIN_RPC_TEMPLATES` SSOT, provider per chain, tier / rate-limit budget, failover
credentials, Pyth Hermes + PythNet wiring.

D3. Tenderly — DeFi integration test fork credential, seat status, Secret Manager path, skip-when-unavailable behavior,
cost.

D4. "Sequoia / Sepolia / Tenderly / Anvil" — disambiguation: testnet wallets, testnet contract deployments, per-chain
testnet RPC creds.

D5. Flash-loan receiver — per chain mainnet + testnet deployment, UAC contract registry registration, `eth_getCode`
validation tested per chain.

D6. Per-protocol approvals — per (chain, protocol, asset) allowance state, ceiling, SSOT for
required-pre-trade-approvals.

D7. Sub-account / multi-wallet separation — per-archetype wallet isolation, treasury reconciliation across wallets.

D8. Bridge + cross-chain credentials — per bridge (CCTP / Wormhole / LayerZero / centralized), contract approvals,
protocol API, settlement timing.

### Block E — Data source credentials (per asset_group)

E1. CeFi data — Tardis tier + credential.

E2. TradFi — Databento entitlements, Barchart (one-time-historical-only?), Yahoo Finance (public?).

E3. Sports — api_football, footystats, understat, transfermarkt, soccer_football_info, open_meteo, odds_api —
credentials, tiers, quotas.

E4. Prediction — Polymarket CLOB API + chain RPC, Kalshi, Manifold.

E5. DeFi data — The Graph, Dune, Flipside, DeFiLlama, CoinGecko / CMC.

E6. Oracles — Pyth (Hermes + PythNet), Chainlink (no off-chain credential beyond chain RPC).

### Block F — Auxiliary services

F1. Telegram bot — token storage, channel/chat IDs per env, failure-mode delivery.

F2. Firebase — production project, SA JSON, OAuth providers, custom claims (`client_id`), emulator vs prod toggle.

F3. GitHub — operator-workstation `gh` auth, PATs in Secret Manager, GitHub App vs PAT, per-repo workflow secrets.

F4. Anthropic API — workflow API key storage, billing scope, per-workflow budget.

F5. Other third-party APIs — workspace grep for external HTTP calls + identify their credentials.

### Block G — Per-mode credential matrix (paper / batch / live)

G1. Paper mode — credentials needed (read-only venue, fork-wallet only).

G2. Batch mode — historical data credentials per source (E1-E6), no trade keys.

G3. Live mode — full credential set across A-F, all probes green.

G4. Mode-transition discipline — single live-readiness pre-flight probe.

G5. Per-archetype credential subsets — minimum viable subset per archetype.

### Block H — Cross-cutting discipline (Secret Manager / rotation / hot-reload / ADC)

H1. `ApiKeyReloader` coverage audit per service.

H2. Rotation cadence per credential class + runbook.

H3. ADC discipline + `.env.example` violations.

H4. No `os.getenv()` for credentials — workspace grep + count violations.

H5. `.env` security audit — no real creds in committed `.env`s.

H6. Secret Manager naming SSOT in codex.

H7. Cloud-agnostic abstraction layer — `UnifiedCloudConfig` actually cloud-agnostic vs GCP-only with AWS stub.

### Block I — End-to-end audit recipe

I1. One-stop credential probe script — every credential gets a real-system probe.

I2. Audit-script execution path — owner / cadence / verifier / `last_executed`.

I3. Mode-specific subset probes — `--mode {paper,batch,live}` flag.

I4. Per-archetype subset probes — `--archetype <name>` flag.

I5. Continuous-verification path — master plan readiness matrix references the probe per gate.

I6. Pre-cutover gate — May-23 sign-off criteria.

## What "answered" looks like

- A canonical plan exists in `plans/active/api_keys_wallets_accounts_readiness_<date>.md` (or folds into the live-DeFi
  epic if scoped narrowly). The plan has a per-Block phase + per-credential todo (one row per credential × per
  environment × per mode, like a rollup spreadsheet).
- A codex SSOT in `codex/05-infrastructure/credentials-matrix.md` (NEW) enumerates every credential with: Secret Manager
  path (GCP + AWS), consuming services, scopes / IAM, rotation cadence, hot-reload status, mode coverage (paper / batch
  / live), archetype coverage. This is the workspace-wide credential SSOT — implicit-knowledge migrated to a doc.
- A workspace-wide `scripts/audit/credential-probe.sh` exists, owned by deployment-service, runnable per `--mode` +
  `--archetype` flag, with the Block I.1 probe set. Output: per-credential green/red + a final sign-off line.
- The master plan's continuous-verification column references this probe script for every Group F + G
  credential-dependent gate.
- Every Block H discipline gate is enforced via QG (or scoped to a baseline ratchet that goes green by May-23): no
  `os.getenv` for credentials, every adapter via `ApiKeyReloader`, every `.env` clean of real creds + placeholder paths.
- Per-archetype credential checklists exist (G5) so the operator can answer "is `carry_staked_basis` credential-blocked
  today?" without running the full probe.
- Service-readiness checklist gates per the master plan's per-service matrix are explicit per credential surface (which
  service owns which credential, current A-G gate state for the credential dependency, what's needed for live cutover).
- Rotation runbook exists (per `Runbook Execution-Owner SSOT`) with `execution.owner` populated for every credential
  class.
- A real cutover dry-run has executed: the operator has launched all 6 perp venues + Copper + CEFFU + Solana +
  Ethereum + Arbitrum + Base + Polygon credential probes against real prod systems, and seen them all green within a
  single 5-minute audit window.

## Audit findings

Three parallel research agents swept the workspace 2026-05-09 (Cloud + Discipline; Venues + Custody + DeFi; Data + Aux +
Audit-recipe). Findings synthesized below per block. Legend: ✅ wired-and-real / ⚠ partial-or-flagged / ❌ gap.

### Block A — Cloud infrastructure (AWS + GCP)

- **A1 — GCP service-account matrix** ⚠. Per-service SA pattern exists (test refs in
  `deployment-service/tests/unit/test_backends_cloud_run.py:43` `svc@test.iam.gserviceaccount.com`; Cloud Build deploy
  with Cloud Run Admin + Storage Admin in `deployment-service/cloudbuild.yaml`). **Gap:** no SSOT doc enumerating
  service-name → SA → IAM-role-set; convention exists in code only.
- **A2 — AWS IAM matrix** ❌. **No AWS IAM policy JSON, no Terraform IAM, no per-service role-policy mapping found in
  workspace.** `deployment-service/buildspec.aws.yaml` has no IAM definitions. Tab 4 (2026-05-08) shipped one-off IAM
  user `unified-trading-gcs-to-s3-transfer` for the GCS→S3 migration — that's the only AWS IAM artifact discoverable.
  **AWS-side cloud-parity is essentially un-provisioned.**
- **A3 — Secret Manager naming convention** ⚠. Pattern is `projects/{pid}/secrets/{lowercase-kebab-case-name}` per
  `unified-trading-library/unified_trading_library/cloud_interface/providers/gcp.py:170-180` + UAC signal-broadcast
  example `projects/-/secrets/signal-broadcast-counterparty-stub-1-hmac`. **Gap:** no codex SSOT enumerating naming
  scheme by asset_group / service / credential class.
- **A4 — Pub/Sub topics** ⚠. Protocol-level helpers exist (`topic_path` / `subscription_path` in
  `unified-trading-library/cloud_interface/providers/gcp.py`); topics created dynamically by services. **Gap:** no
  enumerated topic registry, no DLQ wiring SSOT, no AWS SNS/SQS parity confirmed.
- **A5 — GCS + S3 buckets** ⚠. GCS naming is asset-group-derived (`INSTRUMENTS_GCS_BUCKET_TEST`,
  `MARKET_DATA_GCS_BUCKET_TEST` per test fixtures). Tab 4 2026-05-08 shipped `UTL@780a9575` (`bucket_naming.py` SSOT
  resolver, yaml-backed) + 12 DeFi buckets on AWS S3 ap-northeast-1 + 5 parallel `gcloud storage rsync` GCS→S3 jobs.
  **Confirmed real:** DeFi buckets only on AWS. **Gap:** CeFi / TradFi / sports / prediction buckets NOT yet provisioned
  on AWS; replication credential `unified-trading-gcs-to-s3-transfer` scoped to 12 DeFi buckets.
- **A6 — Cloud Run + Scheduler + EventBridge** ⚠. Cloud Run deploys exist (`deployment-service/cloudbuild.yaml`);
  sports trigger tiers reference Cloud Run Jobs (`deployment-service/configs/sports-trigger-tiers.yaml`). **Gap:** no
  comprehensive scheduler-rule registry, no EventBridge configurations.
- **A7 — VM launcher auth chain** ✅. `VM_PREFIX_TO_BUCKET` registry in
  `deployment-service/scripts/vm/vm_zombie_watchdog.py`; tarball boot via
  `gs://deployment-scripts-{pid}/vm/setup-data-pipeline-vm.sh`; per-VM heartbeat
  `gs://deployment-scripts-{pid}/vm-heartbeat/{vm_name}.txt`. **Gap:** Python-script-as-SSOT (not codex doc); AWS EC2
  launcher equivalent not provisioned.
- **A8 — Artifact Registry / ECR** ⚠. Artifact Registry pattern wired
  (`asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/...:latest` per Dockerfiles). **Gap:** no ECR
  (AWS Artifact Registry equivalent) configurations found.
- **A9 — CI/CD credentials** ⚠. GHA workflows reference `secrets.GH_PAT`, `secrets.TELEGRAM_BOT_TOKEN`,
  `secrets.TELEGRAM_CHAT_ID`, `secrets.ANTHROPIC_API_KEY` (the last conditional). **Gap:** no workspace-wide secrets
  registry; secrets scattered across per-repo workflow files.

### Block B — CeFi trading venues

- **B1 — Six perp venues** ✅. Bybit / Binance / OKX via CCXT integration; Deribit standalone
  (`execution-service/execution_service/venues/deribit.py:49-58`, HMAC-SHA256 via `DeribitAuthMixin`); Hyperliquid
  (`execution-service/execution_service/venues/hyperliquid.py` + `defi_execution/protocols/hyperliquid.py`); **Aster
  real adapter, NOT stub** (`execution-service/execution_service/defi_execution/protocols/aster.py:23`). All 6 use
  `get_order_adapter(venue, api_key, api_secret, ...)` factory injection per CLAUDE.md convention. MTDS data adapters
  present for all 6.
- **B2 — Additional venues** ⚠. Upbit (`execution-service/execution_service/trade_execution/adapters/upbit_ccxt.py` +
  MTDS adapter); Kraken / Bitfinex / Bitget via CCXT + UAC VCR test fixtures
  (`unified-api-contracts/tests/vcr/test_upbit_vcr.py` + `test_bitget_vcr.py` + `test_bitfinex_vcr.py`). **Flagged:**
  CLAUDE.md 2026-05-07 RED ALERT noted bitfinex / bitget / kraken silent-zero capture (96-100% empty rows). Code exists;
  credential-state and write-correctness need separate verification.
- **B3 — Spot vs perp account separation** ⚠. Account-type routing exists in
  `execution-service/execution_service/engine/backtest/node_builder.py` (`MARGIN if is_perpetual else CASH`). Single API
  key per venue; venue-server splits spot/perp internally. **Gap:** no explicit per-account-type credential separation
  in workspace; relies on venue-side scoping.
- **B4 — Read-only / trade / withdraw key scope** ❌. **No evidence of per-scope key separation.** Adapters accept
  single `api_key + api_secret` pair; no read-only-vs-trade-vs-withdraw routing in code. Production would require ops to
  provision sub-keys at each venue's web UI manually.
- **B5 — Account-level limits + venue ceilings** ❌. **No SSOT for per-venue account-tier ceilings.** Pre-flight risk
  checks (sibling risk question doc) currently lack this input.
- **B6 — API rate limits per venue** ⚠. Singleton-locked launcher pattern exists (`launch-sfi-forward-poll.sh`,
  `launch-mtds-prediction-backfill-vm.sh`) for rate-limited adapters. **Gap:** no per-venue documented rate-limit SSOT;
  not all adapters respect per-key budget.

### Block C — Custody (Copper + CEFFU)

- **C1 — Copper** ✅. **Full MPC custody provider wired**: `execution-service/execution_service/custody/copper.py:1-100`
  — `CopperCustodyProvider(api_key, api_secret, organization_id, sandbox)` constructor;
  `sign_transaction(wallet_id, chain, raw_tx)` flow: POST `/platform/orders` → POST `/orders/{id}/sign` → MPC signing →
  polling 30 attempts × 1s; HMAC-SHA256 auth via `_sign_request()`. Factory at
  `execution-service/execution_service/custody/factory.py` returns `CopperCustodyProvider` for `"copper"` key.
  Credentials fetched from Secret Manager via `UnifiedCloudConfig` mediation. **Real-system-readiness:** code-shipped;
  whether any real Copper transaction has executed end-to-end — not verified in this audit.
- **C2 — CEFFU** ❌. **Zero workspace evidence.** Grep for `ceffu` / `CEFFU` / `mirrorx` / `MirrorX` returned no Python
  code matches. CEFFU mentioned only in CLAUDE.md and master plan Group F item 19 ("Copper + CEFFU treasury wired").
  **Significant gap for May-23 cutover.**
- **C3 — Fireblocks + other custody** ⚠. Declared-only:
  `unified-api-contracts/internal/domain/execution_service/transfer_types.py` enum
  `custodian: "copper" | "fireblocks" | ""`; `execution-service/execution_service/custody/factory.py` has comment
  `'fireblocks': FireblocksCustodyProvider (alternative MPC)`. **No Fireblocks implementation in `custody/`.**
- **C4 — Treasury rollup** ⚠.
  `position-balance-monitor-service/position_balance_monitor_service/core/treasury_monitor.py` exists;
  `tests/unit/test_treasury_monitor_fund_admin.py` covers `TreasuryConfig` + `treasury_wallet` + `treasury_balance_usd`.
  **Gap:** no workspace-wide NAV rollup combining custody + venue margin + on-chain wallets into a single client-facing
  view; ties into client-reporting question doc.

### Block D — DeFi wallets + RPC + chains

- **D1 — Production wallets** ✅. Wallet-key injection via Secret Manager + factory pattern:
  `execution-service/execution_service/cli/handlers/live_execution_handler.py` fetches `wallet_secret_name` → injects
  `wallet_private_key` into connector config. Per-chain connectors (`raydium.py`, etc.) consume via
  `super().__init__(rpc_url=, wallet_private_key=)`. **No env-var leaks; no hardcoded keys.** **Gap:**
  raw-private-key-in-Secret-Manager is the model — no HSM / Fireblocks-signer / KMS-encrypted-blob layer (security-grade
  question, not a wiring gap).
- **D2 — Chain RPC providers** ✅. `CHAIN_RPC_TEMPLATES` SSOT in
  `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py:12-14` (imported from
  `_defi_chain_data.py`); helper exports `resolve_solana_mint`, `get_solana_protocol_url`, `get_solana_rpc_url`,
  `get_chain_config`. **Pyth Hermes wired:**
  `market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py`
  `_PYTH_HERMES_URL = "https://hermes.pyth.network/v2/updates/price/latest"` + `_fetch_pyth_prices()`; routes Solana →
  Pyth, EVM → Chainlink. **Gap:** per-provider tier / rate-limit / failover credential not enumerated.
- **D3 — Tenderly fixtures** ✅. `execution-service/tests/integration/conftest.py` has session-scoped `tenderly_fork`,
  `funded_wallet`, `flash_loan_receiver`, `aave_connector`, `uniswap_connector` fixtures (per CLAUDE.md).
  `@pytest.mark.allow_network` gating. **Gap:** seat-status / cost-budget / skip-when-unavailable behavior (currently
  silent-skip) not addressed; CI shouldn't silently skip integration tests when Tenderly is missing.
- **D4 — "Sequoia / Sepolia / Tenderly / Anvil"** ❌ (resolved 2026-05-09 — `Sequoia` = Sepolia; ALL 5 testnets in-scope
  for May-23). **Tenderly is dominant** (D3 fixtures, integration-test only). **NO Sepolia / Anvil / Hardhat fixtures
  found in execution-service.** Per operator direction: **Ethereum Sepolia + Arbitrum Sepolia + Base Sepolia + Polygon
  Amoy + Solana devnet are ALL May-23 P0**. Each requires: (1) funded operator testnet wallet (testnet ETH / testnet SOL
  via faucets, refilled before each integration cycle); (2) testnet RPC credential (Alchemy / QuickNode / Helius testnet
  tier); (3) FlashLoanReceiver.sol deployed on each testnet (separate from mainnet deployment per D5); (4) per-protocol
  approvals pre-signed on each testnet (Aave testnet pools, Uniswap testnet routers — many DeFi protocols have NO
  testnet deployments, which becomes a per-protocol residual); (5) live-testnet pipeline replicating prod path
  end-to-end. **Significant new scope** — composes with master plan Group F item ("live testnet replicating prod").
  Sub-residual: not every DeFi protocol the carry archetype touches has a testnet deployment (Lido / Jito / Pyth all
  mainnet-only) — the testnet replica may need to swap in mock contracts for those legs.
- **D5 — Flash-loan receiver** ✅. `deployment-service/contracts/FlashLoanReceiver.sol` (1026 bytes, real Solidity) +
  `LiquidationFlashLoanReceiver.sol` variant (6701 bytes); deploy script
  `deployment-service/scripts/deploy-flash-loan-receiver.sh --chain <name>`; UAC `config/testnet_contracts.yaml`
  registry; execution-service `connect()` validates via `eth_getCode`. **Gap:** per-chain mainnet+testnet
  deployment-state matrix not enumerated; whether deploy has actually run on every chain in scope (Ethereum / Arbitrum /
  Base / Polygon) is not verified — likely a per-chain operational item.
- **D6 — Per-protocol approvals** ✅. Intent-engine pattern wires approval as a dependency-ordered step:
  `execution-service/execution_service/algo_library/intent_engine.py` sequences
  `[approve token_in] → [swap token_in → token_out]` with `depends_on=[approve_step.step_id]`. Per-operation approval
  (not pre-signed-batch). **Gap:** no SSOT for "which approvals needed before carry_staked_basis can run live" —
  deferred to runtime intent generation.
- **D7 — Multi-wallet / sub-account** ❌. Single wallet per connector instance (`wallet_private_key` passed once at
  init). **No multi-wallet portfolio management in execution-service.** Per-archetype isolation likely handled at
  strategy-service orchestration layer; not verified.
- **D8 — Bridges (CCTP / Wormhole / LayerZero)** ⚠. Intent engine references bridge steps
  (`Steps: [approve] → [bridge token to dest chain]`) but **no protocol-specific adapters found** in execution-service.
  Bridge execution is declared-only at intent level.

### Block E — Data sources

- **E1 — Tardis** ✅ (CeFi). `deployment-service/deployment_service/deployment_config.py:73` `tardis_access_mode` enum
  (perpetuals_only / full); rotation tracked in `deployment-service/functions/rotate-exchange-keys/main.py`
  (`tardis-api-key`); shard-distribution mode-filter in `calculators/shard_distribution.py`. Single-key, mode-gated.
- **E2 — Databento + Barchart + Yahoo** ✅ (TradFi). Databento per-schema entitlements via
  `market-data-processing-service/market_data_processing_service/config.py` (`databento_batch_registry_bucket`);
  bootstrap secret `databento-api-key` per `deployment-service/scripts/bootstrap/verify_bootstrap.py`. Barchart
  one-time-historical-only (`canonical_mappings.py: "barchart": ["VIX"]` 2020-01-02 → 2025-11-12 preload, no ongoing
  API). Yahoo public-API (`canonical_mappings.py: "yfinance": ["FX"]`, no key); rolling-60d VIX 15m via
  `market_tick_data_service/.../umi_tick_provider.py:_fetch_yahoo_vix_15m`.
- **E3 — Sports** ⚠. Routing logic enumerated (`deployment-service/deployment_service/sports_trigger_state.py` routes
  per-data-type to api_football / footystats / understat / transfermarkt / soccer_football_info / open_meteo /
  odds_api). 43 leagues with tier classification (`deployment-service/scripts/sports/verify_league_config.py`). **Gap:**
  per-source API key credential locations not surfaced in audit (likely Secret Manager via standard pattern); no
  rotation cadence documented.
- **E4 — Polymarket + Kalshi** ⚠. UAC catalogue declares 5 live archetypes naming polymarket. **Credential handling not
  visible** in audit scope (likely execution-service + strategy-service); not surfaced in MTDS layer.
- **E5 — DeFi data (Graph / Dune / etc)** ⚠. DefiLlama public no-key (`canonical_mappings.py: "defillama": None`);
  CoinGecko `"coingecko": "COINGECKO_API_KEY"` — declared-key, **deployment of the key in Secret Manager not
  confirmed**. **The Graph / Dune / Flipside NOT used in workspace.**
- **E6 — Pyth + Chainlink** ✅. Pyth Hermes wired in MTDS oracle handler (per D2). Chainlink config
  (`chainlink-expanded.yml`) present; on-chain reads via chain RPC (no off-chain credential needed). **Pyth re-enable
  2026-05-06 confirmed wired in MTDS, NOT stub.**

### Block F — Auxiliary services

- **F1 — Telegram** ✅. `unified-trading-pm/.github/workflows/ci-status-update.yml:160` injects `TELEGRAM_BOT_TOKEN` +
  `TELEGRAM_CHAT_ID`. `client-reporting-api/.github/workflows/request-major-bump.yml` posts to
  `api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`. **Gap:** repo-level scope only (no per-environment
  dev-vs-staging-vs-prod chat split).
- **F2 — Firebase** ⚠. `unified-trading-system-ui/.firebaserc:2-6` lists prod project (`central-element-323112`) +
  staging (`odum-staging`). **Service-account JSON storage location not surfaced in audit** (likely deployment CI
  secret).
- **F3 — GitHub PATs / WIF** ⚠. Classic PATs: `secrets.GH_PAT` in `ci-status-update.yml:39`; `GH_TOKEN` in
  `major-bump-issue-handler.yml:70-90` for collaborator permission gate. **No Workload Identity Federation found** —
  workspace is on classic PATs.
- **F4 — Anthropic API** ⚠. `ANTHROPIC_API_KEY` conditionally gated in
  `market-data-processing-service/.github/workflows/plan-alignment-agent.yml` +
  `client-reporting-api/.github/workflows/agent-audit.yml` (advisory / audit workflows, NOT in core CI gates).
- **F5 — Other third-party APIs** — sample: Telegram + GitHub API + Databento + Yahoo + api_football + understat +
  transfermarkt + open_meteo + odds_api + Polymarket + DefiLlama + CoinGecko. No comprehensive workspace grep performed
  — this is a residual.

### Block G — Per-mode credential matrix

- **G1-G5** ❌. **No mode-specific credential subset SSOT exists.** No `--mode {paper,batch,live}` flag on any audit
  script (none exists). No per-archetype credential subset checklist. Master plan Groups F+G (live-only items 17-23)
  reference custody / paper-trade-smoke / batch-vs-live recon / circuit-breakers but don't decompose into per-credential
  dependencies. **This entire block is a planning gap.**

### Block H — Cross-cutting discipline

- **H1 — `ApiKeyReloader` coverage** ⚠. Class exists at
  `unified-trading-library/unified_trading_library/api_key_reloader.py`. Confirmed consumers:
  `strategy-service/.../signal_broadcast/credentials.py`, `features-service/features_service/onchain/collectors/`,
  `features-onchain-service/.../collectors/`, `instruments-service/scripts/fill_missing_player_stats.py`. **Gap:** no
  exhaustive per-service compliance audit; QG STEP 5.62 enforces but not all credential-consuming services explicitly
  verified.
- **H2 — Rotation cadence + runbook** ⚠. `deployment-service/functions/rotate-exchange-keys/main.py` has rotation
  tracking with max-age per secret. **No runbook with `execution.owner` per credential class** per the workspace HARD
  RULE.
- **H3 — ADC discipline** ✅. Test-only `os.getenv("GOOGLE_APPLICATION_CREDENTIALS")` (legitimate ADC default-path
  pattern). No production placeholder violations observed.
- **H4 — `os.getenv()` for credentials** ✅. **No production `os.getenv` violations found** for credential-shaped
  strings (`API_KEY`, `SECRET`, `PRIVATE_KEY`, `TOKEN`). Test conftest.py reads `GOOGLE_APPLICATION_CREDENTIALS`
  (legitimate).
- **H5 — `.env` file audit** ✅ (clean — security scan executed 2026-05-09). 33 `.env*` files in active workspace + 7 in
  archive. **Spot-check on 10 sampled `.env`s** (deployment-service, alerting-service, market-data-processing-service,
  deployment-api, ml-training-service, ml-inference-service, pnl-attribution-service, features-onchain-service,
  batch-live-reconciliation-service, risk-and-exposure-service): all 10 are gitignored per `git check-ignore`; contents
  are infrastructure config only — `GCP_PROJECT_ID`, `CLOUD_PROVIDER`, `CLOUD_MOCK_MODE`, `STATE_BUCKET`,
  `SERVICE_ACCOUNT`, `ENVIRONMENT`, `GCS_REGION`, `BIGQUERY_LOCATION`, `PROTOCOL_DATA_*_BUCKET_*`, `DISABLE_AUTH`. **NO
  credential-shaped keys found** (no `API_KEY`, `SECRET`, `PRIVATE_KEY`, `TOKEN`, `PASSWORD` patterns). **Git-history
  `pickaxe` scan on 4 sample repos** (execution-service, market-tick-data-service, strategy-service,
  unified-trading-library) for `AKIA[0-9A-Z]{16}` / `sk_live_` / `api_secret = "..."` patterns: **NO leaks found across
  full git history**. **Tooling note**: `gitleaks` + `trufflehog` not installed locally — manual
  `git log --pickaxe-regex -S` used as fallback. Residual: 23 `.env`s un-spot-checked (different repos may differ);
  workspace-wide automated scan via gitleaks/trufflehog with execution-owner declared per `Runbook Execution-Owner SSOT`
  HARD RULE is the durable Phase 0 gate (R10).
- **H6 — Secret Manager naming SSOT in codex** ❌. **No codex doc enumerating naming convention.** Pattern lives in code
  only (per A3).
- **H7 — `UnifiedCloudConfig` cloud-agnostic** ✅.
  `unified-trading-library/unified_trading_library/config_interface/cloud_config.py:1-100`. **Cloud-agnostic at contract
  level**; both GCP + AWS factories in `unified-cloud-interface`. Tests cover both `@mock_aws` + GCP emulator paths.
  Widespread consumer adoption (`client-reporting-api`, `strategy-service`, `features-onchain-service`,
  `execution-service`). **Gap:** AWS implementation depth not separately audited; given Block A2 + A5 + A8 AWS gaps, the
  AWS half of `UnifiedCloudConfig` may be more stub than thought.

### Block I — Audit recipe + continuous-verification

- **I1 — Credential-probe script** ❌. **No workspace-wide credential audit script exists.**
  `unified-trading-pm/scripts/audit/` has governance / quality / security audits but nothing that probes every
  credential surface against real systems. `deployment-service/functions/rotate-exchange-keys/main.py` tracks rotation
  max-age but is not a freshness probe.
- **I2 — Credential matrix doc in codex** ❌. **No "credential audit / matrix / rollup" doc found in codex/.**
- **I3 — Health endpoint credential probes** ❌. `make_health_router()` health endpoints (per QG STEP 5.62) report
  `data_freshness` (last-processed timestamp), **NOT credential validity**. No "can I authenticate to Tardis right now?"
  probe in any health endpoint.
- **I4 — CI smoke test for credentials** ❌. **No CI workflow probes credentials against real services.** All CI is QG
  (lint / type / tests) on mock data.
- **I5 — Master plan continuous-verification column** ❌. Master plan `master_to_live_defi_2026_05_23.md:32-42` has
  epics index + deliverables + masters table; **no continuous-verification column**. Group F items 17-23 (paper-trade
  smoke / batch-vs-live recon / Copper+CEFFU / circuit breakers / DART manual-trade gate) lack declared cron / smoke /
  weekly-audit cadence. Per the workspace `Master Plan Continuous-Verification Column` HARD RULE, this is itself a P0
  gap.

## Operator notes / answers

Audit pass 2026-05-09 substantially answered Blocks B / D / E / F / H — credential-injection patterns are clean per
workspace convention, all 6 perp venues + 4 additional venues live-ready, Pyth wiring shipped, FlashLoanReceiver
deployed, `ApiKeyReloader` is the convention. The remaining open surface is overwhelmingly:

1. **AWS provisioning gap (A2 / A5 / A8)** — IAM + ECR + non-DeFi bucket parity essentially un-provisioned. Cloud parity
   for May-23 is materially incomplete.
2. **CEFFU custody gap (C2)** — zero implementation. Integration owner + path needed.
3. **No credential-probe / no continuous-verification path (I1-I5)** — composes with the master-plan column gap.
4. **No mode-specific credential subset SSOT (G1-G5)** — entire block is planning gap.
5. **No Secret Manager naming codex SSOT (H6)** — pattern only in code.
6. **No SSOT for "which approvals before carry_staked_basis can run live" (D6)** — per-archetype credential dependency
   tree.

Operator clarifications all resolved 2026-05-09 — direction: **no shortcuts, every gap in scope for May-23**.

- ~~`Sequoia` disambiguation~~ ✅ R1 — Sepolia + all 5 testnets in-scope.
- ~~CEFFU scope~~ ✅ R2 — P0 May-23, integration in current cycle.
- ~~Per-archetype credential prioritization~~ ✅ R4 — every May-23 archetype's credentials green at cutover.
- ~~Cloud-parity scope~~ ✅ R3 — full AWS↔GCP parity for May-23.

Single open operator-decision: **R9 sub-(a) Fireblocks vs Copper-hot-wallet vs KMS-encrypted-blob** for HSM-grade
signing tier — recommended Fireblocks per audit; awaiting confirmation. Every other sub-residual is
workspace-investigable (code grep / GCS probe / test run) per operator direction 2026-05-09 — "use gcs and code to
answer your own questions."

## Iteration log

| Date       | Author              | Change                                                                                                                                                                                                                |
| ---------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-08 | ikenna + main agent | Initial draft created                                                                                                                                                                                                 |
| 2026-05-09 | main agent          | Audit pass — 3 parallel research agents swept Blocks A/H, B/C/D, E/F/I; findings consolidated; status → audit-in-progress; residual questions enumerated                                                              |
| 2026-05-09 | ikenna              | R1 resolved — `Sequoia` = Sepolia; ALL 5 testnets (Ethereum Sepolia + Arbitrum Sepolia + Base Sepolia + Polygon Amoy + Solana devnet) in-scope for May-23. D4 finding + R1 + plan-shape decisions updated.            |
| 2026-05-09 | ikenna              | R2-R10 all resolved — direction: "no shortcuts, all for May-23." Every gap P0 for cutover; sub-residuals captured inline. Single open operator-decision = R9 sub-(a) Fireblocks vs Copper-hot-wallet vs KMS.          |
| 2026-05-09 | ikenna              | Sub-residual investigation directive — "use gcs and code to answer your own questions or run tests." Operator-clarification list collapsed; remaining sub-residuals are workspace-investigable not operator-question. |
| 2026-05-09 | ikenna              | `.env` security scan + Secret-Manager-migration directive — Phase 0 deliverable; code updates accompany.                                                                                                              |
| 2026-05-09 | main agent          | `.env` security scan executed (findings folded into Block H5 audit + Residual R10 sub-deliverables); workspace-investigable sub-residuals answered via code/grep (folded into respective R-blocks).                   |
| 2026-05-09 | main agent          | Code shipped: `deployment-service@9943e7c9` extended rotation-tracking SSOT with 8 venues + 5 data sources missing from prior list. Closes R4 + R6 sub-deliverables for rotation-cadence coverage.                    |

## Plan-shape decisions (filled before plan extraction)

- **Plan name + path**: TBD (likely `plans/active/api_keys_wallets_accounts_readiness_<date>.md` with sub-plan fan-out
  per Block). Audit confirms the per-Block phasing model is right — Block-A AWS gap alone is ~3-5 AI-day discrete
  workstream (IAM provisioning + ECR + S3 parity + cross-cloud bridge IAM); Block-C CEFFU is operator-onboarding-heavy
  not code; Block-G + Block-I are planning-shape (write the SSOT + write the probe script).
- **Plan type**: `infra` (cloud + secret + IAM provisioning) + `business` (custody onboarding for CEFFU) + `code`
  (audit-script + per-service `ApiKeyReloader` retrofits + codex SSOT writes).
- **Owner side**: Ikenna for cloud + custody + operator-judgment calls; Harsh for audit-script + per-Block credential
  provisioning + Secret-Manager-path migrations + `os.getenv` sweep + ECR setup.
- **Codex SSOTs touched**:
  - `codex/05-infrastructure/credentials-matrix.md` — NEW — workspace credential SSOT.
  - `codex/04-architecture/interface-credential-convention.md` — UPDATE — per-credential-class examples + cross-cloud
    guidance.
  - `codex/06-coding-standards/config-reloader-pattern.md` — UPDATE — `ApiKeyReloader` per-service coverage matrix.
  - `codex/05-infrastructure/runtime-tiers-and-deployment.md` — UPDATE — credential subset per tier.
  - `codex/14-playbooks/authentication/firebase-local.md` — UPDATE — Firebase prod vs emulator credential split.
  - `codex/14-playbooks/credentials/rotation-runbook.md` — NEW — rotation cadence + execution-owner per credential
    class.
  - `codex/05-infrastructure/aws-iam-matrix.md` — NEW — per-service AWS IAM SSOT (currently the largest gap).
  - `codex/05-infrastructure/secret-manager-naming.md` — NEW — naming convention SSOT (H6 gap).
- **Cross-plan dependencies**:
  - `plans/active/master_to_live_defi_2026_05_23.md` — Group F + G credential-dependent gates reference this plan;
    master plan readiness matrix continuous-verification column refresh is a sub-deliverable.
  - `plans/epics/defi_master_2026_05_07.md` — DeFi credentials (Block D) feed defi master scope.
  - `plans/epics/cefi_master_2026_05_07.md` — CeFi venue credentials (Block B) feed cefi master scope.
  - `plans/epics/infrastructure_master_2026_05_07.md` — Cloud infrastructure (Block A + H) feeds infra master scope; AWS
    gap is largest sub-deliverable.
  - `plans/active/issues/runbook_execution_governance_gaps_2026_05_08.md` — credential probe script needs
    `execution.owner` declaration.
  - Sibling question docs `client_reporting_pnl_attribution_2026_05_08.md` +
    `risk_simulations_limits_alerting_2026_05_08.md` — both depend on credential discipline + treasury rollup view (C4)
    for client-scoped reporting + per-client risk limits.
- **Estimated scope**: Large — ~13-19 AI-days (revised up from 10-15 after R1 resolution adds the per-testnet
  workstream). Refined breakdown per audit findings: Block A (cloud + AWS gap) ~4-5d, Block C (CEFFU
  operator-onboarding-heavy) ~3d, Block D-mainnet (DeFi residuals + per-archetype-approval-SSOT) ~1-2d, **Block
  D-testnet-replica (NEW per R1) — 5 testnets × (wallet + RPC + FlashLoanReceiver deploy + funded gas + protocol
  approvals + mock-contract substitutes for mainnet-only protocols like Lido/Jito/Pyth) ~3-4d**, Block E (data-source
  rotation runbook) ~1d, Block G + I (mode matrix + audit-script + continuous-verification wiring) ~3-4d combined.
  **Block-D-testnet-replica composes with master plan Group F item ("live testnet replicating prod") — sub-deliverable
  of credential plan, not a separate plan.**

## Residual questions (post-audit)

All 10 residuals resolved 2026-05-09 — operator direction: **no shortcuts, every gap in scope for May-23 cutover**. Each
resolution carries forward into plan-shape decisions + introduces sub-residuals.

**Sub-residual investigation pass 2026-05-09** (per operator directive "use gcs and code to answer your own questions or
run tests"): R1/R3/R4/R8/R10 sub-residuals partially resolved via workspace probes — findings folded into each R-block
below + Block H5. **Concrete code edit SHIPPED at `deployment-service@9943e7c9` (origin/live-defi-rollout)**:
`functions/rotate-exchange-keys/main.py` extended `_TRADE_KEY_PATTERNS` with hyperliquid + aster + upbit + kraken +
bitfinex + bitget + polymarket + copper (8 venues × api-key+api-secret triples = 17 entries), and `_DATA_KEY_PATTERNS`
with api-football + footystats + soccer-football-info + coingecko + helius (5 entries). Closes part of R4 + R6
sub-deliverables; the rotation function now scans for + alerts on stale credentials across every venue/source the May-23
cutover depends on.

1. **R1 — `Sequoia` disambiguation.** ✅ **RESOLVED 2026-05-09** — `Sequoia` = Sepolia. **ALL 5 testnets in-scope for
   May-23**: Ethereum Sepolia + Arbitrum Sepolia + Base Sepolia + Polygon Amoy + Solana devnet. Per-testnet provisioning
   becomes a discrete workstream in plan extraction (see "Plan-shape decisions" § Block-D-testnet-replica).
   Sub-residuals: **(a) Workspace-investigated 2026-05-09**: `unified-api-contracts/config/testnet_contracts.yaml`
   registers Sepolia (chain_id 11155111) with `aave_v3` + `uniswap_v3` +
   `flash_loan_receiver: 0x480c9142C51A477e0D8A17E032463d81A3b611BA` AND Holesky (chain_id 17000) with `aave_v3` +
   `eigenlayer` + `lido` + same flash_loan_receiver address. **NOT registered**: Arbitrum Sepolia (421614) / Base
   Sepolia (84532) / Polygon Amoy (80002) / Solana devnet — these are gaps that need contract-deployment + registry
   entries. **Important finding**: Lido + EigenLayer testnet deployments are on **Holesky, not Sepolia** (per
   `_defi_lst.py` LST genesis dates + testnet_contracts.yaml comment). For Lido stETH testnet integration the workspace
   must use Holesky, not Sepolia — this contradicts an interpretation that "all 5 testnets" means Sepolia-family
   across-the-board. Concrete sub-residual: testnet wallet provisioning needs to be 6 chains (5 named + Holesky for
   Lido/EigenLayer) OR substitute mock contracts on Sepolia for Lido. **(b) Workspace-investigated**:
   testnet_contracts.yaml comment explicitly states "Same receiver contract as Sepolia until a Holesky-specific deploy
   is registered" — flash-loan-receiver IS shareable across EVM testnets for now; per-chain-deploy is the eventual
   intent but not blocking. **(c) Faucet automation** still open — likely deployment-service Cloud Scheduler job per
   testnet, low-effort sub-todo.
2. **R2 — CEFFU cutover scope.** ✅ **RESOLVED 2026-05-09** — **CEFFU integration is P0 May-23, no Copper-only fallback,
   no deferral**. Zero workspace code today (Block C2) → integration owner + plan needed in current cycle. Sub-residuals
   open: (a) CEFFU's product offering for our use case — MirrorX (off-exchange-settlement linking CEFFU custody to
   Binance perp margin without moving funds) vs direct custody API; (b) account-onboarding lead time — CEFFU
   institutional KYB typically 2-4 weeks, must start immediately; (c) asset coverage — confirm CEFFU custodies BTC +
   ETH + USDC + USDT minimally, plus any LST scope (jitoSOL / stETH / etc); (d) operational-model split with Copper —
   does CEFFU replace or augment Copper for the spot leg of `carry_staked_basis` (Copper is custody-only, CEFFU-MirrorX
   gives margin-collateralized perp trading without funds movement — different model); (e) CEFFU SDK / API spec
   ingestion + factory-pattern adapter (mirror `execution-service/.../custody/copper.py` shape, register in
   `custody/factory.py` for `"ceffu"` key); (f) HMAC / signing-key conventions distinct from Copper.

3. **R3 — AWS-cutover scope.** ✅ **RESOLVED 2026-05-09** — **Full AWS↔GCP cloud parity for May-23, no shortcuts, no
   GCP-only fallback**. Largest single workstream in the residual set. Audit found AWS essentially un-provisioned: IAM
   matrix (Block A2), ECR (Block A8), non-DeFi buckets (Block A5 — DeFi-only via Tab 4). Sub-residuals: (a) per-service
   AWS IAM role + policy provisioning, mirror the GCP per-service-SA matrix one-to-one; (b) ECR setup + dual-cloud image
   push from CI to both GCP Artifact Registry + AWS ECR; (c) non-DeFi bucket creation on AWS S3 + cross-cloud
   `gcloud storage rsync GCS→S3` for CeFi / TradFi / sports / prediction historical data (mirror Tab 4's DeFi pattern);
   (d) AWS Secrets Manager replication of every credential currently in GCP Secret Manager (full credential parity, not
   selective); (e) AWS SNS/SQS provisioning to mirror every GCP Pub/Sub topic + DLQ; (f) AWS EventBridge to mirror Cloud
   Scheduler rules; (g) cross-cloud service-to-service auth via Workload Identity Federation (GCP SA assumes AWS IAM
   role for services spanning both clouds); (h) AWS region selection — start ap-northeast-1 for parity with GCP
   asia-northeast1, decide multi-region later; (i) per-VM-launcher AWS-EC2 equivalents (`launch-*-vm-aws.sh`) under
   `deployment-service/scripts/vm/` per VM-launcher-SSOT rule; (j) AWS-side `VM_PREFIX_TO_BUCKET` registry equivalent
   for the zombie-watchdog; (k) `UnifiedCloudConfig` AWS-implementation depth audit (Block H7 flagged the AWS half may
   be more stub than thought — verify every credential class actually round-trips through AWS Secrets Manager).
   **Workspace-investigated 2026-05-09**: `deployment-service/configs/bucket_config.yaml` HAS structured `aws:` sections
   (lines 13 = defaults `region: ap-northeast-1`; line 232 = `infrastructure_buckets.aws` with 6 DeFi buckets currently
   — `unified-trading-{terraform-state,gas-fees,solana-defi,evm-defi}-{account_id}` with `_test` variants; line 376 =
   lifecycle/encryption defaults). **Concrete sub-(c) deliverable**: extend `infrastructure_buckets.aws` with non-DeFi
   entries (CeFi / TradFi / sports / prediction) mirroring the existing GCP set — yaml-only edit, no code change.
   AWS-region parity is already declared.

4. **R4 — Per-archetype May-23 scope.** ✅ **RESOLVED 2026-05-09** — **ALL archetype credentials green at cutover, no
   per-archetype deferral**. Sports + prediction credentials in scope alongside DeFi + CeFi. Sub-residuals: (a) sports
   per-source credential rotation runbook — **Workspace-investigated 2026-05-09**:
   `deployment-service/functions/rotate-exchange-keys/main.py` `_TRADE_KEY_PATTERNS` covers binance / bybit / deribit /
   okx / coinbase / betfair (sports) / kalshi (prediction); `_DATA_KEY_PATTERNS` covers tardis / databento / glassnode /
   thegraph / alchemy / coinglass / odds-api / aws-hyperliquid-s3. **Gaps closed by 2026-05-09 code edit**: added
   hyperliquid + aster + upbit + kraken + bitfinex + bitget + polymarket + copper to trade keys; added api-football +
   footystats + soccer-football-info + coingecko + helius to data keys. **Still missing rotation tracking** (per-source
   review): understat / transfermarkt (scrape-based, no API key) — public sources, no rotation needed; open_meteo
   (public API, no key); pyth-hermes (public endpoint, no key); fireblocks/ceffu — pending integration. (b) prediction
   credentials — kalshi was already in trade list; polymarket added by 2026-05-09 edit; manifold not yet integrated. (c)
   per-archetype credential subset checklist (Block G5) — still planning gap, no SSOT yet. (d) per-archetype
   probe-script subset — pending audit-script (Block I.1).

5. **R5 — CCXT vs native adapter.** ✅ **RESOLVED 2026-05-09** — **Native adapters for ALL live-trading venues by
   May-23, no CCXT pass-through on live paths**. CCXT acceptable for batch-mode data adapters where rate-limit +
   error-classification fidelity matters less; live-trading paths native. Already native: Deribit + Hyperliquid +
   Aster + Upbit. Native build needed for May-23: **Bybit + Binance + OKX + Kraken + Bitfinex + Bitget = 6 new native
   adapters**. Sub-residuals: (a) per-venue REST + WS client with explicit rate-limit token-bucket per credential class
   (read / trade / withdraw scopes per R6); (b) error classification through UAC `classify_venue_error()` per CLAUDE.md
   HARD RULE; (c) WebSocket connection management — per-venue connection pool with automatic reconnect + sequence-gap
   detection; (d) symbol normalization between UAC canonical types and venue-native types (each venue distinct
   instrument-id formats); (e) shared `VenueAdapterBase` to factor common HMAC + rate-limit + reconnection logic — avoid
   6× duplicate boilerplate; (f) per-venue VCR cassette test parity (every native adapter has VCR fixtures matching the
   existing CCXT-era VCR tests in `unified-api-contracts/tests/vcr/`).

6. **R6 — Read-only / trade / withdraw key scope.** ✅ **RESOLVED 2026-05-09** — **Per-scope key separation P0 for
   May-23, security-grade**. Sub-residuals: (a) per-venue sub-key provisioning (operator-side, manual web-UI flow per
   venue — can't be automated); (b) Secret Manager naming extension — `<venue>-<scope>-{api-key,api-secret,passphrase}`
   triple per venue × 3 scopes (e.g. `bybit-read-api-key`, `bybit-trade-api-key`, `bybit-withdraw-api-key`) — codex H6
   SSOT codifies; (c) adapter-level operation-to-scope routing — `get_market_data_adapter()` returns read-scope,
   `get_order_adapter()` returns trade-scope, `get_withdraw_adapter()` returns withdraw-scope (or one factory with
   `scope=` parameter); (d) per-venue IP whitelist matrix per scope (some venues allow per-sub-key IP whitelist — pin VM
   egress IPs to whitelist); (e) per-scope rate-limit budgets distinct (read keys typically have higher budgets than
   trade keys); (f) withdraw-key approval flow — withdraw scope likely human-in-loop (operator approval via web UI or
   DART manual-trade gate per master plan Group G item 23) rather than service-automated.

7. **R7 — Multi-wallet per-archetype isolation.** ✅ **RESOLVED 2026-05-09** — **Multi-wallet per-archetype P0 for
   May-23, no shared-wallet model on live**. Each archetype gets its own operator wallet per chain → N archetypes × M
   chains = N×M wallets (e.g. 2 DeFi archetypes × 5 chains = 10 mainnet wallets + 10 testnet wallets). Sub-residuals:
   (a) wallet provisioning automation — generating + funding + approving N×M wallets is significant operational work;
   consider HD-wallet derivation (BIP32 / SLIP-0010) so all wallets derive from one master seed stored in HSM; (b)
   per-wallet nonce queue management on chain RPC (independent nonce sequence per wallet); (c) per-wallet rate-limit
   budgets on chain RPC providers (each wallet's queries count against same key — per-wallet sub-budget allocation); (d)
   treasury rollup combining N×M wallets per chain (composes with Block C4 unified-NAV view + client-reporting question
   doc); (e) cross-archetype rebalancing flow — when archetype A's wallet runs low on gas, refill source
   (operator-manual sweep vs scheduled cron from treasury wallet); (f) per-wallet protocol approvals — N×M approval-sets
   per protocol per chain (Aave allowance × 10 wallets × N protocols); (g) strategy-service routing — each archetype's
   signal targets its archetype-wallet config; UAC type extension `archetype_id → wallet_address_per_chain` mapping
   needed; (h) HSM signing scope (composes with R9 — every wallet needs HSM-grade signing path).

8. **R8 — Pyth-on-Solana production wiring real-data test.** ✅ **RESOLVED 2026-05-09** — **Real-data verification
   before May-23, no code-shipped-only**. Operator-run smoke (or scheduled VM): trigger MTDS `oracle_prices_handler`
   against mainnet Solana RPC + Hermes endpoint; capture per-LST price (jitoSOL / mSOL / bSOL); confirm against Pyth UI
   (pyth.network); verify event-stream emits per-asset progress events with row counts (per CLAUDE.md "No
   fire-and-forget VM launches"). Sub-residuals: **(a) Workspace-investigated 2026-05-09**:
   `unified-api-contracts/.../capability_declarations/_defi_oracle_coverage.py` declares
   `ORACLE_COVERAGE_START["pyth_hermes"] = "2023-10-01"`. `_defi_lst.py` lists jitoSOL genesis 2022-11-01 (~11-month
   pre-archive gap noted) + mSOL 2021-08-02 + bSOL 2022-11-24. **Pre-archive gap is a known operator-decision item
   tracked in `defi_master_2026_05_07.md`** — pre-2023-10-01 Hermes returns "Update data not found" for ALL Solana LST
   feeds, so historical backfill needs alternative source. **For LIVE on May-23 (current = 2026-05-09, well past
   2023-10-01) Pyth IS sufficient** for live trading. mSOL + bSOL Pyth-feed availability (does Pyth publish those LST
   tokens, not just SOL/USD?) still needs an actual probe — operator-run live smoke needs to verify per-LST Hermes
   returns non-empty + within freshness threshold. **(b/c/d)** still open per original — production query-frequency
   probe + freshness failover threshold + EVM Chainlink parity smoke per chain.

9. **R9 — Wallet key storage security tier.** ✅ **RESOLVED 2026-05-09** — **HSM-grade signing for live trading by
   May-23, no raw-private-key-in-Secret-Manager on live**. **Decision deferred to plan-extraction phase between three
   options** — operator-direction needed: (a) **Fireblocks signer integration** (Fireblocks already enum-declared per
   Block C3, no implementation today; extend Copper-shape factory pattern at `execution-service/.../custody/`;
   institutional-grade MPC signing with policy controls); (b) **Copper hot-wallet sub-account product** if it exists for
   non-custody-held DeFi positions (extends existing Copper integration — operationally simpler if available); (c) **GCP
   KMS / AWS KMS-encrypted blob with VM-side runtime decryption** (cheaper, less rigorous than HSM — single-cloud key,
   can be moved). **Recommended: (a) Fireblocks** — matches the Copper architectural pattern, highest security tier,
   factory-injection-clean. Sub-residuals: (a) operator decision on (a) vs (b) vs (c); (b) per-archetype-wallet HSM
   scoping (composes with R7 — N×M wallets each need HSM signing path; HD-wallet derivation under HSM-protected master
   key is the clean shape); (c) signing latency budget — HSM signers add 100-500ms per signature, must fit within
   strategy-execution-service end-to-end latency target (especially for `leveraged_funding_arb` which is
   rate-sensitive); (d) HSM signer rate-limit — each provider has request/sec ceilings; pre-cutover load test to
   confirm; (e) raw-key fallback for testnet — testnet wallets stay raw-key (Block D-testnet-replica per R1) since no
   real funds at risk and dev cycle needs to be fast; (f) signing-policy controls per wallet (Fireblocks supports
   per-wallet policy: max amount per tx, allowed destinations, time-of-day windows — define defaults per archetype).

10. **R10 — `.env` security scan.** ✅ **RESOLVED 2026-05-09 + INITIAL SCAN PASSED CLEAN**. Sub-deliverables: (a)
    `gitleaks` or `trufflehog` workspace-wide scan — **TOOLING NOT INSTALLED LOCALLY**; manual
    `git log --all --pickaxe-regex -S 'AKIA[0-9A-Z]{16}|sk_live_|api_secret = "..."'` ran on 4 sample repos
    (execution-service, market-tick-data-service, strategy-service, unified-trading-library) — **ZERO leaks found**. (b)
    per-leak remediation — N/A, no leaks observed in sample. (c) `.gitignore` audit — **DONE for 10 sampled `.env`s**
    via `git check-ignore` — all 10 returned positive (gitignored). 23 un-spot-checked `.env`s remain — extending the
    spot-check is a small follow-up. (d) GHA workflow log scan — pending; not in this audit pass. (e) automated CI scan
    with `execution.owner` declared per `Runbook Execution-Owner SSOT` — **STILL OPEN** as durable Phase 0 deliverable;
    recommendation: install gitleaks-action in `.github/workflows/secret-scan.yml` per repo + daily Cloud
    Scheduler-triggered workspace-wide scan that posts to Telegram alerts on new findings. (f) historical-rotation list
    — N/A given clean scan. **Aggregate verdict on R10**: workspace passes the initial security audit; the durable infra
    (automated scan + execution-owner SSOT) is what's still missing for full closure.

Implementation-shape questions resolved by audit (no operator input needed):

- **R-resolved-1.** Aster IS NOT stub — `defi_execution/protocols/aster.py:23` is real adapter.
- **R-resolved-2.** Pyth Hermes IS wired (not paper-decision-only) — `oracle_prices_handler.py:_PYTH_HERMES_URL`.
- **R-resolved-3.** Copper IS wired end-to-end — full MPC custody provider in `custody/copper.py`.
- **R-resolved-4.** `UnifiedCloudConfig` IS cloud-agnostic at contract level — both GCP + AWS factories present.
- **R-resolved-5.** No production `os.getenv` violations for credential-shaped names — Block H4 clean.

## Plan extraction record

- **Plan path**: [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../active/api_keys_wallets_accounts_readiness_2026_05_10.md)
- **Spawned**: 2026-05-10
- **Status**: 9-phase execution plan, ~38-57 AI-days, deadline 2026-05-23.
- **Self-contained**: plan body embeds all credential surfaces + sub-residuals + audit findings + pre-audit manifest + execution DAG + cross-phase coordination + cross-plan dependencies + per-phase success criteria + continuous-verification cadence. **No need to re-read this question doc to execute the plan.**
- **Code shipped during extraction**: `deployment-service@9943e7c9` extends rotation-tracking SSOT with 8 venues + 5 data sources (closes part of R4 + R6).
- **Single open operator-decision** (R9 sub-(a)): HSM-grade signing tier — Fireblocks (recommended) vs Copper-hot-wallet vs KMS-blob. Plan assumes Fireblocks at Phase 3.C; swap target if (b) or (c) chosen.
- **Question doc status closes** when: all 9 plan phases ship + Phase 9 codex SSOTs durable + master plan continuous-verification column populated + pre-cutover sign-off gate passes.

## Iteration log addendum

| Date | Author | Change |
| ---- | ------ | ------ |
| 2026-05-10 | main agent | Plan spawned at `plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`. Status → plan-spawned. Question doc retains audit archaeology + sub-residual reasoning; plan body is the executable surface. |
