---
doc_type: issue
title: >-
  New out-of-scope CME commodity-futures wave (CL/GC/HG/NG/PA/PL) discovered live 2026-08-11 — NOT from the known,
  still-paused wave_launcher.py cron
summary: >-
  While checking live `tradfi-bf-*` fleet state to execute an operator-approved kill of the 14 out-of-scope VMs named in
  `tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md`, found that those specific 14 have
  already completed/cleared naturally (none present in the 2026-08-11 live snapshot). Instead, a DIFFERENT set of 9
  `tradfi-bf-cme-ohlcv-1m-*` VMs is running — all commodity futures (CL crude oil, GC gold, HG copper, NG nat gas, PA
  palladium, PL platinum), 2020/2021 date windows — which `tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`
  explicitly names as out-of-scope-until-November ("6M/CL/CT/HG commodities... entirely out of this scope... killed, not
  resumed"). Confirmed the known root cause (the `uts-prod-tradfi-wave-launcher-cron` Cloud Scheduler job) is still
  `state: PAUSED` as of this check — so this is a NEW, unidentified launch path, not a recurrence of the already-tracked
  bug. Not killed — outside the scope of what the operator explicitly approved (which named a specific, now-moot, set of
  VMs), and the launch source is unknown, so a 3-signal staleness check + operator sign-off on kill/no-kill is needed
  before touching them, per the sibling doc's own precedent.
status: archived
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [tradfi, scope-ruling, vm, backfill, possible-violation]
related:
  [
    /plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md,
    /plans/active/issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md,
    /plans/active/issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md,
  ]
created: "2026-08-11"
author: main
priority: P1
parent_epic: tradfi_master
source: >-
  Live `gcloud compute instances list --filter='name~"^tradfi-bf-"'` snapshot (via AWS SSM to the orchestrator VM,
  read-only, ubuntu login shell for ambient GCP identity) taken 2026-08-11 while attempting to execute an
  operator-approved kill of a different, now-completed VM set.
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

# New out-of-scope CME commodity-futures wave — source unknown, cron confirmed paused

> **ARCHIVED 2026-08-12** — all 3 todos resolved. Launch source root-caused to the host `wave_launcher.py` cron
> consulting a stale `MVP_SCOPE["tradfi"].underliers` SSOT (slot-31); 3-signal staleness check found all 7 VMs alive,
> kill/no-kill routed to the operator via BLK-3412aed6 (slot-26); SSOT narrowed to drop GC/SI/PL/PA/NG/CL/HG —
> `unified-api-contracts@671fe035` (slot-32). No further action pending; this session only flipped the last checkbox and
> archived (the code todo was already shipped but left unflipped).

## Observation (2026-08-11)

Live snapshot (read-only, via SSM to the orchestrator VM `i-0c9b283b31d6b5ca7`, `sudo -u ubuntu -i` login shell for
ambient GCP credentials — the bare SSM shell has no active gcloud account, ubuntu's login shell does):

```
tradfi-bf-cme-ohlcv-1m-btc-2021-20260811-000908  asia-northeast1-c  RUNNING
tradfi-bf-cme-ohlcv-1m-cl-2020-20260811-030226   asia-northeast1-c  RUNNING
tradfi-bf-cme-ohlcv-1m-es-2021-20260811-030452   asia-northeast1-c  RUNNING
tradfi-bf-cme-ohlcv-1m-gc-2020-20260811-030247   asia-northeast1-c  RUNNING
tradfi-bf-cme-ohlcv-1m-gc-2021-20260811-001046   asia-northeast1-c  RUNNING
tradfi-bf-cme-ohlcv-1m-hg-2021-20260811-030536   asia-northeast1-c  RUNNING
tradfi-bf-cme-ohlcv-1m-ng-2021-20260811-060754   asia-northeast1-c  RUNNING
tradfi-bf-cme-ohlcv-1m-pa-2020-20260811-030324   asia-northeast1-c  RUNNING
tradfi-bf-cme-ohlcv-1m-pl-2020-20260811-060624   asia-northeast1-c  RUNNING
```

BTC (2021) and ES (2021) are in-scope per `tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`'s table (CME BTC/ETH
futures full history; ES full history). The other 7 — CL, GC (×2 years), HG, NG, PA, PL — are commodity futures,
explicitly named out-of-scope-until-November by that same doc: "Any FX/commodity futures backfill not named above (the
currently-running `tradfi-bf-cme-ohlcv-1m-g0{1,2,3}-*` fleet — 6A/6B/6C/6E/6J/6L currency futures, 6M/CL/CT/HG
commodities — is entirely out of this scope) ... killed, not resumed."

## Why this is NOT the already-tracked `wave_launcher.py` bug

`tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md` root-caused a recurring violation to the
`uts-prod-tradfi-wave-launcher-cron` Cloud Scheduler job (`0 */3 * * *` UTC → Cloud Run Job
`uts-prod-tradfi-wave-launcher`) and confirmed it `state: PAUSED` as of 2026-08-09 ~13:06Z. Re-checked live 2026-08-11:
**still `state: PAUSED`, `userUpdateTime: 2026-06-24` (predates the 2026-08-09 pause action, meaning it has not been
toggled since)**. The 14 out-of-scope VMs that same doc's Progress Log left running pending a "sunk-cost vs
ongoing-violation" operator decision are **not present in this snapshot** — they completed naturally in the ~2 days
since. This commodity wave is a _different_ set of instrument roots, a _different_ naming shape (no `g0N-` bundling
artifact, matching the fixed single-root launcher naming per that doc's todo 1), and exists despite the confirmed-paused
cron — so it did not come from that mechanism. Launch source not yet identified (not investigated further — out of scope
for what this session was doing; flagging for whoever picks this up).

## What was NOT done

- Did not kill, stop, or otherwise touch any of the 7 out-of-scope VMs. The operator's 2026-08-11 "kill now" decision
  was scoped to the specific 14 VMs named in
  `tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md` — those are gone; this is a different,
  newly-discovered set, and per that doc's own precedent (3-signal staleness check + operator sign-off before killing
  genuinely-alive out-of-scope work), extending the same approval to an unrelated discovery isn't warranted without at
  least a staleness check and a fresh sign-off.
- Did not investigate the launch source (who/what started these 7 VMs, given the known cron is paused).
- Did not run a 3-signal staleness check (heartbeat/log/write-activity) on any of the 7.

## Action items

- [x] ✅ [INFRA] P1. Identify the launch source for the 7 out-of-scope commodity VMs (CL/GC×2/HG/NG/PA/PL) given the
      known `wave_launcher.py` cron is confirmed paused — check for a second scheduler job, a manual dispatch, an
      AO-dispatched todo that shouldn't have targeted these roots, or another automation path. Repo: deployment-service.
      — completed 2026-08-11 (slot-31, no code shipped — pure documentation-linkage; identical root cause independently
      documented already, this todo cross-links it). **IDENTIFIED — not a mystery/second automation path.** The launch
      source is the SAME live mechanism `tradfi_satellite_ao_dispatch_batch11_2026_08_10.md` todo 10 already
      root-caused: a **HOST cron (`0 */3 * * *`) on the monitor host** running `wave_launcher.py` from a live git
      checkout (self-updates via `git pull` each tick) — NOT the Terraform-managed Cloud Scheduler job
      `uts-prod-tradfi-wave-launcher-cron` (confirmed still `state: PAUSED`, `userUpdateTime: 2026-06-24`, unchanged) /
      Cloud Run Job `uts-prod-tradfi-wave-launcher` (dormant `:latest` image, no execution since June). No second
      scheduler, no manual `gcloud run jobs execute`, no AO-dispatched todo — searched `plans/active/` +
      `terraform/gcp/wave_launcher_scheduler.tf` (single Scheduler resource defined) for any alternate trigger; none
      found. **Why the 2026-08-10 scope-fix didn't stop these 7**: `deployment-service@48f55e934b` (landed
      2026-08-10T17:33:42Z, BEFORE all 7 VMs' 2026-08-11 03:02–06:07Z launch timestamps) correctly changed
      `wave_launcher.py::_cme_root_universe()` to consult
      `unified_api_contracts…mvp_scope.MVP_SCOPE["tradfi"].underliers` instead of a hardcoded root list — but
      `MVP_SCOPE["tradfi"].underliers`
      (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/_mvp_scope_rules.py:704-712`) itself STILL
      lists `GC/SI/PL/PA/NG/CL/HG` as in-scope FUTURE-cell underliers, per the older 2026-06-24 "commodity roots backing
      a Binance tradfi-perp" decision — it was never narrowed to reflect the 2026-08-09 scope ruling
      (`tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` line 108-109: FX/commodity futures "entirely out of
      this scope... being killed" until November). So the host cron IS now correctly consulting the SSOT the fix pointed
      it at — the SSOT itself is stale, not the consulting code. **This is an ongoing, self-perpetuating violation**:
      every future 3-hourly tick will keep re-launching/replacing these same 7 commodity roots until
      `MVP_SCOPE["tradfi"].underliers` is narrowed. See new P0 follow-up todo below. Repo: deployment-service (launch
      mechanism), unified-api-contracts (stale SSOT — the actual fix surface).
- [x] ✅ [DATA] P0. **Narrow `MVP_SCOPE["tradfi"].underliers`** (unified-api-contracts,
      `unified_api_contracts/canonical/crosscutting/_mvp_scope_rules.py:704-712`) to drop `GC/SI/PL/PA/NG/CL/HG` per the
      2026-08-09 scope ruling (`tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`: commodity futures "entirely
      out of scope" until November) — this is the ACTUAL fix `wave_launcher.py@48f55e934b` was supposed to enable but
      didn't, because it consults this SSOT and the SSOT was never updated. Without this, the host cron will keep
      relaunching commodity-root VMs every 3 hours indefinitely, regardless of any kill decision on the
      currently-alive 7. Coordinate with the operator's BLK-3412aed6 kill/no-kill answer first (if "no-kill for
      sunk-cost", the underliers narrowing should still land to stop FUTURE relaunches — only the currently-alive 7 are
      exempted). Verify no other consumer of `MVP_SCOPE["tradfi"].underliers` (e.g. catalogue MVP-tagging, completeness
      denominators) regresses from the narrowing — cite in the commit. Repo: unified-api-contracts. — completed
      2026-08-11 (slot-32): `unified-api-contracts@671fe035` narrowed `underliers` (dropping GC/SI/PL/PA/NG/CL/HG) +
      `MVP_CME_EXCHANGE_CODES` derived from it; commit message documents the no-regression verification (wave_launcher
      has no root-specific test assertions, MTDS symbol lookups are derivation-based). Checkbox flip only this session
      (code was already shipped, todo was left unflipped) — verified `671fe035` on `origin/live-defi-rollout`.
- [x] ✅ [INFRA] P2. Run the 3-signal staleness check (GCS heartbeat blob mtime, run.log tail activity, active data
      writes) on each of the 7 VMs once the source is identified, then route the kill/no-kill call per the same
      sunk-cost-vs-ongoing-violation framing as the sibling doc — do not blind-kill. — completed 2026-08-11 (slot-26):
      all 7 VMs ALIVE+progressing; determination + kill/no-kill routed via BLK-3412aed6.

## Progress Log

- **2026-08-11**: filed after discovering this live during an unrelated kill-execution attempt (see Observation above).
  Not investigated further this session.
- **2026-08-11 ~09:00Z, slot-26 (dispatched P2 — 3-signal staleness check)**: Completed the 3-signal staleness check on
  all 7 out-of-scope commodity VMs (cl-2020, gc-2020, gc-2021, hg-2021, ng-2021, pa-2020, pl-2020) at ~2026-08-11T08:57Z
  (read-only via UTL `cloud_interface`; no VMs touched, nothing written). **Determination: ALL 7 GENUINELY ALIVE +
  PROGRESSING — none qualify for a staleness-based kill.**
  - **Signal 1 — GCS heartbeat blob** (`gs://deployment-scripts-central-element-323112/vm-heartbeat/<vm>.txt` mtime):
    all 7 within 09–50s of check time (08:56:52Z–08:57:39Z) — inside the sibling doc's 60s alive threshold.
  - **Signal 2 — run.log tail activity**: all 7 `vm-logs/<vm>/run.log` actively growing (last_modified 08:55:12Z–
    08:57:13Z) with `PIPELINE_HEARTBEAT` (~60s cadence) + `RESOURCE_SAMPLE` (~30s, cpu≈100–190%) + `Pre-flight` /
    `DatabentoAdapter` processing lines; `WATCHDOG_TRACE.log` also fresh.
  - **Signal 3 — active data writes**: `StreamingParquetWriter` uploading to PROD
    `market-data-tick-tradfi-prd-central-element-323112/raw_tick_data/by_date/day=…` (e.g. gc-2021 24,558 rows
    day=2021-09-10 @08:56:30Z; pl-2020 multiple uploads day=2020-05-28 @08:55:43Z), `ManifestWriter` per-VM shard
    updates (`_index/per_vm/<vm>-c45.parquet`), monotonic `PROGRESS.json` (cl 2020-11-03 / gc-2020 2020-11-03 / gc-2021
    2021-09-09 / hg 2021-06-17 / ng 2021-03-04 / pa 2020-10-13 / pl 2020-06-02). Canonical
    `pipeline_mode=batch_databento` paths; no duplicate-pair race (one VM per root+year).
  - **Routing**: kill/no-kill filed to operator via `/blocked` (**BLK-3412aed6**) — same sunk-cost-vs-ongoing-violation
    framing as the sibling doc. All-alive means no autonomous staleness-kill is warranted; the ruling doc's "killed, not
    relaunched" commodity language vs. the sunk-cost + November-needed canonical data is the operator's judgment call.
    No VMs touched. P1 (launch-source identification) remains open and is the critical follow-up — the source is still
    unidentified (known cron confirmed PAUSED), so the wave could recur independently of this decision.
- **2026-08-11, slot-31 (dispatched P1 — launch-source identification)**: Identified — the live host cron already
  root-caused in `tradfi_satellite_ao_dispatch_batch11_2026_08_10.md` todo 10 (not a new mechanism); grepped
  `plans/active/` + `terraform/gcp/` for any second scheduler/trigger, found none. Root cause of why the 7 commodity VMs
  launched DESPITE the 2026-08-10 17:33 scope-fix (`deployment-service@48f55e934b`): the fix correctly points
  `wave_launcher.py` at `MVP_SCOPE["tradfi"].underliers`, but that SSOT itself still lists GC/SI/PL/PA/NG/CL/HG as
  in-scope (stale vs the 2026-08-09 ruling — never narrowed). Filed new P0 todo to narrow the SSOT — that's the actual
  remaining fix; without it the host cron will keep relaunching commodity roots every 3h regardless of the BLK-3412aed6
  kill/no-kill answer on the currently-alive 7. No code changed this session (investigation + doc only).
