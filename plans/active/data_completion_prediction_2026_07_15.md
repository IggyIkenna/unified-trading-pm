---
doc_type: plan
title: Data completion to 100% — Prediction manifest canonicalisation + backfill (split from M-1)
summary: >-
  Prediction slice of the data-completion-to-100% program, split out of data_completion_to_100_all_ag_2026_06_21 (M-1)
  on 2026-07-15 per operator ruling (plan-reconcile §8) when M-1 breached the absolute 5000-line ceiling. Carries the
  prediction scope M-1 absorbed in the 2026-07-13 consolidation, migrated VERBATIM — no scope added, dropped or
  reworded. M-1 remains the coordinator hub for cross-cutting work (bucket naming, source provenance, bar-edge) and owns
  the shared Progress Log.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [backfill, manifest, honest-coverage, data-completion, prediction, data-correctness]
related: [/plans/active/data_completion_to_100_all_ag_2026_06_21.md]
created: 2026-07-15
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2
last_updated: 2026-07-15
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: [data_completion_to_100_all_ag_2026_06_21 (M-1) — split 2026-07-15, plan-reconcile §8 operator ruling A]
drift_direction: advance-code
context_scope:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/per-asset-group-bucket-layouts.md,
    /codex/02-data/pipeline-mode-partition.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_prediction_manifest.py,
  ]
---

# Data completion to 100% — Prediction

> **Split from M-1 on 2026-07-15** (`data_completion_to_100_all_ag_2026_06_21.md`, plan-reconcile §8, operator ruling
> A). M-1 had reached 5,366 lines — the only file in the corpus over the absolute 5,000-line ceiling — after absorbing
> 130 folded-in todos in the 2026-07-13 consolidation. This plan carries M-1's **prediction** scope **verbatim**; M-1
> stays the coordinator hub (measured snapshot, per-AG launch matrix, cross-cutting scope, shared Progress Log).
>
> **Read M-1 first** for the program-level snapshot + launch matrix. Cross-cutting items (bucket-name SSOT, data-source
> provenance, bar-edge) deliberately stayed there — they are not prediction-specific.

### From `prediction_manifest_canonicalisation_2026_06_01.md` (archived 2026-07-13 -- Prediction manifest + data canonicalisation (legacy->canonical single-walk, L3 owner for prediction))

- [x] ✅ [DATA] P0. C0 ONE bundled walk: copy legacy `raw_tick_data/` + `processed_candles/` objects → canonical
      `pred-prd` at the canonical path (env-tier + `asset_group=` + `pipeline_mode=` partition); rewrite manifest rows
      to v9; typed empty-reasons. **`category=`→`asset_group=` lands on BOTH the object PATHS and the manifest `_index`
      ROWS in this walk** (CODE side — writers emit `asset_group=` — already shipped via archived
      `venue_axis_asset_group_vocabulary_2026_04_25`; this is historical data+manifest only). Server-side
      `gcs_copy_object` (layout-aware: prediction = `raw_tick_data/`/`processed_candles/`). RUN ON A VM via
      `VM_TASK=canonical-migration` (gated on L0 tarball-prune fix) OR locally if object count is small (P0 audit
      decides). **(MIGRATED FROM: `prediction_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)** — ✅ **na-eligibility-audit 2026-08-10: KEEP-NA-STALE-ITEM, closed.** See this same doc
      (`data_completion_prediction_2026_07_15.md`)'s own 2026-07-13 "Plan A `canonical_question_group` OBJECT-LAYER
      migration" section directly below, which states it "supersedes the C0/E-checklist copy-walk above for the _object
      shape_ question; the copy-walk itself already ran" and confirms the legacy
      `market-data-tick-prediction-…`/`instruments-store-prediction-…` buckets are CONFIRMED GONE (404, version-purged)
      — "there is no legacy-bucket input left to map". This item's copy-FROM source (the legacy bucket) no longer exists
      because the copy already ran as E4 (2026-06-29, pre-dating this doc). Closing on the doc's own superseding
      evidence; the sibling rider/verification items directly below (pipeline_mode rider, source rider, post-walk
      comparison, CF-7 relabel) are NOT closed by this — their own text leaves genuine ambiguity about whether they
      completed alongside E4, left open pending a closer per-item read.

- [ ] [DATA] P0. C-pipeline_mode RIDER: the `pipeline_mode=` partition for prediction lands in THIS walk (satisfies
      `pipeline_mode_partition_migration_2026_06_01.md` for prediction — do NOT run it separately). **(MIGRATED FROM:
      `prediction_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. C-source RIDER: stamp `source` = the data-source API (`polymarket_clob` / `polymarket_gamma_api` /
      `kalshi_*`) on every prediction cell in THIS walk (path/`pipeline_mode` → `source` column), re-consolidate into
      the `_index` — HARD, swap-resilient (a future Polymarket data-provider change stays distinguishable). Closes
      `data_source_provenance` Phase 6 prediction. **Venue ≠ source invariant preserved**: Polymarket/Kalshi remain
      VENUES (cross-venue dispersion is a feature-layer concern, not a source merge); when Kalshi lands it is a venue
      addition AND its cells stamp `kalshi_*` as source. Do NOT open a separate prediction source walk. **[CODE-WIRED —
      slot-5 confirmed 2026-06-03; operator picked source-column over N/A]** The CODE foundation is already in place:
      UAC `SOURCE_PRIORITY` carries `("prediction","trades")=["polymarket_clob"]`, `("prediction","book_snapshot")`,
      `("prediction","prediction_canonical_question_group")`, and
      `("prediction","MARKET_LIFECYCLE")=["polymarket_gamma_api"]` (+ `EMISSION_LATENCY_MS_BY_SOURCE` entries), and the
      UTL `manifest_writer.add()/record_captured_*` AUTO-STAMP the sole external source via `default_source` for
      single-source cells (no `MissingSourceError` — `source_required` is False). So **live/new writes already stamp
      `source`**; this rider is now just the HISTORICAL `_index` backfill — ensure the rebuild's `record_*` calls flow
      the parquet's own `data_source` (or let `default_source` auto-stamp `polymarket_clob`), no writer code change
      needed. The stale "prediction N/A" line was corrected in CLAUDE.md + `data_source_provenance` row (slot-5
      2026-06-03). **(MIGRATED FROM: `prediction_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [ ] [DATA] P0. Post-walk: re-run the `(date,venue,data_type)` comparison → **legacy-only CELLS = 0**; canonical
      `_index` all v9; `pipeline_mode` non-null; **`source` populated on every cell (HARD — zero blank; the API source
      per venue) — closes `data_source_provenance` Phase 6 prediction**. This is the C-GREEN signal `bucket_name_ssot…`
      Phase 6/7 waits on for the prediction legacy bucket decommission. **(MIGRATED FROM:
      `prediction_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. E6 CF-7 relabel. **CF-7 NOW BAKED INTO THE MIGRATOR (mtds@4b311c93)** — `_cf7_normalise` runs in BOTH
      path transforms BEFORE dedup: `venue UNKNOWN/blank → POLYMARKET` (prediction is single-venue today; Kalshi lands
      born-canonical), `data_type prediction_trades → trades` (verified the same markets). Grounded by the
      operator-requested overlap verification (2026-06-01): clean `(POLYMARKET,trades)` overlap is **byte-identical**
      between legacy + canon (401 common dates; sampled days had identical `condition_id` sets + identical per-object
      row counts) → legacy-wins + relabel loses nothing; canon's apparent 22 'canon-only' cells are venue=UNKNOWN/blank
      DRIFT (not unique data — canon has NO `ohlcv_*`/question_group that legacy has). **Residual (object-level,
      small):** blank `data_type` (17 rows, both buckets) is skip+logged by the migrator → diagnose at rebuild from the
      parquet's own `data_type` column; confirm the ~21 UNKNOWN-venue cells are object-backed (relabel) vs phantom
      (honest drop). **(MIGRATED FROM: `prediction_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [ ] [UAC] P3. **FINDING — new `grain_for_instrument_type('prediction','prediction_market')` returns `leaf` (slot-5
      verify 2026-06-07).** Correct for the INSTRUMENT axis (prediction markets are per-market leaves; no
      options_chain/futures_chain underlying-bundle), and **INERT today** — prediction's enumerator/catalogue do NOT
      consume `grain_for_instrument_type`; they drive cqg enumeration via the per-row `instr.data_type` grain-binding
      (the G1-ENUM reference). **Latent trap**: prediction's MANIFEST/atom grain is the cqg BUNDLE
      (`prediction_canonical_question_group`), NOT a per-market leaf — so IF a future refactor unifies the grain
      mechanisms and treats `grain_for_instrument_type` as THE enumeration-grain SSOT for prediction, it would over-fan
      per-market → the exact false-`expected_unattempted` pollution G1-ENUM prevents. Reconcile then (prediction needs a
      cqg-bundle grain value OR the unified path must preserve the data_type binding). Owner: the G1-ENUM bundle-grain
      SSOT (`proper_instrument_catalogue_lifecycle_rollup_2026_06_04` / coordinator G1-ENUM). Repo:
      unified-api-contracts. parent_epic: manifest_master. **Not owed now (HOLD; inert) — and NOT a deferred fix:**
      `leaf` is the CORRECT value for the instrument axis (changing it would be wrong), and the trap is already guarded
      by the existing grain-bound round-trip test (is@ec75c4e9) that asserts every prediction catalogue row carries
      `data_type` (so the `_row_data_types` short-circuit can't be silently bypassed). There is nothing to safely change
      today; this is a CONDITIONAL note for IF a future refactor ever unifies the two grain mechanisms (owned by the
      cross-cutting G1-ENUM SSOT, not prediction). **(MIGRATED FROM:
      `prediction_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] [UAC] P3. **CLOSED 2026-07-30 (na-eligibility-audit, prediction tranche) — EXACT DUPLICATE of the item directly
      above, no work dropped.** This checkbox was a verbatim second copy of the
      `grain_for_instrument_type('prediction','prediction_market')` finding (its text is a strict subset of the
      preceding item's — identical through "Not owed now (HOLD; inert)", minus that item's extra "and NOT a deferred
      fix" paragraph). Both were introduced by the same 2026-07-13 MTDS-consolidation migration from
      `prediction_manifest_canonicalisation_2026_06_01.md`, which folded the finding in twice. Closing the duplicate
      only — the surviving copy above still carries the full finding, its HOLD status, and its G1-ENUM owner, so the
      tracked work is unchanged and nothing becomes untracked by this close.

### 2026-07-13 — Plan A `canonical_question_group` OBJECT-LAYER migration — combined design (supersedes the C0/E-checklist copy-walk above for the _object shape_ question; the copy-walk itself already ran)

> **Operator ruling 2026-07-13**: prediction = ONE combined migration straight to the Plan A `canonical_question_group`
> shape — no interim pure-copy. **SCOPE CORRECTION (same day, fresh audit PM@194b7d542)**: the legacy
> `market-data-tick-prediction-…`/`instruments-store-prediction-…` buckets are CONFIRMED GONE (404, version-purged) —
> the historical "573,451 legacy objects" figure (`gcs_delete_list_and_e2e_data_accounting_2026_06_18.md`,
> `instruments_mtds_subset_consistency_remediation_2026_06_17.md`) refers to objects already copied into canonical
> `pred-prd` by the prior copy-walk (E4, ran 2026-06-29) and is now HISTORICAL PROVENANCE only — **there is no
> legacy-bucket input left to map**. The fresh audit counts **5.42M total objects** currently in
> `market-data-tick-pred-prd-central-element-323112` across ALL prediction data_types (trades, book_snapshot_5,
> market_lifecycle, …) — this migration's actual scope is the **`trades`/`prediction_trades` subset of that corpus
> only** (see "Scope: which data_type" below), not the full 5.42M.

**Codex SSOTs for this section**: `/codex/02-data/per-asset-group-bucket-layouts.md` ~L121 ("PREDICTION (post-Plan A
target)" table row — the ratified object shape); `/codex/02-data/pipeline-mode-partition.md` § "Predictions migration
(Plan A)"; `/codex/02-data/availability-manifest-and-data-status.md` § "Bundled data_types"
(`prediction_canonical_question_group` / `PREDICTION_GROUPS`). No conflicting in-flight migration found:
`gcloud compute instances list` (2026-07-13) shows no prediction/canonical-migration VM running; the only
prediction-adjacent active plans are `prediction_canonical_identity_migration_2026_07_08.md` (instruments-service
catalogue identity — orthogonal, different repo/data-plane), `predictions_other_bucket_and_ui_drilldown_2026_06_20.md`
(UI/OTHER-bucket, references this plan for the writer/data side — do not duplicate there), and
`prediction_capture_incident_remediation_2026_07_06.md` (capture-path dtype hardening + PERP adapter correction —
orthogonal).

#### Current state (verified live, 2026-07-13)

- Legacy buckets 404 confirmed (`gcloud storage buckets describe` on both `market-data-tick-prediction-…` and
  `instruments-store-prediction-…`).
- `market-data-tick-pred-prd-central-element-323112` raw_tick_data is **still per-market-file** (NOT yet the cqg
  rollup): sampled
  `day=2026-06-26/pipeline_mode=live_kalshi/asset_group=prediction/venue=KALSHI/ instrument_type=prediction_market/data_type=book_snapshot_5/KALSHI:PREDICTION_MARKET:{ticker}.parquet`
  (one file per market) and multiple other days 2021→2026-06 showing `data_type=trades` / `data_type=prediction_trades`
  (older, not yet CF-7-relabeled) per-market files. **Zero objects found anywhere under
  `data_type=prediction_canonical_question_group`** — the bundled OBJECT shape has never been written; only the MANIFEST
  already emits a `data_type=prediction_canonical_question_group` bundle row (see next point) — this is the gap this
  migration closes.
- Live `_index` (755,943 prediction rows, checked via direct parquet download) already shows
  `prediction_canonical_question_group` as a manifest data_type (POLYMARKET captured=7,289, KALSHI captured=10,040, plus
  various empty/expected states) — **the live writer already computes+emits the cqg-BUNDLE MANIFEST atom**
  (`manifest_finalize.py::_finalize_prediction_bundles`, fed by `partitioned_writer.py::_update_prediction_counts` /
  `_prediction_cluster_counts`) but the **raw OBJECT is still written per-market** (`partitioned_writer.py::write_chunk`
  groups by `symbol`, not by `canonical_question_group`, for non-derivative prediction rows). So the manifest has been
  "lying ahead" of the object layer since Wave-2 — this migration makes the object layer catch up.
- `trades`/`prediction_trades` manifest cells (10,799 total captured across venues) also exist as a SEPARATE, redundant
  per-market atom (`venue_fetch.py::_record_venue_shard_counts` → `shard_counts`/`captured_per_instrument_shards`, fed
  by `writer.underlying_counts` i.e. `_row_counts`) — this generic per-symbol atom is UNCHANGED by the design below (out
  of scope for this pass; flagged as a residual below).

#### Scope: which data_type actually rolls up

Only the raw **`trades`** data_type physically bundles into the `canonical_question_group={cqg}/ticks.parquet` shape.
Evidence: a live per-market `trades` object's columns are
`side, asset, conditionId, size, price, timestamp, title, slug, eventSlug, outcome, outcomeIndex, transactionHash, condition_id, data_type, instrument_type, underlying, market_category, market_type, resolution_period, data_source, venue, chain, ts_event, symbol`
— i.e. it carries EXACTLY the "6 legacy axes" the task names
(`data_source`/`chain`/`market_category`/`underlying`/`market_type`/`resolution_period`), already as ROW COLUMNS (not
path segments — that flattening already happened in the E4 copy-walk). `book_snapshot_5` / `market_lifecycle` rows ALSO
carry a `canonical_question_group` column (both adapters stamp it — `polymarket_adapter.py:676,795`,
`kalshi_adapter.py:520` — consumed today only by the MANIFEST completeness bundle, which conflates all three data_types
into one `_prediction_cluster_counts` accumulator) but have a DIFFERENT row schema (book depth levels, not trade prints)
— physically bundling them into the same file as `trades` would mix schemas. `prediction_trades` is a pre-CF-7 alias of
`trades` on older objects (2025-03-14→2026-03 sampled); the live adapter (`polymarket_adapter.py:664`) hardcodes
`data_type="trades"` today, so `prediction_trades` is a closed historical set, not a live emission.

#### Target write shape (ratified)

```
raw_tick_data/by_date/day={D}/pipeline_mode={mode}/asset_group=prediction/venue={V}/
  data_type=prediction_canonical_question_group/canonical_question_group={CQG}/ticks.parquet
```

One file per `(canonical_question_group, day)` per venue; `market_id` (the bare `symbol`/`condition_id`/ticker) survives
as a ROW COLUMN; the 6 legacy axes stay as row columns (harmless, already flattened). `pipeline_mode` sits LEFT of
`asset_group=` per `pipeline-mode-partition.md` (unchanged from today).

#### Design — live-writer code change (drafted + reverted this session; NOT shipped — see "Why not shipped")

Fully designed and validated (re-derivable from this spec without re-investigation):

1. **UAC** `unified_api_contracts/canonical/partition_paths.py::build_prediction_partition_path` — add an optional
   `canonical_question_group: str = ""` kwarg. When given, returns the bundle path above instead of the per-market
   `{condition_id}.parquet` path (`condition_id`/`data_type` args become don't-cares for the bundle branch). Add a
   module constant `BUNDLED_PREDICTION_DATA_TYPE = "prediction_canonical_question_group"`; export both through
   `unified_api_contracts/gcs_paths.py` (the existing facade `build_prediction_partition_path` is already re-exported
   there and imported by MTDS from there, not from `canonical.*` directly — Citadel import-surface rule).
2. **MTDS** `engine/orchestrator/symbol_rules.py::_build_partition_path_for_asset_group` — new
   `canonical_question_group: str = ""` kwarg; when set (prediction only), delegate to the UAC builder above (a NEW code
   path, unlike the existing prediction/tradfi inline-duplication debt — no reason to duplicate the format string here
   too). Add `_PREDICTION_CQG_BUNDLE_DATA_TYPES = frozenset({"trades"})` next to `_UNDERLYING_PARTITIONED_TYPES`
   (deliberately narrow — see "Scope" above for why `book_snapshot_5` is excluded).
3. **MTDS** `engine/orchestrator/partitioned_writer.py`:
   - `_get_writer(...)` — new `cqg: str = ""` param; when set, key =
     `(instrument_type, BUNDLED_DATA_TYPE, "__cqg__", cqg)` (a 4-tuple, so it can never collide with the existing
     3-tuple per-symbol/per-underlying keys) and the GCS path is built via the UAC bundle branch (`file_name` fixed at
     `"ticks.parquet"`).
   - `write_chunk(...)` — add `cqg = self._resolve_prediction_cqg_bundle_key(dt_str, group_df)`; when non-empty, pass
     `symbol="", file_symbol="", cqg=cqg` to `_get_writer` instead of the per-symbol kwargs (mirrors exactly how
     `options_chain`/`futures_chain` already bundle by `underlying` while each contract's own `symbol` column survives
     as a row value — same mechanism, new bundle key). New helper
     `_resolve_prediction_cqg_bundle_key(dt_str, group_df)`: returns `""` unless
     `self._asset_group == "prediction" and dt_str in _PREDICTION_CQG_BUNDLE_DATA_TYPES and "canonical_question_group" in group_df.columns`
     and the column has a non-null/non-empty value for the group (falls back to per-market on unclassified, rather than
     joining a bogus bundle). `_update_row_and_symbol_counts` / the generic `shard_counts` atom are deliberately LEFT
     UNCHANGED (see residual below).
   - No change needed to `_update_prediction_counts` / `manifest_finalize.py::_finalize_prediction_bundles` — the
     manifest atom is already correct and independent of the object layer.

This was implemented + code-reviewed against the exact `options_chain`/`futures_chain` bundling precedent this session,
then **reverted (`git checkout --` on just these 2 files per repo — confirmed clean, no foreign WIP touched)** before
commit — see "Why not shipped" below. The spec above is complete enough to re-apply directly.

#### Why not shipped this session — the real blocker (READ BEFORE RE-ATTEMPTING)

Cutting the object over to the bundle shape without a companion change breaks the **live PREDICTION candle pipeline** in
`market-data-processing-service` (MDPS), a DIFFERENT repo, silently:

- `market_data_processing_service/app/core/orchestration_scanner.py::_blob_matches_data_type_partition` (line ~248)
  matches raw shard blobs by the literal substring `f"data_type={data_type}/"` — for prediction "trades" candles this
  means it looks for `data_type=trades/` in the blob name. After cutover, NEW days' trades data lands under
  `data_type=prediction_canonical_question_group/` instead — the scanner finds 0 blobs → MDPS silently stops building
  prediction OHLCV candles for every day after cutover. **The exact same equivalence-map mechanism this file already has
  for DeFi** (`_DEFI_DEX_DATA_TYPE_ONDISK_SEGMENTS`, used by `_blob_matches_data_type_partition`/
  `_data_type_requires_partition` for the dex_pools/dex_swaps on-disk-vs-logical data_type collapse) is the right
  template to extend for prediction (`"trades" → ["prediction_canonical_question_group", "trades"]` on-disk segments).
- `market_data_processing_service/app/core/dependency_checker.py::check_upstream_data_per_shard` (line ~552) does its
  own independent raw `list_blobs` + substring match on `data_type={data_type}/` — same failure mode. Used by
  `cli/handlers/process_handler.py::_filter_shards_by_per_shard_check` (opt-in via `--per-shard-check`, NOT confirmed
  whether the live prediction MDPS cron passes that flag — VERIFY before assuming it's inert).
- `market_data_processing_service/app/adapters/prediction/trades_adapter.py` (`PredictionTradesAdapter`) — encouraging
  finding: its own docstring says "Polymarket ticks.parquet contains multiple condition_ids (instruments) in one file.
  The orchestrator detects this via the instrument_key column which this adapter adds from condition_id" — i.e. the
  candle adapter ALREADY expects to receive a multi-instrument combined frame with a derived `instrument_key`, which is
  compatible with (maybe even written in anticipation of) the bundle shape. This piece may need **zero** changes —
  VERIFY by reading how `orchestration_scanner.py` hands the scanned+concatenated frame to this adapter today.

Per the task's own contract ("if the live path needs a code change… ships FIRST, else the migration chases a moving
target") and the workspace's data-pipeline-correctness HARD RULE (no regressions), shipping the MTDS-only half now would
have silently broken live candle production — so it was reverted rather than shipped half-done. **Clean boundary**:
MTDS+UAC diff is fully specified above; the missing companion piece is scoped to 2-3 functions in 2 files in MDPS
(`orchestration_scanner.py`, `dependency_checker.py`) + one VERIFY read (`trades_adapter.py`) — small enough for a
single follow-up session to design+ship all three repos together, QG'd, before touching any object.

#### Historical rollup — reuse `rebuild_prediction_manifest.py`'s classify/atom logic (NOT built this session)

`market-tick-data-service/market_tick_data_service/scripts/rebuild_prediction_manifest.py` already contains the EXACT
classify-and-bundle logic needed (battle-tested, unit-tested): `compute_object_atom()` re-classifies each per-market
object's rows via UAC `classify_polymarket_to_canonical_group`/`classify_kalshi_to_canonical_group`, groups by
`(date, venue, cqg)`, and currently only EMITS A MANIFEST ROW per bundle (`record_captured_from_counts`). The historical
migration script is a SIBLING tool that reuses `parse_canonical_prediction_path` / `compute_object_atom` /
`merge_object_into_aggregate` verbatim but, instead of (or in addition to) `emit_manifest_rows`, **concatenates the real
per-object DataFrames per `(date, venue, cqg)` group and writes ONE physical parquet** to the target path via the new
UAC/MTDS builder above — CF-11 honest-absence rules (0-row → failed, missing envelope → failed,
`ClassifierConfidenceLow` → failed, never a bogus bundle) carry over unchanged. Row-parity invariant for the SMOKE step:
`sum(per-market object row counts for a (day,venue,cqg)) == rollup file row count`. Perf-contract unchanged
(`ThreadPoolExecutor`, `--start-date`/`--end-date`/`--workers`, per-object `try/except…continue`, idempotent). Launch
via `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` (existing registered launcher family) once the
live-writer companion change (above) has shipped + been running for at least one full day (so the rollup script's date
range never overlaps a still-in-flight per-market-only day).

#### Phased next steps (in order — each gates the next)

- [ ] [CODE] P0. Ship the MTDS+UAC live-writer bundle change (spec above) TOGETHER WITH the MDPS companion change
      (`orchestration_scanner.py` data_type-equivalence map extension + `dependency_checker.py` per-shard-gate update +
      VERIFY `trades_adapter.py` needs no change) as ONE coordinated cross-repo QG+quickmerge — 3 repos
      (unified-api-contracts, market-tick-data-service, market-data-processing-service), each gated green independently
      per the "commit is the quality boundary" rule. Verify in a live/paper run (not just unit tests) that a NEW day's
      prediction trades still produce candles post-cutover before calling this done.
- [ ] [DATA] P1. Build the historical rollup migration script (reuse `rebuild_prediction_manifest.py` logic, spec above)
      with `--dry-run` first; smoke-test on 1 day × 1 venue against real GCS data verifying the row-parity invariant,
      then a small multi-day/multi-venue dry-run sample.
- [ ] [DATA] P1. Pre-migration drain (stop prediction writers/crons per the HARD RULE) → snapshot `_index` →
      registered-launcher VM walk (SPOT, per-VM date shards, no-fire-and-forget) rewriting the
      `trades`/`prediction_trades` corpus into per-(cqg,day) rollup files, `--apply` only after a full dry-run plan
      review → resume writers.
- [ ] [DATA] P1. Post-verify: CF-audit the pred surface (row-parity per (day,venue,cqg) sampled; manifest cross-check
      against the ALREADY-correct bundle atom — should now match 1:1 with real objects instead of being ahead of them);
      confirm deployment-ui prediction drilldown reads the new shape (cross-ref
      `predictions_other_bucket_and_ui_drilldown_2026_06_20.md`).
- [ ] [DATA] P2. Only after content-verified closure (sports-template content-aware verifier, snapshot-first): delete
      the superseded per-market `trades`/`prediction_trades` objects. Journal every step in THIS section's Progress Log
      (below), not a new plan.

**Progress Log (this section)**:

- **2026-07-13** — Design session. Confirmed legacy buckets 404 (no migration input there); confirmed no in-flight
  conflicting prediction migration VM; confirmed current `pred-prd` shape is still per-market (0 objects at
  `data_type=prediction_canonical_question_group` anywhere sampled); confirmed the manifest already emits the cqg-bundle
  atom (17,329 captured cells) ahead of the object layer. Drafted + validated the full MTDS+UAC write-path code change
  (options_chain/futures_chain bundling precedent), then discovered mid-implementation that MDPS's
  `orchestration_scanner.py`/`dependency_checker.py` raw-blob scanners hardcode `data_type={requested}/` substring
  matching for the raw shard discovery feeding live prediction candle-building — shipping the writer change alone would
  silently stop prediction OHLCV candle production for every day after cutover. Reverted the MTDS+UAC edits (clean
  `git checkout --` on only the 2 files per repo I'd touched; confirmed no foreign WIP disturbed) rather than ship a
  partial cross-repo change into a live data pipeline. Full spec + exact file:line references captured above so the next
  session implements directly instead of re-diagnosing. Fresh-audit correction folded in: 573,451 was the pre-copy-walk
  legacy count (bucket now gone); current `pred-prd` total is 5.42M objects across all data_types, of which only the
  `trades`/`prediction_trades` subset is this migration's physical-rollup scope.

- [x] ✅ [CODE] P1. **CLOSED — na-eligibility-audit 2026-08-06 (prediction tranche). RESOLVED/NO-ACTION, same finding
      already ruled in the sibling cefi doc.** FLAG-3 (deployment-api) — DECIDED (operator 2026-06-02): env-tier the
      `*-store` buckets, `-prd` initial. **Superseding ruling**: `data_completion_cefi_2026_07_15.md:180-193`
      ("deployment-api FLAG-3 — RESOLVED/NO-ACTION (main ruling 2026-07-28)") — the exact same call sites
      (`commentary/pipeline_uat.py:167/181/195/211` + `deployment_api_config.py:547`), same
      `downstream_services_manifest_canonicalisation_2026_06_01.md` MIGRATED-FROM provenance. Main's later ruling
      (2026-07-28) found this is NOT a mechanical f-string→`resolve_bucket_name` swap: those reads are non-AG
      **pipeline-health summary** buckets (`# CORRECT-LOCAL`, a deliberate QG STEP-5.69 allowlist), not the AG-scoped
      market-data stores `resolve_bucket_name(asset_group=…)` resolves — swapping them would point health reads at
      wrong/nonexistent buckets. Ruling: keep `# CORRECT-LOCAL` AS-IS, no code change; `deployment_api_config.py` store
      buckets already use typed `effective_*` config (FLAG-3-compliant). This prediction-doc copy of the finding
      predates that ruling and never got its checkbox flipped to cite it — closing now, no work dropped (the ruling
      already covers this call site set in full).

- [ ] [DATA] P0. Per-AG (cefi/tradfi/prediction): Phase-0 layout audit → re-tarball+pin SHAs → **G1 full-corpus
      dry-run** (`launch-canonical-migration-vm.sh <ag> <start> <end> dry`; confirm `TOTAL planned` ≈ full-corpus object
      count) → writer drain + `_index` snapshot → `--apply` additive copy → **E5 rebuild RUN** → CF-1…CF-12 verify →
      completeness COUNT gate → strategically-sampled cross-shard verify → fleet drain → **DELETE legacy (END-only,
      irreversible)**. Home: each AG plan §C/§E + `cf_data_state_audit_slot3_2026_06_01.md` GATES G1–G8. (E6 CF-7
      relabel + E7 verify + E8 delete ride here.) **(MIGRATED FROM:
      `downstream_services_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. Downstream service C-walks (MDPS rides the AG tick walk; features/strategy/execution =
      writer-fix-first, re-audit when input C-GREEN + first batch runs). Home: this plan § C. **(MIGRATED FROM:
      `downstream_services_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] [CODE] P1. **CLOSED 2026-07-30 (na-eligibility-audit, prediction tranche) — EXACT DUPLICATE of the "FLAG-3
      (deployment-api)" item earlier in this section, no work dropped.** Same operator decision (2026-06-02, env-tier
      the `*-store` buckets, `-prd` initial), same call sites (`commentary/pipeline_uat.py:167/181/195/211` +
      `deployment_api_config.py:547`), same prereq (bucket-SSOT owner registers the env-tiered names in
      `cloud-providers.yaml`), same repo, and the same
      `(MIGRATED FROM: downstream_services_manifest_canonicalisation_2026_06_01.md, 2026-07-13)` provenance — the
      consolidation folded this one finding in twice under two spellings of its own name ("FLAG-3" and "FLAG 3").
      Closing the duplicate only; the surviving copy above still carries the full work item, so nothing becomes
      untracked by this close.

- [x] ✅ [CODE] P2. **CLOSED — na-eligibility-audit 2026-08-06 (prediction tranche). Stale premise; never this plan's
      scope, and already resolved elsewhere.** FLAG 2 (DEFI scope → slot-2 / bucket_name_ssot):
      `_BUCKET_CATEGORY_OVERRIDES` (data_status_service.py:2902) hardcoded 6 DeFi sub-buckets bypassing
      `resolve_bucket_name`. Item's own text already said "Not in another AG slice's scope" and redirected to
      `defi_manifest_canonicalisation_2026_06_01.md` §H — that redirect target is now ARCHIVED (superseded_by
      `data_completion_to_100_all_ag_2026_06_21`). The live copy of this finding,
      `data_completion_defi_2026_07_15.md:363-368`, is already `[x]` CLOSED: **"na-eligibility-audit 2026-08-01: CLOSED
      — stale premise, root cause found + fixed elsewhere"** — `deployment-api`'s DeFi sub-bucket-fold machinery
      (`_BUCKET_CATEGORY_OVERRIDES`/`_MTDS_DEFI_SUB_DIMENSIONS` in `services/data_status/defi.py`) is now empty, every
      DeFi sub-bucket ever created has been consolidated into the single shared bucket, shipped
      `deployment-api@f919c87`. Independently reconfirmed active/dispatched at
      `defi_satellite_ao_dispatch_batch3_2026_07_26.md:427` (`assigned_vm: planning`). Closing this stale copy; nothing
      left untracked.

- [ ] [CODE] P2. **GAP-4 (all consumers): ASSERT v9 schema columns on manifest read.** `read_availability_index`
      backfills missing v9 cols as NULL on a v8 manifest → consumers silently read NULL
      `asset_group`/`pipeline_mode`/`source`. Add a `schema_version`/`asset_group`-present assertion (or
      `assert_consolidator_healthy`) in `manifest_window_guard`
      (features-service@`features_service/common/manifest_window_guard.py:85` — after `read_availability_index`),
      `manifest_allocation_guard` (strategy-service@`strategy_service/manifest_allocation_guard.py`), MDPS
      `dependency_checker` so a non-v9 upstream is caught loud, not silently consumed. **⚠️ DESIGN NUANCE (slot-3
      2026-06-02 — why deferred, not shipped half-baked):** the prod corpus is **100% v8 TODAY** (pre-migration), so a
      hard `schema_version==9` assert would break EVERY consumer immediately, and an unconditional warn would fire on
      100% of reads (pure noise). Ship it as a **loud WARN that fires only on MIXED-version drift** (some rows v9, some
      not, within one read) OR an `asset_group`-column-absent-on-a-supposedly-migrated-bucket signal — the real
      post-migration regression — NOT a blanket "not v9" warn. Becomes a hard assert only AFTER each AG's G3 migration
      flips its corpus to v9. P2 + warn-only → low value pre-migration; real value is the post-migration regression
      catch. (slot-3 2026-06-02: deferred under context budget with this design spec so the next agent ships the
      non-noisy form.) **(MIGRATED FROM: `downstream_services_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per
      MTDS consolidation ruling.)**

- [ ] [DATA] P1. **MDPS** C-walk: bundle any `processed_candles/` debt into the SAME AG tick-bucket walk (no second walk
      on an AG `_index` — single-walk discipline); ensure CF-4 source PROPAGATION + CF-1/2/3/5/8 land there. **(MIGRATED
      FROM: `downstream_services_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. **features** C-walk: ONE bundled walk per `features-*-{ag}` index for any P0 debt (v9 +
      `asset_group=` + `pipeline_mode=` partition + typed reasons + `available_at`); CF-4 stays exempt. **(MIGRATED
      FROM: `downstream_services_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. **strategy** C-walk: ONE bundled walk for strategy output `_index` debt (v9 + `asset_group=` + typed
      reasons + `available_at`). Small corpus → likely local, fast. **(MIGRATED FROM:
      `downstream_services_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. **execution** C-walk: ONE bundled walk for execution-record/ledger `_index` debt (same set). Small
      corpus → likely local, fast. **(MIGRATED FROM: `downstream_services_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. Post-walk per service: re-run the P0 CF audit → all applicable CF GREEN (data-state). Each service's
      canonical-form section in its audit-instruction file goes GREEN. Hands C-GREEN to `bucket_name_ssot…` L6 for any
      downstream legacy buckets. **(MIGRATED FROM: `downstream_services_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

## Progress Log

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid (+2 stale duplicate items closed) — P0
  cross-repo object-layer migration whose remaining work is a pre-migration writer drain, a registered-launcher VM walk,
  and a gated prod-object delete; `/ag-closeout-audit` has independently re-triaged this doc's Phase-B CQG-bundle
  migration to "0 AO-eligible, needs its own dedicated plan" across FOUR separate passes (batch1/2/3/4, re-confirmed by
  batch6 2026-07-29). Not re-litigated. Two exact-duplicate checkboxes introduced by the 2026-07-13 MTDS-consolidation
  migration were closed with evidence (the second `grain_for_instrument_type` copy and the second `FLAG 3`
  deployment-api copy) — 23 open todos -> 21, no tracked work dropped.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: re-verified context_scope, no change needed (5 entries) --
  `rebuild_prediction_manifest.py` (cited twice in-body, the manifest-rebuild script this plan's todos operate on)
  remains the correct source target alongside the M-1 coordinator + the 3 pipeline/bucket/manifest codex SSOTs.
- **na-eligibility-audit 2026-08-06 (prediction tranche, autonomous)**: KEEP-NA, valid for 19/21 open items (P0
  cross-repo CQG-bundle object-layer migration + downstream C-walks — genuinely design/VM/delete-gated, consistent with
  the 2026-07-30 audit and 4-5 independent ag-closeout-audit "0 AO-eligible" passes, not re-litigated). 2 items closed
  as KEEP-NA-STALE (FLAG-3 deployment-api, FLAG-2 DeFi `_BUCKET_CATEGORY_OVERRIDES`) — both stale copies of findings
  already resolved/closed in sibling AG docs (`data_completion_cefi_2026_07_15.md`, `data_completion_defi_2026_07_15.md`
  respectively) that never had their checkbox flipped here. 21 open todos -> 19, no tracked work dropped.
- **context-scout 2026-08-07**: re-verified context_scope, no change needed (5 entries) -- M-1 coordinator, 3
  pipeline/bucket/manifest codex SSOTs, and `rebuild_prediction_manifest.py` remain accurate.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 19 open items, matches the 2026-08-06 count; consistent with 3
  prior audit passes and 4-5 `/ag-closeout-audit` "0 AO-eligible" rulings on the Phase-B CQG-bundle migration. No change
  in substance.
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (prediction tranche)**: KEEP-NA, valid — re-checked
  against the full round-11 precedent set (IAM self-service default, D16 all-repos carve, S5.1 tiering,
  plan-destination-default-to-AO for auto-filed findings, escalation-N=3-days, reversibility-qualified deletes
  agent-executable after a fresh check, Option B retirement, GSM secret `deepseek-v4-pro-api-key` + 5 Slack webhooks) —
  none bound any of the 19 open items. This is a cross-repo CQG-bundle object-layer migration + 5 downstream-service
  C-walks, gated on a coordinated MTDS+UAC+MDPS writer-code ship, a pre-migration writer drain, a registered-launcher VM
  walk, and a content-verified prod-object delete — genuinely design/VM/delete-shaped, not IAM/tiering/secret-shaped.
  Consistent with 4 prior audit passes and 4-5 independent `/ag-closeout-audit` "0 AO-eligible" rulings. No
  reclassification.
- **na-eligibility-audit 2026-08-10 (prediction tranche)**: KEEP-NA-STALE-ITEM — closed 1 of 19 open items (C0 "copy
  legacy objects" walk, this doc's own line-133 "supersedes"/operator-ruling text confirms the legacy bucket is
  404/version-purged and the copy already ran as E4 2026-06-29 — a "later dated section overrides an earlier checkmark"
  case, not fresh work). 19 -> 18 open. Remaining 18 items re-confirmed genuinely NA (design/VM/delete-gated cross-repo
  CQG-bundle migration + downstream C-walks), consistent with 5 prior audit passes. No RECLASSIFY candidates. Sibling
  rider items (pipeline_mode/source riders, post-walk comparison, CF-7 relabel) deliberately left open pending a closer
  per-item read — see this doc's Phase-1 classification detail in the 2026-08-10 prediction- tranche
  na-eligibility-audit run report.
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (5 entries) -- recent passes closed 1 stale
  checkbox (C0 copy-walk, superseded by E4) and re-confirmed the RECLASSIFY verdict, no new source/codex reference
  introduced; M-1 coordinator, 3 pipeline/bucket/manifest codex SSOTs, and `rebuild_prediction_manifest.py` remain
  accurate.
