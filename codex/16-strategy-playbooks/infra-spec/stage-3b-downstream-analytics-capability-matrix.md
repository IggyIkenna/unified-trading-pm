---
doc_type: codex-ssot
title: Stage 3B — Downstream Analytics Capability Matrix
summary:
  Authoritative 26-capability × 3-integration-mode (signals_only / client_strategy_and_downstream / full_pipeline)
  support matrix keyed off instruction_schema_fit — analytics needing upstream lineage (regime/model/feature-drift) are
  structurally not_available to signals-only; consumed by the Stage 3C cost() line-item filter, sales fit-check, and
  visibility slicing.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, execution, uac, verification, docspec, reconciliation]
related:
  [
    /codex/16-strategy-playbooks/infra-spec/stage-3b-instruction-schema-contract.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-uac-combo-rules.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md,
  ]
created: 2026-04-20
authoritative_for: [downstream analytics capability × integration-mode support matrix (signals-only vs full-pipeline)]
referenced_by:
  [
    /codex/16-strategy-playbooks/infra-spec/stage-3b-instruction-schema-contract.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Stage 3B — Downstream Analytics Capability Matrix

> **Purpose.** What Odum can produce for a client is a function of how deeply that client integrates upstream.
> Signals-only clients keep their research lineage off Odum's infrastructure, so certain analytics — anything that
> requires upstream regime / model / feature context — are structurally `not_available` for them, regardless of how much
> they pay. Full-pipeline clients unlock everything because their upstream is on Odum. This matrix is the authoritative
> specification of that relationship.
>
> **Consumers of this matrix:**
>
> 1. Stage 3C derivation engine — `pricing_quote(...)` line items exclude analytics that the `instruction_schema_fit`
>    value cannot support.
> 2. Sales — pre-demo fit-check reads this matrix to avoid selling analytics the prospect won't actually receive.
> 3. Client-reporting-tool — visibility slicing keys off integration mode to hide analytics cards that would show empty
>    data.
> 4. pb2b / pb2a briefing documents — the honest answer to "what reporting do I get?" is keyed off this matrix.
>
> **Sources:**
>
> - [`../_ssot-rules/10-strategy-instruction-schema-principles.md`](../../14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md)
>   §"Package boundaries" — block 6 (research/promote) and certain block-11 analytics excluded from signals-only.
> - [`../_ssot-rules/05-building-block-dimensions.md`](../../14-customer-journeys/_ssot-rules/05-building-block-dimensions.md)
>   block 11 (analytics packs) — sub-scoped per analytic family.
> - [`../_ssot-rules/07-data-licensing-boundaries.md`](../../14-customer-journeys/_ssot-rules/07-data-licensing-boundaries.md)
>   — enriched analytics are always sellable; anything that exposes raw data is not.
> - [`../_ssot-rules/03-same-system-principle.md`](../../14-customer-journeys/_ssot-rules/03-same-system-principle.md) —
>   research ≡ live infrastructure; the same service produces the analytic in both contexts (when the lineage is
>   available).
> - [`stage-3b-instruction-schema-contract.md`](stage-3b-instruction-schema-contract.md) §1 "What Odum does NOT need" —
>   the upstream IP that signals-only clients do NOT send is precisely the lineage certain analytics require.
> - [`stage-3b-uac-combo-rules.md`](stage-3b-uac-combo-rules.md) §1.16 — `instruction_schema_fit` dimension values.

---

## Integration modes (columns)

Three values of `instruction_schema_fit`. These are the matrix columns.

| Column                             | What the client runs upstream                                                                                                                                                                                | What Odum sees                                                                                                                                         |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **signals_only**                   | Full upstream: regime classification, model, feature eng, signal generation, portfolio construction — all client-side                                                                                        | Instructions conforming to the rule-10 8-field schema + client's own fills as they come back via reconciliation                                        |
| **client_strategy_and_downstream** | Client's strategy logic hosted on Odum infrastructure (client deploys their strategy into Odum's strategy-service). Research + feature eng may still be upstream, or may use Odum's research stack alongside | Strategy runs ON Odum infra — Odum sees signal → instruction → fill chain within the hosted boundary, but upstream features/models may still be opaque |
| **full_pipeline**                  | Optional upstream participation — the client can (and usually does) use Odum's research/promote/feature-engineering stack                                                                                    | Full lineage: research runs, backtests, promotion decisions, features, models, signal decisions, instructions, fills                                   |

**Mental model.** Each row below asks: "How much upstream lineage does this analytic need to compute?" Analytics that
only need client's fills + Odum's execution data are supported across all columns. Analytics that need the signal's
decision context, regime tag, or model output are supported only when Odum holds that context.

---

## Capability rows

Each capability: what it means + one-line support per integration mode + the structural reason. The reason is the
load-bearing part — it explains WHY the cell is what it is so sales + clients can't negotiate around a structural gap.

### Core execution-derived (supported everywhere)

These capabilities only require data that flows through Odum's execution + reconciliation stack. They work for every
integration mode because they don't require upstream lineage.

#### 1. P&L attribution (basic — total / by-instrument / by-venue)

| signals_only | client_strategy_and_downstream | full_pipeline |
| ------------ | ------------------------------ | ------------- |
| ✅ supported | ✅ supported                   | ✅ supported  |

Reason: basic P&L decomposes into (qty × price move) per fill — Odum sees all fills in all three modes.

#### 2. Execution quality metrics — TCA, slippage vs arrival, fill rate

| signals_only | client_strategy_and_downstream | full_pipeline |
| ------------ | ------------------------------ | ------------- |
| ✅ supported | ✅ supported                   | ✅ supported  |

Reason: TCA compares Odum's fills against market reference prices at instruction arrival; Odum timestamps every
instruction, so the "decision price" reference is known in all three modes. Block-11 `execution_quality_analytics`
sub-pack.

#### 3. Execution alpha (live fills P&L vs matching-engine simulated fills)

| signals_only | client_strategy_and_downstream | full_pipeline |
| ------------ | ------------------------------ | ------------- |
| ✅ supported | ✅ supported                   | ✅ supported  |

Reason: Execution alpha = live P&L – simulated fills P&L. Both legs need only (instruction, market data, venue
capability) — all of which Odum has in every mode. Matching engine is the deterministic simulator. See the "Batch =
Live" CLAUDE.md principle + execution-service `matching_engine/` module.

#### 4. Reconciliation (basic — instructions vs fills vs positions)

| signals_only | client_strategy_and_downstream | full_pipeline |
| ------------ | ------------------------------ | ------------- |
| ✅ supported | ✅ supported                   | ✅ supported  |

Reason: Reconciliation is structurally downstream — compare what Odum sent to a venue vs what the venue reports back.
Runs on execution data alone.

#### 5. Exposure tracking (by-venue / by-chain / by-instrument_type)

| signals_only | client_strategy_and_downstream | full_pipeline |
| ------------ | ------------------------------ | ------------- |
| ✅ supported | ✅ supported                   | ✅ supported  |

Reason: Exposure is a straightforward projection of position-balance-monitor state; position state is derived from
fills, which Odum sees in all three modes. Block-11 `exposure_analytics` sub-pack.

#### 6. Client-reporting-tool surfaces (positions, NAV, statements)

| signals_only | client_strategy_and_downstream | full_pipeline |
| ------------ | ------------------------------ | ------------- |
| ✅ supported | ✅ supported                   | ✅ supported  |

Reason: Rule-03 same-system — the reporting surface is shared across audiences. All three modes see their own
entitlement-sliced view. Block 1 (reporting core) is always included.

#### 7. Regulatory filings (MIFID, best-ex, transaction reporting)

| signals_only                                    | client_strategy_and_downstream                  | full_pipeline                                   |
| ----------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- |
| ✅ supported (if Reg Umbrella block 2 included) | ✅ supported (if Reg Umbrella block 2 included) | ✅ supported (if Reg Umbrella block 2 included) |

Reason: Block 2 (regulatory umbrella reporting) is orthogonal to integration mode — it gates by client type (Reg
Umbrella engagement), not by schema fit. Runs on Odum's execution data alone.

---

### Partially-supported (depth varies with integration mode)

#### 8. Strategy P&L attribution — decomposed by strategy_id (not per-signal)

| signals_only                                                                                                         | client_strategy_and_downstream | full_pipeline |
| -------------------------------------------------------------------------------------------------------------------- | ------------------------------ | ------------- |
| ⚠️ partial — rolls up to `client_strategy_id` (rule 10 required field §2.6), but individual signal boundaries opaque | ✅ supported                   | ✅ supported  |

Reason: Rule 10 requires `strategy_instruction_id.client_strategy_id` as a stable identifier. Signals-only gets P&L
aggregated by that id — but since Odum does not see the client's internal signal boundaries (alpha decay window, regime
transition, etc.), the client has to grep their own upstream logs to cross-correlate to specific signals.

#### 9. Attribution by regime (risk-on / risk-off / macro regime decomposition)

| signals_only     | client_strategy_and_downstream                                   | full_pipeline |
| ---------------- | ---------------------------------------------------------------- | ------------- |
| ❌ not available | ⚠️ partial — if client's hosted strategy exposes regime as a tag | ✅ supported  |

Reason: **not available** in signals-only because regime classification is explicitly upstream (rule 10 §"What Odum does
NOT need" #1). Odum doesn't know what regime the client thought they were in when they sent the instruction. **Partial**
for client_strategy_and_downstream because the hosted strategy can optionally annotate its decisions with a regime tag
the client writes; Odum will attribute P&L by that tag but the taxonomy is client-defined, not Odum-validated.
**Supported** for full_pipeline because the regime classifier itself is an Odum feature group with a defined schema.

#### 10. Factor attribution (market / size / value / momentum / idiosyncratic)

| signals_only                                 | client_strategy_and_downstream                                                                          | full_pipeline                                                     |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| ⚠️ partial — post-hoc factor regression only | ⚠️ partial — post-hoc factor regression; strategy-level alpha not attributable to client's factor model | ✅ supported with strategy-side factor exposure reported natively |

Reason: **Partial everywhere except full_pipeline.** Post-hoc regressions of client's returns onto Odum's factor library
work regardless of integration — that's a generic analytic. But "the strategy has a 0.4 loading on momentum BY
CONSTRUCTION" requires seeing the upstream portfolio construction, which only full_pipeline provides. Block-11
`factor_attribution_analytics` sub-pack sold at different depths per mode.

#### 11. Liquidity analytics on traded instruments

| signals_only | client_strategy_and_downstream | full_pipeline |
| ------------ | ------------------------------ | ------------- |
| ✅ supported | ✅ supported                   | ✅ supported  |

Reason: Liquidity analytics run on market data, not on upstream model output. Block-11 `liquidity_analytics` sub-pack.

#### 12. Cross-client aggregate analytics

| signals_only                                  | client_strategy_and_downstream | full_pipeline     |
| --------------------------------------------- | ------------------------------ | ----------------- |
| ⚠️ partial — only at opt-in contractual level | ⚠️ partial — same              | ⚠️ partial — same |

Reason: Rule 07 §"Cross-client aggregates" — anonymised cross-client aggregates are Odum-enriched product, but
publishing needs explicit written consent at the contract level. Gating is contractual, not structural.

---

### Strategy-health metrics (need lineage)

#### 13. Strategy health — live-vs-backtest divergence monitor

| signals_only     | client_strategy_and_downstream                                               | full_pipeline |
| ---------------- | ---------------------------------------------------------------------------- | ------------- |
| ❌ not available | ⚠️ partial — only if hosted strategy has a backtest run registered with Odum | ✅ supported  |

Reason: **not available** in signals-only because live-vs-backtest comparison requires a backtest lineage record against
which to compare live P&L — signals-only clients keep backtests upstream, Odum never sees them. **Partial** for
client_strategy_and_downstream because the hosted strategy may register a backtest via Odum's research-service IF the
client uses Odum's research infrastructure for that strategy; not universal. **Supported** for full_pipeline — backtest
is always Odum-registered.

#### 14. Promote-pipeline readiness / maturity ladder tracking

| signals_only     | client_strategy_and_downstream                                | full_pipeline |
| ---------------- | ------------------------------------------------------------- | ------------- |
| ❌ not available | ⚠️ partial — only for strategies promoted via Odum's pipeline | ✅ supported  |

Reason: Maturity ladder (CODE_NOT_WRITTEN → LIVE_ALLOCATED per
[`../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md`](../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md))
is a promote-pipeline artefact — block 6. **not available** in signals-only by rule 10 package boundary (BL-11).
**Partial** for client_strategy_and_downstream because some client strategies may be promoted via Odum, but not all.
**Supported** for full_pipeline.

#### 15. Research-vs-live delta (metrics bound to Odum's research surface)

| signals_only     | client_strategy_and_downstream                    | full_pipeline |
| ---------------- | ------------------------------------------------- | ------------- |
| ❌ not available | ⚠️ partial — only if research ran on Odum's stack | ✅ supported  |

Reason: The delta is between Odum's research run and Odum's live run — same component, different data binding per
rule 03. If research wasn't on Odum, there's no Odum-side research record to delta against.

#### 16. Feature-drift monitor (live feature distribution vs training)

| signals_only     | client_strategy_and_downstream                              | full_pipeline |
| ---------------- | ----------------------------------------------------------- | ------------- |
| ❌ not available | ⚠️ partial — only if feature engineering uses Odum features | ✅ supported  |

Reason: Feature drift requires the feature group + training-window distribution, both of which live upstream in
signals-only. Odum doesn't see features in signals-only (rule 10 §"What Odum does NOT need" #2–#3).

#### 17. Model-performance monitoring (decay, calibration, hit rate)

| signals_only     | client_strategy_and_downstream     | full_pipeline |
| ---------------- | ---------------------------------- | ------------- |
| ❌ not available | ⚠️ partial — same condition as #16 | ✅ supported  |

Reason: Rule 10 explicitly lists model logic as upstream IP Odum does not receive.

#### 18. Regime-conditional reporting (P&L, Sharpe, drawdown, hit rate by regime)

| signals_only     | client_strategy_and_downstream                                        | full_pipeline |
| ---------------- | --------------------------------------------------------------------- | ------------- |
| ❌ not available | ⚠️ partial — only if regime tag flows through as instruction metadata | ✅ supported  |

Reason: Same structural issue as #9. Regime is upstream; Odum needs it as an explicit tag to do regime-conditional
reporting.

---

### Research + promote surfaces (block 6 — full-pipeline only by default)

#### 19. Backtest execution + P&L decomposition

| signals_only     | client_strategy_and_downstream | full_pipeline |
| ---------------- | ------------------------------ | ------------- |
| ❌ not available | ❌ not available               | ✅ supported  |

Reason: Block 6 excluded from signals_only by rule 10 (BL-11). `client_strategy_and_downstream` can get hosted strategy
execution but does not receive research/backtest surface by default — that's a full-pipeline capability. Upgrade path:
pay for full pipeline.

#### 20. Paper trading surface

| signals_only     | client_strategy_and_downstream | full_pipeline |
| ---------------- | ------------------------------ | ------------- |
| ❌ not available | ❌ not available               | ✅ supported  |

Reason: Same — paper trading is a block-6 surface.

#### 21. Shadow deployment / promote-to-prod flow

| signals_only     | client_strategy_and_downstream | full_pipeline |
| ---------------- | ------------------------------ | ------------- |
| ❌ not available | ❌ not available               | ✅ supported  |

Reason: Shadow + promote is the research/promote pipeline (block 6) — excluded from signals-only and from
client_strategy_and_downstream by default. Full-pipeline includes it.

---

### Reconciliation depth (differs by mode)

#### 22. Reconciliation depth — matching at fill level

| signals_only | client_strategy_and_downstream | full_pipeline |
| ------------ | ------------------------------ | ------------- |
| ✅ supported | ✅ supported                   | ✅ supported  |

Reason: Same as #4.

#### 23. Reconciliation — matching at signal level (did each signal produce the intended exposure?)

| signals_only                                                                                   | client_strategy_and_downstream | full_pipeline |
| ---------------------------------------------------------------------------------------------- | ------------------------------ | ------------- |
| ⚠️ partial — at `client_strategy_id` rollup, not per-signal unless client annotates explicitly | ✅ supported                   | ✅ supported  |

Reason: Rule 10 required field `strategy_instruction_id` gives aggregated reconciliation but not per-signal.

#### 24. Reconciliation — matching at intent level (did the model's decision flow through correctly?)

| signals_only     | client_strategy_and_downstream                                 | full_pipeline |
| ---------------- | -------------------------------------------------------------- | ------------- |
| ❌ not available | ⚠️ partial — requires hosted strategy to expose decision trace | ✅ supported  |

Reason: Intent-level reconciliation needs the model decision — upstream IP. Only full_pipeline has it.

---

### Cross-strategy / portfolio-level analytics

#### 25. Portfolio-level risk attribution (correlation, beta, tail)

| signals_only                                           | client_strategy_and_downstream | full_pipeline                                                           |
| ------------------------------------------------------ | ------------------------------ | ----------------------------------------------------------------------- |
| ⚠️ partial — post-hoc portfolio analysis on live fills | ⚠️ partial — same              | ✅ supported with forward-looking construction-based risk decomposition |

Reason: Post-hoc works anywhere. Forward-looking decomposition ("this new position adds 0.3 beta to momentum") requires
the upstream portfolio construction model — only full_pipeline.

#### 26. Capacity / capital-saturation modelling

| signals_only     | client_strategy_and_downstream                   | full_pipeline |
| ---------------- | ------------------------------------------------ | ------------- |
| ❌ not available | ⚠️ partial — requires capacity model from client | ✅ supported  |

Reason: Capacity models derive from market-impact + liquidity + client portfolio size — client's capacity model is
upstream IP in signals-only.

---

## Summary matrix — 26 capabilities × 3 modes

```
LEGEND:  ✅ supported   ⚠️ partial   ❌ not available
```

| #   | Capability                                             | signals_only | client_strategy_and_downstream | full_pipeline |
| --- | ------------------------------------------------------ | :----------: | :----------------------------: | :-----------: |
| 1   | Basic P&L (total / by-instrument / by-venue)           |      ✅      |               ✅               |      ✅       |
| 2   | Execution quality — TCA / slippage / fill rate         |      ✅      |               ✅               |      ✅       |
| 3   | Execution alpha (live vs matching-engine)              |      ✅      |               ✅               |      ✅       |
| 4   | Basic reconciliation (instructions vs fills)           |      ✅      |               ✅               |      ✅       |
| 5   | Exposure tracking (by venue / chain / instrument_type) |      ✅      |               ✅               |      ✅       |
| 6   | Client-reporting-tool surfaces                         |      ✅      |               ✅               |      ✅       |
| 7   | Regulatory filings (if Reg Umbrella block 2)           |      ✅      |               ✅               |      ✅       |
| 8   | Strategy P&L by `client_strategy_id`                   |      ⚠️      |               ✅               |      ✅       |
| 9   | Regime-attribution reporting                           |      ❌      |               ⚠️               |      ✅       |
| 10  | Factor attribution                                     |      ⚠️      |               ⚠️               |      ✅       |
| 11  | Liquidity analytics                                    |      ✅      |               ✅               |      ✅       |
| 12  | Cross-client aggregates (contract-gated)               |      ⚠️      |               ⚠️               |      ⚠️       |
| 13  | Strategy-health — live-vs-backtest                     |      ❌      |               ⚠️               |      ✅       |
| 14  | Promote-pipeline / maturity-ladder                     |      ❌      |               ⚠️               |      ✅       |
| 15  | Research-vs-live delta                                 |      ❌      |               ⚠️               |      ✅       |
| 16  | Feature-drift monitor                                  |      ❌      |               ⚠️               |      ✅       |
| 17  | Model-performance monitor                              |      ❌      |               ⚠️               |      ✅       |
| 18  | Regime-conditional reporting                           |      ❌      |               ⚠️               |      ✅       |
| 19  | Backtest execution + decomposition                     |      ❌      |               ❌               |      ✅       |
| 20  | Paper trading surface                                  |      ❌      |               ❌               |      ✅       |
| 21  | Shadow deployment / promote flow                       |      ❌      |               ❌               |      ✅       |
| 22  | Reconciliation — fill-level                            |      ✅      |               ✅               |      ✅       |
| 23  | Reconciliation — signal-level                          |      ⚠️      |               ✅               |      ✅       |
| 24  | Reconciliation — intent-level                          |      ❌      |               ⚠️               |      ✅       |
| 25  | Portfolio-level risk attribution                       |      ⚠️      |               ⚠️               |      ✅       |
| 26  | Capacity / capital-saturation model                    |      ❌      |               ⚠️               |      ✅       |

---

## Usage rules for sales, demo-ops, and contract desk

1. **Do not price analytics that structurally won't work in the client's mode.** The derivation engine filters these out
   of `pricing_quote` automatically. A manually-quoted analytic on a signals-only client that the matrix says is
   `not_available` is a mis-sale and gets rejected by contract-desk review.
2. **Partial (⚠️) cells require per-engagement scoping.** When the matrix says "partial — requires X", the engagement
   must specify whether X is present. No cell ships as ⚠️ without clarification in the contract.
3. **Upgrade path is explicit.** A client moving signals_only → full_pipeline gets every ✅/⚠️/❌ cell re-evaluated. The
   upgrade is a commercial event — new quote, not a per-capability bolt-on.
4. **Pre-demo fit-check uses this matrix.** Sales tells the prospect before the demo which cells turn ❌ under their
   integration mode. Unsurprising. Surprises here are rule-10 violations — prospect learns in the demo that the analytic
   they wanted doesn't work in their mode, and the engagement collapses.

---

## Reconciliation pass (vs Agent A's merged rules 05 / 07 / 10)

Reconciliation pass completed 2026-04-20 against the three merged rule files.

### Verified (no change needed)

- **Rule 05 block 6** (research / promote pipeline) — definition matches. The "Research + promote surfaces" section
  header in this matrix maps to capabilities #19, #20, #21; reasoning aligns with rule 05's description of block 6
  scope. Rule 05 §"Composition rules" explicitly excludes block 6 from the `(Client, downstream) → signals-only DART`
  typical blocks — load-bearing for #19/#20/#21's `signals_only = ❌`.
- **Rule 05 block 11** (analytics packs) — sub-scoping (`execution_quality`, `exposure`, `factor_attribution`,
  `regime_classification`, `liquidity`) aligns with rule 05 §"Sub-scoping within a block". Capabilities #2 / #5 / #10 /
  #11 / #18 correctly map to these analytic families.
- **Rule 07 §"Cross-client aggregates"** (line 84) — capability #12's "contract-gated partial" reasoning matches
  verbatim.
- **Rule 10 §"What Odum does NOT need"** (line 45) — the 4-item list (regime classification / raw model logic /
  signal-generation methodology / broader upstream IP) is the structural reason for `not_available` on capabilities #9,
  #13, #16, #17, #18, #24, #26. All seven map cleanly.
- **Rule 10 §"Package boundaries"** (line 60) — block 6 exclusion from signals-only confirmed. Capabilities #19, #20,
  #21 correctly gate on full_pipeline only.

### Resolved in this reconciliation pass

None — this matrix aligned with rules 05 / 07 / 10 as merged. Edits landed in sibling doc
[`stage-3b-uac-combo-rules.md`](stage-3b-uac-combo-rules.md) §1.15 and §3 BL-19 only.

### Watch-for (future rule-text changes)

- **Rule 10 §"What Odum does NOT need" revisions.** If Agent A adds / removes / renames upstream-IP items, re-evaluate
  capabilities #9, #13, #16, #17, #18, #24, #26 — their `signals_only = ❌` cells cite the exact list. Addition of a new
  upstream-IP item typically opens a new `❌` capability row.
- **Rule 05 block 11 (analytics packs) scope changes.** If rule 05 repartitions analytic families, re-check capabilities
  #2 / #5 / #10 / #11 / #18 cell assignments.
- **Rule 05 block 6 boundary changes.** If rule 05 later permits signals-only clients partial access to a block-6
  surface (e.g. read-only research view on their own flow), capabilities #19 / #20 / #21 `signals_only` cells move from
  `❌` to `⚠️`.
- **Rule 10 §"Package boundaries" Included/Excluded list.** If an analytic currently `signals_only = ✅` is moved to
  "Not included by default" in rule 10's list, the matrix row flips to `⚠️` (selected analytics packs clause) or `❌`.
