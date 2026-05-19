---
name: agent-orchestrator-slack-notifications-2026-05-19
overview:
  Wire Slack push notifications into the agent-orchestrator Cloud Run service — blocked/stale/failed
  slot events POST to #agent-orchestrator-alerts via AGENT_ORCHESTRATOR_SLACK_WEBHOOK (already in
  Secret Manager). Depends on agent_orchestrator_cloud_run_deployment_2026_05_19 P1 (Cloud Run
  staging service must exist before --update-secrets can run).
type: infra
status: active
epic: epic-infra

estimate_class: brand-new
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.0

locked_by: live-defi-rollout
locked_since: 2026-05-19

completion_gates:
  code: C4
  deployment: D3
  business: none

repo_gates:
  - repo: agent-orchestrator
    code: C4
    deployment: D3
    business: none

depends_on:
  - agent_orchestrator_cloud_run_deployment_2026_05_19  # P1 must be complete (Cloud Run service must exist)

owner: harsh
cadence: ad-hoc (one-shot wiring)
verifier: ikenna (check #agent-orchestrator-alerts for real notification after smoke)
last_executed: not-yet-run

todos:
  - id: p0-secret-wire
    content: |
      - [ ] [AGENT] P0. Wire AGENT_ORCHESTRATOR_SLACK_WEBHOOK into Cloud Run staging (depends on deployment plan P1)
        - [ ] Confirm `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` exists in Secret Manager: `gcloud secrets describe AGENT_ORCHESTRATOR_SLACK_WEBHOOK --project=central-element-323112`
        - [ ] IAM bind: grant Cloud Run staging SA (`agent-orchestrator-staging@central-element-323112.iam.gserviceaccount.com`) access to the secret: `gcloud secrets add-iam-policy-binding AGENT_ORCHESTRATOR_SLACK_WEBHOOK --member="serviceAccount:<SA>" --role="roles/secretmanager.secretAccessor" --project=central-element-323112`
        - [ ] Same IAM bind for `AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET` (future slash-command verification)
        - [ ] `gcloud run services update agent-orchestrator-staging --update-secrets=AGENT_ORCHESTRATOR_SLACK_WEBHOOK=AGENT_ORCHESTRATOR_SLACK_WEBHOOK:latest,AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET=AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET:latest --region europe-west4 --project central-element-323112`
        - [ ] Verify env var present: `gcloud run services describe agent-orchestrator-staging --region europe-west4 --project central-element-323112 --format='get(spec.template.spec.containers[0].env)'` — confirm `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` appears
      Full-execution criterion: `gcloud run services describe` shows both secrets mounted. Verified via: grep for secret name in describe output.
    status: todo

  - id: p1-notification-module
    content: |
      - [ ] [AGENT] P1. Implement server/notifications/slack.py (depends on P0)
        - [ ] Create `server/notifications/__init__.py` (empty)
        - [ ] Create `server/notifications/slack.py`:
            ```python
            import httpx
            import os
            from datetime import datetime, timezone

            _WEBHOOK_URL = os.environ.get("AGENT_ORCHESTRATOR_SLACK_WEBHOOK", "")

            async def _post(payload: dict) -> None:
                if not _WEBHOOK_URL:
                    return  # silently skip in local dev (no secret mounted)
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(_WEBHOOK_URL, json=payload)
                    resp.raise_for_status()

            async def notify_slot_blocked(slot_id: str, agent_tag: str, reason: str) -> None:
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                await _post({"text": f":octagonal_sign: *Slot {slot_id} BLOCKED* [{ts}]\nAgent: `{agent_tag}`\nReason: {reason}"})

            async def notify_slot_stale(slot_id: str, last_heartbeat: str, stale_minutes: int) -> None:
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                await _post({"text": f":warning: *Slot {slot_id} STALE* [{ts}]\nLast heartbeat: {last_heartbeat} ({stale_minutes}min ago)"})

            async def notify_slot_failed(slot_id: str, error_detail: str) -> None:
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                await _post({"text": f":x: *Slot {slot_id} FAILED* [{ts}]\n{error_detail}"})
            ```
        - [ ] Add `httpx` to `pyproject.toml` `[project.dependencies]` (flat deps only)
        - [ ] Unit tests `tests/test_slack_notifications.py` — mock `httpx.AsyncClient.post`; assert correct payload shape for each of the 3 event types; assert no-op when `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` is empty string
      Full-execution criterion: `bash scripts/check.sh` passes; unit tests green; basedpyright `server/notifications/` clean (timeout 120s); ruff clean.
    status: todo

  - id: p2-event-hook-wiring
    content: |
      - [ ] [AGENT] P2. Wire notification calls into server event handlers (depends on P1)
        - [ ] Grep server codebase for `add_blocked`, `slot_stale`, `slot_failed` / equivalent event emission points: `rg "add_blocked|stale|failed|blocked" server/ --type py`
        - [ ] Wire `notify_slot_blocked()` at the point where a slot transitions to BLOCKED state
        - [ ] Wire `notify_slot_stale()` in the background staleness-check loop (wherever the server polls for heartbeat age > threshold)
        - [ ] Wire `notify_slot_failed()` at the point where a slot transitions to FAILED state
        - [ ] Ensure each call is `await`-ed and wrapped in `try/except Exception` — Slack outage must NOT crash the server: `try: await notify_slot_blocked(...) except Exception: pass  # Slack outage non-fatal`
        - [ ] Integration smoke: `curl -X POST http://localhost:8765/api/slots/test-slot/simulate-blocked` (or equivalent test endpoint) → verify message appears in #agent-orchestrator-alerts within 5s
      Full-execution criterion: manual smoke in local dev produces a message in Slack. `bash scripts/check.sh` still passes post-wiring. No uncaught exceptions in server logs when Slack URL is missing.
    status: todo

  - id: p3-staging-smoke
    content: |
      - [ ] [AGENT] P3. End-to-end smoke on staging Cloud Run (depends on P2 + P0)
        - [ ] Push code to main → deploy-staging CI triggers (from deployment plan P4) → new Cloud Run revision deploys
        - [ ] Trigger a test notification against staging: `curl -X POST https://agent-orchestrator-staging-<hash>-ew.a.run.app/api/slots/smoke-test/simulate-blocked -H "Authorization: Bearer <JWT>"` (or equivalent test endpoint)
        - [ ] Verify message appears in #agent-orchestrator-alerts Slack channel within 10s
        - [ ] Verify server logs show `POST https://hooks.slack.com/... 200` (not a 4xx/5xx)
        - [ ] `gcloud run revisions list --service agent-orchestrator-staging --region europe-west4 --project central-element-323112` — confirm latest revision has both secrets mounted
      Full-execution criterion: Slack message visible in #agent-orchestrator-alerts from staging URL. Cloud Run logs show 200 from Slack. Verified via: screenshot in ping ack OR `gcloud logging read 'resource.type=cloud_run_revision AND textPayload=~"hooks.slack"' --project=central-element-323112 --limit=5`.
    status: todo

  - id: p4-codex-update
    content: |
      - [ ] [AGENT] P4. Codex doc update (can run concurrent with P3)
        - [ ] Update `codex/04-architecture/agent-orchestrator-overview.md` (created in deployment plan P6): add "Slack notifications" section describing the 3 event types, secret name, non-fatal failure pattern, and that signing secret is mounted for future slash-command verification
        - [ ] Strike "Slack notification when blocked" from `agent-orchestrator/TODO.md` Done-items list (or add to "Completed" section)
        - [ ] Verify `AGENT_ORCHESTRATOR_SLACK_CLIENT_SECRET` + `AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET` IAM policy includes prod Cloud Run SA (for when deployment plan P5 runs prod cutover)
      Full-execution criterion: codex doc updated with Slack section. TODO.md item struck. Prod SA IAM binding pre-wired (verify via `gcloud secrets get-iam-policy AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET --project=central-element-323112`).
    status: todo

isProject: true
---

# agent-orchestrator Slack Notifications

> **What this is.** Wire `blocked` / `stale` / `failed` slot events from the agent-orchestrator
> backend to the Slack channel `#agent-orchestrator-alerts` via incoming webhook. All credentials
> are already in GCP Secret Manager (`central-element-323112`) — provisioned 2026-05-19 by Ikenna.
> No human gates in this plan — agent runs end to end.
>
> **Depends on**: `agent_orchestrator_cloud_run_deployment_2026_05_19` P1 (Cloud Run staging service
> must exist so `--update-secrets` has a target). Agent steps P1-P4 of this plan can be written
> in parallel with the deployment plan — only P0 (secret mount) must wait for P1 of the deployment.
>
> **Secret inventory** (all already in Secret Manager — no provisioning needed):
>
> | Secret name                                | Value            | Used for                           |
> | ------------------------------------------ | ---------------- | ---------------------------------- |
> | `AGENT_ORCHESTRATOR_SLACK_WEBHOOK`         | real webhook URL | POST notifications                 |
> | `AGENT_ORCHESTRATOR_SLACK_APP_ID`          | A0B4N3802N9      | reference                          |
> | `AGENT_ORCHESTRATOR_SLACK_CLIENT_ID`       | real             | OAuth (future)                     |
> | `AGENT_ORCHESTRATOR_SLACK_CLIENT_SECRET`   | real             | OAuth (future)                     |
> | `AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET`  | real             | request verification (slash cmds)  |
> | `AGENT_ORCHESTRATOR_SLACK_VERIFICATION_TOKEN` | real          | legacy verify (deprecated by Slack)|
>
> **No human gates** — Harsh Slot 11 runs this entirely. No operator steps required.

---

## Phase DAG

```
P0 (wire --update-secrets to staging Cloud Run)  ← waits for deployment plan P1
   │
   ├── P1 (implement server/notifications/slack.py + unit tests)  ← can start immediately
   │      │
   │      ▼
   │   P2 (wire hooks into server event handlers)
   │      │
   ▼      ▼
   P3 (staging smoke — real Slack message in #agent-orchestrator-alerts)
      │
      └── P4 (codex update) — concurrent with P3
```

P1 code work can start immediately (no Cloud Run dependency). P0 + P3 require the staging
Cloud Run service to exist (deployment plan P1).

---

## Pre-audit manifest

**What changes**:

| Surface                                    | Action                                                                  |
| ------------------------------------------ | ----------------------------------------------------------------------- |
| `agent-orchestrator/server/notifications/` | New module — `__init__.py` + `slack.py`                                 |
| `agent-orchestrator/pyproject.toml`        | Add `httpx` to `[project.dependencies]`                                 |
| `agent-orchestrator/server/server.py`      | Import + `await` notification calls at blocked/stale/failed transitions |
| Cloud Run staging service                  | `--update-secrets` adds 2 env vars (webhook + signing secret)           |
| `codex/04-architecture/agent-orchestrator-overview.md` | New "Slack notifications" section                          |

**What does NOT change**:

- Webhook URL or Slack app config — already provisioned, no re-auth needed
- Any other service's code — this plan is agent-orchestrator-only
- The Cloud Run service name, region, or project — same `agent-orchestrator-staging` from deployment plan P1

---

## Risks

1. **Cloud Run SA name unknown until deployment plan P1 runs.** Mitigation: P0 first step looks up SA
   via `gcloud run services describe ... --format='get(spec.template.spec.serviceAccountName)'` —
   no hardcoding.
2. **Slack outage.** Mitigation: all notification calls wrapped in `try/except Exception: pass` —
   server never crashes on Slack failure.
3. **httpx not in existing pyproject.** Mitigation: P1 adds it to flat `[project.dependencies]`;
   QG catches missing dep before push.

---

## Full-execution closeout summary (filled at P3 completion)

| Phase | What ran | Verification | SHA |
| ----- | -------- | ------------ | --- |
| P0    | _pending_ | _pending_   | —   |
| P1    | _pending_ | _pending_   | —   |
| P2    | _pending_ | _pending_   | —   |
| P3    | _pending_ | _pending_   | —   |
| P4    | _pending_ | _pending_   | —   |

---

## Temporary states + their canonical follow-up plans

| Temporary state                                      | Follow-up plan                                       |
| ---------------------------------------------------- | ---------------------------------------------------- |
| Prod Cloud Run SA not yet bound to Slack secrets     | Deployment plan P5 (prod cutover) — agent binds prod SA at that time per P4 codex note |
| `AGENT_ORCHESTRATOR_SLACK_VERIFICATION_TOKEN` stored but unused | Slack deprecated verification tokens in favour of signing secret — use signing secret for slash-command verification if/when slash commands are added |
