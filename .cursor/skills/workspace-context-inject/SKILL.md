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
- Plans live in unified-trading-pm/plans/ai or unified-trading-pm/plans/active
- uv not pip; basedpyright not pyright; quickmerge not git push
- Delete deprecated code; no parallel code paths
- Search unified libraries before implementing anything new

## For sub-agents (Task tool)

When launching any sub-agent, add to the prompt:

"Follow all workspace cursor rules in .cursorrules. See no-summary-docs.mdc for documentation rules; plans only in
unified-trading-pm or unified-trading-pm/plans/ai/. uv not pip, basedpyright not pyright, quickmerge not git push.
Delete deprecated code; no parallel code paths — see delete-deprecated.mdc. Search unified libraries before implementing
anything new."

## External libs

For prompts involving external libraries/APIs: append "use context7" to get current docs.
