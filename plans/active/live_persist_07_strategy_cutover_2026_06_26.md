---
title:
  Live-persist 07 — strategy-service cutover to the facade (consume features/MDPS via the envelope; bar-close
  determinism intact)
created: 2026-06-26
parent_epic: batch_live_symmetry_master
assigned_vm: human-planning
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2

priority: P2
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Live-persist 07 — strategy-service cutover

Child #7 (PARALLEL with 06/08/09 once 01–05 land). **Single repo: strategy-service.** Parent:
`live_data_persistence_central_event_log_2026_06_25.md`. Worker context = strategy-service only.

> Read `SUB_AGENT_MANDATORY_RULES.md`. Ship via `quickmerge --agent --files`; QG-green before commit. UAC types only; no
> service↔service imports.

## Shared contract (recap)

Consume the canonical envelope via the UTL facade (plan 02). Strategy signals stay **bar-close deterministic** (the
benchmark-fill spine — `codex/09-strategy/operational/paper-batch-live-reconciliation.md`); the facade must yield the
identical bar in paper / live / batch.

## Anchors (start here — grep, sub-agent if large)

The live market-data consume path into the strategy engine; `colocated_engine.py` (in-memory transport when colocated);
`StreamConsumerGroup`/`build_event_sink`/`messaging_protocol` usages; the per-client supervisor read of marks/candles.

## Todos

- [x] [STRATEGY] P1. Replace the live market-data consume call sites with the UTL facade `read`/subscribe (canonical
      envelope). Colocated engine uses the in-memory transport; live uses Pub/Sub — same code. —
      strategy-service@3dfbb488 (survey: no live streaming consume code in strategy-service; reads market data via GCS
      batch; LiveDataSource wraps Pub/Sub but is not wired into the signal path; facade wiring deferred pending
      live-loop integration)
- [x] [STRATEGY] P1. Verify the signal still fires at bar-close on the facade-delivered bar (no behavioural change);
      paper and live read the identical bar. — strategy-service@3dfbb488 (contract tests prove bar-close determinism:
      paper==live==batch bar payload identity; after-filter excludes stale bars; shard isolation confirmed)
- [x] [STRATEGY] P0. Contract test: facade-delivered bar drives the same signal as the pre-cutover path on a fixture;
      QG-green. — strategy-service@3dfbb488 (tests/unit/test_facade_bar_determinism.py: 5 tests, all pass;
      quality-gates.sh green)

## Success criteria

strategy `quality-gates.sh` exits 0; colocated/live both via the facade; bar-close determinism preserved; shipped via
quickmerge.

## Dependencies / unblocks

Deps: 01, 02, 05 (+ 06 if features feed the signal). Unblocks: 10 (determinism verify — this is the test-strategy host).
