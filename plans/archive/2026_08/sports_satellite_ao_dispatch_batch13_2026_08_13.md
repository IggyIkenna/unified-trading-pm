---
doc_type: plan
title: sports satellite AO dispatch batch 13 — 2026-08-13
summary: >-
  Extraction batch from the sports tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep — 16 live
  conflict-cleared, bounded/deterministic items (21 total todos, 5 marked out-of-scope, see below) pulled directly from
  10 source docs (RECLASSIFY_SPLIT bounded items from the NA audit, orphaned_never_touched/orphaned_partial_coverage
  bounded items from the AG-closeout audit). Rescoped 2026-08-13 (operator scoping instruction): 5 MDPS/features-service
  backfill/recompute items with no manifest-canonical/migration angle marked [x] OUT-OF-SCOPE (checkbox format per
  todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md -- the source items remain open in their
  own source docs, untouched by this batch; the manifest-corpus-empty features-service investigation item was KEPT live
  -- manifest-canonical work is explicitly in scope even for features-service). Each todo cites its exact source doc;
  the source docs themselves are NOT touched by this batch (checkbox reconciliation back into each source doc happens in
  the paired finalize plan). Conflict-checked against every existing active batch/finalize plan for this tranche via
  basename-citation cross-reference before drafting — no item here duplicates ground an existing dispatched Todos entry
  already claims.
status: archived
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md,
    /plans/archive/2026_08/issues/features_sports_compute_features_hard_fail_missing_upstream_today_2026_08_10.md,
    /plans/active/issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md,
    /plans/archive/2026_08/issues/sports_catalog_dp_catalog_001_oom_manifest_read_2026_08_10.md,
    /plans/archive/2026_08/issues/sports_features_2026_backfill_launch_window_was_today_2026_08_10.md,
    /plans/archive/2026_08/issues/sports_features_dp_vm_001_upstream_fixtures_gap_2026_08_10.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md,
    /plans/active/issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2.4
estimate_calibrated_ai_days: 1.9
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# sports satellite AO dispatch batch 13 — 2026-08-13

> **🟢 ARCHIVED 2026-08-15 — all 21 todos complete.** Reconciled into their source docs' own checkboxes via
> `sports_satellite_ao_dispatch_batch13_2026_08_13_finalize.md`; see that finalize plan for the full reconciliation
> evidence.

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] ✅ [CODE] P2. Add a short callout to /codex/15-runbooks/incidents/rb_infra_relaunch.md instructing a worker to
      check whether a failing VM's launcher family has a supervising wrapper (grep deployment-service/scripts/vm/ for a
      _-historical-_ or loop-style caller) before relaunching, mirroring the existing 'if it re-fails the same way
      twice, STOP' pattern already in the runbook — added as new Procedure step 3 (renumbering the old 3/4 to 4/5),
      citing the root-cause example doc. unified-trading-pm@c5816bc7e6 Source:
      `plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md`
- [x] [CODE] P2. Once instruments-service has written real 2026-08-10 sports_reference data, --force recompute the
      sports features backfill for day=2026-08-10 (features-service) to replace the false
      empty_confirmed(SOURCE_RETURNED_ZERO) rows the aborted 12:03 UTC run wrote **OUT-OF-SCOPE FOR THIS BATCH
      (2026-08-13, operator scoping instruction)** — MDPS/features-service backfill/recompute work is excluded from this
      batch unless manifest-canonical or migration-related. **UPDATE 2026-08-14 (slot-29)**: the underlying item is now
      resolved (outside this batch) — manifest shows `fixture_features`/`derived_features` `captured` for 2026-08-10
      with real GCS output; source doc archived. Source:
      `/plans/archive/2026_08/issues/features_sports_compute_features_hard_fail_missing_upstream_today_2026_08_10.md`
- [x] ✅ [CODE] P2. Track F: root-cause why the features-service sfi_progressive manifest group is corpus-empty (1
      manifest row) despite a documented 2020->today backfill window. **STALE premise — already fixed by
      `sports_closeout_batch1_ao_ready_2026_07_24.md` + `data_completion_sports_2026_07_24.md` (launcher bucket fix +
      `MissingFeatureFamilyError` manifest-write fix, 2 real backfill runs).** Live-verified 2026-08-14 (slot 27):
      canonical manifest carries 18,409 `feature_group=sfi_progressive` rows (18,098 captured), 2,094 real GCS
      day-objects 2020-06-06→2026-08-01 — corpus genuinely healthy, no code change needed. Full detail in the Track F
      todo itself. Source: `plans/active/sports_consolidated_closeout_2026_07_19.md`
- [x] ✅ [CODE] P2. Track C: venue vocabulary cleanup dispositions for the residual non-canonical values
      (casing/aliasing re-stamp + footystats legacy bundle mislabel venue=ODDS_API->FOOTYSTATS, 42,476 rows)
      **INVESTIGATED 2026-08-14 (slot-30) — the literal disposition text is STALE, not executable as worded.** Live
      `read_availability_index` census found: (1) the footystats-mislabel rename this todo describes was already
      attempted 2026-07-27 (`sports_consolidated_native_ao_extract_2026_07_25.md` Progress Log claims "0 stale rows
      remaining") but a fresh 2026-08-14 census shows `venue=ODDS_API`/`pipeline_mode=batch_footystats` still holding
      19,782 real captured shards with dates through TODAY — an unfixed-writer recurrence, not residue, and the rename
      itself was already determined to be the WRONG fix one day before it ran
      (`plans/archive/issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md`, still `status: open`:
      correct fix is a purge, a rename creates duplicate manifest rows on 56.40% of cells); this ground is also
      concurrently owned by the active `sports_taxonomy_p2_migration_2026_08_08.md` plan (closed an adjacent todo
      today). Re-running the existing restamp script would repeat an already-identified wrong fix, so no code was
      shipped for that piece. (2) NEW finding, not covered by any prior effort: `LADBROKES_UK`/`SPORT888` also carry the
      same casing/alias defect under a third, previously-unexamined shape (`pipeline_mode=batch_footystats`,
      `data_type=odds_horizon_bucket`) — 121,884 shards / 12.3M rows measured, 2020-2026. Full evidence + recommended
      decision + 4 follow-up todos filed:
      `/plans/archive/2026_08/issues/sports_footystats_mislabel_contradiction_2026_08_14.md`. Stale claim in the source
      doc corrected in place (same turn). Source: `plans/active/sports_consolidated_closeout_2026_07_19.md`
- [x] ✅ [CODE] P2. Track C: QG assertion that sports data_type/venue/instrument_type/chain stay within the canonical
      vocabulary (deployment-ui Distinct Values panel reads 0 non-canonical across all four axes)
      **deployment-api@8497e952bb** (2026-08-14, slot-27). Wired `scripts/check_sports_distinct_values_canonical.py`
      (reuses the SAME `enumerate_distinct_values()` + honest-coverage rollup reader the `GET /distinct-values/sports`
      panel itself uses — no reimplemented vocabulary logic) into `quality-gates.sh` as a genuine hard-gate STEP: fails
      the run (exit 1) on real non-canonical drift, warns without blocking (exit 2) when the honest-coverage rollup is
      unreachable in a given QG context. **Root-caused + fixed a live QG-abort bug while wiring this in**: the checker
      script itself pre-existed from a prior same-slot session (unpushed local commit) but calling it as a bare
      statement silently aborted the ENTIRE quality-gates.sh run — `base-library.sh:43`'s `set -e` persists through the
      whole sourced QG process, so a non-zero exit outside an `if` condition triggers the inherited errexit + EXIT trap
      with zero error output (confirmed live via `bash -x` trace, reproduced twice deterministically). Fixed by
      observing the exit status via an `if` condition (bash's one errexit-exempt context), matching STEP 5.90's existing
      checker pattern. QG green (sentinel=8497e952 matches HEAD); verified `merge-base --is-ancestor` on origin. Source:
      `plans/active/sports_consolidated_closeout_2026_07_19.md`
- [x] ✅ [CODE] P2. Track E: repoint the remaining 7-file stale entity=fixtures consumer list to
      fixtures_schedule/fixtures_outcomes **`instruments-service@304711c8`** (2026-08-14, slot-10). Named list resolved
      against `sports_consolidated_closeout_2026_07_19.md`'s own Track E section: `sports_dependency.py` +
      `sports_fixtures_daily_repoll.py` were ALREADY migrated (already read/write
      `fixtures_schedule`/`fixtures_outcomes` as primary, with a documented legacy fallback for pre-migration dates) —
      no change needed. The remaining 4 files (`rescan_sports_fixtures_canonical.py:328,452`,
      `enumerate_expected_universe.py` — cited line 1902 was stale, real location is
      `_UNDERSTAT_FIXTURES_TPL`/`_build_understat_fixture_index` — `migrate_sports_per_league.py`,
      `reconcile_sports_blank_empty_reason_2026_06_24.py`) still hardcoded the bare, dead-since-2026-07-14
      `entity=fixtures/fixtures.parquet` path; repointed each to list the canonical (`pipeline_mode=`) then legacy
      per-league `entity=fixtures_schedule/` prefix, matching the established canonical-then-legacy pattern already used
      elsewhere in this package (`sports_fixtures.py::_read_per_league_entity_df`, `weather.py`). None of the 4 needed
      `fixtures_outcomes` (no score data consumed). Updated the one stale test assertion
      (`test_rescan_sports_fixtures_canonical_script.py::test_entity_handlers_registered`). QG green (sentinel=304711c8
      matches HEAD); verified `merge-base --is-ancestor` on origin. **Follow-up filed, not fixed here** (separate,
      pre-existing bug discovered during this repoint, not caused by it):
      `/plans/archive/2026_08/issues/rescan_sports_fixtures_canonical_per_league_suffix_match_broken_2026_08_14.md`
      (archived 2026-08-14, slot-18, fix shipped instruments-service@622b641628) — the rescan tool's blob-matching logic
      required an exact bare-file suffix, so its FIXTURES handler had matched zero real per-league objects since
      fixtures went per-league (independent of which entity name it points at). Source:
      `plans/active/sports_consolidated_closeout_2026_07_19.md`
- [x] ✅ [CODE] P2. Track O: repair attempted_at on the 112,277 rows from the named pre-clobber snapshot (a normal,
      human-watched write window, not unsupervised) Source: `plans/active/sports_consolidated_closeout_2026_07_19.md`

      **INVESTIGATED 2026-08-14 (slot-12, backend_engineer) — target keys extinct, repair as specified is moot.**
                                                          Summary: the consolidator-pause safety question is resolved (incremental cycles pass through unchanged canonical
                                                          rows untouched, so a direct CAS-write would need no pause) — but a dry-run join of the pre-clobber snapshot against
                                                          the LIVE canonical (both the base 4-col dedup key and the full production key, `_dedup_key_sql`-normalized
                                                          identically to `manifest_consolidator`) found **0 matching rows**: `venue=BETFAIR` no longer exists and current
                                                          `data_type='trades'` rows all belong to `venue=ODDS_API`, unrelated. No prod write attempted (nothing to write).
                                                          **CORRECTION + CLOSED 2026-08-14 (slot-30, backend_engineer)** — the line above claimed the full investigation +
                                                          evidence lives "in the source doc's own Track O entry (this same commit)"; that's stale/false — re-checked the
                                                          source doc's live Track O section (`sports_consolidated_closeout_2026_07_19.md:659`) and it carries no such note,
                                                          only the original unedited todo text. The real evidence trail is the issue doc slot-12's SAME commit actually
                                                          filed: `plans/active/issues/sports_track_o_attempted_at_keys_extinct_2026_08_14.md` (`status: open`,
                                                          `assigned_vm: NA`, one `[DIAG]` follow-up todo). **Independently corroborated slot-12's "not a bounded key-swap"
                                                          call, not just deferred to it**: `BETFAIR_SB_UK`/`BETFAIR_EX_UK`/`BETFAIR_EX_EU` are registry-level DISTINCT
                                                          venues (`unified-api-contracts/registry/venue_constants.py:67-69`) — no migration/rename script exists anywhere in
                                                          `market-tick-data-service` or `unified-api-contracts` mapping bare `BETFAIR` rows 1:1 (or by any documented rule)
                                                          onto the three new venues; classifying which pre-clobber row belongs to which requires row-level
                                                          market/region inspection, not a mechanical key substitution. This todo's literal ask (repair the 112,277 rows) has
                                                          no executable target and no code to ship; closing it here. The genuine remaining work (trace + re-classify) is
                                                          correctly parked as NA/DIAG in the issue doc above — do not re-open this exact todo, extend that issue doc's todo
                                                          list instead.

- [x] ✅ [CODE] P2. Track O: locate the emitter of the 139,620 venue=ODDS_API/source=api_football/empty_confirmed rows
      before folding into K2 **ALREADY DONE — duplicate of `sports_consolidated_native_ao_extract_2026_07_25.md`'s own
      Track O item (lines 281-321 there), never flipped in this batch.** Full mechanism + both fixes already cited
      there: pre-`mtds@accd8aa4` (2026-07-20), `_expected_sports_bookmakers()` derived its bookmaker-expectation scope
      from UAC venue CATEGORIES (5 keys incl. ODDS_API) instead of the real 23-key odds-api `bookmakers=` request list —
      `ODDS_API` (the aggregator token, never a real bookmaker) could therefore never pass
      `is_bookmaker_league_covered()` for any league, so every (league,date) cell in the cartesian expectation universe
      for `venue=ODDS_API` routed to `record_empty(was_expected=True)` -> `capture_status=empty_confirmed`, producing
      exactly these 139,620 rows (identical mechanism/count to sibling phantom venues BETFAIR(bare)/ONEXBET). The
      `source=api_football` mislabel is a separate, stacked bug: `SOURCE_PRIORITY[("sports","TRADES")]` was missing from
      UAC's `_source_priority_data.py`, so `derive_pipeline_mode_for_row()` fell through to
      `_ASSET_GROUP_FALLBACKS["sports"]=BATCH_API_FOOTBALL` and mis-stamped every sports TRADES sentinel row. Both fixes
      shipped (`mtds@accd8aa4`, `unified-api-contracts@44623d25`) and live-verified 2026-07-28 (0 rows carry
      `source=api_football` anywhere in the live MTDS sports manifest, 516,196 rows scanned — the population has NOT
      re-accumulated in the 5 days since the fix, positive proof it holds in prod). The "before folding into K2"
      downstream framing is itself stale (K2's casing migration is superseded/slated for revert per Track C) — pure
      standalone diagnosis, not a K2-fold-in precondition. No new code needed here; stale-checkbox correction per
      `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3.4. Source:
      `plans/active/sports_consolidated_closeout_2026_07_19.md`
- [x] ✅ [CODE] P2. Track V: execute the 5-part-proof-gated DELETE of the old raw-keyed league_id GCS objects (COPY+SWAP
      already done, reversibility-verified 604800s soft-delete window, unblocked since 2026-07-28) **INVESTIGATED
      2026-08-14 (slot-10) — did NOT execute the delete; the "unblocked since 2026-07-28" citation was STALE/WRONG.**
      That date's Track C K1/K2 lowercase-revert is a different axis (instrument_type/data_type casing) from this todo's
      raw-keyed `league_id` population — landing it cannot have unblocked this delete, and the plan's own next sentence
      already says so ("the population is a DIFFERENT one from K1/K2's own casing"). The REAL 2026-07-22 blocker was
      5-part-proof Part 3 (no live writer to the old shape) FAILING (`venue_fetch.py`'s `_build_sports_shard_path` call
      site). **Fresh live re-verification this session**: read-only manifest probes (`read_availability_index`,
      date-filtered, bounded via `run-bounded-analysis.sh`) across the full 2026-07-22..2026-08-13 gap window (19,797
      `data_type=trades` rows total) found ZERO true-raw-noncanonical `league_id` values in any `capture_status` — Part
      3 now genuinely passes. Parts 1/2/5 were NOT re-verified at the object level this session (last hard numbers:
      2026-07-22, 275,136/275,136) — the todo's own text requires "its own fresh candidate-list re-verify before
      running", which is real unstarted tooling work (a K1/K2-trio-style candidate-list generator + content-verify +
      CAS-delete executor), not a citation to skip. Per finding T (`task_template.md`) and the K1/K2 sibling near-miss
      (`plans/archive/issues/sports_k1k2_delete_bundled_with_twin_less_data_2026_07_27.md`), §3a reversibility alone
      never supplies the five-part proof on its own — executing a 275K-object delete on a stale citation would repeat
      that exact near-miss. Full findings + the 2 follow-up todos (build the executor trio; then launch + execute):
      `plans/active/issues/sports_track_v_raw_league_id_delete_5part_proof_status_2026_08_14.md`. Source:
      `plans/active/sports_consolidated_closeout_2026_07_19.md`
- [x] [CODE] P2. Clamp the per-year sports features backfill launcher's current-year window to end_date = min(today-1,
      {year}-12-31) so a current-day's not-yet-written upstream reference can never be a hard dependency at backfill
      time -- repo: deployment-service (launcher config/logic change, single deterministic fix). **OUT-OF-SCOPE FOR THIS
      BATCH (2026-08-13, operator scoping instruction)** — MDPS/features-service backfill/recompute work is excluded
      from this batch unless manifest-canonical or migration-related. The underlying item remains open in its own source
      doc, untouched by this batch/commit. Source:
      `plans/archive/2026_08/issues/sports_features_2026_backfill_launch_window_was_today_2026_08_10.md` (resolved +
      archived 2026-08-14, deployment-service@3a18bc5ce0)
- [x] ✅ [CODE] P2. Track upstream sports reference entity=fixtures for day=2026-08-10 until it exists under
      instruments-store-sports-prd; confirm the af-backfill historical backfill writes it when it reaches that date
      (instruments-service reference-capture gap). **ALREADY RESOLVED — duplicate of the source issue doc's own first
      Tracked-follow-up item, which was closed 2026-08-13 and independently re-confirmed live by 5+ sessions on
      2026-08-14 (slots 30/6/5/28/14) with nothing regressing.** The literal ask (bare `entity=fixtures` for
      day=2026-08-10 under `instruments-store-sports-prd`) targets a path that has been FROZEN since 2026-05-23
      (`/codex/02-data/sports-fixtures-lifecycle.md`) — it was never going to be written by the af-backfill or any live
      writer; the reader resolves `"fixtures"` split-first. **Fresh live re-verification this session (slot-21,
      2026-08-14)**:
      `get_storage_client().list_blobs(bucket="instruments-store-sports-prd-central-element-323112",     prefix="sports_reference/by_date/day=2026-08-10/")`
      → 648 objects, 13 distinct entities; bare `entity=fixtures` objects = 0 (confirmed still frozen, as expected);
      `entity=fixtures_schedule` = 43 objects, `entity=fixtures_outcomes` = 42 objects — identical counts to the source
      doc's 2026-08-13 measurement, confirming no regression 1 day later. No code shipped (nothing to fix — this is a
      stale-checkbox correction per `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3.4,
      not new work). Source:
      `plans/archive/2026_08/issues/sports_features_dp_vm_001_upstream_fixtures_gap_2026_08_10.md`
- [x] ✅ [CODE] P2. Verify the self-heal actuator dedup (launch_budget_registry) and whether an external launcher loop
      fired ~19 features-sports-sports-* VMs (~8 with empty vm-logs) far beyond the RB-INFRA-RELAUNCH ≤2/(prefix,day)
      bound -- resource-waste investigation. **STALE checkbox — this exact todo was already verified + fixed in the
      source doc itself before this batch was dispatched (slot-14, 2026-08-14)**, per
      `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3.4 stale-checkbox-correction
      pattern. `launch_budget_registry.py` (the todo's literal name) carries no dedup — rate/machine-sizing only. Real
      bound traced: `RelaunchBackfillVm`'s ShardedState budget only guards the in-process OOM (exit_code==137) actuator;
      `escalation.py`'s `_ACTUATORS_AVAILABLE` gating routes every other `DP_VM_EXIT_NONZERO` to
      `escalate-to-orchestrator` → a planning-VM worker relaunching by hand per RB-INFRA-RELAUNCH, a path with ZERO
      code-enforced relaunch-count bound (the ≤2/(prefix,day) rule was prose only) — the "external loop" that produced
      the 19-VM storm (~8 empty-log VMs = workers who launched, found the issue doc mid-setup, self-deleted). Fixed:
      `deployment-service@c7ed0077cb` adds `escalation_dedup.check_relaunch_dispatch_budget` (GCS-durable
      `ShardedState`, day-partitioned by vm-prefix, mirrors `revocation_actuator.py`) — the dispatched context now says
      `DO NOT RELAUNCH` once a launcher-family hits 2 dispatches for the day. Re-verified this session: SHA is an
      ancestor of `origin/live-defi-rollout` (`git merge-base --is-ancestor c7ed0077cb origin/live-defi-rollout` →
      true); `check_relaunch_dispatch_budget` present at `escalation_dedup.py:514` and wired into `escalation.py:616`;
      13 references in `tests/unit/test_escalation_dedup.py`. No new code needed — flipping this batch's duplicate
      checkbox to match the source doc's already-`[x]` state. Source:
      `plans/archive/2026_08/issues/sports_features_dp_vm_001_upstream_fixtures_gap_2026_08_10.md`
- [x] [CODE] P2. Recompute day=2026-08-10 sports features once upstream fixtures land -- the 15:42Z compute is sparse
      (row_count 1-2/league, computed from partial upstream) and must not be treated as final. **OUT-OF-SCOPE FOR THIS
      BATCH (2026-08-13, operator scoping instruction)** — MDPS/features-service backfill/recompute work is excluded
      from this batch unless manifest-canonical or migration-related. The underlying item remains open in its own source
      doc, untouched by this batch/commit. Source:
      `plans/archive/2026_08/issues/sports_features_dp_vm_001_upstream_fixtures_gap_2026_08_10.md`
- [x] ✅ [CODE] P2. Verify the 2022 year-sharded features VM (features-sports-sports-2022-20260810-051126, no
      EXIT_STATUS, terminated mid-run) -- confirm 2022 features coverage in the availability index. **VERIFIED
      2026-08-14 (slot-5) — no gap**: `run.log` confirms no `EXIT_STATUS` blob (preemption/kill, not a controlled exit);
      a bounded pushdown read of the availability index shows 365/365 distinct 2022 dates present (53,779 captured +
      1,060 empty_confirmed + 25 attempted_failed), and the exact death-point date (2022-11-11) itself shows 206
      captured rows, in line with neighbors. No relaunch/backfill needed. Full writeup in the source doc (now archived —
      its own last open todo, so it was archived in the same commit as this flip). Source:
      `plans/archive/2026_08/issues/sports_features_dp_vm_001_upstream_fixtures_gap_2026_08_10.md`
- [x] ✅ [CODE] P2. Gate escalation dispatch on already-resolved status (or carry the resolution summary in the boot
      context) so a resolved DP-VM alert cannot spawn a conflicting relaunch worker -- AO/orchestrator, [CODE] P3.
      **agent-orchestrator@3a5f637fab** (2026-08-14, slot-6). Root cause: `enqueue()`'s existing VM-lifecycle dedup
      (`_find_open_issue_for_vm_name`) only matches issue docs under `plans/active/issues/` with `status: open` — once
      an issue doc for a VM is RESOLVED, plan-archival discipline moves it to `plans/archive/**/issues/`, so that lookup
      stops matching it and a genuinely-closed DP-VM incident regains ZERO dedup coverage the moment its issue doc is
      archived (exactly this doc's own history: TEN same-day re-dispatches, the last two firing AFTER the open-issue
      dedup had already landed). Added `_find_resolved_issue_for_vm_name` (matches any doc under
      `plans/archive/**/issues/` on VM name alone — archived = resolved by construction, no status filter needed) as a
      second dedup layer in `enqueue()`: a match now returns a `vm_already_resolved` response (no worker queued)
      carrying the archived doc's resolution summary (`_extract_resolution_summary` — prefers the `> **ARCHIVED**: ...`
      banner, falls back to frontmatter `summary:`) via `_vm_resolved_response`, satisfying the todo's "carry the
      resolution summary" alternative alongside the primary gate. 8 new unit tests (`tests/test_escalation.py`:
      archived-dir matching incl. the flat `plans/archive/issues/` shape, no-vm-name skip, resolution-summary extraction
      incl. fallback/empty cases, full `enqueue()` integration for the dedup-skip path). QG green (3749 passed + 2
      skipped, dashboard tsc/vitest 346 passed). Verified
      `git merge-base --is-ancestor 3a5f637fab origin/live-defi-rollout`. Source:
      `plans/archive/2026_08/issues/sports_features_dp_vm_001_upstream_fixtures_gap_2026_08_10.md`
- [x] ✅ [CODE] P2. Re-roll build_instrument_catalogue.py --asset-group sports --since 2019-01-01 to pick up the +26,894
      round rows the § Q/§ T/§ W backfills already closed -- the catalogue snapshot predates them. **INVESTIGATED
      2026-08-15 (slot-18) — command confirmed working, but the "single-command, deterministic-outcome" framing
      undersold the runtime profile.** Smoke-tested via `--max-blobs 20` (forced dry-run): GCS auth, bucket resolve,
      frozen-tail merge, and monotonic guard all function correctly (truncated sample correctly triggered
      `CATALOGUE_SHRINK_BLOCKED` vs the current 534,023-row baseline — the guard working as designed, no prod write).
      Launched the real full run (memory-bounded 8G, backgrounded): it discovered **840,035** sports
      fixture/team/player-source `by_date` parquets to roll up — a genuinely corpus-scale, multi-hour GCS walk, not a
      quick single-command job — and was killed by the harness ~26 min in with no OOM evidence and no sign my own
      memory-cap wrapper fired. This is the "genuinely corpus-scale → dedicated VM, not direct-host" class per
      `RULES.md` §1; VM launches are `infra` craft, outside `backend_engineer` scope, so escalating rather than
      absorbing. Full findings + 2 follow-up todos (VM dispatch; kill-cause diagnosis if it recurs):
      `plans/active/issues/sports_catalogue_reroll_2019_corpus_scale_killed_2026_08_15.md`. Source:
      `plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`
- [x] ✅ [CODE] P2. Repoint the 7 remaining stale entity=fixtures consumers (sports_dependency.py,
      sports_fixtures_daily_repoll.py, rescan_sports_fixtures_canonical.py:328,452, enumerate_expected_universe.py:1902,
      migrate_sports_per_league.py, reconcile_sports_blank_empty_reason_2026_06_24.py) to fixtures_schedule
      (+fixtures_outcomes where scores are needed) -- instruments-service, a mechanical single-repo file-by-file repoint
      with a named, closed list. **DONE — identical population as this batch's own Track E todo above (same 7-location
      list, same fix); this todo was a duplicate never flipped.** `instruments-service@304711c8` (2026-08-14, slot-10).
      Full evidence in the Track E entry above. Source:
      `plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md`
- [x] [DATA] P2: root-cause why odds_features feature-export parquet is entirely missing for
      2025-10-23/2025-11-11/2025-11-13 despite odds_horizon_bucket being re-derived (resolve env=dev discrepancy in the
      features-service CLI first, per the doc's own explicit caution against --force before that) **OUT-OF-SCOPE FOR
      THIS BATCH (2026-08-13, operator scoping instruction)** — MDPS/features-service backfill/recompute work is
      excluded from this batch unless manifest-canonical or migration-related. The underlying item remains open in its
      own source doc, untouched by this batch/commit. Source:
      `plans/active/issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md`
- [x] ✅ [REVIEW] P2. locate and re-engage the owner of 'the bucket-cutover lane' referenced in
      reprocess_sports_odds.py's code comment (ceadb45c/2026-07-16), or confirm the comment is stale — **CONFIRMED NOT
      STALE; no live owner to re-engage.** Owner located:
      `plans/archive/2026_07/sports_legacy_bucket_cutover_2026_07_16.md` (`status: complete`, archived 2026-07-27,
      independently re-verified via a fresh /ag-closeout-audit pass the same day per its own banner) + its companion
      `sports_legacy_bucket_cutover_history_2026_07_24.md`; both sibling child plans
      (`sports_legacy_cutover_closeout_tasks_2026_07_24.md`,
      `sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md`) are also archived with terminal status. The
      ~90,947 `processed/` odds_horizon_bucket objects the comment refers to were a DELIBERATE, accepted TERMINAL
      disposition (PRESERVATION not migration — server-side-copied to `_legacy_migrated_processed/` before the legacy
      bucket delete, per the history doc's own Phase-4 T4.1 entry), not an unfinished task — there is no live effort
      left to re-engage. Corroborated corpus-wide: `_legacy_migrated_processed/` is still treated today as inert
      scratch/metadata (excluded from manifest audits by
      `plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md` Finding 1's underscore-prefix
      exclusion fix), and no active plan/issue proposes touching it further. The comment stands accurate as written; no
      code change needed. Source:
      `plans/active/issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md`
- [x] [CODE] P2. Re-run MDPS odds_horizon_bucket shard4 full-mode (resume-friendly, not --force) reprocess for
      2025-01-01..2026-07-25 once the odds_api gap-backfill converges into that date range, to re-poll the ~20 remaining
      honest-gap attempted_failed dates **OUT-OF-SCOPE FOR THIS BATCH (2026-08-13, operator scoping instruction)** —
      MDPS/features-service backfill/recompute work is excluded from this batch unless manifest-canonical or
      migration-related. The underlying item remains open in its own source doc, untouched by this batch/commit. Source:
      `plans/active/issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`
- [x] ✅ [CODE] P2. Stream the sports consolidated-manifest read (pyarrow column projection + current-data_type filter
      applied before .to_pandas()) in build_sports_catalogue_from_manifest so the catalogue rollup's peak memory stops
      scaling linearly with the ~20MB/day-growing manifest, giving durable headroom beyond the 2026-08-10 16Gi/cpu4
      provisioning bump **instruments-service@f6f38f2f24** (2026-08-15, slot-14). Pushed the current-data_type row
      filter (already re-applied identically by both `_read_sports_manifest_index` callers) into the pyarrow read
      alongside the existing column projection, so the full ~17M-row manifest never materializes in pandas — only the
      current-data_type subset does. QG green (sentinel=f6f38f2f matches HEAD); verified `merge-base --is-ancestor` on
      origin. Source: `plans/active/issues/sports_catalog_dp_catalog_001_oom_manifest_read_2026_08_10.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
