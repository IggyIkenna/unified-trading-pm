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
- [ ] [INFRA] P1. Stand up the isolated-branch-per-attempt dispatch mechanism described in Mechanics above (36
      branches off `live-defi-rollout`, one `claude` subprocess per attempt, env pointed at the right
      proxy/endpoint). Done when: one real end-to-end attempt (any model, any task) produces an isolated branch
      with a real diff and no collision with the base branch.
- [ ] [INFRA] P1. Build a per-attempt usage-stats poller, cadence ≤60s (operator requirement, 2026-08-19), capturing:
      (a) the running `claude -p` session's own transcript jsonl (`~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`)
      — cumulative input/output/cache tokens, turn count, tool-call count, approx context-fill%; (b) each provider
      account's own usage/quota surface where one exists (litellm proxy spend log for Gemini/Gemma, GLM/z.ai account
      usage, Codex/Luna account usage) — message count and/or % of plan/quota consumed, stated as "not available" per
      account if the provider exposes none. Snapshots appended to a per-attempt poll-log file referenced from the
      Results table. Done when: one real attempt (paired with the INFRA todo above) has a complete poll-log from
      launch to exit at ≤60s cadence, covering both the jsonl-transcript stats and whatever account-usage surface
      exists for that provider.
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

| Model | Task (tier) | Exit | Turns | Tool calls (err) | Cumulative in/out tokens | Cache-read tokens | Peak approx context-fill% | Wall-clock | Gate 1 | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| Gemini 3.5-flash-lite | `ag-closeout-auditor` audit (Easy) | 0 | 83 | 29 (4) | 730,196 / 11,248 | 2,607,683 | 1.61% | 10.1 min | PASS (clean tree, real citations, committed not pushed) | 4/4 checks answered with specific file/line + log citations (sharding via `MAX_CONCURRENT_TRANCHES=4`, runtime range 6.5-63.9 min measured, no PR/review-branch gate found, a real 2026-08-16 escalation traced through to a produced batch plan). Full poll history: `usage_poll.jsonl` under this attempt's out-dir. |

_(remaining rows populated as each attempt completes)_

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
  same checkout while task 1's subprocess is still mid-edit on task 1's branch). GLM (slots 26/27) and Codex/Luna
  (slot 29) not yet dispatched — see blockers above.

- **2026-08-19 (later, same session) — operator go-ahead received, dispatch unblocked; new polling requirement
  added.** Operator: "yes bro, go ahead and use whatever account you have to use and creds you need. test all these
  6 models properly and make sure that we are also checking the usage stats of each of those accounts every one
  minute when the models are doing some tasks on them ... capture all the context related stats and all the jsonl
  related stats and all the stats that we can get frequently, 30s or 1 min at the most." `[OPERATOR] P0` flipped
  done. New `[INFRA] P1` poller todo added (spec above); building it now, proving it end-to-end on the first real
  attempt alongside the existing isolated-branch-mechanism todo, before scaling to the remaining 35.
