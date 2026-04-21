---
name: performance-overlay-continuous-timeline-2026-04-21
overview:
  Single shared `<PerformanceOverlay>` chart primitive that renders per-instance continuous backtest → paper →
  live timelines from the `odum-paper` account's P&L series, with overlay / stitched / per-view modes.
  Consumed by Strategy Catalogue (Plan B FOMO tearsheets), DART terminal, Reports (IM allocator view), IM dashboards.
type: ui
epic: epic-code-completion
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-21

completion_gates:
  code: C3
  deployment: D0
  business: none

repo_gates:
  - repo: unified-trading-system-ui
    code: C0
    deployment: D0
    business: none
  - repo: unified-trading-api
    code: C0
    deployment: D0
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

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
#   - Backtest: ran historically, persisted as P&L series keyed on (instance_id)
#   - Paper: `odum-paper` account's live-running paper fills (ongoing)
#   - Live: `odum-live` twin account's real fills (for instances that graduated)
#
# Three render modes on the same primitive:
#   - "overlay"   — all three series on the same X axis, colour-coded, so
#                   users see drift between backtest/paper/live
#   - "stitched"  — backtest until paper starts; paper until live starts;
#                   live from then onwards. Single continuous line. Markers
#                   where each transition happened.
#   - "split"     — three sub-charts stacked; same X axis, independent Y.
#
# Allocator queries the UI must support (via filter props):
#   - Live vs paper on same window, same instance
#   - Live vs backtest on same window
#   - Trend when strategy graduated from backtest-only → live (was there alpha
#     decay as capital scaled?)
#   - Per-venue slice (for venue-set-variant instances — see alpha per venue)
#
# ────────────────────────────────────────────────────────────────────────────

todos:
  # ──────────────────────────────────────────────────────────────────────
  # PHASE 1 — API endpoint (SEQUENTIAL, P0)
  # ──────────────────────────────────────────────────────────────────────
  - id: p1-performance-series-api
    content: |
      - [ ] [AGENT] P0. `unified-trading-api`
        `GET /api/v1/strategy-instances/{instance_id}/performance?views=backtest,paper,live&from=&to=&per_venue=bool`.
        Returns `{series: {backtest?, paper?, live?}, transition_markers: {paper_started_at, live_started_at},
        phase_annotations: PhaseTransition[]}`. Pulls from odum-paper/live account P&L streams via
        position-balance-monitor-service. Permissioned by `reporting` entitlement (FOMO) OR the instance's
        subscription (Reality).
    status: pending

  - id: p1-api-cache-strategy
    content: |
      - [ ] [AGENT] P0. Series cached with 60s TTL for paper/live (fast-moving)
        and 1-hour TTL for backtest (historical, mutates only on re-run).
        Per-venue slices computed on-demand; if `per_venue=true`, response
        expands to `series: {backtest: {aggregate, per_venue: {[venue]: series}}, ...}`.
    status: pending

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 2 — Shared chart primitive (SEQUENTIAL after Phase 1, P0)
  # ──────────────────────────────────────────────────────────────────────
  - id: p2-performance-overlay-component
    content: |
      - [ ] [AGENT] P0. `components/strategy-catalogue/PerformanceOverlay.tsx`:
        Props: `{ instance_id, mode: "overlay"|"stitched"|"split", views:
        ("backtest"|"paper"|"live")[], range?, per_venue?: boolean,
        showPhaseMarkers?: boolean }`. Uses existing chart library. Respects
        tearsheet-style aesthetic (monospace ticks, tabular-nums, thin grid).
        Colour palette: backtest=muted-blue, paper=amber, live=emerald.
        Transition markers rendered as dashed verticals with phase-badge labels.
    status: pending

  - id: p2-performance-stats-sidecar
    content: |
      - [ ] [AGENT] P0. `<PerformanceOverlayStats>` sidecar component —
        computes Sharpe, MDD, CAGR, win-rate, avg-trade-size per view; renders
        as a compact table. Drives the FOMO tearsheet header.
    status: pending

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 3 — Consumer wiring (SEQUENTIAL after Phase 2, P0)
  # ──────────────────────────────────────────────────────────────────────
  - id: p3-wire-fomo-tearsheet
    content: |
      - [ ] [AGENT] P0. Wire `<PerformanceOverlay mode="stitched" views=["backtest","paper","live"]>` +
        `<PerformanceOverlayStats>` into the `<FomoTearsheetCard>` (Plan B Phase 3).
    status: pending

  - id: p3-wire-dart-terminal
    content: |
      - [ ] [AGENT] P0. Add a "Performance" tab to the DART terminal strategy-
        detail panel — `<PerformanceOverlay mode="overlay">` with all three
        views toggleable. Positioned next to existing P&L + positions tabs.
    status: pending

  - id: p3-wire-reports-im-allocator
    content: |
      - [ ] [AGENT] P1. Reports → P&L Attribution gets a new "Allocator View"
        sub-section per strategy, showing the 3-way overlay with
        `per_venue=true` so IM allocators can see venue-level degradation.
    status: pending

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 4 — Tests + QG + codex (PARALLEL, P1)
  # ──────────────────────────────────────────────────────────────────────
  - id: p4-overlay-tests
    content: |
      - [ ] [AGENT] P1. `__tests__/performance-overlay.test.tsx`:
        per-mode render, missing-view fallbacks (e.g. instance only has
        backtest → stitched mode just shows backtest), per-venue expansion,
        transition-marker rendering.
    status: pending

  - id: p4-codex-performance-overlay-doc
    content: |
      - [ ] [AGENT] P1. Create `codex/09-strategy/architecture-v2/performance-overlay.md`:
        3 modes, allocator query patterns, odum-paper source, venue-slice
        semantics. Cross-ref odum-paper-client-zero.md + strategy-catalogue-
        3tier.md.
    status: pending

  - id: p4-qg-final
    content: |
      - [ ] [SCRIPT] P0. UI typecheck + full test suite + unified-trading-api QG all green.
    status: pending

# ────────────────────────────────────────────────────────────────────────────
# SUCCESS CRITERIA
# ────────────────────────────────────────────────────────────────────────────
# - /api/v1/strategy-instances/{id}/performance returns 3-view series with
#   transition markers
# - <PerformanceOverlay> renders overlay/stitched/split modes with per-venue
#   expansion
# - Wired into FOMO tearsheets, DART terminal, Reports Allocator View
# - Codex doc shipped + cross-linked
# ────────────────────────────────────────────────────────────────────────────
