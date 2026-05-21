---
title: D0 — orchestrator-service → agent-orchestrator migration
parent_epic: orchestrator_master
priority: P0
status: active
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
locked_by: live-defi-rollout
locked_since: 2026-05-20
related_plans:
  - agent_orchestrator_cloud_run_deployment_2026_05_19.md
  - master_to_live_defi_2026_05_23.md
---

# D0 — Orchestrator-Service Migration

Port alignment, CORS, LEDGER.md deprecation for the orchestrator-service → agent-orchestrator rename. Ensures all
workspace configs consistently use port 8026 and the new `agent-orchestrator.odum-research.com` domain.

Codex SSOTs: `codex/04-architecture/agent-orchestrator-overview.md`

---

## Phase 1 — Port 8026 alignment

- [x] ✅ [AGENT] P2. Align orchestrator port: updated `scripts/orchestrator.service`, `scripts/dev.sh`,
      `scripts/orchestrator-demo.service`, `scripts/populate_demo.py` from 8765 → 8026. App.tsx BOOTSTRAP_URL also
      updated. agent-orch@tab/ikennaigboaka/1 2026-05-21.

## Phase 2 — CORS + CLAUDE.md update

- [x] ✅ [AGENT] P2. `agent-orchestrator.odum-research.com` already in CORS allowed origins via `_default_cors_origins`
      in `server/server.py` (shipped earlier, commit `8daa12d`). No additional change needed.
- [ ] [AGENT] P2. Update CLAUDE.md orchestrator reference to confirm port 8026 is the deployed port; add prod URL.

## Phase 3 — LEDGER.md deprecation header

- [x] ✅ [AGENT] P3. `ikenna_orchestrator/LEDGER.md` and `harsh_orchestrator/LEDGER.md` annotated with deprecation
      banner: "⚠️ OFFLINE FALLBACK ONLY — primary work-split surface is the agent-orchestrator dashboard."
      pm-repo@tab/ikennaigboaka/1 2026-05-21.

## Success criteria

- [x] ✅ Port updated to 8026 across service template, dev script, demo service, and App.tsx.
- [ ] `curl -H "Origin: https://agent-orchestrator.odum-research.com" -I http://localhost:8026/health` returns
      `Access-Control-Allow-Origin: https://agent-orchestrator.odum-research.com`.
- [x] ✅ LEDGER.md files carry deprecation header (offline fallback, not primary).

## Temporary states + canonical follow-up plans

- Phases 1-3 are low-complexity config cleanups; no downstream dependencies.
