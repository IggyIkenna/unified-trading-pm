---
doc_type: issue
title: unified-trading-ci `lint` (actionlint) job is RED — 30 pre-existing shellcheck findings across 3 workflow files
summary: >-
  Discovered while shipping the content-sentinel dependency-content-aware fix
  (uac_value_only_config_change_breaks_utl_untested_2026_07_20.md item [A]): unified-trading-ci's `lint.yml`
  (actionlint) job fails on push to `main` with 30 shellcheck info/style/warning findings in semver-agent.yml,
  update-dependency-version.yml, and request-major-bump.yml — none in the file this task touched
  (python-quality-gates-v2.yml). Confirmed PRE-EXISTING: identical 30-finding count on the commit immediately prior to
  this task's push, byte-for-byte same signature.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-ci]
scope: [engineer, admin]
tags: [ci-cd, lint, shellcheck, actionlint, pre-existing]
related:
  [
    /plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-09
author: worker-slot18
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: cicd
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
source: ["discovered 2026-08-09 while shipping uac_value_only_config_change_breaks_utl_untested_2026_07_20.md item [A]"]
---

# unified-trading-ci `lint` job is red on pre-existing shellcheck findings

## What I found

`unified-trading-ci`'s only CI gate (`.github/workflows/lint.yml`, actionlint) fails on every push to `main` — verified
on run `31311558496` (this task's own push, sha `f0bfaa2`) and the immediately prior run `31307694125` (sha `2c48c4b`,
unrelated commit): both report the exact same 30 shellcheck findings (a mix of `info`/`style`/`warning` severity —
`SC2015`, `SC2034`, `SC2129`, `SC2086`), all in `.github/workflows/semver-agent.yml`,
`.github/workflows/update-dependency-version.yml`, and `.github/workflows/request-major-bump.yml`. None reference
`python-quality-gates-v2.yml`, the file this task edited — my change is clean (verified locally with the cached
`actionlint` binary before pushing, and confirmed no new findings landed in the live run).

This repo has `main` as its only branch (no LDR/staging tiers — see its README), and `lint.yml` is not wired as a
required branch-protection check, so this red does not currently block anyone from pushing — it just means the "lint"
check has read red since at least the 2026-08-06 workflow-hosting migration that moved these files here (per their
recent git history, all three were touched during that extraction).

## Why it matters

Low urgency (shellcheck `info`/`style` findings, not correctness bugs), but a permanently-red required CI check on this
repo's only automated gate erodes its signal value — a future REAL actionlint/ shellcheck regression in these files
would be invisible against this pre-existing red.

## Recommended decision

Fix the 30 shellcheck findings (mostly mechanical: `A && B || C` → real if/then/else, unused-var removal, redirect
consolidation, missing quotes) across the three named files so `lint.yml` goes green, or add scoped
`# shellcheck disable=` pragmas if any are intentional.

## Todos

- [x] [DEVOPS] P3. Fix shellcheck findings in `unified-trading-ci/.github/workflows/semver-agent.yml` (7 findings —
      SC2015 ×4, SC2034, SC2129 ×2) so the `lint` actionlint job goes green. ✅ unified-trading-ci@a12e147 — actual live
      finding count was 9, not 7 (SC2015 ×4, SC2034 ×1, SC2129 ×2, plus an SC2086 the filing session's count missed): 4×
      `A && echo ... || true` → real `if`/`then`/`fi` (Slack best-effort-post-then-log pattern); the unused
      `CHANGED_FILES` var (computed, never read — `DIFF_BASE` is the value actually consumed) removed entirely rather
      than exported/suppressed; 2× consecutive `GITHUB_OUTPUT` redirects grouped into `{ ...; } >> file`; the unquoted
      `$SCHEMA_FILES` word-split into `git diff`'s pathspec args converted to a `mapfile` bash array so each path is a
      properly-quoted arg. Verified: downloaded actionlint v1.7.12 locally, 0 findings in this file before push,
      confirmed 0 findings in this file in the LIVE CI run after push (`gh run view 31339579198 --log-failed` — zero
      `semver-agent.yml` mentions in the 21 remaining findings), YAML re-parses cleanly.
- [x] [DEVOPS] P3. Fix shellcheck findings in `unified-trading-ci/.github/workflows/update-dependency-version.yml`
      (actual live count 2026-08-09: 4 findings, matches this todo's original count — SC2129 ×3, SC2015) so the `lint`
      actionlint job goes green. ✅ unified-trading-ci@6105330 — 3× SC2129 (two 5-line + one 3-line consecutive
      `GITHUB_OUTPUT` redirect blocks) grouped into `{ ...; } >> "$GITHUB_OUTPUT"`; 1× SC2015 (`notify-failure`'s Slack
      best-effort `A && B || C`) converted to a real `if`/`then`/`fi`, same pattern as the semver-agent.yml fix.
      Verified: actionlint 0 findings in this file after (was 4), YAML re-parses, whole-repo run confirms the remaining
      17 findings are unrelated (request-major-bump.yml, major-bump-issue-handler.yml — todos 2 and 3).
- [x] ✅ [DEVOPS] P3. Fix shellcheck findings in `unified-trading-ci/.github/workflows/request-major-bump.yml` (**actual
      live count 2026-08-09: 14 findings, not the 1 originally logged** — this todo's original count was
      stale/undercounted, same class of drift as the semver-agent.yml todo above) so the `lint` actionlint job goes
      green. — unified-trading-ci@14be063 (see Progress Log for detail).
- [ ] [DEVOPS] P3. Fix shellcheck findings in `unified-trading-ci/.github/workflows/major-bump-issue-handler.yml` (3
      findings, live count 2026-08-09) — a 4th file with findings not covered by any of this doc's original 3 todos,
      discovered while verifying the semver-agent.yml fix against a live `lint` run
      (`gh run view --repo IggyIkenna/unified-trading-ci --log-failed`, run 31339579198). Same fix class as the other 3
      todos, so the `lint` actionlint job goes green.

## Progress Log

- **2026-08-09** — Filed while shipping `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` item [A]
  (content-sentinel dependency-content-aware fix). Confirmed the red is pre-existing and unrelated to that change
  (identical failure signature before/after).
- **2026-08-09 (slot-15, cicd)**: Closed todo 1 (semver-agent.yml) — unified-trading-ci@a12e147, direct push to `main`
  (single-branch repo, no PR requirement — confirmed via `gh api .../branches/main/protection`, no
  `required_pull_request_reviews`). Discovered while verifying against a live CI run that this doc's finding counts were
  stale for 2 of the other 3 items: request-major-bump.yml is actually 14 findings (not 1), and a 4th untracked file
  (major-bump-issue-handler.yml, 3 findings) also has pre-existing shellcheck red — added as a new todo per the
  findings-closure rule rather than silently expanding scope inline. update-dependency-version.yml's original count (4)
  was accurate. Did not attempt todos 2-4 (different files, out of this task's own dispatched scope — brief was
  specifically the semver-agent.yml todo).
- **2026-08-09 (slot-15, cicd)**: Closed todo 2 (update-dependency-version.yml) — unified-trading-ci@6105330, pushed to
  both `live-defi-rollout` and `main` (kept the two branches in sync; this repo's `lint.yml` only fires on push to
  `main`). Todos 3-4 (request-major-bump.yml, major-bump-issue-handler.yml) remain — different files, out of this task's
  own dispatched scope.
- **2026-08-10 (cicd worker, slot 4)**: Closed todo 3 (request-major-bump.yml) — unified-trading-ci@14be063, pushed to
  both `main` and `live-defi-rollout` (same sync pattern as todo 2). Session died mid-task after the first two of three
  fixes were staged but uncommitted; the orchestrator's dirty-state gate auto-preserved that partial WIP to
  `wip-preserve/orchestrator-slot-4-3dd2656` on respawn — re-verified it matched, then re-applied all 3 fixes fresh
  (superset of the preserved partial WIP) rather than merging the stale branch. Live count confirmed 14, matching the
  doc's already-corrected count: 1× SC2129 (Validate step, 4 consecutive `GITHUB_OUTPUT` redirects grouped into
  `{ ...; } >> "$GITHUB_OUTPUT"`), 11× SC2086 + 1× SC2129 (Summary step, `$GITHUB_STEP_SUMMARY` quoted + 11 redirects
  grouped), 1× SC2015 (notify-failure Slack alert, `curl && echo || true` converted to real `if`/`then`/`fi`, same
  pattern as the semver-agent.yml/update-dependency-version.yml fixes). Verified: downloaded actionlint v1.7.12 locally,
  0 findings in this file after (was 14); whole-repo run confirms remaining 3 findings are all in
  major-bump-issue-handler.yml (todo 4, out of scope); confirmed live in CI too (`gh run view 31346582234 --log-failed`
  on `main` HEAD `14be063` — zero `request-major-bump.yml` mentions in the failed-check log, only
  `major-bump-issue-handler.yml`). Todo 4 remains open — different file, out of this task's own dispatched scope.
