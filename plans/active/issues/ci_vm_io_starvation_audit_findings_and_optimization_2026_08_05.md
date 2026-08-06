---
doc_type: issue
title: >-
  CI VM I/O starvation — audit findings, root causes, and proposed solutions (shared repos + pre-built venvs +
  worktree-based QG execution)
summary: >-
  Interactive audit session 2026-08-05: verified all 25 self-hosted runner pools migrated to dedicated CI VM
  (i-042a6332509482556, ci-escalation-runner-vm-1). The migration is complete (zero runners on the old planning VM), but
  the new VM is under severe I/O starvation — 92.9% iowait, load 171-245 on 16 vCPUs, CI effectively stalled. Root
  causes: (1) volume provisioned at default 6,000 IOPS instead of needed 16,000, (2) shared-VM resource caps
  (CPUQuota=400%, MemoryMax=8G) never removed after migration to dedicated box, (3) no fleet-wide concurrency cap — 25
  repos' QG-v2 runs all fire simultaneously during promotion events, (4) each QG run does a fresh git clone + uv sync
  writing ~1.7 GB to disk. Proposed solutions: bump volume to 16,000 IOPS (done), remove shared-VM resource caps (done),
  add host-level concurrency cap, replace actions/checkout + uv sync with git worktrees from shared bare repos +
  pre-built shared venvs (external deps only — internal deps are already editable installs). Also documents remaining
  GitHub billing sources (PM's own workflow copies still on ubuntu-latest) and stale codex docs.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, i-o-starvation, capacity, performance, optimization, concurrency, git-worktree]
related:
  [
    /plans/active/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/active/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
    /codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md,
    /codex/07-security/self-hosted-runner-security-posture.md,
  ]
created: "2026-08-05"
author: ikennaigboaka [interactive session]
priority: P0
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
estimate_class: infra
depends_on: []
parent_epic: infrastructure_master
resolved_by:
source: ["interactive audit session 2026-08-05 — CI runner migration verification + I/O starvation diagnosis"]
locked_by:
locked_since:
context_scope:
  [
    /plans/active/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/active/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
    scripts/quality-gates-base/qg-host-governor.sh,
  ]
---

# CI VM I/O Starvation — Audit Findings, Root Causes, and Proposed Solutions

> **Session date:** 2026-08-05. Interactive audit of the dedicated CI VM after the runner-fleet migration. All findings
> are live-verified via SSM, CloudWatch, and GitHub API. No estimates.

---

## Part 1 — Migration Verification (PASS)

All 25 self-hosted runner pools are running exclusively on the dedicated CI VM. Zero runners remain on the old planning
VM.

| Check | Source | Result | | ------------------------------------ |

| ----------------------------------------------------------------------------- |
| ----------------------------------------------------------------------------- |
| ----------------------------------------                                      |                                              | GitHub API — runner registrations    |
| `gh api repos/IggyIkenna/<repo>/actions/runners` across all 25 repos          | All runners are `ip-172-31-3-59-*` (new VM). |
| **Zero** `ip-172-31-5-118-*` (old VM).                                        |                                              | Old VM — active runner service units |
| `systemctl list-units "github-glue-runner*@*.service" --state=active` via SSM | **0 units**                                  |                                      | Old VM — Runner.Listener     |
| processes                                                                     | `ps aux                                      | grep Runner.Listener` via            |
| SSM                                                                           | **0 processes**                              |                                      | Old VM — orchestrator health | `systemctl is-active orchestrator.service` via SSM | `active`, |
| 19 slot workers, load ~6.5                                                    |                                              | New VM — runner service units active |
| `systemctl list-units "github-glue-runner*@*.service" --state=active` via SSM | **34 active units** (all 25 pools)           |                                      |
| New VM — Runner.Listener processes                                            |
| `ps aux                                                                       | grep Runner.Listener` via SSM                | **34                                 |
| processes** (56 total runner procs)                                           |

---

## Part 2 — New VM Health (FAIL — I/O Starvation)

### Finding 1: Volume provisioned at default IOPS, not the needed spec

|                | New CI VM (actual)                  | Old VM (runners' prior home)        |
| -------------- | ----------------------------------- | ----------------------------------- |
| **Instance**   | `i-042a6332509482556`               | `i-0c9b283b31d6b5ca7`               |
| **Type**       | `c8i.4xlarge` (16 vCPU / 32 GB)     | `m8i.4xlarge` (16 vCPU / 64 GB)     |
| **Volume**     | `vol-03880fe9bf1ea805b`, 300 GB gp3 | `vol-0b4f0237fa0f5cd0f`, 700 GB gp3 |
| **IOPS**       | **6,000** (AWS 300GB default)       | **16,000** (bumped 2026-07-28)      |
| **Throughput** | **500 MB/s** (default)              | **1,000 MB/s** (bumped 2026-07-28)  |

The migration plan specified "300GB gp3" but never explicitly bumped IOPS/throughput. AWS gp3 defaults: 3,000 IOPS
base + free tier up to 6,000 for 300GB. The runners were migrated FROM a 16,000 IOPS volume TO a 6,000 IOPS volume.

### Finding 2: Current snapshot (11:00 UTC, live via SSM `top`/`iostat`)

| Metric              | Value                 | Healthy?                                       |
| ------------------- | --------------------- | ---------------------------------------------- |
| CPU iowait          | **92.9%**             | 🔴 Normal <10%                                 |
| CPU idle            | **0.0%**              | 🔴 Normal >30%                                 |
| CPU real (us+sy+ni) | ~7%                   | 🟢 Minimal compute                             |
| Load (1/5/15 min)   | **171 / 230 / 245**   | 🔴 10–15× vCPU count                           |
| Memory              | 19.6 / 31.5 GB (62%)  | 🟢                                             |
| Swap                | 0 MB                  | ⚠️ No safety valve                             |
| Disk avg queue      | 2.4 (hourly avg)      | 🟡 CloudWatch won't alarm but burst saturation |
| Disk util (nvme0n1) | 71.3% at 52 MB/s read | 🔴                                             |

### Finding 3: 24h EBS trend — sustained, not a spike

| Metric                 | 24h ago → Now           | Trend                              |
| ---------------------- | ----------------------- | ---------------------------------- |
| VolumeReadOps (avg/s)  | 67k → **156k**          | Climbing as pools migrated         |
| VolumeWriteOps (avg/s) | 47k → **1.5k**          | **99% collapse** — writers starved |
| VolumeReadBytes        | 2.6 GB/h → **8.9 GB/h** | 3.4× increase                      |

### Finding 4: Impact — CI is stalled

- **`ci-status-update`**: 5 consecutive runs queued, none picked up (all 3 PM writers offline)
- **PM `quality-gates-v2`**: 5 consecutive LDR→main promotion runs FAILED
- **`ldr-to-main-promote-fleet`**: 10 of last 20 runs CANCELLED (the promote workflow itself couldn't complete its 37s
  sweep on the I/O-starved VM)
- **9 of 25 repos**: Runners offline (can't maintain GitHub registration handshake)
- **`alerting-service`**: Only repo with 1 online runner

### Finding 5: Root cause #1 — shared-VM resource caps never removed

The `github-glue-runner.slice` on the new VM still had the resource limits designed for the OLD shared topology where
runners and AO shared a box:

| Limit      | Before (shared-VM design)   | After (dedicated VM fix) |
| ---------- | --------------------------- | ------------------------ |
| CPUQuota   | `400%` (4 of 16 vCPUs)      | `infinity`               |
| CPUWeight  | `50` (loses CPU contention) | `100` (default)          |
| MemoryHigh | `18 GB` (soft throttle)     | `infinity`               |
| MemoryMax  | `20 GB` (hard kill)         | `infinity`               |

The slice's own comment: _"Purpose: a CI burst must NEVER starve the agent-orchestrator sharing this VM."_ On the
dedicated CI VM, there is no orchestrator to protect. The fleet was running at 18 GB — right at the MemoryHigh soft cap.
And only 4 of 16 vCPUs were usable.

**Fixed 2026-08-05**: Caps removed live via `systemctl set-property` + persisted via drop-in at
`/etc/systemd/system/github-glue-runner.slice.d/override-dedicated-vm.conf`. CPU and memory are now wide open.

### Finding 6: Root cause #2 — no fleet-wide concurrency cap

The `ldr-to-main-promote-fleet` workflow fires on schedule `*/5 * * * *` (declared every 5 min for over-declaration
reasons — GitHub silently drops most ticks, delivering ~every 15 min effectively). Each successful run opens promotion
PRs across all repos with changes, triggering `quality-gates-v2` on all 25 repos simultaneously.

`quality-gates-v2.yml` concurrency:

```yaml
concurrency:
  group: quality-gates-v2-${{ github.ref }}
  cancel-in-progress: true
```

- **Same repo, same ref**: Cancels in-progress run → starts new one (correct, saves minutes)
- **Different repos**: **Runs concurrently** — no cross-repo queuing. `github.ref` is per-repo.
- **Result**: Fleet-wide promotion → 25 independent QG runs → 25 concurrent git clones + venv builds

There is no fleet-wide concurrency limit. The QG governor (`qg-host-governor.sh`) limits concurrent heavy phases within
a SINGLE QG run (K = `max(2, floor(16/4))` = 4), not across repos.

---

## Part 3 — Per-Run I/O Cost Analysis

### What one QG-v2 run actually writes to disk (MTDS example, live measurement)

| Step                                   | What happens                                           | Disk writes             | Cached?                                                    |
| -------------------------------------- | ------------------------------------------------------ | ----------------------- | ---------------------------------------------------------- |
| `actions/checkout@v4`                  | `git clone --depth=2` from GitHub                      | 200–500 MB              | **No** — fresh clone per run                               |
| Sibling repos clone                    | `git clone --depth=1` for UAC, UTL, etc.               | 50–200 MB each          | **No** — fresh clone per run                               |
| `uv sync --frozen` — **external deps** | Install numpy, pandas, fastapi… from `~/.cache/uv`     | **~1 GB** into `.venv/` | `~/.cache/uv` is persistent (43 GB), but `.venv/` is fresh |
| `uv sync --frozen` — **internal deps** | `editable = true`, `path = "../..."` → creates pointer | **Near-zero**           | Already just pointer updates                               |
| `pytest` + coverage                    | Test execution                                         | 10–50 MB                | No                                                         |
| **Total per run**                      |                                                        | **~1.7 GB**             |                                                            |
| **25 concurrent**                      |                                                        | **~42 GB**              |                                                            |

At 6,000 IOPS (~96 MB/s throughput): 42 GB ÷ 96 MB/s = **7+ minutes of pure write time, zero reads.** Reads (git clone
source, uv cache, source files) compete for the same disk. Hence 92.9% iowait.

### Key insight: internal deps are already efficient

Internal deps are declared as `editable = true` with `path = "../unified-trading-library"` in `pyproject.toml`:

```toml
[tool.uv.sources.unified-trading-library]
path = "../unified-trading-library"
editable = true
```

This means `uv sync` doesn't copy internal dep code into the venv — it just creates a pointer (`.pth` file). When
internal dep code changes (every commit), re-running `uv sync` just updates the pointer. **Near-zero I/O.**

External deps (numpy, pandas, fastapi, etc.) are the problem — they rarely change between runs (same lockfile), but
`uv sync` reinstalls them into a fresh `.venv/` every run (~1 GB written each time).

---

## Part 4 — Proposed Solution: Shared Repos + Pre-Built External Venvs + Worktrees

### Architecture

```
/opt/repos/                          ← bare repos, git fetch every 5 min (reuse existing slot-refresh timers)
  unified-trading-library.git/
  market-tick-data-service.git/
  ... (25 repos)

/opt/venvs/                          ← pre-built venvs, EXTERNAL DEPS ONLY
  market-tick-data-service/          ← rebuilt ONLY when uv.lock changes (rare)
  instruments-service/
  ...

/tmp/qg-<run-id>/                    ← per-run worktree, deleted after job
  market-tick-data-service/          ← git worktree add from bare repo
  unified-trading-library/           ← sibling: worktree from bare repo
  unified-api-contracts/             ← sibling: worktree from bare repo
  .venv/                             ← cp -al from shared venv
```

### Per QG run — 3 steps instead of clone + sync

```bash
# Step 1: Worktrees (instant — shared object DB, zero clone)
git -C /opt/repos/market-tick-data-service.git worktree add --detach \
  /tmp/qg-30893378880/market-tick-data-service <sha>
git -C /opt/repos/unified-trading-library.git worktree add --detach \
  /tmp/qg-30893378880/unified-trading-library <pinned-sha>

# Step 2: Shared venv (instant — hardlink copy, external deps only)
cp -al /opt/venvs/market-tick-data-service/.venv \
  /tmp/qg-30893378880/market-tick-data-service/.venv

# Step 3: Repoint internal deps (instant — editable is just pointer updates)
cd /tmp/qg-30893378880/market-tick-data-service
uv sync --frozen --no-install-project
# External deps: unchanged → skip. Internal deps: editable → update .pth pointer.
```

### I/O comparison

|                                | Current (clone fresh)         | Proposed (worktree + shared venv) |
| ------------------------------ | ----------------------------- | --------------------------------- |
| Git objects (main + siblings)  | Clone 100-400 MB from network | Already in bare repos — zero      |
| Working tree (main + siblings) | Write 250-700 MB              | Write 250-700 MB (unchanged)      |
| External deps (venv)           | **Write ~1 GB every run**     | **Hardlink copy — ~zero**         |
| Internal deps (editable)       | Near-zero (pointer)           | Near-zero (pointer — unchanged)   |
| **Total per run**              | **~1.7 GB**                   | **~250-700 MB**                   |
| **25 concurrent**              | **~42 GB**                    | **~6-18 GB**                      |
| **At 16,000 IOPS (256 MB/s)**  | ~2.7 min pure write           | ~23-70 sec pure write             |

### Isolation model

Each run gets its own worktree at `/tmp/qg-<run-id>/`. Bare repos are read-only during checkout. Git handles concurrent
`worktree add` safely. The shared venv is copied via hardlinks (`cp -al`), so each run's `.venv/` is a separate inode
tree — modifying it doesn't affect other runs or the shared source. Each run's working tree is its own filesystem tree.
Per-job cleanup: `git worktree remove` + `rm -rf`.

### Why `cp -al` works for the venv

Hardlinks share the same data blocks on disk. When a run modifies a file in its `.venv/`, the filesystem copies the
block (copy-on-write at the filesystem level). Since QG runs don't modify installed packages (they install and read
them), this effectively means zero additional block writes beyond the directory entries.

### When the shared venv rebuilds

Only when `uv.lock` changes. A lockfile change means external deps changed — the shared venv is rebuilt once, then all
subsequent runs get the updated venv via fresh hardlink copy. Lockfile changes are rare (dependency bumps, version
updates).

---

## Part 5 — Remaining GitHub Billing

All fleet repos have their CI workflows on `[self-hosted, glue]`. But several workflow copies in PM itself were never
flipped.

### PM workflows still on `ubuntu-latest` (billing GitHub minutes)

**Never flipped (candidates for migration to self-hosted):**

| Workflow                       | Aug 4 runs           | Why still hosted                                |
| ------------------------------ | -------------------- | ----------------------------------------------- |
| `semver-agent.yml`             | Not in PM Aug 4 runs | Never flipped — fleet repos already self-hosted |
| `publish-package.yml`          | Not in PM Aug 4 runs | Never flipped                                   |
| `major-bump-issue-handler.yml` | Not in PM Aug 4 runs | Never flipped                                   |
| `request-major-bump.yml`       | Not in PM Aug 4 runs | Never flipped                                   |
| `main-backmerge-to-ldr.yml`    | 1 run                | Never flipped                                   |
| `build-smoke-all-repos.yml`    | Not in Aug 4 runs    | Never flipped                                   |

**Deliberately hosted (failure independence — must work when self-hosted VM is down):**

| Workflow                          | Aug 4 runs |
| --------------------------------- | ---------- |
| `ci-health.yml`                   | 4 runs     |
| `cloud-build-failure-watcher.yml` | 1 run      |
| `ldr-ci-monitor.yml`              | 1 run      |
| `notify-slack.yml`                | As needed  |

### Other repos with GitHub-hosted workflows

| Repo                        | Workflow                     | Runs on                              |
| --------------------------- | ---------------------------- | ------------------------------------ |
| `deployment-ui`             | `ui-quality-gates-v2.yml`    | `ubuntu-latest` — full UI build/test |
| `unified-trading-system-ui` | `ui-quality-gates-v2.yml`    | `ubuntu-latest` — full UI build/test |
| `deployment-service`        | `sync-vm-scripts-to-gcs.yml` | `ubuntu-latest`                      |

---

## Part 6 — Stale Docs (not fixed — audit only)

| Doc                                                              | Issue                                                                                                                                                                             |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md` | Entire runbook describes reinstalling glue runners on the **planning VM**. Runners no longer live there — they're on `ci-escalation-runner-vm-1`. Needs full rewrite or archival. |
| `codex/07-security/self-hosted-runner-security-posture.md`       | Summary still says runner pools are "on the orchestrator VM." Body describes pre-migration state as current. Mitigation ladder step 3 ("dedicated VM") is now the actual state.   |
| `codex/05-infrastructure/agent-orchestrator-deploy.md`           | Already has the new "CI-runner fleet — split off to a dedicated VM" section ✅. But still says AO is at `m8i.4xlarge` (downsize pending per the migration plan).                  |

---

## Part 7 — Prioritized Action Items

- [x] ✅ [INFRA] P0. **Remove shared-VM resource caps from `github-glue-runner.slice` on the dedicated CI VM.** Done
      2026-08-05 via SSM: CPUQuota=infinity, CPUWeight=100, MemoryMax=infinity, MemoryHigh=infinity. Persisted via
      drop-in at `/etc/systemd/system/github-glue-runner.slice.d/override-dedicated-vm.conf`. Evidence: live
      `systemctl show` confirms all four properties at `infinity`/`100`.

- [x] ✅ [INFRA] P0. **Bump the CI VM volume to 16,000 IOPS / 1,000 MB/s.** Done 2026-08-05 via
      `aws ec2 modify-volume --volume-id vol-03880fe9bf1ea805b --iops 16000 --throughput 1000`. Live, non-disruptive
      operation — same procedure done safely on the old VM during the July 28 incident. Evidence:
      `aws ec2 describe-volumes` confirms the new IOPS/throughput values.

- [ ] [INFRA] P1. **Add host-level concurrency cap on the CI VM — Option B investigated 2026-08-06 with real
      measurements and REJECTED as unsafe; still open.** Full investigation + real `TasksCurrent` baseline (274-326
      idle, ~46 tasks/active run measured via a real dispatch) + why plain `TasksMax` risks hard fork failures inside
      legitimate concurrent jobs rather than graceful queuing, why IO-bandwidth throttling is the better fit but needs a
      `system.slice`-wide `io` controller delegation this session wasn't willing to make live, and the recommended safer
      mechanism (an `ACTIONS_RUNNER_HOOK_JOB_STARTED` wrapper around the already-proven `qg-host-governor.sh` token
      mode) — see `/plans/active/ci_vm_exposure_remediation_2026_08_06.md` todo 3 for full detail. Not duplicated here.

- [ ] [INFRA] P1. **Flip PM's remaining workflow copies to self-hosted.** `semver-agent.yml`, `publish-package.yml`,
      `major-bump-issue-handler.yml`, `request-major-bump.yml`, `main-backmerge-to-ldr.yml` in PM's `.github/workflows/`
      are still on `ubuntu-latest`. Every other repo's copies are already on `[self-hosted, glue]`. PM is the straggler.

- [ ] [INFRA] P1. **Implement shared bare repos + pre-built external venvs + worktree-based QG execution.** Replace
      `actions/checkout@v4` + `uv sync` in the self-hosted execution path with: (1) `git worktree add` from shared bare
      repos at `/opt/repos/`, (2) `cp -al` of shared pre-built venvs at `/opt/venvs/` (external deps only), (3)
      `uv sync --frozen --no-install-project` to repoint editable internal deps. Estimated I/O reduction: ~1 GB per run
      (eliminating the external-dep venv rebuild). See Part 4 for full design. The `content-gate` cache-hit fast-path
      (skip QG entirely when the same tree already passed) is preserved and unaffected.

- [ ] [INFRA] P2. **Migrate `ui-quality-gates-v2` for `deployment-ui` and `unified-trading-system-ui` to self-hosted.**
      These run full UI build/test suites on `ubuntu-latest` — billing GitHub for every PR/push.

- [x] ✅ [INFRA] P2. **Add swap to the CI VM — done 2026-08-06.** 16GB `/swapfile` (`fallocate`+`mkswap`+`swapon`,
      persisted via `/etc/fstab`), live-verified (`swapon --show` / `free -h`). Full detail + evidence:
      `/plans/active/ci_vm_exposure_remediation_2026_08_06.md` todo 1. Also shipped in the same session, not previously
      tracked as a todo here: durable resource-history-sampler + S3-mirrored backup parity with the AO box (same plan,
      todo 2) — a real latent bug (`PrivateTmp=yes` missing under `ProtectSystem=strict`) found and fixed in the
      checked-in `agent-orchestrator` SSOT along the way, not just live-patched.

- [ ] [DOC] P2. **Update stale codex docs.** `central-vm-relaunch-glue-runner-reinstall.md` needs full rewrite (runners
      no longer on planning VM). `self-hosted-runner-security-posture.md` needs summary/body updated (runners now on
      dedicated VM). `agent-orchestrator-deploy.md` needs the downsize reflected once todo 8 of the migration plan
      resolves.

- [ ] [INFRA] P3. **Complete AO box downsize.** `i-0c9b283b31d6b5ca7` is still at `m8i.4xlarge` — per the migration
      plan, downsize to `m8i.2xlarge` once operator confirms. Currently on hold.

---

## Progress Log

- **2026-08-06 (interactive session, human-driven)** — Closed the swap gap + shipped resource-history-sampler parity
  with the AO box (both live-verified, real bug found+fixed in the shared SSOT along the way). Investigated the
  concurrency-cap todo with real measurements (real `TasksCurrent` baseline + a live dispatch's measured task cost) and
  rejected plain `TasksMax` as unsafe once sized against those numbers — left open with a concrete safer next step
  identified rather than shipped half-verified. Full detail: `/plans/active/ci_vm_exposure_remediation_2026_08_06.md`.
- **2026-08-05 (interactive audit)** — Verified migration completion (25/25 pools on dedicated VM, zero on planning VM).
  Diagnosed I/O starvation: volume at default 6,000 IOPS, shared-VM resource caps still active, no concurrency cap.
  Removed resource caps live. Bumped volume to 16,000 IOPS. Documented proposed worktree + shared-venv architecture.
  Identified remaining GitHub billing sources. Flagged stale codex docs.
- **context-scout 2026-08-05**: populated context_scope (5 entries).
