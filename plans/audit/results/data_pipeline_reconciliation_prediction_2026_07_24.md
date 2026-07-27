---
doc_type: audit-result
title: "Data-pipeline reconciliation — prediction, raw-tick layer (2026-07-24/25)"
summary: >-
  Four-surface canonicalisation reconciliation of asset_group=prediction, raw-tick layer, over the PROD bucket
  market-data-tick-pred-prd-central-element-323112 only (read-only; candles layer explicitly out of scope this
  dispatch). Bucket reachable, manifest index healthy (no lock, latest run success, 0-op incremental). Manifest =
  761,288 rows; reachable_coverage (formula named) = 95.82%, up from 94.63% on the 2026-07-20 prior run over the same
  AG. HEADLINE FINDING (filed as a big-finding issue doc, operator-notify): a targeted, content-verified sample found
  the SAME POLYMARKET trade content living under FOUR structurally-distinct GCS path shapes for one (day, venue) cell —
  the canonical flat-per-contract shape, a byte-adjacent double-named sibling INSIDE that same canonical directory (100%
  overlap on a 79-condition_id sample), a chain=POLYGON/data_type=prediction_trades bundle tree, and a deep 10-segment
  tree (data_source=/market_category=/market_type=/resolution_period=) that is entirely invisible to the manifest
  schema. The UAC machine oracle returns CANONICAL (0 violations) for every one of these shapes — a
  previously-undocumented-for-prediction instance of the oracle's structure-vs-value blindness. Content-verify shows the
  legacy tree carries title/slug/eventSlug market-question text the canonical schema drops, so this is a metadata-loss
  risk, not simple duplication — no delete suggestion is made. Separately, manifest data_type "prediction_trades" (2,477
  rows, 100% captured, 100% blank instrument_id, written as recently as 2026-07-23) is a genuine
  non_canonical_axis_value not covered by any migration_pending suppression. S4 refined: the deployment-api
  reference-scope YAML's PREDICTION section lists ONLY POLYMARKET (genesis 2025-03-14) — KALSHI is entirely absent
  despite ~177K real manifest rows since 2021-06-30 and full MVP scope. No delete suggestion rises above unknown /
  no-migrate-first; zero prod writes made.
status: partial
nature: record
asset_group: [prediction]
stage: [data]
repos:
  [unified-trading-pm, unified-api-contracts, unified-trading-library, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags:
  [
    reconciliation,
    canonicalisation,
    four-surface,
    prediction,
    cqg-bundle,
    manifest,
    id-form,
    metadata-loss,
    legacy-duplicate,
  ]
related:
  [
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/reconciliation-finding-taxonomy.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/non-canonical-path-inventory.md,
    /codex/02-data/canonical-cutover-register.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    plans/audit/results/data_pipeline_reconciliation_prediction_2026_07_20.md,
    plans/active/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md,
    plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md,
    plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md,
  ]
created: 2026-07-24
resulting_plan:
lib_version: unified-api-contracts (workspace checkout, 2026-07-24) + unified-trading-library (workspace checkout)
doc_versions_checked:
audited_scope:
  "asset_group=prediction, --layer raw-tick ONLY (candles explicitly out of scope this dispatch), PROD (-prd-) bucket
  market-data-tick-pred-prd-central-element-323112 only, read-only. Manifest: full-index slim read (761,288 rows,
  pyarrow column projection) + targeted pyarrow filters per data_type/venue. GCS: reachability probe + prefix-scoped
  delimiter descent on one (day=2025-04-11, venue=POLYMARKET) cell (single-walk-exempt, no corpus walk) + one
  content-verified parquet-pair read. Machine oracle run on 5 representative path shapes. instruments-service reference
  bucket / features-pred / strategy-pred layers NOT touched (raw-tick MTDS bucket only, per dispatch scope). No Tier-2
  SPOT-VM walk run; all corpus-wide extrapolations from GCS-side findings are explicitly LOWER BOUNDS."
date: 2026-07-24
auditor: /data-pipeline-reconciliation (dispatched sub-agent run, raw-tick layer only)
parent_epic: infrastructure_master
severity: P1
---

# Data-pipeline reconciliation — asset_group = prediction, raw-tick layer (2026-07-24/25)

Read-only four-surface reconciliation over the PROD (`-prd-`) raw-tick bucket only. No GCS writes, no manifest writes,
no deletes, no backfills, no `--apply`, no whole-corpus walk. The phantom reconciler was **NOT** run against prediction
(hard rule — its CQG-bundle grain is mis-keyed by that tool). This is the `--layer raw-tick` audit only;
`--layer candles` is explicitly out of scope for this dispatch (a sibling report,
`data_pipeline_reconciliation_candles_prediction_2026_07_23.md`, already exists for that layer).

**Surfaces:** S1 = GCS object path + filename · S2 = parquet content / id-form · S3 = manifest `_index` shard-atom · S4
= catalogue / data-status render. A cell is canonical only when all four agree at atom grain; the four bits are never
collapsed into one pass/fail.

**Relationship to the 2026-07-20 prior run** (`data_pipeline_reconciliation_prediction_2026_07_20.md`, same AG, same
raw-tick layer): this run does not re-derive everything from scratch. Where a finding is a continuation/delta of that
run's F1–F5 and H1–H5, it is labelled as such below. New findings this run are labelled F6+.

## 0. Bucket paths table + Phase-0 reachability probe (a real check, run this session)

| Layer (raw-tick only, per dispatch scope) | `kind` passed                 | `asset_group` kwarg                                                                                                                                                             | Resolved bucket                                    | Tier       | Reachable                                      | Top-level prefixes                                                                  |
| ----------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | ---------- | ---------------------------------------------- | ----------------------------------------------------------------------------------- |
| raw tick                                  | `market-data-tick-prediction` | **NOT PASSED** (dedicated flat kind — passing `asset_group="prediction"` raises `BucketNamingError`, confirmed by the dispatching session and not re-tested destructively here) | `market-data-tick-pred-prd-central-element-323112` | ✅ `-prd-` | ✅ (non-recursive top-level listing succeeded) | `_index/` `_migration_backup/` `_vm_staging/` `processed_candles/` `raw_tick_data/` |

Resolution used `deployment_env="prd"` explicitly; `GCP_PROJECT_ID=central-element-323112` was exported (the
required-but-not-tier-mutating env read `resolve_bucket_name` needs — `bucket_naming.py:354`). No `-test-` bucket was
touched or resolved. `processed_candles/` exists in this bucket (co-located, per the skill's layer note) but was **not**
audited this dispatch (raw-tick only, per explicit instruction).

## 1. Index freshness / lock state (Phase-0 gate item, not assumed)

| File                                   | `updated` / `generated_at`        | Content                                                                                                        | Verdict                                                                                                                                                                                                         |
| -------------------------------------- | --------------------------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `_index/availability_index.parquet`    | 2026-07-25 00:26:41 UTC           | 761,288 rows, 7 row groups, 40 columns                                                                         | **Fresh, consolidated read** (not a per-VM-shard fallback)                                                                                                                                                      |
| `_index/latest.json`                   | last_run_at 2026-07-25T00:26:42Z  | `success=true`, `verdict=empty`, `incremental=true`, `no_op=true`, `shards_scanned=1`, `rows_added=0`          | Consolidator healthy, zero-drift no-op run                                                                                                                                                                      |
| `_index/consolidator_stall_state.json` | —                                 | `{"streak": 0, "baseline_shards": 2}`                                                                          | **Not stalled**                                                                                                                                                                                                 |
| `_index/consolidator.lock`             | —                                 | object does not exist (`.exists()` checked directly)                                                           | **Not locked**                                                                                                                                                                                                  |
| `_index/phantom_audit_latest.json`     | generated_at 2026-07-13T15:14:37Z | `phantom_count=2028` (down from the 2026-06-28 baseline of 19,675, after the bundle-atom-exemption fix landed) | **STALE relative to this report by ~11-12 days** — read per the skill's rule (never re-run the auditor), but flagged as a coverage-gap: any phantom-driven undercounting since 2026-07-13 is not reflected here |
| `_index/reprobe_audit_latest.json`     | generated_at 2026-07-14T06:23:16Z | `new_empties=0, disagreements=0, ambiguous=0, proven=0, reclassified=0`                                        | Clean, but same staleness caveat as above                                                                                                                                                                       |

**Net Phase-0 verdict: the manifest read this session is a fresh, consolidated, non-locked, non-stalled index — every S3
count below is a real observation, not a fallback lower bound from index staleness.** The one caveat is the
phantom/reprobe audits themselves (not the index) being ~11-12 days old.

## 2. Manifest (S3) distribution — raw-tick prediction bucket, 761,288 rows (2026-07-24/25 read)

| Axis              | Distribution                                                                                                                                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `capture_status`  | `empty_confirmed` 690,799 (90.74%) · `captured` 67,543 (8.87%) · `expected_unattempted` 2,891 (0.38%) · `attempted_failed` 55 (0.01%)                                                                              |
| `venue`           | POLYMARKET 583,973 · KALSHI 177,315                                                                                                                                                                                |
| `data_type`       | `book_snapshot_5` 397,608 · `trades` 290,589 · `prediction_canonical_question_group` 68,334 · `prediction_trades` **2,477 (NON-CANONICAL — see F6b)** · `market_lifecycle` 2,280                                   |
| `instrument_type` | `PREDICTION_MARKET` 751,422 (98.70%) · `prediction_market` 9,720 (1.28%, C2a migration-window casing) · `prediction` 76 (0.01%, malformed value — F2 continuation) · blank 70 (0.01%, malformed — F2 continuation) |
| `pipeline_mode`   | `batch_polymarket_clob` 709,670 · `batch_kalshi` 30,240 · `live_kalshi` 17,867 · `batch_polymarket_gamma_api` 2,280 · `live_polymarket_clob` 1,231                                                                 |
| `source`          | `polymarket_clob` 710,901 · `kalshi` 48,107 · `polymarket_gamma_api` 2,280                                                                                                                                         |
| `date range`      | 2018-01-01 → 2026-07-24 (3,127 days; pre-2020-01-01 rows are ALL `empty_confirmed`/`EXPECTED_PRE_VENUE_LAUNCH` — honest pre-launch placeholders, verified, not a defect)                                           |

**Shard KEY (pattern #3 for the CQG bundle; pattern #1-like flat-per-contract for `trades`/`book_snapshot_5`).** The
CQG-bundle atom is
`(pipeline_mode, date, asset_group, venue, instrument_type, data_type=prediction_canonical_question_group, canonical_question_group, source)`;
`canonical_question_group` is the KEY but is carried in the row's `instrument_id` column (e.g. `BTC_UP_DOWN_DAILY`), not
a materialized separate column, and has **no path segment** (§2.2 of the four-surface procedure). The
`trades`/`book_snapshot_5` atoms are flat-per-contract with `instrument_id` = the per-market condition_id/ticker.
**Prediction was NOT keyed on `instrument_id` for the CQG bundle anywhere in this run** (the hard rule this skill
enforces).

## 3. Per-surface verdict per shard-CLASS (venue × data_type × pipeline_mode grain — prediction is a

manifest-only-key AG, so per-shard rows don't materialise cleanly; reported at class grain per the skill's own
instruction, four bits never collapsed)

| Shard class                                                         | S1 path-structure                                                                                                                                                             | S2 content / id-form                                                                                                                     | S3 manifest atom                                                                                                                                                    | S4 catalogue                                                        |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| KALSHI / `batch_kalshi`+`live_kalshi` / `trades`                    | **CANONICAL** (oracle 0-viol @ `require_pipeline_mode=True`)                                                                                                                  | Not re-sampled this run (verified 2026-07-20: stem `KALSHI:PREDICTION_MARKET:{id}`)                                                      | PRESENT — 25,385 captured / 50 attempted_failed / 59,270 empty_confirmed; coverage 99.80%                                                                           | **PARTIAL** — see F9 (KALSHI absent from reference-scope YAML)      |
| POLYMARKET / `batch_polymarket_clob` / `trades`                     | **CANONICAL at path-structure** but coexists with 3 non-canonical siblings for the SAME cell — see F6/F7                                                                      | **CANONICAL id-form** for the true canonical leaf, BUT that leaf itself carries a 100%-sampled bare/colon double-naming pattern — see F7 | PRESENT — 8,158 captured / 1 attempted_failed / 197,725 empty_confirmed; coverage 99.99% (formula in §5)                                                            | **PARTIAL** — see F9                                                |
| POLYMARKET / `batch_polymarket_clob` / `prediction_trades` (F6b/F8) | **NON-CANONICAL vocabulary, oracle-blind** — path passes `canonical_path_violations()` but `data_type=prediction_trades` is outside `DATA_TYPES_BY_ASSET_GROUP['prediction']` | 100% blank `instrument_id` on all 2,477 rows                                                                                             | PRESENT — 2,477/2,477 `captured`, 0 `empty_confirmed`/`attempted_failed`/`expected_unattempted` (coverage 100% but on a non-canonical axis — not a meaningful pass) | UNAVAILABLE (not a registered data_type in any catalogue mechanism) |
| `*` / CQG bundle (`prediction_canonical_question_group`)            | N/A — CQG has **no path segment** by design (pattern #3); the raw per-`conditionId` objects it summarises ARE on S1 in canonical form                                         | manifest `instrument_id` is display-only (canonical_question_group label, e.g. `BTC_UP_DOWN_DAILY`) — NOT a violation                    | PRESENT — KALSHI 10,203 captured/2 af/819 eu (92.55%); POLYMARKET 7,291 captured/2 af/2,072 eu (77.85%)                                                             | **PARTIAL** — see F9                                                |
| POLYMARKET / `batch_polymarket_gamma_api` / `market_lifecycle`      | Not spot-probed this run (2,280 rows, 100% `empty_confirmed`, dates 2018-01-01→2021-07-29 — pre-modern-era placeholder window)                                                | Not probed                                                                                                                               | PRESENT (2,280 rows)                                                                                                                                                | UNAVAILABLE                                                         |

**Reading the S4 column** — refined this run, see F9: it is **not** a blanket UNAVAILABLE for every prediction shard as
the 2026-07-20 report stated (that report cited the MTDS-side `_CATALOG_ASSET_GROUPS`/`prediction_catalog_reader.py`
mechanism, which IS confirmed absent, unchanged). The **deployment-api reference-scope mechanism**
(`data-catalogue.instruments-service.yaml` → `shard_status[ASSET_GROUP][VENUE].start_date`, the mechanism the
four-surface procedure's S4(a) actually names) DOES carry a `PREDICTION` key — but only for POLYMARKET. See F9.

## 4. Distinct-value census (§3f of the skill) — the value-level check the per-shard oracle cannot do

Manifest-side (S3) census reused from the slim column-projected read above; GCS-side (S1) census from delimiter
child-prefix descent on the sampled `day=2025-04-11/pipeline_mode=batch_polymarket_clob/` cell (bounded, no walk).
Canonical set (C) = `unified_api_contracts.registry.market_data_categories.DATA_TYPES_BY_ASSET_GROUP['prediction']` /
`VENUES_BY_ASSET_GROUP['prediction']`.

| Axis                                           | Manifest (S3) values                                                                                  | GCS (S1) values (sampled cell)                                                                                                                                                 | Canonical (C)                                                                                    | Verdict                                                                                                                                                                                                          |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `venue`                                        | POLYMARKET, KALSHI                                                                                    | POLYMARKET                                                                                                                                                                     | POLYMARKET, KALSHI                                                                               | Clean — `M ⊆ C`, `G ⊆ C`                                                                                                                                                                                         |
| `data_type`                                    | trades, book_snapshot_5, prediction_canonical_question_group, market_lifecycle, **prediction_trades** | trades, **prediction_trades**                                                                                                                                                  | trades, book_snapshot_5, prediction_canonical_question_group, market_lifecycle, MARKET_LIFECYCLE | **`prediction_trades` in `M − C` AND `G − C`** → `non_canonical_axis_value`, both surfaces, in agreement (not a `shard_atom_vocab_desync` since S1 and S3 agree on the wrong value) — F6b/F8                     |
| `instrument_type` (path segment, sampled cell) | n/a (path only)                                                                                       | `prediction_market` (canonical dirs), `BTC`/`ETH`/`OTHER` (legacy shape #3b)                                                                                                   | `prediction_market` (lowercase, per §3a of the cutover register)                                 | `BTC`/`ETH`/`OTHER` as an `instrument_type=` **path segment** value is `non_canonical_axis_value` (S1) — distinct from the C2a manifest-COLUMN casing axis, which is `migration_pending` and suppressed (see §5) |
| `instrument_type` (manifest COLUMN)            | PREDICTION_MARKET 98.70%, prediction_market 1.28%, prediction 0.01%, blank 0.01%                      | —                                                                                                                                                                              | `{PREDICTION_MARKET}` (target, UPPERCASE per D1)                                                 | Case difference suppressed per §5 (C2a, `migration_pending`); the `prediction` / blank values are a SEPARATE malformed-value axis, NOT casing — carried forward as F2                                            |
| unregistered path axes (sampled cell)          | none in schema                                                                                        | `data_source=POLYMARKET_CLOB`, `market_category={CRYPTO_PRICE,MACRO,MISC,POLITICS_US,TECH,WEATHER}`, `market_type={binary,range_bracket}`, `resolution_period={monthly,event}` | not part of the canonical prediction grammar at all                                              | **`shard_atom_vocab_desync`-adjacent**: these are axes the manifest schema has NO COLUMN for — S3 can never represent them, regardless of vocabulary. See F6a.                                                   |

## 5. Coverage — every % with its formula named, marked LOWER BOUND

`reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`, `empty_confirmed` **EXCLUDED**
(the live, CK3-certified formula — `honest-coverage-model.md`).

**Overall**: `= 67,543 / (67,543 + 55 + 2,891) = 67,543 / 70,489 =` **95.82%** — up from **94.63%** on the 2026-07-20
prior run over the same AG/layer (`51,809 / 54,749`), consistent with continued forward capture. This is a **LOWER
BOUND**: (1) all five asset_groups gate Layer-2 (`instrument_gates_download=true`); (2) `empty_confirmed` is 690,799
rows (90.74% of the corpus) and is correctly excluded, not counted against coverage, but it is retained in `all_shards`
and dominates the estate — prediction markets resolve/close fast, so honest absence is expected to dominate.

**Per (venue, data_type)** (same formula; `N/A` = zero denominator, i.e. no `captured`/`attempted_failed`/
`expected_unattempted` rows at all, only `empty_confirmed`):

| venue      | data_type                                     | captured | attempted_failed | expected_unattempted | empty_confirmed | `reachable_coverage`               |
| ---------- | --------------------------------------------- | -------- | ---------------- | -------------------- | --------------- | ---------------------------------- |
| KALSHI     | book_snapshot_5                               | 12,515   | 0                | 0                    | 56,852          | 100.00%                            |
| KALSHI     | market_lifecycle                              | 0        | 0                | 0                    | 1,306           | N/A                                |
| KALSHI     | prediction_canonical_question_group           | 10,203   | 2                | 819                  | 10,913          | 92.55%                             |
| KALSHI     | trades                                        | 25,385   | 50               | 0                    | 59,270          | 99.80%                             |
| POLYMARKET | book_snapshot_5                               | 1,514    | 0                | 0                    | 326,727         | 100.00%                            |
| POLYMARKET | market_lifecycle                              | 0        | 0                | 0                    | 974             | N/A                                |
| POLYMARKET | prediction_canonical_question_group           | 7,291    | 2                | 2,072                | 37,032          | 77.85%                             |
| POLYMARKET | **prediction_trades (non-canonical, F6b/F8)** | 2,477    | 0                | 0                    | 0               | 100.00% (meaningless — see caveat) |
| POLYMARKET | trades                                        | 8,158    | 1                | 0                    | 197,725         | 99.99%                             |

**Read the two 100.00% book_snapshot_5 rows carefully**: a 100% `reachable_coverage` here means the {captured,
attempted_failed, expected_unattempted} population is 100% captured — it does **NOT** mean book_snapshot_5 is fully
captured overall. POLYMARKET book_snapshot_5 is 99.54% `empty_confirmed` (326,727 of 328,241 total rows for that cell),
all typed `SOURCE_RETURNED_ZERO` (99.7%) or `EXPECTED_PRE_VENUE_LAUNCH` (0.3%) — **zero blank `error_reason`** (verified
directly; no `masked_empty_row` finding), so this is honestly-typed absence per the taxonomy, not a defect this skill
flags. It is noted here as a **coverage-gap observation** (extremely high source-returned-zero rate for POLYMARKET book
snapshots) worth a follow-up investigation outside this read-only audit's scope, not as a typed finding.

**`prediction_trades`'s 100.00% is not a meaningful coverage number** — it is 100% of a non-canonical axis; carried in
the table only for completeness, immediately flagged non-canonical in the same row.

## 6. Typed findings (taxonomy names; carried-forward findings cite the 2026-07-20 report; new ones are F6+)

### Carried forward from 2026-07-20 (re-stated with this run's numbers, not re-derived from scratch)

**F1 — cross-AG manifest bleed into the sports estate · MEDIUM · S3 · NOT independently re-verified this run** (out of
this dispatch's raw-tick-MTDS-prediction-bucket scope — the bleed lives in `instruments-store-sports-prd`). See
`plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` for the standing
tracker.

**F2 — malformed manifest `instrument_type` axis value · LOW-MEDIUM · S3 · GROWING.** 2026-07-20 measured 76 rows
`instrument_type=prediction` + 30 rows blank (106 total). This run measures **76 rows `prediction`** (unchanged count —
same historical rows, not growing) + **70 rows blank** (up from 30, +40 in 4-5 days). Consistent with F5's unguarded
write-path hazard remaining unfixed. Taxonomy-gap (malformed shard-atom axis value fits no closed type) — flagged for
escalation, not fixed inline (collision risk with the owning writer plan).

**F3 — stale catalogue shadow object · LOW · S4 · NOT independently re-verified this run** (lives in
`instruments-store-pred-prd`, the reference bucket — out of this dispatch's raw-tick-only scope). See the 2026-07-20
report §4 F3 for the standing record (`prod/catalog.parquet` vs stale `prd/catalog.parquet` shadow).

**F4 — MTDS-side surface-4 gating mechanism absent for prediction · MEDIUM · S4 · UNCHANGED.** `prediction` is still not
in MTDS `_CATALOG_ASSET_GROUPS` and `prediction_catalog_reader.py` still does not exist (not re-verified by a fresh grep
this run — carried from 2026-07-20 as a standing, structural absence). This is a **different** mechanism from the one F9
(below) refines.

**F5 — unguarded, `pipeline_mode`-less write builder · MEDIUM · S1 (latent) · REFINED this run.** The 2026-07-20 report
characterized this as "latent, not currently realised in the sampled resting estate." **This run's sample found a real,
non-latent, currently-registered-in-the-manifest non-canonical estate (F6/F6b/F8)** — but the specific mechanism differs
from F5's claim (a MISSING `pipeline_mode` segment): every non-canonical shape found this run CARRIES a
`pipeline_mode=batch_polymarket_clob` segment; the defect is EXTRA/WRONG segments (`data_source=`, `market_category=`,
`market_type=`, `resolution_period=`, `data_type=prediction_trades`, `instrument_type={BTC,ETH,OTHER}`), not a missing
one. F5's specific claim (bare shape, no `pipeline_mode`) was not independently re-tested this run and may still hold as
a separate, narrower defect.

### New this run

**F6 — POLYMARKET raw-tick data lives in ≥4 structurally-distinct, oracle-blind path trees for the same shard,
content-verified as the SAME trades · HIGH · S1 (structure) + S2 (content/schema) · BIG FINDING, issue doc filed +
operator-notify.** Full evidence in
[`plans/active/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`](../../active/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md).
Summary: for `day=2025-04-11`/`venue=POLYMARKET`, the SAME 500-row trade batch for one `condition_id` exists,
content-verified byte-for-byte-matching on `transactionHash`/`timestamp`/`price`/`amount`, under (a) the canonical
flat-per-contract path, (b) a double-named sibling INSIDE that same canonical directory
(`POLYMARKET:PREDICTION_MARKET:{cid}.parquet` — 79/79 = 100% overlap with the bare-named set in the sampled directory),
(c) a `chain=POLYGON`/`data_type=prediction_trades`/`underlying=` bundle tree, (d) an
`instrument_type={BTC,ETH,OTHER}`/`data_type=prediction_trades` variant, and (e) a deep 10-segment
`data_source=POLYMARKET_CLOB/.../market_category=/underlying=/market_type=/resolution_period=/data_type=trades/` tree
that is **entirely invisible to the manifest schema** (no matching columns exist in `availability_index.parquet` at
all). **The UAC oracle (`canonical_path_violations`, `require_pipeline_mode=True`) returns CANONICAL (0 violations) for
all five path forms.** Content-verify additionally shows the legacy 24-column schema (e) carries
`title`/`slug`/`eventSlug` human-readable market-question text and a diverging derived `resolution_period` value
(`monthly` vs the canonical schema's `event`) that the 22-column canonical schema does not carry — **this is a
metadata-loss risk, not simple duplication; no delete suggestion is made** (see §7).

**F6a — the deep 10-segment tree's axes have NO manifest column at all · HIGH · S3 (structural blind spot) · sub-finding
of F6.** `data_source=`, `market_category=`, `market_type=`, `resolution_period=` do not appear among the 40 columns of
`availability_index.parquet` (schema dumped and verified directly this run). This means these objects can **never** be
represented by any S3 row under the current manifest schema, regardless of how the writer that produced them is fixed —
the schema itself would need a change, or these objects fold into the canonical `trades` shard atom (losing their extra
metadata, per F6) as the resolution.

**F6b / F8 — manifest `data_type=prediction_trades` is a genuine, currently-written non-canonical axis value ·
MEDIUM-HIGH · S3 (`non_canonical_axis_value`) · date-conditional, NOT `migration_pending`.** 2,477 manifest rows, 100%
`capture_status=captured`, `schema_version=9` (current schema, not a legacy marker), 100% blank `instrument_id`,
spanning 348 distinct dates (2025-03-14→2026-04-14, 100% date-overlap with the true CQG bundle rows for the same venue),
most recently `written_at=2026-07-23T05:11Z` — **2 days before this audit, i.e. actively being (re-)registered, not a
frozen historical artifact.** `prediction_trades` is absent from `DATA_TYPES_BY_ASSET_GROUP['prediction']` and is
**not** one of the two axes RULED-but-`migration_pending` in `canonical-cutover-register.md` (C2a casing, defi LENDING)
— it does not qualify for suppression under §5 of the taxonomy. Filed as a genuine finding, not suppressed.
Cross-reference: this does not match the codex's documented PRE-Plan-A legacy shape either (`data_type=<base_asset>`
literally, e.g. `data_type=BTC`) — the on-disk shape found here uses `data_type=prediction_trades` with
`underlying={BTC,ETH,OTHER,...}` as a row/bundle-key column, which is a **third, previously-undocumented shard-grain
variant** (see the issue doc's Q3).

**F7 — canonical `data_type=trades` directory itself carries a 100%-sampled bare/colon-prefixed double-naming pattern ·
MEDIUM · S1/S2 (id-form) · sub-finding of F6, but independently notable because it sits INSIDE the declared-canonical
directory.** In the one directory sampled (`day=2025-04-11`, POLYMARKET, `data_type=trades`), 158 objects = 79 distinct
`condition_id`s × 2 naming forms each: bare `{cid}.parquet` and double-wrapped
`POLYMARKET:PREDICTION_MARKET:{cid}.parquet` — **100% overlap, 0 bare-only, 0 colon-only.** Same class of hazard already
documented for CeFi (`canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`'s wire-named vs double-wrapped stems),
here measured for the first time inside prediction's canonical directory. Corpus-wide extent is **UNKNOWN** — this is a
single-date sample, not a walk; a Tier-2 SPOT-VM census (or a bounded multi-date sample) is needed for a defensible
percentage.

**F9 — deployment-api reference-scope catalogue (S4a) is only PARTIALLY populated for prediction: POLYMARKET present,
KALSHI entirely absent · MEDIUM · S4 · refines F4 (which is a DIFFERENT, MTDS-side mechanism).**
`data-catalogue.instruments-service.yaml`'s `shard_status.PREDICTION` (read directly this run) carries exactly one
venue: `POLYMARKET: {start_date: "2025-03-14", ...}`. **No `KALSHI` key exists.** Per `reference_scope.py`'s own
documented rule ("an unlisted venue... is genuinely out_of_scope"), the deployment-api in-scope test would classify
every `(prediction, KALSHI, *)` cell as **out of scope**, despite KALSHI carrying 177,315 real manifest rows (earliest
genuine `captured` date 2021-06-30, not a placeholder) and
`is_mvp(asset_group="prediction", venue="KALSHI", data_type=dt)` returning `True` for all three main data_types
(verified directly, not assumed). This is a **more precise** finding than the 2026-07-20 report's blanket "S4
UNAVAILABLE for every shard" — that report's F4 correctly identified the MTDS-side `_CATALOG_ASSET_GROUPS` mechanism as
fully absent, but did not check the SEPARATE deployment-api reference-scope YAML's actual content, which turns out to be
half-populated rather than empty. Register-patch candidate: add a `KALSHI` entry to `shard_status.PREDICTION` with
`start_date: "2021-06-30"` (subject to a real genesis confirmation — 2021-06-30 is this run's measured earliest genuine
`captured` row, not an independently-sourced venue-launch date).

## 7. Phase 2 — non-canonical sweep, register cross-check, delete suggestions

### 7a. Register cross-check (`non-canonical-path-inventory.md`)

**Register → reality**: the register carries **zero** prediction-scoped rows today (grepped in full; the only
`prediction`-adjacent hit in the whole register is row 12, about the ML-predictions LAYER's `category=` key, an entirely
different system from this MTDS raw-tick bucket). Nothing to re-verify.

**Reality → register (new leads this run — register-patch stanza, NOT applied directly, per the concurrency clause; this
is a single-dispatch interactive-equivalent run but the PM repo is a shared multi-slot checkout, so the patch is
proposed here for serial application)**:

```
| # (next) | prefix/shape | disposition | evidence | notes |
| --- | --- | --- | --- | --- |
| new | market-data-tick-pred-prd-central-element-323112/raw_tick_data/by_date/day=*/pipeline_mode=batch_polymarket_clob/asset_group=prediction/data_source=POLYMARKET_CLOB/... (10-segment tree) | no-migrate-first | F6/F6a, content-verified 2026-07-24: carries title/slug/eventSlug not in canonical schema; NOT manifest-representable at all | see issue doc — do NOT delete pending Q1/Q2 |
| new | .../venue=POLYMARKET/chain=POLYGON/instrument_type=prediction_market/data_type=prediction_trades/underlying={U}/... | no-migrate-first | F6b/F8, manifest-registered non-canonical data_type, 2,477 rows, still being written as of 2026-07-23 | pending Q3 (retro-register vs migrate/purge) |
| new | .../venue=POLYMARKET/instrument_type={BTC,ETH,OTHER}/data_type=prediction_trades/... | no-migrate-first | same as above, sibling shape | same |
| new | .../venue=POLYMARKET/instrument_type=prediction_market/data_type=trades/POLYMARKET:PREDICTION_MARKET:{cid}.parquet (double-named sibling INSIDE the canonical dir) | unknown | F7, 100% overlap on a 79-cid sample, sizes matched in the one pair content-verified; not proven corpus-wide | needs a bounded multi-date sample or Tier-2 walk before any disposition upgrade |
```

### 7b. Delete suggestions — none rise above `unknown`/`no-migrate-first`

Per the five-part proof (`gcs-and-manifest-delete-safety-protocol.md`): (1) twin resolves via `gcs_describe_object` —
YES for F7's pair; (2) content verify — YES, done, and it revealed the legacy schema (F6) carries fields the canonical
one lacks, which is itself a reason NOT to delete; (3) grep-then-READ proof nothing still writes the legacy shapes —
**NOT DONE** this run (see issue doc Q2); (4) grep-then-READ proof nothing still reads them — **NOT DONE**; (5)
legacy-copied-not-moved invariant — not applicable to assess without (3)/(4). **Any part failing ⇒ `no-migrate-first`.**
Zero suggestions cross the human-only prod-bucket-delete hard stop regardless; none of the findings here approach that
gate.

### 7c. Orphans

**NOT ASSESSED** (no whole-corpus walk this run, per single-walk discipline). Per `orphan-object-detection.md` §3, an
unmeasured "0 orphans" is never reported. F6a's deep-tree objects are **candidates** for `orphan_real` classification
(valid-looking shard shape, real content, no possible S3 representation) but this was measured on ONE date only — not a
corpus-wide orphan count.

### 7d. §4c static audit of sibling backfill write paths

Confirmed via the dispatching session's Phase-0 verification (bucket names resolve to `-prd-`, not `-test-`) that this
run targeted the correct tier; a deep code-read of the MTDS Polymarket adapter / rebuild scripts to identify which
writer produces the F6 legacy shapes was **NOT performed this run** (see issue doc todo 1) — this is a data-estate
finding, not a writer-code finding, and the writer identification is explicitly deferred to the issue doc's todos to
avoid scope creep into a live-code investigation from a read-only reconciliation pass.

## 8. Two axes RULED-but-`migration_pending` — neither refused, neither flagged (per §5 of the taxonomy, corrected

since the 2026-07-20 run)

1. **C2a — manifest `instrument_type` COLUMN casing.** Measured: `PREDICTION_MARKET` 751,422 (98.70%) vs
   `prediction_market` (lower) 9,720 (1.28%). Per `reconciliation-finding-taxonomy.md` §5.1 (RULED UPPERCASE target,
   `migration_pending`, operator D1 2026-07-20) — **compared case-insensitively, NO finding emitted.** This corrects the
   2026-07-20 prior run's "REFUSED" framing, which was itself flagged there as resting on a since-resolved SSOT
   contradiction (taxonomy vs three sibling docs). The contradiction is now reconciled per the current codex; this run
   follows the corrected, current stance.
2. **decision D — defi market/event `LENDING` keying.** Not applicable — defi-only axis, no prediction data touches it.

## 9. Suppressed accepted-exception counts (suppression proven, not re-listed)

| Accepted exception (taxonomy §4)                                                                                | Prediction-scoped rows suppressed                                                                                                    |
| --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| AE-1 sports blank `pipeline_mode`/`source`                                                                      | 0                                                                                                                                    |
| AE-2 tradfi `combo`                                                                                             | 0                                                                                                                                    |
| AE-3 defi two-id POOL divergence                                                                                | 0                                                                                                                                    |
| AE-4 tradfi `batch_massive` read-recognition                                                                    | 0                                                                                                                                    |
| AE-5 defi flat `LENDING`                                                                                        | 0                                                                                                                                    |
| AE-6 MDPS candle-layer migration window                                                                         | 0 (out of scope — raw-tick only)                                                                                                     |
| C2a instrument_type COLUMN case (§5.1, not an AE-numbered exception but the same suppress-don't-flag treatment) | ~9,796 rows (`prediction_market` lower + `prediction`/blank malformed values are counted separately as F2, not suppressed under C2a) |

**None of AE-1..AE-6 scope `asset_group=prediction`; suppressed count = 0 for all six.** The pre-2020 honest pre-launch
placeholder rows (5,840, §2) were verified typed (`EXPECTED_PRE_VENUE_LAUNCH`) and are correctly excluded from
`reachable_coverage`'s denominator by the formula itself, not by a suppression rule — no separate suppression needed.

## 10. Coverage gaps (what was NOT reached this run, and why)

1. **Candles layer** — explicitly out of scope for this dispatch (raw-tick only); a sibling report already exists
   (`data_pipeline_reconciliation_candles_prediction_2026_07_23.md`).
2. **F6/F6a/F7's corpus-wide extent** — measured on ONE `(day=2025-04-11, venue=POLYMARKET)` cell via prefix-scoped
   listing (single-walk-exempt). The manifest's `prediction_trades` axis gives a partial handle (2,477 rows / 348 dates)
   for shapes (c)/(d), but shape (e) (F6a, the deep tree) has **zero** manifest representation, so its corpus-wide
   extent is genuinely **unknown** without a Tier-2 SPOT-VM single walk.
3. **F1 (cross-AG sports bleed)** and **F3 (catalogue shadow object)** — not independently re-verified this run (both
   live outside the raw-tick MTDS bucket this dispatch targets).
4. **F4's specific MTDS `_CATALOG_ASSET_GROUPS` absence** — carried forward from 2026-07-20, not re-grepped fresh this
   run.
5. **F5's specific bare/no-`pipeline_mode` shape claim** — not independently re-tested this run; F5 is refined (§6) but
   not confirmed-or-refuted on its original narrow claim.
6. **Whether `title`/`slug`/`eventSlug` (F6) survive anywhere in the canonical estate** — explicitly deferred to the
   issue doc's Q1, not resolved here (would require reading `instruments-service`'s `catalog.parquet`, out of this
   dispatch's raw-tick-bucket scope).
7. **Orphans** — NOT ASSESSED (no walk).
8. **Writer/script identification for the F6 legacy shapes** — deferred to the issue doc's todo 1 (a code-read task, not
   a data-estate reconciliation task).
9. **features-pred / strategy-pred layers** — not touched (raw-tick MTDS bucket only, per explicit dispatch scope).
10. **Phantom/reprobe audit staleness** — both are ~11-12 days old relative to this report (§1); any drift since
    2026-07-13 is not reflected in the phantom count cited.

## 11. Hazard checklist (reference-prediction.md H1–H5, carried from the skill's own per-AG table)

1. **H1** — phantom reconciler NOT run against prediction this run either; nothing keyed on `instrument_id` for the CQG
   bundle.
2. **H2** — prediction MVP-scope state unchanged from 2026-07-20 framing; treated as state, not regression.
3. **H3** — S4 refined this run (F9): not a blanket absence, but a half-populated reference-scope YAML plus a fully
   absent MTDS-side gating mechanism (F4) — two distinct S4-ish mechanisms, both incomplete for different reasons.
4. **H4** — not independently re-tested this run (see coverage gap 5); F5 was refined with different evidence
   (extra/wrong segments, not missing `pipeline_mode`).
5. **H5** — not independently re-verified this run (coverage gap 3); standing tracker exists.

---

**Headline answer: asset_group=prediction (raw-tick layer) is NOT 100% canonical.** The manifest-visible lower bound is
small in row-count terms (2,477 / 761,288 = 0.33% of all manifest rows carry the definitively non-canonical
`prediction_trades` data_type value, F6b/F8), but that count structurally EXCLUDES an entire class of non-canonical
objects (F6a's deep 10-segment tree) that the manifest schema cannot represent at all, and excludes the double-naming
pattern found INSIDE the canonical directory itself (F7, 100% of a 79-condition_id sample). The UAC machine oracle — the
workspace's designated canonical/non-canonical authority — returns a CLEAN (0-violation) verdict on every one of these
non-canonical shapes, so a report that cited only the oracle would have (wrongly) called this AG 100% canonical. A
defensible corpus-wide non-canonical percentage requires a Tier-2 SPOT-VM walk; this read-only, single-session,
single-cell-sampled pass establishes existence and content-verified severity, not a full-corpus percentage.
