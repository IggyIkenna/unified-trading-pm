---
doc_type: codex-ssot
title: Sub-Agent Workflow
summary: >-
  Canonical rules for spawning + coordinating sub-agents — when to fan out (3+ repos / 3+ steps / >100K-token reads),
  the HARD mandatory-rules injection (paste SUB_AGENT_MANDATORY_RULES.md or the agent MUST NOT proceed), parallelization
  limits (max 10, never same file), explicit model= selection, and the background-wake watchdog rule.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [orchestrator, sub-agent, role-registry, model-tier, escalation]
related: [/codex/12-agent-workflow/README.md, /codex/12-agent-workflow/async-wait-and-poll-discipline.md]
created: 2026-03-27
authoritative_for: [sub-agent spawning + coordination workflow (mandatory-rules injection + parallelization limits)]
referenced_by:
owner: pm-orchestrator
last_reviewed: 2026-06-25
code_refs:
type: coding-standard
---

# Sub-Agent Workflow

> Canonical SSOT for spawning and coordinating sub-agents in this workspace. Sub-agents preserve the main context window
> and cost ~10× less than doing everything in the main thread. Related: `/codex/12-agent-workflow/README.md` (agent
> topology) · `.cursor/rules/core/sub-agent-workflow-standard.mdc`.

---

## When to use sub-agents

| Trigger                               | Why sub-agent                                                                                   |
| ------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Multi-repo operation (3+ repos)       | Each repo is an independent context slice; parallel agents avoid a 100K+ token main-thread read |
| 3+ sequential steps within a plan     | Sub-agents return only their final result (≤ 400 tokens), keeping the orchestrator context lean |
| Task requires > 100K token file reads | Prevents context explosion in the calling agent                                                 |
| Independent parallel tasks            | Different repos = zero conflict risk; up to **10 parallel agents**                              |

**Single-repo, ≤ 2 steps**: do it inline in the current agent; spawning overhead outweighs the benefit.

---

## Mandatory rules injection (HARD RULE)

Sub-agents start **fresh** — they do NOT inherit cursor rules, CLAUDE.md, or any prior context.

Before any other content in the spawn prompt, paste `SUB_AGENT_MANDATORY_RULES.md`:

```bash
# Local (from the workspace root)
RULES=$(bash unified-trading-pm/scripts/agents/inject-mandatory-rules.sh "$WORKSPACE_ROOT" "$REPO")
```

Or instruct the sub-agent explicitly:

```
Before any action, read unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md
and follow ALL rules strictly.
```

**If injection fails or the sub-agent cannot read the rules file, the agent MUST NOT proceed.**

For finish-to-DONE dispatches ("finish completely while I'm away"), ALSO paste
`cursor-configs/AUTONOMOUS_AGENT_RULES.md` — the completion contract (no DEFERRED leftovers, drive to done on a
self-paced loop).

---

## Parallelization rules

- **Different repos** — always safe to parallelize; zero file conflict risk.
- **Same file** — never parallelize; guaranteed conflict.
- **Same repo, different files** — safe to parallelize only if files are independent (no shared imports to change).
- **Max 10 parallel agents** at once.

Send all independent `Agent` tool calls in a **single message** so they run concurrently:

```python
# Good — all 3 launch in parallel
Agent({"prompt": "...", "subagent_type": "general-purpose"})  # repo A
Agent({"prompt": "...", "subagent_type": "general-purpose"})  # repo B
Agent({"prompt": "...", "subagent_type": "general-purpose"})  # repo C
```

```python
# Bad — sequential spawns waste wall-clock time
Agent({"prompt": "... repo A ..."})
# wait for result...
Agent({"prompt": "... repo B ..."})
```

---

## Model selection for sub-agents

Always set `model=` explicitly — sub-agents NEVER inherit the parent's model:

| Task                                                                  | Model      |
| --------------------------------------------------------------------- | ---------- |
| Research, code edits, most tasks                                      | `"sonnet"` |
| Cross-repo architecture, > 200K context, complex multi-step reasoning | `"opus"`   |

`thinking: max` requires Opus. `thinking: medium` on Opus is always wrong.

---

## What sub-agents return

Sub-agents return **only their final result** (≤ 400 tokens summary). The orchestrator:

1. Does NOT see intermediate tool calls or file reads.
2. Trusts but verifies: the result describes what the agent **intended**, not necessarily what it **did**. When a
   sub-agent writes or edits code, check the actual changes via `git diff` before reporting the work as done.

---

## Dispatch patterns

### Research dispatch (read-only)

Use `subagent_type: "Explore"` for targeted code/file lookups:

```
subagent_type: "Explore"
prompt: "Find where classify_venue_error is defined and all call sites. Quick search."
```

### Implementation dispatch

Give the agent a complete, self-contained brief — it has no prior context:

```
Before any action, read unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md.

Context: [what the task is, what files are involved, what the current state is]
Task: [exactly what to implement/fix/ship]
Acceptance: [how to know it's done — QG green, test passes, etc.]
Do NOT ask for confirmation — ship it.
```

### Fan-out = a tracked plan todo (HARD RULE)

Any "a slot should do X / hand off / out of scope" is **not real** until it's a `- [ ] [CATEGORY] P<n>. …` todo in a PM
active plan with the **target repo named** + cold-start context. Verbal/chat dispatch is banned.

---

## Background agents and wake discipline

- A dispatched sub-agent is **not a reliable wake source** — a silent crash or rate-limit sends no completion signal.
- Always arm your own `run_in_background` heartbeat watchdog (≤ 30-min) in the same turn as the dispatch.
- `ScheduleWakeup` is NOT a reliable unattended timer — use a tracked `run_in_background` task instead.
- SSOT: `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` § "Wake sources".
