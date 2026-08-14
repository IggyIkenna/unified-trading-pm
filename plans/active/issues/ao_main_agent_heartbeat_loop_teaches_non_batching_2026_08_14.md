---
doc_type: issue
title: agents/main.md's per-tick poll loop is written as sequential numbered steps that teach the batching anti-pattern
summary: >-
  Investigating a batching-efficiency regression (multi_tool_turn_pct 15.67%->5.03% in a recent window) found
  orch-agent-main's own control loop sits at ~0% multi-tool turns and now makes up ~24% of all fleet turns in the
  degraded window. Root cause traced to agents/main.md itself: STEP 2A (POST /api/agents/$AGENT_ID/poll) and STEP 2.5
  (GET /api/state -> blocked_queue, explicitly documented as running "every tick", unconditional on STEP 2A's result)
  are two genuinely independent lookups written as separate numbered steps -- exactly the anti-pattern
  tool-call-batching.md's own "Reviewing for this" section warns about ("A role doc, runbook, or skill that walks an
  agent through a numbered one-command-per-step procedure is actively teaching the anti-pattern").
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, batching, main-agent, role-doc]
related:
  - /codex/06-coding-standards/tool-call-batching.md
  - /plans/archive/2026_08/issues/ao_kick_escalation_rate_limit_blind_force_kill_2026_08_14.md
  - /plans/active/ao_consolidated_closeout_2026_08_12.md
created: "2026-08-14"
author: main (Claude Code, interactive session)
parent_epic: orchestrator_master
resolved_by:
locked_by:
locked_since:
source: >-
  Found while investigating a batching-efficiency regression the operator flagged from the dashboard's new "Batching
  Efficiency" panel. Not yet actioned -- offered to fix in chat, operator has not yet confirmed; filed here per the
  workspace HARD RULE that every deferral becomes a tracked todo, not just a chat mention.
assigned_vm: NA
execution_scope: local-only
priority: P3
drift_direction: advance-code
depends_on: []
---

# agents/main.md's poll loop teaches sequential, non-batched turns

## Evidence

`agents/main.md` STEP 2A (line ~287-290): poll for operator messages. `agents/main.md` STEP 2.5 (line ~237-243): "every
tick — you are the FIRST responder" check of `blocked_queue` via `GET $SERVER_URL/api/state`.

Neither step's outcome changes whether the other runs — they are independent lookups. Written as separate numbered steps
rather than "run these together," which is the documented anti-pattern per
`/codex/06-coding-standards/tool-call-batching.md`'s "Reviewing for this" section.

Measured effect (2026-08-14, live investigation via SSM against a real AO batching-regression window): main's own
session went from 13.2% multi-tool turns (doing real dispatch work) in a healthy window to 0.0% multi-tool turns in a
degraded window, where its now-heavier share (243/1013 = 24% of all fleet turns) was pure poll-then-check heartbeat
activity.

## Todo

- [ ] [DOCS] P3. Rewrite `agents/main.md` STEP 2A + STEP 2.5 to instruct running the `/poll` call and the `/api/state`
      blocked-queue check together in ONE turn (two `tool_use` blocks in the same message) each tick, since they never
      depend on each other's result. Verify no other per-tick step in main.md's loop has the same numbered-step-without-
      dependency shape before calling this done — grep the full STEP sequence, not just 2A/2.5.
