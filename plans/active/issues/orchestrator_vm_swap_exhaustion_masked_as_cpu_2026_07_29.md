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
asset_group: [cross-cutting]
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
last_updated: 2026-07-29
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
not resource capacity — flagged for whoever owns that plan, out of scope for this doc.

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

## Todos

- [x] [BACKEND] P3. Once the runner-capacity crisis's remedy ships, spot-check swap% on the dashboard. — **Done
      2026-07-29**: post-resize `free -h` shows 54GB available (vs 269MB before); the dashboard's Swap tile is live and
      will reflect this on the next `/ws/vm-resources` push.
- [ ] [REVIEW] P3. Consider whether the crisis doc's "What I found" section is worth a one-line correction the next time
      someone touches that file for other reasons (swap/memory, not just CPU/disk — **also now the instance-type
      correction above**, c7i.4xlarge not m8i.4xlarge) — not worth a dedicated edit on its own given the line cap, but
      cheap to fold in opportunistically.
- [ ] [OPERATOR] P3. Decide whether to provision additional Claude accounts into the scheduled-jobs headroom-check
      rotation pool, given 5/6 are currently exhausted through 2026-08-02 in the worst case — a real subscription-cost
      decision, not something to action without operator sign-off.
- [ ] [BACKEND] P2. Investigate the `features-service` dirty-worktree quarantine blocking 5/9 `ag_closeout_auditor` +
      9/9 `na_eligibility_auditor` tranches (see finding above, run window 2026-07-29T05:00-05:18 UTC). Identify which
      slot worktree(s) have the stuck `features-service` checkout (stale `.git/index.lock`, or a local commit sitting
      ahead of `origin/live-defi-rollout` past the 900s age guard) and clear it. The hourly retry means no work is lost
      while this is open, but it won't self-resolve.

## Codex SSOTs

- None directly own host-resource-panel metrics. No new contract established here — an existing pattern (the 2026-07-28
  iowait addition) extended with one more metric.
