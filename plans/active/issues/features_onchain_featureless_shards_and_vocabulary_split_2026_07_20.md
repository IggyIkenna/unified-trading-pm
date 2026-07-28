---
doc_type: issue
title: >-
  features-onchain: five of seven feature groups are byte-identical FEATURE-LESS shards stamped `captured`, six
  never-produced groups carry false `captured` manifest rows, and three vocabularies disagree about what a feature_group
  is called
summary: >-
  A question about feature_group naming uncovered a larger P0. On any given day, five of the seven on-chain feature
  groups written to features-defi-prd are BYTE-IDENTICAL parquets containing only ['timestamp','instrument_id',
  'timestamp_out'] — 153,956 rows and zero feature columns — and every one is stamped capture_status=captured. Six
  further groups have false `captured` manifest rows with zero GCS objects, traced 1:1 to six batch-skip sites that
  `return True` with a zero row count. Separately, the UAC feature registry, the features-service CLI, the writer
  literals and ml-service each use a different vocabulary for feature_group, so four consumer repos read names that no
  writer emits and each swallows the miss into an empty result. The vocabulary question needs an operator ruling
  (registry-authoritative is REFUTED; adopting writer names would ratify a dishonest manifest; renaming is a PROD data
  migration). The producer and loudness fixes do not need one and are being applied.
status: open
nature: issue
asset_group: [defi]
stage: [data, features]
repos: [features-service, strategy-service, ml-service, e2e-testing, deployment-api, unified-api-contracts]
scope: [engineer, admin]
tags: [silent-failure, data-correctness, feature-groups, manifest-honesty, ssot-contradiction, defi]
related:
  [
    /plans/archive/issues/silent_wrong_answer_bucket_resolution_class_2026_07_20.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md,
  ]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend
drift_direction: advance-code
depends_on: []
source:
  [
    "adversarial adjudication workflow run 2026-07-20 after noticing that the feature_group the P&L engine reads is not
    the one the producer writes; the naming question was masking the feature-less-shard P0",
  ]
resolved_by:
locked_by:
---

# features-onchain — feature-less shards, false captures, and a three-way vocabulary split

> **Read this before acting on section 6 of [[silent_wrong_answer_bucket_resolution_class_2026_07_20]]** — that section
> originally said `aave_rate_impact` merely needed a backfill. It does not. Running the calculator writes `rate_impact`,
> which the reader still cannot see.

## 1. P0 — five of seven written feature groups contain NO features

On `day=2026-03-05` in `gs://features-defi-prd-central-element-323112/onchain/`:

| feature_group             | md5                        | verdict                         |
| ------------------------- | -------------------------- | ------------------------------- |
| `flash_loan_availability` | `hnf702rMHOEF1FQOiCGffw==` | **byte-identical, no features** |
| `health_factor`           | `hnf702rMHOEF1FQOiCGffw==` | **byte-identical, no features** |
| `liquidation_events`      | `hnf702rMHOEF1FQOiCGffw==` | **byte-identical, no features** |
| `rewards`                 | `hnf702rMHOEF1FQOiCGffw==` | **byte-identical, no features** |
| `risk_params`             | `hnf702rMHOEF1FQOiCGffw==` | **byte-identical, no features** |
| `lending_rates`           | `KNXwk8qjFOXb3km/JII9ww==` | real — 15 columns               |
| `lst_yields`              | (absent that day)          | real — 8 columns, 15 days only  |

Those five files are 153,956 rows of `['timestamp','instrument_id','timestamp_out']` and **nothing else**. Reproduced
independently on a second day (`2026-05-20`). 118 days each.

**Mechanism** (`features_service/onchain/engine/orchestrator_calculators.py`, ~221-320): each calculator builds its
output column list defensively —

```python
for c in ("ltv", "liquidation_threshold"):
    if c in rate_data.columns:
        cols.append(c)
return rate_data.select(cols)
```

When the upstream `load_rate_indices()` payload lacks the feature columns, this returns a **non-empty** frame of base
columns. The writer sees rows, writes the parquet, returns `result=True`, and the manifest stamps `captured`. The lookup
cannot fail and the caller cannot fail — the same shape as [[silent_wrong_answer_bucket_resolution_class_2026_07_20]],
and the same shape as the `aave_utilization` false-zero bug already documented **in this very file** at
`orchestrator_calculators.py:183-191`, fixed there and left in place everywhere else.

To every downstream consumer these are indistinguishable from real shards: right path, right name, plausible row count,
`captured` in the manifest.

## 2. P0 — six false `captured` manifest rows, explained exactly

`onchain/_index/availability_index.parquet` holds 13 rows, all `date=2026-01-25`, all
`capture_status=captured / expected=True / available=True`. Six carry `instrument_count=0` and have **zero GCS
objects**: `perp_funding_rates`, `macro_sentiment`, `lst_native_rates`, `rate_impact`, `onchain_perps`, `utilization`.

`features_service/onchain/engine/orchestrator.py` contains exactly **six** `FEATURE_GROUP_SKIPPED_BATCH_INCOMPATIBLE`
sites (~225, ~466, ~508, ~642, ~709, ~811), each doing `self._last_record_count = 0; return True`. The wrapper at
:176-179 writes a **captured** manifest row on any `True`. Six skip sites → six false rows. A 1:1 mechanical match.

This is the banned "empty placeholder rows that look populated" pattern, verbatim.

## 3. The vocabulary split — three (arguably four) names for one concept

| source                                   | example names                                                                                       |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------- |
| UAC registry (`FEATURE_GROUP_TO_FAMILY`) | `aave_lending_rates`, `aave_risk_params`, `aave_rate_impact`, `lst_staking_yields`, `eigen_rewards` |
| features-service CLI (`FEATURE_GROUPS`)  | `lending_rates`, `risk_params`, `rate_impact`, `lst_yields`, `rewards`                              |
| writer literals / GCS partition values   | `lending_rates`, `risk_params`, `lst_yields`, `rewards`, `health_factor`, `liquidation_events`      |
| ml-service `DEFI_FEATURE_GROUPS`         | a fourth set, defined twice in two files                                                            |

**Zero objects exist under any registry-canonical name.** No alias layer exists anywhere.

**Registry-authoritative is REFUTED**, and the reason matters: `lending_rates` is a genuine **multi-protocol merge** —
on `day=2026-03-05` its `protocol` column is AAVE_V3 152,961 / COMPOUND_V3 36 / SPARK 9 / null 950, produced by
`_load_merged_lending_data` gathering Aave + Compound + Kamino into one frame. Renaming it to `aave_lending_rates` would
**mislabel 995 non-Aave rows** — manufacturing a fresh silent wrong answer of exactly the class being killed. The
registry also has no name at all for `health_factor` or `liquidation_events` (118 days each), and declares
`onchain_regime`, which has no calculator and no data. A vocabulary that cannot name existing production shards cannot
be authoritative over them.

**But writer-authoritative cannot simply be ratified either**: 11 of the writer's 13 names are unbacked — six have zero
objects, five are the feature-less placeholders above. Ratifying it into UAC would enshrine a manifest that positively
asserts never-produced data as captured.

That is why the naming question is an operator ruling and not an engineering choice.

## 4. Confirmed downstream consumers, all failing SILENTLY

| repo             | site                               | reads                      | what happens                                                                   |
| ---------------- | ---------------------------------- | -------------------------- | ------------------------------------------------------------------------------ |
| strategy-service | `pnl/engine/orchestrator.py:125`   | `aave_rate_impact`         | swallowed → `{}` → **unadjusted P&L + 0 bps presented as adjusted**            |
| e2e-testing      | `scripts/defi/colocated_engine.py` | wrong prefix + wrong names | per-group `except: pass` → **backtests complete green on ZERO features**       |
| ml-service       | `cloud_feature_provider.py:384`    | a fourth vocabulary        | total miss → empty DataFrame behind a `logger.warning` → **trains on nothing** |
| deployment-api   | `breakdowns_core.py:325`           | 11 registry names          | the 7 real groups can never appear → **11 phantom coverage gaps rendered**     |

## 5. Coverage stops at 2026-05-22

The `onchain/` prefix has 118 day partitions ending `day=2026-05-22`, though the objects were _written_ 2026-07-18 — so
the pipeline runs, its date range simply ends two months back. **Any DeFi P&L or model training against a recent date
gets nothing under ANY vocabulary.** The manifest is simultaneously frozen at 1 of 118 days and the consolidator reports
`shards_scanned=1 / rows_in=0` against 723 live objects, so the manifest has also stopped self-correcting. This may
outrank the naming question entirely.

## 6. Operator rulings — RESOLVED 2026-07-21

1. **Which vocabulary is canonical for `feature_group`?** ✅ **RULED: option A (adopt writer/CLI names).** The UAC
   onchain registry was reconciled to the writer vocabulary — `unified-api-contracts@e9faf32e`: renamed
   `aave_lending_rates→lending_rates`, `aave_utilization→utilization`, `aave_risk_params→risk_params`,
   `lst_staking_yields→lst_yields`, `eigen_rewards→rewards` (protocol-agnostic), `aave_rate_impact→rate_impact`; ADDED
   `health_factor` + `liquidation_events`; DROPPED `onchain_regime` / `defillama_tvl` / `protocol_rewards` (no writer
   dispatch). Final = the CLI's 13. No GCS partition renamed, no prod-data migration. deployment-api auto-follows.
   **Follow-up (not blocking):** two adjacent vocabularies still carry the old names — `required_inputs.py`
   (`FEATURE_REQUIRED_INPUTS`, currently dormant, no runtime call site) and `internal/schemas/_feature_contracts.py`
   (own consumers/test) — reconcile in a dedicated pass.
2. **Any rename is a PROD DATA MIGRATION** — moot under ruling #1 (writer names are already what's on disk; the registry
   reconciliation moves NO objects).
3. **The six false `captured` rows** + **4. the five feature-less shard families** — ✅ **RULED: mark→recompute**, but
   BOTH are BLOCKED on deeper defects (a frozen onchain index/consolidator, and the missing MTDS chain-field collection)
   — the producer honesty already shipped (`features-service@907e17b4`); the durable close is fix-consolidator →
   re-derive-index → build-MTDS-collectors → recompute. Full analysis:
   [[onchain_manifest_dishonest_and_recompute_blocked_2026_07_21]]. Do NOT hand-edit the frozen prod index.
4. **Registry membership corrections** — ✅ done as part of ruling #1 (`health_factor`/`liquidation_events` added,
   `onchain_regime` dropped) in `e9faf32e`.
5. **Does DeFi ML training run in prod today?** ✅ **RULED: no.** The ml-service empty-DataFrame guard
   (`ml-service@93309c5`) stands as a latent correctness guard, not an active P0.

## 7. Being applied now (correct under EVERY surviving hypothesis, no ruling needed)

These are producer-honesty and loudness fixes. None renames anything, none touches prod data.

- Calculators declare a required-output-column set; a frame lacking them is **not written** — `record_failed` /
  `record_empty` with an explicit reason.
- The captured-manifest write is gated on the frame carrying at least one non-base column, not merely on non-emptiness.
- The six batch-skip sites stop returning `True` into a captured write.
- strategy-service splits honest absence (404) from a real error and propagates `rate_impact_unavailable`, so an
  unadjusted P&L is never presented as adjusted.
- e2e `colocated_engine.py` prefix `onchain_features/` → `onchain/` (that prefix exists under no hypothesis), and a run
  resolving zero feature groups **fails** instead of emitting empty ticks. Group names deliberately **not** re-pointed —
  three of the four writer equivalents are the feature-less placeholders, so "fixing" the names would convert a total
  miss into a quiet partial success, which is worse.
- ml-service raises on a DeFi total miss instead of returning an empty frame behind a warning; the duplicated
  `DEFI_FEATURE_GROUPS` definitions are collapsed so they cannot drift apart.
- deployment-api emits observed-but-unexpected groups as an explicit mismatch bucket, so vocabulary drift renders as
  drift rather than as a coverage hole.
- A machine check enumerating all three vocabularies and reporting the diff, so this can never drift silently again.

## 8. Two unverified signals, recorded but NOT asserted

- The written parquets appear to contain exact duplicate rows (same `timestamp` + `instrument_id` repeated).
- Manifest `instrument_count` is identical (14,630,914) across six different groups, which is implausible as a per-group
  count.

Both warrant a look. Neither was verified, and neither should be repeated as fact until it is.

## VERIFIED 2026-07-28 (slot-7) — both §8 signals CONFIRMED, root causes established (investigation only, no fix)

Read-only, per todo's stated scope (`defi_satellite_ao_dispatch_batch1-040`). Repos touched: features-service,
unified-trading-library (read-only inspection of the live `features-defi-prd-central-element-323112` bucket via UTL's
`get_storage_client()`/`download_bytes` — no writes).

**(a) Exact duplicate rows — CONFIRMED, sampled evidence from both reference days.**

Downloaded and read the real `onchain/by_date/day={day}/feature_group={g}/features.parquet` shards (note: the actual
canonical prefix is `onchain/by_date/day=.../`, not the bare `onchain/day=.../` shorthand used in §1 above — confirmed
via a direct `list_blobs` on the bucket) for all 6 groups that have real objects on disk
(`flash_loan_availability`/`health_factor`/`lending_rates`/`liquidation_events`/`rewards`/`risk_params`; `lst_yields`
has no object on either sampled day — consistent with its 15-day-only coverage noted in §1):

| day          | rows written | exact-duplicate `(timestamp, instrument_id)` rows | fraction |
| ------------ | -----------: | ------------------------------------------------: | -------: |
| `2026-03-05` |      153,956 |                                           111,341 |   ~72.3% |
| `2026-05-20` |       84,331 |                                            65,087 |   ~77.2% |

Every one of the 5 feature-less groups is still byte-identical (md5-confirmed) to each other on both days, matching §1's
finding independently. **Verdict: YES, confirmed — the majority of rows in every sampled shard are exact duplicates on
the (timestamp, instrument_id) key**, on both reference days named in the todo.

**(b) `instrument_count` identical across six groups — CONFIRMED, root cause found (NOT a live-orchestrator bug).**

Read the manifest directly (`onchain/_index/availability_index.parquet` AND its sole source shard
`onchain/_index/per_vm/_legacy_seed.parquet` — both byte-for-byte reproduce the same 13 rows). Confirmed live: exactly
six `feature_group` rows (`lending_rates`, `health_factor`, `rewards`, `liquidation_events`, `risk_params`,
`flash_loan_availability` — precisely the 6 groups that route through `_process_daily_feature_group()` in
`orchestrator.py` and have real GCS objects) all carry `instrument_count=14630914`, `date=2026-01-25`,
`capture_status=captured`.

Traced the live-orchestrator code path first (`features_service/onchain/engine/orchestrator.py:177` +
`orchestrator_daily_loop.py:202`): `self._last_record_count` is explicitly reset to `0` at the top of
`process_feature_group()` **before** dispatch to any specific `_process_*` method, and reset again inside
`_process_daily_feature_group()` — so the live per-call `ManifestWriter.add(row_count=self._last_record_count, ...)`
path (`orchestrator_manifest.py:90-96`) cannot itself produce a value shared across groups; each call gets its own fresh
counter. **This rules out a live-code cross-group state-leak as the cause.**

Root cause is instead in the artifact itself: `_index/per_vm/_legacy_seed.parquet` is UTL's own documented "permanently
frozen, never pruned" bootstrap-seed shard convention (`manifest_consolidator.py` — "so the historical rows appear in
[the availability index]"), not a live per-day write. Directly verified the number's provenance: summing
`flash_loan_availability`'s real per-day row count (via parquet metadata `num_rows`, no full download) across **all 118
real day-partitions** currently on disk (`day=2026-01-25` .. `day=2026-07-26`) gives **exactly 14,630,914** — an exact
match, not an approximation. So the seed row's `instrument_count` is a **whole-corpus cumulative row-count SUM**,
stamped onto one synthetic manifest entry dated `2026-01-25` (apparently the first backfill day, used as a placeholder
date) with `capture_status=captured`, rather than a genuine single-day shard count.

It is identical across all six groups **not because of a copy-paste/shared-variable bug in the seeding process**, but as
a direct, deterministic consequence of §1's own root defect: all six calculators consume the SAME
`load_rate_indices()`/merged-loader output and only differ in which COLUMNS they retain (five drop every real feature
column defensively; `lending_rates` keeps its real columns but drops no ROWS) — so their row cardinality is identical,
day-for-day, corpus-wide. Six independently-computed 118-day sums over row-identical inputs are mathematically bound to
land on the same total. **This is not a second, independent bug — it is signal (b) surfacing the same §1 defect from a
different angle** (row-count/manifest side rather than row-content side).

This also corroborates §5's "manifest frozen at 1 of 118 days" finding: the legacy-seed bootstrap row was never
superseded by real per-day manifest writes because the consolidator has been stalled since 2026-07-18 (confirmed:
`onchain/_index/per_vm/` contains only this one shard, `last_modified=2026-07-18T11:02:45Z`, alongside a
`consolidator_stall_state.json` sentinel) — the same already-tracked consolidator-stall blocker named in
[[onchain_manifest_dishonest_and_recompute_blocked_2026_07_21]].

**Not determined**: the exact one-off script/process that originally generated `_legacy_seed.parquet` (no matching
seed/backfill script was found in the current features-service/unified-trading-library/instruments-service trees — it
was likely an uncommitted or since-deleted ad hoc bootstrap run). The DATA-level mechanism (whole-corpus sum,
byte-exact-matched) is conclusively established regardless of which script produced it.

**Disposition**: both signals are real and now asserted as fact. No fix applied (investigation-only per this todo's
scope) — the fix path is already the one this doc's ruling #3 names (fix-consolidator → re-derive-index →
build-MTDS-collectors → recompute), not a new one.

## Todos

- [ ] [DATA] P0. **Fix onchain features consolidator → re-derive-index → build-MTDS-collectors → recompute** — the
      mark→recompute fix for the 6 false-`captured` rows and 5 feature-less shard families (ruling #3) is BLOCKED on the
      frozen onchain manifest/consolidator (stalled since 2026-07-18); full chain tracked in
      `onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md`, not yet executed.
