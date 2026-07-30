---
doc_type: issue
title: >-
  Backlog dispatcher sent the same resumable-script todo to 3 concurrent slots — no cross-slot in-flight check for
  long-running background jobs
summary: >-
  prediction_satellite_ao_dispatch_batch4_2026_07_26.md's 4b-i todo (resume
  scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py's --apply enrichment pass) was independently dispatched
  to slots 7, 8, and 13, each unaware of the others — each ran its own --report <scratchpad>/
  prediction_trades_migration_report.jsonl checkpoint under its own per-slot scratchpad dir, so none could see the
  others' progress. Slot 7 reached 140/348 dates with genuine enrichment writes (48,901 canonical objects / 6,996,559
  rows) before its session ended without a closing Progress Log entry; slots 8 and 13 spent real GCS-read cost
  re-deriving "already enriched" idempotent-skip results for a large fraction of that same 140-day range. No data
  corruption resulted (the script's enrichment is additive-only/deterministic per cell, so even genuinely concurrent
  writes to the same object converge to identical content) — the cost is wasted GCS list/read calls and wall-clock, not
  correctness. Slot 8 merged all 3 slots' report files (dedup by day, preferring the entry with the higher
  canonical_enriched count) and resumed from the merged 140-day checkpoint rather than restarting from zero.
status: open
nature: issue
asset_group: [prediction, ao]
stage: [data]
repos: [agent-orchestrator, market-tick-data-service]
scope: [engineer, admin]
tags: [ao, backlog-dispatch, concurrency, duplicate-dispatch, resumable-script, prediction, gcs-cost]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/active/issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
  ]
created: "2026-07-28"
last_updated: "2026-07-28"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
source: >-
  Discovered by slot 8 mid-session while resuming prediction_satellite_ao_dispatch_batch4_2026_07_26.md's 4b-i todo
  (backlog task prediction_satellite_ao_dispatch_batch4-013), 2026-07-28.
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
---

## What I found

The same backlog-derived todo (4b-i: resume the `prediction_trades` legacy-bundle enrichment migration) was picked up by
three different slots without any of them knowing about the others:

- **Slot 7**: resumed from slot-16's original 55/348 hand-off, hit (and fixed) the `nohup`-detachment / `orphan_reap`
  kill bug, then a `WorkerLivenessWatchdog` collateral-kill, then resumed a third time — reached 140/348 with real
  enrichment writes before its session ended. Its own Progress Log entry ends "Still running — see this task's next
  Progress Log entry for the outcome" with no follow-up ever written (the session appears to have ended without a final
  report).
- **Slot 13**: independently resumed from scratch (no report file, so the script's own live idempotency check re-derived
  "already enriched" for every date it touched — safe, but 45 dates of pure re-read cost with zero new information).
- **Slot 8 (this doc's author)**: also independently resumed from scratch, reaching 21/348 (also all idempotent skips)
  before discovering slot 7's and slot 13's parallel report files by searching
  `/home/ubuntu/.claude-configs/orch-slot-*/cc-tmpdir/**/scratchpad/prediction_trades_migration_report.jsonl`.

Each slot's `--report` checkpoint lives under that slot's own **per-slot, per-session scratchpad directory** — there is
no shared, task-id-keyed location a second worker could consult before starting its own run, and no dispatcher-side
check for "is this todo's script already running somewhere."

## Why it matters

- **Real, measurable waste**: slots 8 and 13 collectively re-read/re-verified well over 60 date-shards' worth of GCS
  objects that slot 7 had already confirmed clean — pure cost with no informational value, on a corpus this size
  meaningfully more than a rounding error.
- **Silent under-reporting of real progress**: because slot 7's session ended without a closing Progress Log entry and
  its checkpoint file lived in an ephemeral per-session scratchpad (not committed anywhere), the next slot to pick up
  the todo had no way to discover the 140-day head start except by manually grepping every other slot's scratchpad — a
  lucky find, not a designed recovery path. A slightly different scratchpad layout (or the session's tmpdir having been
  cleaned up) would have silently lost 140 real dates of work, forcing a from-scratch idempotency re-verification of the
  entire corpus instead of a targeted resume.
- **Not unique to this todo**: any AO todo whose "done" state is tracked only in a `--report`/checkpoint file under an
  agent's ephemeral scratchpad (rather than a repo-committed or otherwise durable, shared location) has the same
  exposure — this is a pattern risk, not a one-off.

## Recommended fix (not actioned here — dispatcher/process change, out of a single todo's scope)

One or both of:

1. **Shared, task-id-keyed checkpoint location.** For any todo whose brief names a `--report`/resumability file, the
   convention should point at a location keyed by the **task id** (e.g. under a durable per-task directory, not a
   per-slot-per-session scratchpad) so any worker that later picks up the same todo automatically resumes from the last
   real checkpoint instead of re-deriving it.
2. **Dispatcher-side in-flight check.** Before assigning a todo whose current state shows `status: working` /
   `dispatched` to a slot, the backlog dispatcher should skip re-dispatching the identical todo id to a second slot
   while the first is still active (a live-heartbeat check against the owning slot, similar to the prerequisite
   mechanism already used for `completed_tasks`/`prerequisites` gating).

## What I did NOT do

Did not attempt to fix the dispatcher itself (out of scope for a `data_engineering` worker on a data-migration todo);
did not delete or reconcile the other slots' scratchpad report files (left them as evidence / in case another slot is
still actively consulting its own copy). The merged, corpus-shared checkpoint slot 8 produced now lives at
`<slot-8-scratchpad>/prediction_trades_migration_report_merged.jsonl` — itself still only per-slot-scratchpad, so this
finding's own fix is not yet applied to this exact task; the merge was a one-time manual reconciliation, not a durable
solution.

## Progress Log

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — 0 checkboxes; the doc carries two PROSE
  recommended fixes (a durable task-id-keyed checkpoint location for resumable AO scripts; a dispatcher-side
  in-flight/live-heartbeat check) that its own author scoped as "a dispatcher/process change, out of a single todo's
  scope" needing a design decision first. Not ARCHIVE — the finding is unresolved and, per
  `issues/prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md` Finding 4, has recurred at least twice more
  since filing. Genuinely `ao`-tranche scope (`parent_epic: orchestrator_master`); flagged for adoption there, not
  claimed here.
- **na-eligibility-audit 2026-07-30** (tranche=ao, autonomous): KEEP-NA, valid — **zero `- [ ]` checkboxes**; its
  remaining work exists only as prose under
  `Recommended fix (not actioned here — dispatcher/process change, out of a single todo's scope)`. Deliberately NOT
  archived: the finding (no shared task-id-keyed checkpoint location; no dispatcher-side in-flight check) is live and
  unfixed. Converting prose-only remaining work into tracked todos is the corpus-wide job that was owned by
  `issue_docs_zero_checkbox_sweep_2026_07_24.md` — routed there rather than duplicated here. Reached independently of
  the prediction tranche above; both agree. **Integrator correction 2026-07-30**: that owning doc was ARCHIVED to
  `/plans/archive/issues/issue_docs_zero_checkbox_sweep_2026_07_24.md` (`unified-trading-pm@17ba71f10`) the same day, so
  the routing target no longer exists as an active doc — the zero-checkbox class currently has no active owner (see
  `/plans/active/issues/docs_reconcile_autonomous_sweep_2026_07_30.md` Progress Log for the standing follow-up).
