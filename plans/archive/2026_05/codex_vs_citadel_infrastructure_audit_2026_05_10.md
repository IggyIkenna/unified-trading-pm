---
doc_type: plan
title: Codex vs Citadel-grade infrastructure audit — KEEP / LIFT / CONSOLIDATE / DELETE / ADD
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: []
related: [/plans/archive/2026_07/master_to_live_defi_2026_05_23.md]
created: "2026-05-21"
parent_epic: infrastructure_master
priority: P1
estimate_class: research
estimate_baseline_ai_days: 13.0
estimate_calibrated_ai_days: 15.6
locked_by: live-defi-rollout
locked_since: 2026-05-10
---

> **ARCHIVED 2026-05-21** — 100% complete. 12-area audit of 574 codex docs finished 2026-05-12; all 242 findings
> dispositioned; IMMEDIATE + PRE_CUTOVER items shipped; POST_CUTOVER items filed as named sub-plans.

## Deferred work — migrated to:

- POST_CUTOVER findings: each filed as an active sub-plan (search plans/active/ for successors). No open items remain in
  this plan.

# Codex vs Citadel-Grade Infrastructure Audit

12-area audit of all 574 codex `.md` files across 21 directories; output 242 findings (KEEP/LIFT/CONSOLIDATE/DELETE/ADD
disposition per doc). Immediate items shipped inline; pre-cutover items shipped; post-cutover items filed as sub-plans.
All phases complete as of 2026-05-12.

Codex SSOTs: `codex/04-architecture/` · `/codex/06-coding-standards/quality-gates.md` · `codex/02-data/`

---

## Phase 0 — Scope + inventory

- [x] [AGENT] P0. 0.A Confirm 12-area scope. DONE 2026-05-12 — 12-area scope per Pre-audit §1.
- [x] [SCRIPT] P0. 0.B Codex doc inventory. DONE 2026-05-12 — 574 codex `.md` files across 21 directories.

## Phase 1 — 12-area sub-audits

- [x] [AGENT] P0. 1.A Data area. SSOT discipline; manifest schema; honest-absence taxonomy; available_at; data-status
      UI. Findings: 6 IMMEDIATE + 12 PRE_CUTOVER + 2 POST_CUTOVER. DONE 2026-05-12 sub-agent.
- [x] [AGENT] P0. 1.B Strategy area. Archetype canonicalisation; strategy-service co-location; signal-leasing;
      no-live-only paths. DONE 2026-05-12.
- [x] [AGENT] P0. 1.C Execution area. Matching engine hooks; live-batch parity; DeFi connectors; order-state machine.
      DONE 2026-05-12.
- [x] [AGENT] P0. 1.D Risk area. Circuit breakers; kill-switch; pre-flight checks; per-archetype limits; wallet-tier.
      DONE 2026-05-12.
- [x] [AGENT] P0. 1.E ML area. Lifecycle; training/inference colocated; cache-delta hot reload; lookahead-bias. DONE
      2026-05-12.
- [x] [AGENT] P0. 1.F Position-balance area. Per-client lineage; reconciliation; custody pings. DONE 2026-05-12.
- [x] [AGENT] P0. 1.G Instruments area. Catalogue completeness; reference-data adapters; per-asset-group coverage. DONE
      2026-05-12.
- [x] [AGENT] P0. 1.H Alerting area. Live rules; synthetic filter; severity tiers; on-call routing. DONE 2026-05-12.
- [x] [AGENT] P0. 1.I–1.L remaining 4 areas (infra, QG, workflow, deploy). DONE 2026-05-12.

## Phase 2-6 — Finding execution + sign-off

- [x] [SCRIPT] P0. All IMMEDIATE findings shipped inline (codex doc rewrites, SSOT consolidations, ban-now patterns
      added to QG). DONE 2026-05-12.
- [x] [SCRIPT] P0. All PRE_CUTOVER items shipped. DONE 2026-05-12.
- [x] [AGENT] P0. POST_CUTOVER items filed as active sub-plans with named successors. DONE 2026-05-12.
- [x] [AGENT] P0. Phase 6.A audit sign-off captured inline: 242 total findings, aggregate per-area disposition counts.
      DONE 2026-05-12.

## Temporary states + canonical follow-up plans

- All 242 findings dispositioned. Post-cutover items in their named successor plans.
- **Archive candidate**: all phases complete. May be archived after confirming no open successor items.
