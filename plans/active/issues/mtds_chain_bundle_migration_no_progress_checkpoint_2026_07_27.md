---
doc_type: issue
title:
  rewrite_tradfi_chain_bundle_content_id_2026_07_25.py has no PROGRESS.json checkpoint — SPOT preemption restarts from
  object 0
summary: >-
  All 8 shards of the tradfi chain-bundle --apply fleet (run-id 20260727-041704) were preempted mid-run with zero
  EXIT_STATUS and no PROGRESS.json checkpoint, forcing a full restart-from-object-0 on relaunch. Not a correctness bug
  (the script's idempotent design makes this safe) but a real efficiency/wall-clock cost, unlike the PROGRESS-checkpoint
  contract other migration executors in this same family already implement.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [infra, spot-vm, preemption, checkpoint, tradfi, migration]
created: 2026-07-27
assigned_vm: NA
parent_epic: infrastructure_master
priority: P2
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
source:
  [
    "slot-9, discovered while gating tradfi_manifest_content_recovery_completion_2026_07_24.md's chain-bundle --apply
    fleet, 2026-07-27",
  ]
related: [/plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md]
resolved_by:
locked_by:
locked_since:
---

# rewrite_tradfi_chain_bundle_content_id_2026_07_25.py has no PROGRESS.json checkpoint

## What I found

Gating `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s chain-bundle `--apply` fleet (run-id
`20260727-041704`, 8 SPOT shards), found all 8 VMs had vanished from `gcloud compute instances list` with **zero
`EXIT_STATUS`** written. `gcloud compute operations list` confirmed genuine `compute.instances.preempted` system events
for all 8 (two waves, ~22:12/22:31 UTC 2026-07-26) — not silent success, as the gate todo's own text correctly warned to
check for.

`run.log` for shard0 showed only **4000/33498 objects (11.9%)** processed at the moment of preemption (~1.4 objects/sec
measured; a full shard is a ~6.6h job at that rate). None of the 8 shards had written a `vm-logs/{vm}/PROGRESS.json`
checkpoint — the contract CLAUDE.md's spot-VM rule describes (`RelaunchPreemptedVm` resumes from measured progress via
this file, monotonic-gated) simply doesn't exist for this script. Relaunching (`SHARD_OF=8` fresh fan-out, run-id
`20260727-061325`) therefore restarts every shard from object 0 — safe (the script's own `already_canonical` disposition
makes re-processing an already-rewritten object a no-op, confirmed by reading the executor), but wasteful: the ~12%
average progress lost per shard (likely higher for shards preempted in the second wave, ~19 minutes later) adds real
wall-clock time to an already multi-hour campaign, and a future preemption during the SAME run would compound this
indefinitely with no way to converge faster than a full from-scratch pass each time.

Sibling migration executors in the SAME session already implement this pattern correctly —
`market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py` shipped a "SPOT-preemption resume
checkpoint" (`mdps@efa559a`) and
`market-tick-data-service/scripts/migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` has an equivalent — so
there's a proven, in-repo pattern to mirror rather than design from scratch.

## Why it matters

This script family runs on SPOT VMs (cost-optimized, expected to preempt periodically per the workspace's own SPOT
policy) processing multi-hour, tens-of-thousands-of-object worklists. Without a checkpoint, EVERY preemption costs
roughly "average progress at kill time" of re-work, which compounds across the fleet's total preemption count over a
campaign's lifetime — plausibly doubling or tripling real wall-clock cost for a campaign that gets preempted multiple
times, and is exactly the class of waste `/vm-preemption-billing-waste-audit` looks for.

## Recommended decision

- [ ] [SCRIPT] P2. Add a periodic `PROGRESS.json` write (object-index or last-processed-key, monotonic-gated) +
      read-on-start resume to `rewrite_tradfi_chain_bundle_content_id_2026_07_25.py`, mirroring
      `migrate_candle_canonical_2026_07.py`'s SPOT-preemption resume checkpoint (`mdps@efa559a`) or
      `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`'s equivalent. Repo: market-tick-data-service. **Done
      when**: a deliberately-killed shard mid-run resumes from its last checkpoint on relaunch instead of restarting
      from object 0, verified on a real (or `-test-`) run.
- [ ] [DATA] P3. Audit the OTHER tradfi/cefi/defi canonical-migration executors in this family
      (`market-tick-data-service/scripts/migrate_*_2026_07*.py`) for the same gap — the two known-compliant scripts
      cited above suggest this is inconsistent across the family rather than a universal pattern, worth a quick census
      before assuming any specific untested script has (or lacks) the checkpoint.
