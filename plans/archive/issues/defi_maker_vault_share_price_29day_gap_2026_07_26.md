---
doc_type: issue
title:
  vault_share_price manifest has a handler-wide, root-caused 29-day gap (2026-06-22..2026-07-20) -- MAKER + 4 other
  protocols, backfill still open
summary: >-
  Found while verifying defi_satellite_ao_dispatch_batch2_2026_07_26.md's "90-day lst-rates backfill for
  ANKR/STADER/STAKEWISE/SWELL/MANTLE/MAKER" todo. MAKER is NOT actually part of lst_rates_handler.py -- it is registered
  under vault_share_price_handler.py (data_type=vault_share_price), a different handler entirely. The 5 genuine LST-rate
  venues (ANKR/STADER/STAKEWISE/SWELL/MANTLE) show 90/90 days captured already (no backfill needed -- the daily cron
  organically covers the window). Originally filed as a MAKER-only gap; root-caused 2026-07-28 as HANDLER-WIDE (all 5
  vault_share_price protocols -- ETHENA/FRAX/MAKER/MORPHOVAULTS/YEARN_V3 -- show the identical missing 2026-06-22
  through 2026-07-20 window). Cause: collect-vault-share-price had no Cloud Scheduler entry until
  deployment-service@600d31c (2026-07-22); a post-fix retroactive backfill covered history only through 2026-06-21,
  leaving this exact crack before the new cron's 2026-07-21 start. Underlying cause already fixed + healthy; only the
  29-day backfill (now scoped to all 5 protocols) remains open.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, mtds, lst-rates, vault-share-price, maker, manifest-gap]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/archive/issues/defi_five_never_captured_venues_fix_2026_07_22.md,
  ]
created: 2026-07-26
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-07-26 (slot-8, data_engineering) while verifying defi_satellite_ao_dispatch_batch2_2026_07_26.md's LST
    rates backfill todo -- direct manifest reads against market-data-tick-defi-prd's availability_index.parquet
    (column+filter pushdown, not a full-corpus read).",
  ]
resolved_by: 2026-07-28 (slot-11) — 29-day gap backfilled for all 5 protocols, manifest-verified 145/145 captured
locked_by:
locked_since:
---

> **🟢 RESOLVED 2026-07-28 (slot-11)** — 29-day gap backfilled for all 5 `vault_share_price` protocols
> (ETHENA/FRAX/MAKER/MORPHOVAULTS/YEARN_V3), manifest-verified 145/145 rows captured. No code change was needed; the
> underlying scheduling gap was already fixed by `deployment-service@600d31c`.

# MAKER's vault_share_price has a real 29-day manifest gap

## What I found

1. **MAKER is not an `lst_rates` venue.** `grep -rln '"MAKER"' market_tick_data_service/cli/handlers/` returns only
   `vault_share_price_handler.py` — `lst_rates_handler.py` never references MAKER.
   `load_evm_lst_contract_addresses_for_date` (the function `lst_rates_handler.py` actually uses) does not return a
   `MAKER` key for any date checked (2026-07-20/23/25, live-verified). MAKER's 87 legacy rows under
   `data_type=lst_rates` (2026-04-27..2026-07-22, `written_at` all clustered at `2026-07-23T01:30:05Z` — a single
   retroactive batch write, not organic day-by-day capture) look like a stale/legacy classification that correctly
   stopped being written once the writer's real `data_type=vault_share_price` classification took over — not a bug in
   `lst_rates_handler.py`.

2. **The 5 genuine LST-rate venues need NO backfill.** Direct manifest read (columns=[date,venue,data_type,
   capture_status,written_at], filters on venue+data_type — not a full-index load, see "measurement trap" below) shows
   ANKR/STADER/STAKEWISE/SWELL/MANTLE at 90/90 captured days for 2026-04-27..2026-07-25, all via the daily cron's
   organic day-by-day writes (verified `uts-prod-mtds-collect-lst-rates-cron` healthy: last 4 Cloud Run executions
   2026-07-23..2026-07-26 all `Completed True`, vs. 2 `Completed False` on 2026-07-21/22 before the crash-loop fix
   `mtds@522185a6` landed). The 90-day RPC backfill the parent todo asked for was ALREADY organically complete for these
   5 — running it would have been ~2,340 wasted RPC calls.

3. **MAKER's real data type (`vault_share_price`) has a genuine gap.** Filtering the manifest to
   `venue=MAKER, data_type=vault_share_price`: 61/90 days captured in the 2026-04-27..2026-07-25 window, with a single
   contiguous missing block: **2026-06-22 through 2026-07-20 (29 days)**. Confirmed these are NOT `attempted_failed`
   rows silently mislabeled — a direct manifest query for exactly those 3 spot-checked dates (2026-07-23/24/25, the
   originally-suspected gap before the reclassification was found) returned a genuinely EMPTY DataFrame — the writer
   never even attempted these days, not a recorded failure. Days before 2026-06-22 and after 2026-07-20 (including the
   most recent 07-21..07-25) ARE captured, so this isn't an ongoing/current outage — it's a bounded historical gap.

## Why it matters

29 consecutive days of missing `vault_share_price` data for MAKER is a real coverage hole in the DeFi manifest,
independent of (and not fixed by) the LST-rates backfill work this was originally found while verifying.

## Root cause (found 2026-07-28, slot-9, `data_engineering`)

**Not MAKER-specific — it's the whole `vault_share_price` handler, and the gap is already structurally fixed.**

1. **The gap is identical across all 5 protocols, not just MAKER.** Direct manifest read of
   `data_type=vault_share_price` for 2026-06-15..2026-07-25, grouped by `venue`, shows ETHENA / FRAX / MAKER /
   MORPHOVAULTS / YEARN_V3 ALL missing the exact same 29 days (2026-06-22..2026-07-20 inclusive) — proving this is a
   handler-wide scheduling gap, not a MAKER-specific contract/config bug. (Ruled out the config-change hypothesis too:
   `git log --all -p -- vault_share_price_handler.py` shows the `sDAI` registry entry — address
   `0x83F20F44975D03b1b09e64809B757c47f942BEeA`, chain, protocol, underlying — has never changed since it was first
   added 2026-05-03, commit `9475e66b`.)

2. **`collect-vault-share-price` had NO Cloud Scheduler / Cloud Run Job entry until 2026-07-22.** The handler code
   (`VaultSharePriceHandler`) has existed since 2026-05-03 (commit `9475e66b`, market-tick-data-service), but it was
   never wired into `deployment-service/terraform/gcp/defi_collection_scheduler.tf`'s `defi_collect_operations` map —
   confirmed by `git log` on that file: commit `600d31c` ("feat(defi): schedule mev-events, bridge-events,
   vault-share-price DeFi collect jobs (Terraform-only)", 2026-07-22T18:28:49+01:00 = 17:28:49Z) is the FIRST commit
   that adds a `"vault-share-price"` block to `defi_collect_operations` (schedule `10 1 * * *`). Before that commit the
   map only had 11 entries; `vault-share-price` wasn't one of them — the file's own header comment says so explicitly
   ("none of which had a scheduler entry" pre-existed this class of fix). Cloud Logging confirms this empirically: the
   Cloud Run Job `uts-prod-mtds-collect-vault-share-price`'s earliest log entry EVER is a `NOTICE` at
   `2026-07-22T17:30:58Z` — 2 minutes after the terraform commit landed — i.e. that is the job's first-ever execution,
   full stop. `gcloud run jobs executions list` shows only 7 executions total, all `2026-07-22` or later, all
   `Completed True`, and it has run cleanly on the `10 1 * * *` schedule every day since (verified through
   `2026-07-28`).

3. **A retroactive backfill (run 2026-07-23) filled history back to 2023-01-18, but stopped one day short of where the
   new organic cron picked up, leaving exactly this 29-day hole.** Per-row `written_at` timestamps for
   `venue=MAKER,data_type=vault_share_price` show: every row from `2023-01-18` through `2026-06-21` was written in a
   single batch on `2026-07-23T13:51:35Z..16:55:xxZ` (clearly a day-by-day backfill script, ~30-90s/day cadence,
   matching `launch-mtds-vault-share-price-backfill-vm.sh`'s documented ~30s/day rate) — NOT organic daily capture. Then
   `2026-07-21` was written `2026-07-22T17:33:39Z` (the new cron's first live run, 2 min after job creation — this is
   what backfilled the "day before" gap boundary, not the scheduled 01:10 cron) and `2026-07-22` onward are organic
   `01:10-01:11 UTC` daily runs. **Nothing ever wrote `2026-06-22..2026-07-20`** — the historical backfill's window
   ended at `2026-06-21` (one day before the org cron began), so those 29 days fall in the crack between "backfill
   covered up to X" and "cron started covering from Y" where X+1 != Y.

**Net**: no code fix is needed — the underlying cause (missing scheduler wiring) was already fixed by `600d31c`
(unrelated to this issue; it was fixing `mev-events`/`bridge-events`/`vault-share-price` scheduling together) and is
confirmed running healthily. The only remaining action is the backfill for the 29-day crack, which is exactly what the
`[SCRIPT] P2` todo below already covers — it is now UNBLOCKED (underlying cause confirmed fixed).

## Recommended decision

- [x] [DIAG] P2. Root-cause the 2026-06-22..2026-07-20 MAKER `vault_share_price` gap — ✅ 2026-07-28 (slot-9,
      data_engineering). Root cause: `collect-vault-share-price` had no Cloud Scheduler/Cloud Run Job entry until
      `deployment-service@600d31c` (2026-07-22); a post-fix retroactive backfill (2026-07-23) covered history through
      2026-06-21 but the org cron only started covering from 2026-07-21, leaving this exact 29-day crack. Confirmed
      handler-wide (all 5 protocols show the identical gap, not just MAKER) and confirmed the underlying scheduling gap
      is already fixed + healthy (7/7 executions `Completed True` since 2026-07-22, daily `01:10 UTC`). See "Root cause"
      section above for full evidence. No code change required — nothing to ship in market-tick-data-service.
- [x] [SCRIPT] P2. ✅ 2026-07-28 (slot-11). Backfilled the confirmed 29-day gap (2026-06-22..2026-07-20) for ALL 5
      `vault_share_price` protocols (ETHENA/FRAX/MAKER/MORPHOVAULTS/YEARN_V3) via
      `deployment-service/scripts/vm/launch-mtds-vault-share-price-backfill-vm.sh 2026-06-22 2026-07-20` — SPOT VM
      `mtds-vault-share-price-20260728-055107` (asia-northeast1-c), ran 05:51:07..05:57:20 UTC, exit_code=0, "Batch
      complete: 29 results collected", self-deleted on completion. Manifest-verified via direct
      `market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` read
      (columns=[date,venue,data_type,capture_status,written_at], filters on data_type=vault_share_price — not a
      full-corpus load): 145/145 rows present for the window (29 days × 5 protocols), all `capture_status=captured`,
      zero gaps remaining. Non-blocking IAM warning during the run (`run-ledger` pubsub publish 403 on the VM's default
      service account) is a separate, already-tracked issue
      (`/plans/active/issues/vm_run_ledger_publish_iam_permission_denied_2026_07_28.md`) — did not block or affect the
      backfill write path. No code change required (repo: market-tick-data-service, deployment-service — launcher script
      used as-is).

## Measurement trap (for the next reader)

`market-data-tick-defi-prd`'s `availability_index.parquet` is ~15GB uncompressed as a full-schema `pd.read_parquet` load
(matches the already-documented `mtds_backfill_vm_startup_oom_rc137_2026_07_14` finding) — a naive full read took over 5
minutes and 16GB+ RSS before being killed. Always use `columns=[...]` + `filters=[...]` (row-group predicate pushdown)
for a targeted query — the same filtered read above completed in seconds.

## Progress Log (append-only)

- 2026-07-26 (slot-8, `data_engineering`): filed while verifying `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s
  LST-rates backfill todo. Confirmed no backfill needed for the 5 genuine LST venues; confirmed MAKER's real gap is in a
  different handler/data_type than the parent todo assumed; did not attempt the RPC backfill (would have been wasted
  work) or root-cause the vault_share_price gap (out of scope for this pass — flagged with exact evidence rather than
  guessed at).
- 2026-07-28 (slot-9, `data_engineering`): root-caused the `[DIAG] P2` todo. Direct manifest read
  (`market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, columns+filters pushdown)
  showed the 2026-06-22..2026-07-20 gap is IDENTICAL across all 5 `vault_share_price` protocols, not MAKER-specific —
  reclassified the issue from MAKER-only to handler-wide (title/summary updated above). Confirmed via `git log` on
  `deployment-service/terraform/gcp/defi_collection_scheduler.tf` that `collect-vault-share-price` had no Cloud
  Scheduler/Cloud Run Job entry until commit `600d31c` (2026-07-22); confirmed empirically via
  `gcloud logging read resource.type=cloud_run_job resource.labels.job_name=uts-prod-mtds-collect-vault-share-price`
  that the job's earliest-ever log line is `2026-07-22T17:30:58Z` (2 min after that commit landed) and
  `gcloud run jobs executions list` shows only 7 executions total, all post-2026-07-22, all `Completed True`. Confirmed
  the retroactive backfill (per-row `written_at` timestamps, all clustered `2026-07-23T13:51..16:55Z` for
  2023-01-18..2026-06-21) stopped one day short of where the new cron's organic coverage began (2026-07-21), producing
  this exact crack. Ruled out a MAKER-specific config/contract-address change (`git log --all -p` on the handler shows
  the `sDAI` registry entry unchanged since 2026-05-03). No code fix needed — the scheduling gap is already fixed and
  running healthily; flipped `[DIAG] P2` to done and rescoped the remaining `[SCRIPT] P2` backfill todo to cover all 5
  protocols (was MAKER-only) since the finding shows the gap is handler-wide. Did not run the backfill itself — separate
  tracked todo, now unblocked for the next dispatch.
- 2026-07-28 (slot-11): ran the `[SCRIPT] P2` backfill. Launched
  `deployment-service/scripts/vm/launch-mtds-vault-share-price-backfill-vm.sh 2026-06-22 2026-07-20` — SPOT VM
  `mtds-vault-share-price-20260728-055107` (asia-northeast1-c, e2-standard-8), ran 05:51:07..05:57:20 UTC (~6 min, well
  under the ~15min estimate), exit_code=0, log shows "Batch complete: 29 results collected", self-deleted on completion
  per `VM_SHUTDOWN_ON_COMPLETION=true`. Manifest-verified via direct filtered read of
  `market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`
  (columns=[date,venue,data_type,capture_status,written_at], filters=[data_type==vault_share_price] — not a full-corpus
  load, per this doc's own "measurement trap" note): 145/145 rows present for the 2026-06-22..2026-07-20 window across
  ETHENA/FRAX/MAKER/MORPHOVAULTS/YEARN_V3 (29 days × 5 protocols), all `capture_status=captured`. The gap is fully
  closed. Launch-time tarball-freshness warning (4 stale tarballs) did not affect correctness — the handler's vault
  registry has been unchanged since 2026-05-03 (already confirmed above) and the run's own log confirms it wrote the
  expected 5-protocol/8-vault set correctly. One non-blocking IAM 403 in the run log (`run-ledger` pubsub publish, VM
  default service account lacks `pubsub.topics.publish`) did not affect the backfill's data write path — already tracked
  separately at `/plans/active/issues/vm_run_ledger_publish_iam_permission_denied_2026_07_28.md`, no new issue filed.
  Both todos now done; issue closed (`status: resolved`).
