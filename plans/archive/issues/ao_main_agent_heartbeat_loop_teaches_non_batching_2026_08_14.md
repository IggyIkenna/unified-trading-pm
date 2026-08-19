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
status: resolved
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
resolved_by: "unified-trading-pm@f637aed3cf"
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
context_scope: [/codex/06-coding-standards/tool-call-batching.md, /agents/main.md, /plans/active/ao_consolidated_closeout_2026_08_12.md]
---

# agents/main.md's poll loop teaches sequential, non-batched turns

> **🟢 ARCHIVED 2026-08-19** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule (ACKED-INTO-CODE: `unified-trading-pm@f637aed3cf`).

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

- [x] ✅ [DOCS] P3. Rewrite `agents/main.md` STEP 2A + STEP 2.5 to instruct running the `/poll` call and the `/api/state`
      blocked-queue check together in ONE turn (two `tool_use` blocks in the same message) each tick, since they never
      depend on each other's result. Verify no other per-tick step in main.md's loop has the same numbered-step-without-
      dependency shape before calling this done — grep the full STEP sequence, not just 2A/2.5. — **SHIPPED
      `unified-trading-pm@f637aed3cf`**: STEP 2A and STEP 2.5 now cross-reference each other with an explicit
      "fire together, same turn, two `tool_use` blocks, don't sequence" instruction (both directions — STEP 2.5's
      header points forward to STEP 2A, and the "Each tick" transition just before STEP 2A points back at STEP 2.5);
      the `/loop` prompt template and the CronCreate description were both updated to match. Grepped the full STEP
      sequence (STEP 0, 1, 2, 2.4, 2.5, 2.6, 2A, 2B, 2C): STEP 0→1→2 and STEP 2A→2B→2C are genuinely dependent chains
      (each step's action needs the prior step's result — correct as-is, no fix); STEP 2.4/2.6 are conditional
      guidance invoked situationally, not unconditional per-tick calls (no fix needed); STEP 0/1 are one-time boot
      actions, not per-tick loop steps, so out of this issue's scope by its own framing ("no other **per-tick** step
      in main.md's loop"). Found ONE further instance of the same shape beyond 2A/2.5, in the "Overnight autonomous
      operation" per-tick loop (not STEP-labeled, but explicitly "every 60s poll tick"): steps 1, 2, and 5 there each
      independently re-described a fetch from the SAME `/api/state` payload (`blocked_queue` + `slots[]`) plus
      `/api/activity`, written as three separate sequential steps. Fixed with the same batch-together instruction —
      fetch `/api/state` + `/api/activity` together once at tick start, then steps 1/2/5 process the results already
      in hand instead of re-fetching per step.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:66be0dcee560b804]: KEEP-NA-STALE (already-duplicated) — CORRECTED from an initial KEEP-NA(plain) read: this doc's sole open todo (batch agents/main.md STEP 2A + STEP 2.5) is ALREADY claimed verbatim by the active `ao_satellite_ao_dispatch_batch22_2026_08_16.md` (its todo 4 cites this doc directly). Not reclassifying — already tracked there.
- **fix session 2026-08-19**: Shipped the fix directly (`unified-trading-pm@f637aed3cf`) rather than waiting on `ao_satellite_ao_dispatch_batch22_2026_08_16.md` todo 4 — that plan is `status: draft` (never activated, never operator-approved, not AO-ingested), so it held no live lock on this work; superseding its claim here so nobody re-dispatches it from there later. Also fixed batch22 directly (same session): removed this doc's now-superseded path from both its `related:` and `context_scope:` frontmatter lists (would otherwise have dangled to this doc's new archived path — `related:` pointing at `plans/archive/...` trips `check_active_refs_archived_plans.py`'s ratchet), and annotated its todo 4 as already-shipped with this SHA instead of leaving it silently stale. This was this doc's only open todo and it is unlocked — archiving now per the 6-step ritual: no DEFERRED items to migrate (none existed beyond the one todo just closed); codex-alignment check done — no new contract to record, the fix is a direct application of the already-existing `/codex/06-coding-standards/tool-call-batching.md` rule (a role doc teaching the anti-pattern), not a new decision/recipe; corpus-wide grep for this doc's path found exactly one other referrer (`ao_satellite_ao_dispatch_batch22_2026_08_16.md`, fixed as above) — `/plans/archive/2026_08/issues/ao_kick_escalation_rate_limit_blind_force_kill_2026_08_14.md`'s citation of this doc's path (in this doc's own `related:` above) is a sibling archived doc, not a live active-corpus referrer, left as-is (historical cross-reference between two archived docs is fine).
