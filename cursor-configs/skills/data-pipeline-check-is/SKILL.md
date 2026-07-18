---
name: data-pipeline-check-is
description:
  Run the instruments-service data-pipeline end-to-end smoke check for one operator-given day — Phase 0
  provisions/verifies the `-test-` buckets, Phase 1 proves force-refetch + skip-if-fresh for every MVP (asset_group,
  venue) shard, Phase 2 proves the live/MVP leg, then writes + prints the report path. Never invents `--day` — it must
  come from the operator. Composes with `/autonomous`'s no-pause contract — under `/autonomous`, loop to the next
  unchecked asset_group/venue instead of stopping at "done, what's next." Trigger on `/data-pipeline-check-is`, "run the
  IS pipeline check", "smoke-test instruments-service for <day>", "prove the IS backfill force/skip path works".
---

# /data-pipeline-check-is — instruments-service pipeline e2e smoke check

Proves, on real infrastructure (never mocks), that instruments-service's backfill path actually does three things a
`-test-`-bucket-only dev smoke test can't: (a) a genuinely-missing shard's adapter/download path really works when
`--force`d, (b) an already-captured shard's skip-if-fresh logic really fires and avoids a wasted re-download, (c) the
same holds in `--mode live`. Writes are **test-bucket-only** — this never mutates real captured production data.

**Shard atom (IS only)**: `(asset_group, venue, day)` — IS has no `--data-types`/instrument-level flag; per-venue
instrument-type coverage (SPOT_PAIR/PERPETUAL/FUTURE/OPTION/…) is a reporting dimension, never a separate shard key.
SPORTS shards are `(sports_provider, day)`.

## Read the VM run.log as ground truth, not the report verdict (added 2026-07-18)

**While the raw->canonical instrument-id migration is in flight, this check's pass/fail is actively misleading.** The
verification looks up a manifest row keyed on the sampled RAW symbol while the writer records the row under the
CANONICAL id, so it returns `manifest_status_invalid:no_matching_row` on shards that genuinely succeeded. Measured
2026-07-18: a full `--tardis-only` sweep reported `total=18 passed=1 failed=17` while **all 18 venues had written real
records** (DERIBIT 3396, OKX 2790, BYBIT 1188, ...). Anyone — or any cron — alerting on these verdicts would see
near-total failure where there is none.

Score a run from the VM `run.log` instead:

```
instruments: date=<DAY> wrote <N> records across <M> venues
Shard completeness OK: M/M venues written for date=<DAY>
```

A cell is genuinely OK when records > 0, completeness is OK, and there is no `Traceback`. Full evidence + the fix
dependency: `issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md` (the downloader-side
fix shipped as `market-tick-data-service@687abd54`).

For THROUGHPUT measurement pitfalls (this check cannot measure throughput — it is boot-dominated), see the matching
section in the `data-pipeline-check-mtds` skill.

## 0. `--day` is REQUIRED — never synthesize one

This check is meaningless without a real target day. If the invoking prompt doesn't carry an explicit
`--day YYYY-MM-DD`, **stop and ask the operator for one** before doing anything else — do not default to "today" or any
other synthetic date. A smoke check silently run against the wrong day proves nothing and wastes real VM spend.

## 1. Composing with `/autonomous`

- **Invoked plainly** (`/data-pipeline-check-is --day 2026-07-09`): run Phases 0→3 once through the full MVP
  (asset_group, venue) matrix for that day, then stop and report.
- **Invoked under `/autonomous`** (e.g. `/autonomous /data-pipeline-check-is --day 2026-07-09`): first read
  `cursor-configs/AUTONOMOUS_AGENT_RULES.md` + `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` per that skill's contract,
  then run this workflow on the self-paced loop — see step 6. The no-pause / no-`DEFERRED` completion contract applies:
  don't stop mid-matrix to ask "should I continue?"

## 2. Phase 0 — provisioning gate (a real check, not an assumption)

`get_write_bucket_name()` rewrites to `-test-{pid}` on `IS_TEST_RUN=true` but does **not create** the bucket — the
`-test-` sibling for `instruments-store-*` is not pre-declared in `bucket_config.yaml`. Verify all 5 asset groups before
targeting any of them for the first time:

```bash
PROJECT_ID="central-element-323112"
for ag in cefi defi tradfi sports prediction; do
  bucket="instruments-store-${ag}-test-${PROJECT_ID}"
  if gcloud storage buckets describe "gs://${bucket}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    echo "OK   gs://${bucket}"
  else
    echo "GAP  gs://${bucket} — MISSING, provisioning gate fails for ${ag}"
  fi
done
```

- A missing bucket is a **real audit finding** — provision it (mirroring the PROD sibling's region/storage class), never
  silently skip the asset_group:

```bash
gcloud storage buckets create "gs://instruments-store-${ag}-test-${PROJECT_ID}" \
  --project="${PROJECT_ID}" --location=asia-northeast1 --uniform-bucket-level-access
```

- Do not advance an asset_group into Phase 1 until its `-test-` bucket exists.

## 3. Phase 1 — batch force + skip matrix

For each MVP `(asset_group, venue)` cell for `--day` (MVP scope from
`unified_api_contracts.canonical.crosscutting.mvp_scope.is_mvp()`):

```bash
cd instruments-service && python3 scripts/pipeline_e2e_check.py \
  --asset-group <AG> --venue <VENUE> --day <DAY> --legs force,skip
```

> **Doc-fix (2026-07-18): the checker's own flag is `--venue` (singular), never `--venues`.** `--venues` is the
> LAUNCHER's flag (`launch-instruments-backfill-vm.sh`) — passing it to `scripts/pipeline_e2e_check.py` itself errors
> `unrecognized arguments`.

This sequences, per shard, via the shared `unified_trading_library.pipeline_e2e_check` engine:

1. **force-leg**: launches
   `launch-instruments-backfill-vm.sh --asset-group <AG> --venues <VENUE> --start <DAY> --end <DAY> --vm-name instr-backfill-<AG>-pipelinecheck-<run_ts> --test-run --force`;
   polls the VM's `EXIT_STATUS`/`run.log` GCS observability contract to a terminal state; on `SUCCESS` verifies the
   test-bucket parquet is (re)written and the manifest row shows `captured`.
2. **skip-leg** (same shard, no `--force`): confirms the freshness-preflight skip signal appears in `run.log` and that
   the test-bucket object's fingerprint (generation + `updated`) is **unchanged** from the force-leg. IS's skip-leg is
   self-contained — `IS_TEST_RUN=true` routes **both** the freshness read and the write to the same `-test-` bucket, so
   a force-run-then-skip-run pair on one shard is a genuine, complete proof (no PROD pre-check needed here, unlike
   MTDS).

### 3a. TradFi-only, ALL shards — Phase D terminal gate (added 2026-07-18)

Per `tradfi_consolidated_closeout_2026_07_18.md` Phase D — the plan's **terminal gate**, run together with
`data-pipeline-check-mtds`'s own tradfi-only sweep (§3c there): post-migration, prove force-refetch + skip-if-fresh
across **every** tradfi shard before any real MVP backfill runs.

**IS's tradfi shard atom is just `(venue, day)`** — all 7 tradfi venues (`NASDAQ`, `NYSE`, `CME`, `ICE`, `CBOE`, `KRX`,
`FX`), no `data_type` axis (IS has none). Run one shard per venue for the same `--day`:

```bash
cd instruments-service && python3 scripts/pipeline_e2e_check.py \
  --asset-group TRADFI --day <DAY> --legs force,skip
```

Repeat with `--venue <V>` for each of the 7 venues (or omit `--venue` to enumerate all of them in one run, per
`enumerate_cells()`'s existing TRADFI coverage).

**Known gap (2026-07-18, code-confirmed, out of this skill's own scope to fix):** unlike the MTDS engine, IS's
`scripts/pipeline_e2e_check.py` does **not yet** support `--require-captured`/`--auto-day`/`--mvp-only` — it always
force-checks the literal `--day` you pass, on every enumerated venue, with no "skip an unprovable cell" safety net.
Reference-data catalogue snapshots are largely day-insensitive, so this is usually fine, but if a specific venue was
genuinely never captured on `--day` you will see a real `no_matching_row`/`manifest_status_invalid` failure rather than
an honest `skipped`. Either pick a `--day` known to have IS coverage for all 7 tradfi venues, or read the VM `run.log`
(§ "Read the VM run.log as ground truth" above) before treating a failure as real. Adding `--require-captured`/
`--auto-day` parity to the IS engine is a tracked follow-up (`tradfi_consolidated_closeout_2026_07_18.md` Phase D), not
yet shipped as of this doc revision.

**Green definition (the plan's Phase D exit criterion, IS half):** every one of the 7 tradfi venues carries a `passed`
force + skip verdict for `--day`. Combined with `data-pipeline-check-mtds`'s green tradfi-only, all-shards run
(including its `canonical` leg — IS has no canonical-shape leg of its own; the shape assertion runs against the MTDS
manifest + the IS catalogue is covered by the plan's separate Phase B catalogue-migration self-verify, not this
checker), that is what "tradfi is code-complete, migrated, honestly-covered, and verified" means.

## 4. Phase 2 — live leg (MVP-scoped)

```bash
cd instruments-service && python3 scripts/pipeline_e2e_check.py \
  --legs live --mvp-only --day <DAY>
```

- Same launcher, `--test-run`, scoped to MVP venues only. No separate force/skip split on this leg — `--mode live`
  already always forces (`_adapter.py:158`).

## 5. Write + present the report — do not just point at the file

`report.write_report()` emits a markdown + sibling JSON pair; the script itself prints the **full rendered report**
(pass/fail table + the bucket-path table below) to stdout on exit, not just the file path:

```
report written to plans/audit/results/data_pipeline_e2e_check_is_<YYYY_MM_DD>.md

<full markdown: frontmatter, summary, Results table, Bucket paths table, Failed/Ambiguous sections>
```

- **Relay this printed content directly to the operator in your response — do not say "done, see the report" and make
  them go open the file.** The report's "Bucket paths" table (auto-generated, not hand-built) shows exactly which bucket
  the parquet write and the manifest write/read each targeted per shard/leg — for IS these should always match (fully
  test-bucket self-contained, plan finding #2); a mismatch here would itself be a real finding, not expected behavior.
- Every shard cell must carry a force-verdict and a skip-verdict; every MVP venue must carry a live-verdict. A cell with
  neither is not "skipped" — it's a gap, and belongs on the next tick (see step 6) or as a flagged gap in the report.

## 6. Under `/autonomous` — loop, don't stop at "done, what's next"

- After Phase 2 + report emission for the current `(asset_group, venue)` cell, do **not** report "done" and wait for the
  next instruction.
- Pick the **next unchecked** `(asset_group, venue)` cell in the MVP matrix for the same `--day` and repeat Phases 1→2
  for it, appending to (never overwriting) the same day's report.
- Only stop the loop once **every** MVP `(asset_group, venue)` cell for `--day` carries a force + skip + live verdict —
  then print the final report path and a one-line matrix-completion summary (cells proved / cells with gaps).
- A flat progress metric (no new cell proved across a tick) is a STALL — diagnose (`gh run view --log-failed`-style VM
  log inspection), don't repeat the same failing launch.

## Extending to a new service

Copy this file, swap: the per-service script path (`<service>/scripts/pipeline_e2e_check.py`), the launcher script name,
the shard atom (IS = `(asset_group, venue, day)` — a new service defines its own), the MVP predicate, and the
sampled-instrument-id source. The shared engine (`unified_trading_library.pipeline_e2e_check`) and this skeleton never
change — see the `data-pipeline-check-mtds` skill for the sibling that already differs on shard atom (6-tuple incl.
`data_type`) and skip-leg proof (PROD pre-check required).

## Measuring throughput for ANY asset_group — use the network-RX counter (added 2026-07-18)

**Completion-based numbers are not throughput.** Do NOT derive MB/s from `Tardis streaming success` lines, parquet
bytes, rows/s, or this check's own timings — all of them credit work only when a shard COMPLETES, so with hundreds of
large shards in flight they collapse exactly when concurrency is working hardest, and parquet output is not comparable
across venues (DERIBIT runs 2-3M rows/shard compressing to ~6.5 MB vs bybit-spot ~289k rows at ~8.3 MB). On 2026-07-18
that instrument produced four successive wrong answers — 15-16 -> 13.5 -> 11.5 -> 9.4 MB/s — for a cefi backfill VM
whose ACTUAL sustained rate, measured off the wire, was **4.15 MB/s**.

**The canonical measure (works for every asset_group, no ssh needed — IAP is often unavailable):**

```bash
bash deployment-service/scripts/vm/measure-vm-throughput.sh <vm-name> [zone] [project] [startRFC3339]
```

It reads `compute.googleapis.com/instance/network/received_bytes_count` from Cloud Monitoring and reports total GB,
**mean (the sustained rate to quote)**, peak minute, and a per-5min profile. Window defaults to the VM's
`creationTimestamp`, so the whole run is covered.

Rules when reporting a throughput figure for any asset_group:

- Quote the **MEAN over the whole run**, never a peak minute or a short window.
- **Always show the per-5min profile** — it reveals ramps and collapses an average hides. The 2026-07-18 cefi run ramped
  to ~12.8 MB/s for ~15 min then fell to ~2-3 MB/s for the next 50; the mean alone (4.15) hides both.
- RX is **compressed bytes off the wire** (Tardis serves `.csv.gz`) — a DIFFERENT quantity from parquet output. Never
  compare an RX figure against a parquet-derived baseline; state which one any target refers to.
- RX covers the whole interface, so it includes small non-fetch traffic (catalogue/manifest reads). Uploads are TX, so
  they do not inflate it.
- If the metric returns no data (VM younger than ~3 min — Monitoring lags), report the number as **UNMEASURED**. Do not
  substitute a completion-derived figure.

## Not wired into `quality-gates.sh`

This check does real I/O + real VM spend + multi-minute-plus runtime — it stays a standalone, on-demand skill
(cron-schedulable later via the `schedule` skill), never part of `instruments-service/scripts/quality-gates.sh`.
