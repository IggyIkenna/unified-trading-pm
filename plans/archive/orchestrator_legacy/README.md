# Orchestrator legacy (Harsh side) — RETIRED 2026-05-25

> **DEPRECATED / ARCHIVE — do not wire anything to these files.**
> This is the retired file-based orchestration mechanism for the Harsh side. The
> authoritative work-split surface is now the **agent-orchestrator dashboard**
> (FastAPI + Vite, `:8026` local / `agent-orchestrator.odum-research.com` prod).
> SSOT: `codex/04-architecture/agent-orchestrator-overview.md`.

## Why this was archived

The dashboard cutover (see `plans/archive/2026_05/d0_orchestrator_migration_2026_05_20.md`)
moved slot status, backlog, and account state into the orchestrator's own SQLite + config
(`agent-orchestrator/data/config/`). These files became offline-fallback-only and then
unused. The running dashboard reads `backlog.yaml` / `accounts.json` from
`agent-orchestrator/data/config/` — **never** from here — so nothing live depends on this
folder.

## What moved here (Half A — dead, harsh-only)

| File / dir | Was |
|---|---|
| `harsh_orchestrator/LEDGER.md` | offline-fallback shift ledger |
| `harsh_orchestrator/BACKLOG.md`, `backlog.yaml` | curated dispatch queue (superseded by dashboard plan-auto-extraction) |
| `harsh_orchestrator/accounts.json` | account config (live copy lives in `agent-orchestrator/data/config/`) |
| `harsh_orchestrator/pings/` | per-slot intra-side ping ledger (stale) |
| `harsh_orchestrator/AGENT_ONBOARDING.md` | superseded by `agent-orchestrator/agents/*.md` |
| `harsh_orchestrator/{HARSH_WAKEUP_*,CONTINUATION_PROMPTS_TEMPLATE,THEMATIC_CLUSTERS,poll_main_prompt}.md` | one-off prompts/templates |
| `harsh_orchestrator/acks/` | rules-refresh ack tracking |
| `scripts/harsh_auto_poll.sh` | harsh-only auto-poll driver (was never scheduled) |

## What did NOT move (Half B — still live, intentionally left in place)

These stay at `unified-trading-pm/harsh_orchestrator/` and `scripts/agents/` because two
**ENABLED** prod Cloud Scheduler jobs still read them on every run (they `git clone`
`live-defi-rollout` and iterate both sides' ping inboxes):

- `harsh_orchestrator/_agent_pings.md` — read by `uts-prod-plan-hygiene-sweep-cron`
  (daily 05:00 UTC) and `uts-prod-orphan-ping-audit-cron` (every 4h).
- `scripts/agents/audit_ping_orphans.sh` + `scripts/agents/cron_orphan_ping_audit_entrypoint.sh`
  — shared cross-side scripts (read `ikenna_orchestrator/` + `harsh_orchestrator/` inboxes).

Retiring Half B requires editing those shared entrypoints to stop iterating the per-side
inboxes (canonical inbox is `plans/active/_agent_pings.md`), disabling/`terraform apply`-ing
both schedulers, and coordinating the symmetric `ikenna_orchestrator/` side — a deliberate
cross-side change, not a quiet move.

## Recovery

Everything here is in git history at its original path; `git log --follow` from any file
recovers full provenance.
