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
- [x] ✅ [CODE] P2. Mine unified-trading-system-ui backtest views for the analytics surface before extending the
      analytics schema section further Source:
      `plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md` — unified-trading-pm: mined
      all 5 backtest-analytics views (`lib/types/backtest-analytics.ts`'s shared `BacktestAnalytics` bundle,
      `backtest-vs-operating-panel.tsx`'s layered cost-of-reality attribution model, `backtest-comparison-panel.tsx`'s
      per-`slot_label` breakdown table, and the two lighter KPI-card list views). Full inventory + reuse recommendations
      recorded in the source issue doc's 2026-08-14 Progress Log entry; its own checkbox flipped there too. No code
      changes — read-before-build mining pass, per the todo's own scope.
- [x] ✅ [CODE] P2. Verify current DeFi canonical-migration-defi-rebuild fleet completion and consolidated-manifest
      freshness state Source: `plans/active/issues/pipeline_smoke_sweep_findings_2026_07_20.md` — unified-trading-pm
      (this batch): **BOTH VERIFIED LIVE 2026-08-14, no code changes needed.** (1) Fleet completion: zero live
      `canonical-migration*` VMs (`gcloud compute instances list`); full GCS `vm-logs/` listing (via
      `get_storage_client()`, no gsutil) shows `canonical-migration-defi-rebuild-20260810-204358` is the latest
      `-rebuild-*` entry, no relaunch since; its raw `run.log` independently confirms terminal SUCCESS (`rc=0`,
      `exit_code=0`, `total_shards: 5832208`, all 5 chunks through `2026-12-31`, elapsed 12780.2s) — matching
      `defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md`'s "Resolution" section. (2) Manifest
      freshness: live read of `market-data-tick-defi-prd-central-element-323112`'s consolidated
      `_index/availability_index.parquet` blob age ≈250s at check time — well inside DeFi's 3600s
      `AG_STALENESS_BUDGET_SEC` override, only 2 outstanding per-VM shards. **Byproduct finding, fixed same commit**:
      while tracing the rebuild chain, found the OOM doc mislabeled which VM actually OOM'd (`-180141` was cited, but
      the real OOM signature — `rc=137` — belongs to `-141813`; `-180141` was instead killed by the unrelated
      rogue-delete incident documented in `claude_code_agent_deletes_active_canonical_migration_vm_2026_08_10.md`) —
      corrected inline + Progress Log entry added to that doc. Full evidence trail in that doc's 2026-08-14 Progress Log
      entry.
- [x] ✅ [CODE] P2. Determine the root cause of sports data being ~4 weeks stale Source:
      `plans/active/issues/pipeline_smoke_sweep_findings_2026_07_20.md` — unified-trading-pm (this batch):
      **ROOT-CAUSED, no ongoing outage (verified live 2026-08-14).** Live GCS/manifest verification (via
      `unified_trading_library.cloud_interface.get_storage_client()`, no gsutil) of the sports consolidated manifest
      (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 15.65M rows) shows
      **zero real capture gap**: every daily-cadence data_type (`standings`, `teams`, `injuries`, `odds`, `matches`) has
      a `captured` row for every single day from 2026-06-01 straight through today 2026-08-14 (75/75 dates in-window for
      standings/teams); `fixtures`/`fixtures_schedule`/`fixtures_outcomes` run through 2026-12-06 (forward-poll
      lookahead); overall `written_at` max is today 18:06 UTC. The Cloud Scheduler cron `uts-prod-sports-scheduler-cron`
      (`*/5 * * * *`, ENABLED) driving Cloud Run job `uts-prod-sports-scheduler` (created 2026-04-29, well before the
      07-20 finding) is firing and completing successfully every 5 min (`gcloud run jobs executions list` confirms 5
      consecutive clean executions at check time); the dedicated per-tier Cloud Scheduler crons
      (`uts-prod-sports-fixtures-{midnight,6am,noon,6pm}-t1-schedule`,
      `uts-prod-sports-enrichment-{soccer-football-info,     transfermarkt,footystats}-daily`,
      `features-service-sports-daily-trigger`) are all ENABLED and current. **So the 2026-07-20 "~4 weeks stale, last
      captured 2026-06-24" reading was itself a false-stale VERDICT, not a real outage** — same tooling-defect class as
      this doc's own §1 (3 other false/misleading verdicts from the same sweep session). Root cause of the false
      reading: the sports bucket's consolidated-manifest merge cycle structurally runs 400-460s (5.4M+ row incremental
      merge) against the reader's 120s default `MANIFEST_CONSOLIDATED_STALENESS_SEC` budget — a distinct-but-adjacent
      defect independently root-caused the very next day
      (`plans/archive/issues/manifest_consolidator_stale_sports_bucket_2026_07_21.md`, resolved) and fixed by bumping 14
      sports launchers' staleness override to 1800s. The smoke-sweep's ad-hoc recency check (an interactive-session
      query, not a checked-in script — no matching tool found under `market-tick-data-service/scripts`,
      `instruments-service/scripts`, or `deployment-service/scripts`) had no such override and is exactly the read shape
      most exposed to landing mid-merge or on the stale-fallback path. No code fix needed here — the adjacent
      consolidator-staleness defect was already fixed 2026-07-21, and live data confirms sports capture has been
      continuous since at least 2026-06-01. This closes the source doc's "Still open" sub-item 3 (sports staleness cause
      unconfirmed) and the 2026-08-06 na-eligibility-audit's outstanding re-verify instruction; checkbox reconciliation
      back into `pipeline_smoke_sweep_findings_2026_07_20.md` happens in this batch's paired finalize plan, per this
      batch's own frontmatter note.
- [x] ✅ [CODE] P2. dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md -- parallelize
      exit_code_fleet_monitor.py/heartbeat_stall_watcher.py's sweep() via ThreadPoolExecutor Source:
      `plans/active/issues/plan_reconciler_findings_all_2026_08_12.md` — **ALREADY SHIPPED, duplicate dispatch, no new
      code needed (verified 2026-08-14).** `deployment-service@069ced1412` ("perf(dp-monitors): parallelize per-VM GCS
      reads in exit-code + heartbeat sweeps", backend_engineer slot-28 2026-08-13) already parallelizes both sweeps'
      pure per-VM I/O via `ThreadPoolExecutor` (`_SWEEP_IO_MAX_WORKERS`), keeping classify/route/emit sequential to
      protect shared state — exactly this todo's ask. Confirmed live in the current worktree: both
      `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py` and `.../heartbeat_stall_watcher.py` import
      `ThreadPoolExecutor` and wrap their per-VM read phases in it (`_SWEEP_IO_MAX_WORKERS=16`); `069ced1412` verified
      an ancestor of current `deployment-service` HEAD. The source issue doc's own `archive_exempt: true` note
      (2026-08-13) already flags this exact batch's item as one of two known duplicate "parallelize sweep()" dispatches
      spawned from the same source finding — this flip closes that duplicate. The source doc itself stays open (further
      follow-on classify/route/emit-phase work is tracked there, out of this todo's ThreadPoolExecutor-specific scope).
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
- [x] ✅ [CODE] P2. check_na_corpus_ratchet.py -diff-base fenced-code-block checkbox-overcounting bug (Section 3 log)
      Source: `plans/active/issues/plan_reconciler_findings_all_2026_08_12.md` — unified-trading-pm (this batch):
      **FIXED.** `check_na_corpus_ratchet.py`'s `--diff-base` mode hand-duplicates its own `_CHECKBOX_RE` (module
      comment explains why: it must not depend on `generate_na_doc_tranche_inventory.py`'s disk-only `_iter_docs()` for
      its git-ref path) and that duplicate carried no fence-awareness, so a checkbox-shaped line quoted inside a ` ``` `
      code block (e.g. a doc citing another plan's todo list as evidence) was counted as a real open todo in both
      `_counts_map_live()` and `_counts_map_at()`. Same underlying bug class as
      `plans/active/issues/na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md` (which tracks
      `generate_na_doc_tranche_inventory.py`'s own separate, still-open copy of the same gap — out of this todo's scope)
      and identical to this same plan's `Item J` (Source:
      `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`) — both todos name the exact same
      `_CHECKBOX_RE`-has-no-fence-awareness defect in this same script; fixing it here closes both. Added
      `_count_open_checkboxes_fence_aware()` (toggle-flag fence skip, same shape as `check_na_duplicate_staleness.py`'s
      own `FENCE_RE` toggle) and wired it into `_na_open_todos_from_text()`. 6 new unit tests in
      `test_check_na_corpus_ratchet.py` pin: a real open checkbox counts, a fenced one doesn't, an all-fenced doc
      reports 0 (the exact live shape from the 2026-08-02 issue doc), the `* [ ]` star-bullet variant still matches when
      unfenced, and `_na_open_todos_from_text` end-to-end. Verified live: `_count_open_checkboxes_fence_aware` returns 0
      on an all-fenced sample, 2 on an unfenced `-`/`*` mixed sample.
- [x] ✅ [CODE] P2. Item A -- retag deployment_api_quickmerge_blocked_pre_existing_test_failures_2026_08_04.md
      asset_group cross-cutting->ui Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md` —
      unified-trading-pm (this batch): retagged `asset_group: [cross-cutting]` → `[ui]` in
      `plans/archive/issues/deployment_api_quickmerge_blocked_pre_existing_test_failures_2026_08_04.md` (dominant owner
      — deployment-api repo, both broken tests, and the re-ship target) plus a `sports` cross-reference note on todo 2
      (its fix touches a sports-domain registry despite the doc's own tag), per
      `ag_closeout_audit_cross_cutting_parked_2026_08_06.md`'s `[WORKER REC]`. Progress Log entry added to the target
      doc.
- [x] ✅ [CODE] P2. Item G -- correct stale G3/G10 status text in batch_live_reconciliation_service_audit_2026_05_27.md
      citing the successor doc Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md` —
      unified-trading-pm@df3a908b1a: **G10 corrected.** Added a CORRECTED 2026-08-14 annotation to §7.1's G10 line (was
      "still genuinely open as of 2026-07-27") citing `blrs_g3_g10_rescope_2026_07_28.md` (fully archived, 4/4 todos
      `[x]`) and `citadel_paper_batch_live_reconciliation_2026_06_19.md`'s `P3.BLRS3` (flipped `[x]`), matching the
      existing G3 correction's format/style. **G3 needed no change** — a prior `/plan-reconcile` pass already corrected
      its status line on 2026-08-12.
- [x] ✅ [CODE] P2. Item H -- live re-verify citadel_paper_batch_live_reconciliation_2026_06_19.md P9.2's UAC
      version-drift citation against current UAC Source:
      `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md` — unified-trading-pm@f32a181dcc:
      **RE-VERIFIED live 2026-08-14 — self-resolved, no fix needed.** The cited `unified-api-contracts=0.26.0` (local)
      vs `0.27.0` (main) pairing from the 2026-06-20 provenance no longer exists at any version: UAC's current tag is
      `v0.124.0`; strategy-service's `pyproject.toml` constraint `unified-api-contracts>=0.123.0,<1.0.0` (path/editable
      dep, not a frozen pin) is satisfied. Live check-only run of `run-version-alignment.sh` (no `--fix`) confirms
      "Alignment OK" — no strategy-service/UAC drift flagged. Two unrelated, currently-open drift conditions exist (PM
      self-version drift; a fleet-wide 21-repo local-vs-origin/main `staging_versions` lag) but neither is the cited
      pairing — out of scope. P9.2 in the target doc flipped `[x]` with the full re-verify citation.
- [x] ✅ [CODE] P2. Item J -- fix check_na_corpus_ratchet.py's --diff-base fenced-code-block checkbox-overcounting regex
      bug Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md` —
      unified-trading-pm@4484ad1200: **ALREADY SHIPPED, verified 2026-08-14 (same underlying defect this batch's own
      preceding "Section 3 log" todo above already closed).** `_count_open_checkboxes_fence_aware()` (toggle-flag fence
      skip) is wired into `_na_open_todos_from_text()` in `scripts/plan-hygiene/check_na_corpus_ratchet.py`, replacing
      the bare `_CHECKBOX_RE` scan that previously double-counted checkbox-shaped lines inside fenced code blocks.
      Commit verified ancestor of `origin/live-defi-rollout`. No new code needed — this checkbox closes the duplicate
      dispatch.
- [x] ✅ [CODE] P2. Item K -- add the missing backlog todo to
      plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md once grace lifts Source:
      `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md` — unified-trading-pm (this batch):
      **ALREADY DONE, verified live 2026-08-14 — no new todo needed.** Grace has lifted (target doc's `locked_by` is
      empty; last commit touching it, `02aa7912cf`, is dated 2026-08-12, >12h before this check). The real backlog todo
      the source doc's 4 Progress Log entries referenced already exists in the target doc: the
      `check_prosewrap_padding.sh` `--diff-base <ref>` conversion P3 todo (added + shipped
      `unified-trading-pm@e89d4931e5`, 2026-08-11 — its own text states "This closes the LAST of the 4 originally-named
      option-(c) checks"). Confirmed live: `check_prosewrap_padding.sh` carries a real `--diff-base <ref>` usage line +
      diff-scoped-mode implementation block (not just a doc claim), and `e89d4931e5` verified an ancestor of current
      `origin/live-defi-rollout` HEAD. No gap remains to backfill.
- [x] ✅ [CODE] P2. Item L -- backfill the real sha in over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md's
      placeholder evidence citation Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md` —
      **ALREADY FIXED, no new code needed (verified 2026-08-14).** A prior `/plan-reconcile` pass (2026-08-12) already
      backfilled the target doc's `over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md` line ~138 todo with
      the real sha, replacing the literal `<sha>` placeholder: it now reads "Implemented `unified-trading-pm@d4f7fab9d8`
      (2026-08-02 — CORRECTED 2026-08-12 /plan-reconcile...)". Live-verified this commit is genuine:
      `git log -1     d4f7fab9d8` resolves (author ikennaigboaka, 2026-08-02 23:27:33Z),
      `git merge-base --is-ancestor d4f7fab9d8     origin/live-defi-rollout` confirms it's landed, and
      `git show --stat d4f7fab9d8` confirms it touches `scripts/plan-hygiene/check_line_caps.sh` (41 lines changed) —
      matching the cited "small-marker-append carve-out" work. No gap remains; this item's finding (Item L in
      `plan_reconciler_findings_cross_cutting_2026_08_10.md`) is closed by an earlier session's fix, not this one.
- [x] ✅ [CODE] P2. Item N -- fix 3 docs' stale 'closeout over 1000-line hard cap' citations (now 720 lines) Source:
      `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md` — same commit as this flip: corrected
      the stale "already over the 1000-line hard cap" citations in all 3 docs
      (`promote_ref_orphaned_on_manual_pr_close_2026_08_06.md` summary+body,
      `unified_trading_system_ui_block_list_parity_test_failing_2026_08_04.md` Progress Log,
      `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md` Progress Log — traced its indirect
      reference through the deadlock doc, confirmed same claim) — live-verified
      `cross_cutting_consolidated_closeout_2026_07_25.md` is 733 lines (under the 1000-line hard cap). Text-only
      correction per Item N's narrow scope; did not execute the newly-unblocked archival/repoint follow-ups (left
      tracked in their own docs).
- [x] ✅ [CODE] P2. De-cohort the freshness thresholds (e.g. 90d + hash(path) % 14 jitter, or stagger last_reviewed on
      bulk authoring) Source: `plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md` — unified-trading-pm
      (this batch): `check_codex_doc_freshness.py`'s effective staleness window is now `staleness_days + jitter(path)`,
      where `jitter` is a stable sha256-derived 0-13 day offset over the doc's WORKSPACE-RELATIVE path (never the
      builtin `hash()`, which is `PYTHONHASHSEED`-salted and would move a doc's cutover day on every run/slot). Threaded
      through `_check_parsed`/`_check_doc` via an optional `workspace_root` param (defaults to `None` → falls back to
      `str(path)`, so existing direct-call unit tests keep working unmodified); `main()` passes the resolved `pm_root`
      so the same doc jitters identically across every `.tabs/<N>/` slot worktree. Only changes WHEN the
      already-advisory `stale` reason fires — the three blocking authoring reasons are untouched. 6 new unit tests
      added, incl. a same-stamp 30-doc cohort proving a partial (not all-or-nothing) tip at the un-jittered cutover day
      and full tip 13 days later, and a same-relative-path cross-worktree-prefix identity check.
      `.venv/bin/python3 -m pytest` on the test file: 51/51 green.
- [x] ✅ [CODE] P2. Write up the correctness-ratchet-vs-hygiene-ratchet distinction (currently only in commit messages)
      as a doc Source: `plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md` — unified-trading-pm (this
      batch): new SSOT `/codex/06-coding-standards/ratchet-correctness-vs-hygiene.md` — defines the two kinds (a
      correctness ratchet asserts a claim TRUE, must never be re-baselined by a passer-by; a hygiene ratchet tracks
      calendar/prose debt, may be absorbed with the debt named in the commit), gives the one-question decision test, a
      worked-examples table (evidence-backed-completion, adapter contract regression, CODEX_MAX_VIOLATIONS, SHA
      reachability = correctness; codex-doc-freshness `stale`, cross-reference links, prosewrap = hygiene), and notes
      how it composes with (not duplicates) `check_codex_doc_freshness.py`'s existing clock-vs-authoring split. Linked
      from `quality-gates.md`'s `related:`. Source doc's own todo intentionally left untouched per this batch's stated
      policy (checkbox reconciliation into source docs happens in the paired finalize plan).
- [x] ✅ [CODE] P2. Implement the safe-field allow-list + UnsafeConfigChangeError guard in
      strategy-service/strategy_service/config_reloaders.py per the operator-confirmed 2026-08-12 ruling (option A)
      Source: `plans/active/issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md` —
      strategy-service@c688512912: added `SAFE_STRATEGY_RELOAD_FIELDS = frozenset({"strategy_params"})` +
      `UnsafeConfigChangeError` (RuntimeError subclass) to `config_reloaders.py`. `_on_strategies_reload` now diffs the
      incoming `StrategyDomainConfig` against the currently active snapshot field-by-field (skipping the very first
      load, which has no baseline); a `strategy_params`-only change still atomic-swaps as before, an
      `enabled_strategies` change (different archetype/code path) raises `UnsafeConfigChangeError` and the previously
      active config stays in effect — `FieldFilteredCallbackRegistry.notify` (UTL) already catches `RuntimeError` from a
      reload callback and logs it, so the reload is rejected without crashing the process; a restart is still required
      to actually apply an archetype change (this guard does not auto-restart). 5 new unit tests in
      `tests/unit/test_config_reloaders.py` (`TestStrategySafeFieldAllowList`): safe field hot-reloads, unsafe field
      raises + keeps prev config, the registry-level end-to-end swallow path, first-load bypass. Updated
      `/codex/04-architecture/live-strategy-config-hot-reload.md` (this batch, same commit set) to stop describing the
      guard as unimplemented design intent — the "What can hot-reload safely" table and "Live = batch" section now
      reflect the strategies-domain enforcement; the instruments-domain hot-swap contradiction remains open/unenforced
      (out of this todo's scope — still tracked in the source issue doc). Evidence: `bash scripts/quality-gates.sh`
      green (sentinel = HEAD `c688512912edae9a2efc254282bb1749404aa68e`, 5992 passed / 0 failed); quickmerge verified
      `c6885129` ancestor of `origin/live-defi-rollout`.
- [x] ✅ [CODE] P2. FLEET-WIDE: instruments-store _index v9-COLUMN populate for cefi/tradfi/defi (+ prediction source) —
      pattern-identical to the already-shipped sports v9-column populate script Source:
      `plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md` — unified-trading-pm (this batch):
      **ALREADY SHIPPED + APPLIED LIVE, no new code needed (verified 2026-08-14).**
      `instruments-service/scripts/populate_is_index_v9_2026_06_19.py` (`instruments-service@96fd4260`) is the
      pattern-identical fleet-wide script this todo asked for — it already exists, covers all 4 AGs
      (cefi/defi/tradfi/prediction), and was `--apply`'d live on 2026-06-19 (confirmed via
      `_index/snapshots/pre_is_v9_{ag}_2026_06_19.parquet` present in all 4 buckets). Live-re-verified via a fresh
      `--asset-group` dry-run against each of the 4 prod `_index` objects today: `schema_v9_pct` / `pipeline_mode_pct` /
      `source_pct` / `asset_group_pct` all **100.0%** for prediction (31,625 rows, source_dist:
      polymarket_gamma_api/polymarket_clob/instruments_service/kalshi), tradfi (27,516 rows, 100% instruments_service),
      cefi (85,064 rows, 100% instruments_service), and defi (138,327 rows, 100% instruments_service). `captured` counts
      unchanged in every dry-run (no data loss). Byproduct observation: defi's dry-run also reported
      `venue_changes: 120088` from the SAME script's bundled venue-canonicalisation step (`canonicalise_venue_column`) —
      this is DISTINCT from the v9-column scope of this todo and is already tracked under the existing active defi
      venue-canonicalization plans (e.g. `plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`,
      `plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`), so no new issue doc filed here.
- [x] ✅ [CODE] P2. Key execution policies by (client_id, slot_label) — §B Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` — **ALREADY SHIPPED, no new code
      needed (verified 2026-08-14).** `execution-service@c2053c47` already implements this: `v2/policy_resolver.py`'s
      `binding_key(client_id, slot_label)` (`f"{client_id}:{slot_label}"`) plus `ExecutionPolicyResolver` (bindings dict
      keyed by that pair → `policy_ref`, resolved via `resolve()`/`resolve_config_algorithm()`) and
      `v2/policy_spec.py`'s `ExecutionPolicyDomainConfig.bindings` (the GCS-hosted binding table, same key shape).
      Confirmed live in the current worktree; `c2053c47` verified an ancestor of `origin/live-defi-rollout`.
- [x] ✅ [CODE] P2. Give the execution-policy registry a GCS loader + DomainConfigReloader subscription — §B Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` — **ALREADY SHIPPED, no new code
      needed (verified 2026-08-14).** `execution-service@c2053c47` already added
      `execution_service/v2/policy_reloader.py` following the existing three-reloader pattern
      (instruments/clients/rate-limits in `config_reloaders.py`):
      `start_execution_policy_reloader(config_store_bucket, project_id)` builds a
      `DomainConfigReloader[ExecutionPolicyDomainConfig]` (domain=`"execution-policies"`), registers `_on_policy_reload`
      (atomic-swap into `_active_policy_resolver`, exposed via `get_active_policy_resolver()`), and calls
      `start_watching()`; `stop_execution_policy_reloader()` mirrors it. Confirmed live in the current worktree:
      `config_reloaders.start_domain_config_reloaders`/`stop_domain_config_reloaders` call the policy reloader
      start/stop alongside the other three (same function, same commit lineage); `execution_service/api/app.py` calls
      `start_domain_config_reloaders` at service startup; `execution_service/v2/__init__.py` exports
      `get_active_policy_resolver`/`start_execution_policy_reloader`/`stop_execution_policy_reloader`; wrapper-level
      coverage in `tests/unit/test_config_reloaders.py` (empty-bucket-disabled + stop-when-none paths exercise the
      policy-reloader call sites). `c2053c47` verified an ancestor of `origin/live-defi-rollout`.
- [x] ✅ [CODE] P2. Wire policy evaluation into the live execution path (select_algorithm takes config_algorithm from
      the resolved policy) — §B Source: `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` —
      **ALREADY SHIPPED, no new code needed (verified 2026-08-14).** `execution-service@c2053c47` (same commit as this
      batch's two preceding "ALREADY SHIPPED" todos) already wires this: `HandlerRegistry.select_algorithm()`
      (`execution_service/engine/routing/handler_registry.py:149-174`) falls back to
      `resolve_config_algorithm(self._policy_resolver, client_id, slot_label, policy_context)` when no explicit
      `config_algorithm` is supplied, feeding the resolved policy's `then_algo` into the same `config_algorithm` hook
      `select_algorithm()` already validates against `ALGOS_BY_INSTRUCTION_TYPE`; the v2 `TradeHandler`/`SwapHandler`
      path (`execution_service/v2/handlers.py:152-156`) calls the identical `resolve_config_algorithm` helper via
      `get_active_policy_resolver()`. Confirmed live in the current worktree (`git log` shows `c2053c47` as the
      introducing commit; `git rev-list --left-right --count HEAD...origin/live-defi-rollout` = `0 0`, i.e. fully landed
      on `origin/live-defi-rollout`). Test coverage:
      `tests/unit/test_handler_registry.py::test_select_algorithm_resolves_config_algorithm_from_policy` (explicitly
      cites "plan § G1") + `tests/unit/v2/test_policy_resolver.py`. This closes the same underlying gap as this batch's
      later "G1 — feed config_algorithm through the already-threaded selector hook" todo (§D framing of the identical §B
      ask) — no separate fix needed there either.
- [x] ✅ [CODE] P2. Add the reference price to the shared instruction envelope with its mark mode — §C Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`

      **DONE 2026-08-14 (slot-21, infra).** `unified-api-contracts@c869c35bcb`: added `reference_price: Decimal | None`
                      + `reference_price_mark_mode: ReferencePriceMarkMode` (new StrEnum: `STATIC_AT_SEND` |
                      `UPDATE_AS_UNDERLYING_MOVES`, default `STATIC_AT_SEND`) to `StrategyInstructionEnvelope`
                      (`internal/architecture_v2/schemas.py`) — not just `QuoteInstruction`, which now narrows the envelope's
                      optional field to its own pre-existing required `Decimal` (unaffected). Re-exported `ReferencePriceMarkMode`
                      via `unified_api_contracts.internal`. This is the field the strategy-service `reference_price` param-schema
                      section (`refprice_mark_mode`/`refprice_source`/`refprice_max_drift_bps`, shipped inert in `4762c211ab`)
                      configures once a construction site sets it — wiring construction sites + the actual repricing/drift-cap
                      behavior is out of this todo's scope (separate open §C todos: "prove the standalone-backtest property",
                      "reconcile ref price with the ε=0 spine"). 3 new unit tests
                      (`tests/internal/unit/test_instruction_envelope_reference_price.py`): envelope defaults (`None`/
                      `STATIC_AT_SEND`), a `TradeInstruction` (no dedicated field of its own) carrying both fields, and
                      `QuoteInstruction.reference_price` staying required. Regression-verified against the local editable UAC
                      install: execution-service's `test_quote_maintenance.py` + `test_router_and_handlers.py` (34 tests, both
                      construct `QuoteInstruction`) unaffected. **Byproduct fix, separate commit same session**: found + fixed a
                      pre-existing UAC QG red (`tests/test_deployment_ui_cross_repo_invariant.py` expecting a `builds_history`
                      route module deployment-api deliberately deleted per `ui_satellite_ao_dispatch_batch4_2026_08_13.md`) —
                      verified pre-existing on a clean tree at `HEAD~1` before touching it; a peer (slot-2,
                      `unified-api-contracts@8771a4b7`) landed the identical fix independently in the same window, so mine was
                      dropped via `git rebase --skip` during reconciliation (kept the peer's better-documented version, zero
                      duplicate diff). `bash scripts/quality-gates.sh` green on the rebased HEAD (sentinel = `c869c35bcb`).

- [x] ✅ [CODE] P2. Subscribe strategy-service to ClientDomainConfig — §D Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` — **ALREADY SHIPPED, no new code
      needed (verified 2026-08-14).** `strategy-service@c55b586c9c` already wires this (docstring cites it as "B1,
      2026-08-13"): `strategy_service/config_reloaders.py` imports `ClientDomainConfig`, maintains a module-level
      `_client_reloader: DomainConfigReloader[ClientDomainConfig]` + `_active_clients` snapshot, `_on_clients_reload()`
      atomic-swaps the config, invalidates `ClientConfigStore`'s cache, and fans out to
      `register_client_change_callback()` registrants with the same shard-isolation discipline as the instrument-change
      loop; `start_domain_config_reloaders()` starts the `clients` domain reloader alongside `strategies`/`instruments`
      — mirroring execution-service's existing three-reloader pattern exactly, per this todo's own ask. Confirmed live
      in the current worktree; `c55b586c9c` verified an ancestor of `origin/live-defi-rollout`.
- [x] ✅ [CODE] P2. Resolve execution-service's missing config.py (rename-vs-document decision applied consistently) —
      §D Source: `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` —
      execution-service@ff12d5fb87: **DOCUMENT, not rename.** `execution_service/service_config.py` (already at the
      900-line hard cap) is execution-service's `config.py`-equivalent — schema + defaults, hot-reloadable via
      `config_reloaders.py`. Renaming it to `config.py` would collide with the existing `execution_service/config/`
      PACKAGE (JSON backtest/grid `ConfigLoader`, unrelated) — confirmed live: a package always shadows a same-named
      sibling module, so the rename broke every `get_execution_config`/`ExecutionServicesConfig` import via a
      circular-import error when attempted and was reverted the same session. Full rationale documented in
      `execution_service/config/__init__.py`'s module docstring (where a reader looking for `config.py` lands first),
      pointing to `service_config.py` as the real target — kept out of `service_config.py` itself to respect its line
      cap.
- [x] ✅ [CODE] P2. Close the Bybit API-key reload asymmetry in DATA_SOURCE_TO_SECRET — §D Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` — **ALREADY SHIPPED, no new code
      needed (verified 2026-08-14).** This todo's literal ask — fix UAC's `DATA_SOURCE_TO_SECRET` registry so it can
      express Bybit — is already done: `unified-api-contracts@8c72b501` added the bare `"BYBIT": "bybit"` entry to
      `VENUE_TO_DATA_SOURCE` and `"bybit": "bybit-trade-api-key"` to `DATA_SOURCE_TO_SECRET`
      (`unified_api_contracts/canonical/canonical_mappings.py`), with its own comment explicitly citing "plan § D, close
      the Bybit API-key reload asymmetry" as the motivation. Confirmed live in the current worktree (both entries
      present) and `8c72b501` verified an ancestor of `origin/live-defi-rollout`. The bespoke `_BybitKeyReloader` in
      `execution-service/execution_service/config_reloaders.py` (landed separately via `execution-service@c2053c47`,
      also already an ancestor of `origin/live-defi-rollout`) remains, but its own docstring now documents why: it
      resolves the Bybit **trade-scope secret pair with a fallback to the unscoped pair**
      (`_resolve_bybit_credentials`), a capability the generic single-secret-name `ApiKeyReloader` structurally does not
      implement — a real, documented capability gap distinct from the registry gap this todo targeted, not an accidental
      "silently unmaintained" duplicate. No further registry or reloader change is warranted by this todo's scope.
- [x] ✅ [CODE] P2. G1 — feed config_algorithm through the already-threaded selector hook Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` — **ALREADY SHIPPED, no new code
      needed (verified 2026-08-14).** `execution-service@c2053c47` (confirmed ancestor of current HEAD `ff12d5fb87`)
      already does exactly what G1 asks: resolves the per-`(client_id, slot_label)` execution policy and feeds its
      `then_algo` into the existing `config_algorithm` hook. Verified at BOTH real call sites, not just the
      `HandlerRegistry.select_algorithm()` wrapper this batch's earlier "Wire policy evaluation into the live execution
      path — §B" todo already confirmed: `execution_service/v2/handlers.py`'s `TradeHandler.handle()` and
      `SwapHandler.handle()` (lines 180/200) both call `_resolve_selected_algorithm(instruction, self.action)`, which
      resolves `get_active_policy_resolver()` and calls
      `resolve_config_algorithm(resolver, instruction.identity.     client_id, instruction.identity.strategy_instance_id, context)`
      — the v2 live-instruction path's own concrete caller of the hook. This closes the same underlying gap as that
      earlier §B todo (identical §D framing of the same ask); no separate code change is warranted.
- [x] ✅ [CODE] P2. Delete the shadow BookType (J1) and import UAC's enum Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` — **ALREADY SHIPPED, no new code
      needed (verified 2026-08-14, slot-21).** `execution-service@a75d953ece` already deletes the shadow `BookType`
      class in `execution_service/cli/domain_runners.py` and imports UAC's SSOT enum
      (`from unified_api_contracts.internal import BookType`), with `validate_book_type()` now validating against the
      enum itself. Confirmed live in the current worktree (module imports `BookType` from UAC, no local shadow class
      remains) and `a75d953ece` verified an ancestor of `origin/live-defi-rollout`. This is the exact fix the source
      doc's own J1 row already documents as resolved (line 521 of the source doc). No further action.
- [x] ✅ [CODE] P2. Add a participation cap to the passive fill path, filtered to the filling side per PB.8 — §K Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` — execution-service@f3402a7c11:
      **wired, not just primitive.** `TradeMatcher.capped_passive_fill_quantity` / `filling_side_volume` /
      `should_fill_passive_order` already existed (built earlier the same day) and were unit-tested as pure functions,
      but no live matcher consumed them — confirmed via a full-repo grep, the only caller was the primitive's own test
      file. Wired into `L1Matcher._match_passive()` (`execution_service/matching_engine/engine.py`): the LIMIT (passive)
      branch now participation-caps against `kwargs['trades']` (`Sequence[CandleTrade]`) when supplied, filtered to the
      FILLING side per PB.8 (a resting BUY fills only against aggressive SELLs at price <= limit, never total candle
      volume), via `kwargs['participation_cap_pct']` (default `1` = uncapped, sourced from the execution-policy
      `then_params` per `policy_resolver.participation_cap_from_params` — same routing point already established for
      `SubCandleVWAPMatcher`). Falls back to the prior full-fill-at-price behavior when no trade tape is supplied
      (fidelity-ladder graceful degradation, same discipline as § I's book-columns → sub-candle VWAP → OHLC bar rungs).
      A raised `ValueError` from an out-of-range cap is caught and returned as a rejected `MatchResult` (never
      propagated) to preserve `BaseMatcher.match()`'s never-raises contract. IOC/MARKET (aggressive) and FOK are
      unaffected — the cap only applies to the passive path. 8 new tests in
      `tests/unit/matching_engine/test_l1_matcher_participation.py`: no-trades/empty-trades fallback, cap-binds partial
      fill, requested-below-cap full fill, default-uncapped-but-still-filling-side-only (proves the PB.8 over-count this
      closes), FOK/IOC unaffected, sell-side symmetry, and the invalid-cap-value fails-loud-without-raising case.
      Evidence: `bash scripts/quality-gates.sh` green (sentinel = HEAD `f3402a7c1105c486d3d50e1c671aeb14741ebd49`);
      quickmerge verified `f3402a7c11` ancestor of `origin/live-defi-rollout`.

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
