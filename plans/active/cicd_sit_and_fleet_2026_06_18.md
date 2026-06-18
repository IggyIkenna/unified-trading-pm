---
title: CI/CD SIT + Fleet — system-integration-tests mechanics, fleet rulesets, UAC-orphan cap
name: cicd_sit_and_fleet_2026_06_18
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
created: 2026-06-18
date: 2026-06-18
author: ikenna [autonomous]
status: active
locked_by: live-defi-rollout
locked_since: 2026-06-18
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
parent_consolidation: cicd_docs_and_consolidation_2026_06_18
source:
  - sit_uac_orphan_cap_stale_consumer_list_2026_06_07 (consolidated)
  - cicd_contract_hardening_2026_06_01 (SIT + fleet subset)
---

> **Consolidated 2026-06-18** (see `cicd_docs_and_consolidation_2026_06_18`). **SSOT:**
> `codex/08-workflows/ci-cd-flow.md` (§ "Breaking = public-surface change" / SIT) + `CICD-WORKFLOW-CATALOG.md`. Zero
> open items dropped.
>
> **NOT consolidated here:** `fleet_audit_triad_deferred_followups_2026_06_01` stays standalone — it is a cross-domain
> fleet-audit grab-bag (its `[DATA]` tradfi/defi reprocess + GCS-migration items belong to the data-pipeline track, not
> cicd). Only its cicd-infra items are conceptually adjacent; it is referenced, not absorbed.

# CI/CD SIT + Fleet

**Scope.** The system-integration-tests gate (lock/debounce/unlock/starvation), the per-repo branch-protection ruleset
rollout, fleet-wide CI hygiene audits, and the UAC removed-symbol orphan cap that SIT consumers read.

## Open work

### SIT mechanics

- [ ] [SCRIPT] P2. Review `sit-gate.yml` + `sit-unlock.yml` membership in the `manifest-update` concurrency group
      (displacement-class review). (cicd_contract_hardening #26)
- [ ] [WORKFLOW] P2. Upgrade `sit-starvation-detector` from alert-only toward auto-redispatch (composes with the sprawl
      fold-into-`sit-debounce`; see cicd_release_machinery). (cicd_contract_hardening #28)
- [ ] [SCRIPT] P2. Promote `system-integration-tests` LDR→main so the SIT report-back goes live (promotion + e2e
      verify). (cicd_contract_hardening #30)
- [ ] [DESIGN] P2. Per-cone parallel staging locks (design doc — let independent dep cones promote concurrently).
      (cicd_contract_hardening #32)
- [ ] [SCRIPT] P2. Audit the fleet for `[skip ci]` version-bump commits stranded on staging (the same deadlock
      signature). (cicd_contract_hardening #25)

### Fleet ruleset rollout (blocked on per-repo QG-RED — real debt)

- [ ] [SCRIPT] P2. greeks-service ruleset — blocked on v2-RED (coverage floor + C901); fix the per-repo debt, then
      enable. (cicd_contract_hardening #15)
- [ ] [SCRIPT] P2. fund-administration ruleset — blocked on the uv-sync starlette cross-repo conflict; resolve, then
      enable. (cicd_contract_hardening #16)
- [ ] [SCRIPT] P2. e2e-testing ruleset — blocked on 14 ruff errors; fix, then enable. (cicd_contract_hardening #17)

### Fleet deploy-config + smokes

- [ ] [SCRIPT] P2. Tier-D — per-service Cloud Run deploy-config audit + add the missing HTTP deploys.
      (cicd_contract_hardening #12)
- [ ] [SCRIPT] P2. Tier-E — wire game-day + synthetic smokes into the staging SIT schedule. (cicd_contract_hardening
      #13)

### UAC orphan cap

- [ ] [SCRIPT] P2. Drive the 328 removed-symbol orphans down (add UTL to the consumer set and/or follow facade/`__all__`
      re-exports), then lower the cap from 400. (sit_uac_orphan)

## Closed on consolidation (premise superseded — not carried)

- uts-ui LDR→staging PR instability (CodeBuild + Vercel deploy fail) — CLOSED: the Vercel-strip (cicd_release_machinery,
  Vercel-app uninstall) removes the Vercel checks; UI deploy is a separate track. (cicd_contract_hardening #9)
- UAC+UTL `BATCH_HYPERLIQUID` enum migration half-promoted — CLOSED: explicitly OUT-OF-SCOPE for cicd; owned by the
  data/features track. (cicd_contract_hardening #22)

## Continuous verification

SIT: a breaking change locks staging, runs SIT, unlocks, and promotes — with no dangling lock surviving the
`sit-starvation-detector` window. Fleet: every repo carries the `quality-gates-v2` required-check ruleset (0 repos
unprotected). Orphan cap: the removed-symbol count trends down and the cap follows it.
