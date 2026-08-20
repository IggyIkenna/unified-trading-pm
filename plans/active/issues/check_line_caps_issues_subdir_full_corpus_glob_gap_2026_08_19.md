---
doc_type: issue
title: check_line_caps.sh full-corpus mode never globs plans/active/issues/*.md — sports_all_vendor_honest_coverage_convergence_2026_08_07.md sits 17L over cap, unflagged
summary: >-
  `scripts/plan-hygiene/check_line_caps.sh`'s full-corpus mode target list is
  `plans/active/*.md` + `plans/epics/*.md` — a bash glob that matches only DIRECT children, never
  `plans/active/issues/*.md`. Confirmed live: `plans/active/issues/*.md` has 488 files; zero of them are matched by
  `plans/active/*.md`. SCOPED mode (the prek pre-commit hook) DOES catch issue docs (its directory filter is a
  substring match, `[[ "$f" != *"plans/active/"* ... ]]`, which matches the `issues/` subpath) — so an issue doc is
  only checked at the moment someone stages it, never by the routine hygiene sweep / `/plan-reconcile` Phase-0 input
  gather / CI `plan-health-agent.yml` cron. Found while epic-scoping `/plan-reconcile sports_master`:
  `plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md` is 1017 lines (17 over the
  1000L hard cap) and does not appear anywhere in a full-corpus `check_line_caps.sh --quiet` run's output.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, line-caps, check_line_caps, quality-gate, glob-gap]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
  ]
created: "2026-08-19"
author: plan_reconciler
parent_epic: plan_hygiene_master # was: infrastructure_master (stale slug, folded 2026-08-18; retargeted to plan_hygiene_master, not security_and_cross_cutting_master, since this doc's content — check_line_caps.sh glob coverage — is explicitly plan_hygiene_master-owned scope; corrected cross-epic sweep 2026-08-19)
source: >-
  Found live while running `/plan-reconcile sports_master`'s Phase 0 deterministic inventory
  (`check_line_caps.sh --quiet` full-corpus pass) and cross-checking it against the epic's own child-doc line counts.
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
resolved_by:
archive_exempt:
locked_by:
locked_since:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    scripts/plan-hygiene/check_line_caps.sh,
    plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
  ]
---

# check_line_caps.sh full-corpus mode misses plans/active/issues/\*.md entirely

## What I found

`scripts/plan-hygiene/check_line_caps.sh`'s no-args (full-corpus) branch sets:

```bash
TARGETS=("$PM_DIR/plans/active"/*.md "$PM_DIR/plans/epics"/*.md)
```

A bash glob with no `**`/`shopt -s globstar` matches only files DIRECTLY inside `plans/active/`, never files inside
its `issues/` subdirectory. Verified live (`bash -c 'g=(plans/active/*.md); ... echo count-containing-issues'`):
0 of the glob's matches contain `issues` in the path, while `plans/active/issues/*.md` independently globs to 488
files. **Every one of those 488 issue docs is invisible to the routine full-corpus sweep** — the daily hygiene cron
(`plan-health-agent.yml`), `run_hygiene_sweep.sh --ci`, and every `/plan-reconcile`/`/ag-closeout-audit`/
`/na-eligibility-audit` Phase-0 input-gather that calls this script with no file args.

**SCOPED mode (the prek pre-commit hook, called with the staged file list) DOES catch issue docs** — its directory
filter (`[[ "$f" != *"plans/active/"* && "$f" != *"plans/epics/"* ]] && continue`) is a substring match, and
`plans/active/issues/foo.md` contains the substring `plans/active/`, so it passes the filter. This means an issue
doc's line-cap is enforced ONLY at the moment someone stages it for commit — never by the standing corpus-wide gate.

**Concrete instance found**: `plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md` is
**1017 lines** — 17 over the 1000L hard cap — and does not appear in a full-corpus
`bash scripts/plan-hygiene/check_line_caps.sh --quiet` run's output (confirmed live, 2026-08-19). It has 3 open
todos (not zero-open, so it is not archival-eligible under the zero-open-todo exemption) — a genuine live-plan
over-cap violation sitting outside the baseline ratchet's visibility entirely, meaning it was never counted into
`hard_count` in `line_caps_baseline.yaml` and will never surface as "a regression" even if it grows further, because
the full-corpus scan simply never looks at it.

## Why it matters

- The line-cap gate exists specifically to stop a live coordinator/hub doc from growing into an unreadable mass — an
  issue doc is exactly the shape most prone to this (long-running incident docs accreting Progress Log entries over
  weeks, as this one has: created 2026-08-07, still open, 1017L by 2026-08-19).
- The gap is corpus-wide, not sports-specific — any of the other 487 issue docs could be silently over cap right now
  with nobody the wiser. This finding was discovered incidentally during an epic-scoped `/plan-reconcile sports_master`
  pass and is being filed here rather than fixed inline, since fixing the script correctly requires re-verifying
  SCOPED-mode's own exception logic (marker-append / link-repoint / whitespace-repair / single-todo-flip) still
  behaves correctly once full-corpus mode starts seeing 488 additional files, and re-baselining `hard_count` in
  `line_caps_baseline.yaml` against whatever the true corpus-wide violation count turns out to be — genuinely new
  work, not a same-file mechanical fix this pass should improvise.

## Recommended decision

**A: Fix the full-corpus glob to include `plans/active/issues/*.md`, re-run to get the true violation count, and
re-seed `line_caps_baseline.yaml` accordingly. [WORKER REC]** — closes the blind spot outright; the baseline-ratchet
mechanism already exists precisely to make a bulk-onboarding of newly-visible pre-existing debt safe (it tolerates
the debt without blocking the pipeline, same as the original 2026-07-24 two-tier migration did for `plans/active/`
itself).
**B: Leave issue docs exempt from the full-corpus sweep** (treat them as intentionally unbounded, matching how
`plans/archive/` doc are unbounded) — rejected as the recommendation: unlike an archived record, an OPEN issue doc
with live todos is exactly the kind of doc the cap exists to bound, and SCOPED mode already proves the intent was to
cover it (the prek hook enforces it on stage).

## Todos

- [ ] [SCRIPT] P2. Fix `check_line_caps.sh`'s full-corpus `TARGETS` glob to also include `plans/active/issues/*.md`
      (e.g. add a third glob element or switch to `find`), re-run full-corpus mode to get the true violation count
      across all 488 previously-invisible issue docs, and re-seed `hard_count` in
      `scripts/plan-hygiene/line_caps_baseline.yaml` via `--update-baseline` to match. Done when: a full-corpus run
      lists `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` as a HARD violation and the baseline is
      updated to include it (and any other newly-surfaced issue-doc violations) without silently exceeding the
      shrinking-ratchet contract.
- [ ] [DOC] P3. Once the gate covers it, split or trim
      `plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md` (1017L, 3 open todos) under
      the 1000L cap — operator-gated per the normal split-a-plan rule (not a mechanical fix).

## Progress Log

- **2026-08-19 (`/plan-reconcile sports_master`, epic-scoped run)**: filed. Found while auditing the sports_master
  epic's child docs — `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` (`parent_epic: sports_master`)
  is 1017L and invisible to `check_line_caps.sh`'s full-corpus mode. Confirmed the root cause is a bash-glob
  subdirectory gap (not specific to this doc or this epic) via direct testing. Not fixed in this pass — the script
  fix + rebaseline is genuinely new infra-tranche work, correctly scoped as its own tracked todo rather than an
  improvised inline change during a sports-scoped audit.
- **context-scout 2026-08-20**: refreshed context_scope (2 entries) — the script (fix target) and the concrete
  over-cap instance doc still cover the finding.
