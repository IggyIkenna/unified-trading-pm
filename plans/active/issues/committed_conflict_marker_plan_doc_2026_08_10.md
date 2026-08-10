---
doc_type: issue
title:
  Committed git conflict markers reached LDR in a plan doc (multi_leg_execution_systems_audit) — hygiene gate did not
  fire; concurrent same-file Progress-Log appends were the root cause
summary: >-
  slot 31's commit unified-trading-pm@505bfe3ced (flip audit-plan todo 3) reached live-defi-rollout with committed
  conflict-marker debris in `plans/active/multi_leg_execution_systems_audit_2026_08_10.md`: an orphaned mid-doc
  `=======` line + a trailing conflict-close marker line, a dropped todo-4 Progress-Log line ("live Pub/Sub leg."), and
  a garbled duplicate "Prediction-arb engines specifically" tail. Repaired inline by slot 18 (git-history ground truth)
  in the commit that ships that audit's todo 5. A conflict-marker gate EXISTS (`check_conflict_markers.sh`, wired into
  `run_hygiene_sweep.sh` both `--precommit` staged-plans and full-sweep) yet the markers reached LDR — the staged-plans
  path did not fire for slot 31's commit shape. Root cause: the audit plan's todos 3/4/5 were concurrently dispatched to
  three slots but ALL append Progress-Log entries + flip checkboxes in the SAME plan doc, violating the workspace rule
  "concurrent todos MUST touch different files". (Marker strings are referenced here as "seven-`>`/`<`" to avoid
  tripping the same conflict-marker gate this doc describes.)
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, conflict-marker, concurrency, plan-authoring, shared-branch, hygiene-gate]
related:
  [
    /plans/active/multi_leg_execution_systems_audit_2026_08_10.md,
    /plans/active/issues/multi_leg_paper_batch_live_parity_gap_2026_08_10.md,
    /plans/active/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
  ]
created: 2026-08-10
author: claude-code (slot 18, tradfi data_engineering, multi_leg_execution_systems_audit todo 5)
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: cicd
drift_direction: none
depends_on: []
locked_by:
resolved_by:
source:
  [
    "Found live 2026-08-10 while slot 18 shipped `multi_leg_execution_systems_audit_2026_08_10.md` todo 5: the plan file
    already carried committed conflict-marker debris from slot 31's concurrent todo-3 flip (`505bfe3ced`) — confirmed on
    origin, not a working-tree artifact.",
  ]
context_scope:
  [
    /scripts/plan-hygiene/check_conflict_markers.sh,
    /scripts/plan-hygiene/run_hygiene_sweep.sh,
    /plans/active/multi_leg_execution_systems_audit_2026_08_10.md,
  ]
---

# Committed conflict markers reached LDR in a plan doc — hygiene gate did not fire

> **Notation note:** git conflict-marker strings are referenced here as "seven-`>` close marker" / "seven-`<` open
> marker" (and `=======` verbatim — that form is deliberately NOT flagged by the gate). This is because
> `check_conflict_markers.sh` matches the literal 7-character marker strings anywhere in a doc (mid-line or in
> backticks), so a doc that writes them verbatim trips the very gate it documents.

## What I found

**Slot 31's commit `505bfe3ced` (flip audit-plan todo 3) shipped committed conflict-marker debris to
`live-defi-rollout`** in `plans/active/multi_leg_execution_systems_audit_2026_08_10.md`:

1. An orphaned `=======` line (line ~238) inserted mid-Progress-Log, replacing the todo-4 entry's dropped final line
   ("live Pub/Sub leg.") — the parent commit (`1c3fe0f816`) shows the todo-4 entry correctly ended "...recommendation,
   not just the **live Pub/Sub leg.**".
2. A trailing conflict-close marker line (the seven-`>` form, suffixed with the committing commit's short sha) at the
   end of the todo-3 Progress Log entry (last line of the file).
3. A garbled duplicate tail inside the todo-3 entry: "**Prediction-arb engines specifically**: ...
   `ArbitrageCrossDomainEventEngine` (CME↔Polymarket, 1" + a dangling "(dated futures basis) in `carry_and_yield/`, and
   `StatArbPairsFixedEngine` in `stat_arb_pairs/`." — a truncated/mixed conflict-resolution artifact duplicating the
   entry's own clean "**"Prediction-arb engines" (plural)**" paragraph.

**Verified on origin** (via `git show origin/live-defi-rollout:...` + `git log -S` on the close-marker string →
introduced by `505bfe3ced`), not a working-tree artifact of my own edits. **Repaired inline by slot 18** (git-history
ground truth: parent `1c3fe0f816` restored the dropped todo-4 line; the orphaned `=======` + close-marker debris and the
garbled duplicate tail were removed) in the same commit that ships the audit's todo-5 flip.

**The conflict-marker gate EXISTS but did not fire for this commit.** `scripts/plan-hygiene/check_conflict_markers.sh`
(catches the seven-`<` open and seven-`>` close markers incl. mid-line + the prettier-mangled spaced form; deliberately
does NOT match `=======` — a 7+ `=` run collides with setext-H1 underlines, per its header) is wired into
`scripts/plan-hygiene/run_hygiene_sweep.sh` BOTH in the `--precommit` staged-plans path (line ~95,
`check_conflict_markers.sh --quiet "${STAGED_PLANS[@]}"`) and in the full-sweep body (line ~336, `run_check ... hard`).
The `plan-hygiene` pre-commit hook (`.pre-commit-config.yaml` line ~91) runs the sweep `--precommit` on staged
`plans/`/`codex/` files. Yet the committed close-marker line reached LDR — so the staged-plans check did NOT run (or ran
with an empty `STAGED_PLANS`) for slot 31's commit shape. That specific wiring gap needs a bounded verification (todo
1).

**Root cause is the plan-authoring/dispatch shape, not a git defect.** The audit plan's todos 3, 4, 5 are all
same-priority `[DATA] P1` and were dispatched CONCURRENTLY to three slots (31 → todo 3, another → todo 4, 18 → todo 5),
and ALL three append Progress-Log entries + flip checkboxes in the SAME file
(`multi_leg_execution_systems_audit_2026_08_10.md`). That violates the workspace rule "concurrent todos MUST touch
different files". Slot 31's rebase/merge resolution against a peer's earlier commit botched the file — this is the same
shared-plan-file contention class that already produced
`quickmerge_concurrent_same_file_edit_blind_overwrite_2026_08_08.md`.

## Why it matters

- Committed conflict markers are corrupt content on the shared integration branch: they read as plausible-ish markdown,
  can double/mangle todos (the 2026-06-21 precedent in `check_conflict_markers.sh`'s own header), and mislead any reader
  of the plan. A plan doc carrying conflict-marker debris is not valid SSOT content.
- The gate's coverage has a KNOWN blind spot even on a correctly-run sweep: `=======` is deliberately un-checked (setext
  collision), so the orphaned middle-marker form can reach LDR even when the sweep runs. The close-marker (`>`) form
  SHOULD have been caught — its non-firing is the actionable gap.
- The concurrent-same-file Progress-Log-append pattern is a standing hazard for multi-todo audit plans dispatched to
  parallel slots; this plan's todos 3/4/5 should not have been concurrently dispatched against one file.

## Recommended decision

1. Verify + close the gate gap: reproduce slot 31's commit shape (quickmerge `--agent` on the AO VM, marker-bearing
   staged plan) against `run_hygiene_sweep.sh --precommit` and confirm whether `STAGED_PLANS` is populated; fix so a
   committed marker can never reach LDR regardless of commit path.
2. Narrow `check_conflict_markers.sh`'s `=======` exclusion so an ORPHANED `=======` debris line (not serving as a
   setext-H1 underline directly under an H1 text line) is caught — the corpus uses ATX (`##`) headers, so a setext
   underline is already non-canonical.
3. Process note (tracked via todo 3): audit active plans for the same concurrent-same-file shape and mark them
   `sequential: true` or split so parallel slots never append to one plan doc's Progress Log simultaneously.

## Todos

- [ ] [DEVOPS] P1. **Verify why the committed-conflict-marker gate did not fire on `unified-trading-pm@505bfe3ced`**
      (slot 31's `multi_leg_execution_systems_audit_2026_08_10.md` todo-3 flip, which shipped a committed close-marker
      line + orphaned `=======` to LDR). The `--precommit` staged-plans check (`run_hygiene_sweep.sh` line ~95,
      `check_conflict_markers.sh --quiet "${STAGED_PLANS[@]}"`) should have caught it. Reproduce the exact commit shape
      (quickmerge `--agent` on the AO VM against a marker-bearing staged plan) and determine whether `STAGED_PLANS` is
      populated for that path; if empty-by-design for some commit shape, fix the sweep to scan the staged file
      regardless. Done when: a marker-bearing plan committed via the same path is REJECTED pre-push, with the gap
      identified + closed (or a documented, intentional exclusion). (repo: unified-trading-pm)
- [ ] [DEVOPS] P2. **Narrow `check_conflict_markers.sh`'s `=======` exclusion** so an ORPHANED mid-doc `=======` line (a
      committed `=======` NOT directly under an H1 text line as a setext underline — the corpus uses ATX headers, so a
      genuine setext underline is already non-canonical) is flagged as conflict-marker debris. Keep the
      setext-H1-underline false-positive guard. Done when: a fixture with an orphaned `=======` in a Progress Log fails
      the check, and a genuine `Title` + setext-underline form still passes. (repo: unified-trading-pm)
- [ ] [DOCS] P2. **Scan active plans for the concurrent-same-file-Progress-Log shape** that corrupted
      `multi_leg_execution_systems_audit_2026_08_10.md`: multiple same-priority `- [ ]` todos in ONE plan doc that each
      append a Progress-Log entry + flip a checkbox in that same doc (concurrent dispatch → parallel slots edit one
      file). For each hit, flip the plan to `sequential: true` (a genuine same-file dependency) or split the todos so
      concurrent workers touch different files. This plan's todos 3/4/5 are the concrete first instance. Done when: the
      audit plan's remaining structure is sequential-if-reused and the scan finds no other active plan with >1
      same-file-editing concurrent todo. (repo: unified-trading-pm)

## Progress Log

- **2026-08-10 (slot 18)**: filed after shipping the audit plan's todo 5, where the working tree's `git checkout HEAD`
  (to recover from the slot-31/18 safe-doc-push conflict) exposed the already-committed debris on origin. Repaired the
  plan doc inline (git-history ground truth) in the same commit as the todo-5 flip; the repair is documented in that
  plan's Progress Log entry. This doc tracks the durable gate/planning fixes. Note: the first draft of this doc wrote
  the marker strings verbatim and tripped `check_conflict_markers.sh` (the gate matches mid-line/in-backtick); rewritten
  with the seven-`>`/seven-`<` notation above.
