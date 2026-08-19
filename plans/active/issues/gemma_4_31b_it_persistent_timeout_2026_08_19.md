---
doc_type: issue
title: "google/gemma-4-31b-it — persistent zero-byte timeout via API, works in NVIDIA playground"
summary: >-
  Real, unresolved finding from a local isolated pilot session testing the paused GLM/Codex-Luna/Gemini/Gemma
  providers (2026-08-18/19): `google/gemma-4-31b-it` (NVIDIA NIM) times out with ZERO bytes back on every one of
  5 real API attempts — 2 keys, streaming and non-streaming, direct-to-NVIDIA and through our LiteLLM proxy — while
  the operator's own NVIDIA playground session got a real response (48.15s, 34.59s TTFT) for an equally trivial
  prompt. Not a rate-limit (no 429 anywhere in this set), not a credentials issue (2 different keys, both otherwise
  valid), not our proxy's translation (fails identically bypassing it). Root cause not isolated — needs the
  playground's actual wire request (Network tab → Copy as cURL) to diff against, which this session could not get
  from the operator (repeated pastes were the Console tab, not Network).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, gemma, nvidia, nim, timeout, litellm, model-routing]
related:
  [
    /plans/active/kimi_gemma_provider_onboarding_2026_08_16.md,
    /plans/active/codex_mcp_tool_use_bridge_2026_08_18.md,
    /codex/15-runbooks/agent-orchestrator-local-pilot-isolation-runbook.md,
  ]
created: "2026-08-19"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
assigned_role: infra
drift_direction: none
resolved_by:
locked_by:
depends_on: []
source: >-
  Interactive session, isolated local pilot clone (per the local-pilot-isolation-runbook), real GSM-sourced
  credentials, real API calls throughout. Nothing here touched the live orchestrator VM or production accounts.
context_scope:
  [
    /plans/active/kimi_gemma_provider_onboarding_2026_08_16.md,
    agent-orchestrator/config/litellm/grok_gemini_proxy.yaml,
    agent-orchestrator/server/gemini_headroom.py,
    agent-orchestrator/server/nvidia_headroom.py,
  ]
---

# `google/gemma-4-31b-it` — persistent zero-byte timeout via API, works in NVIDIA playground

## Current state (do not re-litigate without new evidence)

- **`google/diffusiongemma-26b-a4b-it`**: fully proven working, including a real tool_use/tool_result round trip
  through the LiteLLM proxy (tool name/id preserved, correct final answer). This is the working Gemma model — use
  it as the reference/control for anything that needs "a real working Gemma."
- **`google/gemma-4-31b-it`**: real, reproducible failure — see evidence table below. Registered, paused
  (per `kimi_gemma_provider_onboarding_2026_08_16.md`), and per operator instruction (2026-08-18) staying
  registered and monitored, NOT removed, while this is unresolved.

## Evidence table (2026-08-18/19, all real attempts, no fabricated data)

| # | Path | Key | Streaming | Result |
|---|------|-----|-----------|--------|
| 1 | Real AO-style tool-call test (`run_tool_use_roundtrip`) via isolated LiteLLM proxy | GSM `nvidia-api-key` | non-streaming | Timeout at 60s, zero bytes |
| 2 | Same, retried with 100s timeout | GSM `nvidia-api-key` | non-streaming | Timeout at 100s, zero bytes |
| 3 | Direct curl to `integrate.api.nvidia.com`, NVIDIA's own documented example payload incl. `chat_template_kwargs: {enable_thinking: true}` | Operator-pasted key (fresh, since rotated — see Security note) | non-streaming | Timeout at 60s, zero bytes |
| 4 | Direct curl to `integrate.api.nvidia.com`, `stream: true` | GSM `nvidia-api-key` | streaming (SSE) | Timeout at 90s, zero bytes (not even a first SSE chunk) |
| 5 | Through isolated LiteLLM proxy, plain text, `/v1/messages` | GSM `nvidia-api-key` (via proxy) | non-streaming | Timeout at 150s, zero bytes, **and zero server-side log lines in the LiteLLM proxy's own log** — not even a uvicorn access-log entry |
| — | **Control**: `build.nvidia.com/google/gemma-4-31b-it/playground` (operator's own browser session) | Operator's own | unknown (likely streaming, standard for a chat UI) | **Real success**: 48.15s total, 34.59s TTFT, 3.91 TPS, "1+1=2" |

**Ruled out**: rate-limiting (attempt 5's log DOES show a real 429 from an EARLIER, unrelated DiffusionGemma
request in the same session — confirming the proxy logs 429s when they happen; gemma-4-31b-it attempts produced
no such signal, just silence). Credentials (2 different keys, both otherwise valid — the GSM key is independently
proven valid via DiffusionGemma's successful tool-use round trip and a real `/v1/models` listing that included
`google/gemma-4-31b-it` by name). LiteLLM's payload translation (attempts 3/4 bypassed LiteLLM entirely and failed
identically). The `enable_thinking` chat_template_kwarg (attempt 3 included it, still failed).

**Not ruled out / not isolated**: whether the playground uses a different backend/route than the public
`integrate.api.nvidia.com/v1/chat/completions` REST endpoint; whether the playground's browser JS sends a request
shape none of attempts 1-5 reproduced. This needs the actual wire request to resolve — see next steps.

**Security note**: the operator pasted a live NVIDIA API key in plain text into the interactive session for
attempt 3 (2026-08-18). Flagged in-session; the operator should confirm it's been rotated on build.nvidia.com if
not already done. That key is not reproduced here.

## Next steps for whoever picks this up

0. **[UI] Flag per-model health in the dashboard, live-derived, not a hardcoded label** — operator ask,
   2026-08-19: while this is open, the dashboard should visibly distinguish `diffusiongemma-26b-a4b-it` (working)
   from `gemma-4-31b-it` (broken, this issue) so nobody dispatches to the broken one blind. Reuse the EXACT
   precedent already shipped for Kimi: `KimiWalletPanel.tsx`'s `allKimiAccountsPaused()` — derived live from
   `GET /api/accounts`, not a static string, so the banner disappears on its own the moment this issue resolves.
   For Gemma specifically there is no existing per-model (only per-provider) health field on `AccountView` — check
   whether one needs adding, or whether `last_used_at`/a new `health_status` field on the NVIDIA account row is the
   right vehicle. Done when: a `.gemma-degraded-banner` (or similar) renders live off real account state, with a
   Playwright regression spec mirroring `kimi-wallet-reconciliation.spec.ts`'s "shows the paused banner" test.
1. **Get the playground's real wire request**: DevTools → **Network** tab (not Console) → filter Fetch/XHR → send
   a playground message → find the `chat/completions` (or similar) request → right-click → Copy → **Copy as
   cURL**. Diff it against attempt 3's payload above — likely differences to check: a different `api_base`/route
   entirely, additional headers (a session/trace id NVIDIA's gateway might require), or a genuinely different
   `stream`/`chat_template_kwargs` shape than what NVIDIA's own docs example (attempt 3) used.
2. If the diffed request reveals a fixable gap, apply it to `config/litellm/grok_gemini_proxy.yaml`'s
   `gemma-4-31b-it` `litellm_params` and re-test attempts 1-2's tool-use round trip for real.
2. If no meaningful diff is found, this may be a genuine NVIDIA-side outage/degradation specific to this model's
   public API route (distinct from the playground's route) — worth a direct NVIDIA support/forum check, or simply
   re-testing again after some real elapsed time (days, not another same-session retry — 5 attempts across ~20
   minutes already exhausted the cheap-retry space without new signal).
3. Do not keep blind-retrying with real requests without new information (evidence table above already covers
   streaming/non-streaming × 2 keys × proxy/direct — a 6th identical attempt adds nothing).

## Progress Log

- **2026-08-19**: Filed following an interactive pilot-testing session. Full evidence table above is the complete
  real record; nothing summarized away. Operator will hand this to another engineer (Harsh) to continue while this
  session moves on to GLM/Gemini real-CLI testing.
