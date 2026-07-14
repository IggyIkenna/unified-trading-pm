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

- [ ] [OPERATOR] P0. Review + ship the `vm` baseline written to `scripts/dev/qg_resource_baseline.json` (22 repos,
      uncommitted in slot 16) to LDR — data-only file change.
- [ ] [INFRA] P1. Consolidate the baseline schema to a host-portable canonical per-repo cost the governor reads (RSS +
      cpu_s are host-invariant per finding #1) — keep `local`/`vm` as provenance; governor reads `max(local,vm)`
      (conservative) or a fresh canonical run. Unmeasured repo → conservative default (e.g. 2 GB) + a WARN to profile
      it, never a free pass.
- [ ] [INFRA] P1. Re-measure instruments-service AND unified-trading-library in isolation (instruments jumped +182 %;
      confirm it is real growth, not measurement contention from the live-workspace sweep) and refresh their baseline.
- [ ] [INFRA] P1. Measure per-repo CPU demand under the profiler's UNPINNED `--parallel` mode (real config, no
      single-core/thread caps) to get PEAK concurrent cores per repo → feed `cpu_weight` for the CPU gate. The
      single-core-pinned baseline can't see this (basedpyright + pytest burst multi-core).
- [ ] [INFRA] P1. Baseline freshness loop — the governor records each run's observed peak tree-RSS; a DAILY job promotes
      observations → the committed baseline (free — we already run every repo's QG most days). A single-run observed
      peak > 20 % above baseline → Slack alert (NOT a silent bump; a +182 %-style jump means something is wrong).

### Phase 1 — Interim quick-win: raise K on 61 GB hosts (operator-approved 2026-07-14)

- [ ] [INFRA] P0. Re-verify the 2026-05-29 swap-incident repro does NOT recur at higher K on a 61 GB host (drive N
      concurrent heavy QG runs; watch `free -h` swap-in rate + load) — the issue doc requires this before touching the
      floor. Capture evidence.
- [ ] [INFRA] P0. Raise `QG_HOST_CONCURRENCY` on 61 GB fleet hosts from 1 to `floor(0.7×RAM / heaviest-single-run-RSS)`
      = floor(43 / 5.5) = **7** (use **6** for margin — NOT 8: 8×UTL = 44 GB > the 43 GB ceiling) in
      `agent-orchestrator/scripts/bootstrap_vm.sh` + live `.env.local`; measure the fleet queue-time drop. (Interim —
      once the gates land in Phase 3, K loosens to the runaway backstop, RAM-derived per host.)

### Phase 2 — Host capacity introspection (portable)

- [ ] [INFRA] P1. `qg_host_capacity` in `qg-host-governor.sh`: emit MemTotal + MemAvailable + physical cores — Linux
      (`/proc/meminfo`, `lscpu -p=core`/`nproc`) AND macOS (`sysctl hw.memsize`/`hw.physicalcpu`; a REAL MemAvailable
      equivalent from `vm_stat` — (free + inactive + purgeable + file-backed) × pagesize, net of the compressor — not a
      raw "free"); bash 3.2-safe. Add `--probe` printing detected capacity + derived RAM/CPU budgets.
- [ ] [INFRA] P2. Unit tests for the capacity parser on captured Linux + macOS `/proc/meminfo`/`vm_stat` fixtures (no
      live-host dependence).

### Phase 3 — Reservation ledger + dual-gate admission

- [ ] [INFRA] P1. Reservation ledger (replaces the K-token bucket) at the HOST-SHARED path
      `${WORKSPACE_ROOT%/.tabs/*}/.benchmarks/qg-governor/` (strip the per-slot `.tabs/<N>` suffix — raw
      `WORKSPACE_ROOT` is per-slot, which would silently break cross-slot coordination); flock-protected; PID-liveness
      sweep prunes dead reservations.
- [ ] [INFRA] P1. RAM gate — TWO independent clauses (never a single `min()`): (1) reservation bound
      `sum_reserved_peak + this_repo_peak ≤ QG_RAM_BUDGET` (caps stacking of same/mixed heavy repos — the 6×UTL case);
      (2) live backstop `MemAvailable ≥ this_repo_peak + QG_MEM_FLOOR` (external pressure + climb headroom). Per-repo
      peak from the canonical baseline; unmeasured → conservative default. Check-and-reserve ATOMIC under one flock.
- [ ] [INFRA] P1. CPU gate — `running_weight + this_cpu_weight ≤ floor(cores × QG_CPU_FRAC)`, `cpu_weight` from the
      Phase-0 unpinned parallel measure (peak concurrent cores), NOT a flat 1-per-run.
- [ ] [INFRA] P1. Per-repo cgroup cap — wrap each admitted run at `QG_MEM_CAP = 1.2 × baseline_peak` (existing
      base-service hook, currently 0/off) so a runaway/mis-measured run is OOM-killed in its OWN cgroup, not the host.
- [ ] [INFRA] P0. Global 80 % valve + kill-switch — if live host used-RAM crosses 80 %, ABORT the offending/newest run +
      Slack-alert. Catches aggregate pressure per-repo caps miss; doubles as the fast rollback.
- [ ] [INFRA] P2. Light-slice bypass — only TESTS + TYPE CHECK acquire; `QG_SLICE=lint-codex` acquires nothing.
- [ ] [INFRA] P3. Oversize guard (defensive) — peak > `QG_RAM_BUDGET` waits for `sum_reserved_peak==0` then runs solo +
      loud warning. Rare-to-never ≥ 16 GB (heaviest 5.5 GB < 11 GB budget); no stacked-oversize drain logic needed.
- [ ] [INFRA] P2. Env knobs — `QG_MEM_SAFETY_FRAC` (0.70) / `QG_MEM_FLOOR_GB` / `QG_CPU_FRAC` (0.80) / `QG_MEM_CAP_MULT`
      (1.20) / `QG_HOST_RAM_ABORT_PCT` (80) / `QG_HOST_CONCURRENCY` demoted to a loose runaway backstop (RAM-derived
      default, no longer the primary control).

### Phase 4 — Fairness + observability

- [ ] [INFRA] P2. FIFO ticket + head-of-line aging so a heavy repo (UTL) is not starved by light runs on a small host.
- [ ] [INFRA] P2. MAX_DURATION fix — stamp work-start AFTER admission so governor queue time can't fail a green run
      (issue doc todo #2).
- [ ] [INFRA] P2. Slack alerting via the reusable `notify-slack.yml`/carrier (dedup + cooldown) — three triggers:
      per-run RSS over its `1.2×` cap; daily observed-peak > 20 % above baseline; host RAM > 80 % abort.
      Actionable-only, state-transition deduped (per the AO/CI alerting rules).
- [ ] [INFRA] P3. `--status` shows QG_RAM_BUDGET / reserved / CPU_SLOTS / waiters / per-repo reservations + an
      admitted-vs-queued decision log for tuning.

### Phase 5 — Rollout + retire fixed K

- [ ] [INFRA] P1. Remove the `QG_HOST_CONCURRENCY=1` pin from `bootstrap_vm.sh` (keep the env as an optional override);
      retire the Phase-1 interim bump onto the governor.
- [ ] [INFRA] P1. Update `codex/06-coding-standards/quality-gates.md` — the dual-gate model + the corrected heavy-tier
      order (UTL → instruments → execution → …; the stale "execution/features = #2" fixed).
- [ ] [INFRA] P2. Close the 4 todos in `issues/qg_host_governor_severe_contention_2026_07_13.md` (this plan resolves all
      four) and banner the issue resolved.

### Phase 6 — Cross-host verification

- [ ] [INFRA] P1. Simulate 16 / 24 / 61 / 96 / 128 GB via a `QG_MEM_TOTAL_OVERRIDE` + core-count override: assert
      admission matches the cross-host table (16 GB → ~2 heavy; 24 GB → ~3; 61 GB → CPU-bound ~cores; 128 GB →
      CPU-only).
- [ ] [INFRA] P1. Concurrency/race test — fire N simultaneous acquires on the SAME heavy repo (6×UTL) and assert they
      SERIALIZE under the flock and never over-admit past the RAM bound (the design's crux); include a crash test (kill
      a holder, assert its reservation is swept).
- [ ] [INFRA] P2. Live fleet soak — queue-time-under-contention delta vs K=1 (`scripts/dev/benchmark-qg-under-load.sh`);
      confirm no swap regression + no false 80 % aborts on the 61 GB host.

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

## Deferred / open decisions

- Canonical-cost source (Phase 0): `max(local,vm)` vs a fresh single canonical measurement — decide at Phase 0.
- `cpu_weight` per-repo refinement (Phase 3 CPU gate) deferred to v2 unless the count-based slot proves too coarse.
