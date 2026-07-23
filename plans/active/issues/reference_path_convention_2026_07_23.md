---
doc_type: issue
title: >-
  Cross-reference path convention rollout — /plans/... + /codex/... leading-slash migration, remaining format/existence
  cleanup, and the archival-ritual reference-update gap
summary: >-
  Operator-directed hardening (2026-07-23): every cross-doc reference (inline prose, `related:` frontmatter) must be a
  leading-slash path rooted at the unified-trading-pm repo root (e.g. /plans/active/<slug>.md,
  /codex/<section>/<doc>.md) — never a bare filename or a ../-relative path. Corpus-wide migration executed
  (scripts/plan-hygiene/fix_reference_paths.py, 2,418 files touched across two passes) and a new hard, shrinking-ratchet
  checker wired into run_hygiene_sweep.sh (scripts/plan-hygiene/check_reference_paths.py). This doc tracks what the
  migration could NOT safely auto-fix (109 format violations — ambiguous or genuinely dangling bare filenames) and what
  it surfaced but didn't cause (1,286 pre-existing dangling /plans/ + /codex/ references) as its own cleanup backlog,
  plus the separate finding that CLAUDE.md's 5-step archival ritual never actually named a reference-update step.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, codex, references, cross-doc-links, quality-gates, archival, baseline-ratchet]
related:
  [
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
created: "2026-07-23"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [operator request 2026-07-23]
resolved_by:
locked_by:
depends_on: []
---

# Cross-reference path convention rollout

## What shipped 2026-07-23

- `scripts/plan-hygiene/fix_reference_paths.py` — a two-pass mechanical migration (codex-ref normalization to
  `/codex/...` including codex-internal relative refs like `../06-coding-standards/foo.md`; `related:` field bare-
  filename resolution to a full `/plans/...` or `/codex/...` path via a corpus-wide filename index). Ran corpus-wide:
  2,149 files in pass 1 (9,883 codex-ref occurrences + 2,310 `related:` entries fixed), 269 more files in pass 2 once
  the codex-internal-relative shape was added (3,120 more occurrences).
- `scripts/plan-hygiene/check_reference_paths.py` — the standing checker, wired **hard** into `run_hygiene_sweep.sh`
  (`scripts/plan-hygiene/reference_paths_baseline.yaml` is a shrinking-ratchet baseline, same shape as the
  fallback-import/DTZ ratchets: fails only on a NEW violation above the seeded baseline, never on this backlog).
- `/codex/11-project-management/cross-reference-path-convention.md` — the SSOT for the rule itself.
- `plans/active/task_template.md`'s `related:` frontmatter example line now points to the SSOT (see the first todo
  below, already done).

## Todos

- [x] [DOC] P2. ✅ **DONE 2026-07-23** — added the pointer to `plans/active/task_template.md`'s `related:` frontmatter
      example line. `pm@<commit-pending>`.
- [x] [DOC] P1. ✅ **DONE 2026-07-23** — CLAUDE.md's archival ritual is now the 6-step ritual, with the reference-
      update step spelled out explicitly + a note this was a gap, not a regression. `pm@<commit-pending>`.
- [x] [DOC] P2. ✅ **PARTIALLY DONE 2026-07-23** — while staging the corpus-wide migration, the commit hook's
      `check_frontmatter_yaml.py` surfaced 25 pre-existing files with genuinely invalid frontmatter YAML (unrelated to
      this work — confirmed via `git show HEAD:<path>` on each, all already broken before this session touched them). 17
      were a simple unquoted-colon-in-plain-scalar issue and got fixed mechanically (colon → em-dash, matching
      CLAUDE.md's own "no `: ` in unquoted text" convention). **8 remain broken and deliberately untouched** — deeper
      indentation-based block-mapping structural issues, not simple colons, too risky to auto-fix under time pressure:
      `/codex/15-runbooks/alerting/README.md`, `/codex/15-runbooks/alerting/_template.md`,
      `/codex/15-runbooks/incidents/README.md`,
      `plans/archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md`,
      `plans/archive/2026_06/cicd_v2_latency_reduction_2026_06_10.md`, `plans/archive/api_keys_and_auth.plan.md`,
      `plans/archive/carry_staked_basis_structure_axis_2026_05_04.plan.md`,
      `plans/archive/cross_asset_group_catalogue_audit_2026_05_10.md`. This commit's mechanical reference-path fix to
      these 8 was reverted (not applied) so they wouldn't block the commit — they're still on the OLD bare/relative
      codex-ref format, tracked in `format_count`'s baseline (raised 109→167 to cover them). **Done when**: each of the
      8 parses as valid YAML AND has the reference-path fix (re)applied, then `--update-baseline` drops `format_count`
      back down.
- [ ] [REVIEW] P2. Reconcile the archival-mechanics inconsistency this surfaced: `plans/archive/` holds 1,564 files (so
      plans DO get physically moved by some process), but this session's own archival work (4 sports fold-in plans,
      2026-07-23) added a banner + `status: superseded` and left the files IN `plans/active/` — meaning 2 of those 4 are
      still being scanned (and hard-failing) by `check_line_caps.sh`. Decide: does "archival" mean physical move (get it
      out of the actively-scanned corpus, but then every referrer needs updating per the todo above) or
      stay-in-place-with-banner (referrers never break, but active/ never shrinks)? Whichever is chosen, state it as the
      SSOT rule, not two competing practices.
- [ ] [DOC] P3. **109 format violations** (baseline-seeded, `scripts/plan-hygiene/reference_paths_baseline.yaml`) — bare
      `related:` filenames the migration could not safely resolve: some are genuinely ambiguous (multiple files share
      the basename, e.g. `README.md` in ~35 places), some are genuinely dangling (target doesn't exist anywhere under
      `plans/` or `codex/`). Re-run `python3 scripts/plan-hygiene/check_reference_paths.py` for the live list; fix
      what's resolvable by hand, remove references that are genuinely stale, then `--update-baseline` to ratchet the
      count down. **Done when**: `format_count` in the baseline reaches 0.
- [ ] [DOC] P3. **1,286 existence violations** (baseline-seeded) — pre-existing dangling `/plans/...`/`/codex/...`
      references this migration surfaced but did not cause: codex docs describing planned-but-never-shipped content
      (e.g. several `codex/09-strategy/architecture-v2/` docs cite sibling strategy docs that appear to have never been
      written), and references to plans since renamed/archived/consolidated under a different slug. Re-run
      `python3 scripts/plan-hygiene/check_reference_paths.py` for the live list. Large enough to warrant its own triage
      pass (candidate for a Workflow fan-out — independent per-reference, no cross-file dependency) rather than one
      session's manual sweep. **Done when**: `existence_count` in the baseline reaches 0, or the remaining count is
      explicitly re-baselined with a stated reason per entry (e.g. "intentionally documents unshipped future work").
- [ ] [REVIEW] P3. Confirm `/plan-reconcile`'s existing contradiction-sweep phases are sufficient to catch a doc that
      moves without its referrers being updated going forward (the archival-ritual gap above, once fixed, should be
      enforced by more than operator diligence) — extend the skill's Phase 1/AO-dispatch-readiness hunters if not.

## Codex SSOTs

`/codex/11-project-management/cross-reference-path-convention.md` (the rule), `plans/PLAN_FORMAT.md` (frontmatter schema
— confirms `depends_on`/`parent_epic`/`supersedes`/`superseded_by`/`entry_point_for` are bare-slug fields, out of this
convention's scope).
