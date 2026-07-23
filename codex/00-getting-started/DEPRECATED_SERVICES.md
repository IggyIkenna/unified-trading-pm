---
doc_type: codex-ssot
title: Deprecated Services (2026)
summary:
  Registry of removed/consolidated post-trade services — reconciliation-service folded into position-balance-monitor,
  risk+exposure merged into risk-and-exposure-service, plus the pre-May-23 5→2 strategy/ML repo consolidation
  (soft-freeze + BLOCKED-CUTOVER auto-flip).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, ml-service, strategy-service]
scope: [engineer]
tags: [deprecation, consolidation, refactor, migration, strategy, ml]
related:
  [
    /codex/04-architecture/strategy-service-architecture.md,
    /codex/04-architecture/ml-service-architecture.md,
    ../11-project-management/service-registry.yaml,
    ../../plans/archive/2026_05/strategy_repo_consolidation_2026_05_19.md,
  ]
created: "2026-03-27"
authoritative_for: [deprecated/consolidated post-trade service migration status]
referenced_by:
owner:
last_reviewed:
code_refs:
---

# Deprecated Services (2026)

The following services have been removed or consolidated as part of the post-trade infrastructure refactor.

## Removed Services

### reconciliation-service

**Status**: REMOVED **Reason**: Functionality integrated into `position-balance-monitor-service` **Date**: Feb 2026

`position-balance-monitor-service` is now the **source of truth** for positions and handles:

- Position tracking from fills
- Account query integration (via `unified-order-interface`)
- Exchange reconciliation (fetch + compare positions)
- Position state API (for strategy queries)

**Migration**:

- All reconciliation logic → `position-balance-monitor-service`
- API endpoints → Query `position-balance-monitor-service` position state API
- Reconciliation events → Standard lifecycle events in `position-balance-monitor-service`

---

### risk-monitor-service + exposure-monitor-service

**Status**: MERGED **Reason**: Consolidated into `risk-and-exposure-service` **Date**: Feb 2026

`risk-and-exposure-service` provides:

- **Pre-trade risk checks** (reject instructions violating limits)
- **Real-time risk monitoring** (exposure aggregation, limit monitoring)
- **Breach alerting** (alert on limit violations)

**Migration**:

- Risk monitoring logic → `risk-and-exposure-service` pre-trade checks + monitoring
- Exposure tracking → `risk-and-exposure-service` exposure aggregation
- Risk metrics → `risk-and-exposure-service` unified metrics

---

## Planned Deprecation — 2026-05-23 Consolidation (IN-FLIGHT)

> **[DELTA 2026-05-22]** **Current state:** As of 2026-05-22 (one day before cutover), the consolidations below are
> still IN-FLIGHT — no Phase 7 archive has landed. **Planned delta:** Phase 6 parity + Phase 7 archive are the
> outstanding gate items per `plans/active/strategy_repo_consolidation_2026_05_19.md` and
> `plans/active/ml_repo_consolidation_2026_05_19.md`. If Phase 6 parity slips past 2026-05-23, the entries below
> auto-flip to `BLOCKED-CUTOVER` (source repos remain alive un-archived; archive deferred post-cutover per the
> soft-freeze rule). **Target:** all 5 source repos archived; sub-packages canonical in `strategy-service/` and new
> `ml-service/` respectively.

The following 5 repos are being consolidated into 2 target repos pre-2026-05-23 cutover, mirroring the features-service
precedent (2026-05-08).

### Strategy consolidation (3 repos → `strategy-service` in-place)

| Source repo                        | Status                     | Target sub-package           | Plan                                                     |
| ---------------------------------- | -------------------------- | ---------------------------- | -------------------------------------------------------- |
| `risk-and-exposure-service`        | PLANNED-ARCHIVE 2026-05-19 | `strategy_service/risk/`     | `plans/active/strategy_repo_consolidation_2026_05_19.md` |
| `position-balance-monitor-service` | PLANNED-ARCHIVE 2026-05-19 | `strategy_service/position/` | `plans/active/strategy_repo_consolidation_2026_05_19.md` |
| `pnl-attribution-service`          | PLANNED-ARCHIVE 2026-05-19 | `strategy_service/pnl/`      | `plans/active/strategy_repo_consolidation_2026_05_19.md` |

Target architecture SSOT: `04-architecture/strategy-service-architecture.md` (status: stub until Phase 9).

### ML consolidation (2 repos → new `ml-service`)

| Source repo            | Status                     | Target sub-package      | Plan                                               |
| ---------------------- | -------------------------- | ----------------------- | -------------------------------------------------- |
| `ml-training-service`  | PLANNED-ARCHIVE 2026-05-19 | `ml_service/training/`  | `plans/active/ml_repo_consolidation_2026_05_19.md` |
| `ml-inference-service` | PLANNED-ARCHIVE 2026-05-19 | `ml_service/inference/` | `plans/active/ml_repo_consolidation_2026_05_19.md` |

Target architecture SSOT: `04-architecture/ml-service-architecture.md` (status: stub until Phase 9).

**Soft freeze (both consolidations)**: no new public-API surfaces, no new top-level packages, no module renames in any
of the 5 source repos until Phase 7 archive lands. Internal bugfixes + test work continue. Cross-plan banner
coordination per `/codex/05-infrastructure/plan-aware-merge-resolution.md`.

**Auto-flip to `BLOCKED-CUTOVER`** if Phase 6 parity slips — sub-packages remain merged (correctness preserved), source
repos remain alive un-archived, archive deferred post-cutover. No late-binding hacks.

---

## Archived Documentation

Archived documentation for these services can be found in:

- `01-domain/batch/per-service/_archived/`
- `02-data/batch/per-service/_archived/`
- `03-observability/batch/per-service/_archived/`
- `04-architecture/batch/per-service/_archived/`
- `05-infrastructure/batch/per-service/_archived/`

---

## Current Post-Trade Services

| Service                            | Purpose                                        | Priority    |
| ---------------------------------- | ---------------------------------------------- | ----------- |
| `position-balance-monitor-service` | Source of truth for positions + reconciliation | P0-critical |
| `risk-and-exposure-service`        | Pre-trade risk checks + real-time monitoring   | P0-critical |
| `pnl-attribution-service`          | P&L attribution (unchanged)                    | P2-medium   |

---

**See Also**:

- `11-project-management/epics/post-trade-and-execution-epic.md`
- `10-audit/_service-pipeline-post-trade.yaml`
- `11-project-management/service-registry.yaml`
