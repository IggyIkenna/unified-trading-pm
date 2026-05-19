---
name: agent-orchestrator-cloud-run-deployment-2026-05-19
overview:
  Migrate orchestrator-service (FastAPI + Vite dashboard) to Cloud Run on odum-research.com — rename to
  agent-orchestrator, mirror unified-trading-system-ui's Firebase Hosting + Cloud Run fabric, add staging+prod envs,
  strict-auth flip, decommission Harsh's laptop nginx after 1-week dual-run. Unblocks Slack push notifications (separate
  follow-up plan).
type: infra
status: active
epic: epic-infra

estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8

locked_by: live-defi-rollout
locked_since: 2026-05-19

completion_gates:
  code: C5
  deployment: D3
  business: none

repo_gates:
  - repo: orchestrator-service
    code: C2
    deployment: D1
    business: none
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on: []

owner: ikenna
cadence: ad-hoc (one-shot migration)
verifier: ikenna (dashboard login + healthz curl) + harsh (cross-operator smoke after Phase 5)
last_executed: not-yet-run

todos:
  - id: p0-compliance-scaffold
    content: |
      - [ ] [AGENT] P0. Phase 0 — Compliance scaffold + repo rename
        - [ ] Pre-audit: grep workspace for `orchestrator-service` references (imports, scripts, codex) — confirm or refute the "unrelated trading orchestrator-service module" hypothesis; if collision exists, choose disambiguation (agent-orchestrator wins, document the other in scope)
        - [ ] Rename local directory orchestrator-service/ → agent-orchestrator/; push GitHub repo rename IggyIkenna/orchestrator-service → IggyIkenna/agent-orchestrator (preserves PRs + redirects old URLs)
        - [ ] Fix `orchastrator` typo across docs/server/scripts/dashboard (Harsh's original misspelling — ~40 references)
        - [ ] Add UTL as pyproject dep + wire `make_health_router` into existing `server/server.py` with state.json mtime-based `data_freshness` callback (QG STEP 5.62 — only one of the three STEPs applied; see exemption note below)
        - [ ] ~~ServiceBootstrap (QG STEP 5.61)~~ — **EXEMPT** (operator decision 2026-05-19): ServiceBootstrap is a CLI dispatcher for batch/live trading services with `--asset-group`/`--mode` patterns; orchestrator has no such CLI (uvicorn-only). Client-reporting-api's source comment confirms its instantiation is a token gesture. Operator chose lightest path. Codex doc at P6 documents the exemption.
        - [ ] ~~typed `config_reloaders.py` (QG STEP 5.34)~~ — **EXEMPT** (operator decision 2026-05-19): orchestrator's `server/config.py` is module-level env-driven functions, not a typed config class; full compliance requires a config-class refactor that's a separate workstream. Codex doc at P6 documents the exemption.
        - [ ] Pyproject + Dockerfile match workspace pattern: `ARG PROJECT_ID` + `FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest`
        - [ ] Allocate port 8026 in unified-trading-pm/scripts/dev/ui-api-mapping.json (next available in 80xx sequence)
        - [ ] quality-gates.sh wiring — keep existing `scripts/check.sh` for now (operator-tooling exemption); PM `base-service.sh` integration deferred to follow-up
      Full-execution criterion: `bash scripts/check.sh` passes locally on the renamed repo with ruff + basedpyright + prettier + tsc clean; `/health` and `/readiness` endpoints respond 200 on `uvicorn server.server:app`; new Dockerfile builds against the workspace UTL base image. Verified via: `bash scripts/check.sh 2>&1 | tail -5` shows clean exit + `curl localhost:8765/health` returns expected shape.
    status: todo

  - id: p1-cloud-run-staging
    content: |
      - [ ] [AGENT] P1. Phase 1 — Cloud Run staging deploy (depends on P0)
        - [ ] Create deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh mirroring deploy-ui.sh shape (rejects missing --env; supports --env=prod|uat + --cloud + --build-env-file= override)
        - [ ] Add config/docker-build.env.{production,uat} (server-side env: ORCHASTRATOR_MODE=live, ORCHASTRATOR_PUBLIC_URL, dashboard build needs only ORCHASTRATOR_API_BASE_URL since it's a Vite SPA not Next.js)
        - [ ] Cloudbuild YAML at scripts/cloudbuild-agent-orchestrator.yaml — pulls prior :uat or :production tag as cache source
        - [ ] First image build + push: europe-west4-docker.pkg.dev/central-element-323112/cloud-run-source-deploy/agent-orchestrator:uat
        - [ ] First `gcloud run deploy --env=uat` creates Cloud Run service `agent-orchestrator-staging` in central-element-323112/europe-west4 (matches odum-portal-staging convention)
      Full-execution criterion: `curl https://agent-orchestrator-staging-<hash>-ew.a.run.app/healthz` returns `{"status":"ok","mode":"live","uptime_seconds":<int>}` (200). `gcloud run services describe agent-orchestrator-staging --region europe-west4 --project central-element-323112` shows `Conditions: Ready=True` + last revision SHA matching deployed commit. Verified via: `gcloud run services list --project central-element-323112 --region europe-west4 --filter "metadata.name=agent-orchestrator-staging"`.
    status: todo

  - id: p2-firebase-hosting-domains
    content: |
      - [ ] [HUMAN+AGENT] P2. Phase 2 — Firebase Hosting + custom domains (depends on P1)
        - [ ] Add agent-orchestrator/firebase.json with prod+uat hosting targets, each rewriting `/api/*` and `/healthz` to the matching Cloud Run service (region europe-west4) and serving built Vite dashboard at `/`
        - [ ] Add agent-orchestrator/.firebaserc with hosting targets prod=agent-orchestrator-prod-site, uat=agent-orchestrator-uat-site (both under central-element-323112 firebase project)
        - [ ] dashboard/vite.config.ts: confirm build output goes to a Firebase-Hosting-friendly path (dist/ → public/ relative to firebase.json)
        - [ ] First `firebase deploy --only hosting:uat` from local laptop
        - [ ] [HUMAN] Operator (Ikenna): Firebase Console → Hosting → uat target → Add custom domain `agent-orchestrator.staging.odum-research.com` — Firebase returns 2 DNS records (A or CNAME)
        - [ ] [HUMAN] Operator (Ikenna): paste those records into odum-research.com DNS provider (provider TBD — operator will identify at Phase 2 kickoff)
        - [ ] [HUMAN] Wait ≤15min after DNS propagates for Firebase to auto-issue Let's Encrypt SSL
        - [ ] Repeat for prod: agent-orchestrator.odum-research.com → prod target
      Full-execution criterion: browser loads https://agent-orchestrator.staging.odum-research.com → dashboard renders, /api/healthz returns 200 via SSL, sign-in page appears. SSL cert issued by Google (subject CN matches subdomain). Verified via: `openssl s_client -connect agent-orchestrator.staging.odum-research.com:443 -servername agent-orchestrator.staging.odum-research.com </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer`.
    status: todo

  - id: p3-strict-auth-flip
    content: |
      - [ ] [AGENT] P3. Phase 3 — Strict auth flip on staging (depends on P2)
        - [ ] Create GCP Secret Manager secret `ORCHASTRATOR_JWT_SECRET` (32-byte random); IAM bind to agent-orchestrator-staging Cloud Run service account
        - [ ] `gcloud run services update agent-orchestrator-staging --update-secrets=ORCHASTRATOR_JWT_SECRET=ORCHASTRATOR_JWT_SECRET:latest`
        - [ ] Replace server/auth.py permissive `validate_credentials` with hashed-user-list check (matches scripts/manage_users.py argon2 schema already in repo)
        - [ ] Flip `auth.ALLOW_ANONYMOUS=False` env var on Cloud Run service
        - [ ] Bootstrap users: ikenna + harsh via `manage_users.py` against staging DB (or whichever data-state mode is active)
        - [ ] Sign-in smoke test sequence: (a) valid creds → JWT issued + dashboard loads; (b) wrong password → 401; (c) anonymous → 401 (matches AUTH_INVENTORY.md flip-day checklist)
      Full-execution criterion: 3-curl smoke test passes on staging URL. Curl 1: `POST /api/auth/login` with valid creds returns 200 + JWT. Curl 2: same with wrong password returns 401. Curl 3: `GET /api/state` without bearer returns 401. Verified via: documented curl block in docs/AUTH_INVENTORY.md "Flip-day checklist" + visual sign-in test in browser.
    status: todo

  - id: p4-ci-wireup
    content: |
      - [ ] [AGENT] P4. Phase 4 — CI/CD wire-up (depends on P3)
        - [ ] Add .github/workflows/quality-gates.yml referencing PM template `python-quality-gates.yml@live-defi-rollout`
        - [ ] Add .github/workflows/deploy-staging.yml — on push to main, Cloud Build → push image → `gcloud run deploy --env=uat` → `firebase deploy --only hosting:uat`
        - [ ] Add .github/workflows/deploy-prod.yml — `workflow_dispatch` only (manual), `--env=prod` + `firebase deploy --only hosting:prod`
        - [ ] GCP service account + Workload Identity Federation for GHA → GCP auth (matches pattern of other workspace services — copy from client-reporting-api .github/workflows/)
        - [ ] Test deploy-staging by pushing a trivial commit (e.g. README typo fix)
      Full-execution criterion: trivial commit → `gh run list --branch main --repo IggyIkenna/agent-orchestrator --limit 3` shows quality-gates AND deploy-staging both green within 10min; `gcloud run revisions list --service agent-orchestrator-staging` shows new revision deployed with matching commit SHA in container metadata. Verified via: end-to-end timestamp comparison + curl /healthz returns new uptime_seconds reset.
    status: todo

  - id: p5-prod-cutover
    content: |
      - [ ] [HUMAN+AGENT] P5. Phase 5 — Prod cutover + Harsh laptop decommission (depends on P4 + ≥1-week staging soak + **hard gate: workers-on-VMs successor plan reaches D3**)
        - [ ] **HARD PREREQUISITE** for the "shut down laptop nginx" step below: `agent_orchestrator_workers_on_vms_2026_05_XX.md` (TBD slug) must reach D3 first. Reason: Cloud Run containers cannot tmux-spawn; killing Harsh's laptop with workers still tmux-spawning there kills the workers. Workers must move to VMs before laptop decommission.
        - [ ] Manual `gcloud run deploy --env=prod` (workflow_dispatch on deploy-prod.yml) — first prod deployment
        - [ ] Configure prod GCS state bucket: create gs://agent-orchestrator-state-prod/ (europe-west4, lifecycle: 30-day version retention); IAM bind to prod Cloud Run SA
        - [ ] Set ORCHASTRATOR_GCS_BUCKET=agent-orchestrator-state-prod on prod Cloud Run (covers TODO.md "Off-laptop continuity" requirement)
        - [ ] One-shot state migration: gsutil cp Harsh's laptop data/state/state.json → gs://agent-orchestrator-state-prod/state.json (validated via diff after prod startup reads it back)
        - [ ] Bootstrap users on prod (ikenna + harsh, separate JWT secret from staging)
        - [ ] Both operators switch primary dashboard bookmark to https://agent-orchestrator.odum-research.com
        - [ ] 7-day dual-run period: laptop `orch.epiphanytechnologies.com` remains live as fallback (no migration of laptop state — laptop is read-only after this point); explicitly mark via README on laptop "READ-ONLY FALLBACK 2026-MM-DD → 2026-MM-DD+7"
        - [ ] After 7 consecutive days no fallback: shut down laptop nginx site (`sudo rm /etc/nginx/sites-enabled/orch.epiphanytechnologies.com && sudo systemctl reload nginx`) + remove orch.epiphanytechnologies.com DNS record
      Full-execution criterion: Both operators using https://agent-orchestrator.odum-research.com daily for 7 consecutive business days with zero fallback to laptop URL (verified via Cloud Run access logs: 0 hits to laptop nginx during business hours over 7-day window). data/state/state.json mtime in gs://agent-orchestrator-state-prod/ updated within last 30min during business hours. Laptop nginx site file removed + DNS record gone. Verified via: `gcloud storage ls -L gs://agent-orchestrator-state-prod/state.json | grep "Update time"` + `dig orch.epiphanytechnologies.com +short` returns empty.
    status: todo

  - id: p6-codex-claudemd-updates
    content: |
      - [ ] [AGENT] P6. Phase 6 — Codex SSOT + CLAUDE.md updates (can run concurrent with P5 1-week soak)
        - [ ] New codex doc unified-trading-pm/codex/04-architecture/agent-orchestrator-overview.md (purpose, deployment shape mirroring UI's pattern, secret model via GCP Secret Manager, auth flip rationale, GCS state mirror, dashboard URL + local-dev URL + port 8026)
        - [ ] Update unified-trading-pm/codex/08-workflows/local-dev.md: add port 8026 entry + "agent-orchestrator local dev" subsection (`uv sync && scripts/dev.sh`)
        - [ ] Update CLAUDE.md "Key repo map": register agent-orchestrator alongside DART + client-reporting + deployment-api as a workspace service. Note: ikenna_orchestrator/ + harsh_orchestrator/ LEDGER.md files remain as offline-review fallback but agent-orchestrator dashboard is authoritative work-split surface
        - [ ] Update agent-orchestrator/README.md "Quick start" + "public URL" sections to point at the new odum-research.com URLs (replace orch.epiphanytechnologies.com)
        - [ ] Update agent-orchestrator/docs/OPERATIONS.md "Behind a public domain" section: replace the laptop-nginx+Let's-Encrypt recipe with the Firebase-Hosting+Cloud-Run recipe used by the rest of the workspace
        - [ ] Strike completed TODO.md items: "Off-laptop continuity" (Phase 5), "Strict auth" (Phase 3), "Slack notification when blocked" (handed off to slack-followup plan)
      Full-execution criterion: `grep agent-orchestrator unified-trading-pm/cursor-configs/CLAUDE.md` returns the new repo-map entry. New codex file head-50 reads cleanly with frontmatter. Old `orch.epiphanytechnologies.com` references in agent-orchestrator/docs/ replaced (verified via `grep -r epiphanytechnologies agent-orchestrator/ | wc -l` returns 0 except in historical TODO.md "Done since" entries).
    status: todo

isProject: true
---

# Agent Orchestrator → Cloud Run on odum-research.com

> **What this is.** Take Harsh's already-built FastAPI + Vite-dashboard orchestrator (currently running on his laptop at
> `orch.epiphanytechnologies.com` behind nginx + Let's Encrypt) and move it to the workspace's standard deployment
> fabric: Firebase Hosting in front of Cloud Run, served at `agent-orchestrator.{staging.,}odum-research.com`. Same
> infra primitives as `unified-trading-system-ui` (DART) — no new infra needed.
>
> **Why now.** (1) Laptop deploy is a single point of failure + makes Slack push notifications harder to wire (we'd have
> to do it twice — once on laptop, once after Cloud Run cutover). Operator explicitly chose to wait the extra day to do
> it once. (2) Strict auth flip (TODO.md item) is more legitimate from a real Cloud Run service than a permissive laptop
> nginx. (3) Cross-operator usage requires a public-stable URL not coupled to either laptop.
>
> **Decisions captured 2026-05-19 (operator-confirmed):**
>
> 1. Match workspace pattern: ONE GCP project (`central-element-323112`) with env tier (staging vs prod as separate
>    Cloud Run services).
> 2. Service name: `agent-orchestrator` (disambiguates from any `orchestrator-service` collision in the workspace).
> 3. DNS records: operator (Ikenna) will paste records into **Squarespace DNS** (confirmed 2026-05-19) when Firebase
>    Console provides them at Phase 2 kickoff.
> 4. Harsh's laptop deploy stays as fallback for 1 week after Phase 5 prod cutover; decommissioned cleanly after.
> 5. Plan-first workflow per CLAUDE.md doc→plan→code.
> 6. **No separate Firebase project / no edits inside `unified-trading-system-ui`** (operator clarification mid-draft):
>    `firebase.json` + `.firebaserc` live in the agent-orchestrator repo but point at the same Firebase project
>    (`central-element-323112`) used by DART. The new subdomain is an additional hosting target on that shared project —
>    no service-extra inside the UI repo.
> 7. **Scope expansion captured as named successor plans** (operator clarification mid-draft): worker execution migrates
>    from laptop tmux to VMs; multi-Claude-account failover; Slack notifications. All three become follow-up plans
>    landing AFTER P5 prod cutover (this plan is the prerequisite — once the backend is on Cloud Run + dashboard is at a
>    stable URL, the worker-VM + account-failover + Slack work all sit cleanly on top). See **Out of scope** table
>    below.
> 8. **Operator-only steps (Ikenna handles manually — agent pings when ready)** (operator-confirmed 2026-05-19):
>    - **Squarespace DNS record paste** (Phase 2: 2 records per subdomain × 2 subdomains = 4 record pastes total).
>    - **Slack workspace setup**: Slack app creation, webhook URL, bot token, channel `#agent-orchestrator-alerts` — all
>      handled by Ikenna in the Slack admin UI as part of the Slack successor plan. Agent waits for credentials before
>      wiring.
>    - **Firebase Console "Add custom domain" clicks** (Phase 2: required to get Firebase to issue the DNS records that
>      then go to Squarespace).
>    - All other Phase 0-6 steps: agent executes autonomously without waiting.

---

## Phase DAG

```
P0 (compliance scaffold + rename)
   │
   ▼
P1 (Cloud Run staging deploy)
   │
   ▼
P2 (Firebase Hosting + custom domains)  ◄── HUMAN step: Firebase Console + DNS paste
   │
   ▼
P3 (strict-auth flip on staging)
   │
   ▼
P4 (CI/CD wire-up)
   │
   ▼
P5 (prod cutover + 7-day soak + laptop decommission)  ◄── HUMAN step: workflow_dispatch + DNS paste
   │
   └── P6 (codex + CLAUDE.md updates) — can run concurrent with P5's 7-day soak window
```

Sequential — no internal parallelism within each phase except where called out. Phase boundaries are QG gates: next
phase cannot start until prior phase's Full-Execution Criterion is verified by `[ ]` → `[x]` flip on its checkbox.

---

## Pre-audit manifest

**What changes externally** (downstream consumers must update):

| Affected surface                                                                 | Action                                                                                                     |
| -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `IggyIkenna/orchestrator-service` GitHub repo                                    | Rename to `IggyIkenna/agent-orchestrator`. GitHub auto-redirects old URLs; PR refs preserved.              |
| `unified-trading-system-repos/orchestrator-service/` local dirs (both operators) | Rename to `agent-orchestrator/`. Operators re-clone or `git mv` locally; no auto-redirect for local paths. |
| CLAUDE.md references to ikenna_orchestrator/ + harsh_orchestrator/ LEDGER.md     | Keep — these stay as offline fallback. Add agent-orchestrator as authoritative live surface alongside.     |
| `orch.epiphanytechnologies.com` references in any workspace doc                  | Replace with `agent-orchestrator.odum-research.com` after P5 cutover.                                      |
| Harsh's bookmarks, his terminal aliases, anything else laptop-bound              | Out of scope — Harsh handles his own side.                                                                 |

**What does NOT change**:

- Server's internal HTTP API contract (`/api/slots/*`, `/api/agents/*`, `/api/auth/*` etc.) — unchanged.
  Backwards-compat for any agents/scripts that POST to it.
- Dashboard's tmux-spawn flow — unchanged (tmux still local on each operator's box; Cloud Run hosts state + dispatch,
  not agent execution).
- Worker/main/review/backup agent boot prompts — unchanged. Only `<SERVER_URL>` substitution flips.
- State file format (data/state/state.json) — unchanged; just moves storage from laptop disk to GCS bucket at P5.

**What I'm explicitly NOT verifying in pre-audit** (deferred to Phase 0 first step):

- Whether any other workspace consumer imports from `orchestrator-service` Python package name. The
  `unified-trading-system-repos/orchestrator-service/` is structured as a standalone server, not a pip-installed dep, so
  this should be empty — but P0 first todo verifies.

---

## Out of scope (named successor plans)

| Item                                                                                                                                                                                        | Successor                                                                                                                            | Why deferred / blocked-by                                                                                                                                                                                                                                                                                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Worker execution on VMs** (move worker tmux sessions from laptops to GCE VMs — long-running per-slot worker VMs with auto-restart, gcloud-managed lifecycle, no laptop dependency)        | `plans/active/agent_orchestrator_workers_on_vms_2026_05_XX.md` — to be written immediately after P5.                                 | Currently `POST /api/slots/{id}/spawn` runs `tmux new-session` on whatever box the backend is on. After P5, that's a Cloud Run container — no tmux possible. Worker execution MUST move to dedicated VMs that the Cloud Run backend ssh-spawns into. This is the big architecture shift the operator called out 2026-05-19. |
| **Multi-Claude-account failover + parallelism** (handle rate-limit hits by switching to a second Anthropic account; track usage per-account; failover N→M on cap-hit; surface in dashboard) | `plans/active/agent_orchestrator_multi_account_failover_2026_05_XX.md` — to be written after worker-VMs plan lands.                  | Today `data/config/accounts.json` lists one account (`harsh-primary`). Operator wants parallelism across 2+ accounts + automatic failover when one hits its 5h cap. Builds on worker-VMs because each worker invocation needs to be tagged with an account_id, and failover means re-dispatching to a different VM/account. |
| **Slack push notifications** (blocked, stale, failed events)                                                                                                                                | `plans/active/agent_orchestrator_slack_notifications_2026_05_XX.md` — to be written after P5 prod cutover lands.                     | Webhook URL + bot token via GCP Secret Manager; one shot once Cloud Run service is stable. Wiring is `add_blocked` + `slot_stale` + `slot_failed` event hooks → POST to Slack webhook.                                                                                                                                      |
| GCS per-event streaming (per-event JSON to `events/<date>/<hh:mm>_<type>.json`)                                                                                                             | Defer per TODO.md guidance ("Build when 2+ backends are in real use").                                                               | n/a                                                                                                                                                                                                                                                                                                                         |
| Cross-backend aggregated view                                                                                                                                                               | Defer. After P5 cutover both operators share one backend — aggregation no longer needed.                                             | n/a                                                                                                                                                                                                                                                                                                                         |
| Backlog editing UI                                                                                                                                                                          | Defer per TODO.md.                                                                                                                   | n/a                                                                                                                                                                                                                                                                                                                         |
| Mock backend (`/demo` subpath)                                                                                                                                                              | Out of scope — Harsh's `orchastrator-demo.service` setup can be ported separately if useful, but not load-bearing for the migration. | n/a                                                                                                                                                                                                                                                                                                                         |

---

## Risks + open questions

1. **DNS provider unknown until P2 kickoff.** Mitigation: 4 likely candidates (Cloud DNS, Cloudflare, Google Domains,
   Squarespace); operator identifies + clicks at kickoff. If access is missing, P2 stalls; we can fall back to a
   temporary `*.firebaseapp.com` URL while resolving.
2. **GitHub repo rename touches Harsh's local clone.** Coordinate with Harsh before pushing the rename: he needs to
   either `git remote set-url origin git@github.com:IggyIkenna/agent-orchestrator.git` or re-clone. Add to
   `_agent_pings.md` cross-side notification at P0 start.
3. **`orchestrator-service` directory rename in the workspace.** Some agents may have hardcoded paths. Mitigation: P0
   first step greps workspace for hardcoded `orchestrator-service/` paths; replaces with `agent-orchestrator/`. Trace
   any remaining hits via `_agent_pings.md`.
4. **Phase 5 7-day soak might catch real outages.** Acceptance: laptop fallback IS the safety net for those 7 days. If
   laptop fails too, both operators degrade to git-history + CLI work-split mode (pre-2026-05-16 baseline).
5. **Cost.** Cloud Run idle cost ~$5-15/mo; Firebase Hosting free tier covers expected traffic; GCS state bucket <$1/mo.
   Total ~$15-25/mo additional GCP spend. Accepted by operator.

---

## Codex SSOT updates (per HARD RULE — enumerated at plan-write time)

Per CLAUDE.md "Post-Plan-Phase Codex Audit (HARD RULE)":

| Codex doc                                              | Action                                                                                                                  |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| `codex/04-architecture/agent-orchestrator-overview.md` | NEW at P6. Architecture, deploy shape, auth, state mirror.                                                              |
| `codex/08-workflows/local-dev.md`                      | UPDATE at P6. Add port 8026 + agent-orchestrator local dev block.                                                       |
| `cursor-configs/CLAUDE.md` "Key repo map" line         | UPDATE at P6. Add agent-orchestrator to the list.                                                                       |
| `codex/05-infrastructure/launcher-script-ssot.md`      | UPDATE at P1. Register `deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh` as a canonical launcher.     |
| `agent-orchestrator/docs/OPERATIONS.md` (repo-local)   | UPDATE at P6. Replace "Behind a public domain (nginx + Let's Encrypt)" recipe with Firebase Hosting + Cloud Run recipe. |

---

## Full-Execution closeout summary (filled at P5 + P6 completion)

To be filled in when the plan archives. Pattern: per-phase, list (a) what ran on real infra, (b) commit SHA, (c)
verification command + actual output. Plan does NOT archive until all 7 phases have a row here.

| Phase | What ran (cmd + duration) | Verification (cmd + observed output) | SHA |
| ----- | ------------------------- | ------------------------------------ | --- |
| P0    | _pending_                 | _pending_                            | —   |
| P1    | _pending_                 | _pending_                            | —   |
| P2    | _pending_                 | _pending_                            | —   |
| P3    | _pending_                 | _pending_                            | —   |
| P4    | _pending_                 | _pending_                            | —   |
| P5    | _pending_                 | _pending_                            | —   |
| P6    | _pending_                 | _pending_                            | —   |
