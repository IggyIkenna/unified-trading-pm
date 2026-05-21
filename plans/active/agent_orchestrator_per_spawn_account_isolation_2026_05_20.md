---
title: agent-orchestrator per-spawn account isolation (HOME-shim) — SUPERSEDED
parent_epic: orchestrator_master
priority: P2
status: paused
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-05-20
related_plans:
  - agent_orchestrator_workers_on_vms_2026_05_19.md
  - master_to_live_defi_2026_05_23.md
---

# Agent-Orchestrator Per-Spawn Account Isolation (HOME-shim)

> **SUPERSEDED 2026-05-21** by `orchestrator_master.md` § Auth & accounts r3 + Phase 4 r3. `claude setup-token` produces
> a 1-year long-lived OAuth token via `CLAUDE_CODE_OAUTH_TOKEN` env var — bypassing the
> `.credentials.json`-file-contention problem this plan was designed to solve. No further work needed here.

This plan proposed a HOME-shim approach for per-spawn account isolation (each spawned Claude agent gets its own
`~/.claude/` HOME via `HOME=/tmp/agent-N`). Superseded by the simpler OAuth token env-var path.

Codex SSOTs: `codex/04-architecture/agent-orchestrator-overview.md`

---

## Status

All work in this plan is SUPERSEDED. No further phases needed.

## Temporary states + canonical follow-up plans

- Superseded by: `orchestrator_master.md` § Auth & accounts r3 + Phase 4 r3 (operator-confirmed 2026-05-21).
