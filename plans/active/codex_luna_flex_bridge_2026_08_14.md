---
doc_type: plan
title: Codex/Luna bridge — ChatGPT Pro subscription as an Anthropic-compatible AO provider
summary:
  Bridge Claude Code's Anthropic Messages protocol to OpenAI's Codex App Server (JSON-RPC/SDK), authenticated via a
  $200/mo ChatGPT Pro subscription, so AO can dispatch sonnet-tier fallback work to Luna (GPT-5.6) while every
  skill/hook/CLAUDE.md stays untouched — the harness never knows it isn't talking to Claude.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, codex, luna, openai, model-routing, multi-provider, subscription-billing, bridge]
related:
  [
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
    /codex/06-coding-standards/model-tier-selection.md,
    agent-orchestrator/docs/omniroute_cli_setup_guide.md,
    agent-orchestrator/docs/deepseek_cli_setup_guide.md,
  ]
created: 2026-08-14
last_updated: 2026-08-14
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
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
    agent-orchestrator/server/codex_bridge_server.py,
    agent-orchestrator/server/accounts.py,
    agent-orchestrator/server/model_pricing.py,
    agent-orchestrator/server/deepseek_native_proxy_server.py,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /codex/06-coding-standards/model-tier-selection.md,
  ]
---

# Codex/Luna bridge — ChatGPT Pro subscription as an Anthropic-compatible AO provider

## Why

Operator decision (interactive session, 2026-08-14): add OpenAI's Luna (GPT-5.6) as a fourth sonnet-tier fallback
provider, but billed via a **$200/mo ChatGPT Pro subscription** (Codex entitlement) rather than metered API — OpenAI
does not expose that subscription as a generic Anthropic- or OpenAI-compatible REST endpoint; it's consumed through the
**Codex App Server / SDK** (stateful JSON-RPC thread/turn model, authenticated via `~/.codex/auth.json`). Standing
requirement, restated multiple times this session: Claude Code's harness — CLAUDE.md, skills, hooks, slash commands —
must not be reengineered for any new provider; every provider must present as if it's just another Claude account.
DeepSeek and GLM (see the sibling plan) achieve this because their vendors ship a native Anthropic-compatible endpoint.
**Codex has no such endpoint** — this plan's core deliverable is a bespoke local bridge that provides one.

**Ruled out this session**: xAI's SuperGrok+OpenCode subscription integration (a DIFFERENT open-source coding harness,
not an API facade — bridging into it would mean running a second, competing agent harness, which conflicts with the
"stays Claude Code" requirement) and the `omniroute` provider slot (self-hosted but the third-party `omniroute.online`
service itself is unconfirmed/undocumented scaffolding per `docs/omniroute_cli_setup_guide.md` — not used here).

**Real usage grounding (measured 2026-08-14, 7-day rolling AO-fleet window)**: DeepSeek alone carried 452 tasks / 26,783
turns / ~5.0B cache-read tokens over 7 days — a real, continuous fallback volume, not sporadic. Codex Pro's own bundled
Luna allowance (OpenAI's stated range: ~1,000-5,600 messages/5h + a separate weekly cap) is plausibly comparable in
order of magnitude if Luna absorbs a DeepSeek-like share of fallback traffic — but OpenAI states this as a wide range,
not a number to bank on, and AO's own routing split (how much of the fallback pool goes to Luna specifically, vs.
DeepSeek/GLM/Grok) is not yet decided. Treat the $200/mo bet as directionally reasonable, not proven — the plan includes
a real post-launch measurement checkpoint rather than trusting this estimate.

**Codex SSOTs this plan depends on** (read before touching the cited mechanism): the sibling
`deepseek_claude_blended_provider_routing_2026_07_28.md` plan owns `select_account_for_spawn()`, `AccountProvider`, the
`preferred_provider`/`_resume_pass` pinning mechanism, and `model_pricing.py`'s `RateCard` system — this plan REUSES
those, it does not reimplement them. `claude-cli-multi-account-headless-auth.md` for the `oauth_token_env_file` contract
every account assumes. `model-tier-selection.md` for the sonnet/opus/fable eligibility gate this provider must respect
identically to DeepSeek/GLM (opus/fable hard-pinned to Claude, never Codex).

## Non-goals

- Not building a general-purpose OpenAI-API translation layer — that's the sibling Grok/Gemini proxy plan's job. This
  plan is specifically the Codex App Server / subscription-auth bridge, a structurally different problem (stateful
  thread/turn protocol + ChatGPT session auth, not a stateless chat-completions REST call).
- Not touching the interactive Claude Code CLI/VS Code surfaces directly — the bridge is a backend service; how an
  interactive session might also use it is a separate, later decision.
- Not attempting to expose Codex's own subscription entitlement to a script/automation OUTSIDE Claude Code — scope is
  strictly "make Claude Code able to spawn a Luna-backed session," nothing broader.

## Design summary

A new local service (`codex_bridge_server.py`, mirroring `deepseek_native_proxy_server.py`'s standalone-FastAPI-process
shape) exposes `POST /v1/messages` in Anthropic Messages format. Internally it:

1. Translates the incoming Anthropic-format request (system prompt = CLAUDE.md + skill content, message history, `tools`
   schema) into a Codex SDK thread — either resuming an existing thread (multi-turn within one task) or creating a fresh
   one.
2. Drives the thread via the Codex App Server's JSON-RPC interface, authenticated through the ChatGPT-Pro-backed
   `~/.codex/auth.json` session (auto-refreshed by Codex itself, no OAuth handling needed in the bridge).
3. Translates Codex's turn/tool-execution events back into Anthropic-shape `tool_use`/`tool_result`/streaming events as
   they occur, and the final response into an Anthropic Messages response body.
4. Captures real token usage at the interception point (the bridge sees both sides of the exchange) for accurate billing
   — no trusting a self-reported number, same principle as every other new provider this session.

Registered as `accounts.json` provider `"codex"`, `oauth_token_env_file` pointing at an env file that sets
`ANTHROPIC_BASE_URL` to the bridge's local address (mirrors the exact shape of the ruled-out OmniRoute doc's env-file
template, minus the third-party dependency).

## Todos

- [ ] [OPERATOR] P1. Complete ChatGPT Pro ($200/mo) subscription signup and persist an authenticated
      `~/.codex/auth.json` session on the orchestrator VM (`planning`) — a human ChatGPT OAuth flow, cannot be automated
      by a worker. Done when: `~/.codex/auth.json` exists on the VM and a manual `codex` CLI smoke call succeeds against
      it.
- [ ] [OPERATOR] P1. Name which existing Claude seat(s) to shut down to offset the new $200/mo spend — genuine
      business/value judgment with no data-derivable answer (real seat list isn't visible from this checkout; the
      committed `accounts.mock.json` is example-only). Done when: the seat(s) are named and the corresponding
      `accounts.json` entries are removed/disabled.
- [ ] [INFRA] P0. Build `codex_bridge_server.py` — a standalone FastAPI process exposing `POST /v1/messages` (Anthropic
      Messages format), translating to/from the Codex App Server SDK's JSON-RPC thread/turn model, authenticated via
      `~/.codex/auth.json`. Structure mirrors `deepseek_native_proxy_server.py` (standalone process, not inline in the
      main orchestrator). Done when: a manual `curl -X POST /v1/messages` with a simple prompt returns a valid
      Anthropic-shape response sourced from a real Luna completion.
- [ ] [INFRA] P0. Translate system-prompt injection correctly — CLAUDE.md + skill content arriving as the Anthropic
      request's system block must reach Codex's own instructions channel unmodified, not dropped or truncated. Done
      when: a real request carrying a distinctive CLAUDE.md marker string is proven to influence the Codex-backed
      response (the marker is echoed/acted on), not just passed through blind.
- [ ] [INFRA] P0. Translate `tool_use`/`tool_result` round-tripping correctly — skills, hooks, and subagent tool calls
      depend on this working both directions (Claude Code issuing a tool call, the bridge translating it into whatever
      Codex's own tool-execution model expects, and the result translated back). Done when: a real multi-step
      tool-calling exchange (not a single-turn text response) completes correctly through the bridge.
- [ ] [REVIEW] P0. **Smoke-test gate before any real fleet traffic** (operator instruction, 2026-08-14): run an actual
      skill invocation and an actual tool call through the bridge, not just a "say hello" prompt — Codex's protocol is
      structurally more different from Anthropic's than OpenAI's/Gemini's chat-completions-style APIs are, so this is
      the highest-risk piece of the whole multi-provider effort. Done when: a dated Progress Log entry records a real
      skill (e.g. a slash-command invocation) and a real tool call (e.g. a file edit) both completing correctly through
      a Codex-backed session, verified by inspecting the actual result, not trusting the session's own claim.
- [ ] [INFRA] P1. Register `AccountProvider` value `"codex"` (extends the Literal the sibling DeepSeek/GLM plan owns).
      Deploy the bridge process on the orchestrator VM (or reachable from it) — same requirement the ruled-out OmniRoute
      doc flagged: it must run where workers actually spawn, not the operator's laptop. Done when: an `accounts.json`
      entry with `provider: "codex"` resolves to `status: healthy` via `/api/accounts`.
- [ ] [DATA] P1. Quota tracking reusing the SAME `five_hour_pct`/`weekly_pct` fields Claude already uses (Codex Pro's
      5h-rolling + separate weekly cap is the same shape) — calibrate the REAL ceiling via live measurement over the
      first operating week rather than trusting OpenAI's stated 1,000-5,600/5h range, and gate dispatch on it exactly
      like Claude's existing headroom exclusion (not just display). Done when: a measured real ceiling is recorded and
      an account nearing it is excluded from `select_account_for_spawn()`'s pick in a simulated test.
- [ ] [INFRA] P1. Accurate usage-capture — the bridge already sits inline on both sides of every exchange (unlike a
      passthrough proxy), so capture real token counts there directly rather than trusting any self-reported number.
      Done when: captured counts are cross-checked against the Codex/ChatGPT dashboard's own usage view for a real
      sample and found to agree within a stated tolerance.
- [x] [INFRA] P1. ✅ Add an explicit soft same-provider preference so a `sequential: true` plan's later todos prefer the
      SAME provider its earlier todos used (when healthy) rather than round-robining independently per-todo — the
      GENERAL mechanism, shipped in the sibling plan's `select_account_for_spawn()` (new
      `sequential_preferred_account_id` param). — `agent-orchestrator@7ae567cbb6`. Confirmed structurally (not just
      assumed) that any provider switch is always a fresh tmux/process spawn, never an in-place `ANTHROPIC_BASE_URL`
      change mid-session.
- [ ] [REVIEW] P1. Codex-specific verification, blocked on the account existing: once a Codex account is registered,
      confirm (a) a crash-resume onto a Codex-backed session stays on Codex via `_resume_pass`'s existing
      `preferred_provider` pin, (b) a `sequential: true` chain measurably prefers Codex across its own todos via the
      now-shipped `sequential_preferred_account_id` mechanism. Done when: a real dispatch proves both (a) and (b)
      against a live Codex account, not just the generic mechanism's own unit tests.
- [ ] [DATA] P2. Add an informational `model_pricing.py` entry for Luna (metered-API-equivalent rate, $0.20/$1.20 per 1M
      standalone — used for cost/value tracking against the subscription's flat fee, not real billing, same treatment as
      GLM's Coding Plan). Done when: `price_usage()` returns a value for the Luna model string.
- [ ] [REVIEW] P2. After ~2 weeks live, measure real Luna utilization against the tier's own ceiling and real completion
      quality vs. the Claude/DeepSeek baseline — confirms or corrects this session's directional estimate that the
      $200/mo bet pencils out given real fallback volume. Done when: a dated Progress Log entry with real
      messages-used-vs-ceiling and quality numbers lands.
- [ ] [INFRA] P2. Add streaming (SSE) support to `codex_bridge_server.py` — the 2026-08-15 blind-build shipped a
      non-streaming-only bridge (module docstring gap #3): functionally correct for Claude Code but a real UX regression
      vs. every other provider (pane goes silent for the whole turn instead of live-updating). Deliberately NOT
      attempted blind — DeepSeek's own native proxy needed a documented real engineering effort (including a fail-safe
      circuit breaker for mid-stream failures) to get right, and that can't be replicated without a live Codex session
      to test against. Done when: a real streaming turn through the bridge updates the Claude Code pane incrementally,
      not just at completion, verified against an actual live Codex session.

## Progress Log

- **2026-08-14 (interactive session)**: Plan authored from a same-session design conversation covering provider
  identification, billing-model pivot (metered API → ChatGPT Pro subscription bridge), OpenCode alternative investigated
  and ruled out, and real 7-day AO usage data pulled to ground the utilization estimate. No code written yet.

- **2026-08-14 (later, separate session) — Gemini auth findings, cross-reference only, unrelated to this plan's own
  ChatGPT-Pro-subscription auth model.** Recorded here since this plan is part of the same 2026-08-14 multi-provider
  onboarding family: a same-day session confirmed real Gemini auth/billing mechanics — `generateContent`'s "no longer
  available to new users" 404 is a per-retired-model-name problem, not an API-surface one (same error hit identically
  through classic REST, the new Interactions REST endpoint, and the SDK); and a project's billing can pass every
  config-level health check yet still have every paid call denied by Google's internal payment-dunning gate (confirmed
  live on the org's shared `central-element-323112` project). Full findings live in the sibling
  `/plans/active/grok_gemini_translation_proxy_2026_08_14.md` Progress Log, which owns Gemini onboarding for this plan
  family — not duplicated here.

- **2026-08-15 — `codex_bridge_server.py` scaffold shipped (operator instruction: "build blind but at best you can" — no
  `~/.codex/auth.json` access this session).** `agent-orchestrator@5a9c1dd90e`. What's real and tested: the standalone
  FastAPI process exists (`POST /v1/messages`, `GET /health`), request/response translation against the real
  `openai-codex` SDK surface (`Codex()`/`thread_start()`/`thread.run()`, confirmed via live docs research, not guessed),
  `AccountProvider` extended with `"codex"` (`server/accounts.py`), a Codex `RateCard` entry NOT yet added (todo below
  still open), and 12 new unit tests (request parsing, prompt-flattening, error handling, SDK-failure wrapping) — all
  green, full suite 3777 passed. **None of this session's shipped code satisfies any todo's stated "Done when" bar** —
  every one of them requires a REAL Codex completion/session, which is structurally impossible without live
  `~/.codex/auth.json` access. Checkboxes below stay unflipped on purpose; this entry records real progress without
  overclaiming it. Three gaps stated plainly in the module's own docstring (not discovered later, deliberately designed
  around given the blind-build constraint):
  1. **No incremental Codex thread reuse** — every request starts a fresh thread and replays the full flattened history,
     matching Anthropic's own per-call statelessness rather than guessing at a session-correlation heuristic (there's no
     stable session id in an Anthropic Messages request body to key one on). Forfeits Codex's native context caching; a
     documented inefficiency, not a silent one.
  2. **Tool-use translation is a structural stub** — `tool_use`/`tool_result` content blocks are rendered as a labelled
     text placeholder (`[tool_use: name input=...]`), NOT translated into whatever Codex's own tool-execution model
     expects. This is exactly the mandatory smoke-test gate's job to catch — do not skip it.
  3. **No streaming (SSE) support** — returns one non-streaming response. Functionally correct for Claude Code (slower
     pane updates, not a correctness gap), but a real engineering gap vs. DeepSeek's own native proxy. Also NOT done
     this session (genuinely blocked, not skipped): `model_pricing.py` Luna entry, real usage-capture wiring (a
     token-count placeholder exists, clearly marked never-to-be-trusted-for-billing), and the bridge is not deployed
     anywhere — it's a file in this repo, not a running service.

- **context-scout 2026-08-15**: refreshed context_scope (6 entries) — added `codex_bridge_server.py` (the bridge
  scaffold shipped earlier today, now the concrete build target) and
  `/codex/06-coding-standards/model-tier-selection.md` (the doc's own "Why" section already names this as a hard
  dependency — every provider decision here must respect the opus/fable-hard-pinned-to-Claude rule it defines); dropped
  `autospawn.py` (the shared routing mechanism it carries is already-shipped per this doc's own todo, lower-value than
  the two additions for the REMAINING open work) to stay within the 6-entry cap.
