---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 13 part 2 — 2026-08-13
summary: >-
  Extraction batch from the cross-cutting tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep —
  37 live conflict-cleared, bounded/deterministic items (39 total todos, 2 marked out-of-scope, see below) pulled
  directly from 11 source docs (RECLASSIFY_SPLIT bounded items from the NA audit,
  orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Rescoped 2026-08-13
  (operator scoping instruction): 2 MDPS/features-service-backfill duplicate items (already independently marked
  out-of-scope in their home tranche batches) with no manifest-canonical/migration angle marked [x] OUT-OF-SCOPE
  (checkbox format per todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md). Each todo cites
  its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation back into each
  source doc happens in the paired finalize plan). Conflict-checked against every existing active batch/finalize plan
  for this tranche via basename-citation cross-reference before drafting — no item here duplicates ground an existing
  dispatched Todos entry already claims.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/mtds_main_promotion_stall_and_qg_alert_redispatch_2026_08_11.md,
    /plans/archive/issues/mtds_type_ignore_ratchet_blocks_prek_intel_mac_fix_2026_08_03.md,
    /plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md,
    /plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md,
    /plans/active/issues/pipeline_smoke_sweep_findings_2026_07_20.md,
    /plans/active/issues/plan_reconciler_findings_all_2026_08_12.md,
    /plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md,
    /plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md,
    /plans/active/issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md,
    /plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md,
    /plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 5.6
estimate_calibrated_ai_days: 4.4
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# cross-cutting satellite AO dispatch batch 13b — 2026-08-13

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] ✅ [CODE] P2. Diagnose why no successor promote PR opened for market-tick-data-service (check
      ldr_to_main_fleet_promote.sh per-repo logic and ahead_by trend) Source:
      `plans/active/issues/mtds_main_promotion_stall_and_qg_alert_redispatch_2026_08_11.md` —
      unified-trading-pm@0f26818135: **DIAGNOSED — correct behavior, not a stall.** Fleet bot ran + evaluated MTDS each
      tick (verbatim run 31477434767 09:22:47Z:
      `SKIP market-tick-data-service: main tree == LDR tree (content-identical)`). The `ahead_by` 1384→1436 is
      squash-skew SHA noise, not unpromoted content: LDR carries 1436 original commit SHAs the squash promote never
      replays onto main; `git rev-parse main^{tree} == LDR^{tree}` (byte-identical). No successor PR opened because
      there was nothing to promote. Code fix: SKIP line now prints the compare ahead_by so this reads as a
      self-documented correct decision. A successor PR (#963) did open once real content landed 08-12, then merged
      stream #963-#980; #981 (current LDR tip cbc6531b) is open + mergeable(blocked on its own v2).
- [x] ✅ [CODE] P2. Read unified-trading-ci's python-quality-gates-v2.yml on: trigger config to find and fix the ~15-min
      redispatch, or migrate the Slack step to the dedup'd notify-slack.yml carrier Source:
      `plans/active/issues/mtds_main_promotion_stall_and_qg_alert_redispatch_2026_08_11.md` — **ALREADY FIXED, no new
      code needed (verified 2026-08-14).** The redispatch was root-caused: the promote-PR head is a per-SHA frozen ref
      (`promote/<repo>/<sha12>`), and PM's drain bot supersedes a promote PR roughly every ~15min — almost exactly
      matching the observed 9:34/9:49 double-page cadence — so every successor PR minted a brand-new dedup key and a
      still-red condition re-paged on each supersession. The Slack step was already routed through the dedup'd
      `notify-slack.yml` carrier (`dedup_key: qg-fail:{repo}:{base_ref-for-PR|ref_name-for-push}`, `cooldown_min: 120`)
      before this todo was even drafted. Three peer-session commits on `unified-trading-ci` fully closed the gap:
      `45eabc2` (2026-08-12, 15-min debounce before alerting on a promote-PR failure — most self-resolve via supersede),
      `e499f9d` (tier-3 AO escalation at 30min via `promote_qg_failure`), and `ec6d421` (2026-08-13, REDESIGNED the
      debounce to track the underlying CONDITION across PR supersessions by walking real `quality-gates-v2` run history
      for a continuous-failure streak, instead of sleeping 15min and re-checking one ephemeral PR number — the original
      per-PR debounce was structurally unreachable since the drain bot superseded the PR before the sleep ended, exactly
      the bug this todo's `~15-min` symptom points at). Confirmed live on `unified-trading-ci@67698d8`
      (`.github/workflows/python-quality-gates-v2.yml` — `debounce-promote-qg-fail` job derives `duration_min` from run
      history and only fires `notify-qg-fail` once the streak is genuinely ≥15min old, with a 120min cooldown after
      that). No further action.
- [x] ✅ [CODE] P2. Investigate and document why standalone quality-gates.sh --no-fix treats the local type:ignore
      ratchet (STEP 5.94/5.95) as non-fatal while quickmerge's internal re-gate treats the identical finding as fatal
      Source: `plans/archive/issues/mtds_type_ignore_ratchet_blocks_prek_intel_mac_fix_2026_08_03.md` —
      `market-tick-data-service@9effa3529c`. **ROOT-CAUSED + DOCUMENTED (2026-08-14).** Not a --no-fix-vs-full-mode
      difference (STEP 5.94/5.95 has no branch on that flag) — it's a MOVING-HEAD attribution window: both invocation
      paths run the identical script/flags, but 5.94/5.95 scope to `git diff <merge-base> HEAD`, and quickmerge's
      `--agent` re-gate only fires after its sentinel-invalid retry rebases local HEAD onto whatever a peer slot pushed
      meanwhile — widening the window enough to surface a peer commit's net-new bare `# type: ignore` that an earlier,
      narrower-scoped standalone run never saw. Full mechanism + code-line citations documented in the issue doc's todo
      3 and as a code comment at `market-tick-data-service/scripts/quality-gates.sh` (diff-scoped-attribution helper
      docstring). Issue doc flipped `status: open -> resolved` (all 3 todos closed).
- [x] ✅ [CODE] P2. Resolve the diff base to the branch's own last-gated point instead of a fixed origin/main proxy
      Source: `plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md` —
      unified-trading-pm@715a90d7ac: `run_hygiene_sweep.sh`'s `DIFF_BASE_REF` now resolves from the triggering CI event
      instead of a fixed `origin/main` — a `push` (only fires on `push:[main]`) uses the event's `before` SHA read from
      `$GITHUB_EVENT_PATH`; a `pull_request` uses its own `$GITHUB_BASE_REF`; any other trigger
      (`workflow_dispatch`/schedule/unset, incl. the LDR-health-check dispatches and the cron entrypoint) stays
      baseline+buffer. Both resolved refs are best-effort fetched then only applied once verified locally, so an
      unresolvable base fails safe to baseline+buffer rather than reading all pre-existing debt as new. Promote-PR
      exclusion unchanged, still wins over base resolution. Verified via 5 simulated scenarios (push/PR/promote-PR/
      workflow_dispatch/unresolvable-SHA) against the extracted resolution block — all matched expected behavior.
- [x] ✅ [CODE] P2. Add a detector for a non-convergeable (monotonically-growing-violation-count) ratchet gate distinct
      from an ordinary retryable failure Source:
      `plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md` —
      agent-orchestrator@197c5ca521: Added `detect_non_convergeable_gate()` + `_extract_violation_count()` +
      `_root_key_violation_history()` in `server/escalation.py` — walks a wall's `root_key` re-escalation chain (the
      same chronic-wall lineage `_resolve_root_key` already threads) and flags `resolution="non_convergeable"` when the
      parsed violation count grows for `NON_CONVERGEABLE_MIN_STREAK` (3) consecutive attempts, paging immediately
      instead of waiting out the normal `PAGE_AFTER_REESCALATIONS` grace period. `notify_escalation_unresolved`
      (`server/notifications/slack.py`) now takes a `non_convergeable` kwarg and renders a distinct "NON-CONVERGEABLE
      gate" header. 4 new tests in `tests/test_escalation.py` (pure extractor/detector + a real-SQLite-session
      root_key-chain walk + a full wiring test asserting the first-miss immediate page). Evidence:
      `bash scripts/quality-gates.sh` green (3640 pytest passed, 336 vitest passed); quickmerge verified `197c5ca52`
      ancestor of `origin/live-defi-rollout`.
- [x] ✅ [CODE] P2. Fix the ldr-to-main-promote.yml rate mismatch that lets a fast-failing check manufacture an
      unbounded stream of superseded PRs Source:
      `plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md` —
      unified-trading-pm@7840229ddf: the doomed-run detector superseded an in-flight promote PR on the FIRST tick that
      observed any failed QG-slice check-run, even mid-run — since `checks` fails in ~3.5min, ticks are 15min apart, and
      LDR gets ~4 commits/3min, every tick minted a fresh frozen head and restarted validation from zero (measured PR
      #2713→#2717, 5 PRs in ~35min), and this path never reached the genuine-failure escalation (only fires from the
      completed-run MSTATE=blocked branch, which a doomed-and-closed PR never gets to). Now requires
      DOOMED_STREAK_THRESHOLD=3 consecutive doomed observations of the SAME open PR (tracked via the bot's own
      "doomed-tick" PR comments — a fresh PR after supersede starts back at 0) before superseding, and fires the same
      ldr_main_qg_failure orchestrator escalation once confirmed. Evidence: `bash scripts/quality-gates.sh` green
      (sentinel = HEAD 99bfba4a9); YAML + embedded bash syntax verified (`python3 -c yaml.safe_load` + `bash -n` on the
      extracted `run:` block); quickmerge verified `7840229ddf` ancestor of `origin/live-defi-rollout`.
- [x] ✅ [CODE] P2. Extend the proven --diff-base pattern to check_ag_closeout_linkage Source:
      `plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md` —
      unified-trading-pm@96b33046f9: added `--diff-base <ref>` mode to `check_ag_closeout_linkage.py`, git-backed
      (`ls-tree`/`cat-file --batch`, no live-disk read) rebuild of the orphan graph/closeout-family/body-blob at the
      base ref, compared by PATH IDENTITY against the HEAD orphan set (not message text, since this check's wording can
      legitimately reword the same orphan e.g. archived-coordinator phrasing). Wired into `run_hygiene_sweep.sh`'s
      shared `DIFF_BASE_REF` guard alongside the other four consumers. Verified: `--diff-base HEAD`/`HEAD~50` both 0 new
      (baseline currently 0 orphans); unresolvable ref falls back safe (empty base-orphan set); `--only`/`--tranche`
      modes unaffected; full `run_hygiene_sweep.sh --no-regen` green (0 hard failures) with the new wiring live;
      `bash scripts/quality-gates.sh` sentinel = HEAD `a4e15c8411`; quickmerge verified `96b33046f9` ancestor of
      `origin/live-defi-rollout`.
- [x] ✅ [CODE] P2. Make check_ui_api_flow_coverage.py hard-fail instead of silently exiting 0 when its manifest file is
      missing Source:
      `plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md` —
      unified-trading-pm@d5ea8d0755: **root-caused + fixed.** The checker script itself already returned a distinct exit
      code 2 for a missing/unparseable manifest (verified: reproduced live,
      `python3     check_ui_api_flow_coverage.py --workspace-root <missing> --warning-only` → exit 2, unaffected by
      `--warning-only`). The actual gap was the CALLER: `quality-gates.sh`'s post-gate wraps the checker in
      `--warning-only` (which forces the coverage-gap path to always exit 0), so under that invocation any non-zero exit
      can only mean a config error — yet the wrapper's `if/else` only tested zero-vs-nonzero and routed exit 2 into the
      same non-blocking `log_warn` as an ordinary coverage gap, so a missing manifest never failed CI at all. Fixed
      `scripts/quality-gates.sh`'s FLOW_CHECKER block to capture the real exit code and hard-fail (`log_fail` +
      `exit 1`) specifically on exit 2; other non-zero exits remain non-blocking. Verified both paths in isolation
      (manifest-missing → exit 1; manifest-present → exit 0/pass) before shipping. Evidence:
      `bash     scripts/quality-gates.sh` green (sentinel = HEAD `d5ea8d0755`, UI/API flow coverage check itself passed
      4/4 journeys with the real manifest present); quickmerge verified `d5ea8d0755` ancestor of
      `origin/live-defi-rollout`.
- [x] ✅ [CODE] P2. Fix the client_context.py docstring (remove the nonexistent max_leverage field, correct
      min_balance_per_venue naming) Source:
      `plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md` —
      strategy-service@3146cfd068: `risk_limits` docstring now lists the real fields
      (`max_position_usd`/`max_drawdown_pct`/`max_order_size_usd`), notes `min_balance_per_venue` lives on
      `ClientsYamlEntry` (not inside `risk_limits`), removes the nonexistent `max_leverage`, and points at
      `unified_api_contracts.canonical.domain.strategy.clients_yaml_schema` as the schema SSOT.
- [x] ✅ [CODE] P2. Instantiate or explicitly waive clients.yaml for every factory-registered archetype that can run
      Source: `plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md` —
      deployment-service@e355c14ad3: strategy-service's `clients_yaml_coverage.uncovered_archetypes()` gate (already
      shipped, with its own test `test_clients_yaml_coverage_gate.py`) measured 30 of 32 factory-registered archetypes
      with neither a `clients.yaml` nor a waiver. Created `clients_waiver.yaml` under
      `deployment-service/configs/strategy/{archetype}/` for all 30 (only `carry_staked_basis` and
      `arbitrage_price_dispersion` have real per-client data — no fabricated client entries). Verified
      `uncovered_archetypes()` now returns `[]`. `bash scripts/quality-gates.sh` green (sentinel = HEAD
      `e355c14ad3875c4af73d67a7010e6c42d0aea5ad`); quickmerge verified `e355c14ad3` ancestor of
      `origin/live-defi-rollout`.
- [x] ✅ [CODE] P2. Record the resolved per-client config surface ownership in codex
      (per-client-isolation-architecture.md) Source:
      `plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md` — unified-trading-pm: added
      a "Config surface ownership" section to `/codex/04-architecture/per-client-isolation-architecture.md` with the
      three-surface table (wallet_mapping.json / clients.yaml / strategy_service configs) + live-vs-not verdicts, the
      two known gaps (archetype-first keying, missing leverage/venue-selection/coin-universe fields), and a pointer to
      the operator's 2026-08-12 `(client_id, slot_label)` target-state ruling in the source issue doc.
- [ ] [CODE] P2. Mine unified-trading-system-ui backtest views for the analytics surface before extending the analytics
      schema section further Source:
      `plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md`
- [ ] [CODE] P2. Verify current DeFi canonical-migration-defi-rebuild fleet completion and consolidated-manifest
      freshness state Source: `plans/active/issues/pipeline_smoke_sweep_findings_2026_07_20.md`
- [ ] [CODE] P2. Determine the root cause of sports data being ~4 weeks stale Source:
      `plans/active/issues/pipeline_smoke_sweep_findings_2026_07_20.md`
- [ ] [CODE] P2. dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md -- parallelize
      exit_code_fleet_monitor.py/heartbeat_stall_watcher.py's sweep() via ThreadPoolExecutor Source:
      `plans/active/issues/plan_reconciler_findings_all_2026_08_12.md`
- [x] [CODE] P2. dp_vm_002_mdps_cefi_2021_silent_zero_false_positive_2026_08_11.md -- re-launch mdps-cefi-2021 sharded
      backfill from checkpoint **OUT-OF-SCOPE FOR THIS BATCH (2026-08-13, operator scoping instruction)** —
      MDPS/features-service backfill/recompute work is excluded from this batch unless manifest-canonical or
      migration-related. The underlying item remains open in its own source doc, untouched by this batch/commit. Source:
      `plans/active/issues/plan_reconciler_findings_all_2026_08_12.md`
- [x] [CODE] P2. sports_features_2026_backfill_launch_window_was_today_2026_08_10.md -- clamp per-year sports features
      backfill launcher's end_date **OUT-OF-SCOPE FOR THIS BATCH (2026-08-13, operator scoping instruction)** —
      MDPS/features-service backfill/recompute work is excluded from this batch unless manifest-canonical or
      migration-related. The underlying item remains open in its own source doc, untouched by this batch/commit. Source:
      `plans/active/issues/plan_reconciler_findings_all_2026_08_12.md`
- [ ] [CODE] P2. check_na_corpus_ratchet.py -diff-base fenced-code-block checkbox-overcounting bug (Section 3 log)
      Source: `plans/active/issues/plan_reconciler_findings_all_2026_08_12.md`
- [ ] [CODE] P2. Item A -- retag deployment_api_quickmerge_blocked_pre_existing_test_failures_2026_08_04.md asset_group
      cross-cutting->ui Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. Item G -- correct stale G3/G10 status text in batch_live_reconciliation_service_audit_2026_05_27.md
      citing the successor doc Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. Item H -- live re-verify citadel_paper_batch_live_reconciliation_2026_06_19.md P9.2's UAC version-drift
      citation against current UAC Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. Item J -- fix check_na_corpus_ratchet.py's --diff-base fenced-code-block checkbox-overcounting regex
      bug Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. Item K -- add the missing backlog todo to
      plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md once grace lifts Source:
      `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. Item L -- backfill the real sha in over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md's
      placeholder evidence citation Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. Item N -- fix 3 docs' stale 'closeout over 1000-line hard cap' citations (now 720 lines) Source:
      `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. De-cohort the freshness thresholds (e.g. 90d + hash(path) % 14 jitter, or stagger last_reviewed on bulk
      authoring) Source: `plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md`
- [ ] [CODE] P2. Write up the correctness-ratchet-vs-hygiene-ratchet distinction (currently only in commit messages) as
      a doc Source: `plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md`
- [ ] [CODE] P2. Implement the safe-field allow-list + UnsafeConfigChangeError guard in
      strategy-service/strategy_service/config_reloaders.py per the operator-confirmed 2026-08-12 ruling (option A)
      Source: `plans/active/issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md`
- [ ] [CODE] P2. FLEET-WIDE: instruments-store _index v9-COLUMN populate for cefi/tradfi/defi (+ prediction source) —
      pattern-identical to the already-shipped sports v9-column populate script Source:
      `plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`
- [ ] [CODE] P2. Key execution policies by (client_id, slot_label) — §B Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Give the execution-policy registry a GCS loader + DomainConfigReloader subscription — §B Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Wire policy evaluation into the live execution path (select_algorithm takes config_algorithm from the
      resolved policy) — §B Source: `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Add the reference price to the shared instruction envelope with its mark mode — §C Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Subscribe strategy-service to ClientDomainConfig — §D Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Resolve execution-service's missing config.py (rename-vs-document decision applied consistently) — §D
      Source: `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Close the Bybit API-key reload asymmetry in DATA_SOURCE_TO_SECRET — §D Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. G1 — feed config_algorithm through the already-threaded selector hook Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Delete the shadow BookType (J1) and import UAC's enum Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Add a participation cap to the passive fill path, filtered to the filling side per PB.8 — §K Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
