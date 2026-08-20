---
doc_type: plan
title: Nick AI platform disclosure — closing the pre-audit's measured gaps
summary: >-
  Remediation of the 6 gap classes the Nick AI pre-audit measured (external API surface, archetype feature-group
  declarations, granularity declaration, per-AG BACKTESTABLE blockers, sports action-vocabulary confirmation, stale
  codex numbers). The audit is done — this plan does not re-measure. Dispatched as interactive-session sub-agents
  (same mechanism as the pre-audit itself), not AO-ingested.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, strategy, execution]
repos:
  [
    instruments-service,
    market-tick-data-service,
    execution-service,
    strategy-service,
    unified-api-contracts,
    deployment-api,
  ]
scope: [admin, engineer]
tags: [nick-ai, external-api, readiness-remediation, venue-readiness, archetype-feature-groups, client-disclosure]
related:
  [
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-16
source: >-
  Operator direction 2026-08-16, remediating the measured gaps from the Nick AI pre-audit (§§5-6 of the disclosure
  plan). Same interactive-session dispatch mechanism as the pre-audit itself, per the operator's own instruction.
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: brand-new
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 5.0
assigned_role: backend_engineer
effort: high
last_updated: "2026-08-16"
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    unified-trading-library/unified_trading_library/cloud_interface/api_auth.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_feature_groups.py,
  ]
---

# Nick AI platform readiness remediation

## Read first

[`/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md`](/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md)
§§ PRE-AUDIT MEASUREMENTS 5-6 and
[`/plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md`](/plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md).
**The audit is done — every gap below is already evidenced there. This plan does not re-measure.**

## Two findings that changed the dispatch prompt's original scope — read before assuming the todos below match it verbatim

1. **W2 (archetype declarations) cannot be a bounded engineering todo.** `ARCHETYPE_FEATURE_GROUPS`'s own docstring
   (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_feature_groups.py`): *"Coverage is
   deliberately partial. A wrong entry here would silently mislead a contract-step-17 BACKTESTABLE check — worse than
   an honest gap — so only archetypes traced to real dispatch code are declared."* Real tracing already found **zero**
   dispatch-code signal for the undeclared archetypes (`venue_readiness_and_registry_hardening_2026_08_16.md` Progress
   Log, 2026-08-16). Dispatching a sub-agent to "declare" them would fabricate strategy-domain judgment against this
   same-day ruling — a CLAIM≤MEASUREMENT violation, not a gap to close. **Resolved per operator direction 2026-08-16**:
   built a candidate-mapping scaffold instead — [**Archetype Feature
   Scaffold**](https://claude.ai/code/artifact/c6c345e7-10fb-4679-b9d2-6eada7fc3f6c), 55 undeclared archetypes (a
   measured correction — see the artifact's own "count correction" banner: the enum's docstring says 59/54, a live
   Python import measures 60 total / 5 confirmed / 55 undeclared), each tagged confidence high/medium/low with a
   grounded rationale, explicitly **not committed to any file**. Nothing in this plan dispatches W2 engineering work;
   see the tracked review item below.
2. **W4-DeFi's "paused crons" blocker is already fully diagnosed and gated — not new investigation.** Read directly:
   `/plans/active/defi_consolidated_closeout_2026_07_18.md` Track 8 (2026-07-22 correction entry). 7 schedulers (not
   14) are paused because a live `canonical-migration-defi-per-instrument-*` VM is actively rewriting exactly those
   data types; resuming now would race live writes against it. Two todos already track the resume, correctly gated
   (Track-1/2 landing + the migration VM finishing; the `dex_pool_state` pair additionally gated on
   `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` per task_template.md finding P). **This plan adds no new
   DeFi-cron work** — see the cross-reference item below.

## W1 — External HTTP layer (the headline; longest pole; independent — start in parallel)

**Measured state** (audit, unchanged): `instruments-service`, `market-tick-data-service`, `execution-service` each
have `api/main.py` at 62/116/43 lines exposing only `/health` + `/readiness` (line counts re-confirmed live
2026-08-16, unchanged from the audit). The contracts underneath (schemas, instruction taxonomy) are production-real —
this is missing surface, not missing capability.

**Auth — upgrade from the dispatch prompt's original framing.** The dispatch prompt said "mirror deployment-api's
`auth.py`" (`X-API-Key` only, no org/tier scoping — built for an internal ops console, no external counterparty
concept). A better-fitted precedent already exists and is unused by any of these 3 services:
`unified_trading_library.cloud_interface.api_auth.create_api_auth()` — a real, tested UTL dependency supporting
`X-Service-Token` (S2S), legacy `X-API-Key`, **and Bearer JWT with `org_id` + `subscription_tier`** (admin / internal
/ external-pro / external-basic). The JWT leg is exactly the counterparty shape this artifact pitches — an external
org, tier-limited — that deployment-api's simpler internal pattern doesn't have. Each todo below builds on this UTL
helper, not a hand-rolled copy.

- [x] [BACKEND] P0. **instruments-service: build the external instruments surface.** — `instruments-service@2fcf7a19`.
      New router `instruments_service/api/routers/external.py` wired into `api/main.py`, protected by
      `unified_trading_library.cloud_interface.api_auth.create_api_auth("instruments-service")` (top-level
      `create_api_auth`/`AuthContext` re-export, same pattern already live in
      `client-reporting-api/client_reporting_api/api/routes/exports.py`). Read logic lives in new
      `instruments_service/engine/orchestrator/catalogue_query.py`, reusing the existing
      `resolve_instruments_store_kind`/`resolve_bucket_name`/`get_storage_client` bucket-resolution path (the SAME one
      `writers.py`/`instruments_handler.py` use) rather than duplicating it — reads back the already-written
      `instrument_availability/by_date/.../instruments.parquet` catalogue, never re-fetches via URDI. Two endpoints:
      `GET /v1/instruments` (query by asset_group/venue/instrument_type, JSON, row-capped) and
      `GET /v1/instruments/bulk` (streamed combined-parquet dump via chunked `StreamingResponse`; a two-pass
      schema-unify — `pa.unify_schemas(..., promote_options="permissive")` — was required after a live multi-venue
      test crashed on real per-venue schema drift, e.g. `tick_size` decimal128(2,2) vs decimal128(9,8); confirmed
      value-preserving on real data before landing).
      **Done-when evidence**: `quality-gates.sh --no-fix` → `✅ ALL QUALITY GATES PASSED` (exit 0). Live local run
      (uvicorn, real ADC creds against prod GCS, read-only) with a minted `create_token()` JWT (`org_id=org-nick-ai-test`,
      `subscription_tier=data-pro`): no-token → 401; bad `asset_group` → 400;
      `GET /v1/instruments?asset_group=cefi&venue=DERIBIT&instrument_type=PERPETUAL&limit=2` → 200, 2 real rows
      (`DERIBIT:PERPETUAL:ADA-USDC@LIN`, ...); `GET /v1/instruments/bulk?asset_group=cefi` (all 23 cefi venues, no
      venue filter) → 200, `transfer-encoding: chunked`, 670,695-byte parquet, read back via `pd.read_parquet` as
      13,141 real rows across all 23 venues; unmatched venue → 404. All against live prod data (cefi, day=2026-08-16),
      not a unit-test mock.
- [x] ✅ [BACKEND] P0. **market-tick-data-service: build the external market-data surface.** — SHIPPED
      `market-tick-data-service@6fefa63676` (`api/routers/external.py` 310 lines, `tests/unit/api/test_external_router.py`
      221 lines, 4-line wiring change to `api/main.py`). Verified AT ORIGIN by reading the blobs back from
      `origin/live-defi-rollout`, not from the ship script's exit code; quickmerge's own post-push ancestry check also
      confirmed `6fefa6367` is an ancestor. `ahead=0`.
      **The blocker cleared on its own and the work was never re-done.** The STEP 5.70 adapter-contract-call baseline
      regression (`market-tick-data-service@bd07cfc3`, a different slot's unrelated orchestrator refactor) blocked
      EVERY MTDS quickmerge fleet-wide, not just this todo. Re-running
      `scripts/quality_gates/check_adapter_contract_regression.py --workspace-root <root>` standalone on 2026-08-17
      returned **OK — 378 baselined file(s) at or above minimum**: whoever owned that refactor resolved it upstream.
      **The right call was NOT to regenerate the baseline.** That gate counts
      `classify_venue_error|ADAPTER_FETCH_FAILED|record_captured|record_empty|record_failed` per file and exists
      because a prior incident silently wiped 31 `classify_venue_error` calls — so a count DROP is a real
      shard-level-failure-isolation regression, and "confirm-and-regenerate" would have papered over a correctness bug
      had the call site genuinely gone. It hadn't; the count recovered at source. Recording this because the
      confirm-and-regen path is the tempting one under deadline and is wrong by default for this specific gate.
      **Recovery note**: the completed work sat UNCOMMITTED in the worktree for ~8 hours behind the cleared blocker.
      Liveness was checked before inheriting it (479 min since last edit, no `.agent-claim`, well past the 120s
      protect threshold) and the `.pyc` for `test_external_router` confirmed those tests had actually executed rather
      than merely been written. Issue doc
      [`/plans/archive/issues/mtds_orchestrator_adapter_contract_baseline_regression_2026_08_16.md`](/plans/archive/issues/mtds_orchestrator_adapter_contract_baseline_regression_2026_08_16.md)
      should now be closed as resolved-upstream.
- [x] [BACKEND] P0. **execution-service: build the external instruction-submission surface.** Same auth pattern. One
      endpoint accepting a `StrategyInstructionEnvelope` (already-real schema —
      `unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py`, class
      `StrategyInstructionEnvelope`) and routing it through the existing internal instruction-handling path — this
      surface should be a thin authenticated front door onto real logic, not new instruction-processing code. Done-
      when: a submitted instruction reaches the real handler (verified via a paper-mode round-trip, not a mock),
      `quality-gates.sh --no-fix` green, cited. **execution-service@3567e7a180.** New router
      `execution_service/api/external_instruction_api.py` (`POST /external/instructions`), wired into
      `api/main.py` — the service's actual deployed entrypoint (Dockerfile CMD
      `execution_service.api.main:create_app`), which was previously health-only. Auth via
      `unified_trading_library.cloud_interface.api_auth.create_api_auth("execution-service")` per the upgraded
      framing above. Accepts the real `StrategyInstructionV2` union; TRADE routes through
      `ManualOperationHandler.build_instruction()` -> `ManualOperationHandler.execute()` ->
      `LiveOrchestrator.execute_instruction()` — the identical real, already-tested path DART's internal
      `/manual/instruction` route uses in production (`execution_service/api/manual_instruction_api.py`); no new
      instruction-processing code was written. Non-TRADE actions (SWAP/LEND/BORROW/STAKE/.../CANCEL — the other 10
      `StrategyInstructionV2` variants, which route through a different internal subsystem this session did not
      touch) get an honest HTTP 501, never a silent drop. Paper-mode round-trip evidence (real, not mocked):
      `tests/unit/test_external_instruction_api.py::TestExternalInstructionSubmission::test_trade_envelope_reaches_the_real_handler_and_produces_a_real_paper_fill`
      POSTs a real `TradeInstruction` envelope (validated by the real `StrategyInstructionV2` Pydantic union) through
      the real FastAPI route to a real (non-`unittest.mock`) `PaperLiveOrchestrator` implementing the same
      `LiveOrchestrator` protocol a live venue orchestrator satisfies — deterministic paper fill: qty=1.5,
      price=42000.00 (from the envelope's own `reference_price`), status=COMPLETED, and the object the orchestrator
      received carries the venue/side/instrument/quantity the envelope->`StrategyInstruction` conversion computed
      (`venue="binance"`, `side="BUY"`, `instrument_id="BTC-USDT"`) — only the live-venue-credential boundary was
      stood in for. `quality-gates.sh --no-fix` full run GREEN (156s, sha `cd6800303df525cd5f16a85c80d43b59b52fcf47`
      == HEAD at ship time). **Found, not acted on (matching-engine-adjacent, explicitly out of this session's
      scope)**: `ManualOperationHandler`'s lazily-created production orchestrator
      (`execution_service/cli/handlers/live_execution_handler.py:_create_orchestrator_for_venue` ->
      `execution_service.engine.orchestrator.ExecutionOrchestrator`) does not actually structurally satisfy the
      `LiveOrchestrator` protocol it's `cast()` to — `ExecutionOrchestrator.execute_instruction()` takes a different
      `Instruction` type (`execution_service.engine.execution.types.Instruction`, needs `.algorithm`/`.params`) and
      returns `None`, not the `StrategyInstruction`/`dict[str, object]` the protocol and `ManualOperationHandler`
      expect. Every existing test of this path (`tests/unit/test_manual_operation.py`,
      `tests/unit/test_manual_instruction_close_all_contract.py`) mocks the orchestrator, so this mismatch is
      real and pre-existing but untested end-to-end — worth a follow-up todo for whichever session next touches the
      matching engine.

## W2 — Archetype feature-group scaffold

- [x] [REVIEW] P1. ✅ Operator reviewed the [Archetype Feature
      Scaffold](https://claude.ai/code/artifact/c6c345e7-10fb-4679-b9d2-6eada7fc3f6c) 2026-08-16 and approved the
      35-row High-confidence tier for declaration. Shipped —
      `unified-api-contracts@a617bbdf` ("feat: declare 35 High-confidence StrategyArchetype feature_group mappings
      (operator-reviewed scaffold, W2)"): `ARCHETYPE_FEATURE_GROUPS` grew from 5 to 40 declared archetypes (verified
      via direct Python import: `len(ARCHETYPE_FEATURE_GROUPS)==40`, `len(UNDECLARED_ARCHETYPES)==20`,
      `40+20==60` ✓); the module docstring now honestly distinguishes the two evidence tiers (dispatch-code-traced
      vs. operator-reviewed-scaffold) rather than conflating them. One real, correct side-effect caught by
      `quality-gates.sh` and fixed in the same commit:
      `tests/unit/test_venue_strategy_consumability.py::test_venue_with_no_satisfying_archetype_fails` asserted a
      venue offering only `ohlcv_1m` satisfies no archetype — no longer true, since `ML_DIRECTIONAL_CONTINUOUS`/
      `RULES_DIRECTIONAL_CONTINUOUS`/`TSMOM_BTC_CTA` all resolve to `ohlcv_1m`-only inputs now. Fixed the fixture to
      `mev_events` (a real registry gap — zero feature_group consumers anywhere) rather than weakening the check.
      `quickmerge.sh` printed a transient exit-10 "silent revert" warning mid-run (a concurrent peer's push landing
      during the Not-Behind Gate) — verified directly (file content diff + `git show HEAD:<path>` + `git
      merge-base --is-ancestor HEAD origin/live-defi-rollout`) that the final commit genuinely landed with the full
      change on both local HEAD and origin before treating it as done; not a blind re-run.
- [x] [REVIEW] P2. ✅ Fully resolved 2026-08-18 — `unified-api-contracts@0f2e43ad3e`, `@1595fdc149`. This todo's own "12 Low
      registry gap" framing turned out to be an undercount: an operator follow-up ("I'm surprised we can't do the
      vaults, the pools, the perp inverse... dated carries") prompted a real features-service investigation, which
      found live, already-dispatched calculators for 6 of the 12 supposed gaps — perp funding (`perp_funding_rates`,
      one CeFi and one DeFi-Hyperliquid calculator, both writing under `asset_group=cefi`), DeFi LP/vault
      (`vault_share_price_apy`, `pool_invariant_drift`, `dex_pool_swap_flow`, `concentrated_liquidity_il_realised`).
      Declared `CARRY_BASIS_PERP`/`_INV`, `CARRY_FUNDING_DISPERSION`, `DEFI_LP_VAULT`, `DEFI_LP_POOL`,
      `DEFI_LP_CONCENTRATED` against them — each cited to a real dispatch site (`onchain/engine/orchestrator.py` /
      `onchain/schemas/feature_builder_registry.py`), never inferred from naming. Also declared `EVENT_DRIVEN`
      (scoped by the operator to "earnings results and corporate actions... macro news from Fred or Forex Factory")
      against `yield_curve` + `economic_results`, both real FRED-sourced-via-MTDS feature_groups. **Found and
      excluded rather than silently wired**: `corporate_actions` (dividends/splits) is live but sourced exclusively
      from `polygon_corporate_actions_adapter.py` — Massive-fka-Polygon.io, fleet-banned — filed as
      `features_service_corporate_actions_polygon_io_banned_vendor_2026_08_18.md`, with a real precedent already in
      the same handler (`yfinance` already used for its earnings leg) proposed as the fix; `earnings_results` is
      genuinely yfinance-clean and live-dispatched but reads a live external API call, not a captured
      `(asset_group, data_type)` MTDS shard, the same input-shape mismatch as `economic_events`/`forexfactory` —
      correctly left undeclared, though an earlier note in the code wrongly said "no dispatch site," caught and
      fixed before shipping. Separately filed
      `features_service_calendar_domain_manifest_tracking_gap_2026_08_18.md`: the whole calendar family (including
      the newly-declared FRED legs) writes to a real, documented path convention but is entirely invisible to the
      honest-coverage manifest — no `record_captured` call anywhere in that domain. 2 test failures surfaced by the
      new declarations (`yield_curve`/`economic_results` needed `fetch_completed_at`, not `tick_timestamp`) — fixed
      before shipping, full `quality-gates.sh --no-fix` green (422s).

      **Second wave, same day** — `unified-api-contracts@1595fdc149`. Operator instruction: "do all the medium
      confidence. for mev what do we actually need and double check mtds or features don't expose [it]." Declared
      all 8 remaining Medium-confidence rows by direct analogy to an already-declared sibling archetype
      (`ARBITRAGE_CROSS_DOMAIN_EVENT`, `MARKET_MAKING_ML_LEAN`, `ML_DIRECTIONAL_EVENT_SETTLED`,
      `RULES_DIRECTIONAL_EVENT_SETTLED`, `VOL_ML_LEAN`, `PORTFOLIO_FACTOR_ALLOCATION`, `PORTFOLIO_RISK_PARITY`,
      `PORTFOLIO_TACTICAL_OVERLAY`) — same weaker evidence tier as the original 35, not upgraded to dispatch-traced,
      each comment states the sibling it copies and its specific weak point. For MEV, ran the requested
      double-check exhaustively rather than re-asserting the prior finding: confirmed `mev_events_handler.py` in
      MTDS really does capture real rows, then searched the WHOLE workspace (features-service,
      market-data-processing-service, strategy-service, execution-service) and found zero consumers anywhere —
      the earlier finding held. Went further per "what do we actually need": `mev_events` only logs MEV that
      ALREADY happened; backrun/sandwich/JIT-liquidity/liquidation-bundle strategies need to act on a pending
      transaction before someone else does, which needs mempool visibility — a data source this codebase has no
      adapter for at all. This reframes the MEV gap as a missing data-capture capability, not a missing
      feature_group declaration — a materially different (and larger) piece of work than the other 4 filed issues
      this session. **Registry now 55/60** — the only 5 remaining are the 4 MEV archetypes (genuine
      infrastructure gap) + `PORTFOLIO_MULTI_STRATEGY` (structural input-shape mismatch, not a naming gap). Full
      `quality-gates.sh --no-fix` green again before shipping. Scaffold artifact refreshed to match:
      [Archetype Scaffold Review](https://claude.ai/code/artifact/e9c372d4-211c-4776-9719-0b671d730116).

## W3 — Granularity declaration (step 13) — NOW THE CRITICAL PATH FOR THE ARTIFACT (operator ruling 2026-08-17)

> **W3 is no longer "land early, independent" — it BLOCKS the artifact's numbers.** Finding 2026-08-17: the venue
> denominator is **`(venue, data_type)` 2-tuples only** — 353 pairs — because `VENUE_DATA_TYPE_CAPABILITIES` is
> `dict[str, VenueCapabilityRecord]` keyed by venue with a per-data_type dict inside, and **has no instrument_type
> axis at all**. The denominator script's own docstring says so: _"(venue, data_type) pairs, not venue count."_
>
> **The mismatch**: the coverage NUMERATOR already goes to 3-tuples where data supports it — the TradFi audit
> produced `(venue × instrument_type × data_type)` cells, 244 of them, and canonical GCS paths carry
> `instrument_type=` as a partition key. So a venue carrying `trades` on both spot and perp is ONE denominator pair
> but TWO real coverage cells. Any percentage computed as captured-cells ÷ 353 divides one unit by another. The
> artifact's collapse hierarchy is AG → venue → instrument_type → data_type, so its leaf level currently has no
> denominator to divide by.
>
> **OPERATOR RULING 2026-08-17 — land the instrument_type axis FIRST, then measure once at 3-tuple granularity
> throughout.** Chosen over (a) publishing at `(venue, data_type)` and collapsing the tree a level, and (b)
> publishing mixed granularity per AG with the unit stated. Rationale: cleanest numbers, measured once, and it
> removes a whole class of unit-mismatch error from a client-facing document — accepted as real registry work ahead
> of the Tuesday target.
>
> **Consequence for sequencing**: no artifact percentage is final until this lands. The batch-2 audit's per-shard
> work should run AFTER the axis exists, or it measures against a denominator that is about to change.

**Ruled 2026-08-16** in `venue_readiness_and_registry_hardening_2026_08_16.md`: a UAC registry, keyed per
`(venue × instrument_type × data_type)`, extending `VenueCapabilityRecord`
(`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`) — it already carries the
`(venue × data_type)` axis this needs, missing only the instrument-type axis and the granularity/exceptions fields.
Seed from manifest + plans + code, never hand-populated; where the three disagree, **the manifest is the measurement
and wins** — a disagreement is itself a finding, not a tie to break quietly. Do not conflate this with per-venue
coverage-*start-dates* (an interval) — step 13 asks for the achievable *fidelity tier*, a different axis (the
tradfi sub-agent's pre-audit read conflated these; correct that reading here, don't repeat it).

- [x] [AGENT] P0. ✅ Done 2026-08-17 (operator ruling 2026-08-17, `/plans/epics/system_readiness_master.md` W3) —
      `unified-api-contracts@d19866d339`. **Land the
      instrument_type axis on the coverage DENOMINATOR itself** — distinct from the granularity/fidelity-tier item
      below, which extended the CONCEPT for a different question (what tier is achievable in a cell already known to
      exist). This item answers which (venue, instrument_type, data_type) cells exist at all. Additive, not a
      mutation of `VENUE_DATA_TYPE_CAPABILITIES` (same repo-wide-migration reasoning the granularity item already
      recorded): new module `unified_api_contracts/registry/venue_instrument_type_axis.py` inverts the existing,
      already-tested G1-ENUM validity combinator (`VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` +
      `valid_data_types_for_venue_instrument_type`) rather than a fresh hand-authored table — "what the code already
      encodes," per the operator's seeding instruction. **Measured: 353 → 660 (venue, instrument_type, data_type)
      triples** (12 (venue, data_type) cells, 3.4%, disclosed as unresolved rather than silently dropped or
      force-matched — pre-existing G1-ENUM combinator gaps, e.g. FRED's `ohlcv_1d`/`yield_curve` have no covering
      tradfi instrument_type roster entry). `generate_venue_universe_denominator.py` now reports BOTH — the old
      2-tuple figure for comparison and the new 3-tuple figure as THE denominator. **Two real over-counting bugs
      found and fixed while landing this, not fabricated as a clean inversion**: (1) a naive full-roster probe
      multiplies every sports `odds` cell 5x — `fixture`/`exchange_odds`/`fixed_odds`/`prop` all list `"odds"` in
      their valid-data_types set, but `market_data_categories.py`'s own comment marks them "future fixture-grain
      scaffolding... NOT consulted by the real producer," unlike `("sports","odds")` itself (CONFIRMED against
      1,806,527 real captured rows) — excluded the four scaffolding rows so every real bookmaker cell resolves to
      exactly `{"odds"}`. (2) a naive DeFi probe over the full cross-protocol instrument_type union leaked unrelated
      protocols' instrument_types onto each other via `valid_data_types_for_venue_instrument_type`'s own documented
      "protocol doesn't declare this type → fall back to the global union" fallback (built for a different, forward,
      use case) — measured live: `AAVE_V3-ETHEREUM` (lending-only) wrongly resolved `oracle_prices` to
      `PERPETUAL`/`STAKING`/`SPOT_PAIR`/`SOLANA_VAULT` before the fix; narrowed the DeFi roster to each venue's OWN
      protocol before probing, which also dropped total triples from a garbage 1365 to the correct 660. 10 new unit
      tests (`tests/unit/test_venue_instrument_type_axis.py`) cover both regressions directly plus the full-registry
      accounting invariant (every declared pair is either a triple or a disclosed unresolved cell, never silently
      dropped). Full `quality-gates.sh --no-fix`: ALL QUALITY GATES PASSED (191s), sentinel
      `8df50774f21bc5e75fc8e72752715acd4a375372` == HEAD at ship time.
      **Docs still quoting the stale 353 figure, listed not edited per this dispatch's explicit boundary** (other
      agents reading them this session): `/plans/active/venue_e2e_wiring_2026_08_16.md`,
      `/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`,
      `/plans/active/nick_ai_platform_readiness_remediation_finalize_2026_08_16.md:113`.
- [x] [AGENT] P0. ✅ Done 2026-08-16 — `unified-api-contracts@693e823adb`. **Extend `VenueCapabilityRecord` with the
      instrument-type axis + granularity/exceptions fields**, seeded from a reconciliation of the live manifest,
      `VENUE_DATA_TYPE_CAPABILITIES`, and the readiness-contract's own fidelity vocabulary. Built ADDITIVELY rather
      than mutating `VenueCapabilityRecord` in place (that dict has ~192 manually authored entries across 2 files with
      no instrument_type key anywhere in its shape — a repo-wide breaking migration outside this todo's scope): new
      module `unified_api_contracts/registry/venue_granularity.py` (+ `venue_granularity_seed.py` for the literal seed
      data, split out the same way `defi_venue_capabilities.py` was split from `market_data_categories.py`) declares
      `GranularityRecord`/`VenueDataTypeGranularity`/`get_granularity(venue, instrument_type, data_type)`, using the
      REAL vocabulary — `unified_api_contracts.internal.domain.matching_engine.BookType` (6 members: `L2_MBP` >
      `CANDLE_BOOK_COLS` > `L1_MBP` > `L0_TOB`, plus `AMM`/`ALPHA_ZERO`) — not the 3-member `ExecutionFidelityTier`
      the dispatch prompt's own text named (that closed enum has no `L0_TOB`/`AMM`/`ALPHA_ZERO` members; `BookType` is
      the one that does). Seeded: fresh live pulls of `_index/availability_index.parquet` for cefi/tradfi/sports/
      prediction (401/362/315/199MB, via UTL `download_from_storage` — the existing single-file manifest-index read
      path, not a corpus walk) reconciled against `VENUE_DATA_TYPE_CAPABILITIES`; DeFi seeded from code only
      (`DEFI_VENUE_DATA_TYPE_CAPABILITIES`) since its index measured 6.8GB (~17x every other AG) and a fresh pull
      would have crossed into the single-walk-discipline-banned territory. 412 populated `(venue, data_type)` cells
      across all 5 asset groups (187 manifest-sourced + 225 code-sourced). Every manifest-vs-code disagreement found is
      cited in `GRANULARITY_DISAGREEMENTS` (10 entries) — including the flagship finding: COINBASE-SPOT has 49,638
      real captured `book_snapshot_5` rows since 2020-01-01 even though `MVP_SCOPE['cefi']` declares it `{trades}`-only
      — plus 8 over-declared cells (code says captured, manifest measured 0 rows), a new undeclared `depth_of_book_10`
      data_type at 4 major CeFi venues, and the sports derived/retired-type exclusion category. 17 unit tests
      (`tests/unit/test_venue_granularity.py`) cover query resolution, the instrument_type-exception override
      mechanism, registry population per asset_group, and that the disagreement citations are actually present, not
      just in code comments. Full `quality-gates.sh --no-fix`: ALL QUALITY GATES PASSED (270s).

## W4 — Per-AG BACKTESTABLE blockers

- [x] [AGENT] P1. ✅ **CeFi: close the wallet-capability + error-classification gaps.** —
      `unified-api-contracts@a0e6f3b9e7`. Confirmed `transfer_types.py::VENUE_WALLET_CAPABILITIES` is the real
      cefi-scoped registry (its downstream consumer, `defi/wallet_config.py`, cites it 3x as the SSOT venue-name
      source and carries no per-venue capability data of its own — it's custody/wallet-provisioning config).
      Both registries now cover 25/25 canonical cefi venues (`VENUES_BY_ASSET_GROUP["cefi"]`), verified via a direct
      Python import against the real call-site-derived family mapping (bitfinex_native.py/bitget_native.py default
      `venue=` to the bare family string — confirmed by direct read of execution-service, not assumed; 0 missing on
      both axes). Fixed 2 pre-existing stale, non-canonical keys in `VENUE_WALLET_CAPABILITIES` in the same pass
      (bare `"OKX"` — removed from the venue universe 2026-08-04 — and `"BYBIT-FUTURES"` — never a declared venue,
      Bybit's UTA covers spot+derivatives under `"BYBIT"` alone) rather than leaving them as unreachable dead keys.
      Added 16 new wallet-capability entries + 6 new error-classification families (`bitfinex`/`bitget`/
      `coinbase_cde` in `cefi.py`; `pacifica`/`extended`/`lighter` in `onchain_perps.py`, matching the existing
      HYPERLIQUID/ASTER on-chain-CLOB placement convention rather than duplicating into cefi.py). Sourced from real
      material: ccxt's vendored per-exchange exception tables (bitfinex/bitget — a maintained mirror of each
      exchange's own documented codes) and each adapter's own real `_classify_*_error()` normalization function
      (coinbase_cde/pacifica/extended/lighter — direct-read-confirmed). One genuine `unverified` gap flagged inline:
      `EXTENDED-STARKNET`'s `custody_provider` left empty rather than asserting "copper" — StarkNet's Cairo-VM/
      STARK-curve signing differs from every other ON_CHAIN entry's secp256k1/EVM curve, and Copper's public
      supported-chain list was not confirmed to cover it; no real-fund custody assignment invented without a direct
      check. `quality-gates.sh --no-fix` green (272s, sentinel `3f1e133f759842c16e9975d69cdb403a147c316b` == HEAD at
      ship time).
- [x] [AGENT] P1. ✅ **Sports: fix the mock-only live config + resolve the step-8 registry contradiction.** Both
      halves done. Mock-config half: `deployment-api@8239f10a77` (prior session, see Progress Log entry above).
      Step-8 registry-contradiction half: `unified-api-contracts@96ef3e173f`. Confirmed the contradiction directly
      (read both sides, not the prior session's summary): `VENUE_TO_ADAPTER_KEY`'s `NO_ADAPTER_YET` sentinels for
      BETFAIR_EX_UK/BETFAIR_EX_EU/MATCHBOOK/PINNACLE/etc. are CORRECT and NOT stale — that registry is specifically
      the URDI/instruments-service REFERENCE-DATA axis (own docstring: "instruments-service owns the key→class
      instantiation table"), a different service and question from execution capability, and IS genuinely has no
      reference-data adapter for these MTDS-owned odds venues. The actually-stale side was `is_venue_executable()`
      itself: the 2026-08-08 sports-taxonomy-P1 operator ruling
      (`sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`, cited in `market_data_categories.py`'s own comment)
      explicitly ordered it to become "a SEPARATE executable predicate" from the data axis, but its body was left as
      a bare passthrough of `VENUE_TO_ADAPTER_KEY` — it never actually diverged. Fixed by adding
      `SPORTS_EXECUTION_ADAPTER_VENUES` (a new, verified frozenset naming the exactly-4 bookmaker families with a
      real, wired execution-service adapter — confirmed via direct directory listing of
      `execution_service/sports_execution/adapters/exchanges/` + `routing.py::SportsExecutionRouter._build_adapter`:
      betfair.py → BETFAIR_EX_UK/BETFAIR_EX_EU only, betfair.py's real BACK/LAY logic is Exchange-product-specific —
      Sportsbook/BETFAIR_SB_UK has no such API and is deliberately excluded; matchbook.py → MATCHBOOK; kalshi.py →
      KALSHI; polymarket_clob.py → POLYMARKET. SMARKETS is cited as a design target in strategy-service's
      `MarketMakingEventSettledEngine` source comment (`archetype_leg_spec_seeds.py`) but has NO real adapter file
      today, confirmed by direct listing — deliberately excluded) and making `is_venue_executable()` check it OR the
      data axis. Also fixed the now-provably-wrong same-day comment in `market_data_categories.py` that asserted
      "None has a real IS/URDI execution adapter" for the whole 22-bookmaker block including MATCHBOOK — a doc that
      misled this session, corrected in the same commit per the findings-triage HARD RULE. Did NOT touch
      execution-service (read-only per task scope — its dispatch map was already correct, nothing to fix there).
      `quality-gates.sh --no-fix` green on unified-api-contracts (255s, sentinel
      `a0e6f3b9e779fed7f15aa329d6c92d0e9c18ec21` == HEAD at ship time).
- [x] [AGENT] P2. ✅ **Sports: confirm or add the back/lay action mapping (W5).** —
      `unified-api-contracts@4753c4bbcd`. Confirmed by direct read: back/lay is NOT `TradeInstruction.side` (that
      class has no `side` field — it has `direction: Literal["LONG","SHORT","FLAT"]`, a plausible but NOT the
      verified path) and is NOT a member of `InstructionActionV2` or `AccountActionV2` directly. The real, concrete,
      already-existing resolution: back/lay is modeled as two DISTINCT instrument-type variants
      (`instrument_type="BET_BACK"`/`"BET_LAY"`, informal string labels, not real `InstrumentType` enum members) of
      the SAME `InstructionActionV2.QUOTE` action, per the two `CompatibilityEntry` rows already declared in
      `schemas.py`'s `COMPATIBILITY_SEED` for the `MARKET_MAKING_EVENT_SETTLED` archetype — strategy-service's
      `MarketMakingEventSettledEngine` (cited in UAC's own `archetype_leg_spec_seeds.py`) emits "2x QuoteInstruction
      BET_BACK+BET_LAY" per market. Concretized downstream in `CanonicalSportsOrder.bet_side: str  # BACK | LAY`
      (`unified_api_contracts/internal/domain/sports/execution.py`), set from execution-service's real Betfair
      adapter's own `side: str` parameter (`sports_execution/adapters/exchanges/betfair_order_mapping.py::place_order`
      — read directly, confirmed real, not mocked). Added citation comments at both the `COMPATIBILITY_SEED` BET_BACK/
      BET_LAY rows and the `bet_side` field pointing at each other + the real engine, closing the audit's "plausibly
      ... unconfirmed" gap with a concrete, bidirectional code citation — no schema change needed, the mapping was
      already correct, just undocumented. `quality-gates.sh --no-fix` green (208s, sentinel
      `96ef3e173f951ffa51add1711d7b5bed04c18412` == HEAD at ship time).
- [x] [AGENT] P1. ✅ Done 2026-08-16 — `execution-service@0e1b7b98dd`. **Prediction: wire Polymarket into the existing
      matching engine for paper mode.** Step 1 confirmed this was a WIRING task, not a new-engine task: a real,
      working depth-walked matching-engine path already exists for CeFi
      (`execution_service/providers/matching_engine.py::MatchingEngineExecutionProvider` +
      `execution_service/providers/l2_depth_provider.py::L2DepthProvider`, proven by pre-existing
      `tests/unit/providers/test_matching_engine_provider.py`) — `_execute_l2`/`walk_book_for_fill` are already
      venue-agnostic, and the JSON bid/ask-array row parser (`L2DepthProvider._row_to_snapshot`/`_parse_level_list`)
      already handles Polymarket's real `book_snapshot_5` wire format (JSON arrays of `[price, size]`) byte-for-byte
      unchanged — proven directly by a new test feeding it real Polymarket-shaped JSON strings. The ONLY genuine gap
      was `L2DepthProvider`'s GCS-prefix resolution being hardcoded to the CeFi Binance-ETH-PERP MVP shape (no
      `asset_group` parameter existed at all). Closed it: `L2DepthProvider.load_date()`/`_l2_candidate_prefixes()`
      now accept `asset_group="prediction"`, resolving the real UAC canonical path
      (`asset_group=prediction/venue=POLYMARKET/instrument_type=prediction_market/data_type=book_snapshot_5/
      {condition_id}.parquet`) via `unified_api_contracts.gcs_paths.candidate_parquet_paths` — CeFi's default path is
      byte-for-byte unchanged (regression test asserts this). Also wired the actual PRODUCTION consumer,
      `execution_service/engine/handlers/prediction_handler.py::PredictionBetHandler`, which previously computed
      every backtest/paper fill via a flat `benchmark_price + 10bps` heuristic regardless of real book data (the
      "from-scratch simulator" fallback the operator's ruling said not to use) — it now prefers a genuine
      `walk_book_for_fill` VWAP fill via a shared `L2DepthProvider` for POLYMARKET, falling back to the flat-spread
      heuristic only on honest absence of loaded book data (unwired venue — KALSHI deliberately excluded, its
      `book_snapshot_5` is measured far thinner in the pre-audit — or no snapshot loaded for that timestamp).
      **Fidelity tier: `BookType.L2_MBP`** — cited from two independent real registries, not assumed:
      `unified_api_contracts.registry.venue_granularity.get_granularity("POLYMARKET", "prediction_market",
      "book_snapshot_5")` (manifest-sourced 2026-08-16, `source="manifest"`) and
      `execution_service.matching_engine.engine.MatchingEngine.get_book_type_for_asset_group("prediction")`, which
      independently agree. Real-fill evidence (non-mock): a large BUY against an injected real 3-level Polymarket ask
      book (`[[0.65,200],[0.66,150],[0.67,100]]`) walks 2+ levels and fills strictly above the best ask (VWAP, not a
      flat markup); a small BUY fills at the exact best-ask price with `levels_walked==1` — both proven through the
      real `PredictionBetHandler.execute()` → `walk_book_for_fill()` path, not a mocked interface.
      **Precisely-scoped remaining gap (not fixed here, out of this task's bounded scope)**: `ExecutionInstruction`
      has no `side` field, so the real-depth fill only walks the ASK side (BUY the named outcome's shares, mirroring
      `PolymarketAdapter.place_bet`'s BACK→BUY convention) — a SELL/LAY leg needs a side signal added to
      `ExecutionInstruction` first, a separate schema change. Also cross-referencing
      `/plans/archive/2026_08/execution_service_live_orchestrator_protocol_mismatch_untested_2026_08_16.md`: this
      Prediction wiring does NOT touch `ManualOperationHandler`/`LiveOrchestrator`/`ExecutionOrchestrator` at all —
      `PredictionBetHandler` is a fully separate dispatch path (`OperationType.PREDICTION_BET` via
      `HandlerRegistry`), so that issue's protocol-mismatch landmine was not in this task's path, confirmed by
      direct read rather than assumed. 4 new/extended tests (9 total across the two touched test files) +
      `quality-gates.sh --no-fix` full run GREEN (185s, sentinel `23ab0a25991d7da68b6dc8486e6af2d850be1a59` == HEAD
      at ship time; one method-size-cap fix needed after first run — split `execute()`'s two result-building
      branches into `_book_fill_result`/`_flat_spread_fallback_result` helpers).
- **DeFi — no new todo.** See the "Two findings" section above; the pause is already correctly diagnosed and gated
  in `/plans/active/defi_consolidated_closeout_2026_07_18.md` Track 8. Nothing to add here.

## W6 — Codex refresh: deferred to the gated finalize companion

Refreshing `/codex/02-data/honest-coverage-model.md`'s stale certified numbers (defi/tradfi/sports/prediction) needs
the FINAL post-remediation state, not the pre-remediation snapshot — tracked in
[`nick_ai_platform_readiness_remediation_finalize_2026_08_16.md`](/plans/active/nick_ai_platform_readiness_remediation_finalize_2026_08_16.md),
gated on this plan via `depends_on` + `gate_on_depends: true`.

## Known traps (already applied once in the pre-audit; re-apply during remediation)

Probe the vocabulary the writer emits (registries key on CONSTANTS, not literals) · 0 hits ≠ missing, check the
directory before concluding absence · `canonical_path_violations()` is path-structure-only, value-blind · stale
`/data-pipeline-check-*` skills — read the real registries directly · sports 2020-06 data floor already applied
upstream · Databento boundary is by SOURCE not asset group · never weaken a check to make a state pass — an accurate
`unverified` is correct output, not a failure to fix · **credentials gate RUNNING, never BUILDING** — build the full
path, mark `BLOCKED-CREDENTIALS` where it can't run · do not edit the artifact HTML — the operator reviews numbers
before they reach a client document.

## Progress Log

**2026-08-16 — W4-CeFi, W4-Sports step-8 (UAC half), and W5 shipped (interactive sub-agent, `unified-api-contracts`
only, per the dispatch prompt's repo scope).** Executed 3 bounded todos, shipped as 3 separate quickmerges (one QG
sweep covered items 1-2's diffs together sequentially; item 3's own small diff got its own fast green re-run) —
`unified-api-contracts@a0e6f3b9e7` (W4-CeFi), `@96ef3e173f` (W4-Sports step-8), `@4753c4bbcd` (W5). Full evidence in
each checkbox above; summary of the one genuinely investigative finding: the step-8 "registry contradiction" the
prior session flagged was NOT what it looked like — `VENUE_TO_ADAPTER_KEY`'s `NO_ADAPTER_YET` sentinels for the
sports bookmakers are correct (that registry is the URDI/instruments-service reference-data axis, not execution);
the real bug was `is_venue_executable()` never actually implementing the "separate executable predicate" the
2026-08-08 operator ruling ordered — it was still a bare passthrough of the data-axis sentinel. Fixed at the root
(new `SPORTS_EXECUTION_ADAPTER_VENUES` frozenset + `is_venue_executable()` now ORs both axes) rather than editing
`VENUE_TO_ADAPTER_KEY` itself, which would have broken the URDI resolution path for venues with no real
reference-data adapter class (execution-service adapters live in a completely different factory/service than
instruments-service's URDI adapters — plugging an execution-service adapter name into `VENUE_TO_ADAPTER_KEY` would
have made `get_adapter_for_canonical_venue()` try to instantiate a nonexistent class). Also found and fixed (same
commit) a stale same-day comment in `market_data_categories.py` that asserted zero real execution adapters for the
whole 22-bookmaker block, which was wrong for MATCHBOOK. Did not touch execution-service anywhere (read-only per
task scope) — confirmed its real dispatch map (`SportsExecutionRouter`) needed no fix, only UAC's stale predicate
did. No blockers hit on any of the 3 items; all done-when criteria met with live, direct-read-verified evidence, not
assumed from the prior session's summary.

**2026-08-16 — W3 granularity registry shipped.** `unified-api-contracts@693e823adb`. Built the step-13 granularity
declaration as a NEW additive registry (`venue_granularity.py` + `venue_granularity_seed.py`) rather than mutating
`VenueCapabilityRecord` in place — that dict's ~192 entries have no instrument_type key anywhere in their shape, so
reshaping it live was out of scope; the new registry expresses the (venue x instrument_type x data_type) axis via a
per-(venue, data_type) default + per-instrument_type exceptions, proven queryable by 17 unit tests. Corrected a
citation drift while building it: this todo's own text (and the umbrella plan's GRANULARITY section) both named
`execution_fidelity.py`'s vocabulary as `L2_MBP > CANDLE_BOOK_COLS > L1_MBP > L0_TOB` plus `AMM`/`ALPHA_ZERO`, but
`execution_fidelity.py`'s actual `ExecutionFidelityTier` enum is a DIFFERENT, narrower 3-member closed enum
(`L2_TICK`/`CANDLE_BOOK_COLS`/`OHLC_BAR`) with none of those 6 names — the real 6-member vocabulary lives in
`unified_api_contracts.internal.domain.matching_engine.BookType`, which this registry uses instead. Real reconciliation
against a FRESH manifest pull (cefi/tradfi/sports/prediction — 401/362/315/199MB `_index/availability_index.parquet`
files via UTL `download_from_storage`, the existing single-file manifest-index read path) found 10 disagreement
findings, all cited in `GRANULARITY_DISAGREEMENTS` rather than silently resolved — the standout: COINBASE-SPOT has
49,638 real captured `book_snapshot_5` rows since 2020-01-01 even though `MVP_SCOPE['cefi']` declares it `{trades}`-only
(execution_fidelity() therefore always clamps it to OHLC_BAR); also a previously-undeclared `depth_of_book_10` data_type
(10-level CeFi depth, richer than `book_snapshot_5`'s 5-level) with real captured rows at 4 major venues and zero
mention anywhere in `VENUE_DATA_TYPE_CAPABILITIES` or `MVP_SCOPE`. DeFi's own `_index/availability_index.parquet`
measured 6.8GB (~17x every other asset_group's) — deliberately NOT pulled fresh this session (single-walk discipline:
a multi-GB ad-hoc download to seed one registry crosses out of "reuse the existing read path"); DeFi's 225 rows are
seeded from `DEFI_VENUE_DATA_TYPE_CAPABILITIES` (source="code"), disclosed as a real, non-silent gap in this session's
reconciliation completeness rather than presented as manifest-verified. Also found `market_data_categories.py`'s own
`BASE_GRANULARITY_BY_DATA_TYPE` constant is named "granularity" but encodes a data_type's TEMPORAL SAMPLING CADENCE
(step 14/15 territory), not this module's step-13 fidelity-tier/depth concern — a naming collision worth a doc note
for whoever tackles steps 14/15, not fixed here (renaming a live imported constant was out of scope). Cross-referenced
into `/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`'s "Publish the granularity view" P1 todo
(that todo can now render from this registry). Full `unified-api-contracts` `quality-gates.sh --no-fix`: ALL QUALITY
GATES PASSED (270s, 17/17 new tests green).

**2026-08-16 — W4 Sports mock-config half done (step-8 registry-contradiction half still open — see checkbox).**
`deployment-api@8239f10a77`. Wired `deployment-api/deployment_api/routes/sports_venues.py`'s `GET /sports/venues`
off the hardcoded `{"venues": [], "status": "live_not_configured"}` stub. Read the sibling pattern
(`routes/venue_credentials.py`) and the real credential source (`execution-service/execution_service/
adapters/sports_factory.py::_LIVE_VENUE_CONFIGS`, consumed by `sports_execution/routing.py::SportsExecutionRouter`)
before writing anything — deployment-api has no Python dependency on execution-service (no service↔service deps),
so live mode probes Secret Manager directly for the SAME secret names `SportsExecutionRouter` loads
(`betfair-app-key`, `matchbook-username`, `kalshi-api-key-id`, `polymarket-clob-api-key`), never
re-implementing adapter/credential logic. Deliberately scoped to the 4 real, adapter-backed venues only —
did not fold in bookmakers still `NO_ADAPTER_YET` in UAC's `venue_adapter_keys.py` (confirmed live: `BETFAIR_EX_UK`,
`PINNACLE`, `DRAFTKINGS` etc. are still `NO_ADAPTER_YET` there despite real adapters existing in execution-service —
this IS the step-8 registry contradiction the other half of this todo covers; left untouched, not my scope).
Left `update_venue_credentials`/`check_venue_health`/`enable_venue`/`disable_venue` on their honest
`live_not_configured` stub — no real backend exists for those mutations, and inventing one wasn't asked.

Live curl evidence (local uvicorn, `DISABLE_AUTH=true ENVIRONMENT=development GCP_PROJECT_ID=central-element-323112`,
real ADC, real Secret Manager — not mocked): `GET /sports/venues` returned real per-venue status —
`betfair` and `kalshi` show `"status":"active","has_credentials":true` (real secrets `betfair-app-key`/
`kalshi-api-key-id` resolved), `matchbook`/`polymarket` show `"status":"unconfigured","has_credentials":false`
(no secret present) — 4/4 real venues, no `live_not_configured` stub anywhere in the response.
`status_filter=active` correctly narrowed to the 2 configured venues. `quality-gates.sh --no-fix` green
(sentinel `98edcd6f301ddc38a0030808eb29e9cc5d0f7eee`, matches landed HEAD's parent).

Adjacent finding (fixed in the same commit, zero regression risk — no test file existed for that route):
`venue_credentials.py:87` called `get_secret_client(project_id)` — a positional-arg bug that lands `project_id`
in the function's `provider` parameter (UTL signature is `get_secret_client(provider=None, project_id=None, ...)`),
which raises `ValueError("Unsupported cloud provider")` on every real (non-empty) project_id. Used the correct
`project_id=` keyword form in the new sports code and fixed the one sibling instance directly in this file family.
**3 more instances of the same bug pattern found but NOT fixed** (different files, outside this task's scope,
`infra_health.py` in particular being a CI/CD-adjacent health gate that deserves its own blast-radius check before
an ad-hoc fix) — filed as
[`/plans/archive/issues/deployment_api_client_factory_positional_project_id_bug_2026_08_16.md`](/plans/archive/issues/deployment_api_client_factory_positional_project_id_bug_2026_08_16.md).
Operator notified in this session's final report per the findings-triage HARD RULE (CI/CD-adjacent = worth a flag,
even though not itself data-correctness/cross-repo).

**2026-08-16 — authored.** Read the two source docs (nick_ai plan §§5-6, full pre-audit results) plus the venue-
readiness umbrella plan and `defi_consolidated_closeout_2026_07_18.md` Track 8 before drafting — found the two
scope-changing landmines documented above (W2 fabrication risk, W4-DeFi already-answered). Confirmed a better-fitted
auth precedent for W1 (`unified_trading_library.cloud_interface.api_auth`) by reading it directly rather than
mirroring the dispatch prompt's original citation blind. Verified the 3 thin `api/main.py` line counts (62/116/43)
still match the audit exactly. Built and published the W2 scaffold artifact (55 rows, confidence-tagged, grounded in
a direct read of the full `StrategyArchetype` enum + `FEATURE_REQUIRED_INPUTS` registry — not inferred from category
names alone); caught and corrected a real count-drift while building it (enum docstring claims 59/54, a live Python
import measures 60/5/55 — noted in the artifact itself, not silently used the stale number). Operator ruling
2026-08-16 on the Polymarket paper-trading blocker: simulate via the existing matching engine, framed above as a
wiring-first investigation given Polymarket's real CLOB depth data, not an assumed from-scratch build.

**2026-08-16 — W1 execution-service shipped (`execution-service@3567e7a180`).** Built
`execution_service/api/external_instruction_api.py` (new `POST /external/instructions` router) and wired it into
`api/main.py` — confirmed by direct read that `main.py` (not `app.py`) is the container's actual deployed entrypoint
(Dockerfile `CMD uvicorn execution_service.api.main:create_app`); `app.py` is a separate, richer FastAPI app only
served by the CLI's live-execution `--serve` path, already carrying `/manual/instruction` + kill-switch + DeFi
wiring. Auth via `unified_trading_library.cloud_interface.api_auth.create_api_auth("execution-service")` (read the
module directly first, per the task) — `create_api_auth`/`AuthContext` are exported at the UTL top-level facade, no
deep import needed. TRADE instructions convert to the internal `StrategyInstruction` shape via the existing
`ManualOperationHandler.build_instruction()` and route through `ManualOperationHandler.execute()` ->
`LiveOrchestrator.execute_instruction()` — literally the same call the internal manual-trade API makes; zero new
execution logic. Verified with a real (non-mock) `PaperLiveOrchestrator` test double implementing the actual
`LiveOrchestrator` protocol — full details + evidence in the W1 checkbox above. Two QG fixes needed after first full
gate run: (1) `# CORRECT-LOCAL` marker required on the local `ExternalInstructionResponse(BaseModel)` response DTO
(STEP 5.9 schema-provenance — matches the existing convention already used by `manual_schemas.py`/
`preview_schemas.py` in this same directory); (2) ruff B008 on `auth: AuthContext = Depends(_api_auth)` — fixed by
switching to `Annotated[AuthContext, Depends(_api_auth)]` (modern FastAPI style; oddly `api/app.py`'s pre-existing
`Depends(verify_admin_auth)` default-value calls don't trigger B008 the same way — not chased further, non-blocking
once switched). Full `quality-gates.sh --no-fix` green (156s) with a sentinel matching HEAD before shipping via
quickmerge. **Scope discipline held**: did not touch sports adapters, Polymarket, or the matching engine per the
dispatch prompt's explicit carve-out; the one matching-engine-adjacent finding (a real
`ExecutionOrchestrator`/`LiveOrchestrator`-protocol type mismatch in the lazy-orchestrator path, pre-existing and
untested end-to-end) is logged in the checkbox evidence above, not fixed.

**2026-08-16 — W1 instruments-service done, `instruments-service@2fcf7a19`.** Read `api_auth.py` directly (not just
cited) before writing anything, confirming the JWT/`X-Service-Token`/`X-API-Key` shape and finding
`client-reporting-api/client_reporting_api/api/routes/exports.py` as a live precedent already using
`create_api_auth`+`AuthDep` exactly this way. Found no existing generic "query the catalogue" reader inside
instruments-service itself (only write-path helpers + one UTL lifecycle-bounds loader scoped to a different purpose)
— built `engine/orchestrator/catalogue_query.py` reusing the SAME bucket-resolution primitives
(`resolve_instruments_store_kind`/`resolve_bucket_name`) and the SAME `download_bytes`+`pd.read_parquet` idiom already
used throughout the orchestrator package, rather than reinventing bucket/path logic. Verified the real shard path shape
directly against prod GCS (`instrument_availability/by_date/day=.../pipeline_mode=batch_instruments_service/
asset_group=cefi/venue=BINANCE-SPOT/instruments.parquet`) before writing the reader, confirming the R2 full-hive
canonicalisation is what's actually live. First cut of the bulk-parquet writer (naive "cast every shard to the first
shard's schema") crashed for real against live multi-venue data — `ArrowNotImplementedError: Unsupported cast from
string to null` — caught by testing against real prod data (23 cefi venues, day=2026-08-16) BEFORE shipping, not by a
unit test; root cause: per-venue schema drift is real (all-null columns infer as pyarrow `null` in one venue's shard
vs a concrete type in another; `tick_size` decimal128 precision differs per venue). Fixed with a two-pass
schema-unify (`pa.unify_schemas(..., promote_options="permissive")`) — re-verified value-preserving (0.01 stays 0.01,
just wider precision) and correct (13,141 rows / 23 venues round-tripped) before shipping. `quality-gates.sh --no-fix`
green. Shipped via quickmerge, landed LDR `instruments-service@2fcf7a19`. No blockers hit — the UTL auth module
imported cleanly and the internal bucket/storage primitives were reachable exactly as described.

**2026-08-16 — W4 Prediction Polymarket matching-engine wiring done, `execution-service@0e1b7b98dd`.** Investigated
first per the todo's own instruction: found a real, working, venue-agnostic depth-walked matching-engine path already
existed for CeFi (`MatchingEngineExecutionProvider` + `L2DepthProvider` + `walk_book_for_fill`), and its JSON
bid/ask-array row parser already handled Polymarket's real `book_snapshot_5` wire format unchanged — so this was
purely a wiring task, confirmed rather than assumed. Closed the one real gap (`L2DepthProvider`'s GCS-prefix
resolution was hardcoded CeFi-only, no `asset_group` param existed) and wired the actual production consumer
(`PredictionBetHandler`, which previously used a flat-markup heuristic for every backtest fill — the exact
"from-scratch simulator" pattern the operator's ruling said to avoid) to prefer a real depth-walked fill for
POLYMARKET. Fidelity tier `L2_MBP` cited from two independent real UAC/matching-engine registries, not assumed. Cross-
checked the `execution_service_live_orchestrator_protocol_mismatch_untested_2026_08_16.md` landmine directly —
confirmed by reading the code that `PredictionBetHandler` is a fully separate dispatch path from
`ManualOperationHandler`/`LiveOrchestrator`, so that issue was not encountered. Hit one dirty-deps quickmerge block
mid-session (a concurrent peer session's live WIP in `unified-api-contracts`, mtime <30s — correctly left untouched
per the liveness-gated protocol, waited via a background poll for it to clear rather than forcing a direct push) —
retried quickmerge once the dep went clean and it landed normally. Full evidence + the precisely-scoped SELL/LAY gap
(no `side` field on `ExecutionInstruction` yet) are in the W4 checkbox above.
- **na-eligibility-audit 2026-08-17** [body-hash:4df90236bc3a353d]: KEEP-NA, valid -- 1 open item (grep-verified, matches inventory_open_todos=1): the 20 undeclared archetype-feature-group scaffold rows (8 ambiguous 'Medium' + 12 'Low' genuine registry gaps needing new feature_group definitions). The whole plan's frontmatter/source carries an explicit dated operator ruling on DISPATCH MECHANISM — 'Same interactive-session dispatch mechanism as the pre-audit itself, per the operator's own instruction' — governing how this plan's work is executed regardless of any individual item's content-boundedness. The doc's own W2 section additionally establishes that mechanically declaring ambiguous archetype mappings would 'fabricate strategy-domain judgment... a CLAIM≤MEASUREMENT violation, not a gap to close' — real judgment content, consistent with staying NA.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries) -- re-verified all 6 still resolve; unchanged.
- **na-eligibility-audit 2026-08-17** [body-hash:b292dcdbdfeef601]: KEEP-NA, valid -- re-verified, no content change since the 2026-08-17 marker. Sole remaining open item (W2's 20 undeclared archetype-feature-group rows, 8 Medium + 12 Low) stays explicitly operator-paced pending review of the published Archetype Feature Scaffold artifact; the doc's own W2 section states mechanically declaring ambiguous mappings would fabricate strategy-domain judgment. Cross-cutting tranche audit.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — 0/0 checkboxes open (all 11 W1-W5 todos checked off; W6 codex-refresh properly redirected via depends_on+gate_on_depends to the named finalize companion plan, not orphaned). But real remaining work sits only in prose.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
