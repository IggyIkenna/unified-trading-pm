---
doc_type: issue
title: >-
  orchestrator.service crash-loop paged nobody for ~6 minutes (2026-08-20) — no watchdog exists for "is the
  orchestrator process itself alive"; separately, the LiteLLM proxy's /health endpoint returns 500, unchased
summary: >-
  Live incident 2026-08-20: an unrelated push (git-staleness alerting fix) triggered ao-self-pull's routine restart,
  which crash-looped on a pre-existing config/code mismatch (two `provider: "grok"` accounts in the live, gitignored
  `data/config/accounts.json` that the AccountDef schema rejected). Root cause fixed same session (accounts removed,
  `load_accounts()` hardened to skip one malformed entry instead of crashing the whole service,
  `agent-orchestrator@868062b82f`). This doc tracks the two things that fix did NOT address: (1) the service was down
  for ~6 minutes with zero paging — nothing watches "is the orchestrator process itself alive," a structural gap since
  a crashed orchestrator cannot page about its own crash; (2) a related LiteLLM proxy health-check anomaly noticed
  during the same session's Grok-removal verification, not investigated.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, alerting, watchdog, incident, litellm]
related:
  [
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/15-runbooks/safe-service-restart-procedures.md,
    /plans/active/grok_gemini_translation_proxy_2026_08_14.md,
  ]
created: "2026-08-20"
last_updated: "2026-08-20"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /codex/04-architecture/agent-orchestrator-alerting.md,
    agent-orchestrator/server/accounts.py,
    agent-orchestrator/config/litellm/grok_gemini_proxy.yaml,
  ]
source: >-
  Interactive session, 2026-08-20 — live incident response (dashboard reported "cannot load") plus a residual
  observation surfaced during the same session's Grok-removal verification pass.
---

# orchestrator.service crash-loop had zero alerting; LiteLLM proxy /health anomaly unchased

## What happened (root cause already fixed, this doc tracks what wasn't)

19:12:31–19:18:18 UTC: `orchestrator.service` crash-looped every ~17s on
`pydantic_core.ValidationError: ... input_value='grok'` (two live accounts with `provider: "grok"` in
`data/config/accounts.json`, gitignored/VM-local, never version-controlled — a leftover from before Grok was
decommissioned that survived because that file isn't in git). Discovered only because the operator manually noticed
the dashboard wouldn't load. Fixed: removed the two accounts, hardened `accounts.py::load_accounts()` to skip one
malformed entry with a loud log instead of crashing the whole load (`agent-orchestrator@868062b82f`, tests added).

## Gap 1 — no watchdog for "is the orchestrator process itself alive"

Every alerting mechanism this fleet has (`notify_*` functions, the escalation queue, scheduled-job status) is emitted
*by* the orchestrator process. None of it can fire while the process itself is down or crash-looping — the fleet has
no external heartbeat/dead-man's-switch watching the orchestrator host from outside the orchestrator's own process.
A 6-minute outage with zero pages is the direct, measured consequence.

- [ ] [INFRA] P1. Design + implement an external liveness check for `orchestrator.service` itself — a systemd
      `OnFailure=` unit, or a separate lightweight cron/timer on the same VM that polls `/api/healthz` and pages
      Slack directly (bypassing the orchestrator's own notification path, which is exactly what's unavailable when
      this fires) on N consecutive failures. Cite `/codex/04-architecture/agent-orchestrator-alerting.md` for the
      channel/dedup conventions to follow. (repo: agent-orchestrator)

## Gap 2 — LiteLLM proxy `/health` returns 500, not investigated

During the same session's Grok-removal verification, a bare unauthenticated `curl` against the LiteLLM proxy's
`/health` route returned `http_code=500`. Plausibly benign (LiteLLM's health route needing auth or a real backend
probe rather than a bare unauthenticated hit) but not confirmed either way — flagged as observed, not investigated.

- [ ] [INFRA] P3. Confirm whether the LiteLLM proxy's `/health` 500 is expected (auth-gated) or a real problem —
      check `litellm-grok-gemini-proxy.service`'s logs at the time of a real `curl` attempt, and confirm the Gemini
      routing it actually serves works via a real completion, not just the health route. (repo: agent-orchestrator)

## Progress Log

- **2026-08-20**: doc authored during pre-compact checkpoint, capturing two residual findings from the day's
  incident-response + Grok-removal sessions that hadn't been tracked as todos yet.
