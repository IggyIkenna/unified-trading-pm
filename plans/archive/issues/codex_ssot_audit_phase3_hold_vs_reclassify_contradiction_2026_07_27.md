---
doc_type: issue
title: >-
  codex_vs_repo_docs_ssot_audit Phase-3 — operator FIX-STALE-only hold vs NA→planning reclassification contradiction
summary: >-
  The codex_vs_repo_docs_ssot_audit_2026_06_01 plan's own 2026-07-27 registry says REDIRECT/DELETE APPLY (Phases 3/4)
  "stays under the operator's standing FIX-STALE-only hold", yet the SAME plan was reclassified assigned_vm:NA→planning
  on 2026-07-27 and Phase 3 (that very apply) was dispatched to a worker. Executing ~20-repo irreversible
  REDIRECT/DELETE doc conversions against a standing operator hold is an operator-authority call — a worker cannot infer
  the hold is lifted. BLOCKED pending an explicit operator ruling.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ssot-contradiction, operator-decision, docs-audit, governance, blocked]
related:
  [
    /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md,
    /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27.md,
  ]
created: "2026-07-27"
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: review
drift_direction: correct-codex
last_updated: "2026-07-27"
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: gate-clearance-pass-2026-07-28
source:
  [
    /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
  ]
---

# Phase-3 apply: operator hold vs reclassification contradiction

> **STATUS: RESOLVED 2026-07-28 (operator gate-clearance pass).** Ruling: **Option A** — the FIX-STALE-only hold is
> **LIFTED** (the deliberate 2026-07-27 `NA→planning` reclassification is treated as the authorization signal that was
> intended), AND the plan-sanctioned **opus** sub-agent fan-out is authorized/required for the redirect/slim editorial
> judgment (folding in Option C's model-tier discipline rather than treating it as a separate contingent path).
> Reasoning: per the operator's standing general instruction on gated design-choice items with no specific answer on
> file — "unpause whatever needs unpausing to unblock a task" and "opt for full completions, no shortcuts" — a hold that
> is only blocking a deliberate, already-reclassified dispatch state, with no fresh risk introduced since 2026-06-01, is
> exactly the kind of pause that should lift rather than persist as a standing contradiction. The plan
> (`codex_vs_repo_docs_ssot_audit_2026_06_01.md`) has been flipped back `assigned_vm: NA → planning`, its banner
> updated, and Phases 3/4's gate language updated to reflect the clearance — see that plan for the live execution state.
> This issue doc stays as the durable record of the contradiction + ruling; no further action needed here.
>
> **Prior history (superseded by the ruling above, kept for record)**: Server block `BLK-d1b29089` (slot 16, 2026-07-27)
> escalated this to the operator; main answered SPLIT-DECISION and escalated GATE-1 up. **UPDATE 2026-07-28 (main
> agt-4d8de7, pre-ruling):** the block RECURRED as predicted — slot-12 hit it on task
> `codex_vs_repo_docs_ssot_audit-006` (BLK-613a61ff). Main answered PARK and, to stop the re-dispatch churn, executed
> issue-doc **Option B's park mechanism**: flipped the plan `assigned_vm: planning → NA`
> (`unified-trading-pm@b1651c1c4`, banner added to the plan). That was always a REVERSIBLE coordination stop-gap, not
> the GATE-1 resolution itself — the ruling above is the actual resolution.

## What I found

`codex_vs_repo_docs_ssot_audit_2026_06_01.md` carries a self-contradiction as of 2026-07-27:

1. **The plan HOLDS the apply.** Every 2026-07-27 registry entry (Appendix-A/B + the deployment-service / MDPS /
   instruments-service refreshed registries) states that REDIRECT/DELETE **APPLY** (= Phases 3/4) "stays Phase-3/4 under
   the operator's FIX-STALE-only hold" (operator chose FIX-STALE-only on 2026-06-01; only ~340 FIX-STALE literal fixes
   were permitted to land, DELETEs/REDIRECTs explicitly held). See plan line ~315 ("operator chose FIX-STALE-only;
   DELETEs/REDIRECTs held") and the per-repo "Apply stays Phase-3/4 under the operator FIX-STALE-only hold" notes.
2. **The plan DISPATCHES the apply.** The same plan was reclassified `assigned_vm: NA → planning` on 2026-07-27 (per
   `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` Phase 1, "after verifying its remaining open todos are
   bounded/deterministic and conflict-free"), which made Phase 3 (the redirect+slim APPLY) dispatchable — and it WAS
   dispatched to slot 16 (task `codex_vs_repo_docs_ssot_audit-003`).

The reclassification's source note does not mention the standing FIX-STALE-only hold, so it is plausible the hold was
overlooked when flipping to `planning`.

## Why it matters

- Phase 3 mutates ~20 repos of documentation via REDIRECT/DELETE conversions — irreversible-ish editorial calls the
  operator explicitly reserved. A worker executing them against a still-standing hold is a unilateral governance breach.
- It is a genuine **SSOT/governance contradiction** (findings-triage "big finding" class): the same document both holds
  and dispatches the same work.
- It will **re-block every future worker** dispatched Phase 3/4 until resolved (the plan reads as "dispatch me" while
  its registries read "held") — wasted dispatch cycles.

## Secondary gate (model tier) — resolved in principle, still open in practice

The plan is `model_tier: opus-required` / `execution_model: opus-1m`, and Phase-3 redirect/slim **judgment** is
explicitly opus-gated ("sonnet acceptable ONLY for the mechanical FIX-STALE literal sweeps"). Task -003 was dispatched
to slot 16 which **runs sonnet** (self-reported; the slot is _registered_ opus — a runtime drift main flagged to the
operator separately). The plan's own self-check: "Sonnet on this plan → STOP." So even if GATE-1 clears, Phase-3
judgment must run on opus (plan-sanctioned opus sub-agent fan-out, or re-dispatch to a genuine opus slot).

## Recommended decision (operator)

- **Option A (recommended):** Confirm the FIX-STALE-only hold is **LIFTED** for this plan (the deliberate NA→planning
  reclassification is the authorization signal) AND authorize the plan-sanctioned **opus** sub-agent fan-out for the
  redirect/slim judgment. Then a sonnet orchestrator may drive it with opus sub-agents doing the editorial edits. Also:
  update the plan's registry notes to drop the now-stale "under the operator FIX-STALE-only hold" language so it stops
  contradicting the dispatch state.
- **Option B (conservative):** Hold **remains** in force — restrict workers to FIX-STALE-only, keep Phase-3/4
  REDIRECT/DELETE apply deferred, and set the plan back to `assigned_vm: NA` (or gate Phases 3/4 behind a false
  prerequisite) so it stops auto-dispatching the held apply.
- **Option C:** Re-dispatch Phase 3 to a genuine **opus** slot (honours the model-tier HARD STOP most literally),
  contingent on Option A's hold-lift.

## What already shipped this session (permitted slice — NOT the blocked apply)

The operator-hold-PERMITTED mechanical FIX-STALE archived-mirror sweep (plan line-519) was completed + shipped: 3
`unified-trading-codex/` → PM `/codex/` repoints across 2 repos — `trading-agent-service@b481cf9`,
`ibkr-gateway-infra@2496fcb` — and the line-519 checkbox flipped (`unified-trading-pm@6edc6db49`). The other 3 named
repos already used the live form. This did NOT touch any REDIRECT/DELETE apply.

## Todos

- [x] ✅ [DOCS] P1. **RULED 2026-07-28 (retagged from [OPERATOR-DECISION]) — GATE-1 resolved: Option A (hold LIFTED),
      folding in Option C's opus-tier discipline.** Reconciled the plan (`codex_vs_repo_docs_ssot_audit_2026_06_01.md`):
      flipped `assigned_vm: NA → planning`, updated its banner + Phase 3/4 gate text to state the hold is lifted rather
      than pending, and flagged (in that plan's own banner) that every per-repo registry note still saying "Apply stays
      Phase-3/4 under the operator's FIX-STALE-only hold" is now historical language, not a live gate — whoever executes
      Phase 3/4 should update those notes as each repo's apply lands, so the plan does not drift back into
      self-contradiction. (repo: unified-trading-pm)
