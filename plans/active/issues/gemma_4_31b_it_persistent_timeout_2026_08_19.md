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
    /plans/active/codex_mcp_tool_use_bridge_2026_08_18.md,
    /codex/15-runbooks/agent-orchestrator-local-pilot-isolation-runbook.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
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
    /plans/archive/2026_08/kimi_gemma_provider_onboarding_2026_08_16.md,
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

0. ✅ **[UI] DONE 2026-08-19** (slot 3, isolated pilot) — flag per-model health in the dashboard, live-derived, not a
   hardcoded label. Added `AccountDef.health_status: Literal["healthy","degraded"] | None` (`server/accounts.py`,
   `server/models/accounts.py`, wired via a new `_account_health_status()` reader into `_account_to_view()` in
   `server/routes/accounts.py` — deliberately NOT reusing `status`, which reflects the unrelated pause/rate-limit
   state, not "does this model respond"). `NvidiaCapacityPanel.tsx` gained `degradedNvidiaAccounts()` + a
   `.gemma-degraded-banner`, following the exact `KimiWalletPanel.tsx`/`allKimiAccountsPaused()` precedent —
   live-polled from `GET /api/accounts`, disappears on its own once the flag flips back to `"healthy"`. Tooltip
   cites this issue doc and the real evidence by name. **Evidence**: `agent-orchestrator@3b610af0b0` (landed on
   `live-defi-rollout`) — full `quality-gates.sh` green (4150 passed/4 skipped pytest, pip-audit clean, `tsc`
   clean, 418/418 vitest); new `NvidiaCapacityPanel.test.ts` (4 cases) + a new Playwright case in
   `nvidia-capacity.spec.ts` ("shows the degraded banner for gemma-4-31b-it only... DiffusionGemma stays
   unflagged") — 10/10 real e2e passed, including a full regression run of Kimi's 7 existing banner specs (no
   collateral damage). **Real remaining gap, not code**: the LIVE VM's `data/config/accounts.json` (gitignored,
   operator-managed, separate from the shipped `accounts.mock.json` e2e fixture) still needs
   `health_status: "degraded"` set on the real `nvidia-gemma-4-31b-it` account for the banner to actually show in
   production — a manual operator/dispatch step, same category as the original `POST /api/accounts/{id}/disable`
   pause, not something this pilot session did or should do from a slot checkout.
- [ ] [OPERATOR] P2. Set `health_status: "degraded"` on the real `nvidia-gemma-4-31b-it` account in the LIVE VM's
      `data/config/accounts.json` (gitignored, operator-managed — distinct from the shipped `accounts.mock.json` e2e
      fixture). Without it the `NvidiaCapacityPanel.tsx` degraded banner shipped in item 0
      (`agent-orchestrator@3b610af0b0`) never actually renders in production. Same category as the original
      `POST /api/accounts/{id}/disable` pause — a host-local operator step, not a repo commit. Done-when:
      `GET /api/accounts` returns `health_status: "degraded"` for that account and the banner is visible in the live
      dashboard. Repo: agent-orchestrator (host config, no sha).

- [ ] [INFRA] P1. DEFERRED-BY-DESIGN — RULED 2026-08-22 (D83): stop pursuing further investigation — blind-retrying
      guidance applies, and the remaining lead (capturing the NVIDIA playground's wire request to diff against attempt
      3's payload) has no guaranteed resolution. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md
      ledger.

- **[INFRA] P2. CANCELLED — SUPERSEDED 2026-08-22 (D83 ruling: investigation stopped per the item above, so no
  diff-based proxy fix will be pursued).**

- [ ] [OPERATOR] P3. Per D83 ruling (2026-08-22): treat this as a probable NVIDIA-side outage/degradation specific
      to this model's public API route (distinct from the playground's route): raise a direct NVIDIA support/forum
      check, or re-test after real elapsed time (days, not another same-session retry). Done-when: either a support
      thread is filed and linked here, or a fresh dated attempt is added to the evidence table.
      Repo: agent-orchestrator.

> **Guard (was numbered step 3, kept as a rule, not a todo)**: do NOT keep blind-retrying with real requests without
> new information — the evidence table above already covers streaming/non-streaming x 2 keys x proxy/direct, and a
> 6th identical attempt adds nothing.

## Progress Log

- **2026-08-19**: Filed following an interactive pilot-testing session. Full evidence table above is the complete
  real record; nothing summarized away. Operator will hand this to another engineer (Harsh) to continue while this
  session moves on to GLM/Gemini real-CLI testing.

- **2026-08-19 (slot 3, isolated pilot, new key)**: Operator generated a fresh, THIRD NVIDIA key
  (`.tabs/3/agent-orchestrator/keys.env`, never GSM-stored) specifically to re-test this. Two real, bounded calls
  direct to `https://integrate.api.nvidia.com/v1/chat/completions`: (1) control — `google/diffusiongemma-26b-a4b-it`,
  real `HTTP 200` in 0.41s, confirming the new key itself is valid; (2) `google/gemma-4-31b-it`, 110s bounded
  timeout — **identical zero-byte timeout** (`curl: (28) Operation timed out ... 0 bytes received`), matching the
  exact failure signature of every prior attempt. This is now a **6th real attempt across a 3rd distinct key**,
  further reinforcing "not a credentials issue" from the evidence table above. Per this doc's own "do not keep
  blind-retrying" guidance, no further raw-API retries were made this session — real signal here would come from
  step 1 (the playground's actual wire request), which needs the operator's own browser DevTools session, not
  something reproducible from this environment.

  **Step 0 ([UI] health banner) — implemented, tested, and shipped this session**, in the isolated `.tabs/3` slot
  per the local-pilot-isolation-runbook (dashboard code change, not a live-orchestrator pilot launch — no server
  instance spun up against real credentials; only the repo's own self-isolating `mode=mock` Playwright/vitest test
  infra was used). Real per-account (not per-provider) health field added, following the "live-derived, not
  hardcoded" precedent from `KimiWalletPanel.tsx`'s `allKimiAccountsPaused()`:
  - `AccountDef.health_status: Literal["healthy", "degraded"] | None` (`server/accounts.py`) — operator-declared
    static config, same shape as `tier`/`variant`/`gcp_project`, deliberately NOT reusing `status` (which reflects
    the unrelated pause/rate-limit state — both Gemma accounts are independently `disabled` for the task-routing
    gate, not this bug).
  - `AccountView.health_status` (`server/models/accounts.py`) + `_account_health_status()` reader wired into
    `_account_to_view()` (`server/routes/accounts.py`), mirroring the existing `_account_provider()` pattern
    (accounts.json-read, no DB/ORM change needed).
  - `NvidiaCapacityPanel.tsx`: new `degradedNvidiaAccounts()` pure helper + `.gemma-degraded-banner` rendering,
    fetched live from `GET /api/accounts` (polled, same as Kimi's banner) — disappears on its own the moment the
    operator flips the account back to `"healthy"`. Tooltip cites this issue doc by name and the real evidence
    (6 attempts, 3 keys) so the reason is never a bare label.
  - `dashboard/src/types.ts`, `dashboard/src/styles.css` (`.gemma-degraded-banner`, mirrors `.kimi-paused-banner`'s
    severity), `data/config/accounts.mock.json` (e2e fixture: `nvidia-diffusiongemma-demo` → `"healthy"`,
    `nvidia-gemma-4-31b-demo` → `"degraded"`).
  - **Real test evidence**: new `NvidiaCapacityPanel.test.ts` (4 vitest cases for the pure helper); new Playwright
    case in `nvidia-capacity.spec.ts` ("shows the degraded banner for gemma-4-31b-it only... DiffusionGemma stays
    unflagged") — **10/10 passed** against the real e2e stack (`mode=mock`, real server boot), including a
    regression run of all 7 existing Kimi-banner specs (no collateral damage). Two pre-existing test fixtures
    (`layout.test.ts`, `KimiWalletPanel.test.ts`) needed a `health_status: null` field added to their `AccountView`
    mock builders to keep typechecking — done, `tsc --noEmit` clean, full vitest suite **418/418 passed**. Backend
    `AccountDef`/`AccountView` construction sanity-checked directly (`degraded` and default-`None` both validate).
  - **Shipped**: `quality-gates.sh --no-fix` confirmed green (4148 passed/4 skipped pytest, pip-audit clean, `tsc`
    clean, 418/418 vitest) before shipping; landed via `quickmerge.sh --agent --files ...` scoped to exactly the 11
    touched files as `agent-orchestrator@3b610af0b0` on `live-defi-rollout` (re-verified green in quickmerge's own
    Stage 3 re-gate: 4150 passed/4 skipped). See the flipped step 0 above for the full evidence citation. The live
    VM's real `accounts.json` (gitignored, operator-managed, separate from the shipped `accounts.mock.json` e2e
    fixture) still needs `health_status: "degraded"` set on the real `nvidia-gemma-4-31b-it` account for the banner
    to actually render in production — a manual operator/dispatch step, same category as the original
    `POST /api/accounts/{id}/disable` pause, not something this pilot session did or should do from a slot
    checkout.

- **2026-08-19 (operator, live browser session) — real DevTools evidence, likely root cause identified.** Operator
  opened `build.nvidia.com/google/gemma-4-31b-it/playground` with DevTools Network tab open. Two real findings:
  1. **The playground itself failed this session** ("Error / Retries exhausted: 3/3" on a trivial weather prompt) —
     the FIRST time the playground has been observed failing (the original control test, 2026-08-18/19, succeeded:
     48.15s, "1+1=2"). Directly contradicts treating the playground as a reliable "always works" control.
  2. **Real NVCF (NVIDIA Cloud Functions) queue-status telemetry captured** — one of the `gemma-4-31b-it`-named
     Network requests returned: `{"functionId": "48c619ec-c254-48da-8fcc-6ef8a04fed6e", "queues": [{"functionVersionId":
     "c27f9810-ac0d-469b-b5c7-446c7ff5799e", "functionName": "ai-gemma-4-31b-it", "functionStatus": "ACTIVE",
     "queueDepth": 148}]}`. Operator confirmed `queueDepth` fluctuates across requests (goes down, then back up) —
     real, live queue congestion, not a static/cached number. Operator also reports most `gemma-4-31b-it` requests in
     the same session returned real `200`s, with one real `500` — i.e., the playground gets through MOST of the time,
     just not always, consistent with variable real-time queue depth rather than a dead function.

  **Working theory**: the playground does NOT make a single synchronous call the way our direct curl does — the
  `functionId`/`queueDepth` JSON shape is NVCF's own real async submit+poll status-check API. Likely flow: submit →
  poll this queue-status endpoint repeatedly → fetch the real completion once the function executes. The public
  OpenAI-compatible `integrate.api.nvidia.com/v1/chat/completions` endpoint is supposed to do this polling
  server-side and just hold the HTTP connection open for the caller — but for this specific heavily-queued function,
  that server-side wait appears to silently hang/drop rather than ever completing.

  **Real test of "is it just slow" — NEGATIVE, rules out patience alone**: re-ran the direct curl (new/3rd key, same
  as prior attempts) with a 300s (5 min) bounded timeout instead of the prior 60-150s range. Result: **still a real
  zero-byte timeout** (`curl: (28) Operation timed out after 300002 milliseconds with 0 bytes received`,
  `HTTP_STATUS:000`). This is now a **7th real failed attempt across 3 keys**, and it rules out "the synchronous
  endpoint just needs more time" — 5 real minutes of patience did not produce a response. Combined with the
  playground's own frequent 200s (which return in well under 5 minutes per the earlier 48s control), this points
  toward a real MECHANISM difference (async submit+poll vs. a naive synchronous hold that gets dropped), not merely
  "wait longer." **Next real step**: capture the actual SUBMIT request (the first `gemma-4-31b-it`-named POST in a
  successful playground turn) and its response headers/status (looking for a `202`/`NVCF-REQID`/`Location`-style
  marker), plus the exact queue-status polling endpoint URL/headers — this would confirm or refute the submit+poll
  theory directly and point at a concrete, buildable fix (switch the proxy/client to the real async flow) rather
  than an NVIDIA-side wait.

- **context-scout 2026-08-20**: re-verified context_scope (4 entries), unchanged.
- **2026-08-22 — ruling D83 (gemma-4-31b investigation)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Stop — blind-retrying guidance applies; the remaining lead has no guaranteed
  resolution. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
