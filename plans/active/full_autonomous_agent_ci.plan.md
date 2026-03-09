---
name: full-autonomous-agent-ci
overview: |
  Full multi-repo autonomous agent CI suite. Extends the single-repo agent_ci_prototype to all repos and adds four specialized agent types. Agents run overnight in tier order (T0->T1->T2->T3). Each tier runs repos in parallel via GHA matrix strategy. On QG failure, agents retry up to 3x with failure context. Telegram delivers morning summary. Dependency chain ordering enforced by GHA needs graph — no cross-tier contamination.
todos:
  - id: bootstrap-telegram
    content: >-
      Create Telegram bot via BotFather, note token. Start conversation with bot to get chat_id. Propagation script
      created: scripts/workspace/propagate-github-secrets.sh — runs against all 59 repos from workspace-manifest.json
      using gh secret set (TELEGRAM_BOT_TOKEN secret) and gh variable set (TELEGRAM_CHAT_ID variable). Steps: (1)
      @BotFather /newbot → copy token. (2) Get chat_id via @userinfobot or by sending a message and calling getUpdates.
      (3) Fill TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .act-secrets at workspace root. (4) Run:
      TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh
      (or run interactively — will prompt). (5) Verify: gh secret list --repo IggyIkenna/unified-trading-pm shows
      TELEGRAM_BOT_TOKEN; gh variable list shows TELEGRAM_CHAT_ID. GATE: dry-run passes (--dry-run flag) then live run
      shows 59 OK / 0 FAILED.
    status: in_progress
  - id: write-pm-rules-alignment-workflow
    content:
      "Create unified-trading-pm/.github/workflows/rules-alignment-agent.yml: trigger on push paths plans/active/**,
      clone codex as sister repo, run claude --print --dangerously-skip-permissions with prompt: read git diff HEAD~1
      for changed plan files, for each new constraint check cursor-rules/ for an .mdc file covering it, create missing
      rules following existing .mdc format (globs, description, body), quickmerge any new/changed rules files"
    status: completed
  - id: write-codex-docs-sync-workflow
    content:
      "Create unified-trading-codex/.github/workflows/codex-sync-agent.yml: trigger on repository_dispatch
      type=manifest-updated (this trigger was fixed in PR #1351 in PM manifest-sync.yml), clone PM as sister repo, run
      claude --print --dangerously-skip-permissions with prompt: read updated workspace-manifest.json and active PM
      plans, update docs/ to reflect current architecture, quickmerge changes"
    status: completed
  - id: write-semver-agent-workflow
    content:
      "Create .github/workflows/semver-agent.yml template: trigger on push to staging or main, run claude --print
      --dangerously-skip-permissions with prompt: read git diff for changes to __init__.py and exported symbols, read
      commit messages for feat!:/feat:/fix: prefixes, apply pre-1.0 rule (feat!=minor, feat=minor, fix=patch), update
      pyproject.toml version field, append CHANGELOG.md entry with date and summary, dispatch repository_dispatch
      type=version-updated to all dependent repos listed in workspace-manifest.json"
    status: completed
  - id: write-tier-orchestrator
    content:
      "Create unified-trading-pm/.github/workflows/overnight-agent-orchestrator.yml: schedule cron 0 1 * * *, read
      workspace-manifest.json to get repos per tier, dispatch workflow_dispatch to each T0 repo agent-audit.yml, wait
      for all T0 to complete (poll gh run list or use workflow_run trigger chain), then dispatch T1, T2, T3 in order.
      Send Telegram summary at end: pass count, fail count, blocked list."
    status: completed
  - id: rollout-agent-audit-yml
    content:
      "Create scripts/rollout-agent-workflows.sh: for each repo in workspace-manifest.json (excluding PM and codex),
      copy market-tick-data-service/.github/workflows/agent-audit.yml, replace SERVICE_NAME/SOURCE_DIR/LOCAL_DEPS
      variables, commit and quickmerge. Script should be idempotent (skip if workflow already exists and is up-to-date)."
    status: completed
  - id: wire-retry-dispatch
    content:
      "Update each agent-audit.yml (post-rollout) to add retry self-dispatch: add workflow_dispatch inputs attempt
      (default 1) and prior_context (default empty string). At end of workflow, on failure and attempt < 3, run gh
      workflow run agent-audit.yml --field attempt=$((attempt+1)) --field prior_context=$(cat failure-summary.txt).
      Include prior_context in claude prompt so agent knows what the previous attempt failed on."
    status: completed
  - id: rollout-plan-alignment-agent
    content:
      "Create .github/workflows/plan-alignment-agent.yml template: trigger on pull_request types opened synchronize,
      clone PM as sister repo to access active plans, run claude --print with prompt: read PR diff via gh pr diff, read
      all active PM plan todos, post gh pr comment if any diff changes are clearly out-of-scope for active plan tasks
      (advisory only, never block merge). Roll out to all repos via rollout script."
    status: completed
  - id: test-pm-quickmerge-cascade
    content:
      "Validate the full cascade: quickmerge a plan change in PM, verify manifest-sync.yml fires (check GHA logs),
      verify codex receives repository_dispatch type=manifest-updated, verify rules-alignment-agent checks new plan
      todos for rule coverage, verify Telegram receives all three notifications. This is the integration test for the
      whole system."
    status: pending
  - id: verify-tier-ordering
    content:
      Trigger overnight-agent-orchestrator manually (workflow_dispatch), verify in GHA that T1 jobs do not start until
      all T0 jobs complete, T2 waits on T1, T3 waits on T2. Verify no cross-tier repo contamination (each agent's
      ephemeral workspace only has read-only clones of deps, never writes to them). Unblocked after
      rollout-branch-protection completes.
    status: pending
  - id: rollout-branch-protection
    content: >-
      Set branch protection (require quality-gates status check + enable auto-merge) on all 52 service/API repos.
      Without branch protection, gh pr merge --auto merges immediately without waiting for CI to pass. Script: iterate
      workspace-manifest.json service/api-service tiers, call gh api repos/:owner/:repo/branches/main/protection with
      required_status_checks: {strict: true, contexts: [quality-gates]}. Prereq for gh pr merge --auto to actually gate
      on CI.
    status: pending
  - id: set-anthropic-api-key-sit
    content: >-
      Add ANTHROPIC_API_KEY secret to system-integration-tests repo so sit-plan-sync-agent.yml can run. Command: gh
      secret set ANTHROPIC_API_KEY --repo IggyIkenna/system-integration-tests. Verify: gh run list --workflow
      sit-plan-sync-agent.yml after next push to SIT main.
    status: pending
  - id: repos-update-pm-plans-in-gha
    content: >-
      Each service repo's agent-audit.yml adds a post-quickmerge step: after successful QG run, clone PM sibling
      (already done in setup-workspace.sh), find the plan todo(s) for this service, mark them completed, commit to the
      current PM branch, push. This allows PM to have up-to-date plan status before staging-to-main fires, eliminating
      circular reference between PM manifest updates and service repo merges. Design: add a
      scripts/update-pm-plan-status.sh helper that takes SERVICE_NAME and TODO_ID, updates the .plan.md YAML status
      field, and commits to the current PM branch.
    status: completed
    notes: |
      RESOLVED 2026-03-09: scripts/update-pm-plan-status.sh created — takes --service, --todo, --status, --notes,
      --plan, --dry-run; auto-discovers plan file by service name or todo ID; Python-based YAML line editor;
      auto-commits plan change to PM branch. Committed f771289.
  - id: pm-manifest-remote-ssot-check
    content: >-
      Add a pre-check to quickmerge.sh (before Stage 1): fetch origin/main of PM, compare versions block against local
      manifest. If local PM is behind remote: in interactive mode prompt user to pull; in GHA mode auto-pull. Prevents
      stale-manifest quickmerges where a service repo thinks a dep is at version X but PM remote already has it at X+1,
      causing constraint mismatches in downstream repos after merge.
    status: completed
    notes: |
      RESOLVED 2026-03-09: Stage 0.5 added to quickmerge.sh — fetches origin/main of unified-trading-pm, warns if
      local PM is N commits behind remote (shows hash diff); CI auto-pulls ff-only; interactive warns and continues.
      Skipped when running FROM unified-trading-pm itself to avoid self-check recursion. Committed f771289.
  - id: smoke-test-gate
    content: >-
      In system-integration-tests repo, add a GHA workflow (smoke-test-gate.yml) that triggers on push to staging
      branch, runs the smoke test suite (pytest tests/smoke/ or similar), and on success dispatches staging-validated
      event to unified-trading-pm. PM staging-to-main.yml is already wired to receive this dispatch and promote all
      repos from staging to main in topological order. This closes the loop on the staging-to-main automation. Blocked
      until: (1) SIT smoke tests exist in tests/smoke/, (2) SIT ANTHROPIC_API_KEY set (set-anthropic-api-key-sit todo).
    status: pending
isProject: false
---

# Full Autonomous Agent CI Suite

**Purpose:** Roll out the agent_ci_prototype pattern to all repos and add the four specialized agent workflows needed
for overnight autonomous operation.

**Depends on:** `agent_ci_prototype` plan completing the prototype todos (configure-github-repo-prototype,
add-github-secrets, test-manual-trigger-prototype).

**Scope:** All repos in workspace-manifest.json + PM + unified-trading-codex.

---

## System Architecture

```
PM push (plans/active/** changed)
  └── rules-alignment-agent.yml
        └── Claude checks cursor-rules/ coverage → creates missing .mdc → quickmerge

PM push (workspace-manifest.json or plans/ changed)
  └── manifest-sync.yml fires repository_dispatch type=manifest-updated to codex
        └── codex-sync-agent.yml
              └── Claude updates docs/ → quickmerge

Any repo PR opened/updated
  └── plan-alignment-agent.yml
        └── Claude reads diff + active plans → advisory PR comment (never blocks)

Any repo merge to staging/main
  └── semver-agent.yml
        └── Claude reads API diff + commits → bumps pyproject.toml + CHANGELOG → dispatches version-updated

Cron 01:00 UTC nightly
  └── overnight-agent-orchestrator.yml (PM)
        ├── T0 repos: parallel matrix (agent-audit.yml)
        │     ↓ all pass
        ├── T1 repos: parallel matrix (needs: t0)
        │     ↓ all pass
        ├── T2 repos: parallel matrix (needs: t1)
        │     ↓ all pass
        └── T3 repos: parallel matrix (needs: t2)
              ↓
        Telegram morning summary
```

## Retry Loop

Each `agent-audit.yml` self-dispatches on failure:

```yaml
on:
  workflow_dispatch:
    inputs:
      attempt: { default: '1' }
      prior_context: { default: '' }

- name: Self-dispatch on failure
  if: failure() && fromJSON(inputs.attempt) < 3
  run: |
    gh workflow run agent-audit.yml \
      --field attempt=$(({{ inputs.attempt }} + 1)) \
      --field prior_context="$(cat failure-summary.txt | head -50)"
```

Agent prompt includes `prior_context` so Claude knows what attempt N-1 failed on and does not repeat the same fix.

## Telegram Morning Summary Format

```
*Overnight QG Report 2026-03-07*
T0: 8/8 pass
T1: 5/6 pass | unified-internal-contracts BLOCKED (attempt 3/3)
T2: waiting on T1
Blocked repos: unified-internal-contracts (ruff E501 x3 after 3 attempts)
```

## Semver Decision Rules

| Commit pattern | API change     | Pre-1.0 bump | Post-1.0 bump |
| -------------- | -------------- | ------------ | ------------- |
| `feat!:`       | Breaking       | minor        | major         |
| `feat:`        | New export     | minor        | minor         |
| `fix:`         | None           | patch        | patch         |
| Any            | Removed export | minor        | major         |

Agent reads both commit messages AND actual API surface diff. Commit message takes precedence if it signals `feat!:`.

## Auth Requirements

Same as prototype — all repos need:

- `ANTHROPIC_API_KEY`
- `GH_PAT` (repo scope, all workspace repos)
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

The `rollout-agent-audit-yml` script should also set these secrets via `gh secret set` if provided as environment
variables during rollout.
