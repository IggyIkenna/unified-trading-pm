---
doc_type: plan
title: TradFi consolidated closeout — native AO extract finalize (reconcile the parent's own checkboxes + archive)
summary: >-
  Gated closeout for `tradfi_consolidated_native_ao_extract_2026_07_25.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until all 10 of that plan's todos are done. Unlike the batch1/batch2 satellite extractions
  (whose "source docs" were OTHER plans/issues), this extraction's todos are the CLOSEOUT PLAN'S OWN native todos — so
  the reconciliation target for most of them is `tradfi_consolidated_closeout_2026_07_18.md` itself: flip its 9
  corresponding native checkboxes (todo 10 of the parent extraction already edits that file directly and is excluded
  from this reconciliation pass), correct the Split-notice digest's stale catalogue-migration line (found live during
  the extraction's own triage), and re-check the 3 deliberately-deferred native todos for any newly-cleared gate.
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, native-extract, archival]
related:
  [
    /plans/active/tradfi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_consolidated_native_ao_extract_2026_07_25]
gate_on_depends: true
source: >-
  Fresh AO-eligibility triage session, 2026-07-25, per `task_template.md` §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# TradFi consolidated closeout — native AO extract finalize

> **Machine-gated on `tradfi_consolidated_native_ao_extract_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 10 tasks in that plan are `done`. `sequential: true` because
> todo 2 (reconcile) needs todo 1's context and both write to the SAME file
> (`tradfi_consolidated_closeout_2026_07_18.md`) as todo 10 of the parent extraction already touched — this whole plan's
> edits to that file must run as one serial pass, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Verify each of the parent extraction's 9 non-todo-10 todos actually landed with real evidence**
      before touching the closeout doc: re-read each cited target doc
      (`tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`,
      `krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md` [archived, cite-only], a new
      `tradfi_adapter_dead_code_fallback_audit_2026_07_25.md`, the shipped UAC/MTDS commit for the billing-entitlement
      classification, `data_status_page_ux_and_canonicalisation_2026_07_16.md`,
      `distinct_values_noncanonical_audit_2026_07_20.md`, `phantom_captures_tradfi_2026_06_28.md` + the 2 archived docs
      it cites, and the KRX catalogue live-read) and confirm the cited evidence is real (commit exists, report exists,
      live read shows what's claimed) — do not trust a todo's own "done" claim without re-verifying at least one hard
      fact per todo. **Done when**: each of the 9 todos has a confirmed-real evidence citation recorded (or, for any
      that don't check out, a note that it's NOT actually done and should stay open, re-queued rather than falsely
      reconciled).
- [ ] [REVIEW] P1. **Reconcile `tradfi_consolidated_closeout_2026_07_18.md`'s own 9 corresponding native checkboxes**
      (todos 1-9 of the parent extraction — NOT todo 10, which already edited that file directly as part of its own
      scope): for each of the 9, flip/update the closeout doc's own line to reflect the verified-real evidence from todo
      1 above, citing the parent extraction's commit(s). Specifically: (a) update the MVP-cell table (native lines
      199-208) per todo-1's per-cell wiring-proof/no-proof verdicts; (b) update the KRX name-column "STILL OPEN" note
      (native lines 392-400) per the parent's todo-9 result. Also, while editing this same file in this same pass,
      **correct the Split-notice digest's stale catalogue-migration line** (native lines 132-138: the digest currently
      says catalogue Surface A migration is "NOT yet executed" — the parent extraction's own frontmatter/triage found it
      is `[x]` "SHIPPED + APPLIED LIVE 2026-07-25" in `tradfi_manifest_content_recovery_completion_2026_07_24.md`;
      re-verify live before correcting, don't just copy the extraction's claim forward uncritically). **Done when**: all
      9 checkboxes/notes in the closeout doc are updated with verified evidence citations, the stale digest line is
      corrected (or confirmed still accurate if re-verification disagrees with the extraction's claim), and the 3
      deliberately-deferred native todos (adapter smoke findings, live defects, BLOCKED-INFRA certify) are re-checked
      once more for any gate that cleared in the interim — if any cleared, spin a new tracked todo/plan rather than
      silently resolving it here.
- [ ] [DOC] P1. **Archive `tradfi_consolidated_native_ao_extract_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): confirm the Deferred section's 3 items are still correctly deferred (not silently
      dropped) → add the archive banner → run the codex-alignment check → grep the corpus for every referrer of
      `tradfi_consolidated_native_ao_extract_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every corpus
      referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same commit.
