---
name: promote-workflow-may23-cli-path
overview: Harden the operator-CLI promote path (run-paper.sh + run-live.sh + colocated_engine.py) so the May-23 live-DeFi cutover ships with two archetypes (carry_staked_basis lead + ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion hedge) running ≥7 continuous days on real custody + real venues + real wallet, with full event audit trail + reconciliation + kill-switch arming. UI-driven workflow is post-cutover (separate plan).
type: plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: 13 days
spawned_from: plans/questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md
companion_to: plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md
locked_by: live-defi-rollout
locked_since: 2026-05-10
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md
  - plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md
  - plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md
  - plans/epics/defi_master_2026_05_07.md
  - plans/epics/strategy_and_dart_master_2026_05_07.md
related_codex:
  - codex/09-strategy/operational/cli-promote-paths.md
  - codex/04-architecture/promote-workflow-architecture.md
  - codex/05-infrastructure/strategy-vm-launcher-shape.md
  - codex/04-architecture/custody-providers.md
  - codex/05-infrastructure/launcher-script-ssot.md
---

# Promote Workflow — May-23 cutover via operator-CLI path

## Why this plan exists

The promote workflow audit (`plans/questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md`, completed 2026-05-10) found that the **UI-driven promote pipeline is 100% mock** (9 lifecycle sub-pages exist, `onPromote` callback unimplemented, no backend endpoint, no paper/live VM launcher, no candidate manifest, 4 competing lifecycle SSOTs, no ranking surface). **But the operator-CLI path is genuinely capable**: [`e2e-testing/scripts/defi/run-paper.sh`](../../../e2e-testing/scripts/defi/run-paper.sh) + [`run-live.sh`](../../../e2e-testing/scripts/defi/run-live.sh) + [`colocated_engine.py`](../../../e2e-testing/scripts/defi/colocated_engine.py) (1343 lines) integrate strategy + execution + position + P&L + risk in shared memory; auto-detect DeFi/CeFi/TradFi/Sports; support Tenderly fork (paper) + Copper MPC (live); run `--continuous`.

**Strategic call**: For May-23, the promote workflow = **operator-CLI**. The UI workflow is a 4-6 week post-cutover plan. **No shortcuts** means: harden the CLI path so every gate that the UI would enforce (custody connected / venue keys present / alerting wired / kill-switch armed / risk limits set / recon green / paper-evidence ≥3d) is enforced via CLI pre-flight, scripted, repeatable, and verifiable. Cutover runs without operator improvising mid-run.

Per CLAUDE.md HARD RULE *"Plans Run To Actual Completion, Not Smoke-Test Green"*: every phase's done-definition includes a **Full-execution criterion** with the actual command + machine + duration + verification probe + observed output. Phases marked PARALLEL run concurrently; phases marked SEQUENTIAL gate on the prior phase's QG.

## Pre-audit manifest

Per Citadel-Grade § 1, the audit (Question doc `## Audit findings` section) is the pre-audit. Concrete files this plan touches:

| File | Repo | Action |
|------|------|--------|
| `deployment-service/scripts/vm/launch-strategy-paper-vm.sh` | deployment-service | NEW (Phase 1) |
| `deployment-service/scripts/vm/launch-strategy-live-vm.sh` | deployment-service | NEW (Phase 1) |
| `deployment-service/scripts/vm/vm_zombie_watchdog.py` | deployment-service | UPDATE — register `strategy-paper-` + `strategy-live-` prefixes in `VM_PREFIX_TO_BUCKET` (Phase 1) |
| `e2e-testing/scripts/defi/preflight-cutover.sh` | e2e-testing | NEW (Phase 2) |
| `e2e-testing/scripts/defi/run-paper.sh` | e2e-testing | UPDATE — call preflight-cutover.sh as required gate (Phase 2) |
| `e2e-testing/scripts/defi/run-live.sh` | e2e-testing | UPDATE — call preflight-cutover.sh as required gate (Phase 2) |
| `strategy-service/scripts/run_2yr_config_grid_backtest.py` | strategy-service | UPDATE — write to canonical PATH_REGISTRY path + emit manifest row (Phase 3) |
| `unified-trading-library/unified_trading_library/config_interface/paths/registry.py` | UTL | VERIFY — `backtest_results/strategy_id={strategy_id}/run_id={run_id}/` is canonical; reader shape mismatch blocked at lift (Phase 3) |
| `unified-trading-library/unified_trading_library/domain/execution_client.py` | UTL | UPDATE — fix path mismatch with PATH_REGISTRY (Phase 3) |
| `execution-service/execution_service/custody/copper.py` | execution-service | OPERATIONAL — first live-signing dry-run on testnet (Phase 4.A) |
| `execution-service/execution_service/venues/initializer.py` + 5 venue adapters | execution-service | UPDATE — testnet-mode constructor for Bybit/Binance/OKX/Hyperliquid/Aster (Phase 4.B) |
| `execution-service/execution_service/defi_execution/connectors/solana_*.py` | execution-service | NEW — Solana paper analogue for LST yield archetypes (Phase 4.C) |
| `batch-live-reconciliation-service/` | batch-live-reconciliation-service | NEW — minimum-viable per-archetype P&L diff + per-trade fill comparison + cron VM (Phase 5.A) |
| `alerting-service/alerting_service/notifiers/router.py` + Secret Manager paths | alerting-service | UPDATE — Phase 4 paging targets wired (Phase 5.B) |
| 13 codex docs (Phase 7) | unified-trading-pm | NEW + UPDATE per Phase 7 enumeration |
| `unified-trading-pm/cursor-configs/CLAUDE.md` | unified-trading-pm | UPDATE — add "Promote Workflow Path" key rule (Phase 7) |
| `unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.md` | unified-trading-pm | UPDATE — `Last verified` columns + new pvl-p17e/p23d/p23e sub-todos + cross-reference (Phase 9) |

## Execution DAG

```
Phase 1 (launcher scripts)  ──┐
Phase 2 (preflight checklist)─┤
                              ├── Phase 3 (F18 2yr backtest) ──┐
                              │                                 │
Phase 4.A (Copper)         ───┤                                 │
Phase 4.B (perp testnets)  ───┤── PARALLEL ──────────────────── ├── Phase 6 (paper evidence ≥3d) ── Phase 8 (live dry-run) ── Phase 9 (master refresh)
Phase 4.C (Solana paper)   ───┤                                 │
Phase 4.D (Tenderly val)   ───┤                                 │
                              │                                 │
Phase 5.A (recon service)  ───┤                                 │
Phase 5.B (alert paging)   ───┤── PARALLEL ──────────────────── ┘
Phase 5.C (48h staging)    ───┤
Phase 5.D (live rehearsal) ───┘
                              │
Phase 7 (codex SSOTs)         │── runs alongside; codex updates ride with each phase per Post-Plan-Phase Codex Audit HARD RULE
```

QG gate between every phase; next phase cannot start until prior phase QG passes (per Citadel-Grade § 2).

## Phase 1 — Launcher script SSOT for paper + live VMs (P0, ~1d, SEQUENTIAL — gates everything)

**Why first**: Audit Block D2 + E3 + E7 all blocked on missing launchers. Per CLAUDE.md *"VM launcher script SSOT"* HARD RULE every gcloud / aws ec2 launcher MUST live under `deployment-service/scripts/vm/`. Without these, no compliant paper/live deployment exists.

- [ ] [AGENT] P0. **Write `deployment-service/scripts/vm/launch-strategy-paper-vm.sh`**.
  - VM-name pattern: `strategy-paper-{archetype}-{ts}` per CLAUDE.md VM Naming Convention.
  - Boots VM with `setup-data-pipeline-vm.sh` tarball mode (default; production path).
  - Boot script: `cd /opt/code/e2e-testing && bash scripts/defi/run-paper.sh --archetype $ARCHETYPE --candidate-version $CANDIDATE_VERSION --tick-interval 3600 --continuous`.
  - Singleton-locked per `(archetype, environment)` to prevent thundering herd (per CLAUDE.md *"Singleton-locked launchers"*).
  - Env required: `MANIFEST_PER_VM_SHARDS=true`, `VM_NAME=$VM_NAME`, `RUN_TS="$(date +%Y%m%d-%H%M%S)"`.
  - Done: launcher exists; smoke-launch with `--dry-run` returns valid gcloud command; smoke-launch with real `--mode paper` for 90s emits STARTED event in `gs://${PID}-events/events/strategy-service/...` partition.

- [ ] [AGENT] P0. **Write `deployment-service/scripts/vm/launch-strategy-live-vm.sh`**.
  - VM-name pattern: `strategy-live-{archetype}-{ts}`.
  - Same shape as paper launcher but invokes `run-live.sh` with `--mode live`.
  - **Additional pre-flight**: refuses launch if `--dry-run-live-cutover-passed` flag absent in launch metadata (forces operator to run Phase 8 dry-run before any real-capital launch).
  - Singleton-locked per `(archetype, environment)`.
  - Done: launcher exists; `--dry-run` returns valid command; pre-flight refuses launch without metadata flag.

- [ ] [AGENT] P0. **Register prefixes in `VM_PREFIX_TO_BUCKET`** at [`deployment-service/scripts/vm/vm_zombie_watchdog.py`](../../../deployment-service/scripts/vm/vm_zombie_watchdog.py).
  - Add `"strategy-paper-": None` (heartbeat-only — paper VMs don't write to a shard bucket).
  - Add `"strategy-live-": None` (same — live VMs emit events but don't write data shards).
  - Per CLAUDE.md: a VM whose prefix is not in the dict is invisible to the zombie watchdog.

- [ ] [SCRIPT] P0. **Bounce vm-zombie-watchdog VM** so it picks up the new prefixes.
  - `gcloud compute instances delete vm-zombie-watchdog-* --zone=asia-northeast1-c --quiet`
  - `bash deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh`
  - Per CLAUDE.md: running watchdog only fetches Python at boot.

- [ ] [SCRIPT] P0. **Smoke-launch each launcher** with `--dry-run` (printed gcloud command), then with `--mode paper` for ≥90s, then verify events.
  - Probe: `gcloud storage ls gs://${PID}-events/events/strategy-service/$(date +%Y-%m-%d)/strategy-paper-carry_staked_basis-*/` — directory exists with `hour=*` partition.
  - Read first JSONL, assert `event=="STARTED"`.
  - 10min recheck for new events with row counts (per CLAUDE.md *"No fire-and-forget VM launches"*).

**Phase 1 done definition** (per *"Plans Run To Actual Completion"* HARD RULE):
- ✅ Both launchers exist in `deployment-service/scripts/vm/` with the canonical shape.
- ✅ `VM_PREFIX_TO_BUCKET` includes both prefixes.
- ✅ vm-zombie-watchdog VM bounced; new instance running.
- ✅ Real paper-VM launched + STARTED + STOPPED events observed in event archive.

**Full-execution criterion**:
- **What ran**: `bash deployment-service/scripts/vm/launch-strategy-paper-vm.sh --archetype carry_staked_basis --tick-interval 3600 --continuous=false --max-runtime 300` on operator workstation; VM `strategy-paper-carry_staked_basis-<ts>` ran for 5 minutes then auto-shutdown.
- **Verification**:
  - `gcloud compute instances list --filter="name~strategy-paper-carry_staked_basis-"` showed RUNNING then absent.
  - `gcloud storage ls gs://${PID}-events/events/strategy-service/<today>/strategy-paper-carry_staked_basis-*/` returned `hour=*/` directories.
  - First JSONL = `event=="STARTED"`, last JSONL = `event in {"STOPPED","FAILED"}`.

**Phase 1 QG**: workspace QG runs clean on deployment-service. Launcher bash-syntax check passes (per `codex/05-infrastructure/launcher-script-ssot.md`).

## Phase 2 — Operator pre-flight checklist (P0, ~0.5d, SEQUENTIAL after Phase 1)

**Why**: Audit Block H6 + Block I1 step 8/9 — no pre-flight check exists today; operator improvises. Without this gate, the live cutover can launch with missing custody / missing API keys / unwired alerting and silently degrade.

- [ ] [AGENT] P0. **Write `e2e-testing/scripts/defi/preflight-cutover.sh`** that probes:
  - Copper credential present in Secret Manager + sandbox sign-test passes (HMAC handshake + poll loop completes).
  - All 6 perp venue API keys present in Secret Manager + read-write scope verified per venue (Bybit / Binance / OKX / Hyperliquid / Aster / Deribit).
  - Solana wallet funded with ≥0.01 SOL native gas (probe via RPC `getBalance`).
  - Tenderly fork seat available (probe Tenderly API).
  - All chain RPCs reachable (`eth_chainId` per chain in `CHAIN_RPC_TEMPLATES`).
  - Kill-switch YAML loaded + parses (`unified-trading-pm/configs/circuit_breaker_config.yaml`).
  - Alerting paging targets configured in Secret Manager (Telegram bot tokens, PagerDuty key — per Phase 5.B).
  - Composes with `plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md` credential matrix.
  - Done: each probe exits 0/1; aggregate report printed; refuses to exit 0 if any P0 probe fails.

- [ ] [AGENT] P0. **Update `e2e-testing/scripts/defi/run-paper.sh`** + **`run-live.sh`** to call `preflight-cutover.sh --mode paper` / `--mode live` as required pre-flight gate (refuses to start if pre-flight non-zero).

- [ ] [SCRIPT] P0. **Run preflight-cutover.sh on operator workstation** for both paper + live mode against carry_staked_basis. Resolve any failing probes by either fixing config OR explicitly waiving (write `--waive-<probe>` flag with operator-justification).

**Phase 2 done definition**:
- ✅ `preflight-cutover.sh` exists, all 8 probes implemented.
- ✅ `run-paper.sh` + `run-live.sh` invoke as required gate.
- ✅ Operator-run report shows all 8 probes green for paper + all 8 for live, OR explicit waivers documented.

**Full-execution criterion**:
- **What ran**: `bash e2e-testing/scripts/defi/preflight-cutover.sh --mode paper --archetype carry_staked_basis` on operator workstation.
- **Verification**: report shows 8 probes; all green OR each amber/red has documented waiver in commit message.

## Phase 3 — F18 2-year config-grid backtest run (P0, operator-action ~8-12h wall-clock, SEQUENTIAL after Phase 1)

**Why**: Audit Block A1 + master plan F18. 2-year backtest is operator-pending; informs the live-config selection. Path-drift fix gates this — without canonical PATH_REGISTRY adherence, results are invisible to downstream consumers.

- [ ] [AGENT] P0. **Resolve path drift**: pick `backtest_results/strategy_id={strategy_id}/run_id={run_id}/` (PATH_REGISTRY) as canonical. Update [`unified-trading-library/.../domain/execution_client.py:199-296`](../../../unified-trading-library/unified_trading_library/domain/execution_client.py#L199-L296) reader to honor PATH_REGISTRY (currently uses `backtest_results/{run_id}/` — silent mismatch). Migrate 2yr-grid script (`backtests/config_grid_2yr/{archetype}/{run_id}/`) to canonical OR keep separate sub-prefix `backtest_results/grid_2yr/{archetype}/{run_id}/`.

- [ ] [AGENT] P0. **Update `strategy-service/scripts/run_2yr_config_grid_backtest.py`** to:
  - Write to canonical PATH_REGISTRY path.
  - Emit `record_captured` manifest row per `(archetype, run_id, asset_group)` per CLAUDE.md *"Honest absence vs fake placeholders"* HARD RULE.
  - Validate `GroupBMetrics` schema on output rows (4-pillar gate per CLAUDE.md "Cluster validation MANDATORY at `record_captured`").
  - Honor `--candidate-emit` flag that auto-promotes top-K results to `ConfigRegistry` for paper-mode pickup.

- [ ] [SCRIPT] P0. **Operator runs the 2yr backtest** for both archetypes:
  - `bash strategy-service/scripts/run_2yr_config_grid_backtest.py --archetype carry_staked_basis --candidate-emit --top-k 3` (background, ~6h)
  - `bash strategy-service/scripts/run_2yr_config_grid_backtest.py --archetype "ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion" --candidate-emit --top-k 3` (background, ~6h, parallel)
  - Operator inspects ranking output + picks lead config for each archetype + records `candidate_version` in plan completion notes.

**Phase 3 done definition**:
- ✅ Path drift resolved + reader updated.
- ✅ 2yr backtest runs landed; each archetype has 3 candidate configs ranked by Sharpe + max_drawdown.
- ✅ `candidate_version` recorded for each archetype.

**Full-execution criterion**:
- **What ran**: 2 background runs, each ~6h, on operator workstation OR a long-running GCE VM `strategy-backtest-2yr-{ts}`.
- **Verification**: `gcloud storage ls gs://${PID}-config/backtest_results/strategy_id=carry_staked_basis/run_id=*/` returns parquet files; sample-inspect parquet shows non-NaN rows; manifest has `record_captured` rows for both archetypes.

## Phase 4 — Custody + perp testnet hardening (P0, ~2-3d, PARALLEL sub-phases, SEQUENTIAL after Phase 1)

### 4.A — F19 Copper sub-account provisioned + first live-signing dry-run

- [ ] [SCRIPT] P0. **Operator provisions Copper sub-account** for the May-23 cutover wallet (testnet first).
- [ ] [SCRIPT] P0. **First live-signing dry-run** via [`execution-service/execution_service/custody/copper.py`](../../../execution-service/execution_service/custody/copper.py) HMAC-SHA256 sign + poll loop on testnet.
  - Probe: signed transaction returned within poll-interval; on-chain confirmation observed.
- [ ] [AGENT] P0. **Verify CEFFU stays STUB-status with explicit doc** in `codex/04-architecture/custody-providers.md` (per master plan Q&A 3 deferral). Manual handoff procedure for Binance flows documented.

### 4.B — pvl-p20b 5 perp venue testnet wiring

- [ ] [AGENT] P0. **Audit current testnet support** for Bybit / Binance / OKX / Hyperliquid / Aster in `execution-service/execution_service/venues/initializer.py` + `execution-service/execution_service/defi_execution/connectors/cefi_base.py`.
- [ ] [AGENT] P0. **Implement testnet-mode constructor** for each missing venue. Pattern: `--testnet` flag → swap base URL + use testnet-scoped credentials from Secret Manager `paper/<venue>/<env>` namespace.
- [ ] [SCRIPT] P0. **Smoke-test each testnet** with read-only API call (e.g. `get_account_info`) to verify credential + endpoint pair.

### 4.C — pvl-p20c Solana paper analogue

- [ ] [AGENT] P0. **Implement Solana devnet wiring** for LST archetypes (jitoSOL/mSOL/bSOL).
  - Pyth Hermes for prices (per CLAUDE.md unbanned 2026-05-06).
  - Solana devnet RPC URL in `CHAIN_RPC_TEMPLATES`.
  - Devnet wallet provisioning via standard CLI.
- [ ] [SCRIPT] P0. **Smoke-test Solana paper** by running `colocated_engine.py --strategy-id carry_staked_basis --execution-provider solana_devnet` for 10min.

### 4.D — Tenderly fork validated end-to-end for `carry_staked_basis`

- [ ] [SCRIPT] P0. **Tenderly fork dry-run** for carry_staked_basis lead archetype on EVM side (Aave staking + perp short hedge).
  - Verify mock fills produce expected P&L decomposition.

**Phase 4 done definition**:
- ✅ Copper sub-account provisioned + first live-signing succeeded on testnet.
- ✅ All 5 perp venue testnets reachable + sign-readable.
- ✅ Solana devnet wiring works end-to-end for LST archetypes.
- ✅ Tenderly fork validated for carry_staked_basis EVM legs.

**Full-execution criterion**:
- **What ran**: 4 parallel sub-phase verification commands; outputs captured in plan completion notes.
- **Verification**: per-sub-phase probe outputs preserved in `plans/active/issues/` if any failed.

## Phase 5 — Reconciliation + alerting wire-up (P0, ~2-3d, PARALLEL with Phase 4)

### 5.A — F21 batch-live-reconciliation-service minimum-viable shipment

- [ ] [AGENT] P0. **Stand up `batch-live-reconciliation-service`** as a Cloud Run service (or GCE cron VM `batch-live-recon-{ts}`).
  - Reads batch backtest output (PATH_REGISTRY canonical) + live event-stream paper/live runs.
  - Computes per-archetype P&L diff + per-trade fill comparison.
  - Emits `BATCH_LIVE_RECON_DRIFT` event when drift > 5bps.
  - Daily cadence; alerting rule wires to Telegram + PagerDuty.
- [ ] [AGENT] P0. **Wire UTL `batch_live_reconciler` helper** ([`UTL@908b1647`](../../../unified-trading-library/unified_trading_library/batch_live_reconciler.py)) into the new service.
- [ ] [SCRIPT] P0. **First recon dry-run** against carry_staked_basis paper run.

### 5.B — F22 Phase 4 alerting paging-target Secret Manager wiring

- [ ] [SCRIPT] P0. **Provision Telegram bot tokens** for the May-23 alerting channel.
- [ ] [SCRIPT] P0. **Provision PagerDuty integration key** (or skip if Telegram-only for cutover).
- [ ] [AGENT] P0. **Update `alerting-service/alerting_service/notifiers/router.py`** to read paging targets from Secret Manager paths defined in master plan F22 spec.

### 5.C — F22 Phase 7 quietness 48h staging dry-run

- [ ] [SCRIPT] P0. **Run alerting-service in staging** for 48h continuous; verify zero false-positive pages.

### 5.D — F22 Phase 8 live rehearsal

- [ ] [SCRIPT] P0. **Live rehearsal** — run alerting-service against carry_staked_basis paper run for 24h; verify alerts fire correctly on synthetic kill-switch trip.

**Phase 5 done definition**:
- ✅ batch-live-recon-service running, daily cadence, drift alerts wired.
- ✅ Alerting paging targets in Secret Manager + router reads them.
- ✅ 48h staging dry-run quiet.
- ✅ Live rehearsal alert fired correctly on synthetic trip.

**Full-execution criterion**: per-sub-phase verification commands captured in plan notes; all 4 green.

## Phase 6 — Paper-mode evidence run (P0, operator-monitored ≥3 continuous days, SEQUENTIAL after Phase 3 + 4 + 5)

**Why**: Audit Block I1 step 6 + master plan `pvl-p18a`. Without ≥3d paper evidence on the lead pair, no live promotion can be operator-justified.

- [ ] [SCRIPT] P0. **Launch paper VM** for carry_staked_basis with the candidate config selected in Phase 3.
  - `bash deployment-service/scripts/vm/launch-strategy-paper-vm.sh --archetype carry_staked_basis --candidate-version <version>`.
- [ ] [SCRIPT] P0. **Launch paper VM** for ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion with its candidate config.
- [ ] [SCRIPT] P0. **Monitor for ≥3 continuous days**:
  - Daily event-stream verification (STARTED + per-tick progress events + per-fill events).
  - Daily reconciliation report green from Phase 5.A service.
  - No `STRATEGY_PAPER_FAILED` (when event type ships) OR equivalent stale-data signal.
  - Per CLAUDE.md *"No fire-and-forget VM launches"* — active verification protocol.

**Phase 6 done definition**:
- ✅ Both archetypes ran paper-mode for ≥3 continuous days (target ≥7 for the May-23 cutover; ≥3 is the gate to unlock Phase 8 live dry-run).
- ✅ Per-day event-archive confirmation.
- ✅ Per-day recon report shows drift within tolerance.
- ✅ No silent failures.

**Full-execution criterion**:
- **What ran**: 2 paper VMs running for ≥72h continuous each, with operator-checked event streams.
- **Verification**: `gcloud storage ls gs://${PID}-events/events/strategy-service/` shows continuous JSONL files for the full run; manifest has per-tick captured rows.

## Phase 7 — Codex SSOTs (May-23 subset, P0, runs alongside per Post-Plan-Phase Codex Audit HARD RULE)

These codex docs ride with the phases that produce them — NOT batched at plan-end.

- [ ] [AGENT] P0. **NEW** `codex/09-strategy/operational/cli-promote-paths.md` — `run-paper.sh` + `run-live.sh` as May-23 SSOT path; per-mode operator pre-flight checklist; ships with Phase 2.
- [ ] [AGENT] P0. **NEW** `codex/04-architecture/promote-workflow-architecture.md` (May-23 section only — operator-CLI path; full UI section deferred to post-cutover plan); ships with Phase 7.
- [ ] [AGENT] P0. **NEW** `codex/05-infrastructure/strategy-vm-launcher-shape.md` — paper-VM + live-VM launcher convention; ships with Phase 1.
- [ ] [AGENT] P0. **UPDATE** `codex/04-architecture/custody-providers.md` — populate Copper operational verification result; CEFFU subsections explicitly DEFERRED with named successor (post-cutover plan); ships with Phase 4.A.
- [ ] [AGENT] P0. **UPDATE** `codex/05-infrastructure/launcher-script-ssot.md` — add strategy-paper / strategy-live launcher patterns; ships with Phase 1.
- [ ] [AGENT] P0. **UPDATE** CLAUDE.md — add **"Promote Workflow Path"** key rule:
  - "May-23 cutover = operator-CLI via `e2e-testing/scripts/defi/run-paper.sh` + `run-live.sh` + `colocated_engine.py`. UI-driven workflow ships post-cutover per `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`. Do NOT attempt to wire the Promote UI's `onPromote` callback to a backend before May-23 — there is no backend to wire to and the May-23 critical path doesn't need it."
  - Cross-reference the May-23 cutover plan + post-cutover plan + question doc.

## Phase 8 — Live cutover dry-run (P0, operator-action, SEQUENTIAL after Phase 6)

**Why**: Audit Block I1 step 8. Verify all 9 reality-check steps pass for the lead archetype before any real-capital launch.

- [ ] [SCRIPT] P0. **`run-live.sh --dry-run`** with carry_staked_basis lead archetype.
  - No actual fills.
  - Real wallet handshake (Copper sign request, but no broadcast).
  - Real venue handshake (auth + balance check, no order submit).
  - Real custody handshake.
  - Verify all 9 reality-check steps from Block I1 now pass for the lead archetype.
- [ ] [SCRIPT] P0. **Set the `--dry-run-live-cutover-passed` flag** in launch metadata so live launcher accepts subsequent real-mode launches.

**Phase 8 done definition**:
- ✅ Dry-run completes without error.
- ✅ All 9 I1 reality-check steps pass.
- ✅ Launch metadata flag set.

**Full-execution criterion**:
- **What ran**: `bash e2e-testing/scripts/defi/run-live.sh --dry-run --archetype carry_staked_basis` on operator workstation.
- **Verification**: dry-run report shows green per step; flag persisted to GCS metadata bucket.

## Phase 9 — Master plan refresh (P0, ~0.5d, SEQUENTIAL after Phase 8)

- [ ] [AGENT] P0. **Update `plans/active/master_to_live_defi_2026_05_23.md`**:
  - Refresh `Last verified` columns for F17/F18/F19/F20/F21/F22/G23 with actual completion dates.
  - Add new sub-todos under Group F:
    - `pvl-p17e-launcher-scripts` — DONE per Phase 1.
    - `pvl-p23d-promote-api-and-preflight` — DEFERRED to post-cutover plan.
    - `pvl-p23e-live-deployment-events` — DEFERRED to post-cutover plan.
  - Add cross-reference to this plan + post-cutover plan in master plan body (Group F + G sections).

- [ ] [AGENT] P0. **Update CLAUDE.md "Master Plan Continuous-Verification Column"** — verify the new continuous-verification rows for F17/F18/F19/F20/F21/F22/G23 reference the actual cron / Tab / QG that runs between checkpoints (per Master Plan Continuous-Verification Column HARD RULE).

## Phase 10 — Live cutover go (P0, operator-action, SEQUENTIAL after Phase 9)

- [ ] [SCRIPT] P0. **Operator launches LIVE** for both archetypes:
  - `bash deployment-service/scripts/vm/launch-strategy-live-vm.sh --archetype carry_staked_basis --candidate-version <version>`
  - `bash deployment-service/scripts/vm/launch-strategy-live-vm.sh --archetype "ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion" --candidate-version <version>`
- [ ] [SCRIPT] P0. **DART manual-trade window — first 3 days**: operator-monitored every trade signal (per master plan G23 + line 1292 design). Operator-confirms each trade via existing CLI; full UI manual-trade gate is post-cutover.
- [ ] [SCRIPT] P0. **Day 4-7+ automation**: kill-switch + DART pause/override available; automation enabled for fills.
- [ ] [SCRIPT] P0. **Continuous monitoring**: daily reconciliation report; daily event-archive verification; alerting on-call.

**Phase 10 done definition**:
- ✅ Both archetypes in LIVE_RUNNING for ≥7 continuous days by 2026-05-23.
- ✅ Service-readiness checklist Group F items 17-22 + G item 23 green for both.
- ✅ Question doc `plans/questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md` flips status `iterating → closed` (first end-to-end run shipped).

**Full-execution criterion**:
- **What ran**: 2 live VMs running ≥7 continuous days; operator-confirmed trades for first 3 days; automated for days 4-7+.
- **Verification**: continuous event-archive presence; per-day reconciliation green; live P&L attribution captured per-archetype; no kill-switch trips OR all trips diagnosed + resolved within SLA.

## Done definition (overall plan)

- ✅ All 10 phases completed.
- ✅ May-23 cutover live with both archetypes ≥7 continuous days.
- ✅ Master plan readiness matrix refreshed.
- ✅ All 5 NEW codex docs shipped + 3 UPDATE codex docs reflect actual state.
- ✅ CLAUDE.md "Promote Workflow Path" key rule added.
- ✅ Question doc closes (status: closed).

**Full-execution criterion (overall)**:
- **What ran**: end-to-end live cutover for May-23 lead pair via the hardened operator-CLI path.
- **Verification**: full event-archive trail from backtest → candidate → paper → live cutover for both archetypes; recon green per-day; P&L attribution captured.

## Temporary states + canonical follow-up plans

- **Promote UI mock-only**: deferred to `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`. Operator-CLI is May-23 path.
- **CEFFU custody STUB**: deferred per master plan Q&A 3. Post-cutover plan picks up if Binance institutional flow opens.
- **4 lifecycle SSOTs not consolidated**: deferred to post-cutover plan Phase 1 (state-machine consolidation).
- **`StrategyVersion` provenance enrichment** (pinned shas + model refs): deferred to post-cutover plan Phase 2 (`CandidateManifest` UAC type).
- **Promote / candidate / lifecycle-pause events not in UAC**: deferred to post-cutover plan Phase 3 (event taxonomy consolidation).
- **Per-archetype Pydantic config schemas (G2 — only 5 of 53 seeded)**: deferred to post-cutover plan Phase 4.
- **Drift detection**: deferred to post-cutover plan Phase 5.
- **Cross-service auto-registration on promote (H1-H3)**: deferred to post-cutover plan Phase 6.
- **Continuous backtest cron**: deferred to post-cutover plan Phase 7.
- **Multi-tenant client-id flow (H4)**: deferred to Tier 3 post-launch.

## Composes with

- CLAUDE.md "Plans Run To Actual Completion" — every phase has Full-execution criterion.
- CLAUDE.md "No fire-and-forget VM launches" — every VM in this plan has paired event-verification.
- CLAUDE.md "VM launcher script SSOT" — Phase 1 ships launchers in canonical location.
- CLAUDE.md "Singleton-locked launchers" — paper + live launchers per-archetype singleton-locked.
- CLAUDE.md "Master Plan Continuous-Verification Column" — Phase 9 refresh.
- CLAUDE.md "Post-Plan-Phase Codex Audit" — Phase 7 codex docs ride with their phases.
- CLAUDE.md "Citadel-Grade Planning Standards" — pre-audit + phased DAG + parallelization + success criteria + downstream consumer updates + SSOT discipline.
- `plans/active/master_to_live_defi_2026_05_23.md` — this plan executes the Group F/G live-only items.
- `plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md` — Phase 2 pre-flight composes with credential matrix.
- `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md` — companion plan for everything deferred.
