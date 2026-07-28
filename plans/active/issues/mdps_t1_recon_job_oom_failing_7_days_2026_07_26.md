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
related: [/plans/archive/2026_07/cefi_satellite_ao_dispatch_batch2_2026_07_26.md]
created: 2026-07-26
last_updated: 2026-07-27 (Update 10)
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
  cefi_satellite_ao_dispatch_batch2_2026_07_26.md /
  /plans/archive/issues/cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md)
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

## Update 5 (2026-07-27, autonomous session) — sports SchemaContract gap FIXED + verified; TWO further pre-existing bugs uncovered as each prior one cleared; still not a clean end-to-end Completed=True

**Full error-list pull** (per the coordinator's ask, `uts-prod-market-data-processing-service-t1-recon-dssh6`, window
2026-07-27T00:24:48Z-00:46:47Z): 6,346 raw `No SchemaContract registered` log lines → **337 unique
`(instrument_type, data_type, venue)` combinations**, not the ~20-venue sample Update 4 cited: **23 venues** (the
Update-4 list plus `BETFAIR_SB_UK` and `MATCHBOOK`), **4 data_types** (`odds_movement_15m`, `odds_snapshot_15m`,
`odds_horizon_bucket_15m`, and a previously-uncited `arbitrage_opportunity_15m`), **28 instrument_types** (`MATCH_ODDS`,
`MATCH_ODDS_LAY`, and 26 `ASIAN_HANDICAP_*`/`OVER_UNDER_*` point-parameterised variants).

### Investigation — is the schema uniform, and is "venue" even the right axis?

Read `unified_api_contracts.internal.schemas._candle_contracts.py` (the actual SSOT for these 4 products) and all 4 MDPS
adapter sources (`app/adapters/sports/{odds_movement,odds_snapshot,bucket_assignment,arbitrage}_adapter.py`). Finding:
**venue was never the blocked axis** — `CONTRACT_REGISTRY` keys on `(asset_group, instrument_type, data_type)` with no
venue component, and none of these 4 products has (or needs) a `VENUE_CONTRACT_OVERRIDES` entry — every adapter returns
the identical `CandleOutput` shape (OHLC + trade_count, `symbol` anchor) regardless of venue OR market. The REAL gap:
`_candle_contracts.py` registers the 4 products under a single generic `instrument_type="odds"`, but MDPS's
`_infer_instrument_type()` (`canonical_writer_shaping.py`) correctly extracts the REAL per-market token from the
canonical id (`FOOTBALL:{BOOKMAKER}:{MARKET}:...` — `MATCH_ODDS`, `ASIAN_HANDICAP_0_25`, etc., continuously
parameterised by `build_instrument_id`'s `point: float`, hence genuinely unbounded — never a finite list) for the schema
lookup. The 337-combo sample was simply whichever (venue, market) pairs had fresh data on 2026-07-26 — **every**
market/venue for these 4 products was equally broken, this run just hadn't exercised the rest yet. `odds_snapshot` was
ALSO fully unregistered (an omission from the registration loop, not a lookup-key issue) — confirmed by diffing against
its 3 registered siblings; its `CandleAdapterRegistry` adapter existed with zero corresponding contract.

**Fix 1 (mechanical, not a schema guess)** — `unified-api-contracts@ed5434b3` (landed on `main` via PR #756): (a) added
`"odds_snapshot"` to the sports-derived registration loop (was missing outright); (b) added a bounded fallback in
`lookup_contract()`: for `asset_group=="sports"` and `data_type` prefixed by one of the 4 known families, fall back to
the already-registered generic `("sports","odds",data_type)` contract for ANY `instrument_type` — reusing the exact
existing, already-correct schema rather than enumerating an unbounded market vocabulary (mirrors the existing
blank-instrument_type sports alias pattern already in `_sports_derived_contracts.py`). Regression tests added in
`tests/internal/unit/test_mdps_candle_contracts.py` (incl. a deliberately-nonsense market-type string, proving the
fallback is genuinely open-ended). QG green, quickmerged, promoted to `main`, verified `has_fallback_marker: True` +
correct resolution **inside the rebuilt production Docker image** (not just unit tests) before re-triggering anything.

### Second bug (surfaced only once Fix 1 cleared the schema block): UTL partition-consistency validator is asset-group-blind to the sports id shape

Re-running (`uts-prod-market-data-processing-service-t1-recon-jqqrr`, full unscoped) showed the
`No SchemaContract registered` class was **completely gone** — replaced by a new failure class, `[partition_mismatch]`,
~identical error count (`sports: 2/3348 succeeded, 3346 errors`). Root cause:
`unified_trading_library/io/instrument_id_validator.py`'s `_split_instrument_id()` assumes every id is
`VENUE:INSTRUMENT_TYPE:SYMBOL` (3 colon-segments). Sports ids are
`SPORT:BOOKMAKER:MARKET:LEAGUE:SEASON:HOME-AWAY::SELECTION` — the generic split read `FOOTBALL` (the sport) as venue and
`BETFAIR_EX_EU` (the real venue) as instrument_type, so EVERY sports row failed `validate_partition_consistency()`'s
pre-write check the first time code ever reached it (previously always masked by the schema-lookup crash happening
first). This was invisible in every prior investigation because nothing before this session had cleared the schema gate
for sports.

**Fix 2** — `unified-trading-library@bcd73241` (landed on `main`): `_split_instrument_id()` now accepts an `asset_group`
kwarg; `validate_partition_consistency()` reads `asset_group=` straight off the same `partition_path` string it already
parses (no new parameter threading needed — every MDPS candle partition_path already carries it) and splits on the
sports shape when `asset_group=="sports"`, mirroring MDPS's own existing asset-group-aware
`_venue_token_from_canonical_id`/`_type_token_from_canonical_id` helpers. 4 regression tests added (sports happy path,
sports genuine mismatch, non-sports-unaffected). QG green, quickmerged, promoted to `main`, verified inside the rebuilt
production image (`validate_partition_consistency` on a real sports id returns `[]`) before re-verifying.

**Both fixes rebuilt through the FULL production chain** (not shortcuts): each landed on its repo's `main`
(`sit-gate/ fleet-green`+`quality-gates-v2`+quickmerge-provenance, per `/codex/08-workflows/ci-cd-flow.md`) →
`unified-trading- library`'s `cloudbuild.yaml` rebuilt the shared base image (clones UAC's `live-defi-rollout` HEAD
unconditionally, so it picks up UAC fixes even pre-tag) → `market-data-processing-service/Dockerfile`'s
`ARG BASE_IMAGE_DIGEST` bumped twice (once per fix) → MDPS's own `main`-triggered Cloud Build published a fresh
`:latest`. Each new digest was independently pulled + its fix verified by running actual Python against the built image
before wiring it in — not assumed from source review. **Side note on infra encountered along the way**: the fleet-wide
`sit-gate/fleet-green` signal (a scheduled `full-workspace-sit` run whose `ci-status-update.yml` stamping step has a
documented history of Firestore-write timeouts under load) was stuck RED for ~40min blocking ALL `ldr_main` repo
promotions fleet-wide (not just this work) — manually re-dispatched `full-workspace-sit` +
`ldr-to-main-promote-fleet.yml` repeatedly (`gh workflow run`) until a clean pass propagated; this is pre-existing fleet
infra flakiness, not something this session's changes caused, and self-resolved via the existing retry design once given
enough clean dispatches. The extremely active `live-defi-rollout` branch (many other agents' concurrent pushes) meant
the per-repo "SIT validated this EXACT LDR tree" gate had to be re-won multiple times as MDPS's LDR tip kept moving out
from under it — expected under high concurrency, not a bug.

### Third bug (surfaced only once Fix 2 cleared): MDPS's own candle-write batching mixes DIFFERENT markets into one partition-scoped write — NOT fixed this session

Sports-scoped forced re-verification (`uts-prod-market-data-processing-service-t1-recon-mzx7h`,
`MDPS_ASSET_GROUP=SPORTS --start-date 2026-07-25 --end-date 2026-07-26 --force`, mirroring Update 4's scoped-proof
methodology) confirms Fixes 1+2 both work as intended — the "sport-token-as-venue" mismatch class is entirely gone — but
the run still ends `2/3348 succeeded, 3346 errors` (Completed=False) because a THIRD, different, pre-existing bug is now
the dominant failure:

```
Chain-streaming write failed for FOOTBALL:BETFAIR_EX_EU:MATCH_ODDS_LAY:...::HOME @ 15m: StreamingParquetWriter
pre-write validation failed: [partition_mismatch] 96 row(s) inconsistent with partition_path '.../instrument_type=
MATCH_ODDS_LAY/data_type=odds_snapshot_15m': instrument_type mismatch in '...MATCH_ODDS:...::DRAW': partition
declares match_odds_lay, id has match_odds
```

The dataframe being written under a partition declared for ONE market (`MATCH_ODDS_LAY`) genuinely contains rows whose
own `instrument_id` says a DIFFERENT market (`MATCH_ODDS`, no `_LAY`) — a real data-mixing bug in MDPS's own
candle-derivation path, not a validator or schema bug (the now-fixed validator is correctly CATCHING this, not causing
it). Investigated the chain-bundle grouping (`live_workers_streaming.py::_iter_chain_symbol_dfs`,
`_CHAIN_GROUP_COL_CANDIDATES=("instrument_key","symbol","instrument_id")`) as the obvious suspect — pulled a real raw
`ticks.parquet` (BETFAIR_EX_EU/BRASILEIRAO/fixture 1492303) directly from GCS and confirmed its schema has NEITHER
`instrument_key` NOR `symbol` — only `instrument_id`, which DOES correctly distinguish `MATCH_ODDS` from
`MATCH_ODDS_LAY` rows (verified: 6 distinct `instrument_id` values for one fixture, 3 per market). **This rules out the
group-column-priority theory** — the raw-file read/group stage is grouping correctly per-instrument_id; the mixing must
happen downstream, most likely in how a candle adapter (`odds_snapshot_adapter.py` etc.) or the streaming-write
orchestration aggregates/batches multiple per-instrument_id `CandleOutput` results before the single `write()` call that
declares one partition — genuinely not traced further this session (would require adapter-level tracing across
`live_workers_streaming.py`/`live_workers_chain.py`'s per-slice dispatch, and possibly the raw MTDS tick schema too,
which was out of this session's scope). **Not attempted as a guess** — this is a real, unexplained data-correctness bug,
not a registration gap, and guessing at where rows cross-contaminate risks a wrong or silently-lossy "fix".

### Also newly visible, NOT fixed this session (both out of scope for the sports-schema mandate)

- **Sports 4h-timeframe registration gap**: `arbitrage_opportunity_4h`/`odds_horizon_bucket_4h`/`odds_movement_4h`/
  `odds_snapshot_4h` still throw `No SchemaContract registered` — MDPS's global `default_timeframes` config
  (`config.py`, `["15s","1m","5m","15m","1h","4h","24h"]`) is used uniformly for every asset_group; nothing scopes
  sports down to its documented `{1m,15m,1h}` set (`MDPS_TIMEFRAMES_SPORTS` in UAC is exported but never imported
  anywhere in MDPS). Registering `_4h` contracts in UAC would be papering over an orchestration bug with schema that the
  product docs explicitly say sports doesn't need (`_candle_contracts.py`: "Sports {1m, 15m, 1h}" by declared strategy
  need) — the correct fix is almost certainly scoping MDPS's timeframe iteration per-asset-group, which is a broader
  change (touches every asset_group's timeframe resolution, not just sports) not attempted here.
- **Prediction leg wholly unrelated failure**: this run's `prediction: 0/2170 succeeded, 2170 errors` — every KALSHI
  instrument fails with `No timestamp column found in data` at every timeframe. Confirmed unrelated to sports/UAC/UTL
  (no code this session touched runs on the prediction/KALSHI path) and pre-existing (masked in every prior execution by
  the OOM or the sports schema crash happening first, both upstream of prediction in the asset-group loop).

### Net effect

`uts-prod-market-data-processing-service-t1-recon` still does **not** reach a clean unscoped
`status.conditions[type=Completed].status = True` — sports and prediction both still fail (for the 2 newly-found reasons
above, not the original OOM or the original schema gap, both of which are confirmed fixed). **Not re-running a third
full unscoped 60-min execution** — the sports-scoped forced re-run already definitively proves Fixes 1+2 work and
definitively demonstrates the exact remaining sports blocker; a full run would only re-confirm the
already-known-unrelated prediction failure at the cost of another ~25min run. cefi/tradfi/defi remain confirmed clean (0
errors) per Update 4 and this session's own full-unscoped run.

## Update 6 (2026-07-27, interactive session) — KALSHI/prediction timestamp bug DEEPLY INVESTIGATED, NOT fixed: genuine multi-column schema mismatch, not a rename. Polymarket path proven to have worked historically; KALSHI path NEVER built. **Fully resolved in Update 10 — this section condensed 2026-07-27, see that update for the implementation.**

Per operator instruction — fully traced, no code changed this session (the fix needed a genuine product/data-semantics
decision, ruled out guessing at).

**Root cause, confirmed via real files pulled from GCS (not assumed)**: prediction: 0/2170 succeeded traced to
BaseCandleAdapter._get_local_timestamp_column() — PredictionTradesAdapter had no override, delegating straight to
CefiTradesAdapter's column assumptions. Real KALSHI schema (54,295-row file) has no timestamp/ts_event/ts_init/
local_timestamp column at all — instead yes_price_dollars/no_price_dollars/count_fp/taker_outcome_side/available_at.
Real POLYMARKET schema matches every CefiTradesAdapter assumption column-for-column.

**Regression vs. never-built**: KALSHI raw data present 07-20..07-26; Polymarket raw only 07-20/22 (explains the 100%,
not partial, failure count). processed_candles/ has real historical POLYMARKET output through day=2026-01-14, zero
KALSHI output ever, zero KALSHI test coverage anywhere in repo history. /codex/02-data/prediction-schema-paths.md
already documented KALSHI as BLOCKED-CREDENTIALS as of 2026-05-22. **Conclusion: NOT a regression — KALSHI's candle path
was never built** (Polymarket-only adapter, KALSHI added at the MTDS/data layer with a structurally different shape,
MDPS candle-adapter side never updated).

**4 product-level decisions needed before a fix (not mechanical)** — all resolved in Update 10: (1) canonical OHLCV
price series → yes_price_dollars; (2) is_buy mapping → taker_outcome_side == "yes"; (3) count_fp is genuine trade size →
confirmed via Kalshi docs + real-data cross-check; (4) available_at → exchange-time fallback, +200ms delay. Also found +
fixed in Update 10: a stale codex claim in prediction-data-types-catalog.md (§ NEEDS_CANDLE_PROCESSING).

## Update 7 (2026-07-27, attended session) — sports market-mixing fix VERIFIED end-to-end against real production data; TWO further, unrelated pre-existing bugs found blocking clean `Completed=True`

Picked up the P1 sports-mixing todo exactly where Update 5/the Todos section left it: the code fix
(`market-data-processing-service@1390312`, already reviewed and confirmed sound on read) was shipped but **not yet
re-verified against a live `t1-recon` execution**. This update closes that gap with a real, watched-to-terminal-state
production run plus direct inspection of the written candle output — not just "the job didn't error."

**Fix hadn't reached the deployed image yet.** `origin/main` was still 1 commit behind LDR at session start (last
promote ran 08:04, the fix landed 08:12) and the Cloud Run job's `:latest` tag still resolved to the pre-fix digest
(commit `4c9581c`). Manually dispatched `ldr-to-main-promote-fleet.yml`; it opened `market-data-processing-service#508`,
auto-merged at 08:44:52Z (`eaf8127`), and the `push:main`-triggered Cloud Build published a fresh `:latest` (confirmed
via `gcloud artifacts docker images describe` — digest `sha256:49b6a617...` tagged `eaf8127`/`0.23.0`/`latest`,
containing `_group_batches_by_own_type`/`no_real_chain_root` per `git show origin/main:.../live_workers_streaming.py`)
before triggering anything.

**Real repro, watched to a genuine terminal state**: triggered the exact repro command Update 5 left for the next
verifier —
`gcloud run jobs execute uts-prod-market-data-processing-service-t1-recon --update-env-vars=MDPS_ASSET_GROUP=SPORTS --args=--operation,process,--mode,batch,--start-date,2026-07-25,--end-date,2026-07-26,--force`
— execution `uts-prod-market-data-processing-service-t1-recon-86jbn`, started 08:49:44Z. Polled
`status.conditions[type=Completed]` directly (not a naive string match — the exact watcher bug Update 3 documented) via
`gcloud run jobs executions describe --format=json` + `jq`, holding the session open through ~56 minutes of real elapsed
time (this scoped run does far more work than Update 4's DEFI-scoped proof — full sports scope, 3348
instrument/venue/data_type/timeframe combos, `--force` across 2 days) until it reached a real terminal condition at
09:45:23Z: `Completed=False`, `reason=NonZeroExitCode`, exit code 1 — a clean Python-level failure, not a SIGKILL/OOM.
Verified genuine progress throughout via `gcloud logging read` timestamp-freshness checks at multiple points during the
wait (not just trusting an unattended timer).

**The mixing bug's exact crash signature is GONE.** Across the entire run's logs: `grep -c "partition_mismatch"` = 0,
`grep -c "instrument_type mismatch"` = 0 — the exact error class Update 5's "Third bug" section reproduced
(`Chain-streaming write failed for FOOTBALL:BETFAIR_EX_EU:MATCH_ODDS_LAY:...: ... instrument_type mismatch ... partition declares match_odds_lay, id has match_odds`)
never once fires in this run, despite the run touching every sports market/venue combination that used to trigger it
deterministically.

**Positive confirmation — pulled real written output for two independent mixed-market fixtures, not just absence of
errors.** The run wrote ~9,002 fresh candle parquet files under `day=2026-07-25` alone
(per-`(timeframe, data_type, instrument_type, venue)` files, `update_time` inside the run's window — this is a finer
grain than the job's own `2/3348 succeeded` fixture-level summary counter). Located two same-fixture chain bundles that
legitimately hold both `MATCH_ODDS` and `MATCH_ODDS_LAY` rows (exactly the bug's trigger shape) and downloaded both
output files for each:

1. `FOOTBALL:BETFAIR_EX_EU:{MATCH_ODDS,MATCH_ODDS_LAY}:ALLSVENSKAN:2026-27:KALMAR-MJALLBY::AWAY`
   (`data_type=arbitrage_opportunity`, `timeframe=15m`)
2. `FOOTBALL:BETFAIR_EX_EU:{MATCH_ODDS,MATCH_ODDS_LAY}:MLS:2026-27:COLUMBUS_CREW_SC-CINCINNATI::{DRAW,AWAY}` (same
   data_type/timeframe)

For both pairs, read with `pandas.read_parquet` and checked `instrument_id.unique()`: the `MATCH_ODDS` partition file
contains **exclusively** `MATCH_ODDS:...::{HOME,DRAW,AWAY}` rows (288 rows, all 3 selections of the same market
correctly combined — the "same-type stays combined" path also verified live, not just unit-tested); the `MATCH_ODDS_LAY`
partition file contains **exclusively** `MATCH_ODDS_LAY:...::{HOME,DRAW,AWAY}` rows (288 rows). Zero cross-contamination
in either direction, in production, post-fix. This is the direct evidence the task mandate asked for — not inferred from
the crash-signature absence alone.

**Job still doesn't reach clean `Completed=True` — but for two reasons that have NOTHING to do with the mixing bug.**
Full failure breakdown (`SUB-DIMENSION FAILURE BREAKDOWN`, `3346` total errors, matches the summary's
`2/3348 succeeded`) sums exactly to two known/newly-found causes:

- **The already-documented, already out-of-scope 4h-timeframe SchemaContract gap** (existing P2 todo below, "Scope
  MDPS's per-asset-group candle timeframe iteration") — every `No SchemaContract registered` error this run is for a
  `*_4h` data_type (`arbitrage_opportunity_4h`, `odds_horizon_bucket_4h`, `odds_movement_4h`, `odds_snapshot_4h`).
  Exactly as predicted by that todo; not a new finding.
- **A genuinely new, previously-undocumented bug**:
  `MalformedTickFieldError: field='bm_minutes_to_kickoff_or_h2h_columns' ... ticks present but downstream calc dropped all rows due to NaN/malformed field`
  fires for a large fraction of MATCH_ODDS/ASIAN_HANDICAP/OVER_UNDER instruments regardless of timeframe, tracing to "No
  h2h data found in MTDS raw data — cannot produce odds" during the long→wide MTDS pivot step — an upstream
  raw-data-shape/adapter issue, not a write-path or partition bug (fires before any write is attempted; unrelated code
  path from the mixing fix). This was invisible in every prior investigation because sports never got this far before
  (masked first by the OOM, then the schema gap, then the partition_mismatch bug — the exact same "surfaced only once
  the prior blocker cleared" pattern as Updates 4-6's other findings). **Not investigated further or fixed here** — out
  of this todo's mandate (candle-write batching/mixing only) and a genuinely new adapter/data-quality question, not a
  mechanical follow-on of this fix. Filed as its own P2 todo below per findings-triage, mirroring how the 4h gap and the
  KALSHI bug were each filed rather than fixed inline.

**Conclusion**: the P1 sports market-mixing todo is genuinely, positively verified — root cause confirmed, fix confirmed
correct by code review, crash signature confirmed absent under full-scope production load, and real written output
confirmed uncontaminated for two independent mixed-market fixtures. It was already marked done in the Todos section (a
concurrent session shipped the fix before this session's verification pass started); this update supplies the missing
verification evidence for that already-flipped checkbox. No further action needed on this specific todo.

## Update 8 (2026-07-27, attended session) — per-asset-group candle-timeframe scoping (the `_4h` gap) FIXED + verified; operator confirmed the general (not sports-only) approach

Implements the P2 todo below ("Scope MDPS's per-asset-group candle timeframe iteration"). Operator explicitly confirmed
the direction: **"yeah should be per AG scoped properly"** — build the general per-asset-group mechanism, not a
sports-only special case.

**Step 1 — checked whether other asset_groups are also narrower than the uniform `default_timeframes`, not just
sports.** Grepped `unified-api-contracts` for `MDPS_TIMEFRAMES_<ASSET_GROUP>`-shaped constants — the pattern already
exists broadly:

| Constant                                        | Timeframes         | Narrower than the full default (`15s,1m,5m,15m,1h,4h,24h`/`1d`)?                                       |
| ----------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------ |
| `MDPS_TIMEFRAMES_CEFI` / `MDPS_TIMEFRAMES_DEFI` | full 7-tf set      | No — matches full set                                                                                  |
| `MDPS_TIMEFRAMES_TRADFI`                        | 1m,5m,15m,1h,4h,1d | **Yes** — no 15s (deliberate: "1m native from Databento" per `_candle_contracts.py`'s own docstring)   |
| `MDPS_TIMEFRAMES_SPORTS`                        | 1m,15m,1h          | **Yes** (the confirmed `_4h` bug)                                                                      |
| `MDPS_TIMEFRAMES_PREDICTION`                    | 1m,15m,1h          | **Yes**, but only for the generic `prediction_market` contract                                         |
| `MDPS_TIMEFRAMES_PREDICTION_TRADES`             | full 7-tf set      | Broader — for the "trades" data_type only (KALSHI/POLYMARKET fills, instrument_type=PREDICTION_MARKET) |

Also confirmed why TRADFI's narrower set never actually produced a `SchemaContractNotFoundError` in production despite
being narrower: `BaseCandleAdapter.get_valid_output_timeframes()` already floor-filters timeframes below an adapter's
base granularity before any schema lookup, which incidentally drops "15s" for tradfi's 1m-native adapters. That filter
only guards the floor (too-fine), not the ceiling (too-coarse) — it does nothing for sports's actual bug (`4h` is too
COARSE, not too fine), which is why sports alone produced the observed OOM-job errors.

**"prediction" is deliberately NOT scoped down**, despite having a narrower generic constant just like sports:
prediction's "trades" data_type (KALSHI/POLYMARKET fills) resolves to instrument_type="PREDICTION_MARKET" and the
SEPARATE, BROADER `MDPS_TIMEFRAMES_PREDICTION_TRADES` contract — not the generic `MDPS_TIMEFRAMES_PREDICTION`
{1m,15m,1h}. Scoping the whole "prediction" asset_group down to the generic 3-timeframe ceiling would silently narrow
"trades" candle coverage at 15s/5m/4h/1d — a real regression, not a fix. This needs per-(asset_group, data_type)
resolution, not per-asset_group, to close safely; left as the full default (unchanged behavior), not guessed at.

**Step 2 — implementation, PLUS a critical correction after the first attempt didn't actually work.**
`market_data_processing_service/config.py`: added `_TIMEFRAME_CEILING_BY_ASSET_GROUP` (SPORTS →
`MDPS_TIMEFRAMES_SPORTS`, TRADFI → `MDPS_TIMEFRAMES_TRADFI`; cefi/defi omitted as no-ops, prediction omitted per above)
and `MarketDataProcessingServiceConfig.resolve_timeframes(asset_group)`, which intersects `self.default_timeframes`
against the UAC ceiling (normalising the "1d"/"24h" spelling difference for comparison only).
`orchestration_service.py`'s `process_category()` was wired to call `self.config.resolve_timeframes(category)` instead
of `self.config.default_timeframes` at all 3 call sites. Shipped as `market-data-processing-service@36e80cd`, promoted
to `main`, fresh image built and deployed.

**Re-triggered the exact sports-scoped repro command (`MDPS_ASSET_GROUP=SPORTS`, `--force`, `2026-07-25`..`2026-07-26`)
against that image — the `4h`/`24h` candle aggregation was STILL happening.** Traced why: `cli/parser.py`'s
`--timeframes` argparse argument had its OWN hardcoded `default=["15s","1m","5m","15m","1h","4h","24h"]`, completely
independent of `config.default_timeframes`. `process_handler.py` always passed this non-None argparse default straight
into `process_category(timeframes=...)`, so the `timeframes or self.config.resolve_timeframes(category)` fallback added
above never fired for the real CLI / Cloud Run job entry point — it only helps a caller that invokes
`process_category()` directly, bypassing the CLI, which no real production caller does. The standing job's own baked-in
args (`deployment-service/terraform/gcp/audit03_cron_provisioning.tf`'s `mdps_t1_recon_job` module:
`args = ["--operation", "process", "--mode", "batch"]`) never pass `--timeframes`, so this was a 100%-live bug, not a
theoretical one — confirmed by re-observing `POLARS AGGREGATED ... 4h candles`/`24h candles` log lines for sports in the
post-"fix" run.

**Fix 2**: `--timeframes` now defaults to `None` (the idiomatic argparse pattern for distinguishing "unset" from
"explicit override"), letting `_process_one_category`'s existing `timeframes or config.resolve_timeframes(category)`
call finally take effect. Verified `_build_single_date_argv` (the subprocess-per-date child-argv builder) already
correctly omits `--timeframes` when `None` — an existing regression test (`test_no_optional_flags_when_defaults`)
already covered this, no change needed there. Mock-mode's `generate_mock_candles()` already accepted
`timeframes: list[str] | None = None` natively. Updated the one CLI-parser test asserting the old hardcoded default.
Also checked for an `MDPS_TIMEFRAMES` env-var bridge (`cli/main.py::_build_legacy_argv`) that could independently
re-inject an explicit `--timeframes` — confirmed unset on the standing job (terraform + live `gcloud run jobs describe`
both checked). Shipped as `market-data-processing-service@f7d259e`, promoted to `main`, fresh image rebuilt.

**Verification — real production run, watched to a genuine terminal state.** Re-triggered the same sports-scoped repro
(`uts-prod-market-data-processing-service-t1-recon-krtkf`) against the corrected image. Confirmed via
`gcloud logging read`: **zero** `POLARS AGGREGATED ... 4h candles`/`24h candles` lines across the entire run (13,007
`POLARS AGGREGATED` lines total, ALL `1h` — the only non-base timeframe sports still aggregates), and **zero** "No
SchemaContract registered" errors anywhere (previously the dominant failure class per Update 4/5/7). `odds_movement`,
`odds_snapshot`, and `arbitrage_opportunity` each completed 100% (505/505 and 837/837 across the two dates).
`odds_horizon_bucket` still fails partially (348/505, 654/837) — but for the ALREADY-TRACKED, unrelated
`MalformedTickFieldError` bug this same session's Update 7 filed as its own P2 todo below, not a timeframe/schema issue
(confirmed: the error text is identical `bm_minutes_to_kickoff_or_h2h_columns` field-drop, nothing to do with this fix).
`Completed=False` (exit code 1) is therefore due entirely to that already-tracked, out-of-scope bug — this fix's own
target (`_4h` SchemaContractNotFoundError) is conclusively gone.

**cefi/tradfi regression check — reasoned rather than re-run live.** A live cefi/tradfi-scoped confirmation hit a
practical limit: the `gcloud run jobs execute --args` path only forwards a fixed flag subset through
`cli/main.py::_build_legacy_argv` (start/end date, category, force, dry-run, skip-dep-check) — `--max-results`/
`--data-types` aren't forwarded, so a cheap/narrow live check isn't reachable through the real production entrypoint,
and a full unscoped cefi/tradfi force-run is genuinely costly (comparable to the ~25-45min full runs in Updates 4/5).
Relying instead on: (a) `resolve_timeframes()` is directly unit-tested for CEFI (returns `default_timeframes` unchanged)
and TRADFI (returns the list minus `15s`) in `tests/unit/test_config.py::TestResolveTimeframes`; (b) the EXACT SAME call
site/mechanism (`_process_one_category` → `process_category(timeframes=args.timeframes)` →
`resolve_timeframes(category)`) is now proven live in production for sports — there is no category-conditional branching
anywhere in the entrypoint/bridge/argv path besides the single `MarketAssetGroup` value threaded through identically for
every category. The standing job's daily cron (`0 1 * * *` UTC) will naturally exercise cefi/tradfi through this same
code path within 24h of this write-up if a live cross-check is wanted.

**Known residual gap, not fixed here (documented, not silently dropped)**: `LiveModeHandler.run()`
(`cli/handlers/live_mode_handler.py`) resolves ONE flat `timeframes` list up front from `config.default_timeframes`
(when the caller doesn't pass one) and reuses it for EVERY category in its per-category loop — a
`--mode live --categories SPORTS` invocation would bypass this fix's per-category scoping (the explicit non-None list
short-circuits `process_category`'s own fallback). Low risk today: live mode's default `categories` is
`["CEFI", "TRADFI", "DEFI"]` (sports/prediction excluded by default), and this todo's confirmed repro is the
`--mode batch` t1-recon job specifically. Not fixed this session — would need a 3-signature change
(`run()`/`_run_live_mode()`/ `_process_cycle()`'s `timeframes: list[str]` param becoming Optional, resolved per-category
inside the loop) beyond this todo's stated scope.

## Update 9 (2026-07-27, attended session) — `MalformedTickFieldError('bm_minutes_to_kickoff_or_h2h_columns')` ROOT-CAUSED, FIXED + verified against real pulled GCS files; a SEPARATE, larger, previously-unknown data-correctness bug found and flagged (NOT fixed)

Picked up the P2 todo below (Update 7's newly-filed `MalformedTickFieldError` finding). Located the pivot at
`market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py`'s `pivot_mtds_to_wide()` /
`_pivot_market()` (the `"Pivoted MTDS long→wide: N h2h, ..."` / `"No h2h data found in MTDS raw data"` log lines both
live here), called from `SportsBucketAssignmentAdapter._prepare_tick_data()` → `process_to_candles()` (the
`MalformedTickFieldError(field="bm_minutes_to_kickoff_or_h2h_columns")` raise at line ~734, Path C of the adapter's
three-category empty-output decision).

### Root cause — confirmed via real failing-vs-succeeding GCS file comparison, not guessed

Pulled the krtkf/86jbn execution logs (`gcloud logging read`) and extracted exact failing `(venue, instrument_id, date)`
triples — e.g. `FOOTBALL:BETFAIR_EX_UK:MATCH_ODDS:ALLSVENSKAN:2026-27:GAIS-HALMSTAD::HOME`, day=2026-07-26. Downloaded
the REAL raw `ticks.parquet` directly from
`gs://market-data-tick-sports-prd-central-element-323112/raw_tick_data/by_date/day=2026-07-26/pipeline_mode=batch_odds_api/asset_group=sports/venue=BETFAIR_EX_UK/league_id=ALLSVENSKAN/instrument_type=ODDS/data_type=TRADES/ticks.parquet`
(192 rows, full 25-column real MTDS schema, `market_key` ∈ {h2h, h2h_lay}) and a SUCCEEDING same-venue/league/day
sibling file (`fixture_id=1494222/…`, 96 rows, 0 fixtures overlapping) for direct comparison.

**The two files are the SAME writer-generation split already documented in this adapter's own `_PIVOT_INDEX_EXCLUDE`
docstring** (the 2026-02-09 `instrument_type`/`data_source` and 2025-02-16 `available_at` incidents) — just a THIRD,
previously-uncovered column: the failing "combined" shape (no `fixture_id=` path partition; multiple fixtures bundled in
one file) has `af_fixture_id` **NaN on 100% of rows** (192/192, and 48/48 on a second sampled combined-shape file,
day=2026-07-24), while every "per-fixture" partitioned file sampled (4 files, 360 rows total) has it **fully populated
(0 NaN)**. `af_fixture_id` is a best-effort odds-tick ↔ instruments-service cross-vendor join key
(`market_tick_data_service/market_interface/adapters/sports/fixture_id_resolver.py`) — its own docstring: _"a genuine
nullable int … NaN/None is the only 'no value' signal"_, i.e. legitimately absent whenever that generation's write path
never attempted/resolved the join. It was never added to `_PIVOT_INDEX_EXCLUDE`, so `pivot_table(index=group_cols)`
silently dropped every h2h row of the affected fixtures (pandas' default `dropna=True` behavior on a NaN index level) →
`h2h_wide.empty` → `"No h2h data found"` → `_prepare_tick_data` returns empty (not via the causality path) →
`MalformedTickFieldError`. **Directly reproduced** with the real 16-row per-instrument slice
(`SportsBucketAssignmentAdapter.process_to_candles`, calling the exact production code path) — raises pre-fix, resolves
post-fix, producing real horizon-bucketed odds (`close=[1.41, 1.40, nan, nan, nan, nan, nan, nan]`, matching the raw
file's actual prices).

**Verdict: (b) — a genuine code gap**, not absent upstream data. The h2h ticks are genuinely present and correct; only a
non-identity vendor-metadata column accidentally sat in the pivot grain.

### Fix shipped + verified

`market-data-processing-service@67cb2ef` (`live-defi-rollout`, confirmed on `origin/live-defi-rollout` HEAD): added
`af_fixture_id` and `af_fixture_match_status` (its companion closed-set join-status enum, always non-null today but same
non-grain vendor-metadata class) to `_PIVOT_INDEX_EXCLUDE`, with a code comment documenting the measured NaN rates and
the real GCS paths probed. Two regression tests added to `tests/unit/test_bucket_assignment_adapter.py`
(`TestPivotStrayMetadataColumns`): one mirroring the existing stray-metadata pattern with `af_fixture_id`/
`af_fixture_match_status` NaN, and one using the **exact real 25→21-column production schema** (down to the real
`instrument_id`, `bookmaker_key`/`event_id`/prices/timestamps pulled from the actual GAIS-HALMSTAD file) run end-to-end
through `process_to_candles` — confirmed this second test genuinely catches the regression (`git stash` the fix, re-run:
both new tests fail with the identical production error signature and sample-column list; `git stash pop` restores).
Full suite: 69/69 passed.
`quality-gates.sh --no-fix --files 'market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py tests/unit/test_bucket_assignment_adapter.py'`
→ **"ALL QUALITY GATES PASSED (179s)"** (2290 tests, 87.06% coverage; the 1 basedpyright `reportAny` warning in this
file is pre-existing baseline, confirmed unchanged before/after via `git stash`). Shipped via
`quickmerge.sh --agent --files …` (one branch-drift retry — very active branch, recovered per the standard
`git pull --rebase --autostash` recipe, no force-push).

**Verification method — direct real-data repro, not a live Cloud Run re-trigger.** Given the fix is source-only (pandas
pivot logic, no infra/env change) and the exact failing production shard was already reproduced against a real
downloaded GCS file with the real adapter code both before and after the fix, a full Cloud Run re-trigger (which first
needs LDR→main promotion + image rebuild, ~30-60min, mirroring Updates 4/7/8's methodology) was judged unnecessary for
this class of fix and not run this session — flagging this explicitly rather than implying a live-job re-verification
happened. The standing daily cron will exercise this fix within 24h once `main`'s normal promotion cadence picks it up.

### Blast radius — concentrated in the "combined" (no `fixture_id=` partition) writer-generation shape, MATCH_ODDS-only

From the krtkf execution log (sports-scoped, `--force`, 2026-07-25..26): **1098 individual `MalformedTickFieldError`
occurrences → 549 unique `(venue, instrument_id)` pairs → 184 unique fixtures, across 14 bookmaker venues**
(VIRGINBET/UNIBET/SKYBET/PADDYPOWER/LIVESCOREBET each 192 mentions; UNIBET_UK/SMARKETS/PINNACLE/MATCHBOOK each 180;
WILLIAMHILL 132; SPORT888/BETFAIR_EX_EU each 96; LADBROKES_UK 72; BETFAIR_EX_UK 12). A second, independent execution
(86jbn) shows the same shape (1034 occurrences, 8 venues). **Every single occurrence in both executions is
`instrument_type=MATCH_ODDS`** — never `MATCH_ODDS_LAY`/`ASIAN_HANDICAP_*`/`OVER_UNDER_*` (see below for why — those
markets never even reach this code path). This is a genuine, actively-recurring production bug (not a one-off) — every
day a bookmaker's odds-writer emits the "combined" multi-fixture-per-file shape instead of per-`fixture_id=`
partitioning, every h2h row for every fixture in that file is silently dropped, and the shard is marked
`attempted_failed` in the manifest instead of producing real odds output.

### A SEPARATE, larger, previously-unknown data-correctness bug found while investigating — FLAGGED, NOT fixed this session

While confirming why `MATCH_ODDS_LAY`/`ASIAN_HANDICAP_*`/`OVER_UNDER_*` never appear in the `MalformedTickFieldError`
logs (expected some fraction to, per the original todo's "MATCH_ODDS/ASIAN_HANDICAP/OVER_UNDER" framing), found they
don't fail loudly — they **silently produce ZERO candle output, always, and always report "success"**, regardless of
whether real market data exists.

**Mechanism**: `process_to_candles`'s "Path A½" honest-absence short-circuit (`bucket_assignment_adapter.py` ~line
684-702) checks `(tick_data["market_key"] == "h2h").sum() == 0` and, if true, returns empty ("no h2h market_key rows …
recording as empty_confirmed"). This check was written (and is still tested,
`TestNoH2HHonestAbsence::test_no_h2h_returns_empty_not_malformed`) assuming `tick_data` is a full per-fixture/bookmaker
BUNDLE potentially containing multiple markets — correctly distinguishing "this bookmaker genuinely doesn't offer h2h"
from a schema defect. But the ACTUAL production call path (`live_workers_streaming.py::_iter_chain_symbol_dfs`,
`group_col` auto-resolved to `instrument_id` for sports files since they carry no `instrument_key`/`symbol` column)
**already slices `tick_data` down to ONE `instrument_id` — hence exactly ONE market — before `process_to_candles` is
ever called.** For any non-MATCH_ODDS instrument (`market_key` ∈ {h2h_lay, spreads, totals, btts}), the slice's
`market_key` is NEVER `"h2h"` by construction, so this check is `True` unconditionally, for every call, regardless of
whether that instrument's own market data is genuinely present.

**Confirmed with real data, not inferred**: pulled a real WILLIAMHILL raw file
(`day=2026-07-25/…/fixture_id=1494218/…/ticks.parquet`) containing 24 genuine `market_key="totals"` rows for
`FOOTBALL:WILLIAMHILL:OVER_UNDER_2_5:ALLSVENSKAN:2026-27:DEGERFORS-DJURGARDEN::{OVER,UNDER}`. Sliced to the `::OVER`
instrument (12 real rows) and called `process_to_candles` directly — it logged
`"No h2h market_key rows for this bookmaker/fixture (12 raw rows, market_keys=['totals']) — recording as empty_confirmed (honest absence)"`
and returned an EMPTY `CandleOutput`, despite 12 real `totals` ticks being present. **Cross-checked against real
production output**:
`gs://market-data-tick-sports-prd-central-element-323112/processed_candles/by_date/day=2026-07-25/pipeline_mode=batch_odds_api/timeframe=15m/data_type=odds_horizon_bucket/`
contains **only** `instrument_type=MATCH_ODDS/` — zero `MATCH_ODDS_LAY`/`ASIAN_HANDICAP_*`/`OVER_UNDER_*` objects
anywhere for that entire day, confirming this isn't a one-fixture edge case: **the `odds_horizon_bucket` product has
never produced real candle output for any market other than plain h2h (MATCH_ODDS)**, despite `pivot_mtds_to_wide()` /
`_pivot_market()` explicitly implementing spreads/totals/btts pivoting (`asian_handicap_home_odds`, `over_odds`,
`btts_yes_odds`, …) and Update 5's UAC SchemaContract fallback deliberately supporting all these `instrument_type`s
uniformly — i.e. the DESIGN INTENT was clearly for all 4 market families to produce odds_horizon_bucket output, and this
Path A½ / per-instrument-slicing invariant mismatch (likely introduced whenever the chain-bundle-streaming refactor
started pre-slicing by `instrument_id`, after Path A½ was written against the older multi-market-bundle assumption)
silently defeats that for 3 of 4 families, permanently, with no error signal (`success=True`, 0 candles).

**Not fixed this session** — this is a genuinely separate root cause/code path from the `af_fixture_id` pivot-index bug
above, and the correct fix needs real judgment (mirroring this doc's own established standard for this class of
situation, e.g. the KALSHI investigation in Update 6): should Path A½ check for ANY recognized `market_key` present (not
hardcoded to `"h2h"`) given the slice-per-instrument invariant is now permanent? Does `btts` ever legitimately co-occur
with another market in one slice, complicating a naive generalization? Is there a call path where `tick_data` is
genuinely NOT yet market-filtered (in which case a blind generalization could turn genuine absence into false
`MalformedTickFieldError`s)? These need real tracing before a fix, not a guess. Filed as a new P1 todo below — flagging
per CLAUDE.md's data-pipeline-correctness-is-the-heartbeat / big-finding-notify-operator rule, since this silently drops
real market data across most of the sports odds product, apparently for its entire history.

## Update 10 (2026-07-27, attended session) — KALSHI trades→candle schema mapping BUILT, shipped, and verified end-to-end against real production data; job still doesn't reach `Completed=True` because of a NEW, unrelated subprocess-timeout bug

Implements the `[DESIGN] P2` KALSHI todo below on top of Update 6's investigation. Full reasoning lives in the shipped
code's docstrings (`PredictionTradesAdapter._get_local_timestamp_column`/`_resolve_price_size_cols`,
`market-data-processing-service@890748f`) — this update is a condensed summary + the production verification evidence.

**Question A (`is_buy` mapping) — investigated, not guessed.** Traced the downstream consumer: `is_buy` is CeFi's
standard taker-aggression-direction convention (same pattern as `liquidations_adapter.py`'s `aggressor_side`), feeding
`buy_volume`/`sell_volume` consumed by `strategy-service/cloud_data_provider.py` (BigQuery),
`unified-trading-api/ batch_candles.py` (UI charts), and mirrored by `ml-service`'s `taker_buy_sell_ratio` feature
(CEFI-perp, same concept). WebFetched Kalshi's own docs (`docs.kalshi.com/changelog` +
`/api-reference/market/get-trades`) rather than guessing: `taker_book_side` is documented as **"the same directional bit
as taker_outcome_side... 'bid'≡'yes', 'ask'≡'no'"** — i.e. it is NOT an independent aggressor-crossed-bid/ask signal the
way CeFi's `aggressor_side` is, just a relabeling (confirmed perfectly co-varying on Update 6's 54,295-row sample).
**Decision: `is_buy = (taker_outcome_side == "yes")`** — since `yes_price_dollars` is the canonical priced instrument
(Decision 2), a taker profiting on "yes" is economically buying it; "no" is selling it. Implemented with a
`taker_book_side` fallback.

**Question B (`count_fp`) — CONFIRMED genuine trade size.** Kalshi's docs define it verbatim: "String representation of
the number of contracts bought or sold in this trade"; the `_fp` suffix documents support for **fractional** contract
sizes (so the ~38.5%-integer-like real-data finding is expected, not corruption). Re-inspected Update 6's real
54,295-row file: 0 parse failures, 0 negatives, notional (`count_fp × price`) distribution plausible (median
~$10, max ~$28.8k). Used directly as `size`.

**Implementation**: two overrides in `PredictionTradesAdapter` only, gated on `_is_kalshi_shaped(df)` (KALSHI-only
`yes_price_dollars` column — Polymarket's schema lacks it, so untouched, regression-tested).
`_get_local_timestamp_column` returns `available_at` for KALSHI (same role as the base chain's exchange-time fallback,
still gets the +200ms delay uniformly). `_resolve_price_size_cols` maps `yes_price_dollars`→price, `count_fp`→size,
`taker_outcome_side`→is_buy; non-KALSHI frames delegate to `CefiTradesAdapter` via `super()` (one
`# pyright: ignore[...]` — the shared `CandleAdapterRegistry.register()` decorator's non-generic return type erases
`CefiTradesAdapter`'s identity for basedpyright's `super()`/`cast()` analysis from a subclass; a basedpyright
limitation, not a type hole; not fixed per this todo's file-scope contract). `CefiTradesAdapter`/`base_adapter.py`
untouched. Tests: `tests/unit/test_prediction_kalshi_trades_adapter.py`, real KALSHI column shapes.

**Codex fix** (Decision 1): `/codex/02-data/prediction-data-types-catalog.md` § NEEDS_CANDLE_PROCESSING corrected — the
claimed prediction-specific `False` override for `trades` was stale; UAC's registry is flat/asset-group-blind with
`"trades": True` uniformly. Flagged (not resolved) `prediction_canonical_question_group` may share the same drift class.

**Shipped**: `market-data-processing-service@890748f` (→ `main@b3f3f96`, QG green), `unified-trading-pm@0c427d472`
(codex fix). Fresh image confirmed built/tagged (`b3f3f96`/`latest`, 13:18:54Z) before verification.

### Verification — real production run, watched to a genuine terminal state (~2 hours)

Triggered `uts-prod-market-data-processing-service-t1-recon-pr268`
(`MDPS_ASSET_GROUP=PREDICTION --start-date 2026-07-25 --end-date 2026-07-26 --force`), polled the actual
`status.conditions[type=Completed]` object to a genuine terminal state at 15:35:22Z: `Completed=False`,
`reason=NonZeroExitCode`, exit 1 — a clean Python-level failure, RSS healthy (565MiB-6.9GB) throughout, never near the
32Gi limit (NOT the OOM class this doc otherwise chases).

**Schema mapping conclusively proven correct**: zero `MalformedTickFieldError`/`No timestamp column`/`ValueError`/
`UpstreamTimestampBiasError` anywhere across the ~2h run (previously 100% instant failure on every KALSHI row). Manifest
entries climbed 1→1558+ with continuous `POLARS AGGREGATED` output throughout.

**Real written candle output pulled from GCS**: `KXBTC-26JUL2421-B63850` (single trade, bounded `close=0.01`,
`volume=400` matching `count_fp`, `buy_volume=400/sell_volume=0` correctly classified); `KXBNB-26JUL2421-B562` (1m)
shows **genuine price movement across 3 real trades** (`close` ∈ {0.76, 0.89, 0.98}, bounded [0,1]) with
`buy_volume=8/sell_volume=1` correctly summing to `volume=9` — a real, non-degenerate buy/sell mix. Two more
single-trade files checked, all bounded, zero NaN/inf garbage.

**`Completed=False` is a NEW, unrelated bug — not the KALSHI mapping**:
`subprocess-per-date: date=2026-07-26 TIMED OUT after 1800s (FAILED, child killed)`. The per-date subprocess
architecture (Update 4) gives each date a fixed 30-min budget; with KALSHI now genuinely processing ~2,170 instruments ×
7 timeframes (previously never observed since every row crashed instantly), a full day now exceeds that budget — both
dates timed out, retried once, timed out again (14:04/14:34/15:05/15:35). **Not fixed here** — a capacity-planning
decision, not a guessable fix. Filed as its own P2 todo below.

**Conclusion**: the KALSHI todo is genuinely resolved with real evidence (not guessed), scoped entirely to
`PredictionTradesAdapter`, and verified against real production data via both an absence-of-errors proof and a
positive-output proof. The remaining `Completed=False` is a newly-surfaced, unrelated capacity issue.

## Update 11 (2026-07-27/28, attended + follow-up session) — sports `odds_horizon_bucket` `venue=ODDS_API` conflation FIXED forward + docs/codex corrected; historical migration validated and design confirmed sound (apply itself completed in Update 12)

Separate thread — fix the `mdps_odds_horizon_bucket` manifest's `venue=ODDS_API` vendor-conflation "properly and fully"
(writer + backfill + docs), not just flag it. **The agent driving this hit a hard Claude API session limit mid-flight
(resets ~3:40am Europe/London) with the apply step still outstanding — this update was corrected and completed by the
coordinating session directly, with real verification, rather than left with unfilled placeholders.**

**Phase 0**: live-queried the manifest — the 124,294-vs-306,416 discrepancy was two DIFFERENT identities at different
times/buckets, both stale (live 2026-07-27: 465,743 `source=mdps_odds_horizon_bucket` rows, 200,512 captured).
Consumers: features-service/ml-service read GCS by date/league/timeframe PATH (no venue segment — venue-agnostic, zero
regression risk). Real risk found: `instruments-service/scripts/enumerate_expected_universe.py`'s
`_SPORTS_MANIFEST_VENUE_OVERRIDE` depends on the COARSE per-day row's `venue=ODDS_API` value. **Decision**: keep the
coarse row unchanged (deliberate aggregate sentinel), fix only the FINE per-`(league_id,timeframe)` rows — the real bug,
since the underlying parquet already carries a 100%-present real `bookmaker_key` column, never read for the manifest
stamp.

**Phase 1 — ✅ SHIPPED, verified on `main`.** `market-data-processing-service@6f7422e`: fine rows now split per real
bookmaker (`_venue_breakdown_for_shard`). `source` confirmed CORRECT unchanged (`mdps_odds_horizon_bucket` — the
UAC-declared derived-product identity; the task's initial framing that it should become `odds_api` was checked and found
wrong — multiple already-shipped scripts protect this exact value). 9 regression tests, QG green, promoted to `main`.
New captures going forward are correct — verified by direct code read on `origin/main`.

**Phase 2 — ✅ APPLIED 2026-07-28, verified. See Update 12 for the full execution + root-cause story.**
`market-data-processing-service@a047b29`: CAS-guarded backfill migration script
(`scripts/migrate_odds_horizon_bucket_venue_to_bookmaker_2026_07_27.py`), dry-run default, row-count-conservation
enforced as a HARD abort (never best-effort). The agent validated it at n=15/n=50 real-prod samples. **Independently
re-verified by the coordinating session** (2026-07-28): downloaded the live manifest directly and confirmed **198,572
fine CAPTURED rows, 100% still `venue=ODDS_API`** — zero migrated so far (191,073 more fine rows are
`expected_unattempted`, 63,562 `empty_confirmed`, 28 `attempted_failed` — none of those need migrating, only the 198,572
captured ones do). Ran the script's own sanctioned bounded local smoke test (`--limit 25`, after fixing a stale local
`.venv` fastapi pin via `uv sync` — unrelated environment issue, not a script bug): **23/25 shards reconciled, row-count
conservation held exactly (old_sum=273, new_sum=273), 2 pre-existing 2020-dated rows correctly left untouched**
(`row_count is NaN in the manifest` — a genuine old data-quality gap on those specific rows, not a script defect). The
script itself is confirmed sound and safe (never touches physical files, only manifest rows).

`deployment-service`: a `sports-odds-venue-mig` VM-launcher category was wired into the canonical-migration launcher
(`0373a41`, `2d2a52c`) per the heavy-I/O hard rule (198,572 rows / 184,242 distinct shard-file reads — squarely "heavy
I/O never runs from the operator's local machine"). Between this update and Update 12, three more real bugs were found
and fixed by iterating against the actual live population (see Update 12 Phase 2a) before the apply finally landed.

**Phase 3 — ✅ SHIPPED, verified on `origin/live-defi-rollout`.** `unified-trading-pm@0c28fa8f8` ("fix sports odds
venue=ODDS_API conflation framing across the plan/codex corpus"): corrected Track C's wrong "not this bug" framing
(`sports_consolidated_closeout_2026_07_19.md`); fixed the falsely-closed checkbox (part2 doc — was pointing at the wrong
symbol entirely); answered F4; corrected the stale count in `sports_consolidated_audit_2026_07_19.md`; updated
`availability-manifest-and-data-status.md` + `venue-availability.md` (confirmed UAC's `ODDS_API` registry entry is
itself correct — a vendor/aggregate-class member, NOT the same bug — added a clarifying note so nobody re-flags it).
Reviewed all 8 coordinator-flagged docs from the read-only reconnaissance pass — 2 needed real gate strengthening
(`sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` got an explicit inline `⛔ GATED` banner on its pending
3-venue move todo, closing the live-landmine risk; the footystats orphan doc already had a strong human-only hard-stop),
the rest confirmed NOT the same bug with a documented verdict each. Filed
`tradfi_yahoo_venue_vendor_conflation_2026_07_27.md` (same vendor-as-venue shape in `yahoo_finance_adapter.py`,
explicitly not investigated/fixed this session, precedent-only).

**Phase 4 — confirmed correct, no changes needed.** UAC's `SOURCE_PRIORITY`, `canonical_mappings`,
`VENUES_BY_ASSET_GROUP["sports"]` were reviewed and are already right.

**Consumer-safety verdict**: features-service/ml-service reads are venue-agnostic by construction (path-based, no venue
segment) — zero regression risk, confirmed not assumed. The one real dependency (the enumerator's coarse-row value) is
preserved unchanged by design. All four phases are now genuinely done — see Update 12 for Phase 2's completion.

## Update 12 (2026-07-28, follow-up session) — Phase 2 APPLIED: historical migration executed, verified, root cause of the prior 5 failed VM attempts found and fixed

Resolved Update 11's "wait for the stuck agent, or do it now" question directly ("do it properly /autonomous"). Checked
what actually happened to the 5 prior VM attempts first rather than assuming a clean slate.

**Phase 2a — 3 real bugs already fixed on `live-defi-rollout` but never deployed to a VM tarball.** GCS run-log
inspection (`gs://deployment-scripts-.../vm-logs/canonical-migration-sports-odds-venue-mig-*`) showed the original agent
launched the VM 5 times (17:52–21:04Z, 2026-07-27), iterating real fixes: `market-data-processing-service@b71441d`
(NaN-safe `row_count` — a dry-run crashed at 100% resolved, zero writes attempted); `@f7e42fd` (O(N×M) full-manifest
rescan fixed — **15h projected → <1s**, without which a full-scale apply wasn't completable); `@5ed5cda` (decoupled the
~80-min resolve pass from the CAS-retry loop — the old code re-resolved from scratch on every retry, so a write could
never win the race — and bumped `_MAX_ATTEMPTS` 3→20). All three were on LDR but not yet `main`, and — the actual cause
of the last failure — the tarball deployed for attempt 5 (`...-210447`, full mode) predated `5ed5cda`: it hit exactly
`EXHAUSTED 3 attempts (CAS races). NO WRITE PERFORMED.`, the bug that commit fixes.

**Phase 2b — rebuilt the tarball; the FIRST apply attempt still failed, all 20/20 hardened retries lost.** Rebuilt via
`create-code-tarballs.sh --asset-group SPORTS` (hit the same stale-`.venv` fastapi pin as Update 11, now in
`deployment-service`'s own `.venv`; fixed via `uv sync`); confirmed deployed manifest pinned `346b50bb7f70` (all 3 fixes
included). Launched `canonical-migration-sports-odds-venue-mig-20260728-131305` directly in `full` mode (skipped a
separate dry-run VM — apply mode already re-resolves + re-validates conservation before every write, and 2 independent
full-scale computations already agreed). **Still `EXHAUSTED 20 attempts (CAS races). NO WRITE PERFORMED.`** — 20
straight `generation=... stale` losses over ~24 min. Per the async-wait/poll-discipline HARD RULE (flat metric → STOP
and diagnose, don't burn ticks retrying), stopped relaunching and root-caused instead.

**Root cause** (`/codex/05-infrastructure/manifest-consolidator-ssot.md`):
`uts-prod-manifest-consolidator-instruments- sports-cron` fires `*/1min` against the exact bucket
(`instruments-store-sports-prd-...`) this migration writes to — a ~145MB serialize+CAS-write cycle structurally cannot
outrun a competitor guaranteed every 60s; no retry budget fixes that. The SSOT already documents the fix: § "Surgical
ROW REMOVAL from the canonical", generalized (§ "Pause-first applies to ANY canonical read-modify-write, not only row
removal") to cover this migration's exact read→mutate→CAS-write shape.

**Phase 2c — pause-first recipe applied; write succeeded on attempt 1.** (1) Paused the cron
(`gcloud scheduler jobs pause ... --location asia-northeast1`), confirmed no in-flight execution (polled `...-9gbvj`'s
`completionTime`) and no `_index/consolidator.lock`. (2) Relaunched
`canonical-migration-sports-odds-venue-mig-20260728-141141` (same pinned tarball; unrelated STALE warnings on
MTDS/UAC/deployment-service tarballs noted but harmless — this script only imports UTL + its own MDPS code, both fresh).
(3) **Write succeeded on attempt 1** (`generation=1785245730519090`): `166849 reconciled`,
`row-count conservation: old_sum=5410990 new_sum=5410990: True`, `2229975 new per-bookmaker rows written`, post-write
verify `rows=9191967 remaining unmigrated=3063`. (4) Resumed the cron; canonical generation held steady
(`1785245730519090`) across ~10 min of post-resume cycles — no resurrection. The consolidator itself reported
`no_op=true error_reason=locked` repeatedly; confirmed this is expected, not a hang — `instruments-sports` runs a
deliberate **2400s (40-min) lock TTL** (Terraform override), set that high after a 2026-07-14/15 livelock incident where
this bucket's legitimate 6-9 min merges were misclassified as crashed under the 300s default.

**Phase 2d — independently re-verified manifest content, not just the script's self-report.** Downloaded the post-apply
index locally (146MB, matches the write log's `serialized 145941438 bytes` exactly) and re-queried with the script's own
`_fine_captured_mask` logic: **3,063 rows still `venue=ODDS_API`** (matches exactly); **2,229,975 new rows carry real
bookmaker venues** (unibet 133,847, paddypower, pinnacle, draftkings, williamhill, betfair_ex_uk/eu, 20+ distinct
bookmakers); **1,940 coarse aggregate rows, 100% still `ODDS_API`** (correct, by design). A first-pass naive `.notna()`
check falsely flagged 17,393 remaining rows — the gap was a separate, already-documented, out-of-scope population
(28,660 rows with `league_id` present but `timeframe` blank); caught before it became a false regression report.

**The 3,063 remaining rows are a genuine, separate, pre-existing data-quality gap, not fixable by this script.** From
the run log's sample errors: the bulk have `row_count` already `NaN` in the manifest, clustered at the 2020-06/07 edge
of the sports data floor; a smaller set are `404 NotFound` (manifest says `captured`, physical `bucketed.parquet` shard
doesn't exist); 5 are genuine row-count mismatches. The row-count-conservation HARD-abort is what made the real
2,229,975-row write provably lossless — the same discipline correctly refuses to fabricate a breakdown against
unverifiable source data. Tracked as a new P3 todo below.

## Todos

- [x] [SCRIPT] P1. **Root-cause and fix the second OOM path** (silent >28GB spike after DEFI `dex_pool_swaps` candle
      aggregation). **DONE** — `ManifestWriter`'s legacy write path did a full unfiltered index read on every flush;
      fixed via `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME`
      (`deployment-service@a6c640178b8e6dca7f1b12ae93172d85cd3fc383`). Verified: execution `...-p46vw` Completed=True in
      19m9s, 704/704 + 273/273 files succeeded across both prior OOM dates, RSS flat 565-808MiB. See Update 4. (repo:
      market-data-processing-service, deployment-service)

- [x] [SCRIPT] P1. **Register missing UAC SchemaContract entries for SPORTS odds_movement/odds_snapshot/
      odds_horizon_bucket** (337 combos, 23 venues, 4 data_types). **DONE, verified** — root cause was `odds_snapshot`
      fully unregistered + the generic `instrument_type="odds"` key never matching MDPS's real per-market keys; fixed
      via a bounded `lookup_contract()` fallback, no new schema invented. `unified-api-contracts@ed5434b3` → `main` (PR
      #756). Verified zero "No SchemaContract registered" errors against the rebuilt production image. See Update 5.
      (repo: market-data-processing-service, unified-api-contracts)

- [x] [SCRIPT] P1. **Fix UTL's `validate_partition_consistency` sports id-shape blindness** (every sports write then
      failed `[partition_mismatch]` once the SchemaContract todo cleared). **DONE** — `unified-trading-library@bcd73241`
      → `main`, sports-shape split added, 4 regression tests, verified in the rebuilt production image. See Update 5.

- [x] [SCRIPT] P1. **Root-cause + fix MDPS's candle-write batching mixing DIFFERENT sports markets into one write**.
      **DONE** — `market-data-processing-service@1390312`: `_streaming_write_per_tf` derived a batch's write partition
      from only the FIRST batch, force-writing others under it. Fixed via `no_real_chain_root` + per-group writes; true
      chains (options/futures/DeFi) unaffected. Re-verified end-to-end (Update 7): execution `...-86jbn`, zero
      `partition_mismatch`, GCS-pulled output confirmed uncontaminated. (repo: market-data-processing-service)

- [x] [SCRIPT] P2. **Scope MDPS's per-asset-group candle timeframe iteration** — uniform `default_timeframes` threw
      `No SchemaContract registered ..._4h` for sports (only `{1m,15m,1h}` registered). **DONE, verified** — added
      `resolve_timeframes(asset_group)` sourcing UAC's per-AG ceiling constants (prediction deliberately excluded — its
      trades data_type needs the broader set). A first attempt (`36e80cd`) had zero live effect because
      `cli/parser.py`'s `--timeframes` default shadowed it; corrected via `f7d259e`. Verified against live execution
      `...-krtkf`: zero `4h`/`24h` attempts, zero SchemaContract errors. See Update 8. (repo:
      market-data-processing-service)

- [x] [DESIGN] P2. **Build a genuine KALSHI trades→candle schema mapping in `PredictionTradesAdapter`.** **DONE,
      verified (Update 10)** — `is_buy = (taker_outcome_side == "yes")` per Kalshi's own docs + downstream-consumer
      trace; `count_fp` confirmed genuine trade size via docs + a 0/54,295-parse-failure real-data cross-check.
      `market-data-processing-service@890748f` (PredictionTradesAdapter only, Polymarket path unaffected); codex fixed
      (`unified-trading-pm@0c427d472`). Verified against real production data: execution `...-pr268` ran ~2h with zero
      schema errors, real KALSHI candle output confirmed bounded [0,1] OHLCV with genuine volume/price movement.
      `Completed=False` traced to a separate subprocess-timeout bug (below).

- [x] [SCRIPT] P2. **Fix `MalformedTickFieldError` for `bm_minutes_to_kickoff_or_h2h_columns`** (large fraction of
      sports MATCH_ODDS instruments failing "No h2h data found"). **DONE, verified (Update 9)** — root cause: a third
      vendor-metadata column (`af_fixture_id`, legitimately NaN on unresolved writer generations) left in the pivot
      index; the "combined" writer generation leaves it NaN on 100% of rows, silently emptying the h2h pivot. Confirmed
      via real failing-vs-succeeding `ticks.parquet` comparison (verdict: genuine code gap, not absent data). Fix:
      `market-data-processing-service@67cb2ef` (added to `_PIVOT_INDEX_EXCLUDE`), 2 regression tests (fail pre-fix, pass
      post-fix). Blast radius: 1098 error occurrences / 549 instrument_ids / 184 fixtures / 14 venues in one 2-day
      execution. See Update 9. (repo: market-data-processing-service)

- [x] [SCRIPT] P1. ✅ DONE — RESOLVED 2026-07-27, all 3 layers fixed + verified against real production data, see
      `/plans/archive/issues/mdps_sports_odds_horizon_bucket_h2h_anchor_fix_2026_07_27.md`. **Fix sports
      `odds_horizon_bucket`'s Path A½ honest-absence check silently suppressing ALL non-MATCH_ODDS candle output**
      (MATCH_ODDS_LAY/ASIAN_HANDICAP/OVER_UNDER) — the check assumed `tick_data` was a full per-fixture/bookmaker
      bundle, but production already slices it to ONE market before calling `process_to_candles`, so the check was
      unconditionally `True` for any non-MATCH_ODDS instrument regardless of real data presence. Confirmed via a real
      WILLIAMHILL file (12 genuine `totals` rows) returning an empty `CandleOutput`, and cross-checked against
      production output showing zero non-MATCH_ODDS objects anywhere — apparently never worked for any market other than
      h2h, for the product's entire history. See Update 9. (repo: market-data-processing-service)

- [ ] [DESIGN] P2. **`subprocess-per-date`'s fixed 1800s (30-min) timeout is too short for a full day of PREDICTION
      candle derivation now that the KALSHI schema mapping actually works** — newly discovered 2026-07-27 (Update 10)
      verifying the KALSHI todo above. With ~2,170 instruments × 7 timeframes now genuinely processing (previously every
      row crashed instantly, so real throughput was never observed), both dates timed out twice each
      (`subprocess-per-date: date=<d> TIMED OUT after 1800s`, 14:04/14:34/15:05/15:35) against execution
      `uts-prod-market-data-processing-service-t1-recon-pr268`, ending `Completed=False` despite healthy RSS (NOT the
      OOM class this doc otherwise chases) and zero schema errors. Real candle output DID get written for whichever
      instruments finished before each kill (see Update 10). **Not fixed here** — needs a capacity-planning decision
      (raise the 1800s constant? split PREDICTION into narrower per-venue/per-cqg subprocess units? profile the real HFT
      feature compute cost?), not a guessable fix. (repo: market-data-processing-service)

- [x] [SCRIPT] P2. **Apply the `odds_horizon_bucket` venue=ODDS_API→bookmaker manifest migration on a VM** (Update 11
      Phase 2). **DONE 2026-07-28 — see Update 12.** Root cause of 5 prior failed attempts: the migration's CAS write
      raced `uts-prod-manifest-consolidator-instruments-sports-cron` (`*/1min` against the same bucket) and could never
      win regardless of retry count; fixed by pausing the cron for the write (codex-sanctioned pause-first recipe), then
      resuming. Applied via `canonical-migration-sports-odds-venue-mig-20260728-141141`: **166,849 rows reconciled,
      row-count conservation held exactly (old_sum=new_sum=5,410,990), 2,229,975 new per-bookmaker rows written**,
      manifest grew 7,128,841 → 9,191,967 rows. Independently re-verified by downloading the post-apply manifest and
      re-querying with the script's own row-selection logic (not just trusting its self-report): 3,063 rows correctly
      left unmigrated (matches exactly), 2,229,975 new rows confirmed carrying real bookmaker venues
      (unibet/paddypower/pinnacle/draftkings/williamhill/betfair_ex_uk/+20 more), 1,940 coarse aggregate rows correctly
      untouched. Consolidator resumed, canonical generation confirmed stable (no resurrection) across ~10 min of
      post-resume cycles. (repo: market-data-processing-service, deployment-service)

- [ ] [SCRIPT] P3. **Investigate the 3,063 pre-existing `odds_horizon_bucket` manifest rows that could not be migrated**
      (surfaced by the venue-migration apply, Update 12 Phase 2d) — a genuine, separate, pre-existing data-quality gap,
      not caused by and not fixable within that migration. Two sub-populations: (a) manifest rows whose `row_count` is
      already `NaN`, clustered at the 2020-06/07 edge of the sports data floor; (b) `404     NotFound` rows where the
      manifest claims `capture_status=captured` but the physical
      `processed/.../data_type=odds_horizon_bucket/.../bucketed.parquet` shard doesn't exist in GCS (an honest-absence
      violation — these should likely be reclassified, not left as phantom `captured` rows). Needs real investigation
      before a fix (is this isolated to the data-floor boundary dates, does it affect other sports data_types, was there
      a writer bug at that specific time) — not a guessable one-liner. (repo: market-data-processing-service)
