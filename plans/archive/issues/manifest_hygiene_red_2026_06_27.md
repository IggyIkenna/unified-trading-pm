---
doc_type: issue
title: Manifest hygiene RED — 1 AG(s) with findings (2026_06_27)
summary:
  "The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: defi. Finding-classes:
  schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captur..."
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest, data-correctness, defi, phantom-captures, data-pipeline, monitoring, audit]
related: [data_pipeline_hardening_self_monitoring_2026_06_22]
created: 2026-06-27
parent_epic: observability_master
priority: P2
source: [manifest_hygiene_daily.py, data_pipeline_hardening_self_monitoring_2026_06_22.md]
assigned_vm: NA
resolved_by: delegated to plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md for execution
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

> **🟢 RESOLVED 2026-06-27 -- tracking fully handed off to the named active dispatch-batch plan. Archived per
> issue-doc-lifecycle.**

# Manifest hygiene RED — 1 AG(s) with findings (2026_06_27)

> Auto-filed by the daily data-pipeline audit `manifest_hygiene_daily.py` (Wave 4b, Phase 5 scripted→LLM escalation
> hop). A deterministic candidate list was non-empty — the verdicts below need a worker's judgment (real gap vs code
> bug, straggler vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: defi. Finding-classes:
schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captured_no_parquet,
shard_4pillar_fail.

Candidate list(s) (deterministic, machine-written):

- `plans/audit/results/manifest_hygiene_defi_2026_06_27.csv` (path corrected 2026-07-28 — the `.tabs/<N>/` slot-path
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

**Corrected 2026-07-12 (plan-reconciliation findings 206, 209; §A2 B-queue ruling)** — the open todo below directs
diagnosis "in `market-tick-data-service`" for all 5 finding-classes; two of them are now known NOT to be MTDS bugs:

- `phantom_captured_no_parquet` + `shard_4pillar_fail` — root-caused as false positives in the shared audit script
  itself (`e2e-testing/scripts/audit/manifest_hygiene_daily.py` `_check_phantom` / `_check_4pillar`), fixed
  `e2e-testing@3e37b0c` (2026-07-06, 7 new tests, 57/57 green; verified via `git log`). See
  `manifest_hygiene_red_2026_07_06.md` (same script, cefi instance) for the full root-cause writeup. A worker picking up
  this todo should NOT re-diagnose these two classes as an MTDS bug.
- `schema_version_not_v9` — the alert-TRUTHFULNESS bug (string-vs-int `schema_version` compare producing a false "100%"
  count) was fixed same-day in the sibling issue
  `data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md` Finding 1 (SHIPPED
  `e2e-testing@21ce846`, QG green 81s; verified via `git log`). The underlying REAL non-v9 residual (~4-13%) is still
  open and tracked there (OPERATOR-GATED real-infra op) — not a fresh diagnosis target here.
- `oracle_expects_but_empty` + `noncanonical_path_on_disk` — NOT addressed by either fix above; the open todo's
  "diagnose + fix ... in `market-tick-data-service`" directive still applies to these two classes as originally written.

(was: the todo below presented as an undifferentiated 5-class MTDS diagnosis target with no cross-reference to the
same-day/since-shipped fixes above.) Checkbox intentionally left unflipped below — this is a scope-narrowing annotation,
not a completion claim; `oracle_expects_but_empty` and `noncanonical_path_on_disk` are still open and undiagnosed.

## Final triage verdict (2026-07-28, slot-5) — the 2 classes left open by the 2026-07-12 note

Per `plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` batch2-item — read the full candidate CSV (8
rows: `oracle_expects_but_empty`×4, `schema_version_not_v9`×1 — out of scope, already fixed elsewhere per the 2026-07-12
note above — and `shard_4pillar_fail`×1 — also out of scope, false-positive already fixed):

- **`oracle_expects_but_empty`** — sample candidate:
  `venue=UNISWAP_V4 data_type=dex_pool_swaps date=2026-06-23/2026-06-24` (15,697 DIVERGENT_EMPTY cells total that day).
  **Verdict: REAL GAP, not a code bug** — the very next day's phantom reconcile
  (`mvp_backfill_defi_onchain_v10_2026_06_27.md`, 2026-06-28T21:35Z entry) flipped 219,632 phantom `empty_confirmed`
  rows to `attempted_failed`, including **dex_pool_swaps=20,586** with `UNISWAP_V4=69,573` as the top venue by volume —
  i.e. this exact cell was a phantom-capture misclassification that got corrected one day after this CSV was generated.
  The underlying `dex_pool_swaps` gap for UNISWAP_V4 remains an ACTIVE, tracked backfill target: see
  `plans/active/issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md` (status: open, 2026-07-24) which
  documents UNISWAP_V4 dex_pool_swaps as "PARTIAL, expected pre-2025 absence" with a currently-running fleet (relaunched
  2026-07-23), and the still-`status: active` `plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md`. No fresh MTDS
  code fix needed here — already covered by those two live efforts.
- **`noncanonical_path_on_disk`** — **zero candidates** in this CSV (confirmed by reading the file in full: only
  `oracle_expects_but_empty`/`schema_version_not_v9`/`shard_4pillar_fail` rows present). `_check_path_canonicality`
  (`e2e-testing/scripts/audit/manifest_hygiene_daily.py`) is a deterministic index-only check with no link-tracking
  suppression path, so an empty candidate list here means the check genuinely found 0 violations for defi on 2026-06-27.
  Confirmed clean, nothing to triage.

## Todos

- [x] [CODE] P1. Manifest hygiene RED — 1 AG(s) with findings (2026_06_27) — diagnose + fix the root cause
      (misclassified-empty vs real gap, not-v9 schema row, or oracle-expects-but-empty divergence) in
      `market-tick-data-service`. Read `SUB_AGENT_MANDATORY_RULES.md` + the data-pipeline codex SSOT + the candidate
      CSV(s) above first (source `manifest_hygiene_daily.py`). — already covered by
      plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md (see that doc for execution). **Final triage
      of the 2 still-open classes done 2026-07-28 (slot-5) — see "Final triage verdict" section above: both are real,
      already-tracked residuals of the live `mvp_backfill_defi_onchain_v10_2026_06_27.md` /
      `mtds_dex_pools_swaps_backfill_verification_2026_07_24.md` effort (`oracle_expects_but_empty`) or confirmed clean
      (`noncanonical_path_on_disk`, 0 candidates) — no new code fix required.
