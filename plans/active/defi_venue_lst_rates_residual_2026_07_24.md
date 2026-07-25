---
doc_type: plan
title: DeFi venue hygiene + lst-rates aggregation residual — forked from migration_verification_orphan_safety_2026_06_10
summary: >-
  2 small residual todos forked verbatim out of the archived migration-verification/orphan-safety harness plan
  (2026-07-24 plan line-cap remediation split): folding the `lst-rates` corpus into the DeFi could-exist / data-status
  view, and reconciling orphan/junk DeFi venue spellings (`VAULT`, `SUSHISWAP` classic-vs-V3 ambiguity).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [defi, lst-rates, venue-canonicalisation, manifest, migration, plan-split, residual]
related:
  [
    /plans/active/migration_verification_orphan_safety_2026_06_10.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Forked verbatim from `plans/active/migration_verification_orphan_safety_2026_06_10.md` (its own Progress Log, entry
  dated 2026-06-16) as part of the 2026-07-24 plan line-cap remediation
  (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 18 / bucket (d)). The parent plan's durable
  protocol (CF-15…CF-21) had already migrated to codex; these were the last genuinely-open items in its defi-venue
  thread and are tracked here going forward.
---

# DeFi venue hygiene + lst-rates aggregation residual

> **Origin.** Both todos below are moved **verbatim** from
> `plans/active/migration_verification_orphan_safety_2026_06_10.md` (now trimmed + unlocked; full historical Progress
> Log archived to `plans/audit/results/migration_orphan_safety_goalpost_verification_2026_06_10.md` as an Appendix).
> Neither is a data gap — both are data-status aggregation / venue-spelling hygiene items, explicitly NICE-TO-HAVE / P3
> in the source.

## Todos

- [ ] [DATA] P3. **NICE-TO-HAVE — fold the `lst-rates` corpus into the DeFi could-exist / data-status view.** The 5 LST
      venues (ANKR/STADER/STAKEWISE/SWELL/MANTLE + LIDO/ROCKETPOOL/ETHENA/… already-live) have captured `lst_rates` data
      in the dedicated `lst-rates-central-element-323112` bucket, but the defi projected index + the deployment-api
      could-exist drilldown read only the `market-data-tick-defi` corpus → these venues' real rows are invisible in the
      DeFi data-status (read as zero). Fold the `lst-rates` availability_index into the defi data-status aggregation
      (the rollup/`manifest_source` read path) so their captured rows are credited. NOT a data gap (data exists) — a
      data-status aggregation completeness item. Repos: deployment-api (data_status aggregation) + the defi projection
      rebuild. Provenance: 2026-06-16 lst-rates bucket verification.
- [ ] [DATA] P3. **Orphan / junk defi venues** — `VAULT` (generic, 1113 captured rows, not a protocol → exclude or map
      to the real protocol) + `SUSHISWAP` classic-vs-`SUSHISWAP_V3` ambiguity (data-semantics call: is bare `SUSHISWAP`
      the classic AMM = `SUSHISWAP-ARBITRUM`, or V3?). Reconcile `ALL_DEFI_VENUES` / `LEGACY_DEFI_VENUE_ALIASES` to
      remove the residual orphans.

## Success criteria

1. `lst-rates` captured rows are credited in the DeFi could-exist / data-status view (verified: the 5 LST venues no
   longer read as zero).
2. `VAULT` + `SUSHISWAP` classic-vs-V3 ambiguity resolved in `ALL_DEFI_VENUES` / `LEGACY_DEFI_VENUE_ALIASES` (data-
   semantics call made + encoded).

## Progress Log

- 2026-07-24 — plan forked from `migration_verification_orphan_safety_2026_06_10.md` (line-cap remediation split); no
  further work done yet beyond what the parent's archived Progress Log already recorded.
