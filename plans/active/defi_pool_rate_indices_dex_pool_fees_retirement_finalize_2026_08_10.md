---
doc_type: plan
title: >-
  Finalize — reconcile `defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md`'s evidence back into its source
  docs and archive
summary: >-
  Gated finalize companion (operator ruling 2026-07-24) for the POOL/rate_indices/dex_pool_fees retirement plan. This is
  a batch-style extraction from `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`'s Todos section —
  reconciles evidence back into that doc's corresponding checkbox (and `defi_track01_...`'s R3 tracking, which this work
  also gates on), checks whether either source doc is now fully done, and archives this plan + its parent once complete.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [defi, finalize, archival, retirement]
related:
  [
    /plans/active/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
effort: low
drift_direction: advance-code
depends_on: [defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Required companion per task_template.md §4 "Every AO-dispatched plan needs a gated finalize plan" — authored alongside
  the retirement plan in the same session. `status: active` (not draft — `gate_on_depends: true` already holds this
  plan's tasks until the retirement plan's are done, so a matching draft status is redundant per task_template.md §4);
  the retirement plan itself stays `status: draft` until the rebuild VM reaches terminal SUCCESS.
---

# Finalize the POOL/rate_indices/dex_pool_fees retirement plan

## Todos

- [ ] [REVIEW] P1. **Reconcile the retirement plan's completed-todo evidence back into its source docs.** Re-verify
      (don't trust the plan's own copy) each cited commit/count against live state, then update: (1)
      `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`'s `## Todos` item "Retire POOL / `rate_indices` /
      `dex_pool_fees` legacy manifest rows" — flip to `[x]` with evidence citing the actual commits/counts from the
      retirement plan's Progress Log; (2) `defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s R3 checkbox —
      append a closing note that the post-rebuild retirement + rollup + panel re-check completed, with the same
      evidence. Check whether either source doc, after this reconciliation, has zero remaining open todos — if so, flag
      it as an archival candidate for the next todo rather than assuming it stays open (both currently have other
      unrelated open todos — `spot_pair` cross-check, `<blank>` panel fix in `defi_distinct_values...`; several
      unrelated tracks in `defi_track01...` — so neither is expected to fully close here, but verify rather than
      assume).
- [ ] [DOC] P2. **Run the standard 6-step archival ritual on the retirement plan itself** (all todos done, unlocked) —
      move to `plans/archive/2026_08/`, fix corpus-wide referrer paths (this finalize plan's own
      `related:`/`depends_on` pointer and any other doc that cites the active path), per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`. Then self-archive this finalize plan the
      same way once its own todos are done.
