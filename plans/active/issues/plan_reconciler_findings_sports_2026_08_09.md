---
doc_type: issue
title: "plan_reconciler daily deep reconciliation run — sports tranche, 2026-08-09"
summary: >-
  Run-findings doc for plan_reconciler dispatch agt-196785 (slot 4, 2026-08-09), tranche=sports. Corpus: 87
  asset_group:sports-tagged docs in plans/active + plans/active/issues (~3.3MB); 18 (21%) are in the 12h grace window
  and read-only this run, leaving 69 non-grace docs as the actionable set, plus the normative refs (PLAN_FORMAT.md /
  task_template.md / INDEX.md / ACTIVE_INDEX.md) and codex which stay in scope for every shard per
  cursor-configs/skills/plan-reconcile/SKILL.md.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, scheduled, sports]
related: []
created: "2026-08-09"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: review
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by: plan_reconciler
locked_since: "2026-08-09"
supersedes:
superseded_by:
resolved_by:
source: "slot 4, plan_reconciler agt-196785, 2026-08-09"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
    unified-trading-pm/plans/epics/sports_master.md,
  ]
drift_direction: advance-code
depends_on: []
---

# plan_reconciler run — 2026-08-09 (agt-196785, tranche=sports)

## Scope + method

- `TRANCHE=sports` supplied → this run audits ONLY `asset_group: sports`-tagged docs (87 docs, ~3.3MB) + normative refs
  - codex, per `cursor-configs/skills/plan-reconcile/SKILL.md` § "Topic-scoped (sharded) runs". A sibling wave of
    workers on other slots covers the other 9 tranches today; cross-tranche contradictions are out of this shard's reach
    by design (caught only by the weekly `all` run).
- **Naming deviation (noted for the operator):** `agents/plan_reconciler.md` STEP 2b specifies the findings-doc path as
  `plan_reconciler_findings_<TODAY>.md` with no tranche component — but today is a sharded multi-tranche day (per
  SKILL.md's Sun-Fri per-tranche cadence), so multiple sibling slots running concurrently would collide on that exact
  filename. This doc uses `plan_reconciler_findings_sports_2026_08_09.md` (tranche-qualified) instead, consistent with
  how other tranche-scoped skills name their outputs (e.g. `sports_satellite_ao_dispatch_batchN_<date>.md`). Filed as a
  hygiene finding below (see `## Filed`) — the boot-prompt SSOT should adopt this convention explicitly.
- Grace set (newest commit <12h old at run start, `date +%s`=1786244451 / 2026-08-09 03:00:51 UTC): 18 of 87 sports docs
  (21%). Read-only context this run.
- Non-grace actionable set: 69 sports docs, spanning `parent_epic: sports_master` (55 docs, most numerous),
  `infrastructure_master` (17), `instruments_master` (7), `agent_operating_framework_master` (3), `manifest_master` (2),
  `predictions_master` (1), `observability_master` (1), `mtds_mdps_master` (1) — note some docs carry >1 asset_group tag
  so epic-membership counts overlap the 87 total.

## Flips verified

1. **`sports_taxonomy_p2_migration_2026_08_08_finalize.md` todo 5** ("Correct the historical record in
   `sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md`") — flipped `[x]`. The target doc already
   carried a prominent `⚠️ CORRECTION 2026-08-08` banner (added before this finalize plan was even authored); fixed the
   doc's own "Deferred work" section, which still asserted the pre-correction "fully resolved... 0/0/0/0 non-canonical"
   claim uncaveated below the banner. unified-trading-pm@a14406bc5.

## Contradictions (resolved — same-doc self-contradictions, evidence-backed per SKILL.md's AUTO-RESOLVE calibration)

1. `sports_consolidated_native_ao_extract_2026_07_25.md:77` — body banner said "Status: draft" against a frontmatter
   `status: active` + 33/33-done doc. unified-trading-pm@37674d6fc.
2. `sports_closeout_track_x_hygiene_2026_07_25.md:63` — same pattern (4/5 done). unified-trading-pm@37674d6fc.
3. `data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md:57` — same pattern.
   unified-trading-pm@c9f9b208b.
4. `sports_predictions_live_mode_activation_readiness_2026_07_21.md:86-102` — stale "hard BLOCKER" banner re: the
   cross-AG prediction-bleed bug; `sports_consolidated_closeout_2026_07_19.md` Track C shows it closed 2026-08-07 (0
   bleed rows holding 11 days). unified-trading-pm@c9f9b208b.
5. `sports_predictions_live_mode_activation_readiness_2026_07_21.md:218-261` — Todo 2 marked `[x]` but its own text said
   "Checkbox NOT flipped"/"Leaving checkbox open" twice, and the doc's own 2026-08-07 na-eligibility-audit entry
   explicitly asked the next sports-tranche pass to re-verify a live poll cycle. **Independently re-verified live**:
   `mtds-live-sports-odds-api-trades-20260804-131449` VM RUNNING, `run.log` (33,060 lines, 2026-08-04→08-09) has zero
   ERROR/401/OUT_OF_USAGE_CREDITS entries, live manifest writes firing every ~60s as of the check. Done-when met,
   checkbox correctly stays `[x]`. unified-trading-pm@c9f9b208b.
6. `data_pipeline_check_mdps_features_2026_07_20.md:772` — "Do NOT launch CEFI without operator go-ahead" was stale;
   doc's own Progress Log (2026-08-02 `BLK-ddb925b1`, reconfirmed 08-05) shows CEFI's gate cleared.
   unified-trading-pm@463755102.
7. `mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md:199-201` — audit note claimed a retry "not tracked
   as a todo" while the todo sat 2 lines above it. unified-trading-pm@984b38808.
8. `sports_satellite_ao_dispatch_batch10_2026_08_06_finalize.md:93-95` — Progress Log falsely claimed a codex path "does
   not resolve" while quoting the identical (real, `ls`-verified) path on both sides. unified-trading-pm@984b38808.
9. `canonical_player_stats_fixture_events_quality_2026_07_16.md:208-212` — a `[x]` todo's "decide + execute" framing
   conflated a done half (decision + script shipped) with a still-open half (the prod `--apply-prod` pass, tracked
   separately in Follow-ups); annotated per the half-done-item rule. unified-trading-pm@984b38808.
10. **D8 vs D9 cross-plan conflict** (`sports_satellite_ao_dispatch_batch10_2026_08_06_finalize.md` todo 2 vs
    `sports_taxonomy_p2_migration_2026_08_08_finalize.md` todo 5) over
    `sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md`'s disposition — see Flips verified #1;
    resolved at the source by fixing the target doc's internal inconsistency rather than either finalize plan.
    unified-trading-pm@a14406bc5.

## Doc-drift (confirmed, NOT auto-fixed — plans→codex edits are never autonomous)

1. `codex/02-data/sports-2020-06-data-floor.md:127-131` says decision-14 is "still open" —
   `sports_consolidated_closeout_2026_07_19.md:801-815` shows it DONE 2026-07-27 (`instruments-service@05c6a75f`). Codex
   `last_reviewed: 2026-08-08` postdates the fix by 12 days, missed during that review.
2. `codex/02-data/non-canonical-path-inventory.md` entry 16 ("VERIFIED 2026-07-20", flat-shape claim) is contradicted by
   `backfill_smoke_write_path_canonical_audit_finalize_2026_08_08.md:81-88`'s proof the writer was hive-canonicalized
   2026-07-22 — 2 days after the codex entry's stated verification.
3. `sports-data-types-catalog.md`'s Venue Axis list (32 members, several wrong names) is stale vs the live 31-member
   registry — already independently tracked by `sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`'s own open P2
   todo (`:540-555`); this run just corroborates it independently, no new filing needed.
4. `sports_odds_feature_naming_canonicalization_2026_07_21.md:441` / `:210-214` — TWO separate instances of the same
   pattern: a "Codex SSOT updates"/"Codex SSOTs" section promises a **new** codex doc
   (`sports-canonical-league-cup-registry.md`, `codex/09-strategy/architecture-v2/archetypes/...`) that was never
   created, and the promise itself was never converted to a tracked todo. For the league/cup registry doc, the
   underlying content (`LEAGUE_REGISTRY`) may have landed inside the EXISTING `sports-data-source-coverage-matrix.md`
   instead — not independently confirmed this pass. **Recurring pattern worth naming**: this corpus's "Codex SSOT
   updates" sections are a structural blind spot — nothing mechanically checks whether a promised new codex doc actually
   got written.

## Hygiene fixes

1. Repointed 5 dangling refs in `sports_predictions_live_mode_activation_readiness_2026_07_21.md` (`related:` +
   `context_scope` + 3 body mentions) from
   `/plans/active/issues/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md` (moved) to
   `/plans/archive/2026_08/...`. unified-trading-pm@c9f9b208b.
2. Fixed 7 non-canonical todo-format violations (numbered/lettered sub-item prefixes and one em-dash-after-priority)
   across 5 files, mechanically flagged by `check_todo_format.sh` but outside the auto-fixer's coverage.
   unified-trading-pm@42dfe897b.
3. Converted `mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md` (assigned_vm:planning, P1, zero
   checkboxes) to carry a real tracked todo for its 2 prose-only remediation options. unified-trading-pm@544386c53.
4. Normalized `locked_by: ""` → blank on the archived `sports_index_recency_masked_captured_atoms_2026_07_13.md` (a
   verified false-positive lock — see Filed #12). unified-trading-pm@2e481b26b.

## Filed

**Alerted (Phase 5.9(a) reconciliation)**: `BLK-43da7ab8` — batched blocked-question covering Filed items #2, #3, #6
below (the 2 big findings + the zero-checkbox `assigned_vm` preference call), `recommendation: A`, `can_continue: true`.
`routed_to_operator` (3: items #2/#3/#6) `== parked` (1 blocked-question ID covering all 3, `[unresolved]` pending
operator answer) — reconciled.

1. **Findings-doc naming collision risk on sharded multi-tranche days** — `agents/plan_reconciler.md` STEP 2b's
   `plan_reconciler_findings_<TODAY>.md` path has no tranche component; every sibling slot running today would target
   the identical filename. Recommend `plan_reconciler_findings_<tranche-or-all>_<TODAY>.md`. Outside `plans/**` write
   scope.
2. **BIG FINDING — `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` (P0)**: this doc's own self-identified
   next-checkpoint (2026-08-08 t1h triggers) has passed with zero follow-up Progress Log entry as of 2026-08-09. Also
   1017L, over the 1000L hard line-cap — a split finding (operator-gated). Also contains a todo (`:573-575`) marked
   "AO-dispatchable" that embeds a `BLOCKED-OPERATOR-DECISION` marker which IS in `_NON_DISPATCHABLE_RE`'s recognized
   alternation (confirmed via `blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md:13`) — this todo
   will silently never dispatch despite its own claim. Needs operator attention on 2 fronts (stale checkpoint +
   self-defeating dispatch tag) plus a plan split.
3. **BIG FINDING — `sports_satellite_ao_dispatch_batch9_2026_08_04.md`**: the entire 84-item Deferred section (~lines
   408-802) has every bullet's justification cut off mid-sentence with an identical bracketed truncation tag ("[citation
   truncated — ...re-verified in batch10 Progress Log (2026-08-06)]"). This doc's own reasoning for all 84 deferred
   classifications is not independently verifiable from the doc alone, on a `status: active`, operator-approved P2 plan.
   The "re-verified in batch10" claim was not independently confirmed this pass. Also: no finalize-sibling doc found for
   batch9 (or batch11) — `task_template.md` §4 requires one per AO-dispatched plan; confirmed batch10 has one, could not
   locate batch9's or batch11's.
4. **`sports_track_h_denominator_gated_2026_07_28.md`** — its founding premise ("`gate_on_depends` converts the
   prose-block into a real DISPATCH gate") is contradicted by
   `sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md:249-250`'s later, explicit finding that `gate_on_depends`
   gates ARCHIVAL, not dispatch. Not independently verified this pass whether Track H's single P0 todo has since been
   prematurely dispatched against unmet prerequisites — needs a live backlog/dispatch-history check.
5. **Same-tag+priority collision bug** (known class, `task_template.md` 2026-07-31 finding, previously caused a real
   `/done` REJECTION): `sports_closeout_track_s2_foldin_2026_07_25_finalize.md` todos 1+2 both `[REVIEW] P1`;
   `sports_taxonomy_p4_backfill_2026_08_08_finalize.md` todos 1-3 all `[REVIEW] P1`, todos 4-5 both `[REVIEW] P2`. Needs
   the documented fix pattern applied (differentiate tags/priorities); not applied this pass (needs `task_template.md`'s
   exact prescribed remedy read first).
6. **Zero-checkbox doc needing an `assigned_vm` ruling**:
   `sports_api_football_live_odds_second_source_conflicts_with_wipe_ruling_2026_08_02.md` — `assigned_vm: planning`,
   zero checkboxes, pure operator-decision prose, 7+ days open with no ruling recorded. This is itself a
   preference/authority call (whether to reclassify to `NA`), not evidence-resolvable — routed as a question, not
   auto-fixed.
7. **Unowned prose follow-ups (HARD RULE: every follow-up is a todo, never prose)**:
   `sports_af_full_entity_completion_2026_08_03.md:171-175` (stale
   `SPORTS_ENTITY_LEAGUE_COVERAGE`/`SPORTS_ENTITY_START_DATES` registry entries "actively mislead any future census") —
   not converted this pass, needs a todo.
8. **Stale/cosmetic items not reached this pass** (lower priority, noted for a future sweep): malformed blockquote
   parenthetical in `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md:48-54`; 3 stale
   cross-reference counts in `sports_consolidated_closeout_2026_07_19.md` (`:826-836` "~9-11 open" → actually 1,
   triple-confirmed; `:556-558` Track C still describes the retired exchange_fixed_odds_fork prescriptively; `:142-148`
   split-notice off-by-one) — **skipped**: this doc is exactly at its 1000L hard cap, and a net-positive edit would
   breach it; needs a compaction pass first. Severe leading-whitespace formatting defect in
   `estate_orphan_assessment_2026_07_21.md:144-317` (~400+ leading chars/line, ~174 lines, breaks markdown rendering,
   content unaffected). 2 stray-space broken filename refs in
   `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md:121,386`. Checkbox-less bullet
   (`sports_odds_feature_naming_canonicalization_2026_07_21.md:197-204`) not normalized to match corpus
   `[x]`-with-annotation convention.
9. **Archived-doc findings** (out of this skill's edit scope — "archive is out of audit scope but valid evidence"):
   `plans/archive/2026_07/sports_odds_exchange_fixed_fork_2026_07_18.md` has 10 open P0-P2 todos for a design later
   retired by operator ruling (2026-08-08), never reconciled against the retirement.
   `plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md` has 5 open todos (2 `BLOCKED-*`-tagged), no
   trace in either successor doc.
10. **Cross-tranche finding, out of write scope** (another sibling slot owns the `ci` tranche today):
    `plans/active/issues/ag_closeout_audit_ci_parked_2026_08_08.md:61,198` has a stale literal-path reference to
    `ag_closeout_audit_sports_tooling_followups_2026_08_06.md`, which moved to `plans/archive/2026_08/issues/`.
    `plans/active/INDEX.md` (auto-generated) is also stale after the same move — fix is regenerating the index, not a
    hand-edit.
11. **Locked docs needing operator attention**: `instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md`
    — `locked_since: 2026-05-21` predates `created: "2026-07-30"` by 2+ months (internally impossible for a genuine
    lock), blocking a valid archival of a properly-superseded doc.
    `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` — `locked_by: live-defi-rollout`, 46+
    days stale, flagged as a likely tooling anomaly by 2 prior na-eligibility-audit passes (07-29, 08-07), never fixed.
    Both moot right now (neither doc is otherwise archive-ready), but the corpus-wide `locked_by: live-defi-rollout`
    pattern (62 docs corpus-wide, confirmed via grep, not sports-specific) looks systemic — worth a single consolidated
    operator ruling on what that value is supposed to mean rather than N per-doc fixes.
12. **SCRIPT BUG (outside `plans/**`, filed not fixed)**: `scripts/hooks/check-locked-plan-deletion.sh:57` extracts
    `locked_by:`'s raw YAML text via `grep -oP` then does a naive bash `[[ -n "$LOCKED_BY" ]]` truthiness check — this
    treats the literal 2-character YAML empty-string `""` as a non-empty/truthy lock, false-blocking archival of any doc
    using that convention (vs. the corpus's more common bare `locked_by:` null, which correctly reads empty). Reproduced
    directly this run (blocked `sports_index_recency_masked_captured_atoms_2026_07_13.md`'s legitimate archival).
    Suggested fix: also treat the literal strings `'""'` and `"''"` as empty.

## Archive candidates (operator review)

1. **`sports_index_recency_masked_captured_atoms_2026_07_13.md`** — archived: true (see Hygiene fixes / Flips). All 7
   todos HARD-evidenced, unlocked (after script-bug workaround), not grace. `plans/archive/2026_08/issues/`.
2. **`sports_consolidated_native_ao_extract_2026_07_25.md`** — archived: false, locked: false. Triple-confirmed 33/33
   done, unlocked — but its own companion `sports_consolidated_native_ao_extract_2026_07_25_finalize.md`
   (`gate_on_depends: true`) is the designated archival vehicle (its own todo 4 runs the ritual once the parent hits
   0-open, which it now does). Not archived directly by this run — banner corrected only (see Contradictions #1); the
   finalize plan's gate is now satisfiable for the next dispatch.

## Refuted (dropped by verify)

1. The apparent contradiction about whether `sports_odds_feature_naming_canonicalization_2026_07_21.md`'s 3-repo naming
   migration is "unstarted" (per `sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` and
   `sports_satellite_ao_dispatch_batch10_2026_08_06.md`, both dated 2026-08-06) is **self-resolved by the corpus's own
   newer doc**: `sports_satellite_ao_dispatch_batch11_2026_08_09.md` (2026-08-09) explicitly calls batch10's "unstarted"
   premise stale, and this run's own batch3 hunter independently confirmed all 8 execution todos in the canonicalization
   doc are shipped (only todo 10, a cross-ref check, and the checkbox-less todo 9 remain). No action needed — not a live
   contradiction, just two now-superseded snapshots.

## Coverage (hunters / batches / docs)

- **Corpus**: 87 `asset_group: sports`-tagged docs in `plans/active/` + `plans/active/issues/` (~3.3MB), identified via
  frontmatter grep at run start.
- **Grace set**: 18 of 87 (21%) had commits <12h old at run start — read-only context, none written.
- **Non-grace actionable set**: 69 docs.
- **Fan-out**: 10 wave-1 read-only hunters (9 epic-cluster batches covering all 87 docs in full + 1 dedicated
  data-pipeline-milestones-drift/closeout-cross-check hunter), `model=sonnet`, `SUB_AGENT_MANDATORY_RULES.md` pasted at
  every spawn. All 87 docs read in full by exactly one hunter (verified: batch sizes summed to 87, no gaps/overlaps
  beyond the deliberate 300KB-target bin-packing). One hunter's report was truncated on first delivery
  (infra_batch/a858977705999cf38, 400,968 subagent output tokens) — recovered via `SendMessage` asking it to resend the
  missing section from its own context (no rework needed).
- **Candidates generated**: ~50 across contradictions (14), archive candidates (2), zero-checkbox docs (2), AO-dispatch-
  readiness defects (~10), codex drift (4), structural/cosmetic issues (~8), locked-doc anomalies (3), missing-
  finalize-sibling gaps (2), big findings (2).
- **Verified + applied this pass**: 10 same-doc contradictions, 1 cross-plan conflict, 1 archival, 3 hygiene-fix classes
  (dangling refs, todo-format ×7, 1 zero-checkbox conversion) — 25 commits total on the review branch.
- **Adversarial verification method**: for same-doc contradictions with a newer dated banner/entry in the SAME doc
  contradicting an older one, applied SKILL.md's explicit AUTO-RESOLVE calibration (provable from the doc's own later
  text — ran the check, cited the command/output) rather than spawning separate refuter/confirmer sub-agents for each;
  for the 2 archive candidates and the D8/D9 cross-plan conflict, verified inline against live infra (VM/log checks) and
  the actual target-doc content directly (this run is effort=max/opus-tier per its own boot contract) rather than
  fanning out a dedicated verifier wave, given the candidate count was small enough for direct inline verification.

## Plans not reached

Given the ~50-candidate volume this run's DETECT phase surfaced (see Coverage), the following confirmed-real findings
were NOT independently fixed this pass — each is captured under **Filed** above with enough detail for a future
sports-tranche pass (or an operator) to act without re-deriving:

- Doc-drift items #1-4 (codex edits — never autonomous by design, correctly routed not fixed).
- Filed #2-4 (2 big findings + Track H dispatch-history check) — need either an operator decision or a live
  backlog/dispatch-history check this pass didn't perform.
- Filed #5 (same-tag+priority collision fix) — needs `task_template.md`'s exact prescribed remedy read first, not
  applied blind.
- Filed #6-7 (assigned_vm ruling + 1 unowned-prose-to-todo conversion).
- Filed #8 (5 cosmetic/stale-count items, 1 explicitly skipped due to a hard line-cap risk on the target doc).
- Filed #9 (2 archived-doc findings — out of edit scope by design).
- Filed #10 (1 cross-tranche doc — out of this run's write scope by design, another slot owns `ci` today).
- TIER 4.4/4.5 from this run's own working queue (2 "promised codex doc never written" cases) — flagged under Doc-drift
  #4 but not independently converted to todos or verified moot this pass.
