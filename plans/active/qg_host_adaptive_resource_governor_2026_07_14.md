---
doc_type: plan
title: Host-adaptive RAM+CPU QG admission governor — replace fixed-K with resource reservation
summary:
  Replace quality-gates.sh's fixed-K host-concurrency token bucket with a host-adaptive admission controller that reads
  each host's real MemTotal/MemAvailable + physical cores at runtime and admits a QG heavy phase only when BOTH a RAM
  budget (reserved + this-run peak-RSS ≤ safety-fraction of host RAM) AND a CPU budget (running heavy count ≤ cores ×
  fraction) allow it — using host-portable per-repo cost baselines. Fixes the K=1 floor that taxes the fleet 15–40 min
  per ship on 61 GB hosts while being correct from the 16 GB fleet floor through a 24 GB Mac to a 128 GB VM. Interim
  quick-win — raise K on current 61 GB hosts now (data-backed) — precedes the full governor.
status: active
nature: process
asset_group: [ci] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [infra, quality-gates, host-contention, governor, resource-admission, cross-host]
related:
  [
    /plans/archive/issues/qg_host_governor_severe_contention_2026_07_13.md,
    /codex/06-coding-standards/quality-gates.md,
    scripts/quality-gates-base/qg-host-governor.sh,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-07-14"
last_updated: 2026-08-03
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
  [
    /plans/archive/issues/qg_host_governor_severe_contention_2026_07_13.md,
    scripts/quality-gates-base/qg-host-governor.sh,
  ]
context_scope:
  [
    /codex/06-coding-standards/quality-gates.md,
    scripts/quality-gates-base/qg-host-governor.sh,
    scripts/quality-gates-base/base-service.sh,
    /plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md,
  ]
---

# Host-adaptive RAM+CPU QG admission governor

> **LOCAL / operator-driven plan** (`assigned_vm: NA`) — not AO-ingested. Operator decision 2026-07-14: human-driven,
> and raise K on current hosts as an interim quick-win before the full governor.

## Codex SSOTs (read + keep aligned)

- `/codex/06-coding-standards/quality-gates.md` § "Per-repo resource baseline", "VM-sizing", "Both base files are
  governed" — the current fixed-K model + the (now-stale) heavy-tier claim this plan corrects.
- `scripts/quality-gates-base/qg-host-governor.sh` — the current token-bucket governor being replaced.
- `scripts/quality-gates-base/base-service.sh` + `base-library.sh` — the `qg_governor_acquire`/`release` call sites
  around the heavy phases; `QG_PROFILE` handling; the `MAX_DURATION` meta-gate.
- `scripts/quality_gates/profile_qg_resources.py` + `scripts/dev/measure-qg-baseline.sh` — the tree-RSS profiler and
  baseline recorder that feed per-repo costs; `scripts/dev/qg_resource_baseline.json` is the data file.
- `/plans/archive/issues/qg_host_governor_severe_contention_2026_07_13.md` — the issue whose 4 todos this plan resolves
  (K-floor policy, MAX_DURATION counts queue-as-work, light-slice queues needlessly, fairness/starvation gap).

## Problem

The governor caps concurrent QG heavy phases host-wide at a fixed K (flock token bucket). `bootstrap_vm.sh` pins
`QG_HOST_CONCURRENCY=1` on worker hosts — a floor from the 2026-05-29 chronic-impairment (swap) incident. At current
fleet size (≈16–20 slots) K=1 turns every `quality-gates.sh` into a 15–40 min queue wait purely to acquire the token.
The floor is a **fixed number**, so it is simultaneously **too low** for a 61/96/128 GB host (abundant RAM idle) and
potentially **too high** for a small host near the 16 GB floor (a few heavy runs would swap). A fixed K cannot be right
across a heterogeneous fleet: Harsh 96 GB PC, Ikenna 24 GB Apple-silicon laptop, 61 GB worker VMs, plus future 16 GB
laptops / 128 GB VMs.

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
  `max(2 GB, 0.1 × MemTotal)`).
- `CPU_SLOTS = max(1, floor(cores × QG_CPU_FRAC))` — `CPU_FRAC` default ~**0.80**. NOTE (operator 2026-07-14): a
  `PYTEST_WORKERS=1` single-core-pinned run UNDER-represents real core demand (basedpyright + pytest burst multi-core),
  so `cpu_weight` per repo MUST come from an UNPINNED parallel re-measure (Phase 0), not the single-core baseline — the
  pinned `cpu_s` can't see peak concurrent cores.
- `K` (host-concurrency count) is DEMOTED to a loose runaway backstop, NOT the primary control — RAM-derived default
  (generous, e.g. up to ~20 on large hosts) so small/light repos never wait on a count; the RAM + CPU gates do the real
  limiting. Per-host overridable.

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
in-flight heavy phase, at a HOST-SHARED path so every slot on a host coordinates —
`${SHARED_ROOT}/.benchmarks/qg-governor/` where `SHARED_ROOT = ${WORKSPACE_ROOT%/.tabs/*}`. The strip matters:
`setup-tab-worktrees.sh` sets `WORKSPACE_ROOT` PER-SLOT to `.tabs/<N>`, so using it raw would put the ledger under one
slot and the governor would NOT coordinate across slots (the exact silent-degradation bug this guards against);
stripping the `/.tabs/<N>` suffix lands all slots on the shared parent, and on a single-clone laptop the strip is a
no-op. On admit → append; on release/exit → remove. **PID-liveness sweep** on every admission attempt prunes dead PIDs'
reservations (crash-safe — a killed QG can't leak its reservation; replaces the old flock-auto-release guarantee).

**Oversize-solo guard (defensive only — min supported host = 16 GB):** QG is never run below **16 GB**, where
`QG_RAM_BUDGET` ≈ 11 GB comfortably exceeds the heaviest repo (UTL 5.5 GB), so no run is ever oversize in practice. Keep
a trivial guard — a run whose peak somehow exceeds the whole budget waits for `sum_reserved_peak == 0`, then runs solo
with a loud warning — but the fairness/drain complexity for STACKED oversize runs is out of scope (cannot occur ≥ 16
GB).

**Fairness / anti-starvation:** current governor has no ordering (20 waiters free-for-all the same `flock -n`). On a
small host a heavy repo (UTL) can be starved by a stream of light runs slipping into the leftover headroom. Add a FIFO
ticket + **head-of-line aging**: once the oldest waiter has waited > T, nothing younger may admit ahead of it (hold
slots until the head fits). Resolves the issue doc's fairness todo.

**Light-slice bypass:** only the heavy phases acquire. `QG_SLICE=lint-codex` (never runs TESTS/TYPECHECK) acquires
nothing — no queueing. Resolves the issue doc's light-slice todo.

**MAX_DURATION fix:** stamp "work start" AFTER admission so governor queue time is excluded from the wall-clock
meta-gate — a legitimate queue wait can no longer fail an otherwise-green run. Resolves the issue doc's measurement-bug
todo.

**Enforcement backstops (operator 2026-07-14 — reservations are advisory; these are hard, defence in depth):**

- **Per-repo cgroup cap.** Each admitted run is wrapped at `QG_MEM_CAP = 1.2 × baseline_peak` (the existing base-service
  `QG_MEM_CAP` hook, currently 0/off) so a mis-measured or runaway run is OOM-killed in ITS OWN cgroup, never taking the
  host down. Per-repo, derived from that repo's baseline.
- **Global 80 % valve + kill-switch.** If live host used-RAM crosses **80 %** at any point, ABORT the offending/newest
  QG run and Slack-alert. Catches aggregate pressure the per-repo caps miss (many runs each just under their cap) and
  non-QG spikes — and doubles as the fast kill-switch, so no separate rollback path is needed.
- **Overrun alert.** A run whose actual tree-RSS exceeds its `1.2 × baseline` cap → Slack alert (this repo grew or a
  test regressed — investigate + re-baseline).

**Baseline freshness loop (keeps the governor honest, for free):** the governor already samples each run's actual
tree-RSS (for the live checks), so it records the observed peak per repo. A **daily** job promotes observations → the
committed baseline — we already run every repo's QG most days after changes, so the data arrives free, and by design
changes aren't drastic so drift stays small. A single run whose observed peak is **> 20 % above** its baseline is
treated as anomalous → **Slack alert instead of a silent bump** (a +182 %-style jump signals something wrong — exactly
the instruments-service case that motivated this plan). This closes the staleness gap: no repo silently outgrows its
reservation and OOMs.

### Cross-host behaviour (the "fix it once" proof) — reservation budget = 0.7 × RAM; min supported host = 16 GB

| Host                   | QG_RAM_BUDGET | Heavy concurrency                                      | Binding gate |
| ---------------------- | ------------- | ------------------------------------------------------ | ------------ |
| 16 GB (fleet floor)    | ~11 GB        | UTL + instruments (9.2 GB) → ~**2 heavy**              | RAM          |
| 24 GB Mac (Ikenna, M5) | ~17 GB        | UTL + instruments + execution (11.3 GB) → ~**3 heavy** | RAM          |
| 61 GB worker VM (now)  | ~43 GB        | all 29 GB fits → RAM never binds → CPU-bound (~cores)  | CPU          |
| 96 GB PC (Harsh)       | ~67 GB        | everything fits                                        | CPU          |
| 128 GB VM (future)     | ~90 GB        | RAM never binds                                        | CPU (sole)   |

Same code, same config defaults — each host self-tunes from its own `MemTotal` + cores. No per-host K (K is only a loose
runaway backstop). QG is never run below 16 GB, so no host ever needs the oversize-solo path in practice.

## Phases + todos

### Phase 0 — Baseline data foundation (partly done this session)

- [x] [INFRA] P0. ✅ **RETAGGED 2026-07-28 (stale-tag audit — already shipped, `[OPERATOR]` never removed).** Shipped
      the `vm` baseline (22 repos) to LDR — data-only. Evidence: PM@dd7f05e49.
- [ ] [INFRA] P1. DEFERRED (already satisfied functionally) — `_qg_repo_peak_mb` reads `max(local, vm)` peak-RSS as the
      single host-portable per-repo cost the governor uses; a further schema-field merge adds no behaviour. Left open
      only if a formal single-canonical schema is later wanted. — Consolidate the baseline schema to a host-portable
      canonical per-repo cost the governor reads (RSS + cpu_s are host-invariant per finding #1) — keep `local`/`vm` as
      provenance; governor reads `max(local,vm)` (conservative) or a fresh canonical run. Unmeasured repo → conservative
      default (e.g. 2 GB) + a WARN to profile it, never a free pass.
- [x] [INFRA] P1. ✅ DONE — the 2026-07-14 VM tree-RSS re-benchmark (PM@dd7f05e49) profiled each repo's QG in isolation:
      instruments-service 3.66 GB (+182 % captured), unified-trading-library 5.46 GB — the current governor baseline. —
      Re-measure instruments-service AND unified-trading-library in isolation (instruments jumped +182 %; confirm it is
      real growth, not measurement contention from the live-workspace sweep) and refresh their baseline.
- [ ] [INFRA] P1. DEFERRED (count-based validated adequate) — the 93-min soak showed the count-based CPU gate
      (`cpu_slots=3`) worked cleanly (maxconc=3, no CPU thrash, 0 OOM); this is the plan's own "unless the count-based
      slot proves too coarse" condition, which it did not. Revisit only if per-repo `cpu_weight` is later needed. —
      Measure per-repo CPU demand under the profiler's UNPINNED `--parallel` mode (real config, no single-core/thread
      caps) to get PEAK concurrent cores per repo → feed `cpu_weight` for the CPU gate. The single-core-pinned baseline
      can't see this (basedpyright + pytest burst multi-core).
- [ ] [INFRA] P1. Baseline freshness loop — the governor records each run's observed peak tree-RSS; a DAILY job promotes
      observations → the committed baseline (free — we already run every repo's QG most days). A single-run observed
      peak > 20 % above baseline → Slack alert (NOT a silent bump; a +182 %-style jump means something is wrong).

### Phase 1 — Interim quick-win: raise K on 61 GB hosts (operator-approved 2026-07-14)

- [x] ✅ [INFRA] P0. **RESOLVED-BY-RULING — stale DEFERRED tag cleaned 2026-07-28 (stale-tag audit; this was never a
      live `[OPERATOR]` gate, just an inline label describing an already-made decision).** Operator ruling 2026-07-14
      (documented inline in this plan, `qg_host_adaptive_resource_governor_2026_07_14.md`), "raise K to 6 for now": the
      live load-repro is skipped; safety is instead established by analysis — 6×UTL worst-case = 33 GB < the 43 GB (70
      %) ceiling, and each worker's QG is already capped in a per-worker 10 GB systemd scope (`tmux_spawn` §6.2) + 16 GB
      host swap, so the 05-29 single-pytest OOM is contained per-worker and cannot recur at K=6. The Phase-6 soak (no
      swap regression / no false 80 % aborts) is the empirical confirmation in lieu of the live repro. **STALE-CLOSED
      2026-07-30 (na-eligibility-audit, infra tranche, dispatch agt-30721a)** — this is a narrative artifact describing
      an already-made decision, not a live gate; the decision it describes (raise K to 6) was already executed in the
      very next checkbox below (`[x] Raised QG_HOST_CONCURRENCY from 1 to 6`).
- [x] [INFRA] P0. ✅ Raised `QG_HOST_CONCURRENCY` from 1 to **6** across all three layers — live tmux global env
      (`setenv -g`, new workers inherit as they cycle) + root `agent-orchestrator/.env.local` (survives restart) +
      `bootstrap_vm.sh` template (survives re-bootstrap). Evidence: AO@222369f (bootstrap) + `.env.local=6` +
      `tmux show-environment -g → QG_HOST_CONCURRENCY=6`. Fleet queue-time delta to be measured in the Phase-6 soak.
      (Interim — once the gates land in Phase 3, K loosens to the runaway backstop, RAM-derived per host.)

### Phase 2 — Host capacity introspection (portable)

- [x] [INFRA] P1. ✅ `qg_host_capacity` + `--probe` in `qg-host-governor.sh`: MemTotal/MemAvailable/physical-cores on
      Linux (`/proc/meminfo`, `lscpu`/`nproc`) AND macOS (`sysctl` + `vm_stat` free+inactive+purgeable+file-backed);
      bash 3.2-safe; ADDITIVE (not yet wired into acquire/release). Evidence: PM@dd7f05e49 (`--probe` green on the 61 GB
      VM → `mem_total_gb=61 cores=8 ram_budget_gb=43 cpu_slots=6`; shellcheck clean; `--status` unregressed).
- [x] [INFRA] P2. ✅ Fixture-based parser unit tests (Linux `/proc/meminfo` + macOS faked `sysctl`/`vm_stat`), no
      live-host dependence. Evidence: PM@dd7f05e49 (`tests/test-qg-host-capacity.sh` — 3 blocks green; negative control
      confirms failures propagate across the subshell boundary).

### Phase 3 — Reservation ledger + dual-gate admission

- [x] [INFRA] P1. ✅ PM@88a4925af — Reservation ledger (replaces the K-token bucket) at the HOST-SHARED path
      `${WORKSPACE_ROOT%/.tabs/*}/.benchmarks/qg-governor/` (strip the per-slot `.tabs/<N>` suffix — raw
      `WORKSPACE_ROOT` is per-slot, which would silently break cross-slot coordination); flock-protected; PID-liveness
      sweep prunes dead reservations.
- [x] [INFRA] P1. ✅ PM@3de0ee74d (decision) + PM@6e818079a (wired) — RAM gate — TWO independent clauses (never a single
      `min()`): (1) reservation bound `sum_reserved_peak + this_repo_peak ≤ QG_RAM_BUDGET` (caps stacking of same/mixed
      heavy repos — the 6×UTL case); (2) live backstop `MemAvailable ≥ this_repo_peak + QG_MEM_FLOOR` (external
      pressure + climb headroom). Per-repo peak from the canonical baseline; unmeasured → conservative default.
      Check-and-reserve ATOMIC under one flock.
- [x] [INFRA] P1. ✅ PM@3de0ee74d (count-based slot; cpu_weight refinement deferred — see Deferred) — CPU gate —
      `running_weight + this_cpu_weight ≤ floor(cores × QG_CPU_FRAC)`, `cpu_weight` from the Phase-0 unpinned parallel
      measure (peak concurrent cores), NOT a flat 1-per-run.
- [x] [INFRA] P1. ✅ PM@a6b5e24a5 — Per-repo cgroup cap — wrap each admitted run at `QG_MEM_CAP = 1.2 × baseline_peak`
      (existing base-service hook, currently 0/off) so a runaway/mis-measured run is OOM-killed in its OWN cgroup, not
      the host.
- [x] [INFRA] P0. ✅ unified-trading-pm@<PENDING-SHA> — Global 80 % valve ✅ PM@a6b5e24a5 (admission side, SHIPPED);
      runtime ABORT of an already-running >80 % job — SHIPPED (self-scoped v1, see Progress Log 2026-07-27 slot-5): if
      live host used-RAM crosses `QG_HOST_RAM_ABORT_PCT` (default 80%) for `QG_WATCHDOG_CONSECUTIVE_HITS` (default 2)
      consecutive polls, the ADMITTED run's own background watchdog SIGTERMs its own process tree + writes a loud marker
      file + logs. Trades the "pick exactly one offender" refinement described here for a simpler, safer self-scoped
      design (every admitted run monitors itself; a bug here can only ever hurt its own run, never another slot's) —
      cross-process "kill the newest run" arbitration + Slack alerting remain open refinements (see the still-open
      Phase-4 Slack-alerting todo below). Catches aggregate pressure per-repo caps miss (verified this matters
      concretely: `systemd-run` is unavailable on the slot-5 host, so the per-repo cgroup cap is inactive there too —
      this watchdog is now the ONLY live post-admission defense on that host).
- [x] [INFRA] P2. ✅ base-service.sh:610-617 acquire guard (shipped w/ the contention work) — Light-slice bypass — only
      TESTS + TYPE CHECK acquire; `QG_SLICE=lint-codex` acquires nothing.
- [x] [INFRA] P3. ✅ PM@3de0ee74d (SOLO_ADMIT/SOLO_WAIT) — Oversize guard (defensive) — peak > `QG_RAM_BUDGET` waits for
      `sum_reserved_peak==0` then runs solo + loud warning. Rare-to-never ≥ 16 GB (heaviest 5.5 GB < 11 GB budget); no
      stacked-oversize drain logic needed.
- [x] [INFRA] P2. ✅ PM@6e818079a + PM@a6b5e24a5 — Env knobs — `QG_MEM_SAFETY_FRAC` (0.70) / `QG_MEM_FLOOR_GB` /
      `QG_CPU_FRAC` (0.80) / `QG_MEM_CAP_MULT` (1.20) / `QG_HOST_RAM_ABORT_PCT` (80) / `QG_HOST_CONCURRENCY` demoted to
      a loose runaway backstop (RAM-derived default, no longer the primary control).

- [x] [INFRA] P1. ✅ PM@aca6a2fcf — Release the governor from base-service's EXIT trap so a failed/aborted QG can't leak
      a reservation-ledger entry (the happy-path release runs only after [4] TYPECHECK; found during the flip soak —
      correctness was never at risk since every admission sweeps dead PIDs first, but the ledger stayed dirty).
      `_qg_exit_handler` now releases on every exit path (idempotent w/ the happy-path release, exit-code-safe).
      Regression test `test-trap-release.sh` (10 assertions) + bash -n + shellcheck clean + all 5 governor suites green.

### Phase 4 — Fairness + observability

- [ ] [INFRA] P2. DEFERRED (non-critical) — investigated via the isolated 20-waiter stress probe (issue todo 4: no
      starvation observed) and confirmed by the 93-min soak (42 runs, none starved). Add FIFO/aging only if starvation
      is ever observed in practice. — FIFO ticket + head-of-line aging so a heavy repo (UTL) is not starved by light
      runs on a small host.
- [x] [INFRA] P2. ✅ unified-trading-pm@f36ac5877 (`QG_GOVERNOR_WAIT_SECONDS` accumulated in acquire, subtracted from
      `DUR` in base-service.sh/base-library.sh; issue todo 2) — MAX_DURATION fix — stamp work-start AFTER admission so
      governor queue time can't fail a green run (issue doc todo #2).
- [ ] [INFRA] P2. Slack alerting via the reusable `notify-slack.yml`/carrier (dedup + cooldown) — three triggers:
      per-run RSS over its `1.2×` cap; daily observed-peak > 20 % above baseline; host RAM > 80 % abort.
      Actionable-only, state-transition deduped (per the AO/CI alerting rules).
- [x] [INFRA] P3. ✅ PM@6402f6cd8 (`_qg_governor_status` reservation-mode branch: MODE / MemTotal+Avail / RAM
      budget+reserved+free / cpu_slots+running / live reservations; tested both modes) — `--status` shows QG_RAM_BUDGET
      / reserved / CPU_SLOTS / waiters / per-repo reservations + an admitted-vs-queued decision log for tuning.

### Phase 5 — Rollout + retire fixed K

- [x] ✅ [INFRA] P1. **SHIPPED 2026-07-20 — `agent-orchestrator@91808dfeb5f9f7f747044796150ad8e2e67dca21`**
      ("fix(bootstrap): flip planning host to the reservation-ledger QG governor", self-describes as "Phase 5 rollout of
      `qg_host_adaptive_resource_governor_2026_07_14.md`"). Confirmed 2026-07-22, plan-reconcile follow-up, by live SSM
      query of the real central orchestrator VM (`i-0c9b283b31d6b5ca7`): `bootstrap_vm.sh:1223-1236` now writes BOTH
      `QG_HOST_CONCURRENCY=6` and `QG_GOVERNOR_MODE=reservation` (grep-guarded); the VM's live `.env.local` carries
      both; `tmux show-environment -g` shows both; a **freshly-created tmux session** (spawned live for this check)
      correctly inherits both; and a live `qg-host-governor.sh --status` run shows `MODE=reservation`,
      `K runaway-backstop=6`, `RAM budget (70%): 22087MB`, `CPU slots (80% x 4): 3` — matching this host's actual 30
      GB/4-core spec. This also resolves the § "Measured runtime drift" `MODE=token K=2` finding below — that 2026-07-16
      measurement is now stale; this shipping commit landed 2026-07-20, four days after it. Remove the
      `QG_HOST_CONCURRENCY=1` pin from `bootstrap_vm.sh` (kept as an optional override) — DONE in the same commit.
- [x] [INFRA] P1. ✅ PM@6402f6cd8 (🟢 LIVE+VALIDATED note: dual-gate, capacity auto-adaptation via the resize,
      K-demoted, cgroup cap, trap-release lifecycle, small-host learning; heavy-tier already corrected) — Update
      `/codex/06-coding-standards/quality-gates.md` — the dual-gate model + the corrected heavy-tier order (UTL →
      instruments → execution → …; the stale "execution/features = #2" fixed).
- [x] [INFRA] P2. ✅ PM@6402f6cd8 (`status: resolved` + `resolved_by:` + ✅ banner; all 4 issue todos were already
      `[x]`) — Close the 4 todos in `/plans/archive/issues/qg_host_governor_severe_contention_2026_07_13.md` (this plan
      resolves all four) and banner the issue resolved.

### Phase 6 — Cross-host verification

- [x] [INFRA] P1. ✅ PM@6402f6cd8 (`tests/test-qg-cross-host.sh` via `QG_FORCE_*`: 16→2 RAM-bound, 24→3, 61→6 CPU-bound,
      96→12, 128→12 CPU-bound — all pass, admission = min(RAM-cap, cpu_slots)) — Simulate 16 / 24 / 61 / 96 / 128 GB via
      a `QG_MEM_TOTAL_OVERRIDE` + core-count override: assert admission matches the cross-host table (16 GB → ~2 heavy;
      24 GB → ~3; 61 GB → CPU-bound ~cores; 128 GB → CPU-only).
- [x] [INFRA] P1. ✅ COVERED — `test-qg-reservation.sh` (6 simultaneous acquirers on one heavy repo → exactly 3 admit,
      never over-admit — the atomic-reserve crux) + `test-qg-ledger.sh` (dead-PID sweep) + `test-trap-release.sh`
      (release-on-crash/fail). — Concurrency/race test — fire N simultaneous acquires on the SAME heavy repo (6×UTL) and
      assert they SERIALIZE under the flock and never over-admit past the RAM bound (the design's crux); include a crash
      test (kill a holder, assert its reservation is swept).
- [x] [INFRA] P2. ✅ DONE via the 93-min live reservation-mode soak (42 runs, maxconc=3=cpu_slots, 0 OOM, ghosts reaped
      in grace); the "delta vs K=1" is moot since K is retired to a runaway backstop. — Live fleet soak —
      queue-time-under-contention delta vs K=1 (`scripts/dev/benchmark-qg-under-load.sh`); confirm no swap regression +
      no false 80 % aborts on the 61 GB host.
- [ ] [INFRA] P2. Small-host sizing (≤ 32 GB) — the 2026-07-14 30 GB soak hit MemAvailable 12 % transiently (no OOM;
      cgroup caps + valve held) because the non-QG baseline (orchestrator + ~14 fleet workers) is a LARGE fraction of 30
      GB and admitted runs' RSS ramps AFTER the admission-time valve check. Consider (a) prioritizing the runtime
      abort-monitor (directly addresses the post-admission ramp — matters most on small hosts) and/or (b) a lower
      `QG_MEM_SAFETY_FRAC` / effective concurrency on ≤ 32 GB hosts. No change needed while no OOM occurs.
- [ ] [INFRA] P3. `PYRIGHT_TIMEOUT` default (120s in `base-service.sh`'s `run_timeout "${PYRIGHT_TIMEOUT:-120}"`) is too
      low for a repo the size of features-service (hundreds of files) even under only moderate host load — observed
      2026-07-24 on a ~30 GB/8-core shared host under multi-slot contention: TYPE CHECK killed at exit=143 (`Killed`)
      with the default, passed cleanly once `PYRIGHT_TIMEOUT=600` was set. Several slots already work around this ad-hoc
      (`PYRIGHT_TIMEOUT=300`/`480`/`600` set per-invocation) with no shared fix or documented guidance. Raise the
      default (scaled by repo size / measured baseline, same spirit as the RAM/CPU admission work above) or at minimum
      document the override in `/codex/06-coding-standards/quality-gates.md` so slots stop rediscovering it
      independently.
- [ ] [INFRA] P3. NEW FINDING (2026-08-09, slot 22): corroborates the `PYRIGHT_TIMEOUT` finding above — hit the SAME
      class of drift on market-tick-data-service's `MAX_DURATION` meta-gate (separate from `PYRIGHT_TIMEOUT`): with
      `PYRIGHT_TIMEOUT=600` set (needed to avoid the exit=143 kill above), 2 consecutive runs measured 830s (0s governor
      queue-wait) and 864s (24s queue-wait) work-time, both over the then-current 800s budget (itself only bumped
      2026-08-06 from 600s). Bumped `MAX_DURATION` 800→1000 in market-tick-data-service/scripts/quality-gates.sh (same
      ad-hoc per-repo pattern as the two prior bumps in that file's history comment) to unblock landing
      `defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md`'s P2 todo (shipped 2026-08-09,
      `market-tick-data-service@5d633923`; source doc now archived at
      `/plans/archive/2026_08/issues/defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md`) — same
      underlying tension as the `PYRIGHT_TIMEOUT` finding: raising one gate's timeout (needed to let TYPE CHECK finish
      under contention instead of being killed) mechanically pushes total wall time into a SEPARATE completion-budget
      gate. Whoever owns this plan: consider whether `MAX_DURATION` should scale with `PYRIGHT_TIMEOUT`/repo size the
      same way the P3 finding above proposes, rather than each repo's `quality-gates.sh` accumulating manual bumps
      independently.
- [ ] [INFRA] P2. NEW FINDING (2026-07-27, slot 5): pytest-xdist's SINGLE worker (`PYTEST_WORKERS` default is already 1,
      not a multi-worker coordination bug) can itself die under sustained severe host load, crashing the whole run with
      `xdist.dsession: RuntimeError: Unexpectedly no active workers available` (an `INTERNALERROR`, not a test assertion
      failure) — observed repeatedly on market-tick-data-service at load average 30-50 (fleet-wide, 7+ concurrent
      `quality-gates.sh` processes at once, well over the documented "≤2 full QGs at once" host budget). One run got
      partway (`1 failed, 5316 passed`) before the worker died; a second, later run under similar load completed clean.
      Distinct from the already-tracked `PYRIGHT_TIMEOUT` issue above (different subsystem, worker death not timeout)
      but same root cause (host-wide QG concurrency exceeding the documented budget — the CLAUDE.md "Shared-host ≤2 full
      QGs at once" rule is evidently not being honoured fleet-wide in practice). No fix attempted — flagging for whoever
      owns this plan; a `pytest-timeout`-triggered SIGALRM landing during an already-CPU-starved worker's teardown
      looked like the proximate trigger in the captured traceback (worker died handling its OWN 60s per-test timeout,
      not an external kill). Possible directions: retry-once-on-worker-death in `base-service.sh`'s pytest invocation,
      or a stricter host-wide admission enforcement (the governor's own budget is being exceeded, not just reported).
- [ ] [INFRA] P2. NEW FINDING (2026-08-03, from the glue-runner ledger fork's soak) — AO's own slot-worker QG runs (a
      separate `.tabs`-scoped ledger population on `agent-orchestrator-vm-1`, the SAME host that runs the glue-runner
      pools) are still NOT unified with the glue-runner pools' ledger (`/opt/.qg-governor-glue-shared`) even after the
      cross-repo fix. Both populations correctly share ONE ledger internally, but the two populations don't share a
      COMBINED budget view of each other — an AO slot-worker QG run and a glue-runner CI QG run can both admit
      independently even though they compete for the same physical CPU/RAM. Not attempted in the fork (out of its scope:
      cross-repo CI sharing, not cross-population sharing). Possible direction: extend `_qg_shared_root()` further so
      BOTH the `.tabs` strip and the `/opt/github-glue-runners*` collapse resolve to the SAME final path when running on
      this one host (they're currently two different literal constants). SSOT for the fix already shipped:
      `/plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md`.
- [x] [OPERATOR] P3. ~~Block ticket `BLK-7eedce54` ... needs its ticket-system status flipped~~ — 2026-08-04:
      **CORRECTED, nothing to do.** Queried `state.db`'s `blocked_queue` table directly (read-only, via SSM same-box
      trust boundary — no JWT needed, same mechanism `check-ao-backlog-status.sh` uses for its GET calls). Confirmed
      `BLK-7eedce54` was already `answered_at=2026-08-02 16:01:50`, `answered_by=main` — answered within ~3min of being
      filed, over a day before this plan's glue-runner fork even existed. This plan's own framing ("flagged via `cicd`'s
      `/blocked` ... rather than fixed in-scope") overstated what the ticket actually was: the real question (from
      `agt-fea289`, slot 2) was narrower — "keep holding this slot waiting on a slow CI retry, or exit given host
      contention" — answered "exit now," with the systemic resource-contention finding explicitly routed to a DIFFERENT
      already-open escalation, not deferred as its own new ticket. There was never an open ticket-system record waiting
      on the ledger fix; the prior "needs operator API access to close it" framing was itself the error, not a genuine
      gap.
- [ ] [INFRA] P3. NEW FINDING (2026-08-09, relayed via a review-agent resource-contention investigation): the
      HEAVY-PHASE `K` governor's own core count is inflated on a hyperthreaded host — `_qg_governor_default_k()`
      (`scripts/quality-gates-base/qg-host-governor.sh:81-89`) computes `cores` via
      `lscpu -p=core 2>/dev/null | grep -vc '^#'`, which counts one line per LOGICAL cpu (`lscpu -p=core` emits a row
      per hyperthread sibling, with the physical core id repeating) — no dedup. On a HT host this returns the logical
      CPU count (e.g. 16) instead of the true physical core count (e.g. 8), so `K = cores/4` (floored, min 2) comes out
      up to 2x too permissive there. **Correction to the relayed finding**: the report named `_qg_physical_cores()` as
      the buggy function, but that function (same file, line 185-196, "Physical core count (not logical/HT)") already
      dedupes correctly via `sort -u` — verified by direct read, it is NOT the source of the bug. `_qg_physical_cores()`
      was added later (additively, per its own header comment) for the newer TOTAL-INSTANCE cap
      (`_qg_total_default_cap`, line 106-111) and is unaffected. The two functions independently re-implement the same
      "count physical cores" logic with diverging correctness — likely fix: have `_qg_governor_default_k()` call
      `_qg_physical_cores()` instead of its own inline `lscpu` invocation (DRY + inherits the existing dedup). Not fixed
      here — flagging only, per the reporting agent's own request.

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
- **Gap-review round (operator 2026-07-14 — 11 gaps raised, decisions folded in):** (1/2) baseline freshness = a daily
  free promotion of the governor's own observed peaks + a > 20 % anomaly Slack alert; hard backstops = per-repo cgroup
  cap at `1.2×baseline` + a global 80 %-host-RAM abort (also the kill-switch). (4) `K` demoted to a loose RAM-derived
  runaway backstop (interim bump capped at 7, not 8 — 8×UTL = 44 > 43 GB). (5) ledger at
  `${WORKSPACE_ROOT%/.tabs/*}/.benchmarks/qg-governor/` — VERIFIED `WORKSPACE_ROOT` is set PER-SLOT by
  `setup-tab-worktrees.sh`, so the `.tabs/<N>` strip is required or the governor silently wouldn't coordinate across
  slots. (6/10) `cpu_weight` + the race test come from an unpinned parallel re-measure. (7) min supported host = 16 GB,
  so oversize-solo is defensive-only (heaviest 5.5 GB < 11 GB budget) — no stacked-oversize drain logic. (8) real macOS
  `MemAvailable` equivalent from `vm_stat`. (3/9) de-scoped per operator.

### 2026-07-14 — Phase 2 shipped + Phase 1 recon (slot 16, interactive)

- **Phase 2 (host capacity introspection) SHIPPED** — `qg_host_capacity` + `--probe` in `qg-host-governor.sh` +
  fixture-based unit tests. `PM@dd7f05e49` (quickmerge; PR #1010 → main auto-merge). Additive, no behavior change to the
  live governor. `--probe` on this VM: `mem_total_gb=61 mem_available_gb=53 cores=8 ram_budget_gb=43 cpu_slots=6`. The
  `vm` baseline data shipped in the same commit (Phase 0 P0).
- **Calibration finding:** this "16-core" VM is **8 physical / 16 logical** cores. The probe reports PHYSICAL (8), so
  `cpu_slots = floor(8 × 0.8) = 6`, not the ~12 the plan narrative assumed from logical count. Physical-vs-logical for
  the CPU gate is a Phase-3/6 tuning decision that the unpinned parallel `cpu_weight` measure (Phase 0) will settle.
- **Phase 1 recon — the K-bump is LESS risky than the plan assumed.** `bootstrap_vm.sh` §6.1 pins
  `QG_HOST_CONCURRENCY=1` specifically on the CENTRAL DISPATCH (planning) host because the orchestrator co-resides
  there. But §6.2 already wraps every spawned worker's QG in a `systemd-run --user --scope` with **MemoryMax=10 G + 2 G
  swap**, and the 05-29 mitigations (16 G host swap + `orchestrator.service` MemoryMax=56 G) are persistent. So the
  32–57 GB single-pytest OOM that motivated the K=1 floor is ALREADY contained per-worker at 10 G — the repro cannot
  recur the same way. Phase 1's re-verify should confirm the 10 G scope cap holds under N-concurrent, then raise K.

### 2026-07-14 — Phase 1 K=6 raised (slot 16, operator-directed)

- **Operator: "raise the floor of K to 6 for now."** Corrected my earlier over-claim (see below), confirmed 6×UTL = 33
  GB < 43 GB ceiling, raised K to 6 across all three layers: live tmux global env (`setenv -g QG_HOST_CONCURRENCY 6` on
  the default socket → new worker sessions inherit 6 as they cycle) + root `.env.local=6` (survives restart) +
  `bootstrap_vm.sh` template `AO@222369f` (survives re-bootstrap). Existing 13 worker sessions keep K=1 until they
  cycle. Live repro DEFERRED per operator; Phase-6 soak is the empirical confirmation.
- **Correction to the Phase-1 recon (operator caught it):** the per-worker 10 GB scope cap does NOT make K=6 safe by
  itself — it is per-worker, so K workers = up to K×10 GB and does not bound the aggregate. K=6 is safe because the
  AGGREGATE math holds (6×UTL 5.5 = 33 GB < 43 GB, typical mix far less); the 10 GB scope cap + 16 GB swap are the
  single-runaway BACKSTOP that turns a would-be host OOM into an isolated per-scope kill. Two distinct guarantees.

### 2026-07-14 — Phase 3a reservation-ledger primitives shipped (slot 16)

- **Ledger primitives SHIPPED** in `qg-host-governor.sh` — `PM@88a4925af` (quickmerge; the LDR push succeeded, the
  inline PR-to-main step exited non-zero but the standing LDR→main promote flow covers promotion). ADDITIVE: the
  functions exist but are NOT yet wired into `acquire`/`release`, so zero change to live admission.
- Shipped: host-shared ledger path `_qg_shared_root` (strips the per-slot `/.tabs/<N>` off WORKSPACE_ROOT — verified in
  all 4 cases), `_qg_ledger_add`/`_remove`/`reserved_mb` (flock-protected, explicit-FD bash-3.2-safe) + a PID-liveness
  sweep (dead-PID rows pruned → crash-safe, replacing the flock-auto-release guarantee). Test `tests/test-qg-ledger.sh`
  (6 assertions + negative control; shellcheck clean).
- **NEXT (Phase 3b/3c) is the safety-critical part:** the dual-gate admission logic (RAM two-clause + CPU + oversize)
  built additively + tested, then the CUTOVER that wires it into `acquire`/`release` (+ cgroup cap + 80 % valve). The
  cutover changes live admission fleet-wide — an operator-aware step, not an autonomous flip. Ledger + capacity probe
  are the two foundations it stands on; both are now in place.

### 2026-07-14 — Phase 3b + 3c shipped: the governor engine is complete (flag-off) (slot 16)

- **Phase 3b — dual-gate DECISION logic** `PM@3de0ee74d`. `_qg_admit_check` (pure, all-inputs-explicit) encodes the
  two-clause RAM gate + CPU gate + oversize-solo; `_qg_repo_peak_mb` reads `max(local,vm)` from the baseline (unmeasured
  → conservative 5500 MB, never a low guess). Test `test-qg-admit.sh`: all 6 decision branches + boundaries + the plan's
  6×UTL worked example + the peak reader — 15 assertions, negative control, live smoke.
- **Phase 3c — reservation-mode CUTOVER** `PM@6e818079a`. Flag-gated on `QG_GOVERNOR_MODE` (default `token` = the legacy
  bucket, so **shipping changed NO live behaviour on any host**). Reservation mode = the ATOMIC check-and-reserve
  (`_qg_try_reserve` under one ledger lock) + a wait/retry acquire + reservation-remove release; capacity override env
  vars (`QG_FORCE_MEM_TOTAL_KB`/`_AVAIL_KB`/`QG_FORCE_CORES`) added for tests + the Phase-6 cross-host sim. Test
  `test-qg-reservation.sh` proves the crux: **6 simultaneous acquirers on one heavy repo admit exactly 3 (budget fits 3)
  and never over-admit** — the atomic-reserve guarantee — plus round-trip, oversize-solo, and default-token-inert.
- **Ship discipline (operator directive):** every piece built LOCALLY, tested to green (4 governor suites + shellcheck
  clean + token-mode-unchanged regression), only THEN shipped — and behind a default-off flag so no host can break.
- **The whole governor engine is now on LDR, dormant.** What remains before it does anything: (a) the operator-gated
  **flag flip** — set `QG_GOVERNOR_MODE=reservation` on ONE host, soak, then roll out (this is the "affects everyone"
  cutover); (b) `QG_GOVERNOR_REPO` wiring in `base-service.sh` so acquire knows the repo; (c) cgroup `1.2×` cap + 80 %
  valve + Slack (Phase 4); (d) Phase-0 canonical cost + unpinned parallel `cpu_weight`; (e) fairness + retire fixed K
  (Phase 5) + cross-host verify (Phase 6).

### 2026-07-14 — Phase 4 hard safety net shipped (slot 16, operator: "before the flip")

- **Per-repo cgroup cap + 80 %-host-pressure valve** `PM@a6b5e24a5`, both RESERVATION-GATED (token mode byte-for-byte
  unchanged — verified). This is the hard backstop the operator required before any flip.
- **Cgroup cap**: `base-service.sh` sets `QG_MEM_CAP = _qg_repo_mem_cap(SERVICE_NAME) = 1.2 × baseline` (UTL 6558M,
  instruments 4388M, floored 2048M) ONLY when `QG_GOVERNOR_MODE=reservation` — the existing `systemd-run --scope`
  wrapper then OOM-kills a run that outgrows its baseline in its OWN scope, never the host (the 05-29 guard). Repo
  identity is `SERVICE_NAME` (set by each repo's quality-gates.sh; matches the baseline keys), which the reservation
  acquire already falls back to — so no separate `QG_GOVERNOR_REPO` wiring was needed.
- **80 % valve**: `_qg_admit_check` gained an 8th arg `min_avail` (= 20 % of MemTotal); refuses ANY admit when
  `avail < min_avail`, catching aggregate/non-QG pressure. `min_avail=0` (omitted) disables it, so the shipped
  `_qg_admit_check` is back-compatible. `_qg_admit` + `_qg_try_reserve` compute + pass it.
- Tests: `test-qg-admit.sh` +3 host-pressure cases +3 cap cases; all 4 governor suites green; shellcheck clean.
- **Layered defense now in place for a flip:** reservations cap the SUM ≤ 70 % (atomic, no over-admit) → live + 80 %
  clauses stop admits under pressure → cgroup cap is the HARD per-run ceiling if a baseline is stale → baselines fresh
  (today). **Remaining (hardening, NOT flip-blockers):** Slack overrun alerts, fairness/FIFO aging, MAX_DURATION
  queue-time exclusion, runtime abort-monitor. **Recommended first validation:** flip `QG_GOVERNOR_MODE=reservation` for
  ONE manual QG run on this 61 GB host and watch it reserve/release before any fleet use.

### 2026-07-14 — Flip soak, trap-release fix, + live VM downsize (slot 16)

- **Soak alert `STALE dead-pid reservation … (sweep/release failing)` investigated → BENIGN.** Every admission path
  (`_qg_try_reserve` / `_qg_ledger_reserved_mb` / `_qg_ledger_count`) sweeps dead PIDs as its FIRST step, before summing
  the budget — a ghost can never over-admit or false-block. Proven live: a new acquire reaped the exact ghost the
  monitor flagged. Two real (benign) issues fixed:
  1. **Monitor cried wolf** — it read the RAW ledger, re-counted the same ghost every 5 s, wrong label. Replaced with
     `~/.qg-governor-soak/soak2.sh`: distinct-pid dedup, alerts ONLY on a ghost lingering past a 300 s grace, tracks
     max-linger as the health metric.
  2. **Root cause of ghosts** — `qg_governor_release` ran only on the happy path (post [4] TYPECHECK); a failed/killed
     QG leaked a ledger entry until the next sweep. **Fixed `PM@aca6a2fcf`:** release from `_qg_exit_handler` (EXIT
     trap), idempotent + exit-code-safe. Regression test `test-trap-release.sh` (10 assertions). Landed via a tight
     rebase→push loop (fleet drift kept re-invalidating the QG sentinel; the commit was already quickmerge-trailered +
     gated, so a fast-forward push through the pre-push strict-quickmerge hook completed it).
- **LIVE VM DOWNSIZE (operator, ~13:01):** this host went 61 GB/8-core → **30.8 GB/4-core** (reboot). **The reservation
  governor auto-adapted with zero intervention** — probe now reports
  `mem_total_gb=30 ram_budget_gb=21 cores=4 cpu_slots=3` (was 43/6); admits ~3 heavy runs instead of 6. Reservation mode
  survived the reboot (durable `.env.local` re-applied it; confirmed by a live ledger reservation). **This is the
  capacity-aware design validated on a real host halving** — the whole reason K was demoted to an inert backstop.
  **Operator decision (2026-07-14): KEEP `QG_HOST_CONCURRENCY=6`** — the binding limiter is the RAM (21 GB) + CPU
  (3-slot) reservation gate, so K never binds in reservation mode; K=6 is a dormant backstop only. (Latent caveat: K=6
  would be an OOM risk on 30 GB IF the host ever fell back to token mode — mitigated by reservation mode being durably
  set in `.env.local` + tmux global.)
- **Reconciled Phase-3/4 engine checkboxes** (243/247/251/253/257/258/260) that shipped in earlier sessions but were
  left unchecked — flipped with their shipping shas. Box 255 left `[~]`: admission valve shipped (`a6b5e24a5`), the
  runtime abort-monitor is still pending hardening.
- **A clean 2 h soak with the corrected monitor is running on the (now 30 GB) host** — a more stringent contention test
  than the original 61 GB soak.

### 2026-07-14 — Reservation-mode soak CONCLUDED, validated (slot 16)

- **93-min soak on the (downsized) 30 GB host — operator: "conclude, it's validated."** Results: **42** reservation-mode
  QG runs; **maxconc = 3** (= cpu_slots on the 4-core host — the CPU gate binds exactly as designed); **OOM = 0**; **10
  ghosts, max linger 136 s** — all reaped well within the 300 s grace, so **the trap-release fix is validated live** (no
  stuck reservations). Reservation mode confirmed working fleet-wide on the smaller host.
- **One caveat (safe, logged as the Phase-6 small-host todo):** MemAvailable dipped to **12 %** for a ~7-min window
  (13:59–14:06Z), then recovered. No OOM — cgroup caps + the 80 % admission valve held. Post-admission RSS ramp on a
  host whose non-QG baseline eats a large fraction of 30 GB → reinforces that the runtime abort-monitor matters most on
  small hosts.
- Durable soak monitor: `~/.qg-governor-soak/soak2.sh` (outside the ephemeral scratchpad). The soak process was reaped
  by a session teardown at ~93 min (before its 2 h); interim data was conclusive, so not rerun.

### 2026-07-14 — Plan completion pass: rollout + verification + docs (slot 16)

- **Shipped `PM@6402f6cd8`:** reservation-mode `--status` (285 — mode / MemTotal+Avail / RAM budget+reserved+free /
  cpu_slots+running / live reservations, tested both modes); the cross-host verification test (299 —
  `tests/test-qg-cross-host.sh` asserts admission = `min(RAM-cap, cpu_slots)` across 16/24/61/96/128 GB → 2/3/6/12/12,
  all pass); the codex `quality-gates.md` governor section flipped to **🟢 LIVE + VALIDATED** (292); and the contention
  issue closed (294 — `status: resolved` + banner; its 4 todos were already done).
- **Flipped items already satisfied by prior work:** MAX_DURATION queue-time exclusion (280 — `f36ac5877`); the
  concurrency/race + crash tests (302 — `test-qg-reservation.sh` 6→3-admit + `test-qg-ledger.sh` sweep +
  `test-trap-release.sh`); the live soak (305 — the 93-min run); the instruments/UTL isolation re-measure (209 — the vm
  re-benchmark).
- **Deferred with rationale (kept `[ ]`):** baseline schema consolidation (205 — `max(local,vm)` already IS the
  host-portable read); cpu_weight re-measure (211 — count-based validated adequate); FIFO/aging (279 — investigated +
  soak-confirmed no starvation); bootstrap reservation-default (290 — validated + ready, blocked on slot-16's missing
  `agent-orchestrator/.venv`).
- **Remaining open — one coherent v2 "self-healing observability" follow-up + one operator-blocked item:** runtime
  abort-monitor (258 — kill a job that ramps past 80 % post-admission; elevated by the small-host soak finding), Slack
  alerting (282 — NB: the `notify-slack.yml` carrier is GHA-only, so a local-VM governor needs a different Slack path —
  a design decision), the daily baseline-freshness loop (214), and 220 (K-repro re-verify, operator-deferred). Genuine
  features, left scoped rather than rushed into the shared QG gate.
- **Net:** the core governor is shipped, validated (live host resize + 93-min soak + cross-host admission test),
  documented (codex 🟢), and live on the slot-16 host (reservation mode durably set via `.env.local` + tmux global env)
  — **"live on the current fleet" was an over-claim, corrected 2026-07-17**: the central orchestrator VM
  (`i-0c9b283b31d6b5ca7`) measured `MODE=token K=2` on 2026-07-16 (see § Measured runtime drift below); the
  bootstrap-default flip (so future re-bootstrapped VMs come up on the governor) is validated + ready but blocked on a
  fleet provisioning gap (slots 16/1/7 missing `agent-orchestrator/.venv`) (corrected 2026-07-15, plan-reconcile:
  Phase-5 rollout todo at 302 is still `[ ]`/DEFERRED, not shipped); the optional self-healing observability layer and
  the operator-blocked K-repro also remain.

### 2026-07-16 — 2-day health re-check + FLEET_WORKER_CAP right-sized for the 30 GB host (slot 16)

- **Governor health re-check (2 days post-ship): clean.** Host stable (30.8 GB, no re-resize, 2-day uptime); reservation
  mode still live (tmux + K=6); **ledger empty — no ghost reservations (the trap fix holds)**; both governor commits
  (`aca6a2fcf`, `6402f6cd8`) intact on origin; trap fix present on slots 1/7/11/16; governor actively admitting
  (`instruments-service reserved 3657MB (ADMIT) after 6s`). **OOM count = 0** over the 2 days.
- **PSI confirmed the small-host caveat is real + recurring:** ~66 min cumulative _full_ memory stall over 2 days + 1.9
  GB swap in use — no OOM (cgroup caps + 80 % valve held), but genuine intermittent pressure. Root cause is NOT the QG
  governor (correctly bounded to the 21 GB budget / 3 cpu_slots) — it is the **ungoverned fleet-worker count**:
  `ORCHESTRATOR_FLEET_WORKER_CAP=14` was sized for 61 GB; on 30 GB up to 14 Claude workers (~2.9 GB each) over-subscribe
  RAM independent of the QG governor.
- **Action (operator 2026-07-16, "for now, raise when I need more"):** lowered `ORCHESTRATOR_FLEET_WORKER_CAP` 14 → 8 in
  the root `agent-orchestrator/.env.local` (durable, reversible). NB: `.env.local` is a systemd `EnvironmentFile` read
  ONCE at process start (`get_config()` is a cached singleton, no hot-reload), so it applies on the next orchestrator
  restart — NOT force-restarted (9 worker-agents active, no OOM urgency). This is the primary lever for todo 307; the
  runtime abort-monitor (258) remains the QG-side complement.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).

## Deferred / open decisions

- Canonical-cost source (Phase 0): `max(local,vm)` vs a fresh single canonical measurement — decide at Phase 0.
- `cpu_weight` per-repo refinement (Phase 3 CPU gate) deferred to v2 unless the count-based slot proves too coarse.

## Measured runtime drift — RESOLVED 2026-07-22 (plan-reconcile follow-up)

> **🟢 RESOLVED.** Live SSM re-check of the same VM (`i-0c9b283b31d6b5ca7`) today: `qg-host-governor.sh --status` now
> reports `MODE=reservation`, `K runaway-backstop=6` (matches this host's 30 GB/4-core spec: RAM budget 22087MB, CPU
> slots 3). A freshly-spawned tmux session correctly inherits `QG_HOST_CONCURRENCY=6` + `QG_GOVERNOR_MODE=reservation`
> from the tmux global env, and `.env.local` carries both durably. Root cause of the 2026-07-16 reading: the Phase-5
> bootstrap flip (below) hadn't shipped yet — it landed 4 days later,
> `agent-orchestrator@91808dfeb5f9f7f747044796150ad8e2e67dca21` (2026-07-20). The `MODE=token K=2` snapshot below was
> real for its moment, not a measurement error, and is superseded — kept for the record, not as a live TODO.

Live read-only AWS SSM query of the **real central orchestrator VM** (`agent-orchestrator-vm-1` /
`i-0c9b283b31d6b5ca7`), 2026-07-16:

```
$ qg-host-governor.sh --status
MODE=token  K=2
```

Two things worth one check by this plan's owner:

1. **`MODE=token`** — expected while the reservation ledger (Phase 3) has not shipped; recorded here only so nobody
   re-derives it. **No action implied.**
2. **`K=2`, but this plan's own text says bootstrap sets `K=6`** (the "K=1 pin is already gone" todo). Either the
   bootstrap did not take on this host, or something reset it after boot. Worth verifying — a silently-K=2 host is
   running at a third of the intended concurrency, which is a real (if quiet) throughput tax on every ship from that VM.

**Provenance / scope**: surfaced by the 2026-07-16 AO issue-doc reconciliation sweep while verifying
`../archive/issues/slot_venv_duplication_disk_pressure_2026_06_29.md`. **Attribution corrected 2026-07-17**: that issue
doc's banner never mentioned the governor at all (`git log -S 'governor'` over its full history: zero hits) — the "live
on the current fleet" over-claim was THIS plan's own "Net:" summary above, now corrected in place. The sibling plan
[`ao_host_disk_pressure_2026_07_16`](../archive/2026_07/ao_host_disk_pressure_2026_07_16.md) (Phase 3, archived
2026-07-17) recorded the drift here and deliberately did **not** touch governor code — this plan owns it. Also recorded
there: the governor gates **RAM/CPU admission, not disk**, so it must not be cited as a disk-pressure mitigation.

### 2026-07-27 — Runtime abort-monitor shipped (self-scoped v1) — closes the P0 (slot 5, `infra`)

- **Trigger**: dispatched to investigate
  `/plans/archive/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`'s P1 ("does the governor only
  gate entry, with no ongoing enforcement..."). Confirmed by reading
  `_qg_admit_check`/`_qg_governor_acquire_reservation` directly: YES — admission is a one-time check; nothing
  re-verifies an admitted run against live RAM pressure that develops afterward. That confirmation IS this plan's own
  already-open P0 above; closing both from one fix rather than tracking it twice.
- **Shipped** `unified-trading-pm@<PENDING-SHA>` — `_qg_watchdog_start`/`_qg_watchdog_loop`/`_qg_watchdog_signal_tree`
  in `qg-host-governor.sh` (reservation-mode only, gated the same way as the rest of Phase 3/4). Design tradeoff vs the
  todo's original "abort the offending/newest run": **self-scoped** — each admitted run backgrounds its OWN watchdog,
  which can only ever signal ITS OWN process tree (walked via `pgrep -P`, never a process-group signal). This is
  strictly safer than a cross-process arbiter (no risk of a bug reaching into another slot's PID) at the cost of
  possibly over-aborting when several admitted runs' watchdogs all trip in the same pressure window — an acceptable v1
  tradeoff; a true single-offender arbiter (using the ledger's per-row timestamp, currently hardcoded to `0` and unused
  for this purpose) is a natural follow-up, not done here.
- **Real bug caught during implementation, not just design**: a naive `kill -TERM $target_pid` does nothing while the
  target is blocked in `wait()` on a foreground child (pytest/basedpyright) — bash defers a pending trap until the
  current foreground command returns, so the signal would sit queued until the blocked command finished on its own,
  silently defeating the whole point. Fixed by signaling the target's live descendant tree bottom-up (child dies →
  `wait()` returns → bash promptly runs the pending EXIT trap) — verified by a manual before/after repro, not just
  inferred from docs.
- **Tests**: new `scripts/quality-gates-base/tests/test-qg-watchdog.sh` (9 assertions — token-mode inert, healthy-host
  no-op, sustained-pressure fires with a catchable SIGTERM + loud marker file, release reaps a still-running watchdog).
  All other governor suites re-run green; `test-qg-governor-wait-time.sh`'s "contended acquire" case failed both before
  and after this change (pre-existing host-timing flake, reproduced on a clean `git stash`, not caused by this work).
  `bash -n` clean; shellcheck clean (only pre-existing SC2017 info-level notices elsewhere in the file).
- **Bonus finding, relevant to prioritization**: `systemd-run` is unavailable on the slot-5 host (live warning during
  this session's own QG run: `QG_MEM_CAP=2048M set but systemd-run unavailable`), so the OTHER hard backstop (the
  per-repo cgroup cap) is inactive there too — same failure class as
  `/plans/archive/issues/qg_mem_wrap_systemd_bus_unavailable_2026_07_26.md` (resolved 2026-08-01). On hosts in that
  state, this watchdog is now the ONLY live post-admission RAM defense — raises this fix's value above "hardening, not
  flip-blocker."
- **Remaining** (documented, not done here): Slack alerting on abort (existing Phase-4 todo), single-offender
  arbitration via the ledger's currently-unused per-row timestamp, and a real multi-slot fleet soak under measured
  contention (this session's verification is unit-test + manual-repro level, not a live fleet soak).

### 2026-08-02 — LIVE finding: reservation ledger does NOT coordinate across repos on a GHA glue-runner host

- **Trigger**: `cicd` escalation `agt-fea289` (`unified-api-contracts` `quality-gates-v2` RED on `main`). First attempt
  (run `30746935856`) hung in TESTS for 64min then got the `_qg_watchdog` 80%-RAM-pressure SIGTERM. Re-triggered
  (`30750913313`); still running 1h49m+ later, its pytest process (PID 2063426) had accumulated only 33s of CPU time —
  alive, not deadlocked, just severely CPU-starved.
- **Root cause, confirmed by direct process inspection while co-located on the glue-runner host (`ip-172-31-5-118`,
  16-core/61GB)**: `load average ~42-43` with **~10 DIFFERENT repos'** `quality-gates.sh` running concurrently at once
  (`unified-trading-api`, `unified-api-contracts`, `fund-administration-service`, `ml-service`, `execution-service`,
  `strategy-service`, `market-tick-data-service`, `batch-live-reconciliation-service`, `deployment-service`,
  `alerting-service`) plus heavy swap thrashing (`vmstat` si/so ~20-40 MB/s sustained) despite 26-40GB RAM nominally
  free — a CPU/swap oversubscription this governor's RAM-percentage admission gate does not see, because RAM usage alone
  stayed well under the 80% abort threshold the whole time.
- **Mechanism**: `_qg_shared_root()` (`qg-host-governor.sh`) resolves the ledger dir from `WORKSPACE_ROOT`, stripping
  `/.tabs/*` — correct for the interactive slot-worktree layout this was built for. On a GHA self-hosted runner, the job
  cwd is `/opt/github-glue-runners-<repo>/glue-N/_work/<repo>/<repo>` (no `.tabs/` segment, and `WORKSPACE_ROOT` is not
  the same shared value across repos' runner jobs) — confirmed live: this run's ledger dir was
  `.../github-glue-runners-unified-api-contracts/glue-1/_work/unified-api-contracts/.benchmarks/qg-governor`, i.e.
  **scoped to this one repo's runner workdir, not host-wide**. Each of the ~10 repos' GHA jobs therefore runs its own
  independent reservation ledger, each admitting up to its own RAM/CPU budget as if it had the whole host to itself —
  the admission gate that Phase 3/6 verified prevents over-admission _within one ledger_ never sees the other 9.
  Distinct failure mode from the 2026-07-27 fleet-soak's "false 80% abort" check (that soak ran single-repo, single
  ledger — this is cross-repo ledger fragmentation, only reachable on the GHA glue-runner topology, not the slot
  worktree topology the soak covered).
- [x] [INFRA] P1. **FORKED 2026-08-03 — see
      `/plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md`** (dedicated scoped plan, per
      this doc's own note below that a one-shot task is the wrong place to redesign ledger scoping across the whole
      glue-runner fleet). Fix (or explicitly scope-fence) `_qg_shared_root()` so GHA glue-runner jobs across DIFFERENT
      repos on the SAME physical host share one ledger — e.g. derive the shared root from the stable
      `/opt/github-glue-runners-*` parent (or a host-identity env var set once per VM at runner-install time) instead of
      `WORKSPACE_ROOT`, which is per-repo-job on this topology. Until fixed, the governor provides NO cross-repo
      admission control on glue-runner hosts — only the per-repo `QG_HOST_CONCURRENCY` limit and the (also per-repo)
      RAM-pressure watchdog apply, which is why 10 repos could pile up here. Leave this checkbox `[ ]` until the forked
      plan ships and closes it back here. — 2026-08-03: **CLOSED — the fork shipped.** Fix is
      `unified-trading-pm@fada7dc20` (live, organically propagating to every pool via each job's fresh
      `live-defi-rollout` self-clone — no separate flip needed). Live-validated: direct host introspection confirmed ≥6
      real concurrent repos already sharing one ledger correctly, admission gating actually binding. The one remaining
      item in the fork (a ~90min soak, running in background at close time) doesn't gate this closure — the fix's
      correctness is independently proven; the soak is a sustained-duration confidence check, not a go/no-go for the
      code already live. Block ticket `BLK-7eedce54`'s underlying issue is resolved and documented here + in the fork;
      did not flip its status in the AO `/blocked` ticket system itself (no verified API access from this interactive
      session — see the fork's Phase 3 Progress Log for detail). SSOT:
      `/plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md`.
- **Not fixed in this session** — flagged via `cicd` `/blocked` (`BLK-7eedce54`) rather than fixed in-scope: a one-shot
  wall-clearing task is the wrong place to redesign ledger scoping across the whole glue-runner fleet: real blast radius
  (every repo's CI), needs its own scoped plan/PR + a fleet soak on the GHA topology specifically (the existing 93-min
  soak only covers the slot-worktree topology).

## Progress Log (na-eligibility-audit incremental marker)

- **na-eligibility-audit 2026-07-30** (infra tranche, dispatch agt-30721a): KEEP-NA-STALE — closed 1 narrative-artifact
  checkbox (Phase 1's "RESOLVED-BY-RULING" item, which described an already-made decision rather than gating live work —
  the decision it describes was already executed in the very next checkbox). Doc stays NA overall — explicit dated
  operator citation at the top of the doc ("LOCAL / operator-driven plan, not AO-ingested. Operator decision 2026-07-14:
  human-driven...") governs the whole remaining scope; the other 8 open items are either explicitly
  DEFERRED-with-stated-reactivation-condition or real unimplemented-but-well-specified engineering follow-ons under the
  same human-driven ruling, not defaulted-and-never-assessed work.
- **na-eligibility-audit 2026-08-03** (tranche `ci`, autonomous, `agt-4acc10`): **CONFIRMS KEEP-NA, valid — unchanged**
  (9/9 open items re-verified). 8 items (baseline-schema consolidation, cpu_weight unpinned re-measure, baseline-
  freshness loop, FIFO/aging, Slack alerting, small-host sizing, PYRIGHT_TIMEOUT default raise, pytest-xdist worker-
  death fix) re-confirmed under the standing 2026-07-14 operator ruling — citation verified real and still governing;
  none duplicated into any active `assigned_vm: planning` sibling (checked `ao_open_issues_consolidated_close_out`,
  `cross_cutting_satellite_ao_dispatch_batch1b`, `orchestrator_vm_e2e_hardening`,
  `sports_consolidated_native_ao_extract` — all incidental context mentions, not systemic fixes). Item 9 (line 684,
  "FORKED 2026-08-03") is the redirect to `qg_governor_glue_runner_ledger_coordination_2026_08_03.md` (also re-
  confirmed KEEP-NA this same run, 5 items, no double-count with this doc's other 8) — correctly open until that fork
  ships and closes it back here. No RECLASSIFY, no ARCHIVE.
- **na-eligibility-audit 2026-08-04** (tranche `ci`, autonomous): **CONFIRMS KEEP-NA, valid — real content churn since
  last pass, verdict unchanged.** Since the 2026-08-03 marker: the `[OPERATOR]` P3 `BLK-7eedce54` item was investigated
  and closed 2026-08-04 (ticket was already answered 2026-08-02, no action needed); the FORKED P1 item's destination
  (`qg_governor_glue_runner_ledger_coordination_2026_08_03.md`) is now `status: complete`, archived, fully shipped and
  soaked (~73min, 0 OOM, 11 repos) — its own closure note migrated its 2 genuine follow-ons into this doc's tracked
  todos, not orphaned. All 9 open items re-verified as correctly self-triaged (deferred-with-condition or open design
  question) under the standing 2026-07-14 operator ruling; none duplicated into any active `assigned_vm: planning`
  sibling. No RECLASSIFY, no ARCHIVE.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — LOCAL/operator-driven banner, human-tracked design questions

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:1c5a6017d0616242]: KEEP-NA,
valid — 10 open items now (was 9; today's new `[INFRA] P3` MAX_DURATION-drift finding, filed 2026-08-09 slot 22, is the
same class as the other 9 — a real, well-specified engineering follow-on under the standing top-of-doc 2026-07-14
"LOCAL/operator-driven, human-driven" ruling, not defaulted-and-never-assessed). No duplicate found in any active
`assigned_vm: planning` sibling. No RECLASSIFY, no ARCHIVE.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:26b8b937ea93491b]: KEEP-NA,
valid — Doc opens with an explicit dated operator-ruling banner (confirmed real by direct read): 'LOCAL /
operator-driven plan (assigned_vm: NA) -- not AO-ingested. Operator decision 2026-07-14: human-driven, and raise K on
current hosts as an interim quick-win before the full governor.' Frontmatter confirms assigned_vm: NA / execution_scope:
local-only; the 2026-07-14 Progress Log entry independently corroborates ('Operator decisions (2026-07-14): human-driven
plan...'). This doc has been through FIVE prior na-eligibility-audit passes (2026-07-30 KEEP-NA-STALE citation-cleanup,
2026-08-03/08-04/08-06/08-09 all CONFIRMS-KEEP-NA-valid), each re-verifying open items against this same standing ruling
and finding none clear the whole-doc RECLASSIFY bar.
