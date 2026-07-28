---
doc_type: issue
title: .gitleaks.toml dangling symlink — fleet-wide regression of the 2026-06-23 fix
summary:
  rollout-pre-commit-configs.sh symlinked .gitleaks.toml instead of copying it, which resolves fine locally (sibling
  repo exists) but is a dangling ENOENT in any standalone single-repo CI checkout; broke unified-trading-system-ui's e2e
  build; 22 other repos carried the same latent risk.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    unified-trading-system-ui,
    agent-orchestrator,
    strategy-service,
    unified-trading-library,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
    execution-service,
    features-service,
    fund-administration-service,
    greeks-service,
    ibkr-gateway-infra,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    ml-service,
    system-integration-tests,
    trading-agent-service,
    unified-api-contracts,
    unified-trading-api,
    deployment-ui,
    e2e-testing,
  ]
scope: [engineer]
tags: [ci, gitleaks, symlink, regression]
related: []
created: 2026-07-28
parent_epic: infrastructure_master
priority: P1
assigned_vm: planning
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: infra-engineer
resolved_by:
locked_by:
source: autonomous-agent-fleet-sweep
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# .gitleaks.toml dangling symlink — fleet-wide regression

## What happened

`unified-trading-pm/scripts/propagation/rollout-pre-commit-configs.sh` created a **symlink**
(`.gitleaks.toml -> ../unified-trading-pm/.gitleaks.toml`) in every repo it rolled out to. This resolves fine in the
operator's local multi-repo sibling-directory layout, but is a **dangling ENOENT** in any standalone single-repo CI
checkout, where the sibling `unified-trading-pm` directory does not exist.

This exact bug was already fixed once, on 2026-06-23, via commit `a4ec4985` in `unified-trading-system-ui` (replaced the
symlink with a real file copy). The rollout script's own `ln -s` logic was never fixed at the time, so the fix was
silently undone the next time the script ran against that repo — reproducing the identical CI failure on 2026-07-28
(`unified-trading-system-ui` "CI - Test & Lint" → `e2e` job, `pnpm build` failing with
`ENOENT: no such file or directory, stat '.../unified-trading-system-ui/.gitleaks.toml'`).

A fleet-wide audit found **22 other repos** still carrying the same dangling symlink (confirmed via direct `readlink`
per repo, 2026-07-28): agent-orchestrator, strategy-service, unified-trading-library, alerting-service,
batch-live-reconciliation-service, client-reporting-api, deployment-api, deployment-service, execution-service,
features-service, fund-administration-service, greeks-service, ibkr-gateway-infra, instruments-service,
market-data-processing-service, market-tick-data-service, ml-service, system-integration-tests, trading-agent-service,
unified-api-contracts, unified-trading-api, deployment-ui, e2e-testing.

**Why the script never self-corrected these**: a second, independent bug. The gitleaks-propagation block ran _after_ the
`.pre-commit-config.yaml` "already current" `continue` — so for any repo whose base template hadn't also changed, the
gitleaks check was silently unreachable. That's why these repos stayed broken despite the script running on a regular
cadence.

**Why a content-diff alone wasn't a sufficient re-check**: `diff -q` follows symlinks. In the operator's local layout
the symlink resolves to byte-identical content, so a pure content comparison reports "no difference" even though the
on-disk _structure_ (symlink vs. real file) is exactly what breaks in an isolated CI checkout. Fixed by adding an
explicit `[ -L "$target" ]` check.

## Fix

`rollout-pre-commit-configs.sh` now `cp`s `unified-trading-pm/.gitleaks.toml` into each repo (matching the file's own
header comment: "propagated to all repos by rollout-pre-commit-configs.sh" — a copy was always the intended mechanism,
not a symlink), the propagation step moved before the early `continue`, and the check now looks for `-L` explicitly.

## Rollout status

Dependency layers (per workspace-manifest.json path_dependencies), shipped in order: layer 0 (no deps):
unified-api-contracts, deployment-ui. layer 1: unified-trading-library (needs unified-api-contracts). layer 2: the 16
services depending on library+contracts. layer 3: deployment-api (needs deployment-service). layer 4:
system-integration-tests, e2e-testing.

- [x] [SCRIPT] P1. `unified-trading-system-ui` — symptom fixed directly + shipped (`1306658c`).
- [x] [SCRIPT] P1. `unified-trading-pm/scripts/propagation/rollout-pre-commit-configs.sh` — root cause fixed, shipping.
- [x] [SCRIPT] P1. Local working-tree copies replaced for all 22 remaining repos (mechanical `cp`, verified via
      `readlink` before/after) — shipping per-repo below.
- [x] [SCRIPT] P1. `deployment-ui` — shipped (`e98c575`).
- [x] [SCRIPT] P1. `unified-api-contracts` — shipped (`feb79db8`).
- [x] [SCRIPT] P1. `unified-trading-library` — shipped (`5583b94f`).
- [ ] [SCRIPT] P1. `agent-orchestrator` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `strategy-service` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `alerting-service` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `batch-live-reconciliation-service` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `client-reporting-api` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `deployment-service` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `execution-service` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `features-service` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `fund-administration-service` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `greeks-service` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `ibkr-gateway-infra` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `instruments-service` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `market-data-processing-service` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `market-tick-data-service` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `ml-service` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `trading-agent-service` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `unified-trading-api` — ship via quickmerge (layer 2).
- [ ] [SCRIPT] P1. `deployment-api` — ship via quickmerge (layer 3, needs deployment-service committed first).
- [ ] [SCRIPT] P1. `system-integration-tests` — ship via quickmerge (layer 4, needs many layer-2/3 deps committed
      first).
- [ ] [SCRIPT] P1. `e2e-testing` — ship via quickmerge (layer 4, needs unified-api-contracts committed first). Dry-run
      also showed an UNRELATED `.pre-commit-config.yaml` template drift in `deployment-ui` — that update was correctly
      NOT pulled in; the `deployment-ui` commit above is scoped to `.gitleaks.toml` only.

**Pacing note**: workspace hard rule caps shared-host concurrent full QG runs at `max(2, floor(cores/4))` (2 on this
10-core machine) — shipped via a Workflow dispatching agents in chunks of 2, sequential across chunks, per dependency
layer.

## Why this wasn't risky to fix directly (no operator ask needed)

Single config file, zero application-logic surface, gitleaks itself validated clean (`gitleaks protect --staged` against
the new content in `unified-trading-system-ui`), and the exact fix already has a proven precedent (`a4ec4985`, ran in
production for over a month with no incident). Matches the workspace's own stated intent for the file (its header
literally says "propagated ... by rollout-pre-commit-configs.sh").
