---
doc_type: issue
title: plan_reconciler daily findings — 2026-08-07 (cross-cutting tranche)
summary:
  Run-findings + progress journal for the daily plan-reconciler shard on the cross-cutting tranche (dispatch
  agt-c6e8c7). Records flips verified, contradictions, doc-drift, hygiene fixes, filed items, archive candidates,
  refuted candidates, and coverage.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [reconciler, run-findings, cross-cutting, agt-c6e8c7]
related: [/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
created: 2026-08-07
parent_epic: plan_hygiene_master
author: plan_reconciler
source: agt-c6e8c7
assigned_vm: NA
priority: P2
locked_by: plan_reconciler-agt-c6e8c7
resolved_by:
---

# plan_reconciler run findings — 2026-08-07 (tranche: cross-cutting)

> Dispatch `agt-c6e8c7` · slot 13 · review branch `plan_reconciler/agt-c6e8c7` Tranche: `cross-cutting`
> (`asset_group: cross-cutting` + `cross_cutting_consolidated_closeout_2026_07_25.md` Tracks) Normative refs
> (`PLAN_FORMAT.md` / `task_template.md` / `INDEX.md` / `ACTIVE_INDEX.md`) + codex stay in scope per shard rule.

## Progress Log

- 2026-08-07 00:35 UTC — boot; STEP 1 complete. All slot repos FF'd to origin/live-defi-rollout (PM at ac3dd5b8a).
  Hygiene sweep: 4 hard failures (ref-path format 83 vs baseline 81; ref-path existence 92 vs 86; AG-closeout orphans 77
  vs 69; terminal-status-in-active 5 vs 0) + 1 soft (todo-format, 80 non-canonical). Archive-candidates check: 11. Grace
  set (~12h window): ~43 cross-cutting docs READ-ONLY this run.
- Operator OOM directive (via heartbeat 2026-08-07): acknowledged — this slot launched NO heavy RAM/IO-bound process
  this run; nothing I launched was OOM-killed. All analysis is grep/read-only; no full-corpus walks, no QG runs.
- 2026-08-07 ~00:45 UTC — STEP 2 done: review branch `plan_reconciler/agt-c6e8c7` created + pushed (findings doc = this
  file). STEP 3 wave-1: 10 read-only plan-batch hunters launched in background (B_A closeout hub, B_B satellites, B_C
  data1, B_D data2, B_E data3, B_F bucket, B_G instruments, B_H mtds/infra, B_I strategy, B_J features) — each pasted
  SUB_AGENT_MANDATORY_RULES.md, model=sonnet, batch ≤336KB, grace-set tagged, contradiction/missed-flip/
  claims-digest/mechanical/plan↔codex contract. Wave-2 (pending, spawn when slots free): 8 issue-batch hunters (I1_AO,
  I2_GOV, I3_CIDEPLOY, I4_MANIFEST, I5a macro+perp, I5b misc-data, I6a instr/features, I6b mtds/mdps) + mechanical
  adjudicator + codex-alignment + topic/plan-format-meta hunter.
- **RESUME STATE (post-compaction)**: dispatch agt-c6e8c7, slot 13, review branch `plan_reconciler/agt-c6e8c7` (pushed,
  ahead=0). Next actions in order: (1) await/collect wave-1 hunter results → spawn wave-2; (2) STEP 4 adversarial verify
  (refuter+confirmer+tiebreaker per candidate, HARD-evidence bar for flips:
  `git merge-base --is-ancestor <sha> origin/live-defi-rollout`); (3) STEP 5 apply confirmed (flip/archive/banner,
  checkpoint commits by name, prettier, heartbeat each); (4) STEP 6 route hard via /blocked can_continue:true + file;
  (5) STEP 7 prettier flush, push branch, `gh pr create --base live-defi-rollout --head plan_reconciler/agt-c6e8c7`,
  POST /api/plan_health/result; (6) STEP 8 poll /messages, apply answers, POST /api/slots/13/done.
- **Phase-0 inventory (durable — regen commands if /tmp is gone)**: hygiene sweep =
  `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` (was /tmp/hygiene_sweep.txt); itemized ref-paths =
  `python3 scripts/plan-hygiene/check_reference_paths.py` (was /tmp/refpath_violations.txt, 175 itemized: format 83 /
  existence 92); orphans = `python3 scripts/plan-hygiene/check_ag_closeout_linkage.py` (was /tmp/orphans.txt, 77, ~30
  cross-cutting); todo-format = `bash scripts/plan-hygiene/check_todo_format.sh` (80 non-canonical); moved-docs feed =
  `git log --diff-filter=AR --name-status --since="3 days ago" -- plans/ codex/` (was /tmp/moved_docs.txt, 411 moves —
  mostly other tranches' issue archival 2026-08-06); tranche corpus lists =
  `rg -l '^asset_group:.*cross.cutting' plans/active plans/active/issues plans/epics` (58 plans / 67 issues / 20 epics).
  Terminal-status 5: only cross-cutting one is `issues/sit_stamp_skipped_on_detached_head_pinned_sha_2026_08_06.md` — IN
  GRACE (9h), not touched this run. Archive-candidates 11: mostly other tranches; cross-cutting ones:
  archive_candidates_content_verification_backlog (GRACE), ag_closeout_audit_cross_cutting_parked ×3 (verify).

**I1 (AO/fleet issue batch, 9 docs) — 2026-08-07:**

- IA1 [P2, GRACE] `ao_fleet_health…:129` "#791 open since 2026-08-06T16:42:19Z" vs `:110` "OPEN since
  2026-08-05T16:42:19Z" (gh confirms 08-05T16:42:19Z) — date typo understates wedge age by a day.
- IA2 [P3] `review_role_boot…:174-175` "all 3 of that doc's `[SCRIPT]` todos are still unchecked" vs
  `boot_composer_misroutes_lifecycle_roles…:180` `[x]` @agent-orchestrator/0a8ed16 (re-verified ancestor;
  `_ONE_SHOT_ESCALATION_ROLES` live at `server/prompts.py:70`) — the 08-06 audit entry is stale; the one-shot guard
  lands exactly the change that could moot review_boot's `[DOCS] P1` for na_eligibility_auditor/ag_closeout_auditor.
- IA3 [P3, GRACE] `watchdog_kill_events…:111-112` Gap-2 "cannot actually SEE the AO host's kill events" vs own
  `:134-138` `[x]` deployment-ui@ed2466e (verified ancestor; option (b) always-rendered card + smoke spec) —
  context/Why-it-matters never reconciled.
- IA4 [P3, GRACE] `ao_fleet_health…:5-9` summary "shipped 4 fixes directly" vs PL `:177-179` "Shipped 3 fixes directly +
  ruling" — counting inconsistency.

**I5c (misc-data issue batch, 6 docs) — 2026-08-07:**

- C1 [P2] `live_pipeline_persistence_hot_path_decoupling…:218-220` open CODE todo premise "52 warm-sink-persist-*
  subscriptions, confirmed live via gcloud list" vs same doc 🔴 CORRECTION 2026-07-31 `:57-67` "returns only **2** of
  the 52" (GCP auto-expiry; fix = `expiration_policy { ttl = "" }` + terraform apply — neither in the todo's scope 1-4)
  — stale premise mis-routes a worker toward compactor-only build when subscriptions are gone; work tracked in new
  fleet-wide plan → ownership split, no superseded marker on the todo.
- C2 [P2, GRACE] `defi_cefi_venue_chain_axis_contamination…:318-329` `[x]` P2 "scheduling/cron half shipped"
  (deployment-service@8eff211) recorded "Gate: BLK-0ea70dac unanswered" in the ship entry, while the todo's own gate
  text says "can ship any time post the raw-capture fix landing" and siblings (slot-13/5/9, 08-06) document gate still
  NOT met (raw `derivative_ticker` ~0 objects at reader path; fix todo `- [ ]`) — flip executed against an unresolved
  operator decision + unmet gate; no RESOLVED bookend for BLK-0ea70dac in the log.
- C3 [P2] `honest_coverage_smoke_harness_4ag_verify…:183-206` -004 task text pins `prd/catalog.parquet` + park "operator
  writes catalog to prd/ OR task amended" vs same doc `:193-194` + `:287` live: `prod/catalog.parquet` EXISTS
  (10,561,159 bytes), `prd/` = 404, runner default env "prod" (`run_live_verify_tradfi.py:68`) — park blocker (d)
  bypassable WITHOUT operator decision; BLOCKED-PREREQUISITES park (prereq landed + archived 07-24) still standing →
  re-dispatch bounces into 404 path.
- C4 [P3, GRACE] `defi_cefi…:330-359` open P1 "The **35** corrupted MANIFEST rows" vs same doc `:800-803` slot-9 08-04
  live-found **42** ("not 35") + cleanup executed on all 42 (CAS rewrite 42,192,492→42,192,450) — todo step 2 never
  updated; worker gating on "35" re-scans a clean population.
- C5 [P3] `backfill_vm_slack_alert_e2e_verification…:3` title "three gaps found" vs body Gap 4 section (added 06-23).

- **RESUME STATE (post-compaction 2, 2026-08-07 ~02:00 UTC)**: STEPS 1-7 DONE, STEP 8 in flight.
  - Delivery: review branch `plan_reconciler/agt-c6e8c7` (ahead=0), PR **#2418** (base live-defi-rollout). Findings doc
    (this) + `plan_reconciler_batch_journal_2026_08_07.md` (detail). `plan_health/result` POSTED (10 contradictions + 15
    doc-drift). Git-status "AHEAD=8 unpushed" nudges are EXPECTED (review-branch delivery) — do NOT push to LDR.
  - **5 blocked questions posted (awaiting operator answers)**: BLK-9b3d751f (codex rewrites ×8), BLK-b3ddcbe7
    (ml-service full.json.gz live gap — deploy-verify first), BLK-3051fc32 (ml-models-store delete authority — annotate
    fold_ml to human-only disposition), BLK-00e5bdf7 (5 archive unlocks: perp_funding / macro_micro /
    ao_park_disposition / fleet_data_acquisition [casing-fix caveat] / live_mode_event_sink), BLK-f8e14d80 (FRED
    live-state → tradfi-owned issue).
  - **Next actions in order**: (1) poll /messages for answers; (2) apply each answer (codex rewrites → 8 doc edits per
    the cited locations in this doc's Codex-drift section; unlocks → [unlock-plan] + 6-step archive ritual for the 5;
    FRED → file `plans/active/issues/fred_live_capture_and_backfill_gap_2026_08_07.md` routed to tradfi; ml-service →
    deploy-check then reconcile the [x] claim); (3) commit each on the review branch with `docs(plans):` prefix; (4)
    when ALL 5 resolved → POST /api/slots/13/done {"task_id":"agt-c6e8c7",...} as the LAST action.
  - Watcher: background task polling /messages every 45s (script /tmp/wait_answers.sh; re-create if /tmp wiped: curl
    /api/slots/13/messages, print texts containing BLK-/option/answer, loop).

## Deferred work after 2026-08-07

| Item                                                                      | State / why deferred                                 | Blocked on                     |
| ------------------------------------------------------------------------- | ---------------------------------------------------- | ------------------------------ |
| 5 /blocked answers applied                                                | Operator-owned (human decision)                      | operator answers via dashboard |
| 8 codex corrections                                                       | Operator-owned (authorization ruling)                | BLK-9b3d751f                   |
| 5 archive unlocks + archival ritual                                       | Operator-owned ([unlock-plan] grants)                | BLK-00e5bdf7                   |
| ml-service full.json.gz deploy-check                                      | Cannot be done yet (needs prod deploy investigation) | BLK-b3ddcbe7                   |
| FRED tradfi-owned issue                                                   | Operator-owned (routing ruling)                      | BLK-f8e14d80                   |
| batch1b:208-224 mirror reversal                                           | Cannot be done yet (doc in 12h grace at verify)      | grace expiry (next run)        |
| batch1 evidence placeholder shas (:90,:299,:350)                          | Not done — mechanical fix                            | next run (non-grace)           |
| `dp_consolidator_scheduler_paused_defi_recurrence` terminal-status (defi) | Other-tranche (defi)                                 | defi sibling worker            |
| sit_stamp terminal-status (cross-cutting)                                 | Cannot be done yet (grace at run start)              | grace expiry                   |
| INDEX.md regen                                                            | Operator-owned (regeneration decision)               | operator                       |

**Recommended next item**: poll /messages for the first answer and apply it — everything downstream (PR update, /done)
hangs on the answers.

## Lessons (2026-08-07 run)

- **/blocked API**: ONE question per POST; fields task_id/question/options[]/recommendation/can_continue/authority.
  Traps: an array payload 422s; unquoted-heredoc expands backticks into command substitution; `recommendation` needs
  explicit quotes in the heredoc. Validate with `python3 -m json.tool` before POST.
- **sed traps**: `|` in the pattern breaks `s|...|` — switch delimiter; line-wrapped prose breaks single-line patterns —
  anchor on the un-wrapped fragment or use Edit. Grep-verify after every sed.
- **No-double-gate rule (2026-07-30 finding)**: a finalize plan with `gate_on_depends: true` MUST be `status: active` —
  `draft` is machine-hostile and FAILS check_finalize_plan_coverage (regression > baseline 0). My initial IAM-finalize
  `active`→`draft` flip was rejected by the gate; the correct fix was the body banner. Run the checker standalone BEFORE
  touching any finalize status.
- **plan_health/result** needs `X-Orchestrator-Secret` from agent-orchestrator/.env.local (route is
  /api/plan-health/result, not /api/plan_health/result).
- **Post-08-05 history-rewrite shas**: PL-cited shas in e2e-testing/UTL/IS may resolve ONLY on origin/main or
  wip-preserve branches. Find the LDR re-stamp via `git log origin/live-defi-rollout --oneline --grep=<subject>`
  - `git diff <old> <re-stamp> --stat` (expect trivial/env-only). Flip citing the LDR re-stamp.
- **Findings-doc line cap**: incremental journaling blew the 1000-line hard cap → split into a consolidated findings
  doc + raw batch-journal doc. Write the journal in a companion doc from the start.
- **e2e-testing default branch is main** (origin/HEAD→main) though it HAS live-defi-rollout; LDR↔main diverged (Option-B
  direct promote 08-05) — check BOTH before judging ancestry.

## Flips verified (confirmed + applied 2026-08-07, adversarial-verified; review branch 3b4bd3c79)

- IF1 ✅ `deployment_api_artifact_pipeline_health_test_date_drift_flake_2026_07_29.md:90-101` → `[x]` @cf55369 (ancestor
  ✓; `test_artifact_pipeline.py:881` live).
- I1 ✅ `colocated…:77-83` (1.3b) + `:93-103` (1.7e) → `[x]` @features-service/3162d627 + @43a2b56b (1.7e carries
  batch1's ratchet caveat: ~1020 errors remain, ratchet REQUESTED).
- I-F1..F4 ✅ `carry_staked…:602-606`,`:619-620`,`:633-634` → `[x]` @e2e-testing/326a345 (LDR re-stamp; env-only diff
  verified); `:651-652` → `[x]` @2ac1a9d(+760d6ba) — NOT 326a345 (that commit has no liquidity code).
- I-F5 ✅ `carry_staked…:667-668` → `[x]` @mtds/98d12be — same HyperliquidS3Downloader asset_ctxs axis, not Tardis
  (refutation FAILED).
- G1 ✅ `instruments_completion_tracker…:556-560` → `[x]` citing LDR re-stamps UTL@a1b08307/00d33d12 + IS@cbbad6ae
  (PL-cited originals unresolvable; issue archived resolved).
- M2 ✅ `bucket_fold_ml…:233-237` → `[x]` @PM/5f04b0702 (ml-store key live :70/:232).
- M3 ✅ `bucket_fold_features…:95-103` `[~]`→`[x]` @UAC/cb951936 + UTL@16d35d05 (re-stamp of 4f0bcc34).
- ⚠️ REVERSAL ✅ `features_service_coverage…:93-98` `[x]`→`[ ]` — @25932d23 never landed (wip-preserve only, no twin);
  origin LDR data_loader.py:275-283 pre-fix shape — false evidence; mirror in batch1b:208-224 flagged (grace), NOT
  reversed.
- F5 CORRECTED: IAM finalize stays `status: active` per the 2026-07-30 no-double-gate finding (gate_on_depends holds it;
  `draft` is machine-hostile) — body banner corrected instead (documents active-but-gated with parent's 2 open todos).
- S3 ✅ `batch1…:80` stale Status-draft banner annotated STALE (active + 21/22 [x], retained for provenance).
- F1 ANNOTATED: `residuals…:643-654` Kraken — verify-or-refresh note added (completion never recorded in corpus; sibling
  docs still list open).
- M4 KEPT-AS-IS: fold_ml `[~]` TF-STATE RECONCILE — 32-destroy apply-block + deferred imports keep it honest.

## Contradictions (consolidated — full detail in batch journal)

- **Stale-claim class (mis-routes dispatch, GRACE-flagged where noted)**: hub CF-manifest job "never succeeded" vs first
  rollup 07-26 (S1/A3, GRACE); hub mtds-retry-audit "NOT started, AO-eligible" vs archived complete (S4/A1, GRACE); hub
  models-MVP "parked pending ruling" vs ruled+shipped 07-27/28 (A2, GRACE); hub e2e "stale hold" vs HOLD LIFTED 07-27
  (A5, GRACE); hub vm_exec_stall "in flight" vs resolved (A4, GRACE); hub cefi CF "all open" vs GREEN 08-01 (S2, GRACE);
  hub Track 12 bucket-resolution active-path cite (A6, GRACE); batch3 "status: draft" in two parked docs vs active 08-06
  (G1 — FIXABLE, 16h); M-2 DEFERRED vs RESUMED 07-27 (H5 — FIXABLE); data_completion "RULED 08-06 APPROVED" vs stale
  BLOCKED-OPERATOR-DECISION tag (C2, GRACE); "8 source docs" vs 10 (A8); cefi Era-B "unadjudicated" vs GREEN (M1-C1);
  FRED "not a ban" Massive vs removal ruling (MA3, GRACE); perp/carry Aster map rows "no GCS data" vs captured 07-29
  (P1/P2).
- **Doc-internal self-contradictions**: M8 "REMAINING" 3 of 4 shipped (E1); WAVE-5 bundles shipped scope (E2); catalogue
  G-invariant vs G4 applied (E5); phase0 producer "unbuilt" vs catalogues promoted (G3); foundation G4 "pending D2" vs
  D2 landed (G4); citadel P2.11.18 dup-deleted-vs-inflates (I2); ensemble PL calls flipped todo "stale open" (I3);
  tracker PL "closed checkbox" vs open box (G1); IAM summary/related stale (F8/F9, GRACE); defi_cefi "35 rows" vs 42
  cleaned (C4, GRACE); findings risk-table F28 OPEN vs [x] RESOLVED (F28); margin-emitter "no emitter" vs DONE cefi
  path; auth_wired NOT_REGISTERED vs AVAILABLE; RULED-leftover "rule A/B/C" in 2 docs (I6a); over_cap "1001L permanently
  unverdictable" vs 992L trimmed (G2, GRACE); perp "no cron" vs premise-wrong (P5); live_pipeline 52-sub premise vs
  2-sub correction (C1); batch3_finalize false-staleness note (S6 — FIXABLE).
- **Doc↔code contradictions**: FRED capability filter vs live attempted_failed (MA1, GRACE); FRED backfill
  "self-sufficient" vs 99 dates only (MA2, GRACE); M1-C2 rejected fallback shipped vs ruling; ui_block_list resolved
  evidence but vitest never run; E2/E3 baseline raises vs "frozen 237/658" claims.

## Doc-drift (consolidated — full detail in batch journal)

- Epic roster/count staleness: infra_master "19" vs 45 (F7), mtds_mdps "4" vs 8 (C7/J5/H5), batch_live_symmetry "2" vs 5
  (E3/I5), strategy_master "9" vs 8 (I5), observability "15" vs 12 (C7), infra_master lists archived mtds doc "active"
  (F6/A1), manifest_master "16" vs 14 + archived child as active (B_E/H1), deployment_master archive-path plan as active
  (J6), infrastructure_master missing both cross-cutting children (A7).
- Stale archive-path cites (active vs archive): plan_line_cap_remediation ×6 docs (C4/H6), data_source_provenance ×2,
  data_completion ×6 refs (C6, GRACE), features_e2e features_input_manifest (J3), foundation defi/sports homes (G5 —
  FIXABLE), mtds_venue_backfill ×3 (H6/H7), vintage bare slugs (B_B), I7 issue-path cites ×4.
- Frontmatter: stale last_updated ~30 docs (inventory in journal); missing last_updated ×5; NA+orchestrator-agent
  pairing ×4 docs (D1/H-mech — same class milestones ruled RESOLVED → FIXABLE); deprecated epic assigned_vm
  vm-defi/vm-cross-cutting/vm-ml ×3 (D4/F-mech); quoted YAML dates ×2; repos: template-copied ×4 (B_C);
  summary-truncated ×2 (perp, macro).
- Mechanical: placeholder shas ×6 (batch1 ×3, closeout, disk_io, fleet_audit); `[~]` markers ×2 (M3/M4); malformed todos
  ×4; line-caps: standardisation 980L (20 from hard), residuals 929L, reconciliation_skill 977L, catalogue 900L,
  ag_closeout 987L, hub 885L — all <1000 hard; defi_cefi 1001L OVER hard (issues/ glob gap, ROUTE); WONTFIX as open
  `[ ]` ×1 (B_C); twin todos ×2 (I6).
- Normative: PLAN_FORMAT.md:106 assigned_role hyphenated forms (data-pipeline-engineer/infra-engineer) resolve to NO
  role file — task_template + docspec.py:411 + role_registry.py:38-47 = underscore canonical → FIXABLE.
- INDEX.md stale (27 absent + 3 dangling + count mismatch; regen last 08-06 18:03) → ROUTE (regen via script).
- Zero-checkbox register: 15 live vs 12 (3 new: ag_closeout_defi_parked, sit_stamp, stash-audit report) — GRACE.

## Near-miss flips (flag, not flip — full detail in journal)

- F1 Kraken 7-week "ETA ~1h" (verify-or-refresh); msgpack 21/23 foreign-gated; provenance audit tool (prod run
  sequenced); SFI/TM verify targets aborted run-id (H3); RESUME-runbook executed-per-annotation (B_H); alias-sunset ×4
  (live tofu-plan verify pending); glue_runner unresolvable cite (IF2); ui_block_list vitest pending; wip_preserve sweep
  threshold unrecorded + new live orphan; slot2 pre_boot half; carry_staked 28/28 open; honest_coverage -004
  over-parked; pipeline_smoke bundled todo; DRIFT trio partial.

## Codex-drift candidates (ROUTE — operator ruling required for codex rewrites)

- `/codex/02-data/carry-venue-live-integration-reference.md:116-118`,`:124` — FUNDING_PERIODS_PER_DAY refs + Aster "no
  GCS backfill" (both resolved in-reality; ~14 days old) — I5b.
- `/codex/02-data/live-data-persistence-and-event-log.md:7-8`,`:111` — "52 subscriptions provisioned" vs 50/52 expired
  (07-31 correction) — I5c.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md:159` — plan_reconciler row: cadence, model,
  dead script ref (fix todo exists in daily_analyst §5) — B_I.
- `/codex/02-data/tradfi-data-types-catalog.md` — tradfi_ohlcv_handler 0 refs + Polygon rows post-removal — I5a.
- `/codex/02-data/pipeline-mode-partition.md:81` — T+30d passed 7 weeks, un-reverified — B_E.
- `/codex/02-data/pipeline-mode-and-batch-live-reconciliation.md:231-245` — partition table mirrors stale plan state —
  B_E/C2.
- `/codex/05-infrastructure/manifest-consolidator-ssot.md:64-67` vs `:111` — internal inconsistency (pending vs LIVE) —
  codex-alignment C5.
- `/codex/06-coding-standards/quality-gates.md:1850-1851` — ban vs 08-06 DEFAULT-RULED relaxation not applied — I6b.
- Epic-embedded summaries: infra_master:725 (consolidator estate), mtds_mdps:734 (manifest v9).
- v2:525 archetype-doc update now-actionable (22 shipped families; archetype docs still `implementation_status: design`)
  — codex-alignment C1.

## Filed

- (to be completed at STEP 6 — /blocked routes + issue docs)

## Archive candidates (operator review — all `locked_by`, need `[unlock-plan]`)

- `perp_funding_data_semantics_and_cadence_2026_06_16.md` — 20/20 [x], open status.
- `macro_micro_econ_data_capture_audit_2026_06_05.md` — 7/7 [x], open status.
- `ao_park_disposition_blocked_answer_no_follow_through_2026_07_31.md` — resolved, all [x] (locked_since predates
  created).
- `fleet_data_acquisition_health_2026_06_21.md` — resolved, all [x] (CAVEAT: venue-casing fix unexecuted prose).
- `live_mode_event_sink_topic_missing_2026_06_21.md` — resolved, all [x], self-declared archive-eligible 07-30.
- `capability_wizard_gap_discovery_2026_06_11.md` — 42/42 [x] but EXPLICIT keep-open-by-design → NOT candidate.
- `features_service_coverage_and_script_canon_2026_06_10.md` — 8/8 [x] but closed-not-done + false-evidence flip → NOT
  clean (archival would launder unfinished work).
- NOT-READY (verified open): ag_closeout_audit_cross_cutting_parked ×3 (3/6, 1/1, 4/5 open).

## Refuted (dropped by verify)

- batch3_finalize false-staleness note refuted as-written (paths resolve) — fix = correct the note, not the cites.
- context_scout P0 duplicate — documented intentional cross-track, no action.
- M4 fold_ml TF-STATE RECONCILE — keep `[~]`-style caveat (BIG FINDING 32 destroys keeps operator-aware).
- I-F7 capacity-book productionise — low confidence, script extension genuinely open.
- IF2 glue_runner flip — evidence unresolvable as written (flag only).

## Coverage (hunters / batches / docs)

- Wave-1: 10/10 plan batches (B_A closeout hub, B_B satellites, B_C data1, B_D data2, B_E data3, B_F bucket, B_G
  instruments, B_H mtds/infra, B_I strategy, B_J features) — 43 docs read in full.
- Wave-2: 9/9 issue batches (I1_AO, I2_GOV, I3_CIDEPLOY, I4_MANIFEST, I5a macro, I5b perp, I5c misc-data, I6a
  instr/features, I6b mtds/mdps) — 65 issue docs read in full.
- Specialists: mechanical adjudicator (332/332 hygiene items classified) · codex-alignment (8 candidates verified,
  bounded codex-ref sweep ~551 refs) · meta/plan-format (normative drift, INDEX, zero-checkbox, line-cap glob,
  terminal-status) · STEP-4 adversarial verifier (in flight at journal time).
- Tranche totals: 58 plans / 67 issues / 20 epics = 145 docs; ~108 cross-cutting docs read in full this run.

## Plans not reached

- None within the cross-cutting tranche (100% coverage of plans + issues batches; epics read as hubs by every batch's
  parent check). Docs in grace were read but flagged READ-ONLY (~43).
