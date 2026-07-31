---
doc_type: issue
title: BLRS G3 (agent dispatch) + G10 (UI wiring) are bigger than their one-line framing — rescoped
summary:
  Closing out `batch_live_reconciliation_service_audit_2026_05_27.md`'s G1/G3/G10 todo (P1.BLRS1/P2.BLRS2/P3.BLRS3 in
  `citadel_paper_batch_live_reconciliation_2026_06_19.md`), G1 shipped clean but G3 and G10 turned out to need a real
  design decision / a whole missing gateway layer, not a mechanical "wire the call" — rehoming as their own scoped
  finding per the backend_engineer craft escalation rule.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [batch-live-reconciliation-service, trading-agent-service, unified-trading-api, unified-trading-system-ui]
scope: [engineer, admin]
tags: [reconciliation, blrs, findings, rescope]
related:
  [
    /plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
  ]
created: 2026-07-28
parent_epic: batch_live_symmetry_master
priority: P2
source:
  [
    batch-live-reconciliation-service/batch_live_reconciliation_service/stages/stage4_agent_analysis.py,
    trading-agent-service/trading_agent_service/api/main.py,
    unified-trading-api/unified_trading_api/routes/reporting.py,
    unified-trading-api/unified_trading_api/routes/positions.py,
    unified-trading-system-ui/hooks/api/use-reports.ts,
  ]
assigned_vm: planning
resolved_by: >-
  All 4 todos done: G3 design-decision + design-plan-authoring resolved via
  `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md` (unified-trading-pm@b30848f1c); G10's two gateway
  proxies shipped unified-trading-api@d7fdea4 + unified-trading-api@df6d5ee; G10's UI wiring shipped
  unified-trading-system-ui@c92078e2 (useResolveBreak/useBookCorrection wired into the reconciliation page's resolve
  dialog + book-correction action, plus a discovered `/api/reporting/*` gateway-rewrite fix).
locked_by:
locked_since:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# BLRS G3 + G10 — rescope after verification (2026-07-28)

> **🗄️ ARCHIVED 2026-07-31** — all 4 todos are `[x]`, zero remaining, `locked_by:` empty. Per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`, a doc with every todo done archives
> immediately. G3's build-phase follow-up work lives in
> `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md` §5 (not duplicated here).

## What I found

Dispatched task `batch_live_reconciliation_service_audit-001` asked to close G1 (resolution API mock-backed), G3 (stage4
agent dispatch markdown-only), G10 (UI→resolution-API wiring unverified) — the three orphaned gaps rehomed as
`P1.BLRS1`/`P2.BLRS2`/`P3.BLRS3` in `citadel_paper_batch_live_reconciliation_2026_06_19.md`.

**G1 — done, shipped this task.** `resolution_api.py` now reads `t1-recon/recon/index.json` + `summary_{date}.json` from
the recon bucket (`_current_breaks()`), falling back to the illustrative mock set only when no run has ever produced a
summary (never masking a genuine zero-deviation day). `stage5_results_writer.py` now serializes per-deviation detail
(`metric_name`/`actual_value`/`threshold`/`instrument_id`/...) into the summary JSON so the resolution API has real data
to flatten into breaks. 6 new unit tests, full QG green. Evidence: `batch-live-reconciliation-service@80380c5`.

**G3 — NOT done. "Wire the real dispatch call" undersells the actual gap.** `trading-agent-service`'s `api/main.py`
exposes ONLY `/health` + `/readiness` (via UTL `make_health_router`) — there is no inbound endpoint, no PubSub/event
subscriber loop, no consumption surface of ANY kind for a "reconciliation analysis task." The service's only existing
loops (`app/loops/l2_signal.py` et al.) subscribe to `commodity-signals-{commodity}` topics for its own L2/L3
trade-decision pipeline — a completely different domain (commodity trading signals, not recon analysis). Codex
(`/codex/08-workflows/t1-batch-dag.md:146`) says Stage 4 dispatches to "trading-agent-service (reconciliation analysis
task)" but that task type does not exist anywhere in the repo. Building it requires a real design decision (what does
"analysis" mean here — an LLM call over the `_build_agent_prompt()` markdown? a new FastAPI endpoint? a new PubSub
topic + consumer loop?) — this is the "figure out how X should look" class of open-ended judgment call the
plan-authoring rules reserve for a human decision, not a mechanical todo. I did not build it.

**G10 — verified, and it's much bigger than "BLRS's resolution API."** `unified-trading-system-ui`'s
`hooks/api/use-reports.ts` defines 9 hooks calling reconciliation endpoints that **do not exist in `unified-trading-api`
at all**:

- `useReconciliationBreaks`/`useResolveBreak`/`useBookCorrection` →
  `/api/reporting/reconciliation/{breaks,resolve,book-correction}` — `unified_trading_api/routes/reporting.py` has only
  a bare `GET /reconciliation` (proxies to client-reporting-api); no `/breaks`, `/resolve`, or `/book-correction`
  sub-route, and no proxy to BLRS's `/t1-recon/*` router at all.
- `useReconciliationDeviations`/`useReconciliationBalances`/`useReconciliationPnL`/`useReconciliationSummary`/
  `useResolveDeviation`/`useAutoReconHistory` → `/api/positions/reconciliation/*` —
  `unified_trading_api/routes/positions.py` has only `/active`, `/summary`, `/balances` (position data), zero
  `reconciliation/*` sub-routes, no proxy to strategy-service/position's real reconciliation API
  (`api/reconciliation_routes.py`, confirmed real+DB-backed in the parent audit's § 5.5).

**Mitigating factor**: `grep`-verified zero UI page/component consumes any of these 9 hooks (`rg` across `.tsx`/`.ts`
outside `use-reports.ts` itself — 0 hits). So this is not a live user-facing break — it's two halves of an unfinished
feature (hooks written on spec, gateway never built) that happen to compile fine because nothing calls them. Framing
matters: G10's original "unverified" was accurate; the verified state is "both ends are stubs," not "one wire is loose."

## Why it matters

Both are real pre-F21-activation gaps (BLRS "never run in prod" per the parent audit, but Stage 4 + the resolution UI
are both on the critical path to a usable operator surface once it does). Neither is a bounded, worker-determinable todo
as currently worded — dispatching them as-is would have an agent either build unplanned scope (a new
trading-agent-service task type, or ~9 gateway routes across 2 backend domains with real response-shape decisions) or
silently skip them again, which is how this sat unaddressed since 2026-05-27.

## Recommended decision

- **G3**: needs an `[OPERATOR]`/main-agent design call first — pick ONE of: (a) LLM-backed analysis endpoint in
  trading-agent-service that ingests the Stage-4 markdown prompt and returns root-cause/suggestions; (b) a PubSub
  topic + consumer loop (matches the existing `l2_signal.py` subscriber pattern) that trading-agent-service polls async;
  (c) defer indefinitely — codex's Stage-4 framing stays aspirational, mark `agent_report_{date}.md` as the terminal
  artifact (an operator reads it, no automated dispatch). Recommend (c) short-term (lowest risk, matches "prod-gated
  behind F-21" reality) with (a)/(b) as a real backlog item once BLRS goes live.
- **G10**: once a decision is made on whether the recon UI ships at all pre-F21, build the ~9 missing gateway routes as
  ONE bounded todo per domain (BLRS proxy: 3 routes in `reporting.py`; strategy-service/position proxy: 6 routes in
  `positions.py`) — both are mechanical proxy-and-reshape work once the target endpoints are confirmed (BLRS's are;
  strategy-service/position's are per the parent audit § 5.5). Until then, the 9 orphaned hooks are harmless (unused)
  and don't need deleting.

## Todos

- [x] ✅ [OPERATOR] P2. **Operator-ruled 2026-07-29 (interactive decision session) — a 4th option, not (a)/(b)/(c)
      above.** Decide G3's dispatch mechanism (a/b/c above) for `trading_agent_service` Stage-4 consumption; once
      decided, file the build as a scoped todo naming the exact endpoint/topic shape. Repo: trading-agent-service.

  **The operator's actual ruling (verbatim intent, preserved in full — this is new design content, not a pick from the 3
  listed options):** a **daily-scheduled LLM analysis job**, run as a script on the planning VM (AO) — mirroring the
  existing daily reconciler/auditor scheduled-job pattern (`plan_reconciler`/`docs_reconciler`/`ag_closeout_auditor`/
  `na_eligibility_auditor`), not an endpoint inside trading-agent-service (option a) and not a PubSub consumer loop
  (option b). The job compares, across a scheduled daily run: **trades, PnL/positions, ML signals, strategy execution
  decisions, and data-quality gaps.** Operator's key structural insight: since `pipeline_mode` is the only thing
  separating storage across batch/live/paper, the SAME analysis logic/scripts should work uniformly across all three
  modes — same features, same data shape, just a different `pipeline_mode` partition; this should NOT need mode-specific
  analysis code. **The LLM's specific job**: explain WHY things happened (diagnosis, not just detection) and **create
  issues** (i.e. file `plans/active/issues/*.md` docs, matching this workspace's own findings-triage convention) when it
  finds problems — not just a metrics dashboard or a passive report.

  This is a genuinely new, substantial system component (a daily cross-cutting LLM trading-analyst job spanning
  trades/PnL/ML/strategy/data-quality across all pipeline_modes) — NOT mechanical enough to dispatch as a single bounded
  todo. Per the plan-authoring hard rule (an open-ended design call is a human decision, not a todo), this needs its own
  scoped LOCAL design plan before any code is written.

- [x] ✅ [DESIGN] P1. **Author a scoped design plan for the daily cross-cutting LLM trading-analysis job** (per the
      2026-07-29 ruling above) — define: (1) the exact daily trigger/schedule and which planning-VM AO account/rotation
      slot it draws from (mirroring the existing reconciler-job headroom pattern); (2) the concrete data sources per
      category (trades, PnL/positions, ML signals, strategy execution decisions, data-quality gaps) and confirm they
      really do share one `pipeline_mode`-partitioned shape across batch/live/paper as the operator expects — this is an
      assumption to verify, not just assume; (3) the LLM prompt/analysis contract (what "diagnosis" output looks like)
      and the issue-doc-creation mechanism (frontmatter, naming, dedup against already-filed issues so it doesn't
      re-file the same finding daily); (4) how this relates to (doesn't duplicate) BLRS's own `agent_report_{date}.md`
      terminal-artifact output — is this job BLRS's actual G3 consumer, a superset of it, or a separate parallel system
      that BLRS's report becomes one input to? Answer that scoping question explicitly in the new plan's own opening
      section. `assigned_vm: NA` (a design plan, not yet AO-dispatchable) per the plan-destination default.

      **DONE 2026-07-29 (slot 16)** — `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md`
                                                                                                                                                                                                                                                                                                                      (unified-trading-pm@b30848f1c). All 4 points answered, each grounded in a dedicated research pass rather than
                                                                                                                                                                                                                                                                                                                      assumed: (1) traced the 4 live systemd-timer reconciler jobs end-to-end (dispatch script → `plan_health.py` →
                                                                                                                                                                                                                                                                                                                      `agents/<role>.md`) for the exact scheduling/account/slot mechanics — no new slot config needed, inherits the
                                                                                                                                                                                                                                                                                                                      shared headroom pool + scheduled-task reserve automatically; also found the referenced codex table
                                                                                                                                                                                                                                                                                                                      (`agent-orchestrator-single-vm-architecture.md`) is stale (says opus/daily; live reality is sonnet/hourly-retry)
                                                                                                                                                                                                                                                                                                                      and filed that as a follow-up. (2) The `pipeline_mode`-uniformity assumption is **VERIFIED FALSE** — 5 distinct,
                                                                                                                                                                                                                                                                                                                      mutually-inconsistent mode-differentiation mechanisms exist across trades/PnL/positions/ML/strategy datasets
                                                                                                                                                                                                                                                                                                                      (several with a dead no-op `mode=` kwarg the path template silently drops), with code:line citations for each;
                                                                                                                                                                                                                                                                                                                      the design routes around this by reusing BLRS's own already-working per-stage adapters rather than building a
                                                                                                                                                                                                                                                                                                                      uniform reader. (3) Prompt contract + dedup mechanism specified, reusing this workspace's own
                                                                                                                                                                                                                                                                                                                      pre-task-plan-conflict-check discipline for the dedup step. (4) Scoping question answered in the new plan's own
                                                                                                                                                                                                                                                                                                                      §0: this job completes BLRS Stage 4's never-built LLM-dispatch leg (confirmed via full code read that Stage 4
                                                                                                                                                                                                                                                                                                                      today only builds a markdown prompt and never calls an LLM) — not a superset (BLRS's batch-vs-live symmetry
                                                                                                                                                                                                                                                                                                                      engine stays necessary) and not fully separate (consumes BLRS's `summary_{date}.json` as one input). 6 scoped
                                                                                                                                                                                                                                                                                                                      follow-up build-phase todos filed in the new plan's §5 (skill/role-file build, scheduling wire-up, Stage 4
                                                                                                                                                                                                                                                                                                                      artifact removal, the dead-mode-kwarg bug, the stale codex table, 2 operator policy calls) — none bundled into
                                                                                                                                                                                                                                                                                                                      this design todo's own scope.

- [x] ✅ [CODE] P3. Build the BLRS resolution-API gateway proxy — `GET /api/reporting/reconciliation/breaks`,
      `POST /api/reporting/reconciliation/resolve`, `POST /api/reporting/reconciliation/book-correction` in
      `unified_trading_api/routes/reporting.py`, proxying to BLRS's `/t1-recon/{breaks,resolve,book-correction}`
      (mock-mode + real-mode per the file's existing `mock_mode` split). Repo: unified-trading-api. — **DONE —
      unified-trading-api@d7fdea4.** Added a `_blrs_proxy()` helper (env-var-only `LIVE_SERVICE_BLRS_URL`, no hardcoded
      default port since BLRS has no registered local-dev port unlike client-reporting-api's 8014) that in real mode
      proxies the raw request to BLRS's `/t1-recon/*` and forwards BLRS's real HTTP status code verbatim (a 404 from
      BLRS reaches the UI as a real 404, not masked as a mock-mode 200 — the UI's `apiFetch` throws on any non-2xx).
      Mock mode falls back to `MockStateStore`/`get_service()` (empty `reconciliation_breaks` until a fixture is seeded
      — same accepted-empty convention as this file's other unseeded resources) — POST `/resolve` synthesizes an honest
      acknowledgement using UAC's `ReconciliationResolution`/`ReconciliationAction` (not a re-implemented local type),
      and POST `/book-correction` returns an honest `NOT_FOUND` rather than fabricating booking params with no real
      break to derive them from. GET `/breaks` forwards the raw query string as-is (BLRS's filter surface is
      `venue`/`break_type`/`status`; the UI's extra `category`/`date_from`/`date_to` params are accepted-and-ignored on
      both sides — no field-name mapping invented). 10 new unit tests (mock-mode +
      real-mode-via-monkeypatched-`httpx.AsyncClient`) in `test_reporting_blrs_proxy.py`; full `quality-gates.sh` green
      (65s).
- [x] ✅ [CODE] P3. Build the strategy-service/position reconciliation-API gateway proxy — the 6 routes
      `useReconciliationDeviations`/`Balances`/`PnL`/`Summary`/`useResolveDeviation`/`useAutoReconHistory` call under
      `/api/positions/reconciliation/*`, proxying to strategy-service/position's real `api/reconciliation_routes.py`.
      Repo: unified-trading-api. — **DONE — unified-trading-api@df6d5ee.** Added a `_strategy_recon_proxy()` helper in
      `routes/positions.py` (mirrors the BLRS `_blrs_proxy()` pattern from `reporting.py`) that in real mode proxies to
      strategy-service's `/reconciliation/*` routes via the already-registered `LIVE_SERVICE_STRATEGY_URL` env var (no
      new port invented — reuses the same slot `strategy_performance.py`'s PBM adapter probes) and forwards
      strategy-service's real HTTP status code verbatim. Mock mode falls back to `MockStateStore`/`get_service()`:
      `deviations`/`balances`/`pnl`/`auto-recon/history` are empty until seeded (accepted-empty convention); `summary`
      is computed live from the `recon_deviations` mock collection rather than hardcoded (never masking a genuine
      zero-deviation day) with `last_run` staying `None` (no real run to report in mock mode); `resolve` synthesizes an
      honest low-stakes acknowledgement (mirrors BLRS's own `/resolve` — nothing here needs deriving from a real
      deviation, unlike book-correction) using a local `DeviationResolveRequest` model (mirrors strategy-service's own
      `deviation_id`/`action`/`note`/`resolved_by` shape — UAC's `ReconciliationResolution` uses `break_id` instead, so
      it doesn't fit this endpoint's real field names) built on UAC's `ReconciliationAction` enum (reused, not
      re-implemented). 15 new unit tests (mock-mode + real-mode-via-monkeypatched-`httpx.AsyncClient`) in
      `test_positions_reconciliation_proxy.py`; full `quality-gates.sh` green (72s).
- [x] ✅ [UI] P3. Once the two gateway proxies above ship, wire at least one operator-facing page/component to consume
      the 9 existing `use-reports.ts` reconciliation hooks (currently zero consumers) — pick the page during that todo's
      own scoping, don't invent one here. Repo: unified-trading-system-ui. — **DONE —
      unified-trading-system-ui@c92078e2.** Picked `/services/reports/reconciliation` (already the
      resolve/book-correction UX, but the dialog only mutated local React state — no backend call). Wired
      `useResolveBreak()` into the resolve dialog's Confirm action (POSTs `{break_id, action, note, resolved_by}` to the
      BLRS proxy; pending/error states surfaced in the dialog) and `useBookCorrection()` into the Book Correction action
      (POSTs `{break_id}`, threads the real venue/instrument_id/side/quantity/execution_mode/reason into the
      trading-book prefill on success, falls back to the existing client-derived estimate on a 404/no-live-break — same
      honest-fallback pattern the gateway proxy itself uses). 3 new Vitest tests
      (`tests/unit/components/reports/reconciliation-client.test.tsx`) mock the two hooks + assert the exact
      payload/response wiring; `tsc --noEmit` + `eslint` clean; full `quality-gates.sh` green (170s, 288 tests). **Also
      fixed a discovered gateway bug while browser-verifying this against a live `unified-trading-api` mock-mode
      instance**: `next.config.mjs`'s `/api/reporting/:path*` rewrite pointed at `client-reporting-api` (port 8014) —
      which has no `/api/reporting` prefix at all (confirmed by grep: its own routes are `/api/reports`,
      `/api/v1/documents`, etc.) — instead of `unified-trading-api`'s own `/reporting` router (routes/reporting.py)
      where these hooks' endpoints, and the whole rest of `use-reports.ts`'s domain, actually live. Verified via curl
      before (404 through the Next proxy) and after (real backend JSON) the fix. This was silently breaking all 16
      `use-reports.ts` hooks in real (non-mock) deployments, not just the 2 wired here.
