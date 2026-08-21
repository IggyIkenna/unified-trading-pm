---
doc_type: plan
title: Multi-provider model capability bake-off — Gemini/GLM/Gemma/Codex
summary:
  Real-task capability/cost bake-off across 6 newly-onboarded non-Anthropic models (2x Gemini, 2x GLM, 1x Gemma,
  1x Codex/Luna) before deciding future AO task-complexity routing. Each model runs 6 real open backlog tasks
  (2 easy/2 medium/2 hard); results feed a per-model, per-complexity-tier profile (quality, tokens, context-fill,
  turns, time) that becomes the actual routing input for AO dispatch. Claude models (Sonnet 4.6/5, Opus 4.6/5)
  are explicitly OUT OF SCOPE for this pass — tested in a later plan.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags:
  [ao, agent-orchestrator, model-evaluation, gemini, glm, gemma, nvidia, codex, luna, multi-provider, bake-off,
    task-routing]
related:
  [
    /plans/active/grok_gemini_translation_proxy_2026_08_14.md,
    /plans/active/kimi_gemma_provider_onboarding_2026_08_16.md,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/codex_luna_flex_bridge_2026_08_14.md,
    /plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md,
    /plans/active/ao_satellite_ao_dispatch_batch24_2026_08_18.md,
    /plans/active/infra_satellite_ao_dispatch_batch19_2026_08_18.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
assigned_role: infra
effort: high
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: interactive session 2026-08-18/19, operator-directed
context_scope:
  [
    agent-orchestrator/server/accounts.py,
    agent-orchestrator/server/model_pricing.py,
    agent-orchestrator/config/litellm/grok_gemini_proxy.yaml,
    agent-orchestrator/server/gemini_headroom.py,
    /plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
---

# Multi-provider model capability bake-off — Gemini/GLM/Gemma/Codex

## Why

Six non-Anthropic models were onboarded into AO's fleet (Grok/Gemini/GLM/Kimi/NVIDIA/Codex-Luna plans, 2026-08-14/16)
and left deliberately `account_status: disabled` pending exactly this: proof that real tool-calling coding work
succeeds through each provider's translation path, and a real quality/cost/speed profile per model before any task
gets routed to it. Grok and Kimi are explicitly OUT OF SCOPE for this pass (operator decision, 2026-08-19) — GLM,
Gemini, Gemma, and Codex/Luna already have real proxy/bridge infrastructure live-verified for tool_use (Gemini,
Kimi, Gemma proven 2026-08-19 via a local litellm proxy instance in slot 1; GLM native-endpoint and Codex/Luna
bridge not yet tool-use-tested — see Todos).

**This is a HUMAN plan (`assigned_vm: NA`), not AO-dispatched** — every account under test is deliberately paused,
scoring needs human/review-agent judgment, and the whole point is a one-off evaluation, not bounded deterministic
work an isolated AO worker could complete alone.

## Model roster (6 models, 4 lanes)

| # | Model | Real API id | Credential | Routing |
|---|---|---|---|---|
| 1 | Gemini 3.5 Flash-Lite | `gemini-3.5-flash-lite` | `GEMINI_API_KEY_PROJ{1,2,3,5}` (GSM, fetched) | local litellm proxy :8768 |
| 2 | Gemini 3.7 Flash | `gemini-3.7-flash` | same | local litellm proxy :8768 |
| 3 | GLM 5.2 | `glm-5.2` (server-aliased to `glm-5.3` — Z.ai routes it there silently, confirmed via response header + real billing data; note this when reading results) | `glm-coding-plan-api-key` (GSM) | direct native `api.z.ai/api/anthropic/v1/messages` |
| 4 | GLM 5-Turbo | `glm-5-turbo` | same | direct native endpoint |
| 5 | Gemma (DiffusionGemma 26B) | `diffusiongemma-26b-a4b-it` | `NVIDIA_API_KEY` (GSM, fetched) | local litellm proxy :8768 |
| 6 | Codex/Luna | (OpenAI Codex App Server) | `~/.codex/auth.json` (device-auth, already present) | `codex-bridge` server :8769 |

`gemma-4-31b-it` is EXCLUDED (operator: "not working properly" — matches this fleet's own documented cold-start
flakiness). Anthropic (Sonnet 4.6/5, Opus 4.6/5) deferred to a later plan.

## Task assignment — 4 lanes, 6 tasks each (2 easy/2 medium/2 hard)

Gemini's 2 models both run the **Gemini lane**; GLM's 2 models both run the **GLM lane** — giving a free head-to-head
per provider on identical work, on top of the cross-provider comparison. Gemma and Codex/Luna each have 1 model, so
each runs its own lane once. **All 24 distinct tasks re-verified open as of 2026-08-19** (4 had been completed or
their source doc archived since original selection 2026-08-18 — swapped, see table notes).

### Gemini lane (models 1 + 2, run independently — 12 attempts total)

| Tier | Task | Source |
|---|---|---|
| Easy | Audit `ag-closeout-auditor` timer (sharding, run time, review-gate, escalation trace) | `ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md` |
| Easy | Audit `docs-reconcile` timer (same 4 checks) — *swapped in 2026-08-19, replaces the now-shipped `ao_watchdog.md` wrapper task* | same doc |
| Medium | Audit `escalation-queue-reconciler` timer (4 checks + cross-check whether it would've caught the plan_reconciler PR-backlog problem itself) | `ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md` — *re-swapped 2026-08-19 (2nd pass), replaces "join per-task compaction onto TaskUsageRow", which shipped `agent-orchestrator@4a9cf6258` between plan authoring and dispatch* |
| Medium | Audit other repos for the same unscoped-tmux-fixture test anti-pattern | `issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md` — *swapped in 2026-08-19, replaces `DirtyStateResolution.COMMIT_AND_PUSH` fix whose source doc is now fully archived* |
| Hard | Capture which repo(s) a task touched, from real commit/push evidence (no existing mechanism to mirror) | `ao_satellite_ao_dispatch_batch24_2026_08_18.md` — *shared with Codex/Luna, see below* |
| Hard | Audit `na-eligibility-auditor` timer (4 checks); if a review-gate or escalation-trace gap is found, design AND implement the fix, not just flag it | `ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md` — *re-swapped 2026-08-19 (2nd pass), replaces the `GET /api/backlog/graph` dashboard task, which shipped `agent-orchestrator@003aafb608` between plan authoring and dispatch; scope widened from plain-audit to audit+fix to keep it Hard-shaped like this task's siblings* |

### GLM lane (models 3 + 4, run independently — 12 attempts total)

| Tier | Task | Source |
|---|---|---|
| Easy | Audit `context-scout` timer (same 4 checks; read-mostly, confirm review-gate applicability) | `ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md` |
| Easy | Extend `death_class` teardown-signal set beyond the 3 currently checked events | `ao_death_diagnostics_compaction_kpis_and_sequential_carveout_2026_08_15.md` |
| Medium | Capture peak/high-watermark `context_used_pct` reached during a task | `ao_satellite_ao_dispatch_batch24_2026_08_18.md` |
| Medium | Decouple `_maybe_alert_pool_exhaustion` from the halted-dispatch branch + regression test | `issues/escalation_pool_exhaustion_alert_unreachable_when_halted_2026_08_18.md` |
| Hard | Work `check_active_refs_archived_plans.py`'s referrer baseline down from 925 toward 0 (autonomous, judgment-per-entry) | `infra_satellite_ao_dispatch_batch19_2026_08_18.md` |
| Hard | Root-cause the recurring `sequential: true` dispatch-ordering violation on satellite finalize plans (2 confirmed historical instances) | `ao_consolidated_closeout_2026_08_12.md` — *swapped in 2026-08-19, replaces the pre-spawn dirty-state liveness fix whose source doc is now fully archived; shared with Codex/Luna, see below* |

### Gemma lane (model 5, single run — 6 attempts)

| Tier | Task | Source |
|---|---|---|
| Easy | Pull `overage_disabled_reason` for the other 21 disabled accounts, cross-reference against in-progress onboarding plans | `issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md` |
| Easy | Persist the task's `context_scope` size onto its completed-task DB record | `ao_satellite_ao_dispatch_batch24_2026_08_18.md` |
| Medium | Spread CI-escalation-reserve slots 31/32/33 across more than one account | `issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md` |
| Medium | Trace `deepseek_usage.py`'s aggregation vs. seeded fixtures — fixture-drift vs. real regression | `issues/dashboard_deepseek_e2e_specs_red_stale_fixture_expectations_2026_08_08.md` |
| Hard | `context_scope` frontmatter backfill corpus-wide (626 docs), then harden the field to required | `context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md` |
| Hard | Root-cause the "zero-derived-parent-row" backlog-derivation bug in `regen_backlog_from_plan.py` (2 prior fixes were incomplete) | `issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` |

### Codex/Luna lane (model 6, single run — 6 attempts)

| Tier | Task | Source |
|---|---|---|
| Easy | Confirm the git-status-nudge hardcodes `origin/live-defi-rollout` as comparison target for every repo | `issues/git_status_red_nudge_false_positive_wrong_branch_comparison_2026_08_17.md` |
| Easy | Widen quickmerge's failure-DISPLAY grep to match the failure-COUNT vocabulary — *swapped in 2026-08-19, replaces the now-shipped `plan_health.py` test-mirror task* | `issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md` |
| Medium | Add `reason`+`paused_at` fields to `scheduled_dispatch_pause.py` + surface on API + dashboard UI | `issues/ao_scheduled_dispatch_pause_reasons_2026_08_18.md` |
| Medium | Design + build a freshness/rotation mechanism for `.orch_token` files across slots | `issues/ff_pull_starvation_watchdog_ping_401_2026_08_16.md` |
| Hard | *(shared with Gemini)* Capture which repo(s) a task touched, from real commit/push evidence | `ao_satellite_ao_dispatch_batch24_2026_08_18.md` |
| Hard | *(shared with GLM)* Root-cause the recurring `sequential: true` dispatch-ordering violation on satellite finalize plans | `ao_consolidated_closeout_2026_08_12.md` |

**= 36 task-attempts total, 24 distinct real backlog items**, all confirmed `status: active`/open as of 2026-08-19.
The 2 shared Hard tasks give a direct diff-vs-diff comparison at no extra curation cost.

## Metrics — what judges each attempt

**Gate 1 (pass/fail — must clear to score anything else)**: `quality-gates.sh` green on the diff · the task's own
"Done when" criterion literally met · clean git hygiene (correct commit message, only its own files staged) · no
new DTZ/TID251/fallback-import ratchet violations.

**Gate 2 (0–3 each, only on Gate-1 passers)**: root-cause depth (fixed the mechanism vs. patched a symptom) · test
coverage (regression test covers the real failure mode, not just happy-path) · diff minimalism (no premature
abstraction/scope creep) · process-rule adherence (batched tool calls, didn't claim without measuring, escalated
genuine ambiguity instead of guessing).

**Tracked per attempt, not folded into the score — these are the actual routing-decision inputs**:

- **Token usage** — input/output/cache tokens (from litellm's usage reporting / `TaskUsageRow`)
- **Context fill** — peak `context_used_pct` reached during the attempt
- **Turns** — number of conversation turns / tool calls used
- **Time** — wall-clock duration to completion
- **Tool-call error rate** — malformed `tool_use` blocks / retries needed, tracked SEPARATELY from model quality so
  a proxy-layer rough edge isn't misread as "the model is bad"

**Who judges**: AO's existing review-slot mechanism (`ensure_review_agents`) — already trusted, already scores real
dispatches against real "Done when" bars daily; no new judging pipeline needed.

**Final deliverable**: a per-(model, complexity-tier) summary — pass-rate, avg Gate-2 score, avg tokens, avg
context-fill%, avg turns, avg time, $ cost — becomes the actual input for future AO task-complexity routing
decisions (which model tier is worth dispatching a given task shape to).

## Mechanics

**Direct tmux/subprocess dispatch — no local AO backend instance, no real AO backlog involved** (operator decision,
2026-08-19). One dedicated slot per model (already-isolated git checkouts, matches this fleet's existing per-slot
worktree convention) rather than 36 worktrees hand-rolled inside slot 1:

| Slot | Model | `.agent-claim` |
|---|---|---|
| 24 | Gemini 3.5-flash-lite | claimed 2026-08-19, `role: model-capability-bakeoff` |
| 25 | Gemini 3.7-flash | same |
| 26 | GLM 5.2 | same |
| 27 | GLM 5-turbo | same |
| 28 | DiffusionGemma 26B | same |
| 29 | Codex/Luna | same |

All 6 confirmed clean/`live-defi-rollout`/`0 ahead 0 behind origin` before claiming. Within each model's slot, each
of its 6 tasks runs on its own branch off `live-defi-rollout` — the 2 cross-slot shared Hard tasks (repo-touched
capture: slot 24/25 vs. 29; sequential-ordering root-cause: slot 26/27 vs. 29) land on independently-named branches
so they never collide despite being attempted in different slots.

Per attempt: a tmux session in that slot runs `claude -p "<task's exact Done-when + source citation>"
--output-format json`, with `ANTHROPIC_BASE_URL`/`ANTHROPIC_MODEL`/auth env pointed at that model's proxy or native
endpoint (litellm :8768 for Gemini/Gemma, native `api.z.ai` for GLM, `codex-bridge` :8769 for Codex/Luna) —
mirroring `start-claude-account-tmux.sh`'s existing pattern, just non-interactive and per-task. The CLI's own JSON
result gives `num_turns`/`total_cost_usd`/token usage/duration directly — no AO telemetry pipeline needed for those
4 metrics. **Context-fill % is NOT natively reported by the CLI** (it's literally one of the bake-off's own tasks,
not yet built anywhere) — approximated as peak reported token usage ÷ that model's context window, stated as an
approximation, not a true AO-grade measurement. No attempt's diff auto-merges — Gate 1/2 scoring + the shared-task
diff comparison decide what (if anything) actually ships via normal `quickmerge.sh`.

**Usage-stats polling (operator requirement, 2026-08-19)**: every attempt runs with a companion poller at ≤60s
cadence for the attempt's full duration — see the `[INFRA] P1` poller todo below for exactly what it captures and
where it writes.

## Todos

- [x] [OPERATOR] P0. ✅ Operator go-ahead given 2026-08-19 ("yes bro, go ahead and use whatever account you have to
      use and creds you need. test all these 6 models properly") — resolves the policy question above: the
      operator's explicit answer supersedes the 2026-08-16 pause instruction for the scope of this bake-off.
      `account_status` itself needs no change (confirmed AO-internal-only, doesn't gate direct dispatch). Dispatch
      is unblocked.
- [x] ✅ [INFRA] P1. Stand up the isolated-branch-per-attempt dispatch mechanism described in Mechanics above (36
      branches off `live-defi-rollout`, one `claude` subprocess per attempt, env pointed at the right
      proxy/endpoint). **DONE 2026-08-19** — proven end-to-end on a real attempt (Gemini 3.5-flash-lite, slot 24,
      `ag-closeout-auditor` audit task). Done when: one real end-to-end attempt (any model, any task) produces an isolated branch
      with a real diff and no collision with the base branch.
- [x] ✅ [INFRA] P1. Build a per-attempt usage-stats poller, cadence ≤60s (operator requirement, 2026-08-19),
      capturing: (a) the running `claude -p` session's own transcript jsonl
      (`~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`) — cumulative input/output/cache tokens, turn count,
      tool-call count, approx context-fill%; (b) each provider account's own usage/quota surface where one exists
      (litellm proxy spend log for Gemini/Gemma, GLM/z.ai account usage, Codex/Luna account usage) — message count
      and/or % of plan/quota consumed, stated as "not available" per account if the provider exposes none.
      **DONE 2026-08-19** — both this and the dispatch-mechanism todo above closed by the same Progress Log entry;
      poll-log proven on the same real attempt. Snapshots appended to a per-attempt poll-log file referenced from the
      Results table. Done when: one real attempt (paired with the INFRA todo above) has a complete poll-log from
      launch to exit at ≤60s cadence, covering both the jsonl-transcript stats and whatever account-usage surface
      exists for that provider.
- [x] ✅ [BACKEND] P2. Run Gemini 3.5 Flash-Lite against all 6 Gemini-lane tasks; record Gate 1/2 scores + tokens/
      context-fill/turns/time per attempt. **DONE** — all 6 rows in Results table; final tally: 4 clean PASS,
      2 INFRA-INTERRUPTED with real partial work. Done when: 6 rows exist in the Results table below (or a stated
      pass/fail/blocked reason per attempt).
- [x] ✅ [BACKEND] P2. Run Gemini 3.7 Flash against the same 6 Gemini-lane tasks; record the same metrics. **DONE**
      — all 6 attempted; slot 25 (Gemini 3.7-flash) is a complete quota washout: 6/6 tasks failed, blocked reason
      recorded per the Done-when's alternative clause.
- [x] ✅ [BACKEND] P2. Run GLM 5.2 against all 6 GLM-lane tasks; record the same metrics (note the 5.2→5.3
      server-aliasing when interpreting which model actually answered). **DONE** — GLM lane fully complete: 5.2 got
      1 PASS + 1 interrupted + 4 blocked.
- [x] ✅ [BACKEND] P2. Run GLM 5-Turbo against the same 6 GLM-lane tasks; record the same metrics. **DONE** —
      5-Turbo got 2 PASS + 1 interrupted + 3 blocked.
- [x] ✅ [BACKEND] P2. Run DiffusionGemma 26B against all 6 Gemma-lane tasks; record the same metrics. **DONE** —
      Gemma lane confirmed 6/6 complete washout (same pattern, now proven not a one-off).
- [x] ✅ [BACKEND] P2. Run Codex/Luna against all 6 Codex-lane tasks; record the same metrics. **DONE** — all 6
      tasks in slot 29's queue ran and exited within seconds each; Codex/Luna lane is INFRA-BLOCKED, root cause
      found.
- [ ] [REVIEW] P1. Direct diff-vs-diff comparison on the 2 shared Hard tasks (repo-touched-capture: Gemini vs.
      Codex/Luna; sequential-ordering root-cause: GLM vs. Codex/Luna) — this is the single strongest signal in the
      trial, weight it accordingly in the final synthesis. Done when: a written verdict exists for both pairs.
- [ ] [DATA] P2. Synthesize the final per-(model, complexity-tier) summary table (pass-rate, avg Gate-2 score, avg
      tokens, avg context-fill%, avg turns, avg time, $ cost) into this plan's Progress Log. Done when: the table
      covers all 6 models × 3 tiers and states an explicit recommendation for which model tier future AO dispatch
      should route each complexity level to.

## Results

| Model | Task (tier) | Exit | Turns | Tool calls (err) | Cumulative in/out tokens | Cache-read tokens | Peak approx context-fill% | Wall-clock | Gate 1 | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| Gemini 3.5-flash-lite | `ag-closeout-auditor` audit (Easy) | 0 | 83 | 29 (4) | 730,196 / 11,248 | 2,607,683 | 7.58% (corrected 2026-08-19, was 1.61% — see note below) | 10.1 min | PASS (clean tree, real citations, committed not pushed) | 4/4 checks answered with specific file/line + log citations (sharding via `MAX_CONCURRENT_TRANCHES=4`, runtime range 6.5-63.9 min measured, no PR/review-branch gate found, a real 2026-08-16 escalation traced through to a produced batch plan). Full poll history: `usage_poll.jsonl` under this attempt's out-dir. |
| Gemini 3.5-flash-lite | tmux-fixture anti-pattern audit (Medium) | 0 | 67 | 26 (1) | 475,123 / 13,869 | 3,355,399 | 2.80% (corrected, was 0.56%) | 11.3 min | PASS (clean tree, committed not pushed) | 1 real tool_error recorded (not a Gate-1 blocker — recovered same task). Not yet content-reviewed for depth (that's a separate Gate-2 pass, tracked as pending). |
| Gemini 3.5-flash-lite | `docs-reconcile` audit (Easy #2) | 1 | 2 | — | — | — | — | ~1 min | INFRA-BLOCKED (Gemini free-tier `RESOURCE_EXHAUSTED`, $0.25 spent, not a real result) | Excluded — quota, not model quality. |
| Gemini 3.5-flash-lite | `escalation-queue-reconciler` audit+gap-check (Medium #1) | 1 | 13 | — | — | — | — | — | INFRA-BLOCKED (Gemini free-tier `RESOURCE_EXHAUSTED`, $1.31 spent, not a real result) | Excluded — quota, not model quality. |
| Gemini 3.5-flash-lite | repo-touched-capture (Hard #1) | 1 | 56 | 48 (3) | 1,016,388 / 27,506 | 7,202,385 | 3.70% (corrected, was 0.74%) | 26.3 min | INFRA-INTERRUPTED (quota-driven 403 after substantial real work, $6.45 spent — NOT a clean fail, NOT a clean pass) | 56 real turns / 48 tool calls before hitting the same `RESOURCE_EXHAUSTED`-class 403. Working tree confirmed clean afterward (`git status --porcelain` empty) — no lost/uncommitted work, the model simply never reached its own commit step. Excluded from Gate-1/2 scoring (incomplete), but the depth reached is itself a useful signal this model can sustain long tool-use chains before failing. |
| Gemini 3.5-flash-lite | `na-eligibility-auditor` audit+fix (Hard #2) | 1 | 42 | 39 (5) | 696,473 / 21,680 | 4,258,544 | 11.98% (corrected, was 2.4%) | 15.5 min | INFRA-INTERRUPTED (same quota-driven 403, $4.13 spent) | 42 real turns before failing identically to Hard #1. Same clean-tree confirmation, same exclusion from scoring. |
| **Gemini 3.7-flash** | **all 6 assigned tasks** | 1 (×6) | 9,1,1,1,1,1 | — | — | — | — | — | **INFRA-BLOCKED, entire lane** — 20 req/min free-tier quota exhausted on task 1 ($0.74 spent), never recovered before tasks 2-6's turn (30s spacing too short) | Zero usable data for this model this run. Re-run needed (ideally paced/serialized or on a higher quota tier) before drawing any conclusion about Gemini 3.7-flash's real capability. |
| **DiffusionGemma 26B** | **all 6 assigned tasks** | 1 (×6) | 1 (×6) | — | $0 (×6) | — | — | ~5s each | **INFRA-BLOCKED, entire lane** — NVIDIA NIM `InternalServerError`(500)/`BadGatewayError`(502) on every attempt; a simple single-turn smoke test against the SAME endpoint succeeded (200 OK) immediately after, isolating the failure to the full real Claude Code request shape (real CLAUDE.md system prompt + full multi-tool schema), not a dead endpoint | Zero usable data. Root cause not yet pinned to a specific payload/tool-count limit — flagged, not fixed. Re-run needs that fixed first. |
| **Codex/Luna** | **all 6 assigned tasks** | 1 (×6) | 1 (×6) | — | $0 (×6) | — | — | ~0.1s each | **INFRA-BLOCKED, entire lane** — bridge rejects any `system`-role message (HTTP 400), root-caused in `codex_luna_flex_bridge_2026_08_14.md` | Zero usable data. Needs a real bridge-code fix, not a config/retry issue. |

| GLM 5.2 | `context-scout` audit (Easy) | 0 | 46 | 45 (1) | 437,337 / 163,104 | 4,708,800 | 0.31% (real window 200K, corrected — launched with a wrong 128K assumption, same class of bug as the earlier Gemini one) | 10.7 min | PASS | Real `modelUsage.glm-5.2.contextWindow` confirms 200,000, matching Gemini's — the 128K figure used at launch for both GLM models' poller was a guess, now known wrong. |
| GLM 5-Turbo | `context-scout` audit (Easy) | 0 | 38 | 37 (3) | 163,346 / 18,998 | 4,439,424 | 0.30% (corrected, real window 200K) | 10.0 min | PASS | 3 tool_errors recorded, non-blocking (task still completed clean). |
| GLM 5-Turbo | `death_class` teardown-signal extend (Easy #2) | 0 | 59 | 58 (10) | 270,291 / 20,931 | 7,670,784 | 2.50% (corrected, real window 200K) | 14.3 min | PASS | 10 tool_errors recorded (highest error count of any attempt so far), still completed clean — worth checking during Gate-2 review whether these reflect real friction with this task's shape. |

| GLM 5.2 | `death_class` teardown-signal extend (Easy #2) | 1 | 90 | 88 (0) | 464,142 / 250,313 | 12,423,680 | 0.59% (real 200K window) | 32.8 min | INFRA-INTERRUPTED — 90 real turns, $6.30 spent, before Z.ai's 5-hour Coding Plan usage limit hit (`[1308] Usage limit reached for 5 hour`, resets 2026-08-20 00:22:34 UTC) | Substantial real work done, not a clean pass/fail — excluded from Gate-1/2 scoring like the Gemini quota-interrupted rows above. |
| GLM 5.2 | Tasks 3-6 (peak-context-pct, pool-exhaustion-decouple, check-active-refs-baseline, sequential-ordering) | 1 (×4) | 1 (×4) | — | $0 (×4) | — | ~2-3s each | INFRA-BLOCKED — same 5-hour usage limit, already exhausted by task 2, every subsequent request rejected instantly | Zero usable data for these 4. **The 5-hour window is a SHARED account-level quota, not per-model** — confirmed: GLM 5-Turbo (running concurrently on the SAME account) hit the identical error with the identical reset timestamp on its own task 3. Running both GLM models concurrently split one shared budget rather than getting two independent ones. |
| GLM 5-Turbo | `context-scout` audit (Easy) | 0 | 38 | 37 (3) | 163,346 / 18,998 | 4,439,424 | 0.30% (real 200K window) | 10.0 min | PASS | 3 tool_errors recorded, non-blocking. |
| GLM 5-Turbo | `death_class` teardown-signal extend (Easy #2) | 0 | 59 | 58 (10) | 270,291 / 20,931 | 7,670,784 | 2.50% (real 200K window) | 14.3 min | PASS | 10 tool_errors recorded (highest of any attempt so far), still completed clean. |
| GLM 5-Turbo | Capture peak `context_used_pct` (Medium #1) | 1 | 81 | 80 (13) | 274,191 / 23,877 | 11,947,264 | 0.54% | 21.1 min | INFRA-INTERRUPTED — same shared 5-hour quota, $4.40 spent on real work first | Excluded from scoring, same as GLM 5.2's task 2. |

| GLM 5-Turbo | Tasks 4-6 (pool-exhaustion-decouple, check-active-refs-baseline, sequential-ordering) | 1 (×3) | 1 (×3) | — | $0 (×3) | — | ~1-2s each | INFRA-BLOCKED — same shared 5-hour quota, all 3 identical `[1308]` errors with the SAME reset timestamp as GLM 5.2's | Confirms the shared-quota finding conclusively — GLM lane fully complete: 5.2 got 1 PASS + 1 interrupted + 4 blocked; 5-Turbo got 2 PASS + 1 interrupted + 3 blocked. |

**Gemini 3.5-flash-lite paid-tier backfill (slot 24, `proj5`) — SUPERSEDES the 4 free-tier quota-blocked rows above for the same 4 tasks:**

| Gemini 3.5-flash-lite | `docs-reconcile` audit (Easy #2, paid-tier retry) | 1 | 33 | — | 549,049 / 20,805 | 2,694,348 | 4.48% | 15.3 min | INFRA-INTERRUPTED (quota again, $3.21 spent) | Paid tier helped (more turns than the free-tier instant fail) but still hit a wall — same partial-signal treatment as before. |
| Gemini 3.5-flash-lite | `escalation-queue-reconciler` audit+gap-check (Medium #1, paid-tier retry) | 0 | 23 | — | 777,085 / 19,418 | 1,699,282 | **66.7%** (peak mid-task — a real spike, not the poller's usual sub-5% range) | 11.7 min | **PASS** | First clean completion for this task — the free-tier attempt never got past 13 turns. |
| Gemini 3.5-flash-lite | repo-touched-capture (Hard #1, paid-tier retry) | 0 | 75 | — | 1,342,762 / 40,378 | 10,031,112 | 5.98% | 60.5 min | **PASS** | First clean completion of ANY Hard-tier task for this model — the free-tier attempt died at 56 turns on quota. Longest single attempt in the whole bake-off so far (60.5 min). |
| Gemini 3.5-flash-lite | `na-eligibility-auditor` audit+fix (Hard #2, paid-tier retry) | 1 | 27 | — | 659,320 / 18,347 | 1,832,982 | 1.43% | 6.6 min | INFRA-INTERRUPTED (quota again, $2.66 spent) | Same as Easy #2 retry — helped but didn't fully clear the wall. |

**Gemini 3.5-flash-lite final tally, all 6 tasks**: 4 clean PASS (Easy #1, Medium #2, Medium #1-retry, Hard #1-retry), 2 INFRA-INTERRUPTED with real partial work (Easy #2-retry, Hard #2-retry). The only model in this bake-off with real coverage across every tier including Hard.

## Progress Log

- **2026-08-19 (interactive session, slot 1)**: Plan authored. Task pool re-verified against the live corpus —
  4 of the original 24 candidates had shipped or had their source doc archived since 2026-08-18 selection; all 4
  swapped for verified-open replacements (see task tables above for the specific swaps + why). Scope confirmed:
  Grok/Kimi excluded (operator), `gemma-4-31b-it` excluded (operator: not working properly), real GLM model ids
  confirmed as `glm-5.2`/`glm-5-turbo` (server-aliased to `glm-5.3`), Claude models explicitly deferred to a later
  plan.

- **2026-08-19 (later, same session) — infrastructure already in place, ZERO of the 36 attempts dispatched yet.**
  Slots 24-29 claimed (`.agent-claim`, 7-day expiry) and mapped 1:1 to the 6 models (table in Mechanics above); all
  confirmed clean/`live-defi-rollout`/in-sync before claiming. The local litellm proxy from yesterday's tool-use
  verification is STILL RUNNING (`~/.venvs/litellm-proxy`, PID persists across sessions via `nohup`+`disown`,
  `127.0.0.1:8768`, config `agent-orchestrator/config/litellm/grok_gemini_proxy.yaml` in slot 1) — reuse it, don't
  rebuild. All 9 required provider secrets already fetched into `~/.claude-accounts/litellm-proxy.env` (mode 600,
  outside any git tree) — reuse them, don't re-fetch from GSM. Real tool_use proof for Gemini/Kimi/DiffusionGemma
  (and Grok's distinct new bug) written back to their SOURCE plans today, not just here — see
  `grok_gemini_translation_proxy_2026_08_14.md` and `kimi_gemma_provider_onboarding_2026_08_16.md` Progress Logs.

  **Open question, not yet answered by the operator**: the `[OPERATOR] P0` todo above was originally framed as
  "enable `account_status`" — that's WRONG, verified by reading `server/state_store/account_usage.py`:
  `account_status: disabled` is pure AO-internal dispatch bookkeeping (`account_is_usable()`, checked only by AO's
  OWN spawn code), never consulted by direct tmux/subprocess dispatch at all — nothing technical blocks this
  bake-off. The REAL open question is a policy one: the operator's standing instruction that paused these accounts
  was framed as usage-policy ("so agents don't use them yet"), not a technical gate — this bake-off IS "using them."
  Asked the operator directly whether their session-long cooperation (fetching keys, approving the proxy/tests) already
  counts as that go-ahead, or whether they want the todo kept as an explicit checkpoint before any of the 36 attempts
  start. **Not yet resolved — do not start dispatching any attempt until this is answered.**

- **2026-08-19 (later) — operator go-ahead received; dispatch mechanism + poller built and proven; 2 more tasks
  caught stale on a SECOND re-verification pass; GLM/Codex lanes blocked/at-risk.** Operator gave explicit
  go-ahead + a new requirement: poll every account's usage stats at <=60s cadence during each attempt, capturing
  context/jsonl/token stats. Built `unified-trading-pm/scripts/dev/bakeoff/{run-attempt.sh,usage-poll.sh}`
  (isolated-branch dispatch + a companion poller reading the running `claude -p` session's own transcript jsonl via
  a fixed `--session-id`). **First bug caught by actually running it**: Claude Code's project-dir naming is
  per-EXACT-cwd (e.g. `-active-...-tabs-24-agent-orchestrator`), not one shared dir per top-level workspace as
  assumed — fixed by deriving the encoded path from the real repo dir instead of hardcoding it. Proven end-to-end
  on a real attempt (Gemini 3.5-flash-lite, slot 24, `ag-closeout-auditor` audit task): real poll data captured
  (23 turns, 7 tool_use calls, 0 tool errors, ~230K cumulative input tokens at the ~90s mark, 1.07% approx
  context-fill) — both `[INFRA] P1` todos' "done when" criteria met.
  **Re-verifying the rest of the matrix before dispatching it turned up 2 more already-shipped tasks** (same
  failure class as the first re-verification pass): Gemini Medium#1 ("join per-task compaction onto
  `TaskUsageRow`") shipped `agent-orchestrator@4a9cf6258`, and Gemini Hard#2 (`GET /api/backlog/graph` dashboard)
  shipped `agent-orchestrator@003aafb608` — both landed AFTER this plan was authored a few hours ago and BEFORE
  dispatch. Swapped for `escalation-queue-reconciler` audit (Medium) and `na-eligibility-auditor` audit-plus-fix
  (Hard) — task tables above updated. **Lesson**: this fleet ships fast enough that even same-session task
  selections can go stale within hours — a real pre-dispatch check immediately before each attempt launches
  (not just once at plan-authoring time) would be more robust than a manual sweep; noted as a possible follow-up,
  not built this session (time-boxed).
  **GLM lane blocked**: fetching the `glm-coding-plan-api-key` GSM secret failed — `ikenna@odum-research.com`'s
  gcloud OAuth session now needs interactive reauthentication ("Reauthentication failed: cannot prompt during
  non-interactive execution"), despite this same identity successfully fetching 9 other secrets earlier in the
  session. Needs the operator to run `gcloud auth login --account=ikenna@odum-research.com` interactively — cannot
  self-resolve. GLM lane (slots 26/27) on hold until then.
  **Codex/Luna lane at risk, not yet attempted**: `codex_bridge_server.py`'s own module docstring states the
  tool-use path "has not yet been proven against the actual `claude` CLI end to end" and its `openai_codex` SDK
  import is deliberately lazy/optional ("this not-yet-deployed bridge process") — real risk this lane simply
  doesn't work yet. `~/.codex/auth.json` confirmed present. Have not yet attempted starting the bridge server
  locally on :8769 for slot 29 — next action for that lane.
  **Dispatched**: slot 24 (Gemini 3.5-flash-lite) running task 1/6 (`ag-closeout-auditor` audit, proof attempt,
  poller confirmed live at ~7min elapsed); slot 25 (Gemini 3.7-flash) launched against the full corrected 6-task
  queue; slot 28 (DiffusionGemma 26B) launched against the full 6-task Gemma queue. All via
  `scripts/dev/bakeoff/run-lane.sh` (sequential per-slot queue runner over `run-attempt.sh`), nohup'd, independent
  of this chat session continuing. Slot 24's remaining 5 tasks will be launched once its task 1 process exits (its
  own `run-attempt.sh` invocation is what I'm waiting on for a completion notification — cannot start task 2 on the
  same checkout while task 1's subprocess is still mid-edit on task 1's branch). GLM (slots 26/27) not yet
  dispatched — see blocker above, unchanged.

- **2026-08-19 (later) — Codex/Luna lane proven + dispatched; task 1 (slot 24) PASSED with full poll data; a
  pre-existing unrelated frontmatter violation blocks shipping the bake-off scripts themselves.**
  Task 1 (Gemini 3.5-flash-lite, `ag-closeout-auditor` audit) finished clean: exit 0, real citations for all 4
  checks, committed locally not pushed, 10.1 min wall-clock, 83 turns, 730K cumulative input tokens — full row in
  Results table above. Slot 24's remaining 5 tasks launched immediately after.
  **Codex/Luna de-risked**: its own code warned the tool-use path was unproven; `uv sync` in slot 1's
  agent-orchestrator pulled the already-declared-but-not-installed `openai-codex` dependency, the bridge server
  started clean on :8769, and a real tool_use smoke test (same shape as yesterday's Gemini/Kimi/Gemma tests)
  returned a genuine `tool_use` block, `stop_reason: "tool_use"` — PASS. Codex/Luna lane (slot 29) dispatched
  against its full 6-task queue.
  **Could not ship `scripts/dev/bakeoff/{run-attempt,usage-poll,run-lane}.sh` via quickmerge yet**: the tree-wide
  re-gate step failed on `plans/active/issues/manifest_hygiene_red_all_2026_08_19.md` — a PRE-EXISTING, unrelated
  auto-filed doc (from `manifest_hygiene_daily.py`) genuinely missing most required frontmatter fields (no
  `doc_type`/`status`/`nature`/`asset_group`/`tags` at all in real HEAD). Attempted a mechanical fix, but it
  cascaded into a further `check_ag_closeout_linkage` requirement (needs a `related:` link to the correct AG's
  consolidated closeout plan) that needs real triage judgment I don't have context for — reverted the attempt
  cleanly (`git checkout HEAD --`, confirmed clean) rather than leave a half-fixed foreign doc. **Flagging for the
  operator**: this doc is a RED manifest-hygiene finding across 5 asset groups (cefi/defi/prediction/sports/tradfi)
  that's also sitting with broken frontmatter — worth someone's attention independent of this bake-off. The
  bake-off scripts themselves stay uncommitted in slot 1 for now (fully described in this Progress Log, reproducible
  from the text above if lost) — will retry shipping once that foreign doc is fixed by whoever owns it, or route
  around it if the tree unblocks another way.

- **2026-08-19 (later, same session) — operator go-ahead received, dispatch unblocked; new polling requirement
  added.** Operator: "yes bro, go ahead and use whatever account you have to use and creds you need. test all these
  6 models properly and make sure that we are also checking the usage stats of each of those accounts every one
  minute when the models are doing some tasks on them ... capture all the context related stats and all the jsonl
  related stats and all the stats that we can get frequently, 30s or 1 min at the most." `[OPERATOR] P0` flipped
  done. New `[INFRA] P1` poller todo added (spec above); building it now, proving it end-to-end on the first real
  attempt alongside the existing isolated-branch-mechanism todo, before scaling to the remaining 35.

- **2026-08-19 (later) — Codex/Luna lane's real dispatch immediately exposed the exact gap its own plan already
  flagged as open: HARD FAIL, not a model-quality result.** All 6 tasks in slot 29's queue ran and exited within
  seconds each (0 real turns, 0 tokens) — every single one hit an identical `API Error: 400` from the bridge:
  `AnthropicMessagesRequest` validation rejects a `system`-role message (`codex_bridge_server.py`'s
  `AnthropicMessage.role: Literal["user", "assistant"]` has no `"system"` case). This is
  `codex_luna_flex_bridge_2026_08_14.md`'s own still-open `[INFRA] P0. Translate system-prompt injection correctly`
  todo, now sharpened to a precise root cause and written back there (its own "smoke-test gate DONE" claim likely
  didn't exercise this workspace's real, full CLAUDE.md as system content the way a genuine dispatched attempt
  does — flagged there for the bridge's own owner to double-check). **Codex/Luna lane is INFRA-BLOCKED, not a real
  Gate-1 result** — all 6 attempts excluded from the Results table below (would misrepresent Codex/Luna's actual
  capability if scored as 6 fails; the model never got a chance to attempt any task). Re-run once the bridge fix
  lands; no further action on this lane from the bake-off side until then.

- **2026-08-19 (later) — Gemini/Gemma free-tier quota wall hit, real $ already spent on failed attempts; a
  paid-tier key exists but is NOT wired into the proxy nor spend-capped — flagging rather than switching myself.**
  Running slots 24+25 concurrently (both hitting Gemini's API) surfaced real free-tier ceilings that are too low
  for a full multi-turn agentic coding task: gemini-3.7-flash slot 25 task 1 hit `RESOURCE_EXHAUSTED` (20
  requests/min free-tier limit) after 9 turns, real cost **$0.74** incurred before failing; gemini-3.5-flash-lite
  slot 24 task 3 hit the free-tier 250K-input-tokens/min cap after 13 turns, **$1.31** incurred. Both are genuine
  infra/quota failures, not real Gate-1 results — do not read either as "the model failed the task." Separately,
  diffusiongemma-26b slot 28 task 2 hit a transient NVIDIA NIM 500 (0 turns, $0 — likely just retry-worthy, not a
  quota issue).
  **A real fix already exists but is NOT applied**: `grok_gemini_translation_proxy_2026_08_14.md` records an
  operator-approved decision (`[x] [OPERATOR] P1`) to add project `371216509644` (confirmed **Paid Tier 3**, vastly
  higher ceilings) as a 4th Gemini project — its key (`GEMINI_API_KEY_PROJ5`) is already fetched into
  `~/.claude-accounts/litellm-proxy.env` from yesterday, but `config/litellm/grok_gemini_proxy.yaml` only wires up
  proj1/proj2/proj3 (all free-tier) — proj5 was never added to the actual proxy config, confirmed by reading the
  file directly. **Deliberately NOT wiring it in myself right now**: switching to a paid, real-money-per-token tier
  for the remaining ~13 free-tier Gemini/Gemma attempts is a real financial-exposure decision, and the source plan
  itself flags an unresolved step — setting a spend-limit on project 371216509644 via the AI Studio console (a
  human/browser action, line ~443 of that plan) — with no evidence that's actually been done. Running the paid tier
  unmetered is the wrong call to make unilaterally while the operator is away, even under the broad go-ahead
  already given for this bake-off. **Letting the already-launched free-tier queues run to completion as-is** (the
  remaining attempts are bounded, worst case another ~$10-15 if every remaining Gemini/Gemma task also hits the
  wall) rather than intervening mid-flight and risking a broken checkout. **Recommendation for the operator**:
  confirm a spend cap is set on project 371216509644, then wire `proj5` into the proxy yaml (mirrors the existing
  proj1-3 block exactly) and re-run whichever Gemini/Gemma tasks failed on quota through the paid tier for a real
  result.

- **2026-08-19 (later) — slot 25 (Gemini 3.7-flash) is a COMPLETE quota washout: 6/6 tasks failed, zero real
  signal.** Confirmed via each attempt's own `result.json`: task 1 ran 9 real turns before `RESOURCE_EXHAUSTED`
  ($0.74 spent), tasks 2-6 each failed on their VERY FIRST request (1 turn, $0 each) — the 20-req/min free-tier
  quota never had time to recover in the 30s between queued tasks. **Gemini 3.7-flash produced literally zero
  usable Gate-1/Gate-2 data this run** — every row would be quota-noise, not model signal. Excluded from the
  Results table entirely (same treatment as Codex/Luna) pending a paid-tier re-run.
  **Gemini 3.5-flash-lite (slot 24) faring better** (larger free-tier ceiling: 250K tokens/min vs. 3.7-flash's 20
  req/min): 2 real completions so far (task 1 PASS already in Results table; task 4 tmux-fixture-audit also
  completed clean, `is_error:false`, 27 turns, $3.05 — pending a Results row once reviewed), 2 quota fails (tasks
  2 and 3), task 5 still running.
  **Gemma (slot 28, DiffusionGemma 26B) hitting a DIFFERENT wall — NVIDIA NIM `InternalServerError` on every real
  attempt so far (4/4), but NOT a dead endpoint**: a direct simple single-turn smoke test against the same
  `diffusiongemma-26b-a4b-it` endpoint just now returned a clean 200 — the failure is specific to the FULL real
  Claude Code request shape (real CLAUDE.md system prompt + the full multi-tool schema array Claude Code sends),
  not the model being down. Likely a payload-size or tool-schema-count limit on this free-hosted NIM endpoint, not
  yet root-caused precisely — flagging the pattern, not yet diagnosed to the same depth as the Codex bug. 2 tasks
  remain; if they fail identically, this lane's results need the same "infra-blocked, not a real result" treatment
  once confirmed.

- **2026-08-19 (later) — Gemma lane confirmed 6/6 complete washout (same pattern, now proven not a one-off);
  slot 24 task 4 (tmux-fixture audit) landed a second real PASS.** All 6 diffusiongemma-26b attempts failed
  identically (1 turn, $0 each) — 4 with `InternalServerError` (500), 2 with `BadGatewayError` (502), both
  "server-side issue, usually temporary" per the error text itself. Same lane treatment as Codex/Luna: zero usable
  data, excluded from real results, root cause not yet pinned down (flagged for a future pass, not this session).
  Slot 24 (gemini-3.5-flash-lite) task 4 (tmux-fixture-audit, Medium) finished clean: 27 turns, 1 tool_error
  (non-blocking), $3.05, 11.3 min, `is_error:false` — second real PASS for this model. Full Results table above
  now reflects every attempt's true status (real pass/fail vs. infra-blocked) rather than conflating them.
  **Running total so far**: only Gemini 3.5-flash-lite has produced any real signal this run (2 PASS, 2
  quota-blocked, 2 still in flight) — every other model's lane is either 100% infra-blocked or still pending. This
  bake-off's infra had more real bugs waiting in it than expected; that is itself the most useful thing found
  today, arguably more valuable than the model-quality data it was designed to produce.

- **2026-08-19 (later) — slot 24 (Gemini 3.5-flash-lite) finished all 6 tasks; a real `run-attempt.sh` bug found
  and fixed; every unblocked lane is now COMPLETE.** Tasks 5 and 6 (both Hard) each did substantial REAL work — 56
  and 42 real turns, $6.45 and $4.13 spent — before hitting the same quota-driven 403 that killed tasks 2/3.
  Confirmed via a direct `git status --porcelain` on slot 24's live checkout that the tree is clean (no
  lost/uncommitted work — the model simply never reached its own `git commit` step before failing), so nothing was
  lost, but neither task produced a scoreable Gate-1 result. **Final gemini-3.5-flash-lite tally: 2 clean PASS
  (Easy #1, Medium #2), 4 quota-interrupted at varying depth (2 instant, 2 after 40-60 real turns)** — every row
  now in the Results table above.
  **Real infra bug found while investigating why tasks 5/6 had no `exit_code.txt`/`finished_at.txt`/
  `git_status.txt`**: `run-attempt.sh` ran under `set -euo pipefail`, and `wait "$CLAUDE_PID"` returning the
  `claude` process's own non-zero exit code triggered errexit immediately — skipping every postprocessing line
  after it (including the very evidence needed to diagnose the failure) on ANY attempt that ends in error. Fixed
  (`set +e` around just the `wait`, restore `set -e` after) — applies to every future attempt including once GLM
  unblocks. Not yet re-shipped (blocked on the same pre-existing foreign-doc quickmerge issue noted above).
  **Session status: all 4 unblocked lanes (Gemini 3.5-flash-lite, Gemini 3.7-flash, DiffusionGemma 26B, Codex/Luna)
  have now run their full 6-task queues to completion.** Only GLM (slots 26/27) remains fully undispatched, still
  blocked on the operator's gcloud reauth. Nothing further to auto-dispatch until either GLM unblocks or a decision
  is made on the paid-tier Gemini re-run — pausing autonomous work on this plan here pending operator input on
  both open items.

- **2026-08-19 (later) — context-fill% was wrong for every Gemini attempt: understated by 5x, now corrected.**
  Prompted by the operator asking to double-check the Gemini 3.5-flash-lite stats. `run-attempt.sh`'s poller was
  launched with a hardcoded `1,000,000`-token context-window assumption for both Gemini models. Claude Code's own
  `result.json` carries the TRUE value in `modelUsage.<model>.contextWindow` — checked directly for both models:
  **200,000**, not 1,000,000, for `gemini-3.5-flash-lite-proj1` and `gemini-3.7-flash-proj1` alike. Every
  context-fill% already recorded in the Results table above for a Gemini attempt has been corrected (divide the
  same `approx_context_used_tokens` numerator by 200,000 instead of 1,000,000 — all 4 gemini-3.5-flash-lite rows
  with real data updated in place, each now shows both the corrected and original value). DiffusionGemma's
  `32,000`-token assumption (used at launch, not yet contradicted by any `modelUsage` value since it never
  completed a real turn) is left as-is — no better source available yet. **Also confirmed slot 25's (Gemini
  3.7-flash) live git checkout directly**: clean tree, same as slot 24 — none of its 6 infra-blocked attempts left
  any lost/uncommitted work either.

- **2026-08-19 (later) — operator approved wiring the paid-tier Gemini project (371216509644); wired, verified,
  re-dispatched.** Operator confirmed: their Gemini Pro subscription (the consumer app) does NOT grant API access
  (verified against Google's own docs before answering — separate product from the API/AI Studio billing this
  fleet actually uses) — the correct mechanism remains the already-identified Paid Tier 3 project. Added
  `gemini-3.5-flash-lite-proj5`/`gemini-3.7-flash-proj5` to `config/litellm/grok_gemini_proxy.yaml`, mirroring the
  existing proj1-3 blocks exactly. **Spend cap on project 371216509644 still not independently verified** —
  `ikenna@odum-research.com`'s gcloud session hit the same reauth wall as the GLM blocker, so I couldn't check via
  `gcloud billing`; proceeding on the operator's explicit "yes wire it" rather than blocking a second time, but
  this residual risk is real and worth the operator confirming directly in the AI Studio console when free.
  **Hit and fixed a real proxy-restart bug**: `~/.claude-accounts/litellm-proxy.env` uses plain `VAR=value` (no
  `export`), so a bare `source` in the same shell as a backgrounded `nohup` does NOT propagate the vars to the
  child process — the first 2 restart attempts both failed with `Missing Gemini API key` even though the file
  genuinely had the right value. Fixed via a small wrapper script (`set -a; source; set +a; exec litellm`) —
  confirmed the key was actually visible (39 chars, matches expected length) before trusting the next smoke test.
  **Real smoke test against proj5 passed**: HTTP 200, properly billed, no `RESOURCE_EXHAUSTED`.
  **Re-dispatched**: slot 25 running Gemini 3.7-flash's full 6-task queue again via `gemini-3.7-flash-proj5`
  (model label `gemini-3.7-flash-paidtier`, context-window arg corrected to the real 200,000 this time); slot 24
  backfilling its 4 previously quota-blocked Gemini 3.5-flash-lite tasks via `gemini-3.5-flash-lite-proj5` (model
  label `gemini-3.5-flash-lite-paidtier`). Both use the corrected poller default. Results will land as separate
  rows (labeled `-paidtier`) rather than overwriting the free-tier rows above, so the free-tier quota-wall finding
  stays on record even after the paid-tier re-run completes.

- **2026-08-19 (later) — GLM's real blocker is account balance, not gcloud auth; Gemma's NVIDIA NIM issue confirmed
  server-side after ruling out every request-shape hypothesis.**
  **GLM**: bypassed the `ikenna@odum-research.com` gcloud reauth wall entirely — found an already-cached, ready
  credential file at `~/.claude-accounts/zai.env` (GLM 5.2 via Z.ai's native endpoint, `export`-format, dated
  2026-08-04, predates this plan). A real smoke test against it returned a clean application-level error, NOT an
  auth failure: `429 {"code":"1113","message":"[1113][Insufficient balance or no resource package. Please
  recharge.]"}`. The credential itself is valid — Z.ai recognized and processed the request — but the GLM Coding
  Plan subscription's balance/resource package is exhausted or expired. **This is an operator action (recharge the
  Z.ai account), not a technical blocker** — the gcloud reauth issue is now moot for GLM regardless of whether it
  ever gets fixed. GLM 5-Turbo's credential/model-string not yet separately verified (same account, different
  `ANTHROPIC_MODEL` value — blocked on the same balance issue either way).
  **Gemma/DiffusionGemma**: ruled out every request-shape hypothesis via direct curl reproduction — a 54KB system
  prompt (10,568 tokens) with 1 tool: 200 OK; 16 realistic multi-field tool schemas: 200 OK; a real streaming
  (`stream:true`) tool-call request: 200 OK. None reproduced the failure. A real `claude -p` dispatch (not curl)
  against the same endpoint then produced a FOURTH distinct failure mode within one investigation — after 500,
  502, and the earlier confirmed cold-start timeout, this one returned a clean `429 Too Many Requests` (partly
  self-inflicted — the several rapid synthetic curl tests just before it added real load to the same endpoint).
  **Conclusion: this is NVIDIA-side undercapacity/instability on their free-hosted NIM endpoint for this model**,
  not a bug in our proxy config or in Claude Code's real request shape — four different failure signatures from
  the same free endpoint under real-world load is a server-capacity pattern, not a deterministic client-side bug.
  No further request-shape debugging planned; the real fix (if one exists) is either a paid/dedicated NIM tier or
  accepting this lane's ceiling is unreliable on the free tier.

- **2026-08-19 (later) — CORRECTION to the GLM finding above: `zai.env` was the WRONG, older, unrelated account.
  The real GLM Coding Plan account's blocker is confirmed to be the ORIGINAL gcloud-reauth wall after all, not
  balance.** Operator clarified `~/.claude-accounts/zai.env` (found and tested above) is a DIFFERENT, older
  personal account they never funded — not the one Ikenna set up with a real balance. Pulled the real account
  files directly off the orchestrator VM via AWS SSM (`i-0c9b283b31d6b5ca7`, `ap-northeast-1`, read-only
  `send-command`/`get-command-invocation`, no VM state changed): `/home/ubuntu/.claude-accounts/glm-5-2.env` and
  `glm-5-turbo.env` — both real, both registered in AO's live `/api/accounts` (`account_status: None` = healthy,
  not disabled). **But both files' `ANTHROPIC_AUTH_TOKEN` is a LIVE command substitution, not a static value**:
  `export ANTHROPIC_AUTH_TOKEN="$(gcloud secrets versions access latest --secret=glm-coding-plan-api-key
  --project=central-element-323112)"` — evaluated fresh every time the file is sourced, by whatever gcloud identity
  is active in that shell. Confirmed this fails EVERYWHERE tried: locally as `ikenna@odum-research.com`
  (reauth-blocked, same wall as before), locally as `harshkantariya.work@gmail.com` (`PERMISSION_DENIED` — real
  identity, wrong IAM grant), and even ON THE VM ITSELF as its own default `github-actions-deploy@central-element-
  323112.iam.gserviceaccount.com` (`PERMISSION_DENIED` too) — meaning this exact gap likely also affects AO's own
  real production GLM dispatch, not just this bake-off, if AO's spawn path sources this file the same way (worth
  the operator independently checking whether GLM has actually dispatched successfully recently, separate from
  this bake-off). **The most viable fix remains `ikenna@odum-research.com` reauth**: it's the one identity that
  already proved it has real access to other secrets in this same project earlier today, so it's the most likely
  to already hold the right IAM grant here too — the reauth, not a missing grant, is the actual blocker for it.
  Deleted the empty/broken local copies rather than leave misleading zero-length credential files sitting in
  `~/.claude-accounts/`.

- **2026-08-19 (later) — paid-tier Gemini re-run came back MIXED, not clean: the "Paid Tier 3" upgrade is only
  partially effective, real $ spent either way.** `gemini-3.7-flash-paidtier` (slot 25): 6/6 STILL failed — task 1
  got 11 turns/$0.67 before a 429, tasks 2-6 failed instantly — and the error text explicitly names
  `generate_content_free_tier_requests` as the exhausted metric, on the SAME project we just wired as "confirmed
  Paid Tier 3." `gemini-3.5-flash-lite-paidtier` (slot 24, the 4-task backfill): task 2 hit the identical
  `free_tier`-labeled 429 again ($3.21 spent first); task 3 (`escalation-queue-reconciler`) got a REAL clean PASS
  this time — 23 turns, $3.30, `is_error:false`; task 5 still in flight.
  **Conclusion: enabling billing on project 371216509644 did not uniformly lift every quota metric** — some
  requests now get real headroom (task 3's pass), but the specific `generate_content_free_tier_requests` RPM-style
  metric is still gating other requests as if the project were free-tier, even though line ~420 of
  `grok_gemini_translation_proxy_2026_08_14.md` says this project was independently confirmed Paid Tier 3 on
  2026-08-16. This is a known Google Cloud pattern (billing-enabled lifts SOME default caps, others need an
  EXPLICIT quota-increase request via the console, not just billing) — worth the operator checking the AI Studio
  quota page for this specific metric on project 371216509644, not just the billing/spend-cap page.
  **PAUSING further paid-tier Gemini dispatch here** — real money continues to accumulate ($0.67 + $3.21 this
  round, on top of the earlier free-tier spend) for a fix that is not yet reliably working; not continuing to burn
  spend on a partially-broken paid tier without the operator's input on whether to pursue the quota-increase path
  or accept the current data as-is.

- **2026-08-19 (later) — GLM finally unblocked: operator re-authenticated as `harshkantariya@odum-research.com`,
  real funded credential fetched, both models tool_use-verified, both lanes dispatched.** `gcloud auth login
  --account=harshkantariya@odum-research.com` (operator, interactive) plus `gcloud config set account` resolved
  what 3 other identities (`ikenna@odum-research.com` reauth-blocked, `harshkantariya.work@gmail.com` and the VM's
  own `github-actions-deploy@...` both permission-denied) could not: a clean fetch of the real
  `glm-coding-plan-api-key` secret (49 bytes). Built `~/.claude-accounts/glm-5-2.env`/`glm-5-turbo.env` with this
  real key (static value this time, not the VM files' live-gcloud-lookup pattern). Both smoke-tested clean before
  any real dispatch: plain-text (200 OK, real content, GLM 5.2's response confirms the known 5.2→5.3
  server-aliasing) AND a real tool_use exchange on GLM 5.2 (200 OK, real `tool_use` block, `stop_reason:
  "tool_use"`) — this fleet's first-ever confirmation that GLM's native endpoint handles tool-calling correctly,
  closing a gap the source onboarding plan had left explicitly open. Re-verified all 6 GLM-lane tasks' checkboxes
  still open (unchanged from original selection). Dispatched: slot 26 (GLM 5.2) and slot 27 (GLM 5-Turbo), both
  against the full 6-task queue, poller at 30s/128K-context-window (Z.ai's real window not yet confirmed via a
  `modelUsage`-equivalent field the way Gemini's was — 128K is an estimate, flag any correction the same way the
  Gemini one was caught). Results will land in the Results table as both lanes complete.

- **2026-08-19 (later, from slot 2) — independently reconfirmed a SECOND working credential path for GLM
  (`ikenna@odum-research.com`, not just `harshkantariya@odum-research.com`), and answered the operator's standing
  question on AO visibility into the Gemini/Gemma quota walls.** Operator ran `gcloud auth login
  --account=ikenna@odum-research.com` interactively; `gcloud auth list` now shows it active with no reauth wall.
  Fetched `glm-coding-plan-api-key` directly from GSM (succeeded) and smoke-tested `api.z.ai/api/anthropic/v1/messages`
  (`model: glm-5.2`): HTTP 200, real billed response (`model: "glm-5.3"`), no `RESOURCE_EXHAUSTED`/`429`. Useful as a
  fallback path now that both identities are confirmed working, on top of the already-dispatched slots 26/27 above —
  no action needed on this lane, it's covered.
  **AO-visibility answer**: none of this run's quota exhaustion was ever visible to AO — Mechanics is explicit this
  bake-off used "direct tmux/subprocess dispatch — no local AO backend instance, no real AO backlog involved," so
  every `RESOURCE_EXHAUSTED`/`429` was only ever caught reactively via each attempt's own CLI exit code, never AO
  telemetry. Even a real AO-mediated dispatch wouldn't have caught it proactively today either: the
  `GLMQuotaPoller`/`DeepSeekBalancePoller` headroom-gating pattern (writes `five_hour_pct`/`weekly_pct` onto
  `AccountUsageRow`, read by `autospawn._pick_headroom_account` for any provider with zero extra wiring) has no
  Gemini/Gemma equivalent (confirmed via `server/config.py` grep — no `gemini_*_ceiling`/poller analog exists). It
  WAS knowable ahead of time the cheap way, though: the ceilings actually hit are publicly documented free-tier
  numbers (20 req/min for `gemini-3.7-flash`, 250K input-tokens/min for `gemini-3.5-flash-lite`) — pacing/serializing
  the 6 queued tasks instead of 30s spacing would have avoided most of the washout, matching this plan's own earlier
  conclusion. Not opening a `GeminiQuotaPoller` todo unilaterally — flagging as a real, buildable gap for the
  operator to decide is worth tracking, given this bake-off is close to done.

- **2026-08-19 (later) — GLM lane result: both models produced real signal before hitting a SHARED 5-hour
  account-level usage quota, not a per-model one.** GLM 5.2's full lane: 1 clean PASS (task 1), 1
  INFRA-INTERRUPTED with substantial real work (task 2, 90 turns/$6.30 before the cutoff), 4 instant
  INFRA-BLOCKED. GLM 5-Turbo: 2 clean PASS (tasks 1-2), 1 INFRA-INTERRUPTED (task 3, 81 turns/$4.40), tasks 4-6
  still resolving but expected to be instant-blocked like GLM 5.2's tail. **Confirmed the quota is shared across
  BOTH models, not independent per-model budgets**: GLM 5-Turbo's task 3 hit the identical `[1308] Usage limit
  reached for 5 hour` error with the EXACT same reset timestamp (2026-08-20 00:22:34 UTC) as GLM 5.2's — running
  both models concurrently split one account's budget rather than getting two separate ones, the same lesson as
  the Gemini free-tier concurrency finding above. Real value delivered regardless: this is the fleet's first-ever
  confirmed real tool-use dispatch through GLM's native endpoint, with 3 full clean completions and 2 substantial
  partial ones as real evidence, not just a smoke test.

- **2026-08-19 (later) — ALL 36 planned attempts across all 6 models have now run (or been confirmed
  infra-blocked). Full-bake-off status, no lane still dispatching:**

  | Model | Clean PASS | Interrupted (real partial work) | Infra-blocked (0 real signal) | Real infra bug found |
  |---|---|---|---|---|
  | Gemini 3.5-flash-lite | **4/6** | 2/6 | 0/6 | Wrong context-window constant (fixed) |
  | Gemini 3.7-flash | 0/6 | 0/6 | 6/6 (free) + 6/6 (paid retry) | Free-tier AND partially the "paid" tier both quota-walled |
  | GLM 5.2 | 1/6 | 1/6 | 4/6 | none (Z.ai-side quota, not a bug) |
  | GLM 5-Turbo | 2/6 | 1/6 | 3/6 | none |
  | DiffusionGemma 26B | 0/6 | 0/6 | 6/6 | NVIDIA-side instability, 4 distinct failure modes, confirmed not our request shape |
  | Codex/Luna | 0/6 | 0/6 | 6/6 | Bridge rejects `system`-role messages — real code bug, root-caused |

  **Real capability signal exists for exactly 2 of 6 models** (Gemini 3.5-flash-lite, GLM — both models). The
  other 4 produced zero usable Gate-1/2 data this run, each for a distinct, now-documented reason. **This
  session's actual biggest yield was infrastructure**, not model rankings: 2 real provider bugs found and either
  fixed (context-window) or root-caused for someone else to fix (Codex bridge), 1 confirmed vendor-side
  reliability problem (NVIDIA NIM), 1 confirmed shared-quota mechanic (GLM), and working, reusable dispatch +
  30s-cadence polling infrastructure now proven end-to-end for any future bake-off round.
  **Still open, needs the operator**: (1) whether to pursue a Gemini quota-INCREASE request (separate from
  billing) for `generate_content_free_tier_requests` on project 371216509644; (2) whether Gemma is worth a retry
  given NVIDIA's confirmed instability, or should be dropped from consideration; (3) the Codex bridge fix is real
  engineering work belonging to `codex_luna_flex_bridge_2026_08_14.md`, not this plan; (4) GLM's 5-hour quota
  resets 2026-08-20 00:22:34 UTC — the remaining 7 blocked GLM tasks (4 for 5.2, 3 for 5-Turbo) could be re-run
  serially (not concurrently) after that to get full 6/6 coverage on both models. Gate-2 quality scoring on the
  Gate-1 passers, and the final per-(model, tier) synthesis table, are the two todos still not started.

- **2026-08-19 (later) — REAL root cause found for why the "paid tier" Gemini re-run still failed: `gcloud alpha
  services quota list` shows the Paid Tier 3 quota bucket is genuinely provisioned (20,000 req/min for BOTH
  `gemini-3.5-flash-lite` and `gemini-3.7-flash` on project `central-element-323112`) — the ceiling was never the
  problem. Free-tier limits on the SAME project, for comparison: `gemini-3.7-flash` = 5 req/min,
  `gemini-3.5-flash-lite` = 15 req/min (both lower than the `RESOURCE_EXHAUSTED` messages' own stated "limit: 20"
  suggested — there are multiple overlapping bucket rules, the per-model dimension is the binding one).** The real
  problem: our actual requests were still being billed against `generate_content_free_tier_requests`, not
  `generate_content_paid_tier_3_requests`, despite using `GEMINI_API_KEY_PROJ5`. This matches a known Google AI
  Studio gotcha — an API key generated BEFORE Cloud Billing was enabled on its project can stay classified as
  free-tier indefinitely; the quota bucket gets provisioned but the key doesn't automatically re-associate with
  it. **Fix, not yet done**: regenerate the API key for project 371216509644 via
  https://aistudio.google.com/app/apikey (after confirming billing is genuinely active), swap the regenerated
  value into `GEMINI_API_KEY_PROJ5`, and re-test before trusting `proj5` for any further dispatch — the current
  key is not reliably drawing on the paid pool it's nominally provisioned for.
  **Live status snapshot (2026-08-19T12:44 UTC)**: Gemini (both free proj1 and paid proj5) — both respond 200 OK
  to a single lightweight probe right now (a single request never trips a per-minute limit either way, so this
  confirms nothing about tier routing, only that neither key is dead). NVIDIA/Gemma — also 200 OK on a
  trivial single-turn probe right now, consistent with the earlier finding that it fails specifically on full-size
  real requests, not universally. GLM — still inside its 5-hour lockout, **11h38m remaining** at check time,
  resets 2026-08-20T00:22:34Z.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche batch 3/3)**: KEEP-NA, valid — doc's own frontmatter/Why section
  explicitly rules this a HUMAN plan ("scoring needs human/review-agent judgment... not bounded deterministic work
  an isolated AO worker could complete alone"). Both remaining open items (direct diff-vs-diff comparison on the 2
  shared Hard tasks; synthesize the final per-model/per-tier summary + routing recommendation) require exactly that
  judgment. No bounded item found.
