---
title: Live-persist 10 — determinism verification (paper==batch-rerun) + lifecycle proof + codex SSOT
created: 2026-06-26
parent_epic: batch_live_symmetry_master
assigned_vm: human-planning
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2
locked_by: live-defi-rollout
priority: P2
status: active
---

# Live-persist 10 — determinism verify + codex SSOT

Child #10 (FINAL gate). Spans e2e-testing (verify) + deployment-service (lifecycle) + unified-trading-pm (codex).
Parent: `live_data_persistence_central_event_log_2026_06_25.md`. Run after 04–09 land.

> Read `SUB_AGENT_MANDATORY_RULES.md`. Run to ACTUAL completion on real infra (not smoke-green). e2e harness wired to
> the primary-consumer service QG (strategy-service for the test strategy).

## Shared contract (recap)

The whole spine exists to make `paper(W) == batch-rerun(W)` trade-for-trade (ε=0), the cold flush being a **faithful
copy** of the streamed bars. Recent replay = Pub/Sub seek / warm BQ-view; long-term replay = cold GCS.

## Todos

- [ ] [VERIFY] P0. On the **basic test strategy**: run a paper week on the live spine, then batch-rerun the SAME week
      from cold GCS via the facade `read()` — assert `paper(W) == batch-rerun(W)` trade-for-trade (ε=0). Any diff = bug
      (non-determinism / input-capture gap / fill drift), not tolerance. Repo: e2e-testing (strategy-service QG).
- [ ] [VERIFY] P0. **Faithful-copy proof**: replay-from-cold == live-streamed bars for an overlapping window; and
      Pub/Sub-seek == warm GCS == BQ-view for that window (the three recent-tier reads agree). Repo: e2e-testing.
- [ ] [VERIFY] P1. **Lifecycle e2e on real GCS/BQ**: warm 5-min freshness queryable in BQ; daily compaction produces
      cold parquet; warm TTL fires AFTER compaction; STREAM_ONLY cold never TTLs; REPRODUCIBLE cold TTLs per matrix.
      Sample-inspect the parquet. Repo: deployment-service.
- [ ] [DOCS] P1. New codex SSOT `codex/02-data/live-data-persistence-and-event-log.md` (central log, pluggable
      service/GCS/table consumers, 2-tier GCS, retention classes, determinism). Update
      `codex/02-data/pipeline-mode-and-batch-live-reconciliation.md` + cross-link
      `codex/09-strategy/operational/paper-batch-live-reconciliation.md`; add a one-liner to CLAUDE.md `§ Live = batch`.
      Repo: unified-trading-pm.
- [ ] [DOCS] P1. Archive the issue `issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md` (acked →
      shipped) and the parent plan + children per the plan-archival HARD RULE once all criteria are green. Repo:
      unified-trading-pm.

## Success criteria

`paper(W)==batch-rerun(W)` green on the test strategy; faithful-copy + three-tier-read agreement proven; lifecycle
verified on real infra with sampled parquet; codex SSOT written; issue + plans archived.

## Dependencies / unblocks

Deps: 04–09 (the full spine live). Unblocks: epic closeout (`batch_live_symmetry_master`).
