---
doc_type: plan
title: D0 — orchestrator-service → agent-orchestrator migration
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/agent_orchestrator_cloud_run_deployment_2026_05_19.md,
    /plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
  ]
created: "2026-05-20"
parent_epic: orchestrator_master
priority: P0
archived_at: 2026-05-21
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
locked_by: live-defi-rollout
locked_since: 2026-05-20
---

> ## ARCHIVED 2026-05-21
>
> All phases complete. Port 8026 aligned across service/dev/demo configs. CORS confirmed (agent-orch@`8daa12d`).
> LEDGER.md deprecation headers added. CLAUDE.md updated with prod URL. Archiving under orchestrator_master.

# D0 — Orchestrator-Service Migration

Port alignment, CORS, LEDGER.md deprecation for the orchestrator-service → agent-orchestrator rename. Ensures all
workspace configs consistently use port 8026 and the new `agent-orchestrator.odum-research.com` domain.

Codex SSOTs: `/codex/04-architecture/agent-orchestrator-overview.md`

---

## Phase 1 — Port 8026 alignment

- [x] ✅ [AGENT] P2. Align orchestrator port: updated `scripts/orchestrator.service`, `scripts/dev.sh`,
      `scripts/orchestrator-demo.service`, `scripts/populate_demo.py` from 8765 → 8026. App.tsx BOOTSTRAP_URL also
      updated. agent-orch@tab/ikennaigboaka/1 2026-05-21.

## Phase 2 — CORS + CLAUDE.md update

- [x] ✅ [AGENT] P2. `agent-orchestrator.odum-research.com` already in CORS allowed origins via `_default_cors_origins`
      in `server/server.py` (shipped earlier, commit `8daa12d`). No additional change needed.
- [x] ✅ [AGENT] P2. Update CLAUDE.md orchestrator reference to confirm port 8026 is the deployed port; add prod URL.
      Already present: "port 8026 locally; `agent-orchestrator.odum-research.com` prod" in "Key repo map" § System-First
      Architecture. Verified 2026-05-21 — all workspace CLAUDE.md symlinks confirmed. No code change needed.

## Phase 3 — LEDGER.md deprecation header

- [x] ✅ [AGENT] P3. `ikenna_orchestrator/LEDGER.md` and `harsh_orchestrator/LEDGER.md` annotated with deprecation
      banner: "⚠️ OFFLINE FALLBACK ONLY — primary work-split surface is the agent-orchestrator dashboard."
      pm-repo@tab/ikennaigboaka/1 2026-05-21.

## Success criteria

- [x] ✅ Port updated to 8026 across service template, dev script, demo service, and App.tsx.
- [x] ✅ `curl -H "Origin: https://agent-orchestrator.odum-research.com" -I http://localhost:8026/health` returns
      `Access-Control-Allow-Origin: https://agent-orchestrator.odum-research.com`. CORS verified at agent-orch@`8daa12d`
      (`_default_cors_origins` includes `agent-orchestrator.odum-research.com`). Human verification on local dev ok.
- [x] ✅ LEDGER.md files carry deprecation header (offline fallback, not primary).

## Temporary states + canonical follow-up plans

- Phases 1-3 are low-complexity config cleanups; no downstream dependencies.
