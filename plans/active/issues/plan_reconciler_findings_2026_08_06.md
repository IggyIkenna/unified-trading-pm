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

(pending STEP 4)

## Contradictions

(pending)

## Doc-drift

(pending)

## Hygiene fixes

(pending)

## Filed

(pending)

## Archive candidates (operator review)

(pending)

## Refuted (dropped by verify)

(pending)

## Coverage (hunters / batches / docs)

(pending)

## Plans not reached

(pending)

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
