---
doc_type: plan
title: Venue readiness & registry hardening — the umbrella
summary: >-
  Umbrella for getting the system to full capability in a shape that makes the Elysium carve-out doable and cheap to
  keep in sync. Five workstreams: lazy/scoped loading (strategy-service factory, UAC __init__, execution-service
  algorithms), registry SSOT hardening, service-config abstraction (config.py + schemas + hot-reload + GCS, no
  in-service hardcoding), venue e2e wiring across instruments-service → execution-service for batch/live/paper
  including transfers and feature-group availability, and a per-venue smoke-test bar. Holds the VENUE READINESS
  CONTRACT — the repeatable multi-step path a new venue follows to reach a known readiness state — plus the
  definition-of-done every child plan measures against. Design rulings stay LOCAL here; mechanical per-venue sweeps
  fork to AO-dispatched children.
status: active
nature: process
asset_group: [cross-cutting]
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
scope: [engineer, admin]
assigned_vm: NA
execution_scope: local-only
tags: [venue-readiness, registry-ssot, lazy-loading, config-abstraction, carve-out-prerequisite, smoke-test]
priority: P0
source: operator-request-2026-08-16
parent_epic: security_and_cross_cutting_master
related:
  [
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
    /plans/active/venue_capability_route_axis_and_cross_ag_declarations_2026_08_14.md,
  ]
created: 2026-08-16
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
estimate_class: infra
estimate_baseline_ai_days: 12.0
estimate_calibrated_ai_days: 9.6
last_updated: "2026-08-16"
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
    /codex/06-coding-standards/config-reloader-pattern.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /plans/archive/issues/uac_kamino_venue_reachability_cascade_regression_2026_08_15.md,
  ]
---

# Venue readiness & registry hardening — the umbrella

> **Operator framing 2026-08-16**: two tracks, not one. **(a)** get the system to full capability _and_ into a shape
> that makes the carve-out doable; **(b)** get the carve-out to the contracted scope. This plan owns (a). The carve-out
> plan owns (b) and states the same split in its own §A5: _"these gate readiness to carve, not the carve-out's own
> content."_

## Why this is not just "lazy loading"

The lazy-load refactor was the entry point, but the operator's ruling widened it: the goal is that **adding a venue has
a clear, repeatable, multi-step path across the codebase to a known readiness state** — and that the information
needed to walk that path lives in ONE place per concern, not scattered through services.

Three failure modes this exists to end:

1. **Partial wiring.** A venue exists in one service's registry and not another's, so it reads as supported while some
   leg of the chain cannot serve it. The venue-coverage cascade already catches one direction of this; the fix is to
   make full wiring the default, not the exception.
2. **Hardcoded, unfindable config.** Behaviour buried in service code rather than declared in a config module with a
   schema, so the answer to "what is this venue configured to do" requires reading implementation.
3. **Unknown error semantics.** We do not systematically record how each venue's API response codes and error codes are
   handled. Without that, a new venue's failure behaviour is discovered in production.

## THE VENUE READINESS CONTRACT

The durable output of this plan. A venue is at a named readiness state when every row for that state is true. This is
what a child plan measures against, and what a new-venue rollout follows step by step.

| #   | Step                            | What "done" means                                                                                                            |
| --- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 1   | **Declared**                    | Present in the UAC venue registry with its capability record — route/mode axis, data types, instrument types. One declaration, no per-service copies. |
| 2   | **Reference data**              | instruments-service resolves its instruments; coverage windows and archive templates present.                                 |
| 3   | **Market data — batch**         | MTDS captures every declared data type; availability manifest reconciles; **a batch smoke test passes per data type**.        |
| 4   | **Market data — live**          | A live adapter exists for every batch adapter (never the reverse). Cascade invariant 1.                                       |
| 5   | **Features**                    | The venue's data reaches the feature groups that consume it; no feature group silently lacks it.                              |
| 6   | **Strategy — position read**    | A position adapter resolves for the venue in **batch, live and paper** (per-mode capability axis, not one boolean).           |
| 7   | **Strategy — slot eligibility** | Declared in the archetype/slot catalogues that can legitimately trade it.                                                     |
| 8   | **Execution — instruction**     | An adaptor handles every `InstructionActionV2` the eligible archetypes emit for it. Compared by ACTION, not venue name.        |
| 9   | **Execution — transfers**       | Every applicable `BusTransferType` has a working rail for the venue.                                                          |
| 10  | **Error semantics**             | Every API response code and error code from the venue's own docs is mapped to a classified outcome. SSOT, not per-call-site.  |
| 11  | **Config**                      | All venue config declared in a `config.py`-style module with a schema — hot-reloadable, GCS-backed. No in-service hardcoding. |
| 12  | **Reachability**                | Every component above is CALLED from a production path, not merely present. |

**Readiness states** (a venue is at the highest state whose rows all pass):

- **`BACKTESTABLE`** — steps 1-3, 5, 11, 13-15. We can research and backtest it honestly. **The floor for every venue
  in the universe.** Needs no venue credentials.
- **`PAPER-READY`** — + steps 4, 6-10, 16. **Requires REAL live connectors for reading market data**, plus real
  paper/testnet execution accounts. Also requires a settled, RECORDED answer to: does this venue have a testnet, how
  does it behave, or must we simulate it through our own matching engine in a way that stays as close as possible to
  both backtest and live? Per venue, written down, not assumed.
- **`LIVE-READY`** — + live execution credentials and live mode proven.

> **Credentials gate RUNNING, never BUILDING.** Exhausting the free path is a credential ask, not a descope. Build the
> full path; mark `BLOCKED-CREDENTIALS` if it cannot be RUN. What separates the states is which ACCOUNTS exist, not
> which code exists.

### Shipped evidence — Nick AI readiness remediation cross-references (2026-08-17)

Reconciled from `/plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md`'s W3-W5 (its own W2 finalize
todo asked for step-row citations, not a duplicate log — full narrative stays in that plan's Progress Log). Mapped
by the table's real step NAMES, not by number, after finding that plan's own "steps 9/10 for CeFi, 11/8 for Sports,
4 for Prediction" shorthand didn't fully match this table when checked directly (step 4 "Market data — live" does
not fit the Polymarket item — see below).

- **Step 9 (Execution — transfers)**: CeFi `VENUE_WALLET_CAPABILITIES` now covers 25/25 canonical cefi venues (was
  partial) — `unified-api-contracts@a0e6f3b9e7`.
- **Step 10 (Error semantics)**: CeFi error-classification extended to 6 new venue families
  (bitfinex/bitget/coinbase_cde/pacifica/extended/lighter) — same commit, `unified-api-contracts@a0e6f3b9e7`.
- **Step 8 (Execution — instruction)**: Sports `is_venue_executable()` was a bare passthrough of the
  reference-data axis (`VENUE_TO_ADAPTER_KEY`) despite a 2026-08-08 ruling to make it a separate executable
  predicate — fixed via new `SPORTS_EXECUTION_ADAPTER_VENUES` frozenset —
  `unified-api-contracts@96ef3e173f`. Back/lay action-mapping confirmed (not a schema gap, already correct via
  `BET_BACK`/`BET_LAY` `CompatibilityEntry` rows) — `unified-api-contracts@4753c4bbcd`.
- **Step 11 (Config)**: Sports `GET /sports/venues` wired off its hardcoded `live_not_configured` stub onto real
  Secret Manager probes for the 4 adapter-backed venues — `deployment-api@8239f10a77`.
- **PAPER-READY clause** ("must we simulate through our own matching engine... written down, not assumed"): answered
  for POLYMARKET — wired into the existing `MatchingEngineExecutionProvider`/`L2DepthProvider` depth-walk path for
  real VWAP fills in `PredictionBetHandler`, replacing a flat-markup heuristic — `execution-service@0e1b7b98dd`. Not
  a step-4 item; step 4 is live *market data*, not execution simulation — cited here instead of forcing a wrong
  mapping.
- **Step 13 (Granularity)**: see the GRANULARITY section immediately below — `unified-api-contracts@693e823adb`.
  **Not yet sufficient for the artifact's coverage denominator** — that additive registry expresses fidelity tier
  per (venue, data_type) with per-instrument_type *exceptions*, which is a different fact from an *enumeration* of
  which instrument_types exist per (venue, data_type). The latter is what the coverage denominator needs (a venue
  carrying `trades` on both spot and perp is 2 real cells, not 1) and is tracked separately as
  `system_readiness_master.md` W3's "Land the instrument_type axis on `VenueCapabilityRecord`" P0 item — confirmed
  by direct read of `unified-api-contracts/scripts/generate_venue_universe_denominator.py`, which still computes
  the 2-tuple denominator from `VENUE_DATA_TYPE_CAPABILITIES` alone as of this citation.

## GRANULARITY — what the data supports, declared per venue (operator ruling 2026-08-16)

Readiness is not binary per venue; it is bounded by **what granularity the data actually has**. This is the section
that makes the registry worth presenting: it answers _"this is what's available, this is the granularity, this is what
you can do with it."_

### The normalisation rule

> **HARD RULE: strategy-service NEVER reads market-tick-data-service directly.** It reads through features-service or
> market-data-processing-service, so it always receives a normalised shape. Everything a strategy consumes arrives as a
> candle-like structure — which is why strategy-side granularity reduces to _which candle series exist, at what
> interval_.

Verified 2026-08-16: the rule HOLDS today — strategy-service's only mention of MTDS is a docstring cross-reference, not
an import. But it is **convention, not enforcement**; nothing fails if someone adds the import.

### Execution matching is bounded by the same data, and must FAIL CLOSED

The fidelity vocabulary already exists — `L2_MBP` > `CANDLE_BOOK_COLS` > `L1_MBP` > `L0_TOB`, plus `AMM` and
`ALPHA_ZERO`, with `execution_fidelity.py` mapping each tier to the data it needs. What is missing is a per-venue
declaration of **which tier is actually achievable**, and enforcement that nothing asks for a richer one.

- A venue with only bars cannot support queue-aware matching. Attempting it produces a **fabricated** fill quality —
  the same failure class as a simulated connector reporting a live fill.
- The correct behaviour is to **refuse at the execution-service layer**, not to match as though tick data existed.
- Deviations are **per instrument and per data type**, not per venue — one venue can carry full depth for its majors
  and bars only for the long tail. The registry must express that, never a venue-level average.
- Non-orderbook markets substitute their own shape — time-sliced odds snapshots stand in for ticks. That is a distinct
  matching class, not a degraded orderbook, and should be modelled as such.

### Contract steps added by this ruling

| #   | Step                     | What "done" means                                                                                                                            |
| --- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| 13  | **Granularity declared** | Per (venue x instrument-type x data-type): the interval/depth the data actually supports, exceptions expressed at the level they occur.         |
| 14  | **Derivation path**      | How candles are made and aggregated from it, and which candle series each consuming feature group reads.                                        |
| 15  | **Trigger frequency**    | Strategy-service tick cadence and MDPS derivation cadence are consistent with the declared granularity — nothing triggers faster than its data. |
| 16  | **Matching class**       | The achievable fidelity tier, declared. Execution REFUSES a richer tier rather than approximating one.                                          |

- [x] [AGENT] P0. ✅ Done 2026-08-16 — unified-trading-pm@0a1412cb6b. **Gate the normalisation rule.** Add a
      check that fails if strategy-service imports market-tick-data-service. It holds today by convention only; the
      gate makes it durable and costs almost nothing. Implementation: `scripts/validation/check-no-service-deps.py`
      already ran a fleet-wide raw-cross-service-import scan (WARN-only, ~39 pre-existing tracked violations across
      other pairs, per the utl_reuse_phase9 note in that file) — hard-failing it fleet-wide would have broken those
      repos' gates. Added a narrow `_HARD_FAILED_PAIRS` set containing exactly
      `("strategy-service", "market-tick-data-service")`; every other pair stays WARN-only, unaffected. Verified
      2026-08-16 the pair had zero pre-existing hits (confirmed above at line 133), so hard-failing carries no
      baseline-remediation cost. `base-service.sh` wires this script into every service's `quality-gates.sh`
      automatically (QG-INFRA carve-out path), so strategy-service picks it up with no per-repo change. Added 2 unit
      tests (`tests/unit/test_check_no_service_deps.py::TestMainHardFailedNormalisationRule`) confirming (a)
      strategy-service importing MTDS hard-fails with `[FAIL]` + "normalisation rule" in the message, and (b) an
      unrelated pair (features-service importing MTDS) stays `[WARN]`-only. Full suite 31/31 passed
      (`.venv/bin/python3 -m pytest tests/unit/test_check_no_service_deps.py -q`); full `quality-gates.sh --no-fix`
      exit 0.
- [x] ✅ [OPERATOR] P0. **Granularity declaration home — RULED 2026-08-16: a UAC registry**, consistent with venue lists
      and adapter keys already being UAC data, and readable by execution-service so it can fail closed rather than match
      as if it had tick data. Not instruments-service (that would make execution's fail-closed check depend on IS), and
      not manifest-derived-at-runtime.
      **Seeding, per the operator: do NOT hand-populate from scratch.** Most of it is derivable from the manifest as it
      stands, plus the plans still to complete, plus what the code already encodes — treat those three as the seed and
      reconcile, so population is a diff against existing knowledge rather than fresh data entry. Where the three
      disagree, the manifest is the measurement and wins; a disagreement is itself a finding, not a tie to break
      quietly. The instrument-type axis and the granularity/exceptions fields are the genuinely new part.
      **Concrete target, from the W2 evidence below**: extend `VenueCapabilityRecord` — it already carries the
      (venue × data-type) axis this needs. Keyed per (venue x instrument-type x data-type), expressing exceptions at
      that granularity, read by both MDPS and execution-service. **Cross-reference (2026-08-16, W2 resolved)**:
      `/plans/archive/2026_08/registry_ssot_hardening_2026_08_16.md` todo 1 resolved the three `VenueCapability*`-named UAC
      types as genuinely orthogonal — no merge, all three survive. Of the three, `VenueCapabilityRecord`
      (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:2508`) is the shape closest
      to this item's need — it is already keyed per-venue with a per-data_type `dict[str, DataTypeAvailability]`
      value, i.e. the same (venue × data-type) axis this item needs, just missing the instrument-type axis and the
      granularity/exceptions fields themselves. `VenueCapability` (StrEnum) is a flat operation-kind vocabulary, not
      a per-data-type record — wrong shape. `VenueCapabilityV2` (BaseModel) has zero live instances anywhere — not a
      populated target to extend. This is evidence for the operator's shape call, not a decision on it.
- [x] [AGENT] P0. **Make execution fail closed on fidelity.** Today the tier clamps DOWN silently, which is right for a
      backtest and wrong for a live/paper caller that assumed better. Decide per path — clamp-and-record versus refuse —
      and make refusal the default when a caller explicitly requests a tier the venue cannot serve. —
      `execution-service@88aa0f10fe`: `clamp_tier()`/`select_book_type()`/`resolve_matching_fidelity_rung()` gained a
      `refuse_unservable: bool = False` kwarg (never a `mode ==` comparison — STEP 5.77 forbids that outside the CLI
      seam); default preserves clamp-and-record, `refuse_unservable=True` raises `FidelityRefusedError`
      (`ErrorCategory.DATA_QUALITY`). Mode→boolean resolution deferred to whichever future CLI entry point starts
      passing `max_tier` (zero production callers do today). QG: `✅ ALL QUALITY GATES PASSED`.
- [x] ✅ [AGENT] P1. Extracted to `cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md` item 5 (na-eligibility-audit 2026-08-17). **Publish the granularity view.** Render it as a table a human can read: venue, instrument type, data
      type, granularity, achievable matching class. This is what makes "what can we actually do here" answerable without
      reading code — and it is the same table we can show a counterparty. **The registry to render from now exists**
      (2026-08-16, `unified-api-contracts@693e823adb`,
      `/plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md` W3):
      `unified_api_contracts.registry.venue_granularity.VENUE_GRANULARITY_CAPABILITIES` +
      `get_granularity(venue, instrument_type, data_type)`, 412 populated `(venue, data_type)` cells across all 5 asset
      groups (instrument_type expressed as a default + per-instrument exceptions, not a literal per-triple row) — this
      todo is now purely a rendering task, not a data-population one.
      Landed evidence reconciled: `unified-api-contracts@2f74bd8da2` shipped
      `scripts/generate_venue_granularity_report.py`; the batch16 plan flip is recorded in
      `unified-trading-pm@2bfe44b0e6`.

## STRATEGY CONSUMABILITY — a venue with no consumer is not ready (operator ruling 2026-08-16)

A venue is only ready if **at least one strategy archetype can actually use what it provides**. Data nobody consumes is
not capability; it is storage. This forces the readiness contract to close end-to-end rather than stopping at "we
capture it".

Two directions, and both must hold:

| Direction        | The test                                                                                    | Failure looks like                                                                       |
| ---------------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Venue to strategy | For every data type the venue provides, is there an archetype that consumes it?               | A venue supplies a data type nothing trades. Captured, stored, inert.                       |
| Strategy to venue | For every archetype tied to the venue, are ALL its required inputs available from that venue? | Lido is declared as a venue, but staking rates are missing — so no archetype can run on it. |

The second is sharper and more common: a venue can be 90% wired and still useless because the ONE input its only
candidate archetype needs is the one that is absent.

### The chain exists, except for one link — measured 2026-08-16

    venue          -> data types                        EXISTS   venue capability record
    feature_group  -> required (asset_group, data_type) EXISTS   FEATURE_REQUIRED_INPUTS, a real UAC SSOT
    archetype      -> feature_groups                    MISSING  the gap

`unified_api_contracts/canonical/domain/features/required_inputs.py` already declares, per feature group, the
`(asset_group, data_type)` inputs it needs, with `get_required_inputs` / `has_required_inputs` /
`validate_required_inputs` helpers. But **nothing maps an archetype to the feature groups it consumes** — zero hits
across `engine/strategies/v2/` — so the composition cannot be computed in either direction today.

Closing that one link makes both tests mechanical rather than manual, and it is the smaller half: the expensive half,
per-feature-group input requirements, already exists.

- [x] [AGENT] P0. ✅ Shipped — `unified-api-contracts@2fa22fee` ("feat: declare StrategyArchetype to feature_group
      mapping (UAC SSOT)"), on `origin/live-defi-rollout`, `ahead=0`. **Declare archetype to feature_groups.** The
      missing link. Composes with `FEATURE_REQUIRED_INPUTS` per the design recorded in the Progress Log below (5
      confirmed archetypes, 54 explicitly `UNDECLARED_ARCHETYPES`, never silently "consumes nothing"). The external
      blocker (karak/pendle/symbiotic DeFi-connector reachability) that held this for 16 confirmations across the
      session cleared — someone else's in-flight `DeFiAdapter` dispatch-wiring work landed; the invariant now passes
      standalone (`test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions PASSED`, re-verified
      2026-08-16).
- [x] [AGENT] P0. ✅ Shipped — `unified-api-contracts@5a74178360` ("feat: add contract step 17 real check, both
      directions"), on `origin/live-defi-rollout`. **Add contract step 17 as a real check, both directions.** New
      module `unified_api_contracts/internal/architecture_v2/venue_strategy_consumability.py` composes
      `FEATURE_REQUIRED_INPUTS` + `ARCHETYPE_FEATURE_GROUPS` (no restating either): `satisfying_archetypes()` /
      `archetype_fully_satisfiable()` implement direction (b) — at least one of the 5 confirmed archetypes' full
      data_type requirement set is a subset of the venue's; an `UNDECLARED_ARCHETYPES` member can never satisfy this
      (undeclared ≠ "needs nothing", so it must not silently count). `orphaned_data_types()` implements direction
      (a) — every venue data_type not in the union of what any feature_group consumes, and not in a caller-supplied
      `declared_unused` set, is orphaned. `contract_step_17_check()` combines both into a `Step17Result.passed` verdict.
      12 unit tests (`tests/unit/test_venue_strategy_consumability.py`) cover: the data_type-vs-feature_group-name
      distinction (`"lending_rates"` feature_group → `"lending_indices"` data_type, not the group's own name),
      undeclared-archetype exclusion, orphan detection, declared-unused suppression, and the combined verdict. Exported
      from the `architecture_v2` package `__init__.py`. Full `unified-api-contracts` `quality-gates.sh --no-fix`:
      `✅ ALL QUALITY GATES PASSED (253s)`. **Note**: this implements the step-17 spec as promoted to the contract
      table (row 17, above) — "at least one archetype" — not the stricter "every archetype tied to the venue" framing
      in the motivating § STRATEGY CONSUMABILITY prose above it; that stricter direction needs a venue↔archetype
      tie (`venue_universe`), which turned out to be per-slot comma-separated strings scattered across
      `strategy-service/strategy_service/engine/strategies/v2/archetype_slots_*.py` (confirmed via grep this session),
      not a clean UAC SSOT — consolidating that is separate scope, not blocking this check.
- [x] [AGENT] P1. ✅ Shipped — `unified-api-contracts@36a31a165f` ("fix: lst_yields feature_group required its own
      name as data_type instead of lst_rates"), on `origin/live-defi-rollout`, `ahead=0`. **Report the unconsumed
      set.** New `scripts/generate_venue_consumability_report.py` (permanent, re-runnable) runs
      `contract_step_17_check` across all 192 venues in `VENUE_DATA_TYPE_CAPABILITIES`. Measured 2026-08-16: only 9
      venues (all single-purpose `lending_indices` lenders — AAVE-PLASMA, BENQI-AVALANCHE, EULER_V2-*, FLUID-PLASMA,
      MARGINFI-SOLANA, SOLEND-SOLANA, VENUS-*) fully pass both directions; 172/192 have >=1 orphaned data_type; 21
      distinct data_types are orphaned fleet-wide (`dex_pool_state`/`dex_pool_swaps` 33/31 venues, `oracle_prices` 49,
      `odds` 31, `staking_yields` 26, `lst_rates` 19, etc.) — expected given only 5 of 59 `StrategyArchetype` members
      are declared in `ARCHETYPE_FEATURE_GROUPS` today (54 `UNDECLARED_ARCHETYPES`), so most captured data has no
      archetype to consume it yet — a scope gap, not a bug, tracked separately by the archetype-declaration backlog.
      **Correction, 2026-08-16 (later, interactive session)**: `ARCHETYPE_FEATURE_GROUPS` moves fast — a same-day
      re-measurement found 40/60 declared (not 5/59), spanning every asset_group (not DeFi-only), and a fresh
      `generate_venue_consumability_report.py` run showed 30/192 fully pass + 161/192 have orphans (not 9/172). Do
      not cite either historical figure above as current — re-run the script; this whole section moves as fast as
      the registry does. See `venue_e2e_wiring_2026_08_16.md`'s "Derive the work list" todo for the discovery.
      **But one real bug surfaced by the report, fixed in the same change**: `required_inputs.py`'s `"lst_yields"`
      feature_group declared its required input as `data_type="lst_yields"` (self-referential) instead of
      `data_type="lst_rates"` (the raw exchange-rate ticks it's actually computed from — confirmed via
      `features-service/features_service/onchain/engine/lst_features.py` and
      `strategy-service/.../canonical_lst_yields_index_provider.py`), unlike the sibling `"lending_rates"` entry which
      correctly points at `data_type="lending_indices"`. This meant **no real LST venue could ever satisfy
      YIELD_STAKING_SIMPLE / CARRY_STAKED_BASIS / CARRY_STAKED_BASIS_DATED / CARRY_RECURSIVE_STAKED**, even though 19
      real LST venues (LIDO-ETHEREUM, ETHERFI-ETHEREUM, JITO-SOLANA, etc.) genuinely provide the data under the
      `lst_rates` name. Same root-cause drift also left a duplicate/erroneous `("defi", "lst_yields")` raw-data_type
      entry in both `availability_semantics.py` and `_source_priority_table.py` alongside the correct
      `("defi", "lst_rates")` entry — removed both — plus a stale `test_validity_matrix_completeness.py` exclusion-list
      entry that already carried a `# canonical name is lst_rates` comment flagging this exact bug but never acted on
      it — removed. Full `unified-api-contracts` `quality-gates.sh --no-fix`: `✅ ALL QUALITY GATES PASSED (253s)`.
- [ ] [AGENT] P2. **Consolidate `venue_universe` into a clean UAC SSOT.** Currently per-slot comma-separated strings
      scattered across `strategy-service/strategy_service/engine/strategies/v2/archetype_slots_*.py` (confirmed via
      grep 2026-08-16) — not derivable as a clean `archetype -> venues` map today. Needed only to implement the
      *stricter* "every archetype tied to the venue" direction described in the motivating § STRATEGY CONSUMABILITY
      prose above; the shipped contract-step-17 check (`unified-api-contracts@5a74178360`) implements the weaker
      "at least one archetype" version, which is the one actually promoted to the contract table (row 17) and does
      not need this. Natural fit for W4 ("venue e2e wiring") once that workstream forks.

| #   | Step                       | What "done" means                                                                                                       |
| --- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 17  | **Strategy consumability** | At least one archetype's inputs are fully satisfiable from this venue, AND every data type it provides is consumed or declared unused. |

## CANONICAL ORTHOGONALITY — no orphaned data types, no near-duplicates (operator ruling 2026-08-16)

Step 17 stops a VENUE being orphaned. This extends the same test one level down: **a DATA TYPE must not be orphaned
either.** If a venue produces liquidations, something in the code must consume liquidations — otherwise we pay to
capture, store and reconcile a stream nobody reads.

### The vocabulary must be minimal and truly orthogonal

A strategy that reads LST rates should read **`lst_rates`** — not `lst_sol_rates`, not a DeFi-flavoured variant of the
same idea. Where two data types are *in principle the same thing* and differ only by a column or five, they are not two
data types; they are one, recorded twice.

The requirement is an audit toward the **minimum set of data types that are genuinely orthogonal to each other**:

- Two types describing the same measurement with different column sets: **normalise into one**, then **migrate and
  purge** — GCS objects AND the manifest, so no second shape survives to be read by accident.
- Extra columns do not justify a separate type. The superset absorbs the subset.
- The same logic applies to VENUES: two venue identities with the same name and the same data types are one venue.
  Worked example: a `COINBASE` and a `COINBASE-2` that both supply only perpetuals should be one entry, not two.

### This composes with three existing SSOTs — it is not new machinery

That matters for cost: the hard parts are already built, and already safety-gated.

| Concern                        | Existing SSOT                                                                                |
| ------------------------------ | ----------------------------------------------------------------------------------------------- |
| Merging/renaming an entity     | [entity-rename-and-split-consumer-migration-rule](/codex/02-data/entity-rename-and-split-consumer-migration-rule.md) — every consumer migrates in the SAME change; a token grep misses path-prefix, filename and registry-membership binders |
| Purging GCS objects + manifest | [gcs-and-manifest-delete-safety-protocol](/codex/02-data/gcs-and-manifest-delete-safety-protocol.md) — deletes need the 5-part proof, and prod-bucket deletes are HUMAN-ONLY unless reversibility-qualified |
| Recording the cutover          | [canonical-cutover-register](/codex/02-data/canonical-cutover-register.md)                        |

**The purge half is therefore operator-gated by construction.** An agent may propose and prove a merge; it may not
delete prod data on its own authority.

### Contract steps added by this ruling

| #   | Step                        | What "done" means                                                                                                             |
| --- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 18  | **Data-type consumability** | Every data type this venue emits is consumed by at least one feature group or archetype, or is explicitly declared unused.        |
| 19  | **Canonical orthogonality** | The data type belongs to the minimal orthogonal set — no near-duplicate exists, or the merge is recorded in the cutover register. |

- [x] [AGENT] P0. ✅ **Audit the data-type vocabulary for near-duplicates.** Findings below. Proposal only — the merge
      follows the rename rule and the purge follows delete-safety.
- [x] [AGENT] P0. ✅ **Audit for orphaned data types** — captured but consumed by nothing. Findings below.
- [x] [AGENT] P1. ✅ **Audit venue identities for duplicates** — the same effective venue represented twice. Same
      treatment: propose, migrate consumers in one change, register the cutover, route the purge through delete-safety.
      Findings below: zero duplicates found, no merge to sign off.
- [ ] [OPERATOR] P0. **Sign off each proposed merge before migration** (the two near-duplicate/orphan candidates below
      that need a decision, not the ones already ruled). Merging two data types rewrites paths, manifest rows and
      consumer bindings at once, and the purge is a prod delete. Both sides are operator-gated.

### Audit findings (2026-08-16) — data-type vocabulary, 31 venue-emitted types

Method: enumerated `VENUE_DATA_TYPE_CAPABILITIES` (`unified_api_contracts/registry/market_data_categories.py` +
`defi_venue_capabilities.py`) as the target vocabulary (31 distinct `data_type` strings — narrower than the 60-item
`ALL_DATA_TYPES`/`DATA_TYPES_BY_ASSET_GROUP` union; the 29-item delta is a separate, not-yet-audited observation, noted
at the end, not folded into these results). Cross-checked consumption against `required_inputs.py`'s
`FEATURE_REQUIRED_INPUTS`, `archetype_feature_groups.py`'s `ARCHETYPE_FEATURE_GROUPS`, and repo-wide literal-string
greps across `features-service`/`strategy-service`/`ml-service` — a 0-grep-hit result was cross-checked against the
actual writer existing before being called orphaned, per this workspace's claim-vs-measurement rule.

**Near-duplicates:**

- **`book_snapshot` vs `book_snapshot_5` (cefi) — real duplicate, already a documented legacy alias, not a new bug.**
  `book_snapshot_5` is the canonical venue-emitted name; `book_snapshot` (bare) is called out verbatim as a "legacy
  alias" in `availability_semantics.py:133` and `_source_priority_table.py:171-177`. **The gap this audit surfaces**:
  every CeFi feature_group in `required_inputs.py` (`microstructure`, `book_depth_bands`, `liquidity_walls`,
  `liquidation_clusters`, `flow_interaction`, `order_flow_inference`, `composite_sr`) is keyed on the legacy bare name,
  not the canonical one — `book_snapshot_5` has zero cefi `required_inputs.py` entries (only `prediction` uses the
  canonical name literally). Needs an operator call: rename the `required_inputs.py` keys to the canonical name, or
  declare the bare alias itself canonical for cefi and fix the doc comments instead.
- **`funding_rate` vs `perp_funding` (cefi) — investigated, RULED NOT a duplicate, no action.** Different endpoints,
  different semantics (continuous Tardis-fed field vs. realized periodic settlement), and this codebase already has a
  169-day cross-source parity measurement on record (`market_data_categories.py` HYPERLIQUID comment, ~L101-111: only
  60.7% of 2,640 overlapping rows matched within 2e-5, worst divergence 1.2e-3) that disproved an earlier
  "byte-identical" assumption. Keep both.
- **`vault_share_price` vs `lst_rates` (defi, MAKER-ETHEREUM cell only) — not a vocabulary-level duplicate, one
  already-tracked cell-level instance.** Both names are correct for other venues. `defi_venue_capabilities.py`
  (L284-295) already documents MAKER-ETHEREUM's capture moved to `lst_rates_handler.py` (same `convertToAssets()` call)
  and calls `vault_share_price` there "an orphaned, non-producing duplicate" — pre-existing finding, already tracked in
  `vault_share_price_handler_capture_gap_since_2026_06_22.md`. No new action.
- **AMBIGUOUS — flag for operator judgment**: `("defi","swap")`, `("defi","fx_rate")`, `("defi","liquidity")`,
  `("defi","market_state")`, `("defi","vault_state")`, `("defi","solana_defi")` are registered in
  `AVAILABILITY_AT_SEMANTICS` with zero matching `VENUE_DATA_TYPE_CAPABILITIES` entry and zero writer/feature-group
  reference found — they read like a superseded early generic-defi naming scheme (`swap`→`dex_pool_swaps`,
  `market_state`→`dex_pool_state`, `vault_state`→`vault_share_price`/`vault_apy`/`vault_tvl`). Not exhaustively ruled
  out as scaffolding for a not-yet-migrated path. Needs an operator call: dead-code delete or keep as reserved.

**Orphaned data types (captured + tracked, zero feature_group/archetype consumer found anywhere in the workspace):**

`governance_events`, `mev_events`, `position_data`, `token_transfers`, `bridge_events` (all defi, real MTDS writers,
tracked by manifest/data-status/deployment-api, zero reads in `features-service`/`strategy-service`/
`required_inputs.py`), and `rewards` (raw AAVE_V3 `RewardsController` emissions, distinct from `eigenlayer_rewards` —
`required_inputs.py`'s `"rewards"` feature_group actually consumes `eigenlayer_rewards`, not `rewards`; the
`features-service` `eigen_rewards_calculator.py:53` comment confirms this directly: *"replaces a stale ... 'rewards'
guess that never matched anything on disk"*). Six confirmed orphans, each resolves to: declare explicitly unused, wire
a real consumer, or merge/purge — operator sign-off required per the todo above before any action.

**Ambiguous, needs a closer look (not yet ruled either way):**

- `flash_loan_events` — declared consumed via `required_inputs.py`'s `flash_loan_availability` feature_group (real UAC
  registration) and has a real writer, but zero `features-service` calculator literally reads it. Looks aspirational/
  not-yet-implemented rather than genuinely orphaned — verify whether `flash_loan_availability` computes anything today
  before classifying.
- `staking_yields` — not in `required_inputs.py`, zero `features-service` hits, but IS read by
  `ml-service/ml_service/training/app/core/feature_query_support.py`. Real ML-training consumer; whether that satisfies
  "consumed by a feature group" per step 18's wording is a scope question, not a fact question.

**Secondary observation, not folded into the above**: 29 of the 60 `ALL_DATA_TYPES` union have no
`VENUE_DATA_TYPE_CAPABILITIES` entry at all (`gas_fees`, `tbbo`, `mbp_10`, `perp_trades`, `perp_daily_ctx`,
`perp_mark_price`, `native_staking_rates`, `utilization`, `flash_loan_availability`, `vault_apy`, `vault_tvl`, 7
`swaps_ohlcv_*` MDPS-processed types, `corporate_action_confirmed`, `earnings_result`, `macro_result`,
`volatility_index`, `ohlcv_15m`, `arbitrage_opportunity`, `odds_horizon_bucket`, `trades_inplay`,
`prediction_canonical_question_group`, `market_lifecycle`). Some are confirmed real via in-code comments explaining an
alternate capture mechanism (e.g. `gas_fees` via bare `ALCHEMY`); others (`tbbo`/`mbp_10`/`ohlcv_15m`) are explicitly
commented as currently-unreachable/deferred. Out of scope for this pass (target vocabulary was the venue-emitted 31,
per the ruling's own "a venue produces X" framing) — a follow-up audit item, not added as a new todo here since it
needs its own P-tag and scoping decision first.

### Audit findings (2026-08-16) — venue identities, 169 canonical venues

Method: mirrors the data-type audit's method above. Enumerated the full canonical venue universe (`ALL_VENUES`, 169
entries = `sorted(union of VENUES_BY_ASSET_GROUP.values())`, which already folds in DeFi's phase="live" filter) via a
one-off scan script, and checked for (a) exact normalized-form collisions (strip `-`/`_`, uppercase — catches
SPELLING duplicates like the already-resolved VELODROME_V2/VELODROMEV2 case), (b) bare venue names co-existing with a
product-suffixed sibling (catches the OKX-bare-removal class of issue), and (c) overlap between the two
deprecated/ghost-venue registries (`DEPRECATED_DEFI_GHOST_VENUE_NAMES`, `EMPTY_OR_DEPRECATED_DEFI_VENUES` in
`unified_api_contracts/registry/capability_declarations/_defi_coverage.py`) and the live canonical set (catches a
name flagged dead that's still counted).

**Result: zero venue-identity duplicates found.** The registry has already had ~15 prior operator rulings
systematically eliminate every duplicate-spelling pattern this scan can detect (OKX bare removed 2026-08-04,
COINBASE bare→COINBASE-SPOT 2026-07-10, BINANCE-DELIVERY deregistered 2026-08-10, bare BETFAIR removed 2026-08-08,
YEARN→YEARN_V3 2026-07-08, VELODROME_V2/VELODROMEV2 + TRADER_JOE_V2/TRADER_JOEV2 resolved via
`LEGACY_DEFI_VENUE_ALIASES` — legacy glued forms are non-canonical ALIASES, not a second canonical entry — LADBROKES/
BET888SPORT sports folds, legacy Tardis ids OKEX/CRYPTOFACILITIES folded via `CEFI_VENUE_FOLD`). This audit confirms
none of that work has regressed and finds no NEW instance of the pattern.

- **Exact normalized-form collisions**: none across all 169 venues.
- **Bare + suffixed co-existing**: `BYBIT`/`BYBIT-SPOT`, `KALSHI`/`KALSHI-PERP`, `POLYMARKET`/`POLYMARKET-PERP` — each
  pair investigated and ruled NOT a duplicate. The bare form and the suffixed form are two different real products
  (bare = perpetual-futures / prediction YES-NO market, suffixed = spot / crypto-perp-CLOB respectively) — same shape
  as the already-canonical OKX-SPOT/OKX-SWAP/OKX-FUTURES split, just using the bare string for one product instead of
  suffixing every product. A naming-CONVENTION inconsistency (worth a style-only cleanup someday), not an identity
  duplicate — no merge candidate, no action.
- **Deprecated/ghost-name overlap with the live set**: `DEPRECATED_DEFI_GHOST_VENUE_NAMES` has zero overlap.
  `EMPTY_OR_DEPRECATED_DEFI_VENUES` overlaps on `TRADER_JOE_V2-AVALANCHE` + `UNISWAP_V3-POLYGON` — investigated and
  ruled NOT a bug: that registry is a coverage-EXPECTATION dampener (`venue_has_no_expected_defi_coverage()`,
  docstring: "subgraph returns 0 instruments"), a different axis from canonical membership — a venue can correctly be
  both real/canonical AND expected to have zero rows. No contradiction, no action.

No merge/purge proposal follows from this audit — there is nothing for the operator to sign off here. Scan script
destroyed after use (regenerable in minutes from `ALL_VENUES`/`VENUES_BY_ASSET_GROUP`; no open todo depends on it).

## Workstreams — each forks to its own child plan

Children are authored separately so each stays under the line cap and workstreams can run concurrently. **Design
rulings stay in this LOCAL plan; mechanical per-venue sweeps fork to AO-dispatched children** (operator ruling
2026-08-16).

- [x] [AGENT] P0. ✅ **W1 — lazy/scoped loading.** Forked to
      [`/plans/active/lazy_scoped_loading_refactor_2026_08_16.md`](/plans/active/lazy_scoped_loading_refactor_2026_08_16.md).
      Three layers; UAC is the dominant one with fleet-wide blast radius. Referenced by carve-out §A5 P0 #2.
- [x] [AGENT] P0. ✅ **W2 — registry SSOT hardening.** Forked to
      [`/plans/archive/2026_08/registry_ssot_hardening_2026_08_16.md`](/plans/archive/2026_08/registry_ssot_hardening_2026_08_16.md) —
      unified-trading-pm@a8465760e5. A same-pattern grep sweep across all 7 umbrella repos, done at authoring
      time, found 4 of 5 concerns (adapter keys, instrument types, data types, error-code classification) already
      single-SSOT with zero per-service redefinitions; the child plan's real open scope is a same-repo
      `VenueCapability*` naming-overlap resolution plus an error-code coverage audit.
- [x] [AGENT] P0. ✅ **W3 — service-config abstraction. NO new plan — this ground was already owned.** A W3 child was
      drafted 2026-08-16 and **deleted before shipping** once the overlap was measured: §&nbsp;D of
      [`/plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`](/plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md)
      ("Per-service config centralisation + hot reload") already tracks the typed `client_configs` schema, the
      per-service knob inventory, the execution-service `config.py` resolution and the API-key reloader asymmetry.
      The operator's 2026-08-16 shape ruling plus its two open sub-questions (schema mechanism; what the gate
      asserts) were folded into that section as a `§ D delta` rather than duplicated here. **Lesson**: the pre-task
      plan-conflict check must grep the corpus by CONCERN, not by filename — a filename grep for "config_abstraction"
      could never have found a plan named "service_config_ownership_and_instruction_contract".
- [x] [AGENT] P0. ✅ **W4 — venue e2e wiring.** Forked to
      [`/plans/active/venue_e2e_wiring_2026_08_16.md`](/plans/active/venue_e2e_wiring_2026_08_16.md) (real, 163
      lines, `status: draft`). **Correction 2026-08-16: the file DOES exist** — a prior entry here claimed it "was
      never actually created" and delinked it; that claim was itself wrong (a misread during an unrelated dispatch's
      broken-link check) and is fixed here per the HARD RULE that a misleading pointer is a finding fixed on
      contact. Its content already documents the method (per venue × data type, not per venue), the per-AG batch
      fork structure, and the hard rules the sweep must not violate — none of that is "undocumented until the fork
      happens," contrary to the prior claim. **Still blocked on the same one thing**: the universe denominator
      below (its own P0 "Define the universe precisely for W4/W5" remains open). Fresh per-AG venue counts measured
      2026-08-16 (cefi 25, defi 79 protocol identities/105 spellings, tradfi 8, sports 37 canonical/45 physical,
      prediction 2 — see
      [`/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md`](/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md)
      § PRE-AUDIT MEASUREMENTS §1) are useful input to that denominator work but do not by themselves satisfy it —
      that todo needs one machine-readable list, not five separately-measured counts.
- [x] [AGENT] P0. ✅ **W5 — smoke-test bar.** **Correction 2026-08-20 (/plan-reconcile F-G31-1)**: the file DOES
      exist — a prior entry here claimed it "was never actually created," mirroring the identical W4 claim above,
      which was itself corrected same-day for W4 but never corrected here. `/plans/active/venue_smoke_test_bar_2026_08_16.md`
      exists (190 lines, 9 open + 1 done todo), was created in the SAME commit as W4's child plan
      (`c6c5ca34984a3f23f03f11e1d01be9f336e627f5`), and has a companion
      `/plans/active/venue_smoke_test_bar_finalize_2026_08_16.md` (6 open todos) gated on it. That claim was itself
      wrong. Records that the Databento exemption is by **SOURCE, not asset
      group** (a TradFi venue sourced elsewhere is in scope), and specifies that a smoke test must provably FAIL on
      a venue with no data — the pass-on-zero-rows trap has already cost this corpus real time. That content lives
      only in this line until the fork actually happens.

## Design rulings needed before the mechanical children dispatch

These are the LOCAL half of the split — an AO worker cannot settle them alone, so they must be resolved here first.

- [x] ✅ [OPERATOR] P0. **Error-code SSOT shape — RULED 2026-08-16: extend `classify_venue_error()`.** Not a separate
      registry and not per-venue declaration files. The existing UAC classifier grows into a (venue, code) registry, so
      raw venue codes stay bound to the behaviour they already trigger — shard-level failure isolation and the
      `DependentAction` ladder — rather than being classified in one place and acted on in another. Requirements the
      shape must keep: greppable per venue, and diffable when a venue changes its API.
      **Consequence for W4/W5**: population is now unblocked and is the expensive half — it is per-venue mechanical
      work, so it belongs in the AO-dispatched children, not here.
- [x] ✅ [OPERATOR] P0. **Config-abstraction target shape — RULED 2026-08-16: one `config.py` per service, split by
      domain ONLY where the line cap forces it.** The default and the thing the gate asserts is a single per-service
      module; a domain split is a mechanical remedy for a file that breaches the cap, never a design choice made up
      front. So "where is this service's config" always has one answer, and a split is self-evidently cap-driven.
      **Open sub-questions this ruling does NOT settle** (fold into the W3 child, do not re-ask the operator): the
      schema mechanism, and what precisely the gate checks to prove no in-service hardcoding crept back. Existing
      pattern to extend: [config-reloader-pattern](/codex/06-coding-standards/config-reloader-pattern.md).
- [x] [AGENT] P0. ✅ **Define the universe precisely for W4/W5 — RESOLVED 2026-08-16: the real denominator is
      (venue, data_type) pairs, not venue count, and the "158 venues / 84 families" figure is a stale one-off manual
      tally (`venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md:62-65`, 2026-08-14) with no producing
      script — already independently found to not hold (a 151-183 range measured 2026-08-16 in
      `nick_ai_platform_disclosure_artifact_2026_08_16.md` § PRE-AUDIT MEASUREMENTS §1) — superseded, do not cite it
      again.** SSOT for the pair count is `VENUE_DATA_TYPE_CAPABILITIES` in
      `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:2564` — each venue's own
      `.data_types` field, flattened to pairs, IS the readiness-contract denominator per the design ruling above (P0
      2 lines up). Measured 2026-08-16 via the new script below:
      **192 declared venues, 353 (venue, data_type) pairs.** DeFi coverage: 127 of `ALL_DEFI_VENUES`'s 135 canonical
      venues already have a capability declaration (union with `VENUE_DATA_TYPE_CAPABILITIES` = 200 venues); the
      remaining 8 have none and are excluded from the denominator until declared (new todo below). Made reproducible,
      not a one-off number, via
      `unified-api-contracts/scripts/generate_venue_universe_denominator.py` — re-run it, the count moves every time
      either registry changes. **W4/W5 are now unblocked.** SHIPPED —
      `unified-api-contracts@e7ee398117`.
- [x] ✅ [AGENT] P1. **PARTIAL — the 3 conflict-free venues extracted to
      `cross_cutting_satellite_ao_dispatch_batch22_2026_08_21.md` item 3 (na-eligibility-audit 2026-08-21,
      cross-cutting tranche); the 5 Alchemy venues stay BLOCKED-OPERATOR-DECISION, correcting my own
      over-broad first pass at this extraction.** `FLUID-ARBITRUM`/`SUSHISWAP_V2-ARBITRUM`/`SUSHISWAP_V3-ARBITRUM`
      are clean (registered in `ALL_DEFI_VENUES`, no `VENUE_DATA_TYPE_CAPABILITIES` entry, no conflicting shipped
      fix) — extracted. `ALCHEMY-{ARBITRUM,BASE,ETHEREUM,OPTIMISM,POLYGON}` are NOT extracted: the 2026-08-17
      na-eligibility-audit pass (line below) already found these 5 directly contradict a shipped fix
      (`unified-api-contracts@21a7e5c305`, 2026-08-09) that deliberately DELETED these exact composite-spelling
      keys as phantom declarations no writer can match — re-adding them needs an explicit decision from the
      operator between OPTION A (teach the denominator to resolve gas_fees via bare-venue+chain-column grain,
      matching the shipped design) and OPTION B (deliberately re-declare a different-shaped record with a
      cross-reference to the removal) — see the 2026-08-17 na-eligibility-audit finding two lines below for the
      full evidence trail. Stays open here, `assigned_vm: NA`, BLOCKED-OPERATOR-DECISION.
- [x] ✅ [AGENT] P1. **Readiness state — RULED 2026-08-16 (operator): DERIVED from the contract steps.** Not declared,
      and not a hybrid. A declared state rots, and a stale `LIVE-READY` is precisely the claim-exceeds-measurement
      failure this workspace bans. **The binding consequence**: every contract step must become genuinely
      machine-checkable — a step with no real check cannot contribute a passing verdict, and must surface as
      "unverified", never silently as ready. That makes step-checkability a hard prerequisite of W4/W5 rather than a
      nice-to-have, and it is the reason step 17 is tracked as a real bidirectional check above.

## Definition of done for the umbrella

- [ ] [AGENT] P0. **Every venue in the universe reaches at least `BACKTESTABLE`**, with the batch smoke test passing
      per data type, and the readiness state visible per venue rather than asserted in prose.
- [ ] [AGENT] P0. **A new venue can be taken to `BACKTESTABLE` by following the contract above with no tribal
      knowledge** — verified by doing it for one venue end to end and recording where the contract was ambiguous.
- [ ] [AGENT] P1. **The carve-out's §A5 prerequisites are satisfied for the contracted scope** — the four CEX venues
      and Lido at `LIVE-READY`, which is the intersection of this plan and the carve-out's.
- [x] [AGENT] P2. ✅ **Cross-link the karak remediation-direction split + author pendle's own issue doc.** SHIPPED —
      `unified-trading-pm@abf0117caa`. Added a bidirectional pointer between `karak_decommission_2026_08_16.md`
      (delete direction) and `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md` (its "20 never-
      instantiated connectors" list, which had listed Karak as needing wiring) — each now explicitly states the
      decommission decision supersedes the wire-it framing for Karak. Authored
      `plans/active/issues/pendle_venue_onboarding_2026_08_16.md`: Pendle is a real registered venue (UAC
      `venue_adapter_keys.py`/`capability_declarations/_defi.py`, YIELD class) with a working simulation-only
      connector, zero `DeFiAdapter` dispatch wiring, zero UAC `DEFI_VENUE_TO_CONNECTOR_CLASS` entry — confirmed a
      latent, not active, SIT-invariant gap (no strategy archetype currently declares it in `venue_universe`, so it
      wasn't in the failing set that blocked L228). Both older docs' `related:` frontmatter updated to cross-link
      all three.

## Progress Log

**2026-08-16 — authored.** Split out of the carve-out plan's §A5 P0 #2, which asked only for the lazy-load refactor;
the operator then widened the scope to registry hardening, config abstraction, full venue e2e wiring and a smoke-test
bar, framed as track (a) — "get the system to full capability and into a shape that makes carve-out doable". Shape
(umbrella + children) and split (LOCAL design / AO mechanical) both operator-chosen the same day.

**2026-08-16 — dead reference dropped.** `strategy-service/EXTRACTION_AUDIT.md` was cited in `context_scope` but does
not exist in the repo (working tree or git history, confirmed by full recursive search) — removed. See the child plan's
Progress Log for the independent spot-check of the numbers this file was meant to back.

**2026-08-16 — contract step 1 ("Declared") partially evidenced by W2.** Per
`/plans/archive/2026_08/registry_ssot_hardening_2026_08_16.md`'s Measured Baseline (2026-08-16 sweep), three of the five
"one declaration, no per-service copies" concerns are **clean, no fold needed**: adapter keys (exactly one
`VENUE_TO_ADAPTER_KEY` dict), instrument types (zero redefinitions outside UAC), and data types (zero redefinitions
outside UAC) — all across the 7 umbrella repos. The capability-record concern (three orthogonal `VenueCapability*`
types, no merge needed) and error-code-map concern (implementation clean, coverage unverified) are also resolved/
in-progress there; see that plan's todos 1 and 3. A future venue-readiness check should cite this baseline rather than
re-running the same sweep.

**2026-08-16 — "Declare archetype to feature_groups" (the P0 above this entry) built and verified, NOT YET SHIPPED —
blocked by an unrelated repo-wide gate, not a design gap.** Research pass found `MULTI_GROUP_STRATEGIES`
(strategy-service `cli/handlers/batch_data_loading.py`) is stale pre-v2 scaffolding (references archetype names that
predate the current 59-member `StrategyArchetype` enum) — do not extend it. Of the 59 archetypes, only 5 have real
code-level evidence for their feature_group consumption, traced to `paper_run_handler.py`'s tick-loader dispatch
(frozenset-keyed by `spec.archetype`): `CARRY_STAKED_BASIS`, `CARRY_STAKED_BASIS_DATED`, `CARRY_RECURSIVE_STAKED` →
`{lending_rates, lst_yields}`; `YIELD_STAKING_SIMPLE` → `{lst_yields}`; `YIELD_ROTATION_LENDING` → `{lending_rates}`.
The remaining 54 (ML_DIRECTIONAL, RULES_DIRECTIONAL, MARKET_MAKING, VOL_TRADING, STAT_ARB_PAIRS, EVENT_DRIVEN, most
ARBITRAGE_STRUCTURAL/MEV, DEFI_LP, PORTFOLIO, the CARRY_BASIS_PERP/DATED family) have zero code signal — no
feature-name→feature_group registry exists to derive them mechanically either (checked: sample archetype default
feature names like `"zscore_btc_1h"` don't map to a group without domain judgment). Operator ruling this session:
declare only the 5 confirmed, mark the rest explicitly UNDECLARED (never silently "consumes nothing"), track the rest
as follow-up.

Built in `unified-api-contracts` (working tree, uncommitted as of this entry):
`unified_api_contracts/internal/architecture_v2/archetype_feature_groups.py` (new — `ARCHETYPE_FEATURE_GROUPS`,
`UNDECLARED_ARCHETYPES`, `ArchetypeFeatureGroupUndeclaredError`, `get_archetype_feature_groups()`,
`get_archetype_required_inputs()` — composes with `canonical.domain.features.required_inputs
.FEATURE_REQUIRED_INPUTS`, does not restate it), `unified_api_contracts/internal/architecture_v2/__init__.py`
(exports wired in), `tests/unit/test_archetype_feature_groups.py` (new). Full repo `quality-gates.sh` run: 13246
passed, 1 unrelated pre-existing failure (`test_execution_service_venue_coverage_cascade_invariant.py
::test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions`, confirmed via `git stash` on a
clean tree to reproduce identically with none of these 3 files present).

**Not shipped**: `quickmerge.sh` re-gates the full repo and blocks on that same failure — `karak`/`pendle`/`symbiotic`
DeFi-connector reachability, already tracked (`/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`
P0, `/plans/archive/issues/symbiotic_venue_onboarding_2026_08_16.md` P1). The baseline file's own commit note documents
this exact set flip-flopping reachable/unreachable twice already today under a concurrent session's active DeFiAdapter
wiring work — confirmed stable (not a stale race) via two identical consecutive quickmerge re-gates minutes apart.
Operator chose "wait and retry later" over hand-editing the contested baseline file. **Resume**: `cd
unified-api-contracts && git status` — if the 3 files above are still present in the working tree, re-run
`bash scripts/quickmerge.sh "feat: declare archetype to feature_groups SSOT link (venue_readiness_and_registry_hardening_2026_08_16
L228)" --agent --files 'unified_api_contracts/internal/architecture_v2/archetype_feature_groups.py
unified_api_contracts/internal/architecture_v2/__init__.py tests/unit/test_archetype_feature_groups.py'` once the
karak/pendle/symbiotic gate has cleared (check the two issue docs above first); if it lands, flip the "Declare
archetype to feature_groups" checkbox above with the resulting `unified-api-contracts@<sha>`. If the 3 files are
gone (a different session's checkout, or this slot's working tree was reset), this entry has the full design to
redo it without re-running the archetype research — the 5-archetype mapping + citations above is the complete
answer, not just a pointer.

**2026-08-16 — still blocked, 3rd confirmation, NOT a stale race.** Post-compact re-check: the committed baseline
JSON on disk (`unified-api-contracts@88a71f8e`) currently reads `unreachable_defi_venues: ["morpho", "kamino"]`
only — karak/pendle/symbiotic look cleared from a snapshot read. A direct standalone re-run of
`tests/test_execution_service_venue_coverage_cascade_invariant.py::test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions`
(not a snapshot read — the actual invariant) shows they are **not** cleared:
`new_regressions=['karak', 'pendle', 'symbiotic']`. Cross-checked against both open issue docs
(`venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`,
`symbiotic_venue_onboarding_2026_08_16.md`) — both still carry their `- [ ]` (unchecked) P0 "wire
Symbiotic/karak/pendle into DeFiAdapter's real dispatch" todos, consistent with the live measurement, not with the
baseline file's snapshot. The baseline file's own description already documents this exact flip-flop happening
twice earlier today under a concurrent session's active DeFiAdapter dispatch work and says to trust a fresh
re-run over its own prose — this is that fresh re-run, and it confirms the gap is still open. Not retrying
quickmerge a 3rd time against the same root cause; this is someone else's in-flight work
(execution-service DeFiAdapter dispatch wiring), not a defect in the 3 archetype-feature-groups files. **Resume**:
before the next quickmerge attempt, re-run the invariant test standalone first (not just a baseline-file read) —
`cd unified-api-contracts && .venv/bin/python -m pytest tests/test_execution_service_venue_coverage_cascade_invariant.py::test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions -v`
— only proceed to `quickmerge.sh` once that passes standalone.

**2026-08-16 — still blocked, 4th confirmation, same root cause; two new cross-doc findings tracked as a todo.**
Another fresh standalone re-run of the invariant (not a baseline snapshot) reproduces the identical
`new_regressions=['karak', 'pendle', 'symbiotic']` — the 4th identical confirmation today, stable not flapping. Per
this session's own async-wait guidance ("two identical consecutive failures... stop blind-retrying"), no further
bare rechecks planned; the actual unblock is someone else's in-flight `DeFiAdapter` dispatch-wiring work landing.
While surveying that work's tracked docs, found: (1) `karak_decommission_2026_08_16.md` (delete — wrong contract
address) and `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md` (wire up) give karak opposite
remediation directions with no cross-reference between them; (2) pendle has no dedicated remediation doc, only
incidental mentions across 7 other issue docs. Neither blocks this plan's P0 directly, so not fixed inline —
tracked as the new P2 todo above ("Cross-link the karak remediation-direction split...") rather than editing two
other active docs mid-session. This plan's own 3 files remain unchanged and correct (re-read in full this session,
no drift); nothing here changes the resume recipe two entries above.

**2026-08-16 — still blocked, 5th confirmation, pre-compact audit.** A full `unified-api-contracts` QG suite run
(13246 passed, 1 failed, 678 skipped, 5 xfailed) reproduces the identical single failure —
`test_execution_service_venue_coverage_cascade_invariant.py::test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions`
— nothing else red. Fifth identical confirmation today; per this session's own async-wait guidance the condition is
stable, not flapping, and the cause is confirmed external (someone else's in-flight `DeFiAdapter` dispatch-wiring
work for karak/pendle/symbiotic, not these 3 files). No further action taken this entry beyond logging the
confirmation — the resume recipe from the "3rd confirmation" entry above still applies verbatim: re-run the
invariant standalone first, only quickmerge once it passes. `unified-api-contracts` working tree unchanged
(3 files, `ahead=0`/`behind=0` on committed history); `unified-trading-pm` clean.

**2026-08-16 — still blocked, 6th confirmation, direct-cause recheck.** Checked the actual blocking condition directly
instead of re-running the full invariant: `execution-service` HEAD moved `37bfaeed0` → `9af4713c` (a routine
`origin/main` backmerge, not new work) since the last check; its most recent substantive commit is still `37bfaeed`
("wire real Uniswap/Lido/Jupiter into live dispatch... Jito jitoSOL connector") — unrelated to karak/pendle/symbiotic.
`grep -rin "karak\|pendle\|symbiotic" defi_adapter.py` = 0 hits, same as every prior check. All 3 tracking issue docs
(`plans/active/issues/karak_decommission_2026_08_16.md`, `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`,
`symbiotic_venue_onboarding_2026_08_16.md`) remain `status: open` — none flipped to resolved/in-progress since last
checked. Condition unchanged; did not re-run the full QG suite (the direct-cause check is a cheaper, equally conclusive
signal — the invariant fails iff these venues are unwired, and they're still unwired). A `ScheduleWakeup` (1800s) is
armed to repeat this exact check — note for any session reading this cold: that wakeup is ephemeral (not itself
durable), so if no further Progress Log entry appears after this one, the wakeup either hasn't fired yet or this
session ended before it could; re-arm manually if picking this up fresh. `unified-api-contracts` still 3 uncommitted
files, `ahead=0`/`behind=0`; `unified-trading-pm` clean.

**2026-08-16 — still blocked, 7th confirmation (full-suite + direct-cause, both fresh).** Two independent checks this
pass, both consistent: (1) a background full `unified-api-contracts` QG suite run (180.77s) reproduces the identical
single failure — `1 failed, 13246 passed, 678 skipped, 5 xfailed` — with
`test_execution_service_venue_coverage_cascade_invariant.py::test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions`
as the sole failure, nothing else red; (2) a fresh direct-cause recheck: `execution-service` HEAD unchanged at
`9af4713c` (no new commits), `grep -rin "karak\|pendle\|symbiotic" defi_adapter.py` = 0 hits, all 3 tracking issue docs
still `status: open`. Also during this pass, `unified-trading-pm` fast-forwarded one commit behind
(`dd6ddfb80b` → `7d1ac5c51a`) — a different slot's unrelated doc-only commit
(`docs(plans): pause aster relaunch-budget-scaling ruling...`, slot-1) — pulled in cleanly via `--ff-only`, touches
none of this plan's files. `unified-api-contracts` still exactly the same 3 uncommitted files, `ahead=0`/`behind=0`.
Condition is now confirmed stable across 7 independent checks (5 full-suite, 2 direct-cause) spanning the whole session;
resume recipe unchanged from the "3rd confirmation" entry above. Standing instruction remains in force: do not
hand-wire the venues or edit the SIT ratchet baseline.

**2026-08-16 — still blocked, 8th confirmation, direct-cause recheck (heartbeat).** `execution-service` HEAD unchanged
at `9af4713c` (no new commits); `grep -rin "karak\|pendle\|symbiotic" defi_adapter.py` = 0 hits, same as every prior
check; all 3 tracking issue docs still `status: open`. Condition confirmed stable across 8 independent checks (5
full-suite, 3 direct-cause) spanning the whole session. `unified-api-contracts` still the same 3 uncommitted files,
`ahead=0`/`behind=0`; `unified-trading-pm` clean at `ahead=0`/`behind=0`. Resume recipe unchanged from the "3rd
confirmation" entry above. Standing instruction remains in force: do not hand-wire the venues or edit the SIT ratchet
baseline.

**2026-08-16 — still blocked, 9th & 10th confirmations, two quickmerge attempts.** Attempted to ship
`archetype_feature_groups.py` via `quickmerge.sh` twice in succession (`quickmerge_uac.log`, `quickmerge_uac_retry2.log`
in scratchpad); both re-ran the full `unified-api-contracts` QG suite and both failed identically at
`test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions` — `1 failed, 13246 passed, 678 skipped,
5 xfailed`, quickmerge's own re-gate step reported "REAL failure, not a lost race" both times. Same 3-venue signature as
every prior check. Condition now confirmed stable across 10 independent checks (7 full-suite, 3 direct-cause) spanning
the whole session — this is not flapping, it is a stable external blocker. `unified-api-contracts` HEAD unchanged at
`c9e5780e33` (`_backmerge` merge commit), still the same 3 uncommitted files, `ahead=0`/`behind=0`. Resume recipe
unchanged from the "3rd confirmation" entry above. Standing instruction remains in force: do not hand-wire the venues or
edit the SIT ratchet baseline.

**2026-08-16 — still blocked, 11th confirmation, background QG run.** A full `unified-api-contracts` QG suite run
(background task, harness-tracked, not a scratchpad file) completed after the 9th/10th entries above: `1 failed, 13246
passed, 678 skipped, 5 xfailed in 180.77s` — same failing test,
`test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions`, nothing else red. 11th identical
confirmation this session (8 full-suite/quickmerge, 3 direct-cause). Resume recipe unchanged from the "3rd confirmation"
entry above. Standing instruction remains in force: do not hand-wire the venues or edit the SIT ratchet baseline.

**2026-08-16 — still blocked, 12th confirmation, standalone targeted re-run after PM fleet sync.** `unified-trading-pm`
fast-forwarded 5 commits (`a924a6e84d`→`284e0b8bc1`: cefi Barchart removal + OKX xperp marker dispatch plans from other
concurrent work, none touching this plan or `unified-api-contracts`). Re-ran
`test_execution_service_venue_coverage_cascade_invariant.py` standalone in `unified-api-contracts` post-sync: same
single failure, `test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions`, identical
`['karak', 'pendle', 'symbiotic']` signature, `1 failed, 10 passed in 0.49s`. 12th identical confirmation this session
(8 full-suite/quickmerge, 4 direct-cause/targeted). Condition remains stable; external fleet activity elsewhere on the
shared branch has not touched the blocker. Resume recipe unchanged from the "3rd confirmation" entry above. Standing
instruction remains in force: do not hand-wire the venues or edit the SIT ratchet baseline.

**2026-08-16 — still blocked, 13th confirmation, /heartbeat check-in.** `unified-trading-pm` fast-forwarded 1 more
commit (`541ead2b3a`→`396c8a1bdb`: AO-dispatched strategy-service-centralization plan from other concurrent work, does
not touch this plan or `unified-api-contracts`). Re-ran
`test_execution_service_venue_coverage_cascade_invariant.py` standalone in `unified-api-contracts`: same single
failure, `test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions`, identical
`['karak', 'pendle', 'symbiotic']` signature, `1 failed, 10 passed in 0.44s`. 13th identical confirmation this session
(8 full-suite/quickmerge, 5 direct-cause/targeted). Condition remains stable across multiple unrelated fleet syncs.
Resume recipe unchanged from the "3rd confirmation" entry above. Standing instruction remains in force: do not
hand-wire the venues or edit the SIT ratchet baseline.

**2026-08-16 — still blocked, 14th confirmation, /heartbeat check-in.** `unified-trading-pm` fast-forwarded 4 more
commits (`396c8a1bdb`→`eeb1113ebc`: a DP-FETCH-009 stale-manifest-rows issue doc + a `main`↔`_backmerge` merge + an
unrelated promote PR merge + na-audit-round-7 rulings — none touch this plan or `unified-api-contracts`). Re-ran
`test_execution_service_venue_coverage_cascade_invariant.py` standalone in `unified-api-contracts`: same single
failure, `test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions`, identical
`['karak', 'pendle', 'symbiotic']` signature, `1 failed, 10 passed in 0.44s`. 14th identical confirmation this session
(8 full-suite/quickmerge, 6 direct-cause/targeted). Condition remains stable across multiple unrelated fleet syncs.
Resume recipe unchanged from the "3rd confirmation" entry above. Standing instruction remains in force: do not
hand-wire the venues or edit the SIT ratchet baseline.

**2026-08-16 — still blocked, 15th confirmation, /heartbeat check-in — partial progress detected.**
`execution-service`'s `defi_adapter.py` now DOES dispatch Symbiotic: `SymbioticConnector` is imported, injected, and
`_execute_symbiotic_staking()` is wired into the venue-routing `if "SYMBIOTIC" in venue:` branch (0 hits for
karak/pendle unchanged). This looked like it might clear the invariant, so re-ran
`test_execution_service_venue_coverage_cascade_invariant.py` standalone in `unified-api-contracts`: still fails,
identical `['karak', 'pendle', 'symbiotic']` signature, `1 failed, 10 passed in 0.45s`. Diagnosed why symbiotic still
shows unreachable despite the new dispatch code: the test's own `DEFI_VENUE_TO_CONNECTOR_CLASS` map (in
`unified-api-contracts/tests/test_execution_service_venue_coverage_cascade_invariant.py`) has no entry for
`symbiotic`/`karak`/`pendle` at all — `unreachable_defi_venues()` short-circuits to "unreachable" the moment
`DEFI_VENUE_TO_CONNECTOR_CLASS.get(venue)` returns `None`, before it ever checks `connector_supports_live()` or actual
dispatch wiring. So the remaining gap is now on the **UAC test's own connector-class registry**, not (or not only) on
execution-service's dispatch — execution-service's symbiotic wiring is real progress but insufficient alone; the map
entry is presumably part of the same in-flight work and just hasn't landed yet. This map lives in the SIT-adjacent test
file itself, which the standing instruction already covers ("do not hand-wire the venues or edit the SIT ratchet
baseline") — not touching it. `karak_decommission_2026_08_16.md` still `status: open`; no dedicated pendle issue doc
exists yet (L342 below covers authoring one). 15th identical-outcome confirmation this session (8 full-suite/quickmerge,
7 direct-cause/targeted), though this is the first one to observe partial upstream progress rather than zero change.
Resume recipe unchanged from the "3rd confirmation" entry above. Standing instruction remains in force: do not
hand-wire the venues, do not add the missing `DEFI_VENUE_TO_CONNECTOR_CLASS` entries, and do not edit the SIT ratchet
baseline.

**2026-08-16 — UNBLOCKED, 16th confirmation — L228 shipped.** Re-ran the invariant standalone:
`test_execution_service_venue_coverage_cascade_invariant.py::test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions
PASSED`. `unified-api-contracts` working tree came back clean (`git status --porcelain` empty) — the 3 files tracked
as uncommitted-but-verified since the "NOT YET SHIPPED" entry above are now committed as `2fa22fee` ("feat: declare
StrategyArchetype to feature_group mapping (UAC SSOT)"), present on `origin/live-defi-rollout`,
`git rev-list --count origin/live-defi-rollout..HEAD` = 0. **CORRECTED 2026-08-19 (`/plan-reconcile
security_and_cross_cutting_master` Phase 1/3, independently re-verified against
`unified-api-contracts/tests/data/execution_service_venue_reachability_baseline.json`'s own dated docstring +
`git log` on that baseline file — commits `88a71f8e`/`6dba7ac5`)**: the original entry below was wrong about the
mechanism. **Karak and pendle did NOT get wired** — `execution-service/execution_service/adapters/defi_adapter.py`
has zero `karak`/`pendle` references today (live-verified), and the baseline file's own docstring explicitly
confirms both remain "STILL genuinely unreachable... DeFiAdapter has no KARAK/PENDLE gate marker at all" (they stay
correctly listed in `unreachable_defi_venues`, an accepted, tracked ratchet gap — not a masked false-green). The
real cause of the SIT invariant going green was narrower: **Symbiotic alone** got a real `DeFiAdapter` dispatch wire
(`execution-service@85c8310b2`) AND the checker's own `DEFI_VENUE_TO_CONNECTOR_CLASS`/`DEFI_VENUE_TO_GATE_MARKER`
dicts (which previously had no entry for symbiotic/karak/pendle at all, making all three unconditionally
"unreachable" as a false NEGATIVE signal regardless of wiring) got a real symbiotic entry added — karak/pendle's
entries were correctly RESTORED to the baseline, not removed. This session's own 3 files shipping and the invariant
passing were two independent, correctly-outcomed events, not causally "karak/pendle landing." No live-safety risk
found (the ratchet baseline is accurate); the original claim below is left struck-through rather than deleted, per
this corpus's audit-trail-preservation convention.

~~Someone else's concurrent `DeFiAdapter` dispatch-wiring work (karak/pendle/symbiotic) landed and cleared the SIT
invariant; this session's own 3 files were then shipped (by this or another slot — the commit predates this check)
without needing to touch the ratchet baseline.~~ Also
corrected a stale entry the same edit: the "Deferred work" table below still listed L342 (karak cross-link + pendle
issue doc) as "Not done" though the Definition-of-done section above already recorded it shipped
(`unified-trading-pm@abf0117caa`) — a misleading pointer, fixed on contact rather than left to re-mislead the next
reader. Table rewritten to drop both resolved items and reflect that "Add contract step 17" is now the sole
actionable P0.

- **na-eligibility-audit 2026-08-17** [body-hash:2d0818123cc6d9f1]: RECLASSIFY candidate PARKED (conflict) -- stays KEEP-NA. The 'Declare capability for the 8 undeclared DeFi venues' todo (lines 574-580) bundles 2 sub-cases the conflict-check split apart: (a) the 5 ALCHEMY-{ARBITRUM,BASE,ETHEREUM,OPTIMISM,POLYGON} gas_fees entries directly contradict an already-shipped fix in the active issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md (unified-api-contracts@21a7e5c305, 2026-08-09), which DELETED those exact composite-spelling keys as phantom declarations no writer could ever match (the real MTDS writer emits bare 'ALCHEMY' + a separate chain= column) -- re-adding them as worded would reintroduce a pattern deliberately removed; (b) the other 3 venues (FLUID-ARBITRUM, SUSHISWAP_V2/V3-ARBITRUM) show no such contradiction. BLOCKED-OPERATOR-DECISION: needs an explicit ruling on the Alchemy/gas_fees portion -- OPTION A: teach the denominator script to resolve gas_fees via bare-venue+chain-column grain (matching the shipped design) rather than composite per-chain keys [WORKER REC -- keeps the phantom-key fix intact]; OPTION B: deliberately re-declare a different-shaped composite record for Alchemy gas_fees with an explicit cross-reference to the 2026-08-09 removal (if there's a reason the removal doesn't apply to declaration-only capability records). Not flipped; not guessed. Cross-cutting tranche audit conflict-check finding.

- **context-scout 2026-08-17**: refreshed context_scope (6 entries) — added a fingerprint match found while scouting
  a different batch: `issues/uac_kamino_venue_reachability_cascade_regression_2026_08_15.md` independently records
  the identical `unreachable_defi_venues: ["morpho", "kamino"]` baseline content
  (`unified-api-contracts@88a71f8e`) and the same `test_execution_service_venue_coverage_cascade_invariant.py` test
- **`/plan-reconcile uac_master` 2026-08-18**: the doc referenced above resolved and archived
  (`kamino`/`morpho` left the baseline, `unified-api-contracts@9b982906`) — repointed the `context_scope` entry to
  `/plans/archive/issues/uac_kamino_venue_reachability_cascade_regression_2026_08_15.md`.
  this plan's own Progress Log traces above — that doc's sole open todo (close it once morpho/kamino leave the
  baseline) is this plan's own wiring work reaching completion. context_scope added on both docs; this doc's other 5
  entries and remaining content not otherwise re-scouted this pass (out of the assigned batch's scope).

- **context-scout 2026-08-17 (full pass)**: independently re-verified all 6 entries (the fingerprint-match entry
  above plus the other 5) against this doc's own body text — the carve-out plan (the doc's stated purpose), the
  reachability audit issue (contract step 12's basis), config-reloader-pattern (cited by name in the Design-rulings
  section), tier-and-import-architecture (the strategy-service-never-reads-MTDS hard rule), shard-level-failure-
  isolation (cited by name in the Error-code-SSOT-shape ruling: "shard-level failure isolation and the
  DependentAction ladder"). All still resolve; list unchanged (6 entries, at the target cap) — this doc's own
  remaining scope (1 open P1 todo, otherwise waiting on its 5 forked children) is thin enough that the existing
  plan/codex pointers outweigh adding a source path.

- **na-eligibility-audit 2026-08-17** [body-hash:123ebd72ee10e83c]: RECLASSIFY (per-todo split) -- of 7 open todos, 1 is bounded/worker-determinable and extracted to cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md item 5: 'Publish the granularity view' -- the doc's own text confirms this is now purely a rendering task (the underlying VENUE_GRANULARITY_CAPABILITIES registry + get_granularity() already shipped 2026-08-16 with 412 populated cells), not a data-population one. Doc stays assigned_vm: NA for its remaining 6 items: 'Consolidate venue_universe into a clean UAC SSOT' (explicitly deferred pending W4's fork), 'Sign off each proposed merge' ([OPERATOR] P0), 'Declare capability for the 8 undeclared DeFi venues' (already PARKED as a conflict by this same tranche's earlier 2026-08-17 pass -- BLOCKED-OPERATOR-DECISION, not re-litigated here), and the 3 'Definition of done for the umbrella' items (cross-cutting completion bars spanning the whole umbrella's mechanical sweep across ~7 repos, not single-outcome work -- matches the 'multi-file, multi-day' bar even where individually phrased as one todo). Conflict-check clear for the extracted item: no other active plan claims building this render/report. Cross-cutting tranche audit.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — 6 open checkboxes (grep matches Phase-0's 6); every item is either explicitly [OPERATOR]-tagged, already PARKED by two same-day 2026-08-17 na-eligibility-audit passes on THIS exact doc.

- **context-scout 2026-08-20**: refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, batch 3/3): RECLASSIFY (per-todo split), corrected
  mid-pass. First pass extracted the full "8 undeclared DeFi venues" todo without re-reading this doc's own
  2026-08-17 audit history first — the 2026-08-17 pass had already found 5 of the 8 (the Alchemy gas-fee-oracle
  spellings) conflict with a shipped fix that deliberately removed those exact keys, and PARKED that item
  BLOCKED-OPERATOR-DECISION. Caught before shipping this pass's final report: narrowed the extraction to only the
  3 conflict-free venues (Fluid/Sushiswap) in `cross_cutting_satellite_ao_dispatch_batch22_2026_08_21.md` item 3;
  the 5 Alchemy venues stay on this doc, `assigned_vm: NA`, BLOCKED-OPERATOR-DECISION per the 2026-08-17 finding.
  Doc's other 5 open items stay NA unchanged (operator sign-off gate, venue_universe SSOT consolidation deferred to
  W4, 3 umbrella completion-bar items spanning ~7 repos — none single-outcome/bounded).

## Deferred work after 2026-08-16

**2026-08-16 correction**: this table previously listed W3/W4/W5 and both `[OPERATOR]` design rulings as unresolved.
That went stale — the Workstreams section and Design-rulings section above (L354-410) already record both rulings as
RULED and W3 as resolved (folded into an existing plan, no new plan needed). Rewritten to match current state.

| Item | State | Blocked on |
| --- | --- | --- |
| "Consolidate `venue_universe` into a clean UAC SSOT" (P2, L265) | Not started | Natural fit for W4 once its own blocker (below) clears; not needed for the shipped "at least one archetype" reading of step 17 |
| W3 "service-config abstraction" child plan | ✅ Resolved, no new plan | Folded into `/plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` § D delta |
| W4 "venue e2e wiring" child plan | Forked (`status: draft`) | ✅ Unblocked 2026-08-16 — "Define the universe precisely for W4/W5" resolved, see § "Design rulings needed before the mechanical children dispatch" above |
| W5 "smoke-test bar" child plan | **Corrected 2026-08-20**: DOES exist (`plans/active/venue_smoke_test_bar_2026_08_16.md`, 9 open/1 done todos + a gated finalize plan) — the "not forked yet" claim was itself stale | ✅ Unblocked 2026-08-16 — same resolution as W4; per F-G31-3, still sat at `status: draft` (undispatchable) 4 days past its own unblock condition — separately corrected in that doc |
| "Error-code SSOT shape" design ruling (L321) | ✅ RULED 2026-08-16 | Extend `classify_venue_error()` into a (venue, code) registry — see L397-403 |
| "Config-abstraction target shape" design ruling (L325) | ✅ RULED 2026-08-16 | One `config.py` per service, domain-split only when cap-forced — see L404-410 |
| "Declare capability for the 8 undeclared DeFi venues" (P1, new) | ✅ PARTIAL — 3/8 extracted 2026-08-21, 5/8 BLOCKED-OPERATOR-DECISION | 3 conflict-free venues (Fluid/Sushiswap) → `cross_cutting_satellite_ao_dispatch_batch22_2026_08_21.md` item 3; 5 Alchemy venues need an operator ruling per the 2026-08-17 conflict finding above |

**Recommended next item**: **W4 "venue e2e wiring"** (`venue_e2e_wiring_2026_08_16.md`) — its universe-definition
blocker is resolved (192 declared venues / 353 (venue, data_type) pairs is the real denominator, per
`unified-api-contracts/scripts/generate_venue_universe_denominator.py`), so the per-venue mechanical sweep can now
dispatch. The CANONICAL ORTHOGONALITY audits (P0/P0/P1, below) and the 8-venue DeFi capability gap (P1, new row
above) remain independently actionable and can run concurrently — different file sets, no conflict.
