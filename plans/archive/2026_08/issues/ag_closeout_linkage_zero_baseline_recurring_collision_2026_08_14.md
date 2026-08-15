---
doc_type: issue
title: >-
  check_ag_closeout_linkage.py — zero-tolerance baseline keeps tripping on ordinary concurrent AO-batch archival (3rd
  distinct incident)
summary: >-
  `check_ag_closeout_linkage.py`'s baseline reached `orphan_count: 0` on 2026-08-10 (commit `0a2b761511`, "38->0,
  baseline ratcheted 49->0") and has held at 0 since. On 2026-08-14 (during a `/ci-reconcile` sweep) it failed live CI
  for `unified-trading-pm`@`db8633402c` — 5 orphans (`ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md`,
  `batch8_finalize_2026_08_08.md`, `batch9_2026_08_08.md`, `batch9_finalize_2026_08_08.md`, +1 already cleared by a
  later commit before this doc was written). Root cause: this is a **whole-corpus SCALAR ratchet** (§ classification (g)
  in `/cursor-configs/skills/ci-reconcile/SKILL.md`) — at baseline 0, ANY single doc that lands without a
  `related:`/body-mention link back to its tranche's `<prefix>_consolidated_*` family fails the NEXT unrelated commit's
  CI run, not the commit that actually created the gap. `unified-trading-pm` ships via quickmerge at high concurrent
  velocity (multiple slot sessions archiving/creating `ao`-tranche batch docs the same day — this incident's 4 docs
  spanned batch5/8/9, authored across several sessions on 2026-08-03/08-08), so each individual commit's own local
  `quality-gates.sh` run only ever sees its own snapshot and never trips — the corpus-wide CI run on a LATER, unrelated
  commit is the first point anything crosses zero. Fixed THIS incident's 4 docs by adding a `related:` edge to
  `/plans/active/ao_consolidated_closeout_2026_08_12.md` in each (verified `check_ag_closeout_linkage.py` returns `0
  orphan(s)` after) — shipped `unified-trading-pm@87191cc7c7`.

  This is the SAME failure shape as
  `/plans/archive/2026_08/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md` (measured drift between
  ratchet-seed time and audit time) and
  `/plans/archive/2026_08/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md` (a structural gate gap)
  — three independent incidents on the same checker in under 3 weeks, the first two both closed by re-measuring/
  widening rather than changing the check's SHAPE. At non-zero baseline the gap could go unnoticed for days (87 vs 69);
  at baseline 0 it now fires within hours of any concurrent-archival collision, which will keep recurring at the current
  `ao`/`sports`/`defi`/etc. batch-dispatch cadence.
status: resolved
resolved_by: slot-24, 2026-08-15
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, ag-closeout-audit, quality-gates, linkage, orphan-detection, ratchet, ci-reconcile]
related:
  [
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md,
    /plans/archive/2026_08/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /cursor-configs/skills/ci-reconcile/SKILL.md,
    /scripts/plan-hygiene/check_ag_closeout_linkage.py,
    /scripts/plan-hygiene/ag_closeout_linkage_baseline.yaml,
  ]
created: "2026-08-14"
last_updated: "2026-08-14"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /scripts/plan-hygiene/check_ag_closeout_linkage.py,
    /scripts/plan-hygiene/check_terminal_status_archived.py,
    /codex/06-coding-standards/quality-gates.md,
  ]
source: >-
  Found live during a `/ci-reconcile` fleet sweep (2026-08-14) triggered by operator-forwarded `#ci-failures` Slack
  alerts — `python-quality-gates-v2` FAILED on `unified-trading-pm` push to `live-defi-rollout` sha `db8633402c`.
---

# ag-closeout-linkage — zero-baseline recurring collision

> **🟢 ARCHIVED 2026-08-15 — RESOLVED.** Both todos done. Todo 2 (`--only`/`--diff-base` diff-scoped modes + wiring into
> `run_hygiene_sweep.sh`'s precommit/CI-gate paths) was already shipped pre-existing on disk
> (`unified-trading-pm@96b33046f9` et al.) — closed out by adding the missing regression coverage
> (`test_check_ag_closeout_linkage.py::test_diff_base_does_not_flag_a_pre_existing_orphan_from_an_earlier_commit`
>
> - `::test_diff_base_flags_an_orphan_this_commit_itself_introduced`), confirming the corpus-wide baseline mode remains
>   as the periodic/audit-scope check (`run_hygiene_sweep.sh` full-sweep + `--diff-base` CI-gate path, unchanged).

## Todos

- [x] [SCRIPT] P2. **Fix this incident's 4 live orphans** — add a `related:` edge from each of
      `ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md`, `batch8_finalize_2026_08_08.md`, `batch9_2026_08_08.md`,
      `batch9_finalize_2026_08_08.md` to `/plans/active/ao_consolidated_closeout_2026_08_12.md`. **Done when**:
      `python3 scripts/plan-hygiene/check_ag_closeout_linkage.py` returns `0 orphan(s) (baseline 0)`. **DONE
      2026-08-14** — verified locally then shipped `unified-trading-pm@87191cc7c7` via quickmerge.
- [x] [SCRIPT] P2. **Convert `check_ag_closeout_linkage.py` to a diff-scoped/attributed check**, mirroring the pattern
      already used for `check_terminal_status_archived.py --only` / `check_finalize_plan_coverage.py --only` and the 6
      checks migrated 2026-08-09 (per `/cursor-configs/skills/ci-reconcile/SKILL.md` § classification (f)/(g)): only
      fail a commit/PR if the docs it ITSELF touches are newly-orphaned relative to the diff base, not the whole
      corpus's current total. This removes the "whichever unrelated commit happens to land next after the collision"
      false-attribution and stops the zero-baseline hair-trigger recurring on ordinary same-day multi-slot batch
      archival — the exact failure mode this doc, `ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md`, and
      `ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md` all independently hit. **Done when**: the script
      gains a `--only <staged-files>` (or equivalent diff-base) mode wired into the fast/precommit path per the existing
      pattern, a regression test proves a same-day multi-commit archival race no longer trips an unrelated commit, and
      `run_hygiene_sweep.sh`'s full-corpus mode is kept as the periodic/audit-scope check (not removed — still useful
      for catching drift between audits). **DONE 2026-08-15** — `--only` (2026-08-09) and `--diff-base` (2026-08-14,
      `unified-trading-pm@96b33046f9`) were already shipped and wired into `run_hygiene_sweep.sh` (lines ~300 precommit
      `--only`, ~488 CI-gate `--diff-base` via `DIFF_BASE_REF`/`AGCLOSEOUT_DIFF_ARGS`) prior to this todo being picked
      up; the corpus-wide baseline mode (`main()`'s default path) is unchanged and still runs as the fallback/periodic
      check. Closed the one remaining gap — no regression test proved the diff-scoped mode actually stops the collision
      — by adding `test_diff_base_does_not_flag_a_pre_existing_orphan_from_an_earlier_commit` (asserts a doc already
      orphaned at the base ref, untouched by the commit under test, is NOT flagged) and
      `test_diff_base_flags_an_orphan_this_commit_itself_introduced` (asserts a commit that itself drops a `related:`
      link IS flagged) to `test_check_ag_closeout_linkage.py`. Verified locally:
      `python3 -m pytest scripts/plan-hygiene/test_check_ag_closeout_linkage.py -q` → 14 passed.
