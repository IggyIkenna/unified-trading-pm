---
doc_type: plan
title: prediction satellite AO dispatch batch 13 — 2026-08-19
summary: >-
  Extraction batch from the prediction tranche's 2026-08-19 /na-eligibility-audit sweep — 2 conflict-cleared,
  bounded/deterministic read-only audit items pulled from data_completion_prediction_2026_07_15.md via the per-todo
  RECLASSIFY_SPLIT path, closing the loop on 4 items an earlier pass (2026-08-10) tagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE
  and explicitly deferred to "a closer per-item read" that 3 subsequent passes (round11 08-09, context-scout 08-15,
  08-18) never delivered. Both extracted items are read-only audits/diagnostics against the prediction manifest and raw
  objects — no live-pipeline code change, no GCS mutation. 2 sibling rider items (pipeline_mode/source stamping) stay in
  the source doc: their own text confirms the underlying work already landed or needs no separate action, and both are
  fully subsumed by this batch's item 1 comparison result — extracting them separately would be duplicate dispatch, not
  additional coverage. Conflict-checked against every active planning doc under parent_epic: predictions_master and
  parent_epic: manifest_master, the tranche's consolidated closeout, and every existing prediction satellite batch
  (1-12) before drafting — no item here duplicates ground an existing dispatched todo already claims.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, satellite-batch, na-eligibility-audit, reclassify-split, manifest-audit]
related:
  [
    /plans/active/data_completion_prediction_2026_07_15.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19" # item 1 shipped PASS same day, no bump needed
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/data_completion_prediction_2026_07_15.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_prediction_manifest.py,
  ]
source: >-
  Drafted by the 2026-08-19 /na-eligibility-audit prediction-tranche run (autonomous, dispatch agt-0e920e) — per-todo
  RECLASSIFY_SPLIT path. Items 1-4 of data_completion_prediction_2026_07_15.md's C0-walk rider family were tagged
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE by the 2026-08-10 na-eligibility-audit pass, which explicitly deferred a "closer
  per-item read" to a future run (source doc Progress Log, 2026-08-10 entry) — 3 subsequent passes (round11 08-09,
  context-scout 08-15, 08-18) re-confirmed KEEP-NA without delivering that read. This run performed the promised closer
  read: items 1 and 2 (pipeline_mode/source riders) have no independent remaining action per their own text ("do NOT run
  it separately"; "no writer code change needed" — historical backfill only) and are fully covered by this batch's item
  1 pass criteria, so they stay in the source doc as KEEP-NA, annotated as answered-by-this-batch. Items 3 and 4's
  residual are genuine, precisely-scoped, read-only audits with stated done-whens — promoted to RECLASSIFY per the
  bounded-outcome bar ("does X match Y" / "count instances of Z" is eligible when precisely scoped).
---

# prediction satellite AO dispatch batch 13 — 2026-08-19

> Extracted from `/plans/active/data_completion_prediction_2026_07_15.md` (source doc keeps `assigned_vm: NA` — 16
> other items remain genuinely gated there). Both todos below are **read-only** — no code change, no GCS write/delete.

- [x] ✅ [DATA] P0. **Post-walk `(date,venue,data_type)` comparison for prediction manifest.** Source: `data_completion_prediction_2026_07_15.md` item 3 (verbatim: "re-run the `(date,venue,data_type)` comparison → legacy-only CELLS = 0; canonical `_index` all v9; `pipeline_mode` non-null; `source` populated on every cell (HARD — zero blank; the API source per venue)"). Read-only — no GCS mutation, no code change; reuse `rebuild_prediction_manifest.py`'s classify/comparison logic (or a dedicated read-only comparison invocation of it) against the live prediction `_index`.
  **Done-when (report all 4, PASS only if all 4 hold)**:
  1. legacy-only cells = 0
  2. every canonical `_index` row is schema v9
  3. `pipeline_mode` is non-null on every row
  4. `source` is populated (non-blank) on every row, correct API-source-per-venue
  **If all 4 PASS**: (a) flip `data_completion_prediction_2026_07_15.md` items 1 and 2 `[x]`, citing this result — their own text already says they need no independent action beyond this check; (b) flip this item `[x]` here; (c) READ `data_source_provenance` Phase 6 prediction and `bucket_name_ssot…` Phase 6/7's C-GREEN-for-prediction gate — if this comparison is confirmably their sole remaining blocker, cite this evidence there too (do not flip either unless you've read it and confirmed that).
  **If ANY criterion FAILS**: do not flip any checkbox anywhere. Report FAIL with exact counts/examples per failing criterion as a new `plans/active/issues/<slug>_2026_08_19.md` finding (findings-triage HARD RULE) — a failure here means the C0-walk didn't fully land and needs a design/build follow-up, out of this todo's read-only scope.

  **RESULT: PASS — all 4 criteria hold (2026-08-19, slot-33).** Read the live canonical `_index`
  (`market-data-tick-pred-prd-central-element-323112/_index/availability_index.parquet`, 2,814,442 rows) via UTL
  `read_availability_index_safe` (column-pruned: date/venue/data_type/schema_version/pipeline_mode/source/
  capture_status/instrument_id/asset_group), run under `scripts/dev/run-bounded-analysis.sh --mem-cap 6G` (per the
  data_engineering craft's memory-bounding guardrail) inside `market-tick-data-service/.venv`. No GCS write, no code
  change.
  1. **legacy-only cells = 0**: both legacy buckets (`market-data-tick-prediction-central-element-323112`,
     `instruments-store-prediction-central-element-323112`) confirmed still 404/gone via `storage.Client().bucket(...).exists()`
     — no legacy source exists to diverge from, so legacy-only cells = 0 by construction (consistent with the L6
     decommission's own 2026-07-13 record in `legacy_bucket_dual_write_decommission_2026_07_24.md`, which already
     confirmed 0 legacy-only cells and deleted both buckets before this doc was written).
  2. **canonical `_index` all v9**: `schema_version` distribution = `{9: 2,814,442}` — 100% v9, no other value present.
  3. **`pipeline_mode` non-null on every row**: 0 rows with blank/null `pipeline_mode` (0 / 2,814,442).
  4. **`source` populated + correct per-venue**: 0 rows with blank/null `source` (0 / 2,814,442). Per-venue
     distribution: `POLYMARKET → polymarket_clob (2,282,066) / polymarket_gamma_api (2,922)`;
     `KALSHI → kalshi (529,454)` — both match the API-source-per-venue expectation (UAC `SOURCE_PRIORITY` registry
     entries cited in the source doc's C-source RIDER item), no mismatches found.

  (a) Flipped `data_completion_prediction_2026_07_15.md` items 1 (C-pipeline_mode RIDER) and 2 (C-source RIDER) `[x]`,
  citing this result. (c) Read `data_source_provenance_enforcement_2026_07_24.md` — its 12 open items are cross-AG P0
  rollups / cross-plan-sequencing judgment calls, none is a prediction-specific item gated solely on this comparison,
  so no flip made there. Read `legacy_bucket_dual_write_decommission_2026_07_24.md`'s L6 item — prediction's row is
  already `✅ DONE 2026-07-13` (buckets deleted, predates this result) — nothing left to flip. Evidence:
  `unified-trading-pm@<see commit>`.

- [ ] [DATA] P1. **CF-7 relabel residual diagnosis for prediction.** Source: `data_completion_prediction_2026_07_15.md` item 4's residual (verbatim: "blank `data_type` (17 rows, both buckets) is skip+logged by the migrator → diagnose at rebuild from the parquet's own `data_type` column; confirm the ~21 UNKNOWN-venue cells are object-backed (relabel) vs phantom (honest drop)"). Read-only diagnosis/classification only — no relabel, no delete, no code change.
  **Scope**:
  1. For the ~17 blank-`data_type` rows (both legacy+canonical buckets, per the CF-7 migrator's skip-log) — read each row's own parquet object and determine its true `data_type` from the object's own column data; report the resolved value per row.
  2. For the ~21 UNKNOWN-venue cells — for each, determine whether the underlying GCS object exists (object-backed — would need a relabel) or has no backing object (phantom — an honest drop, no action needed).
  **Done-when**: a report listing every one of the ~17+~21 rows/cells with its resolved classification, plus corrected counts if the real numbers differ from the ~17/~21 estimates in the source doc.
  **If the report finds object-backed cells needing an actual relabel**: file that as a new, separately-scoped `plans/active/issues/<slug>_2026_08_19.md` finding — do not perform the relabel in this todo.

## Progress Log

- **2026-08-19 (drafted)**: Batch drafted by the 2026-08-19 `/na-eligibility-audit` prediction-tranche run (dispatch
  agt-0e920e). Conflict-check clear: active planning docs under `parent_epic: predictions_master` and
  `parent_epic: manifest_master` (3 DeFi-only docs, no overlap), `prediction_consolidated_closeout_2026_07_18.md`
  (Deferred-work bullets are about E2 aliases/A2 residual/CQG residual §5/Phase-B prod migration — none overlap these 2
  items), and every existing prediction satellite batch 1-12 (batch6's 2 mentions of
  `data_completion_prediction_2026_07_15.md` are about the UNRELATED Phase-B CQG-bundle object-layer migration
  [items 6-11 in the source doc], not the C0-walk rider items extracted here) — no competing claim found on either item.
- **2026-08-19 (item 1 shipped — slot-33)**: Item 1 (post-walk comparison) ran PASS on all 4 criteria — see the item's
  own RESULT block above for full evidence. Flipped item 1 `[x]` here and items 1/2 `[x]` in
  `data_completion_prediction_2026_07_15.md` (both cited its own text as needing no independent action beyond this
  check). Read `data_source_provenance_enforcement_2026_07_24.md` and `legacy_bucket_dual_write_decommission_2026_07_24.md`'s
  L6 gate per the item's step (c) — neither had a prediction-specific item still gated on this result (the L6 gate for
  prediction was already `✅ DONE 2026-07-13`), so no flip made in either. Item 2 (CF-7 relabel residual diagnosis)
  untouched — separate, not in this task's scope.
