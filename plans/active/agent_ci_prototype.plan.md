---
name: agent-ci-prototype
overview: Prototype autonomous agent CI pipeline for market-tick-data-service. Agent bootstraps a full workspace, runs the canonical audit, unit tests, quality gates, and quickmerge to auto-merge to main when CI passes.
todos:
  - id: create-github-workflow
    content: "Create .github/workflows/agent-audit.yml in market-tick-data-service: workflow_dispatch trigger, clones all sibling deps + pm + codex into ephemeral workspace, sets GH_TOKEN from GH_PAT secret, installs Python 3.13 + uv + claude-code-sdk, runs scripts/run-agent.sh"
    status: completed
  - id: create-quality-gates
    content: "Create market-tick-data-service/scripts/quality-gates.sh adapted from quality-gates-service-template.sh with SERVICE_NAME=market-tick-data-service, SOURCE_DIR=market_tick_data_service, all 8 LOCAL_DEPS wired"
    status: completed
  - id: create-setup-workspace
    content: "Create market-tick-data-service/scripts/setup-workspace.sh: accepts WORKSPACE_ROOT, clones all sibling repos via GH_TOKEN, creates .cursor/rules symlink, runs uv pip install -e .[dev]"
    status: completed
  - id: create-quickmerge
    content: "Create market-tick-data-service/scripts/quickmerge.sh as a copy of unified-trading-pm/scripts/quickmerge.sh (canonical SSOT; local copy needed for CI context where relative paths don't resolve)"
    status: completed
  - id: create-run-agent
    content: "Create market-tick-data-service/scripts/run-agent.sh: orchestrates audit prompt → quality gates → quickmerge. Calls claude --print --dangerously-skip-permissions with trading_system_audit_prompt contents."
    status: completed
  - id: configure-github-repo
    content: "Configure market-tick-data-service repo: Settings > General > Allow auto-merge: ON; branch protection rule for main requiring quality-gates status check to pass before merging"
    status: pending
  - id: add-github-secrets
    content: "Add ANTHROPIC_API_KEY and GH_PAT (with repo scope on all workspace repos) to market-tick-data-service repo secrets"
    status: pending
  - id: test-manual-trigger
    content: "Trigger Actions > agent-audit > Run workflow manually; verify all 5 quickmerge stages pass, PR is created, CI passes, auto-merge happens"
    status: pending
  - id: verify-no-secrets-committed
    content: "Verify: git log --all -- '*.env' '*.secrets' shows nothing; workflow YAML contains no hardcoded tokens"
    status: pending
isProject: false
---

# Agent CI Prototype — market-tick-data-service

**Purpose:** Prototype a fully autonomous agent pipeline for `market-tick-data-service`. Once validated here, this pattern will be rolled out to all 52 service repos.

**Scope:** Single repo prototype — `market-tick-data-service`

**SSOT:** This plan is the canonical tracking artifact. Claude Code working notes at `.claude/plans/hashed-meandering-frost.md`.

---

## Architecture

```
GitHub Actions runner (ubuntu-latest, ephemeral)
  workspace/
    market-tick-data-service/   <- checkout
    unified-api-contracts/      <- cloned via GH_PAT
    unified-internal-contracts/
    unified-trading-library/
    unified-domain-client/
    unified-events-interface/
    unified-config-interface/
    unified-market-interface/
    unified-sports-execution-interface/
    unified-trading-pm/         <- cloned (quickmerge + rules)
    unified-trading-codex/      <- cloned (audit prompt + standards)
    .cursor/rules/              <- symlink -> unified-trading-pm/cursor-rules/
```

## Auth (Secrets)

| Secret              | Purpose                                                                                                                           |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `ANTHROPIC_API_KEY` | Claude Code SDK invocation                                                                                                        |
| `GH_PAT`            | Everything: clone private repos, create PRs, auto-merge. Exposed as `GH_TOKEN` in workflow env so `gh` CLI uses it automatically. |

`GH_PAT` requires `repo` scope (read+write) on all workspace repos. Built-in `GITHUB_TOKEN` is NOT used.

## Agent Invocation

```bash
claude --print --dangerously-skip-permissions \
  "$(cat unified-trading-pm/plans/active/trading_system_audit_prompt.plan.md)" \
  > audit-report.txt
```

- `--print`: non-interactive (no REPL)
- `--dangerously-skip-permissions`: allows tool use (bash, file read/write) without prompts

## Quickmerge Flags in CI

```bash
bash scripts/quickmerge.sh "agent: audit + quality gates pass" --quick --files "..."
```

- `--quick`: skips `act` simulation (we're already in CI)
- No `--skip-tests` or `--skip-typecheck` — hardened logic only

## Auto-merge Flow

1. `quickmerge.sh` → PR branch → push → `gh pr create` → `gh pr merge --auto --squash`
2. GH Actions CI `quality-gates` job runs on the PR
3. CI passes → GitHub squash-merges to main and deletes branch
4. CI fails → PR stays open, re-trigger agent

## GitHub Repo Settings Required

- `Settings > General > Allow auto-merge: ON`
- Branch protection on `main`: require `quality-gates` status check before merging
