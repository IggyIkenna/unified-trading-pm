---
doc_type: plan
title: Host-adaptive RAM+CPU QG admission governor — replace fixed-K with resource reservation
summary:
  Replace quality-gates.sh's fixed-K host-concurrency token bucket with a host-adaptive admission controller that reads
  each host's real MemTotal/MemAvailable + physical cores at runtime and admits a QG heavy phase only when BOTH a RAM
  budget (reserved + this-run peak-RSS ≤ safety-fraction of host RAM) AND a CPU budget (running heavy count ≤ cores ×
  fraction) allow it — using host-portable per-repo cost baselines. Fixes the K=1 floor that taxes the fleet 15–40 min
  per ship on 61 GB hosts while being correct on an 8 GB VM, a 24 GB Mac, and a 128 GB VM. Interim quick-win — raise K
  on current 61 GB hosts now (data-backed) — precedes the full governor.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [infra, quality-gates, host-contention, governor, resource-admission, cross-host]
related:
  [
    plans/active/issues/qg_host_governor_severe_contention_2026_07_13.md,
    codex/06-coding-standards/quality-gates.md,
    scripts/quality-gates-base/qg-host-governor.sh,
  ]
created: "2026-07-14"
last_updated: "2026-07-14"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [plans/active/issues/qg_host_governor_severe_contention_2026_07_13.md, scripts/quality-gates-base/qg-host-governor.sh]
---

# Host-adaptive RAM+CPU QG admission governor

> **LOCAL / operator-driven plan** (`assigned_vm: NA`) — not AO-ingested. Operator decision 2026-07-14: human-driven,
> and raise K on current hosts as an interim quick-win before the full governor.

## Codex SSOTs (read + keep aligned)

- `codex/06-coding-standards/quality-gates.md` § "Per-repo resource baseline", "VM-sizing", "Both base files are
  governed" — the current fixed-K model + the (now-stale) heavy-tier claim this plan corrects.
- `scripts/quality-gates-base/qg-host-governor.sh` — the current token-bucket governor being replaced.
- `scripts/quality-gates-base/base-service.sh` + `base-library.sh` — the `qg_governor_acquire`/`release` call sites
  around the heavy phases; `QG_PROFILE` handling; the `MAX_DURATION` meta-gate.
- `scripts/quality_gates/profile_qg_resources.py` + `scripts/dev/measure-qg-baseline.sh` — the tree-RSS profiler and
  baseline recorder that feed per-repo costs; `scripts/dev/qg_resource_baseline.json` is the data file.
- `plans/active/issues/qg_host_governor_severe_contention_2026_07_13.md` — the open issue whose 4 todos this plan
  resolves (K-floor policy, MAX_DURATION counts queue-as-work, light-slice queues needlessly, fairness/starvation gap).

## Problem

The governor caps concurrent QG heavy phases host-wide at a fixed K (flock token bucket). `bootstrap_vm.sh` pins
`QG_HOST_CONCURRENCY=1` on worker hosts — a floor from the 2026-05-29 chronic-impairment (swap) incident. At current
fleet size (≈16–20 slots) K=1 turns every `quality-gates.sh` into a 15–40 min queue wait purely to acquire the token.
The floor is a **fixed number**, so it is simultaneously **too low** for a 61/96/128 GB host (abundant RAM idle) and
potentially **too high** for an 8 GB VM (two heavy runs would swap). A fixed K cannot be right across a heterogeneous
fleet: Harsh 96 GB PC, Ikenna 24 GB Apple-silicon laptop, 61 GB worker VMs, plus future 8 GB / 128 GB VMs.

## Goal

One governor, correct on every host, that decides admission from the host's **measured capacity** (RAM + cores read at
runtime) and **per-repo measured cost** (host-portable), never a hand-set number. Resolve the contention issue's 4 todos
in the same change. Fix it once — no per-host tuning, no recurring "raise/lower K" tickets.

## The measured foundation (this session, 2026-07-14 — VM tree-RSS re-benchmark)

Re-profiled 22/23 repos on a 61 GB / 16-core worker VM with the committed methodology (`QG_PROFILE`, single-core pinned,
`PYTEST_WORKERS=1`, whole-process-tree RSS). Full data written to `scripts/dev/qg_resource_baseline.json` `vm` key.
Findings that drive the design:

1. **RSS is host-portable.** 16/22 repos within ±6 % of the committed `local` (different host) numbers → per-repo
   peak-RSS is a portable cost the governor can trust across hosts. (CPU-seconds likewise; only wall varies with core
   speed.)
2. **Heavy-tier reordered — codex is stale.** Real order now: **UTL 5.46 GB → instruments-service 3.66 GB → execution
   2.09 → deployment-api 1.77 → features 1.61 → …**. The codex claims "UTL 5.27, then execution/features ~1.9 GB" as #2;
   instruments-service silently grew **+182 % (1.30 → 3.66 GB)** since 2026-06-17 (absorbed the reference-data SSOT /
   URDI consolidation). Proof that a static baseline goes stale — the governor must re-measure on a cadence.
3. **On a 61 GB host RAM is NOT the binding constraint.** Sum of ALL 22 repos' peak RSS run at once = **29.1 GB** vs a
   70 % ceiling of **43 GB**. Even a pathological all-at-once fits with 14 GB spare. The K=1 floor is drastically
   over-conservative here; the real limiter at high concurrency is **CPU (16 cores)**, not RAM.
4. **Fleet runs `PYTEST_WORKERS=1`** (memory-frugal default in `base-service.sh`) → the single-worker measurements ARE
   the true per-run footprint; no worker-count multiplier needed.

## Design — host-adaptive dual-gate admission controller

Replace the K-token bucket with a **reservation ledger + dual gate**. A run acquires before the heavy phase (TESTS +
TYPE CHECK) and releases after.

**Host capacity (read live, per host):** `MemTotal`, `MemAvailable`, physical cores. Linux via `/proc/meminfo` +
`lscpu`/`nproc`; macOS via `sysctl hw.memsize` / `hw.physicalcpu` + `vm_stat` (bash 3.2-safe — the Mac host has no
`lscpu`/`/proc` and runs bash 3.2; the governor already uses explicit-FD flock for this reason).

**Budgets:**

- `QG_RAM_BUDGET = QG_MEM_SAFETY_FRAC × MemTotal` — the ceiling on the SUM of in-flight QG peak reservations (STATIC;
  `SAFETY_FRAC` default **0.70**, operator-specified). Bounds QG's own total footprint.
- `QG_MEM_FLOOR` — live-availability floor reserving OS + orchestrator + interactive headroom (default
  `max(2 GB, 0.1 × MemTotal)`; Mac skews higher).
- `CPU_SLOTS = max(1, floor(cores × QG_CPU_FRAC))` — `CPU_FRAC` default ~**0.80** (leave cores for the orchestrator +
  interactive). One `PYTEST_WORKERS=1` run ≈ 1–1.5 cores at peak, so a count-based slot ≈ cores works for v1; a per-repo
  `cpu_weight = ceil(cpu_s / wall_s)` refinement is optional.

**Admission (ALL must hold) — the check-and-reserve is ATOMIC under one flock, so N simultaneous acquirers serialize
instead of all-admitting:**

1. **RAM reservation bound** (pure ledger): `sum_reserved_peak + this_repo_peak ≤ QG_RAM_BUDGET`. This is what stops 6
   UTL runs (6 × 5.5 = 33 GB) from stacking — each admitted run's peak is reserved, so the run that would exceed the
   budget queues instead.
2. **Live-availability backstop** (pure live reading): `MemAvailable ≥ this_repo_peak + QG_MEM_FLOOR`. Ensures free RAM
   actually exists NOW for this run to climb into — catches memory pressure from NON-QG sources (orchestrator, OS, other
   processes) the ledger can't see, and the "host already 50 % used" case.
3. **CPU**: `running_heavy_count + 1 ≤ CPU_SLOTS`.

**Two INDEPENDENT memory clauses, never a single `min()`.** Clause 1 is pure-ledger (bounds QG's own stack); clause 2 is
pure-live (bounds external pressure + climb headroom). Folding them into `min(frac×MemTotal, MemAvailable − floor)`
DOUBLE-COUNTS in-flight QG memory — a climbing run appears in BOTH the shrinking `MemAvailable` AND the reservation sum
— which blocks admits far too early. Separate clauses guard the two distinct failure modes without double-counting.

**Worked example — 6 agents QG UTL, host already 50 % used (61 GB / 16-core):** `QG_RAM_BUDGET` = 0.7 × 61 = 43 GB;
`MemAvailable` ≈ 30 GB; `FLOOR` ≈ 6 GB. Acquires serialize under the flock: run 1 reserves 5.5 GB (sum 5.5 ≤ 43 ✓,
MemAvail 30 ≥ 11.5 ✓), run 2 → 11, run 3 → 16.5 — but as they climb `MemAvailable` falls, so by ~run 3–4 the LIVE clause
(`MemAvailable ≥ 11.5`) blocks further admits even though the reservation clause alone would allow ~7. ~3–4 UTL runs
admit, the rest QUEUE (FIFO, with aging). No OOM. On an idle 61 GB host the same math admits ~7; on a 24 GB Mac, ~1–2.

**Reservation ledger** (replaces the K flock tokens): a flock-protected record of `{pid, repo, rss_mb, ts}` per
in-flight heavy phase. On admit → append; on release/exit → remove. **PID-liveness sweep** on every admission attempt
prunes dead PIDs' reservations (crash-safe — a killed QG can't leak its reservation; replaces the old flock-auto-release
guarantee).

**Oversize-solo escape (critical for small hosts):** if `this_repo_peak > QG_RAM_BUDGET` (e.g. UTL 5.5 GB on an 8 GB
host where budget ≈ 5.6 GB and the live-floor clause can never be met alongside anything else), the run must **wait
until `sum_reserved_peak == 0` then run SOLO** and log LOUDLY that the host is undersized for this repo (it will swap —
accept or resize). Without this the run waits forever for budget that never exists → deadlock.

**Fairness / anti-starvation:** current governor has no ordering (20 waiters free-for-all the same `flock -n`). On a
small host a heavy repo (UTL) can be starved by a stream of light runs slipping into the leftover headroom. Add a FIFO
ticket + **head-of-line aging**: once the oldest waiter has waited > T, nothing younger may admit ahead of it (hold
slots until the head fits). Resolves the issue doc's fairness todo.

**Light-slice bypass:** only the heavy phases acquire. `QG_SLICE=lint-codex` (never runs TESTS/TYPECHECK) acquires
nothing — no queueing. Resolves the issue doc's light-slice todo.

**MAX_DURATION fix:** stamp "work start" AFTER admission so governor queue time is excluded from the wall-clock
meta-gate — a legitimate queue wait can no longer fail an otherwise-green run. Resolves the issue doc's measurement-bug
todo.

### Cross-host behaviour (the "fix it once" proof) — budget = 0.7×RAM − floor

| Host                   | RAM_BUDGET | Heavy concurrency                                                 | Binding gate      |
| ---------------------- | ---------- | ----------------------------------------------------------------- | ----------------- |
| 8 GB VM (future)       | ~3.6 GB    | UTL/instruments run **SOLO** (>budget, warn+swap); light repos ~1 | RAM (solo escape) |
| 24 GB Mac (Ikenna, M5) | ~14 GB     | UTL+instruments+execution (11.3 GB) → ~**3 heavy**                | RAM               |
| 61 GB worker VM (now)  | ~37 GB     | all 29 GB fits → RAM never binds → ~**12** (16×0.8)               | CPU               |
| 96 GB PC (Harsh)       | ~64 GB     | everything fits                                                   | CPU               |
| 128 GB VM (future)     | ~88 GB     | RAM never binds                                                   | CPU (sole)        |

Same code, same config defaults — each host self-tunes from its own `MemTotal` + cores. No per-host K.

## Phases + todos

### Phase 0 — Baseline data foundation (partly done this session)

- [ ] [OPERATOR] P0. Review + ship the `vm` baseline written to `scripts/dev/qg_resource_baseline.json` (22 repos,
      uncommitted in slot 16) to LDR — data-only file change.
- [ ] [INFRA] P1. Consolidate the baseline schema to a host-portable canonical per-repo cost the governor reads (RSS +
      cpu_s are host-invariant per finding #1) — keep `local`/`vm` as provenance; governor reads `max(local,vm)`
      (conservative) or a fresh canonical run. Unmeasured repo → conservative default (e.g. 2 GB) + a WARN to profile
      it, never a free pass.
- [ ] [INFRA] P1. Re-measure instruments-service AND unified-trading-library in isolation (instruments jumped +182 %;
      confirm it is real growth, not measurement contention from the live-workspace sweep) and refresh their baseline.

### Phase 1 — Interim quick-win: raise K on 61 GB hosts (operator-approved 2026-07-14)

- [ ] [INFRA] P0. Re-verify the 2026-05-29 swap-incident repro does NOT recur at higher K on a 61 GB host (drive N
      concurrent heavy QG runs; watch `free -h` swap-in rate + load) — the issue doc requires this before touching the
      floor. Capture evidence.
- [ ] [INFRA] P0. Raise `QG_HOST_CONCURRENCY` on 61 GB fleet hosts from 1 to a safe RAM-derived value
      (`floor(0.7×RAM / heaviest-single-run-RSS)` ≈ 6, or a flat 6–8) in `agent-orchestrator/scripts/bootstrap_vm.sh` +
      live `.env.local`; measure the fleet queue-time drop. (Interim — the governor replaces this in Phase 5.)

### Phase 2 — Host capacity introspection (portable)

- [ ] [INFRA] P1. `qg_host_capacity` in `qg-host-governor.sh`: emit MemTotal + MemAvailable + physical cores — Linux
      (`/proc/meminfo`, `lscpu -p=core`/`nproc`) AND macOS (`sysctl hw.memsize`/`hw.physicalcpu`, `vm_stat` for
      available); bash 3.2-safe. Add `--probe` printing detected capacity + derived RAM/CPU budgets.
- [ ] [INFRA] P2. Unit tests for the capacity parser on captured Linux + macOS `/proc/meminfo`/`vm_stat` fixtures (no
      live-host dependence).

### Phase 3 — Reservation ledger + dual-gate admission

- [ ] [INFRA] P1. Replace the K-token flock bucket with a reservation ledger (flock-protected; per-PID reservation files
      or a locked JSON) + PID-liveness sweep pruning dead reservations.
- [ ] [INFRA] P1. RAM gate — TWO independent clauses (never a single `min()`): (1) reservation bound
      `sum_reserved_peak + this_repo_peak ≤ QG_RAM_BUDGET` (caps stacking of same/mixed heavy repos — the 6×UTL case);
      (2) live backstop `MemAvailable ≥ this_repo_peak + QG_MEM_FLOOR` (external pressure + climb headroom). Per-repo
      peak from the canonical baseline; unmeasured → conservative default. Check-and-reserve ATOMIC under one flock.
- [ ] [INFRA] P1. CPU gate — `running_heavy_count + 1 ≤ floor(cores × QG_CPU_FRAC)`.
- [ ] [INFRA] P0. Oversize-solo escape — a repo whose peak > `QG_RAM_BUDGET` (or can't meet the live clause beside
      anything) waits for `sum_reserved_peak==0` then runs SOLO + LOUD undersized-host warning (prevents 8 GB deadlock).
- [ ] [INFRA] P2. Light-slice bypass — only TESTS + TYPE CHECK acquire; `QG_SLICE=lint-codex` acquires nothing.
- [ ] [INFRA] P2. Env knobs — `QG_MEM_SAFETY_FRAC` (0.70) / `QG_MEM_FLOOR_GB` / `QG_CPU_FRAC` (0.80) /
      `QG_HOST_CONCURRENCY` demoted to an OPTIONAL hard-cap override (no longer the primary control).

### Phase 4 — Fairness + observability

- [ ] [INFRA] P2. FIFO ticket + head-of-line aging so a heavy repo (UTL) is not starved by light runs on a small host.
- [ ] [INFRA] P2. MAX_DURATION fix — stamp work-start AFTER admission so governor queue time can't fail a green run
      (issue doc todo #2).
- [ ] [INFRA] P3. `--status` shows RAM_BUDGET / reserved / CPU_SLOTS / waiters / per-repo reservations + an
      admitted-vs-queued decision log for tuning.

### Phase 5 — Rollout + retire fixed K

- [ ] [INFRA] P1. Remove the `QG_HOST_CONCURRENCY=1` pin from `bootstrap_vm.sh` (keep the env as an optional override);
      retire the Phase-1 interim bump onto the governor.
- [ ] [INFRA] P1. Update `codex/06-coding-standards/quality-gates.md` — the dual-gate model + the corrected heavy-tier
      order (UTL → instruments → execution → …; the stale "execution/features = #2" fixed).
- [ ] [INFRA] P2. Close the 4 todos in `issues/qg_host_governor_severe_contention_2026_07_13.md` (this plan resolves all
      four) and banner the issue resolved.

### Phase 6 — Cross-host verification

- [ ] [INFRA] P1. Simulate 8 / 24 / 61 / 96 / 128 GB via a `QG_MEM_TOTAL_OVERRIDE` + core-count override: assert
      admission behaves per the cross-host table (8 GB → UTL solo, no deadlock; 24 GB → ~3 heavy; 61 GB → CPU-bound ~12;
      128 GB → CPU-only).
- [ ] [INFRA] P2. Live fleet soak — queue-time-under-contention delta vs K=1 (`scripts/dev/benchmark-qg-under-load.sh`);
      confirm no swap regression on the 61 GB host.

## Progress Log

### 2026-07-14 — VM re-benchmark + plan authored (slot 16, interactive)

- Re-benchmarked 22/23 repos on this 61 GB/16-core worker VM with the tree-RSS profiler (`profile_qg_resources.py`,
  `QG_PROFILE`, single-core pinned). Prior `/usr/bin/time` sweep was killed — it measured single-process RSS (~1.8×
  undercount vs tree-RSS); the profiler is the correct tool and matches the committed `local` methodology.
- Data written to `scripts/dev/qg_resource_baseline.json` `vm` key (22 repos; UI excluded — early-bail). **Uncommitted
  in slot 16 pending operator review** (Phase 0 todo). 9 non-zero gate exits were the workspace-level "production
  readiness validators" (plans/manifest state) firing against the live root workspace — a measurement artifact, not
  fleet-red; RSS stays valid (heavy phases ran).
- Key findings drove the design above: RSS host-portable (±6 %); instruments-service +182 % → new #2 (codex stale); 61
  GB host all-at-once = 29 GB ≪ 43 GB ceiling (RAM not binding — CPU is); fleet `PYTEST_WORKERS=1`.
- Operator decisions (2026-07-14): human-driven plan; raise K now as interim quick-win (Phase 1), gated on the
  2026-05-29 repro re-verify.
- **Design refinement (operator review — same/mixed-repo stacking, e.g. 6 agents QG UTL on a half-full host):** the RAM
  gate is now TWO independent clauses, not the single `min()` first drafted. Clause 1 (reservation-sum ≤
  `QG_RAM_BUDGET`) caps stacking of concurrent heavy runs via the ledger; clause 2 (`MemAvailable ≥ this_peak + FLOOR`)
  catches non-QG pressure + climb headroom. The single-`min()` form double-counted in-flight QG memory (present in both
  the shrinking `MemAvailable` AND the reservation sum) and would have blocked admits too early. Check-and-reserve is
  atomic under one flock so N simultaneous acquirers serialize. Worked example (6×UTL, 50 %-used 61 GB → ~3–4 admit,
  rest queue) added to the design section.

## Deferred / open decisions

- Canonical-cost source (Phase 0): `max(local,vm)` vs a fresh single canonical measurement — decide at Phase 0.
- `cpu_weight` per-repo refinement (Phase 3 CPU gate) deferred to v2 unless the count-based slot proves too coarse.
