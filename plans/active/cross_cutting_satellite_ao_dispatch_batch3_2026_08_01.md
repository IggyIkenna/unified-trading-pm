---
doc_type: plan
title: Cross-cutting satellite AO batch 3 — 8 conflict-cleared todos from the 2026-08-01 never-cited pre-filter sweep
summary: >-
  Third AO-dispatch batch for the cross-cutting tranche, produced by re-invoking `/ag-closeout-audit cross-cutting`
  (autonomous, scheduled `ag_closeout_auditor` dispatch `agt-a5c7d6`, slot 13). Phase 0 used
  `generate_ag_closeout_audit_candidates.py --tranche cross-cutting` (90 tranche members, 11 never-cited) plus a manual
  `asset_group: meta`-sweep gap check that surfaced 1 more genuine member missed by the generator's epic-filter logic
  (`data_pipeline_alerts_batch_remediation_2026_07_15.md` — parent_epic `observability_master`, not one of the 5
  DATA_EPICS, but real cross-cutting content per its own 2026-07-31 mistag-correction comment). A Phase-1 `Workflow` (12
  agents, one per candidate) classified all 12: **6 exclude_cross_cutting** (mistags — content is genuinely
  ao/ci/ui/infra/tradfi, not multi-asset-group; NOT retagged by this batch per the 2026-07-30 primary-owner rule — see
  the parked-findings issue doc below) and **6 genuinely orphaned**, of which this batch drafts 8 conflict-cleared todos
  across 5 of those 6 docs (the 6th, `order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md`, is 100% operator-gated
  — see Deferred). Every todo was grepped against all 6 prior cross-cutting covering docs (consolidated closeout +
  batch1/1b/2 + their finalizes) with zero citations found in any — a clean, unclaimed orphan population, not a
  re-litigation of prior batches' ground.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm, features-service, unified-trading-library, deployment-service, strategy-service]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-3, satellite-docs, never-cited-sweep]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.4
estimate_calibrated_ai_days: 1.9
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit cross-cutting re-invocation 2026-08-01 (autonomous, dispatch agt-a5c7d6, slot 13), Phase 1 Workflow
  classification of the 12 never-cited/gap candidates found by Phase 0.
---

# Cross-cutting satellite AO batch 3

> **Status: draft** — this batch is `assigned_vm: NA` / `status: draft` pending explicit operator review + approval to
> dispatch (flip to `assigned_vm: planning` + `status: active`), per CLAUDE.md's "Plan destination — ASK BEFORE
> CREATING" HARD RULE and this skill's own Autonomous-mode Phase 3 contract (a skill-drafted plan is never
> auto-shipped). Every todo below is independently conflict-cleared and file-disjoint from every other todo here and
> from every open todo in batch1/1b/2 — safe to dispatch as-is once approved.

## Todos

- [ ] [DIAG] P2. **Audit `multi_timeframe`'s `feature_builder_registry.py` `depends_on` entries.** Source:
      `issues/feature_builder_registry_dag_dead_code_audit_2026_08_01.md`. That doc already found + fixed a live bug in
      `cross_instrument`'s `composite_sr`/`flow_interaction` builders (a declared DAG dependency whose consuming
      calculator never actually received the upstream-computed DataFrame — silently recomputed internally instead) and
      confirmed `delta_one` is harmless/decorative scaffolding. Read
      `features_service/multi_timeframe/schemas/feature_builder_registry.py`'s declared `depends_on` entries; for each,
      check whether the dependent calculator's `__init__`/build path accepts an upstream-injected DataFrame (real bug →
      apply the same thread-the-frame fix already demonstrated on `composite_sr`) vs. recomputes internally (harmless,
      no action, note it) vs. is genuinely dead scaffolding (delete the stale `depends_on` entry). **Done when**: every
      declared dependency in this module is classified real-bug-fixed / confirmed-harmless / deleted-dead-code with
      cited evidence, and the source doc's corresponding checkbox is flipped.
- [ ] [DIAG] P2. **Audit `onchain`'s `feature_builder_registry.py` `depends_on` entries.** Source:
      `issues/feature_builder_registry_dag_dead_code_audit_2026_08_01.md`. Same method as the `multi_timeframe` todo
      above, applied to `features_service/onchain/schemas/feature_builder_registry.py`. **Done when**: every declared
      dependency in this module is classified real-bug-fixed / confirmed-harmless / deleted-dead-code with cited
      evidence, and the source doc's corresponding checkbox is flipped.
- [ ] [DIAG] P2. **Audit `volatility`'s `feature_builder_registry.py` `depends_on` entries.** Source:
      `issues/feature_builder_registry_dag_dead_code_audit_2026_08_01.md`. Same method as the `multi_timeframe` todo
      above, applied to `features_service/volatility/schemas/feature_builder_registry.py`. **Done when**: every declared
      dependency in this module is classified real-bug-fixed / confirmed-harmless / deleted-dead-code with cited
      evidence, and the source doc's corresponding checkbox is flipped.
- [ ] [OPS] P3. **Verify the manifest-consolidator cadence-reduction billing savings materialized.** Source:
      `issues/manifest_consolidator_cadence_cost_audit_2026_07_20.md` § 5/§6 "Resolution criteria (b)". The
      cadence-reduction fix shipped `deployment-service@7b832cb0` on 2026-07-30; today (2026-08-01) the first fully-
      settled post-ship day (2026-07-31) should already be queryable. Re-run the doc's own §5 BigQuery billing-export
      recipe for `purpose=manifest-consolidator` against 2026-07-31, confirm the ~$109/day (~$3,270/mo) addressable
      savings materialized, and grep `#data-pipeline-alerts` history + the
      `uts-prod-consolidator-liveness-watchdog-{fast,slow}` Cloud Run execution logs for the 24h+ post-ship window for
      any `CONSOLIDATOR_DOWN`/ `ManifestConsolidatorStaleError` events attributable to the change. **Done when**: the
      billing comparison and the zero-regression check are both recorded with cited evidence, and the doc's checkbox is
      flipped (or, if the numbers don't match, the discrepancy is recorded and a fresh todo filed rather than silently
      closed).
- [ ] [BACKEND] P3. **Reproduce + root-cause the prettier proseWrap inline-code-span mangling bug.** Source:
      `issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md`. Build a minimal `.md` fixture with a
      long backtick inline-code span near `printWidth=120` to reproduce the mangling (confirmed live in 2 real docs this
      session, see the paired todo below). Determine root cause (a `.prettierrc` config issue vs. a prettier-version
      bug) and apply either (A) a `.prettierrc` fix or (B) a plan-hygiene/prek lint check that catches multi-space runs
      inside backtick spans + over-padded continuation lines. Confirm the fix against the exact `fd1b02c2c`-style
      pattern the source doc documents. **Done when**: the fixture reproduces the bug pre-fix and no longer reproduces
      it post-fix, the root cause is recorded, and the source doc's todo 1 checkbox is flipped.
- [ ] [BACKEND] P3. **Hand-fix the live prettier-mangled span in
      `sports_stats_delayed_live_capture_still_dead_post_fix_2026_07_29.md`.** Source:
      `issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md` todo 2. Confirmed still live as of
      2026-08-01 at lines 403/412/422 (`printWidth=120        PERMANENT errors`, `batch_understat        filter`,
      `entity_wanted("XG")` padding). Re-run prettier (if the paired todo above has already landed a fix) or hand-fix
      the multi-space-run mangling directly. **Verify content-only via `git diff -w` before committing** — this must be
      a zero-semantic-change whitespace fix, nothing else in that doc's content may change. **Done when**: `git diff -w`
      on the fix commit shows no non-whitespace delta, and the source doc's todo 2 checkbox is flipped.
- [ ] [DOC] P3. **Document `VersionGovernanceReloader` + `StrategyDirectiveReloader` in the live-strategy-config
      hot-reload SSOT.** Source: `issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md` follow-up 2. Both
      reloaders are already shipped in `strategy-service/strategy_service/config_reloaders.py` but undocumented in
      `/codex/04-architecture/live-strategy-config-hot-reload.md`. Read the shipped code and add documentation of both
      reloaders' actual behavior to the SSOT. Independent of that doc's unresolved A/B/C safety-guard decision (follow-
      up 1, operator-gated — do not touch that question here). **Done when**: the SSOT documents both reloaders with the
      same depth as the existing `StrategyConfigReloader` section, and the source doc's follow-up 2 checkbox is flipped.
- [ ] [DOCS] P0. **Correct the mbp_10/CME scope framing + audit the `DP_RUN_MOSTLY_EMPTY` suppression decision for that
      cell.** Source: `data_pipeline_alerts_batch_remediation_2026_07_15.md`'s second open item. Edit
      `plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` to state
      plainly that the CME/`mbp_10` UAC registry restriction is a confirmed-still-intentional operator MVP-scope
      decision, not an open gap (that doc's own "Resolution — mbp_10" section already carries this framing internally —
      this is a top-of-doc/summary correction so the framing isn't buried). Then audit the `DP_RUN_MOSTLY_EMPTY`
      detector (`deployment-service` data-pipeline monitors) to determine whether the (tradfi, CME, `mbp_10`) cell
      should be suppressed or reclassified as expected, following the same narrowing precedent already used for the
      KRX/ICE/CBOE cells in that same sub-issue doc, and implement whichever the precedent implies. **This is a content
      edit to a tradfi-titled doc; re-verify no concurrent tradfi-tranche edit is in flight on that file immediately
      before committing** (verified clear as of this batch's authoring — 2026-08-01, zero commits in the preceding 6h,
      no `locked_by`). **Done when**: the framing correction is committed, the suppression/reclassify decision is
      implemented or explicitly recorded as already-correct-as-is, and
      `data_pipeline_alerts_batch_remediation_2026_07_15.md`'s second open item checkbox is flipped.

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION)

- **`issues/order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md`** (2 open, 100% of this doc's remaining work).
  Todo 1 is an explicit `[OPERATOR] P2` — rule between 3 named design options (A: advance UAC's `OrderStatus` to the
  full 9-state contract the codex doc declares / B: retreat the codex doc to the shipped 7-state enum / C: split into a
  venue-reported `OrderStatus` + a separate internal lifecycle enum) for a genuine SSOT-vs-shipped contradiction in the
  order-lifecycle enum. Todo 2 (write the regression test) is explicitly sequenced behind todo 1 — its content is
  undefined until the enum shape is ruled. Neither is batchable until the operator decides. Zero coverage found anywhere
  in the corpus's active plans.
- **`issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md`** follow-up 1 (1 open; follow-up 2 is batched
  above). `[OPERATOR] P2` — rule between A (implement the safe-field allow-list + `UnsafeConfigChangeError` guard) / B
  (retire the guard claim from the design doc) / C (split: gate archetype-family changes only, keep instrument-universe
  hot-swap) — specifically requires an operator judgment call on whether a live instrument-universe swap is
  position-state-safe. Not batchable until ruled.

## Deferred — time-/sequencing-gated (re-check on the next iteration)

- **`data_pipeline_alerts_batch_remediation_2026_07_15.md`** first open item (`[REVIEW] P0`, "PARTIALLY DONE, time-bound
  limit"). The dedup-fix code itself is independently verified done (unit tests + adversarial re-derivation); what
  remains is confirming a RESOLVED/green bookend actually posts to `#data-pipeline-alerts` once the underlying
  sports/tradfi/cefi conditions genuinely clear — that requires real wall-clock time AND those separate data-fix efforts
  to land first, neither of which a worker can force. Re-check on the next cross-cutting audit pass whether the
  underlying conditions have cleared; if so, this becomes a bounded live-observation todo.

## Not orphaned — checked, not assumed (recorded so a later pass does not re-raise them)

- **`plans/active/ao_slot_capacity_policy_ci_scheduled_split_2026_07_29.md`**,
  **`issues/checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md`**,
  **`issues/deployment_api_sigabrt_crash_loop_unresolvable_sha_citation_2026_07_31.md`**,
  **`issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`**,
  **`issues/workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md`**,
  **`tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md`** — all 6 verdicted `exclude_cross_cutting` by
  this batch's Phase 1 Workflow: each carries `asset_group: [cross-cutting]` but real content that is genuinely ao / ci
  / ui-or-infra / infrastructure / ao / tradfi respectively (not multi-asset-group cross-cutting scope). Per the
  2026-07-30 primary-owner rule ("a retag... belongs to the OWNING tranche alone, so N workers never race the same
  file"), this batch does NOT perform those retags — full evidence + recommended target tranche per doc is filed in
  `issues/ag_closeout_audit_cross-cutting_parked_2026_08_01.md` for the owning tranches' own next audit pass to action.
  Recorded here too so a future cross-cutting pass does not re-classify them as fresh orphans.

## Codex SSOTs

`/codex/02-data/availability-manifest-and-data-status.md`, `/codex/11-project-management/doc-frontmatter-schema.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`.

## Progress Log

- **2026-08-01** — Drafted (`/ag-closeout-audit cross-cutting`, autonomous, dispatch `agt-a5c7d6`, slot 13). Phase 0: 90
  tranche members via `generate_ag_closeout_audit_candidates.py`, 11 never-cited + 1 found via manual meta-sweep gap
  check (`data_pipeline_alerts_batch_remediation_2026_07_15.md`, parent_epic outside the generator's DATA_EPICS filter).
  Orthogonality HARD CHECK re-run: 0 genuine dual-tag mistags (4 hits were all legitimate multi-AG coordination docs, 2+
  specific AGs alongside cross-cutting). Phase 1 (`Workflow`, 12 agents): 6 exclude_cross_cutting (all mistags,
  corroborated in 4/6 cases by independent prior audits from other tranches), 6 orphaned_never_touched. Phase 3
  conflict-check: all 8 drafted todos grepped clean against all 6 prior covering docs + spot-checked for
  recent-commit/lock collisions on the 2 todos touching other-tranche-titled docs (both clear). `status: draft` pending
  operator review.
- **plan_reconciler 2026-08-02** (whole-corpus pass, mechanical-adjudicator hunter, `check_codex_refs.sh` BROKEN-ref
  flag): fixed the "## Codex SSOTs" section's `ao-dispatch-batch-naming-and-conflict-check.md` ref, which was pointing
  at the `12-agent-workflow` directory — disk-verified correct location is
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` (same directory-swap defect the
  companion finalize plan's context-scout pass already flagged). See
  `/plans/active/issues/plan_reconciler_findings_undefined.md`.
