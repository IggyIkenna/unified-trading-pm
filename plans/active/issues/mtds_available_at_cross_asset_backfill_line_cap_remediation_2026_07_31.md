---
doc_type: issue
title:
  mtds_available_at_cross_asset_backfill_2026_07_13.md is over its 1000-line hard cap (1003/1000) — needs archival/split
summary: >-
  `plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` is at 1003 lines, over `check_line_caps.sh`'s
  1000-line hard cap for `plans/active/*.md`. Not yet a scoped-commit blocker (the SCOPED prek gate only refuses a
  commit that stages the over-cap file itself; the full-corpus baseline mode currently tolerates it as pre-existing
  debt), but it blocks any future todo that needs to ADD content to this plan (a new P3 retrofit todo was deferred out
  of it for exactly this reason — see
  `plans/active/issues/dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md`, now archived) and it is a
  genuinely large Progress Log read for every `/plan-reconcile`/`/ag-closeout-audit` sweep. Per the sibling prediction
  issue's own finding, prediction's todos all read `[x]` except the still-open apply/resume pair (gated on the same
  pause/apply/resume protocol as tradfi); tradfi is likewise all done except apply/resume — so most of the plan's
  historical Progress Log entries document already-CLOSED lanes and are archival candidates, not live work.
status: resolved
nature: issue
asset_group: [tradfi, prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, line-cap, archival, manifest-consolidator]
related:
  [
    /plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/archive/issues/dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md,
    /plans/archive/issues/dp_consolidator_scheduler_paused_prediction_recurrence_2026_07_31.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-07-31
author: unknown
parent_epic: manifest_master
assigned_vm: planning
locked_by:
priority: P3
resolved_by: plan_reconciler-agt-d7a9f2-2026-08-09
source: >-
  Deferred from plans/active/issues/dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md's "Recommended
  decision" § follow-up 2 (2026-07-31) per the archival-ritual requirement that a DEFERRED prose item be migrated into a
  real tracked todo before that doc archives.
execution_scope: orchestrator-agent
drift_direction: correct-docs
depends_on: []
last_updated: 2026-08-09
context_scope:
  [
    /plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/active/task_template.md,
    /plans/archive/issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md,
    /plans/archive/2026_08/mtds_available_at_cross_asset_backfill_progress_log_history_2026_08_01.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# mtds_available_at_cross_asset_backfill_2026_07_13.md line-cap remediation

> **✅ RESOLVED 2026-08-09 (plan_reconciler, dispatch agt-d7a9f2).** Both todos done: the split (todo 1) landed
> 2026-08-01; todo 2 (cross-plan `depends_on`+`gate_on_depends` sequencing) closed RESOLVED-BY-EVENTS — its target plan
> is archived `status: complete` with no remaining apply/resume work to sequence. Archived per the 6-step ritual.

## What I found

`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` is 1003 lines, 3 over `check_line_caps.sh`'s
1000-line hard cap for `plans/active/*.md` (see `/codex/11-project-management/` line-cap policy, enforced via
`scripts/plan-hygiene/check_line_caps.sh`). It is not currently a HARD gate failure (full-corpus mode tolerates
pre-existing debt against the shrinking-ratchet baseline in `line_caps_baseline.yaml`), but it already blocked one
concrete piece of work: `dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md`'s pause-retrofit todo had to
be filed and resolved as a standalone issue doc instead of a todo inside this plan, purely because staging an edit to an
over-cap file trips `check_line_caps.sh`'s SCOPED (prek) mode.

The plan's own Progress Log records (per the sibling prediction issue's finding, mirrored here for tradfi): every
prediction todo reads `[x]` except the still-open apply/resume pair; every tradfi todo reads `[x]` except its own
still-open apply/resume pair. Both open pairs are gated on the same pause/apply/resume backfill protocol (currently
mid-flight, tracked live in the plan itself). The bulk of the plan's ~1000 lines is Progress Log narrative for lanes
that are already fully closed (snapshot, cron-pause, dry-run, bundled/non-bundled split, sports) — good candidates to
extract into an archived history doc per this workspace's standard split pattern, leaving the still-open apply+resume
work in a trimmed active plan.

## Why it matters

An over-cap active plan is a standing tax on every corpus-wide sweep (`/plan-reconcile`, `/ag-closeout-audit`,
`/na-eligibility-audit`) that re-reads it in full, and it structurally blocks any future todo that needs to add content
to the plan itself (as already happened once). Left alone, this will keep generating standalone-issue-doc workarounds
instead of a normal in-plan todo.

## New finding, 2026-07-31 (slot-15) — the AO dispatcher offered "Resume the prediction consolidator cron"

(`mtds_available_at_cross_asset_backfill-006`) while its logical prerequisite, "Apply `rebuild_prediction_manifest.py`"
(`-001`, line 164), is still `- [ ]` open. Re-read the plan's own text before acting (per the standing "read the plan
first" rule) — line 164 is unambiguously unchecked, and no full-range `rebuild_prediction_manifest.py` apply exists
anywhere in `market-tick-data-service` history (checked the Progress Log for the script name; only the `--dry-run` todo,
line 142, is done). Resuming now would violate this plan's own HARD constraint section ("dry-run first, snapshot

- pause... before applying, and verify... before resuming") — the exact class of mistake
  `dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md` documents a different agent making and
  self-correcting earlier the same day. **Declined to resume** — did not touch the prediction cron or run any resume
  script. Root cause: this plan has no machine-encoded ordering between the "Apply" and "Resume" backlog tasks
  (`sequential: true` at the plan level doesn't establish a per-todo `depends_on`/`prereqs.completed_tasks` chain —
  `task_template.md`'s own documented limitation, "no per-todo prereq syntax"), so the dispatcher's priority/tier
  ranking picked the resume task ahead of its logical prerequisite. Skipped the task (`reason_code=BLOCKED`) rather than
  executing it or leaving it silently stuck. Added as a second todo below (bundled into this same doc rather than a
  third overlapping issue doc, since fixing it requires editing the same over-cap plan the split todo already targets).

## Recommended decision

Split the plan: extract the closed lanes' Progress Log history into an archived companion doc, leave the still-open
tradfi/prediction apply+resume todos (plus the still-open sports lane, if any) in a trimmed
`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` under the 1000-line cap. Do this only once the
plan's own todos are stable enough to avoid mid-split churn (a live in-flight pause/apply/resume protocol is currently
running against it) — check the plan's own status before starting.

## Todos

- [x] ✅ [PLAN] P3. Split `plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`: extract fully-closed
      lanes' Progress Log entries into an archived history doc (standard split pattern, `superseded_by`/pointer back
      from the trimmed plan), leaving the still-open apply+resume todos (and any other still-open lane) in the active
      plan, landing it back under the 1000-line hard cap. Verify no todo is currently `locked_by`/mid-dispatch before
      splitting. (repo: unified-trading-pm) — ✅ 2026-08-01 (slot-11, cicd): see Progress Log for full evidence.
- [x] [PLAN] P2. **RESOLVED-BY-EVENTS 2026-08-09 (plan_reconciler), not executed.** ~~While splitting (todo above), add
      explicit per-todo sequencing between each asset group's "Apply `rebuild_{prediction,tradfi}_manifest.py`" and
      "Resume the {prediction,tradfi} consolidator cron" todos via the cross-plan `depends_on` + `gate_on_depends: true`
      split~~ — the target plan (`mtds_available_at_cross_asset_backfill_2026_07_13.md`) no longer exists in
      `plans/active/`: verified it archived to
      `/plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md` with `status: complete` (16/17
      checkboxes done; the sole remaining open item is an unrelated orchestrator `orphan_reap` follow-up, not an
      apply/resume todo). Every apply/resume/go-no-go todo this restructure was meant to sequence-guard completed
      without the guard ever being built — the race this todo hedged against never materialized. Building the
      depends_on/gate_on_depends split now would restructure a plan that no longer has any open apply/resume work to
      sequence. **This todo carried `assigned_vm: planning` (live AO-dispatchable) — flagging closed here specifically
      to stop a future dispatch from being wasted discovering the target is gone.** (repo: unified-trading-pm)

## Progress Log

**2026-08-01 (slot-11, cicd)**: dispatched to the `[PLAN] P3` split todo (`-001`). Before touching the target plan,
re-checked `GET /api/backlog` per the sibling `-002` entries' recommendation:
`mtds_available_at_cross_asset_backfill-006` ("Resume the prediction consolidator cron") was still `status: dispatched`
(`dispatched_to: 3`, `dispatched_at: 2026-07-31T23:33:21Z`, ~82 min stale by my check). Rather than decline a third time
on that alone, checked the actual liveness of slot 3 via `GET /api/activity?limit=300`: slot 3 had been repeatedly
`worker_kicked` (`kind: idle`) every ~2 minutes continuously since 00:36:17Z — a stuck/idle session, not a live worker
about to append a Progress Log entry to the target file. Independently confirmed via
`git log -1 --format=%cI -- <plan path>` that the plan's last real commit was `2026-07-31T04:37:15+00:00` (`ccfec294c`)
— well before both slot 4's and slot 13's declined touches, confirming neither of those (nor `-006`'s stale dispatch)
has actually written to the file since. Concluded the collision risk both prior slots correctly flagged was no longer
live and proceeded.

Read the full 1004-line plan end to end and confirmed slot 13's shape finding still held: 15 todos total (6 open — lines
164/169/288/297/311/323 — prediction apply/resume, tradfi apply/resume, defi go/no-go + implement-and-apply; 9 closed),
`## Progress Log` (lines 336-1004, ~668 lines) entirely historical narrative for closed lanes, each closed todo already
carrying its own inline evidence summary (same shape the `deployment_api_sigabrt_crash_loop_2026_07_24.md` line-cap
precedent used, followed here as the established split pattern).

**Executed the split**: extracted lines 338-922 (every Progress Log entry from the 2026-07-13 plan authoring through the
2026-07-14 DeFi handler audit dispatch, data_engineering slot-8) verbatim to a new archive doc,
`/plans/archive/2026_08/mtds_available_at_cross_asset_backfill_progress_log_history_2026_08_01.md` (`doc_type: plan`,
`status: complete`, `nature: record`, mirroring `defi_master_history_2026_07_24.md`'s frontmatter shape for a
plan-sourced history extraction). Kept the two most recent Progress Log entries (2026-07-28 gate-cleanup pass,
2026-07-29 crons-paused/fresh-snapshots) inline in the live plan — deliberately, since they describe the CURRENT infra
state (both consolidator crons paused, fresh 2026-07-29 snapshots taken) that any future apply/resume dispatch needs
without opening the archive. Added a pointer note at the top of the live plan's `## Progress Log` section (same
"line-cap remediation... new entries append below" convention as the sigabrt precedent). Added the new archive doc to
the live plan's `related:` frontmatter list and bumped `last_updated`. Touched NOTHING in the Todos section itself — all
15 checkboxes (open and closed) preserved verbatim, byte-for-byte, only the Progress Log section was restructured.

**Verified**: live plan now 425 lines (was 1004) —
`bash scripts/plan-hygiene/check_line_caps.sh plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` →
`✅ within cap`. Both files' YAML frontmatter parse cleanly (`yaml.safe_load`); `check_frontmatter_schema.py` on the
live plan → zero violations (the archive doc is out-of-scope for that check by design — `plans/archive/**` is excluded,
confirmed by reading the script). `diff`-verified the archive doc's body + the live plan's trimmed tail together
reconstruct the original file's Progress Log content exactly (no line dropped, no line duplicated). No code/production
changes — plan-doc-only split, shipped via the `docs(plans):` carve-out.

**What I did NOT do**: did not touch the second todo below (`-002`, the cross-plan `depends_on`+`gate_on_depends`
apply→resume ordering restructure) — that is a separate, larger structural change (an actual plan fork into an
apply-plan + a gated resume-plan) outside this task's own scope (`-001` only); leaving it for the dispatcher's normal
next-task assignment rather than fanning out to a second todo in this same session, per the one-task-at-a-time worker
rule. Did not touch any cron, snapshot, or manifest — pure doc restructuring.

**2026-07-31 (slot 4, data_engineering)**: dispatched to the `[PLAN] P2` todo above. Did NOT execute the split — two
blocking findings, neither of which is a normal "wait for the prerequisite" situation the dispatcher would otherwise
gate on:

1. **This todo's own suggested mechanism is invalid.** `task_template.md` (corrected 2026-07-21, "Ordering + how
   prerequisites ACTUALLY work") states plainly: _"there is NO per-todo prereq syntax; regen never parses prereqs from
   todo text"_ and _"the earlier 'add explicit `prereqs.completed_tasks`' advice was wrong"_ — `RULES.md` confirms
   `regen_backlog_from_plan.py` does not derive per-task `prereqs.completed_tasks` from plan content, and hand-editing
   `backlog.yaml` to add them is explicitly banned ("NEVER hand-edit `backlog.yaml` to add prereqs — author the
   frontmatter; the backend derives them"). The only two real mechanisms are (a) `sequential: true` (already set on the
   target plan, and independently confirmed STILL not reliably gating dispatch order as of today — see
   `issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md`'s 2026-07-31 entries, two fresh
   unrelated-plan recurrences hours after the `agent-orchestrator@77769ab` fix landed), or (b)
   `depends_on: [plan-slug]` + `gate_on_depends: true` — a CROSS-PLAN mechanism (`_wire_gate_on_depends_prereqs`), which
   gates at plan granularity, not per-todo. Given (a) is demonstrably unreliable for exactly this apply/resume ordering
   right now, the template's own prescribed fix for "partial-parallelism isn't expressible in one plan" is to **SPLIT**:
   an "apply" plan (prediction/tradfi/defi applies, safely parallel across asset groups) and a separate "resume" plan
   with `depends_on: [<apply-plan-slug>]` + `gate_on_depends: true`. Corrected this todo's own text above to point at
   the real mechanism.
2. **Unsafe to execute right now regardless of mechanism** — before touching the target plan, checked `GET /api/backlog`
   for any todo currently `dispatched`/mid-flight on it (per this todo's own sibling `-001`'s "verify no todo is
   currently `locked_by`/mid-dispatch before splitting" precondition, which applies equally here since both todos edit
   the same file): `mtds_available_at_cross_asset_backfill-006` ("Resume the prediction consolidator cron") is
   `status: dispatched`, `dispatched_to: 12`, `dispatched_at: 2026-07-31T23:13:54Z` — i.e. RIGHT NOW, live, on this
   exact plan file. Every prior slot dispatched this same premature "-006" class of task (the plan's own Progress Log:
   findings #2-#7, plus the sibling sequential-dispatch-bug issue doc's 2026-07-30/31 entries) resolved it by
   declining + appending a Progress Log entry to the SAME plan file — a likely-imminent concurrent commit to the exact
   file this todo needs to restructure (extract history, fork into 2 new plan docs). Running the split concurrently
   risks a rebase collision or a dropped append during conflict resolution. The sibling `-001` split todo is ALSO still
   `status: queued`/unclaimed (never executed) — this todo's own precondition ("while splitting the todo above") is not
   met either.

**Declined to execute** (skipping this task rather than forcing a same-file edit concurrent with a live dispatch, or
attempting the invalid `prereqs.completed_tasks` mechanism the todo originally named). No files in the target plan
touched. Recommend re-dispatch once (a) `-006`/the plan's currently-dispatched task clears (done or declined+skipped)
and (b) the sibling `-001` split todo is picked up — ideally both `-001` (split) and this todo (cross-plan
`depends_on`+`gate_on_depends` restructure) are done together in one pass, per this todo's own "while splitting"
framing, by whichever worker claims `-001`.

**2026-07-31 (slot 13, data_engineering)**: dispatched to the `[PLAN] P3` todo above (`-001`, the split itself, distinct
from slot 4's touch on `-002`). Read the full target plan (1004 lines) end to end and confirmed the split shape slot 4's
finding + this doc's "What I found" section describe still holds: 6 still-open todos (prediction apply/resume, tradfi
apply/resume, defi go/no-go + implement-and-apply, lines 164/169/288/297/311/323), everything else in the Todos section
`[x]`, and the ~670-line Progress Log (lines 336-1004) is entirely historical narrative for already-closed lanes
(dispatch-order-bug findings #2-#8, snapshot/pause evidence, the tradfi bundled/non-bundled investigation + dead-branch
fix, the DeFi handler audit) — a real, ready-to-execute split.

Before touching the target plan, checked this todo's own precondition ("verify no todo is currently `locked_by`/
mid-dispatch before splitting") via `GET /api/backlog`: `mtds_available_at_cross_asset_backfill-006` ("Resume the
prediction consolidator cron") is `status: dispatched`, `dispatched_to: 3`, `dispatched_at: 2026-07-31T23:33:21Z` —
still live 13+ minutes in at the time of this check (23:46:29Z), unchanged from slot 4's identical finding on the
sibling todo earlier today. Per this plan's own extensive Progress Log precedent (dispatch-order findings #2-#8), a
`-006`-class dispatch that gets declined (the overwhelmingly likely outcome — every prior `-006`/`-014` dispatch across
8+ touches was declined, and each decline appended a new Progress Log entry to the exact file this split needs to
restructure) lands a same-region commit on `plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` — the
identical file whose Progress Log section this split rewrites/relocates in its entirety. A concurrent append there
during a full-file restructure is a near-certain rebase collision, not just a theoretical one.

**Declined to execute**, same reasoning as slot 4's touch above: no files in the target plan touched, no split
performed. This is now the SECOND independent confirmation (slot 4 on `-002`, this touch on `-001`) that `-006`'s
live-dispatch status is blocking BOTH split-related todos from proceeding safely. Calling `/skip-current-task` so
another slot can retry once `-006` clears (done or declined+skipped) — recommend whoever picks this up next re-check
`GET /api/backlog` for `-006`'s status FIRST, before re-reading the full plan, to avoid burning a full read cycle only
to hit the same block.

- **context-scout 2026-08-03**: populated context_scope (5 entries).

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
