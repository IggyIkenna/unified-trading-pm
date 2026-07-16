---
doc_type: plan
title:
  GitHub Actions CI/CD cost reduction — self-host the glue, kill the minute-minimum tax, fix cron cadence (DRAFT /
  suggestions)
summary: >-
  PM is ~48% of a ~$1,000/mo GitHub Actions bill despite a code freeze because it is the fleet CI/CD control tower —
  ~79% of its runs are automation (status routing, deploy dispatch, promotion/health crons), only ~8% are doc commits.
  All repos are private (every minute billed) and there are ZERO self-hosted runners, so the biggest untapped lever is
  moving lightweight glue off $0.008/min GitHub-hosted runners onto compute we already run 24/7. This plan proposes a
  tiered fix — self-host the switchboard+crons, collapse the quality-gates job fan-out that pays a 1-min minimum per
  sub-second job, and fix cron cadence. Decisions closed 2026-07-15 (B1 on the planning-VM; ci-status-update trimmed to
  use the VM's warm state; serverless B2 dropped; promote bots kept). Execution in progress.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, github-actions, cost, self-hosted-runner, workflows, spend-reduction, draft, suggestions]
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

# GitHub Actions CI/CD cost reduction — proposal (DRAFT)

> **⚠️ THESE ARE SUGGESTIONS, NOT FINAL DECISIONS.** This plan is `status: draft` and **human-only** (`assigned_vm: NA`,
> `execution_scope: local-only`) — it will **not** be ingested or dispatched to any agent. It exists to lay out the
> options and evidence so the operator can decide **which, if any,** of these changes to make and in what order. No
> workflow, runner, or infra change below is approved to execute. Flip individual items to real todos (and the plan to
> `active`) only after an explicit operator ruling on the open questions in § "Decisions needed".

---

## Execution pre-flight & runbook (READ FIRST — context not obvious from the todos)

**State 2026-07-15:** decisions closed; runner infra authored + pushed (`scripts/self-hosted-runners/`); **NOTHING
deployed, no `runs-on` flipped.** Work continues from **slot 1** (`.tabs/1/`), root left to the AO worker.

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

- The planning-VM `i-0c9b283b31d6b5ca7` has **no inbound SSH/:8765** → drive it via **AWS SSM**
  (`aws ssm send-command --region ap-northeast-1 --instance-ids i-0c9b283b31d6b5ca7 …`), the same channel as
  `/check-agent-orchestrator`. Then `bash scripts/self-hosted-runners/setup-glue-runners.sh install`.
- Registration token = an **admin PAT with `Administration:write` on unified-trading-pm**. The fleet `GH_PAT` (loaded by
  `load-gh-token.sh`; Secret Manager `github-token`) was **verified** to register runners (JIT `generate-jitconfig`
  returned ok=true 2026-07-15). Prefer the Secret-Manager path (`GH_TOKEN_SECRET`) so no PAT sits on disk.
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
- [ ] [INFRA] P1. **STEP 2 — flip `runs-on`** on the **38 flip-MOVE (PM-local direct) workflows only** (`ubuntu-latest`
      → `[self-hosted, glue]`), editing PM's `.github/workflows/*.yml` **directly** (these are NOT templated — do NOT
      touch `scripts/workflow-templates/`; the `KEEP-T`/`KEEP-R`/`KEEP-M`/`KEEP-D` set stays hosted;
      **`persist-cicd-event` is `MOVE-C` — converted in STEP 2c, NOT flipped**). **Pace = canary → phased groups
      (operator 2026-07-15):** flip ONE low-risk MOVE workflow first (`reconcile-release-tags` — has
      `workflow_dispatch`), confirm a green self-hosted run, then roll the remaining ~37 out in **small batches** (not
      all at once). (Takes effect on push — do NOT push until the runners are live on the VM, else those workflows queue
      with no runner.)
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
- [ ] [INFRA] P1. **Runner-slot ISOLATION + design (operator 2026-07-16 — resolves the review's #9/#10/#11).** The glue
      runners live in a **totally separate slot: their own folder, their own environment/venv**, fully isolated from the
      AO and its worker slots (no shared clone). So: the "warm checkout" is a **dedicated runner-owned clone**, NEVER an
      AO slot clone (removes the live-worker race the review flagged); the pre-installed `google-cloud-firestore` (STEP
      2b) lives in **that slot's dedicated venv**, not any AO/system Python. **Runner mode: use a LONG-LIVED
      (non-ephemeral) pool for the high-frequency writer** (`ci-status-update`) with per-job `_work` cleanup — at ~2-5s
      runtime the JIT re-registration overhead (generate-jitconfig + config + connect, several seconds) would otherwise
      dominate and cap burst throughput; keep JIT-ephemeral for the low-frequency movers where clean-state-per-job is
      cheap. Update `setup-glue-runners.sh` / `glue-runner-run.sh` to the dedicated-slot + long-lived-writer design
      before deploy (currently they assume a single JIT-ephemeral pool).
- [ ] [VERIFY] P1. After 3–5 days, re-measure PM's billed minutes (ledger); confirm the moved workflows bill ~$0 and the
      VM absorbed the load without contention (slice `MemoryCurrent` < 8G, orchestrator load unaffected).
- [ ] [DOCS] P2. **Codex: write down the self-hosted-glue security posture (operator 2026-07-16 — important, not
      blocking).** On self-hosted runners the runner user carries the VM's **ambient cloud identity** (ADC + AWS-WIF) —
      STEP 2b drops the per-job `auth` step _precisely because_ of this — so every glue job runs with the runner slot's
      cloud creds, a wider blast radius than GitHub-hosted's scoped short-lived tokens. Mitigation posture to record: a
      **dedicated low-privilege runner user + scoped service account** (separate from the orchestrator SA), the runner
      in its own isolated slot (already decided); and **if the exposure ever becomes a real concern, move the runners to
      a dedicated VM** (operator's stated fallback). Update `codex/05-infrastructure/` (runner conventions) +
      `codex/07-security/`. Reduced severity given the slot-isolation; documented so the posture is explicit.
- [x] ✅ [OPERATOR-DECISION] P2. **Failure-independence RESOLVED (operator 2026-07-16 — the review's #2).** The 4
      CI-health watchers (`ci-health`, `cloud-build-failure-watcher`, `ldr-ci-monitor`, `branch-health`) **STAY HOSTED**
      (`KEEP-M`) alongside `overnight-dead-man-switch` — GitHub-hosted is the right home for light monitors whose value
      is independence from our infra. They cost a few
      $/mo total; keeping them hosted means a VM/pool outage never
      blinds the fleet's failure detection + auto-recovery. (No runner-offline page needed — the watchers ARE the
      independent signal.) **Corollary (final review):** the watchers' shared alert carrier `notify-slack` must ALSO stay
      hosted (`KEEP-D`) or they'd detect-but-not-page during a VM outage — measured cost ~$1/mo.
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
  **~$1/mo** (117 posts/30d + a small deduped-but-billed tail; `cloud-build-failure-watcher` ~51 billed is the
  bulk). Two earlier intermediate numbers ($4/$22)
  were artifacts of counting skipped `notify` jobs + API rate-limiting — corrected. Classifier now emits `KEEP-D`
  (curated `KEEP_HOSTED_DEPS`). `persist-cicd-event` left MOVE (secondary ledger, not the alert path) — flagged as the
  one open straddle.
- 2026-07-16 (final review) — **`persist-cicd-event` straddle RESOLVED → option C (operator): convert to a composite
  action.** Unlike `notify-slack`
  (~$1/mo, alert-only), `persist` fires on ~every run (called by 5 KEEP + 17 MOVE incl.
  the 13k/mo `ci-status-update`) so where it runs is real money (the A3/A4 dollars). A single reusable can't be
  hosted-for-KEEP and on-VM-for-movers, and flipping it would hang the hosted callers on a VM outage. Converting it to
  `.github/actions/persist-event` makes it run as steps **inside each caller's own job** → on the caller's runner (movers
  → VM/$0,
  KEEP → hosted, no hang) AND drops the separate billed job (the A3/A4 win). Classifier tags it **`MOVE-C`** (move by
  conversion, do NOT flip; still counted in the 39 → 38 flip + 1 convert). Added **STEP 2c** (convert + rewire 22
  callers + delete the old workflow), sequenced with the flip. Supersedes options-doc A3. `persist-cicd-event` was the
  last open straddle — none remain.
