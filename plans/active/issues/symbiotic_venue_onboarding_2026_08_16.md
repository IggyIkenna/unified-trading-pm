---
doc_type: issue
title: Close Symbiotic's remaining readiness gaps (NOT a from-zero build — most layers already exist)
summary: >-
  Operator decision 2026-08-16: get Symbiotic (restaking, DefaultCollateral model) to full readiness per the
  VENUE READINESS CONTRACT (/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md, steps 1-19).
  **Corrected same session, before this doc shipped**: an initial pass assumed Symbiotic needed building from
  scratch across every layer; a dedicated research pass found it is ALREADY wired through UAC (venue + capability
  declared), instruments-service (adapter exists), MTDS (batch adapter exists), and execution-service
  (supports_live=True) — strategy-service has a bespoke position adapter (correctly bespoke, not generic, because
  Symbiotic has withdrawal-queue state a balance read would misrepresent). The real gaps are narrower: a wrong
  hardcoded contract address, missing DeFiAdapter dispatch wiring (the actual reachability gap), a missing
  features-service calculator, an un-registered UAC LST address + venue_constants.py entry, a STALE codex catalogue
  doc claiming MTDS/execution are still pending when they've shipped, and unconfirmed manifest/backfill coverage
  (code existing is not the same claim as data flowing — this session's own recurring lesson). This doc reflects the
  corrected, verified state — do not re-read it as "build from zero."
status: open
nature: issue
asset_group: [cross-cutting, defi]
stage: [data, features, strategy, execution]
repos:
  [
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    features-service,
    strategy-service,
    execution-service,
    unified-trading-system-ui,
  ]
scope: [engineer]
assigned_vm: NA
execution_scope: local-only
tags: [defi, symbiotic, restaking, venue-onboarding, venue-readiness-contract, honest-coverage]
priority: P1
source: operator-request-2026-08-16
parent_epic: infrastructure_master
related:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /plans/active/issues/karak_decommission_2026_08_16.md,
    /codex/02-data/defi-venue-protocol-catalogue.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-08-16
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /codex/02-data/defi-venue-protocol-catalogue.md,
    execution-service/execution_service/defi_execution/protocols/symbiotic.py,
    unified-api-contracts/unified_api_contracts/registry/lst_token_addresses.py,
  ]
---

# Close Symbiotic's remaining readiness gaps

## Ground truth — what already EXISTS, verified (do not rebuild these)

| Layer | File(s) | State |
|---|---|---|
| UAC — venue declared | `registry/defi_venues.py:78,392,477` (`SYMBIOTIC-ETHEREUM` in `ALL_DEFI_VENUES`, short↔long map, status=`live`) | ✅ exists |
| UAC — capability declared | `registry/capability_declarations/_defi.py:1067-1073` (`ProtocolClass.RESTAKING`, `data_types=["staking_yields","oracle_prices"]`) | ✅ exists, no `required_tokens` (correct — multi-vault, no single receipt token) |
| UAC — `venue_constants.py` | — | ❌ **missing entirely** (EtherFi has a full entry: capability sets, protocol type, chain, fee model, alpha profile — Symbiotic has none) |
| UAC — LST token address SSOT | `registry/lst_token_addresses.py` | ❌ **missing** — and the address currently hardcoded in execution-service is WRONG anyway (see below) |
| instruments-service | `reference_data/adapters/defi/symbiotic.py`, registered in `factory.py` | ✅ exists — "4-vault curated registry" per the catalogue doc |
| MTDS batch adapter | `market_interface/adapters/defi/restaking_symbiotic_adapter.py`, registered in `factory.py` | ✅ exists — data types `staking_yields`, `oracle_prices` |
| MDPS | — | ✅ correctly N/A — LST/restaking oracle-price and staking-yield data is consumed raw by strategy-service/FS, no candle-derivation step exists for this shape (same as EtherFi) |
| features-service | — | ❌ **missing** — zero Symbiotic hits; EtherFi's equivalent is `lst_staking_calculator.py`'s `LstStakingCalculator`, but that pattern is single-token-LST-shaped and won't fit Symbiotic's multi-vault shape directly |
| strategy-service position read | `position_interface/factory.py` `case "symbiotic":` → bespoke `position_interface/adapters/symbiotic.py` (`SymbioticPositionAdapter`) | ✅ exists, **correctly bespoke, not generic** — `_generic_token_balance_adapter`'s own docstring explicitly excludes Symbiotic ("withdrawal queues... a bare balance misrepresents" this position) |
| execution-service | `defi_execution/protocols/symbiotic.py:77-79`, `supports_live=True # real DefaultCollateral.deposit()/withdraw() via sign_and_send_transaction() (wstETH only)` | ✅ exists, real write path — **but wrong address, and zero DeFiAdapter dispatch (reachability gap)** |
| Strategy wizard | `unified-trading-system-ui`'s `lib/registry/capability-manifest.ts`, auto-derived from UAC's `openapi/capability-manifest.json` | ✅ **no direct code change needed** — once UAC fully declares the venue and the manifest is regenerated, the wizard picks it up automatically |
| Tests | `test_symbiotic_metadata.py` (IS), `test_restaking_symbiotic_adapter.py` (MTDS), `test_symbiotic_connector.py` + `test_bespoke_defi_readers.py` (strategy-service), `test_connector_live_capability.py` (execution-service) | ✅ exist per layer — **no dedicated FS test**, consistent with the FS gap above |

**Authoritative onboarding checklist**: `/codex/02-data/defi-venue-protocol-catalogue.md` — this IS the SSOT status
table (✅ PRODUCTION / 🟢 CODE-SHIPPED-AWAITING-BACKFILL / ◐ / ✗ legend), not something this doc should duplicate.
**Its Symbiotic row (line 200) is STALE**: it says "MTDS + EXEC pending Phase 3+4" — both now have real, shipped
code (table above). Fixing that row is todo #1, before anything else, so the next reader of the SSOT doc isn't
misled the same way this issue's first draft was.

## Real gaps (measured this session)

1. **Wrong hardcoded vault address.** `execution_service/defi_execution/protocols/symbiotic.py`'s
   `DEFAULT_COLLATERAL_WSTETH` constant (`0xC0d33c8D411E2d88f6c46BeEa89C51c23e23c52C`) resolves to **zero deployed
   bytecode** on live Ethereum mainnet (verified this session, block 25,765,709). The real, verified contract is
   `0xC329400492C6ff2438472D4651Ad17389fCb843a` ("Symbiotic: DC_wstETH Token" on Etherscan) — confirmed real
   bytecode, live `totalSupply()` = 16,349 wstETH. Same defect class as Karak's wrong address
   (`/plans/active/issues/karak_decommission_2026_08_16.md`), caught before it propagated further into new wiring.
2. **Zero DeFiAdapter dispatch — the actual reachability gap.** `supports_live=True` is real, but nothing in
   `DeFiAdapter`'s `_dispatch_defi_operation` gates on a `"SYMBIOTIC"` venue marker — confirmed via this session's
   own execution_service_venue_reachability_baseline.json (unified-api-contracts), which lists `symbiotic` as an
   unreachable venue alongside `morpho`/`karak`/`pendle`. This is steps 8 and 12 of the readiness contract, and it's
   the one gap that actually blocks live execution — everything else in the table above is either already correct
   or a data/documentation gap, not a "can we trade this" gap.
3. **UAC registration incomplete.** No `venue_constants.py` entry, no LST address SSOT entry (blocked on fixing the
   address first — don't migrate a wrong address into the SSOT).
4. **No features-service calculator.** Real gap, needs its own design (multi-vault shape, not the single-token LST
   calculator pattern EtherFi uses) — or an explicit "declared unused" per the umbrella plan's step 18 bar, if FS
   genuinely isn't the right consumer for this data shape.
5. **Manifest/backfill coverage unconfirmed.** Code existing at every layer is not the same claim as data actually
   flowing and reconciling — per this session's own repeated lesson ("built but unreachable" / "code-shipped
   awaiting backfill" are different states from "PRODUCTION"). This doc's batch-smoke-test proof (below) is a
   Dune-sourced spot-check, not a confirmation that MTDS's own `restaking_symbiotic_adapter.py` has actually been
   run and is reconciling in the manifest.
6. **`carry_and_yield` strategy-archetype coverage for Symbiotic specifically is unconfirmed** — the research pass
   found EtherFi's chain-map entry (`staked_basis.py:167`) but did not confirm or deny a Symbiotic equivalent;
   needs a direct check, not an assumption either way.

## Batch-backfill smoke test — PROVEN, real data (2026-08-16, this session)

Per the operator's explicit sequencing ("first smoke test... once you've proven we can get a day, then it's
great"): queried Dune's pre-indexed `symbiotic_ethereum.defaultcollateral_evt_deposit`/`_evt_withdraw` decoded
tables (ABI-decoded, no raw `eth_getLogs` needed — the free-tier RPC route hit provider-side rate limits on log
queries, Dune's indexed tables were the production-grade alternative) against the **verified real** contract
address for a single UTC day, **2026-08-15**: 3 real withdraw events, real tx hashes, real amounts (0.0116 /
0.2248 / 0.0313 wstETH), zero deposits that day. Dune query IDs: `8345258` (day slice), `8345262` (earliest
activity / genesis lookup). This proves the raw data is fetchable at daily granularity; it does NOT prove MTDS's
own adapter has been run against it (gap #5 above) — those are different claims.

**Genesis / honest-coverage floor: 2024-06-11.** Cross-verified two ways: public reporting places Symbiotic's
mainnet launch in June 2024; the earliest `Transfer` event the verified vault contract ever emitted is
`2024-06-11 11:00:35 UTC` (Dune query `8345262`). Use as the backfill floor — pre-genesis data is
fabrication-by-construction, same principle as the sports 2020-06 floor
(`/codex/02-data/sports-2020-06-data-floor.md`).

## Todos

- [ ] [AGENT] P0. **Refresh the stale catalogue-doc row** (`/codex/02-data/defi-venue-protocol-catalogue.md:200`) —
      MTDS and execution-service are no longer "pending Phase 3+4"; update to reflect the real shipped state (and
      re-check its ✅ PRODUCTION bar — manifest ≥99% coverage — before marking it fully done; per gap #5, this is
      likely still 🟢 CODE-SHIPPED-AWAITING-BACKFILL-VERIFICATION, not ✅ PRODUCTION, until #6 below is checked).
- [x] [AGENT] P0. **Fix the wrong `DEFAULT_COLLATERAL_WSTETH` address** in
      `execution_service/defi_execution/protocols/symbiotic.py` to `0xC329400492C6ff2438472D4651Ad17389fCb843a`,
      citing this issue doc as provenance (matching the `# DERIVED from <source>` citation convention every other
      address in that file uses). — execution-service@70ac877f6a, QG green.
- [x] [AGENT] P0. **Wire Symbiotic into `DeFiAdapter`'s real dispatch** (the reachability gap) — add a
      `symbiotic_connector` parameter + a `"SYMBIOTIC"` venue-gate marker in the STAKE handler (mirrors
      `LIDO-ETHEREUM`'s gating in `_execute_staking`), matching `symbiotic.py`'s existing
      `preflight_validate_operation(venue_id, "supply")` pattern. Remove `symbiotic` from
      `unified-api-contracts/tests/data/execution_service_venue_reachability_baseline.json`'s
      `unreachable_defi_venues` list in the SAME change (ratchet-down convention). — execution-service@85c8310b20,
      QG green. Baseline already excluded `symbiotic` (removed by a concurrent session earlier this session) — no
      change needed there. Also wired `symbiotic_connector` into `LiveExecutionHandler._build_defi_adapter` (the
      real live-execution constructor call site) so the connector actually reaches the adapter at runtime, not just
      in the dispatcher's type signature.
- [ ] [AGENT] P0. **Add `venue_constants.py` entry** for Symbiotic (UAC) — mirror EtherFi's shape (capability sets,
      `ProtocolClass.RESTAKING`, chain, fee model, alpha profile).
- [ ] [AGENT] P0. **Add the corrected address to the UAC LST SSOT** (`registry/lst_token_addresses.py`,
      `LST_TOKEN_ADDRESS_BY_CHAIN["ETHEREUM"]["wstETH-symbiotic"]` or whatever key convention fits — check the
      existing 6-entry shape first, this may need a per-vault key since Symbiotic is multi-vault, not a single
      symbol like the LST venues already there) — only after the address fix above lands.
- [ ] [AGENT] P1. **Confirm whether MTDS's `restaking_symbiotic_adapter.py` has actually been run and is
      reconciling in the availability manifest** — gap #5. If yes, cite the evidence (manifest coverage %,
      `capture_status`); if no, that's the real remaining batch-backfill work, scoped by the genesis date above.
- [ ] [AGENT] P1. **Design (or explicitly decline) a features-service calculator** for Symbiotic's multi-vault
      restaking shape — not a copy of `lst_staking_calculator.py` (single-token shape mismatch). If FS genuinely
      isn't the right consumer, state that explicitly per the umbrella plan's step 18 "consumed or declared unused"
      bar — don't leave it silently unaddressed.
- [ ] [AGENT] P1. **Confirm or add `carry_and_yield` strategy-archetype coverage** for Symbiotic (check
      `engine/strategies/v2/carry_and_yield/staked_basis.py` and `recursive_staked.py` directly — the research pass
      found EtherFi's entry but did not confirm Symbiotic's presence or absence).
- [ ] [AGENT] P2. **Regenerate/copy the UAC `openapi/capability-manifest.json`** into
      `unified-trading-system-ui`'s wizard registry once the UAC-layer todos above land, per that file's own
      "do NOT hand-edit — copy a fresh capability-manifest.json" instruction. No wizard code change needed.
- [ ] [AGENT] P2. **Add a features-service test** once the calculator design todo above resolves (currently the
      only layer with zero test coverage for this venue).
- [ ] [OPERATOR] P2. **Decide the LST SSOT key shape for multi-vault protocols** — the existing 6 entries are all
      single-symbol-per-venue (`stETH`, `wstETH`, etc.); Symbiotic (and any future multi-vault restaking venue)
      needs either a per-vault key convention or a documented reason it stays out of that specific SSOT and uses a
      different registration path. Decide before todo #5 above, since population is the expensive half.

## Progress Log

- **2026-08-16 (draft 1, superseded same session)**: initial pass assumed Symbiotic needed building from zero
  across every layer. Corrected before shipping — see draft 2 below.
- **2026-08-16 (draft 2, current)**: corrected after a dedicated cross-repo research pass found Symbiotic already
  substantially wired (UAC, IS, MTDS, execution-service, strategy-service all have real code). Rewrote the whole
  doc to reflect "close remaining gaps" rather than "onboard from zero" — leaving the first framing in place would
  have sent whoever picks this up down a wasteful rebuild path, the same "didn't verify, assumed absence" error
  this workspace has flagged repeatedly (`e2e_wiring_reachability_audit_2026_08_15.md`'s own lessons section).
  Batch-backfill smoke test proven (Dune, real day 2026-08-15, real events) and genesis date established
  (2024-06-11, two independent sources), per the operator's explicit sequencing. Found and scoped the wrong
  hardcoded vault address (same defect class as Karak's).
