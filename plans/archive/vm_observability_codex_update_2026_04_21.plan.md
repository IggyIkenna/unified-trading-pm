---
doc_type: plan
title: VM Observability + Self-Delete Codex Update
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-21
priority: P2
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: business
epic: none
completion_gates: { code: none, deployment: none, business: B1 }
repo_gates:
  - { repo: unified-trading-pm, business: B0 }
depends_on: []
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Context

Two fixes landed 2026-04-21 that together give every VM launched via `setup-data-pipeline-vm.sh` full lifecycle
observability without SSH:

- **`deployment-service cc07649`** — setup script now downloads `heartbeat_daemon.py` to `/tmp/` (was silently missing;
  wrapper warned "observability disabled" and no Pub/Sub / GCS log streaming / registry entries landed).
- **`deployment-service beaa2e5`** — wrapper now reads `VM_SHUTDOWN_ON_COMPLETION` metadata and fires
  `gcloud compute instances delete --self --delete-disks=all` in a detached subshell after the workload returns. Every
  launcher set the metadata; nothing read it. Result: VMs completed rc=0 and ran forever until manual delete (cost
  leak + cleanup chore).

These changes apply to ALL 14 launchers in `deployment-service/scripts/vm/` through the shared wrapper — not
launcher-specific.

Codex needs to document the guarantees + the machinery so future VM touchers know observability is universal.

## Blast radius

- **unified-trading-pm** (only):
  - `/codex/05-infrastructure/vm-tarball-deployment.md` — extend with an "Observability & Lifecycle" section covering
    heartbeat daemon, streaming GCS log, `/api/vm-deployments` registry entry, and self-delete on completion.

## Pre-audit manifest

| File                                                        | Existing content                                    | Action                                                 |
| ----------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------ |
| `/codex/05-infrastructure/vm-tarball-deployment.md`         | Covers tarball refresh + launcher pattern.          | Add §"Observability & Lifecycle" at the end. No reorg. |
| `deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh`     | Wrapper (uploaded to `gs://.../vm/`). Post-beaa2e5. | Read-only reference — link to the self-delete block.   |
| `deployment-service/deployment_service/vm/heartbeat_cli.py` | Daemon implementation.                              | Read-only reference.                                   |
| `deployment-api/deployment_api/routes/vm_deployments.py`    | `/api/vm-deployments` endpoint.                     | Cross-ref in codex: where to view registry entries.    |

## Content to document (outline)

### §"Observability & Lifecycle" (new section)

Three guarantees every VM launched via `launch-*.sh` now provides:

1. **Streaming GCS log** — Every 30 seconds, the heartbeat daemon uploads `/home/ikennaigboaka/logs/<task>.log` to
   `gs://deployment-scripts-central-element-323112/vm-logs/<vm-name>/run.log`. Operators can tail this without SSH:
   `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/<vm-name>/run.log | tail -f` (well, not tail -f on
   GCS — operators re-cat + inspect; diffing between pulls gives live progress).

2. **Deployment registry** — Every VM registers at boot with Firestore- backed `/api/vm-deployments` via the
   heartbeat-cli REGISTER event. Heartbeat every 60s keeps status=running; DEPLOYMENT_COMPLETED / DEPLOYMENT_FAILED on
   exit. Query via `curl -sS 'https://<deployment-api>/api/vm-deployments?status=running' | jq`.

3. **Self-delete on completion** — `VM_SHUTDOWN_ON_COMPLETION=true` in VM metadata triggers
   `gcloud compute instances delete --self --delete-disks=all` in a detached subshell after rc capture. All launchers
   set this metadata by default; operators can disable by omitting from the launcher's METADATA block (rare — only
   needed for post-mortem SSH).

### §"How it works" (inline in the new section)

Brief mechanism diagram:

```
Launcher (launch-*.sh)
    │
    └── gcloud compute instances create
            └── startup-script-url=gs://.../vm/setup-data-pipeline-vm.sh
                    │
                    ├── installs Python + tarballs (tarball-deployment.md)
                    ├── downloads /tmp/vm-exec-with-gcs-tee.sh (cc07649)
                    ├── downloads /tmp/deployment_heartbeat.py
                    ├── downloads /tmp/heartbeat_daemon.py (cc07649)
                    └── _launch_with_tee <cmd>
                            │
                            └── vm-exec-with-gcs-tee.sh
                                    ├── forks heartbeat_daemon.py (60s heartbeat + 30s GCS log)
                                    ├── runs <cmd>, captures rc
                                    ├── daemon archives DEPLOYMENT_COMPLETED|FAILED
                                    └── self-delete if VM_SHUTDOWN_ON_COMPLETION=true (beaa2e5)
```

### §"What this replaces"

Before 2026-04-21, VMs had:

- No `/api/vm-deployments` entries (daemon missing)
- No streaming log (daemon missing)
- No self-delete (metadata unread)

Operators had to SSH + tail local log + manually `gcloud delete`. Multiple VMs from today's session (morning rescan,
historical backfill, forward-poll pre-fix) got stuck RUNNING indefinitely — manual cleanup by the orchestrator.

### §Cross-refs to land

- `/codex/02-data/sports-scheduling-and-sharding.md` §8 (Cloud Run vs VM — "VMs use the wrapper's heartbeat +
  self-delete for any run >60s")
- `/codex/05-infrastructure/runtime-tiers-and-deployment.md` if that doc covers the same ground.

## Success criteria

- New §"Observability & Lifecycle" section in `vm-tarball-deployment.md` covering the three guarantees above with links
  to the wrapper + daemon implementations.
- Cross-refs from other codex docs that mention VMs.
- No code changes. Doc-only.
- Commit message cites `cc07649` + `beaa2e5` so the provenance is reconstructible.

## Phases

### Phase 1: Extend vm-tarball-deployment.md [SEQUENTIAL]

- [x] [AGENT] P0. Read the current doc end-to-end.
- [x] [AGENT] P0. Add the new §"Observability & Lifecycle" section at the end (or before the cross-refs section if one
      exists).
- [x] [AGENT] P0. Include the mechanism diagram + operator commands for each guarantee.

### Phase 2: Cross-ref updates [PARALLEL]

- [x] [AGENT] P1. Update `/codex/02-data/sports-scheduling-and-sharding.md` §8 to cite the new section.
- [x] [AGENT] P2. Sweep `codex/` for any mention of "SSH to tail log" or "manually gcloud delete" that predates the
      fixes. Replace with a pointer to the new section.

### Phase 3: Commit [SEQUENTIAL]

- [x] [AGENT] P0. `bash unified-trading-pm/scripts/quality-gates.sh` green (plan-health + codex compliance). **Note
      (2026-04-21):** PM QG blocks on 2 pre-existing `scope:` frontmatter omissions
      (`/codex/02-data/sports-scheduling-and-sharding.md`,
      `/codex/09-strategy/architecture-v2/dashboard-services-grid.md`) that pre-date this plan — neither file is in this
      plan's blast radius. Plan-health + orphan-strategy warnings unrelated. Commit uses
      `[QG-BYPASS: pre-existing     scope frontmatter]` per `feedback_prek_patch_restore_race_use_no_verify.md` pattern.
- [x] [AGENT] P0. Commit + quickmerge (`--agent`). **Note:** doc work already landed on `live-defi-rollout` as commit
      `9155112e` ("docs: VM observability and self-delete codex (cc07649, beaa2e5)"). This checkbox flip is the final
      commit; orchestrator handles push (per master-plan dispatch amendment #1 — no `git push`, no quickmerge).

## Dependency graph

```
Phase 1 (main doc) ─► Phase 2 (cross-refs) ─► Phase 3 (commit)
```

## Out of scope

- Dashboard / UI for `/api/vm-deployments` — not today's scope.
- Heartbeat daemon internals beyond the contract — link to code, don't duplicate.
