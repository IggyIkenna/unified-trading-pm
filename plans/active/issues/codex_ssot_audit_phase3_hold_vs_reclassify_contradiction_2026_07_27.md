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
status: open
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
resolved_by:
source:
  [
    /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
  ]
---

# Phase-3 apply: operator hold vs reclassification contradiction

> **STATUS: `BLOCKED-OPERATOR-DECISION`.** Server block `BLK-d1b29089` (slot 16, 2026-07-27) escalated this to the
> operator; main answered SPLIT-DECISION and escalated GATE-1 up. This doc is the durable capture so a fresh session
> does not re-derive the block from scratch or plow ahead into held work.

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

- [ ] [OPERATOR-DECISION] P1. **Rule on GATE-1**: is the 2026-06-01 FIX-STALE-only hold LIFTED for
      `codex_vs_repo_docs_ssot_audit_2026_06_01` (Option A), still in force (Option B), or lift+re-dispatch-to-opus
      (Option C)? Then reconcile the plan so its dispatch state and its registry hold-language agree. (repo:
      unified-trading-pm)
