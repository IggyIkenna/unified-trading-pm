---
doc_type: issue
title:
  "POLYMARKET raw-tick data lives in ≥4 structurally-distinct, oracle-blind path trees for the same shard —
  content-verified identical trades, but the abandoned legacy tree carries richer metadata (title/slug/eventSlug) the
  canonical schema drops"
summary: >-
  Four-surface reconciliation of asset_group=prediction (raw-tick layer,
  market-data-tick-pred-prd-central-element-323112) found that for a sampled (day=2025-04-11, venue=POLYMARKET) cell,
  the SAME 500-row trade batch for one condition_id exists as content-VERIFIED-identical (same
  transactionHash/timestamp/price values) parquet objects under FOUR different path shapes: (1) the canonical
  flat-per-contract shape (instrument_type=prediction_market/data_type=trades/{cid}.parquet, 22 columns), (2) a
  byte-adjacent DOUBLE-NAMED sibling inside that SAME canonical directory (POLYMARKET:PREDICTION_MARKET:{cid}.parquet,
  100% overlap in a 79-condition_id sample), (3) a bundle-per-underlying legacy tree carrying an unregistered
  chain=POLYGON segment and a non-canonical data_type=prediction_trades value (registered nowhere in UAC
  DATA_TYPES_BY_ASSET_GROUP['prediction']), and (4) a DEEPLY non-canonical 10-segment tree
  (data_source=POLYMARKET_CLOB/.../market_category=/underlying=/market_type=/resolution_period=/data_type=trades/{cid}.parquet,
  24 columns) that is entirely INVISIBLE to the manifest schema (no
  data_source/market_category/market_type/resolution_period columns exist in the availability_index.parquet schema at
  all -- S3 can never represent these objects). The UAC machine oracle (canonical_path_violations,
  require_pipeline_mode=True) returns CANONICAL (0 violations) for ALL FOUR shapes -- a live,
  previously-undocumented-for-prediction instance of the oracle's structure-vs-value-form blindness (already documented
  for CeFi in canonical_path_oracle_blind_to_filename_stem_2026_07_20.md). Content-verify (mandatory per the
  delete-safety protocol) shows shape (4)'s schema carries title/slug/eventSlug human-readable market-question fields
  and a raw unix timestamp the canonical schema (1) does NOT carry, plus a diverging derived resolution_period value
  (monthly vs event) for the byte-identical trade -- so this is not simple duplication, it is a schema regression risk:
  deleting the legacy tree without confirming those fields survive elsewhere (e.g. instruments-service catalog.parquet
  question text) would be a genuine metadata loss. Separately, the manifest's data_type=prediction_trades axis (2,477
  rows, 100% capture_status=captured, 100% blank instrument_id, most recently written 2026-07-23 -- 2 days before this
  audit) is a genuine non_canonical_axis_value finding not covered by any migration_pending suppression rule in the
  cutover register. Read-only diagnosis; no GCS/manifest writes made.
status: resolved
nature: issue
asset_group: [prediction]
stage: [data]
repos:
  [unified-trading-pm, unified-api-contracts, unified-trading-library, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags:
  [
    data-correctness,
    prediction,
    polymarket,
    canonicalisation,
    machine-oracle,
    false-clean,
    legacy-duplicate,
    metadata-loss,
    reconciliation,
    operator-notify,
  ]
related:
  [
    plans/audit/results/data_pipeline_reconciliation_prediction_2026_07_24.md,
    plans/audit/results/data_pipeline_reconciliation_prediction_2026_07_20.md,
    plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md,
    plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/reconciliation-finding-taxonomy.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/non-canonical-path-inventory.md,
  ]
created: 2026-07-24
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
source:
  [
    /data-pipeline-reconciliation --asset-group prediction --layer raw-tick,
    2026-07-24/25,
    read-only against prod GCS central-element-323112 (market-data-tick-pred-prd-central-element-323112),
  ]
resolved_by:
  ACKED-INTO-PLAN. Schema extension + writer fix shipped (unified-api-contracts@90ddcc01 added title/slug/event_slug as
  first-class canonical `trades` ColumnSpec entries; market-tick-data-service@84154e1a stopped the writer dropping them
  at ingest); both registered in codex/02-data/canonical-cutover-register.md §6e +
  codex/02-data/non-canonical-path-inventory.md row 22. The still-open historical raw-object migration (shapes #3/#3b/#4,
  explicitly registered `no-migrate-first`, not yet done) is absorbed by the still-active
  /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md (todo 4b) -- not lost, tracked there.
locked_by:
estimate_class: research
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

> **🟢 RESOLVED 2026-07-28 (ACKED-INTO-PLAN)** — schema extension + writer fix shipped; the still-open historical
> migration is absorbed by `/plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md` (see `resolved_by`
> above). Archived per `/codex/11-project-management/issue-doc-lifecycle.md`.

# POLYMARKET legacy dual-write path trees + oracle-blind non-canonical estate (prediction raw-tick)

> Surfaced by `/data-pipeline-reconciliation --asset-group prediction` (raw-tick layer), 2026-07-24/25, read-only
> against prod GCS `market-data-tick-pred-prd-central-element-323112`. Escalated per the workspace's
> data-correctness/cross-repo/SSOT-contradiction big-finding rule. No prod GCS or manifest writes were made producing
> this doc; all evidence below is from `gcs_describe_object`/`list_blobs` reads and direct parquet reads.

## What I found (evidence, not inference)

Sampled cell: `day=2025-04-11`, `venue=POLYMARKET`, `pipeline_mode=batch_polymarket_clob`. Four structurally-distinct
GCS path shapes hold data for the SAME logical shard:

| #   | Shape                                                                  | Example path (tail)                                                                                                                                                                                                       | Objects this date                         | Columns | Oracle verdict (`require_pipeline_mode=True`)                          |
| --- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ------- | ---------------------------------------------------------------------- |
| 1   | **Canonical target**                                                   | `.../venue=POLYMARKET/instrument_type=prediction_market/data_type=trades/{cid}.parquet`                                                                                                                                   | 158 (79 cids × 2 naming forms, see #2)    | 22      | CANONICAL (0 violations)                                               |
| 2   | **Double-named sibling, SAME directory as #1**                         | `.../data_type=trades/POLYMARKET:PREDICTION_MARKET:{cid}.parquet`                                                                                                                                                         | (counted inside the 158 above)            | 22      | CANONICAL (0 violations) — oracle drops the filename before validating |
| 3   | **Bundle-per-underlying legacy, `chain=` + non-canonical `data_type`** | `.../venue=POLYMARKET/chain=POLYGON/instrument_type=prediction_market/data_type=prediction_trades/underlying={U}/ticks_migrated_*.parquet`                                                                                | 3 (BTC/ETH/OTHER)                         | bundle  | CANONICAL (0 violations)                                               |
| 3b  | **Same bundle, `instrument_type=` overloaded with base-asset**         | `.../venue=POLYMARKET/instrument_type={BTC\|ETH\|OTHER}/data_type=prediction_trades/ticks_migrated_*.parquet`                                                                                                             | 3                                         | bundle  | CANONICAL (0 violations)                                               |
| 4   | **Deep 10-segment unregistered tree**                                  | `.../data_source=POLYMARKET_CLOB/venue=POLYMARKET/chain=POLYGON/market_category={cat}/underlying={U}/market_type={t}/resolution_period={p}/data_type=trades/{cid}[.parquet\| POLYMARKET:PREDICTION_MARKET:{cid}.parquet]` | **158** — exact match to shape #1's count | 24      | CANONICAL (0 violations)                                               |

**The oracle (`unified_api_contracts.canonical.partition_paths.canonical_path_violations`) returns an EMPTY violation
list — i.e. "CANONICAL" — for all five rows above**, including shape #4's 10-segment tree carrying axes (`data_source=`,
`market_category=`, `market_type=`, `resolution_period=`) that appear NOWHERE in the canonical prediction grammar
(`cross-asset-canonical-target-ssot.md` §1/§8) and NOWHERE in the manifest schema (the `availability_index.parquet` for
this bucket has 40 columns; none of those four names is one of them — see the schema dump in the sibling audit report).
This is the oracle's documented structure-vs-value-form blindness
(`canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`), previously measured only for CeFi; this is the first
concrete measurement of the SAME blind spot for prediction, and it is worse here because the extra axes aren't even axes
the oracle's clauses check for ANY asset_group — they're simply unknown key=value hive segments the "every subsequent
segment must be key=value" clause happily accepts.

### Content-verify (the mandatory step before any duplicate/delete framing)

Per `gcs-and-manifest-delete-safety-protocol.md`, existence/path-shape similarity is not evidence of duplication —
content must be read. Read both parquets for
`condition_id=0x7ed4abfdcfd6f80808a69c6b6e988374c2940de32ef1ce3c60d2a90d11a888b8` (day=2025-04-11):

- **Same underlying trades**: both files hold 500 rows; row 0 in both has identical `transactionHash`
  (`0x918b7ac5903cfb173c970322898d050f472bf3a1c7d4f6999d23206e4af17dd6`), identical `timestamp` (2025-04-11T18:50:19Z /
  unix `1744397419`), identical `amount`/`size` (1000.0), identical `price` (0.001) — this IS the same trade, captured
  twice under two different writers/schemas.
- **Schema #1 (canonical, 22 cols)**: `amount`, `instrument_id` (full composite `POLYMARKET:PREDICTION_MARKET:{cid}`),
  `canonical_question_group=OTHER`, `asset_group`, `resolution_period=event`. No `title`/`slug`/`eventSlug`.
- **Schema #4 (legacy 10-segment tree, 24 cols)**: `size` (not `amount`), `title="Bitcoin above $84,000 on April 11?"`,
  `slug`/`eventSlug` (human-readable market identifiers), raw unix `timestamp` + a separate `ts_event`,
  `market_category=CRYPTO_PRICE`, **`resolution_period=monthly`** — diverges from schema #1's `resolution_period=event`
  for the byte-identical trade. No `instrument_id` column at all.

**This is not simple duplication.** The legacy tree (#4) carries market-question text (`title`/`slug`/`eventSlug`) that
the canonical schema drops entirely, and the two schemas disagree on a derived classification field
(`resolution_period`) for the same trade. A `legacy_duplicate` delete suggestion on shape #4 would be premature and is
explicitly **NOT** made here — see Open questions below.

### The manifest-registered non-canonical axis (separate from the four path shapes)

`data_type=prediction_trades` — **2,477 manifest rows**, 100% `capture_status=captured`, 100% blank `instrument_id`,
`schema_version=9` (current, not a legacy schema marker), most recently `written_at 2026-07-23T05:11Z` (2 days before
this audit). This value is **absent from
`unified_api_contracts.registry.market_data_categories.DATA_TYPES_BY_ASSET_GROUP['prediction']`**
(`= ['trades', 'book_snapshot_5', 'prediction_canonical_question_group', 'market_lifecycle', 'MARKET_LIFECYCLE']`) and
is **not covered by any axis in `canonical-cutover-register.md`** — it is not a `migration_pending` suppression
candidate, it is a live `non_canonical_axis_value` (S3) in agreement with the matching non-canonical S1 shapes #3/#3b.
348 distinct dates, 100% date-overlap with the true `prediction_canonical_question_group` bundle rows for the same
venue.

## Why this is a big finding (not a routine drift item)

1. **Data-correctness**: a downstream reader trusting "oracle says canonical" for prediction (exactly the workspace's
   own stated HARD RULE for judging canonicality) would certify all five shapes above as fine — none would ever surface
   without the value-level census this audit ran ad hoc.
2. **Metadata-loss risk**: the legacy tree is not junk — it carries fields the canonical schema does not. Any cleanup
   plan that treats path-shape non-canonicality as sufficient grounds for deletion would destroy the only surviving copy
   of `title`/`slug`/`eventSlug` for these markets, unless those fields are proven to survive elsewhere (the
   `instruments-service` `InstrumentRecord.question` backfill is a candidate but was NOT checked in this pass).
3. **Cross-repo**: touches `unified-api-contracts` (the oracle + `DATA_TYPES_BY_ASSET_GROUP`),
   `market-tick-data-service` (the writer(s) that produced shapes #3/#3b/#4 — filenames stamped
   `ticks_migrated_20260419T101933Z.parquet` strongly suggest a 2026-04-19 migration script, not the live writer, but
   this was not traced to a specific script/commit in this read-only pass), and potentially `instruments-service` (if
   `title`/`slug`/`eventSlug` needs to be recovered into the reference-data catalogue).
4. **Scale is a LOWER BOUND**: this was measured on ONE (day, venue) cell via prefix-scoped listing (single-walk-exempt
   per the reconciliation skill's no-walk routes). The manifest's `prediction_trades` axis alone spans 348 distinct
   dates (shapes #3/#3b's likely footprint); shape #4 has ZERO manifest representation, so its true corpus-wide extent
   is UNKNOWN without a Tier-2 SPOT-VM single walk.

## What I did NOT do (explicitly, so this isn't mistaken for a completed fix)

- No GCS object was deleted, moved, or copied.
- No manifest row was written or modified.
- No corpus-wide walk was run (single-walk discipline — this is a targeted, prefix-scoped sample per the skill's
  sanctioned no-walk routes).
- No attempt was made to trace which specific writer/script produced shapes #3/#3b/#4, or to confirm/deny whether
  `title`/`slug`/`eventSlug` are preserved anywhere downstream.

## Open questions (for the operator / the owning plan, not resolved here)

1. **Q1 — is `title`/`slug`/`eventSlug` preserved anywhere in the canonical estate today?** If yes (e.g. IS
   `catalog.parquet` `question` column, per `deployment_api/services/prediction_catalogue.py`'s docstring reference to
   `InstrumentRecord.question`), the legacy tree may be safely deletable after a content-verified copy check. If no, a
   migration path needs to be designed BEFORE any delete suggestion can rise above `no-migrate-first`.
2. **Q2 — is the deep 10-segment tree (#4) still being WRITTEN, or is it fully historical?** The sampled objects carry
   no obvious timestamp-in-filename; `grep-then-READ` on the MTDS Polymarket adapter/migration scripts was not done in
   this pass. If still live, this is an active writer defect (P0); if historical-only, it's a migration cleanup item
   (P2).
3. **Q3 — should `DATA_TYPES_BY_ASSET_GROUP['prediction']` register `prediction_trades` retroactively (if it turns out
   to be an intentional pre-Plan-A shape), or should the ~2,477 manifest rows be migrated/purged?** Given the codex's
   own "Predictions migration (Plan A)" section describes the PRE-Plan-A shape as `data_type=<base_asset>` (e.g. literal
   `data_type=BTC`), not `data_type=prediction_trades` with `underlying=BTC` as a row column — the `prediction_trades`
   value does not even match the documented legacy shape. This may be a THIRD, previously undocumented shard-grain
   variant.

   **✅ RESOLVED 2026-07-25 (operator ruling, asked directly in-session).** Investigated first (operator asked: which
   service owns it, what's the schema, what canonicals could it migrate to, own-or-market trades) before ruling:
   - **Owner**: `market-tick-data-service` — confirmed via `source=polymarket_clob` column + the
     `ticks_migrated_20260419T101933Z.parquet` filename (a 2026-04-19 migration/backfill script within MTDS, not the
     live writer, not `instruments-service` — IS holds reference/catalog data only, never raw ticks).
   - **Schema (directly read, day=2025-04-11/underlying=BTC sample, 500 rows)**:
     `proxy_wallet, side, asset, conditionId, size, price, timestamp, title, slug, icon, event_slug, outcome, outcome_index, name, pseudonym, bio, profile_image, profile_image_optimized, transaction_hash, condition_id, data_type, instrument_type, underlying, available_at, source`
     — 25 columns. Confirms + extends the doc's earlier schema-#4 finding: this shape ALSO carries the trader-identity
     fields (`name`/`pseudonym`/`bio`/`profile_image`) and outcome labels (`outcome`/`outcome_index`) that schema #4's
     comparison didn't test for.
   - **Own or market trades?** **Market trades, unambiguously.** `proxy_wallet`/`name`/`pseudonym`/`bio`/
     `profile_image` are the COUNTERPARTY's public Polymarket profile fields (different per row, i.e. per distinct
     trader) — this is a public CLOB trade-tape capture (other participants' executed trades), not the trading system's
     own orders/positions. Same pattern as any CeFi trade-tape capture.
   - **Canonicals it could migrate to**: the natural target is the canonical `data_type=trades` flat-per-contract shape
     (#1/#2 above) — but that schema is only
     `amount, instrument_id, canonical_question_group, asset_group, resolution_period` (5 cols). A straight migration
     would silently drop the trader-identity fields, the market-question text (`title`/`slug`/`event_slug`), and the
     outcome labels — none of which exist anywhere else in the canonical corpus (Q1, whether IS's catalogue backfills
     `title`/`slug`/`eventSlug`, is STILL open, separate from this ruling).
   - **Operator ruling: extend the canonical `trades` schema to preserve these fields, then migrate without loss** —
     rejected both "migrate + accept the loss" (metadata is valuable, not proven redundant) and "register as a permanent
     separate canonical variant" (grows the canonical grammar unnecessarily when the real fix is closing a schema gap).
     This is now real cross-repo schema-evolution work, not a quick fix — see updated Todos below.

## Todos

- [x] [CODE] P1. Grep-then-READ the MTDS Polymarket adapter + `rebuild_prediction_manifest.py` (and any
      `*migrat*2026_04_19*` script) to identify which writer/script produced shapes #3/#3b/#4 and whether any is still
      live. Repo: `market-tick-data-service`. Gate: a named commit/script + a live-vs-historical verdict. — already
      covered by plans/active/prediction_satellite_ao_dispatch_batch1_2026_07_25.md (see that doc for execution).
- [x] [CODE] P1. Confirm whether `title`/`slug`/`eventSlug` (or equivalent human-readable market text) is recoverable
      from `instruments-service`'s `prod/catalog.parquet` (`InstrumentRecord.question`) for the condition_ids sampled
      here, before any delete suggestion is entertained for shape #4. Repo: `instruments-service`. — already covered by
      plans/active/prediction_satellite_ao_dispatch_batch1_2026_07_25.md (see that doc for execution).
- [x] ✅ [DATA] P2. Once Q1/Q2 are answered, either (a) register the register-patch stanza in
      `non-canonical-path-inventory.md` with a real disposition, or (b) design a migration that folds shape #4's extra
      metadata into the canonical schema before any legacy-tree cleanup. Repo: `unified-trading-pm` +
      `unified-api-contracts` (schema) + `market-tick-data-service` (writer). — **DONE, option (b).** Per the Q3
      operator ruling (2026-07-25) recorded below, the schema was extended rather than dropped or permanently forked:
      `unified-api-contracts@90ddcc01` added `title`/`slug`/`event_slug` as first-class canonical `trades` `ColumnSpec`
      entries; `market-tick-data-service@84154e1a` stopped the Polymarket writer from dropping them at ingest
      (`eventSlug`→`event_slug`/`outcomeIndex`→`outcome_index` canonicalized). Both shipped + QG-green 2026-07-28
      (slot-12, via `plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo "Extend the canonical
      `trades` schema..." 4a). `non-canonical-path-inventory.md` row 22 registers the resulting disposition
      (`no-migrate-first` — migration must precede any legacy-tree delete); see the todo directly below for the
      register-side confirmation.
- [x] [DESIGN] P1. **Design the extended canonical `trades` schema** (Q3 RESOLVED — operator ruling 2026-07-25: extend,
      don't drop or permanently-fork). Decide which of the 25 `prediction_trades` columns become first-class canonical
      fields (at minimum `title`/`slug`/`event_slug`/`outcome`/`outcome_index` — the market-question + resolution
      metadata with no surviving copy elsewhere; trader-identity fields `proxy_wallet`/`name`/`pseudonym`/`bio`/
      `profile_image` need a separate call — privacy/PII-adjacent, confirm they're genuinely needed downstream before
      keeping them canonical) against the current 5-column `trades` schema
      (`amount, instrument_id,     canonical_question_group, asset_group, resolution_period`). Repo:
      `unified-api-contracts`. — already covered by plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md
      (see that doc for execution).
- [x] [CODE] P1. **Update the MTDS Polymarket CLOB writer** to emit the extended schema going forward, and **migrate**
      the 2,477 `data_type=prediction_trades` rows (+ shape #4's 158+ objects, per Q2's live-vs-historical finding) into
      the canonical `data_type=trades` path/shape under the extended schema — copy+verify+delete per the standard
      delete-safety protocol, no data loss. Repo: `market-tick-data-service`, `unified-api-contracts`. — already covered
      by plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md (see that doc for execution).
- [x] ✅ [DATA] P2. Register the extended schema + this migration in `canonical-cutover-register.md` and
      `non-canonical-path-inventory.md` so a future reconciliation pass doesn't re-flag the (now-closed) gap. Repo:
      `unified-trading-pm`. — **DONE, verified 2026-07-28 (already present, not re-added).** Both registers already
      carry the exact disposition this todo asks for: `codex/02-data/canonical-cutover-register.md` § 6e ("prediction
      `trades` schema — POLYMARKET market-question metadata") documents the Q3 ruling, the writer-root fix SHAs, and an
      explicit `effective-from 2026-07-28 (new writes) / NOT migrated (historical)` state table;
      `codex/02-data/non-canonical-path-inventory.md` row 22 documents shapes #3/#3b/#4 with the same disposition
      (`no-migrate-first`), the exact row/date counts, and a pointer to
      `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 4b for the still-open migration. **Not marking this
      gap fully closed** — deliberately, matching the register's own wording: the writer fix is registered as done, but
      the historical raw-object migration (shapes #3/#3b at 55/348 dates, shape #4 corpus-wide extent still unknown) is
      registered as explicitly NOT YET migrated, so a future reconciliation pass won't misread partial progress as
      complete. Both citations re-read fresh this pass, not assumed from an earlier mention.

## Progress log

- 2026-07-24/25: Found during `/data-pipeline-reconciliation --asset-group prediction` (raw-tick layer), read-only.
  Content-verified via direct parquet reads (not just existence/size). Filed per the big-finding rule; not independently
  corroborated by a second session yet.
- 2026-07-25: Q3 asked directly to the operator via interactive chat. Investigated first (this session, read-only —
  resolved the bucket via `resolve_bucket_name(kind='market-data-tick-prediction', ...)`, the dedicated prediction kind,
  not `asset_group='prediction'` on `market-data`) rather than answering from inference: confirmed MTDS ownership, read
  the real 25-column schema off a live sample object, confirmed these are public market trades (not own executions) via
  the trader-identity columns. Operator ruled: extend the canonical schema, don't drop the metadata or leave it
  permanently forked. Todos above rewritten from a generic "register or migrate" placeholder into the actual 3-step
  design→writer/migrate→register sequence this ruling implies.
- 2026-07-27 (`prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todo 5, combined investigation, read-only —
  slot-12): **(a) Named commit/script per path shape + live-vs-historical verdict — ALL THREE (#3/#3b/#4) are
  HISTORICAL, none written by any code path live today:**
  - **Shapes #3/#3b** (bundle-per-underlying, `chain=POLYGON` + non-canonical `data_type=prediction_trades`, or
    `instrument_type={BTC|ETH|OTHER}` overload): this is the Polymarket adapter's ORIGINAL pre-fix output — commit
    `da270f9bbf7bdb8802e4b9bc48be5bd9c4067a66`'s message (2026-04-19 11:03 +0100, "feat(polymarket): re-shard tick data
    to 6-dim canonical layout") explicitly describes finding these as one of "two drifted layouts" already live at that
    time. Commit `ca246a9b27f8d74114d294bb6d16b0eb27064c9f` (2026-04-19 17:51 +0100, "retire prediction_trades alias")
    confirms the Polymarket adapter had ALREADY switched to writing canonical `data_type="trades"` by that date (only
    Kalshi needed the fix in that commit) — grep of the current HEAD's `polymarket_adapter.py`/ `kalshi_adapter.py`
    confirms zero live references to the string `"prediction_trades"` today. Not still live.
  - **Shape #4** (10-segment
    `data_source=POLYMARKET_CLOB/.../market_category=/underlying=/market_type=/ resolution_period=/data_type=trades/{cid}.parquet`):
    produced by the ONE-OFF migration script `market_tick_data_service/scripts/migrate_polymarket_canonical.py`, ADDED
    by commit `da270f9bbf7bdb8802e4b9bc48be5bd9c4067a66` (2026-04-19) as what it believed at the time was the "new
    canonical 6-dim layout." This was later superseded: the ACTUAL final canonical grammar is the flat shape UAC's
    `build_prediction_partition_path` (`unified_api_contracts/canonical/partition_paths.py:376`, docstring "verified
    2026-04-29" against the live adapter + `PartitionedTickWriter`) emits —
    `day=/asset_group=prediction/venue=/instrument_type=/data_type=/ {condition_id}.parquet`, with NO
    `chain=`/`data_source=`/`market_category=`/`underlying=`/`market_type=`/ `resolution_period=` path segments (those
    classifier values are only PARQUET COLUMNS in the canonical file — confirmed live in the current
    `polymarket_adapter.py::_annotate_cid_dataframe`, lines 662-674, which sets `data_type="trades"` and attaches
    `underlying`/`market_type`/`resolution_period`/`canonical_question_group` as DataFrame columns, never as path
    segments). `market_tick_data_service/scripts/rebuild_prediction_manifest.py`'s own header comment (lines 192-213)
    independently documents this same flat shape as the "post-migration canonical layout... verified 2026-06-02," i.e.
    the 6-dim scheme shape #4 represents was abandoned before that date. `migrate_polymarket_canonical.py` itself was
    DELETED by commit `bce12993cd3e75a76ce4150b19040b61add45a05` (2026-06-10, "chore(orphan-wip): inherit prior-session
    migration cleanup") as one of ~15 obsolete one-off migration scripts removed in that sweep. Not still live — no
    writer for this shape exists in the tree today.
  - **The manifest's `data_type=prediction_trades` axis (2,477 rows, `written_at` as recent as 2026-07-23)** is NOT
    evidence of a live writer either — it is a manifest-metadata artifact of REPAIR tooling, not new capture.
    `rebuild_prediction_manifest.py` is a manually-invoked GCS re-walk/repair script (not a cron — no workflow/cron
    reference found anywhere in the repo; ~8 fix commits touching it in the last few weeks confirm it gets run ad hoc by
    agents doing manifest repairs) whose `_LEGACY_PRED_RE` fallback path (line ~314,
    `data_type=kv.get("data_type") or ""`) re-emits a manifest row carrying WHATEVER `data_type=` value is baked into an
    old object's legacy path, verbatim — so a re-walk run around 2026-07-23 touching historical `prediction_trades`
    objects would refresh `written_at` without any new capture event. Corroborating: a dedicated fix-in-progress script,
    `scripts/canonicalize_prediction_manifest_2026_07_18.py` (created 2026-07-18, last touched 2026-07-19), exists
    SPECIFICALLY to fold these `prediction_trades` manifest rows into `trades` — its own checklist item 6 ("VERIFY: a
    fresh read shows 0 `prediction_trades` rows...") is still unchecked, i.e. the migration is real but not yet
    confirmed complete; this is the P2 todo already tracked below, not new scope.
  - **(b) title/slug/eventSlug recoverability from instruments-service's `prod/catalog.parquet`** — MIXED verdict,
    checked against the exact sampled `condition_id=0x7ed4abfdcfd6f80808a69c6b6e988374c2940de32ef1ce3c60d2a90d11a888b8`
    (bucket `instruments-store-pred-prd-central-element-323112`, resolved via the dedicated flat kind
    `instruments-store-prediction` — NOT `instruments-store`/`asset_group=prediction`, which raises `BucketNamingError`;
    see `instruments_service/engine/orchestrator/catalogue.py::resolve_instruments_store_kind`):
    - **Slug: YES, fully recoverable.** The sampled row's `raw_symbol` column = `"bitcoin-above-84000-on-april-11"`
      (matches the legacy tree's `slug`/title in slug form). Corpus-wide over all `venue=POLYMARKET, data_type=trades`
      catalogue rows (1,417,424 rows): `raw_symbol` is **0% NULL** — always populated.
    - **Title/question: NO, not recoverable for the sampled row**, and unreliable corpus-wide. The sampled row's
      `question` column = `None` despite the column existing in the schema and despite a dedicated backfill having been
      attempted (`prod/catalog.20260717T172057Z.questionbackfill.pred.bak.parquet` backup object present in the bucket,
      dated 2026-07-17). Corpus-wide: `question` is **93.2% NULL** (1,321,095 of 1,417,424 POLYMARKET-trades rows) — the
      questionbackfill pass reached only ~6.8% of rows. So a delete-suggestion for shape #4 CANNOT rely on "title
      survives in the catalogue" as a blanket justification; slug alone survives.
    - **eventSlug: NO, not recoverable anywhere.** No `event_slug`/`eventSlug` column exists in the catalogue schema at
      all (confirmed via the full 39-column schema dump) — `market.event_slug` is used only transiently inside
      `classify_polymarket_to_canonical_group()` classification
      (`reference_data/adapters/prediction/polymarket/ parsing.py:105`) and is never persisted to any `InstrumentRecord`
      field.
  - Read-only throughout: no GCS/manifest writes made; `.venv` synced via `uv sync` (instruments-service had none) to
    read the catalogue with `pyarrow.fs.GcsFileSystem` + predicate pushdown (no whole-corpus walk — targeted
    `venue=`/`data_type=` column reads only).
