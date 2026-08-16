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
      per-token price parity. The archived doc's own per-token numbers (2026-08-06, cite before trusting stale):
      Kimi K3 $3/$15 per 1M in/out (dominated by Claude Sonnet 5's $2/$10 intro); Kimi K2.6 $0.95/$4.00 per 1M
      in/out, 80.2% SWE-bench, 262K context (above DeepSeek on price, below on benchmark+context); **K2.5 was never
      evaluated** — no prior number exists, get one fresh. **DeepSeek's "no flat-rate plan" side confirmed
      2026-08-16** (WebSearch, deepseek.ai/pricing): DeepSeek is pure pay-per-token, "no monthly subscriptions on
      the API," now moving to peak/off-peak billing as of today 16:00 UTC — no flat-rate/max-plan equivalent exists
      to compare against, so that half of the reconciliation is closed. Remaining: (1) re-verify K3/K2.6 rates
      haven't moved since 08-06 and get a real K2.5 number, (2) get Moonshot's max plan's real terms — price,
      capacity ceiling, hard-quota-vs-metered-convertible, and whether it's usable via API at all (not just their
      chat UI) — this last point is the load-bearing one for the whole reconciliation and must not be assumed.
      Done when: this plan's Progress Log records the max plan's real terms plus the refreshed per-token table,
      both cited to a live source, before any account is registered.

      **Research pass 2026-08-16 (background agent) — real numbers, plus a critical unconfirmed caveat**: real API
      model IDs confirmed via `platform.kimi.ai/docs/models`: `kimi-k3` (1M/1,048,576 ctx, $3/$15 per 1M in/out —
      matches the archived table, unchanged), `kimi-k2.6` (256K/262,144 ctx, ~$0.95/$4.00 — matches archived table),
      `kimi-k2.5` (256K ctx, ~$0.60/$3.00 — new, was never previously evaluated), plus `kimi-k2.7-code` and legacy
      `moonshot-v1-{8k,32k,128k}`. API confirmed OpenAI-chat-completions-shaped at `https://api.moonshot.ai/v1`.
      **The pricing conclusion is unchanged from 2026-08-06 — Kimi still loses to DeepSeek on raw $/token.**
      **Unconfirmed-but-load-bearing caveat**: multiple secondary sources (no primary Moonshot doc found) describe
      Kimi's subscription tiers (Adagio free → Vivace $199/mo) as a **CLI/chat-app product on SEPARATE billing from
      the metered developer API** — i.e. paying for a higher membership tier reportedly does NOT grant API token
      capacity, the same shape as Claude Max not covering Anthropic API usage. **If true, this undercuts the whole
      "huge max plan DeepSeek doesn't have" rationale**, since AO dispatch needs programmatic HTTP API access, not a
      CLI-rate-limited product. This must be confirmed directly with Moonshot (support/docs, not aggregator sites)
      before any paid membership tier is purchased on the strength of this plan's rationale — get a plain
      pay-as-you-go/metered API key with a small prepaid top-up for the live-check todos below regardless; that
      doesn't depend on the max-plan question being resolved either way.

      **Primary-source confirmation, 2026-08-16 (operator screenshot, `kimi.com/platform` Pricing page — upgrades
      the research pass above from secondary-sourced to primary-sourced)**: exactly three models currently listed —
      **K3**: $3.00 input / $15.00 output / $0.30 cache-hit per MTok, 1M-token context, "most capable flagship."
      **K2.7 Code**: $0.95 input / $4.00 output / $0.19 cache-hit per MTok, 256K-token context, coding-specialized.
      **K2.6**: $0.95 input / $4.00 output / $0.16 cache-hit per MTok, 256K-token context, general-purpose
      (vision+text, thinking/non-thinking modes). All three match the research pass exactly. **K2.5 is absent from
      the current pricing page entirely** — corroborates the earlier single-source claim that it's being sunset;
      treat k2.5 as likely-retired, not a live option, until the live `/v1/models`-equivalent check in the next
      todo confirms one way or the other. Given this, K2.7 Code (not evaluated at all in the 2026-08-06 rejection)
      is the more relevant NEW comparison point going forward, not K2.5.
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
- [ ] [INFRA] P1. Live-verify Gemma's real available NIM models — operator explicit direction (2026-08-16): **try
      different Gemmas**, not just the two informally-named candidates (`google/diffusiongemma-26b-a4b-it` and a
      `google/gemma-4-31b`-shaped ID). Enumerate NVIDIA's REAL Gemma-family catalog on build.nvidia.com (Gemma 2/3/4,
      CodeGemma, any diffusion variant) rather than assuming those two informal names are the complete or even
      correctly-spelled set. For each real candidate found: confirm it exists via a real authenticated call, record
      real context-window size and rate-limit numbers (NVIDIA's own docs claim "unlimited prototyping" — get the
      REAL enforced per-minute/per-day ceiling by testing against it, the same way Grok 4.6's 500K context ceiling
      was proven hard-enforced rather than trusted from docs). Done when: every real Gemma variant NVIDIA NIM
      actually hosts is confirmed live (not just the original two guesses), and at least one real rate-limit ceiling
      is measured, not assumed from NVIDIA's marketing language.

      **Research pass 2026-08-16 (background agent) — real catalog, via NVIDIA's own `docs.api.nvidia.com`
      reference pages**: full Gemma lineup confirmed beyond the original two guesses — `google/gemma-7b` (Gemma 1,
      legacy, ~8K ctx), `google/gemma-2-2b-it`/`google/gemma-2-9b-it` (4K-8K ctx), `google/codegemma-7b`
      (code-specialized, ~8K ctx), `google/gemma-3-1b-it`/`google/gemma-3-27b-it` (32K/128K ctx, real published
      MMLU/GSM8K/HellaSwag/BBH numbers), ShieldGemma 2 (safety classifier, not a chat model), **`google/gemma-4-31b-it`**
      (dense, 256K ctx, MMLU Pro 85.2%/AIME-2026 89.2%/LiveCodeBench-v6 80.0%/Codeforces ELO 2150/GPQA-Diamond 84.3%),
      **`google/diffusiongemma-26b-a4b-it`** (diffusion-MoE, 26B total/3.8B active, 256K ctx, MMLU Pro 77.6%/GPQA
      73.2%/Codeforces ELO 1429, ~1000 tok/s on one H100 — confirmed weaker on reasoning/coding but faster, matching
      the operator's original informal note). **ID correction**: the informally-named `google/gemma-4-31b` is
      missing the required `-it` suffix — the real hosted ID is `google/gemma-4-31b-it`; the bare non-instruct ID is
      not a NIM chat-completions endpoint. Rate limits: no official NVIDIA-hosted rate-limit spec page found — only
      community-reported (~40 RPM/model/key default, ~200 RPM on request, ~1,000 free inference credits for new
      accounts) — NVIDIA's own forum-cited language is "dependent on model, use-case, and current overall traffic,"
      confirming "unlimited prototyping" masks real, variable, undocumented throttling. Signup: free NVIDIA Developer
      Program account → build.nvidia.com → Settings → API Keys → Generate (key prefix `nvapi-`, works fleet-wide
      across the catalog, no card required). API shape confirmed OpenAI-compatible (base_url
      `https://integrate.api.nvidia.com/v1`, standard `chat.completions.create`).

      **Real smoke test result, 2026-08-16 (key supplied by operator, stored in GSM `nvidia-api-key`)**: a live
      authenticated call against BOTH `google/gemma-4-31b-it` and `google/diffusiongemma-26b-a4b-it` returned
      `HTTP 403 {"status":403,"title":"Forbidden","detail":"Authorization failed"}` — and the SAME 403 against a
      completely unrelated model (`meta/llama-3.1-8b-instruct`), confirming this is key-wide, not a Gemma-specific
      access-scope issue. Key round-tripped through GSM byte-for-byte correct (70 chars, prefix/suffix verified) —
      not a storage/copy-paste corruption on this end. Response also carried a `deprecation: 2026-08-25T00:00:00Z`
      header on this endpoint — worth re-checking closer to that date regardless of the auth outcome. **Needs
      operator-side diagnosis**: check the key's status on the build.nvidia.com dashboard — whether it needs an
      activation step, or whether it's an NGC-catalog key rather than a Build-inference key (NVIDIA has more than
      one key flavor; only a Build/integrate-scoped key works against this endpoint).
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
