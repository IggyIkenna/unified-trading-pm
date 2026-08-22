#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# inject-mandatory-rules.sh — Generates the mandatory rules preamble for ANY autonomous agent prompt.
#
# SSOT: unified-trading-pm/scripts/agents/inject-mandatory-rules.sh
#
# Usage (in shell scripts):
#   RULES_PREAMBLE=$(bash unified-trading-pm/scripts/agents/inject-mandatory-rules.sh "$WORKSPACE_ROOT" "$TARGET_REPO")
#   FULL_PROMPT="${RULES_PREAMBLE}\n\n${TASK_PROMPT}"
#
# Usage (in GHA workflows — inline):
#   RULES_PREAMBLE=$(bash unified-trading-pm/scripts/agents/inject-mandatory-rules.sh "$(pwd)" "$REPO_NAME")
#
# Arguments:
#   $1 — WORKSPACE_ROOT (absolute path to workspace)
#   $2 — TARGET_REPO (repo name the agent will edit, or "all" for workspace-wide agents)
#
# Output: Full text preamble to prepend to any agent prompt. Includes:
#   1. SUB_AGENT_MANDATORY_RULES.md (complete)
#   2. Workspace context block (WORKSPACE_ROOT, target repo, edit restrictions)
#   3. Critical operational rules (venv, quality gates, basedpyright, git safety)
#
# WHY THIS EXISTS:
#   Agents in --print mode CANNOT read files from disk. Telling them "read .cursorrules"
#   is useless — they never see it. The rules MUST be pasted into the prompt text itself.
#   This script ensures every agent entrypoint injects identical, complete rules.
#   Without this, agents silently ignore workspace standards (pip instead of uv,
#   os.getenv instead of UnifiedCloudConfig, pytest instead of quality-gates.sh, etc.)

set -euo pipefail

WORKSPACE_ROOT="${1:?Usage: inject-mandatory-rules.sh <WORKSPACE_ROOT> <TARGET_REPO>}"
TARGET_REPO="${2:?Usage: inject-mandatory-rules.sh <WORKSPACE_ROOT> <TARGET_REPO>}"

PM_DIR="${WORKSPACE_ROOT}/unified-trading-pm"
RULES_FILE="${PM_DIR}/cursor-configs/SUB_AGENT_MANDATORY_RULES.md"

# ── Validate ─────────────────────────────────────────────────────────────────
if [ ! -f "$RULES_FILE" ]; then
  echo "ERROR: SUB_AGENT_MANDATORY_RULES.md not found at $RULES_FILE" >&2
  echo "Agent MUST NOT proceed without mandatory rules." >&2
  exit 1
fi

# ── Emit preamble ────────────────────────────────────────────────────────────
cat <<PREAMBLE_EOF
# ══════════════════════════════════════════════════════════════════════════════
# MANDATORY RULES — READ BEFORE ANY ACTION
# You are an autonomous agent. You MUST follow ALL rules below.
# Failure to follow these rules will produce incorrect, unsafe, or rejected work.
# ══════════════════════════════════════════════════════════════════════════════

$(cat "$RULES_FILE")

# ══════════════════════════════════════════════════════════════════════════════
# WORKSPACE CONTEXT
# ══════════════════════════════════════════════════════════════════════════════

- Workspace root: ${WORKSPACE_ROOT}
- Target repo: ${TARGET_REPO}
$(if [ "$TARGET_REPO" != "all" ]; then
cat <<RESTRICT
- You have READ access to the entire workspace (codex, dependencies, workspace rules)
- You can ONLY EDIT files in ${TARGET_REPO}/ directory
- DO NOT edit unified-trading-codex/, unified-trading-library/, unified-trading-pm/, or other repos
RESTRICT
else
cat <<FULL
- You have READ and WRITE access to the workspace
- Respect per-repo boundaries — commit only to the repo you are changing
FULL
fi)

# ══════════════════════════════════════════════════════════════════════════════
# CRITICAL OPERATIONAL RULES (reinforced — agents violate these most often)
# ══════════════════════════════════════════════════════════════════════════════

1. NEVER run \`pytest\` or \`python -m pytest\` directly — ALWAYS \`cd <repo> && bash scripts/quality-gates.sh\`
2. NEVER use \`pip install\` — ALWAYS \`uv pip install\`
3. NEVER use \`os.getenv()\` — ALWAYS \`UnifiedCloudConfig\`
4. NEVER run \`basedpyright .\` or \`basedpyright\` (no args) — ALWAYS \`timeout 120 basedpyright <source_dir>/\`
5. NEVER use \`git push\` **alone** to land work — ALWAYS \`bash scripts/quickmerge.sh "msg" --agent\` for commit+PR. **Exception:** if the branch has **unpushed commits** before quickmerge, run \`git push -u origin <branch>\` first so \`origin/<branch>\` matches your tip (stash does not protect commits). See \`always-use-quickmerge.mdc\` § Push before quickmerge.
6. NEVER use \`--dep-branch\` — it is HUMAN-ONLY and exits(1) with \`--agent\`
7. NEVER run \`git reset --hard\`, \`git clean -fd\`, or \`git checkout .\` — these destroy work
8. NEVER create *_SUMMARY.md, *_STATUS.md, READY_TO_*, COMPLETION_* files
9. NEVER use \`try/except ImportError\` around library imports — fail loud
10. NEVER use \`# type: ignore\` to hide architectural violations — fix the root cause
11. For tests: \`cd <repo> && bash scripts/quality-gates.sh\` (per-repo .venv). NEVER .venv-workspace for pytest.
12. Only run basedpyright 2-3 times total per session — once to see errors, once to verify fix.

# ══════════════════════════════════════════════════════════════════════════════
# SELF-CHECK: If you catch yourself about to use pip, os.getenv, git push **instead of**
# quickmerge, pytest directly, or basedpyright without a source dir — STOP. Re-read above.
# (A safety \`git push\` to sync an unpushed branch tip before quickmerge is OK.)
# ══════════════════════════════════════════════════════════════════════════════

PREAMBLE_EOF
