---
doc_type: plan
title: MTDS/MDPS 2-survivor consolidation — fold-in/archive mapping for active plans outside M-1/M-2
summary: >-
  Enforces the mtds_mdps_master 2-survivor consolidation (operator ruling 2026-07-12, plan-reconciliation findings
  175/142/146: "ENFORCE 2 survivors") by enumerating every active/draft/paused plan carrying `parent_epic:
  mtds_mdps_master` outside the two named survivors — M-1 `data_completion_to_100_all_ag_2026_06_21` and M-2
  `mtds_file_size_refactor_2026_06_08` — proposing a fold-in/archive/keep disposition per plan with justification, and
  gating any execution behind explicit operator approval of the mapping.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [mtds, mdps, consolidation, plan-hygiene, fold-in, archive, plan-reconciliation]
related:
  [
    ../epics/mtds_mdps_master.md,
    data_completion_to_100_all_ag_2026_06_21.md,
    mtds_file_size_refactor_2026_06_08.md,
    issues/plan_reconciliation_operator_decisions_2026_07_11.md,
  ]
created: "2026-07-12"
last_updated: 2026-07-12
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
  plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md §A2"
---

> **Why this plan exists.** `plans/epics/mtds_mdps_master.md` already declares (2026-06-26 consolidation banner): "live
> MTDS/MDPS work now runs through 2 themed survivors" — M-1 (`data_completion_to_100_all_ag_2026_06_21.md`,
> backfill-to-100% + honest-absence remediation) and M-2 (`mtds_file_size_refactor_2026_06_08.md`, retitled "MTDS/MDPS
> tech-debt & coverage," ⏸️ DEFERRED/non-essential). In practice, **13 more active/draft/paused plans still carry
> `parent_epic: mtds_mdps_master`** and were never folded or archived under that consolidation — this plan is the
> enumeration + proposed mapping the operator ordered, gated on their approval before anything is touched.

## Codex SSOTs

| Doc                                                                             | Owns                                                                              |
| ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `codex/02-data/data-pipeline-correctness-hard-rule.md`                          | Data-correctness heartbeat rule — governs whether folded scope can be deferred    |
| `codex/02-data/honest-coverage-model.md`                                        | Two-layer/two-view coverage model M-1's backfill scope must stay consistent with  |
| `codex/05-infrastructure/manifest-consolidator-ssot.md`                         | Manifest-consolidator ownership — relevant to several canonicalisation candidates |
| `codex/11-project-management/doc-frontmatter-schema.md`, `plans/PLAN_FORMAT.md` | Archival ritual (5-step) + frontmatter this plan's execution must follow          |
| `plans/active/task_template.md`                                                 | Plan-authoring rules this plan + its spawned edits must conform to                |

## Pre-audit manifest — candidates found via `rg -l '^parent_epic: mtds_mdps_master' plans/active/*.md`

Full command run this session: `grep -l "^parent_epic: mtds_mdps_master" plans/active/*.md` cross-checked against
`^status:` per file. 20 files matched; 2 are the named survivors (excluded below); 5 are `status: complete` and already
functionally done (listed separately as simple-archive, not fold/keep decisions); the remainder are the real
fold/archive/keep candidates.

### Survivors (excluded — not candidates)

| Slot | Plan                                          | Role                                          |
| ---- | --------------------------------------------- | --------------------------------------------- |
| M-1  | `data_completion_to_100_all_ag_2026_06_21.md` | Backfill-to-100% + honest-absence remediation |
| M-2  | `mtds_file_size_refactor_2026_06_08.md`       | ⏸️ DEFERRED — MTDS/MDPS tech-debt & coverage  |

### Plan-hygiene debt — already functionally done, simple archive (no fold decision needed)

| Plan                                                        | Status   | Open/Done | Note                                                                                                                                      |
| ----------------------------------------------------------- | -------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `mdps_book_microstructure_precompute_columns_2026_06_28.md` | complete | —         | `status: complete`, un-archived                                                                                                           |
| `mdps_features_full_month_benchmark_binance_2026_06_28.md`  | complete | —         | `status: complete`, un-archived                                                                                                           |
| `tradfi_mdps_passthrough_dependency_gap_2026_06_28.md`      | complete | —         | `status: complete`, un-archived                                                                                                           |
| `solana_defi_legacy_migration_2026_05_27.md`                | active   | 0/31      | Functionally complete (0 open todos); frontmatter stale                                                                                   |
| `mdps_polars_engine_cost_sharpening_2026_06_28.md`          | active   | 0/6       | Functionally complete; summary literally says "Un-defer the M-2 Polars work" — fold completion credit into M-2 Progress Log, then archive |

### Proposed fold/archive/keep mapping (finalize per todos 1-4 before presenting)

| Plan                                                                   | Theme (operator-named)                  | Status / open-done | Proposed disposition                                     | Justification                                                                                                                                                                                                   |
| ---------------------------------------------------------------------- | --------------------------------------- | ------------------ | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`         | bucket-naming                           | active, 14/17      | FOLD → M-1                                               | Legacy-bucket drain + migrate + decommission is data-correctness/backfill-flavor, M-1's core mandate                                                                                                            |
| `data_source_provenance_all_asset_groups_2026_06_01.md`                | data-provenance                         | active, 19/17      | FOLD → M-1                                               | "stamp source... backfill existing objects" is literally M-1's backfill-to-100% scope                                                                                                                           |
| `macro_econ_adapter_scaffolds_2026_06_09.md`                           | macro/micro-econ                        | active, 6/6        | FOLD → M-1                                               | New adapters directly expand captured coverage — M-1's backfill mandate                                                                                                                                         |
| `cefi_manifest_canonicalisation_2026_06_01.md`                         | per-AG canonicalisation (cefi)          | active, 24/55      | FOLD → M-1                                               | Per-AG single-walk v9 canonicalisation IS the backfill-to-100% mandate M-1 already owns                                                                                                                         |
| `tradfi_manifest_canonicalisation_2026_06_01.md`                       | per-AG canonicalisation (tradfi)        | active, 23/37      | FOLD → M-1                                               | Same as cefi row                                                                                                                                                                                                |
| `prediction_manifest_canonicalisation_2026_06_01.md`                   | per-AG canonicalisation (prediction)    | active, 10/59      | FOLD → M-1                                               | Same; near-complete (86%), small residual to migrate                                                                                                                                                            |
| `downstream_services_manifest_canonicalisation_2026_06_01.md`          | per-service canonicalisation            | active, 11/40      | FOLD → M-1                                               | Explicitly "coordinated under the defi_manifest_canonicalisation MASTER" (see next row)                                                                                                                         |
| `defi_manifest_canonicalisation_2026_06_01.md`                         | cefi-universe / cross-plan coordination | active, 23/41      | **JUDGMENT CALL — see todo 5**                           | Self-titled "MASTER: canonical-SSOT for data+manifest, cross-plan coordinator" wrapping tradfi/sports/downstream/cefi/prediction — a SECOND coordinator competing with M-1's role. Do not resolve unilaterally. |
| `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` | (infra/foundation)                      | active, 17/13      | FOLD → M-1                                               | Gates "all v9 manifest --apply runs on Phase 0 completion" — direct prerequisite of M-1's canonicalisation scope                                                                                                |
| `bar_edge_left_vs_right_remediation_2026_06_08.md`                     | (data-correctness, MDPS)                | active, 1/10       | FOLD → M-1                                               | Near-done (1 open); candle-edge data-correctness fix, not tech-debt — M-1 not M-2                                                                                                                               |
| `mdps_features_reduced_artifact_tracker_2026_06_28.md`                 | (cost/coverage tracker)                 | **draft**, 0/0     | ARCHIVE (abandoned stub)                                 | Never finalized/populated (0 todos, still draft — never ingested anyway); if operator wants the stated intent kept alive, add ONE todo under M-2 instead of reviving this file                                  |
| `sports_manifest_canonicalisation_2026_06_01.md`                       | sports vertical                         | active, 2/101      | **KEEP-WITH-JUSTIFICATION** (operator-ruled, see todo 6) | Ruling 175/142/146: "sports_manifest stays mtds_mdps child" — no fold/archive action                                                                                                                            |

## Todos

- [ ] [AUDIT] P0. **Confirm the candidate enumeration is complete** — re-run
      `grep -l "^parent_epic: mtds_mdps_master" plans/active/*.md` and cross-check `^status:` for every hit against the
      tables above; the seed tables were built this session and should be treated as a draft, not final. Gate: explicit
      confirmation the candidate count (13 non-survivor, non-trivially-complete plans) is accurate or a corrected count
      with the delta explained.
- [ ] [AUDIT] P0. **Read each candidate's full body** (not just summary/tags/todo-count) to confirm the proposed theme
      classification and disposition in the mapping table above — flag any candidate whose actual scope diverges from
      its title/summary.
- [ ] [AUDIT] P0. **Verify the plan-hygiene-debt table** — for the 3 `status: complete` files + the 2 functionally-done
      `active` files, confirm zero remaining open work (re-check todo checkboxes + any Progress Log claiming residual
      scope) before treating them as simple-archive.
- [ ] [DESIGN] P0. **Finalize the fold-in/archive/keep mapping table** — incorporate todos 1-3's findings into the seed
      table above; this finalized table is what gets presented to the operator in the HARD GATE below.
- [ ] [DESIGN] P0. **Resolve (as a proposal, not a decision) the `defi_manifest_canonicalisation_2026_06_01.md` judgment
      call** — it is itself a coordinator ("MASTER... cross-plan coordinator") wrapping several of the OTHER candidates
      in this mapping (tradfi/sports/downstream/cefi canonicalisation). Propose either (a) fold its coordination
      content + all its wrapped sub-plan references into M-1, treating M-1 as the sole surviving coordinator, or (b) the
      reverse. State a recommendation but do not execute either — this is exactly the kind of call the HARD GATE below
      exists for.
- [ ] [AUDIT] P0. **Confirm `sports_manifest_canonicalisation_2026_06_01.md` disposition** = KEEP-WITH-JUSTIFICATION per
      operator ruling 175/142/146 (`plan_reconciliation_operator_decisions_2026_07_11.md` §A2: "sports_manifest stays
      mtds_mdps child, sports_master wording fixed"). No fold/archive action on this plan. The ruling's paired
      "sports_master wording fixed" item is a `sports_master` epic-body edit — out of this plan's scope; file a one-line
      pointer todo in `sports_master`'s own tracking (or the reconciliation issue doc) rather than executing it here.
- [ ] [BLOCKED-OPERATOR-DECISION] P0. **HARD GATE — present the finalized mapping table to the operator for approval**
      using the structured-options escalation format (`SUB_AGENT_MANDATORY_RULES.md` § "When escalating a question" —
      minimum 2 options, recommendation marked explicitly, "Other" free-text). **Do NOT execute any fold-in, archive, or
      the todo-5 judgment call until the operator responds.** This todo blocks every todo below it.
- [ ] [CODE] P1. **Execute approved M-1 fold-ins** (gated on the HARD GATE above) — for each candidate approved for M-1,
      migrate its open todos into `data_completion_to_100_all_ag_2026_06_21.md` with provenance
      (`**MIGRATED     FROM:** <plan>`, matching the epic's existing convention already used for its P2 greeks item),
      then archive the source plan via the 5-step ritual (migrate DEFERRED → banner → codex-alignment check → parent-doc
      update → clear lock).
- [ ] [CODE] P1. **Execute approved M-2 fold-ins** (gated on the HARD GATE above) — same migration + archival ritual for
      candidates approved for M-2 (e.g. `mdps_polars_engine_cost_sharpening_2026_06_28.md`, whose own summary says it
      "un-defers the M-2 Polars work" — fold its completion credit into M-2's Progress Log before archiving).
- [ ] [CODE] P1. **Archive the plan-hygiene-debt candidates** (gated on the HARD GATE above, though these are low-risk)
      — the 3 `status: complete` files + the 2 functionally-done `active` files, 5-step ritual, no fold needed (nothing
      open to migrate).
- [ ] [CODE] P1. **Execute the operator's ruling on the todo-5 judgment call** exactly as approved — do not improvise
      beyond the approved mapping if the operator's answer differs from either proposed option.
- [ ] [DOCS] P1. **Update `plans/epics/mtds_mdps_master.md`** banner + `related:`/`related_plans:` frontmatter to
      reflect the post-execution state — remove archived plans from active-plan references, append a dated note
      recording the consolidation completion with this plan's sha, and reconfirm the "2 survivors" framing is now
      actually true (no orphaned `parent_epic: mtds_mdps_master` plans left outside M-1/M-2/the operator-kept
      exception).
- [ ] [DOCS] P1. **Post-phase codex-alignment check** — grep `codex/` for stale references to any folded/archived plan
      name from this mapping; update or SUPERSEDED-banner as needed.
- [ ] [DOCS] P2. **Wire the executed mapping into the reconciliation issue doc** — append a dated Progress Log entry to
      `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 citing findings 175/142/146 and
      this plan's final mapping + execution shas.

## Progress Log

- **2026-07-12** — Plan authored per operator ruling 2026-07-12 (findings 175/142/146,
  `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2: "ENFORCE 2 survivors... fold-in/
  archive mapping authored as HUMAN plan for operator approval; sports_manifest stays mtds_mdps child, sports_master
  wording fixed"). Candidate enumeration + seed mapping table drafted this session via
  `grep -l "^parent_epic: mtds_mdps_master" plans/active/*.md` cross-checked against `status:`/todo-counts/summaries; 13
  non-survivor active/draft/paused candidates + 5 plan-hygiene-debt (functionally-done, un-archived) files found. No
  fold/archive action executed — this plan's own HARD GATE todo blocks execution until operator approval.
