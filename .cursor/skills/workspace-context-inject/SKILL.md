---
name: workspace-context-inject
description:
  "Inject workspace rule reminders into prompts for unified-trading workspace. Use when starting multi-repo work,
  launching sub-agents, or when context is long and rules may be forgotten. Covers uv, quickmerge, basedpyright,
  delete-deprecated, plans placement."
---

# Workspace Context Inject

When starting work or launching sub-agents in the unified-trading workspace, include these reminders at the TOP of
prompts:

## Core reminders

- Follow all workspace cursor rules in .cursor/rules
- Plans live in unified-trading-pm/plans/ai or unified-trading-pm/plans/active; **venue axis / asset group** SSOT:
  `unified-trading-pm/plans/active/venue_axis_asset_group_vocabulary_2026_04_25.plan.md` (UAC/UTL/MDPS/MTDS first)
- uv not pip; basedpyright not pyright; quickmerge not git push
- Delete deprecated code; no parallel code paths
- Search unified libraries before implementing anything new

## For sub-agents (Task tool) — FULL RULES REQUIRED

Sub-agents get reduced context and do NOT inherit rules. You MUST pass the full rules.

**Option 1 (preferred):** Paste the contents of `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the
TOP of the prompt.

**Option 2:** Include at TOP: "Before any action, read unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md
and follow ALL rules strictly. WORKSPACE_ROOT is <path>. For quality gates: cd <repo> && bash scripts/quality-gates.sh
(per-repo .venv). Never .venv-workspace for pytest." See venv-usage-ssot.mdc.

Never rely on reminders alone — sub-agents need the full rules set.

## External libs

For prompts involving external libraries/APIs: append "use context7" to get current docs.
