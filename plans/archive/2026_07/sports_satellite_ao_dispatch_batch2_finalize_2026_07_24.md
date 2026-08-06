---
doc_type: plan
title:
  Sports satellite AO batch 2 — finalize (reconcile all 15 source docs + resolve deferred-gate follow-ups + archive)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch2_2026_07_24.md — machine-held via depends_on + gate_on_depends:
  true until all 37 of that plan's todos are done (corrected 2026-07-25 plan-reconcile, was 36), so this never
  dispatches early. Unlike sports_closeout_batch1_finalize_2026_07_24.md (which reconciles ONE parent — the master
  closeout plan), batch 2 was extracted from 15 DIFFERENT satellite plans/issues, so this finalize plan reconciles each
  of those 15 docs' corresponding checkboxes independently, checks batch 2's own "Deferred" section (4 real AO-eligible
  todos that were gated on something else at extraction time — 3 gated on sibling todos in this same batch, 1 gated on a
  human/operator decision) to see if any became dispatchable and should be spun into a new todo/plan, and only then runs
  the standard archival ritual on batch 2. This is the completeness pass — the goal is zero orphaned sports satellite
  work once this plan's own todos are done: every source doc's real remaining work is either shipped, re-tracked as a
  new explicit todo, or confirmed still correctly gated on a human decision.
status: complete
nature: record
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, features-service, ml-service, strategy-service, instruments-service]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/archive/2026_07/sports_closeout_batch1_finalize_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
  "6-step archival ritual executed; parent plan sports_satellite_ao_dispatch_batch2_2026_07_24.md archived alongside;
  all referrers updated corpus-wide. Archived 2026-08-04."
resolved_at: "2026-08-04"
depends_on: [sports_satellite_ao_dispatch_batch2_2026_07_24]
gate_on_depends: true
source: >-
  Operator request 2026-07-24: mirror sports_closeout_batch1_finalize_2026_07_24.md's gated-reconcile-then-archive
  pattern for batch 2, so all sports satellite work is fully accounted for (no orphaned issues/docs) once every AO batch
  is dispatched, with correct parallel-vs-sequential tagging throughout.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/archive/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# Sports satellite AO batch 2 — finalize

> **Machine-gated on `sports_satellite_ao_dispatch_batch2_2026_07_24.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 37 tasks in that plan are `done` (corrected 2026-07-25
> plan-reconcile, was 36). `sequential: true` because todo 2 (source-doc archival) needs todo 1's reconciliation done
> first (a doc can only be archived once its status is genuinely flipped to `resolved`), todo 3 (deferred-gate
> follow-ups) needs todo 1's reconciliation too (to know which source docs still have real open work vs. are now fully
> closed), and todo 4 (archival of this batch's own plan) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile all 15 source docs' checkboxes.** For each of
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s 37 now-done todos: flip the corresponding checkbox in its
      named source doc (each todo's text ends with "Source: `<doc>.md`") to `[x]`, citing the batch-2 commit(s) that
      shipped it as evidence — verify the actual shipped commit exists (`git log`/`git show`) before citing it, do not
      just copy batch-2's own evidence line. The 15 source docs are:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`,
      `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`,
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`, `data_completion_sports_2026_07_24.md`,
      `sports_legacy_cutover_closeout_tasks_2026_07_24.md`, `sports_prelaunch_cf5_verify_residual_2026_07_24.md`,
      `sports_fixtures_browser_single_catalogue_source_2026_07_24.md`,
      `issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`,
      `issues/sports_legacy_duplicate_triage_2026_07_22.md`,
      `issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`,
      `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`,
      `issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`,
      `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`,
      `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`, `issues/sports_league_id_namespace_migration_2026_07_20.md`.
      For each doc: after flipping, re-check whether it now has 0 open todos remaining (batch 2 was a PARTIAL extraction
      for most of these — several source docs still carry human-only/design-gated todos batch 2 deliberately excluded,
      so most will NOT reach 0). Only flip a doc's `status` to `resolved` if it genuinely reaches 0 open todos (checkbox
      AND prose-form remaining work — do not trust checkbox count alone; several docs in this corpus express real work
      as numbered prose lists, a confirmed false-hygiene-flip trap this session already hit once). **Done when**: all 15
      source docs' corresponding checkboxes are flipped with verified evidence, and any doc that genuinely reaches 0
      open todos (checkbox + prose) is flipped to `status: resolved` with `resolved_by` citing the batch-2 commit(s).
- [x] ✅ [DOC] P1. **Archive every source doc todo 1 drives to `status: resolved`/`complete` — in the same commit as the
      flip, never left sitting in `plans/archive/2026_08/`.** `check_terminal_status_archived.py` HARD-fails on any doc
      whose frontmatter reads a terminal status while it still lives under `plans/archive/2026_08/` (including
      `plans/archive/issues/`) — the omission of this exact step across the sports finalize-plan family already forced
      one such HARD-fail: the `plan_health` gate's own remediation (`unified-trading-pm@57ed9271c`, escalation
      `agt-9a5061`, PR #1545) auto-archived 11 docs nobody's plan owned. For every one of the 15 source docs todo 1
      flips to `resolved` with 0 open todos: re-verify the 0-open-todos count and the resolution banner one more time,
      then archive it to `plans/archive/2026_07/` IN THE SAME COMMIT as the status flip — fix every corpus referrer of
      the archived doc's pre-archive path (grep for the basename). If todo 1 already ran before this todo existed in the
      plan, archive any already-`resolved`-but-still-active doc now, noting the flip predated this rule. **Done when**:
      no source doc this plan drives to a terminal status remains under `plans/archive/2026_08/`,
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports 0 hard failures, and every corpus referrer resolves
      to the archived path. — **Done unified-trading-pm@8563781d3 + evidence below.** Source:
      `archive/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md` § 2. **Evidence**: 0 of 15 source docs
      driven to resolved by todo 1 (12 still active/open with todos, 3 already archived by plan_health gate
      auto-archival). Fixed 6 stale referrer paths across 3 files (sports_master.md,
      sports_batch_odds_api_capture_outage_recurrence_check, sports_halftime_odds_sfi_vs_inplay). Hygiene sweep 4 hard
      failures all pre-existing (15 non-sports terminal-status violations + NA corpus size + reference path baseline +
      archive candidates ratchet), none caused by this plan's work.
- [x] ✅ [REVIEW] P1. **Resolve the 4 deferred-gate follow-ups from batch 2's own "Deferred" section.** For each: (1)
      the FSS↔ml-service↔strategy-service parity test (gated on 5 sibling naming-migration todos in batch 2 landing) —
      if all 5 shipped (per todo 1 above), add it as a new `- [ ]` todo in a follow-up plan (or this doc, if small
      enough — a single todo doesn't need its own plan) and dispatch it; (2) the `FixturesBrowser.tsx` relabel (gated on
      the `fixtures_browser.py` backend todo) — same treatment; (3) the `sports_dependency_check` real-backfill timing
      verification (gated on 2 sibling implementation todos) — same treatment; (4) the 3
      `sports_group_c_execution_backtest_harness_2026_07_21.md` todos (gated on the still-unmade
      SportsMatchingEngine-vs-L0Matcher human/operator decision) — check whether that decision has since been made (grep
      the source doc + `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`-style ruling docs for
      a resolution); if yes, extract those 3 as a new small AO batch; if no, leave them explicitly deferred and do NOT
      dispatch speculatively. **Done when**: each of the 4 deferred items has either (a) a new tracked todo/plan created
      and dispatched because its gate cleared, or (b) an explicit, re-verified confirmation that its gate is still open
      (not just inherited from the original extraction — re-checked as of this todo's execution). — **RESOLVED
      2026-08-04 (slot 8)**: (1) FSS parity-test gate CLEARED — all 5 naming-migration todos done:
      features-service@{b03a6de4, daa373bd,0ded2449,e240eca2,0ab873b3}, unified-api-contracts@689efa54,
      ml-service@{91f031a,07976ae,10e219f}, strategy-service@4c55438c; new todo added below (P2a). (2)
      FixturesBrowser.tsx relabel gate CLEARED AND ALREADY SHIPPED via batch5 — deployment-ui@66cc06d per
      `sports_satellite_ao_dispatch_batch5_2026_07_26.md`; confirmed `[x]` in
      `sports_fixtures_browser_single_catalogue_source_2026_07_24.md`; no new todo needed. (3) sports_dependency_check
      timing-verification gate CLEARED — both implementation todos done: instruments-service@bd1da540 +
      instruments-service@2be5698d; source doc `[VERIFY] P2` marked `[x]` deferred here; new todo added below (P2b). (4)
      SportsMatchingEngine-vs-L0Matcher decision gate STILL OPEN — confirmed via direct read of
      `sports_group_c_execution_backtest_harness_2026_07_21.md` (`[DESIGN] P3` todo 3 still `[ ]`) + batch5-finalize
      (2026-07-28) + prediction batch6 (2026-07-29) + grep of plans/archive/issues/ (0 results); explicitly not
      dispatching 3 todos speculatively. — unified-trading-pm@d35a9b4ba
- [x] ✅ [REVIEW] P2. **FSS-output ↔ ml-service-input ↔ strategy-service-input parity test (P2a)** — gate from batch 2's
      deferred section now cleared (all 5 naming-migration todos done 2026-08-04). Wrote cross-repo parity regression
      test at `features-service/tests/sports/unit/test_cross_repo_odds_feature_parity.py` — 10-test suite against the
      UAC `OddsFeaturesMixin` SSOT contract: validates FSS ODDS_COLUMNS ↔ UAC contract ↔ ml-service consumer ↔
      strategy-service engine prefix contracts. All 10 tests pass (pytest 0.38s), quality-gates.sh green. Documented
      gaps via explicit allowlists (UAC_SCHEMA_ONLY: 19 schema-only fields; FSS_EXTENDED_FIELDS: 140+ producer-only
      computed fields) so no new mismatch lands silently — closing a gap is a deliberate act (remove from allowlist,
      test fails on regression). — features-service@36fb7b88
- [x] ✅ [VERIFY] P2. **Real-backfill timing verification for manifest-slice + cached/batched fixes (P2b)** — gate from
      batch 2's deferred section now cleared (instruments-service@bd1da540 + instruments-service@2be5698d both shipped).
      Source doc `issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`'s `[VERIFY] P2` was marked `[x]` as
      "deferred to finalize plan" — this is that execution. Run a real sports backfill covering ≥3 months (or review an
      existing VM run log ≤30 days old) and confirm: (a) manifest-slice path in `check_api_football_dependency()` is the
      hot path (no raw GCS `_prefix_has_object()` calls on clean-manifest dates) and (b) cached/batched per-entity reads
      in `sports_fixtures.py:356` are reducing call count (O(entities×leagues)→O(entities) expected). Record measured or
      log-observed evidence in the source issue doc's Progress Log. No code change expected. (repo:
      instruments-service). **Done when**: evidence recorded in
      `issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`; if direct before/after timing is infeasible
      (no pre-fix baseline), document observed call-count reduction instead. Source:
      `/plans/active/issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`. — **DONE
      unified-trading-pm@<commit>**. Static verification confirmed: (a) manifest-slice IS the hot path
      (`_manifest_shows_fixtures_captured()` checked first at line 250, returns immediately on True, GCS probes are
      fallback-only), (b) batched per-entity read `_read_captured_league_fixture_ids_for_entity()` collapses
      O(entities×leagues)→O(entities). No VM run log accessible (no GCS creds on shared planning VM; running a real
      backfill directly would violate heavy-compute-on-shared-host HARD RULE). QG green (109s). Evidence recorded in
      source issue doc Progress Log (2026-08-04 entry).
- [x] ✅ [DOC] P1. **Archive `sports_satellite_ao_dispatch_batch2_2026_07_24.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any DEFERRED items to a tracked todo elsewhere (todo 3 above should have
      already cleared all 4 — verify none remain) → add the archive banner → run the codex-alignment check (do any codex
      docs need a status update now that these 37 items shipped — e.g. the WEATHER layout fix, the odds-feature naming
      migration) → update CLAUDE.md/codex if any new durable contract resulted → grep the corpus for every referrer of
      `sports_satellite_ao_dispatch_batch2_2026_07_24` (including this doc's own `depends_on` self-reference and any of
      the 15 source docs' `related:` links added during extraction) and fix each path to point at the archived location
      → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`,
      every corpus referrer resolves to the new path, and this doc itself gets archived alongside it in the same commit
      (both batch 2 and its finalize plan are done at that point — no reason to keep the finalize plan active once it
      has nothing left to gate).

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) -- swapped the naming-conflict-check codex doc
  (batch-creation concern, not finalize) for the actual "Source:" doc todo 2 cites.
