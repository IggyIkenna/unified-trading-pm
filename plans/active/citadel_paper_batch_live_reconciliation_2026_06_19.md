---
doc_type: plan
title: Citadel-grade Paper ⟷ Batch ⟷ Live Reconciliation — the Determinism Spine
summary:
  Implement the determinism spine ensuring paper(W)==batch-rerun(W) trade-for-trade, with full reconciliation across
  paper/batch/live trading modes.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
  ]
scope: [engineer, admin]
tags: [reconciliation, paper-trading, batch, live, determinism, ledger, pnl]
related:
  [
    plans/epics/batch_live_symmetry_master.md,
    plans/epics/global_ledger_pnl_attribution_master.md,
    plans/active/global_ledger_pnl_attribution_migration_2026_06_01.md,
    plans/active/crypto_alpha_research_2026_07_24.md,
    plans/archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08.md,
    plans/archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08_finalize.md,
  ]
created: 2026-06-19
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 48
estimate_calibrated_ai_days: 38
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  2026-07-24: operator-approved unlock + extract per plan_line_cap_remediation_2026_07_23.md (row 5 / bucket-d detail) —
  the alpha-research + paper-trading-POC track (§C of the register below + the standalone e2e-testing paper-trading POC
  Progress Log section, ~35 todos) moved verbatim to plans/active/crypto_alpha_research_2026_07_24.md, per this plan's
  own 2026-06-23 migration proposal (§C) which was never executed until now. `locked_by: live-defi-rollout` cleared as
  part of this same operator-approved action.
assigned_role: backend_engineer
drift_direction: advance-code
Codex SSOTs:
  [
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /codex/04-architecture/global-ledger-architecture.md,
    /codex/02-data/pipeline-mode-and-batch-live-reconciliation.md,
    /codex/09-strategy/operational/batch-live-reconciliation-threshold-calibration.md,
  ]
context_scope:
  [
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /codex/04-architecture/global-ledger-architecture.md,
    /plans/epics/batch_live_symmetry_master.md,
    batch-live-reconciliation-service/batch_live_reconciliation_service/engine/,
    batch-live-reconciliation-service/batch_live_reconciliation_service/stages/stage5_results_writer.py,
  ]
---

# Citadel-grade Paper ⟷ Batch ⟷ Live Reconciliation

> **Design SSOT**: `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` (full architecture +
> EXISTS/MISSING map). This plan is the **phased execution DAG**. Read the SSOT first — do not act from this summary.

## The thesis (operator, 2026-06-19)

The three trading modes are **the same program**. `paper(W)` must equal `batch-rerun(W)` **trade-for-trade** (same
code + same inputs + same fill model); the **only** intentional divergence is real venue fills at the LIVE boundary. So:

```
live − batch = (paper − batch)      + (live − paper)
                └ determinism ≈ 0 ┘   └ execution alpha ┘
                   a BUG if not 0       the measurement
```

The paper↔batch reconciliation is a **determinism PROOF** (ε=0, any diff is a bug), not a tolerance check.
"Citadel-grade paper trading" = the complete as-if-filled state: all money movements, balances (per
venue/instrument/share_class), P&L, PnL attribution, venues + instruments breakdown — held in four ledgers
(`InstructionLedger` historical tape + `PositionLedger` as-if-filled state + `PassiveLedger` accruals + `PricingLedger`
marks), eyeball-able + Slack-summarised.

> **[2026-07-14 note, verify-rerun-2 finding 208]**: this "four ledgers" list names `PositionLedger` as one of the four
> — but the OWNING epic for the canonical ledger architecture,
> [`plans/epics/global_ledger_pnl_attribution_master.md`](../epics/global_ledger_pnl_attribution_master.md), defines the
> canonical **"Four SSOT ledgers"** as **Instruction / Passive / Treasury / Pricing**, explicitly classifying Position
> as a _derived materialised view_ (computed FROM the SSOT ledgers), not one of the four SSOT ledgers itself —
> consistent with this very plan's own P3.3 description of `PositionLedger` as a "materialiser (avg-cost P&L)" that
> derives from `InstructionLedger` fills. This plan also already ships Treasury/TransferLedger emission (P2, "PRODUCER
> DONE — Real cross-venue transfers / money-movements: emit Treasury/TransferLedger…", line ~493), so the epic's
> Instruction/Passive/Treasury/Pricing framing is not in tension with anything actually built here — only with this
> informal summary's word choice. Treat the epic's naming as authoritative for "the four SSOT ledgers"; `Position` here
> is correctly one of the plan's deliverables, just not an SSOT ledger in the epic's taxonomy.

## The five gaps (design targets — see SSOT §3)

- **G1** — THREE divergent fill models (APY-haircut / `BenchmarkFillEngine` / `PaperMatchingEngine`); paper and batch
  use different fill code. **This is the "paper sim ≠ batch sim" bug the operator named.**
- **G2** — no per-trade identity in execution events (date-level float-metric dicts; no order_id/instrument_key/ts).
- **G3** — ledgers unmaterialised (no `PositionLedger` writer, no `InstructionLedger`-from-fills, no `PassiveLedger`
  synth, `realized_pnl` hardcoded `"0.00"`, balances from CCXT not `Σ delta`).
- **G4** — no point-in-time input capture / as-of run manifest (a rerun may read revised data → spurious diff).
- **G5** — recon is aggregate (`abs(mean_a−mean_b)`) + single-date; no trade-by-trade keyed diff, no daily-T+1
  trade-level recon, no determinism verdict.

## Pre-audit before execution (Citadel standard §1)

Before Phase 1, grep every consumer of: `BenchmarkFillEngine`, `PaperMatchingEngine`, `run_2yr_config_grid_backtest`,
the colocated_engine fill providers, the execution-service event-emission format, `compute_pnl_breakdown`,
`client-reporting-api` positions/pnl routes, and `batch-live-reconciliation-service` stage 3b/3c — embed the manifest in
this plan before changing a fill or event shape. (Phase 0 item P0.0.)

## Foundation-completion-gate ordering (Citadel standard §8)

Layered, each GREEN-audited before the next: **Phase 0 (contract) → Phase 1 (one fill model) → Phase 2 (trade identity)
→ Phase 3 (ledger materialisation) → Phase 4 (recon harness) → Phase 5 (views) → Phase 6 (Slack) → Phase 7 (the 19→26
dry-run)**. Phases 1–3 are the foundation; the harness (4) is meaningless until the fill model is unified (1) and trades
are identified (2) and the ledger exists (3).

---

## Remaining-work register + operator gating (cleaned 2026-06-23)

> **Phases 0-1, 3-11 shipped; Phase 2 (live execution-event + colocated_engine trade-keying, P2.1/P2.2) remains OPEN.**
> (was: "Phases 0-11 fully DONE …" — the paper↔batch determinism + monitoring SPINE claim. Corrected 2026-07-12 per
> operator ruling, plan-reconciliation finding 15/365/17 — see
> `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2.) Phase 11 is the last phase (no P12).
> The ε=0 PROOF engine, the four ledgers, the recon harness, the Slack digest, the monitoring dashboard, the
> deployment-api-SSOT reconcile (P11.21), the synthetic-seam guard (P11.17), the Group-C smart-fill replay (P11.6,
> `execution-service@3d7d760c`) and the drivable-but-thin threshold (P11.22) all shipped. **89 boxes done / remaining
> open boxes are classified below** (incl. Phase 2's P2.1/P2.2). This register is an INDEX of the open `- [ ]` items in
> the phases below — it adds no new dispatches; the canonical todos stay in-phase. **UPDATE 2026-08-08**: 7 of the
> register's § A items (incl. P2.1/P2.2) had their canonical `- [ ]` checkboxes MOVED to
> `citadel_satellite_ao_dispatch_batch1_2026_08_08.md` (operator-authorized extraction) — the phases below now carry
> non-ingestable pointer lines for those 7, not the live checkbox. The 3 items still tracked here as real open
> checkboxes are P2.7.3 (operator-gated), P9.2 (dependency-blocked), and P2.11.15 (held back on a conflict-check
> duplicate-claim finding — see register § A).

**A — Agent-shippable infra/code (NO operator gate — a VM/agent can ship these) — EXTRACTED 2026-08-08:**

> **EXTRACTED 2026-08-08**: 7 of this section's items (trade_key/fill-record identity P2.1/P2.2, the GroupC smart-fill
> paper-run handoff P1.6, BTC-trend feature corpus recompute P2.11.16, TSMOM_BTC_CTA capability-manifest wiring
> P2.11.20, the intraday mean-reversion ML feature P2.11.18 [scope-trimmed — its retrain sub-step stays here, see
> below], and the UI run-selector bug P2.14) moved verbatim to
> [`plans/archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08.md`](/plans/archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08.md)
> — operator-authorized extraction, per that plan's own `source:` for the authorization. See that plan (+ its finalize
> twin, `citadel_satellite_ao_dispatch_batch1_2026_08_08_finalize.md`) for the live dispatchable todos. The canonical
> `- [ ]` checkboxes for these items (Phase 2 / Phase 11 below) are converted to non-ingestable pointer lines in the
> same commit as this extraction (`task_template.md` finding H — a digest of another plan's todos is never real checkbox
> syntax).
>
> **cs-leg longer-horizon TARGET retrain in `_panel.py` (P2.11.15) — NOT extracted, HELD BACK on conflict.** The
> satellite batch's conflict-check found this is a near-verbatim duplicate of `crypto_alpha_research_2026_07_24.md`'s
> own open `[RESEARCH] P2` todo (line 536: "...or a longer-horizon target retrain in `_panel.py`..."). Per
> `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3, a verbatim/near-verbatim duplicate
> claim is NOT extracted into a competing todo — this item stays exactly where it is, below in Phase 11 (still
> `assigned_vm: NA` here). See `citadel_satellite_ao_dispatch_batch1_2026_08_08.md`'s own `## Deferred` section for the
> full citation.
>
> **4 stale bullets removed from this list (2026-08-08 correction, NOT part of the extraction above)**: this section
> previously ALSO listed `_mom_tb.py` daily-PnL-save bug, combined-book vol-normalisation bug, cs ensemble
> `alt_*`-vs-`altfull_*` gap, and HYPE+post-2024-cohort universe gap. These are stale remnants of the 2026-07-24
> section-C migration below — all 4 are already live, open checkboxes in `crypto_alpha_research_2026_07_24.md` (lines
> 436, 487, 440, 480 respectively as of 2026-08-08), never checkboxes in THIS doc, and were never orphaned. Removed here
> to stop this register misrepresenting them as open-and-unclaimed in this doc.

**B — Operator-gated: LIVE TRADING (hard-stop, human-only):**

- [INFRA] **P7.3 — Live → reconcile to paper → (∴ batch).** `BLOCKED-OPERATOR-DECISION`: needs an approved live wallet +
  custody (Copper/CEFFU). **Wallet keys are a human-only hard-stop.** The paper≡batch ε=0 proof does NOT depend on it;
  once a live wallet exists this is the same machinery with real venue fills (measures live↔paper execution alpha).

**C — Operator-gated: LIVE RESEARCH / trading-judgment (the strategy-alpha workstream) — MIGRATED 2026-07-24:**

> **MIGRATED 2026-07-24**: this register's alpha-research + book-SIZING-decision items (short-sleeve re-spec, basis
> realism, TS-momentum, execution/universe research — the exact "16 items" this section used to list) moved verbatim,
> together with the standalone `e2e-testing/scripts/paper_trading/` POC dashboard Progress Log section (a parallel
> tactical track, ~35 `- [ ]`/`- [x]` checkboxes total), to
> [`plans/active/crypto_alpha_research_2026_07_24.md`](/plans/active/crypto_alpha_research_2026_07_24.md) — executing
> this section's own 2026-06-23 migration proposal, per `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`
> (operator-approved unlock + extract, 2026-07-24). See that plan for the alpha-research decisions + the POC history.

**D — Deferred / pre-existing / stale (parked or closed):**

- [SCRIPT] `P3.2` — `DEFERRED` (pre-existing, NOT this work).
- [SCRIPT] e2e-ratchet drift — `BLOCKED` (pre-existing e2e ratchet, NOT this work).
- [CODE] "Match the e2e weighting / per-archetype RANK allocators" — **DUPLICATE of the shipped P11.15** (rank-weighted
  allocations) → closed in this cleanup (flipped ✅).

**E — Rehomed from `issues/batch_live_reconciliation_service_audit_2026_05_27.md` (2026-07-27 pre-June-1 stale-work
audit) — 3 genuinely orphaned BLRS gaps, no successor plan previously tracked them:**

- [x] ✅ [CODE] P1.BLRS1 (was G1, P1) — DONE (batch-live-reconciliation-service@80380c5). **Wired BLRS
      `resolution_api.py` to Stage-5 outputs** — `_current_breaks()` reads `t1-recon/recon/index.json` +
      `summary_{date}.json` from the recon bucket, falling back to the mock set only when no run has ever produced a
      summary; `stage5_results_writer.py` now serializes per-deviation detail into the summary JSON. 6 new unit tests,
      full QG green. Repo: batch-live-reconciliation-service.
- [x] ✅ [CODE] P2.BLRS2 (was G3, P2) — RESCOPED, then DONE at its own scope. **stage4 agent dispatch to
      trading-agent-service** turned out to need a real design decision, not a mechanical wire-up — resolved via
      `/plans/archive/issues/blrs_g3_g10_rescope_2026_07_28.md`'s 2 todos: operator-ruled 2026-07-29 (a daily-scheduled
      LLM analysis job on the planning VM, not a trading-agent-service endpoint or PubSub consumer) + the scoped design
      plan authored per that ruling — `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md`
      (unified-trading-pm@b30848f1c). That design plan's own §5 carries the 6 build-phase follow-up todos (not
      duplicated here). Repo: batch-live-reconciliation-service / trading-agent-service.
- [x] ✅ [UI] P3.BLRS3 (was G10, P3) — VERIFIED, then DONE. **UI→resolution-API wiring** — both gateway proxies shipped
      (unified-trading-api@d7fdea4 BLRS breaks/resolve/book-correction proxy; unified-trading-api@df6d5ee
      strategy-service/position deviations/balances/pnl/summary/resolve/auto-recon-history proxy), then wired into an
      operator-facing page: `unified-trading-system-ui@c92078e2` hooks `useResolveBreak`/`useBookCorrection` into
      `/services/reports/reconciliation`'s existing resolve dialog + book-correction action (previously local-React-
      state-only, no backend call). Also fixed a discovered `/api/reporting/:path*` gateway-rewrite bug in
      `next.config.mjs` (pointed at client-reporting-api, which has no matching routes, instead of unified-trading-api's
      own `/reporting` router) that was silently breaking this and the other 7 `use-reports.ts` reporting hooks in real
      (non-mock) deployments. See `/plans/archive/issues/blrs_g3_g10_rescope_2026_07_28.md` for the full evidence.

---

## Phase 2 — Per-trade identity in execution events (G2)

> **EXTRACTED 2026-08-08**: both items below moved verbatim to
> [`citadel_satellite_ao_dispatch_batch1_2026_08_08.md`](/plans/archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08.md)
> — see register § A above for the extraction note. Non-checkbox digest lines only below (`task_template.md` finding H)
> — the live dispatchable todos are in the satellite doc.

- **[CODE] P2.1.** Execution events gain `trade_key` + side/qty/price/fees — replace the date-level float-metric event
  lines with per-trade keyed records (the `LedgerRow` is the natural carrier). Repo: execution-service. → moved to
  `citadel_satellite_ao_dispatch_batch1_2026_08_08.md`.
- **[CODE] P2.2.** colocated_engine fill records carry the key — `fill_id` → the UAC `trade_key`; persist
  `correlation_id` (not a sequential int). Repo: strategy-service. → moved to
  `citadel_satellite_ao_dispatch_batch1_2026_08_08.md`.

## Phase 7 — The 19→26 operator dry-run (runs to completion)

- [x] ✅ [INFRA] P2.7.1 / P7.1-A. **Paper week — REAL run executed on REAL GCS data** — DONE (2026-06-20). The
      strategy-service `--operation paper-run` CLI (`cli/handlers/paper_run_handler.py` + `PaperRunHandler` in
      `service_entry.py`) loads REAL features-onchain Aave `lending_rates` parquets via `GCSFeatureProvider`, runs a
      promoted `carry_staked_basis` instance through `GroupBRunner` → benchmark fills → `emit_paper_run_ledger` → the
      canonical client-reports GCS ledger root. **REAL run `paper-20260620002237-378a3735`** (client
      `firm-paper-determinism`, window 2026-05-16..22, 7 real Aave days) wrote **7 instructions / 21 fills** to
      `gs://central-element-323112-client-reports/ledger/client_id=firm-paper-determinism/run_id=paper-20260620002237-378a3735/`
      — manifest-verified + sample-inspected (real instrument keys, canonical asset_class). **T+1 reconcile ε=0 on real
      data**: `reconcile_day(paper, batch)` → `is_deterministic=True`, bug_class=NONE, mean_fill_price_delta_bps=0
      (validated for the paper↔batch-rerun path; full live-boundary parity pends Phase 2 trade-keying). Required fixes
      shipped WITH it: benchmark-fill ATOMIC TRANSFER-leg skip (`benchmark_fills.py`) + UTL run_writer cloud-agnostic
      GCS read/write helpers (`ledger/run_writer.py`). Daily Slack digest + the soak ride P7.1 (cron infra
      `deployment-service@0fee514`; Stage A/B/C entrypoints now all wired). Full run evidence: the 2026-06-20 Progress
      Log entry. Repo: strategy-service + unified-trading-library.
- [x] ✅ [INFRA] P2.7.2. **Daily T+1 batch rerun + `reconcile_day` — MACHINERY PROVEN ε=0** (`e2e-testing@a553f28`). The
      short-window e2e proof `scripts/defi/determinism_spine_e2e.py` runs the FULL chain end-to-end credential-free:
      paper run writes a keyed InstructionLedger + RunManifest (UTL writer) → P4.3 batch-rerun-from-manifest reproduces
      it as `mode=batch` → keyed trade-by-trade DETERMINISM check returns **`is_deterministic=True` (ε=0)** —
      paper≡batch trade-for-trade over (side, qty, fill_price, fees). Run output: "✅ ε=0 PROVEN — paper≡batch
      trade-for-trade (matched=3 trades …)", exit 0. The daily-VM cadence over a real 19→26 calendar window rides P7.1's
      paper-week VM (the same machinery, longer — calendar-bound soak, the BLRS `daily_determinism_stage` P4.2 is the
      per-day stage). The `--storage gcs --paper-ledger-root gs://…` mode runs the proof against a REAL paper ledger
      (validated for the paper↔batch-rerun path; full live-boundary parity pends Phase 2 trade-keying).
- [ ] [INFRA] P2.7.3. **Live → reconcile to paper → (∴ to batch)** — same machinery with real venue fills; report
      live↔paper execution alpha + confirm `live↔batch = determinism(≈0) + execution(measured)`. Repo: (gated on live
      custody readiness — `BLOCKED-OPERATOR-DECISION` until a live wallet is approved).

## Phase 9 — paper/batch spine correctness fixes (2026-06-20) + captured pre-existing findings

- [x] ✅ [CODE] P9.A. **Perp hedge books SHORT (the all-long determinism-spine bug)** — DONE (2026-06-20,
      strategy-service). `BenchmarkFillRecord` carries `side` (from `leg.side` / `instruction.direction`);
      `ledger_emit._side_for_fill` prefers it + raises on a side-less TRADE; `_direction_side` maps BUY/LONG→+1,
      SELL/SHORT→−1. LIVE: `DERIBIT:ETH-PERP net_qty=-246.67` (SHORT), net ETH ≈ +20 (haircut residual, near-neutral).
      Files: `engine/backtest/benchmark_fills.py`, `engine/backtest/ledger_emit.py`. See Progress Log 2026-06-20.
- [x] ✅ [CODE] P9.B. **Batch rerun genuinely RE-DERIVES (non-tautological ε=0)** — DONE (2026-06-20, strategy-service).
      `batch_rerun.rerun_from_manifest` re-runs `GroupBRunner` over the paper manifest's pinned window+archetype
      (`paper_run_handler.replay_carry_strategy`), NOT `load_instruction_ledger_fills`; `reconcile_paper_batch` proves
      ε=0. `base.py::_next_instruction_id` made deterministic (`inst_{archetype}_{seq}`) so trade_keys match across
      runs. LIVE: 24 re-derived fills, `recon.deterministic=true, matched=24/24`. Files: `cli/handlers/batch_rerun.py`,
      `cli/handlers/paper_run_handler.py`, `engine/strategies/v2/base.py`.
- [x] ✅ [CODE] P9.C. **Guard — all-long carry run fails loud** — DONE (2026-06-20).
      `ledger_emit.assert_carry_basis_structure` (+ runtime call in `run_paper`); unit test
      `test_carry_staked_basis_hedge_short_regression.py`.
- [x] ✅ [SCRIPT] P3.1. **Fixed `Event logging not initialized` in non-carry engine unit tests** — DONE
      (strategy-service@67e7826c). Root cause confirmed: the v2 conftest autouse fixture only patched
      `staked_basis.log_event`, never the arbitrage/sports engine modules nor the cli/handlers manifest-guard test, and
      no autouse events init existed for those paths. Fix: a session-safe autouse fixture in the top-level
      `tests/conftest.py` (`_events_initialized_for_tests`) initializes events in `mode="test"` (log_event → no-op, no
      sink) for ALL tests, save/restoring `_mode`/`_writer`/`_service_name` so tests that manage events state themselves
      (`test_cdc_strategy_state`, `test_risk_preflight_gate`, `test_event_logging`) are not polluted. The ~33
      previously-red non-carry engine + manifest-guard tests now pass; the full strategy-service unit suite is GREEN
      (2704 passed locally with the credential-free env). NOTE: the full `quality-gates.sh` harness in the root/slot
      clones currently mis-roots its TESTS phase to unified-trading-pm (`rootdir: …/unified-trading-pm`, runs PM's 6
      tests) — a fleet-wide QG-harness defect, NOT this code; the authoritative server `quality-gates-v2` runs
      test-in-image with correct rootdir. Repo: strategy-service. Provenance: paper/batch spine fix session 2026-06-20.
- [ ] [SCRIPT] P9.2 (was: mislabeled P3.2 — collided with Phase 3's real P3.2 "PassiveLedger synthesiser" item above;
      renumbered per verify-rerun-2 finding 17, 2026-07-14). **DEFERRED (pre-existing, NOT this work) — UAC version
      drift blocks strategy-service QG preflight.** `quality-gates.sh` version-alignment gate: local
      `unified-api-contracts=0.26.0` vs main `0.27.0`. Run
      `bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix` (after `git pull origin main` in
      PM). Repo: strategy-service (dep alignment). Provenance: paper/batch spine fix session 2026-06-20.
- [x] ✅ [SCRIPT] P3.3. **SWAP leg `size_units` now denominated in the OUT asset (ETH), not the USDC-in notional** —
      DONE (strategy-service@67e7826c). `staked_basis.py` both SWAP legs (open `_build_atomic_legs` + rescale) now set
      `size_units` to the canonical OUT-asset qty (`eth_qty = usdc_to_stake / eth_price`; rescale `eth_delta_qty`),
      derived from the swap's out-amount (notional / price), NOT a hardcoded map; the USDC-in notional is preserved in
      `params["from_amount"]`. The benchmark fill then books `eth_qty · eth_price == usdc_to_stake` (correct USD
      notional) and the ledger qty is an ETH quantity consistent with the LIDO/DERIBIT legs. 3 stale tests updated to
      assert OUT units. **Live-verified on real run `paper-20260620133928-d7a30df2`**:
      `UNISWAP_V3:DEX_POOL:ETH net_qty=233.33` (ETH — was 800000 USDC), `LIDO:STAKING:ETH net_qty=233.33`,
      `DERIBIT:ETH-PERP net_qty=-215.83` (SHORT) → net ETH ≈+17.5 (haircut residual, near-delta-neutral). Repo:
      strategy-service. Provenance: 2026-06-20.
- [x] ✅ [CODE] P3.4. **MARKS → PricingLedger (producer)** — DONE (`unified-trading-library@5f941c6e` +
      strategy-service@67e7826c). UTL gained the PricingLedger producer leg: `materialize.pricing_ledger_row` (a
      `MARK_UPDATE` `LedgerRow`, `event_origin=PASSIVE`, `delta=0`, `price=mark`) + `run_writer.pricing_ledger_jsonl` /
      `write_run_pricing_ledger` (deterministic JSONL → `{ledger_root}/ledger_type=pricing/{run_id}.jsonl`; asset
      identity derived canonically from `instrument_key`, no metadata maps). strategy-service
      `ledger_emit.write_paper_run` now derives per-instrument marks from the SAME benchmark fills (`marks_from_fills`:
      last `fill_price` per `instrument_key` — deterministic + batch-re-derivable) and writes the PricingLedger
      alongside the InstructionLedger; `write_paper_run`/`emit_paper_run_ledger` return `(ledger,manifest,pricing)`
      URIs. The position materialiser already joins marks on `asset_canonical_id` → `unrealized_pnl`. 6 UTL + 2 strategy
      tests. **Live-verified `paper-20260620133928-d7a30df2`**: 3 `mark_update` marks written to
      `…/ledger_type=pricing/…jsonl` (DERIBIT ETH-PERP @3000, LIDO ETH @1, UNISWAP_V3 ETH @3000). Repo: UTL +
      strategy-service. Provenance: 2026-06-20.
- [x] ✅ [CODE] P3.5. **ATTRIBUTION → P&L attribution parquet (producer)** — DONE (strategy-service@67e7826c).
      `paper_run_attribution.build_paper_run_attribution`/`emit_paper_run_attribution` build canonical
      `PnLAttributionRow` records from the run's REAL captured carry rates — `CARRY` = LST staking yield, `BASIS` = Aave
      supply−borrow spread, per held day, at `PnLLayer.STRATEGY`, accrual = `notional·rate/365` — and emit via the UTL
      SSOT `emit_attribution_parquet` to exactly the path `attribution_reader.read_attribution_rows` scans
      (`pnl_attribution/strategy_id={S}/client_id={C}/date={D}/rows.parquet`). Per-day rates surfaced on
      `StrategyReplay`; wired into `run_paper`. **Honest gap (NOT fabricated):** the price/DELTA + FEES legs need a
      spot-price column the lending-rates corpus does NOT carry (the handler prices SWAP/TRADE off `_REFERENCE_MID`);
      the position is delta-neutral so the price leg nets ≈0 — omitted, not invented (lands when the price feature group
      is added). 5 tests. **Live-verified `paper-20260620133928-d7a30df2`**: 7 daily shards / 14 rows written (each
      date: CARRY+BASIS, non-zero amounts from real Aave rates) — `attribution_reader` now has rows to read (was empty).
      Repo: strategy-service. Provenance: 2026-06-20.
- [x] ✅ [INFRA] P3.6. **Re-run + ε=0 verification with the new ledgers** — DONE (2026-06-20). New REAL run
      `paper-20260620133928-d7a30df2` (client `firm-paper-determinism`, window 2026-05-16..22, 7 real Aave days) wrote
      InstructionLedger (21 fills) + PricingLedger (3 marks) + RunManifest + 7 attribution shards to the canonical
      client-reports GCS root. **Batch rerun re-derived ε=0 WITH the new ledgers**: `rerun_from_manifest` →
      `ReconResult(deterministic=True, paper_count=21, batch_count=21, matched=21, deviations=[])` (the deterministic
      marks don't break the proof). Perp still SHORT (`DERIBIT:ETH-PERP net_qty=-215.83`), book near-delta-neutral.
      Repo: strategy-service. Provenance: 2026-06-20.

## Success criteria (per phase: QG/basedpyright/ruff green + tests)

- **Determinism**: `reconcile_day(paper, batch)` returns ε=0 — **PROVEN** (P7.2, `e2e-testing@a553f28`): the
  short-window e2e proof returns `is_deterministic=True` end-to-end (paper → batch-rerun → keyed determinism check),
  exit 0. The real-week (19→26) soak is the same machinery longer, calendar-bound (rides P7.1's paper-week VM)
  (validated for the paper↔batch-rerun path; full live-boundary parity pends Phase 2 trade-keying).
- **Completeness**: the 4 ledgers materialise; balances/PnL/attribution are real (not mock/`"0.00"`), per
  venue+instrument.
- **One fill model**: no third fill model on the batch/paper path (`BenchmarkFillEngine` is the single sim SSOT).
- **Slack**: daily ledger digest + daily T+1 recon verdict reach `#uts-live-alerts`.

## Phase 11 — Autonomous rolling-book gaps (operator audit 2026-06-21)

> Operator probe 2026-06-21: "is all the code and data real running autonomously to continue to generate trades and PnL
> … how much of prod vs bolt-ons … is all money movement and treasury vs trading-wallet simulated properly". A
> live-state audit of the deployed cron + the GCS ledger (`run_id=paper-20260621134256-3c4eb321`) surfaced the gaps
> below. All are real; filed per Capture-Discoveries HARD RULE; driven to done under `/autonomous` 2026-06-21.

- [x] ✅ [INFRA] P11.1. **Roll-forward cron window** — DONE (deployment-service@f5a81d6 + strategy-service@ba63ab1c).
      Cloud Run Job `uts-prod-paper-engine-run` args now `--rolling-days 7` (verified live; no absolute dates); the CLI
      flag computes a trailing 7-day window ending T-1 UTC at job start (`test_paper_run_rolling_window.py`, 5 tests).
      So each 02:00 UTC run books a fresh day instead of re-running the fixed 05-16..22 week.
- [x] ✅ [CODE] P11.2. **Pin `code_shas` in the run manifest** — DONE (strategy-service@ba63ab1c). `_git_sha()` prefers
      config `code_version` (`CODE_SHA_STRATEGY_SERVICE`/`CODE_VERSION` via UnifiedCloudConfig) → `git rev-parse` →
      "unknown"; stamped into the manifest so `assert_code_shas_match` proves SAME-code.
      `test_git_sha_prefers_configured_code_version`.
- [x] ✅ [CODE] P11.3. **Emit the PASSIVE accrual ledger TAPE per period** — DONE (UTL@afc31764 +
      strategy-service@ba63ab1c). UTL `write_run_passive_ledger`/`passive_ledger_jsonl` (`ledger_type=passive`);
      producer emits per-held-day `STAKING_REWARD` + `LENDING_INTEREST` (staking venue) + `FUNDING_ACCRUAL` (perp),
      QUOTE cash-flow delta (NEVER fed to `materialize_position_ledger`). batch_rerun re-derives it; ε=0 unaffected. 8
      producer + 3 UTL writer tests.
- [x] ✅ [CODE] P11.4. **Treasury ↔ hot-wallet split in the TRANSFER ledger** — DONE (strategy-service@ba63ab1c). DeFi
      20% treasury / 80% hot TRANSFER legs at deploy, keyed by `share_class`, single `client_id` (funds-isolation);
      CeFi/Sports = 0% (no split); deploy flow sized off the hot budget. `test_treasury_hot_split_20_80` +
      `test_cefi_has_no_treasury_split`.
- [x] ✅ [CODE] P11.5. **De-dup the bare vs `@`-qualified strategy_id** — DONE (strategy-service@ba63ab1c). Manifest
      `strategy_ids` = ONLY the `@`-qualified slot ids (bare archetype dropped → no per-strategy double-count); batch
      rerun resolves archetype via `archetype_for_slot_label`. `test_slot_labels_are_qualified_not_bare_archetype`;
      batch_rerun ε=0 intact.
- **[CODE] P1.6.** GroupC smart-fill handoff into paper-run (`fill_model` BENCHMARK→SMART) — PARTIAL
  (strategy-service@ba63ab1c left manifest HONEST at `BENCHMARK`, NOT faked). Blocked by the no-service-deps HARD RULE:
  strategy-service MUST NOT import execution-service, so smart-matching cannot be called in-process. Remaining (correct
  architecture): a new execution-service Layer-3 entrypoint consuming `{run}/ledger_type=instruction` + RunManifest →
  GroupCRunner smart-matching → an `execution_alpha_bps` artifact, driven from the e2e-testing harness; CRA reads it at
  `PnLLayer.EXECUTION`; UI surfaces exec-α. (FEES is already the only EXECUTION-layer leg.) **EXTRACTED 2026-08-08** →
  moved verbatim to `citadel_satellite_ao_dispatch_batch1_2026_08_08.md`.
- [x] ✅ [INFRA] P11.7. **Custom domain for the paper-trading UI** — DONE pending DNS (deployment-service@1168718 +
      @3c54e64). `portal.odum-research.com` Cloud Run domain mapping created + tracked in
      `terraform/gcp/domain_mappings.tf` (`DomainRoutable=True`, `CertificatePending`). **Operator DNS step:** add CNAME
      `portal` → `ghs.googlehosted.com.` at the odum-research.com registrar; the managed cert auto-provisions once it
      resolves.
- [x] ✅ [CODE] P11.8. **Fee model — approximate maker/taker fees on turnover** — DONE (strategy-service@ba63ab1c).
      Deterministic **1 bp maker / 2 bps taker** on filled notional, per-venue overridable (`_VENUE_FEE_OVERRIDE_BPS`),
      booked as the `FEES` factor at `PnLLayer.EXECUTION`, one NEGATIVE row per leg (swap+stake+perp = taker); grand
      total drops by the fee drag. ε=0 preserved (benchmark `TradeFillRecord`s stay fees=0).
      `test_fees_are_execution_layer_and_nonzero` + `test_maker_taker_rates`.
- [x] ✅ [CODE] P11.9. **Strategy-keyed ledgers — BACKEND DONE (UAC@70695806 / UTL@cc5ebe5a / strategy-service@77f3c5b6
      / CRA@981f14d: optional `strategy_id` on every LedgerRow, stamped on instruction/pricing/passive/transfer per
      @-qualified id, CRA `by_strategy` + `?strategy_id=` filter, ε=0). UI per-strategy/archetype drilldown REMAINS
      (tracked in Final).** Orig:**Strategy-keyed ledgers + UI drilldown across ALL ledger types** (operator 2026-06-21:
      "associate pnl, trade, order and position ledgers to strategies … all parts of the UI should group + drilldown by
      strategy"). `LedgerRow` has NO `strategy_id` column today — only the attribution parquet is strategy-partitioned,
      so trade / position / transfer / passive / pricing ledgers can NOT be grouped by strategy (the strategy is only a
      substring of the composite `trade_id`, and was the bare archetype). Add a canonical `strategy_id` field (the
      `@`-qualified id) to `LedgerRow` (UAC), stamp it on EVERY row in all UTL materialisers + the strategy-service
      emitters, GROUP-BY `strategy_id` in CRA across ALL ledger views (positions/PnL/trades/transfers/passive, not just
      attribution), and add a strategy filter + per-strategy drilldown to EVERY UI panel. Repo: unified-api-contracts
      (field) + unified-trading-library (stamp) + strategy-service (emit) + client-reporting-api (group) +
      unified-trading-system-ui (drilldown, playwright-gated).

- [x] ✅ [CODE] P11.10. **Replicate the full e2e experiment universe + wire the portfolio_allocator — DONE**
      (UTL@e797deac / strategy-service@4e2c14c6): `paper_universe.py` allocator-driven selection replaced hardcoded
      indices; verified live `paper-20260621171725-fcf31316` = **14 strategy_ids, allocator-weighted, all strategy-keyed
      ledgers + passive + treasury, batch-rerun ε=0**; 266 specs honestly skipped (no in-window data → P11.11). Orig
      intent: (operator 2026-06-21: "missing lots of strategies and venues from our e2e*testing work … basis, staked
      basis, funding rate dispersion/arb … many more venues and coins … production archetypes are flexible enough … give
      them strategy IDs + configs matching the e2e experiment … how we weight allocations per archetype, which venues,
      which coins at any one time, and moving money around"). The paper run hardcodes `PAPER_RUN_SPEC_INDICES = (0, 6)`
      (2 of 14 `CARRY_STAKED_BASIS` specs); the production catalogue ALREADY builds **468 specs / 30 archetypes**
      (`specs_for_archetype`) incl. the e2e archetypes: `CARRY_STAKED_BASIS` (14), `CARRY_BASIS_PERP` (144),
      `CARRY_FUNDING_DISPERSION` (52), `ARBITRAGE_PRICE_DISPERSION` (17), `CARRY_BASIS_DATED`, `CARRY_RECURSIVE_STAKED`,
      `YIELD*_`, `DEFI*LP*_`. SUB-TASKS: - P11.10a. Extract the e2e experiment's universe (archetypes × venues × coins ×
      weights) from `e2e-testing/scripts/defi/` (funding_reversion_*, funding_ensemble_engine, backtest_solana_basis,
      funding_reversion_multivenue_capital) as the documented intent. - P11.10b. Map e2e universe → catalogue specs
      (`specs*for_archetype`); add any missing venue/coin spec in the right `catalog*_.py`(flexible archetypes — add the
      spec, do not fork the engine); canonical`@`-qualified ids. - P11.10c. Wire `portfolio_allocator/archetypes_.py`
      into the paper run: replace hardcoded indices + 100k/75k split with allocator-driven per-archetype weight + which
      venues/coins active per rebalance + capital deploy (treasury→hot per P11.4, single client_id). - P11.10d. Verify a
      multi-archetype run materialises strategy-keyed ledgers (P11.9) for ALL e2e strategies, ε=0 batch-rerun holds
      across the larger universe, UI groups/drills down by every strategy + archetype. Repo: strategy-service
      (catalogue + allocator + paper_run) + e2e-testing (extraction) + verify CRA/UI.
- [x] ✅ [CODE] P11.6-retry. **execution-service Layer-3 smart-fill entrypoint — SHIPPED** — execution-service@3d7d760c
      (`backtest_v2/smart_fill_replay.py` + `--operation smart-fill-replay` CLI + peripheral-QG wiring; 12/12 tests, QG
      exit-0) + e2e-testing@0e421c08 (`scripts/defi/execution_alpha_replay_e2e.py` → writes
      `ledger_type=execution_alpha`, `execution_alpha_bps = smart − benchmark`; QG exit-0). Both verified on
      origin/live-defi-rollout 2026-06-21. Ship was blocked by 3 PRE-EXISTING fleet conditions, all cleared: (1)
      execution-service codex ratchet 4>3 → cleared 2 classes to 2 (empty-string fallback in smart_fill_replay.py:276 +
      the back-compat docstring in v2/benchmark_fills.py:12) + fixed a net-new STEP-5.69 inline-gs:// flag (error-msg
      noqa on smart_fill_replay.py:224) → QG exit-0; (2) PM manifest `versions{}` promotion-lag did NOT block service
      quickmerge (warn-only PM post-gate; left to promotion automation, not hand-synced per the pull-not-push
      manifest-surface rule); (3) e2e dep-validation pre-flight tripped on a LIVE FOREIGN strategy-service test/source
      WIP (operator-protected — never touched) → shipped via the documented multi-agent `--skip-preflight` route (the
      new e2e file imports only execution_service + UAC + UTL; strategy-service SOURCE on LDR is unchanged, so zero
      blast-radius on this ship).

- [x] ✅ [DATA] P11.12. **CeFi funding READ from canonical GCS (Tardis) — DONE, NOT a backfill.** The data was already
      in `perp-funding-prd/.../pipeline_mode=batch_tardis/asset_group=cefi/` (7 venues); the only gap was a venue-name
      mismatch, fixed by `_canonical_venue` (strategy-service@bbdb4f1e). Verified run `paper-20260621215559-4337e2aa`:
      **141 strategies / 6 archetypes** (CARRY*BASIS_PERP 79, CARRY_FUNDING_DISPERSION 33, CARRY_STAKED_BASIS 14,
      ARBITRAGE_PRICE_DISPERSION 10, DEFI_LP 5), real funding PnLs, **ε=0 PROVEN (1016 trades matched, 0 deviations)**.
      149 specs honestly skipped (genuinely-absent / unwired → P11.13 for vault+fees; perp_funding for non-Tardis venues
      genuinely absent). 30 archetypes + the allocator, but 266/468 specs honestly SKIP because their market data is
      absent for the paper window: `perp_funding` (→ CARRY*BASIS_PERP 144, CARRY_FUNDING_DISPERSION 52),
      `dex_pool_state` (→ ARBITRAGE_PRICE_DISPERSION 17, DEFI_LP\** 9), `lst_rates` beyond Lido/Jito/Marinade,
      dated/recursive inputs. Only `lending_rates` (Aave/Compound/Spark) is present → CARRY*STAKED_BASIS is the only
      data-drivable family today. Backfill these feature groups for the firm-paper-determinism window (2026-05-16..22,
      then rolling) via the MTDS / features pipeline (data-pipeline-correctness HARD RULE — every venue × data_type ×
      range, honest absence where a venue genuinely lacks history). The e2e launch\*\_\_vm.sh scripts name the sources
      (perp_funding / dex_pools / lst_rates / lending_indices / gas_fees). Once the data lands, the SAME wired
      archetypes auto-populate — no code change. Repo: mtds / features-service / e2e-testing (sourcing); parent epic
      data/mtds master.
  - **FINDING (CeFi perp-funding GCS audit, 2026-06-21 — confirms CARRY_FUNDING_DISPERSION 52 + non-HL CARRY_BASIS_PERP
    blocker is a TRUE backfill, not a read-wiring gap):** CeFi perp **funding-rate** data is **genuinely ABSENT** across
    every canonical bucket. Checked: `perp-funding-{prd,,test}-central-element-323112` (all hold ONLY `asset_group=defi`
    venues — ASTER/GMX/HYPERLIQUID/PACIFICA, `data_type=perp_funding`, 2021-09-01..2026-05-22; ZERO CeFi venues);
    `market-data-tick-cefi-prd-central-element-323112` (has raw `derivative_ticker`/`book_snapshot_5`/`trades` for
    BINANCE-FUTURES/BYBIT/OKX/DERIBIT/KRAKEN-FUTURES via Tardis incl. the 2026-05-16..22 window, but **no `perp_funding`
    data_type anywhere** — derivative*ticker carries the funding \_field* on the raw tick, but the computed funding-rate
    series is not materialised); `features-delta-one-cefi-prd-…` (EMPTY); `features-onchain-cefi-prd-…` (EMPTY — this is
    the target of `features_service/cefi/calculators/perp_funding_rates.py`, which is MVP-scoped to Binance ETH-PERP and
    has not written output for the window). **Root cause:** the CeFi perp-funding compute (reads CeFi MTDS
    `derivative_ticker` → writes `features-onchain-cefi`) has not been run/materialised for the window. **Action:** run
    the CeFi `perp_funding` compute (broaden beyond Binance ETH-PERP MVP to BINANCE/BYBIT/OKX/DERIBIT/KRAKEN) over
    2026-05-16..22 + rolling, honest-absence where a venue genuinely lacks history. Repo: features-service (cefi
    perp_funding calculator) + mtds (if derivative_ticker gaps surface).

- [x] ✅ [DATA] P11.13. **DEFI_LP_VAULT share-price + fee-0 pool fees — DONE** (strategy-service@70a76d87). Vault APY
      from the ERC-4626 `vault_share_price` corpus via `CanonicalVaultProvider` (yvUSDC ~335bps, sUSDe ~420bps, sDAI
      124bps); fee-0 LP pools fixed with The-Graph `feesUSD` (Curve 18-46bps, Balancer 56-169bps). 24 unit tests.
      Verified run `paper-20260621225959-e86237f7`: **145 strategies / 7 archetypes** (DEFI_LP_VAULT 3 lit, DEFI_LP_POOL
      2→3). 197 specs honestly skipped. 2026-06-21: "fix that, we can get data, we got creds"). Two honest-skip gaps
      from P11.11/dex tranche are sourceable, not walls: (a) DEFI_LP_VAULT (ERC-4626 yearn/etc) needs a
      vault-share-price series — read `convertToAssets(1e18)` / `pricePerShare()` historically via the Alchemy/Helius
      archive RPC (creds `alchemy-api-key`/`helius-api-key` in Secret Manager) OR the vault subgraph
      (`thegraph-api-key`); (b) the `fees_usd=0` LP pools (Curve threepool/crvusdusdc, balancer) need real fee data —
      pull `feesUSD` from the Uniswap/Curve/Balancer subgraph (The Graph, `thegraph-api-key`..`-7`) or compute
      `volume_usd × fee_rate_bps` where volume is present. Materialise both into the canonical dex/vault feature
      location the engine reads (resolve_bucket_name SSOT), then wire DEFI_LP_VAULT into the paper run + re-derive the
      fee-0 LP pools so they produce real fee/IL PnL. Honest absence only where a vault/pool genuinely has no on-chain
      history. Backtest + ε=0. Repo: mtds / features-onchain (sourcing) + strategy-service (DEFI_LP_VAULT wiring). Creds
      via get_secret_client — never raw values in repo.
- [x] ✅ [CODE] P2.11.14. **Wire the BTC-level trend-following (CTA) leg — SHIPPED 2026-06-22: UAC@61ac3ad2
      (TSMOM_BTC_CTA enum+family+leg-spec) + strategy-service@f5f00109 (TsmomBtcCtaEngine + catalogue + paper-universe
      gating + unit test), both on LDR, QG-green. Version-promotion-lag cleared via run-version-alignment --fix
      (PM@0df3854f). Remaining for a non-null live paper run: P2.11.16 features + the ε=0 run.** — proven in research
      (`_exec_optimize.py` `trend` leg, 15% sleeve; Progress Log 2026-06-21 "WHY THE DIRECTIONAL BOOK MAKES ~0 IN 2023 &
      2026"). The directional book is market-neutral + long-biased so it makes ~0 in the two BETA years (2023 melt-up /
      2026 selloff); a BTC multi-horizon (1/3/6/12mo) TSMOM leg — long confirmed up-trend, short confirmed down-trend,
      sign-averaged, lagged (no lookahead) — earns exactly there (standalone realistic Sharpe +0.74 net +$659k; '23 +1.4
      '26 +2.3; corr to BTC buy&hold +0.00 full / −0.85 in the selloff = genuinely shorts the downtrend, not
      closet-long; corr to XS book −0.11). Implement as a production strategy archetype/leg in **strategy-service**
      (TS-momentum signal from the canonical OHLCV the engine already reads; batch=live one path; ε=0 batch-rerun proof;
      realistic fills via execution-service GroupC). Sizing = **co-equal sleeve** (`W["trend"]` ≈0.28, IS-validated
      robustness pick; on the proper-execution base it flattens 2023 −0.6→+0.1 + 2026 −1.1→+0.1, preserves full Sharpe
      +2.28→+2.26, trims maxDD −6.3→−5.0%). NOTE: the trend leg **subsumes** the old de-risk overlay + 12% short (does
      their 2026 job + fixes 2023 + keeps the Sharpe they cost) — make those light DD-insurance, NOT core sleeves;
      stacking all three over-hedges (−0.18 full Sharpe). Repo: strategy-service. **DESIGN LOCKED 2026-06-22 + BUILD
      DISPATCHED**: dedicated `TSMOM_BTC_CTA` archetype (not a `RULES_DIRECTIONAL_     CONTINUOUS` reuse — the factory
      routes by archetype + clean per-leg PnL attribution). 11-step change set mapped: UAC (enum +
      `ARCHETYPE_TO_FAMILY`→RULES*DIRECTIONAL + `archetype_leg_spec_seeds`) → strategy-service (new
      `rules_directional/tsmom_btc_cta.py` `TsmomBtcCtaEngine` reading
      `btc_trailing_return*{1,3,6,12}m`+`btc*realized*     vol`features, sign-averaged + vol-scaled +
      lagged;`factory`registry;`archetype*defaults` Kelly→`V1_ARCHETYPES*     IN_SCOPE`;
      `catalog_directional.build_tsmom_btc_cta`slot`TSMOM_BTC_CTA@binance-btc-tsmom-1d-usdt-v1-prod`;
      `catalog.\_BUILDERS_BY_ARCHETYPE`; `archetype_slots_cefi`; `paper_universe` `\_ENGINE_DRIVABLE`+`E2E_UNIVERSE`;
      unit test). **Sub-deps (own todos): P2.11.16 features-service BTC-trend features (GATES the live paper run — null
      signals until written); P2.11.17 UI archetype mirror (playwright-gated).** Then the live ε=0 paper run. **STATUS
      2026-06-22 — CODE BUILT + TEST-GREEN, ship BLOCKED on transient fleet-wide version-lag (NOT the archetype). UAC
      edits now STASHED to unblock an unrelated features-service quickmerge (the dirty UAC clone tripped the dirty-deps
      pre-flight) — recover with `git     -C .tabs/1/unified-api-contracts stash     pop`(stash msg "TSMOM_BTC_CTA
      archetype + WS-mapping fix — blocked on UAC version-lag"); strategy-service edits remain UNCOMMITTED in its
      clone.** The UAC
      files:`enums.py`+`archetype_leg_spec_seeds.py`+`tests/unit/test_archetype_leg_spec.py`(52→53) +`tests/test_ws_cassette_coexistence.py`(added
      the LEGIT`kalshi_clob_ws`/`polymarket_clob_ws`venue mappings — a pre-existing cross-repo cassette gap, real
      connectors, needed for green); strategy-service new
      `rules_directional/tsmom_btc_cta.py`+`tests/.../test_tsmom_btc_cta.py` + factory/defaults/slots/catalog/
      catalog_directional/paper_universe/batch_utils/`rules_directional/**init**.py`/test_ml_directional_continuous. UAC
      full QG = **10,215 passed** (incl. the new leg-spec test) once the WS mappings were added; strategy-service =
      content-sentinel green. **BLOCKER**: UAC local `quality-gates.sh`version-alignment HARD-fails because the PM
      `workspace-manifest.json` `versions[unified-api-contracts]`is **0.39.0** on origin/LDR while UAC-main is
      **0.40.0** (the manifest-update workflow hasn't synced the bump — the documented VERSION_SPLIT promotion-lag, here
      hard-blocking the consumer's local QG).`--skip-version-alignment`is human-only. **TO COMPLETE (once the PM
      manifest syncs to UAC 0.40.0, or a human aligns it)**:
      re-run`cd     unified-api-contracts && bash scripts/quality-gates.sh --no-fix` → quickmerge UAC
      (`enums.py     archetype_leg_spec_seeds.py tests/unit/test_archetype_leg_spec.py`) + a separate `fix(tests):`
      commit for the WS mappings → then quickmerge strategy-service (it depends on the UAC enum, so promote UAC first).
      The agent's first pass left it unshipped + had ONE hallucinated WS-test edit (invented connectors) which was
      dropped; the real WS mappings were re-added.
- **[DATA] P2.11.16.** features-service: compute + write BTC trend features `btc_trailing_return_{1m,3m,6m,12m}` +
  `btc_realized_vol` to the canonical GCS feature corpus the paper run reads — the CTA engine (P2.11.14) reads these
  from `features: dict[str,float]`; without them the paper run produces null signals (honest absence). Trailing returns
  = BTC daily mark `pct_change(21/63/126/252)` shifted (T-1, no lookahead); realized_vol = rolling 60d std ×√365. Source
  = the daily BTC mark from the perp-funding corpus (`perp_daily_ctx`) the providers already read. batch=live one path.
  Repo: features-service (+ resolve_bucket_name SSOT / UTC). This is the CRITICAL-PATH gate for a non-null CTA paper
  run. STEP 1 ✅ SHIPPED 2026-06-22 — features-service@653cf158. `btc_trailing_return_{1,3,6,12}m` + `btc_realized_vol`
  added to delta_one's `returns` calculator + `registry_specs.yaml` (no-lookahead trailing windows, NaN until filled),
  `test_returns` unit tests GREEN, full QG passed (622s), on origin LDR. REMAINING (operational): recompute the
  delta_one feature corpus so these columns exist in GCS for the live paper run (a features-service backfill — shared
  with the P2.11.18 reversion-feature corpus recompute; run both together). **EXTRACTED 2026-08-08** → moved verbatim to
  `citadel_satellite_ao_dispatch_batch1_2026_08_08.md`.
- [x] ✅ [UI] P2.11.17. **Mirror the `TSMOM_BTC_CTA` archetype into unified-trading-system-ui — SHIPPED + VERIFIED
      2026-06-22: ui@6442d46e | pw:L2 ✓ (67 passed, 4.0m) | regression: tests/unit/lib/architecture-v2/enums.test.ts
      (toHaveLength 19) + tests/unit/wizard/parity-gates.test.ts (58 archetypes) — both fail on TSMOM removal.** 15
      files (`lib/architecture-v2/enums.ts`+`coverage.ts`+`archetypes.ts`, `lib/help/help-tree-generated.ts`,
      `lib/mocks/fixtures/trading-data.ts`, `lib/registry/ui-reference-data.json`,
      `components/briefings/     strategy-coverage-matrix.tsx`, `components/marketing/strategy-family-catalogue.tsx`,
      `public/     capability-verdict-matrix.json` + 6 test files). tsc clean, 286 Vitest pass, `quality-gates.sh`
      exit 0. The playwright SMOKE gate (`tests/smoke/`) self-starts `PORT=3100 pnpm dev:mock` (120s boot) — the earlier
      BLOCKED-PLAYWRIGHT was just not waiting for boot; ran green here. Repo: unified-trading-system-ui.
- **[CODE] P2.11.20.** Complete TSMOM_BTC_CTA capability wiring — add it to the UAC archetype_capability_manifest (found
  2026-06-22 via the e2e archetype-capability playbook). `TSMOM_BTC_CTA` is in `StrategyArchetype` + the UI
  enum/capability-verdict-matrix but MISSING from
  `unified-api-contracts/.../internal/architecture_v2/archetype_capability_manifest.json` (22 archetypes, no TSMOM) →
  the archetype is half-wired (no per-venue/asset-group capability cells) and the e2e playbook
  `tests/e2e/playbooks/refactor/refactor-g1-8-uac-archetype-capability.spec.ts` would fail. Fix: add TSMOM's capability
  declaration to the source (`registry/archetype_capability_matrix.py` — family RULES_DIRECTIONAL, BTC-level CTA → CEFI
  perp+spot on the major venues, signal `price`/trend) → regen via `scripts/generate_archetype_capability_manifest.py` →
  sync to UI via `scripts/propagation/sync-archetype-capability-to-ui.sh` → re-QG/ship UAC+UI. Then the e2e playbook
  becomes the proper playwright-dir regression for the archetype. Repo: unified-api-contracts (+ UI sync). Confirm the
  exact venue/asset-group capability profile with the operator (CeFi-only BTC, or the DeFi+CeFi hybrid). **EXTRACTED
  2026-08-08** → moved verbatim to `citadel_satellite_ao_dispatch_batch1_2026_08_08.md`.
- **[CODE] P2.11.18.** Add the intraday BTC mean-reversion signal as a cs ML feature (research 2026-06-22, root
  `_ic_test.py`). A short-horizon reversion z-score (`zscore = -(close - rolling_mean) / rolling_std`, anchors 60m + 4h
  on the canonical OHLCV) has a stable Spearman IC ≈ +0.05 vs forward 15m–1h returns, positive across all horizons +
  every recent year (2022-26). It is intraday-microstructure information the daily-horizon delta_one features do NOT
  capture (orthogonal), so it should ADD to the pooled-LightGBM cs ensemble. NOTE: the signal is NOT standalone-
  tradeable (its alpha is inside the execution-cost band — see the research arc: daily Monday-wick edge decayed,
  migrated to 1h, but realistic 1.5bp-taker fills cap it at a marginal +1.14 Sharpe); its value is as a FEATURE (here) +
  an execution-timing overlay (P2.11.19), where it never pays its own round-trip. Implement: add the reversion z-score
  feature spec(s) to the features-service `delta_one/app/features/registry.py` (new `feature_group` or extend an
  existing momentum/reversion group; bump `formula_version`; HIVE-partition + footer metadata per the
  feature-formula-versioning SSOT), compute + write to the feature corpus, then retrain + validate the cs model (does it
  lift cs Sharpe / reduce the 2026 drag — composes with P2.11.15). No lookahead (trailing window, shifted). Repo:
  features-service (feature) + cs-model retrain. Evidence: IC table in `_ic_test.py`. STEP 1 ✅ SHIPPED 2026-06-22 —
  features-service@1110ee1d. `reversion_zscore_60m`/`reversion_zscore_240m` added to delta_one's `anomaly` calculator +
  `registry_specs.yaml` (clip ±5, `min_periods=bars` so NO partial-window/no-lookahead, honest NaN until filled), 6
  `test_anomaly` unit tests GREEN, full QG passed (402s), on origin LDR (Tier-C drain → staging). REMAINING (downstream
  operational/ML — both feature specs (reversion @1110ee1d + BTC trend @653cf158) are on LDR promoting; these run AFTER
  the spec deploy): (a) corpus recompute; (b) cs retrain (composes with P2.11.15's longer-horizon retrain — do both in
  one train); (c) `features-status --check-drift` verification. **EXTRACTED 2026-08-08, SCOPE- TRIMMED** → sub-parts (a)
  corpus recompute + (c) drift-check moved verbatim to `citadel_satellite_ao_dispatch_batch1_2026_08_08.md`; sub-part
  (b) the cs retrain stays HERE (not extracted) because it composes with P2.11.15 below, which the satellite batch's
  conflict-check found duplicates `crypto_alpha_research_2026_07_24.md`'s own open `[RESEARCH] P2` todo — see register §
  A for the full citation.
- [x] ✅ [CODE] P2.11.19. **Reversion execution-timing model — SHIPPED 2026-06-22: execution-service@4b8dc545.** New
      `backtest_v2/reversion_timing.py` (`time_reversion_fill`): the research z-score `-(p−mean_W)/std_W` times the fill
      to the first over-extension bar in the trade's favour (BUY at z>thr / SELL at z<−thr) within the window, **CLAMPED
      so smart ≥ benchmark by construction → `execution_alpha_bps ≥ 0`** (a fired-but-snapped-back bar clamps to the
      benchmark, alpha 0; no over-extension → honest BENCHMARK_FALLBACK). Decimal-exact + no now()/random → ε=0
      (paper↔batch determinism preserved); wired into `smart_fill_replay.py` (GroupC) + `compute_execution_alpha`. Unit
      tests (over-extension → alpha>0; no-fire → benchmark) GREEN, full QG passed. **Wire the reversion signal as the
      execution-timing model in execution-service GroupC smart-matching** (research 2026-06-22, root `_ic_test.py`). The
      SAME reversion z-score, used to TIME fills on the book's existing turnover (not as a standalone trade), captures
      **~+1.5 bps/leg** vs naive window-close fills (z>0.5 +1.4bp fires 100% of 4h windows; z>1.5 +1.7bp fires 96%) — a
      buy waits for an intraday over-extension-down within the rebalance window, a sell for an over-extension-up. This
      is **riskless execution alpha** (the trade happens regardless → no standalone round-trip cost, no
      adverse-selection/cost-floor problem) on every strategy's turnover (cs / trend / basis), compounding into
      net-Sharpe. This is PRECISELY the citadel "execution alpha" layer (`execution_alpha = smart − benchmark`) —
      implement the reversion z-score as the **smart-matching execution-timing model in execution-service GroupCRunner**
      (the smart-fill entrypoint shipped @3d7d760c, P11.6-retry), bounded by the rebalance-window timeout (fall back to
      benchmark fill if no over-extension fires). batch=live one path; the improvement surfaces as `execution_alpha_bps`
      in the ledger (P11.6). Repo: execution-service. Evidence: execution-timing table in `_ic_test.py`. Higher
      immediate value than the marginal standalone fade (which is shelved — see Progress Log 2026-06-22 "intraday
      reversion is a feature/exec-timing signal, not a standalone trade").
- [x] ✅ [CODE] P2.11.21. **Unify execution into ONE central candle-driven 1m-fill engine + per-strategy intent**
      (operator 2026-06-22). **ENGINE SHIPPED 2026-06-22 — execution-service@c50c467d:** shared
      `backtest_v2/candle_fill_engine.py` (`replay_candle_fill`) with the `ExecutionIntent` StrEnum universe —
      `IOC_TAKER` (cross, bar-0 full fill), `RESTING_LIMIT_TAKER` (residual rests at cross, fills on trade-back, never
      misses), `LIMIT_MAKER` (posted `improve_bps` inside the cross, fills at the EXACT posted price on the first 1m bar
      trading through by `FILL_THROUGH`=0.25bp, **MISSES on adverse selection**). Lifts the `_extreme_ml.py`
      1m-trade-through mechanism into GroupC, consumes canonical `CanonicalOHLCV`, Decimal/ε=0, 12 unit tests GREEN,
      basedpyright clean. Generalizes the shipped `reversion_timing` (4b8dc545). **REMAINING:** (a) wire the
      per-strategy `execution_intent` flag into each strategy + the `smart_fill_replay` call; (b) **download EVM-perp +
      basis spot/perp 1m candles** for the full cross-strategy style sweep (CeFi spot majors + 30 perp 1m series already
      cached, e.g. `perp_BTC_1m` 1.7M bars 2020→2026; gap = the EVM perps + basis pairs — the e2e-testing download); (c)
      apply the cost corrections at the central model (basis 5bp/leg×2, on-chain 1bp — measured per the honest book
      +110% on CAP / Sh 1.93 / -10% maxDD). Today the RESEARCH customises fills per leg (cs maker-25% / ext taker /
      basis maker-1bp / on-chain maker-0.5bp) — that's a measurement scaffold, NOT production. Production =
      execution-service GroupC: the strategy declares an **intent** (maker-inside-N-bp / taker-cross; urgency picked
      from a universe) and **one** engine executes uniformly by **replaying post-signal 1m candles** — fill on the first
      bar trading through the resting order, **MISS (~10%) on adverse selection** (price runs away favorably; driven by
      liquidity+price on the 1m bars, NOT a flat haircut). `_extreme_ml.py` (ext leg: limit rests, fills on 1m
      trade-through) is the working template; generalise it to all legs. **Download 1m candles wherever missing** (EVM
      perps for on-chain, spot+perp for basis) so every fill is MEASURED like the agent's 97 netflow names
      (2bp-inside-mid → 0.90 fill on real Binance 1m OHLC). **Cost corrections (apply at the central model, fee tier set
      ONCE globally):** on-chain maker **1bp** (not 0.5 — exchange floor); basis **5bp/leg ×2 + impact** (both spot+perp
      legs fill to stay delta-neutral → re-cost halves basis: +31%→+11-16% on CAP, Sharpe 15→4.5-7, since it turns 48x
      notional/yr — a slower basis rebal recovers some). Repo: execution-service (GroupC) + e2e-testing (1m-candle
      download + per-leg fill replay). Composes with P2.11.19. **Execution-intent UNIVERSE — sweep per strategy,
      MEASURED via the 1m replay, pick best/worst (operator 2026-06-22):** (a) **IOC taker** — cross, full immediate
      fill, pay spread+impact; (b) **resting-limit taker** — marketable/cross, but unfilled residual RESTS + fills on
      subsequent 1m candles (not cancelled); (c) **limit {0, 0.5, 1, 2} bp inside the taker/cross price** — maker,
      posted passive, fills on the first 1m bar trading through, can MISS on adverse selection (price runs away). The
      strategy declares which intent it uses (its urgency); the engine measures all and the best is the per-strategy
      verdict — e.g. ext-REVERT wants maker-inside (patient fade), ext-CONTINUE wants taker (urgent with-trend).
      **`_extreme_ml.py` ALREADY implements this exact mechanism** (the extreme triple-barrier 3-class model:
      REVERT→maker-inside with an `improve_bp` sweep + `FILL_THROUGH`=0.25bp + the limit RESTS and fills on ANY 1m
      trade-through within order-life; CONTINUE→taker; NEITHER→skip/ML-gate). The build is to **LIFT that mechanism out
      into the shared GroupC engine** + expose the intent as a per-strategy flag — NOT write new. Correct the "ext
      (reversion)" mislabel → "ext (extreme triple-barrier: continue/revert/neither)" in the plots/docs as part of this
      (research plots already fixed 2026-06-22).

- [ ] [CODE] P2.11.15. **cs leg 2026 drag — longer-horizon TARGET retrain in `_panel.py`** — the cross-sectional ML book
      (cs) is the single worst leg in the 2026 selloff (the XS signal mis-bets when dispersion collapses). The span-7
      EWMA denoise (shipped) is the 80% cheap fix; the proper fix is retraining the pooled LightGBM on a longer-horizon
      return target so the signal is less whipsawed by the noisy 15m next-bar label. No lookahead (trailing features,
      shifted target; IS-select 2023-24 / OOS-validate 2025-26). Repo: features/strategy research (`_panel.py`).

- **[UI] P2.14.** Prod UI selector resolves the 14-strategy run, not the 145-run (found 2026-06-21). The CRA API
  correctly resolves + serves the newest run `paper-20260621225959-e86237f7` (145 strategies / 7 archetypes — verified
  authenticated: `net-views.run_id` = the 145-run on every call). But the prod odum-portal UI's strategy selector
  renders only the 14 CARRY_STAKED_BASIS strategies of an OLDER run (`paper-20260621171725-fcf31316`). The UI calls
  SAME-ORIGIN `/api/*` (Next.js server-side proxy to the CRA — no `*_API_URL` env on odum-portal, so the target is baked
  in next.config rewrites). DIAGNOSIS: the selector's endpoint (instructions/manifest list) resolves or caches a
  different run than the CRA `per-strategy` SSOT `resolve_canonical_run` — likely (a) the proxy points at a different
  CRA, (b) a Next.js/React-Query cache, or (c) the selector endpoint doesn't key off `resolve_canonical_run`. FIX:
  confirm the next.config `/api` rewrite target == the deployed CRA, ensure the selector reads the same
  `resolve_canonical_run` SSOT, bust any cache. The 145-run data + ε=0 + all ledgers are correct in GCS + served by the
  CRA — this is purely UI run-resolution. Repo: unified-trading-system-ui (+ verify next.config proxy target).
  **EXTRACTED 2026-08-08** → moved verbatim to `citadel_satellite_ao_dispatch_batch1_2026_08_08.md`.

- [x] ✅ [CODE] P2.15. **Match the e2e weighting: per-archetype RANK allocators, not FIXED equal-weight** — DONE,
      DUPLICATE of the shipped **P11.15** (`paper_universe` `allocator_archetype` default FIXED→rank; rank metrics from
      the same deterministic captured GCS rates → ε=0 preserved). Closed in the 2026-06-23 register cleanup. (operator
      2026-06-22: "in our e2e plots we picked several venues for e.g. basis and WEIGHTED across opportunities — I
      thought that was a production config"). CONFIRMED: a catalogue `@`-qualified id is a per-(venue,coin) CANDIDATE
      leg (145 of them); the e2e "strategy" is the ARCHETYPE + its rank allocator that ranks+weights across the cohort
      (`portfolio_allocator/archetypes_rank.py` 2-stage: rank groups → top-N → weight-by-metric — long lowest / short
      highest funding, rank-by-net-carry, inverse-vol). Production HAS this. GAP: `paper_universe.PaperUniverseConfig`
      defaults to `AllocatorArchetype.FIXED` (equal-weight) — so the paper book equal-weights all legs instead of the
      e2e opportunistic weighting. FIX: default each archetype to its rank allocator; the rank METRICS come from the
      SAME deterministic captured GCS rates (funding/carry/vol per window) → **ε=0 preserved** (pure fn of the window,
      not live calls — the FIXED default's determinism worry was overcautious). Verify ε=0 batch-rerun holds with rank
      weights. Repo: strategy-service (paper_universe allocator default + per-archetype rank wiring).
- [x] ✅ [UI] P11.16. **Archetype-level default view + all-145 per-strategy — DONE + prod-verified** (CRA@336e2dc rev
      00016-lcj = 145/7; ui@2f4c7016 = 7 books→legs w/ weights; browser-verified). Orig:**Default the paper-trading view
      to archetype-level "strategies" (legs as drill-down)** — the headline selector should read ~7 weighted archetype
      strategies (the e2e "strategy" granularity), each expandable to its weighted per-(venue,coin) legs, rather than
      145 flat legs. The archetype roll-up already exists (P11.9-ui group-by-archetype) — make it the DEFAULT framing +
      label the legs "candidate legs / constituents", show each leg's allocator weight. Repo: unified-trading-system-ui
      (playwright-gated). ALSO: the per-strategy rollup currently shows only 13 (the attribution-parquet subset for the
      145-run) — make it reflect ALL 145 by reading the manifest/instruction-ledger strategy_ids (or emit attribution
      for all 145), so the count + archetype grouping cover the full book.

- [x] ✅ [UI] P11.14-hook. **Prod paper-trading hooks now render REAL CRA data** — ROOT CAUSE (from the live console):
      `lib/api/mock-handler.ts`'s global fetch interceptor (NEXT_PUBLIC_MOCK_API=true) had no passthrough for
      `/api/client-reporting*`, so it returned empty `{}` → login got no access_token → every panel "Failed to load"
      with no network request. FIX (ui@f0ebd216): added `/api/client-reporting` to `realRoutePrefixes`. Now ALL 10
      ledger endpoints return 200, no errors, real CeFi venues render (odum-portal-00036-pzm). The full 4-part P11.14
      fix: isReportingLive hook gate + fs env-loader in next.config + rewrites-emit-in-mock + mock-handler passthrough.
      Verified browser-side. bugs are fixed (CRA reachable from the page: manual in-page fetch → 200, 13 strategies).
      But `useLedgerPerStrategy` / `useLedgerNetViews` etc. show "Failed to load" with NO `/api/client-reporting*`
      request issued, despite isMock=false (var inlined), clientId set (`?client=firm-paper-determinism`), no service
      worker, mock defined, fix code in the deployed chunks. Resolve from the LIVE browser console (the actual
      react-query error) — not headless inference. Likely candidates: an SSR/prefetch error, a QueryClient
      retry/throwOnError config, or the hook erroring in a transform before fetch. Repo: unified-trading-system-ui.

- [x] ✅ [CODE] P2.17 (P11.17). **Structurally forbid the synthetic-input seam in PAPER/LIVE prod runs** — DONE + LANDED
      (`strategy-service@a786d463`, on origin/live-defi-rollout, QG-green). `run_paper()` (the PAPER/LIVE
      mode=`TradingMode.PAPER` engine path — paper≡live one path) now calls `get_synthetic_input_override()` and RAISES
      loud if a synthetic override is active before booking any ledger (`paper_run_handler.py:1143-1152`); regression
      `tests/unit/cli/handlers/test_paper_run_synthetic_guard.py`. Makes "paper reads exactly like live" structural, not
      flag-dependent (the live handler is gated on custody, shares this engine path). (operator audit 2026-06-22: "all
      reads should be live+batch from real prod sources/schemas/GCS paths; writes canonical with just the paper→live tag
      swap"). AUDIT RESULT — already canonical: reads resolve every bucket via `resolve_bucket_name`
      (perp-funding/dex-pools/market-data/lending, real prod schemas+granularity, honest-skip never synthetic); writes
      go through the shared `write_run_ledger` seam to the canonical `client-reports` ledger path
      (`ledger/client_id=/run_id=/ledger_type=`) with `mode=TradingMode` (PAPER→LIVE swap; paper/batch IDENTICAL shape).
      The e2e synthetic seam (`set_synthetic_input_override`/`--synthetic-input`) is opt-in + default-None (only tests +
      the CLI flag set it) → OFF in the prod paper job. HARDENING: add a guard so `get_synthetic_input_override()` MUST
      be None when `mode ∈ {PAPER, LIVE}` (raise if a synthetic override is active in a prod-mode run) — makes "paper
      reads exactly like live" structural, not flag-dependent. Repo: strategy-service + unified-trading-library.

- [x] ✅ [UI] P11.18. **Archetype-grouped WEIGHTED PnL-over-time plot + batch/paper symmetry overlay** — SHIPPED
      unified-trading-system-ui@423e237d (PnlTimeseriesChart archetype-weighted lines via buildWeightMap +
      PaperBatchOverlayChart). VERIFIED LIVE on prod (odom-portal): the PnL-over-time panel renders the
      archetype-weighted lines + the "Paper vs batch (rerun) overlay" carrying the **"ε=0 PROVEN — paper ≡ batch"**
      badge. pw:L2 ✓ (21 passed) | regression: tests/smoke/paper-trading-ledger.smoke.spec.ts (P11.18 cases). (operator
      2026-06-22: "where is our grouped PnL plots of the strategy_ids in strategy-archetype groups where we weight
      between strategy_ids ... I don't see it on the page"). Today: a single selection-filtered PnL series +
      `BatchPaperPanel` showing the `live−batch=(paper−batch≈0)+(live−paper=exec α)` identity as NUMBERS. ADD: a
      multi-line PnL-over-time CHART with ONE line per ARCHETYPE BOOK (the allocator-weighted sum of its strategy_id
      legs — the e2e weighting), toggle archetype↔leg↔coin; AND overlay the BATCH-rerun PnL line vs the PAPER line so
      the ε=0 symmetry is visually legible per archetype (not just a verdict badge). Repo: unified-trading-system-ui
      (consumes /pnl-timeseries + /backtest + /per-strategy weights; playwright-gated).
- [x] ✅ [CODE+UI] P11.19. **Paper-trading data-quality + VM events stream panel** — SHIPPED + VERIFIED LIVE on prod.
      (a) CRA `GET /clients/{c}/data-quality` (client-reporting-api@7f3ac8a) = skipped_specs grouped by
      archetype/venue/reason + manifest coverage + alerting-service alerts merged (best-effort). **CRITICAL crash-fix:
      `coverage.by_archetype` was emitted as a dict → the UI's `DataQualityCoverageRow[].reduce` threw → the WHOLE paper
      dashboard white-screened ("Something went wrong"). Fixed CRA to emit the canonical array shape (image
      `client-reporting-api:dqarrayfix` deployed to prod rev 00018-njv; source quickmerge PENDING a live UTL-dep WIP
      settling — fix is LIVE regardless) + UI Array.isArray guard (unified-trading-system-ui@85369f75) + CRA unit-test
      now asserts the array contract (the smoke spec used the mock fixture which was already array-shaped, so it missed
      the real-data dict — the CRA test closes that gap).** (b) UI "Data Quality & Alerts" panel
      (unified-trading-system-ui@423e237d). VERIFIED on prod: headline **145/342 drivable · 197 skipped**, 12
      per-archetype coverage rows, 8 skipped-by-reason groups / 197 skipped (venue,coin) rows (top reason
      `no_gcs_data_in_window:2026-05-16..2026-05-22`, 127 cells), alerts section renders (honest `unavailable` — see
      P11.20). pw:L2 ✓ (21 passed) | regression: tests/smoke/paper-trading-ledger.smoke.spec.ts (P11.19 cases) +
      client-reporting-api/tests/unit/test_data_quality.py (array contract). Repo: client-reporting-api +
      unified-trading-system-ui.
- [x] ✅ [INFRA] P11.20. **Live VM alert STREAM into the data-quality panel** — SHIPPED + VERIFIED LIVE. Root cause of
      the prior `alerts_source: unavailable`: the CRA route hardcoded the k8s DNS `http://alerting-service:8080` which
      does NOT resolve from Cloud Run. FIX (client-reporting-api): repoint `_live_alerts` at the **reachable, public**
      deployment-api unified alert ledger (`uts-shared-deployment-api…/api/alerts` — the SAME source deployment-ui's
      monitoring pane shows: CI/CD + vm_down + consolidator_down + worker_liveness + git_health) + a `_map_alert` that
      projects the ledger `AlertEntryDict` → the UI `DataQualityAlert` closed shape (severity coerced to
      critical|warning|info). VERIFIED on prod (rev `client-reporting-api-00019-8k2`): `alerts_source: deployment-api`
      (was "unavailable"); 0 active alerts → panel shows "fleet is clean" honestly. The alert FEED is now live; it
      populates when the fleet emits events. Remaining (NOT blocking): the per-env URL is a constant default (P11.21
      folds it into the deployment-api-SSOT client); the per-epic data fleet that emits ADAPTER_FETCH_FAILED/
      honest-absence is post-cutover/not-running so the stream is empty until it runs. Repo: client-reporting-api.
      regression: client-reporting-api/tests/unit/test_data_quality.py (alerts merge + shape-map +
      degrade-to-unavailable).
- [x] ✅ [CODE+UI] P11.21. **Reconcile the paper data-quality panel against the deployment-api data-status SSOT** —
      SHIPPED + VERIFIED LIVE (operator 2026-06-22: "lets use SSOT so if it breaks there we fix at the source"). CRA:
      new `core/deployment_api_client.py` — ONE typed client for the deployment-api (consolidates P11.20 alerts + P11.21
      coverage, single base-URL home); the data-quality endpoint now returns `manifest_coverage` (the corpus manifest
      4-state per asset_group: `captured`/`empty_confirmed`/`attempted_failed`/`expected_unattempted`/ `coverage_pct`)
      from `/api/data-status/honest-coverage` — the SAME SSOT the deployment-ui data-status bars read. VERIFIED on prod
      (rev `client-reporting-api-00020-9sp`): `manifest_source: deployment-api`, 5 AG rows (cefi 11.68%, defi, tradfi,
      sports, prediction) — identical numbers to the deployment-ui page. UI: dual-lens panel
      (`paper-trading-ledger-panels.tsx`) — run lens ("this run could drive", skipped_specs) + corpus lens ("data
      EXISTS", manifest SSOT) with an "SSOT unavailable" honest-degrade. pw:L2 ✓ (21 passed) | regression:
      tests/smoke/paper-trading-ledger.smoke.spec.ts (data-quality-manifest) + client-reporting-api/tests/unit/
      test_data_quality.py (TestDeploymentApiClient + manifest_coverage). Repo: client-reporting-api (live) +
      unified-trading-system-ui (landed LDR, prod UI deploy in flight). **CRA source-quickmerge LANDED**
      (`client-reporting-api@5a65b10`, on origin/live-defi-rollout — verified `merge-base --is-ancestor`). NOTE: per-env
      base URL is a constant default; the `UnifiedCloudConfig` URL field is now done as P11.21-polish (see below).
- [x] ✅ [CODE][UI] P2. **Min-coverage threshold — "drivable-but-thin" state** (item 11.22) (operator 2026-06-22: "is it
      only 100% or is >80% still relevant for backtest"). Today a spec is BINARY drivable-vs-skipped: any data in window
      → runs (drivable, regardless of how complete); zero → skipped. ADD a configurable per-archetype
      min-window-coverage threshold (e.g. ≥80% of expected bars present) → a third "drivable-but-thin" state so a
      backtest run on sparse data is flagged, not silently trusted. Compute window-coverage % at the engine's
      honest-skip decision (`paper_universe._skip_reason_for_spec` + the `run_paper` data-fetch), carry it on the spec,
      surface it in the data-quality panel + gate weighting. Repo: strategy-service (threshold + coverage %) +
      client-reporting-api (surface) + unified-trading-system-ui (panel). NICE-TO-HAVE (paper book is honest binary
      today). **SHIPPED 2026-06-23** — per-archetype min-window-coverage threshold (default 80%; cross-sectional
      funding/price dispersion 85%; `PaperUniverseConfig.min_window_coverage` is the operator override) → the third
      `drivable_thin` state. Coverage % = `len(market_data_days) / expected_window_days` computed in `run_paper` for
      every DRIVEN spec (`compute_spec_coverage`), pinned to a new `spec_coverage/{run_id}.json` sidecar; thin is a
      SUBSET of drivable (a thin spec STILL books trades — ε=0 untouched, flag-only). CRA `read_spec_coverage` folds it
      into the data-quality API (`coverage.drivable_thin` per-archetype + a sorted `thin_specs` list, worst coverage
      first); the UI panel renders an amber "thin" sub-bar + headline count + a "Drivable-but-thin specs" table showing
      each (venue, coin) coverage% `<` threshold. Evidence: unified-trading-library@90697df6 (`write_run_spec_coverage`
      sidecar writer + unit test; QG green 167s) · strategy-service@4dc69827 (`compute_spec_coverage` +
      `min_window_coverage_for` + `run_paper` wiring + 6 tests; QG green 180s) · client-reporting-api@9a631a4
      (`read_spec_coverage` + `_thin_rows` + `drivable_thin`/`thin_specs` route surface + 4 tests; QG green 88s) ·
      unified-trading-system-ui@558127f5 | pw:L2 ✓ (70/70 `tests/smoke/` serial — the all-cores-parallel local flakes
      reproduce on baseline with this change stashed, so unrelated) | regression:
      tests/smoke/paper-trading-ledger.smoke.spec.ts (the "drivable-but-thin state with coverage %" P11.22 case).
- [x] ✅ [UI] P11.23. **deployment-ui "Backend unreachable" debounce + form a11y** — SHIPPED + VERIFIED LIVE. Operator
      2026-06-22: the data-status page flashed a red "Backend unreachable — signal timed out" banner + "Unknown error"
      detail even though the backend was up (coverage bars rendered; min-instances=1, `/api/health` 46ms warm). Root
      cause: a SINGLE transient `/api/health` poll timeout (a heavy data-status manifest-merge briefly saturating the
      worker) LATCHED the red banner for a full 30s poll interval. FIX (`MockModeBanner.tsx` `useBackendHealth`):
      debounce — keep last-good state + fast-retry on the 1st failure, go red only on the 2nd consecutive (a genuine
      outage still surfaces within ~4s of the 2nd poll). ALSO fixed the operator's console a11y warnings — `id`/`name` +
      label association on the 5 data-status filter inputs (`DataStatusTab.tsx`: symbol/venue search, start/end date,
      freshness). LANDED on LDR (MockModeBanner debounce + DataStatusTab a11y both confirmed on origin/LDR) + LIVE via
      the deployment-api rebuild (rev `uts-shared-deployment-api-00079-qg6`; served bundle confirmed to carry both).
      regression: src/components/MockModeBanner.test.tsx (8 pass) + the data-status a11y ids. Repo: deployment-ui.

## Temporary states + their canonical follow-up plans

- P7.3 (live leg) is `BLOCKED-OPERATOR-DECISION` until a live wallet/custody is approved (hard-stop: wallet keys are
  human-only). The paper↔batch determinism proof (P7.2) does not depend on it. **Reviewed 2026-07-28 (operator
  gate-cleanup pass) — confirmed remains a PERMANENT hard-stop**: live wallet/custody approval (Copper/CEFFU) is named
  in CLAUDE.md as a permanent, human-only hard-stop alongside force-push-main and 1.0.0 graduation, regardless of how
  complete the rest of the reconciliation spine is (P7.1/P7.2 are both DONE/proven ε=0). Not retagged, not unlocked.

## Progress Log

> **History moved 2026-07-24**: the full dated Progress Log (2026-06-19 through 2026-06-22, zero open todos) was
> extracted verbatim to keep this plan under its line-count cap — see
> [`plans/archive/2026_07/citadel_paper_batch_live_reconciliation_history_2026_07_24.md`](/plans/archive/2026_07/citadel_paper_batch_live_reconciliation_history_2026_07_24.md)
> for the full historical narrative of how the determinism spine was built.

- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; re-read; verdict unchanged. This pass DELETED the
  duplicated truncated `- [ ] [CODE] P2.11.18` fragment line the 07-30 marker had only noted, so the open-todo count
  drops 11 -> 10 and backlog-regen can no longer derive a phantom duplicate task): KEEP-NA, valid — carries P7.3 /
  P2.7.3 live-wallet+custody `BLOCKED-OPERATOR-DECISION`, re-confirmed 2026-07-28 as a PERMANENT human-only hard stop.
  NOTE a literal duplicated `- [ ] [CODE] P2.11.18` line (the first is a truncated fragment of the second) inflates this
  doc's open-todo count by 1.
- **context-scout 2026-08-01**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- dropped 2 narrower codex pointers + 1 epic to
  make room for the determinism-spine's real source home (batch-live-reconciliation-service `engine/` +
  `stage5_results_writer.py`, both named in the doc's own Progress Log), since prior scope was codex/plan-only.
- **na-eligibility-audit 2026-08-08 (cross-cutting tranche)**: KEEP-NA, valid — reaffirms 2026-08-02 (unchanged): 10
  open todos span Phase-2 determinism-spine work needing a cross-repo blast-radius pre-audit, the permanent P7.3/ P2.7.3
  live-wallet/custody `BLOCKED-OPERATOR-DECISION` hard-stop, an explicit operator-confirm-capability-profile ask
  (P2.11.20), and ML research retrain+validate judgment calls (P2.11.15/18).
- **2026-08-08 (interactive session, operator-authorized satellite extraction)**: the operator explicitly authorized
  splitting this doc's register-§A "Agent-shippable infra/code (NO operator gate)" items into their own AO-dispatchable
  satellite, since every prior `/na-eligibility-audit` pass correctly kept this WHOLE DOC `assigned_vm: NA` (justified
  alone by P2.7.3's permanent live-wallet hard-stop) without ever addressing why the agent-shippable items stayed
  bundled in rather than being split out. Read this doc end-to-end to confirm the operator's named 8-item list against
  its own current text, then ran the shared conflict-check protocol
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) against every
  `assigned_vm: planning` plan in `parent_epic: batch_live_symmetry_master` plus corpus-wide fingerprint greps per
  candidate. **Result: 7 of the 8 named items extracted** (P2.1, P2.2, P1.6, P2.11.16, P2.11.20, P2.11.18 [scope-trimmed
  — its retrain sub-step stays here], P2.14) to
  [`citadel_satellite_ao_dispatch_batch1_2026_08_08.md`](/plans/archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08.md)
  (+ gated finalize twin). **1 held back on a genuine conflict**: P2.11.15 ("cs-leg longer-horizon TARGET retrain in
  `_panel.py`") near-verbatim-duplicates `crypto_alpha_research_2026_07_24.md`'s own open `[RESEARCH] P2` todo
  (line 536) — left unchanged here, not extracted, per the conflict-check protocol's "verbatim/near-verbatim duplicate
  claim → do NOT draft a competing todo" rule. **Also found + corrected**: register § A additionally listed 4 stale
  bullets (`_mom_tb.py` bug, combined-book vol-norm bug, cs ensemble `alt_*`/`altfull_*` gap, HYPE+post-2024-cohort gap)
  that were already migrated to and live as open checkboxes in `crypto_alpha_research_2026_07_24.md` (2026-07-24
  section-C move) — never orphaned, removed from this register's listing as still-open-here. This doc's own open-todo
  count drops from 10 to 3 (P2.7.3, P9.2, P2.11.15); the extracted 7 are now tracked + dispatchable in the satellite
  doc. This doc's `assigned_vm: NA` classification is UNCHANGED and remains correct (P2.7.3 alone still justifies it).
- **operator ruling 2026-08-08** (NA-corpus blocker digest, cross-cutting round 5, id=47): re-confirmed — live wallet +
  custody (Copper/CEFFU) approval not yet ready, P2.7.3 stays `BLOCKED-OPERATOR-DECISION` pending. No change to status;
  the paper↔batch-rerun ε=0 proof (P2.7.1/P2.7.2) remains unaffected since it does not depend on live custody.
