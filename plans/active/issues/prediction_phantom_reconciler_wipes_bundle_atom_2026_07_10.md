---
doc_type: issue
title:
  "Phantom-manifest reconciler wipes ~15,769 legitimately-captured prediction bundle-atom cells to attempted_failed — it
  has no bundle-aware existence check (synthetic cqg instrument_id has no on-disk path segment)"
summary:
  "Read-only diagnosis of the live pred-prd _index (760,300 rows, 2026-07-10) found ZERO rows anywhere with
  data_type=prediction_canonical_question_group at capture_status=captured — all 71,767 bundle rows are
  empty_confirmed/attempted_failed/expected_unattempted. Root cause traced against live GCS + live code: the
  phantom-manifest reconciler (unified_trading_library/reconcile/manifest.py, _PHANTOM_ERROR_REASON, lifted from
  instruments-service/scripts/reconcile_phantom_manifest_rows_all.py) assumes a PER-OBJECT row-key where instrument_id
  maps to a real GCS path segment. But the v9 prediction bundle atom's instrument_id is a SYNTHETIC
  canonical_question_group label (e.g. BTC_UP_DOWN_DAILY) that never appears as a path segment — the raw objects are
  per-cid `trades` parquets, and NO `data_type=prediction_canonical_question_group/` folder exists on disk by design
  (the bundle is a manifest-only atom, cluster-validated at write time, not object-existence-validated). So the phantom
  prober finds 'no object at canonical path' for EVERY bundle row and demotes 100% of them to
  attempted_failed[phantom_captured_no_parquet_at_canonical_path]. Net: ~15,769 legit captured bundle cells (7,278
  POLYMARKET + 8,491 KALSHI) were wiped. Verified: a real per-cid object parses+classifies to cqg=BTC_UP_DOWN_DAILY,
  envelope resolves, row_count=500 — the rebuild wrote it captured, then the reconciler (written_at
  2026-06-27T09:36:17Z) demoted it. This is the PRIMARY driver of the prediction _index residual, and it falsifies the
  earlier working hypothesis that the schema_version=4 legacy rows are 'superseded by an existing v9 captured bundle' —
  there is NO captured v9 bundle row for any date to supersede them."
status: open
nature: notes
asset_group: [prediction]
stage: [data, meta]
repos: [unified-trading-library, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [manifest, phantom-reconciler, bundle-atom, data-correctness, prediction, canonicalisation, cross-repo]
related:
  [
    plans/active/prediction_manifest_canonicalisation_2026_06_01.md,
    plans/active/downstream_services_manifest_canonicalisation_2026_06_01.md,
    codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-10
parent_epic: mtds_mdps_master
priority: P0
assigned_vm:
resolved_by:
locked_by:
source:
  - /autonomous prediction _index residual root-cause diagnosis 2026-07-10 (read-only, live prod GCS
    central-element-323112)
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Phantom reconciler wipes prediction bundle-atom captured cells (bundle-atom blind spot)

> **Surfaced by the /autonomous prediction `_index` residual root-cause diagnosis (2026-07-10, read-only against live
> prod GCS `central-element-323112`).** Operator-notify-required (data-correctness / cross-repo / contradicts stated
> hypothesis). No prod writes were made during diagnosis.

## The bug (root cause)

The phantom-manifest reconciler demotes a `captured` manifest row to
`attempted_failed[phantom_captured_no_parquet_at_canonical_path]` when it cannot find a GCS object at the row's
canonical path. Its path-existence check (`unified_trading_library/reconcile/manifest.py`, five drift axes: hive-vocab,
instrument_type casing, empty-schema-4, path-prefix, chain-bundle) assumes `instrument_id` is a **per-object** key that
maps to a real path segment.

The v9 prediction **bundle atom** breaks that assumption: its `instrument_id` is a **synthetic
`canonical_question_group`** (e.g. `BTC_UP_DOWN_DAILY`), `data_type=prediction_canonical_question_group`,
`instrument_type=prediction`. The raw objects on disk are per-`conditionId` `data_type=trades` parquets; there is **no**
`data_type=prediction_canonical_question_group/` folder — the bundle is a **manifest-only atom**, validated at
write-time by cluster validation (`observed_clusters={market_id: rows}`), NOT by object existence. So the phantom prober
can never match an object for any bundle row → demotes **100%** of them.

**Impact (measured on the live `_index`):** ZERO `data_type=prediction_canonical_question_group` rows at `captured`
across the whole corpus; ~**15,769** legit captured bundle cells (7,278 POLYMARKET + 8,491 KALSHI) wiped to
`attempted_failed`. This is why E7 CF-verify cannot go GREEN and why the schema_version=4 legacy per-instrument rows may
be the only surviving manifest evidence of real activity for those days.

## Secondary gap (smaller)

The rebuild's canonical-path regex `_CANONICAL_PRED_RE`
(`market_tick_data_service/scripts/rebuild_prediction_manifest.py`) silently drops an older-migration object layout
shaped `venue=…/chain=POLYGON/instrument_type=prediction_market/…/underlying=BTC/…parquet` (~3.3% of objects on the
sampled day) — `parse_canonical_prediction_path` returns `None` for that shape. Not the primary driver, but a real
coverage gap.

## Remediation (ordered — DO NOT purge legacy rows until step 1+2 land)

1. **[CODE, P0, base-tier — blast-radius-gated] Make the phantom reconciler bundle-aware.** In
   `unified_trading_library/reconcile/manifest.py` (+ the IS wrapper `reconcile_phantom_manifest_rows_all.py`): EXEMPT
   bundle-atom data_types (`prediction_canonical_question_group`, and any manifest-only bundle atom) from the
   object-at-canonical-path existence check — their existence is proven by write-time cluster validation, not a path
   segment. Prefer a principled exemption keyed on "manifest-only bundle atom" (mirror the existing `schema_version=4`
   skip pattern), NOT a prediction-only hack. **HARD (rule 11): this reconciler runs against ALL asset groups' manifests
   — verify the exemption does not weaken phantom detection for cefi/tradfi/sports/defi (per-object atoms) before
   shipping; add a regression test that a bundle-atom captured row survives reconcile while a genuinely-phantom
   per-object row is still demoted.**
2. **[CODE, P1] Fix the rebuild `_CANONICAL_PRED_RE`** to also parse the
   `chain=/underlying=/instrument_type=prediction_market` older-migration object shape (or confirm those objects are
   superseded and should be dropped).
3. **[DATA, P0] Re-run `rebuild_prediction_manifest.py`** after 1+2 land → the ~15,769 real bundle cells re-emit as
   `captured`; then re-diagnose whether a captured v9 equivalent now exists per date before touching the legacy rows.
4. **[DATA] Then** re-evaluate the schema_version=4/5 legacy per-instrument rows (9,174), the 189 UNKNOWN/blank-venue
   rows, and the 17 blank-`data_type` phantom aggregate-markers — only after the captured bundle is restored (they may
   be the only evidence today).

## Safe-to-execute-NOW cleanups (independent of the phantom root cause)

- **124 lowercase `venue="kalshi"` duplicate rows** — 100% exact byte-identical collision with canonical
  `venue="KALSHI"` rows (same capture_status/pipeline_mode/source/error_reason, differ only in venue casing), zero
  object-backing on GCS. **Safe, idempotent, zero data-loss** → delete the 124 lowercase rows, keep the uppercase
  (pattern: `scripts/delete_tradfi_aggregate_phantom_markers_2026_07_07.py`). No sign-off needed.
- **27,292 `batch_polymarket_clob` blank-`source` rows** (`written_at ≤ 2026-06-29`, pre the
  `manifest_record_expected_empty_blank_source_2026_07_08` fix) — a rebuild CF-11 re-emit backfills
  `source=polymarket_clob` via the now-fixed `_stamp_producer_source`. Idempotent but heavy (rewrites the whole ~700K
  honest-absence corpus); a surgical direct-writer targeting just this filter is cheaper. (The 639,991 `live_*`
  blank-source rows are EXEMPT by design — producer-source is never back-stamped for live/replay pipeline_modes.)
