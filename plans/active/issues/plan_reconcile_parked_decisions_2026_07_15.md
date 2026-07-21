---
doc_type: issue
title:
  Plan-reconcile 2026-07-15 (autonomous) — parked operator decisions — SSOT/rules corrections, archival unlocks,
  near-complete consolidations, line-cap split
summary:
  Output of an autonomous /plan-reconcile sweep over the full plans corpus (445 docs; 158 hunt agents; 484 agents total
  incl. adversarial verification). Auto-fix classes were applied and committed separately. This doc parks every judgment
  call the autonomous contract forbids an agent from making alone — normative/SSOT rule edits, archiving locked plans,
  where near-complete remnants fold, a cross-repo code defect, and a hard line-cap split — each with options and a
  marked worker recommendation for an asynchronous operator ruling.
status: resolved
resolved_by:
  "All sections ruled + applied 2026-07-15 in-session — §1 99331e940 · §2 2235cd79c · §4 deployment-ui@0bcd098 · §6
  93cb228c5+98e8fd5ba · §7 ed58dd108+a9ca22690 · §8 d59b100b0 · §9 451a89e7c · §10 5bce62fc0. §3 self-resolved via the
  §6 ruling. Corpus 143->100 active, 0 orphans, 0 files over the 5000-line ceiling, hygiene 0 hard failures."
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, deployment-ui, market-tick-data-service]
scope: [engineer, admin]
tags: [plan-reconcile, contradictions, done-but-unchecked, archival, consolidation, line-cap, ssot, operator-decision]
related:
  [
    plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md,
    plans/active/data_completion_to_100_all_ag_2026_06_21.md,
  ]
created: 2026-07-15
parent_epic: plan_hygiene_master
priority: P1
source: [autonomous /plan-reconcile run 2026-07-15 (main session, Opus 4.8 1M)]
assigned_vm: NA
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-15
locked_since:
---

# Plan-reconcile 2026-07-15 — parked operator decisions

> **Provenance.** Autonomous `/plan-reconcile` over `plans/{active,active/issues,epics}` — 445 docs, 15 MB, 1852 open /
> 3236 done checkboxes. 158 hunt agents (81 epic-cluster + 16 topic + 23 done-but-unchecked + 2 mechanical + 20
> fully-done archival verifiers + 16 near-complete analyzers); 484 agents total including adversarial
> refuter/confirmer/tiebreaker verification. **82 raw contradictions + 45 raw flips → 61 + 39 CONFIRMED, 27 REFUTED**
> (21% kill-rate). Auto-fix classes applied + committed separately. Everything below was parked as a judgment call per
> the skill's autonomous contract.

> **✅ ALL SECTIONS RULED + APPLIED 2026-07-15 (same session). This doc is CLOSED — nothing is awaiting an operator.**
>
> | §             | Ruling                           | Applied                                                                                                                  |
> | ------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
> | §1 CeFi       | A — record NON-DURABLE + re-open | `99331e940` — reclass recorded non-durable (66,007→112,727 af); capture defect re-opened as [DATA] P0 on the blocker doc |
> | §2 CLAUDE.md  | A — edit the rule                | `2235cd79c` — Polygon.io→Massive corrected; chain-vs-vendor trap documented                                              |
> | §3            | (self-resolved via §6, option B) | `93cb228c5` + `98e8fd5ba`                                                                                                |
> | §4 UI staging | A — fix the UI properly          | `deployment-ui@0bcd098` — PromotionPipeline derives from ldr_main; pw:L2 spec PROVEN to catch the bug                    |
> | §6 folds      | A — approve the whole table      | `93cb228c5` (14 folded + 2 flipped) → `98e8fd5ba` (13 shells archived)                                                   |
> | §7 unlock 14  | A — unlock + verify              | `ed58dd108` (6) → `a9ca22690` (19 incl. codex-sync). 1 KEEP_ACTIVE correctly held                                        |
> | §8 line-cap   | A — split by asset_group         | `d59b100b0` — M-1 5,366→4,121; 4 children; corpus at ZERO files over 5,000                                               |
> | §9 ledger     | A — drop the number              | `451a89e7c` — AST-verified 39 at HEAD; count removed from both sites                                                     |
> | §10 skips     | A — triage per-item              | `5bce62fc0` — F43 reconciled; populator's 2 silent bugs fixed + DO-NOT-APPLY warned; 5 of 10 needed no action            |
>
> **Corpus effect: 143 → 100 active plans; 0 orphans; 0 files over the 5,000-line ceiling; hygiene 0 hard failures.**
>
> Everything below is the ORIGINAL parked text, kept as the record of what was asked and why. Sections retain their
> options for provenance — do not re-answer them.

> **🟢 (superseded by the block above) OPERATOR RULED 2026-07-15 — §2, §6, §7 answered and APPLIED.**
>
> | §                            | Ruling                    | Applied                                                                                                                 |
> | ---------------------------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
> | **§2** CLAUDE.md Polygon.io  | **A** — edit CLAUDE.md    | ✅ `2235cd79c` — verified against live UAC (`possible_manifest.py:217`, `canonical_mappings.py:124/456`) before editing |
> | **§6** fold 16 near-complete | **A** — approve the table | ✅ `93cb228c5` (14 folded verbatim + 2 flipped) → `98e8fd5ba` (13 shells archived; 3 parked, codex-referenced)          |
> | **§7** unlock 14 fully-done  | **A** — unlock + verify   | ✅ `ed58dd108` — 14/14 verified: 13 SAFE_TO_ARCHIVE, **1 KEEP_ACTIVE**; 6 archived, 7 blocked on a repoint pass         |
>
> **Corpus effect: 143 → 117 active plans.** Still open below: **§1** (CeFi reclass non-durable), ~~**§3**~~
> (`p1_dualwrite` draft — RESOLVED by the §6 ruling, option B), **§4** (deployment-ui staging stage), **§8** (the
> 5358-line split), plus the residual archival blockers recorded in §5b/§7-residual.

## §1 — P1 DATA-CORRECTNESS: CeFi `futures_chain` reclass is NON-DURABLE (big finding)

**Docs:** `plans/active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md` (~L61-67) ↔
`plans/active/issues/deribit_options_chain_af_g4_blocker_2026_07_03.md`

The bundle-verification plan asserts (citing `mvp_backfill_cefi_tick_v10:869-874`) that CeFi `futures_chain`
`attempted_failed` cells were reclassified to `empty_confirmed` as a settled state. The blocker issue doc shows the
66,007-cell reclass was **immediately re-populated as `attempted_failed`** — i.e. the reclass is non-durable and the
plan's "settled" framing is false. Per the data-pipeline-correctness HARD RULE this is a heartbeat finding, not
bookkeeping.

- **A: Correct the bundle plan to record the reclass as NON-DURABLE + re-open the underlying capture defect as the live
  item, owned by the blocker issue doc. [WORKER REC]** — restores an honest manifest story; the blocker doc already owns
  the root cause.
- **B:** Treat the re-population as expected churn; annotate both docs and leave the classification as-is.
- **C:** Escalate to a dedicated data-correctness plan (foundation-gate implications for layer N+1).
- **Other:** operator free-text.

## §2 — P1 NORMATIVE RULE IS WRONG: CLAUDE.md calls Polygon.io a removed provider, but it is re-adopted as Massive

**Docs:** `cursor-configs/CLAUDE.md:291` ↔ `plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md:281`

CLAUDE.md's conditional DeFi/provider index states:
`removed providers (Elysium/Arkham/Bloxroute/Infura/Kaiko/Polygon.io) — do NOT reference`. The 2026-06-05 audit
documents that Polygon.io **rebranded to Massive** and was **deliberately re-adopted** as Databento's secondary TradFi
source (`SOURCE_PRIORITY` includes `massive`; see `plans/active/tradfi_massive_dual_source_2026_05_28.md`). The rule
file is therefore actively mis-routing every agent that reads it.

> Verified: workspace-root `CLAUDE.md` is a SYMLINK to `cursor-configs/CLAUDE.md` — one edit, not two.

**Why parked (not auto-fixed):** the skill's HARD GATE — a normative/SSOT rule edit is never applied from an agent's own
judgment, however strong the evidence. This one needs your word.

- **A: Edit CLAUDE.md:291 — drop Polygon.io from the removed list and note "Polygon.io → rebranded Massive, re-adopted
  as the secondary TradFi source (see `codex/02-data/tradfi-databento-sourcing-ssot.md`)". [WORKER REC]** — smallest
  edit that stops the mis-routing; keeps the rule one-line per CLAUDE.md's format.
- **B:** Keep CLAUDE.md as-is and instead correct the codex SSOT + let the conditional index point there.
- **C:** Leave both; treat "Polygon.io" (the old brand) as genuinely removed and "Massive" as a distinct, allowed
  provider — no doc change.
- **Other:** operator free-text.

## §3 — P1 dispatch-affecting: `deployment_registry_firestore_p1_dualwrite` stuck at `status: draft`

**Docs:** `plans/active/deployment_registry_firestore_migration_2026_07_14.md` ↔
`plans/archive/2026_07/deployment_registry_firestore_p1_dualwrite_2026_07_14.md:9`

P1's frontmatter is still `status: draft` (never flipped to `active`) although 6/7 of its todos have shipped; the P0
plan's own draft-gating todo (to flip P1 active) was never executed. `draft` = NOT ingested by the orchestrator, so the
plan is invisible to dispatch despite being live work.

**Why parked:** flipping `draft → active` changes what the AO ingests and dispatches — a live-routing change, not
bookkeeping.

> **🟢 RESOLVED 2026-07-15 by the §6 ruling — option B, no separate answer needed.** The operator's §6 approval covered
> `deployment_registry_firestore_p1_dualwrite → deployment_registry_firestore_p0_unblock_2026_07_14.md`, which IS option
> B below. Applied: remnant folded (`93cb228c5`), shell reached zero open todos, archived to `plans/archive/2026_07/` as
> `status: complete` (`98e8fd5ba`). The dispatch-invisibility is therefore gone — the live work is now tracked in
> P0_unblock, which is `status: active` and ingested. Nothing further to rule here.

- **A: Flip `p1_dualwrite:9` `status: draft` → `active` (truth-telling; the work already happened) and tick the P0
  gating todo. [WORKER REC — superseded]**
- **B: ✅ TAKEN (via §6):** fold the one open todo into `deployment_registry_firestore_p0_unblock_2026_07_14.md` and
  archive the P1 shell.
- **C:** Leave as-is (intentionally parked pending the fleet dual-write decision).

## §4 — P2 cross-repo CODE defect: deployment-ui hard-codes a `staging` promotion stage

**Docs:** `plans/active/monitoring_control_plane_master_2026_06_10.md` ↔
`plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` · **Code:** `deployment-ui/src/pages/RepoCi.tsx` L1432-1490

The shipped deployment-ui "promotion-pipeline strip" hard-codes 5 stages including `staging`, but the fleet default is
**LDR→`main` DIRECT, staging BYPASSED** (per-repo `ldr_main` toggle). The verifier's judgement: _"the plan text is a
symptom; the live UI is the defect."_ Out of scope for a doc-only reconcile → routed to you.

- **A: Make `PromotionPipeline` derive its stages from the repo's `ldr_main` toggle (a `[UI]` change → needs `pw:L2` + a
  regression spec), and correct the plan text. [WORKER REC]**
- **B:** Doc-only: annotate the plan as superseded by the direct-promote model; leave the UI (accepting a misleading
  strip).
- **C:** File a standalone deployment-ui plan and leave both docs annotated.
- **Other:** operator free-text.

## §5 — Fully-done plans: archival needs your call

The sweep verified all 20 unlocked all-boxes-ticked plans (each: spot-check the `[x]` evidence + hunt for open work
described in **prose** rather than checkboxes). **17 cleared SAFE_TO_ARCHIVE; 3 did not.** Of the 17, only **7 were
actually archived** (`unified-trading-pm@c2c1d9457`) — the other **10 are parked in §5b below**, because archiving them
is not autonomous-safe.

The 3 that did **not** clear the bar (left active — this is exactly why verification beats trusting the boxes):

| Plan                                               | Verdict            | Why                                                                                                                                                                                                                                                                                                                                                 |
| -------------------------------------------------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `data_pipeline_e2e_check_2026_07_10`               | **NEEDS_OPERATOR** | All 30 todos `[x]` w/ strong evidence, but the Progress Log (through 2026-07-14) carries live open threads: DEFI consolidator SIGKILL, TradFi Databento silent-zero-rows, W1/G4 forensics chain. Handed off to `issues/*` docs, or still in-scope here? Also: todo #24 is absent from the file with no explanation.                                 |
| `execution_fidelity_tiers_uac_governed_2026_06_28` | **NEEDS_OPERATOR** | All 5 todos `[x]` + commits verified reachable, BUT a `[⚠️ CORRECTED 2026-07-14]` note says todo 3 (`execution-service@42956add`) DID change the live matching-engine's book-type selection and "should get the standard live-safety review if it hasn't already". No such review doc exists. **Live-trading-path change with an open safety gap.** |
| `gcs_bucket_estate_cleanup_2026_07_10`             | **KEEP_ACTIVE**    | Not archivable: was already falsely marked `complete` once and flipped back to `active` on 2026-07-14 (§5j finding 78). Named next action never executed (`lending-indices` + `-prd` confirm-then-delete). Left untouched — correctly still live.                                                                                                   |

- **A: Archive `data_pipeline_e2e_check` (residual threads genuinely live on their own issue docs) + hold
  `execution_fidelity_tiers` until the live-safety review is done. [WORKER REC]**
- **B:** Hold both until you confirm each hand-off boundary.
- **C:** Archive both now; accept the open threads live elsewhere.
- **Other:** operator free-text.

> **Independent P1 spun out of §5:** `execution_fidelity_tiers` flags an **unreviewed live matching-engine change**
> (`execution-service@42956add`). Regardless of the archival ruling, that review either happened and is unrecorded, or
> it never happened. Worth its own answer.

> **🟢 §5 RULED 2026-07-21 (operator, via `/plan-reconcile`)**: the live-safety review of `execution-service@42956add`
> DID happen, just wasn't documented at the time. `execution_fidelity_tiers_uac_governed_2026_06_28.md` is now archived
> (`plans/archive/2026_07/`) with the confirmation cited inline. Note: a separate, INTERVENING audit
> (`canonical_closeout_open_questions_2026_07_18.md` §C5) had already listed this plan as "archival-ready" without ever
> surfacing this open question — a near-miss this table's own existence prevented from becoming a silent skip.
> `data_pipeline_e2e_check_2026_07_10` — separately confirmed independently-verified/archived by this same
> `/plan-reconcile` run (its residual threads live on their own issue docs, per WORKER REC option A above).

### §5b — 10 verified-done plans NOT archived: archival is blocked, not skipped

All 10 are verified SAFE_TO_ARCHIVE. Archiving them is blocked on a **ref-graph coupling nobody had surfaced**: the
corpus holds **95 inbound mentions / 69 path-refs** to the 17 cleared plans. A naive `git mv` would have snapped 69
links — the classic rule-11 "green where I looked, broke the fleet" regression. The 7 archived were exactly those with
zero inbound refs or a single ref in a LIVE doc (repointed in the same commit).

**Group A — referenced from `codex/` SSOT docs → archiving requires a plans→codex edit (never autonomous):**

| Plan                                                   | codex doc referencing it                                                           |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `foundation_gates_and_capture_to_100_2026_07_06`       | `codex/02-data/defi-completeness-oracle.md`                                        |
| `honest_coverage_smoke_harness_2026_06_28`             | `codex/02-data/shard-coverage-classification.md` — calls it **"Plan (in-flight)"** |
| `global_ledger_epic_reaudit_2026_07_12`                | `codex/04-architecture/global-ledger-architecture.md`                              |
| `deployment_registry_firestore_p4_dynamodb_2026_07_14` | `codex/05-infrastructure/*`                                                        |

Note the second row: codex asserts a plan is _in-flight_ that is verified **done**. That is live plan↔codex drift
(review-blocking per CLAUDE.md) independent of archival.

**Group B — inbound refs live in HISTORICAL records → rewriting them would falsify a past audit:**

`canonical_id_p0_ccxt_live_batch_divergence_2026_07_08` (15 refs) · `canonical_id_p0_strategy_reconciliation_2026_07_08`
(8) · `is_catalogue_completion_2d_2026_07_06` (7) · `deployment_observability_expansion_2026_07_08` (4) ·
`features_read_book_columns_not_snapshots_2026_06_28` (3) · `canonical_id_p0_defi_adapter_type_filter_bug_2026_07_08`
(2)

Their refs sit largely in `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` and
`plans/audit/results/` — where a ref like `active/foo.md:146` is a **point-in-time citation of where a finding was**,
not a live link. The worker deliberately did not rewrite these.

- **A: Archive all 10 — repoint the 4 codex refs (and fix the "in-flight" wording), and leave historical-record
  citations untouched as point-in-time (accepting they name an `active/` path that no longer exists). [WORKER REC]** —
  matches how the corpus already annotates archived refs ("path never existed under active/ post-archival").
- **B:** Archive Group B only (6); hold Group A until the codex sync is ruled on separately.
- **C:** Archive none; keep all 10 in `plans/active/` until a dedicated archival+codex-sync pass.
- **Other:** operator free-text.

## §6 — Near-complete plans (≤1 open todo): fold destination needs a ruling

Per the skill, **where live work lives is a planning decision** — the worker never auto-folds. Each remnant below has a
verified fold target recommended by an analyzer that read the candidate siblings.

| Plan (1 open todo)                                            | Lock     | Recommended fold target                                                                                                  |
| ------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------ |
| `bybit_futures_chain_write_shape_migration_2026_07_13`        | LOCKED   | `data_completion_to_100_all_ag_2026_06_21.md` (M-1; 2-survivor consolidation ruling)                                     |
| `canonical_id_p0_kraken_futures_collision_2026_07_08`         | unlocked | `canonical_id_builder_retrofit_checklist_2026_07_08.md` (remnant is a NEW `FI_`/`FF_` schema-grain issue)                |
| `canonical_instrument_id_cefi_defi_backfill_2026_07_14`       | unlocked | `plans/epics/instruments_master.md` (remnant = post-phase codex audit)                                                   |
| `ci_failures_channel_cleanup_2026_07_13`                      | unlocked | `plans/epics/observability_master.md` (remnant = post-rollout volume re-check)                                           |
| `deployment_obs_backend_kinds_health_2026_07_09`              | unlocked | `deployment_observability_expansion_2026_07_08.md` (LIVE/PAPER `stalled` needs 2 new subsystems)                         |
| `deployment_registry_firestore_p1_dualwrite_2026_07_14`       | unlocked | `deployment_registry_firestore_p0_unblock_2026_07_14.md` (sibling already carries the twin item) — **interacts with §3** |
| `honest_coverage_v2_instrument_denominator_2026_06_28`        | LOCKED   | `instruments_completion_tracker_2026_07_06.md` (ratifies a move already recorded in-plan 2026-06-28/07-06)               |
| `layer1_remeasure_and_certify_2026_07_06`                     | unlocked | `tradfi_v9_stage1_finish_2026_07_06.md` (remnant intrinsically blocked on Plan 2 tasks 2-11)                             |
| `mvp_backfill_cefi_tick_v10_2026_06_27`                       | LOCKED   | `cefi_completion_program_2026_07_15.md` (same-day coordinator created by a completion audit of this very plan)           |
| `predictions_lookahead_and_reader_migration_2026_06_20`       | LOCKED   | `plans/epics/predictions_master.md`                                                                                      |
| `scripts_lifecycle_marker_rollout_2026_06_18`                 | LOCKED   | `repo_scripts_governance_audit_2026_06_18.md` (sibling carries a near-duplicate open todo)                               |
| `sports_fixtures_schema_split_completion_2026_06_20`          | LOCKED   | `sports_p2_features_history_to_ml_ready_2026_06_27.md`                                                                   |
| `sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27` | LOCKED   | `sports_p2_history_apifootball_2015_to_present_2026_06_27.md` (its 4 named prereqs live there)                           |
| `utl_reuse_phase8_codex_ssot_archive_2026_07_13`              | LOCKED   | `plans/epics/infrastructure_master.md` (no sibling owns hygiene/archival closeout)                                       |

- **A: Approve the whole table — fold each remnant into its recommended target, then archive the emptied shells. [WORKER
  REC]** — every target was justified against the sibling's actual scope.
- **B:** Approve per-row (reply with exceptions); worker applies the rest.
- **C:** Fold none — keep the shells as standalone trackers.
- **Other:** operator free-text.

### §6b — Two "near-complete" remnants are actually already shipped (flip, not fold)

Both are LOCKED and were surfaced by the analyzer, **not** by the adversarially-verified flip sweep — so they are
**recommended, not verified**. They need either your ruling or a verified re-check next pass.

- `instruments_catalogue_incremental_rollup_2026_06_29` — the todo's own stated condition to stay open ("unless the
  catalogue goes stale again BEFORE Phase 3 lands") is spent: Phase 3 landed.
- `understat_local_backfill_completion_2026_07_06` — superseded by a larger dedup fix already shipped + re-verified
  in-plan (`instruments-service@2f56038e`, 683,592 mislabeled dup rows dropped).

- **A: Verify both against the HARD-evidence bar next pass, then flip. [WORKER REC]**
- **B:** Flip both now on the analyzer's evidence.
- **C:** Leave open.

## §7 — Archiving LOCKED fully-done plans needs `[unlock-plan]`

14 plans have **every todo `[x]`** but carry `locked_by: live-defi-rollout`. Per CLAUDE.md, `locked_by:` blocks archival
without `[unlock-plan]` — **ASK, never autonomous**. They are otherwise identical to the 17 already archived.

`aster_cefi_data_defi_bucket_migration_2026_07_13` · `coinbase_bare_name_migration_2026_07_06` ·
`mvp_catalogue_finalization_v10_2026_06_27` · `mvp_reconciliation_closeout_v10_2026_06_27` ·
`sports_odds_bookmaker_coverage_enumeration_2026_06_20` · `utl_reuse_phase0_guardrails_2026_07_13` ·
`utl_reuse_phase1_strategy_risk_hwm_2026_07_13` · `utl_reuse_phase2_api_auth_dedup_2026_07_13` ·
`utl_reuse_phase3_ml_model_registry_2026_07_13` · `utl_reuse_phase4_features_builder_registry_2026_07_13` ·
`utl_reuse_phase5_deployment_api_cloud_sdk_2026_07_13` · `utl_reuse_phase6_venue_health_retry_2026_07_13` ·
`utl_reuse_phase7_low_lint_tail_2026_07_13` · `utl_reuse_phase9_deployment_registry_extract_2026_07_13`

> Note: 9 of the 14 are the `utl_reuse_phase*` chain — likely intended to archive together once phase 8 (§6, the
> closeout phase) completes.

- **A: `[unlock-plan]` the 14 → worker verifies each to the same bar as the 17 (spot-check evidence + no open prose
  work), archives those that clear, reports any that don't. [WORKER REC]**
- **B:** `[unlock-plan]` only the non-`utl_reuse_*` 5; hold the phase chain until phase 8 lands.
- **C:** Hold all 14 (locks are deliberate).
- **Other:** operator free-text.

## §8 — Line-cap: one file breaches the absolute 5000-line ceiling

Per the line-cap rule (ratified by operator 2026-07-15): long-lived **master plans + epics are exempt** from the
500/1000 caps, but a **strict 5000-line ceiling applies to ANY file, no exemption**.

**Corpus scan result: exactly one breach.**

| File                                                       | Lines    | Verdict                                     |
| ---------------------------------------------------------- | -------- | ------------------------------------------- |
| `plans/active/data_completion_to_100_all_ag_2026_06_21.md` | **5358** | **BREACH** — over the absolute 5000 ceiling |

Everything else over 1000 (20 files: `sports_manifest_canonicalisation` 4145, `sports_data_sources_canonical_completion`
3777, `master_to_live_defi_2026_05_23` 2263, …) is a long-lived master/living-inventory plan → **exempt, no action**.
Splitting a plan is a planning decision → parked.

M-1 (`data_completion_to_100_all_ag`) is the consolidation survivor that absorbed 130 folded-in todos on 2026-07-13,
which is why it grew past the ceiling. It has 160 open / 171 done todos.

- **A: Split M-1 by asset_group into child plans under `manifest_master`, keeping M-1 as the thin coordinator hub.
  [WORKER REC]** — preserves the 2-survivor consolidation intent while getting under the ceiling.
- **B:** Split by the "Folded-in scope 2026-07-13" boundary (pre-fold core vs folded-in scope).
- **C:** Raise M-1's exemption to master-plan status and accept >5000 (rejects the ceiling you just set).
- **Other:** operator free-text.

## §7-residual — 7 verified-done plans still blocked from archival (after the §7 ruling)

The §7 [unlock-plan] ruling was applied: all 14 were verified, 6 archived (`ed58dd108`). These 7 are **verified
SAFE_TO_ARCHIVE** but their blast radius is not autonomous-safe — archiving them needs a deliberate repoint pass:

| Plan                                                   | Blocker                                                                                                                                     |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `utl_reuse_phase1_strategy_risk_hwm_2026_07_13`        | 1 codex SSOT ref → plans→codex edit (never autonomous)                                                                                      |
| `utl_reuse_phase5_deployment_api_cloud_sdk_2026_07_13` | 1 codex SSOT ref                                                                                                                            |
| `utl_reuse_phase6_venue_health_retry_2026_07_13`       | 1 codex SSOT ref                                                                                                                            |
| `aster_cefi_data_defi_bucket_migration_2026_07_13`     | 14 live refs, mixed live + historical                                                                                                       |
| `coinbase_bare_name_migration_2026_07_06`              | **live functional `depends_on`** from the draft follow-on `coinbase_bare_name_migration_execution_service_2026_07_10` — not a cosmetic link |
| `mvp_reconciliation_closeout_v10_2026_06_27`           | 5 live refs                                                                                                                                 |
| `utl_reuse_phase7_low_lint_tail_2026_07_13`            | 4 live refs, mixed                                                                                                                          |

Plus the 3 §6 shells parked for the same reason (codex-referenced, remnants already folded out, zero open todos):
`honest_coverage_v2_instrument_denominator_2026_06_28` · `instruments_catalogue_incremental_rollup_2026_06_29` ·
`scripts_lifecycle_marker_rollout_2026_06_18`.

**And one KEEP_ACTIVE (correctly not archived):** `sports_odds_bookmaker_coverage_enumeration_2026_06_20` — all 3 boxes
`[x]` with all 3 shas verified reachable, but the body carries extensive unresolved open work never converted to
checkboxes. The 4th false-done plan this run caught.

- **A: One dedicated archival+codex-sync pass — repoint the codex refs, resolve the coinbase `depends_on`, leave
  historical citations untouched, archive all 10. [WORKER REC]**
- **B:** Archive only the 4 non-codex ones (aster_cefi, coinbase, mvp_reconciliation_closeout, utl_reuse_phase7) after
  resolving the coinbase dependency; hold the codex-referenced 6.
- **C:** Leave all 10 active — they are inert (zero open todos) and harmless where they are.

## §9 — P2: `carry_staked` says the ledger EventType closed-set is 37; the re-audit AST-counted 39

> **Filed late (2026-07-15).** This was the 4th operator-gated contradiction and was MISSED from the first cut of this
> doc — recorded here rather than silently dropped.

**Docs:** `plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md:212` (and again `:250`) ↔
`plans/active/global_ledger_epic_reaudit_2026_07_12.md:214`

- A: _"Ledger taxonomy = UAC `canonical.crosscutting.ledger` (37 EventTypes incl DEPOSIT/WITHDRAWAL_TO_BANK/…)"_
- B: _"`EventType` = **39** at HEAD `a2751f36` (AST-counted), not 37 (`+2` via `dc67ae6f` margin-traceability,
  additive)."_

The carry plan asserts 37 as an unqualified current fact, twice, in a **funds-isolation-adjacent** design context.
Authoritative side is **B** (AST-verified at HEAD, dated later, `status: complete`).

- **A: Drop the number — say "the UAC `canonical.crosscutting.ledger` EventType closed set" with no count, so it cannot
  re-stale on the next enum bump. [WORKER REC]** — the count is derivable from UAC; hardcoding it in prose is the bug.
- **B:** Write "39 EventTypes (37 base + 2 margin-traceability via `dc67ae6f`)" at both sites — accurate today,
  re-stales on the next bump.
- **C:** Leave it as a point-in-time note.

## §10 — 10 contradiction fixes the writer-agents SKIPPED (not applied, not previously surfaced)

Phase 5b applied 55 and **skipped 10**. The count was reported; the items were not. Surfacing them now — several are
genuine rulings, not noise. **None were applied.**

| #   | Doc                                                        | Skipped because                                                                                                                                                        |
| --- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `epics/instruments_master.md`                              | Roster says "3 active plans"; 15 declare this `parent_epic`. Regenerating it is a restructure, not a fix — needs `populate_epic_bodies` or an operator-directed regen. |
| 2   | `issues/phantom_captures_tradfi_2026_06_28.md`             | The recommended_fix text was **truncated mid-sentence** in my bundle — the agent refused to guess. (My bundling bug, not the agent's.)                                 |
| 3   | `pipeline_mode_partition_migration_2026_06_01.md`          | Re-verified as a **non-finding** at apply-time — line 49 already has the correct canonical hive key order.                                                             |
| 4   | `honest_coverage_smoke_harness_2026_06_28.md`              | **Operator-gated**: flipping `status: active → complete` conflicts with the doc's own newer 2026-07-14 annotation (finding 22). Also codex-referenced (see §5b).       |
| 5   | `epics/manifest_master.md`                                 | Placing `mtds_available_at_cross_asset_backfill` into a P0/P1/P2/P3 tier is a **planning decision**, not a count fix.                                                  |
| 6   | `epics/mtds_mdps_master.md`                                | Part 2 of the fix targeted a **second file** — outside the one-file-per-agent scope. Needs a follow-up pass.                                                           |
| 7   | `issues/capability_wizard_analysis_findings_2026_06_11.md` | The mirrored F43 flip lives in a **different file** (`capability_wizard_gap_discovery`) — out of scope.                                                                |
| 8   | `issues/capability_wizard_analysis_findings_2026_06_11.md` | Two further in-file "F43 = OPEN" mentions weren't named by the confirmed fix; one sits **inside a table** (fragile).                                                   |
| 9   | `issues/tradfi_unreachable_databento_..._2026_07_15.md`    | The stale `1186/1186, 100.0%` clause sits inside a **large quoted YAML scalar** — a surgical edit risked breaking the frontmatter.                                     |
| 10  | `issues/macro_micro_econ_data_capture_audit_2026_06_05.md` | **The recommended fix is unsafe** — doc_b contains a _later reversal_ of the very correction being applied. Applying it would have re-introduced a stale claim.        |

- **A: Action 4/5/6/7/8 as a small follow-up pass (the real ones); close 3 and 10 as refuted-at-apply-time; re-run 2 and
  9 with the fix-text intact and a YAML-safe editor. [WORKER REC]**
- **B:** Fold all 10 into the next `/plan-reconcile` run's candidate set.
- **C:** Accept as-is — none are correctness-critical.

## Answering

Reply per-section (`§1: A`, `§4: B`, …). **§2, §6, §7 were ruled + applied on 2026-07-15**; **§3** self-resolved via §6.
Still open: **§1** (CeFi reclass non-durable — data-correctness), **§4** (deployment-ui staging stage), **§8**
(5358-line split), **§7-residual** (10 verified-done plans blocked on a repoint/codex-sync pass), **§9** (ledger
EventType count), **§10** (the 10 skipped fixes).
