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
  - id: qg-vm-rightsizing
    content: |
      - [ ] [INFRA] P1. Worker-VM right-sizing audit — DATA-DRIVEN off the per-repo baseline, not a guess (Harsh 2026-06-02). Current fleet = AWS `m7i.xlarge` (4 vCPU / 16 GB) × 8 slots/VM (~2 GB/slot) — already OOM-prone under parallel QG. Compute the floor = (peak per-run RSS × peak-concurrent-QG-under-the-governor) and compare to Harsh's hypothesis (~64 GB / 8 vCPU). Decide machine type AND slots-per-VM together (a bigger box OR fewer slots — the governor caps concurrency either way; do not just throw RAM at 8 uncapped runs). If a change is warranted, update `deployment-service/scripts/vm/launch-epic-vm-aws.sh` + `orchestrator_vm_registry.yaml`. NOTE: fleet is currently consolidated to 2 running VMs — this is a scale-back-up decision.
    status: todo
  - id: qg-governor
    content: |
      - [ ] [SCRIPT] P0. Cross-slot concurrency governor — a host-level `flock`/token-bucket wrapper so at most K QG runs execute concurrently across ALL slots (default K = `max(1, floor(physical_cores/4))`, env-overridable `QG_HOST_CONCURRENCY`). Wire it into `quality-gates-base/base-service.sh` so every repo's `quality-gates.sh` acquires a host token before the heavy (pytest/basedpyright) phases. Converts 8× simultaneous thrash into orderly queueing → p95 wall-clock drops with NO added parallelism. This is the core fix. `nice -n10` + `ionice -c2 -n7` the QG process tree.
    status: todo
  - id: qg-slot-aware-workers
    content: |
      - [ ] [SCRIPT] P0. Replace `pytest -n auto` (grabs ALL cores per slot → N-slot oversubscription) with a slot-aware cap: `-n $(QG_PYTEST_WORKERS or min(4, floor(free_cores / active_slots)))`. `active_slots` read from the orchestrator/registry or a host token count. Default conservatively; never let one slot's pytest claim the whole box. Document the formula in `codex/06-coding-standards/quality-gates.md`.
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
      - [ ] [SCRIPT] P1. Move `--cov` off the hot path — coverage instrumentation touches every executed line (large CPU/RAM cost). Make it opt-in: iterative/`--quick` runs skip coverage; coverage + the coverage floor are enforced ONLY on the gate-to-main (quickmerge Pass 1) full run. No change to the merge-gate coverage requirement — only to when it is paid.
    status: todo
  - id: qg-shared-caches
    content: |
      - [ ] [SCRIPT] P2. Persistent shared caches across worktrees/slots — ruff cache (`~/.cache/ruff`), pytest cache, basedpyright cache, and uv cache keyed + shared so the first slot warms them for all. Verify cache locations are NOT per-worktree (the default `.ruff_cache`/`.pytest_cache` inside each worktree defeats sharing) — repoint to a host-shared dir via env.
    status: todo
  - id: qg-offload-full-run
    content: |
      - [ ] [DESIGN] P2. Offload the heavy full run off the contended dev host — design (not yet implement) routing the gate-to-main full suite + coverage to a dedicated CI/VM so the dev host only ever runs the light iterative gate. Decide the trigger boundary (quickmerge already two-passes via `.qg_last_passed_sha`). Output a short ADR; implementation is a follow-up todo gated on this design.
    status: todo
  - id: qg-codex-ssot-update
    content: |
      - [ ] [AGENT] P1. Update `codex/06-coding-standards/quality-gates.md` with a new "Resource governance under multi-slot load" section: the governor, slot-aware worker formula, sentinel cache semantics, coverage-on-gate-only rule, and the explicit anti-pattern ("`-n auto` per slot on a shared host is oversubscription, not speedup"). Per CLAUDE.md Post-Plan-Phase Codex Audit HARD RULE.
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

## Phased execution DAG

```
Phase 0 (measure)         qg-bench-aggregate ── proves oversubscription, sets K
                          qg-perrepo-baseline ─ per-repo cost (local+VM) → 2× drift guard + VM-sizing input
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
