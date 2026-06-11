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

## Composes with

- `codex/08-workflows/ci-cd-flow.md` § "LDR is the SSOT" + § "Two-Pass Workflow Model" + the content-first dep-resolution
  update (2026-06-11).
- `plans/active/ldr_trunk_promotion_decoupling_2026_06_10.md` (Gap 1 is its incomplete-rollout tail).
- `plans/active/issues/instruments_service_version_phantom_2026_06_11.md` (RESOLVED — the version phantom Gap 1 amplified).
