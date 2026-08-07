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

**I4 (manifest/data-status issue batch, 8 docs) — 2026-08-07:**

- M1-C1 [P2] cefi Era-B: `cf_manifest_audit_first_full_rollup…:267` "must NOT suppress cefi's genuine, still-live,
  unadjudicated Era-B gap (521,513 rows)" (flipped 08-05 @d3fb74d7) vs
  `cross_cutting_manifest_canonicalisation…: 233-235` "confirmed CF-1/CF-3/CF-4/CF-5/Era-B all GREEN for cefi
  (mtds@c2ae82e0, 9,662,116 rows, re-verified post-apply)" (08-01; satellite batch1:483 independently confirms) — a
  worker dispatched on "cefi Era-B unadjudicated" redoes closed work. Doc 1's Finding-2 cefi row (:87) never re-dated
  after 08-01.
- M1-C2 [P2] `fleet_data_acquisition_health…:65` "REVISED 2026-07-10 (operator): canonicalize every venue key to ONE
  UPPERCASE convention — not a runtime fallback" vs live code: the REJECTED fallback IS what shipped
  (`websocket_streaming_handler.py:140-142` `get(venue.lower())/get(venue.upper())` added 06-21 @5830cc81; registry
  still mixed-case: `polymarket`/`kalshi` lower vs `POLYMARKET` upper) — doc `status: resolved` (08-04) without the
  canonicalization ever landing (08-04 slot-5 closeout verified items (a)-(d) only).
- M1-C3 [P3] `cross_cutting_manifest_canonicalisation…:128` "CF-8 (available_at) RED on ALL five AGs" vs
  `cf_manifest_audit…:122-127` — same 5 RED / 5 GREEN split; 5 buckets at literal 100% `available_at` fill — doc 2's
  CF-8 paragraph never updated through 08-06 touches.
- M1-C4 [P3, GRACE] `data_status_rollup_ml_service…:272-274` audit note "a deferred verification never turned into its
  own todo" — the follow-up todo EXISTS at `:269-270` — note factually wrong about own content.
- M1-C5 [P3, GRACE — ⚠️ BIG, route] `data_status_rollup_ml_service…:124-155` `[x]` "ROOT-CAUSED + FIXED …
  deployment-api@aaa0d1d" (SERVICE_TO_KIND→ml-store) vs LIVE PROBE 08-07:
  `gs://central-element-323112-data- status-rollups/ml-service/` contains ONLY `coverage.json.gz` (fresh 08-06T12:44Z —
  worker runs the coverage step) — `full.json.gz` ABSENT ~360 cron cycles post-fix; sibling services write it
  (instruments 08-05, strategy 08-01). Either the fixed image never deployed (stray revision pin?) or a new failure mode
  — "FIXED" claim live-contradicted.
- M1-C6 [P3] `cf_manifest_audit…:101` "cefi CF-3 red isn't in that todo's scope, fold it in when worked" vs cefi CF-3
  GREEN since 08-01 — fold-in instruction moot.

**I5b (perp-funding semantics issue, 1×282KB doc + 3 cross-checked) — 2026-08-07:**

- P1 [P2] `carry_staked_basis_funding_scan_experiment…:97` "Funding (Aster) — public API (no GCS data)" map row vs perp
  doc `:534-538` ASTER `derivative_ticker` rows `capture_status=captured, source=aster` since 2026-07-29 + forward
  resumed 08-04 — map routes a reader to re-derive a fixed gap.
- P2 [P3] `cross_venue_funding_reversion_research…:236` "Aster needs a GCS backfill (today only live-API)" vs backfilled
  07-29 (perp `:534-539`,`:641-678`).
- P3 [P3] carry_staked `:591-592` "treat Deribit funding as suspect until that's fixed" vs same doc `:134` + perp
  `:210-215` CONFIRMED 2026-06-17 (stores 8h figure) — "suspect" line never corrected.
- P4 [P3] carry_staked `:96` map row `pipeline_mode=batch_hyperliquid_rest` vs RETIRED by operator R4 (06-07) →
  canonical `batch_hyperliquid`, verified 0 remaining fleet-wide (`:517-530`,`:672-681`; cross_venue `:259`).
- P5 [P3] perp doc `:649-651` "no cron ever wired" vs own `:667-668` "Premise was wrong: cron + registry entries existed
  since 2026-05-20" — only RESOLVED block carries correction; `:313-317`/`:649-651` still state the wrong root cause.
- P6 [P3] cross_venue `:179-180` `(blocked-by issue doc)` annotation stale — blocker fully resolved (perp P1 `:216-244`
  DONE 07-27 + historical reprocessing `:328-340` confirmed 08-03); harness switch itself remains open.

## Near-miss flips (I5b — [x]-evidence flags, correct shas identified)

Perp doc: 0/20 open (archive candidate). Flags on `[x]` whose cited shas do NOT resolve on LDR (post-08-05 rewrite /
copy-paste class):

- M1 [P3] `:202-209` cites UTL@b587b91b/ed622af8 + EXEC@38c7e06f — NONE on LDR; real commits: UTL@1beb1043 +
  EXEC@efb57e30 (ON-LDR, same message; `return_metrics.py:59` confirms the deletion live).
- M2 [P3] `:565-570` cites UTL@3b4bd6b8 (ASTER→BATCH_ASTER override) — NOT on LDR; equivalent UTL@c48e3be0 IS.
- M3 [P2] `:627-633` cites MTDS@497918c2 — WRONG commit (that sha = ohlcv-admit commit, correctly cited at `:620`); the
  Aster `book_snapshot_5` WS connector was added by MTDS@d43fd628 (ON-LDR) — adjacent-sha copy-paste.

## Doc-drift

**I5b (perp batch):**

- Archive candidate (operator review): perp doc — `status: open`, ALL 20 todos `[x]`, `locked_by: live-defi-rollout` →
  `[unlock-plan]` needed. At EXACTLY 1000 lines (hard cap). `summary:` truncated mid-sentence (`:8`).
- Corrupted indentation: lines ~260-430 + ~486-510 carry ~190+ leading spaces (line 260 = 964 chars) — editor artifact.
  `last_updated: 2026-08-04` vs PL 08-05/08-06.
- 14.4h since last commit — outside 12h grace (eligible for non-grace treatment, still locked).

## Codex-drift candidates (I5b — ROUTE: codex rewrite needs operator ruling)

- P2 `/codex/02-data/carry-venue-live-integration-reference.md:116-118` still says UTL `FUNDING_PERIODS_PER_DAY`
  "disagrees (Aster/Deribit 8× wrong)" + "no historical cadence tracker" — BOTH RESOLVED (dict deleted 06-17
  UTL@1beb1043; tracker shipped 08-03 UAC@e8b45af4 + MTDS@fd9efc85); `:124` lists Aster among "no GCS funding backfill"
  venues (GCS data since 07-29). Sole codex file still referencing the deleted dict; ~14 days old. A reader of this SSOT
  re-files already-fixed issues.

## Flips verified

- M1-MF2 [flag-not-flip] `pipeline_smoke_sweep…:111` single open todo — sub-item 1 (prediction bucket) resolved
  elsewhere (batch1:812-815 + milestones_gate:463; flat `kind='market-data-tick-prediction'` is canonical per codex
  bucket-isolation-model:104; the checker was the defect) but sub-items 2-3 unverified (08-03/08-06 entries: standing
  re-verify never executed) — bundled checkbox can't partially close.
- M1-MF1 [evidence proves OPPOSITE] `data_status_rollup…:269` follow-up todo NOT flippable — deployment-api@aaa0d1d IS
  LDR-ancestor but done-when artifact (fresh full.json.gz on */20 cycle) demonstrably absent (C5) → stay-open +
  re-diagnose (deployed-image check first).
- Evidence-resolution: ALL other `[x]` shas in batch are LDR ancestors EXCEPT post-08-05 history-rewrite orphans: UTL
  `21069582/6ce1ddb6/6af7c4b7/057264fd/78481472/9bdcf7a2/d3fb74d7` + instruments-service `ca3902bb/5b509c0b` resolve
  ONLY on wip-preserve branches; content present as rewritten commits
  (`46e2c596/c27c0d70/64eb1b1b/60192d6a+3568f419/06c009ec/44930c21/ed8a79b4/ac1883a7`). Doc 1:118's literal "confirmed
  present on origin/main" (6af7c4b7) now false as written. NOT flip reversals — every flipped todo's WORK is on current
  LDR.

## Doc-drift

**I4 (manifest batch):**

- Archive candidates (operator review, both `locked_by: live-defi-rollout` → `[unlock-plan]` needed):
  `fleet_data_acquisition_health_2026_06_21.md` (resolved, all `[x]`, last touch 08-04; CAVEAT: its operator-ruled
  venue-casing fix C2 is unexecuted prose — archive only with that surfaced) ·
  `live_mode_event_sink_topic_missing _2026_06_21.md` (self-declared archive-eligible 07-30 in its Progress Log).
- Cross-ref path violations (feed to adjudicator — same checker family): doc4 `related` :16-17 + doc5 `:23-24` no
  leading `/`; doc6 `:18` bare slug `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25` (resolves to archive/2026_08);
  doc8 `:159` `plans/active/bucket_estate_consolidation_to_sub100…` wrong dir + no leading slash (actual
  archive/2026_07); doc3 `:101` `data_status_offline_rollup_2026_05_06.md` actual
  `plans/ai/ data_status_offline_rollup_2026_05_06.plan.md`; doc2 `:230,:236` bare-name cites.
- [GRACE] doc3 `last_updated: 2026-07-26` stale vs PL through 08-05. Near-complete: docs 1,2,7,8 (1 open each); doc3's
  single open = evidenced-still-open (MF1). No line-cap breaches (max 341).

## Codex-drift candidates (I4)

- D1 [P3] `cross_cutting_manifest_canonicalisation…:124` defi "populate 2,477 blank source" listed genuinely-open vs
  `cf_manifest_audit…:89` defi tick bucket "(clean)" all-CF-GREEN on first-ever complete audit — needs one re-check
  (either fixed→stale claim or 07-26 audit missed them).

## Flips verified

- IF1 ✅ **CONFIRMED FLIP CANDIDATE (non-grace)** —
  `deployment_api_artifact_pipeline_health_test_date_drift_flake _2026_07_29.md:90-101` open `- [ ] [CODE] P3` whose own
  body documents "**SHIPPED deployment-api@cf55369**"; hunter ran
  `git merge-base --is-ancestor cf55369 origin/live-defi-rollout` → **yes**; artifact live —
  `tests/unit/api/test_artifact_pipeline.py:881` computes `two_days_ago = (datetime.now(UTC) - timedelta(days=2))`,
  `:879-880` comment cites this exact bug. Needs `- [x]` + sha (also makes the doc a near-complete → archive candidate).

## Contradictions

**B_C (data1 batch, 5 docs) — 2026-08-07:**

- C1 [P1] `plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md:93-94` claims tradfi retry "FOLDED
  IN" to the wave-launcher vs its own open todo `:127-128`
  `- [ ] [DATA] P1. Retry the tradfi attempted_failed (13 cells)` — unreconciled: either close-by-reference or add a
  cross-note.
- C2 [P1, GRACE] `plans/active/data_completion_to_100_all_ag_2026_06_21.md:737` "RULED 2026-08-06 (operator): APPROVED —
  go ahead with the delete" vs still-live `BLOCKED-OPERATOR-DECISION` tag `:747` + `last_updated: 2026-08-03` `:40`
  predates the ruling. Doc in grace → flag only.
- C3 [P1] `plans/epics/observability_master.md:46` + `:156-159` roster lists
  `data_pipeline_alert_substrate_residual_2026_07_24.md` as active — it is ARCHIVED (`plans/archive/2026_07/…`, status
  complete); sibling doc cites the archive path correctly.
- C4 [P2] three docs carry BOTH path forms for `plan_line_cap_remediation_2026_07_23` (archive vs stale active):
  `data_pipeline_ag_residual…:25` vs `:44-46`,`:65`; `data_source_provenance_enforcement…:20` vs `:37-38`,`:53-55`;
  `data_completion_to_100…:484-486`,`:625-628`,`:632-635`.
- C5 [P2, GRACE] `data_pipeline_alerts_batch_remediation_2026_07_15.md` `related:` `:31-34` cites 3 archived issue docs
  as active (its own body `:119` uses the archive path correctly). Doc in grace → flag only.
- C6 [P2, GRACE] `data_completion_to_100_all_ag…:167-168`,`:210`,`:145-146`,`:511-516` stale active refs to archived
  issues. Doc in grace → flag only.
- C7 [P2] `plans/epics/mtds_mdps_master.md:727` + `:76-79` "4 active plans parent_epic mtds_mdps_master" vs ACTUAL 8
  (`rg -l '^parent_epic: mtds_mdps_master' plans/active/*.md`); `plans/epics/observability_master.md:97` "15 active
  plans" vs actual 12.

**B_B (satellites batch: hub + batch1/1b/3 + finalizes + context_scout + vintage) — 2026-08-07:**

- S1 [P1, GRACE] hub `cross_cutting_consolidated_closeout_2026_07_25.md:176-181`,`:479-480`,`:701-704` claims the
  `uts-prod-cf-manifest-audit` job "never succeeded / fully open / failing daily since 07-04" vs
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md:462-468` documenting the FIX (execution qsp6r 07-26, first
  ever audit object written, issue archived `status: resolved`) — most mis-route-prone stale claim in the tranche
  (reader would re-dispatch the fix). Flag only.
- S2 [P2, GRACE] hub Track 2 `:199-203` "cefi CF items all still open" vs batch1 `:470` CF-1/CF-4/CF-5/Era-B all GREEN
  2026-08-01 (slot 6 data_engineering). Flag only.
- S3 [P2] "**Status: draft.**" body banner vs `status: active` frontmatter — `batch1…:80`, `batch1b…:69-72` (batch1b
  side GRACE; batch1 side candidate).
- S4 [P2, GRACE] hub Track 9 `:351-353` `mtds_retry_safe_default_audit` "NOT started 5 open / 0 done" vs batch1b `:552`
  all 5 `[x]` (PM@4d3713ade) + doc archived `status: complete`. Flag only.
- S5 [P2] `batch1_finalize…:130-138` open-todo census superseded ("20 still-open" vs actual ~3 combined; todo 1's
  working premise needs re-derivation).
- S6 [P2] `batch3_finalize…:113-117` Progress-Log note claims two Codex SSOT paths are "STALE/swapped" — disk verifies
  BOTH resolve exactly as cited; the note is self-contradictory (its own parenthetical names the same locations). Should
  be corrected so a future pass doesn't "fix" correct citations. (Only false codex-drift claim.)
- S7 [P3, GRACE] hub PL 08-02 `:727-742` "batch3 remains status: draft" vs batch3 `status: active` + operator-approved
  08-06 (`batch3…:18`,`:56`). Historical, informational.

**B_D (data2 batch: hardening / self-healing / reconciliation_skill / milestones_gate) — 2026-08-07:**

- D1 [P2] non-canonical pairing `assigned_vm: NA` + `execution_scope: orchestrator-agent` on
  `data_pipeline_hardening_self_monitoring_2026_06_22.md:35-36` AND
  `data_pipeline_self_healing_completion_residual_2026_07_24.md:28-29` — same class `milestones_gate…:505` row 3 RULED
  RESOLVED (flip execution_scope→local-only) for sibling docs; these two never got the fix (both forked in the same
  07-24 4-way split).
- D2 [P3] `data_pipeline_e2e_milestones_gate_2026_07_24.md:141` parenthetical "it lives directly under plans/active/" —
  target archived 2026-07-28; correction note itself now stale.
- D3 [P3] `data_pipeline_reconciliation_skill_2026_07_20.md:34` related entry bare `issues/…` prefix (non-leading-
  slash).
- D4 [P3, epic caveat] `plans/epics/manifest_master.md:32` `assigned_vm: vm-defi` +
  `plans/epics/observability_master.md:37` `vm-cross-cutting` — retired multi-VM-era values; framework epic
  self-corrected to NA 08-02. Low confidence (epic frontmatter may be exempt).
- D5 [P3] `data_pipeline_reconciliation_skill…:11-12` banner "0 open / 42 done" vs actual 2 open / 44 done / 46 todos (4
  added since snapshot) — time-anchored but "is expected here" claim now misleading.

**B_J (features batch: v2 engines / features e2e / bigquery / sports precompute / forexfactory) — 2026-08-07:**

- J1 [P1] stale `last_updated` ×3: `v2_engine_venue_buildout…:23` (07-13 vs PL 08-01/03) ·
  `features_service_e2e_pipeline_test…:29` (06-03 vs 07-27 banner + PL 08-01/03) ·
  `bigquery_feature_ml_compute_engine_option…` (06-27 vs PL 08-01/03).
- J2 [P2] `v2_engine_venue_buildout…:787-789` "dispatched to AO" vs child `l2_book_microstructure_capture…:21`
  `assigned_vm: NA` — self-documented stale framing survives on the todo line (own closure note :799-802 admits it).
- J3 [P2] `features_service_e2e_pipeline_test…:19` (also `:103`,`:118`,`:728`) cites
  `plans/active/features_input_manifest_migration_2026_05_25.md` — file is at `plans/archive/2026_05/` (verified).
- J4 [P2] `features_service_e2e_pipeline_test…:46-54` `context_scope` cites 2 active plans
  (`data_completion_cefi_2026_07_15`, `data_pipeline_check_mdps_features_2026_07_20` — verified existing) absent from
  `related:` `:17-21`.
- J5 [P2] `plans/epics/mtds_mdps_master.md:725-728` roster "4 active plans" vs live 8 — same finding as C7 (merged).
- J6 [P2] `plans/epics/deployment_and_user_management_master.md:120-123` lists
  `data_status_page_ux_and_canonicalisation_2026_07_16` at `../archive/2026_08/` with "**status**: active" in the P1
  block, one refresh after the 07-30 note (:49-55) claims roster regenerated to 7 active.

**B_H (mtds/infra batch: file_size_refactor / venue_backfill / infra_capture ×2 / infra_ops_residual) — 2026-08-07:**

- H1 [P1] `plans/epics/manifest_master.md:49` + `:184-186` lists `migration_verification_orphan_safety_2026_06_10` as
  ACTIVE child — file at `plans/archive/`, `status: complete`, no supersession banner anywhere in epic (fork
  `infra_ops_residual…:117` cites the correct archive path).
- H2 [P1] `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md:316-319` open
  `[ ] [DATA] P0. B0 backfill instruments to NO-MISSING (runs FIRST)` vs own body `:133`,`:156` "tradfi B0 = COMPLETE;
  no action" + B2 (which B0 gates) `[x]` at UAC@b654eb6 — P0 text never narrows to remaining cefi/defi legs.
- H3 [P1] `mtds_venue_backfill…:447-452` SFI/TM verify todo names the ABORTED run-id fleet (`20260619-161036` SFI ×4
  - `tm-backfill-20260619-161123`) — same doc `:507-513` records the 4 chunks killed (self-inflicted 429s) and single
    stream `sfi-backfill-20260619-221723` relaunched; history doc: chunk-2of4 DELETED, wrote ZERO. Re-verify targets the
    wrong run-id.
- H4 [P2] `infra_capture_and_devops_leftovers_finalize…:66-90` 🟡 RE-VERIFIED banner "all 4 remain genuinely blocked,
  none silently stale" vs own todo-2 annotation `:178-198` (08-02): "2 of the 4 have cleared" (MANTLE paid-RPC
  UAC@1924bfed; Live-ODDS quota ruled 07-28; ASTER freeze lifted 07-28). Banner uncorrected.
- H5 [P2] `plans/epics/mtds_mdps_master.md:101-110` M-2 "⏸️ DEFERRED 2026-06-26" vs
  `mtds_file_size_refactor_2026_06_08.md:54` "🟢 RESUMED 2026-07-27" + `status: active`.
- H6 [P2] `mtds_venue_backfill…:64` cites `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` — file at
  `plans/archive/issues/` (same class as B_C's C4).
- H7 [P2] `mtds_venue_backfill…:428-429` FLEET-WIDE todo "homed under
  `data_source_provenance_all_asset_groups_2026_06_01.md`" — archived; live owner is
  `data_source_provenance_enforcement_2026_07_24.md`.

**B_E (data3 batch: standardisation / catalogue / partition_migration / warm-sink ×2) — 2026-08-07:**

- E1 [P2] `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md:463` M8 "PARTIAL — REMAINING: cadence
  column (UTL) + run_class + writer stamp" vs same-doc GATE-0 `:599`,`:605`,`:606-610` `[x]` (cadence column, deploy-
  api slice, UI slice SHIPPED) — 3 of 4 "REMAINING" items are `[x]` in the same doc; genuine remainder = run_class +
  writer stamp.
- E2 [P2] `master_data_canonicalisation_migration_catalogue_2026_06_07.md:330` WAVE-5 open todo lists shipped items
  (M3/M4/M7, `live_websocket`→`live_<source>`) as open scope vs standardisation `:597-598`,`:600-601`,`:611-616` `[x]`
  (GATE-0 9/9, `live_websocket` rg=0 fleet-wide) — genuine remainder = G5 backfills→100%, M6/M7, M8 wiring.
- E3 [P2] `plans/epics/batch_live_symmetry_master.md:68-69` "2 active plans" + `:77-78` P0 empty vs actual 5 active
  (incl. P0 `live_event_log_warm_sink_recovery…:25`,`:28`) — no roster disclaimer banner; last_updated 07-12.
- E4 [P2] `pipeline_mode_partition_migration_2026_06_01.md:87-92` rider table names 5 ARCHIVED plans as live riders +
  "no canonicalisation plan yet" cell vs archived `instruments_manifest_canonicalisation` complete. Self-flagged banner
  `:70-72` but table + Phase-1 todos un-updated.
- E5 [P2] `master_data_canonicalisation_migration_catalogue…:117-121` "NO `--apply` until G0+G1+G2+G3 GREEN"
  (unqualified) vs own Gate-State Board `:201-209` G4 `--apply` 🟢 applied 2026-06-29/07-06 while G2 🟡 — invariant
  paragraph untouched at 07-12 board refresh.
- E6 [P2, GRACE] `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md:63-66` counts two
  time-gated parent todos; one flipped `[x]` 08-02 (52-subs hold, cron fired); `:38` "10 total todos" vs actual 11.

## Doc-drift

**B_E (data3 batch):**

- Line caps: `master_data_canonicalisation_migration_catalogue` 900L · `pipeline_mode_source_batch_live_replay_std` 980L
  — both >500 soft, standardisation **20 lines from the 1000 hard cap** (riskiest doc in batch; no remediation banner
  unlike catalogue's 1289→953).
- Stale `last_updated`: warm-sink `:24` (07-31 vs PL 08-02/03) · finalize `:19` (07-31 vs 08-06 body note) · catalogue
  `:42` quoted-string `"2026-08-05"` (quote-style flag).
- Catalogue registry rows `:605`,`:606`,`:615`,`:621` name archived-complete plans without archive notation (P2;
  contrast G0 rows' "FOLDED→M-1, archived" style); `plans/epics/manifest_master.md:127` "16 active plans" vs 14 actual +
  `related_plans` cites archived `migration_verification_orphan_safety` (same class as H1).
- Huge-whitespace continuation lines in standardisation `~:796-826`,`:914-926` (6-space pasted blocks, P3).

## Codex-drift candidates (B_E)

- P2 `pipeline_mode_partition_migration…:114-115` flip-instruction targets
  `/codex/02-data/pipeline-mode-and-batch- live-reconciliation.md` text that moved ("Phase 5 DEFERRED" note → "IN
  PROGRESS riders", codex `:231-233`); codex per-bucket table `:236-245` mirrors the plan's stale table ("In L3 walk
  plan" ×5) rather than archived/ landed reality.
- P3 `/codex/02-data/pipeline-mode-partition.md:81` "Reader fallback removal (T+30d, ~2026-06-15) ⏸ deferred" — T+30d
  passed; flag for re-verify.

**B_A (closeout hub batch: hub / ag_closeout_audit_rollout / determinism child / asset_class rename / mvp) —
2026-08-07:**

- A1 [P0, GRACE] hub Track 9 `:352-355` `mtds_retry_safe_default_audit` "**NOT started**, 5 open / 0 done, AO- eligible"
  vs `plans/archive/2026_08/…` `status: complete` 5/5 `[x]` (mtds@0041a8a6 + PM@4d3713ade). Criterion `:363` now MET.
  Third side: `plans/epics/infrastructure_master.md:595-597` still lists it "**status**: active" (P2 — epic side
  fixable, not grace).
- A2 [P1, GRACE] hub Track 4 `:241`,`:248` models-MVP "BLOCKED-OPERATOR-DECISION / stays parked" vs ruling 2026-07-27
  - P2b shipped 07-28 (mvp `:166-170`,`:176` UAC@0fb9821b; batch1b retagged 07-29).
- A3 [P1, GRACE] hub Track 14 `:480` + open todo `:701-704` CF job "never successfully produced output, failing daily
  since 07-04" vs first complete 10-bucket rollup 2026-07-26 (`cf_manifest_audit_first_full_rollup…:5-7`); also cites
  daily-failure doc under ACTIVE path (`:480` — it's archived). Hub-internal discord `:178` disputes the framing yet
  Track 14 retained it.
- A4 [P2, GRACE] hub Track 14 `:493` vm_exec_stall "regex fix identified, VM relaunch/verify in flight" vs archived
  `vm_exec_stall_watchdog_checkpoint_regex_mismatch` `status: resolved` 08-03 (postdates hub's own last_updated).
- A5 [P2, GRACE] hub Track 10 `:370` e2e "stuck behind STALE hold banner… escalate" vs
  `features_service_e2e_pipeline_test…:64` "✅ HOLD LIFTED (2026-07-27, operator decision)" — criterion `:373` met.
- A6 [P2, GRACE] hub Track 12 `:419` `silent_wrong_answer_bucket_resolution_class…` cited at ACTIVE path — archived
  `status: resolved` (own frontmatter `related:` :69 uses archive path).
- A7 [P2/P3] `last_updated` lags Progress Log in all 5 batch docs (ag_closeout_audit_rollout worst: 07-25 vs log through
  08-06, 12 days).
- A8 [P3] "8 source docs" vs 10 listed — `cross_cutting_strategy_execution_determinism…:7`,`:9`,`:94` + hub Track 24
  `:695` (self-aware via re-verify todo, cosmetic).
- A9 [P3] `mvp_scope_catalogue_tagging…:172` "(draft)" descriptor stale vs batch1b `status: active` `:14`.

## Doc-drift

**B_A (closeout batch):**

- Line caps: hub 885L · ag_closeout_audit_rollout 987L — both >500 soft, <1000 hard.
- NEAR-COMPLETE: hub (1 open), ag_closeout (1 open), determinism child (1 open) — all GRACE docs.
- Space-corrupted doc refs in hub (P3): `:352`,`:369`,`:370`,`:350`,`:178` (e.g.
  "`features_service_e2e_pipeline_test_ 2026_05_26.md`").
- `ag_closeout_audit_rollout:15` status comment `# was: complete (2026-07-25)` 13 days stale (P3, GRACE); hub PL
  ordering 07-27 entry after 07-25/26 (P3).
- P2 `plans/epics/infrastructure_master.md:595-597` P3 backlog marks archived mtds doc "status: active" (path repointed
  :46, status not); BOTH cross-cutting children missing from infra_master inventory despite
  `parent_epic: infrastructure_master` (grep 0 hits; contrast AOF/instruments_master which list children correctly).
- Cleared: `execution_scope: orchestrator-agent` on mvp IS canonical (PLAN_FORMAT.md:99,143 — closed set of two).

## Near-miss flips (B_A — flag, not flip)

- `ag_closeout_audit_rollout…:114-118` (GRACE) open todo's first half evidence-complete in-doc (`:955-958` "all 34 open
  entries resolved… 0 `**Status**: open`"); mass-flip half genuinely open (`:963-966` partially done) → re-scope
  candidate.

**B_G (instruments batch: tracker / foundation / phase0 / residuals / store_cf / is_catalogue / extra_forbid) —
2026-08-07:**

- G1 [P1] tracker `instruments_completion_tracker…:698-701` "na-eligibility-audit 2026-08-03: **Closed 1 checkbox**
  (generic manifest-reprocessing utility)" vs `:556-560` checkbox still `- [ ]` "STILL OPEN (reconciled 2026-07-28) —
  genuinely unbuilt"; supporting issue `plans/archive/issues/manifest_reprocessing_generic_utility…` `status: resolved`.
  Progress Log vs body directly contradictory; flip candidate.
- G2 [P2] tracker `:90-93` "STILL PENDING" banner (post-apply chain) vs own Stage-1 `[x]` `:210-216` (orphan-sweep E=0,
  E5 rebuild, IS enumerate-seed, IS catalogue all done 07-06/09/10) — only "Ikenna's migration sign-off" genuinely
  pending.
- G3 [P2] `instruments_foundation_phase0_cross_cutting…:376-383` granularity-aware producer "STILL OPEN, unbuilt, no
  evidence" vs same doc `:417-422` "Catalogues — ALL 5 AG regenerated + promoted (2026-06-26, monotonic ACCEPT)… builder
  auto-handles league/cqg grain" (sports 1,608 + prediction 1,204,816 promoted on that producer).
- G4 [P2] `instruments_foundation_completeness…:200-201`,`:347-348` "G4 OPEN pending D2" vs D2 LANDED (tracker
  `:444-446`; `cefi_layer1_denominator_gaps…` archived resolved) — should read "pending re-verify"; open-ness itself
  intentional (tracker :446-447).
- G5 [P2] `instruments_foundation_completeness…:46-47`,`:214-215`,`:283-286`,`:350-353` cite ARCHIVED defi/sports plans
  as live work homes (`defi_instrument_catalogue_and_capture_pipeline` [complete], `sports_fixture_completeness_oracle`
  [complete]) — self-acknowledged `:366-368` "flagged for /plan-reconcile, not rewritten here" → THE fix candidate.
- G6 [P2] `instruments_mtds_consistency_remediation_residuals…:9` summary "14 residuals remain open" vs actual 7 (own PL
  `:926-929` "2 of 7 open items") — reader sees double the residual work.
- G7 [P3] tracker Stage-6 `:528-533` "flip stale checkboxes" — 3 of 4 named targets already flipped (N9c RESOLVED,
  migrate-first-4-AGs moot, incremental_rollup complete); only N5r/N6r open.
- G8 [P3] foundation `:346` "11 items still `- [ ]`" vs phase0 doc 13 open.
- G9 [P3] tracker Stage 0 `:198-200` both halves resolved (both docs archived complete; operator unlock DID happen) —
  "operator unlock REQUIRED" premise no longer holds.

## Doc-drift

**B_G (instruments batch):**

- Line caps: residuals 929L (71 from 1000 hard — watch/split next edit) · tracker 704L · phase0 619L — >500 soft.
- Stale `last_updated` 6 of 7 docs (extra_forbid GRACE; foundation/phase0/residuals/store_cf/is_catalogue).
- P3 `is_catalogue…:71-72` doc-purpose tension: "historical/audit record, not gating anything" while holding 3 open P0
  todos. Mojibake `residuals:647` (`ðŸŸ¢ IN PROGRESS`). Sha truncation inconsistency foundation `:216` (`1407b7fd`) vs
  tracker `:456` (`1407b7f`).
- Cleared: no terminal-in-active, no superseded-while-active, no archive candidates; instruments_master epic lists all 6
  children with matching estimates.

## Near-miss flips (B_G — flag, not flip)

- G-F1 [P1] = G1 (tracker utility checkbox; flippable with PL entry + archived issue).
- G-F2 [P1] `residuals:643-654` F1 Kraken backfill — 7-week-old "🟢 IN PROGRESS… ETA ~1h" note frozen since 06-18;
  08-01/08-06 audits reviewed without resolving → verify-complete-or-refresh candidate.
- G-F3 [P2] `is_catalogue…:249-253` G1.code open though own banner `:80-86` records "CODE SHIPPED 2026-06-07"
  (uac@97c26dbe + is@6ea46565, both QG green) — stale pre-ship text.
- G-F4 [P2] `is_catalogue…:287-295` G1.run vs `:308-312` `[x]` G1.run-bounded (4 AG live-window seeds materialised
  06-19) — same act described twice; reframe or flip bounded part.
- G-F5 [P2] `instruments_store_cf…:211-218` bar-edge fix COMMITTED is@20a92886 (08-05) but BLOCKED on repo-blocker
  RB-d3bb9020 (IS QG red, `test_sports_fixture_stamps_canonical_instrument_id`) — correctly open (commit ≠ shipped);
  surface so the committed fix doesn't rot.
- G-F6 [P3] `is_catalogue…:254-260` G1.dry-run — 2-3 of 5 AGs DONE in-body.
- G-F7 [P3] tracker Stage-3 `:385-392` tradfi cert relocated to `tradfi_consolidated_closeout…` Phase C — flip-with-
  pointer candidate.

## Codex-drift candidates (B_G)

- P2 instruments-service QG red (RB-d3bb9020) blocking committed is@20a92886 — code-health signal for daily runner (not
  text drift). P3 G1-gap list check (TRADER_JOE_V2… vs UNISWAP_V4 cells migrated canonical — different axes).

**B_I (strategy batch: carry_staked / ensemble / citadel / colocated / cross_venue / daily_analyst) — 2026-08-07:**

- I1 [P1] `colocated_feature_pipeline_in_memory_handoff…:77-83` (1.3b) + `:93-103` (1.7e) open SUPERSEDED-BY-BATCH1 vs
  batch1 `:152-153` `[x]` @features-service/3162d627 (QG 18261 passed) + `:155-156` `[x]` @43a2b56b — colocated's own
  contract (:66-67 flip-both-copies-together) not honoured → flip candidates.
- I2 [P2] citadel `:811-814` single 08-02 PL entry self-contradicts: "DELETED the duplicated P2.11.18 fragment (11→ 10)"
  then "a literal duplicated `- [ ] [CODE] P2.11.18` line still inflates count" — grep: exactly ONE P2.11.18 (`:551`);
  stale sentence.
- I3 [P2] ensemble `:334-335` PL (08-02) calls `[HISTORICAL] P3` "stale open checkbox" vs `:132` `[x]` FLIPPED 07-31
  (UAC@487b9a9 + strategy-service@6b285fad) — postdates the flip, wrong about doc's own state.
- I4 [P2] rank-allocator fold tracked open in TWO active sibling plans: cross_venue `:173` (CarryStakedBasisRank-
  Allocator) + ensemble `:118`/`:114`/`:145` (CarryFundingDispersionRankAllocator) — double-dispatch risk; split docs
  disagree on ownership.
- I5 [P2] epic counts both directions: batch_live_symmetry "2 active plans" vs 5; strategy_master "9 active" vs 8 (9th
  related_plans entry `:47` is archived vol_dvol).
- I6 [P2] carry_staked twin todos: `:274`/`:535` lending-indices legacy-bucket writer fix; `:203`/`:267` Aave- Ethereum
  backfill — one item two checkboxes each (inflates 28-open count by 2).
- I7 [P2] stale issue-path cites (active vs archive): carry_staked `:74`, citadel `:157`,`:138`, ensemble `:40`.

## Doc-drift

**B_I (strategy batch):**

- Line caps: citadel 819L · carry_staked 770L · cross_venue 518L — >500 soft, <1000 hard.
- Stale `last_updated` ALL 6 docs (carry_staked 07-24 vs PL 08-03; ensemble 07-24 vs 08-02/03; citadel 07-24 vs
  08-02/03; cross_venue 07-24 vs 08-03; colocated 07-27 vs 08-05; daily 07-29 vs 08-04/05 — GRACE).
- carry_staked **28/28 todos open** — zero completion signal despite PL journaling shipped `--live` work (see flips
  below); highest open-count in tranche.
- `daily_trading_analyst…:48` `source: [blrs_g3_g10_rescope_2026_07_28]` bare slug (GRACE, P3).
- citadel register §D `:160` bullet carries no `[x]`/`[ ]` marker (noted for consistency, not an error).

## Near-miss flips (B_I — verify candidates, strong in-doc evidence)

All `carry_staked_basis_funding_scan_experiment…` unless noted (PL `:405-531` journals shipped; todos open):

- I-F1 [P1] `:602-606` `--live` multi-venue snapshot mode vs PL `:409-412` shipped e2e-testing@6e2ffb8 (14 venues, 446
  funding points, coins 30→40, cash-margin default — every spec element present).
- I-F2 [P1] `:619-620` dYdX v4 + Vertex wire vs PL 06-17 + `:409` (both PUBLIC, wired at 6e2ffb8).
- I-F3 [P2] `:633-634` live/paper history carve-out vs `:407` (operator 06-17 carve-out in shipped commit).
- I-F4 [P2] `:651-652` liquidity snapshot constant backfill vs `:452`.
- I-F5 [P2] `:667-668` HYPE HL-S3 history pull vs cross_venue `:154-155` `[x]` 100% coverage 2023-05-20→2026-06-09
  (1117/1117 days, 0 gaps, mtds@98d12be) — HYPE listing window inside corpus.
- I-F6 [P2] `:628-630` Drift creds/RPC — harness half shipped at 6e2ffb8; production MTDS remainder tracked `:622` →
  partial-flip candidate.
- I-F7 [P2] cross_venue `:423-424` capacity-book productionise — [floor,cap] rail shipped in ensemble
  (e2e-testing@5eef20f); script extension specifically remains open (low confidence).
- I-F8 [P1] colocated 1.3b/1.7e = I1 above.
- Verification note: I-F1..F6 shas live in the e2e-testing repo — verify `git merge-base --is-ancestor` from that clone
  in STEP 4.

## Codex-drift candidates (B_I)

- P2 `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md:159` plan_reconciler scheduled-jobs table
  "systemd timer, daily 01:00 UTC, opus/max" vs live reality "hourly-retry, sonnet-forced" (daily_analyst §1
  code-verified) — fix ALREADY tracked as open §5 todo `daily_trading_analyst…:324-327` (GRACE doc). No codex rewrite
  this run (operator ruling required); route via /blocked.

**B_F (bucket batch: 5 fold docs + IAM + closeout + decommission + finalize) — 2026-08-07:**

- F1 [P1] `legacy_bucket_dual_write_decommission…:167` "cefi/defi/tradfi/sports unaffected, this item stays open for
  them" (L6 legacy flat-tick decommission) vs `bucket_estate_consolidation_closeout…:120-121` "Legacy flat
  tick+instruments twins (−8) — **ALL 8 CONFIRMED DELETED**" (404 evidence through 07-17, updated 07-31). Decommission
  L6 also covers tier-first/long-form shapes → partial-non-contradiction possible, but flat twins in BOTH scopes;
  decommission `:181-182` version counts also stale if buckets deleted.
- F2 [P1] `bucket_fold_ml…:154-157` open P0 treats `ml-models-store` delete as agent-executable ("This also closes the
  parent plan's W2 flat-`ml-models-store` delete todo — flip it too") vs
  `bucket_estate_consolidation_closeout… :166-177` "**NOT executed — this is a HARD STOP, not a judgment call**: 'Any
  prod-bucket delete… Human executes; agent suggests'… Ready-to-run for the operator". Two ACTIVE docs disagree on
  agent-vs-human authority for the same prod bucket → execution-authority ambiguity, ROUTE-worthy.
- F3 [P2] `bucket_fold_portfolio_state…:151-152` "**ALL 5 FOLDS NOW COMPLETE**" while fold_ml delete `:154` open +
  closeout `:143-147` ml legacy variants open.
- F4 [P2, GRACE: IAM] decommission `:114-117` "⏸️ GATED on G4 applies — all 5 AG `--apply` still `[ ]` (2026-06-12)" vs
  IAM `:159-161` "G4 🟢 all 5 AGs (updated 2026-07-12)".
- F5 [P1] `bucket_iam_write_protection_per_tier_2026_06_09_finalize…:12` `status: active` vs `:58` "**STATUS: `draft` —
  NOT dispatched**" — with `assigned_vm: planning` + `gate_on_depends: true` + parent holding 2 open todos (P1.3 :271,
  P2.1b :297): frontmatter value risks AO dispatch of a self-declared-undispatched doc.
- F6 [P2] `plans/epics/infrastructure_master.md:595-597` indexes archived-complete `mtds_retry_safe_default_audit` as
  "**status**: active" under P3 backlog (dup of A1 third side — merge).
- F7 [P2] `plans/epics/infrastructure_master.md:498` "19 active plans declare parent_epic" vs ACTUAL 45
  (`rg -l '^parent_epic: infrastructure_master' plans/active/*.md`).
- F8 [P2, GRACE] IAM `:7-8` summary "Group B phase blocked on the env-split rollout plan" vs body `:115-131` (env-split
  archived/superseded 07-13; dev/stg retired).
- F9 [P2, GRACE] IAM `:271-272` open P1.3 "Verify dev/stg workloads… IAM-denied a `-prd-` write" vs same-doc retirement
  banner `:122-127` (dev/stg PERMANENTLY retired 07-13) — AO worker could pick it up against retired tiers.
- F10 [P3] closeout `:121-128` −8 enumeration muddle: "6 of 8 (…)" + "instruments-store-cefi (the 7th/8th)" + "remaining
  2 (sports pair)" = 9 items for an 8-bucket set.

## Doc-drift

**B_F (bucket batch):**

- Non-canonical `[~]` todo markers (both done-work in disguise, P2): `bucket_fold_features…:95` (BUCKETS PROVISIONED —
  content absorbed by `[x]` cutover UAC@cb951936/UTL@4f0bcc34), `bucket_fold_ml…:158` (TF-STATE RECONCILE — "DONE
  2026-07-18", flip blocked by own BIG FINDING 32 IAM/scheduler destroys :164-172).
- [P3, GRACE] IAM malformed todos: `:133` `- [x] ✅ **Tier set — RESOLVED**` (no `[TAG]`, no `P#`); `:146`
  `- [x] ✅ P0.0.` (non-canonical priority).
- [P3] NEAR-COMPLETE: IAM finalize 1 open todo.
- [P3] Deprecated epic `assigned_vm`: `infrastructure_master:28` `vm-cross-cutting` · `mtds_mdps_master:71` `vm-ml`
  (same class as D4).
- `last_updated` behind body batch-wide (closeout 07-25 vs 07-31; decommission 07-24 vs 08-03; IAM 07-31 vs 08-06; 4
  fold docs 07-17 vs 07-31/08-06; finalize 07-30 vs 08-03).
- [P3, GRACE] IAM 725 lines > 500 soft; IAM `:18` `related:` cites `plans/active/cicd_contract_hardening_2026_06_01` —
  verified ABSENT from active AND archive.
- [P3] closeout `:99` placeholder sha `unified-trading-pm@<see plan-flip commit>`; execution_strategy `:74` 🟡
  "MIGRATION IN FLIGHT" banner with 6/9 todos done.
- ARCHIVE-CANDIDATES: none (every batch plan ≥2 open todos).

**STEP-4 verification results (mechanical, shas) — 2026-08-07:**

- ✅ ANCESTOR-of-LDR + artifact live: deployment-api@cf55369 (IF1) · features-service@3162d627 + @43a2b56b (I1 colocated
  1.3b/1.7e) · mtds@98d12be (I-F5 HL backfill) · agent-orchestrator@623009e3 (wip-preserve sweep, ancestor yes but
  age-threshold alert unrecorded → flag) · agent-orchestrator@0a8ed16 (IA2) · instruments-service@96ea6c4b re-stamp
  confirmed (I3 IF2; identical content e324dff2 IS ancestor).
- ⚠️ **e2e-testing re-stamp pattern**: carry_staked PL-cited shas (6e2ffb8, 37dcede, 5eef20f, 3d219d7) are NOT ancestors
  of origin/live-defi-rollout — they resolve on origin/main (promoted lineage); LDR carries the SAME commits re-stamped
  (6e2ffb8 → **326a345**, diff = sports/live.env only, 3 lines). Root cause = the 08-05 provenance-marker Option-B
  direct promote rewrote e2e-testing main's lineage (matches I3 IF2 class). → flip candidates I-F1..F4 must cite the
  LDR-resolvable re-stamp (326a345) with a note, NOT the PL-cited sha.
- ✅ M2: `ml-store` key PRESENT at `configs/cloud-providers.yaml:70` (Fold-B comment) → flip candidate confirmed.
- ✅ G1 support: `plans/archive/issues/manifest_reprocessing_generic_utility_2026_07_07.md` `status: resolved`.
- NOT flips (verified open): e2e-testing LDR/main DIVERGED (neither ancestor — Option-B recreate 08-05); I-F6 (Drift
  production remainder tracked :622) partial; I-F7 low-confidence; IF2 (glue_runner cite unresolvable); fleet #791 still
  OPEN/DIRTY.

## Near-miss flips (I1 — flag, not flip)

- `slot2_wedged…` `[BACKEND] P2` — escalation code IS live (`worker_liveness_watchdog.py:2179,2184-2186` resume cap 1,
  config.py:490; AO@e608378 ancestor) but 2nd half (`phase=pre_boot` bookkeeping mismatch) un-evidenced → flag, not
  flip.
- `wip_preserve…` `[SCRIPT] P3` — `server/orphan_ref_verify_watchdog.py` (AO@623009e3, ancestor) implements the hourly
  sweep, but "age-thresholded alert OR documented runbook check" unrecorded; NEW unrecovered ref live in slot-13 UTL
  clone (`cascade-unified-trading-library-e4f136a9382a`) → surfacing still not effective in practice.
- `ao_park_disposition…:90-93` `[x]`'s "**Not live-verified end-to-end**" caveat — done-when since met by others
  (`sports_af_full_entity_completion…:210-220` POST /park 08-04 confirmed parked:true; ao_done_gate…:181) →
  cross-reference resolution candidate.
- Verified NOT flips: fleet #791 open/dirty; review_boot `[DOCS] P1` + `[BACKEND] P2` genuinely open; benchmark 4 open;
  watchdog_gaps `[INFRA] P2` no execution evidence.

## Doc-drift

**I1 (AO/fleet batch):**

- Placeholder sha: `orchestrator_vm_disk_io…:176-177` `unified-trading-pm@<SHA>` never resolved.
- Archive candidate (operator review): `ao_park_disposition…` — `status: resolved`, all todos `[x]`, but
  `locked_by: live-defi-rollout` blocks archival (`[unlock-plan]` needed); `locked_since: 2026-05-21` PREDATES
  `created: 2026-07-31` (frontmatter defect).
- Stale `last_updated`: benchmark doc 08-03 vs PL 08-06 (GRACE).
- All 9 docs ≤447 lines (no cap breach). Codex refs all resolve; stale line-number cites noted (prompts.py:111-124,
  backlog.py:709) — not drift.

## Near-miss flips (B_F — candidates with caveats)

- M1 [P2] alias-sunset group (fold_ml `:238-241`, fold_features `:167-168`, execution_strategy `:179-180`,
  portfolio_state `:163-164`): UTL half (UTL@055948e33) + yaml half (deployment-service@a91e520f) both LANDED per
  closeout `:183-213` + features `:371-375`; residual = never-run live `tofu plan` verify — flip should follow that
  final verify.
- M2 [P2] fold_ml `:233-237` PM mirror re-sync — `ml-store` key ALREADY PRESENT at `configs/cloud-providers.yaml:70`
  (with Fold-B comment) — deliverable present; gate evidently cleared.
- M3 [P2] fold_features `:95-103` `[~]` Provision todo — content absorbed by the `[x]` atomic cutover `:113-116`.
- M4 [P2] fold_ml `:158` `[~]` TF-STATE RECONCILE self-declared DONE — candidate-with-caveat (BIG FINDING 32 destroys
  keeps it operator-aware).
- NOT candidates (verified open): IAM P2.1b (`:297` — removal + post-removal P2.3 re-run not executed; RULED APPROVED
  AO-dispatchable 08-06), IAM P1.3 (`:271`), AWS legs ×2, closeout recon-bucket (`:81`), closeout ml-models-store
  (`:143` deliberately `- [ ]`).

## Codex-drift candidates (B_F)

- Clean: `/codex/05-infrastructure/bucket-isolation-model.md` reflects folded shapes (`:142-150`, SUPERSEDED banner
  `:152-153`).
- P3 `infrastructure_master:725` embedded codex-SSOT summary (2026-05-26 vintage) stale on consolidator estate shape vs
  fold docs (consolidator retargeted single-root, legacy crons paused-not-removed) — note only;
  `manifest-consolidator-ssot.md` itself not re-audited (out of shard scope).

**I3 (CI/deploy issue batch, 12 docs) — 2026-08-07:**

- IC1 [P2, GRACE] `prod_mutation_evidence_artifact_gap…:87` "**RULED 2026-08-06: YES, extend it**" vs same todo `:90-95`
  "Rule on whether to extend the §8b evidence-backing contract…" — ruling declared both done and pending in one todo
  (frontmatter already reclassified planning `:115-123`).
- IC2 [P2, GRACE] `provenance_marker_broken_by_history_rewrite…:3-8` title+summary "…AND alerting-service are stuck" vs
  PL correction `:238-249` (live-verified alerting marker `ancestor=True`, "never broken by this bug"; SIT-gate timing)
  — title mis-routes alerting work to wrong doc.
- IC3 [P3, GRACE] `provenance_marker…:167-168` "No parallel tactical unblock needed" vs `:171-175` "**Tactical unblock
  in parallel**" — same todo asserts both (retag leftover).
- IC4 [P3, GRACE] `gcp_service_accounts_registry_diverged…:116-122` "**DEFAULT-RULED 2026-08-06 … option (a)**" vs
  "**Decide direction (a) vs (b)** … Blocks the rest" — decision both made and pending in one todo.
- IC5 [P3, GRACE] `agent_orchestrator_stale_pm_workflow_ref…:23-28` claims promote PR #813 is the promotion path with
  "real, large, multi-file conflict" — live: #813 closed; #815 (opened 08-06T23:41Z) is current promote PR; todo 3
  ("Reconcile PR #813's conflict") targets a closed PR.
- IC6 [P3, GRACE] `glue_runner_units_stopped…:336-337` PL "P2 still correctly scoped to agent-orchestrator" vs corrected
  todo `:147-149` + context-scout `:367-369` (watchdog lives in unified-trading-pm; "no such path exists" in AO).

## Flips verified

- IF1 ✅ **CONFIRMED FLIP CANDIDATE (non-grace)** —
  `deployment_api_artifact_pipeline_health_test_date_drift_flake _2026_07_29.md:90-101` open `- [ ] [CODE] P3` whose own
  body documents "**SHIPPED deployment-api@cf55369**"; hunter ran
  `git merge-base --is-ancestor cf55369 origin/live-defi-rollout` → **yes**; artifact live —
  `tests/unit/api/test_artifact_pipeline.py:881` computes `two_days_ago = (datetime.now(UTC) - timedelta(days=2))`,
  `:879-880` comment cites this exact bug. Needs `- [x]` + sha (also makes the doc a near-complete → archive candidate).

## Near-miss flips (I3 — flag, not flip)

- IF2 [GRACE] `glue_runner_units_stopped…:76-87`,`:311-318` `[x]` cites `instruments-service@96ea6c4b` "shipped to LDR
  (verified ancestor)" — `git merge-base --is-ancestor 96ea6c4b origin/live-defi-rollout` → **NO** (lives on
  `origin/wip-preserve/slot-5-…-20260805T111826Z`); identical-content `e324dff2` (diff-stat empty) IS ancestor —
  post-08-05-rewrite re-stamp. Content on LDR under different SHA; cited evidence doesn't resolve as written.

## Doc-drift

**I3 (CI/deploy batch):**

- `artifact_pipeline` doc: `last_updated: 2026-07-29` stale vs PL through 08-06; `author: unknown`; near-complete (1
  open todo = IF1).
- `promote_ref_orphaned…`: frontmatter missing `estimate_class`/`estimate_baseline_ai_days`/
  `estimate_calibrated_ai_days`/`assigned_role` (PLAN_FORMAT-required); todo `- [ ] [P3]` no role tag; todo P3 vs
  frontmatter `priority: P2` mismatch.
- `gcp_service_accounts…`: PL 08-01 entry truncates mid-sentence ("…is stated…").
- CLEARED: `deployment_api_events_global_state…` `status: open` + `resolved_by` set = intentional re-open per
  `check_terminal_status_archived` (open P3 follow-up), NOT a defect.
- Archive candidates: none (every doc ≥1 open). Line caps: max 425, no breach.

## Doc-drift

**B_H (mtds/infra batch):**

- > 500 soft: `mtds_venue_backfill` 586L · `infra_capture` 602L (GRACE doc flagged for size only). <1000 hard.
- Frontmatter pairing mismatch (P3, same class as D1): `mtds_file_size_refactor:25-26` + `mtds_venue_backfill:47-48`
  `assigned_vm: NA` + `execution_scope: orchestrator-agent` (`infra_ops_residual:33-34` pairs correctly).
- Stale `last_updated`: `mtds_file_size_refactor:31` (07-12 vs banner 07-27 + PL 08-01/03).
- NEAR-COMPLETE (informational): `infra_capture_finalize` 1 open (intentional, baseline-1 coverage, documented).
- Archived copy `plans/archive/infra_capture_and_devops_leftovers_2026_07_06_finalize_2026_07_25.md` correctly
  `superseded` + `superseded_by` — properly bannered, NOT a finding.
- Roster drift `mtds_mdps_master:725-753` "4 listed" vs 7-8 actual — merged with C7/J5 (P3, epic disclaimer covers).

## Near-miss flips (B_H — flag, not flip)

- `infra_ops_residual…:94-120` RESUME-runbook todo — own annotation 08-03: gate cleared + runbook "already EXECUTED"
  (`tradfi_v9_stage1_finish` now archived); todo text still frames runbook as not-yet-run → re-verify vs live cron state
  per its own annotation.
- `infra_capture…:177-178` (GRACE) ASTER connector EXECUTED 07-30, checkbox deliberately open; verification re-homed to
  `issues/cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30.md` (exists, open); VM gone from fleet, zero
  `live_aster` rows 07-30→08-01 — gate (rows landing) genuinely unresolved.
- `mtds_file_size_refactor…:124-125` gate-verify todo — both split todos `[x]` cite MTDS@6f753c5cb (≤900 lines `wc -l`)
  but no green-QG run cited after split; boundary-restoration claim un-evidenced → needs verify, not flip.
- Line caps: `reconciliation_skill` 977 lines (>500 soft, 23 from 1000 hard) · `hardening` 584 · `milestones_gate` 519 —
  all <1000 hard.
- `self_healing…:25-26` quoted YAML strings `created:"2026-07-24"` / `last_updated:"2026-07-24"` + last_updated NOT
  bumped despite 08-02/08-06 PL entries (P3).
- NEAR-COMPLETE (informational): `hardening` exactly 1 open todo (L529), open state deliberate per 08-06 KEEP-NA.
- ARCHIVE-CANDIDATE check: `milestones_gate` 0-open active but EXEMPT (archive_exempt: true, standing reference per its
  own banner L15-19, KEEP-NA 08-02/08-06) — expected, NOT a candidate.

**B_J (features batch):**

- Line caps: `features e2e` 760L, `v2` 803L (>500 soft, <1000 hard). `task_template.md` 570L > 500 soft — GRACE.
- Line-number citations (P2, template §3): `features e2e:90` (staked_basis.py:450), `:588-590`
  (timeframe_resampler.py:93), `:128` ("17 CLI FEATURE_GROUPS (parser.py)").
- Inline YAML comment in frontmatter (P3): `forexfactory:14` `# corrected 2026-08-02 ag-closeout-audit…`.
- Stale deferral marker (P3): `features e2e:693`,`:711` "Re-check before dispatch (2026-07-27)" — no newer check in PL
  through 08-03.
- Epic-internal open todos (P3, epics not ingested): `features_and_ml_master:220`,`:396-416`,`:820`,`:824`;
  `mtds_mdps_master:405` (MDPS densify "Handed to slot-1-main 2026-06-02" — open with 06-02 hand-off marker),
  `:526/:528/:531`,`:573/:580`,`:845/:851`.
- NEAR-COMPLETE (informational): `sports_prediction_mvp…` 1/1 open — deliberate scope-risk STOP, not a candidate.

## Codex-drift candidates (B_J)

- P2 `v2_engine_venue_buildout…:525` open
  `[DOC] P2. If any engine family ships, update codex/09-strategy/architecture-v2/archetypes/…` — 20 engine families
  report SHIPPED; archetype doc update pending by the plan's own condition.

## Doc-drift

**B_B (satellites batch):**

- Stale `last_updated`: `batch1b` (07-27 vs PL 08-06; GRACE) · `context_scout` (07-30 vs PL 08-06) ·
  `june_2026_vintage_audit_findings` (07-28 vs PL 08-06).
- Placeholder evidence shas in `[x]` todos (P2): `batch1…:90`,`:299`,`:350` "unified-trading-pm@<see plan-flip
  commit>" — evidence-backed-completion check cannot resolve.
- Malformed todo ordering: `batch1…:210` `- [x] ✅ [DATA]` (✅ after [x]) · `vintage…:304` `- [x] [PLAN] P2.` (no ✅) ·
  `vintage…:847` mixed.
- `batch1b` todo-count drift: "All 17 todos" banner vs actual 18 (P3; GRACE).
- `vintage` bare-slug refs (no leading slash, P3): `:179`,`:200`,`:296`,`:339`,`:401`,`:445`.
- Epic-side: `plans/epics/infrastructure_master.md:595-597` lists `mtds_retry_safe_default_audit` as active pointing at
  `../archive/2026_08/` — doc is archived `status: complete` (P2). Epic `related_plans` + P0-P3 omit the 4 batch docs +
  finalizes declaring `parent_epic: infrastructure_master` (P3). `plan_hygiene_master.md:172` 2026-05-23-era
  stale-deadline todo (P3, out-of-batch noted).

## Near-miss flips (B_B — read-refuted, honestly open)

- `batch1b…:110-118` open todo with 2 of 3 sub-items strike-through-DONE with shas (features-service@60992d3e,
  @7717fbee, e2e-testing@4b5a743, PM@aa8f111, features-service@ce369620); item 3 (script-homes sweep) genuinely open,
  gated on `repo_scripts_governance_audit_2026_06_18.md` → re-scope candidate (GRACE).
- `vintage…:200` dual-track migration todo: batch1b perp-funding leg SHIPPED (RESOLVED 08-06, batch1b:310,
  UAC@66297dc4); tracker Stage 2c/GAP-4 leg keeps it alive → annotation candidate.
- `vintage…:351-352` SUPERSEDED todo's predicate "batch1b hasn't run" now false (batch1b 16/18 [x], ModelsMvpRule
  UAC@0fb9821b; live tracking = batch1b:604) → re-annotation candidate.
- `context_scout…:148` P0 corpus backfill = documented intentional cross-track duplicate with
  `ao_satellite_ao_dispatch_batch3_2026_07_31.md` todo 1, KEEP-NA-STALE 08-01/08-06 — NOT a violation, no action.
- Stale `last_updated` (Progress Log/body postdates it): `data_completion_to_100…:40` (08-03 vs 08-06 ruling; GRACE) ·
  `data_feed_sla…:23` (06-27 vs 08-05) · `data_pipeline_ag_residual…:29` (07-24 vs 08-03) · `data_pipeline_alerts…:37`
  (07-15 vs 08-05; GRACE) · `data_source_provenance…:30` (07-24 vs 08-03) · `plans/epics/observability_master.md:57` ·
  `plans/epics/mtds_mdps_master.md:80`.
- Stale Progress-Log count: `data_pipeline_alerts…:131` "both remaining open todos unchanged" — doc has 1 open (GRACE).
- `repos:` frontmatter template-copied (omits actually-touched MTDS/MDPS/UAC/UTL/IS/execution/strategy/features):
  `data_completion_to_100…:14`, `data_feed_sla…:11`, `data_pipeline_ag_residual…:17`, `data_source_provenance…:14`
  (alerts doc's list is accurate).
- WONTFIX left as open `- [ ]`: `data_source_provenance…:186` (vs the closed-`[x]`-MOOT convention M-1 used for the same
  Massive-removal class at `data_completion_to_100…:689`).
- Line caps: `data_completion_to_100…` = 814 lines > 500 soft (its own comment `:40` claims "943 lines" — stale
  self-ref; GRACE). All 5 data docs otherwise under cap.
- Bare-slug ref (P3): `data_completion_to_100…:98` cites `migration_verification_orphan_safety_2026_06_10.md` pathless —
  file lives in `plans/archive/`.
- Zero-completion signal: `data_source_provenance_enforcement…` 19/19 todos open, 0 flipped since verbatim migration
  2026-07-24 (3 audits, no completion signal).

## Near-miss flips (B_C — read-refuted, honestly open)

- `data_feed_sla…:141` msgpack bump 21/23 shas shipped; 2 repos BLOCKED on foreign gates (agent-orchestrator /
  alerting-service) — correctly unflipped.
- `data_source_provenance…:199` audit tool BUILT (read-only); PROD run sequenced post-backfill — open honest.
- `data_source_provenance…:106`/`:145` tradfi slice DONE w/ shas (UAC@637288d4 + mtds@0579438); cefi case + wiring
  REMAINING — open honest.
- `data_completion_to_100…:148` gate-check cites `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` as tracking
  home (verified exists + active) — correctly open elsewhere.

## Hygiene fixes

(none yet)

## Filed

(none yet)

## Archive candidates (operator review)

(none yet)

## Refuted (dropped by verify)

(none yet)

## Coverage (hunters / batches / docs)

(none yet)

## Plans not reached

(none yet)
