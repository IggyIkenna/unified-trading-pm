---
doc_type: codex-ssot
title: Execution Algo Catalogue
summary:
  Execution Algo Catalogue playbook-concept — SSOT in execution-service algo_library (VWAP/TWAP/POV/Adaptive) +
  matching_engine; 7 orphan /services/execution/* pages, UAC capability exposure audit pending, /services/execution/tca
  broken; lists the parity gaps to build.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin, sales]
tags: [catalogue, execution, ui, uac, page-triage, audit]
related:
  [
    /codex/14-customer-journeys/playbook-concepts/catalogues.md,
    ../page-triage/broken-links.md,
    /codex/14-customer-journeys/playbook-concepts/visibility-slicing.md,
  ]
created: 2026-04-19
authoritative_for: [execution-algo catalogue UI-surface parity gap]
referenced_by:
  [
    /codex/14-customer-journeys/playbook-concepts/README.md,
    /codex/14-customer-journeys/playbook-concepts/catalogues.md,
    /codex/14-customer-journeys/playbooks/02b-research-dart.md,
    /codex/14-customer-journeys/playbooks/03c-demo-dart.md,
    /codex/14-customer-journeys/roadmap/plan-references.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Execution Algo Catalogue

One of the four catalogues. See [catalogues.md](catalogues.md) for the umbrella pattern.

## Status: ⚠ SSOT exists in execution-service; UI surface fragmented

## Service SSOT

- [execution-service/algo_library/](https://) — execution algorithm library (VWAP, TWAP, POV, Adaptive, etc.)
- [execution-service/matching_engine/](https://) — historical matching engine for execution-alpha simulation

## UAC registry

**Audit needed** — verify execution-service algos are exposed as UAC capability declarations + per-venue applicability.
Likely partial; flag gaps.

## UI route (today)

7 pages under `/services/execution/`:

- `overview`, `algos`, `benchmarks`, `candidates`, `handoff`, `venues`, `[executionId]` (dynamic detail), `tca` (BROKEN
  — referenced but no page.tsx)

All 7 are orphans per static audit — tab-only access. No inbound links from dashboard, trading, or observe.

## Gap vs canonical pattern

| Parity feature        | Strategy Catalogue |                  Execution Algo Catalogue                  |
| --------------------- | :----------------: | :--------------------------------------------------------: |
| Overview page         |         ✅         |             ✅ `/services/execution/overview`              |
| Coverage matrix       |         ✅         | — (needs: algo × venue × asset class × order-type support) |
| By-combination filter |         ✅         |                             —                              |
| Per-entry detail      |         ✅         |     ✅ `/[executionId]` dynamic (check what it shows)      |
| Admin lock-state      |         ✅         |                             —                              |
| Blocked               |         ✅         |                             —                              |

## What to build for parity

1. **Unify as `/services/execution-catalogue/` OR leave under `/services/execution/` but enhance to catalogue surface**
2. **Decision point**: does execution-algo-catalogue live under DART service family or under Trading? Currently both
   routes touch it. Resolve in [../playbooks/02b-research-dart.md](../playbooks/02b-research-dart.md).
3. **Coverage matrix**: algo × venue × asset_group × order_type (limit / market / iceberg / TWAP / etc.)
4. **Per-algo detail**: algo spec, benchmarks it supports, TCA reports, venue applicability
5. **Fix the `/services/execution/tca` broken link** — either build the page or prune the reference

Tracked in [../roadmap/next-waves.md](../roadmap/next-waves.md).

## Relationship to other catalogues

- Execution Algo Catalogue is CONSUMED by Strategy Catalogue — every strategy has a chosen execution algo per venue
- Feeds INTO Trading service (the terminal uses these algos)
- TCA (transaction cost analysis) reports go to Reports service (`/services/reports/trades`)

## Cross-playbook surface

- **pb2b (DART briefing)** — mentioned as one of four catalogues
- **pb3c (DART demo)** — demo user sees algo catalogue
- **pb3a/b (IM / Reg)** — NOT surfaced (IM clients see execution quality via TCA but not algo-level detail)

## Related

- Umbrella: [catalogues.md](catalogues.md)
- Broken link: `/services/execution/tca` — tracked in [../page-triage/broken-links.md](../page-triage/broken-links.md)
- Visibility slicing: [visibility-slicing.md](visibility-slicing.md)
