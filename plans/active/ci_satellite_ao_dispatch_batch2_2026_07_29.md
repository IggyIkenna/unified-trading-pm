---
doc_type: plan
title: CI satellite AO batch 2 — second AO-dispatch extraction for the ci tranche
summary: >-
  Second AO-dispatch batch for the `ci` topic tranche, produced by `/ag-closeout-audit ci` (autonomous mode, 2026-07-29)
  re-running against `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (still `status: active`, 14/30 todos done at audit
  time) per the skill's iterative-drain methodology. Phase 0: re-checked batch1's own conflict-gated Deferred items
  first (D2-D6) — three have cleared since 2026-07-26 (D5 operator-ruled TODAY 2026-07-29, D7/D3(1) and D18 already
  resolved per batch1's own 2026-07-28 gate-cleanup notes) and become todos here; D3's remaining quickmerge.sh claims
  and D2/D6 remain genuinely gated, carried forward. Phase 0.3 also caught a real script bug —
  `generate_ag_closeout_audit_candidates.py`'s `ao`/`ci`/`infra` membership branch silently returns zero candidates once
  the tranche's own consolidated-closeout doc is archived (which `ci`'s was, 2026-07-28) — worked around via a direct
  frontmatter sweep (`asset_group` containing `ci`) per the skill's now-documented 2026-07-27 schema-migration guidance
  (see
  `plans/active/issues/generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md`
  for the bug report). Phase 1 read all 9 newly-surfaced candidate docs end-to-end (29 direct `asset_group:[ci]` docs
  minus batch1/finalize minus already-cited/self-dispatched, plus 1 already-known `asset_group:[meta]` fold-in) via a
  Workflow — all 9 confirmed genuinely orphaned (7 `orphaned_never_touched`, 2 `orphaned_partial_coverage`). Phase 3's
  conflict-check found `scripts/quality-gates-base/base-service.sh` claimed by 3 candidates and `base-library.sh` by 2 —
  rationed to one todo per file, same discipline as batch1. 14 conflict-cleared bounded todos below; the rest deferred
  by taxonomy (file-contention / operator-gated / duplicate-of-self-dispatched / too-large / role-mismatch).
status: draft
nature: process
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    unified-trading-library,
    market-tick-data-service,
    deployment-api,
    strategy-service,
    features-service,
    execution-service,
    instruments-service,
    greeks-service,
    e2e-testing,
    unified-api-contracts,
    system-integration-tests,
  ]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-2, satellite-docs, quickmerge, quality-gates, test-speed]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/active/ci_satellite_ao_dispatch_batch2_finalize_2026_07_29.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-07-29"
last_updated: "2026-07-29"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5.5
estimate_calibrated_ai_days: 4.4
assigned_role: cicd
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit ci` run 2026-07-29 (ag_closeout_auditor scheduled worker, slot 7), re-triaging
  `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s Deferred section + a fresh Phase 1 sweep of docs never touched by
  batch1 (9 new-since-2026-07-26 or previously-missed tranche members).
---

# CI satellite AO batch 2

> **⚠️ STATUS: `draft` — NOT dispatched, NOT ingested.** Flipping this (and its finalize sibling) to `status: active` is
> the operator's call per CLAUDE.md § "Plan destination — ASK BEFORE CREATING" and the `/ag-closeout-audit` skill's
> autonomous-mode rule. Drafted by a scheduled one-shot audit worker; nothing here has been shipped.

> **Why this plan exists.** `ci_satellite_ao_dispatch_batch1_2026_07_26.md` is still active with 16/30 todos open — this
> is NOT a replacement for it. This is the tranche's SECOND extraction: items batch1 deliberately deferred (now
> conflict-cleared) plus docs that never existed or were never discovered as of batch1's 2026-07-26 snapshot.

## Same-file contention — read before editing this plan

Same-priority todos in one plan run **concurrently**, so they must touch disjoint files (CLAUDE.md § Plans). Three files
are contended this round:

- **`scripts/quality-gates-base/base-service.sh` — claimed by 3 candidates.** Only todo 1 touches it (folds in the
  `--durations=25` addition too, since it already owns the file this round).
  `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md`'s BATS-phase todo also wants this file — deferred to
  batch 3 (see `## Deferred`).
- **`scripts/quality-gates-base/base-library.sh` — claimed by 2 candidates.** Only todo 11 (the `${TMPDIR:-/tmp}` port)
  touches it. The `--durations=25` addition (same source as the base-service.sh contention above) also wanted this file
  — deferred to batch 3, do not add a second base-library.sh todo here.
- **`scripts/quickmerge.sh` — claimed by 4 candidates.** Only todo 1 touches it (the ENVIRONMENT-alignment piece).
  `stale_staging_versions_manifest_2026_07_23.md`'s STAGE 1.6 dormancy gate (D8, previously "reserved" for this batch —
  see note in `## Deferred`), `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md`'s redundant-hook
  deletion (D4), and `ldr_to_main_promote_churn_fix_verification_2026_07_27.md`'s Option-B removal (operator-gated
  anyway) are all deferred again.

Every audit/verification todo records its findings **in its own named source doc**, never in this plan's body, so
concurrent workers do not collide on this file.

## Todos

- [ ] [INFRA] P1. **Bind configuration into the QG sentinel + align quickmerge/standalone `ENVIRONMENT` resolution + add
      the `--durations=25` visibility flag.** Three related `scripts/base-service.sh`/`scripts/quickmerge.sh` changes
      bundled into one todo (same file, avoids a same-priority collision with the other two candidates this round — see
      § Same-file contention): (a) mix `ENVIRONMENT` (and any other gate-affecting env var) into the QG sentinel hash so
      a sentinel produced under one configuration cannot satisfy a run under another, with a regression test proving a
      dev-written sentinel does NOT satisfy a prod-context quickmerge; (b) make quickmerge's and a standalone
      `quality-gates.sh --no-fix` run resolve the SAME explicit `ENVIRONMENT` for the same branch context — do NOT flip
      quickmerge itself to `production` (that trades this hazard for real prod-credential exposure on every slot's every
      commit); instead make the standalone entrypoint derive `ENVIRONMENT` from the same branch-conditional logic
      quickmerge uses, covering every repo's entrypoint, not just the 3-4 currently-affected repos, with a regression
      test asserting both paths resolve identically for the same branch; (c) add `--durations=25` to the shared pytest
      invocation in `base-service.sh` (visibility only, zero behavior change). **Done when**: (a) and (b) each have a
      passing regression test, `quality-gates.sh` is green in every repo touched, and (c)'s duration output is visible
      on a real PM run. Sources: `issues/qg_sentinel_environment_blind_2026_07_23.md` (Resolution checklist items 2 + 5,
      RULED 2026-07-28 — no longer operator-gated) · `issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md`
      (`--durations=25` item).
- [ ] [DOC] P2. **Correct the "re-run quality-gates.sh --no-fix then retry" recovery guidance** wherever it is taught
      (agent prompts, runbooks) — as written today it is a sentinel-laundering step, not a fix; correct it to describe
      the post-todo-1 behavior (sentinel now binds configuration, so the recovery is genuinely safe). Sequenced after
      todo 1 lands (describes its outcome). Source: `issues/qg_sentinel_environment_blind_2026_07_23.md` (Resolution
      checklist item 4).
- [ ] [INFRA] P2. **Fix the env-coupled `ENVIRONMENT`-ambient-default tests in `deployment-api` and `strategy-service`**
      (set the environment explicitly per-test instead of relying on the ambient default, same pattern already shipped
      in `unified-trading-library`). **Explicitly excludes the two `market-tick-data-service` cases** — those stay gated
      pending `mtds_deployment_env_race_survives_single_worker_2026_07_23.md`'s own cascade-instrumentation step (still
      open, see `## Deferred`); fixing them first would silence the only known reproducer of a real leak before its
      cause is confirmed. **Done when**: both repos' env-coupled tests pass under `ENVIRONMENT=development` and unset,
      and `quality-gates.sh` is green in both. Source: `issues/qg_sentinel_environment_blind_2026_07_23.md` (Resolution
      checklist item 3, partial — the non-MTDS half).
- [ ] [DEVOPS] P2. **Ship the branch-health PROMOTION-LAG vs PROVENANCE-BLOCKED fix + clear the 2 live provenance
      blocks.** Three bundled fixes in `scripts/cicd/promotion_lag_monitor.py` and 2 external repos (internally related,
      one source doc): (a) when a promote PR carries `<!-- promote:provenance-blocked -->`, classify the branch-health
      alert as `PROVENANCE-BLOCKED` (not `PROMOTION LAG`), inlining the offending SHA + subject + the "re-ship or
      revert, do NOT hand-arm" remedy, deduped by state-transition per `/codex/04-architecture/ci-alerting.md`; (b)
      clear the 2 currently-live blocks at source — `market-tick-data-service@d302f07a` (re-ship via
      `quickmerge --agent --files`, or revert on LDR) and `deployment-ui`'s offending commit (identify via
      `git log origin/main..origin/live-defi-rollout` + trailer scan, same remedy) — **do NOT hand-arm auto-merge on
      either**; (c) confirm `_backmerge` merge commits are carve-out-exempt in `check_strict_quickmerge.py` (already
      confirmed exempt by batch1's todo 4 — this is a re-verification, not new work). **Done when**: the alert
      reclassification is live and tested against a synthetic provenance-blocked PR, both named blocks are cleared (or
      explicitly reverted), and the `_backmerge` exemption is re-confirmed in this doc. Source:
      `issues/promotion_lag_alert_hides_provenance_block_2026_07_17.md` (retagged `[OPERATOR]` → `[DEVOPS]` 2026-07-28 —
      re-shipping/reverting an already-identified bypassing commit needs no operator judgment call).
- [ ] [SCRIPT] P2. **Extend the `Quickmerge:` commit trailer to recognize the dirty-deps direct-push carve-out.**
      **RULED 2026-07-29 (operator direct answer, same-day as this audit) — Option 2.** Add a third structured trailer
      value alongside today's `agent`/`human` — e.g. `Quickmerge: direct-carveout-dirty-deps` — to
      `scripts/cicd/check_strict_quickmerge.py`'s accepted-value set (reuses the existing trusted trailer-presence
      mechanism, no new spoofable free-text heuristic), and update the dirty-deps direct-push recipe
      (`SUB_AGENT_MANDATORY_RULES.md` / the git-safety codex) to stamp it on every sanctioned direct push. **Done
      when**: a synthetic commit carrying the new trailer value is recognized as carve-out-exempt by
      `check_strict_quickmerge.py` (regression test), and the recipe doc change is verified against
      `check_reference_paths.py`. Source: `issues/check_strict_quickmerge_blind_to_dirty_deps_carveout_2026_07_23.md`
      (`asset_group: [meta]` — folded into `ci` per the skill's meta-sweep rule; content is quickmerge governance).
- [ ] [FIX] P1. **Close the `detect_breaking_change.py` registry-data-dict blind spot end to end.** One combined todo
      (internally sequential, single source doc): (a) spec the contract-surface allowlist extension — which
      registry-dict mutations count as breaking vs additive-OK, citing the manifest `schema_version` precedent as the
      design pattern; (b) implement the extension in `scripts/cicd/detect_breaking_change.py` and tag the 3 registry
      constants (`INSTRUMENT_TYPES_BY_VENUE`, `VENUES_BY_ASSET_GROUP`, `VENUE_DATA_TYPE_CAPABILITIES` in
      `unified-api-contracts`) as contract surface; (c) add regression cases to `test_detect_breaking_change.py`
      including the exact `23fa3a99` (OKX, SPOT_PAIR) removal fixture; (d) close the SIT coverage gap — add the
      live-registry `build_expected('cefi')` + capability/fold cross-repo invariant to `system-integration-tests`,
      resolve the `strict=False` xfail on `test_venue_to_tardis_matches_inverted_venue_mapping`; (e) reproduce
      end-to-end: confirm the post-fix differ on `23fa3a99` returns `is_breaking:true` and the new SIT invariant goes
      RED on the (OKX, SPOT_PAIR) removal; (f) once (a)-(e) land, update the breaking-differ section of
      `/codex/08-workflows/ci-cd-flow.md`. **Explicitly excludes** the doc's [DESIGN] P2 item (whether a registry-change
      promote should additionally fan out and run consumer QG, e.g. instruments-service) — that is a genuine
      blast-radius design fork, parked as an operator question (see `## Escalated to the operator`), not required for
      this todo's own done-when. **Done when**: (b)-(e) are all individually verified per their stated proof, and (f)
      lands. Source: `issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md` (all 7 todos, still
      fully unchecked since creation 2026-07-09 — genuinely never touched by any active plan).
- [ ] [SCRIPT] P2. **Fix real `sleep()`-based test waste — the non-MTDS fleet.** Mocking the clock instead of sleeping
      real wall-time, zero behavior risk, across 3 repos (excludes `market-tick-data-service`'s
      `test_sports_catalog_reader_timeout.py` — that file is ALREADY self-dispatched under
      `issues/mtds_sports_catalog_reader_timeout_test_flaky_under_contention_2026_07_27.md`, `assigned_vm: planning`; do
      not duplicate, but flag for whoever picks that task up that monkeypatching `_BLOB_TIMEOUT_SECS` down — this doc's
      proposed fix — would also resolve that doc's flakiness, since a near-zero timeout removes the wall-clock race
      entirely, not just widens the margin): (a) `unified-trading-library` —
      `test_manifest_freshness.py`/`test_agent_action.py`/`test_pipeline_heartbeat_timer.py` sleep-based waits
      (~11.65s/run); (b) `features-service` — `test_feature_cache.py` `sleep(1.1)`; (c) the smaller batch/low-value
      sleeps in `deployment-api`, `instruments-service`, `greeks-service`. **Done when**: every named test passes with
      the real sleep replaced by a mocked/monkeypatched clock and the per-repo `quality-gates.sh` stays green. Source:
      `issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md` (§ "Real sleep()-based test waste").
- [ ] [SCRIPT] P3. **CI-cost tooling: size + add the `uv` package-cache action; merge redundant ruff-ratchet
      invocations.** (a) Size the real savings of an `actions/cache@v4` step for the `uv` package cache in
      `python-quality-gates-v2.yml` BEFORE adding it (the doc's own precondition) — record the measurement, then add it
      if it's worth the added cache-restore overhead; (b) merge `check_ruff_rule_ratchet.py`'s per-rule-group full-tree
      ruff invocations into one `--select` pass. **Done when**: the cache sizing is recorded with a go/no-go decision
      (and the step added if "go"), and the ruff-ratchet checker runs measurably fewer full-tree passes with identical
      violation output. Source: `issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md` (§ tooling speed).
- [ ] [SCRIPT] P3. **Dead-code cleanup: 3 confirmed-stale deletions.** (a) `execution-service` — re-verify ~40
      files/~10,082 lines importing a pre-refactor module path are still genuinely dead, then delete; (b)
      `unified-trading-library` — delete the already-skip-marked dead test importing a moved `ConfigReloader` path; (c)
      `e2e-testing` — fix the stale `SERVICES` arrays in `run-full-pipeline.sh` referencing archived pre-merge
      `features-*-service` repos. **Done when**: (a)'s re-verification is recorded before deletion (per "delete
      deprecated code, no shims" — confirm dead first), all three repos' `quality-gates.sh` stay green post-delete, and
      (c)'s `SERVICES` array matches the live repo topology. Source:
      `issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md` (§ dead code).
- [ ] [BACKEND] P1. **Widen MTDS's ungated test coverage — fix + widen `PYTEST_UNIT_DIR`.** One combined todo
      (internally sequential, single source doc): (a) fix the 8 non-integration `tests/market_interface/unit/` failures
      (`test_defi_handlers.py` ×5, `test_defi_adapters_boost_2.py` ×2, `test_barchart_and_yahoo_adapters.py` ×1 — the
      Barchart test may simply delete per the codex's Barchart-retired citation); (b) fix the remaining 12 of the
      original 14 `tests/market_interface/adapters/**` canonical-output/write failures (databento ×12, tradfi-writes ×1,
      tardis-options ×1 minus the 2 already fixed — **verify each remaining failure first: check whether it encodes the
      OLD pre-D1/D2 contract before fixing**, per the doc's own caveat); (c) once (a) and (b) are green, widen
      `PYTEST_UNIT_DIR` to the full `market_interface` unit/adapters/clients/schema_validation/cli + `tests/cli` set
      (rule 11a: proof in the same change); (d) decide the `tests/integration/**` story (12 modules never run anywhere)
      — wire into a credentialled CI lane or mark credential-dependent ones explicitly. **Done when**: (a)-(c) are each
      individually green with the widened `PYTEST_UNIT_DIR` proven in the same commit, and (d)'s decision is recorded
      with rationale. Source: `issues/mtds_ungated_test_families_2026_07_17.md` (todos 1-4 — well cross-referenced
      across cefi/infra/ci but never actually executed by any of them per this audit's corpus-wide citation check).
- [ ] [QG] P2. **Fleet sweep: a PM quality-gate check comparing every repo's `tests/*/unit/` dirs against its
      `PYTEST_UNIT_DIR`.** So no other repo silently ends up in MTDS's pre-todo-11 situation (a whole test family never
      collected by the gate). New standalone PM script, shrinking-ratchet baseline (do not fail the gate red on existing
      fleet debt this todo doesn't fix). **Done when**: the checker exists, correctly flags a synthetic
      new-uncollected-dir case, and the baseline is seeded at today's real fleet count. Source:
      `issues/mtds_ungated_test_families_2026_07_17.md` (todo 5).
- [ ] [INFRA] P2. **Port the `${TMPDIR:-/tmp}` hardcoded-path fix to `scripts/quality-gates-base/base-library.sh`.**
      Mirrors the already-shipped `base-service.sh` fix in the same source doc — grep for the ~10+ named hardcoded
      `/tmp/` checker-capture sites in `base-library.sh`, apply the identical substitution pattern, verify `bash -n`,
      re-run `quality-gates.sh` on a library-tier repo (e.g. `unified-api-contracts`). **Done when**: every named site
      uses `${TMPDIR:-/tmp}`, `bash -n` passes, and the named library-tier repo's `quality-gates.sh` is green on a full
      tmpfs. Source: `issues/qg_hardcoded_tmp_paths_false_failures_on_full_tmpfs_2026_07_26.md` (sole open todo).
- [ ] [BACKEND] P2. **Root-cause and fix `plan-health-agent.yml`'s dead `schedule` trigger (1/200 firings since
      2026-03-07).** One combined todo (todo 2 is gated on todo 1's output, same source doc): (a) compare the workflow's
      trigger/concurrency/permissions blocks line-by-line against 2-3 reliably-firing sibling crons — the doc has
      already ruled out disabled-workflow-state, recently-added-trigger, and concurrency-group collision; the leading
      untested hypothesis is `pull_request`-trigger-volume deprioritization; escalate to GitHub support/status page only
      if no structural cause is found; (b) once root-caused, ship the fix (e.g. split the `pull_request`- triggered
      sweep into its own workflow file to remove shared-workflow contention, or adjust concurrency scoping) and verify
      via a real schedule-triggered run appearing within 48 hours of shipping. **Done when**: (a) records a root cause
      (or a documented, GH-support-escalated absence of one), and (b)'s fix is verified by an actual schedule-fired run
      post-ship. Source: `issues/plan_health_agent_dead_schedule_trigger_2026_07_27.md` (todos 1-2).
- [ ] [DOC] P2. **`monitoring_control_plane_master_2026_06_10.md` reconciliation + one bounded status check.** (a)
      Reconcile G3 (manifest-consolidator-health, still literally `- [ ]` since 2026-06-12) against what actually
      shipped: `unified_deployment_health_cockpit_2026_06_23` (status complete) delivered the underlying capability, and
      `consolidator_throughput_backlog_monitor_2026_07_09` (active, cross-cutting tranche batch2) extended it further —
      close G3 against these with an explicit cross-reference, or re-scope it to whatever residual gap remains once
      those two are read; (b) re-verify the Deferred-work row citing `cicd_contract_hardening_2026_06_01.md`'s (now
      ARCHIVED) "promote system-integration-tests LDR → main" todo — check whether the routine LDR→main drain has since
      promoted `system-integration-tests` to `main`, and if not, promote it. **Explicitly excludes** the Rollout-ratchet
      panels / G4 items (UI-touching, needs a `[UI]`-capable role + `pw:L2` gate, this batch's `assigned_role` is
      `cicd`) and the "Runtime-level deploy signal v2" P0 item (scope too open-ended for a bounded todo as currently
      written — see `## Escalated to the operator`) — both deferred. **Done when**: G3 is either closed-with-citation or
      re-scoped with a stated residual, and (b)'s promotion status is recorded (and acted on if still pending). Source:
      `monitoring_control_plane_master_2026_06_10.md` (G3 line 429, Deferred-work row line 622).

## Deferred

Tagged by WHY, per the `/ag-closeout-audit` non-batchable taxonomy.

### Conflict-gated (file-contention this round — re-triageable in batch 3+)

| id  | Item                                                                                                                                                                   | Competing claim it collided with                                                                                                                                                                                                                      |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E1  | `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md` — add BATS phase to `base-service.sh`                                                                     | Todo 1 owns `base-service.sh` this round                                                                                                                                                                                                              |
| E2  | `ci_test_content_and_tooling_speed_findings_2026_07_28.md`'s `--durations=25` addition to `base-library.sh`                                                            | Todo 11 owns `base-library.sh` this round (todo 1 already carries the `base-service.sh` half of this same item)                                                                                                                                       |
| E3  | `stale_staging_versions_manifest_2026_07_23.md` (D8) — STAGE 1.6 dormancy-aware dep gate in `quickmerge.sh`                                                            | Todo 1 owns `quickmerge.sh` this round. **Note**: this item was previously flagged "reserved for batch 2" in batch1's Deferred D8 — superseded this round by the higher-priority (P1 vs P2) sentinel-binding fix; genuinely next in line for batch 3. |
| E4  | `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` (D4) — delete redundant `pre-push-strict-quickmerge.sh` + repoint referrers in `quickmerge.sh` | Todo 1 owns `quickmerge.sh` this round; both referrer todos (batch1 todo 1, batch1 todo 18) are now done, so this is otherwise fully conflict-cleared — top of the batch-3 queue for this file.                                                       |
| E5  | `quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` steps 2-4 (D3(4)) — broaden the `live-defi-rollout` branch check                                 | Same file as todo 1; also has its own internal step-2 precondition not re-verified this round.                                                                                                                                                        |

### Operator-gated (needs a ruling, not a re-triage)

| id  | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E6  | `ldr_to_main_promote_churn_fix_verification_2026_07_27.md` — removing quickmerge.sh's PM-specific Option-B direct-PR-open step needs explicit operator sign-off first ("should PM's quickmerge stop opening its own promote PR and rely 100% on the bot") — genuine judgment call, not a re-triage. Todo 2 (the before/after churn measurement) is further gated on todo 1 landing.                                                                                                                                                                            |
| E7  | `mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md` — root-causing the 14+ confirmed DEPLOYMENT_ENV leak occurrences is explicitly NOT bounded as currently framed (5 independent investigation sessions have failed to pin the mechanism). This is the SAME underlying bug as `mtds_deployment_env_race_survives_single_worker_2026_07_23.md` (D3(3), already parked pending its own cascade-instrumentation step) — both docs explicitly say "read together, do not duplicate investigation." Stays parked on that single shared blocker. |
| E8  | `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`'s [DESIGN] P2 item — should a UAC registry-change promote additionally fan out and run consumer QG (e.g. instruments-service)? Genuine blast-radius design fork, parked rather than folded into todo 6 above.                                                                                                                                                                                                                                                                              |
| E9  | `digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md` / `post_cutover_silent_assumption_sweep_2026_07_23.md` § F4 — `digest-drift-sweep` non-convergence + `ubuntu-latest` fan-out cost. Re-verified this round: still open, unchanged since batch1's D2 (`post_cutover`'s F4 todo is still unchecked). Same file as batch1 todo 3 (done) — now technically file-available, but the non-convergence root cause itself is still unparked/unresolved, so no bounded fix exists to dispatch yet.                                                      |
| E10 | `post_cutover_silent_assumption_sweep_2026_07_23.md` § F4 — disable/fix the 4 vacuous crons (`sit-debounce-trigger`, `freeze-deferred-build-replay`, `fix-approval-timeout`, `supersede-stale-dep-update-prs`). Re-verified this round: still open, unchanged. Needs a per-cron disable-vs-fix ruling.                                                                                                                                                                                                                                                         |
| E11 | `check_strict_quickmerge_blind_to_dirty_deps_carveout_2026_07_23.md`'s Option 2 sibling docs (`mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md`, `sports_odds_ownership_registry_split_brain_...`, others) that reference the SAME dirty-deps carve-out class — out of scope for todo 5 above, which is scoped to the checker + recipe only.                                                                                                                                                                                                           |

### Role-mismatch (needs a `[UI]`-capable slot, not `cicd`)

| id  | Item                                                                                                                                                                                                                                                                                      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E12 | `ci_test_content_and_tooling_speed_findings_2026_07_28.md` — `unified-trading-system-ui` (Playwright `--project=chromium` scoping, browser-binary cache, ESLint ignore-list tightening) + `deployment-ui` (vitest jsdom→happy-dom, npm→pnpm migration). Same pattern as batch1's D20/D28. |
| E13 | `monitoring_control_plane_master_2026_06_10.md` — Rollout-ratchet panels (deployment-api reader + deployment-ui panel) + G4 (folds into the same panel work).                                                                                                                             |

### Too-large-or-risky / needs a design pass first

| id  | Item                                                                                                                                                                                                                                                                                                                                                                                                                  |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E14 | `monitoring_control_plane_master_2026_06_10.md` — "Runtime-level deploy signal v2" (P0, line 253): resolve what is actually RUNNING (Cloud Run revisions / deployment registry / VM heartbeats) vs `main` HEAD and surface the diff. Scope is open-ended as written (which signals, what "surface the diff" means concretely — new panel vs alert) — needs a scoping/design pass before it can become a bounded todo. |

### Low-priority / near-moot

| id  | Item                                                                                                                                                                                           |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E15 | `ci_test_content_and_tooling_speed_findings_2026_07_28.md` — resume/track the stalled 3-agent PM-cost-breakdown workflow angle. Doc's own note calls this "explicitly low-priority/near-moot." |

## Escalated to the operator (parked, not guessed)

Three questions, quotes/locations/options/recommendation, not resolved autonomously:

1. **E8** — should a UAC registry-change promote (breaking-change differ scope) additionally fan out and run consumer QG
   (e.g. instruments-service) beyond today's producer-repo-only gate? Recommendation: not required for todo 6's core fix
   to be complete; worth a follow-up once todo 6 lands and the blast-radius tradeoff can be evaluated against real
   fan-out cost data.
2. **E14** — does `monitoring_control_plane_master`'s "Runtime-level deploy signal v2" (P0) need a dedicated
   scoping/design session before it's AO-dispatchable, or is there a narrower done-when the operator already has in mind
   that would make it bounded? Recommendation: scoping session first — the current line-253 text names 3+ candidate
   signal sources with no stated priority among them.
3. **E6** — should quickmerge.sh's PM-specific Option-B direct-PR-open step be removed in favor of 100% bot-driven drain
   (matching every other repo), per `ldr_to_main_promote_churn_fix_verification_2026_07_27.md`'s measured churn finding?
   Recommendation: yes (removes a measured, real CI-run churn source with no stated benefit to keeping Option-B), but
   this changes the fleet's core shipping gatekeeper for one specific repo, so it needs explicit sign-off before any
   worker touches `quickmerge.sh` on this basis.

## Codex SSOTs (read before executing any todo)

- `/codex/08-workflows/ci-cd-flow.md` — pipeline / quickmerge / strict-quickmerge / gate set / release + wheel
- `/codex/06-coding-standards/quality-gates.md` — how gates run; never `pytest` directly; ratchet-baseline convention
- `/codex/04-architecture/ci-alerting.md` — `notify-slack.yml` carrier, `dedup_key` + cooldown, recovery-gated
  all-clears
- `/codex/06-coding-standards/ui-testing-layers.md` — why E12/E13 need a `[UI]`-capable role, not `cicd`
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `plans/active/task_template.md` §4 — finalize-plan-coverage rule

## Progress Log

- **2026-07-29** — Drafted by `/ag-closeout-audit ci` (autonomous mode, `ag_closeout_auditor` scheduled worker, slot 7).
  Phase 0: `ci_consolidated_closeout_2026_07_25.md` confirmed archived 2026-07-28 (its own single todo done); covering
  set re-derived as `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (active, 14/30 todos done) + its gated finalize
  (draft). Found + worked around a real bug in `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py`: its
  `ao`/`ci`/`infra` membership branch derives candidates from the tranche's consolidated-closeout doc's own citations
  (`_closeout_paths()`, globs `plans/active/`), which silently returns zero once that doc is archived — stale relative
  to the skill's own documented 2026-07-27 schema migration (asset_group `ci` is now the primary membership signal for
  this tranche, not the old closeout-citation workaround). Filed
  `issues/generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md` and
  worked around via a direct frontmatter sweep. Found 31 docs with `asset_group` containing `ci` (29 after excluding
  batch1+finalize); cross-referenced batch1's citations (basename AND truncated-prose-paraphrase matching, since batch1
  sometimes elides long filenames with `…`) plus self-dispatch status (`assigned_vm: planning` + `status: active/open`)
  to narrow to 9 genuinely never-touched candidates, PLUS folded in 1 already-known `asset_group: [meta]` doc
  (`mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`, identified via
  `ag_closeout_audit_scope_widening_triage_2026_07_26.md`'s completed corpus-wide meta-sweep — but classified
  `orphaned_partial_coverage`/not-bounded, see E7, not drafted here). Phase 1: all 9 read end-to-end via a `Workflow`
  (one agent per doc) — 7 `orphaned_never_touched`, 2 `orphaned_partial_coverage`. Also re-checked batch1's own
  conflict-gated Deferred items D2-D6 per the iterative-drain methodology: D5 (dirty-deps carve-out) was RULED by the
  operator TODAY (2026-07-29, same day as this audit — a genuine coincidence, not this audit's own doing); D7/D3(1)
  (sentinel ENVIRONMENT binding) and D18 (promotion-lag alert) were already resolved per batch1's own 2026-07-28
  gate-cleanup notes but never extracted into a todo until now; D2, D6, and D3's remaining sub-items remain genuinely
  gated (re-verified against their source docs' current state, unchanged). Phase 3: conflict-check found
  `scripts/quality-gates-base/base-service.sh` claimed by 3 candidates (todo 1, `pm_bats_tests`, the `--durations=25`
  half) and `base-library.sh` by 2 (todo 11, the `--durations=25` other half) — rationed one todo per file. Also caught
  a genuine near-duplicate: `ci_test_content_and_tooling_speed_findings_2026_07_28.md`'s proposed
  `test_sports_catalog_reader_timeout.py` fix is the SAME FILE as the already-self-dispatched
  `mtds_sports_catalog_reader_timeout_test_flaky_under_contention_2026_07_27.md` (`assigned_vm: planning`) — excluded
  from todo 7 to avoid dispatching a competing fix to already-claimed work; noted for that task's own worker instead. 14
  todos drafted, 15 items deferred (E1-E15), 3 escalated to the operator. Nothing shipped, nothing flipped to `active`.
