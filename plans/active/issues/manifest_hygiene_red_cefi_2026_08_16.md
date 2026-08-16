---
doc_type: issue
title: "Manifest hygiene RED — 1 AG(s) with findings (2026_08_16)"
created: 2026-08-16
author: "manifest_hygiene_daily.py (data-pipeline daily audit)"
parent_epic: observability_master
assigned_vm: planning
source:
  - manifest_hygiene_daily.py
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
locked_by: live-defi-rollout
summary:
  "Daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for cefi
  (schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk) — first real
  run after the _DIVERGENCE_CLI path-resolution fix landed."
status: open
nature: process
asset_group: [cefi]
stage: [meta]
repos: [e2e-testing]
scope: [engineer, admin]
tags: [manifest-hygiene, data-pipeline, daily-audit]
related:
  [
    dp_audit_sibling_repo_cli_paths_and_escalation_commit_identity_2026_08_16,
    cefi_consolidated_closeout_aggregated_sources_2026_07_24,
  ]
priority: P1
resolved_by:
---

# Manifest hygiene RED — 1 AG(s) with findings (2026_08_16)

> Auto-filed by the daily data-pipeline audit `manifest_hygiene_daily.py` (Wave 4b, Phase 5
> scripted→LLM escalation hop). A deterministic candidate list was non-empty — the
> verdicts below need a worker's judgment (real gap vs code bug, straggler
> vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: cefi. Finding-classes: schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captured_no_parquet, shard_4pillar_fail.

Candidate list(s) (deterministic, machine-written):

- `/home/ubuntu/unified-trading-system-repos/.tabs/12/unified-trading-pm/plans/audit/results/manifest_hygiene_cefi_2026_08_16.csv`

## Why it matters

Each class is a data-correctness signal: non-v9 rows are pre-canonicalisation stragglers; oracle-expects-but-empty is a candidate C1 misclassification (real gap vs code bug — needs judgment); non-canonical paths break selective reads; phantoms are captured cells with no parquet.

## Recommended decision

Triage each candidate CSV: confirm real gaps → backfill; confirm code bugs → fix the adapter/writer; confirm intentional new venues/spellings → extend the UAC oracle/canonical builders. Per data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 3/5.

Cold-start context: read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
in full + `/codex/05-infrastructure/data-pipeline-alerts.md` + the candidate CSV(s)
above before acting.

## Todos

- [ ] [CODE] P1. Manifest hygiene RED — 1 AG(s) with findings (2026_08_16) — diagnose + fix the root cause (misclassified-empty vs real gap, not-v9 schema row, or oracle-expects-but-empty divergence) in `market-tick-data-service`. Read `SUB_AGENT_MANDATORY_RULES.md` + the data-pipeline codex SSOT + the candidate CSV(s) above first (source `manifest_hygiene_daily.py`).
