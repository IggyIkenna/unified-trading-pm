---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 16 — 2026-08-17
summary: >-
  Extraction batch from the cross-cutting tranche's 2026-08-17 /na-eligibility-audit sweep (slot 28,
  na_eligibility_auditor, dispatch agt-7e78e2) — 5 conflict-cleared, bounded/deterministic items pulled from 3
  source docs (RECLASSIFY per-todo split). Each todo cites its exact source doc; the source docs themselves have
  already had their extracted checkbox flipped with a citation in the same audit pass, not deferred to this
  batch's finalize. Conflict-checked against every active assigned_vm:planning plan in the relevant parent_epics
  (orchestrator_master, agent_operating_framework_master, plan_hygiene_master, infrastructure_master), the
  cross-cutting consolidated closeout, and existing satellite batches (13/14/15) before drafting — no item here
  duplicates ground an existing dispatched todo already claims.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts]
scope: [engineer, admin]
tags: [cross-cutting, ao-dispatch, satellite-batch, na-eligibility-audit, plan-hygiene, git-tooling]
related:
  [
    /plans/active/issues/git_stash_push_pop_silently_drops_content_under_high_branch_velocity_2026_08_17.md,
    /plans/active/issues/na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2.0
assigned_role: infra
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/git_stash_push_pop_silently_drops_content_under_high_branch_velocity_2026_08_17.md,
    /plans/active/issues/na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md,
    unified-trading-pm/scripts/plan-hygiene/generate_na_doc_tranche_inventory.py,
  ]
source: >-
  /na-eligibility-audit cross-cutting tranche, dispatch agt-7e78e2, slot 28, 2026-08-17. Each item's own Source:
  line below names the exact source doc + todo it was extracted from.
---

# cross-cutting satellite AO dispatch batch 16

## From `git_stash_push_pop_silently_drops_content_under_high_branch_velocity_2026_08_17.md`

- [x] ✅ [SCRIPT] P2. **Attempt a clean repro of BOTH the stash-pathspec-staleness defect AND the transient-empty-pathspec
      no-op-push variant, in a scratch repo.** Two distinct hypotheses to test, both
      already fully specified by the source doc: (a) stash push a static file list → pull → pop with conflict →
      resolve → stash push the SAME static list again without re-querying `git status` → pull → pop — confirm or
      rule out that a stale, non-re-derived pathspec is what dropped content across repeated cycles; (b) a
      `stash push -- $pathspec` call where `$pathspec` is transiently empty (e.g. immediately after a prior failed
      commit attempt's own hook-triggered patch save/restore) — confirm it silently no-ops rather than erroring,
      and that a following unconditional `stash pop` then pops whatever unrelated stash happens to be on top. If
      confirmed, this closes a real gap in the stash-based reconciliation pattern several codex docs and worker
      instructions currently recommend. Done-when: each hypothesis is either reproduced with a minimal, saved
      repro script, or ruled out with a stated reason; a positive repro is written up with the exact sequence that
      triggers it. **Related, not a duplicate**: `plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md`
      already confirmed a DIFFERENT root cause (cross-process stash-interleaving between two concurrent sessions
      sharing one `.git`) for a related symptom class — read it first for context, but this todo's two hypotheses
      are about a SINGLE session's own repeated push/pull/pop cycling, a mechanically distinct claim. Source:
      `/plans/active/issues/git_stash_push_pop_silently_drops_content_under_high_branch_velocity_2026_08_17.md`
      todo 1. Repo: unified-trading-pm (scratch repro, not shipped code).
      — `unified-trading-pm@9e5e873988`; Evidence: `bash scripts/dev/repro-stash-pathspec-cycles.sh` reproduced both hypotheses.
- [x] ✅ [SCRIPT] P2. **Promote the CONFIRMED `git pull --rebase --autostash` per-batch fix into the durable recovery
      guidance** (reconcile with the existing nuanced `--ff-only`-from-a-clean-tree guidance already at
      `/codex/05-infrastructure/per-tab-worktrees.md:602`, don't blanket-override it). Not a hypothesis — the source doc's own "Third incident" section confirms `git pull --ff-only`
      can permanently stall once local history has genuinely diverged (a categorical git constraint), and that
      switching a per-batch reconciliation loop's pull to `git pull --rebase --autostash` fixed it, validated
      empirically across ~9 further batches with zero further loss. Add this as explicit guidance to
      `/codex/05-infrastructure/per-tab-worktrees.md` and/or
      `/codex/12-agent-workflow/host-concurrency-and-commit-provenance.md`: any multi-cycle commit loop
      reconciling against a shared branch should default its per-cycle pull to `--rebase --autostash`, never
      `--ff-only`. Done-when: the guidance is added to at least one of the two named codex docs, citing this
      finding. Source:
      `/plans/active/issues/git_stash_push_pop_silently_drops_content_under_high_branch_velocity_2026_08_17.md`
      todo 3. Repo: unified-trading-pm — unified-trading-pm@e022d3f0e3 + Evidence: /codex/05-infrastructure/per-tab-worktrees.md.

## From `na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md`

- [ ] [SCRIPT] P2. **Root-cause the remaining hash-instability cause(s) beyond the 2 already-confirmed bugs.**
      Bug 1 (residual blank-line delta between stacked markers) and bug 2 (same-date tie-break picks the first
      marker, not the latest) are both confirmed and have candidate fixes, but applying both together against all
      11 prediction-tranche mismatches the source doc measured leaves **0 of 11 self-consistent** — a third,
      unidentified cause remains. Trace 2-3 more of the 11 mismatches the same way the source doc traces
      `prediction_phase_e_football_arb_live_2026_07_24.md` (parent-commit hash vs. declared marker hash vs.
      current hash, diffed at the `_VERDICT_MARKER_LINE_RE`-stripped body level) until every case is explained,
      not just the first one found. Done-when: every one of the 11 mismatches has a stated, evidenced cause (not
      necessarily all the same cause). Source:
      `/plans/active/issues/na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md` todo 1. Repo:
      unified-trading-pm.
- [ ] [SCRIPT] P2. **Once item 3 above is fully root-caused, implement the complete fix in `generate_na_doc_tranche_inventory.py`
      and audit the 5 other importers for a duplicated reimplementation.** **Ordering NOT machine-enforced**: no
      `sequential:`/`gate_on_depends` links this todo to item 3 above — both are P2 same-priority in this plan and
      would dispatch concurrently under the default same-priority-concurrent rule, risking two workers editing
      `generate_na_doc_tranche_inventory.py` at once despite the stated "sequentially gated" intent below.
      Fix `body_content_hash()` / `_VERDICT_MARKER_LINE_RE` / `_latest_verdict_marker()` in
      `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` for every confirmed cause (not a partial fix —
      the source doc is explicit that shipping a fix that isn't fully correct forces a full unscoped corpus
      re-audit for no complete-correctness payoff). Then audit the 5 other declared importers
      (`check_extracted_checkbox_citation.py`, `generate_context_scope_inventory.py`, `check_na_corpus_ratchet.py`,
      `generate_tranche_doc_inventory.py`, `na_marker_helper.py`) for a duplicated/independently-drifted
      reimplementation of the same hashing or marker-parsing logic rather than an import of the fixed function —
      a duplicate would need the same fix applied twice. Sequentially gated on item 3 above within this same
      batch (ordinary plan structure, not a cross-doc blocker). Done-when: the fix is shipped + QG-green, and each
      of the 5 importers is confirmed to import (not reimplement) the fixed logic, or is itself fixed if it
      doesn't. Source:
      `/plans/active/issues/na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md` todo 2. Repo:
      unified-trading-pm.

## From `venue_readiness_and_registry_hardening_2026_08_16.md`

- [x] ✅ [AGENT] P1. **Publish the granularity view.** Render `unified_api_contracts.registry.venue_granularity`'s
      `VENUE_GRANULARITY_CAPABILITIES` + `get_granularity(venue, instrument_type, data_type)` (already shipped,
      412 populated `(venue, data_type)` cells across all 5 asset groups, instrument_type expressed as a default +
      per-instrument exceptions) as a table a human can read: venue, instrument type, data type, granularity,
      achievable matching class. This is now purely a rendering/reporting task, not a data-population one — the
      registry to render from already exists. Done-when: a re-runnable script (mirroring the existing
      `generate_venue_universe_denominator.py`/`generate_venue_consumability_report.py` pattern in the same repo,
      not a one-off) produces the table, and it is genuinely readable by a human without further processing.
      Source: `/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`, "Publish the granularity
      view" todo (§ GRANULARITY). Repo: unified-api-contracts. — shipped `unified-api-contracts@2f74bd8da2`
      (`scripts/generate_venue_granularity_report.py`, re-runnable; renders all 412 (venue, data_type) cells
      across the 5 asset groups + an honest "unclassified" bucket for the 25 registry venues absent from
      `VENUE_TO_ASSET_GROUP`).

## Progress Log

- **2026-08-17 (na_eligibility_auditor, dispatch agt-7e78e2, slot 28)**: drafted alongside the mandatory finalize
  companion, `cross_cutting_satellite_ao_dispatch_batch16_2026_08_17_finalize.md`.
- **context-scout 2026-08-19**: re-verified context_scope (5 entries, unchanged) — all 5 open todos still map 1:1 to
  the 3 already-cited source docs plus the 2 already-cited code targets (`generate_na_doc_tranche_inventory.py` for
  the hash-fix items, `venue_granularity.py` for the granularity-view item); all paths confirmed resolving on disk.
- **context-scout 2026-08-20**: trimmed context_scope to 3 entries — the venue-granularity todo is now done, so
  dropped its 2 tied entries; the 4 remaining open todos are still fully covered by the 3 kept entries.
- **2026-08-20 (infra worker, slot 19)**: Ran the saved scratch-repo repro
  `scripts/dev/repro-stash-pathspec-cycles.sh` successfully. Hypothesis A reproduced a stale static pathspec
  omission (`stash` count unchanged and `d.txt` remained dirty after the second push); hypothesis B reproduced an
  empty-pathspec no-op (`stash` count unchanged) followed by an unconditional `stash pop` applying the unrelated
  leftover stash. Script shipped in `unified-trading-pm@9e5e873988`.
