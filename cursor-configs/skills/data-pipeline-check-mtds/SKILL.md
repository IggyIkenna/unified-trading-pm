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

## Modes

- **Interactive (default, operator present)**: "Invoked plainly" below — run once through the full MVP
  `(asset_group, venue, data_type)` matrix for the given `--day`, stop, report.
- **Autonomous / AO-dispatched**: "Invoked under `/autonomous`" below — no-pause loop per step 6. `--day` still MUST
  come from the operator or the dispatching plan/task in either mode — this skill never invents it.

**ASK > PARK when the operator is reachable** (same calibration as `/plan-reconcile`): a genuine ambiguity this skill
can't resolve deterministically (BLOCKED-CREDENTIALS, an infra outage vs. a real regression) gets asked directly if the
operator is in the session, and parked as a `BLOCKED-OPERATOR-DECISION` issue-doc entry only when nobody's reachable —
never silently guessed at or skipped either way.

## 1. Composing with `/autonomous`

- **Invoked plainly** (`/data-pipeline-check-mtds --day 2026-07-09`): run Phases 0→3 once through the full MVP
  `(asset_group, venue, data_type)` matrix for that day, then stop and report.
- **Invoked under `/autonomous`** (e.g. `/autonomous /data-pipeline-check-mtds --day 2026-07-09`): first read
  `cursor-configs/AUTONOMOUS_AGENT_RULES.md` + `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` per that skill's contract,
  then run this workflow on the self-paced loop — see step 6. The no-pause / no-`DEFERRED` completion contract applies:
  don't stop mid-matrix to ask "should I continue?"

## 1a. Run the driver on its own VM — DEFAULT, do not run inline on the shared host

Live evidence 2026-08-06: the driver process itself (not the per-shard VMs it launches — those already ran on their own
SPOT VMs) reached **21.9GB RSS** on a `--legs force,skip` run and got OOM-killed by the AO host's resource-watchdog
after competing with every other slot for the shared host's fixed memory pool. Every invocation in §3/§4 below — run via
`deployment-service/scripts/vm/launch-pipeline-e2e-check-driver-vm.sh` instead of a bare
`cd market-tick-data-service && python3 ...`: swap the command's head, keep every flag below it identical.

**Default to per-`--asset-group` invocations (5 separate driver-VM launches), not one unscoped sweep** — confirmed
2026-08-14 (`mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md`): an unscoped `--mvp-only` sweep with
no `--asset-group` filter enumerates the FULL post-fix MVP surface (3126 shards as of that date — see
`mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md` for why the real count is this large, not the
~52-cell cefi-only figure this doc used to quote elsewhere) and the top-level `pipeline_e2e_check.py` process was
SIGKILLed (exit 137, OOM) about 10 minutes / ~30 shards in — on the DEDICATED, ISOLATED e2-highmem-4 (32GB) driver VM
this §1a already exists to provide, not the shared host. A root-cause fix (bounding the driver's per-shard memory
growth) is tracked in that issue doc; until it ships, scope every invocation to one `--asset-group` at a time:

```bash
for AG in CEFI DEFI TRADFI SPORTS PREDICTION; do
  bash deployment-service/scripts/vm/launch-pipeline-e2e-check-driver-vm.sh \
    --service mtds --day <DAY> --asset-group "$AG" --legs force,skip --mvp-only --require-captured --auto-day \
    --wall-clock-timeout-sec 14400 --project central-element-323112
done
```

Each launch still prints its own `vm_name=...` immediately and returns — poll each independently. This bounds any single
driver process to a fraction of the full 3126-shard surface (CEFI alone was already ~30+ shards deep and still climbing
when the unscoped run OOM'd, so even a per-asset_group run may need further splitting by `--venue` if it still OOMs —
check the driver RSS trend in `run.log` before assuming a smaller scope is automatically safe).

**Always pass an explicit `--wall-clock-timeout-sec` well above the 3600s (1hr) CLI default** — confirmed live
2026-08-15 (same issue doc, Progress Log): `pipeline_e2e_check.py`'s own defense-in-depth SIGALRM backstop
(`_setup_wall_clock_timeout`, exit code 3) force-terminates the driver at the default 1hr mark regardless of whether
it's making genuine progress, and a real `--legs force,skip --mvp-only` sweep — even scoped to ONE asset_group —
routinely needs longer than that (each force+skip shard pair costs ~2-5 min of VM-launch-and-wait overhead; CEFI's
~30+-shard depth alone is 1-2.5hrs). This is the same `rc=3` this issue doc's still-open SPORTS todo flagged as
"undiagnosed" — root-caused: it is the wall-clock timeout firing mid-sweep, not a distinct crash. 14400s (4hr) is a
safe floor for a per-asset_group MVP sweep; a genuinely unscoped full sweep needs much more (many-hour run, see §1a
above) and is why the per-`--asset-group` split remains the recommended default regardless of this flag.

Prints `vm_name=...` immediately, then returns — async (the driver VM self-deletes on completion). Poll
`gs://deployment-scripts-central-element-323112/vm-logs/<vm_name>/{run.log,EXIT_STATUS}`, or via
`unified_trading_library.pipeline_e2e_check.launcher.launch_vm_and_wait()` (same contract every other launch-and-wait
caller uses). The report mirrors to
`gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/<run_date>/` in
addition to the local `plans/audit/results/...md` path in §5 — the local copy doesn't survive the driver VM's
self-delete. The raw `pipeline_e2e_check.py` command shown inline in §3/§4 (for reference) is fine for a quick dev-local
dry-run against a tiny scope only — never for a real sweep.

## 2. Phase 0 — provisioning gate (a real check, not an assumption)

`get_write_bucket_name()` rewrites to `-test-{pid}` on `IS_TEST_RUN=true` but does **not create** the bucket — the
`-test-` sibling for `market-data-tick-*` is not pre-declared in `bucket_config.yaml`. Verify all 5 asset groups before
targeting any of them for the first time (prediction uses the short `pred` form in the bucket name):

> **⛔ NEVER gate on `gcloud storage buckets describe` / `gsutil ls -b` (2026-07-19).** Both need `storage.buckets.get`,
> which the `unified-trading-sa` service account does NOT have — it holds OBJECT-level read/write only. Measured
> 2026-07-19: bucket-metadata calls return `AccessDeniedException: 403` for EVERY bucket including
> `market-data-tick-cefi-prd-*`, which the same session had been reading objects from continuously. So a describe-based
> gate reports "GAP MISSING" for all 5 asset groups even when every bucket exists, and following it literally provisions
> 5 DUPLICATE buckets — directly against `bucket_estate_consolidation_to_sub100_2026_07_13`. `gcloud storage ls` (bucket
> list) is equally blind: it returns **0 buckets** for this project.
>
> **Use an OBJECT-level probe instead** — it distinguishes MISSING (404) from EXISTS-but-EMPTY, which is the state a
> fresh `-test-` sibling is legitimately in:

```bash
PROJECT_ID="central-element-323112"
for ag in cefi defi tradfi sports prediction; do
  mtds_ag="${ag}"; [ "${ag}" = "prediction" ] && mtds_ag="pred"
  bucket="market-data-tick-${mtds_ag}-test-${PROJECT_ID}"
  out=$(gsutil ls "gs://${bucket}/**" 2>&1 | head -1)
  case "$out" in
    *NotFound*|*404*|*"does not exist"*)  echo "GAP  gs://${bucket} — MISSING, provisioning gate fails for ${ag}" ;;
    *"matched no objects"*|"")            echo "OK   gs://${bucket} (exists, empty — normal for an unwritten test sibling)" ;;
    *AccessDenied*|*403*)                 echo "??   gs://${bucket} — 403 on objects too; escalate, do NOT provision blind" ;;
    *)                                    echo "OK   gs://${bucket} (exists, has objects)" ;;
  esac
done

# Legacy describe-based form — DO NOT USE (false-negatives without storage.buckets.get):
#   if gcloud storage buckets describe "gs://${bucket}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
#     echo "OK   gs://${bucket}"
#   else
#     echo "GAP  gs://${bucket} — MISSING, provisioning gate fails for ${ag}"
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

### 2a. `--allow-live-prod-writes` is PROHIBITED — never pass it (HARD RULE)

MTDS's pipeline checker is **fail-closed by default** — the batch force/skip legs hardcode `--test-run`
(`market-tick-data-service/scripts/pipeline_e2e_check.py:1369`), and the launcher bakes `IS_TEST_RUN=true`
(`launch-mtds-backfill-vm.sh:198`), so every write resolves to a `-test-` bucket. However, the checker also registers
ONE explicit prod-write escape hatch: `--allow-live-prod-writes` (`pipeline_e2e_check.py:2561`, `:2642`, `:1983`). When
passed, the live leg builds its launcher argv **without `--test-run`** — `IS_TEST_RUN` is never set, `test_aware` never
fires, and `get_tick_data_bucket` returns the PROD `-prd-` bucket. The leg is additionally fire-and-forget (returns
`status="skipped"` with "verification skipped" because the VM never terminates).

**⛔ NEVER pass `--allow-live-prod-writes` to `pipeline_e2e_check.py` from this skill.** This flag exists for standalone
operator-driven prod-live launches ONLY — it is never appropriate for a `/data-pipeline-check-mtds` smoke check. The
skill's entire purpose is proving the pipeline on `-test-` buckets without touching production data; passing this flag
defeats that guarantee and writes real PROD objects with no guard.

**This prohibition is absolute — there is no operator override within this skill's invocation.** A PROD live launch is
out of scope for `/data-pipeline-check-mtds` entirely. If a prod live verification is genuinely needed, it must be done
as a separate, explicitly-scoped operator action outside this skill, never by passing `--allow-live-prod-writes` through
these instructions.

Provenance: `backfill_smoke_write_path_canonical_audit_2026_07_20.md` §1a.

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
> SSOTs: `/codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap ·
> `plans/archive/2026_07/cefi_completion_program_2026_07_15.md` (the measured N=3-vs-N=1 evidence).

For each MVP `(asset_group, venue, data_type)` cell for `--day` (MVP scope from
`unified_api_contracts.canonical.crosscutting.mvp_scope.is_mvp()`; enumerate the Sports `league_id` axis as its own
cells, never collapsed):

**Run via the §1a driver-VM launcher, not inline.** Underlying command:

```bash
cd market-tick-data-service && python3 scripts/pipeline_e2e_check.py \
  --asset-group <AG> --venue <VENUE> --data-types <DT> --day <DAY> --legs force,skip \
  --require-captured --auto-day
```

> **Doc-fix (2026-07-18): the checker's own flag is `--venue` (singular), never `--venues`.** `--venues`/plural
> `--data-types` are the LAUNCHER's flags (`launch-mtds-backfill-vm.sh`, invoked internally by this checker) — passing
> `--venues` to `scripts/pipeline_e2e_check.py` itself errors `unrecognized arguments`. This block is moot for a
> tradfi-only, all-shards run (§3c below) — omit `--venue`/`--data-types` entirely and let `--asset-group TRADFI` drive
> the full enumeration.

> **ALWAYS pass `--require-captured --auto-day` (added 2026-07-18).** Without them the matrix tests shards that CANNOT
> be proven and reports false failures:
>
> - **`--require-captured`** — only check cells that genuinely have captured PROD data. A force-leg re-downloads the
>   sampled instrument and asserts a parquet appears; on a cell with no data it fetches nothing and reports a FALSE
>   `no_parquet` failure. Unprovable cells are now recorded `skipped/no_captured_data_for_cell` instead of burning a VM.
> - **`--auto-day`** — per cell, substitute a day that actually HAS data when `--day` doesn't, preferring a
>   **non-first-of-month** day (day-1 is Tardis's free/no-auth tier, so a 1st exercises the UNAUTHENTICATED path). The
>   corpus is sparse and uneven — DERIBIT `options_chain` has been captured on exactly ONE day ever, `volatility_index`
>   on one, DERIBIT `liquidations` on three, OKX `trades` only on a 1st — so a single global `--day` cannot cover the
>   real surface. Measured 2026-07-18: a single-day run covered 46 of the 52 ever-captured Tardis cells; `--auto-day`
>   closes the remaining 6.
> - The run also unions in cells the PROD index shows as captured but the UAC lists omit — `OKX-FUTURES`/`OKX-SWAP`
>   (absent from `VENUES_BY_ASSET_GROUP['cefi']`) and `volatility_index` (absent from
>   `DATA_TYPES_BY_ASSET_GROUP['cefi']`): **8 live cells the matrix had never enumerated**, so it reported a clean sweep
>   while never testing them.
> - **`--bundle`** (force-leg-only sweeps) carries ALL shards on ONE VM per day at the VM's native 32-way concurrency
>   instead of one VM per shard. The cap-1 Tardis rule bounds concurrent **VMs** (one shared IP), NOT shards per VM — a
>   single VM fetching 32-wide is exactly what production backfill does. Measured 2026-07-18: the per-shard runner
>   spends ~155s of VM boot per cell versus 3-9s of actual fetching (~80% boot, ~3% fetch) to move 0.0-33 MB, so a
>   46-cell run burned ~2h of boot for ~47 MB. Bundling takes a 52-cell full-surface run from 52 VMs to **7** (one per
>   distinct day). Each shard is still verified independently. Do NOT use it with skip/live legs — the skip leg must
>   observe the force leg's object fingerprint, so bundling would change what it proves.
> - **`--tardis-only`** scopes to venues sourced via the Tardis adapter (`VENUE_TO_ADAPTER_KEY == 'tardis'`), excluding
>   native-REST HYPERLIQUID / ASTER / LIGHTER-ZKSYNC / PACIFICA-SOLANA / EXTENDED-STARKNET, which do not count against
>   the N=1 Tardis IP cap.
>
> **Interpreting verdicts while the raw→canonical instrument-id migration is in flight:** the downloader's
> `--instrument-ids` matches RAW venue-native symbols EXACTLY (no substring/ underlying expansion), while the manifest
> keys on canonical ids. So (a) the sampler takes the raw symbol from the PROD parquet listing, and (b) a cell whose
> PROD data is ALREADY canonical-named cannot be force-fetched at all and returns 0 rows — that is the migration
> boundary, NOT a pipeline error. When a verdict looks wrong, read the VM `run.log`
> (`Processed date=…: N venues ok, 0 failed, R total records`) as ground truth.

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

### 3a. CeFi DERIBIT / BINANCE-FUTURES bundle regression cells (explicit — the plain MVP loop misses one of these)

Per `plans/active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md` (the bundle backfill verification
plan) and `plans/active/issues/deribit_options_chain_af_g4_blocker_2026_07_03.md` (the structurally-absent-channel
regression), the `cefi` leg of Phase 1's per-`(asset_group, venue, data_type)` loop MUST cover these cells explicitly —
two are already inside the plain MVP loop above (call them out because they carry known regression history), the third
is a **hand-added negative check** the MVP loop will never reach on its own:

- **DERIBIT, OPTION → `options_chain`** — the ONLY Deribit-options MVP data_type
  (`CeFiMvpRule.instrument_type_data_types["OPTION"] = {"options_chain"}`,
  `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_mvp_scope_rules.py:553`); already inside the
  plain MVP loop, but this cell had a near-total historic failure (10,114 `attempted_failed` / 1 `captured` at
  discovery, still 99.999% failed 12 days later per the issue doc's 2026-07-15 corroboration) — treat it as the
  highest-value force/skip cell in the cefi matrix, not a routine one. Canonical GCS shape (per
  `market-tick-data-service/market_tick_data_service/reader.py`'s documented path convention, bucket resolved via
  `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="cefi")`):
  `raw_tick_data/by_date/day={DAY}/asset_group=cefi/venue=DERIBIT/instrument_type=OPTION/data_type=options_chain/underlying={BTC|ETH}/ticks.parquet`
  — bundled per `underlying=`, never per strike (see the shard-atom note above).
- **DERIBIT / BINANCE-FUTURES, PERPETUAL → `derivative_ticker`** (carries the `funding_rate` field) — MVP per
  `CeFiMvpRule.instrument_type_data_types["PERPETUAL"]` (`_mvp_scope_rules.py:554`); already inside the plain MVP loop.
  This is what "verify funding … populated" in the bundle-verification plan's P2 spot-checks means — `funding_rate` is a
  FIELD inside the `derivative_ticker` parquet (`CEFI_PERPETUAL_DERIVATIVE_TICKER` schema contract,
  `unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py:250`), not a separate `data_type`.
- **DERIBIT `futures_chain` — NOT an MVP data_type, and must NEVER be attempted.** This cell will **never** surface from
  the plain MVP-driven loop above: no CeFi venue (Deribit included) declares `futures_chain` anywhere in `CeFiMvpRule`,
  and Tardis confirms structurally that **no** CeFi Tardis venue exposes a `futures_chain` channel at all
  (`GET /v1/exchanges/<exch>` audit, cited in the bundle-verification plan). That MVP-scope blind spot is exactly what
  the 2026-07-15 regression exploited: the retry path kept attempting this off-MVP, structurally-absent channel anyway,
  re-stamping `attempted_failed` over a prior `empty_confirmed` reclass (66,007 → 112,727 rows in the manifest, 100.0%
  failed / 0 captured — see the bundle-verification plan's "P0 — DERIBIT + BINANCE-FUTURES bundle verification" section
  and the issue doc's "2026-07-15 corroboration"). **Add this as a hand-listed NEGATIVE-check cell** (never derived from
  `is_mvp()` — that's the whole point):

  ```bash
  # negative-check: DERIBIT futures_chain must show 0 attempted_failed for <DAY> (expected_unattempted/empty_confirmed
  # only — a captured or attempted_failed row here means the retry path is still hitting a channel Tardis never offers).
  python3 -c "
  from unified_trading_library import read_availability_index, resolve_bucket_name
  bucket = resolve_bucket_name(cloud='gcp', kind='market-data', asset_group='cefi')
  df = read_availability_index(bucket)
  day_col = 'date' if 'date' in df.columns else 'day'
  row = df[(df['venue'].astype(str).str.upper() == 'DERIBIT')
           & (df['data_type'] == 'futures_chain') & (df[day_col] == '<DAY>')]
  bad = row[row['capture_status'] == 'attempted_failed']
  print('FAIL: futures_chain attempted a structurally-absent channel' if not bad.empty else 'PASS: futures_chain not attempted')
  "
  ```

  - **PASS** = no row, or a row with `capture_status` in `{expected_unattempted, empty_confirmed}` — the shard was never
    (mis)attempted for `<DAY>`.
  - **FAIL** = any `attempted_failed` row for this cell — the regression is still firing; report it as a flagged gap
    labeled `regression_check: structural_channel_reattempted`, never silently reclassify it yourself — the
    reclassify-after-the-fact approach is what already failed once (66,007 reclassed rows the retry path then grew back
    past); the real fix is gating the writer so the shard is never attempted, and that fix belongs to the issue doc, not
    this skill.
  - Run the **force-leg twice in a row** for this cell (same `<DAY>`) and diff the `attempted_failed` count between the
    two reads — a rising count on the SAME day is the retry-storm signature re-firing, not a one-time miscapture.

### 3b. Content-level spot-checks (a `captured` capture_status alone doesn't prove the columns are real)

Per the bundle-verification plan's P2 spot-checks: a manifest `capture_status=captured` only proves a parquet exists,
not that its numeric columns are populated rather than an all-NaN blanket (the exact failure mode the plan's DERIBIT
finding hit: 136/138 "captured" rows were `PHANTOM_CAPTURED_NO_OBJECT`). Add these as report-level content assertions
against the actual test-bucket parquet the force-leg just wrote (read it directly with pandas/pyarrow, not a fresh PROD
read):

- **DERIBIT `options_chain`** (3 random `<DAY>`s from the force-leg run): assert the Deribit-only columns `mark_iv`,
  `greeks_delta`, `greeks_gamma`, `greeks_vega`, `greeks_theta` are not all-null across the underlying's parquet
  (`CEFI_OPTIONS_CHAIN_SNAPSHOT`, `_snapshot_contracts.py:55` — these five are `provided_by_venues={"DERIBIT"}`
  precisely because only Deribit's Tardis feed carries Greeks/IV).
- **BINANCE-FUTURES `derivative_ticker`** (1 `<DAY>` from the force-leg run): assert `funding_rate` and `open_interest`
  are not all-null (`CEFI_PERPETUAL_DERIVATIVE_TICKER`, `contracts.py:250`).
- A cell that passes `capture_status=captured` but fails this content check is a **distinct failure mode** — label it
  `content_check: NaN_blanket` in the report; don't conflate it with a manifest-level force/skip failure or the 3a
  structural-absence negative check.

### 3c. TradFi-only, ALL shards — Phase D terminal gate (added 2026-07-18)

Per `tradfi_consolidated_closeout_2026_07_18.md` Phase D — the plan's **terminal gate**: post-migration, prove
force-refetch + skip-if-fresh + a **canonical-shape regression** across **every** tradfi `(venue, data_type)` shard, not
just the MVP cells, before any real MVP backfill runs.

> **Databento concurrency knobs (added 2026-07-18, A3.1 — "large VM doing more, not wasting").** Databento is the slow
> stage; its limits are **per-IP** (~100 concurrent conn / 100 req/s × 0.8 ≈ **80 effective**, not per-key). A tradfi
> ohlcv backfill's concurrency axis is **dates** (one server-batched `download_batch` per date), so saturate the budget
> from ONE large VM via `launch-mtds-backfill-vm.sh --batch-date-concurrency N` (→ `VM_BATCH_DATE_CONCURRENCY` metadata
> → the UTL `ServiceCLI` gated concurrent-date driver, default 1 = serial/byte-identical) plus
> `DATABENTO_MAX_CONCURRENT_REQUESTS` (VM-metadata → env). **Opt-in / default-off** and requires the UTL driver deployed
> in the code tarball — omit it for a plain smoke check. Verify a real backfill's e2e win with the RX-counter method in
> the "Measuring throughput" section below (download MB/s) + manifest rows/hr, NOT `%CPU`/log-line rate.

**Enumeration is narrowed, not the raw cross-product.** TRADFI's raw `VENUES_BY_ASSET_GROUP × DATA_TYPES_BY_ASSET_GROUP`
list is 7 venues × 10 data_types = 70 cells, but `enumerate_mtds_shards` narrows TRADFI the same way it already narrows
PREDICTION — to each venue's UAC-declared fetchable capability set (`get_expected_data_types_for_venue`) — because most
of the raw 70 are either IS-domain reference surfaces MTDS batch can never fetch
(`corporate_action_confirmed`/`earnings_result`/`macro_result`) or billing-gated-by-design data_types no adapter serves
for that venue (`CME/tbbo`, `NASDAQ/mbp_10`, …). **Measured 2026-07-18, the real fetchable surface is 12 cells:**

| Venue                                                                       | Fetchable data_types                | Source                                                                                              |
| --------------------------------------------------------------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------- |
| NASDAQ                                                                      | `ohlcv_1s`, `ohlcv_1m`              | Databento                                                                                           |
| NYSE                                                                        | `ohlcv_1s`, `ohlcv_1m`              | Databento                                                                                           |
| CME                                                                         | `ohlcv_1s`, `ohlcv_1m`              | Databento                                                                                           |
| CBOE                                                                        | `ohlcv_1s`, `ohlcv_1m`, `ohlcv_24h` | Databento (1s/1m) + Yahoo (24h)                                                                     |
| ICE                                                                         | `ohlcv_24h`                         | Yahoo                                                                                               |
| KRX                                                                         | `ohlcv_24h`                         | Yahoo                                                                                               |
| FX                                                                          | `ohlcv_24h`                         | Yahoo — **no databento adapter** (`VENUE_TO_ADAPTER_KEY['FX'] == '__no_adapter_yet__'`); verify the |
| daily-KRW write path works or record it `BLOCKED-…`, never silently skip it |

**Operator data-type priority (2026-07-18) — what an MVP force-leg actually exercises:** Databento intraday MVP
backfills are **`ohlcv_1m` ONLY** (`mbp_10`/`trades`/`tbbo` are billing-gated by design — the 1-month L3 / 1-year L1
entitlement — not a bug to chase); daily cells (Treasuries, KRW) are Yahoo-sourced `ohlcv_24h`.

**`--mvp-only` for TRADFI is a hand-listed set, not `is_mvp()`.** Measured 2026-07-18:
`is_mvp(asset_group='tradfi', venue='CME', instrument_type='FUTURE', data_type='ohlcv_1m')` is **False** with no
`base_ccy` (only True once `base_ccy='ES'` is supplied) — this checker's enumeration-time MVP probe has no sampled
instrument yet, so it can never supply one, and naively probing every `InstrumentType` with none silently returns
**zero** tradfi cells. The engine instead hand-lists the operator's MVP universe (2026-07-18, expanded 2026-08-09) as 6
`(venue, data_type)` cells:

| MVP item                                                                                   | Shard             |
| ------------------------------------------------------------------------------------------ | ----------------- |
| S&P index futures + options, CME BTC/ETH futures + options, Treasury futures (ZT/ZF/ZN/ZB) | `CME/ohlcv_1m`    |
| Delta-one single-stock equities + ETFs (NASDAQ-listed)                                     | `NASDAQ/ohlcv_1m` |
| Delta-one single-stock equities (NYSE-listed)                                              | `NYSE/ohlcv_1m`   |
| Daily Treasury yield indices (US2Y/US5Y/US10Y/US30Y/US3M)                                  | `CBOE/ohlcv_24h`  |
| DXY (US Dollar Index) — added 2026-08-09 scope ruling                                      | `ICE/ohlcv_24h`   |
| Daily KRW/USD                                                                              | `FX/ohlcv_24h`    |

**The canonical-shape regression** (`--legs …,canonical`) is a 4th leg, TRADFI-only: after the force-leg writes to the
`-test-` bucket, it reads that shard's freshly-written `instrument_id`/`instrument_type` rows and asserts every
FUTURE/OPTION-embedded id matches `^[A-Z0-9-]+:(FUTURE|OPTION):[A-Z0-9]+-USD@LIN-\d{8}(-\d+(\.\d+)?-[CP])?$` (0 raw, 0
whitespace, 0 non-`@LIN`) — via the **shipped** `unified_api_contracts.assert_tradfi_derivative_ids_canonical` (never a
re-implemented regex, so it can't drift from the Phase-B migration scripts' own self-check). A shard with zero
FUTURE/OPTION ids (a pure `EQUITY`/`INDEX` `ohlcv_24h` cell) records a vacuous `passed`, not a false failure. Every
non-TRADFI shard records `skipped/canonical_shape_check_is_tradfi_only` — safe to request `canonical` alongside any
`--asset-group`.

**MVP cells first, then every shard:**

**Run via the §1a driver-VM launcher, not inline.** Underlying command:

```bash
cd market-tick-data-service && python3 scripts/pipeline_e2e_check.py \
  --day <DAY> --asset-group TRADFI --legs force,skip,canonical \
  --mvp-only --require-captured --auto-day
# then, once the 5 MVP cells are green:
cd market-tick-data-service && python3 scripts/pipeline_e2e_check.py \
  --day <DAY> --asset-group TRADFI --legs force,skip,canonical \
  --require-captured --auto-day
```

- No `--tardis-only` — every tradfi venue routes via `databento`/Yahoo, none via Tardis (`VENUE_TO_ADAPTER_KEY`); tradfi
  cells are NOT subject to the N=1 Tardis IP cap and may run in parallel (subject to real Databento rate limits).
- `--legs force,skip,canonical` omits `live` for tradfi by default — MTDS's live producer needs a registered
  `WSFeedConnector` per venue (Phase 3.5 rollout), which tradfi venues may not have; add `,live` once one is confirmed
  registered for the venue under test.
- **Green definition (the plan's Phase D exit criterion):** every tradfi `(venue, data_type)` cell carries a `passed`
  force + a labeled skip (`genuine`/`ambiguous`) + a `passed` canonical verdict. Combined with a green
  `data-pipeline-check-is --asset-group TRADFI` run (§ below), that is what "tradfi is code-complete, migrated,
  honestly-covered, and verified" means before the real MVP backfill runs.

### 3d. Reading a full-surface failure correctly — 3 lessons from a 2026-07-23 exhaustive run

A real all-shards run surfaced 21 failures that split into distinct, differently-actionable causes. Read the `reason`
string carefully before assuming which bucket a new failure belongs to:

- **SPOT preemption (`vm_not_success:vm_self_deleted_no_exit_status`)** is real infra noise, not a code bug — verify via
  `gcloud compute operations list --filter="targetLink~<vm-name>"` for a genuine `compute.instances.preempted` event,
  then just re-run that one leg. **Gap (2026-07-23), CODE WRITTEN 2026-07-30 (not yet shipped):** the fleet's
  auto-detect+relaunch DOES cover these VM name prefixes by registry match, but its trigger (a systemd-installed
  `PREEMPTED` signal file) only reliably fires partway through a multi-hour production backfill's boot — a single-shard
  smoke-test VM is disproportionately likely to die in the early-boot blind window first. `launch-mtds-backfill-vm.sh`
  (and `launch-instruments-backfill-vm.sh` for the IS-side pipeline-check VMs) gained a fix to also write the native GCE
  `shutdown-script` preemption signal (available from t=0, not gated on the systemd unit installing), closing this blind
  window — shipped `deployment-service@db5d3c7`. Manual re-run of a checker VM is still a safe fallback, just no longer
  the only recourse. Was tracked at `/plans/archive/issues/vm_fleet_preemption_autorecovery_gap_2026_07_23.md`
  (archived, all todos done).
- **An honest-empty shard's skip leg failing (`no_parquet_under`) does NOT mean the skip-leg checker is broken again** —
  but DOES mean re-verify against the currently-shipped fix before assuming it's the same already-fixed bug. Two related
  but DISTINCT code paths both had to be fixed (`mtds@98a81c26`): (1) the skip VM independently re-deriving
  `ok (honest-empty...)` itself, and (2) — the more common real path — the skip VM's freshness pre-flight correctly
  recognizing nothing is captured and skipping its own fetch entirely, writing NO per-VM manifest row, which used to
  fall through to a generic `no_parquet_under` failure. If a skip leg for an honest-empty shard fails on a version after
  `mtds@98a81c26`, that's new — don't assume it's understood.
- **A chain-bundle (`futures_chain`/`options_chain`) force leg failing `no_parquet_under` at an `--auto-day`-picked
  historical day is very likely NOT a day-selection problem — verify the real cause before pinning a different day.**
  `--auto-day` reads the manifest for a day with a real `captured` row and is usually right; pinning a "known-good" day
  does not help if the real cause is that the sampled `underlying` is now a canonicalized English product name (e.g.
  "AUD") being passed as `--instrument-ids` to a venue (CME/`GLBX.MDP3`) whose curated Databento symbol list uses raw
  exchange codes ("6A") — that mismatch is day-independent and will recur on any day. Read the VM's `run.log` for
  `instrument_ids filter [...] matched nothing ... curated symbol(s) available [...]` before touching the day. Full
  root-cause + open design question: `plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`.
  Separately, a chain-bundle sampler can pick a genuinely garbage `underlying` value from legacy manifest rows (e.g.
  `"TICKS"`, not a real product root) — fixed (`mtds@98a81c26`) by preferring a
  `is_recognized_tradfi_underlying()`-passing row when one exists in the matching set (TRADFI-only; CEFI chain shards
  like Deribit are not filtered this way).

## 4. Phase 2 — live leg (MVP-scoped)

**Run via the §1a driver-VM launcher, not inline.** Underlying command:

```bash
cd market-tick-data-service && python3 scripts/pipeline_e2e_check.py \
  --legs live --mvp-only --day <DAY>
```

- Same launcher, `--test-run`, scoped to MVP venues covering **both** IS + MTDS MVP scope. No separate force/skip split
  on this leg — `--mode live` already always forces.

### 4a. Live-leg Tardis guard-gap — defer Tardis-sourced venues while a backfill VM is running

> **The live leg's launcher (`launch-mtds-live.sh`) does NOT source `tardis-concurrency-guard.sh`**, unlike the batch
> force/skip launcher (`launch-mtds-backfill-vm.sh`). So a live-leg smoke check against a Tardis-sourced
> `(asset_group=cefi, venue=...)` cell can launch a VM concurrently with an active Tardis backfill/sharded VM, with no
> guard coordination between them.
>
> **Mitigation verified 2026-08-02 (BLK-5aa3ce78):** MTDS's live-mode capture path — both `--live-source native`
> (per-venue native WS connectors) and `--live-source tardis-machine` (the free, unauthenticated `stream-normalized`
> sidecar) — never opens the authenticated `datasets.tardis.dev` connection the N=1 IP cap protects. So the live VM does
> NOT materially contend for the shared Tardis IP with a concurrent backfill, and the measured 403-storm /
> false-`attempted_failed` corruption risk (see § 3 above) has not been observed in live-leg usage. The structural gap
> remains: the launchers are not coordinated, and if a future live connector change ever routes through the paid
> endpoint, it would contend.
>
> **Operational recommendation:** prefer deferring live-leg checks for Tardis-sourced venues while a real
> Tardis-consuming backfill/sharded VM is confirmed running. Scoping to cap-exempt venues only (`--tardis-only` is a
> batch-force flag — live-leg MVP scoping to HYPERLIQUID / ASTER / LIGHTER-ZKSYNC / PACIFICA-SOLANA / EXTENDED-STARKNET
> is manual) avoids the question entirely. If a live-leg check against a Tardis venue is needed concurrently with an
> active backfill, monitor the backfill VM's `run.log` for 403s during the live VM's window — a zero count confirms no
> contention this run, but does not structurally guarantee it for future connector changes.
>
> Full evidence: `/plans/archive/issues/mtds_live_smoke_vm_not_tardis_guarded_2026_07_28.md` (P1/P2 closed NOT-A-BUG
> 2026-08-02; P3 tracked here),
> `/plans/active/issues/mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02.md`.

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
- For `cefi`, the report MUST also carry the § 3a DERIBIT `futures_chain` negative-check verdict
  (`PASS`/`FAIL: regression_check=structural_channel_reattempted`) and the § 3b content-check verdicts
  (`PASS`/`FAIL: content_check=NaN_blanket`) for DERIBIT `options_chain` greeks/IV and BINANCE-FUTURES
  `derivative_ticker` funding/open_interest — as their own rows, distinct from the force/skip/live verdicts above (three
  different failure modes on the same cell must never collapse into one pass/fail bit).

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

## Measuring throughput — how NOT to get it wrong (added 2026-07-18)

**This check cannot measure throughput. Do not quote its numbers as pipeline MB/s.** It fetches ONE instrument per VM,
so it is boot-dominated: measured 2026-07-18, ~155s of VM boot per cell versus 3-9s of actual fetching (~80% boot, ~3%
fetch, ~15% finalize). Ten cells moved 2.1M rows but only 47 MB over ~40 min of wall clock — an aggregate ~0.02 MB/s
that says nothing about the pipeline. To measure throughput, run a REAL 32-wide backfill VM
(`launch-cefi-sharded-backfill.sh`) and read ITS logs.

When you do measure it, these five traps were all hit for real on 2026-07-18 and produced four successive wrong answers
(15-16 -> 13.5 -> 11.5 -> 9.4 MB/s) before the workload was properly characterised:

1. **Completion-based MB/s structurally UNDERCOUNTS under concurrency.** The metric only credits bytes when a shard
   COMPLETES, but 32-wide means 100-300 shards sit in flight with their bytes already downloaded and uncredited.
   In-flight grew 114 -> 216 -> 297 while the "rate" appeared to collapse — nothing was wrong. A falling completion rate
   is NOT evidence of a stall; check `requests` vs `successes` before concluding anything.
2. **Short windows are wave-noise.** Completions arrive in waves, so the same run yielded: 14.62 MB/s (66s window),
   14.00 (187s), 15.71 (307s), 16.36 (425s), 13.52 (535s), 11.41 (660s). Anything under ~15 min of fetching is not a
   number. Always exclude the first 300s (startup burst) AND require a long window.
3. **Throughput is VENUE-MIX dependent — always report the blended whole-run average.** Same VM, same day, zero errors:
   bybit-spot and friends ran 12-18.6 MB/s while DERIBIT (options chains) ran ~3.4 MB/s. A figure sampled while fast
   venues dominate is not a planning number. Any ETA must use the blended average, because a real backfill has to
   traverse DERIBIT too.
4. **Do not grep a bare `429`** — it matches millisecond timestamps (`14:40:18,429`) and manufactures a phantom
   throttling story. Match `HTTP 429` / `TooManyRequests`. Same for `error` (matches `error=-` in success lines).
5. **Low CPU with work in flight is normal, not a hang.** `cpu=1.6%` with 297 requests in flight means the box is
   waiting on network I/O — the expected state for a download-bound pipeline. Confirm via swap/rss/threads and the last
   completion timestamp before calling it stalled.

6. **Completion-based metrics CANNOT settle sustained throughput — use the VM's network RX counter.** Both MB/s and
   rows/s credit work only when a shard COMPLETES, so with 300+ large shards in flight (2-3M rows each) they collapse
   exactly when concurrency is working hardest. Measured 2026-07-18 over 32.4 min: 1,628 shards / 577.6M rows / 14.57 GB
   completed = 297k rows/s and 7.49 MB/s — but with hundreds of shards downloaded-but-uncredited, so the true rate is
   higher and UNQUANTIFIED. Four successive figures (15-16 -> 13.5 -> 11.5 -> 9.4 MB/s) were all produced by this broken
   instrument. **The authoritative measure is bytes off the wire**: `cat /sys/class/net/ens4/statistics/rx_bytes`
   sampled twice over 20-60s (via `gcloud compute ssh <vm> --tunnel-through-iap`). If SSH/IAP is unavailable, say the
   number is unmeasured rather than quoting a completion-derived one.
7. **Parquet output-MB/s is NOT venue-comparable.** Compression varies enormously: DERIBIT dated futures run 2-3M rows
   per shard but compress to ~6.5 MB, while bybit-spot runs ~289k rows at ~8.3 MB — ~10x the row work for smaller
   output. Comparing venues by output MB/s makes the row-heavy, well-compressing ones look "slow" when they are not.

**Ground truth is the VM `run.log`, never the report verdict**:
`Processed date=...: N venues ok, 0 failed, R total records` plus `StreamingParquetWriter: uploaded ...`. While the
raw->canonical id migration is in flight the report's pass/fail is actively misleading — a full IS sweep reported
`failed=17` when all 18 venues had genuinely written records.

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

## Extending to a new service

Copy this file, swap: the per-service script path (`<service>/scripts/pipeline_e2e_check.py`), the launcher script name,
the shard atom (MTDS = the 6-tuple incl. `data_type` — a new service defines its own), the MVP predicate, and the
sampled-instrument-id source. The shared engine (`unified_trading_library.pipeline_e2e_check`) and this skeleton never
change — see the `data-pipeline-check-is` skill for the sibling that already differs on shard atom (no `data_type`, no
instrument-level flag) and skip-leg proof (self-contained, no PROD pre-check needed).

## Not wired into `quality-gates.sh`

This check does real I/O + real VM spend + multi-minute-plus runtime — it stays a standalone, on-demand skill
(cron-schedulable later via the `schedule` skill), never part of `market-tick-data-service/scripts/quality-gates.sh`.
