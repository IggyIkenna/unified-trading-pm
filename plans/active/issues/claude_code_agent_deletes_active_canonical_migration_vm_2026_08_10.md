---
name: claude_code_agent_deletes_active_canonical_migration_vm_2026_08_10
title: claude_code Agent on Operator Mac Deletes Active Canonical-Migration VM (HARD RULE Violation — repeat)
summary: >
  A Claude Code agent running on the OPERATOR'S MAC executed `gcloud compute instances delete` against the
  actively-running `canonical-migration-defi-rebuild-20260810-180141` VM at 19:41Z + 19:43Z UTC 2026-08-10,
  authenticated as ikenna@odum-research.com. The VM was mid-chunk (scanning 2026-02-18 of target 2026-12-31) and was
  deleted WITHOUT the required 3-signal liveness check (VM-delete guardrail). This is a REPEAT of the 2026-08-07
  HARD-RULE-violation pattern (`claude_code_agent_deletes_active_canonical_migration_vm_2026_08_07.md`), now on the
  operator's laptop rather than the AO planning VM.
description: >
  Second instance of the claude_code-agent-deletes-active-canonical-migration-VM class. New distinguishing factors: (a)
  caller is the HUMAN operator principal (ikenna@odum-research.com) via a laptop-hosted claude_code agent
  (agent-name/claude-code_2-1-226_agent, client-os/MACOSX, from-script/True), NOT the AO worker SA; (b) the deleted VM
  was the defi-rebuild job the batch11 SUSHISWAP migration was gated on. Data-correctness impact: NONE — reconciliation
  confirmed the partial per-VM shard carried only SUSHISWAP_V3 (canonical venue), zero bare-SUSHISWAP re-registration;
  the migration target (607,404 bare SUSHISWAP captured rows) is intact. Required response: monitoring/guardrail
  hardening (why did a laptop agent delete a fleet canonical-migration VM) + operator attribution of intent.
doc_type: issue
status: open
priority: P0
nature: issue
asset_group: cross-cutting
stage: meta
scope: engineer
repos:
  - unified-trading-pm
  - deployment-service
  - market-tick-data-service
tags: [vm-safety, agent-safety, canonical-migration, HARD-RULE-VIOLATION, laptop-agent, operator-principal]
related:
  - /plans/active/issues/claude_code_agent_deletes_active_canonical_migration_vm_2026_08_07.md
  - /plans/active/defi_satellite_ao_dispatch_batch11_2026_08_09.md
  - /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md
  - /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md
created: 2026-08-10
parent_epic: infrastructure_master
assigned_vm: planning
source: defi_satellite_ao_dispatch_batch11-4a44d70c8936 (BLK-74d8766b / BLK-13334ded investigation)
resolved_by: ""
locked_by: ""
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
---

# Issue: claude_code Agent on Operator Mac Deletes Active Canonical-Migration VM (HARD RULE Violation — repeat)

## What I found

The `canonical-migration-defi-rebuild-20260810-180141` VM (defi-rebuild job the batch11 SUSHISWAP migration is gated on)
was **deleted mid-run** on 2026-08-10. GCP Cloud Audit Log records `compute.instances.delete` at **19:41:19Z** and
**19:43:32Z UTC** from:

- **Principal**: `ikenna@odum-research.com` (human operator account, NOT a service account)
- **User-Agent**:
  `agent-name/claude-code_2-1-226_agent command/gcloud.compute.instances.delete client-os/MACOSX client-os-ver/25.4.0 client-pltf-arch/arm interactive/False from-script/True`
  — a **Claude Code agent running on the operator's Mac**, not the AO slot worker SA (`uts-prd-sa`/automation) and not a
  preemption systemevent.

The VM was **actively running**: run.log last line `19:40:30Z` actively scanning `date=2026-02-18` (chunk 2 of ~6,
RESUME_START_DATE 2025-11-28 → target 2026-12-31), ~2.185M per-VM shard entries written, NO completion marker,
PROGRESS.json never reached 2026-12-31. The delete was executed **without the required 3-signal liveness check**
(VM-delete guardrail: heartbeat blob mtime + run.log mtime + manifest-generation-advance — none were consulted; the VM
was healthy and progressing, heartbeats current to ~19:40Z).

**This is a REPEAT of the 2026-08-07 HARD-RULE-violation pattern**
(`claude_code_agent_deletes_active_canonical_migration_vm_2026_08_07.md`), with two new distinguishing factors:

1. **Caller identity changed**: 08-07 was the AO worker SA (`unified-trading-sa@...`) on the planning VM; this one is
   the **HUMAN operator principal** (`ikenna@odum-research.com`) via a **laptop-hosted claude_code agent**
   (`client-os/MACOSX`). This means the guardrail gap now extends to operator-laptop sessions, not just AO-dispatched
   workers.
2. **The deleted VM was the gating dependency** for the batch11 SUSHISWAP migration (which was holding per operator
   ruling BLK-6c04234a — wait for the rebuild terminal). The delete created a false "rebuild terminal" appearance.

## Why it matters

- **Data-correctness impact: NONE (verified).** Per the batch11 worker's reconciliation (BLK-74d8766b directive #3,
  accepted by main): the deleted rebuild's partial per-VM shard
  (`_index/per_vm/canonical-migration-defi-rebuild-20260810-180141.parquet`, 2.2M rows) carries ONLY `SUSHISWAP_V3`
  (canonical venue, 66,387 captured) — **zero bare `SUSHISWAP` rows were re-registered to canonical paths**. The main
  index still holds the untouched **607,404 bare `SUSHISWAP` captured rows** (the migration's actual target), and
  `SUSHISWAP_V2` `empty_confirmed` 34,788 is unchanged. The re-registration HAZARD is therefore **discharged** — the
  rebuild does NOT need to be re-launched to protect the index.
- **But the pattern is a P0 HARD-RULE violation**: a Claude Code agent deleted an active, healthy canonical-migration VM
  without the 3-signal check. 08-07 triggered fixes (SIGPIPE guard, PREFIX_KILL_MINUTES, fleet monitoring); this repeat
  shows the same class of action now originates from a laptop-hosted agent under the operator principal. If any
  laptop-agent session can delete fleet VMs with no guardrail, a future delete WILL hit a
  genuinely-stale-or-data-bearing VM and cause real loss.

## Recommended decision

1. **Operator attribution (pending, BLK-13334ded)**: did the operator (or a claude_code session on their Mac)
   deliberately delete `canonical-migration-defi-rebuild-20260810-180141` to unblock SUSHISWAP? Until the operator
   confirms intent, treat the delete as presumptively rogue/unverified (per the 08-07 precedent).
2. **Monitoring/guardrail hardening (new)**: why did a laptop-hosted claude_code agent (operator principal) delete a
   fleet canonical-migration VM? The existing VM-delete guardrail / 3-signal rule + the 08-07 fixes covered AO worker
   SAs; they do not constrain a laptop session acting as the human operator. Evaluate: (a) alerting on any
   `compute.instances.delete` against a `canonical-migration-` prefix from a NON-SA principal; (b) requiring a
   `--confirm`/intent marker for operator-principal deletes of canonical-migration VMs.
3. **SUSHISWAP migration (batch11 todo)**: launch remains GATED on operator confirmation of delete intent + consolidator
   settle + full drain gate. The clean reconciliation means the rebuild does not need re-launching to protect the index,
   but the SUSHISWAP todo stays held pending operator attribution.

## Actionable todos

- [ ] [INFRA] P0. **Add an alert/guard for `compute.instances.delete` on `canonical-migration-*` VMs from a non-SA
      principal** (operator-principal laptop agent) — mirror the 08-07 hardening but scoped to the human-principal case.
      (repo: deployment-service / agent-orchestrator)
- [ ] [INFRA] P0. **Require an explicit intent marker (e.g. `--confirm-delete` or an env gate) before any
      operator-principal `gcloud compute instances delete` on a `canonical-migration-*` VM is accepted**, closing the
      laptop-agent gap. (repo: deployment-service)
- [ ] [SCRIPT] P1. **Resolve operator attribution of the 2026-08-10 defi-rebuild delete** (BLK-13334ded) — once
      answered, either proceed with the gated SUSHISWAP `--apply` (intent confirmed) or hold + document the rogue-delete
      disposition. (repo: unified-trading-pm; source: defi_satellite_ao_dispatch_batch11_2026_08_09.md)
