---
doc_type: issue
title: "Manifest hygiene RED — 1 AG(s) with findings (2026_07_06)"
created: 2026-07-06
parent_epic: observability_master
assigned_vm: NA
source:
  - manifest_hygiene_daily.py
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
locked_by:
summary:
  "The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: cefi. Finding-classes:
  schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captur..."
status: resolved
nature: process
asset_group: [cefi]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [manifest-hygiene, data-pipeline, daily-audit]
related: []
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-06
resolved_by: e2e-testing@3e37b0c
---

# Manifest hygiene RED — 1 AG(s) with findings (2026_07_06)

> Auto-filed by the daily data-pipeline audit `manifest_hygiene_daily.py` (Wave 4b, Phase 5 scripted→LLM escalation
> hop). A deterministic candidate list was non-empty — the verdicts below need a worker's judgment (real gap vs code
> bug, straggler vs intentional new venue). See `codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: cefi. Finding-classes:
schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captured_no_parquet,
shard_4pillar_fail.

Candidate list(s) (deterministic, machine-written):

- `/home/ubuntu/unified-trading-system-repos/.tabs/11/unified-trading-pm/plans/audit/results/manifest_hygiene_cefi_2026_07_06.csv`

## Why it matters

Each class is a data-correctness signal: non-v9 rows are pre-canonicalisation stragglers; oracle-expects-but-empty is a
candidate C1 misclassification (real gap vs code bug — needs judgment); non-canonical paths break selective reads;
phantoms are captured cells with no parquet.

## Recommended decision

Triage each candidate CSV: confirm real gaps → backfill; confirm code bugs → fix the adapter/writer; confirm intentional
new venues/spellings → extend the UAC oracle/canonical builders. Per
data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 3/5.

Cold-start context: read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` in full +
`codex/05-infrastructure/data-pipeline-alerts.md` + the candidate CSV(s) above before acting.

## Todos

- [x] [CODE] P1. ✅ Manifest hygiene RED — 1 AG(s) with findings (2026_07_06) — root cause diagnosed as TWO
      false-positives in the AUDIT code itself (`e2e-testing/scripts/audit/manifest_hygiene_daily.py`), NOT in
      `market-tick-data-service`. `_check_phantom` counted ANY log line containing "phantom" — filed the CLEAN "Phantom
      captures: 0" + "Manifest is clean." lines as 2 findings. `_check_4pillar` used `rc != 0` alone — conflated `rc=2`
      harness error (`GCP_PROJECT_ID must be set`) with `rc=1` real fail, sampled the ALL-GREEN tallies line via a loose
      `"phantom" in line.lower()` match against `manifest_phantom_captured_zero_rows=0`. Fixed: phantom now parses
      `Phantom captures: N` deterministically; 4pillar distinguishes `rc=2` (SKIPPED w/ harness-error reason) from
      `rc=1` (real fail w/ `\bFAIL\b` whole-word sample matcher). 7 new tests, 57/57 green. Remaining REAL findings (10
      DIVERGENT_EMPTY + 10 MISSING_EXPECTED + 344,842 non-v9 rows) are covered by
      `mvp_backfill_cefi_tick_v10_2026_06_27.md` (link-tracking uncovers DERIBIT / BYBIT-SPOT / COINBASE-FUTURES not yet
      in the roster — extension of that plan, not a code fix in this task). — e2e-testing@3e37b0c + evidence:
      `tests/unit/test_dp_audit.py::test_check_phantom_clean_manifest_reports_zero` +
      `test_check_4pillar_harness_error_is_skipped_not_fail` + 5 more; QG green sentinel
      `3e37b0c684edf85579cc1a581cb5d2f8ca75707c`.
