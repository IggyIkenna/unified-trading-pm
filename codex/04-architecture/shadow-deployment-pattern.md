---
doc_type: codex-ssot
title: Shadow Deployment Pattern — Archetype Upgrades
summary:
  How a new archetype-engine build promotes from shadow to prod — per-archetype observation window, policy gates
  (dispersion/correlation/drawdown), PROMOTE/EXTEND/REJECT/ROLLBACK evaluator, and the two persistence sinks
  (ArchetypeBuildRegistry + PromotionDecisionLedger).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, strategy-service, unified-trading-library]
scope: [engineer, admin]
tags: [strategy, execution, verification, reconciliation, monitoring]
related:
  [
    /codex/04-architecture/artifact-versioning.md,
    /codex/04-architecture/schema-versioning.md,
    /codex/06-coding-standards/strategy-identity-versioning.md,
  ]
created: 2026-04-18
authoritative_for:
  [
    shadow deployment pattern for archetype-engine build promotion,
    ArchetypeBuildRegistry + PromotionDecisionLedger persistence,
  ]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/MIGRATION.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-uac-combo-rules.md,
    plans/epics/strategy_and_dart_master_SUPERSEDED_2026_05_21.md,
    plans/epics/strategy_master.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Shadow Deployment Pattern — Archetype Upgrades

> **What it is:** How we promote a new version of an archetype engine from shadow mode to production.
>
> **Where the code lives:** `strategy-service/engine/strategies/v2/shadow_deployment.py` — policy artifact, comparison
> metrics, evaluator, registry.

## Motivation

When we ship a new version of an archetype engine — say `ML_DIRECTIONAL_CONTINUOUS@build=2.0.0` upgrading to `2.1.0` —
we can't just cut traffic over. The production strategy instances built on top of the old engine are running live
capital; a behavioral regression in the new build could drift positions, breach risk gates, or mis-attribute P&L. The
shadow deployment pattern is how we de-risk every archetype upgrade through a structured observation window with defined
promotion gates.

The pattern is **per-archetype**, not per-strategy-instance — one promotion decision cuts over every production instance
of that archetype simultaneously, because the archetype is the code path they all share.

## Lifecycle

```
         ┌──────────────────────────────────────────────────────┐
         │  1. ship new archetype build → tagged "shadow"        │
         │     (prod instances keep running on the old build)    │
         └──────────────────────────────────────────────────────┘
                                  │
                                  ▼
         ┌──────────────────────────────────────────────────────┐
         │  2. V2EngineOrchestrator(shadow_mode=True) runs       │
         │     alongside prod for every production instance —    │
         │     same ticks, same features, same configs. Outputs  │
         │     go to a logging sink; no venue I/O.               │
         └──────────────────────────────────────────────────────┘
                                  │
                                  ▼
         ┌──────────────────────────────────────────────────────┐
         │  3. ShadowComparisonMetrics accumulate over the       │
         │     observation window (default: 14 days, tight       │
         │     archetypes 21 days).                              │
         └──────────────────────────────────────────────────────┘
                                  │
                                  ▼
         ┌──────────────────────────────────────────────────────┐
         │  4. evaluate_shadow_deployment(policy, metrics)       │
         │     returns PROMOTE / EXTEND / REJECT / ROLLBACK.     │
         │     Decision is persisted (policy content-hash + ts). │
         └──────────────────────────────────────────────────────┘
                                  │
                                  ▼
                         ┌────────┴────────┐
                         │                 │
                         ▼                 ▼
                   PROMOTE or EXTEND    REJECT or ROLLBACK
                   cutover at next      archive shadow build,
                   allocator tick       stay on prod (or revert
                                        if already promoted)
```

## The policy artifact

`ShadowDeploymentPolicy` is an immutable, content-hashed, versioned-per-archetype artifact. Defaults err conservative;
tight archetypes (market making, vol trading, liquidation capture, recursive staking) get stricter gates because
mis-promotion there carries inventory/atomicity risk that a broader archetype doesn't.

### Standard policy gates

| Gate                                 | Default | Tight archetypes |
| ------------------------------------ | ------- | ---------------- |
| `min_shadow_duration`                | 14 days | 21 days          |
| `min_shadow_trade_count`             | 100     | 500              |
| `max_pnl_dispersion_bps` (vs prod)   | 50 bps  | 25 bps           |
| `max_fill_dispersion_bps` (per fill) | 15 bps  | 8 bps            |
| `min_signal_correlation` (vs prod)   | 0.90    | 0.95             |
| `max_shadow_drawdown_bps`            | 300 bps | 150 bps          |
| `rollback_on_sum_equality_drift`     | true    | true             |
| `rollback_on_risk_gate_divergence`   | true    | true             |

**Tight archetypes** (auto-applied by `build_default_shadow_policy`): `MARKET_MAKING_CONTINUOUS`,
`MARKET_MAKING_EVENT_SETTLED`, `VOL_TRADING_OPTIONS`, `LIQUIDATION_CAPTURE`, `CARRY_RECURSIVE_STAKED`.

### Decision order (highest priority first)

1. **Rollback-trigger events** (sum-equality drift in PBMS, or risk-gate divergence vs prod) → `ROLLBACK` if the build
   was already promoted, else `REJECT`. These are hard fails that can't be overridden by other metrics looking good.
2. **Insufficient observation window OR trade count OR missing dispersion metrics** → `EXTEND`. The system is not saying
   the build is bad; it's saying there isn't enough data yet.
3. **Any dispersion / correlation / drawdown gate fails** → `REJECT`. Build doesn't match prod closely enough.
4. **All gates pass** → `PROMOTE`. Cutover happens at the next allocator tick.

## What the evaluator DOES NOT decide

- **Build quality below the gates.** If a shadow build fails promotion, it's archived but the archetype code isn't
  automatically rolled back in the repo. Human judgment decides whether to iterate or abandon.
- **Multi-stage ramps.** Some teams want "promote to 10% of instances, observe, then 100%." This module returns a single
  bool-like decision per archetype; staged rollouts are a deployment-service concern layered on top.
- **Cross-archetype correlation.** If two archetypes share a feature artifact and it goes bad, this module won't catch
  it — the artifact-versioning plumbing + PBMS sum-equality invariants do.

## Why "promote archetype-wide" not "promote per instance"

Every instance of `ML_DIRECTIONAL_CONTINUOUS` runs the same `on_tick` body — the only thing that varies is config.
Promoting per instance means running two archetype versions side-by-side across the firm's production mesh, which
doubles the surface area for cross-version bugs and makes P&L attribution ambiguous. Archetype-wide promotion is the
clean seam.

The counter-argument — "what if build 2.1.0 is great for strategy A but bad for strategy B?" — is handled by the
dispersion gates. If the shadow build causes even one production strategy instance to diverge beyond the cap, the
decision is REJECT regardless of how the other instances look.

## How this interacts with the plan

`plans/archive/strategy_architecture_v2_2026_04_17.plan.md` had "Shadow deployment pattern specifics for archetype
upgrades" as a TBD. This doc + `shadow_deployment.py` + the 16 unit tests close that item.

## Persistence

The evaluator is pure — it produces a `ShadowEvaluation` and returns it. Phase 2 of
`plans/archive/strategy_architecture_v2_finalization_2026_04_19.plan.md` adds the durable surfaces the decision needs to
land on so every PROMOTE / EXTEND / REJECT / ROLLBACK is auditable post-incident.

### Authoritative stores

There are exactly two persistence sinks. Anything else that wants to observe promotion activity subscribes to the UTL
events — it does not write its own parallel store.

1. **`ArchetypeBuildRegistry`** — in-process append-only history of `(archetype, build_version, status)` rows. SSOT for
   "what's PROD right now?" and "which build did we roll back from?". Source:
   `strategy-service/strategy_service/engine/strategies/v2/archetype_build_registry.py`.
2. **`PromotionDecisionLedger`** — GCS-backed JSONL, one file per `(archetype, build_version)` at
   `gs://{project}-strategy-artifacts/promotion-decisions/{archetype_id}/{build_version}.jsonl`. SSOT for "what did the
   evaluator decide, when, why?". One row per `evaluate_shadow_deployment()` call — EXTEND + REJECT history is kept
   alongside PROMOTE. Source: same module.

### Call graph

```
evaluate_shadow_deployment(policy, metrics, now, sink=make_ledger_sink(...))
                                                    │
                    ┌───────────────────────────────┘
                    ▼
       PromotionDecisionLedger.append  ──▶  GCS JSONL (one row per call, no overwrites)
                    │
                    └──▶  event_logger(ARCHETYPE_SHADOW_EVALUATED, …)

ArchetypeBuildRegistry.promote_to_prod / .rollback / .archive_build
     ──▶ emits ARCHETYPE_PROMOTED_TO_PROD / ARCHETYPE_ROLLED_BACK / ARCHETYPE_BUILD_ARCHIVED
```

### Schema

Each JSONL row is a self-describing, sort-key-stable JSON object:

```jsonc
{
  "evaluation_id": "f47c8a…", // uuid4 hex
  "archetype": "ML_DIRECTIONAL_CONTINUOUS",
  "build_version": 3,
  "evaluated_at_utc": "2026-04-19T12:34:56.789+00:00",
  "decision": "EXTEND", // PROMOTE | EXTEND | REJECT | ROLLBACK
  "reasons": ["window 7 days < required 14 days"],
  "policy_content_hash": "9f2c…", // 16-char sha256 prefix
  "window_observed_seconds": 604800.0,
  "metrics_snapshot": {/* optional ShadowComparisonMetrics serialisation */},
  "metadata": {/* caller-supplied free-form */},
}
```

### State machine

`ArchetypeBuild.status` takes one of four values:

| Status        | Meaning                                                                                       |
| ------------- | --------------------------------------------------------------------------------------------- |
| `SHADOW`      | build is live in shadow-mode, accumulating ShadowComparisonMetrics                            |
| `PROD`        | promoted; authoritative for production traffic                                                |
| `ARCHIVED`    | SHADOW build that never promoted (REJECTED or manually retired)                               |
| `ROLLED_BACK` | previously-PROD build that was reverted; rollback immediately re-PRODs `parent_build_version` |

Transitions are append-only — the table never mutates an existing row. A build that was SHADOW → PROD → ROLLED_BACK
appears as three rows, in that order.

### UTL events emitted

| Constant                     | Emit site                                          |
| ---------------------------- | -------------------------------------------------- |
| `ARCHETYPE_SHADOW_EVALUATED` | every `evaluate_shadow_deployment` call (via sink) |
| `ARCHETYPE_PROMOTED_TO_PROD` | `ArchetypeBuildRegistry.promote_to_prod`           |
| `ARCHETYPE_ROLLED_BACK`      | `ArchetypeBuildRegistry.rollback`                  |
| `ARCHETYPE_BUILD_ARCHIVED`   | `ArchetypeBuildRegistry.archive_build`             |

All four are registered in `unified_trading_library.events.STANDARD_LIFECYCLE_EVENTS` via
`unified-trading-library/unified_trading_library/events/event_types.py` — no bespoke event sink needed.

### Atomicity

Within one process the ledger serialises read-modify-write under an instance-level `threading.Lock`. **Cross-process
atomicity is not yet implemented** — the GCS path is eventually-consistent if two services append for the same
`(archetype, build_version)` at the same time. Today the `evaluate_shadow_deployment` caller is a single background task
per archetype, so this isn't a practical concern. When promotion runners become HA, move to generation-check CAS
(`If-Match` on the blob generation) — tracked as a follow-up in the Phase 2 plan item.

### What persistence DOES NOT do

- **Does not derive decisions.** The evaluator is authoritative; persistence just records what the evaluator said.
- **Does not retry.** A sink-write failure propagates; the caller decides whether the decision retry is safe.
- **Does not time-travel.** The ledger is append-only — to undo a recorded decision, record a new one that supersedes
  it.

## Cross-references

- Artifact versioning (the build numbers being promoted): [`artifact-versioning.md`](artifact-versioning.md)
- Schema versioning (distinct axis — don't confuse a schema bump with a code bump):
  [`schema-versioning.md`](schema-versioning.md)
- Strategy identity (archetype is one of the 5 layers):
  [`/codex/06-coding-standards/strategy-identity-versioning.md`](/codex/06-coding-standards/strategy-identity-versioning.md)
- PBMS sum-equality invariant (the rollback trigger):
  [`/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md`](/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md)
- Shadow allocator mode (related but different — `shadow_mode=True` on `ClientAllocatorInstance` emits directives that
  are observed but not acted on):
  [`/codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md`](/codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md)
