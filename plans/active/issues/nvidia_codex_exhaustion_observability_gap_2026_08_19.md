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
last_updated: "2026-08-19"
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
| **NVIDIA/Gemma** | RPM (shared per key, measured today: 15-20 concurrent breaking point) | **Nowhere.** `nvidia_headroom.py` computes and DISPLAYS it (`GET /api/accounts/nvidia/capacity`) but nothing calls it from dispatch logic | ❌ |
| **Codex/Luna** | Unknown — no API signal exists at all (`boost_multiplier` stays permanently `None`, confirmed in `multi_provider_context_billing_reconciliation_2026_08_16.md`) | **Nowhere**, proactively or reactively | ❌ |

So today there are really **three different real mechanisms**, not one uniform one:
1. Generic pct-ceiling fields (Claude, GLM) — the closest thing to a real uniform primitive.
2. Per-provider bespoke branch inside the shared gate (Gemini only).
3. An entirely separate, parallel code path outside the shared gate (DeepSeek only).

And NVIDIA/Codex have none of the three.

## The reactive fallback doesn't save NVIDIA/Codex either

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

- [ ] [BACKEND] P2. **Wire NVIDIA into the shared gate.** Add `nvidia_account_has_rate_headroom()`
      (`server/nvidia_headroom.py`, mirroring `gemini_account_has_rate_headroom()`'s shape) and call
      it from `_account_meets_dispatch_headroom()` the same way Gemini is called today. Use the real
      measured breaking point (15-20 concurrent requests, this session) as the starting ceiling, not
      the unconfirmed community-reported "~40 RPM" figure — flag it as `ceiling_confirmed=false` still
      if no sustained-rate (not just burst) measurement exists. Done when: a simulated near-ceiling
      NVIDIA account is excluded from `_pick_headroom_account`'s candidate list, same proof shape as
      GLM's own todo in `deepseek_claude_blended_provider_routing_2026_07_28.md`. Repo:
      agent-orchestrator.
- [ ] [BACKEND] P2. **Build a reactive fallback for Codex/Luna** (and confirm/build the same for
      NVIDIA as defense-in-depth). No proactive quota signal exists for Codex — OpenAI's ChatGPT
      Plus/Codex API has never been confirmed to expose one. The realistic fix is reactive: catch a
      real 429/rate-limit-shaped error response from `codex_bridge_server.py` (or the litellm proxy
      for NVIDIA) and set a cooldown via the SAME mechanism Claude's `rate_limited_until` uses, rather
      than requiring `usage_poller.py`'s Claude-only path. Done when: a simulated 429 from either
      provider results in a real cooldown that `account_is_usable()` then correctly honors.
      Repo: agent-orchestrator.
- [ ] [REVIEW] P3. **Live-verify (or disprove) whether `tmux_pruner.py`'s pane-text rate-limit scanner
      catches a non-Claude-shaped error message at all.** Not confirmed either way this session — the
      regex LOOKS Claude-specific but the outer scan doesn't branch on provider, so this needs a real
      check (feed a real GLM/NVIDIA 429 pane-text sample through `scan_rate_limits_once()` and see
      what happens), not an assumption from reading the regex alone. Repo: agent-orchestrator.
- [ ] [BACKEND] P3. **Stronger proof, if wanted**: reproduce the NVIDIA 429 through a real (isolated,
      non-fleet) AO dispatch path end-to-end and confirm via the instance's own `activity_log`/
      `AccountUsageRow` whether anything gets recorded — the piece explicitly not done in this doc (see
      "What was NOT done" above). Not urgent — the code-trace + real-429 combination already
      establishes the gap; this would only sharpen the proof. Repo: agent-orchestrator.
