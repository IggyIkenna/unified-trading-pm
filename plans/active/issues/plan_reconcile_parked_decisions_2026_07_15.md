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
status: open
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
resolved_by:
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
> (21% kill-rate). Auto-fix classes applied + committed separately. **Nothing below was applied** — each item is a
> judgment call parked per the skill's autonomous contract.

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

- **A: Flip `p1_dualwrite:9` `status: draft` → `active` (truth-telling; the work already happened) and tick the P0
  gating todo. [WORKER REC]**
- **B:** Leave draft; fold the one open todo into `deployment_registry_firestore_p0_unblock_2026_07_14.md` and archive
  the P1 shell (see §6 — the near-complete analyzer independently recommends this same fold target).
- **C:** Leave as-is (intentionally parked pending the fleet dual-write decision).
- **Other:** operator free-text.

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

## Answering

Reply per-section (`§1: A`, `§6: A except layer1_remeasure → B`, …). Ruled items are applied on the next
`/plan-reconcile` pass. §2 (CLAUDE.md) and §7 (`[unlock-plan]`) are the two blocking on your word specifically — the
rest have safe defaults.
