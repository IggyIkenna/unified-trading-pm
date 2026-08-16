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

- [ ] [AGENT] P0. **Gate the normalisation rule.** Add a check that fails if strategy-service imports
      market-tick-data-service. It holds today by convention only; the gate makes it durable and costs almost nothing.
- [ ] [OPERATOR] P0. **Where does the granularity declaration live?** Keyed per (venue x instrument-type x data-type),
      must express exceptions at that granularity, read by both MDPS and execution-service. Most likely an extension of
      the UAC venue capability record rather than a new registry — but that is a shape call, and it should be made
      before population, because population is the expensive half.
- [ ] [AGENT] P0. **Make execution fail closed on fidelity.** Today the tier clamps DOWN silently, which is right for a
      backtest and wrong for a live/paper caller that assumed better. Decide per path — clamp-and-record versus refuse —
      and make refusal the default when a caller explicitly requests a tier the venue cannot serve.
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

## Workstreams — each forks to its own child plan

Children are authored separately so each stays under the line cap and workstreams can run concurrently. **Design
rulings stay in this LOCAL plan; mechanical per-venue sweeps fork to AO-dispatched children** (operator ruling
2026-08-16).

- [x] [AGENT] P0. ✅ **W1 — lazy/scoped loading.** Forked to
      [`/plans/active/lazy_scoped_loading_refactor_2026_08_16.md`](/plans/active/lazy_scoped_loading_refactor_2026_08_16.md).
      Three layers; UAC is the dominant one with fleet-wide blast radius. Referenced by carve-out §A5 P0 #2.
- [ ] [AGENT] P0. **W2 — registry SSOT hardening.** Author the child plan. Every venue fact declared once: capability
      record, data types, instrument types, adapter keys, error-code map. Audit for per-service copies and fold them.
      Depends on nothing; can start immediately.
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
