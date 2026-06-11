---
title: "CI/CD pipeline self-healing gaps — semver-agent trigger starvation, LDR-rewind data loss, orchestrator stale-PR escalation"
created: 2026-06-11
locked_by: live-defi-rollout
priority: P1
status: active
source:
  - 2026-06-11 CI-board firefight (triage queue 4→14 conflict walls)
---

# CI/CD pipeline self-healing gaps (2026-06-11)

Three distinct systemic gaps surfaced during the 2026-06-11 CI-board firefight. Each needs a careful, fleet-validated
fix (deliberately NOT shipped blind during the firefight — see rule 11). All three have a precise root cause + fix below.
The acute board symptoms (14-item triage queue, instruments phantom, MTDS red main) were resolved manually; these are
the underlying causes so it does not recur.

## Gap 1 — semver-agent trigger starvation → staging→main drain stops fleet-wide (P1)

**Symptom**: `staging_commits{}` empty fleet-wide → `staging-to-main.yml` skips ("nothing to promote") → ~10 repos had
content stuck on staging never reaching main.

**Root cause**: The LDR-trunk decoupling (`ldr_trunk_promotion_decoupling_2026_06_10.md`, the `A3 drop push:[staging] QG`
change) removed `staging` from `python-quality-gates-v2.yml`'s `push:` triggers. But `semver-agent.yml` still triggers
ONLY on `on: workflow_run: workflows:["quality-gates-v2"], types:[completed], branches:[staging]` — which needs a v2 run
with `head_branch == staging`. The LDR→staging Tier-C drain PR's v2 has `head_branch=live-defi-rollout` (the PR head), so
the `branches:[staging]` filter never matches → **semver-agent has not fired since ~2026-06-10 23:40 fleet-wide** → it
never dispatches `version-bump` → PM `update-repo-version.yml` never writes `staging_commits` → `staging-to-main.yml`
skips. (It DOES still fire off an existing staging→main PR's v2 re-run, which is why a manual staging→main merge bumps
the version — observed: instruments 0.3.0→0.4.0.)

**Fix (the intended draining signal already exists)**: make semver-agent fire off the **LDR→staging drain PR's v2
completion**. Minimal change in `scripts/workflow-templates/semver-agent.yml.tmpl` trigger (~line 37-40):
```yaml
  workflow_run:
    workflows: ["quality-gates-v2"]
    types: [completed]
    branches: [staging, live-defi-rollout]   # add live-defi-rollout
```
plus a guard step: proceed only when the triggering run is the LDR→staging promote PR (head=live-defi-rollout AND an
open/merged PR base=staging exists) OR head=staging; the template already scans the live `staging` tip (line ~104) so the
bumped SHA is the staging head, not the LDR head. The bump-rate circuit breaker (≥3/hr) already guards a loop.

**Blast radius (rule 11)**: fleet template → all ~24 repos. Roll via `rollout-workflow-templates.sh --template
semver-agent.yml` + commit/push each per-repo copy to LDR + promote to main (workflow triggers fire only from the default
branch). **Canary** on market-tick-data-service: confirm its semver-agent fires off the next LDR→staging drain PR's v2,
writes `staging_commits[market-tick-data-service]`, staging→main opens. Then fan out. **Interim manual unblock** (no
code): `gh workflow run quality-gates-v2.yml --repo <r> --ref staging` per stuck repo fires the staging-head v2 → semver
bumps → drains.

- [ ] [WORKFLOW] P1. Fix `semver-agent.yml.tmpl` trigger per above; canary on market-tick-data-service; roll out
  fleet-wide + promote to main. Verify a real LDR→staging drain fires semver + writes staging_commits.

## Gap 2 — LDR-rewind dropped committed feat work fleet-wide (P1, data integrity)

**Symptom**: features-service / unified-trading-api / agent-orchestrator / fund-administration-service had real committed
work on `staging` that was **absent from `live-defi-rollout`** (e.g. features-service's volatility/treasury/DXY feature
calculators, uta's seed.py refactor, AO's MainAgentKeeper). My safety guard caught this and aborted force-syncing them
(which would have re-dropped the work).

**Root cause**: NOT a quickmerge-to-staging bug (verified: per-repo `quickmerge.sh` are correctly symlinked to PM SSOT,
target LDR; the only `base=staging` PRs are Tier-C drains with `head=live-defi-rollout`). The dropped commits were ALL
merged to staging via `head=live-defi-rollout` Tier-C drains (e.g. features-service PR #123, base=staging, head=LDR,
merged 10:13Z) — i.e. **they WERE on LDR at drain time**. A **clean-start force-sync that rewound `live-defi-rollout` to a
slightly-stale snapshot after ~10:13** dropped those recent commits from LDR while staging retained them. The
`staging-backmerge-to-ldr` safety-net did not recover them.

**Recovery done**: back-merged `staging → LDR` for each affected repo (recovered the dropped commits to LDR, QG-green),
then their drain PRs cleared. **Residual risk**: repos that lost LDR commits which were NOT yet drained to staging are
silently gone (recoverable only from `origin/wip-preserve/*` or reflog) — not detectable by the staging>LDR guard.

- [ ] [SCRIPT] P1. Add a guard to the clean-start force-sync (`sync-all-to-main.sh` / the force-sync procedure):
  **before force-rewinding LDR, assert the target snapshot is an ancestor-or-equal of every branch that drained FROM it
  (staging)** — abort + alert if the rewind would drop commits that already reached staging. Composes with
  `codex/08-workflows/ci-cd-flow.md` § "LDR is the SSOT — back-merge DOWN first".
- [ ] [SCRIPT] P2. One-off: diff `origin/wip-preserve/*` + reflog vs current LDR per repo to detect any silently-dropped
  commit NOT on staging; recover or confirm none.

## Gap 3 — orchestrator does not auto-resolve stuck/conflicting promote PRs (P1, operator-raised 2026-06-11)

**Operator ask**: "agent-orchestrator should be picking up these stale PRs via escalation — if they don't have a
`Quickmerge:` trailer in the push, the orchestrator should spawn a worker in a slot, run quality gates + resolve the
commits, and if happy quickmerge so they go through and delete the stale PR. A merge conflict / auto-merge-didn't-work
case should be figured out and fixed automatically."

**Current state**: `ci-failure-watcher.py --auto-recover` only close+reopens the narrow `BLOCKED + no failed check + v2
absent` mechanical deadlock. `--escalate` is meant to spawn a worker for a genuine CONFLICTING/DIRTY wall, but in
practice "yields no worker spawned" when the orchestrator is headroom-less (per CLAUDE.md). So a fleet event that creates
~13 conflict-wall drain PRs at once (template rollout leaving staging behind + an LDR rewind) is NOT auto-handled — it
required a manual firefight.

**Recommended fix**: the escalation path must reliably (a) spawn a worker even under load (queue + AutoSpawn, not a
no-op), (b) the worker runs the deterministic recovery this firefight used: classify the conflict (drain-noise/template/
version → force-sync staging=LDR; real staging content LDR lacks → back-merge staging→LDR; staging→main → promote
clean-FF), run QG, quickmerge, then **close the now-empty drain PR**. Encode the classifier + recovery as a worker
runbook the orchestrator dispatches on a conflict-wall alert.

- [ ] [ORCHESTRATOR] P1. agent-orchestrator: make `--escalate` actually spawn a worker for conflict-wall promote PRs
  (queue if headroom-less) + give the worker the deterministic staging/LDR/main reconciliation runbook (this firefight's
  recipe) + auto-close emptied drain PRs. Target repo: `agent-orchestrator` (server escalation path + a worker runbook).

## Gap 3b — Tier-C drains are BORN in the v2-never-reported deadlock + auto-recover lags ~hourly (P1)

**Symptom (recurring)**: a fresh wave of "Auto-merge stuck → staging" Tier-C drain PRs (e.g. 2026-06-11 ~19:24:
alerting#81, BLRS#73, deployment-api#66, deployment-service#67, instruments#439, strategy#172) — all `MERGEABLE/BLOCKED`,
`v2 absent`, no failed check (the exact v2-never-reported signature), all `staging⊆LDR` (clean FF). They pile up every
time LDR gets new content.

**Root cause**: (1) The `ldr-to-staging-promote` (Tier-C) bot creates the drain PR with a token whose
`pull_request`/`push` event is **suppressed by GitHub's own-token loop-prevention**, so `quality-gates-v2` never fires on
the new PR head → required check missing → BLOCKED-from-birth (auto-merge can never complete). (2) `ci-failure-watcher
--auto-recover` is the designed self-heal (workflow_dispatch-re-fire v2, since close+reopen is equally token-suppressed),
but its `schedule: */15` is **throttled by GitHub to an effective ~70–90 min cadence** (observed: runs at 18:59 / 17:52 /
16:38 / 15:11 — not every 15 min), so a wave of stuck drains stays visibly parked for up to ~1.5h before recovery.

**Fix (durable — stops the recurrence at the source)**:
- [ ] [WORKFLOW] P1. `ldr-to-staging-promote` (Tier-C): after creating the drain PR, **explicitly
  `gh workflow run quality-gates-v2.yml --ref <pr-head-sha>`** (or create the PR with `GH_PAT` so the `pull_request`
  event fires) — so the drain PR is never born-deadlocked and auto-merge completes immediately. Verify a fresh drain
  reports v2 within minutes + auto-merges with no manual touch.
- [ ] [WORKFLOW] P2. ci-failure-watcher: don't rely on `schedule` cadence alone (GitHub throttles it) — add a
  `pull_request`-event-driven path (or shorten the practical detection window) so the v2-absent deadlock is recovered in
  minutes, not the next ~hourly tick.

## Gap 4 — deployment-ui should show "agent working / pending" for a repo under active recovery (P2, operator-raised 2026-06-11)

**Operator ask**: "the dashboard should show if an agent is working on it as pending — that's the repos in deployment-ui."
When a stuck/conflicting promote PR is actively being recovered (by the orchestrator's escalated worker per Gap 3), the
deployment-ui Repos-CI board should render that repo as **pending / being-worked**, not **stuck** — so the operator can
tell "an agent has this" apart from "genuinely parked, needs attention."

- [ ] [UI] P2. deployment-ui Repos-CI board: surface a `working`/`pending` state per repo (driven by the orchestrator's
  active-worker assignment for that repo's stuck PR) distinct from `stuck`. Composes with Gap 3 (the orchestrator must
  first own + assign the recovery). Playwright gate per CLAUDE.md (`pw:L2 ✓` + regression spec) before ticking.

## Gap 5 — image-build trigger + gate redesign (operator-decided 2026-06-11)

**Today (verified)**: image builds are **cloud-native** (GCP Cloud Build triggers + AWS CodeBuild webhook — NOT GitHub
Actions, so cheap + no GHA minutes). They fire on **`live-defi-rollout` push** and are **NOT a required check anywhere**
(every repo's `main` requires only `quality-gates-v2`). AWS CodeBuild webhook = single filter group `EVENT=PUSH,
HEAD_REF=^refs/heads/live-defi-rollout$`. GCP has 3 triggers per service (`…-live-defi-rollout`, `…-feature-build`,
`…-build`). The red "Build not triggered: PR approval required" on a staging drain PR is the LDR build's check surfacing
on the PR (head=LDR commit) — noise, not a staging build.

**Decided design**:
- **Build contexts**: feature-branch (dev deploy off a feature branch) + **LDR (OPT-IN, fast feedback)** + **main
  (ALWAYS, the deploy gate)**.
- **`quickmerge --build` flag**: the user decides per-ship whether they want the LDR image. quickmerge stamps a commit
  trailer (e.g. `Build-LDR: true`, alongside the existing `Quickmerge:` trailer). The v2 workflow's existing **"Dispatch
  cloud-build trigger"** step reads that trailer and conditionally dispatches the LDR build. No flag → no LDR build (save
  cost); the **main build always runs** regardless.
- **Gate**: the **staging→main and staging gates FAIL if the image build fails** — add the GCP Cloud Build + AWS
  CodeBuild check contexts to each deployed repo's `main` `required_status_checks` (and the build must run on the main
  commit — add a `PUSH ^refs/heads/main$` filter group to the AWS webhook in
  `terraform/modules/cloud-build/aws/main.tf`; confirm the GCP `…-build` trigger is on main).
- **Exclusions (no image build at all)**: **unified-trading-pm** (no Dockerfile, no build project — confirmed; not
  deployed), **e2e-testing** + **system-integration-tests** (test harnesses, no CodeBuild). UI repos
  (`deployment-ui`/`unified-trading-system-ui`) have Dockerfiles but build via **GCP only** (no AWS CodeBuild) — keep as
  is.

- [ ] [WORKFLOW] P2. quickmerge: add `--build` flag → `Build-LDR: true` commit trailer; v2 "Dispatch cloud-build
  trigger" step reads it → conditional LDR build dispatch. **(quickmerge flag SHIPPED 2026-06-11 — see Progress Log;
  v2-step path DROPPED as unworkable — v2 never runs on LDR. LDR opt-in is realized cloud-natively via the AWS
  CodeBuild webhook `COMMIT_MESSAGE` filter, NOT a GHA dispatch.)**
- [ ] [TERRAFORM] P2. AWS CodeBuild webhook: add `PUSH ^refs/heads/main$` filter group (keep LDR group). Confirm GCP
  `…-build` trigger targets `main`. `terraform/modules/cloud-build/aws/main.tf`. **(CORRECTED 2026-06-11: the live AWS
  webhooks + GCP triggers are IMPERATIVELY managed and DRIFTED from this terraform — a blind `terraform apply` would
  revert live config fleet-wide. GCP `…-build` already fires on `^main$` (green). The AWS-main filter group is BLOCKED
  on the failing AWS build, see new todo below.)**
- [ ] [PROTECTION] P2. **BLOCKED-DESIGN — do NOT flip naïvely (would deadlock the fleet).** Empirically (2026-06-11):
  NO image build runs on the staging→main PR head — GCP `…-build` fires on `push:^main$` (POST-merge), AWS does not fire
  on main. Adding either context to `main` `required_status_checks` blocks every staging→main PR on a check that only
  runs AFTER the merge it gates (the exact 2026-06-11 deadlock class). The correct gate needs a build that runs on the
  **PR head pre-merge** and posts a check the PR can require. See the new [WORKFLOW] todo "PR-head image-build gate"
  below — that machinery must land first; only then is this protection change safe (canary MTDS, watch one real green
  PR-head build, then fleet).
- [ ] [WORKFLOW] P2. **NEW (the real main-gate mechanism)**: build/validate the image on the **staging→main PR head**
  (a `pull_request: base=main` job that triggers Cloud Build, WAITS for it, and whose own success IS the required
  check) so an image-build failure blocks promotion pre-merge. Canary MTDS, prove green on a consumer repo + across
  branches (rule 11) before fleet-rolling into the v2 required-check template. Target: PM `quality-gates-v2.yml.tmpl`
  (or a new `image-build-gate.yml.tmpl`).
- [ ] [WORKFLOW] P3. Stop the LDR build's CodeBuild check from posting on LDR→staging drain PRs (the red noise).
  **(REALIZED 2026-06-11 via the `--build` opt-in: gating the AWS CodeBuild LDR webhook on `COMMIT_MESSAGE: Build-LDR:
  true` means non-opted LDR commits don't build → no CodeBuild status → no drain-PR noise. See Progress Log.)**
- [ ] [BUILD-FIX] P3. **NEW (decision item surfaced 2026-06-11)**: the AWS CodeBuild fleet (`terraform/cloud-build/aws`)
  is DRIFTED from terraform (live webhooks fire on LDR, not `var.branch_pattern`/main) and builds are intermittently red
  in PR context — decide whether AWS ECR is still a live deploy target. If YES: reconcile TF↔live (the live imperative
  webhook config is the SSOT to capture) + stabilise the build before any AWS gate. If NO: retire the AWS CodeBuild
  projects + webhooks (GCP `…-build` is the prod image build). Until decided, AWS is NOT a `main` required gate. Repo:
  `deployment-service`.

**Build-trigger surface map (3 interlocked paths — fully traced 2026-06-11; the implementation MUST reconcile all 3,
which is why this is canary-first, not a one-shot edit):**
1. **AWS CodeBuild webhook** (`terraform/modules/cloud-build/aws/main.tf`, single filter group): `EVENT=PUSH,
   HEAD_REF=^refs/heads/live-defi-rollout$` — direct, LDR-only.
2. **GCP Cloud Build triggers** (3 per service): `…-live-defi-rollout`, `…-feature-build`, `…-build` (the `…-build` is
   the intended main trigger — confirm its `branch_pattern`).
3. **v2 workflow step** `Dispatch cloud-build trigger (staging only)` in `scripts/workflow-templates/quality-gates-v2.yml.tmpl`
   (line ~72): `if: event_name=='push' && ref=='refs/heads/staging' && metadata_only!='true'` → `repository_dispatch
   qg-passed` to **`cloud-build-router.yml`** in PM. So builds ALSO fan out from a staging push via the router.
   The `--build` flag must thread through THIS step (read the `Build-LDR:` trailer) for the LDR path, while the AWS/GCP
   main trigger handles the always-on gate. quickmerge flag insertion point: `scripts/quickmerge.sh` arg `case` block
   (~line 116) + the trailer-stamp site.
**Canary order (MTDS)**: (1) quickmerge `--build`→trailer; (2) v2 step reads trailer (conditional LDR dispatch via
router); (3) test a quickmerge WITH and WITHOUT `--build`, confirm the LDR build fires/doesn't; (4) add main build
trigger (AWS filter group + GCP `…-build`); (5) add the build check to MTDS `main` required_status_checks + watch ONE
real staging→main gate on a green image; **only then** fleet-roll the template + TF + protection (skip PM/e2e/SIT).

## Gap 5 — Progress Log (autonomous finish-to-done, 2026-06-11)

Append-only. Durable state across context compaction (AUTONOMOUS_AGENT_RULES rule 6).

### Trace of live deployed state (grounding — the plan's TF/gate premises were partly false)

- **GCP triggers (MTDS)** — 3 exist, IMPERATIVELY created (NOT the drifted `terraform/cloud-build/gcp` module, whose
  module triggers point at a dead `connection_name="ln"`):
  - `market-tick-data-service-build` → push `^main$` via `iggyikenna-github` connection → check context
    `market-tick-data-service-build (central-element-323112)` — **GREEN on main**. This is the always-on prod build, but
    it fires **POST-merge** (`push:main`), so it is NOT a viable PR-head required check.
  - `market-tick-data-service-live-defi-rollout` → LDR push → `…-live-defi-rollout (central-element-323112)` — GREEN
    (the useful fast-feedback build; not the noise).
  - `market-tick-data-service-feature-build` → feature branches.
- **AWS CodeBuild (MTDS)** — project `market-tick-data-service`; LIVE webhook = single filter group `EVENT=PUSH,
  HEAD_REF=^refs/heads/live-defi-rollout$`, `pullRequestBuildPolicy.requiresCommentApproval=ALL_PULL_REQUESTS`. This is
  **DRIFTED from `terraform/cloud-build/aws/main.tf`** (TF says it fires on `var.branch_pattern`/main). It builds on
  EVERY LDR push (cost). **Correction (verified 2026-06-11): the AWS build is NOT persistently failing — the last 3
  builds SUCCEEDED.** The audit's "red noise on drain PRs" is the CodeBuild status surfacing on the drain PR (head = LDR
  commit) — intermittent failures and/or the `requiresCommentApproval` PR-context status. Gating the LDR webhook on the
  `Build-LDR` trailer removes the AWS status from non-opted LDR commits entirely → clean drain PRs + cost saved.
- **v2 `dispatch-cloud-build` step** — `if: event_name=='push' && ref=='refs/heads/staging'`; the template's `on:` no
  longer has `push:[staging]` (A3, 2026-06-10) → the step is **DEAD/skipped** on every commit. Cannot be the LDR-build
  dispatcher (v2 never runs on LDR).
- **staging→main PR head** — empirically the ONLY build-ish check is `Dispatch cloud-build trigger` = **skipped**. **No
  image build runs on the PR head.** Confirms the gate-deadlock risk.

### Decisions made (operator away; decide-and-document, AUTONOMOUS_AGENT_RULES rules 1–2)

1. **LDR build opt-in is realized CLOUD-NATIVELY, not via the v2 GHA step.** quickmerge `--build` stamps `Build-LDR:
   true`; the AWS CodeBuild LDR webhook gets a `COMMIT_MESSAGE` filter requiring that literal. Default OFF → no AWS LDR
   build → kills the red noise (Gap 5 P3) AND realizes opt-in (Gap 5 P2). Reason: the v2 step can't see LDR commits;
   COMMIT_MESSAGE webhook filtering is the cloud-native primitive the operator preferred ("cheap, no GHA minutes"). GCP
   LDR build (`…-live-defi-rollout`) stays always-on (green, free fast-feedback; GCP push triggers can't filter commit
   message anyway).
2. **The `main` required-check gate is NOT flipped.** As literally specified it deadlocks the fleet (no build on the PR
   head; GCP `-build` is post-merge; AWS is red). The correct gate is a NEW PR-head build job (tracked todo). Forcing
   the bad gate is the exact class the dispatch's #1 rule forbids.
3. **No `terraform apply` against the cloud-build modules.** Live infra is imperatively managed + drifted; apply would
   revert live webhooks/triggers fleet-wide. The AWS webhook canary change is applied imperatively (reversible) and
   mirrored into the TF module as documented intent only.

### Shipped

- `unified-trading-pm/scripts/quickmerge.sh` — `--build` flag → `Build-LDR: true` trailer (additive; inert until a
  cloud-native reader gates on it; `Quickmerge:` strict-guard unaffected — substring match). **SHIPPED PM@f6a4dbecf**
  (LDR; rides standing LDR→main PR, v2-gated; PM QG green; `bash -n` OK).

## Composes with

- `codex/08-workflows/ci-cd-flow.md` § "LDR is the SSOT" + § "Two-Pass Workflow Model" + the content-first dep-resolution
  update (2026-06-11).
- `plans/active/ldr_trunk_promotion_decoupling_2026_06_10.md` (Gap 1 is its incomplete-rollout tail).
- `plans/active/issues/instruments_service_version_phantom_2026_06_11.md` (RESOLVED — the version phantom Gap 1 amplified).
