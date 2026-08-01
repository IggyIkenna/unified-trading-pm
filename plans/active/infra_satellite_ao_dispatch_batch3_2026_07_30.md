---
doc_type: plan
title:
  Infra satellite AO batch 3 — the last two conflict-clear extractions in the infra tranche (tranche hits the
  stop-iterating condition after this)
summary: >-
  Third AO-dispatch batch for the `infra` topic tranche, produced by `/ag-closeout-audit infra` (2026-07-30). The
  tranche's covering set is now real (batch1 active, batch2 active, both with gated finalize twins) and the same-day
  `/na-eligibility-audit infra` run already reclassified 21 NA docs to `assigned_vm: planning`, so the membership sweep
  (`generate_ag_closeout_audit_candidates.py --tranche infra`, itself fixed earlier today in
  `unified-trading-pm@6228cff7e`) returns only 6 docs never cited by any covering doc. All 6 were read end-to-end:
  exactly TWO carry conflict-clear, bounded, worker-determinable work, and both are partial carve-outs (each source doc
  keeps its own judgment-gated remainder at `assigned_vm: NA`). The other 4 are non-batchable by the skill's own
  taxonomy — event-timing-gated, operator-scoping-gated, blast-radius-judgment-gated, and design-preference-gated
  respectively. This is a deliberately thin batch, and the audit's own conclusion is that a batch4 could not extract
  anything new: after these two land, every remaining orphaned infra doc's open work is PURELY non-batchable, which is
  the skill's explicit stop-iterating condition.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, satellite-docs, batch-3, plan-hygiene, tooling-safety, fleet-monitoring]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch3_finalize_2026_07_30.md,
    /plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/infra_satellite_ao_dispatch_batch2_2026_07_27.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md,
    /plans/active/issues/git_health_not_clean_since_pinned_constant_2026_07_27.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.7
estimate_calibrated_ai_days: 0.56
assigned_role: infra
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/infra_satellite_ao_dispatch_batch3_finalize_2026_07_30.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit infra` run 2026-07-30. Phase 0.3 (Orthogonality HARD CHECK) shipped separately earlier the same
  day (`unified-trading-pm@ae6e6c2c9`, 2 asset_group mistags fixed). This is the run's Phase 3 output: the
  iterative-drain re-check of batch1's and batch2's own Deferred sections found NOTHING newly cleared, so both
  extractions below come from fresh Phase-1 triage of the 6 never-cited orphans.
---

# Infra satellite AO batch 3

> **⚠️ STATUS: `draft` — NOT dispatched, NOT ingested.** Flipping this (and its finalize twin) to `status: active` is
> the operator's call per CLAUDE.md § "Plan destination — ASK BEFORE CREATING" and the `/ag-closeout-audit` skill's
> autonomous-mode rule. Nothing here has been shipped.

## Why this batch is thin — and why it is the last one

The infra tranche's dispatch layer is no longer the zero-todo digest that batch1 was authored against:

- `infra_satellite_ao_dispatch_batch1_2026_07_26.md` — `status: active`, 22 open of 25 todos, gated finalize twin.
- `infra_satellite_ao_dispatch_batch2_2026_07_27.md` — `status: active`, 9 open todos, gated finalize twin.
- `infra_consolidated_closeout_2026_07_25.md` — now carries 3 real `[REVIEW]` Track close-out criteria (added per
  `issues/autonomous_session_operator_decisions_2026_07_25.md` entry #38), so the hub is a measurable covering set.
- The same-day `/na-eligibility-audit infra` run reclassified **21** `assigned_vm: NA` docs to `planning` with gated
  finalize twins (`unified-trading-pm@4c6587543`) — those docs are now their own dispatch vehicles and are correctly out
  of scope for a batch extraction.

Against that covering set, `generate_ag_closeout_audit_candidates.py --tranche infra` reports **32 members / 7 covering
docs / 6 never cited in any real covering doc**. Every one of the 6 was read end-to-end (per-doc read, not a checkbox
count). Two yielded conflict-clear bounded work; four did not. See the disposition table below.

**Stop-iterating assessment (SKILL.md § "The `batchN` methodology", rule 3).** After the two todos below, the residual
open work across all 6 orphans is PURELY from the non-batchable taxonomy (event-timing-gated · operator-scoping-gated ·
blast-radius-judgment-gated · design-preference-gated · the two partial carve-outs' own judgment remainders). A batch4
could not extract anything new without either a new orphan appearing or one of the standing operator questions being
answered. **Recommendation to the operator: report the residual as "needs direct human action, not another batch" rather
than scheduling a batch4 against this tranche.**

## Why a batch + finalize PAIR rather than a single thin plan

Considered and rejected: the same-day sibling `/plans/archive/2026_07/ci_satellite_ao_dispatch_batch3_2026_07_30.md`
shape (one plan, no finalize twin, archival folded into the single todo's done-when — since archived, its work verified
already complete under separate dispatch). That shape is only available under `task_template.md` §4's **single-todo**
carve-out, which `scripts/quality_gates/check_finalize_plan_coverage.py` implements literally (`_todo_count(...) <= 1`,
and it filters on `assigned_vm: planning` — NOT on `status`, so a `draft` plan counts too). Measured on this tree before
authoring: the check reports **0 violations at baseline 0**, so a 2-todo `assigned_vm: planning` plan with no gated twin
would be a **hard regression (exit 1)**, not a warning. Artificially fusing the two todos into one to qualify for the
carve-out was also rejected — they are in different repos (`unified-trading-pm` vs `agent-orchestrator`), share no file
and no dependency, and fusing them would serialize unrelated work onto one worker purely to dodge a gate. So: a real
pair, with a genuinely small finalize twin (`infra_satellite_ao_dispatch_batch3_finalize_2026_07_30.md`).

The twin also does real work here rather than being ceremony: **neither source doc becomes archivable** when its
extracted item lands (each keeps judgment-gated todos at `assigned_vm: NA`), so the finalize step must reconcile
checkboxes _without_ archiving — precisely the distinction `task_template.md` §4 exists to get right.

## Rules this plan follows

- Every todo ends with `Source: <doc> #<original-item-number>` plus an explicit **Done when** clause.
- Both todos are **partial carve-outs** per
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 1a: the bounded items land here, the
  source docs are NOT retagged and stay `assigned_vm: NA` for their remaining judgment-call items. This does not
  contradict the same-day `/na-eligibility-audit infra` KEEP-NA verdicts on both docs — those verdicts are about each
  DOC's `assigned_vm`, which is unchanged; the git-health verdict explicitly notes its "diagnostic todos feed directly
  into" the design call, which is exactly what todo 2 extracts.
- `sequential:` deliberately unset — the two todos touch disjoint repos and files and are independently dispatchable.
- The source docs' own checkboxes are NOT touched by this plan — the finalize twin does that once each todo is `[x]`.

## Todos

- [x] ✅ [SCRIPT] P2. **Make `scripts/workspace/sync-gitignore-cursorignore.py --dry-run` actually gate every write.** —
      `unified-trading-pm@78a3740bf`: gated the `.gitignore`/`.cursorignore` writes + the chained
      `untrack-ignored-files.py` call behind `dry_run` (prints "would update" instead of writing; forwards `--dry-run`
      not `--untrack` downstream). Regression test `tests/unit/test_sync_gitignore_cursorignore_dry_run.py` (4 cases)
      proves zero writes under `--dry-run` + correct flag forwarding. Live-verified:
      `--dry-run --repo unified-trading-pm` + a `git status --short -- .gitignore .cursorignore` sweep across all 25
      slot repos afterward showed zero diffs. `quality-gates.sh` green at this SHA. Verified live at HEAD 2026-07-30
      (re-read the file, do not trust this restatement): `main()` calls `gitignore_path.write_text(...)` /
      `cursorignore_path.write_text(...)` unconditionally (~L294-296, printing `Updated <repo>/`), then unconditionally
      shells out to `untrack-ignored-files.py --untrack` (~L327-334); the `dry_run` flag is consulted **only** inside
      the `--purge-history` branch (~L305-321). The module docstring at L13 already promises "Preview changes without
      writing anything", so this aligns behaviour with an already-documented contract rather than inventing one. Note
      the callee already supports report-only mode — but its gate is
      `dry_run = "--dry-run" in sys.argv and "--untrack" not in sys.argv` (`untrack-ignored-files.py` ~L54-58), so the
      caller must pass `--dry-run` **without** `--untrack`, not both. **Scope guard**: flag-gating only. Do NOT touch
      `scripts/templates/.gitignore.central` or attempt the template↔PM-live reconciliation — that is the source doc's
      todo 2, explicitly self-described as per-line human judgment, and it stays NA. Repo: unified-trading-pm. Source:
      `issues/gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md` #1 (`[SCRIPT] P2`, first of
      3). **Done when**: (a) a `--dry-run` invocation performs zero mutation — proven by a `git status --short` sweep
      across all 25 repos showing zero `.gitignore`/`.cursorignore` diffs, zero newly-created `.cursorignore`, and zero
      `D `-flagged index entries afterwards; (b) the chained untrack call runs in report-only mode under `--dry-run`;
      (c) the printed output says "would update" rather than "Updated" in that mode; (d) a regression test under PM's
      `tests/unit/` proves the write path is not reached when `--dry-run` is set; (e) `bash scripts/quality-gates.sh` is
      green.
- [ ] [BACKEND] P3. **Root-cause the fleet git-health `not_clean_since` pinned-constant and record a verdict** (the
      source doc's two diagnostic todos, combined: #2's answer depends on #1's, and both read the same
      reporter→route→aggregation data path). Three candidate mechanisms, named by the source doc itself — (i) the
      reporter posts a non-refreshing `reported_at` (`unified-trading-pm/scripts/dev/slot-git-status-report.sh` takes it
      as `sys.argv[3]` ~L402 and emits it ~L432, a single traceable hop); (ii) the fleet-aggregation view collapses to
      one global snapshot's value instead of the per-`(host, slot, repo)` `SlotGitStatusRow` value
      (`agent-orchestrator/server/routes/git_health.py`, `_propagate_not_clean_since` ~L74, `req.reported_at` threaded
      ~L243-272, read back ~L290/L322/L351); (iii) the **already-shipped** `dirty_consecutive_ticks >= 2` hysteresis
      confirm-gate (`agent-orchestrator@2530316`, flipped `[x]` in `ao_satellite_ao_dispatch_batch1_2026_07_26.md`) is
      simply never clearing for repos edited on-and-off all day — in which case the field is behaving as documented and
      is merely useless for one-shot "dirty just now vs hours ago" checks. **Test (iii) FIRST** — it is the cheapest and
      it is the one hypothesis that has changed since the doc was filed. The archived flicker doc's narrowing rule ("do
      NOT re-hunt a reporter-internal race unless a post-`agent-orchestrator@529b0dc` recurrence is observed") does NOT
      block this: the 2026-07-27 observation IS a post-`529b0dc` recurrence — cite that explicitly in the verdict so a
      future reader does not re-close this as out-of-bounds. **Explicitly OUT of scope**: choosing between "bugfix the
      existing field" and "add a separate last-dirty-transition field" (source doc todo 3) — that is the field-design
      fork the `/na-eligibility-audit` ruled KEEP-NA. If the diagnostic makes exactly one answer provably right, record
      it as a _recommendation_ in the source doc; do not implement it. Repos: agent-orchestrator (diagnosis; a code
      change only if the verdict is (i) or (ii) and the fix is a like-for-like correction, not a schema/field addition),
      unified-trading-pm (read-only). Source: `issues/git_health_not_clean_since_pinned_constant_2026_07_27.md` #1 + #2.
      **Done when**: a written verdict in that doc's Progress Log names WHICH mechanism produces the constant, cites the
      specific file+line and a reproduction (e.g. two `/api/fleet/git-health` reads spanning a real dirty→clean→dirty
      transition on one slot), and states whether any code changed; if code changed, `quality-gates.sh` is green in the
      touched repo.

## The other 4 orphans — why they are NOT batch3 todos

| doc                                                                                           | residual open work                                                                   | non-batchable category                                                                                                                                                                                                                                                                                                                                              |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `issues/legacy_bucket_template_literals_2026_07_16.md`                                        | 1 todo — pay down 15 baselined `…-{project_id}` bucket-template literals             | **Event-timing-gated.** The doc's own Disposition section sequences each pay-down to "as each asset group reaches its own legacy-bucket decommission"; none of `features-onchain`/`-calendar`/`-store`/`-sports`/`instruments-store-tradfi` has. Not a decision waiting to be made — an event waiting to happen. The ratchet already prevents regression meanwhile. |
| `issues/s5_7_required_docs_gaps_2026_07_29.md`                                                | 3 todos — tier the S5.1 required-docs set by repo type, then fill/reconcile the gaps | **Operator-scoping-gated.** The doc self-classifies as "a scoping judgment … not a bounded worker todo", and todo 1's own text ends "— OPERATOR/main scoping decision first"; todos 2 and 3 are both sequenced behind it.                                                                                                                                           |
| `issues/vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md`                                  | 3 todos, all `[HUMAN]`-tagged — Class-B stall-kill + naming-heuristic widening       | **Blast-radius-judgment-gated.** Each requires the whole-fleet naming-collision review the parent issue doc's own rule mandates before touching the shared `_is_backfill_vm()`; that widening was _explicitly rejected as out-of-scope_ for the narrower Gap-3 fix, and a false positive against a legitimately-continuous live/paper VM name is the failure mode.  |
| `issues/na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md` | 1 todo of 4 (other 3 `[x]`, `unified-trading-pm@6228cff7e`)                          | **Design-preference-gated.** The remaining P3 is literally "Evaluate bundling … consider extracting one shared membership-test module" — a preference call with no stated tiebreaker, so no worker-determinable outcome.                                                                                                                                            |

The two extracted docs are **partial** carve-outs, for the record:
`gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md` keeps todos 2 (template reconciliation,
human per-line judgment) and 3 (`[VERIFY] P3`, gated on todo 2);
`git_health_not_clean_since_pinned_constant_2026_07_27.md` keeps todo 3 (the field-design fork). Both stay
`assigned_vm: NA`.

## Deferred — batch1/batch2 re-check (iterative-drain step 1), nothing newly cleared

Measured 2026-07-30 against the live corpus, not carried forward on trust:

| id  | Item (batch1 Deferred numbering)                                                                                                                                               | Still gated because                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| G1  | #2 — the 4-item `base-service.sh`/`base-library.sh` serialized unit (RULED, entry #36 option A)                                                                                | The ruling declared those two files a **serialized resource, one owning plan at a time** — and two other tranches still hold live claims. `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` is `status: active` with its `[BACKEND] P3` MTDS retry_safe todo (sub-item 3 = generalize the lint into `base-service.sh`) still `- [ ]`; `ci_satellite_ao_dispatch_batch2_2026_07_29.md` claims `base-service.sh` (todo 1) and `base-library.sh` (todo 11) and additionally reserves a further `base-library.sh` change for a ci batch3. Infra cannot take ownership this round. Re-check once both land. |
| G2  | #3 — move the `0.10.8` constant into `resolve-canonical-versions.py`                                                                                                           | Same `base-service.sh`/`base-library.sh` contention as G1 (2 of its 3 hardcoded sites live there).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| G3  | #4 — deployment-ui `DATA_PIPELINE_SERVICES` (GAP G-UI) in `DataStatusTab.tsx`                                                                                                  | The entry-#35 ruling (option A) sequences infra behind cross-cutting: "let cross-cutting batch1 land `DataStatusTab.tsx` first, infra picks it up once quiet." Measured: `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` is `status: active` and its `[INFRA] P2` four-part todo — part (B) edits `DataStatusTab`/`HonestCoverageCard` — is still `- [ ]`. Not quiet yet.                                                                                                                                                                                                                             |
| G4  | #1 — MTDS ungated test families / `PYTEST_UNIT_DIR`                                                                                                                            | Still an unanswered operator question in the batch1 item-14 register (two prescribed approaches, one gated behind 22 currently-failing tests). Unchanged.                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| G5  | #5-#10 — `managed-by` labels · repo_scripts DEPRECATE · fastapi/starlette caps · MTDS >900 tail · the corpus-wide sweeps · the 2 sports-doc-split-blocked reference-path fixes | Unchanged since 2026-07-26: still subsumed by wider active claims, still dep-manifest/corpus-wide-scale, or still blocked on sports batches 3/5 splitting their own oversized docs.                                                                                                                                                                                                                                                                                                                                                                                                                              |
| G6  | batch2's sole Deferred item (`tradfi_backfill_throughput_followups_2026_07_24.md`)                                                                                             | Still owned by `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` (`status: active`), whose own "Done when" flips the source checkboxes. Not re-derived here — `infra_satellite_ao_dispatch_batch2_finalize_2026_07_27.md` already owns that re-check.                                                                                                                                                                                                                                                                                                                                                          |

## Conflict check performed before drafting

- **`scripts/workspace/sync-gitignore-cursorignore.py` / `untrack-ignored-files.py` /
  `scripts/templates/.gitignore.central`** — `rg` across all of `plans/active/` (plans + issues) returns **zero** other
  claimants. Clean.
- **`agent-orchestrator/server/routes/git_health.py` / `scripts/dev/slot-git-status-report.sh`** — checked against every
  active `parent_epic: orchestrator_master` planning doc (todo 2's source doc lives in that epic, not
  `infrastructure_master`). `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s two git-health todos are both `[x]` done
  (the loopback-preference fix and the `dirty_consecutive_ticks>=2` gate).
  `ao_satellite_ao_dispatch_batch2_2026_07_30.md` has one adjacent `[INFRA] P3` — re-mint a stale `~/.orch_token` on one
  host — which its own text scopes as a credential/host action with "no code change expected", and its
  `_track_dirty_tick` mention sits in its Deferred section describing an already-shipped, already-archived doc.
  **Adjacent subsystem, no file-level collision.**
- **Pairwise across the 2 todos below** — disjoint repos, disjoint files. No collision.
- **`check_delete_vm_launch_gating.sh` shape** — neither todo performs a GCS delete, an `--apply`, or a VM launch, so no
  `[OPERATOR]` tag or delete-safety citation is required.

## Codex SSOTs (read before executing a todo)

- `/codex/06-coding-standards/quality-gates.md` — how gates run; never `pytest` directly
- `/codex/06-coding-standards/script-homes.md` — `scripts/` ownership + lifecycle markers (todo 1's file)
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 1a — the partial-carve-out shape both
  todos use
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the bar the 4
  non-extracted orphans fail
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step ritual the finalize twin runs
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this pair satisfies

## Progress Log

- **2026-07-30** — Drafted by `/ag-closeout-audit infra`, Phase 3. Phase 0 re-derived the covering set (batch1 active +
  batch2 active + both gated finalize twins + the hub's 3 `[REVIEW]` Track criteria) and used
  `generate_ag_closeout_audit_candidates.py --tranche infra` directly — the membership bug that made ao/ci/infra sweeps
  unreliable was fixed earlier today (`unified-trading-pm@6228cff7e`, verified present on this tree). Phase 0.3's
  Orthogonality HARD CHECK shipped separately this morning (`unified-trading-pm@ae6e6c2c9`). Iterative-drain step 1
  (re-check batch1/batch2 Deferred before fresh triage) found **nothing newly cleared** — the two ruled-but-still-gated
  clusters (G1 `base-service.sh` serialization, G3 `DataStatusTab.tsx` sequencing) were each re-verified against the
  live checkbox state of the competing plan, not assumed. Fresh Phase-1 read of all 6 never-cited orphans end-to-end
  produced exactly 2 conflict-clear bounded extractions, both partial carve-outs. Both source docs' code claims were
  re-verified against the live tree before drafting (the `--dry-run` write path and the unconditional untrack call were
  read directly; `git_health.py`'s `_propagate_not_clean_since` and the reporter's `reported_at` argv hop were both
  confirmed present). Left `status: draft` deliberately — the flip is the operator's call. Nothing shipped.
- **2026-07-30** — Recorded the stop-iterating verdict above: this is expected to be the infra tranche's **last**
  satellite batch. A batch4 has no material to extract unless a new orphan appears or one of the standing operator
  questions (G1/G3/G4, plus the `s5_7` scoping call) is answered.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
