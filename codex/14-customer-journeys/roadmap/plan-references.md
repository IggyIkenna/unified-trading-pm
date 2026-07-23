---
doc_type: codex-ssot
title: Plan references
summary:
  Reference map pointing each next-waves.md follow-up wave item to where its current context already lives (existing
  plans, codex SSOTs, UI repo files) — avoids re-discovering context per new plan.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, unified-api-contracts, unified-trading-library, unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [roadmap, plan-hygiene, catalogue, dart, ui, registry]
related: [/codex/14-customer-journeys/roadmap/next-waves.md, ../../../plans/PLAN_FORMAT.md]
created: 2026-04-19
authoritative_for: [customer-journey follow-up wave reference map]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/roadmap/README.md,
    /codex/14-customer-journeys/roadmap/next-waves.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Plan references

For every follow-up wave in [next-waves.md](next-waves.md), where the current information lives. Use this to avoid
re-discovering context that's already in an existing plan or memory entry.

## Wave 1 — Demo flows

| Wave item                         | Reference                                                                                                                                  | Location                                |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------- |
| 1a. Staging Firebase              | [five_space_ia_execution_child_plan_2026_04_17.md](../../../plans/ai/five_space_ia_execution_child_plan_2026_04_17.md) ticket #12          | Active plan                             |
| 1a. Firebase staging details      | [docs/FIREBASE_ENVIRONMENTS.md](../../../../unified-trading-system-ui/docs/FIREBASE_ENVIRONMENTS.md)                                       | UI repo docs                            |
| 1a. Staging build template        | [config/docker-build.env.staging.firebase.example](../../../../unified-trading-system-ui/config/docker-build.env.staging.firebase.example) | UI repo config                          |
| 1b. Demo personas                 | [lib/auth/personas.ts](../../../../unified-trading-system-ui/lib/auth/personas.ts)                                                         | Current fixture (5 + 3 IR = 8 personas) |
| 1c. Visibility slicing            | MEMORY.md "Phase 10.5 backend shipped" entry                                                                                               | Conversation memory                     |
| 1c. UAC `slots_visible_to` helper | [unified-api-contracts strategy_availability](https://) Phase 10.5 commit                                                                  | UAC repo                                |
| 1c. Entitlement gate logic        | [components/shell/lifecycle-nav.tsx:102-113](../../../../unified-trading-system-ui/components/shell/lifecycle-nav.tsx#L102-L113)           | UI repo code                            |

## Wave 2 — Four-catalogue parity

| Wave item                          | Reference                                                                                                                                | Location               |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| 2a. Data catalogue SSOT            | [02-data/availability-manifest-and-data-status.md](../../02-data/availability-manifest-and-data-status.md)                               | Codex                  |
| 2a. Data capability declarations   | `unified-api-contracts/registry/capability_declarations/`                                                                                | UAC repo               |
| 2a. Availability manifest v4       | MEMORY.md / CLAUDE.md                                                                                                                    | Conversation           |
| 2b. UTL ml/ sub-package            | [unified-trading-library ml/](https://)                                                                                                  | UTL repo               |
| 2b. ML Model Catalogue             | No dedicated doc yet; cross-linked from [catalogue-ml-model.md](../playbook-concepts/catalogue-ml-model.md)                              | This SSOT              |
| 2c. execution-service algo_library | [execution-service/algo_library/](https://)                                                                                              | Execution service repo |
| 2c. Execution algos intro          | [catalogue-execution-algo.md](../playbook-concepts/catalogue-execution-algo.md)                                                          | This SSOT              |
| All catalogues pattern             | [catalogues.md](../playbook-concepts/catalogues.md)                                                                                      | This SSOT              |
| Strategy catalogue reference impl  | [catalogue-strategy.md](../playbook-concepts/catalogue-strategy.md) + [09-strategy/architecture-v2/](../../09-strategy/architecture-v2/) | This SSOT + Codex      |

## Wave 3 — Fund / org / client

| Wave item                     | Reference                                                                                                                                                                                                                                                                        | Location                        |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| 3a. JWT claims                | [firebase-production.md](../authentication/firebase-production.md) gap section                                                                                                                                                                                                   | This SSOT                       |
| 3b. User-mgmt provisioning    | [user_management_merge_2026_03_23.plan.md](../../../plans/ai/user_management_merge_2026_03_23.plan.md)                                                                                                                                                                           | Active plan                     |
| 3b. Fund / org / client model | [fund-org-hierarchy.md](../playbook-concepts/fund-org-hierarchy.md)                                                                                                                                                                                                              | This SSOT                       |
| 3b. SMA vs Pooled             | [sma-vs-pooled.md](../playbook-concepts/sma-vs-pooled.md) + [share_class_architecture_2026_04_01.plan.md](../../../plans/archive/share_class_architecture_2026_04_01.plan.md) + [04-architecture/share-class-architecture.md](../../04-architecture/share-class-architecture.md) | This SSOT + active plan + codex |
| 3c. API key issuance          | [07-security/secrets-management.md](../../07-security/secrets-management.md), UTL ApiKeyReloader pattern                                                                                                                                                                         | Codex                           |

## Wave 4 — DART rebrand

| Wave item                    | Reference                                                                                                                                                                                            | Location                 |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| 4a. UI nav files             | [site-header.tsx](../../../../unified-trading-system-ui/components/shell/site-header.tsx), [spaces-nav-sections.tsx](../../../../unified-trading-system-ui/components/shell/spaces-nav-sections.tsx) | UI repo                  |
| 4a. Playbook SSOT definition | [glossary.md](../glossary.md)                                                                                                                                                                        | This SSOT                |
| 4b. Marketing copy           | [public/homepage.html](../../../../unified-trading-system-ui/public/homepage.html), [lib/briefings/content.ts](../../../../unified-trading-system-ui/lib/briefings/content.ts)                       | UI repo                  |
| 4c. Trademark check          | Web search results (HSBC DART non-competing, DARTS India non-competing)                                                                                                                              | In-conversation research |

## Wave 5 — Orphan promotion

| Wave item                    | Reference                                                                                                            | Location           |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------ |
| Triage matrix                | [triage-matrix.md](../page-triage/triage-matrix.md)                                                                  | This SSOT          |
| Duplicate clusters           | [duplicate-clusters.md](../page-triage/duplicate-clusters.md)                                                        | This SSOT          |
| Partial archive              | [partial-archive.md](../page-triage/partial-archive.md)                                                              | This SSOT          |
| Promote lifecycle nav config | [lib/config/services/promote.config.ts](../../../../unified-trading-system-ui/lib/config/services/promote.config.ts) | UI repo            |
| Reports sub-nav (proposed)   | N/A yet                                                                                                              | New plan writes it |
| Observe merge proposal       | [duplicate-clusters.md](../page-triage/duplicate-clusters.md) item #7                                                | This SSOT          |

## Wave 6 — Nav-config cleanup

| Wave item      | Reference                                                     | Location  |
| -------------- | ------------------------------------------------------------- | --------- |
| Broken hrefs   | [broken-links.md](../page-triage/broken-links.md)             | This SSOT |
| Nav SSOT files | [information-architecture.md](../information-architecture.md) | This SSOT |

## Wave 7 — Staging smoke

| Wave item           | Reference                                                                                          | Location  |
| ------------------- | -------------------------------------------------------------------------------------------------- | --------- |
| Playwright setup    | [tests/e2e/playbooks/](../../../../unified-trading-system-ui/tests/e2e/playbooks/) (after Phase 5) | UI repo   |
| Test matrix         | [test-matrix.md](../testing/test-matrix.md)                                                        | This SSOT |
| Staging env details | [staging-odum-research-co-uk.md](../environments/staging-odum-research-co-uk.md)                   | This SSOT |

## Wave 8 — Briefings content

| Wave item             | Reference                                                                                  | Location  |
| --------------------- | ------------------------------------------------------------------------------------------ | --------- |
| Briefings fixture     | [lib/briefings/content.ts](../../../../unified-trading-system-ui/lib/briefings/content.ts) | UI repo   |
| Briefings session     | [lib/briefings/session.ts](../../../../unified-trading-system-ui/lib/briefings/session.ts) | UI repo   |
| Partial-archive list  | [partial-archive.md](../page-triage/partial-archive.md)                                    | This SSOT |
| IR presentation pages | `/investor-relations/*` routes                                                             | UI repo   |

## Cross-cutting references (useful for any new plan)

- Plan format: [../../../plans/PLAN_FORMAT.md](../../../plans/PLAN_FORMAT.md)
- Plan locking: MEMORY.md or PM repo README
- CLAUDE.md rules: repo root or codex/
- SUB_AGENT_MANDATORY_RULES.md: for Claude-invoked sub-agents
- Venue registry: [02-venues/](../../02-venues/)
- Strategy architecture v2: [09-strategy/architecture-v2/](../../09-strategy/architecture-v2/)
- Compliance: [07-security/compliance.md](../../07-security/compliance.md)
