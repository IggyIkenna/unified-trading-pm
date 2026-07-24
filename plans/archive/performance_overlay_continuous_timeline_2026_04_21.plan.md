---
doc_type: plan
title: ────────────────────────────────────────────────────────────────────────────
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-api, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-21"
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

---

name: performance-overlay-continuous-timeline-2026-04-21 overview: Single shared `<PerformanceOverlay>` chart primitive
that renders per-instance continuous backtest → paper → live timelines from the `odum-paper` account's P&L series, with
overlay / stitched / per-view modes. Consumed by Strategy Catalogue (Plan B FOMO tearsheets), DART terminal, Reports (IM
allocator view), IM dashboards. type: ui epic: epic-code-completion status: active locked_by: live-defi-rollout
locked_since: 2026-04-21

completion_gates: code: C3 deployment: D0 business: none

repo_gates:

- repo: unified-trading-system-ui code: C0 deployment: D0 business: none
- repo: unified-trading-api code: C0 deployment: D0 business: none
- repo: unified-trading-pm code: C0 deployment: none business: none

depends_on:

- strategy_lifecycle_maturity_model_2026_04_21

# ────────────────────────────────────────────────────────────────────────────

# CONTEXT

# ────────────────────────────────────────────────────────────────────────────

#

# The USP of the IM/DART allocator experience is the ability to see a single

# strategy instance's performance as a continuous function across backtest →

# paper → live, with the ability to overlay all three for alpha-decay / slippage

# diagnosis.

#

# Source of all three series: the `odum-paper` client-zero account (Plan A).

# - Backtest: ran historically, persisted as P&L series keyed on (instance_id)

# - Paper: `odum-paper` account's live-running paper fills (ongoing)

# - Live: `odum-live` twin account's real fills (for instances that graduated)

#

# Three render modes on the same primitive:

# - "overlay" — all three series on the same X axis, colour-coded, so

# users see drift between backtest/paper/live

# - "stitched" — backtest until paper starts; paper until live starts;

# live from then onwards. Single continuous line. Markers

# where each transition happened.

# - "split" — three sub-charts stacked; same X axis, independent Y.

#

# Allocator queries the UI must support (via filter props):

# - Live vs paper on same window, same instance

# - Live vs backtest on same window

# - Trend when strategy graduated from backtest-only → live (was there alpha

# decay as capital scaled?)

# - Per-venue slice (for venue-set-variant instances — see alpha per venue)

#

# ────────────────────────────────────────────────────────────────────────────

todos:

# ──────────────────────────────────────────────────────────────────────

# PHASE 1 — API endpoint (SEQUENTIAL, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p1-performance-series-api content: |
  - [x] [AGENT] P0. `unified-trading-api`
        `GET /api/v1/strategy-instances/{instance_id}/performance?views=backtest,paper,live&from=&to=&per_venue=bool`.
        Returns
        `{series: {backtest?, paper?, live?}, transition_markers: {paper_started_at, live_started_at},     phase_annotations: PhaseTransition[]}`.
        Shipped as `unified_trading_api.routes.strategy_performance` with deterministic mock series (13 unit tests
        green). Real odum-paper/odum-live PBM wiring pending — see `p1-pbm-wiring-followup`. status: done

- id: p1-api-cache-strategy content: |
  - [x] [AGENT] P0. In-process TTL cache shipped: 60s for paper/live, 3600s for backtest. `per_venue=true` expands to
        `series.{view}.per_venue.{venue}` per §4 of performance-overlay.md. `reset_cache_for_tests()` hook exposed.
        status: done

- id: p1-pbm-wiring-followup content: |
  - [x] [AGENT] P1. Replace deterministic mock series in `strategy_performance.py` with a real query against
        position-balance-monitor-service P&L streams keyed on `(odum-paper | odum-live, instance_id, regime)`. Gate on
        `reporting` entitlement OR `(org, instance_id)` subscription. _(archived 2026-04-22 — mock remains; wire PBMS
        query in a future active plan.)_ status: deferred

# ──────────────────────────────────────────────────────────────────────

# PHASE 2 — Shared chart primitive (SEQUENTIAL after Phase 1, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p2-performance-overlay-component content: |
  - [x] [AGENT] P0. `components/strategy-catalogue/PerformanceOverlay.tsx` + `PerformanceOverlayView` pure renderer (for
        SSR + test use). Overlay / stitched / split modes via recharts `ComposedChart`. Palette matches codex
        (backtest=#8AA4C7, paper=#E0A84A, live=#27AE60). Phase markers rendered as dashed `<ReferenceLine>` verticals
        with paper/live labels. Missing-view fallback = toggle disabled + tooltip. status: done

- id: p2-performance-stats-sidecar content: |
  - [x] [AGENT] P0. `<PerformanceOverlayStats>` sidecar — Sharpe (annualised), MDD, CAGR, win-rate, avg trade notional
        per view. Residual row appears automatically when exactly two views are selected (paper−live / backtest−live).
        status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 3 — Consumer wiring (SEQUENTIAL after Phase 2, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p3-wire-fomo-tearsheet content: |
  - [x] [AGENT] P0. `<FomoTearsheetCard>` (+ `<RealityPositionCard>`) now render
        `<PerformanceOverlay mode="stitched" views=["backtest","paper","live"]>` with no sidecar (compact tearsheet tile
        shape). `PerformanceOverlayPlaceholder.tsx` deleted — no re-export shim. status: done

- id: p3-wire-dart-terminal content: |
  - [x] [AGENT] P0. DART terminal strategy-detail page (`app/(platform)/services/trading/strategies/[id]`) gets a
        `Performance` tab next to the P&L tab. `<PerformanceOverlay mode="overlay">` with all 3 views toggleable + stats
        sidecar + phase markers. status: done

- id: p3-wire-reports-im-allocator content: |
  - [x] [AGENT] P1. Reports → P&L Attribution gains an "Allocator View" tab
        (`components/reports/allocator-strategy-overlay.tsx`) with a strategy-instance picker and
        `<PerformanceOverlay mode="split" perVenue>` for venue-level degradation diagnosis. status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 4 — Tests + QG + codex (PARALLEL, P1)

# ──────────────────────────────────────────────────────────────────────

- id: p4-overlay-tests content: |
  - [x] [AGENT] P1. `tests/unit/components/strategy-catalogue/performance-overlay.test.tsx` — 8 tests cover overlay /
        stitched / split modes, missing-view fallback (disables toggle), stats sidecar rows, residual on 2-view
        selection, empty-state fallback, per_venue rendering. Plus 13 UTA backend tests in
        `tests/unit/routes/test_strategy_performance.py`. status: done

- id: p4-codex-performance-overlay-doc content: |
  - [x] [AGENT] P1. Create `/codex/09-strategy/architecture-v2/performance-overlay.md`: 3 modes, allocator query
        patterns, odum-paper source, venue-slice semantics. Cross-ref odum-paper-client-zero.md + strategy-catalogue-
        3tier.md. status: done

- id: p4-qg-final content: |
  - [x] [SCRIPT] P0. `npx tsc --noEmit` clean on Plan-C files (the 3 pre-existing unrelated TS errors in `admin/github`,
        `admin/questionnaires`, `functions/src/setCapabilityClaim.ts`, `lib/mocks/fixtures/defi-walkthrough.ts` are
        outside this plan's scope). `CI=true npm test -- --run` 1059/1060 green — single unrelated flake in
        `site-header-nav.test.tsx` (marketing-header href, separate agent's scope). `npm run orphan-audit -- --blocking`
        exits 0 (220/223 reachable, 0 orphans). UTA `pytest tests/unit/routes/test_strategy_performance.py` 13/13 green.
        status: done

# ────────────────────────────────────────────────────────────────────────────

# SUCCESS CRITERIA

# ────────────────────────────────────────────────────────────────────────────

# - /api/v1/strategy-instances/{id}/performance returns 3-view series with

# transition markers

# - <PerformanceOverlay> renders overlay/stitched/split modes with per-venue

# expansion

# - Wired into FOMO tearsheets, DART terminal, Reports Allocator View

# - Codex doc shipped + cross-linked

# ────────────────────────────────────────────────────────────────────────────
