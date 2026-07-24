---
doc_type: codex-runbook
title: Position Reconciliation Deploy Gate
summary:
  Operator contract for scripts/deploy/position-reconciliation-check.sh — the pre/post-deploy gate wired into
  cloud-build-router.yml that snapshots /positions before a deploy and compares after, failing the rollout on lost
  positions, disappeared position-ids, or quantity drift beyond tolerance. Currently non-blocking when /positions is
  absent; flips to a hard gate once the endpoint ships.
status: current
nature: process
asset_group: [meta]
stage: [meta]
repos: [batch-live-reconciliation-service, execution-service, unified-trading-pm]
scope: [engineer, admin]
tags: [runbook, reconciliation, deploy-gate, execution, position, quality-gates]
related:
  [
    /codex/04-architecture/reconciliation-resolution.md,
    /codex/04-architecture/separation-of-concerns.md,
    ../../plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
  ]
created: 2026-05-12
owner:
  deployment-service maintainer (cloud-build-router invocation) + execution-service / position-balance-monitor-service
  maintainers (/positions endpoint contract)
cadence: per-deploy (every pre-deploy + post-deploy invocation of `cloud-build-router.yml` on trading-critical services)
verifier:
  pre-deploy `snapshot` produces JSON file in $RUNNER_TEMP; post-deploy `compare` diffs against snapshot; exit 0 on
  match; exit nonzero on quantity-delta-out-of-tolerance / position-id-disappeared.
last_executed:
code_refs:
author: slot 8 sub-agent (Position-balance audit PB-9 PRE_CUTOVER)
execution:
  {
    owner:
      deployment-service maintainer (cloud-build-router invocation) + execution-service /
      position-balance-monitor-service maintainers (/positions endpoint contract),
    cadence:
      per-deploy (every pre-deploy + post-deploy invocation of `cloud-build-router.yml` on trading-critical services),
    verifier:
      pre-deploy `snapshot` produces JSON file in $RUNNER_TEMP; post-deploy `compare` diffs against snapshot; exit 0 on
      match; exit nonzero on quantity-delta-out-of-tolerance / position-id-disappeared.,
    last_executed:
      NEVER (script exists at `unified-trading-pm/scripts/deploy/position-reconciliation-check.sh`; gate is currently
      non-blocking when /positions endpoint absent — flips to hard gate once endpoint ships),
  }
---

# Position Reconciliation Deploy Gate

## TL;DR

`unified-trading-pm/scripts/deploy/position-reconciliation-check.sh` is the pre/post-deploy gate that compares
open-positions on a trading-critical service before + after a deploy and fails the deploy if positions disappeared or
quantities changed beyond tolerance. Wired into `.github/workflows/cloud-build-router.yml` per
`codex/00-SSOT-INDEX.md:310`. This doc is the operator-facing contract: what it asserts, the tolerance, what an operator
does on a break.

## Protocol

Two invocations bracketing the deploy:

1. **PRE-DEPLOY** — `bash scripts/deploy/position-reconciliation-check.sh snapshot <SERVICE_URL> <SNAPSHOT_FILE>`. GETs
   `<SERVICE_URL>/positions` + writes JSON to `<SNAPSHOT_FILE>`. Runs **before** the new revision is deployed.
2. **POST-DEPLOY** — `bash scripts/deploy/position-reconciliation-check.sh compare <SERVICE_URL> <SNAPSHOT_FILE>`. GETs
   `<SERVICE_URL>/positions` again + diffs against the pre-deploy snapshot. Runs **after** the new revision is serving
   traffic.

## What it asserts

- **No positions were lost** — `len(post_positions) >= len(pre_positions)`.
- **No position IDs disappeared** — `set(pre_position_ids) ⊆ set(post_position_ids)`.
- **No quantity drift beyond tolerance** — for each shared position_id,
  `abs(post.qty - pre.qty) / pre.qty <= tolerance`.

Tolerance is hardcoded in the script (read it before tuning); the master plan's continuous-verification column treats
deploy-time deviation as a continuous signal — break = block deploy.

## Soft-fail behaviour

- **Endpoint absent (404)**: WARNING + exit 0 (non-blocking, legacy). Per script docstring: **once the endpoint ships,
  the gate becomes blocking**.
- **5xx / network error**: WARNING + exit 0 (non-blocking, treats as transient).
- **Deviation detected**: exit nonzero → cloud-build-router marks deploy as failed → operator-runbook flow below.

## Operator action on a break

1. **Stop the deploy** — gate exits nonzero; cloud-build-router halts the rollout.
2. **Inspect the diff** — pre + post snapshot JSON files uploaded as workflow artefacts.
3. **Classify the break**:
   - **Position disappeared** → severe; new revision lost state. Roll back immediately.
   - **Quantity drift > tolerance** → investigate. Most common cause: fill arrived during deploy window + got attributed
     to the wrong revision. Reconcile against execution-service fills stream for the deploy interval.
   - **Quantity drift < tolerance but non-zero** → expected (active trading during deploy); no action.
4. **Resolve** via `batch-live-reconciliation-service` resolution API (`POST /api/resolve`) if real reconciliation
   issue, or via roll-back if lost state.

## Cross-references

- Script source: `unified-trading-pm/scripts/deploy/position-reconciliation-check.sh`
- CI wiring: `.github/workflows/cloud-build-router.yml`
- SSOT pointer: `codex/00-SSOT-INDEX.md:310`
- Resolution API: `/codex/04-architecture/reconciliation-resolution.md`
- Master plan F-21: `master_to_live_defi_2026_05_23.md` Group F (Reconciliation suite)
- Position SSOT (PBMS): `/codex/04-architecture/separation-of-concerns.md` (PB-7 follow-up — position-balance-monitor as
  positions SSOT codex doc pending)
