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
status: complete
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
last_updated: "2026-08-20" # archived — batch13-finalize reconciliation confirmed both items land clean
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

- [x] ✅ [DATA] P1. **CF-7 relabel residual diagnosis for prediction.** Source: `data_completion_prediction_2026_07_15.md` item 4's residual (verbatim: "blank `data_type` (17 rows, both buckets) is skip+logged by the migrator → diagnose at rebuild from the parquet's own `data_type` column; confirm the ~21 UNKNOWN-venue cells are object-backed (relabel) vs phantom (honest drop)"). Read-only diagnosis/classification only — no relabel, no delete, no code change.
  **Scope**:
  1. For the ~17 blank-`data_type` rows (both legacy+canonical buckets, per the CF-7 migrator's skip-log) — read each row's own parquet object and determine its true `data_type` from the object's own column data; report the resolved value per row.
  2. For the ~21 UNKNOWN-venue cells — for each, determine whether the underlying GCS object exists (object-backed — would need a relabel) or has no backing object (phantom — an honest drop, no action needed).
  **Done-when**: a report listing every one of the ~17+~21 rows/cells with its resolved classification, plus corrected counts if the real numbers differ from the ~17/~21 estimates in the source doc.
  **If the report finds object-backed cells needing an actual relabel**: file that as a new, separately-scoped `plans/active/issues/<slug>_2026_08_19.md` finding — do not perform the relabel in this todo.

  **RESULT: NO-ACTION — all residuals PHANTOM, 0 object-backed, 0 remaining in the live estate (2026-08-19, slot-31).**
  Read-only diagnosis against (a) the live canonical `_index` (`market-data-tick-pred-prd-central-element-323112`,
  **2,814,442 rows**, via `read_availability_index_safe` column-pruned under `run-bounded-analysis.sh`), (b) the pre-CF7
  `_index` snapshot `_index/snapshots/pre_cf7_v4_cleanup_2026_07_11.parquet` (**757,476 rows** — the historical state carrying
  the residual cells), and (c) a 41-day GCS delimiter-walk of the canonical object layer (venue + data_type spellings, same
  strategy as `audit_index_vs_gcs_spellings.py`). No GCS write, no relabel, no delete, no code change.

  1. **~21 UNKNOWN-venue cells — corrected count = 21 (exact), ALL PHANTOM.** The pre-CF7 snapshot carries exactly **21**
     `venue=UNKNOWN` rows (all `data_type=trades`, `capture_status=captured`, dates 2025-03-14..2026-04-06) — every one with a
     **blank `instrument_id`**. A blank-iid `trades` cell has no condition_id → no object filename → structurally **cannot be
     object-backed** (the CF-11 re-emit in `_rebuild_prediction_cf11.py` explicitly skips this malformed legacy-phantom class).
     A further **168 `venue=''` (blank) cells** of the same shape sit alongside (corrected total unk+blank = **189**; the source
     doc's ~21 counted only the `UNKNOWN` spelling). Live `_index` today: **0** UNKNOWN/blank-venue cells of ANY status. Object
     layer: **0** `venue=UNKNOWN`/blank-venue dirs (41-day walk) — corroborated by the E5-rebuild census argument (the live
     `_index` was rebuilt from a full object walk and emits a row per on-disk venue, so 0 UNKNOWN rows ⟹ 0 UNKNOWN-venue
     objects). **Classification: phantom → honest drop; no relabel needed; no object-backed residual exists.**
  2. **~17 blank-`data_type` rows — corrected count = 18, ALL PHANTOM.** The pre-CF7 snapshot carries **18** `data_type=''`
     rows (**17 `attempted_failed` + 1 `empty_confirmed`**, all `venue=POLYMARKET`, **blank `instrument_id`**) — i.e. **0
     captured**, no object identity. The "diagnose at rebuild from the parquet's own `data_type` column" remedy is **moot**:
     there is no parquet behind a blank-iid cell (no condition_id → no object path). Live `_index` today: **0** blank-data_type
     rows. Object layer: **0** blank `data_type=` dirs (41-day walk). **Classification: phantom → honest drop; no action. No
     captured data was lost (these cells were never captured).**
  3. **CF-7 relabel confirmed complete at the object layer.** On-disk venues = **{KALSHI, POLYMARKET}** only; on-disk object
     data_types = **{book_snapshot_5, trades}** only. The legacy aliases (`prediction_trades` 3,385 rows and `book_snapshot`
     5 rows in the pre-CF7 snapshot) are **absent from the live `_index`** — fully relabeled to `trades`/`book_snapshot_5` by
     the CF-7 `_cf7_normalise` (`migrate_prediction_to_pred_prd_v9.py`) at copy time. The `market_lifecycle` (4,560) /
     `MARKET_LIFECYCLE` (2,280) casing split in the live `_index` is the **documented intentional dual-casing**
     (`/codex/02-data/prediction-data-types-catalog.md` §"MARKET_LIFECYCLE dual-casing": UAC-canonical `market_lifecycle` for
     MTDS/MDPS, `MARKET_LIFECYCLE` for instruments-service) and is 100% `empty_confirmed` — **not a CF-7 residual, no action.**

  **No object-backed cells needing a relabel were found → per this item's own instruction, no new issue doc filed.** The ~21
  UNKNOWN-venue resolution was independently recorded in `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`
  (slot-14, 2026-08-04: "0 UNKNOWN-venue cells … cleaned up by a prior pass with no new action needed").

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
- **2026-08-19 (item 2 shipped — slot-31)**: CF-7 relabel residual diagnosis ran **NO-ACTION** — see the item's RESULT
  block above for the full report. Corrected counts vs the source doc's estimates: **21 UNKNOWN-venue cells (exact)** + **168
  blank-venue cells** (sibling phantom class, extra beyond the ~21) + **18 blank-data_type rows (vs ~17)** — ALL phantom
  (blank `instrument_id` → no condition_id → no backing object; the CF-11 re-emit's malformed-class skip) and ALL absent from
  the live 2,814,442-row `_index` and the on-disk object layer (41-day delimiter walk: venues {KALSHI, POLYMARKET}, data_types
  {book_snapshot_5, trades}). No object-backed cells found → no relabel, no delete, no code change (per the brief); no new
  issue doc filed (the item's own instruction gates issue-filing on object-backed cells, none found). The prior
  `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` `[x]` resolution (slot-14 2026-08-04) is confirmed.
  Item 2 flipped `[x]`.
- **2026-08-20 (finalize reconciliation — slot-11)**: `prediction_satellite_ao_dispatch_batch13_2026_08_19_finalize.md`
  item 1 re-verified `data_completion_prediction_2026_07_15.md` items 1-4 against these two results. Items 1/2/3 were
  already correctly flipped; item 4 (E6 CF-7 relabel) was flipped `[x]` citing this batch's item 2 NO-ACTION result. No
  new follow-up pending. Both this batch's todos land clean → archived via the standard 6-step ritual (this same
  commit).

> **ARCHIVED 2026-08-20** — this batch's 2 todos both landed clean (item 1 PASS, item 2 NO-ACTION) and were reconciled
> into `data_completion_prediction_2026_07_15.md`'s own items 1-4 by
> `prediction_satellite_ao_dispatch_batch13_2026_08_19_finalize.md` item 1. No new follow-up pending; no codex-alignment
> change needed (routine data-completeness audit, no new contract established). superseded_by: N/A.
