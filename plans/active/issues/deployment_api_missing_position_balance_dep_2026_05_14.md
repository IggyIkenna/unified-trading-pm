---
title: "deployment-api missing position_balance_monitor_service dependency"
created: 2026-05-14
author: slot-2-api-football
source:
  - deployment-api/treasury_routes.py:26
  - deployment-api/pyproject.toml
  - unified-trading-pm/workspace-manifest.json
severity: P1
suggested_owner: deployment-api maintainer / operator triage
---

## What I found

`deployment-api` fails to start with `ModuleNotFoundError: No module named 'position_balance_monitor_service'`.

Root cause: `deployment-api/treasury_routes.py:26` imports:
```python
from position_balance_monitor_service.core.treasury_monitor import TreasuryMonitor
```
But `position_balance_monitor_service` is **not declared** in:
- `deployment-api/pyproject.toml` `[project.dependencies]` (file has only empty `[]` deps)
- `unified-trading-pm/workspace-manifest.json` `deployment-api` entry `"dependencies": []`

**Workaround applied in this session** (2026-05-14):
```bash
deployment-api/.venv/bin/pip install -e /home/hk/unified-trading-system-repos/position-balance-monitor-service
```
This is a dev-venv-only fix — the Docker image and CI environments are unaffected and will still fail.

## Why it matters

- `deployment-api` cannot start without the workaround, blocking deployment-ui data-status functionality
- Any CI build or fresh clone will fail to start deployment-api on import of `treasury_routes.py`
- The missing dep is invisible to basedpyright (it finds the module via the installed venv, not pyproject.toml)
- `workspace-manifest.json` mismatch means dependency alignment checks will NOT catch this

## Recommended decision

**Fix** (both changes required together):
1. Add to `deployment-api/pyproject.toml` dependencies:
   ```toml
   "position-balance-monitor-service>=<current_version>",
   ```
2. Add to `workspace-manifest.json` under `deployment-api.dependencies`:
   ```json
   "position-balance-monitor-service"
   ```
3. Run `bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix` to verify
4. Re-run `bash deployment-api/scripts/setup.sh` to reinstall venv cleanly
5. Quickmerge both repos

**Note**: `deployment-api` has `"dependencies": []` in workspace-manifest.json. It should depend on
`position-balance-monitor-service` (and possibly other services it imports). A broader audit of
deployment-api's actual imports vs declared deps is warranted.
