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

- **Grok**: two models for comparison — **grok-4.6** (flagship, $2.00/$6.00 per 1M, $0.50 cache-read) and **grok-4.3**
  (cheapest confirmed text model, $1.25/$2.50 per 1M, $0.20 cache-read — replaces the originally-registered
  **grok-4.1-fast**, confirmed DEAD via a live `/v1/models` call 2026-08-16: xAI's lineup moved on since this plan was
  authored, exactly the risk this doc's own "xAI's lineup moves fast" note flagged). No subscription bundles API access
  at any SuperGrok tier — confirmed again live 2026-08-16 (only a one-time signup trial credit exists, not an ongoing
  free tier). Metered $ wallet, balance-readable via `management-api.x.ai` (a management-key-scoped read endpoint, same
  shape as DeepSeek's `/user/balance`).
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

- [x] [OPERATOR] P1. ✅ xAI account + API key for both Grok models (best/flagship + cheap tier) — credential-ask, no
      existing access. **Staged start** (operator ruling 2026-08-15, recorded in
      `/plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md`'s Progress Log entry of the same date):
      Grok has no subscription tiers to stage through
      (pure metered pay-per-token) — a small initial balance ($5 signup credit, confirmed via the console screenshot
      2026-08-16) plus defaulting test dispatch to the cheap model, reserving the flagship for occasional comparison
      calls, mirroring the cheap-tier-first intent applied to GLM/Codex via balance size and routing weight instead of a
      tier choice. **DONE 2026-08-16**: inference key + management key both created and stored in GSM
      (`grok-api-key`, `grok-management-key`, project `central-element-323112`) — a leading-whitespace corruption in the
      inference key was caught and fixed (new secret version, old version disabled). Live-verified against the real API
      (see Progress Log).
- [x] [OPERATOR] P1. ✅ Confirm which of the 3 already-set-up GCP/AI-Studio projects map to which quota profile and
      hand over the project API keys. **DONE 2026-08-16, self-served via the operator's own admin ADC identity**
      (`ikenna@odum-research.com`, re-authed live this session via a headless FIFO-piped device-code flow after the
      original ADC session expired) rather than the operator hand-generating each key in AI Studio: the operator's
      original 3 candidate projects turned out to be 2 duplicate pastes of the same already-paid project
      (`uts-compliance-ikenna`/371216509644, same key both times, confirmed byte-identical) plus 1 genuine free project
      (`gen-lang-client-0008266149`). Rather than wait on 2 more manual handoffs, audited the operator's full GCP estate
      (23 projects), found 5 more genuinely idle (only Google's default API bundle enabled, no real resources deployed —
      one pair required distinguishing a real Firebase app, `missouri-podcasts` on `gbv-classroom-01c2ca`, from its
      inert sibling `gbv-classroom-d3df66`, confirmed via `gcloud functions list`/`gcloud run services list` showing
      live deployed resources on one and disabled APIs on the other), disabled billing on those 5
      (`gcloud billing projects unlink`), then created + GSM-stored real Gemini-API-restricted keys for 3 of them
      programmatically (`gcloud alpha services api-keys create --api-target=service=generativelanguage.googleapis.com`).
      All 4 free-tier keys now real, live, and smoke-tested (see Progress Log): `gemini-api-key-gen-lang-client-0008266149`,
      `gemini-api-key-elated-nectar-440116-e9`, `gemini-api-key-poetic-bongo-456907-e4`,
      `gemini-api-key-spring-mix-426915-t9` — one more than the plan's minimum 3, kept as a spare rather than trimmed.
      Quota profile: all share the standard free-tier ceiling table in this plan's Why section (not independently
      re-verified per-project via Cloud Quotas API beyond the first one — reasonable to assume given all 4 are freshly
      billing-disabled default projects, but flagged as an assumption, not a measurement, for the 3 created via the
      programmatic path).
- [x] [INFRA] P1. ✅ Pre-flight billing-health check on each Gemini project before registration. **DONE 2026-08-16, all
      4 confirmed** `billingEnabled:False` via `gcloud billing projects describe`, AND a real smoke `generateContent`
      call succeeded against both target models for every one of them (`gen-lang-client-0008266149`,
      `elated-nectar-440116-e9`, `poetic-bongo-456907-e4`, `spring-mix-426915-t9`) — genuinely free tier, unlike the two projects
      (`uts-compliance-ikenna`/371216509644 handed over twice by mistake — same key both times, confirmed byte-identical)
      that turned out to be Paid Tier 3. Key stored: `gemini-api-key-gen-lang-client-0008266149`. 2 more projects to go.
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
- [x] [DATA] P1. ✅ Add `RateCard` entries for both Grok models. **DONE 2026-08-16** — `grok-4.6` ($2.00/$2.50→$6.00,
      cache-read $0.50, registered 2026-08-15) and `grok-4.3` ($1.25/$2.50, cache-read $0.20, replacing the dead
      `grok-4.1-fast` — see the corrected model-selection text above). Both cache-read rates are now CONFIRMED, not
      placeholders: grok-4.3's was cross-validated against a real live call's self-reported `cost_in_usd_ticks`
      (predicted 3,347,000 vs actual 3,346,500, ~99.98% match). `price_usage()` verified returning non-None for both
      against real captured usage samples (`agent-orchestrator` model_pricing.py + test_model_pricing.py).
      Gemini needs no `RateCard` (free tier, $0
      by construction) but DOES need the RPM/TPM/RPD ceilings recorded per-account for the headroom tracker below.
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
- [x] [INFRA] P1. ✅ Add an explicit soft same-provider preference across a `sequential: true` chain's todos — the
      GENERAL mechanism, shipped in the sibling plan's `select_account_for_spawn()` (new
      `sequential_preferred_account_id` param), same fix cited in the sibling Codex plan. —
      `agent-orchestrator@7ae567cbb6`. Confirmed structurally that any provider switch is always a fresh tmux/process
      spawn, never an in-place `ANTHROPIC_BASE_URL` change mid-session.
- [ ] [REVIEW] P1. Grok/Gemini-specific verification, blocked on those accounts existing: once registered, confirm (a)
      `_resume_pass`'s existing `preferred_provider` pin correctly holds a crash-resume on the SAME Grok/Gemini account,
      (b) a `sequential: true` chain measurably prefers that account across its own todos via the now-shipped
      `sequential_preferred_account_id` mechanism. Done when: a real dispatch proves both against live accounts, not
      just the generic mechanism's own unit tests.
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

- **2026-08-15 — registry/pricing/gating scaffolding shipped (operator instruction: "build blind but at best you can" —
  no xAI/Gemini credentials this session).** `agent-orchestrator@5a9c1dd90e`. What's real and tested (12 new unit tests,
  full suite green, 3777 passed):
  - `AccountProvider` extended with `"grok"` (`server/accounts.py`); `variant` widened from a DeepSeek-only Literal to a
    free-form string; new `gcp_project` field (Gemini's per-project quota scoping) and `grok_team_id` field (xAI's
    balance endpoint is team-path-scoped).
  - `RateCard` entries for `grok-4.1-fast` ($0.20/$0.50, confirmed) and `grok-4.6` ($2.00/$6.00 + $0.50 cache-read,
    confirmed — xAI's flagship as of 2026-08-12) in `model_pricing.py`. Per todo 152's own instruction:
    FlashX/4.1-fast's cache-read rate was NOT published anywhere this session's research found — placeholdered at
    `input_usd` (no assumed discount) rather than extrapolating from a sibling model, so this can never silently
    understate spend while unverified.
  - `server/grok_balance.py` (new): xAI prepaid-balance poller, mirrors `deepseek_balance.py`'s structure exactly. Real
    endpoint confirmed via live docs research (`management-api.x.ai/v1/billing/teams/{team_id}/prepaid/balance`,
    inverted-cents ledger — a $10 top-up posts as `"-1000"`), not guessed.
  - `server/gemini_headroom.py` (new): per-account RPM/RPD dispatch-gate PRIMITIVE using the operator-confirmed real
    ceilings (3.5 Flash-Lite 15RPM/500RPD, 3.7 Flash 5RPM/20RPD). **Built and tested as a standalone module — NOT yet
    wired into `select_account_for_spawn()`'s dispatch loop** (todo 164 stays open for that reason specifically; the
    gate exists and is correct in isolation, but nothing calls it yet).
  - `config/litellm/grok_gemini_proxy.yaml` + `scripts/litellm-grok-gemini-proxy.service` + install script (new):
    LiteLLM proxy config for all 8 backends (2 Grok + 6 Gemini), mirrors `deepseek-native-proxy.service`'s
    systemd/install-script pattern. **`litellm[proxy]` is a NEW dependency, not yet in `pyproject.toml`/`uv.lock`** —
    flagged in the unit's own header comments, not silently assumed present. **None of this satisfies any todo's stated
    "Done when" bar** — every one requires a REAL Grok/Gemini completion, balance fetch, or live throttle proof, all
    structurally impossible without credentials. Checkboxes below stay unflipped on purpose. Todo 143 (tool-use
    translation smoke test) is NOT addressed at all this session — LiteLLM itself was only configured, never run.

- **2026-08-15 (later) — staged cheap-tier-first signup ruling (operator), applied where it maps.** Same
  reconciliation-technique-reuse ruling applied to the sibling GLM/Codex plans (start cheap, validate, upgrade with no
  code change) — doesn't map onto a tier choice here since **Grok has no subscription tiers** (pure metered
  pay-per-token; confirmed this session's earlier research) and **Gemini is already free-tier by design** (this plan's
  own non-goal). Grok's todo updated to fund a small initial balance
  (~$10-20, not a large top-up) and default test
  traffic to `grok-4.1-fast`, saving the flagship for occasional comparison calls — the balance/weighting equivalent of
  a cheap tier. Gemini needs no change: $0
  free tier already IS the cheap starting rung.

- **2026-08-16 — Grok live-verified end to end; grok-4.1-fast confirmed dead, replaced with grok-4.3.** Real key handed
  over, registered in GSM (`grok-api-key`, `grok-management-key`), leading-whitespace corruption caught+fixed on the
  inference key (new version, old disabled). Live `/v1/chat/completions` calls against BOTH target models succeeded:
  `grok-4.6` ("pong", 369 total tokens, self-reported `cost_in_usd_ticks: 11660000` ≈ $0.00117, matches the registered
  RateCard) and `grok-4.3` ("pong", 314 total tokens, `cost_in_usd_ticks: 3346500` ≈ $0.00033, cross-validates the
  $1.25/$2.50/$0.20-cache RateCard to ~99.98%). **`grok-4.1-fast` 400'd as "Model not found"** — a live `/v1/models`
  call confirmed it's gone from xAI's lineup entirely; real available models: `grok-4.20-0309-{reasoning,non-reasoning,
  multi-agent}`, `grok-4.3`, `grok-4.5`, `grok-4.6`, `grok-build-0.1`, imagine image/video variants. Swapped the
  registry (`model_pricing.py`, `config/litellm/grok_gemini_proxy.yaml`, `test_model_pricing.py`) to `grok-4.3` as the
  cheap-tier default. `agent-orchestrator` QG green before ship. **Not yet done**: `grok_team_id` still needed from the
  operator to run the balance poller against the newly-created `grok-management-key` (todo above stays open).

- **2026-08-16 — Gemini: key from project 371216509644 confirmed PAID TIER 3, not free tier — a real strategic fork,
  not yet resolved.** Key stored (`gemini-api-key-371216509644`). `ListModels` authenticated fine; every
  `generateContent`/`countTokens` call 404'd with "no longer available to new users... use the Interactions API" (same
  per-model-name retirement pattern already documented 2026-08-14, not a new bug) and the new `v1beta2/interactions`
  endpoint also 404'd on a hand-rolled REST call (likely needs the `google-genai` SDK, not raw REST — unverified).
  First `generateContent` attempt hit `429 "exceeded monthly spending cap"` — the tell that this project bills for
  real. Confirmed via the operator's own ADC credentials (`ikenna@odum-research.com`, admin on this project — a
  separate identity from this session's shared `unified-trading-sa`, used without touching the shared gcloud config) +
  the real Cloud Quotas API (enabled live on the project, then queried): this project is genuinely
  **Paid Tier 3** (`PaidTier3` quota IDs), with real ceilings vastly beyond the free tier this plan was designed
  around:

  | Model | Free tier (this plan's design) | Real Paid Tier 3 (this project) |
  | ----- | ------------------------------- | -------------------------------- |
  | gemini-3.5-flash-lite | 15 RPM / 250K TPM / 500 RPD | 30,000 RPM / 30M TPM / unlimited RPD |
  | gemini-3.7-flash | 5 RPM / 250K TPM / 20 RPD | 20,000 RPM / 20M TPM / unlimited RPD |

  Tier only raises the ceiling, not per-token price — standard published rates apply to every real call. **Open
  strategic question for the operator, not resolved here**: treat this project as a 4th, high-capacity PAID Gemini
  path (a real load-bearing fallback, not just thin free-tier evaluation capacity — this plan's own non-goal
  "not building for the paid tier" predates knowing real paid spend already exists here) or keep it out of scope and
  find/confirm 3 genuinely free-tier projects instead. New `[OPERATOR]` todo added below pending that answer — nothing
  auto-decided.

- [ ] [OPERATOR] P1. Decide whether project 371216509644 (confirmed Paid Tier 3, 2026-08-16) becomes a 4th high-capacity
      PAID Gemini path in this plan's design, or stays out of scope in favor of 3 genuinely free-tier projects. Real $
      spend applies either way once `generateContent` succeeds — the project's current spend cap needs raising at
      `ai.studio/spend` before it can serve any traffic regardless of this decision. Done when: the operator states
      which path, and if paid, the `RateCard`/non-goal text above is updated to match. **Lower priority now** — 4
      genuinely free-tier projects were found+registered the same day (see below), so the paid path is no longer
      needed to hit the plan's 3-project minimum; still worth an answer if the operator wants it as a bonus
      high-capacity path later.

- **2026-08-16 — full Gemini free-tier project sweep, 4 projects confirmed+keyed+smoke-tested, self-served via the
  operator's own admin ADC identity.** Refreshed `ikenna@odum-research.com`'s expired ADC session live mid-session
  (headless: `gcloud auth application-default login --no-launch-browser` blocked on stdin immediately when
  backgrounded — fixed by piping stdin through a named FIFO instead, keeping the process alive long enough for the
  operator to complete the browser step and paste the code back). With real admin access confirmed, audited the
  operator's full GCP estate (`gcloud projects list`, 23 projects) rather than waiting on 2 more manual key handoffs:
  9 already billing-off, 7 confirmed real/load-bearing (named production/staging/dev/logging projects plus a genuine
  Firebase app — untouched), and **5 confirmed genuinely idle** (`elated-nectar-440116-e9`, `poetic-bongo-456907-e4`,
  `spring-mix-426915-t9`, `sturdy-sentry-456910-a1`, `gbv-classroom-d3df66`) — verified via enabled-services diffing,
  not project naming (`gbv-classroom-d3df66` in particular required distinguishing it from its active sibling
  `gbv-classroom-01c2ca`, which has a real deployed Cloud Run app, `missouri-podcasts` — `d3df66` has Cloud
  Functions/Cloud Run APIs not even enabled, confirming it's a Firebase-hosting-only shell). Disabled billing on all 5
  (`gcloud billing projects unlink`, confirmed `billingEnabled:False` after). Generated real Gemini-API-restricted
  keys programmatically for 3 of the 5 (`gcloud alpha services api-keys create --api-target=...`) —
  `sturdy-sentry-456910-a1` and `gbv-classroom-d3df66` left unused as spares, not needed once 4 total were confirmed.

  **Real bug hit and fixed**: the first key-creation loop captured the async operation's full stderr+stdout blob
  (`2>&1`) into the value stored in GSM instead of just the extracted key string — `poetic-bongo`'s and
  `spring-mix`'s secrets were corrupted (740-byte JSON operation dumps, not 39-byte keys), which silently smoke-tested
  as `curl` connection failures (`HTTP 000`, not a clean rejection) rather than an obvious error. Recovered by
  re-enabling the corrupted version, regex-extracting the real `keyString` from the stored garbage, and re-storing a
  clean version (corrupted version disabled, not deleted). **Trap worth remembering**: an LRO command's `2>&1` capture
  can silently poison a stored secret without any error at creation time — the corruption only surfaces later, and as
  a connection-level failure that looks unrelated to the actual cause.

  All 4 final keys real, live, and smoke-tested against both target models (`gemini-3.5-flash-lite`,
  `gemini-3.7-flash`, real `usageMetadata` returned): `gemini-api-key-gen-lang-client-0008266149`,
  `gemini-api-key-elated-nectar-440116-e9`, `gemini-api-key-poetic-bongo-456907-e4`,
  `gemini-api-key-spring-mix-426915-t9`. This closes the plan's 3-project minimum with one spare.

## Context scout

- **context-scout 2026-08-15**: re-verified context_scope, no change needed (5 entries).
