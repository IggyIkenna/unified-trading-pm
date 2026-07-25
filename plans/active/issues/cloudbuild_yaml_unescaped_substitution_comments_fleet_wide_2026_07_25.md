---
doc_type: issue
title:
  "cloudbuild.yaml comment-only single-dollar substitution references (VERSION/BASE_IMAGE_DIGEST) trip Cloud Build's
  substitution validator — confirmed blocks manual gcloud builds triggers run, 15 repos affected"
summary: >-
  While completing `utl_prod_cloud_build_trigger_missing_fleet_stale_base_image_2026_07_25.md`'s todo 2 (manually verify
  the recreated `unified-trading-library-prod` trigger), `gcloud builds triggers run unified-trading-library-prod
  --branch=main` failed with `INVALID_ARGUMENT: key in the template "VERSION" is not a valid built-in substitution`.
  Root-caused: Cloud Build's substitution validator statically scans the RAW YAML string content of every build step —
  including comment lines (`#`) inside multi-line bash heredoc blocks — for `$KEY` patterns. Bash never touches text
  inside a `#` comment, but Cloud Build's own pre-processor does not distinguish "live code" from "comment" within a
  step's string value; an unescaped single-`$` reference anywhere is treated as an undeclared substitution and fails
  validation, UNLESS it is a genuine Cloud Build built-in (`$PROJECT_ID`/`$BUILD_ID`/`$COMMIT_SHA`/etc.) or a declared
  custom substitution (always `_`-prefixed, e.g. `$_SERVICE_NAME`). Fixed unified-trading-library (`@44922ad1` +
  `@71dcf0f4`, 5 occurrences of bare `$VERSION`/ `$IMAGE_TAG`). A fleet-wide grep for the SAME pattern (bare,
  non-builtin, non-underscore, undeclared single-`$` reference anywhere in a repo's `cloudbuild.yaml`) found the
  IDENTICAL bug in **15 more repos** — same root cause (a shared cloudbuild.yaml authoring convention across the fleet
  uses `$VERSION` as a plain bash-script local variable in both code AND comments, and comments were never escaped).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    deployment-api,
    deployment-service,
    execution-service,
    features-service,
    fund-administration-service,
    greeks-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    ml-service,
    strategy-service,
    trading-agent-service,
  ]
scope: [engineer, admin]
tags: [ci, cloudbuild, gcp, substitution, fleet, infra, p1]
related: [/plans/active/issues/utl_prod_cloud_build_trigger_missing_fleet_stale_base_image_2026_07_25.md]
created: 2026-07-25
parent_epic: infrastructure_master
priority: P1
source:
  "Found 2026-07-25 (slot 2, infra) while verifying the recreated unified-trading-library-prod Cloud Build trigger —
  fixed UTL's own instance, then ran a fleet-wide grep for the same pattern and found 15 more repos with it."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# cloudbuild.yaml comment-only unescaped substitutions — fleet-wide, 15 repos

## What I found

Confirmed live:
`gcloud builds triggers run unified-trading-library-prod --project central-element-323112 --region=asia-northeast1 --branch=main`
failed twice with `INVALID_ARGUMENT: key in the template "VERSION" is not a valid built-in substitution` before the fix
(`unified-trading-library@44922ad1` + follow-up `@71dcf0f4` — the first commit's own shipping hit a git-stash-pop
conflict that partially reverted one of the five escapes; caught + fixed on the second commit). Root cause: Cloud
Build's static substitution validator scans the ENTIRE raw string value of every build step — the multi-line bash
`args: - "-c" - | ...` blocks are YAML string scalars, and Cloud Build's parser walks that whole string for `$KEY`
tokens BEFORE bash ever executes it, so a `#`-comment mention of `$VERSION` (never touched by bash) is indistinguishable
to Cloud Build from a real substitution reference. `$$VERSION` (escaped) is correctly ignored; `$VERSION` (bare, single
`$`) is not.

**Fleet-wide grep** (repo-relative to `.tabs/2/`, single-pass over every `*/cloudbuild.yaml`, excluding Cloud Build
built-ins `PROJECT_ID`/`BUILD_ID`/`PROJECT_NUMBER`/`LOCATION`/`TRIGGER_NAME`/`BRANCH_NAME`/`TAG_NAME`/`REVISION_ID`/
`COMMIT_SHA`/`SHORT_SHA`/`REPO_NAME`/`REPO_FULL_NAME`/`TRIGGER_BUILD_CONFIG_PATH`, and every repo's own DECLARED
`_`-prefixed custom substitutions) found the identical bare-`$` pattern in:

| Repo                              | Variable                         | Line(s)  |
| --------------------------------- | -------------------------------- | -------- |
| agent-orchestrator                | `$VERSION`                       | 150      |
| alerting-service                  | `$VERSION`                       | 269      |
| batch-live-reconciliation-service | `$VERSION`                       | 94, 261  |
| deployment-api                    | `$BASE_IMAGE_DIGEST`             | 201      |
| deployment-service                | `$BASE_IMAGE_DIGEST`             | 80       |
| execution-service                 | `$VERSION`                       | 278      |
| features-service                  | `$VERSION`                       | 94, 270  |
| fund-administration-service       | `$VERSION`                       | 238      |
| greeks-service                    | `$VERSION`                       | 259      |
| instruments-service               | `$VERSION`                       | 74, 243  |
| market-data-processing-service    | `$VERSION`                       | 237      |
| market-tick-data-service          | `$BASE_IMAGE_DIGEST`, `$VERSION` | 108, 309 |
| ml-service                        | `$VERSION`                       | 94, 261  |
| strategy-service                  | `$VERSION`                       | 308      |
| trading-agent-service             | `$VERSION`                       | 94, 262  |

Every occurrence spot-checked (agent-orchestrator:150, execution-service:278, deployment-api:201) is comment-only, same
as the UTL case — none is a real code reference (those all correctly use `$$VERSION`/`$$BASE_IMAGE_DIGEST` already,
matching the established double-`$` bash-escaping convention elsewhere in the same files).

## Why this wasn't independently confirmed for each repo

**Not verified whether this also breaks real webhook/push-triggered builds** (the only reproduction in this session was
a MANUAL `gcloud builds triggers run --branch=main` invocation against `unified-trading-library-prod`) — it is possible
Cloud Build validates substitutions more strictly on an explicit `triggers run` call (which synthesizes a push event +
explicit substitutions map) than on a real GitHub-webhook-driven push (which may resolve differently). Given every one
of these 15 repos is a live, currently-deploying service, if this bug blocked real push-triggered builds too, it would
already be a fleet-wide outage as loud as the UTL one — which has not been reported. **Do not assume** either way; the
next step for whoever picks this up is confirming via `gh run list` / Cloud Build history whether any of these repos'
`-prod` triggers have recently failed with the identical `NOT_FOUND`/`INVALID_ARGUMENT` substitution message, OR whether
push-triggered builds genuinely tolerate what manual runs reject.

## Recommended fix

Mechanical, one-line-per-occurrence, identical pattern to the UTL fix: escape every comment-only bare `$VERSION`/
`$BASE_IMAGE_DIGEST` (and re-scan for any OTHER bare non-builtin, non-underscore, undeclared `$NAME` while in each file,
the same way the UTL exhaustive re-scan caught one instance the first patch pass missed) to `$$VERSION`/
`$$BASE_IMAGE_DIGEST`, matching every other reference in the same files. Verify per-repo via:

```python
import re
builtins = {'PROJECT_ID','BUILD_ID','PROJECT_NUMBER','LOCATION','TRIGGER_NAME','BRANCH_NAME','TAG_NAME',
'REVISION_ID','COMMIT_SHA','SHORT_SHA','REPO_NAME','REPO_FULL_NAME','TRIGGER_BUILD_CONFIG_PATH'}
declared = set(re.findall(r'^\s{2}(_[A-Za-z0-9_]+):', content, re.M))
bad = [m.group(2) for m in re.finditer(r'(?<!\$)\$(\{)?([A-Za-z_][A-Za-z0-9_]*)', content)
       if m.group(2) not in builtins and m.group(2) not in declared and not m.group(2).startswith('_')]
# bad must be empty
```

Ship each repo's fix via that repo's own quickmerge two-pass (quality-gates.sh → quickmerge --agent), same as the UTL
fix. No behavior change to the actual build (bash never executed these comments) — pure YAML-string escaping.

## Todos

- [x] ✅ [INFRA] P1. Fix `agent-orchestrator/cloudbuild.yaml` line 150 (bare `$VERSION` in comment → `$$VERSION`) + run
      the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo: agent-orchestrator) —
      agent-orchestrator@d421635, exhaustive re-scan confirmed zero remaining bare substitutions.
- [x] ✅ [INFRA] P1. Fix `alerting-service/cloudbuild.yaml` line 269 (bare `$VERSION` in comment → `$$VERSION`) + run
      the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo: alerting-service) —
      alerting-service@0c7c42d, exhaustive re-scan confirmed zero remaining bare substitutions.
- [x] ✅ [INFRA] P1. Fix `batch-live-reconciliation-service/cloudbuild.yaml` lines 94, 261 (bare `$VERSION` in comments
      → `$$VERSION`) + run the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo:
      batch-live-reconciliation-service) — batch-live-reconciliation-service@d7c76fb, exhaustive re-scan (the same
      builtins/declared-substitution-aware regex from this doc's Recommended fix) confirmed zero remaining bad
      substitutions; `quality-gates.sh` green (155s).
- [x] ✅ [INFRA] P1. Fix `deployment-api/cloudbuild.yaml` line 201 (bare `$BASE_IMAGE_DIGEST` in comment →
      `$$BASE_IMAGE_DIGEST`) + run the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo:
      deployment-api) — deployment-api@0badf57, exhaustive re-scan confirmed zero remaining bare substitutions.
- [x] ✅ [INFRA] P1. Fix `deployment-service/cloudbuild.yaml` line 80 (bare `$BASE_IMAGE_DIGEST` in comment →
      `$$BASE_IMAGE_DIGEST`) + run the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo:
      deployment-service) — deployment-service@cee6a71, exhaustive re-scan confirmed zero remaining bare substitutions.
- [x] ✅ [INFRA] P1. Fix `execution-service/cloudbuild.yaml` line 278 (bare `$VERSION` in comment → `$$VERSION`) + run
      the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo: execution-service) —
      execution-service@6ae9c71b, exhaustive re-scan confirmed zero remaining bare substitutions.
- [ ] [INFRA] P1. Fix `features-service/cloudbuild.yaml` lines 94, 270 (bare `$VERSION` in comments → `$$VERSION`) + run
      the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo: features-service)
- [x] ✅ [INFRA] P1. Fix `fund-administration-service/cloudbuild.yaml` line 238 (bare `$VERSION` in comment →
      `$$VERSION`) + run the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo:
      fund-administration-service) — fund-administration-service@b62d896, exhaustive re-scan confirmed zero remaining
      bad substitutions; `quality-gates.sh` green (97s).
- [x] ✅ [INFRA] P1. Fix `greeks-service/cloudbuild.yaml` line 259 (bare `$VERSION` in comment → `$$VERSION`) + run the
      exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo: greeks-service) —
      greeks-service@081ad53, exhaustive re-scan confirmed zero remaining bare substitutions.
- [x] ✅ [INFRA] P1. Fix `instruments-service/cloudbuild.yaml` lines 74, 243 (bare `$VERSION` in comments →
      `$$VERSION`) + run the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo:
      instruments-service) — instruments-service@ea239573, exhaustive re-scan (builtins/declared-substitution-aware
      regex from this doc's Recommended fix) confirmed zero remaining bad substitutions; `quality-gates.sh` green
      (196s).
- [x] ✅ [INFRA] P1. Fix `market-data-processing-service/cloudbuild.yaml` line 237 (bare `$VERSION` in comment →
      `$$VERSION`) + run the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo:
      market-data-processing-service) — market-data-processing-service@be66050, exhaustive re-scan confirmed zero
      remaining bad substitutions; `quality-gates.sh` green (90s).
- [ ] [INFRA] P1. Fix `market-tick-data-service/cloudbuild.yaml` lines 108 (`$BASE_IMAGE_DIGEST`), 309 (`$VERSION`) in
      comments → double-escaped + run the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge.
      (repo: market-tick-data-service)
- [x] ✅ [INFRA] P1. Fix `ml-service/cloudbuild.yaml` lines 94, 261 (bare `$VERSION` in comments → `$$VERSION`) + run
      the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo: ml-service) —
      ml-service@1257161, exhaustive re-scan confirmed zero remaining bare substitutions.
- [x] ✅ [INFRA] P1. Fix `strategy-service/cloudbuild.yaml` line 308 (bare `$VERSION` in comment → `$$VERSION`) + run
      the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo: strategy-service) —
      strategy-service@0616a141, exhaustive re-scan confirmed zero remaining bad substitutions; `quality-gates.sh`'s own
      STEP 5.19 ("cloudbuild.yaml substitutions OK") independently confirmed the fix; green (190s).
- [x] ✅ [INFRA] P1. Fix `trading-agent-service/cloudbuild.yaml` lines 94, 262 (bare `$VERSION` in comments →
      `$$VERSION`) + run the exhaustive re-scan above to confirm zero remaining. Ship via quickmerge. (repo:
      trading-agent-service) — trading-agent-service@b0436ce, exhaustive re-scan (builtins/declared-substitution-aware
      regex from this doc's Recommended fix) confirmed zero remaining bad substitutions; `quality-gates.sh` green
      (112s).
- [ ] [INFRA] P2. Determine whether this bug class also blocks real webhook/push-triggered builds (not just manual
      `gcloud builds triggers run`) for any of the 15 repos above — check each repo's recent Cloud Build history /
      `cloud-build-router.yml` run logs for a `NOT_FOUND`/`INVALID_ARGUMENT`/"not a valid built-in substitution"
      failure. If any repo's real push-triggered builds ARE affected, that repo's base/service image may be silently
      stale exactly like unified-trading-library was — escalate to the operator immediately per the data-pipeline/
      infra-correctness HARD RULE (this would be a live, currently-silent outage, not a latent one). (repo:
      cross-cutting investigation, no single owning repo)

## Codex SSOTs

No existing SSOT covers Cloud Build comment-substitution escaping specifically. If this recurs after the fix (a new
`cloudbuild.yaml` edit reintroduces a bare `$NAME`), consider a QG check mirroring the exhaustive-rescan snippet above —
out of scope for this doc, flagging as a possible follow-up, not a todo here.
