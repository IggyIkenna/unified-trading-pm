---
doc_type: issue
title: Plan reconciler findings — sports tranche (agt-132fc8)
summary:
  Run-findings doc for the sports-tranche sharded daily reconciliation (dispatch agt-132fc8, 2026-08-06). Hunter fan-out
  DETECT → adversarial VERIFY → apply confirmed → route hard items. Live journal for the run.
status: open
resolved_by:
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, findings, sports, reconciliation]
related: [/plans/epics/sports_master.md]
parent_epic: sports_master
priority: P2
assigned_vm: NA
created: 2026-08-06
author: plan_reconciler
source: agt-132fc8
locked_by: plan_reconciler
---

# Plan reconciler run-findings — sports tranche (agt-132fc8)

> Live journal for the 2026-08-06 sports-tranche reconciliation shard. Sections are appended as the run progresses.
> Normative refs (PLAN_FORMAT.md / task_template.md / INDEX.md / ACTIVE_INDEX.md) + codex stay in scope per the
> sharded-run contract; audit corpus = `asset_group: sports` docs in `plans/active/` + `plans/active/issues/` +
> `plans/epics/sports_master.md`.

## Coverage (hunters / batches / docs)

**Corpus** (2026-08-06, from `rg -l '^asset_group:.*sports'` over `plans/active/` + `plans/active/issues/` +
`plans/epics/`): 82 docs = 1 epic (`sports_master.md`, 168.5 KB) + 28 active plans + 53 issues. **Non-grace working set
= 53 docs (1.96 MB)**, grace set (newest git change <12h, context-only) = 29 docs + this findings doc.

**Hunter fan-out plan (10 hunters, all read-only, sonnet, SUB_AGENT_MANDATORY_RULES injected):**

| Hunter            | Batch                         | Docs                                                                                                                                                                                                                                                                                                                                                                                                           | Size       |
| ----------------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| A (epic-cluster)  | closeout core                 | sports_consolidated_native_ao_extract (main GRACE + finalize), sports_closeout_track_s2_foldin (+finalize), sports_closeout_track_x_hygiene (+finalize), sports_closeout_exchange_fixed_odds_fork (+finalize), sports_track_h_denominator_gated, sports_track_h_denominator_prereqs                                                                                                                            | 10         |
| B (epic-cluster)  | data completion               | data_completion_sports, predictions_ml_walk_forward_and_arb, sports_arb_decay_window_and_alpha_gate_design, sports_odds_feature_naming_canonicalization, sports_canonical_universe_and_apifootball_reference_expansion, sports_catalog_league_grain_only_scope, sports_group_c_execution_backtest_harness                                                                                                      | 7          |
| C (epic-cluster)  | satellite AO + features sweep | sports_satellite_ao_dispatch_batch5, batch9_finalize, data_pipeline_check_mdps_features_finalize, sports_features_layer_findings_sweep (+part2, part3)                                                                                                                                                                                                                                                         | 6          |
| D (epic-cluster)  | odds API cluster              | sports_odds_api_scattered_multiyear_gaps, sports_batch_odds_api_capture_outage_recurrence_check, sports_odds_venue_enumeration_undercount_predrain, sports_odds_stale_fixture_reinjection, mtds_sports_odds_api_force_fetch_no_parquet, sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured, sports_odds_feature_naming_four_way_mismatch, sports_halftime_odds_sfi_vs_inplay | 8          |
| E (epic-cluster)  | estate/instruments            | estate_orphan_assessment, instruments_remaining_work_audit, mtds_is_full_adapter_smoketest_findings, instruments_service_sports_footystats_uac_overlap_qg_red                                                                                                                                                                                                                                                  | 4          |
| F (epic-cluster)  | recon/stats/fixtures          | sports_cf8_available_at_backfill_regression, sports_stats_delayed_live_capture_still_dead_post_fix, sports_fixtures_schedule_wrong_schema_day, candle_feature_canonical_path_divergence, sports_peripheral_bucket_league_vocabulary_contamination                                                                                                                                                              | 5          |
| G1 (epic-cluster) | ops/mdps                      | autonomous_session_operator_decisions, mdps_sports_honest_absence_writes_fail_fetchevidence_gate, mtds_pipeline_check_process_killed_during_skip_leg_poll, mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp, ml_training_and_prediction_pipeline_launchers_stale_post_consolidation, mdps_features_deadcode_consolidation, sports_catalog_dp_catalog_001_junk_name_crash                             | 7          |
| G2 (epic-cluster) | fetch/manifest/coverage       | footystats_matches_predictions_fetch_gaps, sports_dependency_check_manifest_vs_gcs_path, backfill_smoke_write_path_canonical_audit, adapter_findings_gcs_manifest_deployment_api_reconciliation_gap, sports_index_recency_masked_captured_atoms, phantom_audit_estate_coverage_gap                                                                                                                             | 6          |
| EPIC              | epic hub                      | sports_master.md in full + closeout cross-check                                                                                                                                                                                                                                                                                                                                                                | 1 (168 KB) |
| CODEX             | codex-alignment               | Codex SSOTs sections of 12 sports plans + 2 known-broken refs (sports-canonical-league-cup-registry, plan-completion-and-archival-discipline)                                                                                                                                                                                                                                                                  | 12 plans   |

**STEP-1 hygiene inputs** (sweep 2026-08-06 21:51 UTC): 4 hard failures — reference-path format 83 (baseline 81),
existence 88 (86), AG-closeout linkage 75 orphans (69), terminal-status-archived 3 (0); archive-candidates ratchet RED.
All corpus-wide ratchets — flagged, not sports-fixable in this shard. Sports-relevant flags: 2 BROKEN codex refs (see
CODEX hunter), 2 estimate DRIFTs (`sports_satellite_ao_dispatch_batch9/10_finalize`, 50% infra), 1 priority-tier WARN
(sports_odds_stale_fixture_reinjection P1), INDEX.md drift 19 (corpus-wide, not sports-owned).

**Cross-slot observation (noted, not touched)**: the ROOT PM clone (`unified-trading-pm`, not this slot) is checked out
on the ci-tranche reconciler's review branch `plan_reconciler/agt-a304c9` (PR #2400 open, committed work pushed) with
leftover staged WIP (`plan_reconciler_ci_late_findings_2026_08_06.md` staged-mod + untracked
`ag_closeout_audit_ci_parked_2026_08_06.md`). Not this run's work — left untouched, reported for awareness only.

## Flips verified

## Contradictions

## Doc-drift

## Hygiene fixes

## Filed

## Archive candidates (operator review)

## Refuted (dropped by verify)

## Plans not reached

---

## Hunter results — 10/10 complete (2026-08-06)

All 10 hunters returned (A,B,C,D,E,F,G1,G2,EPIC,CODEX — sonnet, read-only, full-doc reads, no writes). Every non-grace
sports doc was read in full by exactly one hunter; the epic was read by the EPIC hunter + cross-checked by 6 batch
hunters (zero doc↔epic track/status contradictions on batch docs; the epic's OWN listing drift is flagged below).

## Candidate registry (deduped; verify status as of 2026-08-06 22:30 UTC)

**V-wave 1 in flight (adversarial pairs, 6 agents):**

- **V1 [P0]** odds-api launch-readiness cross-doc contradiction —
  `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md:279-280,294` ("NOT YET LAUNCHED (corrected
  2026-08-02 … both gates are clear)") vs `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md:163-170,173,181-183`
  ("BLOCKED-CREDENTIALS 2026-08-02: OUT OF USAGE CREDITS, `x-requests-remaining: -772`, /v4/historical 401 since 08-01
  12:40:24Z" + an embedded "UNBLOCKED 2026-07-31 … launch the backfill" directive inside the same P1) vs
  `mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md:183-189` (same 401 evidence). Acting on doc A launches a
  backfill whose every call 401s. → cross-doc banner fix + operator notify.
- **V2 [P1]** false-progress flip — `sports_closeout_track_s2_foldin_2026_07_25.md:391` features-recompute `[x]` flipped
  at launch (slot-4, 08-06) while Progress Log :521-528 records VM `fts-backfill-20260806-012831` still RUNNING (~1h in
  at 02:34Z, no exit signal); done-when ("VM exit 0, manifest rows written") unmet; slot-13 reverted the identical
  pattern earlier the same day (:460-461); also `--force` (:398) vs `--redo-all` (:517) discrepancy on the same
  relaunch. → revert + note.
- **V3 [P1]** false-progress flip — `candle_feature_canonical_path_divergence_2026_07_20.md:317` todo 3 `[x]` "✅
  VERIFIED 2026-08-04" while its own continuation (:329-330) + Progress-Log audits (:533-535, :589-593) say the ~7.1M
  TradFi leaf-id repair is unresolved pending an operator ruling. → revert or adjudicate.
- **MECH-1a/1b/2 (3 confirmer agents, in flight)** — ~35 mechanical edits: frontmatter last_updated (~19 docs), statuses
  (sports_index_recency → resolved; sports_catalog resolved_by clear), counts (process_killed 2/2→3/3; fixtures_schedule
  85→≥86; halftime banner 5→3; batch5 12→11), stale summaries/titles (cf8, force_fetch, scattered_multiyear_gaps),
  banners (track_x draft; finalize draft), path repoints (~15: mdps_features×4, catalog_league_grain×3,
  group_c+odds_feature_naming, dependency_check×2, backfill_smoke×2, convention `../`×7, canonical_universe
  p2_history×2, footystats×2), codex-ref plan-side fixes (batch10_finalize — GRACE-deferred; canonical_universe:424 —
  wave 2), epic 8-item drift (E1-E8).

**Wave-2 verify (after wave 1):** V4 stats_delayed recommended-decision banner · V5 sweep-part2 K0-DECISION banner · V6
canonical_universe floor banner · V7 audit §1.3 count fix · V8 canonical_universe:424 codex-ref repoint.

**Refuted (dropped by verify, no flip):** all 15 missed-flip candidates across hunters carry their own counter-evidence
— operator-gated (canonical_universe:319 E8 `--drop-stale` BLOCKED-OPERATOR; cf8:357 BLK-d9137d48 STOP; halftime:197
cutover-gated), prereq-sha-only (arb_decay:144, group_c:77, batch5:116, sweep:604, footystats:173, data_completion:414,
backfill_smoke:284), or genuinely open per the doc's own notes (smoketest:358 FLUID, audit:825 umbrella, estate:344,
part2:211/:758, stale_fixture:246, batch_odds:279). **prereqs:118 (batch_footystats copy+swap) =
reported-done-unflipped** — fresh census 0 non-registry rows, 15,980/15,980 verify PASS, only ship-mechanics pending
(RB-166e706f) — SOFT self-report only, no HARD evidence chain in-session → FILED, not flipped.

**P1 route (owner decision):** `mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md` —
`assigned_vm: planning` + `execution_scope: orchestrator-agent` with ZERO checkboxes (verified by grep: 0
`- [ ]`/`- [x]`); remediation exists only as prose (:130-141) so the AO can never ingest a data-correctness masking
defect. Fix direction (convert prose→todos vs flip NA) is a content call → route to owner.

**Archive candidates (operator review):** (1) `instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md` —
superseded duplicate physically in active/issues, zero-checkbox by design, `locked_since: 2026-05-21` predates
`created: 2026-07-30` (impossible lock metadata — copy-paste; lock blocks auto-archive → ASK); refs from
`zero_checkbox_sweep_all_tranches_2026_07_31.md`, `ag_closeout_audit_sports_tooling_followups_2026_08_06.md`,
`docs_reconcile_operator_decisions_2026_08_02.md` (sports/cross-tranche referrers noted). (2)
`sports_index_recency_masked_captured_atoms_2026_07_13.md` — all 7 todos done; status→resolved + archive after fix.

**Epic drift (EPIC hunter, 8 items, non-grace 52h):** E1 golden-window coordinator banner → dead superseded coordinator
(:67-75; :20/:71 wrong `../active/` paths) · E2 Assigned-listing: 6 archived-complete plans shown "active"
(:1387-1430) + "16 active plans" vs measured 25 (:1382) + 17 actual plans missing — section is SCRIPT-GENERATED
(`scripts/plans/populate_epic_bodies_2026_05_21.py`), no epic filter → hand-edit sports_master only + flag fleet re-run
· E3 SFI backfill BLOCKED-ON-FREEZE stale (:1351-1353; freeze lifted 2026-07-17) · E4 P0 "DO NOT resume FWD/BACKFILL
VMs" self-contradictory (:448-449; Phase 2 complete 05-23, Phase 4 resumed) · E5 master-plan cross-refs wrong path +
"KEPT ACTIVE" false claim (:1546-1549) · E6 last_updated (:62) → 2026-08-02 · E7 critical-path "Phase 1 partial" (:367;
all phases complete) · E8 dangling `plans/ai/` ref (:1550, dir gone).

**Grace-deferred:** `sports_satellite_ao_dispatch_batch10_2026_08_06_finalize.md` codex-ref path swap (3h — GRACE;
`codex/11-project-management/plan-completion-and-archival-discipline.md` → `12-agent-workflow/…`, verified moved) ·
native_ao_extract draft banner + last_updated (GRACE, context-only).

---

## Run state — resume here (compaction checkpoint 2026-08-06 ~23:10 UTC)

**Status: STEP 4 near-complete (6/6 pair verdicts in; MECH-1a + MECH-2 still in flight). STEP 5-8 pending. Branch
`plan_reconciler/agt-132fc8`, pushed, ahead=0 (c81c90238).**

### Verdict log

- **V1 [P0] odds-launch — CONFIRMED both sides; fix direction corrected by refuter + verified by reconciler.** Quotes
  verbatim; no doc entry after 08-02 in the 3 docs clears the blocker. **BUT the blocker was resolved OUTSIDE the docs
  on 2026-08-03**: operator purchased a 10,000,000-credit top-up (BLK-6728ec9a Option B) — verified by me in
  `plans/archive/issues/odds_api_key_quota_exhausted_4_days_after_provisioning_2026_08_02.md` (`status: resolved`, L21;
  `x-requests-remaining: 14992590` L48-49/L159-160; "10,000,000-credit top-up on top of the recurring 5,000,000/month
  base" L132-133). None of the 3 docs mentions it. **Apply = reconcile all 3 docs to RESOLVED** (texts below), NOT
  block-the-launch. Concurrency guard now exists (`deployment-service@28c8d5f`, cap 1). No operator question needed
  (already answered 08-03); notify informational.
- **V2 [P1] s2_foldin flip — CONFIRMED both sides.** Refuter ran a LIVE `gcloud compute instances list` check: VM
  `fts-backfill-20260806-012831` **still RUNNING ~21h after launch** (done-when definitively unmet). Flip commit
  `1fb2dbf56` (slot-4, 01:34:28Z) ~15 min after slot-13's revert `0610e690e` (01:19:01Z) of the identical pattern.
  **Sub-finding REFUTED**: todo `--force` (L398, in-VM CLI cmd) vs progress `--redo-all` (L516, launcher invocation) are
  TWO LAYERS of one invocation (launcher `--redo-all` composes CLI `--force`, launcher L192-194) — no flag fix; fold a
  clarifying clause into the revert note. Revert note text below.
- **V3 [P1] candle todo-3 — CONFIRMED both sides.** Flip commit `e0a44adb4` (slot-11, 2026-08-04 22:19:46Z). Cited
  execution doc has **17 todos not 20**; its todo 14 + BIG-FINDING log exclude this deliverable; audits
  07-30/08-03/08-04 all call todo 3 open; sibling `tradfi_manifest_content_recovery_completion_2026_07_24.md` L343 still
  `- [ ]` (Databento 1,328 cells) and its L350 "verify+close" `[x]` carries placeholder SHA `unified-trading-pm@<SHA>`
  (evidence-fabrication violation). Revert text below. **Cross-tranche (FILE only):** L350 flip revert → tradfi tranche.
- **MECH-1b [last_updated ×33] DONE** — full table below; **no KEEP cases**; docs #7 (`mdps_sports_honest_absence`) and
  #15 (`sports_index_recency`) need the `last_updated:` line ADDED; preserve quoting style; doc 33 (epic) preserves its
  inline `# was:` comment.
- **MECH-1a [19 items] DONE — 19/19 CONFIRM-STALE, no rejections** (drop-in replacement texts are re-derivable from the
  cited lines; each fix direction is documented in the registry). Two EXTRA stale surfaces flagged beyond the cited
  lines: #5 cf8 — the frontmatter SUMMARY (L11 "did not isolate the exact line…") is also stale, amend alongside the
  title; #6 fixtures_schedule — title (:4) AND body heading (L39) carry the same stale "85", mirror "at least 86". #4
  (sports_index_recency status→resolved) wants a Progress-Log line noting the 2026-08-06 flip. #17 (track_x) needs BOTH
  the revert AND a new `- [ ]` re-author todo (proposal drafted). #15 (process_killed) proposes 3 `- [ ] [OPS] P2` todos
  from the 3 prose bullets.
- **MECH-2 [paths/epic]: still in flight** — apply per its verdict (edit list below).

### Apply texts (confirmed)

**V1-DocA** (`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`, top of file, above the 🟢 RESOLVED
2026-07-29 banner):

> 🟠 CORRECTED 2026-08-06 — the 2026-08-02 "both gates are clear" claim below predates the same-day discovery (in
> `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` P1) that the-odds-api.com was OUT OF USAGE CREDITS
> (`x-requests-remaining: -772`, `/v4/historical` 401 since 2026-08-01 12:40:24Z — a NEW blocker, distinct from the July
> DEACTIVATED_KEY one; corroborated by `mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md` todo 2). That quota
> blocker is RESOLVED 2026-08-03: operator purchased a 10,000,000-credit top-up (BLK-6728ec9a Option B), live-verified
> `x-requests-remaining: 14992590` — see
> `plans/archive/issues/odds_api_key_quota_exhausted_4_days_after_provisioning_2026_08_02.md` (resolved). Launch is
> genuinely unblocked on the credential side; re-verify live (curl `/v4/historical/...` → non-401) before launching per
> standing discipline, and respect the sibling OOM P1 (`mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`): small
> chunk sizes, no blind relaunch.

**V1-DocB** (`sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`): (a) retag P1 first line: "**BLOCKED-CREDENTIALS
2026-08-02 → RESOLVED 2026-08-03** (10M top-up landed, live-verified `x-requests-remaining: 14992590`; quota doc
archived resolved) — the do-NOT-relaunch directive below is superseded; re-verify live via curl before any launch." (b)
append to embedded L173 block: "(2026-07-31 state — superseded by the 2026-08-02 quota marker above, itself RESOLVED
2026-08-03; not current, act only after live re-verification)."

**V1-DocC** (`mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md`, on the [OPERATOR] P2 todo L183-189): append
"✅ RESOLVED 2026-08-03 — operator topped up 10M credits (BLK-6728ec9a); live-verified `x-requests-remaining: 14992590`;
SPORTS/ODDS_API force-refetch is unblocked."

**V2 revert** (`sports_closeout_track_s2_foldin_2026_07_25.md` L391 `- [x]` → `- [ ]` + note appended to the todo
body, + a Progress Log entry):

> **Corrected 2026-08-06 (plan_reconciler agt-132fc8)**: this todo was `[x]`-flipped at relaunch (08-06, slot-4) with
> its own done-when ("VM exit 0, manifest rows written for enriched dates") unmet — VM `fts-backfill-20260806-012831`
> was still RUNNING (slot-16 verified at 02:34Z; live re-verified RUNNING 2026-08-06 ~22:30Z via
> `gcloud compute instances list`), no exit signal, no manifest rows yet. Reverted to `[ ]` so the backlog re-derives
> it; re-flip only on VM exit 0 + manifest rows for enriched dates — same correction slot-13 applied to the identical
> 08-05 launch-flip pattern. Flag note: launcher `--redo-all` composes CLI `--force` (lock bypass ≠ CLI force); do NOT
> relaunch with bare launcher `--force` — it would skip every date (2026-07-18 silent-no-op class).

**V3 revert** (`candle_feature_canonical_path_divergence_2026_07_20.md` L317 — replace the `- [x] ✅ VERIFIED …` stamp +
false "all 20 todos [x]" claim; keep L320-330 continuation verbatim):

> `- [ ] 3. [DATA] P1. **REVERTED 2026-08-06 (false-progress audit, plan_reconciler agt-132fc8) — falsely flipped [x] 2026-08-04 (slot-11, e0a44adb4)** — the cited `/plans/archive/2026_07/candle_canonical_path_migration_execution_2026_07_24.md`covers the PATH migration (17 todos [x], not 20) + the executor's leaf-id-resolution CODE, but its own todo-14 + BIG-FINDING entries explicitly exclude this deliverable ("TRADFI's ~7.1M quarantined objects = its todo 3 ... NOT duplicated by this plan's todo list"); no content-read leaf-id resolution pass has run and no accept-the-loss operator ruling exists (unanswered authority call per 2026-07-30/08-03/08-04 audits; gating deliverable`tradfi_manifest_content_recovery_completion_2026_07_24.md`L343 still`-
> [ ]`).** Canonicalise **TradFi candle leaf ids** (`E1AF0_C3200_migrated_*`→`VENUE:TYPE:SYMBOL`) or rule the migration
> naming acceptable.

Also check candle todo 2 (L311-316, same class — "Repair itself is still pending P7 `--apply`") and revert if confirmed
on read.

### MECH-1b values (apply; preserve quoting style; add line where missing)

| Doc                                   | new value                          |     | Doc                              | new value    |
| ------------------------------------- | ---------------------------------- | --- | -------------------------------- | ------------ |
| estate_orphan_assessment              | 2026-08-06                         |     | data_completion_sports           | 2026-08-03   |
| instruments_remaining_work_audit      | 2026-08-06                         |     | predictions_ml_walk_forward      | 2026-08-06   |
| mtds_is_full_adapter_smoketest        | 2026-08-06                         |     | sports_arb_decay                 | "2026-08-03" |
| autonomous_session_operator_decisions | "2026-08-05"                       |     | sports_odds_feature_naming_canon | "2026-08-03" |
| ml_training_launchers                 | 2026-08-06                         |     | sports_catalog_league_grain      | 2026-08-03   |
| mdps_features_deadcode                | 2026-08-06                         |     | sports_group_c                   | "2026-08-03" |
| mdps_sports_honest_absence            | **ADD** 2026-08-06                 |     | s2_foldin                        | "2026-08-06" |
| sports_cf8                            | 2026-08-06                         |     | track_x_hygiene                  | "2026-08-06" |
| batch_odds_outage                     | 2026-08-06                         |     | exchange_fixed_odds_fork         | "2026-08-03" |
| halftime                              | 2026-08-06                         |     | track_h_gated                    | "2026-08-03" |
| footystats                            | 2026-08-06                         |     | track_h_prereqs                  | "2026-08-03" |
| dependency_check                      | 2026-08-06                         |     | native_ao_extract_finalize       | "2026-08-03" |
| backfill_smoke                        | 2026-08-05                         |     | s2_foldin_finalize               | "2026-08-03" |
| adapter_findings                      | 2026-08-05                         |     | track_x_finalize                 | "2026-08-03" |
| sports_index_recency                  | **ADD** 2026-08-06                 |     | fork_finalize                    | "2026-08-03" |
| phantom_audit                         | 2026-08-06                         |     | canonical_universe               | 2026-08-06   |
| sports_master (epic)                  | 2026-08-02 (keep `# was:` comment) |     |                                  |              |

### Edit list — STEP 5 apply (non-grace ≥18h unless marked; per-verdict)

- REVERT: s2_foldin:391 (V2 text) · candle:317 (V3 text) · candle:311-316 todo 2 (check) · track_x:150-160 (MECH-1a #17)
- BANNERS: V1 reconcile ×3 docs (texts above) · stats_delayed:214-215 (V4 wave 2) · part2 K0:560-577 (V5 wave 2) ·
  canonical_universe:371-372 floor (V6 wave 2) · canonical_universe:424 codex-ref repoint (V8 wave 2) ·
  dependency_check:293-301 RE-TRIAGE (MECH-2 #5a)
- STATUS/COUNTS (MECH-1a, 19 items): process_killed:72 · sports_catalog:65 · footystats:52 ·
  sports_index_recency:28→resolved · cf8:3-4+40 · fixtures:7 · force_fetch:13+181 · scattered:22-23 · halftime:121,127 ·
  batch5:11 · sweep:666-669 · part2:752 · finalize:57 · process_killed:174-185 · track_x:62 · honest_absence:27 ·
  footystats:186-188
- last_updated: MECH-1b table above (33 docs)
- PATHS (MECH-2): mdps_features×4+../ · catalog_league_grain×3 · group_c+odds_feature_naming related · predictions_ml
  gate→629 · dependency_check refs×2 · backfill_smoke provenance+text · convention refs×7
  (footystats:27→`/plans/archive/2026_07/instruments_service_docs_consolidation_2026_07_08.md`; backfill_smoke:37;
  adapter_findings:38; phantom:26; cf8:26; peripheral:29→`/plans/active/sports_consolidated_closeout_2026_07_19.md`) ·
  canonical_universe p2_history×2+counts · fork:346-348
- EPIC `sports_master.md`: E1 golden-window banner+paths (:67-75,:20,:71) · E3 SFI freeze un-block (:1351-1353) · E4 P0
  wait-condition (:448-449) · E5 master-plan cross-refs (:1546-1549) · E7 critical-path row (:367) · E8 dangling
  plans/ai (:1550) · E6 last_updated→2026-08-02 (:62) · **E2 roster hand-edit** (25 declared vs 16 listed; 6
  archived-as-active rows; 17 missing; count line; populator has NO epic filter — do not run in shard; flag fleet
  re-run)
- GRACE-DEFERRED (do NOT edit): batch10_finalize:79 codex path · native_ao_extract banner+last_updated
- CROSS-TRANCHE (FILE only): tradfi_manifest_content_recovery_completion L350 placeholder-SHA flip

### P0 odds-launch — resolved-outside-docs (no operator question needed)

The contradiction is real and reconciled per V1 texts; the underlying blocker was already answered by the operator on
2026-08-03 (10M top-up, BLK-6728ec9a, archived quota doc resolved). Informational notify only; the tracked
`[OPERATOR] P0` follow-up below becomes "confirm docs reconciled" — self-owned.

### Tracked follow-ups (`- [ ]`)

- [ ] [DOC] P1. `mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp` — convert prose remediation to `- [ ]`
      todos or flip `assigned_vm` → NA (owner decision; planning+orchestrator-agent with zero checkboxes).
- [ ] [DOC] P2. `sports_track_h_denominator_prereqs` todo 1 (batch_footystats copy+swap) — reviewer re-verify fresh
      census (0 non-registry `league_id` rows; 15,980/15,980 PASS reported) + flip.
- [ ] [DOC] P2. Archive `instruments_service_sports_footystats_uac_overlap_qg_red` after unlock —
      `locked_since: 2026-05-21` predates `created: 2026-07-30` (impossible metadata); fix or `[unlock-plan]` first.
- [ ] [DOC] P2. Archive `sports_index_recency_masked_captured_atoms` after status → resolved.
- [ ] [DOC] P3. `batch10_finalize` codex path swap
      (`codex/11-project-management/plan-completion-and-archival-discipline.md` → `12-agent-workflow/…`) — grace expires
      2026-08-07 ~03:30Z.
- [ ] [DOC] P3. `sports_consolidated_native_ao_extract` stale draft banner + last_updated (grace).
- [ ] [DOC] P2. Fleet re-run `scripts/plans/populate_epic_bodies_2026_05_21.py` (all-epic roster regeneration;
      sports_master hand-fixed this run).
- [ ] [DOC] P2. Cross-tranche file: `tradfi_manifest_content_recovery_completion` §B.5 "verify+close" placeholder-SHA
      flip (trafdi tranche).

### Deferred work after 2026-08-06

| Item                                                    | State              | Blocked on                          |
| ------------------------------------------------------- | ------------------ | ----------------------------------- |
| MECH-1a + MECH-2 verdicts                               | Cannot be done yet | harness notifications (auto-arrive) |
| Wave-2 verify V4/V5/V6/V7/V8                            | Cannot be done yet | wave-1 slots + verdicts             |
| STEP 5 apply (~35 edits)                                | Not done           | verdicts                            |
| STEP 6 route (informational notify + `_agent_pings.md`) | Not done           | STEP 5                              |
| STEP 7 PR + result POST `/api/plan_health/result`       | Not done           | STEP 5-6                            |
| STEP 8 `/done`                                          | Operator-owned     | operator answers                    |

**Recommended next:** apply V1/V2/V3 confirmed texts + MECH-1b last_updated (all verdicts in hand) as the first STEP-5
commit class, then MECH-1a/MECH-2 as their verdicts land, then wave 2.

### Lessons (this run)

- **Grace**: name-date ≠ git-change-date — re-check `git log -1 --format=%ct` per doc immediately before editing (caught
  batch10_finalize at 3h while named 08-06).
- **Adversarial verification earns its keep**: V1-refuter found the 08-03 top-up that the confirmer missed — without the
  pair, I'd have bannered BLOCKED-CREDENTIALS on an already-resolved blocker. Always cross-check beyond the candidate
  docs (the resolution lived in an archived doc).
- `populate_epic_bodies` has NO epic filter → in sharded runs, hand-edit the shard's epic roster + flag a fleet re-run.
- **Circular-evidence class**: flips citing "covered by doc X (all todos [x])" where X's own todos defer the work back
  (candle todo 3 ↔ B.5; "all 20" vs actual 17) — check the cited doc's closure conditions, not just its checkboxes.
- **Layered-flag class**: `--force` (CLI) vs `--redo-all` (launcher) can be one invocation at two layers — verify the
  launcher's composition logic before flagging a discrepancy (refuter did; I wouldn't have).
- Live `gcloud` checks by verifiers are decisive for VM-state claims (V2: still RUNNING ~21h).
- Verifier prompts must carry the candidate contract inline (/tmp prompt files die with the session — this section
  exists because of that).
- The heartbeat nudge fires on aggregate slot state (agent-orchestrator ahead=1, market-tick-data-service dirty=1 —
  inherited, untouched); verify before reacting.
