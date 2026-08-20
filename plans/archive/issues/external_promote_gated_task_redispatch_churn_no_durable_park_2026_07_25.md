---
doc_type: issue
title:
  A verification task gated on an EXTERNAL promote (deployment-api LDR->main) reads "ready (no blockers)" and
  release-requeues, so it re-dispatches to a fresh worker on every tick (observed 3x — slots 8, 2, 5 — on
  deployment_registry_reaper-002 while deployment-api@3fea307 stayed off main); it should PARK durably via an
  auto_unpark prereq (as batch2-011 does), not churn through workers
summary: >-
  On 2026-07-25 main (agt-52bb99) observed deployment_registry_reaper_not_draining_stale_entries-002 re-dispatch to
  THREE workers in sequence (slot 8 ~13:14Z -> slot 2 ~12:5xZ -> slot 5 ~13:19Z). The task's remaining work is a
  verification — re-confirm the gunicorn fix deployment-api@3fea307 is live + observe reap-tick convergence — that
  cannot complete until deployment-api promotes LDR->main. That promote is stuck on a KNOWN issue
  (sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md, P2/DEVOPS, ~156min precedent). Main measured
  `git merge-base --is-ancestor 3fea307 origin/main` = FALSE on every re-dispatch (fix genuinely not on main yet). The
  gap: this EXTERNAL gate (a promote landing on main) cannot be expressed as a backend `depends_on`/blocker, so
  `/api/backlog/<id>/blockers` returns "ready (no blockers)" and the dispatcher hands it to the next free worker each
  tick. Each worker boots, does a fast check-and-release (cheap, <1s git check — not a full wasted cycle), and the task
  requeues, repeating indefinitely until the promote lands. Contrast batch2-011, which parks DURABLY via a named
  `auto_unpark__sports_satellite_ao_dispatch_batch2-011` prereq that survives re-derivation and correctly holds the task
  (and its 52 downstream) until the unpark condition fires. A worker-applied `priority_override` park (priority 999)
  does NOT survive a backlog re-derivation tick (it gets wiped and re-dispatched) — so the reaper task has no durable
  park and churns. Low blast radius (cheap check-and-release, self-terminates when the promote lands), but it is real
  dispatch noise, it repeatedly re-raises the same operator/main blocked question, and it defeats the "pick up other
  work" answer because the backend keeps handing the SAME gated task back.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, external-gate, promote-gate, auto-unpark, re-dispatch, churn, throughput, watchdog]
related:
  [
    /plans/archive/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md,
    /plans/archive/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md,
    /plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-25
author: unknown
last_updated: 2026-08-06
priority: P3
parent_epic: orchestrator_master
source:
  "main orchestrator (agt-52bb99) read-only per-task diagnosis + git ancestry checks during poll loop, 2026-07-25
  ~13:10-13:20Z"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/archive/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/issues/gated_skip_park_no_slack_page_2026_07_25.md,
    agent-orchestrator/server/auto_park.py,
    agent-orchestrator/server/routes/slots_ops.py,
  ]
depends_on: []
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. The single [BACKEND] P3 todo is [x] done — implemented + shipped agent-orchestrator@23bd0b3
> (Part 1 auto_park.py docstring documenting priority_override vs auto_unpark__ prereq, Part 2 park_now/manual_park
> wiring, 2 new tests, QG green 2507 passed). Moved by the 2026-08-06 AO issue-doc archive sweep.

# External-promote-gated verification task re-dispatches every tick instead of parking durably

## Evidence (read-only, on-host :8765 + git, 2026-07-25, main agt-52bb99)

- Task: `deployment_registry_reaper_not_draining_stale_entries-002`. Remaining work = verify `deployment-api@3fea307`
  gunicorn fix is live on the deployed container + observe reap-tick convergence — impossible until deployment-api
  promotes LDR->main.
- `/api/backlog/<id>/blockers` → **"ready (no blockers)"** on every check (the external promote gate is invisible to the
  backend).
- Re-dispatch trail (all `status=dispatched` to a different `dispatched_to` across ticks): **slot 8** (raised
  `BLK-394af695`, main answered A: park + monitor + pick up other work) -> **slot 2** (main messaged the gate context +
  park recommendation) -> **slot 5** (3rd worker, same wall).
- `git merge-base --is-ancestor 3fea307 origin/main` = **FALSE** measured at each re-dispatch — the fix is genuinely not
  on main; workers are correctly detecting a real gate, not a phantom.
- The gate's root (the stuck promote) is already tracked: `sit_validated_tree_treadmill_blocks_breaking_promotes` (P2,
  DEVOPS-owned).

## Root cause / the gap

An external condition (a commit reaching `main` via the LDR->main promote) is not representable as a backend
`depends_on`/blocker, so the task reads dispatchable and is handed to the next free worker every tick. The worker can
only discover the gate at runtime (a git ancestry check), then release — and because a worker-applied
`priority_override` park (priority 999) does NOT survive a backlog re-derivation tick, nothing makes the park stick. The
mechanism that WOULD make it stick already exists and is proven in the same fleet: the named `auto_unpark__<task-id>`
prereq (as `sports_satellite_ao_dispatch_batch2-011` uses) durably parks a task + its downstream until the unpark
condition fires.

## Todos

> **✅ CONFLICT RESOLVED 2026-07-31 — OPERATOR RULED OPTION A** (corpus-wide ownership-conflict sweep; this is the
> decision the "Deferred — HELD" section below was waiting on, and it recommended exactly this). The file-collision was
> with `/plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s `[BACKEND] P3` "Audit every
> `/skip-current-task` `reason_code` for a silent, unpaged durable park", which is **explicitly AUDIT-ONLY** ("do not
> change `auto_park.py` in this todo"). **Sequence: batch1's read-only audit lands FIRST, then this doc's implementation
> dispatches against its findings.** Nobody edits `auto_park.py` until the audit exists — that is what stops the two
> from racing on the same file.
>
> The operator also allowed folding "if that's cleaner once you read current state". It is: the two former todos were a
> mechanism-design item and a diagnostic question whose answer (why does a `priority_override` park evaporate but a
> named `auto_unpark__` prereq survive?) **is the input that decides the mechanism**. Sequencing them as separate
> dispatches would have re-read the same dispatcher code twice. **Folded into one gated item below**; neither half was
> dropped — both done-whens are preserved verbatim.

- [x] ✅ [BACKEND] P3. **READY.** Durably park via `auto_unpark__<task-id>` (not `priority_override`) in `auto_park.py`.
      — agent-orchestrator@23bd0b3 Context: in `agent-orchestrator`'s dispatcher (`server/auto_park.py`), a
      `priority_override` park does not survive backlog re-derivation, but a named `auto_unpark__<task-id>` prereq does.
      Gate cleared 2026-08-01 — the prerequisite audit (`ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s
      `/skip-current-task` `reason_code` audit) found zero uncovered `reason_code` gaps; full table in
      `/plans/archive/issues/gated_skip_park_no_slack_page_2026_07_25.md`. In one change: **(1) [was todo 2 — do this
      first, it decides (2)]** Confirm why a `priority_override` (priority 999) park does not survive backlog
      re-derivation while a named `auto_unpark__` prereq does — document the difference so workers pick the durable
      mechanism for external gates (cross-ref RULES.md sec4 and the batch2-011 park). If `priority_override` parks are
      meant to be durable, that is a separate bug and gets its own todo; if not, workers should stop using them for
      anything that must outlast a re-derivation tick. **(2) [was todo 1]** Give a worker that hits an EXTERNAL gate (a
      commit/promote not yet on a target branch) a way to park the task DURABLY — either (a) let it set a named
      `auto_unpark__<task-id>` prereq keyed on the gate condition (mirroring batch2-011), which the dispatcher already
      honors and which survives re-derivation, or (b) support an explicit "gated on external ref reaching branch X"
      marker the dispatcher treats as a real blocker; pick between them using (1)'s finding and the audit's table rather
      than guessing. **Done when**: BOTH halves land — the priority_override-vs-prereq difference is documented, AND a
      promote-gated verification task parks after the FIRST worker detects the gate and does NOT re-dispatch to a fresh
      worker every tick, resuming only when the gate clears, with a test simulating "ref not yet on main".
      **na-eligibility-audit 2026-08-03**: the stated GATE (`ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s
      `/skip-current-task` `reason_code` audit) is now CLEARED — that plan (archived 2026-08-01, 11/11 todos done)
      records its own todo 8 executed fresh 2026-08-01 (read-only, found zero uncovered codes), and its Progress Log
      explicitly states it "cleared the gate on
      `external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md`." The GATED prefix no longer blocks
      dispatch; the two-part implementation itself remains open/undone.

## Deferred — hold RELEASED 2026-08-06 (was held by the `/na-eligibility-audit ao` conflict-check, 2026-07-30)

**✅ HOLD RELEASED — the stated blocker previously required an operator decision and is now resolved by measurement, not
by judgment.** The hold existed for exactly one reason: a file-collision + sequencing overlap with an OPEN
`[BACKEND] P3` in `ao_satellite_ao_dispatch_batch1_2026_07_26.md`. Measured at HEAD 2026-08-06: that plan is at
`/plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md`, `status: complete`, **0 open / 11 done** — the
colliding todo is closed and the plan is archived, so the overlap that justified the hold no longer exists. Retagged in
this same edit per CLAUDE.md's rule that a resolved gate is never left stale, and phrased deliberately without the
literal non-dispatchable marker substring, because `_NON_DISPATCHABLE_RE` scans the entire block and the substring alone
would silently re-exclude these todos from ingestion — the exact defect tracked in
`/plans/active/issues/ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md`.

**Scope note — what this edit does NOT do.** Releasing the hold does not flip `assigned_vm`. Both todos were verdicted
**RECLASSIFY** on the merits in Phase 1 (bounded, stated done-whens, no authority call — todo 1 even names the proven
`auto_unpark__<task-id>` mechanism to reuse), so they now look reclassify-eligible with nothing blocking them. But
deciding whether a doc's own `assigned_vm: NA` classification should change is `/na-eligibility-audit`'s remit, not
`/plan-reconcile`'s — this pass clears the blocker and hands the reclassification question there rather than
self-authorising it. The two-part implementation itself remains open and undone.

Both open `[BACKEND] P3` todos were verdicted **RECLASSIFY** in Phase 1: they are bounded, with stated done-whens, no
operator gate and no undecided authority call — todo 1 even names the proven mechanism to reuse (the
`auto_unpark__<task-id>` prereq that `sports_satellite_ao_dispatch_batch2-011` already uses and the dispatcher already
honors), and todo 2 is a pure code-read-and-document with a determinable outcome.

**They were NOT flipped, because Phase 2's conflict-check did not clear them.** Both sides:

- **This doc** would change the dispatcher/park path so an external-ref gate produces a durable park, and would document
  why a `priority_override` park does not survive re-derivation while a named `auto_unpark__` prereq does.
- **`/plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md`** (ACTIVE, `assigned_vm: planning`) carries
  an OPEN `[BACKEND] P3`: "Audit every `/skip-current-task` `reason_code` for a silent, unpaged durable park … Read the
  skip handler in `agent-orchestrator/server/routes/slots_ops.py` and `server/auto_park.py::maybe_auto_park` (plus
  `_ESCALATING_REASON_CODES`)". It is **AUDIT-ONLY** by its own wording ("do NOT change `auto_park.py` in this todo") —
  so this is a file-collision + sequencing overlap rather than a verbatim duplicate claim, the same class batch1 itself
  used to defer the AutoSpawn no-eligible-worker gap ("FILE-COLLISION-gated only").

Notably, batch1's audit todo ends "if the audit finds an uncovered code, file it as a NEW tracked todo in the source doc
instead" — an external-promote gate is plausibly exactly such an uncovered code, so the two could converge into one item
rather than two.

- **A: Sequence — let batch1's audit-only pass land first, then dispatch this doc against its findings. [WORKER REC]**
  The audit is read-only and cheap, it enumerates every `reason_code`'s park/paging coverage, and its output is the
  natural specification for this doc's fix. Zero collision risk and it may fold both todos into one well-scoped change.
- **B: Flip this doc to `planning` now** and rely on the two workers not colliding (batch1's todo is read-only, so the
  risk is moderate rather than severe) — faster, but two agents would be reasoning about `auto_park.py` concurrently
  with no shared conclusion.
- **C: Fold these two todos into `ao_satellite_ao_dispatch_batch1_2026_07_26.md`** so one plan owns the whole
  `auto_park.py` surface.
- **Other**: operator may specify a different sequencing.

## Triage / charter note

Main (agt-52bb99) diagnosed read-only (per-task `/api/backlog` + `/blockers` + `git merge-base` ancestry) and is
charter-barred from editing dispatch/task state, hand-parking tasks, or hand-editing backlog.yaml. Severity **P3**: low
blast radius (cheap check-and-release per re-dispatch, self-terminates the moment the promote lands — which the
DEVOPS-owned treadmill fix will do), but a real, repeatable dispatch-noise + throughput gap that also defeats the "pick
up other work" guidance by handing the SAME gated task back to each freed worker. Filed per the big-finding triage rule
(cross-cutting dispatch gap, recurred 3x in one window). The durable-park mechanism already exists (auto_unpark) — this
is about routing external-gate tasks through it instead of through the churn path.

## Progress Log

- **na-eligibility-audit 2026-07-30**: Both todos RECLASSIFY-verdicted in Phase 1 but **HELD at Phase 2 (conflict) —
  parked as BLOCKED-OPERATOR-DECISION**, see the `## Deferred — HELD by the /na-eligibility-audit ao conflict-check`
  section above for both sides, the three options and the marked recommendation. `assigned_vm` deliberately left `NA`
  pending that ruling.
- **2026-08-01 — GATE CLEARED.** The prerequisite audit (`ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s
  `[BACKEND] P3`, AUDIT-ONLY) is done — full per-`reason_code` table now in
  `/plans/archive/issues/gated_skip_park_no_slack_page_2026_07_25.md`'s Progress Log. Finding relevant to this doc's
  todo: the audit found **zero uncovered `reason_code` gaps** (BLOCKED/PARKED/GATED all page identically; OTHER never
  reaches durable-park), so this doc's implementation todo is not folding in a newly-discovered code — it proceeds
  exactly as scoped above. This doc is now unblocked to dispatch; not implemented in this pass (out of scope for the
  audit-only batch todo that was gating it).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — added
  `/plans/archive/issues/gated_skip_park_no_slack_page_2026_07_25.md`, the archived audit doc whose per-`reason_code`
  table this doc's own Progress Log names as the input the implementation todo proceeds against.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, CONFLICT-PARKED — RECLASSIFY held — sole remaining item verbatim-claimed
  by ao_satellite_ao_dispatch_batch6's open [BACKEND] P3 todo (same two-part durable-park mechanism, same done-when,
  source explicitly cited); batch6_finalize owns the checkbox flip. Parked as BLOCKED-OPERATOR-DECISION — dispatch
  through batch6, not a parallel flip.
- **2026-08-06 (operator session)**: **RECLASSIFIED `assigned_vm: NA` → `planning`.** Operator decided to dispatch this
  doc directly rather than route through `ao_satellite_ao_dispatch_batch6_2026_08_04.md` (which stayed `status: draft`,
  untouched) — no plan wrapper needed for a single bounded, already-scoped todo. Also cleaned the stale "GATED: do not
  start" prefix in the todo text itself (the gate cleared 2026-08-01; the prefix would have read as a live instruction
  to a fresh worker). If `ao_satellite_ao_dispatch_batch6_2026_08_04.md` is later activated, its own todo 3 (same
  source, same mechanism) should be dropped or marked superseded-by-this-doc to avoid double dispatch.
- **2026-08-06 (slot-6, infra worker)**: **IMPLEMENTED + SHIPPED.** agent-orchestrator@23bd0b3. Part 1 — documented the
  priority_override vs auto_unpark__ prereq dual mechanism in `server/auto_park.py` module docstring (priority_override
  survives regen since Defect B fix, but the auto_unpark__ prereq is the truly durable gate — stored in the
  prerequisites store independently of backlog.yaml, gates dispatch at pick_next_task level, survives all regen paths
  unconditionally). Part 2 — added `park_now: bool = False` field to `SkipCurrentTaskRequest`
  (`server/models/slots.py`), wired in the skip handler (`server/routes/slots_ops.py`) so a worker that detects an
  EXTERNAL gate calls `manual_park()` directly on the first skip, bypassing `maybe_auto_park`'s N-skip threshold. The
  task parks with BOTH priority_override AND auto_unpark__<task-id> prereq — the same durable recipe `auto_park.py`'s
  threshold escalation already uses, now triggerable on first encounter. Two new tests in `tests/test_auto_park.py`:
  manual_park succeeds with no prior cooldown row, and the maybe_auto_park (threshold-gated) vs manual_park (park_now)
  contrast. Full QG green (2507 passed, basedpyright 0/0/0).
