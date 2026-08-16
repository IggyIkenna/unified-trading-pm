---
doc_type: issue
title:
  "codex/05-infrastructure/deployment-ui-architecture.md's tab-shell description (6 tabs + Monitor 4-sub-tab) is
  obsolete — deployment-ui's nav was substantially restructured since the doc's 2026-05-15 baseline; needs a full
  content rewrite, not just re-attestation"
summary: >-
  Found doing the freshness-gate content review for the 2026-08-16 `codex-freshness-sweep` failure (doc was 93d stale,
  last_reviewed=2026-05-15). The doc's core "six top-level tabs (Deploy / Monitor / Data Status / Builds / Readiness /
  Config) + Monitor's 4 lifecycle-class sub-tabs" model does not match the shipped deployment-ui nav. Confirmed against
  `deployment-ui/src/components/NavMenu.tsx` (`NAV_GROUPS`, current HEAD): the live app now has 7 nav groups / 15
  screens (Overview, Deploy & Deployments, Data, Cost & Artifacts, Repos & Alerts, Safety & Chaos, Research) with no
  top-level "Monitor" tab or lifecycle-class sub-tab grouping at all. Contributing changes per NavMenu.tsx's own
  changelog comments: live/batch/paper cockpit sub-tabs merged into one unified `/deployments` table (operator decision
  2026-07-08); the `?tab=` cockpit-pane query scheme retired site-wide for one-plain-route-per-screen (2026-07-17 nav
  audit); standalone `/vm-deployments` page retired (2026-07-21); Fleet tab removed (2026-07-27); `CloudBuildsTab`
  retired and folded into the `/artifacts` Pipeline tab (`ArtifactPipeline.tsx`). Partial good news: the doc's "four
  orthogonal axes" framing (lifecycle class / cloud target / env tier / service) is NOT entirely wrong — the
  cloud-target toggle (`CloudProviderContext.tsx`) and env-tier-by-hostname resolution both still exist unchanged in
  current `deployment-ui/src`; it's specifically the § "The six top-level tabs" + § "Monitor sub-tab structure"
  diagram/table sections (plus every cross-reference assuming that shell) that are obsolete. A stopgap 🟡 drift-notice
  banner was added to the doc same-turn (2026-08-16) citing this evidence and pointing readers at `NavMenu.tsx` as
  ground truth in the meantime, so `last_reviewed` could be honestly bumped without leaving readers misled — but the
  actual content (six-tab diagram, the tab/sub-tab tables, the "What's NEW vs reused" table's now-stale component
  names) still needs a real rewrite pass against the live NAV_GROUPS + page structure.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, deployment-ui, deployment-api]
scope: [engineer]
tags: [documentation, codex-drift, deployment-ui, nav, freshness-gate, ssot]
related:
  [
    /codex/05-infrastructure/deployment-ui-architecture.md,
    /codex/05-infrastructure/ui-architecture.md,
    /codex/03-deployment/data-status-ui-surface.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: docs_engineer
drift_direction: advance-docs
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found 2026-08-16 during the `/ci-reconcile` fix for the `codex-freshness-sweep` GHA failure flagging
  `deployment-ui-architecture.md` as 93d stale (last_reviewed=2026-05-15).
depends_on: []
context_scope:
  [
    deployment-ui/src/components/NavMenu.tsx,
    deployment-ui/src/App.tsx,
    deployment-ui/src/contexts/CloudProviderContext.tsx,
    deployment-ui/src/pages/Deployments.tsx,
    deployment-ui/src/pages/ArtifactPipeline.tsx,
    codex/05-infrastructure/deployment-ui-architecture.md,
  ]
---

# deployment-ui-architecture.md nav-shell content is obsolete vs shipped app — needs a rewrite pass

## What's still true

- The **repo pair + purpose** (deployment-ui + deployment-api as the workspace's deploy/monitor/observe SSOT surface)
  is accurate.
- The **cloud-target toggle** (`CloudProviderContext.tsx`, auth-always-available pattern, both clouds loaded at boot)
  is accurate and unchanged.
- **Env-tier-resolved-by-hostname** (no in-UI toggle) is accurate and unchanged.
- `codex/05-infrastructure/ui-architecture.md` still points to this doc as the deployment-ui specifics SSOT — no
  successor doc exists yet, so this is a rewrite-in-place, not a supersession.

## What's obsolete (verified against `deployment-ui/src/components/NavMenu.tsx` `NAV_GROUPS`, current HEAD)

| Doc claims                                                             | Live reality                                                                                                      |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| 6 top-level tabs: Deploy / Monitor / Data Status / Builds / Readiness / Config | 7 nav groups / 15 screens: Overview, Deploy & Deployments, Data, Cost & Artifacts, Repos & Alerts, Safety & Chaos, Research |
| Monitor tab has 4 lifecycle-class sub-tabs (Backfill / Experiments / Live / Scheduled) | No "Monitor" tab exists. Live/batch/paper cockpit sub-tabs merged into one unified `/deployments` table (2026-07-08) |
| `?tab=` cockpit-pane query param scheme                                | Retired site-wide 2026-07-17 nav audit — one plain route per screen |
| Standalone `/vm-deployments` list page                                 | Retired 2026-07-21 (`vm_deployments_venue_panels_orphaned_route_2026_07_21.md`) — folded into `/deployments` |
| Fleet tab                                                               | Removed 2026-07-27 (`deployment_ui_fleet_tab_removal_2026_07_27.md`) |
| `Builds` tab / `CloudBuildsTab` component                              | Retired; manual-trigger action ported into `/artifacts` Pipeline tab (`ArtifactPipeline.tsx`) |

## Follow-up

- [ ] [DOCS] P2. Rewrite `codex/05-infrastructure/deployment-ui-architecture.md`'s § "The six top-level tabs" +
      § "Monitor sub-tab structure" + the "What's NEW vs reused" table against the current
      `deployment-ui/src/components/NavMenu.tsx` `NAV_GROUPS` shape (Overview / Deploy & Deployments / Data / Cost &
      Artifacts / Repos & Alerts / Safety & Chaos / Research), the merged `/deployments` unified table, and the
      `/artifacts` Pipeline tab — cite current file paths + a fresh commit SHA per surface the way the existing
      "Phase 9 shipped patterns" section does. Remove the 2026-08-16 drift-notice banner once the rewrite lands.
- [ ] [DOCS] P3. Audit the doc's other cross-references (`data-status-ui-surface.md` stub,
      `deployment_ui_lifecycle_tabs_2026_05_08.md` plan-provenance links) for the same kind of drift while doing the
      rewrite — they were sourced from the same 2026-05-08/05-15 baseline.
