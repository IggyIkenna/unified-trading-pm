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
asset_group: [infrastructure]
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
context_scope:
  [
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
    scripts/plan-hygiene/check_reference_paths.py,
  ]
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
- [x] [DOC] P3. ✅ **DONE 2026-07-25 (agt-72ba07)** — plan_health hard-failure regression (`existence_count` 1257→1381,
      +124 net new dangling refs / 79 distinct stale targets) root-caused to two un-referrer-updated moves: (1) the
      `codex/14-playbooks/` → `codex/14-customer-journeys/` rename (with a `infra-spec/` subset moving to
      `codex/16-strategy-playbooks/infra-spec/` instead) left 78 distinct `/codex/14-playbooks/...` targets dangling
      across 104 files; (2) `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`'s archival to
      `plans/archive/issues/...` (commit `61618a105`) left 66 referrers pointing at the old active/ path. Applied a
      mechanical corpus-wide path substitution (old target → verified-real new target only; left the ~14 genuinely
      unmapped `14-playbooks/...` refs untouched — those predate both renames and are part of the existing backlog
      below, not this regression) — `existence_count` now 956 (< prior baseline 1257, a net IMPROVEMENT since the fix
      touched every occurrence of each stale target, not just the new ones), baseline ratcheted down via
      `--update-baseline`. `pm@<commit-pending>`.
- [x] [DOC] P3. **2026-07-25 plan_health regression (agt-4b54e5)**: 3 new dangling refs landed from the 2026-07-25
      terminal-status archival sweep (`ad4b1952c`) not updating referrers — `/plans/active/issues/<slug>.md` targets
      moved to `/plans/archive/issues/<slug>.md`. Fixed 2 of 3
      (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` → `cefi_tardis_throughput_collapse_350x_2026_07_17.md`;
      `gcs_bucket_estate_cleanup_2026_07_10.md` (archive) →
      `gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md`), bringing `existence_count` to 1256 (< baseline 1257,
      gate green). **Left unfixed**: `plans/archive/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md`'s
      `related:` still points at `/plans/archive/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md`
      (now archived) — that file is itself 1216L, over the 1000L hard cap (RULE-11), so staging it for even a 1-line
      reference fix is blocked by `check_line_caps.sh`'s no-exceptions-on-touched-files rule until it's split. **Done
      when**: split `sports_shard_enumeration_cartesian_blowup_2026_07_20.md` under 1000L (fold into the P3 line-cap
      cleanup below or its own pass), then fix the reference. — CLOSED (na-eligibility-audit 2026-08-03): the 3rd
      reference was repointed to the archive path without a split, `unified-trading-pm@ca9551fbc` (2026-07-29);
      confirmed live in the file today.
- [ ] [DOC] P3. Same class of gap as the todo above, second instance (found 2026-07-25, slot-8):
      `plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md` (exactly 1000 lines, at the hard cap) carries a
      body-prose reference `issues/fss_bookmaker_dispersion_dead_code_overwrites_best_odds_2026_07_25.md` that needs
      repointing to `plans/archive/issues/fss_bookmaker_dispersion_dead_code_overwrites_best_odds_2026_07_25.md` — same
      `check_line_caps.sh` no-exceptions block (a same-length text swap still trips prettier's paragraph reflow into
      1001 lines, per `terminal_status_archival_backlog_sweep_2026_07_25.md`'s slot-2 Progress Log entry). **Done
      when**: split `sports_satellite_ao_dispatch_batch2_2026_07_24.md` under 1000L, then fix the reference.
- [x] [REVIEW] P3. ✅ **DONE 2026-08-02 (slot-12)** — determination: **NOT sufficient as they stood; extended.**
      Verified by reading the actual code, not the skill's own prose: `check_reference_paths.py`'s existence check DOES
      scan every `/codex/...`/`/plans/...` reference anywhere in body text (`GOOD_REF_RE.finditer(text)` over the whole
      doc, not just frontmatter). But two things blunt it in practice — (a) `run_hygiene_sweep.sh` invokes it `--quiet`
      (`scripts/plan-hygiene/run_hygiene_sweep.sh:181`), which suppresses the itemized per-file violation list, so Phase
      1 mechanical adjudicators have nothing to adjudicate even when the gate goes red; (b) it's a shrinking-ratchet
      check with substantial slack (`reference_paths_baseline.yaml`; live-verified 2026-08-02: existence baseline 901,
      live count 913) — a moderate single-move regression (this doc's own cited incidents: 78/66/3 new dangling
      referrers each) can land entirely inside that slack without ever pushing the corpus-wide total over the ratchet
      ceiling. Net effect: for inline body-text references — the dominant referrer shape a doc move actually breaks —
      the existing mechanism gave no per-move specificity and could silently miss a genuine regression, exactly matching
      what happened in all three of this doc's 2026-07-25 incidents (none were caught by a `/plan-reconcile` pass; all
      were found manually after the fact). Frontmatter `related:`/`depends_on`/ `supersedes` referrers ARE reliably
      caught today (Phase 0's own inventory script computes those directly, ungated) — the gap was specifically inline
      body-text citations. **Extended**: added Phase 1 hunter 8 ("Moved-doc referrer hunter") to
      `cursor-configs/skills/plan-reconcile/SKILL.md` — a git-log-diff-driven, ratchet-independent pass that greps the
      full corpus body text for every recently-moved doc's OLD path and routes any hit straight to the existing Phase 4
      auto-fix row, plus a note to re-run `check_reference_paths.py` without `--quiet` so its itemized list becomes a
      real Phase-1 candidate feed. Also corrected Phase 0's own text, which previously assumed the mechanical checker
      always surfaces the flag (untrue under its default `--quiet` + ratchet invocation). `pm@<commit-pending>`.

## Codex SSOTs

`/codex/11-project-management/cross-reference-path-convention.md` (the rule), `plans/PLAN_FORMAT.md` (frontmatter schema
— confirms `depends_on`/`parent_epic`/`supersedes`/`superseded_by`/`entry_point_for` are bare-slug fields, out of this
convention's scope).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Doc mixes bounded
  mechanical cleanup with one genuine unresolved policy decision (archival convention: physical-move vs
  stay-in-place-with-banner) that the bounded items depend on for correctness — stays NA as a whole; the mechanical
  cleanup items are individually plausible future RECLASSIFY candidates for a dedicated split once the policy decision
  lands.
- **sports_satellite_ao_dispatch_batch3_finalize todo 2, 2026-07-31**: ratchet measurement while archiving 2 source docs
  (`dp_catalog_not_running_sports_prediction_2026_07_15.md`, `sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`
  restored from a wrong archival) — `check_reference_paths.py` now reads 187 format / 919 existence (baseline 161/901),
  and `check_archive_candidates.sh` reads 7 (baseline 4). Confirmed via `git stash` that BOTH ratchets were already over
  baseline on the clean tree before this session's edits — none of the new violations belong to any file this session
  touched (verified by grep). Pre-existing drift from other slots' concurrent work since the baseline was last lowered,
  not a regression this session caused. Not fixed here (corpus-wide, well outside this todo's scope) — flagging the live
  numbers for whoever next runs `--update-baseline` or works this doc's own P3 todos.
- **na-eligibility-audit 2026-07-31**: KEEP-NA, valid — confirms continuity of the 2026-07-30 verdict above (this run's
  only change since was the ratchet-measurement Progress Log entry directly above, a status note, not a todo/scope
  change). Re-checked the open-todo mix on independent review: the P2 REVIEW item ("does archival mean physical-move or
  stay-in-place-with-banner") is still a genuine unresolved policy call, and both P3 dangling-reference todos partially
  depend on that same policy answer for correctness (archival-caused dangling refs are a subset of the existence-
  violation backlog, per this doc's own 2026-07-25 Progress Log entries). Doc stays NA as a whole; unchanged from
  yesterday's assessment.
- **na-eligibility-audit 2026-08-02** (infra tranche, dispatch agt-fe5e17): KEEP-NA, valid — third consecutive
  confirmation. The only change since the 2026-07-31 verdict is the new REVIEW P3 item (added and closed same-day,
  2026-08-02, slot-12: verified `check_reference_paths.py`'s existence check IS body-text-aware but blunted by
  `--quiet` + ratchet slack, then extended `/plan-reconcile`'s SKILL.md with a new moved-doc-referrer hunter) — an
  already-resolved investigation, not new open scope. The 5 open items (`- [ ]` count confirmed via
  `grep -cE '^- \[ \]'`) are unchanged from the prior two verdicts: the P2 REVIEW archival-convention policy call is
  still unresolved, and the two P3 dangling-reference backlogs still partially depend on it. Doc stays NA as a whole.
- [ ] [DOC] P3. **2026-08-03 baseline drift, root cause not yet investigated**: `check_reference_paths.py` live-run
      showed `existence_count` 88 vs. baseline 87 (format_count 81, unchanged/passing) — confirmed via `git stash`
      round-trip that this +1 already existed at HEAD before that session's own edits, so it landed via someone else's
      commit in the interim (this doc's own baseline had dropped to ~87-901 range across 2026-08-02, so a lot of cleanup
      landed that day too — exact commit that introduced the +1 not identified). **Done when**: run
      `python3 scripts/plan-hygiene/check_reference_paths.py` fresh, diff against this doc's last-known-good baseline
      number, find + fix the specific new dangling ref, `--update-baseline`.
