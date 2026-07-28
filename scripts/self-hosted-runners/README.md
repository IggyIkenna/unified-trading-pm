<!--
owner: platform / ci-cd (operator: Ikenna)
cadence: on-demand (install/teardown) + weekly health glance
verifier: bash setup-glue-runners.sh status  (systemd active + >=1 runner Online per pool + slot clone fresh)
last_executed: NEVER (files created 2026-07-15, redesigned two-pool 2026-07-16; not yet deployed)
-->

# Self-hosted "glue" runners on the planning-VM

Moves unified-trading-pm's IO-bound CI **glue** off GitHub-hosted runners ($0.006/min, billed) onto the always-on
orchestrator VM (self-hosted runner minutes are **free** from GitHub's side). This is **B1** of
[`../../plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md`](../../plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md)
— read that plan's **▶ START HERE** before deploying. **All glue workflows live in this repo**, so runners register to
`unified-trading-pm` only (a personal account has no org-level runners — repo-scoped is correct, and it's exactly why
cross-repo reusables must stay hosted).

## Two pools — and why

| Pool       | Mode              | Labels                    | Serves                                    |
| ---------- | ----------------- | ------------------------- | ----------------------------------------- |
| `glue-N`   | JIT-**ephemeral** | `self-hosted,glue`        | the ~37 low-frequency movers              |
| `writer-N` | **long-lived**    | `self-hosted,glue-writer` | `ci-status-update` (~13k/mo, ~2-5s a job) |

The writer pool exists because JIT re-registration (generate-jitconfig + config + connect ≈ seconds) would **dominate**
a ~3s job and cap burst throughput. Three things about this are load-bearing and easy to break:

- **The labels are DISJOINT on purpose.** Label matching is a **subset** test — a writer labelled
  `self-hosted,glue,writer` would still satisfy `runs-on: [self-hosted, glue]` and steal the movers' jobs. So the writer
  pool omits `glue` entirely. `ci-status-update.yml` is therefore the **one** MOVE workflow that does not get the
  uniform flip recipe: it targets `[self-hosted, glue-writer]`.
- **There is no "long-lived JIT."** A JIT config is single-use _by construction_ (auto-deregisters after one job). The
  writer registers once via `config.sh` + a registration token, then loops `run.sh`. That means the writer **does** keep
  `.credentials` on disk — the accepted trade, and the reason the security-codex todo exists.
- **`prune` is EPHEMERAL-ONLY.** A JIT runner is only ever `offline` if it crashed, but a long-lived writer is
  _legitimately_ offline across every reboot. Pruning on `offline` alone would deregister the writer pool out from under
  a rebooting VM. The `glue-` name prefix is the guard.

## Isolation scope — folder/venv/clone only (operator decision, 2026-07-16)

Runners run as **`ubuntu`** and reuse the VM's **existing** GCP/AWS/GitHub creds and toolchain. There is **no dedicated
OS user and no separate service account**, deliberately:

- Everything needing true clean-room isolation (QG, PR gates, image builds) is **already GitHub-hosted and stays
  there**.
- The MOVE set is all first-party automation with **zero `pull_request` triggers** (by construction — the classifier
  sends every `pull_request` workflow to KEEP), and all repos are **private**, so there is no fork-PR path for untrusted
  code to reach the box.
- The **AO already runs as `ubuntu`** on this VM with the same ambient creds, so glue-as-`ubuntu` barely moves the blast
  radius.

What _is_ isolated is the slot: its **own folder, own venv, own clone** — never an AO slot clone (that would race a live
worker). `HOME` is deliberately **not** redirected: it would break `$HOME/.config/gcloud` ADC resolution, and the
`git config --global` in two movers is inert because every clone carries a **local** identity that overrides it.

## The slot

| Path                               | Role                                                                              |
| ---------------------------------- | --------------------------------------------------------------------------------- |
| `${RUNNER_BASE}/repo`              | runner-**owned** clone; pre-staged code so the writer does **no checkout at all** |
| `${RUNNER_BASE}/venv`              | dedicated venv (`google-cloud-firestore` for STEP 2b) — not AO/system Python      |
| `${RUNNER_BASE}/toolcache`         | shared `RUNNER_TOOL_CACHE` — `actions/setup-python` pays download cost **once**   |
| `${RUNNER_BASE}/repo.refreshed-at` | freshness stamp; `status` flags it red past 30 min                                |

`${RUNNER_BASE}` defaults to `/opt/github-glue-runners`.

## Files

| File                                       | Role                                                                   |
| ------------------------------------------ | ---------------------------------------------------------------------- |
| `setup-glue-runners.sh`                    | install / status / preflight / teardown / prune (run ON the VM)        |
| `glue-runner-run.sh`                       | per-runner ExecStart wrapper; **forks on the pool** in the `%i` name   |
| `job-cleanup.sh`                           | `ACTIONS_RUNNER_HOOK_JOB_COMPLETED` — per-job `_work` wipe for writers |
| `refresh-slot-repo.sh`                     | FF-pulls the slot clone; **stale pre-staged code = silent wrongness**  |
| `github-glue-runner@.service`              | systemd template unit (`%i` = `<pool>-<index>`)                        |
| `github-glue-slot-refresh.{service,timer}` | 10-min slot-clone refresh                                              |
| `github-glue-runner.slice`                 | resource cap protecting the orchestrator                               |
| `classify-glue-workflows.sh`               | **SSOT** for MOVE vs KEEP                                              |

## Deploy (on the planning-VM, as a sudo user)

```bash
cd <pm-clone>/scripts/self-hosted-runners
./setup-glue-runners.sh preflight      # toolchain parity vs ubuntu-latest — do this FIRST
sudo GH_TOKEN_SECRET=GH_PAT GLUE_COUNT=5 WRITER_COUNT=3 ./setup-glue-runners.sh install
./setup-glue-runners.sh status         # expect 8 units active, both pools Online/idle, slot fresh
```

### The admin token — exactly one source

`install` requires **exactly one** of these and refuses if both are set (they can disagree, and silently preferring one
would mean the token you _think_ registers runners isn't the one that does):

| Source                   | Stored in `/etc/github-glue-runner.env` | Use                                                 |
| ------------------------ | --------------------------------------- | --------------------------------------------------- |
| `GH_TOKEN_SECRET=<name>` | the secret **name** only                | **preferred** — on this VM `GH_TOKEN_SECRET=GH_PAT` |
| `GH_PAT=<token>`         | the literal token (0600 root)           | legacy; only for a host with no ADC                 |

On the secret path no credential is ever written to disk: the wrapper resolves the token from Secret Manager at every
start using the ADC of `ubuntu`. Pair with `GCP_PROJECT=<proj>` only if the secret isn't in the VM's default project.

Two consequences worth knowing:

- **Rotation is free.** Both the wrapper and `resolve_admin_token` access the secret's `latest` version by name, so
  adding a new version rotates every runner with no redeploy and no edit to the env file.
- **ADC is per-user, and `install` runs as root while the runners run as `ubuntu`.** A root-only ADC would let install
  pass and then leave 8 units crash-looping. `install` therefore resolves the secret via `sudo -u ubuntu` — as the
  account that actually has to do it — and probes `Administration:write` up front (a `registration-token` POST,
  expecting 201) so a bad token fails in one HTTP call instead of in the journal.

`status` and `prune` resolve a token the same way: explicit env first, else the secret name recorded in the env file.
Since that file is `0600 root`, run them under `sudo` if you want the live-runner listing; without a token `status`
degrades to omitting that section rather than failing.

**Toolchain parity is the real migration risk**, not isolation. Hosted `ubuntu-latest` pre-seeds a large toolchain; this
VM does not. `preflight` checks what the MOVE set actually invokes (`gh` 181 · `jq` 111 · `python3` 105 · `uv` 32 ·
`aws` 22 · `gcloud` 16 · `pip` 15 · `npm` 1). `docker` is **not** needed — its hits are a step _named_ `docker-build`
that only dispatches to Cloud Build, plus the Artifact Registry hostname in `gcloud artifacts docker images describe`.

## Which workflows move

Registering runners does **nothing** until a workflow asks for them. `classify-glue-workflows.sh` is the SSOT:

```bash
./classify-glue-workflows.sh          # -> MOVE (→ PM-local direct flip): 39   KEEP (→ GitHub-hosted): 17
```

> ⚠️ **Flip PM's `.github/workflows/*.yml` DIRECTLY. Do NOT route this through `rollout-workflow-templates.sh`.** The 4
> `KEEP-T` fleet templates are rolled out to ~24 repos that have **no glue runners**; flipping a template would hang the
> workflow in every one of them. This is the opposite of the normal never-hand-edit-a-per-repo-copy rule, because here
> PM _is_ the only repo involved.

**Never flip** a `KEEP-*` verdict, and never flip `persist-cicd-event` (verdict `MOVE-C` — it moves off hosted by being
**converted to a composite action**, not by a `runs-on` change; a reusable's `runs-on` is independent of its caller, so
flipping it would hang its hosted callers). The six KEEP classes, five of which break something if naively flipped:

- `KEEP` (4) — real test/PR gates (`quality-gates-v2`, `python-quality-gates-v2`, …): CPU-bound, and the clean room.
- `KEEP*` (2) — `build-smoke-all-repos`, `publish-package`: build **locally** (heavy), must not hit the light VM.
- `KEEP-T` (4) — fleet templates: flipping hangs ~24 repos.
- `KEEP-R` (1) — `image-build-validate`: a **cross-repo reusable** called by 24 repos; a reusable runs on the
  **caller's** runners, which are hosted → flipping blocks every staging→main promote fleet-wide.
- `KEEP-M` (5) — failure-independence monitors: their value is detecting that **this VM** is broken.
- `KEEP-D` (1) — `notify-slack`: the alert carrier the KEEP-M monitors call; on the VM, a VM outage would let them
  detect a failure but not page.

**Canary `reconcile-release-tags`** (a MOVE workflow that has `workflow_dispatch`). Do **not** use `branch-health` — it
is now `KEEP-M`.

> **Ordering:** runners must be live **before** any flip reaches `main`. `schedule` / `repository_dispatch` workflows
> run their definition from the **default branch**, so a flip on LDR does nothing until it promotes — and once it does,
> a missing runner means a hung job.

## Verify / operate

```bash
./setup-glue-runners.sh status                        # both pools + slot freshness + slice memory
journalctl -u 'github-glue-runner@glue-1' -n 50 --no-pager
journalctl -u 'github-glue-runner@writer-1' -n 50 --no-pager
systemctl list-timers 'github-glue-slot-refresh*'     # slot clone must refresh every ~10 min
./setup-glue-runners.sh prune                         # clear OFFLINE EPHEMERAL runners only
```

Health signal: `>=1` runner Online **per pool**, slice `MemoryCurrent` well under 8 GiB, and the slot clone refreshed
within ~10 min. A queued glue job with 0 Online runners = that pool is down →
`systemctl restart 'github-glue-runner@glue-*'`. **A stale slot clone is the quiet failure**: the writer keeps
succeeding while writing Firestore rows from outdated code, so treat a red freshness stamp as an incident, not a nit.

## Rollback (instant, safe)

Flip the affected workflows' `runs-on` back to `ubuntu-latest` (they run on GitHub-hosted again immediately), then
`sudo ./setup-glue-runners.sh teardown`. No data lives on the runners.

## Security notes

- `/etc/github-glue-runner.env` holds the admin token 0600/root; or use the Secret-Manager path (nothing on disk).
- Runners run as non-root `ubuntu` and carry the VM's **ambient cloud identity** (ADC + AWS-WIF) — see the plan's
  security-codex todo. The JIT pool keeps no persistent `.credentials`; the **writer pool does**, by necessity.
- Hardening option: a dedicated fine-grained PAT scoped to **only** `Administration: write` on unified-trading-pm.
