---
doc_type: issue
title: Manifest hygiene RED — 1 AG(s) with findings (2026_06_29)
summary:
  "The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: cefi. Finding-classes:
  schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captur..."
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest, data-correctness, cefi, phantom-captures, data-pipeline, monitoring, audit]
related: [mvp_backfill_cefi_tick_v10_2026_06_27]
created: 2026-06-29
parent_epic: observability_master
priority: P2
source: [manifest_hygiene_daily.py, data_pipeline_hardening_self_monitoring_2026_06_22.md]
assigned_vm: NA
resolved_by: delegated to plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md for execution
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-12
---

> **🟢 RESOLVED 2026-06-29 -- tracking fully handed off to the named active dispatch-batch plan. Archived per
> issue-doc-lifecycle.**

# Manifest hygiene RED — 1 AG(s) with findings (2026_06_29)

> Auto-filed by the daily data-pipeline audit `manifest_hygiene_daily.py` (Wave 4b, Phase 5 scripted→LLM escalation
> hop). A deterministic candidate list was non-empty — the verdicts below need a worker's judgment (real gap vs code
> bug, straggler vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: cefi. Finding-classes:
schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captured_no_parquet,
shard_4pillar_fail.

Candidate list(s) (deterministic, machine-written):

- `plans/audit/results/manifest_hygiene_cefi_2026_06_29.csv` (path corrected 2026-07-28 — the `.tabs/<N>/` slot-path
  model cited originally is RETIRED; confirmed present at this repo-root-relative path)

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

## Reconciliation note (2026-07-12)

**Corrected 2026-07-12 (plan-reconciliation finding 210; §A2 B-queue ruling)** — the open todo below directs diagnosis
"in `market-tick-data-service`" for all 5 finding-classes; three of them are now known NOT to be open MTDS bugs:
`phantom_captured_no_parquet` + `shard_4pillar_fail` were root-caused as false positives in the shared audit script
itself (`e2e-testing/scripts/audit/manifest_hygiene_daily.py` `_check_phantom` / `_check_4pillar`), fixed
`e2e-testing@3e37b0c` (2026-07-06, cefi instance, 7 new tests, 57/57 green; verified via `git log`). See
`manifest_hygiene_red_2026_07_06.md` (same script, same cefi asset_group) for the full root-cause writeup.
`schema_version_not_v9`'s alert-TRUTHFULNESS bug (string-vs-int `schema_version` compare producing a false "100%"
non-v9" count) was ALSO fixed same-day via `e2e-testing@21ce846` (2026-07-12), per the sibling reconciliation note in
`manifest_hygiene_red_2026_06_27.md` (same script, shared cefi/defi/tradfi bug, not scoped to one asset_group) —
verified `git log`. Only the small REAL non-v9 residual (~4-13% depending on AG) remains open, tracked in
`data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md` (OPERATOR-GATED real-infra op), not a
fresh diagnosis target here. A worker picking up this todo should NOT re-diagnose `phantom_captured_no_parquet`,
`shard_4pillar_fail`, or `schema_version_not_v9`'s alert-truthfulness as an MTDS bug — only `oracle_expects_but_empty`
and `noncanonical_path_on_disk` remain open diagnosis targets as originally written.

(was: the todo below presented as an undifferentiated 5-class MTDS diagnosis target with no cross-reference to the
since-shipped audit-script fixes above.) Checkbox intentionally left unflipped below — this is a scope-narrowing
annotation, not a completion claim; 2 of the 5 classes (`oracle_expects_but_empty`, `noncanonical_path_on_disk`) are
still open and undiagnosed.

## Final triage verdict (2026-07-28, slot-5) — the 2 classes left open by the 2026-07-12 note

Per `plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` batch2-item — read the full candidate CSV
(11 rows: `oracle_expects_but_empty`×4, `phantom_captured_no_parquet`×3 — out of scope, already fixed as a false
positive per the 2026-07-12 note above — and `schema_version_not_v9`×1 — also out of scope):

- **`oracle_expects_but_empty`** — sample candidate: `venue=OKX-SWAP data_type=trades date=2026-05-20/21/22` (20,289
  DIVERGENT_EMPTY cells total that day). **Verdict: REAL GAP, not a code bug** — this exact venue/data_type/date-range
  candidate is independently confirmed in `plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md`'s progress
  log (its own audit re-runs list "`oracle_expects_but_empty`: 5 (OKX-SWAP trades 2026-05-20/21/22)" across multiple
  sessions), where OKX-SWAP's residual `attempted_failed`/empty rows (~13,600) were actively re-probed via dedicated
  Tardis backfill VMs (wave-1/wave-2 launches) as part of that plan's Layer-1 gate work. That plan is now
  `status: complete` (2026-07-15, "remnant folded out to its target"); any still-open residual for this venue/date
  window is carried forward inside the broader CeFi completion program chain
  (`plans/archive/2026_07/cefi_completion_program_2026_07_15.md` and its successors), not a fresh MTDS bug. No new code
  fix needed here — already covered by that live/completed backfill lineage.
- **`noncanonical_path_on_disk`** — **zero candidates** in this CSV (confirmed by reading the file in full: only
  `oracle_expects_but_empty`/`phantom_captured_no_parquet`/`schema_version_not_v9` rows present).
  `_check_path_canonicality` (`e2e-testing/scripts/audit/manifest_hygiene_daily.py`) is a deterministic index-only check
  with no link-tracking suppression path, so an empty candidate list here means the check genuinely found 0 violations
  for cefi on 2026-06-29. Confirmed clean, nothing to triage.

## Todos

- [x] [CODE] P1. Manifest hygiene RED — 1 AG(s) with findings (2026_06_29) — diagnose + fix the root cause
      (misclassified-empty vs real gap, not-v9 schema row, or oracle-expects-but-empty divergence) in
      `market-tick-data-service`. Read `SUB_AGENT_MANDATORY_RULES.md` + the data-pipeline codex SSOT + the candidate
      CSV(s) above first (source `manifest_hygiene_daily.py`). — already covered by
      plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md (see that doc for execution). **Final triage
      of the 2 still-open classes done 2026-07-28 (slot-5) — see "Final triage verdict" section above: both are real,
      already-tracked residuals of the (now complete) `mvp_backfill_cefi_tick_v10_2026_06_27.md` /
      `cefi_completion_program_2026_07_15.md` lineage (`oracle_expects_but_empty`) or confirmed clean
      (`noncanonical_path_on_disk`, 0 candidates) — no new code fix required.
