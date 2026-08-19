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
| Medium | Join per-task compaction occurrence onto `TaskUsageRow` | `ao_satellite_ao_dispatch_batch24_2026_08_18.md` |
| Medium | Audit other repos for the same unscoped-tmux-fixture test anti-pattern | `issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md` — *swapped in 2026-08-19, replaces `DirtyStateResolution.COMMIT_AND_PUSH` fix whose source doc is now fully archived* |
| Hard | Capture which repo(s) a task touched, from real commit/push evidence (no existing mechanism to mirror) | `ao_satellite_ao_dispatch_batch24_2026_08_18.md` — *shared with Codex/Luna, see below* |
| Hard | Build `GET /api/backlog/graph` + hand-rolled-SVG dependency-graph dashboard view (no d3/mermaid allowed) | `issues/ao_residuals_after_dispatch_hardening_2026_07_17.md` |

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

Each of the 36 (model, task) attempts runs in its OWN isolated git branch/worktree off `live-defi-rollout` — never
directly on a shared branch — so the 2 shared-Hard-task pairs don't collide and no attempt's diff pollutes another's.
A `claude` CLI subprocess is spawned per attempt with `ANTHROPIC_BASE_URL`/`ANTHROPIC_MODEL` set to the target model
(litellm proxy :8768 for Gemini/Gemma, native `api.z.ai` for GLM, `codex-bridge` :8769 for Codex/Luna). No attempt's
diff auto-merges — Gate 1/2 scoring + the shared-task diff comparison decide what (if anything) actually ships via
normal `quickmerge.sh`.

## Todos

- [ ] [OPERATOR] P0. Temporarily enable `account_status` for exactly the accounts this bake-off needs (1 Gemini
      project pair per model variant tested, the GLM Coding Plan account, 1 NVIDIA/Gemma account, the Codex/Luna
      account) — every one is currently paused per standing 2026-08-16 operator instruction ("fully shipped ready
      to use but on pause mode"). Re-disable each account once its 6 attempts are recorded. Done when: all 6 models'
      accounts show `account_status: enabled` for the duration of their own run only.
- [ ] [INFRA] P1. Stand up the isolated-branch-per-attempt dispatch mechanism described in Mechanics above (36
      branches off `live-defi-rollout`, one `claude` subprocess per attempt, env pointed at the right
      proxy/endpoint). Done when: one real end-to-end attempt (any model, any task) produces an isolated branch
      with a real diff and no collision with the base branch.
- [ ] [BACKEND] P2. Run Gemini 3.5 Flash-Lite against all 6 Gemini-lane tasks; record Gate 1/2 scores + tokens/
      context-fill/turns/time per attempt. Done when: 6 rows exist in the Results table below (or a stated
      pass/fail/blocked reason per attempt).
- [ ] [BACKEND] P2. Run Gemini 3.7 Flash against the same 6 Gemini-lane tasks; record the same metrics.
- [ ] [BACKEND] P2. Run GLM 5.2 against all 6 GLM-lane tasks; record the same metrics (note the 5.2→5.3
      server-aliasing when interpreting which model actually answered).
- [ ] [BACKEND] P2. Run GLM 5-Turbo against the same 6 GLM-lane tasks; record the same metrics.
- [ ] [BACKEND] P2. Run DiffusionGemma 26B against all 6 Gemma-lane tasks; record the same metrics.
- [ ] [BACKEND] P2. Run Codex/Luna against all 6 Codex-lane tasks; record the same metrics.
- [ ] [REVIEW] P1. Direct diff-vs-diff comparison on the 2 shared Hard tasks (repo-touched-capture: Gemini vs.
      Codex/Luna; sequential-ordering root-cause: GLM vs. Codex/Luna) — this is the single strongest signal in the
      trial, weight it accordingly in the final synthesis. Done when: a written verdict exists for both pairs.
- [ ] [DATA] P2. Synthesize the final per-(model, complexity-tier) summary table (pass-rate, avg Gate-2 score, avg
      tokens, avg context-fill%, avg turns, avg time, $ cost) into this plan's Progress Log. Done when: the table
      covers all 6 models × 3 tiers and states an explicit recommendation for which model tier future AO dispatch
      should route each complexity level to.

## Results

_(populated as each model's run completes)_

## Progress Log

- **2026-08-19 (interactive session, slot 1)**: Plan authored. Task pool re-verified against the live corpus —
  4 of the original 24 candidates had shipped or had their source doc archived since 2026-08-18 selection; all 4
  swapped for verified-open replacements (see task tables above for the specific swaps + why). Scope confirmed:
  Grok/Kimi excluded (operator), `gemma-4-31b-it` excluded (operator: not working properly), real GLM model ids
  confirmed as `glm-5.2`/`glm-5-turbo` (server-aliased to `glm-5.3`), Claude models explicitly deferred to a later
  plan.
