---
doc_type: codex-ssot
title: Cross-Domain State Fabric — Semantic Profile x Performance Tier, StateEnvelope, Valuation Interface
summary: >-
  The common cross-domain contract for absolute-state publication and reference-generation valuation across all five
  asset groups — two orthogonal axes (semantic profile of continuous-quote / block-ledger / event-resolution, and
  performance tier of hot / warm / cold), the StateEnvelope invariants, the valuation interface and why the Taylor
  factor-state form is the continuous-quote KERNEL rather than a universal formula. Carries the operator ruling
  register of 2026-08-20.
status: current
nature: ssot
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    execution-service,
    features-service,
    greeks-service,
    market-tick-data-service,
    strategy-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [architecture, state-fabric, factor-state, semantic-profile, performance-tier, finality, retraction, hft, ssot]
related:
  [
    /codex/04-architecture/slow-fast-routing-split.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
  ]
created: 2026-08-20
authoritative_for:
  [
    cross-domain state fabric contract (semantic profile x performance tier),
    StateEnvelope invariants and logical_position ordering,
    valuation interface vs continuous-quote kernel scoping,
  ]
referenced_by:
owner:
last_reviewed: 2026-08-20
code_refs:
---

# Cross-Domain State Fabric

> **What it is:** the contract every asset group shares for publishing absolute state and valuing against an immutable
> reference generation — and the two orthogonal axes that decide the mechanics and the deployment of each venue.
>
> **What it is NOT:** this is not
> [/codex/04-architecture/slow-fast-routing-split.md](/codex/04-architecture/slow-fast-routing-split.md). That doc
> splits **venue routing** (slow eligibility vs fast SOR — _which venue_). This doc splits **valuation and state**
> (slow reference generation vs fast evaluation — _what is it worth right now_). Two different slow/fast splits; do not
> conflate them.

## Provenance

Settled 2026-08-20 in an operator Q&A session that reviewed an external engineering specification,
`Cross_Venue_Factor_Repricing_Platform_Technical_Specification` v1.0 (20 August 2026), against the in-flight design in
[/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md](/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md)
sections 11-15. That external spec is a **continuous-quote profile specification using BTC as its worked example** — it
is not, and does not claim to be, an implementation spec for 192 venues and 60 archetypes. This doc is the cross-domain
layer above it.

## 1. Two orthogonal axes

The single most common framing error is to bundle _what kind of substrate this is_ with _how fast we must react to it_.
They are independent.

| Axis                 | Values                                                     | Decides                                                        |
| -------------------- | ---------------------------------------------------------- | -------------------------------------------------------------- |
| **Semantic profile** | `continuous_quote` \| `block_ledger` \| `event_resolution` | ordering key, finality model, recovery, mutation, action verbs |
| **Performance tier** | `hot` \| `warm` \| `cold`                                  | deployment, latency SLO, transport, infrastructure spend       |

Counter-examples that force the split: a DeFi mempool race is more latency-critical than a thin CeFi venue that prints
twice a minute; a sports book becomes effectively tick-rate the instant a goal lands; many continuous-quote venues never
justify colocated infrastructure.

**The one dependency between the axes**: a profile _bounds_ the achievable tier without determining it. `hot` on
`block_ledger` can only ever mean **first in the block / winning the mempool race** — block time is a physical floor, so
a microsecond SLO on an L1 venue is unmeetable by construction. State the bound in the manifest or someone will spec a
latency target physics will not honour.

## 2. The three semantic profiles

| Concern          | `continuous_quote`                    | `block_ledger`                                         | `event_resolution`                                      |
| ---------------- | ------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------- |
| **Ordering**     | feed epoch + sequence; local RX order | chain, block hash/height, tx index, log index          | event id, provider version, phase, correction sequence  |
| **Time**         | exchange event/send time + local RX   | block time, observation, inclusion, finality time      | occurrence, publication, receipt                        |
| **Mutation**     | newer complete state supersedes older | tentative -> canonical -> final; **reorg can retract** | provisional -> corrected/voided -> resolved             |
| **Recovery**     | snapshot + incremental bridge         | backfill canonical logs; reapply after reorg           | authoritative snapshot / correction / resolution        |
| **Action verbs** | cancel, reprice, amend, take          | submit/replace tx, change gas, route, wait             | quote, suspend, reopen, settle                          |
| **Primary risk** | gaps, staleness, double reaction      | reorg, gas, MEV, nonce, finality                       | bad event sequencing, corrections, premature settlement |

Asset groups map to profiles, not one-to-one: CeFi and TradFi are `continuous_quote`; DeFi is `block_ledger`; sports and
prediction are `event_resolution` — but prediction's continuous factors (implied probability, time decay) behave exactly
like the continuous-quote profile between discrete events.

### 2a. The `block_ledger` finality ladder

`included` and `confirmed` are not the same state and must not be collapsed. The ladder is:

```
observed -> included -> canonical -> confirmed -> finalized
                     \-> retracted/reorged
```

The venue manifest configures **which actions are permitted at each stage**. Acting on `observed` is a `hot`-tier
capability; the `warm` tier acts from `included` onward.

### 2b. Discrete events are a 2x2, not a list

Operator ruling 2026-08-20. Two **independent** questions decide how a discrete event is handled: is its **time** known
in advance, and is its **content** known in advance? A one-dimensional "scheduled vs unscheduled" split collapses two
different things and gets the staking case wrong.

|                  | **Content known**                                                         | **Content unknown**                                                           |
| ---------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **Time known**   | staking payment, funding settlement, LST rebase, coupon, expiry _instant_ | FOMC, CPI, earnings, option settlement fixing, prediction resolution deadline |
| **Time unknown** | barrier / knock-out trigger, liquidation at a known level                 | goal, red card, depeg, oracle deviation, exchange halt, expiry _outcome_      |

Each quadrant has a different correct response:

- **Time known + content known -> STAND ASIDE and reconcile.** There is nothing to reprice — the value change is
  already known. The exposure is **position and ledger reconciliation**, not price. Do not trade through a funding
  settlement or a staking payment; close the window, let the ledger settle, reopen.
- **Time known + content unknown -> PRE-ARM, then react to content.** Tighten the validity envelope, cut size or
  withdraw _before_ the event; after it, both paths run (below).
- **Time unknown + content known -> PRE-COMPUTE THE BRANCH.** The post-event state is derivable now, so compute it
  ahead and switch on trigger. This is the one place a per-branch snapshot earns its cost.
- **Time unknown + content unknown -> REACT ONLY.** A fast pull is usually the right default.

**One event, two consumers, different latencies — not two events.** A news release or a goal feeds BOTH the fast path
(defensive get-out-of-the-way, or aggressive entry where the archetype supports news/event trading) and the slow path
(features and ML digesting the content). Modelling these as separate events reintroduces double reaction.

**Venue mechanics can make the fast path moot.** Betfair freezes accounts around a goal, so the reaction budget there
is set by the venue, not by our latency. Check the venue's own behaviour before spending on speed.

### 2c. Suppression is not a kill

The action mask has **three** states, not two:

| State        | Meaning                                  | Release                                     |
| ------------ | ---------------------------------------- | ------------------------------------------- |
| `PERMITTED`  | normal, per source tier and confidence   | n/a                                         |
| `SUPPRESSED` | a **scheduled** window; nothing is wrong | reopens on schedule, no incident, no unkill |
| `KILLED`     | something is wrong; recovery required    | per the autonomous recovery matrix          |

Conflating a scheduled suppression with a kill produces false incidents and invents an un-kill path where none is
needed. The funding-settlement and staking-payment windows above are `SUPPRESSED`, never `KILLED`.

## 3. The common StateEnvelope

Every profile publishes absolute state through one envelope. The **payload** differs by profile; the envelope and its
invariants do not.

```
StateEnvelope {
  domain_id; bucket_id; profile_id; schema_generation; model_generation;
  state_epoch; state_sequence; correction_or_retraction_of;
  logical_position;                    # profile-specific ordering key, NOT a timestamp
  observed_at; received_at; received_in_region;
  effective_from; effective_until;     # bitemporal validity window
  account_scope;                       # HARD isolation boundary, not a filter
  completeness_mask; finality_state; quality_flags; uncertainty; action_mask;
  changed_factor_mask; absolute_state_payload;
}
```

**Invariants that hold in every profile:**

1. **Absolute state, never additive commands.** Newer replaces older; a duplicate or reordered packet is discarded on
   `(state_epoch, state_sequence)` lexicographic comparison. Consumers compute their own difference to their reference
   generation. This is what makes a provisional estimate and its later confirmation _one revision_, not two commands.
2. **`logical_position` is the ordering key and is profile-specific.** It is not a clock. Cross-venue data is never
   globally reordered by nominal exchange timestamp.
3. **Retraction is one operation, not three.** A chain reorg, a sports scoring correction and a voided market are the
   same envelope-level `correction_or_retraction_of` mechanism. Do not build a DeFi-specific reorg path.
4. **`received_in_region` is required**, because paper/batch equivalence is evaluated per region (see § 5).
5. **`account_scope` is a hard boundary.** Market state is not client-scoped; position state always is. See
   [/codex/04-architecture/client-funds-isolation.md](/codex/04-architecture/client-funds-isolation.md).
6. **Uncertainty travels with the mean.** A suspicious observation must be able to widen uncertainty _without_ moving
   the mean, so the action layer quotes less aggressively rather than confidently quoting wrong.

## 4. The valuation interface, and what is NOT universal

The interface is common:

```
D_i(t) = f_i( x(t), q(t), tau(t), c(t) ; M_i )
```

where `x` is canonical factor/belief state, `q` is position/exposure state, `tau` is the profile clock or phase, `c` is
execution context and `M_i` is the immutable model generation.

**The kernel behind `f_i` is profile-specific.** This scopes — and does not reverse — the factor-state ruling recorded
in the delta-proxy issue doc section 11:

| Profile            | Kernel                                                                                                     |
| ------------------ | ---------------------------------------------------------------------------------------------------------- |
| `continuous_quote` | `F_i = U_i0 + J_i.Dz + 0.5 Dz' H_i Dz + Theta_i.Dt + a_i0 + [A Dq]_i + c_i` (Jacobian/Hessian Taylor form) |
| `block_ledger`     | exact AMM reserve / tick-math simulation; a Taylor surrogate is valid ONLY inside a certified range        |
| `event_resolution` | finite-state transition model / posterior lookup; full recomputation after a material discrete event       |

**The universal invariant is "evaluate current absolute state against an immutable reference generation" — not
"delta/gamma everywhere."** Writing the Taylor form as if it were universal is the error this table exists to prevent.

### 4a. The adjustment matrix `A`

`A` is position-independent (ruled) but **not** market-independent — an option's delta moves with the underlying, and
inverse-contract risk per unit moves with price. Adopted form: **low-rank plus sparse diagonal**, `A ~= L R + D`, with a
small absolute risk-factor state `r` published on the hot lane so a fill costs a rank-1 update rather than a dense
column. `A` is fixed within a generation; its market-state drift is absorbed by the validity envelope forcing an earlier
refresh — a mechanism that has to exist anyway.

## 5. Four double-reaction barriers, generalised

The barriers are independent and all four are required. They generalise beyond tick data:

| Barrier                | Key                                                          | Prevents                                                                   |
| ---------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------- |
| 1. Exact transport     | packet/update sequence + connection epoch (+ **block hash**) | duplicate copies of one physical message                                   |
| 2. Semantic cause      | exchange event / trade / update linkage across state planes  | trade, BBO and depth — three consequences of ONE match — as three shocks   |
| 3. Economic innovation | residual vs current (or bounded fixed-lag) factor state      | a follower venue or late leader re-applying an already-absorbed move       |
| 4. Consumer state      | absolute state epoch + sequence                              | duplicate/reordered packets and provisional-then-confirmed double counting |

Barrier 2 is the one most often missing from a first design: a trade print, a BBO change and a depth update are usually
**one exchange event**, not three independent confirmations.

The plane progression by profile:

```
continuous_quote:  trade -> BBO -> depth -> recovery snapshot
block_ledger:      mempool observation -> included tx/log -> canonical block -> finality
event_resolution:  third-party play event -> scoreboard state -> official correction -> resolution
```

A later plane does not repeat the whole move. It contributes residual information, improves completeness, lowers
uncertainty, expands the action mask, confirms finality, or corrects/retracts an earlier cause.

> **The reorg trap.** Barrier 1 keyed on `tx_hash` alone will wrongly suppress the same transaction re-included under a
> different block hash. The dedup key MUST carry the block hash, and the retraction path MUST be able to un-apply —
> otherwise barrier 1 and reorg handling fight each other and the loser is silent.

## 6. Source tiers

Orthogonal to action permissions. Permissions say _what actions a source may authorise_; tiers say _what a source may
influence at all_.

| Tier | Meaning                                                 |
| ---- | ------------------------------------------------------- |
| 0    | may directly move actionable factor state               |
| 1    | confirmation, uncertainty reduction, defensive use only |
| 2    | recovery and fallback                                   |
| 3    | recording / research only                               |

Selection is by marginal decision value, semantics, health, cost and latency — never nominal message rate.

## 7. Component ownership

| Concern                                                          | Owner                                                      |
| ---------------------------------------------------------------- | ---------------------------------------------------------- |
| venue adapters, decode, book build, arbitration                  | market-tick-data-service                                   |
| local RX timestamp + region capture                              | market-tick-data-service (boundary)                        |
| slow generation: anchor `z_0`, loadings, covariance, vol, greeks | features-service (greeks-service folds in — see ruling R7) |
| fast nowcast `z_hat`, single-writer per (bucket, region)         | new component; NOT per-execution-process                   |
| valuation, adjustment matrix, credit                             | strategy-service                                           |
| quote actor, order-state diff, execution                         | execution-service                                          |
| venue manifest / capability declarations                         | unified-api-contracts (extend existing registry — see R10) |

**One logical factor state per bucket per region.** A per-execution-process estimator would give N disagreeing
estimates of one BTC — the same duplication already rejected for per-strategy fair value.

## 8. Cross-region delay estimator

Required, and a **second consumer of the RX-time capture**, not new instrumentation.

- **Never RTT/2.** WAN paths are asymmetric and the asymmetry is the quantity that matters.
- **The venue clock cancels; the regional clocks do not.** For one event seen in two regions,
  `(t_rx,A - t_ex) - (t_rx,B - t_ex) = t_rx,A - t_rx,B` — the venue's clock drops out exactly, however bad it is. A and
  B must still be comparable, so regional clock discipline is the floor, and any delay smaller than the clock
  uncertainty is reported as **indistinguishable**, never as a number.
- **Distribution, not mean**: p50/p90/p99/p99.9 per directed pair per path.
- Published as a versioned generation, consumed the same way loadings are.

Four consumers: the measurement-variance age penalty; the fixed-lag window bound (delay + uncertainty over budget ->
fall back to nowcast rather than block); WAN-partition detection; and **the topology decision itself** — if a region's
delay to a venue is 40ms and its local advantage is 2ms, a factor engine there earns nothing. That last one makes this
estimator a gate on the multi-region build.

## 9. Operator ruling register — 2026-08-20

| #   | Ruling                                                                                                                                              |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| R1  | One contract, three semantic profiles. Not one universal implementation; not CeFi-only.                                                             |
| R2  | Split slow/fast. features-service owns the slow generation; a single-writer component per (bucket, region) owns the fast nowcast.                   |
| R3  | Substrate-neutral binary contract; Python/cloud first, Rust-colo-ready. Fixed-layout versioned schema from day one, no JSON on the hot lane.        |
| R4  | Capture local RX time **and region** at the MTDS boundary; paper/batch equivalence becomes **per-region**, not global.                              |
| R5  | Finality-tiered state with explicit retraction; on-chain defence moves **pre-trade** (the action mask gates submission).                            |
| R6  | A discrete event-state change **invalidates the snapshot** rather than being a `Dz` move. Trust region reads "no discrete state change since z_0".  |
| R7  | **greeks-service folds into features-service** — one home for model coefficients, no cross-service generation protocol to fail open.                |
| R8  | `A ~= L R + D` low-rank; publish small absolute risk-factor state `r`; market-state drift governed by the trust region.                             |
| R9  | A cross-region delay estimator is required, with the properties in § 8.                                                                             |
| R10 | The venue manifest **extends the existing UAC capability registry**. No fourth parallel venue registry.                                             |
| R11 | Profile defaults for most manifest fields, but **mandatory explicit override on `finality_model` and `ordering_key`** — no default for those two.   |
| R12 | Performance tier is a **declared SLO + continuous measurement + divergence alert**, not a declaration alone.                                        |
| R13 | DeFi: `profile=block_ledger`, `delivered_tier=warm`, `hot_capability=specified-not-implemented-not-certified`. A programme-scope call, not a limit. |
| R14 | Semantic profile and performance tier are **orthogonal**. Profile bounds the achievable tier; it does not determine it.                             |
| R15 | The Taylor factor-state form is the **continuous-quote kernel**, not universal. The universal invariant is reference-generation evaluation.         |
| R16 | Retraction/correction is **one envelope operation** across all profiles. `logical_position` is the ordering key and is not a timestamp.             |

**R11's rationale is a measured failure shape, not a preference.** A miss path that returns a plausible default is
exactly `get_venue_asset_group()` returning `"cefi"` for every venue, MTDS dropping a `data_type` filter and returning
200, and three chain registries each giving a different answer — all filed 2026-08-19. `finality_model` and
`ordering_key` are the two fields where a wrong default is silently dangerous.

## 10. The kill switch and the action mask are ONE mechanism

`action_mask = {}` at instrument scope **is** a kill at instrument scope. Do not build these as two systems. The
kill-switch SSOT — arming authority, resume authority, exit playbooks, the recovery timeline — remains
[/codex/04-architecture/autonomous-recovery-matrix.md](/codex/04-architecture/autonomous-recovery-matrix.md); what is
recorded here is only the slow/fast decomposition, which is the same decomposition as everything else in this doc.

**Measured 2026-08-20 — the reaction path is well wired.**
`execution-service/execution_service/engine/kill_switch_bus_bridge.py` bridges the UTL `KillSwitchBus` into
execution-service's `engine.kill_switch`; `kill_switch.is_active()` gates every order path; `register_cancel_on_arm`
callbacks fire on the inactive->active transition so arming **cancels** rather than merely blocking new orders. Scopes
are typed (`GLOBAL / VENUE / CLIENT / STRATEGY / INSTRUMENT / ARCHETYPE`) with `ScopedKillSwitchSpec` /
`ScopedKillSwitchState` and a `KillSwitchTrigger` event in UAC.

**The four concerns and their cadences:**

| Concern                                                                   | Owner                 | Cadence                                             |
| ------------------------------------------------------------------------- | --------------------- | --------------------------------------------------- |
| **Declaration** — what counts as a kill condition, its scope, `exit_mode` | strategy / UAC config | slow, versioned generation                          |
| **Detection** — noticing the condition holds                              | **OPEN — see below**  | must be fast for the infrastructure class           |
| **Reaction** — cancel, gate, execute the exit playbook                    | execution-service     | fast, every order path                              |
| **Resume** — un-kill                                                      | recovery matrix       | direction- and scope-aware; `manual_unkill` = human |

**A slow strategy cadence does NOT make the kill slow.** Declaration is versioned config, not a per-tick decision, and
the exit playbooks live in UAC so execution-service can act with strategy-service entirely down.

**OPEN — detection ownership per condition.** Every kill-switch _subscriber_ found on 2026-08-20 is strategy-side
(`archetype_kill_switch_subscriber.py`, `pnl/kill_switch_bus_subscriber.py`, `risk/circuit_breaker_registry.py`); those
consume. Which component _detects_ each condition and publishes to the bus was **not measured**. If detection for a
given condition sits behind a slow loop, that condition is latent at that loop's cadence however fast the reaction is —
the same shape as `HealthFactorMonitor` having no production entry point. The conditions that cannot tolerate a slow
detector are the infrastructure class: feed staleness, sequence gap, position divergence, venue disconnect, clock
breach, ack timeout, model trust breach.

## 11. Dust — three concerns, three owners

Operator framing 2026-08-20, correct for two of the three parts:

| Concern            | What it is                                                                                          | Owner / cadence                                                                  |
| ------------------ | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **Dust policy**    | thresholds, sweep cadence, target currency                                                          | strategy config, slow, via instructions                                          |
| **Dust avoidance** | min-notional rounding; not leaving an unfillable stub after a partial fill or a tick-rounded resize | **execution, fast** — a property of the order-state diff, not of the instruction |
| **Dust sweeping**  | consolidating residual balances                                                                     | slow, and it is a **transfer** — so it can never cross a `client_id`             |

**Measured 2026-08-20**: the token `dust` appears in `strategy_service/pnl/engine/reward_attribution.py`,
`reward_attribution_drain.py`, `backtest_v2/action_handlers.py`, `benchmark_fills.py` and `strategies/v2/base.py` — it
is a PnL-attribution and backtest concern today. Whether **dust avoidance** is owned anywhere is UNVERIFIED: only the
token `dust` was searched, and min-notional / lot-size logic may exist under other names.

## 12. Not settled here

- The `hot`-tier `block_ledger` contract fields (mempool observation id, simulation state root, bundle sequence,
  relay/builder capability, gas-policy IO, inclusion/finality feedback) are to be **defined, not implemented** — R13.
- Position vectors: whether to adopt `q_confirmed` / `q_pricing` (fill-probability-weighted) / `q_worst`.
- Parts II-V of the restructured specification: the per-profile detail, archetype manifests and per-profile
  certification. Only Part I (this doc) exists.
- The five Wave-0 rulings tracked in the delta-proxy issue doc section 15.
- **Kill-switch detection ownership per condition** (section 10) — the reaction path is measured and wired; the
  detection path is not. This is the highest-value open item, because a slow detector makes a fast reaction irrelevant.
- **Dust avoidance ownership** (section 11) — hypothesis only; a single-token search is not a measurement.
- **Whether the fast nowcast component deploys colocated with MTDS and execution-service**, which is where the market
  feed already terminates.
- **The recovery plane** — checkpointing, per-channel recovery capability, scoped readiness as a capability vector,
  and batch/paper/live activation. Under measurement 2026-08-20; not yet ruled.
