---
title: "deployment-api missing position_balance_monitor_service dependency"
created: 2026-05-14
author: slot-2-api-football
source:
  - deployment-api/treasury_routes.py:26
  - deployment-api/pyproject.toml
  - unified-trading-pm/workspace-manifest.json
severity: P1
status: RESOLVED
resolved_at: 2026-05-14
resolved_by: slot-2-wave2
resolution_commits:
  - deployment-api@edce262
  - unified-trading-pm@1d472ee9
suggested_owner: deployment-api maintainer / operator triage
---

## ✅ RESOLVED 2026-05-14 (slot-2-wave2)

Shipped both halves of the fix:

1. **deployment-api@edce262** — added `position-balance-monitor-service>=0.1.0,<1.0.0` to `[project.dependencies]` +
   matching `[tool.uv.sources]` editable path. `uv.lock` regenerated via `uv sync`.
2. **unified-trading-pm@1d472ee9** — added `position-balance-monitor-service` (>=0.1.0,<1.0.0, required=true) to
   `workspace-manifest.json` deployment-api dependencies array. `canonical-dependency-manifest.json` +
   `derived-dependency-manifest.json` regenerated.

**Verification**:

- `.venv/bin/python -c "from deployment_api.routes import treasury_routes"` → ✅ succeeds.
- `bash run-version-alignment.sh --json` → no new misalignments introduced (pre-existing e2e-testing + UTL freezegun +
  features-service self-version drift are unrelated).

deployment-api topo position (level 6) → position-balance-monitor-service (level 5) ordering already correct in
`topologicalOrder` — no level change needed.

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
`position-balance-monitor-service` (and possibly other services it imports). A broader audit of deployment-api's actual
imports vs declared deps is warranted.
