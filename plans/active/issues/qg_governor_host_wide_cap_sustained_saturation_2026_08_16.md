---
doc_type: issue
title: QG host-wide governor (cap=6) saturated continuously for 30+ minutes, twice, on one ordinary shipping task
summary: >-
  Shipping a single-file, one-off manifest-mutation script through the normal quickmerge flow hit two separate 30+
  minute stretches where quality-gates.sh's host-wide concurrency governor (market-tick-data-service sub-cap 1 /
  host-wide cap 6) stayed continuously saturated with no free token, before eventually clearing. Not a defect in the
  shipped change — flagged as a monitoring/capacity question: is cap=6 undersized for current fleet size, or was this
  an unusual peak (many slots landing work around the same time)?
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer, admin]
tags: [qg-governor, host-concurrency, quality-gates, capacity, observability]
related: [/plans/active/infra_consolidated_closeout_2026_07_25.md]
created: 2026-08-16
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
resolved_by:
source: >-
  slot-22 (data_engineering), 2026-08-16: observed while shipping
  defi_satellite_ao_dispatch_batch11_2026_08_09.md's BLAZESTAKE lst_rates reclassify todo — a completely unrelated,
  single-file change, no reason to expect an unusual gate.
context_scope: [/codex/06-coding-standards/quality-gates.md]
---

## What I found

Running `bash scripts/quality-gates.sh --no-fix` for `market-tick-data-service` (and again inside quickmerge's own
auto re-gate after an unrelated rebase) produced this log pattern, repeated every 30s with no other output in between:

```
[qg-governor] total-instance tokens busy (market-tick-data-service sub-cap 1 / host-wide cap 6) — queued 30s
...
[qg-governor] total-instance tokens busy (market-tick-data-service sub-cap 1 / host-wide cap 6) — queued 1920s
```

Two separate invocations sat in this exact state continuously: one for ~32 minutes (1920s+) before its background
task was reaped, the next for ~11.5 minutes before it happened to acquire a token and complete normally (full
`quality-gates.sh` run then took ~470s once it got a slot — matches the documented baseline). A live `ps aux` during
the wait showed 10+ concurrent `bash scripts/quality-gates.sh` processes across many different slots (17, 20, 24, 26,
27, 30, 33, ...) all either running or themselves queued at the governor — genuine fleet-wide load, not a hung
process (the process I was tracking stayed alive, in its own `sleep 1`-poll wait loop, the whole time).

## Why it matters

- The shipping task itself was trivial (one new file, no dependencies changed) — the QG wait dominated the session's
  wall-clock cost by an order of magnitude (30-45 min of queueing vs. ~8 min of actual gate work).
- If this is routine at current fleet size, `host-wide cap 6` may be undersized relative to how many slots now run
  concurrently, and every worker pays this tax on every ship.
- Equally possible this was a load SPIKE (many slots landing work in the same window) rather than a standing problem —
  I did not capture governor occupancy at a calmer time to compare, so I can't distinguish undersized-cap from
  normal-peak-contention from this session alone.

## Recommended decision

Not urgent enough to block on — filed as a P3 investigation, not a fix-now item. Whoever picks this up should:

1. Sample `[qg-governor] ... queued Ns` wait durations across a normal week (not just this one incident) to establish
   a baseline distribution, not just this one 30-45 min data point.
2. If sustained, consider raising `host-wide cap` (check current sizing rationale first — it may already be tuned to
   available host RAM/CPU, in which case the fix is host resources, not the cap number) or spreading QG-heavy work
   more evenly across the fleet's dispatch cadence.

## Todos

- [ ] [SCRIPT] P3. **Sample QG-governor queue-wait durations over a representative week** (not a one-off incident) and
      compare against the host's RAM/CPU budget that sized `host-wide cap 6` in the first place, to determine whether
      the cap is undersized for current fleet concurrency or this session's 30-45 min waits were an unusual peak.
      Repo: unified-trading-pm (governor script lives under
      `scripts/quality-gates-base/base-service.sh`). Done when: a dated finding states either "cap is adequately
      sized, this was peak contention" or "cap should be raised to N, here's why" with supporting samples.
