---
doc_type: issue
title: MDPS t1-recon Cloud Run job OOMs every day — 7 consecutive failures, unrelated to reader-bridge deploy
summary: >-
  `uts-prod-market-data-processing-service-t1-recon` (GCP Cloud Run job, asia-northeast1) has failed EVERY scheduled
  execution for the past 7 days (2026-07-20 through 2026-07-26), each time with "The configured memory limit was
  reached" despite an already-generous 32Gi container limit. Discovered incidentally while triggering the job to verify
  the D3 reader-bridge deploy — the reader-bridge code is unrelated to this failure and is not implicated.
status: open
nature: issue
asset_group: [cefi, tradfi, defi, sports, prediction]
stage: [meta]
repos: [market-data-processing-service]
scope: [engineer, admin]
tags: [mdps, oom, cloud-run-job, candle-derivation, production-incident]
related: [/plans/active/cefi_satellite_ao_dispatch_batch2_2026_07_26.md]
created: 2026-07-26
last_updated: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  Discovered 2026-07-26 while verifying the cefi reader-bridge Cloud Run job deploy (see
  cefi_satellite_ao_dispatch_batch2_2026_07_26.md / cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md)
resolved_by:
---

# MDPS t1-recon Cloud Run job — 7 consecutive daily OOM failures

## What I found

Triggered `uts-prod-market-data-processing-service-t1-recon` manually (execution
`uts-prod-market-data-processing-service-t1-recon-kv4br`) purely to confirm the D3 reader-bridge fix
(`market-data-processing-service@0035f79`, already on `origin/main`) runs correctly. The execution failed at
2026-07-26T14:35:19Z:

```
Task uts-prod-market-data-processing-service-t1-recon-kv4br-task0 failed with exit code: 0 and message:
The configured memory limit was reached.
```

Logs show the job successfully bootstrapped, validated cloud connectivity, and began "Processing candles for 2026-07-25"
across **all 5 asset groups** (`cefi, tradfi, defi, sports, prediction`) and a combined list of **~50 data_types** in
one process, before being OOM-killed ~22 minutes in.

**This is not a one-off.** `gcloud run jobs executions list` shows every execution for the past 7 days failed
(`status.conditions[type=Completed].status = False`):

| Execution                                              | Completion (UTC)     |
| ------------------------------------------------------ | -------------------- |
| uts-prod-market-data-processing-service-t1-recon-kv4br | 2026-07-26T14:35:19Z |
| uts-prod-market-data-processing-service-t1-recon-p9kqm | 2026-07-26T03:09:31Z |
| uts-prod-market-data-processing-service-t1-recon-9lxrk | 2026-07-25T01:19:03Z |
| uts-prod-market-data-processing-service-t1-recon-pl2dx | 2026-07-24T01:14:27Z |
| uts-prod-market-data-processing-service-t1-recon-fcgp9 | 2026-07-23T01:09:06Z |
| uts-prod-market-data-processing-service-t1-recon-ffndb | 2026-07-22T01:06:00Z |
| uts-prod-market-data-processing-service-t1-recon-gcq7k | 2026-07-21T01:05:50Z |

The job's container is already configured with a 32Gi memory limit
(`spec.template.spec.template.spec.containers[0] .resources.limits.memory`), so this is not a case of an
obviously-too-small default — either the per-run working set has grown past 32Gi (more instruments/data_types/history
than when this limit was set), or there is a memory leak / unbounded accumulation in the candle-derivation path for a
subset of these data_types. **Not investigated further here** — root-causing which asset_group/data_type combination is
actually driving the memory growth, and whether the fix is a memory bump, a workload split (per-asset-group executions
instead of one combined run), or a code-level leak fix, is a real engineering judgment call, not a bounded todo I can
resolve unattended.

## Why it matters

MDPS candle derivation for `t1-recon` has not completed successfully in at least 7 days across ALL FIVE asset groups —
this is the process that reconciles/backfills candles this job is meant to keep current. Silent for a week because the
failure produces `exit code: 0` (a clean-looking shutdown from the container platform's point of view) rather than a
loud crash — worth checking whether this job's failures are even reaching the standing CI/VM-billing-waste alerting
paths, since "exit code 0 but OOM-killed" is exactly the kind of ambiguous signal those monitors are built to catch.

## Recommended next step

Operator/engineer judgment call on the fix direction (memory bump vs. per-asset-group split vs. leak fix) — flagging
rather than resolving unilaterally, per this being a genuine design decision, not a scoped todo.

## Resolution update (2026-07-26, interactive session)

Root-caused (not just flagged) and fixed. `check_upstream_manifest_has_live_gap()` in
`market_data_processing_service/app/core/dependency_checker.py` read the upstream `availability_index.parquet` with
`columns=` pruning but **no date filter**. Confirmed via `RESOURCE_SAMPLE` log timing correlation (both RSS spikes —
15947MiB and 18706MiB — land entirely inside this one call's window, both times, deterministically) and via a direct
`pyarrow.parquet.ParquetFile` metadata check: the DEFI upstream index has grown to ~27.4M rows (~1.0GB compressed) vs
CEFI's 8.7M rows (~152MB) — an unfiltered decode of even a handful of pruned columns across every row still materializes
12-18GB of pandas/polars overhead. The sibling call `check_shard_freshness` (same function, called just before this one)
already applies `filters=[("date", "==", date)]` via UTL's row-group pushdown — this call site was simply the one left
unfiltered. Not a regression of the archived `mdps_filter_pushdown_memory_audit_and_fix_2026_05_28` plan's fix (that
covered scanner file-listing + per-day `gc.collect()`; this is a different, previously-uncovered call site).

**Fix shipped**: added `filters=[("date", "==", date)]` to match the established pushdown pattern, plus a regression
test asserting the kwarg is passed. QG green. `market-data-processing-service@6b44226` (landed on `live-defi-rollout`).

**Not yet verified against a real production run** — the fix needs to reach `main` (GCP Cloud Build only triggers on
push:main; it's currently only on `live-defi-rollout`, pending the normal ~15-60min auto-promotion) and a fresh image
built before `uts-prod-market-data-processing-service-t1-recon` can be re-triggered to prove the OOM is actually gone,
not just theoretically fixed. That's the one remaining step — see Todos.

## Update 3 (2026-07-26/27, interactive session) — original fix CONFIRMED, but job still fails via a SECOND, distinct OOM

`market-data-processing-service@6b44226` promoted to `main` (verified: git content-diff, not SHA-ancestor — LDR→main
promotion squashes/rewrites, so `git merge-base --is-ancestor` is unreliable here; the actual
`filters=[("date", "==", date)]` line was confirmed present in `git show origin/main:.../dependency_checker.py`). Fresh
Cloud Build `dbfbf45a-09ba-496b-8463-7d5102aaff0c` (tag `14617c1`, 2026-07-26T22:59:10Z) matches that content exactly.

Re-ran the job: execution `uts-prod-market-data-processing-service-t1-recon-7q78v`, confirmed via
`gcloud artifacts docker images list --include-tags` to have used image `sha256:4ab492d3...` tagged `14617c1` — the
correct, fix-containing image, not stale.

**The original bug IS fixed** — `RESOURCE_SAMPLE` trend for this execution shows rss peaking at ~6.3GB (23:15:43) then
resetting to <1GB (23:16:47, next asset_group/date_type boundary) and climbing again to ~3.5GB (23:21:51). This is
categorically different from the pre-fix pattern (a gradual, unbroken climb to 14.86 GiB from the single unfiltered
27.4M-row DEFI manifest read) — no evidence of that call site reappearing.

**But the job still failed** — `Completed=False`, "The configured memory limit was reached", at 2026-07-26T23:23:00Z,
this time at ~13 min elapsed (vs ~22 min pre-fix — earlier, not later). Container limit confirmed unchanged at 32Gi
(`gcloud run jobs describe ... resources.limits` = `memory=32Gi`). Logs show:

- Last RESOURCE_SAMPLE before death: 23:21:51, rss=3516MiB (13.6%) — nowhere near the limit.
- Last app log line: 23:21:29, finishing `POLARS AGGREGATED` candle work for DEFI `dex_pool_swaps`/2026-07-25 (704
  files, 0 skipped, just-listed from `market-data-tick-defi-prd-central-element-323112`).
- **Zero log lines of any kind between 23:21:51 and the `WARNING Container terminated on signal 9` at 23:22:58** — a
  67-89s gap where >28GB was allocated with no intermediate log output at all (confirmed via direct
  `gcloud logging read` on the execution, not the truncated default 2000-line pull which only covered the first 34s of
  the run).

**A genuinely different, not-yet-root-caused bug** — this is NOT a regression of the fix; it's a second OOM path, likely
specific to `defi`/`dex_pool_swaps`'s unusually high per-day file count (704 for one asset_group/data_type/date) or
whatever runs immediately after that data_type's `ThreadPoolExecutor` batch completes (the trailing
`MEMORY_HIGH_WATER_MARK` `log_event()` call, or the transition to the next data_type/asset_group). Ruled out during this
session: `ProcessingResult` (lightweight dataclass, no embedded DataFrames — not the accumulator);
`ManifestFreshnessCache._refresh_locked` / `check_shard_freshness` (already date-filtered per the 2026-07-14
`mtds_backfill_vm_startup_oom_rc137` fix, and called once per category/date, not per data_type, so not in the hot path
here).

**Also fixed in this session, unrelated**: the interactive-session watcher script used to monitor this execution had its
own bug — it parsed `gcloud run jobs executions describe` output via a Python `print(status, '|', msg)` call, which
inserts a space before the `|`; the bash `${var%%|*}` split then left a trailing space on the status value, so
`[ "$cond_status" = "False" ]` never matched and the watcher polled uselessly for the full 45-minute timeout instead of
exiting the moment the real terminal `Completed=False` appeared at the 12-minute mark. Caught by manually re-deriving
state from `gcloud run jobs executions describe` directly, not from the watcher's own output.

## Update 4 (2026-07-27, autonomous session) — second OOM ROOT-CAUSED, FIXED, and verified against the exact crash shard; job still doesn't reach Completed=True end-to-end because of a SEPARATE, pre-existing, unrelated bug

**Root cause of the second OOM**: `ManifestWriter._read_with_generation()`
(`unified_trading_library/manifest_writer/_writer_io.py`, the legacy/non-per-VM canonical-index write path) does an
**unfiltered `pd.read_parquet()` of the ENTIRE `_index/availability_index.parquet`** on every `.flush()` call — no
column pruning, no row filtering, unlike the already-fixed read-path call site from Update 3. DEFI's index is
1,072,639,216 bytes / ~27.4M rows (confirmed via `gcloud storage du`). `write_candle_parquet()` /
`close_candle_streaming_writer()` (`market_data_processing_service/app/core/canonical_writer.py` +
`canonical_writer_streaming.py`) call `_flush_manifest_with_backoff()` — `ManifestWriter.write()` + `.flush()` — **once
per (file × timeframe)**, and `flush()` unconditionally forces the drain (not gated by the module-buffer time throttle).
The Cloud Run job never set `MANIFEST_PER_VM_SHARDS=true` (confirmed absent via `gcloud run jobs describe` before the
fix), unlike every sibling t1-recon job (`t1_recon_instruments_jobs.tf`'s `is-defi-t1-recon-job` /
`is-tradfi-t1-recon-job`, and the `market-tick-data-service` fast/cefi t1-recon jobs in the same terraform file) — this
job was simply missed when that convention was established. With `max_workers=8` (this job's vCPU count) worker threads
each independently flushing per shard, several **concurrent** full ~1GB/27.4M-row pandas decodes of the canonical index
blow past 32Gi within the observed 67-89s silent window — the SAME "unbounded full-index materialization" defect class
as the Update 3 bug, just in the WRITE path instead of the READ path, and gated on `MANIFEST_PER_VM_SHARDS` rather than
a date filter. This also explains why the crash landed the exact instant DEFI `dex_pool_swaps` started writing: it was
the ONLY data_type in that run whose manifest actually needed a write (every other asset_group/data_type was already
fresh in the manifest and skipped) — the first real exercise of this Cloud Run job's legacy write path in that run.

**Fix**: enabled per-VM shard writes for this job, matching the established pattern.

- Live (immediate):
  `gcloud run jobs update uts-prod-market-data-processing-service-t1-recon --update-env-vars=MANIFEST_PER_VM_SHARDS=true,VM_NAME=mdps-t1-recon-job`
  — confirmed present via a fresh `describe` before re-triggering.
- Source (durable): `deployment-service@a6c640178b8e6dca7f1b12ae93172d85cd3fc383` — added the same two env vars to
  `terraform/gcp/audit03_cron_provisioning.tf`'s `mdps_t1_recon_job` module, with a comment explaining the mechanism.
  `quality-gates.sh --no-fix --files terraform/gcp/audit03_cron_provisioning.tf` passed ("ALL QUALITY GATES PASSED
  (195s)"); shipped via `quickmerge.sh --agent`, verified present on `origin/live-defi-rollout` HEAD.
- Writes now route to `_index/per_vm/mdps-t1-recon-job.parquet` (small, per-writer, no CAS, no full-index read); reads
  stay correct because `read_availability_index()` always unions per-VM shards on top of the consolidated blob
  regardless of the reading caller's own settings, and the standing manifest consolidator folds the shard into the
  canonical index on its normal cadence.

**Verification — the exact crash shard, forced, on the exact crash date, twice**: triggered execution
`uts-prod-market-data-processing-service-t1-recon-p46vw` scoped to `MDPS_ASSET_GROUP=DEFI` /
`MDPS_DATA_TYPES=dex_pool_swaps` (via `gcloud run jobs execute --update-env-vars`, a per-execution override — the
permanent job env is untouched by this scoping) with `--start-date 2026-07-25 --end-date 2026-07-26 --force` (forces
reprocessing regardless of manifest freshness; the 2-day span was a workaround for a `gcloud run jobs execute --args`
quirk that rejects an identical `--start-date`/`--end-date` value pair, not a deliberate 2-day test). Result —
`status.conditions[type=Completed].status = True`, "Execution completed successfully in 19m9.03s":

| Date (subprocess-per-date leg)                                    | Files | Succeeded | Failed | Candles   |
| ----------------------------------------------------------------- | ----- | --------- | ------ | --------- |
| 2026-07-25 (the exact date/shard that OOM'd twice)                | 704   | 704       | 0      | 4,452,710 |
| 2026-07-26 (fresh data — 273 NEW files had landed since Update 3) | 273   | 273       | 0      | 1,825,822 |

Both legs logged "SUB-DIMENSION STATUS: All (data_type x instrument_type) combinations passed" and clean
`🏁 defi processing complete: N/N succeeded, 0 errors`. Live logs during the run repeatedly showed
`ManifestWriter: per-VM shard updated (... total entries, ... new, process_final=False) at market-data-tick-defi-prd-central-element-323112/_index/per_vm/mdps-t1-recon-job.parquet`
— direct confirmation the per-VM path is what's actually executing, not the legacy CAS path. RSS stayed flat
(565-808MiB) through the entire 704-file burst — a stark contrast to the pre-fix climb toward the 32Gi ceiling.
Container exited cleanly (`exit(0)`, no signal 9).

Minor, unrelated blemish noted (not the OOM bug, not blocking):
`atexit manifest flush failed ... (0 module + 2-4 per-vm rows lost): cannot schedule new futures after interpreter shutdown`
fired at the end of each `--subprocess-per-date` child's exit — a tiny (2-4 rows per leg, out of ~5000+ written)
shutdown-race loss in the atexit drain path, most likely those last few in-flight `ThreadPoolExecutor` futures racing
process teardown. Not investigated further here; low blast radius, and the manifest consolidator + a future recon pass
would pick up any genuinely missed shard.

**Full-job coverage — a SEPARATE, pre-existing, unrelated bug blocks a genuinely clean end-to-end `Completed=True`.**
Per the coordinator's explicit ask to confirm the WHOLE job (not just DEFI) completes clean: triggered a second,
unscoped execution `uts-prod-market-data-processing-service-t1-recon-dssh6` (full args, no asset_group/data_type
narrowing, date defaulted to 2026-07-26) that touched all 5 asset groups in one process. It reached a real terminal
state (`Completed=False`, exit code 1, `retriedCount=1` — Cloud Run's own automatic retry also failed the same way) —
but **not from an OOM**: `cefi`/`tradfi`/`defi`/`prediction` all completed cleanly (0 errors each — `defi` had 0
upstream files for 2026-07-26 at the time this leg ran), and `sports` failed hard with
`sports: 2/3348 succeeded, 3346 errors` — every failure is
`No SchemaContract registered for asset_group='sports' instrument_type=<MATCH_ODDS|MATCH_ODDS_LAY|OVER_UNDER_2_5|...> data_type='odds_movement_15m'|'odds_snapshot_15m'| 'odds_horizon_bucket' venue=<...>`
across ~20 bookmaker venues (WILLIAMHILL, BETFAIR_EX_EU, BETFAIR_EX_UK, BETONLINEAG, BETRIVERS, BETSSON, BETVICTOR,
CASUMO, CORAL, DRAFTKINGS, FANDUEL, LADBROKES_UK, LIVESCOREBET, PADDYPOWER, PINNACLE, SKYBET, SMARKETS, SPORT888,
UNIBET, UNIBET_UK, VIRGINBET) — `unified_api_contracts.internal.schemas.contracts. CONTRACT_REGISTRY` is missing schema
contracts for these (data_type, instrument_type, venue) combinations. This is a UAC schema-registration gap, has ZERO
relationship to this OOM fix (the fix only touches a Cloud Run job's env vars; it never touches sports code paths), and
was invisible for at least the last 3 known executions because the job always died from the OOM (during DEFI processing,
upstream of sports in the asset-group loop) before ever reaching sports. **Not a bounded fix I can guess at** —
registering ~20 venue × several instrument_type schema contracts requires real domain knowledge of what each
combination's actual schema should be; grepped `plans/active/issues/` and found no existing tracked issue for it, so
this is a genuine new finding. Filed as its own todo below rather than attempted inline.

Given (a) the specific OOM mechanism is directly proven fixed (per-VM shard write confirmed active in logs, RSS flat
through the exact crash shard/date, 977/977 file success), and (b) the full-unscoped run independently confirms NO OOM
occurs anywhere across all 5 asset groups (the only failure is the unrelated, deterministic, pre-existing sports schema
gap — a clean Python-level exception, not a SIGKILL/memory-limit event), a third, more expensive full-`--force` run
(which would additionally force full CEFI/TRADFI corpus reprocessing, adding real time/cost for a result already
strongly implied by the per-category `_cleanup_after_day` + `gc.collect()` isolation boundary already documented in
Update 3's own RSS-reset-at-boundary evidence) was judged not worth the added cost — this is a reasoned engineering
call, flagged here rather than silently assumed.

## Todos

- [x] [SCRIPT] P1. **Root-cause and fix the second OOM path** (the silent >28GB spike after DEFI `dex_pool_swaps`
      finishes candle aggregation). **DONE** — root cause: `ManifestWriter`'s legacy (non-per-VM) canonical-index write
      path does a full unfiltered read of the entire availability_index.parquet on every flush; fix: enabled
      `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=mdps-t1-recon-job` for this job (live via `gcloud run jobs update`,
      durable via `deployment-service@a6c640178b8e6dca7f1b12ae93172d85cd3fc383`). Verified:
      `uts-prod-market-data-processing-service-t1-recon-p46vw`, `status.conditions[type=Completed].status = True`
      ("Execution completed successfully in 19m9.03s") — 704/704 DEFI dex_pool_swaps files succeeded for 2026-07-25 (the
      exact date/shard that OOM'd in both prior executions), 273/273 for 2026-07-26, 0 failures, RSS flat 565-808MiB
      throughout (vs. the pre-fix climb toward 32Gi). See Update 4 for full evidence. (repo:
      market-data-processing-service, deployment-service)

- [ ] [SCRIPT] P1. **Register the missing UAC SchemaContract entries for SPORTS odds_movement_15m / odds_snapshot_15m /
      odds_horizon_bucket** across the ~20 bookmaker venues enumerated in Update 4 (WILLIAMHILL, BETFAIR_EX_EU,
      BETFAIR_EX_UK, BETONLINEAG, BETRIVERS, BETSSON, BETVICTOR, CASUMO, CORAL, DRAFTKINGS, FANDUEL, LADBROKES_UK,
      LIVESCOREBET, PADDYPOWER, PINNACLE, SKYBET, SMARKETS, SPORT888, UNIBET, UNIBET_UK, VIRGINBET) × instrument_type
      (`MATCH_ODDS`, `MATCH_ODDS_LAY`, `OVER_UNDER_2_5`, and whatever else the full error list in execution
      `uts-prod-market-data-processing-service-t1-recon-dssh6`'s logs enumerates — re-pull via `gcloud logging read`
      filtered to that execution name for the complete set, this doc only cites a representative sample). This is a
      SEPARATE, pre-existing bug from the OOM above (confirmed unrelated — the OOM fix never touches sports code) that
      was invisible until now because the job always died earlier (during DEFI) before reaching sports. It currently
      blocks `uts-prod-market-data-processing-service-t1-recon` from ever reaching a clean
      `status.conditions[type=Completed].status = True` end-to-end, even with the OOM fixed — every sports
      odds_movement/odds_snapshot/odds_horizon_bucket shard for these venues silently fails
      (`sports: 2/3348 succeeded, 3346 errors` observed 2026-07-27). Add the missing contracts to
      `unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY` (and `VENUE_CONTRACT_OVERRIDES` if venue-
      specific schemas differ), or confirm with an operator whether these venue/data_type combinations are even supposed
      to be live yet (a genuine design/data question, not purely mechanical — the AO-eligibility bar per
      `task_template.md` finding O applies: if the correct schema per venue isn't determinable from existing sibling
      contracts alone, this needs a human call on what the schema should be before an agent enumerates the fix). Once
      fixed, re-run `uts-prod-market-data-processing-service-t1-recon` unscoped and confirm
      `status.conditions[type=Completed].status = True` end-to-end across all 5 asset groups before closing this todo.
      (repo: market-data-processing-service, unified-api-contracts)
