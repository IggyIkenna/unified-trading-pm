---
doc_type: issue
title:
  na-eligibility-audit's own Progress Log marker text is silently cut off mid-sentence with a literal "..." on at
  least 2 docs (2026-08-18 dated entries) -- a distinct defect from the already-tracked body_hash instability bug
summary: >-
  Found while epic-scoping `/plan-reconcile deployment_and_user_management_master`: 2 of this epic's 17 child docs
  (`plans/active/github_actions_operator_gated_followups_2026_07_17.md`,
  `plans/active/test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md`) each carry a 2026-08-18-dated
  `na-eligibility-audit` Progress Log marker whose narrative text ends mid-sentence with a bare "..." -- confirmed via
  a raw `tail -c` byte read (not a Read-tool rendering artifact): the github_actions doc's marker ends "...needs a
  human auth step a worker cannot perform, plus..." (the clause naming the SECOND blocking reason, after "plus", is
  never written); the test_impact doc's marker ends "...The doc's frontmatter sets..." (the actual frontmatter claim
  is never stated). Both are the LAST line of their file, both dated the same day (2026-08-18), both end on a bare
  trailing ellipsis with no closing punctuation -- consistent with a script-side text-generation/character-budget
  truncation, not a human typo (a human writing "plus..." to trail off is implausible mid a structured audit-verdict
  marker whose whole purpose is precision). **Not the same bug as
  `na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md`** (that doc is about `body_content_hash()`
  producing an unstable hash across repeated marker appends, a Phase-0 incremental-skip SIGNAL bug) -- this is about
  the marker's own NARRATIVE TEXT being cut off mid-word, a content-loss bug, checked directly against that doc's
  content and confirmed disjoint (no overlap in root cause description).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [na-eligibility-audit, plan-hygiene, tooling-bug, truncation, progress-log, script]
related:
  [
    /plans/active/issues/na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md,
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /plans/active/test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
created: "2026-08-19"
author: "claude-code (plan_reconciler, epic-scoped deployment_and_user_management_master run)"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
assigned_role: review
drift_direction: NA
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Found during a `/plan-reconcile deployment_and_user_management_master` epic-scoped pass, 2026-08-19, while reading
  every child doc in full. Confirmed via `tail -c 400 <file>` on both affected files (raw byte read, not the Read
  tool's rendered view) -- both files genuinely end with the literal text shown in the summary, not a display
  truncation.
context_scope:
  [
    /plans/active/issues/na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    scripts/plan-hygiene/na_marker_helper.py,
  ]
---

# na-eligibility-audit marker text silently truncated mid-sentence

## What was found

Two independent child docs of `deployment_and_user_management_master` (a `ci`-tranche doc and a cross-epic-shared
doc) each carry a `na-eligibility-audit 2026-08-18` Progress Log entry that is the last line of the file and ends on
a bare, unpunctuated `...`:

1. `plans/active/github_actions_operator_gated_followups_2026_07_17.md:734` (verified via `wc -l` == 733 + `tail -c
   400`):

   > **na-eligibility-audit 2026-08-18** (ci tranche): KEEP-NA, valid -- 4 open items confirmed by direct grep,
   > matching the doc's own most recent full audit (2026-08-10: 'Full read (1001 lines, both pages) + grep confirm 4
   > open todos, matching phase0=4'). Item 1 (STEP 2d) is dependency-blocked on the still-open digest-drift-sweep
   > investigation per the D3 table's 2026-08-12 correction. Item 2 (bare-host bootstrap) is structurally blocked —
   > the doc itself flags the GCP-ADC leg as 'interactive', i.e. needs a human auth step a worker cannot perform,
   > plus...

   The clause after "plus" — presumably naming a SECOND reason item 2 is structurally blocked (the doc's own body
   also names systemd + real GH-runner-registration as un-provable in a container, alongside the GCP-ADC leg cited
   before the cut) — is never written. The sentence has no closing period.

2. `plans/active/test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md:503` (last line of the file):

   > **na-eligibility-audit 2026-08-18** (ci tranche): KEEP-NA, valid -- Fleet-wide test-impact-selector measurement
   > + rollout plan; Phase 1 (measurement) and most of Phase 2 (implementation, including a scoped MDPS production
   > promotion) are shipped. grep confirms 2 open checkboxes: the deprioritized-but-repurposed divergence-analysis
   > tool (L246, has a stated done-when but is individually bounded-looking) and the fleet-wide evidence-sufficiency
   > judgment call (L273, explicitly gated on 'the reviewer judges large enough to trust'). The doc's frontmatter
   > sets...

   Whatever claim about the frontmatter this marker was about to make is never stated.

Both markers are otherwise well-formed (correct `**na-eligibility-audit <date>** (<tranche>): <VERDICT>, ...`
header, correct bullet indentation) — only the free-text narrative tail is missing. Both are the FINAL line of their
respective file, both dated the same day, both cut off at a similar point in a multi-sentence explanation (roughly
400-450 characters into the marker's own text) — consistent with a fixed-length text buffer/append operation that
truncates rather than a per-doc content difference.

## Why this is a distinct bug from the tracked body_hash issue

`na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md` documents `body_content_hash()` producing a
DIFFERENT hash before/after a marker append (a residual blank-line delta + a same-date tie-break bug), which causes
the Phase-0 inventory to wrongly re-flag an already-audited doc as "in scope." That bug is about hash STABILITY, not
about what TEXT gets written into a marker. Neither of the 2 confirmed repros in that doc shows truncated marker
prose — its own quoted examples are complete sentences. This finding is about the marker-authoring/append step
itself losing text, a content-loss bug with a different (and arguably worse) blast radius: a future reader trusting
this marker's verdict has no way to know a load-bearing clause was silently dropped, versus the hash bug which is at
worst a wasted re-verification pass with the correct answer preserved.

## Impact assessed

Both truncated markers still carry a clear, unambiguous VERDICT (`KEEP-NA, valid`) before the cut — the missing text
is supporting rationale, not the verdict itself, so neither doc's dispatch-eligibility classification is wrong as a
result of this specific truncation. Not a correctness incident for either doc's current state. The risk is
forward-looking: a future reader (human or agent) citing "item 2 is structurally blocked... plus [the missing
reason]" as established fact will find only the first reason, understating how blocked the item actually is; the
frontmatter claim in the second example is simply absent.

## Recommended next steps

1. [SCRIPT] P3. Locate the na-eligibility-audit skill/script code path that appends a Progress Log marker (likely
   `cursor-configs/skills/na-eligibility-audit/SKILL.md`'s own worker prompt/output-formatting step, or a shared
   `na_marker_helper.py`-adjacent utility per the sibling body_hash issue's importer list) and check for a
   fixed-length truncation (string slice, LLM max-token cutoff on a sub-call, or a shell/API response-size limit)
   around the ~400-450 character mark of the narrative text.
2. [SCRIPT] P3. Once root-caused, decide the fix: either raise/remove the length limit if one exists, or restructure
   the marker-writing step so a genuinely long rationale is written as a SHORTER marker line plus a separate,
   un-truncated Progress Log paragraph (matching how several manually-written entries elsewhere in this corpus
   already split "one-line marker + full paragraph" when the full explanation is long).
3. [DOC] P3. Once root-caused, do a bounded corpus grep for the same trailing-bare-ellipsis-at-EOF signature
   (`rg -l '\.\.\.$' plans/active/*.md plans/active/issues/*.md` narrowed to lines matching the
   `**na-eligibility-audit` marker prefix) to size the full blast radius beyond the 2 instances found incidentally
   here — this run did not do a corpus-wide sweep, only noticed these 2 while reading one epic's child docs in full.

## Todos

- [x] ✅ [SCRIPT] P3. Root-cause the truncation (recommended next step 1 above). **DONE 2026-08-20 (slot-7,
      review).** Read `scripts/plan-hygiene/na_marker_helper.py` in full: it writes `marker_suffix_text` VERBATIM
      (`marker_line = f"- **na-eligibility-audit {date}** [body-hash:{h}]: {suffix}\n"`, `append_one()`) — no length
      limit, no slicing, anywhere in the file. `git log --follow` confirms the script has existed since 2026-08-17
      (`f57cd9eaf4`/`6a858c6895`), before every confirmed 2026-08-18-dated truncated instance, and it has never
      contained truncation logic. **Verdict: not a shipped-script bug.** The truncation is introduced upstream, by
      individual na-eligibility-audit agent sessions composing the `suffix` text themselves (as a CLI arg or a
      JSON-batch field) before calling this helper — exactly what this doc's own 2026-08-19 corroborating Progress
      Log entry caught live: a session's own ad hoc "naive fixed-length (220-char) clip of a long evidence string,"
      not a defect inside any file this repo ships. The likely trigger: `SKILL.md`'s own marker guidance (line 75,
      `"<one-line why>"`) tells agents to keep the marker short but gives no canonical HOW — no length constant, no
      safe-truncation helper, no worked example — so, under that "keep it one-line" pressure, individual sessions
      each improvise their own inline slice (`text[:220]` or equivalent) when the real evidence rationale runs long,
      and a naive character-offset slice has no clause/paren awareness, producing the bare mid-word/mid-clause cuts
      this doc catalogs. This explains why every confirmed instance is `na-eligibility-audit 2026-08-18` (same
      guidance, read independently by several parallel tranche sessions the same day, each re-deriving the same
      failure-prone pattern) rather than a single script defect that would recur on every date the audit has run.
      Root cause for todo 2: add a canonical safe-truncation helper (clause/paren-boundary-aware, matching the fix
      this doc's own 2026-08-19 entry already hand-rolled once) either inside `na_marker_helper.py` or as documented
      SKILL.md guidance, so future sessions call it instead of re-inventing an unsafe one.
- [x] ✅ [SCRIPT] P3. Implement the fix once root-caused (recommended next step 2 above). **DONE 2026-08-20 (slot-4,
      review).** Added `truncate_marker_suffix()` and the `truncate` subcommand to
      `scripts/plan-hygiene/na_marker_helper.py`; it prefers sentence/clause boundaries, preserves balanced
      delimiters, labels intentional shortening as `… [rationale truncated]`, and rejects bare trailing ellipses on
      normal `append`/`batch` writes. Updated `cursor-configs/skills/na-eligibility-audit/SKILL.md` to require the
      complete rationale or this explicit helper.
- [ ] [DOC] P3. Corpus-wide sweep for the same signature once the fix ships, to find + backfill every other instance
      (recommended next step 3 above).

## Progress Log

- **2026-08-19 (plan_reconciler, epic-scoped `deployment_and_user_management_master` run)**: filed. Found
  incidentally while reading 2 of the epic's 17 child docs in full; confirmed genuine (not a Read-tool artifact) via
  a raw `tail -c` byte read on both files. Not fixed here (root-causing a script-side truncation is out of scope for
  a docs-only reconciliation pass) — filed with full repro text so a future session doesn't have to re-find it.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): RECLASSIFY whole-doc — all 3 todos are a bounded
  investigate-then-fix-then-sweep chain (root-cause a specific truncation, implement the fix, corpus-sweep for other
  instances), the standard SCRIPT-bugfix shape, no operator gate found. Conflict-check clear (no active
  `plan_hygiene_master` planning doc or satellite batch touches this). Flipped `assigned_vm: NA -> planning`.
  **Fresh corroborating instance found + self-corrected THIS SAME RUN, with a concrete root-cause hint for todo 1**:
  writing this run's own 27 KEEP-NA Progress Log markers, a naive fixed-length (220-char) clip of a long evidence
  string cut 8 of them mid-clause with no ellipsis (e.g. one ended "...multi-repo build/design work (M6, M7." —
  unbalanced parens, dangling mid-list) — the exact defect shape this doc describes, reproduced live by cutting a
  string at a raw character offset without checking for a clause/paren boundary. Caught via a scripted paren-balance
  check before shipping and fixed by cutting at the nearest safe boundary instead; all 8 verified clean in the final
  files. If the tracked script/LLM-sub-call mechanism does something equivalent (slice/truncate a marker string at a
  fixed length without boundary-awareness), that is a plausible root cause worth checking first. Companion:
  `na_eligibility_audit_marker_text_silently_truncated_2026_08_19_finalize_2026_08_19.md`.
- **plan_reconciler 2026-08-19 (dispatch agt-f212cb, ci tranche)** — additive evidence for todo 3 (corpus-wide
  sweep), found incidentally by this run's own 6 hunter batches while reading the ci tranche in full (not a
  dedicated sweep — still not superseding todo 3's own planned corpus-wide pass). **11 MORE confirmed instances**,
  all byte-verified (`tail -c`, not a Read-tool artifact), all `na-eligibility-audit 2026-08-18` markers:
  `plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md:626`,
  `plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md:826`,
  `plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md:880`,
  `plans/active/issues/deployment_api_mtds_meta_missing_blocks_workspace_qg_step_5_83_2026_08_03.md:213`,
  `plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md:149`,
  `plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued3_2026_08_03.md:565`,
  `plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md:985` (**structural
  variant** — this one is NOT at literal EOF, a later entry was appended after it, so the bug can leave a
  truncated entry stranded MID-document, not only at file-end — worth checking the root-cause fix handles both
  cases), `plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md:343`,
  `plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md:235`,
  `plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md:296`,
  `plans/active/issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md:229`,
  `plans/archive/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md:344` (path updated — this
  doc was archived by this same plan_reconciler run, same commit chain). Every truncation instance found across
  this run's ci-tranche sweep is a `na-eligibility-audit 2026-08-18` marker, always on an `assigned_vm: NA` doc —
  strengthens the existing 220-char-clip-without-boundary-awareness root-cause hypothesis. **Scale finding,
  important for todo 3's sizing**: a corpus-wide grep this session (by one of the hunter batches) found **116
  docs** carry a `"na-eligibility-audit 2026-08-18"` entry — the true blast radius of this bug is almost certainly
  much larger than the 13 instances now confirmed across both runs combined (2 original + 11 here); todo 3's own
  planned sweep should treat 116 as the upper-bound candidate count to check, not a fresh unknown.
- **context-scout 2026-08-20**: refreshed context_scope (3 entries)
- **2026-08-20 (slot-4, review)**: implemented todo 2 with the safe truncation helper and append validation; focused
  syntax/regression checks pass. Todo 3 (corpus-wide sweep for the bare-trailing-ellipsis signature) remains open for
  a separate dispatch.
