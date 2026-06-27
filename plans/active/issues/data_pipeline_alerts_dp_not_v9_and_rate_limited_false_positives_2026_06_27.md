---
title: DP_NOT_V9 + DP_SOURCE_RATE_LIMITED data-pipeline alerts are false-positives (string-vs-int compare + over-broad rate-limit regex + consolidation-lag captured count)
created: 2026-06-27
source:
  - "Slack #data-pipeline-alerts 2026-06-27 08:25/08:32 (DP_SOURCE_RATE_LIMITED sports-ref-v3-1 + RESOLVED)"
  - "Slack #data-pipeline-alerts 2026-06-27 09:02 (DP_SOURCE_RATE_LIMITED instr-backfill-tradfi-ice-20260627-075400)"
  - "Slack #data-pipeline-alerts 2026-06-27 09:02 (DP_NOT_V9 cefi / defi / tradfi)"
locked_by: live-defi-rollout
priority: P2
status: active
---

## TL;DR

Five alerts fired this morning. **None of them are real data loss.** Two distinct alerting bugs:

1. **`DP_NOT_V9` (cefi/defi/tradfi)** — the audit reports "N/N rows non-v9" while its own distribution shows the
   majority ARE v9. Caused by a **string-vs-int comparison** (`schema_version` is a string column, compared to the int
   `9`). Behind that false count there is a **small REAL residual** (rows whose `schema_version` is empty / a legacy
   '4'/'5'/'6' / a contaminated source-name or instrument-key) that the bug currently buries.
2. **`DP_SOURCE_RATE_LIMITED` (sports-ref-v3-1, instr-backfill-tradfi-ice-…)** — both VMs exited `rc=0` and actually
   wrote data; neither run.log shows an HTTP-429. The "rate limited / flat captured 0→0" verdict is a false-positive
   from (a) an over-broad rate-limit regex, (b) RATE_LIMITED out-ranking the PROGRESS/HONEST_ABSENCE signals, and (c) a
   consolidation-lag "captured 0→0" trigger for short-lived self-deleting backfill VMs.

Data is fine. These are observability bugs that train operators to ignore the channel.

---

## Finding 1 — `DP_NOT_V9`: string-vs-int compare flags 100% of rows as non-v9

### Evidence (from the alerts)
- `cefi: count=5040874 — 5040874/5040874 rows non-v9; dist={'9': 4678549, '5': 180089, '6': 136374, '4': 33398, '': 12464}`
- `defi: count=8481830 — 8481830/8481830 rows non-v9; dist={'9': 7389546, 'onchain_subgraph': 735533, 'onchain_rpc': 333043, 'pyth_hermes': 12203, 'hyperliquid': 10517, '6': 988}`
- `tradfi: count=2536166 — 2536166/2536166 rows non-v9; dist={'9': 2437690, '': 88417, '4': 8343, 'NASDAQ:ETF:ETHA': 460, 'NYSE:EQUITY:LLY': 36, … (60+ instrument keys)}`

The count says **100% non-v9**, but each distribution shows `'9'` is the **dominant** value (cefi 93%, defi 87%,
tradfi 96%). The report contradicts itself.

### Root cause (confirmed)
- [`e2e-testing/scripts/audit/manifest_hygiene_daily.py:65`](e2e-testing/scripts/audit/manifest_hygiene_daily.py#L65)
  `_CANONICAL_SCHEMA_VERSION = 9` — an **int**.
- [`e2e-testing/scripts/audit/manifest_hygiene_daily.py:107`](e2e-testing/scripts/audit/manifest_hygiene_daily.py#L107)
  `non_v9 = int((df["schema_version"] != _CANONICAL_SCHEMA_VERSION).sum())`.
- [`e2e-testing/scripts/audit/_dp_common.py:170`](e2e-testing/scripts/audit/_dp_common.py#L170) reads the parquet raw
  (`pd.read_parquet(...)`) with **no dtype coercion** for `schema_version`. The dist keys (`'9'`, `'5'`, `''`, …) prove
  the column is **object/string** dtype.
- Therefore `df["schema_version"] != 9` is element-wise `str != int` → **`True` for every row** → `non_v9 == len(df)`.

This is the same class of bug observed (separately) in the tradfi run.log this morning:
`WARNING Handler InstrumentsHandler failed on payload 24: '<' not supported between instances of 'str' and 'int'`.

### The REAL residual the bug hides (do NOT lose this)
After fixing the compare to normalise types, the TRUE non-v9 counts are:

| AG     | true non-v9 | of total | what the non-'9' values are |
|--------|-------------|----------|------------------------------|
| cefi   | ~362,325    | ~7%      | legacy `'4'/'5'/'6'` + `''` (empty) |
| defi   | ~1,092,284  | ~13%     | source-names `onchain_subgraph/onchain_rpc/pyth_hermes/hyperliquid` + legacy `'6'` |
| tradfi | ~98,476     | ~4%      | `''` (empty) + legacy `'4'` + instrument-keys `NASDAQ:ETF:ETHA`, `NYSE:EQUITY:LLY`, … |

Two sub-classes inside that residual:
- **Legacy stragglers** (`'4'/'5'/'6'`) — pre-canonicalisation rows the audit is *supposed* to flag; legitimately need
  a re-canonicalisation pass. This is the audit working as intended.
- **Contaminated `schema_version`** (source-names for defi, instrument-keys for tradfi, empty `''`) — these are NOT
  schema versions; a source/instrument-key field bled into the column.

### Contamination root cause (investigated 2026-06-27 — CONFIRMED write-side, current writer CLEAN)
- The **current UTL writer is clean**: `schema_version=MANIFEST_SCHEMA_VERSION` (int `9`) is set BY NAME on every write
  path — `record_captured` ([`_writer_captured.py:367`](unified-trading-library/unified_trading_library/manifest_writer/_writer_captured.py#L367)),
  `add()` ([`_writer_ingest.py:355`](unified-trading-library/unified_trading_library/manifest_writer/_writer_ingest.py#L355)),
  the serializer ([`_writer_io.py:475`](unified-trading-library/unified_trading_library/manifest_writer/_writer_io.py#L475)).
  No positional/column-order risk remains, so NEW captures are correct. The contamination is **not being re-introduced
  by the live writer.**
- The contaminated values are **persisted on disk** in the consolidated `_index/availability_index.parquet`; the audit
  reads them faithfully (read-side is innocent — [`_dp_common.py:170`](e2e-testing/scripts/audit/_dp_common.py#L170) is a
  plain `read_parquet`, no rename/reorder).
- Historical origin: (a) the **pre-2026-06-16 `_records_to_dataframe` serializer** silently dropped `source` /
  `pipeline_mode` / `transport` / `instrument_id` columns (fixed as of 2026-06-16, documented in `_writer_io.py`); and
  (b) **old positional GCS-hive-path rebuild scripts** (defi/tradfi) that built rows from parsed object paths and
  misaligned columns, bleeding `source` (defi → `onchain_subgraph`…) and `instrument_id` (tradfi → `NASDAQ:ETF:ETHA`…)
  into the `schema_version` position. CeFi has no per-instrument hive path → no contamination, only genuine legacy
  numbers.
- **Remediation = re-run the existing `populate_v9_index_columns_inplace.py`**
  ([`market-tick-data-service/.../scripts/populate_v9_index_columns_inplace.py:178`](market-tick-data-service/market_tick_data_service/scripts/populate_v9_index_columns_inplace.py#L178))
  with `--apply` against the defi + tradfi index buckets — its `not_v9 = str(v) != "9"` filter catches every contaminated
  row. **⚠ Prerequisite before any `--apply`**: verify a sample of contaminated rows is a *single-column* contamination
  (only `schema_version` is wrong) vs a *full-row positional shift* (other columns also misaligned). If the whole row is
  shifted, bumping `schema_version=9` would MASK a deeper corruption — those rows need re-derivation, not a version bump.
  This is a **prod-manifest-mutating, operator-gated** real-infra op (needs GCS read of actual rows, which this slot
  can't safely do), so it is surfaced to the operator below rather than auto-applied.

---

## Finding 2 — `DP_SOURCE_RATE_LIMITED`: clean rc=0 runs misclassified as throttled

### Evidence (from the alerts)
- **sports-ref-v3-1**: `Exit code: 0`, manifest `198 total entries, 198 new`, `wrote empty_confirmed for 4
  fixture-dependent entities`, `0 injuries returned by API`, `all canonical leagues captured`, `PROGRESS: chunk=25/25`,
  then `VM_SHUTDOWN_ON_COMPLETION` self-delete. **No HTTP-429 anywhere in the trace.** → auto-`RESOLVED` 7 min later.
- **instr-backfill-tradfi-ice-…**: `Exit code: 0`, `instruments: date=2026-06-25 wrote 1 records across 1 venues`,
  manifest `81 total entries, 7 new, process_final=True`, `Shard completeness OK: 1/1 venues written`. **Wrote data;
  no 429.** Yet the alert says "drained with a flat captured count (0 → 0)".

### Root cause (verified — it is the CLASSIFIER, not the captured count)
The "flat captured 0→0" is **correct**, not a lag bug: `_make_captured_reader`
([`cli.py:251`](deployment-service/deployment_service/data_pipeline_monitors/cli.py#L251)) already reads the **per-VM
shard** `_index/per_vm/{vm}.parquet` and counts only `capture_status == "captured"` rows. Both VMs legitimately wrote
**honest-absence / sentinel** rows, not captured rows — sports backfilled zero-fixture 2022 dates (`wrote
empty_confirmed`), tradfi-ice seeded the target universe (`wrote expected_unattempted`) — so 0 *captured*-status rows is
the right answer. The bug is purely in `classify_no_capture_reason`:

1. **`_RATE_LIMIT_RE` is over-broad.**
   [`_gcs.py:511-517`](deployment-service/deployment_service/data_pipeline_monitors/_gcs.py#L511) — the bare
   `rate.?limit(ed)?` alternative matches any benign rate-limiter config / backoff-budget / telemetry line, and the
   alternation literally includes the event name `DP_SOURCE_RATE_LIMITED`, so the regex **self-matches** on a heartbeat /
   prior-alert / comment echo. Either match → RATE_LIMITED on a clean run with no actual 429.
2. **The 4-state honest-absence writes weren't recognized.**
   [`_gcs.py:491-510`](deployment-service/deployment_service/data_pipeline_monitors/_gcs.py#L491) `_HONEST_ABSENCE_RE`
   did not match `empty_confirmed` / `expected_unattempted` / `Zero-fixture fast path`. So even WITHOUT the rate-limit
   mismatch, the sports run (no "Wrote N rows" progress line) would have fallen through to `SILENT` →
   `DP_VM_GONE_NO_CAPTURE` — a *different* false positive. The classifier had no signal for "the writer recorded honest
   absence".

Net: a clean backfill VM doing legitimate honest-absence work pages `DP_SOURCE_RATE_LIMITED` (regex mismatch) and would
otherwise page `DP_VM_GONE_NO_CAPTURE` (unrecognized absence). The captured-count machinery is fine; precedence is left
as-is (a genuine 429 still correctly out-ranks a benign-absence phrase).

---

## Why it matters
Both alert classes fired on healthy runs during normal backfill load. Recurrent false-positives train operators to mute
`#data-pipeline-alerts`, which masks a REAL future catalog/consolidator/schema failure. Same robustness theme as the
2026-06-24 transient-GCS false-positive issue (`data_pipeline_alert_transient_gcs_pressure_false_positives_2026_06_24.md`).
Independently, the `DP_NOT_V9` bug is also **hiding a real ~4–13% non-v9 residual** behind a "100%" cry-wolf number.

## Recommended decision (none urgent — data is not at risk)

### Finding 1 — DP_NOT_V9 (alert truthfulness — SHIPPED `e2e-testing@21ce846`, QG green 81s)
- [x] ✅ [CODE] P2. Normalise the schema_version compare so the count is truthful — `astype("string").str.strip()`,
  strip a float `.0`, treat empty/NaN as non-v9, compare against `str(_CANONICAL_SCHEMA_VERSION)`. —
  `e2e-testing` `manifest_hygiene_daily._check_v9`. + 2 regression tests (string-dtype `'9'`/`''`/source-name; all-'9'
  is clean) in `test_dp_audit.py`.
- [x] ✅ [CODE] P2. Make the alert ACTIONABLE — the `_check_v9` sample now splits the non-v9 residual into
  `legacy_version` (numeric `4/5/6/8` → re-canonicalise) vs `missing` (empty) vs `contaminated` (source-name /
  instrument-key → writer root-cause), so an operator sees which class it is. — `e2e-testing` audit.

### Finding 1 — DP_NOT_V9 (real residual — OPERATOR-GATED real-infra op)
- [ ] [DATA] P2. **Operator decision (prod-manifest mutation):** clean the contaminated defi/tradfi `schema_version`
  rows. Recommended = re-run `populate_v9_index_columns_inplace.py --apply` on the defi + tradfi index buckets — BUT
  first verify a sample of contaminated rows is single-column (only `schema_version` wrong) and not a full-row
  positional shift (see Contamination root cause above). Needs GCS access + a snapshot before mutating. **Surfaced to
  operator — not auto-applied from this slot.**

### Finding 2 — DP_SOURCE_RATE_LIMITED (classifier — SHIPPED `deployment-service@d36f281`, QG green 98s)
- [x] ✅ [CODE] P2. Tighten `_RATE_LIMIT_RE` to genuine throttle signals only (HTTP-429 / "Too many requests" / "quota
  exceeded" / "rate limit" qualified by an error/retry context / throttled); DROP the bare `rate.?limit(ed)?` substring
  and the self-referential `DP_SOURCE_RATE_LIMITED` token. — `deployment-service` `_gcs.py`.
- [x] ✅ [CODE] P2. Recognize the writer's 4-state honest-absence/sentinel writes as HONEST_ABSENCE — add
  `empty_confirmed` / `expected_unattempted` / `Zero-fixture fast path` to `_HONEST_ABSENCE_RE` so a backfill that hit
  genuinely empty cells is benign, not GONE_NO_CAPTURE. Precedence left UNCHANGED (a genuine 429 still out-ranks a
  benign-absence phrase). — `deployment-service` `_gcs.py`.
- [x] ✅ [TEST] P2. Regression tests in `test_data_pipeline_monitors.py`: empty_confirmed/expected_unattempted →
  HONEST_ABSENCE; a benign "rate limiter configured" line + the literal `DP_SOURCE_RATE_LIMITED` echo → NOT
  RATE_LIMITED; genuine 429 / "quota exceeded" / "rate limit exceeded" → still RATE_LIMITED.

### Secondary (observed, out of alert scope)
- [ ] [CODE] P3. `InstrumentsHandler failed on payload 24: '<' not supported between instances of 'str' and 'int'`
  (tradfi ICE run.log 07:58:04) — a str/int comparison bug in the instruments handler (same bug class as DP_NOT_V9);
  non-fatal (rc=0) but it dropped payload 24. — `instruments-service` `InstrumentsHandler`.

## Codex SSOTs
- `codex/05-infrastructure/data-pipeline-alerts.md` (DP-MANIFEST-* + daily digests)
- `codex/02-data/availability-manifest-and-data-status.md` ("trust the actual distribution, not the constant")
- `codex/04-architecture/autonomous-recovery-matrix.md` (DP_SOURCE_RATE_LIMITED backoff actuator)
