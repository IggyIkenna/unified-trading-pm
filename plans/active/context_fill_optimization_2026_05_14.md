---
title: "Context fill-up optimization — reduce compact cycle frequency"
created: 2026-05-14
author: harsh-main
type: improvement
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

## Problem

Context compaction cycles are happening more frequently than before, taking 1-2 min each and
causing token waste + information loss. Root cause: three independent sources of context bloat.

---

## Source 1 — CLAUDE.md fixed-cost per turn (~58KB every turn)

**Current state**: ~999 lines / ~58KB. Loaded on every single turn regardless of task.

The file header says "lean index" but large sections still have inline content — tables,
multi-paragraph rules, code blocks — where a codex SSOT doc already exists.

**Fix**: For every section that has a codex SSOT pointer, strip inline content to 1-2 lines +
the pointer only. Reader goes to codex when detail is needed. Only rules with NO codex home
stay inline.

**Target**: ~300-400 lines / ~15KB. Saves ~25KB per turn (permanent).

**How to identify what to trim**: any section that ends with `SSOT: codex/...` and also has
>5 lines of inline content is a candidate. The inline content moves to the codex doc (or is
already there); the CLAUDE.md entry becomes the 1-liner + pointer.

**Size budget reminder** (already in CLAUDE.md): target ≤1200 lines / 70KB, hard cap 1500 / 90KB.
This task pushes toward a new target of ≤400 lines / 25KB.

---

## Source 2 — Orchestrator poll running in main context (variable, per cycle)

**Current state**: the `/loop` orchestrator poll runs all commands — `git fetch`, ping file reads,
LEDGER reads, plan file reads — directly in the main conversation. Every tool result lands in
context and stays there permanently. A typical poll cycle adds ~8-12 tool results, each
potentially large (LEDGER alone is several hundred lines).

**Fix**: Rewrite the loop to use the `Agent(subagent_type="general-purpose")` tool for the
actual poll work. The sub-agent reads all files, does all work, returns a ≤150-word summary.
Main context accumulates only the short summary per cycle.

**Expected savings**: ~80% reduction in per-cycle context growth.

**Implementation sketch**:
```
/loop 5m [one-liner trigger]
  → main context calls Agent("do the poll, return ≤150 word summary")
  → sub-agent: git fetch, read pings, handle STARTED/DONE/blockers, push
  → sub-agent returns: "Cycle N: slot 3 DONE (sha), slot 5 STARTED. No blockers. 0 0 on LDR."
  → main context stores that 1 line per cycle
```

The sub-agent prompt should include SUB_AGENT_MANDATORY_RULES.md inline (per workspace rules).

---

## Source 3 — `.claude/rules/*.md` loaded globally for every session

**Current state**: 5 rules files load for every session regardless of context:
- `universal.md` — workspace-wide (appropriate)
- `pm-repo.md` — only relevant in PM repo sessions
- `ui.md` — only relevant in UI repo sessions
- `workspace-workflow.md` — workspace-wide (appropriate)
- `python-backend.md` — only relevant in Python service sessions

**Fix**: Move repo-specific rules (`pm-repo.md`, `ui.md`, `python-backend.md`) into each
repo's own `CLAUDE.md` (or a `.claude/rules/` inside each repo). They load only when Claude
Code is opened from within that repo.

For the multi-repo workspace (opened from `/home/hk/unified-trading-system-repos/`), keep only
truly workspace-global rules at the root level.

**Note**: This is the lowest-impact of the three fixes. Address after Sources 1 + 2.

---

## Recommended execution order

- [x] [DOC] P0. Trim CLAUDE.md from ~999 lines to ~400 lines — strip inline content wherever
  a codex SSOT pointer already exists. Verify no rule is lost (all content moves to codex, not
  deleted). Budget: target ≤400 lines / 25KB. (6a08f50c — 399 lines / 25.3KB; all rules preserved, inline content compressed to 1-3 lines + SSOT pointer)

- [ ] [SCRIPT] P1. Rewrite orchestrator loop to use Agent sub-agent for poll execution — main
  context receives ≤150 word summary per cycle instead of raw tool results. Update spawn prompt
  to include SUB_AGENT_MANDATORY_RULES.md inline.

- [ ] [DOC] P2. Relocate `pm-repo.md` + `ui.md` + `python-backend.md` from workspace-root
  `.claude/rules/` into per-repo CLAUDE.md or per-repo `.claude/rules/`. Keep `universal.md`
  + `workspace-workflow.md` at workspace root.

---

## Success criteria

- Compact cycles occur ≤1× per extended orchestrator session (currently: every ~15-20 min)
- CLAUDE.md ≤400 lines / 25KB verified by `wc -l` + `wc -c`
- Orchestrator poll cycle adds ≤200 tokens to main context (measurable by checking context
  size before/after one cycle)
