---
doc_type: plan
title: QG governor — cross-repo ledger coordination on GHA glue-runner hosts
summary: >-
  The reservation-ledger admission governor (qg_host_adaptive_resource_governor_2026_07_14.md) is shipped and validated
  on the interactive slot-worktree topology, but does NOT coordinate across different repos' CI jobs on a GitHub Actions
  self-hosted glue-runner host — each repo's job resolves its own isolated ledger, so N repos' quality-gates.sh can pile
  onto one physical host with no shared admission control. Confirmed live 2026-08-02 (10 repos, load average 42-43, one
  16-core/61GB host). This plan forks that flagged-but-unscoped gap (parent plan's 2026-08-02 entry, open P1 todo, block
  ticket BLK-7eedce54) into its own scoped fix — design, implement, validate, roll out.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, quality-gates, ci, self-hosted-runners, host-contention, governor, glue-runner, resource-admission]
related:
  [
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-08-03"
last_updated: 2026-08-03
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "plans/active/qg_host_adaptive_resource_governor_2026_07_14.md § 2026-08-02 LIVE finding",
    "cicd escalation agt-fea289",
    "block ticket BLK-7eedce54",
  ]
context_scope:
  [
    /codex/06-coding-standards/quality-gates.md,
    scripts/quality-gates-base/qg-host-governor.sh,
    plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
  ]
---

# QG governor — cross-repo ledger coordination on GHA glue-runner hosts

> **LOCAL / operator-driven plan** (`assigned_vm: NA`) — not AO-ingested. Forked out of
> `qg_host_adaptive_resource_governor_2026_07_14.md`'s 2026-08-02 finding per that doc's own note: "a one-shot
> wall-clearing task is the wrong place to redesign ledger scoping across the whole glue-runner fleet — real blast
> radius (every repo's CI), needs its own scoped plan/PR + a fleet soak on the GHA topology specifically."

## Codex SSOTs (read + keep aligned)

- `/codex/06-coding-standards/quality-gates.md` § the governor's dual-gate model (🟢 LIVE + VALIDATED banner) — this
  plan extends it to a second topology, doesn't replace it.
- `scripts/quality-gates-base/qg-host-governor.sh` — `_qg_shared_root()` is the exact function this plan changes; the
  reservation ledger primitives (`_qg_ledger_add`/`_remove`/`reserved_mb`), the dual-gate admission (`_qg_admit_check`),
  and the cgroup cap / 80% valve / watchdog it feeds are all UNCHANGED by this plan — only ledger-path resolution
  changes.
- `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md` — the parent plan. Phases 0-6 shipped + validated on
  the interactive slot-worktree topology (93-min soak, 0 OOM, cross-host admission tests 16-128 GB). Its 2026-08-02
  Progress Log entry is the full root-cause writeup this plan implements the fix for.
- `plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` +
  `.../fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` — the still-open, days-long incident this fix should
  materially reduce once live. Both currently `status: open`; the day-2 doc is at 999/1000 lines (near its hard cap)
  from continuous per-repo firefighting (`PYTEST_TIMEOUT`/`PYRIGHT_TIMEOUT` raises) that treats symptoms, not this root
  cause.

## Problem

`_qg_shared_root()` resolves the reservation ledger's directory from `WORKSPACE_ROOT`, stripping the per-slot
`/.tabs/<N>` suffix — correct for the interactive slot-worktree topology (every slot on one host lands on the same
shared parent). On a GHA self-hosted glue-runner host, a job's cwd is
`/opt/github-glue-runners-<repo>/glue-N/_work/<repo>/<repo>` — there is no `.tabs/` segment, and `WORKSPACE_ROOT` is
**not** a shared value across different repos' runner jobs on the same physical host (it's per-repo-job). So each repo's
CI job resolves its own isolated ledger, scoped to its own runner workdir, and admits against its own private view of
the host's RAM/CPU budget as if it owned the whole machine.

**Confirmed live, 2026-08-02** (investigating a red `unified-api-contracts` `quality-gates-v2` run, `cicd` escalation
`agt-fea289`): on glue-runner host `ip-172-31-5-118` (16-core/61GB), **~10 different repos'** `quality-gates.sh` were
running concurrently — `unified-trading-api`, `unified-api-contracts`, `fund-administration-service`, `ml-service`,
`execution-service`, `strategy-service`, `market-tick-data-service`, `batch-live-reconciliation-service`,
`deployment-service`, `alerting-service` — `load average ~42-43`, heavy swap thrashing (`vmstat` si/so ~20-40 MB/s)
despite 26-40GB RAM nominally free (a CPU/swap oversubscription the RAM-percentage gate alone can't see). Each repo's
ledger was independently near-empty — none of them saw the other nine.

This is the direct mechanism behind the fleet-wide QG capacity crisis that's been active since 2026-07-27 and is still
ongoing today (2026-08-03) — the shared-host admission control the parent plan built and validated **provides no
protection at all on the machine class that actually runs CI**, only on interactive dev VMs.

## Goal

Make the reservation ledger (unchanged internals — same admit/reserve/release, same RAM+CPU dual-gate, same cgroup cap +
80% valve + watchdog) resolve to **one shared path per physical glue-runner host**, regardless of which repo's job is
running, without breaking the existing slot-worktree resolution or accidentally merging ledgers **across** different
hosts (which would silently corrupt the whole budget model — each host's RAM/CPU budget is a property of that host).

## Design — three candidate shared-root strategies (decide in Phase 0)

1. **Stable `/opt/github-glue-runners-*` parent.** Derive the shared root one level up from the per-repo runner
   directory (e.g. `/opt/github-glue-runners-shared/.benchmarks/qg-governor/`). Simple, no new provisioning step — but
   requires confirming every glue-runner host actually uses this exact parent-directory shape (verify, don't assume from
   one host's observed layout).
2. **Host-identity env var set at runner-install time.** A `QG_HOST_ID` written once when a runner is provisioned, read
   by every runner service on that host. Most explicit, but couples this fix to a runner-provisioning change — a host
   bootstrapped before this ships would silently fall back to the broken per-repo-job path unless retrofitted.
3. **Host machine-id.** `/etc/machine-id` on Linux (or the instance id via cloud metadata) — always available with zero
   new provisioning coupling, host-unique by construction, works identically whether the caller is a slot-worktree
   session or a glue-runner job (could plausibly unify both resolution paths into one, rather than branching on
   topology).

No strategy is pre-selected — Phase 0 decides, with the actual verification each option's tradeoff above depends on
(don't pick (1) or (2) without checking the stated caveat first).

## Phases + todos

### Phase 0 — Confirm topology + decide the resolution strategy

- [ ] [INFRA] P0. Enumerate the actual directory layout on at least 2-3 different glue-runner hosts (not just the one
      observed 2026-08-02) — `ls /opt/ | grep github-glue-runners` (or equivalent) per host — to confirm whichever
      strategy is picked below actually generalizes, not just fits the one host already seen. Gate: a recorded layout
      sample from ≥2 hosts in this plan's Progress Log.
- [ ] [INFRA] P0. Decide the shared-root resolution strategy (one of the 3 above, or a combination) and record the
      decision + reasoning in this plan's Progress Log before writing any code — this is a real design choice, not a
      mechanical follow-on.

### Phase 1 — Implementation (additive, flag-gated — mirrors the parent plan's own rollout discipline)

- [ ] [INFRA] P1. Extend `_qg_shared_root()` in `scripts/quality-gates-base/qg-host-governor.sh` to detect the
      glue-runner topology and resolve the chosen host-shared path — additive only, so a host not yet on the new path
      keeps its exact current (broken-but-unchanged) behavior until explicitly cut over. Gate: `shellcheck` clean + the
      function's existing test harness pattern extended, not replaced.
- [ ] [INFRA] P1. Fixture-based unit tests (no live-host dependence, same style as `qg_host_capacity`'s tests): assert
      two DIFFERENT simulated repos' runner workdirs on the SAME simulated host resolve to the identical ledger path,
      and that two simulated DIFFERENT hosts never collide. Gate: new test file green, all existing governor test suites
      (5, per the parent plan) still green — zero regression on the slot-worktree path.

### Phase 2 — Live validation on the actual glue-runner topology

- [ ] [INFRA] P1. On one glue-runner host, trigger ≥2 different repos' `quality-gates-v2` runs concurrently (or manually
      exercise `qg-host-governor.sh --status`/acquire calls from two repo checkouts on the same host if a live
      concurrent CI trigger isn't practical) and confirm both resolve to the SAME ledger directory with combined
      reservations visible to both. Gate: a `--status` read from repo A showing repo B's live reservation.
- [ ] [INFRA] P1. A sustained soak on the GHA topology specifically — the parent plan's 93-min soak only covered the
      slot-worktree topology; this is a genuinely different failure surface (cross-repo, not cross-slot). Target a
      comparable duration (~90min+) with multiple real repos' CI landing on the same host, watching for 0 OOM, no false
      80% aborts, and admission actually gating once the combined reservation approaches budget. Gate: a dated soak
      summary in this plan's Progress Log with the same shape as the parent plan's 2026-07-14 soak entry (run count,
      maxconc, OOM count, any ghost-reservation lingers).

### Phase 3 — Rollout + close the loop

- [ ] [INFRA] P1. Flip the glue-runner shared-root resolution live across the glue-runner fleet, coordinating timing so
      the cutover itself doesn't collide with whatever firefighting is active in
      `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` (or its day-3 successor) at the time. Gate:
      `qg-host-governor.sh --status` on ≥3 different glue-runner hosts post-flip, each showing the new shared-root path
      in use.
- [ ] [INFRA] P2. Update `/codex/06-coding-standards/quality-gates.md` to note the glue-runner topology is now covered
      (mirrors the parent plan's own 🟢 LIVE + VALIDATED banner update pattern). Close the parent plan's 2026-08-02 todo
      (`_qg_shared_root()` glue-runner fix) by pointing it at this plan's completion, and close block ticket
      `BLK-7eedce54`.
- [ ] [INFRA] P2. Once live + soaked, check whether `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` and
      its day-2 continuation can be marked resolved (or at minimum banner a material-improvement note with a
      before/after escalation-rate comparison) — this fix directly targets their root cause, so their own resolution
      should follow, not be assumed automatically.

## Progress Log

### 2026-08-03 — Plan authored (interactive session)

- Authored in direct response to investigating this morning's CI-failure Slack-alert burst (~13+ alerts, 8:19-9:25
  local) across 9 repos — root-caused the bulk of it to this exact gap via the parent governor plan's own 2026-08-02
  entry, which had already diagnosed but explicitly deferred the fix ("needs its own scoped plan/PR"). This plan is that
  fork. No code changed yet — Phase 0 is the next actionable step.
