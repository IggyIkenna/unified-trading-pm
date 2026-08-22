---
doc_type: issue
title: "Manifest hygiene RED — 1 AG(s) with findings (2026_08_16)"
created: 2026-08-16
author: "manifest_hygiene_daily.py (data-pipeline daily audit)"
context_scope: [/codex/02-data/availability-manifest-and-data-status.md, /codex/05-infrastructure/data-pipeline-alerts.md, /codex/02-data/four-surface-reconciliation-procedure.md]
parent_epic: observability_master
assigned_vm: planning
source:
  - manifest_hygiene_daily.py
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
locked_by:
summary:
  "Daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for cefi
  (schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk) — first real
  run after the _DIVERGENCE_CLI path-resolution fix landed."
status: resolved
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
resolved_by: e2e-testing@9ed5f78e3f
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

> **📦 ARCHIVED 2026-08-22 (archival pass 2)** — `locked_by: live-defi-rollout` placeholder cleared (corpus-wide
> fix, `scripts/plans/clear_locked_by_placeholder_2026_08_12.py --apply`); 0 open todos, `status: resolved`.
> Kept as a historical daily-monitor record.
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

- [x] ✅ [CODE] P1. Manifest hygiene RED — 1 AG(s) with findings (2026_08_16) — diagnosed. **Root cause is NOT a
      market-tick-data-service code bug or an oracle misclassification** — the `oracle_expects_but_empty`/
      `oracle_expects_no_manifest_row` findings for the 10 sampled venue×data_type pairs (BINANCE-FUTURES/SPOT,
      BYBIT, COINBASE-SPOT/FUTURES, KRAKEN-SPOT, OKX-SPOT/SWAP, DERIBIT) are REAL, GENUINE gaps — they are exactly
      the residual coverage the active P0 `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` chronological
      Tardis backfill is mid-flight filling (measured ~26% complete as of 2026-08-15T21:53Z per that plan's own
      STALE banner). DERIBIT's `options_chain`/`futures_chain` rows are additionally already tracked by the
      still-open `issues/deribit_options_chain_af_g4_blocker_2026_07_03.md`. `schema_version_not_v9` (1/29,938,146
      rows) is an immaterial legacy straggler, not a code defect.

      **The actual bug** (`e2e-testing/scripts/audit/manifest_hygiene_daily.py`): the daily audit's link-tracking
      suppression (`_active_backfill_residual_venues`) — whose whole purpose is to silence a per-day escalation for
      a venue already covered by an active backfill wave — globbed ONLY the retired `mvp_backfill_<ag>_*.md`
      filename convention. cefi's roster-of-record plan forked/renamed to
      `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` on 2026-07-25, so the glob matched zero files in
      `plans/active/`, the roster silently went empty for cefi, and suppression was disabled with no signal that it
      happened — every divergence finding for cefi has re-escalated as "new" ever since (compounded by this being
      the FIRST run where the detector could even fire at all, per the related
      `dp_audit_sibling_repo_cli_paths_and_escalation_commit_identity_2026_08_16.md` container-path fix that landed
      the same day).

      **Fixed**: widened `_active_backfill_residual_venues`'s glob to sweep both the legacy
      `mvp_backfill_<ag>_*.md` convention AND the current `<ag>_*backfill*.md`/`<ag>_*coverage*.md` convention, so a
      future plan rename doesn't silently disable suppression again. Added a regression test
      (`test_active_backfill_residual_venues_parses_current_naming_convention`) planting a
      `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`-shaped fixture. Also appended a
      `| VENUE | status |` roster table to `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` itself (a pure
      format restatement of that plan's own already-documented 26-venue MVP roster, in the exact markdown-table
      shape `_BACKFILL_ROSTER_ROW_RE` parses) so the now-fixed glob has real table rows to extract — a glob fix
      alone would not have re-enabled suppression, since the target plan's venue mentions are prose lists, not
      tables. 226/226 e2e-testing unit tests green (full suite, forced non-cached run). — e2e-testing@9ed5f78e3f +
      unified-trading-pm (this doc + the roster-table plan edit, same commit batch). No backfill work itself was
      performed here — that is `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`'s own in-progress scope,
      unchanged by this fix.
