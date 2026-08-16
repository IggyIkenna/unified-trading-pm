---
doc_type: plan
title: Multi-provider context accuracy + unified billing reconciliation
summary:
  Two linked problems surfaced testing the 4 new providers (Grok/Gemini/GLM/Codex) live — (1) context_used_pct, the
  number driving AO's 60% pre-compact trigger — is fed by per-turn token counts that are REAL for some providers and a
  known-fake char/4 estimate for Codex specifically, so the same uniform compact mechanism behaves accurately for some
  backends and not others; (2) there is no unified way to reconcile per-task billing to a fleet total, or to compare
  "what we spend / what we get" across metered-$, first-party-token, subscription-flat-rate, and rate-limited-free-tier
  providers on one normalized (input/output/cache-read/cache-write) basis. Human-driven — investigation, live testing,
  and design calls throughout, not bounded background-worker todos.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    context-window,
    tokenizer,
    pre-compact,
    billing,
    reconciliation,
    multi-provider,
    grok,
    gemini,
    glm,
    codex,
  ]
related:
  [
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/grok_gemini_translation_proxy_2026_08_14.md,
    /plans/active/codex_luna_flex_bridge_2026_08_14.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/issues/claude_anthropic_flat_rate_billing_calibration_2026_08_12.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-08-16
last_updated: 2026-08-16
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 6
assigned_role: infra
effort: max
drift_direction: advance-code
depends_on: [deepseek_claude_blended_provider_routing, grok_gemini_translation_proxy, codex_luna_flex_bridge]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
context_scope:
  [
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/codex_bridge_server.py,
    agent-orchestrator/scripts/orchestrator/calibrate_account_value.py,
    agent-orchestrator/server/model_pricing.py,
    agent-orchestrator/server/orm.py,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
  ]
---

# Multi-provider context accuracy + unified billing reconciliation

## Why

Testing the 4 new providers live (2026-08-16) surfaced two related gaps that predate this session but only became
visible once real traffic flowed through real proxies:

**1. Context-window/tokenizer accuracy is NOT uniform across providers, but the mechanism that depends on it IS.**
`context_lifecycle.py`'s 60% pre-compact trigger reads `context_used_pct` by scraping Claude Code's own self-reported
"N% context used" pane text — a number Claude Code computes from the `usage.input_tokens`/`output_tokens` fields in
each turn's response. For Grok/Gemini/GLM those fields are REAL (LiteLLM/GLM's native endpoint pass through the
vendor's own usage accounting). For **Codex/Luna they are a placeholder**:
`server/codex_bridge_server.py::_estimate_tokens` is `len(text) // 4` — a crude heuristic, explicitly marked
"never to be trusted for billing" in its own docstring. This session independently demonstrated exactly how
unreliable a naive text-length-based token estimate can be: a word-count heuristic on a real Grok 4.6 context-limit
test undercounted the real (xAI-tokenizer-measured) count by 1.6x. If Codex's fake estimate has a similar or worse
skew, `context_used_pct` for a Codex-backed session is silently wrong, and the SAME 60%-trigger mechanics that work
correctly for Grok/Gemini/GLM will misfire for Codex specifically — either compacting too early (wasted turns) or,
worse, letting a session run past its real context ceiling undetected (an uncontrolled 400 mid-session, a materially
worse failure than the "recover with a fresh session" path this codebase already has for a *known*-saturated session).

The context-window claims themselves (from vendor docs/research, not yet all live-verified) also need direct testing
rather than trusted at face value — this session tested exactly one (Grok 4.6's 500K ceiling, confirmed real and
hard-enforced, no silent server-side truncation) and found nothing wrong, but that's 1 of 9 registered models. The
same test also settled a separate, real question: **none of the raw provider APIs self-compact** — Grok 4.6 rejected
an over-limit request with a clean `400`, not a truncated/summarized response. Context self-compaction only exists as
a **Claude Code harness feature** (`/compact`), never as vendor-API server-side behavior — worth stating plainly since
it was live-tested, not assumed.

**Separately (operator correction, 2026-08-16): the self-compaction question needs re-testing through the REAL path.**
The 500K-limit test above was a raw HTTP probe directly against the proxy, bypassing Claude Code entirely — it proves
the *backend* doesn't self-compact, but says nothing about whether Claude Code's own `/pre-compact` → `/compact`
mechanism, and the skills/hooks wrapped around it, actually work correctly when the backend is Grok/Gemini/GLM/Codex
specifically. DeepSeek already proved this end-to-end (`deepseek_claude_blended_provider_routing_2026_07_28` Progress
Log, 2026-07-29: "CLAUDE.md/agents/\*.md need no DeepSeek special-casing — both load identically regardless of which
backend ANTHROPIC_BASE_URL points at"), but that result does not automatically transfer to the 4 new providers and
needs its own live verification, the same way DeepSeek's was actually proven rather than assumed.

**Historical incident check**: one real, already-fixed compact-related bug was located
(`agent-orchestrator@c00dc13f9d`, 2026-08-04 — a pre-Skills CLI binary silently swallowed `/pre-compact` with no
error signal). That fix is generic (pane-text detection of "Unknown command"), not provider-specific, and does not
need re-verification per new provider. **A second, different incident the operator specifically recalled — "compact
runs, but the next turn still resends the full pre-compact history as if it hadn't shrunk" — was NOT located** in
this session's search. Either it exists in a doc/conversation not yet surfaced by grep, or it's being conflated with
something else. Flagged as an open question rather than guessed at (see todo below).

**2. There is no unified, model-agnostic per-task billing reconciliation.** Two distinct goals, stated by the
operator 2026-08-16, not yet designed:

- **Reconciliation**: the sum of every task's attributed billing should equal the fleet's real total spend. Today
  this exists cleanly for DeepSeek (`task_usage` table, real per-token cost) **and, corrected 2026-08-16, for
  Anthropic too** — `claude_anthropic_flat_rate_billing_calibration_2026_08_12.md` shipped a real, live
  `boost_multiplier` system (`compute_claude_wallet_reconciliation()`, `ClaudeWalletPanel.tsx`,
  `agent-orchestrator@616450ffac`) with real per-account numbers already pulled (Max20 accounts cluster 14x-32x; a
  genuine Pro-tier ~1047x outlier is still under investigation there, not a data bug — see that doc's own open
  todos). This plan's original framing wrongly described the Claude subscription-value question as unsolved; it
  isn't — it's the reusable PRECEDENT this plan should generalize, not a gap to fill from scratch. The 4 newer
  providers (Grok/Gemini/GLM/Codex) still have no per-task cost attribution built at all.
- **Normalized bang-for-buck**: everything should reduce to input/output/cache-read/cache-write token counts so
  providers are comparable regardless of billing shape — metered-$ (Grok), first-party token counts we trust
  (Anthropic, Gemini), subscription-flat-rate where the real value per dollar is now KNOWN for Claude (see above) but
  still genuinely UNKNOWN for GLM's Coding Plan (the one remaining real "Sonnet multiplier"-shaped gap — no
  equivalent calibration has been built for GLM's flat-rate subscription), and rate-limited-free-tier where "spend"
  doesn't exist but capacity does (Gemini's free tier — remaining-RPD-as-a-proxy needs a tested methodology, not an
  assumption). **Every number that lands in this system should be the provider's PUBLISHED rate** (not a computed
  effective rate) — that published number times real token counts is what answers "how much bang for the buck are we
  actually getting" against what we pay.

Real turn-shaped variance matters here too, not just $/token: "some models are cheap per turn but need many turns;
some are cheap per token but burn a lot of them" (operator, 2026-08-16) — a single-prompt test (what this session ran)
is a proxy, not a real workflow, and the eventual dashboard needs to show real per-task turn counts alongside token
counts once this reconciliation layer exists, so that distinction is visible on real work, not just a synthetic probe.

**Backfill is explicitly required, not optional** (operator ruling, 2026-08-16): whatever reset-aware reconciliation
mechanism gets built must be run back across ALL existing `account_usage_history`, not just applied going forward —
the existing ledger's reset-crossing windows should be reconciled, not left as dropped/unknown data.

## Non-goals

- Not rebuilding `calibrate_account_value.py`'s conservative single-clean-window design — that script answers a
  narrower, different question ($-per-percent-multiplier for ONE quota window) and merging across a reset there would
  genuinely corrupt that specific calculation (two different weekly-budget dollar values, ambiguous transcript
  attribution). The new reset-aware primitive is additive, not a replacement for that script.
- Not attempting to make Gemini's free tier report a dollar cost — it's genuinely $0. The goal there is a tested
  capacity-consumption proxy, not inventing a price that doesn't exist.
- Not building this as an AO-dispatched background-worker plan — see the operator's explicit "human plan" instruction,
  2026-08-16. The design calls and live-testing judgment here don't fit the AO-eligible bar (deterministic,
  worker-executable outcome).

## Todos

- [ ] [OPERATOR] P2. Point at the actual incident doc/conversation for "compact runs but the next turn resends the
      full pre-compact history as if it hadn't shrunk" — this session's grep found the 2026-08-04 unsupported-binary
      incident (a different failure mode, already fixed, generic) but not this one. Done when: either the real
      incident is located and its fix's generality (provider-specific vs. generic) is confirmed, or the operator
      confirms it should be independently re-tested rather than assumed to be the same class of bug.
- [ ] [INFRA] P0. Fix Codex/Luna's fake token-count estimate (`_estimate_tokens = len(text)//4`,
      `codex_bridge_server.py`) — confirmed unreliable via this session's own 1.6x-off word-count test on a real
      tokenizer comparison. Investigate first whether the `openai-codex` SDK's own thread/turn result carries real
      usage data not currently being read (an easy fix if so); if genuinely unavailable, a real tokenizer
      (tiktoken-compatible for the GPT-5.6 family) is the fallback, not a better heuristic guess. Done when: a real
      sample of Codex-backed turns' captured token counts are cross-checked against the actual ChatGPT/Codex usage
      dashboard and found to agree within a stated tolerance — same standard already required by
      `codex_luna_flex_bridge_2026_08_14.md`'s existing accurate-usage-capture todo, which this directly unblocks.
- [ ] [REVIEW] P1. Verify Claude Code's own end-to-end `context_used_pct` display is accurate for Grok/Gemini/GLM —
      the individual API responses carry real vendor-reported usage (confirmed this session), but the CUMULATIVE
      session-level percentage Claude Code itself computes and displays has not been independently checked end-to-end.
      Done when: a real multi-turn session against each of the 3 providers shows a `context_used_pct` reading that
      tracks real cumulative token consumption within a stated tolerance.
- [ ] [REVIEW] P0. Live-test `/pre-compact` and `/compact` through the REAL harness (not a raw HTTP probe) for each of
      Grok, Gemini, GLM, and Codex — spawn real `claude` CLI sessions against each new account, run long enough to
      approach or force the 60% threshold, and confirm: (a) the skill/command actually executes (not silently
      swallowed), (b) `context_used_pct` genuinely drops afterward — proving compaction reduces what gets resent, not
      just that the command ran, (c) CLAUDE.md/skills/hooks behave identically to the already-proven DeepSeek case.
      Done when: a dated Progress Log entry records this for all 4 providers, each independently verified, not
      assumed to transfer from DeepSeek's or each other's result.
- [ ] [REVIEW] P2. Live-test the remaining context-window claims from this session's research table (Grok 4.3's 1M,
      GLM's 1M/131K, Gemini's 1,048,576/65,536 — already confirmed live for Gemini, DeepSeek's 1,048,576/384,000,
      GPT-5.6's 1.05M/128K) the same way Grok 4.6's 500K was — a real oversized request, built on-host to avoid
      transport payload limits, confirming the vendor enforces its documented ceiling and does not silently truncate.
      Done when: each is either confirmed live or explicitly flagged as still resting on published docs only.
- [ ] [INFRA] P1. Design + build the reset-aware rolling-window cumulative-consumption primitive: given a wall-clock
      period that may cross one or more quota resets, compute TRUE total consumption as
      `(100 - pct_at_period_start) + pct_at_first_reset_boundary + ... + pct_at_period_end`, chained across every
      reset the period spans, using the existing `*_window_start`/`*_resets_at` fields `account_usage_history`
      already carries. Additive to, not a replacement for, `calibrate_account_value.py`'s existing conservative
      single-window design. Done when: a real historical window that crosses at least one confirmed reset produces a
      correct, testable total (verified against real 5h/weekly reset timestamps in the live data, not synthetic).
- [ ] [INFRA] P1. Backfill the reset-aware primitive across the FULL existing `account_usage_history` table —
      explicit operator requirement (2026-08-16): this is not going-forward-only. Done when: every historical
      reset-crossing window in the live table has a computed, correct cumulative-consumption value, not left as
      dropped/unknown.
- [ ] [DATA] P1. Design the unified per-task billing schema — normalized input/output/cache-read/cache-write token
      counts as the common denominator across every provider's billing shape (metered-$, first-party-token,
      subscription-flat-rate, rate-limited-free-tier), each priced at the provider's PUBLISHED rate (not a computed
      effective rate) for the "bang for the buck" comparison. Must generalize DeepSeek's existing `task_usage` table
      rather than create a second, parallel per-task ledger. Done when: a design doc or schema proposal covers all 7
      currently-registered providers (Anthropic, DeepSeek, Grok, Gemini, GLM, Codex) with a concrete field mapping
      for each.
- [ ] [DATA] P1. Reconciliation proof: sum of every task's attributed billing (once the schema above is populated for
      a real window) must equal the fleet's real total spend for that window, per provider. Done when: a dated
      Progress Log entry shows this reconciling within a stated tolerance for at least DeepSeek + one new provider.
- [ ] [REVIEW] P2. Gemini free-tier capacity-as-proxy methodology: design and run a real test that translates
      "remaining RPD/RPM capacity in a given window" into a spend-equivalent comparison figure, the way
      `gemini_headroom.py`'s ceilings are already tracked for dispatch-gating — this is the same underlying data,
      repurposed for the reconciliation/comparison goal rather than just the dispatch gate. Done when: a documented,
      tested methodology exists, not just the raw ceiling numbers already recorded.
- [ ] [REVIEW] P2. Verify the "manual/interactive Claude usage sits on separate accounts from AO dispatch" assumption
      is actually true today, not just believed — this is the stated precondition for treating AO's own usage
      tracking as clean/isolated from personal usage. Done when: the account roster is checked against what AO
      actually dispatches to vs. what's used interactively, and any overlap is flagged.
- [ ] [UI] P3. Once the reconciliation layer exists, surface real per-task turn counts alongside token counts on the
      dashboard — the stated reason for building this at all: "some models are cheap per turn but need many turns;
      some are cheap per token but use lots of tokens" is only visible on real task data, not a synthetic single-prompt
      probe. Done when: a real dispatched task's turn count and token count are both visible in one place.

## Progress Log

- **2026-08-16 (created)**: Plan authored from a same-session investigation following the live 9-model billing/context
  test battery (see the sibling provider plans' 2026-08-16 Progress Log entries for that raw data). Real findings this
  session, cited above: Codex's fake `len(text)//4` token estimate (confirmed via direct code read), the
  provider-agnostic-mechanism-vs-provider-specific-data-accuracy gap in `context_lifecycle.py`, Grok 4.6's 500K
  context ceiling confirmed live (hard-enforced, no self-compaction), and `calibrate_account_value.py`'s deliberate
  (not buggy) reset-window-dropping design. No code written yet — investigation + plan authoring only.
