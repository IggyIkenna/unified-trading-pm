---
doc_type: plan
title:
  Prediction satellite AO batch 6 — post-batch4 residual sweep (capture-incident P0 data bug, arb-bridge, credential
  reshape, VM backfill, RULED fixture-pairing/politics-geo)
summary: >-
  Sixth AO-dispatch batch for prediction, produced by the `/ag-closeout-audit prediction` scheduled run 2026-07-29
  (ag_closeout_auditor, slot 14). Phase 1 classified 22 prediction-primary/dual-legit AG candidate docs (of 61
  `asset_group:[prediction]` members found by `generate_ag_closeout_audit_candidates.py`; 34 excluded as genuinely
  cross-AG per the skill's Phase-0.3 orthogonality filter — dual-tagged with cefi/defi/tradfi/cross-cutting, not
  prediction-primary) via a Workflow fan-out (22 agents, 0 errors): 1 `archivable_after_planned_work`, 1 sports-primary
  `exclude_cross_cutting`, 8 `orphaned_never_touched`, 12 `orphaned_partial_coverage`. Phase 3 conflict-checked every
  orphaned item against the full active covering-plan set (consolidated-closeout + phase_ab/c/d/e +
  native_ao_extract(+finalize) + batch1/1f/2/2f/4/4f) plus archived batch3/3f/5/5f for historical disposition —
  excluded: 2 docs already self-dispatching (`assigned_vm: planning` + `status: open`, confirmed via a live re-read
  mid-audit since this corpus is edited concurrently by many agents), 1 residual already claimed by a DIFFERENT existing
  plan (`code_quick_cross_repo_fix_backlog_2026_07_28.md`, `asset_group:[meta]`), 1 too-large-for-a-batch multi-repo
  migration (`data_completion_prediction_2026_07_15.md`'s Phase-B object-layer CQG-bundle migration — 4× independently
  re-triaged to 0 AO-eligible across batch1/2/3/4, needs its own dedicated plan), 1 not-AO-eligible item that is really
  `ao`-tranche scope (an AO-dispatcher-checkpoint/in-flight-detection design question, not prediction data work), and 4
  genuinely sports-primary docs (confirmed by 3 independent prior audits as "owned by the sports tranche, excluded to
  avoid duplicate dispatch" — not re-drafted here; flagged in the Progress Log for the sports tranche's own sibling
  audit this same dispatch wave). This batch extracts the 9 remaining conflict-clear, bounded, prediction-owned
  AO-eligible source docs — headlined by a **P0 active data-correctness bug**: 79% of daily Kalshi volume has been
  silently mis-bucketing to `canonical_question_group=OTHER` every day since at least 2026-07-12 (17+ days as of this
  audit), root-caused to a one-line write-time bug at `instruments-service/.../prediction.py:95` — plus two items
  `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` already RULED buildable (2026-07-28, lifting a prior
  `BLOCKED-OPERATOR-DECISION` gate) but never actually turned into a dispatched checkbox (a ruling is not a dispatch;
  confirmed batch4's own gated `_finalize` doc does not build them either, so drafting them here is not a duplicate).
  `status: draft` — a skill-drafted AO batch is never auto-shipped; flipping to `active` to dispatch is an operator
  decision (CLAUDE.md "Plan destination — ASK BEFORE CREATING" HARD RULE).
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    strategy-service,
    execution-service,
    features-service,
    deployment-service,
  ]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-6, satellite-docs, data-correctness]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /plans/active/prediction_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/active/issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md,
    /plans/active/issues/kalshi_mass_attempted_failed_unclassified_adapter_error_2026_07_27.md,
    /plans/active/issues/prediction_arb_live_execution_bridge_2026_07_20.md,
    /plans/active/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md,
    /plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-29"
last_updated: "2026-07-29"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit prediction scheduled run 2026-07-29 (ag_closeout_auditor, slot 14, dispatch agt-17d52d). Phase 0
  discovered the covering-plan set (13 active docs + 4 archived batch3/5+finalize pairs); Phase 1 classified 22
  prediction-tranche candidate docs via Workflow `wf_6e35eef8-57b` (22 agents, 0 errors, ~2.92M subagent tokens, 386
  tool calls, ~20min wall-clock). Phase 3 conflict-checked every orphaned item against the full covering-plan set — see
  Progress Log for the per-item disposition trail (self-dispatching / claimed-elsewhere / too-large / sports-owned /
  genuine-gap).
assigned_role: data_engineering
drift_direction: advance-code
---

# Prediction satellite AO batch 6 — post-batch4 residual sweep

> **Machine-dispatchable only once flipped `status: active` by the operator** (CLAUDE.md "Plan destination — ASK BEFORE
> CREATING"). Paired with
> [`prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md`](/plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md)
> (`depends_on: [prediction_satellite_ao_dispatch_batch6_2026_07_29]`, `gate_on_depends: true`, also `status: draft`).

## Why this batch exists

`/ag-closeout-audit prediction` (this run, 2026-07-29) re-classified every prediction-primary candidate doc not already
inside the active covering-plan set. 20 of 22 audited docs came back `orphaned_*`. Applying the shared conflict-check
protocol (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) narrowed that to **9 source
docs carrying genuine, conflict-clear, bounded AO-eligible work** — see the Progress Log for why each of the other 11
was excluded (already self-dispatching, claimed by a different plan, too large for a batch todo, not AO-eligible, or
sports-tranche-owned).

## Todos

- [ ] [CODE] P0. **Fix the write-time `canonical_question_group` mis-bucketing bug — 79% of daily Kalshi volume silently
      routes to `OTHER`.** Root cause (confirmed via Phase 6 of the source doc, added 2026-07-26):
      `instruments-service`'s `_extract_prediction_canonical_group` (in the `prediction.py` classifier module, around
      line 95) passes the FULL `instrument_key` instead of the bare Kalshi ticker into the CQG classifier, so the
      classifier fails to match the real canonical group and every affected row falls into the `OTHER` catch-all —
      silently, with no error, every day since at least 2026-07-12 (17+ days of ongoing corruption as of this audit).
      Fix: pass the bare ticker (mirror the Polymarket path's already-correct extraction), add a regression test
      asserting a representative Kalshi ticker classifies to its real CQG (not `OTHER`), and confirm `quality-gates.sh`
      green in instruments-service. This is a live, ongoing data-correctness defect — per CLAUDE.md "Data pipeline
      correctness is the heartbeat," fix in full, no deadline deferral. **Source**:
      `prediction_capture_incident_remediation_2026_07_06.md` (Phase 6, the sole open P1 CODE item — its gated P2
      "assess historical backfill" follow-on is a separate, explicit operator/architect judgment call, NOT included in
      this todo). **Done when**: the fix ships (instruments-service commit SHA cited), the regression test passes, and
      Phase 6's checkbox in the source doc is flipped citing this todo + SHA. (Housekeeping note, not part of this
      todo's scope: `prediction_phase_ab_residuals_2026_07_24.md`'s A1 item is a stale, pre-Phase-6, generic reference
      to "harden the capture path" — whoever executes this todo should also correct A1 to point at Phase 6 /this todo
      instead of leaving it as a confusing duplicate-looking reference.)

- [ ] [BACKEND] P1. **Build the paper-LIVE routing seam: `AtomicInstruction` → `AtomicLegExecutor` via the UTL
      `EventTransport` facade.** Architecture was RULED 2026-07-28 (use the codex-mandated live=batch
      `unified_trading_library.streaming.event_facade` spine — `InMemoryTransport` for paper/colocated; no operator
      decision remains). Build: strategy-service publish side, execution-service subscribe+route side,
      `InMemoryTransport` wiring, and a round-trip proof test (a strategy-emitted `AtomicInstruction` via
      `InMemoryTransport` reaches `AtomicLegExecutor.execute`). **Source**:
      `plans/active/issues/prediction_arb_live_execution_bridge_2026_07_20.md` (sole `## Todos` item). **Done when**:
      the round-trip test passes and `quality-gates.sh` is green across both repos; flip the source doc's checkbox
      citing the SHAs.

- [ ] [BACKEND] P2. **Two-sided Betfair odds — persist back+lay, not just one side.** Item `[5]` under the source doc's
      "Smaller open items (documented, not blocking paper)" — items `[1]`-`[4]` shipped 2026-07-20, this one is still
      open and needs a Betfair-exchange book source. Different component (Betfair adapter) from the EventTransport todo
      above — no file overlap expected, safe to run concurrently. **Source**:
      `plans/active/issues/prediction_arb_live_execution_bridge_2026_07_20.md` (item [5]). **Done when**: back+lay both
      persist for a sampled Betfair market and the source doc's item [5] is marked shipped with the commit SHA.

- [ ] [INFRA] P1. **Launch the historical prediction re-backfill under the widened catalogue, sharded across several
      SPOT VMs, full 2025-03-14→today range.** RULED 2026-07-28 GO (per the source doc's own latest dated section) — no
      operator decision remains. Qualifies for the safe-idempotent VM-launch justification (task_template.md finding T /
      CLAUDE.md's VM-launcher rule): SPOT-provisioned, per-shard idempotent (safe to re-run on preemption),
      PROGRESS-checkpointed per the shipped checkpoint contract. Use the sanctioned launcher registry (grep
      `VM_PREFIX_TO_BUCKET` first — do not hand-roll a name); after completion, re-run the issue doc's own
      already-proven P2 VERIFY methodology at full-corpus scale. **Source**:
      `plans/active/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md` (sole
      remaining `[INFRA] P1` todo). **Done when**: the backfill completes across all shards (STARTED <60s + ≥1
      progress/hr + STOPPED/FAILED verified, no fire-and-forget), the post-completion VERIFY re-run is recorded, and the
      source doc's checkbox is flipped citing VM name(s) + evidence.

- [ ] [SCRIPT] P1. **Kalshi execution credential reshape + live paper-order verify.** Todo 1: read the existing
      `kalshi-api-credentials` bundled JSON secret's fields and provision two new Secret Manager secrets
      (`kalshi-api-key-id`, `kalshi-private-key-pem`) from them, verified non-empty via
      `gcloud secrets versions access`. RULED 2026-07-28 — explicitly NOT wallet-key-class (a reshape of already-live
      credential data), now AO-executable IAM-self-service per RULES.md §5. Todo 2 (gated on todo 1): place a real
      Kalshi paper order end-to-end through execution-service, capture logs/commit evidence. Different files
      (`execution_service/adapters/...` Kalshi credential wiring) from the EventTransport-bridge todo above — no overlap
      expected. **Source**: `plans/active/issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md` (both
      todos). **Done when**: both secrets exist and verify non-empty, a real paper order completes end-to-end with
      captured evidence, and both source-doc todos are flipped citing the SHAs/evidence.

- [ ] [DIAG] P2. **Kalshi mass `attempted_failed` unclassified-adapter-error investigation + contingent fix.**
      Internally-sequential 3-step chain (combined into one todo per the skill's own "sequential work → one todo" rule):
      (1) check whether the mass-`attempted_failed` anomaly recurred on a recent date; (2) pull actual adapter
      exceptions to reclassify `UNCLASSIFIED_ADAPTER_ERROR` into a typed `classify_venue_error()` bucket; (3) if step 2
      confirms rate-limit-shaped errors, apply a contingent backoff/concurrency-cap fix (named precedent to mirror: the
      Tardis single-VM-queue backoff pattern). **Source**:
      `plans/active/issues/kalshi_mass_attempted_failed_unclassified_adapter_error_2026_07_27.md` (all 3 todos). **Done
      when**: the recurrence check + reclassification verdict are recorded, the contingent fix ships if warranted (or is
      explicitly ruled out with evidence if not), and the source doc's todos are flipped.

- [ ] [SCRIPT] P2. **cqg partition-completeness — recent-window catalogue re-enumeration (operational run, already-
      fixed classifier).** A bounded operational re-walk using the classifier fix that already shipped — not a code
      change. **Source**: `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` (the `[~]` in-progress
      "cqg partition-completeness" item). **Done when**: the re-enumeration run completes with a dated verdict recorded
      in the source doc's Progress Log and its checkbox flipped.

- [ ] [BACKEND] P2. **Build the fixture-pairing residual — registry-resolution + mapping-population + arb-layer wiring
      across UAC/IS/features-service/strategy-service.** RULED 2026-07-28 in
      `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s "RULED 2026-07-28" section: generalize the
      already-proven soccer fixture-match resolver pattern
      (`instruments-service/reference_data/adapters/prediction/fixture_match.py` — registry-resolution + per- instrument
      side-table + closed-set honest-absence, no silent fallback) to the cross-venue pairing problem. Build the FULL
      mechanism (no partial/heuristic-only pairing) — batch4 already retagged this `[BACKEND]` (was `[DESIGN]`) and
      removed the "needs a design session first" gate; batch4's own gated `_finalize` doc does NOT build this either
      (its 3 todos are reconciliation/archival-scoped only), so drafting it here is not a duplicate. **Source**:
      `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` (the fixture-pairing residual item, per
      batch4's ruling). **Done when**: the mechanism is wired end-to-end across all 4 repos with a passing integration
      test, and both the source doc's checkbox and batch4's "RULED" section are updated to note it shipped (citing this
      todo + SHAs).

- [ ] [UAC] P2. **Politics/geo cross-venue canonicalization — structured audit + build.** RULED 2026-07-28 (same batch4
      section as above): (1) enumerate every Kalshi Politics 2049-series vs Polymarket TRUMP/GEO family pair with a
      proposed canonical grouping + recommendation per pair; (2) apply the arbable/non-arbable call per pair using
      objective structural signals (same underlying resolution date + same real-world referent, mirroring the soccer
      fixture-matcher's `af_fixture_id`-equivalence test) wherever they disambiguate; (3) escalate ONLY the specific
      pairs where structural signals don't disambiguate as a narrow options+recommendation operator question — not the
      whole audit. Batch4 retagged this `[UAC]` (was design-gated); its `_finalize` doc does not build it either.
      **Source**: `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` (the politics/geo
      canonicalization item, per batch4's ruling). **Done when**: the structured enumeration + per-pair calls are
      recorded, any genuinely-tied residual is filed as a narrow operator question (not a blocker to closing this todo),
      and the source doc's checkbox is flipped.

- [ ] [DIAG] P2. **Investigate why 8 registered `canonical_question_group`s have zero manifest rows.** Freshly
      discovered (2026-07-27), postdates every prior triage pass — genuinely never seen by any covering doc. **Source**:
      `plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md` (the new `[DIAG] P2` item; the doc's other 4-item
      ML dependency chain remains correctly time-gated on `sports_master` Group E's FSS ≥95% non-NULL threshold — NOT
      part of this todo, do not attempt it). **Done when**: a verdict (registry drift, writer gap, or
      genuinely-empty-by-design) is recorded with evidence, and the source doc's checkbox is flipped.

- [ ] [SCRIPT] P1. **Phase 5 — canonical-groups backfill, ~24 remaining groups beyond the initial 9+7-CME.** Mirror the
      already-shipped 7 CME-linked groups' pattern: per-group UAC `PREDICTION_GROUPS` registry entry +
      instruments-service catalog backfill + MTDS backfill, with cluster-validation counts as the done-when. Needs
      unified-api-contracts + instruments-service + market-tick-data-service (structurally outside
      `prediction_phase_c_data_status_ui_2026_07_24.md`'s repos, which is deployment-api/deployment-ui only and cannot
      deliver this — confirmed by 3 independent prior audits). **Source**:
      `plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md` (the `[SCRIPT] P1` "Phase 5" item — full
      remaining group list in the source doc). **Done when**: all ~24 groups are registered + backfilled +
      cluster-validated, and the source doc's checkbox is flipped citing SHAs.

- [ ] [INFRA] P3. **Enable BQ external tables for prediction live-depth data.** Stated command:
      `terraform apply ... -var=create_bq_external_tables=true ...` (per the source doc's own Progress Log). Cleanup,
      not a hard blocker — an already-permissioned-SA workaround is live. **Source**:
      `plans/active/prediction_live_clob_depth_capture_2026_07_24.md` (the "Enable BQ external tables" prose item under
      "Pending after warm data confirmed"). **Done when**: `terraform apply` completes and the source doc's Progress Log
      records it done.

- [ ] [INFRA] P3. **Grant the default compute SA `roles/pubsub.publisher` (or confirm the workaround is permanent and
      close as won't-fix).** A workaround via a different already-permissioned SA is live, so this is cleanup only, not
      blocking. If the executing identity hits `PERMISSION_DENIED` granting this itself, it is the SAME ambient identity
      (`unified-trading-sa`/`uts-orchestrator-epic-role`) this corpus's workers already run as — grant the specific role
      yourself per RULES.md §5 (least-privilege, verify live), do not file a blocked-question. **Source**:
      `plans/active/prediction_live_clob_depth_capture_2026_07_24.md` (the "Grant project-level roles/pubsub.publisher"
      prose item). **Done when**: either the grant is applied and verified live, or the doc is updated to record the
      workaround as the permanent posture with the grant item struck through.

## Deferred — housekeeping already covered by an existing (draft) plan, not re-drafted here

- **`prediction_satellite_ao_dispatch_batch2_2026_07_25.md` is DONE (7/7 todos checked) but not yet archived.** Its
  gated `_finalize` (`prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25.md`, `status: draft`, `depends_on`
  satisfied) already covers: (a) reconciling `kalshi_live_capture_regression_and_drift_2026_07_13.md`'s
  stale-but-actually-shipped checkboxes (this audit independently confirmed items 1 & 3 are done, item 2 correctly
  forked to `kalshi_execution_credential_secret_name_mismatch_2026_07_26.md` — matches batch2_finalize todo 1's scope
  exactly); (b) correcting `prediction_consolidated_closeout_2026_07_18.md`'s stale "0 open todos" index claims for
  `prediction_arb_live_execution_bridge_2026_07_20.md` and
  `prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` (batch2_finalize todo 2); (c) archiving batch2 itself
  (todo 3). **Not re-drafted here** — flipping batch2_finalize to `active` (a separate operator action from this batch)
  is the correct next step, not a new batch6 todo. Flagging in this Progress Log so it isn't lost.

## Deferred — already self-dispatching (assigned_vm: planning + status: open, not a real orphan)

- **`plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`** — 1 open `[DATA] P2` item
  (investigate the KALSHI-venue scaffold-row provenance mislabel, 129,227 rows). Confirmed via a live re-read mid-audit:
  `assigned_vm: planning`, `status: open`, proper `- [ ]` checkbox format — this is ALREADY its own independent
  AO-dispatch surface via `regen_backlog_from_plan.py`'s direct `issues/`-directory scan (its predecessor P1 todo in
  this same doc was picked up and completed by a real worker two days after being added). Drafting a batch6 todo for it
  would duplicate an already-dispatching backlog item.
- **`plans/active/issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md`** — same
  situation (`assigned_vm: planning`, `status: open`). Its higher-value remaining item (the delta_one benchmark number)
  is also already substantively closed today (2026-07-29) via a cross-cutting infra plan
  (`data_pipeline_check_mdps_features_2026_07_20.md`) outside this tranche's covering set; only a small
  currently-unreachable volatility-module echo genuinely remains, tracked on the self-dispatching doc itself.

## Deferred — claimed by a different existing plan (not a prediction-tranche gap)

- **`plans/active/prediction_cqg_residual_2026_07_24.md`'s remaining leg** (delete dead `None`-branch handling + stale
  docstrings in MTDS `rebuild_prediction_manifest.py` / `kalshi_adapter.py`) is already tracked and "in flight as part
  of the MTDS CODE_QUICK backlog pass" per `plans/active/issues/code_quick_cross_repo_fix_backlog_2026_07_28.md`
  (`asset_group: [meta]`, outside this tranche). Not re-drafted here to avoid a duplicate claim on the same fix.

## Deferred — too large for a batch todo (needs its own dedicated plan)

- **`plans/active/data_completion_prediction_2026_07_15.md`'s Phase-B OBJECT-layer CQG-bundle migration** — a
  coordinated 3-repo code change (UAC + market-tick-data-service + market-data-processing-service) to cut prediction
  `trades` objects from per-market files to per-`(canonical_question_group,day)` bundle files, plus a historical rollup
  migration script, VM-drain+walk+apply, post-verify, and legacy-object deletion. Confirmed un-started and uncovered by
  this audit; independently re-triaged to "0 AO-eligible, needs its own dedicated plan" by batch1, batch2 (as a
  `Phase-B-naming-ambiguity` operator-gated conflict), batch3, and batch4 — four separate prior passes agree. Recommend
  a dedicated design/scoping plan, not a batch todo, per the skill's "too-large-or-risky" taxonomy. The doc's
  manifest-VALUE-relabeling slice (source/data_type/instrument_type stamping) is separately, genuinely already covered
  (applied live 2026-07-19 via `prediction_phase_ab_residuals_2026_07_24.md`'s Phase B todo) — not part of this
  residual.

## Deferred — not AO-eligible (needs a scoping/design decision first, likely `ao`-tranche scope)

- **`plans/active/issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md`** — two prose-only recommended
  fixes (a durable, task-id-keyed checkpoint location for resumable AO scripts; a dispatcher-side
  in-flight/live-heartbeat check to stop re-assigning an already-dispatched todo to a second slot), both explicitly
  scoped by the doc's own author as "a dispatcher/process change, out of a single todo's scope" needing a design
  decision (where the shared checkpoint lives; the exact heartbeat-staleness threshold) before becoming a bounded todo.
  This is agent-orchestrator dispatch/checkpoint architecture, not prediction data work — flagging for the
  `ao`-tranche's own closeout audit rather than drafting it here. Note: the failure this issue predicts has recurred at
  least twice more since filing (2026-07-29 Progress Log entries in
  `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`), so this is a live, worsening gap worth the `ao` tranche's
  attention, not a stale concern.

## Deferred — genuinely sports-primary (owned by the sports tranche, not re-drafted here)

Per the skill's Orthogonality rule, `[sports, prediction]` is a legitimate dual-tag (same betting-market work tagged two
ways), so these 4 docs are valid prediction-tranche candidates too — but their actual content, `parent_epic`, and 3
independent prior audits (batch3, batch3_finalize, batch5 — all 2026-07-26) all converge on "owned by the sports
tranche, excluded here to avoid duplicate dispatch." Re-confirmed by this run, not re-litigated:

- `plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md` (8 open `[DESIGN]` todos + 3 unanswered
  operator sign-off questions — design-gated, not AO-eligible).
- `plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md` (5 open todos, design-gated on an unresolved
  SportsMatchingEngine-vs-L0Matcher duplication call + a plan-wide operator sign-off gate).
- `plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` (residual: strategy-service
  migration + a cross-repo parity test — genuinely uncovered, but should be drafted as a SPORTS-tranche batch item).
- `plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md` (residual: 4 checkbox-drift items + 2
  substantively-undone REVIEW todos + a missing codex SSOT note — same as above, sports-tranche scope).
- `plans/active/issues/sports_odds_naming_migration_uncommitted_wip_and_checkbox_drift_2026_07_25.md` (1 remaining
  `[OPERATOR]` reclassification judgment call, not AO-eligible; sports's own active `batch6` already carries the
  identical item per this run's evidence).
- `plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md` — classified `exclude_cross_cutting` by
  Phase 1 (not even a borderline case): 5 of 6 remaining todos build sports-only live-trading infrastructure, the doc's
  own text explicitly carves prediction OUT of scope ("a separate question... prediction hasn't reached 'ML pipeline
  running' yet"), and `parent_epic: sports_master` confirms it.

**Also surfaced, dual-tagged `[sports, prediction]` but content is 100% sports-side**:
`plans/active/issues/gcs_path_resolution_centralization_audit_sports_prediction_2026_07_28.md` — 2 open `[SCRIPT] P2`
todos (fix the live-mode sports-odds writer shape mismatch; delete 5 dead `sports_*` PATH_REGISTRY rows + their dead
consumer classes), genuinely uncovered by anything in this tranche's covering set, but both items are
sports-odds/sports-registry content with zero prediction-market-specific work — recommend the sports tranche's own
`/ag-closeout-audit sports` sibling run (this same dispatch wave) claim it rather than duplicating here.

## Progress Log

- 2026-07-29 (slot 14, ag_closeout_auditor, dispatch agt-17d52d): drafted by the `/ag-closeout-audit prediction`
  scheduled run. Phase 0: rediscovered the covering-plan set via `generate_ag_closeout_audit_candidates.py` (8
  auto-detected covering docs) + a manual addition (`prediction_consolidated_native_ao_extract_2026_07_25.md`, the
  non-finalize sibling — the script's `dispatch_batch|satellite|_finalize` filename regex doesn't match
  `native_ao_extract`, a real gap in the script worth a future fix) + the 4 archived batch3/5(+finalize) docs for
  historical context. Phase 0.3: 61 candidate docs (`asset_group` containing `prediction`, excluding covering docs and
  resolved/archived/superseded status); applied the orthogonality filter (exclude docs dual-tagged with a genuinely
  different peer AG — cefi/defi/tradfi/cross-cutting — per the skill's Phase 0.3 rule), narrowing to 22
  prediction-primary or legitimately-dual-tagged (`[sports, prediction]` / `[prediction, ao]`) candidates. Phase 1:
  Workflow `wf_6e35eef8-57b`, 22 agents, 0 errors, ~2.92M subagent tokens, 386 tool calls, ~20min wall-clock — full
  per-doc verdicts + evidence in the workflow journal. Phase 3: conflict-checked every orphaned verdict against the full
  covering-plan set (see the 6 Deferred sections above for the excluded population's disposition); drafted this batch's
  13 todos across 9 conflict-clear source docs. `status: draft` per CLAUDE.md — awaiting operator review before flip to
  `active`.
