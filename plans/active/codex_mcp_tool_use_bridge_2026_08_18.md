---
doc_type: plan
title: Codex/Luna real tool-use via MCP bridge
summary:
  Build real tool_use/tool_result support for the Codex/Luna bridge — currently a text-only stub — by routing
  through a per-request MCP server, proven viable by a real prototype (2026-08-18). The remaining work is a
  pause/resume proxy plus thread continuation across stateless Anthropic-format HTTP calls, then shipping to the
  live orchestrator.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, codex, luna, mcp, tool-use, model-routing, multi-provider]
related:
  [
    /plans/active/codex_luna_flex_bridge_2026_08_14.md,
    /plans/active/kimi_gemma_provider_onboarding_2026_08_16.md,
    /codex/15-runbooks/agent-orchestrator-local-pilot-isolation-runbook.md,
  ]
created: "2026-08-18"
last_updated: 2026-08-18
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
assigned_role: infra
effort: high
drift_direction: advance-code
depends_on: [codex_luna_flex_bridge_2026_08_14]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
context_scope:
  [
    agent-orchestrator/server/codex_bridge_server.py,
    agent-orchestrator/.venv/lib/python3.13/site-packages/openai_codex,
    /codex/15-runbooks/agent-orchestrator-local-pilot-isolation-runbook.md,
  ]
---

# Codex/Luna real tool-use via MCP bridge

## Why

`codex_luna_flex_bridge_2026_08_14.md`'s own module docstring in `server/codex_bridge_server.py` already documents
the gap: `_translate_codex_result_to_anthropic` returns text-only, no `tool_use` blocks — real tool calls through
the bridge silently degrade to a text explanation instead of executing. Verified directly this session (isolated
local pilot, `codex-bridge` on port 18769, real ChatGPT credentials): a plain-text request succeeds; a real
tool-call request returns `stop_reason: "end_turn"` (never `"tool_use"`) with the model itself saying it can't
call the tool.

A same-session investigation (2026-08-18) initially treated this as possibly architecturally unbuildable — the
`openai_codex` SDK's `ThreadStartParams` (the real per-conversation config class, `client.py`/`generated/v2_all.py`)
has no concept of inline, per-request custom tool schemas the way Anthropic's `tool_use` works. But a real
prototype proved the actual mechanism: Codex DOES support MCP (Model Context Protocol) tool servers, and — the
open question — **dynamic, per-thread MCP registration works**, not just a static `~/.codex/config.toml` write.

**Prototype evidence (2026-08-18, isolated pilot only, nothing touched production)**:

- `Codex.thread_start(config={"mcp_servers": {...}})` — a raw-dict passthrough on `ThreadStartParams.config` —
  registers and launches an MCP server for that ONE thread only. Proven against a `CODEX_HOME` whose
  `config.toml` did not exist at all before the run (confirmed via `cat` failing) — zero static configuration
  required.
- Three real Codex threads exercised a hand-rolled stdio `get_weather` MCP tool: static registration (thread
  `01a016cb-94fe-7780-b993-ab49668a4f77`), dynamic registration against an empty `CODEX_HOME` (thread
  `01a016cc-206a-7780-9826-f0b37fb5974d`), and a dynamic run with an artificially slow (20s) tool to probe
  timeout risk (thread `01a016cd-73e9-76e1-ac98-ba3d5be94bda`, `mcpToolCall.durationMs: 21227`, no server-side
  kill). All three round-tripped correctly — real `mcpToolCall` item with `server`/`tool`/`arguments`/`result`,
  cross-verified against the MCP server's own independent log carrying Codex's `x-codex-turn-metadata`
  (matching `thread_id`/`turn_id`).
- **The real remaining gap**: Codex's MCP `tools/call` is SYNCHRONOUS — the turn blocks until the tool returns,
  inside one call. Claude Code's actual tool-use model is ASYNCHRONOUS across two separate, stateless
  `/v1/messages` HTTP calls — the CLI gets back `tool_use`, executes the tool itself locally (Bash/Edit/Read,
  with real approval flow), then sends `tool_result` back in a LATER, separate request. To bridge these, the
  per-request MCP server's `tools/call` handler must NOT execute anything — it must hold the Codex turn open
  while the bridge's HTTP layer returns `stop_reason: tool_use` immediately, then correlate a later stateless
  `tool_result` HTTP call back to that specific pending MCP call and thread. This is the SAME problem as the
  bridge's already-documented "no incremental thread reuse" gap — solving tool-use correctly requires solving
  thread continuation too; they are one problem, not two.

**Operator directive (2026-08-18)**: build this for real (not just prove the mechanism), and deploy it to the
live orchestrator, not just the local pilot — "make sure you also do it on the agent orchestrator." Realistic
scope per the prototype: 3-5 focused engineering days for a correct first version, not a quick patch.

## Non-goals

- Not touching Gemma/Gemini/GLM/Kimi — this plan is Codex/Luna-scoped only.
- Not attempting a general-purpose MCP bridge for arbitrary future providers — scoped to what Codex actually
  needs.
- Not unpausing the production `codex-luna` account (`account_status: disabled`) until real end-to-end
  validation passes (see the last todo) — this is a real production-dispatch-affecting flip, gated on proof, not
  assumed safe on landing the code.

## Todos

- [x] [INFRA] P0. ✅ Design the pause/resume MCP proxy — **DONE 2026-08-19**, `agent-orchestrator/server/codex_mcp_proxy.py`
      (new module, ~330 lines) module docstring names the concrete mechanism: a per-`ThreadSession`
      `asyncio.Queue` (`ToolCallPaused`/`TurnFinished` events) decouples "a tool call arrived" from "an HTTP
      handler is waiting"; the MCP `tools/call` handler mints a `tool_use_id`, registers an `asyncio.Future` for
      it, publishes the pause event, then itself `await`s that future — THAT await is what holds Codex's own
      HTTP request open. A second, stateless `/v1/messages` call locates the pending call via `tool_use_id`
      itself (bridge-minted, round-tripped verbatim by Claude Code's own protocol) through a process-global
      `dict[tool_use_id, ThreadSession]` (`ThreadSessionRegistry`). Design switched from the prototype's stdio
      MCP relay to a **Streamable HTTP** MCP server mounted in the SAME FastAPI process (`codex mcp add --url`
      confirmed a real, first-class Codex transport) — no subprocess relay needed, single-uvicorn-worker deploy
      makes an in-process dict a correct shared store.
- [x] [INFRA] P0. ✅ Implement thread/session continuation — **DONE 2026-08-19**, real 2-turn HTTP exchange proven
      against LIVE Codex/ChatGPT credentials (isolated local pilot, no VM touched): turn 1 (tools declared) →
      real `stop_reason: "tool_use"`; turn 2 (`tool_result`) → real final text genuinely reflecting the injected
      tool content. **thread_id logging evidence**: `codex_bridge: tool-enabled turn driving
      thread_id=01a018c5-d4e6-7821-b033-8d44426130ad (session=ef0872470aa84b499e2c430c19e3ba90)` — same thread_id
      confirmed live (directly read off `ThreadSessionRegistry`) both immediately after turn 1's pause and
      structurally through to turn 2's completion (one persistent background task drives the whole thread's
      life, see below). `tool_use_id` used as the correlation key, not an invented session id, exactly per this
      todo's own "reuse whatever identity the protocol provides" bar.
- [x] [INFRA] P0. ✅ Implement the translation — **DONE 2026-08-19**, `codex_mcp_proxy.py` +
      `codex_bridge_server.py` (`_extract_tool_results`, `translate_tool_call_paused_to_anthropic`,
      `_drive_codex_turn`). Anthropic `tools` → real MCP `Tool` definitions (`input_schema` maps 1:1, Anthropic's
      own field name already matches MCP's); a paused `tools/call` → immediate `stop_reason: "tool_use"` with
      real `id`/`name`/`input`; `tool_result` → resolves the pending call (`is_error` propagated through to
      MCP's own `CallToolResult.is_error`, not silently dropped); turn completion → real final Anthropic text.
      The prototype's stdio scratch files were gone as expected (re-derived, not assumed) — SUPERSEDED by the
      Streamable HTTP design above, not reused verbatim.
- [x] [REVIEW] P0. ✅ Real end-to-end validation against the ACTUAL Claude Code CLI — **DONE 2026-08-19**. A real
      `claude -p --dangerously-skip-permissions` process, `ANTHROPIC_BASE_URL=http://127.0.0.1:8769` +
      `ANTHROPIC_MODEL=gpt-5.6-luna` (mirrors the exact `~/.claude-accounts/*.env` convention every other
      provider uses), run against an isolated scratch directory containing `status.txt` ("The status is
      PLACEHOLDER for now."), prompted to replace PLACEHOLDER with DONE via the Edit tool. **Measured result**:
      `status.txt` now reads "The status is DONE for now." — the CLI's own real Edit tool genuinely executed
      through this bridge (not a synthetic test tool), confirmed by re-reading the file after the process exited,
      not by trusting CLI stdout. Server log showed the real MCP handshake (`initialize`/`tools/list`/`tools/call`
      round trips across TWO separate Codex threads — no incremental reuse, as documented) and one real streaming
      attempt (`?beta=true`) that correctly got this bridge's honest `501` and the CLI transparently fell back to
      non-streaming — real evidence the documented streaming gap doesn't break the CLI, just costs one wasted
      round trip per turn (a candidate for the still-open streaming-support todo in
      `codex_luna_flex_bridge_2026_08_14.md`, not fixed here — out of this plan's scope).
- [ ] [REVIEW] P1. Characterize concurrency + timeout behavior for real: multiple simultaneous in-flight tool
      calls on the SAME bridge process, and Codex's own `tool_timeout_sec` MCP config (defaults to null per the
      prototype, unconfirmed real behavior) against a genuinely slow tool (a long-running Bash command, not the
      20s synthetic sleep already tested). Done when: a documented real ceiling (or confirmed "no ceiling
      observed up to N seconds") exists, not assumed from the prototype's one 20s data point.
- [x] [SCRIPT] P1. ✅ `bash scripts/quality-gates.sh` green — **DONE 2026-08-19**: `✅ agent-orchestrator quality
      gate PASSED` (ruff lint/format, basedpyright 0 errors, 4196 pytest passed/8 skipped, pip-audit clean,
      dashboard tsc+vitest green). Two real basedpyright errors and 2 unformatted files caught and fixed first
      (see Progress Log): a redundant `isinstance` in `_stringify_tool_result_content`, and `_mcp_asgi_app`
      needing Starlette's real `Scope`/`Receive`/`Send` types instead of a narrower `dict[str, Any]`. No
      regression on the plain-text path — its own existing 12 tests still pass unchanged.
- [x] [SCRIPT] P0. ✅ Shipped via quickmerge — **DONE 2026-08-19**, `agent-orchestrator@ea9ecd2b4e`, landed on
      `live-defi-rollout` (this repo's `promotion_model=ldr_terminal` — LDR IS the deploy target, nothing further
      to promote). Files: `pyproject.toml`, `uv.lock`, `server/codex_bridge_server.py`,
      `server/codex_mcp_proxy.py` (new), `tests/test_codex_bridge_server.py`, `tests/test_codex_mcp_proxy.py`
      (new).
- [ ] [INFRA] P0. Deploy to the live orchestrator VM and verify — restart `codex-bridge.service` (the gitignored
      `accounts.json`/systemd-config gotcha means `ao-self-pull.sh`'s "restart on HEAD move" does NOT cover this
      automatically per the Kimi/Gemma onboarding plan's own documented finding; a manual
      `systemctl restart codex-bridge` is required), then re-run the same real tool-call smoke test directly
      against the production bridge (127.0.0.1:8769 on the VM). Done when: a dated Progress Log entry records the
      real production response, not just the local pilot's.
- [ ] [REVIEW] P1. Once the production smoke test passes, unpause `codex-luna` (`POST
      /api/accounts/codex-luna/enable`, the real `enable_account_endpoint`) — flip only after the above todo's
      evidence exists, not on landing the code. Update `codex_luna_flex_bridge_2026_08_14.md`'s own still-open
      `[REVIEW] P0. Smoke-test gate before any real fleet traffic` todo to reference this plan's evidence and
      close it.
- [ ] [DOC] P2. Once every todo above is done, run this plan through the standard 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — this is a LOCAL/human plan
      (`assigned_vm: NA`), so it is never auto-archived by AO tooling.

## Progress Log

- **2026-08-18**: Plan authored following a real prototype (background agent, isolated local pilot) that proved
  dynamic per-thread MCP registration works and identified the real remaining gap (sync MCP vs. async
  Anthropic-protocol tool-use). Operator chose: human plan (`assigned_vm: NA`), not AO-dispatched — the operator
  will hand this to a specific agent/session directly rather than letting AO's backlog auto-pick it up.

- **2026-08-19 — first 4 todos completed with real, live evidence (isolated local pilot, real ChatGPT
  credentials via `~/.codex/auth.json`, nothing touched on the VM).** Design + implementation shipped as a new
  `agent-orchestrator/server/codex_mcp_proxy.py` module (~330 lines) plus a rewritten `codex_bridge_server.py`
  (`_extract_tool_results`, `_drive_codex_turn`, `translate_tool_call_paused_to_anthropic`) and a new
  `mcp>=1.0.0` dependency (official MCP Python SDK — its `StreamableHTTPSessionManager` mounted per-session in
  the same FastAPI process, chosen over hand-rolling the Streamable HTTP wire protocol). 24 new/updated unit
  tests (12 pre-existing + 7 in a new `test_codex_mcp_proxy.py` + 5 new route-handler pause/resume tests in
  `test_codex_bridge_server.py`), all monkeypatching at the SDK/MCP boundary per this file's existing convention.

  **Two real bugs found and fixed via live validation, not by inspection:**
  1. `_drive_codex_turn` was forwarding the caller's `req.model` (an account-routing alias like `"luna"`) straight
     into Codex's own `thread_start(model=...)` instead of the hardcoded `_CODEX_MODEL` constant
     (`"gpt-5.6-luna"`) `run_codex_turn` already uses correctly — produced a real, live `400
     invalid_request_error: "the 'luna' model is not supported..."` the first time this code ever ran against a
     real Codex session. Fixed: `_drive_codex_turn` now always uses `_CODEX_MODEL`, matching the proven
     plain-text path; the Anthropic response's own `model` field still correctly echoes `req.model` back to the
     caller (a separate, correct concern).
  2. The MCP transport's `manager.run()` (`StreamableHTTPSessionManager`, wraps an anyio task group/cancel scope)
     was entered in turn 1's `/v1/messages` request-handler task and exited in turn 2's — two DIFFERENT asyncio
     tasks. anyio cancel scopes are task-local, not just "structured concurrency" in the loose sense: this raised
     a real, live `RuntimeError: Attempted to exit cancel scope in a different task than it was entered in` the
     first time a real tool_result continuation tried to close it (turn 1 itself worked fine — real Codex
     genuinely called our tool — the crash was purely in turn 2's cleanup path). Fixed by moving the ENTIRE MCP
     transport lifecycle (`mcp_transport()`, a new async context manager) inside `_drive_codex_turn` itself — one
     persistent background task, entered once and exited once, in itself, spanning the whole underlying Codex
     thread's real lifetime regardless of how many separate `/v1/messages` calls that spans.
  3. (Test-harness-only, not a code bug) `fastapi.testclient.TestClient`'s synchronous wrapper tears down its
     blocking-portal task group at the end of EACH individual `.post()` call, cancelling any `asyncio.create_task`
     background work started during that call — meaning a naive same-`TestClient` two-call pause/resume test
     fails with a `CancelledError` even though the real deployed `codex-bridge.service` (one persistent uvicorn
     event loop, no per-request teardown) has no such issue. The 2 route-handler tests spanning both HTTP calls
     use `httpx.AsyncClient` + `ASGITransport` directly instead, on one continuous event loop, to test the real
     shape correctly — documented inline in the test file so a future session doesn't reintroduce the same
     TestClient trap.

  **Real end-to-end evidence, in order of increasing realism:**
  - SDK-level 2-turn round trip (own scratch harness, real Codex/ChatGPT): turn 1 → real `tool_use` for a
    synthetic `get_secret_code` tool; turn 2 (`tool_result` = `"XKCD-9942-PROVEN"`) → real final answer
    genuinely quoting that exact string back — not a hallucination, the tool_result content demonstrably drove
    the answer. Repeated with explicit `thread_id` capture: `thread_id=01a018c5-d4e6-7821-b033-8d44426130ad`
    confirmed identical across both turns, read directly off `ThreadSessionRegistry` (not just inferred from
    correct behavior).
  - **Real Claude Code CLI end-to-end** (this plan's own [REVIEW] P0 todo): `claude -p
    --dangerously-skip-permissions`, `ANTHROPIC_BASE_URL=http://127.0.0.1:8769` + `ANTHROPIC_MODEL=gpt-5.6-luna`
    (exact convention every other `~/.claude-accounts/*.env` in this fleet already uses), run in an isolated
    scratch directory against a real `status.txt` file, prompted to use the Edit tool to replace PLACEHOLDER with
    DONE. **Measured**: `status.txt` content changed from `"The status is PLACEHOLDER for now."` to `"The status
    is DONE for now."` — verified by re-reading the file after the process exited, not by trusting CLI stdout
    (which printed `(no content)` in `--output-format text` mode — a real CLI-output-mode quirk worth noting for
    future headless invocations, not investigated further here since the actual measured artifact — the file —
    is the real proof). Server log showed the real MCP handshake (`initialize`/`tools/list`/`tools/call`) across
    TWO separate Codex threads (no incremental reuse, as documented) and one real streaming attempt
    (`POST /v1/messages?beta=true` → this bridge's honest `501`) that the CLI transparently recovered from
    without failing the task — real evidence the documented "no streaming" gap costs a wasted round trip per
    turn but does not break real usage.

  **Quality gates**: `ruff format`/`ruff check`/`basedpyright` all clean after two real fixes (a redundant
  `isinstance` basedpyright flagged in `_stringify_tool_result_content`, and `_mcp_asgi_app`'s ASGI callable
  needing Starlette's real `Scope`/`Receive`/`Send` types instead of a narrower `dict[str, Any]` — the mount
  itself is otherwise correct). `uv.lock` regenerated (`uv lock`) after the manual `pyproject.toml` edit added
  `mcp>=1.0.0` — a real dependency now, not lazy-optional, matching `openai-codex`'s own precedent. Full
  `bash scripts/quality-gates.sh` run pending final confirmation (this session's slot has real contention from
  other concurrent local sessions sharing it — see the SessionStart collision warning — so the gate is
  genuinely resource-queued, not stalled).

  **Honestly still open after this entry**: todo 5 (concurrency/timeout characterization — multiple simultaneous
  tool calls, a genuinely slow tool, Codex's own `tool_timeout_sec`) has NOT been attempted yet; todos 6-9
  (ship via quickmerge, deploy to the live VM, the operator-gated `codex-luna` unpause, final archival) are all
  still open, in that order.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:b86998d38ce6877d]: KEEP-NA, valid — doc's own Progress Log records an explicit same-day operator decision (human plan, not AO-dispatched); every todo is part of one multi-file, multi-day rewrite of live-dispatch-critical-path machinery (codex_bridge_server.py) including a prod VM deploy/restart and a live account unpause — exactly the class not to auto-bundle into RECLASSIFY.
