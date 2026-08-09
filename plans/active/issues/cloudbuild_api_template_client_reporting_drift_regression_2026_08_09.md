---
doc_type: issue
title:
  cloudbuild-api-template.yaml forward-port and client-reporting-api's own revert landed in opposite directions minutes
  apart — drift checker RED, blocks unified-trading-pm QG fleet-wide
summary: >-
  Two same-day commits pulled the `quality-gates` Cloud Build step in opposite directions. First,
  `configs/cloudbuild-api-template.yaml` was edited to forward-port client-reporting-api's local `_RUN_INIMAGE_QG` guard
  pattern (comment: "Forward-ported 2026-08-09 from client-reporting-api"). Minutes later,
  `client-reporting-api@b75b798` reverted that exact guard OUT of client-reporting-api's own `cloudbuild.yaml`,
  reasoning it was "accidental drift" and that "nothing in this repo ever sets _RUN_INIMAGE_QG=true, so the guard was
  dead code." Net effect: the template now HAS the guard (+ `set -e`, a `VERSION` var, an echo line, `$$VERSION`-tagged
  docker run); client-reporting-api's own file does NOT. `check_cloudbuild_template_drift.py` fails RED
  (client-reporting-api: 4 markers > baseline 3), blocking `quality-gates.sh`'s post-gate suite for EVERY commit in
  `unified-trading-pm` — the sentinel `quickmerge --agent` ships needs a full-repo green run, so this is not scoped to
  whoever touches cloudbuild files.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, client-reporting-api]
scope: [engineer, admin]
tags: [cicd, cloudbuild, drift, quality-gates, regression]
related: [/plans/archive/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md]
created: 2026-08-09
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: cicd
drift_direction: fix-regression
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found blocking `unified-trading-pm`'s `quality-gates.sh` Pass-1 while shipping an unrelated `scripts/dev/` addition
  (2026-08-09 interactive session, slot 5) — the post-gate `cloudbuild-template-drift` check failed on every run and the
  sentinel `--agent` ship path needs a full green run.
depends_on: []
---

# cloudbuild-api-template.yaml forward-port vs client-reporting-api revert — opposite directions, same day

## What I found

`scripts/quality_gates/check_cloudbuild_template_drift.py` fails deterministically (reproduced 3/3 standalone runs, plus
every `quality-gates.sh` full run):

```
[FAIL] client-reporting-api (cloudbuild-api-template.yaml): 4 drift marker(s) > baseline 3.
New/over-baseline marker(s): step arg dropped: quality-gates::set -e ...
```

Traced both sides of the drift:

1. `unified-trading-pm/configs/cloudbuild-api-template.yaml`'s `quality-gates` step carries a comment:
   `# Forward-ported 2026-08-09 from client-reporting-api (which added this locally without ever forward-porting it here...)`.
   The template's step now includes: the `_RUN_INIMAGE_QG` substitution (default `"false"`), a `set -e`, a `VERSION`
   variable read from `/workspace/VERSION`, an echo line, and a docker run tagged `$$VERSION`.
2. `client-reporting-api@b75b798` ("fix(ci): revert accidental \_RUN_INIMAGE_QG guard drift in client-reporting-api
   quality-gates step", 2026-08-09 09:28:49, slot-32) removed exactly that guard block from client-reporting-api's OWN
   `cloudbuild.yaml` — including the substitution, `set -e`, the `VERSION` var, and the echo — leaving a bare
   unconditional `docker run` tagged `$SHORT_SHA` (not `$$VERSION`). Commit message claims this restores "GREEN
   (client-reporting-api: 3, == baseline)" and that it now matches `configs/cloudbuild-api-template.yaml` exactly — that
   claim is stale: the template had already been (or was concurrently) edited to ADD the same guard the commit was
   removing.
3. Net result: the two commits pulled in opposite directions around the same few minutes. The template now has content
   client-reporting-api's consumer file lacks — the exact "dropped content" class `check_cloudbuild_template_drift.py`
   exists to catch (mirrors, in reverse, the "consumer carries content the template doesn't" case the linked 2026-07-20
   archived issue originally covered).
4. Confirmed this is NOT stale-clone noise: my `client-reporting-api` slot clone is at `origin/live-defi-rollout` HEAD
   (0 ahead/0 behind) and already contains `b75b798`; the failure is 100% reproducible against current committed content
   on both sides, not a race or a dirty working tree.

## Why it matters

- Blocks `quality-gates.sh`'s post-gate suite for `unified-trading-pm` fleet-wide — any agent shipping ANY unrelated
  change via the sanctioned `quickmerge --agent` sentinel path hits this red gate, not just someone touching cloudbuild
  configs. Hit while shipping an unrelated `scripts/dev/` script this session.
- The two commits' stated rationales directly contradict each other on whether the `_RUN_INIMAGE_QG` guard belongs in
  client-reporting-api's build at all — this needs an actual reconciling decision (keep the guard in both template +
  consumer, or drop it from both), not another one-sided edit that just re-flips the same coin.

## Recommended next step

**(a) is correct — evidenced, not a toss-up.** `_RUN_INIMAGE_QG: false` is the established fleet-wide canonical pattern,
decided 2026-06-17 (`plans/archive/2026_06/cloud_build_router_aws_parity_2026_06_10.md`: "In-image QG is **dropped**
(`_RUN_INIMAGE_QG: false` canonical on both clouds, DECISION 2026-06-17)") and already live, consistently, in
`alerting-service`, `execution-service`, `deployment-api`, `market-tick-data-service`, `strategy-service`,
`instruments-service`, `greeks-service`, and `configs/cloudbuild-service-template.yaml` (grepped all
`.tabs/5/*/cloudbuild.yaml` — every one of these repos carries the guard right now). `b75b798`'s "nothing sets it true,
so it's dead code" is true only of client-reporting-api's OWN trigger config today, not of the pattern itself — the
guard exists precisely so a deploy trigger CAN opt in later (per the substitutions comment: "Deploy triggers set
\_RUN_INIMAGE_QG=true to keep the gate on feature/LDR builds"), and every other consumer keeps it dormant-but-present
the same way. Re-add the guard block (+ `set -e` / `VERSION` var / echo / `$$VERSION`-tagged docker run) to
`client-reporting-api/cloudbuild.yaml`'s `quality-gates` step so it matches `configs/cloudbuild-api-template.yaml`
byte-for-byte — this also reverts `b75b798`'s incidental `$SHORT_SHA`→`$$VERSION` tag regression (the template tags
`$$VERSION`, not the raw short SHA, for the same "manual submit may not set SHORT_SHA" reason the build step's own
SAFE_SHA fallback exists).

After the fix, re-verify `check_cloudbuild_template_drift.py` reports `client-reporting-api: 3 (== baseline)`.

## Todos

- [ ] [CICD] P1. **Re-add the `_RUN_INIMAGE_QG` guard to `client-reporting-api/cloudbuild.yaml`'s `quality-gates` step**
      (repo: client-reporting-api) — restore the substitution + `set -e` + `VERSION` var + echo + `$$VERSION`-tagged
      docker run that `b75b798` removed, matching `configs/cloudbuild-api-template.yaml` byte-for-byte (see "Recommended
      next step" above for why (a), not (b), is the right direction). Confirm `check_cloudbuild_template_drift.py`
      reports `client-reporting-api: 3 (== baseline)` afterward, and that `unified-trading-pm`'s `quality-gates.sh`
      cloudbuild-template-drift post-gate is green again (unblocks every other agent's `quickmerge --agent` in this
      repo).

## Codex SSOTs

- `plans/archive/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md` — the original
  drift-checker rationale + baseline mechanics this extends

## Progress Log

- **2026-08-09 (backend_engineer, slot 5)**: Filed while blocked shipping an unrelated `unified-trading-pm` change —
  `quality-gates.sh`'s cloudbuild-template-drift post-gate is deterministically red (3/3 reproductions) due to two
  same-day commits pulling `client-reporting-api`'s `quality-gates` Cloud Build step in opposite directions. Declaring a
  `qg_red` repo-blocker for `unified-trading-pm` per RULES.md § 4b and continuing to wait for this to resolve rather
  than absorbing the reconciliation myself (different repo, different craft scope than this session's assigned task).
