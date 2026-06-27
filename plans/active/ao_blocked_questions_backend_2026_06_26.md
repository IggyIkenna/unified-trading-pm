---
doc_type: plan
title: AO blocked-questions — backend (authority field · clean question · Slack · condition rename)
summary: Backend half of the blocked-questions / conditions clarity work — replace the operator-gated text-prefix hack with a structured authority field, route operator-only questions to Slack with a rich payload, and end the dependency-vs-blocked-question confusion (RULES + rename "condition"). The blocked-questions UI plan depends on the authority field this adds.
status: active
nature: design
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, blocked-questions, conditions, escalation, slack, backend]
related: [ao_blocked_questions_ui_2026_06_26.md, ../epics/orchestrator_master.md, ../../codex/12-agent-workflow/work-philosophy.md, ../../codex/04-architecture/agent-orchestrator-overview.md]
created: 2026-06-26
parent_epic: orchestrator_master
assigned_vm: vm-cross-cutting
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
last_updated: 2026-06-26
locked_by: live-defi-rollout
locked_since: 2026-06-26
supersedes:
superseded_by:
depends_on:
source:
assigned_role: backend-engineer
drift_direction: advance-code
---

# AO blocked-questions — backend

> **Backend lane** of the blocked-questions / conditions clarity work (work-philosophy **L4** role split). The
> blocked-questions UI plan (`ao_blocked_questions_ui`) depends on the **`authority`** field this adds. Grounding: today
> operator-gated is an unstructured text prefix (`bootstrap.py:195`) — making it a real field fixes the message, the
> routing, and the main-agent decision at once.

## Tasks

- [x] [CODE] P0. **Add a structured `authority` field** to the blocked row (`blocked_queue`): `main_agent` | `operator`.
      The main agent reads it to decide whether it may answer or must defer to a human (Harsh / Ikenna). `bootstrap.py`
      migration. **Gate**: a blocked row carries `authority`; the main agent answers only `authority=main_agent`. ✅
      agent-orchestrator@1f968e1 — BlockedRow.authority; \_add_missing_columns() migration; BlockedView.authority;
      add_blocked() accepts authority param.
- [x] [CODE] P0. **Stop dumping the raw `[OPERATOR-GATED plan todo — main agent must NOT answer…]` prefix** into the
      `question` (`bootstrap.py:195`). The `question` becomes a clean short prompt; the operator-gated signal lives in
      `authority`. **Gate**: a blocked row's `question` is a clean prompt + options, no raw todo-brief dump. ✅
      agent-orchestrator@1f968e1 — sync_backlog_to_db sets question=task.brief[:600] (no prefix); authority="operator".
- [x] [CODE] P1. When `authority=operator`, **post to Slack on creation** with a rich payload: the raising
      **agent/slot + role**, the **question**, the **options**, the **recommendation**, and context (task/plan). Extends
      `_alert_unanswered_operator_gated_blocks`. **Gate**: a synthetic operator-gated block posts a Slack message
      carrying agent + question + options + recommendation. ✅ agent-orchestrator@1f968e1 —
      notify_operator_gated_blocked() accepts options+recommendation; renders in Slack blocks.
- [x] [DOCS] P0. **Distinguish a dependency/blocker from a blocked-question** in `agents/RULES.md` + the boot prompts: a
      task gated by EARLIER tasks (e.g. 6–10 need 1–5 done) is a **prerequisite/dependency** (task `prereqs`), NOT a
      blocked-question for the operator. **Gate**: RULES states the distinction; a prereq-gated agent waits on the
      prereq instead of escalating a question. ✅ agent-orchestrator@1f968e1 — RULES.md §5 "Prerequisites vs
      blocked-questions — do NOT conflate them" added; old §5→§6, §6→§7.
- [x] [DESIGN] P1. **Rename "condition" → a clearer term** (`blocker` / `gate` / `prerequisite` — operator picks) across
      the model + dashboard, since "condition" is the word agents conflate with blocked-questions. **Gate**: operator
      approves the term; rename applied (`ConditionRow` + `conditions` table + UI) with no stale agent-facing
      "condition". ✅ agent-orchestrator@9758270 — operator chose **`prerequisite`**. End-to-end rename: `ConditionRow`→
      `PrerequisiteRow` + `conditions` table → `prerequisites` (guarded ALTER-TABLE migration, pre-`create_all`),
      `ConditionView`/`ConditionSetRequest`→`Prerequisite*`, `/api/conditions`→`/api/prerequisites`, `set_condition`→
      `set_prerequisite`, `StateResponse.conditions`→`prerequisites`, `TaskPrereqs.conditions`→`prerequisites`, gcs-sync
      key, `condition_set` activity event, + the full dashboard (panel/tone/types/api/tests). English prose ("race
      condition" etc.) deliberately preserved. QG green (920 py + 65 vitest + tsc + basedpyright); verified live —
      `/api/state` returns `prerequisites`, table migrated, zero data loss.

## Success criteria

- `authority` is a structured field driving who-answers; operator-only questions reach Slack with full context; the
  question text is clean; RULES + the rename stop agents conflating prerequisites with blocked-questions.
- **Runtime-verified on the local `harsh_pc` AO.**

## Codex SSOT updates

- `codex/04-architecture/agent-orchestrator-overview.md` — the `authority` field + the dependency-vs-blocked-question
  distinction + the condition→term rename.

## Progress Log

- 2026-06-26: Split from the AO-observability tracker (blocked-questions backend lane). Unblocks
  `ao_blocked_questions_ui`.
- 2026-06-26: All P0+P1 code+docs tasks complete — agent-orchestrator@1f968e1. authority field on BlockedRow with
  migration. Clean question text (no prefix). Slack rich-payload with options+recommendation. RULES.md §5 prereqs vs
  blocked-questions distinction. Remaining: DESIGN condition rename (needs operator pick of term).
