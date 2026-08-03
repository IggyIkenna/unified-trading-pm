---
doc_type: plan
title: Scoped reference-path hygiene pass over plans/archive/ — finalize
summary: >-
  Gated closeout for plans_archive_reference_path_hygiene_2026_08_02.md — machine-held via depends_on + gate_on_depends
  until both of that plan's todos are done. Re-verifies the reference-path ratchet actually moved (check_reference_paths
  back at/below the pre-regression baseline: format 161, exist 901), confirms no AMBIGUOUS/UNRESOLVED entry was silently
  dropped, and archives this plan pair once confirmed.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, reference-paths, ratchet, mechanical, finalize]
related:
  [
    /plans/active/plans_archive_reference_path_hygiene_2026_08_02.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/active/plans_archive_reference_path_hygiene_finalize_2026_08_02.md,
  ]
created: 2026-08-02
last_updated: "2026-08-03"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: review
drift_direction: correct-codex
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [plans_archive_reference_path_hygiene_2026_08_02]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/plans_archive_reference_path_hygiene_2026_08_02.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched (`assigned_vm: planning`) plan needs a gated
  finalize plan; this one shipped without its pair, tripping `check_finalize_plan_coverage.py`'s ratchet (baseline 0,
  regression 1). Authored same-session to close the regression, mirroring the shape of existing finalize plans (e.g.
  ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md).
---

# Scoped reference-path hygiene pass over `plans/archive/` — finalize

> **🟢 ARCHIVED 2026-08-03.** Todos 1+2 (ratchet re-verify, AMBIGUOUS/UNRESOLVED spot-check) were already done by
> slot-15/slot-14 with independent evidence. Todo 3 (archive) is CLOSED HERE AS A DUPLICATE — this doc was one of 3
> independently-authored finalize plans gating the identical parent plan; a sibling doc
> (`plans_archive_reference_path_hygiene_finalize_2026_08_02.md`) performed the one actual archival covering the parent
>
> - all 3 finalize siblings in a single commit. See that doc's Progress Log for the full consolidation account. Moved to
>   `/plans/active/plans_archive_reference_path_hygiene_2026_08_02_finalize.md`.

## Todos

- [x] ✅ [SCRIPT] P2. **Re-verify the ratchet actually moved, not just that the apply ran.** Re-run
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` (or the standalone `check_reference_paths` checker it wraps)
      and confirm format violations are back at/below the pre-regression baseline (161) and exist violations at/ below
      baseline (901) — the two numbers named in the source plan's own "Why this plan exists" section. If either is still
      above baseline, re-open a follow-up todo naming the specific still-violating files rather than closing this doc.
      **RESULT (slot-15, 2026-08-03): ratchet confirmed moved and holding.** Ran both the standalone checker
      (`python3 scripts/plan-hygiene/check_reference_paths.py`) and the full `run_hygiene_sweep.sh --ci` — live counts:
      format 81/81 ✅ (exact match to the current baseline, itself already ratcheted down from the source plan's own
      final todo), existence 87/87 ✅ (exact match). Both are far below the 161/901 pre-regression numbers cited in this
      todo's own text (those numbers predate the `dfdb0887` archive-scope-exclusion + the source plan's own further
      `--update-baseline` to 81/87 — current `reference_paths_baseline.yaml` reads
      `format_count: 81, existence_count:     87`, and live == baseline exactly, so no drift since the source plan's
      last verified state). The full sweep's "Reference path convention (/plans, /codex — ratchet)" hard check reported
      ✅ PASS. The sweep DID report 3 unrelated hard failures this session (prettier proseWrap-continuation-padding
      ratchet, `assigned_vm:NA` corpus size ratchet, Archive-candidates ratchet) — all out of this todo's scope
      (different ratchets, not reference-path); not chased here.
- [x] ✅ [REVIEW] P2. **Spot-check the AMBIGUOUS/UNRESOLVED triage.** For each entry the source plan's todo 2 recorded
      as hand-disambiguated or genuinely-dangling, re-read the actual file to confirm the recorded disposition matches
      what's on disk now (a concurrent edit could have moved the target again). Done when every entry is confirmed, or
      any drift found is logged as a new todo naming the specific file. **RESULT (slot-14, 2026-08-03): all entries
      confirmed, no drift.** Re-ran `python3 scripts/plan-hygiene/fix_reference_paths.py --dry-run` live and
      re-inspected the actual files (not just the plan's stale snapshot): (1) **the 7 hand-disambiguated AMBIGUOUS
      entries (3 files)** — `plans/archive/2026_05/work_split_2026_05_22_ikenna.md` still cites its three targets under
      `/plans/archive/2026_05/...` (all 11 `related:` paths verified to exist on disk);
      `plans/archive/2026_07/work_split_2026_05_22_ikenna.md` still cites the same three basenames under
      `/plans/archive/2026_06/...` (all verified to exist);
      `plans/archive/2026_05/compute_optimization_mock_data_2026_05_13.md` still cites
      `/plans/archive/2026_05/mock_data_pipeline_benchmarking_2026_05_10.md` (the plan doc,
      `doc_type: plan,     status: complete` — confirmed, not the root `type: question` doc). No concurrent edit moved
      any target; the live dry-run reports 0 AMBIGUOUS entries under `plans/archive/**` now (down from 7), consistent
      with the fix holding. (2) **The genuinely-dangling entries** — live dry-run now reports 31
      `UNRESOLVED .../not found anywhere` entries under `plans/archive/**` (recorded as 33 in the source plan's todo 2).
      Listed all 31 citing files: every one is a plausible 2026-04/05-era archived doc citing another old doc by bare
      basename — no candidate resolves anywhere in the live corpus, matching the "frozen historical record, not chased"
      disposition. The 33→31 delta is a benign decrease (fewer dangling, not more) from ordinary corpus churn since
      2026-08-02/03, not a sign any entry was mis-triaged. No drift found; no new todo needed.
- [x] ✅ [PLAN] P2. **Archive both plans** once the two todos above confirm clean — standard 6-step archival ritual
      (banner, referrer repoint, inventory regeneration) per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`. **RESULT (slot-11, 2026-08-03): DUPLICATE
      todo, closed via consolidation, not independently re-executed.** Discovered this doc is one of 3
      independently-authored finalize plans gating the identical parent (see this doc's own Progress Log: two authors
      already collided on 2026-08-02; this doc + a 2nd, separately-authored `..._2026_08_03.md` sibling are a 3rd
      independent collision found 2026-08-03). Performing the archival 3 times in parallel was a real race risk for no
      benefit (one `git mv` per doc, period). The sibling `plans_archive_reference_path_hygiene_finalize_2026_08_02.md`
      performed the actual archival (parent + all 3 finalize docs, one commit); this todo is marked done by that
      consolidation rather than re-doing the same `git mv`.

## Progress Log

- **2026-08-03 (slot-15)** — Worked todo 1: re-ran the ratchet check both standalone (`check_reference_paths.py`) and
  via the full `run_hygiene_sweep.sh --ci`. Live format/existence counts (81/87) match the current baseline exactly,
  well below the 161/901 pre-regression numbers named in the todo. Confirmed no drift since the source plan's own
  last-verified state. See the todo's own RESULT note for detail. Next: todo 2 (spot-check the AMBIGUOUS/UNRESOLVED
  triage).
- **2026-08-03 (slot-14)** — Worked todo 2: re-ran `fix_reference_paths.py --dry-run` live and re-read the actual files
  rather than trusting the source plan's stale snapshot. Confirmed the 3 hand-disambiguated files still point at
  existing, correct targets (0 AMBIGUOUS remain under `plans/archive/**`, down from 7) and the 31 currently-dangling
  entries (down from the recorded 33, a benign decrease) are all genuine frozen historical refs — no drift. See the
  todo's own RESULT note for the full breakdown. Next: todo 3 (archive both plans).
- **2026-08-03 (slot-11, dispatched to a duplicate sibling doc's own finalize task)** — Discovered this doc while
  corpus-grepping for referrers as part of archiving `plans_archive_reference_path_hygiene_finalize_2026_08_02.md`.
  Closed todo 3 by consolidation rather than duplicate execution — see that todo's own RESULT and the sibling doc's
  Progress Log for the full account. Archived alongside the parent + the other duplicate finalize (`..._2026_08_03.md`)
  in one commit.
