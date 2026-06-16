---
scope: [engineer, admin]
name: dart-mode-toggle
overview:
  SSOT for the DART operator surface — 3-way mode visualization (batch / paper / live), per-strategy event/fill/P&L
  rendering wired to real backend, and the manual-trade gate UI for `OperationalMode.MANUAL` strategies. Composes with
  the existing `dart-scope-bar.tsx` cockpit + `execution-mode-toggle.tsx` mode pills.
type: codex-ssot
status: stub (ownership split clarified 2026-05-10)
created: 2026-05-09
last_reviewed: 2026-05-10
locked_by: live-defi-rollout
locked_since: 2026-05-09
spawned_from: plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md
implements_in:
  - plans/active/master_to_live_defi_2026_05_23.md # Group G item 23 — conceptual model + readiness gating (sub-items pvl-p23a / pvl-p23b / pvl-p23c)
  - plans/active/promote_workflow_may23_cli_path_2026_05_10.md # Phases U5 (pvl-p23a DART 3-way) + U6 (pvl-p23c manual-trade gate UI) — actual UI surfaces
---

# DART mode toggle — 3-way visualization + manual gate

> **Stub doc — ownership split (clarified 2026-05-10).** The conceptual model + readiness gating live in
> `master_to_live_defi_2026_05_23.md` Group G item 23 (sub-items `pvl-p23a` / `pvl-p23b` / `pvl-p23c`). The **actual UI
> surfaces** (DART 3-way visualization + ManualTradeGateDialog component + execution-service unhold path + Playwright
> e2e) ship via `promote_workflow_may23_cli_path_2026_05_10.md` **Phases U5 + U6**. Stub fill-in happens via BOTH plans
> together — master plan owns the contract; promote-workflow plan owns the implementation. (Mode-data API endpoint
> `pvl-p23b` ships via the same promote-workflow plan **Phase U2**.)

## TL;DR

Three operator-facing surfaces compose in DART (unified-trading-system-ui):

1. **3-way comparison view** — batch / paper / live P&L curves + fills blotter + events + position trajectory + risk
   metrics for a single strategy archetype, side-by-side.
2. **Per-mode separate views** — the operator picks one mode via the existing `dart-scope-bar.tsx` Execution Stream
   toggle; canvas updates to show that mode's data exclusively.
3. **Manual-trade gate** — for `OperationalMode.MANUAL` strategies, per-trade approval affordance with pre-trade risk
   preview (margin / position-limit / worst-case loss). Approve / deny / timeout per instruction. Approval emits
   `MANUAL_APPROVED` event → execution-service unholds from manual-pending queue.

All three surfaces wired to **real backend** — not mock fixtures.

## Composability with existing DART surfaces

The current DART code (audit 2026-05-08):

- [`unified-trading-system-ui/components/shell/dart-scope-bar.tsx`](../../../../unified-trading-system-ui/components/shell/dart-scope-bar.tsx)
  — multi-axis filter cockpit with Execution Stream toggle (paper vs live, mock-only data today).
- [`unified-trading-system-ui/components/trading/execution-mode-toggle.tsx`](../../../../unified-trading-system-ui/components/trading/execution-mode-toggle.tsx)
  — Live ↔ Batch toggle (mock-only data today).
- [`unified-trading-system-ui/docs/reference/manual-trader-workflow.md`](../../../../unified-trading-system-ui/docs/reference/manual-trader-workflow.md)
  — design spec for manual gate, NOT implemented.

This SSOT extends those surfaces — doesn't replace them. The Execution Stream toggle gains a third option (batch);
ExecutionModeToggle gains paper as a third pill; both wire to the real backend per `pvl-p23b`.

## 3-way comparison view (`pvl-p23a`)

For any strategy archetype + run window, render three lanes simultaneously:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ DART Terminal — strategy: carry_staked_basis · window: 2026-05-20→23     │
├──────────────────────────────────────────────────────────────────────────┤
│ Filter chips: asset_group=defi · instrument_type=lst · venue=*           │
├──────────────────────────────────────────────────────────────────────────┤
│  Batch                  │  Paper                  │  Live                │
│  P&L: $1,247            │  P&L: $1,189            │  P&L: $1,156         │
│  Fills: 47              │  Fills: 47              │  Fills: 47           │
│  Drawdown: -2.1%        │  Drawdown: -2.4%        │  Drawdown: -2.6%     │
│  ┌──────────────────┐   │  ┌──────────────────┐   │  ┌──────────────────┐│
│  │ P&L curve (b)    │   │  │ P&L curve (p)    │   │  │ P&L curve (l)    ││
│  └──────────────────┘   │  └──────────────────┘   │  └──────────────────┘│
│  Fills blotter          │  Fills blotter          │  Fills blotter       │
│  Events                 │  Events                 │  Events              │
│  Positions              │  Positions              │  Positions           │
└──────────────────────────────────────────────────────────────────────────┘
```

Alternative rendering: **stacked-line-series canvas** — single P&L chart with three colored series (batch/paper/live)
overlaid. Picked at component-design time per UI rehearsal. Filter chips apply across all three lanes.

## Mode-data API (`pvl-p23b`)

Single API endpoint serves all three lanes:

```
GET /strategy/{strategy_id}/runs?mode=batch|paper|live&start={ts}&end={ts}
→ Response:
  {
    "strategy_id": "carry_staked_basis",
    "mode": "paper",
    "window": {"start": "...", "end": "..."},
    "pnl_curve": [...],
    "fills": [...],
    "events": [...],
    "positions": [...],
    "risk_metrics": {...}
  }
```

Lives on `deployment-api` or `strategy-service` — TBD per `pvl-p23b` design. Single endpoint per workspace pattern (one
API surface per logical resource); DART doesn't talk to three separate endpoints.

## Manual-trade gate (`pvl-p23c`)

For `OperationalMode.MANUAL` strategies, the manual-pending queue at execution-service holds each instruction until
operator action. DART surfaces:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Manual approval — instruction #42 · strategy: <id> · 14:23:18 UTC        │
├──────────────────────────────────────────────────────────────────────────┤
│ Action: BUY 1.5 ETH @ market on Bybit                                    │
│ Pre-trade preview:                                                       │
│   Margin used post-fill:  $4,820 / $20,000 (24%)                         │
│   Position limit:         within (current: 0.3 ETH; post: 1.8 ETH)       │
│   Worst-case loss:        -$240 if -8% gap to next session               │
│   Active alerts:          none                                           │
├──────────────────────────────────────────────────────────────────────────┤
│       [ Approve ]    [ Deny ]    [ Timeout: 5min ]                       │
└──────────────────────────────────────────────────────────────────────────┘
```

- **Approve** → emits `MANUAL_APPROVED` event with operator identity → execution-service unholds → fill at live venue.
- **Deny** → emits `MANUAL_REJECTED` event → strategy treats as fill-failure (per existing fill-failure event handling).
- **Timeout** → per-strategy config: cancel-with-audit / escalate-to-secondary-operator / hold-indefinitely.

**DART is the canonical operator surface**. Fallback approval channels (Telegram interactive button,
email-with-confirm-link, Slack interactive button) ship as a P1 follow-up, not in-scope for May-23.

## Cosmetic changes to existing components

- `dart-scope-bar.tsx` Execution Stream toggle: paper / live → **batch / paper / live** (3 segments).
- `execution-mode-toggle.tsx` pill: Live / Batch → **Live / Paper / Batch**.
- `LiveConfirmDialog` stays as mode-toggle confirmation. New `ManualTradeGateDialog` component handles per-trade
  approval (distinct from mode-toggle approval).

## Composes with

- [`../../04-architecture/operational-modes.md`](../../04-architecture/operational-modes.md) — canonical mode SSOT.
- [`../../04-architecture/paper-vs-live-execution-seam.md`](../../04-architecture/paper-vs-live-execution-seam.md) —
  execution-only seam.
- [`../../09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md`](../../09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md)
  — per-archetype 4-state matrix; DART surfaces the state per archetype.
- [`dart-terminal-vs-research.md`](dart-terminal-vs-research.md) — DART surface taxonomy.
