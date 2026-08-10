---
doc_type: issue
title: >-
  audit-false-done re-run 2026-08-10: audit STILL exits 1 — 16 false_done rows (up from 14), 1,528 unresolved plan_refs
  (up from 1,013) — recurrence of the parent doc's triaged breach, 2 rows overlap the triaged set
summary: >-
  Re-run of `scripts/orchestrator/audit_false_done.py` (the
  `ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08_finalize_2026_08_08.md` todo 1) against the LIVE
  `state.db` on 2026-08-10 ~16:20Z: the audit does NOT exit 0 — it finds **16 `false_done` rows** (parent doc had 14 at
  2026-08-08 triage), **914 honest**, **11 unauditable** (`brief_hash` NULL), **1,528 unresolved** (plan_ref did not
  resolve at `origin/live-defi-rollout` — up from 1,013). There is NO `SuccessExitStatus=1` in
  `audit-false-done.service`, so exit 1 = genuine breach, not a configured-soft exit. Two of the 16
  (`defi_cefi_venue_chain_axis_contamination-011` now `done_sha=no-code:gate-still-unmet-verified`,
  `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed-025` now `done_sha=0e9185d2c`) are the same
  task stems the parent doc's triage already FLIP-verdict'd — the breach RECURRED on them (reopened + re-done without
  the checkbox flipping). The other 14 are NEW false-done rows not in the parent doc's triaged set. The finalize plan's
  premise ("confirm audit exits 0 before archiving the parent doc") is NOT met — do NOT archive the parent doc until the
  16 rows are triaged to a genuinely clean audit.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, backlog, false-done, audit, commit-push-flip, plan-hygiene, state-db, recurrence]
related:
  [
    /plans/active/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08_finalize_2026_08_08.md,
    /plans/active/issues/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md,
    /plans/archive/issues/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
author: ikennaigboaka [slot-22]
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
source: >-
  Live audit re-run for `ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08_finalize_2026_08_08.md` todo 1
  (slot 22 dispatch, task `-28aa3f5fc829`, 2026-08-10).
---

# audit-false-done 2026-08-10 re-run: still 16 false_done (up from 14), 1,528 unresolved (up from 1,013)

## What I found

Re-ran `scripts/orchestrator/audit_false_done.py` against the LIVE DB
(`/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/state.db`, 306MB, the file the running
orchestrator process holds open) reading plans at `origin/live-defi-rollout` (NOT the working tree). Fresh run,
2026-08-10 ~16:20Z:

```
plans read at : origin/live-defi-rollout @ 24e4c1753f   (NOT the working tree)
done rows with a plan_ref: 2469
  false_done  : 16   <- reopen via POST /api/backlog/{id}/reopen
  honest      : 914
  UNAUDITABLE : 11   (brief_hash NULL — unknown, NOT clean)
  unresolved  : 1528  (plan_ref did not resolve at origin/live-defi-rollout)
exit code: 1
```

The `audit-false-done.service` unit has NO `SuccessExitStatus=1` (checked the unit file directly) — exit 1 is the
genuine-breach signal per the parent doc's own contract ("the unit exiting 1 on a genuine breach is correct behavior").
The audit is therefore genuinely RED and the finalize plan's done-gate ("confirm audit exits 0 ... before archiving") is
NOT satisfied.

**16 false_done rows** (task_id / done_sha / the todo line that is still `- [ ]`):

| #   | task_id                                                                             | done_sha                            | todo still `- [ ]` (first line)                                                           |
| --- | ----------------------------------------------------------------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------- |
| 1   | `honest_coverage_smoke_harness_4ag_verify-001`                                      | `1ca3672`                           | `[VERIFY] P2. BLOCKED-PREREQUISITES (2026-07-06, slot-6 planning — BOUNCE #4). Once P…`   |
| 2   | `defi_cefi_venue_chain_axis_contamination-011`                                      | `no-code:gate-still-unmet-verified` | `[DATA] P1. NEW 2026-08-04. Once…`                                                        |
| 3   | `defi_cefi_venue_chain_axis_contamination-783eda8294a7`                             | `d3586664c7`                        | `[DATA] P1. NEW 2026-08-04 (operator ruling, interactive session) — supersedes the "no-…` |
| 4   | `ao_scheduled_job_reserve_and_staggering-52320045f29c`                              | `2b628cd30f`                        | `[DATA] P2. Mid-run session death may NOT be fully closed…`                               |
| 5   | `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed-025`         | `0e9185d2c`                         | `[DATA] P1. Round-8 ACTUAL LAUNCH — all 8 shards… **Gated on pr…`                         |
| 6   | `sports_taxonomy_p3_consumers-cf4d5df0dd61`                                         | `8af9324`                           | `[CODE] P0. Add BOTH T-2h and T-6h as MODEL horizons…`                                    |
| 7   | `cefi_satellite_ao_dispatch_batch13-2646b6a5a2fb`                                   | `7b6331f4b`                         | `[SCRIPT] P2. Wire depth_of_book_10 into the CeFi live event-log capture…`                |
| 8   | `prediction_satellite_ao_dispatch_batch6-a878572ff8da`                              | `953188e730`                        | `[BACKEND] P2. Two-sided Betfair odds — persist back+lay…`                                |
| 9   | `tradfi_year_shard_backfill_launcher_missing_source_self_deletes-29a9ae419060`      | `9768ac81a`                         | `[DATA] P2. Once the next ES_OPT launch happens post-e2-highmem-4 fix…`                   |
| 10  | `defi_satellite_ao_dispatch_batch11-4a44d70c8936`                                   | `107e1f18c`                         | `[SCRIPT] P1. Migrate + purge the historical SUSHISWAP-ARBITRUM GCS objects/manifest…`    |
| 11  | `sports_fixtures_object_wrong_schema_instrument_catalog_contamination-a1f0ce98de8b` | `1fffacce40`                        | `[DATA] P1. Enumerate the full scope of schema-mismatched objects…`                       |
| 12  | `defi_risk_params_cron_job_fleet_wide_zero_rows-446c87badf4c`                       | `b5a92312`                          | `[DATA] P0. Diagnose the Cloud Run Job uts-prod-mtds-collect-risk-params…`                |
| 13  | `sports_all_vendor_honest_coverage_convergence-9e96b5aa58cd`                        | `68b711c29d`                        | `[SCRIPT] P1. Odds_api gap-backfill campaign — babysit the mtds-backfill-odds-* fleet…`   |
| 14  | `anthropic_per_task_actual_spend_and_account_calibration-8c5e32b30bff`              | `5516a0a`                           | `[BACKEND] P0. Build a slot-to-account-over-time attribution map…`                        |
| 15  | `anthropic_per_task_actual_spend_and_account_calibration-a395363eaf64`              | `ff2f1c5`                           | `[BACKEND] P0. Add a globally message.id-deduped transcript walker…`                      |
| 16  | `anthropic_per_task_actual_spend_and_account_calibration-17fdbb6d42c1`              | `ce3389fbe9`                        | `[BACKEND] P0. TIME-CRITICAL — start snapshotting the account usage meters…`              |

Key observations:

1. **Recurrence on 2 triaged rows.** `defi_cefi_venue_chain_axis_contamination-011` was FLIP-verdict'd in the parent doc
   at 2026-08-08 (`done_sha=45b5112e7` at audit time); the LIVE row is now `status=done`,
   `done_sha=no-code:gate-still-unmet-verified` — a NEWER false-done (reopened and re-done with a gate-shaped done_sha,
   checkbox still `- [ ]`). Same for `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed-025` (parent
   triaged it; live row is `done` with `done_sha=0e9185d2c`, checkbox still `- [ ]`). The fix the parent doc applied did
   not hold on these two.
2. **14 NEW rows** not in the parent doc's triaged set — false-dones created after the parent triage (the fleet kept
   dispatching and marking rows `done` without flipping the checkbox).
   `sports_all_vendor_honest_coverage_convergence-9e96b5aa58cd` is notably the odds_api gap-backfill babysit todo
   (checkbox `- [ ]` in the live tracker doc, row `done`) — a live, ongoing backfill marked done in the backlog.
3. **1,528 unresolved plan_refs** (up from the parent doc's 1,013). The parent doc's "characterise the 1,013" todo is
   flipped `[x]`, but the count GREW by ~515. Likely same expected explanation (rows pointing at since-archived plans),
   but the growth means the characterisation is now stale and the count is larger than what was bound.

## Why it matters

The parent doc's `ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08_finalize_2026_08_08.md` finalize plan
is gated on this exact audit being clean ("confirm audit exits 0 with no new false-done rows introduced by the triage
itself, before archiving"). It is NOT clean: the audit still exits 1, the false_done count went UP (14→16), and two
triaged rows recurred. Archiving the parent doc now would archive a false-clean signal and leave 16 gate-opening false
completions live (`gate_on_depends` trusts backlog `done` over the plan checkbox — exactly the failure class that
dispatched `sports_travel_calculator-001` 38 times). These 16 must be reopened/triaged FIRST.

## Recommended decision

1. Reopen each of the 16 false-done rows via `POST /api/backlog/{id}/reopen` (or the row's plan checkbox flip, if the
   work genuinely completed) — per-row verdict, mirroring the parent doc's REOPEN-or-FLIP discipline.
2. Re-run the audit after the triage to confirm exit 0.
3. Re-characterise the unresolved 1,528 (parent's 1,013 characterisation is now stale).

## Todos

- [ ] [BACKEND] P0. **Reopen or FLIP all 16 false-done rows listed above** (repo: agent-orchestrator,
      `POST /api/backlog/{id}/reopen` for each, or verify+flip the plan checkbox where the work genuinely completed;
      priority P0 for the 3 `anthropic_per_task_actual_spend_and_account_calibration` P0-shaped rows +
      `defi_risk_params_cron_job_fleet_wide_zero_rows-446c87badf4c`). **Done when**: audit re-run exits 0.
- [ ] [BACKEND] P1. **Re-characterise the 1,528 `unresolved` rows** (up from 1,013) — confirm the growth is still
      expected (rows whose plan_ref points at since-archived plans) and no NEW non-archived referents are being dropped.
      **Done when**: a fresh unresolved-count breakdown by category is recorded.
- [ ] [BACKEND] P2. **Root-cause why 2 triaged rows recurred** (`defi_cefi_venue_chain_axis_contamination-011`,
      `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed-025`) — the parent FLIP/verify didn't hold;
      if a reopen+re-done path re-creates a false-done, that's a mechanism bug worth its own fix, not a per-row
      accident. **Done when**: mechanism identified + fix filed (or shown to be per-row mishandling).
