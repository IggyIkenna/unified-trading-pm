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
  is Gate 1 of the 8-gate provider-readiness framework (Gates 2-4 live in each provider's own onboarding plan; Gates
  5-6 in deepseek_claude_blended_provider_routing Phase 4/5; Gates 7-8 in multi_provider_context_billing_reconciliation)
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
    /plans/active/kimi_gemma_provider_onboarding_2026_08_16.md,
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
| Token-count accuracy                    | ✅ native, no translation layer                             | ✅ verified post-proxy-fix (was lossy pre-fix, now closes the gap) | — not yet smoke-tested                             | ⚠️ request-count tracked (RPM/TPM/RPD gate); $/token accuracy not independently confirmed | ❌ **known bug** — "Codex's fake token estimate," open `[INFRA] P0` to fix | — not yet smoke-tested, only plain-text probes run       |
| Tool calls                              | ✅ native                                                    | ✅ implied by 6+3-task pilot correctness (not itemized as its own tool-call-specific check) | — not yet smoke-tested                             | ✅ **explicitly smoke-tested 2026-08-18** — tool_use/tool_result round-trip verified by ID-correlation, not just name-matching | ❌ **FAILS** — tool_use/tool_result translation confirmed still a structural text-placeholder stub, not a real translation (re-confirmed 2026-08-16) | — not yet smoke-tested                                    |
| Chained bash commands                   | ✅ native (implied by ordinary fleet operation)              | — not explicitly itemized; pilots imply general task-following but no bash-chain-specific check found | — not yet smoke-tested                             | — not yet smoke-tested                                     | ❌ blocked transitively by the tool_use stub above           | — not yet smoke-tested                                    |
| Reset-window semantics understood       | ✅ built — header-poll (`usage_poller.py`) + TUI-scrape fallback for the rich payload; new-account inheritance gotcha documented 2026-08-18 (see `claude_anthropic_flat_rate_billing_calibration_2026_08_12.md`) | ✅ 30-min balance poller (current-balance gauge, not a %-of-plan concept — DeepSeek is metered, not subscription) | ❌ "reuse Claude's `five_hour_pct`/`weekly_pct` fields" todo still open/unbuilt | ⚠️ built DIFFERENTLY — RPM/TPM/RPD event-counting against a static ceiling, not a periodic vendor poll; genuinely minute-scale as the operator flagged | ❌ "reuse Claude's `five_hour_pct`/`weekly_pct` fields" todo still open/unbuilt | ⚠️ **may not apply at all** — NVIDIA NIM's free tier is traffic-dependent rate limiting, not a resetting quota bucket, per NVIDIA forum staff (2026-08-18 research); needs confirming before treating this as a gap rather than a non-applicable dimension |
| "Max tier" behavior                     | N/A (not a GLM/Codex-style named tier)                       | N/A                                                        | — GLM Lite→Max upgrade explicitly gated on Lite-tier pipeline validation first (open `[OPERATOR] P3`); behavioral difference itself unverified | N/A (free-tier + one paid project; no "max" concept)         | — ChatGPT Plus→Pro upgrade gated on bridge validation, which is itself blocked by the tool_use stub | N/A                                                          |
| Vendor plan/limit directly readable?    | ⚠️ partial — header %-util readable via poller; rich payload (`extra_usage`, per-model submeters) needs the slow TUI path, not the fast poller | ✅ dollar balance directly queryable (metered API, no plan-% concept) | ❌ not built                                        | ❌ no live vendor quota poll; statically configured ceiling only, self-tracked request counts | ❌ not built                                                | ❌ not credit-based per NVIDIA's own description; no vendor-side readable ceiling found |
| **Overall Gate-1 verdict**              | **PASS** (one genuine N/A, rest ✅/⚠️-explained)              | **near-PASS** — 2 dimensions never explicitly itemized (chained-bash, standalone cache-vs-tool-call split) | **NOT STARTED** — 0 of 8 dimensions smoke-tested yet | **PARTIAL** — tool calls is the strongest-evidenced dimension of any new provider; cache/reasoning/chained-bash untested | **FAILS — blocked** — tool_use stub is a hard blocker for 3 of 8 dimensions; do not attempt Gate 2 until fixed | **NOT STARTED** — 0 of 8 dimensions smoke-tested beyond plain-text probes |

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
- [ ] [REVIEW] P1. **Run Gemma's 7 untested dimensions** beyond the plain-text probes already done, and separately
      confirm/refute whether "reset-window semantics" is a real dimension for NVIDIA NIM's free tier at all (per the
      2026-08-18 research finding that it's traffic-dependent rate limiting, not a quota bucket) — if confirmed
      non-applicable, change that cell to N/A with the citation rather than leaving it an open gap. **Done when**: every
      Gemma cell above is ✅/⚠️/❌/N/A with a cited evidence line. Source: `kimi_gemma_provider_onboarding_2026_08_16.md`.
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
