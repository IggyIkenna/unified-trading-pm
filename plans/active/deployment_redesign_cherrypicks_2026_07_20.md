---
doc_type: plan
title: Deployment data-status redesign cherry-picks (A–E) from Harsh's superseded branch
summary: >-
  Harsh's feat/data-status-redesign branch (deployment-ui + deployment-api, late May) is ~800–1090 commits behind LDR
  and superseded as a whole — do NOT merge it. A capability-by-capability comparison against current production found
  five self-contained items worth taking as targeted cherry-picks/reimplementations rather than a branch merge: (A)
  Needs-Attention triage panel [UI], (B) dark-theme-default fix [UI], (C) reason_summary/reason_category on drilldown
  tree nodes [API], (D) mock-mode /coverage-summary + drilldown fixes [API], (E) a flat primary×date capture_status
  matrix endpoint [API]. Everything else on the branch is already shipped equal-or-better in prod.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, deployment-api]
scope: [engineer]
tags: [deployment-ui, deployment-api, data-status, cherry-pick, redesign, ui]
related: [/plans/active/distinct_values_noncanonical_audit_2026_07_20.md]
created: "2026-07-20"
last_updated: "2026-07-20"
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  operator ask 2026-07-20 ("anything we can merge in from Harsh's deployment branch above what we already have" → "do
  all A–E")
---

# Deployment data-status redesign cherry-picks (A–E)

> **Context.** Two subagents compared Harsh's `feat/data-status-redesign` (deployment-ui 31 commits / deployment-api 8
> commits, `ComsicTrader <harshkantariya.work@gmail.com>`, late May) against current `origin/live-defi-rollout`.
> Verdict: the redesign as a whole is superseded — prod independently rebuilt every idea equal-or-better
> (HierarchicalShardDrilldown predates the branch; TypedReasonBadges ⊃ reasonCategory.ts; SmartDownloadButton; date
> presets; heatmap). Do NOT merge the branch. Five self-contained items survive as targeted picks. Operator
> (2026-07-20): "do all of them A–E."

## Todos

- [ ] [BACKEND] P0. C — deployment-api: surface `reason_category` + `reason_summary` on the hierarchical drilldown tree
      nodes. Data already exists (`error_reason` projected into the df); wire prod's OWN
      `compute_empty_reason_counts`/`compute_failure_pillar_counts` (`services/data_status/coverage_metrics.py`) into
      `DrilldownNode.to_dict()` (`services/data_status_hierarchical.py`). NOT Harsh's classifier. Unit-test. Ship+flip.
- [ ] [BACKEND] P1. D — deployment-api: mock-mode fixes. `/coverage-summary` returns all-zeros in mock because
      `_status_core.get_coverage_summary` (registered first, wins) has a zero mock while the rich mock lives in the
      unreachable `_deploy_turbo.get_data_coverage_summary`. Port the rich per-asset-group mock INTO the winning
      `_status_core` handler — do NOT reorder routes (the `__init__.py:91` import order is deliberate). Also synthesise
      a non-empty mock drilldown tree. Update the tests that lock in the zeros
      (`tests/unit/test_route_data_status_mock.py`). Ship+flip.
- [ ] [BACKEND] P1. E — deployment-api: add a flat `(primary × date)` capture_status matrix endpoint (heatmap-shaped)
      reimplemented against `services/manifest_source.read_manifest_index` predicate-pushdown reader + the current
      `services/data_status/` package layout — NOT Harsh's own index_cache/mock modules. Honest-absence + in-process TTL
      cache like the sibling endpoints. Unit-test. Ship+flip.
- [x] [UI] P1. ✅ B — deployment-ui: dark-theme default. **FIXED** — deployment-ui@2c4e950. Playwright-verified the real
      defect first (`emulateMedia({colorScheme:'light'})`): `--color-bg-primary` resolved to `#ffffff` on a light-OS
      context with ZERO opt-out (no `.theme-light` consumer, no toggle anywhere). Note the light palette is itself
      well-crafted — NOT visually "washed out" as the source commit claimed; the genuine bug is behavioural (OS
      preference silently overrides the app's dark-first identity, unrecoverable). Fix mirrors `1d99062`: light palette
      moved from `@media (prefers-color-scheme: light)` to a plain `.theme-light` opt-in (+ same pattern on the
      cost-breakdown resizer hover icon). Verified both directions post-fix. pw:L2 ✓
      `tests/smoke/theme-dark-default.spec.ts` (2 tests).
- [x] [UI] P2. ✅ A — deployment-ui: Needs Attention triage panel. **SHIPPED** — deployment-ui@615bddf. Derived purely
      from the ALREADY-fetched `/api/data-status/manifest`/`turbo` response
      (`capture_status_counts.     attempted_failed`, `dates_missing`, `dates_found_list`) — no new backend endpoint,
      stale `redesignData.ts` NOT ported. `src/lib/needs-attention.ts` (`deriveNeedsAttention`, ranks
      failures>gaps>stale, **per-kind** cap after a real starvation bug was caught in test: a flat global cap let a
      noisy gap bucket crowd out every stale item) + `src/components/NeedsAttention.tsx` wired above the Data Coverage
      card; row click filters + scrolls. Documented scope boundary: `venue_summary.expected_but_missing` not surfaced
      (name-only, would need fabricated severity). 12 Vitest cases + pw:L2 ✓ `tests/smoke/needs-attention-panel.spec.ts`
      (4 tests).

## Progress Log

### 2026-07-20 — plan created

- Analysis complete (two subagents, per-repo). A–E are the surviving cherry-picks; branch merge rejected as superseded.
- Ordered C→D→E (API, independent, low-risk) then B→A (UI, needs playwright). B is verify-then-maybe-fix.
