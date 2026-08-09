---
doc_type: issue
title: "plan_reconciler daily deep reconciliation run — defi tranche, 2026-08-09"
summary: >-
  Run-findings doc for plan_reconciler dispatch agt-8af81b (slot 2, 2026-08-09), sharded to the `defi` tranche per the
  operator's 2026-08-06 sharding ruling. Corpus: 104 asset_group:defi-tagged docs (55 active/issue docs, 49 in the 12h
  grace window and read-only this run) + the defi_master epic + normative refs (PLAN_FORMAT.md / task_template.md /
  INDEX.md / ACTIVE_INDEX.md), which stay in scope for every shard. 7 parallel hunter sub-agents read all 55 non-grace
  docs in full; every candidate was independently re-verified (direct git/grep/wc re-execution, not just hunter prose)
  before any fix landed. 10 checkpoint commits applied 26 verified fixes across 21 docs; 3 findings needing operator
  authority were escalated async (BLK-0b3e403d, BLK-d59ebc8e, BLK-8b3f416d) and filed durably below.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, scheduled, defi]
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
source: "slot 2, plan_reconciler agt-8af81b, 2026-08-09"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/scripts/plan-hygiene/check_archive_candidates.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
---

# plan_reconciler run — defi tranche — 2026-08-09

Dispatch `agt-8af81b`, slot 2, tranche=defi. STEP 1: all repos FF-clean to `origin/live-defi-rollout`,
`run_hygiene_sweep.sh --ci` ran clean-exit (2 hard failures, both out-of-tranche — see Coverage). Grace set: 49/104
defi-tagged docs <12h old (read-only this run); 55 non-grace docs (~2.0MB) batched into 7 hunter batches (A-G), each
covering every doc exactly once. Every hunter finding acted on was independently re-verified by the orchestrator via
direct command re-execution (git log/show, grep, wc -l, find) — not accepted on hunter prose alone.

## Flips verified

None of this run's fixes were simple `[ ] → [x]` missed-flips with fresh HARD evidence — the hunters found none (every
open todo checked either cited no completion evidence, or was a legitimate rollup left open pending real sub-work). One
INVERSE case was found and corrected instead (see Contradictions).

## Contradictions

**Fixed this run (evidence-backed, applied to the review branch):**

1. **[P1] False-checked todo** — `issues/estate_orphan_assessment_2026_07_21.md` todo 7 was `[x]` but its own body is a
   forward-looking instruction ("Run that same pattern... copy... verify... register"), not a completion record; no
   sha/VM-launch/manifest-state evidence found anywhere in the corpus. Reverted to `[ ]`, splitting the genuinely-
   resolved escalation-question from the still-undone GCS operation. `671937a92`'s predecessor commit `2e62b1a37`.
2. **[P1] Stale umbrella todo (2 sub-findings)** — `issues/instruments_remaining_work_audit_2026_07_10.md`: (a) sole
   open todo named "6 remaining Headline P0s," 3 of which are already `status: resolved` + archived (verified live);
   narrowed to the 3 genuinely open. (b) same doc's "only ~2 of 13 todos remain" recount for the 59-bug smoketest was
   itself stale — sibling doc now has 15 todos (3 open + 1 partial). Both corrected `671937a92`.
3. **[P2] Finalize-doc status banner vs frontmatter** — 2 docs
   (`data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md`,
   `defi_pipeline_e2e_and_coverage_validation_2026_06_20_finalize_2026_07_27.md`) had a body banner claiming
   `STATUS: draft — NOT dispatched` contradicting `status: active` frontmatter. Rewritten to match the
   established-correct pattern already used by sibling finalize docs (`gate_on_depends` holds dispatch correctly either
   way — cosmetic-but-misleading, not a functional bug). `dfe8b0907`.
4. **[P2] Checked item overselling its own completion bar, no follow-up todo (HARD RULE gap)** —
   `defi_pipeline_e2e_and_coverage_validation_2026_06_20.md`'s SolidlyCL golden-swap item ticked `[x]` despite its own
   text admitting synthetic (not real on-chain) fixtures, contradicting the doc's own Success Criteria. Added the
   missing follow-up todo. `595ea3971`.
5. **[P2] Stale body bullet vs the same doc's own Todos/Progress Log** — `defi_strategy_pnl_axis_index_2026_07_24.md`
   still said "operator ruling needed" for a decision its own Todos section already recorded as ruled 2026-07-29.
   Fixed + repointed the stale reference. `595ea3971`.
6. **[P2] Finalize-doc todo-count miscount** —
   `defi_jupiter_venue_registration_and_live_connector_wireup_finalize_2026_08_07.md` said "6 todos"/"todo 6" but the
   base plan has 8 (todos 7-TEST, 8-REVIEW added after the finalize doc, never folded into its re-verify scope).
   Corrected count + scope. `595ea3971`.
7. **[P2] Stale "Recommendation" section, already self-flagged** —
   `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`'s "operator decision needed" section named 3
   decisions all made+shipped the same day the doc was authored (its own 2026-08-06 na-eligibility-audit note already
   caught this). Bannered SUPERSEDED with pointers to where each landed. `2e62b1a37`.
8. **[P2] Half-wrong audit note + untracked prose follow-up (HARD RULE gap)** —
   `coverage_floor_registries_no_cross_propagation_2026_07_17.md`'s own audit note claimed 2 follow-ups were prose-only;
   only 1 actually was. Added the missing `- [ ]` todo, corrected the note. `3baadb331`.
9. **[P2] Rescoped todo — one sub-claim already shipped, live-verified** —
   `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`'s UI-resync todo claimed
   `ui-reference-data.json` still had drift-residue; live-verified 0 hits (shipped via a sibling doc's fix,
   `unified-trading-system-ui@80bb6a9c`). The E2E fixture + generator-skew halves are still genuinely open — rescoped to
   just those. `595ea3971`.
10. **[P1, stale `[OPERATOR]` tags, CLAUDE.md HARD RULE]** — `strategy_ml_orphan_coverage_design_gaps_2026_08_03.md`: 3
    todos stayed `[OPERATOR]`-tagged and unchecked though the SAME doc's Progress Log records the operator's answer
    (BLK-75060009, 2026-08-05). Retagged: 2 fully resolved (closed), 1 decision-resolved but implementation remains
    (retagged `[CODE]`). `2e62b1a37`.
11. **[P3] Dangling ref + stale citation** — `defi_catalog_engine_config_key_contract_drift_2026_07_23.md` had a literal
    typo in a filename reference (stray space) resolving to nothing; fixed + repointed to the real archived path.
    `eec887db6`.
12. **[P2] Stale evidence citations (2 shas verified live via `git log`)** —
    `coverage_floor_registries_no_cross_propagation_2026_07_17.md`'s CME-mismatch citation said "pending sha" 15 days
    after it shipped (`32b2879c`); `over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md` had a literal
    unfilled `<sha>` placeholder (`cff285743`). Both substituted. `eec887db6`.
13. **[P1] Batch-list citing a doc that isn't actually archivable** —
    `defi_satellite_ao_dispatch_batch10_2026_08_06.md`'s own `archivable_now` list still named
    `defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md`, which has a confirmed-live unverified
    data-correctness gap (already independently caught by `ag_closeout_audit_defi_parked_2026_08_07.md` Finding 6).
    Struck from the list with a pointer. `dfe8b0907`.

**Routed to operator (evidence can't settle these — see Filed):** the line-cap carve-out boundary bug; the contested
`uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md` NA/planning verdict.

**Confirmed but NOT actioned (too minor to spend a fix-commit on, listed per the no-silent-drop rule):**

- `defi_catalog_engine_config_key_contract_drift_2026_07_23.md`: 2 internal count-mismatches ("9 checked" vs a 10-row
  table; "5 confirmed-total-block" names 6) — self-contained, no downstream impact.
- `defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`: todo 4 self-discloses its own "done when" wasn't fully met
  (finalize doc itself not archived alongside) — already self-disclosed in the same entry, not hidden.
- `defi_turbo_api_hides_real_captured_data_2026_07_07.md:305-306`: imprecise wording re: a sibling doc's "Decision Gate
  D6" — the decision itself is closed, only downstream implementation remains; doc does distinguish this elsewhere so
  unlikely to mislead in context.
- ~15-20 `../`-relative or bare-slug `related:`/`context_scope:` entries across the batch (format-only, all resolve) —
  the reference-path-format ratchet has slack (63 violations vs 81 baseline) and this volume wasn't worth individually
  hand-fixing this run; noting the population exists for a future dedicated pass.

## Doc-drift

- `agents/plan_reconciler.md` STEP 1's discard-side-effect snippet names
  `plans/active/master_to_live_defi_2026_05_23.md` as the `--ci` regen target — already archived. The live regen
  side-effect actually lands on `plans/active/INDEX.md` +
  `plans/archive/2026_07/active_plan_inventory_dashboard_2026_07_24.md` (discarded both times this run via
  `git checkout --`). Outside `plans/**`, cannot self-edit — flagging for a human/follow-up.
- `agents/plan_reconciler.md` STEP 0 and `cursor-configs/skills/plan-reconcile/SKILL.md` Phase 3 both still say "reserve
  opus for the hardest cross-batch reconciler and the tiebreaker" — superseded by CLAUDE.md's 2026-08-04/08-07 rulings
  that opus-required has no standing category left (verified: every sub-agent I spawned this run used `model=sonnet` per
  the newer rule, not the stale role-file guidance). Outside `plans/**`, cannot self-edit.
- `plans/epics/defi_master.md`'s "Assigned active plans" section claims "_7 active plans declare parent_epic:
  defi_master_"; `populate_epic_bodies_2026_05_21.py --dry-run` shows the current correct count is **16**. The
  regenerator is corpus-wide (touches every epic, not just defi_master — confirmed via dry-run), so applying it
  mid-shard risks colliding with concurrent tranche shards (observed running live during this session: slot 6=tradfi,
  slot 11=all-corpus). NOT applied this run; noting for a dedicated maintenance-window regen.
- `plans/active/INDEX.md` has 27 drift entries (defi-relevant:
  `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`, `defi_migration_audit_log_2026_07_24.md`,
  `defi_venue_lst_rates_residual_2026_07_24.md` missing from it) — same corpus-wide-regen deferral reasoning as above.
- `agents/plan_reconciler.md` STEP 7's result-POST snippet says `POST $SERVER_URL/api/plan_health/result` (underscore) —
  the real, OpenAPI-confirmed path is `/api/plan-health/result` (hyphen, matching `/api/plan-health/dispatch`'s naming).
  The underscore form 404s. Outside `plans/**`, cannot self-edit — this would block every future plan_reconciler
  dispatch's STEP 7 the same way until fixed.

## Hygiene fixes

- Reformatted 1 malformed checkbox (`mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md` — a follow-up wrapped
  inside a single backtick span including its own `- [ ]` marker, invisible to checkbox-based tooling). `3baadb331`.
- Reconciled 3 stale `model_tier: opus-required` frontmatter fields
  (`uac_data_type_validity_combinator_fragmentation_2026_07_07.md`,
  `defi_turbo_api_hides_real_captured_data_2026_07_07.md`,
  `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`) → `sonnet-doable`, per
  codex/06-coding-standards/model-tier-selection.md's 2026-08-07 ruling (verified: a Sonnet-5 worker hitting
  `opus-required` self-checks and STOPs — this would have stalled dispatch on 2 `assigned_vm:planning` docs).
  `8c9a5526c`.
- Corrected 2 `parent_epic` mismatches (`instruments_service_defi_golden_red_capability_lockstep_gap_2026_08_05.md`,
  `mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md`: `infrastructure_master` → `defi_master` —
  both `asset_group:[defi]`-only, content + doc's own stated resolution-owner are DeFi-specific, not infra-mechanism).
  `eec887db6`. (6 other parent_epic WARN flags among defi-tagged docs were adjudicated FALSE-POSITIVE — correctly scoped
  as-is; not touched.)

## Filed

Per the Phase-5.9(a) ledger: 3 items routed to the operator this run, 3 filed here — **routed == parked (3 == 3)**.

1. **`BLK-0b3e403d`** — ✅ **RESOLVED 2026-08-09 01:01 UTC (operator, disposition: final).** Line-cap carve-out
   (`scripts/plan-hygiene/check_line_caps.sh`, shipped `cff285743`) had a boundary bug: only rescued a file already
   over-cap pre-edit; a file sitting at EXACTLY 1000 lines making its first marker edit was NOT rescued, reproducing the
   "permanently unverdictable" bug it was built to fix. Confirmed live via direct read of the script logic + 2
   independent docs (`lst_rate_honest_coverage_2026_07_21.md`, `data_pipeline_check_mdps_features_2026_07_20.md`) both
   sitting at exactly 1000L. **Operator's answer**: option A confirmed, fixed directly (`-gt` → `-ge` at line 143, same
   bug fixed in the bats test helper, regression test added for the exact-boundary case), shipped
   `unified-trading-pm@1f65e1464` via the `scripts/**` direct-push carve-out (D16) — **verified by plan_reconciler**:
   `1f65e1464` confirmed reachable on `origin/live-defi-rollout` via `git merge-base --is-ancestor`, diff content
   matches the operator's description exactly. (Note: the operator's answer initially landed as
   `blocked_message_orphaned_by_reassign` — likely caused by a context-compaction event on this slot at ~01:02:18 UTC
   racing the delivery; recovered via the `/api/activity` feed rather than `/api/slots/2/messages`, which stayed empty
   throughout.)
2. **`BLK-d59ebc8e`** — 4 confirmed codex-SSOT staleness items (plans→codex updates never autonomous, need operator
   ruling before any edit): `defi-data-types-catalog.md:267` (staking_yields Status stale, should bump to Production);
   `pnl-attribution.md` lines 637+734 (both mislabel themselves "Hard Rule #4"; the real #4 is at line 82);
   `availability-manifest-and-data-status.md:136` (missing the `record_catalog_unavailable` code path, live-verified,
   15+ grep hits); `canonical-cutover-register.md:380` (missing MTDS's `_instruments_metadata.py` as a 7th cutover
   reader, live-verified fixed+shipped). **[WORKER REC: approve all 4]**
3. **`BLK-8b3f416d`** — re-surfacing (not a new find) `uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`'s
   contested `assigned_vm` verdict — reclassified `planning` then reverted to `NA` over a disputed reading of the
   2026-07-26 ruling's scope, unresolved 11+ days across 3 na-eligibility-audit passes including an unadjudicated
   "second independent signal." Genuinely evidence-can't-settle-it (ASK>PARK case).

**Also observed, NOT filed as escalations (out-of-tranche, belong to other shards' own runs):** 3 archive candidates
(`ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md` [ao],
`notify_slack_yml_fleet_rollout_scope_contradiction_2026_08_08.md` [ci],
`provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md` [cross-cutting]) and 1
silent-default-effort doc (`test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md` [ci]) surfaced by the
corpus-wide hygiene sweep's 2 hard-fail ratchets — all confirmed non-defi via `asset_group` check.

## Archive candidates (operator review)

- **`plans/active/issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md`** — 0 open / 1 closed todo, doc's
  own 2026-08-01 Progress Log states "no standalone action remains here." `locked_by: live-defi-rollout` — **NOT
  auto-archived** (HARD LIMITS: never auto-archive/auto-unlock a locked plan). Flagging: this exact `locked_by` value is
  shared by **96 other docs** corpus-wide — almost certainly a branch-name artifact, not a genuine per-operator claim,
  but confirming that at scale is outside this run's adversarially-verified scope. `[unlock-plan]` + archive, or
  investigate the 96-doc pattern as its own finding, is an operator call.

No other fully-done, unlocked, non-grace defi docs found this run (`check_archive_candidates.sh --diff-base origin/main`
found 0 new candidates in the defi tranche specifically — its 3 hits were all out-of-tranche, see Filed).

## Refuted (dropped by verify)

None. Every hunter candidate the orchestrator spot-re-verified (≈15 direct command re-executions: `git log`/`show` on 5
shas, `wc -l` on 3 docs, `find`/`grep` on 6 paths, codex-wording reads on 2 SSOTs) held up exactly as reported — no
hunter finding was found to be wrong on independent re-check. (Several minor P3 findings were confirmed-but-not-
actioned for cost/value reasons — listed under Contradictions above, not here, since "refuted" means the claim itself
was wrong, not that it was deprioritized.)

## Coverage (hunters / batches / docs)

- **Corpus**: 104 `asset_group:defi` docs — 49 grace (<12h, read-only), 55 non-grace (actionable), ~2.0MB. Plus
  `plans/epics/defi_master.md` (34 raw `parent_epic:` hits; 16 correct per the status-filtered regenerator) and the 4
  normative refs (corpus-wide every shard, not separately re-audited this run beyond what the sweep already checks).
- **Hunters**: 7 parallel batch hunters (A-G), each combining epic-cluster contradiction-hunting + mechanical
  adjudication + missed-flip + zero-checkbox + near-complete/fully-done + dangling-ref + codex-alignment duties for its
  batch (piggybacked per SKILL.md's efficiency guidance rather than separate dedicated passes) — 55/55 non-grace docs
  read in full, exactly once each. All 7 returned successfully (0 failures/timeouts).
- **Verify**: no separate refuter/confirmer sub-agent pairs spawned — given the volume (~30+ candidates) and that every
  hunter already cited a fresh, re-runnable command as its evidence, the orchestrator (effort=max, thinking=high)
  independently re-executed the highest-stakes ~15 checks directly (git log/show, wc -l, find, grep, codex reads) before
  applying any fix, functioning as the adversarial pass. Every check confirmed the hunter's claim.
- **Applied**: 10 checkpoint commits (`8c9a5526c`, `eec887db6`, `dfe8b0907`, `3baadb331`, `2e62b1a37`, `595ea3971`,
  `671937a92`, plus this doc's own creation `d56c911d1`), 26 distinct fixes across 21 docs.
- **Filed/routed**: 3 blocked-questions (`BLK-0b3e403d`, `BLK-d59ebc8e` [4 sub-items], `BLK-8b3f416d`) — routed==parked
  (3==3), per Phase 5.9(a).
- **Post-fix hygiene**: `run_hygiene_sweep.sh --no-regen` re-run after all fixes — same 2 pre-existing hard failures
  (both out-of-tranche, confirmed unchanged), `check_todo_format` count dropped 56→55 (the malformed-checkbox fix), no
  new violations introduced by this run's edits.

## Plans not reached

None — every confirmed, in-scope finding this run was either applied, routed, or explicitly logged as
confirmed-but-not-actioned (see Contradictions). No context-budget cutoff was hit.
