---
scope: [engineer, admin]
---

# CLI Promote Paths — May-23 SSOT

> **Scope**: May-23 subset only. Post-cutover Phase 2 extends with full pinned-shas CandidateManifest + cross-service
> auto-registration.
>
> SSOT: `plans/active/promote_workflow_may23_cli_path_2026_05_10.md` § Phase 2

---

## Overview

May-23 cutover ships on **dual-track promote**:

| Track              | Path                                                                 | Trigger                             |
| ------------------ | -------------------------------------------------------------------- | ----------------------------------- |
| **PRIMARY** (CLI)  | `run-paper.sh` → `colocated_engine.py` → `run-live.sh`               | Operator-initiated from workstation |
| **SECONDARY** (UI) | Promote button → POST `/promote/{id}/{manifest_id}` → VM auto-launch | Browser-driven via UTS-UI           |

Both tracks produce the same operational outcome: a strategy VM running in `paper` or `live` mode, emitting events to
the event archive.

---

## CLI Track Scripts

### `run-paper.sh` — Paper Trading

**Location**: `e2e-testing/scripts/defi/run-paper.sh`

**What it does**: creates a Tenderly fork of mainnet, runs real smart contract calls with live data. No money at risk.
Real slippage + real gas from EVM math.

```bash
# Single strategy
bash e2e-testing/scripts/defi/run-paper.sh --strategy carry_staked_basis

# All DeFi strategies
bash e2e-testing/scripts/defi/run-paper.sh --asset-group defi

# Continuous mode (1h tick interval)
bash e2e-testing/scripts/defi/run-paper.sh --strategy carry_staked_basis --continuous
```

**Pre-flight gate**: calls `preflight-cutover.sh` automatically unless `--skip-preflight` is passed (DANGEROUS —
requires operator justification).

**Required env**:

- `TENDERLY_API_KEY` — Secret Manager or local env
- `CLOUD_PROVIDER` / GCP credentials for VM launch

### `run-live.sh` — Live Trading

**Location**: `e2e-testing/scripts/defi/run-live.sh`

**What it does**: promotes a paper-validated strategy to live capital deployment. Triggers `launch-strategy-live-vm.sh`
via deployment-service.

```bash
bash e2e-testing/scripts/defi/run-live.sh --strategy carry_staked_basis
```

**Gate**: requires paper trading to have passed ≥7d without P&L breach. Script checks `preflight-cutover.sh` live-mode
probes before launching.

**Required env**:

- `CLOUD_KMS_KEY_URI` — envelope key for `CLOUD_KMS_ENCRYPTED` custody (May-23)
- `PRIVATE_KEY_SECRET_REF` — wrapped private key in Secret Manager
- Strategy MUST be in `PAPER_1D` or `LIVE_EARLY` maturity phase in strategy-service

### `colocated_engine.py` — Paper Mode Entry Point

**Location**: `e2e-testing/scripts/defi/colocated_engine.py`

Directly invocable for a single strategy run without VM scaffolding. Useful for local debugging and CI smoke tests.

```bash
python3 e2e-testing/scripts/defi/colocated_engine.py \
    --strategy carry_staked_basis \
    --mode paper \
    --asset-group defi
```

---

## Per-Mode Operator Pre-Flight Checklist

### Before `run-paper.sh`

- [ ] `preflight-cutover.sh` green (all probes pass or explicitly waived)
- [ ] Tenderly API key provisioned (`TENDERLY_API_KEY`)
- [ ] Strategy config validated (`carry_staked_basis` / `arbitrage_price_dispersion`)
- [ ] Event archive reachable (GCP PubSub + GCS)
- [ ] Manifest row exists in `strategy_candidate_manifests` Firestore collection

### Before `run-live.sh`

All paper checks above, PLUS:

- [ ] Paper trading ran ≥7d with Sharpe > backtest threshold (from Phase 3 backtest)
- [ ] `CLOUD_KMS_ENCRYPTED` key provisioned + `PRIVATE_KEY_SECRET_REF` set
- [ ] Kill-switch YAML present (`codex/04-architecture/kill-switch-circuit-breaker.md`)
- [ ] `ManualTradeGateDialog` enabled in DART terminal for first 3 trading days
- [ ] Recon endpoint green (`/recon` probe in `preflight-cutover.sh`)
- [ ] Copper MPC sub-account provisioned (June-1 flip; May-23 uses KMS)

---

## VM Launcher Convention

Paper and live strategy VMs are launched via:

| Script                                                      | VM prefix         | Mode                  |
| ----------------------------------------------------------- | ----------------- | --------------------- |
| `deployment-service/scripts/vm/launch-strategy-paper-vm.sh` | `strategy-paper-` | Paper (Tenderly fork) |
| `deployment-service/scripts/vm/launch-strategy-live-vm.sh`  | `strategy-live-`  | Live (real capital)   |

Both launchers: emit STARTED within 60s + emit ≥1 progress event/hour + emit STOPPED/FAILED at exit. Fire-and-forget is
banned.

Full shape spec: `codex/05-infrastructure/strategy-vm-launcher-shape.md`.

---

## Post-Cutover Extensions (NOT May-23 scope)

- Full `CandidateManifest` with pinned shas / model refs / features manifest version
- Cross-service auto-registration on Promote button press
- UI-primary track without CLI fallback
- Firebase `execution-full` enforcement at backend (currently at UI layer only)

Successor plan: `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`
