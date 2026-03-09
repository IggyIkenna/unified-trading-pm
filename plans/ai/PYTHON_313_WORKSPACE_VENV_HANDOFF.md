# Python 3.13.x + .venv-workspace Handoff — Agent Takeover

**Created:** 2026-03-09 **Purpose:** Status and remaining work for agents to complete the Python 3.13.x /
.venv-workspace rollout and quickmerge.

---

## 1. Completed Work

### 1.1 Template Changes (Propagated)

| Change | Location | Status | | ---------------------------------------------------- | --------Repos that passed:
unified-trading-pm, matching-engine-library, unified-events-interface, unified-internal-contracts,
unified-reference-data-interface, unified-trading-library, execution-algo-library, unified-market-interface,
instruments-service, pnl-attribution-service, client-reporting-ui, deployment-ui, live-health-monitor-ui,
logs-dashboard-ui, ml-training-ui, onboarding-ui, strategy-ui, unified-trading-ui-auth-------------------------------- |
------ | | `.python-version` → `3.13` (was 3.13.9/3.13.1) | 6 repos | Done | | `.python-version` added to `.gitignore` |
All repos | Done | | `.python-version` removed from git tracking | All repos | Done | | setup.sh prefers
`.venv-workspace` when available | PM template → all repos | Done | | quality-gates bootstrap uses `.venv-workspace`
first | Codex templates → all repos | Done | | Docs: 3.13.9 → 3.13.x | execution-service, PM | Done | | Merge conflict
resolved | matching-engine-library/quality-gates.sh | Done |

### 1.2 Repos Successfully Quickmerged

- unified-trading-ui-auth (PR #4)
- deployment-ui (PR #4)
- (Others may have completed; check PR status per repo)

### 1.3 Skipped (Per User Request)

- **unified-trading-pm** — being pushed by other agents; do not quickmerge.

---

## 2. Remaining Work — Per Repo

### 2.1 Dependency Chain (Must Fix in Order)

| Order | Repo                                 | Blocker                                                                    | Fix                                                                                   |
| ----- | ------------------------------------ | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| 1     | **unified-api-contracts**            | bandit not installed                                                       | `uv sync --extra dev`; then quickmerge                                                |
| 2     | **unified-internal-contracts**       | Depends on UAC                                                             | After UAC merged, quickmerge                                                          |
| 3     | **unified-cloud-interface**          | 10 basedpyright errors (pandas, google.cloud.devtools, reportArgumentType) | Fix type errors or add QUALITY_GATE_BYPASS_AUDIT.md entries                           |
| 4     | **unified-events-interface**         | Codex: `setup_events()` without `sink=`                                    | Template already excludes `def setup_events`; verify rollout applied; may need bypass |
| 5     | **unified-config-interface**         | Depends on UCI, UEI                                                        | After UCI/UEI merged, quickmerge                                                      |
| 6     | **unified-reference-data-interface** | Depends on UCI, UIC                                                        | After UCI/UIC merged, quickmerge                                                      |

### 2.2 Quality Gate Failures (Fix Before Quickmerge)

| Repo                                                  | Failure                                                                      | Fix                                                        |
| ----------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------- |
| matching-engine-library                               | Merge conflict (fixed)                                                       | Re-run quickmerge                                          |
| ibkr-gateway-infra                                    | Ruff: `Failed to format ibkr_gateway_infra: No such file or directory`       | Check SOURCE_DIR; may need glob exclusion                  |
| system-integration-tests                              | Ruff: `Failed to format system_integration_tests: No such file or directory` | Check SOURCE_DIR; may need glob exclusion                  |
| batch-audit-ui                                        | TypeScript: Cannot find module `@unified-trading/ui-auth`                    | `npm install` in workspace or link unified-trading-ui-auth |
| settlement-ui                                         | Same as above                                                                | Same                                                       |
| client-reporting-ui, logs-dashboard-ui, onboarding-ui | Same (if affected)                                                           | Same                                                       |

### 2.3 Repos With Changes But Not Yet Quickmerged

All repos except unified-trading-pm have local changes (`.gitignore`, `.python-version` removal, setup.sh,
quality-gates.sh). After fixing blockers above, run quickmerge in topological order.

---

## 3. Quickmerge Command (Per Repo)

```bash
cd /path/to/repo
source /path/to/unified-trading-system-repos/.venv-workspace/bin/activate  # for Python repos
bash scripts/quickmerge.sh "chore: use Python 3.13.x, .venv-workspace, add .python-version to gitignore" \
  --quick --dep-branch "chore/python-313-workspace-venv" --skip-tests
```

For repos with dependency conflicts, use `--dep-branch` so quickmerge cascades. For leaf repos with no path deps, omit
`--dep-branch` if not needed.

---

## 4. Suggested Agent Execution Order

1. **Fix unified-api-contracts**: `uv sync --extra dev` → quickmerge
2. **Fix unified-cloud-interface**: Resolve 10 basedpyright errors (or document bypass)
3. **Fix unified-events-interface**: Verify setup_events check; add bypass if needed
4. **Fix matching-engine-library**: Re-run quickmerge (conflict already resolved)
5. **Fix ibkr-gateway-infra, system-integration-tests**: SOURCE_DIR / ruff path
6. **Fix UI repos** (@unified-trading/ui-auth): npm link or workspace install
7. **Cascade**: unified-internal-contracts → unified-config-interface → unified-reference-data-interface → rest

---

## 5. Key Paths

| Item                           | Path                                                                          |
| ------------------------------ | ----------------------------------------------------------------------------- |
| Workspace venv                 | `unified-trading-system-repos/.venv-workspace`                                |
| Setup SSOT                     | `unified-trading-pm/scripts/setup.sh`                                         |
| Quality gates library template | `unified-trading-codex/06-coding-standards/quality-gates-library-template.sh` |
| Quality gates service template | `unified-trading-codex/06-coding-standards/quality-gates-service-template.sh` |
| Rollout script                 | `unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py`     |
| Workspace manifest             | `unified-trading-pm/workspace-manifest.json`                                  |

---

## 6. Cursor Rules Reminders (For Agents)

- **uv not pip** — always `uv pip install` / `uv sync`
- **quickmerge not git push** — use `bash scripts/quickmerge.sh "message"`
- **--dep-branch** when dependencies have uncommitted changes
- **Never** `git reset --hard` — use `git stash` + `--dep-branch` for cascade
- **Runtime verification** — run code, wait 8–10s, check for errors before claiming done
