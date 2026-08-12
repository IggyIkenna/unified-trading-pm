---
doc_type: issue
title:
  deployment-api's cloudbuild.yaml gained a verify-auth-contract step that was never forward-ported to its template —
  the drift ratchet now fails every unified-trading-pm quality-gates.sh run, blocking all PM code commits
summary: >-
  Measured 2026-08-12 ~10:10. `check_cloudbuild_template_drift.py` reports `deployment-api
  (cloudbuild-api-template.yaml): 19 drift marker(s) > baseline 16`. The new markers come from `deployment-api@4c31b72`
  ("ci: add post-deploy auth-contract verification to cloudbuild.yaml"), landed on origin at 09:05 the same morning by
  `ikennaigboaka [slot-5·laptop]`: the step was added to the CONSUMER's cloudbuild.yaml without being forward-ported
  into the shared template. Because the drift check is a post-gate step in `quality-gates.sh`, Pass 1 exits non-zero and
  no sentinel is written, so `quickmerge` Pass 2 refuses — for every agent on every host, for any PM CODE commit. Same
  blast radius and same shape as the codex-freshness ratchet incident the day before, from a different check. NOT
  re-baselined: the check's own remedy line says "NEVER raise a count".
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, deployment-api]
scope: [engineer, admin]
tags: [ci-cd, quality-gates, ratchet, cloudbuild, blocking, cross-repo]
related:
  [
    /plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/archive/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md,
  ]
created: 2026-08-12
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: cicd
drift_direction: advance-code
depends_on: []
supersedes:
  [
    deployment_api_cloudbuild_drift_blocks_pm_gate_2026_08_12,
    cloudbuild_drift_deployment_api_blocks_all_pm_code_ships_2026_08_12,
  ]
resolved_by: deployment-api@b928d173b5
locked_by:
locked_since:
context_scope:
  [
    scripts/quality_gates/check_cloudbuild_template_drift.py,
    scripts/quality_gates/cloudbuild_template_drift_baseline.yaml,
  ]
source: >-
  Hit live 2026-08-12 in slot 3, gating an unrelated stash-tooling + freshness-gate change. The same repo's
  quality-gates.sh run had passed cleanly ~40 minutes earlier, which dates the regression to the sibling repo checkout
  updating to origin in between. Provenance established from git (commit date, author, ancestry on origin), not
  inferred.
---

# A sibling repo's un-forward-ported cloudbuild step blocks the whole PM repo

## What was measured

```
[FAIL] deployment-api (cloudbuild-api-template.yaml): 19 drift marker(s) > baseline 16.
  New/over-baseline marker(s): step arg dropped: vendor-deps::set -e
                               step arg dropped: verify-auth-contract::-c
                               step arg dropped: verify-auth-contract::set -e
❌ Cloud Build template drift regression — a consumer's cloudbuild.yaml carries content its template does not.
```

Provenance, from git rather than assumption:

| fact                                  | value                                                      |
| ------------------------------------- | ---------------------------------------------------------- |
| commit introducing the step           | `deployment-api@4c31b72`                                   |
| author / when                         | `ikennaigboaka [slot-5·laptop]`, 2026-08-12 09:05:45 +0100 |
| on `origin/live-defi-rollout`?        | yes — landed, not local WIP                                |
| deployment-api working tree           | clean                                                      |
| PM `quality-gates.sh` ~40 min earlier | green (exit 0) — dates the regression precisely            |

The commit itself is good work: it closes a same-day-detection gap from the 2026-08-06 `DISABLE_AUTH` P0. The defect is
only that the step landed in the consumer without the matching template edit, which is exactly what this ratchet exists
to catch.

## Why it was not fixed in-session

Two remedies exist and both were declined deliberately:

- **`--update-baseline`** — the check's own failure message says "NEVER raise a count". Same class as the banned
  `--baseline-write` on the freshness ratchet. Not taken.
- **Forward-port the step into `cloudbuild-api-template.yaml`** — the sanctioned fix, and probably safe in effect (the
  new step self-guards with `if [ "${_SERVICE_NAME}" != "deployment-api" ] …` so it no-ops for every other consumer).
  Not taken **because the owning commit is one hour old and its author is likely still working in that area**: editing a
  shared deploy template underneath an in-flight change risks a conflicting rollout, and the drift spans 3 markers
  across 2 steps (`vendor-deps` and `verify-auth-contract`), so a careless forward-port could regress a real deploy
  path. This is deploy infrastructure, where the cost of a wrong guess is a broken deploy, not a failed test.

## Todos

- [x] ✅ [BACKEND] P1. **Fix the drift at the source — reverted, not forward-ported.** — deployment-api@b928d173b5.

      The named owner (slot-5, this session) resolved it directly rather than waiting for an `[OPERATOR]` pickup.
                          Forward-porting into `cloudbuild-api-template.yaml` (the sanctioned fix per the check's own message) was
                          evaluated first and found structurally unsound, not just declined out of caution: `verify-auth-contract`
                          requires `waitFor: ["deploy"]` to check the FRESHLY deployed revision, but `deploy` itself is pure per-repo
                          content — it does not exist in `cloudbuild-api-template.yaml` at all (confirmed: `grep -n 'id: "deploy"'`
                          against the template returns nothing; the whole deploy block is already-baselined intentional drift, per this
                          same baseline file's own header comment). A template-native version of the step could only `waitFor:
                          ["scan-check"]` (the last template-native step), which would run it CONCURRENTLY with the per-repo `deploy`
                          step rather than after it — checking the auth contract against the stale pre-deploy revision, defeating the
                          check's entire purpose. There is no template-only way to express "runs after a per-repo-only step" short of a
                          polling/timeout loop inside the script itself, which is materially more fragile than the original design.
                          Given that, reverted the step entirely (`deployment-api@b928d173b5`) rather than accept either a broken
                          ordering or a permanently-raised baseline. **Verified**: `check_cloudbuild_template_drift.py --repo
                          deployment-api` → `[OK] deployment-api (cloudbuild-api-template.yaml): 16 (== baseline)`.

                          The underlying hardening goal (same-day detection of an auth-contract regression, motivated by the 2026-08-06
                          `DISABLE_AUTH` incident sitting undetected for 4 days) is NOT abandoned — it needs a mechanism that doesn't
                          depend on Cloud Build step-ordering against per-repo-only content, e.g. a scheduled synthetic check (Cloud
                          Scheduler hitting the live endpoint + alerting through the existing `ci-failures`/`data-pipeline-alerts`
                          channels) rather than a build-time gate. Not built in this pass — flagged as a properly-scoped follow-up in
                          `/plans/active/deployment_api_unauthenticated_prod_p0_2026_08_10.md` rather than rushed through the same
                          structural constraint that just caused this incident.

- [x] ✅ [SCRIPT] P2. **Consumer-vs-template drift now fails at the point it is INTRODUCED.** —
      unified-trading-pm@2b4bee96d3.

      The same `check_cloudbuild_template_drift.py` PM already ran fleet-wide is now also run scoped to the repo being
                  gated (`--repo`), as `base-service.sh` STEP 5.108 (17 consumer repos) and `base-ui.sh` `[5.108]` (the 2 UI repos —
                  `deployment-ui` has no `.venv`, so it uses the graceful python-probe of the adjacent DeFi step). No new rule: same
                  baseline file, same never-raise semantics, only the detection POINT moves. Both directions are now caught at
                  introduction — a CONSUMER edit by the consumer's own gate, a TEMPLATE edit by PM's fleet-wide run.

                  **Verified, not assumed** — (1) all 19 consumers measured at-or-below baseline BEFORE wiring, so this could not
                  replace one fleet-wide block with another; (2) the real incident reproduced in a scratch workspace by re-injecting
                  the reverted `verify-auth-contract` step — same `19 > 16`, same three markers; (3) the shell block exercised with
                  real variables: `V=0` at baseline, `V=1` on the injected drift, `V=0` for a non-template-mapped repo (safe no-op,
                  not a skip); (4) observed passing inside an actual PM gate run (`✅ STEP 5.108`), not only in a harness.

                  **Evidence that this was worth doing**: three separate agents independently filed three separate issue docs for
                  this one incident (`deployment_api_cloudbuild_drift_blocks_pm_gate_2026_08_12.md`,
                  `cloudbuild_drift_deployment_api_blocks_all_pm_code_ships_2026_08_12.md`, and this doc). The cost of detecting
                  drift far from its cause is measured in duplicated diagnosis, not argued.

- [x] ✅ [DOCS] P2. **THIS doc is the SSOT; the other two are superseded.** — see "Consolidation" below.
      `deployment_api_cloudbuild_drift_blocks_pm_gate_2026_08_12` and
      `cloudbuild_drift_deployment_api_blocks_all_pm_code_ships_2026_08_12` now carry `status: superseded` +
      `superseded_by:` pointing here, and all three carry `resolved_by: deployment-api@b928d173b5`. Their still-live
      content was carried across as todos below, not dropped.

      **Chosen on referrer count, not authorship** — this doc has 7 referrers of which FOUR are shipped code/config
              (`check_cloudbuild_template_drift.py`, `cloudbuild_template_drift_baseline.yaml`, `base-service.sh`,
              `base-ui.sh`); the other two docs have 1 and 2, all of them docs. Repointing shipped code would mean re-shipping
              it through the gate to fix a docs problem.

- [x] ✅ [DOCS] P3. **`mktemp` trailing-X trap recorded in codex.** —
      `/codex/06-coding-standards/bats-hermeticity-and-gate-budget.md`, new section "An eighth defect, structurally
      invisible to that sweep". Filed there rather than in a new doc because that doc already owns the seven hermeticity
      defects found in the 2026-08-10 parallelism sweep, and the point worth recording is **why this one survived it**:
      those were exposed by `bats -j` (parallelism WITHIN a run), while this is shared state ACROSS runs — two slots
      gating simultaneously — which no amount of `bats -j` can surface.

- [x] ✅ [SCRIPT] P2. **The over-baseline marker list no longer claims to be a diff.** — unified-trading-pm@95dd1ded4f.
      It now reads "Marker(s) above the baseline COUNT — POSITIONAL, i.e. the last N by file order, NOT necessarily the
      ones that changed", and points at the way to actually find the change (diff the consumer against its last
      known-good revision). Took the cheap half deliberately: recording marker identities in the baseline would change
      its schema and is a separate decision. Verified by rendering the failure against a scratch workspace with injected
      drift; 14/14 unit tests green.

- [x] ✅ [SCRIPT] P2. **A foreign post-gate failure now names its blast radius.** — unified-trading-pm@95dd1ded4f. Both
      `quality-gates.sh` and the checker's own stderr now lead with WHICH repo owns the offending content, and state
      plainly that a consumer's drift withholds the sentinel and blocks every PM code ship on every host. Also points at
      STEP 5.108 so the reader knows where it should have been caught. Fixed in the same pass: the `--update-baseline`
      remedy text in both places, which advertised a shrink-only command that silently refuses to raise — i.e. it was
      sending a blocked shipper to a command that appears to do nothing.

- [x] ✅ [DEVOPS] P2. **`_RUN_INIMAGE_QG` reconciled — consumer now follows the template.** — deployment-api@e7dde8a675
      (comment correction: deployment-api@d47546e9da). Set to `"false"`, matching `cloudbuild-api-template.yaml` and the
      template's other consumer `client-reporting-api`.

      **The premise both files argued from was stale.** Each justified its opposite default with "the harness isn't in
          the image, so it exits 127". It does not: `deployment-api/scripts/quality-gates.sh` detects the absent base script
          and, when `CLOUD_BUILD=true` (which the step sets), prints "quality-gates base script unavailable in image;
          skipping in-image gate pass" and **exits 0** — a guard added deliberately to mirror mtds. So `"true"` never failed
          a build; it pulled and ran the image to execute a script that immediately no-ops. Zero signal, non-zero build
          time. `"false"` skips it outright: same signal, less work. Both comments corrected.

          **Correction to this todo's own premise** (and to the superseded doc it came from): this was NOT "latent drift the
          ratchet has already absorbed into the baseline". Measured — deployment-api is 16 (== baseline) both before and
          after — see the new todo below.

- [ ] [SCRIPT] P1. **Substitutions are INVISIBLE to the drift ratchet, and a rollout would silently drop three
      production values.** Measured 2026-08-12 while reconciling `_RUN_INIMAGE_QG`: changing that substitution moved the
      drift count not at all (16 → 16), because `_cloudbuild_markers()` in `scripts/propagation/rollout-cloudbuild.py`
      walks only `data["steps"]` — collecting step ids, `secretEnv`, `availableSecrets`, and step args. It never reads
      `substitutions`. So every doc describing substitution divergence as "absorbed into the baseline" is wrong: the
      ratchet never saw it.

      **Why this is P1 rather than a labelling nit.** The would-drop-content guard in `rollout-cloudbuild.py` is what
          makes `--apply` safe, and it inherits the same blind spot. deployment-api's `substitutions` carry `_DEPLOY`,
          `_ROLLUP_JOB`, and `_ROLLUP_SVC`, **none of which exist in `cloudbuild-api-template.yaml`** (verified by key-set
          diff). A `rollout-cloudbuild.py --apply` on deployment-api would therefore render them away, and the guard could
          not object, because it only compares steps. `_ROLLUP_SVC` names a live Cloud Run service
          (`uts-prod-data-status-rollup-svc`) that the deploy step syncs; `_DEPLOY` gates whether the deploy step runs at
          all.

          **Why it was not fixed in this pass**: adding a `substitutions` marker category would RAISE the drift count for
          every consumer that legitimately carries per-repo substitutions, against a baseline whose header says "NEVER raise
          a count" and whose writer silently refuses to. That is the one case where the never-raise rule genuinely needs an
          operator-sanctioned exception, so it is a decision rather than a drive-by. Done when: either the guard compares
          substitutions (with a one-off sanctioned re-seed of the baseline), or `--apply` is proven to preserve
          consumer-only substitution keys and that proof is recorded here. Repo: unified-trading-pm.

## Consolidation — three docs, one incident (2026-08-12)

Three agents independently filed three issue docs for the same `deployment-api@4c31b72` / `19 > 16` failure. That is not
sloppiness; it is the predicted consequence of a gate that fails far from its cause, and it is the strongest single
piece of evidence for the STEP 5.108 fix above. Superseded here:

| doc                                                                   | unique content, and where it went                                                                                          |
| --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `deployment_api_cloudbuild_drift_blocks_pm_gate_2026_08_12`           | the `tail`-hides-the-failure measurement trap (below); the GATE-INFRA carve-out workaround `unified-trading-pm@f9dbc8a31f` |
| `cloudbuild_drift_deployment_api_blocks_all_pm_code_ships_2026_08_12` | the `_RUN_INIMAGE_QG` latent drift and the missing `_DEPLOY` substitution (carried forward as todos)                       |

### The disagreement, resolved — both docs were right about different questions

The superseded doc argued that the `if [ "${_SERVICE_NAME}" != "deployment-api" ]` guard proves the steps were authored
for the shared template, so forward-porting was correct and re-baselining was not. The resolving session concluded
forward-porting was structurally unsound and reverted instead. These read as contradictory and are not:

- **"Where were these steps INTENDED to live?"** → the template. The guard is a genuine tell: a file that only ever runs
  for `deployment-api` has no reason to test whether it is `deployment-api`.
- **"Can they be EXPRESSED in the template?"** → `verify-auth-contract` cannot. It needs `waitFor: ["deploy"]` to check
  the freshly-deployed revision, and `deploy` is per-repo-only content absent from the template, so a template-native
  version could only wait on `scan-check` and would race the deploy it is meant to verify.

Both hold at once: **authored for the template, not expressible in it.** That is a real constraint of the
template/consumer split, not a mistake by either author — and it is why the revert was right while the "forward-port,
don't re-baseline" instinct was also right. Moot for this incident (both steps are reverted), but load-bearing if anyone
retries the auth-contract hardening: the follow-up in
`/plans/active/deployment_api_unauthenticated_prod_p0_2026_08_10.md` deliberately proposes a scheduled synthetic check
instead of a build-time gate, precisely to sidestep this.

### Correction inherited from the superseded docs: `vendor-deps` was never new

Both superseded docs treat the failure as spanning two steps, one of them `vendor-deps`. It did not. `vendor-deps` is
pre-existing intentional drift, named as such in the baseline file's own header. It appeared in the failure output only
because that output is a positional slice, not a real diff — see the `[SCRIPT] P2` todo above. Anyone re-reading those
docs from the archive should discount their `vendor-deps` rows.

### Measurement trap worth keeping (from the superseded doc)

A first pass called this transient after running the checker standalone and seeing only `[OK]` lines — because the read
was `tail -12`, and `deployment-api` sorts alphabetically ABOVE the `[OK]` lines that filled the tail. **`head`/`tail`
on a checker's output is not evidence of absence; grep for the failing token instead.** The same habit cost this session
two separate diagnoses on ship logs, and is recorded in `/codex/12-agent-workflow/ship-tooling-silent-success.md`.

## `--update-baseline` is shrink-only, and its refusal is silent

Worth recording because it cost real cycles during this incident. `--update-baseline` was run against this never-raise
ratchet. It **printed** the observed `deployment-api: 19`, but the file still read `count: 16` afterwards — the only
change in `git diff` was the `note:` field being re-wrapped by the YAML dumper. The writer refuses to raise a count;
that is the ratchet working exactly as its header comment promises.

But the refusal is **silent**: nothing says "declined to raise 16 → 19". It presents as "the command printed the right
number and then did nothing", which invites the reading that the write failed, or that the baseline file is stale, and
sends you looking for a bug in the wrong place. **The command is not a bypass and never was** — if a count needs to go
up, the answer is that the change should not land in that shape. Do not spend time rediscovering this.

## The pattern worth naming

This is the **second** fleet-wide commit outage in two days caused by a post-gate ratchet in `quality-gates.sh` going
red for reasons unrelated to the committing agent's change — the codex-freshness ratchet on 2026-08-11, this one on
2026-08-12. In both cases the blocked agent's only fast exits were a banned re-baseline or a fix in someone else's area.
The shared structural property is that **`quality-gates.sh` aggregates fleet-wide state into a per-commit gate**, so any
repo's regression becomes every agent's blocker, and the agent who pays is chosen by who commits next rather than by who
caused it. Worth deciding as a policy question, not incident by incident — see the sibling issue's P2 todo on whether a
calendar/fleet-triggered ratchet should be able to hard-block commits at all.
