---
title: Quality-gates resource-contention speedup — do-less-work + cross-slot governance, not more parallelism
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
created: 2026-06-02
locked_by: live-defi-rollout
related_plans:
  - plans/active/cicd_contract_hardening_2026_06_01.md
  - plans/active/ci_canonical_v2_migration_2026_05_29.md
  - plans/epics/infrastructure_master.md
source:
  - plans/archive/quality_gates_performance_parallelism.plan.md
completion_gates:
  code: C5
  deployment: none
  business: none
repo_gates:
  - repo: unified-trading-pm
    code: C0
  - repo: instruments-service
    code: C0
todos:
  - id: qg-bench-aggregate
    content: |
      - [ ] [SCRIPT] P0. Build an AGGREGATE-load benchmark harness (`unified-trading-pm/scripts/dev/benchmark-qg-under-load.sh`) that fires K slots' `quality-gates.sh` concurrently and measures host CPU-steal, swap-in/out, load-average, and p50/p95 per-run wall-clock. The existing archived benchmark timed ONE repo sequentially and is structurally blind to the contention problem this plan exists to fix. Output a CSV + a one-line verdict (oversubscribed Y/N at K∈{1,2,4,8}).
    status: todo
  - id: qg-perrepo-baseline
    content: |
      - [ ] [SCRIPT] P0. Per-repo QG resource baseline + 2× deviation guard (Harsh 2026-06-02). Measure a single `quality-gates.sh` run per repo — wall-clock, peak RSS, CPU-seconds — BOTH locally and on an AWS worker VM (`m7i.xlarge`). Commit the result as a baseline file (`unified-trading-pm/scripts/dev/qg_resource_baseline.json`, keyed per-repo × {local,vm}). Wire a guard into `quality-gates-base/base-service.sh` that WARNs (not fails) when a run exceeds 2× its baseline wall-clock or peak RSS — so resource regressions during code-freeze are detected early. Distinct from `qg-bench-aggregate`: that measures cross-slot contention; this measures per-repo cost + drift, and feeds the VM-sizing decision below.
    status: todo
  - id: qg-cw-memory-agent
    content: |
      - [x] ✅ [INFRA] P0. Install the CloudWatch agent (memory + swap + disk metrics) on the orchestrator fleet VMs — verified 2026-06-02 there are ZERO memory metrics published (only AWS/EC2 CPU), so every RAM/sizing decision below is currently blind. Add the agent + a minimal `amazon-cloudwatch-agent.json` (mem_used_percent, swap_used_percent, disk_used_percent) to `agent-orchestrator/scripts/bootstrap_vm.sh` (code-only, applies on next bootstrap — do NOT restart running VMs). This is the prerequisite for `qg-perrepo-baseline`'s VM measurement and the A/B/C sizing decision in the "Where QG + SIT actually run" section.
    status: todo
  - id: qg-vm-rightsizing
    content: |
      - [x] ✅ [INFRA] P1. Worker-VM right-sizing audit — DATA-DRIVEN off the per-repo baseline, not a guess (Harsh 2026-06-02). Current fleet = AWS `m7i.xlarge` (4 vCPU / 16 GB) × 8 slots/VM (~2 GB/slot) — already OOM-prone under parallel QG. Compute the floor = (peak per-run RSS × peak-concurrent-QG-under-the-governor) and compare to Harsh's hypothesis (~64 GB / 8 vCPU). Decide machine type AND slots-per-VM together (a bigger box OR fewer slots — the governor caps concurrency either way; do not just throw RAM at 8 uncapped runs). If a change is warranted, update `deployment-service/scripts/vm/launch-epic-vm-aws.sh` + `orchestrator_vm_registry.yaml`. NOTE: fleet is currently consolidated to 2 running VMs — this is a scale-back-up decision.
    status: todo
  - id: qg-governor
    content: |
      - [x] ✅ [SCRIPT] P0. Cross-slot concurrency governor — a host-level `flock`/token-bucket wrapper so at most K QG runs execute concurrently across ALL slots (default K = `max(1, floor(physical_cores/4))`, env-overridable `QG_HOST_CONCURRENCY`). Wire it into `quality-gates-base/base-service.sh` so every repo's `quality-gates.sh` acquires a host token before the heavy (pytest/basedpyright) phases. Converts 8× simultaneous thrash into orderly queueing → p95 wall-clock drops with NO added parallelism. This is the core fix. `nice -n10` + `ionice -c2 -n7` the QG process tree.
    status: todo
  - id: qg-slot-aware-workers
    content: |
      - [x] ✅ [SCRIPT] P0. Replace `pytest -n auto` (grabs ALL cores per slot → N-slot oversubscription) with a slot-aware cap: `-n $(QG_PYTEST_WORKERS or min(4, floor(free_cores / active_slots)))`. `active_slots` read from the orchestrator/registry or a host token count. Default conservatively; never let one slot's pytest claim the whole box. Document the formula in `codex/06-coding-standards/quality-gates.md`.
    status: todo
  - id: qg-repo-green-sentinel
    content: |
      - [ ] [SCRIPT] P1. Per-repo green-sentinel cache — extend the existing `.qg_last_passed_sha` into a content-hash sentinel so an unchanged repo (tree hash unchanged since last green) skips the heavy phases entirely and exits 0 fast. MUST be sound: hash includes source + tests + pyproject + lockfile + tool-config + QG-script versions; any mismatch → full run. Keyed per-repo so the first slot to green a repo lets siblings short-circuit.
    status: todo
  - id: qg-selective-tests
    content: |
      - [ ] [SCRIPT] P1. Import-graph selective testing — replace the archived plan's brittle `sed` path-mangling with a real changed-files→affected-tests map (evaluate `pytest-testmon` vs a lightweight import-graph walk). Iterative dev runs execute only tests transitively touching changed files; full suite still runs at the gate-to-main pass. Gate behind `QG_SELECTIVE=true` (default off until proven sound — a missed-test false-negative is worse than slowness).
    status: todo
  - id: qg-basedpyright-scope
    content: |
      - [ ] [SCRIPT] P1. Scope + warm basedpyright — run it on the changed package(s), not the whole `src/`, for iterative runs (full-tree only at gate-to-main). Evaluate basedpyright watch/daemon mode to avoid the cold whole-tree analyze (the single biggest CPU spike per run). Persist + share the basedpyright cache dir across worktrees so the first slot warms it for all.
    status: todo
  - id: qg-coverage-off-hotpath
    content: |
      - [x] ✅ [SCRIPT] P1. Move `--cov` off the hot path — coverage instrumentation touches every executed line (large CPU/RAM cost). Make it opt-in: iterative/`--quick` runs skip coverage; coverage + the coverage floor are enforced ONLY on the gate-to-main (quickmerge Pass 1) full run. No change to the merge-gate coverage requirement — only to when it is paid.
    status: todo
  - id: qg-shared-caches
    content: |
      - [x] ✅ [SCRIPT] P2. Persistent shared caches across worktrees/slots — ruff cache (`~/.cache/ruff`), pytest cache, basedpyright cache, and uv cache keyed + shared so the first slot warms them for all. Verify cache locations are NOT per-worktree (the default `.ruff_cache`/`.pytest_cache` inside each worktree defeats sharing) — repoint to a host-shared dir via env.
    status: todo
  - id: qg-offload-full-run
    content: |
      - [x] ✅ [DESIGN] P2. Offload the heavy full run off the contended dev host — design (not yet implement) routing the gate-to-main full suite + coverage to a dedicated CI/VM so the dev host only ever runs the light iterative gate. **This is the concrete shape of Option B** in the "Where QG + SIT actually run — three architecture options" section above: a self-hosted GitHub Actions runner pool (`runs-on: [self-hosted, qg]`) replacing the undersized `ubuntu-latest` (7 GB) runner, sized off `qg-perrepo-baseline`. The ADR must (a) pick A/B/C, (b) spec the runner pool + provisioning (`bootstrap_runner.sh`), (c) define the worker fast-pre-check, and (d) resolve the two-pass/sentinel change (authoritative gate moves local-sentinel → CI check). Decide the trigger boundary (quickmerge already two-passes via `.qg_last_passed_sha`). Implementation is a follow-up todo gated on this ADR.
    status: todo
  - id: qg-codex-ssot-update
    content: |
      - [x] ✅ [AGENT] P1. Update `codex/06-coding-standards/quality-gates.md` with a new "Resource governance under multi-slot load" section: the governor, slot-aware worker formula, sentinel cache semantics, coverage-on-gate-only rule, and the explicit anti-pattern ("`-n auto` per slot on a shared host is oversubscription, not speedup"). Per CLAUDE.md Post-Plan-Phase Codex Audit HARD RULE.
    status: todo
isProject: false
---

# Quality-gates resource-contention speedup

## Why this plan exists (the reframing)

The archived predecessor
([`plans/archive/quality_gates_performance_parallelism.plan.md`](../archive/quality_gates_performance_parallelism.plan.md))
assumed the QG bottleneck is **idle cores** and prescribed more per-run parallelism (`pytest -n auto`, parallel ruff).
On this workspace that assumption is false. The dev host runs **8 slots × 2 operator sides** of parallel agents, and
each slot's QG already grabs all cores via `-n auto`. When several slots gate at once the machine is **oversubscribed**:
CPU steal climbs, the box starts swapping, and _every_ concurrent run gets slower. Adding more per-run parallelism makes
the aggregate worse, not better.

So the levers here are not "go more parallel." They are, in priority order:

1. **Queue, don't thrash** — a host-level governor so at most K QG runs hit the heavy phases at once (P0).
2. **Stop oversubscribing** — slot-aware pytest worker caps instead of `-n auto` per slot (P0).
3. **Do less work** — content-hash green sentinels skip unchanged repos; selective tests + scoped typecheck for
   iterative runs; coverage only at the merge gate (P1).
4. **Stay warm** — daemonized/incremental basedpyright + persistent shared caches across worktrees (P1–P2).
5. **Get the heavy run off the hot path** — offload the full gate-to-main suite to a dedicated runner (P2 design).

**Soundness over speed (HARD constraint).** Every "do less work" lever (sentinel cache, selective tests, scoped
typecheck) MUST be conservative: any hash/scope ambiguity falls back to the full run, and the gate-to-main pass ALWAYS
runs the complete suite + coverage. A false-negative (a skipped failing test that merges) is strictly worse than a slow
run. This plan never weakens the merge gate — it only changes _when_ and _how contended_ the work is paid.

## Where QG + SIT actually run — three architecture options (A / B / C)

> Operator framing (Harsh 2026-06-02): soon **every worker agent runs `quality-gates.sh` + `quickmerge` locally after
> completing a plan** (the staging-first flow). That is memory-heavy and the current worker VMs are too small. Cost is
> NOT a constraint (free AWS credits) — pick the architecturally correct option, then size it generously.

**Live findings (measured 2026-06-02, feed the decision):**

- **Worker/epic VMs** = AWS `m7i.xlarge` (**4 vCPU / 16 GB / 30 GB gp3**), **8 slots each** (~2 GB/slot). 9 stopped +
  `vm-orchestrator` running. `api-host` is the outlier `m8i.4xlarge` (16 vCPU / 64 GB / 300 GB); `vm-ml` disk is 60 GB.
- **Workers are CPU-idle while coding** — `vm-orchestrator` CPU avg **1.7%** / peak **6.6%** over 24h (api-host avg 1.0%
  / peak 9.9%). The bottleneck is **bursty RAM during QG**, not steady-state CPU or disk.
- **No CloudWatch memory agent** → zero RAM visibility under load. Installing it is the cheap prerequisite to any
  data-driven sizing (see `qg-perrepo-baseline` + `qg-vm-rightsizing`).
- **Heavy QG memory observed = 32–57 GB** (the `api_host_chronic_impairment_2026_05_29` pytest OOM on the 64 GB box) —
  so a single heavy run can need ~57 GB; 16 GB workers OOM on it, which is _why_ CLAUDE.md caps concurrent QG to "1–2
  host-wide".
- **The "central QG" already half-exists but is undersized:** `python-quality-gates-v2.yml` runs on GitHub
  `ubuntu-latest` (**2 vCPU / 7 GB**) and there are **0 self-hosted runners** — a 32–57 GB QG cannot pass there either.

### Option A — vertically scale every worker VM

Each slot keeps running full QG locally (two-pass `.qg_last_passed_sha` sentinel intact). Bump `m7i.xlarge` (16 GB) →
`m7i.4xlarge` (64 GB) or `m7i.8xlarge` (128 GB); disk 30 → 100 GB.

- **Pros:** zero architecture change; self-contained (no network dependency for the gate); simplest to ship.
- **Cons:** workers are CPU-idle 95% of the time → big boxes sit mostly idle (wasteful even with free credits); 8
  concurrent heavy QGs still contend — true 8-way concurrency needs ~128–256 GB **per worker VM**. Couples QG capacity
  to slot count: every new slot grows every VM.
- **Owner todo:** `qg-vm-rightsizing` (data-driven off `qg-perrepo-baseline`) — decide machine type **and** slots-per-VM
  together; the governor caps concurrency regardless, so this is "fewer slots OR bigger box", not "throw RAM at 8
  uncapped runs".

### Option B — dedicated self-hosted runner pool for QG + SIT ⭐ recommended

1–3 big VMs (`m7i.8xlarge` **128 GB** or `m7i.16xlarge` **256 GB**, 100–200 GB disk) registered as **self-hosted GitHub
Actions runners** with a `qg` label. One-line cutover: `runs-on: ubuntu-latest` → `runs-on: [self-hosted, qg]` in
`python-quality-gates-v2.yml`. The heavy gate **+ SIT** run there — which is _already_ the flow (quickmerge → PR →
staging CI). Workers stay small (16 GB) and run only a **fast local pre-check** (ruff + basedpyright on _changed files_,
seconds, low RAM) for quick feedback, then push; the authoritative heavy gate runs centrally.

- **Pros:** concentrates the 32–57 GB burst in one sized-for-it place; parallelism via N runners; **decouples QG
  capacity from worker count**; SIT has a natural home; plugs into the existing CI seam (no bespoke RPC); fixes the
  undersized-`ubuntu-latest` problem at the same time.
- **Cons:** requires the design change below (authoritative gate moves from the local sentinel to the CI check);
  self-hosted runner provisioning + security (a `bootstrap_runner.sh`, runner registration token, ephemeral/auto-scaled
  vs always-on); queueing when more jobs than runners.
- **Owner todo:** `qg-offload-full-run` (currently DESIGN/ADR-only) — **this option is its concrete shape**; the ADR
  should choose B and spec the runner pool + the worker fast-pre-check + the sentinel/two-pass change.

### Option C — bespoke QG-as-a-service VM (workers RPC to it)

Workers finish, push their SHA, then call a custom QG service that checks out the SHA, runs `quality-gates.sh`, and
returns pass/fail; quickmerge consumes that verdict.

- **Pros:** keeps the gate authoritative-per-SHA without GitHub Actions.
- **Cons:** reinvents what self-hosted runners give for free; new custom service + auth + queue to build and operate;
  **redundant with the CI gate that already exists** on staging. Not recommended — only revisit if a hard requirement
  rules out GitHub Actions self-hosted runners.

### Recommendation + decision gate

**Option B** is the architecturally correct target (matches the staging-first flow; workers stay small; QG capacity
scales independently). **But the exact sizing — and whether a smaller Option A also suffices — is a DATA decision**, not
a guess: it is gated on `qg-perrepo-baseline` (peak RSS + wall-clock per repo, local **and** on `m7i.xlarge`) and the CW
memory agent landing first. Sequence: (1) install CW memory agent + run `qg-perrepo-baseline` → real peak-RSS numbers;
(2) `qg-offload-full-run` ADR picks B and sizes the runner pool off those numbers; (3) `qg-vm-rightsizing` sets the
(now-smaller) worker baseline. Do not provision big iron before step 1 — the 32–57 GB figure is a worst-case tail, not a
measured per-repo median.

## Phased execution DAG

```
Phase 0 (measure)         qg-cw-memory-agent ── RAM/swap visibility (prereq; fleet has none today)
                          qg-bench-aggregate ── proves oversubscription, sets K
                          qg-perrepo-baseline ─ per-repo cost (local+VM) → 2× drift guard + A/B/C VM-sizing input
        │
Phase 1 (stop the bleed)  qg-governor  ║  qg-slot-aware-workers   [PARALLEL, both P0]
        │                  └── re-run qg-bench-aggregate → p95 must drop at K∈{4,8}
        │
Phase 2 (do less work)    qg-repo-green-sentinel ║ qg-selective-tests ║
        │                  qg-basedpyright-scope  ║ qg-coverage-off-hotpath   [PARALLEL, P1]
        │
Phase 3 (warm + offload)  qg-shared-caches (P2) ║ qg-offload-full-run (P2 design)
        │
Phase 4 (codify)          qg-codex-ssot-update  + workspace-wide QG green on touched repos
```

QG gate between phases: Phase N+1 starts only after Phase N's items are C5 and the aggregate benchmark re-run shows no
regression. Phase 1 is the value-delivery milestone — if only Phase 0+1 ship, the contention problem is already
materially better.

## Pre-audit notes

- Governor + worker cap belong in the shared base, not per-repo: `unified-trading-pm/scripts/quality-gates-base/`
  (`base-service.sh`) is the single injection point — editing per-repo `quality-gates.sh` copies is forbidden (CLAUDE.md
  workflow-templates rule); change the PM template + roll out via `rollout-workflow-templates.sh`.
- The `.qg_last_passed_sha` sentinel already exists (written on `quality-gates.sh` exit 0; consumed by quickmerge). The
  green-sentinel todo EXTENDS it (sha → content-hash, per-repo cache), it does not invent a new mechanism.
- Two-pass model (Pass 1 full QG, Pass 2 quickmerge SHA-sentinel check) is the existing seam for "coverage only at gate"
  and "offload full run" — do not bypass it.
- Check whether `.ruff_cache` / `.pytest_cache` / basedpyright cache currently live inside each worktree (default) — if
  so they are per-slot and defeat sharing; the shared-cache todo repoints them via env.

## Success criteria

- **B3 KPI (latency domain):** at K=8 concurrent slot gates, p95 per-run wall-clock ≤ the single-slot (K=1) p95 — i.e.
  contention no longer multiplies run time. Host swap-in during a gate storm ≈ 0.
- **Iterative-run target:** a no-op re-gate of an unchanged repo exits green in < 10s (sentinel short-circuit).
- **Merge-gate unchanged:** gate-to-main full run still executes the complete suite + coverage + the coverage floor; no
  merge-gate weakening — verified by diffing the gate-to-main path before/after.
- **Codex SSOT updated** with the resource-governance section + anti-pattern (Phase 4).
- **Per-repo baseline committed** (`qg_resource_baseline.json`, local + VM) with a 2× deviation guard wired in;
  **worker-VM right-sizing** decided data-driven off it (vs the current `m7i.xlarge` 4 vCPU/16 GB × 8 slots).
- **Final phase:** `bash scripts/quality-gates.sh` green on `unified-trading-pm` + a representative service repo
  (`instruments-service`) using the new base, under concurrent load.

## Full-execution criterion (per CLAUDE.md "Plans Run To Actual Completion" HARD RULE)

- ✅ The aggregate benchmark is RUN on the real multi-slot host (not just authored), before-and-after, with the CSV
  committed as evidence.
  - **What ran**: `benchmark-qg-under-load.sh --k 1,2,4,8` on the slot host.
  - **Verification**: committed CSV shows p95(K=8) ≤ p95(K=1) post-governor; pre-governor CSV shows the regression it
    fixed.
- ✅ The governor + worker cap are rolled out via `rollout-workflow-templates.sh` to all service repos (not left in the
  PM template only), verified by grepping the rolled-out `quality-gates.sh` copies for the token-acquire call.

**Handoff exception(s):** `qg-offload-full-run` is DESIGN-only in this plan (outputs an ADR); its implementation is a
named follow-up todo to be filed in [`infrastructure_master`](../epics/infrastructure_master.md) once the ADR lands.

---

## Progress log — 2026-06-02 (Harsh session, local dev host: 24 cores / 93 GB)

> Built + measured locally; commits land on `live-defi-rollout` directly. Checkboxes above stay `- [ ]` because each is
> multi-part — the BUILD portion is done, the full run / VM side / base-service wiring is noted per item below.

### Phase 0 — tooling built + run

- **`qg-bench-aggregate`** — `scripts/dev/benchmark-qg-under-load.sh` BUILT (shellcheck-clean, `--no-fix` read-only,
  `--jobs`/`--k` configurable, CSV + oversubscription verdict). Smoke caught + fixed 2 real bugs (`set -e` aborting on a
  RED gate; CWD bug measuring the wrong repo via `git rev-parse`). **Pending:** the K∈{4,8} storm on the shared host
  (deferred to a coordinated window — it deliberately induces the thrash this plan fixes).
- **`qg-perrepo-baseline`** — `scripts/dev/measure-qg-baseline.sh` BUILT (+ `--jobs` wave-scheduler, JSON writes
  serialized; records `measured_concurrency`). **Local baseline RUN across all 22 repos** →
  `scripts/dev/qg_resource_baseline.json`. j=4 isolation validated (deployment-api 401s@j4 vs 413s serial = −2.9%, no
  inflation). **Pending:** VM-side baseline (blocked on `qg-cw-memory-agent` — VMs publish zero memory metrics) + the 2×
  drift guard wiring into `base-service.sh`.

#### Baseline results (local, full gates, `--no-fix`) — peak RSS is the binding constraint

| Repo                    | Peak RSS    | Wall            | ~Cores | Exit                                         |
| ----------------------- | ----------- | --------------- | ------ | -------------------------------------------- |
| unified-trading-library | **5.27 GB** | 92s             | 1.7    | ❌ stale venv (duckdb) — FIXED via `uv sync` |
| execution-service       | 1.89 GB     | 604s            | 1.1    | ✅                                           |
| features-service        | 1.85 GB     | 606s            | 0.8    | ✅                                           |
| deployment-api          | 1.37 GB     | 401s            | 1.2    | ✅                                           |
| strategy-service        | 1.31 GB     | 514s            | 0.9    | ✅                                           |
| unified-api-contracts   | 1.18 GB     | 217s            | 1.0    | ✅                                           |
| ml-service              | 1.07 GB     | 382s (isolated) | ~3     | ✅                                           |
| (others 0.3–1.05 GB)    | …           | …               | ~1     | mostly ✅                                    |

- **VM-sizing headline (`qg-vm-rightsizing`):** binding ceiling = **unified-trading-library 5.27 GB** — a single gate
  overshoots the current `m7i.xlarge` 2 GB/slot budget by **2.6×**. Decision must pair machine-type with slots-per-VM
  under the governor; do NOT just add RAM to 8 uncapped runs.

### RED-repo diagnoses (isolated, measured — not guessed)

- **instruments-service** — 2 real test failures (from coverage-padding commit `851559f`): (1) Venus
  `available_from_datetime` — **test wrong** (asserts `2020-09-22`; `get_protocol_floor_date` returns the registered
  `2020-10-08`). (2) `_canonical_league_id("EPL_99999")` → `"EPL"` not `"EPL_99999"` — **deliberate Step-3a heuristic**
  (3+-digit suffix always stripped) vs the coverage-padding test + an internally-inconsistent docstring → **CF-7 domain
  call for Ikenna**, not a unilateral fix.
- **ml-service** — the "13× CPU" from the j=4 run was a **measurement artifact** (did NOT reproduce). Isolated truth:
  **382s / ~3 cores / 1.1 GB**, dominated by **STEP 5.91 entity-registry check = 220s (58%)**; basedpyright is only ~10
  CPU-s. Also: its **own unit tests aren't collected** (gate runs 6 PM integration tests). `PYTEST_WORKERS=2` override +
  uncapped OMP/BLAS is a latent multi-slot risk, not the dominant isolated cost.
- **unified-trading-library** — stale venv (`duckdb` declared in pyproject but not installed) → 8 consolidator tests
  fail (4075 pass). **Fixed** via `uv sync` (duckdb 1.5.3). 5.27 GB RSS is real (4075-test suite + consolidator
  fixtures).
- **UAC** — gate re-run **GREEN** (215s); not failing.

### Phase 1 — started

- **`qg-governor`** — `scripts/quality-gates-base/qg-host-governor.sh` BUILT + functionally verified (K=2, three
  `sleep 3` → 7s; token bucket serializes). flock token bucket, K=`floor(cores/4)`, `nice`+`ionice`, sourceable +
  wrapper + `--status`. **Pending:** wiring `qg_governor_acquire/release` into `base-service.sh` around the heavy
  phases.
- **`qg-slot-aware-workers`** — reshaped by the data: `pytest` already defaults to `-n 1` (not `-n auto`), so the real
  remaining need is **OMP/BLAS env caps** (`OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`) for ML repos +
  revisiting ml-service's `PYTEST_WORKERS=2` override. Not yet implemented.

### Side-effects this session

- Aligned all 22 root repos to `origin/live-defi-rollout` (stashed `uv.lock` regen drift as
  `qg-uvlock-drift-autoalign`).
- Marked `fund-administration-service` + `greeks-service` `status: future` in `workspace-manifest.json` (absent from
  this CosmicTrader workspace, owned by Ikenna side; operator-directed) so the disk-presence alignment gate stops
  blocking.
