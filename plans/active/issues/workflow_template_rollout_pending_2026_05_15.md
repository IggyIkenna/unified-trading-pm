---
title: workflow-template rollout pending — 22 repos, 3 templates, script bug fixed
created: 2026-05-15
author: slot-8
source:
  - scripts/workflow-templates/rollout-workflow-templates.sh
  - scripts/workflow-templates/semver-agent.yml.tmpl
locked_by: live-defi-rollout
---

## What I found

`bash scripts/workflow-templates/rollout-workflow-templates.sh --dry-run` shows **3 templates need propagation** across **22 repos**.

### Critical script bug (FIXED — PM@542f0e26)

`rollout-workflow-templates.sh` only substituted `{{DEP_REPOS}}` for `.tmpl` files but NOT `__REPO_NAME__` or `__SOURCE_DIR__`. Running the rollout would have overwritten correctly-deployed per-repo `semver-agent.yml` files with raw template placeholders (`__REPO_NAME__`, `__SOURCE_DIR__`), breaking CI semver-agent for all 22 repos.

**Fix applied**: added `repo_underscore="${repo//-/_}"` + sed substitution for `__REPO_NAME__`/`__SOURCE_DIR__` in the `.tmpl` processing block.

### Templates needing propagation (post-fix, legitimate content changes)

| Template | Change | Repos affected |
|---|---|---|
| `semver-agent.yml.tmpl` | Codex repo consolidated into PM (`unified-trading-pm/codex/10-audit/` vs old `unified-trading-codex/`); new "Dispatch schema-changed to PM" step for T0 libraries; removed `concurrency` block | 22 repos |
| `major-bump-issue-handler.yml` | Multi-environment Telegram routing (prod/staging/dev tokens) | 22 repos |
| `update-dependency-version.yml` | Direct copy update (check diff) | 22 repos |

### New templates to create (not yet in any repos)

| Template | Target | Notes |
|---|---|---|
| `uac-registry-sync.yml` | `unified-trading-system-ui` only | Dispatched on `uac-registry-updated` event |
| `uic-openapi-sync.yml` | `unified-trading-system-ui` only | Dispatched on `uac-openapi-updated` event |
| `workspace-qg.yml.tmpl` | All service repos with `.github/workflows/` | Cross-repo QG trigger with `{{DEP_REPOS}}` |

**Note**: `uac-registry-sync.yml` and `uic-openapi-sync.yml` should only go to `unified-trading-system-ui`, not all repos. The rollout script currently deploys them everywhere — this needs a repo-filter guard before running.

## How to propagate

```bash
cd /home/hk/unified-trading-system-repos/unified-trading-pm

# Step 1: Run rollout (script bug now fixed)
bash scripts/workflow-templates/rollout-workflow-templates.sh \
  --template semver-agent.yml 2>&1  # or run without filter for all

# Step 2: Per repo — commit and push
for repo in alerting-service batch-live-reconciliation-service ...; do
  cd /home/hk/unified-trading-system-repos/$repo
  git fetch origin
  git add .github/workflows/
  git commit -m "ci: roll out workflow templates (semver-agent + major-bump + dep-update)"
  git push origin HEAD:live-defi-rollout
done
```

**Before running**: add repo-filter guard in rollout script for `uac-registry-sync.yml` and `uic-openapi-sync.yml` (UI-only templates).

## Why it matters

- Semver-agent references old `unified-trading-codex` repo that no longer exists as a standalone repo — will fail at checkout step when triggered
- Major-bump Telegram notifications go to wrong channel if per-env routing not applied
- New `workspace-qg.yml` template enables cross-repo QG triggering on dep updates

## Recommended decision

- P1: Propagate `semver-agent.yml` to all 22 repos (codex path fix is critical — triggers on staging push)
- P1: Propagate `major-bump-issue-handler.yml` (Telegram multi-env routing)
- P2: Add repo-filter guard in rollout script for UI-only templates, then propagate `workspace-qg.yml`
- P2: Deploy `uac-registry-sync.yml` + `uic-openapi-sync.yml` to `unified-trading-system-ui` only
