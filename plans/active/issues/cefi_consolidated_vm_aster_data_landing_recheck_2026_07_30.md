---
doc_type: issue
title:
  "Re-check the consolidated CeFi live-capture VM's ASTER data landing after the 13:30 UTC daily instrument-catalogue
  refresh (2026-07-30)"
summary: >-
  mtds-live-cefi-consolidated-20260730-010147 was launched 2026-07-30 01:01 UTC with ASTER's book_snapshot_5 +
  liquidations shards folded in per the operator's 2026-07-28 ruling (infra_capture_and_devops_leftovers_2026_07_06.md).
  VM booted cleanly and all 17 shards are running, but every shard (ASTER and all 15 pre-existing venues alike) is
  waiting on today's instrument-availability catalogue, which instruments-service's daily scheduler
  (google_cloud_scheduler_job.is_daily_enum, schedule "30 13 * * *") had not yet produced at launch time. This is
  expected 300s-retry behavior, not a bug — needs a follow-up check after 13:30 UTC to confirm real data actually lands
  once the catalogue refreshes.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, instruments-service]
scope: [engineer]
tags: [cefi, aster, live-capture, verification, follow-up]
related:
  [
    /plans/active/infra_capture_and_devops_leftovers_2026_07_06.md,
    /plans/archive/issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md,
  ]
created: 2026-07-30
priority: P2
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: "autonomous session 2026-07-30, VM launch + monitoring for infra_capture_and_devops_leftovers_2026_07_06.md"
resolved_by:
drift_direction: advance-code
context_scope:
  [
    /plans/active/infra_capture_and_devops_leftovers_2026_07_06.md,
    /plans/archive/issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /plans/active/cefi_satellite_ao_dispatch_batch4_2026_07_31.md,
  ]
---

# CeFi consolidated VM — ASTER data-landing re-check after 13:30 UTC

## What happened

Launched `mtds-live-cefi-consolidated-20260730-010147` (`asia-northeast1-c`, `e2-highmem-16`, on-demand) at
2026-07-30T01:01:47Z, folding ASTER `book_snapshot_5` + `liquidations` into the MVP shard list per the operator's
2026-07-28 ruling. Confirmed healthy:

- Boot + full setup completed in ~140s (well under the STARTED<60s-class check — this counts the whole dependency
  install + shard launch, not just VM creation).
- All 17 shards (15 pre-existing venues + 2 new ASTER) confirmed running via direct SSH `ps aux` — steady CPU
  accumulation, not crash-looping.
- **Every shard, ASTER included, is correctly logging `IS universe empty ... retrying in 300s`** because today's
  (2026-07-30) `instruments.parquet` does not exist yet under
  `gs://instruments-store-cefi-prd-central-element-323112/instrument_availability/by_date/day=2026-07-30/...` for ANY
  venue — confirmed via direct GCS listing that yesterday's (2026-07-29) equivalent exists for every venue including
  ASTER. Root cause: `deployment-service/terraform/gcp/daily_is_enumeration_scheduler.tf`'s
  `google_cloud_scheduler_job.is_daily_enum` runs at `30 13 * * *` (13:30 UTC) — it simply had not fired yet at 01:16
  UTC launch/check time. This is designed retry behavior, not a defect.

## Todos

> **✅ OWNERSHIP RESOLVED 2026-07-31 (corpus-wide ownership-conflict sweep, operator ruling keep-one-cite-the-other).**
> The near-verbatim "verify `live_aster` rows land" claim appeared in both this doc and
> `/plans/active/infra_capture_and_devops_leftovers_2026_07_06.md`'s `[DATA] P1`. **Split by phase, not deleted from
> either**: the infra plan OWNS _register + launch_ the ASTER live connector (its actual scope, and it holds all the
> prereq history); **THIS doc OWNS the post-launch data-landing verification** — it is newer (2026-07-30 vs 2026-07-06),
> carries the concrete dated command, and already declares itself the thing that flips the infra plan's checkbox. The
> infra plan's todo now cites this doc for the verification half instead of restating it.
>
> **Not verified this session, and deliberately not claimed either way**: the 2026-07-30T13:30Z re-check could not be
> run — `gcloud storage ls` failed reauth in this non-interactive slot for all three credentialed identities
> (`unified-trading-sa` has no valid credentials here; the operator account needs an interactive `gcloud auth login`).
> The todo stays `- [ ]`. Whoever picks it up runs the command below first; a fabricated "rows landed" is worse than an
> unrun check.

> **📤 ALL THREE TODOS BELOW ARE EXTRACTED ELSEWHERE — do NOT dispatch from this doc (`/na-eligibility-audit`
> 2026-08-02, tranche=cefi).** Split across two satellite batches, each Source-citing this doc: **todos 1 and 2** (the
> `gcloud storage ls` ASTER landing re-check and the 2-3 pre-existing-venue spot-check) are claimed verbatim by
> `/plans/active/cefi_satellite_ao_dispatch_batch4_2026_07_31.md` todo 2 (`assigned_vm: planning`, still `status: draft`
> — activation is the operator's call, `unified-trading-pm@2d5fb4b59`); **todo 3** (the ASTER `liquidations` multi-hour
> listen window, added 2026-07-31 and therefore not visible to batch4 when it was drafted) is claimed by
> `/plans/active/cefi_satellite_ao_dispatch_batch5_2026_08_02.md` todo 4 `[DIAG] P3` (`status: active`,
> `unified-trading-pm@766822efe`). This doc stays `assigned_vm: NA` deliberately — flipping it would create a second
> dispatch path for checks already claimed twice over. Each batch's done-when includes flipping the source checkbox
> here, so those workers own closing them.

- [ ] [DATA] P2. **After 2026-07-30T13:30Z UTC**, re-check whether real rows are landing:
      `gcloud storage ls "gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2026-07-30/pipeline_mode=live_aster/**"`.
      If populated: flip `infra_capture_and_devops_leftovers_2026_07_06.md`'s ASTER-connector todo's remaining checkbox
      with this evidence, and archive/retire `issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md` as
      resolved (both per that plan's own completion mandate). If still empty well past 13:30 UTC, treat as a genuine new
      bug (this doc's finding only explains absence BEFORE the catalogue refresh) and investigate the live shard logs
      fresh (SSH, `sudo tail -f /home/ikennaigboaka/logs/live-aster-*.log`) rather than assuming the same root cause
      applies. **STILL NOT VERIFIED, checked 2026-08-02T13:32Z UTC (slot 2, spot-check during an unrelated finalize-plan
      reconciliation)**: ran the exact command above for day=2026-07-30 AND day=2026-07-31 AND day=2026-08-01 — **all
      three return zero objects** (`ERROR: ... matched no objects`); listing each day's full `pipeline_mode=` partition
      set shows only `batch_*` modes present (e.g. `batch_hyperliquid`, `batch_kalshi_perp`, `batch_tardis`,
      `batch_deribit`) — **no `live_*` pipeline_mode has appeared under this bucket on any of the 3 days checked**, well
      past the 13:30 UTC catalogue refresh this todo's branch condition names. Separately: the 2026-07-30-launched VM
      (`mtds-live-cefi-consolidated-20260730-010147`) is no longer in the live fleet
      (`gcloud compute instances list     --filter="name~mtds-live"` returns only one instance) — it has been replaced
      by `mtds-live-cefi-consolidated-20260802-130832`, created 2026-08-02T13:08:40Z, ~24 minutes before this check (too
      fresh to expect any data from). **Did not chase further** (out of scope for the task that triggered this
      spot-check) — but this is now past the "genuine new bug" threshold this todo's own branch anticipates: 3 full days
      with zero live rows from the OLD VM, and an unexplained VM replacement with no landed-data window in between.
      Whoever picks this up next should SSH the current VM, `sudo tail -f` the ASTER shard logs fresh (per this todo's
      own fallback instruction), and separately check why the 07-30 VM disappeared (self-heal/zombie-watchdog relaunch?
      crash? manual replace?) before assuming the fresh VM will behave differently.
- [ ] [DATA] P3. Spot-check 2-3 of the 15 pre-existing venues (e.g. HYPERLIQUID, BINANCE-FUTURES) the same way — they
      hit the identical empty-universe wait, so their data-landing should resume at the same time; confirms the fix is
      fleet-wide, not ASTER-specific relief only.
- [ ] [DATA] P3. **ASTER `liquidations` shows 100% `empty_confirmed` in the manifest (563/563 samples) — investigated
      2026-07-31, inconclusive, needs a longer real-world check, not a re-guess.** Live-tested the real connector
      directly (`AsterLiquidationsWSConnector` in `market_tick_data_service/live/connectors/aster_book_liq_ws.py`):
      connects to `wss://fstream.asterdex.com/ws` cleanly, `SUBSCRIBE !forceOrder@arr` gets a normal
      `{"id":1,"result":null}` ack (no error), and `_parse_aster_force_order`'s field mapping
      (`o.s`/`o.S`/`o.p`/`o.q`/`o.T`) matches the real Binance-compatible `forceOrder` wire shape exactly — this is NOT
      the same bug class as the BINANCE-FUTURES/ASTER book_snapshot_5 `bids`/`asks` vs `b`/`a` mismatch (already fixed,
      market-tick-data-service@4f244845). Two live listen windows (20s, then 90s) received the subscribe ack and ZERO
      `forceOrder` events — consistent with genuine liquidation rarity on a lower-volume, all-market stream (unlike
      book_snapshot_5's 100ms cadence, liquidations are inherently sparse even on a healthy feed), but ~110s combined is
      far too short to rule out a subtler reconnect-drop bug if the 563 samples span hours/days. DoD before closing
      either way: run a live listen window of several hours (or check the connector's own reconnect-flag/log activity
      over the VM's actual uptime) — if it goes that long with zero events despite reconnecting cleanly, this is
      data-source reality, not a bug, and should be closed as such; if there's ANY silent multi-hour disconnect with no
      reconnect, that's the real bug to fix.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY candidate PARKED on conflict-check:
  `infra_capture_and_devops_leftovers_2026_07_06.md` (active, assigned_vm:planning) already carries the near-verbatim
  "verify `live_aster` rows land" claim, and this doc's own todo says to flip THAT plan's checkbox. Duplicate dispatch
  risk. Filed as BLOCKED-OPERATOR-DECISION in this run's Deferred list; `assigned_vm` unchanged.

- **na-eligibility-audit 2026-08-01** (tranche=cefi, autonomous): KEEP-NA, pending. Both open todos (ASTER recheck +
  2-venue spot-check) clear the bounded-outcome bar on their own merits (one `gcloud storage ls` command per venue,
  fully-specified branches) and the 2026-07-30 park reason (conflict with
  `infra_capture_and_devops_leftovers_2026_07_06.md`) is independently confirmed RESOLVED (that doc's verification-half
  checkbox now explicitly re-homes to this doc, 2026-07-31 banner). NOT reclassified this run because
  `cefi_satellite_ao_dispatch_batch4_2026_07_31.md` todo 2 already drafted this exact scope verbatim (Source-cited) —
  batch4 is `status: draft`, not active. Reclassifying independently now risks the same `gcloud storage ls` check being
  dispatched twice via two mechanisms once batch4 activates. Recommend: prefer batch4's operator-review/activation path
  over an independent flip here.
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **na-eligibility-audit 2026-08-02** (tranche=cefi, autonomous): **KEEP-NA-STALE (already-duplicated) — citation fixed,
  not reclassified.** Re-entered scope on the 2026-08-02 ASTER-liquidations investigation append (which added evidence,
  not new work). The 08-01 verdict's open question — batch4 was `status: draft`, so was todo 3 covered anywhere? — is
  now settled: `cefi_satellite_ao_dispatch_batch5_2026_08_02.md` (active, planning, `unified-trading-pm@766822efe`)
  extracted todo 3 as its `[DIAG] P3` and explicitly documented in its "What was excluded and why" section that todos
  1-2 were left to batch4 as a near-verbatim duplicate under conflict-check § 3. So all three todos are now claimed with
  no gap and no double-claim. Extraction banner added above the todos. `assigned_vm: NA` unchanged. Also merged a stray
  second `## Progress Log (na-eligibility-audit)` heading back into the single `## Progress Log` section (structural
  fix, no content change).
