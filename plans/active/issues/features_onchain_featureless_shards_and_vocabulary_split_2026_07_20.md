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
    silent_wrong_answer_bucket_resolution_class_2026_07_20.md,
    defi_consolidated_closeout_2026_07_18.md,
    defi_dex_pools_delete_order_stale_2026_07_20.md,
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

Both warrant a look. Neither was verified, and neither should be repeated as fact until it is. </content>
