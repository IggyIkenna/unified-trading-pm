---
doc_type: issue
title: qg-host-governor severe contention on this host — QG_HOST_CONCURRENCY=1 floor vs 20-way slot demand
summary:
  quality-gates.sh queued 40+ minutes combined across two attempts behind the shared qg-host-governor token on this
  host, with contention worsening (16→20 concurrent slot QG runs). QG_HOST_CONCURRENCY=1 is a deliberate floor from a
  prior chronic-impairment incident (confirmed by main, not a misconfiguration) — filed for the infra/host owner to
  decide whether it still fits current fleet size, plus a separate measurement-bug finding (MAX_DURATION counts governor
  queue time as work time).
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
source: [plans/archive/issues/api_host_chronic_impairment_2026_05_29.md, scripts/quality-gates-base/qg-host-governor.sh]
related: [plans/active/utl_reuse_phase1_strategy_risk_hwm_2026_07_13.md]
tags: [infra, quality-gates, host-contention, governor]
depends_on: []
---

# qg-host-governor severe contention — QG_HOST_CONCURRENCY=1 floor vs 20-way slot demand

## What I found

Shipping a small, already-validated change to `strategy-service/strategy_service/risk/core/pre_trade_check_engine.py`
(task `utl_reuse_phase1_strategy_risk_hwm-003`), `quality-gates.sh` queued behind the shared `qg-host-governor.sh` token
for **40+ minutes combined across two attempts** on this host, with contention _worsening_ while I waited:

- Attempt 1: queued ~930s, then the run itself completed but FAILED solely on the wall-clock meta-gate
  (`Quality gates must complete in <300s (took 1238s)`) — every substantive check (tests, lint, basedpyright,
  codex-compliance ratchet) was green. The 1238s was almost entirely governor queue time, not real work.
- Attempt 2 (with the sanctioned `IGNORE_TIMEOUT=true` flag to bypass just the wall-clock check): queued 1590s+ and
  still climbing as of filing this doc, with no sign of resolving.
- Competing top-level `quality-gates.sh` process count observed climbing from 16 → 20 over the wait window; host load
  average climbing toward 5 (16 cores).
- `bash scripts/quality-gates-base/qg-host-governor.sh --status` → `K=1` — a single host-wide token for ALL slots, below
  the general documented default `max(2, floor(cores/4))` = 4 on this 16-core host.

**Escalated via `/blocked` (BLK-fbc1938a) rather than self-adjusting.** Main's ruling, after checking directly:
`QG_HOST_CONCURRENCY=1` in `.env.local` on this host is **not a misconfiguration** — `bootstrap_vm.sh` deliberately
writes this floor, tracing back to `plans/archive/issues/api_host_chronic_impairment_2026_05_29.md`. Main confirmed real
memory pressure directly on this host at the time (`free -h`: ~3.8GB swap in active use of 15GB, matching memory climbs
observed during backend restarts today) — consistent with the original incident this floor exists to prevent. Captured
here per main's instruction: `free -h` at filing time —

```
               total        used        free      shared  buff/cache   available
Mem:            61Gi        10Gi        10Gi        72Mi        41Gi        51Gi
Swap:           15Gi       3.8Gi        12Gi
```

## Why it matters

The K=1 floor is doing its job (preventing the prior chronic-impairment failure mode), but at the current fleet size
(≥20 slots issuing QG runs concurrently) it converts every full `quality-gates.sh` invocation into a 15-40+ minute wait
purely for token acquisition — a severe throughput tax across the whole fleet, and it will keep worsening as slot count
grows. The wall-clock meta-gate (`MAX_DURATION`) also has no way to distinguish "queued" time from "real work" time, so
a long queue wait can independently fail an otherwise-green run (as attempt 1 did here) unless the caller knows to pass
`IGNORE_TIMEOUT=true` — a workaround most callers won't think to reach for.

## Recommended decision

Two independent, non-conflicting questions for whoever owns this:

1. **Is K=1 still the right floor** given current fleet size and the memory pressure observed today, or does the host
   need more RAM/swap headroom (or fewer concurrently-scheduled slots) so K can safely rise above 1 without recreating
   the 2026-05-29 incident? Main's read was "do not self-adjust blind" — this needs someone with host-capacity context
   to decide, not a code-level fix.
2. **Should the `MAX_DURATION` wall-clock check exclude `qg_governor_acquire()` queue time** by design (e.g. stamp the
   "work start" timestamp AFTER token acquisition, not at script start) so a legitimate long queue wait doesn't
   masquerade as a performance regression on an otherwise-fast run? This is a genuine measurement bug independent of the
   K=1 policy question.

## Update 2026-07-13 (slot 12, cicd escalation agt-d20784, execution-service RB-327b389f)

Hit the same wall shipping the click/pillow pip-audit fix: two full `bash scripts/quality-gates.sh` attempts queued 21+
min and 15+ min respectively without acquiring the token, while a THIRD, independent slot 12 `quality-gates.sh`
invocation moments earlier (a `QG_SLICE=lint-codex` run — a light slice that never even calls the heavy phases the
governor guards) hit the SAME unconditional `qg_governor_acquire()` call at `base-service.sh:601` and queued 900s before
its own `timeout 900` killed it.

**New data point beyond the K=1-is-a-deliberate-floor finding above**: while the full-run was stuck reporting
`all 1 tokens busy`, I checked ground truth directly —

```
$ cat /proc/locks | grep 8817482          # inode of /tmp/qg-host-governor/slot.1
(no output — zero lock records on that inode)
$ exec 250>/tmp/qg-host-governor/slot.1 && flock -n 250 && echo ACQUIRED
ACQUIRED                                   # succeeded instantly, in a fresh shell
```

At that exact moment `/proc/locks` showed **no process holding the token**, yet dozens of already-running
`quality-gates.sh` processes across slots 5/8/9/10/11/13/14/15 (many 20-40+ min into their own queue wait) kept
reporting `all 1 tokens busy` on their next 30s narration tick. This is consistent with the K=1-under-20-way-demand
churn described above (a token can free and be re-grabbed by some OTHER waiter inside the ~2s poll interval, so any
single point-in-time snapshot can show "free" while the aggregate remains saturated) — I could NOT fully rule that out
with a single snapshot, so I did **not** treat this as a confirmed second bug and did not change governor code. Flagging
as a data point for whoever picks up the K=1 policy todo below: worth re-checking whether real turnover-under-churn
fully explains 20-40 min waits, or whether the acquire loop itself has a starvation/fairness gap under this many
concurrent waiters (no fairness queue — every waiter free-for-alls the same `flock -n` each tick, so a convoy of 20
waiters can in theory starve indefinitely even with genuine turnover).

**What I did**: did NOT self-adjust `QG_HOST_CONCURRENCY` or leave a `QG_GOVERNOR_DISABLE=true` run in flight against
the heavy TESTS/TYPECHECK phases (confirmed swap still at 3.4-3.8GB used — the original memory-pressure condition
persists) — killed that bypass attempt and re-queued respecting the K=1 floor with `IGNORE_TIMEOUT=true` per this doc's
own sanctioned workaround. `QG_GOVERNOR_DISABLE=true` IS safe/sanctioned for a lint-only `QG_SLICE` (no heavy phase ever
runs under it, so bypassing the queue adds no memory pressure) — used that for the fast pip-audit-only verification, but
not for the full run.

## Update 2026-07-14 (slot 10, decision on todo 1)

Re-measured live on this same host before deciding (not self-adjusting blind — this is the fresh host-capacity context
the prior escalations asked for):

```
$ free -h
               total        used        free      shared  buff/cache   available
Mem:            61Gi        12Gi        16Gi       104Mi        31Gi        49Gi
Swap:           15Gi       3.9Gi        12Gi
$ uptime
 load average: 4.00, 4.02, 2.89   (16 cores)
$ bash scripts/quality-gates-base/qg-host-governor.sh --status
qg-host-governor: K=1  dir=/tmp/qg-host-governor  flock=yes
  tokens held now: 0/1
```

Concurrent full `quality-gates.sh` demand has dropped back to ~2 runs (vs. the 16-20 that drove the 40+min queue waits
in the original filing) — the acute contention has subsided for now. **But the swap signal has not cleared**: 3.9Gi swap
in active use is the same magnitude as both the 2026-05-29 original chronic-impairment repro and yesterday's filing
(3.8Gi). Swap pressure, not raw concurrency count, was the root trigger for the K=1 floor — and it's exactly under a
demand spike back to 16-20 concurrent runs (the scenario this floor exists for) that swap pressure would compound
fastest. Raising K now would remove the guard right as it becomes needed again next time fleet size spikes.

**Decision: keep `QG_HOST_CONCURRENCY=1` on this host.** Do not raise it while swap sits in the multi-GB range; re-open
this decision only once swap usage on this host is observed near-zero sustained across a normal fleet-load window. The
real throughput-tax fix is todo 2 below (stop counting governor queue-wait against `MAX_DURATION`) — it relieves the
false-failure pain without touching the memory-safety floor. Left todos 2-4 open for their assigned crafts; did not
implement them under this SPEC-decision todo.

## Todos

- [x] [SPEC] P2. Decide whether this host's `QG_HOST_CONCURRENCY=1` floor should change given current fleet size +
      today's observed memory pressure; if raised, re-verify against the 2026-05-29 incident's original repro. (repo:
      infra/host config, not a specific service repo) — ✅ **Decision: keep K=1** — swap still ~3.9Gi in use (same
      magnitude as the original incident trigger) despite concurrent-QG demand dropping to ~2; see "Update 2026-07-14"
      above. unified-trading-pm@1aa6038d1.
- [ ] [SCRIPT] P2. Make `qg-host-governor.sh` / `base-service.sh`'s `MAX_DURATION` wall-clock check measure only
      post-token-acquisition work time, not governor queue wait, so queueing under contention cannot fail an
      otherwise-green run. (repo: unified-trading-pm, `scripts/quality-gates-base/`)
- [ ] [SCRIPT] P3. Gate `qg_governor_acquire()` on the caller's `QG_SLICE` at `base-service.sh:601` so a light slice
      (`QG_SLICE=lint-codex`, which never runs TESTS/TYPECHECK) doesn't queue behind the same heavy-phase token as full
      runs — it has nothing to protect against contention-wise. (repo: unified-trading-pm,
      `scripts/quality-gates-base/base-service.sh` + `qg-host-governor.sh`)
- [ ] [SPEC] P3. Investigate whether the acquire loop has a fairness/starvation gap under ~20-way concurrent waiters (no
      fairness ordering — every waiter races the same non-blocking `flock -n` each ~2s tick), separate from the
      K=1-is-too-low policy question above; a single `/proc/locks` snapshot during today's incident showed zero lock
      holders on the token inode while many waiters kept reporting busy, which is consistent with either explanation and
      wasn't conclusively distinguished. (repo: unified-trading-pm, `scripts/quality-gates-base/qg-host-governor.sh`)
