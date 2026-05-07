---
title: "Manifest consolidator silently failing on 3 asset_groups (Arrow TypeError on instrument_count)"
created: 2026-05-07
author: claude-agent (session 2026-05-07)
source:
  - unified-trading-library/unified_trading_library/manifest_consolidator.py (concat path)
  - instruments-service/scripts/enumerate_expected_universe.py:612-640 (writer that emits string-typed instrument_count)
  - manifest-consolidator-20260507-175639 run.log (gs://deployment-scripts-central-element-323112/vm-logs/.../run.log)
  - market-data-tick-{defi,tradfi,prediction,cefi}-central-element-323112 _index/per_vm/expected-universe-enum-*.parquet
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

# Manifest consolidator silently failing on 3 asset_groups (Arrow TypeError on instrument_count)

> **Severity**: P0 — silent data-staleness across 4 asset_groups including DeFi (May 23 live-trading critical path).
> **Blast radius**: `market-data-tick-{defi,tradfi,prediction,cefi}-central-element-323112` canonical manifests +
> every downstream consumer (deployment-api data-status, instruments-service skip-if-exists, MTDS gapfills, MDPS
> pre-flight, features-\* pre-flight, strategy-service archetype runs).
> **Suggested owner**: writegate-honest-coverage Phase 3.D.4 (the agent owning
> `instruments-service/scripts/enumerate_expected_universe.py` per the Tier 3D.1 + 3D.4 expected-universe-enumerator
> work). Cross-ref: `defi_archetypes_doc_plan_drift_2026_05_07.md` already cites this enumerator family as
> "deployment-service@dcc5c87 + instruments-service@8e404c8".

## What I found

`manifest-consolidator-20260507-175639` (run log
`gs://deployment-scripts-central-element-323112/vm-logs/manifest-consolidator-20260507-175639/run.log`) reports
`success=False` on **3 of 12 buckets** with an identical pyarrow error and zero rows-out:

```
[2026-05-07T17:02:08Z] consolidating market-data-tick-defi-central-element-323112
  File "pyarrow/error.pxi", line 92, in pyarrow.lib.check_status
pyarrow.lib.ArrowTypeError: ("Expected bytes, got a 'int' object",
                              'Conversion failed for column instrument_count with type object')
manifest-consolidator bucket=market-data-tick-defi-central-element-323112 success=False
  shards=0 rows_in=0 rows_out=0 ... latency_ms=18542.7 error=ArrowTypeError: ...

[2026-05-07T17:02:37Z] consolidating market-data-tick-tradfi-central-element-323112
... same ArrowTypeError ... success=False ...

[2026-05-07T17:02:51Z] consolidating market-data-tick-prediction-central-element-323112
... same ArrowTypeError ... success=False ...
```

The 4th affected bucket (`market-data-tick-cefi-central-element-323112`) was spared THIS cycle only because the soft
lock from a prior in-flight consolidator was still fresh (`success=True ... error=locked`). The bad shard is sitting
on disk and will fail the next non-locked cycle.

The canonical manifest mtimes confirm staleness:

```
gs://market-data-tick-defi-central-element-323112/_index/availability_index.parquet
  3823059  2026-05-07T14:56:41Z   ← last successful write ~3 hours before run started
```

### Root cause — schema mismatch on a single new shard family

Sniffed every per-VM shard in the 3 failing buckets + cefi for comparison:

| bucket             | shard                                                    | rows    | `instrument_count` arrow type | python type seen   |
| ------------------ | -------------------------------------------------------- | ------- | ----------------------------- | ------------------ |
| **defi**           | `expected-universe-enum-defi-20260507-155353.parquet`    | 1286260 | **`string`**                  | **`{'str'}`** (`""`) |
| **tradfi**         | `expected-universe-enum-tradfi-20260507-154607.parquet`  | 35033   | **`string`**                  | **`{'str'}`** (`""`) |
| **prediction**     | `expected-universe-enum-prediction-20260507-155030.parquet` | (>0) | **`string`**                  | **`{'str'}`** (`""`) |
| **cefi**           | `expected-universe-enum-cefi-20260507-154922.parquet`    | 119152  | **`string`**                  | **`{'str'}`** (`""`) |
| sports             | (no `expected-universe-enum-*` shard yet)                | —       | —                             | —                  |
| every other shard  | `_legacy_seed.parquet`, `blank-reason-recon-*`, `mtds-vault-*`, `cme-events-q*-*`, `local-*`, `tradfi-recent-ice-*`, etc. | int64 | `{'int'}` |

So **every per-VM shard except the four `expected-universe-enum-{asset_group}-*` outputs** writes `instrument_count`
as `int64`. The new enumerator family writes it as the empty string `""`.

When the consolidator concats via `pd.concat([...])` (manifest_consolidator.py:756 `_read_path_subset` →
`_merge_shard_frames` in `manifest_writer.py`), pandas upcasts the mixed `int64` + `string` column to `object` dtype.
At the final `merged.to_parquet(...)` call (manifest_writer.py:2334 / 2383 / 2461) pyarrow tries to coerce the
`object` column according to the **first** observed value's type and then chokes when a later value mismatches —
hence the exact wording `"Expected bytes, got a 'int' object", 'Conversion failed for column instrument_count
with type object'`. The error is symmetric: if the enumerator shard sits at the head of the concat order it expects
bytes (=string), then chokes on the next int from a normal shard.

### Code citation — origin of the empty-string `instrument_count`

[`instruments-service/scripts/enumerate_expected_universe.py:612-640`](../../../../instruments-service/scripts/enumerate_expected_universe.py#L612):

```python
new_rows_records: list[dict[str, object]] = []
for r in absent_rows:
    record: dict[str, object] = {
        "asset_group": asset_group,
        "venue": r.venue,
        "chain": r.chain,
        "data_type": r.data_type,
        "instrument_type": r.instrument_type,
        "instrument_id": r.instrument_id,
        "league_id": r.league_id,
        "date": r.date,
        "capture_status": "empty_confirmed",
        "error_reason": r.reason,
        "attempted_at": attempted_at_iso,
        "row_count": 0,                          # ← scalar int, fine
        "service_name": "instruments-service",
        "enumerator_run_id": run_id,
    }
    new_rows_records.append(record)

new_df = pd.DataFrame(new_rows_records)
# Align columns with the canonical manifest where they overlap; fill
# any missing columns with empty values so the parquet schema lines up.
manifest_cols = list(df.columns)
for col in manifest_cols:
    if col not in new_df.columns:
        new_df[col] = ""                          # ← BUG: blanket "" for every missing column
                                                  #         including the int64 column instrument_count
new_df = new_df.reindex(columns=manifest_cols + [c for c in new_df.columns if c not in manifest_cols])
```

The `instrument_count` column from the canonical manifest is `int64`. The enumerator's records dict has no
`instrument_count` key, so the `if col not in new_df.columns: new_df[col] = ""` loop assigns the empty string `""`
to the entire 1.28M-row column. The on-disk parquet then carries `instrument_count: pa.string()` for every row
of every enumerator shard.

Three reproductions, each from a fresh `gcloud storage cp ... && pyarrow.parquet.read_table(...)`:

```
defi  shard expected-universe-enum-defi-20260507-155353.parquet:
  schema=string | python_types={'str'} | rows=1286260 | sample=['', '', '']
tradfi shard expected-universe-enum-tradfi-20260507-154607.parquet:
  schema=string | python_types={'str'} | rows=35033 | sample=['', '', '']
cefi   shard expected-universe-enum-cefi-20260507-154922.parquet:
  schema=string | python_types={'str'} | rows=119152 | sample=['', '', '']
```

vs. every legacy seed and every other shard:

```
defi  _legacy_seed.parquet:    schema=int64 | python={'int'} | sample=[0, 0, 0]
tradfi _legacy_seed.parquet:   schema=int64 | python={'int'} | sample=[0, 541, 21555]
prediction _legacy_seed.parquet: schema=int64 | python={'int'} | sample=[5295, 0, 13421]
cefi  _legacy_seed.parquet:    schema=int64 | python={'int'} | sample=[0, 0, 980866]
```

## Why it matters

1. **DeFi manifest staleness on the May 23 critical-path.** DeFi is the live-trading target asset_group. Every
   per-VM shard from MTDS / instruments-service / reconcilers landing in
   `gs://market-data-tick-defi-central-element-323112/_index/per_vm/` after 2026-05-07 14:56 UTC is invisible to
   `_index/availability_index.parquet`. Downstream pre-flight gates trust the canonical manifest — `feature_groups`
   compute, MDPS reprocesses, strategy-service archetype runs all read a 3-hour-stale view. Silent. Until an
   operator notices canonical mtime hasn't moved.
2. **Same problem on TradFi + Prediction + CeFi.** TradFi is a paper-trade prerequisite (Group F live-only). CeFi
   carries the perp hedge legs (Bybit/Deribit/Binance/OKX) for the carry_staked_basis archetype. Prediction is
   queued for the post-May-23 archetype line. All three manifests are equally stale once the bug hits its
   matching cycle — only sports + the strategy/instruments-store buckets remain healthy.
3. **Contradicts manifest v5/v6 schema SSOT.** The shard-granularity SSOT in CLAUDE.md is explicit: "writer
   atomicity boundary (parquet finalize + `record_captured`)" must match "manifest row key (v5 columns)" must
   match "data-status display rollup". Allowing `instrument_count` to be int OR string violates pillar 3 ("Schema
   matches contract"). The schema isn't enforced at the writer boundary — `record_empty` / `record_captured` /
   `record_expected_empty` go through `ManifestWriter.add` which has the int64 contract, but
   `enumerate_expected_universe.py` bypasses that contract by building a `pd.DataFrame` directly and calling
   `to_parquet`. Two writer paths producing the same outcome with divergent shapes is the "No double SSOT in
   data-saving methodology" rule violated.
4. **Bug latched ~14:56 UTC 2026-05-07** (per canonical mtime + the enumerator-shard timestamps `155353` /
   `154922` / `154607` / `155030`). It has been silent for **~2.5 hours at issue-doc-write time**. It will get
   worse: every additional successful write from any other writer to a per-VM shard widens the gap between the
   canonical's stale view and the true view, AND each subsequent consolidator cycle re-reads the bad enumerator
   shard from disk and re-fails the same way. There is no self-healing path; the bad shard sits on disk until
   manually cleaned.
5. **Manifest is the inter-service trust boundary.** The "Manifest concurrency principle" rule (workspace-wide)
   has every backfill / gapfill script keying off the canonical via 60-second TTL freshness checks. With the
   canonical frozen, every new MTDS / MDPS / features VM that consults the manifest mid-run sees a stale skip-set
   and may either (a) re-do work some other VM just did (waste) or (b) skip work it shouldn't (correctness gap,
   harder to detect).

## Recommended decision

Single point of failure, single fix on the writer side, but **two operator decisions** ride on top.

### Fix shape (Recommendation: option (a) — fold into writegate Phase 3.D.4)

**(a) [PREFERRED]** Patch `enumerate_expected_universe.py` to typed-fill missing columns instead of blanket `""`:

```python
# Pull the canonical manifest's per-column dtype; fill ints with 0, strings with "", timestamps/etc. with NaT/None.
for col in manifest_cols:
    if col not in new_df.columns:
        canonical_dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(canonical_dtype):
            new_df[col] = 0
        elif pd.api.types.is_float_dtype(canonical_dtype):
            new_df[col] = 0.0
        elif pd.api.types.is_datetime64_any_dtype(canonical_dtype):
            new_df[col] = pd.NaT
        else:
            new_df[col] = ""
```

This keeps the schema-from-canonical pattern (defensible — there are 50+ columns in the v5/v6 manifest and the
enumerator shouldn't need to know all of them) but stops the int64-column corruption. **Owner**: writegate plan
Phase 3.D.4 author (instruments-service@8e404c8 commit author per the cross-ref doc).

**(b)** Stop the blanket-fill entirely and have the enumerator emit ONLY the columns it knows about; let
`_merge_shard_frames` do an outer-join concat that pads missing-from-enumerator columns from the canonical's
dtype. Cleaner long-term but requires changes in `manifest_writer._merge_shard_frames` too — riskier blast radius.

**(c) [REJECTED]** Coerce at consolidator-read-time (`_read_path_subset`) — masks the writer-side schema drift,
violates "manifest migration NOT fallback" rule.

### Operator-decision items

**Decision A** — what to do with the **on-disk bad shards** while the fix lands. Two paths:

1. **Delete the 4 bad enumerator shards** from
   `gs://market-data-tick-{defi,tradfi,prediction,cefi}-central-element-323112/_index/per_vm/expected-universe-enum-{asset_group}-202605*.parquet`,
   let the consolidator unblock immediately (same cycle), then re-run the enumerator with the fixed code. Loses
   the writegate Phase 3.D.4 backfill work that the current shard represents (~1.5M rows total). Writegate can
   re-emit; the enumerator is idempotent on `(shard_key, day)`.
2. **Migrate the bad shards in-place** with a one-shot `pa.Table.cast` script that flips the column dtype
   `string → int64` (filling `""` → `0`) before re-uploading. Preserves the work but adds a script that runs
   once and gets archived. Aligns with "manifest migration, NOT fallback" rule shape.

Either path unblocks the consolidator. **(1) is faster + simpler; (2) preserves throughput.** Operator call.

**Decision B** — does this plan want to **harden the writer contract** at the same time, or punt to a follow-up?

Per the "No double SSOT in data-saving methodology" rule, the right shape is `enumerate_expected_universe.py`
calling `ManifestWriter.record_expected_empty(reason=...)` row-by-row instead of building a DataFrame and
`to_parquet`-ing direct. The script's own comment says it does the latter "to avoid thousands of CAS round-trips
per the reconciler precedent" — which is true for the canonical-write CAS, but per-VM shard writes have NO CAS
contention (the whole point of the per-VM split is one-writer-per-shard). The DataFrame path is a perf
optimisation that gave up the schema contract.

If the operator wants the proper structural fix, the script should batch into a single `pd.DataFrame` built BY
calling `ManifestWriter._build_row(...)` (the same row-builder `record_expected_empty` uses internally), so the
schema is constructed via the contract regardless of which write path is used. That requires a small refactor in
UTL `ManifestWriter` to expose `_build_row` as a public helper. Bigger change; cleaner long-term. Recommend folding
into writegate Phase 3.D.4 closeout, not as part of the Decision-A fast-fix.

### Severity tagging for operator chat

This finding is **case 5 (big / cross-cutting)**: data-correctness, May 23 critical-path, contradicts the
shard-granularity SSOT, contradicts an in-flight VM run (the consolidator). Operator chat-notification + this
issue doc landed together per the Findings Triage Discipline rule.

## Cross-reference

- The bug-introducing commit family is the same one referenced in
  [`defi_archetypes_doc_plan_drift_2026_05_07.md`](./defi_archetypes_doc_plan_drift_2026_05_07.md) opening note:
  _"the rollup-vs-drilldown data-status denominator gap is being closed in parallel via writegate Phase 3.D.4
  expected-universe enumerator (deployment-service@dcc5c87 + instruments-service@8e404c8)"_. Tier 3D.4 itself is
  high-leverage and should not be reverted; only the schema-fill bug needs patching.
- The fix lands in the writegate-honest-coverage plan (`writegate_honest_coverage_endtoend_2026_05_06.plan.md`)
  Phase 3.D.4 closeout, not as a standalone plan.
