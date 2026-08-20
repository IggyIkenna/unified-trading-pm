---
doc_type: issue
title: >-
  NVIDIA/Gemma and Codex/Luna have ZERO exhaustion detection — proactive or reactive — unlike every
  other registered provider; a real live 429 during today's cross-provider smoke test proved it
summary: >-
  The fleet's account-failover switchover mechanism (_account_meets_dispatch_headroom(), the single
  gate shared by fresh dispatch and mid-session proactive kill) is genuinely uniform in HOW it
  switches, but what counts as "exhausted" is bespoke per provider and is NOT uniformly wired: Claude
  and GLM share one generic pct-ceiling mechanism, Gemini has its own bespoke RPM/RPD branch inside
  the same gate function, DeepSeek has an entirely separate peak-window+spend-ceiling path outside
  that function — and NVIDIA/Gemma and Codex/Luna have NEITHER, confirmed by direct code trace AND a
  real, live 429 caught during a 2026-08-19 isolated-pilot cross-provider smoke test (9 models, real
  accounts). This means a real fleet dispatch against NVIDIA or Codex today would keep hammering an
  exhausted account with no automatic failover and no record of why — exactly the "smoke test gets
  stuck on a single exhausted model" failure mode the operator was concerned about.
status: open
resolved_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [agent-orchestrator, autospawn, account-failover, exhaustion, observability, nvidia, gemma, codex, luna, glm]
related:
  [
    /plans/active/issues/worker_slot_account_exhaustion_no_rotation_2026_08_19.md,
    /plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md,
    /plans/active/multi_provider_model_capability_bakeoff_2026_08_19.md,
    /plans/active/kimi_gemma_provider_onboarding_2026_08_16.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-20"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/nvidia_headroom.py,
    agent-orchestrator/server/gemini_headroom.py,
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/server/usage_poller.py,
    agent-orchestrator/server/codex_bridge_server.py,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator, interactive session, 2026-08-19: "telling the system what exhaustion means is a
  model-by-model or provider-by-provider bespoke thing that we need to understand... it can't just be
  UI, it needs to be embedded in the orchestrator." Investigated live during a real 9-model
  cross-provider smoke test in an isolated local pilot (real accounts, real accounts, no live-fleet
  accounts touched).
assigned_role: infra
drift_direction: none
---

# NVIDIA/Gemma and Codex/Luna have zero exhaustion detection — proactive or reactive

## The ask

The switchover mechanism (which account/provider a slot fails over to) should be uniform regardless
of provider. What counts as "exhausted" is legitimately bespoke per provider (rate/min vs rate/day vs
messages/day vs credit-window vs $ balance) — but that bespoke signal needs to be embedded in the
orchestrator's real dispatch-time gating, not just displayed on a dashboard, or a smoke test (or real
fleet dispatch) will get stuck hammering a single exhausted account with no automatic recovery.

## What's actually true today, per provider (verified by direct code trace, 2026-08-19)

The switchover MECHANISM is genuinely uniform: `_account_meets_dispatch_headroom()`
(`server/autospawn.py:1048`) is the single function shared by both `_pick_headroom_account`
(fresh/resume dispatch) and `_drain_worker_account_failover` (mid-session proactive kill) — confirmed
today, no drift between the two paths (this was the exact bug `worker_slot_account_exhaustion_no_rotation_2026_08_19.md`
fixed). The gap is entirely in what feeds INTO that function per provider:

| Provider | What "exhausted" means | Where it's checked | Uniform? |
|---|---|---|---|
| Anthropic/Claude | `weekly_pct`/`five_hour_pct` from real rate-limit headers | Generic `_account_has_headroom()` inside the shared gate | ✅ |
| GLM | Same `weekly_pct`/`five_hour_pct` fields, now populated from real credit-ceiling math (`glm_quota_poller.py`, fixed 2026-08-19) | SAME generic check as Claude — zero GLM-specific code needed | ✅ (as of today) |
| Gemini | RPM/RPD/TPM per (project, model) | Bespoke `gemini_account_has_rate_headroom()`, called explicitly from inside the shared gate | ✅ — but bespoke, not generic |
| DeepSeek | $ balance + peak/off-peak daily/monthly spend ceiling | A THIRD, entirely separate code path (`_deepseek_in_peak_window()` + spawn ceilings) — never routes through `_account_meets_dispatch_headroom()` at all | ⚠️ works, but structurally its own island, not the shared gate |
| **NVIDIA/Gemma** | RPM (shared per key, measured today: 15-20 concurrent breaking point) | ✅ **FIXED 2026-08-19**: `nvidia_account_has_rate_headroom()` wired into `_account_meets_dispatch_headroom()` (agent-orchestrator@86cd2066) | ✅ |
| **Codex/Luna** | **CORRECTED 2026-08-19** (post-fix cross-check against the installed SDK — see todo 2's evidence below): a real, structured signal DOES exist (`RateLimitSnapshot`/`RateLimitWindow.used_percent`) — the original "no API signal exists at all" claim here conflated this with the unrelated $-metered `boost_multiplier` billing-reconciliation signal (`multi_provider_context_billing_reconciliation_2026_08_16.md`), which genuinely IS still `None`. Not yet confirmed live-populated — a real proactive poller is a new follow-up todo below. | ✅ reactive (`codex_bridge_server.py`'s 429 catch, agent-orchestrator@43f8f828); 🟡 proactive poller still an open follow-up | ✅ (reactive) |

So today there are really **three different real mechanisms**, not one uniform one:
1. Generic pct-ceiling fields (Claude, GLM) — the closest thing to a real uniform primitive.
2. Per-provider bespoke branch inside the shared gate (Gemini only).
3. An entirely separate, parallel code path outside the shared gate (DeepSeek only).

And NVIDIA/Codex have none of the three.

## The reactive fallback doesn't save NVIDIA/Codex either

> **✅ STATUS 2026-08-19: both gaps this section describes are now closed** — NVIDIA via a real proactive gate
> (todo 1), Codex via a real reactive 429 catch (todo 2). The analysis below is kept as the accurate PRE-fix
> record, not stale — see the Follow-up section for what shipped and what's still open (a real proactive Codex
> poller, and the still-unfixed pane-scanner gap this section's own last paragraph flags).

`_account_meets_dispatch_headroom()` degrades an uncovered provider to the plain
`account_is_usable()` check, whose only dynamic signal is `rate_limited_until`. Confirmed by direct
grep: **`rate_limited_until` is written ONLY by `usage_poller.py`, which is Claude/Anthropic-only by
design** — it is never set for any other provider, ever. So the "fallback" is a permanent no-op for
NVIDIA and Codex specifically.

There's also a SEPARATE reactive mechanism — `tmux_pruner.py`'s `scan_rate_limits_once()`, which
scrapes live pane TEXT for a rate-limit message and marks the account. This one genuinely runs
regardless of provider (it doesn't branch on `acc.provider`). But its actual date/time EXTRACTION
regex (`_RESET_TIME_RE`, parsing `"resets May 24, 7pm (UTC)"`) is shaped specifically around Claude
Code's own rate-limit message format. A GLM/NVIDIA/Codex-shaped error (confirmed today: raw JSON like
`{"type":"error","error":{"type":"rate_limit_error",...}}` for GLM, or
`{"error":{"message":"litellm.RateLimitError...429..."}}` for NVIDIA-via-litellm) would not match that
pattern — so even this generic-looking scanner likely can't correctly parse a non-Claude exhaustion
message today. Not independently verified live (see "What was NOT done" below).

## Real evidence, not just code-reading — caught live, 2026-08-19

During a 9-model cross-provider smoke test (isolated local pilot, real accounts, task: count lines of
code in a real repo), two models hit real, live exhaustion mid-test:

- **Gemma / `diffusiongemma-26b-a4b-it`** (NVIDIA): real HTTP 429 —
  `litellm.RateLimitError: Nvidia_nimException - Error code: 429 - {'status': 429, 'title': 'Too Many
  Requests'}`. This happened minutes after a deliberate concurrency-ramp test on the same key/model
  (breaking point measured at 15-20 concurrent requests, same session) — a real, reproducible
  consequence of exactly the shared-per-key RPM ceiling `nvidia_headroom.py` tracks but nothing gates
  dispatch on.
- **GLM 5-Turbo**: real HTTP 429 — `"Usage limit reached for 5 hour. Your limit will reset at
  2026-08-20 00:22:34"`. (GLM is NOT part of this gap — it's covered by the generic pct-ceiling
  mechanism as of today's `glm_quota_poller.py` fix — included here only as evidence that real
  exhaustion during real testing is a frequent, not hypothetical, occurrence.)

Both calls were made directly against each provider's real endpoint (bypassing AO's own
selection/dispatch code entirely, since both accounts are deliberately paused on the live fleet) — so
this does NOT by itself prove AO's own dispatch path saw and mis-handled the failure. What it DOES
prove: the failure mode is real and reproducible, not theoretical.

### What was NOT done (stated plainly, not silently skipped)

A full live-AO-dispatch reproduction — start a real (isolated, non-fleet) orchestrator instance,
register an NVIDIA account for real, dispatch a real task through `select_account_for_spawn()`, hit a
429 through THAT path, and query the instance's own `activity_log`/`AccountUsageRow` afterward to
confirm nothing got recorded — was **not** performed. The evidence above is real observed behavior
(the 429) combined with direct code-tracing (the absence of any capture path) — together sufficient to
confirm the gap exists, but short of a full end-to-end proof through AO's own selection code. If that
stronger proof is wanted, it's a real, boundable follow-up (todo 3 below) — not done here because
NVIDIA/Codex are deliberately paused on the live fleet and standing up a second full local AO server
instance (beyond the litellm-proxy/codex-bridge pieces already used) was judged out of scope for a
same-session finding.

## Independent corroboration — Harsh, same day, separate real test (bake-off harness)

A second, independent real test (Harsh, `multi_provider_model_capability_bakeoff_2026_08_19.md`'s
own evaluation harness — 6 Gemini tasks fired ~30s apart) hit the SAME class of failure from a
different angle: real Gemini free-tier rate-limit washout, not caught proactively. Two corrections/
additions this surfaces, worth stating precisely rather than just appended:

- **Gemini is NOT part of this doc's gap** — it already has real dispatch-time gating
  (`gemini_account_has_rate_headroom()`, wired into `_account_meets_dispatch_headroom()`). Harsh's
  "no Gemini/Gemma equivalent exists... no `gemini_*_ceiling` in config.py" is correct for the specific
  POLLER-shaped pattern (GLM/DeepSeek's shape: a background poller writes a %-of-ceiling onto
  `AccountUsageRow`) — Gemini uses a different, already-wired mechanism (real-time activity-log RPM/RPD
  counting), not "no gating at all." Both tests (Harsh's bake-off harness, this doc's smoke test) fired
  requests OUTSIDE AO's real `select_account_for_spawn` dispatch path, so neither proves AO's own gate
  failed — both prove the same thing: real exhaustion is frequent and easy to hit, external tooling
  that bypasses AO's dispatch path gets no protection from it (expected — that path was never in scope).
- **Real, concrete ceiling numbers, worth recording**: Gemini's public free-tier limits — **20 req/min
  for 3.7-flash, 250K tokens/min for 3.5-flash-lite**. Pacing requests to these known numbers would have
  avoided most of Harsh's washout even without new gating code.
- **Architectural preference for the NVIDIA fix below**: prefer the poller pattern (GLM/DeepSeek's
  shape — write a %-of-ceiling onto the shared `AccountUsageRow` fields) over mirroring Gemini's
  bespoke real-time-counting branch. The poller pattern converges toward ONE real generic primitive
  (already shared by Claude+GLM); another bespoke branch would make a fourth parallel mechanism, not a
  more uniform one. A real `GeminiQuotaPoller` (using the two numbers above) is also a buildable
  follow-up in its own right — not opened as its own todo here (Harsh explicitly left it as an open
  question, not urgent given the bake-off is nearly done) — flagged for the operator to weigh in on
  separately, not decided in this doc.

## Follow-up

- [x] ✅ [BACKEND] P2. **Wire NVIDIA into the shared gate.** Added `nvidia_account_has_rate_headroom()`
      (`server/nvidia_headroom.py`, mirrors `gemini_account_has_rate_headroom()`'s call shape) and wired it into
      `_account_meets_dispatch_headroom()` the same way Gemini is wired. Ceiling:
      `TuningDefaults.nvidia_concurrent_request_ceiling` (`server/config.py`, default 15) — the real measured
      burst-concurrency floor (5/10/15 clean, 20 started failing, this session), NOT the unconfirmed community
      "~40 RPM" figure (kept unchanged as the separate `NVIDIA_RATE_CEILING` the dashboard snapshot still
      reports). Real tests prove a near-ceiling NVIDIA account is excluded from `_pick_headroom_account`'s
      candidate list
      (`tests/test_autospawn.py::test_pick_headroom_account_excludes_near_ceiling_nvidia_account_from_candidates`)
      and from `_account_meets_dispatch_headroom()` directly, plus a regression guard and the selected-event
      logging fix that makes the RPM counter actually increment (`NVIDIA_REQUEST_SELECTED_EVENT` was minted back
      in 2026-08-16 but never logged from a real pick — would have made the new gate a permanent no-op).
      Full `quality-gates.sh` green (4287 passed, 0 failed) before shipping. **Evidence: agent-orchestrator@86cd2066**.
      Repo: agent-orchestrator.
- [x] ✅ [BACKEND] P2. **Build a reactive fallback for Codex/Luna.** `codex_bridge_server.py` now catches a
      rate-limit-shaped exception (`_looks_like_rate_limit_error`, matched against the real NVIDIA/GLM 429
      samples recorded in this doc) at both `run_codex_turn`'s and `_drive_codex_turn`'s SDK call sites and
      writes a cooldown via the SAME `state_store.mark_account_rate_limited()` Claude's `usage_poller.py` uses
      (`TuningDefaults.codex_reactive_rate_limit_cooldown_seconds`, default 300s — explicitly an unconfirmed
      placeholder, no real Codex 429 had been observed live at ship time). Required making this bridge a real DB
      writer for the first time — `scripts/codex-bridge.service`'s `ReadWritePaths` updated to include `data/`
      (**a running instance needs `sudo systemctl daemon-reload && sudo systemctl restart codex-bridge`, or a
      re-run of `install-codex-bridge-service.sh`, to pick this up; until then the reactive write fails closed,
      logged, never crashes**). Real tests prove a simulated 429 — both at the helper-function level and through
      `run_codex_turn`'s own wiring — results in a cooldown `account_is_usable()` correctly honors
      (`tests/test_codex_bridge_server.py`). NVIDIA defense-in-depth on the litellm proxy path was judged NOT
      additionally needed: LiteLLM is a third-party off-the-shelf proxy process outside this codebase (unlike
      `codex_bridge_server.py`, bespoke AO code this fix can instrument directly), and NVIDIA is already covered
      by todo 1's proactive gate above. **Evidence: agent-orchestrator@43f8f828**.

      **CORRECTION (same session, coordinator cross-check against the installed SDK after this shipped)**: this
      doc's "no proactive quota signal exists for Codex... never been confirmed to expose one" claim is WRONG.
      The installed `openai-codex` SDK genuinely models one: `RateLimitWindow` (`used_percent: int`, a real 0-100
      field, plus `resets_at`/`window_duration_mins`) nested in `RateLimitSnapshot.primary`/`.secondary` (almost
      certainly mirroring Claude's five_hour/weekly split), reachable via `AccountRateLimitsReadRequest` ->
      `GetAccountRateLimitsResponse` or pushed via `AccountRateLimitsUpdatedNotification` (confirmed part of the
      SDK's PUBLIC notification union in `openai_codex/models.py`, not just internal generated bindings). See
      `.venv/lib/python3.13/site-packages/openai_codex/generated/v2_all.py` lines 2928 (`RateLimitWindow`), 5737
      (`AccountRateLimitsReadRequest`), 6724 (`RateLimitSnapshot`), 7652 (`AccountRateLimitsUpdatedNotification`),
      8002 (`GetAccountRateLimitsResponse`). What's STILL genuinely true: `boost_multiplier` (the unrelated
      $-metered billing-reconciliation signal, `multi_provider_context_billing_reconciliation_2026_08_16.md`)
      stays `None` — that narrower claim was conflated into the broader "no signal at all" one, which was too
      broad. NOT yet traced: whether a real live call actually populates `RateLimitSnapshot` (a type existing in
      generated bindings doesn't prove a live response carries it), which JSON-RPC method the high-level
      `Codex`/`AsyncCodex` wrapper exposes to request it, or whether `_drive_codex_turn`'s notification stream
      ever receives `AccountRateLimitsUpdatedNotification` in practice. See the new follow-up todo below — the
      reactive-429 fix above stays valid, real, tested defense-in-depth regardless of whether the proactive path
      also gets built. Repo: agent-orchestrator.
- [x] ✅ [REVIEW] P3. **Live-verified: `tmux_pruner.py`'s pane-text rate-limit scanner is a genuine no-op for a
      non-Claude-shaped error message.** Fed the real GLM and NVIDIA 429 pane-text samples from this doc's own
      "Real evidence" section through the ACTUAL `scan_rate_limits_once()` (a real test, not code-inference) —
      confirmed: `_RATE_LIMIT_RE` only matches Claude Code's own two English banner phrases ("You've hit your
      ... limit" / "Stop and wait for limit to reset"); neither raw-JSON sample matches, so the account is never
      marked
      (`tests/test_tmux_pruner_rate_limit_scan.py::test_non_claude_shaped_glm_429_text_is_not_caught_by_the_pane_scanner`
      and the parallel NVIDIA test). **Not fixed inline** (explicitly out of this [REVIEW] todo's bounded
      "verify, don't rebuild" scope) — judged NOT a clean one-line regex-widen given real redundancy questions:
      GLM is already fully covered proactively (`glm_quota_poller.py`), NVIDIA now is too (todo 1 above), and
      Codex now has a MORE reliable exact-exception catch (todo 2 above) than pane-text guessing would ever be;
      whether this exact JSON shape is even representative of what a LiteLLM-backed provider renders into a pane
      was also never independently confirmed. **Evidence: agent-orchestrator@16be42cc14**. Repo:
      agent-orchestrator.
- [x] ✅ [BACKEND] P2. **NEW (found this session — coordinator cross-check against the installed SDK, folded into
      todo 2's evidence above): trace and, if confirmed live, build a real proactive Codex rate-limit poller.**
      Map `RateLimitSnapshot.primary`/`.secondary.used_percent` (see todo 2's corrected evidence for the exact
      SDK types/line citations) straight onto the SAME generic `AccountUsageRow.five_hour_pct`/`weekly_pct`
      fields Claude/GLM already share — needing ZERO new bespoke branch in `_account_meets_dispatch_headroom()`,
      matching this doc's own stated preference (poller pattern over a bespoke branch, see "Independent
      corroboration" above) more closely than even the shipped reactive-429 fix does. First step: find the
      JSON-RPC method name / high-level `Codex`/`AsyncCodex` accessor that actually issues
      `AccountRateLimitsReadRequest` (or confirm `AccountRateLimitsUpdatedNotification` fires on a real session)
      — NOT yet traced, only the type surface was confirmed to exist. Done when: a real (or realistically
      simulated, if live Codex access is as constrained as NVIDIA's paused accounts were) call returns a
      populated `RateLimitSnapshot`, and a poller mirroring `glm_quota_poller.py`'s shape writes it onto
      `AccountUsageRow`.

      **RESOLVED 2026-08-20 — traced and built, real vendor read (not GLM's count-based estimate).** Direct
      source read of the installed `openai_codex` SDK (`.venv/lib/python3.13/site-packages/openai_codex/`)
      confirmed `AccountRateLimitsReadRequest` carries a literal `method: Literal["account/rateLimits/read"]`
      field, and `CodexClient.request(method, params, *, response_model)` — the same generic typed-request
      mechanism `run_codex_turn`/`codex_mcp_proxy.py` already use elsewhere in this bridge — is the real
      transport; the response (`GetAccountRateLimitsResponse.rate_limits`, a real `RateLimitSnapshot`) carries
      `.primary`/`.secondary` `RateLimitWindow` objects each with a real `used_percent` + real
      `window_duration_mins`. `Codex` (the high-level wrapper) has no dedicated method for this call — confirmed
      by reading every method on it — so the new poller reaches into its underlying `CodexClient` via `_client`,
      same private-access pattern this repo's own `glm_quota_poller.py` already uses for a same-package
      sibling. New file `server/codex_rate_limit_poller.py`: classifies `primary`/`secondary` by their REAL
      reported `window_duration_mins` (not positionally — the SDK's own field docs make no ordering guarantee),
      writes onto `AccountUsageRow.five_hour_pct`/`weekly_pct` exactly like GLM/Claude. Runs inside
      `codex_bridge_server.py`'s OWN process (a new `lifespan` context manager) because that's the only process
      with a real authenticated `openai_codex.Codex()` session — wired via a new
      `config.codex_rate_limit_poll_interval_minutes` field (default 5min, mirrors GLM's cadence). 7 new unit
      tests (`tests/test_codex_rate_limit_poller.py`) cover window classification (including the
      reversed-primary/secondary case), a real `GetAccountRateLimitsResponse`/`RateLimitSnapshot`/
      `RateLimitWindow` round-trip through the actual DB write path, and graceful SDK-call-failure handling.
      **Real live verification post-deploy**: `journalctl -u codex-bridge` shows `CodexRateLimitPoller started
      (interval=300s)` — the poller is genuinely running in production. **Evidence:
      agent-orchestrator@25589117c3.** Repo: agent-orchestrator.

- [x] ✅ [OPERATOR] P1. **NEW, found live 2026-08-20 during the rate-limit-poller deploy — self-corrected within
      the same session, not currently blocking.** `journalctl -u codex-bridge` initially showed a real
      `TransportClosedError: Codex process closed stdout` with a captured `stderr_tail` reading
      `codex_models_manager::manager: failed to refresh available models: unexpected status 401 Unauthorized:
      Provided authentication token is expired.` (timestamps ~08:50-09:35 UTC 2026-08-20) — read at first as a
      currently-expired token needing an operator re-login. **Corrected by direct re-check, not assumed**:
      inspecting `~/.codex/auth.json`'s structure (key names/types only, never the token values) showed
      `auth_mode: "chatgpt"` with a standard `access_token`/`refresh_token` pair (the same short-lived-access
      + rotating-refresh-token shape Claude's OWN interactive `/login` path uses —
      `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`'s comparison table — NOT a
      long-lived install-once credential) plus `last_refresh: 2026-08-20T09:21:34Z`, only ~4h before this
      check — meaning the refresh_token silently self-healed shortly after the observed crash. A real live
      probe (`Codex().thread_start(...).run(...)` — the exact construction `run_codex_turn`/the new poller
      use) confirmed a genuine turn succeeding right now (`"alive"`), not a stale/cached success. **Net: the
      401 was a real, transient failure (not yet root-caused — network blip vs. a race between concurrent
      codex subprocess launches are both plausible, neither confirmed), auto-recovered via the CLI's own
      refresh logic, and is NOT currently blocking anything.** Left open as a real, unresolved question for a
      future session: whether `auth_mode: "chatgpt"` (session-based, needs periodic silent refresh, apparently
      not always reliable) should be swapped for an API-key-based login (`auth.json`'s own `OPENAI_API_KEY`
      field, currently `null`; the SDK exposes `Codex().login_api_key()` / `ApiKeyLoginAccountParams` for
      exactly this) — that would remove the refresh dependency entirely, mirroring Claude's own
      `setup-token`/`ANTHROPIC_API_KEY` split, but shifts billing from whatever ChatGPT plan is behind the
      current login to metered OpenAI API credits. An operator decision (cost tradeoff), not something to
      switch unilaterally. Repo: agent-orchestrator.
- [ ] [BACKEND] P3. **Stronger proof, if wanted**: reproduce the NVIDIA 429 through a real (isolated,
      non-fleet) AO dispatch path end-to-end and confirm via the instance's own `activity_log`/
      `AccountUsageRow` whether anything gets recorded — the piece explicitly not done in this doc (see
      "What was NOT done" above). Not urgent — the code-trace + real-429 combination already
      establishes the gap; this would only sharpen the proof. **DEFERRED this session**: todos 1-3 above plus
      the new proactive-Codex-poller todo consumed the available effort; this todo was already marked
      not-urgent in this doc's own original text, so left open rather than rushed. **NOTE 2026-08-20: NVIDIA
      accounts are now deregistered** (superseded by self-hosted Ollama Gemma, kimi_gemma_provider_
      onboarding_2026_08_16.md) — the NVIDIA-specific half of this todo is now unreproducible-by-construction,
      not merely deferred. The adjacent real end-to-end proof this todo asked for WAS achieved for the
      NVIDIA-hosted path before deregistration (real backlog task dispatched via `switch_slot_account`,
      completed successfully, closed a real CI escalation — see 2026-08-20 entry below for the fuller
      round-robin validation this was part of). Leaving this line item open only as a historical record;
      no further action possible against it. Repo: agent-orchestrator.

- [x] [BACKEND] P1. **Real, separate production bug found + fixed 2026-08-20: codex-bridge 501'd every
      interactive turn, not just resumed ones** — the actual reason Codex/Luna never completed a real turn
      as an AO worker. Root-caused via a full real-provider round-robin validation pass (all 13 previously-
      paused non-Claude accounts force-enabled on the live production VM and dispatched real backlog work):
      a normal interactive Claude Code session always sends `stream: true`, and `codex_bridge_server.py`
      unconditionally 501'd on it ("does not support streaming yet") — confirmed live via `journalctl` on
      the production `codex-bridge.service`, `POST /v1/messages?beta=true` consistently 501ing on every
      real AO-spawned codex-luna worker's first turn. Fixed with real (single-shot, not token-incremental —
      Codex's own SDK exposes no token-level streaming to forward) Anthropic SSE framing
      (`_stream_single_shot_response`), verified live post-fix: `codex_bridge: tool-enabled turn driving
      thread_id=...` with the MCP proxy healthy, all 200/202s, zero 501s. A separate, narrower bug was fixed
      first and shipped separately: `AnthropicMessage.role` only accepted `user`/`assistant`, rejecting a
      `--resume`'d session's inline system-role message with a 400 — real but NOT the reason a *fresh*
      spawn also failed identically, which is what led to finding the streaming gap. Both fixes + a real
      regression test asserting the actual SSE event sequence: **Evidence: agent-orchestrator@39604c9ced**
      (streaming) and **agent-orchestrator@7a1be88b8c** (system-role + a separate `switch_slot_account`
      missing-`model_flag_for_provider` bug found in the same pass). Repo: agent-orchestrator.

## 2026-08-20 — full provider round-robin validated live on production

Real, evidenced status of the fleet-wide round robin this doc's own summary worried would "get stuck on a
single exhausted model": every registered provider now has at least one REAL completed backlog task proven
through actual AO dispatch on the production VM (not a standalone SDK call) — DeepSeek (multiple), GLM,
Gemini, Codex/Luna (post the P1 fix above), and Gemma via NVIDIA-hosting (before its 2026-08-20
deregistration in favor of self-hosted Ollama — separately timeout-tuned,
**agent-orchestrator@d6fc37c0cb**, see kimi_gemma_provider_onboarding_2026_08_16.md). Three more real,
narrow production bugs found and fixed along the way, all shipped and independently re-verified live
post-deploy: `switch_slot_account` never remapping `--model` per-provider (a known bug class,
`ao_deepseek_model_flag_misalignment_2026_08_05`, one call site missed); `test_resource_history.py` using
local `date.today()` against production code that correctly uses `datetime.now(UTC).date()` — a real,
deterministic failure at the UTC/local date boundary that was blocking `quickmerge`'s re-gate fleet-wide,
not just for this work; and the GLM boost-multiplier reconciliation (`compute_flat_rate_boost_reconciliation`)
never computing for GLM specifically because its poller writes a rolling `weekly_pct` estimate with no fixed
`weekly_window_start` to anchor the existing fixed-cycle window logic — fixed via a synthetic trailing-7-day
window, real tests added (`tests/test_flat_rate_boost_reconciliation.py`). **Evidence:
agent-orchestrator@c48e37e281**. A separate, real, transient coverage-ratchet baseline drift (unrelated to
any of the above — confirmed via a YAML-only diff triggering the identical failure) was also realigned
(**agent-orchestrator@90b372ea9f**) since it was blocking quickmerge fleet-wide, not just this work.

- [x] ✅ [BACKEND] P2. **New, found live 2026-08-20**: `switch_slot_account`'s
      `--resume`-onto-a-different-provider path breaks a large existing Claude session on GLM specifically —
      slot 7's forced Claude→GLM switch hit a real context-compaction failure immediately on resume ("Prompt
      is too long · automatic compaction failed"), while the SAME switch onto Gemini/Gemma completed a real
      turn successfully first, only failing on a LATER unrelated bug (the stale-`--model` issue, already
      fixed as agent-orchestrator@7a1be88b8c). Not yet root-caused to the same precision as the codex-bridge
      streaming bug above — plausible working theory, unconfirmed: a `--resume`'d Claude Code session may
      carry provider-specific compaction/context-window assumptions baked into its own local session state
      that don't transfer cleanly to GLM's real context window, independent of anything AO's own spawn code
      controls. Operator-flagged non-urgent relative to the codex-bridge/ollama-thinking findings above and
      below. Organic (fresh-spawn, no resume) dispatch onto GLM is confirmed unaffected — this is
      resume-path-specific.

      **ROOT-CAUSED and FIXED 2026-08-20, real precision this time.** `--resume`'ing a saturated
      transcript triggers Claude Code's OWN client-side automatic-compaction-on-resume — that compaction
      call has to read the ENTIRE saturated history first (same as any `/compact`), so if the resumed
      session was already near its context ceiling, the compaction call itself fails, surfacing as the
      observed "Prompt is too long · automatic compaction failed" immediately on reconnect, independent of
      which provider it lands on. The REAL bug: this codebase already has an established, tested gate for
      exactly this — `resume_fresh_context_pct` (`worker_liveness_watchdog._resume_or_fresh_respawn`,
      `resume_lifecycle.classify_dead_worker`, `autospawn`'s own resume path, even
      `main_agent_keeper.switch_main_account`) all refuse to `--resume` a session at/above this threshold —
      but `switch_slot_account`/`switch_slot_model` (the two OPERATOR-emergency levers, `slots_ops.py`) were
      the ONE pair of call sites that `--resume`'d unconditionally, bypassing it. Fixed by extracting a
      shared `_refuse_resume_if_saturated()` guard (both endpoints are structural twins) that raises a 409
      BEFORE killing the current session when `context_used_pct >= resume_fresh_context_pct` — the old
      behavior killed the live, still-working session FIRST and only then discovered the resume was doomed,
      leaving the slot with no live session at all instead of the operator's original one; the fix leaves
      the original session completely untouched and tells the operator to use `/spawn` for a fresh start
      instead. Found and fixed the SAME gap in `switch_slot_model` in the same pass (adjacent, same file,
      same root cause — an operator switching just the model on a saturated slot was equally exposed).
      2 new unit tests (`tests/test_switch_account.py`, `tests/test_switch_model.py`) confirm the 409 fires
      and the live session/account/model are left genuinely untouched. **Evidence:
      agent-orchestrator@25589117c3.** Repo: agent-orchestrator.

- **context-scout 2026-08-20**: refreshed context_scope (6 entries)
