---
doc_type: codex-ssot
title: Strategy promote workflow (backtest → paper → live)
summary:
  SSOT-stub for the operator-facing strategy-service --operation promote CLI that flips a strategy archetype across
  backtest→paper→live-testnet→live-mainnet with per-transition audit rows; the full 14-step orchestration lives in the
  two promote plan-of-records (May-23 CLI + post-cutover UI).
implementation_status: active
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, promote, execution, live-trading, runbook]
related:
  [
    /codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md,
    cross-cutting/archetype-paper-readiness.md,
    /codex/09-strategy/architecture-v2/MIGRATION.md,
  ]
created: 2026-05-12
authoritative_for: [strategy-service --operation promote CLI surface]
referenced_by:
owner:
last_reviewed:
code_refs:
doc_kind: workflow_stub
ssot_for: strategy_promote_workflow_cli
created_per: plans/archive/issues/codex_audit_strategy_2026_05_12.md ST-17
---

# Strategy promote workflow (backtest → paper → live)

> SSOT-stub for the operator-facing `--operation promote` CLI surface that flips a strategy archetype across the four
> lifecycle states (backtest → paper → live, per `strategy-lifecycle-maturity.md`). The full state-machine + 14-step
> orchestration lives in two plan-of-records (May-23 + post-cutover); this stub is the codex entry-point per CLAUDE.md
> "Post-Plan-Phase Codex Audit" rule (codex is the intent; plans are orchestration).

## Entry point

```bash
strategy-service --operation promote \
  --strategy-id <slot-label> \
  --from <backtest|paper|live-testnet> \
  --to <paper|live-testnet|live-mainnet> \
  --asset-group <cefi|defi|tradfi|sports|prediction> \
  --reason "<operator justification, audit-trail captured>"
```

Code path: `strategy-service/strategy_service/cli/handlers/group_b_handler.py:55` — `promote: bool` flag dispatches
through `engine/backtest/promote_workflow.py` (Group B promotion pipeline).

## State machine

```
backtest (shadow-only, simulated fills)
   │  14-day shadow gate per ShadowDeploymentPolicy
   ▼
paper (live signals, simulated fills via execution-service "always fill" mode)
   │  28-day shadow gate per ShadowDeploymentPolicy (or 14-day if testnet)
   ▼
live-testnet (live signals, real testnet fills, custody = cloud_kms_encrypted)
   │  manual operator promotion (no autonomous flip)
   ▼
live-mainnet (live signals, real mainnet fills, custody per pre-cutover wallet config)
```

Each transition writes an audit row to `strategy_promote_audit.parquet` with
`(from_state, to_state, operator_id, reason, commit_sha_at_promote)`. Rollback (live → paper) is a separate
`--operation demote` flag — owner-gated.

## Plan-of-records (orchestration, not SSOT)

The 14-step CLI sequence + per-step verifier + per-step rollback procedure is in:

- **May-23 cutover scope**:
  [`plans/active/promote_workflow_may23_cli_path_2026_05_10.md`](../../../plans/active/promote_workflow_may23_cli_path_2026_05_10.md)
- **Post-cutover UI pipeline**:
  [`plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`](../../../plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md)

When the post-cutover UI pipeline lands, this doc updates to include the UI entry-point + cross-references to the
UI-side workflow.

## Cross-references

- [`strategy-lifecycle-maturity.md`](./strategy-lifecycle-maturity.md) — SSOT for the four-state taxonomy + the
  `ShadowDeploymentPolicy` shadow-gate config.
- [`archetype-paper-readiness.md`](./cross-cutting/archetype-paper-readiness.md) — per-archetype paper-mode readiness
  gate driving the backtest → paper transition.
- [`MIGRATION.md`](./MIGRATION.md) — v2 archetype engine catalogue ("the 18 archetype engines need to clear their 14- or
  28-day shadow" framing; counts now 55 per slot 8 audit ST-1).
- CLAUDE.md § "Master Plan" — the live-DeFi-by-2026-05-23 cutover that gates the first
  `--operation promote --to live-mainnet` calls.

## Execution-owner block

```yaml
execution:
  owner: strategy-architecture owner (Ikenna for design + cutover-promotion decisions; Harsh runs CLI verifications)
  cadence: per-archetype as paper-readiness lands (~10 archetypes for May-23 cutover lead pair)
  verifier: |
    Each promotion writes `strategy_promote_audit.parquet` row + emits `STRATEGY_PROMOTED` event in
    `gs://{pid}-events/events/strategy-service/...`. Reviewers verify audit row + event before accepting that the
    promotion landed; a code-shipped promote that has no audit row is NOT operationally-shipped.
  last_executed: NEVER (first promotions gated on archetype-paper-readiness 4-state taxonomy landing per ST-4)
```
