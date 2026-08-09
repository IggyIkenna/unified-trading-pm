---
doc_type: codex-ssot
title: "`<PerformanceOverlay>` — Continuous Backtest / Paper / Live Timeline"
summary:
  SSOT for the <PerformanceOverlay> component + GET /api/v1/strategy-instances/{id}/performance — continuous
  backtest/paper/live P&L timeline in overlay/stitched/split modes, four allocator query patterns, the canonical
  three-colour palette, and the guarantee that the live series is always odum-live (never a real client run).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, unified-trading-api, unified-trading-system-ui]
scope: [engineer]
tags: [strategy, ui, performance, reconciliation, monitoring]
related:
  [
    /codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md,
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
    /codex/09-strategy/architecture-v2/dashboard-services-grid.md,
  ]
created: 2026-04-21
authoritative_for: [PerformanceOverlay backtest/paper/live timeline component + performance API]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/dart-exclusive-research-fork.md,
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
    /codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md,
    /codex/14-customer-journeys/shared-core/odum-paper-client-zero.md,
    /codex/14-customer-journeys/shared-core/strategy-version-governance.md,
  ]
owner:
last_reviewed:
code_refs:
---

# `<PerformanceOverlay>` — Continuous Backtest / Paper / Live Timeline

> **Status:** canonical (2026-04-21) **Owner:** Strategy Architecture v2 + UI **SSOT for:**
> `unified-trading-system-ui/components/strategy-catalogue/PerformanceOverlay.tsx`,
> `unified-trading-system-ui/components/strategy-catalogue/PerformanceOverlayStats.tsx`, `unified-trading-api` endpoint
> `GET /api/v1/strategy-instances/{id}/performance`. **Plan:**
> [`plans/archive/performance_overlay_continuous_timeline_2026_04_21.plan.md`](../../../plans/archive/performance_overlay_continuous_timeline_2026_04_21.plan.md)
> **Depends on:** [`strategy-lifecycle-maturity.md`](./strategy-lifecycle-maturity.md) ·
> [`../../14-customer-journeys/shared-core/odum-paper-client-zero.md`](../../14-customer-journeys/shared-core/odum-paper-client-zero.md)
> **Consumers:** [`strategy-catalogue-3tier.md`](./strategy-catalogue-3tier.md) (FOMO tearsheets) · DART terminal
> (Performance tab) · Reports (IM allocator view).

---

## §1 — What it does

`<PerformanceOverlay>` renders one strategy instance's **continuous** P&L timeline across three regimes:

1. **Backtest** — historical simulation result.
2. **Paper** — `odum-paper` client-zero matching-engine fills (see
   [`../../14-customer-journeys/shared-core/odum-paper-client-zero.md`](../../14-customer-journeys/shared-core/odum-paper-client-zero.md)).
3. **Live** — `odum-live` client-zero real-venue fills (only if the instance graduated to `live_early`+).

These three coloured series on one chart is the USP of the allocator experience — backtest promises, paper confirms,
live proves. An allocator diagnoses alpha decay by watching the gap widen / narrow across regime boundaries.

---

## §2 — Three render modes

The same component supports three modes via a `mode` prop.

| Mode       | What it does                                                                                             | When to use                                          |
| ---------- | -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `overlay`  | All three series on one axis, colour-coded. Shared X.                                                    | Alpha-decay diagnosis; DART terminal Performance tab |
| `stitched` | Single line: backtest until paper starts, paper until live, live thereafter. Markers at each transition. | FOMO tearsheets — "one continuous story"             |
| `split`    | Three stacked sub-charts; shared X, independent Y.                                                       | Reports allocator view — inspect each regime alone   |

### Colour palette (standard)

- Backtest: `muted-blue` (#8AA4C7) — historical, faded to signal "simulated"
- Paper: `amber` (#E0A84A) — active, cautious
- Live: `emerald` (#27AE60) — earnest, real capital

These are the canonical mappings — any new surface consuming `<PerformanceOverlay>` MUST use these three colours, not
rebrand them. Consistency across admin + client + IM surfaces > local aesthetic.

### Transition markers

Dashed verticals at `paper_started_at` + `live_started_at` with a small phase-badge label above the chart (`paper_1d`,
`paper_stable`, `live_early`, `live_stable`). Phase annotations come from `StrategyInstanceLifecycle.phase_history` (see
[`strategy-lifecycle-maturity.md`](./strategy-lifecycle-maturity.md) §1 phase-transition record).

### Missing-view fallbacks

- Instance still in `backtest_*` phases → only backtest series; stitched mode just renders the backtest line.
- Instance in `paper_*` phases but no live → backtest + paper; stitched renders backtest → paper with one transition
  marker; no live series present in the response.
- `per_venue=true` on an instance with one venue → `per_venue` slice has a single entry equal to the aggregate; no
  breakdown available.

Fallback is **silent omission** — if a view isn't available, the toggle is disabled (greyed) with a tooltip explaining
why ("Live series not available yet — instance is at `paper_stable`."). No error states for missing series.

---

## §3 — Allocator query patterns

Four standard queries the UI must support via props, all backed by the same API endpoint:

### 3.1 — Live vs paper on the same window

**Question.** Is the live run tracking the paper run, or diverging?

```tsx
<PerformanceOverlay instance_id={id} mode="overlay" views={["paper", "live"]} range={{ from: "30d", to: "now" }} />
```

Residual (paper − live) is printed in the stats sidecar. Exceeding per-archetype thresholds surfaces a
`STRATEGY_PAPER_LIVE_DRIFT` event to Observe · Risk (see
[`../../14-customer-journeys/shared-core/odum-paper-client-zero.md`](../../14-customer-journeys/shared-core/odum-paper-client-zero.md)
§6).

### 3.2 — Live vs backtest on the same window

**Question.** Do live results agree with what the backtest predicted for this window?

```tsx
<PerformanceOverlay instance_id={id} mode="overlay" views={["backtest", "live"]} range={{ from: "30d", to: "now" }} />
```

Measures **strategy-model fidelity** (not execution alpha — use §3.1 for that).

### 3.3 — Alpha decay on scale (the promotion question)

**Question.** When this strategy graduated `paper_stable → live_early`, did alpha decay as real capital scaled in?

```tsx
<PerformanceOverlay instance_id={id} mode="stitched" views={["backtest", "paper", "live"]} showPhaseMarkers />
```

Allocator scans the stitched line for a kink at the `live_early` marker. A dropping slope post-live indicates capacity /
market-impact issues at the current allocation size. The fix is either: (a) scale down, (b) widen the venue-set variant
(e.g. `ely_base_3cex → ely_premium_6cex` for more liquidity).

### 3.4 — Per-venue slice

**Question.** Which venues are driving execution degradation?

```tsx
<PerformanceOverlay instance_id={id} mode="split" views={["paper", "live"]} per_venue />
```

API response expands: `series.live.per_venue = { [venue_id]: series }`. Each venue renders as a sub-line within the
`live` chart. Allocator drills into the underperformer and either: (a) removes the venue from the venue-set variant, (b)
routes around it via execution-service routing weights.

---

## §4 — API contract

### Endpoint

```
GET /api/v1/strategy-instances/{instance_id}/performance
    ?views=backtest,paper,live
    &from=ISO-8601-or-rolling-window    (e.g. "30d", "2026-01-01")
    &to=ISO-8601-or-now                 (default "now")
    &per_venue=bool                     (default false)
```

### Response shape

```jsonc
{
  "instance_id": "DEFI_BASIS_ELYSIUM@ely_base_3cex-btc-usdt",
  "series": {
    "backtest": [{"t": "2023-01-01T00:00:00Z", "pnl": 0, "equity": 1000}, ...],
    "paper":    [{"t": "2025-06-01T00:00:00Z", "pnl": 0, "equity": 1000}, ...],
    "live":     [{"t": "2026-01-15T00:00:00Z", "pnl": 0, "equity": 1000}, ...]
  },
  "transition_markers": {
    "paper_started_at": "2025-06-01T00:00:00Z",
    "live_started_at":  "2026-01-15T00:00:00Z"
  },
  "phase_annotations": [
    {"phase": "paper_1d",     "at": "2025-06-01T00:00:00Z"},
    {"phase": "paper_14d",    "at": "2025-06-15T00:00:00Z"},
    {"phase": "paper_stable", "at": "2025-07-01T00:00:00Z"},
    {"phase": "live_early",   "at": "2026-01-15T00:00:00Z"}
  ],
  "per_venue": {
    "live": {
      "OKX":     [{"t": "...", "pnl": 0}, ...],
      "BINANCE": [...],
      "BYBIT":   [...]
    }
  }
}
```

Per-venue sub-object only present when `per_venue=true`. Keys under `per_venue` match the view list (backtest does not
typically expose per-venue; paper + live do).

### Source of truth

- Backtest → `pnl_timeseries/(odum-paper, instance_id, regime=backtest)`
- Paper → `pnl_timeseries/(odum-paper, instance_id, regime=paper)`
- Live → `pnl_timeseries/(odum-live, instance_id, regime=live)`

All materialised by `position-balance-monitor-service` from execution-service fills.

### Cache policy

| Series           | TTL                                                   | Why                                           |
| ---------------- | ----------------------------------------------------- | --------------------------------------------- |
| Paper            | 60s                                                   | Fast-moving; allocator expects near-real-time |
| Live             | 60s                                                   | Same                                          |
| Backtest         | 1h                                                    | Static; only mutates when strategy is re-run  |
| Per-venue slices | computed on-demand with same TTL as the parent series |                                               |

### Permissioning

Two alternative gates (OR):

- **`reporting` entitlement** — grants access to all instances routed `dart_only|im_only|both`. FOMO surface path.
- **Subscription row on `(org, instance_id)`** — grants access even without the `reporting` entitlement. Reality surface
  path.

Admin + internal-trader bypass both gates.

---

## §5 — Stats sidecar

`<PerformanceOverlayStats>` sits next to the chart and recomputes per-view statistics on every range change:

| Stat           | Definition                                                | Displayed per view   |
| -------------- | --------------------------------------------------------- | -------------------- |
| Sharpe         | Annualised Sharpe on daily-return series                  | ✓                    |
| Max drawdown   | Deepest peak-to-trough on the equity curve                | ✓                    |
| CAGR           | Compound annual growth rate over the rendered range       | ✓                    |
| Win rate       | `winning_days / trading_days`                             | ✓                    |
| Avg trade size | Mean notional per fill                                    | ✓                    |
| Residual       | `paper - live` or `backtest - live` when 2 views selected | Only in 2-view modes |

Typography: monospace ticks, tabular-nums. Pairs visually with the chart (same aesthetic as the tearsheet at large).

---

## §6 — Consumers

| Surface                       | Mode                              | Views                   | `per_venue` |
| ----------------------------- | --------------------------------- | ----------------------- | ----------- |
| FOMO tearsheet card           | `stitched`                        | `backtest, paper, live` | false       |
| DART terminal Performance tab | `overlay`                         | toggleable              | false       |
| Reports IM allocator view     | `split`                           | `backtest, paper, live` | true        |
| Admin universe row spark      | inline spark (not full component) | `paper` only            | false       |

Every consumer mounts the **same** component — no alternative "lite" version. Rendering cost is handled at the API/cache
layer (§4), not via divergent components.

---

## §7 — `odum-paper` / `odum-live` as source of truth

A single commercial claim underlies this whole surface: **the live line shown is Odum's own live run of the instance,
never a real client's run.** That guarantee is encoded by the API query layer:

- `views=live` resolves to `pnl_timeseries/(odum-live, instance_id, regime=live)` — always, for every caller.
- Real client P&L never appears in `<PerformanceOverlay>`. Real-client P&L lives on the Reality tab's
  `<RealityPositionCard>` (see [`strategy-catalogue-3tier.md`](./strategy-catalogue-3tier.md) §4.1) which is a different
  component reading a different source.

No code path in `<PerformanceOverlay>` takes `client_id` as input. It's by design — there is only one representative
live run per instance, and it's Odum's.

---

## §8 — Cross-references

- [`strategy-lifecycle-maturity.md`](./strategy-lifecycle-maturity.md) — 9-phase maturity + `odum-paper` seed rows;
  `phase_history` drives transition markers.
- [`../../14-customer-journeys/shared-core/odum-paper-client-zero.md`](../../14-customer-journeys/shared-core/odum-paper-client-zero.md)
  — the series source + drift-monitoring doctrine.
- [`strategy-catalogue-3tier.md`](./strategy-catalogue-3tier.md) — Tier 3 FOMO tearsheets embed this component.
- [`dashboard-services-grid.md`](./dashboard-services-grid.md) — DART + Reports tiles surface this.
