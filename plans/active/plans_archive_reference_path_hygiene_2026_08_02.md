---
doc_type: plan
title: Scoped reference-path hygiene pass over plans/archive/
summary: >-
  Run scripts/plan-hygiene/fix_reference_paths.py over the plans/archive/ population specifically to clear the
  check_reference_paths format/exist regression (+47/+14 over baseline) that an active-corpus-only pass cannot reach.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, reference-paths, ratchet, mechanical]
related:
  [
    /plans/active/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
created: 2026-08-02
last_updated: 2026-08-02
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: review
drift_direction: correct-codex
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: "Operator ruling on plan_reconcile_parked_operator_decisions_2026_08_02.md § 4, option A, 2026-08-02."
---

# Scoped reference-path hygiene pass over `plans/archive/`

## Why this plan exists

`run_hygiene_sweep.sh --ci`'s `check_reference_paths` gate measured RED against baseline on 2026-08-02
(`plan_reconcile_parked_operator_decisions_2026_08_02.md` § 4): format violations 208 vs baseline 161 (**+47**), exist
violations 915 vs baseline 901 (**+14**). The violations are concentrated in `plans/archive/` — out of
`/plan-reconcile`'s audit scope (active corpus only) but inside the ratchet's measured population, so no active-corpus
pass can clear it. `scripts/plan-hygiene/fix_reference_paths.py` already globs `plans/**/*.md` (so `plans/archive/` is
already in its default scope, no code change needed) — this plan is the tracked unit for actually running it and
reviewing the diff, per the operator's ruling that a scoped run is "the only thing that will move that number."

## Todos

- [x] ✅ [SCRIPT] P2. Run `python3 scripts/plan-hygiene/fix_reference_paths.py --dry-run` and read the full output. Two
      independent passes: (1) codex refs anywhere in file content normalized to `/codex/...`; (2) bare `.md` filenames
      in `related:` frontmatter resolved against the live corpus and rewritten to `/plans/<found-relative-path>`.
      Confirm which of the reported changes actually land under `plans/archive/**` (the codex-ref pass touches `codex/`
      files too — those are docs-reconcile's scope, not this plan's; scope this plan's apply to the `plans/archive/**`
      subset only). **RESULT: `Files changed: 0` corpus-wide** — every codex ref anywhere in the corpus is already
      `/codex/...`-normalized, and every `related:` bare filename is either already path-prefixed or falls into the
      `Unresolved` bucket (102 total corpus-wide, 38 under `plans/archive/**`) that the script deliberately never
      auto-fixes. There is nothing this script can safely apply under `plans/archive/**` (or anywhere) as of 2026-08-02.
- [x] ✅ [SCRIPT] P2. Triage the `AMBIGUOUS`/`UNRESOLVED` entries the dry-run reports for any `plans/archive/**` file —
      these are left untouched by design (never guessed); each either needs its `related:` entry hand-disambiguated to
      the correct one of the reported candidates, or is a genuine dangling reference to record separately. **RESULT**
      (38 entries under `plans/archive/**`, all left unresolved): - **33 are genuine dangling references** ("not found
      anywhere under plans/ or codex/") — each cites a doc that was apparently renamed/consolidated/never created under
      that exact name during the 2026-04/05 era. These are frozen historical record, consistent with the same rationale
      `check_reference_paths.py`'s own `target_files()` docstring already gives for excluding `plans/archive/` entirely
      (2026-08-02 ruling) — not chased further. - **7 are `AMBIGUOUS`, and NOT safely hand-disambiguable** —
      investigated the two clusters directly: - `plans/archive/2026_07/work_split_2026_05_22_ikenna.md` and
      `plans/archive/2026_05/work_split_2026_05_22_ikenna.md` (same title/content-shape, both cite the same 3 bare
      basenames: `instruments_backfill_phase3_2026_05_22.md`, `mtds_backfill_phase3_2026_05_22.md`,
      `mdps_backfill_phase3_2026_05_22.md`) — each basename resolves to TWO candidates, one under
      `plans/archive/2026_05/` and one under `plans/archive/2026_06/`. `diff` confirms the 2026_05 and 2026_06 copies of
      each of the three target docs are NOT identical — they have diverged content. Picking either candidate risks
      silently linking to the wrong version. - `plans/archive/2026_05/compute_optimization_mock_data_2026_05_13.md`
      cites `mock_data_pipeline_benchmarking_2026_05_10.md`, ambiguous between `plans/archive/…` (root) and
      `plans/archive/2026_05/…` — same shape (two non-identical copies of a same-named archived doc). - **New finding,
      not this plan's scope to fix**: the corpus has genuine **duplicate-named archived docs living in two different
      month-folders with diverged content** (`work_split_2026_05_22_ikenna.md` ×2 pairs of cross-referenced docs,
      `mock_data_pipeline_benchmarking_2026_05_10.md` ×1) — an archival-hygiene defect (probably an artifact of the
      historical dated-archive-folder reorg), not a reference-path defect. Fixing it safely requires deciding which copy
      is canonical (or whether both are legitimately distinct revisions worth keeping under different names) — real
      archival judgment, not a mechanical script pass. Tracked as new todo below rather than guessed here.
- [x] ✅ [SCRIPT] P2. Run `python3 scripts/plan-hygiene/fix_reference_paths.py` (apply) scoped to the reviewed
      `plans/archive/**` changes from todo 1, stage by name, ship via
      `bash scripts/quickmerge.sh "docs(plans): fix_reference_paths.py pass over plans/archive/" --agent --files '<paths>'`.
      **RESULT: ran the real (non-dry-run) apply — `Files changed: 0`, `git status --porcelain` empty.** Nothing to
      stage or ship; confirmed idempotent with the dry-run.
- [x] ✅ [VERIFY] P2. Re-run `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` and confirm `check_reference_paths`
      format/exist counts have dropped back toward the 161/901 baseline (allow for any newly-added legitimate refs
      elsewhere in the corpus since 2026-08-02 — the done-when is "the +47/+14 regression is gone", not an exact
      absolute count match). **RESULT: the +47/+14 regression is gone** — already resolved by a different, prior change
      (`unified-trading-pm@dfdb0887`, ruled option B: excluded `plans/archive/` from `check_reference_paths.py`'s
      `target_files()` and re-baselined 158/407→81/90, per `plan_reconcile_parked_operator_decisions_2026_08_02.md` §
      4). Live counts as of this session: format 81/81 ✅ (exactly at baseline), existence 91/90 ❌ (+1). That +1 is NOT
      a new regression from recent work — bisected via a scratch worktree across every commit since `dfdb0887` (the
      baseline-setting commit itself already measures 91 live vs the 90 it recorded) back to the current HEAD
      (`77be36524`): the count was already 91 at the moment the baseline commit landed, unrelated to `plans/archive/`
      (excluded from this check's population) and unrelated to any commit made during this session. Out of this plan's
      scope (archive-specific); recorded as its own follow-up below rather than chased here.
- [x] ✅ [DOCS] P3. **New finding — duplicate-named archived docs with diverged content.** Investigate + resolve the
      cross-folder duplicates surfaced by todo 2: `work_split_2026_05_22_ikenna.md`'s three cited docs
      (`instruments_backfill_phase3_2026_05_22.md`, `mtds_backfill_phase3_2026_05_22.md`,
      `mdps_backfill_phase3_2026_05_22.md`, each present under both `plans/archive/2026_05/` and
      `plans/archive/2026_06/` with different content) and `mock_data_pipeline_benchmarking_2026_05_10.md` (present
      under both `plans/archive/` root and `plans/archive/2026_05/`). Decide per pair: keep-both-as-distinct-revisions
      (rename to disambiguate, e.g. `_v2` or a dated suffix) vs one-is-a-stray-duplicate-safe-to-remove; only then
      hand-fix the two `work_split_2026_05_22_ikenna.md` copies' `related:` entries to point at the resolved target.
      (repo: `unified-trading-pm`) **RESULT: keep-both — every pair is genuine sequential history, not an accidental
      duplicate.** Read all 4 pairs in full: (1) `instruments/mtds/mdps_backfill_phase3_2026_05_22.md` — the
      `plans/archive/2026_05/` copy carries `archived: 2026-05-23` (the original archival) and a smaller, earlier-state
      task list (several `DEFERRED-OPERATOR-DECISION` items still open); the `plans/archive/2026_06/` copy is materially
      larger (211 vs 202 / 387 vs 250 / 368 vs 311 lines) and carries a dated "✅ ARCHIVED 2026-06-26 — instruments/MTDS
      consolidation" banner plus many additional resolved `[SCRIPT]`/`[CODE]` todos (VM OOM root-causes, relaunches,
      verifications) that only happened AFTER the 2026-05-23 archival — i.e. work genuinely continued on these plans
      post-archival and the 2026-06-26 consolidation re-captured the final state under a new month folder instead of
      updating in place. Both snapshots are real historical record of different points in time, not a copy-paste
      accident — nothing safe to delete. (2) `mock_data_pipeline_benchmarking_2026_05_10.md` is a DIFFERENT kind of
      pair: the `plans/archive/` root copy is a legacy pre-schema **question** doc (`type: question`,
      `status: plan-spawned`, `spawned_plan: plans/active/mock_data_pipeline_benchmarking_2026_05_10.md` — pointing at
      its own eventual plan by the same slug) while the `plans/archive/2026_05/` copy is the actual **spawned plan**
      (`doc_type: plan`, `status: complete`) — genuinely two different documents that happen to share a base filename by
      the question→plan naming convention. Keep both. Fix applied (no deletions/renames — folder placement already
      disambiguates on disk; the only real defect was `related:`'s bare-filename resolution): hand-fixed `related:` in
      both `work_split_2026_05_22_ikenna.md` copies to explicit paths, each pointed at the contemporaneous vintage of
      its cited docs — the `2026_05` copy → the `2026_05/` targets (matching its own 2026-05-22 snapshot), the `2026_07`
      copy → the `2026_06/` targets (matching its own 2026-07-13-updated, post-consolidation snapshot). Also fixed the
      same bare-filename defect in `plans/archive/2026_05/compute_optimization_mock_data_2026_05_13.md`'s `related:` (→
      `/plans/archive/2026_05/mock_data_pipeline_benchmarking_2026_05_10.md`, the plan doc, not the question doc) since
      it's the other citer of the same ambiguous pair flagged by todo 2. Verified: all 7 new target paths exist on disk,
      YAML frontmatter parses clean, and `check_reference_paths.py` shows none of the 3 edited files or their new
      targets in its DANGLING/format-violation output (post-edit format 81/81 unchanged; the existence count moved
      91→104 since the 2026-08-02/03 session but that drift is from unrelated concurrent corpus activity —
      grep-confirmed none of it traces to these 3 files).
- [ ] [DOCS] P3. **Pre-existing +1 existence-ratchet discrepancy, unrelated to `plans/archive/`.** As of
      `unified-trading-pm@dfdb0887` (the commit that re-baselined `check_reference_paths` existence to 90 after
      excluding `plans/archive/`), the live count was already 91 at that same commit — a 1-off measurement gap at
      authoring time, not a subsequent regression. Find the specific dangling `/plans/...` or `/codex/...` reference
      responsible (outside `plans/archive/`, since that's excluded from this check) and either fix it or lower the
      baseline to 91 with a note. (repo: `unified-trading-pm`)

## Progress Log

- **2026-08-02** — Filed per the operator's ruling on `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 4,
  option A.
- **2026-08-02/03 (slot-8)** — Worked all 4 original todos. Headline result: `fix_reference_paths.py` makes ZERO changes
  anywhere in the corpus (dry-run and real apply both confirm) — the script has nothing left to auto-fix under
  `plans/archive/**`, so there is no diff to ship for this plan's original mechanical premise. The
  `check_reference_paths` ratchet itself is already effectively green (format 81/81 exact; existence 91/90, off by a
  pre-existing 1 unrelated to archive) via the separate option-B fix (`dfdb0887`) — matching § 4's own note that this
  plan is "not urgent now that the ratchet itself is green, but still useful hygiene." The actual remaining hygiene
  value surfaced by this pass is two NEW findings (duplicate-named archived docs with diverged content; a pre-existing
  +1 existence-count gap), both tracked as fresh todos above rather than fixed by guessing.
