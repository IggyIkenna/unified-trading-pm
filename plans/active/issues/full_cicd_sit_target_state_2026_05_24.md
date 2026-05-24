---
title: "Full CI/CD + SIT target state — close the gaps that let staging drift ~1 month undetected"
created: 2026-05-24
author: ikenna (slot 1)
source:
  - "staging staleness audit + UAC pilot PR #48 (2026-05-24)"
  - "plans/active/issues/staging_resync_post_cutover_2026_05_24.md"
locked_by: live-defi-rollout
---

## What I found (the structural gap)

The 2026-05-24 staging audit exposed that our CI/CD + SIT is **not actually continuous**. Staging drifted ~1 month
behind LDR across all 8 active repos (~5000 commits) and **nobody's pipeline caught it**, because of four compounding
structural holes:

1. **`live-defi-rollout` has NO remote CI.** Per CLAUDE.md "CI Verification": LDR quality is enforced _only_ by local
   `quality-gates.sh`. Hundreds of commits/day land on LDR with zero server-side validation. Whatever a slot didn't run
   locally (or ran in a partial workspace) accumulates silently.
2. **The only real CI gate is the `staging` PR.** `quality-gates` (the SIT) runs when `quickmerge` opens a `→ staging`
   PR. So the _first_ time a month of LDR state meets CI is the staging PR — which then surfaces a month of accumulated
   failures at once (the worst possible time to discover them).
3. **No automated LDR→staging promotion.** It's manual `quickmerge` per repo. During the cutover sprint everyone
   (correctly) pushed direct to LDR and deferred quickmerge → staging froze. There is no cron/bot that catches staging
   up when LDR moves; the operator's mental model ("staging auto-syncs on QG pass") does not match reality.
4. **Cross-repo SIT tests misfire in per-repo CI.** `workspace-qg` renders `dep_repos=""` for foundation repos, so
   per-repo CI checks out only that repo. Tests that validate _cross-repo_ invariants (sibling service dirs in
   `test_feature_dag_ssot`, production cassette consumers in `test_cassette_orphan_checker`, MTDS connector coexistence)
   then fail or false-positive because the siblings/consumers aren't present. We patched these to skip-when-no-siblings
   (UAC@f7627f8e) — but skipping is a workaround: **the cross-repo invariants now run nowhere in CI**, only in local
   full-workspace QG.

Net: we have _per-repo_ CI (good for repo-local lint/type/test) but **no continuous cross-repo SIT and no continuous
integration of the actual integration branch (LDR)**.

## Why it matters

- "Staging is current" is load-bearing for: the disaster-recovery game-day (needs current alerting-service + DART on
  staging), promote-to-paper/live (deploys from staging→main artifacts), and any "test it on staging" request. A
  month-stale staging silently breaks all of these.
- Accumulated-debt-at-promotion is the most expensive failure mode: instead of one bad commit failing one PR, a month of
  commits fail one giant PR with interleaved causes → hard to bisect, high-pressure to bypass.
- Cross-repo contracts (UAC↔consumers, feature-DAG SSOT, cassette↔consumer linkage) are exactly the things that break
  silently across repos — and they're the ones with no continuous gate.

## Target state — full CI/CD with real SIT

### Tier A — per-repo CI (mostly exists; keep)

- `workspace-qg` on every push to `main/staging/live-defi-rollout` (NOT just main/staging). Today LDR has no CI; **add
  LDR to the trigger** so repo-local lint/type/unit/codex run on every LDR push. Fast (no cross-repo checkout).
- Keep `dep_repos` = upstream deps only (build/resolve correctness).

### Tier B — full-workspace SIT job (NEW — the missing layer)

- A scheduled + on-promotion GHA (or Cloud Build) job that **checks out ALL active repos** (topologicalOrder from
  `workspace-manifest.json`) into a workspace layout and runs the **cross-repo invariant suite**: feature-DAG SSOT,
  cassette↔consumer linkage, schema-provenance across repos, IS→MTDS URL contract, batch=live parity,
  incident-gateway↔UAC contract, etc.
- This is where the tests we just guarded (skip-in-per-repo-CI) actually execute. Cadence: nightly + on every staging
  promotion. Owner + verifier + last_executed per the runbook-governance rule.
- Gate: a repo cannot promote to staging if the full-workspace SIT is RED for its layer.

### Tier C — continuous LDR→staging promotion (NEW automation)

- A bot/workflow that, when LDR is green (Tier A) + the full-workspace SIT is green (Tier B), **opens/advances the
  `live-defi-rollout → staging` PR per repo in dependency order** and auto-merges on green. Cadence: e.g. every 4–6h or
  on green-LDR-push, so staging never drifts more than hours.
- Must handle the dep-order cascade (UAC→UTL→instruments→services→APIs→deployment→UI→e2e) + the version-bump cascade
  (semver-agent + `update-dependency-version.yml`).
- Conflict policy: LDR is source-of-truth (staging is downstream); preserve only staging-only semver version bumps.

### Tier D — staging→main + deploy (mostly exists; harden)

- semver-agent staging→main promotion: keep. Audit that non-major auto-promotion is healthy.
- **Service deploy configs**: services that must serve HTTP on staging/prod (e.g. alerting-service safety-ops gateway —
  currently a subscriber with NO Cloud Run service) need a `gcloud run deploy` step + service-account/env/ingress
  config. Today the cloudbuild builds+pushes an image but deploys nothing for some services. Audit every service:
  subscriber-only vs HTTP-served, and add Cloud Run deploy for the HTTP ones.

### Tier E — SIT scenarios as CI (close the loop with the DR work)

- The disaster-recovery game-day scenarios (`e2e-testing/scripts/defi/scenarios/`) + synthetic smokes should run against
  the staging stack on a schedule as part of SIT, with the 7 per-scenario asserts. This makes "21/21 game-day" a
  continuous gate, not a manual operator session.

## Phased plan to get there

1. **Unblock now (tracked in `staging_resync_post_cutover_2026_05_24.md`)**: repair the cross-repo SIT misfires (done
   for UAC; replicate the skip-guard pattern per repo), then cascade the dep-order LDR→staging resync to make staging
   current once.
2. **Tier A**: add `live-defi-rollout` to the `workspace-qg` push trigger (edit PM template `workspace-qg.yml.tmpl` +
   `rollout-workflow-templates.sh`). Cost: more Action minutes on LDR; mitigate with the existing concurrency-cancel.
3. **Tier B**: build the full-workspace SIT job (new reusable workflow in PM that checks out the topologicalOrder set +
   runs the cross-repo suite). Move the guarded tests to require this context.
4. **Tier C**: build the auto-promotion bot (dep-order LDR→staging PRs on green).
5. **Tier D**: per-service deploy-config audit + add Cloud Run deploy for HTTP-served services.
6. **Tier E**: wire game-day + synthetic smokes into the staging SIT schedule.

## Recommended decision

This is an epic-sized infrastructure workstream (belongs under `observability_master` or a new `cicd_master` epic). It
is the structural fix that prevents the next month-of-drift. Sequence it **after** the one-time staging resync (which
makes staging current), so Tier C automation starts from a current baseline.

## Status

- [x] Gap + target state documented
- [x] Tier-B cross-repo-SIT-misfire pattern fixed for UAC (UAC@f7627f8e) — replicate per repo
- [ ] Tier A: add LDR to workspace-qg trigger
- [ ] Tier B: full-workspace SIT job
- [ ] Tier C: auto LDR→staging promotion bot (dep-order)
- [ ] Tier D: per-service Cloud Run deploy-config audit
- [ ] Tier E: game-day + synthetic smokes as staging SIT
