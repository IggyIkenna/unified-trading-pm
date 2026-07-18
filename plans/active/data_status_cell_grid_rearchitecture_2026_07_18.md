---
doc_type: plan
title: Data-status manifest cell-grid re-architecture — bound / stream / precompute the full-history view
summary:
  Operator ruled 2026-07-18 to schedule the real fix for a data-status tab that is fast at FULL history. Today the tab's
  manifest cell-grid is built by reading the entire per-service manifest into memory (measured ~18GB IS / 81GB MTDS /
  56GB MDPS) — the root cause of the repeated deployment-api OOMs, currently held off only by a per-request OOM guard +
  a 90-day UI default. This plan replaces that stopgap with a bounded/streamed/precomputed cell-grid so the full history
  renders without loading the whole manifest per request.
status: active
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer]
tags: [data-status, deployment-api, cell-grid, oom, performance, precompute]
related:
  [
    deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md,
    data_status_page_ux_and_canonicalisation_2026_07_16.md,
  ]
created: 2026-07-18
last_updated: 2026-07-18
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: "deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md §4 (operator ruling 2026-07-18: SCHEDULE)"
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Data-status manifest cell-grid re-architecture

**Operator ruling (2026-07-18):** schedule the full re-architecture (previously deferred "not using the tab now"); the
near-term OOM guard + 90-day default stay in place until this lands.

## Context

The data-status tab renders a per-(service, asset_group, venue, data_type, day) coverage cell-grid. It is currently
built by reading the ENTIRE per-service availability manifest into memory per request — measured ~18GB (IS) / 81GB
(MTDS) / 56GB (MDPS). Under Cloud Run concurrency a cold full-history build OOM-kills the container (the repeated
deployment-api OOM incidents). The near-term mitigation is a per-request OOM guard + a 90-day UI default window; the
real fix is to never load the whole manifest per request.

## Design directions (to be chosen in the design task)

- **Bound** — the read is always windowed (never whole-corpus); the UI requests a window, the backend reads only it.
- **Stream** — build the grid via a streaming/aggregating pass rather than materialising the full manifest in memory.
- **Precompute** — an offline job (the hourly consolidator or a sibling) materialises a compact per-window cell-grid
  projection the API reads cheaply (the manifest stays the SSOT; this is a read cache/projection).

## Codex SSOTs (read before designing)

- `codex/05-infrastructure/deployment-observability.md` — deployment-api cache/observability architecture.
- `codex/02-data/availability-manifest-and-data-status.md` — manifest atom + single-walk discipline (no new whole-corpus
  walk is review-blocking — the precompute job must respect this).
- `codex/02-data/honest-coverage-model.md` — the two-layer / two-view coverage model the grid renders.
- `codex/05-infrastructure/manifest-consolidator-ssot.md` — the consolidator (candidate host for a precompute step).

## Todos

- [ ] [BACKEND] P1. **Measure + profile** — instrument the current cell-grid build to confirm the per-service memory
      footprint + the exact read pattern (which manifest columns/partitions a full-history request touches). Baseline
      the numbers this plan must beat.
- [ ] [BACKEND] P1. **Design doc — bound vs stream vs precompute** — evaluate the three directions against the
      single-walk discipline (no new whole-corpus walk), Cloud Run memory, and UI latency; pick one (or a hybrid) and
      record the decision + the projection schema. This is the design gate.
- [ ] [BACKEND] P1. **Implement the bounded read** — the API cell-grid endpoint reads ONLY the requested window from the
      manifest (or the precomputed projection), never the whole corpus; column-pruned + TTL-cached.
- [ ] [BACKEND] P2. **Precompute projection (if chosen)** — an offline job materialises the per-window cell-grid
      projection (respecting single-walk); the API reads it; manifest stays SSOT + fallback.
- [ ] [UI] P2. **Lift the 90-day default** — once the backend is bounded/precomputed, allow full-history windows in the
      UI without the OOM-guard stopgap; add a pw:L2 regression spec for a full-history render.
- [ ] [BACKEND] P2. **Load-test at full history** — prove a full-history cell-grid request stays within Cloud Run memory
      at production concurrency (cite memory p99 + latency); retire the per-request OOM guard.
- [ ] [REVIEW] P2. **Post-phase codex audit** — update `deployment-observability.md` with the new cell-grid
      architecture; confirm no plan↔codex drift.

## Progress Log

- **2026-07-18** — Authored after the operator moved the cell-grid re-architecture from deferred to scheduled. Human
  plan (operator-driven). The near-term OOM guard + 90-day default remain the live mitigation until this lands.
