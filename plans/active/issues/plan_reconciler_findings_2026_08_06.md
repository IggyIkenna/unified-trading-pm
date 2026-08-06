---
doc_type: issue
title: plan_reconciler findings — 2026-08-06 (cefi tranche shard)
summary:
  Run-findings doc for plan_reconciler dispatch agt-bf8439 (cefi tranche). Fan-out DETECT + adversarial VERIFY over the
  cefi corpus; only CONFIRMED items acted on. Grace-window docs are read-only and reported.
status: open
nature: process
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan_reconciler, findings, reconciliation, cefi]
related: [/plans/active/cefi_consolidated_closeout_2026_07_18.md]
created: 2026-08-06
author: plan_reconciler
source: agt-bf8439
parent_epic: cefi_master
priority: P2
assigned_vm: NA
locked_by: plan_reconciler
resolved_by:
---

# plan_reconciler findings — 2026-08-06 (cefi tranche shard)

> Sharded reconciliation run for the `cefi` tranche (dispatch `agt-bf8439`, slot 12). Working set = 93 cefi
> `asset_group` docs; 43 in the 12h grace window (read-only), 50 writable. Normative refs + codex in scope per shard.
> Every action below survived the STEP-4 adversarial verification; refuted candidates are logged under `## Refuted`.

## Run inventory

- Cefi corpus: 93 docs (41 plans/active + 52 plans/active/issues), 50 writable / 43 grace
- Grace set corpus-wide: 316 docs (heavily-worked corpus; touches through 2026-08-06 20:01 UTC)
- Hygiene sweep: 4 hard failures corpus-wide (reference-path ratchet 83v81 / 88v86, AG-closeout linkage 75v69,
  terminal-status-archived 3v0, archive-candidates ratchet); 0 archive candidates from the mechanical sweep
- Phase-0 candidates for this shard: 2 AG-closeout orphans, 3 todo-format docs, 1 delete/VM-launch soft-warn (grace), 3
  terminal-status violations (ALL grace)

## Flips verified

- cefi_4surface:793 `_DRYRUN_COLS` — code half [x] @ instruments-service@97801b5d (1284606a = pre-rewrite twin, NOT
  cited); re-run/decide half split to new todo (promote scratchpad script first)
- cryptovenue:225 Barchart removal — [x] @ unified-api-contracts@844c5ee6b (ancestor-verified) + codex retirement
  2026-06-24; residual = dead smoke_matrix.py:143 key
- backfill_smoke:302 todo 6 — [x] "answered by action" (R2 co-fix/co-migration, utl@43fa6f3f + is@a9be6ce9; register
  §6b)
- honest_coverage:474-475 — [x] KEPT (flip legitimate, 65f653fd9); leading-bold annotated CLOSED-2026-08-03

## Contradictions

- T-C1 [P1] ASTER attempted_failed: closeout Track 6 "unresolved" vs aggregated_sources "resolved 07-26, 150" — both
  GRACE → ROUTED Q1
- T-C2 [P1] archived cutover "ALL COMPLETE" vs fleet 10/44 incomplete — archived doc → ROUTED Q2
- B2-C3 enum audit dual verdicts — resolved via SUPERSEDED cross-ref (Class B 08-05 live read wins)
- B2-C6 units mix (rows/groups) — ambiguous → ROUTED Q6b

## Doc-drift

- 27 codex-alignment findings (hunter C): 14 CODEX-STALE (7 P1) → flag-only, ROUTED Q6c for sweep plan; 3 mis-citations
  re-pointed (adapter_findings, candle_feature, smoketest)
- 9 PLAN-WRONG → all fixed in STEP 5 (8 applied; C8 archive_exempt dual-direction ROUTED Q5)
- cefi_master epic count 5-vs-19 → ROUTED Q4 (regen deferral)

## Hygiene fixes

(pending)

## Filed

- plans/active/issues/plan_reconciler_findings_2026_08_06.md (this doc) = run journal + durable todo surface
- Codex-drift sweep follow-up todo added (see Deferred table) pending operator answer on Q6c

## Archive candidates (operator review)

- coinbase_cde (3/3 [x] sha-evidenced) — NOT auto-archived: locked_by + split verdict → ROUTED Q3
- features_universe_filter — NOT archive-ready (premature LC_TARBALL flip unresolved; locked_by)
- instruments_batch1 (5/5 [x]) — NOT archive-ready (false-completion-claim vehicle issue, grace)
- 3 terminal-status-archived violations — all grace, report-only

## Refuted (dropped by verify)

- A3 honest_coverage inverse-flip — REFUTED (flip legitimate, evidence chain verified) → annotate-only
- A4 archive-ready "stale pending" blocker — REFUTED (dated narrative; subject todo DONE)
- B6 shard24 headline defect — tiebreaker: confirmer evidence won (image postdates fix; UPDATE_TIME=2026-08-02T15:23:00)
  → minimal title reword applied
- B1 Option-B drop — refuter won: annotate-don't-drop (doc deliberately keeps choice open)

## Coverage (hunters / batches / docs)

- 8/8 hunters: B0-B4 (5×10-doc batches), T (topic), M (mechanical adjudicator), C (codex-alignment) — 50 writable docs
  covered, all reports recorded above
- STEP 4: 8 verifier agents (refuter+confirmer × 4 clusters) — 27 candidates verified; splits: A4 (route), B1
  (annotate), B6 (tiebreaker by direct evidence)
- STEP 5: 13 commits applied on plan_reconciler/agt-bf8439 (12 doc-fix commits + findings updates)

## Plans not reached

- None in the writable set: all 50 writable cefi docs were read by ≥1 hunter; 43 grace docs were report-only (recorded
  per-hunter)
- Epic regen (cefi_master) deliberately NOT applied — ROUTED Q4

## Hunter reports received

### B1 (batch 1) — 10 docs read in full (cefi_4surface / deribit_binance_finalize / cefi_ml_live / cryptovenue / candle_divergence / cefi_batch_manifest / mtds_cefi_docker / mtds_pipeline_killed / tardis_impossible / uac_seed_fallback)

**Pending candidates (to verify in STEP 4):**

- M1 [P2] — cefi_4surface:793 `- [ ] [SCRIPT] P0 _DRYRUN_COLS` — doc body:833-837 declares DONE (chain in `_DRYRUN_COLS`
  @ instruments-service@1284606a 2026-07-24), but 2026-08-06 entry :871-879 consciously keeps box open ("re-run + decide
  remediation"). Hunter rec: SPLIT — flip resolved half w/ sha evidence + new scoped todo. VERIFY: sha reachable +
  `'chain' in _DRYRUN_COLS`.
- Z1 [P2] — mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md: ZERO checkboxes; 3 prose follow-ups
  :174-185 must become `- [ ]` todos (zero-checkbox sweep duty).
- C3 [P3] — cefi_4surface:113-116 `[x]` box whose text says fix half still open (deliberate, cross-documented) — suggest
  rename, no content change.
- S1 [P3] — tardis_impossible_combinations:145 + :191 duplicate `## Progress Log` headers.
- S3 [P3] — cefi_master:30 `assigned_vm: vm-cefi` lacks the legacy annotation instruments_master:36 claims applies to
  "ALL epics/*.md".
- H1 [P2] — cefi_ml_directional_continuous_live:184-190 deferred `[RESEARCH] P2` volume feature has "Not yet identified"
  successor (confirmed no owner via grep) → needs fate decision.
- C4 [P3] — last_updated frontmatter stale: cefi_4surface:40 (07-25 vs body 08-04/05/06). closeout:51 + defi_master:60
  are grace/other-tranche → report only.
- C1/C2 [P2] — aggregated_sources (GRACE): open-todo index claims "exactly 8 open" for candle doc (6 already `[x]`) and
  lists 3 tardis DONE todos as open → report only (grace).
- C5/M2 [P3] — defi_master epic: "7 active plans" but 2 archived (count drift); Phase-4 box RESOLVED-annotated but open
  → defi tranche items, report only.
- S2 [P3] — epics retain inline open todos in SUPERSEDED sections (cefi_master 28) — observation.
- AO1/AO2 — both AO docs compliant (AO2 caveat: text-only gate on archived docs → note).

### T (topic hunter — cefi data-completion/coverage/venue claims, corpus-wide)

**Pending candidates (to verify in STEP 4):**

- T-C7 [P3→P2] — deribit_binance_finalize:76-79 (WRITABLE): "backfill VM ... preempted 2026-07-28T10:51 UTC and never
  recovered" — FALSE since 2026-07-30 (relaunch chain: track2_backfill_vm_preempted issue :184/:210/:555, 6th ON_DEMAND
  running 2026-08-06). Doc last_updated 07-31 postdates 2nd relaunch → live-stale claim. FIX: align sentence with
  relaunch chain.
- T-C1 [P1] — closeout:309-310 Track 6 ASTER attempted_failed "unresolved (NOTIFY-OPERATOR)" vs
  aggregated_sources:588-590 "resolved/archived 2026-07-26 (count self-recovered to 150)". Both GRACE → report/route, no
  edit.
- T-C2 [P1] — archive/2026_07/cefi_migration_cutover...:128,134 "ALL COMPLETE / every shard EXIT_STATUS=0" vs fleet
  truth 10/44 shards incomplete (relaunch_round3:416). Archived doc — out of scope to edit; report.
- T-C3 [P2] — aggregated_sources:562-574 E4/E7/E8 listed as open P0 w/ "~1.2M orphan" vs e4_e8_orphan_sweep:158-161
  measured 287,074 DELETED 2026-08-03. GRACE → report.
- T-C4 [P2] — closeout:263-264 "no relaunch has occurred since" vs 5 documented relaunches (track2 issue). GRACE →
  report.
- T-C5 [P3] — aggregated_sources:251-255 "relaunch 21 dead shards" vs own :783-785 + round4 issue (10 shards). GRACE →
  report.
- T-C6 [P3] — aggregated_sources:784-785 "[OPERATOR] P1 relaunch ruling" vs RULED 2026-08-06 (option b), open item is
  [DATA]. GRACE → report.
- T-S1..S5 — suspected stale: tradfi_master:225 (62% backfill claim), infrastructure_master:65 (in-flight VM list),
  closeout:51 last_updated, archived cutover ALL-COMPLETE, aggregated_sources E4/E7/E8 → all grace/other-tranche/archive
  → report only.

### B2 (batch 2) — 10 docs read in full (batch6_finalize / defi_pipeline_finalize / canonical_path_oracle / cefi_backfill / cefi_chain_drop / cefi_enumeration_audit / cefi_onchain_perp_batch / cefi_residual_followups / fail_hard / ml_training_launchers)

**Pending candidates:**

- C1 [P1] — defi_pipeline_finalize:12 `status: active` vs :57 body banner "STATUS: draft — NOT dispatched" —
  frontmatter/body contradiction; AO-ingest surface at risk (dispatch-blocking). VERIFY which side newer (git blame)
  then align.
- C2 [P1] — cefi_backfill:111-113 open `[BACKEND] P2` todo still offers "Option B" while doc's own 08-04 cProfile
  :144-152 says Option B wrong design (0.4%). FIX: align todo text.
- C3 [P1] — cefi_enumeration_audit:216-248 [x] "NOT a marker-format problem" vs :267-281 [x] "no gap / measurement
  artifact" — dual opposite [x] verdicts, no cross-ref. FIX: annotate cross-reference.
- C4 [P1] — cefi_residual_followups:110-122 residual #3 entry still instructs `--apply` "9,850 authoritative" vs
  :516-529 flipped (28,755 dropped, 0 residual). FIX: strike/annotate stale instruction.
- C5 [P1] — canonical_path_oracle:57-61 resolved_by "1,697 colon_wire confirmed gone" vs :287-293 in-body CORRECTION
  (false negative; 63 objects migrated). FIX: update machine-read surface.
- C6 [P2] — cefi_chain_drop:108-109 venue breakdown units mix rows/groups — ambiguous, report.
- C7-C9 [P2] — aggregated_sources digest drift (cefi_backfill "0 open" vs 1 real; fail_hard SHIPPED items listed open;
  residual "14 open"+10,368) — GRACE → report.
- C10 [P2] — defi_master:319 epic gate vs child P0 flip (defi epic) → report.
- C11 [P3] — last_updated staleness: defi_pipeline_finalize:26, cefi_onchain_perp:42, ml_training:35 (all writable) →
  mechanical bump.
- Structural — canonical_path_oracle:299-300 embedded checkbox under [x] parent (regen misparse); ml_training:125-137
  `- [ ] 1.` numbering (todo-format class).
- AO — batch6_finalize 3 open todos READY; defi_pipeline_finalize NOT safe to dispatch until C1 resolved.

### B0 (batch 0) — 10 docs read in full (aster_rolling_adv / track2_finalize / adapter_findings / coinbase_cde / shard24 / estate_orphan / features_universe_filter / mtds_smoketest / no_active_paper_run / onchain_venues_mislabeled)

**Pending candidates:**

- C1 [P1] — aster doc: Phase 2 "DONE 2026-07-26" checked todos (:177-187) vs Deferred table + design text "Not started"
  (:97-100, :212). FIX: align stale Deferred/decision text.
- C2 [P1] — features doc:264 premature `[x]` flip LC_TARBALL_FRESHNESS — own text :269-271 admits done-when's 2nd half
  (real VM launch observation) never performed; 07-31 check :295-303 shows pre-flip blocked state; flip names a
  DIFFERENT test-class set than the 07-31-verified set. Candidate: split/re-open half + annotate.
- C3 [P2] — shard24:5-6 headline "NOT YET in live monitor image" vs own 08-06 log :195-197 (deployed, test-pass
  unverified). FIX: align headline.
- C4 [P2] — coinbase_cde:130-131 todo 1 "pending the registry-discrepancy follow-up" — resolved 07-30 by todo 2
  (:141-147, instruments-service@f9fa7587). FIX: strike stale caveat.
- C5 [P2] — aggregated_sources:307-309, :180-188 digest lists estate #3 + aster Phase-2 items as open vs sources [x] —
  GRACE → report.
- C6 [P2] — cefi_master:629-630 "5 active plans declare parent_epic: cefi_master" vs measured 51 (≥21 root-level) — epic
  roster/count drift. VERIFY what the section means + regen vs hand-fix.
- C7/C8 [P3] — verified non-contradictions (closeout Track 2 / DERIBIT gap) — no action.
- ARCHIVE CANDIDATES — coinbase_cde (3/3 [x], sha-evidenced) + features_universe_filter (5/5 [x] but C2 premature flip →
  NOT archive-ready until C2 resolved). Both assigned_vm: planning, status: open, writable. Cross-tranche grep required
  before any archive.
- AO — track2_finalize 4 open todos READY (machine-held, sequential, done-when on all).
- Structural — mtds_smoketest:409 `[~]` non-standard checkbox marker (regen silently drops); estate:143-174 grotesque
  indentation (P3); aster:83-84 bold span crosses physical lines (P3).

### M (mechanical adjudicator) — Phase-0 flag rulings

**AG-closeout orphans — all 6 REAL** (checker: BFS≤3 over resolvable related: + filename-stem mention in family docs;
family = cefi_consolidated_closeout + aggregated_sources + cefi_consolidated_vm_aster + 2 archive family docs; fixing
all 6 → gate back to 69 baseline). Fix per doc: add `/plans/active/cefi_consolidated_closeout_2026_07_18.md` to
`related:`. **2 WRITABLE → apply:**

1. features_universe_filter_settlement_suffix_and_vm_tarball_staleness:20 (related: currently
   [data_pipeline_check_mdps_features_2026_07_20] — 1-hop dead end)
2. mtds_cefi_docker_image_stale_5mo:31-35 (related: currently [cefi_book_snapshot5, codex] — dead end) **4 GRACE →
   report only:** cefi_book_snapshot5, cefi_derivative_ticker_aiodns, cefi_liquidations_count_stale,
   mtds_live_mode_tardis_datasets.

**Todo-format — all 5 REAL (soft):** backfill_smoke:284 (`- [ ] 3. [DOCS] P2.` → `- [ ] [DOCS] P2.`), backfill_smoke:302
(`6.`), candle_divergence:442 (`9.`), candle_divergence:485 (`13.`), canonical_path_oracle:321
(`- [ ] BLOCKED-UPSTREAM-DESIGN [DATA] P2.` → `- [ ] [DATA] P2. BLOCKED-UPSTREAM-DESIGN — …` manual edit,
fix_todo_format.sh has no rule). Checked `[x] N.` numbered style deliberately not flagged — leave.

**Reference-path:** 1 checker-visible violation = THIS findings doc related: bare basename (fixed this run). Plus 36
checker-INVISIBLE dangling relative refs in 10 cefi docs (targets verified moved to plans/archive/). **WRITABLE subset
(4 docs, 8 refs) → repoint to leading-slash archive path:**

- candle_feature:311 → /plans/archive/2026_07/candle_canonical_path_migration_execution_2026_07_24.md; :390 →
  /plans/archive/2026_07/mdps_candle_manifest_population_disconnect_2026_07_25.md; :497/:505 →
  /plans/archive/2026_08/infra_satellite_ao_dispatch_batch2_2026_07_27.md
- backfill_smoke:279 → /plans/archive/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md
- cefi_4surface:57 → /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md
- instruments_cefi_g1_g5:63/:72 → /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md GRACE subset → report
  (aggregated_sources 15 refs, data_completion_cefi 6, batch7 4, book_snapshot5 2, track7 1, e4_e8 1).

**Moved-doc referrers:** 3 hard findings — NONE in cefi docs (infra_parked×3, governance_sweep, codex naming-convention
merged-away→LEAVE). mtds_qg_red:27/:65 stale ref to archived features_gas_fees doc — GRACE → report.

**Checker blind-spot finding (recommended follow-up, out of shard):** check_reference_paths.py BARE_MD_RE misses
relative `plans/...` refs; find_moved_doc_referrers.sh same. 36+ cefi refs and counting → future all-run / tooling fix.

### B3 (batch 3) — 10 docs read in full (batch8 + finalize / data_pipeline_check_mdps_features + finalize / defi_pipeline_e2e / instruments_cefi_g1_g5 / backfill_smoke / cefi_legacy_bucket / honest_coverage_shard_dimension / mtds_pipeline_check_enumerate / phantom_audit / okx_futures)

**Pending candidates:**

- C1 [P2] — data_pipeline_check_mdps_features_finalize:12 `status: active` vs :57-58 body banner "draft — NOT
  dispatched". KEY CONTEXT: 2026-07-30 ruling makes finalizes active-from-the-start ("Status: active from the start
  (2026-07-30 ruling — no double gate)" per batch4/batch8 finalize headers) → the BODY BANNER is the stale side, not
  frontmatter. Same class as B2-C1 (defi_pipeline_finalize). FIX: replace stale body banner with the ruling banner.
  (Both docs writable.)
- M1 [P2] — okx_futures:133-139 `[SCRIPT] P1` open, all gates cleared (operator RULED option A 2026-08-06 :128-132;
  docstring reconciliation DONE-ELSEWHERE @ market-tick-data-service@8a6bbc97 per batch8:157-164; sub-part (b) Option-B
  revert now dead). Todo names shipped sha + remains open → flip candidate. **BUT okx_futures doc is GRACE (16:22) →
  report only.**
- M3 [P3] — honest_coverage:474-475 `[x]` marker whose own text says "NOT closed here — genuinely contested... left
  open". Inverse-flip: checked box hides an open item. FIX: un-flip to `- [ ]` or annotate — VERIFY in STEP 4.
- A1 [P3] — data_pipeline_check_mdps_features:193 `[DATA] P0` first physical line ends mid-phrase ("NEW todo (was 8's
  remaining scope). [DATA] P0. Complete the automated `/data-pipeline-check-mdps` skill's OWN"); done-when +
  GATED-on-`mdps-e2e-shared-host-teardown-fixed` live on continuation lines (invisible to _parse_open_todos). FIX:
  restructure first line + explicit "not machine-enforced" guard.
- A2/Z1 [P3] — mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md (WRITABLE): ZERO checkboxes,
  `assigned_vm: planning`, open P1 defect (enumerate_mtds_shards mvp_only=True → CEFI/SPORTS zero shards) with concrete
  2-option remediation :130-141 prose-only. Zero-checkbox sweep duty → convert to canonical todos.
- C3 [P3] — cefi_master:631 "5 active plans declare parent_epic: cefi_master" vs 21 measured (48 incl. issues/) —
  auto-populated 2026-05-21, never refreshed. Same class across all 5 epics (infra 19v47, instruments 16v19, manifest
  16v15, aofm 6v7 — other tranches). FIX for cefi_master: regenerate via populate tooling or hand-correct count.
- C2 [P3] — closeout Track 6 aster unresolved (dup of T-C1) — grace.
- C4 [P3] — closeout:51 + aggregated_sources:41 last_updated stale — grace.
- M2 [P3] — agent_operating_framework_master:305/308/311 open boxes N/A-superseded (retagged by AO-tranche reconciler) —
  other tranche, report.
- S2 [P3] — closeout:182 "Phase D/E DONE" phrase stale after RE-OPEN — grace.
- A3/A4 — batch8(+finalize) READY; okx_futures correctly NA.
- H1-H6 — hedges: mostly grace/observations (instruments_master routing gap, closeout overlap flags, aggregated_sources
  aster "0 open"+digest conflict, dp_catalog "resolved, 2 open", okx AAPL-USD research, operator-gated --apply with no
  checkboxes).

## Resume guide (updated at 2nd /pre-compact 2026-08-06 ~22:15 UTC — STEP 4-7 DONE, STEP 8 in wait-loop)

**Run state — STEPS 1-7 COMPLETE. STEP 8 IN PROGRESS (wait-loop):**

- STEP 4 done: 8 verifiers (refuter+confirmer ×4 clusters) — 25 CONFIRMED / 2 refuted; split adjudications: A4→route
  (coinbase_cde locked), B1→annotate-don't-drop, B6→tiebreaker by direct evidence (image UPDATE_TIME
  2026-08-02T15:23:00), D4→sha-trap (1284606a pre-rewrite twin → cite 97801b5d everywhere).
- STEP 5 done: 13 commits on `plan_reconciler/agt-bf8439` (ahead=0, clean tree) — all fixes listed in
  `## Flips verified` + `## STEP-4 verdicts` sections; 25 files touched.
- STEP 6 done: Q1-Q6 POSTed via /api/slots/12/blocked (all can_continue: true) — ASTER attempted_failed (P1), archived
  ALL-COMPLETE (P1), coinbase_cde unlock, epic-regen scope, archive_exempt dual-direction, codex-drift sweep.
- STEP 7 done: PR https://github.com/IggyIkenna/unified-trading-pm/pull/2398 (review into live-defi-rollout);
  plan-health result POSTed 200 ok (25 confirmed/2 refuted, 93 docs, 43 grace, sha 4a5c9963, pr_url #2398).
- **STEP 8 (only remaining)**: wait-loop armed (background task bxmxi5mlo, 12×5min polling GET /api/slots/12/messages +
  /progress heartbeats; exits with ANSWERS-ARRIVED on non-empty messages or WAIT-TIMEOUT-1H-NO-ANSWERS — its completion
  re-invokes this session). On answers: apply each (same verified-fix discipline; a ruled codex edit is now authorized)
  → checkpoint-commit BY NAME → push → then `POST /api/slots/12/done`
  `{"task_id":"agt-bf8439","sha":"<head>","evidence":"...","one_shot_complete":true}` — THE LAST ACTION. If the
  wait-loop times out with no answers: re-arm it and keep waiting (do NOT /done with questions open).

**3rd /pre-compact audit 2026-08-06 (post-compaction re-run, no state change since 2nd):** git clean + ahead=0 (HEAD
133c87add); wait-loop bxmxi5mlo verified ALIVE (PID 3317685, 12×285s, ~21:54 expiry); stale STEP-4 heartbeat watchdog
killed (was posting outdated phase, self-expired ~21:14 anyway); dangling-ref grep-0 in this doc (only corpus match was
a false positive `run_hygiene_sweep.sh` in PLAN_FORMAT.md:306); /tmp scan — the 5 scratchpad inputs (cefi_writable.txt /
grace_set.txt / hygiene_sweep.txt / plan_health_digest.md / plan_skeleton.md) remain regenerable deliberate drops;
`diag_cred.yaml` is another slot's Cloud Build diagnostic YAML (not a credential), `ffpulltokens.*` is the slot cron
ff-pull's empty transient token file — neither mine. **Verdict: safe to compact — YES.**

**4th /pre-compact audit 2026-08-06 (~21:05 UTC, post-2nd-compaction re-run):** git clean + ahead=0 (HEAD 655e228e9,
unchanged since 3rd); wait-loop bxmxi5mlo verified ALIVE (PID 3317685, ps etime ~5min of the 57min loop, ~10 ticks
remaining, expiry ~21:54); /tmp scan — the same 5 regenerable scratchpad inputs (cefi_writable.txt / grace_set.txt /
hygiene_sweep.txt / plan_health_digest.md / plan_skeleton.md) + confirmed-not-mine `diag_cred.yaml` (other slot's Cloud
Build diagnostic YAML) + `ffpullresult.BQl1iQ` (empty ff-pull token file, 0 bytes) — no secrets; **NEW DISCOVERY —
dangling scratchpad handoff FIXED**: cefi_4surface:798's todo said "promote `investigate_chain_lossy_20260724.py` from
the session scratchpad", but the script exists NOWHERE on disk (originating 2026-07-24 session's /tmp long wiped) —
unfulfillable handoff; reworded the todo to re-create-the-diagnostic-from-documented-procedure
(/plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md:94 + 4surface body :760-789), see
cefi_4surface@6b0bad47f; the Cluster A notes :594-595/:614-616 ("promote it first") are historical, the todo is now
authoritative; no other dangling /tmp refs (3rd's grep-0 stands for the rest of the corpus; the other 3 grep hits in
this doc are this audit + the acknowledged handoff, now resolved); no new chat-only findings since 3rd. **Verdict: safe
to compact — YES.**

**Wait-loop cycle 1 2026-08-06 ~21:54 UTC:** bxmxi5mlo completed — 12/12 heartbeats 200, then
`WAIT-TIMEOUT-1H-NO-ANSWERS`. Q1-Q6 still open (can_continue: true). Per STEP 8 rule, re-armed the wait-loop: cycle 2
(task bx1qe43th, 12×285s) was externally KILLED ~21:56 (~2 min in, empty output, queue confirmed empty) — re-armed as
cycle 2b (task bxw5z7w6, 12×285s) which was ALSO externally KILLED ~21:58 (~1 min in, empty output). Two identical kills
~1-2 min in vs cycle 1's full 57 min — post-compaction background-Bash reaping, not operator signals (queue checked
empty each time). SWITCHED MECHANISM ~22:00: persistent Monitor (`wait_cefi_answers`, poll /api/slots/12/messages +
heartbeat every 285s, emits ONLY on ANSWERS-ARRIVED) + recurring cron backstop (:17/:47, "check answers, process if any,
verify monitor alive else re-arm"). On ANSWERS-ARRIVED apply → checkpoint-commit BY NAME → push →
`POST /api/slots/12/done` (THE LAST ACTION). Never /done with questions open.

**Candidate registry:** all pending candidates are above, per hunter. Writable-doc fixes with CONFIRMED-verification
needed (dedup'd across hunters):

1. **Flips/splits**: B1-M1 `_DRYRUN_COLS` cefi_4surface:793 (sha instruments-service@1284606a — verify reachable +
   `'chain' in _DRYRUN_COLS` at instruments-service/scripts/complete_cefi_manifest_canonical_dedup_2026_07_17.py:220,
   then split: flip resolved half + new scoped todo for re-run/decide).
2. **Body-banner aligns** (2026-07-30 "no double gate" ruling = body banner is the stale side): B2-C1
   defi_pipeline_finalize:57, B3-C1 data_pipeline_check_mdps_features_finalize:57-58 — replace "draft — NOT dispatched"
   banner with the ruling banner (pattern: batch4_finalize:57 / batch8_finalize:58-60).
3. **Contradiction text aligns** (reader-verifiable): B2-C2 cefi_backfill:111 Option-B dead (doc's own cProfile
   :144-152); B2-C3 cefi_enumeration_audit dual verdicts (add cross-ref); B2-C4 cefi_residual_followups:110-122 stale
   --apply instruction (28,755 dropped/0 residual at :516-529); B2-C5 canonical_path_oracle resolved_by frontmatter
   (:57-61 vs body :287-293); B0-C1 aster Phase-2 Deferred table "Not started" vs [x] todos :177-187; B0-C3 shard24:5-6
   headline; B0-C4 coinbase_cde:130-131 stale "pending" caveat; T-C7 deribit_binance_finalize:76-79 "never recovered".
4. **Todo-format (mechanical)**: backfill_smoke:284/302, candle_divergence:442/485 (strip leading number),
   canonical_path_oracle:321 (move BLOCKED-UPSTREAM-DESIGN after priority — manual, no fixer rule). B3-A1
   data_pipeline_check_mdps_features:193 first-line truncation restructure.
5. **AG-closeout linkage (writable 2 of 6)**: features_universe_filter:20 + mtds_cefi_docker:31 add
   `/plans/active/cefi_consolidated_closeout_2026_07_18.md` to related:. (4 grace: book_snapshot5,
   derivative_ticker_aiodns, liquidations_count_stale, mtds_live_mode.)
6. **Dangling relative refs (writable 8 refs / 4 docs)**: candle_feature:311/390/497/505, backfill_smoke:279,
   cefi_4surface:57, instruments_cefi_g1_g5:63/72 → repoint to /plans/archive/... per M rulings.
7. **Zero-checkbox (2 docs)**: B1-Z1 mtds_pipeline_check_process_killed:174-185 → 3 follow-ups as todos; B3-A2/Z1
   mtds_pipeline_check_enumerate_shards (planning, zero checkboxes) → add `- [ ] [SCRIPT] P1` todo for option (b)
   per-asset-group fallback.
8. **Inverse-flip**: B3-M3 honest_coverage:474-475 [x] on "NOT closed" item → un-flip/annotate after reading.
9. **Epic count drift**: B0-C6/B3-C3 cefi_master:631 "5 active plans" vs 21 — check
   scripts/plans/populate_epic_bodies_2026_05_21.py for a scoped regen before hand-fixing.
10. **Archive candidates (cross-tranche grep REQUIRED first)**: coinbase_cde (3/3 [x], sha-evidenced) —
    features_universe_filter NOT archive-ready (B0-C2 premature LC_TARBALL flip unresolved).
11. **last_updated bumps (P3)**: cefi_4surface:40, defi_pipeline_finalize:26, cefi_onchain_perp:42, ml_training:35.
12. **C3 [P3] cefi_4surface:113-116** box rename (enumeration half only) — optional.

**GRACE-ONLY (report, never edit):** aggregated_sources (C1/C2/C3/C5/C6/S1 + 15 dangling refs), closeout (T-C1/C4/S2),
okx_futures M1, data_completion_cefi refs, cefi_satellite_batch7 refs,
book_snapshot5/derivative_ticker/liquidations/mtds_live_mode orphan fixes, mtds_qg_red refs, cefi_track7/e4_e8 refs, all
3 terminal-status violations (sit_stamp, sports_mtds_oom, omniroute superseded — omniroute:16:22 touch).

**STEP 6 routing candidates (already enumerated):** T-C1 (ASTER closeout Track 6 vs aggregated_sources — P1 normative
pair, both grace), T-C2 (archived cutover ALL-COMPLETE vs fleet truth), H1 (cefi_ml deferred P2 no owner), B2-C6 (units
mix — ambiguous), epic regen scope question.

**STEP 7 mechanics:** prettier touched .md → stage BY NAME → commit `docs(plans): reconcile ...` → push
plan_reconciler/agt-bf8439 →
`gh pr create --base live-defi-rollout --head plan_reconciler/agt-bf8439 --title "docs(plans): daily reconciliation agt-bf8439 [review]"`
→ POST /api/plan_health/result with full JSON → STEP 8 loop-and-wait → POST /api/slots/12/done.

## Deferred work after 2026-08-06

| item                                                     | state/why deferred                                       | blocked-on             |
| -------------------------------------------------------- | -------------------------------------------------------- | ---------------------- |
| STEP 4 adversarial verification of ~30 candidates        | Not done — hunters still returning (B4, codex-alignment) | hunter completion      |
| STEP 5 apply of 12 writable fix groups (above)           | Not done                                                 | STEP 4 verdicts        |
| STEP 6 route (T-C1/T-C2/H1/units/epic-regen)             | Not done                                                 | STEP 4                 |
| STEP 7 PR + result POST                                  | Not done                                                 | STEP 5/6               |
| STEP 8 /done                                             | Not done                                                 | STEP 7                 |
| Grace-deferred fixes (~25 refs/orphans in 13 grace docs) | Cannot be done yet — 12h grace window                    | elapsed time; next run |
| All 3 terminal-status-archived violations                | Cannot be done yet — grace (touched today)               | elapsed time; next run |

**Next item: collect B4 + codex-alignment hunter results, then run the STEP-4 verifier fan-out (shas:
instruments-service@1284606a, market-tick-data-service@8a6bbc97 via `git merge-base --is-ancestor` in
../instruments-service / ../market-tick-data-service; archive-cross-tranche greps for the 2 archive candidates).**

## Lessons learned this run (don't re-learn)

- **Issue-doc frontmatter schema (pre-commit enforced)**: `status` ∈ {blocked, false-positive, open, resolved,
  superseded} (NOT `active`); `nature` is SCALAR (list crashes docspec `_validate_value` — TypeError unhashable);
  required keys: parent_epic, priority, assigned_vm; `resolved_by:` present-but-empty; `related:` must be leading-slash
  `/plans/...`.
- **Grace computation one-liner**:
  `for f in $(ls plans/active/*.md plans/active/issues/*.md); do ct=$(git log -1 --format=%ct -- "$f"); [ -n "$ct" ] && [ "$ct" -ge $(( $(date +%s) - 43200 )) ] && echo "$f"; done`
  — 316 docs in grace today; the corpus is heavily churned (bulk touches at 18:38 UTC).
- **check_reference_paths.py blind spot (found + documented by M)**: relative `plans/...` refs are invisible to BOTH
  format and existence checks (`BARE_MD_RE` matches no-slash names only) — 36+ dangling cefi refs this run; also
  `find_moved_doc_referrers.sh` misses the same class. Tooling-fix follow-up filed in M's report.
- **check_ag_closeout_linkage.py**: orphan = fails BOTH BFS≤3 over resolvable related: AND filename-stem mention in
  family docs; fixing all 6 cefi orphans returns the corpus gate to the 69 baseline.
- **Finalize body banner vs frontmatter**: 2026-07-30 "no double gate" ruling → finalizes are active-from-the-start; a
  "draft — NOT dispatched" body banner on a finalize is the STALE side (frontmatter active is correct).
- **seed_frontmatter.py refuses foreign-dirty files** — hand-edit instead.
- **Plan reviewer notes**: aggregated_sources digest drift vs sources is chronic (its own :793 todo tracks it; every
  digest entry needs re-verification against the source doc before citation).

### B4 (batch 4) — 10 docs read in full (batch7_finalize / cefi_track2 / data_completion_finalize / instruments_batch1 / autonomous_decisions / mtds_backfill_memory_hang / prediction_capture / deribit_dated_option / aster_recheck / mdps_features_deadcode)

**Pending candidates:**

- C1 [P0] — data_completion_cefi_finalize:12 `status: active`+planning vs :58 body "draft — NOT dispatched" — 3rd
  finalize with the same pattern (with B2-C1, B3-C1). Fix per 2026-07-30 ruling: align BODY banner (stale side), NOT
  frontmatter. VERIFY ruling text from batch4_finalize:57 first.
- C2 [P1] — cefi_track2:69 "2.89M-cell gap is ~1-2 days of work at June rates" vs doc's own measured :198/:234 "3.25
  days/hr → ETA ≈730h ≈30 days". WRITABLE. FIX: annotate/correct stale claim (closeout:222-223 same claim — GRACE →
  report).
- C6 [P2] — batch7_finalize:70-72 claims `mdps_cefi_candle_manifest_orphan_reconciliation` "DELETED by batch7's todo 2
  (git rm)" — VERIFIED ARCHIVED (plans/archive/issues/..., status: resolved), not deleted. WRITABLE. FIX: correct the
  DELETED premise → archived-resolved.
- C7 [P2] — autonomous_session_operator_decisions:445-448 entry-12 Status is a copy-paste of entry 11's lock-mandatory
  resolution. WRITABLE. FIX: correct entry-12 status to its own fold-into-prediction_phase_ab_residuals resolution (READ
  entries first).
- C11 [P3] — last_updated: mdps_features_deadcode_consolidation:30 (07-20 vs 08-03 flips) — WRITABLE → bump.
  closeout:51 + aggregated_sources:41 GRACE → report.
- Structural — prediction_capture:38-43 `related:` bare `plans/...` paths without leading slash (check_reference_paths
  format class). WRITABLE. FIX: add leading slashes.
- C3 [P2] — closeout:586-593 Progress Log claims cefi_threaded_resolver + mdps_candle_manifest "now assigned_vm:
  planning, live in AO backlog" — BOTH ARCHIVED (resolved/complete) → GRACE → report.
- C4 [P2] — infrastructure_master:595-597 roster "status: active" vs archived-complete mtds_retry_safe_default_audit —
  infra epic → report.
- C5 [P2] — closeout:115-116 + :66-72 misc-audit routing + depends_on name archived-complete child → GRACE → report.
- C8 [P3] — aster_recheck zero-objects claim vs live_aster rows tension (self-flagged, todo 1 open) → report.
- C9 [P3] — aggregated_sources ≥10 label↔link active/archive mismatches → GRACE → report.
- C10 [P3] — cefi_track2:248-254 context_scope count 6 vs 5 non-resolving arithmetic → cosmetic, report.
- ARCHIVE CANDIDATE #3 — instruments_satellite_ao_dispatch_batch1 (5/5 [x], planning, sha-evidenced) — **NOT
  archive-ready: pending archival vehicle =
  issues/instruments_satellite_batch1_finalize_false_completion_claim_2026_08_02.md (grace; names batch1 finalize a
  false-completion claim)** → report, do not archive.
- Missed-flips: NONE mechanical. Closeout Track 1 + Track 2 gates + aster todo 1 = correct withholds.
- AO — batch7_finalize READY (C6 wrinkle determinable); cefi_track2 parked-by-design (999+prereq);
  data_completion_finalize DISPATCH HAZARD until C1 fixed; instruments_batch1 moot.
- Hedge-pointers — deribit_dated_option:103/:110 root cause untraced (open), closeout:224 operator-acceptance inference
  question, bybit honest-absence question, mtds_backfill:371 adaptive chunk-size consideration.

### C (codex-alignment hunter) — plan↔codex drift, 50-doc cefi corpus vs codex SSOTs

**27 verified findings** (quotes verified verbatim; all 41 cited codex paths exist; 6 docs have zero /codex refs =
nothing to drift). Split: 9 PLAN-WRONG (3 P1), 14 CODEX-STALE (7 P1 — **flag only, codex edits operator-gated**), 3
mis-citations, 1 codex-wording.

**PLAN-WRONG (writable-doc fixes — pending STEP 4 verify):**

- C1 [P1] — adapter_findings:210-213 "consolidated by a standing `*/1 * * * *` … shows up within ~1 minute" vs
  manifest-consolidator-ssot.md:527-530 — RULED 2026-07-29, shipped 2026-07-30: 12 of 18 consolidator jobs now run
  HOURLY (`0 * * * *`), instruments-bucket consolidation ≤60 min not ~1 min. Plan's DONE-07-29 verdict predates the
  cadence change.
- C2 [P2] — backfill_smoke:302-305 todo 6 open ("decide whether market_lifecycle/futures_contracts are in canonical
  shard grammar scope") vs non-canonical-path-inventory.md:243 + canonical-cutover-register.md:378 — R2 (2026-07-21/22)
  answered by action (co-fixed, co-migrated). Close/reframe todo 6 as done.
- C3 [P2] — cefi_content_migration_shard24:139-140 "flat ≤2/(vm-prefix,day) bound (no preemption carve-out)" vs
  rb_infra_relaunch.md:69-74 — ROOT-CAUSE-DIAGNOSED carve-out ruled 2026-08-02 (bound resets for fix-live relaunch).
  Doc's 08-03/08-06 progress entries never absorbed it.
- C4 [P2] — cefi_legacy_bucket_deleted_before_l3_gate:137-138 "very likely gone — GCS bucket deletion is not a
  soft/reversible operation" vs gcs-and-manifest-delete-safety-protocol.md:266-267 — whole-bucket destroy restorable
  within retention (extended 2026-07-28 operator ruling); qualify with §3a fresh
  `gcs_bucket_soft_delete_retention_seconds()` check (:272).
- C5 [P2] — cryptovenue:225-226 "DEPRECATE + REMOVE all Barchart … IN PROGRESS (this session)" vs
  tradfi-databento-sourcing-ssot.md:325-327 — Barchart RETIRED 2026-06-24 (finding 375), no longer wired. Close/re-scope
  to pure verification. (Side note: codex's own citation of tradfi_massive_dual_source:64 actually reads "Keep existing
  pattern (Yahoo + Barchart)" — retirement rests on finding 375.)
- C6 [P2] — cryptovenue:605-608 "**BLOCKED-DATA** — HYUNDAI/SAMSUNG/SK Hynix … needs operator credential/vendor
  decision" vs tradfi-databento-sourcing-ssot.md:137-140 — KRX hard-not-blocked, freely available via Yahoo, adapters
  exist; plan's own shipped evidence (uac@844c5ee6b "005930/000660/005380 .KS" venue=KRX source=yahoo). Retag from
  BLOCKED-DATA; residual = low-latency basis feed (Option C, ruled 2026-06-28).
- C7 [P2] — cefi_4surface:867 context-scout note "the cross-cutting codex doc (superseded here by the CeFi-specific
  blueprint)" vs cross-asset-canonical-target-ssot.md:16 (`status: current`, cited live at availability-manifest:1117).
  A plan cannot supersede a live codex SSOT. Reword: "dropped as redundant for this log's focus".
- C8 [P1] — cefi_deribit_binance_futures_bundle_verification_finalize:34 `archive_exempt: true` + :83-84 "also NOT
  archived, despite its own only todo now being [x]" vs plan-completion-and-archival-discipline.md:39-44 (locked plans
  the one exception). DUAL DIRECTION: `check_archive_candidates.sh:43,166,204,326` honors archive_exempt since
  2026-08-02 — tooling real, codex (created 07-28) undocumented. Plan should use locked_by OR codex should document
  archive_exempt. → ROUTE, not unilateral plan edit.

**Mis-citations (plan-side re-points):**

- C9 [P2] — adapter_findings:99-100 cites data-status-endpoint-contract.md for "the actual coverage.json v2 response" —
  that doc has zero "coverage.json" occurrences; SSOT = honest-coverage-model.md:522 (## coverage.json v2 schema (CK1)).
- C10 [P2] — candle_feature:206 "the aggregated key deriv_ohlcv appears NOWHERE in codex/plans" now false —
  mdps-candle-canonical-reconciliation.md:174 + per-asset-group-bucket-layouts.md:172 reference deriv_ohlcv_*.
  Historically true (token added by plan's own todo-1 amendment, mdps@752eaff). Mark sentence as pre-amendment history.
- C11 [P2] — mtds_is_full_adapter_smoketest:128-130 "never silent placeholders HARD RULE" cites
  data-pipeline-correctness-hard-rule.md (grep-0 "placeholder"); rule's home = honest-absence-downstream-handling.md:97.
  Claim true, SSOT pointer wrong.

**CODEX-STALE (flag only — operator-gated; P1 cluster first):**

- CS1 [P1] — orphan-object-detection.md:291-294 (+:174-177 §2c) "no known orphan coverage … capped at unknown" vs
  data_pipeline_check_mdps_features:313-318 (DONE 2026-08-03: MDPS candle, features, ml/strategy sweeps built+validated;
  issue archived resolved).
- CS2 [P1] — honest-absence-downstream-handling.md:1246-1248,1256-1258 "content-side check … not yet built into
  /data-pipeline-check-mdps / -features" vs data_pipeline_check_mdps_features:449-454 (DONE 2026-07-31: shared
  `check_inverse_phantom()` in utl@8b894105, consumed by mdps@12a3f6b + features@6afdb414, informational-only).
- CS3 [P1] — per-asset-group-bucket-layouts.md:129 instrument_availability flat `by_date/…/instruments.parquet` vs
  non-canonical-path-inventory.md:243 (RULED HIVE 2026-07-21 (R2), RETIRED-2026-08-03-partial → hive = live-written +
  migrated shape) + cutover-register:377-378.
- CS4 [P1] — availability-manifest-and-data-status.md:69-70 + shard-level-failure-isolation.md:97-98 "instrument_type
  for instruments-service: NOT a shard axis" vs honest_coverage_shard_dimension:203-206/399-404 (D6 approved 2026-07-07;
  `_split_by_instrument_type()` shipped; real `_ROW_KEY_COLUMNS` member). Future agent would treat shipped rows as
  violations.
- CS5 [P1] — availability-manifest:813/834 Layer-1/Layer-2 CEFI venue tables omit KRAKEN-SPOT, KRAKEN-FUTURES,
  BITGET-FUTURES, BINANCE-DELIVERY, OKX-SWAP vs cefi_4surface:107/114/564 + cross-asset-canonical-target-ssot:156/468.
- CS6 [P1] — data-lineage-MTDS-features-ml.md:123-128 "CeFi on-chain-perp 4-venue gap … deliberately deferred" vs
  aster_and_cefi_rolling_adv_feature:179-183 (DONE 2026-07-26: HYPERLIQUID trades candles confirmed non-zero volume;
  full-range VM mdps-backfill-cefi-20260726-165959; ASTER re-scoped+relaunched).
- CS7 [P1] — vm-launcher-runbook.md:364-369 launch-prediction-features-vm.sh as working vs
  mdps_features_deadcode_consolidation:73-77 (BROKEN — packages removed; superseded by launch-features-vm.sh
  --feature-family cross_instrument; re-verified on disk :249).
- CS8 [P2] — vm-launcher-runbook.md:510-516 launch-ml-training-vm.sh as working vs ml_training_launchers:10-13
  (VM_SERVICE=ml_training_service, no such package; internal contradiction with ml-service-architecture.md:140-145
  "deleted").
- CS9 [P2] — data-pipeline-alerts.md:144 DP-VM-007 marker-only preempt detection vs shard24:114-120
  (deployment-service@09a23745 preemption_op_checker + ComputeEngineClient.was_instance_preempted(), benign not page).
- CS10 [P2] — pipeline-mode-partition.md:167-168 rows batch_lighter_candles/batch_pacifica_kline vs UAC
  pipeline_mode.py:160-161 (BATCH_LIGHTER_API; BATCH_PACIFICA removed 2026-07-16 ruling); evidence at
  onchain_venues_mislabeled:136/154-155.
- CS11 [P2] — availability-manifest:986 Data Status Page tree instruments row lacks instrument_type level vs
  honest_coverage_shard_dimension:445-449 (CLOSED 2026-07-27 deployment-api@554cde9, deployment-ui@8f6c4bc). Same D6
  root as CS4.
- CS12 [P2] — instruments-foundation-and-catalogue-completeness.md:319-320 "daily-trigger PAUSED … root cause of
  06-19/20/21 gap" vs instruments_cefi_g1_g5:304/309-310 (G2 signed off 2026-07-06; per-AG scheduler LIVE
  deployment-service@9d0e457; gap-days filled 2026-06-26).
- CS13 [P2] — instruments-foundation-and-catalogue-completeness.md:514-515 "SSOT plan … does not exist yet — needs
  writing" vs instruments_cefi_g1_g5:5/69-70 (extracted 2026-07-24, exists on disk).
- CS14 [P2] — tradfi-databento-sourcing-ssot.md:328 `SOURCE_PRIORITY ["databento","massive","yahoo"]` self-contradicts
  same doc :45-47 + removal-complete banner (massive DELETED uac@a2beed46 + mtds@362a487e). Line 328 should read
  ["databento","yahoo"]. Evidence pre-removal: instruments_batch1:219-221.
- CS15 [P2] — cross-asset-canonical-target-ssot.md:469-470 "PACIFICA CULLED 2026-07-16" + availability-manifest:888 vs
  cefi_4surface:134 (open todo: register PACIFICA-SOLANA (265) in fail-hard quarantine set; verified still open
  2026-08-06 :871-879). Purge incomplete.
- CS16 [P2] — pipeline-mode-partition.md:127 "pipeline_mode is the outermost hive partition" self-contradicts its own
  :130 example + four-surface-reconciliation-procedure.md:266 (day= first). Wording fix only.

**Clean docs (zero drift — 27 verified clean):** all 3 batch finalizes, cefi_track2 + finalize, data_pipeline_check
finalize + data_completion finalize + defi_pipeline_e2e + finalize, canonical_path_oracle, fail_hard_canonical,
cefi_batch_manifest_blank, cefi_chain_drop, cefi_consolidated_vm_aster, cefi_residual_followups, cefi_onchain_perp,
cefi_enumeration_audit, coinbase_cde, estate_orphan, tardis_impossible, mtds_backfill_vm_memory_hang, mtds_cefi_docker,
uac_per_venue_seed, mtds_pipeline_check x2, no_active_paper_run, onchain_venues_mislabeled, prediction_capture,
cefi_ml_directional, instruments_batch1, + 6 no-codex-ref docs (phantom_audit, features_universe_filter,
deribit_dated_option, cefi_backfill, autonomous_decisions, defi_pipeline_finalize).

## STEP 4 verdicts (adversarial verify — refuter/confirmer pairs, 8 agents)

### Cluster D (codex-alignment) — refuter DONE 6/6 CONFIRMED

- **D1 CONFIRMED** — backfill_smoke:302-305 todo 6 → flip `[x]` "answered by action — RULED in-scope": register §6b
  (canonical-cutover-register.md:378-379) + non-canonical-path-inventory.md:243 + archive
  instrument_availability_hive_canonicalisation:190-193 (sink-PREFIX co-fix `instruments-service@a9be6ce9` same commit,
  co-migrated 2026-08-03). ALSO strip leading `6.` (todo-format non-canonical). Residuals noted (sports fixtures /
  32,846 content_mismatch) do not contradict.
- **D2 CONFIRMED** — cefi_4surface:867 → reword "(dropped from this log's context_scope as redundant for its focus)"
  (cross-asset-canonical-target-ssot.md status: current, live-cited at availability-manifest:1117 + 10+ refs; commit
  2748b15fc shows context_scope trim, not supersession).
- **D3 CONFIRMED** — adapter_findings:99-100 → re-point to `/codex/02-data/honest-coverage-model.md` § "coverage.json v2
  schema (CK1)" (data-status-endpoint-contract.md grep-0 coverage.json).
- **D4 CONFIRMED** — candle_feature:206 → mark pre-amendment history; **752eaff DANGLING — DO NOT CITE**; cite
  unified-trading-pm@9161c8d7b/6bd8b4e5b (codex mentions all NEGATIVE — claim strengthened).
- **D5 CONFIRMED** — mtds_is_full_adapter_smoketest:128-130 → add honest-absence-downstream-handling.md:97 citation
  (data-pipeline-correctness-hard-rule.md grep-0 placeholder).
- **D6 CONFIRMED** — autonomous_decisions:445-448 entry-12 → replace with fold-into-prediction_phase_ab_residuals § A3
  resolution (prediction_phase_ab_residuals:279 "2026-07-26 fold-in … entry #12, option A" + archived shell status:
  complete + `unified-trading-pm@2c61a8dc4`).

### Cluster C (live-state claims) — CONFIRMER DONE 6/6 CONFIRMED (refuter still pending)

- **C1 CONFIRMED** — deribit_binance_finalize:77-78 → replace with 5-relaunch chain: 4 SPOT died (3 preemptions +
  WORKER_STALLED kill), 5th 2026-08-06 ON_DEMAND `cefi-queue-heavy-binancefutu-x17-20260806-163512` RUNNING;
  post-backfill gates unmet. (track2_backfill_vm_preempted_no_recovery issue :184-191/:555-560/:594-602.)
- **C2 CONFIRMED** — cefi_track2:69 → append "(June-rate extrapolation did NOT hold live: measured 2026-07-28 ≈3.25
  days/hr → ~30-day ETA — see Progress Log 2026-07-28 entries)".
- **C3 CONFIRMED** — shard24:139-140 → qualify: runbook amended 2026-08-02 root-cause-diagnosed carve-out resets ≤2/day
  bound (rb_infra_relaunch.md:70-74); shard 24's own fix 09a2374 would satisfy once deployed. Doc's 08-03/04/06 entries
  never absorbed it.
- **C4 CONFIRMED** — cefi_legacy_bucket:137-139 → mechanism clause wrong: whole-bucket destroy IS restorable (§3a,
  delete-safety-protocol.md:266-268, extended 2026-07-28 same day doc filed); bucket deleted 2026-07-14 → 7-day default
  window long elapsed → "likely gone" OUTCOME stands, mechanism corrected.
- **C5 CONFIRMED + correction** — cryptovenue Barchart: the "IN PROGRESS (this session)" phrase is at :603, NOT :225.
  :225 is the stale-unflipped `- [ ] [REFACTOR] P2. DEPRECATE + REMOVE all Barchart (own unit — operator 2026-06-24).` →
  FLIP [x] citing uac@844c5ee6b (verified ancestor; commit literally "Barchart removal") + codex retirement; residual =
  dead comments/config (smoke_matrix.py:143, provider_api_versions.yaml:55-59, docstrings) → new scoped todo; do NOT
  delete TRADFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES quarantine.
- **C6 CONFIRMED** — cryptovenue:605-609 BLOCKED-DATA → retag reflecting: KRX twins shipped (005380/005930/000660 .KS,
  UAC tradfi_ticker_universe.py:402-404 + KrxEquityDef + venue_mapping.py:249 "KRX": "yahoo_finance", uac@844c5ee6b);
  residual = low-latency/intraday basis feed only.

### Cluster C (live-state) — REFUTER DONE 6/6 CONFIRMED (matches confirmer)

- C1 — replace :76-79 with 5-relaunch chain (2×2026-07-30 preempted 18:48Z/06:14Z, 08-01 WORKER_STALLED kill, 08-02
  self-delete, 08-06 ON_DEMAND RUNNING). False from authoring moment — relaunch-1 landed 2026-07-30.
- C2 — annotate :69 as 2026-07-18 ruling; measured 2026-07-28 ≈3.25 days/hr → ~30-day ETA; last_updated :25 stale
  (separate flag).
- C3 — qualify :139-140: carve-out added commit d4f7fab9d 2026-08-02; applicability to shard-24 is an operator call (fix
  09a2374 fixed the monitor, not launch path) — fix text frames carve-out exists, do not assert applies.
- C4 — mechanism corrected, conclusion stands (14 elapsed days > 7-day baseline window; never claim restorable).
- C5 — honest close: FLIP :225 [x] + fold residual (delete dead `"BARCHART"` key smoke_matrix.py:143); step (1) "~30
  files" never literally zeroed — close is "verification + one dead-key cleanup".
- C6 — retag :605-608 to plain `[DATA]` (drop BLOCKED-DATA), re-scope to live low-latency basis feed only; sibling
  BLOCKED-DATA mentions :402/:532/:560/:566 share staleness class → flag, don't fix.

### Cluster A (flips/archive) — REFUTER DONE: A1/A2/A5 CONFIRMED, A3 REFUTED, A4 REFUTED-as-blocked

- **A1 CONFIRMED + SHA TRAP**: `instruments-service@1284606a` is a DIVERGED DUPLICATE — NOT on origin/LDR (lives only on
  `origin/wip-preserve/slot-5-instruments-service-diverged-20260805T111826Z`); identical tree shipped as **`97801b5d`**
  (ancestor of origin/LDR) — FLIP MUST CITE `97801b5d`, never 1284606a. Also `investigate_chain_lossy_20260724.py` does
  NOT exist in scripts/ (scratchpad only) — new scoped todo must promote it first. Update :834-837 + :875 sha cites.
- A2 CONFIRMED — batch7_finalize:70-72 → "archived-resolved, not deleted": plans/archive/issues/
  mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md (status: resolved, flip 64ef0b9e3 + archive
  a04f74e1c/ff619d49f, all [x]); stray active duplicate removed by unified-trading-pm@82d6d6bf7; batch7 todo 2
  DONE-ELSEWHERE 2026-08-06.
- A3 REFUTED — honest_coverage:474-475 [x] LEGITIMATE (DONE annotation verified; batch1 todo 4 + uac@e34afc1d reachable;
  deployment-api@554cde9 + deployment-ui@8f6c4bc reachable). Keep. No un-flip. (Nit: follow-up cite is non-slash — out
  of scope.)
- A4 REFUTED-as-blocked — coinbase_cde NOT archive-ready: frontmatter `status: open` (must be resolved) +
  `locked_by: live-defi-rollout` (human `[unlock-plan]` only) + 6-step ritual incl. referrer repoint (3 active docs cite
  via RELATIVE issues/... path — closeout:252, track2:125, launcher-guard:136) + sha correction (todo 3 cites f9fa7587 —
  diverged; real = 82d86feb/00930194 on LDR). B0-C4 "stale pending" caveat REFUTED as blocker (dated narrative, subject
  todo 3 DONE). → route to operator (unlock + ritual) or report.
- A5 CONFIRMED — cefi_master:631 "5 active plans" vs actual 19 active non-issue plans (46 incl. 27 issue docs);
  populate_epic_bodies_2026_05_21.py has NO --epic flag (only --dry-run/--apply, non-recursive over active/*.md) → full
  regen (dry-run first) or flagged hand-fix. → scope question to STEP 6.

### Cluster A — CONFIRMER DONE (A1/A2/A3/A5 match refuter; A4 SPLIT verdict)

- A1 — same verdict; flip split text refined: [x] resolved-half cites `instruments-service@97801b5d` (content-verified
  at HEAD :209-221; v2 reuse :401); new todo = promote investigate_chain_lossy_20260724.py from scratchpad to scripts/
  then re-run/decide. Never cite 1284606a (pre-rewrite twin).
- A2 — same verdict; fix text: "archived-resolved, not deleted; sweep 82d6d6bf7 removed active copy; batch7 todo 2
  DONE-ELSEWHERE".
- A3 — KEEP [x] (flip commit 65f653fd9 verified; batch1 todo 4 + uac@e34afc1d on origin/LDR) + ANNOTATE leading bold →
  "**CLOSED 2026-08-03 (na-eligibility-audit; evidence below) — was NOT closed 2026-07-29/30 here: genuinely contested,
  left open rather than force a premature verdict.**" (kills the on-its-face contradiction). Trap: batch1 FINALIZE
  false-completion-claim issue exists — do not attribute this flip to the finalize twin.
- **A4 SPLIT → operator route**: refuter = NOT archive-ready (status: open + locked_by → human [unlock-plan] per
  archival-discipline:44, agents never auto-unlock); confirmer = YES (locked_by is corpus-wide boilerplate — 62 active
  - 715 archived docs; status flip is part of the archive commit; 4 referrers repointable: track2:125, closeout:252,
    launcher-guard:136, archived cefi_consolidated_native_ao_extract:470). BOTH agree on in-doc fixes (writable, no
    archive): sha cite f9fa7587→82d86feb (pre-rewrite twin), stale :130-131 "pending" caveat → prose fix (window now
    fetchable, _CDE_REGISTRATION_DATE=2025-12-12). → STEP 6 unlock-or-keep question.
- A5 — regen via populate_epic_bodies_2026_05_21.py --dry-run → --apply (whole-corpus, generator-owned since
  2026-07-16); NEVER hand-fix. Dry-run blast radius to be inspected in STEP 5.

### Cluster B (doc-internal contradictions) — CONFIRMER DONE 8/8 CONFIRMED (refuter pending)

- B1 — cefi_backfill:111-113 → rewrite todo to Option A only (range-loop in one process); Option B dropped (08-04
  cProfile :146-152: fixes ~1.6% of ~54.5s wall clock). NOTE :144 "neither adopted here" does not rescue the todo.
- B2 — cefi_enumeration_audit: append SUPERSEDED-2026-08-05 cross-ref to Class B (:243): 08-05 live read (10.7M rows)
  found HYPERLIQUID 182/182 set-diff 0 (marker-vs-token artifact) + KRAKEN-FUTURES 10 legacy id-forms resolving to
  canonical — "no gap / no code fix"; Class A (BYBIT/COINBASE/BITGET marker migration) untouched, still-open P2.
- B3 — cefi_residual:110-122 → annotate residual #3 DONE 2026-07-27 (28,755 dropped / 0 residual, idempotency
  re-verified; Progress Log :607-614 independent record); no --apply pending.
- B4a — canonical_path_oracle resolved_by → reword: 1,697 gone BUT 07-27 "confirmed gone" was FALSE NEGATIVE; 63 objects
  in disjoint live window migrated via batch_live_filename_divergence §5 P1; see CORRECTION.
- B4b — :321 → move BLOCKED-UPSTREAM-DESIGN AFTER [DATA] P2 (deliberate 2026-08-02 retag BLK-fd7b206d kept intent;
  placement broke _TODO_TAG_PRIORITY_RE anchor → ao_done_gate false match; corpus convention = marker after priority).
  TRAP: Bash mangles the literal token in output — use Read/editor content when quoting.
- B4c — :300-301 → move mid-line `- [ ] [SERVICE] P2` to its own line (backlog regen _UNCHECKED_RE anchors line-start
  only — currently INVISIBLE to ingestion).
- B5 — aster:212 Deferred table row → "Done 2026-07-26 (core ask; 2 residuals filed separately); executed via
  cefi_satellite_ao_dispatch_batch1 todo -001; full-range confirmation gated on mdps candle-manifest-emission fix".
  (:97-100 is 07-21 design-decision history — defensible; align the TABLE.)
- B6 — shard24 title :3-6 tail clause → "deploy-lag gap since closed 2026-08-02 (image postdates fix commit —
  batch4:latest UPDATE_TIME=2026-08-02T15:23:00 verified), test-pass half of done-when still unverified per Progress Log
  :195-197". [OPERATOR] P2 todo :154-163 stays open.

## STEP 6 routing log (all POSTed to operator, can_continue: true — none block the run)

- **Q1 [P1]** ASTER attempted_failed contradiction (closeout vs aggregated_sources) — rec A (aggregated_sources current;
  annotate closeout on next writable pass)
- **Q2 [P1]** archived cutover ALL-COMPLETE vs fleet truth — rec B (leave archived doc as written)
- **Q3 [P2]** coinbase_cde archive unlock — rec B (keep active; locked flag; safer default)
- **Q4 [P2]** cefi_master epic count 5-vs-19 — rec B (defer whole-corpus regen to Saturday all-run / dedicated plan;
  dry-run verified whole-corpus blast radius)
- **Q5 [P2]** deribit_finalize archive_exempt dual-direction — rec C (leave both; tooling real, codex gap minor)
- **Q6 [P2/P3]** batch: H1 volume-feature fate (a) keep deferred; B2-C6 units (b) report-only; codex-drift sweep (c)
  file tracked todo — rec A

**Codex-drift sweep follow-up (pending Q6c answer — do not dispatch before operator answer):**

- [ ] [DOC] P1. Dedicated codex-drift sweep plan: fold the 14 CODEX-STALE findings (7 P1) into their SSOTs —
      orphan-object-detection.md:291-294, honest-absence-downstream-handling.md:1246-1258, per-asset-group-bucket-
      layouts.md:129, availability-manifest-and-data-status.md:69-70 + shard-level-failure-isolation.md:97-98 +
      :813/:834/:986, data-lineage-MTDS-features-ml.md:123-128, vm-launcher-runbook.md:364-369/:510-516,
      data-pipeline-alerts.md:144, pipeline-mode-partition.md:167-168/:127, instruments-foundation-and-catalogue-
      completeness.md:319-320/:514-515, tradfi-databento-sourcing-ssot.md:328, cross-asset-canonical-target-ssot.md:
      469-470 — full evidence per finding in this doc's hunter-C section. Codex edits are operator-gated: the plan must
      carry [OPERATOR] approval + the findings doc citation.

## Deferred work after 2026-08-06 (run-close)

| item                                                    | state/why deferred                                | blocked-on               |
| ------------------------------------------------------- | ------------------------------------------------- | ------------------------ |
| STEP 8 operator answers (Q1-Q6) → apply                 | Cannot be done yet — answers pending in dashboard | operator reply           |
| Codex-drift sweep (14 CODEX-STALE findings)             | Operator-gated (Q6c) + codex edits are gated      | operator approval        |
| cefi_master epic body regen (5→19)                      | Whole-corpus regen deferred                       | Saturday all-run / Q4    |
| coinbase_cde archival (unlock + 6-step ritual)          | locked_by + operator question Q3                  | Q3 answer                |
| ASTER attempted_failed annotation on closeout           | GRACE (read-only this run)                        | grace window + Q1 answer |
| epic regen + archival rituals from other tranches' runs | out of shard scope                                | their runs               |

### Lessons learned 2nd half (STEP 4-7 — don't re-learn)

- **PRE-HISTORY-REWRITE SHA TRAP (hit 3× this run)**: any sha cited in a doc written before the 2026-08-05 history
  rewrite may be a diverged twin NOT on origin/live-defi-rollout (`1284606a`→`97801b5d`, `f9fa7587`→`82d86feb`;
  `752eaff` dangling entirely). ALWAYS `git merge-base --is-ancestor <sha> origin/live-defi-rollout` before citing in a
  flip; on fail, find the twin by same-subject/timestamp (the twin is the ancestor-of-LDR commit with the same message).
- **/blocked endpoint schema**:
  `{"task_id","question","options":["A: ...","B: ..."],"recommendation","can_continue", "continue_on"}` — a
  `message`-keyed payload gets 422.
- **plan-health result path**: `/api/plan-health/result` (DASH), not `/api/plan_health/result` (404).
- **Prettier-padded lines**: proseWrap-padded docs have huge trailing whitespace — Edit old_string must be a SHORT
  unique substring (padding excluded); the pre-commit prettier autostage normalizes the result.
- **Bash mangles `BLOCKED-UPSTREAM-DESIGN`** in command output (renders as `n`) — quote the token from Read/editor
  content, never from grep output.
- **Frontmatter edits via perl -0pi are error-prone** (duplicated keys possible) — use the Edit tool and verify with
  `rg -n` after.
- **2026-07-30 no-double-gate ruling applied 3×**: finalize body banner "STATUS: draft — NOT dispatched" is the STALE
  side; frontmatter `status: active` is correct → align the BODY, never the frontmatter.
- **Zero-checkbox sweep is live**: 2 docs this run had prose "Suggested follow-up/remediation" sections with no `- [ ]`
  — convert, don't leave prose (backlog regen only sees line-start `- [ ]`).
- **Epic regen is whole-corpus**: populate_epic_bodies_2026_05_21.py has no --epic flag; a cefi-shard run must NOT regen
  (collides with concurrent tranche runs on shared epics) — defer to unsharded runs.
