---
doc_type: plan
title:
  AO satellite AO batch 15 — 3 bounded doc/script-hygiene items from 2 non-covered `ao`-tranche docs
  (agent_operating_framework_master epic)
summary: >-
  FIFTEENTH AO-dispatch batch for the `ao` topic tranche — a round9 `/na-eligibility-audit ao` re-sweep (2026-08-09)
  per-item satellite extraction from 2 fresh (never-previously-audited), genuinely mixed NA docs:
  `operational_modes_antipatterns_not_actually_deleted_2026_08_09.md` (1 item — a corpus-wide stale-symbol-name rename,
  no judgment call once the real API name is known) and
  `todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md` (2 items — reconcile a documented
  format contradiction between `task_template.md` and `check_todo_regression.sh`, plus a mechanical corpus grep for
  pre-existing instances of the same silent-undercounting bug). Both source docs' OTHER open items stay genuinely NA (an
  operator-only owner/date placeholder, a design decision on a protocol-level flag, and a self-flagged
  cross-file-correlation design call) — this batch extracts only the conflict-clear, no-remaining-judgment items. Split
  from a would-be `orchestrator_master`-epic batch (`ao_satellite_ao_dispatch_batch14_2026_08_09.md`, same run) per the
  established `parent_epic`-is-the-grouping-axis convention (batch11/13 precedent). All 3 todos are file-disjoint, so
  this plan needs no `sequential` gate.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, ao-dispatch, close-out, batch-15, satellite-docs, satellite-extraction, plan-hygiene]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch15_finalize_2026_08_09.md,
    /plans/active/issues/operational_modes_antipatterns_not_actually_deleted_2026_08_09.md,
    /plans/active/issues/todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md,
    /plans/active/ao_satellite_ao_dispatch_batch14_2026_08_09.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.32
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/operational_modes_antipatterns_not_actually_deleted_2026_08_09.md,
    /plans/active/issues/todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md,
    scripts/plan-hygiene/check_todo_regression.sh,
    plans/active/task_template.md,
  ]
source: >-
  `/na-eligibility-audit ao` round9 re-sweep, 2026-08-09 — both source docs were never previously audited (no prior
  na-eligibility-audit marker); each was read end-to-end and split per-item into bounded vs. genuinely-gated per this
  audit's standard method.
---

# AO satellite AO batch 15

> **`status: draft`** — pending operator approval, same convention as batch5-14: flip to `active` to dispatch.
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** once approved, same as the rest of this series.

## Why this plan exists

Two never-before-audited `ao`-tranche NA docs each carried a mix of genuinely-gated items and independently bounded,
worker-determinable ones. Per the whole-doc RECLASSIFY bar not being cleared (both docs retain real judgment-call/
operator-only items), each source doc's bounded item(s) are extracted here instead, leaving the rest open on the source
doc.

- `operational_modes_antipatterns_not_actually_deleted_2026_08_09.md`: 4 open items. 1 (`[DOCS] P3`, rename
  `paper_target_registry` references corpus-wide) is a pure mechanical rename with a known, code-verified real name — no
  judgment call. The other 3 stay NA: 1 is downstream of an `[OPERATOR]` placeholder (assign an owner + target date —
  explicitly "not worker-determinable" per the doc's own text), 1 IS that operator placeholder, and 1 is a design
  decision ("decide whether a protocol-level flag is legitimately different").
- `todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md`: 3 open items. 2 are extracted: the
  format-contradiction fix (`[DEVOPS] P2` — the doc's own text frames both resolution options as small, with a concrete
  done-when: a fresh CANCELLED-format conversion passes the checker cleanly) and a mechanical corpus grep for
  pre-existing silent undercounts (`[DOC] P3`, explicitly "not urgent; a hygiene sweep item," zero judgment). The 3rd
  item (a second, independently-found trigger for the same root cause — the Finding-J archival-extraction case) stays NA
  — the doc's own text self-flags it as needing "design judgment on the cross-file correlation logic, not a mechanical
  one-liner."

A multi-source, per-item batch is the established shape for this series (batch12 pulled 11 items from 4 docs the same
way).

## Rules for every worker on this plan

- Do not edit either source doc's remaining checkboxes beyond what this plan's own drafting already changed (a
  redirect-pointer marking the extracted item). Append your evidence to THIS plan's own todo when you finish; the paired
  finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch15_finalize_2026_08_09.md`) reconciles evidence back into
  each source doc.
- Todos 1 and 2 below (both from the `check_todo_regression.sh` doc) touch the SAME function (`_check_one()`) but are
  scoped to different trigger classes (CANCELLED-format vs. corpus grep for pre-existing instances) — todo 1 changes the
  checker or the template convention; todo 2 is read-only reconnaissance. No file conflict, but land todo 1's decision
  before acting on anything todo 2's grep turns up that would need the same fix.

## Todos

- [ ] [DOCS] P3. **Rename the remaining `paper_target_registry` references corpus-wide.** Five PM docs still use the
      non-existent name: `/plans/epics/defi_master.md`,
      `/codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md`, and three archived plans (leave
      archived ones alone — historical record). Replace with `PAPER_EXECUTION_TARGETS` / `get_paper_target()`, the real
      API in `unified_api_contracts/internal/paper_execution_targets.py`. **Done when**: no ACTIVE plan or codex doc
      references `paper_target_registry`; each points at the real symbol names. Source:
      `/plans/active/issues/operational_modes_antipatterns_not_actually_deleted_2026_08_09.md:147`. Repo:
      unified-trading-pm.
- [x] ✅ [DEVOPS] P2. **Resolve the CANCELLED/SUPERSEDED-format contradiction between `task_template.md` and
      `check_todo_regression.sh` — pick one, then fix the other.** Either (a) teach
      `scripts/plan-hygiene/check_todo_regression.sh`'s `_check_one()` to recognize the documented bold-bullet pattern
      (`^- \*\*\[[A-Z]+\] P\d\. CANCELLED`) and count it as equivalent to a retained checkbox line rather than a loss,
      or (b) update `task_template.md`'s CANCELLED/SUPERSEDED convention to keep the checkbox bracket instead of
      converting to a bold non-checkbox bullet, matching what the checker already expects. Recommended default absent
      new information: (a) — `task_template.md`'s documented convention is the one already in live use elsewhere in the
      corpus (per the source doc's own repro), so teaching the checker to recognize it is less disruptive than rewriting
      an adopted authoring convention. **Done when**: a fresh conversion of a stale todo to CANCELLED/ SUPERSEDED
      format, per whichever convention wins, passes `check_todo_regression.sh --only <file>` cleanly. Source:
      `/plans/active/issues/todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md:94`. Repo:
      unified-trading-pm. — unified-trading-pm@d01cd9ad41 (option (a) shipped: `_check_one()` now counts
      `^- \*\*\[[A-Z]+\] P[0-9]+\. CANCELLED` bullets alongside checkbox lines; verified with a scratch-repo
      before/after repro — old logic flagged a fresh CANCELLED conversion as `lost=1`, fixed logic reports 0 violations;
      a genuine todo deletion still correctly fails). Full QG green.
- [ ] [DOC] P3. **Grep the corpus for any EXISTING bold non-checkbox `CANCELLED —`/`SUPERSEDED` bullets that may have
      already silently reduced a plan's checkbox total below its origin value without anyone noticing** (this check only
      runs `--only` on STAGED files today, so a prior conversion that landed via a path that skipped this hook — e.g.
      `safe-doc-push.sh` before its own recent hardening, or a raw push — could be sitting unnoticed). Report the list;
      no bulk-fix required beyond flagging. **Done when**: the corpus-wide grep result (matches, if any, with file:line)
      is recorded in this todo's evidence. Source:
      `/plans/active/issues/todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md:102`. Repo:
      unified-trading-pm.

## Codex SSOTs (read before starting a todo)

`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-09** — Authored by a round9 `/na-eligibility-audit ao` re-sweep. Conflict-check: grepped all active
  `parent_epic: agent_operating_framework_master` plans, batch10-13/14 (and their finalizes), and the `ao`
  consolidated-closeout doc for `paper_target_registry` and `check_todo_regression` — zero hits outside the two source
  docs themselves. Both source docs are brand-new (created 2026-08-09, never previously touched by a na-eligibility-
  audit or ag-closeout-audit pass), so this is a first-pass classification, not a re-derivation. File-disjointness
  verified across all 3 todos.
