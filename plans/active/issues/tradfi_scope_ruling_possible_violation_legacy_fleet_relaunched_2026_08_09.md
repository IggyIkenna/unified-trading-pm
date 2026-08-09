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

- [x] ✅ [INFRA] P1. **`BLOCKED-OPERATOR-DECISION`: pause or fix the `wave_launcher.py` cron on `planning`** — STOPGAP
      (option 1) confirmed LIVE 2026-08-09 ~13:06Z:
      `gcloud scheduler jobs describe uts-prod-tradfi-wave-launcher-cron --location=asia-northeast1` reads
      `state: PAUSED` (job at `deployment-service/terraform/gcp/wave_launcher_scheduler.tf`). No audit-log entry was
      retrievable to attribute who/when paused it, and the follow-up code fix (option 2 — patch cell-selection to
      consult the scope-ruling table) is still NOT shipped, so this is the reversible stopgap only, not the durable fix
      — if anyone re-enables the job before option 2 lands, the exact same violation reproduces. Leaving option 2 as a
      still-open follow-up (not re-added as a new checkbox here since it duplicates this item's own text — track it via
      re-opening this line if the job is ever re-enabled without the code fix).
- [ ] [INFRA] P2. **Determine whether the NASDAQ/NYSE 2023/2024 relaunch (and the CME duplicates) should be individually
      killed** once the cron itself is paused/fixed (3-signal staleness check + operator sign-off — don't blind-kill
      live in-progress work). Repo: deployment-service. **3-signal check DONE 2026-08-09 ~13:07Z (slot-7) — see Progress
      Log; escalated final kill/no-kill call to operator via `/blocked` BLK-19380fd8, not resolved here.**

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
- **2026-08-09T~09:00Z, slot-22**: **RECURRED, confirming the P1 action item is still unfixed.** While monitoring the
  singleton lock for `tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`'s ES_OPT
  verify/retry todo, observed the exact same `wave_launcher.py` shape fire again: `ps aux` showed PID 1292336
  (`/bin/sh -c` cron wrapper) / 1292342 (actual dispatcher), started 09:00Z — the ~06:08Z kill only stopped that
  invocation, not the underlying cron/timer, exactly as that entry predicted. `/home/ubuntu/wave_launcher_cron.log`
  shows it had already fired `LAUNCH OK` for CME year=2020 root=ES (duplicate of the already-running
  `...-es-2020-...-031341`-lineage VM), CME year=2022 root=ETH (duplicate), CME year=2023 root=MET (duplicate), NASDAQ
  year=2023 (out-of-scope), and was mid-launch on NYSE year=2023 (out-of-scope) when I acted — confirmed live via
  `gcloud compute instances list --filter='name~"^tradfi-bf-"'` (6 CME + 5 NASDAQ-2023 + 1 NYSE-2023 = 12 VMs). Applied
  the same narrow, reversible, precedented action as the ~06:08Z entry: `kill -TERM` on the exact 2 PIDs
  (1292336, 1292342) — confirmed dead 3s later (`ps aux | grep wave_launcher` empty). Did NOT touch the cron/timer
  installer itself (still don't know its exact mechanism — systemd timer vs. crontab vs. something else — that's still
  what the P1 action item below needs to actually close this out). Did NOT touch any already-launched VM (same
  staleness-check posture as before). This is now a **confirmed-recurring** pattern (2 occurrences, ~3h apart: ~06:08Z
  and ~09:00Z) — the reactive kill is a stopgap that will need to repeat every cycle until the P1 fix lands; flagging
  this doc's P1 as higher-urgency given the repeat, not re-triaging the priority itself (already P1).
- **2026-08-09 ~12:47Z, slot-28 (dispatched todo 2 — determine whether the relaunch/duplicates should be individually
  killed)**: root-caused the actual mechanism (prior entries hadn't identified it):
  `deployment-service/terraform/gcp/ wave_launcher_scheduler.tf` wires this as a **GCP Cloud Scheduler job
  (`0 */3 * * *` UTC) → Cloud Run Job**, not a local cron/systemd timer on the `planning` host — confirmed no matching
  systemd timer (`systemctl list-timers --all`, 26 timers, none named wave/tradfi), no crontab entry visible, no GH
  Actions workflow reference. The observed local `ps aux` shell-wrapper PIDs in the prior two entries are the Cloud Run
  Job's container process, which happens to be reachable/visible from this shared host (same GCP project ambient
  credentials) — the 3h recurrence cadence (~06:08Z/~09:00Z/now) matches the Terraform schedule exactly, confirming this
  IS the wired scheduler, not an unknown rogue process. **Current live state (12:47Z), no wave_launcher process running
  (this tick already completed and exited — one-shot Cloud Run Job task, not a persistent daemon)**: 27 `tradfi-bf-*`
  VMs running — the highest count observed across all entries in this doc. Breakdown: 2 confirmed CME duplicate pairs
  (same root+year, two different launcher naming shapes both RUNNING: `cme-ohlcv-1m-es-2020` +
  `cme-ohlcv-1m-g01-es-es-2020`; `cme-ohlcv-1m-met-2023` + `cme-ohlcv-1m-g01-met-met-2023`) + 4 non-duplicated CME
  shards (mbt-2024, met-2024, met-2025 — met-2025 is a NEW out-of-scope year not seen in prior entries) + 19
  out-of-scope equities VMs: NASDAQ 2023(×3)/2024(×4)/**2025(×4, NEW — first appearance of 2025 in this doc)** + NYSE
  2023(×4)/2024(×5). The out-of-scope footprint is GROWING each cycle (12→18-19→27), not stabilizing, and has now spread
  to a 3rd out-of-scope year (2025) beyond the ruling doc's original 2023/2024 observation. **Did NOT kill anything this
  pass** (no process is currently live to kill; the reactive-kill stopgap only ever catches the process mid-run, and per
  the 3-signal staleness rule + this doc's own repeated "operator sign-off needed" framing, individually killing the 19+
  already-running out-of-scope VMs is a judgment call this session should not make unilaterally, even though I now have
  the technical means to (the ambient `unified-trading-sa` GCP identity that ran `gcloud compute instances list` above
  also holds `cloudscheduler.admin` + `compute.admin`, so pausing the Cloud Scheduler job and/or deleting the VMs are
  both mechanically self-service per `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` —
  deliberately not exercised here because the gap is a SCOPE/AUTHORIZATION judgment call, not a permission gap that
  doc's self-service rule covers). Filing a `/blocked` question now (see next entry) since three independent occurrences
  (06:08Z, 09:00Z, this one) have each independently deferred the actual pause-or-fix decision without ever routing it
  to a real operator answer — the passive doc-logging pattern was not surfacing this for a decision.
- **2026-08-09 ~13:07Z, slot-7 (dispatched todo 2 fresh — no evidence a prior `/blocked` call from the ~12:47Z entry
  above actually landed; no answer visible on this slot's boot/heartbeat, no BlockedRow reachable to confirm one way or
  the other)**: **Prerequisite now met** —
  `gcloud scheduler jobs describe uts-prod-tradfi-wave-launcher-cron --location=asia-northeast1` confirms
  `state: PAUSED` (checked into P1 above). **Fresh fleet snapshot (13:06Z)**: 21 `tradfi-bf-*` VMs running (down from
  the 27 at 12:47Z — some completed naturally in the interim, consistent with the paused cron meaning no new launches):
  2 confirmed CME duplicate pairs (`cme-ohlcv-1m-es-2020` + `cme-ohlcv-1m-g01-es-es-2020`; `cme-ohlcv-1m-met-2023` +
  `cme-ohlcv-1m-g01-met-met-2023`) + 3 non-duplicated CME (mbt-2024, met-2024, met-2025) + 8 NASDAQ (2023×2, 2024×3,
  2025×3) + 6 NYSE (2023×3, 2024×3) = 19 out-of-scope equities. **Ran the 3-signal staleness check** (heartbeat blob
  age, run.log tail, active data writes) on one sampled VM per category
  (`tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260809-090109`, `tradfi-bf-nasdaq-ohlcv-1m-2023-d01-20260809-120319`,
  `tradfi-bf-nyse-ohlcv-1m-2023-d01-20260809-120502`, plus `tradfi-bf-cme-ohlcv-1m-es-2020-20260809-120142` for the
  other CME-duplicate lineage): ALL FOUR signal ALIVE, not stale —
  `gs://deployment-scripts-central-element-323112/vm-heartbeat/<vm>.txt` mtimes within 60s of check time on every
  sample; `vm-logs/<vm>/run.log` actively growing (new bytes every check) with real `PIPELINE_HEARTBEAT` +
  `StreamingParquetWriter: uploaded ... ticks.parquet (N rows)` lines timestamped seconds before the check — i.e. these
  are genuinely mid-backfill, not zombied/orphaned processes. **Determination**: none of the 21 qualify for an
  autonomous staleness-based kill (all alive + progressing); the remaining question — whether to kill genuinely-alive
  but out-of-scope/duplicate work now that the cron can't spawn more — is a scope/cost-tradeoff judgment call, not a
  technical one, so per this doc's own standing framing (and the craft's VM-delete guardrail) it stays operator-gated.
  Filed a fresh `/blocked` (`BLK-19380fd8`) with this evidence + 3 options (kill all 21 / let all finish naturally since
  the cron is paused so no further violation accrues / kill only the 2 confirmed CME duplicate pairs and let the 19
  NASDAQ/NYSE finish), recommending option C (duplicates are unambiguous double-spend; the NASDAQ/NYSE premature-year
  work is out-of-scope-but-not-wasteful once already in flight). Did not touch any VM or the scheduler job. This P2 todo
  stays open pending the operator's answer — the determination (documented above) is complete, the kill DECISION is not
  mine to make.
- **2026-08-09 ~13:15Z, slot-7 — operator INTERIM answer on `BLK-19380fd8` (final decision on the non-duplicate VMs
  still PENDING separately)**: operator split the decision by risk category. (1) **CME duplicate pairs are a
  DATA-CORRECTNESS issue, not just scope** — two processes concurrently writing the same shard risks a race / silently
  corrupted or overwritten output, independent of the scope ruling; directed to kill the duplicate side now since the
  legitimate/already-running `g01-*` side is confirmed progressing and nothing legitimate is lost. (2) The remaining
  purely-out-of-scope, non-duplicate VMs are a sunk-cost-vs-ongoing-violation budget tradeoff the operator is deciding
  separately (already flagged to them directly outside this doc) — explicitly NOT auto-resolved by the scope ruling
  alone; leave them running pending that separate answer. **Action taken**: re-confirmed both duplicate pairs still
  RUNNING (`tradfi-bf-cme-ohlcv-1m-es-2020-20260809-120142` + `tradfi-bf-cme-ohlcv-1m-met-2023-20260809-120247` were the
  later-started (`12:0x` UTC) duplicate side vs. the earlier-started (`09:0x` UTC) `g01-*` originals), then
  `gcloud compute instances delete tradfi-bf-cme-ohlcv-1m-es-2020-20260809-120142 tradfi-bf-cme-ohlcv-1m-met-2023-20260809-120247 --zone=asia-northeast1-c --quiet`
  — both confirmed `Deleted`. The `g01-es-es-2020` / `g01-met-met-2023` originals are untouched and still RUNNING.
  **Current fleet for the operator's pending sunk-cost decision (13:16Z, post-dedup-kill)**: 16 `tradfi-bf-*` VMs total
  — 2 in-scope `g01-*` (keep) + **14 out-of-scope, non-duplicate** (down from the 19 cited to the operator ~15min prior
  — 5 completed naturally in the interim under the now-paused cron): 3× CME new-year (mbt-2024, met-2024, met-2025) + 6×
  NASDAQ (2023-d01, 2024-d02/d04/d05, 2025-d02/d04) + 5× NYSE (2023-d01/d03, 2024-d02/d04/d05). All 14 are
  `e2-highmem-16` (16 vCPU / 128GB) on SPOT provisioning. Rough burn estimate (SPOT e2-highmem-16 list-price-derived,
  NOT a Billing-API-verified figure): ~$0.25-0.35/VM-hr → **~$3.50-4.90/hr aggregate** for the 14, on top of whatever
  Databento API-call spend they're each individually accruing (not measured here). No further action taken on these 14 —
  waiting on the operator's separate answer. This P2 todo's duplicate-VM sub-item is now closed (evidence above); the
  NASDAQ/NYSE/CME-new-year sub-item stays open pending that answer.
