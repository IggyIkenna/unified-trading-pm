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
last_updated: 2026-07-27 (Update 9)
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

## Update 6 (2026-07-27, interactive session) — KALSHI/prediction timestamp bug DEEPLY INVESTIGATED, NOT fixed: genuine multi-column schema mismatch, not a rename. Polymarket path proven to have worked historically; KALSHI path NEVER built

Per operator instruction ("P2 — KALSHI/prediction timestamp bug - needs more investigation for better todo") — this
update replaces the thin one-line P2 todo below with a fully-traced investigation. **No code changed this session** —
the fix requires a genuine product/data-semantics decision (see "Why this is NOT mechanical" below), which the operator
explicitly ruled out guessing at.

### Where the error is actually raised

`prediction: 0/2170 succeeded, 2170 errors` at every timeframe traces to
`BaseCandleAdapter._get_local_timestamp_column()`
(`market_data_processing_service/app/adapters/base_adapter.py:169-188`):

```python
def _get_local_timestamp_column(self, df: pd.DataFrame) -> str:
    # Priority: ts_init → local_timestamp → ts_event → timestamp
    ...
    else:
        raise ValueError("No timestamp column found in data")  # line 188
```

Called from `_convert_to_processing_dt` (same file, ~line 213) → called from `CefiTradesAdapter._prepare_tick_data`
(`app/adapters/cefi/trades_adapter.py:109-145`) — `PredictionTradesAdapter`
(`app/adapters/prediction/trades_adapter.py`) has NO override of `process_to_candles`'s tick-preparation step; it
delegates straight to `CefiTradesAdapter.process_to_candles` via `super()` (line 129) once past its own empty/Category-D
handling. So every prediction "trades" file goes through the CeFi base class's column-name assumptions unchanged.

### Real raw schema pulled directly from GCS (not assumed from the docstring)

Bucket `market-data-tick-pred-prd-central-element-323112` (resolved via
`resolve_bucket_name(kind="market-data-tick-prediction")` per `/codex/02-data/prediction-data-types-catalog.md`). Two
real files downloaded and inspected with `pyarrow`:

**KALSHI**
(`.../day=2026-07-25/pipeline_mode=batch_kalshi/asset_group=prediction/venue=KALSHI/instrument_type=prediction_market/data_type=trades/KALSHI:PREDICTION_MARKET:KXMLBGAME-26JUL242215LAASF-LAA.parquet`,
54,295 rows):

```
count_fp, created_time, is_block_trade, no_price_dollars, taker_book_side, taker_outcome_side,
taker_side, ticker, trade_id, yes_price_dollars, data_type, symbol, instrument_id, instrument_type,
canonical_question_group, available_at, underlying
```

**No column named `timestamp`, `ts_event`, `ts_init`, or `local_timestamp` exists anywhere in KALSHI's raw schema** —
hence the ValueError, unconditionally, on 100% of KALSHI shards. Also confirmed (same file):

- `created_time` (string ISO8601) == `available_at` (proper `timestamp[ns, tz=UTC]` column) **exactly, for all 54,295
  rows** (`(created_time - available_at).abs().max() == 0.0s`) — `available_at` is a genuine per-row-accurate stamp of
  the trade's real event time, not a coarse batch/fetch-time artifact (44,077 distinct values across the file, spread
  02:00:10-05:20:30 UTC — real intraday granularity).
- No column named `price`, `size`, `side`, or `amount` — instead: `yes_price_dollars` + `no_price_dollars` (sum to
  **exactly 1.00 for every row**, genuine complementary YES/NO probability pricing), `count_fp` (string-typed, cleanly
  float-parseable, presumably contract count), and THREE side-like columns — `taker_side`/`taker_outcome_side`
  (identical to each other: `yes`=42,340 / `no`=11,955) and `taker_book_side` (`bid`=42,340 / `ask`=11,955, perfectly
  correlated with the other two) — none of which is a `BUY`/`SELL` string the base adapter's `_resolve_price_size_cols`
  understands.

**POLYMARKET**
(`.../day=2026-07-22/pipeline_mode=batch_polymarket_clob/.../data_type=trades/POLYMARKET:PREDICTION_MARKET:0x3d5c...da0.parquet`):

```
side, asset, conditionId, amount, price, outcome, outcomeIndex, transactionHash, timestamp, condition_id,
data_type, symbol, instrument_id, instrument_type, data_source, chain, asset_group, underlying,
market_type, resolution_period, canonical_question_group, available_at
```

This DOES have `price` (double), `amount` (the base adapter's own `_resolve_price_size_cols` already falls back
`size→amount`, `app/adapters/cefi/trades_adapter.py:158-163`), `side` (`BUY`/`SELL` string, matches the adapter's
`.str.lower() == "buy"` check), and a proper `timestamp` column — i.e. **Polymarket's raw schema matches every
assumption `CefiTradesAdapter`/`PredictionTradesAdapter` makes, column-for-column.** The adapter's own docstring
("Polymarket raw parquet columns: price ..., timestamp (int64 unix seconds)") was written against exactly this shape.

### Regression vs. never-built — resolved via a bounded, targeted GCS probe (not a new whole-corpus walk)

- `gcloud storage ls` on `raw_tick_data/by_date/day={2026-07-20,22,24,25,26}/` shows `pipeline_mode=batch_kalshi`
  present on ALL five probed days, while `pipeline_mode=batch_polymarket_clob` is present only on 07-20 and 07-22 (NOT
  07-24/25/26 — the exact days this issue's OOM-recon runs touched). **On the days this bug was actually observed,
  Kalshi was the only venue with any data at all** — this is why the failure count was 0/2170 (100%), not a partial
  Polymarket-succeeds/Kalshi-fails split.
- `processed_candles/by_date/` (the candle OUTPUT path — confirmed via `config.py`'s
  `get_output_bucket_for_asset_group()` that candle writes default to the SAME bucket as the raw-tick source bucket, no
  override env var set for prediction) DOES contain real historical prediction candle output — but a bounded probe found
  the **last day with ANY prediction candle output is `day=2026-01-14`, and every object under it is
  `venue=POLYMARKET`**
  (`pipeline_mode=batch_polymarket_clob/timeframe=15m/data_type=trades/instrument_type=PREDICTION_MARKET/venue=POLYMARKET/...`).
  A parallel probe of `day=2026-07-22` (a day with real raw Polymarket data, confirmed above) found **zero**
  `processed_candles` output — `gcloud storage ls` returned "matched no objects." No `venue=KALSHI` object was found
  under `processed_candles/` on any probed day.
- Zero test coverage anywhere in the repo references Kalshi's actual column names (`yes_price_dollars`,
  `no_price_dollars`, `count_fp`, `taker_side`, `taker_book_side`, `taker_outcome_side`) — grepped
  `tests/unit/test_prediction_adapter_category_d.py` and the full `tests/` tree; zero hits. The adapter's full git
  history (`e197da8` "feat: read hive-partitioned tick data ... prediction adapter" through `792ae5e` "fix(prediction):
  3-segment instrument_keys") shows no commit ever touching Kalshi-shaped columns.
- Corroborating context: `/codex/02-data/prediction-schema-paths.md` documents a
  `[DELTA 2026-05-22 — KALSHI API MIGRATION]` with Kalshi integration verification `BLOCKED-CREDENTIALS` as of that date
  — consistent with real Kalshi trade data only starting to flow in this bucket some time after that (first observed
  here on 2026-07-20, the earliest of the 5 probed days).

**Conclusion: this is NOT a regression.** Polymarket's candle path is proven to have worked (real historical output
through 2026-01-14) and its raw schema still matches the adapter's assumptions today (confirmed on a fresh 2026-07-22
file). **KALSHI's candle path has never worked, because it was never built** — `PredictionTradesAdapter` was written and
tested exclusively against Polymarket's schema; Kalshi was added as a second venue at the MTDS/data layer with a
structurally different upstream API response shape (dual yes/no dollar-pricing vs. single price; string contract-count
vs. numeric size; three-way bid/ask/outcome side encoding vs. BUY/SELL; ISO-string `created_time`+`available_at` vs. a
`timestamp`/`ts_event` column) and the MDPS candle-adapter side was never updated to handle it. The "masked by whichever
bug was fatal earlier" framing in the original todo undersold this — even with the OOM and sports bugs both fixed, this
failure mode was never going to self-resolve; it needs a real design pass.

### SSOT-vs-code contradiction found along the way (flagging, not resolving — outside this todo's scope)

`/codex/02-data/prediction-data-types-catalog.md` (§ NEEDS_CANDLE_PROCESSING) states: _"`trades` has NEEDS_CANDLE=False
for the prediction asset_group — the UAC override for prediction means raw trades are not processed into OHLCV candles.
Only CeFi/TradFi `trades` have NEEDS_CANDLE=True."_ The **actual running code** contradicts this:
`unified_api_contracts/registry/market_data_categories.py:640` declares `NEEDS_CANDLE_PROCESSING: dict[str, bool]` as a
**flat, data_type-keyed dict with no asset_group axis at all** — `"trades": True` — and the adjacent inline comment
(line 697) reads _"Prediction — uses canonical 'trades' / 'book_snapshot_5' (same keys as CeFi)"_, i.e. the code's own
comment says prediction intentionally shares CeFi's `True` value. `orchestration_service.py:646`'s gate
(`if not needs_candle_processing(data_type): ... skip`) calls this with `data_type` only, never `asset_group` — so there
is no code path that could apply a prediction-specific override even if one were intended. Either the codex doc is stale
(describing an override that was never implemented, or was reverted) or the code is missing an intended
asset-group-scoped exception. Not resolved here — genuinely out of this todo's scope (this issue is about MDPS's
candle-derivation _result_, not about whether MDPS should attempt it at all for prediction), but whoever designs the
real Kalshi fix should resolve this contradiction first, since if the codex doc is actually right, the correct fix might
be "stop attempting candle derivation for prediction trades entirely" rather than "build a Kalshi adapter."

### Why this is NOT a mechanical rename (why no fix was implemented this session)

Fixing only the immediate `ValueError` (e.g. adding `available_at` to `_get_local_timestamp_column`'s priority list —
which the evidence above shows WOULD be timestamp-safe on its own) would not produce a working pipeline: the very next
step, `_resolve_price_size_cols`, would then fail on the missing `price` column (`_derive_price_column` only knows
DeFi's `amountUSD`/`amount0`/`amount1` swap-style fallbacks, none of which exist here either) — just trading one error
for another, `MalformedTickFieldError`, with nothing actually fixed. A real fix requires product-level decisions this
session is not positioned to make unilaterally:

1. **Which price series is "the" OHLCV price for a two-sided YES/NO market?** `yes_price_dollars` and `no_price_dollars`
   are complementary (sum to 1.00) — candling one, the other, or both as separate series is a product choice, not
   inferable from the data.
2. **What does `taker_side`/`taker_outcome_side`/`taker_book_side` map to for buy/sell-style features** (buy/sell volume
   split, VWAP direction, whale detection all assume `is_buy`)? Kalshi's bid/ask/yes/no encoding isn't a BUY/SELL string
   swap — it needs an actual mapping decision.
3. **Is `count_fp` genuinely the trade size (contract count)?** It parses cleanly as float, but its semantic meaning
   (vs. a notional-dollar quantity) hasn't been confirmed against Kalshi's API docs.
4. **Timestamp choice**: `available_at` is evidenced-safe (see above), but `_get_local_timestamp_column`'s existing
   4-column priority list is otherwise a genuine HFT local-vs-exchange-time convention (`ts_init`/`local_timestamp` =
   local receive time, `ts_event`/`timestamp` = exchange time, feeding the synthetic 200ms delay logic) — Kalshi has no
   analogous local/exchange split, so wiring in `available_at` needs a decision about whether/how the synthetic-delay
   step still makes sense for it.

Per the operator's explicit standard for this task ("if it turns out to need a genuine judgment call about data
semantics, stop at a well-documented todo instead of guessing"), no code was changed. See the replaced todo below.

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

- [x] [SCRIPT] P1. **Register the missing UAC SchemaContract entries for SPORTS odds_movement_15m / odds_snapshot_15m /
      odds_horizon_bucket** across the ~20 bookmaker venues enumerated in Update 4. **DONE, verified — but does NOT by
      itself unblock a clean end-to-end run; see Update 5's two follow-on todos below.** Full error list re-pulled: 337
      unique combos, 23 venues, 4 data_types (incl. previously-uncited `arbitrage_opportunity_15m`), 28
      instrument_types. Root cause was NOT a venue-registration gap (venue was never in the `CONTRACT_REGISTRY` key at
      all) — it was (a) `odds_snapshot` fully unregistered (omission) and (b) the registry's generic
      `instrument_type="odds"` key never matching MDPS's real per-market lookup key (`MATCH_ODDS`,
      `ASIAN_HANDICAP_0_25`, ... — continuously point-parameterised, genuinely unbounded, confirmed via
      `build_instrument_id`). Fixed both mechanically (no schema invented — reused the existing, already-correct,
      already-uniform-across-markets `CandleOutput` contract via a bounded `lookup_contract()` fallback + the missing
      registration loop entry). `unified-api-contracts@ed5434b3` → `main` via PR #756. Verified `zero` "No
      SchemaContract registered" errors for these 4 data_types at their documented `{1m,15m,1h}` timeframes across a
      full unscoped run AND a forced sports-scoped re-run, both against the rebuilt production Docker image (not just
      unit tests). See Update 5 for full investigation + the exact fallback design. (repo:
      market-data-processing-service, unified-api-contracts)

- [x] [SCRIPT] P1. **Fix UTL's `validate_partition_consistency` sports id-shape blindness** (surfaced immediately once
      the SchemaContract todo above cleared — every sports write then failed `[partition_mismatch]` because
      `_split_instrument_id()` read the sports id's SPORT token as "venue"). **DONE** —
      `unified-trading-library@bcd73241` → `main`, asset_group threaded from the already-present `partition_path` string
      (no new call-site parameter), sports-shape split added, 4 regression tests. Verified inside the rebuilt production
      image before re-wiring. See Update 5.

- [x] [SCRIPT] P1. **Root-cause + fix MDPS's own candle-write batching mixing DIFFERENT sports markets into one
      partition-scoped write**. **DONE** — `market-data-processing-service@1390312` (`live-defi-rollout`). Root cause:
      `_streaming_write_per_tf` (`app/core/live_workers_streaming.py`) accumulated EVERY batch for a timeframe into one
      list and derived the write partition's `instrument_type` from just the FIRST batch (`tf_candles[0]`), then
      force-wrote every other batch under that same partition — for sports' legacy-sentinel `ticks.parquet` bundles (no
      genuine `underlying=` chain root), one raw file legitimately holds rows for DIFFERENT markets (MATCH_ODDS vs
      MATCH_ODDS_LAY), so this force-write is exactly what the pre-write `[partition_mismatch]` validator was correctly
      rejecting. Traced further than Update 5 left off: the shared outer `instrument_id` for this code path gets
      "recovered" from whichever slice is processed FIRST when both `instrument_id` and `input_underlying` start empty
      (`_process_chain_bundle_streaming`'s sentinel-recovery block) — for a TRUE chain (options_chain/futures_chain/DeFi
      reserves) `input_underlying` is always genuinely set from the path, so this recovery never fires and every batch
      already shares one real instrument_type; for sports it fires and the recovered id is only ever representative of
      ONE group, not every group written under it.

      **Fix**: added `no_real_chain_root` (true only for the legacy-sentinel, no-underlying case) to
                                                          `_streaming_write_per_tf`; when true, batches are grouped by their OWN `instrument_id`'s inferred type
                                                          (`_infer_instrument_type`, reusing the existing UAC/MDPS helper — no new schema logic) and each group writes its
                                                          own file under its own representative id via a new `_streaming_write_one_group` helper (extracted from the
                                                          original per-tf write body, unchanged logic). A true chain is provably unaffected: `no_real_chain_root` is false,
                                                          so it takes the untouched single-group path, byte-for-byte identical to the pre-fix code.

                                                          **Regression test**: `tests/unit/test_streaming_write_group_by_type.py` — proves MATCH_ODDS + MATCH_ODDS_LAY
                                                          batches (in the observed crash order, MATCH_ODDS_LAY first) split into 2 groups each keyed by their own correct
                                                          id, while multiple same-market batches (different fixtures) stay combined into 1 group. `quality-gates.sh`
                                                          green (2224 passed, 86.95% coverage, 0 basedpyright errors in touched files).

                                                          **Re-verified end-to-end against real production data (Update 7, 2026-07-27)**: execution
                                                          `uts-prod-market-data-processing-service-t1-recon-86jbn` (the exact repro command below, against the fixed image
                                                          rebuilt on `main`@`eaf8127`), watched to a genuine `Completed=False`/`NonZeroExitCode` terminal state (failing for
                                                          two unrelated, already-triaged reasons, not the mixing bug — see Update 7). Zero `partition_mismatch`/
                                                          `instrument_type mismatch` occurrences anywhere in the run's logs, and two independent freshly-written
                                                          MATCH_ODDS/MATCH_ODDS_LAY output pairs for the same fixture (BETFAIR_EX_EU ALLSVENSKAN KALMAR-MJALLBY;
                                                          BETFAIR_EX_EU MLS COLUMBUS_CREW_SC-CINCINNATI) were pulled directly from GCS and confirmed uncontaminated
                                                          (`instrument_id.unique()` per file contains only that file's own market). See Update 7 for full evidence.

                                                          Repro command used for this verification pass:
                                                          `gcloud run jobs execute uts-prod-market-data-processing-service-t1-recon --update-env-vars=MDPS_ASSET_GROUP=SPORTS --args=--operation,process,--mode,batch,--start-date,2026-07-25,--end-date,2026-07-26,--force`.
                                                          (repo: market-data-processing-service)

- [x] [SCRIPT] P2. **Scope MDPS's per-asset-group candle timeframe iteration** — `config.py`'s `default_timeframes`
      (`["15s","1m","5m","15m","1h","4h","24h"]`) was applied uniformly to every asset_group; sports only has
      SchemaContracts for `{1m,15m,1h}` (`_candle_contracts.py`'s declared "Sports {1m, 15m, 1h}" by strategy need), so
      every run threw `No SchemaContract registered ..._4h` for all 4 sports-derived products. **DONE, verified** —
      operator confirmed the general per-asset-group approach ("should be per AG scoped properly"). Added
      `MarketDataProcessingServiceConfig.resolve_timeframes(asset_group)` (`config.py`), sourcing UAC's
      `MDPS_TIMEFRAMES_SPORTS`/`MDPS_TIMEFRAMES_TRADFI` constants as confirmed-safe per-asset-group ceilings (cefi/defi
      are no-ops; prediction deliberately excluded — its "trades" data_type needs the BROADER
      `MDPS_TIMEFRAMES_PREDICTION_TRADES` set, so scoping it down would regress KALSHI/POLYMARKET trades coverage).
      Wired into `orchestration_service.py::process_category()`. A first attempt (`36e80cd`) didn't actually take effect
      on the real production path — `cli/parser.py`'s `--timeframes` argparse argument had its own hardcoded non-None
      default, shadowing the new fallback; corrected (`f7d259e`) by defaulting `--timeframes` to `None`, the idiomatic
      "unset vs explicit override" argparse pattern. Verified against a live sports-scoped `t1-recon` execution
      (`uts-prod-market-data-processing-service-t1-recon-krtkf`): zero `4h`/`24h` candle aggregation attempts (13,007
      `POLARS AGGREGATED` lines, all `1h`), zero "No SchemaContract registered" errors anywhere,
      `odds_movement`/`odds_snapshot`/`arbitrage_opportunity` all 100% succeeded — the one remaining partial failure
      (`odds_horizon_bucket`) is the already-tracked, unrelated `MalformedTickFieldError` bug (see the P2 todo below).
      cefi/tradfi regression-checked via direct unit tests (`tests/unit/test_config.py::TestResolveTimeframes`) plus the
      identical, category-agnostic call-site mechanism already proven live for sports — a live cefi/tradfi run wasn't
      reachable cheaply through the real production entrypoint (see Update 8 for the full reasoning) and wasn't forced
      given the strength of the existing evidence. See Update 8 for full investigation, the two-shipped-commits story,
      and a documented residual gap in `LiveModeHandler` (out of scope, low risk, not fixed). (repo:
      market-data-processing-service)

- [ ] [DESIGN] P2. **Build a genuine KALSHI trades→candle schema mapping in `PredictionTradesAdapter` — NOT a rename, a
      real venue-schema design decision.** Deepened investigation in Update 6 (2026-07-27) supersedes the original
      one-line todo. Confirmed via real GCS files: KALSHI's raw `trades` schema
      (`count_fp, created_time, is_block_trade, no_price_dollars, taker_book_side, taker_outcome_side, taker_side,     ticker, trade_id, yes_price_dollars, ...`)
      shares almost no column names with what `CefiTradesAdapter`/`PredictionTradesAdapter`
      (`market_data_processing_service/app/adapters/prediction/trades_adapter.py`, inheriting from
      `app/adapters/cefi/trades_adapter.py`) expects (`price`/`size`or`amount`/`side`/one of
      `ts_init`|`local_timestamp`|`ts_event`|`timestamp` — the immediate crash site is
      `base_adapter.py:169-188 _get_local_timestamp_column`, `ValueError: No timestamp column found in data`).
      **Confirmed NOT a regression**: Polymarket's raw schema (`price`, `amount`, `side` ∈ {BUY,SELL}, `timestamp`) DOES
      match the adapter's assumptions (verified on a real 2026-07-22 file) and Polymarket candle output genuinely
      existed historically (real objects found under `processed_candles/by_date/day=2026-01-14/.../venue=POLYMARKET/` —
      the most recent day with ANY prediction candle output found in a bounded probe). **KALSHI's candle path has never
      worked — it was never built**: zero test coverage of Kalshi's real columns anywhere in the repo, zero git history
      touching them, and Kalshi raw ticks only start appearing in this bucket around 2026-07-20 (consistent with the
      `[DELTA 2026-05-22 — KALSHI API MIGRATION]` `BLOCKED-CREDENTIALS` banner in
      `/codex/02-data/prediction-schema-paths.md`).

      **Real open design decisions the next implementer must make** (see Update 6 for full detail + evidence):
                                                      (1) which of `yes_price_dollars`/`no_price_dollars` is the OHLCV price for a two-sided YES/NO market (they sum to
                                                      exactly 1.00 — confirmed on 54,295 real rows); (2) how `taker_side`/`taker_outcome_side`/`taker_book_side`
                                                      (yes/no/bid/ask, not BUY/SELL) map to the adapter's `is_buy` buy/sell-split and whale-detection features;
                                                      (3) whether `count_fp` (string-typed, cleanly float-parseable) is genuinely trade size/contract count;
                                                      (4) timestamp source — `available_at` is evidence-backed safe (confirmed byte-exact match against `created_time`
                                                      across all 54,295 rows of a real file, genuine per-trade granularity, 44,077 distinct values across one day) but
                                                      wiring it into `_get_local_timestamp_column`'s existing local-vs-exchange-time HFT-delay convention needs a
                                                      decision since Kalshi has no local/exchange timestamp split.

                                                      **Also flag before starting**: a genuine SSOT-vs-code contradiction — `/codex/02-data/prediction-data-types-catalog.md`
                                                      claims `NEEDS_CANDLE_PROCESSING["trades"]` has a prediction-specific `False` override, but the actual UAC
                                                      registry (`unified_api_contracts/registry/market_data_categories.py:640`, flat/non-asset-group-keyed) sets it
                                                      `True` for `trades` uniformly, with a comment explicitly stating prediction shares CeFi's `True` value. Resolve
                                                      this FIRST — if the codex doc's intent is correct, the right fix may be "stop attempting prediction candle
                                                      derivation entirely" rather than building a Kalshi adapter. (repo: market-data-processing-service,
                                                      unified-api-contracts if the NEEDS_CANDLE contradiction is resolved as a code fix)

- [x] [SCRIPT] P2. **Investigate + fix `MalformedTickFieldError` for `bm_minutes_to_kickoff_or_h2h_columns` — a large
      fraction of sports MATCH_ODDS instruments fail with "ticks present but downstream calc dropped all rows due to
      NaN/malformed field"**, tracing to "No h2h data found in MTDS raw data — cannot produce odds" during the MTDS
      long→wide pivot step. **DONE, verified (Update 9, 2026-07-27)** — root cause: a THIRD, previously-uncovered
      vendor-metadata column (`af_fixture_id`, a best-effort cross-vendor join key that is legitimately NaN whenever a
      writer generation never resolved it) was left in `pivot_mtds_to_wide()`'s `group_cols` pivot index; the "combined"
      (no `fixture_id=` path partition) writer generation leaves it NaN on 100% of rows, so `pivot_table`'s default
      NaN-index-drop behavior silently emptied the h2h pivot — same bug CLASS as the two already-fixed
      `instrument_type`/`data_source`/`available_at` incidents documented in this file's own `_PIVOT_INDEX_EXCLUDE`
      docstring, just a new column. Confirmed via a REAL failing-vs-succeeding raw `ticks.parquet` GCS comparison (not
      guessed) — h2h ticks were genuinely present and correct; this is verdict (b), a genuine code gap, not absent
      upstream data. **Fix**: `market-data-processing-service@67cb2ef` — added `af_fixture_id`/`af_fixture_match_status`
      to `_PIVOT_INDEX_EXCLUDE`. 2 new regression tests (one using the exact real 25-column production schema),
      confirmed to genuinely catch the regression (fail pre-fix via `git stash`, pass post-fix).
      `quality-gates.sh --no-fix` → ALL QUALITY GATES PASSED. Shipped via `quickmerge.sh --agent`, confirmed on
      `origin/live-defi-rollout` HEAD. Blast radius: 1098 error occurrences / 549 unique instrument_ids / 184 unique
      fixtures across 14 venues in one 2-day sports-scoped execution alone — every occurrence is `MATCH_ODDS` (see the
      new todo below for why ASIAN_HANDICAP/OVER_UNDER/MATCH_ODDS_LAY never appeared here — a separate, larger bug, not
      this one). See Update 9 for full evidence. (repo: market-data-processing-service)

- [ ] [SCRIPT] P1. **Fix sports `odds_horizon_bucket`'s Path A½ honest-absence check silently suppressing ALL
      non-MATCH_ODDS candle output (MATCH_ODDS_LAY/ASIAN_HANDICAP__/OVER_UNDER__), always, regardless of whether real
      market data exists.** Newly discovered 2026-07-27 (Update 9) while investigating the `af_fixture_id` bug above — a
      SEPARATE root cause/code path, not fixed there. `process_to_candles`'s Path A½ check
      (`tick_data["market_key"] == "h2h"`) was written assuming `tick_data` is a full per-fixture/bookmaker bundle
      (correctly distinguishing "bookmaker doesn't offer h2h" from a schema defect), but the actual production call path
      (`_iter_chain_symbol_dfs` grouping by `instrument_id`) already slices `tick_data` to ONE market before
      `process_to_candles` is ever called — so for any non-MATCH_ODDS instrument the check is unconditionally `True`,
      REGARDLESS of whether that instrument's own market data is genuinely present. Confirmed with a real WILLIAMHILL
      file (12 genuine `market_key="totals"` rows for an `OVER_UNDER_2_5::OVER` instrument) returning an EMPTY
      `CandleOutput` instead of real odds, and cross-checked against real production output:
      `processed_candles/.../data_type=odds_horizon_bucket/` for day=2026-07-25 contains ONLY
      `instrument_type=MATCH_ODDS/` objects — zero `MATCH_ODDS_LAY`/`ASIAN_HANDICAP_*`/`OVER_UNDER_*` output anywhere,
      despite `pivot_mtds_to_wide()`/`_pivot_market()` explicitly implementing spreads/totals/btts pivoting and Update
      5's UAC SchemaContract fallback deliberately supporting all these `instrument_type`s. **Apparently never worked
      for any market other than plain h2h, for the product's entire history.** Not fixed this session — needs real
      judgment (does the fix generalize the check to "any recognized market_key present", could `btts` ever legitimately
      co-occur with another market in one slice, is there a call path where `tick_data` is genuinely NOT yet
      market-filtered) before guessing, same standard as the KALSHI investigation (Update 6). Flagged per
      data-pipeline-correctness-is-the-heartbeat — this silently drops real market data across most of the sports
      odds_horizon_bucket product. See Update 9 for full evidence. (repo: market-data-processing-service)
