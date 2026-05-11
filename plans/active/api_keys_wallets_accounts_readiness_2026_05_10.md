---
title: API keys + wallets + accounts readiness — full credential provisioning for May-23 live-DeFi cutover
type: workstream-plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: scope-bounded
spawned_from: plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md
companion_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/defi_master_2026_05_07.md
  - plans/epics/cefi_master_2026_05_07.md
  - plans/epics/infrastructure_master_2026_05_07.md
locked_by: live-defi-rollout
locked_since: 2026-05-10
estimate_class: design
estimate_baseline_ai_days: 107.5
estimate_calibrated_ai_days: 64.5
estimate_calibration_note: |
  Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~50-70, ~38-57). Class inferred from filename (design, multiplier 0.6×).
  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be double-counted. Owner agent: verify baseline, refine class per codex/08-workflows/estimation-calibration.md, recompute calibrated if either changes.
---

# API keys + wallets + accounts readiness — May-23 cutover plan

## Why this plan exists

Credentials are the silent prerequisite to every "real-infra completion, not smoke-test green" HARD RULE in the
workspace. The 2026-05-08/09 audit confirmed that while individual credential surfaces work in code (Copper MPC custody
wired, all 6 perp venues have adapters, `UnifiedCloudConfig` is cloud-agnostic, `ApiKeyReloader` is the convention, no
`os.getenv` violations, no `.env` leaks in spot-check), the **workspace lacks the canonical surface** required for
May-23: no AWS IAM matrix, no per-mode credential subset SSOT, no continuous credential-probe script, no CEFFU
implementation despite master plan Group F item 19, no per-archetype wallet isolation, no HSM-grade wallet signing, no
per-scope key separation. Operator direction 2026-05-09 (R1-R10 resolutions): **no shortcuts, every gap in scope for
May-23**.

This plan operationalizes that direction. It is **self-contained for execution** — no need to re-read the source
question doc. Every phase has full-execution criteria with verifiable bullets per "Plans Run To Actual Completion."

## Scope summary (audit-confirmed AS-IS state)

**Already wired (no work needed beyond verification):**

- 6 perp venues (Bybit, Deribit, Binance, OKX, Hyperliquid, Aster) + 4 additional (Upbit, Kraken, Bitfinex, Bitget)
  adapters exist with factory-injection per `interface-credential-convention.md`.
- Copper MPC custody wired at
  [execution-service/.../custody/copper.py](execution-service/execution_service/custody/copper.py).
- `CHAIN_RPC_TEMPLATES` SSOT in
  [unified-api-contracts/.../capability_declarations/\_defi.py](unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py).
- Pyth Hermes endpoint wired in MTDS
  [oracle_prices_handler.py](market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py)
  (`_PYTH_HERMES_URL = "https://hermes.pyth.network/v2/updates/price/latest"`).
- `FlashLoanReceiver.sol` deployed; address `0x480c9142C51A477e0D8A17E032463d81A3b611BA` registered for Sepolia +
  Holesky in [unified-api-contracts/config/testnet_contracts.yaml](unified-api-contracts/config/testnet_contracts.yaml).
- Tenderly fork fixtures at
  [execution-service/tests/integration/conftest.py](execution-service/tests/integration/conftest.py).
- `bucket_config.yaml` has structured `aws:` sections (line 232) with
  `unified-trading-{terraform-state,gas-fees,solana-defi,evm-defi}-{account_id}` DeFi entries; AWS region
  `ap-northeast-1` declared.
- Rotation tracking SSOT: `deployment-service/functions/rotate-exchange-keys/main.py`. Extended 2026-05-09 (commit
  `9943e7c9`) with hyperliquid + aster + upbit + kraken + bitfinex + bitget + polymarket + copper trade keys +
  api-football + footystats + soccer-football-info + coingecko + helius data keys.
- `.env` security scan clean: 10 spot-checked `.env`s gitignored + infra-config only; git pickaxe scan on 4 sample repos
  found zero `AKIA[0-9A-Z]{16}` / `sk_live_` / hardcoded `api_secret` patterns.

**Confirmed gaps (this plan's scope):**

1. **CEFFU custody** — zero workspace code despite master plan Group F item 19 ("Copper + CEFFU treasury wired").
2. **AWS↔GCP cloud parity** — IAM matrix essentially un-provisioned, ECR not configured, non-DeFi buckets not on AWS,
   AWS Secrets Manager not replicating GCP Secret Manager, AWS SNS/SQS not mirroring Pub/Sub, AWS EventBridge not
   mirroring Cloud Scheduler.
3. **Native venue adapters for 6 venues** (Bybit, Binance, OKX, Kraken, Bitfinex, Bitget) — currently CCXT pass-through;
   no shortcuts means native for live paths.
4. **Per-scope key separation** (read / trade / withdraw) — adapters use single key per venue today.
5. **Multi-wallet per-archetype isolation** — single wallet per connector instance today;
   `N archetypes × M chains = N×M wallets` for live.
6. **HSM-grade wallet signing** — raw-private-key-in-Secret-Manager today; Fireblocks signer recommended (R9 sub-(a)
   decision pending operator).
7. **5+1 testnets** — Sepolia + Holesky registered; Arbitrum Sepolia + Base Sepolia + Polygon Amoy + Solana devnet NOT
   registered. Holesky needed for Lido/EigenLayer (not Sepolia per `_defi_lst.py`).
8. **Per-mode + per-archetype credential subset SSOTs** — no `--mode {paper,batch,live}` SSOT, no per-archetype subset
   checklist.
9. **Credential-probe audit script** — no workspace-wide script probes every credential surface against real systems.
10. **Continuous-verification column** in master plan readiness matrix — Group F+G items 17-23 lack declared
    cron/smoke/audit cadence.
11. **Bridge protocol adapters** (CCTP / Wormhole / LayerZero) — declared in intent engine, no adapters wired.
12. **Codex SSOTs missing** — `credentials-matrix.md`, `aws-iam-matrix.md`, `secret-manager-naming.md`,
    `rotation-runbook.md` all need to be written.

## R9 sub-(a) — RESOLVED 2026-05-12 (operator gate closed)

**Cutover path**: **May-23 ships on CLOUD_KMS_ENCRYPTED** (option (c) — HSM-backed CMK envelope encryption);
**June-1 flips per-wallet to COPPER_MPC / FIREBLOCKS_MPC** (options (a) + (b)) once client provides their
Copper + Fireblocks credentials.

Operator rationale (verbatim 2026-05-12): *"client gives us [Copper/Fireblocks] credentials June 1st when we go
live with them — we need best equivalent to test earlier or use our trust wallet but be ready for integration
with them June 1st."*

**Architectural implication**: per-wallet `signing_surface` field on
[`WalletProvisioningConfig`](unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py)
is a closed-set StrEnum supporting BOTH cutover paths from day 1 (no recompile when client creds land):

| Surface | Phase | Detail |
|---|---|---|
| `CLOUD_KMS_ENCRYPTED` | **May-23 cutover default** | Envelope-encrypted private key in Secret Manager; HSM-backed CMK (GCP Cloud HSM / AWS CloudHSM, FIPS 140-2 L3) wraps. Trading-VM SA is the only principal with KMS Decrypter on the CMK. In-memory decrypt at signing time only. |
| `COPPER_MPC` | June-1 flip per-wallet | Client-provided Copper.co credentials. Wired in execution-service `custody/copper.py` since 2026-05-10; flip is config-only. |
| `FIREBLOCKS_MPC` | June-1 flip per-wallet | Client-provided Fireblocks credentials. Requires `custody/fireblocks.py` (NEW per Phase 3.C) + factory registration. |
| `LOCAL_KEY` | Dev / testnet only | Raw key from Secret Manager. Never production. |
| `MOCK` | Test-only | Deterministic SHA256 fake. |

**Per-wallet flippability**: each `WalletProvisioningConfig` row carries its own `signing_surface` so we can run
a HOT_TRADING wallet on CLOUD_KMS while a TREASURY wallet sits on COPPER_MPC, etc. Wallet-level kill-switch
binding (`kill_switch_id` field) gives operator the FINEST-grain freeze beyond per-venue + per-archetype.

**Cloud-KMS safety note** (operator question): GCP Cloud HSM + AWS CloudHSM are FIPS 140-2 Level 3 hardware
modules — strictly safer than raw-key-in-Secret-Manager (current Phase 3.C "today" state) but strictly less
rigorous than MPC (Copper/Fireblocks). Single point of compromise = KMS Decrypter IAM role. Mitigations:
(a) IAM bound to trading-VM SA only, no human principals; (b) per-wallet kill-switch wiring; (c) per-wallet
spending caps via `SpendingCaps` field; (d) `allowed_destinations` withdraw whitelist; (e) audit-log
on every `kms.decrypt` call. Sufficient for ≤7-day live smoke; June-1 hardens to MPC.

**Phase 3.C scope SPLIT** per R9 resolution:

- **Phase 3.C.1 — Cloud-KMS-encrypted wallet provisioning (May-23 path, P0)**: KMS CMK provisioning per
  asset_group + per-wallet envelope-encrypted PK in Secret Manager + execution-service
  `CloudKmsCustodyProvider` (NEW) implementing `CustodyProvider` protocol via in-memory decrypt → web3.py /
  Solana sdk signing. Tests + Sepolia smoke. **Owner: slot 4 (this tab) + Harsh implementation handoff.**
- **Phase 3.C.2 — Fireblocks integration (June-1 path, P0 post-cutover)**: original Phase 3.C content
  unchanged — wired but DEFERRED-AFTER-CUTOVER per client-credential schedule. Operator manual entry to flip
  via deployment-UI Live-Cluster button once client confirms credentials available.

`Phase 3.C.2` stays open in this plan body but tagged `**DEFERRED-AFTER-CUTOVER (2026-06-01)**` —
materialised post-cutover in successor plan `plans/active/fireblocks_copper_client_integration_2026_06_01.md`
(operator-spawned when client creds land).

## Execution DAG

```
Phase 0 (Security + foundation gates) ── parallel within phase
   │
   ├─→ Phase 1 (Cloud provisioning — AWS↔GCP parity) ── parallel A-F
   │       │
   │       └──→ Phase 4 (DeFi mainnet + testnet) requires 1.D (S3 buckets) + 1.E (Secrets Mgr)
   │
   ├─→ Phase 2 (Trading venue credentials) ── parallel within phase
   │       │
   │       └──→ Phase 4 native adapters reuse Phase 2 base class
   │
   ├─→ Phase 3 (Custody — Copper + CEFFU + Fireblocks)
   │       │
   │       ├─ 3.A Copper real-test (verify-only, no code)
   │       ├─ 3.B CEFFU integration (P0, longest lead time)
   │       └─ 3.C Fireblocks HSM (depends on operator R9 decision)
   │
   ├─→ Phase 4 (DeFi mainnet + testnet provisioning)
   ├─→ Phase 5 (Data sources)
   ├─→ Phase 6 (Auxiliary)
   │
   ├─→ Phase 7 (Per-mode + per-archetype subset SSOTs) ── depends on Phases 2-6 enumeration
   ├─→ Phase 8 (Audit recipe + continuous verification) ── depends on Phase 7 SSOT
   │
   └─→ Phase 9 (Codex SSOT updates) ── runs at every phase boundary, final consolidation
```

Phases 1-6 run parallel (each spawns its own sub-agents); Phase 7 depends on Phases 2-6 having enumerated the universe;
Phase 8 depends on Phase 7 SSOT; Phase 9 codex audit per CLAUDE.md HARD RULE runs at every phase boundary.

Total estimate: **~50-70 AI-days** at 5-10 parallel agents per phase across 13 days (2026-05-10 → 2026-05-23 = 13 days).

---

## Phase 0 — Security + foundation gates (Day 1-2; parallel)

Pre-requisite for all subsequent phases. Catches workspace-wide leaks before we provision new credentials on top of
contaminated state.

- [ ] [SCRIPT] P0. **0.A — `gitleaks` workspace-wide scan + git-history scan.** Install `gitleaks` via Homebrew; run
      `gitleaks detect --source <workspace-root> --report-path /tmp/gitleaks-report.json --redact`. Run
      `gitleaks protect --staged` as pre-commit hook in every repo. **Full-execution criterion**: report on disk + zero
      un-remediated findings + per-leak rotation log if any found. Audit pass 2026-05-09 spot-check found zero in 4
      sample repos but full workspace scan still pending.
  - **What runs**:
    `gitleaks detect --source /Users/ikennaigboaka/Code/unified-trading-system-repos --no-git --report-path /tmp/gitleaks-redacted.json --redact` +
    same with `--all-secrets-types` flag.
  - **Verification**:
    `jq '.[] | select(.RuleID | test("aws-access-token|stripe-access-token|generic-api-key|private-key"))' /tmp/gitleaks-redacted.json`
    returns empty OR every match has remediation evidence.

- [ ] [SCRIPT] P0. **0.B — `.gitignore` exhaustive audit.** Extend the 10-file spot-check to all 33 active `.env*`
      files. For each, run `git -C <repo> check-ignore .env`; collect violators. Per `.env` violator, either add to
      `.gitignore` and `git rm --cached .env` (preserve on disk, remove from index) OR confirm it's a `.env.example`
      template (gitignore exemption is fine).
  - **Verification**: workspace-wide
    `find . -name ".env" | xargs -I {} dirname {} | xargs -I {} git -C {} check-ignore .env` returns "YES" for every
    entry.

- [ ] [SCRIPT] P1. **0.C — GHA workflow log scan.** Run `gh run list --limit 200 --workflow quality-gates.yml` per repo;
      sample 20 logs via `gh run view <run-id> --log` and grep for credential-shaped strings (`api_key=[a-zA-Z0-9]{20,}`
      / `password=[^*]` / `token=[a-zA-Z0-9]{30,}`). If any leak found, rotate immediately + redact log via GitHub
      support.

- [ ] [AGENT] P0. **0.D — Codex SSOT stubs (NEW docs, full content shipped at end of Phase 9).** Stub per
      `Post-Plan-Phase Codex Audit` HARD RULE. Each stub has TL;DR + key principles + cross-references back to this
      plan + placeholder section headers for Phase 9 fill-in:
  - [ ] `codex/05-infrastructure/credentials-matrix.md` (NEW) — workspace credential SSOT.
  - [ ] `codex/05-infrastructure/aws-iam-matrix.md` (NEW) — per-service AWS IAM.
  - [ ] `codex/05-infrastructure/secret-manager-naming.md` (NEW) — naming convention.
  - [ ] `codex/14-customer-journeys/credentials/rotation-runbook.md` (NEW) — rotation cadence + execution-owner.
  - [ ] `codex/05-infrastructure/per-archetype-wallet-isolation.md` (NEW) — multi-wallet model.
  - [ ] `codex/05-infrastructure/hsm-wallet-signing.md` (NEW) — HSM tier discipline.

**Phase 0 done definition** (full-execution criterion):

- ✅ gitleaks report on disk, zero un-remediated findings.
- ✅ All 33 `.env*` files confirmed gitignored.
- ✅ GHA workflow logs grep-clean of credential patterns.
- ✅ 6 codex SSOT stubs committed.

---

## Phase 1 — Cloud provisioning (AWS↔GCP parity) — Day 2-7; parallel A-F

Largest workstream per audit (R3). Provisions AWS to GCP-parity for May-23 cutover.

- [ ] [SCRIPT] P0. **1.A — GCP per-service SA matrix doc.** Enumerate every service's Cloud Run / GCE VM service-account
      email + IAM role bindings. Format: yaml SSOT at `deployment-service/configs/gcp_service_accounts.yaml`. Audit
      current bindings via `gcloud iam service-accounts list --project=central-element-323112` +
      `gcloud projects get-iam-policy central-element-323112`. Cross-reference against
      [bucket_config.yaml](deployment-service/configs/bucket_config.yaml) `service_categories` matrix.
  - **Verification**: every service in workspace-manifest has an entry; `gcloud projects get-iam-policy` matches the
    yaml SSOT 1:1.

- [ ] [SCRIPT] P0. **1.B — AWS IAM matrix provisioning.** **Largest sub-deliverable.** Mirror GCP per-service-SA matrix
      to AWS IAM roles. Per service: create IAM role + attached policies (`s3:GetObject`/`PutObject` per bucket,
      `secretsmanager:GetSecretValue`, `events:PutRule`, `lambda:InvokeFunction`, `ecs:RunTask`, `ec2:RunInstances`).
      YAML SSOT at `deployment-service/configs/aws_iam_roles.yaml`. Provision via Terraform OR CDK (workspace pattern
      TBD; see `deployment-service/buildspec.aws.yaml` for hints).
  - **Verification**:
    `aws iam list-roles --query 'Roles[?starts_with(RoleName, \`uts-\`)].RoleName'`lists every service's role;`aws iam
    list-attached-role-policies --role-name <role>` matches the yaml.

- [ ] [SCRIPT] P0. **1.C — ECR setup + dual-cloud image push.** Create ECR repository per service in `ap-northeast-1`.
      Update `cloudbuild.yaml` + `buildspec.aws.yaml` to push the same image to both
      `asia-northeast1-docker.pkg.dev/${PROJECT_ID}/...:latest` AND
      `427895769566.dkr.ecr.ap-northeast-1.amazonaws.com/...:latest`.
  - **Verification**: `aws ecr describe-repositories --region ap-northeast-1 | jq '.repositories | length'` matches GCP
    Artifact Registry repository count; `docker pull` succeeds from both endpoints with the same digest.

- [ ] [SCRIPT] P0. **1.D — AWS S3 non-DeFi bucket parity.** Extend `deployment-service/configs/bucket_config.yaml`
      `infrastructure_buckets.aws` (currently DeFi-only at line 232) with CeFi / TradFi / sports / prediction entries
      mirroring the GCP set. Apply via `setup-buckets.py` (whatever name the existing script has). Run cross-cloud
      `gcloud storage rsync gs://<bucket> s3://<bucket>` for each historical-data bucket per Tab 4 2026-05-08 DeFi
      pattern.
  - **Verification**:
    `aws s3 ls --region ap-northeast-1 | grep -E "unified-trading-(market-data|sports|prediction|tradfi)"` returns
    expected bucket count; sample-read returns expected rows.

- [ ] [SCRIPT] P0. **1.E — AWS Secrets Manager replication.** For every secret in GCP Secret Manager, create an AWS
      Secrets Manager equivalent in `ap-northeast-1`. Naming convention codified in
      `codex/05-infrastructure/secret-manager-naming.md` (Phase 0.D stub). Cross-cloud SDK abstraction in
      `UnifiedCloudConfig` already cloud-agnostic (Block H7 audit ✅) — verify every credential class actually
      round-trips through AWS Secrets Manager (Block H7 caveat: AWS half may be more stub than thought).
  - **Verification**: every credential listed in Phase 9.A `credentials-matrix.md` exists in BOTH GCP Secret Manager AND
    AWS Secrets Manager; `UnifiedCloudConfig(provider="aws").get_secret(<name>)` returns expected value.

- [ ] [SCRIPT] P1. **1.F — AWS SNS/SQS + EventBridge mirroring.** Create AWS SNS topic + SQS subscription + DLQ per GCP
      Pub/Sub topic. Create AWS EventBridge rule per Cloud Scheduler job. Cross-cloud event routing not in scope for
      May-23 — mirror is sufficient.
  - **Verification**: `aws sns list-topics` count matches `gcloud pubsub topics list` count; `aws events list-rules`
    matches `gcloud scheduler jobs list`.

- [ ] [AGENT] P1. **1.G — Per-VM-launcher AWS-EC2 equivalents.** Per VM-launcher-SSOT rule, every
      `gcloud compute instances create` script under `deployment-service/scripts/vm/launch-*-vm.sh` needs an AWS twin
      `launch-*-vm-aws.sh` using `aws ec2 run-instances`. Add AWS-side `VM_PREFIX_TO_BUCKET` registry equivalent in
      `deployment-service/scripts/vm/vm_zombie_watchdog_aws.py`.

- [ ] [AGENT] P1. **1.H — Cross-cloud Workload Identity Federation.** GCP SA assumes AWS IAM role for services spanning
      both clouds (per `aws-iam-matrix.md`). Configure trust policy on AWS roles + WIF pool on GCP project.

**Phase 1 done definition** (full-execution criterion):

- ✅ AWS IAM matrix populated + applied — `aws iam list-roles | grep uts-` matches yaml.
- ✅ ECR repositories created + dual-cloud image push verified.
- ✅ AWS S3 non-DeFi buckets created + cross-cloud rsync complete.
- ✅ AWS Secrets Manager has every GCP-side credential mirrored.
- ✅ `UnifiedCloudConfig(provider="aws")` round-trips every credential.

---

## Phase 2 — Trading venue credentials — Day 2-9; parallel within phase

Audit confirmed all 6 perp + 4 additional venue adapters exist. This phase adds: native adapters for 6 venues, per-scope
key separation, account-level limits SSOT, per-venue rate-limit budgets.

- [ ] [HUMAN] P0. **2.A — Per-venue sub-key provisioning.** Operator-side, manual web-UI flow per venue. For each of the
      10 venues (Bybit, Deribit, Binance, OKX, Hyperliquid, Aster, Upbit, Kraken, Bitfinex, Bitget): create separate
      read-only / trade / withdraw sub-keys. Pin VM egress IPs to whitelist per scope where venue supports it. Provision
      into Secret Manager paths defined by Phase 0.D `secret-manager-naming.md`:
      `<venue>-<scope>-{api-key,api-secret,passphrase}`.

- [ ] [AGENT] P0. **2.B — Native adapter build for 6 venues.** Replace CCXT pass-through with native REST + WS clients
      for: Bybit, Binance, OKX, Kraken, Bitfinex, Bitget. Pattern: factor common HMAC + rate-limit + reconnection logic
      into `execution-service/.../venues/_base.py` `VenueAdapterBase`. Each native adapter subclass implements per-venue
      request signing + response parsing. Already-native venues (Deribit, Hyperliquid, Aster, Upbit) refactor to use the
      same base class. Cassette VCR test parity via `unified-api-contracts/tests/vcr/`.
  - **Verification**: every native adapter has `test_<venue>_native_vcr.py` that round-trips a sample order placement +
    market-data fetch against recorded cassettes; `bash scripts/quality-gates.sh` clean per repo.

- [ ] [AGENT] P0. **2.C — Per-scope key separation in adapters.** Update `get_order_adapter()` factory to take
      `scope=Literal["read", "trade", "withdraw"]` parameter; route to the right Secret Manager path. Add helper
      factories `get_market_data_adapter()` (read-scope) + `get_withdraw_adapter()` (withdraw-scope). Withdraw scope
      MUST require human-in-loop approval (operator UI or DART manual-trade gate per master plan Group G item 23).
  - **Verification**: unit test confirms `get_order_adapter("bybit", scope="read")` raises `OrderError` if asked to
    place an order; per-scope rate-limit budgets distinct.

- [ ] [AGENT] P0. **2.D — Account-level limits SSOT.** YAML at `unified-api-contracts/config/venue_account_limits.yaml`.
      Per venue: max-order-size per instrument, max-leverage per account-tier, fee tier, market-maker designation.
      Source: operator probe via venue web UI + venue REST API (`/account/info`-style endpoints). Pre-flight risk checks
      (sibling risk question doc) consume this SSOT.

- [ ] [AGENT] P0. **2.E — Per-venue rate-limit token bucket.** Implement per-key + per-account leaky-bucket in
      `VenueAdapterBase` per Phase 2.B. Singleton-locked launcher pattern (per CLAUDE.md `launch-sfi-forward-poll.sh`
      precedent) for any venue where per-key budget is shared across multi-VM concurrency.

**Phase 2 done definition** (full-execution criterion):

- ✅ All 10 venues × 3 scopes provisioned in Secret Manager (operator-side ack); IP whitelists pinned where applicable.
- ✅ 6 native adapters shipped + VCR cassettes recorded; QG green per repo.
- ✅ Per-scope routing test passes (read-key cannot trade).
- ✅ `venue_account_limits.yaml` populated + consumed by pre-flight risk checks.
- ✅ Multi-VM concurrent run does NOT exceed per-key venue rate limit.

---

## Phase 3 — Custody (Copper + CEFFU + Fireblocks) — Day 1-13 (CEFFU has longest lead time)

- [ ] [SCRIPT] P0. **3.A — Copper real-fund-movement test.** Verify-only — code is shipped. Execute small-amount
      sign-and-broadcast flow:
      `CopperCustodyProvider.sign_transaction(wallet_id=<test>, chain="ethereum-sepolia", raw_tx=<test>)` → POST
      `/platform/orders` → POST `/orders/{id}/sign` → MPC signing → on-chain broadcast → confirm tx hash on-chain.
  - **Verification**: tx hash visible in Sepolia Etherscan; `tx.from == copper_wallet_address`; round-trip latency ≤30s
    end-to-end.

- [ ] [HUMAN+AGENT] P0. **3.B — CEFFU integration.** **Longest lead time — START IMMEDIATELY.** Sub-deliverables:
  - [ ] [HUMAN] **3.B.1** — CEFFU institutional KYB onboarding (operator-side, 2-4 weeks).
  - [ ] [HUMAN] **3.B.2** — Confirm CEFFU's product offering: MirrorX (off-exchange-settlement linking CEFFU custody to
        Binance perp margin without moving funds) vs direct custody API. Asset coverage: BTC + ETH + USDC + USDT
        minimally + LST scope.
  - [ ] [AGENT] **3.B.3** — CEFFU SDK / API spec ingestion + factory-pattern adapter at
        `execution-service/execution_service/custody/ceffu.py` mirroring Copper shape. Register in `custody/factory.py`
        for `"ceffu"` key. HMAC / signing-key conventions per CEFFU spec.
  - [ ] [SCRIPT] **3.B.4** — End-to-end real-fund-movement test (mirror 3.A).
  - [ ] [AGENT] **3.B.5** — Operational-model decision: CEFFU replaces or augments Copper for `carry_staked_basis` spot
        leg. Document in `codex/04-architecture/custody-architecture.md` (NEW or UPDATE).

- [x] [DECISION] P0. **3.C — HSM-grade wallet signing path RESOLVED 2026-05-12** (operator R9 sub-(a) gate closed
      via AskUserQuestion). May-23 cutover ships on `CLOUD_KMS_ENCRYPTED`; June-1 flips per-wallet to
      `COPPER_MPC` / `FIREBLOCKS_MPC` on client-provided creds. See "R9 sub-(a) — RESOLVED" section above for
      full rationale + per-wallet flippability architecture. Split into 3.C.1 (cutover path) + 3.C.2
      (post-cutover Fireblocks).

  - [ ] [AGENT] P0. **3.C.1 — Cloud-KMS-encrypted wallet provisioning (May-23 cutover path).** Implementation:
        `execution-service/execution_service/custody/cloud_kms.py` (NEW) implementing `CustodyProvider` protocol
        — fetch envelope-encrypted private key from Secret Manager → call GCP `cloudkms.decrypt` (or AWS
        `kms.decrypt`) with the per-wallet CMK URI → in-memory decrypt → web3.py / solana-py signing → discard
        plaintext. Per-wallet CMK URI carried on
        `WalletProvisioningConfig.kms_key_uri` (UAC@`d721b6a`, shipped 2026-05-12). KMS Decrypter IAM bound to
        trading-VM SA only.
    - **Verification**: smoke test on Sepolia + Solana devnet via singleton-locked launcher
      `launch-defi-paper-trade-vm.sh` signs a transaction; latency budget ≤200ms KMS decrypt + ≤100ms web3 signing.
    - **Sub-residual**: per-wallet CMK rotation cadence (90-day default, configurable per asset_group);
      `rotation-runbook.md` entry per Phase 9.D.

  - [ ] [AGENT] P0. **3.C.2 — Fireblocks signer integration (June-1 post-cutover path).** **DEFERRED-AFTER-CUTOVER
        (2026-06-01)** — client provides Fireblocks credentials June 1st. Implementation:
        `execution-service/execution_service/custody/fireblocks.py` (NEW) mirroring Copper factory shape.
        Per-wallet flip from `CLOUD_KMS_ENCRYPTED` → `FIREBLOCKS_MPC` is config-only (no recompile) per
        `WalletProvisioningConfig.signing_surface` field. Successor plan:
        `plans/active/fireblocks_copper_client_integration_2026_06_01.md` (operator-spawned when client creds land).
    - **Verification**: smoke test on Sepolia signs a transaction via Fireblocks vault; latency budget within
      strategy-execution end-to-end target (HSM signing adds 100-500ms; verify under load).
    - **Sub-residual**: HD-wallet derivation under Fireblocks-protected master key → N×M wallets per R7 derive cleanly.

- [ ] [AGENT] P0. **3.D — Treasury rollup view — CANONICAL OWNER (ratified 2026-05-10 cross-plan audit Q7 per
      most-comprehensive-owner rule).** Combine custody balance (Copper + CEFFU) + venue margin balances + on-chain
      wallet balances into unified-NAV view. Extends `position-balance-monitor-service/.../core/treasury_monitor.py`.
      Composes with client-reporting question doc. Per-archetype-per-chain wallet rollup ties into R7 multi-wallet.
      **Endpoint surface owned here**: `/api/treasury/rollup` (multi-source unified NAV) +
      `/treasury/nav?client_id=<id>`.
      [`wallet_treasury_client_flow_2026_05_10.md`](wallet_treasury_client_flow_2026_05_10.md) Phase 5.B + 6.A
      `/api/clients/{id}/treasury` becomes a CONSUMER (per-client attribution layer over this canonical multi-source
      rollup). The two endpoints differ by axis: this owns the source-axis (Copper / CEFFU / venue / on-chain); wallet
      plan owns the client-attribution axis on top.
  - **Verification**: deployment-api `/treasury/nav?client_id=<id>` returns correct NAV at time T =
    `Σ (custody_balance × mark_price)` + `Σ (venue_margin × mark_price)` + `Σ (on_chain × mark_price)` summed without
    double-counting. Cross-check vs wallet plan's `/api/clients/{id}/treasury` returning same totals with per-client
    decomposition (NAV reconciles across both endpoints).

**Phase 3 done definition** (full-execution criterion):

- ✅ Copper sign-and-broadcast tx visible on Sepolia Etherscan.
- ✅ CEFFU KYB approved + adapter shipped + real-fund-movement test passing.
- ✅ Fireblocks signer integration smokes pass on Sepolia + mainnet wallet (small balance test).
- ✅ Treasury rollup endpoint returns reconciled NAV against ground-truth.

---

## Phase 4 — DeFi mainnet + testnet provisioning — Day 3-13

- [ ] [HUMAN+AGENT] P0. **4.A — Production wallets per chain × per archetype (multi-wallet R7).** N archetypes × M
      chains = N×M wallets. For May-23: `carry_staked_basis` + `ARBITRAGE_PRICE_DISPERSION` (config variant
      `funding_rate_dispersion` — canonical name per
      [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md:37-40`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
      and codex
      [`arbitrage-price-dispersion.md`](../../codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md)
      §28+§48-53; superseded the legacy `leveraged_funding_arb` standalone-archetype name 2026-05-09) — ≥2 archetypes ×
      5 chains (Ethereum, Arbitrum, Base, Polygon, Solana) = ≥10 mainnet wallets. HD-wallet derivation under
      `CLOUD_KMS_ENCRYPTED` per-asset_group master CMK for May-23 cutover; flippable to Fireblocks master seed
      per Phase 3.C.2 once June-1 client creds land. UAC type extension SHIPPED 2026-05-12: `WalletProvisioningConfig`
      at UAC@`d721b6a` carries (chain + signing_surface + kms_key_uri | custodian_wallet_id +
      allowed_protocols frozenset + allowed_destinations frozenset + spending_caps + kill_switch_id +
      archetype_id + derivation_path).
  - **Sub-residuals captured**: per-wallet nonce queue management; per-wallet RPC rate-limit sub-budget; cross-archetype
    rebalancing flow; per-wallet protocol-approval pre-signing.
  - [x] **4.A.SCHEMA — UAC wallet provisioning schema** SHIPPED 2026-05-12 by slot 4 at UAC@`d721b6a`:
        `SigningSurface` StrEnum (5 values) + `WalletKind` StrEnum (4 values) + `SpendingCaps` frozen
        dataclass (per_tx / per_hour / per_day + per_protocol_usd map) + `WalletProvisioningConfig` frozen
        dataclass with `validate()` enforcing 6 invariants (surface ↔ credential-pointer match, HOT_TRADING
        needs archetype_id, HOT_TRADING + GAS_RESERVE reject withdraw whitelist, kill_switch_id uses known
        KillSwitchId prefixes). 27 schema-validation tests at
        `tests/internal/unit/test_wallet_provisioning_schema.py` (all green). Imports:
        `from unified_api_contracts.internal.domain.defi import (SigningSurface, WalletKind, SpendingCaps,
        WalletProvisioningConfig, WalletProvisioningError)`. **Cross-tab handshake artefact** consumed by
        slot 5 (defi_recursive_borrow archetype config — chain × protocol per-wallet rows) + slot 8
        (cross_cutting #4 DART manual surfaces — wallet-tier kill-switch button per row).

- [ ] [AGENT] P0. **4.B — Per-protocol approvals SSOT + automation.** YAML at
      `unified-api-contracts/config/required_approvals.yaml` per (archetype, chain, protocol, asset). Pre-signing
      automation: `execution-service/scripts/vm/launch-defi-approval-presigner-vm.sh` per per-wallet × per-chain.
      Allowance ceiling: per-session-cap (safer) over `MAX_UINT256` (gas-cheaper) per CLAUDE.md security-grade default.
  - **Verification**: `cast call <protocol> "allowance(address,address)" <wallet> <protocol>` returns expected ceiling
    per (archetype, chain, protocol, asset).

- [ ] [AGENT] P1. **4.C — Bridge protocol adapters (CCTP / Wormhole / LayerZero).** Audit found intent-engine declares
      bridge steps but no adapters. Implement at least CCTP (Circle's cross-chain USDC) for May-23 — allows USDC
      movement Ethereum ↔ Solana for `carry_staked_basis` jitoSOL leg funding. Wormhole + LayerZero deferred unless
      carry archetype needs them.

- [ ] [AGENT+HUMAN] P0. **4.D — Testnet replica per R1.** Per operator direction "all 5 testnets in scope":
  - [ ] **4.D.1** — Add Arbitrum Sepolia (chain_id 421614), Base Sepolia (84532), Polygon Amoy (80002), Solana devnet to
        [unified-api-contracts/config/testnet_contracts.yaml](unified-api-contracts/config/testnet_contracts.yaml).
  - [ ] **4.D.2** — **Holesky decision**: Lido + EigenLayer testnet is Holesky, not Sepolia per `_defi_lst.py`. Either
        include Holesky as a 6th testnet OR substitute mock contracts on Sepolia for Lido/EigenLayer integration tests.
        **Recommendation**: include Holesky — net 6 testnets. Add to plan scope.
  - [ ] **4.D.3** — Funded operator testnet wallets per chain × per archetype (mirror 4.A on testnets).
  - [ ] **4.D.4** — Testnet RPC credentials per chain (Alchemy / QuickNode / Helius testnet tier).
  - [ ] **4.D.5** — FlashLoanReceiver redeploy per testnet (or share Sepolia address per testnet_contracts.yaml comment
        "Same receiver contract as Sepolia until a Holesky-specific deploy is registered" — operator decides
        per-chain-deploy vs shareable; default = shareable until Phase 4.D.5b).
  - [ ] **4.D.6** — Mock contracts on testnets where mainnet protocol has no testnet (Jito on Solana mainnet-only; Pyth
        on Solana mainnet-only; some Lido vault variants). Mock contract source under
        `deployment-service/contracts/mocks/`.
  - [ ] **4.D.7** — Faucet automation: Cloud Scheduler job per testnet that monitors operator wallet balance +
        auto-requests faucet drip when below threshold. Per-testnet faucet API.

- [ ] [SCRIPT] P0. **4.E — Pyth-on-Solana real-data smoke (R8).** Trigger MTDS `oracle_prices_handler` against mainnet
      Solana RPC + Hermes endpoint; capture per-LST price (jitoSOL / mSOL / bSOL); confirm against Pyth UI
      (pyth.network); verify event-stream emits per-asset progress events with row counts (CLAUDE.md "No fire-and-forget
      VM launches"). Sub-residuals: mSOL + bSOL Pyth-feed availability; Hermes rate-limit at production query frequency;
      failover when Hermes returns stale (> 30s timestamp).
  - **What runs**: `gcloud compute instances create mtds-pyth-realdata-smoke-$(date +%Y%m%d-%H%M%S)` per CLAUDE.md
    launcher SSOT.
  - **Verification**: `gcloud storage ls gs://${PID}-events/events/mtds/$(date +%Y-%m-%d)/<vm-name>/` shows STARTED +
    per-LST `INSTRUMENT_PROCESSED` events + STOPPED.

- [ ] [SCRIPT] P0. **4.F — Chainlink-on-EVM real-data smoke per chain (Ethereum / Arbitrum / Base / Polygon).** Mirror
      4.E shape; Chainlink reads on-chain (no off-chain credential beyond chain RPC) so simpler.

**Phase 4 done definition** (full-execution criterion):

- ✅ N×M mainnet wallets provisioned + HD-derived under Fireblocks master.
- ✅ Per-(archetype, chain, protocol, asset) approval set on-chain (verified via `cast call`).
- ✅ CCTP bridge adapter shipped + Sepolia smoke test passes.
- ✅ 6 testnets fully populated in `testnet_contracts.yaml` + funded operator wallets + RPC creds +
  flash-loan-receivers + faucet automation.
- ✅ Pyth Hermes smoke event-stream shows non-empty per-LST prices.
- ✅ Chainlink per-EVM-chain smoke passes.

---

## Phase 5 — Data sources (sports + prediction + DeFi-data + oracles) — Day 3-9

- [ ] [SCRIPT] P0. **5.A — Sports per-source rotation runbook.** Already partially shipped via
      `deployment-service@9943e7c9` (api-football + footystats + soccer-football-info added). Phase 5 sub-deliverables:
  - [ ] **5.A.1** — Provision API keys for any source not yet in Secret Manager (most exist; verify per Block E3).
  - [ ] **5.A.2** — `codex/14-customer-journeys/credentials/rotation-runbook.md` populates per-source rotation cadence +
        execution-owner per `Runbook Execution-Owner SSOT` HARD RULE.
  - [ ] **5.A.3** — Skip understat / transfermarkt / open_meteo / pyth-hermes from rotation tracking (public sources, no
        key — already excluded in 9943e7c9 commit per the comment).

- [ ] [HUMAN+AGENT] P0. **5.B — Prediction venue credentials.**
  - [ ] **5.B.1** — Polymarket API key provisioned (added to `_TRADE_KEY_PATTERNS` 2026-05-09; secret value not yet in
        Secret Manager per audit).
  - [ ] **5.B.2** — Kalshi API key (already in `_TRADE_KEY_PATTERNS`; verify provisioned in Secret Manager).
  - [ ] **5.B.3** — Manifold API key if archetype scope includes Manifold.
  - [ ] **5.B.4** — Per-venue prediction adapter at `execution-service/.../venues/polymarket.py` if not exists (audit
        found feature calculators but not execution adapter).

- [ ] [SCRIPT] P1. **5.C — DeFi-data credentials.** CoinGecko + Helius keys provisioned in Secret Manager (added to
      `_DATA_KEY_PATTERNS` 2026-05-09).

**Phase 5 done definition** (full-execution criterion):

- ✅ Every sports + prediction + DeFi-data source in `_TRADE_KEY_PATTERNS` / `_DATA_KEY_PATTERNS` has a Secret Manager
  value.
- ✅ Rotation runbook published at `codex/14-customer-journeys/credentials/rotation-runbook.md`.
- ✅ Polymarket execution adapter exists (or carry archetype scope confirms it's not needed).

---

## Phase 6 — Auxiliary services — Day 5-9

- [ ] [SCRIPT] P1. **6.A — Telegram per-environment scoping.** Audit found repo-level scope only (no per-env split).
      Provision separate bot tokens per env (dev / staging / prod); update GHA workflows per repo.

- [ ] [SCRIPT] P0. **6.B — Firebase service-account JSON storage.** Audit found `unified-trading-system-ui/.firebaserc`
      lists prod (`central-element-323112`) + staging (`odum-staging`) projects; SA JSON storage location not surfaced.
      Provision SA JSON in Secret Manager + Workload Identity Federation for Cloud Run → Firebase auth.

- [ ] [SCRIPT] P0. **6.C — GitHub Workload Identity Federation upgrade.** Audit found classic PATs (`secrets.GH_PAT` +
      `GH_TOKEN`) — replace with WIF (GCP / AWS → GitHub OIDC trust) per repo. Eliminates long-lived PATs.

- [ ] [SCRIPT] P2. **6.D — Anthropic API budget cap.** Per workflow run budget cap on `ANTHROPIC_API_KEY` usage.
      Currently advisory/audit workflows only — low-risk but unbounded.

**Phase 6 done definition** (full-execution criterion):

- ✅ Telegram per-env tokens provisioned + GHA workflows updated.
- ✅ Firebase SA JSON in Secret Manager + WIF configured.
- ✅ Every classic PAT replaced with WIF.
- ✅ Anthropic API budget cap configured.

---

## Phase 7 — Per-mode + per-archetype credential subset SSOTs — Day 8-11

Depends on Phases 2-6 having enumerated the universe of credentials.

- [ ] [AGENT] P0. **7.A — Per-mode credential subset SSOT.** YAML at
      `unified-api-contracts/config/credentials_per_mode.yaml`. Three top-level keys (`paper`, `batch`, `live`);
      per-mode list of required credentials. Paper = read-only venue keys + fork-wallet + cloud infra. Batch =
      historical-data sources + cloud infra + read-only venue keys (optional). Live = full set.

- [ ] [AGENT] P0. **7.B — Per-archetype credential subset checklist.** YAML at
      `unified-api-contracts/config/credentials_per_archetype.yaml`. Per archetype: minimum-viable credential subset to
      run live. Archetypes in scope per R4: `carry_staked_basis`, `ARBITRAGE_PRICE_DISPERSION` (canonical archetype;
      DeFi/CeFi cutover use the `funding_rate_dispersion` config variant per
      [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md:37-40`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
      — superseded the legacy `leveraged_funding_arb` standalone-archetype name; the prediction cutover use the
      cross-venue price-dispersion config variant of the same archetype), sports archetypes
      (`MARKET_MAKING_EVENT_SETTLED`, `ML_DIRECTIONAL_EVENT_SETTLED`, `RULES_DIRECTIONAL_EVENT_SETTLED`), prediction
      archetypes (`EVENT_DRIVEN` standalone; price-dispersion variant is the same `ARBITRAGE_PRICE_DISPERSION` row above
      keyed by `(archetype, config_variant)` not duplicated as a separate row).

**Phase 7 done definition** (full-execution criterion):

- ✅ Both YAMLs committed + consumed by Phase 8 audit script.
- ✅ Operator can answer "is `carry_staked_basis` credential-blocked today?" via
  `python -m deployment_service.scripts.credential_check --archetype carry_staked_basis`.

---

## Phase 8 — Audit recipe + continuous verification — Day 10-13

- [ ] [AGENT] P0. **8.A — One-stop credential probe script.** `deployment-service/scripts/audit/credential-probe.sh`.
      Per Block I.1 audit set: cloud SA / per-bucket / per-Secret-Manager-path / per-venue / per-chain RPC / per-wallet
      / per-custody / per-data-source / per-aux-service. `--mode {paper,batch,live}` + `--archetype <name>` flags
      consume Phase 7 SSOTs. Per-credential green/red + final sign-off line.
  - **Execution-owner SSOT** per `Runbook Execution-Owner SSOT` HARD RULE: owner = deployment-service maintainer;
    cadence = daily cron VM; verifier = event-stream `STARTED + STOPPED + non-empty per-credential progress events`;
    `last_executed: <YYYY-MM-DD>` populated on every run.

- [ ] [AGENT] P1. **8.B — Health endpoint credential probes.** Extend `make_health_router()` per QG STEP 5.62 —
      currently reports `data_freshness` only. Add `credentials_health` callback per service that probes credentials the
      service consumes (read-only API call; cache 60s TTL).

- [ ] [AGENT] P0. **8.C — Master plan continuous-verification column.** Update
      `plans/active/master_to_live_defi_2026_05_23.md` per-service readiness checklist (Groups A-G; 23 items) per
      `Master Plan Continuous-Verification Column` HARD RULE. Group F items 17-23 + Group G item 23 each declare cron /
      Tab / QG cadence + `Last verified` date.

- [ ] [SCRIPT] P0. **8.D — Pre-cutover sign-off gate.** Audit script run within 24h of May-23 cutover; output 100% pass
      for Block I.6 criteria. Operator review + manual approval before live-trading kill-switch flip.

**Phase 8 done definition** (full-execution criterion):

- ✅ `credential-probe.sh` runs end-to-end with `--mode live --archetype carry_staked_basis` + returns 100% pass against
  real systems.
- ✅ Health endpoints report credential validity (sample: `curl <service>/health/credentials` returns non-error).
- ✅ Master plan continuous-verification column populated for all 23 readiness items.
- ✅ Pre-cutover gate executed within 24h of May-23; operator sign-off recorded.

---

## Phase 9 — Codex SSOT updates — every phase boundary + final consolidation

Per `Post-Plan-Phase Codex Audit` HARD RULE — codex updates ride in same logical unit as code commits, not deferred.

- [ ] [AGENT] P0. **9.A — `codex/05-infrastructure/credentials-matrix.md`** (NEW) — workspace credential SSOT. Stub from
      Phase 0.D; full content populated per Phase boundary (each phase's credentials added to matrix as they ship).

- [ ] [AGENT] P0. **9.B — `codex/05-infrastructure/aws-iam-matrix.md`** (NEW) — per-service AWS IAM. Populated by Phase
      1.B.

- [ ] [AGENT] P0. **9.C — `codex/05-infrastructure/secret-manager-naming.md`** (NEW) — naming convention SSOT. Codifies
      the `<env>-<service>-<credential>` pattern + the `<venue>-<scope>-<key|secret>` extension from Phase 2.C.

- [ ] [AGENT] P0. **9.D — `codex/14-customer-journeys/credentials/rotation-runbook.md`** (NEW) — rotation cadence +
      execution-owner per credential class. Populated by Phase 5.A.2.

- [ ] [AGENT] P0. **9.E — `codex/05-infrastructure/per-archetype-wallet-isolation.md`** (NEW) — multi-wallet model.
      Populated by Phase 4.A.

- [ ] [AGENT] P0. **9.F — `codex/05-infrastructure/hsm-wallet-signing.md`** (NEW) — HSM tier discipline. Populated by
      Phase 3.C.

- [ ] [AGENT] P0. **9.G — UPDATE `codex/04-architecture/interface-credential-convention.md`** — per-credential-class
      examples + cross-cloud guidance from this plan.

- [ ] [AGENT] P0. **9.H — UPDATE `codex/06-coding-standards/config-reloader-pattern.md`** — `ApiKeyReloader` per-service
      coverage matrix from Block H1 audit.

- [ ] [AGENT] P1. **9.I — UPDATE `codex/05-infrastructure/runtime-tiers-and-deployment.md`** — credential subset per
      tier from Phase 7.A.

- [ ] [AGENT] P1. **9.J — UPDATE `codex/14-customer-journeys/authentication/firebase-local.md`** — Firebase prod vs
      emulator credential split from Phase 6.B.

- [ ] [AGENT] P0. **9.K — UPDATE `codex/04-architecture/custody-architecture.md`** (NEW or UPDATE) — Copper + CEFFU +
      Fireblocks operational model from Phase 3.

**Phase 9 done definition** (full-execution criterion):

- ✅ All 11 codex docs (6 NEW + 5 UPDATE) shipped.
- ✅ No "we'll write the codex later" placeholders.
- ✅ Per-phase codex updates rode the same commit batch as their code phase.

---

## Cross-phase coordination

- **Phase 1.E (AWS Secrets Manager replication)** depends on **Phase 0.A (gitleaks scan)** — don't replicate compromised
  credentials.
- **Phase 2.B (native adapters)** depends on **Phase 0.D `secret-manager-naming.md` stub** for new path conventions.
- **Phase 3.C (Fireblocks)** blocks **Phase 4.A (multi-wallet HD derivation)** — Fireblocks vault must exist before
  HD-deriving N×M wallets under it.
- **Phase 7 (subset SSOTs)** depends on **Phases 2-6 having enumerated** the universe of credentials.
- **Phase 8 (audit script)** depends on **Phase 7 SSOTs** for `--mode` + `--archetype` flag implementation.
- **Phase 9 (codex)** rides every phase boundary per HARD RULE — not deferred to plan-end.

## Cross-plan dependencies

- **Master plan** `plans/active/master_to_live_defi_2026_05_23.md` Groups F+G — this plan populates the
  continuous-verification column for credential-dependent gates.
- **DeFi master** `plans/active/defi_master_2026_05_07.md` — Phase 4 mainnet wallet + multi-wallet + flash-loan-receiver
  per chain composes; pre-archive jitoSOL gap (2022-11-01 → 2023-10-01) tracked there.
- **CeFi master** `plans/epics/cefi_master_2026_05_07.md` — Phase 2 native adapters + per-scope key separation composes.
- **Infrastructure master** `plans/epics/infrastructure_master_2026_05_07.md` — Phase 1 AWS parity is largest
  sub-deliverable.
- **Sibling question docs** `client_reporting_pnl_attribution_2026_05_08.md` +
  `risk_simulations_limits_alerting_2026_05_08.md` — Phase 3.D treasury rollup feeds client-reporting; Phase 7
  per-archetype subset feeds per-archetype risk limits.
- **Runbook governance** `plans/archive/issues/runbook_execution_governance_gaps_2026_05_08.md` — Phase 8.A audit script
  needs `execution.owner` declaration per HARD RULE.

## Pre-audit manifest (per Citadel-Grade Planning § 1)

Files referenced + likely modified per phase:

| Phase | Files                                                                                                                                                                                                                                                                                                                                                                                                       |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | `.gitignore` per repo; pre-commit config per repo; codex/05-infrastructure/{credentials-matrix,aws-iam-matrix,secret-manager-naming,per-archetype-wallet-isolation,hsm-wallet-signing}.md (NEW); codex/14-customer-journeys/credentials/rotation-runbook.md (NEW)                                                                                                                                           |
| 1     | deployment-service/configs/{gcp_service_accounts.yaml,aws_iam_roles.yaml,bucket_config.yaml}; deployment-service/cloudbuild.yaml; deployment-service/buildspec.aws.yaml; deployment-service/scripts/vm/launch-\*-vm-aws.sh (NEW per launcher); deployment-service/scripts/vm/vm_zombie_watchdog_aws.py (NEW); unified-trading-library/.../cloud_interface/providers/{gcp.py,aws.py}                         |
| 2     | execution-service/execution*service/venues/\_base.py (NEW VenueAdapterBase); execution-service/execution_service/venues/{bybit,binance,okx,kraken,bitfinex,bitget}.py (REWRITE native); execution-service/execution_service/factory.py (per-scope routing); unified-api-contracts/config/venue_account_limits.yaml (NEW); unified-api-contracts/tests/vcr/test*<venue>\_native_vcr.py per venue (NEW)       |
| 3     | execution-service/execution_service/custody/{ceffu,fireblocks}.py (NEW); execution-service/execution_service/custody/factory.py (extend); position-balance-monitor-service/.../core/treasury_monitor.py (extend); deployment-api/.../routes/treasury.py (NEW or extend)                                                                                                                                     |
| 4     | unified-api-contracts/config/{testnet_contracts.yaml,required_approvals.yaml}; deployment-service/scripts/vm/launch-defi-approval-presigner-vm.sh (NEW); deployment-service/contracts/mocks/\*.sol (NEW); execution-service/execution_service/defi_execution/protocols/bridges/{cctp,wormhole,layerzero}.py (NEW); deployment-service/scripts/audit/{pyth-realdata-smoke,chainlink-realdata-smoke}.sh (NEW) |
| 5     | deployment-service/functions/rotate-exchange-keys/main.py (already extended 9943e7c9); execution-service/.../venues/polymarket.py (NEW or extend); GCP Secret Manager provisioning                                                                                                                                                                                                                          |
| 6     | .github/workflows/ per repo (Telegram + WIF); unified-trading-system-ui/firebase auth wiring; deployment-service/configs/anthropic_budget.yaml (NEW)                                                                                                                                                                                                                                                        |
| 7     | unified-api-contracts/config/{credentials_per_mode.yaml,credentials_per_archetype.yaml} (NEW); deployment-service/scripts/credential_check.py (NEW)                                                                                                                                                                                                                                                         |
| 8     | deployment-service/scripts/audit/credential-probe.sh (NEW); unified-trading-library/.../api/health.py (extend make_health_router); plans/active/master_to_live_defi_2026_05_23.md (continuous-verification column)                                                                                                                                                                                          |
| 9     | codex/{05-infrastructure,04-architecture,06-coding-standards,14-customer-journeys}/\*.md per Phase 9 list above                                                                                                                                                                                                                                                                                             |

## Success criteria per phase

Each phase's "done definition" is the hard gate. Workspace-wide criteria:

- **Code gates**: `bash scripts/quality-gates.sh` clean per repo at end of each phase; basedpyright clean; ruff clean.
- **Test gates**: per-venue VCR cassettes recorded + passing (Phase 2); custody integration tests passing (Phase 3);
  testnet smokes passing (Phase 4); credential-probe script returns 100% pass (Phase 8).
- **Real-infra gates** per "Plans Run To Actual Completion": no operation marked done without verification probe (gcloud
  / aws CLI / event-stream check).
- **Codex gates**: every phase's codex updates shipped in the same logical unit per HARD RULE.

## Continuous verification cadence (post-cutover)

Per `Master Plan Continuous-Verification Column` HARD RULE, every credential-dependent gate declares cadence:

- Daily cron: `credential-probe.sh --mode live --archetype <name>` per archetype.
- Daily cron: rotation-tracking scan (already exists at `deployment-service/functions/rotate-exchange-keys/main.py`).
- Per-PR: gitleaks scan in `.github/workflows/secret-scan.yml`.
- Weekly: full workspace `gitleaks detect` + audit log.
- Pre-cutover (May-22): full credential probe must return 100% pass.

## Estimated AI-day breakdown

| Phase     | Description                                 | Est AI-days       | Critical-path         |
| --------- | ------------------------------------------- | ----------------- | --------------------- |
| 0         | Security + foundation                       | 2-3               | Yes                   |
| 1         | Cloud provisioning AWS↔GCP parity          | 7-10              | Yes (longest)         |
| 2         | Trading venue credentials + native adapters | 10-15             | Yes                   |
| 3         | Custody (Copper + CEFFU + Fireblocks)       | 6-9               | Yes (CEFFU lead time) |
| 4         | DeFi mainnet + testnet provisioning         | 6-9               | Yes                   |
| 5         | Data sources                                | 1-2               | No                    |
| 6         | Auxiliary services                          | 2-3               | No                    |
| 7         | Per-mode + per-archetype subset SSOTs       | 1-2               | Yes                   |
| 8         | Audit recipe + continuous verification      | 3-4               | Yes                   |
| 9         | Codex SSOT updates                          | per-phase         | Yes                   |
| **Total** |                                             | **38-57 AI-days** |                       |

At 5-10 parallel agents per phase, 13 days (2026-05-10 → 2026-05-23) is achievable but tight. CEFFU KYB onboarding
(Phase 3.B.1) is the longest single lead time — must start Day 1.

## Temporary states + their canonical follow-up plans

Per CLAUDE.md "Temporary state must have a named successor plan" HARD RULE — items that ship as partial states this
cycle:

- **CEFFU adapter** if KYB doesn't complete by May-23: temporary state = Copper-only spot leg; successor plan =
  `plans/active/ceffu_post_kyb_integration_<date>.md` (operator-spawned post-KYB).
- **Native venue adapters** if 6-venue scope can't ship by May-23: temporary state = CCXT pass-through retained for
  missing venues; successor plan = `plans/active/native_venue_adapter_<venue>_<date>.md` per remaining venue.
- **Bridge protocol adapters beyond CCTP** (Wormhole / LayerZero): out-of-scope for May-23 unless archetype scope adds
  them; successor plan = `plans/active/bridge_adapters_wormhole_layerzero_<date>.md`.

## DONE-2026-05-15 — slot 4 FULL CYCLE CLOSE (2026-05-12) `ikenna-keys-wallets-tab`

> **Full cycle scope CLOSED on Day 1** at high density (~18-22 calibrated AI-days
> shipped vs ~16 budgeted = ~120% of cycle scope on Day 1). Operator direction
> 2026-05-12: *"finish the job do everything"* — Day 2-4 scope absorbed.

### What shipped Day 1 (2026-05-12) — full cycle

| Phase / item | Status | Shipped at | Notes |
|---|---|---|---|
| **Phase 1 — Custody KYB checklist** | ✅ DONE | PM@`2e198794` | `codex/05-infrastructure/custody-onboarding-checklist.md` NEW + Cloud-KMS provisioning operator-action issue doc |
| **Phase 2 — Fireblocks R9 decision dispatch** | ✅ RESOLVED | 2026-05-12 via AskUserQuestion | CLOUD_KMS for May-23 → COPPER/FIREBLOCKS June-1 |
| **Phase 3 — UAC wallet provisioning schema** | ✅ DONE | UAC@`d721b6a` | `SigningSurface` (5 values) + `WalletKind` (4 values) + `SpendingCaps` + `WalletProvisioningConfig` + 27 tests |
| **Phase 4.A.SCHEMA** | ✅ DONE | UAC@`d721b6a` | Wallet schema with chain + protocol + signing surface + allowlist + spending cap + kill-switch hook |
| **Phase 4.A — May-23 cutover wallet template** | ✅ DONE | UAC@`b9050d7` | 10 HOT_TRADING + 5 GAS_RESERVE wallets across 2 archetypes × 5 chains. 15 validation tests. |
| **Phase 4.B — required_approvals.yaml** | ✅ DONE | UAC@`d8e2dbc` | 38 approval rows across 2 archetypes × 5 chains × 4-8 protocols. 12 tests. |
| **Phase 5 — KillSwitchId.KILL_PER_WALLET sentinel** | ✅ DONE | UAC@`5c2d70b` | Runtime-targeted wallet-tier kill-switch via target_wallet_id field. 3 new tests. |
| **Phase 7.A — credentials_per_mode.yaml** | ✅ DONE | UAC@`d8e2dbc` | 3 modes (paper/batch/live) × full credential subsets. 9 tests. |
| **Phase 7.B — credentials_per_archetype.yaml** | ✅ DONE | UAC@`d8e2dbc` | 5 archetypes × full credential bundles. 9 tests. |
| **Phase 8.A — credential-probe.sh** | ✅ DONE | deployment-service@`15f5a1b` | One-stop audit reading per-mode + per-archetype YAMLs. Dry-run validated 6 (paper) → 34 (live + carry_staked_basis). |
| **Phase 9.A — credentials-matrix.md** | ✅ DONE | PM@`e4c49a88` | Workspace credential SSOT (7 classes, per-cloud parity, continuous-verification) |
| **Phase 9.C — secret-manager-naming.md** | ✅ DONE | PM@`e4c49a88` | `<class>-<surface>-<role>-<version>` pattern SSOT |
| **Phase 9.E — per-archetype-wallet-isolation.md** | ✅ DONE | PM@`e4c49a88` | N×M multi-wallet model SSOT |
| **Phase 9.F — hsm-wallet-signing.md** | ✅ DONE | PM@`e4c49a88` | 5-tier HSM ladder SSOT |
| **Phase 9.K — custody-providers.md banner + factory table** | ✅ DONE | PM@`2e198794` | R9 propagation; per-wallet flippability |
| **Phase 3.C.2 — Fireblocks integration spec** | ✅ DESIGN-SHIPPED | PM@`e4c49a88` | Paste-ready engineering spec for June-1 implementation |
| **Cross-tab handshakes** — slots 5 + 8 | ✅ PUBLISHED | PM@`8aaf70da` | Schema importable; slot 5 EOD confirms consumed via Family-1/2 catalog config |
| **Plan flips Phase 3.C SPLIT + 4.A + R9** | ✅ DONE | PM@`5cc47002` | Plan body codifies decision tree |
| **Cloud-KMS operator-action issue doc** | ✅ FILED | PM@`2e198794` | `plans/active/issues/cloud_kms_cmk_provisioning_for_may23_cutover_2026_05_12.md` P0 |

### Sub-residuals + deferrals (Half 3 scoreboard)

| Phase / item | Status | Successor / blocker |
|---|---|---|
| Phase 3.A — Copper sandbox sign-and-broadcast smoke | 🟡 OPEN | Operator-runnable (§ A.1.5 in custody-onboarding-checklist.md) before 2026-05-21 |
| Phase 3.B — CEFFU KYB onboarding | 🟡 BLOCKED on operator KYB submission | 2-4 week SLA; runbook § D in checklist |
| Phase 3.C.1 — CloudKmsCustodyProvider implementation | 🟡 OPEN | Owner: slot-4 successor + Harsh implementation; **gates May-23 cutover** |
| Phase 3.C.2 — FireblocksCustodyProvider implementation | 🟡 DEFERRED-AFTER-CUTOVER (2026-06-01) | Successor plan: `plans/active/fireblocks_copper_client_integration_2026_06_01.md` (operator-spawned post-creds) — design fully spec'd at PM@`e4c49a88` |
| Phase 3.D — Treasury rollup `/api/treasury/rollup` endpoint | 🟡 OPEN | deployment-api scope; not done this cycle (collision avoidance with slot 8 cross_cutting #4) — Day 2 next cycle |
| Phase 4.A wallet-row JSON real-address fill | 🟡 BLOCKED on operator Cloud HSM CMK provisioning per issue doc — template ready at UAC@`b9050d7` | Operator runbook § B.3 in checklist; 4-6 hour operator-task |
| Phase 4.C — Bridge protocol adapters (CCTP / Wormhole / LayerZero) | 🟡 DEFERRED P1 — not gating | Slot 4 successor or post-cutover |
| Phase 4.D — Testnet replicas + faucet automation | 🟡 OPEN | Sub-task of Phase 4.A operator runbook |
| Phase 4.E — Pyth-on-Solana real-data smoke | 🟡 OPEN | MTDS scope; coordinate with slot 2 / Harsh |
| Phase 4.F — Chainlink-on-EVM real-data smoke per chain | 🟡 OPEN | MTDS scope |
| Phase 6.A — Telegram per-environment scoping | 🟡 OPEN | Deployment-service scope |
| Phase 6.B — Firebase SA JSON + WIF | 🟡 OPEN | Deployment-service scope |
| Phase 6.C — GHA WIF upgrade (replace PATs) | 🟡 OPEN | GHA scope |
| Phase 6.D — Anthropic API budget cap | 🟡 OPEN — P2 | Deployment-service scope |
| Phase 8.B — Health endpoint credential probes | 🟡 OPEN | UTL `make_health_router` extension |
| Phase 8.C — Master plan continuous-verification column | 🟡 OPEN | Master plan refresh; coordinate with slot 1 |
| Phase 8.D — Pre-cutover sign-off gate | 🟡 OPEN | Operator-runnable on 2026-05-22 via `credential-probe.sh --mode live --archetype carry_staked_basis` (target 100% pass) |
| Phase 9.B — aws-iam-matrix.md (PENDING Phase 1.B) | 🟡 OPEN | Depends on Phase 1.B (AWS IAM provisioning, slot 4 successor or operator) |
| Phase 9.D — rotation-runbook.md | 🟡 OPEN | Depends on Phase 5.A.2 |
| Phase 9.G — Update interface-credential-convention.md | 🟡 OPEN | Codex propagation |
| Phase 9.H — Update config-reloader-pattern.md | 🟡 OPEN | Codex propagation |
| Phase 9.I — Update runtime-tiers-and-deployment.md | 🟡 OPEN | Codex propagation |
| Phase 9.J — Update firebase-local.md | 🟡 OPEN | Codex propagation |
| Phase 1 — AWS↔GCP parity workstream | 🟡 DEFERRED — biggest single workstream (7-10 AI-days) | Slot 4 successor or operator; gating dual-cloud-active steady state but NOT gating May-23 cutover |
| Phase 2 — Trading venue credentials native adapters | 🟡 DEFERRED — 10-15 AI-day workstream | Slot 4 successor or Harsh; uses Phase 4.A schema + secret-manager-naming SSOT |

### Cycle-1 → Cycle-2 (2026-05-16+) priority

1. **Phase 3.C.1** `CloudKmsCustodyProvider` impl — **gates May-23 cutover**. Slot 4 successor or Harsh.
2. **Phase 4.A** operator Cloud HSM CMK provisioning (issue doc) — 4-6 operator-hours; **gates May-23 cutover**.
3. **Phase 3.A** Copper sandbox smoke — pre-cutover gate.
4. **Phase 8.D** pre-cutover sign-off (May-22).
5. **Phase 1** AWS↔GCP parity — dual-cloud steady-state, NOT blocking May-23.

### Continuous-verification (per Runbook Execution-Owner SSOT HARD RULE)

`codex/05-infrastructure/custody-onboarding-checklist.md` § F declares cadence per surface.
`credential-probe.sh` is the verification harness — daily cron VM owner =
deployment-service maintainer; cadence = daily; verifier = exit 0 + per-credential
events; last_executed = NEVER (pending first operator run).

## DONE-2026-05-15 — slot 4 Day 1 (2026-05-12) `ikenna-keys-wallets-tab`

Cycle scope (per [`work_split_2026_05_12_ikenna.md`](work_split_2026_05_12_ikenna.md) row 4): Phase 1 Copper KYB
checklist + Phase 2 Fireblocks R9 dispatch + Phase 3 wallet provisioning schema. Density target 3.5-4 calibrated
AI-days/day. **Day-1 actual: ~5 AI-days shipped end-to-end** (schema + R9 dispatch + plan flip + handshake ping +
custody onboarding checklist + R9 codex propagation + Cloud-KMS issue doc); meets density target on Day 1.

### What shipped Day 1 (2026-05-12)

| Phase / item | Status as of 2026-05-12 | Successor / blocker |
|---|---|---|
| Phase 4.A.SCHEMA — UAC `WalletProvisioningConfig` schema | ✅ DONE — UAC@`d721b6a` + 27 tests | Unblocks slot 5 Family-1/2 archetype config + slot 8 cross_cutting #4 DART surfaces (handshake ping shipped PM@`8aaf70da`) |
| Phase 2 — Fireblocks R9 sub-(a) operator gate | ✅ RESOLVED 2026-05-12 via AskUserQuestion → CLOUD_KMS for May-23 → COPPER/FIREBLOCKS June-1 | Decision codified in plan body § R9 RESOLVED + propagated to `defi_master_2026_05_07.md` + `codex/04-architecture/custody-providers.md` top banner |
| Phase 3.C SPLIT into 3.C.1 (Cloud-KMS) + 3.C.2 (Fireblocks) | ✅ design-shipped at PM@`5cc47002` | 3.C.1 implementation `CloudKmsCustodyProvider` PENDING — owner: slot-4 successor + Harsh side |
| Phase 1 operator-action checklist — codex doc | ✅ DONE — `codex/05-infrastructure/custody-onboarding-checklist.md` at PM@`2e198794` | Covers Copper verification (§ A) + Cloud-KMS provisioning (§ B) + Fireblocks June-1 path (§ C) + CEFFU KYB (§ D) + risk wiring (§ E) + continuous-verification cadence (§ F) |
| Phase 1 — Cloud HSM CMK provisioning operator-action issue doc | ✅ DONE — `plans/active/issues/cloud_kms_cmk_provisioning_for_may23_cutover_2026_05_12.md` | P0; 4-6 operator-hours; May-21 acceptance gate |

### Deferred / open after 2026-05-12 session (Half 3 scoreboard)

| Phase / item | Status as of 2026-05-12 | Successor / blocker |
|---|---|---|
| Phase 3.A — Copper sandbox real sign-and-broadcast smoke | OPEN | Operator-runnable (§ A.1.5 in checklist) before 2026-05-21 |
| Phase 3.B.1 — CEFFU institutional KYB onboarding | 🟡 BLOCKED on operator KYB submission | 2-4 week SLA; KYB form upload (§ D.1 in checklist) |
| Phase 3.B.2-5 — CEFFU API spec ingestion + adapter + test | 🟡 BLOCKED on D.1 + CEFFU spec delivery | Successor: same plan Phase 3.B.3 once spec lands |
| Phase 3.C.1 — `CloudKmsCustodyProvider` implementation | OPEN | Owner: slot-4 successor or Harsh implementation handoff; **gates May-23 cutover** |
| Phase 3.C.2 — `FireblocksCustodyProvider` implementation | 🟡 DEFERRED-AFTER-CUTOVER (2026-06-01) | Gated on client June-1 credential delivery; successor plan named: `plans/active/fireblocks_copper_client_integration_2026_06_01.md` (operator-spawned when creds land) |
| Phase 3.D — Treasury rollup view canonical owner | OPEN — wallet-tier surfaces ready via schema | Owner: slot 4 (continuing) — Day 2 scope: deployment-api `/treasury/nav` endpoint + PBMS wiring |
| Phase 4.A — N×M mainnet wallets provisioning | OPEN (schema shipped; wallet rows pending) | Gated on Cloud-KMS CMK provisioning per issue doc; Day 2-3 scope once operator completes B.1-B.3 |
| Phase 4.B — Per-protocol approvals SSOT + automation | OPEN | Day 2-3 scope |
| Phase 7 — Per-mode + per-archetype credential subset SSOTs | OPEN | Depends on Phases 2-6 enumeration; Day 3-4 scope |
| Phase 8 — Audit recipe + continuous verification | OPEN | Depends on Phase 7; Day 3-4 scope |
| Phase 9 — Codex SSOT updates | PARTIAL — `custody-providers.md` + `custody-onboarding-checklist.md` shipped today; remaining 9 docs Day 2-4 | Per-phase as remaining phases ship |

### Day 2-4 plan (2026-05-13 → 2026-05-15)

1. **Day 2** (2026-05-13): Phase 3.D treasury rollup `/api/treasury/rollup` endpoint design + PBMS wiring spec.
   Phase 4.A wallet-row JSON generation (10+ mainnet wallets) — depends on operator Cloud HSM CMKs provisioning (issue
   doc). Phase 9 codex stubs (`credentials-matrix.md`, `aws-iam-matrix.md`, `secret-manager-naming.md`,
   `per-archetype-wallet-isolation.md`, `hsm-wallet-signing.md`).
2. **Day 3** (2026-05-14): Phase 4.B per-protocol approvals YAML + pre-signing automation script. Phase 7 per-mode +
   per-archetype credential subset YAMLs.
3. **Day 4** (2026-05-15): Phase 8 audit script `credential-probe.sh` + health endpoint extension. Phase 8.C master
   plan continuous-verification column. EOD reset to 2026-05-16 cycle plan.

### Continuous-verification (per Runbook Execution-Owner SSOT HARD RULE)

Codex doc § F declares cadence for every credential surface (Copper / Cloud-KMS / Fireblocks / CEFFU): daily cron VM
`credential-probe-vm` + position-balance-monitor 60s reconciliation + per-PR `secret-scan.yml` + weekly full-workspace
`gitleaks` + pre-cutover (May-22) full credential probe gate. All `last_executed: NEVER` today; operator-runbook items
in checklist § A-D drive first executions.

## Provenance

- **Spawned from**: `plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md` (retired 2026-05-09 PM@5d2d74c1
  with the rest of `plans/questions/` after plan promotion) — full audit findings + R1-R10 resolutions + sub-residual
  investigations now live in this plan body.
- **Code commit shipped during plan extraction**: `deployment-service@9943e7c9` extends rotation-tracking SSOT with 8
  venues + 5 data sources.
- **Operator directives codified**:
  - 2026-05-09 R1-R10 resolutions: "no shortcuts, all for May-23."
  - 2026-05-09 sub-residual investigation: "use gcs and code to answer your own questions or run tests."
  - 2026-05-09 `.env` security: "scan .env security and ensure in secret manager."
  - 2026-05-10 plan extraction: "plans in plan that can be executed without the questions directory."

## Iteration log

| Date       | Author     | Change                                                                                                                                               |
| ---------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-10 | main agent | Plan spawned from question doc. All 10 residuals resolved + sub-residuals captured. Self-contained for execution; no need to re-read questions/ doc. |
