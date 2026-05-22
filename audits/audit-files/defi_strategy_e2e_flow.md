---
title: "DeFi strategy e2e flow — lifecycle map (client registration → trading → reporting)"
type: reference / lifecycle-map
created: 2026-05-21
status: baseline agreed 2026-05-21 (Harsh + Claude Opus 4.7)
companion_to: audit_03_defi_archetypes_e2e.md
principle: >
  Navigation aid — narrative + SSOT pointers, NOT a restatement of values. For any specific number/threshold, follow the
  pointer to its SSOT to avoid doc drift. Bookends (onboarding, reporting) confirmed via codex sweep 2026-05-21; verify
  against code when the matching ONB-*/RPT-* checkpoints are walked.
---

# DeFi strategy e2e flow — lifecycle map

Worked example: **`carry_staked_basis`** (lead May-23 archetype). `arbitrage_price_dispersion` (APD) deltas noted
inline. Each stage cites its SSOT; bracketed `[IDs]` are the AUDIT-03 checkpoints that verify it.

```
A. onboarding ─▶ B. deploy ─▶ C. data→signal ─▶ D. risk→execution ─▶ E. monitor→P&L→report
```

## A · Onboarding → a client exists

1. **Prospect → approved user.** `/questionnaire` (Firestore) → operator approves at `/admin/organizations/[id]` →
   Firebase Auth user + `/users/{uid}`. Sales funnel; no capital moves. SSOT: `codex/08-workflows/client-onboarding.md`.
2. **`ClientConfig`** created in UAC (`internal/client_config.py`): `client_id`, `share_class` (USDC for carry),
   `categories_enabled`, `max_total_notional_usd`, `max_drawdown_pct`. Entity stack: Elysium (Ireland AIFM) → POD (DeFi
   sub) → BVI Fund. SSOT: `codex/04-architecture/client-config-and-risk-dimensions.md`. ⚠ doc-drift vs CLAUDE.md "Odum
   UK + Cayman" — finding **F-06**. [ONB-01, ONB-07]
3. **Capital + per-client risk limits** → `clients.yaml` (per archetype × shard); wallet hierarchy = treasury (20%) +
   hot (80%). SSOT: `codex/04-architecture/{per-client-isolation-architecture,wallet-hierarchy-and-capital-flow}.md`.
   [ONB-02]
4. **Wallet provisioning** → `wallet_provisioning.json` in GCS; `signing_surface` selects custody (config-only flip).
   May-23 = `CLOUD_KMS_ENCRYPTED`; Copper/CEFFU is June-1 (CEFFU stub today, KD-07). SSOT:
   `codex/04-architecture/custody-providers.md`. [ONB-03, ONB-04, CUS-01]

## B · Config → a running strategy

5. **Slots** generated from the `venue_collateral` matrix → carry = 4 (jito-drift, marinade-drift, lido-deribit,
   lido-bybit). `CarryStakedBasisRankAllocator` weights capital across them. SSOT: carry-staked-basis.md §Catalog /
   §rank allocator. [CSB-15, CSB-17]
6. **Promote** `paper_1d → live_early`. CLI primary: `run-paper.sh → colocated_engine.py → run-live.sh`; UI secondary:
   Promote → `POST /api/promote` → manifest → VM auto-launch. SSOT:
   `codex/04-architecture/promote-workflow-architecture.md`. [CUT-11]
7. **Runtime topology**: `StrategySupervisor` (per archetype × shard VM) → `ClientAdmissionController` spawns one
   `ClientWorker` per `client_id` (spawn, not fork) → preflight (KMS creds → venue auth → balance) → `CLIENT_READY`.
   SSOT: per-client-isolation-architecture.md. [ONB-05, ONB-06, ALC-04]

## C · Data → signal

8. **Pipeline**: instruments-service → MTDS (`lst_rates`, funding via `derivative_ticker`, `dex_pools`,
   `lending_indices`) → features-onchain (`staking_apy_total`, `health_factor`) + features-delta-one (`funding_oi`).
   Honest-coverage gated; batch = live. SSOT: §2.9 DATA-_ + codex 02-data. [DATA-01…10, PIPE-_]
9. **Signal**: engine `on_tick` computes net carry = `staking_apy_total + funding_apy − fees`; if `> entry_bps` →
   `AtomicInstruction` (`LEADER_HEDGE`); returns `[]` if a required feature is missing. APD: emits when cross-venue
   dispersion clears its threshold (`_on_tick` / `_on_tick_funding_rate_dispersion`). SSOT: staked_basis.py /
   price_dispersion.py. [CSB-04/06/14, APD-04/05]

## D · Risk → execution

10. **4-layer pre-flight**: L1 strategy self-check → L2 risk-and-exposure (veto blocks L3+L4) → L3 execution pre-trade →
    L4 venue. `min_health_factor` (1.25) + kill-switch checked. SSOT: risk-gates.md / kill-switch-circuit-breaker.md.
    [RSK-06, CSB-12]
11. **Execution**: legs SWAP(USDC→ETH) → STAKE(→LST) → TRANSFER(→perp margin) → TRADE(short perp); sign via CLOUD_KMS;
    MEV (Flashbots ≥$10k ETH / Jito Solana); slippage guard; `CLOSE_LEADER_IF_HEDGE_FAILS` unwind → fills. SSOT:
    defi-execution-overview.md. [CSB-03/10/11, EXE-*]

## E · Monitor → P&L → report

12. **Monitor**: PBMS positions; recon-freshness gate; circuit breakers + 5-level kill-switch; scenario trips (stETH
    depeg 5% → kill archetype ≤30s); rebalance on peg-drift / funding flip. SSOT: kill-switch-circuit-breaker.md.
    [RSK-01…12]
13. **P&L**: per-factor/per-layer `PnLAttributionRow` (carry = CARRY_BASE + AVS + seasonal − reward-slippage − gas); T+1
    batch recon 02:00 UTC, batch overrides live. SSOT: pnl-attribution.md / restaking-reward-economics.md. [PNL-*]
14. **Report**: client-facing `client-reporting-api` → `ClientReportingTab` (NAV/P&L/attribution) from
    `client-reports/{client_id}/{archetype}/{date}/attribution.parquet`; operator-facing DART 3-way +
    `ManualTradeGateDialog` (first 3 days) + deployment-ui; audit = append-only GCS `audit/` + events JSONL. SSOT:
    client-reporting-architecture.md / dart/mode-toggle.md / audit-logging.md. [RPT-*]

## Reality check — design ≠ code

Open divergences (documented design ≠ running code) are filed in
`audit-results/runs/AUDIT-03_2026_05_21_phase0_design_review.md` (findings F-01…F-06) + indexed in the audit doc §6.
Already-tracked deferrals/gaps (not re-filed): KD-01 (legs hand-built), KD-07 (CEFFU stub), GAP-01 (usdc_idle_yield),
GAP-04 (ASTER ticker), GAP-08 (per-account health_factor).
