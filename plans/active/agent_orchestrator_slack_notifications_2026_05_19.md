---
name: agent-orchestrator-slack-notifications-2026-05-19
overview: >
  Wire Slack push notifications into the agent-orchestrator Cloud Run service — blocked/stale/failed slot events POST to
  #agent-orchestrator-alerts via incoming webhook. All 6 Slack secrets are already in GCP Secret Manager
  (central-element-323112). V1 uses webhook-only (one-way POST); other 5 secrets are staged for future bidirectional
  features. Successor plan to agent_orchestrator_cloud_run_deployment_2026_05_19.
type: infra
status: active
epic: epic-infra

estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2.0

locked_by: live-defi-rollout
locked_since: 2026-05-19

completion_gates:
  code: C4
  deployment: D3
  business: none

repo_gates:
  - repo: agent-orchestrator
    code: C4 # P1+P2 code shipped on side-branch eea2f69 (not yet merged to main) — merge + polish is P2 scope
    deployment: D3 # P4 staging smoke — real Slack message in #agent-orchestrator-alerts
    business: none
  - repo: deployment-service
    code: C1 # deploy-agent-orchestrator.sh needs --update-secrets for webhook
    deployment: D3
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on:
  - agent_orchestrator_cloud_run_deployment_2026_05_19 # P1 must be complete — Cloud Run staging service must exist for --update-secrets

owner: ikenna-main
cadence: ad-hoc (one-shot wiring; ongoing maintenance on event-type additions only)
verifier: ikenna
last_executed: not-yet-run-V1-end-to-end

todos:
  - id: p1-audit-scope-check
    content: |
      - [ ] [AGENT] P1. Audit + scope check — read what's already shipped vs what's missing
        - [ ] P1.1. Confirm branch state: `git log --all --oneline --graph | head -20` in agent-orchestrator —
              verify that eea2f69 (feat: wire Slack hooks) is on a SIDE-BRANCH not merged to main HEAD.
              Current situation (2026-05-19): eea2f69 is on a parallel-agent branch diverged from ea0963f;
              main HEAD is 6f1f583. The notifications module + wiring are NOT live on main.
        - [ ] P1.2. Read current `server/notifications/slack.py` content from eea2f69 (via `git show eea2f69:server/notifications/slack.py`).
              Pre-audit summary (see "Pre-audit manifest" section below for detail):
              31-line file; `_post()` uses plain-text `{"text": "..."}` payload (NO Block Kit);
              no retry on 5xx; no dashboard link; no operator-role field. 3 functions shipped.
        - [ ] P1.3. Confirm which events are wired vs missing at eea2f69:
              WIRED: slot_blocked (server.py blocked_slot endpoint), slot_stale (health.py working-stale pass),
              slot_failed (health.py idle-stale pass as notify_slot_failed).
              NOT WIRED: slot_unblocked (answered_blocked endpoint), agent_stale (health.py agent stale pass).
        - [ ] P1.4. Confirm httpx already in pyproject.toml at main HEAD (it is — added at eea2f69 and present in 6f1f583 pyproject.toml).
        - [ ] P1.5. Confirm `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` in Secret Manager:
              `gcloud secrets describe AGENT_ORCHESTRATOR_SLACK_WEBHOOK --project=central-element-323112`
        - [ ] P1.6. Check Cloud Run SA for staging: `gcloud run services describe agent-orchestrator-staging
              --region europe-west4 --project central-element-323112 --format='get(spec.template.spec.serviceAccountName)'`
              Expected: `1060025368044-compute@developer.gserviceaccount.com` (same SA bound at P3 of parent plan).
        - [ ] P1.7. Confirm whether eea2f69 has unit tests in `tests/test_slack_notifications.py` —
              `git show eea2f69 --stat | grep test`.
      Full-execution criterion: audit table filled in; P2 scope list confirmed; no surprises in branch state.
    status: todo

  - id: p2-webhook-delivery-polish
    content: |
      - [ ] [AGENT] P2. Webhook delivery polish — merge + upgrade to Block Kit + retries (depends on P1 audit)
        - [ ] P2.1. Merge the eea2f69 + bead674 branch work into main (cherry-pick or merge):
              `git cherry-pick eea2f69 bead674` from main. Resolve any conflicts with 6f1f583/aa54607/ec72899/d56e70f/7ef9299/6f1f583.
        - [ ] P2.2. Upgrade `server/notifications/slack.py` from plain text to Block Kit formatting:
              - `notify_slot_blocked`: Block Kit with `header` block (status + slot ID), `section` with
                agent tag + reason + dashboard link (`{ORCHESTRATOR_PUBLIC_URL}/api/blocked/{blocked_id}`),
                `context` block with operator-answer role ("Respond via dashboard or answer_blocked endpoint").
                Use :octagonal_sign: emoji in header text.
              - `notify_slot_stale`: `header` (:warning: Slot N STALE), `section` with last heartbeat +
                stale duration, `context` with "Consider re-spawning via dashboard spawn button."
              - `notify_slot_failed`: `header` (:x: Slot N FAILED), `section` with error detail,
                `context` with "Worker heartbeat loop dead — re-spawn required."
              Block Kit payload shape: `{"blocks": [{"type": "header", ...}, {"type": "section", ...}, {"type": "context", ...}]}`.
              Keep `text` fallback field for notification-only clients.
        - [ ] P2.3. Add idempotent retry on Slack 5xx in `_post()`:
              Max 3 attempts, exponential backoff (0.5s / 1s / 2s), retry only on `httpx.HTTPStatusError`
              where `resp.status_code >= 500`. 4xx (including 403 + 404 webhook-not-found) = log + abort,
              do NOT retry (token rotation required). Keep outer `contextlib.suppress(Exception)` at call
              sites — retries exhaust inside `_post()`, exception surfaced to caller only if all 3 fail.
        - [ ] P2.4. Pass `blocked_id` through to `notify_slot_blocked()` so the dashboard link is concrete.
              Signature change: `notify_slot_blocked(slot_id, agent_tag, reason, blocked_id)`.
              Update call site in server.py (blocked_slot endpoint already has `blocked_id` in scope).
        - [ ] P2.5. Read/export `ORCHESTRATOR_PUBLIC_URL` env var for the dashboard link.
              Config already has `ORCHESTRATOR_PUBLIC_URL` in `config.py` — read via `config.ORCHESTRATOR_PUBLIC_URL`
              (follow existing import pattern in server.py/health.py, no os.environ calls directly per workspace rules).
        - [ ] P2.6. Unit tests `tests/test_slack_notifications.py` — mock `httpx.AsyncClient.post`:
              (a) assert Block Kit payload shape for each of the 3 event types;
              (b) assert no-op when `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` is empty string;
              (c) assert retry logic: mock returns 500 twice then 200 → assert 3 total calls + success;
              (d) assert 4xx → single attempt (no retry);
              (e) assert dashboard link contains blocked_id for slot_blocked event.
              Minimum 8 test cases. Run via `bash scripts/check.sh --no-fix` in diagnostic mode.
        - [ ] P2.7. `bash scripts/check.sh` clean (ruff + basedpyright zero errors). Commit to main.
      Full-execution criterion: `bash scripts/check.sh` passes; unit tests (≥8) green; basedpyright
      `server/notifications/` zero errors; Block Kit payload verified in test assertions; retry
      branch exercises confirmed via mock call-count assertions.
    status: todo

  - id: p3-cloud-run-secret-wiring
    content: |
      - [ ] [AGENT] P3. Cloud Run secret wiring (depends on P2 code merge; requires staging service up)
        - [ ] P3.1. Confirm SA has secretAccessor on AGENT_ORCHESTRATOR_SLACK_WEBHOOK:
              `gcloud secrets get-iam-policy AGENT_ORCHESTRATOR_SLACK_WEBHOOK --project=central-element-323112`
              If missing: `gcloud secrets add-iam-policy-binding AGENT_ORCHESTRATOR_SLACK_WEBHOOK
              --member="serviceAccount:1060025368044-compute@developer.gserviceaccount.com"
              --role="roles/secretmanager.secretAccessor" --project=central-element-323112`
        - [ ] P3.2. Update Cloud Run staging service to mount webhook secret as env var:
              `gcloud run services update agent-orchestrator-staging
              --update-secrets AGENT_ORCHESTRATOR_SLACK_WEBHOOK=AGENT_ORCHESTRATOR_SLACK_WEBHOOK:latest
              --region europe-west4 --project central-element-323112`
        - [ ] P3.3. Update `deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh` to include the
              webhook secret in `RUNTIME_SECRETS` (alongside the existing JWT + users.json secrets):
              Append `,AGENT_ORCHESTRATOR_SLACK_WEBHOOK=AGENT_ORCHESTRATOR_SLACK_WEBHOOK:latest` to the
              `RUNTIME_SECRETS` variable — so future re-deploys keep the secret mounted automatically.
        - [ ] P3.4. Verify secret mounted: `gcloud run services describe agent-orchestrator-staging
              --region europe-west4 --project central-element-323112
              --format='get(spec.template.spec.containers[0].env)'` — confirm AGENT_ORCHESTRATOR_SLACK_WEBHOOK appears.
        - [ ] P3.5. Note: the other 5 Slack secrets (APP_ID, CLIENT_ID, CLIENT_SECRET, SIGNING_SECRET,
              VERIFICATION_TOKEN) are in Secret Manager but NOT mounted to Cloud Run — they are for future
              bidirectional V2 features (slash commands, interactivity, event subscriptions). Do NOT
              mount them now — adds unnecessary surface area. They stay in Secret Manager as-is.
      Full-execution criterion: `gcloud run services describe` output shows AGENT_ORCHESTRATOR_SLACK_WEBHOOK
      in env list. deploy-agent-orchestrator.sh diff shows webhook secret in RUNTIME_SECRETS. Verified via:
      `grep AGENT_ORCHESTRATOR_SLACK_WEBHOOK deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh`.
    status: todo

  - id: p4-smoke-test
    content: |
      - [ ] [AGENT] P4. End-to-end staging smoke test (depends on P2 code on main + P3 secret mounted)
        - [ ] P4.1. Get a valid JWT for staging:
              `curl -X POST https://agent-orchestrator-staging-1060025368044.europe-west4.run.app/api/auth/login
              -H "Content-Type: application/json" -d '{"username":"ikenna","password":"<pw>"}' | jq -r .token`
        - [ ] P4.2. Trigger a slot_blocked notification — POST to blocked endpoint with a test question:
              `curl -X POST .../api/slots/1/blocked -H "Authorization: Bearer <JWT>"
              -H "Content-Type: application/json"
              -d '{"task_id":"smoke-test","question":"Smoke test: is Slack wired?","options":[],"recommendation":""}'`
        - [ ] P4.3. Verify Slack message lands in `#agent-orchestrator-alerts` within 10 seconds.
              Expected fields in message: slot ID, agent tag, reason, dashboard link
              (https://agent-orchestrator.staging.odum-research.com/api/blocked/<blocked_id>),
              operator answer role in context block.
        - [ ] P4.4. Verify Cloud Run logs show successful Slack webhook POST:
              `gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=agent-orchestrator-staging
              AND textPayload=~"hooks.slack"' --project=central-element-323112 --limit=5 --freshness=5m`
        - [ ] P4.5. Check answer endpoint triggers no duplicate Slack notification (answer_blocked should NOT
              post a second message — that's expected V2 scope):
              `curl -X POST .../api/blocked/<blocked_id>/answer -H "Authorization: Bearer <JWT>"
              -d '{"answer":"smoke test passed","from_role":"operator"}'`
        - [ ] P4.6. Screenshot or log-paste of Slack message and Cloud Run logs captured in this plan's
              full-execution closeout table.
      Full-execution criterion: Slack message visible in #agent-orchestrator-alerts with all required fields
      (slot ID, dashboard link, operator role prompt). Cloud Run logs confirm 200 from Slack webhook. No
      server error in health check after smoke. Verified via: log paste + Slack screenshot.
    status: todo

  - id: p5-codex-doc
    content: |
      - [ ] [AGENT] P5. Codex doc (can run concurrent with P4 once P2 code is on main)
        - [ ] P5.1. Create NEW `unified-trading-pm/codex/05-infrastructure/agent-orchestrator-slack-notifications.md`:
              Sections:
              (a) Overview — webhook URL source, Secret Manager path, channel, app ID A0B4N3802N9
              (b) Event types covered in V1 — table: event_function / trigger_location / message_format
                  | Function              | Wired in      | Trigger                                | Message format |
                  | --------------------- | ------------- | -------------------------------------- | -------------- |
                  | notify_slot_blocked   | server.py     | POST /api/slots/{id}/blocked           | Block Kit + dashboard link |
                  | notify_slot_stale     | health.py     | HealthMonitor working-stale pass       | Block Kit + last heartbeat |
                  | notify_slot_failed    | health.py     | HealthMonitor idle-stale (dead worker) | Block Kit + error detail |
              (c) Message format — Block Kit structure (header + section + context), retry policy (3 attempts / exponential backoff / 4xx no-retry)
              (d) Webhook URL rotation flow — gcloud secret update → gcloud run deploy (no code change needed; env var injected at revision start)
              (e) Debugging guide — "Why isn't the webhook firing?":
                  1. `echo $AGENT_ORCHESTRATOR_SLACK_WEBHOOK` in Cloud Run exec → empty = secret not mounted (re-run deploy script)
                  2. Cloud Run logs `grep hooks.slack` → 4xx = bad webhook URL (rotate); 5xx = Slack outage (auto-retries should handle)
                  3. Code path: server.py/health.py → `contextlib.suppress(Exception)` wrapper → `slack_notify.notify_*()` → `_post()` → httpx
                  4. If contextlib.suppress is silencing errors: temporarily add logging at the suppress site, redeploy, reproduce
              (f) How to add new event types — pattern: import slack_notify in target module, add `with contextlib.suppress(Exception): asyncio.run(slack_notify.notify_<new>(...))`; add new `notify_<new>()` in slack.py; add unit test; update this codex table
              (g) Out-of-scope V2 features — list with successor plan reference (see plan's Out-of-scope section)
        - [ ] P5.2. Update `codex/04-architecture/agent-orchestrator-overview.md` "Slack notifications" section —
              add pointer to new codex/05-infrastructure doc instead of inline detail.
        - [ ] P5.3. Run `bash scripts/check.sh` in unified-trading-pm if applicable (markdown lint).
      Full-execution criterion: codex file exists; sections (a)-(g) present; overview doc pointer added.
      Verified via: `grep -c "##" codex/05-infrastructure/agent-orchestrator-slack-notifications.md | awk '$1>=6'`.
    status: todo

isProject: true
---

# agent-orchestrator Slack Notifications (V1)

> **What this is.** Wire one-way Slack push notifications for `blocked` / `stale` / `failed` slot events from the
> agent-orchestrator backend to `#agent-orchestrator-alerts` (workspace: `odum-research`, app:
> `agent-orchestrator-alerts`, App ID: `A0B4N3802N9`). All 6 Slack secrets are already in GCP Secret Manager
> (`central-element-323112`) — no human provisioning gates in this plan.
>
> **V1 scope**: webhook-only (one-way POST). The other 5 Slack secrets (CLIENT_ID, CLIENT_SECRET, SIGNING_SECRET,
> APP_ID, VERIFICATION_TOKEN) are stored in Secret Manager for future V2 bidirectional features but are NOT mounted to
> Cloud Run in this plan.
>
> **Context on prior work**: A parallel-agent session (Harsh Slot, 2026-05-19) shipped a first implementation on a
> side-branch (`eea2f69` + `bead674`) that diverged from `ea0963f` and is NOT yet merged to `main` (`6f1f583`). That
> work implemented the skeleton (31-line `slack.py`, plain-text payloads, no Block Kit, no retries, no dashboard links).
> This plan picks up from that state: P1 audits, P2 polishes and merges, P3 wires Cloud Run secrets, P4 smoke-tests, P5
> writes the codex doc.
>
> **Depends on**: `agent_orchestrator_cloud_run_deployment_2026_05_19` P1 (Cloud Run staging service must exist for
> `--update-secrets`). The code work (P1+P2) can start immediately.

---

## Phase DAG

```
P1 (audit + scope check — read branch state + existing code)
   │
   ▼
P2 (webhook delivery polish — merge + Block Kit + retries + dashboard link + unit tests)
   │
   ▼
P3 (Cloud Run secret wiring — --update-secrets + deploy script update)  ← waits for P1 of deployment plan
   │
   ▼
P4 (staging smoke — real Slack message in #agent-orchestrator-alerts)
   │
   └── P5 (codex doc) — concurrent with P4 once code is on main
```

P2 code work can start immediately. P3 + P4 require the staging Cloud Run service to exist and P2 code to be on main.

---

## Pre-audit manifest (eea2f69 existing scaffold)

**What's already in `eea2f69` (side-branch, NOT on main HEAD `6f1f583`)**:

| File                                       | State at eea2f69                                                                               | Gaps vs task spec                                                                                                        |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `server/notifications/__init__.py`         | EXISTS — empty file                                                                            | None                                                                                                                     |
| `server/notifications/slack.py`            | EXISTS — 31 lines                                                                              | Plain-text payload (no Block Kit); no retry on 5xx; no dashboard link in blocked message; no operator-role context block |
| `server/server.py` (blocked_slot endpoint) | WIRED — `notify_slot_blocked()` called                                                         | Missing `blocked_id` in call signature (needed for dashboard link)                                                       |
| `server/health.py` (working-stale pass)    | WIRED — `notify_slot_stale()` called                                                           | None blocking                                                                                                            |
| `server/health.py` (idle-stale pass)       | WIRED — `notify_slot_failed()` called                                                          | None blocking                                                                                                            |
| `pyproject.toml`                           | WIRED — `httpx>=0.27.0` in dependencies                                                        | Already present at main HEAD 6f1f583 too                                                                                 |
| Unit tests                                 | Status unknown (`ceaaefe` SHA phantom — does not exist; eea2f69 stats show no test file added) | Unit tests likely NOT shipped — P2 must add them                                                                         |
| Cloud Run `--update-secrets`               | NOT done                                                                                       | P3 scope                                                                                                                 |
| `deploy-agent-orchestrator.sh`             | NOT updated                                                                                    | P3 scope                                                                                                                 |
| Codex doc                                  | `agent-orchestrator-overview.md` has a Slack section stub                                      | Full standalone doc is P5 scope                                                                                          |

**Event coverage at eea2f69**:

| Event type     | Wired | Function            | Location   |
| -------------- | ----- | ------------------- | ---------- |
| slot_blocked   | YES   | notify_slot_blocked | server.py  |
| slot_stale     | YES   | notify_slot_stale   | health.py  |
| slot_failed    | YES   | notify_slot_failed  | health.py  |
| slot_unblocked | NO    | —                   | (V2 scope) |
| agent_stale    | NO    | —                   | (V2 scope) |

**What's NOT in eea2f69 that the task spec requires**:

- Block Kit formatting (rich attachments vs plain `{"text": "..."}`)
- Idempotent retry on Slack 5xx
- Dashboard link in blocked message (`/api/blocked/{blocked_id}`)
- "Operator role to answer" context block
- Unit tests (ceaaefe phantom SHA — no test file in eea2f69 diff)

---

## Out of scope (V2 named successors)

| Feature                                              | Why deferred                                                                    | Named successor                                        |
| ---------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------ |
| Bidirectional interactivity — acknowledge from Slack | Requires APP_ID + SIGNING_SECRET + request verification + slash-command handler | `agent_orchestrator_slack_interactivity_2026_05_XX.md` |
| Slash commands (`/orch status`, `/orch slots`, etc.) | Requires Slack Event API subscription + oauth flow + slash endpoint             | Same interactivity plan                                |
| Direct messages to specific operators                | Requires `chat.postMessage` with user IDs (bot token, not webhook)              | Same interactivity plan                                |
| Multi-workspace support                              | Currently single workspace `odum-research` — no demand                          | Not planned; add to successor if demand arises         |
| Notify on slot_unblocked (question answered)         | Low urgency — blocked is the high-value alert; answer is visible in dashboard   | Same interactivity plan or standalone at P3            |
| Notify on agent_stale                                | Lower signal/noise vs slot-level; operator sees in dashboard                    | Same interactivity plan                                |

---

## Risks

1. **Cherry-pick conflicts.** The side-branch (`eea2f69`/`bead674`) diverged from `ea0963f`; since then main got 5 new
   commits (`7ef9299`, `d56e70f`, `ec72899`, `aa54607`, `6f1f583`). Expected conflicts: `pyproject.toml` (httpx already
   added at main) + server.py (6f1f583 may have changed server structure). Mitigation: read
   `git diff ea0963f eea2f69 -- server/server.py` before cherry-pick; resolve by keeping both changes.
2. **Slack outage during smoke.** All calls wrapped in `contextlib.suppress(Exception)` — server non-fatal. Smoke
   re-attempted when Slack recovers.
3. **SA name mismatch.** P3 uses `1060025368044-compute@developer.gserviceaccount.com` (confirmed in P3 of parent plan).
   If prod Cloud Run ever gets a different SA, the IAM binding will need to be repeated. Mitigation: P3.1 reads SA from
   `gcloud run services describe` — does not hardcode.

---

## Codex SSOT updates (per HARD RULE — enumerated at plan-write time)

| Codex doc                                                           | Action | When                                                                  |
| ------------------------------------------------------------------- | ------ | --------------------------------------------------------------------- |
| `codex/05-infrastructure/agent-orchestrator-slack-notifications.md` | NEW    | P5                                                                    |
| `codex/04-architecture/agent-orchestrator-overview.md`              | UPDATE | P5 — add pointer to new codex doc; slim existing inline Slack section |

---

## Full-execution closeout summary (filled at P4 + P5 completion)

| Phase | What ran  | Verification | SHA |
| ----- | --------- | ------------ | --- |
| P1    | _pending_ | _pending_    | —   |
| P2    | _pending_ | _pending_    | —   |
| P3    | _pending_ | _pending_    | —   |
| P4    | _pending_ | _pending_    | —   |
| P5    | _pending_ | _pending_    | —   |

---

## Temporary states + their canonical follow-up plans

| Temporary state                                                        | Follow-up plan                                                                                                              |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| eea2f69 side-branch not merged to main                                 | P2 cherry-pick + polish closes this; branch can be deleted after P2 merge                                                   |
| 5 Slack secrets in Secret Manager but NOT mounted to Cloud Run         | V2 interactivity plan (`agent_orchestrator_slack_interactivity_2026_05_XX.md`) mounts them when slash-command handler ships |
| Prod Cloud Run SA not yet bound to Slack webhook secret                | Deployment plan P5 (prod cutover) — bind prod SA at that time                                                               |
| AGENT_ORCHESTRATOR_SLACK_VERIFICATION_TOKEN stored but unused by Slack | Slack deprecated verification tokens in favour of signing secret; remove from consideration when slash commands added       |
