<!--
owner: platform / ci-cd (operator: Ikenna)
cadence: on-demand (install/teardown) + weekly health glance
verifier: bash setup-glue-runners.sh status  (systemd active + >=1 runner Online)
last_executed: NEVER (files created 2026-07-15; not yet deployed — awaiting operator go)
-->

# Self-hosted "glue" runners on the planning-VM

Moves unified-trading-pm's IO-bound CI **glue** off GitHub-hosted runners ($0.006/min, billed) onto the always-on
orchestrator VM (self-hosted runner minutes are **free** from GitHub's side). This is **B1** from
[`../../plans/active/github_actions_cost_reduction_options_analysis_2026_07_15.md`](../../plans/active/github_actions_cost_reduction_options_analysis_2026_07_15.md)
§ "Capacity assessment". **All glue workflows live in this repo**, so runners register to `unified-trading-pm` only (a
personal account has no org-level runners — repo-scoped is correct).

## Why this is safe here

- Repos are **private** → no untrusted fork PRs → self-hosted is safe even for PR jobs (we still keep the heavy test
  gate on GitHub-hosted, for VM capacity not security).
- Runners are **ephemeral** (JIT config): one job per process, fresh identity each time, auto-deregister, no long-lived
  credentials on disk.
- The whole fleet is **CPU/RAM-capped** by `github-glue-runner.slice` (<=4 of 8 vCPU, <=8 GiB) so a CI burst can never
  starve the agent-orchestrator sharing the VM. Measured glue load: ~1.7 cores avg, ~3,100 jobs/day.

## Files

| File                          | Role                                                          |
| ----------------------------- | ------------------------------------------------------------- |
| `setup-glue-runners.sh`       | install / status / teardown / prune (run ON the VM)           |
| `glue-runner-run.sh`          | per-runner ExecStart wrapper (JIT config → one ephemeral job) |
| `github-glue-runner@.service` | systemd template unit (one instance per runner)               |
| `github-glue-runner.slice`    | resource cap protecting the orchestrator                      |

## Deploy (on the planning-VM, as a sudo user)

```bash
# the VM already has a unified-trading-pm clone; from it:
cd <pm-clone>/scripts/self-hosted-runners
sudo GH_PAT="$(<admin PAT with Administration:write on unified-trading-pm>)" \
     RUNNER_COUNT=8 ./setup-glue-runners.sh install
./setup-glue-runners.sh status         # expect 8 units active, runners Online/idle
```

The token can instead be fetched from GCP Secret Manager at runtime (no PAT on disk): set
`GH_TOKEN_SECRET=<secret-name>` (+ `GCP_PROJECT`) in `/etc/github-glue-runner.env` and leave `GH_TOKEN` unset.

## Which workflows move (STEP 2 — separate change, takes effect on push)

Registering the runners does **nothing** until a workflow asks for them. Flip `runs-on: ubuntu-latest` →
`runs-on: [self-hosted, glue]` for the glue set only. Get the candidate list with:

```bash
./classify-glue-workflows.sh          # prints MOVE (glue) vs KEEP (hosted) for every PM workflow
```

- **MOVE** (IO-bound glue: `repository_dispatch` / `schedule` / `push` bots): `ci-status-update`, `cloud-build-router`,
  `cloud-build-router-aws`, the promotion/health/reconcile crons, the SIT/promotion **orchestration** bots (`sit-gate`,
  `sit-unlock`, `ldr-to-main-promote`, `staging-to-main` — they only open PRs / dispatch, they do NOT run tests), the
  agent/plan bots. **50 workflows.**
- **KEEP on GitHub-hosted** (**6**): `quality-gates-v2` / `python-quality-gates-v2` (the heavy pytest/typecheck gate —
  CPU-bound ~12 min), the two `pull_request` agent bots, and — flagged `KEEP*` by the classifier's heavy-compute
  detector — **`build-smoke-all-repos`** (25-job `docker buildx` matrix) and **`publish-package`** (builds a wheel).
  These build LOCALLY, so they must not run on the light glue VM. **The heavy test gate never touches the VM** — the
  promotion bots (on the VM) just open the PR; the `quality-gates-v2` check that fires on it runs on GitHub-hosted.

Roll the `runs-on` change out via the template SSOT + `rollout-workflow-templates.sh`, never by hand-editing per-repo
copies. **Migrate ONE low-risk workflow first** (recommend `branch-health` or `reconcile-release-tags`), confirm a green
run on `[self-hosted, glue]`, then batch the rest.

## Verify / operate

```bash
./setup-glue-runners.sh status        # systemd + live runner list + slice memory
journalctl -u 'github-glue-runner@1' -n 50 --no-pager
./setup-glue-runners.sh prune         # clear OFFLINE glue-* runners left by a crashed wrapper
```

Health signal: >=1 runner `Online` and the slice `MemoryCurrent` well under 8 GiB. A queued glue job with 0 Online
runners = the fleet is down → `systemctl restart 'github-glue-runner@*'`.

## Rollback (instant, safe)

Flip the affected workflows' `runs-on` back to `ubuntu-latest` (they run on GitHub-hosted again immediately), then
`sudo ./setup-glue-runners.sh teardown`. No data lives on the runners.

## Security notes

- `/etc/github-glue-runner.env` holds the admin token 0600/root; or use the Secret-Manager path (nothing on disk).
- Runners run as non-root `ubuntu`; JIT ephemeral means no persistent `.credentials`.
- Hardening option: a dedicated fine-grained PAT scoped to **only** `Administration: write` on unified-trading-pm.
