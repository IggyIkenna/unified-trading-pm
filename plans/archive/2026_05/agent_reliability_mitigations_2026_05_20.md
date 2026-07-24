---
doc_type: plan
title: Agent reliability mitigations — close the multi-agent loop gaps (2026-05-20)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: []
related:
  [
    agent_orchestrator_workers_on_vms_2026_05_19.md,
    /plans/archive/2026_05/agent_orchestrator_cloud_run_deployment_2026_05_19.md,
    /plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
  ]
created: "2026-05-20"
parent_epic: orchestrator_master
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-05-20
---

> **ARCHIVED 2026-05-21** — Phases 1-4 complete (mirror-events webhook, dirty-state gate, claim tag, in-flight files).
> Phase 5 (gitignore-on-demand) DEFERRED-POST-CUTOVER.

## Deferred work — migrated to:

- Phase 5 gitignore-on-demand → agent-orchestrator PR post-cutover (ships when VM workers are live; P2 convenience
  feature)

# Agent Reliability Mitigations

Four gap categories for multi-agent orchestration: (1) LDR mirror failures go unnoticed; (2) Spawning into a dirty
worktree causes context confusion; (3) No ownership tag on WIP files causes cross-agent overwrite; (4) No in-flight
files record on heartbeat gap — can't recover what last agent was working on. Five phased mitigations.

Codex SSOTs: `/codex/04-architecture/agent-orchestrator-overview.md`

---

## Phase 1 — Mirror-failure → orchestrator alert

- [x] ✅ [AGENT] P0. `POST /api/mirror-events` (no auth — webhook) + `GET /api/mirror-events` (authed) shipped in
      `server/server.py`. `mirror_events` table; `slot.mirror_blocked_at` set on non-ff decisions. agent-orch (shipped
      prior to 2026-05-21 session).
- [x] ✅ [AGENT] P0. `tab-mirror-to-ldr.yml` adds final step POSTing result to `/api/mirror-events` — fire-and-forget,
      exits 0 either way. Rolled out PM@b0af9ba3a. Verified deployed to 8/8 repos with tab-mirror-to-ldr.yml.

## Phase 2 — Pre-spawn dirty-state gate

- [x] ✅ [AGENT] P1. `worktree_clean_check.py` shipped — `check_all_worktrees(slot_id)` runs `git status --porcelain`
      across all repos under `.tabs/<slot_id>/`; `spawn_slot()` calls it before tmux launch; HTTP 409 on dirty.
      agent-orch (shipped prior to 2026-05-21 session).

## Phase 3 — Per-agent `.agent-claim` ownership tag

- [x] ✅ [AGENT] P1. `worktree_claim.py` shipped — writes `.tabs/<N>/.agent-claim` JSON on `spawn_slot`; heartbeat
      updates `expires_at`; `GET /api/slots/<N>/claim` endpoint exists. agent-orch (shipped prior to 2026-05-21).

## Phase 4 — Per-slot heartbeat `in_flight_files`

- [x] ✅ [AGENT] P2. `HeartbeatRequest` carries `in_flight_files: list[InFlightFile]`; slot row stores latest list
      (`in_flight_files_json`). Models + server both updated. agent-orch (shipped prior to 2026-05-21).

## Phase 5 — Gitignored-on-demand pattern

- [x] ✅ [AGENT] P2. Replicate Harsh's local gitignored-on-demand pattern for Ikenna-side + VMs. Script: auto-adds
      `.gitignore` entries for files that have been WIP >30min without a commit. Composes with Phase 2 dirty-state gate.
      **[DEFERRED-POST-CUTOVER 2026-05-21]** — Requires code in agent-orchestrator (outside unified-trading-pm scope).
      Ships as agent-orchestrator PR when VM workers are live. No named successor plan needed (P2 convenience feature).

## Temporary states + canonical follow-up plans

- Phase 1 webhook: backend tolerates 503 until backend is deployed (workflow calls endpoint fire-and-forget).
- Phases 3-4 compose together: claim file = identity anchor; heartbeat in-flight = recovery list.
