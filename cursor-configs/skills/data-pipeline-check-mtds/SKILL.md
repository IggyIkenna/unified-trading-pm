---
name: data-pipeline-check-mtds
description:
  Run the market-tick-data-service data-pipeline end-to-end smoke check for one operator-given day — Phase 0
  provisions/verifies the `-test-` buckets, Phase 1 proves force-refetch + skip-if-fresh for every MVP (asset_group,
  venue, data_type) shard — labeling each skip verdict genuine (prod-captured) vs ambiguous, Phase 2 proves the live/MVP
  leg, then writes + prints the report path. Never invents `--day` — it must come from the operator. Composes with
  `/autonomous`'s no-pause contract — under `/autonomous`, loop to the next unchecked asset_group/venue instead of
  stopping at "done, what's next." Trigger on `/data-pipeline-check-mtds`, "run the MTDS pipeline check", "smoke-test
  market-tick-data-service for <day>", "prove the MTDS backfill force/skip path works".
---

# /data-pipeline-check-mtds — market-tick-data-service pipeline e2e smoke check

Proves, on real infrastructure (never mocks), that MTDS's backfill path actually does three things a `-test`-bucket-only
dev smoke test can't: (a) a genuinely-missing shard's adapter/download path really works when `--force`d, (b) an
already-captured shard's skip-if-fresh logic really fires and avoids a wasted re-download, (c) the same holds in
`--mode live`. Writes are **test-bucket-only** — this never mutates real captured production data. A pre-check step MAY
read PROD to decide what's genuinely missing / already-captured; the actual backfill write always targets the `-test-`
sibling.

**Shard atom (MTDS)**: the real 6-tuple `(asset_group, venue, data_type, day)` + one sampled `instrument_id`/root
(`options_chain`/`futures_chain` group by `underlying=` — one shard is one underlying-root chain, never split per
strike). **Sports adds a real `league_id` axis** — don't collapse leagues into one cell.

**The IS/MTDS asymmetry that changes what "skip" proves (read this before trusting a skip verdict)**: unlike IS, MTDS's
freshness read (`_resolve_freshness_bucket()` → `get_tick_data_bucket()` →
`resolve_bucket_name(kind= "market-data", ...)`) resolves off `DEPLOYMENT_ENV_SHORT`, **not** `IS_TEST_RUN` — so a
no-force run's skip decision is genuinely driven by **PROD** capture state, independent of the test-bucket write target.
A skip-leg is only a real proof when its target shard/day was **already captured in PROD** — otherwise the "skip fired"
report line is ambiguous, not proof of anything.

## 0. `--day` is REQUIRED — never synthesize one

This check is meaningless without a real target day. If the invoking prompt doesn't carry an explicit
`--day YYYY-MM-DD`, **stop and ask the operator for one** before doing anything else — do not default to "today" or any
other synthetic date. A smoke check silently run against the wrong day proves nothing and wastes real VM spend.

## 1. Composing with `/autonomous`

- **Invoked plainly** (`/data-pipeline-check-mtds --day 2026-07-09`): run Phases 0→3 once through the full MVP
  `(asset_group, venue, data_type)` matrix for that day, then stop and report.
- **Invoked under `/autonomous`** (e.g. `/autonomous /data-pipeline-check-mtds --day 2026-07-09`): first read
  `cursor-configs/AUTONOMOUS_AGENT_RULES.md` + `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` per that skill's contract,
  then run this workflow on the self-paced loop — see step 6. The no-pause / no-`DEFERRED` completion contract applies:
  don't stop mid-matrix to ask "should I continue?"

## 2. Phase 0 — provisioning gate (a real check, not an assumption)

`get_write_bucket_name()` rewrites to `-test-{pid}` on `IS_TEST_RUN=true` but does **not create** the bucket — the
`-test-` sibling for `market-data-tick-*` is not pre-declared in `bucket_config.yaml`. Verify all 5 asset groups before
targeting any of them for the first time (prediction uses the short `pred` form in the bucket name):

```bash
PROJECT_ID="central-element-323112"
for ag in cefi defi tradfi sports prediction; do
  mtds_ag="${ag}"; [ "${ag}" = "prediction" ] && mtds_ag="pred"
  bucket="market-data-tick-${mtds_ag}-test-${PROJECT_ID}"
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
gcloud storage buckets create "gs://market-data-tick-${mtds_ag}-test-${PROJECT_ID}" \
  --project="${PROJECT_ID}" --location=asia-northeast1 --uniform-bucket-level-access
```

- Do not advance an asset_group into Phase 1 until its `-test-` bucket exists.

## 3. Phase 1 — batch force + skip matrix

> **⛔ TARDIS CELLS ARE SERIAL — N=1, NEVER ONE-VM-PER-SHARD (HARD RULE, operator 2026-07-16).** Every `cefi` cell whose
> venue is Tardis-sourced (all the standard CEXes — BINANCE-\*, BYBIT, OKX-\*, DERIBIT, KRAKEN-\*, BITGET-\*,
> BITFINEX-\*, COINBASE-SPOT, UPBIT; NOT the native-REST venues HYPERLIQUID / ASTER / LIGHTER-ZKSYNC / PACIFICA-SOLANA /
> EXTENDED-STARKNET) shares ONE academic key that permits ONE active IP. **One VM per shard = one IP per shard = a
> mutual-403 storm**, and this skill has already caused it: three
> `mtds-backfill-cefi-pipelinecheck-20260712-1015{56,57,58}` VMs were launched inside the same second and preempted.
> Measured cost of N=3 in the real gap (2026-07-16): ~94% of requests 403'd (10,300x403/912 ok; 15,034x403/**0** ok),
> **+37,212 FALSE `attempted_failed` manifest rows in 8h** — i.e. the storm does not merely waste time, it CORRUPTS the
> manifest with failures the venue never actually returned — and coverage went BACKWARD 52.13 → 48.38. At N=1: **zero**
> 403s.
>
> Therefore, in this phase:
>
> - **Run Tardis cells STRICTLY ONE AT A TIME** (the shared guard `tardis-concurrency-guard.sh` now enforces
>   `TARDIS_MAX_CONCURRENT_VMS=1` and is wired into `launch-mtds-backfill-vm.sh`, so a second concurrent cefi VM is
>   REFUSED — do not `FORCE=1` past it, wait for the running one).
> - **Prefer bundling over serialising where the check allows it**: `launch-mtds-backfill-vm.sh` accepts multi-valued
>   `--venues "A B C" --data-types "trades book_snapshot_5"`, so one VM can carry many Tardis shards on the single IP.
>   Scale that VM with `TARDIS_MAX_CONCURRENT_DOWNLOADS` / `TARDIS_BOOK_SNAPSHOT_MAX_CONCURRENT` (defaults 16 / 4; the
>   box is typically ~93% idle at those — measured cpu 104%/1600%, rss 7.8GB/128GB) — **never with more VMs**.
> - Non-Tardis cells (native-REST venues above, and non-cefi asset_groups: defi / sports / prediction / tradfi) are
>   UNAFFECTED — they use different keys/paths, do not count against the cap, and may still run in parallel.
> - If a run trips the guard, that is the guard WORKING. Serialise; do not override.
>
> SSOTs: `codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap ·
> `plans/archive/2026_07/cefi_completion_program_2026_07_15.md` (the measured N=3-vs-N=1 evidence).

For each MVP `(asset_group, venue, data_type)` cell for `--day` (MVP scope from
`unified_api_contracts.canonical.crosscutting.mvp_scope.is_mvp()`; enumerate the Sports `league_id` axis as its own
cells, never collapsed):

```bash
cd market-tick-data-service && python3 scripts/pipeline_e2e_check.py \
  --asset-group <AG> --venues <VENUE> --data-types <DT> --day <DAY> --legs force,skip
```

This sequences, per shard, via the shared `unified_trading_library.pipeline_e2e_check` engine:

1. **Sample a real instrument**: `prod_precheck.read_prod_capture_status()` samples a real, currently-live
   `instrument_id`/underlying-root from the actual PROD catalog/manifest at run time — never a hardcoded symbol
   (`smoke_matrix.py::_REPRESENTATIVE_SYMBOL` is a last-resort fallback only, canonical-ID forms are mid-migration and
   genuinely divergent per venue).
2. **force-leg**: launches
   `launch-mtds-backfill-vm.sh --asset-group <AG> --venues <VENUE> --data-types <DT> --instrument-ids <sampled_id> --start <DAY> --end <DAY> --vm-name mtds-backfill-<AG>-pipelinecheck-<run_ts> --test-run --force`;
   polls the VM's `EXIT_STATUS`/`run.log` GCS observability contract to a terminal state; on `SUCCESS` verifies the
   test-bucket parquet is (re)written and the manifest row shows `captured`.
3. **skip-leg pick**: `prod_precheck.read_prod_capture_status()` picks a shard/day already verified **captured in PROD**
   for this `(asset_group, venue, data_type)` — this is what makes the skip verdict meaningful (see the asymmetry note
   above). If no PROD-captured shard/day exists for this cell, the skip-leg still runs but the report MUST label it
   `skip_proof: ambiguous`, never `genuine`.
4. **skip-leg**: same shard, no `--force`; confirms the freshness-preflight skip signal
   (`"Pre-flight: venue=%s date=%s — all requested data_types fully covered"` from `venue_fetch.py:249`) appears in
   `run.log`, and that the test-bucket object's fingerprint (generation + `updated`) is unchanged from the force-leg.

## 4. Phase 2 — live leg (MVP-scoped)

```bash
cd market-tick-data-service && python3 scripts/pipeline_e2e_check.py \
  --legs live --mvp-only --day <DAY>
```

- Same launcher, `--test-run`, scoped to MVP venues covering **both** IS + MTDS MVP scope. No separate force/skip split
  on this leg — `--mode live` already always forces.

## 5. Write + present the report — do not just point at the file

`report.write_report()` emits a markdown + sibling JSON pair; the script itself prints the **full rendered report**
(pass/fail table + the bucket-path table below) to stdout on exit, not just the file path:

```
wrote pipeline_e2e_check report to plans/audit/results/data_pipeline_e2e_check_mtds_<YYYY_MM_DD>.md

<full markdown: frontmatter, summary, Results table, Bucket paths table, Failed/Ambiguous sections>
```

- **Relay this printed content directly to the operator in your response — do not say "done, see the report" and make
  them go open the file.** The report's "Results" table gives per-shard pass/fail; its "Bucket paths" table (new, plan
  todo — auto-generated, not hand-built) shows exactly which bucket the parquet write and the manifest write/read each
  targeted, and flags with ⚠️ when they differ (this is how the real, load-bearing MTDS parquet/manifest bucket
  asymmetry — plan finding #2 / todo 17 — becomes visible without re-deriving it from `run.log` by hand every time).
- Every shard cell must carry a force-verdict and a skip-verdict **labeled `skip_proof: genuine (prod-captured)` or
  `skip_proof: ambiguous`**; every MVP venue must carry a live-verdict. A cell with neither is not "skipped" — it's a
  gap, and belongs on the next tick (see step 6) or as a flagged gap in the report.

## 6. Under `/autonomous` — loop, don't stop at "done, what's next"

- After Phase 2 + report emission for the current `(asset_group, venue)` cell, do **not** report "done" and wait for the
  next instruction.
- Pick the **next unchecked** `(asset_group, venue)` cell (across its `data_type`/`league_id` sub-cells) in the MVP
  matrix for the same `--day` and repeat Phases 1→2 for it, appending to (never overwriting) the same day's report.
- Only stop the loop once **every** MVP `(asset_group, venue, data_type)` cell for `--day` carries a force + skip
  (labeled) + live verdict — then print the final report path and a one-line matrix-completion summary (cells proved /
  cells with gaps / cells with `ambiguous` skip verdicts still needing a PROD-captured shard).
- A flat progress metric (no new cell proved across a tick) is a STALL — diagnose (`gh run view --log-failed`-style VM
  log inspection), don't repeat the same failing launch.

## Extending to a new service

Copy this file, swap: the per-service script path (`<service>/scripts/pipeline_e2e_check.py`), the launcher script name,
the shard atom (MTDS = the 6-tuple incl. `data_type` — a new service defines its own), the MVP predicate, and the
sampled-instrument-id source. The shared engine (`unified_trading_library.pipeline_e2e_check`) and this skeleton never
change — see the `data-pipeline-check-is` skill for the sibling that already differs on shard atom (no `data_type`, no
instrument-level flag) and skip-leg proof (self-contained, no PROD pre-check needed).

## Not wired into `quality-gates.sh`

This check does real I/O + real VM spend + multi-minute-plus runtime — it stays a standalone, on-demand skill
(cron-schedulable later via the `schedule` skill), never part of `market-tick-data-service/scripts/quality-gates.sh`.
