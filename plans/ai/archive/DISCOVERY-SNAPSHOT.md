# Phase 2 Discovery Snapshot

**Post Phase 1 junk removal — working map of what remains and gaps.**

## What Was Cleaned (Phase 1)

Workspace root: 0 `.md` files at root (no stray docs). Codex root: only GLOSSARY.md + README.md remain.

## Workspace Root

- **41 items** (repos + config files)
- **0** `.md` files at root
- Includes: `pyrightconfig.json`, `*.code-workspace`, temp Excel lock file (`~$Copy of...`)

## Codex Root Remaining

- `GLOSSARY.md`
- `README.md`

## 10-Audit Coverage

| Area | Count | Notes |
|------|-------|-------|
| batch/ | 31 entries | Includes meta (_cross-service-concerns, corporate-actions, cross-service), exchange-interface-library, unified-trading-deployment-v3 |
| live/ | 18 entries | Missing: alerting-system, execution-analytics-ui, batch-audit-ui, client-reporting-ui, live-health-monitor-ui, logs-dashboard-ui, ml-training-ui, settlement-ui, strategy-onboarding-ui, trading-analytics-ui |

## Deployment-v2 References to Fix

**In .cursor/:** CURSOR_TEAM_KIT_COMPLETE_INTEGRATION.md, EXECUTION_COMPLETE.md, tasks/*.md, AWS_MIGRATION_STATUS.md, archive/codex-10-audit/*.md

**In codex/:** 07-security/README.md, 10-audit/README.md, 10-audit/ssot-reference-mapping.md, 06-coding-standards/*.md (quality-gates, sub-agent-workflow, dependency-management, formatting, testing-guides)

*Note: deployment-v2 superseded by v3 per WORKSPACE-MANIFEST.removedEntries*

## Services Missing from 10-Audit/batch/

**Manifest repos without batch audit entry:** api-contracts, unified-config-interface, unified-events-interface, unified-domain-client, execution-algo-library, unified-feature-calculator-library, unified-market-interface, unified-ml-interface, unified-trade-execution-interface, unified-defi-execution-interface, matching-engine-library, onboarding-ui

**Audit has but manifest removed:** corporate-actions, unified-trading-deployment-v3. **Audit has strategy-onboarding-ui** — manifest has onboarding-ui (possible rename).

## cursor_instrunctions.md

**EXISTS** at `instruments-service/cursor_instrunctions.md` — typo (should be `cursor_instructions`).

## 01-Domain Per-Service Coverage

| Mode | Count |
|------|-------|
| batch/per-service/ | 30 |
| live/per-service/ | 3 (execution-service, instruments-service, strategy-service) |

**Gap:** Live has 3; batch has 30. Live per-service docs sparse.

## Deployment-v3 Checklist Coverage

18 entries: corporate-actions, execution-service, features-*-service (4), instruments-service, market-*, ml-*, pnl-attribution, position-balance-monitor, risk-and-exposure, strategy-service, template, unified-trading-services, prerequisites, PRIORITY_SUMMARY

**Missing from checklist vs manifest:** Most libraries, api-contracts, UIs (execution-analytics-ui, batch-audit-ui, etc.), onboarding-ui, settlement-ui.

## Other Gaps

1. **Workspace temp file:** `~$Copy of Odum2025Unreconciled List.13Feb26.xlsx` — Excel lock; consider .gitignore.
2. **unified-trading-deployment-v3** not in workspace (superseded by v3) but still in 10-audit/batch.
3. **exchange-interface-library** in audit but not in WORKSPACE-MANIFEST.
