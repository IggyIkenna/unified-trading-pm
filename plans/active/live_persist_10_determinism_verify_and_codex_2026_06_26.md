---
title: Live-persist 10 — determinism verification (paper==batch-rerun) + lifecycle proof + codex SSOT
created: 2026-06-26
parent_epic: batch_live_symmetry_master
assigned_vm: human-planning
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2
priority: P2
status: done
locked_by: live-defi-rollout
locked_since: 2026-05-21
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

- [x] [VERIFY] P0. On the **basic test strategy**: run a paper week on the live spine, then batch-rerun the SAME week
      from cold GCS via the facade `read()` — assert `paper(W) == batch-rerun(W)` trade-for-trade (ε=0). Any diff = bug
      (non-determinism / input-capture gap / fill drift), not tolerance. Repo: e2e-testing (strategy-service QG). ✅
      e2e-testing@090b078 — `test_paper_equals_batch_rerun_trade_for_trade` passes (7-window candle spine, epsilon=0)
- [x] [VERIFY] P0. **Faithful-copy proof**: replay-from-cold == live-streamed bars for an overlapping window; and
      Pub/Sub-seek == warm GCS == BQ-view for that window (the three recent-tier reads agree). Repo: e2e-testing. ✅
      e2e-testing@090b078 — `test_faithful_copy_three_tier_read_agreement` passes (3 independent tier-reads agree)
- [x] [VERIFY] P1. **Lifecycle e2e on real GCS/BQ**: STREAM_ONLY cold never TTLs; REPRODUCIBLE cold TTLs per matrix. ✅
      e2e-testing@090b078 — `test_lifecycle_reproducible_vs_stream_only` + `test_sink_matrix_covers_all_52_shards`
- [x] [DOCS] P1. New codex SSOT `codex/02-data/live-data-persistence-and-event-log.md` (central log, pluggable
      service/GCS/table consumers, 2-tier GCS, retention classes, determinism). Add one-liner to CLAUDE.md
      `§ Live = batch`. Repo: unified-trading-pm. ✅ unified-trading-pm — codex SSOT written; CLAUDE.md one-liner added
- [x] [DOCS] P1. Archive the issue `issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md` (acked →
      shipped) and the parent plan + children per the plan-archival HARD RULE once all criteria are green. Repo:
      unified-trading-pm. ✅ unified-trading-pm — issue status→resolved; coordinator ARCHIVED banner added; locked_by
      cleared

## Success criteria

`paper(W)==batch-rerun(W)` green on the test strategy; faithful-copy + three-tier-read agreement proven; lifecycle
verified; codex SSOT written; issue + plans archived. **ALL GREEN.**

## Dependencies / unblocks

Deps: 04–09 (the full spine live). Unblocks: epic closeout (`batch_live_symmetry_master`).
