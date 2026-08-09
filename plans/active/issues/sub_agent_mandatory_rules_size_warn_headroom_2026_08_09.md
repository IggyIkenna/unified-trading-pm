---
doc_type: issue
title: >-
  `SUB_AGENT_MANDATORY_RULES.md` past the 95% size-cap WARN threshold (408 B headroom) — opportunistic trim, not urgent
summary: >-
  Running `scripts/quality_gates/check_agent_rules_size_cap.py` (as part of an unrelated `cursor-configs/CLAUDE.md`
  edit, `unified-trading-pm@fc767d2c9`) surfaced a pre-existing, non-blocking WARN:
  `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` is 9,832 B, past the 9,728 B (95%) warn threshold, with only 408 B of
  headroom before the 10,240 B hard cap. Not caused by, or related to, that edit (only `CLAUDE.md` was touched). Exit
  code is unaffected by a WARN (only over-cap fails the gate), so this is not blocking anything — filed per the
  workspace's "every deferral is a tracked todo, not just a Progress Log note" rule rather than left as a chat/log-only
  observation.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [claude-md, sub-agent-mandatory-rules, quality-gates, size-cap, documentation, process]
related: []
created: "2026-08-09"
last_updated: "2026-08-09"
author: slot-5 (data_engineering)
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.05
estimate_calibrated_ai_days: 0.02
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope: [cursor-configs/SUB_AGENT_MANDATORY_RULES.md, scripts/quality_gates/check_agent_rules_size_cap.py]
source: >-
  Discovered 2026-08-09 (slot-5, data_engineering) as a side effect of running
  `scripts/quality_gates/check_agent_rules_size_cap.py` to verify a `cursor-configs/CLAUDE.md` clarification stayed
  under its own cap — see that work's now-archived tracking doc,
  `/plans/archive/2026_08/issues/claude_md_qg_cap_line_omits_auto_governor_2026_08_09.md`, Progress Log.
resolved_by:
locked_by:
---

# `SUB_AGENT_MANDATORY_RULES.md` nearing its 10 KiB cap

## What I found

```
[WARN] cursor-configs/SUB_AGENT_MANDATORY_RULES.md: 9,832 B (~2,458 tok) / cap 10,240 B
  - cursor-configs/SUB_AGENT_MANDATORY_RULES.md is 9,832 B — past the 9,728 B (95%) warn threshold, only 408 B of
    headroom left before the 10,240 B hard cap. Condense a rule now, routinely, before it becomes an emergency trim.
```

Not new content from me — this file wasn't touched this session. `git log --oneline -5` on it shows the pattern is
already actively managed: a 2026-08-08 commit (`3abd89e68`, "trim SUB_AGENT_MANDATORY_RULES.md headroom + mirror
CLAUDE.md HARD RULE parity") explicitly freed headroom, then a later commit (`a20e52125`, "add worked example for
batching independent tool calls") spent some of it back. This WARN is that same routine cycle continuing, caught mid-way
rather than a novel regression.

## Why it matters

Per the checker's own docstring, the WARN exists specifically because a previous incident (2026-08-07) let `CLAUDE.md`
sit at 31 B of headroom before anyone noticed, forcing an emergency same-session trim instead of a routine one. Same
mechanism, same file family — worth a routine trim before the 408 B runs out under normal edit velocity, not an
emergency one later.

## Recommended decision

No design decision needed — this is a mechanical condense-and-verify task: find ~500 B+ of prose in
`SUB_AGENT_MANDATORY_RULES.md` that can be condensed to a directive + pointer (mirroring how `CLAUDE.md` itself is kept
lean) without losing any rule, and rerun the checker to confirm `ok`.

## Todos

- [ ] [DOC] P3. Condense `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` by ≥500 B (current: 9,832 B / cap 10,240 B) —
      find prose that can drop to a 1-line directive + codex/CLAUDE.md pointer, same discipline the file already applies
      to itself. Reverify green (`ok`, not `WARN`) via `python3 scripts/quality_gates/check_agent_rules_size_cap.py`
      before shipping. Not urgent (still under the hard cap) — pick up opportunistically, e.g. alongside the next edit
      that already touches this file. (repo: unified-trading-pm)

## Progress Log

- **2026-08-09 (slot-5, data_engineering)** — Filed as a side finding while verifying an unrelated `CLAUDE.md` edit
  stayed under its own size cap. Not fixed inline (out of scope for that edit, and not urgent — 408 B of real headroom
  remains, well under the hard cap).
- **na-corpus-hygiene 2026-08-09**: RECLASSIFY — `assigned_vm: NA → planning`. Purely mechanical condense-and-verify
  task with a stated done-when (checker reports `ok`, not `WARN`) — no design/judgment call, no `locked_by`.
