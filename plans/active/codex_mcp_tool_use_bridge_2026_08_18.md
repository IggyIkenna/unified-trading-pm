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
depends_on: [codex_luna_flex_bridge]
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

- [ ] [INFRA] P0. Design the pause/resume MCP proxy: on an incoming `/v1/messages` request carrying `tools`,
      register a per-request MCP server (via `ThreadStartParams.config={"mcp_servers": {...}}`, proven mechanism
      above) whose `tools/call` handler does NOT execute the tool — it blocks (async wait on a
      resolvable/future) until a matching `tool_result` arrives via a LATER HTTP call. Done when: a written
      design (code comments + a short doc section in `codex_bridge_server.py`'s module docstring) names the
      concrete concurrency primitive (e.g. `asyncio.Future` keyed by a generated tool-call id) and how a second,
      stateless HTTP request locates the correct pending call.
- [ ] [INFRA] P0. Implement thread/session continuation — the bridge must correlate a later, separate
      `/v1/messages` call (carrying `tool_result`) back to the SAME in-flight Codex thread/turn from the
      original request. Reuse whatever conversation-identity the Anthropic protocol already provides (message
      history / a stable identifier Claude Code sends) rather than inventing a new one. Done when: a real 2-turn
      HTTP exchange (turn 1 request with tools → real `tool_use` response; turn 2 request with `tool_result` →
      real final text response) resolves against the SAME underlying Codex thread, verified by thread_id logging.
- [ ] [INFRA] P0. Implement the translation: incoming Anthropic `tools` array → per-request MCP server tool
      definitions; a paused MCP `tools/call` → immediate Anthropic `stop_reason: "tool_use"` HTTP response with
      correct `id`/`name`/`input`; an incoming `tool_result` block → resolves the matching pending MCP call with
      that content, and the subsequent Codex turn completion → the final Anthropic text response. Reuse the
      round-trip translation logic already proven correct in the prototype (`run_experiment.py`,
      `weather_mcp_server.py` — isolated pilot scratch dir, not committed; re-derive the shape, don't assume the
      files still exist in a future session).
- [ ] [REVIEW] P0. Real end-to-end validation against the ACTUAL Claude Code CLI (not just SDK-level probes) —
      spawn a real `claude` process pointed at the bridge (`ANTHROPIC_BASE_URL=http://127.0.0.1:<port>`,
      `ANTHROPIC_MODEL=gpt-5.6-luna`) and drive a real file-edit task end to end. Done when: the CLI's own Edit
      tool genuinely executes against a real file through this bridge, not a synthetic test tool.
- [ ] [REVIEW] P1. Characterize concurrency + timeout behavior for real: multiple simultaneous in-flight tool
      calls on the SAME bridge process, and Codex's own `tool_timeout_sec` MCP config (defaults to null per the
      prototype, unconfirmed real behavior) against a genuinely slow tool (a long-running Bash command, not the
      20s synthetic sleep already tested). Done when: a documented real ceiling (or confirmed "no ceiling
      observed up to N seconds") exists, not assumed from the prototype's one 20s data point.
- [ ] [SCRIPT] P1. `bash scripts/quality-gates.sh` green on the changed `server/codex_bridge_server.py` (+ any
      new module) before shipping — no regression on the existing plain-text path, which already works in
      production.
- [ ] [SCRIPT] P0. Ship via `bash scripts/quickmerge.sh "<msg>" --agent --files 'server/codex_bridge_server.py ...'`
      per this workspace's git discipline (CLAUDE.md) — never a raw `git push`.
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
