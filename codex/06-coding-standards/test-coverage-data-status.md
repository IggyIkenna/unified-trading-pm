---
scope: [engineer]
---

# Test coverage — data-status surface

## Purpose

The data-status surface (deployment-api routes + deployment-ui components + the underlying manifest reads) is the
operator's primary visibility into pipeline health. A test-coverage gap here means a regression ships silently and the
operator first hears about it from a missing data alert hours later. This doc names the test-coverage matrix that every
data-status change MUST satisfy before merging.

## Scope

- **Backend**: `deployment-api/deployment_api/routes/_data_status*.py` + dependents (manifest readers, leaf-stats,
  schema-modal, drilldown lookups, deploy-missing).
- **Frontend**: `deployment-ui/src/` data-status pages + components (DataStatusTab, drilldown panels, schema modal,
  TypedReasonBadges, FailurePillarStack, LeafSchemaModal, deploy-missing-preview).
- **Cross-cutting**: manifest schema (UAC), hive-vocab compatibility, per-asset_group shard atoms.

## The matrix — what MUST be tested per change

| Surface                            | Backend test                                              | Frontend test                                          | Integration                                                     |
| ---------------------------------- | --------------------------------------------------------- | ------------------------------------------------------ | --------------------------------------------------------------- |
| Drilldown to per-leaf depth        | unit: per-route returns full hierarchy per asset_group    | component: drilldown renders to leaf level per shard   | playwright: navigate from venue → instrument → day → schema     |
| Typed error_reason rendering       | unit: typed reason in `/api/data-status` response         | component: TypedReasonBadges renders all closed-set reasons | playwright: badge click opens schema-modal                      |
| Failure pillar stack               | unit: 4-pillar break-down per shard                       | component: FailurePillarStack renders pillars         | playwright: pillar click opens drilldown                        |
| Schema modal (per-leaf)            | unit: `/api/data-status/leaf-stats` returns row count + NaN ratio + available_at envelope | component: LeafSchemaModal renders missing-available_at as writegate violation | playwright: open modal, verify shape  |
| Deploy-Missing preview             | unit: `/data-status/deploy-missing-preview` per launcher  | component: preview surfaces LOCAL-ONLY warnings        | playwright: invoke preview, verify launcher route               |
| Hive-vocab compatibility           | unit: reader handles both `category=` and `asset_group=`  | n/a (backend transparent)                              | n/a (covered by reader)                                         |
| Manifest schema drift              | contract test: every column in UAC schema renders         | n/a                                                    | n/a                                                             |
| Honest-absence rendering (per asset_group) | unit: empty_confirmed vs attempted_failed vs expected_unattempted distinguished in API response | component: each state renders distinctly | playwright: per asset_group sample shows correct semantics      |
| Per-(service, asset_group, venue, data_type) drilldown depth | unit: matches `deployment-ui-drilldown-depth-audit.md` | component: matches the audit table   | playwright: smoke-test every WORKING entry remains WORKING      |

## Audit + ratchet

The `deployment-ui-drilldown-depth-audit.md` ratchet rule applies here:

1. Every (service, asset_group, venue, data_type) row in the audit is tested in the playwright matrix.
2. New rows added to the audit (e.g. a new venue) get matrix entries before the data-status surface ships.
3. Any flip from WORKING → STOPS_AT_INTERMEDIATE_LEVEL_<level> in the audit is a failing test — the regression is caught
   before merge.

## Why this is a separate codex doc

The data-status surface is one of the most-touched-by-parallel-agents surfaces in the workspace (deployment-api +
deployment-ui change weekly). A central test-coverage SSOT prevents the "it works on my machine; backend was right but
frontend regressed silently" failure mode.

## Cross-references

- Drilldown depth audit:
  [`../02-data/deployment-ui-drilldown-depth-audit.md`](../02-data/deployment-ui-drilldown-depth-audit.md)
- Drilldown SSOT (per-shard + hierarchical): [`../02-data/data-status-drilldown.md`](../02-data/data-status-drilldown.md)
- Manifest schema:
  [`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md)
- Honest-absence rendering: [`../02-data/honest-absence-downstream-handling.md`](../02-data/honest-absence-downstream-handling.md)
- Quality gates (which suite runs the matrix): [`quality-gates.md`](quality-gates.md)
- Integration testing layers: [`integration-testing-layers.md`](integration-testing-layers.md)
- UI testing layers: [`ui-testing-layers.md`](ui-testing-layers.md)
