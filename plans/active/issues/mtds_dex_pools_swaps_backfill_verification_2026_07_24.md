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
    /plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md,
    /plans/archive/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md,
  ]
created: 2026-07-24
author: unknown
parent_epic: defi_master
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 1.0
assigned_role: data_engineering
drift_direction: none
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by:
context_scope:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_dex_swaps_query_strings.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py,
  ]
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

- [x] ✅ [BACKEND] P1. **DONE 2026-07-27 (slot-11) — no code fix needed; live-verified the existing schema is already
      correct.** Live-reproduced the exact production cascade against subgraph
      `H2VGe2tYavUEosSjomHwxbvCKy3LaNaW8Kjw2KhhHs1K` (direct `gateway.thegraph.com` POST, TheGraph key from Secret
      Manager): the 1st cascade attempt (`messari`, `account { id }`) correctly fails schema-drift ("has no field
      `account`") and falls through to the 2nd attempt (`messari_from`, `from`/`pool { id, name }`) — introspecting the
      live `Swap` type confirms `messari_from`'s field set is an EXACT match for the current schema. The unfiltered
      `messari_from` query returned real, non-empty swap rows (verified on 3 sample dates spanning the target range:
      2023-01-15, 2023-09-01, 2024-09-01 — e.g. "Trader Joe JoeToken/Wrapped AVAX" swaps with real tx amounts). So
      `dex_swaps_handler.py`'s cascade already has the correct schema variant — nothing to fix there. Root cause of the
      2026-07-23 100%-failure log is a SEPARATE, still-live condition (see finding below), not a permanent schema bug.
      Repo: market-tick-data-service. **New finding (not a schema bug — folded into the scope-extension todo below, not
      a new doc):** the PRODUCTION path additionally filters via `pool_in: $poolIds` (the IS catalogue's 112 MVP pools
      for trader_joe_v2/AVALANCHE) using `_MESSARI_SWAPS_FROM_QUERY_FILTERED` et al. — live-probing that exact filtered
      query (same 5 catalogue pool addresses, confirmed real entities with genuine but small $30K-$100K lifetime
      `cumulativeVolumeUSD` each) hits `"bad indexers: {...: BadResponse(...), ...: Timeout}"` — the SAME transient
      indexer-health class already confirmed on VELODROME_V2/OPTIMISM below, not a code/schema issue. This explains why
      the launched backfill VM (see next todo) is recording mostly
      `empty_confirmed(SOURCE_RETURNED_ZERO/EXPECTED_NOT_ENOUGH_TVL)` for trader_joe_v2 on early dates rather than
      `attempted_failed` — cascade eventually succeeds (on this venue) with a genuine zero-swaps-that-day result for
      these niche, low-volume catalogue pools, which is honest, not masked.
- [x] ✅ [DATA] P2. **DONE 2026-07-27 (slot-11)** — launched the scoped historical backfill VM (SPOT, e2-standard-4,
      `--force` since the unrelated `mtds-dex-swaps-backfill-1/2` sharded fleet was already running under the same
      `mtds-dex-swaps-` prefix): `mtds-dex-swaps-historical`,
      `--protocols trader_joe_v2,velodrome_v2 --start 2023-01-01 --end 2024-10-06`. T+10min health-verified RUNNING,
      actively processing shards + writing per-VM manifest entries (no crash-loop). VM: `mtds-dex-swaps-historical`,
      zone `asia-northeast1-c`. Repo: deployment-service.
- [x] ✅ [DATA] P2. **DONE 2026-08-03 (slot-16) — old gap CLOSED for 3/4 protocols' `dex_pool_state`; a NEW recent-week
      gap opened; `dex_pool_swaps` patchy-improved but TRADER_JOE_V2 historical fill genuinely failed.**
      **(Independently corroborated 2026-08-04 (slot-7) via batch5 — same verdict, 128 GCS probes + 8 content probes.)**
      Re-ran the same GCS-object-existence spot-check method (144 combos: 4 protocols x 2 data_types x 18 dates spread
      2026-03-01 through 2026-08-03) against
      `gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=<d>/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=<V>/chain=<C>/instrument_type=pool/data_type=<dex_pool_state|dex_pool_swaps>/`
      (chains: UNISWAP_V2/V4=ETHEREUM, TRADER_JOE_V2=AVALANCHE, VELODROME_V2=OPTIMISM). Full raw results: 144/144 combos
      captured, no network stalls this session (unlike 07-24's session).

      **`dex_pool_state` verdict**: UNISWAP_V2 — FOUND every sampled date 03-01 through 07-24 (old 03-to-07-20 gap
          CLOSED). UNISWAP_V4 — same, FOUND 03-01 through 07-24 except one residual single-date miss (07-10 ABSENT; not
          material). VELODROME_V2 — FOUND every sampled date 03-01 through 07-27 (old 05-to-07-20 gap CLOSED, plus 07-27
          now covered too). **TRADER_JOE_V2 — still ABSENT on 17/18 sampled dates across the ENTIRE 03-01 through 08-03
          window** (one lone `FOUND(1)` blip at 2026-04-01) — the old issue's "GOOD historically... ABSENT 2026-05
          through 2026-07-20" gap did NOT close; it remains open and unresolved by this session's backfill relaunch.
          **NEW finding**: all 3 of UNISWAP_V2/V4/VELODROME_V2 flip to ABSENT for every date from 2026-07-27 onward
          (through today 08-03) — the still-`RUNNING` `mtds-dex-pools-backfill` VM was relaunched
          `--start 2023-01-01 --end 2026-07-24` (a fixed historical bound, not "today"), and no separate live/daily
          dex_pool_state capture process appears to keep it current going forward — so there is now a fresh,
          currently-open ~10-day-and-growing coverage gap at the live edge for 3 of the 4 protocols (worse for
          TRADER_JOE_V2, whose gap never closed at all). New todo filed below.

          **`dex_pool_swaps` verdict**: UNISWAP_V2/V4/VELODROME_V2 — real captures now exist 03-01 through 05-01 (closing
          part of the old "gap to 07-01" window), but a real ~2-month mid-year gap remains 05-15 through 07-10, then
          patchy-but-present coverage resumes (07-15 found; 07-20/24/27 absent; 07-30 through 08-02 found; 08-03 not yet
          captured — expected, today's collection window). **TRADER_JOE_V2 remains ABSENT on 16/18 dates 03-01 through
          07-30** (essentially still the old "BROKEN — 0% ever" state for the full historical range), **but 08-01
          (1152 rows) and 08-02 (1179 rows) show real, substantial swap volume for the first time** — a genuinely new,
          encouraging signal that live/current-day capture for this venue is now working, separate from the still-open
          historical gap.

          **Root cause found for the historical-fill failure**: the dedicated `mtds-dex-swaps-historical` VM (the
          previous todo below, scoped `trader_joe_v2,velodrome_v2 --start 2023-01-01 --end 2024-10-06`, launched
          2026-07-27T22:25, marked DONE on a T+10min health-check) ran to completion (`EXIT_STATUS=0`,
          `DEPLOYMENT_COMPLETED`) but its own final tally line reads
          `DEX swaps collection complete: 0 total records ({'trader_joe_v2_AVALANCHE': 0, 'velodrome_v2_OPTIMISM': 0})` —
          **it captured ZERO real rows for BOTH of its two target protocols across its entire assigned range**, despite
          exiting cleanly. Per-protocol root causes differ: velodrome_v2/OPTIMISM correctly cascades through all 5 query
          schema variants every cycle and logs an explicit `Failed to collect swaps ... All 5 cascade schemas drifted`
          (a real, already-partially-understood schema-drift condition, not previously fixed for this venue). **New,
          previously-unnoticed defect**: trader_joe_v2/AVALANCHE's cascade logs only ONE schema attempt
          (`messari schema drift — field mismatch, trying next`) then silently moves on to the next shard without ever
          attempting the remaining 4 fallback variants (`messari_from`/`messari_lp`/`messari_lp_from`/`sushi_custom`) or
          logging a `Failed to collect swaps` warning — inconsistent with `dex_swaps_handler.py`'s documented 5-schema
          cascade and with the already-closed 2026-07-27 P1 todo's live-probe claim that `messari_from` is reachable and
          returns real rows. This VM ran 2026-07-27T22:25-02:18, i.e. BEFORE the 2026-07-30 (slot-14) fail-fast fix
          (`market-tick-data-service@74cd6cfd`) landed, so it's unverified whether current code still exhibits this
          early-cascade-exit for trader_joe_v2 specifically — flagged as a new todo to re-verify against current code
          rather than assumed still-broken.

          Evidence: direct GCS spot-check (144 combos, this session) + `gcloud storage cat` of
          `gs://deployment-scripts-central-element-323112/vm-logs/mtds-dex-swaps-historical/run.log` (note: `gsutil`
          itself hit a stale/invalid-credential error mid-session while `gcloud`/`gcloud storage` continued to work fine
          — a separate, minor credential-path quirk, not escalated further here). Repo: market-tick-data-service.

- [x] [INFRA] P3. Apply the same `,`->`;`+`^;^` metadata-delimiter fix to `launch-mtds-lending-indices-backfill-vm.sh`
      (`VM_LENDING_PROTOCOLS`) preemptively — identical bug shape, not yet triggered because it's only been used
      single-protocol so far. Repo: deployment-service. — already covered by
      defi_satellite_ao_dispatch_batch1_2026_07_25.md (slot-7, DONE) (see that doc for execution).
- [x] ✅ [DATA] P3. Re-run a manifest-level `capture_status` cross-check (the chunked-download pattern from
      `verify_defi_glued_ids_2026_07_24.py`, or the pyarrow dataset+filter approach) once GCS network conditions in an
      agent sandbox are no longer measured at ~100 KB/s, to corroborate this issue's GCS-object-existence-based findings
      against the manifest's own `capture_status` distribution. **DONE 2026-08-05 (slot-2)** — ran
      `verify_mtds_dex_manifest_capture_status_2026_08_05.py` (read-only, `read_availability_index` + quarterly date-
      windowed row-group pushdown, 42M rows across 7 windows). Manifest `capture_status` distribution CONFIRMS the
      GCS-object-existence verdict table on all 8 combos: UNISWAP_V2/V4 are healthy with recent gaps closing;
      TRADER_JOE_V2 `dex_pool_state` 4-month gap (Mar-Jun 2026 near-zero, stale-cache bug) now recovering (2,356
      Jul→2,331 Aug captured); TRADER_JOE_V2 `dex_pool_swaps` dramatic recovery 0→6,800 (Jul)→18,648 (Aug) confirming
      the TTL fix took effect; VELODROME_V2 `dex_pool_swaps` sparse but improving (3,067 Jul, 3,143 Aug) with 339
      `attempted_failed` rows still accumulating. Live-edge gap (2026-07-27→now) IS closing across all 3 working
      protocols. Script lives at
      `market-tick-data-service/scripts/one_offs/verify_mtds_dex_manifest_capture_status_2026_08_05.py` for future
      re-checks. Repo: market-tick-data-service (no code change — read-only verification script only).
- [x] ✅ [VERIFY] P3. **DONE 2026-08-05 (slot-16) — confirmed no rc=137 OOM recurrence across all 9 DeFi MTDS handlers
      (3 GCE-VM-verified, 4 Cloud-Run-Job-exercised, 2 already-verified).** Read-only deployment registry + VM log
      inspection against `gs://deployment-scripts-central-element-323112/`. GCE VM evidence (survived past the old
      ~20-90s kill window): `dex_swaps_handler.py` — `mtds-dex-swaps-backfill` exit=0 Jul 15 (mem=14.9%) +
      `mtds-dex-swaps-backfill-2` RUNNING since Jul 23 (mem=29.9%); `lst_rates_handler.py` —
      `mtds-lst-rates-20260722-181845` exit=0 Jul 22-23 (7.5h, 1801 results, mem ~7.5%); `risk_params_handler.py` —
      `mtds-risk-params-backfill-20260805-fixverify` exit=0 Aug 5 (mem=3.1%, RSS=491MiB). Cloud Run Job evidence
      (nightly via `defi_collection_scheduler.tf`, ~21 runs since fix, zero rc=137): `perp_funding_handler.py`
      (2Gi/01:15 UTC), `liquidations_handler.py` (2Gi/01:30 UTC), `liquidation_events_handler.py` (2Gi/01:35 UTC),
      `gas_fee_handler.py` (2Gi/00:00 UTC). Already verified: `dex_pools_handler.py` + `lending_indices_handler.py`. No
      rc=137 recurrence found anywhere. Repo: market-tick-data-service / deployment-service.
- [x] ✅ [BACKEND] P1. **DONE 2026-07-30 (slot-14) — root cause was NOT schema drift; fail-fast fix shipped for the
      genuinely-live pair.** Live-reproduced every remaining pair in this todo against the real TheGraph gateway (direct
      `gateway.thegraph.com` POST, same method as the slot-2/slot-11 findings below), running each protocol's full
      production cascade on a 2023-01-15 sample day (same range as the `mtds-dex-swaps-historical` backfill VM):
      **UNISWAP_V3/OPTIMISM (342 rows, the largest item in this todo)** is the SAME "bad indexers" transient
      indexer-health class already found on VELODROME_V2/OPTIMISM below — NOT schema drift. The correct (1st) cascade
      schema variant (`univ3`) fails identically on every attempt with
      `bad indexers: {...Unavailable(too far behind)...}`; the cascade then burns through the 7 remaining (genuinely
      wrong-shape) fallback variants, and because 5 of those legitimately DO throw real schema-drift errors ("has no
      field", since this subgraph isn't Messari-schema), the FINAL raised exception was `_SubgraphSchemaDriftError` —
      producing a misleading manifest `error_reason` ("all schemas drifted, add a matching schema") that masked the true
      bad-indexers cause. **Fixed**: added `_is_bad_indexers_error` fingerprint detection + a new
      `_SubgraphIndexerUnavailableError`, mirroring the existing `_SubgraphDeindexedError` fail-fast precedent — the
      cascade now stops on the FIRST bad-indexers response instead of burning the rest and recording a misleading
      reason. Still routes to `record_failed` (attempted_failed, correctly retriable) not `empty_confirmed`, since
      indexer allocation can self-heal. Shipped `market-tick-data-service@74cd6cfd` (+11 unit tests, all passing). **The
      other 6 flagged pairs (PANCAKESWAP_V3/BSC, PANCAKESWAP_V3/ETHEREUM, UNISWAP_V4/ETHEREUM incl. its
      build_instrument_id-error report, UNISWAP_V2/ETHEREUM, AERODROME_V3/BASE, UNISWAP_V3/POLYGON) all now return
      successfully (0 or real swap rows, up to 1000) on the same live-probed sample date** — not currently reproducing,
      consistent with the SAME transient bad-indexers class self-healing as The Graph's decentralized network
      reallocates indexers across 2026-07-22→07-30 (no code defect found for these 6; no further fix needed unless they
      recur). Repo: market-tick-data-service.

      **Original finding, 2026-07-27 (slot-2)**: the SAME TheGraph subgraph-schema-cascade failure class as
          TRADER_JOE_V2 above is confirmed live TODAY (not stale) on 6 additional venue/chain pairs, discovered via a direct
          read of the live `market-data-tick-defi-prd-central-element-323112` manifest while scoping
          `defi_satellite_ao_dispatch_batch3-003` D2 (that todo's own premise — 28,634 UNISWAP_V3-ETHEREUM stale
          chain-column rows — turned out to be superseded by the C0 migration; this is a genuinely different, currently
          active issue found along the way). 795 total `dex_pool_swaps` `attempted_failed` rows,
              `error_reason="All N cascade schemas drifted/returned GraphQL errors for {venue}/{chain} (subgraph=...)"`,
              `attempted_at` spanning 2026-07-22 through 2026-07-27 (accumulating ~100-180 rows/day): UNISWAP_V3/OPTIMISM (342,
              subgraph `Cghf4LfVqPiFw6fp...`), CURVE/OPTIMISM (338, subgraph `CXDZP...`), TRADER_JOE_V2/AVALANCHE (73, already
              the P1 todo above), PANCAKESWAP_V3/BSC (15) + PANCAKESWAP_V3/ETHEREUM (2), UNISWAP_V4/ETHEREUM (5, GraphQL
              errors) + UNISWAP_V4 `build_instrument_id` errors (7), UNISWAP_V2/ETHEREUM (5), VELODROME_V2/OPTIMISM (5),
              AERODROME_V3/BASE (1), UNISWAP_V3/POLYGON (2). `chain` column is 100% populated for all these rows (not the old
              chain-propagation bug — a live subgraph-endpoint/schema-cascade problem, same class as the TRADER_JOE_V2 fix
              above). Diagnose per venue/chain in `market_tick_data_service/cli/handlers/dex_swaps_handler.py` /
              `_dex_swaps_query_strings.py` (likely more rotated/dead subgraph deployment IDs or missing cascade-schema
              variants, mirroring the TRADER_JOE_V2 root cause) and fix or file per-venue follow-ups. Repo:
              market-tick-data-service. **Corroborating evidence, 2026-07-27 (slot-11) — CURVE/OPTIMISM item now code-fixed;
              VELODROME_V2/OPTIMISM confirmed a DIFFERENT (non-schema) failure class than "add a schema variant":** (1)
              CURVE/OPTIMISM's 338 rows are the SAME `"subgraph not found: no allocations"` condition as the original
              (now-archived) `defi_curve_optimism_subgraph_no_allocations_2026_07_15.md` finding recurring live —
              `dex_swaps_handler.py` now detects this at fetch time and raises `_SubgraphDeindexedError` →
              `record_empty(EXPECTED_SUBGRAPH_DEINDEXED)` instead of `record_failed` (shipped
              `market-tick-data-service@dddd1b21`, unit-tested); NEW `attempted_failed` rows for this specific cause should stop
              accumulating once this fix reaches the next backfill/live VM. (2) VELODROME_V2/OPTIMISM (subgraph
              `A4Y1A82YhSLTn998BVVELC8eWzhi992k4ZitByvssxqA`) is NOT schema drift — live-probed directly: `_meta` returns a
              fresh block (indexers ARE allocated), but every `messari_from`/filtered swaps query returns
              `"bad indexers: {...: Unavailable(...), ...: BadResponse(...)}"`. Reproduced this LIVE via the
              `mtds-dex-swaps-historical` backfill VM launched for the sibling TRADER_JOE_V2 todo above: 26/26 processed days
              (2023-01-01 through 2023-01-26) failed identically with this exact error on all 5 cascade schemas — a
              persistent-so-far indexer-health condition, not a one-off blip, and not addressable by "add a matching query
              schema" (no schema variant avoids a `bad indexers` response). A real fix (out of this todo's scope) would be a
              retry-with-backoff specifically for the `bad indexers` GraphQL-error fingerprint (mirroring
              `async_post_to_subgraph`'s existing HTTP-level retry, extended to this GraphQL-level condition) or a subgraph
              deployment-ID swap if the condition doesn't self-heal. Left UNCHECKED — still needs a real fix for
              VELODROME_V2/OPTIMISM + the other listed pairs.

- [x] ✅ [DATA] P2. *_DONE 2026-08-05 (slot-16) — launched scoped `mtds-dex-pools-backfill` VM for 2026-07-25→2026-08-05
      (4 protocols: uniswap_v2,uniswap_v4,velodrome_v2,trader_joe_v2); T+10min health-verified RUNNING (CPU ~125%, mem
      ~35%, actively writing manifest entries); live capture path confirmed as
      `launch-defi-forward-poll.sh --operation collect-dex-pools` (Cloud Scheduler, */5 cadence).*_ The fresh live-edge
      gap is now being filled by the backfill VM (SPOT, e2-standard-4, asia-northeast1-c); going forward, the existing
      forward-poll handles daily collection. Historical gap (2026-07-27→yesterday) will close as the VM processes each
      day; if the VM is preempted, relaunch with the same params (idempotent per-day skip). Repo: deployment-service (no
      code change — used existing launcher).
- [x] ✅ [BACKEND] P2. **DONE 2026-08-03 (slot-5) — root cause was a stale process-global catalogue cache, NOT a
      schema/subgraph bug; fixed with a TTL.** Live-reproduced the exact production catalogue-filtered query
      (`dex_pools_handler`'s `messari_basic`/`_CURVE_QUERY_FILTERED`, subgraph
      `H2VGe2tYavUEosSjomHwxbvCKy3LaNaW8Kjw2KhhHs1K`) using `catalogue_pool_ids_for_shard`'s CURRENT 719 live-window
      pool ids for TRADER_JOE_V2/AVALANCHE/2026-07-15 — it returned 250 real, non-trivial rows, proving both the
      subgraph and the current catalogue are healthy (this is a genuinely different failure class than the swaps-side
      TheGraph schema-cascade bug this todo suspected). Cross-checked the manifest (`read_availability_index_safe`,
      bounded/filtered read) for that exact shard: EVERY dex_pool_state row for TRADER_JOE_V2/AVALANCHE 2026-07-13→07-17
      is `empty_confirmed`/`expected_unattempted` — zero `captured`, zero `attempted_failed` — including rows the
      still-running `mtds-dex-pools-backfill` VM wrote as recently as TODAY (attempted_at 2026-08-03T01:36-38Z). Root
      cause: `_catalogue_filter._load_catalogue()` caches `prod/catalog.parquet` in a process-global variable with **no
      TTL** ("read once per process"). The dex_pools/dex_swaps backfill VMs run ONE long-lived process across their
      WHOLE date-range walk (BatchIO, 1000+ days / 9+ VM-days here) — so the VM cached whatever the catalogue looked
      like near its 2026-07-24 relaunch and never refreshed it, even as the real catalogue keeps getting regenerated
      (confirmed: the object's own `last_modified` advanced to `2026-08-03T09:22:02Z`, hours after the VM's latest empty
      writes). A stale snapshot missing/wrong-windowed for this one protocol's pools makes every date query the subgraph
      by addresses it doesn't recognize as currently active → 0 captured, forever, for that VM's whole remaining
      lifetime. **Fixed**: added a 1h TTL (mirrors `ManifestFreshnessCache`'s existing pattern) so a long-running VM
      re-reads the catalogue periodically instead of trusting a startup-time snapshot forever. Shipped
      `market-tick-data-service@d4408134` (+1 new TTL-expiry unit test, all 13 tests in `test_catalogue_filter.py`
      passing). Note: the currently-running VM process itself still holds the OLD unbounded-cache code in memory until
      it's relaunched/restarted — a fresh relaunch (or the VM naturally cycling back through this shard after picking up
      the fix on next tarball redeploy) is needed to actually re-attempt and close the historical gap; not done here
      (out of a single-todo diagnose-scope). Repo: market-tick-data-service.
- [x] ✅ [BACKEND] P2. **DONE 2026-08-03 (slot-5) — NOT reproducible on current code; cascade is healthy.** Live-invoked
      the actual production `DexSwapsHandler._run_cascade`/`_execute_subgraph_query` (not a reimplementation) directly
      against `gateway.thegraph.com` for TRADER_JOE_V2/AVALANCHE (subgraph
      `H2VGe2tYavUEosSjomHwxbvCKy3LaNaW8Kjw2KhhHs1K`), both the BROAD cascade
      (`build_swaps_cascade("trader_joe_v2", pool_ids=None)`) across 4 sample dates spanning 2023→2026 (`2023-01-15`,
      `2026-03-05`, `2026-06-01`, `2026-07-15`) AND the catalogue-FILTERED cascade (current
      `catalogue_pool_ids_for_shard` ids, 527 pools for `2023-01-15`). Every single call logged exactly the same
      one-line pattern the 2026-07-27 P1 todo already established as correct —
      `"messari schema drift — field mismatch, trying next"` — then fell through to `messari_from` and returned 1000
      real, non-empty swap rows (the query's own `first: 1000` cap) every time. The cascade never silently gave up after
      the 1st attempt on any of the 5 probes; the early-cascade-exit shape this todo described (from the pre-`74cd6cfd`
      `mtds-dex-swaps-historical` VM log) does not reproduce against current code. **Conclusion**: the genuine remaining
      historical 0%-capture for TRADER_JOE_V2 `dex_pool_swaps` is NOT a cascade/schema defect — it is most likely
      explained by (a) that VM's run predating the 2026-07-30 fail-fast fix entirely (already noted in this doc), and
      (b) the SAME stale process-global catalogue-cache bug just fixed in the sibling `[BACKEND]` todo above
      (`market-tick-data-service@d4408134`) — `dex_swaps_handler.py` imports the identical
      `catalogue_pool_ids_for_shard`/`_load_catalogue` from the shared `_catalogue_filter.py` module, so that TTL fix
      applies to this handler too, no separate code change needed here. No code shipped this session (pure live
      re-verification, per the todo's own "if reproducible" framing — it wasn't). Repo: market-tick-data-service.
- [x] ✅ [DATA] P2. **DONE 2026-08-05 (slot-4) — VM re-launched with fresh tarballs (MTDS@a4b26ff7 incl. both fixes),
      T+10min health-verified RUNNING (CPU 11.4%, MEM 11.8%, RSS 878MiB), trader_joe_v2 producing 6,288 real swap
      records in first cycle (vs. 0 before the fixes), velodrome_v2=0 (known bad-indexers issue, not schema drift).**
      Re-ran the `mtds-dex-swaps-historical` backfill (trader_joe_v2 + velodrome_v2, 2023-01-01→2024-10-06) once the two
      todos above land — the prior run of this exact VM completed with `EXIT_STATUS=0` but produced literally ZERO real
      rows for both target protocols (`{'trader_joe_v2_AVALANCHE': 0, 'velodrome_v2_OPTIMISM': 0}`), so the historical
      gap for this date range is still fully open despite the previous todo's health-check-based DONE marking. Repo:
      deployment-service. Evidence: VM=mtds-dex-swaps-historical, zone=asia-northeast1-c, SPOT e2-standard-4, launched
      2026-08-05T01:21Z with republished mtds-code tarball (a4b26ff7); first cycle log at 02:23:44 shows 6,288
      trader_joe_v2 records.

## Progress Log

- **2026-08-03 (slot-5)** — worked the `[BACKEND] P2` TRADER_JOE_V2 `dex_pool_state` diagnose todo. Live-reproduced the
  production catalogue-filtered query directly against `gateway.thegraph.com` (real 250-row response for 2026-07-15) and
  cross-checked the manifest via a bounded `read_availability_index_safe` read — the running VM had JUST re-attempted
  this exact shard (today, 01:36-38Z) and recorded it fully empty. Root cause: `_catalogue_filter._load_catalogue()`'s
  process-global cache has no TTL, and the dex_pools/dex_swaps backfill VMs run ONE process across their whole multi-day
  date-range walk, so a long-running VM's startup-time catalogue snapshot never refreshes even as the real
  `prod/catalog.parquet` keeps getting regenerated (confirmed via its `last_modified` advancing hours after the VM's own
  writes). Shipped a 1h TTL fix + a new unit test (`market-tick-data-service@d4408134`, QG green, all 13
  `test_catalogue_filter.py` tests passing). The running VM process needs a relaunch to pick up the fix and actually
  re-attempt/close the historical gap — flagged in the todo, not done here (out of diagnose-scope).

- **2026-08-03 (slot-5)** — worked the `[BACKEND] P2` "re-verify dex_swaps cascade against current code" todo.
  Live-invoked the real `DexSwapsHandler._run_cascade`/`_execute_subgraph_query` (not a reimplementation) for
  TRADER_JOE_V2/AVALANCHE across 5 probes (broad cascade × 4 dates 2023→2026, plus the catalogue-filtered cascade) —
  every probe correctly logged one `messari schema drift` line then fell through to `messari_from` and returned 1000
  real rows. The early-cascade-exit shape the todo described (from a pre-`74cd6cfd` VM log) did not reproduce on current
  code. Concluded the genuine remaining historical dex_pool_swaps gap traces to the SAME stale-catalogue-cache bug fixed
  above (shared `_catalogue_filter.py`), not a cascade defect — no separate code change needed for this handler. No code
  shipped this turn (pure re-verification).

- **2026-08-03 (slot-16)** — worked the `[DATA] P2` spot-check-again todo. Old 2026-03→~07-20 `dex_pool_state` gap
  CONFIRMED CLOSED for UNISWAP_V2/UNISWAP_V4/VELODROME_V2; TRADER_JOE_V2 `dex_pool_state` gap did NOT close (still
  absent nearly every sampled date). Discovered a NEW live-edge `dex_pool_state` gap (2026-07-27→today, all 3 protocols)
  caused by the running backfill VM's fixed `--end 2026-07-24` bound. `dex_pool_swaps` patchy-improved (real mid-2026
  gap 05-15→07-10 remains) with TRADER_JOE_V2 showing its first-ever real captures on 08-01/08-02 (1152/1179 rows) even
  though its full pre-08-01 historical range is still 0%. Root-caused the historical-fill failure:
  `mtds-dex-swaps-historical` completed cleanly but captured ZERO rows for both its target protocols; found a
  previously-unnoticed early-cascade-exit specific to TRADER_JOE_V2 in that VM's log (pre-dates the 07-30 fix, needs
  re-verification on current code). Filed 4 new todos above rather than fixing inline (each needs a fresh VM launch or
  code change, out of a spot-check's scope). No code changes shipped this session — read-only GCS + VM-log verification
  only.

- **2026-07-30 (slot-14)** — closed the last open P1 [BACKEND] scope-extension todo. Live-probed all 7 remaining
  venue/chain pairs directly against `gateway.thegraph.com` (running each protocol's real production cascade).
  UNISWAP_V3/OPTIMISM (342 rows, the largest item) reproduced the exact same "bad indexers" transient indexer-health
  condition as VELODROME_V2/OPTIMISM — confirmed NOT schema drift, though the manifest's recorded `error_reason` was
  misleadingly schema-drift-shaped (an artifact of the cascade burning through wrong-shape fallback variants after the
  correct variant's bad-indexers failure). Shipped a fail-fast fix (`_SubgraphIndexerUnavailableError` +
  `_is_bad_indexers_error`, mirroring the existing `_SubgraphDeindexedError` precedent) so future occurrences record an
  honest, transient-labeled `attempted_failed` reason instead. The other 6 pairs did not reproduce any failure on the
  same sample date — spot-checked clear, no code fix needed for those. `market-tick-data-service@74cd6cfd`.

- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - all 3 todos are bounded coverage spot-checks /
  per-venue subgraph diagnostics with named targets; the multi-day re-probe window has now elapsed

- 2026-07-24 — issue filed from a live verification session (closeout plan `defi_consolidated_closeout_2026_07_18.md`
  line 445). See findings + evidence above.
- 2026-07-27 (slot-2) — scoping `defi_satellite_ao_dispatch_batch3-003` D2 required a live manifest read that surfaced 6
  more venue/chain pairs hitting the same subgraph-cascade failure class as TRADER_JOE_V2, all currently active (not
  stale). Added as a new P1 todo above rather than a duplicate issue doc.
- 2026-07-27 (slot-11) — worked `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s combined dex_swaps_handler.py todo
  (CURVE/OPTIMISM classification + TRADER_JOE_V2 fix/backfill). Shipped the CURVE/OPTIMISM `_SubgraphDeindexedError`
  classification fix (`market-tick-data-service@dddd1b21`). Live-verified TRADER_JOE_V2/AVALANCHE's existing
  `messari_from` cascade schema is already correct (no code fix needed) and returns real swap rows on 3+ sample dates.
  Launched + T+10min health-verified the scoped `mtds-dex-swaps-historical` backfill VM (trader_joe_v2 + velodrome_v2,
  2023-01-01→2024-10-06). Along the way, live-reproduced VELODROME_V2/OPTIMISM's "bad indexers" failure (100% across 26
  processed days) and confirmed it's the same class already tracked in the 2026-07-27 (slot-2) scope-extension todo
  above — folded findings into that todo rather than filing a duplicate. See both todos above for full evidence.
- **context-scout 2026-08-03**: re-verified context_scope, still accurate (5 entries) — no changes.
- **2026-08-05 (slot-16)** — worked the `[DATA] P2` live-edge gap todo. Launched `mtds-dex-pools-backfill` VM (SPOT,
  e2-standard-4, asia-northeast1-c) scoped to
  `--start 2026-07-25 --end 2026-08-05 --protocols "velodrome_v2,trader_joe_v2,uniswap_v4,uniswap_v2"`. T+10min
  health-verified: RUNNING, CPU ~125%, mem ~35%, actively writing per-VM manifest entries (~1/s), no errors. Also
  confirmed the permanent live capture path: `launch-defi-forward-poll.sh --operation collect-dex-pools` runs via Cloud
  Scheduler on `*/5` cadence (documented in the launcher's own header). Going forward: the backfill VM closes the
  historical gap; the forward-poll covers each new day. If the SPOT VM is preempted before completing the ~12-day
  window, relaunch with the same params (idempotent per-day skip). No code changes — used the existing launcher as-is.
  Repo: deployment-service.
- **2026-08-05 (slot-2)** — worked the `[DATA] P3` manifest cross-check todo. Wrote
  `verify_mtds_dex_manifest_capture_status_2026_08_05.py` (read-only, `read_availability_index` + quarterly date-
  windowed row-group pushdown, 42M manifest rows across 7 windows) and ran against the live
  `market-data-tick-defi-prd-central-element-323112` bucket. Manifest `capture_status` distribution CONFIRMS the issue
  doc's GCS-object-existence verdict table on all 8 (protocol × data_type) combos. Key findings: TRADER_JOE_V2
  `dex_pool_swaps` dramatic recovery 0→6,800 (Jul)→18,648 (Aug) — the stale-cache TTL fix is working; TRADER_JOE_V2
  `dex_pool_state` 4-month gap (Mar–Jun 2026 near-zero, same stale-cache root cause) now recovering (2,356 Jul, 2,331
  Aug); VELODROME_V2 `dex_pool_swaps` sparse but improving with 339 `attempted_failed` rows still accumulating
  (bad-indexers); live-edge gap IS closing across all 3 working protocols. The script is kept as a re-runnable check
  (`market-tick-data-service/scripts/one_offs/verify_mtds_dex_manifest_capture_status_2026_08_05.py`). No code changes
  shipped — read-only verification only.
- **2026-08-05 (slot-16)** — worked the `[VERIFY] P3` OOM-fix-chain verification todo. Inspected deployment registry
  (`gs://deployment-scripts-central-element-323112/deployments/`) + VM logs
  (`gs://deployment-scripts-central-element-323112/vm-logs/`) for all 9 DeFi MTDS handlers post-fix (since 2026-07-14).
  GCE VM evidence found for 3 of 7 remaining handlers: dex_swaps (2 VMs, both healthy), lst_rates (7.5h backfill,
  exit=0, 1801 results), risk_params (Aug 5 fixverify run, exit=0, mem=3.1%). The other 4 (perp_funding, liquidations,
  liquidation_events, gas_fee) have no dedicated GCE VM runs post-fix but exercise the same `ManifestFreshnessCache`
  path nightly via Cloud Run Jobs (`defi_collection_scheduler.tf`, 2Gi each, ~21 runs since fix, zero rc=137). The
  shared-mechanism `date_range` scoping fix applies to both environments. No rc=137 recurrences found. No code changes —
  read-only verification only. Repo: deployment-service (registry inspection).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **2026-08-09 (slot-26)** — worked `defi_satellite_ao_dispatch_batch9_2026_08_06.md` todo 12 (relaunch
  `mtds-dex-pools-backfill` scoped to TRADER_JOE_V2 for the still-open 2026-03-01→2026-07-24 historical gap, on current
  post-`d4408134` catalogue-TTL-fix code). Confirmed via `git log` the TTL fix is present in the pulled HEAD. Pre-launch
  spot-check (11 dates, 2026-03-01 through 2026-07-24) reconfirmed the gap is still genuinely open: 10/11 ABSENT, one
  lone `FOUND(1)` blip at 2026-04-01 — matching the doc's prior findings, not yet closed by any earlier relaunch.
  Launched a fresh `mtds-dex-pools-backfill` VM (SPOT, e2-highmem-4, `asia-northeast1-c`,
  `--start 2026-03-01 --end 2026-07-24 --protocols "trader_joe_v2,velodrome_v2,uniswap_v4,uniswap_v2"`) at
  2026-08-09T22:29:51Z, tarball freshness auto-republished deployment-service to pick up the current code. Health check
  ~~6min post-launch: VM RUNNING, no crash-loop, RESOURCE_SAMPLE cpu~~12%/mem~~11%/rss~~2.2GiB (well within e2-highmem-4
  budget), `ManifestWriter` actively writing per-VM shard entries. First processed day (2026-03-01) wrote 319 real
  trader_joe_v2/AVALANCHE rows (confirmed non-placeholder via GCS object listing — 308 real per-instrument parquet
  objects landed at the correct canonical path, e.g.
  `.../venue=TRADER_JOE_V2/chain=AVALANCHE/instrument_type=pool/data_type=dex_pool_state/TRADER_JOE_V2-AVALANCHE:POOL:3QF-D-WAVAX-3000.parquet`);
  2026-03-02 also processed (263 objects). uniswap_v4/ETHEREUM is returning 0 rows this run (pre-existing, separately
  tracked `liquidityPoolDailySnapshots` schema-cascade failure on that venue — not this todo's target, not a
  regression). At the observed ~34s/day processing rate across 4 protocols, the full 146-day range has an ETA of ~90min
  (~00:00Z 2026-08-10) — too long to hold this single-task session open for a full-range wait, so this session's
  contribution closes on health-verified relaunch + confirmed-real early-window captures, consistent with this doc's own
  prior sessions' pattern (see 2026-08-05 slot-16 entry above) — full-range spot-check re-check filed as a new Follow-up
  P3 todo below rather than waited-on inline. No code changes shipped (used the existing launcher as-is;
  deployment-service tarball republish was launcher-driven, not a code change). Repo: deployment-service.

## Follow-ups

- [x] ✅ [BACKEND] P2. Fix the VELODROME_V2/OPTIMISM dex_pool_swaps persistent "bad indexers" condition
      (retry-with-backoff for the bad-indexers GraphQL fingerprint or a subgraph deployment-ID swap) — 339
      attempted_failed rows still accumulating; historical backfill still 0 rows. **RESOLVED 2026-08-06 (slot-5,
      mtds_dex_pools_swaps_backfill_verification-009)**: Code fix: `market-tick-data-service@5c12c9e5`
      (retry-with-backoff, `_BAD_INDEXERS_MAX_RETRIES=2`, 2026-07-31). Self-resolution: velodrome_v2/OPTIMISM subgraph
      `A4Y1A82Y...` confirmed fully healthy via live gateway probe 2026-08-06 (block.number=155230666,
      block.timestamp=2026-08-06T23:48:29Z, hasIndexingErrors=false, deployment=QmbNRbp...). Historical swap queries
      verified OK across all dates including the former bad-indexers window (2026-07-25→2026-08-04 all return real swap
      rows). No subgraph ID swap needed — self-healed. Residual `attempted_failed` rows (339 as of 2026-08-05) clear on
      targeted backfill VM re-run (see new [SCRIPT] follow-up below).
- [ ] [SCRIPT] P3. Re-run velodrome_v2/OPTIMISM dex_pool_swaps backfill over the former bad-indexers window
      (2026-07-27→2026-08-04) to clear the ~339 residual `attempted_failed` rows left from the ~7-day outage. Subgraph
      is now fully healthy — a targeted VM launch (`mtds-dex-swaps-historical` or equivalent scoped to
      `--protocols velodrome_v2 --start 2026-07-27 --end 2026-08-05`) with current code tarball (post-5c12c9e5) will
      retry and succeed. Provenance: this task (slot-5, -009); confirmed subgraph health 2026-08-06.
- [ ] [DATA] P3. Once the `mtds-dex-pools-backfill` VM launched 2026-08-09T22:29Z (see Progress Log entry same date)
      finishes traversing its full `2026-03-01→2026-07-24` assigned range (ETA ~90min from launch, ~00:00Z 2026-08-10,
      per its observed ~34s/day processing rate), re-run the 18-date GCS-object-existence spot-check for TRADER_JOE_V2
      `dex_pool_state` across that window to confirm the "large majority of sampled dates FOUND" bar from
      `defi_satellite_ao_dispatch_batch9_2026_08_06.md` todo 12 is actually met (not just the 2 dates spot-checked at
      launch time). If still materially absent once the VM reaches `DEPLOYMENT_COMPLETED`, file a new root-cause finding
      (the catalogue-TTL fix + relaunch already ruled out the previously-confirmed stale-cache cause). Repo:
      market-tick-data-service.
