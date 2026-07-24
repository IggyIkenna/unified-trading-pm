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
last_reviewed: 2026-07-24
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
  actually targets the right launcher class before trusting it fits).

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
- It does not (yet) wire an automated pre-flight gate that blocks a future wave from re-attempting a known-dead shard —
  that's a separate, larger design (see the gate doc's point 4, last todo). Until it ships, this is a MANUAL audit
  contract: run the skill, read the findings, escalate.

## Related skill

`/vm-preemption-billing-waste-audit` (`cursor-configs/skills/vm-preemption-billing-waste-audit/SKILL.md`) — the
executable checklist for this contract.
