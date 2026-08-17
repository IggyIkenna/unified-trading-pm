---
doc_type: issue
title: "cefi-lighter-zksync-2026 preempted backfill VM can't auto-relaunch — Tardis cap-1 occupied, page-once suppression means no automatic retry once it clears"
summary: >-
  DP-VM-008 escalation (agt-861d79) for VM `cefi-lighter-zksync-2026-20260817-010152` (SPOT-preempted, ~79% done —
  chunk 182/229, `PROGRESS.json` `last_completed_date=2026-07-02`, `monotonic=true`). The in-band `RelaunchPreemptedVm`
  auto-recover actuator already attempted this and self-paged `DP_VM_PREEMPTED_NO_RELAUNCH` (durably suppressed for
  this exact `vm_name` per its page-once-per-VM-name design). Root cause confirmed via a manual repro against the LIVE
  guard: `tardis_running_vm_count` (the guard's own function, sourced directly) returns 1 right now —
  `cefi-binance-futures-2026-heavy-20260817-010713` holds the single Tardis-cap-1 slot (BINANCE-FUTURES is not
  cap-exempt; LIGHTER-ZKSYNC is not cap-exempt either — its `derivative_ticker` leg has no native-REST source, Tardis
  only, per `tardis-concurrency-guard.sh`'s own header). The holder is actively progressing (heartbeat/run.log ~2min
  fresh) but only at `last_completed_date=2026-06-03` of a `heavy` multi-year scope — not close to finishing, so this
  is not a short wait. No live replacement VM exists for the `cefi-lighter-zksync` prefix (checked
  `gcloud compute instances list --filter="name~'^cefi-lighter-zksync'"` — empty). Declining to `FORCE=1` past the
  cap — that overrides a HARD RULE (operator, 2026-07-16, `tardis-concurrency-guard.sh`) that exists specifically to
  prevent a measured mutual-403 storm (+37,212 FALSE `attempted_failed` rows in one 2026-07-16 incident) — this is
  routine INFO-severity SPOT churn with a safe, monotonic checkpoint, not a case that justifies the override. This is
  the SAME operating pattern already established for the `cefi-queue-heavy-binancefutu-x17` chain in
  `cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md` (decline + wait when the cap is occupied by another
  VM, relaunch once clear) — not a novel bug, and the `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` fix
  (durable per-VM GCS claim state) already closed the REPEATED-paging class this doc's storm was about. The residual
  gap this doc DOES surface: once `_already_paged` is set for a `vm_name`, NOTHING re-checks the Tardis cap later and
  retries automatically when it frees — the retry is durably handed to a human/AO-dispatched worker with no standing
  mechanism watching for "cap now clear, and there's a paged-but-never-relaunched VM waiting."
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [cefi, tardis, vm-preemption, dp-vm-008, dp-vm-009, relaunch, cap-1, big-finding]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
  ]
parent_epic: cefi_master
source: "DP-VM-008 escalation agt-861d79 (data_pipeline_failure worker, slot 7), 2026-08-17"
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
priority: P2
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
created: 2026-08-17
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh,
    deployment-service/scripts/vm/tardis-concurrency-guard.sh,
    deployment-service/scripts/recovery/relaunch_backfill_vm.py,
  ]
---

# cefi-lighter-zksync-2026 preempted backfill blocked on Tardis cap-1 — relaunch deferred, not lost

## What I found

Escalation `agt-861d79` dispatched me to relaunch `cefi-lighter-zksync-2026-20260817-010152` (SPOT-preempted). Read
its durable state before acting:

- `LAUNCH_PARAMS.json` env: `VENUES`, `SYMBOLS`, `DATA_TYPES`, `OVERRIDE_START_DATE`, `OVERRIDE_END_DATE`, `FORCE`
  (captured verbatim, not re-derived).
- `PROGRESS.json`: `{"last_completed_date": "2026-07-02", "monotonic": true, "updated": "2026-08-17T03:37:59Z"}` — a
  safe, monotonic resume point. `run.log` shows `chunk=182/229` at the moment of preemption (~79% through this
  shard's chunk range).
- `vm-census/relaunch-paged/vm/cefi-lighter-zksync-2026-20260817-010152.json` **exists** — the in-band actuator
  (`RelaunchPreemptedVm`) already tried and self-paged `DP_VM_PREEMPTED_NO_RELAUNCH` (CRITICAL, `#data-pipeline-alerts`
  `ts=1786939316.418119`). Per its own design this is a durable, page-ONCE-per-`vm_name` suppression — no future
  automated sweep will ever retry this exact VM name again.
- No live replacement: `gcloud compute instances list --filter="name~'^cefi-lighter-zksync'"` → empty.
- No supervising wrapper covers this shard: `rotate-cefi-backfill-vm.sh` only supervises the DIFFERENT
  `cefi-queue-*` naming convention (a distinct launch mode), not `cefi-lighter-zksync-*`.

**Root cause, confirmed live** (sourced `tardis-concurrency-guard.sh` directly and called its own
`tardis_running_vm_count asia-northeast1-c central-element-323112`): returns `1`. The live fleet shows
`cefi-binance-futures-2026-heavy-20260817-010713` RUNNING — BINANCE-FUTURES is not in `TARDIS_CAP_EXEMPT_VENUES`
(`HYPERLIQUID ASTER EXTENDED-STARKNET COINBASE-CDE`), so it holds the single Tardis-cap-1 slot. LIGHTER-ZKSYNC is
ALSO not cap-exempt (removed from the exemption list 2026-07-30 — its `derivative_ticker` leg has no native-REST
source, Tardis-only). A relaunch attempt right now (`1 running + 1 planned = 2 > cap 1`) would be REFUSED by
`tardis_guard_reserve_slot` — exactly the outcome the already-paged `DP_VM_PREEMPTED_NO_RELAUNCH` almost certainly
recorded (guard refusal is one of `RelaunchPreemptedVm`'s explicit page-triggering failure paths).

Checked whether the holder is close to freeing the slot: its own `PROGRESS.json` shows `last_completed_date=2026-06-03`
against a `heavy` multi-year scope, with a fresh heartbeat/run.log (~2min old — genuinely progressing, not stuck) —
this is a long-running shard, not a near-term completion. Waiting it out is not feasible within a one-shot escalation
worker's liveness window.

## Why I did not force it

`FORCE=1` bypasses the Tardis cap-1 HARD RULE (operator, 2026-07-16) that exists specifically because N>1 measured a
mutual-403 storm in production (2026-07-16: 10,300×403/912 ok on one VM, 15,034×403/0 ok on another, +37,212 FALSE
`attempted_failed` rows in 8h, coverage went BACKWARD). This is routine INFO-severity SPOT churn with a clean,
monotonic checkpoint and no urgency — not the kind of case the doc's own precedent (`cefi_track2_backfill_vm_
preempted_no_recovery_2026_07_30.md`, todo dated 2026-08-06) used to justify its one recorded FORCE=1 override (an
explicit operator ruling after a MUCH longer stuck chain). Declining to relaunch now and recording the exact recipe
for later is the same posture ~10 independent review-craft dispatches took in that doc when they found the cap
occupied — decline, log, do not hold the slot for a multi-day-scale wait.

## The residual gap (separate from this one VM)

Once `_already_paged` is set, the automated path for that `vm_name` is closed forever, but nothing else watches for
"the Tardis slot has since freed, and there's a paged-but-never-relaunched VM waiting." Today the recovery is
100% human/AO-worker-driven from the Slack page (which is the runbook's designed behavior, not a bug) — but there is
no standing reconciler that would notice this VM SPECIFICALLY needs attention once
`cefi-binance-futures-2026-heavy-20260817-010713` (or its eventual successor) finishes or gets preempted itself.
Given the docs already list a 414-message `DP_VM_PREEMPTED_NO_RELAUNCH` volume in the last 30h
(`#data-pipeline-alerts`, checked 2026-08-17), most of that volume is plausibly this SAME class (Tardis cap-1
contention across many shards, each paging once, by design) rather than a bug — but nobody has verified that at
scale. Filing this as P2 (not a fix I have — a genuine design question: should there be a periodic "check the cap,
retry the oldest paged-but-not-relaunched VM" reconciler, or is human-driven retry-on-page the intended steady
state at current preemption volume?).

## Recommended decision

- **A [RECOMMENDED]**: Once the Tardis cap frees (`tardis_running_vm_count` returns 0), relaunch
  `cefi-lighter-zksync-2026` reproducing the captured `LAUNCH_PARAMS.json` env verbatim
  (`VENUES`/`SYMBOLS`/`DATA_TYPES`/`OVERRIDE_START_DATE`/`OVERRIDE_END_DATE`/`FORCE` — read fresh from
  `gs://deployment-scripts-central-element-323112/vm-logs/cefi-lighter-zksync-2026-20260817-010152/LAUNCH_PARAMS.json`
  at relaunch time, don't hand-copy this doc's snapshot) via `launch-cefi-sharded-backfill.sh`, with `START_DATE`
  overridden to the checkpoint frontier (`2026-07-02`) per the standard preemption-recovery contract
  (`spot-vms-for-backfill.md` § "Preemption recovery MUST resume from PROGRESS"). Verify STARTED@T+60s + PROGRESS@T+10min,
  per the no-fire-and-forget rule.
- **B**: Assess (as a separate, small design todo) whether a periodic cap-aware reconciler for
  `DP_VM_PREEMPTED_NO_RELAUNCH`-paged VMs is worth building, or whether the current volume is low enough that
  human/AO-worker-driven retry-on-page is fine as the steady state.

## Todos

- [ ] [INFRA] P2. Once `tardis_running_vm_count asia-northeast1-c central-element-323112` (source
      `deployment-service/scripts/vm/tardis-concurrency-guard.sh`) returns `0`, relaunch
      `cefi-lighter-zksync-2026` per option A above. Verify STARTED@T+60s + PROGRESS@T+10min before closing this
      todo. Repo: deployment-service.
- [ ] [DATA] P3. Sample ~20 of the 414 `DP_VM_PREEMPTED_NO_RELAUNCH` messages posted to `#data-pipeline-alerts` in the
      last 30h (as of 2026-08-17) and classify each by failure reason (Tardis cap-1 guard refusal vs. something else)
      to confirm/refute that this is the dominant class at current volume — informs whether option B (a cap-aware
      reconciler) is worth building. Repo: unified-trading-pm (analysis-only, no code).
- [x] ✅ [INFRA] P1. **NEW FINDING, fixed same session**: `launch-cefi-hl-aster-historical-backfill.sh` never sourced
      `tardis-concurrency-guard.sh` or stamped `VM_TARDIS_CONSUMER` — a live guard-bypass, not a hypothetical. Its
      default `VENUES` still bundles `LIGHTER-ZKSYNC` with 3 truly cap-exempt venues even though LIGHTER-ZKSYNC lost
      its exemption on 2026-07-30 (`derivative_ticker` is Tardis-only for that venue). Fixed to mirror
      `launch-cefi-sharded-backfill.sh`'s integration (per-venue `tardis_venue_list_needs_guard` check, explicit
      `VM_TARDIS_CONSUMER` stamp, `tardis_guard_reserve_slot` before create). — deployment-service@2ed70f49b1
- [x] ✅ [INFRA] P1. Retroactively stamped `VM_TARDIS_CONSUMER=1` (via `gcloud compute instances add-metadata`, no
      destructive op) on the 3 already-running VMs this bug had launched invisibly to the guard —
      `cefi-lighter-zksync-2024/2025/2026-20260817-100127` (all in `asia-northeast1-c`, all mid-run with real
      progress, none of them the `derivative_ticker`-Tardis-only leg was skipped). `tardis_running_vm_count` before
      the stamp: `1` (only `cefi-binance-futures-2026-heavy` counted). After: `4` (the true live occupancy). This
      closes the live undercount immediately — any future guard-integrated launch attempt now correctly refuses
      instead of silently stacking a 5th+ concurrent Tardis consumer on top of an already-over-cap fleet.
- [x] ✅ [INFRA] P2. Fleet-wide sweep done — deployment-service@bd3d5fa0ed. Grepped every `launch-*.sh` for
      `derivative_ticker`/Tardis-only markers without the guard sourced nearby, cross-checked against
      `TARDIS_CAP_EXEMPT_VENUES`. Found and fixed a SECOND launcher with the exact same undercounting gap:
      `launch-cefi-onchain-forward-poll.sh` launches LIGHTER-ZKSYNC `derivative_ticker` worker VMs
      (`cefi-lighter-<ts>`, matches neither `TARDIS_VM_NAME_PATTERN` nor any metadata stamp) without ever
      sourcing `tardis-concurrency-guard.sh` — fixed to source the guard, gate per-venue via
      `tardis_venue_list_needs_guard`, stamp `VM_TARDIS_CONSUMER` in VM metadata, and call
      `tardis_guard_reserve_slot` before create (verified via `bash -n` + `DRY_RUN=1` dry-runs for both
      LIGHTER-ZKSYNC (`VM_TARDIS_CONSUMER=1`) and HYPERLIQUID (`VM_TARDIS_CONSUMER=0`)). Also found the PRIOR
      session's fix to `launch-cefi-hl-aster-historical-backfill.sh` was itself incomplete: it added the
      pre-flight `tardis_guard_reserve_slot()` call but never actually stamped `VM_TARDIS_CONSUMER` into the
      created VM's metadata (`needs_tardis_guard` was computed and used for the reserve-slot gate only) — so
      those VMs remained invisible to every OTHER launcher's guard check despite this launcher's own gate
      correctly refusing over-cap; added the missing stamp line. Checked all other `derivative_ticker`-mentioning
      launchers (`launch-aster-forward-poll.sh`, `launch-cefi-extended-starknet-funding-timestamp-vm.sh` — both
      cap-exempt venues only; `launch-cefi-funding-timestamp-fix-vm.sh` — reprocesses already-captured parquet,
      no new Tardis fetch; `launch-cefi-perp-funding-daily-cron-vm.sh` — no venue/create, downstream compute
      only; `launch-mtds-live*.sh` — live WS streaming, not batch Tardis; `launch-cefi-onchain-fwd-daily-cron-vm.sh`
      — only launches the tiny e2-micro cron host, not a Tardis-consuming VM itself; `launch-canonical-migration-vm.sh`
      — `LIGHTER-ZKSYNC` appears only in a comment, no fetch) — none needed the guard. Live-fleet check
      (`gcloud compute instances list --filter="name~'^cefi-lighter-|^cefi-extended-|^cefi-hyperliquid-|^aster-fwd-'"`)
      confirmed no currently-running VM from either fixed launcher needs retroactive metadata stamping — the gap
      was in the CODE PATH, not currently manifesting as a live undercount. QG green (248s) → quickmerge --agent
      → verified `bd3d5fa0e` ancestor-of `origin/live-defi-rollout`.

## Progress Log

- 2026-08-17 — Filed by DP-VM-008 escalation worker (slot 7, agt-861d79). Diagnosed root cause (Tardis cap-1 occupied
  by `cefi-binance-futures-2026-heavy-20260817-010713`, confirmed live via the guard's own `tardis_running_vm_count`
  function), confirmed no safe near-term path to complete the relaunch this session, declined to `FORCE=1` past the
  hard cap rule, and captured the exact recipe (launch_env + checkpoint) for the next worker. `AUTHORING_SLOT` was
  `dp-fleet-monitor` (non-numeric) — skipped the authoring-slot ping per the runbook's documented carve-out (the
  dispatch-time Slack alert already covers the FYI).
- 2026-08-17 — [INFRA] P2 todo dispatched to infra worker (slot 16). Re-verified live: `tardis_running_vm_count
  asia-northeast1-c central-element-323112` (sourced fresh from `tardis-concurrency-guard.sh`) still returns `1` —
  `cefi-binance-futures-2026-heavy-20260817-010713` is still RUNNING and holds the cap; `gcloud compute instances
  list --filter="name~'^cefi-lighter-zksync'"` confirms no live replacement exists. The todo's own gate ("once the
  count returns 0") is not met, so per the same reasoning as the filing worker, declined to `FORCE=1`. Skipping this
  task with `reason_code=GATED` rather than holding a session open across a multi-day-scale wait — the next
  dispatch should re-check the cap live (do not trust this snapshot) before relaunching per option A.

- 2026-08-17T09:25Z — [INFRA] P2 todo dispatched to infra worker (slot 13, same session that just declined the
  sibling `cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md` 10th-relaunch todo ~2min earlier for the
  identical root cause). Re-verified live: `tardis_running_vm_count asia-northeast1-c central-element-323112`
  (sourced fresh) still returns `1` — `cefi-binance-futures-2026-heavy-20260817-010713` still `RUNNING`/SPOT, ~9h13m
  uptime since its `2026-08-17T00:11:46 UTC` launch. `gcloud compute instances list --filter="name~'^cefi-lighter-
  zksync'"` confirms still empty — no live replacement. Gate ("count returns 0") remains unmet. Declining to
  `FORCE=1` for the same reason as both prior entries. Skipping via `reason_code=GATED` — the next dispatch (for
  either this todo or the sibling `cefi_track2` 10th-relaunch todo) should re-check the cap live; both todos share
  the exact same blocking condition and will likely clear together once
  `cefi-binance-futures-2026-heavy-20260817-010713` finishes or is preempted.

- 2026-08-17T10:35Z — [INFRA] P2 todo dispatched to infra worker (slot 8). Re-verified live:
  `tardis_running_vm_count` still returned `1` — but `gcloud compute instances list --filter="name~'^cefi-lighter-
  zksync'"` now showed 3 LIVE replacements (`cefi-lighter-zksync-2024/2025/2026-20260817-100127`, all RUNNING,
  launched 10:01:27Z — ~2.5h into the wait window, NOT via this doc's recommended `launch-cefi-sharded-backfill.sh`
  recipe). Investigated why the count still read `1` despite a 4th non-exempt Tardis consumer running: the new VMs
  were launched by `launch-cefi-hl-aster-historical-backfill.sh` (confirmed via `LAUNCH_PARAMS.json`), which — unlike
  `launch-cefi-sharded-backfill.sh` — never sources `tardis-concurrency-guard.sh` and never stamps
  `VM_TARDIS_CONSUMER`; its VM name (`cefi-lighter-zksync-...`) also doesn't match the guard's
  `TARDIS_VM_NAME_PATTERN` (`-lighter-` ≠ the pattern's `-light-` token). Root cause: this launcher's default
  `VENUES` still lists `LIGHTER-ZKSYNC` alongside 3 genuinely cap-exempt venues, a stale assumption from before
  LIGHTER-ZKSYNC lost its exemption on 2026-07-30 — nobody audited this OTHER launcher when that exemption-list
  change shipped. This is a live guard-bypass of the exact HARD RULE the 2026-07-16 mutual-403 storm precedent
  exists to prevent (checked both VMs' `run.log` for an active storm signature — found none yet; this is a latent-
  risk fix, not an active-incident response). Also confirmed the new VM is NOT resuming from this doc's captured
  checkpoint (`OVERRIDE_START_DATE=2026-01-01` in its `LAUNCH_PARAMS.json`, not `2026-07-02`) — it is a redundant,
  from-scratch re-run of the same shard via a different code path, not the option-A recipe. **Fixed the launcher**
  (see new todos above) — `source`s the guard, per-venue-checks `tardis_venue_list_needs_guard`, stamps
  `VM_TARDIS_CONSUMER` explicitly, calls `tardis_guard_reserve_slot` before create — verified with `bash -n` +
  `DRY_RUN=1` runs for both an exempt (HYPERLIQUID) and non-exempt (LIGHTER-ZKSYNC) venue, shipped clean through
  Pass-1 `quality-gates.sh` (255s, all green) → Pass-2 `quickmerge --agent`, landed + ancestry-verified on
  `origin/live-defi-rollout` at `deployment-service@2ed70f49b1`. **Also retroactively stamped** all 3 already-running
  VMs (`gcloud compute instances add-metadata ... VM_TARDIS_CONSUMER=1`, additive/non-destructive) — live count now
  correctly reads `4`. This todo's own literal gate (relaunch `cefi-lighter-zksync-2026` once the count hits `0`)
  remains UNMET — if anything further from met now that the true occupancy is visible — and forcing a THIRD
  concurrent launch for this shard right now would be actively worse than before this session (would-be 5 vs the
  previously-visible 2). Declining `FORCE=1` for the same reason as every prior entry. Skipping via
  `reason_code=GATED`. Filed a P2 follow-up todo for a fleet-wide sweep (this session found this ONE launcher by
  accident, not via a deliberate audit — there may be other launchers with the same undercounting gap).
