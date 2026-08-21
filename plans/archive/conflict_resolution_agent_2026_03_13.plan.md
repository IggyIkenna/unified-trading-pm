---
doc_type: plan
title: conflict-resolution-agent
summary:
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-13'
overview: 'Autonomous conflict resolution agent for the unified-trading-system CI pipeline. Triggered by merge-conflict-detected repository_dispatch (from staging-to-main.yml or feature-branch-to-staging.yml template). Sets up workspace via setup-workspace-from-manifest.sh, reads AGENTS.md + active PM plans + codex docs for context, uses Claude to propose a conflict resolution (preserving both sides), runs quality gates on the resolved code, pushes an auto-resolve branch, opens a resolution PR, and notifies via Telegram at start ("working") and end ("PR ready"). Humans review and approve; agent never self-merges.

  '
type: infra
epic: epic-infra
superseded_by: cicd_code_rollout_master_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C4, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-pm, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: GHA workflow — no cloud deployment. BR N/A: internal tooling.'}
depends_on: [full_autonomous_agent_ci]
todos:
- {id: create-conflict-resolution-agent-workflow, content: 'Create unified-trading-pm/.github/workflows/conflict-resolution-agent.yml. Trigger: repository_dispatch type=merge-conflict-detected + workflow_dispatch (inputs: repo_name, source_branch, target_branch, original_pr_url). Steps: (1) Telegram "working" immediately; (2) clone repo (depth=50) + PM + codex siblings, run scripts/setup-workspace-from-manifest.sh <repo_name> for manifest-driven dep checkout; (3) read AGENTS.md + SUB_AGENT_MANDATORY_RULES.md + all active PM plans for context; (4) surface conflicts via git checkout target, git merge --no-commit --no-ff origin/source || true, git diff --name-only --diff-filter=U, capture full conflict content per file, git merge --abort; (5) claude --print --dangerously-skip-permissions with AGENTS.md + rules + plans preamble + conflict dump (preserve both sides, output === filename === blocks); (6) parse claude output (awk split on === filename === markers) + write resolved files to auto-resolve/<source>-to-<target>-<sha>
    branch + git push; (7) bash scripts/quality-gates.sh, capture exit code (non-zero = advisory, PR still created); (8) gh pr create resolution branch → target with body noting QG result + original PR URL; (9) Telegram "done" with resolution PR URL + files resolved + QG result.

    ', status: pending}
- {id: wire-staging-to-main-conflict-dispatch, content: 'Modify unified-trading-pm/.github/workflows/staging-to-main.yml. In the per-repo loop, inside the else branch (PR creation failed, ~line 202): add conflict detection via GitHub REST API — list open PRs for staging→main, get mergeable_state (poll 3× with 5s sleep for GitHub''s async computation), check if mergeable_state == "dirty" (GitHub REST uses "dirty" for merge conflicts). If dirty: (1) send Telegram "⚠️ Merge Conflict: $REPO staging→main, agent dispatched"; (2) dispatch repository_dispatch merge-conflict-detected to unified-trading-pm with {repo_name, source_branch: staging, target_branch: main, original_pr_url}. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to the step env block. Existing FAILED list accumulation stays unchanged.

    ', status: pending}
- {id: wire-feature-to-staging-conflict-dispatch, content: 'Modify unified-trading-pm/scripts/propagation/templates/feature-branch-to-staging.yml. Add step "Detect merge conflict and dispatch resolution agent" after the Telegram notify step (end of file). Step runs if: always() so it fires even when auto-merge was skipped. Logic: poll gh pr view $PR_NUMBER --json mergeable -q .mergeable (3× with 5s sleep) until not null. If MERGEABLE == CONFLICTING: (1) Telegram "⚠️ Conflict on {{SERVICE_NAME}} $FEATURE_BRANCH→staging, agent dispatched"; (2) dispatch merge-conflict-detected to unified-trading-pm with {repo_name: {{SERVICE_NAME}}, source_branch: FEATURE_BRANCH, target_branch: staging, original_pr_url: PR_URL}. Requires: GH_PAT (already available), TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID (already in template env from Telegram notify step).

    ', status: pending}
- {id: register-plan-in-ssot-index, content: 'Add plan row to unified-trading-codex/00-SSOT-INDEX.md (after the full_autonomous_agent_ci row, ~line 55) and add row 68 to unified-trading-pm/plans/active/INDEX.md (after row 67, before the Supporting Plans section).

    ', status: pending}
isProject: false
---

# Conflict Resolution Agent

**Purpose:** Close the gap where merge conflicts silently park PRs with no automated recovery. GitHub auto-merge IS
disabled by `mergeable_state=dirty` — CI passing does not unblock it. This agent detects conflicts on both integration
paths and proposes resolutions for human review.

**Depends on:** `full_autonomous_agent_ci` (secrets rollout, agent-audit.yml pattern, Telegram wiring).

---

## Trigger Paths

```
feat→staging PR (service repo feature-branch-to-staging.yml)
  └── QG passes → PR created → auto-merge enabled
        └── [if mergeable_state=CONFLICTING after 15s poll]
              ├── Telegram: "⚠️ Conflict: {{SERVICE_NAME}} feature→staging, dispatching..."
              └── repository_dispatch: merge-conflict-detected → unified-trading-pm

staging→main promotion (staging-to-main.yml)
  └── gh pr create fails (PR exists or new conflict)
        └── [check existing PR mergeable_state via REST API]
              └── [if mergeable_state=dirty]
                    ├── Telegram: "⚠️ Conflict: $REPO staging→main, dispatching..."
                    └── repository_dispatch: merge-conflict-detected → unified-trading-pm
```

## Agent Resolution Flow

```
conflict-resolution-agent.yml (unified-trading-pm)
  triggered by: repository_dispatch merge-conflict-detected
  │
  ├── Telegram: "⚠️ Conflict detected in $REPO, agent working on resolution..."
  │
  ├── Workspace setup
  │     git clone $REPO (depth=50) + PM + codex siblings
  │     bash unified-trading-pm/scripts/setup-workspace-from-manifest.sh $REPO
  │     (clones all manifest deps as siblings)
  │
  ├── Context read
  │     cat unified-trading-pm/AGENTS.md
  │     cat unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md
  │     cat unified-trading-pm/plans/active/*.md (head -200 for token budget)
  │
  ├── Surface conflicts
  │     git checkout $TARGET_BRANCH
  │     git merge --no-commit --no-ff origin/$SOURCE_BRANCH || true
  │     CONFLICTED=$(git diff --name-only --diff-filter=U)
  │     capture full conflict content → /tmp/conflict_dump.txt
  │     git merge --abort
  │
  ├── Claude resolution
  │     Prompt preamble: AGENTS.md + SUB_AGENT_MANDATORY_RULES.md + active plans context
  │     Rules: preserve both sides, union imports, output === filename === blocks
  │     Output: parsed into resolved file contents
  │
  ├── Apply + commit
  │     git checkout $SOURCE_BRANCH
  │     git checkout -b auto-resolve/<source>-to-<target>-<sha>
  │     write resolved files, git add -u, git commit "[skip ci]"
  │     git push origin auto-resolve/...
  │
  ├── Quality gates
  │     bash scripts/quality-gates.sh (result is advisory — PR still created on failure)
  │
  ├── Resolution PR
  │     gh pr create --base $TARGET_BRANCH --head auto-resolve/...
  │     body: original PR link, files resolved, QG result, "review before merging"
  │
  └── Telegram: "✅ Resolution PR ready"
        Repo, branches, files resolved (n), QG: pass/fail, PR URL, original blocked PR URL
```

## What the Agent Does NOT Do

- Does not run quickmerge (the thing is already mid-merge, no further push needed)
- Does not merge the resolution PR — human must approve
- Does not handle dependency version conflicts (`--dep-branch` path for those)
- Does not handle semver label mismatches (semver-agent handles those)
- Does not retry indefinitely — one resolution attempt, human takes it from there

## Secrets Required

All already rolled out to all repos via `full_autonomous_agent_ci`:

- `ANTHROPIC_API_KEY`
- `GH_PAT`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID` (note: some workflows use `vars.TELEGRAM_CHAT_ID` — check PM workflow convention)

## Telegram Message Formats

**On detection (sent by the triggering workflow, before dispatch):**

```
⚠️ *Merge Conflict Detected*
Repo: `<repo_name>`
`<source_branch>` → `<target_branch>`
Blocked PR: <url or N/A>
Agent dispatched to resolve...
```

**On resolution ready (sent by conflict-resolution-agent.yml):**

```
✅ *Conflict Resolution Ready*
Repo: `<repo_name>`
`<source_branch>` → `<target_branch>`
Files resolved: <n> (<file1>, <file2>)
QG: ✅ pass / ⚠️ fail — review before merging
Resolution PR: <PR URL>
Original blocked PR: <url or N/A>
Review and merge when ready.
```
