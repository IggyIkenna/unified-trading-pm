---
doc_type: issue
title: Local dev Mac hit load 308 — six slots gating concurrently, serial-gate rule violated, swap 97% full
summary: >-
  Measured 2026-08-14/15 on the operator's Mac (Mac.mynet, 10 cores, 24 GiB physical + 25 GiB swap). Six slots were
  running quality-gates.sh simultaneously — .tabs/3 alone running THREE repos at once — which violates the workspace
  rule that gate+ship stay SERIAL and parallelise authoring only. Swap reached 97% used (24.8 of 25.6 GB), which is what
  produced a load average of 308: not raw CPU demand but page-fault thrashing, since macOS counts uninterruptible
  threads in load. The QG governor SIGTERM'd a legitimate ship twice. At least one session was already running with
  IGNORE_TIMEOUT=true, meaning sessions are overriding the resource guard rather than backing off, which compounds it.
  Distinct from fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27 — that is CI runners, this is the laptop.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, host-concurrency, contention, developer-experience]
related:
  [
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /codex/06-coding-standards/quality-gates.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
    /plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md,
  ]
created: "2026-08-15"
last_updated: 2026-08-15
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
assigned_role: infra
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: measured while shipping /plans/archive/2026_08/revocation_arming_2026_08_14.md
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /codex/06-coding-standards/quality-gates.md,
    unified-trading-pm/scripts/quality-gates-base/qg-host-governor.sh,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
  ]
---

# Local host: six concurrent quality gates, load 308

## What was measured

Host: `Mac.mynet`, **10 cores**, **24 GiB physical + 25 GiB swap**.

At the peak, `quality-gates.sh` was running in **six slots simultaneously**:

| Slot           | Repos gating concurrently                                                          |
| -------------- | ---------------------------------------------------------------------------------- |
| `.tabs/3`      | **three at once** — features-service, instruments-service, unified-trading-library |
| `.tabs/1`      | agent-orchestrator                                                                 |
| `.tabs/5`      | deployment-service                                                                 |
| `.tabs/6`      | agent-orchestrator                                                                 |
| `.ao-iso-ship` | AO's isolated ship worktree (×2)                                                   |

**Swap was 97% full** — 24.8 GB used of 25.6 GB, 794 MB free. That is the actual mechanism behind `load average: 308`:
not CPU demand but page-fault thrashing, because macOS counts uninterruptible threads in the load figure. Each gate runs
pytest-xdist plus basedpyright, so ~7 gates × ~10 workers is ~70 processes against 10 cores with no memory headroom.

## Why it matters

- The QG governor SIGTERM'd a **legitimate, content-green ship twice**. quickmerge correctly reported it ("Re-gate hit
  ONLY the duration budget — every content check passed. This is HOST CONTENTION, not your change"), but each abort
  still cost a ~10-minute gate cycle.
- **At least one session was running with `IGNORE_TIMEOUT=true`** (slot 3, 38 minutes elapsed). That is the sanctioned
  escape hatch for exactly this condition — so sessions are hitting the wall and overriding rather than backing off,
  which makes the contention worse for everyone else.
- The governor admits by measured RSS against live RAM under one ledger lock, but a run **already admitted** that then
  swaps is not re-evaluated, and `IGNORE_TIMEOUT` removes the duration budget that would otherwise abort it. So the two
  mechanisms that should bound this can both be in effect and still allow the observed state.

## The rule this contradicts

`/codex/12-agent-workflow/host-concurrency-and-commit-provenance.md` §5 and CLAUDE.md are explicit: **parallelise
AUTHORING ONLY — gate+ship stay SERIAL**. One slot running three repos' gates concurrently is a direct violation, and is
the single largest contributor measured here.

## Todos

- [ ] [CODE] P1. Make the serial-gate rule enforceable rather than advisory on a single host: the governor should refuse
      (or queue) a second concurrent `quality-gates.sh` from the SAME slot outright, since that case has no legitimate
      reading — the rule permits parallel authoring, never parallel gating. Repo: unified-trading-pm.
- [ ] [CODE] P1. Re-evaluate admitted runs under sustained swap pressure, not only at admission. A run admitted when RAM
      looked fine and then thrashing for 38 minutes is the shape that produced this. Repo: unified-trading-pm.
- [ ] [CODE] P2. Make `IGNORE_TIMEOUT=true` observable — log who set it and why, so override frequency is measurable. If
      sessions routinely need it, the budget is wrong; if they use it to skip queueing, that is worth seeing. Repo:
      unified-trading-pm.
- [x] ✅ [DOC] P2. Extracted to `cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md` item 10 (na-eligibility-audit 2026-08-17). Record the swap-thrash signature in the quality-gates codex: a load average in the hundreds on this host
      means swap exhaustion, not CPU saturation, and the correct response is to WAIT rather than retry or override.
      Repo: unified-trading-pm.
- [ ] [DOCS] P2. Per D91 ruling (2026-08-22): document the ceiling first; consider RAM only if the queueing/serial-gate
      fixes above don't reduce contention enough on their own. Document the practical concurrent-QG-gate ceiling for
      this host (Mac.mynet, 10 cores / 24 GiB physical + 25 GiB swap) in the quality-gates codex. Repo:
      unified-trading-pm.
- [ ] [CODE] P1. **The per-repo sub-cap queue starves the oldest waiter — it is not FIFO.** Measured 2026-08-15 10:40:
      four distinct `quality-gates.sh` runs on `unified-api-contracts` (sub-cap 1) from `.tabs/4` (×2 sessions — the
      shared-slot case), `.tabs/1` and the root checkout. The run that had waited **36:49** was still printing `queued`,
      while runs aged 1:42, 5:01 and 10:12 were admitted ahead of it. A waiter that can be overtaken indefinitely has no
      bound on its wait, which is a different defect from the host being busy: adding RAM would not fix it. Give the
      ledger FIFO ordering (or aging), so wait time is bounded by queue depth rather than by luck. Repo:
      unified-trading-pm.

## Evidence

- `sysctl vm.swapusage` → `total = 25600.00M  used = 24805.50M  free = 794.50M`.
- `uptime` → `load averages: 308.27 253.45 200.18`, decaying to 29.81 once gates finished.
- Slot attribution via `lsof -a -p <pid> -d cwd` over every `pgrep -f 'bash scripts/quality-gates.sh'` match.
- **Counting caveat worth repeating**: a bare `ps aux | grep -c` over-counts — it catches parent shells, nested children
  and the grep's own wrapper. The honest figure was ~7 distinct runs, not the 10 first reported.

## Progress Log

- **context-scout 2026-08-17**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-17** [body-hash:a9ed035183a85708]: RECLASSIFY (per-todo split) -- extracted the 1 bounded item (record the swap-thrash signature in the quality-gates codex) to cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md item 10. Doc stays assigned_vm: NA for its remaining items. Cross-cutting tranche audit.
- **2026-08-22 — ruling D91 (Mac host QG concurrency)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Document the ceiling first; consider RAM only if queueing fixes don't reduce
  contention. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
