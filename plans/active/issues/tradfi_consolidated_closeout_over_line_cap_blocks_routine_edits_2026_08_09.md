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
asset_group: [tradfi, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, line-caps, tooling-gap, tradfi]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md,
    /plans/active/issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
  ]
created: "2026-08-09"
author: slot-22
priority: P3
parent_epic: tradfi_master
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
---

# tradfi_consolidated_closeout_2026_07_18.md is over the 1000-line hard cap

## Todos

- [ ] [DOCS] P2. **Split or condense `tradfi_consolidated_closeout_2026_07_18.md`** below the 1000-line hard cap (1005L
      currently) so routine content edits (MVP-cell table updates, status corrections) can land again. Options: (a)
      split into a smaller "current status" doc + an archived/appendix doc for historical Progress Log entries (the
      established pattern for other over-cap plans in this corpus), or (b) condense verbose Progress Log entries the way
      `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`'s own saga section was condensed 2026-08-08 (see that doc's
      "Condensed 2026-08-08T21:53Z" note for the precedent). Repo: unified-trading-pm. **Done when**: the file is under
      1000 lines and `check_line_caps.sh <file>` passes.
- [ ] [DATA] P3. **Once the cap is cleared, land the accurate "S&P index options" MVP-cell row** (the corrected text is
      already drafted — see `tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`'s third
      finding for the exact content: 2020-2024 ~94.8-100% covered, 2025 confirmed 0% gap, 2026 73% partial — replacing
      the stale "66% attempted_failed... not yet launched" text). Repo: unified-trading-pm.
- [ ] [SCRIPT] P3. **Consider whether `check_line_caps.sh`'s scoped-mode carve-out should accept a net-zero-LENGTH
      content substitution** (not just `DELETED=0`), per the root-cause analysis already done in
      `plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md` — a shared fix would unblock both that
      doc's link-archival case and this doc's table-row-update case without requiring every over-cap closeout plan to be
      split first. Repo: unified-trading-pm, `scripts/plan-hygiene/check_line_caps.sh`.

## Progress Log

- **2026-08-09, slot-22**: filed after `check_line_caps.sh` blocked a routine MVP-cell table update to this doc
  mid-session. Worked around it by landing the same finding in the two other docs the change also touched, leaving this
  doc's own row stale. Not investigated/fixed further this session (out of scope for the task in progress) — todos above
  are the concrete next steps, not attempted here.
