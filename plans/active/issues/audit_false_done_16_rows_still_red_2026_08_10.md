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
# Bridge for the flip-then-mv two-commit archival (last open todo = own archival
# trigger; see check_archive_candidates_only_mode_no_flip_then_mv_exemption_2026_08_09.md).
# Dropped when this doc is git mv'd to plans/archive/issues/ in the following commit.
archive_exempt: true
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

- [x] ✅ [BACKEND] P0. **Reopen or FLIP all 16 false-done rows listed above** — agent-orchestrator (API only, no code
      commit). All 16 reopened via `POST /api/backlog/{id}/reopen` (reason: false_done audit 2026-08-10). Audit re-run
      exits 0: `false_done: 0, honest: 918, UNAUDITABLE: 11, unresolved: 1529`. Evidence:
      `scripts/orchestrator/audit_false_done.py --db <live state.db> --pm ../unified-trading-pm --ref origin/live-defi-rollout`
      exit 0.
- [x] ✅ [BACKEND] P1. **Re-characterised the 1,529 `unresolved` rows** (up from 1,528) — agent-orchestrator (no code
      commit, investigation-only). **100% expected**: every single plan_ref filename exists in `plans/archive/` — zero
      broken/missing references. 546 unique archived plans; 864 rows via `archive/issues/`, 424 via `archive/2026_08/`,
      241 via `archive/2026_07/`. Growth +516 from 1,013→1,529 is normal fleet archival activity between 2026-08-08 and
      2026-08-10. Verdict: no NEW non-archived referents dropped — the audit's unresolved count is a trailing indicator
      of plan archival, not a correctness defect. See Progress Log for full breakdown.
- [x] ✅ [BACKEND] P2. **Root-cause why 2 triaged rows recurred** (`defi_cefi_venue_chain_axis_contamination-011`,
      `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed-025`) — the parent FLIP/verify didn't hold;
      if a reopen+re-done path re-creates a false-done, that's a mechanism bug worth its own fix, not a per-row
      accident. **Done when**: mechanism identified + fix filed (or shown to be per-row mishandling). — **Mechanism
      identified + fix filed** (see Progress Log 2026-08-10 slot 19): `-025` is a genuine mechanism bug (audit
      `_still_unchecked` matches repeated `- [ ]` lines with byte-identical first lines, so a recurring "launch next
      round" gate perpetually re-flags the same stem — fix = dedupe matched unchecked lines by identity /
      first-occurrence); `-011` is per-row mishandling (worker marked done with `no-code:gate-still-unmet-verified`
      without flipping the checkbox). Fix tracked as a `- [ ]` follow-up below.

- [x] ✅ [BACKEND] P2. **Fix `audit_false_done.py::_still_unchecked` to not re-flag a repeated `- [ ]` line whose first
      line is byte-identical to an already-`[x]`-flipped todo in the same plan.** The recurring "Round-8 ACTUAL LAUNCH"
      gate in `cefi_content_migration_..._2026_07_31.md` recurs because the audit matches by first-line hash alone
      (`_UNCHECKED_RE` + `_brief_hash`), so every "launch the next round" instance with the same first line re-derives
      the same task stem and re-flags false_done. Match the full todo line (or dedupe so only the FIRST unchecked
      occurrence of a given brief counts), so a genuinely-flipped-and-replaced recurrence is not re-flagged. (repo:
      agent-orchestrator; scripts/orchestrator/audit_false_done.py)

## Progress Log

### 2026-08-10 — Todo 4 shipped: `_still_unchecked` recurrence blind spot fixed (slot 16, task `audit_false_done_16_rows_still_red-03d405b42cae`)

**Fix**: `scripts/orchestrator/audit_false_done.py::_still_unchecked` now collects the set of briefs already
`[x]`-flipped anywhere in the same plan (with the `✅` decoration stripped, mirroring regen's `_parse_done_todos`), and
a matching `- [ ]` line is only reported as still-unchecked if that brief is NOT in the flipped set. A
flipped-and-replaced recurrence (byte-identical first line — the recurring "Round-8 ACTUAL LAUNCH" gate) is therefore no
longer re-flagged, while genuinely-open duplicate briefs (no flip anywhere) still flag.

**Tests**: `tests/test_audit_false_done.py` — 5 cases covering the -025 recurrence shape, plain still-unchecked,
flipped-only honest, unflipped duplicates still flag, and cross-brief non-suppression.

**Evidence**: `agent-orchestrator@42d29c3d7a` (full QG green: 3310 passed, 2 skipped; dashboard tsc + vitest clean;
quickmerge landed, SHA ancestor of `origin/live-defi-rollout`).

### 2026-08-10 ~16:40Z — P1 unresolved characterisation (slot 10, task `audit_false_done_16_rows_still_red-29e848430531`)

Re-ran the audit against the live `state.db` (306MB, root clone at
`/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/state.db`) reading plans at
`origin/live-defi-rollout` @ `f21d582f28`. **Audit exits 0** (false_done: 0 — the P0 reopen held).

**Unresolved count: 1,529** (up from 1,528 in the body report at ~16:20Z; 1 more row tipped into unresolved in the
interim — normal: the DB is live and the fleet keeps dispatching/archiving).

**Categorisation methodology**: for each of the 1,529 unresolved rows, extracted the filename from `plan_ref`, then
looked it up against a full `git ls-tree -r origin/live-defi-rollout plans/archive/` index. Every single filename
resolved — zero broken references.

**Results**:

| Category                 | Rows      | Unique plans |
| ------------------------ | --------- | ------------ |
| `plans/archive/issues/`  | 864       | 287          |
| `plans/archive/2026_08/` | 424       | 185          |
| `plans/archive/2026_07/` | 241       | 74           |
| **Total**                | **1,529** | **546**      |

**Plan type breakdown** (unique plans): issue docs 331, satellite dispatch batches 111, other plans 54, finalize plans
31, closeout plans 11, consolidated plans 8. Top plan by row count: `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (29
rows, archived to `plans/archive/2026_08/`).

**Growth analysis** (+516 from 1,013 → 1,529 between 2026-08-08 and 2026-08-10): entirely explained by normal fleet
archival activity. Plans that were still in `plans/active/` during the parent doc's audit have since been completed and
archived — each archived plan's done rows become "unresolved" because `_plan_ref_candidates()` only searches
`plans/active/` variants, not `plans/archive/` subdirectories. This is expected behaviour: the audit's purpose is
finding actively LYING rows (checkbox still `- [ ]` but status=done), not rows pointing to completed/archived work.

**Verdict**: the unresolved count is a trailing indicator of plan archival velocity, not a correctness defect. No NEW
non-archived referents are being dropped. The `_plan_ref_candidates` function could be extended to also search
`plans/archive/` (so genuinely-archived rows become "honest" rather than "unresolved"), but that's a cosmetic
improvement — it wouldn't change the audit's core signal (false_done count).

### 2026-08-10 — Todo 3 (root-cause the 2 recurring rows) — mechanism identified + fix filed (slot 19)

Root-caused both recurring rows. Two DISTINCT mechanisms — one genuine audit blind spot, one per-row mishandling:

**1. `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed-025` — MECHANISM BUG (audit blind spot).**
The todo it derives from is `cefi_content_migration_..._2026_07_31.md` line 888:
`- [ ] [DATA] P1. Round-8 ACTUAL LAUNCH — all 8 shards (16,17,18,19,21,23,41,42). **Gated on prereq ...` (a recurring
"launch the next round" gate). Commit `0e9185d2ce` (the original `-025` completion) did BOTH in one commit: flipped line
888 to `[x]` AND immediately added a NEW `- [ ]` line with a BYTE-IDENTICAL first line
(`- [ ] [DATA] P1. Round-8 ACTUAL LAUNCH — all 8 shards (16,17,18,19,21,23,41,42). **Gated on prereq`). The audit's
`_still_unchecked` hashes only the FIRST LINE of each `- [ ]` line (`_UNCHECKED_RE` captures one line, `_brief_hash`
hashes `m.group(1).strip()`), so the newly-added unchecked line hashes to the SAME `brief_hash` as the old task stem →
the same `-025` stem perpetually re-derives and re-flags false_done on every round. Verified: `-025` queued row's
`brief_hash=0354d900...` == sha256 of the full first line
`[DATA] P1. Round-8 ACTUAL LAUNCH — all 8 shards (16,17,18,19,21,23,41,42). **Gated on prereq`. This is the exact
"reopen+re-done re-creates a false-done" mechanism the todo suspected — it is NOT per-row accident.

**2. `defi_cefi_venue_chain_axis_contamination-011` — PER-ROW MISHANDLING.** Its plan line
(`defi_cefi_..._2026_07_28.md` line 300,
`[DATA] P1. NEW 2026-08-04. Once <cefi_tardis_derivative_ticker_historical_gap backfill> completes: re-run run_cefi_perp_funding_corpus.py...`)
is gated on an upstream backfill that has NOT completed. A worker marked the task done with
`done_sha=no-code:gate-still-unmet-verified` — a `no-code:` decline that verifies the gate is unmet and records
completion WITHOUT flipping the checkbox. Because the checkbox stays `- [ ]`, the audit re-flags it every run until the
backfill actually completes and the line is genuinely flipped. The parent doc's "FLIP" verdict was this `no-code:`
decline, not a checkbox flip — hence "the FLIP didn't hold".

**Fix filed** (tracked below): the audit's `_still_unchecked` must NOT match a `- [ ]` line whose brief is a REPEATED
instance of an already-`[x]`-flipped todo (dedupe by full-todo identity / line number, or require the matched `- [ ]`
line to be the FIRST unchecked occurrence of that brief, not a recurrence). This is a
`scripts/orchestrator/audit_false_done.py` change (server-side audit fix), tracked as a `- [ ]` follow-up in this doc's
Todos below.
