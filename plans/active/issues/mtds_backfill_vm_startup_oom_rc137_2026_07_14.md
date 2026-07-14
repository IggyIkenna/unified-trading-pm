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

- [ ] [BACKEND] P0. Confirm/refute `_register_all_catalog_readers()` (market-tick-data-service
      `engine/orchestrator/__init__.py:684`) as the OOM site for the rc=137 backfill-VM crash — add RSS instrumentation
      immediately around the call, launch one disposable VM (e.g. re-run
      `launch-mtds-perp-funding-backfill-vm.sh --start 2026-07-13 --end 2026-07-14`, smallest possible window), capture
      the memory delta. Repo: `market-tick-data-service`.
- [ ] [BACKEND] P0. If confirmed: scope catalog-reader registration to the job's actual `asset_groups` (not
      unconditionally all four) in `_register_all_catalog_readers()` / its `process_ticks()` call site. Add a regression
      test asserting only the requested asset_group's reader(s) register. Repo: `market-tick-data-service`.
- [x] [SCRIPT] P1. Fleet-wide check: grep the deployment registry archive
      (`gs://deployment-scripts-central-element-323112/deployments/archive/2026-07-1{2,3,4}/*.json`) for `exit_code=137`
      `DEPLOYMENT_FAILED` entries across ALL asset_groups (not just DeFi) to gauge blast radius since `f8cab3f0` landed
      (2026-07-12). Repo: `deployment-service`. — ✅ DONE 2026-07-14, see "Fleet-wide blast-radius check" below.
- [ ] [SCRIPT] P2. Once the fix lands, relaunch `mtds-perp-funding-backfill` and `mtds-dex-swaps-backfill` (same command
      as this session used) and verify past the first `RESOURCE_SAMPLE` without a crash before resuming
      `mvp_backfill_defi_onchain_v10-002`'s G2 verification. Repo: `deployment-service`.

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
