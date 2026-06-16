---
scope: [engineer, admin]
title: Deployment UI Drilldown Depth Audit
status: planned
created: 2026-05-07
authoritative_for:
  Per-asset-group drilldown depth audit of the deployment-ui Data Status panel. Compares current drilldown depth (what
  columns the UI exposes) against target drilldown depth per the codex shard-key matrix; tracks remediation backlog so
  every asset_group can drill to its proper leaf.
referenced_by:
  - plans/epics/infrastructure_master.md
  - plans/ai/data_status_drilldown_shard_atom_alignment_2026_05_07.md
related:
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/04-architecture/shard-granularity-ssot.md
last_reviewed: 2026-05-17
---

# Deployment UI Drilldown Depth Audit

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from active plans. Body to be filled in as
> the drilldown alignment plan is executed.

## Purpose

The shard-key matrix (codified in CLAUDE.md "Shard-granularity SSOT") declares the canonical leaf atom per asset_group —
e.g. CeFi options drill to `(asset_group, venue, data_type, options_chain, root, day)` while DeFi drills to
`(asset_group, chain, venue/protocol, data_type, instrument_id, day)`. The deployment-ui Data Status drilldown today
exposes a per-asset-group set of columns that does not always reach those leaves. This doc audits the gap.

## Scope

- Per-asset-group drilldown column lists in `deployment-ui/src/pages/data-status/`.
- API surface in `deployment-api/deployment_api/services/data_status.py` powering each drill.
- Per-shard-detail / per-shard-download endpoints.
- Excluded: the rollup-level summary (handled by slicer); UI design / styling.

## Outline (planned sections)

1. **Audit methodology** — for each asset_group, list current drilldown columns from the UI source + API param schema
   - shard-key matrix target; produce a delta table.
2. **Per-asset-group findings** — CeFi options / CeFi spot+perp / DeFi / TradFi futures+ETFs+options / Sports /
   Prediction. Each with current depth vs target depth + missing columns.
3. **Missing column dimensions** — `chain` for DeFi (first-class axis), `instrument_type` / `root` for options chains,
   `canonical_question_group` for prediction, `league_id` for sports.
4. **Remediation backlog** — per asset_group, what needs adding to: API schema, UI columns, leaf parquet download, on-
   click behaviour.
5. **Acceptance criteria** — operator can drill from asset_group → leaf parquet via UI clicks alone; no need to
   construct GCS paths manually.
6. **MTDS recovery wiring** — drill-down leaves expose "rerun this shard" CTA via MTDS CLI flags (`--instrument-type`,
   `--root`, `--day`, `--shard-key`).

## Cross-references

- **Plan(s) implementing this:** [`infrastructure_master`](../../plans/epics/infrastructure_master.md),
  [`data_status_drilldown_shard_atom_alignment`](../../plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.md).
- **Related codex SSOTs:** [`availability-manifest-and-data-status`](./availability-manifest-and-data-status.md),
  `shard-granularity-ssot` (TBD lift from CLAUDE.md).
- **Code:** `deployment-ui/src/pages/data-status/`, `deployment-api/deployment_api/services/data_status.py`.

## Open questions

- Should the drilldown UI be metadata-driven (read shard-key matrix from UAC at runtime) or hardcoded per-asset-group
  React components? (metadata-driven scales better but heavier upfront).
- Do we surface partial-bundle status at the bundled-shard leaf? (e.g. options_chain ES.OPT shows 8/11 clusters
  captured)
- For prediction `canonical_question_group`, do we list every market_id under the group as a sub-leaf, or only show
  group-level rollup with a "see markets" tab?
