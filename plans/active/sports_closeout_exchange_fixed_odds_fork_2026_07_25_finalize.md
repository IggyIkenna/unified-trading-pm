---
doc_type: plan
title: Sports EXCHANGE_ODDS/FIXED_ODDS fork — finalize (reconcile parent pointer + archive)
summary: >-
  Gated closeout for sports_closeout_exchange_fixed_odds_fork_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 11 of that plan's todos are done. Reconciles evidence back into
  sports_consolidated_closeout_2026_07_19.md's Track C pointer (the parent's own EXCHANGE_ODDS/FIXED_ODDS content was
  replaced by a short pointer during the 2026-07-25 split) and its QG-assertion todo's forward-pointer note, then runs
  the standard archival ritual on the fork plan. Mirrors sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md's
  pattern.
status: draft
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, exchange-odds, fixed-odds, finalize, archival]
related:
  [
    /plans/active/sports_closeout_exchange_fixed_odds_fork_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_closeout_exchange_fixed_odds_fork_2026_07_25]
gate_on_depends: true
source: >-
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan,
  mirroring the sports_satellite_ao_dispatch_batch3-finalize precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Sports EXCHANGE_ODDS/FIXED_ODDS fork — finalize

> **Machine-gated on `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue any todo below until all 11 tasks in that plan are `done`.

## Todos

- [ ] [REVIEW] P1. **Flip `sports_consolidated_closeout_2026_07_19.md`'s Track C "EXCHANGE_ODDS vs FIXED_ODDS fork —
      MOVED 2026-07-25" pointer to a ✅ DONE line**, citing the fork plan's shipped commits for the mapping decision,
      the drain, the contract fork, the dual-read, both GCS moves, the dependency_checker update, the manifest
      reconcile, the cutover, the legacy retirement, and the codex audit — verify each cited commit exists (`git log`,
      not the fork plan's own claim alone). **Done when**: the parent's pointer line reads ✅ DONE with all shipped
      commits cited.
- [ ] [REVIEW] P1. **Confirm `sports_consolidated_closeout_2026_07_19.md`'s Track C QG-assertion todo's forward-pointer
      note has actually been re-verified** — its own text says the assertion's vocabulary list needs re-checking once
      this fork ships new instrument_type values. Re-run the QG assertion described there against a live sample and
      confirm EXCHANGE_ODDS/FIXED_ODDS are recognized as canonical. **Done when**: the QG assertion todo's own text is
      updated to record this re-verification, citing the fresh run.
- [ ] [DOC] P1. **Archive `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`** via the standard 6-step ritual:
      migrate any still-open follow-up → add the archive banner → codex-alignment check (the codex audit todo above
      already covers this — confirm, don't skip) → grep the corpus for every referrer of
      `sports_closeout_exchange_fixed_odds_fork_2026_07_25` (including this finalize doc's own filename) and fix each
      path to the archived location → clear `locked_by` (already empty, confirm) → archive this finalize doc alongside
      it in the same commit. **Done when**: the plan is moved to `plans/archive/2026_07/`, every corpus referrer
      resolves to the new path, and this finalize doc is archived in the same commit.
