---
doc_type: plan
title: AO blocked-questions — backend (authority field · clean question · Slack · condition rename)
summary:
  Backend half of the blocked-questions / conditions clarity work — replace the operator-gated text-prefix hack with a
  structured authority field, route operator-only questions to Slack with a rich payload, and end the
  dependency-vs-blocked-question confusion (RULES + rename "condition"). The blocked-questions UI plan depends on the
  authority field this adds.
status: active
nature: design
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, blocked-questions, conditions, escalation, slack, backend]
related:
  [
    ao_blocked_questions_ui_2026_06_26.md,
    ../epics/orchestrator_master.md,
    ../../codex/12-agent-workflow/work-philosophy.md,
    ../../codex/04-architecture/agent-orchestrator-overview.md,
  ]
created: 2026-06-26
parent_epic: orchestrator_master
assigned_vm: harsh_pc
assigned_role: backend-engineer
drift_direction: advance-code
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
---

# AO blocked-questions — backend

> **Backend lane** of the blocked-questions / conditions clarity work (work-philosophy **L4** role split). The
> blocked-questions UI plan (`ao_blocked_questions_ui`) depends on the **`authority`** field this adds. Grounding: today
> operator-gated is an unstructured text prefix (`bootstrap.py:195`) — making it a real field fixes the message, the
> routing, and the main-agent decision at once.

## Tasks

- [ ] [CODE] P0. **Add a structured `authority` field** to the blocked row (`blocked_queue`): `main_agent` | `operator`.
      The main agent reads it to decide whether it may answer or must defer to a human (Harsh / Ikenna). `bootstrap.py`
      migration. **Gate**: a blocked row carries `authority`; the main agent answers only `authority=main_agent`.
- [ ] [CODE] P0. **Stop dumping the raw `[OPERATOR-GATED plan todo — main agent must NOT answer…]` prefix** into the
      `question` (`bootstrap.py:195`). The `question` becomes a clean short prompt; the operator-gated signal lives in
      `authority`. **Gate**: a blocked row's `question` is a clean prompt + options, no raw todo-brief dump.
- [ ] [CODE] P1. When `authority=operator`, **post to Slack on creation** with a rich payload: the raising
      **agent/slot + role**, the **question**, the **options**, the **recommendation**, and context (task/plan). Extends
      `_alert_unanswered_operator_gated_blocks`. **Gate**: a synthetic operator-gated block posts a Slack message
      carrying agent + question + options + recommendation.
- [ ] [DOCS] P0. **Distinguish a dependency/blocker from a blocked-question** in `agents/RULES.md` + the boot prompts: a
      task gated by EARLIER tasks (e.g. 6–10 need 1–5 done) is a **prerequisite/dependency** (task `prereqs`), NOT a
      blocked-question for the operator. **Gate**: RULES states the distinction; a prereq-gated agent waits on the
      prereq instead of escalating a question.
- [ ] [DESIGN] P1. **Rename "condition" → a clearer term** (`blocker` / `gate` / `prerequisite` — operator picks) across
      the model + dashboard, since "condition" is the word agents conflate with blocked-questions. **Gate**: operator
      approves the term; rename applied (`ConditionRow` + `conditions` table + UI) with no stale agent-facing
      "condition".

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
