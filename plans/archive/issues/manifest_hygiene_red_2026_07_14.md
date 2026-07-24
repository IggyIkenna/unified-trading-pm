---
doc_type: issue
title: "Manifest hygiene RED — 1 AG(s) with findings (2026_07_14)"
created: 2026-07-14
parent_epic: observability_master
assigned_vm: planning
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
repos: [e2e-testing]
scope: [engineer, admin]
tags: [manifest-hygiene, data-pipeline, daily-audit]
related: []
priority: P2
resolved_by: e2e-testing@0fa7148
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-14
---

# Manifest hygiene RED — 1 AG(s) with findings (2026_07_14)

> Auto-filed by the daily data-pipeline audit `manifest_hygiene_daily.py` (Wave 4b, Phase 5 scripted→LLM escalation
> hop). A deterministic candidate list was non-empty — the verdicts below need a worker's judgment (real gap vs code
> bug, straggler vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: cefi. Finding-classes:
schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captured_no_parquet,
shard_4pillar_fail.

Candidate list(s) (deterministic, machine-written):

- `/home/ubuntu/unified-trading-system-repos/.tabs/2/unified-trading-pm/plans/audit/results/manifest_hygiene_cefi_2026_07_14.csv`

## Why it matters

Each class is a data-correctness signal: non-v9 rows are pre-canonicalisation stragglers; oracle-expects-but-empty is a
candidate C1 misclassification (real gap vs code bug — needs judgment); non-canonical paths break selective reads;
phantoms are captured cells with no parquet.

## Recommended decision

Triage each candidate CSV: confirm real gaps → backfill; confirm code bugs → fix the adapter/writer; confirm intentional
new venues/spellings → extend the UAC oracle/canonical builders. Per
data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 3/5.

Cold-start context: read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` in full +
`/codex/05-infrastructure/data-pipeline-alerts.md` + the candidate CSV(s) above before acting.

## Todos

- [x] [CODE] P1. ✅ Manifest hygiene RED — 1 AG(s) with findings (2026_07_14) — root cause diagnosed as a
      NON-ACTIONABLE-SAMPLE bug in the AUDIT code itself (`e2e-testing/scripts/audit/manifest_hygiene_daily.py`), NOT a
      real MTDS gap in this finding's escalation. `_apply_link_tracking` suppresses a divergence finding-class only when
      EVERY distinct venue is covered by the active `mvp_backfill_cefi_tick_v10_2026_06_27.md` roster (all-or-nothing),
      but the emitted CSV/issue sample was always the top-10 venue×data_type pairs BY COUNT. Verified: all 6 venues in
      today's `oracle_expects_but_empty` sample (BINANCE-FUTURES, BITFINEX-FUTURES, BYBIT, DERIBIT, OKX-FUTURES,
      OKX-SWAP) ARE present in the roster table (confirmed via git blame — committed 2026-06-28, byte-identical across
      slot clones) — the escalation's visible sample was 100% already backfill-tracked, meaning an unlisted long-tail
      venue outside the top-10 was the actual, invisible reason link-tracking couldn't suppress the class (the
      `oracle_expects_no_manifest_row` finding independently confirms the roster-diff methodology: BYBIT-SPOT +
      COINBASE-FUTURES are genuinely uncovered — only mentioned in the plan's prose, never in a `| VENUE |     ... |`
      table row the link-tracking regex matches). Fixed: `FindingClass` now carries the full unsliced venue×data_type
      breakdown; `_apply_link_tracking` re-prioritizes a partially-covered finding's sample toward its uncovered
      venue(s) before slicing to top-10, so a future escalation is actually triageable instead of hiding the real signal
      behind an already-tracked majority. The suppress/escalate decision is unchanged (no findings are newly silenced).
      Also fixed 9 pre-existing RUF002/RUF003 ambiguous-unicode lint violations in the same file (quality-gates.sh was
      already red on these before this task; fixed inline per findings-triage "in your file → fix in same commit"). 4
      new/updated tests (`test_check_divergence_populates_breakdown`, `test_check_missing_expected_reads_csv` breakdown
      assertion, `test_apply_link_tracking_partial_coverage_prioritizes_uncovered_sample`), 61/61 green. The underlying
      BYBIT-SPOT/COINBASE-FUTURES gap + the cefi non-v9 residual + the 4-pillar signal are real data-correctness
      surfaces already covered by `mvp_backfill_cefi_tick_v10_2026_06_27.md`'s in-progress backfill wave — extension of
      that plan's scope, not a code fix in this task. — e2e-testing@0fa7148 + evidence:
      `tests/unit/test_dp_audit.py::test_apply_link_tracking_partial_coverage_prioritizes_uncovered_sample` + 3 more; QG
      green sentinel `0fa714869f7c9a517b019ee407aff547fbb15b3d`.
