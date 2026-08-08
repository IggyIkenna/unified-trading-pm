---
doc_type: plan
title: Sports taxonomy P1 — finalize (reconcile source docs + release the P2/P3 gates + archive)
summary: >-
  Gated closeout for sports_taxonomy_p1_capture_and_contracts_2026_08_08.md. P1 is a batch-style phase whose todos
  resolve open items in SEVERAL source docs, so this finalize reconciles each source doc's own checkbox (not just P1's),
  checks whether reconciling left any source doc at zero open todos and therefore archivable in its own right, confirms
  the capture-outage issue docs are genuinely closed rather than assumed, and only then archives P1.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, canonicalisation, finalize, archival, contracts]
related:
  [
    /plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md,
  ]
created: 2026-08-08
last_updated: 2026-08-08
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
depends_on: [sports_taxonomy_p1_capture_and_contracts_2026_08_08]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/02-data/sports-data-types-catalog.md,
  ]
source: >-
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
locked_by:
locked_since:
---

# Sports taxonomy P1 — finalize

> **Machine-gated** on `sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`.

## Todos

- [ ] [REVIEW] P1. **Reconcile every SOURCE doc P1 resolved, re-verifying each cited commit exists.** P1 is a
      batch-style phase: its todos close open items in
      `/plans/active/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md` (the 19-vs-21 unmapped
      bookmaker classification, resolved mechanically by retiring the split),
      `/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md` (the codex rename/split
      process rule), and the two capture-outage docs (`mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md`,
      `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`). Flip each source doc's OWN checkbox with evidence —
      do not trust a source doc's copy of an evidence line. **Done when**: every named source doc's checkbox is flipped
      and each cited commit is confirmed via `git log`.
- [ ] [REVIEW] P1. **Check whether reconciling left any source doc at zero open todos**, and if so run the same 6-step
      archival ritual on it — a finalize that closes only its own plan while leaving a now-fully-done source doc live is
      the exact omission that caused a real `run_hygiene_sweep.sh --ci` hard-fail (10 violations). **Done when**: each
      source doc is either still open with todos, or archived.
- [ ] [REVIEW] P1. **Confirm capture is STILL live, not merely restored once.** P1's Block A proves a single day; this
      re-checks that raw sports capture has continued writing for the full window since, and that the new staleness
      guard actually fires on a synthetic frozen-source day. A guard that was never observed firing is not a guard.
      **Done when**: continued capture is evidenced across the elapsed window and the guard is demonstrated firing.
- [ ] [REVIEW] P1. **Re-verify the already-archived exchange/fixed-odds fork pair still resolves.** Both
      `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` and its finalize sibling were marked `superseded` and
      **archived to `plans/archive/2026_08/` on 2026-08-08** in the same commit that authored this chain — the parent
      because the operator retired the instrument_type split it exists to implement, the sibling because a
      `gate_on_depends` finalize whose parent went terminal can never fire. Three active-corpus referrers were repathed
      at the time. This todo only re-checks that no NEW referrer has since been authored against the old `plans/active/`
      path (a real risk while this chain is in flight). **Done when**: a corpus-wide grep for either slug shows every
      referrer resolving to the archived location.
- [ ] [REVIEW] P2. **Confirm the P2 and P3 gates can legitimately release.** Both declare `gate_on_depends: true` on P1.
      Verify the contracts they assume actually exist in UAC (venue/executable split, single lowercase `odds`, `horizon`
      axis, retired `markets`/`outcomes`/`settlements`) rather than relying on P1's checkbox state alone. **Done when**:
      each assumed contract is confirmed present in the shipped UAC, or a blocking gap is filed as a `- [ ]` todo.
- [ ] [DOC] P2. **Archive `sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`** via the standard 6-step ritual,
      including the codex-alignment check (P1 CREATES codex docs — the rename/split process rule — and SUPERSEDES
      `sports-data-types-catalog.md`, so this is a real check, not a no-op), the corpus-wide referrer-path fixup for the
      plan slug, and archiving this finalize doc alongside it in the same commit. **Done when**: the plan is in
      `plans/archive/2026_08/`, every referrer resolves, and this doc is archived with it.

## Progress Log

- **2026-08-08** — Authored alongside the parent per the finalize-plan-coverage rule.
