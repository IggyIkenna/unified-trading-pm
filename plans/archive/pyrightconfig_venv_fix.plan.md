---
doc_type: plan
title: pyrightconfig.json — Workspace Venv Fix (All Repos)
summary: 'All per-repo pyrightconfig.json files were missing `venvPath`/`venv`, causing

  cursorpyright/basedpyright in Cursor to fall back to system Python instead of

  .venv-workspace. This broke import resolution for all internal packages (red/yellow

  squiggles on `from unified_internal_contracts import ...` etc.).

  Fixed by adding venvPath + venv to all 39 configs that lacked them and cleaning up

  the workspace-root pyrightconfig.json which had a stale `include: [features_sports_service]`.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, instruments-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-06'
todos:
- {id: fix-sub-repos, content: 'Add venvPath: ''../'' and venv: ''.venv-workspace'' to all 39 sub-repo pyrightconfig.json files that were missing them. Computed relative depth for archive/* repos (venvPath: ''../../''). Preserved all existing settings.', status: done}
- {id: fix-workspace-root, content: 'Fix workspace-root pyrightconfig.json: remove stale include: [features_sports_service] and extraPaths: [''.''], set venvPath: ''.'' and venv: ''.venv-workspace''. Keep pythonVersion, reportAny, reportMissingTypeStubs.', status: done}
- {id: verify-cursor, content: 'In Cursor: Cmd+Shift+P → ''Pylance: Restart Language Server''. Confirm squiggles on unified_internal_contracts and sibling imports are gone for all repos.', status: todo}
isProject: false
---

# pyrightconfig.json — Workspace Venv Fix (All Repos)

**Date:** 2026-03-05 **Scope:** 49 pyrightconfig.json files across all Python repos in the workspace **Trigger:**
Red/yellow squiggles on `from unified_internal_contracts import ...` (and all other internal packages) in Cursor —
basedpyright was not finding the workspace venv.

## Root Cause

Per-repo `pyrightconfig.json` files existed but did not specify `venvPath`/`venv`. Cursorpyright picks up the nearest
`pyrightconfig.json` when analyzing a file and uses it as the authoritative config. Without `venvPath`/`venv`, the
language server has no way to locate `.venv-workspace` independently of VS Code's interpreter selection — and in
multi-root workspaces `${workspaceFolder}` substitution in workspace settings is unreliable. Result: system Python used,
none of the internal packages found.

Additionally, the workspace-root `pyrightconfig.json` had `"include": ["features_sports_service"]` — a stale copy-paste
from features-sports-service — which would cause basedpyright to analyze the wrong scope when invoked from the workspace
root.

## Fix Applied

```python
# For sub-repos (depth 1): venvPath "../", venv ".venv-workspace"
# For archive/* repos (depth 2): venvPath "../../", venv ".venv-workspace"
# For workspace root: venvPath ".", venv ".venv-workspace"
```

39 files fixed, 10 already had correct venv config:

- **Already OK:** alerting-service, features-cross-instrument-service, features-volatility-service, instruments-service,
  unified-defi-execution-interface, unified-domain-client, unified-feature-calculator-library, unified-ml-interface,
  unified-sports-execution-interface, unified-trading-library

## Post-Fix Action Required

After pulling this change, restart the Cursor language server: `Cmd+Shift+P` → **Pylance: Restart Language Server**

## Codex Rule

Per-repo `pyrightconfig.json` MUST include:

```json
{
  "venvPath": "../",
  "venv": ".venv-workspace"
}
```

(Use `"venvPath": "."` for workspace-root config, `"../../"` for archive/\* repos.) This is enforced by the workspace
setup script — see `unified-trading-pm/scripts/workspace/`.
