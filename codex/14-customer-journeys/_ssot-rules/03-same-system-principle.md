---
doc_type: codex-ssot
title: Rule 03 — The same-system principle
summary:
  "The same-system principle — DART/IM/Reg Umbrella are partitioned views of one operating stack; research infra ≡ live
  infra, DART is a live/batch toggle, catalogue rows carry phase tags, paper==live UI — with the orthogonal
  phase-vs-maturity model (every strategy component takes a phase prop)."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin, sales]
tags: [customer-journey, sales, strategy, reconciliation, ui]
related:
  [
    /codex/14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
  ]
created: 2026-04-19
authoritative_for: [same-system principle (one system, partitioned views; phase vs maturity)]
referenced_by:
  [
    /codex/08-workflows/client-onboarding.md,
    /codex/14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/_ssot-rules/09-internal-commercial-oneliners.md,
    /codex/14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md,
    /codex/14-customer-journeys/_ssot-rules/11-codex-scope-registry.md,
    /codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md,
    /codex/14-customer-journeys/_ssot-rules/README.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Rule 03 — The same-system principle

> One system, many views. DART, Investment Management, and Regulatory Umbrella are partitioned views of Odum's internal
> operating stack. Research, paper, and live are phase toggles over the same component tree. Nothing is forked for the
> client.

**Source:** [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On the same-system principle (rule 03)". Expanded
2026-04-19 with the research↔live / terminal-toggle / catalogue-phase-tag / paper-parity sub-claims.

## The five sub-claims

### (a) Client surfaces are partitioned views, not separate products

DART, IM, and Reg Umbrella are the same operating system with restricted visibility per audience. A client on the IM
path and a client on the DART path use the same underlying services, same reporting infra, same catalogue registries.
What differs is which slice of the registry their role and entitlements reveal.

**Compliance example:** IM allocator's `/services/reports/overview` and DART client's `/services/reports/overview`
render from the same route, same component tree, same backend endpoint. The data they see is filtered; the UI is not
rebuilt.

**Violation example:** Standing up a separate `im-reporting-ui` repo or a `/dart/reports/` fork. If two audiences get
the same product capability, they share the route.

### (b) Research infrastructure ≡ live infrastructure

Any metric that is generated during research is generated in live trading via the same component. The component binds to
a different data source (historical vs live), but the metric-generation logic, the schema, and the UI rendering are
identical.

**Compliance example:** P&L attribution on a backtest run and P&L attribution on live fills come out of the same
attribution service, same schema, same chart component. The only difference is the data source pointer.

**Violation example:** A "backtest P&L calculator" that re-implements attribution logic because the researcher didn't
want to call the live service. Any such duplication is a rule-03 violation and must be consolidated.

### (c) DART is a live/batch toggle over the same component tree

The terminal does not fork into a "backtest UI" and a "live UI". It is one UI with a mode selector. Same numbers, same
tables, same charts. Switching from live to batch rebinds the data source; it does not load a different page.

**Compliance example:** User on `/services/trading/terminal` flips a toggle from "live" to "backtest"; the same
positions table re-renders with historical fills; the same risk panel re-renders with historical exposures.

**Violation example:** A `/services/research/backtester/` route that renders a different table component from
`/services/trading/terminal`. Consolidate.

### (d) Strategy catalogue rows carry phase tags, not forked catalogues

The strategy catalogue has one row per slot. That row carries metadata including `lifecycle_phase` (research / paper /
live). The UI does not fork into "research catalogue" / "paper catalogue" / "live catalogue" — one catalogue, one row
per slot, phase shown as a tag.

**Compliance example:** A single row for `STAT_ARB_PAIRS_FIXED/spot/CEFI/binance-coinbase` shows phase = `live` today; a
researcher re-runs it against historical data and the phase indicator flips to `research` in their view while remaining
`live` in the live-trader view.

**Violation example:** Two separate routes `/catalogue/research/` and `/catalogue/live/` that render different row sets.
Wrong — it's one route, rows are phase-filtered.

### (e) Paper trading has same look and feel as live

Paper is not a separate product. It is live trading with simulated fills. The terminal, positions, reports, catalogue,
and observability UIs are identical in paper and live mode. Only the execution-fill source differs.

**Compliance example:** A client on paper mode sees the same P&L dashboard as a client in live. The P&L number is
simulated; the chart is the same.

**Violation example:** A `/paper-trading/` service with its own reporting UI that looks different from
`/services/reports/*`. Consolidate.

## Phase vs maturity — orthogonal dimensions

These two dimensions are frequently confused. They are independent.

| Dimension    | Values                                                                                                                             | Captures                                                                                                                                                                                                                                                                                |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Maturity** | CODE_NOT_WRITTEN → CODE_WRITTEN → CODE_AUDITED → BACKTESTED → PAPER_TRADING → PAPER_TRADING_VALIDATED → LIVE_TINY → LIVE_ALLOCATED | Promotion stage of a strategy slot — how far along the lifecycle it is, set by the promote-pipeline watchdog. Forward-moving in normal operation; only ops intervention demotes.                                                                                                        |
| **Phase**    | research / paper / live                                                                                                            | Execution-context of how a user is viewing / running the slot right now. A `LIVE_ALLOCATED` slot can be viewed in `research` phase when a researcher re-runs it over historical data. A `BACKTESTED` slot can be viewed in `paper` phase when a QA persona drops it into paper trading. |

Worked example:

- Slot `CARRY_BASIS_PERP/binance-perp/USDT` has maturity `LIVE_ALLOCATED` (promoted, capital assigned).
- An analyst opens it in research phase to study its historical behaviour over a new regime window. They see research
  metrics, backtest fills, research-phase tags in the UI.
- A live trader on the same slot sees live metrics, live fills, live-phase tags. Same slot, same UI, phase-filtered
  view.
- A QA engineer re-runs it in paper phase with current live data but simulated fills. Same UI, different phase tag.

**Rule:** every UI component that renders strategy data MUST accept a `phase` prop. The component tree never branches on
phase; the data-source binding does.

## Enforcement rules

1. **No product name implies separation.** Never write "the DART reporting product" or "the IM reporting tool" — there
   is one `/services/reports/*` surface used by both.
2. **No route prefix encodes phase.** Never create `/research/*` or `/backtest/*` or `/paper/*` as a top-level route.
   Phase is a data-binding, not a URL.
3. **No component tree duplicates a phase-variant.** If two components render the same conceptual data with different
   source bindings, they are one component with a `phase` prop.
4. **Cross-audience consistency.** A DART client and an IM client looking at the same catalogue entry see the same
   component; their filters differ, their component does not.
5. **Metric logic lives in one service.** No service re-implements a metric already computed upstream. Rule-03
   violations surface as "I'm re-calculating attribution because calling the service was slow / inconvenient" — fix the
   service, don't fork the logic.

## What this rule is not

- It is not a prohibition on role-based filtering. Admin sees everything; a demo prospect sees a restricted slice. That
  is visibility slicing (rule 06, demo-ops, Stage 3C access_control), not a rule-03 violation.
- It is not a prohibition on audience-specific narrative copy. pb2a and pb2b briefings read differently; they describe
  the same product.
- It is not a prohibition on deployment-topology separation. Staging and production are separate Firebase projects; the
  UI built into them is identical.

## Stage 3 implications

Rule 03 determines three Stage-3 design decisions:

1. **Stage 3B registry** — `lifecycle_phase ∈ {research, paper, live}` is a named dimension in the UAC combo registry,
   orthogonal to maturity. Blocker rules may apply per phase (e.g. certain analytics are research-phase-only due to
   data-license constraints).
2. **Stage 3C derivation engine** — `access_control(user, route, item, phase)` is phase-aware. The same combo is visible
   or not depending on whether the user is entitled to see it in research / paper / live context.
3. **Stage 3E refactor plan** — "no forked backtest / paper / live UIs" is a named G1 refactor item. Any route that
   violates rule 03 today gets consolidated. Current suspects include any legacy `/research/backtests` surfaces that
   duplicate terminal / positions / reporting components.

## Cross-references

- [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On the same-system principle (rule 03)"
- [`04-dart-commercial-axes.md`](04-dart-commercial-axes.md) — the three DART paths all assume one underlying system
- [`06-show-dont-show-discipline.md`](06-show-dont-show-discipline.md) — rule 06 handles WHAT to reveal; rule 03 ensures
  there is only ONE thing to reveal across audiences
- [`../../09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md`](../../09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md) — prior codex
  SSOT on demo/live parity; rule 03 generalises that principle beyond demos
- [`../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md`](../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md)
  — maturity ladder definition
