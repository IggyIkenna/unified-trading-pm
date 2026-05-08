---
plan_type: epic-index
asset_group: cross-cutting
owner: ikenna
created: 2026-05-08
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
name: epics-readme
---

# Epics — May 23 2026 cutover

This directory holds **epic plans** — domain-target wrappers that pin the end-state for May 23 2026 and reference the
existing granular master/sub-plans in `plans/active/` that gate them. Epics do **not** duplicate sub-plans; they
orchestrate them.

## Layer model

```
master_to_live_defi_2026_05_23.md   ← umbrella-of-epics (May-23 cutover master)
        │
        ├── plans/epics/  (this dir)     ← 6 domain epics + 1 cross-cutting epic
        │       │
        │       └─ each references ↓
        │
        └── plans/active/                ← granular masters + sub-plans (defi_master, cefi_master, ml_and_features_master, etc.)
                │
                └─ each references ↓
                       (codex/, code, scripts/)
```

**Rule:** epics live above the granular masters; the May-23 cutover master sits above the epics. None of these layers
duplicates content — each adds orchestration above the layer below.

## The May-23 deliverables (folded 2026-05-08)

Per operator direction 2026-05-08, six same-domain epics were folded into their master plans (less indirection); only
`cross_cutting` remains here as a standalone epic. Each May-23 deliverable now lives in its master plan's
`## May-23 deliverable` section.

| May-23 deliverable                      | Lives in master § "May-23 deliverable"                                         | Scope                | Live/Batch | Archived epic (archaeology)                                                                           |
| --------------------------------------- | ------------------------------------------------------------------------------ | -------------------- | ---------- | ----------------------------------------------------------------------------------------------------- |
| Live DeFi rollout (carry archetypes)    | [`active/defi_master_2026_05_07.md`](../active/defi_master_2026_05_07.md)      | LIVE on real wallet  | Live       | [`archive/live_defi_rollout_may_23_2026.epic.md`](../archive/live_defi_rollout_may_23_2026.epic.md)   |
| CeFi ML                                 | [`cefi_master_2026_05_07.md`](./cefi_master_2026_05_07.md)                     | LIVE on real capital | Live       | [`archive/cefi_ml_may_23_2026.epic.md`](../archive/cefi_ml_may_23_2026.epic.md)                       |
| S&P prediction (CME)                    | [`tradfi_master_2026_05_07.md`](./tradfi_master_2026_05_07.md) (deliverable A) | BATCH ML only        | Batch      | [`archive/sp_prediction_may_23_2026.epic.md`](../archive/sp_prediction_may_23_2026.epic.md)           |
| Price arbitrage (CME futures + ETFs)    | [`tradfi_master_2026_05_07.md`](./tradfi_master_2026_05_07.md) (deliverable B) | BACKTEST only        | Batch      | [`archive/price_arbitrage_may_23_2026.epic.md`](../archive/price_arbitrage_may_23_2026.epic.md)       |
| Sports ML                               | [`sports_master_2026_05_07.md`](./sports_master_2026_05_07.md)                 | BACKTEST only        | Batch      | [`archive/sports_ml_may_23_2026.epic.md`](../archive/sports_ml_may_23_2026.epic.md)                   |
| Prediction markets                      | [`predictions_master_2026_05_07.md`](./predictions_master_2026_05_07.md)       | BACKTEST only        | Batch      | [`archive/prediction_markets_may_23_2026.epic.md`](../archive/prediction_markets_may_23_2026.epic.md) |
| Cross-cutting (catalogue / IDs / infra) | [`cross_cutting_may_23_2026.epic.md`](./cross_cutting_may_23_2026.epic.md)     | Workspace-wide       | Both       | (still active — workspace-wide concerns spanning all domains; explicitly NOT folded)                  |

## How to use these epics

**Read first.** Every epic has the same shape: end-state at May 23, IN/OUT scope, sub-plans consumed, cross-epic
handshakes, cross-cutting inherited. Reading the epic in 5 minutes gives you the orchestration picture; the sub-plans
hold the tactical work.

**Don't duplicate.** If you need to add a new todo, it goes in the relevant sub-plan (or a new sub-plan in
`plans/active/`), and the epic updates only its **sub-plans consumed** table to reference it. Epics are **read-mostly**
— the only writes are: (a) updating the consumed-plans table when a sub-plan is added/removed; (b) updating the
end-state at May 23 if scope changes (operator-approved); (c) closing open questions.

**Status flow.** Sub-plan checkboxes flip in their own files per the workspace `Commit + Push + Flip Plan Checkboxes`
HARD RULE. Epics do not track per-sub-plan checkbox state — they track **completion of the May-23 deliverable** as a
whole, evaluated against the end-state criteria.

**Plan format.** Epics follow the same Cursor-checkbox format (`- [x]` / `- [ ]`) as other plans for any leaf
deliverables they own directly (typically the end-state criteria + cross-epic handshakes), per
[`plans/PLAN_FORMAT.md`](../PLAN_FORMAT.md).

## Composition with workspace rules

- **Capture discoveries as plan todos** (CLAUDE.md HARD RULE). Discoveries during epic execution go into the relevant
  sub-plan, NOT the epic. Epic stays clean.
- **Cross-Plan Coordination Banners.** When a VM launches or an in-flight refactor starts, the banner lands on every
  affected sub-plan AND on every affected epic that consumes those sub-plans.
- **Findings Triage Discipline.** Findings from epic-execution sessions follow the case-1-to-5 routing. Issues that span
  multiple sub-plans get an issue doc under `plans/active/issues/`.
- **Daily work-split.** The two-side daily splits (Ikenna ↔ Harsh) reference epics for the day's domain target +
  reference sub-plans for the tactical scope.

## Lifecycle

Epics are created at scope-decision time (the operator names a domain target with a deadline) and live until that target
ships or is officially deferred. After May 23 cutover:

- Epics whose end-state shipped → `plans/archive/` with `status: complete`.
- Epics that slipped → reset deadline + reset scope, OR archive as `status: deferred`.
- Epics whose end-state is partially shipped → split into a "shipped" archive entry + a "residual" follow-up plan in
  `plans/active/`.

The May-23 cutover master (`master_to_live_defi_2026_05_23.md`) tracks epic-level completion in its readiness matrix;
sub-plan tactical state stays in the sub-plans.
