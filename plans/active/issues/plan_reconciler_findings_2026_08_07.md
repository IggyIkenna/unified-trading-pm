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

## Flips verified

(none yet)

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
