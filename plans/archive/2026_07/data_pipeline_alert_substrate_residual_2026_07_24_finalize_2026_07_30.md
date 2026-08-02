---
doc_type: plan
title: Finalize — data-pipeline alert-substrate residual close-out
summary: >-
  Gated close-out twin for `data_pipeline_alert_substrate_residual_2026_07_24.md`, which was reclassified `assigned_vm:
  NA → planning` by the 2026-07-30 `/na-eligibility-audit cross-cutting` run. Holds the post-ship verification +
  archival ritual for that plan's 3 remaining todos (the per-source SOURCE_RATE_LIMITED / SOURCE_KEY_POOL_EXHAUSTED
  event, the deployment-ui streaming-events pane, and the UTL DP_DAILY_DIGEST / DP_HYGIENE_SUMMARY string constants).
  Flipped to `status: active` 2026-07-30 once the source plan's last todo (the market-tick-data-service
  SOURCE_RATE_LIMITED/SOURCE_KEY_POOL_EXHAUSTED item) landed — `market-tick-data-service@7f42c557`.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, deployment-ui, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit, data-pipeline, alerting, observability]
related:
  [
    /plans/archive/2026_07/data_pipeline_alert_substrate_residual_2026_07_24.md,
    /plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: [data_pipeline_alert_substrate_residual_2026_07_24]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  /na-eligibility-audit cross-cutting, 2026-07-30 — RECLASSIFY verdict on
  data_pipeline_alert_substrate_residual_2026_07_24.md. Phase-2 conflict-check CLEAR for the 3 OPEN todos:
  cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md's claims against this doc all land on items already `[x]`
  here (the Phase-4 writer invariants, the alerting reliability trio, and the dp-audit terraform apply).
---

# Finalize — data-pipeline alert-substrate residual close-out

> **ARCHIVED (2026-07-30) — complete.** All 3 todos done (routing verification, UI live-verification, source-plan
> archival). Superseded by nothing — this twin + its source plan
> (`data_pipeline_alert_substrate_residual_2026_07_24.md`) are both now record-only under `plans/archive/2026_07/`.

> **Gated twin** (`gate_on_depends: true`). Do NOT start until every todo in
> [`/plans/archive/2026_07/data_pipeline_alert_substrate_residual_2026_07_24.md`](/plans/archive/2026_07/data_pipeline_alert_substrate_residual_2026_07_24.md)
> is `- [x]` with cited evidence. Authored by the 2026-07-30 `/na-eligibility-audit` reclassification pass per
> [`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`](/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md)
> § 1(b).

## Why this exists

The source plan is the residual tail of the shipped emit→route→escalate alert substrate. Its 3 remaining todos are
bounded code/UI work, which is why the NA audit reclassified it. Two of them, though, only become REAL once they are
observed end-to-end in prod — a registered event that never routes, or a UI pane that renders nothing, is exactly the
"shipped but not operationally shipped" failure this workspace's plans-run-to-actual-completion rule exists to catch.
This twin holds that verification plus the archival ritual.

## Todos

- [x] ✅ [DATA] P1. **Verify the new rate-limit/health events actually ROUTE, not just emit.** Once
      `SOURCE_RATE_LIMITED{source, venue, http_429_count}` + `SOURCE_KEY_POOL_EXHAUSTED` are emitted by MTDS, confirm
      each has a matching rule in the UAC `DATA_PIPELINE_ALERT_RULES` registry and lands in `#data-pipeline-alerts` —
      not the generic INCIDENT catch-all. This is the exact defect class already recorded on this plan's sibling (the
      `DP_FLEET_MONITOR_RUN_*` events that fell through to the catch-all because they were never registered, fixed
      `unified-api-contracts@92e068ea`). **Done when**: a real or injected 429-storm produces a routed
      `#data-pipeline-alerts` post, with the rule ids cited. Repos: market-tick-data-service, unified-api-contracts. —
      **alerting-service@823b75d**. Confirmed both event names are already correctly registered in UAC
      `DATA_PIPELINE_ALERT_RULES` (`unified_api_contracts/canonical/crosscutting/alerting/rules.py:1362-1363`):
      `DP-RATE-001` → `DP_SOURCE_RATE_LIMITED` (WARN, AUTO_RECOVER) and `DP-RATE-002` → `DP_KEY_POOL_EXHAUSTED`
      (CRITICAL, PAGE_OPERATOR) — these are the ACTUAL event names MTDS emits (`market-tick-data-service@7f42c557`'s
      `ThegraphKeyPoolRotator`/`DatabentoIPRateLimiter`, confirmed via
      `test_acquire_hit_limit_emits_dp_source_rate_limited` in
      `market-tick-data-service/tests/market_interface/unit/test_databento_key_cache_and_config.py`), not the plan's
      shorthand `SOURCE_RATE_LIMITED`/`SOURCE_KEY_POOL_EXHAUSTED`. Traced
      `alerting_service.notifiers.router.route_event` (`router.py:679-690`): `data_pipeline_rule_for(event_name)`
      exact-matches both against `DATA_PIPELINE_ALERT_RULES` and short-circuits to `_route_data_pipeline_event` — the
      #data-pipeline-alerts mirror — BEFORE the generic catch-all can see them, i.e. the `DP_FLEET_MONITOR_RUN_*` defect
      class does not recur here. Added an injected 429-storm regression test proving the routed post end-to-end (no
      prior router-level test existed for these two events specifically):
      `test_dp_source_rate_limited_injected_429_storm_routes_to_mirror_not_page` (WARN → mirror only, no page) and
      `test_dp_key_pool_exhausted_injected_storm_routes_to_mirror_and_pages` (CRITICAL → mirror + PagerDuty/Telegram
      page) in `alerting-service/tests/unit/rules/test_data_pipeline_rules.py`, plus a registry-lookup test asserting
      the `DP-RATE-001`/`DP-RATE-002` registry ids. 16/16 tests green (5 new); full `quality-gates.sh` green, shipped
      via `quickmerge --agent`.
- [x] ✅ [UI] P2. **Confirm the streaming-events pane renders a real VM event stream.** The source plan's `[UI] P0`
      ships the pane; this verifies it against live data rather than mock — per-AG/per-VM tail, honest empty-state when
      a VM has emitted nothing (never a fabricated row). `[UI]` gate applies: needs `pw:L2 ✓` plus a cited regression
      spec per [`/codex/06-coding-standards/ui-testing-layers.md`](/codex/06-coding-standards/ui-testing-layers.md). —
      **deployment-ui@228ccb0** | `pw:L2 ✓` | regression: `tests/smoke/cockpit-streaming-logs-live-contract.spec.ts`.
      Verified LIVE (not just by code-reading): brought up the real, non-mock deployment-api backend
      (`CLOUD_MOCK_MODE=false`, via `unified-trading-pm/scripts/dev/restart-deployment-stack.sh --api`) and curled
      `GET /api/logs/stream/{ref}` directly. A genuinely running VM (`cefi-hyperliquid-2024-20260727-071055`) streamed
      real `vm_event` frames — actual `PIPELINE_HEARTBEAT` / `RESOURCE_PROFILER_SAMPLE` telemetry carrying real
      `asset_group=cefi` data, confirming the per-AG/VM tail is genuine, not fabricated. A never-existed VM ref streamed
      ONLY `heartbeat`/`ping` frames for 35s straight — zero `vm_event`, never a synthesized row (backend trace:
      `deployment-api/routes/log_stream.py` `_vm_sse_generator`'s `_collect_blob_names` returns `([], [])` on an empty
      GCS prefix; the loop simply never yields, it does not invent one). Locked that proven contract into a new hermetic
      Playwright spec (`cockpit-streaming-logs-live-contract.spec.ts`, 2 tests, `page.route()`-fulfilled SSE responses
      shaped exactly like the live-observed payloads — EventSource issues a real network request unlike the app's
      `fetch` calls, so Playwright's route layer can intercept it) + a `data-testid="streaming-logs-empty"` on
      `StreamingLogsPanel.tsx`'s honest-empty-state div for reliable assertion. Both new tests + the directly-related
      `cockpit-alerts-logs-ag-vm-picker.spec.ts` + `cockpit.spec.ts` (40 tests total) pass 100%. The whole-suite
      `npx playwright test --project=chromium tests/smoke/` run shows 407 passed / 17 failed — confirmed by
      `git stash`-ing both my touched files and re-reproducing an identical failure list on the pristine tree, so all 17
      are pre-existing and unrelated to this change; documented + 5 newly-surfaced clusters added as tracked todos in
      the already-open
      [`/plans/active/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md`](/plans/active/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md)
      rather than duplicating a new issue doc. Also discovered `deployment-api/routes/log_stream.py`'s
      `_vm_sse_generator`/`_live_cluster_sse_generator` have zero direct test coverage of the honest-empty-stream
      behavior (verified true by code trace + my live curl, but not by an executable backend test) — out of scope for
      this UI-scoped todo (different repo, different craft; `deployment-api` isn't in this plan's `repos:`), filed as
      [`/plans/archive/issues/deployment_api_log_stream_sse_generator_no_test_coverage_2026_07_30.md`](/plans/archive/issues/deployment_api_log_stream_sse_generator_no_test_coverage_2026_07_30.md)
      (2 concrete `[BACKEND]` todos, both closed + doc archived 2026-08-01 — `deployment-api@e277f4c`) rather than
      silently crossing craft lines.
- [x] ✅ [PLANNING] P3. **DONE 2026-07-30 (plans-corpus-reduction-marathon wave 4).** Both verifications above were done
      (todo 1 by this wave, todo 2 by a concurrent slot-6 session, `deployment-ui@228ccb0`) and the source plan had zero
      open todos + no `locked_by:`. Ran the 6-step archival ritual: both docs moved to `plans/archive/2026_07/`,
      archived-banners added, every corpus referrer (10 for the source plan, 2 for this twin) repointed to the archive
      path. See this doc's own Progress Log + the source plan's archived copy for the full referrer list.

## Codex SSOTs

- [`/codex/05-infrastructure/data-pipeline-alerts.md`](/codex/05-infrastructure/data-pipeline-alerts.md) — the
  failure-mode registry + emit→route→escalate model todo 1 verifies against.
- [`/codex/06-coding-standards/ui-testing-layers.md`](/codex/06-coding-standards/ui-testing-layers.md) — the `pw:L2`
  gate todo 2 must satisfy.
- [`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`](/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md)
  — the naming/pairing convention + the conflict-check that cleared the reclassification.
- [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md)
  — the 6-step archival ritual todo 3 runs.

## Progress Log

- **2026-07-30** — Authored by the `/na-eligibility-audit cross-cutting` tranche run as the paired finalize twin for the
  `NA → planning` reclassification of `data_pipeline_alert_substrate_residual_2026_07_24.md`. No work executed here;
  `status: draft` + `gate_on_depends: true` hold it until the source plan's todos land.
- **2026-07-30 (slot-12)** — Shipped todo 1 (routing verification) — alerting-service@823b75d. Both events were already
  correctly registered (DP-RATE-001/DP-RATE-002); added the missing router-level injected-429-storm regression tests
  proving the routed mirror post. 2 todos remain open (streaming-events pane pw:L2 verification, source-plan archival) —
  plan stays active.
- **2026-07-30 (slot-3, ui_developer)** — Shipped todo 2 (streaming-events pane live verification) —
  deployment-ui@228ccb0. Verified LIVE against the real (non-mock) deployment-api backend: a genuinely running VM
  streamed real telemetry (per-AG/VM tail confirmed genuine), a never-existed VM ref streamed heartbeats-only (honest
  empty-state confirmed, never fabricated). Added `cockpit-streaming-logs-live-contract.spec.ts` (2 tests, `pw:L2 ✓`)
  locking the proven contract in. Along the way: fixed an unrelated pre-existing environment defect in this slot's
  `node_modules` (a stray `npm install` had left `happy-dom` missing; corrected with `pnpm install`, this repo's actual
  package manager — no lockfile drift). Also found the whole-suite `pw:L2` gate carries 17 pre-existing failures
  (confirmed unrelated via stash-diff) — updated the already-open `deployment_ui_l2_smoke_gate_red_2026_07_17.md` rather
  than duplicating it, and filed `deployment_api_log_stream_sse_generator_no_test_coverage_2026_07_30.md` (2 `[BACKEND]`
  todos) for a real, out-of-craft/out-of-repo coverage gap the verification surfaced. 1 todo remains open (source-plan
  archival) — plan stays active.
