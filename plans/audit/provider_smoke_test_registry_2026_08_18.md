---
doc_type: plan
title: Multi-provider LLM fleet — per-provider smoke-test signoff registry (Gate 1)
summary: >-
  Living registry answering, per AO fleet provider (Claude, DeepSeek, GLM, Gemini, Codex/Luna, Gemma — Kimi tracked but
  excluded from fleet scope per standing operator ruling), whether the provider's accounting/dispatch mechanics have
  been verified correct ONCE for that provider (not per-model — once one model works for a provider, its siblings don't
  need re-testing) across 8 dimensions: input/output cache vs. non-cache pricing, reasoning-token handling, token-count
  accuracy, tool calls, chained bash commands, provider-specific reset-window semantics, "max tier" behavior where
  applicable, and whether the provider's own subscription/quota-limit is directly readable vs. needs a workaround. This
  is Gate 1 of the 8-gate provider-readiness framework (Gates 2-3 live in each provider's own onboarding plan; Gate 4
  lives HERE, see below, to keep it out of the near-line-cap deepseek_claude_blended_provider_routing plan; Gates 5-6
  are that plan's own Phase 4/5; Gates 7-8 are in multi_provider_context_billing_reconciliation)
  — a provider cannot clear Gate 2 (real task dispatch) until every ✅-required row here is checked. Initial fill
  (2026-08-18) is derived from cross-referencing the 5 provider onboarding plans' own Progress Logs, not a fresh
  from-scratch verification pass — treat an initial ✅ as "evidence already exists in the source plan," and re-verify
  before trusting a ⚠️/❌ cell as final.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, provider-onboarding, smoke-test, gate, multi-provider, registry, audit]
related:
  [
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/grok_gemini_translation_proxy_2026_08_14.md,
    /plans/archive/2026_08/kimi_gemma_provider_onboarding_2026_08_16.md,
    /plans/active/codex_luna_flex_bridge_2026_08_14.md,
    /plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md,
    /plans/active/issues/claude_anthropic_flat_rate_billing_calibration_2026_08_12.md,
    /codex/06-coding-standards/model-tier-selection.md,
  ]
created: 2026-08-18
last_updated: 2026-08-18
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
context_scope:
  [
    agent-orchestrator/server/state_store/account_usage.py,
    agent-orchestrator/server/usage_poller.py,
    agent-orchestrator/server/model_pricing.py,
    agent-orchestrator/server/deepseek_usage.py,
    agent-orchestrator/server/gemini_headroom.py,
  ]
supersedes:
superseded_by:
depends_on:
source: >-
  Operator request 2026-08-18 (interactive session) — a cross-provider "have we actually verified accounting/dispatch
  correctness once per provider" checklist that persists across account resets/rotations and can be re-derived from the
  HTML artifact regeneration, distinct from the per-provider onboarding plans' own scattered Progress Log evidence.
---

# Multi-provider LLM fleet — per-provider smoke-test signoff registry (Gate 1)

> **What this is, and isn't.** This is a REGISTRY, not a place to do the work — each cell links back to the provider's
> own onboarding plan, where the actual verification runs and evidence lives. Flip a cell here only when you can point
> to real evidence in the source plan (a Progress Log entry, a commit, a pasted test/probe output) — never on
> assumption. A provider's overall Gate-1 verdict is PASS only when every row that applies to it (some dimensions are
> genuinely N/A for some providers — e.g. "max tier" has no meaning for Gemini's free-tier-only setup) reads ✅.
>
> **Legend**: ✅ verified with cited evidence · ⚠️ partially verified / structurally different from Claude's approach,
> not simply missing · ❌ confirmed broken or unbuilt · — not yet attempted · N/A dimension doesn't apply to this
> provider's product shape.

## Registry (as of 2026-08-18)

| Dimension                              | Claude                                                    | DeepSeek                                              | GLM                                                | Gemini                                                     | Codex/Luna                                                | Gemma (NVIDIA NIM)                                    |
| --------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------ | -------------------------------------------------------------- | ---------------------------------------------------------- |
| Input/output cache vs. non-cache pricing | ✅ native Messages API, no lossy layer, 3-tier cache pricing in `model_pricing.py` | ✅ cache-discount math verified against real spend (pilots) | — not yet smoke-tested; accurate-usage-capture proxy still open | — not yet smoke-tested                                     | — not yet smoke-tested                                     | — not yet smoke-tested                                    |
| Reasoning-token handling                | ⚠️ N/A-by-design — Anthropic folds thinking into `output_tokens`, no separate field, confirmed via docs + live transcript (2026-08-13) | ✅ native `completion_tokens_details.reasoning_tokens` field, working | — not yet smoke-tested                             | — not yet smoke-tested                                     | — not yet smoke-tested                                     | — not yet smoke-tested                                    |
| Token-count accuracy                    | ✅ native, no translation layer                             | ✅ verified post-proxy-fix (was lossy pre-fix, now closes the gap) | — not yet smoke-tested                             | ⚠️ request-count tracked (RPM/TPM/RPD gate); $/token accuracy not independently confirmed | ❌ **known bug** — "Codex's fake token estimate," open `[INFRA] P0` to fix | ✅ **verified 2026-08-18** — a precisely-countable 27K-word prompt through the real proxy returned real, mutually-consistent `input_tokens` (30013/30019/30014) across both Gemma variants + Kimi, not a placeholder |
| Tool calls                              | ✅ native                                                    | ✅ implied by 6+3-task pilot correctness (not itemized as its own tool-call-specific check) | — not yet smoke-tested                             | ✅ **explicitly smoke-tested 2026-08-18** — tool_use/tool_result round-trip verified by ID-correlation, not just name-matching | ❌ **FAILS** — tool_use/tool_result translation confirmed still a structural text-placeholder stub, not a real translation (re-confirmed 2026-08-16) | — not yet smoke-tested                                    |
| Chained bash commands                   | ✅ native (implied by ordinary fleet operation)              | — not explicitly itemized; pilots imply general task-following but no bash-chain-specific check found | — not yet smoke-tested                             | — not yet smoke-tested                                     | ❌ blocked transitively by the tool_use stub above           | — not yet smoke-tested                                    |
| Reset-window semantics understood       | ✅ built — header-poll (`usage_poller.py`) + TUI-scrape fallback for the rich payload; new-account inheritance gotcha documented 2026-08-18 (see `claude_anthropic_flat_rate_billing_calibration_2026_08_12.md`) | ✅ 30-min balance poller (current-balance gauge, not a %-of-plan concept — DeepSeek is metered, not subscription) | ❌ "reuse Claude's `five_hour_pct`/`weekly_pct` fields" todo still open/unbuilt | ⚠️ built DIFFERENTLY — RPM/TPM/RPD event-counting against a static ceiling, not a periodic vendor poll; genuinely minute-scale as the operator flagged | ❌ "reuse Claude's `five_hour_pct`/`weekly_pct` fields" todo still open/unbuilt | ⚠️ **built, corrected 2026-08-18** — `nvidia_headroom.py` (shared per-KEY RPM gauge, not per-account like Gemini) + `GET /api/accounts/nvidia/capacity` + `NvidiaCapacityPanel.tsx`, 8 backend tests; ceiling is community-reported (~40 RPM), not vendor-published, and load-tested to a proven-safe floor of 8 concurrent with zero failures — a real dispatch gate exists, it's just calibrated against an unofficial number |
| "Max tier" behavior                     | N/A (not a GLM/Codex-style named tier)                       | N/A                                                        | — GLM Lite→Max upgrade explicitly gated on Lite-tier pipeline validation first (open `[OPERATOR] P3`); behavioral difference itself unverified | N/A (free-tier + one paid project; no "max" concept)         | — ChatGPT Plus→Pro upgrade gated on bridge validation, which is itself blocked by the tool_use stub | N/A                                                          |
| Vendor plan/limit directly readable?    | ⚠️ partial — header %-util readable via poller; rich payload (`extra_usage`, per-model submeters) needs the slow TUI path, not the fast poller | ✅ dollar balance directly queryable (metered API, no plan-% concept) | ❌ not built                                        | ❌ no live vendor quota poll; statically configured ceiling only, self-tracked request counts | ❌ not built                                                | ❌ not credit-based per NVIDIA's own description; no official vendor-side readable ceiling found (community-reported only) |
| **Overall Gate-1 verdict**              | **PASS** (one genuine N/A, rest ✅/⚠️-explained)              | **near-PASS** — 2 dimensions never explicitly itemized (chained-bash, standalone cache-vs-tool-call split) | **NOT STARTED** — 0 of 8 dimensions smoke-tested yet | **PARTIAL** — tool calls is the strongest-evidenced dimension of any new provider; cache/reasoning/chained-bash untested | **FAILS — blocked** — tool_use stub is a hard blocker for 3 of 8 dimensions; do not attempt Gate 2 until fixed | **PARTIAL, corrected 2026-08-18 — more mature than first assessed.** Token-count accuracy ✅ and a real capacity-gate ⚠️ both exist; cache/reasoning/tool-calls/chained-bash still untested. **Separately, already has Gate-2-ADJACENT evidence this registry doesn't track**: a full real `/pre-compact`→`/compact` live-harness cycle succeeded 2026-08-18 (real ~40K-token context built, skill genuinely executed, context measurably dropped 38.7k→4.8k tokens on the actual Claude Code harness) — not a Gate-1 dimension, but the strongest Gate-2-shaped evidence of any new provider, including Gemini. Source: `kimi_gemma_provider_onboarding_2026_08_16.md`. |

**Kimi (Moonshot)**: excluded from this registry's active tracking per the operator's standing scope ruling (waitlisted,
weeks-out ETA, not currently in the 6-provider fleet list) — see the scope banner in the published dashboard artifact.
It shares `kimi_gemma_provider_onboarding_2026_08_16.md` with Gemma at structurally identical maturity, so if the
operator later brings it back into scope, this table gains a 7th column by copying Gemma's row as the starting point,
not by re-deriving from scratch.

## Todo

- [ ] [REVIEW] P1. **Run the 5 missing GLM smoke-test dimensions** (cache, reasoning, token-count, tool calls, chained
      bash) and record evidence here + in `deepseek_claude_blended_provider_routing_2026_07_28.md` (GLM's home plan,
      Phase 3). **Done when**: every GLM cell above is ✅/⚠️/❌ with a cited evidence line, not "—".
- [ ] [REVIEW] P1. **Fill Gemini's 3 remaining untested dimensions** (cache, reasoning, chained bash) — tool calls and
      the RPM/TPM/RPD reset mechanism are already evidenced; this is the closest provider to a full Gate-1 pass besides
      DeepSeek/Claude. **Done when**: every Gemini cell above is ✅/⚠️/❌ with a cited evidence line. Source:
      `grok_gemini_translation_proxy_2026_08_14.md`.
- [ ] [BACKEND] P0. **Unblock Codex/Luna's Gate-1 failure at the root**: fix the tool_use/tool_result translation stub
      (`codex_luna_flex_bridge_2026_08_14.md`'s own `[REVIEW] P0`, "the single biggest remaining gap"). This single fix
      clears 3 of Codex's 8 blocked dimensions at once (tool calls, chained bash, and unblocks token-count accuracy
      once real usage data is confirmed reachable from the SDK's turn result). **Done when**: Codex's row above updates
      from FAILS to at least PARTIAL, with the 3 dimensions' cells changed from ❌ to ✅/⚠️ with cited evidence.
- [ ] [REVIEW] P1. **Run Gemma's 5 remaining untested dimensions** (cache, reasoning, tool calls, chained bash, "max
      tier" N/A-confirmation) — corrected 2026-08-18: token-count accuracy and a real capacity-gate are already done
      (see table), and a full `/pre-compact`→`/compact` live-harness cycle already succeeded, so this is a narrower
      remaining gap than first assessed, not a from-scratch smoke test. **Done when**: every remaining Gemma cell
      above is ✅/⚠️/❌/N/A with a cited evidence line. Source: `kimi_gemma_provider_onboarding_2026_08_16.md`.
- [ ] [REVIEW] P2. **Itemize DeepSeek's 2 never-explicitly-tested dimensions** (chained bash, a standalone tool-call
      check independent of overall pilot-task correctness) — DeepSeek is the fleet's most mature non-Claude provider,
      worth closing out to a clean PASS as the reference case for what "done" looks like for the rest. **Done when**:
      both cells update from "— not explicitly itemized" to ✅/⚠️ with cited evidence. Source:
      `deepseek_claude_blended_provider_routing_2026_07_28.md`.
- [ ] [DOC] P2. **Re-derive this table from the HTML dashboard artifact regeneration** once Gates 2-8 land real
      checkbox state (per the operator's own request that the published artifact persist across account resets/
      rotations) — this doc is the source of truth the artifact should read from, not the other way around.

## Progress Log

- **2026-08-18 (interactive session)**: registry created, initial fill derived from cross-referencing the 5 provider
  onboarding plans' own Progress Logs (via a dedicated deep-read research pass, not a fresh verification run) — see
  the summary caveat above. This is Gate 1 of the operator's 8-gate provider-readiness framework; Gates 2-8 are being
  threaded into the existing provider plans in the same session.

## Gate 4 — credit-exhaustion-aware dispatch (added 2026-08-18)

Homed here rather than in `deepseek_claude_blended_provider_routing_2026_07_28.md` (which owns the actual
`select_account_for_spawn()`/stratified-rotation mechanism these todos integrate with) because that plan was already
at 995 of its 1000-line hard cap. A cross-provider audit (2026-08-18) confirmed none of the 4 items below exist for
ANY provider today, including Claude, despite Claude having the richest usage-history data of the six.

- [ ] [DATA] P1. **Per-account "tasks-remaining" estimate.** From current headroom (Claude's `weekly_pct`/
      `five_hour_pct`, DeepSeek/Kimi's $ balance, Gemini/NVIDIA's remaining RPM/RPD capacity) plus a rolling
      tokens-or-turns-per-task average (`TaskUsageRow` already carries both, per task, per provider), estimate how
      many more tasks an account can serve before hitting its limit — not just a binary healthy/exhausted flag.
      **Done when**: a real estimate is computed for at least one account per provider family (%-based, $-based,
      RPM/RPD-based) and correlates with real remaining capacity within a stated tolerance.
- [ ] [INFRA] P1. **Poll cadence vs. reset-window granularity, audited per provider.** Claude's ~30-min poll is
      fine-grained against a 5h/weekly window; Gemini/Gemma's RPM ceilings are minute-scale and may need much faster
      refresh. **Done when**: every provider's cadence is stated relative to its own window, and any mismatch is
      fixed, not just flagged.
- [ ] [BACKEND] P1. **Prove exhaustion-recovery state survives a process restart.** Concrete failure this must not
      repeat: `plans/active/issues/ao_review_slot_hard_rule_and_diagnostics_2026_08_17.md` — a review slot sat dead
      23+ hours with a silent, unlogged failure to find any account, during a fleet-wide outage (all 7 Claude
      accounts exhausted simultaneously). **Done when**: a real restart (or an equivalent test) preserves/re-derives
      correct exhausted-vs-recovered state without a fresh multi-hour rebuild, generalized past the one Claude-specific
      fix already patched in that issue doc.
- [ ] [REVIEW] P2. **Reconcile against the stratified-rotation dispatch call-site coverage before assuming this is
      separate scope.** Per `deepseek_claude_blended_provider_routing_2026_07_28.md`'s own 2026-08-18 Progress Log,
      only `autospawn_refill` was wired as of that entry — `escalation.py`/`main_agent_keeper.py`/`plan_health.py`/
      `server.py`/`worker_liveness_watchdog.py`/`ensure_review_agents`/the resume pass still passed `task=None`.
      Check that plan's current Progress Log tail first (concurrent sessions are actively landing work on it).
      **Done when**: either every call site is confirmed wired, or the remaining gap is stated with a citation to the
      current state.

      **Re-confirmed 2026-08-19 (interactive session, prompted by an operator ask that planning AND escalation
      dispatch both get the same difficulty/duration-stratified treatment).** Read `deepseek_claude_blended_provider_
      routing_2026_07_28.md` end to end (through its full 1000-line hard cap, latest entry 2026-08-19) and
      `agent-orchestrator/server/autospawn.py::select_account_for_spawn()` directly — the gap is still open, byte-for-
      byte the same list as 2026-08-18: `escalation.py`/`main_agent_keeper.py`/`plan_health.py`/`server.py`/
      `worker_liveness_watchdog.py`/`ensure_review_agents`/the resume pass all still default `task=None`, so none of
      them get difficulty/duration-band rotation — only `autospawn_refill` does. Separately, escalation workers
      register with a flat `role="custom"` (`escalation.py:992-999`, deliberate — keeps promote/chat lanes clean,
      `agent_kind` carries real identity) rather than a `role_registry`-resolved RoleSpec; this does NOT block
      analytics attribution (`task_role_group()`/`_ESCALATION_ROLES` in `server/state_store/slots.py` already
      classify escalation-origin spend into `cicd`/`conflict_resolver`/`data_pipeline_failure`/
      `quality_gate_resolution` independent of the registration-time role label — confirmed via
      `deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md`), so it's a narrower, lower-
      priority gap than the stratification one. **Not implemented in this session** — the operator's own instruction
      for this exact scope was "update the todos in the existing plans," not "implement now," and this is live
      production dispatch-routing code the owning plan has repeatedly treated with operator-ship-review caution
      (e.g. its own Phase 4 `[INFRA]` todo shipped code+tests but left checkboxes unflipped "pending QG + operator
      ship review"). Leaving this todo OPEN rather than flipping it — the wiring itself is still real, undone work.
