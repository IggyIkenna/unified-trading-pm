---
doc_type: codex-ssot
title: Triage matrix — master table
summary:
  Master triage table classifying all 158 unified-trading-system-ui + 19 user-management-ui routes as
  HUB/LINKED/ORPHAN/DYNAMIC/BROKEN_LINK_TARGET with a promote/refactor/merge-into/partial-archive/defer action and
  confidence; deprecate count is intentionally 0.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [ui, page-triage, audit, navigation, refactor, consolidation]
related:
  [
    /codex/14-customer-journeys/page-triage/broken-links.md,
    /codex/14-customer-journeys/page-triage/duplicate-clusters.md,
    /codex/14-customer-journeys/page-triage/partial-archive.md,
    ../roadmap/next-waves.md,
  ]
created: 2026-04-19
authoritative_for: [UI page-triage classification matrix (route -> action)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/information-architecture.md,
    /codex/14-customer-journeys/page-triage/README.md,
    /codex/14-customer-journeys/page-triage/broken-links.md,
    /codex/14-customer-journeys/page-triage/duplicate-clusters.md,
    /codex/14-customer-journeys/page-triage/partial-archive.md,
    /codex/14-customer-journeys/playbook-concepts/investor-relations.md,
    /codex/14-customer-journeys/playbooks/02a-research-im.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Triage matrix — master table

Every route in unified-trading-system-ui (158 pages) + user-management-ui (19 pages) classified against the playbook
spec. Actions drive follow-up plans.

**Data source:** static audit (Phase 0 of the parent plan). Columns:

- `classification` — HUB / LINKED / ORPHAN / DYNAMIC / BROKEN_LINK_TARGET
- `reuse_hint` — which playbook family this could serve
- `action` — promote / refactor / merge-into / partial-archive / deprecate / defer
- `confidence` — High / Medium / Low (how sure we are about the action)

Action legend: see [README.md](README.md).

---

## (public) — 18 routes

| route                         | classification | reuse_hint              | action                              | confidence | notes                                                                |
| ----------------------------- | -------------- | ----------------------- | ----------------------------------- | ---------- | -------------------------------------------------------------------- |
| `/`                           | HUB            | pb1:marketing           | `promote`                           | High       | Canonical homepage — marketing static                                |
| `/investment-management`      | HUB            | pb1:marketing           | `promote`                           | High       | IM service landing                                                   |
| `/platform`                   | HUB            | pb1:marketing           | `promote`                           | High       | DART service landing (UI rebrand to DART label)                      |
| `/regulatory`                 | HUB            | pb1:marketing           | `promote`                           | High       | Reg Umbrella service landing                                         |
| `/firm`                       | HUB            | pb1:marketing           | `promote`                           | High       | Who-we-are                                                           |
| `/contact`                    | HUB            | pb1:marketing           | `promote`                           | High       | Enquiry form                                                         |
| `/demo`                       | LINKED         | pb1:marketing           | `promote`                           | High       | Book a demo                                                          |
| `/demo/preview`               | ORPHAN         | pb1:marketing (unclear) | `defer`                             | Low        | Has broken `/presentation` link; purpose unclear; may fit pb3 signup |
| `/docs`                       | HUB            | pb2:dart-deep           | `promote`                           | High       | Developer docs — reused by pb2                                       |
| `/briefings`                  | HUB            | pb2:\*                  | `promote`                           | High       | Briefings hub                                                        |
| `/briefings/[slug]`           | DYNAMIC        | pb2:\*                  | `promote`                           | High       | Per-pillar briefing pages                                            |
| `/login`                      | HUB            | pb3:\*                  | `promote`                           | High       | Firebase + demo sign-in                                              |
| `/signup`                     | LINKED         | pb3:demo-\*             | `promote`                           | High       | Mock signup                                                          |
| `/pending`                    | ORPHAN         | pb3:demo-\*             | `defer`                             | Low        | Awaiting-approval state; may fit pb3 signup                          |
| `/privacy`, `/terms`          | LINKED         | pb1:marketing           | `promote`                           | High       | Legal                                                                |
| `/services/backtesting`       | ORPHAN         | pb1:marketing           | `merge-into:/platform`              | Medium     | Early-stage public marketing card                                    |
| `/services/data` (public)     | ORPHAN         | pb1:marketing           | `merge-into:/platform`              | Medium     | Duplicate of platform landing                                        |
| `/services/investment`        | ORPHAN         | pb1:marketing           | `merge-into:/investment-management` | Medium     | Duplicate of IM landing                                              |
| `/services/platform` (public) | ORPHAN         | pb1:marketing           | `merge-into:/platform`              | Medium     | Duplicate                                                            |
| `/services/regulatory`        | LINKED         | pb1:marketing           | `merge-into:/regulatory`            | Medium     | Footer link target; keep alive as redirect during merge              |
| `/health`                     | LINKED         | ops:internal            | `promote`                           | High       | Dev health page                                                      |

---

## (platform)/services/data — 13 routes → Data Catalogue surface

| route                         | classification | reuse_hint           | action                           | confidence | notes                                                           |
| ----------------------------- | -------------- | -------------------- | -------------------------------- | ---------- | --------------------------------------------------------------- |
| `/services/data/overview`     | HUB            | cross:catalogue-data | `refactor`                       | High       | Landing; needs catalogue-pattern treatment                      |
| `/services/data/instruments`  | LINKED         | cross:catalogue-data | `refactor`                       | High       | Currently list; needs per-instrument detail route               |
| `/services/data/venues`       | ORPHAN         | cross:catalogue-data | `refactor`                       | Medium     | Part of unified catalogue surface                               |
| `/services/data/coverage`     | LINKED         | cross:catalogue-data | `promote`                        | High       | Coverage view                                                   |
| `/services/data/completeness` | ORPHAN         | cross:catalogue-data | `merge-into:/services/data/gaps` | High       | Duplicate concept                                               |
| `/services/data/missing`      | ORPHAN         | cross:catalogue-data | `merge-into:/services/data/gaps` | High       | Duplicate concept                                               |
| `/services/data/gaps`         | LINKED         | cross:catalogue-data | `promote`                        | High       | Canonical name after merge                                      |
| `/services/data/events`       | ORPHAN         | cross:catalogue-data | `refactor`                       | Medium     | Data event log                                                  |
| `/services/data/logs`         | ORPHAN         | ops:internal         | `promote`                        | Medium     | Ops log view                                                    |
| `/services/data/processing`   | ORPHAN         | ops:internal         | `promote`                        | Medium     | Processing status                                               |
| `/services/data/raw`          | ORPHAN         | cross:catalogue-data | `refactor`                       | Medium     | Raw data view                                                   |
| `/services/data/valuation`    | ORPHAN         | cross:catalogue-data | `refactor`                       | Medium     | Valuation view                                                  |
| `/services/data/markets/pnl`  | ORPHAN         | pb3:demo-dart        | `refactor`                       | Medium     | Broken `/markets/pnl` href also points here; fix href + surface |

---

## (platform)/services/research — 25 routes

| route                                              | classification | reuse_hint               | action                                                                  | confidence | notes                                 |
| -------------------------------------------------- | -------------- | ------------------------ | ----------------------------------------------------------------------- | ---------- | ------------------------------------- |
| `/services/research` (base)                        | LINKED         | pb3:demo-dart            | `promote`                                                               | High       | Research landing                      |
| `/services/research/overview`                      | HUB            | pb3:demo-dart            | `promote`                                                               | High       | Primary landing                       |
| `/services/research/quant`                         | LINKED         | pb3:demo-dart            | `promote`                                                               | High       | Quant tools                           |
| `/services/research/signals`                       | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     | Tab-only; wire into research overview |
| `/services/research/feature-etl`                   | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     | Feature pipeline                      |
| `/services/research/features`                      | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     | Feature list                          |
| `/services/research/execution`                     | LINKED         | pb3:demo-dart            | `promote`                                                               | High       | Execution research                    |
| `/services/research/ml`                            | HUB            | cross:catalogue-ml       | `refactor`                                                              | High       | ML catalogue base — needs unification |
| `/services/research/ml/registry`                   | LINKED         | cross:catalogue-ml       | `promote`                                                               | High       | Model registry                        |
| `/services/research/ml/training`                   | LINKED         | cross:catalogue-ml       | `promote`                                                               | High       | Training runs                         |
| `/services/research/ml/analysis`                   | ORPHAN         | cross:catalogue-ml       | `promote`                                                               | Medium     |                                       |
| `/services/research/ml/config`                     | ORPHAN         | cross:catalogue-ml       | `promote`                                                               | Medium     |                                       |
| `/services/research/ml/governance`                 | ORPHAN         | cross:catalogue-ml       | `promote`                                                               | Medium     |                                       |
| `/services/research/ml/grid-config`                | ORPHAN         | cross:catalogue-ml       | `promote`                                                               | Medium     |                                       |
| `/services/research/ml/monitoring`                 | ORPHAN         | cross:catalogue-ml       | `promote`                                                               | Medium     |                                       |
| `/services/research/strategies`                    | LINKED         | cross:catalogue-strategy | `merge-into:/services/strategy-catalogue`                               | High       | Legacy strategy listing               |
| `/services/research/strategy/catalog`              | HUB            | cross:catalogue-strategy | `merge-into:/services/strategy-catalogue`                               | High       | Legacy catalog — Phase 10.6 replaces  |
| `/services/research/strategy/catalog/[strategyId]` | DYNAMIC        | cross:catalogue-strategy | `merge-into:/services/strategy-catalogue/strategies/[archetype]/[slot]` | High       | Legacy per-strategy                   |
| `/services/research/strategy/families`             | HUB            | cross:catalogue-strategy | `merge-into:/services/strategy-catalogue`                               | High       | Legacy                                |
| `/services/research/strategy/families/[family]`    | DYNAMIC        | cross:catalogue-strategy | `merge-into:/services/strategy-catalogue`                               | High       | Legacy                                |
| `/services/research/strategy/overview`             | HUB            | cross:catalogue-strategy | `merge-into:/services/strategy-catalogue`                               | High       | Legacy                                |
| `/services/research/strategy/backtests`            | LINKED         | pb3:demo-dart            | `promote`                                                               | High       | Still useful as research tool         |
| `/services/research/strategy/candidates`           | LINKED         | pb3:demo-dart            | `promote`                                                               | High       | Promote flow input                    |
| `/services/research/strategy/allocator`            | ORPHAN         | cross:catalogue-strategy | `defer`                                                                 | Medium     | Phase 10.7 splits into IM + DART      |
| `/services/research/strategy/compare`              | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     | Comparison tool                       |
| `/services/research/strategy/execution-policies`   | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     |                                       |
| `/services/research/strategy/handoff`              | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     | Research → promote                    |
| `/services/research/strategy/heatmap`              | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     | Visualisation                         |
| `/services/research/strategy/results`              | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     |                                       |
| `/services/research/strategy/sports`               | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     | Sports-specific research              |
| `/services/research/strategy/unity`                | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     | Unity-specific                        |
| `/services/research/strategy/venues`               | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     |                                       |

---

## (platform)/services/strategy-catalogue — 6 routes

| route                                                        | classification | reuse_hint               | action    | confidence | notes                          |
| ------------------------------------------------------------ | -------------- | ------------------------ | --------- | ---------- | ------------------------------ |
| `/services/strategy-catalogue`                               | HUB            | cross:catalogue-strategy | `promote` | High       | Canonical catalogue (Phase 10) |
| `/services/strategy-catalogue/coverage`                      | HUB            | cross:catalogue-strategy | `promote` | High       |                                |
| `/services/strategy-catalogue/coverage/blocked`              | LINKED         | cross:catalogue-strategy | `promote` | High       |                                |
| `/services/strategy-catalogue/coverage/by-combination`       | LINKED         | cross:catalogue-strategy | `promote` | High       |                                |
| `/services/strategy-catalogue/strategies/[archetype]/[slot]` | DYNAMIC        | cross:catalogue-strategy | `promote` | High       | Per-strategy detail            |
| `/services/strategy-catalogue/admin/lock-state`              | LINKED         | cross:catalogue-strategy | `promote` | High       | Admin surface                  |

---

## (platform)/services/trading — 30 routes

| route                                           | classification | reuse_hint               | action                                                                  | confidence | notes                      |
| ----------------------------------------------- | -------------- | ------------------------ | ----------------------------------------------------------------------- | ---------- | -------------------------- |
| `/services/trading/overview`                    | HUB            | pb3:demo-dart            | `promote`                                                               | High       | Trading landing            |
| `/services/trading/terminal`                    | HUB            | pb3:demo-dart            | `promote`                                                               | High       | Live DART trading terminal |
| `/services/trading/accounts`                    | LINKED         | pb3:demo-dart            | `promote`                                                               | High       | Account list               |
| `/services/trading/accounts/saft`               | ORPHAN         | pb3:demo-im              | `defer`                                                                 | Low        | SAFT flow                  |
| `/services/trading/alerts`                      | LINKED         | pb3:demo-dart            | `promote`                                                               | High       |                            |
| `/services/trading/book`                        | LINKED         | pb3:demo-dart            | `promote`                                                               | High       |                            |
| `/services/trading/bundles`                     | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     |                            |
| `/services/trading/defi`                        | LINKED         | pb3:demo-dart            | `promote`                                                               | High       | DeFi section               |
| `/services/trading/defi/staking`                | LINKED         | pb3:demo-dart            | `promote`                                                               | High       |                            |
| `/services/trading/instructions`                | LINKED         | pb3:demo-dart            | `promote`                                                               | High       | Manual instructions        |
| `/services/trading/markets`                     | LINKED         | pb3:demo-dart            | `promote`                                                               | High       |                            |
| `/services/trading/options`                     | LINKED         | pb3:demo-dart            | `promote`                                                               | High       |                            |
| `/services/trading/options/combos`              | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     | Combo builder              |
| `/services/trading/options/pricing`             | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     |                            |
| `/services/trading/orders`                      | LINKED         | pb3:demo-dart            | `promote`                                                               | High       |                            |
| `/services/trading/pnl`                         | LINKED         | pb3:demo-dart            | `promote`                                                               | High       |                            |
| `/services/trading/positions`                   | LINKED         | pb3:demo-dart            | `promote`                                                               | High       |                            |
| `/services/trading/positions/trades`            | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     | Wire into positions as tab |
| `/services/trading/predictions`                 | LINKED         | pb3:demo-dart            | `promote`                                                               | High       |                            |
| `/services/trading/predictions/aggregators`     | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     |                            |
| `/services/trading/risk`                        | HUB            | pb3:demo-dart            | `promote`                                                               | High       |                            |
| `/services/trading/sports`                      | LINKED         | pb3:demo-dart            | `promote`                                                               | High       |                            |
| `/services/trading/sports/accumulators`         | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     |                            |
| `/services/trading/sports/bet`                  | ORPHAN         | pb3:demo-dart            | `promote`                                                               | Medium     |                            |
| `/services/trading/strategies`                  | LINKED         | cross:catalogue-strategy | `merge-into:/services/strategy-catalogue`                               | Medium     | Likely legacy              |
| `/services/trading/strategies/[id]`             | DYNAMIC        | cross:catalogue-strategy | `merge-into:/services/strategy-catalogue/strategies/[archetype]/[slot]` | Medium     |                            |
| `/services/trading/strategies/basis-trade`      | ORPHAN         | cross:catalogue-strategy | `merge-into:/services/strategy-catalogue`                               | Medium     |                            |
| `/services/trading/strategies/grid`             | ORPHAN         | cross:catalogue-strategy | `merge-into:/services/strategy-catalogue`                               | Medium     |                            |
| `/services/trading/strategies/model-portfolios` | ORPHAN         | cross:catalogue-strategy | `merge-into:/services/strategy-catalogue`                               | Medium     |                            |
| `/services/trading/strategies/staked-basis`     | ORPHAN         | cross:catalogue-strategy | `merge-into:/services/strategy-catalogue`                               | Medium     |                            |
| `/services/trading/custom/[id]`                 | DYNAMIC        | pb3:demo-dart            | `promote`                                                               | Medium     | Custom trading page        |

---

## (platform)/services/execution — 7 routes → Execution Algo Catalogue surface

| route                               | classification     | reuse_hint           | action           | confidence | notes                                        |
| ----------------------------------- | ------------------ | -------------------- | ---------------- | ---------- | -------------------------------------------- |
| `/services/execution/overview`      | HUB                | cross:catalogue-exec | `refactor`       | High       | Needs catalogue-pattern treatment            |
| `/services/execution/algos`         | ORPHAN             | cross:catalogue-exec | `refactor`       | High       | Core catalogue list                          |
| `/services/execution/benchmarks`    | ORPHAN             | cross:catalogue-exec | `refactor`       | Medium     |                                              |
| `/services/execution/candidates`    | ORPHAN             | cross:catalogue-exec | `refactor`       | Medium     |                                              |
| `/services/execution/handoff`       | ORPHAN             | cross:catalogue-exec | `refactor`       | Medium     |                                              |
| `/services/execution/venues`        | ORPHAN             | cross:catalogue-exec | `refactor`       | Medium     |                                              |
| `/services/execution/[executionId]` | DYNAMIC            | cross:catalogue-exec | `refactor`       | Medium     | Per-execution detail                         |
| `/services/execution/tca`           | BROKEN_LINK_TARGET | cross:catalogue-exec | `build-or-prune` | High       | Referenced but missing — see broken-links.md |

---

## (platform)/services/observe — 10 routes

| route                               | classification | reuse_hint    | action                                | confidence | notes               |
| ----------------------------------- | -------------- | ------------- | ------------------------------------- | ---------- | ------------------- |
| `/services/observe/health`          | HUB            | pb3:demo-dart | `promote`                             | High       |                     |
| `/services/observe/risk`            | HUB            | pb3:demo-dart | `promote`                             | High       |                     |
| `/services/observe/alerts`          | LINKED         | pb3:demo-dart | `promote`                             | High       |                     |
| `/services/observe/event-audit`     | ORPHAN         | ops:internal  | `promote`                             | Medium     | Internal audit view |
| `/services/observe/news`            | ORPHAN         | pb3:demo-dart | `promote`                             | Medium     |                     |
| `/services/observe/reconciliation`  | ORPHAN         | pb3:demo-dart | `merge-into:/services/observe/health` | Medium     | Tab it into health  |
| `/services/observe/recovery`        | ORPHAN         | ops:internal  | `merge-into:/services/observe/health` | Medium     | Tab                 |
| `/services/observe/registry`        | ORPHAN         | ops:internal  | `merge-into:/services/observe/health` | Medium     | Tab                 |
| `/services/observe/scenarios`       | ORPHAN         | pb3:demo-dart | `promote`                             | Medium     | Scenario testing    |
| `/services/observe/strategy-health` | ORPHAN         | pb3:demo-dart | `promote`                             | Medium     |                     |

---

## (platform)/services/promote — 10 routes (lifecycle)

All 8 lifecycle pages are orphans per static audit — `/services/promote` only links to `/pipeline`. Phase 3 wires them
via `PROMOTE_LIFECYCLE_NAV`.

| route                                   | classification | reuse_hint    | action    | confidence | notes                  |
| --------------------------------------- | -------------- | ------------- | --------- | ---------- | ---------------------- |
| `/services/promote`                     | HUB            | pb3:demo-dart | `promote` | High       | Lifecycle landing      |
| `/services/promote/pipeline`            | LINKED         | pb3:demo-dart | `promote` | High       |                        |
| `/services/promote/data-validation`     | ORPHAN         | pb3:demo-dart | `promote` | High       | Wire via lifecycle nav |
| `/services/promote/model-assessment`    | ORPHAN         | pb3:demo-dart | `promote` | High       |                        |
| `/services/promote/risk-stress`         | ORPHAN         | pb3:demo-dart | `promote` | High       |                        |
| `/services/promote/execution-readiness` | ORPHAN         | pb3:demo-dart | `promote` | High       |                        |
| `/services/promote/paper-trading`       | ORPHAN         | pb3:demo-dart | `promote` | High       |                        |
| `/services/promote/champion`            | ORPHAN         | pb3:demo-dart | `promote` | High       |                        |
| `/services/promote/capital-allocation`  | ORPHAN         | pb3:demo-dart | `promote` | High       |                        |
| `/services/promote/governance`          | ORPHAN         | pb3:demo-dart | `promote` | High       |                        |

---

## (platform)/services/reports — 12 routes → client-reporting (shared pb3a/pb3b)

Per [../cross-cutting/client-reporting.md](../playbook-concepts/client-reporting.md), all 12 are the SHARED reporting
surface for IM + Reg Umbrella demos and real clients.

| route                               | classification | reuse_hint             | action    | confidence | notes           |
| ----------------------------------- | -------------- | ---------------------- | --------- | ---------- | --------------- |
| `/services/reports/overview`        | HUB            | cross:client-reporting | `promote` | High       |                 |
| `/services/reports/performance`     | ORPHAN         | cross:client-reporting | `promote` | High       | Tab via sub-nav |
| `/services/reports/nav`             | ORPHAN         | cross:client-reporting | `promote` | High       |                 |
| `/services/reports/invoices`        | ORPHAN         | cross:client-reporting | `promote` | High       |                 |
| `/services/reports/ibor`            | ORPHAN         | cross:client-reporting | `promote` | High       |                 |
| `/services/reports/settlement`      | ORPHAN         | cross:client-reporting | `promote` | High       |                 |
| `/services/reports/reconciliation`  | ORPHAN         | cross:client-reporting | `promote` | High       |                 |
| `/services/reports/regulatory`      | ORPHAN         | cross:client-reporting | `promote` | High       |                 |
| `/services/reports/analytics`       | ORPHAN         | cross:client-reporting | `promote` | High       |                 |
| `/services/reports/trades`          | ORPHAN         | cross:client-reporting | `promote` | High       |                 |
| `/services/reports/executive`       | HUB            | cross:client-reporting | `promote` | High       |                 |
| `/services/reports/fund-operations` | ORPHAN         | cross:client-reporting | `promote` | High       |                 |

---

## (platform)/services/manage — 7 routes (internal)

| route                             | classification | reuse_hint    | action                    | confidence | notes                    |
| --------------------------------- | -------------- | ------------- | ------------------------- | ---------- | ------------------------ |
| `/services/manage/clients`        | HUB            | pb3:admin-org | `promote`                 | High       | Client management        |
| `/services/manage/compliance`     | HUB            | ops:internal  | `promote`                 | High       |                          |
| `/services/manage/best-execution` | ORPHAN         | ops:internal  | `promote`                 | Medium     |                          |
| `/services/manage/fees`           | ORPHAN         | ops:internal  | `promote`                 | Medium     |                          |
| `/services/manage/mandates`       | ORPHAN         | ops:internal  | `promote`                 | Medium     |                          |
| `/services/manage/users`          | ORPHAN         | pb3:admin-org | `merge-into:/admin/users` | Medium     | Duplicate of admin/users |
| `/services/manage/users/request`  | ORPHAN         | pb3:admin-org | `defer`                   | Low        | User request flow        |

---

## (platform)/investor-relations — 8 routes

| route                                         | classification | reuse_hint               | action                           | confidence | notes                      |
| --------------------------------------------- | -------------- | ------------------------ | -------------------------------- | ---------- | -------------------------- |
| `/investor-relations`                         | HUB            | cross:ir                 | `promote`                        | High       |                            |
| `/investor-relations/board-presentation`      | ORPHAN         | cross:ir                 | `promote`                        | High       |                            |
| `/investor-relations/plan-presentation`       | ORPHAN         | cross:ir                 | `promote`                        | High       |                            |
| `/investor-relations/investment-presentation` | ORPHAN         | pb2:im-deep + cross:ir   | `partial-archive`                | High       | Extract into pb2a briefing |
| `/investor-relations/platform-presentation`   | ORPHAN         | pb2:dart-deep + cross:ir | `partial-archive`                | High       | Extract into pb2b briefing |
| `/investor-relations/regulatory-presentation` | ORPHAN         | pb2:reg-deep + cross:ir  | `partial-archive`                | High       | Extract into pb2c briefing |
| `/investor-relations/disaster-recovery`       | ORPHAN         | pb2:reg-deep             | `partial-archive`                | Medium     | BCP relevant for umbrella  |
| `/investor-relations/site-navigation`         | ORPHAN         | cross:ir                 | `merge-into:/investor-relations` | High       | Redundant with landing     |

---

## (platform) misc — 4 routes

| route                     | classification | reuse_hint    | action    | confidence | notes                    |
| ------------------------- | -------------- | ------------- | --------- | ---------- | ------------------------ |
| `/dashboard`              | HUB            | pb3:\*        | `promote` | High       | Services portal landing  |
| `/onboarding`             | ORPHAN         | pb3:demo-\*   | `defer`   | Low        | Wizard flow; unclear fit |
| `/settings/api-keys`      | ORPHAN         | pb3:demo-dart | `promote` | Medium     | Per-user API keys        |
| `/settings/notifications` | ORPHAN         | pb3:demo-dart | `promote` | Medium     |                          |

---

## (ops) — 26 routes (Odum-internal)

| route                        | classification | reuse_hint   | action    | confidence | notes                   |
| ---------------------------- | -------------- | ------------ | --------- | ---------- | ----------------------- |
| `/admin`                     | HUB            | ops:internal | `promote` | High       | Admin landing           |
| `/admin/users`               | HUB            | ops:internal | `promote` | High       |                         |
| `/admin/users/[id]`          | DYNAMIC        | ops:internal | `promote` | High       |                         |
| `/admin/users/[id]/modify`   | DYNAMIC        | ops:internal | `promote` | High       |                         |
| `/admin/users/[id]/offboard` | DYNAMIC        | ops:internal | `promote` | High       |                         |
| `/admin/users/catalogue`     | LINKED         | ops:internal | `promote` | High       |                         |
| `/admin/users/firebase`      | LINKED         | ops:internal | `promote` | High       | Firebase-specific admin |
| `/admin/users/health-checks` | LINKED         | ops:internal | `promote` | High       |                         |
| `/admin/users/onboard`       | LINKED         | ops:internal | `promote` | High       |                         |
| `/admin/users/requests`      | LINKED         | ops:internal | `promote` | High       |                         |
| `/admin/users/templates`     | LINKED         | ops:internal | `promote` | High       | Access templates        |
| `/admin/organizations/[id]`  | DYNAMIC        | ops:internal | `promote` | High       | Org detail              |
| `/admin/data`                | LINKED         | ops:internal | `promote` | High       |                         |
| `/approvals`                 | LINKED         | ops:internal | `promote` | High       | Approval workflow       |
| `/config`                    | LINKED         | ops:internal | `promote` | High       |                         |
| `/devops`                    | LINKED         | ops:internal | `promote` | High       |                         |
| `/devops/schemas`            | ORPHAN         | ops:internal | `defer`   | Low        |                         |
| `/devops/topology`           | ORPHAN         | ops:internal | `defer`   | Low        |                         |
| `/engagement`                | ORPHAN         | ops:internal | `defer`   | Low        |                         |
| `/internal`                  | ORPHAN         | ops:internal | `defer`   | Low        |                         |
| `/internal/data-etl`         | ORPHAN         | ops:internal | `defer`   | Low        |                         |
| `/ops`                       | ORPHAN         | ops:internal | `defer`   | Low        |                         |
| `/ops/jobs`                  | LINKED         | ops:internal | `promote` | High       |                         |
| `/ops/services`              | HUB            | ops:internal | `promote` | High       |                         |

---

## user-management-ui — 19 routes

Per user directive, **keep separate** from unified-trading-system-ui. Do not merge.

All 19 routes are `ops:internal` / `pb3:admin-org`. All are `promote` within the user-management-ui surface. See
[user-management-ui](user-management-ui) repo.

---

## Action totals

| Action                              | Count (approx)                |
| ----------------------------------- | ----------------------------- |
| promote                             | ~120                          |
| refactor                            | ~12                           |
| merge-into                          | ~25                           |
| partial-archive                     | ~4 (IR presentations)         |
| defer                               | ~14                           |
| deprecate                           | 0 (none yet)                  |
| broken-link-target → build-or-prune | 1 (`/services/execution/tca`) |

**Deprecate count is intentionally zero.** No page is being flagged for deletion in this pass. That's a follow-up
decision per the user: deletion is the big decision, defer rather than deprecate when in doubt.

## Related

- Broken links: [broken-links.md](broken-links.md)
- Duplicate clusters: [duplicate-clusters.md](duplicate-clusters.md)
- Partial archive details: [partial-archive.md](partial-archive.md)
- Roadmap for follow-up plans: [../roadmap/next-waves.md](../roadmap/next-waves.md)
