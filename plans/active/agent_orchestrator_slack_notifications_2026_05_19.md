---
title: agent-orchestrator Slack notifications (Block Kit + retry + wiring)
parent_epic: orchestrator_master
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
locked_by: live-defi-rollout
locked_since: 2026-05-19
related_plans:
  - agent_orchestrator_cloud_run_deployment_2026_05_19.md
  - master_to_live_defi_2026_05_23.md
---

# Agent-Orchestrator Slack Notifications

Block Kit upgrade for agent-orchestrator Slack notifications: slot_blocked / slot_stale / slot_failed event types get
header+section+fields+context blocks with retry (3 attempts, backoff) and dashboard link. Phases 1-2 shipped; Phase 3
(Cloud Run secret wiring) + Phase 4 (e2e staging smoke) pending.

Codex SSOTs: `codex/04-architecture/agent-orchestrator-overview.md`

---

## Phase 1 — Audit + scope check

- [x] ✅ [AGENT] P0. Pre-audit: `server/notifications/slack.py` confirmed at LDR HEAD (31-line, plain text, no Block
      Kit). `slot_blocked` / `slot_stale` / `slot_failed` wired in server.py + health.py. httpx in pyproject.toml.
      Secret Manager + Cloud Run SA verified. No tests existed. (agent-orchestrator@`eea2f69`)

## Phase 2 — Block Kit delivery polish

- [x] ✅ [AGENT] P0. `slack.py` upgraded: Block Kit header+section+fields+context for all 3 event types; `text` fallback
      kept; `_post()` retry (3 attempts, backoff 0.5s/1.0s; 4xx aborts immediately); `blocked_id` in signature;
      `ORCHESTRATOR_PUBLIC_URL` for dashboard link; 9 unit tests (retry, 4xx abort, no-op on empty webhook, Block Kit
      shape, link presence); ruff+basedpyright clean. (agent-orchestrator@`cd04fc2`)

## Phase 3 — Cloud Run secret wiring

- [ ] [AGENT] P3. Confirm Cloud Run staging SA has `secretAccessor` on `AGENT_ORCHESTRATOR_SLACK_WEBHOOK`; mount webhook
      secret as env var `ORCHESTRATOR_SLACK_WEBHOOK` via `--set-secrets`; update `deploy-agent-orchestrator.sh` to
      include the secret mount; verify via `gcloud run services describe`.

## Phase 4 — E2E staging smoke test

- [ ] [AGENT] P4. Get valid JWT for staging; `POST` to blocked endpoint with test question; verify Slack message lands
      in `#agent-orchestrator-alerts` within 10s.

## Temporary states + canonical follow-up plans

- Phase 3+4 gated on Cloud Run staging service being up (Phase 1 of cloud_run_deployment plan).
- Other 5 Slack secrets (APP_ID, CLIENT_ID, CLIENT_SECRET, SIGNING_SECRET, VERIFICATION_TOKEN): post-Phase 3 scope.
