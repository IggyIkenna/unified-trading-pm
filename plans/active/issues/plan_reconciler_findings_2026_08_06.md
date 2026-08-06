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
related: [cefi_consolidated_closeout_2026_07_18.md]
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
