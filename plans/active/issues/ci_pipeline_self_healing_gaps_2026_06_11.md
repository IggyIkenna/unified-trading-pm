---
title:
  "CI/CD pipeline self-healing gaps — semver-agent trigger starvation, LDR-rewind data loss, orchestrator stale-PR
  escalation"
created: 2026-06-11
locked_by: live-defi-rollout
priority: P1
status: active
source:
  - 2026-06-11 CI-board firefight (triage queue 4→14 conflict walls)
---

# CI/CD pipeline self-healing gaps (2026-06-11)

Three distinct systemic gaps surfaced during the 2026-06-11 CI-board firefight. Each needs a careful, fleet-validated
fix (deliberately NOT shipped blind during the firefight — see rule 11). All three have a precise root cause + fix
below. The acute board symptoms (14-item triage queue, instruments phantom, MTDS red main) were resolved manually; these
are the underlying causes so it does not recur.

## Gap 1 — semver-agent trigger starvation → staging→main drain stops fleet-wide (P1)

**Symptom**: `staging_commits{}` empty fleet-wide → `staging-to-main.yml` skips ("nothing to promote") → ~10 repos had
content stuck on staging never reaching main.

**Root cause**: The LDR-trunk decoupling (`ldr_trunk_promotion_decoupling_2026_06_10.md`, the
`A3 drop push:[staging] QG` change) removed `staging` from `python-quality-gates-v2.yml`'s `push:` triggers. But
`semver-agent.yml` still triggers ONLY on
`on: workflow_run: workflows:["quality-gates-v2"], types:[completed], branches:[staging]` — which needs a v2 run with
`head_branch == staging`. The LDR→staging Tier-C drain PR's v2 has `head_branch=live-defi-rollout` (the PR head), so the
`branches:[staging]` filter never matches → **semver-agent has not fired since ~2026-06-10 23:40 fleet-wide** → it never
dispatches `version-bump` → PM `update-repo-version.yml` never writes `staging_commits` → `staging-to-main.yml` skips.
(It DOES still fire off an existing staging→main PR's v2 re-run, which is why a manual staging→main merge bumps the
version — observed: instruments 0.3.0→0.4.0.)

**Fix (the intended draining signal already exists)**: make semver-agent fire off the **LDR→staging drain PR's v2
completion**. Minimal change in `scripts/workflow-templates/semver-agent.yml.tmpl` trigger (~line 37-40):

```yaml
workflow_run:
  workflows: ["quality-gates-v2"]
  types: [completed]
  branches: [staging, live-defi-rollout] # add live-defi-rollout
```

plus a guard step: proceed only when the triggering run is the LDR→staging promote PR (head=live-defi-rollout AND an
open/merged PR base=staging exists) OR head=staging; the template already scans the live `staging` tip (line ~104) so
the bumped SHA is the staging head, not the LDR head. The bump-rate circuit breaker (≥3/hr) already guards a loop.

**Blast radius (rule 11)**: fleet template → all ~24 repos. Roll via
`rollout-workflow-templates.sh --template semver-agent.yml` + commit/push each per-repo copy to LDR + promote to main
(workflow triggers fire only from the default branch). **Canary** on market-tick-data-service: confirm its semver-agent
fires off the next LDR→staging drain PR's v2, writes `staging_commits[market-tick-data-service]`, staging→main opens.
Then fan out. **Interim manual unblock** (no code): `gh workflow run quality-gates-v2.yml --repo <r> --ref staging` per
stuck repo fires the staging-head v2 → semver bumps → drains.

- [ ] [WORKFLOW] P1. Fix `semver-agent.yml.tmpl` trigger per above; canary on market-tick-data-service; roll out
      fleet-wide + promote to main. Verify a real LDR→staging drain fires semver + writes staging_commits.

## Gap 2 — LDR-rewind dropped committed feat work fleet-wide (P1, data integrity)

**Symptom**: features-service / unified-trading-api / agent-orchestrator / fund-administration-service had real
committed work on `staging` that was **absent from `live-defi-rollout`** (e.g. features-service's
volatility/treasury/DXY feature calculators, uta's seed.py refactor, AO's MainAgentKeeper). My safety guard caught this
and aborted force-syncing them (which would have re-dropped the work).

**Root cause**: NOT a quickmerge-to-staging bug (verified: per-repo `quickmerge.sh` are correctly symlinked to PM SSOT,
target LDR; the only `base=staging` PRs are Tier-C drains with `head=live-defi-rollout`). The dropped commits were ALL
merged to staging via `head=live-defi-rollout` Tier-C drains (e.g. features-service PR #123, base=staging, head=LDR,
merged 10:13Z) — i.e. **they WERE on LDR at drain time**. A **clean-start force-sync that rewound `live-defi-rollout` to
a slightly-stale snapshot after ~10:13** dropped those recent commits from LDR while staging retained them. The
`staging-backmerge-to-ldr` safety-net did not recover them.

**Recovery done**: back-merged `staging → LDR` for each affected repo (recovered the dropped commits to LDR, QG-green),
then their drain PRs cleared. **Residual risk**: repos that lost LDR commits which were NOT yet drained to staging are
silently gone (recoverable only from `origin/wip-preserve/*` or reflog) — not detectable by the staging>LDR guard.

- [x] ✅ [SCRIPT] P1. DONE 2026-06-16 (unified-trading-pm PR #361) — added a **LDR-rewind freshness guard** to
      `admin-force-sync-all-to-main.sh`: before each per-repo force-push (any target), it fetches
      `origin/live-defi-rollout` and asserts the local HEAD it is about to push **includes all of current LDR**
      (`git merge-base --is-ancestor origin/live-defi-rollout HEAD`). If the local snapshot is BEHIND LDR the push is
      blocked (`REWIND-BLOCKED`, repo recorded FAIL) with the dropped-commit count + the refresh recipe — a stale
      snapshot can no longer silently drop LDR commits that may already be on staging. **Squash-proof** (compares HEAD
      directly to LDR; no staging ancestry, which squash-merges break). `--allow-rewind` overrides for the rare
      intentional rewind. Verified: fresh HEAD passes, stale HEAD~N blocks. Composes with
      `codex/08-workflows/ci-cd-flow.md` § "LDR is the SSOT — back-merge DOWN first".
- [ ] [SCRIPT] P2. One-off: diff `origin/wip-preserve/*` + reflog vs current LDR per repo to detect any silently-dropped
      commit NOT on staging; recover or confirm none.

## Gap 3 — orchestrator does not auto-resolve stuck/conflicting promote PRs (P1, operator-raised 2026-06-11)

**Operator ask**: "agent-orchestrator should be picking up these stale PRs via escalation — if they don't have a
`Quickmerge:` trailer in the push, the orchestrator should spawn a worker in a slot, run quality gates + resolve the
commits, and if happy quickmerge so they go through and delete the stale PR. A merge conflict / auto-merge-didn't-work
case should be figured out and fixed automatically."

**Current state**: `ci-failure-watcher.py --auto-recover` only close+reopens the narrow
`BLOCKED + no failed check + v2 absent` mechanical deadlock. `--escalate` is meant to spawn a worker for a genuine
CONFLICTING/DIRTY wall, but in practice "yields no worker spawned" when the orchestrator is headroom-less (per
CLAUDE.md). So a fleet event that creates ~13 conflict-wall drain PRs at once (template rollout leaving staging behind +
an LDR rewind) is NOT auto-handled — it required a manual firefight.

**Recommended fix**: the escalation path must reliably (a) spawn a worker even under load (queue + AutoSpawn, not a
no-op), (b) the worker runs the deterministic recovery this firefight used: classify the conflict (drain-noise/template/
version → force-sync staging=LDR; real staging content LDR lacks → back-merge staging→LDR; staging→main → promote
clean-FF), run QG, quickmerge, then **close the now-empty drain PR**. Encode the classifier + recovery as a worker
runbook the orchestrator dispatches on a conflict-wall alert.

- [x] ✅ [ORCHESTRATOR] P1. DONE 2026-06-12 — agent-orchestrator@2e989df (feature) + @d6cff0f (nested-session deadlock
      hotfix found in the live drill), QG green ×2, 26 escalation tests, deployed + LIVE-VERIFIED on vm-e2e-test. All 3
      sub-parts: (1) **queue-on-no-capacity** — `escalate()` no longer raises/503s when there's no free slot or headroom
      account: the escalation persists to the new `escalation_queue` table (`status='queued'`, full payload) and the
      AutoSpawnLoop tick retries it (oldest-first, ≤2/tick, escalations claim free slots BEFORE backlog tasks; 24h TTL →
      abandoned + Slack; the retry calls with `queue_on_no_capacity=False` so still-blocked rows stay queued). Live
      proof (vm-e2e-test, all 3 accounts at ceiling = the exact firefight condition): `POST /api/escalate` → HTTP 200
      `{"status":"queued", escalation_id agt-979dc0}` + retry-tick logged each AutoSpawnLoop pass — the wall is OWNED,
      not dropped. (2) **deterministic reconciliation runbook** — `agents/conflict-resolver.md` step 2 is now the
      codified firefight ladder (first match wins): superseded→close · drain-noise (`compare` ahead>0 but
      `files==0`)→close, never merge an empty drain · target-only real content→back-merge target INTO source first
      (LDR-is-SSOT; force-sync staging=LDR stays OPERATOR-GATED — worker stops + pings instead) · real conflict→resolve
      on source on merits (workflow-file churn: PM template SSOT decides). (3) **auto-close emptied drain PRs** — new
      step 5c re-runs the compare after reconcile and closes a now-empty PR instead of merging noise. Was: make
      `--escalate` actually spawn a worker for conflict-wall promote PRs (queue if headroom-less) + runbook +
      auto-close. Repo: agent-orchestrator.

## Gap 3b — Tier-C drains are BORN in the v2-never-reported deadlock + auto-recover lags ~hourly (P1)

**Symptom (recurring)**: a fresh wave of "Auto-merge stuck → staging" Tier-C drain PRs (e.g. 2026-06-11 ~19:24:
alerting#81, BLRS#73, deployment-api#66, deployment-service#67, instruments#439, strategy#172) — all
`MERGEABLE/BLOCKED`, `v2 absent`, no failed check (the exact v2-never-reported signature), all `staging⊆LDR` (clean FF).
They pile up every time LDR gets new content.

**Root cause**: (1) The `ldr-to-staging-promote` (Tier-C) bot creates the drain PR with a token whose
`pull_request`/`push` event is **suppressed by GitHub's own-token loop-prevention**, so `quality-gates-v2` never fires
on the new PR head → required check missing → BLOCKED-from-birth (auto-merge can never complete). (2)
`ci-failure-watcher --auto-recover` is the designed self-heal (workflow_dispatch-re-fire v2, since close+reopen is
equally token-suppressed), but its `schedule: */15` is **throttled by GitHub to an effective ~70–90 min cadence**
(observed: runs at 18:59 / 17:52 / 16:38 / 15:11 — not every 15 min), so a wave of stuck drains stays visibly parked for
up to ~1.5h before recovery.

**Fix (durable — stops the recurrence at the source)**:

- [x] ✅ **[DONE 2026-06-12 — `ldr-to-staging-promote.yml` now creates the drain PR with a GitHub App token
      (`78151ca49`), so the `pull_request` event fires and v2 runs at birth; plus a STALE-CHECK v2 force-dispatch
      fallback (`270d02fec`). PR no longer born-deadlocked.]** [WORKFLOW] P1. `ldr-to-staging-promote` (Tier-C): after
      creating the drain PR, **explicitly `gh workflow run quality-gates-v2.yml --ref <pr-head-sha>`** (or create the PR
      with `GH_PAT` so the `pull_request` event fires) — so the drain PR is never born-deadlocked and auto-merge
      completes immediately. Verify a fresh drain reports v2 within minutes + auto-merges with no manual touch.
- [ ] [WORKFLOW] P2. ci-failure-watcher: don't rely on `schedule` cadence alone (GitHub throttles it) — add a
      `pull_request`-event-driven path (or shorten the practical detection window) so the v2-absent deadlock is
      recovered in minutes, not the next ~hourly tick.

## Gap 4 — deployment-ui should show "agent working / pending" for a repo under active recovery (P2, operator-raised 2026-06-11)

**Operator ask**: "the dashboard should show if an agent is working on it as pending — that's the repos in
deployment-ui." When a stuck/conflicting promote PR is actively being recovered (by the orchestrator's escalated worker
per Gap 3), the deployment-ui Repos-CI board should render that repo as **pending / being-worked**, not **stuck** — so
the operator can tell "an agent has this" apart from "genuinely parked, needs attention."

- [ ] [UI] P2. deployment-ui Repos-CI board: surface a `working`/`pending` state per repo (driven by the orchestrator's
      active-worker assignment for that repo's stuck PR) distinct from `stuck`. Composes with Gap 3 (the orchestrator
      must first own + assign the recovery). Playwright gate per CLAUDE.md (`pw:L2 ✓` + regression spec) before ticking.
      **ORCHESTRATOR HALF SHIPPED 2026-06-12 (agent-orchestrator@2e989df)**: `GET /api/escalations/active` returns
      `[{escalation_id, status: queued|dispatched, repo, pr_number, wall_type, slot_id, created_at, dispatched_at, attempts}]`
      — `queued` rows always active; `dispatched` rows active for 2h post-dispatch (escalation workers are one-shot with
      no completion callback; the window stops a finished worker reading as in-progress forever). Live-verified on
      vm-e2e-test. Remaining = the deployment-ui render only.

## Gap 5 — image-build trigger + gate redesign (operator-decided 2026-06-11)

**Today (verified)**: image builds are **cloud-native** (GCP Cloud Build triggers + AWS CodeBuild webhook — NOT GitHub
Actions, so cheap + no GHA minutes). They fire on **`live-defi-rollout` push** and are **NOT a required check anywhere**
(every repo's `main` requires only `quality-gates-v2`). AWS CodeBuild webhook = single filter group
`EVENT=PUSH, HEAD_REF=^refs/heads/live-defi-rollout$`. GCP has 3 triggers per service (`…-live-defi-rollout`,
`…-feature-build`, `…-build`). The red "Build not triggered: PR approval required" on a staging drain PR is the LDR
build's check surfacing on the PR (head=LDR commit) — noise, not a staging build.

**Decided design**:

- **Build contexts**: feature-branch (dev deploy off a feature branch) + **LDR (OPT-IN, fast feedback)** + **main
  (ALWAYS, the deploy gate)**.
- **`quickmerge --build` flag**: the user decides per-ship whether they want the LDR image. quickmerge stamps a commit
  trailer (e.g. `Build-LDR: true`, alongside the existing `Quickmerge:` trailer). The v2 workflow's existing **"Dispatch
  cloud-build trigger"** step reads that trailer and conditionally dispatches the LDR build. No flag → no LDR build
  (save cost); the **main build always runs** regardless.
- **Gate**: the **staging→main and staging gates FAIL if the image build fails** — add the GCP Cloud Build + AWS
  CodeBuild check contexts to each deployed repo's `main` `required_status_checks` (and the build must run on the main
  commit — add a `PUSH ^refs/heads/main$` filter group to the AWS webhook in
  `terraform/modules/cloud-build/aws/main.tf`; confirm the GCP `…-build` trigger is on main).
- **Exclusions (no image build at all)**: **unified-trading-pm** (no Dockerfile, no build project — confirmed; not
  deployed), **e2e-testing** + **system-integration-tests** (test harnesses, no CodeBuild). UI repos
  (`deployment-ui`/`unified-trading-system-ui`) have Dockerfiles but build via **GCP only** (no AWS CodeBuild) — keep as
  is.

- [x] [WORKFLOW] P2. ✅ quickmerge: `--build` flag → `Build-LDR: true` commit trailer — **PM@f6a4dbecf** (PM QG green;
      `bash -n` OK; trailer-logic unit-verified via `git interpret-trailers`). The v2-step dispatch path was DROPPED as
      unworkable (v2 never runs on LDR); LDR opt-in is realized cloud-natively via the AWS CodeBuild webhook
      `COMMIT_MESSAGE` filter (see P3 below + Progress Log "Test evidence").
- [ ] [TERRAFORM] P2. AWS CodeBuild webhook: add `PUSH ^refs/heads/main$` filter group (keep LDR group). Confirm GCP
      `…-build` trigger targets `main`. `terraform/modules/cloud-build/aws/main.tf`. **(CORRECTED 2026-06-11: the live
      AWS webhooks + GCP triggers are IMPERATIVELY managed and DRIFTED from this terraform — a blind `terraform apply`
      would revert live config fleet-wide. GCP `…-build` already fires on `^main$` (green). The AWS-main filter group is
      BLOCKED on the failing AWS build, see new todo below.)**
- [ ] [PROTECTION] P2. **BLOCKED-DESIGN — do NOT flip naïvely (would deadlock the fleet).** Empirically (2026-06-11): NO
      image build runs on the staging→main PR head — GCP `…-build` fires on `push:^main$` (POST-merge), AWS does not
      fire on main. Adding either context to `main` `required_status_checks` blocks every staging→main PR on a check
      that only runs AFTER the merge it gates (the exact 2026-06-11 deadlock class). The correct gate needs a build that
      runs on the **PR head pre-merge** and posts a check the PR can require. See the new [WORKFLOW] todo "PR-head
      image-build gate" below — that machinery must land first; only then is this protection change safe (canary MTDS,
      watch one real green PR-head build, then fleet).
- [ ] [WORKFLOW] P2. **NEW (the real main-gate mechanism)**: build/validate the image on the **staging→main PR head** (a
      `pull_request: base=main` job that triggers Cloud Build, WAITS for it, and whose own success IS the required
      check) so an image-build failure blocks promotion pre-merge. Canary MTDS, prove green on a consumer repo + across
      branches (rule 11) before fleet-rolling into the v2 required-check template. Target: PM
      `quality-gates-v2.yml.tmpl` (or a new `image-build-gate.yml.tmpl`).
- [x] [WORKFLOW] P3. ✅ Stop the LDR build's CodeBuild check posting on drain PRs (the red noise) — REALIZED via the
      `--build` opt-in: the live MTDS AWS CodeBuild webhook is gated on `COMMIT_MESSAGE: Build-LDR: true`, so non-opted
      LDR commits don't build → no CodeBuild status → clean drain PRs. **Evidence (MTDS live test): commit A (with
      trailer) `1b3e6c2c` → AWS CodeBuild fired; commit B (no trailer) `58b77a77` → 0 AWS statuses (gated off); GCP LDR
      build fired on both (always-on by design).** TF module support: **deployment-service@c529afb** (additive,
      default-off). MTDS-only imperative webhook change (reversible; original in `/tmp/mtds_webhook_orig.json`). Fleet
      rollout pending TF↔live reconciliation (BUILD-FIX P3).
- [ ] [BUILD-FIX] P3. **NEW (decision item surfaced 2026-06-11)**: the AWS CodeBuild fleet (`terraform/cloud-build/aws`)
      is DRIFTED from terraform (live webhooks fire on LDR, not `var.branch_pattern`/main) and builds are intermittently
      red in PR context — decide whether AWS ECR is still a live deploy target. If YES: reconcile TF↔live (the live
      imperative webhook config is the SSOT to capture) + stabilise the build before any AWS gate. If NO: retire the AWS
      CodeBuild projects + webhooks (GCP `…-build` is the prod image build). Until decided, AWS is NOT a `main` required
      gate. Repo: `deployment-service`.

> **PARTIALLY SUPERSEDED 2026-06-11 — see "Gap 5 — Progress Log" below.** The surface map's facts hold, but the
> implementation deviated: the v2-step dispatch (path 3) is unworkable (v2 never runs on LDR), LDR opt-in is realized
> via the AWS webhook `COMMIT_MESSAGE` filter, and the `main` required-check gate (canary-order steps 4–5) was NOT
> flipped (it would deadlock the fleet — no build runs on the PR head). Read the Progress Log for what actually shipped.

**Build-trigger surface map (3 interlocked paths — fully traced 2026-06-11; the implementation MUST reconcile all 3,
which is why this is canary-first, not a one-shot edit):**

1. **AWS CodeBuild webhook** (`terraform/modules/cloud-build/aws/main.tf`, single filter group):
   `EVENT=PUSH, HEAD_REF=^refs/heads/live-defi-rollout$` — direct, LDR-only.
2. **GCP Cloud Build triggers** (3 per service): `…-live-defi-rollout`, `…-feature-build`, `…-build` (the `…-build` is
   the intended main trigger — confirm its `branch_pattern`).
3. **v2 workflow step** `Dispatch cloud-build trigger (staging only)` in
   `scripts/workflow-templates/quality-gates-v2.yml.tmpl` (line ~72):
   `if: event_name=='push' && ref=='refs/heads/staging' && metadata_only!='true'` → `repository_dispatch    qg-passed`
   to **`cloud-build-router.yml`** in PM. So builds ALSO fan out from a staging push via the router. The `--build` flag
   must thread through THIS step (read the `Build-LDR:` trailer) for the LDR path, while the AWS/GCP main trigger
   handles the always-on gate. quickmerge flag insertion point: `scripts/quickmerge.sh` arg `case` block (~line 116) +
   the trailer-stamp site. **Canary order (MTDS)**: (1) quickmerge `--build`→trailer; (2) v2 step reads trailer
   (conditional LDR dispatch via router); (3) test a quickmerge WITH and WITHOUT `--build`, confirm the LDR build
   fires/doesn't; (4) add main build trigger (AWS filter group + GCP `…-build`); (5) add the build check to MTDS `main`
   required_status_checks + watch ONE real staging→main gate on a green image; **only then** fleet-roll the template +
   TF + protection (skip PM/e2e/SIT).

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
- **AWS CodeBuild (MTDS)** — project `market-tick-data-service`; LIVE webhook = single filter group
  `EVENT=PUSH, HEAD_REF=^refs/heads/live-defi-rollout$`,
  `pullRequestBuildPolicy.requiresCommentApproval=ALL_PULL_REQUESTS`. This is **DRIFTED from
  `terraform/cloud-build/aws/main.tf`** (TF says it fires on `var.branch_pattern`/main). It builds on EVERY LDR push
  (cost). **Correction (verified 2026-06-11): the AWS build is NOT persistently failing — the last 3 builds SUCCEEDED.**
  The audit's "red noise on drain PRs" is the CodeBuild status surfacing on the drain PR (head = LDR commit) —
  intermittent failures and/or the `requiresCommentApproval` PR-context status. Gating the LDR webhook on the
  `Build-LDR` trailer removes the AWS status from non-opted LDR commits entirely → clean drain PRs + cost saved.
- **v2 `dispatch-cloud-build` step** — `if: event_name=='push' && ref=='refs/heads/staging'`; the template's `on:` no
  longer has `push:[staging]` (A3, 2026-06-10) → the step is **DEAD/skipped** on every commit. Cannot be the LDR-build
  dispatcher (v2 never runs on LDR).
- **staging→main PR head** — empirically the ONLY build-ish check is `Dispatch cloud-build trigger` = **skipped**. **No
  image build runs on the PR head.** Confirms the gate-deadlock risk.

### Decisions made (operator away; decide-and-document, AUTONOMOUS_AGENT_RULES rules 1–2)

1. **LDR build opt-in is realized CLOUD-NATIVELY, not via the v2 GHA step.** quickmerge `--build` stamps
   `Build-LDR: true`; the AWS CodeBuild LDR webhook gets a `COMMIT_MESSAGE` filter requiring that literal. Default OFF →
   no AWS LDR build → kills the red noise (Gap 5 P3) AND realizes opt-in (Gap 5 P2). Reason: the v2 step can't see LDR
   commits; COMMIT_MESSAGE webhook filtering is the cloud-native primitive the operator preferred ("cheap, no GHA
   minutes"). GCP LDR build (`…-live-defi-rollout`) stays always-on (green, free fast-feedback; GCP push triggers can't
   filter commit message anyway).
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
- **MTDS AWS CodeBuild webhook** — gated the LDR filter group on `COMMIT_MESSAGE: Build-LDR: true` (imperative,
  MTDS-only, reversible — original filterGroups saved to `/tmp/mtds_webhook_orig.json`; rollback =
  `aws codebuild update-webhook --project-name market-tick-data-service --region ap-northeast-1 --filter-groups <orig>`).
- `deployment-service/terraform/modules/cloud-build/aws/{main,variables}.tf` — new optional
  `github_commit_message_filter` var + dynamic `COMMIT_MESSAGE` filter (additive, default `""` → no behavior change;
  documents the fleet path). **SHIPPED deployment-service@c529afb** (LDR; `terraform fmt` clean; not QG-gated; rides the
  drain).

### Test evidence (operator-requested MTDS canary, 2026-06-11)

1. **Trailer construction (unit)** — `quickmerge --build` produces a trailer block `Quickmerge: agent\nBuild-LDR: true`;
   without `--build` it is just `Quickmerge: agent`. Both parse cleanly via `git interpret-trailers --parse`.
2. **Live webhook gate (end-to-end on MTDS LDR)** — two net-zero scratch commits (add + remove of
   `.ci-build-flag-test`):
   - Commit **A** `1b3e6c2c` carrying `Build-LDR: true` → **AWS CodeBuild FIRED**
     (`AWS CodeBuild ap-northeast-1 (market-tick-data-service)` status present) + GCP `…-live-defi-rollout` build
     in-progress.
   - Commit **B** `58b77a77` with NO trailer → **0 AWS CodeBuild statuses** (gated off) + GCP `…-live-defi-rollout`
     build queued (always-on).
   - Conclusion: `--build` ⇒ opt-in AWS LDR build; default ⇒ no AWS build ⇒ no drain-PR noise. Exactly the design.
   - (Commit A's AWS build state was `failure` — that is the SEPARATE intermittent AWS-build-health item, BUILD-FIX P3;
     it does not affect the gate, which is about whether the build TRIGGERS.)

### Decision: GCP `…-live-defi-rollout` LDR build stays ALWAYS-ON (not gated by `--build`)

The operator's "no flag → no LDR build" is realized for the **AWS CodeBuild** build (the cost + drain-PR-noise concern
the Gap-5 text centers on). The GCP `…-live-defi-rollout` build is left always-on because (a) it is green and is the
useful "fast feedback" signal the design also calls for, and (b) GCP 2nd-gen push triggers **cannot filter on commit
message** — fully gating GCP would require disabling the native trigger + a heavy `cloud-build-router` dispatch path
(the router has no LDR route and runs deploy/freeze logic). If the operator wants GCP LDR also fully opt-in, that is the
follow-up below.

- [ ] [INFRA] P3. **(optional, operator-decision)** Make the GCP `…-live-defi-rollout` build ALSO opt-in: disable the
      native GCP LDR trigger + add a `--build`-driven dispatch path (router needs an LDR/dev route first). Today GCP LDR
      is always-on fast feedback; only AWS LDR is gated. Repo: `deployment-service` + PM `cloud-build-router.yml`.

### Final report — end-state (autonomous session 2026-06-11)

**Done + verified:** (1) `quickmerge --build` flag + trailer (PM@f6a4dbecf); (2) AWS LDR build is now opt-in on MTDS +
the red drain-PR noise is gone (live-tested A-fires/B-silent); (3) TF module supports the filter for the eventual clean
fleet path (deployment-service@c529afb).

**Deliberately NOT done (would have created the exact fleet-deadlock the dispatch's #1 rule forbids), with the corrected
path documented as tracked todos above:** the `main` required-check image-build gate. Hard evidence: NO image build runs
on the staging→main PR head (GCP `…-build` is post-merge `push:^main$`, green; AWS does not fire on main) — so adding
either context to `main` `required_status_checks` permanently blocks every staging→main PR. The correct gate is a NEW
PR-head build job (the new [WORKFLOW] P2 todo); the AWS-as-gate path is additionally blocked on the drifted/intermittent
AWS build (BUILD-FIX P3). A `terraform apply` was deliberately NOT run — the live AWS webhooks + GCP triggers are
imperatively managed and drifted from terraform; applying would revert live config fleet-wide.

**Fleet rollout (the remaining scale-out) is intentionally NOT done from one session** — it is gated on the TF↔live
reconciliation (BUILD-FIX P3) so the AWS-webhook gate can roll via clean IaC rather than per-repo imperative edits, and
on the PR-head-build gate machinery landing + being proven green across a consumer repo and all branches (rule 11).
Tracked above. The MTDS canary is green; the foundation (`quickmerge --build`) is fleet-live via the symlinked SSOT.

## Gap 6 — `staging-backmerge-to-ldr.yml` silently absent on 4 repos → Tier-C runaway-promote loop (P1, incident 2026-06-15)

**Symptom**: RUNAWAY PROMOTE BREAKER paged for `ml-service`, `agent-orchestrator`, `e2e-testing` (30 LDR→staging drain
merges/6h). `unified-trading-api` (28/6h) + `unified-trading-system-ui` were about to trip; `greeks-service` (15/6h) was
an early-warning.

**Root cause**: Ikenna's 2026-06-08 fleet rollout of `staging-backmerge-to-ldr.yml` (PM template created 06-08
`6a75ca7fb`; workflow first introduced 06-05 `613481d0b`) **silently skipped 8 of 24 repos** — `features-service`,
`fund-administration-service`, `greeks-service`, `ml-service`, `e2e-testing`, `agent-orchestrator`,
`unified-trading-api`, `unified-trading-system-ui`. All 8 were patched 2026-06-15 during this incident (5 by slot-4 at
~19:02–19:04; 3 by the root session at ~19:32–19:35). semver version bumps + UTL
dep-floor bumps + base-image digest refreshes land on `staging` (semver-agent / dependency fan-out), and
`staging-backmerge-to-ldr.yml` is the ONLY mechanism that flows them back DOWN to LDR (`main-backmerge-to-ldr.yml` can't —
the bump is on staging, not yet main). With it absent, LDR stayed behind staging on `version`/pin/digest → the Tier-C
drain perpetually saw a real two-dot content delta → promoted LDR→staging → the promote tried to revert staging's newer
version → semver re-bumped → **ping-pong, ~1 merge/tick** → runaway breaker. `agent-orchestrator` was the worst case: it
gained a `staging` branch (no longer main-direct) but never received the template. The drift IS detected by
`detect_template_drift.py` (`workflow-missing-<name>`) — but only as a **WARN** in a local-only post-gate (CI no-op), so
nobody acted on it for weeks.

**Fixed in real time 2026-06-15** (content-first convergence, LDR-is-SSOT remedy; two sessions in parallel — slot-4
rolled the workflow to features/fund-admin/greeks/ml/e2e ~19:02–04, root session to ao/uta/ui ~19:32–35): backmerged
`staging`→LDR on each diverged repo (conflict-free — LDR hadn't touched the diverging lines since the merge-base) +
rolled out `staging-backmerge-to-ldr.yml`; then promoted the converged LDR→staging via a v2-gated PR (titled NOT
`chore(promote)` to avoid re-inflating the breaker count) so staging gets the workflow + the 3 tripped repos go
tree-equal → the drain skips them at the tree-equality gate BEFORE the runaway breaker → pages stop. `greeks-service`
self-healed (it already had the workflow). Evidence: ao@dbcc2b0 + #303, e2e@760b546 + #286, ml #108, uta@23a20b3,
ui@f2223d47.

- [x] ✅ [WORKFLOW] P1. DONE 2026-06-16 (unified-trading-pm PR #359) — `detect_template_drift.py --workflows` now
      escalates a MISSING `staging-backmerge-to-ldr.yml` / `main-backmerge-to-ldr.yml` from WARN → **ERROR**
      (`CRITICAL_PROMOTE_TEMPLATES`); `staging-backmerge` is gated on the repo actually having an `origin/staging` ref
      (`_repo_has_staging`, so main-direct repos don't false-error), `main-backmerge` applies to all. Non-critical
      templates stay WARN on missing. Logic unit-tested (severity matrix + staging detection).
- [ ] [WORKFLOW] P2. Add a fleet presence-audit to PM QG post-gates (or `ldr-to-staging-promote.yml` itself): for every
      repo in `topologicalOrder` with a `staging` branch, assert `staging-backmerge-to-ldr.yml` exists on `staging` (not
      just LDR — `on: push:[staging]` only fires from the pushed branch). Page if absent. This is the early-warning the
      drift detector's local-only WARN failed to surface.
- [ ] [WORKFLOW] P3. Consider teaching the Tier-C runaway breaker to self-diagnose: when it trips, check whether the
      repo's `staging` lacks `staging-backmerge-to-ldr.yml` and name that in the page (turns a generic "promote loop"
      alert into an actionable root cause).

**Decision (2026-06-15, operator-confirmed) — do NOT add a `schedule`+`workflow_dispatch` drift-tick to
`staging-backmerge-to-ldr.yml`.** It was tried (`49029aa44`) and reverted (`790e7fb51`) the same day. The reverted
commit's premise ("`push:[staging]` NEVER fires — GITHUB_TOKEN suppression") is **empirically false**: the workflow
fires constantly on `push` (unified-api-contracts 100 runs, instruments 52, execution 39 — all `push`), because the
Tier-C drain merges to staging with a **GitHub App installation token**, and App-token pushes DO trigger workflows
(only raw `GITHUB_TOKEN` pushes are suppressed). The ACTUAL incident cause was Layer A (8 repos missing the file), now
fixed. A hourly cron × ~24 repos also adds Actions spend during the same billing-sensitive window that throttled
`main-backmerge`'s tick. The P1/P2 presence-audit above is the correct guard (catches the real failure = a missing
file), not the schedule tick. Re-introduce the tick ONLY on a concrete observed case of a raw-`GITHUB_TOKEN` staging
push (e.g. a semver `chore(release)` bump) that failed to self-heal on the next drain cycle.

## Gap 7 — `promotion_quarantine` is a SELF-PERPETUATING DEADLOCK: skip → never `promoted` → never auto-clears (P1, incident 2026-06-16)

**Found 2026-06-16** while freeing the monitoring-ui "Promotion blocked — staging→main (4)" panel
(execution-service / strategy-service / unified-api-contracts / system-integration-tests, each `attempts:3,
escalated:true`). The four had been quarantined during the recurring jam — but **3 of the 4 merged staging→main cleanly
when trial-merged** (only SIT had a real `pyproject.toml` version conflict). They were NOT blocked by any current
problem; they were stuck purely by the quarantine mechanism itself.

**The deadlock (`staging-to-main.yml`):**

1. The promote-loop builder (`~line 536`) **SKIPS** any repo in `promotion_quarantine`.
2. The counter step (`~line 790`) only **clears** quarantine for repos in the `promoted` set
   (`for repo in promoted: quarantine.pop(repo)`).
3. A skipped repo can never enter `promoted` → its quarantine entry can never auto-clear → it is skipped **forever**.

The escalation message even tells the worker the WRONG recovery: _"Resolve on live-defi-rollout, let quality-gates-v2
re-gate, and the next successful promotion auto-clears the quarantine."_ — but the next promotion **skips** the
quarantined repo, so resolving on LDR does nothing. The only working recovery is a **manual `promotion_quarantine` edit**
(what I did: PM PR #351 cleared all 4 + reconciled stale `versions` for the two already-on-main; then a
`staging-to-main` dispatch promoted strategy/uac). This is why every jam needs hands-on recovery — the auto-recovery the
system claims to have does not exist for this path.

**Recovery performed 2026-06-16 (the manual steps the auto-fix below must replace):**

1. Diagnosed all 4 via trial `git merge staging→main` — execution = already merged (ahead_by=0); strategy + uac merged
   CLEAN; SIT = real `pyproject.toml` conflict (main stuck 0.3.3 + old dep floors vs LDR/staging 0.6.0 authoritative).
2. SIT: `admin-force-sync-all-to-main.sh --repo system-integration-tests --no-commit --preserve-local
   --force-version-override` (main ⊆ LDR, behind_by=0 → content-lossless) → main=LDR (0.6.0), protection restored, the
   open conflicting staging→main PR #231 auto-resolved to MERGED.
3. Cleared `promotion_quarantine` + `promotion_failures` for all 4 and reconciled stale `versions` (exec 0.9.1→0.10.0,
   SIT 0.5.0→0.6.0) in `workspace-manifest.json` — **PM PR #351 (merged)**.
4. `gh workflow run staging-to-main.yml` → promoted strategy + uac (clean merges). Final: quarantine + failures EMPTY;
   all 4 main==LDR (modulo the 1-file semver-brake drain). Monitoring-ui "Promotion blocked (4)" panel clears.

- [x] ✅ [WORKFLOW] P1. Made quarantine **auto-recoverable** — DONE 2026-06-16 (unified-trading-pm PR #358).
      `staging-to-main.yml` merge-builder no longer permanently skips a quarantined repo: it RE-PROBES (lets it through)
      once the re-probe is DUE (`next_probe_after` elapsed / absent), and the existing `changed & ready_set` filter still
      enforces deps-on-main + the merge loop tests real mergeability. A clean re-probe promotes → the counter step's
      existing `for repo in promoted: quarantine.pop()` auto-clears it; a still-conflicting re-probe stays quarantined
      with `next_probe_after` pushed out (bounded exponential backoff 60→120→240, cap 360 min) — no every-run noise, and
      the alert partition already excludes quarantined repos so no re-alert. Logic unit-simulated (due/not-due,
      backoff curve, re-probe-fail stays-quarantined-no-realert, re-probe-success clears). Dormant until a repo
      re-quarantines (quarantine currently empty) → zero immediate behaviour change.
- [x] ✅ [WORKFLOW] P1. Fixed the escalation text — DONE 2026-06-16 (PR #358). It now states the repo WILL be re-probed
      (gives `next_probe_after`), that a now-clean repo self-promotes + auto-clears with no action, and that escalation
      means it's a REAL conflict needing resolution (force-sync main=LDR when `main ⊆ LDR`, else resolve on staging) —
      after which the next due re-probe auto-clears it, so do NOT hand-edit the manifest unless the re-probe is broken.
      (The orchestrator-side `ci_failure_watcher.py` explicit-clear is now redundant for the common case since the
      workflow self-clears; left as the remaining belt-and-suspenders option if ever needed — folded into the P2 below.)
- [ ] [WORKFLOW] P2. Add a watchdog/alert for `promotion_quarantine` entries older than ~2h with `escalated:true` AND a
      currently-clean staging→main merge — that exact combination is the deadlock signature (stuck with nothing wrong).

## Gap 8 — staging→main dep-order gate decides on STALE manifest cache: Firestore overlay dies on `ModuleNotFoundError: google` (P1, incident 2026-06-16)

**Found 2026-06-16** in the live `staging-to-main.yml` STAGE 1.8 (dep-order gate) log:
`ci_status Firestore read unavailable (ModuleNotFoundError: No module named 'google') — using manifest fallback cache`.
The gate's `_fs_overlay()` (and `tier_c_promotion_gate.py::_overlay_firestore_ci_status`) is wrapped in a bare
`except Exception: pass`, so when the PM Actions runner lacks `google-cloud-firestore`, the **live Firestore-authoritative
`ci_status` overlay is silently skipped** and the gate falls back to the manifest's **committed (stale) `ci_status`
cache**. Per `ci_status_firestore_side_store_2026_06_10.md` the whole point of Phase-2 was to make Firestore
authoritative; in CI it is currently a **silent no-op** → promotion-readiness decisions ride stale state, which is one of
the inputs that lets the recurring jam mis-gate (promote-blocked on a dep the manifest THINKS is red but Firestore knows
is green, or vice-versa).

- [x] ✅ [WORKFLOW] P1. Installed the Firestore client in BOTH PM promote workflows — `staging-to-main.yml` +
      `ldr-to-staging-promote.yml` now carry a best-effort `google-github-actions/auth@v3` (GCP_SA_KEY) +
      `pip install "google-cloud-firestore>=2,<3"` step after Checkout, plus a job-level `GOOGLE_CLOUD_PROJECT` env (the
      overlay needs both auth+SDK+project). Mirrors `ci-failure-watcher.yml`. — unified-trading-pm PR #353 (2026-06-16).
      _Verify on the next live run: the gate log shows "overlay applied (live)" not the ModuleNotFoundError fallback._
- [x] ✅ [SCRIPT] P1. Made the overlay failure **LOUD** in all three sites (`_fs_overlay` ×2 in `staging-to-main.yml`
      heredocs + `_overlay_firestore_ci_status` in `tier_c_promotion_gate.py`): split `except Exception: pass` into a
      `ModuleNotFoundError` branch (CI-config bug → `::warning:: SDK unavailable, deciding on STALE cache`) vs a generic
      branch (Firestore degraded → warn + fallback). — unified-trading-pm PR #353 (2026-06-16).
- [x] ✅ [SCRIPT] P2. Gate-start self-check covered by the LOUD `::warning::` above — a missing/failed Firestore client
      now emits an explicit annotation each run, so the side-store's authoritativeness is monitored, not assumed. —
      unified-trading-pm PR #353 (2026-06-16).

## Composes with

- `codex/08-workflows/ci-cd-flow.md` § "LDR is the SSOT" + § "Two-Pass Workflow Model" + the content-first
  dep-resolution update (2026-06-11).
- `plans/active/ldr_trunk_promotion_decoupling_2026_06_10.md` (Gap 1 is its incomplete-rollout tail).
- `plans/active/issues/instruments_service_version_phantom_2026_06_11.md` (RESOLVED — the version phantom Gap 1
  amplified).
