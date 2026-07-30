---
doc_type: plan
title: Sports satellite AO batch 3 — finalize (reconcile source docs + resolve conflict-gated deferrals + archive)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch3_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 12 of that plan's todos are done. Mirrors sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md's
  pattern (reconcile each of the 8 distinct source docs' checkboxes independently), plus one batch3-specific addition:
  re-check the 6 conflict-gated Deferred items once the operator has ruled on the queued decision in
  autonomous_session_operator_decisions_2026_07_25.md — some may become dispatchable once the operator confirms which
  side (the narrow batch3-style fix vs. the master closeout's broader claim) should execute first.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-3, satellite-docs, archival]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-30"
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
depends_on: [sports_satellite_ao_dispatch_batch3_2026_07_25]
gate_on_depends: true
source: >-
  /autonomous session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs
  a companion gated finalize plan, mirroring the batch2/batch2_finalize precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Sports satellite AO batch 3 — finalize

> **Machine-gated on `sports_satellite_ao_dispatch_batch3_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 12 tasks in that plan are `done`. `sequential: true` because
> todo 2 (source-doc archival) needs todo 1's reconciliation done first (a doc can only be archived once its status is
> genuinely flipped to `resolved`), todo 3 (conflict-gated re-check) needs todo 1's reconciliation too, and todo 4
> (archival of this batch's own plan) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 (slot-11, `review`).** Reconciled all 8 distinct source docs against the
      parent's actual current `Source:` citations (ground-truth-derived from the 12 todos directly, not this todo's own
      pre-written doc list — see Progress Log for why 2 of them needed correcting). Found the SAME gate-vs-reality
      mismatch class as the cefi batch1 finalize precedent: parent todo 4 (KALSHI-row disposition) is genuinely `- [ ]`
      still, the only one of the parent's 12 todos not done, despite this finalize plan being machine-gated on all 12
      being done. Its source doc was left untouched (nothing shipped to flip). Of the 8 real source docs behind the
      other 11 done todos: 3 genuinely-open items were found and flipped with independently-verified commit citations (2
      in `issues/sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14.md`, 1 IAM-grant item in
      `issues/dp_catalog_not_running_sports_prediction_2026_07_15.md` — which reached 0 open todos and was flipped to
      `status: resolved`); 1 prose-form finding (not a checkbox) in `data_completion_sports_2026_07_24.md` was annotated
      with its investigation outcome + the filed follow-up issue doc; the remaining 5 docs were already correctly
      reconciled by earlier or later independent sessions (self-flipped at dispatch time, or reconciled by a later pass)
      — re-editing them would have been redundant churn. **Reconcile all 8 distinct source docs' checkboxes.** For each
      of `sports_satellite_ao_dispatch_batch3_2026_07_25.md`'s 12 now-done todos: flip the corresponding checkbox/
      section in its named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-3 commit(s)
      that shipped it — verify the actual shipped commit exists before citing it. The 8 source docs:
      `issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`,
      `issues/sports_odds_team_name_alias_gap_south_america_2026_07_09.md`,
      `sports_consolidated_closeout_aggregated_sources_2026_07_24.md` (6 of the 12 todos),
      `data_completion_sports_2026_07_24.md`, `issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` (2
      todos). For each: after flipping, re-check whether it now has 0 open todos remaining (unlikely for most — batch3
      was a small conflict-cleared slice of each doc's real remaining work). Only flip a doc's `status` to `resolved` if
      it genuinely reaches 0 open todos (checkbox AND prose-form — do not trust checkbox count alone). **Done when**:
      all 8 source docs' corresponding checkboxes/sections are flipped with verified evidence, and any doc that
      genuinely reaches 0 open todos is flipped to `status: resolved`.
- [ ] [DOC] P1. **Archive every source doc todo 1 drives to `status: resolved`/`complete` — in the same commit as the
      flip, never left sitting in `plans/active/`.** `check_terminal_status_archived.py` HARD-fails on any doc whose
      frontmatter reads a terminal status while it still lives under `plans/active/` (including `plans/active/issues/`)
      — the omission of this exact step across the sports finalize-plan family already forced one such HARD-fail: the
      `plan_health` gate's own remediation (`unified-trading-pm@57ed9271c`, escalation `agt-9a5061`, PR #1545)
      auto-archived 11 docs nobody's plan owned. For every one of the 8 source docs todo 1 flips to `resolved` with 0
      open todos: re-verify the 0-open-todos count and the resolution banner one more time, then archive it to
      `plans/archive/2026_07/` IN THE SAME COMMIT as the status flip — fix every corpus referrer of the archived doc's
      pre-archive path (grep for the basename). If todo 1 already ran before this todo existed in the plan, archive any
      already-`resolved`-but-still-active doc now, noting the flip predated this rule. **Done when**: no source doc this
      plan drives to a terminal status remains under `plans/active/`,
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports 0 hard failures, and every corpus referrer resolves
      to the archived path. Source: `archive/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md` § 2.
- [ ] [REVIEW] P1. **Resolve the conflict-gated Deferred section from batch3's own doc**, now that the operator has
      (presumably) ruled on the queued decision in `autonomous_session_operator_decisions_2026_07_25.md`. For each of
      the 6 conflict-gated docs (`data_completion_sports_2026_07_24.md` 2 items,
      `sports_legacy_fixtures_path_migration_2026_07_24.md` 1 item,
      `issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md` 1 item,
      `issues/fixtures_manifest_legacy_backfill_2026_07_24.md` 1 item,
      `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md` 1 item,
      `issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md` 1 item): re-read the specific conflicting
      todo in `sports_consolidated_closeout_2026_07_19.md` to check if it has since shipped (which would resolve the
      conflict by making the narrower item redundant/already-covered) or if the operator's ruling clarified which side
      should execute — if either, either mark the item covered (cite the shipped commit) or extract it as a new tracked
      todo in a follow-up batch. If still genuinely unresolved, leave it explicitly deferred (not speculative). Also
      separately review the 2 `doc_too_large_or_risky_for_batch` docs
      (`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`,
      `issues/sports_features_layer_findings_sweep_2026_07_18.md`) and recommend whether they warrant their own
      dedicated batch4 triage pass. **Done when**: each of the 6 conflict-gated items has either (a) a new tracked
      todo/plan created because the conflict cleared, or (b) an explicit re-verified confirmation the conflict is still
      open; and a recommendation is recorded for whether the 2 large/risky docs need their own batch4 pass.
- [ ] [DOC] P1. **Archive `sports_satellite_ao_dispatch_batch3_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 3 above
      should have already resolved all 6 — verify none remain) → add the archive banner → run the codex-alignment check
      (does `sports-features-bucket-path-ssot.md` under `codex/02-data/`, created by this batch's own todo 5, need any
      further cross-referencing) → grep the corpus for every referrer of
      `sports_satellite_ao_dispatch_batch3_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.

## Progress Log

- **2026-07-30 (slot-11, `review`) — todo 1 reconciliation complete.**
  - **Ground-truth derivation, not this todo's own doc list.** Before reconciling, extracted every actual `Source:`
    citation directly from `sports_satellite_ao_dispatch_batch3_2026_07_25.md`'s 12 todos (`grep -n "Source:"` + reading
    each wrapped line), rather than trusting this todo's own pre-written "8 source docs" summary — which turned out to
    fold 3 DIFFERENT real targets (`sports_live_availability_and_source_latency_2026_07_24.md`,
    `issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md`,
    `plans/archive/issues/instruments_service_codex_compliance_ceiling_drift_2026_07_20.md`) into an overly-broad
    "`sports_consolidated_closeout_aggregated_sources_2026_07_24.md` (6 of the 12 todos)" bucket. The parent's own
    per-todo Source citations carry
    `(corrected 2026-07-25 plan-reconcile — the digest cited here as Source has 0 checkboxes...)` notes explaining
    exactly this: several todos originally cited the aggregated_sources DIGEST (a read-only summary rollup with no live
    checkboxes of its own) and were later corrected to point at the real dispatch/reconciliation target. The
    ground-truth-derived list of 8 distinct docs behind the 12 done todos:
    `issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`,
    `issues/sports_odds_team_name_alias_gap_south_america_2026_07_09.md`,
    `sports_live_availability_and_source_latency_2026_07_24.md` (real target for the source_data_latency re-pin — NOT
    the digest), `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`'s digest pointed at 2 REAL docs for its
    3 covered todos — `issues/sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14.md`
    (features-bucket SSOT + odds_api_team_mapping coverage, 2 todos) and
    `issues/dp_catalog_not_running_sports_prediction_2026_07_15.md` (IAM grant, 1 todo) —,
    `issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md`,
    `plans/archive/issues/instruments_service_codex_compliance_ceiling_drift_2026_07_20.md`,
    `data_completion_sports_2026_07_24.md`, `issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` (2 todos) —
    exactly 8 distinct docs, confirming this todo's own "8 distinct source docs" COUNT was right even though its
    NAMES/attribution were stale.
  - **Gate-vs-reality mismatch found (same class as the cefi batch1 finalize precedent, 2026-07-30).** Parent todo 4
    ("Determine the disposition of ... 20,785 `venue=KALSHI`/`empty_confirmed`/`row_count=0` rows", Source:
    `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`) is still genuinely `- [ ]` — the ONLY
    one of the parent's 12 todos not done, despite this finalize plan being machine-gated
    (`depends_on`+`gate_on_depends: true`) on all 12 being done before dispatch. The dispatcher queued this finalize
    todo anyway. Did NOT touch that source doc (nothing to flip — no work shipped for that todo). This blocks the
    parent's archival (todo 4 of this plan) until resolved, same as the cefi precedent.
  - **Doc-by-doc outcome of the 8 real source docs**: **3 needed an actual edit** —
    `issues/sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14.md` (flipped both its remaining P3
    todos: features-bucket path SSOT — verified `/codex/02-data/sports-features-bucket-path-layout.md` exists and is
    registered in `sports_consolidated_closeout_2026_07_19.md`'s Codex SSOTs list; odds_api_team_mapping coverage gap —
    verified `instruments-service@dd3ecff1` is a real ancestor of current HEAD), and
    `issues/dp_catalog_not_running_sports_prediction_2026_07_15.md` (flipped the IAM-grant P3 todo, verified
    `deployment-service@48d5e0d` is a real ancestor of current HEAD, actually adds
    `terraform/gcp/live_event_log/events_bucket_iam.tf` — batch3's own todo 8 text only cited a placeholder
    "`<see plan flip commit>`" SHA, so this required an independent `git log` lookup rather than trusting the plan text;
    this doc reached genuinely 0 open todos as a result — checkbox AND prose both confirm, per its own 2026-07-30 update
    naming this as the sole remaining item — so its `status` was flipped `open` → `resolved` with `resolved_by`
    extended). `data_completion_sports_2026_07_24.md` got a prose annotation (not a checkbox — the "Enumeration grain
    inconsistency" line is a finding bullet, not a `- [ ]` todo) citing the investigation outcome + the filed follow-up
    `issues/sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md` (verified to exist). **5 docs
    needed no edit** — already correctly reconciled: `sports_fixtures_schedule_wrong_schema_day _2026_04_14.md` (all 4
    todos were checked before batch3 ran; batch3 only appended a bounded re-verification section; `status: open`
    correctly stays open due to a genuine remaining prose gap — 35 leagues with no canonical registry match, pending an
    operator league-registration decision), `issues/sports_odds_team_name_alias_gap _south_america_2026_07_09.md`
    (already independently reconciled + archived 2026-07-29 by a LATER session, citing the exact same
    `unified-api-contracts@96d15ba7` commit), `sports_live_availability_and_source_latency_2026_07_24 .md` (self-flipped
    at dispatch time — its own DATA P2 todo already `[x]`),
    `issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md` (self-flipped at dispatch time with
    matching evidence — `instruments-service@3e08f7d2`; its own `status: open` correctly persists due to a separate,
    still-open P2 structural-gap follow-up out of batch3's scope), and
    `plans/archive/issues/instruments_service_codex_compliance_ceiling_drift_2026_07_20.md` (already `status: resolved`
    with `resolved_by` populated — confirmed by batch3's own todo 9 text: "no further doc edit was needed"; a LATER,
    more complete SHA than batch3's own citation already closed it).
    `issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` (both its todos were self-flipped directly in the
    same doc at dispatch time — the §4.5 self-correction explicitly done "in this same-turn archive-table-flip/
    plan-flip commit", and the error_reason census's fix write-up already lives in its own "§2.5 Update 2026-07-27"
    section; doc already `status: resolved`).
  - No commits shipped in any service repo — this todo is doc-reconciliation only, entirely within `unified-trading-pm`.
