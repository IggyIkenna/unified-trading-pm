# ADR: Offload the heavy QG + SIT to a self-hosted runner pool (Option B)

- **Status:** Accepted (design) — 2026-06-02
- **Plan:** `plans/active/quality_gates_resource_contention_speedup_2026_06_02.md` (todo `qg-offload-full-run`)
- **Decision owner:** Harsh; **implementation:** follow-up todos in `plans/epics/infrastructure_master.md`
- **Composes with:** the host concurrency governor (`qg-host-governor.sh`) + `qg-perrepo-baseline` (sizing input).

## Context

Soon every worker agent runs the full `quality-gates.sh` + `quickmerge` locally after finishing a plan (staging-first
flow). That gate is **memory-bursty**: measured ceilings are unified-trading-library **5.27 GB** locally, and heavy runs
have hit **32–57 GB** (the `api_host_chronic_impairment_2026_05_29` pytest OOM on a 64 GB box). The current substrate is
wrong for it on both ends:

- **Worker VMs** = `m7i.xlarge` (4 vCPU / **16 GB**) × 8 slots — OOM under even 1–2 concurrent heavy QGs, and **CPU-idle
  ~1.7% avg** while coding (the bottleneck is bursty RAM, not steady CPU).
- **The "central" gate is undersized:** `python-quality-gates-v2.yml` runs on GitHub `ubuntu-latest` (2 vCPU / **7 GB**)
  with **0 self-hosted runners** — a 32–57 GB QG cannot pass there either.

Cost is not a constraint (AWS credits); architectural correctness is.

## Decision

**Adopt Option B: a dedicated self-hosted GitHub Actions runner pool for the heavy QG + SIT.** Workers stay small and
run only a fast local pre-check; the authoritative heavy gate runs centrally on sized-for-it runners.

Rejected alternatives:

- **Option A (vertically scale every worker VM to 128–256 GB):** workers are idle 95% of the time → big boxes sit mostly
  idle; couples QG capacity to slot count (every new slot grows every VM). Keep as the fallback if self-hosted runners
  are ever disallowed.
- **Option C (bespoke QG-as-a-service + RPC):** reinvents what self-hosted runners give for free; redundant with the CI
  gate that already exists on staging. Not recommended.

## Design

### 1. Runner pool

- **1–3 VMs** `m7i.8xlarge` (**128 GB** / 32 vCPU) or `m7i.16xlarge` (256 GB), 100–200 GB gp3, registered as GitHub
  Actions **self-hosted runners** labelled `qg`. Start with 2 always-on; revisit auto-scaling once queue depth is known.
- Each runner runs the **same governor** (`QG_HOST_CONCURRENCY` sized to its cores) so even N parallel CI jobs on one
  runner queue rather than thrash.
- **Provisioning:** `deployment-service/scripts/runner/bootstrap_runner.sh` — installs the runner agent, registers with
  a short-lived registration token from Secret Manager, installs the workspace toolchain (uv, Python 3.13, ruff/
  basedpyright pinned), and configures the runner as an ephemeral/auto-removed job runner.

### 2. CI cutover (one line, reversible)

In `python-quality-gates-v2.yml` (and `quality-gates-v2.yml`): `runs-on: ubuntu-latest` → `runs-on: [self-hosted, qg]`.
This simultaneously fixes the undersized-`ubuntu-latest` problem. The required-check name `quality-gates-v2` is
unchanged, so branch protection is untouched.

### 3. Worker fast pre-check (replaces the local full gate for quick feedback)

Workers run a **seconds-long, low-RAM** pre-check before push — `ruff check` + `basedpyright` on **changed files only**
(no pytest fan-out, no coverage). This gives fast local feedback; it is **advisory**, not authoritative.

### 4. Authoritative-gate / two-pass change (the real migration cost)

Today the authoritative signal is the **local** `.qg_last_passed_sha` sentinel that quickmerge Pass 2 trusts. Under
Option B the authoritative gate is the **central CI check** on the pushed SHA. Migration:

- quickmerge opens the staging PR; the `quality-gates-v2` check on the self-hosted pool is the authoritative pass/fail
  (already how staging→main promotion gates).
- The local `.qg_last_passed_sha` becomes the **fast-pre-check** sentinel (advisory), not the merge authority.
- **Soundness:** the central gate still runs the COMPLETE suite + coverage + the coverage floor — no weakening; only its
  _location_ moves off the contended dev/worker host.

### 5. Security

Self-hosted runners execute untrusted-ish PR code → use **ephemeral, single-job** runners on isolated VMs (no production
credentials; least-privilege IAM), registration tokens from Secret Manager, and restrict the pool to this org's private
repos. Never run self-hosted runners on `pull_request` from forks.

## Consequences

- Concentrates the 32–57 GB burst in one sized-for-it place; QG capacity **decouples from worker count**; SIT gets a
  natural home; plugs into the existing CI seam (no bespoke RPC).
- Adds a network dependency for the authoritative gate + runner provisioning/queueing to operate.

## Follow-up implementation todos (file in `infrastructure_master`, gated on this ADR)

1. `[INFRA] Provision the `qg`self-hosted runner pool +`bootstrap_runner.sh`(2×`m7i.8xlarge`).`
2. `[INFRA] Cutover `python-quality-gates-v2.yml`/`quality-gates-v2.yml` `runs-on`→`[self-hosted,
   qg]`; verify the required check still reports.`
3. `[SCRIPT] Add the worker fast-pre-check (ruff + basedpyright on changed files) + repoint `.qg_last_passed_sha` to advisory.`
4. `[DOC] Update `codex/08-workflows/ci-cd-flow.md` two-pass model: authoritative gate = central CI check, not local sentinel.`
