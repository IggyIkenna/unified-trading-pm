---
doc_type: issue
title:
  mtds-perp-funding-backfill VM hangs silently at 2026-05-29 (kalshi_perp genesis date) — no crash, no error, zero
  progress for 53+ min
summary:
  "mtds-perp-funding-backfill (relaunched 2026-07-14T16:07:56Z per mtds_backfill_vm_startup_oom_rc137_2026_07_14's
  fix-verification todo) processed its full backfill range cleanly from 2023-11-01 through 2026-05-28, then went
  completely silent — no 'Perp funding collection complete' line, no error, no traceback, no crash — for 53+ minutes
  (confirmed via two independent checks 21.6min apart, both showing byte-identical last-progress timestamp
  2026-07-14T16:28:37Z). VM remains RUNNING with flat RESOURCE_SAMPLE heartbeats (rss~626-627MiB, cpu~0.2%) the entire
  time — alive, not crashed, just producing zero output. 2026-05-29 is the exact date kalshi_perp transitions from
  'before launch' (honest EXPECTED_PRE_VENUE_LAUNCH, cheap/instant) to its genesis date requiring a real fetch attempt —
  the log's last 'before launch' line for kalshi_perp is dated 2026-05-27, meaning the very next iteration (2026-05-29)
  is the first date kalshi_perp's collector must actually make a live call. This blocks
  mvp_backfill_defi_onchain_v10-002's G2 gate for perp_funding independent of, and in addition to, the already-tracked
  multi-day DRIFT sig-index walker drain."
status: open
nature: record
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [hang, backfill-vm, mtds, perp-funding, kalshi, defi, timeout]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md,
  ]
created: 2026-07-14
assigned_vm: planning
source: [mvp_backfill_defi_onchain_v10-002]
parent_epic: defi_master
priority: P1
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

Dispatched to `mvp_backfill_defi_onchain_v10-002` (G2 final DeFi MVP verification). Per the established cadence, checked
the DRIFT sig-index walker fleet (healthy, both walkers advancing normally — gap walker 1928→2151 parts, resume walker
8296→8538 parts over ~21.6min, zero errors). While tailing logs for the fleet, also opportunistically checked
`mtds-perp-funding-backfill` (relaunched by slot-11 at 2026-07-14T16:07:56Z per the OOM-fix verification todo in
`mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`) since it is one of the two VMs directly gating this task's
perp_funding data_type.

**Timeline of the hang**:

- VM launched 16:07:56Z (`--start 2023-11-01 --end 2026-07-14`), collecting cleanly — genuine "Perp funding collection
  complete for `<date>`: 2 records across 3 protocols" lines throughout, including honest-absence handling for
  `kalshi_perp` (pre-launch dates → `EXPECTED_PRE_VENUE_LAUNCH`) and `polymarket_perp` (DNS NXDOMAIN since 2026-06-21 →
  `attempted_failed`, correctly typed as `SOURCE_UNREACHABLE` not a silent zero).
- Last real progress line:
  **`2026-07-14 16:28:37,536 INFO Perp funding collection complete for 2026-05-28: 2 records across 3 protocols`**.
- From 16:28:37Z onward: **zero** "collection complete" / error / traceback / warning lines of any kind — only
  `RESOURCE_SAMPLE` (flat `rss=626-627MiB`, `cpu=0.0-0.4%`) and `PIPELINE_HEARTBEAT` lines, every ~30-60s, indefinitely.
- Confirmed via two independent checks: first at ~17:00Z (~32min silent), second at 17:21:44Z (~53min silent, byte
  identical last-progress timestamp both times) — this rules out a merely-slow date; the process is genuinely stuck, not
  working through a large per-date payload.
- VM status both checks: `RUNNING` (not preempted, not crashed, not self-deleted) — this is a true hang, not the rc=137
  OOM-kill pattern `mtds_backfill_vm_startup_oom_rc137_2026_07_14.md` already tracks (that issue's crashes are instant
  SIGKILLs with a clear `Killed`/`rc=137` marker; this VM shows no kill signal at all, just silence).

**Root-cause hypothesis (not yet confirmed by a live repro — no SSH access from this data_engineering craft-scoped
sandbox, same constraint noted in the sibling OOM issue doc)**: the immediately preceding log lines show
`kalshi_perp: 2026-05-26 is before launch (2026-05-29) — recording EXPECTED_PRE_VENUE_LAUNCH` and the same for
2026-05-27 — i.e. `kalshi_perp`'s launch date is **2026-05-29**, exactly the date immediately after the last
successfully processed date (2026-05-28). Every date up to and including 2026-05-28 takes the cheap, instant "before
launch" honest-absence branch for `kalshi_perp`; 2026-05-29 is the **first date that branch does not apply**, forcing
`kalshi_perp`'s collector into a real (non-honest-absence) fetch code path for the first time in this VM's entire run.
The hang starting at exactly this boundary is a strong (though not yet SSH-confirmed) signal that `kalshi_perp`'s
live-fetch path lacks a request timeout and is blocked indefinitely on a network call (or a retry/backoff loop that
never logs), analogous to `polymarket_perp`'s already-handled `SOURCE_UNREACHABLE` case but without that case's graceful
catch-and-record-failure wrapper.

Also worth noting (not the primary suspect, but present at the same moment): a `ManifestConsolidatorStaleError` fires on
essentially every date (consolidated blob age >120s threshold, same consolidator-lag class as
`defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`) but is caught gracefully (`ManifestFreshnessCache` logs
the error and "keeps previous membership set") — this does NOT appear to be the hang cause since it fired identically on
every prior date without stalling the loop; flagging only for completeness in case the two are related under different
load conditions.

## Why it matters

- Blocks `mvp_backfill_defi_onchain_v10-002`'s G2 gate for `perp_funding` **independent of** the already-tracked
  multi-day DRIFT sig-index walker drain — even once DRIFT's Helius-quota-gated backfill finishes, this VM will not
  reach `kalshi_perp`'s post-genesis dates (2026-05-29 onward, ~1.5 months short of `--end 2026-07-14`) without
  intervention.
- If the root-cause hypothesis is correct, **any other DeFi/CeFi venue with a mid-range genesis date** could trigger the
  identical silent hang the first time a backfill VM's date loop crosses that venue's launch boundary — this may not be
  `kalshi_perp`-specific or `perp_funding`-specific.
- A silent hang (VM stays `RUNNING`, heartbeats stay green, no error surfaces) is worse than a crash for operational
  visibility — nothing pages, nothing self-heals, and a naive dashboard check would read this VM as healthy indefinitely
  while it makes zero progress. Worth considering a "no data-progress for N minutes while RUNNING" liveness check at the
  deployment-observability layer, not just per-VM crash detection.

## Recommended decision

1. **Confirm the hang site** — a fix-worker with SSH/shell access to the live VM (or a local repro against
   `kalshi_perp`'s collector module with `--start 2026-05-29 --end 2026-05-30`) should attach/thread-dump or add
   targeted logging immediately before/after `kalshi_perp`'s live-fetch call to confirm it's the blocking site.
2. **If confirmed**: add a request timeout (and a `SOURCE_UNREACHABLE`/`attempted_failed` fallback on timeout, mirroring
   the existing `polymarket_perp` DNS-outage handling) to `kalshi_perp`'s collector so a slow/hanging upstream degrades
   to an honest failure record instead of hanging the whole process indefinitely.
3. **VM action** (infra-craft scope, not this session's): once fixed, relaunch `mtds-perp-funding-backfill` from
   `--start 2026-05-29` (its manifest-gated idempotency will skip everything already captured through 2026-05-28) and
   verify it progresses past 2026-05-29 without hanging, before resuming `mvp_backfill_defi_onchain_v10-002`'s G2
   verification for this data_type.
4. Consider whether other venues with mid-backfill-range genesis dates (any DeFi/CeFi venue, not just kalshi_perp) share
   this same missing-timeout risk — worth a quick grep across venue collectors for calls without an explicit timeout
   once this one is confirmed/fixed.

## Todos

- [ ] [BACKEND] P1. Confirm the hang site: attach to (or locally repro) `kalshi_perp`'s live-fetch collector for its
      2026-05-29 genesis date; identify the blocking call (network request without timeout, retry loop, or lock wait).
      Repo: `market-tick-data-service`.
- [ ] [BACKEND] P1. If confirmed as a missing-timeout network call: add an explicit timeout + honest
      `SOURCE_UNREACHABLE`/`attempted_failed` fallback on timeout to `kalshi_perp`'s collector (mirror the existing
      `polymarket_perp` DNS-outage handling pattern in the same file). Add a regression test pinning the timeout
      behavior. Repo: `market-tick-data-service`.
- [ ] [INFRA] P2. Once fixed, relaunch `mtds-perp-funding-backfill --start 2026-05-29 --end 2026-07-14` (manifest-gated,
      skips already-captured dates) and verify it progresses past 2026-05-29 without hanging (T+10min real-progress
      check, not just liveness) before resuming `mvp_backfill_defi_onchain_v10-002`'s G2 verification for perp_funding.
      Repo: `deployment-service`.
- [ ] [SCRIPT] P3. Grep other DeFi/CeFi venue collectors for calls made without an explicit request timeout,
      particularly around genesis-date transition logic (the `EXPECTED_PRE_VENUE_LAUNCH`-to-real-fetch boundary pattern)
      — this hang's root cause, if confirmed, may recur wherever that pattern exists elsewhere. Repo:
      `market-tick-data-service`.

## Evidence

- `mtds-perp-funding-backfill` full `run.log`, last progress line:
  `2026-07-14 16:28:37,536 INFO Perp funding collection complete for 2026-05-28: 2 records across 3 protocols` — no
  further progress/error/traceback lines through at least `2026-07-14T17:21:18Z` (53min+ silent), only
  `RESOURCE_SAMPLE`/`PIPELINE_HEARTBEAT` lines.
- Immediately preceding lines confirm `kalshi_perp` launch date = 2026-05-29
  (`"2026-05-26 is before launch (2026-05-29)"`, `"2026-05-27 is before launch (2026-05-29)"`).
- `gcloud compute instances describe mtds-perp-funding-backfill --zone=asia-northeast1-c` → `status: RUNNING` at both
  the ~17:00Z and 17:21:44Z checks (not preempted, not crashed).
- `gcloud compute operations list` for this instance shows no `preempted`/kill event during the hang window (checked as
  part of confirming this is not the sibling `rc=137` OOM-kill pattern).
