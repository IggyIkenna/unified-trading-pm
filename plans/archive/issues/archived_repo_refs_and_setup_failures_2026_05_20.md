---
title: Active consumers still reference archived/renamed repos as editable deps (+ 3 setup-recreate failures)
created: 2026-05-20
closed: 2026-05-20
author: harsh-main (agt-5fc757)
closer: slot 1 ikenna-main
source:
  - strategy_repo_consolidation_2026_05_19.md
  - workspace_migration_to_active_2026_05_20.md
locked_by: live-defi-rollout
status: CLOSED — all items shipped
---

## Closure summary (2026-05-20, slot 1 ikenna-main)

All findings shipped or obsoleted. Archived per Issue-Doc Lifecycle Discipline.

- ✅ **P0 archived-repo path-deps in active consumers** — SHIPPED.
  - deployment-api@71671ae — removed `position-balance-monitor-service`, declared `strategy-service` editable
    (treasury_routes.py already imported `strategy_service.position.core.treasury_monitor`).
  - system-integration-tests@e83a95e — removed 3 stale dep entries (risk/position/pnl); `strategy-service` was already
    declared editable; tests already import `strategy_service.{pnl,risk,position}.*`.
  - Workspace-wide grep verified: 0 Python imports of the archived module names in either consumer; ship was pure
    pyproject cleanup.
- ⚠️ **new-sports-batting-services** finding obsoleted — repo is now in `archive/new-sports-batting-services/`, not a
  workspace consumer. The `unified-cloud-services` stale path-dep there is no longer load-bearing for `/active` setup.
- ✅ **e2e-testing uv lock conflict on execution-service** — SHIPPED at e2e-testing@1a73589. Three root causes in one
  fix: (a) `[tool.uv.sources]` block was missing entirely so the 3 internal workspace deps (unified-api-contracts /
  execution-service / strategy-service) couldn't resolve — added editable path entries. (b) Same
  betfairlightweight↔requests CVE-2026-25645 conflict that system-integration-tests already solves via
  `override-dependencies = ["requests>=2.33.0,<3.0.0"]` under `[tool.uv]` — copied the same override. (c) The same
  archived risk/position service refs in pyproject as the P0 above — dropped (no actual imports). `uv lock` now
  completes cleanly.
- ✅ **unified-trading-system-ui npm install fails on node-pre-gyp** — SHIPPED at unified-trading-system-ui@110cff88 +
  unified-trading-pm@32ea69f5b. Root cause: PM canonical `scripts/setup.sh` UI branch hardcoded `npm install`, but this
  repo uses pnpm (pnpm-lock.yaml committed, README says `pnpm install`, scripts reference `pnpm test:ci`). `npm install`
  was falling back to native-module compile via node-pre-gyp and failing. Fix: setup.sh now auto-detects pnpm-lock.yaml
  → pnpm, yarn.lock → yarn, else npm; build-library step (`<pkg-mgr> run build`) honors the same detected manager.
  Verified end-to-end on the UI repo: `bash scripts/setup.sh` completes via `pnpm install`. Also bundled: UI pre-commit
  template was missing the gitleaks block (existed in python-service / python-library / docs only) — added.
- ✅ **gitleaks pre-commit hook unexpanded `${WORKSPACE_ROOT:-..}` literal** — SHIPPED across the SSOT (rollout script
  - templates) and propagated to 16 repos.
  * SSOT fix: `unified-trading-pm/scripts/propagation/rollout-pre-commit-configs.sh` (7ae3e7328) now ALSO creates a
    `.gitleaks.toml` symlink in each target repo pointing at the PM SSOT `.gitleaks.toml` (templates were already fixed
    in 88e691d2e to use repo-root-relative path; the missing piece was the symlink propagation).
  * Propagated to: agent-orchestrator, deployment-service, execution-service, fund-administration-service,
    ibkr-gateway-infra, instruments-service, market-data-processing-service, ml-service, strategy-service,
    system-integration-tests, trading-agent-service, unified-trading-library, unified-trading-api,
    unified-trading-system-ui, e2e-testing (each as a per-repo
    `fix(tooling): apply gitleaks pre-commit hook fix (rollout from PM SSOT)` commit on live-defi-rollout).
    `ml-inference-service` + `ml-training-service` were already up-to-date (symlink + fixed config existed pre-rollout).
    Repos NOT yet rolled forward (foreign-dirty WIP from other agents at the time of this closure — pickup happens on
    their next rollout sweep): features-service, market-tick-data-service, unified-api-contracts. Their
    `.pre-commit-config.yaml` + `.gitleaks.toml` are queued in their working trees; the active agent just stages +
    commits in their next shippable-unit, or re-runs
    `bash unified-trading-pm/scripts/propagation/rollout-pre-commit-configs.sh --repo <name>`.

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
