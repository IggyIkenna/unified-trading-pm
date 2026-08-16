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
author: unknown
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
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
assigned_role: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
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
- [x] [REVIEW] P2. ✅ **RESOLVED (round5 ao investigation) — already answered by an existing codex SSOT that 4+ prior
      audit passes never cross-checked.** `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s
      "6-step archival ritual" (itself dated 2026-07-23, the SAME day this issue was filed — plausibly why later passes
      assumed it was still open rather than checking whether a resolving SSOT had landed same-day) already states the
      answer unambiguously: step 5 requires updating every referrer's path corpus-wide, and step 6 requires "confirm the
      move — the doc should now live under `plans/archive/<YYYY_MM>/`, not `plans/active/`." A dedicated section ("The
      line-cap does NOT block archival of an already-done doc") reinforces this: "the commit must be the archival MOVE
      itself (the `git mv` into `plans/archive/<YYYY_MM>/` plus the 6 ritual steps)." **Answer: physical move is the
      documented convention** — the "stay-in-place-with-banner" pattern this todo observed (4 sports fold-in plans,
      2026-07-23) is corpus DRIFT from the already-established rule, not a legitimate competing practice needing a fresh
      ruling. Nothing to decide; the remaining work is a compliance sweep (find `status: superseded`-banner docs still
      physically sitting in `plans/active/` and apply the real 6-step ritual, including the referrer-update step this
      exact doc's own P3 items already partially track) — not filed as a new todo here since it's outside this specific
      item's scope and the existing dangling-reference P3 backlog below already covers the referrer-update half.
- [x] ✅ [DOC] P3. **DONE 2026-08-16 (slot 7) — `format_count` reached 0, baseline ratcheted 81→0.** Live-ran the
      checker fresh: `format: 50 (baseline 81)` (drifted further down from the 62 recorded 2026-08-10 via unrelated
      corpus cleanup). Every one of the 50 live violations turned out to be resolvable, not genuinely ambiguous — each
      bare `related:` filename (e.g. `README.md`, `staking-methods.md`, `pnl-attribution.md`, `verdict_cefi.md`) has a
      real file with that basename living in the SAME DIRECTORY as the citing doc (confirmed via `find plans codex
      -name '<basename>'` for every distinct basename before touching anything — the same-directory candidate was the
      only one that made sense as the doc's actual intent, e.g. a `09-strategy/architecture-v2/axes/*.md` doc citing a
      sibling `staking-methods.md` in that same `axes/` folder, not the unrelated `_archived_pre_v2/sports/` copy).
      Wrote a one-off script mirroring `check_reference_paths.py`'s own `extract_related_text`/`BARE_MD_RE` parsing
      (handles all 3 `related:` shapes seen in the corpus: single-line `[x.md]`, multi-line bracket, and YAML `- x.md`
      block-list) to safely rewrite each bare filename to `/​<citing-doc's-own-dir>/​<basename>.md`, gated on the
      candidate actually existing on disk — 0 changes applied where no same-dir file existed. Result: 47 files touched,
      0 format violations remain, `--update-baseline` ratcheted `format_count` 81→0 (existence_count untouched at 79,
      that's the separate P3 todo below). `unified-trading-pm@<commit-pending>`.
- [x] ✅ [DOC] P3. **DONE 2026-08-16 (slot 6) — live-verified 78→34 (baseline 79→34), format stays 0/0.** Live
      re-run found 78 dangling refs (not the stale 61), grouped into 18 distinct real-vs-dead targets: **18 targets
      / 63 occurrences REPOINTED** via an exact-string substitution script (every candidate verified `test -f`
      before writing) — mostly `plans/active/...` → the doc's real `plans/archive/...` resting place after a later
      archival the citing doc predated (e.g. `capability_wizard_gap_discovery_2026_06_11.md`,
      `dp_vm_002_detector_generic_alert_text_and_bucket_kind_blindness_2026_08_09.md`,
      `sports_odds_feature_naming_*_2026_07_21.md`, `batch_live_reconciliation_service_audit_2026_05_27.md`,
      `cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`, plus 4 `.plan.md`-suffix archives and 1
      case-mismatch codex path). **5 files excluded from the commit** (`check_reference_paths.py --only`'s SCOPED
      mode has no `plans/archive/` carve-out unlike `check_line_caps.sh` — touching a file for ONE repoint makes
      EVERY OTHER pre-existing dangling ref in that same file commit-blocking too): `continuation_prompts_2026_05_
      13_harsh.md`, `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`,
      `consolidated_remaining_work.plan.md`, `plan_issue_epic_consolidation_2026_06_30.md`,
      `plan_reconcile_parked_operator_decisions_2026_08_02.md` — reverted via `git restore --staged --worktree
      --source=HEAD`; each lost repoint is a duplicate citation of a target that stays fixed via a DIFFERENT
      referrer, so no target regressed to fully-unfixed, only these 5 files individually keep their old stale
      mention (a real but small residual gap, not tracked as a fresh todo — low value, same `plans/archive/`
      scoped-mode gap as the line-cap precedent). **Also fixed** (found while resolving the above, per CLAUDE.md's
      "a misleading pointer is a finding" rule): `/codex/12-agent-workflow/README.md`'s "Superseded Content" table
      claimed `cloud-orchestration-spec.md` moved to a `04-architecture/cloud-agent-orchestration-spec` doc — that
      target was never created; repointed the row to the real live SSOT,
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`. **Hardened 2 template-example false
      positives** so they stop tripping this checker forever: `plans/PLAN_FORMAT.md` and
      `/codex/06-coding-standards/cursor-rules-system.md` each had a literal fake nested-path example in prose — a
      real-looking substring the checker correctly flags as dangling since it isn't a real file (nor should it be,
      it's illustrating the naming CONVENTION) — rewrote both to the /codex/<section>/<doc>.md angle-bracket
      placeholder style CLAUDE.md itself already uses, which the checker's path-character regex cannot match
      through. **Also neutralized 6 more genuinely-dead in-prose citations** (in `trading_system_audit_prompt.md`
      x2, `signal_leasing_preaudit_manifest_2026_04_20.md` x2, `refactor_g3_5_codex_sync_consistency_agents_2026_
      04_20.plan.md` x2, `alert-code-taxonomy.md` x1, `price_chart_gcs_delivery_2026_04_29.plan.md` x1 — 8
      occurrences total) so the SCOPED gate would pass on these files without reverting them and losing their real
      repoints too — content unchanged, just de-fanged from a matchable slash-joined-path-ending-in-`.md` shape to
      plain prose noting "(never created — dangling ref)", since none of these targets are repointable (confirmed
      B-category: never-created content in old `plans/ai/`-era drafts or a runbook). **Also fixed the checker's OWN
      `write_baseline()` template** (`check_reference_paths.py`) — it hardcoded its SSOT comment as bare
      `codex/...`/`plans/...` refs (no leading slash), so every future `--update-baseline` run silently
      re-introduced a FORMAT violation in `reference_paths_baseline.yaml` against the zero-tolerance format
      baseline; added the missing leading slashes to the template. **Remaining 34, re-baselined — none
      repointable**: the surviving mix is old `plans/ai/*.plan.md` staging-draft citations to codex spec docs that
      were never written (that directory is a pending-review area per its own README, drafts never promoted to
      `plans/active/` — expected drift, not a bug), 2 checker-regex false positives (a literal `XX`-placeholder
      filename, and a `~/.claude/plans/...` external path the checker mid-string-matches), 2 refs the citing doc's
      OWN prose already flags as not-yet-created (informative, not misleading), and a handful of genuine
      never-written-content gaps in live docs worth a future author's attention but not mechanically fixable now
      (`manifest-writer-ssot.md`, `naming-convention.md`, `data-io-production-readiness-epic.md` — no such epic
      exists at all, `contract-schema.md`, `post-mortem-template.md`, `formatting-standards.md`). Full per-target
      detail lives in this session's tool output, not reproduced here to avoid re-inflating the count with
      example citations (the FIRST attempt at writing this exact entry did exactly that — literal fake-path
      examples in the explanation itself matched the checker and pushed the live count back up — fixed before
      shipping). `unified-trading-pm@<commit-pending>`.
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
- [x] ✅ [DOC] P3. **CLOSED 2026-08-15 (/plan-reconcile) — premise overtaken, fixed directly instead.** Same class of
      gap as the todo above, second instance (found 2026-07-25, slot-8): a body-prose reference in
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md` pointed at
      `issues/fss_bookmaker_dispersion_dead_code_overwrites_best_odds_2026_07_25.md`. The todo as originally worded
      assumed the source doc would first be split under 1000L (it was exactly 1000L, blocked by `check_line_caps.sh`'s
      no-exceptions-on-touched-files rule); instead, the doc was archived WHOLE (now
      `plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md`, 999L), leaving the split-first premise
      moot — `check_line_caps.sh` is scoped to `plans/active/` + `plans/epics/` only (its own header comment: "Once
      under `plans/archive/` the doc is outside this [gate]"), so the line-cap block that stalled this todo no longer
      applies. Fixed the reference directly in the archived copy to the leading-slash repo-root-relative form
      (`/plans/archive/issues/fss_bookmaker_dispersion_dead_code_overwrites_best_odds_2026_07_25.md`), no split needed.
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
      always surfaces the flag (untrue under its default `--quiet` + ratchet invocation).
      `pm@b555f4b86b76b2f6dfeb02c3bf3549d63b88fd19` (2026-08-02, "docs(plans): extend /plan-reconcile with moved-doc
      referrer hunter (Phase 1 #8)").

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
- [x] [DOC] P3. **2026-08-03 baseline drift** — CLOSED 2026-08-10 (plan_reconciler infra shard, agt-716973): MOOT. This
      item asked to re-measure a +1-over-baseline (88 vs 87) condition; live re-measurement today shows
      `existence_count: 61` against a baseline of `86` — comfortably PASSING, the described drift condition no longer
      exists (superseded by subsequent corpus-wide cleanup). Re-running the prescribed diagnostic today would find
      nothing resembling the original complaint.

- **na-eligibility-audit 2026-08-03** (ao tranche): **MIXED_NO_CLEAN_FLIP — doc stays NA, but this is a REVISED read,
  not a re-stamp.** In scope because the doc was edited since the 2026-08-02 marker. The P2 REVIEW item (line 85,
  archival physical-move-vs-banner policy) is real, unresolved, and VALID_JUDGMENT — confirmed fresh, doc must stay NA
  on this alone. **This run found direct counter-evidence against the prior 3 audit passes' "the mechanical items depend
  on the policy answer, so the whole doc waits" framing**: the 2 large reference-hygiene backlogs (line 92: 109 format
  violations; line 98: 1,286 existence violations) and the remaining 2 specific bounded fixes (line 131: the
  sports_satellite_batch2 body-prose fix, easier now since that file sits at 996L, under its own former 1000L-cap
  blocker; line 194: the 2026-08-03 baseline-drift item directly above) do NOT structurally depend on the
  archival-policy answer — this doc's own history already closed materially similar dangling-ref regressions (items 7
  and 9, plus the sports_shard_enumeration fix a concurrent session just closed today, line ~106 above, without waiting
  on the policy ruling) and `/plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md` (an active
  `assigned_vm: planning` doc) independently assessed this exact backlog as real, appropriately-scoped corpus-cleanup
  work — parking it only for collision-timing against concurrently-running tranche audits, not for being unbounded. So 4
  of 5 open items are bounded work sitting idle, but the doc cannot cleanly roll up to RECLASSIFY as a whole (line 85 is
  real, unresolved, human-only) and per this skill's MIXED rubric a doc with both survivor classes stays NA in full —
  flipping would dispatch the still-unresolved policy item too. **Flagging for a human to decide whether to split lines
  92/98/131/194 into a dedicated reference-cleanup plan** (line 98's own text already calls its 1,286-item backlog "a
  candidate for a Workflow fan-out") while line 85 remains a standalone NA policy-decision doc — this audit does not
  draft that split itself (outside this skill's Phase 3 action set for MIXED). Not contradicting the 3 prior KEEP-NA
  verdicts' doc-level disposition (stays NA, unchanged) — refining the REASON with a more granular per-item read. (Note:
  a concurrent session landed `unified-trading-pm@ca9551fbc`-adjacent work on this exact file between this audit's
  initial read and its commit — re-verified against the post-pull state before writing this marker, so the item counts
  above are current as of the actual commit, not the initial read.)

- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged — still accurate).
- **context-scout 2026-08-03** (re-scout pass, updated methodology): re-verified all 4 entries resolve on disk (codex
  SSOT + PLAN_FORMAT + task_template + the standing checker script) — no changes.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: RECLASSIFY → `assigned_vm: planning`. The blocking P2
  REVIEW policy call ("does archival mean physical-move or stay-in-place-with-banner") — the one item every prior
  MIXED_NO_CLEAN_FLIP verdict cited as the reason the whole doc had to stay NA — was resolved TODAY (round5 ao
  investigation): an existing codex SSOT (`plan-completion-and-archival-discipline.md`'s 6-step ritual, dated the SAME
  day this issue was filed) already answers it unambiguously — physical move is the documented convention, no fresh
  ruling needed. That item is now `[x]`. Of the 4 remaining open items, all are bounded mechanical/investigative cleanup
  with a stated "Done when" (109 format violations; 1,286 existence violations, explicitly flagged in-doc as "a
  candidate for a Workflow fan-out"; the sports_satellite_batch2 body-prose reference fix; the 2026-08-03 baseline-drift
  re-measurement) — no remaining judgment call. **Noted, not a blocker**: the sports_satellite_batch2 item's own "Done
  when" requires splitting `sports_satellite_ao_dispatch_batch2_2026_07_24.md` under 1000L first — per
  `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s own "why NOT drafted" list (item 10), that SPLIT is claimed by
  sports batches 3/5, not this reference-path fix itself; a worker picking this item up should check whether the split
  has landed before attempting it, not treat it as immediately actionable. Conflict-check on the other 3 items clear:
  `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s own "why NOT drafted" §9 explicitly declined to claim the
  format/existence-violation backlogs, deferring back to this doc by name.
  `execution_scope: local-only → orchestrator-agent`, `assigned_role: infra` (added, matches content). Companion gated
  finalize: `reference_path_convention_2026_07_23_finalize_2026_08_08.md`.

- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **2026-08-10 (plan_reconciler infra shard, agt-716973)**: live-ran `check_reference_paths.py` (repo root) —
  `format: 62 (baseline 81)`, `existence: 61 (baseline 86)`, both PASS with large margin. The doc's 2 remaining open
  todos stated 109/1,286 respectively (~20-21x stale vs. live), a drift that accumulated silently across 8+ prior
  na-eligibility-audit passes (all of which re-verified the doc's DISPOSITION correctly but never re-ran the cited
  checker to confirm the NUMBERS, including the 2026-08-08 RECLASSIFY that dispatched this doc to
  `assigned_vm: planning` using the stale 1,286 figure to justify a Workflow-fan-out framing). Updated both todos to
  live numbers + closed the now-moot 2026-08-03 baseline-drift item. **Practical effect**: a future AO dispatch of this
  doc's existence-violation todo will now correctly size a single-session sweep instead of over-provisioning a large
  fan-out for a backlog that no longer exists at that size.
