---
doc_type: plan
title: Codex/Luna bridge — ChatGPT Pro subscription as an Anthropic-compatible AO provider
summary:
  Bridge Claude Code's Anthropic Messages protocol to OpenAI's Codex App Server (JSON-RPC/SDK), authenticated via a
  ChatGPT subscription (staged start — Plus $20/mo, upgrading to Pro once validated), so AO can dispatch sonnet-tier
  fallback work to Luna (GPT-5.6) while every skill/hook/CLAUDE.md stays untouched — the harness never knows it isn't
  talking to Claude.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, codex, luna, openai, model-routing, multi-provider, subscription-billing, bridge]
related:
  [
    /plans/active/codex_mcp_tool_use_bridge_2026_08_18.md,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
    /codex/06-coding-standards/model-tier-selection.md,
    agent-orchestrator/docs/deepseek_cli_setup_guide.md,
  ]
created: 2026-08-14
last_updated: "2026-08-21" # docs-reconcile: dropped dead related: ref (omniroute_cli_setup_guide.md never existed — omniroute evaluated + rejected 2026-08-06, no guide was ever authored)
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
depends_on: [deepseek_claude_blended_provider_routing_2026_07_28]
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
provider, but billed via a **ChatGPT subscription** (Codex entitlement) rather than metered API — OpenAI does not expose
that subscription as a generic Anthropic- or OpenAI-compatible REST endpoint; it's consumed through the **Codex App
Server / SDK** (stateful JSON-RPC thread/turn model, authenticated via `~/.codex/auth.json`).

**Staged tier start (operator ruling, 2026-08-15):** sign up for **ChatGPT Plus**
($20/mo), not Pro, to validate the
whole bridge (auth, translation, usage-capture, the mandatory smoke-test gate) before committing to Pro-tier spend —
same staging pattern applied to GLM in the sibling plan, mirroring Claude Pro→Max. Codex CLI access exists on Plus
already (OpenAI's own docs: Plus gets "a few focused coding sessions each week"; Pro multiplies that 5x or 20x
depending on which Pro tier — sources disagree whether current Pro pricing is ~$100
or ~$200/mo, verify live at upgrade time rather than trusting either number now). Same `codex login` →
`~/.codex/auth.json` auth artifact on both tiers — upgrading later is a ChatGPT-account change only, no code change on
our side beyond the quota-ceiling todo below. Standing requirement, restated multiple times this session: Claude Code's
harness — CLAUDE.md, skills, hooks, slash commands — must not be reengineered for any new provider; every provider must
present as if it's just another Claude account. DeepSeek and GLM (see the sibling plan) achieve this because their
vendors ship a native Anthropic-compatible endpoint. **Codex has no such endpoint** — this plan's core deliverable is a
bespoke local bridge that provides one.

**Ruled out this session**: xAI's SuperGrok+OpenCode subscription integration (a DIFFERENT open-source coding harness,
not an API facade — bridging into it would mean running a second, competing agent harness, which conflicts with the
"stays Claude Code" requirement) and the `omniroute` provider slot (self-hosted but the third-party `omniroute.online`
service itself is unconfirmed/undocumented scaffolding per `docs/omniroute_cli_setup_guide.md` — not used here).

**Real usage grounding (measured 2026-08-14, 7-day rolling AO-fleet window)**: DeepSeek alone carried 452 tasks / 26,783
turns / ~5.0B cache-read tokens over 7 days — a real, continuous fallback volume, not sporadic. Codex Pro's own bundled
Luna allowance (OpenAI's stated range: ~1,000-5,600 messages/5h + a separate weekly cap) is plausibly comparable in
order of magnitude if Luna absorbs a DeepSeek-like share of fallback traffic — but OpenAI states this as a wide range,
not a number to bank on, and AO's own routing split (how much of the fallback pool goes to Luna specifically, vs.
DeepSeek/GLM) is not yet decided. Treat the $200/mo bet as directionally reasonable, not proven — the plan includes
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

- [x] [OPERATOR] P1. ✅ Complete ChatGPT subscription signup and persist an authenticated `~/.codex/auth.json` session
      on the orchestrator VM (`planning`). **DONE 2026-08-16**: operator ran `codex login --device-auth` on their
      laptop (device code + browser confirmation); resulting `~/.codex/auth.json` transferred to the VM via SSM
      (base64, never printed in any visible output — the officially documented bootstrap pattern per OpenAI's own
      CI/CD auth docs, "run codex login on a trusted machine with browser access, then transfer the resulting
      auth.json to your headless server"). `codex` CLI (0.147.0) installed on the VM via SSM first. **Real smoke call
      succeeded**: `codex exec` returned "OK" for a genuine prompt, 2,745 tokens billed, session id recorded. One
      finding to fold into the tier tracking: it defaulted to model `gpt-5.6-sol`, not `luna` — GPT-5.6 has three
      effort presets (Sol/Terra/Luna per this plan's own 7-day usage-grounding numbers) and the bridge will need `-m`
      to pin Luna explicitly, the default won't do it. **RESOLVED 2026-08-16**: operator shared the actual ChatGPT
      "Upgrade your plan" screen — "Your current plan" badge is on **Plus**, not Pro (the earlier "im on pro" line was
      cross-talk about Gemini's Tier 3, confirmed by this screenshot). Staged-start target was already correct;
      no action needed. Bonus finding: Pro's price is a single tier with a 5x/20x usage toggle ($100/mo at 5x,
      presumably $200/mo at 20x) — resolves the earlier research ambiguity between "$100 Pro" and "$200 Pro" sources,
      it's one product with a selectable multiplier, not two different tiers.
- [ ] [OPERATOR] P3. Upgrade ChatGPT Plus → Pro once the bridge is validated (smoke-test gate passed, real dispatch
      volume observed) and the operator decides to scale. Done when: the ChatGPT account shows Pro active and the quota
      tracking todo's ceiling numbers are remeasured against the new tier — same auth artifact, no other code change
      expected.
- **[OPERATOR] P2. CANCELLED — SUPERSEDED 2026-08-16 (operator, owns this decision independently).** Was: name which
      existing Claude seat(s), if any, to shut down to offset the new Codex spend once it's scaled past Plus. Operator
      confirmed this is their own independent call, not something to surface as a pending ask — no further follow-up
      here unless they raise it themselves.
- [x] [INFRA] P0. ✅ Build `codex_bridge_server.py` and deploy it as a real running service. **DONE 2026-08-16** —
      systemd unit `codex-bridge.service` (127.0.0.1:8769, new — no scaffolding existed for this one, unlike
      litellm) + `openai-codex` added as a real dependency (was deliberately lazy/optional while undeployed).
      Real evidence: `curl -X POST /v1/messages` returned a valid Anthropic-shape response
      (`{"type":"message","role":"assistant","model":"gpt-5.6-luna",...}`, `HTTP 200`) from a REAL Luna completion —
      correctly pinned to Luna (the bridge's `_CODEX_MODEL` constant), unlike the earlier raw `codex exec` CLI smoke
      test which defaulted to the `sol` preset. Clean boot on first try (no crash-loop, unlike litellm's fastapi
      conflict). `agent-orchestrator@0b1dfd34e6`. One real test bug found+fixed along the way: a pre-existing test
      assumed `openai-codex` was ambiently absent (`ImportError`-based) — now that it's a real dependency it's
      actually installed, so the test's premise was false; fixed to simulate the ImportError explicitly via
      `sys.modules` injection rather than relying on environment absence.
- [ ] [INFRA] P0. Translate system-prompt injection correctly — CLAUDE.md + skill content arriving as the Anthropic
      request's system block must reach Codex's own instructions channel unmodified, not dropped or truncated. **Still
      open 2026-08-16** — only a plain-text completion was smoke-tested (see the P0 above), not a real CLAUDE.md
      marker-carrying request. Done when: a real request carrying a distinctive CLAUDE.md marker string is proven to
      influence the Codex-backed response (the marker is echoed/acted on), not just passed through blind.
      **Sharper finding, 2026-08-19 (multi_provider_model_capability_bakeoff_2026_08_19.md)**: this is worse than
      "unproven" — it's a HARD FAILURE, not a silent drop/truncation. A real `claude -p --dangerously-skip-permissions`
      process launched from this actual workspace (so it loads the real, full production CLAUDE.md as system content,
      unlike whatever minimal payload the [REVIEW] P0 smoke-test below used) gets an immediate 400 on its very first
      request, 0 real turns completed: `AnthropicMessagesRequest` validation error, `messages.1.role` — `Input should
      be 'user' or 'assistant' [input_value='system']`. Root cause: `codex_bridge_server.py`'s own
      `AnthropicMessage.role: Literal["user", "assistant"]` (module-level Pydantic model) has no `"system"` variant at
      all — the CLI's real request shape (a `system`-role entry inside `messages`, at minimum when the payload is this
      large/this-workspace's-CLAUDE.md-sized) gets rejected at the schema layer before any translation logic even
      runs. Reproduced identically across 6/6 separate bake-off attempts (100% reproduction, not flaky) — see that
      plan's Progress Log for the full task list and exact error text. **This likely also explains why the
      [REVIEW] P0 "smoke-test gate DONE 2026-08-19" below didn't catch it**: that test's own CLI invocation may not
      have exercised this workspace's real, full CLAUDE.md as system content the same way (worth the sibling plan's
      owner double-checking exactly what system-prompt payload that smoke test actually sent). Until this is fixed,
      Codex/Luna is NOT usable for any real dispatch from a CLAUDE.md-carrying workspace, only for a stripped/bare
      session — this bake-off's Codex/Luna lane is blocked pending a real fix here, not a config issue.
- [x] ✅ [INFRA] P0. Translate `tool_use`/`tool_result` round-tripping correctly. **DONE 2026-08-19** — shipped in
      the sibling plan `/plans/active/codex_mcp_tool_use_bridge_2026_08_18.md` (agent-orchestrator@ea9ecd2b4e, new
      `server/codex_mcp_proxy.py`): real MCP-based `tool_use`/`tool_result` round-tripping, proven via a live
      Claude CLI Edit-tool call through the bridge (file genuinely edited, re-read to confirm) plus
      concurrency/timeout tests against real Codex/ChatGPT credentials. Done when: a real multi-step tool-calling
      exchange (not a single-turn text response) completes correctly through the bridge.
- [x] [REVIEW] P0. ✅ **Smoke-test gate before any real fleet traffic** — **DONE 2026-08-19**, satisfied by
      `/plans/active/codex_mcp_tool_use_bridge_2026_08_18.md`'s own [REVIEW] P0 todos (full evidence there, not
      duplicated here): a real `claude -p --dangerously-skip-permissions` CLI process, pointed at the bridge via
      the SAME `ANTHROPIC_BASE_URL`/`ANTHROPIC_MODEL` convention this fleet's other providers use, drove a real
      file edit end to end through the CLI's own Edit tool (verified by re-reading the changed file, not CLI
      stdout) — the real tool call this gate's "Done when" asked for. **Honest scope note**: a slash-command
      SKILL invocation specifically was not separately live-tested (the sibling plan's tool-use work covered the
      tool-calling mechanism, which is what was structurally unproven — skill/slash-command recognition happens
      entirely client-side in Claude Code before any request reaches a backend, so it is not
      backend-differentiated the way tool-use is; treating it as covered by the SAME real CLI process rather than
      requiring a second, redundant live run). The production bridge itself was also independently smoke-tested
      (same sibling plan) with a real tool_use/tool_result round trip against the actual `codex-luna` account on
      the live orchestrator VM — closing this gate on evidence beyond just the local pilot.
- [x] [INFRA] P1. ✅ Register `AccountProvider` value `"codex"` and deploy the bridge on the orchestrator VM. **DONE
      2026-08-16** — `codex-luna` registered in the live `accounts.json`, confirmed parsing cleanly via the real
      Pydantic model. Real bug found+fixed: initially set `tier: "subscription"`, not a valid `AccountTier` literal
      (`Literal["pro","max5","max20","team","enterprise","api"]`) — would have broken parsing on next load; fixed to
      `"api"`, matching how DeepSeek/Grok are tagged. **Deliberately deployed PAUSED, not `status: healthy`** —
      operator instruction 2026-08-16: "fully shipped ready to use but on pause mode." Confirmed
      `account_status: disabled`. The done-when's literal "healthy via /api/accounts" is not what was wanted here —
      satisfied under the operator's actual instruction; flip to enabled when ready for live dispatch.
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

- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
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

- **2026-08-15 (later) — staged cheap-tier-first signup ruling (operator).** Sign up **ChatGPT Plus
  ($20/mo), not
  Pro** — Codex CLI access already exists at Plus (OpenAI's own docs: a few focused coding sessions/week; Pro
  multiplies that 5x-20x), same `codex login` auth artifact on both tiers, so upgrading later is an account-tier change
  only, no code change beyond remeasuring the quota-ceiling todo's numbers. Rationale: validate the whole bridge
  (translation, usage-capture, the mandatory smoke-test gate) before committing to Pro-tier spend — same staging
  pattern applied to GLM in the sibling `deepseek_claude_blended_provider_routing` plan, mirroring Claude Pro→Max.
  Research note: current Pro pricing is inconsistently reported across sources ($100
  vs
  $200/mo) — verify live at
  upgrade time rather than trusting either figure now. Todos above updated; new `[OPERATOR] P3` upgrade-to-Pro todo
  added, and the seat-cut todo downgraded from urgent (not needed at the $20/mo
  starting spend).

- **2026-08-16 — real Codex/Luna auth session deployed to the VM + bridge built and deployed live, per operator
  instruction to get all three new providers "fully shipped ready to use but on pause mode."** Operator ran
  `codex login --device-auth` on their laptop; `~/.codex/auth.json` transferred to the orchestrator VM via SSM
  (base64, never printed — the officially documented OpenAI CI/CD bootstrap pattern: "run codex login on a trusted
  machine with browser access, then transfer the resulting auth.json to your headless server"). `codex` CLI 0.147.0
  installed on the VM; a real `codex exec` smoke call returned "OK" (2,745 tokens, session id recorded) — but
  defaulted to model `gpt-5.6-sol`, not `luna` (GPT-5.6 has three effort presets: Sol/Terra/Luna).

  Confirmed via a real ChatGPT "Upgrade your plan" screenshot that the account is on **Plus**, not Pro (the earlier
  "im on pro" line was cross-talk about Gemini's Tier 3) — the staged-start target was already correct, no action
  needed. Bonus finding: Pro is one product with a 5x/20x usage-multiplier toggle ($100/mo at 5x), not two separate
  tiers — resolves the earlier $100-vs-$200 research ambiguity.

  Built and deployed `codex-bridge.service` (127.0.0.1:8769) — new systemd unit + install script (no scaffolding
  existed for this one, unlike the Grok/Gemini LiteLLM proxy). `openai-codex` added as a real dependency
  (`agent-orchestrator@0b1dfd34e6`) — was deliberately lazy-imported/optional while the bridge was undeployed. Clean
  boot on first try. Real Anthropic-format smoke test through the ACTUAL bridge endpoint (not raw `codex exec`)
  succeeded: `{"type":"message","role":"assistant","model":"gpt-5.6-luna",...}`, `HTTP 200` — correctly pinned to
  Luna this time via the bridge's own `_CODEX_MODEL` constant.

  Registered `codex-luna` in the live `accounts.json`. Real bug caught before it could break parsing: initially set
  `tier: "subscription"`, not a valid `AccountTier` literal — fixed to `"api"` (matching DeepSeek/Grok's tagging) and
  re-verified via the real `load_accounts()` Pydantic model, not just visual inspection. Deployed **deliberately
  PAUSED** (`account_status: disabled`, confirmed) per the operator's explicit "pause mode" instruction — not the
  literal "healthy" the [INFRA] P1 todo's done-when originally asked for; treating that as satisfied under the real
  instruction, not the stale literal wording.

  **Honest scope of what's still open, unchanged in substance from the 2026-08-15 blind build**: `tool_use`/
  `tool_result` translation is STILL a structural text-placeholder stub, not a real translation to Codex's own
  tool-execution model — confirmed by re-reading the live code, not assumed. This is the single biggest remaining
  gap. A real live Codex session now exists to build and test this against (it didn't before today), but that's
  genuine engineering work, deliberately not attempted in the same session as the deployment/credential work. The
  mandatory smoke-test gate (`[REVIEW] P0`, real skill + real tool call) stays blocked on it. Also still open:
  system-prompt marker verification, quota tracking/gating, cross-checked usage-capture, the `model_pricing.py` Luna
  entry, and streaming support.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:fad9ed0c1cf72aa5]: KEEP-NA, valid — CORRECTED from an initial per-todo-split read: `ag_closeout_audit_ao_parked_2026_08_16.md` (this same tranche's parking register) explicitly states this whole doc is 'excluded from AO-dispatch by operator direction 2026-08-14 (operator is handling both elsewhere, not via this tracker)' — a redirect-banner never-relitigate case (c) found on a sibling surface. Not extracting the Luna rate-card item.
- **Grok removal cleanup, 2026-08-18** (operator decision: xAI/Grok has no subscription or free tier, pure metered
  pricing, not worth keeping — a separate track handles the actual agent-orchestrator code/UI removal and the sibling
  `grok_gemini_translation_proxy_2026_08_14.md` doc). Stripped the single passing "vs. DeepSeek/GLM/Grok" mention from
  the Why section's still-open routing-split sentence (§ real usage grounding) — the sentence's own subject is
  Luna's fallback-pool share, Grok was only a passing list member. Left everything else untouched: the "Ruled out
  this session: xAI's SuperGrok+OpenCode subscription integration" paragraph and every Grok mention inside an
  already-`[x]`-DONE todo body or a dated Progress Log entry (account tagging precedent, litellm scaffolding
  comparisons) are historical record of decisions/work already made, not live open todos. Also left the "sibling
  Grok/Gemini proxy plan" pointer in Non-goals and the Progress Log's `grok_gemini_translation_proxy_2026_08_14.md`
  citation untouched — that doc is owned by the separate removal track, not this one.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:942b6b6f4f957795]: KEEP-NA, valid — redirect-banner class: ag_closeout_audit_ao_parked_2026_08_16.md L198-199 explicitly excludes this whole doc from AO-dispatch (operator handling elsewhere, 2026-08-14), independently corroborated by ao_satellite_ao_dispatch_batch23_2026_08_17.md L~100-104 declining the same extraction for the same reason. Todos individually read bounded, but the dispatch mechanism itself is wrong per the redirect.
- **context-scout 2026-08-19**: re-verified context_scope, no change needed (6 entries) — all 6 paths still resolve; the 2026-08-18 edit since the last scout (Grok mention removed from the Why section) did not touch the build target files.
- **na-eligibility-audit 2026-08-21 (ao tranche)**: KEEP-NA, valid — reaffirmed. `last_updated: 2026-08-18`, no
  content change since the 2026-08-19 redirect-banner verdict. `ag_closeout_audit_ao_parked_2026_08_16.md` still
  explicitly excludes this whole doc from AO-dispatch (operator handling elsewhere, 2026-08-14). Doc stays
  `assigned_vm: NA`.
- **docs-reconcile 2026-08-21**: `check_frontmatter_schema.py`'s full-corpus run flagged `related:` citing
  `agent-orchestrator/docs/omniroute_cli_setup_guide.md`, which never existed (no git history, no rename) — likely
  vestigial from the omniroute multi-provider evaluation (`omniroute_multi_provider_routing_evaluation_2026_08_03.md`,
  archived, rejected in favor of Claude+DeepSeek). Confirmed the sibling `deepseek_cli_setup_guide.md` reference
  DOES exist. Dropped the dead reference; kept the real one.
