---
doc_type: issue
title: IBKR place_order guard — determinism proof attempted, blocked on missing tradfi paper-trading spine (guard stays active)
summary: >-
  Investigated flipping UAC's `place_order supported=False` guard for IBKR-routed tradfi venues (CME/CBOE/NASDAQ/NYSE/
  ICE/FX + the base `ibkr` source) per the operator's standing "build it, keep the guard active pending
  batch=paper=live determinism proof" ruling. Read the ibkr_tradfi.py adapter (real `_place_order_live` + sim
  `_place_order_sim` paths, both present and correct) and the paper-batch-live determinism-spine SSOT
  (`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`) that defines how this proof is normally
  constructed for other asset classes. Conclusion: the proof CANNOT be legitimately constructed today — not an
  execution-service-scoped gap, but a missing prerequisite one level up (no archetype instance is wired into the
  paper engine with tradfi as its routed asset_group — archetype and venue are orthogonal axes, several archetypes
  already have IBKR-routed catalog rows, none has live paper-engine wiring — and the spine's own G1 "single shared
  fill model" gap is still open workspace-wide). Guard NOT
  flipped. No false-positive proof forced.
status: open
nature: issue
asset_group: [tradfi]
stage: [execution, strategy]
repos: [execution-service, unified-api-contracts, strategy-service]
scope: [engineer]
assigned_vm: NA
execution_scope: local-only
tags: [tradfi, ibkr, determinism, paper-batch-live, guard, place-order]
priority: P2
source: operator-request-2026-08-21
parent_epic: tradfi_master
related:
  [
    /plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md,
    /plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
  ]
created: 2026-08-21
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/capability_declarations/_tradfi.py,
    execution-service/execution_service/trade_execution/adapters/ibkr_tradfi.py,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
  ]
---

# IBKR place_order guard — determinism proof attempted, found infeasible this session

## What was asked

Build the workspace's standard batch=paper=live determinism proof (ε=0, trade-for-trade, per
`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`) for IBKR-routed tradfi order placement, then flip
`unified-api-contracts/unified_api_contracts/registry/capability_declarations/_tradfi.py`'s `place_order
supported=False` guard to `True` for `ibkr`/`cme`/`cboe`/`nasdaq`/`nyse`/`ice`/`fx` if — and only if — the proof
genuinely passes.

## What was read

- `_tradfi.py`'s module docstring + `_gated_tradfi_venue_capability()`: the guard is explicit, intentional, and cites
  exactly the proof this issue was asked to build (`tradfi_consolidated_native_ao_extract_2026_07_25.md todo 1`) as the
  gate. `execution-service/execution_service/trade_execution/adapters/ibkr_tradfi.py`: both paths exist and are
  correctly separated — `_place_order_live()` (real `ib_insync` `IB.placeOrder`) and `_place_order_sim()` (routes to
  `L1MatchingEngine`/`L2MatchingEngine`, TradFi midpoint). Nothing wrong with the adapter itself; it is not the blocker.
- The determinism-spine SSOT (`paper-batch-live-reconciliation.md`): the proof this guard demands is not a
  local execution-service unit test. It requires, per §4.1-§4.5: (1) a strategy archetype actually driving IBKR
  instructions through the shared paper engine (`colocated_engine.py` → `V2EngineOrchestrator.on_tick()`), (2) a
  `RunManifest` pinning code shas + an as-of input snapshot, (3) a batch rerun replaying that exact snapshot through the
  SAME fill model paper used, and (4) `reconcile_day()` (batch-live-reconciliation-service) keyed matching on
  `(instrument_key, strategy_instruction_id, tick_timestamp)` asserting ε=0. The template this proof follows for other
  asset classes (`test_paper_batch_rerun_epsilon0_on_real_sequencing`, strategy-service
  `tests/unit/engine/backtest/test_benchmark_fills.py`) exercises real historical GCS data via `GCSFeatureProvider`
  against a live-wired archetype — not synthetic fixtures.
- The already-existing, current answer to "is this proven for tradfi": the (archived, `status: complete`) plan
  `tradfi_consolidated_native_ao_extract_2026_07_25.md` todo 1 — the exact todo `_tradfi.py`'s guard cites — was
  actually completed **2026-08-04**, with the audit report
  `plans/audit/results/tradfi_mvp_cell_wiring_and_pipeline_verification_2026_08_04.md`. Its verdict, verbatim: **"NO
  tradfi MVP cell has paper/live wiring proven (TradFi is batch-only this cycle per
  `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md:82`)."** `_tradfi.py`'s docstring citing that todo as
  "still open" is now stale — it is done, and its answer is "no proof exists, and none is expected this cycle."

## Why the proof can't be built this session (not a false-positive, not forced)

The blocker is not in execution-service. It is two levels up, and both are workspace-wide, standing, documented gaps:

1. **No archetype instance is wired into the paper engine with tradfi as its routed asset_group.** Archetype
   (e.g. `EVENT_DRIVEN`, `STAT_ARB_PAIRS_FIXED`) and venue/asset_group (defi/cefi/tradfi) are orthogonal axes —
   several archetypes already have IBKR-routed rows in `catalog_trading.py`, so this is not a missing archetype
   TYPE, just a missing paper-engine wiring entry for any tradfi-routed instance. The determinism spine's ledger/manifest/recon
   machinery (G3/G4/G5) is shipped and proven for DeFi carry archetypes (`CARRY_STAKED_BASIS`,
   `CARRY_BASIS_PERP`/`CARRY_FUNDING_DISPERSION` — the only two rows in the spine's own "per-archetype canonical data
   source" table, §4.6). Nothing drives an IBKR/CME/NASDAQ/etc. instruction through `colocated_engine.py` in paper mode
   today — there is no archetype, no `GCSFeatureProvider` wiring, no tradfi entry in `resolve_paper_universe`. Building
   this is itself a multi-repo feature (strategy-service archetype + engine + data wiring), not a test.
2. **The spine's own G1 gap ("single shared fill model", paper ≡ batch) is still open workspace-wide**, per §7's own
   inventory: `MISSING (G1) — GroupCRunner smart-matching not yet wired in paper path`. Even for the two archetypes
   that ARE wired, paper and batch do not yet provably share one fill engine. Constructing a tradfi-specific instance of
   this proof would either (a) require finishing G1 first (out of scope — a cross-cutting spine item, not a tradfi-only
   fix), or (b) synthesize a shortcut fill/replay path just for this guard-flip — which would be exactly the
   false-positive proof this task explicitly ruled out.

Neither gap is "small and clearly scoped" in the sense that would justify fixing it inline. Both are the acknowledged,
still-open subject of the spine's own G1/G2 rows and the tradfi cycle-scoping decision
(`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md:83`, "TradFi is batch-only this cutover cycle"). Forcing a
narrow local proof (e.g., asserting `_place_order_sim()` is internally deterministic across two calls with the same
seed) would prove the sim engine is a pure function — true, but not the property the guard requires, which is paper(W)
== batch-rerun(W) on real driven instructions. Reporting that as "the proof" would be a proxy standing in for the
property, banned under this workspace's measurement-claims discipline.

## Verdict

**Guard NOT flipped.** `_tradfi.py`'s `place_order supported=False` for `ibkr`/`cme`/`cboe`/`nasdaq`/`nyse`/`ice`/`fx`
stays exactly as-is — this is the correct state given no proof exists and none can be honestly constructed this
session. No code shipped in execution-service or unified-api-contracts (nothing needed changing; the adapter itself is
already correct).

## What would need to happen for a future attempt to succeed

- [ ] [DESIGN] P2. DEFERRED-BY-DESIGN — RULED 2026-08-22 (D86): Keep deferred — no evidence the tradfi cycle-scope
      ruling ("batch-only this cycle") has changed. Wiring at least one tradfi archetype (e.g. an S&P/ES-futures
      strategy) into the paper engine — `resolve_paper_universe` + a `GCSFeatureProvider`/data-source wiring entry
      mirroring §4.6's DeFi rows — remains future work once cycle scope changes; needed before any tradfi-venue
      determinism proof can exist. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
- [ ] [CODE] P2. Land the spine's G1 gap (batch running the same `GroupCRunner` smart-matching layer paper uses) —
      cross-cutting, not tradfi-specific; tracked at `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`
      §7, plan-of-record `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md`.
- [ ] [REVIEW] P3. Once both land, re-attempt this guard-flip proof using the SAME `reconcile_day()` /
      `test_paper_batch_rerun_epsilon0_on_real_sequencing`-style methodology already proven for
      `CARRY_STAKED_BASIS`/`CARRY_BASIS_PERP`, scoped to whichever tradfi archetype from the first todo above is
      wired, on real historical Databento/Yahoo data (not synthetic).
- [ ] [DOC] P3. Update `_tradfi.py`'s module docstring — it still cites
      `tradfi_consolidated_native_ao_extract_2026_07_25.md todo 1` as "still open"; that plan is archived and the todo
      is done (2026-08-04) with a "no proof, batch-only this cycle" verdict. Repoint the citation to this issue doc so
      a future reader doesn't chase an already-closed, now-stale reference the way this session initially did.

## Codex SSOTs

`/codex/09-strategy/operational/paper-batch-live-reconciliation.md` (the determinism-spine SSOT this proof would need
to instantiate); `/codex/12-agent-workflow/measurement-claims-discipline.md` (why a proxy proof was not substituted).

## Progress Log

- **2026-08-22 — ruling D86 (TradFi paper-engine wiring)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Keep deferred — no evidence the cycle-scope ruling changed. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
