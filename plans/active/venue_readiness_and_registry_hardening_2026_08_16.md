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
parent_epic: infrastructure_master
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
- [ ] [OPERATOR] P0. **Where does the granularity declaration live?** Keyed per (venue x instrument-type x data-type),
      must express exceptions at that granularity, read by both MDPS and execution-service. Most likely an extension of
      the UAC venue capability record rather than a new registry — but that is a shape call, and it should be made
      before population, because population is the expensive half. **Cross-reference (2026-08-16, W2 resolved)**:
      `/plans/active/registry_ssot_hardening_2026_08_16.md` todo 1 resolved the three `VenueCapability*`-named UAC
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
- [ ] [AGENT] P1. **Publish the granularity view.** Render it as a table a human can read: venue, instrument type, data
      type, granularity, achievable matching class. This is what makes "what can we actually do here" answerable without
      reading code — and it is the same table we can show a counterparty.

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

- [ ] [AGENT] P0. **Declare archetype to feature_groups.** The missing link. Compose it with `FEATURE_REQUIRED_INPUTS`
      to derive each archetype's full input requirement set without restating it anywhere.
- [ ] [AGENT] P0. **Add contract step 17 as a real check, both directions.** A venue is not `BACKTESTABLE` unless at
      least one archetype's requirements are fully satisfiable from it, and every data type it provides is either
      consumed or explicitly declared unused. Declared-unused is a legitimate answer; silence is not.
- [ ] [AGENT] P1. **Report the unconsumed set.** Data types captured but consumed by no archetype are either a missing
      strategy or wasted capture cost. Either is worth knowing; neither is visible today.

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

- [ ] [AGENT] P0. **Audit the data-type vocabulary for near-duplicates.** Output: a proposed minimal orthogonal set,
      each near-duplicate pair named with its superset/subset relationship stated. Proposal only — the merge follows the
      rename rule and the purge follows delete-safety.
- [ ] [AGENT] P0. **Audit for orphaned data types** — captured but consumed by nothing. Each resolves to a missing
      strategy, a merge candidate, or an explicit declared-unused. Never left silent.
- [ ] [AGENT] P1. **Audit venue identities for duplicates** — the same effective venue represented twice. Same
      treatment: propose, migrate consumers in one change, register the cutover, route the purge through delete-safety.
- [ ] [OPERATOR] P0. **Sign off each proposed merge before migration.** Merging two data types rewrites paths, manifest
      rows and consumer bindings at once, and the purge is a prod delete. Both sides are operator-gated.

## Workstreams — each forks to its own child plan

Children are authored separately so each stays under the line cap and workstreams can run concurrently. **Design
rulings stay in this LOCAL plan; mechanical per-venue sweeps fork to AO-dispatched children** (operator ruling
2026-08-16).

- [x] [AGENT] P0. ✅ **W1 — lazy/scoped loading.** Forked to
      [`/plans/active/lazy_scoped_loading_refactor_2026_08_16.md`](/plans/active/lazy_scoped_loading_refactor_2026_08_16.md).
      Three layers; UAC is the dominant one with fleet-wide blast radius. Referenced by carve-out §A5 P0 #2.
- [x] [AGENT] P0. ✅ **W2 — registry SSOT hardening.** Forked to
      [`/plans/active/registry_ssot_hardening_2026_08_16.md`](/plans/active/registry_ssot_hardening_2026_08_16.md) —
      unified-trading-pm@a8465760e5. A same-pattern grep sweep across all 7 umbrella repos, done at authoring
      time, found 4 of 5 concerns (adapter keys, instrument types, data types, error-code classification) already
      single-SSOT with zero per-service redefinitions; the child plan's real open scope is a same-repo
      `VenueCapability*` naming-overlap resolution plus an error-code coverage audit.
- [ ] [AGENT] P0. **W3 — service-config abstraction.** Author the child plan. Per service: a `config.py`-style module
      with declared schemas, hot-reload wiring, and GCS-backed storage — every service, uniformly, so config is always
      findable in the same place. Existing pattern: [config-reloader-pattern](/codex/06-coding-standards/config-reloader-pattern.md).
      No in-service hardcoding; the gate should be able to detect a regression.
- [ ] [AGENT] P0. **W4 — venue e2e wiring.** Author the child plan. Walk the readiness contract steps 1–9 for every
      venue in the universe, instruments-service through execution-service, including transfers and feature-group
      availability. This is the largest workstream and the most mechanical — the best AO-dispatch candidate once the
      contract above is settled.
- [ ] [AGENT] P0. **W5 — smoke-test bar.** Author the child plan. A batch smoke test per data type per venue, so at
      minimum we know we can backtest. **Databento-sourced venues are exempt** (operator, 2026-08-16 — that source is
      already trusted). Where credentials exist or can be provisioned programmatically, add a testnet smoke test too.

## Design rulings needed before the mechanical children dispatch

These are the LOCAL half of the split — an AO worker cannot settle them alone, so they must be resolved here first.

- [ ] [OPERATOR] P0. **Error-code SSOT shape.** Where does "how we handle every API response/error code" live — a UAC
      registry keyed by (venue, code), an extension of `classify_venue_error()`, or per-venue declaration files? It must
      be greppable per venue and diffable when a venue changes its API. Decide the shape before anyone populates it,
      because the population is the expensive half.
- [ ] [OPERATOR] P0. **Config-abstraction target shape.** One `config.py` per service, or per domain within a service?
      What is the schema mechanism, and what does the gate check for to prove no in-service hardcoding crept back?
- [ ] [AGENT] P0. **Define the universe precisely for W4/W5.** "Every venue in our universe" needs a machine-readable
      list before it can be swept — 158 capture venues across 84 families is the current measured figure, but the
      readiness contract applies per (venue × data type), so state the real denominator and where it is derived from.
- [ ] [AGENT] P1. **Decide whether readiness state is DERIVED or DECLARED.** A derived state (computed from the twelve
      steps) cannot drift but needs every step machine-checkable; a declared state is cheap and rots. Prefer derived —
      but only where the check is real, per this workspace's measurement discipline.

## Definition of done for the umbrella

- [ ] [AGENT] P0. **Every venue in the universe reaches at least `BACKTESTABLE`**, with the batch smoke test passing
      per data type, and the readiness state visible per venue rather than asserted in prose.
- [ ] [AGENT] P0. **A new venue can be taken to `BACKTESTABLE` by following the contract above with no tribal
      knowledge** — verified by doing it for one venue end to end and recording where the contract was ambiguous.
- [ ] [AGENT] P1. **The carve-out's §A5 prerequisites are satisfied for the contracted scope** — the four CEX venues
      and Lido at `LIVE-READY`, which is the intersection of this plan and the carve-out's.

## Progress Log

**2026-08-16 — authored.** Split out of the carve-out plan's §A5 P0 #2, which asked only for the lazy-load refactor;
the operator then widened the scope to registry hardening, config abstraction, full venue e2e wiring and a smoke-test
bar, framed as track (a) — "get the system to full capability and into a shape that makes carve-out doable". Shape
(umbrella + children) and split (LOCAL design / AO mechanical) both operator-chosen the same day.

**2026-08-16 — dead reference dropped.** `strategy-service/EXTRACTION_AUDIT.md` was cited in `context_scope` but does
not exist in the repo (working tree or git history, confirmed by full recursive search) — removed. See the child plan's
Progress Log for the independent spot-check of the numbers this file was meant to back.

**2026-08-16 — contract step 1 ("Declared") partially evidenced by W2.** Per
`/plans/active/registry_ssot_hardening_2026_08_16.md`'s Measured Baseline (2026-08-16 sweep), three of the five
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
P0, `/plans/active/issues/symbiotic_venue_onboarding_2026_08_16.md` P1). The baseline file's own commit note documents
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
