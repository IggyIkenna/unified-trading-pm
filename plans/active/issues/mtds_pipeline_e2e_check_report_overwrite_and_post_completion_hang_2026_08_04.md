---
doc_type: issue
title: >-
  market-tick-data-service's pipeline_e2e_check.py has two independent operational defects — a same-day report filename
  collision across separate leg invocations, and a confirmed-twice post-completion process hang
summary: >-
  Found live while executing `prediction_consolidated_native_ao_extract_2026_07_25.md`'s `data-pipeline-check-mtds`
  pre-Phase-B baseline checkpoint todo (2026-08-04). (1) **Report filename collision**: `report.write_report()` keys its
  output path only on `run_date` (`data_pipeline_e2e_check_mtds_<run_date>.md`/`.json`), not on `legs` — running the
  checker in 2 separate invocations for the same day (`--legs force,skip` then `--legs live`, the natural split when
  `--legs force,skip,live` in one call would be an even bigger single-shot VM-launch batch) makes the SECOND invocation
  silently OVERWRITE the FIRST invocation's report at the same path, losing its findings unless manually preserved
  before the second run. Confirmed live: Phase 1's real report (5 shards, 2 legs each, 4 genuine `no_parquet_under`
  failures) was fully overwritten by Phase 2's live-leg-only report before this session manually reconstructed a merged
  doc from captured output. (2) **Post-completion hang, confirmed TWICE independently** (once per phase of the same
  session): after `report.write_report()` completes and prints "wrote pipeline_e2e_check report to ..." with a real
  `Finished:` timestamp, and after confirming (`gcloud compute instances list`) that ZERO check-VMs remain running that
  the process would need to wait on or clean up, the `pipeline_e2e_check.py` process itself does NOT exit — it sits in
  uninterruptible-sleep (`D`) state with RSS climbing at ~465MB/30s (observed: ~3.4GB -> ~3.96GB in 30s on the first
  occurrence) and zero new log output. Both occurrences were terminated via `kill -TERM <exact captured PID>` (never a
  name-based pattern) once the report file's completeness was independently verified (both `.md` and sibling `.json`
  present, `Finished:` timestamp populated, byte counts matching a real write) — no data was lost either time, but an
  unattended/autonomous run of this checker (e.g. via `/autonomous` or a cron-scheduled invocation) would NOT
  self-recover from this and would hang indefinitely, eventually growing RSS on the shared host into the exact incident
  class RULES.md's memory-bounding HARD RULE exists to prevent (3 prior same-shape shared-host OOM incidents:
  2026-07-27, 2026-07-31, 2026-08-01).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags:
  [pipeline-e2e-check, data-pipeline-check-mtds, report-write, process-hang, memory-leak, shared-host, resource-cleanup]
related:
  [
    /plans/active/prediction_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-04"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
source: >-
  Discovered live while running the `data-pipeline-check-mtds --asset-group prediction` pre-Phase-B baseline checkpoint
  (slot 4, data_engineering, 2026-08-04). Report content preserved manually — see
  `plans/audit/results/data_pipeline_e2e_check_mtds_2026_08_02.md`'s provenance note.
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    market-tick-data-service/scripts/pipeline_e2e_check.py,
    /plans/active/prediction_consolidated_native_ao_extract_2026_07_25.md,
  ]
---

# pipeline_e2e_check.py report-overwrite + post-completion hang (2026-08-04)

## What I found

See summary above. Both defects are independently reproducible and were hit for real during a routine
`--asset-group prediction` pre-Phase-B baseline checkpoint run, not a contrived edge case — any operator or agent
running this checker in 2+ leg-scoped invocations on the same day, or relying on it to exit cleanly without manual
supervision, will hit one or both.

## Why it matters

The filename collision silently DESTROYS a real audit-result report (no error, no warning — the second write just
succeeds and clobbers the first), which is exactly the kind of silent data loss the workspace's
`check_evidence_backed_completion.py` / audit-result discipline exists to prevent for OTHER surfaces; this checker's own
report-write path isn't protected by it. The post-completion hang means this checker is NOT safe to run unattended
(autonomous loop, cron `schedule` skill invocation) without an external watchdog — it will consume climbing memory on
the shared host indefinitely once its actual work is done, which is the precise failure mode RULES.md's memory-bounding
guardrail was created to catch (3 prior real outages).

## Recommended decision

## Todos

- [x] ✅ [BACKEND] P2. **Fix the report filename collision** — `report.write_report()` (or its caller in
      `pipeline_e2e_check.py`) should key the output filename on `(run_date, legs)` — e.g.
      `data_pipeline_e2e_check_mtds_<run_date>_<legs_joined>.md` (`legs_joined` = e.g. `force_skip` / `live`) — or
      append/merge into the existing same-day report instead of overwriting it outright. Add a regression test that
      writes a report for `legs=[force,skip]` then `legs=[live]` on the same `run_date` and asserts BOTH reports'
      content is independently readable afterward (either via distinct paths or a verified merge, whichever fix
      direction is chosen). Repo: market-tick-data-service. — unified-trading-library@1bf3e7d1. Implemented the MERGE
      direction (not the filename-suffix direction) in
      `unified_trading_library/pipeline_e2e_check/report.py::write_report()` — it now merges into any pre-existing
      same-day report by `(shard_label, leg)` instead of overwriting it, keeping the existing filename convention
      (`{stem}.md`/`.json`, no legs suffix) that every plan/skill doc already references, so no doc drift. Regression
      coverage: `unified-trading-library/tests/unit/test_pipeline_e2e_check_report_merge_on_rewrite.py` (4 tests —
      two-invocation merge preserves both legs' results; same-leg re-run replaces its own cell without duplicating;
      no-prior-report path unchanged; malformed prior JSON tolerated, not fatal). Full `quality-gates.sh` green on both
      the commit and the quickmerge Pass-1 (sentinel `1bf3e7d12b5e8d10f5e0c95abc86c529663a2bd9`).
- [ ] [BACKEND] P2. **Root-cause and fix the post-completion hang.** After `write_report()` returns and all VM-related
      work is done (confirmed via `gcloud compute instances list` showing none of the run's check-VMs still exist), the
      `pipeline_e2e_check.py` process should exit promptly. Investigate: an un-joined/non-daemon thread (e.g. an SDK
      internal executor, a GCS/Pub/Sub client background thread, a logging handler with a live network connection)
      keeping the process alive; the climbing RSS with zero corresponding log output suggests something is actively
      buffering or retrying in a tight loop without emitting logs — check `google-cloud-storage`/`google-cloud-pubsub`
      client teardown, any `ThreadPoolExecutor`/`asyncio` event loop not explicitly closed, and whether the manifest
      consolidator or observability-event client opens a connection that's never closed. Add an explicit `sys.exit(0)`
      (or equivalent forced-exit) as a defensive backstop after the report-write completes if the true root cause proves
      hard to isolate quickly, but prefer fixing the actual leak/hang over papering over it. Repo:
      market-tick-data-service.
- [ ] [BACKEND] P3. **Add a wall-clock safety timeout** to `pipeline_e2e_check.py`'s own top-level `main()` (e.g. via
      `signal.alarm` or an external `timeout --kill-after=` wrapper documented in this skill's own usage instructions)
      so a future recurrence of either defect above self-terminates instead of hanging indefinitely when run unattended
      (`/autonomous`, `schedule` skill cron). This is a defense-in-depth backstop, not a substitute for the P2
      root-cause fixes above. Repo: market-tick-data-service.

## Progress Log

- **2026-08-04 (slot 4, data_engineering)**: filed while executing
  `prediction_consolidated_native_ao_extract_2026_07_25.md`'s `data-pipeline-check-mtds` pre-Phase-B baseline checkpoint
  todo. Manually reconstructed the lost Phase 1 report content into
  `plans/audit/results/data_pipeline_e2e_check_mtds_2026_08_02.md` before it could be lost for good; terminated both
  hang occurrences via exact-PID `SIGTERM`, no data loss, real VM cost from the extra Phase-2 re-run (session died
  mid-Phase-2 for an unrelated reason, required a fresh re-run) but bounded (`--test-run`, small VMs, ~90s duration cap
  each).
- **2026-08-04 (slot 13, backend_engineer)**: shipped todo 1's fix — unified-trading-library@1bf3e7d1. Chose the merge
  direction over the filename-suffix direction to avoid drifting the many plan/skill docs that hardcode the current
  `data_pipeline_e2e_check_mtds_<date>.md` filename. Todos 2 (post-completion hang root cause) and 3 (wall-clock safety
  timeout) remain open — separate backlog items, not touched by this fix.
