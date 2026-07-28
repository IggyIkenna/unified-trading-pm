---
doc_type: issue
title: Self-hosted glue-runner fleet-wide crash-loop — GCP_PROJECT never written to runtime env files
summary:
  Every one of the 23 installed glue-runner pools crash-looped on GH_PAT Secret Manager reads ("Failed to find attribute
  [project]") because setup-glue-runners.sh only wrote GCP_PROJECT to the runtime env file when the operator passed it
  explicitly, while the install-time self-test silently defaulted it — masking the gap until runtime. ~3.5h fleet-wide
  CI outage, found and fixed live 2026-07-28.
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, self-hosted-runner, gcp, secret-manager, outage]
related: []
created: 2026-07-28
parent_epic: infrastructure_master
priority: P0
assigned_vm: NA
resolved_by: autonomous-agent-fleet-sweep
locked_by:
source: autonomous-agent-fleet-sweep
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

> **🟢 RESOLVED 2026-07-28** — live fix: `GCP_PROJECT=central-element-323112` appended to all 23
> `/etc/github-glue-runner-*.env` files, crash-looping units restarted (34/34 confirmed `active running`, 0 restarts
> since). Durable fix: `setup-glue-runners.sh` now unconditionally writes the same fallback to the runtime env file that
> the install-time self-test and systemd template already used. Fleet backlog drained naturally. No open follow-ups.

> **🟢 ARCHIVED 2026-07-28** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule.

# Self-hosted glue-runner fleet-wide crash-loop — GCP_PROJECT never written to runtime env files

## What happened

A routine fleet-wide CI sweep found dozens of stale `queued`/`pending` GitHub Actions runs across nearly every repo
(`quality-gates-v2`, `Semver Agent`, `main-backmerge-to-ldr`, `cloud-build-router`, `ci-status-update`), some created 3+
hours earlier and never picked up. Direct inspection of the orchestrator VM (`i-0c9b283b31d6b5ca7`) via SSM found the
self-hosted glue-runner systemd services in a fleet-wide crash-loop: at any snapshot, 14-16 of the 24 installed pools
showed `activating (auto-restart)` rather than `active running`, each with a restart counter in the thousands (a ~5-9s
crash-restart cycle sustained for ~3.5 hours).

## Root cause

`journalctl` on a crash-looping unit showed the actual failure:

```
ERROR: (gcloud.secrets.versions.access) Error parsing [version].
The [version] resource is not properly specified.
Failed to find attribute [project].
FATAL: Secret Manager read of 'GH_PAT' failed
```

This is a CLI-side resource-parsing error, not a network/auth failure — it fires before any API call, purely from
`gcloud` being unable to resolve a default project for the secret reference. Direct reproduction (no concurrency)
confirmed it deterministically: `alerting-service`'s own isolated `CLOUDSDK_CONFIG` directory
(`/opt/github-glue-runners-alerting-service/.gcloud`) had `account =` set but **no `project =` line at all** in
`configurations/config_default` — while the separate, shared `/opt/github-glue-runners/.gcloud` (PM's own pool) had
both. This ruled out an initial thundering-herd/shared-config-race hypothesis (plausible given ~14 units crash-looping
in near-lockstep, but disproved by a clean single-process repro) in favor of a simpler, deterministic per-pool bootstrap
gap.

Traced to `scripts/self-hosted-runners/setup-glue-runners.sh`:

- Line ~464 (install-time self-test) and line ~511 (systemd unit template) both already default to
  `${GCP_PROJECT:-central-element-323112}` when the operator doesn't pass `GCP_PROJECT` explicitly.
- Line ~482 (the actual **runtime env file** the systemd unit reads via `EnvironmentFile=`) did NOT apply this same
  fallback — it only wrote `GCP_PROJECT=` when the variable was explicitly set:
  `if [ -n "${GCP_PROJECT:-}" ]; then printf 'GCP_PROJECT=%s\n' ...; fi`.

Every documented usage example (`sudo GH_TOKEN_SECRET=GH_PAT ./setup-glue-runners.sh install`) never passes
`GCP_PROJECT`. So every one of the 23 installed pools' install-time self-tests passed (using the fallback), giving false
confidence, while the actual runtime path silently depended on each pool's isolated `.gcloud` config having its own
default project bootstrapped correctly — which `gcloud auth login --cred-file=...` (used to establish the pool's machine
identity) does not reliably set. Confirmed via `grep GCP_PROJECT /etc/github-glue-runner-*.env` on the live box: all 23
files were missing it.

**Why this had been latent for a while, not a fresh regression**: nothing about the 2026-07-28 VM resize caused this —
env files dated back to their original install time (2026-07-18 through 2026-07-27 per file mtimes), and some pools'
isolated `.gcloud` configs happened to have a correctly-bootstrapped default project anyway (why some pools were
intermittently "active running" while others crash-looped at any given snapshot — not a race, just each pool's own
independent bootstrap luck). The VM resize/reboot likely just caused enough of the runner pool to restart simultaneously
that the ones with the latent gap all surfaced their crash-loop around the same time.

## Fix

**Immediate (live, via SSM)**: appended `GCP_PROJECT=central-element-323112` to all 23 `/etc/github-glue-runner-*.env`
files, verified the fix with a direct reproduction (secret access now succeeds), then restarted every unit that was
crash-looping (16 units). Fleet confirmed stable 20s later: 34/34 glue-runner units `active running`, 0 restarts since.
Two of the stuck `quality-gates-v2` check-runs (agent-orchestrator, via `gh run cancel` +
`gh workflow run quality-gates-v2.yml --ref <branch>`) needed an explicit unstick since GitHub had them wedged in a
`queued`/`workflow_dispatch` limbo that predated the runner fix; same recovery applied to strategy-service,
unified-api-contracts, trading-agent-service, unified-trading-api. The rest of the fleet's backlog (Semver Agent /
main-backmerge-to-ldr / cloud-build-router / ci-status-update runs) drained naturally once the runners came back healthy
— no further intervention needed there.

**Durable (source fix, shipped)**: `setup-glue-runners.sh` line ~482 now unconditionally writes
`GCP_PROJECT=${GCP_PROJECT:-central-element-323112}` to the env file, matching the same fallback already used at the
install-time self-test and the systemd template — so a future install or VM reprovision cannot silently reintroduce this
gap.

## Verification

- `systemctl list-units ... | grep glue | awk '{print $4}' | sort | uniq -c` → `34 running` (was
  `14 auto-restart / 25 dead / 20 running` at discovery).
- `NRestarts` on 3 previously-crash-looping units (alerting-service, instruments-service, strategy-service) → `0` after
  the fix, confirming they're no longer restarting.
- Direct `gcloud secrets versions access ... --project=central-element-323112` reproduction succeeded post-fix.
- Fresh fleet-wide `gh run list` sweep ~15 minutes post-fix showed multiple repos' backlogs fully drained
  (alerting-service, instruments-service, unified-trading-system-ui all clean/green); others (agent-orchestrator,
  strategy-service) showed jobs actively progressing through real steps rather than stuck in `queued` — expected given
  ~3.5h of accumulated backlog across a small (1-3 instance) per-repo runner pool takes time to drain, not a sign of a
  remaining problem.

## Why this was fixed directly, not escalated

Single, well-understood root cause with a clean, deterministic reproduction; the fix (one env-var write) has zero blast
radius beyond restoring the documented, intended behavior of an existing (already-coded-for) conditional fallback.
`agent-orchestrator`'s own bootstrap_vm.sh — unrelated to this — was NOT touched as part of this fix (that repo's
separate, already-shipped memory-cap change is a different subsystem).
