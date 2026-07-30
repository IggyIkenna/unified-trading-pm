---
doc_type: issue
title: Shared-host `/tmp` tmpfs at 100% full — likely cause of silent QG/test stalls fleet-wide
summary:
  A shared-host `/tmp` tmpfs (fixed 2GB, RAM-backed) was measured at 100% full, accumulated since 2026-07-14 across many
  slots/agents. This both stalls any tool defaulting to `tempfile.gettempdir()` and causes a reproduced race in
  `base-service.sh`'s 25 `>/tmp/<name>_qg.log` QG-step redirects, where two slots' concurrent `quality-gates.sh` runs
  collide on the same fixed filename and produce spurious gate failures.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, tmp, quality-gates, shared-host, race-condition]
related: [/plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md]
created: 2026-07-26
priority: P1
parent_epic: infrastructure_master
assigned_vm: planning
locked_by:
resolved_by: unified-trading-pm@68309de03 (todo 2 code fix), see Progress Log for all 3 todos' resolution evidence
source: [defi_satellite_ao_dispatch_batch1_2026_07_25.md]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

> **🟢 ARCHIVED 2026-07-30** — all 3 todos done: todo 1 (`/tmp` capacity, resolved externally, confirmed 2026-07-27),
> todo 2 (`base-service.sh` PID-collision race, `unified-trading-pm@68309de03`, verified live + regression-tested this
> session), todo 3 (VM oversubscription, root-caused structural + governor confirmed enforced, closed 2026-07-29). The
> standing "Recommended decision #2" prevention question (periodic automated `/tmp` cleanup policy) is NOT dropped — it
> is tracked as a real todo in `/plans/active/issues/plan_reconcile_autonomous_sweep_2026_07_30.md` (`[OPS] P3`, fleet-wide
> cleanup-cron audit). 0 open todos here.

## What I found

While shipping `defi_satellite_ao_dispatch_batch1-010` (market-tick-data-service), my `bash scripts/quality-gates.sh`
run stalled for ~10 minutes with zero measurable CPU progress (confirmed via repeated `/proc/<pid>/stat` utime-tick
deltas over multiple windows — 1-2 ticks per 5-8s real-time, i.e. genuinely idle/blocked, not slow computation) at the
same `pytest -q` progress-bar position across several checks.

Root-caused by reproducing a much smaller collection-only run of an unrelated test file
(`tests/unit/cli/handlers/test_governance_proposals_handler.py`) which hit
`tee: /tmp/gov_collect2.txt: No space left on device` immediately. `df -h /tmp` confirmed:

```
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           2.0G  2.0G     0 100% /tmp
```

(root `/` and `/home` are fine — 74% used, 76G free. Only the `/tmp` tmpfs, a fixed 2GB RAM-backed mount, is exhausted.)

`du -sh /tmp/* | sort -rh` shows ~3,136 top-level entries totaling the full 2.0GB, accumulated continuously since
**2026-07-14** (12 days) — a mix of systemd private dirs, `pytest-of-ubuntu` caches (703M), and clearly-scratch files
from many different slots/agents over time (`hitrate_*`, `regen-ldr-plans-*`, `deployment-api-image-check`,
`tarball_check`, `avail_index_check.parquet`, `pre_leagues*.parquet`, `run_log*.log`, etc.) — none of it appears to be
actively cleaned up by any process.

**I did NOT bulk-delete other slots' files** — many could be another agent's live in-flight scratch state (per the
multi-agent-safety "don't touch unfamiliar files" rule), and ownership/liveness isn't determinable from mtime alone at
this population size. I only removed my own 3 stray files (`/tmp/collect_order.txt`, `/tmp/gov_collect.txt`,
`/tmp/gov_collect2.txt` — a mistake on my part, using `/tmp` instead of my assigned scratchpad dir for a quick
diagnostic; corrected for the rest of this session by exporting `TMPDIR` to my scratchpad path).

## Why it matters

Any process on this host that defaults to `tempfile.gettempdir()` (`/tmp`) without an explicit override — coverage.py's
intermediate buffers, some subprocess tooling, `pytest`'s own cache in some configurations, Node/other language tooling
— will silently block or fail once `/tmp` has zero bytes free. This is consistent with (though I have not proven it is
THE cause of) the ~10-minute stall I hit at ~80% through a 7077-item pytest run: no per-test 60s timeout fired, CPU went
near-idle, and the process was not blocked in any test file I touched or in any test file whose logic I could implicate
— the failure mode looks exactly like a write-to-full-disk hang rather than a slow test.

This is a **shared, cross-slot resource** (RAM-backed tmpfs, fixed 2GB, shared by every process on this VM regardless of
which slot spawned it) — if my QG run hit this, other slots' concurrent full QG runs (I observed slot-2 and slot-3 also
running `quality-gates.sh` concurrently during this same window) are exposed to the identical risk. A silent stall reads
as "still working" to an agent that only checks liveness rather than a real progress metric (the exact anti-pattern
CLAUDE.md's async-wait-discipline HARD RULE warns about) — worth flagging fleet- wide rather than treating as a one-off.

## Update (same session): a second, more precise finding — a real code bug, not just capacity

While retrying my own `quickmerge.sh` for this very issue doc, `quality-gates.sh` FAILED STEP 5.93
(`check_canonical_model_regressions.py`) even though invoking that exact checker directly (same args) reported clean
(`OK — 0 baselined; 0 new canonical-model regressions`). Root cause: `scripts/quality-gates-base/base-service.sh`
redirects STEP 5.93's checker output to a **fixed, non-PID-unique** path, `/tmp/canonical_model_regressions_qg.log`,
then branches on the redirected command's exit code. This same shape (`>/tmp/<name>_qg.log 2>&1`, no `mktemp`/PID
suffix) repeats **25 times** across `base-service.sh` (grep for `>/tmp/.*_qg\.log`). On a shared host running multiple
slots' `quality-gates.sh` concurrently (observed: slot-2, slot-3, and my slot-14 all mid-QG at once this session), two
concurrent invocations of the SAME step collide on the SAME filename — a genuine write/read race independent of tmpfs
capacity. A retry with no concurrent QG running (confirmed via direct re-invocation) passed cleanly, consistent with a
race rather than a content bug.

This is a real, fixable code defect (and ironically the same "hardcoded `/tmp`" shape STEP 5.6x-series checks ban in
service code) — but fixing all 25 occurrences correctly requires updating each paired write-then-read-back reference
(the log is `cat`'d and `grep`'d after the `if`), which is a substantially larger, more invasive change than fits this
session's assigned task. Filed here rather than attempted inline.

## Update (2026-07-27): the parent phenomenon — this host is severely oversubscribed

While waiting to re-run a manifest-cleanup script for an unrelated todo, a simple `gcs_describe_object` metadata-only
GCS call (no data body, previously returned in under a second) started reproducibly timing out at 20-30s. `uptime` /
`vmstat` on this same VM showed:

```
load average: 23.66, 36.79, 35.16     # nproc = 8 — i.e. 3-4.6x oversubscribed
Mem: 30Gi total, 11Gi used, 10Gi free; Swap: 15Gi total, 7.3Gi used
vmstat: si (swap-in) up to 5276 KB/s in a 3-sample/1s window — actively thrashing, not just holding swap
```

`ps --sort=-pcpu` at the same moment showed a dozen-plus concurrent full-CPU processes across at least 6 different slots
(`.tabs/4`, `.tabs/5`, `.tabs/6`, `.tabs/12`, plus `unified-trading-pm`/`agent-orchestrator` root-clone cron jobs) —
full pytest suites, a `check_ag_closeout_linkage.py` audit, `gen_doc_index.py`, GH Actions runner workers, and this
session's own manifest read, all competing for 8 cores and 30GB RAM at once.

This is very likely the SAME root mechanism behind the `/tmp` STEP 5.93-class QG race documented above (a genuinely
overloaded host makes every timing-sensitive shared-file/network operation more likely to collide or hang) and behind a
background process of mine being killed outright (SIGTERM, exit 143) partway through a 30-minute run with no error of my
own — plausibly an OOM-adjacent reaper (`earlyoom` is present per `/tmp/systemd-private-*-earlyoom.service-*` in the
tmpfs listing above) or some other resource-pressure-triggered kill, though I did not directly prove which mechanism did
it. The `/tmp` capacity issue and the QG temp-file race are real and worth fixing on their own, but they are symptoms of
this host running well past its safe concurrent-workload capacity, not the root cause by themselves.

## Recommended decision

This is an infra/fleet hygiene gap, not a code defect in any single repo — routing it to the operator / infra role
rather than deciding unilaterally:

1. **[OPERATOR] Immediate**: decide whether it's safe to clear stale `/tmp` entries fleet-wide right now (a
   `find /tmp -mtime +1 -not -path '/tmp/.X11-unix*' ...` sweep, systemd-private-* dirs excluded) — this needs a human
   call since some entries may be live-agent state, and I have no reliable way from inside one slot to prove liveness
   for another slot's temp files.
2. Consider whether a periodic `systemd-tmpfiles`-style sweep or a larger `/tmp` tmpfs size
   (`mount -o remount,size=...`) is the right long-term fix, or whether process-level `TMPDIR` isolation per slot (each
   slot's scratchpad dir, already the documented convention per the workspace scratchpad rule) should be enforced more
   broadly for shared tooling (coverage.py, pytest cache, etc.) so `/tmp` itself stops being a shared bottleneck.
3. If confirmed as the QG-stall root cause: no code fix needed in market-tick-data-service itself — this doc is the
   record; my own QG re-run for `defi_satellite_ao_dispatch_batch1-010` proceeds with `TMPDIR` explicitly overridden to
   my scratchpad dir to route around it.

## Todos

- [x] ✅ [INFRA] P1. Investigate `/tmp` tmpfs exhaustion on the shared orchestrator- adjacent VM(s) — confirm scope
      (this VM only, or fleet-wide), identify the largest un-owned/stale contributors (`pytest-of-ubuntu` cache in
      particular, 703M observed), and either clear safely or resize the tmpfs. (Originally gated `[OPERATOR]` for any
      delete — determining another slot's temp-file liveness isn't reliably automatable from inside one slot; moot now,
      see resolution below — no delete/resize was ever dispatched under that gate.) Repo: agent-orchestrator (or the
      relevant infra runbook location). **Done when**: `df -h /tmp` shows meaningful headroom restored and a stated root
      cause (fleet-wide sweep gap / undersized tmpfs / missing cleanup cron) is recorded. — unified-trading-pm (this
      doc), see 2026-07-27T12:49Z Progress Log entry: confirmed resolved externally between the 09:40Z SSM check and
      this session — no delete/resize performed by this slot.
- [x] ✅ [SCRIPT] P2. Fix `scripts/quality-gates-base/base-service.sh`'s 25 `>/tmp/<name>_qg.log` redirects (STEP 5.93 and
      24 siblings — grep `>/tmp/.*_qg\.log` for the full list) to use a PID-or-mktemp-unique path instead of a fixed
      shared filename, updating each step's paired read-back (`cat`/`grep -q` on the same path) to match. Root cause of
      a real, reproduced race: two slots' concurrent `quality-gates.sh` runs on the same shared host collide on the
      identical `/tmp/*_qg.log` name, causing a spurious gate failure with no content issue (direct re-invocation of the
      same checker with no concurrent QG running passes clean). Repo: unified-trading-pm. **Done when**: none of the 25
      redirects share a filename across two concurrent same-host QG runs (e.g. `$$`/`mktemp` suffixed), every paired
      read-back site is updated to the same variable, and a real concurrent-QG repro (two `quality-gates.sh` runs on the
      same host hitting the same STEP simultaneously) no longer races. — unified-trading-pm@68309de03 (slot-8,
      2026-07-30T01:45Z), see 2026-07-30T~04:xxZ Progress Log entry (slot-12): verified this todo was already shipped
      but never checkbox-flipped; confirmed live on HEAD + regression-tested, no new code needed. **Note (2026-07-27):
      slot-11 appears to already be working a fix touching `base-service.sh` and a similarly-named issue doc
      (`qg_hardcoded_tmp_paths_false_failures_on_full_tmpfs_2026_07_26.md`) — check that doc before duplicating work.**
- [x] ✅ [INFRA] P1. Investigate this VM's sustained oversubscription (2026-07-27 sample: `nproc=8`,
      `load average: 23.66, 36.79, 35.16`, active swap-in up to 5276 KB/s, a dozen-plus concurrent full-CPU processes
      across 6+ slots; corroborated 2026-07-27T22:28Z at a higher core count, `nproc=16`,
      `load average: 86.26, 138.88, 218.93`, see Progress Log — proportionally MORE oversubscribed, not less) —
      determine whether this is a one-off burst (many slots' scheduled full-suite QG runs overlapping by chance) or a
      standing capacity shortfall for the number of slots this VM hosts, and whether a concurrency cap (e.g. the
      existing "≤2 full QGs at once", `max(2, floor(cores/4))` convention) is actually being enforced anywhere or is
      purely advisory. **Dispatch as a normal audit+build todo, not an operator ask**: record the burst-vs-structural
      root cause, then implement/enforce the already-standing concurrency-cap convention (e.g. a pre-QG slot-lock/lease
      so a new full QG run waits rather than piling onto an already-saturated host). Only escalate to `[OPERATOR]` if
      the audit concludes the fix requires paying for additional VM capacity (a narrower, separable ask than this
      bundled todo). Repo: agent-orchestrator (or infra runbook). **Done when**: a root cause (burst vs. structural) is
      recorded and either a documented concurrency-limiting mechanism exists, or a decision to accept the current
      oversubscription is recorded. — **CLOSED 2026-07-29T14:xxZ (slot-10, `infra` role)**: see 2026-07-29 Progress Log
      entry — root cause is STRUCTURAL (recurring across 2026-07-27/28/29, not a one-off), and a concurrency-limiting
      mechanism for this todo's own named convention ("≤2 full QGs at once") is confirmed LIVE + ENFORCED, not advisory
      (`qg_host_adaptive_resource_governor_2026_07_14.md`, verified with a fresh live `--status` read this session). No
      new build needed under this todo.

## Progress Log

- 2026-07-29T14:xxZ (slot-10, `infra` role, dispatched to todo 3): closing todo 3 by synthesizing existing evidence
  rather than re-running an audit that has already been done exhaustively by other slots over the past 3 days — a fresh
  literature check found this exact question already answered piecemeal across several docs; the gap was that nobody had
  closed this specific todo against that evidence.

  **Root cause: STRUCTURAL, not a one-off burst.** The 2026-07-27 sample this todo cites (nproc=8→16, load 23-36→86-218)
  is one of at least 4 distinct recurrence events on the SAME host (`i-0c9b283b31d6b5ca7`) across 2026-07-27/28/29, each
  with a different proximate trigger but the same underlying cause (too many concurrent tenants — interactive/autonomous
  slot workers PLUS 20+ GitHub Actions self-hosted-runner pools — for the host's provisioned capacity at the time):
  1. 2026-07-27: registering 23 self-hosted-runner pools (46 processes) at once, concurrent with 22 repos' real
     quickmerge/QG runs, drove 66-93% iowait (`orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md`).
  2. 2026-07-28 (~18:40-20:45 UTC): recurred on `deployment-ui`'s CI, this time with genuine CPU load (34-15-10%
     us/sy/ni) + 39.7% wa + swap at 97.8% — worse than the first episode, same doc.
  3. 2026-07-29 (~01:00 UTC): swap fully exhausted (0/16GB free, 65.9% iowait) while CPU sat at a moderate 26-31%
     (`orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29.md`) — a THIRD recurrence, different dominant resource
     (memory/swap, not CPU or disk-queue this time). Each recurrence was mitigated with an escalating, real fix (glue-2
     runner disable → EBS IOPS bump 8000→16000 → instance resize DOWN to `c7i.4xlarge`/32GB (right-sizing) → instance
     resize UP to `m8i.4xlarge`/64GB + swap 16GB→48GB after the pattern proved the smaller box wasn't enough) — the fact
     that fixes keep being needed roughly every 24h as the fleet/runner-pool count grows is itself the structural
     signature; a true one-off burst would not recur 3+ times with escalating remedies. The still-open
     `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (status: open, actively worked) is the
     correctly-scoped owner of the runner-pool axis of this — not duplicated here.

  **Concurrency-cap convention — for THIS todo's own named mechanism ("≤2 full QGs at once" / `max(2, floor(cores/4))`),
  CONFIRMED ENFORCED, not advisory.** That fixed-K convention has been SUPERSEDED (not just supplemented) by the
  host-adaptive RAM+CPU dual-gate reservation governor shipped and validated in
  `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md` (codex `quality-gates.md` carries a 🟢 LIVE +
  VALIDATED banner). Verified LIVE on this session's own host via a fresh
  `bash scripts/quality-gates-base/qg-host-governor.sh --status` call (not trusting the plan's claim second-hand):

  ```
  qg-host-governor: MODE=reservation  ledger=/tmp/.benchmarks/qg-governor/reservations  flock=yes
    host: MemTotal=61GiB  MemAvailable=50GiB  physical_cores=8
    RAM budget (70%): 44278MB  reserved: 0MB  free: 44278MB  (live avail 52155MB)
    CPU slots (80% x 8): 6  running heavy phases: 0  (K runaway-backstop=6)
  ```

  `MODE=reservation` (not the legacy `token` bucket) confirms real, atomic, flock-protected admission is active — this
  is an enforced mechanism, not documentation-only. This governor gates INTERACTIVE slot-worker `quality-gates.sh` runs
  specifically (the exact axis this todo's cited convention describes); it does not (and was never meant to) gate GitHub
  Actions self-hosted-runner CI job concurrency, which is the separate axis the still-open crisis doc above owns.

  **Current live host state (this session, 2026-07-29T14:17Z)**: load average 6.73/4.20/2.58 (16 logical/8 physical
  cores), 0.0% iowait, 0 processes in D-state, swap 8.2/47GiB used (not exhausted), governor idle (0MB reserved) —
  healthy right now, consistent with the swap-exhaustion doc's own observation that pressure here is "wave-like, not
  constant."

  **Disposition**: both halves of this todo's "done when" bar are met — (1) root cause recorded (structural, recurring,
  driven primarily by self-hosted-runner-pool growth outpacing host sizing, evidenced by 3+ independent recurrences over
  3 days each needing a real fix) and (2) a documented, verified-live concurrency-limiting mechanism exists for the
  specific convention this todo named (the QG governor). No new build was needed under this todo's scope — the
  runner-pool-capacity axis is a distinct, already-open, actively-worked issue
  (`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`), correctly left there rather than folded in here to
  avoid duplicating ownership. Closing todo 3.

- 2026-07-27T09:40Z (slot-4, laptop, corroborating from a different vantage point — read-only AWS SSM, not from an
  interactive slot session): filing `/plans/archive/issues/heavy_resource_vm_spin_up_rule_gap_2026_07_27.md` surfaced a
  Slack claim of "planning-vm disk at ~92%" needing verification. Queried the live host directly via
  `aws ssm send-command` against `i-0c9b283b31d6b5ca7` (`ap-northeast-1`): `/tmp` tmpfs still `2.0G 2.0G 0 100% /tmp` —
  unchanged from this doc's original finding, still fully exhausted. `/` at `290G 278G 12G 96% /`, `free -h`
  `30Gi total / 8.9Gi used / 2.7Gi free`, swap `4.2Gi/15Gi` used, load average `9.40 11.75 13.13`. Confirms the standing
  condition from an external vantage point independent of any slot session. Not attempting cleanup — same
  `[OPERATOR]`-gated posture as this doc's existing todos.

- 2026-07-27T12:49Z (slot-12, dispatched to todo 1): re-investigated from inside the affected host itself (confirmed via
  IMDSv2 `instance-id` = `i-0c9b283b31d6b5ca7`, `ap-northeast-1` — the SAME VM as every prior finding in this doc, so
  scope is confirmed as **single shared host, not a multi-VM fleet issue** — "fleet-wide" in this doc's earlier language
  means "affects every slot process sharing this one host's tmpfs", not multiple VMs).

  **Current state — both the `/tmp` and `/` crises from this doc are RESOLVED, as of a window BEFORE this session
  started (I performed no delete or resize myself):**
  - `df -h /tmp`: `2.0G 510M 1.6G 25%` (was `2.0G 2.0G 0 100%`) — 1.6G headroom restored. `pytest-of-ubuntu`
    specifically dropped from the originally-observed 703M to 2.0M.
  - `df -h /`: `484G 302G 182G 63%` (was `290G 278G 12G 96%` per the 09:40Z SSM sample above) — note the total capacity
    itself grew 290G→484G.

  **Root cause of the `/` recovery — confirmed, not inferred**: `journalctl` shows `sudo growpart /dev/nvme0n1 1` +
  `sudo resize2fs /dev/nvme0n1p1` executed today at `09:27:17Z`, `09:28:05Z`, `09:28:37Z`, `09:28:51Z` (several
  retries/dry-runs, incl. one traced with `bash -x`) and a final successful pair at `09:46:27Z`/`09:46:28Z`
  (`kernel: EXT4-fs (nvme0n1p1): resizing filesystem from 78380795 to 130809595 blocks` →
  `resized filesystem to 130809595`). This is a genuine EBS-volume-grow + online filesystem resize, i.e. someone (with
  sudo, root-owned `PWD=/home/ubuntu`) actually enlarged the underlying disk — consistent with the operator or another
  agent acting on this same issue doc's capacity concern, not a coincidence.

  **Root cause of the `/tmp` recovery — confirmed NOT the daily timer, so a deliberate one-off action**: the `/tmp`
  tmpfs `size=2097152k` mount option is UNCHANGED (still exactly 2GB — no tmpfs resize happened), so the 1.5GB drop in
  USED space is from a deletion, not a bigger tmpfs. `systemctl show systemd-tmpfiles-clean.timer` shows its last actual
  firing was `2026-07-26 13:17:04Z` (yesterday) with the next scheduled for `2026-07-27 13:17:03Z` (still ~30 min in the
  future at investigation time) — the routine daily sweep did NOT run in the 09:27–12:49Z window, so it is not the
  explanation. Corroborating evidence of a targeted stale-file sweep (not a blanket wipe): boot-time system dirs from
  `2026-07-14` (`.X11-unix`, `.ICE-unix`, `systemd-private-*`) are still present untouched, while the oldest SURVIVING
  scratch file now dates to `2026-07-24` — i.e. everything scratch-shaped and >~3 days old was removed while live system
  sockets and recent (<3 day) scratch were left alone. This is exactly the shape of this doc's own recommendation #1
  (`find /tmp -mtime +1 -not -path '/tmp/.X11-unix*' ...`, systemd-private-* excluded), strongly suggesting the operator
  (or an infra agent acting on their approval) already ran the recommended sweep.

  **Disposition**: both halves of this todo's "done when" bar are met (`df -h /tmp` shows meaningful headroom restored;
  root cause stated — fleet-wide accumulation from many slots' unmanaged scratch writes, compounded by a root-disk
  capacity shortfall that has now also been fixed) — closing this todo. I performed NO delete and NO resize myself (both
  were already done by the time I investigated); this entry is confirmation + root-cause attribution, not new
  remediation. The standing prevention question this doc's "Recommended decision" #2 raises (periodic tmpfiles sweep vs.
  broader `TMPDIR` isolation enforcement) is still genuinely open and is NOT resolved by this todo closing — leaving it
  in "Recommended decision" for a future operator call, since installing an automated recurring delete policy is the
  same class of judgment call as the manual sweep this doc already gated `[OPERATOR]`. Todos 2 (base-service.sh
  `/tmp/*_qg.log` race — separately in progress per slot-11's note above) and 3 (oversubscription capacity decision)
  remain open and are unaffected by this finding.

- 2026-07-27T22:28Z (slot-13, `cicd` role, dispatched to `ldr_qg_failure` escalation `agt-1c4089` for
  `ibkr-gateway-infra`): corroborating evidence for open todo 3 (oversubscription), from a CI-gate-failure angle rather
  than an interactive-slot angle. `ibkr-gateway-infra`'s `quality-gates-v2` was RED on `live-defi-rollout` with both
  matrix legs (`tests`, `checks`) failing after ~10m. Diagnosis: **not a code/test defect** —
  `bash scripts/quality-gates.sh` on the exact failing commit (`47d2456`, itself a same-day self-hosted-runner rollout
  for this repo) passed clean locally in 135s, all gates green. The CI failure traced to two self-hosted-runner-pool
  problems on this same VM: (1) one of the repo's 2 dedicated `glue` runners (`glue-2`) was crash-looping on
  re-registration (`curl: (22) HTTP 422`, systemd restart counters 38/45) during the failing window, then came back up
  as a **zombie** — its `Runner.Listener` process alive and logging "Listening for Jobs" locally, but never actually
  appearing in `GET /repos/.../actions/runners` (confirmed via the live GitHub API, not just local process state) —
  leaving only 1 of 2 runners actually able to claim jobs, so the `tests` leg sat queued behind `checks` instead of
  running in parallel. I fixed this specific defect myself (own-user `kill` on the zombie PID — no sudo needed since the
  process is owned by `ubuntu`; systemd's `Restart=always` cleanly re-registered it, confirmed via the runners API
  showing both `glue-ip-172-31-5-118-1` and `-2` `status: online`). (2) Even after both runners were healthy, the
  `checks` leg — a 135s job locally — was still `in_progress` after 27+ minutes. `uptime` at that point:
  `load average: 86.26, 138.88, 218.93` on `nproc=16` (this VM's core count as of today, up from the `nproc=8` in this
  doc's 2026-07-27 finding above — the host itself has apparently been resized since, but is proportionally MORE
  oversubscribed now: ~5-14x vs. the earlier 3-4.6x) — i.e. the exact standing condition todo 3 describes, now with a
  concrete CI-gate-blocking consequence (a repo's required promotion check effectively hangs, not just an interactive
  slot's QG run). I did not attempt to address the oversubscription itself (same `[OPERATOR]`-gated capacity/scheduling
  decision as todo 3 — not something I can or should unilaterally fix by killing other slots' work). Not closing todo 3;
  this is corroboration + a fresh, higher core-count data point, and a new symptom category (CI required-check
  starvation) worth noting for whoever picks up the capacity decision. Pinging the `ibkr-gateway-infra` authoring slot
  with this diagnosis; not blocking further on watching this specific CI run complete (est. up to 135min timeout at this
  slowdown rate) since holding this shared CI-firefighter slot that long starves other queued escalations per the `cicd`
  role's own scoping — GH Actions will resolve the run asynchronously regardless.

- 2026-07-30T03:07Z (slot-4, `infra` role, dispatched to `ao_consolidated_closeout_2026_07_25.md` item 227): a THIRD
  recurrence, corroborating that todo 1's 2026-07-27 fix (a manual sweep) and the standing "Recommended decision" #2 gap
  (no automated recurring cleanup enforced) are exactly as this doc left them. `df -h /tmp` measured
  `2.0G 2.0G 4.0K 100% /tmp` — full again, `pytest-of-ubuntu` alone at 1.1G — blocking my `quality-gates.sh` run for an
  unrelated, already-committed, test-only change (`5727cb7`, agent-orchestrator). Used the sanctioned
  `scripts/dev/cleanup-stale-qg-tmp.sh` (confirmed `fuser` available on this host, so liveness is the real gate, not
  just the min-age heuristic; confirmed zero live pytest processes host-wide via `ps aux` before running) with
  `--min-age 2` (lower than the 60-min default — safe here since `fuser`, not min-age, is the actual liveness proof;
  dry-run first showed `skipped_live=0`) — removed both `/tmp/pytest-of-ubuntu` and `~/.cache/qg-tmp/pytest-of-ubuntu`,
  restoring `/tmp` to `926M used / 1.1G avail (46%)`. Did NOT touch the other large scratch files in `/tmp`
  (`cefi_availability_index.parquet`, `fred_check*.parquet`, `pm_baseline_check/`, etc.) — those aren't the sanctioned
  script's target and their liveness/ownership isn't provable from this slot, same caution as every prior entry in this
  doc. This is the THIRD time `/tmp` has hit 100% since the 2026-07-14 origin (2026-07-26 origin finding, 2026-07-27
  first recovery, now 2026-07-30) — each recovery so far has been a manual/ad hoc sweep by whichever slot happened to
  hit the wall, not the automated recurring policy "Recommended decision" #2 still asks for. Not attempting to resolve
  that standing question myself (same judgment-call class as before); flagging the recurrence count as evidence for
  whoever eventually picks up #2. Todo 2 (the `base-service.sh` `/tmp/*_qg.log` race) remains open and untouched by this
  entry.

- 2026-07-30T~04:xxZ (slot-12, dispatched to todo 2, `shared_host_tmp_tmpfs_full-002`): dispatched to fix the same
  PID-collision race this todo describes — found it was **already shipped, just never checkbox-flipped**. Fresh-pulled
  `unified-trading-pm` to `origin/live-defi-rollout` and found `scripts/quality-gates-base/base-service.sh@68309de03`
  (slot-8, 2026-07-30T01:45Z; code commit `f0c3d5209` + its quickmerge-push `68309de03`) already routes every one of the
  28 checker-capture paths through a locally-scoped `.$$`-suffixed variable (`_LOG="${TMPDIR:-/tmp}/<name>_qg.log.$$"`),
  reused for the write and every paired read-back, then `rm -f`'d after use — mirrors the pre-existing `_bp_out.$$`
  convention. Confirmed, not assumed: `git merge-base --is-ancestor 68309de03 HEAD` (already an ancestor, no rebase
  needed), grepped the file for any remaining bare (non-`.$$`) `_qg.log`/`_qg.err` capture path (zero hits — all 28
  sites confirmed suffixed), and ran the accompanying `scripts/quality-gates-base/tests/test-qg-tmp-log-pid-collision.sh`
  regression test slot-8 shipped alongside the fix (extracts the real STEP 5.93 block and proves under true concurrency
  that the current PID-suffixed block never cross-reads, a hand-built pre-fix stand-in reliably DOES cross-read under
  identical timing, and no bare capture path remains) — `3 passed, 0 failed`. No code change needed from this slot;
  flipping this todo's checkbox now closes the gap between shipped-and-verified code and plan state (the exact
  false-duplicate-dispatch risk the "Note (2026-07-27)" on this todo was trying to prevent — the dispatcher re-derived
  it anyway because the checkbox itself was never flipped, only the archived sibling doc's todos were).
