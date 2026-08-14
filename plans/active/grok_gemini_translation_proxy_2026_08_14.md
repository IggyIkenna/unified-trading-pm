---
doc_type: plan
title: Grok + Gemini translation proxy — self-hosted Anthropic-format facade
summary:
  Stand up a self-hosted LiteLLM-based proxy presenting an Anthropic-compatible endpoint in front of Grok (xAI,
  OpenAI-shaped backend) and Gemini (Google-shaped backend, free-tier only), so AO can dispatch to both while Claude
  Code's harness — CLAUDE.md, skills, hooks — never changes.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, grok, xai, gemini, google, model-routing, multi-provider, translation-proxy, free-tier]
related:
  [
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/codex_luna_flex_bridge_2026_08_14.md,
    /codex/06-coding-standards/model-tier-selection.md,
  ]
created: 2026-08-14
last_updated: 2026-08-14
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
depends_on: [deepseek_claude_blended_provider_routing]
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
    agent-orchestrator/server/deepseek_balance.py,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
  ]
---

# Grok + Gemini translation proxy — self-hosted Anthropic-format facade

## Why

Operator decision (interactive session, 2026-08-14): onboard Grok (xAI) and Gemini (Google) as additional sonnet-tier
fallback providers, reusing the SAME `select_account_for_spawn()`/`AccountProvider` mechanism the sibling DeepSeek/GLM
plan owns. Unlike DeepSeek/GLM, **neither vendor ships an Anthropic-compatible endpoint** — Grok's API mimics OpenAI's
chat-completions shape, Gemini has its own distinct shape. Standing requirement, restated multiple times this session:
Claude Code's harness (CLAUDE.md/skills/hooks) must not change for any provider — every provider must present as if it's
just another Claude account. This plan's core deliverable is a self-hosted **LiteLLM proxy in Anthropic-passthrough
mode**, chosen over a bespoke translator because it's a mature, well-documented open-source project already built for
exactly this translation (verified this session, not assumed).

**Final model selection, decided this session:**

- **Grok**: two models for comparison — xAI's current best/flagship model, and **Grok 4.1 Fast** ($0.20/$0.50 per 1M,
  the cheapest paid tier available; confirmed this session there is no cheaper option and no subscription bundles API
  access at any SuperGrok tier). Metered $ wallet, balance-readable via `management-api.x.ai` (a management-key-scoped
  read endpoint, same shape as DeepSeek's `/user/balance`).
- **Gemini**: **free tier only, two models** — Gemini 3.5 Flash-Lite and Gemini 3.7 Flash. **Gemini 3.5 Flash (non-Lite)
  is explicitly OUT OF SCOPE** — its generous quota numbers were from a paid-tier project the operator is not using. **3
  API keys, 6 accounts**: one credential per GCP/AI-Studio project (3 keys total), each usable for both models — mirrors
  DeepSeek's existing pro/flash pattern exactly (one credential, two `accounts.json` entries differentiated by
  `variant`). 6 `accounts.json` entries = 3 projects × 2 models, each pair within a project sharing that project's
  single credential. Project stays its own identity dimension because Gemini's rate ceiling is scoped per-project, not
  per-model globally — that's what the extra dimension is for, not a fourth credential axis. Confirmed real per-account
  free-tier ceilings (operator-supplied, 2026-08-14 — supersedes an earlier, much more generous table that turned out to
  be a different, paid-tier project's numbers):

  | Model          | RPM (per account) | TPM (per account) | RPD (per account) | Pooled ×3                     |
  | -------------- | ----------------- | ----------------- | ----------------- | ----------------------------- |
  | 3.5 Flash-Lite | 15                | 250K              | 500               | 45 RPM / 750K TPM / 1,500 RPD |
  | 3.7 Flash      | 5                 | 250K              | 20                | 15 RPM / 750K TPM / 60 RPD    |

  Zero $ spend on either model. Combined ceiling across all 6 accounts (1,560 requests/day) is thin against AO's real
  measured fleet volume (up to 41,820 turns in a single day, 7-day pull 2026-08-14) — Gemini's role here is a free
  evaluation-tier fallback, not meaningful load-bearing capacity; real-time per-request rate-limit gating is mandatory,
  not a nice-to-have, given how fast a 20-request daily ceiling is consumed at fleet scale.

  **Known future option, not built now**: Google has offered a negotiated 50% discount on Gemini 3.7 Flash if the
  operator moves to paid usage (~$0.375/$1.875 per 1M), which also unlocks a much higher quota ceiling. Free-tier-only
  for now per operator instruction; revisit if/when a paid decision is made.

**Codex SSOTs this plan depends on**: the sibling `deepseek_claude_blended_provider_routing_2026_07_28.md` plan owns
`select_account_for_spawn()`, `AccountProvider`, the provider-pinning mechanism, and `model_pricing.py`'s `RateCard`
system — reused here, not reimplemented. `model-tier-selection.md` for the sonnet/opus/fable eligibility gate this
plan's providers must respect identically (opus/fable hard-pinned to Claude, never Grok/Gemini).

## Non-goals

- Not building the Codex/Luna bridge — that's the sibling plan's job (a structurally different problem: stateful
  subscription-authenticated protocol, not a stateless API key call).
- Not pursuing xAI's SuperGrok+OpenCode subscription integration — ruled out this session (a competing agent harness,
  not an API facade; conflicts with the "stays Claude Code" requirement).
- Not building for Gemini's paid tier / the negotiated 3.7 Flash discount — documented as a future option only.

## Design summary

A self-hosted LiteLLM proxy process, deployed on/reachable from the orchestrator VM, exposes an Anthropic-compatible
`/v1/messages` endpoint and routes to two backend classes:

1. **Grok backends** (2 models) — LiteLLM's native xAI provider support, translating Anthropic-format requests to xAI's
   OpenAI-shaped chat-completions API and back, including `tool_use`/`tool_result` translation.
2. **Gemini backends** (6 accounts: 2 models × 3 projects) — LiteLLM's native Gemini provider support, same translation
   shape, with an added per-(project, model) RPM/TPM/RPD headroom tracker that gates dispatch before LiteLLM ever issues
   the call (LiteLLM itself doesn't know about AO's fleet-wide dispatch decisions).

Both register as `accounts.json` entries pointing their `ANTHROPIC_BASE_URL` at the local LiteLLM proxy's address,
differentiated by model/route the same way DeepSeek's pro/flash variants are differentiated today.

## Todos

- [ ] [OPERATOR] P1. xAI account + API key for both Grok models (best/flagship + 4.1 Fast) — credential-ask, no existing
      access. Done when: a real key exists and is handed to an agent session for registration.
- [ ] [OPERATOR] P1. Confirm which of the 3 already-set-up GCP/AI-Studio projects map to which quota profile — the
      operator-supplied numbers in this plan's Why section are one profile; confirm all 3 projects share it or supply
      per-project numbers if they differ, since assuming uniformity across projects would be a real bug. Hand over the 3
      project API keys (one per project, each usable for both models) once confirmed. Done when: 3 real keys exist, each
      tagged with its project and confirmed RPM/TPM/RPD ceiling.
- [ ] [INFRA] P1. Pre-flight billing-health check on each of the 3 Gemini projects before registration, not just a
      quota-number confirmation — two distinct real failure modes found 2026-08-14 testing two OTHER real GCP projects
      (see Progress Log): (a) `billingEnabled:true` on a project means NO free-tier bucket runs in parallel — every call
      bills at standard rates regardless of volume, so any of the 3 projects with billing linked silently invalidates
      this plan's $0-spend design for that project; (b) even a project that looks billing-healthy in every config read
      (`billingEnabled:true`, billing account `open:true`) can still have every paid call denied by Google's internal
      payment/collections gate (`403 "Lightning dunning decision is deny"`) — invisible to any config read, only
      surfaces on a real call. Done when: each of the 3 projects is confirmed `billingEnabled:false` via
      `gcloud billing projects describe <project>` (true free tier), AND a real smoke `generateContent` call against
      each succeeds — not just a config check.
- [ ] [INFRA] P0. Stand up a self-hosted LiteLLM proxy in Anthropic-passthrough mode on/reachable from the orchestrator
      VM (same "must run where workers spawn" requirement flagged in the ruled-out OmniRoute doc — not the operator's
      laptop). Configure Grok (2 models) and Gemini (6 accounts) as backends. Done when: a manual
      `curl -X POST /v1/messages` against the proxy returns a valid Anthropic-shape response sourced from a real Grok
      completion and a real Gemini completion.
- [ ] [REVIEW] P0. Verify system-prompt + `tool_use`/`tool_result` translation correctness with a real skill/tool-call
      smoke test before any live fleet traffic — LiteLLM is designed for this, but it must be proven against THIS
      workspace's actual tool schemas, not assumed correct from general maturity. Done when: a real multi-step
      tool-calling exchange completes correctly through the proxy for both Grok and Gemini backends.
- [ ] [INFRA] P1. Register `AccountProvider` value `"grok"` (2 model variants via the existing `variant` field pattern,
      mirroring DeepSeek's pro/flash split) and extend the existing `"gemini"` value with a new project-identity field
      on `AccountDef` — Gemini is the only provider where one credential ≠ one account (GCP quota is per-project, not
      per-model globally). Done when: QG green, all 8 accounts (2 Grok + 6 Gemini) resolve to `status: healthy` via
      `/api/accounts`.
- [ ] [DATA] P1. Add `RateCard` entries for both Grok models — real
      $/1M input/output confirmed this session
      ($0.20/$0.50 for 4.1 Fast; flagship model's rate to be confirmed at registration since xAI's lineup moves fast).
      **Cache-read rates for these specific models were NOT confirmed this session** (only sibling-model rates were
      found via research) — verify against the live API response, do not hardcode the extrapolated estimate as fact.
      Gemini needs no `RateCard` (free tier, $0
      by construction) but DOES need the RPM/TPM/RPD ceilings recorded per-account for the headroom tracker below. Done
      when: `price_usage()` returns non-None for both Grok models against a real captured usage sample.
- [ ] [INFRA] P1. Build the Grok wallet-balance poller against `management-api.x.ai` (requires a management key with
      billing-read ACLs, separate from the inference API key), mirroring `deepseek_balance.py`'s GSM-first token
      resolution + polling-cadence pattern. Done when: a real balance value is fetched and surfaced via `/api/accounts`,
      refreshing on the same cadence class as DeepSeek's existing poller.
- [ ] [INFRA] P0. Build a per-(project, model) Gemini RPM/TPM/RPD headroom tracker that GATES dispatch (not just
      displays it) inside `select_account_for_spawn()` — given the tightest ceiling is 20 requests/day, real-time gating
      is the only thing preventing an immediate 429 storm at AO's real fleet scale. Done when: a simulated dispatch
      against a near-ceiling stubbed account shows exclusion, and a real live account is proven to actually throttle
      correctly against Google's reported quota (not just AO's own internal counter drifting from reality).
- [ ] [INFRA] P1. Accurate usage-capture for both — verify the LiteLLM proxy's own usage reporting against each vendor's
      real dashboard/console numbers (xAI console, Google AI Studio quota page) before trusting it directly, same
      principle as every other new provider this session (DeepSeek's own compat endpoint under-reported before this was
      caught). Done when: a dated comparison of captured-vs-vendor-reported usage for a real sample of turns is
      recorded, with a stated tolerance.
- [ ] [DATA] P2. Feed any Grok cache-rate gap discovered by the RateCard todo above into the shared heuristic
      reconciliation mechanism built in the sibling DeepSeek/GLM plan (infer from real observed usage vs billed spend
      rather than leaving it unpriced). Done when: a documented, derivation-shown rate lands in `model_pricing.py`.
- [ ] [INFRA] P1. Verify/extend provider-pinning for sequential and resumed tasks (operator instruction, 2026-08-14 —
      same requirement as the sibling Codex plan): confirm the existing `_resume_pass`/`preferred_provider` mechanism
      correctly pins a crash-resume to the SAME Grok/Gemini account it was using, add the same same-provider soft
      preference across a `sequential: true` chain's todos, and confirm any real provider switch is always a fresh
      tmux/process spawn (never an in-place `ANTHROPIC_BASE_URL` change mid-session — should already hold structurally,
      verify with an explicit test rather than assume). Done when: the three-part test described in the sibling Codex
      plan's equivalent todo passes for Grok and Gemini accounts too.
- [ ] [REVIEW] P2. After ~1-2 weeks live, measure real completion quality and (for Grok) real $/task across both
      providers against the Claude/DeepSeek/GLM baseline — feeds the same "get an idea of how well they complete things
      and how much things cost" calibration goal recorded in the sibling plan. Done when: a dated Progress Log entry
      with real per-provider quality and cost numbers lands.

## Progress Log

- **2026-08-14 (interactive session)**: Plan authored from a same-session design conversation covering provider pricing
  research (list vs. cache-weighted vs. subscription-effective rates), OpenCode alternative investigated for Grok and
  ruled out, exact free-tier Gemini quota numbers reconciled after an initial generous-table mixup, and the 6-account (2
  model × 3 project) Gemini structure confirmed. No code written yet.

- **2026-08-14 (later, separate session) — Gemini auth mechanics confirmed against two real GCP projects (not this
  plan's own 3 target projects), directly explaining why this plan's own quota table already needed a mixup
  correction.** Findings:
  - **The `generateContent` 404 "no longer available to new users... use the Interactions API" error is per-MODEL-NAME,
    not per-endpoint.** Confirmed by hitting the identical error through classic REST `generateContent`, the new
    `v1beta2/interactions` REST endpoint, AND the official `google-genai` SDK's `client.interactions.create()` (built
    from the SDK's own `CreateModelInteraction` request schema, not a guessed shape) — all three reject
    `gemini-2.5-flash`/`gemini-2.5-pro` identically for a project classified as a "new user." The fix is a current model
    name, not an API-surface migration. Confirmed working end-to-end (`client.models.generate_content()`, real text +
    `usage_metadata` returned): `gemini-flash-latest`, `gemini-pro-latest`. This plan's chosen models (3.5 Flash-Lite,
    3.7 Flash) are unaffected — neither is on the retired-name list — recorded so the error isn't misdiagnosed as an
    endpoint problem if hit during registration.
  - **Confirmed mechanically why the plan's earlier generous-table mixup happened**: a GCP project's billing-account
    linkage is binary and project-scoped, not key-scoped. `billingEnabled:false` → free tier, the RPM/TPM/RPD numbers
    this plan documents apply. `billingEnabled:true` → NO parallel free bucket at all; every request bills at standard
    rates regardless of volume (verified via `gcloud billing projects describe <project>`).
  - **New failure mode, not yet covered by this plan's design — see the new INFRA todo above.** A project can show
    `billingEnabled:true` AND its billing account can show `open:true`, and still have every paid call denied:
    `403 "Lightning dunning decision is deny for project: ..."` — Google's internal payment/collections gate. Confirmed
    live on the org's shared `central-element-323112` project: every config read looked healthy, but every real API call
    403'd. Invisible to any `gcloud`/API config read; only surfaces on a real call.
  - **Verification method worth reusing for the 3 target projects' quota numbers**: the Cloud Quotas API
    (`cloudquotas.googleapis.com`, enable per-project via `gcloud services enable`) returns real numeric RPM/TPM/RPD
    values per quota-id per model — `GET .../services/generativelanguage.googleapis.com/quotaInfos` with an ADC bearer
    token + `X-Goog-User-Project` header. Ground-truth and scriptable, unlike AI Studio's browser-only dashboard or
    third-party blog posts — worth running against the real 3 projects to independently verify the operator-supplied
    numbers in the Why section's table rather than trusting them un-cross-checked.
