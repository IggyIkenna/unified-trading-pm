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
author: slot-10 (backend-engineer)
resolved_by:
locked_by:
source: [plans/archive/issues/api_host_chronic_impairment_2026_05_29.md, scripts/quality-gates-base/qg-host-governor.sh]
related: [plans/active/utl_reuse_phase1_strategy_risk_hwm_2026_07_13.md]
tags: [infra, quality-gates, host-contention, governor]
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

## Todos

- [ ] [SPEC] P2. Decide whether this host's `QG_HOST_CONCURRENCY=1` floor should change given current fleet size +
      today's observed memory pressure; if raised, re-verify against the 2026-05-29 incident's original repro. (repo:
      infra/host config, not a specific service repo)
- [ ] [SCRIPT] P2. Make `qg-host-governor.sh` / `base-service.sh`'s `MAX_DURATION` wall-clock check measure only
      post-token-acquisition work time, not governor queue wait, so queueing under contention cannot fail an
      otherwise-green run. (repo: unified-trading-pm, `scripts/quality-gates-base/`)
