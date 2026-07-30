---
doc_type: issue
title:
  "gate_on_depends silently no-ops even when the upstream `depends_on` plan IS ingested and has genuinely open (queued,
  non-done) todos — reproduced twice on cefi_track2_coverage_backfill_checkpoints_finalize-001, incl. after a final
  blocked-queue ruling"
summary: >-
  `cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md`'s todo 1 (backlog task
  `cefi_track2_coverage_backfill_checkpoints_finalize-001`) carries `depends_on:
  [cefi_track2_coverage_backfill_checkpoints_2026_07_25]` + `gate_on_depends: true`, and that upstream plan genuinely
  has 2 of 5 todos still open (`cefi_track2_coverage_backfill_checkpoints-004`/`-005`, both live `status: queued` rows
  in the backlog, not done/pruned). Despite that, `finalize-001` was dispatched TWICE (slot 10 at ~15:xx, then slot 12
  at 16:08 — 3 minutes after main's FIRST final ruling to leave it blocked/gated). Live-backlog inspection (`GET
  /api/backlog`) confirms the smoking gun: `finalize-001`'s own row carries `"prereqs": null` — the gate was never wired
  at all, distinct from the two already-archived `gate_on_depends` no-op variants (both of which involved an upstream
  that was NEVER INGESTED — `local-only`/`NA` or otherwise absent from the backlog). Here the upstream IS ingested
  (`assigned_vm: planning`) and its 2 remaining tasks ARE live, non-done backlog rows, which per
  `regen_backlog_from_plan.py`'s own documented logic (`_wire_gate_on_depends_prereqs`, reading `file_to_ids` from
  currently-open backlog task ids under the upstream's `plan_ref`) should have produced `prereqs.completed_tasks:
  [cefi_track2_coverage_backfill_checkpoints-004, cefi_track2_coverage_backfill_checkpoints-005]` on `finalize-001` — it
  produced nothing.
status: open
nature: issue
asset_group: [cefi, meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch-logic, gate_on_depends, plan-discipline, root-cause, recurring-bug, cefi]
related:
  [
    /plans/active/cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
    /plans/archive/issues/gate_on_depends_noop_on_local_only_upstream_2026_07_21.md,
    /plans/archive/issues/gate_on_depends_noop_on_assigned_vm_na_upstream_2026_07_21.md,
  ]
created: "2026-07-30"
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source:
  [
    "cefi_track2_coverage_backfill_checkpoints_finalize-001 (slot 10, then slot 12), main ruling BLK-6c491ad1 2026-07-30",
  ]
resolved_by:
locked_by:
locked_since:
depends_on: []
last_updated: "2026-07-30"
---

# What I found

`cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md`'s todo 1 is machine-gated
(`depends_on: [cefi_track2_coverage_backfill_checkpoints_2026_07_25]`, `gate_on_depends: true`) on ALL 5 todos of
`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` being done. Only 3 of 5 are done — `-004`
(`/data-pipeline-check-is` POST-BACKFILL gate) and `-005` (`/data-pipeline-check-mtds` POST-BACKFILL gate) are both
blocked on a preempted, unrecovered backfill VM (see the related preemption issue doc) and remain live `status: queued`
backlog rows.

Despite this, the derived task `cefi_track2_coverage_backfill_checkpoints_finalize-001` was dispatched to slot 10
(discovered + correctly handled: partial checkbox flip + issue doc filed, `/blocked` BLK-31fcaeb9, main ruled FINAL
"stay blocked/gated"), then dispatched AGAIN to slot 12 only ~3 minutes after that final ruling landed
(`task_dispatched` activity id 242807, 16:08:12, vs. `blocked_answered` id 242781, 16:05:28 — same session). Slot 12
re-filed `/blocked` (BLK-6c491ad1); main's second ruling (16:1x) confirmed the first ruling stands and directed this
follow-up issue doc.

**Root-cause evidence** — `GET /api/backlog` on the live orchestrator, filtered to the relevant task ids:

```
cefi_track2_coverage_backfill_checkpoints-004 | status: queued | priority: 999 | plan_ref: .../cefi_track2_coverage_backfill_checkpoints_2026_07_25.md
cefi_track2_coverage_backfill_checkpoints-005 | status: queued | priority: 20  | plan_ref: .../cefi_track2_coverage_backfill_checkpoints_2026_07_25.md
cefi_track2_coverage_backfill_checkpoints_finalize-001 | status: dispatched | priority: 20 | prereqs: null
```

`finalize-001`'s `prereqs` field is `null` — the gate-derivation step never wired anything onto this task at all. This
is a DIFFERENT failure mode from the two already-archived `gate_on_depends` no-op incidents:

- `gate_on_depends_noop_on_local_only_upstream_2026_07_21.md` and
  `gate_on_depends_noop_on_assigned_vm_na_upstream_2026_07_21.md` — both root-caused to the upstream plan never being
  INGESTED at all (`local-only`/`NA`), so it produces zero backlog task rows, and `_wire_gate_on_depends_prereqs` can't
  distinguish "genuinely nothing left" from "never ingested, so nothing was ever created" — a documented, since-tested
  fail-open.
- **This case is different**: the upstream (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) IS ingested
  (`assigned_vm: planning`), and its 2 remaining todos ARE live, queued (non-done, non-pruned) backlog rows with the
  correct `plan_ref` — exactly the case `_wire_gate_on_depends_prereqs`'s `file_to_ids` lookup is supposed to catch and
  turn into `prereqs.completed_tasks` on the downstream task. It didn't. The already-shipped fix for the two prior
  incidents does not cover this path.

## Why it matters

This is a live, currently-reproducing correctness bug in the dispatcher's gate enforcement, not a one-off. It has now
fired twice on the SAME task in one session, the second time even surviving an explicit final `/blocked` ruling telling
the dispatcher (via a human/main decision, not a machine gate) to leave the task alone — meaning the only thing
currently stopping a third bounce is a human noticing and re-answering, which does not scale. Per main's own framing
(BLK-6c491ad1 answer): "the dispatch-gate-not-enforced bug will keep mis-dispatching OTHER gated tasks" — any other plan
using `depends_on` + `gate_on_depends: true` against an ingested, partially-open upstream is exposed to the same
premature-dispatch risk, silently producing false-progress pressure on workers who then have to notice, decline, and
escalate by hand each time (3 worker-turns burned across 2 slots just for this one instance).

## Recommended decision

Investigate `agent-orchestrator/server/regen_backlog_from_plan.py`'s `_wire_gate_on_depends_prereqs` (currently
~L1917-1993, called from the main scan loop ~L1669) for why `file_to_ids` came back empty (or was never applied) for
`cefi_track2_coverage_backfill_checkpoints_finalize-001` specifically, even though the upstream's 2 open task ids exist
in the live backlog with matching `plan_ref`. Plausible causes to check first (not yet root-caused, worth a fresh
regen+diff trace rather than a guess-and-patch):

- A `_stem()` mismatch between the `depends_on: [cefi_track2_coverage_backfill_checkpoints_2026_07_25]` frontmatter
  value and the `stem_to_path`/`file_to_ids` keying used for the upstream — small path-form or suffix differences are
  the documented failure class here.
- A stale regen snapshot: if `finalize-001`'s row was created in an earlier regen pass (e.g. while the upstream still
  read as fully-done, before `-004`/`-005` were reopened/reinstated by main's 2026-07-28 park-and-reopen), and no
  subsequent regen re-wired `prereqs` onto the ALREADY-EXISTING row (only new rows getting the derived prereqs, not a
  re-sync of existing ones).
- Whether `_wire_gate_on_depends_prereqs` runs its `file_to_ids` lookup keyed by the exact same `_stem(plan_ref)` string
  the upstream tasks carry, given the upstream plan file itself was FORKED
  (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` split out of `cefi_consolidated_closeout_2026_07_18.md`'s
  Track 2 on 2026-07-25) — worth confirming the fork didn't leave a residual keying mismatch.

## Todos

- [ ] [BACKEND] P1. Root-cause why `_wire_gate_on_depends_prereqs` produced `prereqs: null` on
      `cefi_track2_coverage_backfill_checkpoints_finalize-001` despite its upstream
      (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) being ingested with 2 live, open (non-done) backlog
      task rows (`-004`, `-005`) under the matching `plan_ref`. Add a regression test to
      `tests/test_regen_backlog_from_plan.py` reproducing this exact shape: an ingested upstream plan with SOME (not
      all) todos done, re-gated after a prior regen already created the downstream task row. Repo: agent-orchestrator.
- [ ] [BACKEND] P2. Once root-caused, add a periodic/regen-time consistency check that flags (not silently
      auto-corrects) any `gate_on_depends: true` downstream task whose `prereqs` is null/empty while its `depends_on`
      plan has ANY open todo — so this class of gate-noop surfaces as a detectable drift signal instead of only being
      caught when a worker happens to notice and escalate. Repo: agent-orchestrator.
