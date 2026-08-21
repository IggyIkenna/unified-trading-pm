---
doc_type: issue
title: tradfi_consolidated_closeout_2026_07_18.md is over the 1000-line hard cap, blocking routine content edits
summary: >-
  `plans/active/tradfi_consolidated_closeout_2026_07_18.md` is 1005 lines (over the 1000L hard cap enforced by
  `check_line_caps.sh` in the prek plan-hygiene gate). A same-day session (2026-08-09) tried to land a routine,
  net-zero-line MVP-cell table row update (correcting the "S&P index options" row with an accurate manifest count-check,
  per `tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`'s third finding) and was blocked
  by `check_line_caps.sh`'s HARD gate despite the edit adding zero net lines (a same-line table-cell content
  substitution, git-diffed as 1 deletion + 1 addition — the file was already at/over 1005L before the edit, and any
  staged touch to an already-over-cap file trips the gate). Same root-cause CLASS as
  `plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md` (a DIFFERENT closeout doc,
  `cross_cutting_consolidated_closeout_2026_07_25.md` at 1007L, blocked on a link-archival edit) — that doc's own
  analysis found `check_line_caps.sh`'s only scoped-mode carve-out requires `DELETED=0` in the staged diff, which a pure
  content substitution can never satisfy (git diffs at line granularity: swapping one table cell always shows as 1
  deleted + 1 added line, never 0 deleted). The session worked around it by reverting the closeout-plan edit and landing
  the finding only in the two OTHER docs it also touches
  (`tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`,
  `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`) — the closeout plan's own "S&P index options" row remains stale
  (still shows the old, now-confirmed-wrong "66% attempted_failed... not yet launched" text) until this is resolved.
status: open
nature: issue
asset_group: [tradfi] # was [tradfi, cross-cutting] — tradfi-only (tradfi_master parent_epic, no other AGs in body), orthogonality fix 2026-08-10 ag-closeout-audit
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, line-caps, tooling-gap, tradfi]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md,
    /plans/archive/issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
  ]
created: "2026-08-09"
author: slot-22
priority: P3
# was: tradfi_master (epic-assignment audit 2026-08-19) -- core finding is a
parent_epic: plan_hygiene_master
  # generic check_line_caps.sh carve-out gap (a net-zero-length content substitution can never satisfy the
  # DELETED=0 precondition); doc's own text says the identical bug already hit cross_cutting_consolidated_closeout_2026_07_25.md
source: >-
  Discovered live 2026-08-09 while shipping an accurate ES_OPT coverage update — `check_line_caps.sh` refused the
  closeout-plan half of the change (`HARD tradfi_consolidated_closeout_2026_07_18.md 1005L`), pre-commit hook output
  captured verbatim in that session's transcript.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: fix
estimate_class: infra
estimate_baseline: 0.3
calibrated_ai_days: 0.2
assigned_role: backend_engineer
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md,
    /plans/archive/issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md,
    unified-trading-pm/scripts/plan-hygiene/check_line_caps.sh,
  ]
---

# tradfi_consolidated_closeout_2026_07_18.md is over the 1000-line hard cap

## Todos

- [x] ✅ [DOCS] P2. **Split or condense `tradfi_consolidated_closeout_2026_07_18.md`** below the 1000-line hard cap
      (1005L currently) so routine content edits (MVP-cell table updates, status corrections) can land again —
      `unified-trading-pm@<pending>`. Applied option (a): the parent's "## Progress Log" section (14 entries, 2026-07-30
      through 2026-08-08, 139 lines) moved **verbatim** — nothing summarized, rewritten, or dropped — to
      `tradfi_consolidated_closeout_history_2026_07_25.md`'s new "Progress Log entries — 2026-07-30 through 2026-08-08
      (moved 2026-08-09, line-cap remediation)" section, same pattern as the 2026-07-24/2026-07-25 trims already applied
      to this doc. Parent left with a short pointer note in its place. **Verified**: parent now 879 lines (was 1005),
      `bash scripts/plan-hygiene/check_line_caps.sh plans/active/tradfi_consolidated_closeout_2026_07_18.md` exits 0
      (SOFT warning only, no HARD violation).
- [x] ✅ [DATA] P3. **Once the cap is cleared, land the accurate "S&P index options" MVP-cell row** (the corrected text
      is already drafted — see `tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`'s third
      finding for the exact content: 2020-2024 ~94.8-100% covered, 2025 confirmed 0% gap, 2026 73% partial — replacing
      the stale "66% attempted_failed... not yet launched" text). Repo: unified-trading-pm.

      **DONE 2026-08-15 (slot-7, backend_engineer)** — landed via
          `plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s corresponding todo. `unified-trading-pm@<pending>`.

- [ ] [OPERATOR] P3. **CORRECTED 2026-08-12 (/plan-reconcile): de-ambiguated "consider whether X should Y" — this is a
      real gate-design decision, not a worker-determinable task.** Original ask: whether `check_line_caps.sh`'s
      scoped-mode carve-out should accept a net-zero-LENGTH content substitution (not just `DELETED=0`), per the
      root-cause analysis already done in `plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md` — a
      shared fix would unblock both that doc's link-archival case and this doc's table-row-update case without requiring
      every over-cap closeout plan to be split first. **Why this needs an operator call, not a mechanical
      implementation**: loosening a QG-enforced HARD-cap gate's carve-out is a real risk/tradeoff decision (a
      net-zero-length diff can still smuggle a large, unrelated content swap past the cap check) — the SSOT's own "never
      raise the cap" posture on adjacent size gates argues for caution here too. **Done when**: the operator either
      approves the net-zero-length carve-out (then implement + regression-test it against both cited cases) or rules the
      split-first workaround stays the standing pattern (then close this todo as CANCELLED, not implement anything).
      Repo: unified-trading-pm, `scripts/plan-hygiene/check_line_caps.sh`.

## Progress Log

- **2026-08-09, slot-22**: filed after `check_line_caps.sh` blocked a routine MVP-cell table update to this doc
  mid-session. Worked around it by landing the same finding in the two other docs the change also touched, leaving this
  doc's own row stale. Not investigated/fixed further this session (out of scope for the task in progress) — todos above
  are the concrete next steps, not attempted here.
- **2026-08-09, slot-33 (backend_engineer)**: closed todo 1. Moved `tradfi_consolidated_closeout_2026_07_18.md`'s "##
  Progress Log" section (14 entries, 2026-07-30 through 2026-08-08, 139 lines) verbatim to
  `tradfi_consolidated_closeout_history_2026_07_25.md`, left a pointer in its place — option (a) from the todo, matching
  the established 2026-07-24/2026-07-25 split precedent. Parent doc 1005L → 879L; `check_line_caps.sh` now exits 0 on
  it. Todos 2 and 3 remain open (out of this task's scope — a P3 content-landing todo and a P3 tooling-improvement todo,
  both separate follow-ups).

- **context-scout 2026-08-14**: populated context_scope (4 entries).
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
