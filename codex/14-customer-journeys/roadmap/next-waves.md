---
doc_type: codex-ssot
title: Next waves
summary:
  Superseded follow-up-wave backlog (8 waves, ~6-7 new plans) for pb3 demo enablement — catalogue parity,
  fund/org/client scaffolding, DART rebrand, nav cleanup. Superseded 2026-04-20 by stage-3e-refactor-plan.md; kept for
  history only.
status: superseded
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [roadmap, catalogue, dart, ui, playbooks, plan-hygiene]
related:
  [
    /codex/14-customer-journeys/roadmap/plan-references.md,
    ../../16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md,
  ]
created: 2026-04-19
authoritative_for:
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/authentication/firebase-production.md,
    /codex/14-customer-journeys/authentication/firebase-staging.md,
    /codex/14-customer-journeys/implementation-mapping/playbook-to-qa-coverage.md,
    /codex/14-customer-journeys/page-triage/broken-links.md,
    /codex/14-customer-journeys/page-triage/triage-matrix.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-data.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-execution-algo.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Next waves

> **Superseded by [stage-3e-refactor-plan.md](../../16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md)**
> (2026-04-20).
>
> Stage 3E is the authoritative post-Stage-3 refactor backlog — 26 items grouped G1 / G2 / G3 with full context (current
> state, target state, blast radius, blockers, owner, proposed follow-up plan, unlocked playbooks). Content below is
> preserved for historical reference only. Do not add new wave items here; propose G-items to the Stage 3E doc.

Follow-up work items identified during the playbook SSOT plan. Each item is a candidate for its own plan (or rolls into
an existing active plan).

## Wave 1 — Unblock demo flows

Highest priority. Without these, pb3 demos can't run on staging.

### 1a. Staging Firebase project (`odum-staging`)

- **Owner**: Odum ops
- **Existing plan**:
  [five_space_ia_execution_child_plan_2026_04_17.md](../../../plans/ai/five_space_ia_execution_child_plan_2026_04_17.md)
  ticket #12
- **Blocked by**: nothing
- **Unblocks**: every pb3 test, demo-user lifecycle, prod/staging isolation
- **Rough scope**: create Firebase project, wire up build env, update user-management-ui to target either project,
  update docs
- **Plan needed**: NO — existing plan covers it

### 1b. Demo personas (`prospect-reg`, `prospect-dart`)

- **Owner**: UI
- **Blocked by**: staging Firebase (1a) for full fidelity; can add local fixtures today
- **Unblocks**: pb3a and pb3c Playwright tests
- **Rough scope**: add two personas to [lib/auth/personas.ts](unified-trading-system-ui/lib/auth/personas.ts),
  entitlements scoped per flavour
- **Plan needed**: small — can be a ticket in an existing UI plan

### 1c. Visibility slicing — LOCKED-VISIBLE mode

- **Owner**: UI
- **Blocked by**: nothing (code-local change)
- **Unblocks**: pb3a/pb3b correct behaviour (padlock + "contact us" CTA instead of hidden)
- **Rough scope**: add `lockState` prop to service-tile component; render padlock + CTA when user lacks entitlement but
  tile is not truly hidden (demo mode marker)
- **Plan needed**: YES — new small plan for visibility-slicing implementation

## Wave 2 — Four-catalogue parity

Unify the three fragmented catalogues (Data, ML Model, Execution Algo) to match Strategy Catalogue.

### 2a. Data Catalogue surface

- **Owner**: UI + instruments-service/MTDS for SSOT
- **Blocked by**: partial — underlying SSOT exists in services, UAC has capability declarations
- **Unblocks**: pb3c complete DART demo (currently data surface is 13-page jungle)
- **Rough scope**:
  - Create unified `/services/data-catalogue/` surface OR refactor `/services/data/` to catalogue pattern
  - Coverage matrix: instrument × venue × data_type × availability
  - Per-entry detail page
  - Admin surface for lock-state
  - Merge gaps / completeness / missing per triage decision
- **Plan needed**: YES — new plan for data catalogue refactor

### 2b. ML Model Catalogue surface

- **Owner**: UI + UTL for SSOT
- **Blocked by**: audit of UTL ml/ registry completeness
- **Unblocks**: pb3c complete DART demo for ML archetype
- **Rough scope**:
  - Audit [UTL ml/](https://) registry completeness
  - Add UAC declarations if missing
  - Create unified `/services/ml-catalogue/` surface (or promote research/ml to catalogue)
  - Coverage matrix, per-entry detail, admin lock-state, governance tab
- **Plan needed**: YES — new plan for ML model catalogue

### 2c. Execution Algo Catalogue surface

- **Owner**: UI + execution-service for SSOT
- **Blocked by**: audit of execution-service algo_library + UAC declarations
- **Unblocks**: pb3c complete DART demo for execution surface
- **Rough scope**:
  - Audit [execution-service/algo_library/](https://)
  - Add UAC declarations if missing
  - Decide: unified `/services/execution-catalogue/` OR keep under `/services/execution/`?
  - Coverage matrix, per-entry detail
  - Fix `/services/execution/tca` broken link (build the page)
- **Plan needed**: YES — new plan for execution algo catalogue

## Wave 3 — Fund / org / client scaffolding

The structural model from [../cross-cutting/fund-org-hierarchy.md](../playbook-concepts/fund-org-hierarchy.md) needs
full implementation before pb3a/pb3b demos are meaningful.

### 3a. Org-scoped JWT claims

- **Owner**: user-management-api + UI
- **Blocked by**: nothing
- **Unblocks**: client-reporting views can filter by fund+client at JWT layer
- **Rough scope**: extend Firebase custom claims to carry `fund_id` and `client_id`; UI reads via firebase-provider
- **Plan needed**: YES — new plan

### 3b. user-management-ui fund/client provisioning workflow

- **Owner**: user-management-ui
- **Existing plan**:
  [user_management_merge_2026_03_23.plan.md](../../../plans/ai/user_management_merge_2026_03_23.plan.md) (Phase 1-5
  mostly done)
- **Blocked by**: staging Firebase (1a)
- **Unblocks**: admin can actually provision demo prospects end-to-end
- **Rough scope**: extend beyond user-CRUD to org + fund (Pooled/SMA) + client creation with per-client API key gen
- **Plan needed**: MAYBE — may be extension to existing user-management-merge plan

### 3c. Per-client API key issuance flow

- **Owner**: user-management-api + Secret Manager
- **Blocked by**: 3b
- **Unblocks**: pb3 demos show realistic per-client keys
- **Rough scope**: API key generation → Secret Manager → displayed in UI on client-detail page
- **Plan needed**: YES — new plan

## Wave 4 — DART rebrand in UI

### 4a. UI nav label change

- **Owner**: UI
- **Blocked by**: nothing
- **Unblocks**: DART trade name consistency
- **Rough scope**: update [components/shell/site-header.tsx](unified-trading-system-ui/components/shell/site-header.tsx)
  label from "Data, Research & Trading" to "DART" with "Data Analytics, Research & Trading" tooltip; update
  [components/shell/spaces-nav-sections.tsx](unified-trading-system-ui/components/shell/spaces-nav-sections.tsx); keep
  route `/platform` unchanged
- **Plan needed**: SMALL — ticket in next UI plan

### 4b. DART acronym in marketing copy

- **Owner**: Marketing / content
- **Blocked by**: 4a
- **Unblocks**: consistency
- **Rough scope**: update [public/homepage.html](unified-trading-system-ui/public/homepage.html) + briefings content to
  use DART acronym
- **Plan needed**: SMALL — ticket

### 4c. Legal / trademark check

- **Owner**: Marketing / legal
- **Blocked by**: nothing
- **Unblocks**: production use of DART name
- **Rough scope**: clear DART for trademark conflicts (HSBC DART in payments is non-competing per audit; confirm
  legally)
- **Plan needed**: NO — legal consult

## Wave 5 — Orphan promotion from triage matrix

Each `promote` action in [../page-triage/triage-matrix.md](../page-triage/triage-matrix.md) eventually gets wired into
nav or into a playbook surface. Many are currently tab-only.

### 5a. Promote lifecycle nav wiring (8 pages)

- **Owner**: UI
- **Blocked by**: nothing
- **Rough scope**: wire `PROMOTE_LIFECYCLE_NAV` to show all 8 lifecycle pages as stepper tabs from `/services/promote`
- **Plan needed**: SMALL — ticket

### 5b. Reports sub-nav consolidation

- **Owner**: UI
- **Blocked by**: nothing
- **Rough scope**: wire all 12 reports pages under a consistent sub-nav in `/services/reports/overview`
- **Plan needed**: SMALL — ticket

### 5c. Observe audit cluster merge (event-audit + recovery + registry → health tabs)

- **Owner**: UI
- **Blocked by**: nothing
- **Rough scope**: per duplicate-clusters.md item #7, fold into health
- **Plan needed**: SMALL — ticket

## Wave 6 — Nav-config cleanup

### 6a. Broken href fixes (4 confirmed)

- **Owner**: UI
- **Status**: **executed in this plan's Phase 3**
- **Details**: [../page-triage/broken-links.md](../page-triage/broken-links.md)

### 6b. Probable broken ML routes

- **Owner**: UI
- **Blocked by**: ML Catalogue decision (wave 2b)
- **Details**: [../page-triage/broken-links.md](../page-triage/broken-links.md) "5 probable"

## Wave 7 — Staging smoke tests

### 7a. Playwright suite against staging domain

- **Owner**: CI
- **Blocked by**: staging Firebase (1a)
- **Rough scope**: new spec dir `tests/playbooks/staging/` that hits real `odum-research.co.uk` with dedicated
  test-prospect credentials
- **Plan needed**: SMALL

## Wave 8 — Briefings content expansion

### 8a. Move briefings content from fixture to CMS or codex

- **Owner**: Marketing / content
- **Blocked by**: nothing
- **Rough scope**: decide if [lib/briefings/content.ts](unified-trading-system-ui/lib/briefings/content.ts) fixture is
  the long-term home, or migrate to CMS or codex-transclusion
- **Plan needed**: SMALL — needs decision

### 8b. Briefings partial-archive integration (IR slide extraction)

- **Owner**: Content
- **Details**: [../page-triage/partial-archive.md](../page-triage/partial-archive.md)
- **Plan needed**: SMALL

## Summary

| Wave | Plans needed                                                   | Unblocks                           |
| ---- | -------------------------------------------------------------- | ---------------------------------- |
| 1    | 1 new (visibility-slicing) + existing five_space_ia ticket #12 | pb3 demos on staging               |
| 2    | 3 new (Data / ML / Exec catalogue)                             | pb3c DART demo complete            |
| 3    | 2-3 new                                                        | pb3a/pb3b fund-client provisioning |
| 4    | ticket-sized                                                   | DART rebrand                       |
| 5    | ticket-sized × 3                                               | orphan nav wiring                  |
| 6    | done in this plan                                              | nav cleanup                        |
| 7    | 1 small                                                        | staging smoke                      |
| 8    | 1 small                                                        | briefings content strategy         |

**Total new plans**: ~6-7. Plus several ticket-sized items in existing plans.

## Plan reference map

For each wave item, where its reference info lives today → [plan-references.md](plan-references.md).
