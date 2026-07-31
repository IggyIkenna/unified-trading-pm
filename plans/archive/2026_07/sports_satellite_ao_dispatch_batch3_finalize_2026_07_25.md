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
status: complete
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-3, satellite-docs, archival]
related:
  [
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-31"
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

> **🟢 ARCHIVED 2026-07-31 — COMPLETE.** All 4 todos done; the gated parent
> `/plans/archive/2026_07/sports_satellite_ao_dispatch_batch3_2026_07_25.md` is archived alongside this doc in the same
> commit. Was machine-gated on the parent (`depends_on` + `gate_on_depends: true`) until all 12 of its tasks were
> `done`; `sequential: true` enforced todo 2 (source-doc archival) after todo 1, todo 3 (conflict-gated re-check) after
> todo 1, and todo 4 (this doc's own archival) last of all.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 (slot-11, `review`).** Reconciled all 8 distinct source docs against the
      parent's actual current `Source:` citations (ground-truth-derived from the 12 todos directly, not this todo's own
      pre-written doc list — see Progress Log for why 2 of them needed correcting). Found the SAME gate-vs-reality
      mismatch class as the cefi batch1 finalize precedent: parent todo 4 (KALSHI-row disposition) is genuinely `- [ ]`
      still, the only one of the parent's 12 todos not done, despite this finalize plan being machine-gated on all 12
      being done. Its source doc was left untouched (nothing shipped to flip). Of the 8 real source docs behind the
      other 11 done todos: 3 genuinely-open items were found and flipped with independently-verified commit citations (2
      in `issues/sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14.md`, 1 IAM-grant item in
      `/plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md` — which reached 0 open todos and
      was flipped to `status: resolved`); 1 prose-form finding (not a checkbox) in
      `data_completion_sports_2026_07_24.md` was annotated with its investigation outcome + the filed follow-up issue
      doc; the remaining 5 docs were already correctly reconciled by earlier or later independent sessions (self-flipped
      at dispatch time, or reconciled by a later pass) — re-editing them would have been redundant churn. **Reconcile
      all 8 distinct source docs' checkboxes.** For each of `sports_satellite_ao_dispatch_batch3_2026_07_25.md`'s 12
      now-done todos: flip the corresponding checkbox/ section in its named source doc (each todo's text ends with
      "Source: `<doc>.md`"), citing the batch-3 commit(s) that shipped it — verify the actual shipped commit exists
      before citing it. The 8 source docs: `issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`,
      `issues/sports_odds_team_name_alias_gap_south_america_2026_07_09.md`,
      `sports_consolidated_closeout_aggregated_sources_2026_07_24.md` (6 of the 12 todos),
      `data_completion_sports_2026_07_24.md`, `issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` (2
      todos). For each: after flipping, re-check whether it now has 0 open todos remaining (unlikely for most — batch3
      was a small conflict-cleared slice of each doc's real remaining work). Only flip a doc's `status` to `resolved` if
      it genuinely reaches 0 open todos (checkbox AND prose-form — do not trust checkbox count alone). **Done when**:
      all 8 source docs' corresponding checkboxes/sections are flipped with verified evidence, and any doc that
      genuinely reaches 0 open todos is flipped to `status: resolved`.
- [x] ✅ [DOC] P1. **DONE 2026-07-31.** Re-checked all 8 source docs' physical location + status against todo 1's own
      doc-by-doc log: 5 needed no action (already correctly `open` and never archived, or already archived by an
      earlier/later independent session); 1
      (`plans/archive/issues/instruments_service_codex_compliance_ceiling_drift_2026_07_20.md`) was already archived;
      only `issues/dp_catalog_not_running_sports_prediction_2026_07_15.md` was genuinely `status: resolved` with 0 open
      todos (re-verified: all 6 checkboxes `[x]`) while still sitting under `plans/active/issues/` — archived it to
      `plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md` with a `🟢 ARCHIVED` banner, fixed
      its 8 corpus-wide path referrers (`unified-trading-pm@5fb83f4ea`), and ran a codex-alignment check per the
      ritual's step 3 — `/codex/02-data/instruments-foundation-and-catalogue-completeness.md` was stale on 2 shipped
      mechanisms this doc's own todos closed (sports FTP frozen-tail merge `instruments-service@24f84e86`, cefi
      dedup-aware monotonic guard `instruments-service@5c1c3ccb`), updated with both facts + `last_reviewed` bumped.
      **Adjacent finding, also fixed**: while re-verifying the 8 docs, found
      `sports_fixtures_schedule_wrong_schema_day_2026_04_14.md` had been WRONGLY archived 2026-07-25 by an earlier
      100%-checkbox-count sweep (all 4 checkboxes were done, but a genuine "35 leagues need an operator
      league-registration decision" gap existed only as prose, never a checkbox — the exact § 2 "todos not prose" trap —
      so `status: open` correctly never flipped, but the doc sat un-bannered in `plans/archive/issues/` anyway,
      invisible to `regen_backlog_from_plan.py` which only reads `plans/active/*.md`). Added the missing
      `- [ ] [OPERATOR] P3` todo, restored the doc to `plans/active/issues/`, and fixed its 8 corpus referrers too (2
      more `related:` frontmatter entries + 2 more prose citations were stale pointing at the doc's pre-restoration
      archive path, found and fixed in the same pass: `sports_consolidated_closeout_2026_07_19.md`'s "spun off" note,
      and a THIRD, separate stale reference in the same file to an unrelated already-archived doc,
      `sports_fixtures_schedule_noncanonical_raw_league_id_folders_2026_07_24.md`). **Hygiene-sweep caveat**: this
      todo's original done-when cites `run_hygiene_sweep.sh --ci` reporting 0 hard failures — it does NOT (2 hard
      failures: `check_reference_paths` 187/919 vs baseline 161/901, `check_archive_candidates` 7 vs baseline 4).
      Verified via `git stash` that BOTH counts were already over baseline on the clean tree before any edit this
      session made, and confirmed via grep that none of the violating files were touched this session — pre-existing
      corpus drift from other slots' concurrent work, not a regression this todo introduced. Logged the live numbers in
      `issues/reference_path_convention_2026_07_23.md`'s Progress Log rather than silently claiming a clean sweep; not
      fixed here (corpus-wide, unrelated docs, well outside this todo's scope). No source doc this plan drives to a
      terminal status remains under `plans/active/` (the one true positive is archived); every corpus referrer this todo
      is responsible for resolves to its correct current path. Source:
      `archive/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md` § 2.
- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 (slot-8, `review` craft).** Resolved the conflict-gated Deferred section from
      batch3's own doc — see Progress Log for full per-item disposition + citations. Summary: of the 6 docs / 7
      candidates, 3 (footystats, fixtures_manifest_legacy_backfill, sports_odds_stale_fixture_reinjection) were already
      confirmed dispatched + shipped in `sports_satellite_ao_dispatch_batch4_2026_07_25.md` (real commits cited there);
      the remaining 4 (both `data_completion_sports_2026_07_24.md` items, the legacy-fixtures census, the phantom-audit
      spot-check) had all been operator-ruled (entries #5-8, all `resolved`) but 2 were never actually converted into
      tracked work despite a stale `[DECISION] P2` claim in batch4 that they had been — now genuinely closed out. The 2
      `doc_too_large_or_risky_for_batch` docs' recommendation was already answered and executed:
      `sports_satellite_ao_dispatch_batch8_2026_07_30.md` ran the dedicated triage/design pass (part 1 of 3).
- [x] ✅ [DOC] P1. **DONE 2026-07-31.** Archived `sports_satellite_ao_dispatch_batch3_2026_07_25.md` via the standard
      6-step ritual. **Blocking prerequisite found + resolved first**: the parent plan's own todo 4 (KALSHI-row
      disposition, `market-data-tick-sports-prd`'s 20,785 `venue=KALSHI`/`empty_confirmed` rows) was still genuinely
      `- [ ]` despite this finalize plan being machine-gated on all 12 parent todos being done — the SAME
      gate-vs-reality mismatch todo 1 already flagged for its own scope. Investigated via a read-only sub-agent:
      classified as (b) a dormant legacy artifact (live-remeasured, zero drift, single 80s write-touch from an unrelated
      2026-07-13 reason-taxonomy rebuild, not a live reasserting bug), no remediation warranted — see
      `unified-trading-pm@7f3ae6104` (also answers the identical open todo 15 in
      `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`). Parent's 12/12 todos now done.
      Deferred section: confirmed todo 3 above already resolved all 6 docs/7 candidates — none remain, added a closing
      annotation to the parent's own Deferred section pointing at that resolution. Archive banner added. Codex-alignment
      check: `/codex/02-data/sports-features-bucket-path-layout.md` (the doc's real name — the `-ssot.md` name in this
      todo's own text was never accurate) already verified registered in `sports_consolidated_closeout_2026_07_19.md`'s
      Codex SSOTs list (confirmed independently by todo 1 above and re-confirmed here) — no further cross-referencing
      needed. Fixed all 9 other corpus-wide full-path referrers of the parent plan's pre-archive path (both active and
      already-archived citing docs — the existence checker scans body prose too, not just `related:`) to point at its
      new archive location; left bare-filename prose mentions (no path prefix) as historical narrative, since those are
      outside `check_reference_paths.py`'s scope either way. `locked_by` confirmed empty on both docs. Moved
      `sports_satellite_ao_dispatch_batch3_2026_07_25.md` → `plans/archive/2026_07/` and this finalize doc alongside it,
      same commit.

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
    `/plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md` (IAM grant, 1 todo) —,
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
    `/plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md` (flipped the IAM-grant P3 todo,
    verified `deployment-service@48d5e0d` is a real ancestor of current HEAD, actually adds
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

- **2026-07-30 (slot-8, `review` craft) — todo 3 resolved: the 6 conflict-gated docs / 7 candidates from batch3's own
  Deferred section.**
  - **3 of 7 already cleared and shipped, confirmed not re-work**: batch3's own re-check note (in this doc's source
    plan) already recorded that footystats (`issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md`),
    `issues/fixtures_manifest_legacy_backfill_2026_07_24.md`, and
    `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md` cleared on re-check and became dispatchable todos in
    `sports_satellite_ao_dispatch_batch4_2026_07_25.md`. Independently re-verified this is true and shipped: all 3 are
    checked `[x]` in that plan with real commits (`instruments-service@ca8bd7b3ab` for the fixtures-manifest legacy
    enumerator-map fix, `market-tick-data-service@76ca401f` for the odds-horizon-bucket zombie sweep, plus a same-batch
    footystats reconciliation done 2026-07-26). No further action needed on these 3.
  - **Remaining 4 — operator-ruled but 2 never actually converted into tracked work (real gap found).** All 4 map to
    `autonomous_session_operator_decisions_2026_07_25.md` entries #5-8, all `Status: resolved`. But batch4's own
    `[DECISION] P2 Retagged 2026-07-29` checkbox claimed all 4 were resolved-by-reference via entries #5-8 PLUS
    `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s "wider-corpus re-audit" — checking batch5 directly showed this
    over-claimed: batch5's `data_completion_sports_2026_07_24.md` section discusses two DIFFERENT candidates (a
    rate-limit calibration probe + an API-Football quota bump), never the Transfermarkt re-attempt / ODDS+PREDICTIONS
    blank-reason items batch3/4 actually deferred. Flagged + corrected batch4's checkbox in the same pass (addendum
    added, not un-checked — the retag's core citation to entries #5-8 was right, only the batch5-covers-everything claim
    was wrong).
    1. **Transfermarkt PLAYER_VALUES re-attempt (256 cells)** [entry #5, resolved — dispatch as originally scoped]: was
       prose only ("Remaining unaddressed gaps (follow-on todos)") in `data_completion_sports_2026_07_24.md`, never a
       tracked checkbox — violates CLAUDE.md's "every follow-up is a `- [ ]` todo, never prose" rule on its own terms.
       Added a new `- [ ] [DATA] P2` todo in that doc citing entry #5's ruling.
    2. **ODDS+PREDICTIONS blank-reason golden-window measurement** [entry #6, resolved — dispatch the measure-and-file
       as scoped]: same prose-only gap. Added a new `- [ ] [DATA] P2` todo in the same doc citing entry #6.
    3. **`sports_legacy_fixtures_path_migration_2026_07_24.md` fixtures-path census** [entry #7, resolved — dispatch
       as-is, the scope-correction the conflict required was already present in the todo's own Done-when]: the census
       already exists as this doc's own P0 todo (not prose) — no new todo needed, only confirmation the conflict (Track
       S/E/C1) is cleared. Added that confirmation directly under the census todo. Found + closed an unrelated loose end
       while there: the doc's most recent Progress Log entry (a 2026-07-30 na-eligibility-audit park) ended mid-sentence
       ("parked with a recommendation" — nothing after); completed it factually (`sequential: true` + operator
       AO-authorization is the actual parked recommendation, consistent with the rest of that entry's own reasoning)
       rather than leaving a dangling sentence.
    4. **`issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md` STANDINGS/TEAMS spot-check** [entry #8,
       resolved — merge into Track S2's "decision 16" investigation as a corroborating data point, NOT a separate
       classification pass]: `sports_satellite_ao_dispatch_batch7_2026_07_27.md` had already dispatched decision 16's
       day-partition root-cause `[DIAG] P2` todo (2026-07-27), but its text never actually named the fold-in the
       operator ruled for. Amended that todo to explicitly require checking the phantom residual as a corroborating data
       point and to state in its Done-when whether the two share a root cause. **Second, freshly-introduced collision
       found and fixed in the same pass**: a same-day (2026-07-30), unrelated na-eligibility-audit session had
       reclassified this doc's own spot-check checkbox to `assigned_vm: planning` with a "Conflict-check CLEAR" note —
       but that check only grepped batch5 by name and missed this exact, already-resolved operator ruling, so as written
       the doc's own checkbox and batch7's amended todo would have raced as two independent AO dispatch targets
       investigating the same ground. Corrected in place: the doc's own checkbox now explicitly says "DO NOT
       dispatch/investigate this item independently", points at batch7's todo as the actual execution vehicle, and the
       na-eligibility-audit's Progress Log note got a dated correction rather than being silently overwritten.
  - **Large/risky docs recommendation**: already answered and executed — no new recommendation needed.
    `sports_satellite_ao_dispatch_batch8_2026_07_30.md` (`status: active`) is exactly the dedicated triage/design pass
    this todo asked whether to recommend, already run for
    `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` (0 new AO-eligible candidates,
    confirmed fresh) and part 1 of 3 of `issues/sports_features_layer_findings_sweep_2026_07_18.md` (5 candidates
    extracted + 3 reconciled). Confirmed via direct read, not just citation.
  - **Files touched (all `unified-trading-pm`, doc-only, no service-repo commits)**: this plan (todo 3 flip + this Log
    entry), `data_completion_sports_2026_07_24.md` (2 new todos), `sports_legacy_fixtures_path_migration_2026_07_24.md`
    (conflict-clear note + completed dangling sentence), `sports_satellite_ao_dispatch_batch7_2026_07_27.md`
    (decision-16 todo amended), `issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md`
    (do-not-dispatch-independently note + na-eligibility-audit correction),
    `sports_satellite_ao_dispatch_batch4_2026_07_25.md` (addendum on the `[DECISION] P2` over-claim),
    `sports_satellite_ao_dispatch_batch4_finalize_2026_07_25.md` (its own identical todo 3 flipped done, same evidence —
    avoids a future duplicate pass re-doing this exact reconciliation).
