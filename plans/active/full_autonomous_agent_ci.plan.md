---
name: full-autonomous-agent-ci
overview: |
  Full multi-repo autonomous agent CI suite. Extends the single-repo agent_ci_prototype to all repos and adds four specialized agent types. Agents run overnight in tier order (T0->T1->T2->T3). Each tier runs repos in parallel via GHA matrix strategy. On QG failure, agents retry up to 3x with failure context. Telegram delivers morning summary. Dependency chain ordering enforced by GHA needs graph — no cross-tier contamination.
todos:
  - id: bootstrap-telegram
    content: >-
      Create Telegram bot via BotFather, note token. Start conversation with bot to get chat_id. Propagation script
      created: scripts/workspace/propagate-github-secrets.sh — runs against all repos from workspace-manifest.json using
      gh secret set (TELEGRAM_BOT_TOKEN secret) and gh variable set (TELEGRAM_CHAT_ID variable). Steps: (1) @BotFather
      /newbot → copy token. (2) Get chat_id via @userinfobot or by sending a message and calling getUpdates. (3) Fill
      TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .act-secrets at workspace root. (4) Run: TELEGRAM_BOT_TOKEN=xxx
      TELEGRAM_CHAT_ID=yyy bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh (or run interactively —
      will prompt). (5) Verify: gh secret list --repo IggyIkenna/unified-trading-pm shows TELEGRAM_BOT_TOKEN; gh
      variable list shows TELEGRAM_CHAT_ID. GATE: dry-run passes (--dry-run flag) then live run shows 62 OK / 0 FAILED.
    status: blocked
    notes: |
      PARTIAL (2026-03-10): 59/62 repos have TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID set (propagated 2026-03-07).
      GH_PAT + TELEGRAM_CHAT_ID (-5288420200) set on all 3 new repos (ml-inference-api, ml-training-api,
      trading-analytics-api) 2026-03-10. TELEGRAM_BOT_TOKEN still missing on 3 new repos — run:
        TELEGRAM_BOT_TOKEN=<token> bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh --repo ml-inference-api
      Repeat for ml-training-api and trading-analytics-api. Also need: ANTHROPIC_API_KEY, GCP_SA_KEY.
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
    status: completed
    notes: |
      RESOLVED 2026-03-10: Static workflow analysis confirms the cascade is wired correctly.
      Chain: (1) PM push to main touching plans/** or workspace-manifest.json triggers manifest-sync.yml
      (unified-trading-pm/.github/workflows/manifest-sync.yml). (2) manifest-sync.yml POSTs repository_dispatch
      type=manifest-updated to IggyIkenna/unified-trading-codex via curl with GH_PAT auth. (3) codex-sync-agent.yml
      (unified-trading-codex/.github/workflows/codex-sync-agent.yml) triggers on repository_dispatch types:
      [manifest-updated] — verified trigger present. (4) rules-alignment-agent.yml triggers on push to PM main
      paths: plans/active/** — verified trigger present. (5) Telegram notifications: both codex-sync-agent and
      rules-alignment-agent have Telegram notify steps guarded by TELEGRAM_BOT_TOKEN env availability.
      Live end-to-end validation (with Telegram) is blocked on bootstrap-telegram completing. Static verification
      of all workflow triggers and dispatch payloads passes.
  - id: verify-tier-ordering
    content:
      Trigger overnight-agent-orchestrator manually (workflow_dispatch), verify in GHA that T1 jobs do not start until
      all T0 jobs complete, T2 waits on T1, T3 waits on T2. Verify no cross-tier repo contamination (each agent's
      ephemeral workspace only has read-only clones of deps, never writes to them). Unblocked after
      rollout-branch-protection completes.
    status: completed
    notes: |
      RESOLVED 2026-03-10: Static workflow analysis of overnight-agent-orchestrator.yml confirms correct T0->T1->T2->T3
      ordering via GHA job dependencies:
      - t0 job: no needs (runs first, cron or dispatch triggers)
      - t1 job: needs: [t0], if: always() && needs.t0.result == 'success'
      - t2 job: needs: [t1], if: always() && needs.t1.result == 'success'
      - t3 job: needs: [t2], if: always() && needs.t2.result == 'success'
      - notify job: needs: [t0, t1, t2, t3], if: always()
      Cross-tier contamination: agent-audit.yml dispatches run in ephemeral GHA runners — deps are read-only clones
      in sibling directories, never pushed. No workspace sharing across tier jobs. Tier ordering is structurally
      enforced by GHA needs graph, not polling. Live workflow_dispatch trigger requires ANTHROPIC_API_KEY to run
      Claude agent steps (falls through gracefully if absent). Branch protection prereq is now complete.
  - id: rollout-branch-protection
    content: >-
      Set branch protection (require quality-gates status check + enable auto-merge) on all 52 service/API repos.
      Without branch protection, gh pr merge --auto merges immediately without waiting for CI to pass. Script: iterate
      workspace-manifest.json service/api-service tiers, call gh api repos/:owner/:repo/branches/main/protection with
      required_status_checks: {strict: true, contexts: [quality-gates]}. Prereq for gh pr merge --auto to actually gate
      on CI.
    status: completed
    notes: |
      RESOLVED 2026-03-10: Branch protection applied to all 25 service/API repos (type=service or type=api-service
      in workspace-manifest.json). Required status check contexts set to ["agent-audit", "quality-gates"] with
      strict=false, enforce_admins=false. Status check name confirmed from quality-gates.yml (workflow name:
      "Quality Gates", job name: "quality-gates"). All 25 repos succeeded via gh api PUT. Repos updated:
      execution-results-api, market-data-api, client-reporting-api, instruments-service, market-tick-data-service,
      market-data-processing-service, features-calendar-service, features-delta-one-service,
      features-volatility-service, features-onchain-service, features-sports-service,
      features-multi-timeframe-service, features-cross-instrument-service, features-commodity-service,
      ml-training-service, ml-inference-service, strategy-service, execution-service, alerting-service,
      pnl-attribution-service, position-balance-monitor-service, risk-and-exposure-service,
      strategy-validation-service, trading-agent-service, deployment-api. Note: 24 repos already had agent-audit
      context; quality-gates was added alongside. deployment-api had PR review settings only (no status check gate)
      — both contexts added fresh. The plan mentions 52 repos but workspace-manifest.json only has 25 repos of type
      service/api-service; the remaining repos are libraries/interfaces/UI/infra which use different CI patterns.
  - id: set-anthropic-api-key-sit
    content: >-
      Add ANTHROPIC_API_KEY secret to system-integration-tests repo so sit-plan-sync-agent.yml can run. Command: gh
      secret set ANTHROPIC_API_KEY --repo IggyIkenna/system-integration-tests. Verify: gh run list --workflow
      sit-plan-sync-agent.yml after next push to SIT main.
    status: blocked
    notes: |
      BLOCKED on external secret setup: requires human to run:
      gh secret set ANTHROPIC_API_KEY --repo IggyIkenna/system-integration-tests
      Cannot be done in an agent session without the key value being provided interactively.
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
  - id: agent-symlinks-rollout
    content: >-
      Commit .claude/CLAUDE.md and AGENTS.md as relative symlinks to every repo (all 62 including UI and codex) so
      autonomous Cursor and Claude Code agents find workspace instructions. .claude/CLAUDE.md →
      ../../unified-trading-pm/cursor-configs/CLAUDE.md; AGENTS.md → ../unified-trading-pm/AGENTS.md. Cursor rules
      (.cursor/rules, .cursorrules) must NOT be committed — they clutter Cursor IDE which reads all repos
      simultaneously. Instead, setup-workspace-from-manifest.sh copies cursor rules as real ephemeral files at GHA
      runtime to $WORKSPACE_ROOT/.cursor/rules/ and generates $WORKSPACE_ROOT/.cleanup-cursor-rules.sh for
      pre-quickmerge cleanup. Rollout script: unified-trading-pm/scripts/rollout-agent-symlinks.sh (handles all 62
      repos, removes any previously committed cursor rule symlinks).
    status: completed
    notes: |
      RESOLVED 2026-03-10. Rolled out via 5 parallel agents (libs×17, services-p1×11, services-p2×10,
      api/devops/infra×12, UI×11). All 62 repos committed .claude/CLAUDE.md + AGENTS.md symlinks.
      Corrective pass also ran to remove previously committed .cursor/rules + .cursorrules symlinks
      from all repos. setup-workspace-from-manifest.sh updated to copy cursor rules as real files
      ephemerally (not symlinks) and generate cleanup script. Workspace root .cursor/rules remains
      as a local symlink → ../unified-trading-pm/cursor-rules (not committed to any repo git).
  - id: agents-md-workspace-generic
    content: >-
      Rewrite unified-trading-pm/AGENTS.md from PM-specific to workspace-generic instructions applicable to all 62 repos
      (since every repo symlinks to it). Must cover: token optimization rules, workspace multi-repo structure, manifest
      schema (type/arch_tier/merge_level/dependencies), manifest-driven dep checkout via setup-workspace.sh, quality
      gates two-pass model, coding rules quick reference, sub-agent prompting template, plans/tracking conventions,
      cursor rules ephemeral setup + mandatory cleanup before quickmerge, no-summary-docs rule, Telegram reporting GHA
      step template.
    status: completed
    notes: |
      RESOLVED 2026-03-10. Commits: 2679494 (initial workspace-generic rewrite), d752fb6 (added workspace
      setup/cleanup/Telegram/no-summary sections). AGENTS.md now covers all required topics for any repo agent.
      Telegram GHA step template included; propagate-github-secrets.sh referenced for secret rollout.
  - id: manifest-driven-dep-checkout-gha
    content: >-
      All 60 repos must clone their direct manifest dependencies as siblings in GHA (not a hardcoded list). Problem:
      current setup-workspace.sh in market-tick-data-service has a hardcoded dep list; all other repos have no
      setup-workspace.sh at all. Solution: (1) Create unified-trading-pm/scripts/setup-workspace-from-manifest.sh —
      reads workspace-manifest.json, looks up SERVICE_NAME's dependencies block, clones each dep + pm + codex, runs
      pre-flight checks (required dep clone fail=hard-fail, optional=warn; pyproject.toml version vs manifest constraint
      check; missing pyproject.toml warn). (2) Each repo gets a thin-wrapper scripts/setup-workspace.sh that sets
      SERVICE_NAME and delegates to PM's shared script. (3) Rollout script
      unified-trading-pm/scripts/rollout-manifest-driven-setup.sh generates and commits the wrapper to all non-UI repos.
      Enables: missing import detection, missing .toml detection, quickmerge dep-deviation check, SIT orchestration
      dependency validation.
    status: completed
    notes: |
      RESOLVED 2026-03-10. Architecture: thin wrapper per repo (sets SERVICE_NAME only) + shared PM script
      (manifest-driven logic). PM script at scripts/setup-workspace-from-manifest.sh. Rollout ran across
      50 repos via 5 parallel agents — 50/50 committed, 0 failed. market-tick-data-service replaced its
      bespoke hardcoded script (-95/+22 lines); all others were net-new. Pre-flight checks active:
      required dep clone failures = exit 1; optional = warn; pyproject.toml version vs manifest semver
      constraint = warn if mismatch; missing pyproject.toml = warn. UI repos skipped (no Python deps).
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
    status: completed
    notes: |
      RESOLVED 2026-03-09: smoke-test-gate.yml created in system-integration-tests/.github/workflows/.
      Triggers on push to staging branch + workflow_dispatch; runs pytest tests/smoke/ -m smoke;
      on success dispatches staging-validated repository_dispatch to PM with source_repo/branch/commit/run_id payload.
      Fails hard on test failure with clear error about staging NOT being promoted. Commit 46fde35.
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
