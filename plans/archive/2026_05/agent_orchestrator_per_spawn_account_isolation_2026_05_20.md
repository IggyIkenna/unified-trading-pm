---
doc_type: plan
title: agent-orchestrator per-spawn account isolation (HOME-shim) — SUPERSEDED
summary:
status: superseded
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: []
related: [agent_orchestrator_workers_on_vms_2026_05_19.md, /plans/active/master_to_live_defi_2026_05_23.md]
created: "2026-05-20"
parent_epic: orchestrator_master
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-05-20
---

## Deferred work — migrated to:

| Item                                                                                      | Successor plan                                                           |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 4b-cleanup: remove legacy credential-swap code once harsh-primary migrates to setup-token | [`orchestrator_master.md`](../epics/orchestrator_master.md) § 4b-cleanup |

# Agent-Orchestrator Per-Spawn Account Isolation (HOME-shim)

> **ARCHIVED 2026-05-21** — SUPERSEDED by oauth token env-var approach (`CLAUDE_CODE_OAUTH_TOKEN`). No further work
> needed. 0 open todos. status: paused → archived.

> **SUPERSEDED 2026-05-21** by `orchestrator_master.md` § Auth & accounts r3 + Phase 4 r3. `claude setup-token` produces
> a 1-year long-lived OAuth token via `CLAUDE_CODE_OAUTH_TOKEN` env var — bypassing the
> `.credentials.json`-file-contention problem this plan was designed to solve. No further work needed here.

This plan proposed a HOME-shim approach for per-spawn account isolation (each spawned Claude agent gets its own
`~/.claude/` HOME via `HOME=/tmp/agent-N`). Superseded by the simpler OAuth token env-var path.

Codex SSOTs: `/codex/04-architecture/agent-orchestrator-overview.md`

---

## Status

All work in this plan is SUPERSEDED. No further phases needed.

## Temporary states + canonical follow-up plans

- Superseded by: `orchestrator_master.md` § Auth & accounts r3 + Phase 4 r3 (operator-confirmed 2026-05-21).
