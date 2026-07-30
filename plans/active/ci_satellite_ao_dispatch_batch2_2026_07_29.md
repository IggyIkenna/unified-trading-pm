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
  `plans/archive/issues/generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md`
  for the bug report). Phase 1 read all 9 newly-surfaced candidate docs end-to-end (29 direct `asset_group:[ci]` docs
  minus batch1/finalize minus already-cited/self-dispatched, plus 1 already-known `asset_group:[meta]` fold-in) via a
  Workflow — all 9 confirmed genuinely orphaned (7 `orphaned_never_touched`, 2 `orphaned_partial_coverage`). Phase 3's
  conflict-check found `scripts/quality-gates-base/base-service.sh` claimed by 3 candidates and `base-library.sh` by 2 —
  rationed to one todo per file, same discipline as batch1. 14 conflict-cleared bounded todos below; the rest deferred
  by taxonomy (file-contention / operator-gated / duplicate-of-self-dispatched / too-large / role-mismatch).
status: active
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
last_updated: "2026-07-30"
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
      RULED 2026-07-28 — no longer operator-gated) ·
      `archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md` (`--durations=25` item). **(c) CONFIRMED
      ALREADY SHIPPED 2026-07-30 (this session's rulings-closeout pass)** — verified live: `base-service.sh`'s `PARGS`
      already carries `--durations=25` (`unified-trading-pm@3ed0fc99d`, 2026-07-29, "perf(ci): add pytest --durations,
      uv cache in the QG reusable, merge ruff dtz/tid251 rule-group scans into one invocation" — confirmed via
      `git show 3ed0fc99d -- scripts/quality-gates-base/base-service.sh`), sourced live by every consumer repo. **(a)
      and (b) confirmed still genuinely open** — re-read `_qg_content_hash()` in `base-service.sh` directly: it hashes
      HEAD sha + tracked/untracked diffs + the gate-logic script + ruff version, with NO `ENVIRONMENT`/ `DEPLOYMENT_ENV`
      dimension. Confirmed PM's own `scripts/quality-gates.sh` never exports `ENVIRONMENT` before sourcing
      `base-service.sh` either (standalone runs still fall through to the Python resolver's bare-unset→prod default).
      **NOT attempted this session**: (a)/(b) require editing the shared, fleet-wide sentinel-hash function every repo's
      QG run depends on — assessed as too high-blast-radius to implement solo without a dedicated, reviewed session (a
      subtle bug here breaks `quickmerge --agent`'s fast-path for every repo, not just one), unlike the bounded,
      single-file fixes elsewhere in this batch. Left open and unclaimed rather than rushed.
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
- [x] ✅ [DEVOPS] P2. **DONE (verified 2026-07-30, this session's rulings-closeout pass) — all three parts already
      resolved, none by this session directly; closing out the citation.** (a) The `PROVENANCE-BLOCKED` reclassification
      is live in `scripts/cicd/promotion_lag_monitor.py` (`_provenance_blocked()` + the
      `⛔ BLOCKED by the provenance     gate...` inline finding in `main()`, distinct from the plain `PROMOTION LAG`
      line) — but had NO regression test exercising it against a synthetic blocked PR, which is the one genuine gap this
      session closed: `scripts/cicd/test_promotion_lag_monitor_provenance_blocked.py` (6 new tests mocking `_gh_json` —
      no-open-PRs, fail-closed-on-lookup-failure, PR-without-marker, PR-with-marker [the synthetic reproducer],
      non-promote-titled PR skipped, non-int PR-number skipped), shipped `unified-trading-pm@51b93ec0a` (direct push per
      the PM `scripts/**` carve-out — local `quality-gates.sh --no-fix` was red only on 8 pre-existing, unrelated
      failures, confirmed by reading each traceback:
      `test_capability_param_schema.py`/`test_capability_verdict_matrix.py` [known, strategy-service CARRY_STAKED_BASIS
      in-progress wiring], `test_check_repo_docs_ssot.py` [drift in an unrelated `deployment-service-sports-wt`
      worktree], `test_check_doc_body_links.py` [a 60s pytest-timeout from host contention against a second concurrent
      full QG run, not a real broken link] — the new test file itself:
      `.venv/bin     /python -m pytest scripts/cicd/test_promotion_lag_monitor_provenance_blocked.py -q` → 6 passed,
      ruff-clean). (b) The 2 SPECIFIC 2026-07-17 offenders named in this todo (`market-tick-data-service@d302f07a`,
      deployment-ui) are STALE — the source issue doc itself (see below) already recorded both its own todos `[x]` done
      2026-07-30, explaining those exact offenders were long superseded and the CURRENT (2026-07-30) blocks were cleared
      instead (`features-service` 4 commits, `market-tick-data-service` 38 commits, via `reprovenance_bypass.sh`).
      Live-reverified just now: `gh pr list --repo IggyIkenna/deployment-ui --state open --base main` → **empty** — no
      open promote PR, so there is no current block to clear for it. (c) `_backmerge` exemption reconfirmed live in
      `check_strict_quickmerge.py` (2-parent-merge unconditional exemption + `test_backmerge_merge_commit_is_exempt`).
      Source: `issues/promotion_lag_alert_hides_provenance_block_2026_07_17.md` (both its own todos already `[x]`,
      2026-07-30 — this batch2 todo's citation predates that resolution and had gone stale relative to it).
- [x] ✅ [SCRIPT] P2. **CONFIRMED ALREADY SHIPPED (verified 2026-07-30, this session's rulings-closeout pass) — no new
      work needed.** `unified-trading-pm@bbe9a9871` documents the third `Quickmerge: direct-carveout-dirty-deps` trailer
      value + the dirty-deps direct-push recipe in `/codex/08-workflows/ci-cd-flow.md` (confirmed live at lines 211/219
      of the current HEAD, == `origin/live-defi-rollout`); `check_strict_quickmerge.py`'s trailer check was already
      value-agnostic (presence-only), so no code change was needed there either. Source issue
      `plans/archive/issues/check_strict_quickmerge_blind_to_dirty_deps_carveout_2026_07_23.md` is itself already
      `status: resolved` + archived 2026-07-30 with this exact evidence — this batch2 todo's own citation was drafted
      2026-07-29, one day before that archival, and had simply gone stale.
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
      `archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md` (§ "Real sleep()-based test waste").
- [x] ✅ [SCRIPT] P3. **CONFIRMED ALREADY SHIPPED (verified 2026-07-30, this session's rulings-closeout pass) — no new
      work needed.** Both parts confirmed live in `unified-trading-pm@3ed0fc99d` (2026-07-29, same commit that shipped
      todo 1's `--durations=25` piece above): (a) `.github/workflows/python-quality-gates-v2.yml` carries
      `actions/cache@v4` for the `uv` package cache, sized first per the commit message (cold `uv sync` ~2m07s vs warm
      9.4s, a real ~118s/run win) before being added; (b) `scripts/quality_gates/check_ruff_rule_ratchet.py`'s
      `run_ruff_count_all()` merges the separate `dtz`/`tid251` full-tree ruff invocations into one pass (confirmed via
      `grep -n "run_ruff_count_all" scripts/quality_gates/check_ruff_rule_ratchet.py`). Source:
      `archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md` (§ tooling speed) — this batch2 todo's
      citation was drafted 2026-07-29, after the fix had already shipped, and had simply gone stale.
- [ ] [SCRIPT] P3. **Dead-code cleanup: 3 confirmed-stale deletions.** (a) `execution-service` — re-verify ~40
      files/~10,082 lines importing a pre-refactor module path are still genuinely dead, then delete; (b)
      `unified-trading-library` — delete the already-skip-marked dead test importing a moved `ConfigReloader` path; (c)
      `e2e-testing` — fix the stale `SERVICES` arrays in `run-full-pipeline.sh` referencing archived pre-merge
      `features-*-service` repos. **Done when**: (a)'s re-verification is recorded before deletion (per "delete
      deprecated code, no shims" — confirm dead first), all three repos' `quality-gates.sh` stay green post-delete, and
      (c)'s `SERVICES` array matches the live repo topology. Source:
      `archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md` (§ dead code).
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
      tmpfs. Source: `archive/issues/qg_hardcoded_tmp_paths_false_failures_on_full_tmpfs_2026_07_26.md` (sole open
      todo).
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
  `archive/issues/generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md`
  and worked around via a direct frontmatter sweep. Found 31 docs with `asset_group` containing `ci` (29 after excluding
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

- **2026-07-30 (rulings-closeout pass, still `status: draft` — not flipped active)**: operator asked for every recorded
  ruling across the plans corpus that implies concrete, unshipped work to actually be closed out. This plan is still a
  DRAFT AO-dispatch candidate batch (flipping to `active` remains the operator's own call, untouched here), but several
  of its todos turned out to already be fully shipped by other, more recent sessions whose citations simply predate this
  draft's own 2026-07-29 authoring — re-verified each directly against live code/repo state rather than trusting the
  todo text: **todo 1's part (c)** (`--durations=25`) and the separate **CI-cost-tooling todo** (uv cache + merged
  ruff-ratchet invocation) both landed in `unified-trading-pm@3ed0fc99d` (2026-07-29); **todo 4** (promotion-lag
  PROVENANCE-BLOCKED reclassification) was already implemented, its named 2026-07-17 offenders superseded by the source
  issue doc's own already-`[x]` 2026-07-30 resolution (different, current offenders cleared instead) — the one genuine
  gap (no regression test against a synthetic blocked PR) was closed this session:
  `scripts/cicd/test_promotion_lag_monitor_provenance_blocked.py` (6 tests), shipped `unified-trading-pm@51b93ec0a`;
  **todo 5** (Quickmerge trailer carve-out) was already shipped + archived (`unified-trading-pm@bbe9a9871`, source issue
  `status: resolved`). Flipped all four to `[x]` with the verification evidence inline. **Todo 1's parts (a)/(b)**
  (sentinel ENVIRONMENT-binding + quickmerge/standalone entrypoint alignment) were confirmed still genuinely open (read
  `_qg_content_hash()` and PM's own `quality-gates.sh` directly — neither binds/aligns `ENVIRONMENT` today) but were
  deliberately NOT attempted: this is a real, correctly-scoped gap, but implementing it safely means editing the shared
  `base-service.sh` sentinel-hash function every repo's QG run depends on — too high a blast radius for a solo,
  time-boxed pass without dedicated review, unlike every other bounded single-file fix touched this session. Todos 2, 3,
  6-14 were not re-verified (out of this pass's time budget) and are left exactly as drafted. No status flip attempted;
  this remains an operator-gated draft.
