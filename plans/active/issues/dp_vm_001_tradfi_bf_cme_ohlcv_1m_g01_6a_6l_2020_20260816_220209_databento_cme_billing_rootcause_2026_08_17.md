---
doc_type: issue
title:
  DP-VM-001 exit_code=137 on tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-220209 is NOT a generic stall —
  run.log proves the proximate cause is the already-tracked Databento CME/GLBX.MDP3 402 billing block; corrects the
  same-shard sibling docs' "poison instrument" hypothesis; do NOT relaunch until billing resolves
summary: >-
  Escalation agt-5af8eb (wall_type=data_pipeline_failure, DP-VM-001, dispatched to slot 4, 2026-08-16/17) reported VM
  `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-220209` (asset_group=tradfi, shard `g01-6a-6l-2020`, INSTRUMENT_IDS=
  6A/6B/6C/6E/6J/6L FUT+OPT) terminated exit_code=137, dispatcher-classified as stall-induced (watchdog kill), not
  OOM. Unlike the two same-shard sibling docs filed earlier the same day
  (`/plans/archive/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_15.md`,
  `dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_16.md` — both of which
  explicitly did NOT pull `run.log`), this worker DID read the VM's `run.log`
  (`gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log`, via the UTL/SDK-style GCS read, never
  subprocess). It shows: progress was monotonic through `2020-06-09` (23/53 chunks, per `PROGRESS.json`), then on
  `2020-06-10` the process hit `DatabentoAdapter: GLBX.MDP3/ohlcv_1s failed [402]: 402 account_delinquent_invoice`
  (CME dataset), wrote a partial manifest (`SHARD_INCOMPLETE ... missing: ['CME']`), then made no further progress
  for 3903s (> the 3900s stall threshold) until the in-VM watchdog declared `WORKER_STALLED` and self-terminated
  (`exit_code=137`). This is the SAME already-tracked, `status: blocked`, P0 issue
  (`tradfi_databento_account_billing_suspended_2026_08_09.md`) — CME/`GLBX.MDP3` specifically, last confirmed live
  2026-08-15 04:39:56Z and 2026-08-15 (IS reference-data path); this run.log is a fresh, direct reconfirmation at
  2026-08-16T23:11:13Z, ~19h later, same dataset, same 402 signature. **This is not a code bug to fix and not a
  shard-specific poison-instrument issue** — it is the vendor billing block already gated `BLOCKED-OPERATOR-DECISION`
  in the P0 doc. The two sibling docs' "possible shard-specific poison instrument/date" hypothesis (their Todo 2,
  neither of which pulled `run.log`) is corrected here: the actual cause is dataset-wide (GLBX.MDP3/CME), not
  shard-specific — `g01-6a-6l-2020` just happens to need CME data past 2020-06-09, same as any other CME-sourced
  shard would. Per RB-INFRA-RELAUNCH, did NOT relaunch — a relaunch would blindly retry the exact same billing wall.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [deployment-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [dp-vm-001, exit-code-monitor, tradfi-bf-cme, databento, billing, root-cause-correction, operator-decision, page]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md,
    /plans/archive/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_16.md,
    /plans/archive/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/tradfi_bf_cme_ohlcv_1m_relaunch_dispatch_budget_hit_2026_08_16.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
context_scope: [/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md, /codex/15-runbooks/incidents/rb_infra_relaunch.md, /codex/02-data/tradfi-databento-sourcing-ssot.md, /plans/active/tradfi_satellite_ao_dispatch_batch15_2026_08_17.md, deployment-service/deployment_service/data_pipeline_monitors/_gcs.py, deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py]
created: "2026-08-17"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Escalation agt-5af8eb (wall_type=data_pipeline_failure, dispatched to slot 4). Context: "VM
  tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-220209 terminated with exit_code=137 (stall-induced SIGKILL, not
  OOM) — captured did not complete cleanly... RELAUNCH vm=... launcher=(resolve via launcher_registry)
  deployment_id=? asset_group=tradfi." No separate audit CSV attached. This worker read `LAUNCH_PARAMS.json`,
  `PROGRESS.json`, and the tail of `run.log` from GCS (SDK reads, `deployment-scripts-central-element-323112`
  bucket) before deciding, per the runbook's "read the registries, do NOT re-derive args by hand" step and its
  wrapper/replacement checks — found no supervising wrapper for this launcher (`launch-tradfi-bf-cme-ohlcv-1m.sh` is
  directly registered in `launcher_registry.py`, no `*-historical-*` wrapper exists for it) and confirmed via
  `gcloud compute instances list` that no `g01-6a-6l-*` (any year) instance exists anywhere in the current
  39-instance live `tradfi-bf-cme-ohlcv-1m-*` fleet (a fresh wave launched ~2026-08-17T00:06-00:15Z) — this shard is
  not being retried by anything else right now.
---

# DP-VM-001 tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-220209 — root cause is the tracked Databento CME billing block, not a stall to fix or relaunch

## What happened

- VM: `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-220209` (asset_group=tradfi, `VENUE=CME`,
  `START_DATE=2020-01-01`, `END_DATE=2020-12-31`, `INSTRUMENT_IDS=6A.FUT;6A.OPT;6B.FUT;6B.OPT;6C.FUT;6C.OPT;6E.FUT;
  6E.OPT;6J.FUT;6J.OPT;6L.FUT;6L.OPT`, `DEPLOYMENT_ENV=prod`, `ZONE=asia-northeast1-a` — read directly from
  `LAUNCH_PARAMS.json`).
- `PROGRESS.json`: `last_completed_date=2020-06-09`, `monotonic=true`, `last_chunk_seen=23/53` — the shard was
  making genuine, monotonic progress; this is NOT a hang-from-the-start / poison-instrument-at-launch pattern.
- `run.log` tail (verbatim, timestamps UTC):
  ```
  2026-08-16 23:11:13,102 WARNING DatabentoAdapter: GLBX.MDP3/ohlcv_1s failed [402]: 402 account_delinquent_invoice
  Unable to submit the request because there is an unpaid invoice.
  documentation: https://databento.com/docs/portal/billing
  2026-08-16 23:11:13,103 INFO DatabentoAdapter.download_batch_df: CME 2020-06-10 — 0 records
  2026-08-16 23:11:13,104 WARNING market-tick-data-service: SHARD_INCOMPLETE date=2020-06-10 asset_group=TRADFI — expected 1 venues, wrote 0, missing: ['CME']
  2026-08-16 23:11:13,180 WARNING Incomplete batch for date=2020-06-10 — 1/1 venues missing: ['CME'] (writing partial manifest for completed venues)
  [vm-exec] command exited rc=137
  2026-08-16 23:11:17,474 INFO received signal 15 — initiating shutdown
  watchdog exiting iter=64 reason=stall
  ...
  [vm-exec] DEPLOYMENT_FAILED cause=stall reason=WORKER_STALLED mode=no-progress-marker stalled_for=3903 threshold=3900
  ```
- Sequence: shard progressed cleanly through 2020-06-09 → hit the CME/`GLBX.MDP3` 402 billing wall on 2020-06-10 →
  wrote an honest partial manifest for that date → made no further `PROGRESS.json` update for 3903s → the in-VM
  stall watchdog (threshold 3900s) killed it. The exit_code=137 the fleet monitor saw is the watchdog's own kill
  signal, correctly labeled "stall" by the monitor — but the watchdog itself only fired *because* the billing wall
  stopped forward progress, not because of an unbounded-HTTP-hang code defect.

## Why this corrects the sibling docs

Both same-shard sibling docs (`..._2026_08_15.md`, `..._2026_08_16.md`) explicitly recorded "did NOT pull `run.log`
content" and instead recommended (their Todo 2) diagnosing whether this is "a shared code defect" (bound the call
with `asyncio.wait_for`) or "a poison-instrument/date issue specific to this shard." Having now pulled `run.log` for
this third occurrence: **neither hypothesis is correct**. The proximate cause is the account-level/dataset-scoped
Databento billing block already tracked in `tradfi_databento_account_billing_suspended_2026_08_09.md`
(`status: blocked`, P0, recurred multiple times since 2026-08-09, last independently reconfirmed 2026-08-15). No
`asyncio.wait_for` bound would fix this — the adapter DID return promptly (a 402 response, not a hang); the
"stall" is the watchdog correctly firing because a paid-account precondition is false, not a hung call. No
per-shard isolation/skip fix is warranted either — CME data for ANY tradfi shard requiring dates the billing block
covers will hit the identical wall; `g01-6a-6l-2020` is not special.

## Why this is a PAGE (do-not-relaunch) case

- Per RB-INFRA-RELAUNCH, a relaunch is only warranted if the failure isn't a blind retry of the same known cause.
  Here it explicitly is: the root cause is diagnosed, already tracked, and still unresolved — relaunching this VM
  now would just re-fail identically once it reaches 2020-06-10 again.
- No supervising wrapper exists for `launch-tradfi-bf-cme-ohlcv-1m.sh` (grepped `deployment-service/scripts/vm/` —
  no `*-historical-*`/loop wrapper registered for this launcher).
- Live fleet check (`gcloud compute instances list --filter="name~'^tradfi-bf-cme-ohlcv-1m'"`, 2026-08-17 ~00:20Z):
  39 instances RUNNING/STOPPING/PROVISIONING across groups es/eth/g02-g06/met/mbt/nq/btc, all launched in a single
  fresh wave ~00:06-00:15Z the same window — but **zero** `g01-6a-6l-*` instances (any year) anywhere in that wave.
  This shard is not being retried by anything else right now, so there's no wrapper-race concern either way — it's
  simply correctly waiting on the billing block, same as this doc concludes it should.
- No `vm-census/relaunch-paged/vm/<this-vm-name>.json` marker exists (checked) — this VM was never previously
  adjudicated/suppressed; this is a fresh finding, not a repeat of an old suppressed page.

## What this worker did NOT do

- Did not relaunch `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-220209` or any other `tradfi-bf-cme-ohlcv-1m-`
  VM — the root cause is an operator-gated billing block, not something a relaunch fixes.
- Did not change `_MAX_RELAUNCH_DISPATCHES_PER_DAY` or any escalation/budget code — not applicable here.
- Did not independently re-verify whether the fresh 39-instance wave launched ~00:06-00:15Z will also hit the
  CME/GLBX.MDP3 wall for dates it hasn't yet captured (spot-checked one same-family VM,
  `tradfi-bf-cme-ohlcv-1m-es-2020-20260817-000606`, which completed `exit_code=0` with zero `DatabentoAdapter` log
  lines at all — plausibly a Tardis-sourced shard for that instrument, not informative either way about CME/
  Databento billing status). Flagging as unverified rather than guessing; whoever next touches the P0 billing doc
  should re-check whether any of that wave's shards independently confirm CME/Databento is still blocked or has
  been restored.

## Todos

- [ ] [OPERATOR] P1. **DUPLICATE OF `/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`**
      (status: blocked, verified 2026-08-21) — same underlying ask as
      that doc's existing P0 `[OPERATOR]` todo (pay the Databento invoice) — no new action needed beyond that doc; this doc exists to
      correct the sibling docs' hypothesis and record a fresh confirmation. Once billing is restored, the
      `g01-6a-6l-2020` shard (and its 2020-06-10-onward remainder) needs a fresh relaunch — not urgent to track
      separately, the family's normal backfill-completion sweep will pick it up once the AG billing gate lifts.
- [x] ✅ [BACKEND] P3. **EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-d99b5c) →
      `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` Todo 3.** Optional hardening, not blocking: the in-VM
      stall watchdog currently can't distinguish "hung call" from "correctly-fast-failing on a known
      billing/entitlement error" — both surface as generic `exit_code=137`/`WORKER_STALLED`. A cheap improvement
      would be to special-case a `402`/`account_delinquent` response into a distinct terminal state (e.g.
      `DEPLOYMENT_FAILED cause=billing_blocked`) so the fleet monitor and future escalations don't need to re-pull
      `run.log` to tell the two apart — every DP-VM-001 stall escalation for this family so far (three
      same-day/same-week incidents) has had to do this same manual run.log read.

## Progress Log

- 2026-08-17 (slot 4, data_pipeline_failure escalation agt-5af8eb): Read `LAUNCH_PARAMS.json`, `PROGRESS.json`, and
  the tail of `run.log` for the failed VM via GCS SDK reads (`deployment-scripts-central-element-323112` bucket,
  `vm-logs/<vm>/` prefix). Found the proximate cause is a Databento `GLBX.MDP3` (CME) `402 account_delinquent_invoice`
  at 2026-08-16T23:11:13Z, which stopped forward progress and triggered the in-VM stall watchdog 3903s later — not a
  generic hang and not shard-specific poison data. Cross-checked against the existing P0
  `tradfi_databento_account_billing_suspended_2026_08_09.md` (still `status: blocked`, last independently confirmed
  2026-08-15) — this is the same, still-unresolved block, now reconfirmed ~19h later on the same CME dataset.
  Checked for a supervising wrapper (none) and the live fleet (no `g01-6a-6l-*` instance anywhere in the current
  39-VM wave) before concluding a manual relaunch is not warranted. Did not relaunch. Filed this doc to correct the
  two same-shard sibling docs' "poison instrument" hypothesis and appended a fresh-confirmation entry to the P0
  billing doc's Progress Log (same edit session). No code changed.
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): **RECLASSIFY, per-todo split.** Todo 2
  (optional watchdog hardening) is bounded/deterministic — extracted, see checkbox above. Todo 1 (pay invoice) stays
  NA — verbatim duplicate of `tradfi_databento_account_billing_suspended_2026_08_09.md`'s own P0 OPERATOR todo. Doc
  stays `assigned_vm: NA`.
- **2026-08-17 (slot 6, data_pipeline_failure escalation agt-266fcc)**: Received a fresh DP-VM-001 escalation for
  `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260817-110153` (same shard token, `g01-6a-6l-2020`, as this doc's
  original occurrence — a re-launched attempt against the same 2020 CME shard), exit_code=137, family again at
  2/2 relaunch dispatches today. Checked `plans/active/issues/` for an existing open doc first — this one.
  Read `LAUNCH_PARAMS.json`/`PROGRESS.json`/`run.log` for this exact VM via GCS SDK (`download_from_storage`, no
  subprocess): `PROGRESS.json` shows monotonic progress to `2020-05-12` (19/53 chunks), then `run.log` shows the
  identical `GLBX.MDP3/ohlcv_1m|1s failed [402]: 402 account_delinquent_invoice` signature recurring from
  `2020-01-03` onward (747 matching 402/429/SHARD_INCOMPLETE lines total), with `SHARD_INCOMPLETE` partials
  written honestly for each blocked date, then a burst of `429 transient error` retry/backoff noise
  (attempt 2/15 → 8/15, 0.5s→32s backoff) immediately before the stall-watchdog kill at `stalled_for=3928
  threshold=3900`. Same root cause as this doc's original finding — the still-`status: blocked` P0
  `tradfi_databento_account_billing_suspended_2026_08_09.md` CME/GLBX.MDP3 billing block, now reconfirmed live at
  `2026-08-17T12:11Z`. No new information beyond the existing wave-scale finding already paged in that P0 doc's
  Progress Log (2026-08-17, slot 16) — did not re-page the operator (would be a duplicate ask); did not relaunch
  per RB-INFRA-RELAUNCH. No code changed this session.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **dedup pass 2026-08-21**: added an explicit `DUPLICATE OF` marker on the sole open todo (already-verbatim per the
  na-eligibility-audit entry directly below) so the plan-hygiene open-task counter stops double-counting it against
  `tradfi_databento_account_billing_suspended_2026_08_09.md`'s own P0 todo — no content change.
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirmed. Sole open todo is a verbatim duplicate of
  `tradfi_databento_account_billing_suspended_2026_08_09.md`'s own P0 `[OPERATOR]` todo (pay the Databento invoice) —
  no independent action needed here. Cross-referenced this pass: the sibling
  `dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_15.md` doc this doc
  corrects has been ARCHIVED this pass (both its todos closed as moot, citing this doc). `assigned_vm` unchanged.
