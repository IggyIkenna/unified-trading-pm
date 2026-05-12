---
scope: [engineer, admin]
---

# Deprecated UIs Notice

**Date:** 2026-02-21 (LIFTED 2026-05-12 — see banner below for current state)

> **STALENESS LIFT (2026-05-12)** — this doc tracks Round 1 of UI consolidation (3 UIs → `onboarding-ui`) but is
> two rounds behind. The 2026-05-08 consolidation collapsed `onboarding-ui` + 7 more split UIs (`strategy-ui`,
> `live-health-monitor-ui`, `batch-audit-ui`, `client-reporting-ui`, `execution-analytics-ui`, `logs-dashboard-ui`,
> `ml-training-ui`, `trading-analytics-ui`) into the consolidated portal `unified-trading-system-ui`. The active
> product UI surface is now **3 repos**: `unified-trading-system-ui` (consolidated portal) + `deployment-ui` +
> `user-management-ui`. Full current-state inventory: `codex/05-infrastructure/ui-functionality-requirements.md`
> § "Active UI surface". The body below documents Round 1 history; do NOT treat the 3-UI list below as current.

---

## Deprecated Services (ROUND 1 — 2026-02-21 history, retained for archival reference only)

The following UI services have been **deprecated** and consolidated into **onboarding-ui**:

### 1. strategy-onboarding-ui

**Status:** ❌ DEPRECATED  
**Consolidated Into:** `onboarding-ui` Tab 2 (Strategy Onboarding)  
**Reason:** Reduced UI proliferation, better integrated workflows

**Per-Service Docs:** Marked with deprecation notice in all 5 layers (01-domain through 05-infrastructure)

### 2. settlement-ui

**Status:** ⚠️ PARTIAL CONSOLIDATION  
**Setup Workflows Moved To:** `onboarding-ui`  
**Remains:** Analysis/reporting features (planned standalone)  
**Reason:** Separated setup (onboarding) from analysis (reporting)

**Per-Service Docs:** Marked with partial consolidation notice in all 5 layers

### 3. config-ui

**Status:** ❌ DEPRECATED  
**Consolidated Into:** `onboarding-ui` Tabs 1, 4, 5, 6  
**Already Documented:** See `07-services/per-service/config-ui.md`

---

## New Unified Service

**onboarding-ui** - Comprehensive onboarding UI with 6 tabs:

1. Client Onboarding
2. Strategy Onboarding
3. Venue/Exchange Onboarding (NEW)
4. API Key Management
5. Risk Configuration
6. Audit Log

**Epic:** `11-project-management/epics/onboarding-ui-epic.md`  
**Service Registry:** `11-project-management/service-registry.yaml`

---

## Documentation Updates Applied

- ✅ 10 per-service batch docs (01-domain through 05-infrastructure)
- ✅ Audit YAML files (comments added)
- ✅ Service registry (status fields updated)
- ✅ UI documentation summary (deprecation notes)

---

**See per-service docs for full deprecation notices.**
