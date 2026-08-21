---
doc_type: issue
title: >-
  CI VM cost + I/O audit — verified findings, corrected root cause, and the path to downsizing the dedicated CI VM
summary: >-
  Interactive audit 2026-08-05, independently re-verified and CORRECTED 2026-08-06 (3 confirmed, 5 corrected, 6
  falsified — see Part 0). The runner migration to the dedicated CI VM (i-042a6332509482556) is complete. The I/O
  incident was real but MIS-DIAGNOSED: the binding constraint was gp3 THROUGHPUT pinned at 124.x MB/s against a 125 MB/s
  ceiling for 9 straight hours, not IOPS; the claimed 16,000 IOPS bump NEVER HAPPENED (live: 6,000/500). The proposed
  shared-venv optimisation rests on a false premise — `uv` already hardlinks 86.5% of every venv — and its `cp -al`
  "copy-on-write" isolation argument is invalid on ext4. Reframed for the REAL goal (shrink the VM from 16 vCPU/32 GB):
  CPU fits 8 vCPU, but RAM must NOT be halved — observed slice peak 29.7 GB with 6 OOM kills, against admission
  baselines 3-7 weeks stale and wrong by 3.6-5.5x. Raises a NEW P0 security exposure — unified-trading-pm is now a
  PUBLIC repo with 8 self-hosted runners — which inverts two existing "flip to self-hosted" todos.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, i-o-starvation, capacity, performance, optimization, concurrency, cost, security]
related:
  [
    /plans/active/ci_vm_exposure_remediation_2026_08_06.md,
    /plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/archive/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md,
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
parent_epic: ci_master
resolved_by:
source:
  [
    "interactive audit session 2026-08-05 — CI runner migration verification + I/O starvation diagnosis",
    "independent verification + cost/downsizing re-frame 2026-08-06 (AWS API, CloudWatch, SSM, cgroup v2, GitHub API)",
  ]
locked_by:
locked_since:
context_scope:
  [
    /plans/active/ci_vm_exposure_remediation_2026_08_06.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /codex/07-security/self-hosted-runner-security-posture.md,
    scripts/quality-gates-base/qg-host-governor.sh,
    scripts/dev/qg_resource_baseline.json,
    unified-trading-ci/.github/workflows/python-quality-gates-v2.yml,
  ]
---

# CI VM Cost + I/O Audit — Verified Findings and the Path to Downsizing

> **2026-08-05** interactive audit (original). **2026-08-06** independent re-verification against live AWS API,
> CloudWatch, SSM, cgroup v2, and the GitHub API. Sections are marked **✅ CONFIRMED**, **⚠️ CORRECTED**, or **❌
> FALSIFIED**. The 08-05 conclusions are preserved where they held and rewritten where they did not.
>
> **Sibling plan:** `/plans/active/ci_vm_exposure_remediation_2026_08_06.md` (slot-4, same day) shipped swap +
> resource-history parity and investigated the concurrency cap. Its findings are referenced, not duplicated.

> **The real objective (operator, 2026-08-06):** GitHub-hosted CI was ~$1,200/mo (peaks ~$80/day). Runners moved to
> self-hosted → planning VM → dedicated VM. The dedicated VM now costs as much as the GitHub bill it replaced. **The
> goal is to shrink it — target ~8 vCPU and materially less RAM.** Every item below is prioritised against that goal,
> not against wall-clock latency.

---

## Part 0 — Verification verdict at a glance

| 08-05 claim                                   | Verdict       | Reality (measured 2026-08-06)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| --------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Migration complete, 25 pools on dedicated VM  | ✅ CONFIRMED  | 25 pool templates; 17 live runners                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Shared-VM resource caps removed               | ✅ CONFIRMED  | `CPUQuota/MemoryHigh/MemoryMax=infinity`, `CPUWeight=100`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Volume was at "6,000 IOPS / 500 MB/s default" | ❌ FALSIFIED  | Pre-fix was **3,000 / 125** (the real gp3 default)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Volume bumped to 16,000 IOPS / 1,000 MB/s     | ❌ FALSIFIED  | **Never happened.** Live: 6,000 / 500                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Root cause = IOPS starvation                  | ⚠️ CORRECTED  | **Throughput** pinned at 124.x MB/s vs 125 ceiling, 9 h                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| "VolumeReadOps 67k → 156k avg/s"              | ❌ FALSIFIED  | Units error — these are per-60s samples (÷60)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `uv sync` writes ~1 GB per run                | ❌ FALSIFIED  | 86.5% of venv files are hardlinks; near-zero data written                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `cp -al` is safe via "copy-on-write"          | ❌ FALSIFIED  | Root fs is **ext4** — no COW; writes go through shared inodes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| "No fleet-wide concurrency limit exists"      | ⚠️ CORRECTED  | Reservation-mode governor IS a live cross-repo admission gate                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Token governor `K = floor(16/4) = 4`          | ⚠️ SUPERSEDED | Was believed physical-core-based (`floor(8/4)=2`); **corrected again 2026-08-10**: code actually counts LOGICAL cpus (`lscpu -p=core` emits one row per hyperthread sibling, no dedup) — empirically reconfirmed on this exact host (`lscpu -p=core \| grep -vc '^#'` = 16, unique core ids = 8), so live `K` is **4**, not 2. See `/plans/active/qg_host_adaptive_resource_governor_2026_07_14.md` open todo (NEW FINDING 2026-08-09) for the tracked code fix (`_qg_physical_cores()` already exists and dedups correctly; the governor's inline `lscpu` call should use it instead). |
| "0 MB swap — no safety valve"                 | ✅ CLOSED     | True on 08-05; 16 GB `/swapfile` shipped 08-06 by slot-4                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| QG-v2 failures caused by I/O                  | ❌ FALSIFIED  | Content failures — 6 plan-hygiene ratchets, run takes 2m44s                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| "9 of 25 repos runners offline"               | ⚠️ CORRECTED  | Explained by the 08-05 public-repo migration, not I/O                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |

---

## Part 1 — Migration verification (✅ CONFIRMED, table repaired)

The original Part 1 table was structurally broken markdown (cells spilled across ~12 lines) — replaced by this summary.
Verified via GitHub API + SSM: every registration is `ip-172-31-3-59-*` with **zero** `ip-172-31-5-118-*`; the old VM
has 0 runner units and 0 `Runner.Listener` processes, with `orchestrator.service` still `active` (19 slot workers); the
new VM carries 25 pool templates and **17 live runners** (was 34 on 08-05).

**Live runner distribution (2026-08-06):** `unified-trading-pm` 8 · `agent-orchestrator` 3 · `e2e-testing`,
`execution-service`, `features-service`, `market-tick-data-service`, `ml-service`, `strategy-service` 1 each = **17**.
The 8 `dead` systemd units are `github-glue-token-refresh-*` helpers — **disabled by design, not a fault**.

---

## Part 2 — Root cause (⚠️ CORRECTED: throughput, not IOPS)

### Finding 1 (CORRECTED) — the pre-fix volume spec was 3,000 IOPS / 125 MB/s

`aws ec2 describe-volumes-modifications --volume-ids vol-03880fe9bf1ea805b` returns exactly **one** modification in the
volume's entire history:

```
OriginalIops: 3000,  OriginalThroughput: 125   →   TargetIops: 6000,  TargetThroughput: 500
StartTime 2026-08-05T10:59:26Z   EndTime 2026-08-05T11:29:48Z   ModificationState: completed
```

gp3 defaults are 3,000 IOPS / 125 MB/s at **any** volume size (gp2 scales with size; gp3 does not). The 08-05 doc
recorded 6,000/500 as the "actual/default" pre-fix state — that was the value it had just set, read back mid-modify.
**The true pre-incident throughput was 4x worse than documented**, which is why the correct root cause was missed.

### Finding 2 (CORRECTED) — the volume was THROUGHPUT-saturated, not IOPS-saturated

CloudWatch, 2026-08-05, hourly, `vol-03880fe9bf1ea805b`:

| Hour (UTC) | read MB/s | write MB/s | **total MB/s** | total IOPS | ceiling          |
| ---------- | --------- | ---------- | -------------- | ---------- | ---------------- |
| 02:00      | 55.6      | 69.1       | **124.7**      | 2,163      | 125 MB/s         |
| 04:00      | 76.4      | 44.3       | **120.7**      | 2,901      | 125 MB/s         |
| 06:00      | 84.2      | 39.7       | **123.9**      | 2,754      | 125 MB/s         |
| 08:00      | 52.1      | 72.8       | **124.9**      | 2,204      | 125 MB/s         |
| 10:00      | 123.4     | 0.9        | **124.4**      | 2,260      | 125 MB/s         |
| **11:00**  | 273.8     | 104.0      | **377.9**      | **6,719**  | 500 (bump lands) |
| 12:00      | 121.0     | 247.4      | **368.4**      | 5,814      | 500 MB/s         |

**Nine consecutive hours pinned at 124.x MB/s against a 125 MB/s ceiling** — textbook throughput saturation. IOPS in
those hours ran 2,163–2,901 of 3,000: close, but the hard pin was bandwidth. Demand tripled the instant the ceiling
lifted, proving suppressed demand.

**The 6,000/500 bump was the correct and effective fix.** Post-bump the binding constraint moved to IOPS (6,719
measured > 6,000 provisioned).

### Finding 3 (❌ FALSIFIED) — the 24h EBS trend table is a units error

CloudWatch `Volume*Ops` are **Counts per 60-second sample**, not per second. "67k → 156k avg/s" is ~1,100 → ~2,600 IOPS.
Likewise "VolumeWriteOps 47k → 1.5k = 99% collapse — writers starved" is over-read: write ops oscillate 6.6k–71k per
sample across the day with no monotonic collapse. Separately, `%util` (71.3%) is not a saturation signal on NVMe/EBS —
the meaningful figure is `r_await`, currently **0.91 ms** at 154 MB/s.

### Finding 4 (❌ FALSIFIED) — CI failures were not caused by I/O

Two of three symptoms self-recovered: `ldr-to-main-promote-fleet` last 10 runs all **success**; `ci-status-update` last
6 all **success**. But **PM `quality-gates-v2` is red on all of the last 10 runs and it is not I/O** — the `checks`
slice fails in **2m44s** (tests passes in 1m44s) on six plan-hygiene ratchets:

```
❌ FAIL [hard] Reference path convention (/plans, /codex — ratchet)
❌ FAIL [hard] AG-closeout linkage (ratchet)
❌ FAIL [hard] Terminal-status-archived (ratchet)
❌ FAIL [hard] assigned_vm:NA corpus size (ratchet)
❌ FAIL [hard] Silent-default-effort plans (ratchet)
❌ FAIL [hard] Archive candidates (ratchet)
```

**PM's LDR→main promotion is blocked**, re-firing and failing every ~15 min.

### Finding 5 (✅ CONFIRMED) — shared-VM caps removed and persisted

`systemctl show github-glue-runner.slice`: `CPUQuotaPerSecUSec=infinity`, `CPUWeight=100`, `MemoryHigh=infinity`,
`MemoryMax=infinity`, via `/etc/systemd/system/github-glue-runner.slice.d/override-dedicated-vm.conf`. Correct fix.

### Finding 6 (⚠️ CORRECTED) — a cross-repo admission gate already exists

The 08-05 claim "there is no fleet-wide concurrency limit … the governor limits within a SINGLE QG run" describes the
legacy **token** mode. Self-hosted runs use **reservation** mode —
`QG_GOVERNOR_MODE: ${{ inputs.self_hosted_runner_labels != '' && 'reservation' || 'token' }}` in
`.github/workflows/quality-gates-v2.yml`.

Reservation mode **is** a host-wide, cross-repo RAM+CPU admission gate with a flock-protected ledger deliberately
collapsed to one shared dir `/opt/.qg-governor-glue-shared` so every repo's pool coordinates
(`scripts/quality-gates-base/qg-host-governor.sh`). Verified live — the ledger holds real reservation rows.

**The actual gap is sharper and still valid:** `qg_governor_acquire` fires at the start of the **heavy phase**
(`base-service.sh:798`). The setup phase — checkout + N sibling `git clone`s + `uv venv` + `uv sync` — runs **before
admission, unthrottled, on every job simultaneously**. That is the burst.

This is exactly why slot-4's recommended `ACTIONS_RUNNER_HOOK_JOB_STARTED` wrapper
(`/plans/active/ci_vm_exposure_remediation_2026_08_06.md` todo 3) is the right mechanism: a job-started hook gates
**before setup**, which in-gate `qg_governor_acquire` structurally cannot. One amendment to that plan: wrap
**reservation** mode, not token mode — reservation carries the per-repo RAM baselines, which is what the OOM evidence in
Part 5 says actually binds.

Two supporting corrections: `K = max(2, floor(cores/4))` was believed to use **physical** cores (`lscpu` reports 16 CPUs
/ 2 threads-per-core / 8 cores, so `K = 2`) — **corrected again 2026-08-10**: the code's `lscpu -p=core | grep -vc '^#'`
actually counts logical CPUs (no HT dedup), so live `K = 4`; see the Part 0 table above for the full citation. And
**`TasksMax` (option B) is the wrong tool** — independently confirmed by slot-4 with measured numbers (`TasksCurrent`
274–326 idle, ~46 tasks per active run) and rejected. It counts every task/thread in the cgroup (currently 8192), so
hitting it makes `fork()` fail mid-job rather than queueing.

---

## Part 3 — Per-run I/O cost (❌ FALSIFIED: `uv` already hardlinks)

Measured on the live CI VM against `strategy-service`'s venv:

```
total_files=41046    hardlinked_files=35503        →  86.5% of the venv is hardlinks
nlink distribution:  9351 files @2,  7036 @3,  3 @1
every sampled pyarrow/*.so: nlink=3
```

`uv` 0.12.1 defaults to `link-mode=hardlink` when cache and target share a filesystem. Everything here is one ext4
`/dev/nvme0n1p1` (`/tmp` is **not** a separate mount), so hardlinking always applies. The venv shares inodes with the 43
GB `~/.cache/uv`.

Corroborated by this repo's own measurement, quoted in `python-quality-gates-v2.yml`: cold cache **2m07s**, warm cache
**9s**. 1 GB cannot be written in 9 seconds on this volume.

**Consequence:** the "~1 GB into `.venv/` per run" line is wrong, and every figure derived from it (1.7 GB/run, 42 GB at
25 concurrent) is void. Real per-run writes are the **working trees** (~250–700 MB) — which the 08-05 I/O comparison
table itself lists as _unchanged_ under the proposal.

The venv cost that IS real is **metadata**: ~35,500 inode/dentry creations per venv is small random journal I/O.
`cp -al` creates exactly the same number of links, so it does not reduce this either.

---

## Part 3a — The actual dominant cost: `actions/cache` on `~/.cache/uv` (FIXED 2026-08-06)

The clone/checkout is **not** the expensive step — a suspicion worth killing early. Real step timings, self-hosted:

| Step                              | features-service | execution-service | MTDS     | unified-trading-pm |
| --------------------------------- | ---------------- | ----------------- | -------- | ------------------ |
| `Checkout`                        | 1s               | 1s                | 2s       | 6–9s               |
| **`Cache uv package cache`**      | **450s**         | 22s               | **335s** | 13–22s             |
| `Clone …pm and dependencies`      | 11s              | 8s                | 10s      | 2–3s               |
| `Install dependencies` (uv sync)  | 5s               | 2s                | 2s       | 3–5s               |
| `Run quality gates`               | 271s             | 107s              | 167s     | 48–69s             |
| **`Post Cache uv package cache`** | 0s               | **894s**          | 0s       | 0s                 |

`Checkout` is 1–2s because `_work` persists and `.git` survives between jobs (`features-service/.git` = 3.7 MB under
`fetch-depth: 2`) — `actions/checkout` does an incremental fetch, not a clone.

**Why the cache step was so expensive.** `actions/cache` never checks whether files are already on disk. On every run it
downloads the archive and extracts it over `~/.cache/uv` regardless — features-service logged `Cache hit` 0.6s in, then
spent 450s transferring and extracting. **The save cannot succeed by construction**: `~/.cache/uv` is ONE shared 43 GB
directory used by every repo concurrently, while `actions/cache` treats it as private. execution-service's teardown:

```
23:32:42  /usr/bin/tar --posix -cf cache.tzst … --use-compress-program zstdmt
23:47:22  tar: …/home/ubuntu/.cache/uv/archive-v0: file changed as we read it
23:47:36  ##[warning]Failed to save: "/usr/bin/tar" failed with exit code 1
```

894 s tarring 43 GB, then failing and saving nothing — the same shared-cache race the `uv sync` retry loop documents. A
failed save means the next run misses and re-tars forever. execution-service cache usage had reached **8.5 of GitHub's
10 GB cap** (one 5.6 GB entry), so evictions were compounding it.

**Why it existed:** the step was deliberately left unconditional on the stated assumption that "GH-side cache
restore/save costs only a few seconds". That was true on `ubuntu-latest` with a small cache; it was never re-measured
after the self-hosted migration.

**Likely the original incident.** Tarring 43 GB sustains ~50 MB/s read per job; two or three concurrently is 100–150
MB/s — matching the 124.x MB/s pin that held for 9 h against the old 125 MB/s ceiling (Finding 2). Strong inference, not
proof.

**FIXED** — `unified-trading-pm@9b39f6a05`: the step is now gated on `inputs.self_hosted_runner_labels == ''`, so it
runs only for GitHub-hosted repos where it genuinely pays (2m07s cold vs 9s warm). **Verified live**, PM run
`31081212407` (post-push), both slices:

```
skipped   Cache uv package cache          ← was 13–22s on PM
success   Install dependencies      3-4s  ← uv sync still fast = local cache intact
(Post Cache uv package cache — absent: no main step ⇒ no injected post phase)
```

The `Install dependencies` line is the safety proof: `uv` resolved everything from the local cache with no GitHub
restore. The tools cache is **deliberately untouched** — its four install steps are gated on
`steps.tools-cache.outputs.cache-hit`, so gating it would make them all run every time.

---

## Part 4 — Shared repos + pre-built venvs + worktrees (⚠️ RESCOPED)

### What was wrong

1. **The I/O saving is ~zero** (Part 3). `cp -al` from `/opt/venvs/` creates the same ~35,500 hardlinks as `uv` does
   from `~/.cache/uv`, just from a different source.
2. **"Copy-on-write at the filesystem level" is false on ext4.** ext4 has no COW. A write to a hardlinked file writes
   **through the shared inode** — silently corrupting the `/opt/venvs/` master, **the 43 GB uv cache** (uv already
   hardlinked those same inodes), and every concurrent run. Real COW needs `cp --reflink` on XFS/Btrfs.
3. **This failure class has already fired in production.** `python-quality-gates-v2.yml`'s `uv sync` retry loop
   documents it: _"A concurrent uv write/GC in ANOTHER job can evict/rewrite a `cache/archive-v0` entry between this
   job's cache-index read and its extraction"_ — root-caused 2026-08-03, agent-orchestrator PR#766, escalation
   agt-5467b9. Adding `/opt/venvs/` as a **second** shared hardlink source with no GC/refcount discipline reproduces it
   on a surface with no retry wrapper.
4. **No bare-repo GC contract.** With a 5-min fetch loop into `/opt/repos/`, a crashed job leaves a stale worktree
   registration pinning objects forever. Needs `git worktree prune` on a timer plus `gc.auto=0`.
5. **`/tmp/qg-<run-id>` buys nothing** — `/tmp` is on the same ext4 root volume, not tmpfs. Same journal, same
   contention. The workflow already documents that glue runners _persist_ `/tmp` across jobs.

### What survives, and why it now matters more

The **clone** half of the design is right, and the operator independently identified it. The 08-05 doc targets the venv
(already free) and explicitly leaves the working tree (the actual cost) unchanged. Invert that emphasis:

- `Checkout` is **already incremental** (7s; `actions/checkout` reuses the persistent `_work` — hence
  `strategy-service/_work` at 11 GB).
- The **sibling-dep clones are not**: a fresh `git clone --depth=1` of every dep, every run, never cached. That is the
  concrete target — shared bare repos + `git worktree` + `--filter=blob:none`.

Credit it with eliminating **object transfer and pack writes**, not 1 GB of venv. The real reason it matters: **EBS
baseline scales with instance size** (Part 5) — cutting I/O is what makes a smaller instance viable.

---

## Part 5 — Downsizing analysis (NEW — the actual objective)

### EBS ceilings by candidate instance

| Type          | baseline IOPS | baseline MB/s | vCPU | RAM   |
| ------------- | ------------- | ------------- | ---- | ----- |
| `c8i.4xlarge` | 20,000        | **625**       | 16   | 32 GB |
| `c8i.2xlarge` | 12,000        | **312.5**     | 8    | 16 GB |
| `c8i.xlarge`  | 6,000         | **156.25**    | 4    | 8 GB  |
| `m8i.2xlarge` | 12,000        | **312.5**     | 8    | 32 GB |

Measured post-bump peak demand was **378 MB/s**. **A 2xlarge's 312.5 MB/s baseline is below current demand** —
downsizing without first cutting I/O reproduces the starvation incident at 312 MB/s instead of 125.

**This reverses the 16,000 IOPS action item**: on a 2xlarge, sustained is capped at 12,000 IOPS / 312 MB/s, so
provisioning 16,000 buys headroom the target instance cannot use.

### CPU — 8 vCPU fits

One full-fleet wave = **3,809 cpu-seconds** (sum of per-repo `cpu_s`, measured single-core-pinned, so this is the
serial-work metric). On 8 vCPU that is ~476 s ≈ **8 min** against a ~15 min effective wave interval. It fits.

### RAM — do NOT halve it (this is the blocking finding)

Live cgroup v2 `memory.peak` under `/sys/fs/cgroup/github.slice/github-glue.slice/github-glue-runner.slice`, covering
uptime since 2026-08-03 15:50:

```
slice total memory.peak = 31,842,299,904 B = 29.7 GB      (on a 32 GB box)
```

Per-pool observed peaks vs the baseline the admission governor actually reads:

| Repo                       | `qg_resource_baseline.json` | **observed `memory.peak`** | ratio    |
| -------------------------- | --------------------------- | -------------------------- | -------- |
| `agent-orchestrator`       | **absent from the file**    | **18,433 MB**              | n/a      |
| `market-tick-data-service` | 1,271 MB                    | **6,678 MB**               | **5.3x** |
| `unified-api-contracts`    | 1,117 MB                    | **6,146 MB**               | **5.5x** |
| `ml-service`               | 1,345 MB                    | **6,146 MB**               | **4.6x** |
| `features-service`         | 1,727 MB                    | **6,146 MB**               | **3.6x** |
| `instruments-service`      | 3,657 MB                    | **6,146 MB**               | 1.7x     |

And the box **has been OOM-killing** — 6 events since boot, e.g.

```
Aug 04 09:33:34 oom-kill: oom_memcg=/github.slice/github-glue.slice/github-glue-runner.slice
  task_memcg=.../github-glue-runner-market-tick-data-service@glue-1.service
  Killed process 790850 (python) anon-rss:6029360kB      ← 5.75 GB, vs a 1,271 MB baseline
```

**Conclusions:**

1. **The governor is admitting on numbers 3.6–5.5x too low** — a direct cause of the OOM kills: it over-admits because
   it believes repos are far smaller than they are.
2. **`agent-orchestrator` is not in the baseline file at all**, yet peaked at 18 GB.
3. **Cutting RAM to 16 GB would be actively dangerous** — the slice already peaks at 29.7 GB on a 32 GB box.
4. Several repos sit at exactly 6,146 MB, which looks like a per-pool sub-slice cap rather than a natural peak — true
   demand for those may be higher still.

**Target `m8i.2xlarge` (8 vCPU / 32 GB), not `c8i.2xlarge`** — take the CPU halving (the dominant cost line), keep the
RAM. Re-baselining may later justify going lower; today's data does not.

### Baseline staleness (why the cgroup numbers are the trustworthy ones)

| Source        | Date           | Age     | Coverage            |
| ------------- | -------------- | ------- | ------------------- |
| `local` peaks | **2026-06-17** | 7 weeks | 22 of 24 repos      |
| `vm` peaks    | **2026-07-14** | 3 weeks | 21 of 24 (2 absent) |
| recalibrated  | 2026-08-05     | 1 day   | 1 repo              |

45 of 48 rows were measured at `measured_concurrency: 1`, single-core pinned. Two rows are implausible on their face:
`unified-trading-system-ui` at **22 MB** peak RSS (413 cpu_s) and `deployment-ui` at 541 MB / 10 cpu_s — both are
vite/tsc/vitest builds that realistically use GBs. Those are exactly the two repos the 08-05 doc proposed migrating to
self-hosted.

### The largest cost lever: the box is idle between bursts

Current load is 3.23 / 3.13 / 3.28 on 16 vCPU with iowait 5.28% — roughly 20% utilisation. The promote fleet fires a
synchronised burst every ~15 min, then idles. 3,809 cpu-s spread evenly over 15 min needs **4.2 cores**; fired as one
burst it needs 16. **Staggering the fan-out is a pure-software change with zero capacity cost and is the single biggest
downsizing enabler.**

---

## Part 6 — Public-repo migration (NEW, 2026-08-05/06) — cost win and a P0 security exposure

18 of 25 repos are now **public**; 7 remain private. Public repos get unlimited free GitHub-hosted Actions minutes on
standard runners, so their CI need not touch the VM at all. This **explains the "9 of 25 runners offline" finding** —
those pools are public repos, not I/O casualties.

### 🔴 P0 SECURITY — `unified-trading-pm` is PUBLIC with 8 self-hosted runners attached

| Repo                 | Visibility | Registered runners             |
| -------------------- | ---------- | ------------------------------ |
| `unified-trading-pm` | **public** | **8** (5 glue + 3 glue-writer) |
| `deployment-api`     | **public** | API errored — recheck          |

GitHub's explicit guidance is **not** to use self-hosted runners with public repositories: a fork pull request can
execute arbitrary code on the runner. This host carries the 43 GB `~/.cache/uv`, `/opt/.qg-governor-glue-shared`,
persistent `/tmp` across jobs, and an instance IAM role reachable via IMDS. Current posture is permissive — org actions
policy is `allowed_actions: all`, `sha_pinning_required: false` (`default_workflow_permissions: read` is the one
mitigating setting). The fork-PR approval requirement must be verified and hardened, or PM's CI moved off self-hosted.

`/codex/07-security/self-hosted-runner-security-posture.md` is not merely stale — it documents a different threat model
than the one now in force.

### ⚠️ This inverts two existing todos

`unified-trading-pm`, `deployment-ui` and `unified-trading-system-ui` are all **public**. The 08-05 todos "flip PM's
remaining workflow copies to self-hosted" and "migrate `ui-quality-gates-v2` to self-hosted" would therefore **forgo
free minutes AND widen the security exposure**. Both are re-pointed in Part 8.

### The migration is half-done and inconsistent

| Repo                             | Visibility | `self_hosted_runner_labels`   | Runners | Recent runs    |
| -------------------------------- | ---------- | ----------------------------- | ------- | -------------- |
| `unified-api-contracts`          | public     | `""` → ubuntu-latest          | 0       | success ✅     |
| `unified-trading-library`        | public     | `""` (other jobs self-hosted) | 0       | success        |
| `instruments-service`            | public     | `["self-hosted","glue"]`      | **0**   | **failure ×3** |
| `market-data-processing-service` | public     | `["self-hosted","glue"]`      | **0**   | —              |

Public repos still targeting `[self-hosted, glue]` with zero runners cannot dispatch. Completing this migration (public
→ `ubuntu-latest`, remove their pools) simultaneously **fixes the breakage, harvests free minutes, removes the security
exposure, and shrinks the VM's workload to the 7 private repos** — a far larger cost win than any I/O optimisation.

Private repos remaining on self-hosted: `agent-orchestrator`, `e2e-testing`, `execution-service`, `features-service`,
`market-tick-data-service`, `ml-service`, `strategy-service` — ~1,388 of 3,809 cpu-s (**36%** of fleet load).

### Actions-minute economics (measured 2026-08-06)

**Public repos have NO minute limit — GitHub Actions is free and unlimited on standard hosted runners.** Caveats:
GitHub's _larger_ runners are billed even on public repos (stay on standard `ubuntu-latest`), and the 10 GB per-repo
cache cap still applies. Private (personal account): 2,000 min/mo included, then ~$0.008/min Linux 2-core.

Measured job-minutes, 24 h window ending 2026-08-06T07:00Z, via `scripts/cicd/measure-ci-job-minutes.sh` (GitHub's
billing REST API returns 403 for a PAT on a User account, so this measures from run/job timestamps instead — **volume,
not cost**):

| repo (all private)         | runs | jobs      | **min/24h** |
| -------------------------- | ---- | --------- | ----------- |
| `market-tick-data-service` | 49   | 256       | **1,649**   |
| `agent-orchestrator`       | 97   | 361       | **1,519**   |
| `features-service`         | 18   | 148       | 988         |
| `ml-service`               | 33   | 196       | 698         |
| `execution-service`        | 48   | 94        | 561         |
| `strategy-service`         | 13   | 74        | 301         |
| `e2e-testing`              | 25   | 124       | 159         |
| **total**                  |      | **1,253** | **5,875**   |

~5,875 min/day → ~~176,000 min/mo → **~~$1,410/mo if GitHub-hosted**, i.e. MORE than the VM costs. **For the private
set, the self-hosted VM is genuinely the cheaper option** — it is earning its keep, and its sizing is set by these 7
repos alone.

> ⚠️ **These numbers are PRE-cache-fix and were heavily inflated by it.** MTDS ran 256 jobs at ~335s cache restore each
> — ~1,430 of its 1,649 minutes. Across 1,253 jobs, roughly a third to two-thirds of the 5,875 min was `actions/cache`
> doing nothing useful (Part 3a). **Re-measured 2026-08-09: 3,972 min/24h (-32.4%) — see Progress Log.** Sizing
> decisions below may now be revisited against the post-fix number.

The 18 public repos' volume is **not yet measurable**: 16 of them have zero runners and cannot dispatch, so there is no
traffic to count until the migration is finished. What is certain is that their cost is $0 at any volume.

---

## Part 7 — Other verified findings

- **`content-gate` still runs on `ubuntu-latest`** (`python-quality-gates-v2.yml:115`, hardcoded) on every v2 invocation
  for every repo; GitHub bills a full minute for an 11-second job. Absent from the 08-05 Part 5 list. It is also the
  failure-independence path when the VM is down — a deliberate trade, not an automatic flip.
- **Governor marker-file leak**: `/opt/.qg-governor-glue-shared/.benchmarks/qg-governor/` holds **345 files, 344 of them
  `running.<pid>`**, oldest 2026-08-03 — ~115/day, unbounded. The sweep only prunes dead-PID rows inside `reservations`;
  nothing reaps the markers.
- **Scale arithmetic**: the matrix is `slice: [tests, checks]` — two jobs per repo per run, so a full fleet wave is 50
  jobs, not 25 (in ≥2 passes, since most repos have one runner).
- **Stale codex docs** (unchanged from 08-05): `central-vm-relaunch-glue-runner-reinstall.md` still describes the
  planning VM; `self-hosted-runner-security-posture.md` predates both the dedicated VM and the public migration;
  `agent-orchestrator-deploy.md` still records AO at `m8i.4xlarge`.

---

## Part 8 — Action items (re-prioritised against the downsizing goal)

> Sequencing matters: the load-reducing items must land before the load-increasing ones, or the measurements lie.

- [x] ✅ [INFRA] P0. **Remove shared-VM resource caps from `github-glue-runner.slice`.** Done 2026-08-05 via SSM;
      persisted at `/etc/systemd/system/github-glue-runner.slice.d/override-dedicated-vm.conf`. **Re-verified
      2026-08-06**: `systemctl show` confirms `CPUQuotaPerSecUSec=infinity`, `CPUWeight=100`, `MemoryHigh=infinity`,
      `MemoryMax=infinity`.

- [x] ✅ [INFRA] P0. **Bump the CI volume off the gp3 default.** Done 2026-08-05: `3,000 → 6,000` IOPS, `125 → 500`
      MB/s. Evidence: `describe-volumes-modifications` shows `completed`, StartTime `2026-08-05T10:59:26Z`. This
      resolved the true root cause (9 h pinned at 124.x MB/s). **NOTE: the original todo claimed 16,000 / 1,000 — that
      never happened; corrected here 2026-08-06.**

- [x] ✅ [INFRA] P2. **Add swap to the CI VM — done 2026-08-06 (slot-4).** 16 GB `/swapfile`
      (`fallocate`+`mkswap`+`swapon`), persisted via `/etc/fstab`, live-verified. Independently re-confirmed 2026-08-06
      via SSM (`swapon --show`). Detail: `/plans/active/ci_vm_exposure_remediation_2026_08_06.md` todo 1. Same session
      also shipped the durable resource-history-sampler + S3-mirrored backup parity with the AO box (todo 2), fixing a
      real latent `PrivateTmp=yes` bug in the checked-in `agent-orchestrator` SSOT.

- [x] ✅ [INFRA] P0. **Gate the uv cache restore/save off self-hosted runners.** Shipped 2026-08-06,
      `unified-trading-pm@9b39f6a05`. Was costing 335–894s/job for zero benefit (packages already local); the save could
      never succeed (shared 43 GB dir, `tar` exit 1). Evidence: PM run `31081212407` post-push shows
      `skipped Cache uv package cache` on both slices with `Install dependencies` still 3–4s (local cache intact) and
      the post phase absent. Full analysis: Part 3a.

- [x] ✅ [INFRA] P0. **Re-measure fleet job-minutes 24 h after the cache fix.** Re-measured 2026-08-09: **3,972
      min/24h**, down from the 5,875 min/24h pre-fix baseline (**-1,903 min, -32.4%**). Full per-repo breakdown +
      analysis in the Progress Log entry below.

- [ ] [INFRA] P1. **Investigate CI run VOLUME on the two heaviest repos.** `agent-orchestrator` fires 97 runs / 361 jobs
      per day and `market-tick-data-service` 49 runs / 256 jobs. Together that is ~54% of all fleet job-minutes. Cutting
      redundant triggers beats any instance-size choice, and no downsizing fixes it.

- [x] ✅ [OPERATOR] P0. ~~**RULED 2026-08-06, option (a): require approval for all outside-contributor fork PRs +
      restrict `allowed_actions`.** Keep `unified-trading-pm` public and self-hosted; close the fork-PR
      code-execution hole instead of moving CI or making the repo private.~~ **SUPERSEDED BY A DIFFERENT
      REMEDIATION — corrected 2026-08-19 (plan_reconciler).** The security GOAL (close the public-repo fork-PR
      code-execution exposure) was achieved, but via the OPPOSITE mechanism from what this todo scoped: PM's
      self-hosted runners were fully reverted to `ubuntu-latest` on 2026-08-07 (see this same doc's own
      L610-620/L702 "Complete the public-repo migration — DONE 2026-08-07"), not hardened-and-kept per the
      option-(a) ruling below. Codex now documents the revert as the adopted, standing posture:
      `/codex/07-security/self-hosted-runner-security-posture.md:80-89` — "the `unified-trading-pm` exposure is
      RESOLVED (2026-08-07)... Standing invariant going forward: never register a self-hosted runner pool on a
      public repo." Neither `allowed_actions` restriction nor the fork-PR-approval click-through below was ever
      applied (both remained blocked per the 2026-08-08 operator note) — moot now that self-hosted routing itself
      is gone from this repo. Flipped `[x]` on the superseding evidence, not the originally-scoped artifact,
      per this skill's own "close on newer evidence, not the stale cited artifact" convention. **Two sub-parts,
      different mechanisms (kept for the historical record, neither applied — see above):** (1) `allowed_actions` —
      checked live 2026-08-06, currently `"all"` (any marketplace/third-party action can run); tightening to `selected`
      (an explicit allow-list) is agent-executable via
      `gh api -X PUT repos/IggyIkenna/unified-trading-pm/actions/permissions` — **not yet done**, needs the actual
      allow-list enumerated from the workflows currently in use before applying (an incomplete list would break CI). (2)
      **"Require approval for all outside collaborators" on fork-PR workflow runs** — checked live 2026-08-06: this
      setting has **no documented public REST endpoint** (`actions/permissions`, `actions/permissions/workflow`, and
      `actions/required-workflows` were all checked; none expose it). It lives only under the repo's web UI: **Settings
      → Actions → General → "Fork pull request workflows from outside collaborators" → select "Require approval for all
      outside collaborators."** This is the higher-priority half (it's the actual code-execution gate; the
      `allowed_actions` restriction is defense-in-depth) — **flagging for the operator to click through directly**
      rather than risk a wrong/undocumented API call against a live security boundary. `deployment-api`'s visibility
      recheck (mentioned in the original finding) also still needs doing.

      **operator ruling 2026-08-08**: will do it later — leave BOTH sub-parts blocked for now, do not execute either
          autonomously. Preparing the exact ready-to-run steps below so both are a single click/paste next time the
          operator is available; nothing below was applied this session.

          **Sub-part (2) — the exact click-through (unchanged from above, restated for a fast pickup):**
          `github.com/IggyIkenna/unified-trading-pm` → **Settings → Actions → General** → scroll to **"Fork pull request
          workflows"** → select **"Require approval for all outside collaborators."** → Save. Verified live 2026-08-08
          this is STILL the current exposure (re-checked `gh api repos/IggyIkenna/unified-trading-pm/actions/permissions`
          → `{"enabled":true,"allowed_actions":"all","sha_pinning_required":false}` — `allowed_actions` unchanged from the
          2026-08-06 finding, and the fork-PR-approval setting itself is still web-UI-only, no API surface found).

          **Sub-part (1) — the allow-list, now actually enumerated (2026-08-08) so the command below is ready-to-paste,
          not a placeholder:** scanned every `uses:` line across `.github/workflows/*.yml` +
          `scripts/workflow-templates/*.yml*` (the fleet template sources). Local composite-action refs (`./...`) need no
          allow-list entry — only externally-hosted actions do. Full external set, 12 actions:
          `actions/cache`, `actions/checkout`, `actions/create-github-app-token`, `actions/download-artifact`,
          `actions/github-script`, `actions/setup-python`, `actions/upload-artifact`, `astral-sh/setup-uv`,
          `aws-actions/configure-aws-credentials`, `google-github-actions/auth`, `google-github-actions/setup-gcloud`, plus
          the org's own reusable-workflow refs `IggyIkenna/unified-trading-ci` and `IggyIkenna/unified-trading-pm` (PM
          calling its own reusable `python-quality-gates-v2.yml`). Ready-to-run (NOT executed this session — operator
          deferred both sub-parts):

                                                                                                                                                                              ```bash
                                                                                                                                                                              gh api -X PUT repos/IggyIkenna/unified-trading-pm/actions/permissions \
                                                                                                                                                                                -f allowed_actions=selected

                                                                                                                                                                              gh api -X PUT repos/IggyIkenna/unified-trading-pm/actions/permissions/selected-actions \
                                                                                                                                                                                -f github_owned_allowed=true \
                                                                                                                                                                                -f verified_allowed=true \
                                                                                                                                                                                -f 'patterns_allowed[]=astral-sh/setup-uv@*' \
                                                                                                                                                                                -f 'patterns_allowed[]=aws-actions/configure-aws-credentials@*' \
                                                                                                                                                                                -f 'patterns_allowed[]=google-github-actions/auth@*' \
                                                                                                                                                                                -f 'patterns_allowed[]=google-github-actions/setup-gcloud@*' \
                                                                                                                                                                                -f 'patterns_allowed[]=IggyIkenna/unified-trading-ci@*' \
                                                                                                                                                                                -f 'patterns_allowed[]=IggyIkenna/unified-trading-pm@*'
                                                                                                                                                                              ```

          `github_owned_allowed=true` covers every `actions/*` action (checkout/cache/setup-python/upload-download-artifact
          /create-github-app-token/github-script — all GitHub-owned) without needing individual patterns;
          `verified_actions=true` is intentionally NOT set (none of the 12 are in GitHub's "verified creator" program, so it
          would add nothing) — the 6 explicit `patterns_allowed` entries above cover every remaining non-GitHub-owned action
          actually in use. **Before running**: re-derive the `uses:` scan fresh (a workflow may have added a new action
          since 2026-08-08) — `grep -rhoE "uses:\s*[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+" .github/workflows/*.yml
          scripts/workflow-templates/*.yml* | sed 's/uses:\s*//' | sort -u` — and diff against the 12 above before
          applying, so a newly-added action isn't silently locked out mid-CI-run.

- [x] ✅ [INFRA] P0. **Fix the 6 failing plan-hygiene ratchets.** PM's LDR→main promotion is blocked and re-fails every
      ~15 min. Not I/O — the `checks` slice fails in 2m44s on content. Exact list in Finding 4. **DONE — closed
      2026-08-07 (na-eligibility-audit)**: fixed twice, once per recurrence — `unified-trading-pm@b30fb5267`
      (2026-08-06, "resolve 5/6 quality-gates-v2 hygiene ratchet failures blocking LDR->main promote") and
      `unified-trading-pm@50b8643dc` (2026-08-07, "fix all 5 plan-hygiene sweep hard failures blocking LDR->main
      promote" — a second recurrence of the same failure class). The later commit's own message states "Verified:
      `run_hygiene_sweep.sh --ci` EXIT 0 (0 hard failures, 1 pre-existing soft warning)"; confirmed `50b8643dc` is an
      ancestor of current HEAD on `live-defi-rollout`.

- [ ] [INFRA] P0. **Re-baseline `scripts/dev/qg_resource_baseline.json` before any sizing decision.** Live cgroup peaks
      are 3.6–5.5x the recorded values and `agent-orchestrator` is absent entirely; the admission governor over-admits
      on these numbers, a direct cause of the 6 OOM kills. Include both UI repos (22 MB / 541 MB — implausible) and
      re-measure under realistic concurrency, not `measured_concurrency: 1`.

- [x] ✅ [INFRA] P1. **Complete the public-repo migration — DONE 2026-08-07.** `instruments-service` /
      `market-data-processing-service` confirmed fixed (re-rendered templates, zero self-hosted refs, latest
      `quality-gates-v2` runs green on `ubuntu-latest`). PM's own ~40 self-hosted-routed workflows fully reverted
      (`unified-trading-pm@c8cd56251e`, `self_hosted_runner_public_repo_revert_2026_08_05.md` todo 24) — `runs-on`
      flipped via `hosted-baseline.sh` + 5 hand-reviewed files (3 needed a restored `actions/setup-python` step the
      tool's mechanical `restore` had silently dropped — a real gap in the tool, not caught by its own `verify`).
      Live-verified: `QG slice (tests)` green on `ubuntu-latest` for the post-revert commit (run 31174345746); PM's 8
      self-hosted runners (`glue-1..5`, `writer-1..3`) deregistered from GitHub + their systemd units stopped/disabled
      on the CI VM (confirmed `inactive`, no re-registration); the other 7 private repos' pools confirmed untouched. VM
      workload is now the 7 private repos only (~36% of original fleet cpu-s). **Supersedes** the 08-05 "flip PM's
      remaining workflow copies to self-hosted" todo — PM is public, so that flip was always the wrong direction.

- [ ] [INFRA] P1. **Stagger the `ldr-to-main-promote-fleet` fan-out.** The synchronised burst is what sizes the box:
      3,809 cpu-s over 15 min needs 4.2 cores; as one burst it needs 16. Pure software, zero capacity cost, largest
      single downsizing enabler.

- [ ] [INFRA] P1. **Fleet-wide CI concurrency cap.** Plain `TasksMax` (option B) investigated 2026-08-06 with real
      measurements (`TasksCurrent` 274–326 idle, ~46 tasks/active run) and **REJECTED as unsafe** — it makes `fork()`
      fail mid-job rather than queueing. Recommended mechanism: an `ACTIONS_RUNNER_HOOK_JOB_STARTED` wrapper around
      `qg-host-governor.sh`. Full detail: `/plans/active/ci_vm_exposure_remediation_2026_08_06.md` todo 3. **Amendment
      (2026-08-06):** wrap **reservation** mode, not token mode — reservation carries the per-repo RAM baselines, and
      the OOM evidence in Part 5 shows RAM is what binds. The hook also closes the Finding-6 gap by gating **before**
      setup, which in-gate `qg_governor_acquire` structurally cannot.

- [ ] [INFRA] P1. **Cut sibling-clone I/O**: shared bare repos + `git worktree` + `--filter=blob:none` for dep repos.
      Required to get peak throughput under the 312.5 MB/s baseline a 2xlarge imposes. Must ship with a stated venv
      immutability contract, `git worktree prune` on a timer, and `gc.auto=0` — see Part 4. **Do NOT** implement the
      `cp -al` shared-venv half: no I/O saving, and unsafe on ext4. **Supersedes** the 08-05 "shared bare repos +
      pre-built external venvs + worktree-based QG execution" todo.

- [x] ✅ [OPERATOR] P2. **Downsize the CI VM to `m8i.2xlarge` (8 vCPU / 32 GB) — DONE 2026-08-08 08:24 UTC.** Executed
      ~2.5h ahead of the formal 11:00 UTC checkpoint at operator instruction ("it's been 21 hours... should be good
      enough to do an audit"), against a genuinely post-fix 20.6h window (since the 2026-08-07 11:39 UTC PM-revert), not
      a partial/pre-fix one. **Audit (14,819 samples, resource-history-sampler, SSM query)**: `load_avg_1m` max **7.84**
      / p99 3.3 / p95 1.6 / mean 0.3 — **zero of 14,819 samples exceeded 8** (the target's own vCPU count); the single
      busiest real moment in the whole window (13:31-13:32 UTC 2026-08-07) was this same plan's own todo-4 24-repo
      fan-out push wave, already on record. `cpu_percent` max 60.7% / p99 23.8%. `ram_percent` max 28.6% (peak absolute
      8.8 GB of 30.8 GB) — comfortable headroom even keeping 32 GB. `swap_percent` flat at ~2% (322 MB of 15 GB) — no
      memory pressure. `iowait_percent` max 21.8% (brief) / p99 3.3%. **Zero kernel OOM-kills**
      (`journalctl -k --since "2026-08-07 11:39:00" | grep -ic "out of memory\|oom-killer"` = 0) in the entire post-fix
      window. Verdict: picture holds against the target with margin; proceeded per this todo's own pre-registered
      condition. **Pre-flight**: confirmed zero busy runners (`gh api .../actions/runners`, all 7 private repos) and
      zero in-progress workflow runs before stopping — no live job was interrupted. **Execution**:
      `aws ec2 stop-instances` → waited `instance-stopped` →
      `aws ec2 modify-instance-attribute --instance-type m8i.2xlarge` →
      `aws ec2 modify-volume --volume-id vol-03880fe9bf1ea805b --iops 12000 --throughput 312` (from 6,000/500) →
      `aws ec2 start-instances` → waited `instance-status-ok`. **Post-verify**: `nproc`=8, `free -h` shows 30Gi total
      RAM (unchanged), all 9 `github-glue-runner*` systemd units survived the reboot and are `active running`
      (`Restart=always`/`enabled` self-recovered), all 3 monitoring units (`ci-vm-resource-watchdog.timer`,
      `resource-history-sampler.service`, `resource-history-backup.timer`) `active`, and GitHub's own API confirms every
      runner `status: online, busy: false` post-boot (checked
      `agent-orchestrator`/`execution-service`/`strategy-service`). No follow-up needed; the standing
      `ci-vm-resource-watchdog.timer` (shipped same session, see
      `/plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`) continues watching the
      now-smaller box hourly for any regression.
- [ ] [INFRA] P2. **Reap the governor marker-file leak** — 344 stale `running.<pid>` files accumulating ~115/day in the
      shared coordination dir any new concurrency work would build on.

- [ ] [INFRA] P2. **Decide `content-gate`'s runner.** Hardcoded `ubuntu-latest`, one billed minute per 11-second job,
      every repo, every run — against its value as the failure-independence path when the VM is down.

- [x] ✅ [INFRA] P3. **Re-point the UI QG todo.** `deployment-ui` and `unified-trading-system-ui` are both **public**,
      so the 08-05 "migrate `ui-quality-gates-v2` to self-hosted" todo is now backwards — public repos should stay on
      GitHub-hosted (free). If they are ever made private, re-baseline them first: recorded peaks (22 MB / 541 MB) would
      let the governor admit two unmeasured multi-GB builds as nearly free. **Already true — closed 2026-08-07
      (na-eligibility-audit)**: `self_hosted_runner_public_repo_revert_2026_08_05.md` todo 19 confirms
      `unified-trading-system-ui@6441e477` was reverted "EXCEPT `ui-quality-gates-v2.yml` (already correctly
      `ubuntu-latest`)" — the state this todo asks for already holds; nothing actionable remains unless/until a future
      repo-visibility change (the conditional "if ever made private" clause, which is not this checkbox's scope).

- [x] ✅ **[DOC] P2. DONE 2026-08-09 — `unified-trading-pm@c8f7776fb`** (shipped via
      `ci_satellite_ao_dispatch_batch7_2026_08_09.md` todo 1, now archived at
      `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch7_2026_08_09.md`). ~~Update stale codex docs.~~
      `central-vm-relaunch-glue-runner-reinstall.md` (full rewrite — runners no longer on the planning VM, all facts
      live-verified via AWS `describe-instances`/`describe-volumes`); `self-hosted-runner-security-posture.md`
      (dedicated VM, current 7-repo self-hosted set, and the public-repo threat model incident marked RESOLVED);
      `agent-orchestrator- deploy.md` (AO instance size + CI-VM downsize facts corrected — the doc's own text had the
      wrong instance family and date).

- [x] ✅ [OPERATOR] P3. **DONE 2026-08-07 — already executed before being re-asked.** `i-0c9b283b31d6b5ca7` downsized
      `m8i.4xlarge` → `m8i.2xlarge` (see `plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`,
      `status: complete`, full AWS-instance-modify evidence). Operator re-confirmed 2026-08-07 ("already done").

---

## Deferred work after 2026-08-06

| Item                                              | State               | Blocked on                                                                                          |
| ------------------------------------------------- | ------------------- | --------------------------------------------------------------------------------------------------- |
| Re-measure job-minutes post-cache-fix             | **DONE 2026-08-09** | — 3,972 min/24h, -32.4% vs baseline. See Progress Log.                                              |
| Re-baseline `qg_resource_baseline.json`           | **Not done**        | Nobody — real work, and the governor over-admits until it lands                                     |
| Complete public-repo → `ubuntu-latest` migration  | **DONE 2026-08-07** | —                                                                                                   |
| Harden/remove self-hosted runners on public repos | **DONE 2026-08-07** | PM's own revert closed the last public-repo self-hosted exposure                                    |
| Downsize CI VM / planning VM                      | **DONE 2026-08-08** | CI VM 08:24 UTC + planning VM 08-07 (both `[x]` above) — table not resynced                         |
| Could any of the 7 private repos go public?       | **Operator-owned**  | Business call on repo contents; would zero their CI cost                                            |
| Fix the 6 plan-hygiene ratchets                   | **DONE 2026-08-07** | closed twice — `unified-trading-pm@b30fb5267` + `@50b8643dc` (see `[x]` above) — table not resynced |
| Sibling-clone I/O (bare repos + worktree)         | **Not done**        | Low priority — 8–11s/job, dwarfed by what was just removed                                          |

**Table corrected 2026-08-10 (plan_reconciler, ci tranche)** — the "Downsize CI VM / planning VM" and "Fix the 6
plan-hygiene ratchets" rows above had gone stale (both items shipped and are independently `[x]`-verified with commit
shas in the Resolution checklist above; this table was never resynced after). **Recommended NEXT item: re-baseline
`qg_resource_baseline.json`** — the only P1 that is neither operator-gated nor already done; the governor over-admits
until it lands.

---

## Progress Log

- **2026-08-09 (post-cache-fix re-measure)**: Re-ran `bash scripts/cicd/measure-ci-job-minutes.sh`, window since
  2026-08-08T03:27:34Z (>24h post the 2026-08-06 `actions/cache` gate-off, `unified-trading-pm@9b39f6a05`). Result:

  | repo (all private)         | runs | jobs      | min/24h (2026-08-09) | min/24h (2026-08-06 baseline) |
  | -------------------------- | ---- | --------- | -------------------- | ----------------------------- |
  | `agent-orchestrator`       | 158  | 918       | **1,152**            | 1,519                         |
  | `market-tick-data-service` | 182  | 834       | **958**              | 1,649                         |
  | `strategy-service`         | 109  | 492       | **530**              | 301                           |
  | `features-service`         | 65   | 311       | **455**              | 988                           |
  | `ml-service`               | 51   | 247       | **268**              | 698                           |
  | `execution-service`        | 85   | 378       | **412**              | 561                           |
  | `e2e-testing`              | 41   | 188       | **197**              | 159                           |
  | **total**                  |      | **3,368** | **3,972**            | **5,875**                     |

  **Net: -1,903 min/24h, -32.4%** vs the 2026-08-05/06 pre-fix baseline (Part 6). Confirms the cache-fix hypothesis: the
  two heaviest repos shrank the most in absolute terms (`market-tick-data-service` -691 min, `agent-orchestrator` -367
  min) — consistent with MTDS's 256-job, ~335s-each cache-restore cost (Part 3a) being the dominant inflator.
  `features-service` also dropped sharply (-533 min) despite run count rising, same mechanism. Fleet job COUNT actually
  rose (1,253 → 3,368, +169%) in this window — this is real activity growth, not a measurement artifact (same script,
  same methodology, both windows) — while total minutes fell 32%. Per-job cost fell from 4.69 min/job to 1.18 min/job
  (**-75%**), which is the real signature of the cache-fix: the fleet did far more CI work in far less aggregate time.
  **Sizing implication**: the self-hosted VM's true post-fix load is ~68% of what Part 6 sized against, even with job
  volume nearly 3x higher — the downsize-VM deferred item (line 697) and the plan-hygiene-ratchet fix can now reference
  this number instead of the stale one.

- **2026-08-09 (satellite-batch extraction)**: Part 8's `[DOC] P2` "Update stale codex docs" item extracted verbatim
  into `ci_satellite_ao_dispatch_batch7_2026_08_09.md` todo 1 (checkbox above replaced with a citation pointer, per the
  `ci`-tranche satellite-batch-extraction pattern). Every other open item in this doc was re-assessed and left behind —
  see batch 7's own Progress Log for the full per-item reasoning.
- **2026-08-08 (interactive session)**: Also right-sized the AO/planning VM's EBS volume (`i-0c9b283b31d6b5ca7`,
  `agent-orchestrator-vm-1`, `vol-0b4f0237fa0f5cd0f`) while auditing AWS spend more broadly — this VM is out of this
  doc's own CI-VM scope but the same live-CloudWatch-data method applies, recorded here as the closest existing home.
  48h of real `AWS/EBS` CloudWatch metrics (576 5-min samples, full coverage, `VolumeReadOps`/`VolumeWriteOps`/
  `VolumeReadBytes`/`VolumeWriteBytes`) showed combined IOPS peaking at 8,429 (53% of the provisioned 16,000) and
  combined throughput peaking at 68.9 MB/s (6.9% of the provisioned 1,000 MB/s) — even the free gp3 baseline (125 MB/s)
  already covered 1.8x the observed peak. Live `aws ec2 modify-volume` (no downtime, gp3 supports live modification):
  16,000 → 12,000 IOPS (1.4x the observed max), 1,000 → 200 MB/s (2.9x the observed max). Verified via
  `describe-volumes` post-change: `Iops: 12000, Throughput: 200, State: in-use`. Estimated saving:
  $120.00/mo →
  $57.60/mo in IOPS+throughput charges (storage unchanged) — **~$62.40/mo**, on top of the CI-VM
  instance-type downsize below.

- **2026-08-08 (interactive session)**: Executed the downsize todo (Part 8) — see that checkbox's own evidence for the
  full audit numbers, pre-flight, execution, and post-verify detail. Ran ~2.5h ahead of the formal 11:00 UTC checkpoint
  at operator instruction, against a genuinely post-fix (since 2026-08-07 11:39 UTC) 20.6h window rather than a partial
  one. `i-042a6332509482556`: `c8i.4xlarge` → `m8i.2xlarge`, volume `vol-03880fe9bf1ea805b`: 6,000/500 → 12,000 IOPS/312
  MB/s. All 9 self-hosted runner units + all monitoring timers survived the reboot; GitHub confirms every runner back
  `online`. The standing `ci-vm-resource-watchdog.timer` (shipped earlier the same session,
  `/plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`) now watches the smaller box hourly
  for any regression from this resize.

- **2026-08-07 (interactive session)** — Closed the public-repo migration for real: fixed `instruments-service` /
  `market-data-processing-service` (already resolved by concurrent work, confirmed via `gh run list` — both green on
  `ubuntu-latest`) and shipped PM's own full revert (`unified-trading-pm@c8cd56251e`,
  `self_hosted_runner_public_repo_revert_2026_08_05.md` todo 24) — ~40 workflows, `self-hosted-qg-repos.txt`, and the
  `hosted-baseline.sh` snapshot/manifest. Found and fixed a real gap in `hosted-baseline.sh restore --all`: its
  "mechanical flip" classifier only inspects the FIRST commit that introduced a self-hosted `runs-on` line, so 3 files
  (`readiness-verifier.yml`, `ruleset-drift-alert.yml`, `reconcile-release-tags.yml`) whose `actions/setup-python` /
  Firestore-SDK-install steps were removed in a LATER commit got silently restored to `ubuntu-latest` with those steps
  still missing — caught via a fleet-wide grep for python/uv/gcloud usage without a matching setup step, fixed by hand
  from each file's true first-flip-commit parent. Verified live: `QG slice (tests)` green on `ubuntu-latest` for the
  post-revert commit (workflow_dispatch run 31174345746); the only failing leg (`QG slice (checks)`) is the
  pre-existing, unrelated plan-hygiene ratchet failure (`check_reference_paths`/`check_terminal_status_archived`, from
  other agents' concurrent commits, not this change). Deregistered PM's 8 self-hosted runners
  (`glue-1..5`/`writer-1..3`) from GitHub and stopped+disabled their systemd units + PM's dedicated token/slot-refresh
  timers on the CI VM (confirmed `inactive`, no re-registration after 15s+; the other 7 private repos' pools confirmed
  untouched). Captured before/after quiet-moment CI-VM readings (load avg, RAM, swap, runner-unit count — table above)
  and opened a 24h usage-reduction tracking window, operator-set target check 2026-08-08 11:00 UTC, for the CI-VM
  downsize decision. **Process note**: two consecutive `quickmerge.sh --files` invocations hit the shared-clone
  concurrent-commit race (`shared_clone_concurrent_commit_message_swap_2026_07_28.md`) — the "already committed, no diff
  to stage" check raced against a DIFFERENT concurrent agent's commit and silently produced a no-op (verified via a
  direct `git show origin/...` content check, not just trusting the tool's "✅ Landed" message). Recovered by committing
  the exact file list directly (`git add -- <files>` + `git commit`) before re-invoking quickmerge, which then pushed
  correctly — worth remembering as the standard recovery move if this recurs.

- **2026-08-06 (cache-cost session, cont.)** — Traced the "clone is expensive" hypothesis and **falsified it**:
  `Checkout` is 1–2s (persistent `_work`, `.git` survives, `fetch-depth: 2`). The real cost was `actions/cache` on
  `~/.cache/uv` — 335–894s/job, with a save that could never succeed against a shared 43 GB dir. Gated it off
  self-hosted (`9b39f6a05`) and verified live. Measured fleet job-minutes (5,875/24h across the 7 private repos) and
  established the Actions-minute economics: public = free/unlimited, and the VM is genuinely cheaper than GitHub for the
  private set (~$1,410/mo equivalent). Promoted `scripts/cicd/measure-ci-job-minutes.sh` out of the scratchpad.
  **Corrections to my own earlier claims in this session, recorded so they don't survive as folklore:** (a) I asserted
  "RAM must not be halved / target 32 GB" from the 29.7 GB observed peak — the operator correctly pointed out that peak
  is a consequence of UNGATED concurrency, not a requirement; queue the runs and the ceiling becomes the largest single
  job (~6 GB), so 16 GB is plausible and the 32 GB recommendation was over-cautious. (b) I projected "features-service
  756s → 290s" — that is arithmetic from step timings, NOT an observation; only PM has been measured post-fix. (c) The
  `cpu_s`-per-wave figure (3,809) still rests on the 3–7 week stale baseline and should not be trusted until the
  re-baseline lands.
- **2026-08-06 (independent verification + cost re-frame)** — Re-verified every 08-05 claim against live AWS API,
  CloudWatch, SSM, cgroup v2, and the GitHub API. Results: 3 confirmed, 5 corrected, 6 falsified (Part 0). Key
  reversals: root cause is **throughput** (9 h pinned at 124.x MB/s vs a 125 MB/s ceiling), not IOPS; the 16,000 IOPS
  bump **never happened**; `uv` already hardlinks 86.5% of every venv so the shared-venv proposal's saving is ~zero and
  its `cp -al` COW argument is invalid on ext4; a cross-repo admission governor already exists (the real gap is that it
  gates the heavy phase, not setup). Re-framed against the operator's actual goal (shrink the VM): CPU fits 8 vCPU
  (3,809 cpu-s/wave), but **RAM must not be halved** — observed slice peak 29.7 GB with 6 OOM kills, and the baselines
  driving admission are 3–7 weeks stale and wrong by 3.6–5.5x. Discovered the 08-05 public-repo migration is half-done,
  and that **`unified-trading-pm` is public with 8 self-hosted runners** (P0 security) — which inverts two existing
  "flip to self-hosted" todos. Action items re-prioritised and re-sequenced; the false `[x]` corrected in place.
- **2026-08-06 (interactive session, human-driven)** — Closed the swap gap + shipped resource-history-sampler parity
  with the AO box (both live-verified, real bug found+fixed in the shared SSOT along the way). Investigated the
  concurrency-cap todo with real measurements (real `TasksCurrent` baseline + a live dispatch's measured task cost) and
  rejected plain `TasksMax` as unsafe once sized against those numbers — left open with a concrete safer next step
  identified rather than shipped half-verified. Full detail: `/plans/active/ci_vm_exposure_remediation_2026_08_06.md`.
- **2026-08-05 (interactive audit)** — Verified migration completion (25/25 pools on dedicated VM, zero on planning VM).
  Diagnosed I/O starvation: volume at default 6,000 IOPS, shared-VM resource caps still active, no concurrency cap.
  Removed resource caps live. Bumped volume to 16,000 IOPS. Documented proposed worktree + shared-venv architecture.
  Identified remaining GitHub billing sources. Flagged stale codex docs.
- **context-scout 2026-08-05**: populated context_scope (6 entries).

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — actively-evolving incident audit, OPERATOR security items

- **context-scout 2026-08-07**: refreshed context_scope (6 entries, was 6) -- swapped
  `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md` (cited only in frontmatter `related:`, never referenced in
  the doc's own body) for `scripts/plan-hygiene/run_hygiene_sweep.sh` -- the script behind the "Recommended NEXT item"
  (fix the 6 failing plan-hygiene ratchets, Part 8/Finding 4), the most actionable open item and the one currently
  blocking PM's own LDR→main promotion.

**na-eligibility-audit 2026-08-07** (tranche `ci`, autonomous, `agt-cbbd1f`): KEEP-NA, 2 stale items closed — re-read
all 15 open items end-to-end. Closed 2: "Fix the 6 failing plan-hygiene ratchets" (shipped twice,
`unified-trading-pm@b30fb5267` + `@50b8643dc`, `run_hygiene_sweep.sh --ci` verified EXIT 0) and "Re-point the UI QG
todo" (already true — `self_hosted_runner_public_repo_revert_2026_08_05.md` todo 19 confirms `ui-quality-gates-v2.yml`
was already correctly `ubuntu-latest` through the revert). 13 remain genuinely open — operator-gated, judgment-call, or
duplicate-tracked-elsewhere-so-not-closable-here (item 6, "Complete public-repo migration," and item 9, "Cut
sibling-clone I/O," are cross-referenced in sibling NA docs, not done). No `assigned_vm` change. **na-eligibility-audit
2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — re-derived the open-item count fresh and cross-checked
`/ag-closeout-audit ci`'s own fresh same-day 42-agent sweep
(`plans/active/issues/ag_closeout_audit_ci_parked_2026_08_08.md`), which independently classified this doc
`orphaned_never_touched` and extracted exactly ONE item as AO-eligible — the time-gated job-minutes re-measurement — now
claimed by `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 1 (dispatched, `status: active`); flipping this doc's
own copy of that item would create a competing dispatch path, so it stays KEEP-NA-STALE (already-claimed) on citation.
The remaining open items (investigate CI volume; the `[OPERATOR]`-tagged fork-PR-approval item, itself carrying a fresh
2026-08-08 operator ruling to defer both sub-parts; re-baseline `qg_resource_baseline.json`; stagger the promote-fleet
fan-out; the fleet-wide concurrency cap, deferred by the same sweep as D6-22, a genuine judgment call per its own 2
prior na-eligibility-audit verdicts; cut sibling-clone I/O; reap the governor marker-file leak; decide `content-gate`'s
runner; update 3 stale codex docs) were each checked against today's 9 operator-Q&A precedents — none apply. Deferring
to the same-day sibling audit's judgment on AO-eligibility rather than re-litigating in a second pass the same day. No
`assigned_vm` change.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:cf645e1fdcb52a01]: KEEP-NA,
valid — 8 open items (Part 8), all re-verified against today's fresh full read by
`ci_satellite_ao_dispatch_batch7_2026_08_09.md` todo 1 (the sole extractable item — the 3-codex-doc sync — is now DONE
via that batch, `unified-trading-pm@c8f7776fb`; the other 7 were explicitly considered and rejected there: 2 touch the
`qg_host_adaptive_resource_governor_2026_07_14.md` standing operator ruling, 1 has no stated done-when, 2 are
already-deferred fleet-wide-promote judgment calls, 1 is a re-baseline with no forcing function, 1 is the
operator-deferred fork-PR item). No `assigned_vm` change.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:45bde2ce7a6f9fbb]: KEEP-NA,
valid — Large, actively-evolving CI-VM cost/I/O audit (2026-08-05 original, independently re-verified/corrected
2026-08-06: 3 confirmed / 5 corrected / 6 falsified). Most of the original action-item list is already [x] closed with
live AWS/SSM/CloudWatch evidence (VM downsized to m8i.2xlarge, EBS bumped, public-repo migration completed, uv cache
gated off, 6 plan-hygiene ratchets fixed, job-minutes re-measured -32.4%). 8 items remain open. Each falls into one of:
(a) explicit operator-deferred security decision (item 2, [OPERATOR]-tagged, 2026-08-08 ruling 'leave... blocked...

- **context-scout 2026-08-17**: refreshed context_scope (6 entries) -- swapped the now-closed `run_hygiene_sweep.sh`
  (its only relevance, the plan-hygiene ratchet fix, is DONE) for `python-quality-gates-v2.yml`, the concrete file
  behind two still-open items (the hardcoded `content-gate` runner decision; the governor's `QG_GOVERNOR_MODE`
  reservation-vs-token gating).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)

**na-eligibility-audit 2026-08-18** (ci tranche): KEEP-NA, valid -- Large, actively-evolving CI-VM cost/I/O audit (2026-08-05 original, independently re-verified/corrected 2026-08-06: 3 confirmed / 5 corrected / 6 falsified in its own Part 0 table) with 6+ sequential na-eligibility-audit KEEP_NA confirmations from 2026-08-06 through 2026-08-10. Most of the original action-item list is already [x] closed with live AWS/SSM/CloudWatch evidence (VM downsized to m8i.2xlarge, EBS bumped, public-repo migration completed, uv-cache gated off, 6 plan-hygiene ratchets...

**na-eligibility-audit 2026-08-21** (ci tranche wave 2): KEEP-NA, valid — unchanged since the 2026-08-18 verdict.
7 open items confirmed by direct grep, all previously checked against the workspace's accumulated operator-Q&A
precedents with none applying: CI-volume investigation, re-baseline `qg_resource_baseline.json`, stagger the
promote-fleet fan-out, the fleet-wide concurrency cap (same judgment call tracked by the sibling
`ci_vm_exposure_remediation_2026_08_06.md`), cut sibling-clone I/O, reap the governor marker-file leak, and decide
`content-gate`'s runner — each either a judgment call, cross-referenced/duplicate-tracked elsewhere, or lacking a
forcing function. No new facts since 08-18. No `assigned_vm` change.
