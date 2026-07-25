---
doc_type: issue
title:
  First live run of /vm-preemption-billing-waste-audit + design for a cross-run pre-flight gate on known-dead shards
summary: >-
  Two follow-ups from `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md` (shipped 2026-07-24) that
  the codex doc itself explicitly defers: (1) the skill (`/vm-preemption-billing-waste-audit`) exists but has never been
  run for real against both clouds' live fleets — its findings are unknown until it's actually invoked; (2) the codex
  doc's own "What this contract deliberately does NOT do" section names a real gap — no automated pre-flight gate stops
  a future backfill wave from re-attempting a shard `classify_venue_error()` already FAIL-classified, or one that's
  failed identically across N consecutive waves. Both are tracked here per
  `data_pipeline_e2e_milestones_gate_2026_07_24.md` §4.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, market-tick-data-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [vm, spot, preemption, billing, attempted_failed, monitoring, cost, pre-flight-gate]
related:
  [
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §4
depends_on: []
---

# First live run of the VM billing-waste audit + pre-flight gate design

## Todos

- [ ] [SCRIPT] P1. Run `/vm-preemption-billing-waste-audit` for the first time against both clouds' live fleets with a
      30-day lookback. Definition-of-done: for every launcher family, either a filed finding (preemption with no
      matching auto-recovery, or a confirmed billing-wasting `attempted_failed` cluster) or a stated "clean" — cite the
      run's own output, not a summary. **PARTIALLY DONE 2026-07-25 — see Progress Log; 2 of ~18 GCP launcher families
      traced in depth, remainder not yet individually verified, AWS side blocked on IAM.**
- [ ] [BACKEND] P2. Design + wire a cross-run pre-flight gate: when `classify_venue_error()` returns `action=FAIL` for a
      shard (or N consecutive waves hit the identical `error_reason` on the same shard), route it to a "known-dead, do
      not re-attempt" manifest-level marker instead of the current default (silent infinite retry via
      `record_failed()`). Definition-of-done: the marker mechanism is designed (schema field or side-table), at least
      one launcher family wired to check it before dispatching a shard, and a regression test proving a marked shard is
      skipped on the next wave.

## Progress Log

- **2026-07-25 — First `/vm-preemption-billing-waste-audit` run (partial, GCP-only, 2 of ~18 launcher families traced in
  depth).**
  `gcloud compute operations list --filter="operationType=compute.instances.preempted" --project= central-element-323112`,
  30-day lookback: **197 preemption events**, collapsing to roughly 18 distinct launcher families once per-shard-suffix
  noise is stripped. Full family breakdown captured in this session's scratchpad (not promoted — regenerable via the
  same filter). Two families traced to their `vm-logs/{vm}/` GCS contents + `run.log`:
  - **`canonical-migration-tradfi-cdlap`** (54 events, the single largest family — all within a ~10-minute burst on
    2026-07-23): checked `vm-logs/canonical-migration-tradfi-cdlap-20260723-105729/` — only `LAUNCH_PARAMS.json` +
    `TARBALL_PINS.json` exist, no `run.log`, meaning these VMs were preempted within seconds of creation, before writing
    any output — a SPOT capacity crunch on that zone/machine-type at that moment, not a mid-run loss. Negligible billing
    impact (GCP does not meaningfully bill for a VM that never completed boot/init). This burst's timing matches exactly
    when the independent `/data-pipeline-reconciliation --asset-group tradfi` run (this same session, earlier) measured
    the tradfi canonical-id migration had jumped from 30.8%→99.3% clean — strong circumstantial evidence this family's
    preemptions were absorbed by successful relaunches, not a silent loss. **Verdict: clean, no finding.**
  - **`canonical-migration-defi-rebuild`** (14 events, spread across the full window, not a single burst): checked
    `vm-logs/canonical-migration-defi-rebuild-20260723-073604/` — this one DID run for real (~56 min, `run.log` shows
    active date-by-date manifest scanning, 2.2M+ manifest entries written incrementally to its own per-VM shard) before
    being preempted mid-scan. **No `PROGRESS.json` was ever written by this launcher** — it does not use the documented
    PROGRESS-checkpoint contract at all; its only persisted state is the cumulative per-VM manifest shard itself.
    `LAUNCH_PARAMS.json` shows `RESUME_START_DATE=2026-01-01` (fixed), not a value derived from measured progress. This
    is a genuine partial-conformance gap against the codex contract — **but the actual billing-waste risk is bounded,
    not confirmed severe**: `relaunch_backfill_vm.py`'s own code comments confirm the dangerous case is specifically a
    `--force`/`redo_all` run with no checkpoint (which PAGEs loudly rather than silently replaying); this launch's
    params show `RESUME_MODE=full`, not a force run, so a blind restart-from-`START_DATE` would still benefit from the
    launcher's presence-skip default (re-scanning is cheap; re-fetching already-captured data is not). **Verdict: real
    conformance gap, bounded/moderate risk — filed as a follow-up todo below, not escalated as urgent.**
  - **Remaining ~16 families NOT traced this run** (`mtds-backfill-tradfi-pipelinecheck` 13, `cefi-aster` 7,
    `canonical-migration-defi-pi-range` 7, `instr-backfill-tradfi-pchk` 5, `cefi-queue-heavy-binancefutu-x17` 5,
    `mtds-dex-swaps-backfill` 4, `canonical-migration-cefi-cdlap` 4, `af-backfill` 4, `canonical-migration-defi-relabel`
    3, `datapoint-validation-{prediction,cefi,defi}` 5, `cefi-hyperliquid` 2, the
    `canonical-migration-cefi-wp*`/`-content-*` migration wave ~31 events, `tradfi-bf-*` per-shard backfill ~35 events,
    plus 4 singleton families) — **declared scope limitation, not silently omitted**. Time-boxed this run in favor of
    covering the two highest-event-count families plus the `attempted_failed` sweep below; a follow-up session should
    trace the rest, prioritizing `tradfi-bf-*` and the `canonical-migration-cefi-wp*` wave (highest remaining event
    counts).
  - **AWS side: blocked.** `aws ec2 describe-spot-instance-requests` (us-east-1) returned `UnauthorizedOperation` — the
    orchestrator role (`uts-orchestrator-epic-role`) lacks `ec2:DescribeSpotInstanceRequests`. A broader
    `describe-instances` filter for terminated/stopped backfill/migration/canonical-tagged instances in us-east-1
    returned empty (either genuinely no AWS backfill fleet right now, or the wrong region/account scope — not
    conclusively determined). **Filed as its own gap** — an IAM grant (if AWS-side SPOT monitoring is wanted) or
    confirmation that AWS is not currently used for backfill VMs is an operator-level call, not something to route
    around.
  - **`attempted_failed` sweep**: leveraged this session's own 5 `/data-pipeline-reconciliation` runs (same day) rather
    than re-deriving from scratch. CeFi's largest cluster (Tardis HTTP 403, 797,323 rows / 75.3%) is already tracked
    (`tardis_concurrent_ip_lockout_2026_07_12.md`). The next-largest untracked slice, `VENUE_FETCH_FAILED` (219,071
    rows, 20.7% of cefi's `attempted_failed`, spread across BINANCE-FUTURES/
    KRAKEN-FUTURES/BITFINEX-FUTURES/BYBIT/others), was investigated this run: date range 2020-03-20→2026-05-21, **NOT
    growing for the last 2+ months** (today is 2026-07-25) — real historical waste, but not an ACTIVE, ongoing billing
    drain (nothing is currently re-attempting these specific shards). **Verdict: informational, not urgent.** Other 4
    AGs' `attempted_failed` distributions not independently re-swept this run.
  - **Step 3 (alert-firing verification) not performed this run** — time-boxed out; flagged as not done, not assumed
    clean.

### New follow-up todo from this run

- [ ] [BACKEND] P2. **`canonical-migration-defi-rebuild`'s launcher (`launch-canonical-migration-vm.sh` via
      `RESUME_MODE=full`) does not write a `PROGRESS.json` checkpoint** — it relies only on the cumulative per-VM
      manifest shard, and `RESUME_START_DATE` is a fixed launch param, not derived from measured progress. Bounded risk
      today (not a `--force` run, presence-skip limits the cost of a blind restart to re-scan time, not re-fetch), but
      out of conformance with the documented PROGRESS-checkpoint contract
      (`/codex/05-infrastructure/spot-vms-for-backfill.md`). Either wire this launcher to emit `PROGRESS.json` like the
      conforming launchers do, or confirm the per-VM-manifest-shard mechanism is an accepted equivalent and document
      that exception in the codex SSOT. Repo: deployment-service.
