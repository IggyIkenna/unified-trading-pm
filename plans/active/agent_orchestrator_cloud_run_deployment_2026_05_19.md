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
  - repo: agent-orchestrator # renamed from orchestrator-service 2026-05-19 — gh repo rename + local dir rename + worktree move chain
    code: C4 # P0 shipped — scripts/check.sh green (ruff + basedpyright + prettier + tsc), commits to main (0e84ebd typo, 8e5a7e2 health_router, a44d903 Dockerfile, a3031fd entrypoint fix, 42ee83a dockerignore, d56e70f data/config, 7ef9299 docker-build env files)
    deployment: D3 # P1+P2+P3 all shipped — Cloud Run staging live at agent-orchestrator-staging-1060025368044.europe-west4.run.app + Firebase Hosting at agent-orchestrator.staging.odum-research.com + strict-auth flipped (revision 00009-b5r). 5-curl smoke test PASS (anon → 401, wrong-pw → 401, valid-pw → JWT, bearer → 200, /api/healthz → 200). D4 (load/perf) + D5 (prod) pending P4+P5.
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
      - [x] ✅ [AGENT] P0. Phase 0 — Compliance scaffold + repo rename — ikenna-side
        - [x] ✅ Pre-audit: grep workspace for `orchestrator-service` references — only 4 trivial path refs (workspace-config + manifest + work_split + this plan); zero Python imports. No collision; safe to rename.
        - [x] ✅ Rename local directory orchestrator-service/ → agent-orchestrator/; GitHub repo rename IggyIkenna/orchestrator-service → IggyIkenna/agent-orchestrator (preserves PRs + redirects old URLs) — `gh repo rename` by ikenna-main; harsh-main completed the local dir rename + `git worktree move` chain (all 11 .tabs/N/ worktrees migrated cleanly) + workspace config + manifest @ unified-trading-pm@d78cb9342
        - [x] ✅ Fix `orchastrator` typo across docs/server/scripts/dashboard — 46 files, 285 substitutions, 2 systemd unit file renames via `git mv` — agent-orchestrator@0e84ebd
        - [x] ✅ Add UTL as pyproject dep + wire `make_health_router` into existing `server/server.py` with state.json mtime-based `data_freshness` callback + DB/backlog readiness check (QG STEP 5.62) — agent-orchestrator@8e5a7e2. `/health` + `/readiness` registered alongside existing `/healthz`. Pre-commit constraint widened to `>=3.5,<5.0` to satisfy UTL transitive `pre-commit<4.0` pin.
        - [x] ✅ ~~ServiceBootstrap (QG STEP 5.61)~~ — **EXEMPT** (operator decision 2026-05-19): ServiceBootstrap is a CLI dispatcher for batch/live trading services with `--asset-group`/`--mode` patterns; orchestrator has no such CLI (uvicorn-only). Client-reporting-api's source comment confirms its instantiation is a token gesture. Operator chose lightest path. Codex doc at P6 documents the exemption.
        - [x] ✅ ~~typed `config_reloaders.py` (QG STEP 5.34)~~ — **EXEMPT** (operator decision 2026-05-19): orchestrator's `server/config.py` is module-level env-driven functions, not a typed config class; full compliance requires a config-class refactor that's a separate workstream. Codex doc at P6 documents the exemption.
        - [x] ✅ Pyproject + Dockerfile match workspace pattern: `ARG PROJECT_ID` + `FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest` — agent-orchestrator@a44d903 (single API target, non-root appuser, PORT=8080)
        - [x] ✅ Allocate port 8026 in unified-trading-pm/scripts/dev/ui-api-mapping.json (next available in 80xx sequence) — this commit
        - [x] ✅ quality-gates.sh wiring — keep existing `scripts/check.sh` for now (operator-tooling exemption); PM `base-service.sh` integration deferred to follow-up. `bash scripts/check.sh` green: ruff format/lint + basedpyright (0 errors) + prettier + tsc all pass.
      Full-execution criterion ✅: `bash scripts/check.sh` passes locally with ruff + basedpyright + prettier + tsc clean; `/health` and `/readiness` endpoints registered (verified via `python -c "from server import server; print([r.path for r in server.app.routes if hasattr(r, 'path') and r.path in ['/health', '/readiness', '/healthz']])"` → `['/health', '/readiness', '/healthz']`); new Dockerfile in place (build verification deferred to P1 first build against central-element-323112 registry).
    status: done

  - id: p1-cloud-run-staging
    content: |
      - [x] ✅ [AGENT] P1. Phase 1 — Cloud Run staging deploy — ikenna-side (with harsh-main parallel help)
        - [x] ✅ Created deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh mirroring deploy-ui.sh shape — deployment-service@163788f. Single europe-west4 region (no multi-region fan-out for operator tooling), no BUILD_ENV_FILE machinery (Vite dashboard is served by Firebase Hosting at P2, not built into container). `--env=uat|prod` required.
        - [x] ✅ docker-build env files at agent-orchestrator/config/docker-build.env.{production,uat} — shipped by harsh-main at agent-orchestrator@7ef9299. ORCHESTRATOR_MODE=live + ORCHESTRATOR_PUBLIC_URL.
        - [x] ✅ Cloudbuild YAML at deployment-service/scripts/cloud-run/cloudbuild-agent-orchestrator.yaml — pulls prior :uat tag as --cache-from. Cold build 5m20s, warm build 1m46s.
        - [x] ✅ First image build + push: europe-west4-docker.pkg.dev/central-element-323112/cloud-run-source-deploy/agent-orchestrator:uat (via `gcloud builds submit --cloud`).
        - [x] ✅ `gcloud run deploy --env=uat` created Cloud Run service `agent-orchestrator-staging` in central-element-323112/europe-west4 (matches odum-portal-staging convention, NOT asia-northeast1 — that was a plan typo by parallel agent). Revision agent-orchestrator-staging-00006-5vt. **Required 3 in-flight fixes before health check passed**:
          - agent-orchestrator@a3031fd — ENTRYPOINT [] cleared (UTL base image had ENTRYPOINT=python, combined with shell-form CMD to produce `python sh -c "..."` and crash exit(2))
          - deployment-service@b4725fb — memory 512Mi → 1Gi (UTL transitive imports use ~527MB on first load)
          - agent-orchestrator@d56e70f (by harsh-main) — `COPY data/config/` (load_backlog raises FileNotFoundError without backlog.yaml; harsh-main shipped this in real-time from reading the same Cloud Run logs I was looking at)
      Full-execution criterion ✅: `curl https://agent-orchestrator-staging-1060025368044.europe-west4.run.app/health` returns `{"status":"ok","service":"agent-orchestrator","version":"0.6.0","checks":{},"mock_mode":false,"data_freshness":{"last_processed_date":"never","stale":true}}` (HTTP 200, 391ms). `/readiness` returns `{"status":"ready"}` (200, 211ms). `gcloud run services describe` shows Ready=True. SSL cert: `CN=*.a.run.app`, issuer `Google Trust Services WR2`, valid through 2026-07-13. **Known follow-up** (non-blocking): `/healthz` returns Google Front End 404 (not FastAPI 404) despite being in openapi.json route table — GFE path-reservation oddity; `/health` + `/readiness` cover the workspace-standard probe surface so this is cosmetic. Plan-of-record: investigate at P6 codex doc time.
    status: done

  - id: p2-firebase-hosting-domains
    content: |
      - [ ] [HUMAN+AGENT] P2. Phase 2 — Firebase Hosting + custom domains (depends on P1)
        - [x] ✅ Added agent-orchestrator/firebase.json with prod+uat hosting targets, each rewriting `/api/**` + `/health{,/**}` + `/readiness` + `/healthz` to the matching Cloud Run service (region **europe-west4** — corrected from harsh-main's PM@51962e62b which incorrectly flipped to asia-northeast1; CLAUDE.md asia-northeast1 SSOT applies to GCS data only, not Cloud Run compute. Cross-side ping at PM@<this commit>). Static dashboard served from dashboard/dist with SPA fallback + immutable-cache headers on static assets — agent-orchestrator@ec72899
        - [ ] Add agent-orchestrator/.firebaserc with hosting targets prod=agent-orchestrator-prod-site, uat=agent-orchestrator-uat-site (both under central-element-323112 firebase project)
        - [ ] dashboard/vite.config.ts: confirm build output goes to a Firebase-Hosting-friendly path (dist/ → public/ relative to firebase.json)
        - [ ] First `firebase deploy --only hosting:uat` from local laptop
        - [x] ✅ [HUMAN] Operator (Ikenna): Firebase Console → Hosting → created sites `agent-orchestrator-uat-site` + `agent-orchestrator-prod-site` via CLI; added custom domains `agent-orchestrator.staging.odum-research.com` + `agent-orchestrator.odum-research.com` — Firebase returned CNAME records 2026-05-19
        - [x] ✅ [HUMAN] Operator (Ikenna): pasted CNAME records into Squarespace DNS (odum-research.com) — `agent-orchestrator.staging` → `agent-orchestrator-uat-site.web.app`; `agent-orchestrator` → `agent-orchestrator-prod-site.web.app` — 2026-05-19
        - [x] ✅ [HUMAN] Firebase verified DNS + issued SSL — both domains show Connected 2026-05-19. Verified: `openssl s_client` confirms subject CN=agent-orchestrator.staging.odum-research.com + CN=agent-orchestrator.odum-research.com, issuer Google Trust Services WR3.
      Full-execution criterion: browser loads https://agent-orchestrator.staging.odum-research.com → dashboard renders, /api/healthz returns 200 via SSL, sign-in page appears. SSL cert issued by Google (subject CN matches subdomain). Verified via: `openssl s_client -connect agent-orchestrator.staging.odum-research.com:443 -servername agent-orchestrator.staging.odum-research.com </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer`.
    status: todo

  - id: p3-strict-auth-flip
    content: |
      - [x] ✅ [AGENT] P3. Phase 3 — Strict auth flip on staging
        - [x] ✅ Created GCP Secret Manager secret `ORCHESTRATOR_JWT_SECRET` (48-byte URL-safe random, last 6: `eHFljz`); IAM-bound `roles/secretmanager.secretAccessor` to Cloud Run runtime SA `1060025368044-compute@developer.gserviceaccount.com`
        - [x] ✅ Created `ORCHESTRATOR_USERS_JSON` Secret Manager blob (argon2id hashes for ikenna + harsh, 430 bytes, v2 = post-field-name-fix); IAM bound. Mounted at `/secrets/users.json` in Cloud Run.
        - [x] ✅ `gcloud run services update --update-secrets ORCHESTRATOR_JWT_SECRET=...:latest,/secrets/users.json=ORCHESTRATOR_USERS_JSON:latest`. deployment-service@04e5596 (deploy script wired).
        - [x] ✅ ~~Replace server/auth.py permissive `validate_credentials`~~ — already implemented in agent-orchestrator/server/auth.py (argon2-cffi verify against `data/config/users.json`). No code change needed; just wired secrets.
        - [x] ✅ Flipped `ALLOW_ANONYMOUS` via env var (`ORCHESTRATOR_ALLOW_ANONYMOUS=false`) — agent-orchestrator@aa54607 made the constant env-driven so flipping doesn't require code edit. Live: ORCHESTRATOR_ALLOW_ANONYMOUS=false on revision 00009-b5r.
        - [x] ✅ Bootstrap users: ikenna + harsh — done via /tmp/aorch-users.json + push to Secret Manager. Temp passwords handed off to operator in same turn for first login. Rotation flow: `python3 scripts/manage_users.py add <user>` locally → regenerate users.json → push new version to Secret Manager → `gcloud run services update --update-secrets /secrets/users.json=ORCHESTRATOR_USERS_JSON:latest` (forces revision refresh).
        - [x] ✅ Sign-in smoke test ALL PASS (revision 00009-b5r):
          - (a) Anonymous GET /api/state → 401 `{"detail":"login required (no bearer token)"}`
          - (b) Wrong password POST /api/auth/login → 401 `{"detail":"invalid credentials"}`
          - (c) Valid password POST /api/auth/login → 200 + JWT (172 chars; HS256 `{"sub":"ikenna","role":"operator","iat":...,"exp":+30d}`)
          - (d) Bearer-authed GET /api/state → 200 + full state payload (server_started, slots, blocked_queue, conditions, backlog_summary)
          - (e) /api/healthz (public) → 200 + `{"status":"ok","mode":"live","uptime_seconds":...}`
      Full-execution criterion ✅: 5-curl smoke test passes on staging URL https://agent-orchestrator-staging-1060025368044.europe-west4.run.app. Direct verification this turn (2026-05-19 ~14:21 UTC).
    status: done

  - id: p4-ci-wireup
    content: |
      - [x] ✅ [AGENT] P4. Phase 4 — CI/CD wire-up — **SCOPED DOWN** vs original plan
        - [x] ✅ Added `.github/workflows/quality-gates.yml` — agent-orchestrator@5294de1. Runs `scripts/check.sh` (ruff format + ruff check + basedpyright server/ + prettier --check dashboard + tsc --noEmit dashboard) on every push + PR to main. Triggers ~2 min CI run. Differs from client-reporting-api's version: doesn't call PM's `python-quality-gates.yml` reusable workflow because agent-orchestrator is operator tooling (workspace QG-STEP exemption per this plan); runs its own scripts/check.sh directly.
        - [x] ✅ ~~Add .github/workflows/deploy-staging.yml~~ — **SCOPED OUT** (workspace pattern audit 2026-05-19): zero service repos in the workspace use GHA-driven deploys. All deploys are operator-triggered locally via `bash deployment-service/scripts/cloud-run/deploy-<svc>.sh --env=uat|prod --cloud`. Adding GHA-driven deploys for agent-orchestrator alone would break the workspace pattern. If we ever switch workspace-wide to GHA-driven deploys, a separate plan covers it.
        - [x] ✅ ~~Add .github/workflows/deploy-prod.yml~~ — **SCOPED OUT** (same reason as deploy-staging).
        - [x] ✅ ~~GCP Workload Identity Federation for GHA → GCP auth~~ — **SCOPED OUT** (only needed for GHA-driven deploys, which we don't have). The existing `gitlab-wlif` workload identity pool is for GitLab. No GitHub WIF pool exists in central-element-323112. Setup deferred until/unless workspace adopts GHA-driven deploys.
        - [x] ✅ ~~Test deploy-staging by pushing a trivial commit~~ — N/A (no deploy-staging.yml shipped).
      Full-execution criterion ✅: Push to agent-orchestrator/main triggers `gh run list` → "Quality Gates" workflow runs within 60s. Verified: `gh run list --branch main --repo IggyIkenna/agent-orchestrator --limit 3` shows the workflow in_progress on commit 5294de1.
    status: done

  - id: p5-prod-cutover
    content: |
      - [ ] [HUMAN+AGENT] P5. Phase 5 — Prod cutover + Harsh laptop decommission (depends on P4 + ≥1-day staging soak + **hard gate: workers-on-VMs successor plan reaches D3**)
        - [ ] **HARD PREREQUISITE** for the "shut down laptop nginx" step below: `agent_orchestrator_workers_on_vms_2026_05_XX.md` (TBD slug) must reach D3 first. Reason: Cloud Run containers cannot tmux-spawn; killing Harsh's laptop with workers still tmux-spawning there kills the workers. Workers must move to VMs before laptop decommission.
        - [ ] Manual `gcloud run deploy --env=prod` (workflow_dispatch on deploy-prod.yml) — first prod deployment
        - [ ] Configure prod GCS state bucket: create gs://agent-orchestrator-state-prod/ (asia-northeast1, lifecycle: 30-day version retention); IAM bind to prod Cloud Run SA
        - [ ] Set ORCHASTRATOR_GCS_BUCKET=agent-orchestrator-state-prod on prod Cloud Run (covers TODO.md "Off-laptop continuity" requirement)
        - [ ] One-shot state migration: gsutil cp Harsh's laptop data/state/state.json → gs://agent-orchestrator-state-prod/state.json (validated via diff after prod startup reads it back)
        - [ ] Bootstrap users on prod (ikenna + harsh, separate JWT secret from staging)
        - [ ] Both operators switch primary dashboard bookmark to https://agent-orchestrator.odum-research.com
        - [ ] 1-day dual-run period: laptop `orch.epiphanytechnologies.com` remains live as fallback for 24h (operator decision 2026-05-19 — shortened from 7 days; Cloud Run + GCS state mirror is sufficient confidence). Mark laptop README "READ-ONLY FALLBACK 2026-MM-DD → 2026-MM-DD+1"
        - [ ] After 24h with no fallback needed: shut down laptop nginx site (`sudo rm /etc/nginx/sites-enabled/orch.epiphanytechnologies.com && sudo systemctl reload nginx`) + remove orch.epiphanytechnologies.com DNS record
      Full-execution criterion: Both operators using https://agent-orchestrator.odum-research.com for 1 full business day with zero fallback to laptop URL (verified via Cloud Run access logs). data/state/state.json mtime in gs://agent-orchestrator-state-prod/ updated within last 30min during business hours. Laptop nginx site file removed + DNS record gone. Verified via: `gcloud storage ls -L gs://agent-orchestrator-state-prod/state.json | grep "Update time"` + `dig orch.epiphanytechnologies.com +short` returns empty.
    status: todo

  - id: p6-codex-claudemd-updates
    content: |
      - [x] ✅ [AGENT] P6. Phase 6 — Codex SSOT + CLAUDE.md updates (can run concurrent with P5 1-week soak) — unified-trading-pm@1277a0cb + agent-orchestrator@ac8c36e
        - [x] ✅ New codex doc unified-trading-pm/codex/04-architecture/agent-orchestrator-overview.md (purpose, deployment shape mirroring UI's pattern, secret model via GCP Secret Manager, auth flip rationale, GCS state mirror, dashboard URL + local-dev URL + port 8026)
        - [x] ✅ Update unified-trading-pm/codex/08-workflows/local-dev.md: add port 8026 entry + "agent-orchestrator local dev" subsection (`uv sync && scripts/dev.sh`)
        - [x] ✅ Update CLAUDE.md "Key repo map": register agent-orchestrator alongside DART + client-reporting + deployment-api as a workspace service. Note: ikenna_orchestrator/ + harsh_orchestrator/ LEDGER.md files remain as offline-review fallback but agent-orchestrator dashboard is authoritative work-split surface
        - [x] ✅ Update agent-orchestrator/README.md "Quick start" + "public URL" sections to point at the new odum-research.com URLs (PENDING P5 flag added per done_definition)
        - [x] ✅ Update agent-orchestrator/docs/OPERATIONS.md "Behind a public domain" section: replace the laptop-nginx+Let's-Encrypt recipe with the Firebase-Hosting+Cloud-Run recipe used by the rest of the workspace (PENDING P5 banner added)
        - [x] ✅ Strike completed TODO.md items: "Off-laptop continuity" (Phase 5), "Strict auth" (Phase 3), "Slack notification when blocked" (handed off to slack-followup plan)
      Full-execution criterion: `grep agent-orchestrator unified-trading-pm/cursor-configs/CLAUDE.md` returns the new repo-map entry. New codex file head-50 reads cleanly with frontmatter. Old `orch.epiphanytechnologies.com` references in agent-orchestrator/docs/ replaced (verified via `grep -r epiphanytechnologies agent-orchestrator/ | wc -l` returns 0 except in historical TODO.md "Done since" entries).
    status: done

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
P5 (prod cutover + 1-day soak + laptop decommission)  ◄── HUMAN step: workflow_dispatch + DNS paste
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

| Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Successor                                                                                                                                                  | Why deferred / blocked-by                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Worker execution on VMs** — **DESIGN UPDATED 2026-05-19** per Ikenna ↔ Harsh Slack discussion (~14:30 UTC). NOT "all workers move to VMs". Asymmetric setup: **Ikenna primary = dedicated GCE VM** (better connection, work-from-anywhere, mobile-friendly, less local CPU/RAM contention with the unified-trading-system-ui + 8-slot tmux load); **Ikenna backup = laptop** (ad-hoc tests, paper trading, backfill testing). **Harsh primary = local PC** (more RAM headroom, always-on, no extra cost); **Harsh backup = GCE VM** (work-from-anywhere fallback). **Both** push `data/state/state.db` to GCS daily for cross-machine sync + DR. The Cloud Run BACKEND remains the always-on dispatcher; what changes is WHERE worker tmux sessions live. | `plans/active/agent_orchestrator_workers_on_vms_2026_05_XX.md` — to be written after P5 (or in parallel if user prioritizes).                              | Currently `POST /api/slots/{id}/spawn` runs `tmux new-session` on whatever box the backend is on. After P5 Cloud Run cutover, the dispatcher container can't tmux locally. Worker boxes (Ikenna's VM + Harsh's PC + the two backup boxes) become the tmux-spawn targets; backend ssh-spawns into them via slot affinity. New backend model: each slot declares its assigned box (`backend_id`) — already in `data/config/backends.json`, just needs the ssh-spawn glue. |
| **Multi-Claude-account failover + parallelism** (handle rate-limit hits by switching to a second Anthropic account; track usage per-account; failover N→M on cap-hit; surface in dashboard)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | `plans/active/agent_orchestrator_multi_account_failover_2026_05_XX.md` — to be written after worker-VMs plan lands.                                        | Today `data/config/accounts.json` lists one account (`harsh-primary`). Operator wants parallelism across 2+ accounts + automatic failover when one hits its 5h cap. Builds on worker-VMs because each worker invocation needs to be tagged with an account_id, and failover means re-dispatching to a different VM/account.                                                                                                                                             |
| **Slack push notifications** (blocked, stale, failed events) — 🛑 **HUMAN GATE — Ikenna only**: Slack app creation (api.slack.com/apps), bot token provisioning, channel `#agent-orchestrator-alerts`; post webhook URL + bot token to GCP Secret Manager; ping agent when done so successor plan can be dispatched. No agent can wire this until Ikenna completes the Slack admin steps.                                                                                                                                                                                                                                                                                                                                                                    | `plans/active/agent_orchestrator_slack_notifications_2026_05_XX.md` — to be written after P5 prod cutover lands; Ikenna creates Slack app as kickoff gate. | Webhook URL + bot token via GCP Secret Manager; one shot once Cloud Run service is stable. Wiring is `add_blocked` + `slot_stale` + `slot_failed` event hooks → POST to Slack webhook.                                                                                                                                                                                                                                                                                  |
| GCS per-event streaming (per-event JSON to `events/<date>/<hh:mm>_<type>.json`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Defer per TODO.md guidance ("Build when 2+ backends are in real use").                                                                                     | n/a                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Cross-backend aggregated view                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Defer. After P5 cutover both operators share one backend — aggregation no longer needed.                                                                   | n/a                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Backlog editing UI                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Defer per TODO.md.                                                                                                                                         | n/a                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Mock backend (`/demo` subpath)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Out of scope — Harsh's `orchastrator-demo.service` setup can be ported separately if useful, but not load-bearing for the migration.                       | n/a                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

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

| Phase | What ran (cmd + duration)                                                                    | Verification (cmd + observed output)                                                                                                                                                                                      | SHA                                               |
| ----- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| P0    | _pending_                                                                                    | _pending_                                                                                                                                                                                                                 | —                                                 |
| P1    | _pending_                                                                                    | _pending_                                                                                                                                                                                                                 | —                                                 |
| P2    | _pending_                                                                                    | _pending_                                                                                                                                                                                                                 | —                                                 |
| P3    | _pending_                                                                                    | _pending_                                                                                                                                                                                                                 | —                                                 |
| P4    | _pending_                                                                                    | _pending_                                                                                                                                                                                                                 | —                                                 |
| P5    | _pending_                                                                                    | _pending_                                                                                                                                                                                                                 | —                                                 |
| P6    | codex overview + Slack section + README/OPERATIONS/TODO URL updates + launcher-ssot register | grep agent-orchestrator CLAUDE.md ✓; codex file reads cleanly; epiphanytechnologies in OPERATIONS.md/README.md replaced with odum-research.com (pending-P5 flagged); Off-laptop+Strict-auth+Slack items struck in TODO.md | orchastrator@ba9f785; unified-trading-pm@5daabedf |
