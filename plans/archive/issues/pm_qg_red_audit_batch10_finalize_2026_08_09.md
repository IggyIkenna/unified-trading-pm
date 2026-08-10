---
doc_type: issue
title:
  "PM quality-gates.sh red — 3 pre-existing violations found while shipping ci_satellite_ao_dispatch_batch10_finalize"
summary: >-
  Running PM's full `quality-gates.sh` to satisfy an unrelated finalize-plan todo's done-when surfaced 3 pre-existing,
  unrelated corpus-wide QG regressions (codex-compliance broad-except, plan-commit-sha-evidence citation drift ×2,
  plan-discipline filename convention ×2). All 3 categories fixed + verified in this session; full `quality-gates.sh`
  confirmed green afterward.
status: resolved
resolved_by: unified-trading-pm (this session, slot 12) — see Progress Log
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, plan-hygiene, sha-evidence, citation-drift, filename-convention]
related:
  [
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch10_finalize_2026_08_09.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/issues/quickmerge_setup_bootstrap_loop_blocks_commit_2026_08_09.md,
  ]
created: 2026-08-09
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
source: interactive-session (slot 12)
locked_by:
drift_direction: advance-code
depends_on: []
---

# PM quality-gates.sh red — 3 pre-existing violations found while shipping batch10-finalize

## What I found

While executing `ci_satellite_ao_dispatch_batch10_finalize_2026_08_09.md`'s one todo (a pure plan-checkbox
reconciliation), the todo's own done-when required PM's `bash scripts/quality-gates.sh` to be green. It was RED —
verified pre-existing via stash-and-rerun on clean `origin/live-defi-rollout` HEAD (byte-identical failure with and
without my in-progress edit). Three independent, unrelated categories:

1. **Codex-compliance: broad `except Exception:` ×2** in `scripts/finops/measure_agent_fleet_tokens.py` (lines 54, 65),
   tripping the `CODEX_MAX_VIOLATIONS=0` ceiling for the whole repo. **FIXED this session** — narrowed to
   `json.JSONDecodeError` (guards `json.loads(line)`) and `(ValueError, AttributeError)` (guards
   `datetime.fromisoformat(ts...)` against both a malformed string and a non-string `ts`). Verified via `ast.parse` and
   a subsequent green re-run of this specific gate step.

2. **Plan-commit-sha-evidence: 2 citations, 3 occurrences, do not resolve to real commits in this clone** —
   `check_plan_commit_sha_evidence.py` flagged (baseline 0, found 3):
   - `ci_satellite_ao_dispatch_batch9_2026_08_09.md:99` cited `unified-trading-pm@89925f0c6`.
   - `issues/quickmerge_setup_bootstrap_loop_blocks_commit_2026_08_09.md` cited `unified-trading-pm@a766aabc8d` twice
     (frontmatter `resolved_by:` + a todo).

   **FIXED this session — root cause was citation drift, NOT fabrication or lost work.** For each, I content-matched the
   claimed fix (file(s) touched + commit-message description) against the real `git log` for those exact files and found
   the genuine landed commit:
   - `89925f0c6` → real commit is `a52672b6de` ("docs(plans): repoint 4 stale issue refs in
     qg_host_adaptive_resource_governor") — diff matches exactly (touches
     `ci_satellite_ao_dispatch_batch9_2026_08_09.md`, `issues/plan_reconciler_ci_late_findings_2026_08_06.md`,
     `qg_host_adaptive_resource_governor_2026_07_14.md`). Ancestor-verified against `origin/live-defi-rollout`.
   - `a766aabc8d` → real commit is `c389fe9dce` ("fix(scripts): portable UV_VERSION parse (grep -oP -> sed -E) +
     host-scoped push governor") — commit message + touched-file list (`scripts/setup.sh`, `scripts/quickmerge.sh`,
     `scripts/quality-gates-base/base-library.sh`, `scripts/dev/safe-doc-push.sh`) match the doc's own description
     exactly. Ancestor-verified against `origin/live-defi-rollout`.

   Both corrected citations are now in place in their source docs. Most likely mechanism: the author cited a LOCAL
   pre-push commit SHA that then changed when a `git pull --rebase --autostash` reconciliation (or an equivalent
   quickmerge retry) re-committed the same content under a new hash before it finally reached origin — a rebase always
   mints a new SHA for reapplied content, even unchanged. Distinct from, but adjacent to, the
   `quickmerge_agent_regate_resets_branch_loses_local_commit_2026_07_31.md` failure class: here the content did land,
   just not under the SHA that got written down.

   **Also flipped an adjacent stale todo while in `quickmerge_setup_bootstrap_loop_blocks_commit_2026_08_09.md` fixing
   its SHA citation**: its P2 "Commit the pending finops files" todo was stale — all 3 named files
   (`measure_agent_fleet_tokens.py`, `cloud_spend_forecast_2026_08.py`, `llm_and_research_unit_economics.py`) are
   already tracked, landed together in `unified-trading-pm@0f6087516f` (ancestor-verified).

3. **Plan-discipline: 2 issue-doc filenames don't match `<slug>_YYYY_MM_DD.md`** (baseline 1, found 2 — both pre-date
   this session, confirmed via `git log` showing only prior, unrelated commits touching them). **FIXED this session**:
   - `escalation_root_key_stale_predecessor_chaining_2026_08_09_finalize.md` →
     `escalation_root_key_stale_predecessor_chaining_finalize_2026_08_09.md` (`_finalize` moved before the date,
     matching the established `<slug>_finalize_YYYY_MM_DD.md` convention). One real referrer
     (`escalation_root_key_stale_predecessor_chaining_2026_08_09.md`, a bare-basename prose mention) updated in the same
     pass.
   - `plan_reconciler_findings_2026-08-07.md` → `plan_reconciler_findings_2026_08_07.md` (dashes → underscores). Zero
     other referrers found.
   - Neither file was locked (`locked_by:` empty on both) — safe to rename. `git mv` used in both cases to preserve
     history.

## Why it matters

Categories 1-2 silently blocked `quality-gates.sh` (and therefore the standard Pass-1→Pass-2 quickmerge ship path) for
ANY unrelated commit in this repo, for any worker, until fixed — not just for this session's task. Category 2
specifically means two docs carried **unverifiable "done" evidence** for several hours — exactly what
`check_plan_commit_sha_evidence.py` exists to catch (a citation that can't be verified reads identically to a fabricated
one until someone actually checks) — worth flagging even though both turned out to be genuine, just mis-cited.

## Outcome

All 3 categories fixed and verified in this session. Full `bash scripts/quality-gates.sh --no-fix` re-run afterward
confirmed green (modulo the repo's own pre-existing, separately-baselined `A-deferred-no-banner` plan-discipline debt on
`prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md`, unrelated to this finding and already tracked in
`scripts/quality_gates/plan_discipline_baseline.yaml`).

## Progress Log

- **2026-08-09 (slot 12)** — Filed and fully resolved in the same session, during
  `ci_satellite_ao_dispatch_batch10_finalize_2026_08_09.md` execution. All 3 categories fixed and verified; PM
  `quality-gates.sh` confirmed green afterward. See commits citing this doc for evidence.
