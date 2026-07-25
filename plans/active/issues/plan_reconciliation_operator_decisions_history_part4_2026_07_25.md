---
doc_type: issue
title:
  "Plans-corpus contradiction audit 2026-07-11 — history part 4/4 (Section B auto-fix queue, P2-tail + P3, end of
  Section B: instruments_completion_tracker↔instruments_master through epics/features_and_ml_master intra-doc)"
summary:
  "Verbatim extraction of the FINAL 76 of Section B's 176 auto-fix-queue finding entries (P2 tail + all of P3) from
  `plan_reconciliation_operator_decisions_2026_07_11.md`, split for line-cap compliance (`plans/active/task_template.md`
  §3 finding J). Every finding here was applied per the parent's Progress Log (2026-07-11 through 2026-07-14 fixer
  waves) — this file is the closed raw finding text only, not live tracking. Zero open todos. This is the last of the 4
  history parts; Section B ends at the last entry in this file."
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, contradiction-audit, reconciliation, operator-decisions, stale-drift, history]
related: [/plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md]
created: 2026-07-25
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P3
source: [plan_reconciliation_operator_decisions_2026_07_11]
resolved_by:
  "extracted verbatim from the closed 2026-07-11 contradiction audit; every finding's ruling + disposition lives in the
  parent's §A2 rulings table and Progress Log, not in this file"
locked_by:
drift_direction: advance-code
depends_on: []
---

# Plans-corpus contradiction audit — history part 4/4 (Section B, findings 101-176 — Section B ends here)

> **Extracted verbatim 2026-07-25 →** this file, from
> `/plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` (line-cap remediation,
> `plans/active/task_template.md` §3 finding J — the parent was 3927 lines, over the 1000L hard cap). This is the LAST
> of 4 history parts; see the parent doc for the full part index, the §A2 rulings table, Section C (structural gaps),
> Section D (bonus finding), and the Progress Log (which carries every currently-open todo — there are none in this
> file). Content below is byte-for-byte as it appeared in the parent's Section B, unedited. The parent's Section C
> ("Structural gaps") begins immediately after this file's final entry, in the parent doc itself.

#### [P2] active/instruments_completion_tracker_2026_07_06.md ↔ epics/instruments_master.md

- finding ids: 101
- **Epic's auto-populated child-plan count omits the completion tracker** — `epics/instruments_master.md:423`: “"\_3
  active plans declare `parent_epic: instruments_master` in their frontmatter ... Auto-populated by
  `scripts/plans/populate_epic_bodies_2026_05_21.p”  vs  `active/instruments_completion_tracker_2026_07_06.md:51`:
  “"parent_epic: instruments_master"”
  - why: The completion tracker (doc_type: plan, created 2026-07-06 — before the epic's own last_updated of 2026-07-08)
    declares parent_epic: instruments_master in its frontmatter, yet the epic's 'Assigned active plans' section still
    claims only 3 such plans and does not list or link the tracker anywhere in its body, despite th

#### [P2] active/instruments_service_docs_consolidation_2026_07_08.md (intra-doc)

- finding ids: 390,371
- **mechanical:terminal_status_in_active_dir** — `active/instruments_service_docs_consolidation_2026_07_08.md:18`:
  “status: complete” vs `active/instruments_service_docs_consolidation_2026_07_08.md:100`: “- [ ] [DATA] P0. **Read all
  17 existing docs in full** (not just the intros already skimmed) and extract every concrete claim...”
  - why: Frontmatter declares status: complete, but Phase 1 (6 todos, all P0/P1) is still unchecked `- [ ]` with no
    inline resolution banner on those checkboxes (unlike its sibling same-day flips, e.g.
    mdps_book_microstructure_precompute_columns_2026_06_28.md and
    features_read_book_columns_not_snapshots_2026_06_28.md, which eac
- **instruments-service docs-consolidation plan frontmatter status vs its own unchecked Phase-1 audit checkboxes** —
  `active/instruments_service_docs_consolidation_2026_07_08.md:18`: “status: complete” vs
  `active/instruments_service_docs_consolidation_2026_07_08.md:100-117`: “- [ ] [DATA] P0. Read all 17 existing docs in
  full ... - [ ] [DATA] P0. Cross-check every venue-list claim against UAC's registries ... - [ ] [DATA] P”
  - why: Frontmatter declares status: complete, but the body's entire Phase 1 (6 todos, several P0) is left as unchecked
    `- [ ]`. The Progress Log explains the audit work was split into a separate audit doc and the plan's depends_on was
    repointed there instead of flipping these checkboxes — but the checkboxes themselves were ne

#### [P2] active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md (intra-doc)

- finding ids: 80
- **Has the fleet already lifted the aiohttp <3.14 cap, or is that still gated on a future vcrpy release?** —
  `active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md:30`: “## ✅ RESOLVED 2026-06-23 — aiohttp 3.14.1
  shipped fleet-wide (vcrpy 8.2.1 unblock)” vs `active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md:192`:
  “Lift the `<3.14` cap + bump fleet to `aiohttp>=3.14` + drop the two `--ignore-vuln` flags — ONLY when”
  - why: The doc's own top banner declares the aiohttp<3.14 cap already lifted fleet-wide (17/18 repos on 3.14.1+vcrpy
    8.2.1) as of 2026-06-23. The successor todo list still carries an unchecked item phrased as if this hasn't happened
    yet ('ONLY when vcrpy ships an aiohttp-3.14-compatible release'), which was true before 2026-0

#### [P2] active/issues/audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md (intra-doc)

- finding ids: 212
- **audit_writes_escalation_artifacts frontmatter status vs its own fully-verified fix** —
  `plans/active/issues/audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md:16`: “status: open” vs
  `plans/active/issues/audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md:212`: “[x] ✅ [VERIFY] P2.
  Confirm a fresh full run leaves `git status` clean in the PM clone and the escalation is ingested by PlanRegenLoop (no
  dirty untrac”
  - why: Frontmatter still declares status: open, but all 4 todos are checked done including the terminal VERIFY step,
    which cites a live re-run confirming clean git status and successful PlanRegenLoop ingestion at
    unified-trading-pm@ad1fa6bc2 — the doc's body reads as fully resolved while its frontmatter still flags it as an o

#### [P2] active/issues/autospawn_should_spawn_no_revive_pinned_opus_slot_2026_06_29.md (intra-doc)

- finding ids: 219
- **Frontmatter status: open contradicts the doc's own body showing its single fix fully shipped, tested, and evid** —
  `active/issues/autospawn_should_spawn_no_revive_pinned_opus_slot_2026_06_29.md:6`: “status: open” vs
  `active/issues/autospawn_should_spawn_no_revive_pinned_opus_slot_2026_06_29.md:55-63`: “[x] [AGENT] P2. ✅ (opus) Make
  autospawn... — agent-orchestrator@826a496 (new `AutoSpawnLoop._maybe_kill_for_tier_upgrade`... 9 unit tests +
  integratio”
  - why: This issue doc has exactly one fix item and it is checked done with a commit sha, 9 unit tests, and an
    integration assertion, and the Notes section frames it as closing 'the residual starvation edge' with nothing else
    outstanding — yet the frontmatter status was never flipped from open to resolved/closed, so the doc st

#### [P2] active/issues/capability_wizard_analysis_findings_2026_06_11.md ↔ epics/strategy_master.md

- finding ids: 295
- **archetype count: epic's 53 vs same-day finding that the true count is 57** — `epics/strategy_master.md:72`: “**53
  archetypes** per `codex/09-strategy/architecture-v2/archetypes/` — closed-set strategy taxonomy.” vs
  `active/issues/capability_wizard_analysis_findings_2026_06_11.md:126`: “The actual value in `enums.py` is 57 as of
  2026-06-11. 4 new archetypes were added after the audit without a plan update.”
  - why: Both documents carry a 2026-06-11 date; the analysis-findings doc explicitly flags that plan prose (matching
    the epic's own '53 archetypes' wording) is stale and the real count is 57 — the epic was never corrected to reflect
    this, so it still reads as authoritative to a new agent.

#### [P2] active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md (intra-doc)

- finding ids: 115
- **Doc status vs. body completion state** — `active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md:15`:
  “"status: open" (frontmatter)” vs `active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md:187-368`: “All 6
  todos marked "[x] ✅ ... CROSS-REFERENCE MARKER CLOSED 2026-07-06" with no residual open item”
  - why: Every actionable todo in the doc's own body is checked off and explicitly annotated as closed (cross-reference
    markers for cefi/tradfi/prediction all closed), yet the frontmatter still declares status: open with no banner
    explaining why the doc itself remains open despite 100% todo closure — a class-(d) frontmatter/bod

#### [P2] active/issues/data_pipeline_alert_transient_gcs_pressure_false_positives_2026_06_24.md (intra-doc)

- finding ids: 204
- **issue frontmatter status vs body resolution banner** —
  `active/issues/data_pipeline_alert_transient_gcs_pressure_false_positives_2026_06_24.md:5`: “status: open” vs
  `active/issues/data_pipeline_alert_transient_gcs_pressure_false_positives_2026_06_24.md:72`: “All three fixes shipped
  to `deployment-service`... Issue resolved → archive on next sweep.”
  - why: Frontmatter still declares the issue open while the body's own Resolution section states all three fixes
    shipped and explicitly calls for archival — the doc was never flipped to resolved/archived despite its own closing
    banner (class-d intra-doc drift).

#### [P2] active/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md ↔ active/issues/manifest_hygiene_red_2026_06_27.md

- finding ids: 206
- **defi/DP_NOT_V9 false-positive: separately-tracked open item vs same-day shipped audit-code fix** —
  `active/issues/manifest_hygiene_red_2026_06_27.md:55`: “[ ] [CODE] P1. Manifest hygiene RED — 1 AG(s) with findings
  (2026_06_27) — diagnose + fix the root cause (misclassified-empty vs real gap, not-v9 sche” vs
  `active/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md:170`: “Finding 1 —
  DP_NOT_V9 (alert truthfulness — SHIPPED `e2e-testing@21ce846`, QG green 81s) — Normalise the schema_version compare so
  the count is truthf”
  - why: Both docs are dated 2026-06-27 and concern the same manifest-hygiene DP_NOT_V9 finding-class produced by the
    same audit script; the sibling issue diagnosed and shipped a fix for the exact false-positive root cause
    (string-vs-int schema_version compare) that same day, but manifest_hygiene_red_2026_06_27.md's generic tod

#### [P2] active/issues/instruments_service_plan_reconciliation_2026_06_29.md ↔ active/layer1_remeasure_and_certify_2026_07_06.md

- finding ids: 345
- **which Layer-1 honest-coverage certification is the current authoritative figure per asset_group (cefi/defi esp** —
  `active/issues/instruments_service_plan_reconciliation_2026_06_29.md:146`: “A19 `LANDED` — **Certified Layer-1
  (06-29):** cefi 65.91 | defi 69.44 | tradfi 51.43 | sports 30.77 | prediction 66.67. ... **These supersede ALL earl”
  vs `active/layer1_remeasure_and_certify_2026_07_06.md:98`: “**CERTIFIED 2026-07-06 15:01 UTC: cefi Layer-1 = 73.61%
  (present 53 / expected 72; 19 missing tuples; 87 stray).\*\*”
  - why: instruments_service_plan_reconciliation_2026_06_29.md is status: open, last_updated 2026-07-03, and explicitly
    frames its 06-29 Layer-1 figures (cefi 65.91, defi 69.44, ...) as superseding ALL earlier numbers and warns that
    plans citing other figures are citing stale numbers. It was never updated after the 2026-07-03 U

#### [P2] active/issues/is_cefi_manifest_blank_data_type_since_2026_06_29_2026_07_06.md ↔ active/issues/manifest_reprocessing_generic_utility_2026_07_07.md

- finding ids: 122
- **Completeness of the '11 one-off reprocessing scripts' audit** —
  `active/issues/manifest_reprocessing_generic_utility_2026_07_07.md:48-49`: “11 near-identical "load manifest → filter
  by predicate → flip status/reason field → snapshot → write back" scripts, independently reinvented across 3 ” vs
  `active/issues/is_cefi_manifest_blank_data_type_since_2026_06_29_2026_07_06.md:130-134`: “One-off patch script shipped
  instruments-service@40bdfe1d as scripts/backfill_cefi_blank_instruments_data_type_2026_07_06.py. Contract: filter
  date>=2”
  - why: The generic-reprocessing-utility issue (filed 2026-07-07) claims an exhaustive grep found exactly 11
    near-identical one-off reclassify/reprocess scripts across the workspace, but the is_cefi-blank-data_type issue
    (filed one day earlier, 2026-07-06) documents two more scripts matching that exact recurring shape (backfil

#### [P2] active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md (intra-doc)

- finding ids: 271
- **Frontmatter status vs body completion state** —
  `active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md:29`: “status: open” vs
  `active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md:173`: “**CAS-retry lost-update race
  confirmed fixed at both the code level and the sports bucket's data level.**”
  - why: All 4 'Recommended decision' todos in the body are checked [x] ✅ with shipped commit SHAs
    (unified-trading-library@75e59a89, @84528344) and a final re-verification pass explicitly declaring the bug fixed at
    both code and data level, yet the frontmatter still declares status: open (batch header also lists it as status=o

#### [P2] active/issues/manifest_index_read_oom_canonical_cache_2026_06_24.md ↔ active/master_data_canonicalisation_migration_catalogue_2026_06_07.md

- finding ids: 131
- **Coordinator's own orphan-sweep discipline vs an unregistered open issue under the same epic** —
  `active/master_data_canonicalisation_migration_catalogue_2026_06_07.md:2122-2127`: “Swept `plans/active/*.md` +
  `plans/active/issues/*.md` for manifest/migration/catalogue/pipeline_mode/backfill/ coverage/schema themes. \*\*All
  register” vs `active/issues/manifest_index_read_oom_canonical_cache_2026_06_24.md:14,5-6`: “parent_epic:
  manifest_master ... status: open ... created: 2026-06-24 (manifest-writer OOM affecting DeFi/cefi/tradfi/sports
  backfills)”
  - why: The coordinator's own hard rule states any active data-layer plan/issue lacking a registry row is
    'review-blocking', and it promises to re-sweep at every gate promotion. The open issue
    manifest_index_read_oom_canonical_cache_2026_06_24.md (parent_epic: manifest_master, status: open, a cross-cutting
    manifest-read defect

#### [P2] active/issues/mtds_defi_catalog_reader_reads_dead_static_snapshot_path_2026_07_06.md ↔ active/mtds_file_size_refactor_2026_06_08.md

- finding ids: 186
- **"ALL MTDS ships blocked" gate vs an actual successful MTDS ship after that date** —
  `active/mtds_file_size_refactor_2026_06_08.md:38`: “the issue
  `issues/fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet_2026_06_22.md` (which blocks ALL MTDS ships) is a
  SEPARATE doc and is NOT defer” vs
  `active/issues/mtds_defi_catalog_reader_reads_dead_static_snapshot_path_2026_07_06.md:139`: “Full
  `bash scripts/quality-gates.sh` exit 0. (market-tick-data-service@f4dab8f9, shipped 2026-07-06)”
  - why: mtds_file_size_refactor (last_updated 2026-06-26) asserts a live QG-red issue blocks ALL
    market-tick-data-service ships; mtds_defi_catalog_reader shows a full green-QG MTDS ship landing 2026-07-06, ten
    days later, with no note that the blocking gate was lifted — the still-active claim in mtds_file_size_refactor now
    rea

#### [P2] active/issues/mtds_plan_reconciliation_2026_06_29.md ↔ active/tradfi_massive_dual_source_2026_05_28.md

- finding ids: 375
- **TradFi VIX/VX-futures sourcing stack — Barchart's role in the ohlcv_15m SOURCE_PRIORITY list** —
  `active/tradfi_massive_dual_source_2026_05_28.md:52-53,180`: “VX futures (CFE): Massive does NOT cover CFE. Keep
  existing pattern (Yahoo + Barchart as already wired in ("tradfi","ohlcv_15m"): ["databento","yahoo"” vs
  `active/issues/mtds_plan_reconciliation_2026_06_29.md:200`: “tradfi_massive_dual_source: M22 Operator-decision #3
  (L53) + L180 still list Barchart in the ohlcv_15m SOURCE_PRIORITY — Barchart was RETIRED 2026-06-”
  - why: tradfi_massive_dual_source_2026_05_28.md is status: active with last_updated: 2026-06-27 (3 days AFTER the
    2026-06-24 Barchart retirement + Databento-XCBF.PITCH shipment) but still asserts 'no change to the VX cell
    required' and cites the stale ['databento','yahoo','barchart'] priority list at two locations. A separate

#### [P2] active/issues/phantom_captures_sports_2026_06_28.md (intra-doc)

- finding ids: 211
- **phantom_captures_sports frontmatter status vs its own fully-checked todo list** —
  `plans/active/issues/phantom_captures_sports_2026_06_28.md:5`: “status: open” vs
  `plans/active/issues/phantom_captures_sports_2026_06_28.md:98`: “[x] ✅ [SCRIPT] P2. Apply phantom reconciliation for
  sports. **DONE 2026-06-28T04:26Z**: 27,595 phantoms flipped (cap→attempted_failed); manifest uploa”
  - why: Frontmatter declares status: open, but both todos (diagnose root cause AND apply reconciliation) are checked
    done with hard evidence (GCS upload, triage JSONL) — unlike sibling
    phantom*captures*{cefi,defi,tradfi,prediction}.md docs where 'open' correctly matches at least one genuinely
    unchecked todo, this doc gives no

#### [P2] active/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_08.md (intra-doc)

- finding ids: 85
- **frontmatter status vs fully-resolved body** — `active/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_08.md:13`:
  “status: open” vs `active/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_08.md:69`: “[x] ✅ [INFRA] P2. Set `TMPDIR`
  ... instead of relying on the default `/tmp` tmpfs ... — unified-trading-pm@0e29e6d81.”
  - why: All three recommended-decision todos (P2 TMPDIR redirect, P3 tmpfs-resize decision, P3 stale-dir cron) are
    checked done with shipped commits and closing Progress Log entries for each ('Implemented by slot-2', 'closed by
    slot-2' x2), yet the frontmatter still declares status: open rather than resolved.

#### [P2] active/issues/sports_league_id_out_of_universe_overcapture_2026_06_24.md ↔ active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md

- finding ids: 252
- **Out-of-universe overcapture issue doc still open/unresolved vs P2a's shipped write-path gate + wipe implementi** —
  `active/issues/sports_league_id_out_of_universe_overcapture_2026_06_24.md:5,18,92-96`: “status: open ... resolved_by:
  (blank) ... 4. The 1,676,612 out-of-universe rows ...: DROP from the manifest (recommended...) vs KEEP” vs
  `active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md:394-403`: “G1 wipe (Todo 1) — EXECUTED ...
  Post-wipe IS index (19:42 UTC): 2,898,902 rows — canonical only”
  - why: The issue doc's core recommendations — (1) a write-path gate restricting per-league captures to the canonical
    universe, and (4) DROP the out-of-universe rows from the manifest — are exactly what P2a's Todo #1 shipped
    (instruments-service@acfd5ac write-path gates in sports_fixtures.py/process_write.py/footystats.py/unde

#### [P2] active/layer1_remeasure_and_certify_2026_07_06.md ↔ active/tradfi_v9_stage1_finish_2026_07_06.md

- finding ids: 126
- **Tradfi orphan-sweep gate state on 2026-07-10 (585 real orphans still open vs. corpus-wide E=0 gate met)** —
  `active/layer1_remeasure_and_certify_2026_07_06.md:142-157`: “the backgrounded full orphan sweep (task 2, PID 22320)
  ... had actually COMPLETED unattended at 2026-07-10 15:57:41 UTC ... and it is **NOT E=0**: 585” vs
  `active/tradfi_v9_stage1_finish_2026_07_06.md:94-96,195-202`: “🎯 GATE MET 2026-07-10 17:17:22 UTC (slot-3
  sonnet/high) — fresh full corpus-wide re-sweep confirms `orphan_class_E=0, unknown_prefixes=0`. ... === ACC”
  - why: layer1_remeasure_and_certify's latest entry (its own 'RE-CHECKED AGAIN' continuation, referencing a 15:57:41
    UTC sweep result) asserts the orphan gate is NOT met with 585 real orphans outstanding; tradfi_v9_stage1_finish's
    later same-day entry (17:17:22 UTC, ~80 min after) shows the 585-orphan remainder was backfilled

#### [P2] active/layer1_remeasure_and_certify_2026_07_06.md ↔ epics/instruments_master.md

- finding ids: 111
- **Epic hub's auto-populated active-plan roster is stale relative to the actual current set of child plans** —
  `epics/instruments_master.md:423-424`: “\_3 active plans declare parent_epic: instruments_master in their frontmatter.
  Workers pick up in priority order (P0 first). Auto-populated by scripts/” vs
  `active/layer1_remeasure_and_certify_2026_07_06.md:29`: “parent_epic: instruments_master”
  - why: The epic's 'Assigned active plans' section names only 3 old (2026-05/06-era) plans and gives no mention at all
    of the 4 newer AO Plans (is_catalogue_completion_2d, layer1_remeasure_and_certify,
    foundation_gates_and_capture_to_100, instruments_catalogue_incremental_rollup) that all declare parent_epic:
    instruments_maste

#### [P2] active/master_to_live_defi_2026_05_23.md (intra-doc)

- finding ids: 215,368
- **frontmatter last_updated stale vs body content added/dated later** — `active/master_to_live_defi_2026_05_23.md:31`:
  “last_updated: 2026-05-11” vs `active/master_to_live_defi_2026_05_23.md:1245`: “### Group H — Per-client isolation +
  multi-venue concurrency (added 2026-05-20)”
  - why: Frontmatter declares last_updated 2026-05-11, but the body contains an entire section explicitly labeled 'added
    2026-05-20', other content dated 2026-05-24 (sports available_at rename 'FULLY SHIPPED'), and an auto-regenerated
    plan inventory whose rows are dated as late as 2026-07-09/10 — the last_updated field was neve
- **Frontmatter last_updated vs body content currency** — `active/master_to_live_defi_2026_05_23.md:31`: “last_updated:
  2026-05-11” vs `active/master_to_live_defi_2026_05_23.md:1159`: “full DART experience extension ... Target completion
  2026-07-04 (~6 weeks post-cutover).”
  - why: Frontmatter status:active/last_updated:2026-05-11 is stale by nearly two months relative to the plan's own
    body, which carries dated entries and targets well past that (e.g. a 2026-07-04 target-completion date, a 2026-06-15
    deadline at line 1866, and progress-log entries dated 2026-05-18). An agent trusting the frontma

#### [P2] active/mdps_book_microstructure_precompute_columns_2026_06_28.md (intra-doc)

- finding ids: 185
- **declared asset_group/summary scope vs actual implemented scope (class d)** —
  `active/mdps_book_microstructure_precompute_columns_2026_06_28.md:9`: “asset_group: [cefi, prediction, cross-cutting]”
  vs `active/mdps_book_microstructure_precompute_columns_2026_06_28.md:103`: “plan summary names "CeFi + prediction" but
  reality is "CeFi + DeFi (Hyperliquid via DefiBookSnapshotAdapter)" — no prediction `book_snapshot_5` adapte”
  - why: Frontmatter and summary declare scope as CeFi+prediction; the plan's own [IMPLEMENT] todo logs this as
    factually wrong (no prediction book adapter exists; actual scope is CeFi+DeFi) and explicitly defers fixing the doc
    ('logged, not fixed here') — the asset_group field other tooling/dispatch may key on is stale.

#### [P2] active/mdps_book_microstructure_precompute_columns_2026_06_28.md ↔ active/mdps_features_reduced_artifact_tracker_2026_06_28.md

- finding ids: 183
- **coordination-tracker status vs child mini-plan actual dispatch/completion state** —
  `active/mdps_features_reduced_artifact_tracker_2026_06_28.md:37`: “All born `status: draft`; flip the batch to
  `active` together to green-light dispatch.” vs `active/mdps_book_microstructure_precompute_columns_2026_06_28.md:44`:
  “Status-flip note (2026-07-10): all 6 todos confirmed [x] with cited evidence ... Flipped `status: active` →
  `complete`.”
  - why: The tracker (still status: draft, last_updated 2026-06-28) frames the 9 mini-plans as gated on an operator
    flipping the whole batch to active together; child mini-plans 1, 7 and 8 have independently progressed all the way
    through active to complete without the tracker itself ever being updated — a reader of only the tr

#### [P2] active/mdps_features_full_month_benchmark_binance_2026_06_28.md ↔ active/mdps_features_reduced_artifact_tracker_2026_06_28.md

- finding ids: 189
- **Coordination-tracker 'not dispatched, all mini-plans still draft' vs child Plan 7 already dispatched and fully** —
  `active/mdps_features_reduced_artifact_tracker_2026_06_28.md:5,34-36,142`: “status: draft ... Coordination tracker
  (not dispatched — execution_scope: local-only) ... All born status: draft; flip the batch to active together to” vs
  `active/mdps_features_full_month_benchmark_binance_2026_06_28.md:8,44`: “status: complete ... Status-flip note
  (2026-07-10): all 5 todos confirmed [x] with cited evidence ... Flipped status: active → complete.”
  - why: Same pattern as Plan 5: the tracker names mdps_features_full_month_benchmark_binance as its capstone Plan 7
    (gated on Plans 1 and 6) and claims the batch is undispatched draft work pending a coordinated flip. That plan
    independently reached status: complete on 2026-07-10 (full-month Binance benchmark run, cost model, r

#### [P2] active/mdps_features_reduced_artifact_tracker_2026_06_28.md ↔ active/mdps_polars_engine_cost_sharpening_2026_06_28.md

- finding ids: 190
- **Coordination-tracker 'not dispatched, all mini-plans still draft' vs child Plan 8 already dispatched and shipp** —
  `active/mdps_features_reduced_artifact_tracker_2026_06_28.md:5,34-36,143`: “status: draft ... Coordination tracker
  (not dispatched — execution_scope: local-only) ... All born status: draft; flip the batch to active together to” vs
  `active/mdps_polars_engine_cost_sharpening_2026_06_28.md:59-67`: “[x] Convert the candle aggregation path to
  pure-Polars lazy ... market-data-processing-service@c7e0437. Evidence: ... MDPS QG green (sentinel 3604451)”
  - why: The tracker names mdps_polars_engine_cost_sharpening as its independent, dispatch-ready Plan 8 but frames the
    whole batch as undispatched draft work awaiting a coordinated flip. That plan's own body shows all 6 todos checked
    off with real shipped commits (e.g. market-data-processing-service@c7e0437, QG green) deliverin

#### [P2] active/mdps_features_reduced_artifact_tracker_2026_06_28.md ↔ active/tradfi_mdps_passthrough_dependency_gap_2026_06_28.md

- finding ids: 188
- **Coordination-tracker 'not dispatched, all mini-plans still draft' vs child Plan 5 already dispatched and fully** —
  `active/mdps_features_reduced_artifact_tracker_2026_06_28.md:5,34-36,140`: “status: draft ... Coordination tracker
  (not dispatched — execution_scope: local-only) ... All born status: draft; flip the batch to active together to” vs
  `active/tradfi_mdps_passthrough_dependency_gap_2026_06_28.md:8,42-43`: “status: complete ... Status-flip note
  (2026-07-10): all 5 todos confirmed [x] with cited runtime evidence ... Flipped status: active → complete.”
  - why: The tracker explicitly names tradfi_mdps_passthrough_dependency_gap as its Plan 5 and states none of the nine
    mini-plans have been dispatched — they are all 'born status: draft', awaiting a coordinated batch flip to active.
    But that exact child plan independently reached status: complete with all 5 todos shipped and ve

#### [P2] active/monitoring_control_plane_master_2026_06_10.md ↔ epics/observability_master.md

- finding ids: 197
- **Epic child-plan roster is stale (index drift)** — `epics/observability_master.md:99`: “\_13 active plans declare
  `parent_epic: observability_master` in their frontmatter... Auto-populated by
  `scripts/plans/populate_epic_bodies_2026_05_21.”  vs  `active/monitoring_control_plane_master_2026_06_10.md:14`:
  “parent_epic: observability_master”
  - why: The epic's frontmatter last_updated is 2026-06-19 and its body enumerates only ~13 May-23-era (mostly archived)
    plans plus one P1 item. But at least 5 currently-active plans in this same cluster declare parent_epic:
    observability_master in their own frontmatter (monitoring_control_plane_master_2026_06_10, deployment_ob

#### [P2] active/mvp_catalogue_finalization_v10_2026_06_27.md ↔ epics/instruments_master.md

- finding ids: 117
- **Epic's auto-populated count of active child plans vs. actual number of active plans declaring this parent_epic** —
  `epics/instruments_master.md:422`: “"\_3 active plans declare `parent_epic: instruments_master` in their
  frontmatter... Auto-populated by
  `scripts/plans/populate_epic_bodies_2026_05_21.py”  vs  `active/mvp_catalogue_finalization_v10_2026_06_27.md:14`:
  “"parent_epic: instruments_master" (status: active, line 5)”
  - why: The epic's 'Assigned active plans' section, last auto-populated 2026-05-21, claims only 3 active plans declare
    parent_epic: instruments_master. In just this one reading batch, at least 5 status:active PLAN docs
    (mvp_catalogue_finalization_v10, mvp_scope_catalogue_tagging, prediction_canonical_identity_migration, canoni

#### [P2] active/org_migration_to_odumresearch_2026_06_07.md (intra-doc)

- finding ids: 79
- **Frontmatter status (active) vs the plan's own stated urgency/gating** —
  `active/org_migration_to_odumresearch_2026_06_07.md:6`: “status: active” vs
  `active/org_migration_to_odumresearch_2026_06_07.md:35`: “the rulesets justification is GONE; migration is now
  OPTIONAL/low-priority.”
  - why: The doc's frontmatter declares status: active with every Phase 0-5 todo unchecked, but the plan's own top
    banner says the migration's hard driver is gone, it is now optional/low-priority, and a 'Decision pending operator'
    on whether to even proceed is unresolved (as of the last Progress Log entry, 2026-06-07). An 'acti

#### [P2] active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md ↔ epics/predictions_master.md

> NOTE (2026-07-24): the cited plan was subsequently split 3 ways + archived per the plan line-cap remediation — see
> `plans/archive/2026_07/prediction_venue_perps_and_live_clob_depth_2026_06_20.md` (frozen) and its 3 successors
> (`prediction_perps_kalshi_polymarket_parked_2026_07_24.md`, `prediction_live_clob_depth_capture_2026_07_24.md`,
> `prediction_cross_venue_arb_and_coverage_2026_07_24.md`, all `parent_epic: predictions_master`). The finding below is
> a historical citation against the pre-split file and its line numbers are not updated.

- finding ids: 232
- **Epic child-plan index omits an entire P2 plan declaring it as parent_epic** — `epics/predictions_master.md:888-930`:
  “"Assigned active plans \_Active plans declaring `parent_epic: predictions_master`... Auto-populated... the script
  keeps it in sync from frontmatter" / ” vs `active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md:21-26`:
  “"parent_epic: predictions_master ... priority: P2 ... estimate_baseline_ai_days: 8"”
  - why: The epic's 'Assigned active plans' section claims to be auto-synced from frontmatter and lists only 3 P0 plans
    plus a single P2 sub-item (the sentinel fan-out) as the entirety of P2 work; this 213KB, ~8-AI-day plan (perps +
    live CLOB depth + a promoted-to-long-lived arb-detector production service spanning 06-20 throug

#### [P2] active/solana_defi_legacy_migration_2026_05_27.md (intra-doc)

- finding ids: 172
- **Whether the canonical Solana lending/dex-pools buckets contain migrated SOLANA rows (Gate 2/3 completeness)** —
  `active/solana_defi_legacy_migration_2026_05_27.md:147`: “lending_indices/ + dex_pools/ deferred: Gate 2 migration has
  NOT completed (canonical buckets show 0 SOLANA rows — Gate 3 cannot be verified yet).” vs
  `active/solana_defi_legacy_migration_2026_05_27.md:133`: “Gate 3 — manifest reconcile + verify ... DONE 2026-05-30 —
  MTDS@86d0113 ... lending-indices: 2,811 SOLANA rows ... dex-pools: 1,555 SOLANA rows”
  - why: Gate 4's own text (unmodified since 2026-05-28) asserts the canonical buckets show '0 SOLANA rows' and that
    Gate 3 cannot be verified, while Gate 3 (dated 2026-05-30, later) is marked ✅ DONE with concrete non-zero SOLANA
    row counts. Both are unresolved claims about the same current-state fact in the same document; Gate

#### [P2] active/solana_defi_legacy_migration_2026_05_27.md ↔ epics/mtds_mdps_master.md

- finding ids: 173
- **Drift Solana perp-DEX historical data source (S3 archive vs Helius)** — `epics/mtds_mdps_master.md:908`: “MTDS
  Solana perp DEX source wiring for all 4 venues: DRIFT (Drift S3 historical archive), MANGO V4, ZETA, FLASH REST APIs —
  emit perp_funding parquets” vs `active/solana_defi_legacy_migration_2026_05_27.md:576`: “Option 3 (Drift V2 S3
  archive) FAILS — bucket `drift-historical-data-v2` confirmed ends 2025-01-07 ... Option 2 wins architecturally”
  - why: The epic's open P2 backlog item still frames 'Drift S3 historical archive' as the intended/expected wiring
    source for DRIFT, but solana_defi_legacy_migration's Bug-D investigation confirms BOTH Drift S3 archives (V1 ending
    2025-01-08, V2 ending 2025-01-07 with no market/\* prefix at all) are dead ends, and ships a Heliu

#### [P2] active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md (intra-doc)

- finding ids: 255
- **cron pause/resume state disagreement within same doc** —
  `active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md:91`: “both crons resumed
  2026-06-25: `uts-prod-sports-scheduler-cron` ENABLED (\*/5)” vs
  `active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md:451-452`: “**PAUSED sports crons**
  (`uts-prod-sports-scheduler-cron`, `uts-prod-sports-fixtures-noon-t1-schedule`) — **named re-enable gate**”
  - why: The Execution-sequence section (item checked done) states both crons were resumed 2026-06-25 after the
    write-gate shipped and the tarball was rebuilt, but the same doc's 'Temporary states' section still lists the crons
    as currently PAUSED awaiting exactly that same re-enable gate — the doc disagrees with itself about c

#### [P2] active/sports_manifest_canonicalisation_2026_06_01.md (intra-doc)

- finding ids: 147
- **Blocker-ID inconsistency for the L6 legacy-cell decision** —
  `active/sports_manifest_canonicalisation_2026_06_01.md:2153`: “L6-legacy-only 🔴 RED | 5,793 cells (2020-06-01..08,
  ODDS_API/ODDS) — operator decision BLK-6b1bed9c pending” vs
  `active/sports_manifest_canonicalisation_2026_06_01.md:2190`: “**BLK-800ef029 resolved** (Option B: migrate first,
  then schedule E3 drain).”
  - why: The doc frames the L6 legacy-only-cells choice under ID BLK-6b1bed9c with two options: (A) migrate the 8 legacy
    days, or (B) descope/accept loss (line 1994). That 'pending' framing is repeated verbatim across at least 8 separate
    E8 audit entries through 2026-06-29 (lines 2036/2045/2072/2090/2104/2131/2153/2173/2184), a

#### [P2] active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md ↔ epics/sports_master.md

- finding ids: 262
- **sports_master epic VM assignment** — `epics/sports_master.md:39`: “assigned_vm: vm-sports” vs
  `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:208-210`: “Role-based dispatch -- NO epic VM
  (single-VM architecture, 2026-06-27) ... epic VMs deprecated per CLAUDE.md; there is no `vm-sports` to start.”
  - why: The hub epic's own frontmatter still names the deprecated per-epic VM `vm-sports` as its assigned_vm, while the
    coordinator plan under the same epic explicitly states epic VMs are deprecated and 'there is no vm-sports to start'
    -- the epic's own metadata field was never migrated to the {planning, NA} scheme.

#### [P2] active/uac_coverage_90pct_2026_06_10.md ↔ epics/client_isolation_and_governance_master.md

- finding ids: 34
- **Epic's related_plans / priority sections never actually enumerate the uac_coverage_90pct plan** —
  `epics/client_isolation_and_governance_master.md:29-34`: “related_plans: [
  ../active/per_client_isolation_and_venue_fanout_topology_2026_05_20.md,
  ../active/global_ledger_pnl_attribution_discovery_2026_05_21.” vs `active/uac_coverage_90pct_2026_06_10.md:14`:
  “parent_epic: client_isolation_and_governance_master”
  - why: uac_coverage_90pct_2026_06_10.md declares itself a P1 child of this epic and is status:active, but it is absent
    from the epic's related_plans frontmatter and from every priority section body (P0/P1/P2/P3 all read either empty or
    list unrelated items); the epic's own auto-populated 'Assigned active plans' block claims '

#### [P2] active/v2_engine_venue_buildout_2026_06_15.md ↔ epics/strategy_master.md

- finding ids: 298
- **epic's '8 active plans' count is stale — this batch alone has 5+ additional active/open docs declaring parent\_** —
  `epics/strategy_master.md:99`: “\_8 active plans declare `parent_epic: strategy_master` in their frontmatter. Workers
  pick up in priority order (P0 first). Auto-populated by
  `scripts/”  vs  `active/v2_engine_venue_buildout_2026_06_15.md:14`: “parent_epic: strategy_master”
  - why: Epic last_updated is 2026-06-11 and its assigned-plans index still says '8 active plans' (auto-populated
    2026-05-21), but v2_engine_venue_buildout (created 2026-06-15), defi_collateral_sizing (2026-06-17),
    e2e_defi_config_taxonomy (2026-06-17), archetype_venue_universe (2026-06-30), and ui_coverage_ts (2026-07-10) all

#### [P2] archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md ↔ epics/mtds_mdps_master.md

- finding ids: 140
- **Epic child-plan status/ownership vs the child plan's own frontmatter** — `epics/mtds_mdps_master.md:729-731`: “###
  [`live_pipeline_mtds_mdps_features_2026_05_08`]... **status**: active” vs
  `archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md:5,15-16`: “status: complete ... epic: epic-deployment
  ... parent: master_to_live_defi_2026_05_23”
  - why: Same class of drift as the workspace_qg_sweep item: epic P0 table says 'active' for a plan whose own
    frontmatter says complete and whose epic/parent fields point to epic-deployment, not mtds_mdps_master (the plan
    doesn't even carry a parent_epic: mtds_mdps_master field). The epic's index is stale/wrong on ownership and

#### [P2] epics/README.md ↔ epics/escalation_and_disaster_recovery_master.md

- finding ids: 10002
- **epic-registry completeness** — `epics/README.md:164,166-187`: “## 20 epics in 5 tiers | # | Tier | Epic slug |
  Assigned VM | Owns |” vs `epics/escalation_and_disaster_recovery_master.md:7,15,17-19`: “status: active ... created:
  2026-06-25 ... tier: L4 priority: P1 assigned_vm: vm-cross-cutting”
  - why: README's canonical 20-epic table (and the paired 'VM topology (10 VMs serving 20 epics)' table naming
    vm-cross-cutting's owned epics as only
    infrastructure_master/observability_master/batch_live_symmetry_master/client_isolation_and_governance_master) omits
    escalation_and_disaster_recovery_master, a real active L4/P1 ep

#### [P2] epics/README.md ↔ epics/global_ledger_pnl_attribution_master.md

- finding ids: 10003
- **epic count self-citation drift** — `epics/README.md:164`: “## 20 epics in 5 tiers” vs
  `epics/global_ledger_pnl_attribution_master.md:147`: “co-located with `execution_master` + `strategy_master` +
  `trading_agent_master` (per `README.md` § "19 epics in 5 tiers").”
  - why: global_ledger_pnl_attribution_master.md (status: active) cites README.md's section header verbatim as '19 epics
    in 5 tiers', but the live README.md header at line 164 reads '20 epics in 5 tiers' -- the count changed and this
    active epic's own body was never updated to match, a stale cross-reference to a numeric fact ab

#### [P2] epics/dart_and_promote_master.md (intra-doc)

- finding ids: 310,386
- **Intra-doc repos facet omits a repo the body's HARD RULE requires gating on** —
  `epics/dart_and_promote_master.md:12`: “repos: [alerting-service, deployment-api, deployment-ui,
  unified-trading-system-ui]” vs `epics/dart_and_promote_master.md:71`: “any UI repo (unified-trading-system-ui,
  deployment-ui, user-management-ui) MUST pass the playwright verification gate”
  - why: The epic's own repos: frontmatter facet — the grep-native L1 index key agents use per the retrieval model
    documented in agent_operating_framework_master.md — lists only 4 repos and omits user-management-ui, yet the epic's
    own 'UI Verification Contract (HARD RULE)' body text explicitly requires every UI-touching todo in
- **Epic's declared repo scope (frontmatter) vs its copy-pasted playwright-gate scope (body) re: user-management-u** —
  `epics/dart_and_promote_master.md:12`: “repos: [alerting-service, deployment-api, deployment-ui,
  unified-trading-system-ui]” vs `epics/dart_and_promote_master.md:70-72`: “All active plans under this epic that touch
  any UI repo (`unified-trading-system-ui`, `deployment-ui`, `user-management-ui`) MUST pass the playwright ”
  - why: The same HARD RULE paragraph (copy-pasted verbatim from deployment_and_user_management_master.md) names
    user-management-ui as a gated UI repo for the DART/promote epic even though this epic's declared `repos:` field
    never lists it and its 'Owns' line (DART cockpit + ManualTradeGateDialog + promote workflow) doesn't cla

#### [P2] epics/dart_and_promote_master.md ↔ epics/global_ledger_pnl_attribution_master.md

- finding ids: 10008
- **Dangling frontmatter reference: the global-ledger discovery plan was archived but 6 of the 7 handshake-partner** —
  `epics/global_ledger_pnl_attribution_master.md:83`:
  “[`global_ledger_pnl_attribution_discovery_2026_05_21`](../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md)”
  vs `epics/dart_and_promote_master.md:19`: “../active/global_ledger_pnl_attribution_discovery_2026_05_21.md,”
  - why: global_ledger_pnl_attribution_master.md's own body (lines 83, 112) and frontmatter (line 18) correctly link the
    discovery plan at `../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md`, and the file only
    exists on disk at `plans/archive/2026_05/...` (confirmed: no file at `plans/active/global_ledger

#### [P2] epics/defi_master.md (intra-doc)

- finding ids: 40
- **Epic's own P0 dispatch table labels an archived plan 'status: active'** — `epics/defi_master.md:1699`: “###
  [`defi_mtds_subgraph_and_adapter_fixes_2026_06_20`](../archive/2026_06/defi_mtds_subgraph_and_adapter_fixes_2026_06_20.md)”
  vs `epics/defi_master.md:1701`: “status: active · estimate: 3.2 cal AI-days (class: refactor). DEX-swaps subgraph
  schema rewrite (PancakeSwap/SushiSwap/Aerodrome/Camelot) + Compound V”
  - why: The epic's '## Assigned active plans' P0 section links to a child plan whose own path is under archive/2026_06/
    (i.e., already archived), immediately followed by a 'status: active' label and a live estimate/priority — an agent
    trusting the epic's P0 dispatch table could attempt to dispatch work from a plan that has act

#### [P2] epics/execution_master.md ↔ epics/global_ledger_pnl_attribution_master.md

- finding ids: 312
- **global_ledger_pnl_attribution_discovery plan location/status** — `epics/execution_master.md:17`: “related: [...,
  ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md]” vs
  `epics/global_ledger_pnl_attribution_master.md:85`: “**status**: ✅ ARCHIVED 2026-05-23 — 36/38 BACKED + 2/38 PARTIAL.
  Operator [ack] pending on Phase 3/5/6”
  - why: execution_master's frontmatter (related + related_plans) still cites this plan under plans/active/ (path
    confirmed non-existent on disk), while global_ledger_pnl_attribution_master correctly shows it archived to
    plans/archive/2026_05/ on 2026-05-23 — a dangling stale reference in execution_master that hasn't been updat

#### [P2] epics/global_ledger_pnl_attribution_master.md (intra-doc)

- finding ids: 315
- **assigned-active-plan count vs actual plan list (intra-doc)** — `epics/global_ledger_pnl_attribution_master.md:78`:
  “_2 active plans declare `parent_epic: global_ledger_pnl_attribution_master`. Workers pick up in priority order (P0
  first)._” vs `epics/global_ledger_pnl_attribution_master.md:92`: “**status**: ✅ ARCHIVED 2026-05-23 — Stub plan; all
  27 items DEFERRED-OPERATOR-DECISION”
  - why: The banner claims 2 active child plans, but both plans actually listed (discovery and migration) are marked ✅
    ARCHIVED with 0 and 0/27 items respectively — no active plan is shown, so the auto-populated count contradicts the
    body it sits above.

#### [P2] epics/infrastructure_master.md (intra-doc)

- finding ids: 61,69
- **Epic 'must complete' P0 section lists only already-archived/complete plans** — `469`: “## P0 — must complete before
  next foundation gate” vs `471-473`: “workspace_qg_sweep_2026_05_23 ... **status**: ✅ ARCHIVED 2026-05-26 — All items
  completed.”
  - why: The epic's own 'Assigned active plans' > 'P0 — must complete before next foundation gate' heading implies live,
    outstanding work, yet every entry listed under it (workspace_qg_sweep_2026_05_23,
    audit03_deployment_cron_provisioning_2026_05_22, defi_coverage_capability_alignment_2026_05_22) is itself marked ✅
    ARCHIVED/DO
- **epic frontmatter internal date inconsistency** — `epics/infrastructure_master.md:35`:
  “../active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md,” vs `epics/infrastructure_master.md:42`: “last_updated:
  2026-06-19”
  - why: The epic's own `related_plans` list references a plan created 2026-06-30, eleven days after the epic's declared
    `last_updated: 2026-06-19` — the last_updated stamp was not bumped when the frontmatter list was edited, making the
    freshness field unreliable for anyone deciding whether to re-read the epic.

#### [P2] epics/infrastructure_master.md ↔ epics/manifest_master.md

- finding ids: 318,319,343
- **gate_3_phantom_audit_runbook_2026_05_13 status** — `epics/infrastructure_master.md:668`: “Gate 3 phantom-audit
  execution runbook — one-shot phantom reconciliation pre-2026-05-15 freeze gate | Active” vs
  `epics/manifest_master.md:168`: “**status**: ✅ ARCHIVED 2026-05-21 — Gate 3 FIRED 2026-05-17; 0 phantoms all 5
  asset_groups”
  - why: infrastructure_master (last_updated 2026-06-19, over a month after archival) still lists this plan as 'Active'
    with an ../active/ link, while manifest_master (its true owner) shows it archived 2026-05-21 with an ../archive/
    link. An agent following infra_master's table would look for a non-existent active plan and coul
- **current manifest schema version** — `epics/infrastructure_master.md:644`: “Manifest schema v8 + 4-state
  `capture_status` + per-asset-group bucket layout” vs `epics/manifest_master.md:55`: “manifest schema (**v9 current** —
  `MANIFEST_SCHEMA_VERSION = 9` live 2026-05-30, UTL@`c7bfa427`”
  - why: infrastructure_master's Codex-SSOT table (as of its own last_updated 2026-06-19) still describes the manifest
    schema as v8, while manifest_master — the schema's actual epic owner — states v9 has been live workspace-wide since
    2026-05-30, three weeks before infra_master's last edit. The two active docs disagree on a loa
- **manifest schema version currently live (v8 vs v9)** — `epics/infrastructure_master.md:644`:
  “/codex/02-data/availability-manifest-and-data-status.md ... 'Manifest schema v8 + 4-state `capture_status` +
  per-asset-group bucket layout'” vs `epics/manifest_master.md:55`: “**Owns**: manifest schema (**v9 current** —
  `MANIFEST_SCHEMA_VERSION = 9` live 2026-05-30, UTL@`c7bfa427`...”
  - why: Both are active L1/L4 epics. infrastructure_master.md's 'Codex SSOTs' table (last_updated 2026-06-19, three
    weeks after v9 shipped 2026-05-30) still describes the manifest schema doc as owning 'v8', while manifest_master.md
    (the dedicated manifest epic) and numerous active plans (tradfi_manifest_canonicalisation, predi

#### [P2] epics/instruments_master.md (intra-doc)

- finding ids: 96
- **Plan location (archive/) vs declared status (ACTIVE)** — `epics/instruments_master.md:428`: “###
  [`workspace_qg_sweep_2026_05_23`](../archive/2026_05/workspace_qg_sweep_2026_05_23.md) — instruments-service cluster”
  vs `epics/instruments_master.md:430`: “**status**: 🟠 ACTIVE — QG sweep for instruments-service (32 ruff errors).
  `bash scripts/quality-gates.sh` exit 0.”
  - why: The plan is linked from an archive/2026_05/ path (implying archived/closed) yet the epic's own status line
    calls it ACTIVE with an open task — an agent could be misdirected about whether this work is still live or
    historical.

#### [P2] epics/manifest_evolution_SUPERSEDED_2026_05_21.md ↔ epics/manifest_master.md

- finding ids: 322
- **ownership of IS↔MTDS contract enforcement work (incl. folded child `is_mtds_contract_audit_2026_05_20`)** —
  `epics/manifest_evolution_SUPERSEDED_2026_05_21.md:64-65`: “All open scope (schema v8, honest absence taxonomy, writer
  code, GCS data layout, IS↔MTDS contract enforcement) continues there.” vs `epics/manifest_master.md:105`: “**Upstream
  gates**: `instruments_master` (IS→MTDS contract; archive-metadata fields on `InstrumentRecord`)”
  - why: The supersession banner explicitly says IS↔MTDS contract enforcement (one of the 11 folded child plans)
    continues inside manifest_master. But manifest_master's own body never lists `is_mtds_contract_audit_2026_05_20`
    among its child plans and instead treats 'IS→MTDS contract' as an upstream item owned by instruments_ma

#### [P2] epics/manifest_master.md (intra-doc)

- finding ids: 321
- **manifest_master's own 'active plan count' claim vs body reality** — `epics/manifest_master.md:115`: “_7 active plans
  declare `parent_epic: manifest_master` in their frontmatter (verified 2026-06-30)._” vs
  `epics/manifest_master.md:122`: “**status**: ✅ ARCHIVED 2026-05-21 — Phases 1-3 done (100% v8 dist confirmed); Phase
  4 BLOCKED-OPERATOR-DECISION”
  - why: The auto-populated blurb claims 7 active child plans as of 2026-06-30, but every single plan enumerated in the
    P0/P1/P2/Archived sections beneath it (d3_manifest_v8_finish, d5_features_missing_data_downgrade,
    expected_unattempted_propagation_chain, gcs_migration_bundle, honest_coverage_formula_consolidation, manifest_s

#### [P2] epics/orchestrator_master.md (intra-doc)

- finding ids: 325
- **frontmatter last_updated vs body content dates** — `epics/orchestrator_master.md:51`: “last_updated: 2026-05-21” vs
  `epics/orchestrator_master.md:440`: “"DONE 2026-06-10 — `agent-orchestrator@68116f7`."”
  - why: Frontmatter declares the doc last touched 2026-05-21, but the body contains multiple sections dated as late as
    2026-06-07/06-08/06-10 (tab-mirror crash fix, auth_failed cooldown fix, WorkerLivenessWatchdog fix) — the
    frontmatter field is stale by ~3 weeks relative to the doc's own most recent content.

#### [P2] epics/plan_hygiene_master.md (intra-doc)

- finding ids: 326
- **frontmatter last_updated vs body content dates** — `epics/plan_hygiene_master.md:29`: “last_updated: 2026-05-23” vs
  `epics/plan_hygiene_master.md:158-165`: “"DEFERRED items with placeholder successors — resolved per-item audit
  2026-06-25"”
  - why: Frontmatter last_updated is 2026-05-23 but the body's "Findings — 2026-06-01 cross-plan deviation sweep"
    section and its 2026-06-25 per-item audit resolution post-date the declared last_updated by over a month.

#### [P2] epics/trading_agent_master.md (intra-doc)

- finding ids: 334
- **Auto-populated 'active plans' count vs the only listed child's actual archived status** —
  `epics/trading_agent_master.md:41`: “_1 active plans declare `parent_epic: trading_agent_master` in their frontmatter.
  Workers pick up in priority order (P0 first)._” vs `epics/trading_agent_master.md:48`: “**status**: ✅ ARCHIVED
  2026-05-23 — Phases 1-8 complete: directive pipeline + event contracts + UAC schema + codex SSOT shipped.”
  - why: The auto-generated 'Assigned active plans' header claims 1 active child plan, but the only plan listed under it
    is explicitly marked ARCHIVED. An agent trusting the header count (e.g. a dispatcher scanning epic summaries) would
    believe there is live work here when the sole child is closed; the epic's P1-P3 sections are

#### [P2] manifest_hygiene_red_2026_07_03.md ↔ plans/active/issues/audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md

- finding ids: 391
- **mechanical:dangling_ref** —
  `plans/active/issues/audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md:23`: “related:
  [../data_pipeline_hardening_self_monitoring_2026_06_22.md, manifest_hygiene_red_2026_07_03.md]” vs `-`: “file not
  found anywhere under plans/ (no manifest_hygiene_red_2026_07_03.md exists in active/issues, archive/issues, or
  archive; nearest matches are d”
  - why: The related field cites a specific issue doc by filename that does not exist anywhere in the plans corpus. The
    referencing doc's own body explains this is because the 2026-07-03 escalation artifact was left dirty/untracked and
    later wiped by a tree-clean before being committed (illustrating the very bug the issue descr

#### [P2] plans/PLAN_FORMAT.md ↔ plans/active/mvp_reconciliation_closeout_v10_2026_06_27.md

- finding ids: 383
- **SSOT location for the plan-archival '5-step ritual'** —
  `plans/active/mvp_reconciliation_closeout_v10_2026_06_27.md:47`: “`plans/PLAN_FORMAT.md` + `plans/epics/README.md` —
  archival 5-step ritual; plan-hygiene QG.” vs `plans/PLAN_FORMAT.md:57-69`: “## Archive Criteria by Plan Type ...
  **Archive eligibility rule:** A plan is eligible for archive when ALL repos in `repo_gates` have reached the gate”
  - why: Multiple active docs (this one and active/issues/plan_issue_epic_consolidation_2026_06_30.md:191) cite
    PLAN_FORMAT.md + epics/README.md as the SSOT housing the 'archival 5-step ritual' (migrate DEFERRED → banner →
    codex-alignment check → update CLAUDE.md/codex → clear lock). PLAN_FORMAT.md's actual archival content is

#### [P2] plans/active/bucket_env_split_rollout_2026_06.md ↔ plans/epics/infrastructure_master.md

- finding ids: 356
- **Epic's related_plans list vs. child plans' declared parent_epic** — `plans/epics/infrastructure_master.md:26-40`:
  “related_plans: [mvp_reconciliation_closeout_v10_2026_06_27.md, cicd_mvp_ldr_to_main_pipeline_2026_06_30.md, ...] (no
  mention of bucket_env_split_rollo” vs `plans/active/bucket_env_split_rollout_2026_06.md:18`: “parent_epic:
  infrastructure_master”
  - why: Both bucket_env_split_rollout_2026_06.md and bucket_iam_write_protection_per_tier_2026_06_09.md (both status:
    active, P1, locked_by live-defi-rollout since 2026-06-09) declare parent_epic: infrastructure_master, but
    infrastructure_master.md's related_plans/related frontmatter list (lines 15-21, 26-33) does not include

#### [P2] plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md ↔ plans/epics/infrastructure_master.md

- finding ids: 354
- **Current SSOT location/owner for bucket naming (which doc 'owns' the bucket-naming SSOT)** —
  `plans/epics/infrastructure_master.md:645`: “`plans/archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md` |
  Bucket naming SSOT (`resolve_bucket_name()` only; never inline `gs://` f-str” vs
  `plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md:427-428`: “UAC is now named the canonical
  SSOT in `cursor-configs/CLAUDE.md` § Bucket-name SSOT + `/codex/02-data/bucket-naming-and-config.md`
  (deployment-service”
  - why: infrastructure_master's own 'Codex SSOTs' table (a list of docs that supposedly still 'own' live conventions)
    lists an ARCHIVED plan as the thing that 'Owns' the bucket-naming SSOT, with no pointer to the actual current SSOT
    location. bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md (active, P0, same corpus

#### [P2] plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md ↔ plans/epics/mtds_mdps_master.md

- finding ids: 355
- **Epic's child-plan tracking vs. an active plan's declared parent_epic** — `plans/epics/mtds_mdps_master.md:37`:
  “related: [..., bucket_name_ssot_canonicalisation_2026_05_10.md, ...]” vs
  `plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md:19`: “parent_epic: mtds_mdps_master”
  - why: bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md is a P0, actively-locked (locked_since
    2026-06-01), 557-line plan that declares mtds_mdps_master as its parent_epic and explicitly 'reopens' the archived
    plan the epic still lists in its related/frontmatter. Yet mtds_mdps_master.md never references bucket_nam

#### [P3] active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md (intra-doc)

- finding ids: 352
- **Doc's own '## Codex SSOTs' header list left uncorrected against its own later self-correction** —
  `active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md:265`:
  “`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch + regen + ingestion contract.” vs
  `active/ao_dispatch_correctness_regen_reconcile_2026_07_07.md:709-711`: “real doc is
  `/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md`, not the stale
  `12-agent-workflow/...single-vm-architecture.md` in t”
  - why: This still-active plan's Progress Log entry explicitly flags its own Codex-SSOTs section's citation as stale
    and names the real replacement doc, but the '## Codex SSOTs' header block itself (line 265) was never edited to drop
    or replace the flagged citation — a self-acknowledged drift left live and uncorrected in the s

#### [P3] active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md (intra-doc)

- finding ids: 24
- **last_updated frontmatter vs progress-log status-flip date (intra-doc)** —
  `active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:24`: “last_updated: 2026-07-08” vs
  `active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:84`: “**2026-07-10** — **Status-flip note**: all 4
  todos confirmed `[x]` with cited evidence ... Flipped `status: active` → `complete`.”
  - why: The frontmatter `last_updated` field still reads 2026-07-08 even though the doc's own Progress Log records a
    status change (active→complete) two days later on 2026-07-10 — the frontmatter timestamp wasn't bumped alongside the
    status flip.

#### [P3] active/is_catalogue_completion_2d_2026_07_06.md (intra-doc)

- finding ids: 112
- **Frontmatter last_updated predates the doc's own newest Progress Log entries** —
  `active/is_catalogue_completion_2d_2026_07_06.md:28`: “last_updated: 2026-07-06” vs
  `active/is_catalogue_completion_2d_2026_07_06.md:314`: “- **2026-07-07** — **B2 downstream FLIPPED (slot-2
  opus/max).** Wired enumerate_expected_universe.py to the shipped UAC SSOT”
  - why: The frontmatter declares last_updated: 2026-07-06, but the body's Progress Log contains multiple entries dated
    2026-07-07 (B2 downstream flip, MVP-tagging-verify fix) that are chronologically after the declared last-updated
    date — a stale metadata field on the doc's own record of its latest edits.

#### [P3] active/issues/cefi_layer1_denominator_gaps_2026_07_03.md (intra-doc)

- finding ids: 63
- **Frontmatter last_updated predates a body entry dated after it** — `43`: “last_updated: 2026-07-06” vs `208`:
  “COINBASE / DERIBIT-COMBO MVP_SCOPE membership — RESOLVED 2026-07-10 (operator decision #6: "keep both declared")”
  - why: The frontmatter's last_updated field (2026-07-06) is earlier than a body todo explicitly dated 2026-07-10
    (operator decision #6 resolving the COINBASE/DERIBIT-COMBO MVP_SCOPE question), meaning the doc was substantively
    edited after the recorded last_updated timestamp without the field being bumped. Any tooling that us

#### [P3] active/issues/fleet_data_acquisition_health_2026_06_21.md (intra-doc)

- finding ids: 81
- **Frontmatter last_updated date vs a later dated body revision** —
  `active/issues/fleet_data_acquisition_health_2026_06_21.md:30`: “last_updated: 2026-06-27” vs
  `active/issues/fleet_data_acquisition_health_2026_06_21.md:56`: “REVISED 2026-07-10 (operator): fix properly, don't
  paper over the inconsistency with a tolerant fallback.”
  - why: The frontmatter claims the doc was last touched 2026-06-27, but the body contains a revision explicitly dated
    2026-07-10 (13 days later) revising the recommended fix for bug #2. The last_updated field was not bumped when the
    body was edited, so any staleness/triage tooling keying off last_updated would under-count this

#### [P3] active/issues/instrument_id_format_canonicalization_2026_07_08.md (intra-doc)

- finding ids: 97
- **Section header claims 6 findings; body enumerates 8** —
  `active/issues/instrument_id_format_canonicalization_2026_07_08.md:73`: “## The 6 real divergences found, and their
  target canonical format” vs `active/issues/instrument_id_format_canonicalization_2026_07_08.md:219`: “8. **RESOLVED
  2026-07-08 (was: "Prediction's per-market instrument_id is genuinely opaque, and its enrichment columns are 100%
  empty").**”
  - why: The doc's section header still says '6 real divergences' but findings 7 and 8 were added later per this doc's
    own Progress Log — cosmetic count drift that could make a skimming reader underestimate scope.

#### [P3] active/issues/instruments_remaining_work_audit_2026_07_10.md ↔ active/tradfi_v9_stage1_finish_2026_07_06.md

- finding ids: 107
- **tradfi_v9_stage1_finish open-task count (6 of 11) and orphan-sweep blocking-reason vs the plan's own current c** —
  `active/issues/instruments_remaining_work_audit_2026_07_10.md:347-350`: “tradfi_v9_stage1_finish — AO Plan 2 ... 6 of
  11 unchecked ... orphan sweep (blocked on manifest rebuild ordering), straggler VM re-run ...” vs
  `active/tradfi_v9_stage1_finish_2026_07_06.md:94-215`: “🎯 GATE MET 2026-07-10 17:17:22 UTC ... orphan_class_E=0 ...
  Checkbox FLIPPED — the literal gate is genuinely, corpus-wide met”
  - why: By the time task 2 (orphan sweep) checkbox is flipped done, only 5 of 11 tasks remain unchecked (3,4,6,10,11),
    not 6, and the sweep is no longer 'blocked on manifest rebuild ordering' (that ordering block was resolved back on
    2026-07-07 per the plan's own history). This may simply reflect the audit doc being authored e

#### [P3] active/issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md (intra-doc)

- finding ids: 231
- **Self-contradictory 'stale path' description within Finding 1** —
  `active/issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md:66`: “Rewrite all four referrers
  `architecture-v2/cross-cutting/pnl-attribution.md` → `architecture-v2/cross-cutting/pnl-attribution.md`.” vs
  `active/issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md:43`: “The actual doc lives at
  **`/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`** (64 KB, the canonical PnL-attribution SSOT)”
  - why: The doc's own recommended-decision line instructs rewriting a path into the identical path (X → X), and the
    sentence introducing the 'correct' target repeats the exact same path string used earlier as 'does not exist'. The
    described stale path was almost certainly `operational/pnl-attribution.md` but an edit pass appea

#### [P3] active/issues/sports_data_capture_gap_2026_06_29.md (intra-doc)

- finding ids: 280
- **Frontmatter date ordering (last_updated / locked_since predate created)** —
  `active/issues/sports_data_capture_gap_2026_06_29.md:13`: “created: 2026-06-29” vs
  `active/issues/sports_data_capture_gap_2026_06_29.md:23-24`: “last_updated: 2026-06-27 locked_since: 2026-05-21”
  - why: The doc's own frontmatter has last_updated (2026-06-27) and locked_since (2026-05-21) both before its created
    date (2026-06-29), which is internally impossible and indicates copy-pasted/unmaintained frontmatter dates.

#### [P3] active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md (intra-doc)

- finding ids: 266
- **impossible frontmatter date ordering** —
  `active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md:20`: “created: 2026-06-29” vs
  `active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md:30-31`: “last_updated: 2026-06-27
  locked_since: 2026-05-21”
  - why: last_updated (2026-06-27) and locked_since (2026-05-21) both predate the doc's own created date (2026-06-29),
    which is logically impossible -- a copy-paste frontmatter error that would mislead any date-based sorting/staleness
    tooling.

#### [P3] active/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md (intra-doc)

- finding ids: 307
- **Frontmatter/lede summary stale vs. body's own resolution progress** —
  `active/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md:4`: “The tradfi `expected_unattempted` (EU) is
  dead-flat at **1,084,542** while a multi-VM CME/NYSE/NASDAQ databento backfill campaign burns compute.” vs
  `active/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md:140`: “EU journey: 1,084,542 → 336,061 (massive)
  → 1,349 (MVP).”
  - why: The doc's frontmatter `summary:` and opening line still describe the EU as 'dead-flat at 1,084,542', but the
    doc's own later Progress Log records that the same session drove EU down to 336,061 and then to a durable 1,349 via
    an executed operator decision + code fixes. The headline framing (still the first thing a reade

#### [P3] active/prediction_capture_incident_remediation_2026_07_06.md (intra-doc)

- finding ids: 373
- **Freshness of the plan's own frontmatter metadata vs. its Progress Log** —
  `active/prediction_capture_incident_remediation_2026_07_06.md:52 (frontmatter last_updated)`: “last_updated:
  2026-07-06” vs `active/prediction_capture_incident_remediation_2026_07_06.md:264-272`: “2026-07-10 — Phase 0 CLOSED
  for real (sub-agent verification pass, part of the instruments-completion-tracker sweep). ... read
  gs://market-data-tick-c”
  - why: The plan's frontmatter last_updated field (2026-07-06) disagrees with its own body, which carries a substantive
    Progress Log entry dated 2026-07-10 (a Phase-0 closure verification with new evidence). A doc-freshness/index
    consumer (e.g. the L0 doc index or a staleness check) reading only the frontmatter would treat thi

#### [P3] active/sports_p1_golden_window_features_2026_06_27.md (intra-doc)

- finding ids: 263
- **P1d frontmatter last_updated vs body Progress Log** — `active/sports_p1_golden_window_features_2026_06_27.md:21`:
  “last_updated: 2026-06-27” vs `active/sports_p1_golden_window_features_2026_06_27.md:459`: “### 2026-07-03 -- slot 5:
  Todo 4 (feature manifest clean) COMPLETE”
  - why: Frontmatter claims the doc was last updated 2026-06-27, but the body's own Progress Log contains dated entries
    through 2026-07-03 (and several 2026-06-29 entries) -- the last_updated field was never refreshed despite
    substantial later edits, which is misleading to any tooling or reviewer sorting/trusting that field.

#### [P3] active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md (intra-doc)

- finding ids: 253
- **Item #7's stale un-block-sequence text vs item #4 now being flipped done** —
  `active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md:176-178`: “BLOCKED-PREREQUISITES
  (2026-07-08, slot-7)... item #4 and #5 must both reach pending_fetch=0 before this item can flip” vs
  `active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md:1140`: “Gate MET — flipped item #4's
  checkbox ✅.”
  - why: Item #7's bullet text (last edited 2026-07-08) still frames itself as blocked on BOTH item #4 (understat) and
    item #5 (footystats), but the 2026-07-09 progress-log entry flipped item #4 to done — the item #7 checkbox/bullet
    was never rewritten to reflect that only item #5 now blocks it. Cosmetic/staleness rather than a

#### [P3] active/sports_reference_backfill_oom_2026_06_22.md (intra-doc)

- finding ids: 281
- **Plan status vs all-todos-done body** — `active/sports_reference_backfill_oom_2026_06_22.md:9`: “status: active” vs
  `active/sports_reference_backfill_oom_2026_06_22.md:63-80`: “[x] [SCRIPT] P1. Fix per-league skip-check to single
  index read... [x] [SCRIPT] P2. **DONE** Column-prune slim reads via `read_availability_index(colu”
  - why: Every todo in the plan body (including the follow-up marked 'DONE') is checked with shipped commit evidence and
    no remaining open item, but the frontmatter status is still 'active' rather than 'complete' — plan-hygiene drift
    that could cause the item to look like open work.

#### [P3] archive/2026_05/mtds_per_instrument_download_api_2026_04_24.md ↔ epics/mtds_mdps_master.md

- finding ids: 141
- **Epic child-plan status vs the child plan's own frontmatter** — `epics/mtds_mdps_master.md:799-801`: “###
  [`mtds_per_instrument_download_api_2026_04_24`]... **status**: active” vs
  `archive/2026_05/mtds_per_instrument_download_api_2026_04_24.md:5`: “status: complete”
  - why: A third instance of the same systemic pattern: the epic's index still marks this archived/complete plan
    'active', confirming the epic's child-status table is stale across multiple entries, not a one-off typo.

#### [P3] epics/batch_live_symmetry_master.md (intra-doc)

- finding ids: 311
- **Stale 'stub, not yet filled' banner left in place on a heavily-populated, recently-updated epic** —
  `epics/batch_live_symmetry_master.md:49`: “Status: stub created 2026-05-21 by migrate_epics_2026_05_21.py. Operator
  fills body with P0/P1/P2/P3 priority blocks listing all assigned active plans” vs
  `epics/batch_live_symmetry_master.md:75`: “2026-07-08 canonical instrument_id — live!=batch findings”
  - why: The doc still carries its original 2026-05-21 auto-generated 'stub created... Operator fills body' placeholder
    line as if the body were still empty, but the same document (last_updated 2026-07-08 per frontmatter) already
    contains detailed P0 findings, P1 BLRS recon-gate todos, and multiple archived-plan summaries below

#### [P3] epics/features_and_ml_master.md (intra-doc)

- finding ids: 317
- **frontmatter last_updated vs body edit date (intra-doc)** — `epics/features_and_ml_master.md:52`: “last_updated:
  2026-05-21” vs `epics/features_and_ml_master.md:211`: “## Tier-violation cleanup (slot 7, 2026-06-01 — surfaced during
  dependency-alignment)”
  - why: Two whole sections (Tier-violation cleanup; DeFi data-loading dispatch) are dated 2026-06-01, after the
    frontmatter's last_updated of 2026-05-21 — stale metadata that understates how recently the doc was actually edited.
