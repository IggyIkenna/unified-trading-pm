---
doc_type: issue
title: Shared-host `/tmp` tmpfs at 100% full — likely cause of silent QG/test stalls fleet-wide
summary:
  A shared-host `/tmp` tmpfs (fixed 2GB, RAM-backed) was measured at 100% full, accumulated since 2026-07-14 across many
  slots/agents. This both stalls any tool defaulting to `tempfile.gettempdir()` and causes a reproduced race in
  `base-service.sh`'s 25 `>/tmp/<name>_qg.log` QG-step redirects, where two slots' concurrent `quality-gates.sh` runs
  collide on the same fixed filename and produce spurious gate failures.
status: open
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
resolved_by:
source: [defi_satellite_ao_dispatch_batch1_2026_07_25.md]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

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

- [ ] [INFRA] P1. Investigate `/tmp` tmpfs exhaustion on the shared orchestrator- adjacent VM(s) — confirm scope (this
      VM only, or fleet-wide), identify the largest un-owned/stale contributors (`pytest-of-ubuntu` cache in particular,
      703M observed), and either clear safely or resize the tmpfs. `[OPERATOR]` gated for any delete — determining
      another slot's temp-file liveness isn't reliably automatable from inside one slot. Repo: agent-orchestrator (or
      the relevant infra runbook location). **Done when**: `df -h /tmp` shows meaningful headroom restored and a stated
      root cause (fleet-wide sweep gap / undersized tmpfs / missing cleanup cron) is recorded.
- [ ] [SCRIPT] P2. Fix `scripts/quality-gates-base/base-service.sh`'s 25 `>/tmp/<name>_qg.log` redirects (STEP 5.93 and
      24 siblings — grep `>/tmp/.*_qg\.log` for the full list) to use a PID-or-mktemp-unique path instead of a fixed
      shared filename, updating each step's paired read-back (`cat`/`grep -q` on the same path) to match. Root cause of
      a real, reproduced race: two slots' concurrent `quality-gates.sh` runs on the same shared host collide on the
      identical `/tmp/*_qg.log` name, causing a spurious gate failure with no content issue (direct re-invocation of the
      same checker with no concurrent QG running passes clean). Repo: unified-trading-pm. **Done when**: none of the 25
      redirects share a filename across two concurrent same-host QG runs (e.g. `$$`/`mktemp` suffixed), every paired
      read-back site is updated to the same variable, and a real concurrent-QG repro (two `quality-gates.sh` runs on the
      same host hitting the same STEP simultaneously) no longer races. **Note (2026-07-27): slot-11 appears to already
      be working a fix touching `base-service.sh` and a similarly-named issue doc
      (`qg_hardcoded_tmp_paths_false_failures_on_full_tmpfs_2026_07_26.md`) — check that doc before duplicating work.**
- [ ] [INFRA] P1. Investigate this VM's sustained oversubscription (2026-07-27 sample: `nproc=8`,
      `load average: 23.66, 36.79, 35.16`, active swap-in up to 5276 KB/s, a dozen-plus concurrent full-CPU processes
      across 6+ slots) — determine whether this is a one-off burst (many slots' scheduled full-suite QG runs overlapping
      by chance) or a standing capacity shortfall for the number of slots this VM hosts, and whether a concurrency cap
      (e.g. the existing "≤2 full QGs at once" convention) is actually being enforced anywhere or is purely advisory.
      `[OPERATOR]` — this is a capacity/scheduling decision, not a code fix. Repo: agent-orchestrator (or infra
      runbook). **Done when**: a root cause (burst vs. structural) is recorded and either a documented
      concurrency-limiting mechanism exists, or a decision to accept the current oversubscription is recorded.
