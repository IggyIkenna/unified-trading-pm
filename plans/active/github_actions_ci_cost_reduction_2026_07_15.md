---
doc_type: plan
title: GitHub Actions CI/CD cost reduction — self-host the glue, kill the minute-minimum tax, fix cron cadence
summary: >-
  PM is ~48% of a ~$1,000/mo GitHub Actions bill despite a code freeze because it is the fleet CI/CD control tower —
  ~79% of its runs are automation (status routing, deploy dispatch, promotion/health crons), only ~8% are doc commits.
  All repos are private (every minute billed) and there are ZERO self-hosted runners, so the biggest untapped lever is
  moving lightweight glue off $0.006/min GitHub-hosted runners onto compute we already run 24/7. Tiered fix — self-host
  the switchboard+crons (39 MOVE: 38 runs-on flips + 1 composite-action conversion), collapse the quality-gates job
  fan-out that pays a 1-min minimum per sub-second job, and fix cron cadence; 17 workflows stay hosted (test gates,
  fleet templates, a cross-repo reusable, the failure-independence monitors + their alert carrier). ALL decisions closed
  2026-07-15/16. ACTIVE + operator-driven (assigned_vm NA — never auto-dispatched). **DEPLOYED 2026-07-16: D1-D6 ALL
  DONE.** 8 runners live on the orchestrator VM (5 JIT-ephemeral glue + 3 long-lived glue-writer, disjoint labels);
  CANARY GREEN on LDR with billable={} (zero billed minutes) and the JIT deregister/re-register lifecycle proven from
  the journal. 1 of 38 movers is flipped; main is UNTOUCHED. Counts corrected 39/17 -> 38/18 (agent-audit is KEEP-U: a
  pure reusable caller with no runs-on). Next action = OPERATOR GATE, then the next 10 (5 simple + 5 complex), then the
  remaining 26. Two P0s pending: rotate GH_PAT (agent-caused transcript exposure), and quickmerge's --agent sentinel
  races its own rebase on a busy branch.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, github-actions, cost, self-hosted-runner, workflows, spend-reduction]
related:
  - github_billing_dashboard_access_2026_07_09.md
  - cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
created: 2026-07-15
last_updated: 2026-07-16
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role: infra
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  - "operator ask 2026-07-15 (spend investigation): GitHub bill ~$50-82/day during code freeze; why is PM so expensive"
  - "live Enhanced-Billing usage report (users/IggyIkenna/settings/billing/usage) via github-billing-token, Jun+Jul 2026"
  - "PM Actions run-mix sample: 1000 runs / 13.5h window ending 2026-07-15T06:53Z"
drift_direction: advance-code
---

# GitHub Actions CI/CD cost reduction

> **🟢 ACTIVE (operator 2026-07-16) — approved to execute.** All decisions are closed and the flip set is FINAL (**39
> MOVE / 17 KEEP**); the earlier "suggestions, not decisions" framing is withdrawn. Still **operator-driven**:
> `assigned_vm: NA` + `execution_scope: local-only` → this plan is **never auto-dispatched** to agent-orchestrator
> workers; a human/interactive session executes it. **Nothing is deployed yet** — no runners on the VM, no `runs-on`
> flipped, no callers rewired.

---

## ▶ START HERE (first action for a fresh session)

1. **Read this pre-flight §** + § "MOVE / STAY manifest". The flip set is final — do not re-derive it; the SSOT is
   `bash scripts/self-hosted-runners/classify-glue-workflows.sh` → **38 MOVE / 18 KEEP** (corrected from 39/17 on
   2026-07-16: `agent-audit` is **KEEP-U**, a pure reusable caller with no `runs-on`). **37** are flippable.
2. **⛔ D1–D6 + BATCH 2 ARE DONE (2026-07-16) — the runners are LIVE and 10 of 38 movers are self-hosted. Do NOT re-run
   `install`, re-derive the toolchain, or re-pick the canary/batch.** Deployed state, all measured:
   - **8 runners Online** on `i-0c9b283b31d6b5ca7` — `5× glue-*` (`self-hosted,glue`, JIT-ephemeral) + `3× writer-*`
     (`self-hosted,Linux,X64,glue-writer`, long-lived). Labels **disjoint** → writers cannot steal mover jobs.
   - **Deploy clone** = `/opt/glue-deploy/unified-trading-pm` (fresh; **never** an AO slot clone). Runner root =
     `/opt/github-glue-runners` (root-owned; `venv`/`repo`/`toolcache` runner-owned).
   - **No credential on disk**: `/etc/github-glue-runner.env` holds `GH_TOKEN_SECRET=GH_PAT` (the NAME); the wrapper
     resolves it per start via `ubuntu`'s ADC. Rotation needs no redeploy (everything reads `latest` by name).
   - **10 of 38 flipped** (canary + batch 2), **7/7 dispatched GREEN**, incl. BOTH cross-boundary tests (a self-hosted
     caller's `notify-slack` and `persist-cicd-event` jobs ran on GitHub-HOSTED runners, as designed). 2 of the 9 are
     flipped but deliberately un-dispatched (`digest-drift-sweep`, `conflict-resolution-agent` — a dispatch would cause
     real fleet actions; they self-verify on their next natural trigger).
   - **The tool cache is PER-RUNNER, not shared** — the shared one raced `setup-python` (delete-then-create). This is
     the single most likely thing to be 'helpfully' re-optimised back. Do not.
   - **The wrapper self-heals the JIT 409** left by a SIGTERM'd predecessor. Without it, one `systemctl restart` takes
     the whole glue pool down permanently.
3. **HOW TO TOUCH THE BOX AT ALL — read before any VM step.** There is **no inbound SSH** and no open `:8765`; **AWS SSM
   is the only way in**. Use `scripts/self-hosted-runners/ssm-run.sh` (snippet on stdin) — it exists so you do not
   re-discover its three gotchas: SSM runs your snippet under **dash** (so it injects a bash shebang), the payload must
   travel as a **JSON param file** (inline quoting mangles anything real), and a mangled-to-empty payload still reports
   **Success** (so read stdout, never just status). **SSM runs as ROOT, and gcloud ADC is PER-USER with root having
   NONE** — anything touching GCP must `sudo -u ubuntu`.
   ```bash
   echo 'systemctl --no-pager list-units "github-glue-runner@*"' | bash scripts/self-hosted-runners/ssm-run.sh
   ```
4. **⛔ DEPLOY RULE — `git pull` the deploy clone, NEVER patch it.** The box's copy of these scripts comes from
   `/opt/glue-deploy/unified-trading-pm`, a real git clone. Update it with
   `sudo -u ubuntu git -C /opt/glue-deploy/unified-trading-pm fetch --depth 1 origin live-defi-rollout && … reset --hard FETCH_HEAD`,
   then re-run `install`. **Copying a file straight onto the box (scp/base64/heredoc) creates a second source of truth
   and WILL be silently reverted** — that exact mistake wiped the JIT-409 self-heal off the live wrapper on 2026-07-16
   (I patched `/opt/github-glue-runners/` but not the clone; the next `install` copied the clone's older wrapper back
   over it), leaving the box one `systemctl restart` from the pool-death bug. **Verify after every deploy:** the live
   wrapper's sha must equal git's —
   `git show origin/live-defi-rollout:scripts/self-hosted-runners/glue-runner-run.sh | sha256sum` vs
   `sha256sum /opt/github-glue-runners/glue-runner-run.sh`.
5. **THE REVERT PATH EXISTS — use it, don't hand-roll one.** `scripts/self-hosted-runners/hosted-baseline/` holds the
   byte-exact **GitHub-hosted** form of all 56 workflows (the 10 flipped ones recovered from git history; `MANIFEST.tsv`
   records provenance). `hosted-baseline.sh restore <wf>|--all` puts a workflow back — and it restores the
   `setup-python` / `pip install` steps the flip DELETED, which reverting `runs-on` alone would not: that would give a
   hosted job with no Python set up, broken in a NEW way. Run `hosted-baseline.sh verify` before trusting it, and
   **re-run `snapshot` whenever an UNFLIPPED workflow is edited** (its baseline goes stale; verify catches it). The
   baseline is `.prettierignore`d ON PURPOSE — prettier rewrote it once and destroyed the byte-exactness that is its
   whole point.
6. **⏵ NEXT: the OPERATOR GATE.** Batch 2 is green; next is the **remaining 27** (the delta from
   `classify-glue-workflows.sh` vs `git grep -l 'self-hosted, glue' .github/workflows/`). The tail carries **no new
   capability class** — batch 2 covered them all. 10 of the 27 have **no `workflow_dispatch`** and are only validatable
   AFTER promote, so they go LAST. then STEP 2b (ci-status-update trim) + STEP 2c (persist composite action), then Phase
   2 (A1/A2/A5) and Phase 3 (A6/A7/A8).
7. **Two P0s are open and are NOT blocked on the gate** — see the todos: **rotate `GH_PAT`** (agent-caused transcript
   exposure) and the **quickmerge `--agent` sentinel race** (its own STAGE-0.4 rebase invalidates the sentinel STAGE 3
   then checks, so on a busy LDR it can never self-validate; workaround = chain
   `quality-gates.sh --no-fix && quickmerge.sh` in ONE shell to close the window).

**THE LESSON THAT COST THE MOST — apply it to every remaining flip (2026-07-16):** every verifier written before the
deploy reported **green on a box that would have failed**, always the same way — the right worry checked in the wrong
environment. `python3 -m venv --help` passes where creating a venv fails; `bash -lc` finds `uv` in `~/.local/bin` where
the runner (systemd, non-login) never will; `command -v` in the caller's shell says nothing about the job's shell.
**Verify in the environment the runner actually has** (`env -i` + the unit's PATH, as `ubuntu`), and prefer _doing the
real operation_ over asking whether it might work. `systemd-run --uid=ubuntu --setenv=PATH=…` is the honest probe.

**Ordering hard rules:** runners must be live **before** any flip reaches `main` (schedule/dispatch workflows run the
definition from the default branch — see the default-branch gotcha below), and **never flip** a `KEEP-*` workflow or
`persist-cicd-event` (`MOVE-C` → convert, don't flip).

---

## Execution pre-flight & runbook (READ FIRST — context not obvious from the todos)

**State 2026-07-16 (post-deploy):** plan ACTIVE; flip set final at **38 MOVE / 18 KEEP** (37 flippable). **D1–D6
COMPLETE — the runners are LIVE and the canary is GREEN.** `install` exit 0; 8/8 units active; both pools Online with
disjoint labels; refresh timer green; `preflight` exit 0 **on the runner's real PATH**. Canary run `29504914995` on LDR:
claimed by `glue-ip-172-31-5-118-4`, `success`, **`billable: {}`** (zero billed minutes — the thesis, measured), JIT
deregister→restart→re-register proven from the journal. **`main` is UNTOUCHED** (1 flip, LDR only). Next action =
**operator gate**, then the 10. Work continues from **slot 1** (`.tabs/1/`), root left to the AO worker.

### The flip set — CRITICAL split (`bash scripts/self-hosted-runners/classify-glue-workflows.sh` is the SSOT; full list in §"MOVE / STAY manifest")

**39 MOVE / 17 KEEP** (46/10 → 44/12 → 40/16 → 39/17 — the review reclassified `image-build-validate`, the operator kept
the 4 CI-health watchers hosted, then the final review caught the shared alert carrier `notify-slack`). **Only flip the
MOVE set.** The 17 KEEP fall in six classes, five of which would BREAK something if naively flipped:

- **`KEEP-T` (4): `main-backmerge-to-ldr`, `semver-agent`, `major-bump-issue-handler`, `request-major-bump`** — **fleet
  templates** (`scripts/workflow-templates/`) rolled to EVERY repo. Flip the template → hangs the other ~24 repos (only
  PM has runners); hand-edit PM's copy → banned. Leave hosted.
- **`KEEP-R` (1): `image-build-validate`** — a **cross-repo reusable** called by **24 repos'** `image-build-gate.yml`
  (`uses: …/unified-trading-pm/.github/workflows/image-build-validate.yml`). A reusable's jobs run on the **caller's**
  runners, and our `glue` runners are repo-scoped to PM → flipping it hangs the dual-cloud image-build gate in all 24
  repos, **blocking every staging→main promote fleet-wide**. Same failure mode as KEEP-T; the classifier missed it until
  the 2026-07-16 review (it's not in the template dir). Nearly free to leave hosted (only fires on promote PRs).
- **`KEEP-M` (5): `overnight-dead-man-switch`, `ci-health`, `cloud-build-failure-watcher`, `ldr-ci-monitor`,
  `branch-health`** — **failure-independence monitors** (operator KEPT HOSTED 2026-07-16). Their whole value is
  detecting that our infra (incl. THIS VM) is broken; running them on the glue pool would let a VM outage silently take
  out both the detection and the Slack alert (the alerter is on the down box). They're light (a few $/mo total) and
  GitHub-hosted is the right home. `ci-health` also **auto-recovers** stuck promote PRs / the v2-deadlock;
  `cloud-build-failure-watcher` is the ONLY detector for out-of-band Cloud Build failures; `overnight-dead-man-switch`
  watches the orchestrator that runs on this VM. Independence is exactly why these stay.
- **`KEEP-D` (1): `notify-slack`** — the shared **alert carrier** the `KEEP-M` monitors call (`notify` job →
  `uses: ./…/notify-slack.yml`). Hosted **for the WATCHERS' sake, not the movers'**: a reusable's `runs-on` is
  independent of its caller, so if `notify-slack` were on the VM a VM outage would let the hosted monitors DETECT a
  failure but be unable to PAGE (its `notify` job would have no runner) — re-breaking the independence the KEEP-M set
  buys. (Movers don't need it hosted — if the VM is down a mover isn't running, so it has nothing to alert; but since
  `notify-slack` is one reusable with one `runs-on` and the watchers require hosted, hosted wins for everyone. Movers
  calling it need **no change** — GitHub runs that one job on a hosted runner inside the self-hosted workflow.)
  **Measured cost of keeping it hosted: ~$1/mo** (117 Slack posts/30d in the alert ledger + a small deduped-but-billed
  tail — `cloud-build-failure-watcher`'s standing condition is the bulk at ~51 billed/mo). Cheap insurance; cost is not
  the deciding factor, independence is.
- **`KEEP*` (2): `build-smoke-all-repos` (docker buildx), `publish-package` (wheel)** — build locally, too heavy for the
  light VM.
- **`KEEP` (4): `quality-gates-v2` + `python-quality-gates-v2`** (heavy tests) **+ `plan-health-agent` +
  `conflict-resolution-merged`** (`pull_request` bots).

**The 39 MOVE = 38 by `runs-on` flip + 1 by conversion.** One mover is a special case:

- **`MOVE-C` (1): `persist-cicd-event`** — the second straddle, RESOLVED via **option C (operator 2026-07-16): convert
  it to a composite action** (not a `runs-on` flip). It's a high-frequency reusable (fires on ~EVERY run, unlike
  alert-only `notify-slack`) that writes the CI/CD event-ledger row; called by **5 KEEP + 17 MOVE** workflows incl. the
  13k/mo `ci-status-update`. One reusable = one `runs-on`, so a flip can't satisfy both sides (hosted callers would hang
  on a down VM). Fix: rewrite it as `.github/actions/persist-event/action.yml` so it runs as **steps inside each
  caller's own job** → on the caller's runner (movers → VM/$0, KEEP callers → hosted, no hang), which ALSO removes the
  separate 1-min-minimum billed job (the A3/A4 saving). It leaves the workflow set once converted. **Do NOT flip its
  `runs-on`** — convert it (STEP 2c).

### Deploy mechanism (Track 1 step 1)

- **Target VM — VERIFIED 2026-07-16** (`aws ec2 describe-instances`): `i-0c9b283b31d6b5ca7` =
  **`agent-orchestrator-vm-1`**, EIP **13.113.200.22**, **m8i.2xlarge (8 vCPU / 32 GiB)**, running — matches CLAUDE.md's
  central orchestrator, and its 8-vCPU/32-GiB shape is what `github-glue-runner.slice` assumes (`CPUQuota=400%`,
  `MemoryMax=8G`). **NOT** `i-0dd9812a96cdda5dc` (= `agent-orch-human-planning-vm`, 52.194.240.144, m7i.xlarge — the
  operator's interactive box).
- It has **no inbound SSH/:8765** → drive it via **AWS SSM**
  (`aws ssm send-command --region ap-northeast-1 --instance-ids i-0c9b283b31d6b5ca7 …`), the same channel as
  `/check-agent-orchestrator`. Then `bash scripts/self-hosted-runners/setup-glue-runners.sh install`.
- **Registration token = `GH_PAT` in GCP Secret Manager — CORRECTED 2026-07-16 (this doc previously named the WRONG,
  now-DEAD secret).** Probed all candidates against
  `POST /repos/IggyIkenna/unified-trading-pm/actions/runners/registration-token`:
  - ✅ **`GH_PAT`** → **201** (has `Administration:write`). Fine-grained (`github_pat_`), **never expires**. The fleet
    standard — `deployment-api`, `batch-live-reconciliation-service`, `client-reporting-api`, `alerting-service` and
    `scripts/workspace/load-gh-token.sh:68` (`--secret=GH_PAT`) all use it. **Use this one.**
  - ⚠️ `github-automation-token` → 201, fine-grained, non-expiring. Works, but only referenced by docs + a SIT probe
    (legacy "automation workflows" token). Valid fallback, not the standard.
  - ❌ `github-token` → **401 DEAD** (classic `ghp_`, created 2025-11-24, expired/revoked). **This doc used to name it**
    — following the old text would have failed the deploy on a 401. The 2026-07-15 `generate-jitconfig` verification was
    real but was done against `GH_PAT`; only the recorded secret NAME was wrong.
  - Prefer the Secret-Manager path (`GH_TOKEN_SECRET=GH_PAT`) so no PAT sits on disk — **but see the blocker below:
    `cmd_install` currently HARD-REQUIRES `GH_PAT` in the env, so the SM path can't be used for install as written.**
- **⛔ PRE-DEPLOY BLOCKER (found 2026-07-16):** `setup-glue-runners.sh cmd_install` does `[ -n "${GH_PAT:-}" ] || die`
  and writes the literal token into `/etc/github-glue-runner.env`. That directly contradicts this plan's own "prefer the
  Secret-Manager path so no PAT sits on disk". Fix `install` to accept `GH_TOKEN_SECRET` (write
  `GH_TOKEN_SECRET`+`GCP_PROJECT` to the env file, leave `GH_TOKEN` unset — the wrapper already resolves it at runtime
  via ADC) **before** deploying.
- Runner pinned **v2.335.1** + sha256 `4ef2f25285f0…` (in `setup-glue-runners.sh`). Then flip ONE canary
  (`reconcile-release-tags` — a MOVE workflow with `workflow_dispatch`; `branch-health` is now KEEP-M so it can't be the
  canary) → verify green → phased groups.
- **⚠️ Default-branch timing (easy to miss):** `schedule` and `repository_dispatch` workflows run the definition on the
  **default branch (`main`)** — so a `runs-on` flip on LDR does **nothing** until it promotes to `main`. To test the
  canary on the branch before it lands, trigger via `gh workflow run <wf> --ref live-defi-rollout`
  (`workflow_dispatch`), the same canary pattern `ldr-to-main-promote-fleet` documents. **Deploy the runners BEFORE the
  flip reaches `main`**, else every scheduled glue workflow on `main` queues with no runner (fleet-wide stall). Runners
  are repo-scoped (not branch-scoped), so once registered they serve any branch's jobs.

### Implementation specifics (so A1/A2/A5/2b aren't rediscovered)

- **A2 dedup** keys off fingerprints `ci_status_store.py` **already stores** — `sit_validated_tree` /
  `sit_validated_workspace_digest`; skip ONLY on an exact match to a GREEN record.
- **A1 regex** = `\.(md|mdc|rst|txt|svg|png|jpe?g|gif|ico)$` (from `base-service.sh:596`); extend the committed-diff
  check at `python-quality-gates-v2.yml` L170-202 / L585-607; `plans/**`+`codex/**` IN, lockfiles/YAML OUT.
- **A2 dead cache** at `python-quality-gates-v2.yml:90-137` (probe) + `:647-653` (`if:false` save), hardcoded
  `cache-hit=false` at L124.
- **STEP 2b trim** — `ci-status-update.yml` does `actions/checkout@v5` (~L54) + `google-github-actions/auth` (~L82) +
  runtime `pip install google-cloud-firestore` (~L104) + `python3 scripts/cicd/ci_status_store.py …` (~L117). Trim: lib
  pre-installed in the **runner slot's dedicated venv** (no per-run pip); drop the auth step (runner-user ADC);
  **pre-stage `ci_status_store.py` in the runner slot → NO checkout at all** (it only writes 1 Firestore row from the
  dispatch payload). Runner slot is a **separate folder/venv, isolated from AO**; **long-lived (non-ephemeral) pool**
  for this high-freq writer (JIT churn would dominate a ~3s job).
- **Re-measure (VERIFY)**: token via
  `gcloud secrets versions access latest --secret=github-billing-token --project=central-element-323112`;
  `curl …/users/IggyIkenna/settings/billing/usage?year=&month=`; per-workflow via
  `/repos/…/actions/workflows/{id}/runs?created=>DATE` `total_count` × billable-jobs (the timing endpoint returns 0 on
  this account — use the proxy). GitHub purges run history at ~90 days.

---

## MOVE / STAY manifest — the authoritative flip list (generated 2026-07-16 from `classify-glue-workflows.sh`)

> The classifier is the SSOT — regenerate with `bash scripts/self-hosted-runners/classify-glue-workflows.sh`. This
> pasted copy exists so "what moves / what stays" is unambiguous and conflict-free. **Split: 39 MOVE / 17 KEEP.**

**STAY on GitHub-hosted (17) — do NOT flip `runs-on`:**

| Workflow                      | Class      | Why it stays hosted                                                                                  |
| ----------------------------- | ---------- | ---------------------------------------------------------------------------------------------------- |
| `quality-gates-v2`            | KEEP       | real test gate (pull_request/push) — CPU-heavy pytest                                                |
| `python-quality-gates-v2`     | KEEP       | the reusable heavy QG (44 fleet callers) — stays hosted per the ADR                                  |
| `plan-health-agent`           | KEEP       | `pull_request`-triggered                                                                             |
| `conflict-resolution-merged`  | KEEP       | `pull_request`-triggered                                                                             |
| `build-smoke-all-repos`       | KEEP\*     | local docker buildx — too heavy for the light VM                                                     |
| `publish-package`             | KEEP\*     | local wheel build — heavy                                                                            |
| `main-backmerge-to-ldr`       | KEEP-T     | fleet template — flipping hangs ~24 repos; per-repo hand-edit banned                                 |
| `semver-agent`                | KEEP-T     | fleet template                                                                                       |
| `major-bump-issue-handler`    | KEEP-T     | fleet template                                                                                       |
| `request-major-bump`          | KEEP-T     | fleet template                                                                                       |
| `image-build-validate`        | **KEEP-R** | **cross-repo reusable — called by 24 repos; flip hangs their promote gate fleet-wide**               |
| `overnight-dead-man-switch`   | **KEEP-M** | **failure-independence — watches the orchestrator on THIS VM; must stay independent**                |
| `ci-health`                   | **KEEP-M** | **fleet-wide failure detector + stuck-PR auto-recovery; independence from our infra**                |
| `cloud-build-failure-watcher` | **KEEP-M** | **only detector for out-of-band Cloud Build failures**                                               |
| `ldr-ci-monitor`              | **KEEP-M** | **per-repo "is LDR green?" signal**                                                                  |
| `branch-health`               | **KEEP-M** | **promotion-lag / drift / AR-lag monitor**                                                           |
| `notify-slack`                | **KEEP-D** | **the alert carrier the KEEP-M monitors call — must be hosted so they can page when the VM is down** |

**MOVE off hosted (39)** — 38 by `runs-on` flip to `[self-hosted, glue]`, plus **`persist-cicd-event` = `MOVE-C`**
(convert to a composite action — do NOT flip its runs-on):
`agent-audit · agent-runner · cascade-qg-ordering · cassette-drift-check · change-freeze-check · ci-status-consolidator · ci-status-update · cloud-build-router-aws · cloud-build-router · cold-storage-cleanup · conflict-resolution-agent · deterministic-promotion-conflict-resolve · digest-drift-sweep · escalate-to-orchestrator · fix-approval-timeout · freeze-deferred-build-replay · hotfix-mode · ldr-to-main-promote-fleet · ldr-to-main-promote · ldr-to-staging-promote · overnight-agent-orchestrator · persist-cicd-event ⟵MOVE-C · plan-notification · readiness-verifier · reconcile-release-tags · reconcile-staging-versions · removed-symbols-workspace-sweep · rules-alignment-agent · ruleset-drift-alert · secret-health-check · sit-debounce-trigger · sit-gate · sit-unlock · staging-conflict-ldr-main-fallback · staging-to-main · supersede-stale-dep-update-prs · update-repo-version · version-registry-update · workspace-quickmerge-validation`.

> ⚠️ `change-freeze-check`, `agent-runner`, `escalate-to-orchestrator` are `workflow_call` reusables but **PM-internal
> only** (0 cross-repo callers — verified), so safe to flip. `persist-cicd-event` is a `workflow_call` reusable too but
> is **`MOVE-C`** — convert to a composite action (STEP 2c), not a flip. `overnight-agent-orchestrator` moves, but its
> watcher `overnight-dead-man-switch` stays hosted (KEEP-M) → a VM-down orchestrator is still caught. **Movers calling
> `notify-slack` need no change** — it keeps its own `runs-on: ubuntu-latest`, so GitHub runs that one job on a hosted
> runner even inside a self-hosted workflow.

---

## Why we are spending the money (evidence)

Pulled from the **live GitHub Enhanced-Billing ledger** (not estimates) via the existing `github-billing-token`:

- **100% of spend is Actions Linux compute minutes** — not storage, not packages, not Copilot.
- **June net $1,441 · July (1–15) net $485**
  (~$1,000/mo run-rate). Daily figures matched the operator's memory exactly
  (Jul 13 = $82, Jul 14 = $77).
- **PM is the single biggest repo — 35% of spend in June, rising to ~48% in July.**
- PM produced **1,000 workflow runs in a 13.5-hour window (~1,778/day)** during a code freeze. Trigger mix by billed
  share: **repository_dispatch 55% · schedule 18% · pull_request 13% · push 8% · workflow_dispatch 6%.** → **~79%
  automation, ~21% code, and only ~8% is PM's own commits.**
- All repos are **private** (every minute billed; public would be free) and there are **zero self-hosted runners**
  registered — the cheapest lever is completely untapped.

**Root cause:** PM is not expensive because it is a docs repo. It is the **CI/CD control tower** — every repo's CI
dispatches status/build/deploy jobs _into_ PM, and PM runs the fleet's promotion/health cron machinery. The cost is the
switchboard traffic + the timer-driven bots, both of which boot a full `ubuntu-latest` VM for lightweight glue.

### Top cost drivers in PM (13.5h sample, by est. billed-minute share)

| Workflow                      | Share | Trigger              | What it does                                                                                                                        | Assessment                                   |
| ----------------------------- | ----- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `ci-status-update`            | ~33%  | repository_dispatch  | Boots a 2-job VM every ~2.5 min to write ONE Firestore CI-status row for whichever repo just finished CI                            | Purpose right, mechanism ~100× too heavy     |
| `cloud-build-router` + `-aws` | ~20%  | repository_dispatch  | Routes a "QG passed → go build/deploy" dispatch to GCP + AWS, 3 jobs each, both fire on every green                                 | Fires even in freeze when nothing deploys    |
| `quality-gates-v2`            | ~18%  | pull_request         | The real tests/lint/typecheck — but splits into 5–7 jobs, each billed a 1-min minimum (9s "content sentinel" = 1 full min)          | Legit compute, inflated ~3× by fan-out       |
| promotion + health crons      | ~18%  | schedule (_/15–_/30) | `ldr-to-main-promote`, `-fleet`, `staging-to-main`, `branch-health`, `ci-health` — poll "anything to ship/any failures?" on a clock | Real safety nets; over-frequent + duplicated |

---

## Guiding principle

**GitHub-hosted runners are for running _tests_ in a clean throwaway box. Stop using them as the always-on _plumbing_
for status-writing, dispatch-routing, PR-opening, and health-polling.** That glue should run on compute we already pay
for 24/7 (self-hosted runner minutes are free from GitHub's side), or not boot a VM at all. Because every repo is
**private, there are no untrusted fork PRs**, so self-hosted runners are safe here even for PR-triggered workflows —
though we still keep heavy test jobs on hosted runners to avoid loading our own VMs.

---

## Proposed work (SUGGESTIONS — each is a decision, not a commitment)

### Phase 0 — Make the case airtight (do this first, low-risk, read-only)

- [x] ✅ [MEASURE] P1. Pull the **full 4-month (Apr–Jul 2026)** billed attribution + a 30-day per-workflow breakdown —
      DONE 2026-07-15. Results written to the companion doc §"Audit results — April–July 2026" (fleet monthly totals,
      per-repo 4-mo matrix, PM per-workflow + per-cluster). Key: fleet ~$1,000/mo steady-state (Jun peak $1,441, Apr
      ~$0
      pre-machinery); PM $808/4mo = 39% (share climbing to 47.7% in Jul); PM clusters ci-status-update 32% /
      promotion-health-bots 28% / quality-gates-v2 20% / agent-plan bots 13.5% / routers 5% (router **corrected DOWN**
      from the 13.5h sample's ~20%).
- [x] ✅ [MEASURE] P1. Confirm fleet-wide **zero self-hosted runners** + baseline — DONE 2026-07-15: `actions/runners`
      total_count = 0; rate $0.006/min; baseline = ~$1,000/mo fleet / ~$480–510/mo PM (the number the fixes are measured
      against). Evidence in the companion doc §"Audit results".

### Phase 1 — Self-host the switchboard + cron glue (biggest win, ~70% of PM)

- [x] ✅ [OPERATOR-DECISION] P1. **Runner host DECIDED (operator 2026-07-15): the planning-VM** (central orchestrator,
      `i-0c9b283b31d6b5ca7`, m8i.2xlarge 8vCPU/32GB). Capacity verified: glue ~1.7 cores avg vs ~7 idle; fits with a CPU
      cap. See companion doc §"Capacity assessment".
- [x] ✅ [INFRA] P1. **Runner infra files AUTHORED 2026-07-15** (created locally, NOT yet deployed) —
      `scripts/self-hosted-runners/`: `setup-glue-runners.sh` (install/status/teardown/prune), `glue-runner-run.sh`
      (JIT-ephemeral wrapper), `github-glue-runner@.service` + `.slice` (CPUQuota≤400% / MemoryMax 8G to protect AO),
      `classify-glue-workflows.sh`, `README.md` (runbook). Runner pinned **v2.335.1** + sha256; PAT can register (JIT
      verified); all glue is in PM so **repo-scoped runners**, no per-repo fan-out. shellcheck-clean. **Deploy step
      pending operator go** (run `setup-glue-runners.sh install` on the VM with an admin PAT).
- [ ] [REVIEW] P1. **Security gate:** the `classify-glue-workflows.sh` split is **39 MOVE / 17 KEEP** (see pre-flight
      § + §"MOVE / STAY manifest"). KEEP = the 4 test/PR gates + `KEEP*` builders (`build-smoke-all-repos`/
      `publish-package`) + `KEEP-T` templates (4) + **`KEEP-R` cross-repo reusable `image-build-validate`** + **`KEEP-M`
      failure-independence monitors (5)** (`overnight-dead-man-switch`, `ci-health`, `cloud-build-failure-watcher`,
      `ldr-ci-monitor`, `branch-health`) + **`KEEP-D` alert carrier `notify-slack`**. Confirm the MOVE set carries no
      untrusted fork-PR code (private repo → none) before flipping.

- [ ] [INFRA] P1. **`quickmerge.sh --agent` sentinel races its OWN rebase — WRITTEN UP, operator will fix later.** Full
      analysis (mechanism, line refs, repro, 3 candidate fixes + the negative test that must keep passing) lives in
      **`plans/active/issues/quickmerge_agent_sentinel_race_vs_own_rebase_2026_07_16.md`** — that doc is the SSOT; do
      not re-analyse it here. One-line essence: STAGE 0.4 rebases your local commits (new SHAs), then STAGE 3 demands
      the `.qg_last_passed_sha` sentinel be `==` HEAD or an ANCESTOR of it — which a rebase of your own commits makes
      impossible, so on a busy LDR `--agent` can never validate a sentinel it just wrote. **Working practice until
      fixed:** chain `quality-gates.sh --no-fix && quickmerge.sh …` in ONE shell (narrows the window; does not close
      it). Operator 2026-07-16: "we will also fix the issues with quickmerge --agent" — UNACKED, no plan owns it yet.

### ▶ DEPLOY RUNBOOK — D1…D6, strictly in order (operator-approved 2026-07-16)

> Everything buildable off-VM is DONE. These are the on-VM steps. Target = `i-0c9b283b31d6b5ca7`
> (`agent-orchestrator-vm-1`, VERIFIED) via **AWS SSM** (no inbound SSH). Token = **`GH_PAT`** (VERIFIED 201; the old
> `github-token` is DEAD/401). Do NOT skip D2 — `jq`/`npm` on that box are still genuinely unknown, and toolchain parity
> is the real migration risk.

- [x] ✅ [INFRA] P0. **D1 — `install` takes the Secret-Manager path — unified-trading-pm@d287a91cf.** `cmd_install` now
      requires **exactly one** of `GH_TOKEN_SECRET` (+ optional `GCP_PROJECT`) or `GH_PAT`, and **refuses both** (they
      can disagree, and silently preferring one would mean the token you think registers runners isn't the one that
      does). Secret path writes only the secret **NAME** to `/etc/github-glue-runner.env`, `GH_TOKEN` unset — the
      wrapper already resolved it at runtime via ADC. README + a real `--help` added. **Two failure modes pre-empted,
      both found while writing it:** (1) **ADC is PER-USER** and install runs as root while runners run as `ubuntu`, so
      a root-only ADC would pass install then leave 8 units crash-looping → install resolves via `sudo -u ubuntu`, the
      account that actually has to do it; (2) a token without `Administration:write` would fail at first start with an
      opaque journal → install probes `registration-token` (expects 201) up front. `status`/`prune` resolve the same way
      (explicit env → the name in the env file), so they survive a secret-path install; `status` degrades to omitting
      the live listing rather than dying. **Free side effect:** everything reads the secret's `latest` **by name**, so
      rotation needs no redeploy and no env-file edit. **Evidence:** 8/8 harness assertions incl. the REAL Secret
      Manager path (asserted by property, never by value); shellcheck clean (also fixed a pre-existing SC2015 on the npm
      branch); `quality-gates.sh --no-fix` **exit 0**.
- [ ] [SECURITY] P1. **Rotate `GH_PAT` — agent-caused exposure 2026-07-16. OPERATOR-DEFERRED to after this exercise**
      (operator 2026-07-16: "dont worry about the GH_PAT for now i will rotate it after we finish this exercise").
      **Rotation is SAFE whenever you want it — VERIFIED on the box, not assumed:** the PAT is read once at runner START
      (`glue-runner-run.sh:46-47`) purely to mint a JIT config / registration token; the running runner then
      authenticates with its OWN `.credentials`, so rotating deregisters nothing. Everything reads the secret's `latest`
      **by name**, and `glue-*` restarts after every job, so a new version is live within one job cycle (the writers
      pick it up on their next restart). **The real caution is other consumers** — check `deployment-api` and the other
      GitHub tokens for anything pinning a version or holding a copy BEFORE disabling the old version. While testing
      D1's resolver, a harness assertion compared the token **by value** and printed it on mismatch, putting the live
      `GH_PAT` (fine-grained, `Administration:write`, **never expires**) into the session transcript
      (`~/.claude/projects/…/03a5cc50-*.jsonl`) + that conversation's API context. Nothing published publicly. **Fix
      applied to the harness:** secrets are now asserted by PROPERTY (empty / non-empty / length), never by value — a
      failing assertion can no longer leak. **Operator action:** add a new version to the `GH_PAT` secret; every
      consumer reads `latest` by name so no redeploy is needed. Check other holders first (`deployment-api` and the
      other GitHub tokens the operator flagged) for anything pinning a version.
- [x] ✅ [INFRA] P0. **D2 — `preflight` GREEN on the VM (exit 0) — unified-trading-pm@940a5d673.** Ran via AWS SSM
      against `i-0c9b283b31d6b5ca7`. **It only became meaningful after being rewritten**, and that is the headline of
      this phase: the original checked `command -v` in _the caller's_ shell. Run from a login shell it reported **uv ✓**
      — while the runner, which systemd starts WITHOUT `~/.profile`, could not see uv at all. A preflight that passes in
      an environment the runner never uses is worse than none: a confident green on a box that fails 32 of the 38
      movers. It now reads the runner's PATH **from the unit file** (one SSOT, no drift), probes as `ubuntu` with
      `env -i` (scrubbed, so nothing inherited can fake a pass), and is **phase-aware** (before install: prove a venv
      _can_ be built; after: prove pip _does_ resolve).
- [x] ✅ [INFRA] P0. **D3 — scripts on the VM via a DEDICATED deploy clone — `/opt/glue-deploy/unified-trading-pm`.**
      Deliberately **not** the VM's existing PM clone: that one is stale (`09b90024b`, no runner scripts), is shared
      infra referenced by the 16 AO slot clones, and pulling it is a write to something I don't own. Fresh shallow clone
      on LDR instead (the plan's own "or clone fresh"). **Ordering finding: D3 must precede D2** — `preflight` only
      exists in the rewritten script, so the code must reach the box before the gate can run.
- [x] ✅ [INFRA] P0. **D4 — both pools installed, `install` exit 0 — unified-trading-pm@940a5d673.** First-ever
      end-to-end exercise of the systemd path; it failed **three times** first, all one root cause: creating a file
      needs write on the **PARENT**, and `${RUNNER_BASE}` is root-owned while the runner is `ubuntu`. (1) slot venv →
      `Permission denied: /opt/github-glue-runners/venv`; (2) the refresh timer's stamp → first tick failed; (3)
      `status` reported "no admin token resolvable" because plain `gcloud` as root used _root's_ ADC, which does not
      exist here — the same per-user-ADC rule I had encoded into `install` and then not applied to the next function.
      Fixed by pre-creating `venv`/`repo`/`toolcache` runner-owned, seeding the stamp, and routing **all** Secret
      Manager reads through one `secret_access()`. Base stays root-owned so a runner can't drop files at the top level.
- [x] ✅ [VERIFY] P0. **D5 — 8/8 runners live, labels DISJOINT — verified from GitHub's API, not just locally.**
      `5× glue-*` = `self-hosted,glue`; `3× writer-*` = `self-hosted,Linux,X64,glue-writer` (config.sh adds `Linux,X64`;
      JIT does not — harmless, since matching is a subset test and the writers lack `glue`, so they **cannot** steal
      mover jobs). All units active, refresh timer green, slice capped `MemoryMax=8G` / `CPUQuota=400%` away from the
      AO.
- [x] ✅ [VERIFY] P0. **D6 — CANARY GREEN on LDR, `main` untouched — run `29504914995`.** ⚠️ **The canary is
      `workspace-quickmerge-validation`, NOT `agent-audit`** (corrected again — see the KEEP-U finding below).
      Dispatched `--ref live-defi-rollout`; **`main` still says `ubuntu-latest`**, so nothing scheduled changed.
      **Evidence, all four required proofs:** (1) claimed by `glue-ip-172-31-5-118-4`, labels `self-hosted,glue`; (2)
      `completed success`; (3) **JIT lifecycle proven from the journal**, not inferred — `Running job: validate` →
      `Succeeded` → `Deactivated successfully` (exited after ONE job) → `Scheduled restart, counter 1` →
      `Connected to     GitHub` → `Listening for Jobs`; `glue-4 NRestarts=1` while `glue-1 NRestarts=0` (only the runner
      that took the job cycled), `_work` wiped; (4) **`billable: {}` — EMPTY**, i.e. the project's whole thesis
      measured: a hosted run bills a 1-minute minimum, this billed nothing.

### Flip groups — canary (1) → 10 (5 simple + 5 complex) → remaining 27 (operator 2026-07-16)

**Selection is EVIDENCE-BASED**, from profiling all 38 MOVE workflows by LOC · `workflow_dispatch` · job count ·
capabilities exercised (firestore/slack/persist/gcs/git-write/pr-write/dispatch/setup-python/app-token/gcp-auth/
upload-artifact). **The organising principle: the 10 cover EVERY capability class the remaining 27 use**, so once
they're green the tail carries **no new risk** — only more volume. **All 11 have `workflow_dispatch`**, so every one is
provable on LDR before `main` changes at all.

⚠️ **A dispatch RUNS the workflow for real.** Use `dry_run: true` where it exists (`reconcile-release-tags`,
`ci-status-consolidator`, `cold-storage-cleanup`, `staging-conflict-ldr-main-fallback`); `agent-audit` (`audit_only`)
and `reconcile-staging-versions` are no-op-safe by design.

| #   | Workflow                             | LOC | Group                                                  | Capability it PROVES                                                  |
| --- | ------------------------------------ | --- | ------------------------------------------------------ | --------------------------------------------------------------------- |
| 0   | `workspace-quickmerge-validation`    | 71  | **CANARY ✅ DONE**                                     | runner claims job · checkout · gh CLI · **JIT deregister** · artifact |
| 2   | `ruleset-drift-alert`                | 73  | ✅ VERIFIED — slack X-boundary ran on HOSTED           | **slack (CROSS-BOUNDARY)** · `setup-python` → **tool-cache**          |
| 3   | `conflict-resolution-agent`          | 94  | ⚠️ FLIPPED, NOT DISPATCHED (would escalate to AO)      | git-write · dispatch                                                  |
| 4   | `reconcile-staging-versions`         | 145 | ✅ VERIFIED — git-write                                | git-write (no-op safe)                                                |
| 5   | `digest-drift-sweep`                 | 191 | ⚠️ FLIPPED, NOT DISPATCHED (would fan out to 16 repos) | **gcp-auth / runner-user ADC** · dispatch                             |
| 6   | `reconcile-release-tags`             | 72  | ✅ VERIFIED — firestore/pr-write/setup-python/gcp-auth | firestore · pr-write · setup-python · gcp-auth                        |
| 7   | `ci-status-consolidator`             | 97  | ✅ VERIFIED — firestore WRITE                          | **firestore WRITE** · git-write (the manifest projection)             |
| 8   | `readiness-verifier`                 | 124 | ✅ VERIFIED — persist X-boundary ran on HOSTED         | **persist-cicd-event (CROSS-BOUNDARY)** · slack                       |
| 9   | `cold-storage-cleanup`               | 412 | ✅ VERIFIED — GCS (dry_run)                            | **GCS — the ONLY gcs workflow in the MOVE set**                       |
| 10  | `staging-conflict-ldr-main-fallback` | 188 | ✅ VERIFIED — app-token (dry_run)                      | **app-token** · pr-write                                              |

> **⚠️ CANARY CORRECTED TWICE — and the second correction is a rule, not a one-off (2026-07-16).** `agent-audit` was
> picked off a profile of LOC · triggers · job count · capabilities that never asked the one question this entire plan
> depends on: **does the workflow have a `runs-on` to flip?** It does not. Its single job is
> `uses: …/python-quality-gates-v2.yml@main` — a pure **reusable caller**, so the _callee_ picks the runner, that callee
> is a **KEEP**, and it is pinned `@main` so an LDR flip is inert twice over. Flipping it would have been a no-op that
> looked like progress. **Now machine-checked:** `classify-glue-workflows.sh` detects no-`runs-on` and returns
> **`KEEP-U`** (pure reusable caller). **Counts corrected: 39 MOVE / 17 KEEP → 38 MOVE / 18 KEEP**, of which **37 are
> flippable** (the 38th is `persist-cicd-event` = MOVE-C, converted not flipped). Verified: all 37 have a `runs-on`. The
> canary became `workspace-quickmerge-validation` — the true smallest flippable+dispatchable mover (71 LOC,
> `contents: read`, no external writes).

> **🔎 Host-mutation finding (2026-07-16):** `workspace-quickmerge-validation` ran
> `sudo apt-get update && apt-get install -y jq`. Harmless on a throwaway hosted VM; on self-hosted it mutates the
> **live orchestrator box** every 6h and can go red on an apt lock alone — a failure with nothing to do with the job.
> Now guarded (`command -v jq || install`), which is also strictly faster on hosted. **It is the ONLY workflow in the
> MOVE set that does this** (swept all 38), so this is a fixed one-off, not a class — but the pattern to watch when
> reading any remaining mover is "assumes a disposable VM".

**The two CROSS-BOUNDARY tests (#2, #8) are the most important in the batch** — they probe the single biggest
architectural risk in this design. Both are self-hosted CALLERS invoking a **hosted** reusable (`notify-slack` = KEEP-D;
`persist-cicd-event` = MOVE-C, still hosted until converted). A reusable's `runs-on` is independent of its caller, so
these prove the mixed hosted/self-hosted topology actually works — validating the KEEP-D decision **empirically rather
than by argument**. Run them EARLY in the batch; if they fail, the KEEP-D/MOVE-C reasoning is wrong and the remaining
flips must STOP.

**Remaining 27** = everything else, including the 10 with **NO `workflow_dispatch`** (`ci-status-update`, `sit-gate`,
`cloud-build-router`, `cloud-build-router-aws`, `update-repo-version`, `agent-runner`, `hotfix-mode`,
`change-freeze-check`, `plan-notification`, `sit-unlock`) — these are **only** validatable AFTER promote to `main`
(schedule/`repository_dispatch` run the definition from the default branch), so they go LAST and land with the watchdog
already live. `ci-status-update` is the special one: **`[self-hosted, glue-writer]`** + the STEP 2b trim.

> **⚠️ "CANARY ON LDR WITHOUT TOUCHING `main`" IS A COUNTDOWN, NOT A GATE — MEASURED 2026-07-16.** The D6 canary was
> flipped on LDR only, and the standing **`ldr-to-main-promote.yml` (`schedule`, v2-gated auto-merge) promoted it to
> `main` on its own** ~25 min later, with no human action. Observed promote runs: 12:49 → 13:37 → 14:28 UTC (nominally
> `*/15`; GitHub throttles `schedule:` ≈37%, so **assume 15–45 min**). This is the pipeline working exactly as designed
> (CLAUDE.md § "LDR is the SSOT; default promote is LDR→`main` DIRECT") — but it means **every batch goes fleet-live
> within ~45 min of landing on LDR, whether or not you have finished verifying it.** Consequences for the next 10:
>
> - **Do NOT plan to "hold" a batch on LDR.** The `--ref live-defi-rollout` dispatch buys you ONE verification cycle,
>   not an open-ended soak. Verify **immediately** after the dispatch, not "later today".
> - **This was safe for the canary only because the preconditions were already met**: runners live (8/8), the workflow
>   proven green on the pool, read-only (`contents: read`), and the VM-death watchdog live on `main` via hosted
>   `ci-health`. **Confirm those same four before each batch lands on LDR — after that it is out of your hands.**
> - If a batch genuinely must be held back, the flip cannot sit on LDR: either land it behind a `[hotfix]`-style gate,
>   or don't push it until you are ready to have it on `main`.

### ✅ BATCH 2 DONE 2026-07-16 — 9 flipped, 7/7 dispatched GREEN, 2 bugs found and fixed

**Both CROSS-BOUNDARY tests PASS — the design's biggest risk is now measured, not argued.** `readiness-verifier` ran on
`glue-…-4` and its two reusable jobs landed on **GitHub-hosted** runners:
`Slack — send-notification -> success on GitHub Actions 1000329229` and
`Persist — persist-event -> success on GitHub Actions 1000329231`. A self-hosted caller invoking a hosted reusable works
exactly as KEEP-D/MOVE-C predicted. **The flips may continue.**

**Two real bugs, both found by DISPATCHING rather than reading** — neither was visible in any static review:

1. **The shared tool cache RACED (my optimisation, my bug).** One `RUNNER_TOOL_CACHE` shared by all 5 runners looked
   like a free saving; `actions/setup-python` is **delete-then-create and not concurrency-safe**. Three jobs landed
   within 7s (`15:03:02` ruleset-drift-alert ✓ · `15:03:07` readiness-verifier ✗ · `15:03:09` reconcile-release-tags ✓)
   and the loser died on `cp: cannot create symbolic link '.../lib/libpython3.13.so': No such file or directory` — its
   directory deleted mid-copy. It bought ~10s/job and an **intermittent, load-dependent failure** across the 5 movers
   using setup-python: a flaky-CI generator that only appears under concurrency. **Now per-runner** (a sibling of
   `_work`, or the JIT wipe would destroy it every job). Fixed in @<see git>.
2. **`systemctl restart` killed the entire glue pool.** A JIT runner auto-deregisters on a clean exit, but SIGTERM
   leaves an **OFFLINE registration holding the deterministic name**; `generate-jitconfig` then returns **HTTP 409
   "Already exists"**, `curl -f` prints nothing, and `json_get` died with
   `JSONDecodeError: Expecting value: line 1 column 1` — a crash loop whose traceback never names the cause. The canary
   never hit it (clean exit); only a restart does. The wrapper now **self-heals**: it deletes a stale OFFLINE
   registration for its own name, **refuses** to touch an ONLINE one (that would yank a live runner off a running job),
   and surfaces the API's message instead of a JSON traceback. Verified on the box:
   `deleting stale OFFLINE registration … left by a SIGTERM'd predecessor` → Connected → Listening, 5/5 up.

**2 of the 9 are flipped but deliberately NOT dispatched** — a dispatch would have caused real fleet actions, and their
capabilities are already covered by `reconcile-release-tags` (gcp-auth, dispatch):

- **`digest-drift-sweep`** — only skips repos whose digest is current, and the fleet is currently stale (16 repos), so a
  dispatch would fan out `dependency-update` to all 16. A fleet action, not a runner test. It self-verifies on its next
  6-hourly tick.
- **`conflict-resolution-agent`** — requires 3 inputs and escalates to the agent-orchestrator; a dispatch would spawn a
  real AO worker chasing a fabricated conflict. It self-verifies on its next genuine `merge-conflict-detected`.

**Also fixed:** `.github/actionlint.yaml` now declares `labels: [glue, glue-writer]`. Without it actionlint flagged
`label "glue" is unknown` on every flipped workflow — noise the CANARY introduced and I missed, which would have grown
to 38 findings. Verified it still flags a typo'd label, so this is a declaration, not a blanket suppression; QG now
reports **actionlint clean across all 56 workflows**.

**Running total: 10 of 38 movers self-hosted** (canary + 9). Remaining: **27** + `persist-cicd-event` (MOVE-C).

### 🔑 THE VM MUST HAVE THE REPO'S PYTHON — `setup-python` deleted from the movers (operator 2026-07-16)

> **Operator, on seeing 5 movers still running `actions/setup-python`:** _"if the box doesnt have that version then it
> should be solved in the bootstrap setup script — if all the workflows will do setup-python then whats the use of long
> lived vm"._ **Correct, and the sharpest correction of this deploy.**

**What was actually happening:** the box **already had** Python 3.13.13 (uv-managed, the AO's own toolchain). I built
the slot venv on the **system** python (3.12.3) while `pyproject` declares `requires-python >=3.13,<3.14` — so the venv
could not satisfy the repo, every mover kept `actions/setup-python`, and **each job downloaded a THIRD copy of Python
onto a machine we pay for 24/7**. That is the ephemeral-hosted model rebuilt on our own hardware: it keeps the wasted
wall-clock and the ~400MB/runner, drops the benefit, **and it is what made the shared tool cache race that took the pool
down**. "The box doesn't have that version" was a **bootstrap gap**, not a reason to re-download per job.

**The fix (all measured on the box, not reasoned):**

- `bootstrap-ci-host.sh` → **`install_repo_python`** guarantees `REPO_PY=3.13` via **uv**, and `verify()` now FAILS if
  it is missing. Deliberately NOT deadsnakes: 3.13 is not in noble's apt and a third-party PPA on the live orchestrator
  VM is not a trade worth making — and uv fetches the **same python-build-standalone** `actions/setup-python` does, so
  it is the same interpreter, just **resident instead of re-downloaded**.
- `setup-glue-runners.sh` → the slot venv is built with **`uv venv --python 3.13 --seed`** (`--seed` is LOAD-BEARING: a
  bare `uv venv` has **no pip**, and 8 movers run `python3 -m pip install`), and `install` now **refuses** a venv that
  violates `requires-python`. `preflight` asserts the **version**, not merely that `python3` exists.
- The 3 flipped setup-python movers **drop the step entirely**.

**Result, measured:** runner `python3` → `/opt/github-glue-runners/venv/bin/python3` **Python 3.13.13**, pip 26.1.2,
SATISFIES `requires-python`, firestore pre-installed (STEP 2b). `readiness-verifier`'s `Set up Python` step (**7s/run**)
is gone from the step list — **note the honest number:** an earlier draft of this plan claimed **93s → 64s (−31%)** from
wall-clock. That was WRONG: a later run took 83s, and step-level timing shows the job's steps are only ~6-16s of a
64-93s run (the rest is queue + job setup, which this change does not touch). The real saving is **~7s/run**, and speed
was never the point; ~400MB of downloaded Python reclaimed; **the tool-cache race class is eliminated at the root rather
than mitigated.**

⚠️ **Coupling now recorded in each workflow: these are self-hosted-ONLY.** Restoring `runs-on: ubuntu-latest` on any of
them REQUIRES restoring `setup-python` with it, or they get the hosted image's default python.

⚠️ **Still open — the 2 setup-python movers not yet flipped** (`cassette-drift-check`,
`removed-symbols-workspace-sweep`) ask for **`python-version: 3.12`**, which contradicts the repo's own
`requires-python >=3.13,<3.14`. When they flip they will get the slot venv's 3.13. **Check that 3.12 pin is not
load-bearing before flipping them** — if it is, the fix is a second uv-managed interpreter, not a per-job download.

### Then the phased flip (operator pacing 2026-07-16: 1 → 10 → remainder)

- [x] [INFRA] P1. ✅ **STEP 2 — flip `runs-on`: 36 of 37 flippable DONE** — canary `workspace-quickmerge-validation`
      (unified-trading-pm@—) → batch 2 (9, @23ce709cc) → **batch 3 (26, @513f16773)**. Final state **35
      `[self-hosted,     glue]` + 1 `[self-hosted, Linux, X64, glue-writer]`** (`ci-status-update`, the one exception —
      plan L496). `persist-cicd-event` correctly NOT flipped (`MOVE-C` → STEP 2c); `agent-audit` reclassified `KEEP-U`
      (no `runs-on`) ⇒ 37 flippable, not 38. **Evidence:** `actionlint` exit=0 across all workflows;
      `quality-gates.sh     --no-fix` EXIT=0; live proof on the LDR ref — `secret-health-check` run 29556783346
      `check-secrets` → **`glue-ip-172-31-5-118-1` success** (its Slack job SKIPPED = dedup working = unbilled;
      `persist-event` hosted by MOVE-C design). Preconditions checked before flipping the promote critical path:
      watchdog LIVE on `main` (13/13 tests green) · pool 8/8 online · no docker/services/container/dynamic runners in
      the set · `agent-runner` safe (its ONLY caller `conflict-resolution-agent` is already glue — it is NOT the
      `persist-cicd-event` straddle) · `overnight-dead-man-switch` stays hosted (KEEP-M) so a VM-down orchestrator is
      still caught off-box. **1 of 37 DELIBERATELY NOT FLIPPED — `cassette-drift-check`**: flipping it would ACTIVATE a
      bug its own breakage was masking (see the finding below + issue doc). Remaining: STEP 2b trim · STEP 2c convert.
      (Takes effect on push — do NOT push until the runners are live, else those workflows queue with no runner.)
- [ ] [INFRA] P2. **STEP 2c — convert `persist-cicd-event` to a composite action (operator 2026-07-16, option C).**
      Rewrite the reusable workflow as `.github/actions/persist-event/action.yml` (a composite action wrapping the same
      build-JSON + GCS/S3/log-only write steps), then change all **22 callers** (5 KEEP + 17 MOVE) from
      `jobs.<id>.uses: ./.github/workflows/persist-cicd-event.yml` (a job) to a **step**
      `uses: ./.github/actions/persist-event` inside an existing job, and **delete** the old workflow. Effect: persist
      runs on the **caller's** runner (movers → VM/$0, KEEP callers → hosted, no VM-outage hang) AND stops being a
      separate 1-min-minimum billed job (the A3/A4 saving, fleet-wide, done properly). Keep it best-effort
      (`continue-on-error`) exactly as today. Sequence: land with / after the STEP 2 flip (converting before the movers
      are self-hosted gains nothing). Supersedes options-doc A3 (and the persist half of A4).
  - **⚠️ Canary caveat for dispatch-only movers (`repository_dispatch`/`schedule`, NO `workflow_dispatch`):**
    `ci-status-update`, `cloud-build-router*`, `sit-gate`, `sit-unlock`, `hotfix-mode`, `update-repo-version` **cannot
    be canaried on LDR** — `gh workflow run --ref` needs a `workflow_dispatch` trigger, and dispatch/schedule workflows
    only execute their definition from the **default branch (main)**, so the flip is inert on LDR and goes fleet-live
    the instant it hits main. To canary these: **(a)** temporarily add a `workflow_dispatch:` trigger, fire it on LDR,
    remove it after (true pre-merge canary); or **(b)** promote that one flip to main alone with the runners already
    live and a fast revert ready. Do the workflow_dispatch-capable canary (`reconcile-release-tags`) FIRST regardless,
    to prove the pool.
- [ ] [INFRA] P2. **STEP 2b — `ci-status-update` warm-VM trim (do it PROPERLY, operator 2026-07-15).** Confirmed
      structure: `ci-status-update.yml` `update-ci-status` job does `actions/checkout@v5` (L54) +
      `google-github-actions/auth@v3` (L82) + `pip install google-cloud-firestore` (L104) — ~15s on a warm VM for a
      1-row write. A plain `runs-on` flip keeps all three (the runner executes the YAML steps in an isolated `_work`,
      not the VM's warm state). Trim so it uses the warm state: **(1)** the lib is **pre-installed in the runner slot's
      dedicated venv** (see runner-isolation decision below) — no per-run `pip install`; **(2)** drop the `auth` step —
      the Firestore client uses the runner user's ADC; **(3)** avoid a fresh clone. Note `ci_status_store.py` only
      writes one Firestore row from the dispatch payload, so the cleanest form is **pre-stage the script in the runner
      slot and do NO checkout at all** (lighter than a `git fetch`, and it sidesteps any clone-freshness question).
      Result: **~2-5s, near-zero boot churn**. Guard the trimmed steps to self-hosted only. Highest-frequency mover
      (~13k/mo); apply the same pattern to other high-freq movers with redundant setup.
- [x] [INFRA] P1. ✅ **Runner-slot design — DONE** (unified-trading-pm@c44ca1bd4). Two-pool design implemented across
      `setup-glue-runners.sh` (slot: `${RUNNER_BASE}/{repo,venv,toolcache}`; `GLUE_COUNT=5`/`WRITER_COUNT=3`; new
      `preflight`), `glue-runner-run.sh` (forks on the `<pool>-<idx>` systemd instance name), and
      `github-glue-runner@.service`. Evidence: `bash -n` + `shellcheck -S warning` clean on all 5 scripts; pool/index
      fork unit-tested incl. double-digit indices and the unknown-pool reject; classifier re-run unchanged at **39 MOVE
      / 17 KEEP**; `quality-gates.sh --no-fix` EXIT=0. **NOT yet deployed** — no `install` has run on the VM. Original
      todo text retained below for the decision record. **Runner-slot design (operator 2026-07-16 — resolves the
      review's #9/#10/#11).** The glue runners live in their **own folder under `/opt/github-glue-runners`** with their
      **own venv** and their **own clone** of any repo CI needs (NEVER an AO slot clone — removes the live-worker race
      the review flagged); the pre-installed `google-cloud-firestore` (STEP 2b) lives in **that slot's venv**, not any
      AO/system Python. **Scope of isolation = FOLDER/VENV/CLONE ONLY (operator 2026-07-16):** `User=ubuntu`, reusing
      the VM's existing GCP/AWS/GitHub creds and existing toolchain — **no dedicated OS user, no separate SA.**
      Rationale (operator, accepted after challenge): everything needing true clean-room isolation (QG, PR gates, image
      builds) is already GitHub-hosted and stays there; the MOVE set is all first-party automation with **zero
      `pull_request` triggers**, all repos are private (no fork PRs → no untrusted code path), and **the AO already runs
      as `ubuntu` with the same ambient creds**, so glue-as- `ubuntu` barely moves the blast radius. VERIFIED not a
      hazard: the two MOVE workflows doing `git config --global` (`deterministic-promotion-conflict-resolve` L95,
      `rules-alignment-agent` L69) cannot corrupt AO commit attribution because every clone (slot + root) carries a
      **local** identity that overrides `--global`; a `HOME` redirect was considered and REJECTED (it would break
      `$HOME/.config/gcloud` ADC resolution to fix a non-problem). **Runner mode: LONG-LIVED (non-ephemeral) pool for
      the high-frequency writer** (`ci-status-update`) with per-job `_work` cleanup — at ~2-5s runtime the JIT
      re-registration overhead (generate-jitconfig + config + connect, several seconds) would otherwise dominate and cap
      burst throughput; keep JIT-ephemeral for the low-frequency movers where clean-state-per-job is cheap. Update
      `setup-glue-runners.sh` / `glue-runner-run.sh` to the two-pool design before deploy (currently they assume a
      single JIT-ephemeral pool).
- [x] [INFRA] P1. ✅ **Two-pool mechanics — all 4 gaps FIXED** (unified-trading-pm@c44ca1bd4). (a) JIT/long-lived fork
      landed: `glue-*` keeps `run.sh --jitconfig`; `writer-*` registers once via `config.sh --unattended --replace` + a
      `registration-token`, guarded on the `.runner` marker so a restart reconnects instead of re-configuring, then
      loops `run.sh`. (b) Labels DISJOINT: `self-hosted,glue` vs `self-hosted,glue-writer` (writer omits `glue`). (c)
      `_work` cleanup moved to `job-cleanup.sh` via `ACTIONS_RUNNER_HOOK_JOB_COMPLETED`, with `GLUE_RUNNER_DIR` exported
      by the wrapper so the hook cd's to the runner root instead of guessing from `RUNNER_WORKSPACE`. (d) `prune` scoped
      to the ephemeral prefix — **unit-tested against a fixture where `writer-planning-1` is OFFLINE and correctly
      SURVIVES** while `glue-planning-1` is pruned. Also: `RUNNER_COUNT` → `GLUE_COUNT`/`WRITER_COUNT`; dropped a `jq`
      dependency from my own scripts (python3 is guaranteed, jq is a verify-at-deploy item). Two self-inflicted bugs
      caught pre-commit: backticks in a `die` string would have **executed** `gh auth status`, and the status/prune
      f-strings nested double quotes (a syntax error below Python 3.12) — both rewritten and the embedded Python
      unit-tested. Original todo text retained below. **Two-pool mechanics — the 4 correctness gaps the authored scripts
      have (found 2026-07-16 during the redesign; each BREAKS the long-lived pool).** (a) **JIT ≠ long-lived**:
      `--jitconfig` is inherently single-use (auto-deregisters after one job), so the writer pool must use
      `config.sh --token <registration-token>     --unattended --replace` once at install then loop `run.sh` — a genuine
      fork in the wrapper, not a flag; note the writer's `.credentials` DOES then sit on disk (feeds the security-codex
      todo). (b) **Labels must be DISJOINT, not nested**: label matching is a subset test, so a writer labelled
      `self-hosted,glue,writer` would still match `runs-on: [self-hosted, glue]` and steal movers' jobs → writer carries
      **`self-hosted,glue-writer` WITHOUT the `glue` label**; consequence: `ci-status-update.yml` is the **one** MOVE
      workflow not getting the uniform flip recipe. (c) **`_work` cleanup silently stops**: `glue-runner-run.sh:38`
      wipes `_work/*` at wrapper start, correct only for one-process-one-job → a long-lived runner never cleans and
      grows unbounded; use the runner's `ACTIONS_RUNNER_HOOK_JOB_COMPLETED` post-job hook. (d) **`prune` would
      deregister the writer**: `setup-glue-runners.sh:119-130` deletes any OFFLINE `glue-*` runner, but a long-lived
      writer is _legitimately_ offline across reboot/redeploy → prune must target the **ephemeral prefix only**. Also
      split `RUNNER_COUNT` into `WRITER_COUNT`/`GLUE_COUNT` (propose 3 writers + 5 ephemeral: 13k/mo ≈ 18/hr × ~3s is
      trivial; the 3 is purely fleet-wide burst headroom, e.g. 24 repos firing at once).
- [x] [INFRA] P2. ✅ **Refresher AUTHORED** (unified-trading-pm@c44ca1bd4) — `refresh-slot-repo.sh` +
      `github-glue-slot-refresh.{service,timer}` (10-min `OnUnitActiveSec`, `OnBootSec=2min`, `Persistent=true` so a
      rebooted VM refreshes immediately rather than serving a pinned mirror). FF-pull only — the slot clone is a
      read-only mirror so `pull --ff-only` must always succeed; a non-FF means something dirtied it, and the script
      **fails loudly rather than forcing** (deliberately no `reset --hard`, which would discard the evidence). Stamps
      `repo.refreshed-at`; `setup-glue-runners.sh status` flags it RED past 30 min. **Timer not yet running** (deploy
      step). Original todo text retained below. **Pre-staged clone needs a REFRESHER (gap found 2026-07-16 — not
      previously in this plan).** STEP 2b pre-stages `ci_status_store.py` in the runner slot so the writer does **no
      checkout at all**. If that clone is pinned at install time it silently drifts from `main` and the writer keeps
      writing Firestore rows with **stale logic** — quiet wrongness, the bad kind. Add a systemd timer doing
      `git -C ${SLOT}/repo pull --ff-only` (+ a staleness assertion the writer can fail loudly on).
- [x] [INFRA] P0. ✅ **Queue-starvation watchdog — BUILT** (unified-trading-pm@6901779de, PR #1086 auto-merge).
      `detect_glue_starvation()` + `_glue_runner_counts()` + a `glue-runners-starved` item from the **pure**
      `build_alert_items()` → `scripts/repo-management/ci_failure_watcher.py`, i.e. **inside `ci-health`'s
      already-billed `watch` job — no new workflow, no new job, ~$0** (vs ~$52/mo standalone `*/5`). `CRITICAL` +
      `RENAG_GLUE_STARVED_MIN = 15` → the carrier re-nags every 15 min while it re-detects, exactly as asked; new
      `--glue-queued-minutes` (default 10) makes the threshold tunable. Detects on **queued-age**, so it catches a
      **wedged** pool too, and the message separates the faults ("0 runners ONLINE → VM down" vs "runners ARE online but
      not draining → wedged") and carries stakes + fix + rollback. **Costs ONE gh call when nothing is queued** (the
      normal case) — per-run job lookups only fire once something is already stale. **Evidence:** 13 new tests, 181/181
      watcher tests green, `quality-gates.sh --no-fix` EXIT=0. **Mutation-tested, not just green**: removing the
      glue-label guard fails `test_hosted_job_queued_does_not_page`; ignoring job status fails
      `test_running_job_is_not_starved` — so the two guards are provably load-bearing. The false-positive guard matters
      most: a HOSTED job queueing on GitHub's own capacity is **not** our outage, and paging on it would train the
      operator to ignore the alarm that exists to say the VM died. QG caught 3 real lint errors of mine (C420/E501/N802)
      — fixed. **NOT yet verified against a live outage** (no runners exist yet); the deploy proves it end-to-end.
      Original todo text retained below. **Queue-starvation watchdog — BLOCKS THE FLIP (operator 2026-07-16).** After
      the move a dead VM is **SILENT**: dispatches are still accepted, jobs sit `queued`, and **nothing pages** —
      verified by grep, all 5 KEEP-M monitors (`ci-health`, `branch-health`, `ldr-ci-monitor`,
      `cloud-build-failure-watcher`) have **ZERO** references to queued/runner state; they detect _failures_, and a
      queued job isn't a failure until GitHub kills it at **24h**. That window = lost `ci_status` transitions → stale
      Firestore → blocked promotes (`MAIN_GREEN` is the dep-on-main gate `staging-to-main.yml` STAGE 1.8 reads). **Not a
      billing risk** (queue time is free — see the Progress Log), purely correctness. **Operator requirement: queued >10
      min → page LOUDLY every 15 min until fixed.** **Design (decided — do NOT build a standalone workflow):** fold the
      detector into **`ci-health`**, which is already `KEEP-M` hosted (correct independence — it must not run on the box
      it watches), already crons **`*/15`** (exactly the requested cadence), and already matrix-fans `alerts` through
      `notify-slack` with per-item `dedup_key`+`cooldown_min` (the re-nag machinery EXISTS). **Cost is the reason:** a
      standalone `*/5` watchdog = **~$52/mo** and `*/15` = **~$17/mo** (1-min minimum × runs), which would eat a third
      of the saving we're chasing; a **step inside `ci-health`'s already-billed `watch` job = ~$0**, and the `notify`
      job only bills when firing. Implementation: new `RENAG_GLUE_STARVED_MIN = 15`; an IO detector; emit an item from
      the **pure** `build_alerts()` (`{key, severity, cooldown_min, message, url}`) →
      `scripts/repo-management/ci_failure_watcher.py`. Detect on **queued >10 min** (not "0 runners online") so it also
      catches a **wedged** pool, and put runner state in the message so the responder can tell "VM down" from "pool
      wedged". `severity: CRITICAL`, stable `key`, recovery bookend on a distinct short-cooldown key. **`ci-health` must
      stay KEEP-M forever** — flipping it would make the watchdog queue behind the very outage it exists to report.
- [x] [INFRA] P1. ✅ **Failsafe CI-host bootstrap AUTHORED + container-PROVEN** (unified-trading-pm@80f00684a).
      `scripts/self-hosted-runners/bootstrap-ci-host.sh` takes a bare Ubuntu box to CI-ready assuming NOTHING present:
      base OS deps → `gh` (official apt repo) → `gcloud` → `aws` v2 → `uv` (installed **for the runner user**, not root
      — root's `/root/.local` would be invisible to the runner) → `nodejs/npm` → verify. `--check` verifies without
      installing. **Evidence: full run against a bare `ubuntu:24.04` container → all 10 tools resolve, EXIT=0.** That
      run **earned its keep immediately**: it caught a `sudo: command not found` — the script itself calls
      `sudo -u ${RUNNER_USER}`, but cloud images ship `sudo` so the dependency was **invisible on planning-VM** and
      would have surfaced only on a minimal/hardened image mid-incident. Exactly the assumed-present class the operator
      predicted. `sudo` + `python3-venv` (a SEPARATE package — `command -v python3` passes while `python3 -m venv`
      fails, and the slot venv needs it) are now explicit in `install_base` with the provenance recorded inline.
      Original todo text retained below. **Failsafe CI-host bootstrap script (operator 2026-07-16).** The current design
      deliberately reuses planning-VM's existing toolchain + creds — which **hides the dependency**: if that VM dies and
      we must stand up a replacement CI host, we don't know what it actually needs, and `preflight` only _checks_ (it
      would fail on a bare box with no path forward). Author `scripts/self-hosted-runners/bootstrap-ci-host.sh` that
      provisions a **bare Ubuntu** box to CI-ready — **assume NOTHING is present**: OS deps,
      `git`/`jq`/`python3`+venv/`uv`/`gh`/`gcloud`/ `aws`/`npm`, cloud auth (GCP ADC + AWS), then hand off to
      `setup-glue-runners.sh install`. **Operator discipline: UPDATE THIS SCRIPT AT EVERY DEPLOY STEP** — each time the
      real deploy reveals something missing/assumed, fold it back in, so the script converges on truth instead of
      drifting into fiction.
- [ ] [VERIFY] P1. **PROVE the bootstrap on a bare host** — ⏳ **PARTIAL** (unified-trading-pm@80f00684a). ✅
      **Container leg DONE**: bare `ubuntu:24.04` → EXIT=0, all 10 tools resolve; found + fixed the `sudo` assumption.
      Reproduce:
      `docker run --rm -v "$PWD/bootstrap-ci-host.sh:/b.sh:ro" ubuntu:24.04 bash -c 'useradd -m -s /bin/bash ubuntu; bash /b.sh'`.
      ❌ **STILL UNPROVEN — a container structurally cannot exercise these:** IMDS / EC2 instance role · GCP ADC
      (interactive; STEP 2b's trim depends on runner-user ADC) · **systemd — so `setup-glue-runners.sh install` (units,
      slice, refresh timer) is UNTESTED end-to-end** · actual runner registration against GitHub. **Do NOT tick this off
      the container pass**; it closes only when a real bare VM runs it. The upcoming planning-VM deploy proves the
      systemd/registration legs; the bare-VM leg stays open until we genuinely rebuild a host.
- [ ] [INFRA] P2. **Toolchain parity with `ubuntu-latest` (gap found 2026-07-16 — the real migration risk, not
      isolation).** ⏳ **PARTIAL** (unified-trading-pm@c44ca1bd4): the inventory is measured and
      `setup-glue-runners.sh preflight` is written (checks `gh`/`jq`/`python3`/`uv`/`aws`/`gcloud`/`git` fatally, `npm`
      advisory), and the shared `RUNNER_TOOL_CACHE=${RUNNER_BASE}/toolcache` is wired into the wrapper so
      `actions/setup-python` pays the download cost ONCE across all runners instead of per job. **Still open: run
      `preflight` ON the box** — nothing here is verified against the real VM yet, so `jq`/`npm` presence remains
      unknown. Do this at deploy, BEFORE any flip. Hosted images pre-seed a large toolchain; the VM has
      gcloud/gh/python/uv. MOVE-set inventory: `gh` 181 · `jq` 111 · `python3` 105 · `uv` 32 · `aws` 22 · `gcloud` 16 ·
      `pip` 15 · `npm` 1. **`docker` = FALSE ALARM** (all 21 hits are a step _named_ `docker-build` that only dispatches
      to Cloud Build, plus the Artifact Registry hostname in `gcloud artifacts docker images describe`) — nothing
      invokes the daemon, which independently confirms the classifier's heavy-detection. **Verify `jq` + `npm` on the
      box at deploy.** Real friction = **`actions/setup-python@v6` on 5 movers** (`cassette-drift-check`,
      `readiness-verifier`, `reconcile-release-tags`, `removed-symbols-workspace-sweep`, `ruleset-drift-alert`): hosted
      pre-seeds the tool cache, self-hosted resolves against `RUNNER_TOOL_CACHE` and on a miss downloads/builds a Python
      **per job** — won't break, but turns a ~5s job slow. Pre-seed the tool cache once at install.
- [ ] [VERIFY] P1. **Use `scripts/cicd/measure-billed-notify-cost.sh`** (promoted out of a scratchpad 2026-07-16 — it is
      what produced this plan's notify-slack numbers, and the measurement took THREE attempts to get right: skipped jobs
      are not billed, and a throttled API call silently counts as 0). After 3–5 days, re-measure PM's billed minutes
      (ledger); confirm the moved workflows bill ~$0 and the VM absorbed the load without contention (slice
      `MemoryCurrent` < 8G, orchestrator load unaffected).
- [ ] [DOCS] P2. **Codex: write down the self-hosted-glue security posture (operator 2026-07-16 — important, not
      blocking).** On self-hosted runners the runner user carries the VM's **ambient cloud identity** (ADC + AWS-WIF) —
      STEP 2b drops the per-job `auth` step _precisely because_ of this — so every glue job runs with the runner slot's
      cloud creds, a wider blast radius than GitHub-hosted's scoped short-lived tokens. Mitigation posture to record: a
      **dedicated low-privilege runner user + scoped service account** (separate from the orchestrator SA), the runner
      in its own isolated slot (already decided); and **if the exposure ever becomes a real concern, move the runners to
      a dedicated VM** (operator's stated fallback). Update `codex/05-infrastructure/` (runner conventions) +
      `codex/07-security/`. Reduced severity given the slot-isolation; documented so the posture is explicit. **Two
      facts MEASURED on the box at D4/D6 (2026-07-16) that this doc must record, because both correct a claim the design
      comments currently make:** (1) **the JIT config is passed as a COMMAND-LINE ARG**
      (`run.sh --jitconfig     <base64>`), so the blob — which decodes to `.credentials` incl. the auth URL and RSA
      params — is visible in `ps` to any local user. Single-use and auto-deregistered, and the box is effectively
      single-tenant (`ubuntu` + root, and the AO already runs as `ubuntu`), so this is consistent with the accepted
      isolation scope — but it is NOT the "no credential exposure" the JIT-vs-long-lived framing implies. (2) **the
      ephemeral pool DOES write `.credentials` / `.credentials_rsaparams` / `.runner` to disk**, contradicting the
      letter of `glue-runner-run.sh`'s "No long-lived `.credentials` on disk". The spirit holds — they are single-use,
      replaced each cycle, and belong to an already-deregistered runner — but the wrapper wipes only `_work`/`_diag`, so
      a stale (useless) credential file persists between cycles. Fix the comment, and decide whether to wipe them too.
- [x] ✅ [OPERATOR-DECISION] P2. **Failure-independence RESOLVED (operator 2026-07-16 — the review's #2).** The 4
      CI-health watchers (`ci-health`, `cloud-build-failure-watcher`, `ldr-ci-monitor`, `branch-health`) **STAY HOSTED**
      (`KEEP-M`) alongside `overnight-dead-man-switch` — GitHub-hosted is the right home for light monitors whose value
      is independence from our infra. They cost a few
      $/mo total; keeping them hosted means a VM/pool outage never
      blinds the fleet's failure detection + auto-recovery. (No runner-offline page needed — the watchers ARE the
      independent signal.) **Corollary (final review):** the watchers' shared alert carrier `notify-slack` must ALSO
      stay hosted (`KEEP-D`) or they'd detect-but-not-page during a VM outage — measured cost ~$1/mo.
      Split → **39 MOVE / 17 KEEP**.

### Phase 2 — Shrink the fleet-wide hosted QG (the real $ that stays on GitHub-hosted: A1 + A2 + A5)

> These three touch the shared reusable `python-quality-gates-v2.yml` (44 callers, all ~25 repos) → fleet-wide savings.
> QG is the ADR-sensitive gate — no coverage loss, green-only guards.

- [ ] [INFRA] P1. **A1 — docs-only fast-path (operator: do it).** Extend the committed-diff check
      (`python-quality-gates-v2.yml` L170-202 / L585-607) to the `base-service.sh:596` docs regex so a pure
      docs/plans/codex change skips the ~12-min pytest+typecheck legs (keep lint-codex). Scope: `plans/**`+`codex/**`
      IN, lockfiles/workflow-YAML OUT. Also gate `dispatch-cloud-build` on `docs_only!='true'`.
  - **🔴 CORRECTNESS (do it PROPERLY — operator 2026-07-16, "this is the whole point of CI"):** the skip MUST still
    **report the required `quality-gates-v2` status check as SUCCESS for the PR-head SHA** — a _green_ skip, NOT an
    absent check. Branch protection hard-requires that context; if the fast-path makes it MISSING, the branch-protected
    LDR→main promote PRs (the biggest beneficiary) go **permanently BLOCKED** (the same `[skip ci]`→missing-check hazard
    in CLAUDE.md). Verify on a real docs-only promote PR that the required check goes green, not that it vanishes.
- [ ] [INFRA] P1. **A2 — FIX the content-gate dedup properly (operator: fix now).** Rebuild the byte-identical-tree skip
      on the **Firestore tree-fingerprints** (replace the broken `actions/cache` at L90-137 / L647-653). **Correctness
      guard: skip ONLY when that exact tree previously passed GREEN** (never off a failed/unknown run); relies on QG
      determinism. Fleet-wide (does NOT touch SIT; never skips a changed tree).
  - **🔴 CORRECTNESS (operator 2026-07-16, "make it proper"):** "same tree → same result" holds ONLY if the **gate
    itself** is unchanged. The dedup key MUST therefore include the **gate/ruleset version** (the
    `python-quality-gates-v2` workflow + base-script fingerprint / a `QG_GATE_VERSION` bump), not just the source-tree
    hash — otherwise a gate-logic change over a byte-identical tree would skip a run the _new_ gate would fail. AND (as
    with A1) the skip must still **post the required check as SUCCESS for the current SHA**, per-branch — a prior green
    on branch X must not leave branch Y's required context absent. Test: change the gate over an identical tree →
    confirm it does NOT skip.
- [ ] [INFRA] P2. **A5 — collapse the fan-out (operator: measure-then-collapse).** Confirm the merged
      `typecheck`+`lint-codex` leg stays under the pytest leg on the slowest repo, then merge + fold the sub-minute jobs
      (content-sentinel/Slack/dispatch). Target ~30–40% fewer billed job-minutes/run, no coverage loss.
- [ ] [VERIFY] P2. Re-measure a representative QG run's billed job-minutes + the docs-PR / identical-tree skip rates
      before/after (ledger + run counts).

### Phase 3 — Cadence + de-duplication (cheap wins)

- [x] ✅ [OPERATOR-DECISION] P2. **Promote bots — KEEP BOTH (operator 2026-07-15; "retire duplicate" WITHDRAWN).**
      Re-inspection: `ldr-to-main-promote` is **PM-only** and `ldr-to-main-promote-fleet` serves the **23 `ldr_main`
      repos** (PM excluded, `promotion_model` unset) — disjoint scopes, complementary, NOT duplicates. Optional future
      consolidation only (moot once self-hosted at $0).
- [ ] [INFRA] P2. Slow promotion/health crons from `*/15` toward **hourly** (or purely event-driven off the promotion PR
      event) during freeze; keep the event path for real-time needs. Lower priority once these are on self-hosted, but
      fewer idle boots is cleaner regardless.
- [ ] [INFRA] P3. **Debounce `ci-status-update`** — coalesce multiple repo reports arriving within a short window into
      one write instead of N runner boots (careful to preserve the CAS + stale-write ordering the Firestore store relies
      on).

### Phase 4 — Serverless (B2) — DROPPED (operator 2026-07-15)

- [x] ✅ [OPERATOR-DECISION] P3. **B2 DROPPED.** ci-status-update runs on the VM (B1) with its setup trimmed (STEP 2b) →
      ~2-5s at $0; the only thing serverless would add (~1s + zero boot churn) is irrelevant at the promotion crons'
      15-min read cadence. The `deployment-api` endpoint stays a cheap **fallback** to revisit ONLY if VM churn/latency
      ever bites — not planned now.

### Phase 5 — Prove the savings

- [ ] [VERIFY] P3. Two weeks after rollout, re-pull the billing ledger and compare to the Phase-0 baseline; record
      actual $/mo saved per repo. Target landing: **fleet ~$1,000/mo → ~$300–400/mo**, and structurally flat when
      activity grows (glue cost stays on our VM; only real test minutes scale).

---

## Expected impact (rough — Phase-0 will make exact)

| Step                                         | Effort | Est. monthly saving            |
| -------------------------------------------- | ------ | ------------------------------ |
| 1. Self-host switchboard + cron glue         | Low    | ~$400–500 fleet                |
| 2. Collapse `quality-gates-v2` fan-out       | Low    | ~$50–80                        |
| 3. Retire duplicate promote bot + slow crons | Low    | ~$30–50                        |
| 4. (Later) Serverless `ci-status-update`     | Medium | folds into #1, removes VM load |

## The honest tradeoff

Self-hosted runners are infrastructure **we** now maintain (patching, disk, capacity, auto-restart). For lightweight
glue on a VM we already run 24/7 that is nearly free. For heavy test fleets it is real work — which is exactly why the
proposal keeps heavy test jobs on GitHub-hosted and only moves the glue.

## Decisions — RESOLVED (operator 2026-07-15)

All closed; full ledger in the companion doc §"Decisions — MADE". In short: (1) direction approved; (2) runner host =
the shared orchestrator/planning-VM; (3) promote bots — **keep both** (not duplicates, disjoint scopes); (4) **B2
serverless DROPPED** — ci-status-update runs on the VM with its setup trimmed to use warm state; (5) cron cadence —
disable dead staging crons, **leave promotion crons at `*/15`** (they're $0 self-hosted; the SLA was deliberate).

## Codex SSOTs (read before executing any item)

- `codex/08-workflows/ci-cd-flow.md` — quickmerge / LDR-is-SSOT / promotion flow / branch protection
- `codex/05-infrastructure/` — runner + VM infra conventions; workflow-template rollout
- `codex/04-architecture/ci-alerting.md` — notify-slack carrier (touched if cron cadence changes)
- Related: `plans/active/issues/github_billing_dashboard_access_2026_07_09.md` (the billing-token that made this
  measurable), `plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` (the LDR→main promotion refactor this
  overlaps)

## Progress Log

- 2026-07-16 — **Hosted baseline + full VM pre-seeding (operator-directed). STOPPED at the operator's gate — no further
  workflows flipped.** Two operator asks, both done:
  1. **BACKUP ALL 56 WORKFLOWS** (`scripts/self-hosted-runners/hosted-baseline.sh` + `hosted-baseline/`): the migration
     was a **one-way door** without this — flipping deleted work the VM does (setup-python, pip installs), so reverting
     `runs-on` ALONE would give a hosted job with no Python set up: broken in a NEW way. `snapshot` recovers the 10
     already-flipped workflows from **git history** (parent of the first commit introducing `self-hosted, glue`, which
     predates every change this epic made to each), and copies the other 46 live. **Verified, not assumed:**
     setup-python RECOVERED in all 3 files I had deleted it from; the original UNGUARDED `apt-get install jq` recovered;
     0 baselines carry the flip marker; 56/56 valid YAML; **round-trip tested** (restore → `ubuntu-latest` **with** its
     setup-python, actionlint-clean → `git checkout` back). **My own `verify` then caught two defects in the backup I
     had just pushed:** (a) the prek **prettier hook rewrote the baseline** at commit time, destroying the
     byte-exactness that is its entire point (live workflows are only formatted when STAGED, so several had never been
     through prettier while my copies went through immediately) → `.prettierignore` now exempts it, re-snapshotted,
     46/46 byte-identical; (b) `.gitignore`'s global `*.tsv` **silently swallowed MANIFEST.tsv**, the provenance record
     that makes the backup auditable → scoped negation. Neither was visible without running `verify` against the pushed
     result.
  2. **PRE-SEED EVERY MOVER DEP** — operator: _"if all the workflows will do setup-python then whats the use of long
     lived vm"_. Surveyed all 38 movers: `google-cloud-firestore` ×9 · `pyyaml` ×3 · `pydantic` ×1 · `uv` ×2 ·
     `claude-code` npm ×1 · `jq` ×1. New SSOT `slot-venv-requirements.txt` (every entry cites its consumers; versions
     pin the same RANGES the workflows asked for, so pre-installing changes **availability, not resolution**);
     `setup-glue-runners.sh` installs from it; `bootstrap-ci-host.sh` gains `install_repo_python` (Python 3.13 via uv —
     **not** deadsnakes: 3.13 is not in noble's apt and a PPA on the live orchestrator is not a trade worth making) and
     `install_claude_code`. The 3 flipped workflows with installs dropped them; **all 3 dispatched GREEN with zero
     installs**. Slot venv verified on the box: firestore 2.28.0 · pydantic 2.13.4 · PyYAML 6.0.3 · uv 0.11.29.
  - **Recorded as a hazard, not a win:** the slot venv is **SHARED, MUTABLE state** — all 8 runners resolve `python3` to
    it, so a job that `pip install`s mutates it for every other job. `readiness-verifier`'s `pip install uv` silently
    added uv 0.11.29 to it during a test dispatch. It _worked_, which is the problem: an accumulated dep is invisible,
    unversioned and unreviewable, and a conflicting version would break unrelated jobs with no trace.
  - **HONEST NUMBERS — an earlier entry overclaimed and is corrected here.** I wrote "93s → 64s (−31%)" from wall-clock;
    a later run took **83s**, and step-level timing shows the steps are only **~6-16s of a 64-93s run** (the rest is
    queue + job setup, which none of this touches). Real per-run saving: **`Set up Python` 7s + installs ~3s ≈ 10s of
    step time**. **Speed was never the point** — the real wins are correctness and posture: the tool-cache race class is
    eliminated at the root, ~400MB/runner of duplicate interpreters is gone, and no job mutates the shared host via
    `npm -g`/`apt`.
  - **Coupling now explicit in every touched workflow:** these are **self-hosted-ONLY**. Restoring
    `runs-on: ubuntu-latest` REQUIRES restoring the setup-python / install steps with it — `hosted-baseline/` is the
    exact source for that.
  - Evidence: baseline `hosted-baseline.sh verify` OK (56/56); dispatches `reconcile-release-tags` /
    `ci-status-consolidator` / `readiness-verifier` all `success` on `glue-*` with 0 install steps; pool 8/8 online.
  - **Two MORE of my own bugs, both caught by verifying the box against git rather than trusting my own deploy:** (a)
    **DEPLOY DRIFT — the box silently lost the JIT-409 self-heal.** I had base64-patched that fix straight into
    `/opt/github-glue-runners/` but NOT into the deploy clone, so the next `install` copied the clone's older wrapper
    back over it and reverted the fix. The box was one `systemctl restart` from the pool-death bug again. **Rule now:
    the deploy clone is a git clone — `git fetch && reset --hard` it, NEVER patch it.** base64-to-the-box creates a
    second source of truth and this is exactly how it bites. (b) **The self-heal's guard was too strict.** It refused to
    touch an ONLINE registration under our own name — but right after a restart that IS our SIGTERM'd predecessor
    (GitHub takes ~30-60s to mark a disconnected runner offline). It exit-3'd with _"Another process is serving as this
    runner"_, which is FALSE and would mislead whoever reads the journal at 3am. It self-recovered via `Restart=always`,
    but only after ~30-40s of the whole pool crash-looping every 5s. Now it WAITS (~90s bounded) for the ghost, then
    deletes; still fails loudly if the name is held past that, since then it is genuinely not a ghost. **Measured
    before/after: 0 units running at t+20s → 8/8 running, 8/8 ONLINE, all 5 glue `Listening for Jobs`.**
  - **A third, cosmetic:** the commit message for that fix contains backticked shell (`[ a ] || [ b ] && break`) passed
    inside a DOUBLE-QUOTED argument — bash executed it as command substitution and stripped it from the message
    ("Verified the in the wait loop"). Same class as the `die "... \`gh auth status\`"` trap hit earlier this session.
    Code unaffected; noted so the pattern is recognised the third time.
  - **✅ AUTONOMOUS REAL WORK CONFIRMED (operator asked "are they doing the ACTUAL work?" — fair, since every earlier
    proof was a MANUAL dispatch and 4 of them used `dry_run=true`, i.e. they proved the workflows RUN, not that they DO
    their job).** Checked the natural triggers on `main`: **4 of the 10 have since fired on their OWN cron** — a
    scheduled run has no `dry_run` input, so these are real. All 4 landed on `glue-*`, succeeded, **ZERO-BILLED**:
    `ci-status-consolidator` 16:39 · `reconcile-staging-versions` 16:56 · `staging-conflict-ldr-main-fallback` 17:10 ·
    `reconcile-release-tags` 17:27. **The definitive one:** `ci-status-consolidator` (run 29516479439,
    `glue-ip-172-31-5-118-1`) logged `DRY_RUN: false` and
    `CHANGED deployment-api.ci_status: SIT_VALIDATED -> MAIN_GREEN`, then **committed `208439f92` to main** ("ci:
    consolidate ci_status from Firestore", 1 file, +16/-16). `origin/main`'s manifest now reads
    `deployment-api.ci_status = MAIN_GREEN` — the change is real and it stuck. It has done this twice post-flip (15:42,
    16:39). So the full chain is proven end-to-end on the VM for $0: **cron → glue runner → GCP auth → Firestore read →
    manifest projection → commit+push to main.** **The remaining 6 are NOT yet proven on their natural trigger — they
    are simply not due:** `workspace-quickmerge-validation` + `digest-drift-sweep` (6-hourly, last fired BEFORE the
    flip) · `readiness-verifier` (daily 03:00) · `ruleset-drift-alert` (Mondays 06:00) · `cold-storage-cleanup` (Sundays
    02:00) · `conflict-resolution-agent` (`repository_dispatch` only — fires on a real merge conflict). Their mechanism
    is identical to the proven 4, and all 6 passed a manual dispatch; but **do not claim they are proven autonomously
    until their cron has actually fired** — re-check with:
    `gh run list --workflow=<wf>.yml --branch main --event schedule --limit 1`.
  - **STOP POINT (operator): no further workflows flipped. 10 of 38 remain the total.** Next = operator gate for the
    remaining 27.

- 2026-07-15 — Plan drafted from the live billing investigation (this session). Evidence: Enhanced-Billing ledger
  Jun/Jul 2026 + PM 1000-run/13.5h Actions run-mix sample. Status draft, human-only, suggestions-not-final. Awaiting
  operator ruling on § "Decisions needed".
- 2026-07-15 — **Superset options analysis added**:
  [`github_actions_cost_reduction_options_analysis_2026_07_15.md`](github_actions_cost_reduction_options_analysis_2026_07_15.md)
  (4 parallel investigations). This plan is the execution vehicle for the **self-host** path; the companion doc is the
  wider decision menu (self-host vs fold-into-deployment-api vs RunsOn; the no-infra GitHub-native fixes incl. two
  latent bugs; and why Cloud Build / monorepo / merge-queue were rejected). Baseline rate corrected to **$0.006/min**.
- 2026-07-15 — **Phase 1 STEP 1 cracked** (operator: B1 on the planning-VM). Authored the runner infra under
  `scripts/self-hosted-runners/` (setup/wrapper/systemd template+slice/classifier/runbook) — pinned runner v2.335.1 +
  sha256, JIT-ephemeral, repo-scoped to PM (all glue lives here), CPU-capped to protect the orchestrator, shellcheck
  clean. `classify-glue-workflows.sh` → 46 MOVE / 10 KEEP (refined 2026-07-15). Files pushed; deploy on the VM + the
  runs-on flip are the next steps, gated on operator go.
- 2026-07-16 (later) — **Operator closed the two open review threads.** (1) The 4 CI-health watchers stay HOSTED
  (`KEEP-M`) with `overnight-dead-man-switch` — failure-independence over a few $/mo; the failure-independence follow-up
  todo is RESOLVED. (2) `image-build-validate` stays HOSTED (`KEEP-R`) — moving it would need per-repo runner
  registrations (personal-account runners are repo-scoped; org migration is the only clean multi-repo path), not worth
  it for a promote-PR-only workflow. **Split → 40 MOVE / 16 KEEP**; canary switched to `reconcile-release-tags`.
  Classifier `KEEP_MONITORS` now carries all 5 monitors.
- 2026-07-16 — **Review pass (operator: "grill the plan properly").** Findings folded in: (1) **fleet-breaker** —
  `image-build-validate` was MOVE but is a cross-repo reusable called by 24 repos (flip hangs their promote gate) →
  reclassified **KEEP-R**; classifier now detects cross-repo reusables + a **KEEP-M** failure-independence class
  (`overnight-dead-man-switch`). **Split corrected 46/10 → 44/12**; added the explicit §"MOVE / STAY manifest". (2)
  Canary caveat: dispatch-only movers (`ci-status-update` etc.) can't be `gh workflow run`-canaried → added the
  workflow_dispatch/staged-main options to STEP 2. (3) A1/A2 correctness guards: the skip must still post the required
  `quality-gates-v2` check GREEN (not absent) or promote PRs block; A2's key must include the gate version. (4) Runner
  design finalized (operator): dedicated isolated slot/folder/venv, long-lived pool for the high-freq writer, no
  AO-clone reuse, no per-run checkout for ci-status-update. (5) Added the ambient-creds security codex todo + the
  4-watcher failure-independence follow-up. (6) A3 number corrected (~$78/mo, and $0/double-counted post-B1).
- 2026-07-15 — **Captured execution-critical context** (operator: don't lose it in compaction). Added a
  pre-flight/runbook §. Key catch: 4 MOVE workflows are FLEET TEMPLATES
  (`main-backmerge-to-ldr`/`semver-agent`/`major-bump-issue-handler`/`request-major-bump`) — flipping the template would
  hang the other ~24 repos (no runner there) and hand-editing per-repo copies is banned → they stay hosted (`KEEP-T`).
  Split corrected to **46 MOVE (PM-local direct) / 10 KEEP**; classifier now flags `KEEP-T`/`KEEP*`. Also recorded: SSM
  deploy channel + verified admin PAT, A1/A2/2b code locations, A2 Firestore fingerprint fields, and the billing re-pull
  command for VERIFY.
- 2026-07-16 (final review) — **`notify-slack` reclassified `KEEP-D` → split 39 MOVE / 17 KEEP (operator).** Caught the
  last straddle: every `KEEP-M` monitor's alert lands via the shared reusable `notify-slack`, and a reusable's `runs-on`
  is independent of its caller — so if `notify-slack` moved to the VM, a VM outage would let the hosted watchers DETECT
  a failure but be unable to PAGE. It stays hosted **for the watchers' sake, not the movers'** (a mover on a down VM
  isn't running, so its alert is moot; movers call the hosted carrier with no change — GitHub runs that one job on a
  hosted runner inside the self-hosted workflow). **Measured its cost first** (operator: "actual figures, no guesses"):
  billing has no per-workflow line and it's a nested reusable (0 own runs), so counted the alert ledger + billed
  `send-notification` jobs →
  **~$1/mo** (117 posts/30d + a small deduped-but-billed tail; `cloud-build-failure-watcher`
  ~51 billed is the bulk). Two earlier intermediate numbers ($4/$22)
  were artifacts of counting skipped `notify` jobs + API rate-limiting — corrected. Classifier now emits `KEEP-D`
  (curated `KEEP_HOSTED_DEPS`). `persist-cicd-event` left MOVE (secondary ledger, not the alert path) — flagged as the
  one open straddle.
- 2026-07-16 (final review) — **`persist-cicd-event` straddle RESOLVED → option C (operator): convert to a composite
  action.** Unlike `notify-slack`
  (~$1/mo, alert-only), `persist` fires on ~every run (called by 5 KEEP + 17 MOVE incl.
  the 13k/mo `ci-status-update`) so where it runs is real money (the A3/A4 dollars). A single reusable can't be
  hosted-for-KEEP and on-VM-for-movers, and flipping it would hang the hosted callers on a VM outage. Converting it to
  `.github/actions/persist-event` makes it run as steps **inside each caller's own job** → on the caller's runner
  (movers → VM/$0,
  KEEP → hosted, no hang) AND drops the separate billed job (the A3/A4 win). Classifier tags it **`MOVE-C`** (move by
  conversion, do NOT flip; still counted in the 39 → 38 flip + 1 convert). Added **STEP 2c** (convert + rewire 22
  callers + delete the old workflow), sequenced with the flip. Supersedes options-doc A3. `persist-cicd-event` was the
  last open straddle — none remain.
- 2026-07-16 — **PLAN ACTIVATED (operator: "make this plan active and start working on it").** `status: draft` →
  `active`; DRAFT/"suggestions" banner + tags withdrawn; title cleaned; summary corrected ($0.008 → **$0.006/min** and
  the final 39/17 shape). **Kept `assigned_vm: NA` + `execution_scope: local-only` deliberately** — this is
  operator-driven work executed interactively, NOT auto-dispatched to agent-orchestrator workers (fleet-wide CI changes
  must not be picked up by a background agent). Added a **▶ START HERE** section at the top: the first real task is the
  **runner-infra redesign** (dedicated slot/folder/venv + long-lived pool for the high-freq writer) because the authored
  `setup-glue-runners.sh`/`glue-runner-run.sh` still assume one JIT-ephemeral pool and do NOT match the decided design —
  redesign BEFORE deploying; then SSM-deploy → canary `reconcile-release-tags` → phased flip → STEP 2b/2c → Phase 2/3.
  State at activation: **nothing deployed, no `runs-on` flipped, no callers rewired.**
- 2026-07-16 — **Runner-infra redesign started (execution begins).** Read all four authored artefacts
  (`setup-glue-runners.sh`, `glue-runner-run.sh`, `github-glue-runner@.service`, `github-glue-runner.slice`) against the
  decided design and found **8 gaps**, 4 of which are correctness bugs that would each BREAK the long-lived pool — now
  captured as the "Two-pool mechanics" todo: (a) JIT is single-use **by construction**, so "long-lived JIT" is not a
  thing — the writer needs `config.sh --token` + a `run.sh` loop, a genuine fork in the wrapper; (b) runner labels match
  by **subset**, so a writer labelled `self-hosted,glue,writer` would still match `[self-hosted, glue]` and steal
  movers' jobs → pools must be **disjoint** (`glue-writer` WITHOUT `glue`), making `ci-status-update` the one MOVE
  workflow off the uniform flip recipe; (c) `glue-runner-run.sh:38`'s `_work` wipe is correct only for
  one-process-one-job → a long-lived runner never cleans (use `ACTIONS_RUNNER_HOOK_JOB_COMPLETED`); (d) `cmd_prune`
  deletes OFFLINE `glue-*`, but a long-lived writer is _legitimately_ offline across reboot → prune must scope to the
  ephemeral prefix. Plus: the slot's clone/venv don't exist yet, `RUNNER_COUNT` needs splitting, and the pre-staged
  clone needs a **refresher** (new todo — a pinned clone silently drifts from `main` and the writer would emit Firestore
  rows with stale logic).
- 2026-07-16 — **Isolation scope DECIDED (operator) — folder/venv/clone only, `User=ubuntu`, VM's existing
  creds/toolchain, no dedicated OS user/SA.** Operator challenged the isolation framing ("everything that needs total
  isolation is already GitHub-hosted — why do we need so much isolation?") and was **right**: the self-hosted-runner
  threat model is about public repos accepting fork PRs; here all repos are private, the MOVE set has **zero
  `pull_request` triggers** by construction, and **the AO already runs as `ubuntu` with the same ambient creds**, so
  glue-as-`ubuntu` barely moves the blast radius. Investigated and **withdrew** my own shared-`$HOME` objection:
  `deterministic-promotion-conflict-resolve` (L95) and `rules-alignment-agent` (L69) do run `git config --global`, but
  every clone (slot + root) carries a **local** identity that overrides it (verified: `harshkantariya [slot-1·laptop]` /
  `[root·laptop]`), so AO commit attribution is immune; a `HOME` redirect was considered and **REJECTED** — it would
  break `$HOME/.config/gcloud` ADC resolution to fix a non-problem. Decision drops the separate-user + ADC-provisioning
  work entirely.
- 2026-07-16 — **Toolchain parity identified as the REAL migration risk (not isolation)** — new todo. MOVE-set tool
  inventory: `gh` 181 · `jq` 111 · `python3` 105 · `uv` 32 · `aws` 22 · `gcloud` 16 · `pip` 15 · `npm` 1. **`docker` is
  a FALSE ALARM** — all 21 hits are a step _named_ `docker-build` (which only dispatches to Cloud Build) or the Artifact
  Registry hostname inside `gcloud artifacts docker images describe`; nothing invokes the daemon, which **independently
  confirms the classifier's heavy-detection** sent the real builders to KEEP. Real friction =
  **`actions/setup-python@v6` on 5 movers** (`cassette-drift-check`, `readiness-verifier`, `reconcile-release-tags`,
  `removed-symbols-workspace-sweep`, `ruleset-drift-alert`): hosted pre-seeds the tool cache, self-hosted
  downloads/builds a Python per job on a miss — won't break, but slow → pre-seed `RUNNER_TOOL_CACHE` at install. Verify
  `jq`/`npm` on the box at deploy.
- 2026-07-16 — **Runner redesign SHIPPED** — unified-trading-pm@c44ca1bd4
  (`feat(ci): redesign glue runners into two pools`). 8 files: `setup-glue-runners.sh` + `glue-runner-run.sh` +
  `github-glue-runner@.service` rewritten; new `job-cleanup.sh`, `refresh-slot-repo.sh`,
  `github-glue-slot-refresh.{service,timer}`; README rewritten. **Verified to the extent possible OFF the VM**:
  `bash -n` + `shellcheck -S warning` clean on all 5 scripts; the prune filter unit-tested against a fixture proving an
  OFFLINE `writer-*` **survives** while an OFFLINE `glue-*` is pruned (the bug that would have deregistered the writer
  pool on every reboot); pool/index fork tested incl. double-digit indices and the unknown-pool reject; embedded Python
  (status listing, prune filter, `json_get`) executed against fixtures; classifier re-run **unchanged at 39 MOVE / 17
  KEEP**; `quality-gates.sh --no-fix` EXIT=0 (the base-image digest-drift warning is pre-existing, warn-only, not ours).
  **NOT verified**: anything requiring the VM — no `install` has run, no runner has registered, `preflight` has never
  executed on the box. Two self-inflicted bugs were caught before commit and are worth remembering: backticks inside a
  `die` string would have **executed** `gh auth status` at expansion time, and the f-strings nested double quotes (a
  syntax error below Python 3.12).
- 2026-07-16 — **README was actively DANGEROUS and is rewritten** (same sha). The old copy told the reader to _"roll the
  `runs-on` change out via the template SSOT + `rollout-workflow-templates.sh`"_ — the exact instruction marked ⛔
  SUPERSEDED in the options doc, which would flip the 4 `KEEP-T` fleet templates and **hang the workflow in ~24 repos
  that have no glue runners**. It also recommended **`branch-health` as the canary** (now `KEEP-M` — must never be
  flipped) and cited the stale 50/6 counts. Now carries the direct-flip warning, the six KEEP classes, the
  `MOVE-C`-don't-flip rule, `reconcile-release-tags` as canary, the runners-live-before-`main` ordering rule, and the
  isolation-scope decision. Anyone following the old README would have broken the fleet.
- 2026-07-16 — **Queued jobs cost NOTHING — the operator's billing worry doesn't exist** (answering "if the VM is dead
  and jobs queue 24h, how does that affect the bill?"). GitHub bills **execution minutes on hosted runners**; queued is
  not executing, and a `runs-on: [self-hosted, glue]` job **cannot execute on billed hardware by definition**. So:
  $0
  queued · $0 running · $0 when GitHub kills it at the 24h mark. **A dead VM is the CHEAPEST possible state** — the
  bill goes DOWN during an outage. The 24h queue is therefore **purely a correctness/availability risk** (lost
  `ci_status` transitions → stale Firestore → blocked promotes via the `MAIN_GREEN` dep-on-main gate), and the savings
  survive an outage intact. **Confidence caveat (stated because the notify-slack figure was wrong twice this session):**
  this is DEDUCTION from the billing model, NOT a measurement — unmeasurable today (zero self-hosted runners ⇒ no
  historical data; the billing report has no per-workflow granularity). Verified there is **no hosted fallback** that
  could re-add cost: `ci-status-reconciler` is retired and absent from `.github/workflows/`. That cuts both ways — no
  hidden spend, but no safety net either. Only real spend in an outage: post-24h mass failures trip `ci-health` →
  `notify-slack` (both hosted) = cents, i.e. the alerting working as designed.
- 2026-07-16 — **Queue watchdog design DECIDED — fold into `ci-health`, do NOT build a standalone workflow.** Cost drove
  it: a standalone `*/5` watchdog = **~$52/mo** and `*/15` = **~$17/mo** (1-min minimum × runs) — a watchdog for a
  cost-reduction project that eats a THIRD of the saving is self-defeating. `ci-health` is already KEEP-M hosted (the
  right independence — it must not run on the box it watches), already crons **`*/15`** (exactly the operator's
  requested page cadence), and its `notify` job **already matrix-fans `alerts` through `notify-slack` with per-item
  `dedup_key` + `cooldown_min`** — the re-nag machinery the operator asked for EXISTS. So the change is a step in an
  already-billed job + an item from the **pure** `build_alerts()` → **~$0**. Detect on **queued >10 min** rather than "0
  runners online" so it also catches a **wedged** pool, with runner state in the message to separate "VM down" from
  "pool wedged". **`ci-health` must stay KEEP-M forever** — flipping it would make the watchdog queue behind the very
  outage it exists to report. NOT yet implemented (P0, blocks the flip).
- 2026-07-16 — **Bootstrap SHIPPED + container-proven** — unified-trading-pm@80f00684a. The container leg immediately
  justified itself by catching `sudo: command not found`: `bootstrap-ci-host.sh` calls `sudo -u ${RUNNER_USER}` but
  never installed sudo — invisible on planning-VM (cloud images ship it), fatal on a minimal image, and it would have
  bitten mid-incident when the failsafe is the only thing standing. `python3-venv` is the same class (present-but-not
  really: `command -v python3` passes while `python3 -m venv` fails). Both now explicit with provenance inline. **Honest
  scope: the container proves the tool-install class ONLY** — IMDS/instance-role, GCP ADC, **systemd (so
  `setup-glue-runners.sh install` remains untested end-to-end)**, and real runner registration are all structurally
  untestable this way and stay open.
- 2026-07-16 — **Queue-starvation watchdog SHIPPED** — unified-trading-pm@6901779de (PR #1086, auto-merge). Landed
  exactly where the design said and NOT as a standalone workflow: `detect_glue_starvation()` + `_glue_runner_counts()` +
  a `glue-runners-starved` item from the pure `build_alert_items()`, all inside `ci-health`'s already-billed `watch` job
  → **~$0** instead of ~$52/mo. The re-nag needed no new machinery — `RENAG_GLUE_STARVED_MIN = 15` rides the carrier's
  existing per-key `cooldown_min`, so the watcher stays stateless and the ledger paces the 15-min re-page.
  **Mutation-tested rather than merely green** (13 new tests + 181/181 watcher suite, QG EXIT=0): removing the
  glue-label guard fails `test_hosted_job_queued_does_not_page`, and ignoring job status fails
  `test_running_job_is_not_starved` — both guards are provably doing work. The label guard is the one that matters: a
  HOSTED job queueing on GitHub's own capacity is not our outage, and paging on it would train the operator to ignore
  the alarm that exists to say the VM died. **Two API-shape traps found while writing it** (recorded inline): the
  _runners_ API returns `labels` as OBJECTS `{id,name,type}` while the _jobs_ API returns plain STRINGS — mixing them up
  silently yields zero matches and an alarm that never fires. QG caught 3 real lint errors of mine (C420 dict
  comprehension, E501, N802) — fixed. **Still unproven against a live outage** (no runners exist yet) — the deploy is
  what proves it end-to-end.
- 2026-07-16 — **Token + VM claims PROBED before deploy — one was wrong, one was right.** ❌ **This plan named a DEAD
  secret**: it said the registration PAT was Secret Manager `github-token`, which probes **401** (classic `ghp_`,
  created 2025-11-24, expired/revoked) — following the deploy step as written would have failed on a 401. The real
  secret is **`GH_PAT`** (what `load-gh-token.sh:68` actually loads, and what `deployment-api`,
  `batch-live-reconciliation-service`, `client-reporting-api` and `alerting-service` all use): probed **201** on
  `POST …/actions/runners/registration-token` ⇒ has `Administration:write`; fine-grained `github_pat_`, **never
  expires** (so the pool can't die on a token expiry). `github-automation-token` also probes 201 and is a valid
  fallback, but is only referenced by docs + a SIT probe. The 2026-07-15 `generate-jitconfig` verification was genuine —
  only the recorded NAME was wrong. ✅ **VM claim was right**: `i-0c9b283b31d6b5ca7` = `agent-orchestrator-vm-1`, EIP
  13.113.200.22, **m8i.2xlarge (8 vCPU / 32 GiB)**, running — which also independently validates the slice sizing
  (`CPUQuota=400%` of 8 vCPU, `MemoryMax=8G` of 32 GiB). It is NOT `i-0dd9812a96cdda5dc` (the human-planning box) —
  worth stating because deploying to the wrong VM would put CI runners on the operator's interactive machine. All probes
  printed status codes and metadata only; no token value was ever echoed.
- 2026-07-16 — **PRE-DEPLOY BLOCKER found in my own script**: `cmd_install` hard-requires `GH_PAT` in the env and writes
  the literal token to `/etc/github-glue-runner.env`, which contradicts this plan's own stated preference for the
  Secret-Manager path (`GH_TOKEN_SECRET`) "so no PAT sits on disk". The runtime wrapper already resolves
  `GH_TOKEN_SECRET` via ADC — only `install` lacks the path. Fix before deploying.
- 2026-07-16 — **Deploy runbook D1…D6 authored + operator pacing fixed (1 → 10 → remainder).** The plan had the canary
  intent but none of the on-VM mechanics, so a fresh session would have had to re-derive them — and would have hit the
  dead-token and install blockers live. Now explicit and ordered: **D1** fix `cmd_install` to accept `GH_TOKEN_SECRET`
  (my blocker — it hard-requires `GH_PAT` and writes the token to disk, contradicting this plan's own preference) ·
  **D2** SSM `preflight` (**gate** — `jq`/`npm` on the box are still UNKNOWN and toolchain parity is the real migration
  risk; a miss gets fixed IN `bootstrap-ci-host.sh` and re-run, **never** hand-installed, or the failsafe starts lying)
  · **D3** scripts onto the VM (verify by sha; never touch an AO slot clone) · **D4** install both pools — **the
  first-ever end-to-end exercise of the systemd path**, which the container structurally could not test · **D5** prove 8
  units + both pools Online + disjoint labels, cross-checked from the GitHub API rather than trusting `status` alone ·
  **D6** canary. **D6's key property: it proves the self-hosted path WITHOUT touching `main`** — `workflow_dispatch`
  executes the definition from the CHOSEN ref, so flipping `reconcile-release-tags` on LDR and dispatching
  `--ref live-defi-rollout` exercises the runners while `main` still says `ubuntu-latest`; nothing scheduled changes
  behaviour until we promote deliberately. D6 also asserts the ephemeral runner **auto-deregisters** afterwards, proving
  the JIT lifecycle rather than merely a green job. Post-D6 pacing per operator: **canary (1) → verify → next 10 →
  verify → remaining ~27**, each batch gated on green + billed-$0 + the queue watchdog staying quiet. `ci-status-update`
  is flagged in STEP 2 as the ONE exception to the uniform recipe (`glue-writer`, not `glue`).
- 2026-07-16 — **Flip groups chosen from EVIDENCE, and the canary CHANGED (operator refinement).** Profiled all 38 MOVE
  workflows by LOC · `workflow_dispatch` · job count · capabilities (firestore/slack/persist/gcs/git-write/pr-write/
  dispatch/setup-python/app-token/gcp-auth/upload-artifact). **My original canary pick was WRONG**:
  `reconcile-release-tags` is only 72 LOC but exercises **firestore + pr-write + dispatch + setup-python + gcp-auth** —
  five capabilities incl. a PR write. It moves to COMPLEX (as the operator suggested). **New canary = `agent-audit`**:
  smallest of all 38 (50 LOC, 2 jobs), `workflow_dispatch`, **ZERO side-effecting capabilities** (pure gh/api glue),
  read-only by design (`audit_only`), blast radius ≈ nil. **Organising principle for the 10: cover every capability
  class the remaining 27 use**, so the tail carries no NEW risk — only volume. All 11 have `workflow_dispatch` ⇒ every
  one is provable on LDR before `main` changes. **The two CROSS-BOUNDARY tests are the batch's real payload**
  (`ruleset-drift-alert` → hosted `notify-slack`; `readiness-verifier` → hosted `persist-cicd-event`): a self-hosted
  caller invoking a HOSTED reusable is the biggest architectural risk in this design, and these validate the
  KEEP-D/MOVE-C reasoning **empirically instead of by argument** — if they fail, the remaining flips STOP. **Safety
  check done**: a dispatch RUNS the workflow for real, and the four destructive candidates all carry `dry_run` inputs —
  including `cold-storage-cleanup`, the ONLY workflow in the entire MOVE set that deletes from GCS. The remaining 27
  include **10 with NO `workflow_dispatch`** (`ci-status-update`, `sit-gate`, `cloud-build-router`, …) which are only
  validatable AFTER promote — so they go last, landing with the watchdog already live.
- 2026-07-16 — **Batch-2 validation: 9/10 flipped workflows PROVEN on the glue pool, all ZERO-BILLED — and my first
  measurement of that lied.** Operator asked to dispatch each flipped workflow rather than wait on crons. Turned out
  almost nothing needed dispatching: the crons had already proven themselves. Evidence, per-JOB `runner_name` +
  `/timing.billable`: `ci-status-consolidator` (schedule 17:38, glue-1) · `reconcile-staging-versions` (schedule 17:56,
  glue-3) · `reconcile-release-tags` (schedule 18:20, glue-1) · `staging-conflict-ldr-main-fallback` (schedule 18:08,
  glue-1) · `digest-drift-sweep` (schedule 18:23, glue-1) · `workspace-quickmerge-validation` (dispatch 14:03, glue-4) ·
  `ruleset-drift-alert` (dispatch 15:36, glue-4) · `readiness-verifier` (dispatch 16:06, glue-5) ·
  `cold-storage-cleanup` (dispatch 15:03, glue-4). Every one reports `billable: {}` = **zero hosted minutes**. **The
  near-miss worth recording**: my first sweep printed a single `runner_name` column truncated to 26 chars, and the
  unique-list sorts `GitHub Actions …` BEFORE `glue-…` (ASCII `G` < `g`), so every cross-boundary run — the ones with a
  glue job AND a hosted reusable job — got cut off exactly at the comma and rendered as **purely hosted**. I was ~1
  minute from reporting "5 workflows silently failed to move". Same class as the earlier `venv --help` / `bash -lc`
  verifier lies: **the tool answered a different question than the one I asked**. Per-JOB output is now the only
  acceptable evidence shape here — a run-level runner name is meaningless for a cross-boundary workflow BY DESIGN. **The
  two cross-boundary tests re-confirmed on real runs**: `readiness-verifier` = `verify-readiness` on glue-5 +
  `send-notification` AND `persist-event` on hosted — i.e. KEEP-D/MOVE-C behaving exactly as designed, hosted jobs being
  correct rather than a regression.
- 2026-07-16 — **10th workflow (`conflict-resolution-agent`) NOT proven — a zero-side-effect test was designed, then
  BLOCKED on permissions; needs operator approval.** It is the only flipped workflow whose success path has a real,
  expensive side effect: `escalate` → `agent-runner.yml` → `repository_dispatch escalate-to-orchestrator` → a REAL
  **Opus** worker on a fabricated conflict. Only its `resolve-and-escalate` job is on glue; `agent-runner.yml` is
  `runs-on: ubuntu-latest` (a KEEP reusable), so proving the flip only requires that job to START. Designed test:
  dispatch **`--ref live-defi-rollout`** with **empty inputs** → the glue job starts, dies at its own
  `: "${REPO_NAME:?}"` guard (conflict-resolution-agent.yml:65), `escalate` is skipped by `needs` (no `if:`, defaults to
  `success()`) ⇒ **no worker spawned**; and LDR is chosen because `ci_failure_watcher.py:123` is
  `WATCHED_BRANCHES = ["main","staging"]` ⇒ the deliberate red X **cannot page #ci-failures**. main==LDR is
  byte-identical for `.github/workflows/`, so the LDR ref runs the same flipped definition. Rejected alternative:
  tripping `agent-runner.yml`'s idempotency gate needs a REAL PR labelled `escalation-dispatched` — which would then
  silently suppress a genuine future escalation. **Blocked by the Bash permission classifier; left for the operator to
  approve rather than worked around.**
- 2026-07-16 — **FINDING (P1, unrelated to this plan, cross-repo): `digest-drift-sweep` has been a SILENT NO-OP since
  birth.** Reading its log to confirm a re-dispatch was safe (the fan-out to 16 repos was the risk) showed
  `Dispatched: 0 / Already fresh: 0 / No ARG found: 16` on EVERY run back through Jul 14 — `Already fresh: 0` being the
  tell. Root cause: `secrets.GITHUB_TOKEN` (:77) is scoped to PM only, so cross-repo `contents/Dockerfile` 404s;
  `curl -sf … || echo ""` (:128-131) swallows it and the empty result is misreported as the benign _"Dockerfile not
  found — may not be image-building"_ (:138-142). **Verified, not inferred**: the exact curl returns HTTP 200 + a valid
  pin with a PAT, HTTP 404 without scope; all 16 repos DO carry `ARG BASE_IMAGE_DIGEST` and ALL are stale vs UTL
  `:latest sha256:5122f7ab…`. Born broken in `0d5663d4d` (2026-06-19); `git log -S` proves it was never `GH_PAT` ⇒ ~27
  days × 4/day ≈ **110 green runs that did nothing**. NOT caused by the flip (`23ce709cc` touched only `runs-on:`).
  **Not fixed here — it is a fleet event, not a one-liner**: every repo being stale means the first correct sweep fans
  `dependency-update` to all 16 at once, `GH_PAT` is pending rotation, and the dispatch POST (:160-176) has the same
  defect. Issue doc: `plans/active/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md`. **Side
  benefit for this plan: the no-op is precisely why re-dispatching it was provably safe** — it cannot dispatch anything.
- 2026-07-17 — **OVERNIGHT VALIDATION: the flip is working. 47 runs, 100% on the glue pool, 0 failures, real work
  proven.** Window 2026-07-16T18:30Z → 2026-07-17T04:49Z, per-JOB evidence: `reconcile-release-tags` 16 ·
  `ci-status- consolidator` 9 · `reconcile-staging-versions` 9 · `staging-conflict-ldr-main-fallback` 9 ·
  `workspace-quickmerge- validation` 2 · `digest-drift-sweep` 1 · `readiness-verifier` 1. Every glue job `billable: {}`
  = **zero hosted minutes**. **`readiness-verifier` fired its own 03:00 daily cron** (previously only ever manually
  dispatched) ⇒ the autonomous path is proven for it too. **Cron delivery measured at ~80-90%**, NOT the ~37% in
  CLAUDE.md's throttle note (hourly crons landed 9/10; `*/30` landed 16/20) — worth re-checking that figure before any
  cooldown is tuned to it. **REAL WORK confirmed, not just green**: `ci-status-consolidator` logged `DRY_RUN: false` →
  `CHANGED deployment-ui.ci_status: SIT_VALIDATED -> FEATURE_GREEN` → `wrote 1 change(s) to workspace-manifest.json`,
  and its log confirms the pre-seeding works: _"No pip install: google-cloud-firestore is pre-seeded in the runner's
  slot venv"_.
- 2026-07-17 — **HONEST CORRECTION: `readiness-verifier` is NOT zero-billed, and yesterday's "every one is" was too
  broad.** Its own `verify-readiness` job IS on glue-3, but `send-notification` + `persist-event` remain HOSTED **by
  design** (KEEP-D / MOVE-C) ⇒ `billable: {"UBUNTU": {jobs: 2, total_ms: 0}}`. **`total_ms: 0` is a trap**: the timing
  API under-reports, but GitHub bills a **1-minute minimum PER JOB**, so those 2 jobs cost ~2 billed minutes despite the
  API's zero. This is exactly why `scripts/cicd/measure-billed-notify-cost.sh` counts JOBS, not ms — do NOT re-measure
  this epic's savings off `/timing.total_ms`. Correct claim: **the moved job bills zero; a KEEP-D/MOVE-C reusable still
  bills 1 min/job** until STEP 2c / A3-A5 land. `readiness-verifier` went 3 hosted jobs → 2.
- 2026-07-17 — **Two measurement bugs of my own, same class as the ones this epic keeps finding.** (1)
  `gh api --paginate --jq '[...]'` emits **one array PER PAGE**, so `jq length` counted only the first ⇒ I
  under-reported 5 runs as 3. (2) `gh api` has **no `--arg` flag**; passing one made every query error out, and my
  blanket `2>/dev/null` swallowed the error and rendered it as a clean `0 run(s) overnight` — **the literal
  `curl -sf || echo ""` bug I wrote the digest-drift-sweep issue doc about, committed by me, one day later.** Rule for
  this epic's evidence: never `2>/dev/null` a measurement command, and never report a count without an independent
  cross-check.
- 2026-07-17 — **FINDING #2 (P1, SSOT contradiction, pre-existing): `reconcile-release-tags` has created ZERO tags since
  the D13 migration.** `created 0 tag(s); 24 repo(s) had no main version` on **20/20 last runs, byte-identical**. Cause
  is dated: `f4a3865e` (2026-06-27) _"migrate to version_source=git-tag (Phase-2/D13 fleet rollout)"_ removed the static
  `version = "X.Y.Z"` from pyproject.toml in favour of `dynamic = ["version"]` + hatch-vcs — but `_main_version()`
  (reconcile_release_tags.py:73-93) still regex-matches that deleted field. **Not a regex bug — a circularity**: D13
  made the TAG authoritative and the version DERIVED; the reconciler reads the derived value to create the tag. Verified
  fleet-wide (6/6 sampled repos `dynamic=1 hatch.version=1 static_version=0`). **Auth is NOT the cause here** — it
  correctly uses `secrets.GH_PAT` and the fetch returns 200, so it is NOT the digest-drift-sweep bug despite looking
  identical from outside. Impact bounded: the PRIMARY path (`update-repo-version.yml`) still tags correctly (manifest
  `execution-service=0.38.1`, tag `v0.38.1` present) — what is gone is the RECOVERY net that the 2026-06-09/06-11
  incidents motivated. Fix is a source swap, not a redesign: the manifest's `versions` map is authoritative and
  `_manifest_repos` (:154) already reads that file. Issue doc:
  `plans/active/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md`.
- 2026-07-17 — **PATTERN (the real lesson of this epic so far): 2 of the 10 audited workflows were long-dead silent
  no-ops, and BOTH are BACKSTOPS.** `digest-drift-sweep` (digest-drift net, dead since birth 2026-06-19) and
  `reconcile-release-tags` (missed-tag net, dead since 2026-06-27). Neither was caused by the flip — the flip is simply
  the first time anyone READ their logs. The shared shape: **a safety net's healthy output and its dead output are the
  same string** (`Dispatched: 0` / `created 0 tag(s)`), so nothing but a human going looking will ever notice. Both want
  the same remedy: assert that "I did nothing" and "I could not look" are DIFFERENT states (if every repo lands in the
  fallback bucket, exit non-zero). This generalises `codex/02-data/honest-absence-downstream-handling.md` from data to
  automation and is worth a codex note. **Cost angle for this plan: the cheapest workflow is one that does not run** —
  `reconcile-release-tags` alone burns ~48 no-op runs/day; auditing WHAT the glue workflows do (not just where they run)
  is a second, larger saving than moving them.
- 2026-07-17 — **STEP 2 COMPLETE: batch 3 shipped, 36/37 flippable now on the pool** (unified-trading-pm@513f16773; 26
  workflows / 38 `runs-on` lines). Final: **35 `[self-hosted, glue]` + 1 `[self-hosted, Linux, X64, glue-writer]`**.
  Verified by a live run on the LDR ref BEFORE `main` inherited it — `secret-health-check` 29556783346 `check-secrets` →
  **glue-1 success**, its Slack job **SKIPPED** (dedup working ⇒ unbilled), `persist-event` hosted per MOVE-C. **Timing
  subtlety worth keeping**: `schedule`/`repository_dispatch` fire ONLY from the DEFAULT branch, so none of the batch-3
  movers exercise glue until the promote lands — `workflow_dispatch --ref live-defi-rollout` is the only pre-promote
  proof, which is exactly why the plan required all-dispatchable batches earlier. The 10 non-dispatchable ones
  (`ci-status-update`, `sit-gate`, `cloud-build-router`, …) are provable only post-promote; the watchdog is live for
  that window.
- 2026-07-17 — **FINDING #3 (P1, pre-existing + a flip TRAP): `cassette-drift-check` — DELIBERATELY NOT FLIPPED (1 of
  37).** Two independent defects. (a) It runs `python unified-trading-pm/scripts/dev/detect_cassette_drift.py`, but that
  file was DELETED from PM by `c2e58f200` ("relocate mock infrastructure scripts to UIC/UAC packages", -293 lines) and
  now lives at `unified-api-contracts/unified_api_contracts/testing/`. python fails every run, but
  `|| { echo drift_detected=true; }` makes the STEP exit 0 ⇒ **job GREEN**; absent on both main and LDR; last 3 runs all
  `success`. So the nightly check has not checked anything since the relocation — and it renders the error as a POSITIVE
  detection (`drift_detected=true` is what the create-issue step keys on), which is worse than silence. (b) **The stale
  `python-version: "3.12"` pin is load-bearing BY ACCIDENT**: UAC needs `>=3.13`, so `uv pip install -e . --system` has
  ALWAYS failed into the `|| uv pip install pydantic pyyaml` fallback (proven in the 03:10 log). On glue, python3 IS the
  **shared slot venv on 3.13**, so `-e . --system` would **SUCCEED** and install an EDITABLE UAC into shared state
  pointing at a `_work` dir the JIT runner DELETES — poisoning every later job on that runner. **Flipping it would
  ACTIVATE a bug the breakage was masking.** Fix = repoint + isolate the venv + stop swallowing the exit code, together.
  Issue doc: `plans/active/issues/cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md`.
- 2026-07-17 — **INDEPENDENT CONFIRMATION of the digest-drift-sweep finding, from a detector I did not write.** The
  batch-3 `quality-gates.sh` run emitted: _"Fleet digest INCONSISTENT — 5 distinct pins across 16 repos (missed fan-out
  from update-dependency-version.yml?)"_ + 15 stale repos + _"fleet pin … is BEHIND :latest"_. That is precisely the
  drift the dead sweep exists to prevent, measured by PM's own `check_base_image_digest_drift`. **The signal was there
  all along — it is `warn-only, non-blocking`**, so it scrolled past every QG run for ~27 days. Two independent
  detectors agreeing raises confidence the sweep fix is worth sequencing; it also suggests the QG warn should become an
  assertion once the sweep works (otherwise we keep a detector nobody acts on).
- 2026-07-17 — **Running tally of the audit's real yield: 3 of 37 movers were already broken, all "green", none caused
  by the flip** — `digest-drift-sweep` (dead since birth 2026-06-19, token scope), `reconcile-release-tags` (dead since
  2026-06-27, D13 SSOT contradiction), `cassette-drift-check` (dead since the script relocation, swallowed exit code).
  **~8% of the audited surface was decorative.** The flip's real value is turning out to be that it forced someone to
  read 37 workflow logs for the first time. Recommend a STEP 2d: assert-not-decorative on the remaining movers (if a
  workflow's "did work" counter is 0 on EVERY run for N days, page) — cheaper than the flip and finds more.
