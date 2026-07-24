---
doc_type: plan
title: Broken Symlinks Remediation — All Workspace Repos
summary:
status: DONE
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui, execution-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-03-09
id: broken_symlinks_remediation_2026_03_09
priority: P2
completed: 2026-03-10
owner: agent
---

## Context

`run-version-alignment.sh` step [0.5/4] now scans for broken symlinks across all workspace repos. First run found **122
broken symlinks** in 3 categories. These were pre-existing; the scan made them visible. None are actively blocking CI
today (validator is WARN not FAIL by default), but they cause `pre-flight-audit.sh` to silently not run in ~55 repos and
`.cursor/rules` to not load in ~8 repos.

## Root Cause Analysis

### Category A — `scripts/pre-flight-audit.sh` wrong depth (55 repos)

Symlink: `<repo>/scripts/pre-flight-audit.sh → ../unified-trading-pm/scripts/validation/pre-flight-audit.sh` Problem:
`../unified-trading-pm/` resolves from `<repo>/scripts/` to `<repo>/unified-trading-pm/` (no such dir). Fix: change
target to `../../unified-trading-pm/scripts/validation/pre-flight-audit.sh`

Affected repos (55): alerting-service, batch-audit-ui (no scripts/ link but has .cursor/rules), client-reporting-api,
client-reporting-ui, deployment-api, deployment-service, deployment-ui, execution-algo-library, execution-analytics-ui,
execution-results-api, execution-service, features-calendar-service, features-cross-instrument-service,
features-delta-one-service, features-multi-timeframe-service, features-onchain-service, features-volatility-service,
instruments-service, live-health-monitor-ui, logs-dashboard-ui, market-data-api, market-data-processing-service,
market-tick-data-service, matching-engine-library, ml-inference-service, ml-training-service, ml-training-ui,
onboarding-ui, pnl-attribution-service, position-balance-monitor-service, risk-and-exposure-service, settlement-ui,
strategy-service, strategy-validation-service, system-integration-tests, trading-analytics-ui, unified-api-contracts,
unified-cloud-interface, unified-config-interface, unified-defi-execution-interface, unified-domain-client,
unified-events-interface, unified-feature-calculator-library, unified-internal-contracts, unified-market-interface,
unified-ml-interface, unified-position-interface, unified-reference-data-interface, unified-sports-execution-interface,
unified-trade-execution-interface, unified-trading-library, unified-trading-ui-auth

**Note:** Before re-targeting, verify `unified-trading-pm/scripts/validation/pre-flight-audit.sh` still exists. If it
has moved or been deleted, remove the symlink instead.

### Category B — `.cursor/rules` symlinks wrong depth (8 repos)

Symlink: `<repo>/.cursor/rules → ../unified-trading-pm/cursor-rules` Problem: same depth issue — resolves to
`<repo>/unified-trading-pm/cursor-rules` (no such dir). Fix: change target to `../../unified-trading-pm/cursor-rules`

Affected repos: batch-audit-ui, deployment-api, deployment-service, features-sports-service, system-integration-tests,
unified-api-contracts, unified-internal-contracts, unified-trading-ui-auth

### Category C — PM `.cursor/rules/*.mdc` internal symlinks (62 files)

Symlink: `unified-trading-pm/.cursor/rules/<name>.mdc → ../../cursor-rules/<name>.mdc` Problem: `.mdc` files are inside
subdirectories of `cursor-rules/` (architecture/, ci-cd/, config/, core/, etc.), not at the root.
`cursor-rules/<name>.mdc` doesn't exist at top level. Fix: map each `.mdc` filename to its actual location in
`cursor-rules/` subdirs and update target. Alternative: if `.cursor/rules/` should be a flat view, create a script that
auto-generates these symlinks by scanning all `cursor-rules/**/*.mdc` files.

**Recommended fix:** make `.cursor/rules` itself a symlink to `cursor-rules/` (already done for workspace root
`.cursor/rules`). The per-file symlinks inside `.cursor/rules/` are then redundant.

### Category D — Codex stale deployment-v3 symlinks (2 files)

- `unified-trading-/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md` → FIXED (now → deployment-service) ✅
- `unified-trading-codex/04-architecture/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg` →
  `../../unified-trading-deployment-v3/configs/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg` Action: check if file exists in
  `deployment-service/configs/`; if yes re-target, if no remove symlink.

## Tasks

- [x] **A: Fix pre-flight-audit.sh depth** — Verified 2026-03-10: all 57 `scripts/pre-flight-audit.sh` symlinks already
      point to `../../unified-trading-pm/scripts/validation/pre-flight-audit.sh` (correct depth). No fixes required; all
      symlinks resolve successfully.

- [x] **B: Fix .cursor/rules depth** — Verified 2026-03-10: all `.cursor/rules` symlinks in all repos (60+) already
      point to `../../unified-trading-pm/cursor-rules` (correct depth). No fixes required; all symlinks resolve
      successfully.

- [x] **C: Fix PM .cursor/rules/\*.mdc symlinks** — Verified 2026-03-10: `unified-trading-pm/.cursor/rules` is already a
      directory symlink to `../cursor-rules` (same pattern as workspace root). No per-file `.mdc` symlinks exist inside
      it. Fix was applied in a prior session.

- [x] **D: Fix codex RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg** — Verified 2026-03-10: SVG symlink already re-targeted to
      `../../deployment-service/configs/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg` and resolves successfully.

- [x] **Verify** — Comprehensive scan on 2026-03-10: **131 total symlinks, 0 broken** across all workspace repos
      (maxdepth 5, excluding .venv/node_modules/.egg-info). All categories A, B, C, D are clean.

## Outcome

**All 122 originally-reported broken symlinks are resolved.** Verification on 2026-03-10 shows 131 symlinks
workspace-wide with 0 broken. The fixes were applied in prior sessions before this audit ran; this session confirmed the
clean state and closed the plan.

## Implementation Note

All fixes should be done via a single agent session that:

1. Runs the bulk fix script for categories A and B
2. Handles category C (PM internal)
3. Handles category D (codex)
4. Commits each repo with `chore(symlinks): fix pre-flight-audit.sh depth ../ → ../../`
5. Runs version-alignment --strict to verify
