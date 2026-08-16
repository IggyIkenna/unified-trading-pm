---
doc_type: plan
title: Kimi (Moonshot) + Gemma (NVIDIA NIM) provider onboarding
summary:
  Onboard two more sonnet-tier fallback providers into the AO fleet, same pattern as the GLM/Grok/Gemini/Codex work
  (live model checks against real APIs, not vendor docs; cheapest-tier-first; real accounts registered but PAUSED
  until task-routing logic exists). Kimi (Moonshot AI — k2.5/k2.6/k3) and Gemma (via NVIDIA's free hosted NIM
  OpenAI-compatible endpoint, not self-hosted Ollama) are explicitly a hedge against a DeepSeek price rise, not an
  immediate dispatch target — task routing (which model for which job) is deliberately out of scope here.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, kimi, moonshot, gemma, nvidia, nim, model-routing, multi-provider, free-tier]
related:
  [
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/grok_gemini_translation_proxy_2026_08_14.md,
    /plans/active/codex_luna_flex_bridge_2026_08_14.md,
    /plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/archive/2026_08/omniroute_multi_provider_routing_evaluation_2026_08_03.md,
    /codex/06-coding-standards/model-tier-selection.md,
  ]
created: 2026-08-16
last_updated: 2026-08-16
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
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
    agent-orchestrator/server/accounts.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/model_pricing.py,
    agent-orchestrator/server/gemini_headroom.py,
    /plans/active/grok_gemini_translation_proxy_2026_08_14.md,
    /plans/archive/2026_08/omniroute_multi_provider_routing_evaluation_2026_08_03.md,
  ]
---

# Kimi (Moonshot) + Gemma (NVIDIA NIM) provider onboarding

## Why

Operator decision (interactive session, 2026-08-16): add two more standby providers beyond the four already
onboarded (GLM, Grok, Gemini, Codex/Luna) — explicitly framed as a hedge, in the operator's own words: **"Other
models are implemented to guard against deepseek price rise."** Same discipline as the prior four: verify real
model names/tiers/limits against live APIs (not trusted vendor docs — this session's GLM/Grok work already caught
two dead model names this way), start at the cheapest viable tier, register real production-ready accounts
(billing/wallet reconciliation working), but leave every new account **paused** (`account_status: disabled`) until
task-routing logic exists to decide which job goes where. Per the operator: **"The future work will be about task
routing (does it do the job) once we fully understand the costs differences"** — that routing question is explicitly
OUT OF SCOPE for this plan; this plan only gets each provider to the same paused-but-production-ready state the
other four already reached.

**Reconciliation flag, not yet resolved — read before doing any Kimi work**: this repo already carries an explicit
prior ruling AGAINST Kimi. `/plans/archive/2026_08/omniroute_multi_provider_routing_evaluation_2026_08_03.md` §
"Phase 3 — decision" recorded the operator's own 2026-08-06 ruling — "all these models were evaluated briefly on a
few tasks... Outcome: Claude + DeepSeek only for now" — with Kimi named specifically as evaluated and rejected
("pricier than DeepSeek, no edge" on K2.6/K3 pricing at that time). That ruling also said re-adding a provider later
is "not going to be hard, maybe a few hours of work only" and should be re-opened "only when there is an actual
decision to add a provider" — today's operator message is that reopening. But the rejection's PRICING BASIS needs
re-checked before treating this as settled: Moonshot's published rates may have changed since 2026-08-06, or the
operator may simply be optimizing for a different goal now (DeepSeek-price-rise insurance, not raw $/task). Todo 1
below exists to make that reconciliation explicit rather than silently re-litigating a decision that was made for a
stated reason.

**Reconciliation answer, given directly by the operator (2026-08-16): "kimi pricier than deepseek BUT has a huge
max plan deepseek doesn't."** This is option (b) from Todo 1's framing below, not (a) — the 2026-08-06 rejection's
per-token pricing conclusion likely still holds (re-verify anyway, since a "still true" claim still needs a live
number), but it doesn't settle the question anymore, because the operator's goal this time isn't $/task parity.
Moonshot offers a large flat-rate/subscription capacity tier ("max plan") with no DeepSeek equivalent at any price —
that's real standby headroom during a DeepSeek price spike or rate-limit crunch that raw per-token comparison can't
capture. Todo 1 narrows accordingly: confirm the real per-token numbers for completeness, but the actual decision
basis is the max-plan's real terms (price, capacity ceiling, whether it's metered-$-convertible or a hard quota) —
get those, not just the per-token table.

**Gemma is NOT self-hosted.** The original framing ("gemma will need more ram... temporarily") assumed a local
Ollama server; the operator's follow-up (relaying a colleague's note, 2026-08-16) redirected this to **NVIDIA's free
hosted NIM endpoint** — `https://integrate.api.nvidia.com/v1`, OpenAI-compatible, GPU supplied by NVIDIA/DGX Cloud,
free for prototyping/development (explicitly NOT a production SLA per NVIDIA's own terms). This removes the VM/RAM
question entirely — no planning-VM resize needed — but introduces a different real question: whether NVIDIA's
"unlimited prototyping" framing survives contact with AO's actual fleet request volume (the same skepticism this
session already applied to Gemini's free-tier ceilings, which turned out much thinner than first assumed).

Confirmed clean slate (2026-08-16 investigation, both local checkout and `origin/live-defi-rollout` — 0 ahead/behind,
plus a live read of the deployed VM's `/api/accounts`): no kimi/moonshot/gemma/nvidia code, GSM secret, or
registered account exists anywhere in the fleet today, despite an earlier operator remark suggesting some of this
had already run. Treat every todo below as net-new work, not a resume.

## Todos

- [ ] [OPERATOR] P0. Reconcile the Kimi re-add against the 2026-08-03/08-06 rejection ruling above — narrowed by the
      operator's direct answer (2026-08-16, see Why): the basis is Moonshot's flat-rate "max plan" capacity, not
      per-token price parity. Pull (1) real current per-token $/1M input/output/cache rates for k2.5/k2.6/k3 for
      completeness, and (2) the max plan's real terms — price, capacity ceiling (requests/tokens per period), and
      whether it's a hard quota or metered-$-convertible. Confirm no DeepSeek equivalent actually exists (don't
      assume — check DeepSeek's current plan page too). Done when: this plan's Progress Log records the max plan's
      real terms plus the per-token table, both cited to a live source, before any account is registered.
- [ ] [OPERATOR] P0. Get Moonshot (Kimi) API credentials from the operator — start on Moonshot's cheapest/basic plan
      tier (mirrors the GLM-Lite / ChatGPT-Plus / Gemini-free staging pattern from the prior four providers). Store
      in GSM as `moonshot-api-key` (+ `moonshot-management-key` if a separate balance/usage-read scope exists, per
      the Grok precedent where the inference key and the balance-read key were confirmed to be genuinely different
      credentials). Done when: the key resolves via GSM and a real authenticated `/v1/models`-equivalent call
      succeeds.
- [ ] [OPERATOR] P0. Get an NVIDIA Developer Program account + API key for the NIM free-hosted endpoint (operator
      must create the NVIDIA account — this is not something that can be done from a service credential). Store in
      GSM as `nvidia-api-key`. Done when: the key resolves via GSM and a real authenticated call against
      `https://integrate.api.nvidia.com/v1` succeeds.
- [ ] [INFRA] P1. Live-verify real Kimi model names/specs via Moonshot's API (never trust the "k2.5/k2.6/k3" naming
      from memory alone — this session already found two dead model names, `grok-4.1-fast` and `glm-4.7-flashx`,
      by skipping this exact check). For each of k2.5/k2.6/k3: confirm it exists via a live `/v1/models`-equivalent
      call, record real context-window size, and real published $/1M input/output/cache-read/cache-write rates.
      Done when: a real API response backs every model's context-window and pricing claim recorded in
      `model_pricing.py`, cited by response, not by docs page.
- [ ] [INFRA] P1. Live-verify Gemma's real available NIM models — the operator's relayed note names two candidates
      (`google/diffusiongemma-26b-a4b-it` and a `google/gemma-4-31b`-shaped ID) with a stated tradeoff
      (DiffusionGemma faster but weaker at reasoning/coding per NVIDIA's own benchmark table). Confirm both exist via
      a real authenticated call, record real context-window size and rate-limit numbers (NVIDIA's own docs claim
      "unlimited prototyping" — get the REAL enforced per-minute/per-day ceiling by testing against it, the same way
      Grok 4.6's 500K context ceiling was proven hard-enforced rather than trusted from docs). Done when: both models
      are confirmed live, and at least one real rate-limit ceiling is measured, not assumed from NVIDIA's marketing
      language.
- [ ] [INFRA] P1. Determine both vendors' native API shape and pick the integration pattern: Moonshot's API is
      OpenAI-chat-completions-shaped (needs the same LiteLLM Anthropic-passthrough proxy pattern as Grok/Gemini,
      `grok_gemini_translation_proxy_2026_08_14.md`) unless live testing finds otherwise; NVIDIA NIM's endpoint is
      explicitly OpenAI-compatible per the operator's relayed note, same expected pattern. Confirm whether the
      EXISTING LiteLLM proxy instance (isolated venv, already running for Grok/Gemini) can just take two more model
      entries, or whether a second instance is needed for isolation/blast-radius reasons. Done when: both providers
      are reachable through a proxy and a real end-to-end smoke test (a `claude` subprocess pointed at the proxy)
      returns a real completion.
- [ ] [SCRIPT] P1. Register `kimi` and `nvidia` in `AccountProvider` (`server/accounts.py`), add real `RateCard`
      entries in `model_pricing.py` using the numbers from the two live-verify todos above, and wire dispatch
      eligibility into `autospawn.py`/`select_account_for_spawn()` — reuse the Gemini per-project-headroom-gate
      pattern (`gemini_headroom.py`) if NVIDIA's rate ceiling turns out to be scoped similarly (per-key or
      per-project, not globally per-model); a flat metered-$ gate (DeepSeek/Grok-style) if not. Register every new
      account with `account_status: disabled` from creation — **paused, not dispatch-eligible**, per this plan's Why
      section. Done when: `load_accounts()` parses both new accounts without error and dispatch correctly skips them
      while paused (verified by a real spawn attempt that falls through to the next eligible provider).
- [ ] [REVIEW] P2. Wallet/balance reconciliation for both: Moonshot (metered $, confirm whether it exposes a
      balance/usage-read endpoint the way DeepSeek's `/user/balance` and Grok's `management-api.x.ai` do, or whether
      it needs the DeepSeek-style "available-balance-only" design already built) and NVIDIA NIM (free tier — likely
      no $ balance at all, so the meaningful reconciliation is against RATE-LIMIT capacity consumed, same shape as
      the Gemini free-tier todo already tracked in `multi_provider_context_billing_reconciliation_2026_08_16.md`).
      Done when: a real number (either $ balance or rate-limit-capacity-consumed) is confirmed readable and matches
      what the vendor's own dashboard/console shows, cross-checked live the way the DeepSeek $50 topup was verified
      this session.
- [ ] [REVIEW] P2. Context-window/tokenizer accuracy check for Kimi and Gemma-via-NVIDIA, following the same
      live-test discipline established in `multi_provider_context_billing_reconciliation_2026_08_16.md` (don't trust
      the char/4 or word-count heuristics — this session already proved a word-count estimate under-measured a real
      Grok context test by 1.6x). Done when: each model's real context ceiling is confirmed via a live probe, not
      copied from a docs page.
- [ ] [REVIEW] P2. Live-test `/pre-compact` → `/compact` through the REAL Claude Code harness (a spawned `claude`
      subprocess, not a raw HTTP probe) for both new providers, same requirement already tracked for GLM/Grok/Gemini/
      Codex in the sibling plan. Done when: a real compact cycle is observed working end-to-end for both.
- [ ] [DATA] P3. Once `multi_provider_context_billing_reconciliation_2026_08_16.md`'s unified per-task billing
      schema is designed, extend it to cover Kimi and NVIDIA/Gemma rather than building a second parallel schema —
      cross-link, don't duplicate. Done when: both providers have a concrete field mapping in that schema (tracked
      as this todo, not a new design doc).
- [ ] [REVIEW] P3. Document the DeepSeek-price-rise-insurance rationale concretely: at what real DeepSeek $/1M rate
      would each of Kimi/NVIDIA-Gemma actually become the cheaper choice, given the real published rates gathered
      above — a one-time comparison table, not a routing implementation (routing itself stays out of scope per this
      plan's Why section). Done when: a real breakeven table exists in the Progress Log, citing the rates gathered
      in the live-verify todos, not re-derived from memory.

## Progress Log
