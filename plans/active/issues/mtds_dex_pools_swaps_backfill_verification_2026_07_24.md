---
doc_type: issue
title:
  mtds-dex-pools/dex-swaps 2026-07-14 backfill verification — dex_pool_state has a real recent gap (VM externally
  killed, not OOM); TRADER_JOE_V2/VELODROME_V2 dex_pool_swaps are genuinely near-zero
summary: >-
  Verified defi_consolidated_closeout_2026_07_18.md's "verify the mtds-dex-pools/dex-swaps backfill VMs" todo
  (uniswap_v2/v4, trader_joe_v2, velodrome_v2, launched 2026-07-14 for 2023-01-01->today). Ground-truth GCS object
  probing (160 venue x data_type x sample-date combos) + real VM run.log/deployment-registry evidence shows the OOM
  crash-loop the todo flagged as a risk did NOT recur post-fix (a5b07ff7e) -- the mtds-dex-pools-backfill VM ran healthy
  for 3 days (2026-07-15->07-18, 1.55M+ manifest shard entries, mem 30-40%) until it was TERMINATED by an explicit
  `v1.compute.instances.delete` API call at 2026-07-18T16:15:52Z (not OOM, not SPOT preemption -- confirmed via audit
  log, no compute.instances.preempted event exists) while mid-run and healthy. This left dex_pool_state with a real,
  patchy but material gap across roughly 2026-03 through today for all 4 protocols. Separately, dex_pool_swaps for
  TRADER_JOE_V2 is 0% captured across the ENTIRE 2023-2026 range (persistent TheGraph subgraph query-schema-cascade
  failure, a code/adapter bug unrelated to the OOM issue) and VELODROME_V2 dex_pool_swaps is only 2/20 sampled dates
  present (capability works when it runs, just was never comprehensively backfilled). Also found + fixed a real launcher
  bug along the way: --protocols comma-separated lists broke gcloud's --metadata parsing (never previously exercised
  with >1 protocol). Relaunched a scoped mtds-dex-pools-backfill run (4 protocols, 2023-01-01->today) as part of this
  verification; dex_pool_swaps for trader_joe_v2/velodrome_v2 needs a code fix (schema cascade) + a dedicated historical
  backfill before the currently-running sharded fleet's 2024-10-07 start date.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags:
  [defi, dex-pools, dex-swaps, backfill, manifest, verification, thegraph, uniswap, trader-joe, velodrome, vm-launcher]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md,
    /plans/active/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md,
  ]
created: 2026-07-24
parent_epic: defi_master
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 1.0
assigned_role: data_engineering
drift_direction: none
assigned_vm: NA
execution_scope: local-only
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py,
    deployment-service/scripts/vm/launch-mtds-dex-pools-backfill-vm.sh,
    deployment-service/scripts/vm/launch-mtds-dex-swaps-backfill-vm.sh,
  ]
depends_on: []
---

# mtds-dex-pools/dex-swaps 2026-07-14 backfill verification (2026-07-24)

## Verdict table

| Protocol      | data_type      | Verdict                            | Evidence                                                                                                                                                                                                                |
| ------------- | -------------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UNISWAP_V2    | dex_pool_state | GOOD, recent gap                   | Real captures 2023-01 through 2026-01/2026-07-01 (scattered sample gaps); ABSENT 2026-03 through 2026-07-20 (patchy, not one clean cutoff)                                                                              |
| UNISWAP_V2    | dex_pool_swaps | GOOD, recent gap                   | Real captures spanning 2023-2026, incl. 2026-07-15 (currently-running fleet); gap 2026-03 to 2026-07-01                                                                                                                 |
| UNISWAP_V4    | dex_pool_state | PARTIAL, expected pre-2025 absence | Correctly absent before 2025-01-31 launch date; captured 2025-03 to 2026-01; ABSENT 2026-03 to 2026-07-20 (only ~1 row/day even when present -- thin)                                                                   |
| UNISWAP_V4    | dex_pool_swaps | PARTIAL, expected pre-2025 absence | Same window as pool_state, plus 2026-07-15 (currently-running fleet)                                                                                                                                                    |
| TRADER_JOE_V2 | dex_pool_state | GOOD historically, recent gap      | Real substantive data (392 rows/day, real USD volume figures) 2023-01 through 2026-03 via a 2026-07-19 targeted backfill (`_migrated_` filenames, NOT from the 07-14/07-15 launches); ABSENT 2026-05 through 2026-07-20 |
| TRADER_JOE_V2 | dex_pool_swaps | **BROKEN — 0% ever**               | 0/20 sampled dates across the FULL 2023-2026 range. Root cause confirmed in VM run.log: persistent TheGraph subgraph query-schema-cascade failure, NOT an OOM/infra issue                                               |
| VELODROME_V2  | dex_pool_state | GOOD historically, recent gap      | Real captures 2023-09 through 2026-03 (also via the 07-19 targeted backfill); ABSENT 2026-05 through 2026-07-20; also absent 2023-01/04/06                                                                              |
| VELODROME_V2  | dex_pool_swaps | **SPARSE — near-zero**             | Only 2/20 sampled dates found (2026-01-15, 2026-07-15). Capability genuinely works (real swap tx hashes/pool names confirmed) but was never comprehensively backfilled                                                  |

Sampling: 20 dates spread 2023-01-15 through 2026-07-20, both data_types, all 4 protocols = 160 combos, probed via
direct GCS `list_blobs(prefix=...)` existence checks (not the manifest — see "Why not the manifest" below), each `FOUND`
cross-checked by downloading + `pq.read_table`-ing at least one real object per (protocol, data_type) to confirm
non-trivial, genuinely-dated row content (not empty placeholders, not the Solana fake-history back-dated-timestamp
signature — every sampled file's own `timestamp` column matches its `day=` partition).

## Why not the manifest (`_index/availability_index.parquet`)

The closeout plan's own todo pointed at manifest `capture_status=captured` spot-checks via the chunked byte-range
download pattern in `verify_defi_glued_ids_2026_07_24.py`. Both that exact pattern AND a pyarrow
`GcsFileSystem`/dataset-with-filter-pushdown alternative were attempted live this session and both failed/stalled:

1. The chunked whole-file download hit the documented "concurrent-writer 404" gotcha directly — the pinned generation
   was invalidated mid-transfer (~25 min in, 4/24 chunks done) by a live consolidator write (confirmed: `gsutil stat`
   mid-session showed `consolidator_content_write_at` from minutes earlier, matching the currently- running dex-swaps
   sharded fleet actively writing).
2. Raw network throughput in this session's sandbox was measured at ~55-110 KB/s for GCS reads (a 24.3 MB run.log took
   ~5 min; a 1 MB `gsutil cat -r` range took 18s) — a full ~940 MB manifest download would have taken 2.5-4.7 hours
   regardless of chunking (bandwidth-bound, not request-count-bound). `pyarrow.fs.GcsFileSystem` stalled completely
   (100s+ with zero response even for a single `get_file_info` HEAD call).

Given this, the verification pivoted to **direct GCS object existence + content probing** (lighter-weight `list_blobs`
LIST calls, not full-object GETs) plus **VM run.log / deployment-registry evidence**, which is at least as strong ground
truth as the manifest for "did real historical rows get produced" and was actually obtainable in this session's network
conditions. A manifest-level `capture_status` cross-check is still worth doing once network conditions improve — flagged
as a follow-up below, not blocking this issue's findings.

## What actually happened to the 2026-07-14-launched VMs (not OOM-crash-looping by the time I checked)

Per `mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`, the OOM fix (`unified-trading-library@a5b07ff7e`, row-group
predicate pushdown, 14.86 GB -> 742 MB peak) was production-verified 2026-07-14 on a 3-day uniswap_v2 dex_pools smoke
window and a 108-day Morpho lending_indices run — but NOT on the original full-range 4-protocol launch this todo asked
about. Tracing the actual GCE audit log + deployment registry + downloaded `run.log` objects:

- **`mtds-dex-pools-backfill`** (dex_pool_state): the 2026-07-14 launch did hit the OOM crash-loop (multiple
  insert/delete cycles that day, matching the OOM issue doc exactly). It was relaunched 2026-07-15T12:19:55Z
  (deployment_id `48726c1e`, `--start-date 2020-01-01 --end-date 2026-07-15`, full default 19-protocol list incl. our 4)
  and ran **healthy for 3 days** — 1,558,509+ per-VM manifest shard entries, RESOURCE_SAMPLE mem consistently 30-40%, no
  `Killed`/`rc=137`/Traceback anywhere in the 152,008-line log. It did NOT crash. It was **terminated by an explicit
  `v1.compute.instances.delete` API call at 2026-07-18T16:15:52Z** (confirmed via
  `gcloud logging read 'protoPayload.resourceName:"mtds-dex-pools-backfill"'`) — 27 seconds after its last healthy log
  line, with the deployment registry entry left permanently `status=running, exit_code=null, completed_at=null` (i.e. it
  never got to mark itself complete — this was an external kill, not a graceful self-shutdown-on-completion, and NOT a
  SPOT preemption either: no `compute.instances.preempted` event exists in the audit log for this VM, and net/cpu/mem
  were all healthy in the deployment registry's own metrics window right up to the cutoff). Most likely explanation:
  another agent/process deliberately stopped it (the closeout plan's own Progress Log shows heavy concurrent
  dex_pools/fake-history investigation activity 2026-07-21 through 2026-07-23) — not confirmed, not investigated further
  here (out of this issue's scope; flagging as context, not blaming).
- **`mtds-dex-swaps-backfill`** (dex_pool_swaps, singular non-sharded VM): relaunched 2026-07-23T04:58:50Z
  (`--start-date 2023-01-01 --end-date 2026-07-22` — exactly the todo's claimed range), ran healthy for ~2h (13
  "collection complete" cycles, no crashes, uniswap_v2 non-zero every cycle), then was **also explicitly deleted**
  (`v1.compute.instances.delete` at 2026-07-23T06:59:12Z / 07:01:25Z) and immediately replaced by a **3-way sharded
  fleet** (`mtds-dex-swaps-backfill-1/2/3`, launched 07:03:09Z, date-range-sharded: 2024-10-07->2025-05-11,
  2025-05-12->2025-12-14, 2025-12-15->2026-07-21) — this reads as a deliberate optimization (parallelize a 3.5-year
  serial backfill), not a failure, and **this fleet is STILL RUNNING as of this verification** (confirmed via
  `gcloud compute instances list`). Good news: it directly explains why UNISWAP_V2/V4 dex_pool_swaps show captures at
  2026-07-15 in the object probe — it's actively filling recent dates right now.

**Conclusion on the todo's core question**: the OOM crash-loop bug itself is confirmed NOT the cause of any remaining
gap — every VM that ran post-fix ran cleanly until something else (an external delete, not a crash) stopped it. The real
remaining gaps are (a) a real-but-patchy dex_pool_state coverage hole for the last ~4-5 months across all 4 protocols
(nobody has been running a pool_state backfill since the 07-18 kill), and (b) two genuinely-unresolved dex_pool_swaps
capture gaps for TRADER_JOE_V2 (code bug) and VELODROME_V2 (never comprehensively backfilled).

## Root cause: TRADER_JOE_V2 dex_pool_swaps — TheGraph subgraph schema cascade failure

From the 2026-07-23 `mtds-dex-swaps-backfill` run.log, every single cycle (13/13 observed):

```
trader_joe_v2/AVALANCHE: messari schema failed, trying next fallback
trader_joe_v2/AVALANCHE: messari_from schema failed, trying next fallback
trader_joe_v2/AVALANCHE: messari_lp schema failed, trying next fallback
trader_joe_v2/AVALANCHE: messari_lp_from schema failed, trying next fallback
trader_joe_v2/AVALANCHE: sushi_custom schema failed, trying next fallback
Failed to collect swaps trader_joe_v2/AVALANCHE: All 5 cascade schemas returned GraphQL errors for
  trader_joe_v2/AVALANCHE (subgraph=H2VGe2tYavUEosSjomHwxbvCKy3LaNaW8Kjw2KhhHs1K). Diagnose: add a
  matching query schema or update the existing one.
```

Underlying GraphQL error: `bad indexers: {...: Unavailable(too far behind), ...: BadResponse(400)}`. This is a
`market_tick_data_service/cli/handlers/_dex_swaps_query_strings.py` schema-cascade gap (or a genuinely dead/rotated
subgraph deployment ID) — a code/adapter issue, completely independent of the OOM fix. No amount of relaunching the
backfill VM will fix this without a code change.

## Launcher bug found + fixed this session (blocking a scoped relaunch)

`deployment-service/scripts/vm/launch-mtds-dex-pools-backfill-vm.sh` and its sibling
`launch-mtds-dex-swaps-backfill-vm.sh` build `--metadata=` by joining `KEY=VALUE` pairs with `,` — but `--protocols`
accepts a comma-separated list (e.g. `"velodrome_v2,trader_joe_v2,uniswap_v4,uniswap_v2"`), and gcloud's default
`--metadata` delimiter IS `,`. Passing a comma-bearing `--protocols` value therefore broke
`gcloud compute instances create` outright:
`ERROR: (gcloud.compute.instances.create) argument --metadata: Bad syntax for dict arg: [trader_joe_v2]`. This path was
apparently never exercised before with >1 protocol (the closeout plan's "wired + smoke-tested 2026-07-14" claim for
these 4 protocols likely used single-protocol launches or the full default list). **Fixed**: both launchers now join
metadata pairs with `;` and pass `--metadata="^;^${METADATA}"` (gcloud's alternate-delimiter syntax), which is
comma-safe. `launch-mtds-lending-indices-backfill-vm.sh` has the **identical** pattern
(`VM_LENDING_PROTOCOLS=${LENDING_PROTOCOLS}` joined with the same `,`-delimited METADATA) and has the same latent bug —
not yet fixed (out of this issue's immediate scope; it has only ever been exercised single-protocol so far, e.g.
`--lending-protocols morpho`), filed as a todo below.

## Action taken this session (read-only verification + one bounded, scoped relaunch)

Relaunched `mtds-dex-pools-backfill` (dex_pool_state) scoped to just the 4 target protocols across the full original
range, using the now-fixed launcher:
`--start 2023-01-01 --end 2026-07-24 --protocols "velodrome_v2,trader_joe_v2,uniswap_v4,uniswap_v2"`. SPOT, idempotent
(skip-if-already-captured per-day), scoped narrower than the original 19-protocol default so it should complete faster
and be less exposed to another multi-day external interruption. T+10min health verified per the "no fire-and-forget"
rule (see Progress Log entry below for the observed outcome).

## Todos

- [ ] [BACKEND] P1. Fix the TRADER_JOE_V2 TheGraph subgraph schema-cascade failure for `dex_pool_swaps`
      (`market_tick_data_service/cli/handlers/dex_swaps_handler.py` / `_dex_swaps_query_strings.py`,
      subgraph=`H2VGe2tYavUEosSjomHwxbvCKy3LaNaW8Kjw2KhhHs1K`) — confirmed 0% capture across the entire sampled
      2023-2026 range; "bad indexers ... Unavailable(too far behind) / BadResponse(400)" on ALL 5 cascade schemas. May
      need a new/updated query schema variant or a subgraph deployment-ID swap. Repo: market-tick-data-service.
- [ ] [DATA] P2. Once the TRADER_JOE_V2 code fix lands, launch a dedicated `dex_pool_swaps` historical backfill for
      TRADER_JOE_V2 + VELODROME_V2 covering **2023-01-01 through 2024-10-06** — the range NOT covered by the
      currently-running `mtds-dex-swaps-backfill-1/2/3` sharded fleet (which starts at 2024-10-07). Repo:
      deployment-service.
- [ ] [DATA] P2. Spot-check `dex_pool_state`/`dex_pool_swaps` coverage again for all 4 protocols across 2026-03 through
      today once the relaunched `mtds-dex-pools-backfill` VM (this session) + the running `mtds-dex-swaps-backfill-*`
      fleet finish, to confirm the recent-months gap identified in this issue actually closed. Repo:
      market-tick-data-service.
- [x] [INFRA] P3. Apply the same `,`->`;`+`^;^` metadata-delimiter fix to `launch-mtds-lending-indices-backfill-vm.sh`
      (`VM_LENDING_PROTOCOLS`) preemptively — identical bug shape, not yet triggered because it's only been used
      single-protocol so far. Repo: deployment-service. — already covered by
      defi_satellite_ao_dispatch_batch1_2026_07_25.md (slot-7, DONE) (see that doc for execution).
- [ ] [DATA] P3. Re-run a manifest-level `capture_status` cross-check (the chunked-download pattern from
      `verify_defi_glued_ids_2026_07_24.py`, or the pyarrow dataset+filter approach) once GCS network conditions in an
      agent sandbox are no longer measured at ~100 KB/s, to corroborate this issue's GCS-object-existence-based findings
      against the manifest's own `capture_status` distribution. Not blocking — object-level evidence here is already
      ground truth for "did real rows land."

## Progress Log

- 2026-07-24 — issue filed from a live verification session (closeout plan `defi_consolidated_closeout_2026_07_18.md`
  line 445). See findings + evidence above.
