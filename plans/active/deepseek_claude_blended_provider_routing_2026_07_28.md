---
doc_type: plan
title: DeepSeek/Claude blended provider routing for agent-orchestrator
summary:
  Register DeepSeek V4 Pro as a second, first-class model provider in agent-orchestrator's account pool, and add a
  routing layer so AutoSpawn decides per-task whether a fresh spawn uses DeepSeek or a Claude Max account — a real
  policy (model-tier eligibility + tunable split + health gate), not blending it into the existing usage%-based
  Claude-account ranking, which would greedily over-select a pay-per-token account every tick.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, deepseek, model-routing, multi-provider, cost-optimization, reliability]
related:
  [
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/06-coding-standards/model-tier-selection.md,
  ]
created: 2026-07-28
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
supersedes:
superseded_by:
source:
---

# DeepSeek/Claude blended provider routing for agent-orchestrator

## Why

Operator goal: reduce Claude Max token spend and outage exposure across the ~14 parallel AO slots by running some spawns
on DeepSeek V4 Pro instead of Anthropic, decided automatically per task (not a mid-session switch — that's explicitly
out of scope for this plan; see "Non-goals").

**Codex SSOTs this plan depends on** (read before touching the cited code):

- `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` — the `oauth_token_env_file` +
  `CLAUDE_CODE_OAUTH_TOKEN` setup-token contract every account currently assumes.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — worker lifecycle + dispatch model this
  routing layer plugs into.
- `/codex/04-architecture/agent-orchestrator-overview.md` — account auth model, `AgentKeeper`, fleet-cap semantics.
- `/codex/06-coding-standards/model-tier-selection.md` — the `sonnet < opus < fable` tier semantics this plan's
  eligibility gate reuses (`opus-required` is qualitative judgment work only, never routed to DeepSeek).

**Findings from a live code read (2026-07-28) that this plan exists to fix, not just add to:**

1. `server/usage_poller.py::_tick_once()` regex-scrapes every account's env file for `CLAUDE_CODE_OAUTH_TOKEN`
   (`usage_tracker.py`'s `_TOKEN_RE`) to poll `/usage`-style quota. An account without that token (any DeepSeek entry,
   by design) hits the `parsed.raw_text_preview == "no token"` branch (`usage_poller.py:377-379`), which calls
   `self._alert_account_auth_failed(...)` and `self._mark_auth_failed_db(...)` — the SAME status
   `_pick_headroom_account()` uses to exclude an account from automatic selection. Adding a DeepSeek account to
   `accounts.json` with no further change gets it marked broken within one poll tick.
2. `server/autospawn.py::_pick_headroom_account()` (called from the main AutoSpawn loop and two other automatic spawn
   paths) ranks **every** account in `accounts.json` by `(five_hour_pct, weekly_pct, active_slot_count)` ascending and
   picks the lowest. A DeepSeek account has no such usage-cap concept — if finding 1's `auth_failed` marking is fixed
   without also addressing this, a DeepSeek entry would read as a permanently-idle "0% used" account and get greedily
   picked for nearly every automatic spawn, starving the 4 Claude accounts of dispatch. Blending providers into this
   ranking function is the wrong fix; a task/tier-aware routing layer in front of it is the right one (see Track 1
   below).
3. The codex SSOT `claude-cli-multi-account-headless-auth.md` and prior session notes referenced a
   `POST /api/slots/{id}/rotate-account` endpoint for manual account switching. Grepped the live code
   (`routes/slots_ops.py`, `server.py`) 2026-07-28: **no such route exists.** The real mechanism is
   `POST /api/slots/{id}/reassign` (kills the session) followed by `POST /api/slots/{id}/spawn` with a different
   `account_id` (starts a fresh session, no conversation resume). Out of scope for this plan to fix the codex drift
   itself, but any todo below that touches manual account switching should use the real mechanism, not the documented
   one.

## Non-goals

- **Mid-session / live model switching is explicitly out of scope.** `ANTHROPIC_BASE_URL` is read once at `claude`
  process launch (confirmed via Anthropic's own GitHub issue tracker); crossing providers requires a fresh spawn. This
  plan only covers **which provider a fresh spawn uses**, decided automatically at spawn time.
- Not touching the interactive Claude Code CLI or VS Code extension surfaces — operator is exploring those manually,
  separately.
- Not fixing the `claude-cli-multi-account-headless-auth.md` doc-vs-code drift on the `rotate-account` endpoint (finding
  3 above) — flagged for a separate, smaller doc-correction pass.

## Design summary

A new `select_account_for_spawn(task_context)` function sits in front of the existing `_pick_headroom_account()`:

1. **Eligibility** — only `sonnet`-tier tasks are DeepSeek-eligible. Any `opus`/`fable`-tier task always routes to the
   existing Claude-only pool, unconditionally (reuses `model_tier.py`'s existing rank — no new judgment call).
2. **Split** — an operator-tunable `tuning.deepseek_route_fraction` config value (start conservative) decides what
   fraction of _eligible_ spawns go to DeepSeek. Round-robin counter, not randomness, so behavior is predictable and
   debuggable during the pilot.
3. **Health gate** — before routing to DeepSeek, check its recent spawn-failure count (mirrors the existing
   `_SPAWN_FAILED_ALERTED` dedup-state pattern already used for spawn failures). Falls back to the Claude pool
   automatically if DeepSeek looks unhealthy — this is what makes the blend a reliability win, not just a cost split.
4. The Claude branch delegates to the **existing, unmodified** `_pick_headroom_account()` ranking, scoped by one added
   `provider == "anthropic"` filter.

## Progress Log

_(none yet — plan just authored 2026-07-28)_

## Todos

- [ ] [INFRA] P0. Add a `provider: Literal["anthropic", "deepseek"] = "anthropic"` field to the `Account` model
      (`server/models/accounts.py`) and document it in `accounts.json`'s schema comment block. Done when: all 4 existing
      accounts parse with the implicit `anthropic` default, and a test account declaring `provider: "deepseek"` also
      parses cleanly with no other required-field errors.
- [ ] [INFRA] P0. Guard `usage_poller.py::_tick_once()` so any account with `provider != "anthropic"` skips the
      `CLAUDE_CODE_OAUTH_TOKEN` probe entirely — no `no token` branch, no `_alert_account_auth_failed`/
      `_mark_auth_failed_db` call for it. Done when: a `provider: "deepseek"` test account survives several consecutive
      poller ticks without being marked `auth_failed`.
- [ ] [INFRA] P0. Register the DeepSeek account end to end: create `~/.claude-accounts/deepseek-v4-pro.env`
      (`ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL=deepseek-v4-pro`, explicit
      `unset CLAUDE_CODE_OAUTH_TOKEN`), add the matching `accounts.json` entry with `provider: "deepseek"`, and push the
      env file to both creds buckets so `CredsEnvPoller` distributes it fleet-wide. Done when:
      `claude -p 'reply AUTH_OK'` sourced against that env file on the orchestrator VM returns `AUTH_OK`.
- [ ] [INFRA] P0. Implement `select_account_for_spawn()` per the Design summary above (eligibility, split via a new
      `tuning.deepseek_route_fraction` config field, health gate reusing the `_SPAWN_FAILED_ALERTED`-style dedup state).
      Done when: unit tests cover all three branches — an `opus`-tier task never routes to DeepSeek across N calls, the
      split ratio is honored within tolerance over N eligible calls, and a simulated recent-failure count on the
      DeepSeek account forces fallback to the Claude pool.
- [ ] [INFRA] P0. Replace the 3 direct `_pick_headroom_account()` call sites in `autospawn.py` (the main AutoSpawn loop
      and the two other automatic spawn paths found this session) with calls into `select_account_for_spawn()`; add the
      `provider == "anthropic"` filter inside `_pick_headroom_account()` itself so its existing ranking logic for the 4
      Claude accounts is otherwise untouched. Done when: the existing autospawn test suite stays green, and a new
      integration test proves a `sonnet`-tier task can land on the DeepSeek account while an `opus`-tier task dispatched
      in the same tick never does.
- [ ] [DATA] P1. Add a spend-guard check before routing to DeepSeek — a config-driven daily/monthly token-spend ceiling,
      mirroring the existing GCP/AWS spend-audit pattern already used elsewhere in this workspace. Done when: a
      simulated over-ceiling day makes `select_account_for_spawn()` stop offering DeepSeek and fall back to Claude, with
      an activity-log event recording why.
- [ ] [UI] P1. Surface `provider` next to `account_id` in the dashboard's slot/account views so it's visible at a glance
      which of the 14 slots are on DeepSeek vs. Claude right now. Done when: the dashboard renders a provider badge per
      active slot.
- [ ] [REVIEW] P2. Pilot the blended pool for one week at the default split fraction, then compare DeepSeek-routed task
      outcomes (QG pass rate, review-flagged rework rate) against the Claude-routed baseline before raising the split.
      Done when: a dated comparison note with the actual pass/rework numbers for both is added to this plan's Progress
      Log.
