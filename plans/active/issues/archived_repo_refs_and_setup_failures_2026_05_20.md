---
title: Active consumers still reference archived/renamed repos as editable deps (+ 3 setup-recreate failures)
created: 2026-05-20
author: harsh-main (agt-5fc757)
source:
  - strategy_repo_consolidation_2026_05_19.md
  - workspace_migration_to_active_2026_05_20.md
locked_by: live-defi-rollout
---

## What I found

While recreating venvs for the `/active` workspace migration, several **active** repos failed
`setup.sh`/`uv pip install` because their `pyproject.toml` still declares **editable path-dependencies on repos that
were archived/merged in `strategy_repo_consolidation_2026_05_19`** (risk-and-exposure-service,
position-balance-monitor-service, pnl-attribution-service → all merged into `strategy-service`):

**`deployment-api/pyproject.toml`**

```
42:    "position-balance-monitor-service>=0.1.0,<1.0.0",
64:    position-balance-monitor-service = { path = "../position-balance-monitor-service", editable = true }
```

**`system-integration-tests/pyproject.toml`**

```
11:    "risk-and-exposure-service>=0.1.0,<1.0.0",
19:    "position-balance-monitor-service>=0.1.0,<1.0.0",
21:    "pnl-attribution-service>=0.1.0,<1.0.0",
44:  [tool.uv.sources.risk-and-exposure-service]  path = "../risk-and-exposure-service"
76:  [tool.uv.sources.position-balance-monitor-service]  path = "../position-balance-monitor-service"
84:  [tool.uv.sources.pnl-attribution-service]  path = "../pnl-attribution-service"
```

On `/home/hk` these still resolve only because the archived repos are physically still at workspace root. They break the
moment those repos are removed/relocated (they did, on `/active`, where the archived repos were moved to `.extra`). I
unblocked the `/active` setup with **root symlinks** (`../<archived-repo>` → `.extra/<archived-repo>`) — but that is a
**band-aid; the real fix is repointing the consumers to `strategy-service`**, and this issue exists on LDR regardless of
the migration.

## Why it matters

- **The consolidation is not actually complete.** The 3 archived repos **cannot be retired/deleted** while
  `deployment-api` + `system-integration-tests` still pin them as editable path-deps — any fresh `setup.sh` / clean
  checkout of those two repos will fail once the archived repos are gone.
- **Drift (review-blocking per Citadel standards):** code was merged into `strategy-service` but the consumers'
  dependency manifests + (likely) imports still point at the dead repos — doc/plan/code drift.
- Surfaced during migration but it is a **live LDR correctness bug**, not a migration artifact.

## Recommended decision

1. In `deployment-api` and `system-integration-tests` `pyproject.toml`: **remove** the `risk-and-exposure-service` /
   `position-balance-monitor-service` / `pnl-attribution-service` dependency lines + their `[tool.uv.sources]` entries,
   and depend on **`strategy-service`** (editable) instead — the merged code now lives under
   `strategy_service.{risk,pnl,position}`.
2. Audit + fix the **imports** in those two consumers to use `strategy_service.*` (the consolidation's import-rewrite
   should have covered this — verify).
3. Re-run `setup.sh` for both; confirm green.
4. Then the 3 archived repos can be truly retired, and the `/active` root symlinks I added become unnecessary (remove
   them).
5. **Owner:** `strategy_repo_consolidation_2026_05_19` Phase 7/8 follow-up.

## Additional setup-recreate failures found in the same audit (lower priority)

These are pre-existing-class issues (not migration-caused), bundled here per operator request:

- **`e2e-testing`** — `setup.sh` fails at "[7] Local path dependencies":
  `uv lock failed — optional dep conflict likely (incompatible extras)` on the `execution-service` editable install. A
  dependency/extras conflict to resolve in `e2e-testing` (or `execution-service`) `pyproject.toml` / `uv.lock`.
- **`new-sports-batting-services`** — `pyproject.toml:41` pins
  `unified-cloud-services = { path = "../unified-cloud-services", develop = true }`, but that repo was **renamed to
  `unified-cloud-interface`** → stale dep name. Also lacks `scripts/setup.sh` (uses the uv fallback path). Fix: repoint
  to `unified-cloud-interface` (confirm the rename) + add/standardize `setup.sh`.
- **`unified-trading-system-ui`** — `npm install` fails on a **node-pre-gyp native build** (`node-pre-gyp ERR! not ok`);
  repo also **ships no `package-lock.json`** (so `npm ci` can't be used). `engines.node = ">=22"`. Likely a node-version
  / native-module toolchain mismatch on the host. Fix: pin/verify node 22 toolchain, commit a `package-lock.json`,
  identify the failing native dep.
