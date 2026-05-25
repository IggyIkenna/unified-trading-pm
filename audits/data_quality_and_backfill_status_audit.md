# Data Quality & Backfill Status Audit

> **Repeatable operational audit** for the GCS data lake — verifies (a) backfill completeness and (b) per-shard data
> quality (rows present, not silent-zero / NaN-filled) across all asset groups. Run this whenever a backfill fleet is in
> flight, before declaring a layer GREEN, and before any downstream layer launch (MTDS→MDPS→features→strategy).

**Runbook fields (HARD RULE — keep current):**

- `owner`: Harsh (data-pipeline)
- `cadence`: on-demand during active backfills + at every layer-completion gate
- `verifier`: per-shard manifest `capture_status` + parquet row/NaN sample (both required — never one alone)
- `last_executed`: 2026-05-25 (CeFi backfill in flight; see § Open Findings)

**Why both signals are mandatory:** the manifest can say `captured` while the parquet is a zero-row / all-NaN
placeholder (silent-zero bug), and a parquet can have rows while the manifest never recorded the shard (phantom). Always
cross-check manifest status against an actual parquet read.

---

## 0. Pipeline order (audit upstream→downstream; never skip the gate)

```
instruments-service ──▶ MTDS (raw ticks) ──▶ MDPS (processed candles) ──▶ features ──▶ strategy
```

A layer is **not** auditable as GREEN until its upstream is GREEN. Features backfill is explicitly gated:
`features_backfill_phase3` declares `gate: mdps_backfill_phase3 per-ag verification GREEN`. See
`codex/11-project-management/foundation-completion-gate-discipline.md`.

---

## 1. Existing audit scripts (use these first — do not reinvent)

| Script                                                                      | What it checks                                                                                                                                   | Invocation                                                                    |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| `instruments-service/scripts/measure_honest_coverage.py`                    | Coverage % per asset_group / venue / data_type (rollup metric). Runs daily → `gs://central-element-323112-honest-coverage/{date}/coverage.json`  | `--asset-group cefi\|defi\|tradfi\|sports\|prediction\|all --output-path ...` |
| `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`        | Phantom captures (manifest=`captured` but no parquet) = backfill-completeness check                                                              | `--asset-group X --dry-run` (never write empties to mask phantoms)            |
| `market-tick-data-service/scripts/audit_structural_checks.py`               | 6 structural checks: schema-version dist, written_at chronology, bucket-name drift, per-VM shard staleness, schema parity, empty/failed accuracy | `--asset-group X --all --checks 1,2,3,4,5,6 --output-dir ...`                 |
| `market-tick-data-service/scripts/validate_manifest_coverage.py`            | Manifest coverage vs UAC instrument catalogue (false-missing rate per day/venue)                                                                 | `--asset-group X --all --start-date --end-date --fail-on-gap`                 |
| `market-data-processing-service/scripts/reconcile_1440_nan_placeholders.py` | NaN-ratio / 1440-NaN-bar placeholder detection (MDPS candles)                                                                                    | per-script args                                                               |
| `features-service/scripts/sports/honest_coverage_report.py`                 | Sports per-league / per-fixture-date coverage                                                                                                    | per-script args                                                               |

Supporting libs (in `unified-trading-library`): `honest_coverage_ratchet.py`, `manifest_completeness.py`,
`manifest_freshness.py`, `manifest_consolidator.py`.

**Fast path:** read the latest pre-computed daily report instead of recomputing —
`gs://central-element-323112-honest-coverage/{latest}/coverage.json`. ⚠️ Confirm `generated_at` is recent; the cron has
stalled before (see Open Findings).

---

## 2. Manual GCS spot-check recipe (ground-truth, complements the scripts)

Use when you need to eyeball actual shard output during a live backfill.

**(a) What's running**

```bash
gcloud compute instances list --project=central-element-323112 \
  --filter="status=RUNNING" --format="value(name,creationTimestamp)" | sort
```

**(b) Bucket + path layout** (flat, no-suffix bucket = canonical prod; `-prd/-test/-dev/-stg` are env variants):

```
gs://market-data-tick-{cefi,defi,tradfi,sports,prediction}-central-element-323112/
  raw_tick_data/by_date/day=YYYY-MM-DD/asset_group=<ag>/venue=<V>/instrument_type=<T>/data_type=<DT>/<SYMBOL>.parquet
  processed_candles/by_date/day=YYYY-MM-DD/timeframe=<TF>/data_type=<DT>/venue=<V>/<SYMBOL>.parquet
  _index/   _vm_staging/   backfill-logs/
```

**(c) Freshness — confirm the CURRENT fleet is writing (not a prior run):**

```bash
gcloud storage ls -l "gs://<bucket>/<...>/<DT>/" | head
# Compare the object write-timestamp against the VM creationTimestamp from (a).
# ⚠️ A date-partition EXISTING is NOT proof of freshness — it may be from a prior run.
```

**(d) Row count + NaN ratio — the silent-zero check (use the MTDS venv; workspace venv lacks pyarrow):**

```bash
PY=/active/unified-trading-system-repos/market-tick-data-service/.venv/bin/python3
gcloud storage cp "gs://<bucket>/<...>/<SYMBOL>.parquet" /tmp/s.parquet
"$PY" -c "import pyarrow.parquet as pq; t=pq.read_table('/tmp/s.parquet'); df=t.to_pandas(); \
print('rows',len(df)); print((df.select_dtypes('number').isna().mean()*100).round(1).to_dict())"
```

Pass: rows > 0, full-day time span, NaN% ~0 on price/volume fields. Sparse types (e.g. `liquidations`) legitimately have
few rows + small files — that is correct honest-coverage, not a failure.

**(e) Coverage formula** (matches `measure_honest_coverage.py`):

```
coverage_pct      = captured / (captured + attempted_failed + expected_unattempted)   # excludes empty_confirmed
all_shards_pct    = captured / total                                                   # includes empty_confirmed
```

---

## 3. Gotchas (learned the hard way — read before auditing)

- **High-cardinality asset groups (CME/tradfi) blow up recursive `ls`.** `gcloud storage ls -lr` over a tradfi date
  partition times out (thousands of instruments/day). Drill targeted paths, or use the manifest reader — never
  recursive-walk tradfi/CME.
- **DeFi is multi-bucket + mostly `empty_confirmed`.** `coverage_pct` can read 99.9% while `all_shards_pct` is ~19%
  because most DeFi shards are legitimately empty. Reading only one DeFi bucket is misleading — see `codex/02-data/`
  honest-coverage docs.
- **Partition existence ≠ data freshness.** A `day=2026-01-21/` partition can exist from a run weeks ago. Always check
  object write-time vs the current VM launch time.
- **Manifest status alone hides silent-zero.** Always pair with a parquet read (§2d).
- **Bucket SSOT:** resolve via `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name`; the flat
  no-suffix bucket is canonical prod.

---

## 4. 2026-05-18 baseline (last good daily coverage report)

| asset_group | coverage_pct | all_shards_pct | captured  | attempted_failed | empty_confirmed |
| ----------- | ------------ | -------------- | --------- | ---------------- | --------------- |
| cefi        | 49.54%       | 49.48%         | 1,302,686 | 1,326,949        | 3,296           |
| defi        | 99.91%       | 19.47%         | 312,731   | 288              | 1,293,171       |
| tradfi      | 94.85%       | 69.71%         | 98,573    | 5,351            | 37,477          |
| sports      | 100.0%       | 99.79%         | 157,174   | 0                | 326             |
| prediction  | 100.0%       | 86.19%         | 14,491    | 0                | 2,321           |

CeFi's 1.33M `attempted_failed` (≈ captured) is the gap the current 119-VM CeFi backfill is closing.

---

## 5. Open findings (investigate / confirm — append as discovered)

- **[2026-05-25] TradFi current VMs may not be writing canonical output.** The 8 `mdps-tradfi-*` VMs (launched 05-23,
  ~49h uptime) show an alive serial console (per-minute gsutil uploads) but NO `processed_candles` objects newer than
  2026-05-07 across sampled year-partitions (2020/2021/2024) — all from prior runs. Possible silent failure OR
  consolidation-pending OR run-tagged path. **Confirm via `audit_structural_checks.py --asset-group tradfi --checks 4`
  (shard staleness) before relying on tradfi.** If broken → file issue doc + relaunch.
- **[2026-05-25] Daily honest-coverage cron stale since 2026-05-18.** `gs://central-element-323112-honest-coverage/` has
  no report after 05-18 (likely paused during code-freeze/migration). The fast-path report is stale — recompute with
  `measure_honest_coverage.py` or restart the cron before trusting it.

---

## 6. Append new checks here

As deeper quality/integrity checks are discovered, add them above (§1 if scripted, §2 if manual, §3 if a gotcha) and log
them here with date + provenance:

- 2026-05-25 — initial version: existing-script inventory, manual GCS recipe, gotchas, 05-18 baseline, 2 open findings.
  (Harsh request to make this a repeatable audit.)
