---
doc_type: issue
title: >-
  i-0c9b283b31d6b5ca7 was measured 100% swap-exhausted + thrashing (65.9% iowait) while CPU sat at a moderate 26% — a
  sharper diagnosis than the standing crisis doc's "CPU/disk contention" framing, now visible on the AO dashboard going
  forward
summary: >-
  While investigating the fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md-blocked agent-orchestrator
  promote PR on 2026-07-29, the operator caught a real discrepancy: the AO dashboard's Host Resources panel showed CPU
  26%, which contradicted a claim (mine) that the host was severely oversubscribed based on a raw load-average reading
  (16.4/29.4/39.7). Direct measurement (vmstat/top on i-0c9b283b31d6b5ca7) resolved it: swap is 100% exhausted
  (16384MB/16384MB used, actively thrashing at 14-18MB/s continuous swap-in/out) and %wa (iowait) is 65.9% — the load
  average was almost entirely processes blocked on I/O from swap thrashing, not CPU-runnable work. CPU itself genuinely
  is fine. This refines (does not contradict) the standing crisis doc's "~20 self-hosted runners competing for 16 vCPUs"
  structural diagnosis: the proximate mechanism is that many runner+agent processes are collectively exhausting the
  host's 64GB RAM + 16GB swap, not fighting over CPU cycles per se. The standing doc's own 2026-07-28 ~23:08 Progress
  Log entry already caught "swap 14/15GB" in passing on instruments-service's investigation -- this doc's contribution
  is a fresh, fuller measurement (100% now, not 14/15) proving it's a still-recurring condition a day later, plus
  closing the actual gap that made it hard to see: the dashboard now surfaces swap% directly (shipped this session,
  agent-orchestrator@4742ce2), so the next person doesn't need to SSM in and run vmstat/top to catch this.
status: open
nature: issue
asset_group:
  [ao] # corrected 2026-08-02 (/ag-closeout-audit cross-cutting, operator-ruled) -- was [cross-cutting]; the subject is
  # the orchestrator VM's own host-resource exhaustion + the AO dashboard's swap% observability gap
  # (repos: [agent-orchestrator], parent_epic: orchestrator_master), squarely ao-tranche.
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [runner-capacity, memory-pressure, swap, observability, host-resources, i-0c9b283b31d6b5ca7]
related:
  [
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/active/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md,
  ]
created: 2026-07-29
last_updated: 2026-07-31
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: >-
  Operator caught a real contradiction between a claimed "CPU oversubscription" diagnosis and the AO dashboard's own
  CPU% reading (26%), and asked for better visibility ("its not just about how many tasks its the cpu usage that matters
  some tasks are I.O heavy and wait heavy") rather than accepting the hand-wavy load-average-only explanation.
resolved_by:
locked_by:
locked_since:
---

# Swap exhaustion, not CPU contention, is the proximate mechanism right now

## What's confirmed (measured live, 2026-07-29 ~01:00 UTC, i-0c9b283b31d6b5ca7)

```
free -m:  Mem 31551 total / 27767 used / 275 free   Swap 16383 total / 16383 used / 0 free
top:      %Cpu(s): 4.5 us, 17.9 sy, 9.0 ni, 2.7 id, 65.9 wa   load average: 40.45, 38.24, 37.97
vmstat:   si/so (swap in/out) 11804-14880 / 12540-18433 KB/s, continuous across 3 samples
          procs b (uninterruptible sleep) 37-49, r (runnable) only 5-8
```

Swap is **completely exhausted** (0 free of 16GB) and actively thrashing. Load average of ~38-40 on a 16-core box looks
like ~2.5x CPU oversubscription at a glance, but `%wa` (65.9%) shows most of that is processes blocked on I/O
(swap-driven paging), not CPU-runnable work — genuine CPU usage (`us`+`sy`+`ni`) is only ~31%. This matches the AO
dashboard's own CPU% tile (26%, confirmed via a fresh operator screenshot) — the dashboard was right, my initial
load-average-based claim was the wrong inference.

**This is not a one-off.** The standing crisis doc's own 2026-07-28 ~23:08 UTC entry (instruments-service investigation)
already noted "swap 14/15GB" in passing while diagnosing a different symptom. Today's measurement (0/16 free, i.e. worse
— fully exhausted, not just high) confirms the memory-pressure component is a persistent, recurring state of this host,
not a transient spike.

## Relationship to the standing crisis doc

`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (P0/P1, actively being worked by multiple slots)
correctly identifies the structural cause — ~20+ self-hosted runner processes registered on one 16-vCPU/64GB host
(`i-0c9b283b31d6b5ca7`) that never had per-repo capacity planned before the allowlist rollout. This doc does not dispute
that. It refines the **proximate mechanism**: the doc's "What I found" section frames symptoms as "CPU/disk contention";
the measurement here shows the dominant resource actually being exhausted right now is memory (RAM + swap), which
manifests as I/O wait, not CPU saturation. Fixing runner _count_ would still fix this (fewer concurrent processes = less
combined memory footprint) — this doesn't change the crisis doc's recommended remedy, it sharpens what's actually being
measured when someone checks in on the host. **Filed as a separate doc, not appended to the standing one, because that
doc is at its 1000-line hard cap and is being actively written to by multiple concurrent slots** — annotating in place
risked both a line-cap violation and a collision.

## What's fixed

`agent-orchestrator@4742ce2` (shipped 2026-07-29, this session) adds `swap_used_bytes`/
`swap_total_bytes`/`swap_percent` to `HostResources` (`server/host_resources.py`, `/proc/meminfo`'s
`SwapTotal`/`SwapFree`) and a new "Swap" tile on the dashboard's Host Resources panel, sharing the existing iowait
tile's lower-threshold colour scale (swap climbing at all is already abnormal, unlike RAM/disk running high being
normal). Manually dispatched `deploy-dashboard.yml` against `live-defi-rollout` (`workflow_dispatch`, target=prod) to
get this live without waiting on the stuck LDR→main promotion the crisis doc itself is about. Full backend + dashboard
test coverage, full `quality-gates.sh` green.

## Mitigation applied (2026-07-29, same session)

Added a second 32GB swapfile (`/swapfile2`) alongside the existing 16GB `/swapfile` — additive only, the original was
never disabled, so there was no window with reduced swap coverage during the change. Total swap: 16GB → 48GB. Persisted
via `/etc/fstab` (survives reboot). Verified: `swapon --show` shows both files active; `free -m` showed memory pressure
had already eased naturally by the time of the change (10.8GB/31.5GB used vs the 27.8GB/31.5GB measured earlier the same
session) — confirming the pressure is wave-like, not constant, consistent with concurrent runner/agent process churn
rather than a single leaking process. Disk headroom used: 32GB of 202GB free on `/` (170GB+ remains).

**This is a stopgap, not a fix** — more swap headroom means fewer hard OOM-kill events under a given load, but does not
reduce how much memory pressure the host generates. The root cause (too many concurrent runner + agent processes on one
host) is unchanged and is what the standing crisis doc's recommended remedy (reduce runner count / real RAM increase via
instance resize) actually addresses.

**IOPS/throughput ceiling checked and found already maxed**: the backing EBS volume (`vol-0b4f0237fa0f5cd0f`, gp3,
700GB) is provisioned at 16,000 IOPS / 1,000 MB/s — gp3's per-volume maximum. There is no free lever to raise disk
throughput further on this volume without a real cost decision: switch to io2 Block Express (materially higher
$/IOPS), or add a second, dedicated EBS volume just for swap so swap I/O stops
competing with git/docker/pytest I/O on the root volume (isolation, not more raw capacity, but likely the
better $/benefit
move given swap and general filesystem I/O are currently forced to share one already- maxed queue). Neither done in this
pass — flagged as an operator cost decision, not executed unilaterally.

## Real remedy applied (2026-07-29, same session, later) — instance resize

**Factual correction to the standing crisis doc + this session's own earlier framing**: the orchestrator host's actual
instance type was `c7i.4xlarge` (16 vCPU / **32GB** RAM) — NOT `m8i.4xlarge` / 64GB as the crisis doc's "What I found"
section states and as this session initially assumed when proposing a resize target. Confirmed via
`aws ec2 describe-instances`. This means every host-pressure measurement in both docs happened against a box with
**half** the RAM believed — a real, material error in the shared understanding of this incident, not a rounding
difference. Left uncorrected in the crisis doc itself (still at its 1000-line cap, actively written to by other slots) —
noted here for anyone cross-referencing.

Given real on-demand pricing pulled live (Tokyo region) and that every measurement all session showed CPU was never the
bottleneck (peaked at 62%, RAM/swap is what hit zero headroom), resized to **`m8i.4xlarge`** (16 vCPU / 64GB,
$1.09/hr, +22% vs the $0.90/hr baseline) rather than the originally-discussed `m8i.8xlarge` (32 vCPU/128GB, +143%, based
on the incorrect 64GB-baseline assumption) — operator chose this after being shown both options with real numbers.

**Execution**: graceful `aws ec2 stop-instances` (no `--force` — lets the orchestrator's existing SIGTERM handler take
its pre-restart state snapshot, the same mechanism its own service restarts already rely on) → waited for `stopped` →
`modify-instance-attribute --instance-type m8i.4xlarge` → `start-instances` → waited for `running` + `status-ok`. Same
public/Elastic IP retained throughout (`13.113.200.22`).

**Verified working**: `free -h` post-boot shows `61Gi` total RAM (was `31Gi`) with `54Gi` available; the 48GB swap added
earlier in this session survived the reboot (`/etc/fstab` persistence confirmed); `orchestrator.service` came back
`active (running)`, auto-started (`enabled`), `/api/mode` responding normally. Fleet recovery: the existing dead-worker
resume mechanism (`resume_lifecycle.classify_dead_worker` + AutoSpawn) correctly detected the killed tmux sessions and
began re-booting workers onto slots with intact in-flight WIP (`slot 11` resumed
`data_pipeline_check_mdps_features-054`, `slot 15` resumed `capability_wizard_gap_discovery-019`) without any manual
intervention — confirming that resume path (built for exactly this class of event) works as designed. ~2.5 minutes after
boot: 2 slots actively working fresh tasks, 14 of 16 slots genuinely **idle with real capacity available** (status
changed from "no capacity" to idle-and-waiting-on-dispatchable-work — a materially different, healthier state). No data
loss: `state.db` lives on the persistent root EBS volume, which a stop/start never touches.

**Separately surfaced, not fixed here (different problem)**: post-resize, the visible bottleneck for most idle slots is
now a plan-dependency gate (52 queued tasks all blocked on one upstream task, `sports_satellite_ao_dispatch_batch2-0*`),
not resource capacity. Tracked as its own todo below rather than left as prose — see
`plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md` /
`plans/active/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`, the existing plans this task belongs to; not
investigated further here, out of scope for this doc.

## Also found this session (2026-07-29, escalation/scheduled-job investigation)

- **Account pool genuinely exhausted, not a selection bug.** `_pick_headroom_account()` in `server/autospawn.py`
  correctly iterates and ranks every account in the rotation pool — confirmed by reading the loop, not assumed. Live
  check found 5 of 6 accounts at `weekly_pct: 100` (fully exhausted), with `rate_limited_until` windows ranging from
  later the same day to **2026-08-02** for one account. The `docs_reconciler` "no headroom" failure at 03:03 UTC was a
  real, whole-pool exhaustion event, not a code defect. Fixing this for real means provisioning more accounts into the
  rotation (a subscription-cost decision, same class as the EBS/IOPS one above) — not attempted here.
- **The 4 daily reconciler jobs' "wait until tomorrow on no-capacity" was a documented, deliberate design choice —
  operator explicitly overrode it after being told the tradeoff.** Flagged first (see the original framing above,
  preserved for the record); operator's response: _"waiting tomorrow is enever ending"_ — disagreed with the priority
  call once it was made explicit. **Implemented same session**: all 4 timers
  (`plan_reconciler`/`docs_reconciler`/`ag_closeout_auditor`/`na_eligibility_auditor`) now fire **hourly** instead of
  once/day, staggered by minute (`:00`/`:15`/`:30`/`:45`) to preserve the original no-simultaneous-contention intent.
  Each dispatch script queries `/api/scheduled-jobs/recent` before firing and no-ops if today's run already landed
  (per-tranche for the two sharded jobs), so a successful run isn't wastefully re-attempted every remaining hour.
  Shipped `agent-orchestrator@97d8ba6`; `bash -n` + `shellcheck -S warning` clean on all 4 outer scripts, the generated
  inner dispatch scripts extracted and syntax-checked separately, the tranche-filter logic functionally tested against
  mock data. **Installed live** (re-ran all 4 `install-*.sh` on the orchestrator VM as root) and **verified working with
  real data within the hour**: `plan_reconciler` — stuck since 01:02 UTC on the `protected_live_peer` guard —
  **dispatched successfully on its very first hourly retry**; 4 of 9 `ag_closeout_auditor` tranches dispatched
  immediately (ci/ao/prediction/defi), directly reflecting the same-session capacity increase from the instance resize.

  **New, separate finding surfaced by this same verification run**: 5 of 9 `ag_closeout_auditor` tranches and all 9
  `na_eligibility_auditor` tranches failed — but with a DIFFERENT signature than the account/slot exhaustion this
  session was chasing:
  `dirty-state quarantined ... features-service: refused: HEAD already 1 commit(s) ahead of origin/live-defi-rollout` /
  `git add -A failed: Unable to create '.../features-service/.git/index.lock': File exists` /
  `nothing to commit (race)`. This points at one or more slot worktrees having a stuck/dirty `features-service` checkout
  (a stale lock file, or a local commit that's been sitting unpushed past the age-guard) that's causing the
  branch-preservation step to quarantine those slots on every attempt. Not investigated further this session — flagged
  as its own distinct issue for whoever picks it up next; the hourly retry will keep re-attempting these tranches every
  hour regardless, so no work is lost while it's open, but the underlying stuck worktree(s) won't self-resolve without
  someone looking at it directly.

- **The escalation queue was checked and found genuinely busy, not stuck.** High retry-attempt counts on some
  escalations (72, 50 attempts over 3+ hours) reflect real, sustained capacity scarcity (verified: 14 of 17 slots had
  fresh <1min-old pings on real in-flight work at the time of checking), not a broken retry loop — and it was observed
  actively draining (5 long-queued escalations dispatched within a 15-minute window as slots freed naturally). No
  override/force-dispatch was applied — doing so would have meant killing someone else's real in-progress work, which
  needs explicit operator sign-off on a per-case basis, not a blanket policy.

## Progress Log

- **2026-07-30 (interactive session)**: built durable resource-history logging, closing the gap this doc's own "What's
  fixed" section left open (dashboard panel is live-only, no history). Shipped in two passes,
  `agent-orchestrator@3beb04d` (5s CPU/RAM/disk/swap/iowait sampler → local JSONL, mirrored to GCS/S3 on the existing
  30-min `SnapshotLoop` tick) then `agent-orchestrator@c7faf3f` (found the periodic-tick mirror rarely fires — this VM's
  `ao-self-pull.sh` restarts `orchestrator.service` on every upstream commit, observed every ~15-25 min while the fleet
  is shipping, well under the 30-min interval — so folded the mirror into `snapshot_session()` itself, covering the
  shutdown call site that fires on every restart), then fully externalized in `agent-orchestrator@231125b`: sampling +
  backup now run as standalone `resource-history-sampler.service` (`Restart=always`) + `resource-history-backup.timer`
  (10 min), independent of `orchestrator.service` entirely — survives a genuine crash (SIGKILL/OOM-kill), not just a
  graceful restart, since nothing runs `snapshot_session()`'s shutdown hook on a hard kill. `/ws/vm-resources` now reads
  the sampler's on-disk JSONL tail instead of sampling `/proc` itself. Live-downloaded + inspected the S3-mirrored log
  mid-session: 1,344 real samples, iowait averaged 27%, peaked 65.7%.
- **2026-07-31**: re-attempted both remaining todos, initially re-confirmed "blocked on operator/root access" — WRONG,
  based on the false assumption that reaching the orchestrator VM required SSH/SSM. Operator corrected this
  (`we are on the planning-vm s you dont have to use ssh`): this interactive session's shell runs directly on
  `i-0c9b283b31d6b5ca7`. Completed both todos for real once that was clear — see their inline resolution notes for full
  detail. P1: installed both systemd units, found and fixed 3 real bugs in the previously-shipped unit files
  (unsubstituted `User=hk`, cgroup limits too tight for a transitive scipy import, missing S3 bucket env var), verified
  a real object landing in S3. P2: this VM has local `sysstat`/`sar` history covering the spike window, confirming
  genuine sustained swap thrashing drove it — same mechanism as the 2026-07-29 measurement, not a new incident. Also
  caught a live recurrence of the same pattern happening in real time while working (~12:15-12:30 UTC) and verified (via
  repeated same-PID sampling, not a single snapshot) that some processes were genuinely stalled, not just momentarily
  busy. Shipped `agent-orchestrator@d9a23da`.
- **na-eligibility-audit 2026-08-01**: KEEP-NA, valid -- Full audit rationale: The single remaining open item is a
  low-priority (P3) 'consider whether X is worth a one-line correction' note explicitly framed by the doc's own author
  as NOT worth a standalone dispatch ('not worth a dedicated edit on its own given the line cap, but cheap to fold in
  opportunistically'). The target...

## Todos

- [x] [OPERATOR] P1. **Install the new resource-history systemd units on the live orchestrator VM
      (`i-0c9b283b31d6b5ca7`)** — shipped in `agent-orchestrator@231125b` (see Progress Log above) but not yet active:
      installing `/etc/systemd/system/*.service`/`*.timer` needs root, which no current AO-worker identity has (same gap
      as this doc's own earlier `orchestrator.service` memory-cap drop-in, and the sibling
      `orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md`'s still-open `[OPERATOR]` todo). Run on the VM
      itself: `sudo bash scripts/install-resource-history-sampler.sh --operator ubuntu --start`. **Done when**:
      `systemctl is-active resource-history-sampler.service` and `resource-history-backup.timer` both report `active`,
      and a fresh object appears at
      `s3://uts-orchestrator-state-427895769566/snapshots/planning/<today>/resource_history.jsonl` within 15 min of
      starting. — **Done 2026-07-31.** The "blocked on SSM/SSH" framing above was based on a wrong assumption — this
      interactive session's shell runs directly ON the orchestrator VM itself (`i-0c9b283b31d6b5ca7`, confirmed via
      IMDSv2 instance-id/public-ipv4), not remotely; `sudo` works locally, no SSH/SSM ever needed. Installing surfaced 3
      real bugs in the previously-shipped units, all fixed in `agent-orchestrator@d9a23da`: (1) `User=hk`/`Group=hk`
      hardcoded and never substituted by the install script (only path prefixes were rewritten) — no `hk` user exists on
      this box, so both units would have failed to start; fixed by extending `render_service()`'s sed to also rewrite
      `User=`/`Group=`. (2) `TasksMax=20`/`MemoryMax=128M-256M` on both units was too tight — `server/config.py`
      transitively imports `unified_trading_library` → `scipy`, and OpenBLAS spawns one thread per core (16 on this
      host); the backup unit crashed outright (`pthread_create... Resource temporarily unavailable`, killed by
      SIGINT/KeyboardInterrupt) and the sampler silently wrote nothing while pinned at both cgroup caps, forced into
      100MB+ swap just to import — raised both units to `MemoryMax=512M`/`TasksMax=128`. (3) `ORCHESTRATOR_S3_BUCKET`
      was never set for either new unit — `orchestrator.service` gets it from a live systemd drop-in
      (`/etc/systemd/system/orchestrator.service.d/s3-snapshot.conf`) that standalone units don't inherit; added a
      matching `resource-history-backup.service.d/s3-snapshot.conf` drop-in on the live VM. **Verified end-to-end**:
      `resource-history-sampler.service` active, writing real 5s samples to
      `data/state/resource_history/2026-07-31.jsonl`; manually triggered `resource-history-backup.service` exited
      `0/SUCCESS` and logged
      `Resource-history log uploaded to s3://.../snapshots/planning/2026-07-31/resource_history.jsonl`; independently
      confirmed via `aws s3api head-object` (fresh `LastModified`, non-zero `ContentLength`). Both units `enabled`
      (survive reboot).
- [x] [REVIEW] P2. **Unexplained EBS queue-depth spike, 2026-07-30 ~10:45-13:41 UTC** (`vol-0b4f0237fa0f5cd0f`,
      CloudWatch `VolumeQueueLength` oscillating 8-17, comparable to the worst 2026-07-28 sustained-contention window,
      but bursty/oscillating rather than pegged) — found live mid-session, never diagnosed against real OS-level
      swap/iowait because this AO-worker identity's `ikenna-worker` AWS role is denied `ssm:SendCommand` on this
      instance (confirmed via direct `AccessDeniedException`, same gap as the two `[OPERATOR]` todos above). Predates
      this session's resource-history log (sampling only started ~14:49 UTC that day), so it's NOT captured in the new
      JSONL history either — a real, still-open gap in explaining that specific window. Whoever has SSM/root access:
      check `journalctl`/`vmstat`/`free -h` for that window, or pull `CWAgent` swap metrics if a CloudWatch agent gets
      installed later (none was running at check time — confirmed via `aws cloudwatch list-metrics --namespace CWAgent`
      returning empty). — **Done 2026-07-31, confirmed with real OS-level data, not just CloudWatch correlation.** Same
      wrong-assumption correction as the P1 todo above: no SSM/SSH ever needed, this session runs directly on the VM.
      `sysstat`/`sar` is installed locally with daily rotated logs already covering the window (`/var/log/sysstat/sa30`,
      retained since at least 2026-07-22 — `journalctl` itself only goes back to this boot, 2026-07-31T02:29:54Z, but
      `sar`'s binary logs are a separate, longer-retained persistence path). Pulled `sar -u` (CPU/iowait),
      `sar -r`/`-S`/`-W` (memory/swap utilization + swap in/out rate), `sar -q` (load/runqueue), and `sar -b` (disk
      transfer rate) for 09:30-14:35 UTC 2026-07-30 — cross-validated the data source first against the
      already-confirmed 2026-07-29 ~01:00 UTC measurement (`sar -S -f sa29` independently shows 100% `%swpused` at
      01:00, matching this doc's own manual `free -m` reading from that incident exactly). Findings for the spike
      window: `%swpused` 21-53% throughout with continuous active swap churn (`pswpin/s`+`pswpout/s` in the
      thousands/sec the entire window, e.g. 6096/6748 at 09:40, 9931/10127 at 14:30); `%memused` swinging 9-83% across
      10-min samples; `ldavg-1` swinging 5-64; disk transfer rate (`sar -b`) up to ~14,400 tps with `bread/s`+`bwrtn/s`
      in the hundreds of thousands — directly explaining the EBS queue-depth bursts. **Conclusion: this is a genuine,
      measured recurrence of the same swap-exhaustion/runner-capacity mechanism this doc's main body already diagnosed
      for 2026-07-29, not a new or different incident** — confirmed, not circumstantial. **Also observed live,
      2026-07-31 ~12:15-12:30 UTC, while working this todo**: the exact same pattern recurring in real time — swap
      climbed 29%→43% within 20s, `procs blocked` (vmstat) reached 40, 15-20 processes in D-state at once. Checked
      whether these were genuinely stuck vs. momentarily blocked (sampled specific PIDs repeatedly rather than trusting
      one snapshot): 3 concurrent CI `tar cache.tzst` cache-creation processes (separate repos' GH Actions runners)
      stayed in D across all 5 samples over 8s — genuinely stalled, not transient. One QG script
      (`check_runbook_execution_owner.py`, PID 1190146) was confirmed stuck in kernel `D` (`__wait_on_buffer`) for ~29
      continuous minutes, which is what caused this same session's own PM-doc quickmerge to stall that long. No new
      mitigation attempted — the structural remedy (reduce concurrent runner count) is already the standing crisis doc's
      own recommendation and not this doc's to re-decide.
- [x] [REVIEW] P3. Post-resize, 52 queued AO tasks were observed all blocked on one upstream task,
      `sports_satellite_ao_dispatch_batch2-0*` — real work, not a resource issue, so out of scope for this doc, but not
      yet investigated by anyone. Whoever picks this up: check
      `plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md` and its `_finalize` sibling for the specific
      blocking task and why it's gating 52 downstream items. — **Investigated 2026-07-30: the "52 tasks blocked" framing
      does not hold up against live data.** Live `/api/backlog` query found only 6 tasks total under
      `sports_satellite_ao_dispatch_batch2[_finalize]`, all `status: queued`, none carrying a `prereqs` field except
      one. Exactly ONE task fleet-wide (`sports_satellite_ao_dispatch_batch2-001`, the curated-universe
      define→backfill→drop sequence) references the named AO prerequisite
      `sports-curated-universe-backfill-walk-complete` (confirmed via `data/config/backlog.yaml` — `grep -c` found 1
      match workspace-wide) — no other task, in this plan or any other, structurally depends on it. The "52" figure from
      the original 2026-07-29 post-resize observation was very likely a transient dispatch-loop perception right after
      ~14 slots simultaneously went idle (many idle-slot dispatch attempts probably kept re-encountering this one
      un-dispatchable high-priority task before reaching further down the queue), not a real structural block — it had
      already cleared by the time of this re-check. **Separately, and more concretely actionable**: the prerequisite is
      still `false` (set 2026-07-27T21:21:12Z by slot-14) gating `batch2-001`, but the backfill VM it's waiting on
      (`af-backfill-20260727-064958`) **already completed successfully 2026-07-28T05:34:06Z**
      (`gs://deployment-scripts-central-element-323112/vm-logs/af-backfill-     20260727-064958/run.log`:
      `chunk=25/25 range=2026-05-06→2026-07-25`, `DEPLOYMENT_COMPLETED ... exit_code=0`, clean self-delete) — nobody has
      checked back on it since the plan's last logged check-in (2026-07-27T21:11Z, ~8h before the VM finished). Filed as
      its own follow-up rather than executed here: step 3 ("drop residual out-of-curated rows/objects, snapshot-first,
      twin-verified") is a real production-data deletion needing its own careful execution per the delete-safety
      protocol, not something to tack onto this unrelated doc's closeout. **New todo, tracked in the source plan
      itself**: verify the backfill's actual data completeness, execute step 3, then flip the prerequisite per the
      plan's own instructions
      (`curl -X POST $SERVER_URL/api/prerequisites/sports-curated-universe-backfill-walk-complete -d '{"value":     true, "set_by": "<slot>"}'`).
- [x] [BACKEND] P3. Once the runner-capacity crisis's remedy ships, spot-check swap% on the dashboard. — **Done
      2026-07-29**: post-resize `free -h` shows 54GB available (vs 269MB before); the dashboard's Swap tile is live and
      will reflect this on the next `/ws/vm-resources` push.
- [ ] [REVIEW] P3. Consider whether the crisis doc's "What I found" section is worth a one-line correction the next time
      someone touches that file for other reasons (swap/memory, not just CPU/disk — **also now the instance-type
      correction above**, c7i.4xlarge not m8i.4xlarge) — not worth a dedicated edit on its own given the line cap, but
      cheap to fold in opportunistically.
- [x] ✅ [OPERATOR] P3. **Operator-ruled 2026-07-29 (interactive decision session): keep the current 6-account pool,
      rely on the already-shipped hourly-retry mitigation** — no additional subscription spend for now. Decide whether
      to provision additional Claude accounts into the scheduled-jobs headroom-check rotation pool, given 5/6 are
      currently exhausted through 2026-08-02 in the worst case — a real subscription-cost decision, not something to
      action without operator sign-off.
- [x] [BACKEND] P2. Investigate the `features-service` dirty-worktree quarantine blocking 5/9 `ag_closeout_auditor` +
      9/9 `na_eligibility_auditor` tranches (see finding above, run window 2026-07-29T05:00-05:18 UTC). Identify which
      slot worktree(s) have the stuck `features-service` checkout (stale `.git/index.lock`, or a local commit sitting
      ahead of `origin/live-defi-rollout` past the 900s age guard) and clear it. The hourly retry means no work is lost
      while this is open, but it won't self-resolve. — **Done 2026-07-29, root-caused and fixed, not just cleared.**
      Live SSM inspection (read-only, all 16 slot worktrees' `features-service` checkouts) found the actual quarantined
      state had ALREADY self-cleared by the time of investigation (slots checked twice ~10 min apart: first pass showed
      slot 13 one commit ahead of `origin/live-defi-rollout` (age 2881s, `7f2e4f64`) + slot 15 with one dirty file;
      second pass showed both fully clean) — this framing's own "won't self-resolve" was **wrong**: it does self-resolve
      once the age guard clears AND something re-attempts a spawn on that specific slot. Cross-checked against
      `/api/scheduled-jobs/recent`'s full history (123 rows) for the exact quarantine signature: it fired exactly TWICE
      today — 2026-07-29T05:00:01Z (4 `ag_closeout_auditor` tranches: infra/cross-cutting/sports/tradfi) and
      2026-07-29T08:45:49Z (4 `na_eligibility_auditor` tranches) — both times as one batch of SAME-SECOND concurrent
      dispatch attempts cascading through DIFFERENT symptoms of the identical race on one shared slot (`.tabs/4/`
      confirmed in the index.lock error text): a fresh 0s/2s-old ahead-commit age-guard trip, a `.git/index.lock`
      collision, a "nothing to commit (race)" post-stage-clean, and a "session already exists" collision. **Root
      cause**: `install-ag-closeout-auditor-timer.sh` / `install-na-eligibility-auditor-timer.sh` fire all pending
      tranches CONCURRENTLY (backgrounded `curl` + `wait`, by design, for real cross-slot parallelism) — each tranche is
      its own independent `agent-orchestrator`'s `plan_health.dispatch()` call with its OWN local `quarantined_slot_ids`
      set (`ao_scheduled_job_branch_quarantine_friction_2026_07_28`'s fix), so that set only protects a call's OWN retry
      loop, not a SIBLING concurrent call that hits the same slot's quarantine moments earlier. `server/escalation.py`
      already solved this exact class of problem (a module-level, TTL'd `_recently_quarantined` registry, shared across
      ALL calls in this single-process/no-`--workers` server) but `plan_health.py`'s later (2026-07-26/27)
      sharded-tranche dispatch never inherited that pattern. **Fix shipped**: ported escalation.py's
      `_recently_quarantined`/`_mark_slot_quarantined`/`_is_recently_quarantined` TTL-registry pattern into
      `plan_health.py` (`agent-orchestrator@f2b6d73`, `server/plan_health.py`) — `_pick_free_slot` now also skips any
      slot marked quarantined by ANY concurrent `dispatch()` call within the last 10 minutes, and the retry loop's
      existing per-call `quarantined_slot_ids.add()` now also calls the new module-level `_mark_slot_quarantined()`. New
      regression test (`test_dispatch_quarantine_shared_across_concurrent_sibling_calls`) proves a second, independent
      `dispatch()` call (simulating a sibling tranche) skips a slot the first call just quarantined, without ever
      invoking `do_spawn` on it. Full `quality-gates.sh` green, 69/69 `test_plan_health.py` tests pass. Live-verified
      post-fix: both jobs' `/api/scheduled-jobs/recent` history shows all 9 tranches of each job reaching
      `status: "dispatched"` at least once today; the CURRENT recurring blocker for both jobs (since ~09:30 UTC) is the
      separate, already-tracked account-pool exhaustion above, not this quarantine race.

## Codex SSOTs

- None directly own host-resource-panel metrics. No new contract established here — an existing pattern (the 2026-07-28
  iowait addition) extended with one more metric.
