---
doc_type: plan
title: cefi venue e2e wiring batch 1 — 2026-08-16
summary: >-
  Fresh carve-out from venue_e2e_wiring_2026_08_16.md's "Fork per-asset-group dispatch batches" P0 todo — walks
  contract steps 1-9 across every cefi (venue, data_type) row from `unified-api-contracts/scripts/
  generate_venue_work_list.py` (70 rows, measured 2026-08-16; re-run the script, this count is not a constant).
  Not an extraction from another source doc — no operator-gated item mixed in, per task_template.md §3 finding Y.
status: complete
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
last_updated: "2026-08-17"
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
- [x] ✅ [BACKEND] P2. **Gap: `COINBASE-FUTURES` has a real batch collector but no live WS connector registered
      anywhere** in `market-tick-data-service/live/connectors/` — `coinbase_book_ws.py` is a helper imported by
      `coinbase_spot_ws.py`, not its own registered venue. A real hard-rule violation ("live for every batch").
      Done-when: a `COINBASE-FUTURES` live connector is registered, or the exclusion is confirmed intentional with
      a cited reason. **Connector registered — BLOCKED-CREDENTIALS, SHIPPED
      `market-tick-data-service@75ef3ef084`.** Live-verified against production (no fixture):
      `wss://ws-md.international.coinbase.com` (Coinbase INTX) accepts a structurally-valid
      `{"type":"SUBSCRIBE","product_ids":[...],"channel":"<name>"}` message (unmarshal succeeds — confirmed via the
      server's own "Failed to unmarshal" vs "Unable to authenticate" REJECT-reason distinction) but rejects EVERY
      channel tested (`MATCHES`/`INSTRUMENTS`/`LEVEL1`/`TICKER`/`FUNDING`) with `"Unable to authenticate"`, including
      with plausible `key`/`passphrase`/`signature`/`time` auth fields attached — unlike sibling COINBASE-SPOT/
      COINBASE-CDE connectors, INTX exposes no public/unauthenticated market-data channel at all, and no INTX
      credential is provisioned anywhere in this fleet (execution-service's transfer wiring only enumerates
      `coinbaseinternational` as a CCXT withdraw-venue string, it loads no credential for it). New file
      `coinbase_intx_ws.py` registers a Protocol-conforming BLOCKED-CREDENTIALS scaffold under venue key
      `COINBASE-FUTURES` (mirrors the `EXTENDED-STARKNET`/`LIGHTER-ZKSYNC` precedent: connect/subscribe/unsubscribe/
      close work today; `stream()` no-ops + logs the credential gap until real INTX API credentials land and
      `_CREDENTIALS_AVAILABLE` is flipped) — deliberately does not fabricate an unverified WS auth signing scheme for
      a live-trading-adjacent data path. Credential ask to unblock: a funded Coinbase International Exchange account
      + issued API key/secret/passphrase, stored under a new GSM secret (suggested name
      `coinbase-intx-api-credentials`).
- [x] ✅ [BACKEND] P0. **Steps 6-8 per unit — done 2026-08-16, 0 of 12 major venues reach a complete
      end-to-end state.** SHIPPED — `unified-trading-pm@4686d503ad`. 3 parallel research passes — strategy-service
      (positions), strategy-service + unified-api-contracts (archetype/slot declarations — the prediction batch's
      citation of `unified-api-contracts` for `archetype_slots_*.py` was itself stale; those files live in
      `strategy-service`, corrected here), and execution-service (order execution) — scoped to the BINANCE/BYBIT/
      OKX/COINBASE/KRAKEN families (12 venues, 36 of cefi's 70 rows) per this todo's own scoping. Step 5 passed for
      every row in scope (confirmed by the steps 1-5 sweep above) — no `BLOCKED-ON` markers needed.

      **Step 6 — position read.** Batch + paper(testnet=false) PASS for all 12 (venue-agnostic
      `LedgerPositionAdapter`, real GCS ledger read, `position_interface/adapters/ledger.py`). **Live PASS for
      only 3/12** (BINANCE-FUTURES, BINANCE-SPOT, BYBIT) — the other 9 raise an unhandled `ValueError: Unknown
      venue` in `position_interface/factory.py::_get_cefi_adapter`'s `match v:` statement (spot-checked directly,
      `factory.py:44-84`): BINANCE gets `_futures`/`_spot` suffix variants, BYBIT/OKX match their bare form ONLY
      (`BYBIT-SPOT`/`OKX-FUTURES`/`OKX-SPOT`/`OKX-SWAP` unreachable despite a real `OKXPositionAdapter` existing),
      COINBASE/KRAKEN have no case at all. The real caller (`ReconciliationEngine.reconcile_all_positions`,
      `reconciliation_engine.py:127-137`) catches this `ValueError` per-position and `continue`s — a position at
      any of the 9 broken venues is **silently dropped from reconciliation**, no `DISCREPANCY`/`CRITICAL`
      snapshot, just a log line. Not hypothetical: OKX-FUTURES is a real target of live carry-strategy code
      (`target_universe/catalog_carry.py:245,471`).

      **Step 7 — archetype/slot eligibility.** Of the 8 archetypes the CSV's `archetype_consumers` column lists
      for these rows, **5 have ZERO real CEFI slot for any of the 12 venues**: `MARKET_MAKING_PREDICTION`
      (structurally scoped to `asset_group:PREDICTION` only in the real capability matrix — the CSV's "consumer"
      listing is a pure data_type-keyed false positive, the exact trap this todo's brief warned about, not a real
      gap), `MARKET_MAKING_INVENTORY_SKEW` / `MARKET_MAKING_QUEUE_MICROSTRUCTURE` / `VOL_TERM_STRUCTURE_ARB` (each
      "engine SHIPPED, NOT registered, matrix UNCHANGED" — already tracked in `v2_engine_venue_buildout_2026_06_15
      .md`, not duplicated here), and `LIQUIDATION_CAPTURE` (wired exclusively to DeFi protocols despite 5 CEFI
      venues declaring `liquidations` data with this as their sole consumer — genuinely new, gap todo below).
      `MARKET_MAKING_CONTINUOUS` is healthiest: real slots for BINANCE-FUTURES/BINANCE-SPOT/BYBIT/OKX-SPOT
      (`archetype_slots_cefi.py:104-125`, `target_universe/catalog_trading.py:371-416`), but OKX-FUTURES/OKX-SWAP
      are excluded from the perp-loop generator entirely (`catalog_trading.py:397-416` lists only
      `binance,bybit,hyperliquid` — no okx, despite the capability matrix claiming otherwise, a matrix/code drift),
      and COINBASE/KRAKEN never appear in any CEFI slot file. `CARRY_BASIS_DATED`/`_INV` only wire BINANCE (as the
      spot leg, paired with Deribit as the futures leg — so BINANCE-FUTURES's own `futures_chain` row isn't
      actually what feeds the archetype) via a legacy lowercase venue-token vocabulary with no confirmed
      normalization to this sweep's canonical dash-form IDs; BYBIT has zero presence in either. Gap todo below.

      **Step 8 — execution.** CEFI genuinely avoids the prediction batch's "old facade" disease — `TRADE` actions
      for all 12 venues DO route through the real `InstructionActionV2` family
      (`execution_service/api/external_instruction_api.py`) via a real single-factory CCXT pattern
      (`execution_service/trade_execution/factory.py::get_order_adapter`), not bespoke per-venue facades. But
      **order placement is only reachable for 3/12** (BYBIT, KRAKEN-SPOT, KRAKEN-FUTURES) — the identical disease
      as step 6: `get_order_adapter` is called with the canonical dash-suffixed venue string
      (`live_execution_handler.py:332-359`), but `CCXT_VENUES` only recognizes bare base names (`factory.py:36-45`)
      — 9/12 venues raise `ValueError: Unsupported venue` before a live order adapter is even built, even though
      the real per-venue CCXT adapter classes underneath are genuine (verified full method bodies for
      `binance_ccxt.py`, `bybit_ccxt.py`, `kraken_rest_adapter.py`). **Cancel and amend are broken fleet-wide for
      all 12 venues, independent of the above** — spot-checked directly: the only HTTP-reachable cancel/amend
      surface (`execution_service/api/manual_instruction_api.py:432,465`) is a hardcoded stub that logs an event
      and returns `{"status":"CANCELLED"}`/`{"status":"AMENDED"}` **without calling any adapter**, and `amend` has
      zero real implementation anywhere (only an orphaned, unused `Protocol` at `trade_execution/oms/protocols.py:
      22-23`) — the real per-adapter `cancel_order` methods are genuine (`binance_ccxt.py:270-306`, real CCXT
      calls) but never invoked by any production caller. Escalated as a dedicated P0 issue doc below — same
      "claims success, does nothing" shape as the already-fixed CCXT-withdraw-stub finding from step 9 below, just
      for order cancellation instead of fund withdrawal.

      **Net: 0 of the 12 major venues reach a genuinely complete end-to-end state** — worse than the prediction
      batch's 0/4, and a real correction to steps 1-5's "flagship, mature, healthy" framing: that framing was
      about DATA (reference/capture/features), which really is healthy; strategy+execution wiring for the SAME
      venues is not. Per-venue detail:

      | Venue | Position: live / batch+paper | Archetype (beyond MM_CONTINUOUS) | Execution: place / cancel |
      | --- | --- | --- | --- |
      | BINANCE-FUTURES | PASS / PASS | CARRY: wrong-leg-role, not a real futures-leg match | FAIL (venue-string) / FAIL (stub) |
      | BINANCE-SPOT | PASS / PASS | — | FAIL (venue-string) / FAIL (stub) |
      | BYBIT | PASS / PASS | CARRY: absent | PASS / FAIL (stub) |
      | BYBIT-SPOT | FAIL (unreachable) / PASS | ambiguous legacy-token match | FAIL (venue-string) / FAIL |
      | COINBASE-CDE | FAIL / PASS | FAIL — never appears anywhere | FAIL — no adapter exists at all |
      | COINBASE-FUTURES | FAIL / PASS | FAIL | FAIL (venue-string) / FAIL |
      | COINBASE-SPOT | FAIL / PASS | FAIL | FAIL (venue-string) / FAIL |
      | KRAKEN-FUTURES | FAIL / PASS | FAIL — never appears | PASS / FAIL (stub) |
      | KRAKEN-SPOT | FAIL / PASS | FAIL | PASS / FAIL (stub) |
      | OKX-FUTURES | FAIL (unreachable under suffix) / PASS | FAIL — excluded from perp loop | FAIL (venue-string) / FAIL |
      | OKX-SPOT | FAIL (unreachable under suffix) / PASS | PASS (spot loop, vocab caveat) | FAIL (venue-string) / FAIL |
      | OKX-SWAP | FAIL / PASS | FAIL — excluded from perp loop | FAIL (self-mislabels FUTURES/SPOT) / FAIL |
- [x] ✅ [BACKEND] P0. **Gap: CEFI live position-read dispatch is broken for 9/12 major venues** —
      `position_interface/factory.py::_get_cefi_adapter`'s venue-match statement only recognizes
      `binance`/`binance_futures`/`binance_spot` plus bare `bybit`/`okx`/`deribit`/`hyperliquid` — every canonical
      dash-suffixed BYBIT-SPOT/OKX-* token, plus all of COINBASE/KRAKEN, raise an unhandled `ValueError` that
      `ReconciliationEngine` silently swallows (per-position `except ValueError: continue`). Escalated + full
      detail: `plans/active/issues/cefi_live_venue_string_dispatch_broken_2026_08_16.md`. Done-when: all 12
      venues resolve to a real adapter under their canonical dash-form venue string, with a regression test using
      dash-form tokens (existing test suite only covers bare lowercase forms). **Fixed —
      `strategy-service@9027c2f5a9`**, full detail + tests in the linked issue doc's now-closed P0 todo.
- [x] ✅ [BACKEND] P0. **Gap: CEFI live order-placement dispatch is broken for 9/12 major venues, same root
      cause as the position gap above** — `execution_service/trade_execution/factory.py`'s `CCXT_VENUES` set
      only recognizes bare venue base names, but callers pass the canonical dash-suffixed string, so
      `get_order_adapter` raises `ValueError: Unsupported venue` for everything except BYBIT and the two
      hardcoded KRAKEN-SPOT/KRAKEN-FUTURES entries. Full detail + the shared root-cause writeup (legacy
      bare-token vocabulary vs. canonical dash-form venue ID, unreconciled across 2 separate service factories):
      `plans/active/issues/cefi_live_venue_string_dispatch_broken_2026_08_16.md`. Done-when: all 12 venues can
      place a live order under their canonical venue string; a shared venue-normalization helper is the preferred
      fix over patching both dispatch tables independently, since the same disease will recur at the next call
      site otherwise. **Fixed — `execution-service@fcc6bbcc2c`**, full detail + tests in the linked issue doc's
      now-closed P0 todo. The shared-normalization-helper preference is tracked as that doc's own open P1
      follow-up, not done as part of this fix (each factory got its own local fix).
- [x] ✅ [BACKEND] P0. **Gap: order cancel/amend are fake-success stubs for every CEFI venue** —
      `execution_service/api/manual_instruction_api.py`'s `/cancel` and `/amend` endpoints log an event and
      return a hardcoded `{"status":"CANCELLED"}`/`{"status":"AMENDED"}` without ever calling any exchange
      adapter; `amend` has zero real implementation anywhere in the codebase. A caller cannot distinguish "the
      order was actually cancelled" from "the stub lied about it" — the same live-money-risk shape as the
      already-fixed CCXT-withdraw-stub (`execution-service@b9ddcd9193`), just for order cancellation. Escalated:
      `plans/archive/issues/cefi_execution_cancel_amend_fake_success_stub_2026_08_16.md`. Done-when: `/cancel`
      calls the real per-venue adapter's `cancel_order` (already genuinely implemented, just unreachable) and
      reports its real result; `amend` gets a real implementation or is explicitly documented as unsupported by
      every underlying venue API (verify per-venue before assuming) with the endpoint failing loud instead of
      lying. **Fixed — `/cancel`: `execution-service@0cb7c767ba`; `/amend`: `execution-service@b8d225615b`**
      (explicit refusal, not a real per-venue amend — CCXT's `editOrder=True` flag doesn't confirm true
      exchange-native atomicity per venue; that verification is the linked issue doc's own open P2 follow-up).
      Full detail + tests in the linked issue doc, both its P0s and its P1 now closed.
- [x] ✅ [BACKEND] P1. **Gap: `LIQUIDATION_CAPTURE` has zero CEFI archetype slot** — wired exclusively to DeFi
      protocols (Aave/Uniswap, `archetype_slots_defi.py:348-350`) despite 5 CEFI venues (BINANCE-FUTURES, BYBIT,
      COINBASE-FUTURES, KRAKEN-FUTURES, OKX-SWAP) declaring `liquidations` data with this as their only declared
      consumer — real captured data (per steps 1-5), zero strategy slot using it for any CEFI venue. Done-when:
      at least one CEFI venue is added to `LIQUIDATION_CAPTURE`'s slot declaration, or the CEFI exclusion is
      confirmed intentional with a cited reason. **CEFI exclusion confirmed intentional — strategy-service@f89c6d8235**
      (cited comment: `LiquidationCaptureEngine` is a flash-loan/on-chain atomic-bundle mechanism structurally
      inapplicable to a CEX order book; the 5 CEFI "consumers" are a `generate_venue_work_list.py` data_type-name
      false positive, same shape as the confirmed `MARKET_MAKING_PREDICTION` finding above. Real CEFI variant
      ("bid-ladder near liq price", per the manifest's `hyperliquid` PARTIAL cell) is unimplemented new archetype
      design — tracked as quant_dev/backend follow-ups in
      `plans/active/issues/liquidation_capture_cefi_bid_ladder_variant_unbuilt_2026_08_17.md`.
- [x] ✅ [BACKEND] P1. **Gap: `CARRY_BASIS_DATED`/`_INV` — BYBIT had zero presence, BINANCE-FUTURES's own
      `futures_chain` data wasn't actually the archetype's futures leg, and the capability matrix claimed Coinbase
      support that doesn't exist in the real generator (matrix/code drift) — done 2026-08-17.** SHIPPED —
      `strategy-service@a2fcb36e0d` + `unified-api-contracts@e64a408c49`. `generate_venue_work_list.py` confirmed
      BYBIT declares real captured `futures_chain` data with `CARRY_BASIS_DATED`/`_INV` as consumers (not a CSV
      false-positive like the `LIQUIDATION_CAPTURE`/`MARKET_MAKING_PREDICTION` findings elsewhere in this batch) —
      a genuine omission, not intentional. Extended `catalog_carry.py`'s crypto dated-basis loop (both
      `build_carry_basis_dated()` and `build_carry_basis_dated_inv()`) to add BYBIT as a second spot-leg venue
      alongside BINANCE, both paired against Deribit as the sole dated-future leg — same spot-only role BINANCE
      already played (BINANCE-FUTURES's own `futures_chain` data is confirmed NOT the future leg; Deribit's dated
      crypto futures/options book is, documented in a code comment at the call site). The new bybit-deribit rows
      stay honestly excluded from paper drivability (`_BASIS_DATED_SATISFIABLE_VENUE_PAIRS` left unchanged —
      binance-deribit raw-tick satisfiability is verified, bybit-deribit is not, so it's excluded the same way
      every other unverified pair already is, not silently assumed). Corrected the manifest's `venue_ids` for both
      archetypes' CEFI `dated_future` cell: removed the stale `coinbase` claim (confirmed real only under the
      sibling `CARRY_BASIS_PERP`), added `bybit`. Manifest regenerated via
      `scripts/generate_archetype_capability_manifest.py --write` (the committed JSON is a deterministic
      round-trip of the live Pydantic registry — hand-editing it directly fails `test_manifest_is_round_trip_stable`).
      3 pre-existing tests updated for the new row counts (16→18 `CARRY_BASIS_DATED`, 3→5 `_INV`) and the new
      honestly-skipped bybit rows: `test_basis_dated_catalog_config_contract.py`,
      `test_paper_universe.py::test_basis_dated_archetypes_are_drivable_only_for_binance_deribit_crypto_rows`.
- [x] ✅ [BACKEND] P1. **Record every NEW gap found during steps 6-8 — done 2026-08-16.** 5 genuinely new gaps
      tracked above (2 escalated as dedicated P0 issue docs given the live-money-risk shape, matching this plan's
      own step-9 precedent): CEFI live position dispatch broken 9/12, CEFI live execution dispatch broken 9/12
      (same root cause), cancel/amend fake-success stub fleet-wide, `LIQUIDATION_CAPTURE` has no CEFI slot,
      `CARRY_BASIS_DATED`/`_INV` BYBIT-absence + matrix/code drift. 3 already-tracked archetype-registration gaps
      (`MARKET_MAKING_INVENTORY_SKEW`/`_QUEUE_MICROSTRUCTURE`/`VOL_TERM_STRUCTURE_ARB` "shipped but not
      registered") confirmed via corpus grep against `v2_engine_venue_buildout_2026_06_15.md` before filing, not
      duplicated. `MARKET_MAKING_PREDICTION`'s apparent CEFI consumption confirmed to be a CSV data_type-keyed
      false positive (structurally scoped to `asset_group:PREDICTION` in the real capability matrix), not a gap.
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
- [x] ✅ [BACKEND] P1. **Gap: `classify_transfer_type` silently defaults to `CEX_WITHDRAW` for venues with neither
      an ON_CHAIN/custody match nor a real CCXT integration** — confirmed for `EXTENDED-STARKNET` (empty
      `custody_provider`, root cause already tracked) and `KALSHI-PERP` (fiat-only, `ccxt_exchange_id` unset).
      Both would attempt a CCXT `withdraw()` call that cannot succeed, rather than failing loud with a clear
      "no transfer rail for this venue" error. Done-when: `classify_transfer_type` (or its caller) fails loud for
      a venue with no real rail, instead of defaulting to a semantic that cannot work; cite the fix against both
      venues. **The fix was already shipped — `unified-api-contracts@f1c5d63b` (2026-08-17) added the exact
      fail-loud `ValueError` this todo asked for, citing both EXTENDED-STARKNET and KALSHI-PERP by name in its
      own comment — but landed with zero test coverage. Closed here by adding the missing regression tests —
      `unified-api-contracts@4567adfe11`**: explicit coverage for both named venues raising `ValueError` (not
      silently returning `CEX_WITHDRAW`), a positive-control (BINANCE-FUTURES, which has a real
      `ccxt_exchange_id`, still classifies as `CEX_WITHDRAW`), and the fully-unknown-venue case. QG green (572s,
      unified-api-contracts), sentinel-verified on `origin/live-defi-rollout`.
- [x] ✅ [BACKEND] P1. **Record every gap found — done 2026-08-16.** 3 genuinely new gaps tracked (COINBASE-FUTURES
      live connector, the CCXT-withdraw-stub issue doc, the wrong-default transfer misrouting); several other
      apparent gaps (KALSHI-PERP/POLYMARKET-PERP step-2 scaffolds, EXTENDED-STARKNET missing batch adapter,
      EXTENDED-STARKNET's empty custody_provider root cause, the `polymarket_market_microstructure` naming
      artifact) confirmed already tracked elsewhere via corpus grep before filing, not duplicated.
- [x] ✅ [BACKEND] P0. **Confirm the parent plan's hard rules held — done 2026-08-16, trivially satisfied.** This
      batch's steps 1-5 and step 9 sweep was investigation/documentation only — zero code was changed in any
      touched repo (the new issue doc is a plan-corpus doc, not a code change).

## Progress Log

- **2026-08-17 — transfer-misrouting gap closed; fix was already shipped, real remaining work was missing test
  coverage.** SHIPPED — `unified-api-contracts@4567adfe11` (slot 16). Dispatched against the `classify_transfer_type`
  todo; direct read of the live function found `unified-api-contracts@f1c5d63b` (slot 18, same day) had already
  landed the fail-loud `ValueError` for EXTENDED-STARKNET and KALSHI-PERP before this task was picked up — verified
  by reading the function body + both venues' `VENUE_WALLET_CAPABILITIES` entries directly, not taken on the
  commit message's word alone. That fix shipped with zero regression coverage, so the genuine remaining work was
  tests, not a second fix: added 4 unit tests in
  `tests/internal/unit/domain/execution_service/test_transfer_types.py` (both named venues fail loud, a
  real-CCXT-rail venue still classifies normally as a positive control, and a fully-unknown venue also fails
  loud). QG green (572s); quickmerge landed after sentinel/push-race retries under branch churn — independently
  verified `4567adfe11` is an ancestor of `origin/live-defi-rollout` before citing it here.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
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

**2026-08-16 — steps 6-8 swept (12 major venues, 36 rows), 5 more real gaps found, 2 escalated as P0 issue
docs — 0/12 venues reach a complete end-to-end state.** SHIPPED — `unified-trading-pm@4686d503ad`. 3 parallel
research passes: strategy-service (positions), strategy-service + unified-api-contracts (archetype/slot
declarations), execution-service (order execution). Batch+paper position read and CEFI's single-factory CCXT
execution pattern are both genuinely healthy across all 12 venues; live position read, live order placement, and
archetype/slot wiring are not — live position read only works for 3/12, live order placement only works for a
DIFFERENT 3/12 (root cause: a legacy bare-token venue vocabulary in 2 separate service dispatch tables never
reconciled against the canonical dash-form venue ID — escalated as
[cefi_live_venue_string_dispatch_broken_2026_08_16](/plans/active/issues/cefi_live_venue_string_dispatch_broken_2026_08_16.md)),
cancel/amend are fake-success stubs fleet-wide (escalated as
[cefi_execution_cancel_amend_fake_success_stub_2026_08_16](/plans/archive/issues/cefi_execution_cancel_amend_fake_success_stub_2026_08_16.md)
— same shape as the already-fixed CCXT-withdraw-stub), and 5 of the 8 archetypes the CSV lists as consumers have
zero real CEFI slot for any venue (one is a CSV false-positive, three are already-tracked "shipped but not
registered" in `v2_engine_venue_buildout_2026_06_15.md`, one — `LIQUIDATION_CAPTURE` — is a genuinely new gap,
tracked as its own P1 todo alongside a `CARRY_BASIS_DATED`/`_INV` matrix/code-drift gap). This meaningfully
revises steps 1-5's "flagship, mature, healthy" framing: that was about data (reference/capture/features), which
holds up; strategy+execution wiring for the same venues does not. Both P0 issue docs' most severe claims (the
position-factory `match` statement, the execution-factory `CCXT_VENUES` set, and the `/cancel`+`/amend` stub
bodies) were independently spot-checked by direct file read before filing, not taken on the sub-agents' word
alone. Remaining open in this batch: the 5 new gap todos themselves (tracked, not blocking this todo's own
completion — this todo's done-when was "a real per-row verdict," which is satisfied).
