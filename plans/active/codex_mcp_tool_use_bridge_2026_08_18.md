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
last_updated: 2026-08-19
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
    agent-orchestrator/server/codex_mcp_proxy.py,
    agent-orchestrator/server/codex_bridge_server.py,
    agent-orchestrator/server/routes/accounts.py,
    /plans/active/codex_luna_flex_bridge_2026_08_14.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
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
- [x] [REVIEW] P1. ✅ Characterize concurrency + timeout behavior for real — **DONE 2026-08-19**, both against live
      Codex/ChatGPT credentials (isolated local pilot). **Concurrency**: two fully independent tool-use turns
      fired via real `asyncio.gather` at the SAME bridge process (distinct `thread_id`s
      `01a018d0-0fcb-73b2-b0a2-79b05567cf64` / `01a018d0-105b-7b60-beeb-7634e9512b3e`), resolved in REVERSE
      creation order specifically to rule out an accidental FIFO-only assumption — both sessions' final answers
      correctly quoted their OWN distinct secret value (`ALPHA-VALUE-3047` / `BETA-VALUE-9182`) with zero
      cross-contamination, confirming `ThreadSessionRegistry`'s per-`tool_use_id` isolation holds under real
      concurrent load, not just by code inspection. **Timeout**: a real tool-use turn paused, then a genuine
      90-SECOND wall-clock wait (measured, `time.monotonic()`-timed) before sending the `tool_result` — 4.5x the
      prototype's earlier untested 20s data point. Result: `HTTP 200`, Codex genuinely accepted the delayed
      result and produced the correct final answer (`SLOW-VALUE-6600`). **No timeout ceiling observed up to
      90s** — Codex's `tool_timeout_sec` MCP config default (`null` per the prototype) holds in practice at this
      duration, not just in the config default's stated intent.
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
- [x] [INFRA] P0. ✅ Deploy to the live orchestrator VM and verify — **DONE 2026-08-19**, instance
      `i-0c9b283b31d6b5ca7` (region `ap-northeast-1`, EIP 13.113.200.22, id `planning`), accessed via
      documented read/write SSM `send-command` (per `agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh`'s
      own header comment — no inbound firewall change, every call CloudTrail-audited). Confirmed `git HEAD` on the
      VM already matched `agent-orchestrator@ea9ecd2b4e` (`ao-self-pull.sh`'s 2-minute cron had already pulled
      it). **A SECOND real deployment gap found and fixed, beyond the already-documented "manual restart
      required" one**: the first `systemctl restart codex-bridge` came back healthy (`/health` 200) but a real
      tool-use smoke test immediately 502'd with `Codex SDK call failed: No module named 'mcp'` — `ao-self-pull.sh`
      pulls CODE but does not `uv sync` a NEW python dependency into the service's `.venv`; restarting alone
      replays the OLD dependency set. Fixed with `sudo -u ubuntu uv sync` (installed `mcp==2.0.0` +
      transitive deps, matching the local `uv.lock` exactly) followed by a second restart. **Worth carrying
      forward**: any future plan shipping a NEW python dependency to a VM-deployed service needs an explicit
      `uv sync` step on that VM, not just a restart — not yet promoted to a standing codex SSOT, flagging here so
      a future session/audit can decide whether `runtime-deployment-topology.md` or `vm-tarball-deployment.md`
      should own it. **Real production evidence** (via a self-contained remote Python script executed through
      SSM, using the VM's own real `codex-luna` ChatGPT credentials, not mine): turn 1 →
      `HTTP 200, stop_reason: "tool_use"`, `tool_use_id=toolu_codex_a06d75bf223b4d0e8220da4e`; turn 2
      (`tool_result="PROD-SMOKE-8821"`) → `HTTP 200`, final answer `"PROD-SMOKE-8821"` — genuinely reflecting the
      injected content, not a hallucination. `codex-bridge.service` confirmed `active` post-restart both times.
- [x] ✅ [REVIEW] P1. **Production smoke test RE-CONFIRMED 2026-08-19** — a real tool_use/tool_result round trip
      against the live `codex-bridge.service` (marker `RESMOKE-DD6149CC32` injected via `tool_result`, echoed back
      verbatim, `MARKER_MATCH=True`). Flagged **READY FOR OPERATOR REVIEW to unpause** `codex-luna` — the
      `BLOCKED-OPERATOR-DECISION` tag this todo carried is retired in this same edit, per the corpus's own "the
      moment an operator tag resolves, retag in the same edit" rule.
      **UNPAUSE CONFIRMED LIVE 2026-08-21 (interactive session)** — independently re-verified rather than trusting
      the operator's statement alone, per this workspace's measurement discipline: queried `AccountUsageRow`
      directly on the orchestrator VM (read-only, via the app's own `session_scope()`, no dashboard JWT) —
      `account_id=codex-luna status=healthy` (not `disabled`), `last_used_at=2026-08-21 05:36:58 UTC`.
      Cross-checked against `TaskUsageRow`: **8 real completed dispatches** to `codex-luna` in the trailing ~2h
      across 5 different real slots (4, 8, 12, 25, 26), including genuine plan-derived backlog tasks
      (`b21_distinct_values_noncanonical_live-…`, `w15_execution_service_venue_adaptor_security_audit-…`,
      `w_execution_orchestrator_oms_persistence_impl-…`), not just one-off dispatches — real fleet traffic is
      flowing through the bridge, not a paused/idle account. `codex_luna_flex_bridge_2026_08_14.md`'s own
      `[REVIEW] P0. Smoke-test gate before any real fleet traffic` todo was already updated to reference this
      plan's evidence and closed (see the 2026-08-19 Progress Log entry below).
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

  Shipped: quality gates ran fully green (`✅ agent-orchestrator quality gate PASSED` — ruff/basedpyright/4196
  pytest/pip-audit/dashboard tsc+vitest) after fixing 2 real basedpyright errors + reformatting 2 files; shipped
  via quickmerge as `agent-orchestrator@ea9ecd2b4e` on `live-defi-rollout` (this repo's `promotion_model:
  ldr_terminal` — LDR IS the deploy target).

- **2026-08-19 (later, same day) — todo 5 (concurrency + timeout characterization) done, real evidence, no code
  changes needed.** Two more live experiments (isolated local pilot, same real credentials): (1) two fully
  independent tool-use turns fired concurrently via `asyncio.gather`, resolved in REVERSE creation order — zero
  cross-session contamination, `ThreadSessionRegistry`'s per-`tool_use_id` isolation holds under real concurrent
  load. (2) A real 90-second wall-clock delay between a tool-use pause and its `tool_result` (4.5x the
  prototype's untested 20s data point) — Codex still accepted the delayed result and answered correctly; no
  timeout ceiling observed at this duration. Full detail on both todo checkboxes above.

  **Honestly still open after this entry**: todos 8 (deploy to the live VM + verify), 9 (operator-gated
  `codex-luna` unpause — NOT mine to do, per this plan's own Non-goals and the operator's 2026-08-16 "disabled"
  instruction), and 10 (final archival, gated on everything above) remain open, in that order.

- **2026-08-19 (later still) — todo 8 (VM deploy + verify) done, real evidence, on the ACTUAL production
  orchestrator VM (instance `i-0c9b283b31d6b5ca7`).** Accessed via the documented read/write SSM `send-command`
  path (`agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh`'s own header comment — the
  established, already-audited mechanism; no ad-hoc access invented). Confirmed the VM's `git HEAD` already
  matched `agent-orchestrator@ea9ecd2b4e` (`ao-self-pull.sh` had already pulled it). First
  `systemctl restart codex-bridge` came back healthy on `/health`, but a real tool-use smoke test immediately
  502'd: `Codex SDK call failed: No module named 'mcp'` — a SECOND real deployment gap, distinct from the
  already-documented "restart isn't automatic" one: `ao-self-pull.sh` pulls code but does not `uv sync` a NEW
  python dependency into the service's `.venv`. Fixed with `sudo -u ubuntu uv sync` (installed `mcp==2.0.0` +
  transitive deps) + a second restart. **Real production evidence** (self-contained remote Python script via
  SSM, using the VM's own real `codex-luna` ChatGPT credentials): turn 1 → `HTTP 200, stop_reason: "tool_use"`
  (`tool_use_id=toolu_codex_a06d75bf223b4d0e8220da4e`); turn 2 (`tool_result="PROD-SMOKE-8821"`) → `HTTP 200`,
  final answer genuinely `"PROD-SMOKE-8821"`. Also updated `codex_luna_flex_bridge_2026_08_14.md`'s own
  `[REVIEW] P0. Smoke-test gate before any real fleet traffic` todo to reference this evidence and close it (a
  documentation-only change — does not touch the account's `enable`/`disable` state).

  **Worth carrying forward, not yet promoted to a standing codex SSOT**: any future plan shipping a NEW python
  dependency to a VM-deployed service needs an explicit `uv sync` step on that VM as part of its own deploy
  todo, not just a restart — flagging here so a future session/audit can decide whether
  `runtime-deployment-topology.md` or `vm-tarball-deployment.md` should own this as a general rule.

  **Honestly still open**: todo 9's actual account-enable flip (`POST /api/accounts/codex-luna/enable`) is
  UNCHANGED, real production-state-affecting, and deliberately NOT done here — that is the one step left for the
  operator, per this plan's own Non-goals. Todo 10 (final archival) is gated on that.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:b86998d38ce6877d]: KEEP-NA, valid — doc's own Progress Log records an explicit same-day operator decision (human plan, not AO-dispatched); every todo is part of one multi-file, multi-day rewrite of live-dispatch-critical-path machinery (codex_bridge_server.py) including a prod VM deploy/restart and a live account unpause — exactly the class not to auto-bundle into RECLASSIFY.

- **context-scout 2026-08-19**: populated/refreshed context_scope (5 entries) — first scout for this doc. Swapped in `codex_mcp_proxy.py` (the actual shipped ~330-line module, now the concrete build target) and `routes/accounts.py` (the `enable_account_endpoint` the remaining operator-gated unpause todo needs) alongside the parent bridge plan and the archival-discipline SSOT (the final todo's ritual); dropped the `openai_codex` venv site-packages path and the local-pilot-isolation runbook — both were prototype-investigation aids from before the module shipped, now lower-value than the real artifacts.

- **2026-08-19 (later still) — production smoke test RE-RUN for fresh, independent evidence, per operator request** (todo 8's own evidence already existed from an earlier run this same day; this is a second, independent confirmation before flagging the unpause todo ready for operator review, not a repeat of the same run). Read-only reconnaissance first (a dedicated Explore sub-agent): confirmed no generic "run an arbitrary command on the VM" wrapper exists — every SSM script hand-rolls its own `aws ssm send-command --document-name AWS-RunShellScript` call (pattern: `check-ao-backlog-status.sh:146-152`); confirmed `codex-bridge.service` still binds loopback-only `127.0.0.1:8769` reading `~/.codex/auth.json` credentials directly, with **no import of `accounts.py`/`account_usage.py` anywhere in `codex_bridge_server.py`** — i.e. `codex-luna`'s `account_status: disabled` is purely an AO-dispatch-eligibility gate (blocks AO's OWN worker-spawn rotation only) and does NOT block a direct script-level call against the bridge, exactly consistent with how the earlier same-day PROD-SMOKE-8821 evidence was obtainable while the account stayed disabled the whole time. No saved copy of the earlier smoke-test script existed anywhere (git history, `scripts/`) — confirmed ad hoc, rewritten fresh here following the same shape.

  Ran a real 2-turn tool_use/tool_result round trip via SSM `send-command` (`AWS-RunShellScript`, instance `i-0c9b283b31d6b5ca7`, region `ap-northeast-1`) against the live `codex-bridge.service`, using its own resident `codex-luna` ChatGPT credentials — no account state touched, no restart, no file changes on the VM. **Real measured result**: `/health` → `200 {"status":"ok"}`; turn 1 (`echo_marker` tool declared) → `HTTP 200`, `stop_reason=tool_use`, real `tool_use_id=toolu_codex_a8eaa455727c4871ac70fc4b`; turn 2 (`tool_result` = freshly-generated marker `RESMOKE-DD6149CC32`) → `HTTP 200`, final text `'RESMOKE-DD6149CC32'` — genuinely echoing the injected content, `MARKER_MATCH=True`. Passed cleanly, no errors, no retries needed. (Usage numbers logged in this run — `input_tokens=44`/`60`, `output_tokens=1`/`4` — are still the OLD `len(text)//4` estimate, since `multi_provider_context_billing_reconciliation_2026_08_16.md`'s `[INFRA] P0` real-usage fix had not yet been deployed to this VM at the time of this run — expected, unrelated to this todo.)

  Updated the `[REVIEW] P1` unpause todo above to **READY FOR OPERATOR REVIEW** with this fresh evidence — deliberately did NOT flip `codex-luna`'s `account_status` myself (`POST /api/accounts/codex-luna/enable`), per this plan's own Non-goals; that flip, and this plan's final `[DOC] P2` archival todo (gated on it), remain for the operator.

- **na-eligibility-audit 2026-08-21 (ao tranche)**: KEEP-NA, valid — reaffirmed. `last_updated: 2026-08-19`, no
  content change since the 2026-08-19 verdict. Both open todos remain: an `[REVIEW] P1` operator-gated account
  unpause (a real production-dispatch-affecting flip, deliberately not mine to do per this plan's own Non-goals),
  and a `[DOC] P2` final archival todo explicitly gated on that unpause. Doc stays `assigned_vm: NA`.
