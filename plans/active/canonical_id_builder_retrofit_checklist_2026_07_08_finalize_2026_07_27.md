---
doc_type: plan
title: >-
  canonical_id_builder_retrofit_checklist_2026_07_08 — finalize (reconcile + archive gate)
summary: >-
  Gated closeout for canonical_id_builder_retrofit_checklist_2026_07_08.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched todos ship (citing each landing commit), then archives it via the standard 6-step ritual once fully
  closed. Authored 2026-07-27 as part of na_docs_validity_and_ao_eligibility_audit_2026_07_26.md's Phase 1
  reclassification pass, per task_template.md's finalize-plan-coverage rule (every assigned_vm:planning plan needs a
  companion gated finalize plan).
status: active
nature: process
asset_group: [cefi, defi, prediction, sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-30"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [canonical_id_builder_retrofit_checklist_2026_07_08]
gate_on_depends: true
source: >-
  na_docs_validity_and_ao_eligibility_audit_2026_07_26.md Phase 1 (2026-07-27) --
  canonical_id_builder_retrofit_checklist_2026_07_08.md was reclassified assigned_vm:NA -> planning after verifying its
  remaining open todos are bounded/deterministic and conflict-free against currently-active AO plans; this finalize doc
  closes the finalize-plan-coverage gate the reclassification itself triggered.
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# canonical_id_builder_retrofit_checklist_2026_07_08 — finalize

> **STATUS: `draft` — NOT dispatched.** Flips to `active` only once the gated plan's todos are done (or on explicit
> operator direction to start reconciling early). Machine-gated via `depends_on` + `gate_on_depends: true`.

## Todos

- [x] ✅ [REVIEW] P2. **Reconcile `canonical_id_builder_retrofit_checklist_2026_07_08.md`'s checkboxes** against
      whatever shipped — **DONE 2026-08-05 (slot-3, `review`).** All 14 checkboxes in the source plan were already
      flipped `[x]` by prior workers. Every cited landing commit verified reachable on `origin/live-defi-rollout`
      (instruments-service@`d2c73500`, `ca2f44e5`, `70eaaa4a`, `d09e0cf4`, `0247912d`;
      market-tick-data-service@`2d59869f`, `fbe8abb9`, `3ee21c8c`; unified-trading-pm@`8e39617f9`). **NOT archived** —
      real residual work remains (see Progress Log below). Source plan stays `active`.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: re-verified context_scope (4 entries), unchanged — code-free finalize gate, all entries
  still resolve.
- **2026-08-05 (slot-3, `review`)** — Reconciliation complete. All 14 source-plan checkboxes already flipped; all cited
  commits verified. **Residual work found (NOT archived — source plan stays active):**
  1. **8 un-migrated ad hoc `instrument_key` f-string sites** (found during 2026-08-01 todo-2 pass, still present at
     2026-08-05): `ankr.py:86`, `mantle.py:86`, `maker.py:101`, `stakewise.py:90`, `swell.py:86`, `stader.py:85` (all
     `:LST:`), `kamino.py:199` (`:SOLANA_VAULT:` — TYPE-correct per todo 1 but still not builder-routed),
     `pendle.py:274` (`:YIELD_BEARING:` — same, TYPE-correct but ad hoc). These use correct enum values so the retrofit
     is pure DRY (passthrough=True, no behavior change), same pattern as the 16 already-done sites.
  2. **Type-filter verification outstanding** — the 7 token types
     (A_TOKEN/DEBT_TOKEN/YIELD_BEARING/STAKING/SPOT_ASSET/POOL) from todo 1's resolution were never confirmed against
     the P0 "23 DeFi adapters silently return empty" type-filter bug
     (`canonical_id_p0_defi_adapter_type_filter_bug_2026_07_08.md`). May already be fixed but was never verified. Source
     plan left `active`; these should be promoted to tracked checkboxes or filed as a follow-up issue.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate.
