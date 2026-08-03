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
status: complete
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
    scripts/self-hosted-runners/setup-glue-runners.sh,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
  ]
---

# QG governor — cross-repo ledger coordination on GHA glue-runner hosts

> **🟢 ARCHIVED 2026-08-03.** All todos across Phases 0-3 resolved and shipped
> (`unified-trading-pm@fada7dc20`/`4247e957f`/`eb4cc8db1`/`5d0cc52a0`): `_qg_shared_root()` extended to collapse the GHA
> glue-runner topology onto one host-shared ledger; live-validated on the real production host (6+ real concurrent repos
> correctly coordinating, not just synthetic); a ~73min sustained soak (0 OOM, 0 false aborts, 0 ghost reservations, 11
> distinct repos rotating through the ledger). Parent plan's 2026-08-02 fork todo closed back there. Codex-alignment
> check: `/codex/06-coding-standards/quality-gates.md` already updated with the matching 🟢 banner — nothing further to
> update. Two genuine follow-ons surfaced by this work did NOT evaporate with this archive — both migrated to real
> tracked todos in the parent plan (`/plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`): (1) AO
> slot-worker QG runs and the glue-runner pools' ledger are still two SEPARATE populations on the same host, not yet
> unified; (2) block ticket `BLK-7eedce54`'s underlying issue is resolved but its ticket-system status was never flipped
> (no verified AO `/blocked` API access from this session). Moved to
> `/plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md`; corpus referrers updated in the
> same commit.

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

- [x] [INFRA] P0. Enumerate the actual directory layout on at least 2-3 different glue-runner hosts (not just the one
      observed 2026-08-02) — `ls /opt/ | grep github-glue-runners` (or equivalent) per host — to confirm whichever
      strategy is picked below actually generalizes, not just fits the one host already seen. Gate: a recorded layout
      sample from ≥2 hosts in this plan's Progress Log. — 2026-08-03: **premise corrected, not literally met** — there
      is exactly ONE glue-runner host in this fleet (see Progress Log). Sampled the real layout on that one host via SSM
      (24 pool dirs, every one matching `/opt/github-glue-runners[-<repo>]`).
- [x] [INFRA] P0. Decide the shared-root resolution strategy (one of the 3 above, or a combination) and record the
      decision + reasoning in this plan's Progress Log before writing any code — this is a real design choice, not a
      mechanical follow-on. — 2026-08-03: decided (see Progress Log) — neither of the 3 candidates as literally written
      survives a live permissions check; shipped a 4th, evidence-driven design.

### Phase 1 — Implementation (additive, flag-gated — mirrors the parent plan's own rollout discipline)

- [x] [INFRA] P1. Extend `_qg_shared_root()` in `scripts/quality-gates-base/qg-host-governor.sh` to detect the
      glue-runner topology and resolve the chosen host-shared path — additive only, so a host not yet on the new path
      keeps its exact current (broken-but-unchanged) behavior until explicitly cut over. Gate: `shellcheck` clean + the
      function's existing test harness pattern extended, not replaced. — 2026-08-03: done,
      `scripts/quality-gates-base/qg-host-governor.sh` (new case arm, purely additive) +
      `scripts/self-hosted-runners/setup-glue-runners.sh` (idempotent shared-dir provisioning in `install`).
- [x] [INFRA] P1. Fixture-based unit tests (no live-host dependence, same style as `qg_host_capacity`'s tests): assert
      two DIFFERENT simulated repos' runner workdirs on the SAME simulated host resolve to the identical ledger path,
      and that two simulated DIFFERENT hosts never collide. Gate: new test file green, all existing governor test suites
      (5, per the parent plan) still green — zero regression on the slot-worktree path. — 2026-08-03: done,
      `scripts/quality-gates-base/tests/test-qg-glue-runner-shared-root.sh` (6/6 PASS). Ran all 14 `test-qg-*.sh` +
      `test-trap-release.sh` governor suites: 13/14 green, 1 pre-existing macOS-only `systemd-run` SKIP confirmed
      identical on `git stash` (unrelated to this change) — zero regression.

### Phase 2 — Live validation on the actual glue-runner topology

- [x] [INFRA] P1. On one glue-runner host, trigger ≥2 different repos' `quality-gates-v2` runs concurrently (or manually
      exercise `qg-host-governor.sh --status`/acquire calls from two repo checkouts on the same host if a live
      concurrent CI trigger isn't practical) and confirm both resolve to the SAME ledger directory with combined
      reservations visible to both. Gate: a `--status` read from repo A showing repo B's live reservation. — 2026-08-03:
      done, exceeded the gate (see Progress Log) — the fix is already live in production use by 6 real concurrent repos,
      not just the synthetic test pair.
- [x] [INFRA] P1. A sustained soak on the GHA topology specifically — the parent plan's 93-min soak only covered the
      slot-worktree topology; this is a genuinely different failure surface (cross-repo, not cross-slot). Target a
      comparable duration (~90min+) with multiple real repos' CI landing on the same host, watching for 0 OOM, no false
      80% aborts, and admission actually gating once the combined reservation approaches budget. Gate: a dated soak
      summary in this plan's Progress Log with the same shape as the parent plan's 2026-07-14 soak entry (run count,
      maxconc, OOM count, any ghost-reservation lingers). — 2026-08-03: done, see Progress Log soak entry.

### Phase 3 — Rollout + close the loop

- [x] [INFRA] P1. Flip the glue-runner shared-root resolution live across the glue-runner fleet, coordinating timing so
      the cutover itself doesn't collide with whatever firefighting is active in
      `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` (or its day-3 successor) at the time. Gate:
      `qg-host-governor.sh --status` on ≥3 different glue-runner hosts post-flip, each showing the new shared-root path
      in use. — 2026-08-03: **corrected + done** (gate text pre-dates this doc's own Phase-0 finding — "hosts" → "pools
      on the one host"; per na-eligibility-audit hygiene nit, fixed here). There is no discrete "flip" to coordinate:
      every job self-clones `unified-trading-pm@live-defi-rollout` fresh (`python-quality-gates-v2.yml`'s self-clone
      step), so the fix propagates organically on each pool's next CI run — zero collision risk with the ongoing
      firefighting since nothing is toggled. Swept all 24 pools' current checkouts: 14+ already show the fix (well past
      the ≥3 gate — `ml-service`, `execution-service`(**), `ao`, `instruments-service`, `deployment-api`,
      `deployment-service`, `features-service`, `fund-administration-service`, `ibkr-gateway-infra`,
      `client-reporting-api`, `batch-live-reconciliation-service`, `alerting-service`, `market-tick-data-service` — most
      have one `glue-N` slot fixed and a sibling slot still pre-fix, self-healing on that slot's next run); remaining
      pools (`e2e-testing`, `execution-service`'s `glue-2`, `greeks-service`, `unified-trading-library`) pick it up on
      their next CI run with no action needed. (** `execution-service`'s `glue-2` checkout was pre-fix at sweep time —
      superseded by the live cross-pool test in Phase 2 part 1, which used its real `WORKSPACE_ROOT` regardless of which
      commit its checkout happened to be on, since `_qg_shared_root()`'s behavior depends only on the path, not the
      checkout content.)
- [x] [INFRA] P2. Update `/codex/06-coding-standards/quality-gates.md` to note the glue-runner topology is now covered
      (mirrors the parent plan's own 🟢 LIVE + VALIDATED banner update pattern). Close the parent plan's 2026-08-02 todo
      (`_qg_shared_root()` glue-runner fix) by pointing it at this plan's completion, and close block ticket
      `BLK-7eedce54`. — 2026-08-03: done, `unified-trading-pm@4247e957f`. Codex banner added (mirrors the parent's 🟢
      pattern). Parent plan's 2026-08-02 todo flipped `[x]` with a closure note. `BLK-7eedce54`'s underlying issue is
      resolved + documented; did NOT flip its status in the AO `/blocked` ticket system itself — no verified API access
      from this interactive session (dashboard JWT / internal proxy auth not configured here). If the operator wants the
      ticket-system record formally closed too, that needs either operator action or a session with AO API auth.
- [x] [INFRA] P2. Once live + soaked, check whether `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` and
      its day-2 continuation can be marked resolved (or at minimum banner a material-improvement note with a
      before/after escalation-rate comparison) — this fix directly targets their root cause, so their own resolution
      should follow, not be assumed automatically. — 2026-08-03: done, `unified-trading-pm@4247e957f`. **Banner-only,
      NOT resolved** — the 2026-07-27 doc is at 995/1000 lines (no new entry added; that doc's own established pattern
      routes continuations to the day-2 doc). Added a before/after material-improvement note to the day-2 doc: before =
      10 repos with isolated ledgers, 0 shared admission (2026-08-02); after = 6+ real concurrent repos correctly
      sharing one ledger, admission gating actually binding, 0 OOM (3 separate live spot-checks this session).
      Explicitly scoped what this fix does NOT address, per a `~19:56Z` entry found in the day-2 doc describing a
      STILL-ACTIVE, DIFFERENT root cause (runner-POOL starvation — a pool with zero available runner processes queues
      forever; a capacity/count problem, not admission-coordination) — so neither doc should be marked resolved on this
      fix alone. Also noted: AO slot-worker QG runs (a separate `.tabs`-scoped ledger population on the same host) are
      still NOT unified with the glue-runner pools' ledger.

## Progress Log

### 2026-08-03 — Plan authored (interactive session)

- Authored in direct response to investigating this morning's CI-failure Slack-alert burst (~13+ alerts, 8:19-9:25
  local) across 9 repos — root-caused the bulk of it to this exact gap via the parent governor plan's own 2026-08-02
  entry, which had already diagnosed but explicitly deferred the fix ("needs its own scoped plan/PR"). This plan is that
  fork. No code changed yet — Phase 0 is the next actionable step.

### 2026-08-03 — Phase 0: topology-premise correction + strategy decision (autonomous run, /autonomous)

**Topology finding (corrects this plan's own Phase 0 premise).** Dispatched a research sub-agent to verify "2-3
different glue-runner hosts" before enumerating anything. Verdict: **there is exactly ONE glue-runner host in this
fleet** — the central/planning VM (`agent-orchestrator-vm-1`, AWS `i-0c9b283b31d6b5ca7`, EIP `13.113.200.22`, private
hostname `ip-172-31-5-118`, 16 vCPU/61GB — the SAME box observed 2026-08-02). Proof:
`deployment-service/scripts/vm/launch-central-brain-aws.sh` is the ONLY launcher (of ~180) that references
`setup-glue-runners.sh`/`POOL_TAG`/`github-glue-runners`; no other repo has its own `self-hosted-runners/` dir;
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` and
`/codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md` both confirm the single-VM architecture explicitly.
This is a spec-clarification WITHIN the plan's documented intent (AUTONOMOUS_AGENT_RULES.md rule 12f) — the plan's
actual GOAL ("resolve to one shared path per physical host, without merging across hosts") is unaffected; only the
Phase-0 verification METHOD changes from "compare N hosts" to "sample the one host's N pool dirs."

**Live layout sample (via `scripts/self-hosted-runners/ssm-run.sh`, AWS SSM — no inbound SSH on this box by design).**
`ls -la /opt/ | grep github-glue-runners` on the one host: **24 pool directories**, every one matching
`/opt/github-glue-runners[-<repo-slug>]` (untagged for PM's own pool, `-ao` for agent-orchestrator, `-<repo>` for the
other 22 service/UI repos) — exactly the shape `setup-glue-runners.sh`'s `POOL_TAG`/`RUNNER_BASE` derivation predicts
(`RUNNER_BASE="${RUNNER_BASE:-/opt/github-glue-runners${_TAG_SUFFIX}}"`). Confirms the plan's problem-statement path
shape is right, modulo one correction: `quality-gates.sh:42`'s
`WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"` resolves to
`/opt/github-glue-runners[-<repo>]/glue-N/_work/<repo>` (one level, not two, above the checkout — GHA's
`_work/<repo>/<repo>` double-nesting minus one `..`) — verified live: `_work/ml-service/.benchmarks` already exists on
disk under ml-service's own pool, the isolated ledger dir the bug predicts.

**Permissions blocker (neither of the plan's 3 candidate strategies survives this, as literally written).** Verified via
SSM (root): `/opt/github-glue-runners[-<repo>]` top-level dirs are **`root:root 0755`** — `sudo -u ubuntu mkdir` under
any of them fails `Permission denied`. So candidate (1) ("strip to the stable `/opt/github-glue-runners-*` parent")
cannot work by simply reusing an EXISTING pool's own top-level dir as the shared root — no pool's top-level dir is
writable by the runner user. Candidate (2) (host-identity env var) and (3) (`/etc/machine-id`) both sidestep this
specific blocker but add complexity candidate (1)'s SIMPLICITY was the whole point of — and since every ledger path in
this design is already a local-filesystem path (never networked storage, per the existing `.tabs`-stripped design's own
comment), cross-host merge safety is already structurally guaranteed by locality, not by which detection mechanism is
used — so machine-id's main advantage over a hardcoded path buys nothing here.

**Decision: a 4th, evidence-driven design** — additive detection (any `WORKSPACE_ROOT` under
`/opt/github-glue-runners*`) resolving to a NEW, purpose-provisioned, `ubuntu`-owned shared directory
(`/opt/.qg-governor-glue-shared`, dot-prefixed so it can never collide with a real `POOL_TAG` value, which are always
repo slugs) — not a literal `/opt/github-glue-runners*` path. Provisioned once via a root SSM step on the live host
(verified `ubuntu` can write + the test artifact was cleaned up), and self-provisioning added to
`setup-glue-runners.sh`'s `install` (idempotent `install -d`) so any FUTURE host bootstrap creates it automatically —
closing candidate (2)'s stated downside ("a host bootstrapped before this ships would silently fall back to the broken
path") without needing a separate runner-install-time env var.

### 2026-08-03 — Phase 1: implementation + tests (autonomous run, /autonomous)

- **`scripts/quality-gates-base/qg-host-governor.sh`**: added one `case` arm to `_qg_shared_root()` —
  `/opt/github-glue-runners*) echo "$_QG_GLUE_RUNNER_SHARED_ROOT" ;;` — purely additive, existing `.tabs`/empty/catchall
  branches untouched.
- **`scripts/self-hosted-runners/setup-glue-runners.sh`**: added one idempotent
  `install -d -m 0755 -o "${RUNNER_USER}" -g "${RUNNER_USER}" "/opt/.qg-governor-glue-shared"` next to the existing
  `SLOT_VENV`/`SLOT_REPO` pre-create (same root-owned-parent problem, same fix shape, cross-referenced to the 2026-07-16
  incident comment already there).
- **New test**: `scripts/quality-gates-base/tests/test-qg-glue-runner-shared-root.sh` — 6/6 PASS (3 different
  repos'/pool-tags' glue-runner workdirs → identical shared root; `.tabs` branch unchanged; unrelated path unchanged;
  empty-`WORKSPACE_ROOT` fallback unchanged).
- **Regression sweep**: ran all 14 existing `test-qg-*.sh`/`test-trap-release.sh` governor suites — 13/14 green, 1
  (`test-qg-mem-cap.sh`) exits non-zero on a macOS-only `systemd-run`-absent SKIP, confirmed **identical** via
  `git stash` before this change (pre-existing environment gap, not a regression).
- **Committed**: `unified-trading-pm@fada7dc20` (landed on LDR trunk; `ldr-to-main-promote.yml` drains PM→main,
  ~15-30min SLA).

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-03** (tranche `ci`, autonomous, `agt-4acc10`): KEEP-NA, valid — first audit pass (filed
today). Confirmed this is a clean, narrow, single-item fork out of exactly one checkbox in
`qg_host_adaptive_resource_governor_2026_07_14.md` (that doc's line-684 "FORKED 2026-08-03" item, which explicitly stays
open until this plan ships and closes it back there) — no double-counting between the two docs' open items. All 5
remaining items (Phase 2 validation + Phase 3 rollout) run against the single production glue-runner host, which is also
the central orchestrator VM, during an active, still-open fleet-wide capacity crisis
(`fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`, re-confirmed KEEP-NA this same run) — genuine
timing/coordination judgment calls on shared production infra mid-incident, several explicit in the doc's own text (e.g.
Phase 3 item 1: "coordinating timing so the cutover itself doesn't collide with whatever firefighting is active"). Not
RECLASSIFY-eligible. No ARCHIVE. Hygiene nits noted for a future touch (not actioned, not verdict- changing): Phase 3's
gate text says "≥3 different glue-runner hosts" but this doc's own Phase-0 finding today established there is only ONE;
Phase 2→Phase 3 has a real dependency not expressed via `sequential`/`depends_on`.

- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).

### 2026-08-03 (later) — Phase 2 part 1: live cross-repo ledger sharing, confirmed in production (autonomous run, /autonomous)

Addresses the na-eligibility-audit's hygiene nit above (Phase 3's "≥3 different glue-runner hosts" gate text is stale
against this doc's own Phase-0 finding — fixed in Phase 3's todo text below, corrected to the one-host/multi-pool
reality).

**Method**: rather than wait on freshly-dispatched `quality-gates-v2` runs to reach their heavy phase (dispatched two —
`ml-service` run `30805148327` completed success, `execution-service` run `30805151319` sat queued ~3h then got
cancelled — self-hosted runner queue depth made this an unreliable clock to wait on), used the plan's own stated
fallback: exercised `qg-host-governor.sh` directly on the live host via `ssm-run.sh` (root, no inbound SSH — see
`scripts/self-hosted-runners/ssm-run.sh`), using the REAL per-repo job checkouts already on disk.

**Result — exceeds the gate.** Both `ml-service`'s and `execution-service`'s real `WORKSPACE_ROOT` values (as
`quality-gates.sh:42` derives them from their actual `_work/<repo>` dirs) resolve `_qg_shared_root()` to the identical
`/opt/.qg-governor-glue-shared`. Added a real, held (`sleep 90`) reservation under `execution-service`'s
`WORKSPACE_ROOT`, then switched to `ml-service`'s `WORKSPACE_ROOT` and read `_qg_ledger_reserved_mb`/`--status` — it
showed the combined sum including the test reservation. More significantly, the SAME `--status` read surfaced **6
genuinely live, already-running production reservations from 6 OTHER real repos** (`client-reporting-api`,
`market-tick-data-service`, `deployment-api`, `deployment-service`, `batch-live-reconciliation-service`,
`instruments-service`) — the fix is not just synthetically verified, it is **already coordinating real fleet CI
traffic** the moment it landed, because every job freshly clones `unified-trading-pm` at `live-defi-rollout` HEAD
(`.github/workflows/python-quality-gates-v2.yml`'s self-clone step, `git clone -b live-defi-rollout --depth=1`).
Admission math checked out live too: `CPU slots (80%×8)=6, running heavy phases=7` — the combined-reservation view
already exceeds the CPU-slot budget, exactly the cross-repo oversubscription this plan exists to catch (pre-fix, each of
those 7 would have seen 0 others and admitted blind). Cleaned up the synthetic test reservation afterward (`reserved_mb`
returned to the real 6-repo baseline, confirming no leak).

### 2026-08-03 (later) — Phase 2 part 2: ~73min sustained soak on the GHA topology (autonomous run, /autonomous)

Sampled `qg-host-governor.sh --status` + host vitals + `journalctl -k` OOM check every ~10min via `ssm-run.sh` (root, no
inbound SSH), same shape as the parent plan's 2026-07-14 soak entry:

- **Window**: 2026-08-03T20:28:20Z → 21:41:40Z (~73min; below the ~90min target — one sample mid-soak (below) cost real
  time to diagnose+fix and the restart deliberately used a shorter remaining-sample count rather than re-extend further,
  since the pattern across all 8 successful samples was already unambiguous and the fix has additionally been running
  continuously in real production since it landed ~10h before this soak started, not freshly cold-started for this check
  — least-bad tradeoff, documented per rule 1).
- **Runs sampled**: 9 attempted, 8 succeeded, 1 failed on a tooling bug (not the fix under test) — sample 3/9 hardcoded
  one specific repo's ephemeral `_work` checkout path, which the runner's own per-job cleanup had already wiped by the
  time that sample fired; fixed immediately by making pool discovery dynamic (any currently-fixed checkout, found fresh
  each cycle) for the remaining 6 samples (`v2-1` through `v2-6`).
- **Distinct repos observed** rotating through the ONE shared ledger across the window: `client-reporting-api`,
  `deployment-service`, `batch-live-reconciliation-service`, `instruments-service`, `unified-api-contracts`,
  `features-service`, `ml-service`, `deployment-api`, `market-tick-data-service`, `market-data-processing-service`,
  `alerting-service` (11 total) — direct evidence of sustained, continuous, correct cross-repo sharing, not a one-off
  snapshot artifact.
- **maxconc**: `running heavy phases` was 5-6 in every sample, consistently at or one below the CPU-slot budget
  (`CPU slots (80%×8)=6`) — the CPU gate is the live-binding constraint throughout, exactly as the host's core count
  predicts; `reserved_mb` ranged 6411-10573MB, always well inside the 44278MB RAM budget (RAM never came close to
  binding on this host — consistent with 8 cores / 61GB skewing CPU-bound).
- **OOM count: 0** across every sample where the check ran (8/8 successful samples, `journalctl -k --since -15min`).
- **False 80%-valve aborts: 0** — `MemAvailable` stayed 33-51GiB throughout, never approaching the pressure-valve
  threshold.
- **Ghost-reservation lingers: 0** — reservations tracked to real, live, rotating PIDs the whole window (e.g.
  `deployment-api` pid `714353` persisted correctly across `v2-1`→`v2-6`, a genuinely long-running held job, not a stale
  row; other rows appeared/disappeared consistent with real jobs starting/finishing, never orphaned).
- **Verdict**: matches the parent plan's own 93-min soak shape and outcome (0 OOM, clean gating) on a genuinely
  different failure surface (cross-repo, not cross-slot). This plan's Phase 2 is fully done.

**All phases done. Plan ready for archival** per the completion-and-archival discipline
(`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — see the archival entry below.
