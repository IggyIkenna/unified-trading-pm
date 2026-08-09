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
priority: P2
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

## Action items

- [ ] [INFRA] P2. **Determine whether the NASDAQ/NYSE 2023/2024 relaunch is authorized** (a scope-ruling amendment, an
      operator override, or a genuine violation) and act accordingly (let it run if authorized; kill per the 3-signal
      staleness check + operator sign-off if it's a genuine violation of the November-2026 gate). Repo:
      unified-trading-pm (cross-check against any newer scope-ruling doc) + deployment-service (identify the
      launcher/actor if a violation).

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
