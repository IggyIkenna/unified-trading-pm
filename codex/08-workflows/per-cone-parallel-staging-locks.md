---
doc_type: codex-ssot
title: Per-cone parallel staging locks — design
summary: >-
  Design doc (no implementation) to replace the global `staging_status.locked` boolean with per-dependency-cone locks,
  so independent T3+ cones can run SIT concurrently while a T0/T1-base breaking change still serialises the whole fleet.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, client-reporting-api, deployment-api, deployment-service, deployment-ui, execution-service]
scope: [engineer]
tags: [ci-cd, quality-gates, refactor, dependency-management, orchestrator]
related: [./ci-cd-flow.md, ./dependency-cascade.md, /codex/04-architecture/tier-and-import-architecture.md]
created: 2026-06-27
authoritative_for: [per-cone parallel staging-lock design (cone_locks map + T0-base-exclusive SIT parallelism rules)]
referenced_by:
owner:
last_reviewed:
code_refs:
---

# Per-cone parallel staging locks — design

> **Status: DESIGN DOC** — no implementation in this plan. Captures the intent so the implementation plan can reference
> a stable SSOT.
>
> **Source:** `plans/active/cicd_workflow_sprawl_consolidation_2026_06_27.md` Task P2.

## Problem

The current staging lock (`workspace-manifest.json::staging_status.locked`) is a **global boolean**: ONE slot in the
entire fleet can run SIT at a time. When a SIT run is in progress, every other repo's LDR→staging promotion blocks until
the lock clears.

This serialises promotions that are **completely independent at the dependency level**. For example: a
`market-tick-data-service` (T3, no shared consumers) and a `unified-api-contracts` (T0, shared by everyone) can have a
breaking change in each simultaneously. Under the current design they must queue behind each other's SIT run even though
their consumers are disjoint.

## Concept: dependency cones

A **dependency cone** is the transitive closure of a package and its dependents:

```
UAC (T0) → UTL (T1) → MTDS (T3), features-service (T3), ml-service (T3), …
                     → execution-service (T4)
market-tick-data-service (T3, isolated) — shares only UTL/UAC at the base
```

Two cones are **independent** when their non-base members are disjoint (i.e. no repo in cone A is a consumer of any repo
in cone B). Independent cones can run SIT concurrently without interfering.

## Proposed design: per-cone locks

Replace the single `staging_status.locked` boolean with a **lock map**
`staging_status.cone_locks: {cone_id: {locked, locked_since, locked_reason, pending_repos}}`.

```json
{
  "staging_status": {
    "cone_locks": {
      "T0-UAC": {
        "locked": true,
        "locked_since": "2026-06-27T10:00:00Z",
        "locked_reason": "SIT running",
        "pending_repos": ["unified-api-contracts", "unified-trading-library"]
      },
      "T3-MTDS": {
        "locked": false
      }
    }
  }
}
```

A repo's promotion is blocked only if **its cone's lock** is held, not any other cone's lock.

## Cone assignment

Cones map to the `tier_and_import_architecture.md` tiers, **split at T3** where independent service families exist:

| cone_id        | members                                                                       |
| -------------- | ----------------------------------------------------------------------------- |
| `T0-T1-base`   | `unified-api-contracts`, `unified-trading-library`                            |
| `T2-cloud`     | `unified-cloud-interface`                                                     |
| `T3-MTDS`      | `market-tick-data-service`, `market-data-processing-service`                  |
| `T3-exec`      | `execution-service`                                                           |
| `T3-features`  | `features-service`, `greeks-service`                                          |
| `T3-strategy`  | `strategy-service`, `trading-agent-service`, `ml-service`                     |
| `T3-infra`     | `deployment-service`, `deployment-api`, `deployment-ui`, `agent-orchestrator` |
| `T3-reporting` | `fund-administration-service`, `client-reporting-api`                         |
| `T4-sit`       | `system-integration-tests` (cross-cone, always runs last)                     |

Cone assignment lives in `workspace-manifest.json::repositories[repo].cone_id` (a new field, operator-maintained,
defaults to `T0-T1-base` to be safe if unset).

## SIT parallelism rules

1. **T0-T1-base lock is exclusive**: when the base tier has a breaking change in SIT, ALL other cones must wait — every
   service depends on `unified-api-contracts` / `unified-trading-library`. The per-cone optimisation is most valuable
   for T3+ cones.
2. **Non-base cones run concurrently**: a `T3-MTDS` SIT and a `T3-exec` SIT may proceed simultaneously, each with their
   own lock.
3. **system-integration-tests cross-cone suite fires ONCE after all per-cone SITs pass**, using the existing
   `full-workspace-sit` dispatch (the current model). Per-cone SIT is a new _fast_ validation layer added BEFORE the
   full SIT, not replacing it.
4. **Retry/starvation logic is per-cone**: each cone's lock has its own `sit_retry_count` and `locked_alert_sent` flags.

## sit-debounce-trigger changes (implementation sketch)

- Read `breaking_pending` per repo → derive its `cone_id` → check THAT cone's lock.
- Dispatch per-cone SIT event to `system-integration-tests` with a `cone_id` payload field.
- `system-integration-tests` already slices the full-workspace SIT by smoke groups; adding a cone-scoped slice is
  additive to the existing `smoke-test-gate.yml` matrix.

## sit-starvation-detector changes (implementation sketch)

- Starvation check must iterate `cone_locks` instead of a single `locked` flag.
- A cone lock stale >25 min triggers remediation for THAT cone only.

## sit-unlock changes (implementation sketch)

- `sit-unlock.yml` accepts an optional `cone_id` input.
- If `cone_id` is provided: clears only that cone's lock.
- If omitted (legacy path): clears the global lock (backward compat while migration is in flight).

## Implementation prerequisites

Before implementing per-cone locks:

1. **Cone assignment audit** — every repo in `workspace-manifest.json::repositories` needs a `cone_id` field; default to
   `T0-T1-base` for safety, then reassign.
2. **system-integration-tests cone slice** — the SIT harness must accept a `cone_id` payload and run only that cone's
   integration tests (not the full workspace suite) for the fast tier.
3. **Manifest schema version bump** — `workspace-manifest.json` schema_version from v9 to v10, with the `cone_locks`
   map; old readers of `staging_status.locked` must still work (read `cone_locks["T0-T1-base"].locked` as the
   global-equivalent fallback).
4. **Operator decision gate**: a breaking T0 change still triggers a full global lock by design (rule 1 above); confirm
   this is acceptable before implementation starts.

## Success criteria (for future implementation plan)

- Two independent T3 cones can SIT concurrently with no deadlock.
- A T0 breaking change still serialises the whole fleet (safety preserved).
- `sit-debounce-trigger.yml` routes each pending repo to its cone's lock slot.
- Starvation detection and retry logic work per-cone.
- Manifest schema-version is bumped; old readers fallback cleanly.
- Rollout is behind a `PERCONE_LOCKS_ENABLED` manifest flag (off by default; flip to enable).
