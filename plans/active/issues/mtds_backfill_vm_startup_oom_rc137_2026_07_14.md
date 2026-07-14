---
doc_type: issue
title:
  MTDS backfill VMs crash rc=137 (SIGKILL) within seconds of handler init — 100% reproducible, likely all-asset-group
  catalog load
summary:
  "Relaunching mtds-perp-funding-backfill and mtds-dex-swaps-backfill per BLK-5b8c2938's operator ruling (Option A) both
  crashed with rc=137 within ~1-2 min of starting, before any per-venue data collection began. The already-running
  mtds-dex-pools-backfill VM crashed identically, including on a re-relaunch scoped to a single day/single protocol
  (2026-07-01→02, uniswap_v2 only) — ruling out backfill date-range size as the cause. Crash site is consistently right
  after '<Handler> initialized' logs, before any per-venue processing output. Top suspect:
  _register_all_catalog_readers() (market_tick_data_service/engine/orchestrator/__init__.py:684, called from
  process_ticks()) loads ALL FOUR asset groups' full instrument catalogues (cefi+defi+tradfi+sports, ~1.6M rows combined
  per commit f8cab3f0's own message) into memory once per process, regardless of which asset_group the job actually
  targets — a DeFi-only 1-day job still pays the full combined-catalogue cost. If this combined footprint has grown past
  what e2-standard-4 (16GB) can hold, EVERY MTDS backfill VM across every asset_group is now at OOM risk, not just DeFi.
  This blocks mvp_backfill_defi_onchain_v10-002's G2 gate and may be silently killing other in-flight backfill VMs
  fleet-wide."
status: open
nature: record
asset_group: [defi, cefi, tradfi, sports]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [oom, backfill-vm, mtds, rc137, defi, catalog-reader, infra]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/issues/cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md,
  ]
created: 2026-07-14
assigned_vm: planning
source: [mvp_backfill_defi_onchain_v10-002]
parent_epic: defi_master
priority: P0
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

Per `BLK-5b8c2938`'s operator ruling (Option A: relaunch both stopped G1 VMs from checkpoint), I relaunched
`mtds-perp-funding-backfill` (deleted the stale-metadata TERMINATED instance, fresh launch `2023-11-01→2026-07-14`) and
found `mtds-dex-swaps-backfill` already relaunched by another process (`2023-01-01→2026-07-14`). T+10min verification
(both `gcloud compute instances list` + full `run.log` fetch) showed **both crashed within ~1-2 minutes of starting**:

- `mtds-perp-funding-backfill`: preflight completed ("PerpFundingHandler preflight complete"), ONE `RESOURCE_SAMPLE`
  logged (`mem=10.8% rss=703MiB` — not high), then `Killed` (bash-reported SIGKILL), `command exited rc=137`,
  `DEPLOYMENT_FAILED exit_code=137`, self-deleted.
- `mtds-dex-swaps-backfill`: same pattern — "DEX swaps handler initialized", ONE `RESOURCE_SAMPLE`
  (`mem=9.9% rss=625MiB`), `Killed`, `rc=137`, self-deleted.
- `mtds-dex-pools-backfill` (already running from G1.6, unrelated to my relaunch): checked opportunistically, found the
  SAME crash pattern on its CURRENT incarnation. Watched it self-relaunch (auto-retry, not by me) a THIRD time scoped to
  a trivial job (`--start-date 2026-07-01 --end-date 2026-07-02 --dex-pools-protocols uniswap_v2` — one day, one
  protocol) — it crashed identically, with **no RESOURCE_SAMPLE at all** this time (killed even faster), confirming this
  is **not** proportional to backfill date-range/protocol-list size.

No `compute.instances.preempted` operation appears in `gcloud compute operations list` for any of the three VMs (only
explicit `insert`/`delete` ops from launches and self-deletes) — this rules out SPOT preemption as the cause. The kill
is `SIGKILL` (rc=137) with **zero application-level error output** — bash reports `Killed` directly, consistent with an
OOM-kill (or an external `kill -9`), not an unhandled Python exception (which would have logged a traceback).

**Root-cause candidate** (not yet confirmed by a live repro — VMs self-delete before I can attach): all three crashes
happen right after the handler's `preflight()` log line and before any per-venue processing output. The next thing that
runs in that exact window is `_register_all_catalog_readers(_config)`
(`market_tick_data_service/engine/orchestrator/__init__.py:684`, called once per process from `process_ticks()`). Per
its own most recent commit (`f8cab3f0`, 2026-07-12, "register catalog readers once per process, not once per date"),
this function registers **all four** asset-group catalog readers — `CeFiCatalogReader`, `DefiCatalogReader`,
`TradFiCatalogReader`, `SportsCatalogReader` — **regardless of which `asset_group` the job actually targets**, each
downloading + parsing its own full instruments catalogue from GCS (`f8cab3f0`'s message: "the combined ~1.6M-row
instruments catalogue"). `f8cab3f0` fixed a _per-date_ re-registration OOM (confirmed trigger for a 2024 DERIBIT-COMBO
VM, RSS→84% of 15GB) by adding a per-process guard — but the guard only stops REPEATED registration; the underlying
**per-process baseline cost of loading all four catalogues once** is unchanged, and unconditional regardless of
asset_group scope. If that combined footprint has grown since `f8cab3f0` landed (2 days ago) to where it doesn't fit in
an `e2-standard-4` (16 GB), every DeFi-only (or any single-asset-group) backfill VM now pays the full four-catalogue
cost and can OOM before touching its own asset_group's data — exactly the symptom observed (crash before ANY per-venue
output, 100% reproducible, insensitive to date-range size).

I did not confirm this diagnosis with a live memory profile (VMs self-delete on failure before SSH access is useful, and
reproducing locally needs the same GCS catalogues + memory ceiling) — flagging as the top suspect with the exact call
site, not a verified fix.

## Why it matters

- Blocks `mvp_backfill_defi_onchain_v10-002` (this plan's G2 final-verification gate) — the operator's chosen unblock
  path (Option A: relaunch) does not currently work; every relaunch attempt (3 so far, across 3 different DeFi handlers)
  crashes before collecting any data.
- If the root-cause candidate is correct, this is **not DeFi-specific** — `_register_all_catalog_readers()` runs for
  every MTDS handler via `process_ticks()`, so any CEFI/TRADFI/SPORTS backfill VM launched since `f8cab3f0` (2026-07-12)
  is at the same OOM risk. This could be silently killing other in-flight fleet VMs right now (each shows
  `DEPLOYMENT_FAILED rc=137` in its own deployment registry entry — worth a fleet-wide grep before assuming this is
  contained to DeFi). DEFI on-chain backfill is called out in this plan's Budget posture as "cheap" — 3 wasted SPOT
  VM-minutes each is not itself expensive, but the false-progress risk (operator ruling executed, appears actioned,
  actually produces zero data every time) is the real cost.

## Recommended decision

1. **Confirm the diagnosis** — a fix-worker (backend_engineer or data_engineering craft) should either reproduce locally
   with memory profiling around `_register_all_catalog_readers()`, or add a one-line RSS log immediately before/after
   that call on a disposable VM to confirm it's the spike site.
2. **If confirmed**, the fix is almost certainly to make catalog-reader registration **scoped to the `asset_groups`
   actually requested** by the job (mirrors the existing `asset_group` filtering everywhere else in this codepath)
   instead of unconditionally registering all four — this both fixes the OOM and removes wasted GCS egress/parse cost
   for every single-asset-group backfill VM.
3. **Do not blindly re-relaunch** `mtds-perp-funding-backfill` / `mtds-dex-swaps-backfill` again until this is fixed —
   it will reproduce the identical crash (confirmed 100% reproducible, 3/3 attempts, including a trivial
   1-day/1-protocol job) and burn SPOT VM-minutes for zero data.
4. Once fixed, resume `mvp_backfill_defi_onchain_v10_2026_06_27.md` G1/G2 per the existing plan — no scope change needed
   beyond this bugfix landing first.

## Todos

- [x] [BACKEND] P0. Confirm/refute `_register_all_catalog_readers()` (market-tick-data-service
      `engine/orchestrator/__init__.py:684`) as the OOM site for the rc=137 backfill-VM crash — add RSS instrumentation
      immediately around the call, launch one disposable VM (e.g. re-run
      `launch-mtds-perp-funding-backfill-vm.sh --start 2026-07-13 --end 2026-07-14`, smallest possible window), capture
      the memory delta. Repo: `market-tick-data-service`. — ✅ DONE 2026-07-14 (slot 2), see "P0 confirm + fix" below —
      REFINED not refuted: registration itself is cheap, the real cost is the first `list_instruments()` call per group.
- [x] [BACKEND] P0. If confirmed: scope catalog-reader registration to the job's actual `asset_groups` (not
      unconditionally all four) in `_register_all_catalog_readers()` / its `process_ticks()` call site. Add a regression
      test asserting only the requested asset_group's reader(s) register. Repo: `market-tick-data-service`. — ✅ DONE
      2026-07-14 — shipped by slot 11 as `market-tick-data-service@d6846f1c` (slot 2 independently implemented the
      identical fix in parallel — same diagnosis, same extraction pattern — reconciled by rebasing slot 2's commits out
      in favor of slot 11's, which landed first; see "P0 confirm + fix" below).
- [x] [SCRIPT] P1. Fleet-wide check: grep the deployment registry archive
      (`gs://deployment-scripts-central-element-323112/deployments/archive/2026-07-1{2,3,4}/*.json`) for `exit_code=137`
      `DEPLOYMENT_FAILED` entries across ALL asset_groups (not just DeFi) to gauge blast radius since `f8cab3f0` landed
      (2026-07-12). Repo: `deployment-service`. — ✅ DONE 2026-07-14, see "Fleet-wide blast-radius check" below.
- [x] [SCRIPT] P2. Once the fix lands, relaunch `mtds-perp-funding-backfill` (same command as this session used) and
      verify past the first `RESOURCE_SAMPLE` without a crash before resuming `mvp_backfill_defi_onchain_v10-002`'s G2
      verification. Repo: `deployment-service`. — ✅ DONE 2026-07-14 (slot 11, data_engineering): relaunched with the
      confirmed-fresh `mtds-code.manifest.json` @ `ecd3a4d4` (d6846f1c ancestor-verified); VM survived past the crash
      point and is genuinely capturing
      (`Perp funding collection complete for 2024-04-03: 2 records across 3     protocols`, per-VM manifest shard writes
      flowing) — **perp-funding side of this todo is resolved.** **`mtds-dex-swaps-backfill` split OUT to its own todo
      below — it crashed again, same `rc=137`, on the SAME fresh fix.**
- [x] [SCRIPT] P0. **NEW FINDING (2026-07-14, slot 11, data_engineering) — `mtds-dex-swaps-backfill` crashes rc=137 with
      a DIFFERENT root cause than the one this issue fixed.** Relaunched with the identical fresh, verified-current
      tarball (`mtds-code.manifest.json` @ `ecd3a4d4`, `d6846f1c` confirmed ancestor) that let
      `mtds-perp-funding-backfill` survive — `mtds-dex-swaps-backfill` still died `rc=137` (SIGKILL), self-deleted, in
      under 25s from process start: `TheGraph key pool loaded` → `DEX swaps handler initialized` → one `RESOURCE_SAMPLE`
      at `rss=666MiB mem=10.3%` (nowhere near an 85%-threshold OOM) → `Killed` → `rc=137`. Since
      `mtds-perp-funding-backfill` used the exact same tarball and survived, **this is NOT the
      `_register_all_catalog_readers()` defect this issue closed** — it is a separate memory spike specific to
      `DexSwapsHandler` (`market_tick_data_service/cli/handlers/dex_swaps_handler.py`, 900 lines, a single monolithic
      `process()` method) that happens BETWEEN `RESOURCE_SAMPLE` ticks (same "spike invisible to the coarse sampler"
      pattern this issue already flagged for the `opt-deribit-combo-2024` outlier). Quick code read (not a full
      RSS-instrumented repro — out of this task's craft-scoped verification brief, filing for a dedicated fix-worker
      instead): `catalogue_pool_ids_for_shard`/`catalogue_filter_ids_and_symbols`
      (`market_tick_data_service/cli/handlers/_catalogue_filter.py`) cache a single DeFi-only `prod/catalog.parquet` —
      much smaller than the 4-asset-group combined catalogue the original fix targeted, so likely NOT the culprit
      either. ~~Leading hypothesis: the handler's single `process()` method building an eager in-memory structure across
      the full 2023-01-01→2026-07-14 (~3.5yr) × 9-protocol swaps range before any GCS flush~~ — **REFUTED, see "P0
      confirm — dex_swaps NEW FINDING closed" below, real cause was elsewhere (`ManifestFreshnessCache`, shared by every
      DeFi handler, not `DexSwapsHandler`-specific).** — ✅ DONE 2026-07-14 (slot 9, data_engineering): root cause
      confirmed + already fixed by `unified-trading-library@0fc088a9` (landed independently the same day, citing this
      exact issue slug) — see below for the RSS evidence and the residual VM-relaunch-verify gap (filed as a new [INFRA]
      todo, out of data_engineering craft scope). Repo: `market-tick-data-service` (diagnosis) /
      `unified-trading-library` (fix, already shipped).
- [ ] [INFRA] P1. **Residual verification gap (2026-07-14, slot 9, data_engineering)**: relaunch
      `mtds-dex-swaps-backfill` one more time with BOTH the `mtds-code` tarball (≥ `d6846f1c`) AND the
      `unified-trading-library-code` tarball (≥ `0fc088a9`) freshly rebuilt via
      `deployment-service/scripts/vm/create-code-tarballs.sh` for `unified-trading-library` (its own tarball is separate
      from `mtds-code.tar.gz` — easy to forget rebuilding when only the MTDS-side SHA was verified fresh, which is the
      likely reason the prior relaunch above still crashed on an otherwise-fresh MTDS tarball), then verify past the
      first `RESOURCE_SAMPLE` without a crash (same T+10min recipe used for `mtds-perp-funding-backfill`'s todo above)
      before resuming `mvp_backfill_defi_onchain_v10-002`'s G2 verification. **Not doable by this data_engineering
      session**: VM launches are out of this craft's scope (`does_not: infra/VM launches → infra`), and this worker
      sandbox's `gcloud` CLI is non-functional (`snap-confine` capability error, `cap_dac_override` missing) — confirmed
      via `gcloud auth list` failing identically to `gcloud compute instances list`, so launch/verify must happen from a
      session with working `gcloud` (e.g. the operator/planning VM). Repo: `deployment-service`.

## P0 confirm — dex_swaps NEW FINDING closed (2026-07-14, slot 9, data_engineering)

**Root cause was NOT `DexSwapsHandler`-specific** — it is `ManifestFreshnessCache._refresh_locked()`
(`unified-trading-library` `manifest_freshness.py`), called by `dex_swaps_handler.py:179-180`
(`freshness_cache = ManifestFreshnessCache(bucket=bucket, ttl_seconds=60)` →
`await asyncio.to_thread(freshness_cache.bulk_load)`) right at the top of every single date's `process()`, BEFORE any
per-venue collection. Confirmed the SAME shared DeFi bucket (`market-data-tick-defi-prd-central-element-323112`) is used
by `dex_swaps_handler.py` (`resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi")`) and
`perp_funding_handler.py` (`get_write_bucket_name("market_data", "defi")`) — same physical bucket, both handlers pay
this same cost; it is a fleet-wide DeFi-handler hazard, not one handler's bug.

**RSS-instrumented repro** (local, `market-tick-data-service` `.venv`, real prod GCS data via ADC — no VM needed, same
technique as the "P0 confirm + fix" section above): downloaded the REAL current consolidated
`_index/availability_index.parquet` for that bucket (445,220,744 bytes on disk, 27,445,013 rows) and parsed it two ways:

| Read                             | Peak RSS      |
| -------------------------------- | ------------- |
| baseline (process just started)  | 515 MiB       |
| after raw parquet bytes download | 946 MiB       |
| **SLIM** (7 row-key/status cols) | **5.30 GiB**  |
| **FULL** (all 41 columns)        | **19.72 GiB** |

An `e2-standard-4` backfill VM has 16 GiB total — the FULL-schema read alone (19.72 GiB) **guarantees** an OOM-kill
before a single byte of per-venue swap data is even fetched, independent of date-range size or protocol count (matches
every observed symptom: crash right after handler-init, before per-venue output, "no RESOURCE_SAMPLE at all" on fast
paths, insensitive to backfill window). The SLIM read (5.30 GiB) leaves a ~10 GiB margin for TheGraph HTTP payloads +
pandas working set — comfortably under the OOM line, consistent with the healthy `RESOURCE_SAMPLE` readings (9-11%
`mem_pct`) logged for both handlers before this bug's crashes.

**Fix already shipped independently** — `unified-trading-library@0fc088a9` ("fix(manifest): ManifestFreshnessCache uses
slim column-pruned read_availability_index, not the ~6.5GB full-schema path", landed 2026-07-14T12:56:50Z, same-day as
this issue, citing `mtds_backfill_vm_startup_oom_rc137_2026_07_14` by name in its own code comment). It changes
`_refresh_locked()` to call
`read_availability_index(self.bucket, columns=[*_ROW_KEY_COLUMNS, "capture_status", "error_reason"])` instead of the
unqualified full-schema call — exactly the SLIM path measured above. No code change needed from this session; this
section is the confirmation + quantification the "Recommended decision" item 1 above asked for, using the REAL current
27.4M-row index (bigger than the ~6.5GB/sports figure that motivated the original comment — worth noting DeFi's own
index has grown to a similarly dangerous size).

**What's NOT yet done**: the fix landing in `unified-trading-library` doesn't by itself prove a freshly-packaged
`mtds-dex-swaps-backfill` VM survives — that needs an actual relaunch with BOTH tarballs rebuilt post-fix (see the new
`[INFRA]` todo above). Flagging as the residual gap rather than closing this out as fully verified.

## P0 confirm + fix (2026-07-14, slot 2)

**RSS-instrumented repro** (local, market-tick-data-service `.venv`, real prod GCS catalogues via ADC, not a disposable
VM — cheaper/faster and gave per-call RSS deltas a VM's coarse `RESOURCE_SAMPLE` log couldn't): registering all four
catalog readers (`sports`/`cefi`/`defi`/`tradfi`) is CHEAP — RSS stayed flat (504.5 MiB) across all four
`register_catalog_reader()` calls, confirming reader `__init__` never eagerly downloads (matches the
`tradfi_backfill_oom_remediation_2026_06_24` per-instance lazy-cache design). The real cost is the FIRST
`list_instruments()` call per group:

| asset_group | rows loaded | RSS delta                         |
| ----------- | ----------- | --------------------------------- |
| sports      | 0           | +3.7 MiB                          |
| cefi        | 358,455     | +304.9 MiB                        |
| defi        | 15,810      | −108.8 MiB (GC reclaim from cefi) |
| tradfi      | 1,170,558   | +566.5 MiB                        |

Combined catalogue is now **1,554,823 rows** (grown from the ~1.6M f8cab3f0 cited 2 days ago — consistent, not
contradictory). **Refined root cause**: `_register_all_catalog_readers()` itself was never the expensive call — the
expense is `_load_sentinel_catalogs()` (`engine/orchestrator/sentinel_catalogs.py`), called ONCE PER DATE from
`_emit_honest_coverage_sentinels()` → `_write_date_manifest()` (`manifest_finalize.py`, near the END of a date's
processing, AFTER per-venue fetching), which UNCONDITIONALLY calls `list_instruments("cefi"/"defi"/"tradfi", ...)`
regardless of the job's own `asset_groups` scope. A DeFi-only job was paying the full cefi (+305MiB) + tradfi (+567MiB)
cost — ~870MiB entirely wasted — every date. This also explains the "no per-venue output" crash pattern reported in
"What I found" above: per-venue fetch DID complete (feeding `_write_shard_counts_to_manifest`), the crash is in the
LATER honest-coverage-sentinel stage, and a trivial 1-day/1-protocol job reaches that stage fast enough to die before
the next periodic `RESOURCE_SAMPLE` fires (explains the "no RESOURCE_SAMPLE at all" 3rd-incarnation crash).

**Fix shipped** — `market-tick-data-service@d6846f1c` (slot 11, landed 2026-07-14T12:42:29Z). Slot 2 (this session)
independently reached the identical diagnosis and implementation in parallel (same root cause, same
`catalog_registration.py` extraction to respect the 900-line file-size gate, same per-asset_group `set` guard, same
`KeyError`-fallback reasoning) — both attempts converged on the same fix, which is itself a useful cross-validation
signal. Slot 2's commits (`42d4397f`, `5361af99`) conflicted with slot 11's on push (identical files, genuine content
conflict — not a false-positive), confirmed via full diff review that slot 11's version is complete and equivalent
(marginally cleaner: set-intersection over registered/requested groups vs. slot 2's `_needs()` closure, and imports UAC/
UTL directly into the new module rather than through the `_orch` package facade, avoiding slot 2's more fragile
circular-import pattern), so slot 2 reconciled via `git rebase --skip` on its own two now-redundant commits rather than
shipping a duplicate. No unique content from slot 2's implementation was lost — RSS-probe findings above are captured
here in the issue doc regardless of whose code shipped.

- `_register_all_catalog_readers(config, asset_groups)` now takes the job's `asset_groups` and only registers readers
  for groups in that list (or all four when `asset_groups` contains `"ALL"` — same convention as
  `get_venues_for_asset_groups`). Replaced the process-wide `_catalog_readers_registered: bool` guard with a
  per-asset_group `_registered_catalog_asset_groups: set[str]` so registration stays idempotent per (process,
  asset_group) across the multi-date loop.
- Leverages EXISTING graceful-degradation: an out-of-scope group's `list_instruments()` call now raises `KeyError` (no
  reader registered) — `_load_sentinel_catalogs()` and the sports Tier-2 sentinel fan-out already catch `KeyError` and
  fall back to UAC seed instruments / v1 sentinels. Zero new failure modes, just skips the download+parse for
  out-of-scope groups.
- Regression tests: `tests/unit/engine/test_catalog_reader_registration_once_per_process.py` — 4 tests pin (a)
  once-per-process idempotency (pre-existing invariant, preserved), (b) once-guard no-op, (c) a DeFi-only job registers
  ONLY `defi`, (d) incremental registration across separate calls with different `asset_groups`. Verified passing (slot
  2, post-reconciliation) + full `market-tick-data-service` `quality-gates.sh` green on `d6846f1c` (file-size gate clean
  at 871 lines).

**Cross-check against slot 3's fleet-wide data below**: this fix's mechanism (skip unconditional `list_instruments()`
for out-of-scope groups) is asset_group-agnostic — a CEFI-only job now skips the DEFI+TRADFI loads instead, so it should
address the 14 post-fix CEFI crashes equally, not just the 4 DEFI ones. The `opt-deribit-combo-2024` outlier
(mem_pct=82.5% at last sample, flagged below as possibly a distinct large-data-volume OOM) is NOT expected to be fixed
by this change if its cause is genuinely different (e.g. full-year options-chain data volume rather than the baseline
catalogue-registration cost) — re-open as a separate issue if it recurs after this fix ships.

## Fleet-wide blast-radius check (2026-07-14, slot 3)

Downloaded + parsed all **1958** deployment-registry archive JSON records for `2026-07-{12,13,14}`
(`gs://deployment-scripts-central-element-323112/deployments/archive/2026-07-1{2,3,4}/*.json` — bounded 3-day fetch, not
a corpus-wide walk). Note: the registry schema's field is `status: "failed"` + `exit_code: 137` (no literal
`DEPLOYMENT_FAILED` string appears in the registry JSON itself — that phrasing was a VM-log convention, not a registry
field. Grepped on the actual schema instead).

**Total `exit_code=137` records: 70** — split cleanly by whether they started before or after `f8cab3f0` landed
(**2026-07-12T23:52:29Z**, confirmed via `git log`):

| Window                                 | Count  | Asset groups          |
| -------------------------------------- | ------ | --------------------- |
| **PRE-fix** (before 23:52:29 on 07-12) | 52     | CEFI only             |
| **POST-fix** (at/after 23:52:29)       | **18** | **CEFI: 14, DEFI: 4** |

**PRE-fix 52 CEFI crashes** are almost certainly the OLD bug `f8cab3f0` targeted (per-date catalog re-registration on
multi-day backfills) — consistent with the commit message's own confirmed trigger case (2024 DERIBIT-COMBO OOM). Not
this issue's concern; already addressed.

**POST-fix 18 crashes are the ones relevant to this issue** — and they confirm the blast radius is **fleet-wide across
CEFI+DEFI, not DeFi-specific**: 14 of 18 (78%) are CEFI backfills (okx-swap, bitfinex-spot, bybit-spot, binance-futures,
bitget-futures ×7, deribit-2026-heavy), only 4 are the DEFI jobs already known from this issue's own repro session.
Spans 07-13 10:32 through 07-14 11:49 — still actively recurring, not a one-time blip.

One post-fix outlier, `opt-deribit-combo-2024` (07-13T00:36, 13 min after the fix landed) shows **mem_pct=82.5%** at its
last sample — high-memory-load pattern distinct from the other 17 post-fix crashes (all single-digit-to-teens mem_pct at
last sample, consistent with "OOM spike happens between samples" already noted in this doc's Evidence section). Flagging
as possibly a separate, genuine large-data-volume OOM (options backfill, full-year range) rather than the baseline
catalog-registration cost — worth excluding from the fix's regression scope unless a live repro says otherwise.

**TRADFI and SPORTS backfills DID run in this window** (226 and 552 registry entries respectively, including 28 TRADFI
and 31 SPORTS `failed` records) but **zero of their failures were `exit_code=137`** (TRADFI failures were all `rc=1`;
SPORTS split `rc=1`/`rc=2`). So observed impact in this window is CEFI+DEFI only — this does NOT rule out latent risk
for TRADFI/SPORTS (they may simply not have hit the crash-inducing code path), but there is no evidence of them being
hit so far.

**Bottom line for the BACKEND fix todos above**: the blast radius is bigger than "DeFi-only" — CEFI backfills are hit
MORE often (14 vs 4) than DeFi post-fix. The fix (scope catalog-reader registration to the job's actual `asset_groups`)
should be validated against BOTH a CEFI and a DEFI repro, not just DeFi, before this issue closes.

## Evidence

- `mtds-perp-funding-backfill` full `run.log` (crash at 2026-07-14T11:41Z): preflight complete → 1 RESOURCE_SAMPLE
  (mem=10.8%) → `Killed` → `rc=137`.
- `mtds-dex-swaps-backfill` full `run.log` (crash at 2026-07-14T11:38Z): handler initialized → 1 RESOURCE_SAMPLE
  (mem=9.9%) → `Killed` → `rc=137`.
- `mtds-dex-pools-backfill` 3rd incarnation `run.log` (crash at 2026-07-14T11:49Z, 1-day/1-protocol job): handler
  initialized → **no RESOURCE_SAMPLE** → `Killed` → `rc=137`.
- `gcloud compute operations list --filter="targetLink~mtds-{perp-funding,dex-swaps,dex-pools}-backfill"`: only
  `insert`/`delete` ops, no `preempted` — rules out SPOT preemption.
- `f8cab3f0` (2026-07-12, `market-tick-data-service`) — the most recent change to `_register_all_catalog_readers()`,
  confirms it loads a combined ~1.6M-row cross-asset-group catalogue once per process.
