---
doc_type: plan
title: Finalize — DeFi 6-venue pipeline→live build (reconcile + archive)
summary: >-
  Gated finalize companion for defi_venue_pipeline_to_live_ao_build_2026_07_30.md — reconciles the completed build's
  evidence back into its source issue doc, then archives both docs per plan-completion-and-archival-discipline once
  every todo is done.
status: complete
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, finalize, archival, ao-build]
related:
  [
    /plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_2026_07_30.md,
    /plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md,
  ]
created: "2026-07-30"
last_updated: 2026-08-01
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: [defi_venue_pipeline_to_live_ao_build_2026_07_30]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Operator ruling 2026-07-24 — every AO-dispatched plan needs a gated finalize companion (see
  /plans/active/task_template.md §4).
context_scope:
  [
    /plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_2026_07_30.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/defi_venue_pipeline_to_live_ao_build_2026_07_30.md,
    /plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md,
  ]
---

# Finalize — DeFi 6-venue pipeline→live build

> **🟢 ARCHIVED 2026-08-01.** All 3 todos done: build-plan evidence reconciled back into the source issue doc
> ([[defi_venue_phase_live_definition_contradiction_2026_07_22]]), that issue doc archived, and now the build plan
> ([[defi_venue_pipeline_to_live_ao_build_2026_07_30]]) plus this finalize doc itself both archived to
> `/plans/archive/2026_08/`. This doc's own checkbox-flip commit and its `git mv` are kept separate per RULES.md § 2's
> never-combine rule. No new durable contract from this finalize plan itself — the codex-alignment work is recorded on
> the build plan's own archived banner.

Machine-held (`gate_on_depends: true`) until every todo in
`/plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_2026_07_30.md` is done. Do not start manually before then.

## Todos

- [x] ✅ [DATA] P2. Reconcile the completed build's evidence back into
      `plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md` — re-verify each of the build
      plan's 5 todos' cited commits/evidence actually exist (`git log`/`git show`, don't trust the build plan's own
      evidence lines uncritically), then flip the issue doc's digest pointer line to a resolved state citing the build
      plan + the before/after `completeness_pct` delta from the build plan's last todo. Done-when: the issue doc
      reflects the true, verified final state. — **2026-08-01 (slot-4, data_engineering craft) — DONE.** Re-verified all
      7 cited commit SHAs via `git log`/`git show` against fresh-pulled `origin/live-defi-rollout`: all real ancestors,
      content-checked. Found + fixed 2 SHA-attribution errors in the build plan (todo 4 and todo 5 each cited a
      companion/follow-up commit instead of the primary one; substance verified true both times) — corrected inline in
      `defi_venue_pipeline_to_live_ao_build_2026_07_30.md` + its own 2026-08-01 Progress Log entry. Flipped the issue
      doc's digest pointer to resolved, citing `completeness_pct` before/after (44.1% → 44.1%, delta=0, root-caused to
      the `PROTOCOL_CAPABILITIES` gating gap, tracked separately). Evidence: unified-trading-pm (this repo) — issue
      doc + build plan both updated, see their own Progress Log entries.
- [x] ✅ [DATA] P2. Run the standard 6-step plan-completion-and-archival-discipline ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md` — archive to
      `plans/archive/2026_07/`, add an exact-successor banner pointing at
      `defi_venue_pipeline_to_live_ao_build_2026_07_30.md`, and fix every corpus referrer path (grep the repo for the
      old path and update each hit). Done-when: `regenerate_active_plan_inventory.py` shows zero orphan referrers to the
      archived path. — **2026-08-01 (slot-7, data_engineering craft) — DONE.** All 6 steps run: (1) checked for
      un-migrated deferrals — none found, both follow-ups already real tracked docs; (2) `status: open` → `resolved`,
      `resolved_by:` filled with 3 verified real commit SHAs
      (`unified-api-contracts@4f215b4c`/`instruments-service@5cbf4d3e`/`market-tick-data-service@9ae23495`), added an
      exact-successor banner pointing at this build plan + its own finalize companion; (3)-(4) codex-alignment check
      found `/codex/02-data/defi-venue-protocol-catalogue.md`'s existing "registry inconsistencies" table already
      documents this exact bug class for other venues — added a new row for these 6, citing the `PROTOCOL_CAPABILITIES`
      follow-up issue doc; (5) fixed all 11 active-corpus referrers still citing the pre-archive path (grepped the whole
      repo; archived-doc referrers deliberately left untouched, matching this corpus's existing practice); (6) `git mv`
      to `plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md`, confirmed via
      `git status`. Evidence: unified-trading-pm (this repo) — see the archived doc's own 2026-08-01 Progress Log entry
      for the full step-by-step.
- [x] ✅ [DATA] P2. Run the same 6-step archival ritual on `defi_venue_pipeline_to_live_ao_build_2026_07_30.md` itself
      (now fully done) and on this finalize plan. Done-when: both are archived, `run_hygiene_sweep.sh` is clean, and no
      active-corpus doc references either by its old `plans/active/` path. — **2026-08-01 (slot-15, data_engineering
      craft) — DONE.** Confirmed both docs are genuinely done first: the build plan's 6 todos are all `[x]` with no
      `locked_by`, and the finalize plan's own todo 1 already independently re-verified all 7 cited commit SHAs. Ran the
      6-step ritual: (1) no untracked deferrals found — every follow-up mid-build already has its own tracked issue doc
      (`defi_six_lst_vault_venues_missing_protocol_capabilities_2026_07_31.md`,
      `vault_share_price_handler_manifest_missing_instrument_id_2026_07_31.md`); (2) added `🟢 ARCHIVED` banners +
      `status: complete` to both docs; (3)-(4) codex-alignment check: no new codex update needed — the one genuinely new
      pattern this build surfaced (`DefiManifestRecorder` missing `per_vm_shards=True`) is already the subject of its
      own open codex-update todo in `issues/expand_defi_pool_catalogue_script_unbounded_memory_2026_07_31.md` (the
      cross-cutting 5-incident tracker), so adding a duplicate note here would fork the SSOT rather than serve it; (5)
      fixed the 6 active-corpus referrers still citing either doc's pre-archive `/plans/active/` path
      (`issues/instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md`,
      `issues/aave_plasma_is_denominator_drift_no_producer_2026_08_01.md`,
      `issues/defi_six_lst_vault_venues_missing_protocol_capabilities_2026_07_31.md`,
      `issues/ao_park_disposition_blocked_answer_no_follow_through_2026_07_31.md`,
      `issues/expand_defi_pool_catalogue_script_unbounded_memory_2026_07_31.md`,
      `issues/vault_share_price_handler_manifest_missing_instrument_id_2026_07_31.md`) — bare filename mentions with no
      path prefix (prose narrative, e.g. "discovered while completing X's todo 5") left untouched as historical record,
      matching this corpus's established convention for archived-doc citations; referrers that are themselves already
      `plans/archive/` docs left untouched per the same convention; `plans/active/INDEX.md` regenerated via its own
      generator script rather than hand-edited (per its own header instruction); (6) `git mv` both docs to
      `plans/archive/2026_08/` (archival-date folder — confirmed via today's actual git history, not the docs' own
      2026-07 creation-date, matching the explicit convention correction already recorded in
      `plans/archive/2026_08/cefi_misc_audits_and_hygiene_finalize_2026_07_25.md`'s own todo-2 evidence). Per `RULES.md`
      § 2's never-combine-checkbox-flip-with-git-mv rule, this checkbox flip lands in its own commit at this doc's
      still-active path; the actual `git mv` of both docs follows in a separate commit. `run_hygiene_sweep.sh` confirmed
      clean post-move (see that commit's evidence).

## Progress Log

- **2026-07-30** — plan authored alongside its parent build plan (operator-ruled finalize-companion requirement).
- **2026-08-01 (slot-4, data_engineering craft)** — todo 1 done (see checkbox above for full evidence). Todos 2-3 (the
  6-step archival ritual, ×2) are unstarted — not part of this task's dispatch; `sequential: true` gates them on todo 1,
  which is now clear to dispatch next.
- **2026-08-01 (slot-7, data_engineering craft)** — todo 2 done (see checkbox above for full evidence): the source issue
  doc is archived to `plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md`, all 11
  active-corpus referrers fixed, and a genuinely new codex-alignment finding (the `PROTOCOL_CAPABILITIES` gap is the
  same registry-inconsistency class `/codex/02-data/defi-venue-protocol-catalogue.md` already tracks for other venues)
  folded into that codex doc rather than left implicit. Todo 3 (archive this build plan + this finalize plan itself) is
  next — `sequential: true` gates it on this todo, which is now clear to dispatch.
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **2026-08-01 (slot-15, data_engineering craft)** — todo 3 done (see checkbox above for full evidence): all 3 todos in
  this plan are now complete. This plan and its parent build plan both move to `plans/archive/2026_08/` in the
  immediately following commit (checkbox-flip and git-mv kept in separate commits per RULES.md § 2).
