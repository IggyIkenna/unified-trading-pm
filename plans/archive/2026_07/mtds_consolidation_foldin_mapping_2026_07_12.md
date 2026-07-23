---
doc_type: plan
title: MTDS/MDPS 2-survivor consolidation — fold-in/archive mapping for active plans outside M-1/M-2
summary: >-
  Enforces the mtds_mdps_master 2-survivor consolidation (operator ruling 2026-07-12, plan-reconciliation findings
  175/142/146: "ENFORCE 2 survivors") by enumerating every active/draft/paused plan carrying `parent_epic:
  mtds_mdps_master` outside the two named survivors — M-1 `data_completion_to_100_all_ag_2026_06_21` and M-2
  `mtds_file_size_refactor_2026_06_08` — proposing a fold-in/archive/keep disposition per plan with justification, and
  gating any execution behind explicit operator approval of the mapping.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [mtds, mdps, consolidation, plan-hygiene, fold-in, archive, plan-reconciliation]
related:
  [
    ../epics/mtds_mdps_master.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/mtds_file_size_refactor_2026_06_08.md,
    issues/plan_reconciliation_operator_decisions_2026_07_11.md,
  ]
created: "2026-07-12"
last_updated: 2026-07-13
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra
drift_direction: correct-codex
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "operator ruling 2026-07-12, plan-reconciliation Q&A (findings 175/142/146) — see
  plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md §A2; execution HARD GATE approved by operator
  ruling 2026-07-13 ('Approve all + unlock')"
---

> **✅ EXECUTED 2026-07-13 [unlock-plan] (operator ruling: "Approve all + unlock").** The HARD GATE below was approved
> and every fold-in/archive/keep disposition executed. See the Progress Log for the full audit trail + execution shas.
> This plan is now complete — no further action required here.

> **Why this plan exists.** `plans/epics/mtds_mdps_master.md` already declares (2026-06-26 consolidation banner): "live
> MTDS/MDPS work now runs through 2 themed survivors" — M-1 (`data_completion_to_100_all_ag_2026_06_21.md`,
> backfill-to-100% + honest-absence remediation) and M-2 (`mtds_file_size_refactor_2026_06_08.md`, retitled "MTDS/MDPS
> tech-debt & coverage," ⏸️ DEFERRED/non-essential). In practice, **17 more active/draft plans still carry
> `parent_epic: mtds_mdps_master`** (12 needing a real fold/archive/keep decision + 5 already-functionally-done
> plan-hygiene-debt) and were never folded or archived under that consolidation — this plan is the enumeration +
> proposed mapping the operator ordered, gated on their approval before anything is touched.
>
> **2026-07-12 verification-pass correction**: the figure above was originally written as "13 more" — re-verified this
> session (todo 1) against `grep -l "^parent_epic: mtds_mdps_master" plans/active/*.md`: **20 files match**, of which 2
> are the named survivors and 1 is this audit plan itself (also carries the epic tag, since it lives under the same
> consolidation — it is not a candidate for its own mapping). That leaves **17** real candidates, not 13 — the original
> count under-counted by not excluding this plan's own file from the "remainder" arithmetic (20 − 2 survivors = 18, then
> off-by-one against the 17 actual candidates). Confirmed breakdown: **12** in the fold/archive/keep table below + **5**
> in the plan-hygiene-debt table = 17. See Progress Log for full audit trail.

## Codex SSOTs

| Doc                                                                              | Owns                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/codex/02-data/data-pipeline-correctness-hard-rule.md`                          | Data-correctness heartbeat rule — governs whether folded scope can be deferred                                                                                                                                                                                                                                                                                                                                                                 |
| `/codex/02-data/honest-coverage-model.md`                                        | Two-layer/two-view coverage model M-1's backfill scope must stay consistent with                                                                                                                                                                                                                                                                                                                                                               |
| `/codex/05-infrastructure/manifest-consolidator-ssot.md`                         | Manifest-consolidator ownership — relevant to several canonicalisation candidates                                                                                                                                                                                                                                                                                                                                                              |
| `/codex/11-project-management/doc-frontmatter-schema.md`, `plans/PLAN_FORMAT.md` | Frontmatter schema + Archive Criteria gate table / Plan Locking mechanics this plan's execution must follow (was: "Archival ritual (5-step)" — corrected 2026-07-14, verify-rerun-2 finding 223: verified via grep neither file contains the 5-step ritual sequence; it is stated only in `cursor-configs/CLAUDE.md` § Plans authoring discipline, per the same-day correction in `mvp_reconciliation_closeout_v10_2026_06_27.md` finding 383) |
| `cursor-configs/CLAUDE.md` § Plans authoring discipline                          | Archival ritual (5-step): migrate DEFERRED → banner → codex-alignment check → update CLAUDE.md/codex → clear lock                                                                                                                                                                                                                                                                                                                              |
| `plans/active/task_template.md`                                                  | Plan-authoring rules this plan + its spawned edits must conform to                                                                                                                                                                                                                                                                                                                                                                             |

## Pre-audit manifest — candidates found via `rg -l '^parent_epic: mtds_mdps_master' plans/active/*.md`

Full command run this session: `grep -l "^parent_epic: mtds_mdps_master" plans/active/*.md` cross-checked against
`^status:` per file. 20 files matched; 2 are the named survivors (excluded below); **1 is this audit plan itself**
(`mtds_consolidation_foldin_mapping_2026_07_12.md` — also carries the epic tag, correctly excluded, not a candidate for
its own mapping); **5 are already functionally done** (3 literally `status: complete`, 2 `status: active` with 0 open
todos — corrected 2026-07-12; the original pass's "5 are `status: complete`" framing was imprecise, listed separately
below as simple-archive, not fold/keep decisions); the remaining **12** are the real fold/archive/keep candidates. 20 −
2 (survivors) − 1 (self) − 5 (hygiene-debt) = **12**, matching the table below.

### Survivors (excluded — not candidates)

| Slot | Plan                                          | Role                                          |
| ---- | --------------------------------------------- | --------------------------------------------- |
| M-1  | `data_completion_to_100_all_ag_2026_06_21.md` | Backfill-to-100% + honest-absence remediation |
| M-2  | `mtds_file_size_refactor_2026_06_08.md`       | ⏸️ DEFERRED — MTDS/MDPS tech-debt & coverage  |

### Plan-hygiene debt — already functionally done, simple archive (no fold decision needed)

> **2026-07-12 verification pass (todo 3)** — re-read every row's frontmatter + todo checkboxes directly (not just the
> seed summary). Two corrections vs the original seed table: (1) `mdps_polars_engine_cost_sharpening`'s frontmatter
> `status:` is **already `complete`**, not `active` as originally written — this makes the archive call even less
> ambiguous, not more; (2) `solana_defi_legacy_migration`'s actual done-count is 32, not 31 (negligible; 0-open
> confirmed either way). Added a `Locked?` column: `locked_by: live-defi-rollout` blocks archival without an explicit
> operator `[unlock-plan]` (`plans/PLAN_FORMAT.md` §"Plan locking" — "Agents MUST NOT archive locked plans even if all
> todos are done"). 4/5 rows are unlocked (archive-clear); `solana_defi_legacy_migration` is locked and needs an
> explicit unlock alongside archival approval.
>
> **✅ EXECUTED 2026-07-13** — all 5 archived to `plans/archive/2026_07/`. `solana_defi_legacy_migration`'s stale
> `status: active` corrected to `complete` + `locked_by` cleared via the operator's blanket `[unlock-plan]`.
> `mdps_polars_engine_cost_sharpening`'s completion credit folded into M-2's Progress Log per its own disposition.

| Plan                                                        | Status                                                      | Open/Done | Locked?                                        | Note                                                                                                             |
| ----------------------------------------------------------- | ----------------------------------------------------------- | --------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `mdps_book_microstructure_precompute_columns_2026_06_28.md` | complete → **✅ ARCHIVED**                                  | 0/6       | no                                             | `status: complete`, verified genuinely 0 open; archived to `plans/archive/2026_07/`                              |
| `mdps_features_full_month_benchmark_binance_2026_06_28.md`  | complete → **✅ ARCHIVED**                                  | 0/5       | no                                             | `status: complete`, verified genuinely 0 open; archived to `plans/archive/2026_07/`                              |
| `tradfi_mdps_passthrough_dependency_gap_2026_06_28.md`      | complete → **✅ ARCHIVED**                                  | 0/5       | no                                             | `status: complete`, verified genuinely 0 open; archived to `plans/archive/2026_07/`                              |
| `solana_defi_legacy_migration_2026_05_27.md`                | active → **✅ ARCHIVED** (`status` corrected to `complete`) | 0/32      | was **yes** (`live-defi-rollout`), now cleared | Functionally complete (0 open todos, verified); frontmatter `status` was stale — corrected + unlocked + archived |
| `mdps_polars_engine_cost_sharpening_2026_06_28.md`          | **complete** → **✅ ARCHIVED**, credit folded into M-2      | 0/6       | no                                             | Functionally + formally complete; completion credit folded into M-2 Progress Log, then archived                  |

### Proposed fold/archive/keep mapping (finalize per todos 1-4 before presenting)

> **2026-07-12 verification pass (todos 1-4)** — every row below was re-read in full (frontmatter + body), open-todo
> counts re-derived from the canonical `- [ ] [TAG] P#.` checkbox convention (the seed table's open counts were already
> accurate against this pattern for 9/12 rows; corrections noted inline for the other 3), and a `Locked?` column added.
> **10/12 rows carry `locked_by: live-defi-rollout`** (`sports_manifest` + `defi_manifest_canonicalisation` included) —
> per `plans/PLAN_FORMAT.md`, archival of a locked plan requires an explicit operator `[unlock-plan]`. This was not
> called out in the seed table; it means every approved FOLD (which ends in archival, todos 8-9) will also need an
> unlock. Recommend the operator's HARD GATE approval double as the unlock authorization (rather than a second
> round-trip per plan) unless the operator wants them handled separately.
>
> **✅ EXECUTED 2026-07-13** — the operator's HARD GATE approval ("Approve all + unlock") doubled as the unlock
> authorization for every locked row below (per the recommendation above). All 9 `FOLD → M-1` rows executed: every open
> todo migrated verbatim into M-1's new "Folded-in scope 2026-07-13" section (130 todos total, provenance + P-levels +
> BLOCKED markers preserved), source plans archived to `plans/archive/2026_07/`. The todo-5 judgment call
> (`defi_manifest_canonicalisation`) was ruled **FOLD → M-1** by the operator.
> `pipeline_mode_source_batch_live_replay_standardisation` was ruled **KEEP standalone** by the operator (overriding
> this table's seed "FOLD → M-1" proposal — see its own row below + the codex SSOTs section note).
> `mdps_features_reduced_artifact_tracker` was ruled **"Keep as tracker"** (overriding the seed's "ARCHIVE (abandoned
> stub)" — the todo-2 re-read below found it is NOT a stub). `sports_manifest_canonicalisation` stays
> KEEP-WITH-JUSTIFICATION per the prior operator ruling (untouched).

| Plan                                                                   | Theme (operator-named)                  | Status / open-done (verified 2026-07-12)                                                                                                           | Locked?                                                      | Proposed disposition                                             | Justification                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ---------------------------------------------------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`         | bucket-naming                           | active, 14/17 (confirmed exact)                                                                                                                    | was yes, now cleared                                         | **✅ FOLDED → M-1** (executed)                                   | Legacy-bucket drain + migrate + decommission is data-correctness/backfill-flavor, M-1's core mandate                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `data_source_provenance_all_asset_groups_2026_06_01.md`                | data-provenance                         | active, 19/17 (confirmed exact)                                                                                                                    | was yes, now cleared                                         | **✅ FOLDED → M-1** (executed)                                   | "stamp source... backfill existing objects" is literally M-1's backfill-to-100% scope                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `macro_econ_adapter_scaffolds_2026_06_09.md`                           | macro/micro-econ                        | active, 6/6 (confirmed exact)                                                                                                                      | was yes, now cleared                                         | **✅ FOLDED → M-1** (executed)                                   | New adapters directly expand captured coverage — M-1's backfill mandate                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `cefi_manifest_canonicalisation_2026_06_01.md`                         | per-AG canonicalisation (cefi)          | active, 24/55 (confirmed exact)                                                                                                                    | was yes, now cleared                                         | **✅ FOLDED → M-1** (executed)                                   | Per-AG single-walk v9 canonicalisation IS the backfill-to-100% mandate M-1 already owns                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `tradfi_manifest_canonicalisation_2026_06_01.md`                       | per-AG canonicalisation (tradfi)        | active, **22**/37 (was 23; off-by-1, minor drift, not concerning — file untouched since `last_updated: 2026-06-27`)                                | was yes, now cleared                                         | **✅ FOLDED → M-1** (executed)                                   | Same as cefi row                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `prediction_manifest_canonicalisation_2026_06_01.md`                   | per-AG canonicalisation (prediction)    | active, **9**/60 (was 10/59; off-by-1, same minor-drift explanation)                                                                               | was yes, now cleared                                         | **✅ FOLDED → M-1** (executed)                                   | Same; near-complete (86%), small residual migrated                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `downstream_services_manifest_canonicalisation_2026_06_01.md`          | per-service canonicalisation            | active, 11/40 (confirmed exact)                                                                                                                    | was yes, now cleared                                         | **✅ FOLDED → M-1** (executed)                                   | Explicitly "coordinated under the defi_manifest_canonicalisation MASTER" (see next row)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `defi_manifest_canonicalisation_2026_06_01.md`                         | cefi-universe / cross-plan coordination | active, 23/41 (confirmed exact)                                                                                                                    | was yes, now cleared                                         | **✅ FOLDED → M-1** (executed — todo-5 judgment call ruled FOLD) | **New evidence (2026-07-12 verify)**: this plan's own in-body banner, dated **2026-06-07** (predates this consolidation plan by over a month), already reads "⬆️ DEMOTED — this §MASTER is now the DeFi EXECUTOR only; the cross-plan/cross-AG coordination role moved UP to `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`" — a **different file under a different epic** (`parent_epic: manifest_master`, confirmed by direct read, correctly outside this plan's `mtds_mdps_master` grep scope). So the "SECOND coordinator competing with M-1" framing in the seed justification is stale: `defi_manifest_canonicalisation` already demoted itself to DeFi-executor-only a month before this audit, and the real cross-AG coordinator lives in a separate epic entirely. The operator ruled **FOLD → M-1** for the DeFi-executor content on this basis.                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` | (infra/foundation)                      | active, **13**/17 (seed table had the columns **swapped** — was written "17/13"; corrected to open-then-done for consistency with every other row) | yes (`live-defi-rollout`), still locked (KEPT, not archived) | **🟢 KEPT STANDALONE** (operator override 2026-07-13)            | Gates "all v9 manifest --apply runs on Phase 0 completion" — direct prerequisite of M-1's canonicalisation scope. **Operator ruled KEEP STANDALONE** (2026-07-13) rather than fold — a P0, 25-repo, 9.6-day cross-cutting foundation/standardisation plan that GATES the per-AG canonicalisation walks (including M-1's own) is a prerequisite-gate, not a backfill task; folding a gate INTO the plan(s) it gates is an unusual shape. Banner added to the plan pointing at M-1.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `bar_edge_left_vs_right_remediation_2026_06_08.md`                     | (data-correctness, MDPS)                | active, 1/10 (confirmed exact)                                                                                                                     | was yes, now cleared                                         | **✅ FOLDED → M-1** (executed)                                   | Near-done (1 open); candle-edge data-correctness fix, not tech-debt — M-1 not M-2                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `mdps_features_reduced_artifact_tracker_2026_06_28.md`                 | (cost/coverage tracker)                 | **draft**, 0/0 (no literal checkboxes — by design, see note)                                                                                       | no                                                           | **🟢 KEEP AS TRACKER** (operator ruling 2026-07-13)              | **Full-body read (todo 2) overturns the seed classification.** This is not an abandoned 0-todo stub: it is a live coordination tracker for **9 mini-plans across 4 different parent epics** (only 4 of the 9 — Plans 1/5/7/8 — carry `parent_epic: mtds_mdps_master`; those 4 are EXACTLY the 4 `status: complete` rows in this plan's own plan-hygiene-debt table above). The tracker itself already carries a **same-day (2026-07-12) self-correction note** citing plan-reconciliation findings 183/188/189/190, documenting that 4/9 mini-plans independently reached `status: complete` with no coordinated batch-flip ever recorded here. The other 5 mini-plans (Plans 2,3,4,6,9) live under `features_and_ml_master` / `batch_live_symmetry_master` / `execution_master` — spot-checked 2026-07-12: `features_read_book_columns_not_snapshots` = complete, `features_no_lookahead_reaggregation_guard` = active, `execution_fidelity_tiers_uac_governed` = active, `honest_coverage_smoke_harness` exists (status not checked), `mvp_for_mdps_and_features_universe_uac` not found (not yet authored). **Operator ruled "Keep as tracker"** (2026-07-13) — its rows for Plans 1/5/7/8 updated to point at their `plans/archive/2026_07/` location (Plan 8 additionally credited to M-2); re-visit closure once all 9 mini-plans resolve. |
| `sports_manifest_canonicalisation_2026_06_01.md`                       | sports vertical                         | active, 2/101 (confirmed exact)                                                                                                                    | yes (`live-defi-rollout`)                                    | **KEEP-WITH-JUSTIFICATION** (operator-ruled, see todo 6)         | Ruling 175/142/146: "sports_manifest stays mtds_mdps child" — no fold/archive action; locked-status is moot here since disposition is KEEP, not archive                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |

## Todos

- [x] [AUDIT] P0. **Confirm the candidate enumeration is complete** — re-run
      `grep -l "^parent_epic: mtds_mdps_master" plans/active/*.md` and cross-check `^status:` for every hit against the
      tables above; the seed tables were built this session and should be treated as a draft, not final. Gate: explicit
      confirmation the candidate count (13 non-survivor, non-trivially-complete plans) is accurate or a corrected count
      with the delta explained. — unified-trading-pm@(uncommitted, docs-only per-plan edit, no ship gate applies to a
      local-only human plan). **Corrected count = 17 total non-survivor plans (12 fold/archive/keep + 5
      plan-hygiene-debt), not 13** — the original "13" omitted excluding this audit plan's own file
      (`mtds_consolidation_foldin_mapping_2026_07_12.md`, which also carries `parent_epic: mtds_mdps_master`) from the
      arithmetic (20 grep hits − 2 survivors − 1 self − 5 hygiene-debt = 12; delta fully explained in the "Why this plan
      exists" correction note + Pre-audit manifest section above).
- [x] [AUDIT] P0. **Read each candidate's full body** (not just summary/tags/todo-count) to confirm the proposed theme
      classification and disposition in the mapping table above — flag any candidate whose actual scope diverges from
      its title/summary. — Read all 12 fold/archive/keep candidates + all 5 plan-hygiene-debt files in full
      (frontmatter + relevant body sections). Two material divergences found and flagged in the finalized table: (1)
      `defi_manifest_canonicalisation_2026_06_01.md` already self-demoted its "MASTER cross-plan coordinator" framing on
      2026-06-07 (a month before this audit) — the real coordinator now lives in a DIFFERENT epic
      (`master_data_canonicalisation_migration_catalogue_2026_06_07.md`, `parent_epic: manifest_master`), which
      materially informed the operator's todo-5 FOLD ruling; (2) `mdps_features_reduced_artifact_tracker_2026_06_28.md`
      is NOT an abandoned 0-todo stub — it is a live 9-mini-plan coordination tracker (4 of the 9 are exactly this
      plan's own plan-hygiene-debt rows) with its own same-day 2026-07-12 self-correction note — reclassified from
      "ARCHIVE" to a flagged operator judgment call, which the operator resolved as "Keep as tracker". All other 10
      candidates' theme/disposition were confirmed consistent with their actual body scope (see per-row Justification
      updates for minor open/done count corrections).
- [x] [AUDIT] P0. **Verify the plan-hygiene-debt table** — for the 3 `status: complete` files + the 2 functionally-done
      `active` files, confirm zero remaining open work (re-check todo checkboxes + any Progress Log claiming residual
      scope) before treating them as simple-archive. — All 5 confirmed genuinely 0 open todos (direct checkbox count,
      both raw and strict `[TAG]`-pattern). One correction: `mdps_polars_engine_cost_sharpening_2026_06_28.md`'s
      frontmatter `status:` is **already `complete`** (seed table said `active`) — strengthens, doesn't weaken, the
      archive call. `solana_defi_legacy_migration_2026_05_27.md` is the only locked row in this table
      (`locked_by: live-defi-rollout`) — archival needed `[unlock-plan]`, granted by the operator's blanket approval.
- [x] [DESIGN] P0. **Finalize the fold-in/archive/keep mapping table** — incorporate todos 1-3's findings into the seed
      table above; this finalized table is what gets presented to the operator in the HARD GATE below. — Both tables
      (plan-hygiene-debt + fold/archive/keep) rewritten in place with dated 2026-07-12 verification notes, corrected
      open/done counts, a new `Locked?` column (10/12 fold candidates + 1/5 hygiene-debt row carry
      `locked_by: live-defi-rollout`, requiring `[unlock-plan]` at execution time — not previously called out), and the
      two scope-divergence flags above. Table is presentation-ready for the HARD GATE todo below.
- [x] [DESIGN] P0. **Resolve (as a proposal, not a decision) the `defi_manifest_canonicalisation_2026_06_01.md` judgment
      call** — it is itself a coordinator ("MASTER... cross-plan coordinator") wrapping several of the OTHER candidates
      in this mapping (tradfi/sports/downstream/cefi canonicalisation). Propose either (a) fold its coordination
      content + all its wrapped sub-plan references into M-1, treating M-1 as the sole surviving coordinator, or (b) the
      reverse. State a recommendation but do not execute either — this is exactly the kind of call the HARD GATE below
      exists for. — **Operator ruling 2026-07-13: FOLD → M-1.** Executed: all open todos from
      `defi_manifest_canonicalisation_2026_06_01.md` migrated into M-1's "Folded-in scope 2026-07-13" section; source
      plan archived to `plans/archive/2026_07/`.
- [x] [AUDIT] P0. **Confirm `sports_manifest_canonicalisation_2026_06_01.md` disposition** = KEEP-WITH-JUSTIFICATION per
      operator ruling 175/142/146 (`plan_reconciliation_operator_decisions_2026_07_11.md` §A2: "sports_manifest stays
      mtds_mdps child, sports_master wording fixed"). No fold/archive action on this plan. The ruling's paired
      "sports_master wording fixed" item is a `sports_master` epic-body edit — out of this plan's scope; file a one-line
      pointer todo in `sports_master`'s own tracking (or the reconciliation issue doc) rather than executing it here. —
      Confirmed: `sports_manifest_canonicalisation_2026_06_01.md` left completely untouched (no fold/archive/edit). The
      "sports_master wording fixed" pointer is recorded in the reconciliation issue doc's 2026-07-13 Progress Log entry
      (see below) rather than executed directly in `sports_master`'s epic body — flagged there for the next agent
      touching that epic, per this todo's own instruction to file a pointer rather than execute it here.
- [x] [BLOCKED-OPERATOR-DECISION] P0. **HARD GATE — present the finalized mapping table to the operator for approval**
      using the structured-options escalation format (`SUB_AGENT_MANDATORY_RULES.md` § "When escalating a question" —
      minimum 2 options, recommendation marked explicitly, "Other" free-text). **Do NOT execute any fold-in, archive, or
      the todo-5 judgment call until the operator responds.** This todo blocks every todo below it. — **✅ APPROVED
      2026-07-13.** Operator ruling (verbatim, recorded in the Progress Log below): "Approve all + unlock" (blanket
      `[unlock-plan]` granted for every locked candidate plan); `defi_manifest_canonicalisation` judgment call (todo 5)
      = "FOLD → M-1"; `pipeline_mode_source_batch_live_replay_standardisation` = "KEEP standalone";
      `mdps_features_reduced_artifact_tracker` = "Keep as tracker"; `sports_manifest_canonicalisation` = KEEP per prior
      ruling 175/142/146. Gate cleared — execution proceeded per the approved mapping.
- [x] [CODE] P1. **Execute approved M-1 fold-ins** (gated on the HARD GATE above) — for each candidate approved for M-1,
      migrate its open todos into `data_completion_to_100_all_ag_2026_06_21.md` with provenance
      (`**MIGRATED     FROM:** <plan>`, matching the epic's existing convention already used for its P2 greeks item),
      then archive the source plan via the 5-step ritual (migrate DEFERRED → banner → codex-alignment check → parent-doc
      update → clear lock). — **DONE.** All 9 FOLD → M-1 candidates executed: 130 open todos migrated verbatim
      (provenance `**(MIGRATED FROM: ...)**` + P-levels + BLOCKED markers preserved) into M-1's new "Folded-in scope
      2026-07-13" section. Each source plan archived via the 5-step ritual (SUPERSEDED/FOLDED banner,
      `status:     superseded` + `superseded_by: data_completion_to_100_all_ag_2026_06_21`, `locked_by`/`locked_since`
      cleared, `git mv` to `plans/archive/2026_07/`). — unified-trading-pm@e4dd7871e.
- [x] [CODE] P1. **Execute approved M-2 fold-ins** (gated on the HARD GATE above) — same migration + archival ritual for
      candidates approved for M-2 (e.g. `mdps_polars_engine_cost_sharpening_2026_06_28.md`, whose own summary says it
      "un-defers the M-2 Polars work" — fold its completion credit into M-2's Progress Log before archiving). —
      **DONE.** `mdps_polars_engine_cost_sharpening_2026_06_28.md` (0 open todos, all shipped) had its completion credit
      folded into `mtds_file_size_refactor_2026_06_08.md` (M-2)'s new Progress Log section, then archived (ARCHIVED
      banner, `git mv` to `plans/archive/2026_07/`). — unified-trading-pm@4336c38f6.
- [x] [CODE] P1. **Archive the plan-hygiene-debt candidates** (gated on the HARD GATE above, though these are low-risk)
      — the 3 `status: complete` files + the 2 functionally-done `active` files, 5-step ritual, no fold needed (nothing
      open to migrate). — **DONE.** All 5 archived: `mdps_book_microstructure_precompute_columns_2026_06_28`,
      `mdps_features_full_month_benchmark_binance_2026_06_28`, `tradfi_mdps_passthrough_dependency_gap_2026_06_28`
      (already `status: complete`, unlocked, simple archive), `solana_defi_legacy_migration_2026_05_27` (stale
      `status:     active` corrected to `complete`, `locked_by` cleared via the operator's blanket unlock), and
      `mdps_polars_engine_cost_sharpening_2026_06_28` (counted in the M-2 fold-in item above). —
      unified-trading-pm@4336c38f6.
- [x] [CODE] P1. **Execute the operator's ruling on the todo-5 judgment call** exactly as approved — do not improvise
      beyond the approved mapping if the operator's answer differs from either proposed option. — **DONE.** Operator
      ruled FOLD → M-1 (matching proposed option (a)); `defi_manifest_canonicalisation_2026_06_01.md`'s open todos
      migrated into M-1 exactly as the other 8 FOLD candidates, no improvisation beyond the approved mapping. —
      unified-trading-pm@e4dd7871e.
- [x] [DOCS] P1. **Update `plans/epics/mtds_mdps_master.md`** banner + `related:`/`related_plans:` frontmatter to
      reflect the post-execution state — remove archived plans from active-plan references, append a dated note
      recording the consolidation completion with this plan's sha, and reconfirm the "2 survivors" framing is now
      actually true (no orphaned `parent_epic: mtds_mdps_master` plans left outside M-1/M-2/the operator-kept
      exception). — **DONE.** Added a "🟢 [2026-07-13] CONSOLIDATION EXECUTED" banner superseding the 2026-07-12
      correction banner, recording the full fold/archive/keep disposition + the post-fold roster (2 survivors +
      `pipeline_mode_source_batch_live_replay_standardisation` standalone + `sports_manifest_canonicalisation`
      delegated + `mdps_features_reduced_artifact_tracker` cross-epic tracker). The `related`/`related_plans`
      frontmatter arrays did not list the 9 folded + 5 archived plans to begin with (checked — they were never in that
      array), so no frontmatter array edit was needed. — unified-trading-pm@8eb5293b3. > **[2026-07-14 correction,
      doc-reconciliation finding 170]**: the "now actually true (no orphaned > `parent_epic: mtds_mdps_master` plans
      left outside M-1/M-2/the operator-kept exception)" reconfirmation above > (was: presented as a durable
      reconfirmation) held only at write-time (09:29:58 UTC) — two brand-new same-day > plans
      (`aster_cefi_data_defi_bucket_migration_2026_07_13`, `bybit_futures_chain_write_shape_migration_2026_07_13`, >
      both filed hours later, both `parent_epic: mtds_mdps_master`, both outside the named roster), plus the >
      pre-existing `plans/active/issues/*.md` scope gap in this plan's own candidate-enumeration grep (it never >
      scanned that directory), show the claim needs a recurring re-derivation, not a one-time reconfirmation. See the >
      parallel 2026-07-14 correction on `plans/epics/mtds_mdps_master.md`'s roster banner (findings 168/176/177) for >
      the current re-derivation command.
- [x] [DOCS] P1. **Post-phase codex-alignment check** — grep `codex/` for stale references to any folded/archived plan
      name from this mapping; update or SUPERSEDED-banner as needed. — **DONE.** Grepped `codex/` for all 14
      folded/archived plan slugs; found 10 codex docs with `plans/active/<slug>.md` path references that would 404
      post-move (`availability-manifest-and-data-status.md`, `bar-boundary-candle-edge-convention.md`,
      `bucket-naming-and-config.md`, `defi-canonical-naming-ssot.md`, `prediction-schema-paths.md`,
      `e2e-pipeline-manifest-wiring.md`, `prediction-batch-live.md`, `tradfi-batch-live.md`, `gcs-object-operations.md`,
      `carry-basis-perp.md`); all repointed to `plans/archive/2026_07/<slug>.md`. Bare (path-less) prose citations of a
      plan name were left as-is (still-valid historical references, not broken links). — unified-trading-pm@e4dd7871e.
- [x] [DOCS] P2. **Wire the executed mapping into the reconciliation issue doc** — append a dated Progress Log entry to
      `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 citing findings 175/142/146 and
      this plan's final mapping + execution shas. — **DONE.** Appended a 2026-07-13 entry to that doc's Progress Log
      (append-only section) citing this plan's mapping + all 3 execution commit shas + the "sports_master wording fixed"
      pointer (from todo 6 above). — unified-trading-pm (this same session's next commit).

## Progress Log

- **2026-07-12** — Plan authored per operator ruling 2026-07-12 (findings 175/142/146,
  `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2: "ENFORCE 2 survivors... fold-in/
  archive mapping authored as HUMAN plan for operator approval; sports_manifest stays mtds_mdps child, sports_master
  wording fixed"). Candidate enumeration + seed mapping table drafted this session via
  `grep -l "^parent_epic: mtds_mdps_master" plans/active/*.md` cross-checked against `status:`/todo-counts/summaries; 13
  non-survivor active/draft/paused candidates + 5 plan-hygiene-debt (functionally-done, un-archived) files found. No
  fold/archive action executed — this plan's own HARD GATE todo blocks execution until operator approval.
- **2026-07-12 (verification pass, todos 1-4)** — Executed the VERIFICATION phase only (enumerate/verify candidates +
  finalize the mapping table); stopped at the HARD GATE per explicit instruction — no fold/archive/edit touched any
  candidate plan or epic, no git commands run. Findings:
  - **Todo 1 (enumeration)**: re-ran the grep; 20 files match, not "13 more" as originally framed. Corrected breakdown:
    2 survivors + 1 self (this plan) + 5 plan-hygiene-debt + **12** fold/archive/keep candidates = 20. The seed
    document's "13" undercounted by not excluding this audit plan's own file from the arithmetic.
  - **Todo 2 (full-body read + scope-divergence check)**: read all 17 candidate files in full. Two material divergences
    from the seed classification: (a) `defi_manifest_canonicalisation_2026_06_01.md` already self-demoted its
    "cross-plan MASTER coordinator" framing via an in-body banner dated **2026-06-07** — a month before this
    consolidation plan existed — stating the coordination role moved to
    `master_data_canonicalisation_migration_catalogue_2026_06_07.md` (confirmed by direct read: that file exists,
    `parent_epic: manifest_master`, correctly outside this plan's grep scope). This substantially de-risks (but does not
    resolve) todo 5's judgment call. (b) `mdps_features_reduced_artifact_tracker_2026_06_28.md` was seeded as "ARCHIVE
    (abandoned stub, 0/0 todos)" — full read shows it is a live 9-mini-plan coordination tracker spanning 4 parent
    epics, already carrying its OWN same-day 2026-07-12 self-correction note (citing plan-reconciliation findings
    183/188/189/190) documenting that 4 of its 9 mini-plans — which are exactly this plan's 4 `status: complete`
    plan-hygiene-debt rows — reached completion outside any coordinated batch-flip. Reclassified from a mechanical
    archive to a flagged operator judgment call (do not blind-archive; risks orphaning cross-references for the 5
    still-open mini-plans under other epics). All other 10 candidates' theme/disposition confirmed consistent with
    actual body scope.
  - **Todo 3 (plan-hygiene-debt re-verify)**: all 5 rows confirmed genuinely 0 open todos. One correction:
    `mdps_polars_engine_cost_sharpening_2026_06_28.md`'s frontmatter `status:` is already `complete` (seed said
    `active`) — strengthens the archive call. `solana_defi_legacy_migration_2026_05_27.md` is the only locked row here
    (`locked_by: live-defi-rollout`) and will need `[unlock-plan]` at archival time.
  - **Todo 4 (finalize table)**: both tables rewritten in place with dated verification notes, corrected open/done
    counts (`tradfi_manifest_canonicalisation` 22 not 23 open; `prediction_manifest_canonicalisation` 9 not 10 open —
    both negligible, files untouched since `last_updated: 2026-06-27` per `stat` mtime check, not live drift;
    `pipeline_mode_source_batch_live_replay_standardisation` had its open/done columns swapped in the seed, corrected to
    13/17), and a new **`Locked?` column** — **10 of 12 fold/archive/keep candidates + 1 of 5 plan-hygiene-debt rows
    carry `locked_by: live-defi-rollout`**, which per `plans/PLAN_FORMAT.md` blocks archival without an explicit
    operator `[unlock-plan]`. This was not surfaced in the seed table at all; flagged so the HARD GATE approval can
    bundle the unlock authorization rather than requiring a second round-trip.
  - **Not executed (out of this pass's scope, per explicit instruction)**: todo 5 (defi_manifest judgment-call
    resolution), todo 6 (sports_manifest confirmation — already operator-ruled, not independently re-flipped here), and
    the HARD GATE itself remain untouched/unchecked. No candidate plan, epic, or codex doc was edited — only this plan's
    own body.
- **2026-07-13 (HARD GATE approval + execution) — operator rulings, recorded verbatim**: "Approve all + unlock" (blanket
  `[unlock-plan]` granted for every locked candidate plan in the mapping tables above); todo-5 judgment call
  (`defi_manifest_canonicalisation_2026_06_01.md`) = **"FOLD → M-1"**;
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` = **"KEEP standalone"**;
  `mdps_features_reduced_artifact_tracker_2026_06_28.md` = **"Keep as tracker"**;
  `sports_manifest_canonicalisation_2026_06_01.md` = **KEEP per prior ruling 175/142/146** (unchanged from 2026-07-12).
  HARD GATE todo flipped to approved; execution proceeded in full per the approved mapping:
  - **9 plans FOLDED into M-1** (`bucket_name_ssot_legacy_dual_write_remediation_2026_06_01`,
    `data_source_provenance_all_asset_groups_2026_06_01`, `macro_econ_adapter_scaffolds_2026_06_09`,
    `cefi_manifest_canonicalisation_2026_06_01`, `tradfi_manifest_canonicalisation_2026_06_01`,
    `prediction_manifest_canonicalisation_2026_06_01`, `downstream_services_manifest_canonicalisation_2026_06_01`,
    `defi_manifest_canonicalisation_2026_06_01`, `bar_edge_left_vs_right_remediation_2026_06_08`) — 130 open todos
    migrated verbatim into M-1's new "Folded-in scope 2026-07-13" section, each source plan archived via the 5-step
    ritual to `plans/archive/2026_07/`. Evidence: unified-trading-pm@e4dd7871e.
  - **1 plan credited into M-2** (`mdps_polars_engine_cost_sharpening_2026_06_28`, already complete) — completion credit
    folded into M-2's Progress Log, archived. **4 plan-hygiene-debt plans simple-archived**
    (`mdps_book_microstructure_precompute_columns_2026_06_28`, `mdps_features_full_month_benchmark_binance_2026_06_28`,
    `tradfi_mdps_passthrough_dependency_gap_2026_06_28`, `solana_defi_legacy_migration_2026_05_27` — the last one's
    stale `status: active` corrected to `complete` + unlocked). Evidence: unified-trading-pm@4336c38f6.
  - **10 codex docs** repointed from stale `plans/active/<slug>.md` references to `plans/archive/2026_07/<slug>.md` for
    the 8 folded/archived slugs that had path-style citations. Evidence: unified-trading-pm@e4dd7871e.
  - **`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`** got a "KEPT STANDALONE" banner;
    **`mdps_features_reduced_artifact_tracker_2026_06_28`** got its Plans 1/5/7/8 rows updated to point at their
    archive/M-2 destination, kept as the live tracker; **`epics/mtds_mdps_master.md`** got a 2026-07-13
    consolidation-executed banner recording the post-fold roster. Evidence: unified-trading-pm@8eb5293b3.
  - **`sports_manifest_canonicalisation_2026_06_01.md`** — confirmed untouched (KEEP-WITH-JUSTIFICATION, no fold/archive
    action), matching todo 6's finding; the paired "sports_master wording fixed" item from the original ruling is filed
    as a pointer in the reconciliation issue doc's own Progress Log (§A2) rather than executed directly here, per todo
    6's explicit scope instruction.
  - **Post-fold roster under `mtds_mdps_master`**: 2 survivors (M-1, M-2) +
    `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05` (standalone prerequisite gate) +
    `sports_manifest_canonicalisation_2026_06_01` (delegated vertical, prior ruling) +
    `mdps_features_reduced_artifact_tracker_2026_06_28` (cross-epic coordination tracker) — no orphaned
    `parent_epic: mtds_mdps_master` plans remain outside this set. This plan
    (`mtds_consolidation_foldin_mapping_2026_07_12`) is now `status: complete` — every todo flipped, mapping fully
    executed.
