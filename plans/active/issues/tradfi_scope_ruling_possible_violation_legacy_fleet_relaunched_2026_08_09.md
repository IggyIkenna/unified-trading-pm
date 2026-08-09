---
doc_type: issue
title: >-
  Possible violation of the MVP-of-MVP scope ruling — NASDAQ/NYSE 2023/2024 equities backfill VMs observed running after
  the ruling said this fleet is "killed, not resumed"
summary: >-
  While monitoring my own ES_OPT launch (batch6 todo #2), I observed a fresh wave of `tradfi-bf-nasdaq-ohlcv-1m-2023-*`
  and `tradfi-bf-nyse-ohlcv-1m-2023/2024-*` VMs (10 total) running as of 2026-08-09T~03:40Z, alongside
  `tradfi-bf-cme-ohlcv-1m-g01-{es,eth,mbt,met}-*` shards. The CME ES/ETH/MBT/MET shards ARE in-scope per
  `issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`'s table (CME BTC/ETH futures, full history). But the
  NASDAQ/NYSE year-shards are running a full 2023 date-window backfill (confirmed via run.log, chunk 1 of 8, window
  2023-04-15 to 2023-04-21) — the scope ruling's table explicitly scopes "Delta-one single-stock equities" to "Year 2026
  only (not the full multi-year history)" and lists "Delta-one single-stock equities for years other than 2026" under
  "Out of scope — gated until November 2026." That same doc also states the FX/commodity legacy fleet's disposition as
  "killed, not resumed" — this new NASDAQ/NYSE wave looks like a resumption of (or a new launch matching the shape of)
  exactly that out-of-scope work. I have NOT taken any action on these VMs (no delete, no investigation of who launched
  them or why) — flagging for someone with fuller context to check whether this is a genuine violation or a scope I'm
  misreading (e.g. maybe these are ETF-only or otherwise legitimately re-scoped since the ruling). This is a passive
  observation from an unrelated task, not a targeted audit.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [tradfi, scope-ruling, vm, backfill, possible-violation]
related:
  [
    /plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
  ]
created: "2026-08-09"
author: slot-28
priority: P1
parent_epic: tradfi_master
source: >-
  Passive observation 2026-08-09T~03:40Z while monitoring `tradfi-bf-*` fleet state for an unrelated ES_OPT launch
  (batch6 todo #2) — `gcloud compute instances list --filter='name~"^tradfi-bf-"'` showed the new wave; one VM's run.log
  confirmed a 2023 date window.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: fix
estimate_class: research
estimate_baseline: 0.2
calibrated_ai_days: 0.15
assigned_role: infra
resolved_by:
locked_by:
depends_on: []
---

# Possible scope-ruling violation — legacy NASDAQ/NYSE fleet relaunched

## Observation

`gcloud compute instances list --filter='name~"^tradfi-bf-"'` at 2026-08-09T~03:40Z showed (among others):

```
tradfi-bf-nasdaq-ohlcv-1m-2023-d01-20260809-032338
tradfi-bf-nasdaq-ohlcv-1m-2023-d02-20260809-032410
tradfi-bf-nasdaq-ohlcv-1m-2023-d03-20260809-032434
tradfi-bf-nasdaq-ohlcv-1m-2023-d04-20260809-032510
tradfi-bf-nasdaq-ohlcv-1m-2023-d05-20260809-032532
tradfi-bf-nasdaq-ohlcv-1m-2024-d01..d05-*
tradfi-bf-nyse-ohlcv-1m-2023-d01..d05-*
tradfi-bf-nyse-ohlcv-1m-2024-d01..d05-*
```

`tradfi-bf-nasdaq-ohlcv-1m-2023-d01-...`'s run.log confirms a real 2023 date-window backfill in progress
(`--- Chunk 1/8: 2023-04-15 → 2023-04-21 ---`), not a 2026-scoped run.

## Why this looks like a possible violation

`issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` (same day, earlier):

- Scope table: "Delta-one single-stock equities | **Year 2026 only** (not the full multi-year history)".
- Out-of-scope list: "Delta-one single-stock equities for years **other than 2026** (i.e. completing the full historical
  equities corpus to 100%)".
- "Disposition of currently-running infra": "167 `tradfi-bf-cme-ohlcv-1m-g0{1,2,3}-*` VMs were running at the time of
  this ruling... Disposition: **killed, not resumed**."

The observed NASDAQ/NYSE 2023/2024 VMs match the shape of exactly the out-of-scope, killed-not-resumed work.

## What I did NOT do

- Did not investigate who launched these VMs or why (out of scope for the task I was actually on).
- Did not kill, stop, or otherwise touch these VMs — per the standing 3-signal staleness-check rule, killing a live VM
  without confirming genuine staleness/authorization risk destroying real in-progress work, and I have no context on
  whether this is sanctioned.
- Did not confirm whether the CME ES/ETH/MBT/MET shards observed in the same fleet snapshot are correctly scoped (they
  appear to be, per the ruling's own table, but not independently re-verified against their actual date windows here).

## ROOT CAUSE CONFIRMED (2026-08-09 ~06:05Z) — `wave_launcher.py` hourly cron, exactly the failure mode the ruling named

`ps aux` on the `planning` VM shows `scripts/wave_launcher.py` actively running (PID 2318657, started 06:00:xx,
`WAVE_MAX_CONCURRENT=20`, invoked via a `/bin/sh -c cd deployment-service && ... python scripts/wave_launcher.py`
wrapper — a scheduled/cron-style invocation, not an interactive session). Its own log
(`/home/ubuntu/wave_launcher_cron.log` on `planning`) shows, this run:

```
CME year=2020 root=ES   args=--only-root ES --year 2020 --no-force-window --force   -> LAUNCH OK
CME year=2022 root=ETH  args=--only-root ETH --year 2022 --no-force-window --force  -> LAUNCH OK
CME year=2023 root=MET  args=--only-root MET --year 2023 --no-force-window --force  -> LAUNCH OK
NASDAQ year=2023 ... --no-force-window --force  (in progress at time of this note)
NYSE/CBOE year=2020..2025 ... --no-force-window --force  (queued in the same WAVE plan)
```

`gcloud compute instances list` immediately before/after confirms this **duplicated already-running CME shards**:
`tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260809-031341` (started 03:13) now has a sibling
`...-es-es-2020-20260809-060222` (started 06:02) — same root, same year, both RUNNING simultaneously. Same pattern for
`eth-eth-2022` and `met-met-2023`. This is the exact `wave_launcher.py` dedup key-mismatch bug already documented in
`issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`'s "Known relaunch gotchas" section — it's not
hypothetical, it's reproducing live, hourly, right now.

**This also explains why the original NASDAQ/NYSE out-of-scope wave (this doc's original observation) exists at all**:
it isn't a one-off relaunch by an unknown actor — `wave_launcher.py`'s own `WAVE:` plan for this run explicitly lists
`NASDAQ year=2023`, `NYSE year=2023/2024`, and `CBOE year=2020..2025` as targets, run with `--force`. The scope ruling
doc explicitly anticipated this: _"If a worker or an autonomous session (e.g. `wave_launcher.py`'s gap-driven dispatch)
would otherwise pick up one of these cells, treat it as `BLOCKED-OPERATOR-DECISION` citing this doc, not as ready
work."_ That guidance was never wired into `wave_launcher.py` itself or into its cron — the cron has continued
dispatching the out-of-scope cells (and duplicating the in-scope ones) every cycle since the ruling was written the same
day.

**Compounding impact on other in-scope work**: this cron's repeated `--force` launches keep the shared `tradfi-bf-*`
singleton lock (`launch-tradfi-backfill-vm.sh`'s `_check_singleton_lock`) continuously occupied, which is directly
blocking `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` todo #2's operator-authorized ES_OPT launch (>2hrs blocked
this session, lock count fluctuating 5-10 rather than converging to 0, because the cron keeps refreshing it). Unless
this cron is paused or fixed, the singleton lock may never naturally clear.

## Action items

- [ ] [INFRA] P1. **`BLOCKED-OPERATOR-DECISION`: pause or fix the `wave_launcher.py` cron on `planning`** (PID pattern
      confirmed via `ps aux | grep wave_launcher`, log at `/home/ubuntu/wave_launcher_cron.log`) so it (a) respects the
      2026-08-09 MVP-of-MVP scope ruling — skip CBOE/NASDAQ/NYSE/FX/commodity cells entirely until November 2026 rather
      than dispatching them with `--force`, and (b) fixes the dedup key-mismatch bug so it stops duplicating
      already-running CME shards. Options: (1) comment out / disable the cron entry until the code fix ships — fastest,
      fully reversible, but pauses legitimate CME progress too; (2) patch `wave_launcher.py`'s cell-selection to consult
      the scope-ruling doc's in-scope table before dispatch — correct fix, more code. Recommend (1) as an immediate
      stopgap + (2) as the follow-up fix, but this needs operator/infra sign-off since the cron is shared infra outside
      any one worker's task scope — not unilaterally touched by this session. Repo: deployment-service (fix) + whichever
      host/repo owns the cron install script (stopgap).
- [ ] [INFRA] P2. **Determine whether the NASDAQ/NYSE 2023/2024 relaunch (and the CME duplicates) should be individually
      killed** once the cron itself is paused/fixed (3-signal staleness check + operator sign-off — don't blind-kill
      live in-progress work). Repo: deployment-service.

## ACTION TAKEN (2026-08-09 ~06:08Z) — killed the live `wave_launcher.py` process (not any VM)

Between 06:02Z and 06:08Z the `tradfi-bf-*` RUNNING count climbed 5 → 6 → 7 → 10 → 12 → 14 → 17 → 18 (live-observed via
repeated `gcloud compute instances list`) as `wave_launcher.py`'s cron invocation worked through its out-of-scope
`WAVE:` plan (CBOE/NASDAQ/NYSE year-shards, per the log excerpt above). This is the same growth pattern that produced
the 167-VM fleet the operator killed in the original 2026-08-09 ruling, actively reproducing in real time.

I killed the two live processes for this invocation (`kill -TERM`, confirmed dead 3s later, no remaining
`wave_launcher.py` process on `planning`):

```
2318645  /bin/sh -c cd deployment-service && ... python scripts/wave_launcher.py >> ~/wave_launcher_cron.log 2>&1
2318657  .venv/bin/python scripts/wave_launcher.py   (the actual dispatcher, WAVE_MAX_CONCURRENT=20)
```

**What I did NOT do**: did not touch the cron _installer/schedule_ (so it will fire again next cycle unless someone
disables it — that's the P1 action item above, needs proper investigation of how it's installed before editing), did not
delete or stop any already-launched VM (the ~18-19 VMs already created by this run, in-scope or not, are left alone per
the staleness-check rule — some may hold real in-progress captured data). This is a stopgap that buys time, not a fix —
the underlying cron will re-run and reproduce this unless the P1 action item is completed first.

**Why I acted instead of only documenting**: the growth was actively worsening in real time (near-doubling every
~1-2min), directly reproducing a failure mode the operator had already explicitly ruled out same-day, and killing a
dispatcher _process_ (not a data-bearing VM) is a narrow, fully reversible action — it can be restarted by anyone,
anytime, and touches no captured data. This matches the standing "confirmed runaway process... may be killed...
investigate + doc it, don't wait on approval" allowance, applied here to the dispatcher rather than to the individual
in-flight VMs (which stay hands-off per the separate staleness-check rule).

## Progress Log

- 2026-08-09: filed as a passive observation during an unrelated ES_OPT monitoring session. Not investigated further.
- 2026-08-09 ~05:20Z: escalating priority context — this NASDAQ/NYSE wave (5 of the 10 `tradfi-bf-*` VMs still RUNNING)
  is now directly co-occupying the shared Databento singleton lock with
  `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` todo #2's operator-authorized, in-scope ES_OPT launch, which has
  been blocked >1hr this session alone (lock flat at 10 VMs across two full 8-10min poll windows, zero clears).
  SSH-verified the in-scope CME `g01` shards (ES/ETH/MBT/MET) are alive and genuinely progressing (not zombied —
  confirmed a fresh 2020-06-03..09 chunk fetch mid-run), so this isn't a stuck-process false lock; it's a real, slow,
  multi-hour full-year backfill that the out-of-scope NASDAQ/NYSE wave is needlessly extending queue time on. Still not
  touching these VMs (no kill, no `--force` bypass of the singleton lock — a shared-account rate-limit collision risks
  corrupting the very run this doc is trying to protect). Flagging that the action item below now blocks P0 authorized
  work, not just a hygiene concern.
