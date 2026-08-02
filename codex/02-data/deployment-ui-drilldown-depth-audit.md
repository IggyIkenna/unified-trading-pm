---
doc_type: codex-ssot
title: Deployment UI Drilldown Depth Audit
summary: >-
  Per-asset-group drilldown depth audit of the deployment-ui Data Status panel — compares the columns the UI exposes
  today against the target leaf atom per the codex shard-key matrix (DeFi needs first-class chain, options needs
  root/instrument_type, prediction needs canonical_question_group, sports needs league_id). RESOLVED — the remediation
  shipped via data_status_drilldown_shard_atom_alignment_2026_05_07 (complete, archived); this doc records the outcome.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer, admin]
tags: [ui, data-status, manifest, audit, defi, single-walk]
related: [/codex/02-data/availability-manifest-and-data-status.md, /codex/02-data/cross-asset-canonical-target-ssot.md]
created: 2026-05-07
authoritative_for: [deployment-ui data-status drilldown depth audit]
referenced_by:
  [
    /plans/epics/infrastructure_master.md,
    /plans/archive/data_status_drilldown_shard_atom_alignment_2026_05_07.md,
  ]
owner:
last_reviewed: 2026-09-30
code_refs:
---

# Deployment UI Drilldown Depth Audit

> **Status:** RESOLVED (verified 2026-07-31). The stub was created 2026-05-07 to anchor forward-references from the
> then-active alignment plan. That plan — `/plans/archive/data_status_drilldown_shard_atom_alignment_2026_05_07.md` —
> is `status: complete` (41/41 todos) and archived, and the drilldown gap it tracked is closed in code (see § Outcome).
> This doc is kept as the audit record; it is no longer a forward-looking backlog.

## Purpose

The shard-key matrix (codified in CLAUDE.md "Shard-granularity SSOT") declares the canonical leaf atom per asset_group —
e.g. CeFi options drill to `(asset_group, venue, data_type, options_chain, root, day)` while DeFi drills to
`(asset_group, chain, venue/protocol, data_type, instrument_id, day)`. The deployment-ui Data Status drilldown today
exposes a per-asset-group set of columns that does not always reach those leaves. This doc audits the gap.

## Scope

- Per-asset-group drilldown column lists in `deployment-ui/src/components/DataStatusDrilldown.tsx` (with
  `DataStatusTab.tsx` / `LiveDataStatusTab.tsx` and helpers in `deployment-ui/src/lib/data-status-helpers.ts`).
- API surface in `deployment-api/deployment_api/services/data_status_drilldown/` powering each drill (sibling modules:
  `services/data_status_service.py`, `services/data_status_hierarchical.py`, `routes/data_status/`).
- Per-shard-detail / per-shard-download endpoints.
- Excluded: the rollup-level summary (handled by slicer); UI design / styling.

## Outline (audit dimensions, as scoped 2026-05-07)

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

## Outcome (verified 2026-07-31)

The remediation backlog above is closed. Verified against the working tree:

| Target leaf axis                        | Where it landed                                                                        |
| --------------------------------------- | -------------------------------------------------------------------------------------- |
| `chain` (DeFi first-class)              | `deployment-api/deployment_api/services/data_status_drilldown/`                        |
| `instrument_type` / `root` (options)    | `deployment-api/deployment_api/services/data_status_drilldown/`                        |
| `canonical_question_group` (prediction) | `deployment-api/deployment_api/services/data_status_drilldown/`                        |
| `league_id` (sports)                    | `deployment-api/deployment_api/services/data_status_drilldown/`                        |
| Drilldown UI                            | `deployment-ui/src/components/DataStatusDrilldown.tsx`                                 |
| MTDS per-shard recovery CTA flags       | `market-tick-data-service` CLI — `--instrument-type`, `--root`, `--day`, `--shard-key`  |

The § "Open questions" below were the 2026-05-07 design questions; they are retained as historical context, not as
live decisions.

## Cross-references

- **Plan(s) that implemented this:** [`/plans/epics/infrastructure_master.md`](/plans/epics/infrastructure_master.md),
  [`/plans/archive/data_status_drilldown_shard_atom_alignment_2026_05_07.md`](/plans/archive/data_status_drilldown_shard_atom_alignment_2026_05_07.md)
  (`status: complete`, archived).
- **Related codex SSOTs:** [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md),
  [`/codex/02-data/cross-asset-canonical-target-ssot.md`](/codex/02-data/cross-asset-canonical-target-ssot.md) (the
  shard-atom grain matrix this doc's "shard-key matrix" referred to; the CLAUDE.md "Shard-granularity SSOT" section it
  was originally slated to be lifted from no longer exists verbatim — this 2026-07-18 cross-asset-group consolidation is
  the doc that superseded it).
- **Code:** `deployment-ui/src/components/DataStatusDrilldown.tsx`,
  `deployment-api/deployment_api/services/data_status_drilldown/`.

## Open questions (historical — 2026-05-07)

- Should the drilldown UI be metadata-driven (read shard-key matrix from UAC at runtime) or hardcoded per-asset-group
  React components? (metadata-driven scales better but heavier upfront).
- Do we surface partial-bundle status at the bundled-shard leaf? (e.g. options_chain ES.OPT shows 8/11 clusters
  captured)
- For prediction `canonical_question_group`, do we list every market_id under the group as a sub-leaf, or only show
  group-level rollup with a "see markets" tab?
