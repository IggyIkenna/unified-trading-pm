---
name: vm-preemption-billing-waste-audit
description:
  Audit both clouds' VM fleets for two silent billing-waste failure modes — a SPOT VM preempted without a matching
  auto-recovery/resume, and any VM class (spot or on-demand) silently re-attempting a structurally non-retriable
  attempted_failed shard on every future backfill wave. Cross-references classify_venue_error() verdicts and the
  PROGRESS-checkpoint contract rather than inventing a parallel mechanism. Every agent watching/monitoring VMs should
  run this regularly, not just when a specific incident is already suspected. Trigger on
  `/vm-preemption-billing-waste-audit`, "check for preempted VMs", "is any VM wasting billing", "audit attempted_failed
  for billing waste", "check VM fleet health for cost".
---

# /vm-preemption-billing-waste-audit — silent billing-waste monitor

Full contract: `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md` — read it before your first run
if this is your first time invoking this skill; this doc is the executable checklist only.

## When to run this

- Regularly, as a standing check whenever you're already looking at VM/fleet state (don't wait for a symptom).
- Before dispatching a new backfill wave over an asset_group/venue that has any prior `attempted_failed` history — cheap
  insurance against re-attempting a known-dead shard.
- After any SPOT VM you launched goes quiet (no progress heartbeat, no STOPPED/FAILED terminal state observed).

## Step 1 — preemption scan (both clouds)

```bash
# GCP — scope to the project(s) actually in use, adjust the lookback window
gcloud compute operations list --filter="operationType=compute.instances.preempted" --format=json

# AWS — spot-interruption equivalent for the account(s) in use
aws ec2 describe-spot-instance-requests --filters "Name=state,Values=cancelled,closed"
```

For each preemption hit: find the matching launcher's `vm-logs/{vm}/PROGRESS.json` and confirm (a) it exists, (b) a
relaunch happened, (c) the relaunch resumed FROM the checkpoint, not from `START_DATE`. **No PROGRESS.json, no relaunch,
or a `START_DATE`-replay relaunch = a finding.** Cite the VM name, the launcher script, and what actually happened vs.
what the PROGRESS-checkpoint contract (`spot-vms-for-backfill.md`) promises.

## Step 2 — attempted_failed billing-waste sweep

For the asset_group(s)/venue(s) you're checking, read the current `attempted_failed` distribution (the data-status
page's Distinct Values / axis-value census, or a direct manifest query). For any elevated cluster:

1. Read the `error_reason` / `classify_venue_error()` verdict recorded for those rows.
2. **Transient class** (rate-limit, timeout, 5xx) — expected to eventually clear on retry; only a finding if the retry
   count is unreasonable for the error class (e.g. dozens of waves, still failing the same way).
3. **Genuine/non-retriable class** (persistent 401/403, impossible venue/date combo) — every future wave that touches
   this shard wastes real billing. Finding: cite the shard `(asset_group, venue, data_type, day)`, the `error_reason`,
   and how many distinct backfill waves have re-attempted it.
4. **Billing-gated class** (e.g. Databento L2/L3 beyond the free-window entitlement) — this should NEVER be recorded
   `attempted_failed` at all; if it is, that's a code-fix finding (see the codex doc's "billing-gated is not a failure"
   section), not just a monitoring one.

## Step 3 — verify alerting actually catches what you found

Check whether a genuine Step 1 or Step 2 finding would have paged via the existing data-pipeline Slack alerting
(`/codex/04-architecture/agent-orchestrator-alerting.md`). If it wouldn't have, that's itself a finding — file it as an
alerting-hardening gap, don't just silently note "the alert didn't fire."

## Report format

For each finding: the exact VM/shard identifier, what the contract expected vs. what actually happened, and a
recommended next action (relaunch-with-checkpoint / mark-known-dead / fix-the-billing-classification /
harden-the-alert). No findings is a valid, expected outcome — say so plainly, don't manufacture one.

## What this skill does NOT do

Does not itself relaunch a VM, mark a shard dead, or change any classification — it is a read-only audit. Findings
requiring action route through the normal findings-triage rule (fix in your own plan if small/clear, file an issue doc
if bigger, escalate to the operator if it's a real cross-cutting billing/data-correctness concern).
