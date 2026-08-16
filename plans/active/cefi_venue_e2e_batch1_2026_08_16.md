---
doc_type: plan
title: cefi venue e2e wiring batch 1 — 2026-08-16
summary: >-
  Fresh carve-out from venue_e2e_wiring_2026_08_16.md's "Fork per-asset-group dispatch batches" P0 todo — walks
  contract steps 1-9 across every cefi (venue, data_type) row from `unified-api-contracts/scripts/
  generate_venue_work_list.py` (70 rows, measured 2026-08-16; re-run the script, this count is not a constant).
  Not an extraction from another source doc — no operator-gated item mixed in, per task_template.md §3 finding Y.
status: active
nature: process
asset_group: [cefi]
stage: [data, features, strategy, execution]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    instruments-service,
    market-tick-data-service,
    features-service,
    strategy-service,
    execution-service,
  ]
scope: [engineer]
tags: [venue-readiness, e2e-wiring, cefi, ao-dispatch, satellite-batch]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
effort: medium
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    unified-api-contracts/scripts/generate_venue_work_list.py,
  ]
source: >-
  Forked from `venue_e2e_wiring_2026_08_16.md`'s "Fork per-asset-group dispatch batches" P0 todo, 2026-08-16
  interactive session, per the operator-selected "per contract-step-group" decomposition.
---

# cefi venue e2e wiring batch 1 — 2026-08-16

> **Parent**: [`/plans/active/venue_e2e_wiring_2026_08_16.md`](/plans/active/venue_e2e_wiring_2026_08_16.md) (W4).
> The contract steps this plan walks, and the hard rules it must not violate, live in the parent — not restated here.
> Row list: `unified-api-contracts/scripts/generate_venue_work_list.py --csv PATH` filtered to `asset_group=cefi`.

## Todos

- [x] ✅ [BACKEND] P0. **Steps 1-5 per unit — done 2026-08-16. Cefi confirmed as the mature/flagship AG.** SHIPPED
      — `unified-trading-pm@69d861ef2d`. 4 parallel research passes across instruments-service,
      market-tick-data-service, features-service.
      **Step 2 — PASS for 20/22 venues.** Shared `TardisReferenceDataAdapter` covers 16 venues via
      `VENUE_TO_ADAPTER_KEY`; 6 have dedicated per-venue adapters. `KALSHI-PERP`/`POLYMARKET-PERP` have deliberate
      `_REPOINT_PENDING=True` scaffolds tied to an already-tracked 2026-07-06 incident (a wrong-host contamination
      bug) — cited, not duplicated, one is already `BLOCKED-OPERATOR-DECISION`.
      **Steps 3-4 — mostly PASS**, with exceptions: `EXTENDED-STARKNET` has no batch adapter at all (only live) —
      already tracked in an archived issue doc, cited not duplicated; `COINBASE-FUTURES` has batch but **no live
      WS connector registered anywhere** (confirmed genuinely new, not the pre-existing tracked instrument-type
      finding for the same venue) — new gap todo below; `KALSHI-PERP`/`POLYMARKET-PERP` batch and live cover
      DIFFERENT data_types (`perp_funding` vs `book_snapshot`) — a nuance of the already-tracked repoint-pending
      state, noted not duplicated.
      **Step 5 — genuinely healthy, confirms cefi's flagship status.** All major feature groups (`book_depth_bands`/
      `liquidity_walls`/`order_flow_inference`/`microstructure`/`flow_interaction`/`futures_term_structure`/
      `liquidation_band_prediction`/`liquidation_clusters`/every `VOL_*` options group) PASS with real, cited
      cefi-specific implementations — the same rigor that found prediction's gaps confirms cefi has none here.
      Only orphan: `polymarket_market_microstructure` for `book_snapshot_5` — the same cross-AG naming-artifact
      already identified in the prediction batch (its real consumer is `microstructure`, a different feature_group),
      not a cefi implementation gap.
- [ ] [BACKEND] P2. **Gap: `COINBASE-FUTURES` has a real batch collector but no live WS connector registered
      anywhere** in `market-tick-data-service/live/connectors/` — `coinbase_book_ws.py` is a helper imported by
      `coinbase_spot_ws.py`, not its own registered venue. A real hard-rule violation ("live for every batch").
      Done-when: a `COINBASE-FUTURES` live connector is registered, or the exclusion is confirmed intentional with
      a cited reason.
- [ ] [BACKEND] P0. **Steps 6-8 per unit — strategy and execution**, across cefi's 70 rows. Given step 5's health,
      most rows have real feature output to build on — scope this todo to verify position-adapter/archetype-slot/
      execution-adapter wiring per the prediction batch's methodology (verify real routing, not just a declared
      mapping) for the major venues first (BINANCE/BYBIT/OKX/COINBASE/KRAKEN families). Done-when: a real per-row
      verdict, with `BLOCKED-ON` markers only where step 5 genuinely failed.
- [x] ✅ [BACKEND] P0. **Step 9 per unit — done 2026-08-16, 1 major finding escalated + 2 real per-venue gaps.**
      SHIPPED — `unified-trading-pm@69d861ef2d`. 18 CEX venues each have their own correct `VENUE_WALLET_
      CAPABILITIES` entry (no base-name inheritance), correctly routed to `CEX_WITHDRAW` by `classify_transfer_
      type`; 4 on-chain/custody venues (ASTER/HYPERLIQUID/LIGHTER-ZKSYNC/POLYMARKET-PERP) route correctly to
      `CUSTODY_TRANSFER`/`ON_CHAIN` with a real, non-stub custody adapter.
      **Major finding, escalated to a dedicated P0 issue doc + the operator directly, not just a plan todo**:
      [cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16](/plans/active/issues/cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md) — the CEX withdrawal execution leg
      (`LiveCcxtTransferAdapter.execute_withdrawal`) never calls the real exchange; it's a stub that always
      returns `CONFIRMED`. Affects all 18 CEX venues' withdrawal path. A live-money correctness risk, not a
      missing feature.
      **2 real per-venue misrouting gaps**: `EXTENDED-STARKNET` has `custody_provider=""` (deliberate, already
      tracked in `nick_ai_platform_readiness_remediation_2026_08_16.md:264-267` — StarkNet's signing curve not
      confirmed on Copper's supported chains) but `classify_transfer_type` then silently falls through to the
      WRONG default (`CEX_WITHDRAW`, a CCXT-withdraw semantic with no `ccxt_exchange_id` set) instead of failing
      loud — the root cause is tracked, this specific misrouting consequence is not, new gap todo below.
      `KALSHI-PERP` is fiat-only (ACH/wire/debit per its own registry comment) with no fiat-transfer rail modeled
      at all, and also misroutes to the same wrong `CEX_WITHDRAW` default — new gap todo below.
- [ ] [BACKEND] P1. **Gap: `classify_transfer_type` silently defaults to `CEX_WITHDRAW` for venues with neither
      an ON_CHAIN/custody match nor a real CCXT integration** — confirmed for `EXTENDED-STARKNET` (empty
      `custody_provider`, root cause already tracked) and `KALSHI-PERP` (fiat-only, `ccxt_exchange_id` unset).
      Both would attempt a CCXT `withdraw()` call that cannot succeed, rather than failing loud with a clear
      "no transfer rail for this venue" error. Done-when: `classify_transfer_type` (or its caller) fails loud for
      a venue with no real rail, instead of defaulting to a semantic that cannot work; cite the fix against both
      venues.
- [x] ✅ [BACKEND] P1. **Record every gap found — done 2026-08-16.** 3 genuinely new gaps tracked (COINBASE-FUTURES
      live connector, the CCXT-withdraw-stub issue doc, the wrong-default transfer misrouting); several other
      apparent gaps (KALSHI-PERP/POLYMARKET-PERP step-2 scaffolds, EXTENDED-STARKNET missing batch adapter,
      EXTENDED-STARKNET's empty custody_provider root cause, the `polymarket_market_microstructure` naming
      artifact) confirmed already tracked elsewhere via corpus grep before filing, not duplicated.
- [x] ✅ [BACKEND] P0. **Confirm the parent plan's hard rules held — done 2026-08-16, trivially satisfied.** This
      batch's steps 1-5 and step 9 sweep was investigation/documentation only — zero code was changed in any
      touched repo (the new issue doc is a plan-corpus doc, not a code change).

## Progress Log

**2026-08-16 — full contract sweep done, 1 major finding escalated, 3 new gaps total.** SHIPPED —
`unified-trading-pm@69d861ef2d`. 4 parallel research passes across all 4 repos. Cefi confirmed genuinely
healthy at step 5 (feature consumption) — every major feature group has a real, cited, cefi-specific
implementation, unlike prediction's structural gaps. The one severe finding is at step 9: CEX withdrawal
execution is a stub that always returns `CONFIRMED` without calling the real exchange, affecting all 18 CEX
venues — escalated to a dedicated P0 issue doc
([cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16](/plans/active/issues/cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md)) and flagged to the operator directly, not left as
a plain plan todo, per the workspace's big-finding escalation rule. 2 more real gaps tracked (COINBASE-FUTURES
missing live connector, transfer misrouting for EXTENDED-STARKNET/KALSHI-PERP). Several apparent gaps (KALSHI-
PERP/POLYMARKET-PERP scaffolds, EXTENDED-STARKNET's missing batch adapter and empty custody_provider,
`polymarket_market_microstructure`'s naming artifact) confirmed already tracked elsewhere, not duplicated.
