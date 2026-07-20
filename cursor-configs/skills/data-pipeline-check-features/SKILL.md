---
name: data-pipeline-check-features
description:
  Run the features-service feature-computation pipeline end-to-end smoke check for one operator-given day — Phase 0
  verifies the `-test-` buckets, Phase 1 proves force-compute + skip-if-fresh for every MVP feature shard (asset_group ×
  feature family) across ALL asset_groups over each family's real multi-day lookback window, a canonical leg asserts the
  computed features carry canonical per-family paths/ids (non-canonical data is SKIPPED, never legacy-passed — it
  becomes migration work), and an opt-in benchmark leg measures amortized per-shard-day throughput and projects
  full-history compute time + SPOT cost + parallelization headroom. Never invents `--day`. Composes with `/autonomous`'s
  no-pause contract. Trigger on `/data-pipeline-check-features`, "run the features pipeline check", "smoke-test
  features-service for <day>", "prove the feature compute force/skip path works", "how long to compute all features".
---

# /data-pipeline-check-features — features-service compute pipeline e2e smoke check

Proves, on real infrastructure (never mocks), that features-service's compute path actually does what a dev-local
`smoke_matrix.py` run can't: (a) a genuinely-computable family shard's read→calculate→write path really works when
`--force`d, over that family's **real multi-day lookback window**, (b) an already-computed shard's skip-if-fresh logic
really fires, (c) the written features carry **canonical** per-family paths/ids, and (d) how long a full-history feature
backfill would take and cost. Writes are **test-bucket-only** — production features are never mutated.

**Shard atom (features)**: `(asset_group, feature_family)` + the target `day` and its family-specific lookback window.
`feature_group` is a reporting/scoping dimension (a requested group fans out to many on-disk `feature_group=` dirs), not
a separate shard key.

**Why the skip proof is SELF-CONTAINED**: the writer's freshness probe (`FeatureWriter.check_exists`) resolves the sink
via `get_data_sink(routing_key=<ag>)`, which honours `PROTOCOL_DATA_SINK_BUCKET_{AG}`. Routing output to the `-test-`
sibling therefore routes BOTH the write and the existence check there — so a force-run-then-skip-run pair on one shard
is a genuine, complete proof (like `data-pipeline-check-is`). `check_exists` **fails OPEN** (a probe error returns False
= redo the work), so a skip that fires is meaningful.

> **Skip-signal caveat**: the per-instrument skip line `"Skipping %s - already processed"`
> (`delta_one/engine/orchestrator.py:395`) is logged at **DEBUG**, so it may not appear in a default-INFO VM `run.log`.
> The **primary** skip proof in this driver is therefore the object **fingerprint** (etag+crc32c+updated+size) being
> unchanged between the force and skip legs; the log line is a secondary signal.

## 0. `--day` is REQUIRED — never synthesize one

If the invoking prompt doesn't carry an explicit `--day YYYY-MM-DD`, **stop and ask the operator** — do not default to
"today". A feature compute pointed at a day whose candle inputs aren't captured proves nothing and burns real VM spend.

## 1. Composing with `/autonomous`

- **Invoked plainly**: run Phases 0→2 once through the scoped family matrix for that day, then stop and report.
- **Invoked under `/autonomous`**: read `cursor-configs/AUTONOMOUS_AGENT_RULES.md` +
  `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` first, then run on the self-paced loop (step 7). No-pause contract
  applies.

## 2. Phase 0 — provisioning gate (object-level probe only)

Features use the **folded per-asset_group** `features` bucket kind (Fold A, 2026-07-18/19) — the retired per-family
aliases (`features-delta-one`, …) now **RAISE** `BucketNamingError`; always resolve `kind="features"`.

> **⛔ NEVER gate on `gcloud storage buckets describe` / `gsutil ls -b`** — `unified-trading-sa` lacks
> `storage.buckets.get`, so a describe-based gate false-negatives every bucket and provisioning on it creates
> duplicates. Object-probe instead:

```bash
PROJECT_ID="central-element-323112"
for b in features-cefi-test features-defi-test features-tradfi-test features-pred-test \
         features-sports-test features-calendar-test; do
  out=$(gsutil ls "gs://${b}-${PROJECT_ID}/**" 2>&1 | head -1)
  case "$out" in
    *NotFound*|*404*|*"does not exist"*)  echo "GAP  gs://${b}-${PROJECT_ID} — MISSING" ;;
    *"matched no objects"*|"")            echo "OK   gs://${b}-${PROJECT_ID} (exists, empty)" ;;
    *AccessDenied*|*403*)                 echo "??   gs://${b}-${PROJECT_ID} — 403 on objects; escalate" ;;
    *)                                    echo "OK   gs://${b}-${PROJECT_ID} (exists, has objects)" ;;
  esac
done
```

Verified 2026-07-20: all six exist (cefi has objects; the rest empty — normal for unwritten `-test-` siblings).
`commodity` resolves to the non-env-split `commodity-signals-batch-*` bucket; resolve it via `resolve_bucket_name`
rather than assuming the `-test-` infix.

## 3. Phase 1 — force + skip matrix (with per-family multi-day lookback)

```bash
cd features-service && python3 scripts/pipeline_e2e_check.py \
  --day <DAY> --legs force,skip --require-captured --auto-day \
  [--asset-group CEFI] [--family delta_one] [--lookback-days N]
```

**The viable `(family × asset_group)` matrix — ~29 cells** (`launch-features-vm.sh::_is_viable_cell` is the SSOT; the
driver enumerates from UAC `FeatureFamily` + this map):

| family             | asset_groups                    |
| ------------------ | ------------------------------- |
| `delta_one`        | CEFI, DEFI, TRADFI, PREDICTION  |
| `volatility`       | CEFI, TRADFI                    |
| `onchain`          | DEFI only                       |
| `sports`           | SPORTS only                     |
| `calendar`         | CEFI, TRADFI (output is GLOBAL) |
| `multi_timeframe`  | CEFI, DEFI, TRADFI              |
| `cross_instrument` | CEFI, TRADFI, PREDICTION        |
| `commodity`        | TRADFI only                     |

- **`calendar` takes NO `--asset-group`** — its output is global; it collapses to a single `GLOBAL` cell.
- **Ordering matters**: `delta_one` is enumerated and force-run **FIRST**, and its `-test-` output bucket is then passed
  as `--source-bucket` to the **derived** families (`multi_timeframe`, and `cross_instrument` where it reads delta_one
  output) so they read the freshly-written test features rather than PROD. Never run a derived family before its
  producer in the same sweep.

### 3a. Multi-day lookback — the axis that makes this different from MDPS/MTDS

Feature families need **more than one day of input**. The window is computed per family from
`features-service/scripts/e2e/resolve_lookback.py` (the driver shells out to it and caches per family):

```
buffer_days = ceil(max_lookback_candles × seconds_per_period × 1.2 / 86400) × calendar_multiplier
              (CEFI/DEFI 1.0, TRADFI 1.45)
input window = [target_day − buffer_days, target_day]
```

- `delta_one` max **200 candles** (`FEATURE_GROUP_LOOKBACK`: moving_averages/market_structure/fibonacci/sr_memory…
  = 200) — at `15s` that's ~1 day, but at `24h` it is ~**288 calendar days** (CEFI) / ~418 (TRADFI).
- `cross_instrument` max **500 candles** — the longest window of any family.
- `multi_timeframe` max 50 (and is transitive on delta_one anyway); `calendar` ~5 (mostly deterministic, 0 lookback);
  `onchain`/`volatility`/`sports` are data-driven (sports needs multi-season history).
- `--lookback-days N` overrides the computed window; families `resolve_lookback` doesn't model floor to 1 day.

**`--require-captured` checks the WHOLE window, not just the target day.** A window is covered iff every required day in
`[target − lookback, target]` carries an acceptable status (`captured`, or `empty_confirmed` for legitimately
non-trading days). Uncovered → `skipped: no_captured_input_for_window` (no VM launched). `--auto-day` slides the window
back to the most recent fully-covered one (preferring a window not anchored on a month-first). The window read uses
`read_availability_index(bucket, columns=[…], filters=[("date",">=",s),("date","<=",e)])` — the pyarrow pushdown is
**only honoured when `columns` is also set**, which is what keeps it memory-safe on the 11M+ row indices.

**Required INPUT per family** (what coverage is checked against):

| family                                             | input                                                                                                                          |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `delta_one`, `multi_timeframe`, `cross_instrument` | MDPS **candles** in `market-data-tick-{ag}-prd-{pid}` (`service_name=="market-data-processing-service"`)                       |
| `volatility`                                       | RAW `options_chain` / `futures_chain` ticks (`service_name=="market-tick-data-service"`)                                       |
| `onchain`                                          | RAW DeFi tick data_types (bypass grains: `lending_indices`, `lst_rates`, `oracle_prices`, `perp_funding`, `vault_share_price`) |
| `sports`                                           | provider match/odds history (multi-season)                                                                                     |

> ⚠️ **Reality check (measured 2026-07-20)**: derived MDPS candles barely exist yet (cefi 6 rows, tradfi 139, prediction
> 168). So candle-dependent families will legitimately report `skipped: no_captured_input_for_window` on most days until
> the candle backfill runs. That is an **honest gap**, not a failure — and it is exactly why `/data-pipeline-check-mdps`
> must be green and its backfill run first.

Per shard the driver sequences, via the shared engine:

1. **force-leg**: launches
   `launch-features-vm.sh --feature-family <FAM> --asset-group <AG> --start-date <window_start> --end-date <DAY> --launch-mode full --vm-name features-<fam>-<ag>-pipelinecheck-<ts> --sink-bucket features-<ag>-test-<pid>`
   with `FORCE=1` (the launcher turns that into the service's `--force`); polls `EXIT_STATUS`/`run.log` to terminal; on
   `SUCCESS` verifies a feature parquet exists on the family's **canonical** path in the `-test-` bucket and the
   manifest row is `captured`/`empty_confirmed`.
2. **skip-leg**: same shard, no `FORCE`; asserts the object fingerprint is **unchanged** from the force-leg (primary
   proof) and looks for the DEBUG skip line (secondary).

**Canonical output templates differ PER FAMILY** — the verify asserts each family's real writer template, never one
generic shape:

- `delta_one`: `delta_one/day={D}/feature_group={fg}/feature_group_version={N}/timeframe={tf}/{instrument_id}.parquet`
  (**no** `by_date/` segment; **has** `feature_group_version=`)
- `volatility`: `volatility/by_date/day={D}/feature_group={fg}/timeframe={tf}/{instrument}.parquet` (**has** `by_date/`;
  **no** version segment)
- `multi_timeframe`: `mtf/…`; `cross_instrument`/`sports`: `by_date/…`; `onchain`: feature-specific
- Because a requested `feature_group` fans out to many on-disk `feature_group=` dirs, existence is asserted **under
  `day={D}/` on the family's canonical prefix** — not against one `feature_group` dir.

### 3b. Canonical-paths principle — non-canonical data is SKIPPED, never legacy-passed (HARD)

Enumeration and verification are built off the **expected canonical** per-family paths/names from the UAC/writer SSOT
for **all** asset_groups. Existing data that doesn't follow canonical shape is **skipped with an honest reason**, never
made to pass by broadening the matcher:

| Situation                                                             | Verdict                                     |
| --------------------------------------------------------------------- | ------------------------------------------- |
| Feature parquet only under a legacy/non-canonical prefix              | `skipped: non_canonical_object_path`        |
| Only captured input for the window is non-canonically shaped          | `skipped: non_canonical_input`              |
| Written feature ids/paths fail the canonical assert (`canonical` leg) | `content_check=non_canonical` (own verdict) |

Retired per-family bucket aliases now **RAISE** — the driver always resolves `kind="features"`. Run the canonical leg:

```bash
cd features-service && python3 scripts/pipeline_e2e_check.py \
  --day <DAY> --legs force,canonical --require-captured --auto-day --family <FAM> --asset-group <AG>
```

**Every `skipped/non_canonical_*` + `content_check=non_canonical` row IS the canonical-migration worklist** — grep them
out of the report.

### 3c. Known orphan families (report as honest-absence, do NOT chase as failures)

Cross-repo lineage audit 2026-07-20 (features → ml-service / strategy-service):

- **`performance_features`** and **`strategy_pnl_archetype`** are **ORPHANS by wiring**: both consume
  `StrategyPnlStreamEvent`, which no upstream currently emits (the `trading-agent-service` allocation-directive
  subscriber is an explicit **NO-OP stub**; the regime allocator is post-cutover). Every run legitimately emits
  `empty_confirmed(EXPECTED_NO_PNL_STREAM)`. The driver records `skipped: expected_no_upstream` — this is the **correct
  honest state**, not data to migrate and not a bug to fix here.
- **Consumed (safe)**: `delta_one` (ml train+infer, strategy), `multi_timeframe` `tf_*` (ml), `cross_instrument`
  (`cross_asset_correlation`, ml tradfi optional), `calendar` (`economic_events`, ml tradfi optional), `onchain` +
  `commodity` + cefi `perp_funding` (strategy/execution), `sports` (ml + strategy).
- **`volatility` is weakly-consumed** — it feeds the greeks/options path; no clean ml/strategy reader was pinned down.
  Flag, don't delete.

## 4. Phase 2 — live leg is OUT OF SCOPE by default

The features live path is `launch-features-cross-cutting.sh` (a long-lived streaming singleton subscribing
`streaming.{ag}.features_computed`), not a bounded batch VM. The `live` leg records `skipped: live_not_in_scope` and is
**not** in the default `--legs`. (The co-located `launch-mdps-features-live.sh` is separately **not runnable** — no
dispatcher branch; see `plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md` S1-b.)

## 5. Benchmark leg → full-history time + SPOT cost + parallelization headroom (opt-in)

> **A single smoke force-leg CANNOT measure throughput** — it is boot-dominated. Never quote a force-leg duration as a
> compute rate.

```bash
cd features-service && python3 scripts/pipeline_e2e_check.py \
  --day <DAY> --legs benchmark --benchmark-days 30 --family <FAM> --asset-group <AG>
```

Complement with the authoritative network measure (`bash deployment-service/scripts/vm/measure-vm-throughput.sh <vm>`),
and see `features-service/scripts/profile_compute_costs.py` for per-family compute-cost profiling. Quote the **MEAN over
the whole run** (never a peak minute), show the per-5min profile, exclude the first 300 s, and report **UNMEASURED**
rather than substituting a completion-derived number if Monitoring has no data yet.

**Projection model** — identical to the MDPS skill:

```
serial_hours = per_shard_day_seconds × shard_days / 3600
VM_hours     = serial_hours / (workers × fleet_width)
cost_$       = VM_hours × $/hr
```

| Variable                | Value / source                                                                                                                                                                                                               |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `per_shard_day_seconds` | **MEASURED** by the benchmark leg                                                                                                                                                                                            |
| `shard_days`            | families × AGs × days, using the **honest per-shard floor** (`min(captured date)`) — never a declared constant; show the flat 2019→today (2757 d) upper bound alongside                                                      |
| `workers`               | features intra-process pool default **4** (`max_workers`); the codex flags per-symbol fan-out (up to 176-way) as the biggest untapped lever                                                                                  |
| `fleet_width`           | **Unbounded** — features are NOT Tardis-capped (they read GCS); shard by date range across N VMs for ~N×; `MANIFEST_PER_VM_SHARDS=true` already set                                                                          |
| `$/hr`                  | `e2-standard-8` **$0.268/hr on-demand → ~$0.024–0.107/hr SPOT**. NOTE: `launch-features-vm.sh` **hardcodes** the machine type (not env-overridable) — editing the launcher is required to use a bigger/compute-optimized SKU |
| egress                  | **$0** intra-region (`asia-northeast1`)                                                                                                                                                                                      |

Codex `performance-targets.md` puts `features_compute` at ≈**2,700 serial-days** at production scale (LOW confidence —
only startup overhead was measured), with a **<2 h** target on `c3-highcpu-176` at 176-way fan-out. Treat that as the
shape of the answer and replace it with the benchmark-measured number.

## 6. Write + present the report — do not just point at the file

The script prints the **full rendered report** to stdout:

```
wrote pipeline_e2e_check report to plans/audit/results/data_pipeline_e2e_check_features_<YYYY_MM_DD>.md
```

- **Relay the printed content directly** — never "done, see the report".
- Every family cell must carry a force-verdict and a skip-verdict; a cell with neither is a gap, not a skip.
- The "Bucket paths" table should show the parquet and manifest writes landing on the SAME `-test-` features bucket
  (self-contained). A mismatch is itself a finding (the phantom-`captured`-with-no-parquet failure mode).
- **Grep for `non_canonical` / `content_check` / `no_captured_input_for_window`** — respectively the canonical-migration
  worklist and the upstream (candle-backfill) dependency list.

## 7. Under `/autonomous` — loop, don't stop at "done, what's next"

- After a family cell completes, pick the **next unchecked** `(asset_group, family)` cell and repeat, appending to the
  same day's report. Respect the producer-before-derived ordering (delta_one first).
- Stop only once every in-scope cell carries force + skip (+ canonical if requested) — then print the final report path
  and a one-line completion summary (proved / gaps / non-canonical / awaiting-candle-input).
- A flat progress metric across a tick is a **STALL** — diagnose the VM `run.log`, don't repeat the failing launch.

## Wired into `quality-gates.sh` (smoke only)

A cheap **import + `--help` + arg-parse** smoke runs in `features-service/scripts/quality-gates.sh` so the driver can't
silently rot. The real check (VM spend, multi-minute runtime) stays a standalone on-demand skill.

## Extending to a new service

Copy this file and swap: the per-service script path, launcher name + argv, shard atom, the canonical output template
(per family here), the lookback model, and the skip-signal. The shared engine
(`unified_trading_library.pipeline_e2e_check`) and this skeleton never change — see `data-pipeline-check-mdps` (candle
shard atom, per-timeframe verify), `data-pipeline-check-mtds` (PROD-scoped skip proof, N=1 Tardis cap), and
`data-pipeline-check-is` (simplest: no data_type axis).
