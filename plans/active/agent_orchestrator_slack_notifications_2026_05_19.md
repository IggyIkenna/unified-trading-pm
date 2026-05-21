---name: agent-orchestrator-slack-notifications-2026-05-19
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
      - [x] ✅ [AGENT] P1. Audit + scope check — **DONE 2026-05-20 (slot 4)**
        - [x] ✅ P1.1. eea2f69 confirmed on live-defi-rollout (not a side-branch); `server/notifications/slack.py` present at LDR HEAD with basic plain-text implementation.
        - [x] ✅ P1.2. Pre-audit confirmed: 31-line file, plain text, no Block Kit, no retry, no dashboard link.
        - [x] ✅ P1.3. WIRED: slot_blocked (server.py), slot_stale (health.py working-stale), slot_failed (health.py idle-stale). NOT WIRED: slot_unblocked, agent_stale (out of P2 scope).
        - [x] ✅ P1.4. httpx in pyproject.toml ✅.
        - [x] ✅ P1.5–P1.6. Secret Manager + Cloud Run SA verified by prior P3 of parent plan (secrets mounted at rev 00009-b5r).
        - [x] ✅ P1.7. No tests at eea2f69 — tests/test_slack_notifications.py did not exist (shipped by P2 this turn).
      Full-execution criterion: ✅ audit table filled in; P2 scope confirmed.
    status: done

  - id: p2-webhook-delivery-polish
    content: |
      - [x] ✅ [AGENT] P2. Webhook delivery polish — **DONE 2026-05-20 (slot 4) — agent-orchestrator@cd04fc2**
        - [x] ✅ P2.1. eea2f69 already on live-defi-rollout (no cherry-pick needed); firebase.json from main also brought to LDR at d9ddc73 (prior slot-10 task).
        - [x] ✅ P2.2. `server/notifications/slack.py` upgraded to Block Kit: header+section+fields+context blocks for all 3 event types; `text` fallback kept.
        - [x] ✅ P2.3. `_post()` retry: 3 attempts, backoff 0.5s/1.0s before 2nd/3rd; 5xx retries; 4xx aborts immediately.
        - [x] ✅ P2.4. `blocked_id` added to `notify_slot_blocked()` signature; server.py call site updated to pass `blocked_id`.
        - [x] ✅ P2.5. `_PUBLIC_URL = os.environ.get("ORCHESTRATOR_PUBLIC_URL", "")` in slack.py (module-level, consistent with _WEBHOOK_URL pattern).
        - [x] ✅ P2.6. `tests/test_slack_notifications.py`: 9 tests — retry (3 calls on 2×500+200), 4xx abort (1 call), no-op on empty webhook, Block Kit shape for all 3 types, dashboard link presence/absence. All 9 PASS.
        - [x] ✅ P2.7. `ruff format + ruff check` clean; `basedpyright server/` 0 errors/warnings.
      Full-execution criterion: ✅ ruff+basedpyright green; 9 unit tests pass (>= 8 required); Block Kit verified in test assertions; retry branch confirmed via mock call-count.
    status: done

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
      - [x] ✅ [AGENT] P5. Codex doc — **DONE 2026-05-20 (slot 4)**
        - [x] ✅ P5.1. `codex/05-infrastructure/agent-orchestrator-slack-notifications.md` created: overview (webhook URL, Secret Manager path, channel, app ID A0B4N3802N9), V1 event table, Block Kit payload shape, retry policy, secret inventory, V2 out-of-scope, unit test pointers.
        - [x] ✅ P5.2. `codex/04-architecture/agent-orchestrator-overview.md` Slack section replaced with 2-line pointer to standalone codex doc.
        - [x] ✅ P5.3. No markdown lint in PM check.sh (TS-only scripts/check.sh equivalent not run here; doc is prose-only).
      Full-execution criterion: ✅ codex file exists with all required sections; overview pointer added.
      Verified via: `grep -c "##" codex/05-infrastructure/agent-orchestrator-slack-notifications.md | awk '$1>=6'`.
    status: done

isProject: true
parent_epic: orchestrator_master
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

| Phase | What ran                                          | Verification                                                         | SHA         |
| ----- | ------------------------------------------------- | -------------------------------------------------------------------- | ----------- |
| P1    | Audit + scope check (2026-05-20 slot 4)           | eea2f69 on LDR confirmed; pre-audit manifest ✅                      | —           |
| P2    | Block Kit + retry + blocked_id + 9 unit tests     | 9 tests PASS; ruff+basedpyright 0 errors                             | cd04fc2     |
| P3    | BLOCKED-OPERATOR: IAM bind for webhook secret     | Ping filed in slot_4.md (2026-05-20)                                 | —           |
| P4    | _pending P3_                                      | _pending_                                                            | —           |
| P5    | Codex doc created + overview updated (2026-05-20) | codex/05-infrastructure/agent-orchestrator-slack-notifications.md ✅ | PM@d460bc67 |

---

## Temporary states + their canonical follow-up plans

| Temporary state                                                        | Follow-up plan                                                                                                              |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| eea2f69 side-branch not merged to main                                 | P2 cherry-pick + polish closes this; branch can be deleted after P2 merge                                                   |
| 5 Slack secrets in Secret Manager but NOT mounted to Cloud Run         | V2 interactivity plan (`agent_orchestrator_slack_interactivity_2026_05_XX.md`) mounts them when slash-command handler ships |
| Prod Cloud Run SA not yet bound to Slack webhook secret                | Deployment plan P5 (prod cutover) — bind prod SA at that time                                                               |
| AGENT_ORCHESTRATOR_SLACK_VERIFICATION_TOKEN stored but unused by Slack | Slack deprecated verification tokens in favour of signing secret; remove from consideration when slash commands added       |
