---
doc_type: codex-ssot
title: agent-orchestrator — deploy + infra reference (the single central orchestrator VM)
summary:
  Deploy + infra reference for the agent-orchestrator central API VM (EC2 13.113.200.22) — SSH access, the systemd-unit
  install script with the KillMode/PrivateTmp/ReadWritePaths flags that must stay, TLS+DNS+CORS setup, and the
  HISTORICAL Cloud Run shape kept only for cloud-agnostic optionality (AWS EC2 is the live target).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, deployment-service, unified-trading-library, unified-trading-system-ui]
scope: [engineer, admin]
tags:
  [orchestrator, infrastructure, aws, ec2, deployment, cloud-run, dns, ci-runner-vm, ci-escalation-runner, glue-runner]
related:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/05-infrastructure/agent-orchestrator-api-host.md,
    /codex/05-infrastructure/launcher-script-ssot.md,
  ]
created: 2026-05-19
authoritative_for:
  [
    agent-orchestrator central API VM deploy + infra reference,
    CI-runner VM identity and split-off history (ci-escalation-runner-vm-1),
  ]
referenced_by:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/05-infrastructure/agent-orchestrator-api-host.md,
    /codex/08-workflows/agent-orchestrator-e2e-operator-runbook.md,
    plans/audit/instructions/orchestrator_master_audit_instructions.md,
  ]
owner:
last_reviewed: 2026-08-09
code_refs:
last_updated: 2026-08-09
author: ikenna-claude-subagent
---

# agent-orchestrator — Deploy + Infra Reference

> **Scope**: This doc covers deploy + infra for the **single central orchestrator VM** — the one TLS-terminating box
> (EC2 `13.113.200.22`, id `planning`) that runs the backend API and hosts all N slot workers as in-process tmux
> sessions. The dashboard SPA itself is **Firebase-hosted** (§ "CORS + SPA cross-origin" below) and calls this VM
> cross-origin — the VM does not serve the SPA. There are no epic VMs (that fleet was retired 2026-06-27; topology SSOT:
> [`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`](/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md)).
> The separate interactive-only `human-planning` VM (`i-0dd9812a96cdda5dc`) was TERMINATED 2026-08-03 — the `planning`
> VM above is now the only VM; do not reference `human-planning` as a live host.
>
> **Cloud-agnostic posture**: the VM runs on AWS EC2 ap-northeast-1. The bootstrap, secrets, and launcher pipeline
> support a `CLOUD_PROVIDER=gcp` toggle to re-spin on GCE if cost / availability ever forces it; no GCP VMs run at
> present and there is no plan to switch back. The Cloud Run shape documented further below is **historical reference
> only** — kept so the legacy deploy scripts in `launcher-script-ssot.md` still make sense in context.
>
> Architecture SSOT:
> [`/codex/04-architecture/agent-orchestrator-overview.md`](/codex/04-architecture/agent-orchestrator-overview.md) ·
> Operator runbook: `/codex/08-workflows/agent-orchestrator-e2e-operator-runbook.md` · Plan-of-record (archived):
> `plans/archive/2026_05/agent_orchestrator_cloud_run_deployment_2026_05_19.md` · Launcher SSOT:
> `/codex/05-infrastructure/launcher-script-ssot.md`

---

## Central API VM (EC2 — `13.113.200.22`)

| Resource       | Value                                                                                                                                                                                                                                                                                                                                                                                   |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Instance       | `i-0c9b283b31d6b5ca7` — `m8i.2xlarge` (8 vCPU / 32 GB Intel Granite Rapids). Live-confirmed `running` 2026-08-09 (`aws ec2 describe-instances --instance-ids i-0c9b283b31d6b5ca7`). **Distinct box from the dedicated CI-runner VM** (`i-042a6332509482556`, § "CI-runner fleet" below) — the two happen to share an instance type today, but are separate hosts; do not conflate them. |
| Region / AZ    | `ap-northeast-1` / `ap-northeast-1c`                                                                                                                                                                                                                                                                                                                                                    |
| Elastic IP     | `13.113.200.22` (allocation `eipalloc-07b7bfe509d63c477`)                                                                                                                                                                                                                                                                                                                               |
| OS             | Ubuntu 24.04 LTS, kernel 6.17                                                                                                                                                                                                                                                                                                                                                           |
| Service        | systemd unit `orchestrator.service`, runs as user `ubuntu`                                                                                                                                                                                                                                                                                                                              |
| Listen         | `127.0.0.1:8765` behind nginx (`api.agent-orchestrator.odum-research.com` :443 with Let's Encrypt)                                                                                                                                                                                                                                                                                      |
| Workspace root | `/home/ubuntu/unified-trading-system-repos/`                                                                                                                                                                                                                                                                                                                                            |
| Slot worktrees | `.tabs/1..17/` (code-only ~3.7 GB each)                                                                                                                                                                                                                                                                                                                                                 |
| Root EBS       | `vol-0b4f0237fa0f5cd0f` — `gp3`, 700 GB / 16000 IOPS / 1000 MB/s provisioned (live-confirmed 2026-08-07 via `describe-volumes`; grown from the 300→500GB progression documented in Disk hygiene below)                                                                                                                                                                                  |
| Cost           | ~$1/hr on-demand — **AWS credits do NOT reliably cover this** (re-confirmed 2026-08-03, live `aws ce get-cost-and-usage`: July 2026 real out-of-pocket cost $1,020, August 1-4 real cost $268 with only $0.01 credited — treat spend as real, not moot). Stop the instance when idle to halt compute                                                                                    |

### SSH access

```bash
# One-time on operator's Mac: fetch the keypair from AWS Secrets Manager
aws secretsmanager get-secret-value \
  --region ap-northeast-1 --secret-id agent-orchestrator-vm-ssh-private \
  --query SecretString --output text > ~/.ssh/agent-orchestrator-key
chmod 600 ~/.ssh/agent-orchestrator-key

# ~/.ssh/config alias (one-time)
cat >> ~/.ssh/config <<'EOF'
Host agent-orchestrator-vm
  HostName 13.113.200.22
  User ubuntu
  IdentityFile ~/.ssh/agent-orchestrator-key
  ServerAliveInterval 60
EOF

# Then any time:
ssh agent-orchestrator-vm
```

### systemd unit deploy via install script (post-2026-05-20)

The SSOT systemd unit lives at `agent-orchestrator/scripts/orchestrator.service`. To deploy changes:

```bash
ssh agent-orchestrator-vm
cd /home/ubuntu/unified-trading-system-repos/agent-orchestrator
git pull --ff-only origin main
bash scripts/install-orchestrator-service.sh --operator ubuntu --dry-run   # preview
bash scripts/install-orchestrator-service.sh --operator ubuntu --restart   # apply
```

Closes the historical SSOT-drift footgun. Required flags in the SSOT that MUST stay:

- `KillMode=process` — without this, `systemctl restart` SIGKILLs the whole cgroup, nuking all spawned workers
- `PrivateTmp=no` — orchestrator + operator must share `/tmp/tmux-<uid>/default` socket for `has_session()` to work
- `ReadWritePaths=/tmp` — `ProtectSystem=strict` makes `/tmp` read-only otherwise; tmux daemon silent-dies trying to
  create `/tmp/tmux-<uid>/default`. This was the root cause of the 2026-05-20 spawn endpoint silent failure.
- `ReadWritePaths=/home/<op>/.aws` + `.config` + `.claude` + `.cache` — spawned tmux+claude workers need these to
  refresh OAuth tokens / read AWS creds / update gcloud ADC / cache

Full root-cause + fix audit: `plans/archive/issues/orchestrator_spawn_tmux_silent_failure_2026_05_20.md`.

### TLS + DNS

- DNS A record `api.agent-orchestrator.odum-research.com` → `13.113.200.22` in Squarespace (managed under the
  `odum-research.com` zone; despite Squarespace UI, actual DNS is on Google Cloud DNS post-Squarespace's 2023 Google
  Domains acquisition)
- CAA record `0 issue "letsencrypt.org"` (alongside the existing `0 issue "pki.goog"`) — added 2026-05-19 to unblock
  certbot
- Cert issued via
  `sudo certbot --nginx -d api.agent-orchestrator.odum-research.com --email ikenna@odum-research.com --agree-tos --non-interactive --redirect`;
  auto-renew via `certbot.timer`

### CI-runner fleet — split off to a dedicated VM (2026-08-05)

This box previously ran BOTH the orchestrator role AND ~25 repos' worth of self-hosted GitHub Actions runner pools
(`github-glue-runner*` systemd units) colocated on the same VM — the confirmed root cause of the fleet-wide CI capacity
crisis (`/plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`: load average 25-65 on
this box's 16 vCPUs). All 25 pools have now been migrated to a dedicated VM, `i-042a6332509482556`
(`ci-escalation-runner-vm-1`, ap-northeast-1) — confirmed zero `github-glue-runner*` units remain active on this
(planning) box (`/plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`). **Naming gotcha**:
"escalation" in this box's NAME is unrelated to the agent-orchestrator's own `/api/escalations/active` (stuck-PR worker
assignment, surfaced in deployment-ui's Repos-CI board via
`deployment-api/deployment_api/routes/_repo_ci_escalations.py`) — the name is a holdover from this box's origin as an
emergency overflow VM during the capacity crisis; its actual, current, sole job is hosting the fleet's self-hosted GHA
workflow runners, nothing escalation-specific. **This box's instance type changed 2026-08-08** — downsized from
`c8i.4xlarge` (16 vCPU / 32 GB) to `m8i.2xlarge` (8 vCPU / 32 GB) per
`/plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` Part 8 todo (a cross-family
change, not just a size step down — RAM was deliberately kept at 32 GB per that audit's own Part 5 finding that halving
RAM would be actively dangerous, so a `c8i.2xlarge`, at only 16 GB, was rejected in favor of `m8i.2xlarge`), after ~21h
of post-fix live load data (14,819 samples, `load_avg_1m` max 7.84 against the target's own 8 vCPUs, zero OOM-kills)
confirmed the downsize was safe; operator-confirmed before execution. Live-confirmed 2026-08-09 (this update):
`aws ec2 describe-instances --instance-ids i-042a6332509482556` → `m8i.2xlarge`, `running`, private IP `172.31.3.59`, AZ
`ap-northeast-1c`. Its root volume, `vol-03880fe9bf1ea805b`, is live-confirmed at **12,000 IOPS / 312 MB/s**
(`aws ec2 describe-volumes --volume-ids vol-03880fe9bf1ea805b`) — matching that instance size's own EBS baseline: IOPS
up from the pre-downsize interim bump's 6,000, throughput down from its 500 MB/s (both now at the smaller instance's own
baseline, not a straight "up from" on both axes). Do not describe this box as still hosting runners on the planning VM,
and do not assume it is still `c8i.4xlarge` or on the interim 6,000/500 volume spec. Full runbook for a from-scratch
relaunch of this box specifically: `/codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md`.

### Disk hygiene

**2026-07-27 incident**: root disk hit 96% used (278/290 GB). Two independent accumulation patterns, both now fixed:

- **Docker image sprawl**: repeated local builds of `market-tick-data-service` / `deployment-api` /
  `unified-trading-library` (each 4-6 GB) left ~15 old `<none>`-tagged images sitting alongside the current one —
  `docker system df` showed 61 GB total / 14 GB reclaimable. `docker image prune -f` only recovers a modest amount in
  practice (old images often share underlying layers with the current tag, so the naive per-image size sum overstates
  real reclaimable space). No automated prune is wired up yet — **re-run `docker image prune -f` periodically** (or wire
  it into whatever build step produces these images) rather than treating one cleanup as permanent.
- **`/tmp` (2 GB tmpfs, RAM-backed, separate from the root EBS volume) filled to 100%**: the stock systemd `tmp.conf`
  ships a 30-day cleanup age, but this VM's 17 concurrent worker slots create scratch files (mktemp dirs, QG artifacts,
  ad-hoc check outputs) that are done within minutes to hours — 30 days let it accumulate for weeks before the daily
  `systemd-tmpfiles-clean.timer` tick ever had a reason to delete anything. Fixed with a local override,
  `/etc/tmpfiles.d/tmp-aggressive-cleanup.conf` (`D /tmp 1777 root root 1d`), which takes precedence over the stock
  `/usr/lib/tmpfiles.d/tmp.conf` without editing the shipped file. The existing daily timer now actually does something;
  no new cron/timer needed.
- **Root volume resized 300 GB → 500 GB** (live, `aws ec2 modify-volume` + `growpart` + `resize2fs`, no downtime) as
  headroom against future recurrence — +$19.20/mo (gp3 is $0.096/GB-month in ap-northeast-1, confirmed via the AWS
  Pricing API). Deliberately NOT sized back down despite the above fixes: even post-cleanup usage sat at 280 GB, which
  would leave only ~20 GB of headroom in a 300 GB volume — the same tight margin that caused this incident. EBS volumes
  can only grow live; shrinking back would require a full new-volume data migration on the live root disk, a materially
  riskier operation than the $19/mo it would save.
- **Gotcha hit while resizing**: `growpart` internally shells out to `sfdisk --list` and captures its output via a temp
  file — with `/tmp` already full, that capture silently failed, so `growpart` errored with a confusing
  `failed [sfd_list:1]` that had nothing to do with the partition table itself. Free `/tmp` space first if `growpart`
  fails this way. Also needed one GPT-specific step first: after growing a GPT-partitioned disk, `sgdisk -e <device>`
  must relocate the backup GPT header to the new end-of-disk before `growpart` will succeed (`sfdisk --list` warns
  `GPT PMBR size mismatch` until this is done).

Full incident write-up: `plans/archive/issues/ao_vm_disk_and_tmp_cleanup_2026_07_27.md`.

### CORS + SPA cross-origin

The Firebase-hosted SPA at `https://agent-orchestrator.odum-research.com` calls the VM at
`https://api.agent-orchestrator.odum-research.com` cross-origin. CORS allow-list is in `server/server.py` and includes
both prod + staging SPA origins + the raw `*.web.app` Firebase URLs. Override via `ORCHESTRATOR_CORS_ORIGINS` env var
(comma-separated).

The SPA's `BOOTSTRAP_URL` (in `dashboard/src/App.tsx`) maps SPA hostname → companion api.\* host explicitly. So the
dashboard talks to the right backend without same-origin nginx proxy.

---

## Cloud Run service shape (HISTORICAL — superseded 2026-05-20 by EC2)

> **Not running today.** The Cloud Run services described below were the first deployment target (mid-May 2026) and were
> superseded by the EC2 central API VM during the 2026-05-20 cutover. The Cloud Run images and deploy script are still
> in the repo for cloud-agnostic optionality (re-spin on Cloud Run if EC2 ever falls over and AWS is the wrong answer)
> but the project is **AWS EC2 today and for the foreseeable future**. Treat this section as reference for what the
> alternative shape would look like, not as current state.

Two independent services — one per env. No silent default.

| Env  | Cloud Run service            | Image tag     | Region       | GCP project            |
| ---- | ---------------------------- | ------------- | ------------ | ---------------------- |
| prod | `agent-orchestrator`         | `:production` | europe-west4 | central-element-323112 |
| UAT  | `agent-orchestrator-staging` | `:uat`        | europe-west4 | central-element-323112 |

**First-live revision** (UAT, P1 2026-05-19): `agent-orchestrator-staging-00006-5vt`

**Resource allocation** (UAT — same shape applies to prod):

| Resource      | Value                                                                    |
| ------------- | ------------------------------------------------------------------------ |
| Memory        | 1Gi (UTL transitive imports use ~527 MB on cold start; 512Mi caused OOM) |
| CPU           | 1 vCPU                                                                   |
| Min instances | 0                                                                        |
| Max instances | 3                                                                        |
| Concurrency   | Cloud Run default (80)                                                   |

**Runtime env**:

```
ORCHESTRATOR_MODE=live         # set via --set-env-vars at deploy
PORT=8080                      # set in Dockerfile; Cloud Run uses this
ORCHESTRATOR_PUBLIC_URL=...    # from config/docker-build.env.{uat|production}
```

**Secrets** (bound via `--update-secrets` after P3 auth flip):

```
ORCHASTRATOR_JWT_SECRET=ORCHASTRATOR_JWT_SECRET:latest
AGENT_ORCHESTRATOR_SLACK_WEBHOOK=AGENT_ORCHESTRATOR_SLACK_WEBHOOK:latest
AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET=AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET:latest
```

---

## Image build flow

Image registry: `europe-west4-docker.pkg.dev/central-element-323112/cloud-run-source-deploy/agent-orchestrator`

Deploy script: `deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh`

```bash
# UAT deploy via Cloud Build (recommended for CI)
bash deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh --env=uat --cloud

# UAT deploy via local docker build (faster for iteration)
bash deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh --env=uat

# Prod deploy (manual workflow_dispatch only — NOT CI-automated)
bash deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh --env=prod --cloud
```

**Cloud Build cache**: `deployment-service/scripts/cloud-run/cloudbuild-agent-orchestrator.yaml` pulls the prior image
tag via `--cache-from` before building. This cuts warm-build time from 5m20s to ~1m46s when only Python source changes
(deps layer is cache-hit).

**Source repo location**: `deployment-service/scripts/cloud-run/` reads `../../../agent-orchestrator` (sibling in the
workspace). The deploy script resolves this at runtime.

---

## Dockerfile shape

Location: `agent-orchestrator/Dockerfile`

Key design decisions:

```dockerfile
ARG PROJECT_ID
FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest AS base

# ... copy source + install deps ...

ENTRYPOINT []   # CRITICAL: clears inherited python ENTRYPOINT from UTL base image
CMD ["sh", "-c", "uvicorn server.server:app --host 0.0.0.0 --port ${PORT}"]
```

**Why `ENTRYPOINT []`**: The UTL base image sets `ENTRYPOINT ["python"]` so UTL services can do `CMD ["-m", "X"]`.
Combined with a shell-form CMD, this produces `python sh -c "uvicorn ..."` which crashes with exit(2) trying to open
"sh" as a Python script. Cleared at P1 (`agent-orchestrator@a3031fd`).

**What this image contains**:

| Copied           | Purpose                                                                                                                       |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `server/`        | FastAPI app + all modules                                                                                                     |
| `agents/`        | Boot-prompt markdown templates (read at runtime by `POST /api/prompts/reload`)                                                |
| `scripts/`       | `manage_users.py` + `check.sh` (for Cloud Run exec debugging)                                                                 |
| `data/config/`   | Committed operator config — backlog, accounts, backends (`.dockerignore` excludes `data/state/` and `data/config/users.json`) |
| `pyproject.toml` | Dep specification (uv.sources stripped before install)                                                                        |

**What this image does NOT contain**:

- Vite dashboard build (served by Firebase Hosting at P2+; API-only image)
- tmux binary (workers-on-VMs successor plan addresses worker execution)
- pre-commit / dev tooling

---

## Runtime env vars

Set via `--set-env-vars` at `gcloud run deploy` time. Controlled by
`agent-orchestrator/config/docker-build.env.{production,uat}`.

```
ORCHESTRATOR_MODE=live
ORCHESTRATOR_PUBLIC_URL=https://agent-orchestrator.staging.odum-research.com  # (uat)
ORCHESTRATOR_PUBLIC_URL=https://agent-orchestrator.odum-research.com           # (prod)
```

For cloud state-snapshot mirroring set `ORCHESTRATOR_S3_BUCKET` (AWS, primary — `uts-orchestrator-state-<account>`)
and/or `ORCHESTRATOR_GCS_BUCKET` (GCP); `SnapshotLoop` no-ops when both are unset.

---

## How to roll back

```bash
# List recent revisions
gcloud run revisions list \
  --service agent-orchestrator-staging \
  --region europe-west4 \
  --project central-element-323112

# Roll back to a specific revision (replace NNNNN with revision number)
gcloud run services update-traffic agent-orchestrator-staging \
  --region europe-west4 \
  --project central-element-323112 \
  --to-revisions agent-orchestrator-staging-NNNNN=100
```

Prod rollback: same command with `agent-orchestrator` (no `-staging`).

---

## How to debug (no SSH on Cloud Run)

Cloud Run containers have no SSH. Use `docker run` locally to exec into the image:

```bash
# Pull the UAT image
docker pull europe-west4-docker.pkg.dev/central-element-323112/cloud-run-source-deploy/agent-orchestrator:uat

# Run interactively (clear ENTRYPOINT, override CMD with shell)
docker run --rm -it \
  --entrypoint "" \
  -e ORCHESTRATOR_MODE=mock \
  europe-west4-docker.pkg.dev/central-element-323112/cloud-run-source-deploy/agent-orchestrator:uat \
  /bin/bash
```

**ARM64 vs AMD64 caveat**: the image is `--platform=linux/amd64`. On an ARM64 Mac (M1/M2/M3), Docker runs it under
emulation. Python execution works but is significantly slower. For quick checks, `python -c "..."` is fine; for anything
CPU-bound, run on a linux/amd64 VM.

**Cloud Run logs** (fastest debugging path):

```bash
gcloud logs read \
  --service agent-orchestrator-staging \
  --region europe-west4 \
  --project central-element-323112 \
  --limit 50
```

---

## P1 first-build issues and fixes

Three blocking issues encountered during first deployment (P1 2026-05-19). Documented here so future re-deploys don't
repeat them:

| Issue                             | Root cause                                                                                    | Fix                                                  | Commit                       |
| --------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ---------------------------- |
| Container crash on startup        | UTL base image `ENTRYPOINT ["python"]` + shell-form CMD → `python sh -c "..."` crash (exit 2) | `ENTRYPOINT []` in Dockerfile                        | `agent-orchestrator@a3031fd` |
| OOM on cold start                 | UTL transitive imports use ~527 MB; Cloud Run default 512Mi too small                         | Memory 512Mi → 1Gi in `deploy-agent-orchestrator.sh` | `deployment-service@b4725fb` |
| `FileNotFoundError: backlog.yaml` | `data/config/` not copied in Dockerfile; server calls `load_backlog()` at startup             | `COPY data/config/ ./data/config/`                   | `agent-orchestrator@d56e70f` |

All three are now baked into the Dockerfile and deploy script. New builds should reach `/health` 200 OK without any of
these re-occurring.

---

## Firebase Hosting fabric (post-P2)

Firebase Hosting fronts the Vite dashboard (static files) and rewrites API traffic to Cloud Run. Mirrors
`unified-trading-system-ui` (DART) fabric.

**Hosting sites** (created 2026-05-19, `central-element-323112` Firebase project):

| Site ID                        | Domain                                         | Status                                   |
| ------------------------------ | ---------------------------------------------- | ---------------------------------------- |
| `agent-orchestrator-uat-site`  | `agent-orchestrator.staging.odum-research.com` | DNS+SSL live; Firebase deploy pending P2 |
| `agent-orchestrator-prod-site` | `agent-orchestrator.odum-research.com`         | DNS+SSL live; Firebase deploy pending P5 |

**DNS** (Squarespace, provisioned 2026-05-19):

- `agent-orchestrator.staging` → `agent-orchestrator-uat-site.web.app` (CNAME)
- `agent-orchestrator` → `agent-orchestrator-prod-site.web.app` (CNAME)

**Rewrite shape** (to be added in `agent-orchestrator/firebase.json` at P2):

```json
{
  "hosting": {
    "rewrites": [
      { "source": "/api/**", "run": { "serviceId": "agent-orchestrator-staging", "region": "europe-west4" } },
      { "source": "/health{,/**}", "run": { "serviceId": "agent-orchestrator-staging", "region": "europe-west4" } },
      { "source": "/readiness", "run": { "serviceId": "agent-orchestrator-staging", "region": "europe-west4" } },
      { "source": "**", "destination": "/index.html" }
    ]
  }
}
```

**Deploy command** (P2+):

```bash
# Deploy dashboard to Firebase Hosting (UAT)
firebase deploy --only hosting:uat \
  --project central-element-323112 \
  -c agent-orchestrator/firebase.json
```

---

## Cloud state bucket (disaster recovery)

`SnapshotLoop` (`server/gcs_sync.py`) mirrors `state.json` + a SQLite hot-copy every 30 min (and on shutdown) to the
cloud bucket(s) set on the central VM's `.env.local`:

- `ORCHESTRATOR_S3_BUCKET` — AWS, the primary path on the current fleet (`uts-orchestrator-state-<account>`).
- `ORCHESTRATOR_GCS_BUCKET` — GCP, the cloud-agnostic mirror; set both to write both clouds.

No-op when unset (local-disk state only). Recovery: restore the snapshot object → restart the service.

---

## Deploy script — launcher registration

`deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh` is registered as a Cloud Run launcher (not a VM
launcher) in `/codex/05-infrastructure/launcher-script-ssot.md` § "Cloud Run launchers". It does NOT need a
`VM_PREFIX_TO_BUCKET` entry or watchdog registration.

The script:

- Requires `--env=prod|uat` (exits 2 without it)
- Supports `--cloud` for Cloud Build path (recommended) or local `docker buildx build`
- Sets `ORCHESTRATOR_MODE=live` via `--set-env-vars`
- Sets `ORCHESTRATOR_PUBLIC_URL` per env
- Memory override: `--memory=1Gi` (deployed at P1)
- References `cloudbuild-agent-orchestrator.yaml` for cache-from warm builds

---

## Cost estimate

| Component                      | Monthly cost                 |
| ------------------------------ | ---------------------------- |
| Cloud Run idle (0–3 instances) | ~$5–15                       |
| Firebase Hosting (static CDN)  | Free tier (expected traffic) |
| GCS state bucket (<10 MB)      | <$1                          |
| **Total**                      | **~$15–25/mo**               |

Accepted by operator (plan decision 2026-05-19).

---

## See also

- `/codex/08-workflows/agent-orchestrator-e2e-operator-runbook.md` — full operator workflows
- `agent-orchestrator/README.md` — architecture overview + local dev
- `/codex/04-architecture/agent-orchestrator-overview.md` — service architecture SSOT
- `/codex/08-workflows/agent-orchestrator-e2e-operator-runbook.md` — day-to-day runbook
- `/codex/05-infrastructure/launcher-script-ssot.md` § "Cloud Run launchers" — script registry
- `plans/active/agent_orchestrator_cloud_run_deployment_2026_05_19.md` — full deployment DAG
