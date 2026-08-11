---
doc_type: issue
title:
  Committed git conflict markers reached LDR in a plan doc (multi_leg_execution_systems_audit) — hygiene gate did not
  fire; concurrent same-file Progress-Log appends were the root cause
summary: >-
  slot 31's commit unified-trading-pm@505bfe3ced (flip audit-plan todo 3) reached live-defi-rollout with committed
  conflict-marker debris in `plans/archive/2026_08/multi_leg_execution_systems_audit_2026_08_10.md`: an orphaned mid-doc
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
    /plans/archive/2026_08/multi_leg_execution_systems_audit_2026_08_10.md,
    /plans/archive/issues/multi_leg_paper_batch_live_parity_gap_2026_08_10.md,
    /plans/active/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
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
archive_exempt: true
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
    /plans/archive/2026_08/multi_leg_execution_systems_audit_2026_08_10.md,
  ]
---

# Committed conflict markers reached LDR in a plan doc — hygiene gate did not fire

> **Notation note:** git conflict-marker strings are referenced here as "seven-`>` close marker" / "seven-`<` open
> marker" (and `=======` verbatim — that form is deliberately NOT flagged by the gate). This is because
> `check_conflict_markers.sh` matches the literal 7-character marker strings anywhere in a doc (mid-line or in
> backticks), so a doc that writes them verbatim trips the very gate it documents.

## What I found

**Slot 31's commit `505bfe3ced` (flip audit-plan todo 3) shipped committed conflict-marker debris to
`live-defi-rollout`** in `plans/archive/2026_08/multi_leg_execution_systems_audit_2026_08_10.md`:

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

- [x] ✅ [DEVOPS] P1. **Verify why the committed-conflict-marker gate did not fire on `unified-trading-pm@505bfe3ced`**
      (slot 31's `multi_leg_execution_systems_audit_2026_08_10.md` todo-3 flip, which shipped a committed close-marker
      line + orphaned `=======` to LDR). **Gap identified + closed** — `unified-trading-pm@caae76d29e`. The
      `check_conflict_markers.sh` gate had ONLY one line of defense: the pre-commit hook
      (`run_hygiene_sweep.sh --precommit`). It was absent from `quality-gates.sh`, `ldr-docs-gate.yml`, and every CI/CD
      workflow. `--diff-filter=ACM` IS populated for modified plan files (confirmed via reproduction), and the checker
      DOES catch `seven-`>` close-marker` markers (confirmed). So the gate works when the pre-commit hook fires — but
      any bypass (`git rebase --continue` after manual conflict resolution, `--no-verify`, a prek race condition on
      shared checkouts) lets markers reach LDR with no second line of defense. **Fix**: wired
      `check_conflict_markers.sh` into (1) `quality-gates.sh` — scoped to the changeset (same pattern as the frontmatter
      schema check), catching markers at Pass-1 QG before quickmerge push; (2) `ldr-docs-gate.yml` — the hourly
      post-push corpus scan, catching any markers that bypassed BOTH the pre-commit hook AND QG within one hour of
      landing on LDR. See Progress Log for full investigation details. Done when: a marker-bearing plan committed via
      the same path is REJECTED pre-push, with the gap identified + closed (or a documented, intentional exclusion).
      (repo: unified-trading-pm)
- [x] ✅ [DEVOPS] P2. **Narrow `check_conflict_markers.sh`'s `=======` exclusion** — `unified-trading-pm@9b7e2cc451`.
      Added an awk-based orphaned-`=======` check: lines of 7+ `=` signs NOT directly under a non-empty text line
      (setext-H1 guard) and shorter than 30 chars (separator-line guard) are flagged as conflict-marker debris. Tested:
      orphaned `=======` → exit 1 (caught); `Title\n=======` setext → exit 0 (skipped); `======...======` (42 chars)
      separator → exit 0 (skipped); combined `=======` + `seven-`>` close-marker` fixture → exit 1 (both caught). Full
      810-file corpus clean (exit 0). Done when: a fixture with an orphaned `=======` in a Progress Log fails the check,
      and a genuine `Title` + setext-underline form still passes. (repo: unified-trading-pm)
- [x] ✅ [DOCS] P2. **Scan active plans for the concurrent-same-file-Progress-Log shape** that corrupted
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
- **2026-08-10 (slot 6, cicd)**: todo 1 investigation + fix shipped (`unified-trading-pm@caae76d29e`). **Root cause**:
  `check_conflict_markers.sh` was wired ONLY into the pre-commit hook (`run_hygiene_sweep.sh --precommit`). Verified via
  reproduction: `--diff-filter=ACM` correctly captures modified plan files, `check_conflict_markers.sh` correctly
  catches `seven-`>` close-marker` markers (exit 1), and `prek` fires the plan-hygiene hook on commit (confirmed by
  committing a marker-bearing test file — rejected with "❌ Conflict marker(s) in staged plans"). So the gate mechanism
  works when invoked. **But it had ZERO presence in**: (a) `quality-gates.sh` — the Pass-1 QG gate that runs before
  quickmerge push, (b) `ldr-docs-gate.yml` — the hourly post-push corpus scan added after the 2026-07-17 fail-open
  incident, (c) any CI/CD GitHub Actions workflow. The standard `check for merge conflicts` pre-commit hook only catches
  the full `seven-`<` open-marker` + `=======` + `seven-`>` close-marker` triple — `505bfe3ced` only had `=======` +
  `seven-`>` close-marker` (no open marker), so it passed. **The pre-commit hook is the SOLE line of defense** — any
  bypass (`git rebase --continue` after manual conflict resolution, `--no-verify`, a prek race condition on shared
  checkouts) lets markers reach LDR undetected. **Fix**: wired `check_conflict_markers.sh` into `quality-gates.sh`
  (changeset-scoped, same pattern as the frontmatter schema check — catches markers at Pass-1 QG before quickmerge push)
  AND into `ldr-docs-gate.yml` (hourly corpus scan — catches any markers that bypassed BOTH the pre-commit hook AND QG
  within one hour of landing on LDR). Pre-commit hook presence confirmed in ALL 12 slots (all `.git/hooks/pre-commit`
  mtimes Jul 7 13:41; slot 31's was Aug 8 13:07). Slot 31's clone has the same `.pre-commit-config.yaml` as slot 6
  (diff-empty). `prek` 0.4.12 installed Jul 30. The marker hash `86e965852f` (from the `seven-`>` close-marker` line) is
  unreachable in the current clone — consistent with a rebase-created commit whose original hash was garbage-collected.
  **Deferred to P2 todos**: (a) narrowing the `=======` exclusion in `check_conflict_markers.sh` to catch orphaned
  mid-doc `=======` lines, (b) scanning active plans for the concurrent-same-file-Progress-Log shape.
- **2026-08-10 (slot 6, cicd)**: todo 2 shipped (`unified-trading-pm@9b7e2cc451`). Added awk-based orphaned-`=======`
  check to `check_conflict_markers.sh`. Lines matching `^={7,}$` are flagged UNLESS (a) the previous line is a non-empty
  text line (setext-H1 underline guard), or (b) the line is ≥30 `=` chars (visual separator convention). Three fixtures
  verified: orphaned `=======` → exit 1 (caught), `Title\n=======` setext → exit 0 (correctly skipped),
  `======...======` 42-char separator → exit 0 (correctly skipped). Combined `seven-`>` close-marker` + orphaned
  `=======` fixture → exit 1 (both caught, separate messages). Full 810-file plans corpus clean (exit 0). The original
  open/close marker PAT is unchanged — this only adds the middle-marker detection that was the proven blind spot in
  `505bfe3ced`.
- **2026-08-10 (slot 6, cicd)**: todo 3 shipped. **Scan results**: 38 active `assigned_vm: planning` plans with >1
  same-priority unchecked todo AND NOT `sequential: true`. Categorized into:
  - **8 HIGH-risk non-batch plans** (≥3 same-priority unchecked todos, genuine work plans where concurrent same-file
    editing is dangerous): `sports_taxonomy_p2_migration_2026_08_08.md`,
    `strategy_archetype_latency_deployment_profile_audit_2026_08_10.md`,
    `strategy_archetype_latency_deployment_profile_execution_2026_08_10.md`,
    `multi_leg_execution_systems_execution_2026_08_10.md`, `sports_taxonomy_p4_backfill_2026_08_08.md`,
    `sports_closeout_track_s2_foldin_2026_07_25.md` (had `sequential: false` — flipped to `true`),
    `sports_group_c_execution_backtest_harness_2026_07_21.md`,
    `tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md` — **all marked `sequential: true`**.
  - **4 MEDIUM-risk non-batch plans** (2 same-priority unchecked todos): `codex_vs_repo_docs_ssot_audit_2026_06_01.md`,
    `data_pipeline_check_mdps_features_2026_07_20.md`, `sports_fixture_grain_catalogue_build_2026_08_10.md`,
    `sports_track_h_denominator_prereqs_2026_07_28.md` — **all marked `sequential: true`**.
  - **10 HIGH-risk satellite dispatch batch / finalize plans** (≥3 same-priority): LEFT AS-IS — each todo targets a
    DIFFERENT repo (structurally designed for parallel dispatch); the plan-flip + Progress-Log append still contends on
    the same file but the work is in different repos and each edit is a one-line append that git can typically
    auto-merge.
  - **16 MEDIUM-risk satellite dispatch batch / finalize plans**: LEFT AS-IS — same reasoning.
  - **`multi_leg_execution_systems_audit_2026_08_10.md`** (the concrete first instance): all 6 todos now checked off;
    marked `sequential: true` for future reference.
  - **Post-fix re-scan**: 0 non-batch, non-satellite active plans with >1 same-priority unchecked todo that aren't
    `sequential: true` — the remaining 26 satellite/finalize plans are structurally exempt (each todo touches different
    repos; the Progress-Log append is a one-line edit; git auto-merge handles non-overlapping appends correctly).
  - **`archive_exempt: true`**: all 3 todos now closed but this issue was created AND resolved today (2026-08-10) — keep
    active through the next plan-reconcile cycle so the operator can review the concurrent-same-file scan findings and
    the `sequential: true` fix across 12 plans before archival.
