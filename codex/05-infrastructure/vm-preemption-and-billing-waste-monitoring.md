---
doc_type: codex-ssot
title: VM preemption + attempted_failed billing-waste monitoring — the standing contract
summary:
  Every SPOT VM must be regularly checked for preemption and, if preempted, for why it wasn't auto-recovered; every VM
  (spot or on-demand) must be checked for silently accumulating attempted_failed rows on transient errors that should
  have retried to success — both classes silently waste real billing if unmonitored. Composes with the existing
  PROGRESS-checkpoint preemption-resume contract (spot-vms-for-backfill.md) and classify_venue_error()
  (shard-level-failure-isolation.md) rather than inventing a parallel mechanism.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, market-tick-data-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [vm, spot, preemption, billing, attempted_failed, monitoring, cost, infrastructure]
related:
  [
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: 2026-07-24
authoritative_for: [VM preemption + attempted_failed billing-waste monitoring contract]
referenced_by:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/deployment-observability.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
owner:
last_reviewed: 2026-08-09
code_refs:
type: infrastructure
execution:
  {
    owner: data-engineering,
    cadence: every VM-monitoring pass; every backfill-wave dispatch,
    verifier: bash the /vm-preemption-billing-waste-audit skill against both clouds' live fleets,
  }
---

# VM preemption + attempted_failed billing-waste monitoring — the standing contract

## Why this exists

Two silent billing-waste failure modes exist independently of each other and neither had a single owning mechanism
before this doc (2026-07-24 gap analysis, `data_pipeline_e2e_milestones_gate_2026_07_24.md` point 4):

1. **A preempted SPOT VM that never resumed.** The PROGRESS-checkpoint contract (see `spot-vms-for-backfill.md`) exists
   so a preempted backfill VM auto-relaunches and resumes from measured progress, not from `START_DATE`. But nothing
   regularly CHECKS that this actually fired for every preemption event — a VM can be preempted, silently fail to
   auto-recover, and simply never finish, with no signal beyond an absent completion.
2. **A VM (spot or on-demand) silently accumulating `attempted_failed` rows on a NON-retriable error.** Every future
   backfill wave that touches the same shard re-attempts it by default (`record_failed()`'s own docstring) — there is no
   automated gate that consults `classify_venue_error()`'s `action` field to stop re-attempting a
   structurally-FAIL-classified shard. Each re-attempt costs real compute/API billing for a call that will never
   succeed.

## The contract

### 1. Regular preemption scan (both clouds)

- GCP: `gcloud compute operations list --filter="operationType=compute.instances.preempted"` per project, for the
  lookback window in question.
- AWS: the equivalent spot-interruption event query for the account(s) in use.
- Cross-reference every preemption hit against the launcher's own `vm-logs/{vm}/PROGRESS.json` checkpoint and the
  orchestrator's relaunch record. **A preemption with no matching relaunch, or a relaunch that restarted from
  `START_DATE` instead of the checkpoint, is a finding** — investigate why the PROGRESS-checkpoint contract didn't fire
  for that specific launcher (see `spot-vms-for-backfill.md`'s own note: verify the specific rebuild/relaunch tool
  actually targets the right launcher class before trusting it fits). **But check the classification gate FIRST**:
  `exit_code_fleet_monitor.sweep()` only ever considers a VM whose name passes
  `deployment_service.data_pipeline_monitors.vm_classification.is_data_vm()` (an ASSET_GROUPS substring OR a
  `DATA_VM_PREFIXES` entry) — a VM invisible to that filter never reaches PREEMPTED classification at all, so
  `RelaunchPreemptedVm` has no chance to fire regardless of whether the checkpoint contract itself is sound
  (`af_backfill_preemption_auto_recovery_not_firing_2026_08_04.md`, archived: 31 VM-name prefixes across the fleet had
  this exact gap before the 2026-08-04 fix + the `test_data_vm_prefixes_cover_every_relaunchable_launcher` regression
  guard closed it). If a genuinely relaunchable prefix (a real `launcher_registry.LAUNCHER_FOR_VM_PREFIX` entry) is ever
  silently missing from that classifier again, that guard test should already be failing CI — treat a live repeat of
  this finding as evidence the guard itself regressed, not just the prefix list.

**Forward-registration closed-loop contract (codified 2026-08-09,
`issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md`'s `[SCRIPT] P2` follow-up).** The 2026-08-04 fix +
its guard test close the loop for an EXISTING `launcher_registry` entry that silently drops out of `DATA_VM_PREFIXES` —
they do not catch a **brand-new** one-off/ad hoc launcher whose `VM_NAME=`/`VM_PREFIX=` was never registered in ANY of
the three registries (`vm_classification.DATA_VM_PREFIXES`, `launcher_registry.LAUNCHER_FOR_VM_PREFIX`,
`vm_prefix_registry.VM_PREFIX_TO_BUCKET`) in the first place — exactly how `af-backfill-` went unnoticed for ~9 days
before that fix. **A new `scripts/vm/launch-*.sh` MUST register its `VM_NAME`/`VM_PREFIX` in all three registries in the
SAME commit that adds the launcher**, or mark it `# non-relaunchable: <reason>` in the launcher script if it is
deliberately not a fleet-monitored data VM (a fan-out wrapper, a read-only audit, a live-service singleton). Enforced by
`deployment-service/scripts/quality_gates/check_vm_launcher_prefix_registration.py` (wired into
`deployment-service/scripts/quality-gates.sh`): it derives each launcher's VM-name prefix from the launcher FILE SET
itself (not the registries' own keys, so a launcher registered nowhere is caught) and fails on a prefix that is new
relative to a per-repo shrinking baseline (`vm_launcher_prefix_registration_baseline.yaml`, seeded 2026-08-09 with the
pre-existing fleet).

### 2. attempted_failed billing-waste audit

- For any VM class showing an elevated `attempted_failed` count (see `deployment-observability.md`'s existing
  `DP_RUN_MOSTLY_EMPTY`/`check_high_attempted_failed` alert — a real, live check, though it is a static cumulative
  manifest-cell check, not a "this run, right now" delta; know that distinction before reading it as a live signal),
  read the classification `classify_venue_error()` assigned per row (`shard-level-failure-isolation.md`).
- **Transient/should-retry** (rate-limit, timeout, 5xx): expected to eventually succeed on retry — not itself a finding
  unless the retry count is unreasonable for the error class.
- **Genuine/non-retriable** (structural 401/403, impossible venue/date combo, billing-gated entitlement guard): every
  future wave re-attempting this shard is pure waste. This is the finding to escalate — cite the shard, the
  `error_reason`, and the count of distinct waves that have re-attempted it.
- **Billing-gated is not a failure.** A request that hits a billing/entitlement guard (e.g. Databento L2/L3 beyond the
  free window) must never be recorded `attempted_failed` — it should be excluded from the denominator entirely, the same
  way `empty_confirmed` legitimate-absence rows are (see `/codex/02-data/honest-coverage-model.md`). If a launcher
  family is found recording these as `attempted_failed`, that's a code-fix finding, not just a monitoring one.

### 3. Verify the alert actually fires

Both classes above should be catchable by the existing data-pipeline Slack alerting (per
`/codex/04-architecture/agent-orchestrator-alerting.md`'s actionable-only convention). If a genuine finding from steps
1-2 would NOT have paged, that alerting gap is itself a finding to harden — do not treat "the alert didn't fire" as
evidence nothing was wrong.

## What this contract deliberately does NOT do

- It does not invent a new retry-classification taxonomy — `classify_venue_error()` is the SSOT for retriable vs.
  non-retriable; this contract only says "consult it and act on stale FAIL verdicts," not "reclassify anything."

**Update 2026-08-09 — the automated pre-flight gate now exists.** A shard `classify_venue_error()` FAIL-classifies (or
that hits `CONSECUTIVE_WAVE_FAIL_THRESHOLD` waves of the identical `error_reason`) is written to a GCS-persisted
side-table (`market_tick_data_service/engine/orchestrator/known_dead_shard_gate.py`, `KnownDeadShardGate`) instead of
silently re-attempted forever via `record_failed()`'s default. Write side wired into `sentinels.py`'s Tier-2 failure
branch; read side wired into `_apply_preflight_skip_filter`, which every launcher family funneling through
`venue_fetch.py`'s `_process_venue` pre-flight check consults before dispatching a shard (currently MTDS only —
`tradfi-bf-*`, `mtds-backfill-tradfi-pipelinecheck`, `mtds-dex-swaps-backfill`, `cefi-aster`, `cefi-hyperliquid`,
`cefi-queue-heavy-binancefutu-x17`; other services' launcher families are NOT yet wired). Design rationale (side-table
over a manifest-schema field) + full schema:
`/plans/archive/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md`. This contract's own
manual-audit posture (run the skill, read the findings, escalate) is UNCHANGED and still the right tool for launcher
families the automated gate doesn't cover yet, or for the preemption-scan half of this contract (§1), which the gate
does not touch.

## Related skill

`/vm-preemption-billing-waste-audit` (`cursor-configs/skills/vm-preemption-billing-waste-audit/SKILL.md`) — the
executable checklist for this contract.
