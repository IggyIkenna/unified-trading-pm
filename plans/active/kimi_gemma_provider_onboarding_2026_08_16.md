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
      **Operator rule, 2026-08-16**: any one-time promotional/voucher credit (confirmed real for Moonshot — see
      Progress Log) must be tracked as part of the real $ balance pool, not excluded as "free" — it's finite and
      consumable the same as a cash recharge, so a reconciliation that ignores it under-reports true consumption
      until it's drawn down. Track TOTAL credited (cash + voucher), not cash-only. Done when: a real number (either
      $ balance or rate-limit-capacity-consumed) is confirmed readable and matches what the vendor's own
      dashboard/console shows — cash and voucher portions both accounted for — cross-checked live the way the
      DeepSeek $50 topup was verified this session.
- [ ] [REVIEW] P2. Context-window/tokenizer accuracy check for Kimi and Gemma-via-NVIDIA, following the same
      live-test discipline established in `multi_provider_context_billing_reconciliation_2026_08_16.md` (don't trust
      the char/4 or word-count heuristics — this session already proved a word-count estimate under-measured a real
      Grok context test by 1.6x). Done when: each model's real context ceiling is confirmed via a live probe, not
      copied from a docs page.
- [ ] [REVIEW] P2. Live-test `/pre-compact` → `/compact` through the REAL Claude Code harness (a spawned `claude`
      subprocess, not a raw HTTP probe) for both new providers, same requirement already tracked for GLM/Grok/Gemini/
      Codex in the sibling plan. Done when: a real compact cycle is observed working end-to-end for both.
- [ ] [INFRA] P1. **New, operator 2026-08-16**: measure each new provider's real MAX-CONCURRENT-REQUESTS ceiling
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
