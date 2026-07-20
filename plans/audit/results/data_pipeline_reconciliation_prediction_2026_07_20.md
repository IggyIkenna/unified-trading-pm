---
doc_type: audit-result
title: "Data-pipeline reconciliation — prediction (2026-07-20)"
summary: >-
  Four-surface canonicalisation reconciliation of asset_group=prediction over PROD buckets only (read-only). All four
  prod buckets (raw-tick, reference, features, strategy) resolve to -prd- tier and are reachable; strategy-store-pred is
  EMPTY as documented. Representative sample exercises every reference-sheet hazard H1-H5. Key measured results:
  reachable_coverage 94.63% (LOWER BOUND; empty_confirmed = 92.6% of rows excluded); the machine oracle finds observed
  pipeline_mode-carrying objects CANONICAL at require_pipeline_mode=True, and both KALSHI and POLYMARKET filename stems
  are canonical id-form (VENUE:PREDICTION_MARKET:{id}); surface-4 has NO gating mechanism for prediction (not in MTDS
  _CATALOG_ASSET_GROUPS, no prediction_catalog_reader) so every S4 verdict is UNAVAILABLE; the H5 cross-AG bleed into
  the sports manifest is CONFIRMED and has GROWN (>=6597 vs documented 4097); a recent malformed-instrument_type cluster
  (106 rows, non-casing) and the unguarded pipeline_mode-less write builder (H4) are new/confirmed writer-side signals.
  The phantom reconciler was NOT run (H1). No delete suggestion rises above unknown; orphans NOT ASSESSED (no walk). C2a
  instrument_type COLUMN casing REFUSED — with an SSOT contradiction surfaced.
status: partial
nature: record
asset_group: [prediction]
stage: [data]
repos:
  [unified-trading-pm, unified-api-contracts, unified-trading-library, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, four-surface, prediction, cqg-bundle, manifest, id-form, cross-ag-bleed]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    gcs-and-manifest-delete-safety-protocol,
    non-canonical-path-inventory,
    canonical-cutover-register,
    orphan-object-detection,
    prediction-data-types-catalog,
    prediction-schema-paths,
  ]
created: 2026-07-20
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=prediction, PROD (-prd-) buckets only, read-only; sample = raw-tick manifest full-index aggregate
  (745,136 rows) + prefix-scoped S1/S2 probes on 3 captured shards + 1 empty-day negative probe + machine oracle on 4
  path shapes + top-level reachability on all 4 buckets + catalogue describe (prod/ + prd/) + H5 slim read of
  instruments-store-sports + code READs. NOT reconciled: features/strategy layers, whole-corpus walk / orphans, parquet
  interiors, market-data(tick)/sports bleed, the bare-shape legacy prefix tree."
date: 2026-07-20
auditor: /data-pipeline-reconciliation (first real execution of the prediction reference sheet + acceptance test)
parent_epic: infrastructure_master
severity: P1
---

# Data-pipeline reconciliation — asset_group = prediction (2026-07-20)

Read-only four-surface reconciliation over PROD (`-prd-`) buckets only. No GCS writes, no manifest writes, no deletes,
no backfills, no `--apply`, no whole-corpus walk. The phantom reconciler was **NOT** run against prediction (hazard H1 —
running it against the CQG-bundle grain wipes bundle rows).

**Surfaces:** S1 = GCS object path + filename · S2 = parquet content / id-form · S3 = manifest `_index` shard-atom · S4
= catalogue / data-status render. A cell is canonical only when all four agree at atom grain; the four bits are never
collapsed.

## 0. Bucket paths table (resolved via `resolve_bucket_name`, never inline `gs://`)

| Layer     | `kind` passed                  | Resolved bucket                                     | Tier     | Reachable | Top-level prefixes                                                                  |
| --------- | ------------------------------ | --------------------------------------------------- | -------- | --------- | ----------------------------------------------------------------------------------- |
| raw tick  | `market-data-tick-prediction`  | `market-data-tick-pred-prd-central-element-323112`  | ✅ -prd- | ✅        | `_index/` `_migration_backup/` `_vm_staging/` `processed_candles/` `raw_tick_data/` |
| reference | `instruments-store-prediction` | `instruments-store-pred-prd-central-element-323112` | ✅ -prd- | ✅        | `_backups/` `_index/` `instrument_availability/` `market_lifecycle/` `prd/` `prod/` |
| features  | `features-prediction`          | `features-pred-prd-central-element-323112`          | ✅ -prd- | ✅        | `xinstrument/`                                                                      |
| strategy  | `strategy-store-prediction`    | `strategy-store-pred-prd-central-element-323112`    | ✅ -prd- | ✅        | _(EMPTY — matches inventory row 21)_                                                |

All four resolve to `-prd-`; **no `-test-` leak**. No bucket was unreachable. Resolution used `deployment_env="prod"`
explicitly (no process-env mutation). Note the reference-sheet caveat honoured: prediction uses the **dedicated flat
yaml keys** with the short `pred` token — `kind="market-data"` with `asset_group="prediction"` does not resolve (the
`market-data` dict has only CEFI/DEFI/TRADFI/SPORTS), confirmed by the `BucketNamingError` raised when reaching the
sports tick bucket in the H5 probe.

## 1. Per-surface verdict per sampled shard (four bits, never collapsed)

| Sampled shard class                                          | S1 path-structure                                                          | S2 content / id-form                                                                    | S3 manifest atom                                                                 | S4 catalogue         |
| ------------------------------------------------------------ | -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | -------------------- |
| KALSHI / `batch_kalshi` / trades                             | **CANONICAL** (oracle 0-viol @ rpm=True)                                   | **CANONICAL** stem `KALSHI:PREDICTION_MARKET:FEDHIKE-26DEC31` …                         | PRESENT (captured)                                                               | **UNAVAILABLE** (H3) |
| POLYMARKET / `batch_polymarket_clob` / trades                | **CANONICAL**                                                              | **CANONICAL** stem `POLYMARKET:PREDICTION_MARKET:0x76151c…`                             | PRESENT (day-2026-07-18 cell empty_confirmed — not an absence bug)               | **UNAVAILABLE** (H3) |
| POLYMARKET / `live_polymarket_clob` / book_snapshot_5        | **CANONICAL**                                                              | **CANONICAL** stem verified; manifest `instrument_id` col 100% grammar                  | PRESENT (captured)                                                               | **UNAVAILABLE** (H3) |
| `*` / CQG bundle (`prediction_canonical_question_group`)     | N/A — CQG has **no path segment**; on-disk = per-`conditionId` (canonical) | manifest `instrument_id` **display-only** (`OTHER`/blank) — pattern #3, NOT a violation | PRESENT (bundle grain; `canonical_question_group` KEY not a materialized column) | **UNAVAILABLE** (H3) |
| POLYMARKET / `batch_polymarket_gamma_api` / market_lifecycle | CANONICAL (template; not spot-probed)                                      | NOT PROBED                                                                              | PRESENT (2,280 rows)                                                             | **UNAVAILABLE** (H3) |

**Reading the S4 column:** it is `UNAVAILABLE` for _every_ prediction shard — not a per-shard failure but a structural
absence (F4/H3). Per the four-surface procedure §3.1, an unreadable surface is `unavailable`, never `absent`, and a
shard with an unavailable surface is INCONCLUSIVE for that surface and never carries a delete suggestion.

**Probe-vocabulary discipline (the rule that already produced one false verdict elsewhere).** Before trusting any zero,
the writer's actual vocabulary was confirmed: object stems are the full canonical id `VENUE:PREDICTION_MARKET:{id}` (not
a bare `conditionId`); POLYMARKET's zero on `day=2026-07-18` was proven to be a legitimate `empty_confirmed` cell (a
genuinely-captured day, 2026-07-19, returned an object), not an absence defect. Templates were enumerated from
`canonical_path_templates("prediction")` — which correctly includes the `live_kalshi` / `live_polymarket_clob` /
`live_polymarket_gamma_api` §5-union prefixes (the shapes whose omission previously false-phantomed 13,292 rows). Note
the reference-sheet caveat: `_AG_SEGMENT_SHAPE[PREDICTION]` is the empty string, so the templates stop at
`asset_group=prediction/` with no venue/instrument_type/data_type tail — those segment values were derived from the
**manifest rows**, not the templates.

## 2. Manifest (S3) distribution — raw-tick prediction bucket, 745,136 rows

| Axis            | Distribution                                                                                                                             |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| capture_status  | empty_confirmed 690,387 · captured 51,809 · expected_unattempted 2,885 · attempted_failed 55                                             |
| venue           | POLYMARKET 581,136 · KALSHI 164,000                                                                                                      |
| data_type       | book_snapshot_5 397,608 · trades 277,358 · prediction_canonical_question_group 67,890 · market_lifecycle 2,280                           |
| instrument_type | **PREDICTION_MARKET 741,029** · prediction_market 4,001 · **prediction 76** · **None 30**                                                |
| pipeline_mode   | batch_polymarket_clob 706,742 · live_kalshi 17,867 · batch_kalshi 17,016 · batch_polymarket_gamma_api 2,280 · live_polymarket_clob 1,231 |
| source          | polymarket_clob 707,973 · kalshi 34,883 · polymarket_gamma_api 2,280                                                                     |
| date range      | 2018-01-01 → 2026-07-20 (3,123 days)                                                                                                     |

**Shard KEY (pattern #3).** The atom is
`[pipeline_mode, date, asset_group, venue, instrument_type, data_type, canonical_question_group, source]`.
`canonical_question_group` is the KEY but is **not a materialized column** in the consolidated index; `instrument_id` is
present on every row but is **display-only** (`OTHER`/blank on CQG rows). Keying prediction on `instrument_id` is banned
(H1) and was not done anywhere in this run.

## 3. Coverage — with its formula named, marked LOWER BOUND

`reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`, `empty_confirmed` **EXCLUDED**
(the live CK3-certified formula, `honest-coverage-model.md`).

`= 51,809 / (51,809 + 55 + 2,885) = 51,809 / 54,749 =` **94.63%** — a **LOWER BOUND**. Two reasons it is a lower bound:
(1) all five asset_groups gate Layer-2 (`instrument_gates_download=true`); (2) `empty_confirmed` is 690,387 rows (92.6%
of the corpus) — prediction markets resolve/close fast, so honest absence dominates and is correctly excluded, not
counted against coverage. No coverage figure in this report is quoted without its formula.

## 4. Typed findings (taxonomy names; taxonomy gaps flagged as escalations)

**F1 — cross-AG manifest bleed into the sports estate · MEDIUM · surfaces S3 · notify operator.**
`asset_group=prediction` rows are physically in the `instruments-store-sports-prd` manifest: **≥6,597** (KALSHI 6,562,
POLYMARKET 35; trades 6,484, CQG 113), dates **2026-07-16 → 2026-07-19**. This has **GROWN** versus the documented 4,097
(2026-06-26 → 07-18) in reference-sheet H5 — the bleed is active. Root cause unlocated (2026-07-20). Read-only: not
"fixed" here. Cross-link: `reference-prediction.md` H5 / `reference-sports.md` H4. _Measurement caveat:_ the sports
index was in **stale per-VM-shard fallback** (`consolidated blob age 168.6s > 120s`), so 6,597 is a partial
recent-weighted count and a lower bound; the `market-data`(tick)/sports manifest was not read. This finding is a
taxonomy gap (no closed type fits a cross-bucket asset_group bleed) — escalated, not silently narrated.

**F2 — malformed manifest `instrument_type` axis value · LOW-MEDIUM · surfaces S3.** 106 recent manifest rows carry a
malformed `instrument_type`: **76 rows `instrument_type=prediction`** (CQG bundle, KALSHI, captured) + **30 rows
`instrument_type=None`** (trades, POLYMARKET, empty_confirmed). All dated 2026-07-16 → 2026-07-19 (post-cutover).
Case-insensitively these are **not** `prediction_market`, so they fall **outside** the C2a casing refusal — `prediction`
is a wrong _value_ (missing `_market`), and `None` is a null axis. Consistent with the H4 unguarded-write hazard (a
silent write path with no canonical guard for prediction). Taxonomy gap (a malformed shard-atom axis value fits no
closed type) — flagged for escalation.

**F3 — stale catalogue shadow object · LOW · surfaces S4.** `instruments-store-pred-prd` holds BOTH
`prod/catalog.parquet` (201,854,166 B, live) and a stale shadow `prd/catalog.parquet` (65,217,347 B, ~2026-06-27) — the
3-char `DEPLOYMENT_ENV_SHORT` leaked into the object key where the intended prefix is the long `prod/`. This is
**non-canonical-path-inventory row 2** (disposition `yes-after-verify`); register→reality re-verified **exactly** (both
byte sizes match the register). Delete disposition unchanged: `no-migrate-first`/`unknown` — the writer that produced
`prd/` is unidentified, no content-verify was done, and a prod-bucket delete is a human-only hard stop. Reported once,
not per shard.

**F4 — surface-4 gating mechanism absent for prediction · MEDIUM · surfaces S4 · declared coverage gap (H3).**
prediction is **not** in MTDS `_CATALOG_ASSET_GROUPS = ("sports","cefi","defi","tradfi")` (`catalog_registration.py:69`,
READ), and **no `prediction_catalog_reader.py` exists** (cefi/defi/sports/tradfi readers all present). The
catalogue-gates-download (G4) contract therefore has no mechanism for prediction, so every prediction shard's S4 verdict
is `UNAVAILABLE` by construction. Stated as a declared coverage gap rather than a fabricated S4 pass/fail.

**F5 — unguarded, `pipeline_mode`-less write builder · MEDIUM · surfaces S1 (latent) · writer-plan todo.**
`build_prediction_partition_path` (`partition_paths.py:383`, READ) has **no `pipeline_mode` kwarg** — it emits the bare
`raw_tick_data/by_date/day=/asset_group=prediction/venue=/instrument_type=/data_type=/{conditionId}.parquet` shape; the
`pipeline_mode=` segment must be string-injected downstream by the dispatcher. The write-time canonical guard is
**tradfi-only** (`partitioned_writer.py:258`: `if self._asset_group == "tradfi": _assert_canonical_tradfi_path(...)`,
READ), so a missed rewrite is a **silent** non-canonical write. The machine oracle confirms the bare shape is
`CANONICAL` at `require_pipeline_mode=False` but a **VIOLATION** at `require_pipeline_mode=True` (prediction cutover
2026-05-19) — i.e. the default is weaker than the declared form (§4.1). _Mitigating:_ every spot-probed recent object
carries the segment and is oracle-canonical at rpm=True, so the defect is latent, not currently realised in the sampled
resting estate. Fix belongs to the MTDS/UAC writer plan — **not fixed inline** (collision risk).

## 5. Refused axes (unruled — reported, not adjudicated)

1. **C2a — manifest `instrument_type` COLUMN casing.** Measured: `PREDICTION_MARKET` 741,029 (99.46%) vs
   `prediction_market` (lower) 4,001 (0.54%). **REFUSED** — reported as a count, no finding, no migration proposed, per
   `reconciliation-finding-taxonomy.md` §5.1. Compared case-insensitively elsewhere (the path segment lowercase and the
   id middle-segment UPPER are settled and were enforced). **SSOT contradiction surfaced** (see §8): three sibling codex
   docs say this axis was RULED UPPERCASE (D1) on 2026-07-20 while the taxonomy still lists it as unruled. Either
   reading yields the same non-action here (refused, or `migration_pending` — never a fresh finding).
2. **decision D — defi market/event `LENDING` keying.** REFUSED, but **not applicable** to prediction (defi-only axis).
   No prediction data touches it.

## 6. Suppressed accepted-exception counts (suppression proven, not re-listed)

| Accepted exception (taxonomy §4)             | Prediction-scoped rows suppressed |
| -------------------------------------------- | --------------------------------- |
| AE-1 sports blank pipeline_mode/source       | 0                                 |
| AE-2 tradfi `combo`                          | 0                                 |
| AE-3 defi two-id POOL divergence             | 0                                 |
| AE-4 tradfi `batch_massive` read-recognition | 0                                 |
| AE-5 defi flat `LENDING`                     | 0                                 |

**None of AE-1..AE-5 scope `asset_group=prediction`; suppressed count = 0.** The legitimate `_unknown_` `conditionId`
stem and the CF-15 `live_`-prefix union were honoured structurally (by enumerating from
`canonical_path_templates("prediction")`), which is prevention, not suppression.

## 7. Delete suggestions, orphans, inventory re-verification

- **Delete suggestions above `unknown`: 0.** No prediction location clears the five-part proof. The `prd/` catalogue
  shadow is `no-migrate-first` (content-verify not done, `prd/`-writer unidentified) and a prod-bucket delete is a
  human-only hard stop regardless.
- **Orphans: NOT ASSESSED (no whole-corpus walk in this run).** Per `orphan-object-detection.md` §3, an unmeasured "0
  orphans" is never reported; orphan enumeration rides the single walk (`migration_orphan_sweep.py`) or does not happen.
- **Inventory re-verification (register ↔ reality), prediction-scoped:**
  1. Row 2 (`instruments-store-pred-prd/prd/catalog.parquet` shadow) — CONFIRMED present, both sizes match the register
     exactly. Disposition unchanged (`yes-after-verify`).
  2. Row 21 (`strategy-store-pred-prd` empty) — CONFIRMED empty.
  3. Reality→register (new leads, disposition `unknown`, not delete candidates):
     `market-data-tick-pred-prd/_vm_staging/` (operational staging dir, not in register) and
     `market-data-tick-pred-prd/_migration_backup/` (register row 23 lists `_migration_backup/`+`_migration_backups/`
     for cefi/defi only — this is a new prediction instance). Both are appended here as leads for the register's
     maintenance contract; neither is a delete candidate.

## 8. SSOT contradiction surfaced (do not resolve here)

`reconciliation-finding-taxonomy.md` §5.1 lists **C2a (instrument_type COLUMN casing) as "genuinely UNRULED"** and
requires the skill to REFUSE it. Three sibling codex docs — `four-surface-reconciliation-procedure.md` §7-O2,
`canonical-cutover-register.md` §3c, and `gcs-and-manifest-delete-safety-protocol.md` §4 — all state the axis was
**RULED UPPERCASE (operator ruling D1) on 2026-07-20** and that "the reconciler now ENFORCES UPPERCASE." The taxonomy is
`authoritative_for` "axes the reconciliation skill must refuse to report on," yet it contradicts the three docs that are
authoritative for the cutover and delete-safety consequences. This run followed the REFUSE path (per the taxonomy and
the invocation constraint). The prediction estate is 99.46% `PREDICTION_MARKET` already, so under either reading the
0.54% lowercase tail is non-action (refused, or `migration_pending`).

## 9. Coverage gaps (what was NOT reached, and why)

1. Surface-4 catalogue gating mechanism is absent for prediction (F4/H3) — S4 is unverifiable by construction, not
   skipped by choice.
2. `market-data`(tick)/sports manifest not read for H5; the `instruments-store-sports` index was in stale per-VM-shard
   fallback, so the exact full bleed count is not pinned (≥6,597).
3. The bare-shape legacy prefix tree (no `pipeline_mode`) was not enumerated on disk — whether resting prediction
   objects exist under it is unmeasured (would require a prefix sweep of the bare shape; recent writes carry the
   segment).
4. Orphans NOT ASSESSED (no walk).
5. Parquet interiors (row-level content columns) were not opened — S2 id-form was verified via the filename stem
   spot-sample only.
6. CQG-bundle S1↔S3 grain comparison was not exhaustively reconciled (the many-to-one object→bundle mapping;
   `canonical_question_group` is not a materialized column) — and must not be done by keying `instrument_id` (H1).
7. features-pred layer: only reachability + top-level (`xinstrument/`) probed; its four surfaces were not reconciled.
   strategy-pred is empty (nothing to reconcile).

## 10. Hazard checklist (reference-prediction.md H1–H5)

1. H1 — phantom reconciler NOT run against prediction; nothing keyed on `instrument_id` (verified `instrument_id` is
   `OTHER`/blank on CQG rows).
2. H2 — prediction not-MVP-ready (Phase-B canonicalisation HELD) treated as state, not regression.
3. H3 — surface-4 gating mechanism absent → declared coverage gap (F4), not a fabricated verdict.
4. H4 — unguarded, `pipeline_mode`-less write builder confirmed by code READ + oracle demo (F5).
5. H5 — cross-AG bleed CONFIRMED and worsening (F1).
