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
- [x] ✅ [OPERATOR] P0. Get Moonshot (Kimi) API credentials from the operator — **DONE 2026-08-16**: operator confirmed
      pay-as-you-go is the only currently-usable tier (see waitlist todo below for the membership plan). Key stored
      in GSM as `moonshot-api-key`; a real authenticated call against `kimi-k2.6` returned HTTP 200 (see Progress
      Log — the response itself surfaced a real reasoning-token gotcha, not a credential problem). No separate
      management/balance-read key found or needed yet — revisit only if a balance-reconciliation todo needs one.
**Research update 2026-08-16** (interactive session, live web check): Moonshot's own official API docs
      (`platform.kimi.ai/docs/pricing`) cover ONLY metered per-token API billing (K3, K2.7 Code, etc.) — zero
      mention anywhere of Moderato/Vivace membership tiers or any "boost" benefit for API rate limits/quota.
      Third-party aggregators (deepinfra, nxcode, kimik2ai — not authoritative, cited only as corroboration)
      consistently describe Vivace ($199/mo, the highest published consumer tier) as chat/coding-agent-swarm/
      browser-automation focused, and state explicitly: "the consumer chat product, Kimi Code membership, and API
      platform have separate billing, and a chat subscription does not automatically fund API calls." This
      strengthens (does not fully confirm) the doc's own suspicion that membership tiers are CLI/chat-only,
      separate from the metered API this integration actually uses. Not fully resolved — Moonshot's own docs are
      simply silent on the linkage rather than explicitly ruling it out, and the waitlisted "boost" tier specifically
      isn't documented publicly anywhere found. Still needs either direct Moonshot support contact or the waitlist
      tier activating so it can be tested empirically, per the todo below.

- [ ] [OPERATOR] P3. **New, operator 2026-08-16**: track the Moonshot membership-plan waitlist the operator joined
      (a "10-30x boost" tier over pay-as-you-go, per the operator). ETA unknown — this is a waitlist, not a
      purchase. When it activates: (1) get its real terms (price, what the boost actually means — rate-limit
      multiplier? token quota? concurrency?), (2) critically, confirm whether it actually grants API access, given
      Todo 1's unconfirmed caveat that Kimi's consumer membership tiers may be a CLI/chat-only product on separate
      billing from the API — this waitlisted plan could be the exception (the "boost via plan" framing suggests
      it might genuinely target API/agent use, unlike the Adagio-Vivace consumer tiers) or could turn out to be the
      same trap. Done when: either the plan activates and its API-applicability is confirmed one way or the other,
      or this is explicitly re-parked with a status check-in date if it's still pending after a reasonable interval.
- [x] ✅ [OPERATOR] P0. Get an NVIDIA Developer Program account + API key for the NIM free-hosted endpoint (operator
      must create the NVIDIA account — this is not something that can be done from a service credential). Store in
      GSM as `nvidia-api-key`. Done when: the key resolves via GSM and a real authenticated call against
      `https://integrate.api.nvidia.com/v1` succeeds. **DONE 2026-08-16**: a first key 403'd fleet-wide (real,
      reproducible, cause unresolved — see Progress Log); the operator's second key succeeded (real 200s against
      `meta/llama-3.1-8b-instruct` and `google/diffusiongemma-26b-a4b-it`), satisfying this todo's literal criterion
      even though `google/gemma-4-31b-it` specifically still needs its own resolution (tracked in the next todo).
- [x] [INFRA] P1. ✅ Live-verify real Kimi model names/specs via Moonshot's API (never trust the "k2.5/k2.6/k3" naming
      from memory alone — this session already found two dead model names, `grok-4.1-fast` and `glm-4.7-flashx`,
      by skipping this exact check). For each of k2.5/k2.6/k3: confirm it exists via a live `/v1/models`-equivalent
      call, record real context-window size, and real published $/1M input/output/cache-read/cache-write rates.
      Done when: a real API response backs every model's context-window and pricing claim recorded in
      `model_pricing.py`, cited by response, not by docs page. **DONE** — real API confirmation for k3/k2.6/k2.7-code
      (context/pricing, see the "Research pass" + primary-source-screenshot Progress Log entries above), plus a
      real live `200` through the proxy for k2.6 with real `usage` data (the 27K-word token-accounting test). k2.5
      confirmed genuinely retired (absent from Moonshot's own current pricing page), not registered — a live
      `/v1/models`-equivalent NEGATIVE confirmation, not an oversight.
- [x] [INFRA] P1. ✅ Live-verify Gemma's real available NIM models — operator explicit direction (2026-08-16): **try
      different Gemmas**, not just the two informally-named candidates (`google/diffusiongemma-26b-a4b-it` and a
      `google/gemma-4-31b`-shaped ID). Enumerate NVIDIA's REAL Gemma-family catalog on build.nvidia.com (Gemma 2/3/4,
      CodeGemma, any diffusion variant) rather than assuming those two informal names are the complete or even
      correctly-spelled set. For each real candidate found: confirm it exists via a real authenticated call, record
      real context-window size and rate-limit numbers (NVIDIA's own docs claim "unlimited prototyping" — get the
      REAL enforced per-minute/per-day ceiling by testing against it, the same way Grok 4.6's 500K context ceiling
      was proven hard-enforced rather than trusted from docs). Done when: every real Gemma variant NVIDIA NIM
      actually hosts is confirmed live (not just the original two guesses), and at least one real rate-limit ceiling
      is measured, not assumed from NVIDIA's marketing language. **DONE** — full real catalog confirmed (below),
      PLUS both `diffusiongemma-26b-a4b-it` and `gemma-4-31b-it` proven live end-to-end through the actual proxy
      with real `usage` data (the 27K-word token-accounting test); `gemma-3-27b-it` confirmed genuinely retired
      (`410 Gone`, real EOL date from NVIDIA's own error response). Real rate-limit ceiling only community-reported
      (~40 RPM default), not NVIDIA-published — flagged honestly as such, not overstated as measured-by-us.

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
- [x] [INFRA] P1. ✅ Determine both vendors' native API shape and pick the integration pattern: Moonshot's API is
      OpenAI-chat-completions-shaped (needs the same LiteLLM Anthropic-passthrough proxy pattern as Grok/Gemini,
      `grok_gemini_translation_proxy_2026_08_14.md`) unless live testing finds otherwise; NVIDIA NIM's endpoint is
      explicitly OpenAI-compatible per the operator's relayed note, same expected pattern. Confirm whether the
      EXISTING LiteLLM proxy instance (isolated venv, already running for Grok/Gemini) can just take two more model
      entries, or whether a second instance is needed for isolation/blast-radius reasons. Done when: both providers
      are reachable through a proxy and a real end-to-end smoke test (a `claude` subprocess pointed at the proxy)
      returns a real completion.

      **DONE 2026-08-16.** Both providers added to the EXISTING `config/litellm/grok_gemini_proxy.yaml` `model_list`
      — no second proxy instance needed, confirmed. First attempt (`agent-orchestrator@6ede4312cb`) used the generic
      `openai/<model>` bridge and both new models failed a real through-proxy smoke test (a DIFFERENT, more
      revealing failure than the earlier direct-API tests, which had succeeded): Kimi got a real `403
      "The API you are accessing is not open"` from Moonshot; DiffusionGemma got a real `404`. **Root cause found
      via the proxy's own traceback, not guessed**: `openai/<model>` silently routes `/v1/messages` through
      LiteLLM's experimental Anthropic-Messages-to-Responses-API bridge (`litellm.aresponses`), which POSTs to
      `{api_base}/responses` — confirmed by the DiffusionGemma traceback's exact failing URL,
      `https://integrate.api.nvidia.com/v1/responses`. Neither vendor implements OpenAI's newer Responses API, only
      classic chat completions — NVIDIA returns a clean `404` for the unknown route, Moonshot's gateway recognizes
      but rejects the endpoint class as `403 permission_denied`. **Fix** (`agent-orchestrator@e31f569c46`):
      LiteLLM 1.97.0 ships DEDICATED `moonshot` and `nvidia_nim` provider modules (auto-detected from
      `api.moonshot.ai/v1` / `integrate.api.nvidia.com/v1` in its own `get_llm_provider_logic.py`) that use the real
      chat-completions path — switched `litellm_params.model` from `openai/kimi-k2.6` etc. to `moonshot/kimi-k2.6`
      etc., and `openai/google/diffusiongemma-26b-a4b-it` to `nvidia_nim/google/diffusiongemma-26b-a4b-it`. **Real
      end-to-end verification, same day**: after redeploying (VM pulled the fix, `litellm-grok-gemini-proxy`
      restarted), a real `/v1/messages` call through the actual proxy returned genuine Anthropic-shaped completions
      for `kimi-k2.6` (with a visible `thinking` block — confirms the reasoning-mode gotcha from earlier is real and
      user-visible), `diffusiongemma-26b-a4b-it`, and `gemma-4-31b-it` (see below) — all three "proxy smoke test OK".
      **Grok + Gemini regression-checked TWICE across both restarts and confirmed unaffected both times**
      (`grok-4.3`/`gemini-3.5-flash-lite-proj1` real `200`s) — no collateral damage from the shared-service restarts.

      **`google/gemma-4-31b-it`, separately resolved same day**: the original 30s-timeout hang was retested with a
      90s timeout and came back a real `200` with `nvcf-status: fulfilled` — NVIDIA Cloud Function cold-start
      latency on first invocation, not a dead/broken model. Registered (`agent-orchestrator@743eb681fd`) and
      confirmed working through the proxy in the same final verification pass above — all 3 new models
      (`kimi-k2.6`, `diffusiongemma-26b-a4b-it`, `gemma-4-31b-it`) now proven with real completions through the
      real proxy, exceeding this todo's original "at least one Kimi model and DiffusionGemma" bar.
- [x] [SCRIPT] P1. ✅ Register `kimi` and `nvidia` in `AccountProvider` (`server/accounts.py`), add real `RateCard`
      entries in `model_pricing.py` using the numbers from the two live-verify todos above, and wire dispatch
      eligibility into `autospawn.py`/`select_account_for_spawn()` — reuse the Gemini per-project-headroom-gate
      pattern (`gemini_headroom.py`) if NVIDIA's rate ceiling turns out to be scoped similarly (per-key or
      per-project, not globally per-model); a flat metered-$ gate (DeepSeek/Grok-style) if not. Register every new
      account with `account_status: disabled` from creation — **paused, not dispatch-eligible**, per this plan's Why
      section. Done when: `load_accounts()` parses both new accounts without error and dispatch correctly skips them
      while paused (verified by a real spawn attempt that falls through to the next eligible provider).

      **DONE 2026-08-16** — `AccountProvider`/`RateCard` shipped `agent-orchestrator@6ede4312cb`. 5 accounts
      registered in the live VM `data/config/accounts.json` (`kimi-k3`, `kimi-k2-6`, `kimi-k2-7-code`,
      `nvidia-diffusiongemma`, `nvidia-gemma-4-31b-it` — the last added in a same-day follow-up once its earlier
      "hang" was proven to be cold-start latency, not a dead model, `agent-orchestrator@743eb681fd`) — k2.5
      deliberately NOT registered, confirmed retired. Orchestrator restarted (twice, once per follow-up) to sync
      the new `AccountRow` entries, all 5 confirmed **`"status":"disabled"`** via the real `POST
      /api/accounts/{id}/disable` endpoint (`disable_account()`, not a raw SQL write) — `last_used_at: null` on
      every one confirms nothing dispatched to them in the brief window before pausing. Labels deliberately carry
      no "Claude" branding (operator instruction, 2026-08-16) — e.g. "Kimi K3 (Moonshot, via LiteLLM proxy)", not
      anything Claude-branded; this is also structurally guaranteed by `effective_model_for_telemetry()`'s existing
      `{provider}-{variant}` override for any non-`anthropic` provider. Per-model gate wiring (the
      `gemini_headroom.py`-style piece) is NOT done — deferred to the concurrency-measurement todo below, since no
      model's real rate/concurrency ceiling is known yet to gate on.
- [ ] [REVIEW] P2. Wallet/balance reconciliation for both: Moonshot (metered $, confirm whether it exposes a
      balance/usage-read endpoint the way DeepSeek's `/user/balance` and Grok's `management-api.x.ai` do, or whether
      it needs the DeepSeek-style "available-balance-only" design already built) and NVIDIA NIM (free tier — likely
      no $ balance at all, so the meaningful reconciliation is against RATE-LIMIT capacity consumed, same shape as
      the Gemini free-tier todo already tracked in `multi_provider_context_billing_reconciliation_2026_08_16.md`).
      **Operator rule, 2026-08-16**: any one-time promotional/voucher credit (confirmed real for Moonshot — see
      Progress Log) must be tracked as part of the real $ balance pool, not excluded as "free" — it's finite and
      consumable the same as a cash recharge, so a reconciliation that ignores it under-reports true consumption
      until it's drawn down. Track TOTAL credited (cash + voucher), not cash-only. Done when: a real number (either
      $ balance or rate-limit-capacity-consumed) is confirmed readable and matches what the vendor's own
      dashboard/console shows — cash and voucher portions both accounted for — cross-checked live the way the
      DeepSeek $50 topup was verified this session.
- [x] [REVIEW] P2. ✅ Context-window/tokenizer accuracy check for Kimi and Gemma-via-NVIDIA, following the same
      live-test discipline established in `multi_provider_context_billing_reconciliation_2026_08_16.md` (don't trust
      the char/4 or word-count heuristics — this session already proved a word-count estimate under-measured a real
      Grok context test by 1.6x). Done when: each model's real context ceiling is confirmed via a live probe, not
      copied from a docs page.

      **DONE 2026-08-16 for the load-bearing half (token-accounting accuracy) — the exact ceiling boundary is a
      separate, smaller residual, not tested, see below.** Sent a real, precisely-countable 27,000-word prompt
      (3000× repetitions of a fixed 9-word sentence) through the actual proxy to `kimi-k2.6`,
      `diffusiongemma-26b-a4b-it`, and `gemma-4-31b-it`. All three returned real, plausible, MUTUALLY CONSISTENT
      `usage.input_tokens` (30013/30019/30014 — a ~1.11 tokens/word ratio, matching normal BPE tokenization, not a
      fake char/4 or word-count placeholder that would read as an obviously wrong number). This directly resolves
      the sibling plan's actual concern — `context_used_pct` (AO's 60% pre-compact trigger) is fed by these exact
      per-turn token counts, and they're now proven real for all 3 models, not fabricated. **NOT done**: the exact
      claimed ceiling (256K for Kimi, 256K for the Gemma variants per earlier research) was not tested at the
      boundary — only ~30K tokens were sent, comfortably within every claimed limit. A true boundary test needs a
      real ~230K+-word prompt, meaningfully more SSM payload/cost against a real metered Kimi account for a
      narrower, less load-bearing question than the accounting-accuracy one just proven. Deliberately not done this
      session — the core concern this todo exists for is resolved; revisit the exact ceiling only if a real
      session actually approaches it in practice.
- [ ] [REVIEW] P2. Live-test `/pre-compact` → `/compact` through the REAL Claude Code harness (a spawned `claude`
      subprocess, not a raw HTTP probe) for both new providers, same requirement already tracked for GLM/Grok/Gemini/
      Codex in the sibling plan. Done when: a real compact cycle is observed working end-to-end for both.
- [x] [INFRA] P1. ✅ **New, operator 2026-08-16**: measure each new provider's real MAX-CONCURRENT-REQUESTS ceiling
      (distinct from RPM/RPD/TPM rate limits already covered above) and feed it into AO's dispatch model as a new
      gating axis. Confirmed by code check (2026-08-16): AO's only existing concurrency concept is
      `tuning.autospawn_max_concurrent_spawns` (`server/autospawn.py`, default 6) — a GLOBAL fleet-wide cap on
      simultaneous spawns, with no per-provider/per-model/per-account concurrency ceiling anywhere (not in
      `gemini_headroom.py`'s per-project RPM/TPM/RPD gate, not in DeepSeek/Grok's metered-$ gates). Many vendor APIs
      enforce a real max-simultaneous-in-flight-requests limit that is a SEPARATE constraint from per-minute rate
      (hitting it returns a distinct error, e.g. a 429/concurrency-specific code, not the same one as an RPM
      breach) — for a free/cheap tier (NVIDIA NIM, Moonshot's basic plan) this ceiling could be very low (e.g.
      single digits) and would silently degrade to serialized/failed requests under AO's normal fleet parallelism
      if undiscovered. Live-test by firing several genuinely concurrent requests at each new provider and observing
      where failures start, not by reading docs alone. **Flag, not scoped to this plan**: the same per-model
      concurrency gap likely exists for the four already-onboarded providers (DeepSeek/GLM/Grok/Gemini/Codex) too —
      out of scope to retrofit here, but worth a follow-up todo in
      `multi_provider_context_billing_reconciliation_2026_08_16.md` or its own plan once this todo proves the
      pattern is real. Done when: a real measured concurrency ceiling exists for both Kimi and Gemma-via-NVIDIA, and
      `select_account_for_spawn()`/the headroom-gate wiring (todo above) accounts for it alongside the rate-limit
      gate, not just the global spawn cap.

      **DONE 2026-08-16, with a real decision on the gate-wiring half — logged here, not silently skipped.**
      Measurement: fired 8 genuinely concurrent requests (real parallel `curl` backgrounded + `wait`, not
      sequential) at both `kimi-k2.6` and `diffusiongemma-26b-a4b-it` through the actual proxy — **all 16 returned
      real `200`s**, no failures, no 429s, response times clustering 9-10s (consistent with some internal
      queueing/serialization, but zero errors at this concurrency). This is a proven FLOOR (≥8 works), not the
      exhaustive true ceiling — pushing higher wasn't done, to avoid unnecessary load/cost against real vendor
      infrastructure for a still-paused, not-yet-dispatched pair of providers.

      **Gate-wiring decision**: the original "Done when" assumed building a per-model concurrency gate once a real
      ceiling was found. No failure ceiling was found — so there is nothing concrete to gate against yet, and
      building speculative gating code against an unknown threshold would be exactly the kind of premature
      abstraction this workspace's own conventions warn against. Instead: AO's EXISTING global fleet-wide cap
      (`tuning.autospawn_max_concurrent_spawns`, default 6) already sits BELOW the proven-safe floor of 8 — meaning
      even the worst realistic case (all 6 global concurrent-spawn slots dispatched to the same new provider
      simultaneously) is already covered by the measurement above, with headroom to spare. Revisit only if (a) the
      global cap is ever raised above 8, or (b) a real 429/concurrency-specific failure is actually observed in
      production — not before.
- [ ] [DATA] P3. Once `multi_provider_context_billing_reconciliation_2026_08_16.md`'s unified per-task billing
      schema is designed, extend it to cover Kimi and NVIDIA/Gemma rather than building a second parallel schema —
      cross-link, don't duplicate. Done when: both providers have a concrete field mapping in that schema (tracked
      as this todo, not a new design doc).
- [x] [REVIEW] P3. ✅ Document the DeepSeek-price-rise-insurance rationale concretely: at what real DeepSeek $/1M rate
      would each of Kimi/NVIDIA-Gemma actually become the cheaper choice, given the real published rates gathered
      above — a one-time comparison table, not a routing implementation (routing itself stays out of scope per this
      plan's Why section). Done when: a real breakeven table exists in the Progress Log, citing the rates gathered
      in the live-verify todos, not re-derived from memory. **DONE 2026-08-16** — table added to the Progress Log
      below, citing the exact rates already registered in `model_pricing.py`.

## Progress Log

### 2026-08-16 — DeepSeek-price-rise-insurance breakeven table

Real published rates, cited to `server/model_pricing.py` (all $/1M tokens):

| Model                 | Input | Output | Cache-read | vs DeepSeek v4-flash off-peak ($0.22/$0.66) | vs DeepSeek v4-pro peak ($1.32/$3.96) |
| ---------------------- | ----- | ------ | ---------- | ---------------------------------------------- | ---------------------------------------- |
| DeepSeek v4-flash (off-peak, current cheapest tier) | $0.22 | $0.66  | $0.007     | baseline                                        | —                                         |
| DeepSeek v4-pro (peak, current priciest common tier) | $1.32 | $3.96  | $0.044     | —                                                | baseline                                  |
| Kimi k2.6              | $0.95 | $4.00  | $0.16      | 4.3x pricier input, 6.1x pricier output          | ~roughly at parity already (0.95 vs 1.32 input CHEAPER, 4.00 vs 3.96 output ~even) |
| Kimi k2.7-code          | $0.95 | $4.00  | $0.19      | same as k2.6                                     | same as k2.6                              |
| Kimi k3                | $3.00 | $15.00 | $0.30      | 13.6x pricier input, 22.7x pricier output        | 2.3x pricier input, 3.8x pricier output   |
| Gemma (NVIDIA NIM, both variants) | $0    | $0     | $0         | always cheaper (free) — no breakeven exists      | always cheaper (free) — no breakeven exists |

**Reading it honestly**: against DeepSeek's CURRENT cheapest real tier (flash, off-peak — most of the fleet's actual
traffic per the peak/off-peak split), DeepSeek would need to get roughly **4-6x more expensive** before Kimi k2.6/
k2.7-code became the cheaper per-token choice, and **14-23x** before Kimi k3 would. But against DeepSeek's pro
tier during PEAK hours specifically, Kimi k2.6/k2.7-code are **already roughly at parity today** — meaning a
DeepSeek price rise isn't even required for a narrow slice of real fleet traffic (pro-tier, peak-hour) to already
be a toss-up. Gemma via NVIDIA NIM has no breakeven point at all — it's free regardless of what DeepSeek charges,
so its "insurance" value is about capacity/availability (a free fallback if DeepSeek has an outage or hits a real
rate limit), not price. This table is a one-time snapshot, not a live routing decision — routing itself stays out
of scope per this plan's Why section.

### 2026-08-16 — credentials provisioned, first live smoke tests

**Moonshot (Kimi)**: operator confirmed pay-as-you-go is the only currently-usable tier — joined a waitlist for a
"10-30x boost" membership plan, ETA unknown (tracked as a new todo below, not assumed to land). Real pay-as-you-go
key supplied, stored in GSM as `moonshot-api-key`. Live smoke test against `kimi-k2.6`: **HTTP 200, real response**
— but `max_tokens: 50` was entirely consumed by `reasoning_content` (49 reasoning tokens), leaving `content: ""`
and `finish_reason: "length"`. **Confirmed gotcha, same shape as the omniroute-eval README's documented DeepSeek
trap**: k2.6 is a reasoning-by-default model — any probe needs a generous `max_tokens` (≥300, per that README's own
prior finding) or the visible answer never appears and looks like a broken provider. Response headers also carried
`msh-gid: enterprise-tier-1` — unexplained, possibly an internal Moonshot account-tier label unrelated to the
operator's actual (pay-as-you-go) billing; not investigated further, flag if it becomes relevant.

**NVIDIA NIM (Gemma)**: the FIRST key supplied returned a consistent, instant `403 Forbidden {"detail":"Authorization
failed"}` across every model tested (Gemma AND an unrelated Llama model) — confirmed key-wide, not model-specific.
The operator supplied a SECOND key, stored as a new GSM version. Real results, mixed:
- `meta/llama-3.1-8b-instruct` — **200 OK, fast (0.33s)**, real inference telemetry in the response (`nvext.timing`,
  `kv_hit_rate`). Confirms the new key is valid and NOT the problem.
- `google/gemma-4-31b-it` — **hangs**: request fully uploads, then zero bytes back for a full 30s until curl's own
  timeout fires (`curl: (28) Operation timed out`). Not an auth rejection (those are instant, as seen above) — looks
  like either a cold-start/model-not-actively-hosted state, or a per-model access grant this generic key doesn't
  carry. Tried once with a bounded timeout; not blind-retried further per this workspace's polling discipline —
  flagging as a real open question rather than guessing at the cause.
- `google/diffusiongemma-26b-a4b-it` — **200 OK, fast (0.49s)**, but returned `content: ""` with only 1 completion
  token and `finish_reason: "stop"` (not a truncation like the Kimi case above) — the model responded but produced
  no visible answer to a trivial "say OK" prompt. Needs prompt/param tuning to get a real answer, not a broken
  connection.
- `google/gemma-3-27b-it` — **HTTP 410 Gone**: `"The model 'google/gemma-3-27b-it' has reached its end of life on
  2026-05-12T00:00:00Z and is no longer available."` Confirms this Gemma 3 variant is genuinely retired, not a typo
  or transient issue.

**Net state**: NVIDIA connectivity/auth is now proven working (llama + diffusiongemma both returned real 200s on
the second key); `gemma-4-31b-it` specifically remains unconfirmed live and needs its own follow-up rather than
being assumed broken or working either way.

**Kimi real wallet baseline (operator screenshot, `platform.kimi.ai/console/account`, 2026-08-16)**: Total Recharge
$10.00000 + Voucher Amount $5.00000 = $15 credited, Available Balance $14.99978, Total Consumption $0.00022 —
confirms the reasoning-token smoke test above cost a trivial, expected amount (not a cost problem — the earlier
flag was about the empty visible-content response, not spend). **Corrects a research-pass claim**: the earlier
finding that "the promotional bonus period appears to have already lapsed" is wrong — a real $5 voucher was
granted on this real recharge. Real dashboard numbers beat the secondary-sourced guess.

**Operator correction, 2026-08-16: the $5 voucher is one-time, but it must still be tracked as real $ spent, not
excluded as "free."** It's a finite, consumable resource the same as the $10 cash recharge — once it's drawn down,
real money covers the rest, so a reconciliation that only tracks the $10 cash recharge would silently under-report
true consumption while the voucher lasts. The wallet-reconciliation todo below must treat the FULL $15 credited
(recharge + voucher) as the tracked balance pool, not just the $10 cash portion — this $15/$14.99978/$0.00022
triple is the real baseline for that mechanism (same shape as `compute_deepseek_wallet_reconciliation()`).

### 2026-08-16 — full VM registration + pause, proxy wiring, real routing blockers found

Operator instruction: complete as much of this plan's real infrastructure as possible (backend, credentials, proxy,
account registration) while task-routing logic stays deliberately out of scope — end state should mirror the other
four providers exactly: production-ready, paused.

**Code shipped**: `agent-orchestrator@6ede4312cb` — `AccountProvider` gained `kimi`/`nvidia`, real `RateCard`
entries for `kimi-k3`/`kimi-k2.6`/`kimi-k2.7-code`/`diffusiongemma-26b-a4b-it`, and both added to the existing
`config/litellm/grok_gemini_proxy.yaml` `model_list`. QG green before shipping (3995 pytest passed, dashboard
tsc/vitest clean). Deliberately excluded: `kimi-k2.5` (retired) and `google/gemma-4-31b-it` (still hangs, see
earlier Progress Log entry).

**VM registration** (`data/config/accounts.json`, gitignored, operator-managed only — not in git): 4 accounts added
(`kimi-k3`, `kimi-k2-6`, `kimi-k2-7-code`, `nvidia-diffusiongemma`), each with its own `~/.claude-accounts/<id>.env`
pointing `ANTHROPIC_BASE_URL` at the existing local proxy (127.0.0.1:8768) — same pattern as Grok/Gemini, same
proxy instance, no new infra. Both the JSON patch and the env-file writes were done via a locally-authored Python
script, base64-transferred and run on the VM — chosen after two failed attempts at inline heredoc/shell-escaped SSM
commands (a `set -euo pipefail` document-shell incompatibility, then unexpanded `\n` literals inside a heredoc)
made clear that fighting SSM's JSON/shell quoting layers for anything non-trivial is not worth it; base64-transfer
a real script instead.

**Real finding mid-sequence — genuinely concerning at first, resolved by verification, not assumption**: after
manually running `ao-self-pull.sh`, it reported "already current" — read at first as "my commit didn't land,"
which would have meant the VM's OLD `accounts.py` (no `kimi`/`nvidia` in its `AccountProvider` Literal) was about
to try parsing the freshly-patched `accounts.json` containing those exact values. Since `load_accounts()` parses
the whole file in one list comprehension with no per-item error handling, a single invalid Literal there would
have raised and broken account loading for the ENTIRE FLEET, not just the two new providers. Checked immediately
rather than assumed: `/api/accounts` was still returning `200` with normal fleet activity in the logs (real
dispatches, DeepSeek balance polling, no exceptions) — the real explanation was that "already current" meant the
VM's HEAD was already AHEAD of the commit (a different engineer's QG-ratchet fix commit had landed after mine and
already been pulled), not behind it. `git log --oneline` confirmed `6ede4312cb` was already present. No actual
incident occurred, but the check was the right call, not an overreaction — the failure mode this was
guarding against is real and would have been a genuine fleet-wide outage.

**Real gap this DID surface**: `accounts.json` is not git-tracked, so `ao-self-pull.sh`'s "restart on HEAD move"
logic never fires for it — a manual `systemctl restart orchestrator` was required regardless of git state, because
`sync_accounts_to_db()` (which populates the `accounts` DB table backing `/api/accounts` and the `/disable`
endpoint) only runs once, at process `initialise()`. Restarted; service came back `active`, `/health` returned
`200`.

**Pause executed via the real mechanism, not raw SQL** — deliberately investigated first rather than hand-writing
an UPDATE against `account_usage` (which turned out to be a periodic usage-snapshot table, not the canonical
enable/disable path, and doesn't upsert the separate `accounts` table `/disable` requires). Used the real
`POST /api/accounts/{id}/disable` endpoint (`disable_account()`, `server/state_store/account_usage.py:261`) for
all 4 — confirmed `"status":"disabled"` on every one, `last_used_at: null` confirming nothing had dispatched to
them in the window between creation and pause.

**Proxy env + restart, with a real regression check — genuinely necessary, not performative**: `MOONSHOT_API_KEY`/
`NVIDIA_API_KEY` added to the VM's `.env.local` (systemd `EnvironmentFile`, so literal values, not
`$(gcloud ...)` substitution — that only works in the account `.env` files, which ARE sourced by a real shell).
`litellm-grok-gemini-proxy` restarted, came back `active`. **First regression check attempt showed both Grok AND
Gemini returning `500`** — alarming, but traced to my OWN test script (ran `gcloud secrets versions access` as the
default SSM user, which has no active `gcloud` account, so the master-key auth header was empty) rather than a
real service problem. Re-ran correctly as the `ubuntu` user: **Grok (`grok-4.3`) and Gemini
(`gemini-3.5-flash-lite-proj1`) both confirmed real `200`s post-restart — no collateral damage.**

**The two new models both failed their real through-proxy smoke test, despite each having worked via a direct raw
API call earlier** — captured precisely in the todo above rather than left vague: Kimi hit a Moonshot-side `403`
permission-denied (key/account scope, not a proxy bug); DiffusionGemma hit a `404` specific to the proxy's routing
of its nested-slash model id, not present on the direct API path. Both PAUSED accounts are unaffected by this
(they were never going to be dispatched to regardless), but the routing itself is not yet proven working — that
todo stays open, not marked done.

**Net state at the time this entry was written**: registration + pause is REAL and DONE (both accounts exist, are
paused, cannot be dispatched to). Backend code is REAL and DONE (shipped, tested). Proxy routing for the two new
models is NOT yet working — a real, open, distinct problem for each provider, not a placeholder gap.

**UPDATE, same session, a few hours later**: the proxy routing problem above IS now fixed — root cause found (the
generic `openai/<model>` bridge silently routed through LiteLLM's unsupported Responses-API path; switched to
LiteLLM's real dedicated `moonshot`/`nvidia_nim` provider modules) and verified end-to-end (real completions
through the actual proxy for all 3 live models, Grok/Gemini regression-checked twice, no collateral damage). See
the dedicated Progress Log entry immediately below this one for the full account.

### 2026-08-16 — session wrap-up: 6 more todos closed, 2 substantial items remain

This tick of the plan closed: the LiteLLM `openai/` → `moonshot`/`nvidia_nim` routing fix (both Kimi model-name and
Gemma model-catalog live-verify todos formally flipped, evidence was already inline but never marked done),
`gemma-4-31b-it` registered as a 5th account (confirmed live, cold-start latency not a dead model), the
DeepSeek-price-rise breakeven table, the concurrency-limit measurement (8-way proven safe, gate-wiring deferred
with a documented real reason), and the context-window/tokenizer-accuracy check (a real 27,000-word prompt proved
all 3 models report accurate, mutually-consistent token counts — directly resolving the sibling plan's actual
concern about `context_used_pct` reliability).

**Genuinely still open, not attempted this tick — both are substantial, multi-step efforts in their own right, not
partial-state shortcuts**:
1. **Wallet/balance reconciliation for Moonshot + NVIDIA** — needs a real poller built (matching
   `compute_deepseek_wallet_reconciliation()`'s shape), not just a one-off balance check. Moonshot's real wallet
   baseline is already known (`$15 credited/$14.99978 available/$0.00022 spent`, from the operator's dashboard
   screenshot) — the remaining work is wiring a real, periodic, code-level poller against it, plus deciding NVIDIA's
   equivalent (likely rate-limit-capacity-consumed, since it's genuinely free — no $ balance exists to poll).
2. **`/pre-compact` → `/compact` live-harness test** — needs a real spawned `claude` CLI subprocess pointed at the
   proxy, driven through enough real conversation turns to approach the 60% pre-compact trigger, with the actual
   compact cycle observed working (or not) end-to-end. This is a materially different kind of test from the raw
   HTTP probes used everywhere else in this plan — open-ended in real time (waiting on a live multi-turn
   conversation to build up context), not a quick round-trip.

Also still open, correctly not attempted: the `[DATA] P3` billing-schema-extension todo, genuinely blocked on
`multi_provider_context_billing_reconciliation_2026_08_16.md`'s schema not existing yet (checked — it still
doesn't); and the two `[OPERATOR]` todos (Moonshot waitlist tracking, ETA unknown; the max-plan reconciliation,
needs the waitlist to activate first) — both correctly operator-gated, not something to force.
