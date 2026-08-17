---
doc_type: plan
title: sports venue e2e wiring batch 1 — 2026-08-16
summary: >-
  Fresh carve-out from venue_e2e_wiring_2026_08_16.md's "Fork per-asset-group dispatch batches" P0 todo — walks
  contract steps 1-9 across every sports (venue, data_type) row from `unified-api-contracts/scripts/
  generate_venue_work_list.py` (31 rows, measured 2026-08-16; re-run the script, this count is not a constant).
  Not an extraction from another source doc — no operator-gated item mixed in, per task_template.md §3 finding Y.
status: active
nature: process
asset_group: [sports]
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
tags: [venue-readiness, e2e-wiring, sports, ao-dispatch, satellite-batch]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
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
estimate_baseline_ai_days: 1.8
estimate_calibrated_ai_days: 1.44
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
    /codex/02-data/sports-2020-06-data-floor.md,
    unified-api-contracts/scripts/generate_venue_work_list.py,
  ]
source: >-
  Forked from `venue_e2e_wiring_2026_08_16.md`'s "Fork per-asset-group dispatch batches" P0 todo, 2026-08-16
  interactive session, per the operator-selected "per contract-step-group" decomposition.
---

# sports venue e2e wiring batch 1 — 2026-08-16

> **Parent**: [`/plans/active/venue_e2e_wiring_2026_08_16.md`](/plans/active/venue_e2e_wiring_2026_08_16.md) (W4).
> The contract steps this plan walks, and the hard rules it must not violate, live in the parent — not restated here.
> Row list: `unified-api-contracts/scripts/generate_venue_work_list.py --csv PATH` filtered to `asset_group=sports`.
> **Sports 2020-06 data floor applies** (`/codex/02-data/sports-2020-06-data-floor.md`) — no step below may treat
> pre-2020-06-06 odds coverage as real.

## Todos

- [x] ✅ [BACKEND] P0. **Steps 1-5 per unit — done 2026-08-16.** SHIPPED — `unified-trading-pm@1c9fe64ae2`.
      3 parallel research passes across instruments-service, market-tick-data-service, features-service (step 5
      trivially checked, see below).
      **Step 2 (instrument resolution) — architecturally different from every other AG, PASS once re-framed.**
      Sports odds venues are NOT in instruments-service at all — `venue_core.py:475-537`'s
      `get_venues_for_asset_groups()` returns a completely disjoint SPORTS list (data providers like
      `API_FOOTBALL`/`FOOTYSTATS`), by deliberate design ("Decision C", operator 2026-06-29, cited in-code): odds
      venues resolve via UAC's `_odds_api_maps.py` directly into MTDS, never through IS's `InstrumentRecord`. All
      31 sampled venues are present in that mapping with a `start_date` — PASS under the real architecture, not a
      gap that the IS-centric framing in this todo's own text implied.
      **Steps 3-4 (batch/live) — 23/31 covered by the shared `OddsApiAdapter`**
      (`market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py`, `REQUESTED_ODDS_API_
      BOOKMAKERS`, folding `LADBROKES`/`BET888SPORT` vendor-spelling aliases via `SPORTS_VENUE_FOLD`). Live: same
      23-key coverage via REST poll + dedicated `odds_api_ws.py`/`betfair_ws.py` WSFeedConnectors — but both are
      correctly, explicitly marked `BLOCKED-CREDENTIALS` in-code (Odds-API Starter tier / Betfair app-key not
      provisioned) — the build exists, only credentials are missing, exactly the workspace's "gate RUNNING never
      BUILDING" rule already satisfied, not a new gap. **8/31 not covered**, in 3 distinct categories: (a)
      `BETMGM`/`BETOPENLY`/`BETWAY` — deliberately excluded with a cited reason ("4-6% price diff vs OddsPapi",
      `odds_api_adapter.py:88`), not a gap; (b) `ONEXBET` — has a separate adapter but confirmed unreachable dead
      code, already flagged by a prior audit (`sports_handler.py`'s own comment, `registry.py`'s STATUS note), not
      a new gap; (c) **`BOVADA`/`NOVIG`/`PROPHETX`/`UNIBET_EU` — genuinely uncovered with no stated reason found**,
      tracked as a new gap todo below.
      **Step 5 (feature consumption) — all 31 rows show `archetype_consumers=NONE`.** No archetype has declared
      needing raw `odds` data at all — a genuine undeclared-scope gap identical in kind to tradfi's 12 NONE rows,
      `BLOCKED-ON:archetype-declaration-backlog` for the whole AG, not investigated further (nothing declared to
      check implementation against).
- [x] ✅ [BACKEND] P1. **Gap: `BOVADA`/`NOVIG`/`PROPHETX`/`UNIBET_EU` have no batch or live odds capture at all —
      done 2026-08-17.** SHIPPED — `market-tick-data-service@1ca534260b`. Split 2+2: **NOVIG/PROPHETX are
      already-intentional** — genuinely prediction-market exchange venues (`SPORTS_PREDICTION_MARKET_VENUES` in
      UAC's `venue_constants.py`), structurally excluded from `bookmakers=` (never requested at all, sourced via
      `asset_group=prediction` instead), already regression-locked by
      `market-tick-data-service/tests/unit/test_sports_sentinel_scope.py::test_prediction_market_venues_excluded_structurally`
      — no code change needed, confirmed intentional (not the BETMGM/BETOPENLY/BETWAY price-diff-QA pattern, a
      different but equally cited reason). **BOVADA/UNIBET_EU were the genuine gap** — no exclusion reason found
      anywhere (unlike the audited boylesports/betway/leovegas price-diff exclusions in
      `odds_api_adapter.py`'s own comment block), yet both carry real historical captured manifest data
      (`aggregator:ODDS_API` route, `batch_start_date=2025-07-31`, UAC's `VENUE_DATA_TYPE_CAPABILITIES`) — Odds-API
      has a genuine `bovada` key (`odds_api_mapping.py::ODDS_API_KEY_TO_VENUE`), and UNIBET_EU is a confirmed
      genuinely-distinct feed from bare `unibet`/`unibet_uk` (live content comparison,
      `test_unibet_uk_is_not_folded_distinct_bookmaker_from_unibet`), not a `SPORTS_VENUE_FOLD` alias target. Added
      both to `REQUESTED_ODDS_API_BOOKMAKERS` (23→25 keys); updated the regression-lock test's wire-string/count/
      newly-expectable assertions in the same commit.
- [ ] [BACKEND] P0. **Steps 6-8 per unit — strategy and execution**, across sports's 31 rows. **All 31 stay
      `BLOCKED-ON:archetype-declaration-backlog`** per the step-5 result above — nothing in this todo is
      dispatchable until at least one archetype declares needing `odds`. Re-check once the archetype-declaration
      backlog moves.
- [x] ✅ [BACKEND] P0. **Step 9 per unit — done 2026-08-16.** SHIPPED — `unified-trading-pm@1c9fe64ae2`.
      Cross-checked 3 independent SSOTs (`SportsHandler.SUPPORTED_VENUES`, `sports_factory.py`'s
      `_LIVE_VENUE_CONFIGS`, UAC's `SPORTS_*_VENUES` constants): real, wired bet-placement adapters exist for
      exactly 4 venues system-wide (`betfair`, `matchbook`, `kalshi`, `polymarket`), none of the other 27 odds-
      sourcing-only venues have any execution capability at all.
      **30/31 — NOT-APPLICABLE.** Odds-sourcing only, confirmed absent from every execution-service venue
      registry (the 3 `BETFAIR_*` regional keys in this AG's list don't match the wired bare `"BETFAIR"` key
      either — a real venue, just not one of these 31's literal spellings).
      **`MATCHBOOK` — genuine FAIL, not NA.** Has real, wired live execution capability but zero
      `VENUE_WALLET_CAPABILITIES` entry and zero transfer-code references anywhere in
      `execution-service/execution_service/engine/transfers/` — no funding rail exists despite live trading
      capability existing. Tracked as its own gap todo below.
- [ ] [BACKEND] P1. **Gap: `MATCHBOOK` has real, wired execution capability but no transfer rail at all** —
      absent from `VENUE_WALLET_CAPABILITIES`
      (`unified-api-contracts/unified_api_contracts/internal/domain/execution_service/transfer_types.py`) and
      from every transfer-code path in `execution-service/execution_service/engine/transfers/`. Same class of gap
      as the prediction batch's KALSHI finding — a live-money correctness risk if trading is ever actually run
      against this venue with no way to fund/withdraw. Done-when: a real `VENUE_WALLET_CAPABILITIES` entry +
      working rail is added, or confirmed intentional with a cited reason.
- [x] ✅ [BACKEND] P1. **Record every gap found — done 2026-08-16.** 2 genuinely new gaps tracked above
      (uncovered odds venues, MATCHBOOK's missing transfer rail); 3 other apparent gaps (price-diff exclusion,
      ONEXBET dead code, BLOCKED-CREDENTIALS live connectors) confirmed already correctly handled/documented
      in-code, not duplicated as new todos.
- [x] ✅ [BACKEND] P0. **Confirm the parent plan's hard rules held — done 2026-08-16, trivially satisfied.** This
      batch's steps 1-5 and step 9 sweep was investigation/documentation only — zero code was changed in any
      touched repo.

## Progress Log

**2026-08-16 — full contract sweep done, 2 new gaps found, sports is architecturally distinct.** SHIPPED —
`unified-trading-pm@1c9fe64ae2`. 3 parallel research passes. Key structural finding: sports odds venues never
resolve through instruments-service at all (a deliberate, documented 2026-06-29 decision — disjoint from every
other AG's step-2 pattern), and all 31 rows show `archetype_consumers=NONE` (no archetype has declared needing
raw `odds` data), so steps 5-8 are trivially `BLOCKED-ON:archetype-declaration-backlog` for the whole AG — no
implementation investigation needed there, unlike prediction/tradfi's partial-NONE rows. Of the 8/31 venues with
no batch/live capture, 6 turned out to be already-documented decisions (3 price-diff-QA exclusions, 1 dead-code
adapter, and the live WS connectors' correct `BLOCKED-CREDENTIALS` status) — checked before filing, not
duplicated. Exactly 2 genuinely new gaps: 4 venues (BOVADA/NOVIG/PROPHETX/UNIBET_EU) with no stated exclusion
reason, and MATCHBOOK having real execution wiring but no transfer rail (same class as the prediction batch's
KALSHI finding).

**2026-08-16 — re-checked the steps-6-8 gate, still blocked, no change.** Dispatched against this plan's "Steps
6-8 per unit" P0 todo, whose done-when is "re-check once the archetype-declaration backlog moves." Re-ran
`unified-api-contracts/scripts/generate_venue_work_list.py --csv` live (not a cached snapshot — the script's own
docstring warns the archetype-declared/undeclared split moves fast) and confirmed all 31 sports rows still show
`archetype_consumers=NONE` — identical to the 2026-08-16 sweep above, zero movement. No archetype has declared
needing raw `odds` data, so steps 6-8 remain undispatchable for the whole AG. Searched
`unified-trading-pm/plans/active/` for a plan that owns/drives the archetype-declaration backlog itself (the thing
this todo is waiting on) — none exists; only this plan and `tradfi_venue_e2e_batch1_2026_08_16.md` cite the
condition, neither drives it. No ETA available. Skipping this task with `reason_code: GATED` (no code shipped —
correctly nothing to ship while blocked) rather than fabricating work or falsely flipping the checkbox.

**2026-08-17 — BOVADA/NOVIG/PROPHETX/UNIBET_EU gap todo closed.** SHIPPED —
`market-tick-data-service@1ca534260b`. NOVIG/PROPHETX confirmed already-intentional (structural prediction-market
exclusion, already regression-locked); BOVADA/UNIBET_EU were the real gap (real historical captured data, no
exclusion reason found anywhere) — added both to `REQUESTED_ODDS_API_BOOKMAKERS` in
`odds_api_adapter.py` and updated `test_sports_sentinel_scope.py`'s hardcoded wire-string/count assertions in the
same commit. Full reasoning in the flipped checkbox above.

**2026-08-17 — re-checked again (slot 15), still blocked, zero movement.** Re-dispatched against the same "Steps
6-8 per unit" P0 todo. Re-ran `unified-api-contracts/scripts/generate_venue_work_list.py --csv` live and confirmed
all 31 sports rows still show `archetype_consumers=NONE` — no change since the 2026-08-16 re-check above.
Re-searched `unified-trading-pm/plans/active/` for a plan that owns/drives the archetype-declaration backlog —
still only this plan and `tradfi_venue_e2e_batch1_2026_08_16.md` cite the condition; neither drives it, and no new
owning plan has appeared. No ETA available. Skipping with `reason_code: GATED` again — no code shipped, correctly
nothing to ship while blocked.
