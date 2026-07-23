---
doc_type: issue
title: Manifest hygiene RED — 1 AG(s) with findings (2026_06_22)
summary:
  "The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: defi. Finding-classes:
  schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captur..."
status: superseded
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-22
parent_epic: manifest_master
priority: P2
source: [manifest_hygiene_daily.py, data_pipeline_hardening_self_monitoring_2026_06_22.md]
assigned_vm:
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

> **🟦 SUPERSEDED → archived 2026-06-30.** Later defi manifest-hygiene snapshot `manifest_hygiene_red_2026_06_27`
> carries the live state; the defi DIVERGENT_EMPTY work is link-tracked to
> `data_pipeline_hardening_self_monitoring_2026_06_22`. Content-verified in the consolidation pass (§6 A1.1 of
> `plan_issue_epic_consolidation_2026_06_30`).

# Manifest hygiene RED — 1 AG(s) with findings (2026_06_22)

> Auto-filed by the daily data-pipeline audit `manifest_hygiene_daily.py` (Wave 4b, Phase 5 scripted→LLM escalation
> hop). A deterministic candidate list was non-empty — the verdicts below need a planning-VM slot's judgment (real gap
> vs code bug, straggler vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: defi. Finding-classes:
schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captured_no_parquet,
shard_4pillar_fail.

Candidate list(s) (deterministic, machine-written):

- `/home/ubuntu/unified-trading-system-repos/unified-trading-pm/plans/audit/results/manifest_hygiene_defi_2026_06_22.csv`

## Why it matters

Each class is a data-correctness signal: non-v9 rows are pre-canonicalisation stragglers; oracle-expects-but-empty is a
candidate C1 misclassification (real gap vs code bug — needs judgment); non-canonical paths break selective reads;
phantoms are captured cells with no parquet.

## Recommended decision

Triage each candidate CSV: confirm real gaps → backfill; confirm code bugs → fix the adapter/writer; confirm intentional
new venues/spellings → extend the UAC oracle/canonical builders. Per
data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 3/5.
