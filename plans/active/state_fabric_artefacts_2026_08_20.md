---
doc_type: plan
title: State fabric — client artefacts (two new documents, seven existing, and a readiness ledger to source them from)
summary: >-
  Owns R27 and the artefact surface. Two new client-facing documents (execution hot/warm/cold plus reproducibility;
  recoverability plus risk), the seven existing HTMLs updated against the 27 rulings of 2026-08-20, the shard-level
  coverage drilldown the walkthrough does not currently have, and — the piece that stops all of it rotting — a
  persisted readiness ledger the artefacts RENDER FROM instead of transcribing by hand.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [state-fabric, client-artefacts, readiness-ledger, coverage, disclosure]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/04-architecture/cross-domain-state-fabric.md,
    /plans/audit/results/state_fabric_reconciliation_dispatch_2026_08_20.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 12
locked_by:
locked_since:
depends_on: []
supersedes:
superseded_by:
source:
context_scope:
  [
    /codex/04-architecture/cross-domain-state-fabric.md,
    /codex/02-data/honest-coverage-model.md,
    /plans/epics/system_readiness_master.md,
    /codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html,
  ]
---

# State fabric — client artefacts

> **Disclosure posture (operator ruling R27, 2026-08-20)**: these are **client-facing**, in
> `codex/14-customer-journeys/commercial-model/`, with gaps framed as **roadmap** rather than as defects — and with
> **factually honest current status**. Roadmap framing sequences the work; it never asserts a capability that does not
> exist. A gap reads as "planned, not yet built", never as an implied capability.
>
> **Standing constraints, unchanged**: no commercial, budget, funding, valuation, cost or ARR figures in any
> client-facing material; never name ClearLoop; nothing from an internal plan reaches a client artefact without
> operator approval.

## The two problems this plan solves

**1. The artefacts do not cover what they are believed to cover.** Measured 2026-08-20 against
`platform-external-api-walkthrough.html` (777KB): it has the right sections — "The coverage model", "Coverage by asset
group", "Shard schemas", "Readiness: batch, paper, live", "Measured versus projected" — but contains **exactly 8
distinct percentage values**, all asset-group rollups (48.73 overall; sports 99.26, prediction 92.81, tradfi 86.96,
cefi 45.57, defi 40.94). Zero occurrences of `capture_status`, `expected_unattempted`, `per day`, `day-by-day`,
`first_date`, `last_date` or `days covered`. It is a **rollup, not a drilldown** — there is no shard-level view and no
per-day coverage anywhere.

**2. The numbers are hand-carried, which is why they rot.** Four skills DERIVE readiness and coverage on demand —
`readiness-state-dump` (with execution instruction-path, execution order-capability, MTDS live-feed and
strategy-position probes), `honest-coverage-dump` (`dump_coverage.py`, `shard_universe.py`),
`archetype-code-completeness`, `gate-evaluation`. **No persisted ledger was found** (searched `readiness_ledger`,
`readiness_state.json`, `readiness_snapshot`, `shard_ledger` — four patterns, so absence is not proof). Derivation
without a ledger means no history, no single artefact to render from, and every update re-runs a skill and transcribes
numbers into HTML by hand. That is exactly how these artefacts went stale before.

Under R17 the readiness state should be a **published, versioned, dated generation** that the audits AND the artefacts
both read — declare once, consume many.

## Todos

### The readiness ledger (do this first — it sources everything below)

- [ ] [BACKEND] P0. **Persist a versioned readiness + coverage ledger** — one dated, content-hashed generation
      emitted by the existing skills rather than a fifth derivation. Must carry: per-shard coverage to the smallest
      shard granularity with per-day resolution, per-venue batch/paper/live readiness, per-archetype code-readiness,
      and the credentials leg. History retained, so improvement is visible.
- [ ] [BACKEND] P0. **Bind the artefacts to the ledger** — HTML renders from the generation, never from transcribed
      numbers. A figure in a client artefact must be traceable to a ledger generation id and date.
- [ ] [REVIEW] P1. **Confirm no fifth derivation was created.** The four existing skills stay authoritative; the
      ledger is their published output. Re-deriving coverage inside the renderer would repeat the exact duplication
      this plan exists to remove.

### The two new documents

- [ ] [DOC] P0. **Execution deep dive** — the whole execution infrastructure across hot / warm / cold path, plus
      reproducibility. Must cover the two orthogonal axes (semantic profile x performance tier), why `hot` on
      `block_ledger` means winning the block rather than microseconds, the order-state diff, output suppression, and
      the batch/paper/live symmetry. Full API contracts, schemas, code snippets and worked examples — spec'd in enough
      detail to be **audited as a design**, not summarised.
- [ ] [DOC] P0. **Recoverability and risk** — what happens when things go stale, when we start cold without the data
      we need, when we must replay. Cover the finality ladder and retraction, the kill/action-mask unification and its
      three states (`PERMITTED` / `SUPPRESSED` / `KILLED`), recovery-quality levels, warm-up and bootstrap types, and
      the honest current state: order and position durability, the timestamp collision, the dormant epsilon=0 proof.
      Same depth requirement — contracts, schemas, examples.
- [ ] [DOC] P1. **State planned-vs-current explicitly in both**, per item, so the roadmap framing never obscures what
      exists today. A reader must be able to tell shipped from planned without cross-referencing anything.

### The existing seven

- [ ] [DOC] P0. **Update all seven existing HTMLs against the 27 rulings.** They are
      `platform-api-reference`, `platform-architecture`, `platform-external-api-walkthrough`,
      `strategy-service-deep-dive`, `strategy-service-walkthrough`, `carveout-engineering`, and
      `ODUM_Elysium_Phase2_Update`. **Seven, not five** — the last two were missed in earlier accounting.
- [ ] [DOC] P0. **Add the shard-level coverage drilldown to the walkthrough** — smallest shard granularity, % across
      days, no exceptions, sourced from the ledger. This is the measured gap above.
- [ ] [DOC] P1. **Correct anything the rulings invalidate** — in particular any text implying the Taylor factor form
      is universal (it is the continuous-quote kernel), or that continuous-quote implies the fast path (profile and
      tier are orthogonal).

### Verification

- [ ] [REVIEW] P1. **Re-run the measurement that found this gap** after the drilldown lands — count distinct
      percentage values and per-day vocabulary in the walkthrough. If it still reads as 8 rollups, the drilldown did
      not land regardless of how much prose was added.
- [ ] [REVIEW] P2. **Check every client-facing figure against the standing constraints** before publication — no
      commercial/budget/funding/valuation/cost/ARR figures, ClearLoop never named.

## Progress Log

**2026-08-20 — authored.** No artefact edited. Created because R27 had zero tracked todos and the shard-drilldown gap
was measured, not assumed. The readiness-ledger todos lead deliberately: writing the drilldown by hand first would
mean transcribing thousands of shard numbers into HTML, which rots the day it is written.
