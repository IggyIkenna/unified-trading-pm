---
name: data-pipeline-check-mdps
description:
  Run the market-data-processing-service (MDPS) candle-derivation pipeline end-to-end smoke check for one operator-given
  day — Phase 0 verifies the `-test-` buckets, Phase 1 proves force-recompute + skip-if-fresh for every MVP candle shard
  (asset_group × venue × instrument_type × data_type × timeframe) across ALL asset_groups, a canonical leg asserts the
  derived candles carry canonical paths/ids (non-canonical data is SKIPPED, never legacy-passed — it becomes migration
  work), and an opt-in benchmark leg measures amortized per-shard-day throughput and projects full-history backfill time
  + SPOT compute cost + parallelization headroom. Never invents `--day`. Composes with `/autonomous`'s no-pause
  contract. Trigger on `/data-pipeline-check-mdps`, "run the MDPS pipeline check", "smoke-test
  market-data-processing-service for <day>", "prove the candle derivation force/skip path works", "how long to backfill
  all candles".
---

# /data-pipeline-check-mdps — MDPS candle-derivation pipeline e2e smoke check

Proves, on real infrastructure (never mocks), that MDPS's candle-derivation path actually does what a dev-local
`smoke_matrix.py` run can't: (a) a genuinely-derivable shard's tick→candle path really works when `--force`d, (b) an
already-fresh shard's skip-if-fresh logic really fires and avoids wasted recompute, (c) the derived candles carry
**canonical** paths/ids, and (d) how long a full-history backfill would actually take and cost. Writes are
**test-bucket-only** — this never mutates real production candles. Reads of PROD raw ticks (the derivation INPUT) are
read-only.

**Shard atom (MDPS)**: `(asset_group, venue, instrument_type, data_type, timeframe)` + `day`. `instrument_type` is
INFERRED by the writer from the raw-tick partition / canonical id — it is not a CLI axis. One VM launch covers a
`(asset_group, venue, data_type, day)` cell and derives **every valid timeframe** for it; each timeframe is then
verified as its **own** `ShardCheckResult`. Sports adds a `league_id` reporting dimension.

**The MDPS/MTDS asymmetry that makes the skip proof SELF-CONTAINED (unlike MTDS)**: MDPS's freshness gate
(`check_shard_freshness(bucket=<output bucket>, service_name="market-data-processing-service", …)`,
`orchestration_service.py:192`) reads the **same bucket it writes**. Routing output to the `-test-` sibling via
`--output-bucket` therefore routes BOTH the write and the freshness read there — so a force-run-then-skip-run pair on
one shard is a genuine, complete proof (like `data-pipeline-check-is`, unlike MTDS whose freshness read is PROD-scoped).
What still must be PROD-verified is the **INPUT**: the raw ticks the derivation consumes.

## 0. `--day` is REQUIRED — never synthesize one

This check is meaningless without a real target day. If the invoking prompt doesn't carry an explicit
`--day YYYY-MM-DD`, **stop and ask the operator for one** — do not default to "today". A smoke check run against a day
with no captured raw ticks proves nothing and burns real VM spend.

## Modes

- **Interactive (default, operator present)**: "Invoked plainly" below — run once through the scoped candle-shard matrix
  for the given `--day`, stop, report.
- **Autonomous / AO-dispatched**: "Invoked under `/autonomous`" below — no-pause loop per step 7. `--day` still MUST
  come from the operator or the dispatching plan/task in either mode — this skill never invents it.

**ASK > PARK when the operator is reachable** (same calibration as `/plan-reconcile`): a genuine ambiguity this skill
can't resolve deterministically (BLOCKED-CREDENTIALS, an infra outage vs. a real regression) gets asked directly if the
operator is in the session, and parked as a `BLOCKED-OPERATOR-DECISION` issue-doc entry only when nobody's reachable —
never silently guessed at or skipped either way.

## 1. Composing with `/autonomous`

- **Invoked plainly**: run Phases 0→2 once through the scoped matrix for that day, then stop and report.
- **Invoked under `/autonomous`**: first read `cursor-configs/AUTONOMOUS_AGENT_RULES.md` +
  `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`, then run this workflow on the self-paced loop (step 7). The no-pause /
  no-`DEFERRED` contract applies — don't stop mid-matrix to ask "should I continue?".

## 2. Phase 0 — provisioning gate (a real check, not an assumption)

MDPS candles are **co-located in the MTDS tick bucket** (`market-data-tick-{ag}-{env}-{pid}`) under a different object
prefix — there is no separate candle bucket. So the `-test-` siblings are the same ones MTDS uses.

> **⛔ NEVER gate on `gcloud storage buckets describe` / `gsutil ls -b`.** Both need `storage.buckets.get`, which
> `unified-trading-sa` does NOT have (object-level read/write only) — a describe-based gate false-negatives EVERY bucket
> and provisioning on it creates DUPLICATES. Use an OBJECT-level probe, which distinguishes MISSING (404) from
> EXISTS-but-EMPTY (the legitimate state of an unwritten `-test-` sibling):

```bash
PROJECT_ID="central-element-323112"
for ag in cefi defi tradfi sports; do
  bucket="market-data-tick-${ag}-test-${PROJECT_ID}"
  out=$(gsutil ls "gs://${bucket}/**" 2>&1 | head -1)
  case "$out" in
    *NotFound*|*404*|*"does not exist"*)  echo "GAP  gs://${bucket} — MISSING" ;;
    *"matched no objects"*|"")            echo "OK   gs://${bucket} (exists, empty)" ;;
    *AccessDenied*|*403*)                 echo "??   gs://${bucket} — 403 on objects; escalate, do NOT provision blind" ;;
    *)                                    echo "OK   gs://${bucket} (exists, has objects)" ;;
  esac
done
# prediction uses the SHORT form:
gsutil ls "gs://market-data-tick-pred-${PROJECT_ID//x/x}/**" >/dev/null 2>&1  # bucket: market-data-tick-pred-test-<pid>
```

Verified 2026-07-20: all five (`cefi/defi/tradfi/sports` + `pred`) exist. A missing bucket is a real audit finding —
provision it mirroring the PROD sibling (`--location=asia-northeast1 --uniform-bucket-level-access`), never silently
skip the asset_group.

## 3. Phase 1 — force + skip matrix

```bash
cd market-data-processing-service && python3 scripts/pipeline_e2e_check.py \
  --day <DAY> --legs force,skip --require-captured --auto-day \
  [--asset-group CEFI] [--venue BINANCE-FUTURES] [--data-types trades]
```

> **⛔ ALWAYS pass `--require-captured` (and normally `--auto-day`). SCOPE THE RUN.** The canonical MVP enumeration is a
> `venue × instrument_type` cartesian product (that is `mdps_mvp_universe`'s UAC definition) crossed with
> candle-producing data_types and their valid timeframes: measured 2026-07-20 that is **447 cells all-AG / 267
> defi-only**. An unscoped `--legs force,skip` run without `--require-captured` would launch **~447 force + ~447 skip
> VMs**. `--require-captured` prunes to cells whose raw-tick INPUT is genuinely captured (the only provable ones);
> `--auto-day` substitutes, per cell, the most recent day that actually has captured input (preferring a
> non-first-of-month day). Always additionally scope with `--asset-group` / `--venue` / `--data-types` for a targeted
> run.

**MDPS is NOT subject to the Tardis N=1 cap.** MDPS reads already-captured ticks from GCS and writes parquet — it never
fetches from a vendor, so it has no shared-IP constraint. Candle cells may run **fleet-wide in parallel** (bounded only
by cost and GCS read bandwidth), unlike the strictly-serial MTDS cefi download path. This is the single biggest
throughput lever (see §5).

Per shard the driver sequences, via the shared `unified_trading_library.pipeline_e2e_check` engine:

1. **Resolve the day**: reads the raw-tick INPUT manifest (`market-data-tick-{ag}-prd-{pid}`, filtered
   `capture_status=="captured"` AND `service_name=="market-tick-data-service"`), grouped by `(venue, data_type)` →
   newest-first captured days. `--require-captured` skips a cell with no captured input
   (`skipped: no_captured_input_for_cell`) rather than launching a VM that can only produce a false failure.
2. **force-leg**: launches
   `launch-mdps-backfill-vm.sh <ag> <DAY> <DAY> full --venues <V> --data-types <DT> --output-bucket market-data-tick-<ag>-test-<pid> --vm-name mdps-backfill-<ag>-pipelinecheck-<ts>-<slug> --force`;
   polls the VM's `EXIT_STATUS`/`run.log` GCS observability contract to a terminal state; on `SUCCESS` verifies the
   test-bucket candle parquet exists on the **canonical** path and the manifest row shows `captured`/`empty_confirmed`.
3. **skip-leg**: same shard, no `--force`; confirms the freshness-preflight skip signal
   `"SKIP date=%s category=%s: already fresh in manifest (use --force)"` (`orchestration_service.py:243`, regex-escaped
   before matching — its `(use --force)` parentheses are regex-significant) appears in `run.log`, AND that the
   test-bucket object's fingerprint (etag+crc32c+updated+size) is **unchanged** from the force-leg. Because the
   freshness read and the write both target the `-test-` bucket, this skip proof is **genuine and self-contained** — no
   PROD pre-check needed.

**Canonical output contract the verify asserts** (LOCKED shape, operator-corrected ruling 2026-07-21; per
`canonical_writer.py` / `output_path_helpers.py`):

```
processed_candles/by_date/day={DAY}/pipeline_mode={pm}/timeframe={TF}/data_type={SOURCE_dt}/instrument_type={IT}/venue={V}/[underlying={U}/]{instrument_id}.parquet
```

- `data_type={SOURCE_dt}` is the **shard's raw SOURCE data_type** (`trades`, `book_snapshot_5`, `derivative_ticker`, …)
  — **NOT** `mdps_data_type_key(src, tf)` (the aggregated key, e.g. `ohlcv_1m`/`book5_ohlcv_5m`/`deriv_ohlcv_1h`).
  Keeping SOURCE on the path was the CORRECTED 2026-07-21 ruling (supersedes the original Option-A framing, which wanted
  the aggregated key); the manifest row is likewise overridden to the SOURCE value right before `record_captured`, so
  path==manifest holds on the SOURCE axis. The `timeframe` is normalised `24h`→`1d`. `instrument_type=` is **required**
  on this declared/canonical template but only **tolerated** (not required) by the force/skip legs' measured template —
  a not-yet-migrated legacy object still on disk during the P7 migration window lacks it and correctly fails the
  canonical leg (`missing_segment=instrument_type`) while still passing force/skip.
- **SPORTS writes under `processed/`**, not `processed_candles/`.
- Manifest verify matches
  `{service_name: "market-data-processing-service", venue, data_type: <shard SOURCE data_type>, timeframe: normalized}`
  - `date` on the **test** bucket (never PROD) — matching the aggregated key here silently finds zero rows for any shard
    where `mdps_data_type_key(source, tf) != source`.

### 3a. Canonical-paths principle — non-canonical data is SKIPPED, never legacy-passed (HARD)

Enumeration and verification are built off the **expected canonical** paths/names/shard-atoms from the UAC SSOT for
**all** asset_groups. Where existing data does not follow the canonical shape, the shard is **skipped with an honest
reason** — it is never made to pass by broadening the matcher (that would hide a real migration gap):

| Situation                                                           | Verdict                                     |
| ------------------------------------------------------------------- | ------------------------------------------- |
| Parquet present only under a legacy/non-canonical prefix            | `skipped: non_canonical_object_path`        |
| Cell's only captured input is non-canonically shaped                | `skipped: non_canonical_input`              |
| Derived ids/paths fail the canonical shape assert (`canonical` leg) | `content_check=non_canonical` (own verdict) |

There is **no legacy `category=` hive-key fallback** in this driver (the MTDS reference has one; it is deliberately
dropped here). Run the canonical leg explicitly:

```bash
cd market-data-processing-service && python3 scripts/pipeline_e2e_check.py \
  --day <DAY> --legs force,canonical --require-captured --auto-day --asset-group <AG>
```

**Every `skipped/non_canonical_*` + `content_check=non_canonical` row in the report IS the migration worklist** — grep
them out of the emitted report and feed them to the canonical-migration todo. A clean canonical leg across all AGs is
what "no orphaned / non-canonical candle data" means.

> **Known gap, not yet implemented (found 2026-07-24, `data_pipeline_e2e_milestones_gate_2026_07_24.md` §5)**: the
> canonical leg verifies path/id SHAPE but does not currently cross-check, per MVP `(asset_group, data_type)` shard,
> that MDPS's actual write behavior (candle-processed vs. passthrough) matches the data_type's declared
> `NEEDS_CANDLE_PROCESSING` value in UAC. Todo: add a check asserting a `NEEDS_CANDLE_PROCESSING=True` shard's output
> actually went through the candle pipeline (not a bare passthrough) and vice versa — this is a real code change to
> `market-data-processing-service/scripts/pipeline_e2e_check.py`'s canonical-leg verifier, not a doc-only fix.

### 3b. What is enumerated per asset_group

- **cefi / defi / tradfi** — `mdps_mvp_universe(ag)` gives the canonical `(venue, instrument_type)` set; data_types come
  from `get_mvp_data_types_for_cefi_venue_itype` (cefi) or the AG's candle-source set, filtered to
  `needs_candle_processing(dt)`; timeframes from `get_valid_timeframes_for_data_type(dt)`.
- **sports / prediction** — `mdps_mvp_universe` **RAISES** for these (MDPS's MVP universe is market-data AGs only), so
  they enumerate from `DATA_TYPES_BY_ASSET_GROUP[ag] ∩ needs_candle_processing`. `--mvp-only` therefore also excludes
  sports/prediction (they have no MVP universe to narrow to).
- **Known enumeration noise, pruned by `--require-captured`**: some sports/prediction reference/lifecycle grains
  (`ODDS`, `trades_inplay`, `MARKET_LIFECYCLE`, `prediction_canonical_question_group`) default
  `needs_candle_processing()=True` because they are absent from `NEEDS_CANDLE_PROCESSING`. They are IS-produced /
  manifest-only grains with no MTDS raw-tick input, so they prune out cleanly.

### 3c. Known orphan / structural cells (report these, don't chase them as failures)

Cross-repo lineage audit 2026-07-20 (MTDS raw → MDPS candles → features → ml/strategy):

- **Produced-but-unconsumed candles** (no downstream feature/ml/strategy reader found): TRADFI `ohlcv_1s`; DEFI
  `book_snapshot_5` / `market_state` / `liquidity` / `fx_rates` (⚠️ contradicts `data-lineage-MTDS-features-ml.md` —
  real code↔codex drift, confirm before acting); SPORTS `arbitrage_opportunity`.
- **Upstream structural trap**: TRADFI `mbp_10` is declared in `DATA_TYPES_BY_ASSET_GROUP` and defaults
  `needs_candle_processing()=True`, but has **no registered MDPS adapter and is not captured by MTDS** — it should be
  pinned `False`. Treat any attempt on it as a finding, not a failure.
- **Consumed-candle set (safe/expected)**: `trades`, `book_snapshot_5` (cefi), `derivative_ticker`, `liquidations`,
  `options_chain`, `futures_chain`, `ohlcv_1m/15m/24h`, `tbbo`, `dex_pool_swaps`.

## 4. Phase 2 — live leg is an HONEST GAP (not a silent skip)

`launch-mdps-features-live.sh` is **code-ready but not operationally runnable**: `setup-data-pipeline-vm.sh` has no
`VM_TASK=mdps-features-live` dispatch branch, and the launcher emits
`VM_SERVICE=market_data_processing_service+features_service` — a `+` cannot appear in a module name, so the VM would
`ModuleNotFoundError`. It is nonetheless registered in `vm_prefix_registry.py` (5 rows), which makes it _look_ live.

The `live` leg therefore records `skipped: live_not_wired` for every shard, and is **not** in the default `--legs`. This
is an honest-absence verdict — see the tracked finding in
`plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md` (S1-b). Do not report the MDPS live path as
proven until that dispatcher branch exists.

## 5. Benchmark leg → full-history time + SPOT cost + parallelization headroom (opt-in)

> **A single smoke force-leg CANNOT measure throughput — it is boot-dominated** (~155 s of VM boot vs seconds of actual
> compute). Never quote a force-leg duration as a pipeline rate. The benchmark leg exists precisely because the smoke
> leg's timings are not a planning number.

```bash
cd market-data-processing-service && python3 scripts/pipeline_e2e_check.py \
  --day <DAY> --legs benchmark --benchmark-days 30 --asset-group <AG> --venue <V> --data-types <DT>
```

It launches ONE **steady-state** VM over a multi-day window (default ~7, use 30 for a planning number) so the boot cost
amortizes, and records wall-clock + a best-effort rows count. Complement it with the authoritative network measure:

```bash
bash deployment-service/scripts/vm/measure-vm-throughput.sh <vm-name> [zone] [project] [startRFC3339]
```

**Rules when quoting a throughput figure** (these traps produced four successive wrong answers on a real 2026-07-18
run): quote the **MEAN over the whole run**, never a peak minute or a short window; always show the per-5min profile;
exclude the first 300 s (startup burst); completion-based MB/s structurally UNDERCOUNTS under concurrency (bytes sit
in-flight uncredited) — the authoritative measure is bytes off the wire (Cloud Monitoring
`instance/network/received_bytes_count`); low CPU with work in flight is normal I/O wait, not a hang; never grep a bare
`429` (it matches millisecond timestamps — match `HTTP 429`). If Monitoring returns no data (VM younger than ~3 min),
report **UNMEASURED** rather than substituting a completion-derived figure.

**Projection model** (`/codex/06-coding-standards/performance-targets.md` §formula):

```
serial_hours = per_shard_day_seconds × shard_days / 3600
VM_hours     = serial_hours / (workers × fleet_width)      [+ per-VM boot/queue overhead]
cost_$       = VM_hours × $/hr
```

| Variable                | Where it comes from                                                                                                                                                                                                                   |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `per_shard_day_seconds` | **MEASURED** by the benchmark leg (never the smoke leg)                                                                                                                                                                               |
| `shard_days`            | shards × days. Days use the **honest per-shard floor** = `min(date where capture_status=='captured')` per cell — never the declared constant (those have been provably late). Report the flat 2019-01-01→today upper bound alongside. |
| `workers`               | MDPS auto-uses `min(cpu_count, 16)` → **8** on the default `e2-standard-8`; `MDPS_MAX_WORKERS` / `--max-workers` overrides                                                                                                            |
| `fleet_width`           | **Unbounded for MDPS** (not Tardis-capped) — shard by date range across N VMs for ~N×; `MANIFEST_PER_VM_SHARDS=true` is already set so parallel shards don't corrupt the manifest                                                     |
| `$/hr`                  | `e2-standard-8` = **$0.268/hr on-demand → ~$0.024–0.107/hr SPOT** (60–91% off). SPOT is the default; GCP promo credits were exhausted 2026-06-20 so on-demand burns real cash                                                         |
| egress                  | **$0** — all VMs and buckets are pinned to `asia-northeast1` (intra-region). Budget a small Class A/B **request** line for a 100 K+ object walk                                                                                       |

**Measured historical floors (2026-07-20, live)**: cefi raw `2019-03-30`, tradfi `2020-01-01`, prediction raw
`2021-06-30` (candles anchor `2025-03-14` — a real divergence worth flagging), defi ≈`2020-01-01`. Flat window
2019-01-01→2026-07-20 = **2757 days**.

**Optimization levers, in the order they pay** (measured/derived 2026-07-20):

1. **Fleet width** — the dominant lever, and free of the Tardis constraint. N date-shard VMs ≈ N×.
2. **Workers per box** — MDPS already auto-scales to cpu count; a bigger `MACHINE_TYPE` (env-overridable on this
   launcher) buys sublinear (~70%) gains since `mdps_compute` is compute-bound.
3. **Disk** — `pd-balanced 250 GB` is already the default and is QG-enforced (a `pd-standard 50 GB` disk collapses to
   2.36 MB/s after ~7.5 GB; pd-balanced 250 GB held 11.1 MB/s — a 4.7× gain). `BOOT_DISK_TYPE=pd-ssd` buys more.
4. **Kernel hot spots** — the candle kernel is polars for the core group-by but still **pandas Python loops** for the
   HFT/whale/carry-forward features (whale detection is an O(n_intervals × n_ticks) `for` loop; `_carry_forward_ohlc` is
   an explicit `for i in range`); `_read_tick_data` does `pl.read_parquet(BytesIO(download_all))` — a full blob into RAM
   with no `scan_parquet` pushdown. Vectorizing those loops / a Rust kernel / predicate-pushdown reads are the remaining
   single-box wins.

## 6. Write + present the report — do not just point at the file

The script prints the **full rendered report** to stdout on exit, not just the path:

```
wrote pipeline_e2e_check report to plans/audit/results/data_pipeline_e2e_check_mdps_<YYYY_MM_DD>.md

<full markdown: frontmatter, summary, Results table, Bucket paths table, Failed/Ambiguous sections>
```

- **Relay the printed content directly to the operator** — never "done, see the report".
- Every shard cell must carry a force-verdict and a skip-verdict. A cell with neither is not "skipped" — it's a gap.
- The "Bucket paths" table shows which bucket the parquet write and the manifest write/read each targeted, flagging ⚠️
  when they differ. For MDPS both should be the SAME `-test-` bucket (self-contained); a mismatch is itself a finding.
- **Grep the report for `non_canonical` and `content_check`** — those rows are the canonical-migration worklist (§3a).

## 7. Under `/autonomous` — loop, don't stop at "done, what's next"

- After Phase 1 + report emission for the current cell, pick the **next unchecked** `(asset_group, venue, data_type)`
  cell and repeat, appending to (never overwriting) the same day's report.
- Stop only once every in-scope cell carries a force + skip verdict (+ a canonical verdict if requested) — then print
  the final report path and a one-line matrix-completion summary (cells proved / gaps / non-canonical / skipped).
- A flat progress metric (no new cell proved across a tick) is a **STALL** — diagnose the VM `run.log`, don't repeat the
  same failing launch.

## Ground truth is the VM `run.log`, not the report verdict

`Processed date=…: N venues ok, 0 failed, R total records` plus `StreamingParquetWriter: uploaded …` is the
authoritative signal. While any raw→canonical id migration is in flight, a verdict can look wrong for migration-boundary
reasons rather than pipeline reasons — read the log before treating a failure as real.

## Wired into `quality-gates.sh` (smoke only)

A cheap **import + `--help` + dry-enumeration** smoke runs in `market-data-processing-service/scripts/quality-gates.sh`
so the driver can't silently rot. The **real** check (VM spend, multi-minute runtime) stays a standalone on-demand
skill, never part of the gate.

## Extending to a new service

Copy this file and swap: the per-service script path, the launcher name + argv, the shard atom, the MVP predicate, the
canonical output path template, and the skip-signal log line. The shared engine
(`unified_trading_library.pipeline_e2e_check`) and this skeleton never change — see `data-pipeline-check-mtds` (PROD-
scoped skip proof, N=1 Tardis cap), `data-pipeline-check-is` (self-contained skip, no data_type axis), and
`data-pipeline-check-features` (per-family CLI divergence + multi-day lookback windows).
