#!/usr/bin/env bash
# Epic: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06
# Lifecycle: temporary
# Delete-when: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md todo 9 ships
#
# Per-repo shipper for the flat-copy -> thin-caller-stub migration. FILES list below is
# todo-4-shaped (main-backmerge-to-ldr.yml + 4 siblings) -- for todo 5 (semver-agent.yml.tmpl)
# change FILES to just that one file and confirm the per-repo self-hosted flag list is still
# accurate (scripts/workflow-templates/self-hosted-qg-repos.txt is the live source, don't
# hand-copy the list below without re-checking it first).
#
# Recovery pattern this script encodes (learned the hard way, 2026-08-07): on this heavily
# concurrent shared workspace, `git commit` immediately after writing (closing the race
# window) beats "write then quickmerge" -- quickmerge's own "already committed, nothing to
# stage" check can race a DIFFERENT session's commit and silently no-op. ALWAYS verify via
# `git show origin/<branch>:<path>` after -- never trust quickmerge's own "✅ Landed" message
# alone (shared_clone_concurrent_commit_message_swap_2026_07_28.md class of bug, hit twice
# this session, including one case that lost generated content entirely, recovered by
# regenerating -- cheap since it's script-derived, not hand-typed).
#
# Usage: bash ship_repo.sh <repo-name> <0|1 self-hosted> <0|1 is-PM>
set -euo pipefail

WORKSPACE=/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1
TEMPLATES="$WORKSPACE/unified-trading-pm/scripts/workflow-templates"
repo="$1"
sh_flag="$2"   # 1 if self-hosted repo, else 0
is_pm="${3:-0}"

cd "$WORKSPACE/$repo"
git fetch origin -q

if [ "$is_pm" = "1" ]; then
  FILES="main-backmerge-to-ldr.yml"
else
  FILES="main-backmerge-to-ldr.yml major-bump-issue-handler.yml request-major-bump.yml staging-backmerge-to-ldr.yml update-dependency-version.yml"
fi

CHANGED=""
for f in $FILES; do
  if [ -f ".github/workflows/$f" ]; then
    python3 /tmp/make_stub.py "$TEMPLATES/$f" "$sh_flag" > ".github/workflows/$f"
    CHANGED="$CHANGED .github/workflows/$f"
  fi
done

if [ -z "$CHANGED" ]; then
  echo "[$repo] no applicable files"
  exit 0
fi

if git diff --quiet -- $CHANGED && git diff --cached --quiet -- $CHANGED; then
  echo "[$repo] no diff after regenerate (already converted?) -- checking remote"
else
  git add $CHANGED
  git commit -m "ci: fleet workflows -> thin caller stubs against unified-trading-ci (fleet dedup)

fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md todo 4.

Quickmerge: agent" -q
fi

bash scripts/quickmerge.sh "ci: fleet workflows -> thin caller stubs against unified-trading-ci (fleet dedup)" --agent --files "$CHANGED" > /tmp/quickmerge_out_$repo.log 2>&1
tail -8 /tmp/quickmerge_out_$repo.log

git fetch origin -q
FIRST_FILE=$(echo $CHANGED | awk '{print $1}')
if git show "origin/live-defi-rollout:$FIRST_FILE" 2>/dev/null | grep -q "uses: IggyIkenna/unified-trading-ci"; then
  echo "[$repo] VERIFIED landed"
else
  echo "[$repo] *** NOT LANDED -- needs retry ***"
fi
