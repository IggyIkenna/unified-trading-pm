---
doc_type: issue
title: "Manifest hygiene RED — 4 AG(s) with findings (2026_08_19)"
summary: "Daily manifest-hygiene-vs-GCS audit found non-empty candidate lists across cefi/defi/prediction/sports/tradfi (schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captured_no_parquet, shard_4pillar_fail) — needs worker triage of real gap vs code bug."
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [manifest-hygiene, data-pipeline, honest-coverage]
related: [/plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md]
created: 2026-08-19
author: "manifest_hygiene_daily.py (data-pipeline daily audit)"
parent_epic: observability_master
priority: P1
assigned_vm: planning
resolved_by:
source:
  - manifest_hygiene_daily.py
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Manifest hygiene RED — 4 AG(s) with findings (2026_08_19)

> Auto-filed by the daily data-pipeline audit `manifest_hygiene_daily.py` (Wave 4b, Phase 5
> scripted→LLM escalation hop). A deterministic candidate list was non-empty — the
> verdicts below need a worker's judgment (real gap vs code bug, straggler
> vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: cefi, defi, prediction, sports, tradfi. Finding-classes: schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captured_no_parquet, shard_4pillar_fail.

Candidate list(s) (deterministic, machine-written):

- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_cefi_2026_08_19.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_tradfi_2026_08_19.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_sports_2026_08_19.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_prediction_2026_08_19.csv`

## Why it matters

Each class is a data-correctness signal: non-v9 rows are pre-canonicalisation stragglers; oracle-expects-but-empty is a candidate C1 misclassification (real gap vs code bug — needs judgment); non-canonical paths break selective reads; phantoms are captured cells with no parquet.

## Recommended decision

Triage each candidate CSV: confirm real gaps → backfill; confirm code bugs → fix the adapter/writer; confirm intentional new venues/spellings → extend the UAC oracle/canonical builders. Per data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 3/5.

Cold-start context: read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
in full + `/codex/05-infrastructure/data-pipeline-alerts.md` + the candidate CSV(s)
above before acting.

## Todos

- [ ] [CODE] P1. Manifest hygiene RED — 4 AG(s) with findings (2026_08_19) — diagnose + fix the root cause (misclassified-empty vs real gap, not-v9 schema row, or oracle-expects-but-empty divergence) in `market-tick-data-service`. Read `SUB_AGENT_MANDATORY_RULES.md` + the data-pipeline codex SSOT + the candidate CSV(s) above first (source `manifest_hygiene_daily.py`).
