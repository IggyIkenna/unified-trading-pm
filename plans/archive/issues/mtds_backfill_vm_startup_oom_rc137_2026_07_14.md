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
    plans/active/issues/mtds_defi_dex_backfill_vm_immediate_sigkill_2026_07_14.md,
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
- [x] [INFRA] P1. **Residual verification gap (2026-07-14, slot 9, data_engineering)**: relaunch
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
      session with working `gcloud` (e.g. the operator/planning VM). Repo: `deployment-service`. — ✅ DONE 2026-07-14
      (slot 2, infra): the local `gcloud`/`gsutil` (snap) ARE broken in this sandbox too (same `cap_dac_override`
      error), but a working NON-snap install at `~/google-cloud-sdk/bin/gcloud` exists and is already in documented use
      by other slots (see this plan's Progress Log) — used that (PATH-prepended) instead of escalating. Rebuilt fresh
      core tarballs (`create-code-tarballs.sh`, no `--asset-group` = UAC+UTL+MTDS+ deployment-service):
      `mtds-code @ ecd3a4d4366f` (descendant of required `d6846f1c`, confirmed via `git merge-base --is-ancestor`),
      `unified-trading-library-code @ 9bc06261292d` (descendant of required `0fc088a9`). Relaunched
      `mtds-dex-swaps-backfill` (`launch-mtds-dex-swaps-backfill-vm.sh`, defaults — `2023-01-01→2026-07-14`); the
      launcher's own `lc_verify_tarball_freshness` confirmed all 4 core tarballs current at launch time. **Verification
      task was performed as specified — but the outcome is a FAILED verification, not a pass: the VM crashed AGAIN,
      identically, even with both confirmed fixes present.** See "P0 residual — dex_swaps STILL crashes on both
      confirmed fixes" below; **this reopens the diagnosis, it does not close it.** New [BACKEND] P0 todo filed below
      for a fix-worker; escalating to operator given this contradicts the prior "fix already shipped, no code change
      needed" closure claim.

- [x] [BACKEND] P0. **NEW FINDING (2026-07-14, slot 2, infra)** — `mtds-dex-swaps-backfill` STILL crashes `rc=137`
      identically even with BOTH confirmed fixes present (`market-tick-data-service@d6846f1c`+ AND
      `unified-trading-library@0fc088a9`+, tarball-freshness-verified at launch time, not just git-ancestor-checked).
      This means the `ManifestFreshnessCache` slim-read fix that this issue's "P0 confirm — dex_swaps NEW FINDING
      closed" section credited with resolving the crash does **not** actually fix it — the crash symptom is
      byte-identical to every prior attempt (handler-init log → ONE `RESOURCE_SAMPLE` at low mem_pct → `Killed` →
      `rc=137`, dead within ~20s of process start, self-deleted before SSH is useful). Needs: (a) a live/attached repro
      — e.g. relaunch with `VM_SHUTDOWN_ON_COMPLETION=false` so the box survives its own crash for `ps`/`dmesg`
      inspection, since the RESOURCE_SAMPLE sampler (5s interval) keeps missing whatever spikes between samples (a
      pattern this issue already flagged twice); or (b) a local RSS-instrumented repro of `dex_swaps_handler.py`'s full
      `process()` path (not just `ManifestFreshnessCache.bulk_load`, which the local repro in "P0 confirm — dex_swaps
      NEW FINDING closed" measured in isolation, not as part of the actual handler invocation) using real prod GCS data,
      same technique as this issue's other RSS-instrumented repros. Repo: `market-tick-data-service` (+
      `unified-trading-library` if the real culprit is elsewhere in a shared cache/reader). See "P0 residual" below for
      the full run.log evidence. — ✅ DONE 2026-07-14 (slot 2, backend_engineer) — **not fully closed, substantially
      advanced**: (1) traced the crash timing precisely — it lands during/right after `freshness_cache.bulk_load()` (the
      very first statement in `process()`), strictly BEFORE any per-venue GraphQL work or manifest-write call, which
      RULES OUT the legacy unqualified `ManifestWriter._read_with_generation()` full-schema read
      (`unified-trading-library` `manifest_writer/_writer_io.py:798`, a separate real hazard flagged but not reachable
      this early); (2) shipped `market-tick-data-service@bc84b3e5` — `rss_probe_span()` entry/exit peak-RSS log brackets
      around `freshness_cache.bulk_load()` and each per-shard `_collect_one_shard()` call in `dex_swaps_handler.py`'s
      `process()` path (option (b) from this todo, done as static+live-repro tracing rather than a full handler
      instantiation — see "P0 full-path RSS trace" below for why); (3) **found and live-confirmed a NEW, concrete,
      currently-active infra condition**: the DeFi bucket's consolidated `availability_index.parquet` is **~4.8 hours
      stale** (17,241.9s > the 120s `MANIFEST_CONSOLIDATED_STALENESS_SEC` default) as of 2026-07-14T17:43Z — see "P0
      full-path RSS trace" below. This did NOT conclusively reproduce the silent SIGKILL locally (my repro hit the
      LOUD-FAIL `ManifestConsolidatorStaleError` path, not a silent OOM, since `MANIFEST_ALLOW_STALE_FALLBACK` is unset
      on every DeFi launcher) — so the exact kill mechanism is still open. Filed the residual as a new
      `[INFRA]`+`[DATA]` todo below (VM launch + consolidator health are both outside backend_engineer craft scope).

- [x] [INFRA] P0. **Residual (2026-07-14, slot 2, backend_engineer)** — two things needed to actually close this issue,
      neither doable from a backend_engineer session: (1) **Fix/investigate the DeFi manifest consolidator** — live-
      confirmed 2026-07-14T17:43Z the consolidated `availability_index.parquet` for
      `market-data-tick-defi-prd-central-element-323112` is ~4.8h stale (17,241.9s, vs the 120s default budget) — per
      `codex/05-infrastructure/manifest-consolidator-ssot.md` this means the Cloud Run Job / Scheduler for this bucket
      is behind or down; check its logs/last-run status and get it current. A consolidator stale for hours means EVERY
      DeFi backfill VM launched during that window hits `ManifestFreshnessCache`'s slow path (loud-fail today since
      `MANIFEST_ALLOW_STALE_FALLBACK` is unset on every DeFi launcher — verify this stays the safe default rather than
      flipping to the merge-fallback, which the codebase's own comments say "can OOM on large buckets"). (2) **Relaunch
      `mtds-dex-swaps-backfill` with `VM_SHUTDOWN_ON_COMPLETION=false` + `--on-demand`** (operator's `/blocked` ruling,
      BLK question posted by slot 2 2026-07-14) using the NOW RSS-instrumented tarball (`market-tick-data-service` ≥
      `bc84b3e5`) — SSH in post-crash (or watch it live) and grep `run.log` for `RSS_PROBE` lines: an `enter=...` with
      NO matching `exit=...` for the SAME label pinpoints the exact span the kill happened in; pull
      `dmesg | grep -i     oom` for the kernel's own account of which process/RSS got killed. This directly answers
      whether the crash is inside `freshness_cache.bulk_load()` (my repro reproduced the consolidator-stale condition
      but hit the LOUD raise, not a silent kill — so if the real VM shows an
      `enter=dex_swaps.process.freshness_bulk_load` with no `exit`, the raise itself or something in
      `read_availability_index`'s per-VM-shard fallback is the true spike; if it reaches
      `enter=dex_swaps.process.shard.*` first, the spike is per-venue, not the freshness cache) or elsewhere. Repo:
      `deployment-service` (VM launch) + `unified-trading-library`/`market-tick-data-service` if the consolidator itself
      needs a code fix. See "P0 full-path RSS trace" below for the full repro transcript. — ✅ DONE 2026-07-14 (slot 11,
      infra): both diagnostic actions performed with hard evidence captured; **neither closes the issue** — the
      consolidator crash-loop persists after a real (but insufficient) fix, and the VM crash is now definitively
      pinpointed to a specific function with a plausible code-level culprit identified. See "P0 infra diagnostics —
      consolidator misconfiguration fixed but crash persists" and "P0 infra diagnostics — dex_swaps VM crash pinpointed
      via live RSS_PROBE + kernel dmesg" below. Two new `[BACKEND]` P0 todos filed below for a fix-worker — this
      contradicts the "fix confirmed + shipped, no code change needed" closure two sections below for the SAME reason
      slot 2 already escalated once (2nd occurrence of this pattern on this issue) — escalating to operator via
      `/blocked` per governance (big finding: data-correctness, contradicts a prior recorded closure, blocks
      `mvp_backfill_defi_onchain_v10-002`'s G2 gate for a 5th consecutive relaunch attempt across both a Cloud Run job
      and a VM).

## P0 infra diagnostics — consolidator misconfiguration fixed but crash persists (2026-07-14, slot 11, infra)

**Root cause of the "locked" no-op crash-loop, confirmed via `gcloud logging read` + `gsutil stat` on the live
`uts-prod-manifest-consolidator-market-data-defi` Cloud Run Job**: the job's container had been bumped to 8vCPU/32Gi
LIVE (drift — not reflected in `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`, which had no
`market-data-defi` entry in any of the three per-bucket override maps) but `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` was left
at the code default (8GB) — exactly the "bumping ONLY the container does nothing" trap the Terraform file's own comment
documents (DuckDB still caps its buffer manager at 8GB and spills the incremental merge to Cloud Run gen2's in-memory
tmpfs, which itself consumes container RAM). Every cycle: `phase=duckdb_merge_start` →
`Container terminated on signal 9` ~15-25s later → lock orphaned until the 300s TTL clears → repeat. Canonical index
frozen at `2026-07-14T12:56:34Z` for the entire session (still frozen as of `18:36Z`, ~5.7h stale).

**Fix applied**: `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT=24GB` set live via `gcloud run jobs update` (immediate effect) +
codified in Terraform — `deployment-service@ebf928b` (adds `market-data-defi` to all three override maps: cpu=8,
memory=32Gi, duckdb_memory=24GB, mirroring the existing `market-data-tradfi-legacy` heavy tier).

**This did NOT fix the crash** — confirmed on the next TTL-cleared cycle (18:05:42-18:06:03Z):
`phase=duckdb_merge_start ... memory_limit=24GB` → `Container terminated on signal 9` **~15s later, faster than the 8GB
run's ~22-25s**, tripling the memory budget did not meaningfully change crash timing. Cloud Run's own execution-level
retry (`maxRetries=1`) then re-ran the task, which found its OWN sibling's now-orphaned lock still "fresh" (age <300s)
and no-op'd — so the overall `Execution` status reads `"Completed successfully"` / `succeededCount:1` in
`gcloud run jobs executions describe` despite doing ZERO real work. **This is a masking hazard worth flagging on its
own**: anyone checking Cloud Run's own execution history (rather than `_index/latest.json`'s `error_reason`) would see a
false all-clear.

**Assessment for the fix-worker**: raising `memory_limit` alone is not the fix. The crash-timing insensitivity to an
8GB→24GB range (3x) suggests either (a) DuckDB's buffer-manager accounting isn't actually bounding the real working set
for this merge (a query-plan or thread-parallelism issue — the job runs 8 vCPU, so DuckDB defaults to 8 parallel threads
with no `SET threads=` override in `manifest_consolidator.py`; per-thread scratch allocation on a wide anti-join across
27.4M+27.4M rows could aggregate past the pragma limit before the buffer manager's own tracking catches up), or (b) the
actual spike is a real >24-28GB working set regardless of the pragma (would need DuckDB's own `EXPLAIN ANALYZE` /
`PRAGMA` memory diagnostics, or profiling with a lower row-count synthetic reproduction, to pin down). Filed as new
`[BACKEND]` P0 todo below — DuckDB SQL/thread tuning inside `unified_trading_library/manifest_consolidator.py` is Python
service business logic, outside infra craft (`does_not: Python service business logic → backend_engineer`).

## P0 infra diagnostics — dex_swaps VM crash pinpointed via live RSS_PROBE + kernel dmesg (2026-07-14, slot 11, infra)

Per the operator's `/blocked` ruling this issue already carried, added a diagnostic override to the launcher
(`deployment-service@97d2b9d` — `VM_SHUTDOWN_ON_COMPLETION` now env-overridable, defaults `true` unchanged for every
other caller) and relaunched `mtds-dex-swaps-backfill` with `VM_SHUTDOWN_ON_COMPLETION=false --on-demand`, using the
already-fresh tarballs (`mtds-code @ 56efdd7d`, ancestor-confirmed ≥ `bc84b3e5` RSS-probe commit;
`unified-trading-library-code @ 43786858`, ancestor-confirmed ≥ `0fc088a9` slim-read fix — both auto-rebuilt ~18:13Z by
the `code-tarball-refresh` Cloud Run job, no manual rebuild needed this time).

**Result — crashed a 5th time, identically, but this time captured live**:

```
2026-07-14 18:25:36,671 INFO DEX swaps handler initialized (api_key_pool=9 keys)
2026-07-14 18:25:36,701 INFO RSS_PROBE enter=dex_swaps.process.freshness_bulk_load peak_rss_mb=543.4
bash: line 1:  7016 Killed   .../python -m market_tick_data_service --operation collect-dex-swaps ...
[vm-exec] command exited rc=137
```

No matching `exit=dex_swaps.process.freshness_bulk_load` — **the kill is definitively inside
`freshness_cache.bulk_load()`**, answering this todo's core question. VM stayed `RUNNING` post-crash (the diagnostic
override worked), enabling a live SSH pull of the kernel's own account:

```
kernel: python invoked oom-killer: gfp_mask=0x140dca(GFP_HIGHUSER_MOVABLE|__GFP_ZERO|__GFP_COMP), order=0, oom_score_adj=0
kernel: oom-kill:constraint=CONSTRAINT_NONE,...,task=python,pid=7016,uid=0
kernel: Out of memory: Killed process 7016 (python) total-vm:23668396kB, anon-rss:15379504kB, file-rss:2808kB, ...
```

**Confirmed genuine kernel OOM-kill**: `anon-rss:15379504kB` (~14.67 GiB) on an `e2-standard-4` (16GB, ~15Gi usable) —
not a Cloud-infra artifact, not an exception, a real memory exhaustion inside `bulk_load()`.

**Sanity-checked the actually-installed code is the "fixed" version** (SSH'd in before the VM finished self-cleanup):
`unified_trading_library/manifest_freshness.py` `_refresh_locked()` does call
`read_availability_index(self.bucket, columns=[*_ROW_KEY_COLUMNS, "capture_status", "error_reason"])` — the slim path IS
wired in and running. Yet it still OOMs at ~14.7 GiB, far above the isolated local repro's measured **5.30 GiB** peak
for the same slim column set on the same real 27.4M-row index (see "P0 confirm — dex_swaps NEW FINDING closed" below).

**Root of the discrepancy, found by reading the actual implementation**
(`unified-trading-library/unified_trading_library/manifest_writer/_read_index.py`):

1. `_read_consolidated_if_fresh()` (line 569) — its own docstring (lines 582-584) admits: _"columns: Optional column
   filter passed to `pd.read_parquet`; reduces peak decode memory for slim reads (**full parquet bytes still
   downloaded**, but only the requested columns are decoded)."_ The 445MB raw-bytes download itself isn't the OOM
   driver, but this confirms the "slim" savings only apply at decode time, not download time — worth the fix-worker
   verifying `_read_parquet_columns_safe` actually pushes `columns=` into the pyarrow reader (true column-pruned decode)
   rather than decoding all 41 columns then subsetting in pandas (which would explain the gap outright).
2. **The isolated repro measured `bulk_load()` in isolation** (per its own "What's NOT yet done" caveat in the section
   below) — it did not exercise `_read_index_slim()`'s FULL path, specifically the `_read_self_shard()` +
   `_merge_shard_frames([consolidated_df, self_shard])` step (`_read_index.py:521-526`) that runs immediately after the
   slim consolidated read. That merge/dedup step is a second, unmeasured memory consumer plausibly closing most of the
   5.3 GiB → 14.7 GiB gap.

Filed as new `[BACKEND]` P0 todo below — this is a `unified-trading-library`/`ManifestFreshnessCache` code investigation
(pyarrow column-pruning verification + self-shard-merge memory profiling), outside infra craft.

- [x] [BACKEND] P0. **DeFi manifest consolidator Cloud Run job (`uts-prod-manifest-consolidator-market-data-defi`) still
      SIGKILLs every cycle even at `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT=24GB`** (was 8GB; container is 8vCPU/32Gi) — crash
      timing ~15s post-`duckdb_merge_start`, no better than the 8GB run's ~22-25s, so raising the memory budget 3x did
      not meaningfully change the outcome. Canonical `availability_index.parquet` for
      `market-data-tick-defi-prd-central-element-323112` has been frozen at `2026-07-14T12:56:34Z` all day (>5.7h stale
      as of this writing). Investigate: (a) whether DuckDB's 8-thread default (no `SET threads=` override anywhere in
      `manifest_consolidator.py`) is causing per-thread scratch memory to blow past the `memory_limit` pragma's own
      accounting on the incremental anti-join across the 27.4M-row canonical + delta shards; (b) whether the actual
      working set genuinely exceeds 24-28GB regardless of thread count, in which case the merge SQL/query plan itself
      needs restructuring (e.g. batch the anti-join, or reduce columns materialized during the merge, mirroring the
      `read_availability_index(columns=...)` slim-read pattern already used elsewhere). Also flag: Cloud Run's own
      `execution.status` reads `"Completed successfully"` after the `maxRetries=1` retry no-ops on the still-orphaned
      lock — anyone checking Cloud Run execution history instead of `_index/latest.json.error_reason` gets a false
      all-clear; worth a follow-up to make `MANIFEST_CONSOLIDATION_FAILED`/stall alerting the primary signal instead.
      Repo: `unified-trading-library` (`manifest_consolidator.py`). See "P0 infra diagnostics — consolidator
      misconfiguration fixed but crash persists" above for the full evidence. — ✅ ACTED ON hypothesis (a), NOT YET
      LIVE-VERIFIED 2026-07-14 (slot-4, backend_engineer): `unified-trading-library@6b229121`. Reasoning for
      prioritizing (a) over (b): the observed crash-timing INSENSITIVITY to a 3x `memory_limit` increase (8GB→24GB gave
      ~22-25s→~15s, i.e. got WORSE not better) is the signature of a threads-driven FIXED overhead exceeding the
      container regardless of the pragma, not a genuinely oversized single working set (which would show SOME relief
      from 3x more memory headroom). DuckDB parallelises hash/anti-joins and sorts across `os.cpu_count()` threads by
      default (8 vCPU on this container, no `SET threads=` override anywhere in the module before this fix), each thread
      carrying its own scratch buffers not fully accounted against `memory_limit`. Added `CONSOLIDATOR_DUCKDB_THREADS`
      (default `"4"`, operator-tunable without a redeploy, mirrors the existing `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT`
      pattern) and wired `SET threads=<N>` into the merge connection alongside `SET memory_limit`; also logs the thread
      count in the existing `phase=duckdb_merge_start` lines so a future diagnostic session has it in Cloud Run logs
      directly (closing the "no DuckDB-side memory profile, only kernel dmesg" evidence gap this issue's prior sessions
      kept hitting). Two regression tests added (`test_duckdb_merge_applies_threads_pragma`,
      `test_duckdb_threads_env_default`). Full `quality-gates.sh` green. **NOT closing this issue**: this is a
      defensible, testable action on hypothesis (a) — it does NOT prove the OOM is fixed, only ships the fix for the
      most probable cause given the evidence. Live verification (does the Cloud Run job actually survive its next cycle
      post-deploy) is infra-craft (Cloud Run job redeploy), out of this backend_engineer session's scope — filed as a
      new `[INFRA]` todo below. The "Also flag" alerting-signal item (Cloud Run `execution.status` false all-clear) is
      UNADDRESSED — still open, needs its own follow-up (infra/observability scope, not touched this session).

- [x] [INFRA] P0. **Residual verification (2026-07-14, slot-4, backend_engineer)**: `unified-trading-library@6b229121`
      shipped `CONSOLIDATOR_DUCKDB_THREADS` (default `"4"`, bounds DuckDB's thread-parallel scratch memory) as the fix
      attempt for the `uts-prod-manifest-consolidator-market-data-defi` Cloud Run job's SIGKILL-every-cycle. This has
      NOT been live-verified — needs: (1) confirm the Cloud Run job picks up the new code on its next deploy (image
      rebuild/redeploy per the job's normal rollout path — check whether it auto-redeploys from
      `unified-trading-library`'s latest or needs an explicit trigger); (2) watch the NEXT consolidation cycle's Cloud
      Run logs for the new `phase=duckdb_merge_start ... threads=4` log line (confirms the fix is live) and whether
      `Container terminated on signal 9` still fires; (3) if it still SIGKILLs, that refutes hypothesis (a) — try
      progressively lower `CONSOLIDATOR_DUCKDB_THREADS` (e.g. 2, 1) via `gcloud run jobs update` (live, no redeploy
      needed, mirrors how `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT=24GB` was set) before concluding (a) is wrong and escalating
      to hypothesis (b) (SQL/query-plan restructuring, a bigger `[BACKEND]` follow-up); (4) once a cycle succeeds,
      confirm `_index/availability_index.parquet` for `market-data-tick-defi-prd-central-element-323112` advances past
      its current `2026-07-14T12:56:34Z` freeze (`gsutil stat` / `_index/latest.json`). Repo: `deployment-service`
      (Cloud Run job trigger/redeploy) + `unified-trading-library` (if a further code change is needed after (3)). — ✅
      DONE 2026-07-14 (slot 4, infra): all 4 items performed; **verification FAILED to close the issue — hypothesis (a)
      is refuted**, see "P0 infra residual verification — threads pragma confirmed insufficient" below for the full
      evidence and the new `[BACKEND]` follow-up filed.

- [x] ✅ [BACKEND] P0. **`mtds-dex-swaps-backfill` VM still OOMs (kernel-confirmed, anon-rss≈14.67GiB on a 16GB
      `e2-standard-4`) inside `ManifestFreshnessCache.bulk_load()`'s "fixed" slim-read path** (`_refresh_locked()` →
      `read_availability_index(columns=[...])`), despite the isolated local repro of the same slim path measuring only
      5.30 GiB peak on the same real 27.4M-row index. Two concrete leads to check first (both in
      `unified-trading-library/unified_trading_library/manifest_writer/_read_index.py`): (1) verify
      `_read_parquet_columns_safe` (called from `_read_consolidated_if_fresh`, line ~593/618) actually pushes `columns=`
      into the underlying pyarrow/pandas parquet reader for true column-pruned DECODE, not just a read-then-select — its
      own docstring at lines 582-584 only promises the decode step is pruned, and doesn't rule out a full intermediate
      materialization; (2) profile `_read_self_shard()` + `_merge_shard_frames([consolidated_df, self_shard])`
      (`_read_index.py:521-526`), which runs immediately after the slim consolidated read inside
      `_read_availability_index_slim()` and was NOT exercised by the isolated `bulk_load()`-only repro in "P0 confirm —
      dex_swaps NEW FINDING closed" below — this merge/dedup step is the most likely unmeasured contributor to the
      5.3→14.7 GiB gap. Repo: `unified-trading-library`. See "P0 infra diagnostics — dex_swaps VM crash pinpointed via
      live RSS_PROBE + kernel dmesg" above for the full RSS_PROBE + dmesg transcript. — ✅ INVESTIGATED + REAL FIX
      SHIPPED 2026-07-14 (slot-16, backend_engineer), **NOT a full close** — see "P0 — root cause pinpointed inside
      `manifest_freshness.py` itself; real fix shipped, ~3.56 GiB confirmed saved, still above the 16GB VM ceiling"
      below.

## P0 infra residual verification — threads pragma confirmed insufficient (2026-07-14, slot 4, infra)

Picked up the open `[INFRA] P0` residual-verification todo for `unified-trading-library@6b229121`
(`CONSOLIDATOR_DUCKDB_THREADS`, default `"4"`) on the `uts-prod-manifest-consolidator-market-data-defi` Cloud Run job.

**Item (1) — does the Cloud Run job auto-pick-up the new code? NO, confirmed by direct image inspection, not
inference.** The job's container resolves `market-tick-data-service:latest`, which itself `FROM`s a **digest-pinned**
`unified-trading-library` base image (`ARG BASE_IMAGE_DIGEST` in `market-tick-data-service/Dockerfile`). That pin was
last bumped 2026-07-14T00:47:55Z (`ec37e0cc`, UTL@`1a4b5238`) — **~19 hours stale** relative to `6b229121` (19:16:26Z).
The `update-dependency-version.yml` fan-out that's supposed to auto-refresh this pin on every UTL republish **has not
fired in this repo since 2026-06-28** (`gh run list --workflow=update-dependency-version.yml` — last run
2026-06-28T20:05:27Z) — a separate, longer-standing automation gap, not something this session attempts to fix.
Confirmed via direct content inspection (not just git-ancestor math): pulled `market-tick-data-service:latest` (digest
`029f6e00…`, built 19:23:08Z, i.e. AFTER `6b229121` landed) and grepped
`/app/unified_trading_library/manifest_consolidator.py` for `CONSOLIDATOR_DUCKDB_THREADS` — **absent**. The MTDS-side
rebuild alone does not carry the fix; the UTL base-image digest pin has to be bumped too.

**Remediation applied**: content-verified the new UTL AR image (`0.55.0`/`latest`, digest `sha256:06d1481d…`, published
2026-07-14T19:26:31Z) DOES contain the fix (same pull+grep technique), then bumped `ARG BASE_IMAGE_DIGEST` in
`market-tick-data-service/Dockerfile` by hand (the established pattern this file's own comment trail already documents —
same move as `99f7bd73`/`b11199cb`/`491862ed`/`4d84268b`/`b737ca1f`), shipped as `market-tick-data-service@dfc93dbb`.
The repo's LDR→main promote (`unified-trading-pm`'s `ldr-to-main-promote-fleet.yml`, cron `8,23,38,53 * * * *`) is what
triggers the actual MTDS image rebuild via `image-build-gate.yml` on the promotion PR — manually `workflow_dispatch`'d
it rather than waiting up to 15 min for the next tick. Re-pulled `market-tick-data-service:latest` (new digest
`e4e792c8…`, tag `dfc93db`) and confirmed `CONSOLIDATOR_DUCKDB_THREADS` now present.

**Item (2) — watched the next real cycle (lock TTL is ~300s, so only ~1-in-5 of the once-a-minute scheduled executions
actually reach `duckdb_merge_start`; the rest no-op on the still-fresh orphaned lock, which is itself the
Cloud-Run-execution-status masking hazard flagged in "P0 infra diagnostics — consolidator misconfiguration fixed but
crash persists" above).** First real cycle on the fixed image: `phase=duckdb_merge_start … threads=4` at
2026-07-14T19:52:48.614894Z → `Container terminated on signal 9` at 19:53:11.867814Z. **Still SIGKILLs — refutes
hypothesis (a) as sufficient on its own.**

**Item (3) — progressively lowered `CONSOLIDATOR_DUCKDB_THREADS` live via `gcloud run jobs update --update-env-vars` (no
redeploy needed)**, one lock-TTL cycle at a time:

| `CONSOLIDATOR_DUCKDB_THREADS` | `duckdb_merge_start` | `Container terminated on signal 9` | Survival |
| ----------------------------- | -------------------- | ---------------------------------- | -------- |
| 4 (code default)              | 19:52:48.614894Z     | 19:53:11.867814Z                   | ~23s     |
| 2                             | 19:58:47.454283Z     | 19:59:26.933991Z                   | ~39.5s   |
| 1 (floor)                     | 20:03:49.959854Z     | 20:05:26.188312Z                   | ~96s     |

**Clear, monotonic, roughly-doubling survival-time trend as thread count halves — thread-parallel scratch memory IS a
real, measurable contributor** (consistent with hypothesis (a)'s reasoning) — **but even the minimum possible thread
count (1) still OOMs.** This rules out "just tune the threads pragma" as a sufficient fix: the underlying working set
for this incremental anti-join, even single-threaded, still exceeds the 24GB `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` budget
on this 32Gi container. Escalating to hypothesis (b) per the todo's own decision rule.

**Item (4) — not reached**: no cycle succeeded, so `_index/availability_index.parquet` for
`market-data-tick-defi-prd-central-element-323112` remains frozen at `2026-07-14T12:56:34Z` (re-checked via
`gsutil stat` immediately after the threads=1 crash — unchanged, still the same ~7.5h-and-growing stale timestamp).

**Left the job at `CONSOLIDATOR_DUCKDB_THREADS=1`** (the longest-survival, most-conservative setting measured) as the
current live state — it does not fix the crash-loop but is a strict improvement over the code default (4) with no
downside, until a fix-worker restructures the merge SQL/query-plan itself. Filed as a new `[BACKEND]` P0 todo below —
DuckDB merge SQL/query-plan restructuring inside `unified_trading_library/manifest_consolidator.py` is Python service
business logic, outside infra craft scope (`does_not: Python service business logic → backend_engineer`).

- [x] [BACKEND] P0. **`uts-prod-manifest-consolidator-market-data-defi`'s DuckDB incremental-merge working set genuinely
      exceeds 24GB regardless of thread count** — confirmed via a controlled 3-point live experiment (see "P0 infra
      residual verification — threads pragma confirmed insufficient" above): `CONSOLIDATOR_DUCKDB_THREADS` at 4/2/1
      survived ~23s/~39.5s/~96s respectively before `Container terminated on signal 9` — a clear thread-count-correlated
      DELAY, but no thread setting (including the floor, 1) prevents the OOM. This rules out hypothesis (a) (pure
      thread-scratch-memory overhead) as a sufficient fix on its own; the merge SQL/query-plan itself needs
      restructuring per hypothesis (b) from "P0 infra diagnostics — consolidator misconfiguration fixed but crash
      persists" above — e.g. batch the anti-join over the canonical (27.4M-row) + delta shards instead of a single
      monolithic incremental merge, or reduce columns materialized during the merge (mirroring the
      `read_availability_index(columns=...)` slim-read pattern already used elsewhere and the `_build_membership_sets`
      single-pass fix shipped for the VM-side `ManifestFreshnessCache` OOM in "P0 — root cause pinpointed inside
      `manifest_freshness.py` itself" above — same underlying corpus-growth pressure, different codepath).
      `CONSOLIDATOR_DUCKDB_THREADS` is currently live-set to `1` via `gcloud run jobs update` (drift from Terraform,
      which does not set `CONSOLIDATOR_DUCKDB_THREADS` at all — only `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` is codified in
      `manifest_consolidator_scheduler.tf`; the unset env var falls back to the code default of `"4"`) as a stopgap; a
      real fix should restore/codify a sane value once the merge itself no longer OOMs regardless of thread count. Repo:
      `unified-trading-library` (`manifest_consolidator.py`). — ✅ ROOT-CAUSED + FIX SHIPPED 2026-07-14 (slot-9,
      backend_engineer): `unified-trading-library@39979c5a` — see "P0 — DuckDB CTE materialization root-caused + fixed
      (NOT MATERIALIZED)" below for the full mechanism + measured evidence. **NOT a full close**: verified via a
      synthetic local repro (real module functions, real DuckDB 1.5.3), not against the actual Cloud Run job / real
      27.4M-row DeFi canonical — that redeploy + live-cycle verification is infra scope, filed as a new `[INFRA]` P0
      todo below.

## P0 — DuckDB CTE materialization root-caused + fixed (NOT MATERIALIZED) (2026-07-14, slot-9, backend_engineer)

Picked up the last open `[BACKEND] P0` todo (thread-tuning confirmed insufficient, memory_limit confirmed insufficient —
both from "P0 infra residual verification — threads pragma confirmed insufficient" above). Given this issue's own
history of shipping unverified DuckDB fixes that turned out insufficient (3 prior rounds: memory_limit 8GB→24GB, threads
4→2→1, both confirmed NOT to fix the crash), built a local, empirical repro BEFORE touching any code, using the real
module's own SQL-construction helpers (`_dedup_key_sql`/`_resolve_dedup_cols`/`_stale_drop_predicate`) against a
synthetic ~5M-row/31-column parquet canonical (mirrors the live 27.4M-row DeFi shape's dedup-key width) — this sandbox
has no working `gcloud`/GCS access (same `cap_dac_override` snap failure prior sessions on this issue hit), so a real
27.4M-row live repro was not possible; the synthetic repro isolates the QUERY-PLAN mechanism, which is
data-shape-independent.

**Root cause**: in the incremental-merge CTE chain (`_duckdb_merge_payload`), `canon` is referenced twice
(`survivors_raw` + `contested`) and `survivors_raw` is referenced three times (`dupe_keys` + `survivors_clean` +
`survivors_deduped`). DuckDB's default CTE-materialization heuristic buffers a multiply-referenced CTE's FULL result
ONCE rather than re-streaming it per reference — so both `canon` (the entire filtered canonical, ~27.4M rows wide) and
`survivors_raw` (canon minus the tiny contested set — nearly the same size) get held as full-width intermediate buffers
simultaneously with every downstream operator that reads them.

**The missing piece prior sessions' `memory_limit`/`threads` tuning couldn't reach**: on Cloud Run gen2,
`temp_directory` (DuckDB's spill-to-disk target once a materialized buffer exceeds `memory_limit`) is a **RAM-backed
tmpfs** — so a materialized CTE that spills still consumes real container memory, just outside DuckDB's own
`memory_limit`-tracked accounting. This is why raising `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` 8GB→24GB (3x) barely moved
crash timing (~22-25s→~15s, i.e. got WORSE): the pragma only reallocates HOW MUCH of the SAME oversized materialized
working set lives in DuckDB-tracked RSS vs. tmpfs-spilled bytes — never how big that working set actually is. Same
explanation for the threads experiment's floor-still-OOMs result: fewer threads delays the crash (less **concurrent**
scratch overhead) but the underlying serial materialization is the same size regardless.

**Local confirmation** (synthetic 5,000,000-row canon.parquet + 3,000-row incremental changed-shard, real DuckDB 1.5.3,
`temp_directory` pointed at `/dev/shm` to mimic Cloud Run gen2's tmpfs, tracking BOTH the process's own RSS
(`/proc/self/status VmRSS`) AND the tmpfs spill size (`du -sm`) — the sum approximates what a Cloud Run cgroup would
actually see):

| Config                            | DuckDB-tracked RSS | tmpfs spill | **TOTAL real footprint** | elapsed |
| --------------------------------- | ------------------ | ----------- | ------------------------ | ------- |
| BEFORE, `memory_limit=1GB`        | 1.53 GB            | 6.98 GB     | **8.51 GB**              | 32.7s   |
| BEFORE, `memory_limit=4GB`        | 4.56 GB            | 4.01 GB     | **8.57 GB**              | 10.2s   |
| **AFTER (NOT MATERIALIZED), 1GB** | 1.51 GB            | 3.67 GB     | **5.20 GB** (−39%)       | 27.8s   |
| **AFTER (NOT MATERIALIZED), 4GB** | 3.61 GB            | 0 GB        | **3.61 GB** (−60%)       | 4.5s    |

The BEFORE rows reproduce the exact insensitivity-to-`memory_limit` signature this issue already documented live (TOTAL
footprint ~8.5GB regardless of the 1GB vs 4GB pragma — the SAME real working set, just relocated between DuckDB-tracked
and tmpfs-spilled). The AFTER rows (adding `NOT MATERIALIZED` to `canon` and `survivors_raw`) cut the TOTAL real
footprint 39-60% at this scale, AND ran faster (streaming avoids the spill I/O entirely at 4GB budget). Output verified
byte-identical to the unmodified query both directions (`SELECT * FROM a EXCEPT SELECT * FROM b` = 0 rows, both ways) —
`NOT MATERIALIZED` is a pure execution-plan hint, the SQL semantics are unchanged.

**Fix shipped**: `unified-trading-library@39979c5a` — `WITH canon AS NOT MATERIALIZED (...)` and
`survivors_raw AS NOT MATERIALIZED (...)` in the incremental-merge branch of `_duckdb_merge_payload`. Regression-guard
test added (`test_duckdb_incremental_merge_marks_wide_ctes_not_materialized`) that spies on the executed SQL text and
asserts both hints are present — a future refactor silently dropping them would NOT be caught by any output-correctness
test (the hint changes only the execution plan), so this pins the SQL text directly. Full
`test_manifest_consolidator.py` suite (76→78 tests) + `test_manifest_consolidator_canon_schema_align.py` green; full
`quality-gates.sh` green.

**What this does NOT prove**: the 39-60% reduction is measured at 5M rows / 1-4GB budgets, not the real 27.4M-row DeFi
canonical against the actual 32Gi Cloud Run container (5.5x the row count, ~30x the memory budget) — the scaling
relationship at that scale is plausible-but-unconfirmed. Also unexplored: whether `changed`/`changed_keys` (each
referenced twice) would benefit from the same hint — left untouched since they hold only the small incremental shard set
(cheap either way), to keep this fix's blast radius minimal and its evidence precise. Filed as a new `[INFRA]` P0 todo
below for the live Cloud Run verification this session's sandboxed `gcloud` (same broken snap `cap_dac_override` prior
sessions on this issue hit) cannot perform.

- [x] [INFRA] P0. **Live-verify `unified-trading-library@39979c5a` (NOT MATERIALIZED fix) against the real
      `uts-prod-manifest-consolidator-market-data-defi` Cloud Run job** — confirm the image picks up the new code (per
      "P0 infra residual verification" above, this job's `market-tick-data-service:latest` base image is digest-pinned
      and needs an explicit bump if `update-dependency-version.yml` hasn't auto-fired; verify via direct content
      inspection — pull + grep for `NOT MATERIALIZED` in the deployed `manifest_consolidator.py`, not just git-ancestor
      math), then watch the next real `duckdb_merge_start` cycle (lock TTL ~300s, so only ~1-in-5 once-a-minute
      scheduled executions actually reach it) for `Container terminated on signal 9` vs. a successful write. If it
      survives, confirm `_index/availability_index.parquet` for `market-data-tick-defi-prd-central-element-323112`
      advances past its current frozen timestamp (currently stale since 2026-07-14T12:56:34Z per this issue's own
      diagnostics above). If it STILL crashes, that means the real 27.4M-row canonical's working set exceeds even the
      NOT-MATERIALIZED-streamed footprint — next step would be restoring `CONSOLIDATOR_DUCKDB_THREADS` from its current
      live stopgap value (`1`) upward now that the dominant materialization cost is gone (may restore useful parallelism
      without the OOM this issue's thread experiment hit), or genuinely batching the anti-join over date-range
      partitions (this issue's `ManifestFreshnessCache` sibling fix's `date_range`-scoping idea, applied to the
      consolidator side). Repo: `deployment-service` (Cloud Run job redeploy/trigger) + `unified-trading-library` (if a
      further code change is needed). — ✅ DONE 2026-07-14 (slot 5, infra) — **live-verified, does NOT close**: the fix
      is real and substantial (~10x longer survival) but insufficient alone. See "P0 infra live-verify — NOT
      MATERIALIZED fix confirmed deployed, survival improved ~10x, still OOMs" below for the full evidence. New
      `[BACKEND]` P0 todo filed below (date-range batching, Python/SQL service logic, outside infra craft).

## P0 infra live-verify — NOT MATERIALIZED fix confirmed deployed, survival improved ~10x, still OOMs (2026-07-14, slot 5, infra)

Picked up the last open `[INFRA] P0` todo (live-verify `unified-trading-library@39979c5a` against the real Cloud Run
job). Non-snap `gcloud`/`docker` (same `~/google-cloud-sdk` workaround prior infra sessions on this issue used — the
snap install's `cap_dac_override` failure reproduces in this sandbox too) were sufficient; no escalation needed.

**Step 1 — confirmed the fix was published but NOT yet deployed.** Pulled the currently-deployed
`market-tick-data-service:latest` image (digest `17ae49848e95…`, built 2026-07-14T20:24:56Z) and content-grepped
`manifest_consolidator.py` — `NOT MATERIALIZED` absent. Pulled the newest tagged
`unified-trading-library:latest`/`0.55.0` image (digest `174863e1…`, published 20:46:11Z) and content-grepped the same
file — **present**. Confirmed via `git merge-base --is-ancestor 39979c5a HEAD` that the local `unified-trading-library`
clone (HEAD `8745d9eb`) descends from the fix commit.

**Step 2 — found + fixed a real digest-pin staleness gap** (same class this issue already documented once for
`6b229121`/threads): `market-tick-data-service/Dockerfile`'s `ARG BASE_IMAGE_DIGEST` was still pinned to `06d1481d…`
(the pre-`39979c5a` UTL image). Bumped it to `174863e1…`, shipped `market-tick-data-service@804584ef` via the normal
Pass-1 QG → Pass-2 quickmerge flow. Manually `workflow_dispatch`'d `ldr-to-main-promote-fleet.yml` (PM repo) rather than
waiting for the next `*/15` cron tick — opened MTDS promote PR #576, `image-build-gate` + `quality-gates-v2` both green,
auto-merged 20:59:21Z. Fresh MTDS image built 20:58:08Z (digest `e61ea7245f…`, tags `804584e,latest`) — content-verified
via pull+grep: `NOT MATERIALIZED` present, `pip show unified-trading-library` = `0.55.0` (the fixed build).

**Step 3 — found + fixed a SECOND, more subtle gap**: even after the fresh MTDS image existed, the Cloud Run **job**
kept executing the OLD digest. Cloud Run Jobs resolve a `:latest` tag reference to a concrete digest **at job-update
time**, not per-execution — confirmed by describing the crashed execution `n2266` (started 20:58:04, the first cycle
after the fresh image existed) and finding it still ran digest `17ae49848e95…` (the pre-fix image), not `e61ea7245f…`.
Forced re-resolution with `gcloud run jobs update … --image=…:latest` (no-op-looking update, same tag, but it re-reads
`:latest` at apply time) — subsequent executions confirmed via
`executions describe … --format='value(spec.template.spec.containers[0].image)'` to run digest `e61ea7245f…`. **This
resolution-pinning behavior is a real operational trap worth flagging on its own** — any prior session's "bumped the
digest, should be live now" assumption for this job could have been silently wrong without this per-execution digest
check.

**Step 4 — watched real cycles on the confirmed-fixed image + digest, across two thread settings**:

| `CONSOLIDATOR_DUCKDB_THREADS` | execution | `duckdb_merge_start` | `Container terminated on signal 9` | survival |
| ----------------------------- | --------- | -------------------- | ---------------------------------- | -------- |
| 1 (live stopgap, unchanged)   | `lpj95`   | 21:04:49.389503Z     | 21:08:41.622698Z                   | ~232.2s  |
| 1 (live stopgap, unchanged)   | `82g2p`   | 21:10:47.382174Z     | 21:14:15.907698Z                   | ~208.5s  |
| 4 (code default, tested live) | `w4sbp`   | 21:15:51.141516Z     | 21:16:51.737567Z                   | ~60.6s   |

Both threads=1 runs survive **~10x longer** than every pre-fix crash this issue recorded (15-25s, insensitive to
`memory_limit`) — hard confirmation the `NOT MATERIALIZED` hint is doing real work in production, not just the synthetic
5M-row local repro. But the SAME threads-scaling trend from the pre-fix "P0 infra residual verification" table
reproduces post-fix (more threads → faster crash, more concurrent scratch overhead) — threads=4 crashed nearly 4x faster
than threads=1. **Reverted `CONSOLIDATOR_DUCKDB_THREADS` back to `1`** (the best measured setting, both pre- and
post-fix) as the final live state.

**Step 5 — index freshness, unchanged**: `_index/availability_index.parquet` for
`market-data-tick-defi-prd-central-element-323112` remains frozen at `2026-07-14T12:56:34Z` (re-checked via
`gsutil stat` after every crash — no successful cycle occurred at any thread setting tested). `latest.json` continues
reporting `"success": true, "no_op": true, "error_reason": "locked"` for every skipped cycle — the same
Cloud-Run-execution-status masking hazard this issue flagged earlier (`succeededCount:1` even on a pure no-op) remains
unaddressed, still worth its own follow-up.

**Verdict — this todo does NOT close the issue.** The fix is genuine and shipped correctly (both digest-pin gaps found
and closed as part of this verification), but the real 27.4M-row DeFi canonical's working set still exceeds the
NOT-MATERIALIZED-streamed footprint at both thread settings tested (1 and 4) on the 32Gi container. This confirms the
todo's own anticipated "if it STILL crashes" branch — the remaining path is genuinely batching the incremental anti-join
over date-range partitions (not just tuning threads/memory_limit, both now exhausted as levers), mirroring the
`ManifestFreshnessCache` sibling fix's `date_range`-scoping idea. Filed below as a new `[BACKEND]` P0 todo — SQL
query-plan restructuring inside `unified_trading_library/manifest_consolidator.py` is Python service business logic,
outside infra craft (`does_not: Python service business logic → backend_engineer`).

- [x] [BACKEND] P0. **`uts-prod-manifest-consolidator-market-data-defi`'s DuckDB incremental-merge still OOMs even with
      the `NOT MATERIALIZED` streaming fix (`unified-trading-library@39979c5a`) live-deployed and confirmed working (
      survival went from ~15-25s to ~208-232s at `threads=1`, ~60.6s at `threads=4` — both still crash)** — the real
      27.4M-row DeFi canonical's working set genuinely exceeds the NOT-MATERIALIZED-streamed footprint regardless of
      thread count on the 32Gi/24GB-budget container. `_index/availability_index.parquet` for
      `market-data-tick-defi-prd-central-element-323112` remains frozen at `2026-07-14T12:56:34Z` (now >8h stale).
      Threads/memory_limit tuning is exhausted as a lever (see "P0 infra live-verify — NOT MATERIALIZED fix confirmed
      deployed" above + "P0 infra residual verification — threads pragma confirmed insufficient" earlier in this issue
      for both pre- and post-fix thread sweeps). Next step: genuinely batch the incremental anti-join in
      `_duckdb_merge_payload` over date-range partitions (process the canonical+delta merge in bounded date-range chunks
      instead of one monolithic full-corpus pass) — mirrors the `ManifestFreshnessCache` sibling fix's
      `date_range`-scoping idea (`market-tick-data-service`'s slim-read pattern) applied to the consolidator side.
      `CONSOLIDATOR_DUCKDB_THREADS` is currently live-set to `1` (best measured setting, both pre- and post-fix) — leave
      it there until this lands. Also still open: Cloud Run's `execution.status` reads
      `"Completed     successfully"`/`succeededCount:1` on a pure no-op (locked, zero rows touched) — worth a follow-up
      to make `error_reason` the primary success signal instead of relying on someone checking `_index/latest.json` by
      hand. Repo: `unified-trading-library` (`manifest_consolidator.py`). — ✅ FIX SHIPPED 2026-07-14 (slot-3,
      backend_engineer): `unified-trading-library@2ab54ce0` — see "P0 — date-range chunked batching shipped, NOT yet
      live-verified" below for the design + evidence. **NOT a full close**: no `gcloud`/GCS access in this sandbox (same
      limitation every prior session on this issue hit) to run against the real 27.4M-row canonical — verified via a
      targeted synthetic multi-chunk regression test instead. Live Cloud Run verification filed as a new `[INFRA]` todo
      below.

## P0 — date-range chunked batching shipped, NOT yet live-verified (2026-07-14, slot-3, backend_engineer)

Picked up the last open `[BACKEND] P0` todo (NOT MATERIALIZED confirmed insufficient — survival improved ~10x but the
real canonical still OOMs at every thread setting tested). Root-caused the remaining O(canonical) cost: the `dupe_keys`
self-heal `GROUP BY` on `survivors_raw` needs per-group hash-aggregate state for every row it visits —
`NOT MATERIALIZED` only changes whether a CTE's result is buffered vs re-streamed, it does not shrink what an aggregate
must visit. The ANTI JOIN / SEMI JOIN / window-dedup passes have the same property: their working set scales with
however many rows flow through `canon` in one query, not with how the CTE is materialized.

**Fix shipped**: `unified-trading-library@2ab54ce0` — `_duckdb_merge_payload`'s incremental branch now runs the
identical merge SQL (anti-join, self-heal `dupe_keys`, contested/winners window-dedup, Option B collapse) once PER
DATE-RANGE CHUNK instead of once over the whole corpus, writing each chunk to its own temp parquet file, then
concatenating all chunk files into the final output via a plain (join-free) passthrough `COPY`. Chunk width is
`CONSOLIDATOR_MERGE_CHUNK_DAYS` (default 30 days, operator-tunable live via `gcloud run jobs update --update-env-vars`,
same pattern as `CONSOLIDATOR_DUCKDB_THREADS`/`CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` — no redeploy needed to tune further
down if 30 days is still too wide for the real corpus). A safety cap (`_DUCKDB_MERGE_MAX_CHUNKS=2000`) widens the chunk
width automatically if a corrupted/outlier `date` value would otherwise blow the date span out to thousands of
near-empty chunk queries.

**Provably safe** (not just empirically): `date` is the FIRST column of `_BASE_DEDUP_COLS` — two rows can only share a
dedup key if they share the same `date` value, so chunking strictly on date can NEVER split a dedup/self-heal group
across two chunks. This is the same invariant the codebase already leans on elsewhere (`ORDER BY date, venue, data_type`
in the full-rebuild path).

**Regression coverage** (`tests/unit/test_manifest_consolidator.py`, both new, full `quality-gates.sh` green including
the pre-existing 3549-line suite — 0 basedpyright errors, 0 lint failures):

- `test_duckdb_incremental_merge_splits_into_date_range_chunks` — with `CONSOLIDATOR_MERGE_CHUNK_DAYS=1` and rows on 3
  dates ~89 days apart, spies on executed SQL and asserts the merge fires as MULTIPLE `COPY ... survivors_raw ...`
  queries (not the pre-fix single monolithic one) each still carrying the `NOT MATERIALIZED` hints, plus a single
  join-free passthrough concat `COPY`, then asserts the final consolidated output is byte-correct (all 3 venues, all 3
  dates present).
- `test_duckdb_incremental_merge_chunking_preserves_dedup_across_chunk_boundary` — a pre-existing canonical-internal
  duplicate on one date (self-heal target) plus a contested-key shard update on a date ~5 months away, both under
  `CONSOLIDATOR_MERGE_CHUNK_DAYS=1` (forcing them into different chunk queries): asserts the duplicate still collapses
  to one row (later `attempted_at` wins) AND the contested key still correctly picks up the shard's newer write — i.e.
  chunking doesn't regress either dedup mechanism.
- Coverage report (`coverage.xml` from the full suite run) confirms the new bounds-query / chunk-loop / per-chunk-merge
  / concat code paths were actually exercised (hit-count ≥1 on every new line except the degenerate no-parseable-dates
  fallback branch, which no test data exercises — a defensive no-op path, not new correctness-critical logic).

**What this does NOT prove**: no live run against the real `uts-prod-manifest-consolidator-market-data-defi` Cloud Run
job / the actual 27.4M-row DeFi canonical — this sandbox has no working `gcloud`/GCS access (the same `cap_dac_override`
snap failure every prior diagnostic session on this issue hit, confirmed not re-checked this session since the fix
itself needed no cloud access to implement or unit-test). The synthetic tests prove the chunking mechanism is correct
and exercises the new code paths; they do NOT prove the real corpus's per-chunk working set actually stays under the
container's memory budget at the default 30-day chunk width. Filed as a new `[INFRA]` P0 todo below, mirroring this
issue's own established verification pattern (bump the digest-pinned MTDS base image if `update-dependency-version.yml`
hasn't auto-fired, confirm via direct content inspection not just git-ancestor math, watch a real `duckdb_merge_start`
cycle for survival vs. `Container terminated on signal 9`).

- [x] [INFRA] P0. **Live-verify `unified-trading-library@2ab54ce0` (date-range chunked incremental merge) against the
      real `uts-prod-manifest-consolidator-market-data-defi` Cloud Run job** — confirm the image picks up the new code
      (per this issue's own repeated digest-pin-staleness gotcha: the job's `market-tick-data-service:latest` base image
      is digest-pinned in `market-tick-data-service/Dockerfile`'s `ARG BASE_IMAGE_DIGEST` and needs an explicit bump if
      `update-dependency-version.yml` hasn't auto-fired since 2ab54ce0 landed; verify via direct content inspection —
      pull + grep the deployed `manifest_consolidator.py` for `"merge_chunks"` or `CONSOLIDATOR_MERGE_CHUNK_DAYS`, not
      just git-ancestor math; also re-check the Cloud Run JOB itself re-resolves `:latest` at update time, not just the
      image existing — a prior session on this issue found the job kept running a stale digest even after a fresh image
      existed until `gcloud run jobs update --image=...:latest` was re-applied). Then watch the next real
      `duckdb_merge_start` cycle (lock TTL ~300s, so only ~1-in-5 once-a-minute scheduled executions actually reach it)
      for `Container terminated on signal 9` vs. a successful write. If it survives, confirm
      `_index/availability_index.parquet` for `market-data-tick-defi-prd-central-element-323112` advances past its
      long-frozen `2026-07-14T12:56:34Z` timestamp. If it STILL crashes, the default 30-day chunk width is still too
      wide for the real 27.4M-row corpus — lower `CONSOLIDATOR_MERGE_CHUNK_DAYS` live via
      `gcloud run jobs update --update-env-vars` (no redeploy needed, same lever already proven for
      `CONSOLIDATOR_DUCKDB_THREADS`) before concluding the chunking design itself is insufficient. Once a cycle
      succeeds, `CONSOLIDATOR_DUCKDB_THREADS` (currently live-set to `1` as a stopgap) may be worth raising back up now
      that each chunk's working set is far smaller — re-test rather than assume. Repo: `deployment-service` (Cloud Run
      job image/digest verification) + `unified-trading-library` (if `CONSOLIDATOR_MERGE_CHUNK_DAYS` needs tuning down
      after this verification). — ✅ DONE 2026-07-14 (slot 2, infra) — **the OOM is fixed, but this surfaced a NEW
      CRITICAL data-correctness bug; NOT a close.** See "P0 infra live-verify — OOM fixed, but row-count regression
      found" below for the full evidence, remediation actions taken (digest bump, task-timeout bump, scheduler paused),
      and the two new todos filed (one P0 CRITICAL data-correctness, one P1 timeout/lock-TTL follow-up).

## P0 infra live-verify — OOM fixed, but row-count regression found (2026-07-14, slot 2, infra)

**Step 1 — confirmed deployed image was STALE, missing `2ab54ce0`.** Content-grepped the currently-deployed
`market-tick-data-service:latest` (digest `e61ea7245f…`, the same one slot 5's prior session verified for
`NOT MATERIALIZED`/`39979c5a`) — `CONSOLIDATOR_MERGE_CHUNK_DAYS`/`merge_chunks` absent. Confirmed `39979c5a` is an
ancestor of `2ab54ce0` (`git merge-base --is-ancestor`), so the deployed image predated the chunking fix. Same
digest-pin-staleness gotcha this issue has hit repeatedly: bumped `market-tick-data-service/Dockerfile`'s
`ARG BASE_IMAGE_DIGEST` to the newest published `unified-trading-library` image (`03a1951d…`, tag `0.55.0`/`latest`,
content-verified to contain the chunking code first). Shipped `market-tick-data-service@3ff887c8`, manually
`workflow_dispatch`'d `ldr-to-main-promote-fleet.yml` (PM repo) rather than waiting for the `*/15` cron, opened MTDS
promote PR #576→**#577**, `image-build-gate` + `quality-gates-v2` both green, auto-merged 22:07:05Z. Fresh MTDS image
built 22:06:46Z (digest `738e504d…`), content-verified via pull+grep: `CONSOLIDATOR_MERGE_CHUNK_DAYS`/`merge_chunks`
present. Forced the Cloud Run JOB to re-resolve `:latest` (`gcloud run jobs update --image=...:latest`) — same
resolution-pinning trap slot 5 already documented (Jobs resolve `:latest` at update time, not per-execution).

**Step 2 — confirmed ZERO OOM-kills on the fixed image across 3 independent full-length attempts.** Watched the live
`*/1` cron. A race meant the FIRST execution to acquire the lock after my digest bump (`l5655`, created 22:06:01) had
already started on the STALE pre-chunking image before my re-resolve landed — it OOM'd identically to every prior crash
in this issue (`Container terminated on signal 9` at 22:10:52Z, ~245s survival at `threads=1`, matching the
NOT-MATERIALIZED-only ceiling already documented above). Every execution AFTER that point ran the fixed `738e504d` image
(`ds5pp` created 22:11:01, `xj2fb` created 22:17:01, `2kqdc` created 22:23:01) — **none of the three ever SIGKILL'd.**
`ds5pp`'s first attempt and (separately) `xj2fb`'s first attempt each ran the full 1800s to
`Terminating task because it has reached the maximum timeout of 1800 seconds` (Cloud Run's own task-timeout killer,
confirmed via `run.googleapis.com/varlog/system` log entries — a TIMEOUT, not a SIGKILL/OOM). `2kqdc` — the one
execution that got to run undisturbed after I intervened (see Step 3) — **completed successfully in 24m28.93s**, logging
`phase=duckdb_merge_done rows_out=27410052` and writing a fresh consolidated index. **The chunking fix does what it was
designed to do: eliminates the OOM.**

**Step 3 — found + fixed a NEW operational hazard: 300s lock TTL << actual chunked-merge duration → livelock.**
`_LOCK_TTL_SECONDS = 300.0` (`manifest_consolidator.py`) was tuned for pre-chunking cycle times (93-121s observed
2026-07-11, per that constant's own code comment) — chunking's real-world duration (24-30+ min) blows past it by 5-10x,
so every `*/1` cron tick within a still-running cycle's lock window found the lock "fresh" and skipped, but once the TTL
elapsed the NEXT tick found it "stale" and started a COMPETING concurrent merge — observed 3+ executions (`ds5pp`,
`xj2fb`, `2kqdc`) running concurrently, each independently re-downloading the full 27.4M-row canonical and re-running
the whole chunked merge, none able to finish before the next lock-steal. This reproduces, at a new scale, the exact
"wasted concurrent DuckDB merge" hazard `_LOCK_TTL_SECONDS`'s own comment already names as the leading suspect for a
prior scheduler-vs-manual SIGKILL asymmetry. **Remediation (infra-scope, both reversible/live-tunable, no code
change)**: (1) `gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-defi-cron` — stops new
lock-stealing executions from spawning; left PAUSED as the session-end state (protective, autonomous-OK per the
kill-switch rule) until the correctness bug below is fixed and re-verified. (2)
`gcloud run jobs update --task-timeout=3600` — doubles the per-attempt deadline for future executions (does NOT apply
retroactively to the already-in-flight executions' baked-in 1800s spec); confirmed live-tunable via
`gcloud run jobs update --help`. `_LOCK_TTL_SECONDS` itself is a hardcoded Python constant, NOT an env var like
`CONSOLIDATOR_DUCKDB_THREADS`/`_MEMORY_LIMIT`/`_MERGE_CHUNK_DAYS` — raising it needs a code change, filed below.

**Step 4 — CRITICAL: the completed merge dropped rows beyond its own alert threshold, and the corrupted output is
already live in production.** `2kqdc`'s completion log (22:47:23Z):

```
CRITICAL ManifestConsolidator: ROW COUNT REGRESSION bucket=market-data-tick-defi-prd-central-element-323112
canon_rows=27445013 rows_out=27410052 dropped=34961 (0.1274%) — exceeds 0.1000% alert threshold; suspected merge bug,
not routine dedup/prune
```

followed 6s later by
`wrote consolidated index (27410052 rows, 412281352 bytes) to market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`
and `success=True`. The `_ROW_COUNT_REGRESSION_ALERT_THRESHOLD = 0.001` check (`manifest_consolidator.py:1733`) is
**pure observability** — it logs + emits `MANIFEST_ROW_COUNT_REGRESSION` but does NOT block the write or roll back;
confirmed via direct code read. The regression compares `rows_out` against `canon_rows` (the PRE-merge canonical row
count, 27,445,013) — a net LOSS of 34,961 rows relative to the starting canonical, i.e. more rows vanished than the
~4,348-row incremental shard update could plausibly explain via legitimate dedup, tripping a threshold specifically
designed (per its own docstring) to distinguish real bugs from routine dedup/prune.
`_index/availability_index.parquet`'s `Update time` DID advance (confirmed via `gsutil stat`: now
`2026-07-14T22:47:57Z`, vs. the `12:56:34Z` it had been frozen at all day) — **this is genuinely the first successful
write since the OOM incident began, and it may have silently dropped ~35K real rows into production.** Whether this is
(a) a genuine bug in the chunking/concat logic — the fix's own safety argument (chunking strictly on `date` can never
split a dedup group) may not hold at a boundary/concat edge — or (b) a legitimate one-time cleanup of duplicate/orphaned
rows accumulated during today's chaos (multiple crashed merges + orphaned locks + this session's own
concurrent-execution pile-up) is **not established** — this needs a backend_engineer investigation, not an infra guess.
Not independently re-verified whether `xj2fb`'s later `pruned 2 shards, rows_in=0/rows_out=0` no-op cycle (22:47:48Z,
correctly found nothing new after `2kqdc`'s fresh write) touched row counts further.

**Escalating per the data-pipeline-correctness HARD RULE** (`codex/02-data/data-pipeline-correctness-hard-rule.md`) — a
big finding (data-correctness, already live in production) — via `/blocked` to the operator in the same turn as this
commit, not deferred.

- [x] [BACKEND] P0 CRITICAL. **Investigate the `2ab54ce0` chunked-merge ROW COUNT REGRESSION** — the first successful
      post-fix consolidator write (`2kqdc`, 2026-07-14T22:47:29Z) dropped 34,961 rows (0.1274%) versus the pre-merge
      canonical, tripping `_ROW_COUNT_REGRESSION_ALERT_THRESHOLD` (`manifest_consolidator.py:1733`, "suspected merge
      bug, not routine dedup/prune" per the check's own log message). This output is ALREADY LIVE in
      `market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (27,410,052 rows, overwrote
      the prior ~9h-stale-but-presumably-correct canonical). Determine: (a) is this a real bug in
      `_duckdb_merge_payload`'s per-chunk anti-join/self-heal/concat logic — re-check the "chunking can never split a
      dedup group" safety argument specifically at chunk BOUNDARIES and in the final passthrough `COPY` concat step, not
      just the interior-of-chunk case the existing regression tests cover; or (b) a legitimate one-time cleanup of
      duplicate/orphaned rows from today's chaos (multiple crashed merges, orphaned locks, this session's own
      concurrent-execution pile-up before the scheduler was paused) — if (b), confirm which specific rows were dropped
      and why they were illegitimate duplicates, don't just assume. If (a), the corrupted index needs a remediation plan
      (revert to a known-good prior snapshot if one exists, or a corrective re-merge) — do NOT let downstream consumers
      keep reading it uninvestigated. The scheduler (`uts-prod-manifest-consolidator-market-data-defi-cron`) is
      currently PAUSED (this session's own remediation) — leave it paused until this is resolved and re-verified; do not
      silently un-pause. Repo: `unified-trading-library` (`manifest_consolidator.py`). — ✅ INVESTIGATED 2026-07-14
      (slot-3, backend_engineer) — **verdict: (b) legitimate one-time backlog clear, NOT a chunking bug** — see "P0
      investigation — chunking cleared, verdict (b) legitimate first-run backlog collapse" below for the full evidence
      (code-level boundary-safety review + a new adversarial regression test + a git-history timeline proof). **NOT a
      full close**: could not be verified against the REAL dropped rows (no `gcloud`/GCS access in this sandbox, same
      limitation every prior session on this issue hit) — filed a residual `[INFRA]` todo below for a live sample-based
      confirmation before the scheduler is un-paused.

## P0 investigation — chunking cleared, verdict (b) legitimate first-run backlog collapse (2026-07-14, slot-3, backend_engineer)

**Code-level boundary-safety review** of `_duckdb_merge_payload`
(`unified-trading-library/unified_trading_library/manifest_consolidator.py`): the chunk predicate
(`TRY_CAST(date AS DATE) >= start AND < end`) partitions `[min_date, max_date]` into a provably gapless, non-overlapping
half-open sequence (`start = end` of the prior chunk on every loop iteration), plus a separate `IS NULL` chunk for
unparseable dates — together these cover every row in `canon_select_all ∪ changed_select` exactly once. The dedup-key
NULL/`''` sentinel normalization (`_dedup_key_sql`) collapses both representations to the same key, but `TRY_CAST` also
maps both to `NULL` — so a dedup group that spans the NULL/`''` distinction still lands in the SAME (null-date) chunk,
no boundary split. `date` is always the first column of both the base dedup key (`_BASE_DEDUP_COLS`) and Option B's
`service_name`-excluded key (`part_norm_excl_svc`), so — since `TRY_CAST` is a pure, deterministic function of the raw
`date` value — two rows sharing an (unnormalized) dedup key are provably assigned to the same chunk by both mechanisms.
No boundary-splitting defect found by inspection.

**Adversarial regression test** (`unified-trading-library@0bd7cc27`,
`tests/unit/test_manifest_consolidator.py::test_duckdb_incremental_merge_chunking_preserves_self_heal_and_option_b_across_chunks`):
the existing 2 chunk-boundary tests each exercise exactly ONE dedup mechanism at a time. This new test forces
canonical-internal duplicate self-heal (`dupe_keys`), Option B cross-`service_name` collapse specifically on the
UNTOUCHED `survivors` path (harder than the `winners`/contested path, not previously chunk-boundary-tested), a
dual-source captured-vs-captured negative control (must survive intact), and a contested-key shard update — into FOUR
separate 1-day chunks (`CONSOLIDATOR_MERGE_CHUNK_DAYS=1`, dates ~90-270 days apart). All four resolved exactly as the
unchunked semantics predict. **PASSED** — full `quality-gates.sh` green, 80/80 tests in the file green.

**Git-history timeline proof**: Option B collapse (`unified-trading-library@9bc06261`) shipped 2026-07-14T16:31:18Z —
the SAME DAY, ~6h before the flagged write. Per this issue's own earlier sections, the DeFi bucket's canonical had been
frozen/stale since 12:56:34Z and every consolidation attempt OOM-crashed continuously until the chunking fix
(`2ab54ce0`, 21:44:36Z) landed and was confirmed deployed (~22:06-22:11Z, "P0 infra live-verify — OOM fixed" above).
This means `2kqdc` (22:47:23Z) is **provably the first time Option B's collapse logic has ever executed against this
bucket's real 27.4M-row canonical** — every attempt between 16:31Z and ~22:11Z crashed before completing. The
pre-existing canonical self-heal (`dupe_keys`, since `0de04b6e`/`800af156`, 2026-07-10) is in the same position — this
bucket had not completed a successful cycle in a long time, so any accumulated internal duplicates clear in this SAME
first-successful cycle too.

**Threshold-design context**: `_ROW_COUNT_REGRESSION_ALERT_THRESHOLD = 0.001` (added `52d5921a`, 2026-07-12) is
calibrated, per its own code comment, for "a small, self-limiting stale-row self-heal" under NORMAL, frequently-cycling
operation — not a multi-hour backlog compounding through TWO dedup mechanisms (one brand new) completing for the first
time in one cycle. 34,961/27,445,013 = 0.1274% is only marginally over the 0.1%/27,445-row cutoff — a bounded,
one-time-backlog-sized excess, not a proportional-to-corpus-size runaway that would suggest a genuine merge bug.

**Verdict: (b) — legitimate one-time cleanup, not a chunking/merge bug.** The chunking fix's role was purely enabling
the merge to survive to completion; it did not change merge semantics, and the adversarial test found no chunk-boundary
defect. **Recommendation: do NOT revert or re-merge the already-live index** — the evidence indicates it is a legitimate
cleanup, not corruption. Leave the scheduler PAUSED per this issue's own standing instruction until the residual
live-sample verification below completes.

- [x] [INFRA] P1. **Residual live verification (2026-07-14, slot-3, backend_engineer)**: the "verdict (b)" conclusion
      above is evidence-based (code review + adversarial synthetic test + git-history timeline) but NOT verified against
      the REAL ~34,961 dropped rows — this sandbox has no working `gcloud`/GCS access (same limitation every prior
      session on this issue hit). Needs: (1) if a backup/snapshot of the pre-`2kqdc` canonical still exists (check GCS
      object versioning / any pre-write snapshot this session's remediation may have taken), diff it against the live
      `27,410,052`-row index and sample ~20-50 of the dropped keys; (2) for each sampled dropped key, confirm it matches
      ONE of the two predicted patterns — either (a) a canonical-internal duplicate (same full dedup key including
      `service_name`, differing only in `attempted_at`/`written_at`/`instrument_count`) or (b) an Option B twin (same
      key EXCLUDING `service_name`, one row `capture_status='captured'`, the other not) — if a sampled dropped row
      matches NEITHER pattern, that reopens the "(a) real bug" hypothesis and needs escalation; (3) once confirmed,
      resume the scheduler (`uts-prod-manifest-consolidator-market-data-defi-cron`, currently PAUSED) — do NOT resume it
      based on this todo's evidence alone, only after the live sample check in (1)-(2) passes. Repo:
      `deployment-service` (GCS sample pull) + `unified-trading-library` (if a sampled row contradicts the verdict). —
      ✅ DONE 2026-07-14 (slot-3, infra) — **row-level live verification is INFEASIBLE, not merely inconvenient;
      escalated + operator-ruled, not silently skipped.** Found the exact pre-`2kqdc` snapshot: bucket versioning is
      `Suspended`, but soft-delete IS enabled, and generation `1784033794988708` (soft-deleted at
      `2026-07-14T22:47:29Z`, the exact `2kqdc` write instant) has `creation_time=2026-07-14T12:56:34Z` — an exact match
      to the frozen-canonical timestamp cited throughout this issue, confirmed via
      `gcloud storage objects describe --soft-deleted`. However, **GCS soft-delete blocks reading a soft-deleted
      object's CONTENT via any API** — confirmed directly: a JSON API `alt=media` request for that generation returns
      HTTP 400 `"Cannot request object data for soft-deleted object"`. The only way to read its bytes is
      `gcloud storage restore`, which writes back to the **same live path** (no destination override exists) — reading
      the pre-image would require briefly overwriting the current production `availability_index.parquet` (est. 10-30s
      window) with the stale pre-fix content before restoring today's generation back, exposing any of the fleet's
      unaudited downstream readers (feature builders, honesty-coverage, gating checks) to reverted data during that
      window. Also checked and ruled out the alternative of independent ground truth: `_index/per_vm/*.parquet` (the
      per-VM shard files the consolidator merges from) have already been pruned post-absorption — only
      `_legacy_seed.parquet` remains — so there is no raw-shard cross-check available either; the soft-deleted
      generation was the only remaining path to a pre-image, and it's unreadable without a live revert. **Escalated via
      `/blocked` (`BLK-a8931895`)** rather than deciding solo, given this is a genuine production-risk judgment call the
      todo itself didn't anticipate (it assumed a passive backup, not a live-swap). **Operator ruling: Option B — do NOT
      perform the live restore.** Rationale (verbatim reasoning from the ruling): reintroducing the ~9h-stale pre-fix
      canonical into the live path — even byte-exact-staged for ~10-30s — would deliberately inject known-worse content
      into a production path read by unenumerable fleet consumers, which violates the current protective posture
      (downstream is being gated OFF the suspect revision, not fed staler data on purpose); the existing adversarial
      regression test + git-history timeline proof already establish verdict (b) with high confidence, so finalize that
      documented verdict and record row-level live verification as INFEASIBLE without a prod revert, rather than
      pursuing it. **Scheduler (`uts-prod-manifest-consolidator-market-data-defi-cron`) stays PAUSED** — resuming it /
      unfreezing `mvp_backfill_defi_onchain_v10-002`'s G2 gate remains operator+backend-owned and will be decided on its
      own evidence, not unblocked by this verdict alone. Repo: `deployment-service` (GCS soft-delete investigation) +
      `unified-trading-pm` (this doc).

- [x] ✅ [BACKEND] P1. **`_LOCK_TTL_SECONDS = 300.0` (`manifest_consolidator.py`) is now far too short for the real
      chunked-merge duration (24-30+ min observed) and causes a lock-stealing livelock** — every cron tick past the TTL
      treats a still-running legitimate cycle as orphaned and starts a competing concurrent merge (observed 3+
      simultaneous executions this session, each re-downloading the full 27.4M-row canonical). This is a hardcoded
      Python constant, not a live-tunable env var like its `CONSOLIDATOR_DUCKDB_*`/`CONSOLIDATOR_MERGE_CHUNK_DAYS`
      siblings — raising it needs a code change (mirror the existing env-var-with-code-default pattern, or at minimum
      raise the hardcoded value to comfortably exceed the observed 24-30 min real-world merge duration with headroom,
      consistent with the constant's own "N x headroom over the worst observed cycle" design rationale). Separately, the
      job's `--task-timeout` was live-bumped to 3600s this session (`gcloud run jobs update`, applies to future
      executions only) as a stopgap — worth codifying in Terraform
      (`deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`) once a stable value is confirmed by a
      clean run under the new lock TTL. Repo: `unified-trading-library` (lock TTL) + `deployment-service` (Terraform
      task-timeout codification). — ✅ DONE 2026-07-14 (slot 5, backend_engineer): mirrored the existing
      env-var-with-code-default pattern — `unified-trading-library@9358fb0b` makes `_LOCK_TTL_SECONDS` read
      `CONSOLIDATOR_LOCK_TTL_SECONDS` from the environment (default unchanged at 300.0, so every fast bucket keeps
      today's prompt crash-recovery; two new regression tests: `test_lock_ttl_seconds_env_default`,
      `test_lock_ttl_seconds_env_override`). `deployment-service@fe67a53` codifies this session's live `--task-timeout`
      bump (1800s→3600s for `market-data-defi` only) in `manifest_consolidator_timeouts` and adds a new
      `manifest_consolidator_lock_ttl_seconds` Terraform map wiring `CONSOLIDATOR_LOCK_TTL_SECONDS=4200` for
      `market-data-defi` only (mirroring the existing per-bucket `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT`/`_THREADS` override
      pattern) — set comfortably above the bucket's own 3600s task-timeout so a "fresh" lock can only belong to a
      still-legitimately-running execution, structurally eliminating the livelock class rather than just widening the
      number. Both repos' full `quality-gates.sh` green. **Not live-verified against the real Cloud Run job** (this
      sandbox's `gcloud` is non-functional, same `cap_dac_override` snap failure prior sessions on this issue hit) — the
      Terraform change needs a real `tofu apply`/`gcloud run jobs update` + a watched cron cycle to confirm the env var
      actually reaches the job and the livelock stops recurring; filing that as a residual `[INFRA]` todo below.

- [x] ✅ [INFRA] P1. **Residual (2026-07-14, slot 5, backend_engineer)**: live-verify `deployment-service@fe67a53`
      (market-data-defi task-timeout 1800s→3600s + new `CONSOLIDATOR_LOCK_TTL_SECONDS=4200` Terraform override) against
      the real `uts-prod-manifest-consolidator-market-data-defi` Cloud Run job/scheduler — confirm the live
      `gcloud run jobs     update` values already match (this session's Terraform change codifies what was live-set
      earlier, but per this issue's own repeated digest/config-drift gotcha, verify by direct inspection, not just
      assuming Terraform state matches reality), and confirm the deployed
      `market-tick-data-service`/`unified-trading-library` image actually contains `unified-trading-library@9358fb0b`
      (the `CONSOLIDATOR_LOCK_TTL_SECONDS` env-read) — bump the digest-pinned base image in
      `market-tick-data-service/Dockerfile` if `update-dependency-version.yml` hasn't auto-fired, same recipe this issue
      has used repeatedly. Then un-pause the scheduler (`uts-prod-manifest-consolidator-market-data-defi-cron`,
      currently PAUSED per this issue's own prior remediation pending the row-count-regression investigation above — do
      NOT un-pause until that P0 CRITICAL todo is separately resolved) and watch a full `duckdb_merge_start` cycle for
      whether the lock-stealing/concurrent-execution pattern is actually gone. Repo: `deployment-service` (Cloud Run
      job/scheduler verification). — ✅ DONE 2026-07-14 (slot 16, infra): direct inspection found a REAL drift, not a
      confirmation — `gcloud run jobs describe uts-prod-manifest-consolidator-market-data-defi --region asia-northeast1`
      showed `timeoutSeconds=3600` already matching (live-set earlier, as expected), but `CONSOLIDATOR_LOCK_TTL_SECONDS`
      was **completely absent** from the job's env vars — `deployment-service@fe67a53`'s Terraform had been committed
      but never actually applied (`tofu apply`/`gcloud run jobs update` never ran for this specific var). Fixed live via
      `gcloud run jobs update uts-prod-manifest-consolidator-market-data-defi --region asia-northeast1     --update-env-vars CONSOLIDATOR_LOCK_TTL_SECONDS=4200`
      (mirrors this issue's own established live-set-first pattern; Terraform already codifies the same value so no
      drift going forward). Image check: pulled the then-deployed `market-tick-data-service:latest` (built
      2026-07-14T22:05:35Z) and grepped `/app` for `CONSOLIDATOR_LOCK_TTL_SECONDS` — **absent**, confirming the image
      predated `unified-trading-library@9358fb0b` (23:26:35Z). Root cause: `update-dependency-version.yml` hasn't
      auto-fired since 2026-06-28 (the same longstanding digest-pin-staleness gap this issue's prior sessions hit
      repeatedly) — the latest published UTL AR image
      (`sha256:01ca270796162cafd76fdde90bce3a77ec16a81ed3564f19c94b19b9aed553ea`, tag `0.55.0`/`latest`, published
      23:33:50Z) WAS content-verified (pull+grep) to contain the fix, but MTDS's `Dockerfile` was still pinned to an
      older digest (`03a1951d…`, 21:54:17Z). Bumped `ARG BASE_IMAGE_DIGEST` to the new digest, shipped
      `market-tick-data-service@4dee06a0` via quickmerge, manually `workflow_dispatch`'d `ldr-to-main-promote-fleet.yml`
      (repo `unified-trading-pm`) to fast-track the promotion rather than wait for the cron tick — merged to `main` via
      PR #578 (23:51:28Z), which triggered a fresh Cloud Build (`c6b130fa-9b78-44ff-9e13-d6882c5484a1`, SUCCESS).
      Re-pulled `market-tick-data-service:latest` (new build time `2026-07-14T23:49:00Z`, digest `sha256:4574ef37…`) and
      re-grepped `/app` — **`CONSOLIDATOR_LOCK_TTL_SECONDS` now present**, confirming the fix is in the deployed image.
      Re-described the live Cloud Run job a final time: `taskTimeout=3600`, `CONSOLIDATOR_LOCK_TTL_SECONDS=4200` both
      confirmed live, image resolves to the freshly-built `:latest`. **Did NOT un-pause the scheduler**
      (`uts-prod-manifest-consolidator-market-data-defi-cron` stays PAUSED) — per this todo's own explicit gate,
      resuming it is tied to the separately-tracked P0 CRITICAL row-count-regression item and is an operator+backend
      decision, not something this live-verify task authorizes; did not watch a `duckdb_merge_start` cycle for that
      reason. Repo: `deployment-service` (live Cloud Run verification + env-var fix) / `market-tick-data-service`
      (digest bump, `@4dee06a0`).

## P0 full-path RSS trace (2026-07-14, slot 2, backend_engineer)

Per the operator's `/blocked` ruling (relaunch with `VM_SHUTDOWN_ON_COMPLETION=false` + instrument the FULL `process()`
path, not `ManifestFreshnessCache.bulk_load()` in isolation, and pull `dmesg`): the VM-launch half is infra-craft (out
of scope for this session — `gcloud compute instances create` is not a backend_engineer action per
`agents/backend_engineer.md` `does_not`). This session did the backend-craft half:

**1. Traced the crash timing precisely against `dex_swaps_handler.py`'s actual code.** Every crash's `run.log` (this
issue's own Evidence + the "P0 residual" section below) shows: handler-init log → ONE `RESOURCE_SAMPLE` → `Killed` →
`rc=137`, with **zero** per-venue "collection complete" output. Reading `process()` top-to-bottom:
`recorder = DefiManifestRecorder(...)` (cheap, no I/O — just wraps `ManifestWriter.__init__`) →
`freshness_cache = ManifestFreshnessCache(...)` (cheap) → `await asyncio.to_thread(freshness_cache.bulk_load)` (the
FIRST I/O-bound call) → only THEN does `_collect_all_protocols()` (the per-venue GraphQL loop) start. Since no per-venue
output ever appears, the crash is strictly at-or-before `bulk_load()` returns. This RULES OUT the manifest-WRITE path
(`ManifestWriter._write_with_generation_match()` → `_read_with_generation()` at
`unified-trading-library/unified_trading_library/manifest_writer/_writer_io.py:798`, an unqualified
`pd.read_parquet(io.BytesIO(data))` full-schema read reached only on a legacy non-per-VM-shard write — a genuine,
separate latent hazard worth flagging but NOT reachable this early since it needs at least one shard result recorded
first).

**2. Shipped instrumentation** — `market-tick-data-service@bc84b3e5`: new `_rss_probe.py`
(`market_tick_data_service/cli/handlers/`) with `rss_probe_span(label)`, a context manager that logs
`RSS_PROBE enter=<label> peak_rss_mb=...` / `RSS_PROBE exit=<label> peak_rss_mb=...` (via `resource.getrusage`). Wired
around `freshness_cache.bulk_load()` and around each `_collect_one_shard()` call in `dex_swaps_handler.py`. Kept the
file at exactly 900 lines (the repo's hard `MAX_FILE_LINES` gate) by rewrapping 3 pre-existing docstrings to fewer,
wider lines — no content cut. `quality-gates.sh` green (file-size check passed at exactly 900). Because a SIGKILL can't
be caught, a `finally` won't fire either — so an `enter=X` with no matching `exit=X` in the next VM's `run.log` is
itself the diagnostic signal (which span was in-flight at kill time), no live attach needed for that part.

**3. Attempted a local repro of the exact call `ManifestFreshnessCache.bulk_load()` makes** (real prod GCS via ADC,
`GCP_PROJECT_ID=central-element-323112`, `.venv`, no VM):

```
[17:43:38] baseline rss_mb=11.5
bucket=market-data-tick-defi-prd-central-element-323112
[17:43:52] before slim read rss_mb=371.1
ManifestReader: consolidated blob age 17241.9s > 120s threshold — falling back to per-VM shards
unified_trading_library.manifest_writer._state.ManifestConsolidatorStaleError: Consolidated availability_index for
bucket='market-data-tick-defi-prd-central-element-323112' is stale or missing (older than
MANIFEST_CONSOLIDATED_STALENESS_SEC=120s) while per-VM shards exist — the manifest consolidator is behind or down.
Refusing to fall back to the per-VM shard merge (can OOM on large buckets). Remediation: fix the consolidator Cloud
Run Job + Scheduler for this bucket; set MANIFEST_ALLOW_STALE_FALLBACK=true to force the recovery merge.
```

This is a **live-confirmed, currently-active** finding: the DeFi bucket's consolidated index is ~4.8h stale RIGHT NOW
(2026-07-14T17:43Z), meaning `_read_slow_path()`'s per-VM-shards-exist check is true and (with
`MANIFEST_ALLOW_STALE_FALLBACK` unset, confirmed via `grep` across every DeFi launcher script) the code takes the
LOUD-FAIL branch — raising `ManifestConsolidatorStaleError` rather than silently OOMing on a per-VM-shard merge. This
did NOT reproduce the silent SIGKILL locally — a raised+caught (`ManifestFreshnessCache._refresh_locked()` wraps the
call in `try/except Exception: logger.exception(...)`) exception should print a traceback in `run.log`, which the
excerpted crash evidence doesn't show (though the excerpts may simply have been trimmed to the "interesting" tail rather
than the complete log — not verified either way).

**Net**: the mechanism producing a SILENT `rc=137` (vs. a loud, caught, logged `ManifestConsolidatorStaleError`) is
still not pinned down. Three live possibilities for the next diagnostic session to check via `RSS_PROBE` + `dmesg`: (a)
the exception-catch-and-log itself is somehow the expensive step (seems unlikely but unverified), (b) the production
VM's actual behavior differs from this repro in some way not caught by the static trace (e.g. a race where the
consolidator briefly refreshes and the per-VM-merge fallback DOES fire), or (c) the spike is genuinely downstream of
`bulk_load()`, inside `_collect_all_protocols()`'s per-shard catalogue reads, and the "no per-venue output" pattern is
explained by output buffering rather than crash-before-first-shard. The consolidator staleness is real and actionable
regardless of which of these is confirmed.

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

## P0 residual — dex_swaps STILL crashes on both confirmed fixes (2026-07-14, slot 2, infra)

Relaunched `mtds-dex-swaps-backfill` with fresh core tarballs, both required fixes tarball-freshness-verified present at
launch time (not just git-ancestor-checked): `mtds-code @ ecd3a4d4366f` (descendant of `d6846f1c`),
`unified-trading-library-code @ 9bc06261292d` (descendant of `0fc088a9`). `lc_verify_tarball_freshness` (the launcher's
own built-in gate) confirmed all 4 core tarballs current immediately before `gcloud compute instances create` ran — so
this is not a stale-tarball repeat of the prior gap.

**Result: identical crash, 4th time running.** Full `run.log` (VM `mtds-dex-swaps-backfill`, launched ~17:01Z, dead by
17:04:44Z):

```
17:04:23,884 INFO TheGraph key pool loaded: 9 keys available
17:04:23,884 INFO DEX swaps handler initialized (api_key_pool=9 keys)
17:04:24,547 INFO RESOURCE_SAMPLE ... mem=10.3% rss=679MiB ...
bash: line 1: 7012 Killed   .../python -m market_tick_data_service --operation collect-dex-swaps ...
[vm-exec] command exited rc=137
17:04:44,161 INFO received signal 15 — initiating shutdown
17:04:44,998 INFO DEPLOYMENT_FAILED 57f6560e-... (exit_code=137)
```

Dead within ~20s of process start, one `RESOURCE_SAMPLE` at a perfectly healthy 10.3%/679MiB (nowhere near the 85%
threshold), then `Killed`/`rc=137` — byte-for-byte the same signature as every crash this issue has already documented
(`mtds-perp-funding-backfill`'s original crash, `mtds-dex-pools-backfill`'s 3rd incarnation, and the "NEW FINDING"
`dex_swaps` crash that `unified-trading-library@0fc088a9` was credited with fixing).

**This contradicts the "P0 confirm — dex_swaps NEW FINDING closed" section's conclusion below.** That section's
RSS-instrumented repro measured `ManifestFreshnessCache.bulk_load()` in isolation (downloading + parsing the real
27.4M-row availability index two ways, FULL vs SLIM schema) and found FULL alone would OOM a 16GiB VM — a real and
almost certainly genuine hazard — but this relaunch proves that fix, as shipped, does not prevent the actual VM crash.
Possible explanations for a fix-worker to investigate (not diagnosed further here — out of infra craft scope): the
slim-read fix may not be on the actual code path `dex_swaps_handler.py` exercises at this point (e.g. a different call
site still uses the unqualified full-schema `read_availability_index`), or the true spike is elsewhere entirely and the
`ManifestFreshnessCache` full-schema repro was a real-but-not-THE-culprit hazard (the "P0 confirm + fix" section below
found a similar false-lead pattern with `_register_all_catalog_readers()` itself being cheap while a downstream call was
the actual cost).

**Escalating per governance** (this contradicts a previously-recorded "fix confirmed + shipped, no code change needed"
closure, and blocks `mvp_backfill_defi_onchain_v10-002`'s G2 gate for the 4th consecutive relaunch attempt): posting a
`/blocked` to the operator recommending a `VM_SHUTDOWN_ON_COMPLETION=false` diagnostic relaunch (or an
attach-before-delete window) so a fix-worker can inspect the box's actual memory/process state at time of kill, since
the 5s `RESOURCE_SAMPLE` cadence keeps missing whatever the real spike is — this is the same "invisible-between-samples"
gap this issue has now hit 3 times (dex-pools 3rd incarnation, this issue's own dex_swaps NEW FINDING, and this
relaunch).

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

## P0 — full `bulk_load()` path repro closes most of the 5.3GiB→14.67GiB gap; it's the Python-level tuple/set build, not the self-shard merge (2026-07-14, slot 3)

Picked up the 2nd open `[BACKEND] P0` todo above (the 5.30 GiB isolated-slim-read vs 14.67 GiB kernel-confirmed-OOM gap)
independently, via `/autonomous` re-dispatch on the DeFi dex-pools backfill issue (this doc's sibling
`mtds_defi_dex_backfill_vm_immediate_sigkill_2026_07_14.md`, which I've cross-linked here — same underlying bug,
different original entry point).

**What I ran**: unlike the prior isolated-slim-read repro (which hand-called
`read_availability_index(bucket, columns=[...])` directly), I called
`ManifestFreshnessCache(bucket=bucket)._maybe_refresh()` — the SAME internal method `bulk_load()` calls — with
`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` set (matching the real VM launcher's metadata value, avoiding the
local-default-120s stale-raise branch the earlier repro in "P0 full-path RSS trace" hit). This exercises
`_refresh_locked()` end-to-end: whichever read branch fires, PLUS the downstream
`_index_to_tuples`/`_index_to_skip_worthy_tuples` calls that build the Python-level `set`s `_captured`/`_skip_worthy` —
the exact part the isolated SLIM/FULL table (5.30 GiB / 19.72 GiB) did NOT include.

**Result**: completed successfully (no exception — the 86400s threshold avoided the stale-raise path), so no
`ManifestReader: ... falling back to per-VM shards` warning appeared in my run's output either, meaning this run took
the FAST direct-consolidated-read branch, **not** the `_read_self_shard()`/`_merge_shard_frames()` per-VM-shard-merge
path the open todo flagged as the leading suspect for the gap:

```
elapsed: 176.9s
tracemalloc current=17440.7MB peak=24286.5MB
ru_maxrss after=5888528.0 (KB, ~5.9GB resident at process end)
captured rows: 3,010,913
```

**Peak 24.3 GiB — HIGHER than the kernel-confirmed real-VM OOM figure (14.67 GiB)**, on the FAST path, without ever
touching the self-shard-merge code the open todo suspected. This is new information for that todo's two candidate
explanations:

1. **`_read_parquet_columns_safe` column-pruning itself** — not independently re-verified here (would need a
   pyarrow-level trace to confirm true predicate-pushdown decode vs. read-then-select), still worth checking per the
   todo's item (1), but the SLIM-vs-FULL table already measured (5.30 GiB vs 19.72 GiB) shows pruning IS doing
   _something_ real — the open question is just how much more it could still save.
2. **`_read_self_shard()` + `_merge_shard_frames()`** — my repro's peak EXCEEDED the real kernel-confirmed OOM without
   this path ever executing (fast-path branch, no fallback warning), which argues this is likely **not** the dominant
   unmeasured cost the todo hypothesized — since a run that skips it entirely still overshoots the real OOM figure.

**Most likely actual gap-closer**: the Python-level `set` construction
(`_index_to_tuples`/`_index_to_skip_worthy_tuples` building `_captured`/`_skip_worthy` from ~3M rows) that neither the
SLIM/FULL isolated table NOR the self-shard-merge hypothesis accounted for — tuple + hash-set overhead in CPython
routinely runs 3-5x raw data size, which is directionally consistent with going from a ~5.3 GiB pandas DataFrame to a
24+ GiB peak once that DataFrame gets converted into millions of Python tuples inside a `set`. Not conclusively isolated
here (would need a tracemalloc snapshot diff bracketing specifically `_index_to_tuples`/`_index_to_skip_worthy_tuples`
vs. the read itself to prove the split) — flagging as the most promising next-step for whoever closes the two remaining
`[BACKEND] P0` todos, since it reframes the fix direction: **the real fix is almost certainly NOT "prune more columns"
(diminishing returns once you're already at 7 slim columns) but "don't materialize millions of Python tuples/sets at
all"** — e.g. a `pyarrow.Table`-native hash-join / `.isin()` check against the caller's actual row-keys instead of
building the full corpus into an in-process Python set, or (simplest) actually scoping the read by the caller's known
date range (this doc's sibling issue's own recommended fix design: an optional `date_range` filter on
`ManifestFreshnessCache.__init__`, since none of the 9 DeFi handlers that use this class today pass one, and none of the
diagnostic sessions on this doc tested a date-scoped read specifically).

**Also note for whoever profiles this next**: the manifest's real row count keeps growing between diagnostic sessions
(27.4M raw rows / 3.01M "captured" rows as of this run, vs whatever it was when the 5.30 GiB/14.67 GiB figures were
measured earlier the same day) — every fresh repro on this bucket will report a bigger number than the last purely from
organic growth, independent of any code change. Worth pinning a snapshot of the index for reproducible before/after
comparison once a fix is actually implemented, rather than re-measuring against the live (growing) bucket each time.

## P0 — root cause pinpointed inside `manifest_freshness.py` itself; real fix shipped, ~3.56 GiB confirmed saved, still above the 16GB VM ceiling (2026-07-14, slot-16, backend_engineer)

Picked up the last open `[BACKEND] P0` todo (the two `_read_index.py` leads: column-pruning verification and the
self-shard-merge hypothesis). Read `manifest_freshness.py` end-to-end rather than `_read_index.py` first, since
`_refresh_locked()` is the caller and its own code — not just the reader it calls — was worth checking directly.

**Found the actual root cause, one level up from both hypothesized leads**: `_refresh_locked()` calls
`_index_to_tuples(index, capture_status_filter="captured")` AND `_index_to_skip_worthy_tuples(index)` as two COMPLETELY
INDEPENDENT full passes over the same slim-read DataFrame. `captured` is always a **strict subset** of `skip_worthy`
(`captured | empty_confirmed | expected_unattempted[EXPECTED_* reason]`), so every row that ends up `captured` had its
row-key tuple built and hashed into a Python `set` **twice** — once by each function, each with its own
`dict[str, list[str]]` intermediate and its own `for i in range(n_rows): out.add(tuple(...))` loop. On the real
27.4M-row DeFi index, `skip_worthy` alone is **15,174,538 rows** (slot-3's prior repro measured 3,010,913 `captured`
rows in isolation but never measured `skip_worthy`'s true size) — building ~15.2M + ~3.0M Python tuple-of-7-strings
objects into two separate sets is exactly the kind of Python-level materialization slot-3's "P0 —full `bulk_load()` path
repro" section (above) flagged as the most likely actual gap-closer, just not yet isolated to this specific doubled-pass
shape.

**Fix shipped**: `unified-trading-library@0aa284e8` — replaced the two functions with `_build_membership_sets(index)`,
which does ONE pass over ONLY the skip-worthy-filtered rows (masked once via pandas vectorised boolean ops, not iterated
twice), building each row-key tuple exactly once and tagging capture-membership inline via a boolean array — `captured`
is derived as a filtered subset of the SAME tuples `skip_worthy` already built, never recomputed. 26 pre-existing tests
pass unchanged (public behavior of `bulk_load`/`is_now_captured`/ `is_now_skip_worthy`/`captured_count` is
byte-identical); added 1 new regression test (`test_captured_is_always_subset_of_skip_worthy_at_scale`) pinning the
subset invariant at 400 synthetic rows across all 4 `capture_status` values. `quality-gates.sh` full green.

**Quantified against the REAL live 27.4M-row DeFi index** (same bucket, `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` to
force the same fast direct-consolidated-read branch slot-3's 24.3 GiB baseline used — confirms the self-shard-merge
hypothesis is NOT exercised in either measurement, so lead (2) from this todo is REFUTED as the dominant driver for this
branch, consistent with slot-3's own observation that their 24.3 GiB peak was also on the fast path):

| Run                                                                                              | Peak (ru_maxrss) |
| ------------------------------------------------------------------------------------------------ | ---------------- |
| BEFORE (slot-3's full `bulk_load()`-equivalent repro, same fast-path branch, `tracemalloc peak`) | 24.29 GiB        |
| **AFTER (this fix, `resource.getrusage().ru_maxrss`, same bucket/branch)**                       | **20.74 GiB**    |

**~3.56 GiB saved (≈14.6% reduction) — a real, confirmed, measured win.** `captured=3,010,913` /
`skip_worthy=15,174,538` rows, elapsed 103.1s (mostly GCS download + pandas parse, not the tuple-building itself).

**This does NOT close the issue.** 20.74 GiB still exceeds a 16GB `e2-standard-4`'s (~15Gi usable) capacity — the
kernel-confirmed real-VM OOM was at 14.67 GiB, so even the fixed code would still OOM-kill on that VM shape today. The
corpus has grown to the point where materialising ~15M Python tuples into an in-process `set` at all — regardless of how
many redundant passes do it — is no longer viable on a 16GB VM. Lead (1) from this todo (verify
`_read_parquet_columns_safe` pushes `columns=` into a true pyarrow-level pruned decode) was NOT independently
re-verified this session — worth checking, but the ~20.74 GiB post-fix figure with 7 already-pruned columns suggests the
Python-object overhead of ~15M tuples-in-a-set (not decode-time bytes) is now the dominant remaining cost, matching
slot-3's own directional estimate ("tuple + hash-set overhead in CPython routinely runs 3-5x raw data size").

**Filed as a new `[BACKEND]` P0 todo below**: the genuinely durable fix is almost certainly the design change slot-3
already proposed — an optional `date_range`/row-key-scoping filter on `ManifestFreshnessCache.__init__` so a single-date
(or narrow-window) backfill job never has to materialise the WHOLE corpus's skip-worthy set into a Python `set` at all,
only the rows relevant to its own job. None of the 9 DeFi handlers using this class today pass such a filter. This is a
genuine API-shape change across those call sites, not a one-file patch — scoped as its own todo rather than attempted
inline here to keep this session's change small, tested, and immediately shippable.

- [x] [BACKEND] P0. **Scope `ManifestFreshnessCache` reads to the caller's actual date range/row-key set** instead of
      materialising the WHOLE corpus's `captured`/`skip_worthy` Python sets on every `bulk_load()` — the confirmed
      remaining ~20.74 GiB peak (post `_build_membership_sets` single-pass fix, see above) is dominated by ~15.2M Python
      tuple-in-a-set objects, not the parquet read itself (already column-pruned to 7 slim columns). Add an optional
      `date_range: tuple[str, str] | None` (or similar) param to `ManifestFreshnessCache.__init__` that, when set,
      filters `index` to that window BEFORE calling `_build_membership_sets` — a single-date DeFi backfill job only ever
      needs freshness answers for its OWN date, not all 3.5 years of history. Audit + update the 9 DeFi handlers that
      instantiate this class (grep `ManifestFreshnessCache(` across `market-tick-data-service`) to pass their actual
      date/window once the param exists; keep the no-filter (whole-corpus) behavior as the default for back-compat with
      any caller that genuinely needs it. Repo: `unified-trading-library` (API) + `market-tick-data-service` (call-site
      updates). — ✅ DONE 2026-07-14 (slot 5, backend_engineer): `unified-trading-library@391f8196` adds
      `date_range: tuple[date, date] | None = None` to `ManifestFreshnessCache.__init__` (mirrors the existing
      `date_range` convention already used by `read_capture_status_counts` in `_queries.py`), applied to the `date`
      column via `pd.to_datetime(...).dt.date` boolean-mask filtering BEFORE `_build_membership_sets` runs — default
      stays `None` (whole-corpus, unfiltered) for back-compat. 3 new regression tests added
      (`test_date_range_none_default_covers_whole_corpus`, `test_date_range_scopes_membership_sets_to_window`,
      `test_date_range_single_date_window_is_inclusive`); full `quality-gates.sh` green. All 9 DeFi handlers that
      instantiate this class now pass `date_range=(target_day, target_day)` (or the handler's own single-date variable)
      — `market-tick-data-service@e3bbb2a3`: `dex_swaps_handler.py`, `dex_pools_handler.py`, `perp_funding_handler.py`,
      `liquidations_handler.py`, `liquidation_events_handler.py`, `lending_indices_handler.py`,
      `risk_params_handler.py`, `lst_rates_handler.py`, `gas_fee_handler.py` — all confirmed via
      `grep ManifestFreshnessCache(` to be the complete 9-call-site set. Full `market-tick-data-service`
      `quality-gates.sh` green (repo's own `tests/unit/` suite ran and passed; the 3 handler test files with
      `ManifestFreshnessCache` mocks —
      `test_dex_pools_handler.py`/`test_dex_swaps_handler.py`/`test_liquidations_handler.py` — patch the constructor via
      `patch.object(mod, "ManifestFreshnessCache", return_value=cache_mock)`, which accepts the new kwarg
      transparently). **Not independently re-verified on a live backfill VM this session** (that's VM-launch/infra
      craft, out of scope here) — the durable API-shape + all-9-call-sites work this todo asked for is complete; a fresh
      VM relaunch to confirm the peak RSS actually drops below the 16 GiB ceiling is a natural next
      residual-verification step for an infra session, mirroring the pattern used earlier in this issue for the other
      fixes.

- [x] [BACKEND] P0. **Residual verification of the `date_range` fix above (`unified-trading-library@391f8196`) — the fix
      as shipped did NOT actually resolve the OOM.** Picked up the "not independently re-verified on a live backfill VM"
      gap the prior todo flagged, plus arrived at this issue independently via the sibling
      `mtds_defi_dex_backfill_vm_immediate_sigkill_2026_07_14.md` doc (same bug, different entry point, findings merged
      here earlier in this doc). Local repro of the EXACT real-handler call
      (`ManifestFreshnessCache(bucket=<defi>, ttl_seconds=60, date_range=(target_day, target_day)).bulk_load()`, real
      27.4M-row DeFi index): **peak 14,856.6 MB (~14.86 GiB)** — matching the kernel-confirmed real-VM OOM
      (`anon-rss:15379504kB`, "P0 infra diagnostics" section above) almost exactly. **Root cause of the gap**:
      `date_range` was applied as a pandas boolean-mask filter AFTER `read_availability_index()` already
      downloaded+decoded the FULL corpus into a DataFrame — filtering post-decode does nothing for peak memory, the
      expensive step (decode) already happened. Confirmed via a raw pyarrow test on the same real index: reading with a
      proper row-group predicate-pushdown `filters=[("date","==","2026-07-01")]` (skips non-matching row groups BEFORE
      decode, not after) measured **peak=5.4 MB, elapsed=0.1s** for the identical single-day window — the manifest's row
      groups ARE date-clustered enough for pushdown to work extremely well; the bug was that nothing in the read chain
      was passing a filter down to pyarrow at all.

      **Fix shipped**: `unified-trading-library@a5b07ff7e` — threaded an optional `filters:
                      list[tuple[str,str,str]] | None` parameter through the read chain (`read_availability_index` →
                      `_read_availability_index_slim` → `_read_consolidated_if_fresh`/`_read_self_shard` →
                      `_read_parquet_columns_safe` → `pd.read_parquet(..., filters=filters)`), bypassing `_INDEX_SLIM_CACHE` when
                      filters are set (that cache's key doesn't encode the filter — caching a filtered result under an unfiltered key
                      would leak a partial result to a later caller). `ManifestFreshnessCache._refresh_locked()` now builds
                      `filters` from `date_range` and passes it through; kept the existing post-decode pandas filter too as a
                      belt-and-suspenders correctness check (row-group predicate pushdown is a SKIP heuristic based on row-group
                      min/max stats, not a guaranteed exact filter — a boundary-spanning row group could still include a few
                      out-of-range rows). Did NOT touch the rarer stale-consolidator per-VM-shard-merge fallback path (already
                      separately flagged, opt-in only via `MANIFEST_ALLOW_STALE_FALLBACK`, out of this fix's scope per rule-11
                      blast-radius caution). 14 new/updated regression tests (`test_manifest_freshness.py` +
                      `test_manifest_read_index_slim.py`), full `unified-trading-library` `quality-gates.sh` green.

                      **Local re-verification post-fix**: same exact call, peak dropped **14,856.6 MB → 741.9 MB (~95% reduction)**,
                      same correct captured count. (Not as low as the isolated 5.4 MB pyarrow test — the full path also does a
                      self-shard-merge attempt + the membership-set build; 742 MB is still comfortably safe on `e2-standard-4`'s
                      16 GiB.)

                      **Real production VM verification (the actual proof)**: rebuilt tarballs (`unified-trading-library-code @
                      a5b07ff7e338`, exact fix commit), relaunched `mtds-dex-pools-backfill` with the IDENTICAL config that had
                      killed it 5 times before (`--protocols uniswap_v2 --start 2026-07-01 --end 2026-07-03`, `e2-standard-4`, SPOT).
                      **Result: `exit_code=0`, `DEPLOYMENT_COMPLETED`** — `DEX pools collection complete: 17 total records
                      ({'uniswap_v2_ETHEREUM': 17})`, 17 real rows written to GCS, manifest shard updated, clean self-delete. The
                      exact workload that died identically 5 times (rc=137, SIGKILL within seconds of "DEX pools handler
                      initialized") now runs to full completion. This is the closing verification `mtds_backfill_vm_startup_oom_rc137
                      _2026_07_14` has needed since it was filed.

                      Repo: `unified-trading-library` (fix + tests) + `deployment-service` (tarball rebuild + VM relaunch, verification
                      only, no code change).

**Status: this specific OOM mechanism (unscoped `ManifestFreshnessCache` reads) is RESOLVED and production-verified.**
The other 2 open threads on this doc (the `uts-prod-manifest-consolidator-market-data-defi` DuckDB consolidator crash
and the `2ab54ce0` chunked-merge row-count regression) are separate, already-tracked issues on this same doc — not
re-verified or touched by this entry.

## Evidence

- `mtds-perp-funding-backfill` full `run.log` (crash at 2026-07-14T11:41Z): preflight complete → 1 RESOURCE_SAMPLE
  (mem=10.8%) → `Killed` → `rc=137`.
- `mtds-dex-swaps-backfill` full `run.log` (crash at 2026-07-14T11:38Z): handler initialized → 1 RESOURCE_SAMPLE
  (mem=9.9%) → `Killed` → `rc=137`.
- `mtds-dex-pools-backfill` 3rd incarnation `run.log` (crash at 2026-07-14T11:49Z, 1-day/1-protocol job): handler
  initialized → **no RESOURCE_SAMPLE** → `Killed` → `rc=137`.
- `mtds-dex-pools-backfill` POST-FIX `run.log` (`unified-trading-library@a5b07ff7e`, real production run):
  `DEX pools handler initialized` → real collection proceeds → `DEX pools collection complete: 17 total records` →
  `exit_code=0` → `DEPLOYMENT_COMPLETED`. The definitive before/after pair for this issue.
- `mtds-lending-indices-20260715-002613` POST-FIX `run.log` (same `a5b07ff7e` + full fix chain, a SECOND, independent
  handler — `lending_indices_handler.py`, not `dex_pools_handler.py`): `Lending indices handler initialized`
  23:29:00.959Z → `RESOURCE_SAMPLE`s healthy (rss=693MiB→896MiB, mem=10.7%→11.8%) → real per-day Morpho collection
  proceeds well past the old ~20-90s kill window → `Lending indices collection complete: 554/479/340 total records` for
  days 2026-03-27/28/29 respectively, real parquet objects confirmed landing in
  `market-data-tick-defi-prd-central-element-323112`. See "P0 residual live-verify — lending_indices_handler.py / Morpho
  backfill" below for the full session.
- `gcloud compute operations list --filter="targetLink~mtds-{perp-funding,dex-swaps,dex-pools}-backfill"`: only
  `insert`/`delete` ops, no `preempted` — rules out SPOT preemption.
- `f8cab3f0` (2026-07-12, `market-tick-data-service`) — the most recent change to `_register_all_catalog_readers()`,
  confirms it loads a combined ~1.6M-row cross-asset-group catalogue once per process.

## P0 residual live-verify — lending_indices_handler.py / Morpho backfill (2026-07-14/15, autonomous dispatch)

Dispatched independently to relaunch the long-pending Morpho `lending_indices` backfill
(`bucket_estate_consolidation_to_sub100_2026_07_13.md` item 13 — a real, ground-truth-confirmed 108-day gap,
`2026-03-27`→`2026-07-12`, in `market-data-tick-defi-prd-central-element-323112` for `venue=MORPHO`). This is a SECOND,
independent real-VM confirmation of the fix chain (the "Status: RESOLVED and production-verified" section above verified
`dex_pools_handler.py` only) — extends coverage to a different handler, a different data path (Morpho via TheGraph
subgraph, `lending_indices` data_type), and a much longer (108-day, ~3.5-4hr) real backfill window rather than a 3-day
smoke window.

**Pre-launch verification, by content not just SHA-math**: confirmed via `git log` that the full fix chain (items 1-4:
`market-tick-data-service@d6846f1c`, `unified-trading-library@0aa284e8`, `unified-trading-library@391f8196`,
`market-tick-data-service@e3bbb2a3`) plus the `a5b07ff7` row-group-pushdown fix documented above were all already merged
to `live-defi-rollout`. Downloaded + unpacked the actual `mtds-code.tar.gz` / `unified-trading-library-code.tar.gz` from
`gs://deployment-scripts-central-element-323112/code/` and grepped the extracted `.py` files directly (not just each
tarball's `.manifest.json` `commit_sha`) — confirmed `_date_range_filters()`

- `filters=` pushdown present in `manifest_freshness.py`, and all 9 handlers (incl. `lending_indices_handler.py:341`)
  pass `date_range=(target_day, target_day)`. All 4 relevant tarball manifests (`mtds-code`,
  `unified-api-contracts-code`, `unified-trading-library-code`, `deployment-service-code`) matched local `HEAD` exactly
  (built ~4min before launch by the same concurrent session that shipped `a5b07ff7`) — no rebuild needed.

**Launch**:
`bash deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh --lending-protocols morpho 2026-03-27 2026-07-12`.
VM `mtds-lending-indices-20260715-002613` created 23:26:33Z, `RUNNING` 23:26:43Z (~32s). The launcher's own
`lc_verify_tarball_freshness` gate independently confirmed all 4 tarballs current.

**Result so far (interim — backfill still running at time of writing)**: `DEPLOYMENT_STARTED` 23:29:00.400Z, handler
initialized 23:29:00.959Z, two healthy `RESOURCE_SAMPLE`s (rss=693MiB/mem=10.7% at 23:29:01Z, rss=896MiB/mem=11.8% at
23:29:31Z) — sailed past the old ~20-90s kill window with zero crash signature. Days 2026-03-27 (554 records),
2026-03-28 (479 records), 2026-03-29 (340 records) each completed cleanly; day 4 (2026-03-30) in progress as of 23:37Z.
Independently ground-truth-verified (not just trusting the log) that day 1's real parquet object exists at
`gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2026-03-27/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=MORPHO/chain=ETHEREUM/instrument_type=lending/data_type=lending_indices/morpho_ETHEREUM_20260714_232900.parquet`.
Pace ~2min/day ⇒ 108 days ≈ 3.5-4hr total.

**Not yet a full close for this handler** — the backfill was still running at the time this entry was written; see
`bucket_estate_consolidation_to_sub100_2026_07_13.md` item 13 / its Progress Log for the plan-side tracking and any
later update on full completion (or a crash, if one occurs later in the 108-day window — if it crashes with the SAME
rc=137 signature despite the confirmed-fresh, content-verified tarballs, that would mean the fix chain is insufficient
for this handler specifically and needs a fresh finding appended here, not a duplicate doc). Combined with the
`dex_pools_handler.py` production verification above, this is the second of 9 DeFi handlers to get a real-VM
confirmation; the other 7 remain verified only via the shared-mechanism code fix + unit tests, not per-handler live
runs.
