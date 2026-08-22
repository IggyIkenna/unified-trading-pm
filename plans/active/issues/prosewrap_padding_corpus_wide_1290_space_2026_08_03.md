---
doc_type: issue
title:
  "Prettier proseWrap continuation-padding corruption is corpus-wide (82 docs, 4472 lines, up to 1290 leading spaces) —
  not the 2 instances the originating issue doc found"
summary: >-
  Root-causing prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md's P3 todo (reproduce + fix the proseWrap
  continuation-padding bug) surfaced that the corruption is far larger in scope than the 2 originally-flagged commits: a
  corpus-wide scan with the new scripts/plan-hygiene/check_prosewrap_padding.sh gate found 82 active plan/issue/codex
  docs already carrying this padding, 4472 violating lines total, up to 1290 leading spaces on one line
  (plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md — a content mirror of the doc that produced the
  original 2 flagged instances, reformatted many more times across subsequent unrelated commits). The new gate is now
  live (shrinking ratchet, baseline=4472) so this cannot grow further unnoticed, but the existing debt is untouched —
  that's this doc's scope.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prettier, prosewrap, tooling, plan-hygiene, cosmetic, corpus-cleanup]
related:
  [
    /plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-03
last_updated: "2026-08-21"
author: unknown
parent_epic: security_and_cross_cutting_master
# reclassified NA -> planning 2026-08-03 (na-eligibility-audit, cross-cutting tranche) — conflict-check CLEAR
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source:
  [
    "Discovered 2026-08-03 by slot 11 (backend_engineer) while root-causing
    prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md's first todo — a corpus-wide survey run as part of
    calibrating the new lint gate's threshold turned up far more existing damage than the 2 commits the parent issue doc
    named.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /scripts/plan-hygiene/check_prosewrap_padding.sh,
    /scripts/plan-hygiene/prosewrap_padding_baseline.yaml,
    /scripts/plan-hygiene/fix_prosewrap_padding.py,
    /scripts/plan-hygiene/run_hygiene_sweep.sh,
  ]
---

# Prettier proseWrap continuation-padding corruption is corpus-wide

## What I found

While root-causing `prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md`'s first todo, I confirmed the bug
is a genuine, reproducible **prettier idempotency defect** (prettier 3.9.5 AND 3.9.6 — the latest release at
investigation time — both affected): a paragraph that is the 2nd+ block inside a list item, once it has been reflowed to
span multiple physical lines, gets its continuation lines' leading-space padding **increased on every subsequent
prettier pass over the same file** instead of converging to a stable wrap. Confirmed with a minimal 4-line fixture,
growing +4 spaces per pass (18→22→26→30→...) with **or without** any backtick inline-code span present — so despite the
parent issue doc's framing, this is not specifically about unbreakable inline-code tokens, it's a broader
list-item-continuation reflow bug. Full repro + minimization work is in the parent doc's Progress Log.

Building `scripts/plan-hygiene/check_prosewrap_padding.sh` (the fix for that todo) required calibrating a leading-indent
threshold against the live corpus, which meant scanning it — that scan found the corruption is NOT limited to the 2
commits the parent doc named:

- **82 files** across `plans/active/`, `plans/epics/`, and `codex/` carry at least one instance.
- **4472 total violating lines** (the gate's own count, now seeded as its ratchet baseline).
- The worst single instance: **1290 leading spaces** on lines 222-231 of
  `plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` — this is the SAME paragraph that produced the
  original `tradfi_backfill_oom_remediation_2026_06_24.md` instances (18 spaces at first commit `e67a7367b`, 338 by
  `129905504`), mirrored into the satellite-batch doc and then reformatted across many MORE unrelated commits, each pass
  compounding the padding further.
- The full file list is reproducible on demand: `bash scripts/plan-hygiene/check_prosewrap_padding.sh` (no args = full
  default corpus scan) prints every file + flagged line.

## Why it matters

- Byte bloat + diff noise on 82 active docs — any future edit to one of these files carries this padding forward in
  `git diff`/`git blame` output, and (per the root-cause finding) makes it WORSE every time prettier reformats the file
  for an unrelated reason.
- The new gate (`check_prosewrap_padding.sh`, wired into `run_hygiene_sweep.sh`'s full sweep as a shrinking ratchet,
  same shape as `check_line_caps.sh` / `check_archive_candidates.sh`) stops this from growing unnoticed going forward,
  but does nothing about the existing 4472 lines — that debt needs a deliberate remediation pass, the same way
  `check_prettier_mangling.sh`'s corpus was fully repaired before that gate went live zero-tolerance (see
  `prettier_emphasis_mangling_corpus_corruption_2026_07_14.md`).

## Recommended decision

Mechanical, bounded remediation — not a design/judgment call:

1. Run `bash scripts/plan-hygiene/check_prosewrap_padding.sh` (no args) to get the current flagged file+line list.
2. Per flagged file: collapse each over-indented continuation line's leading whitespace back to the structurally-correct
   indent for its context (matching the list item's own body indent — usually 2/4/6 spaces depending on nesting depth),
   and collapse any 3+-space run found inside a backtick span back to a single space. Verify **content-only** via
   `git diff -w` (per the parent doc's own verification convention) before committing — this is pure whitespace repair,
   never a wording change.
3. Re-run `check_prosewrap_padding.sh --update-baseline` to lower the ratchet as files get fixed; the target is
   `violation_count: 0`.
4. Because prettier itself still has this idempotency bug (confirmed on latest 3.9.6), a REPAIRED file will drift again
   if it's touched by an unrelated commit and prettier-autostage reformats it — the gate (todo 2 below is NOT itself the
   fix, `check_prosewrap_padding.sh` is) will catch that recurrence going forward, but a repair pass alone doesn't make
   it permanent. No further action needed beyond keeping the gate live; re-open this doc if the ratchet baseline climbs
   again after remediation.

## Todos

- [x] ✅ [BACKEND] P3. **DONE — verified 2026-08-20.** `check_prosewrap_padding.sh` reports 0 violating lines; full
      repair series landed across `unified-trading-pm@8a6dabdd71`…`@162661e410` (baseline 3655→0, git log confirmed).
      Batch-repair the leading-whitespace padding in the 82 flagged files (see § "What I found" — run
      `bash scripts/plan-hygiene/check_prosewrap_padding.sh` for the live list), collapsing over-indented continuation
      lines back to their structurally-correct indent and any 3+-space run inside a backtick span back to a single
      space. Verify content-only via `git diff -w` per file before committing. Fine to split across multiple
      commits/sessions — not a single-commit requirement. **Automation available (2026-08-10, 18th promote-wall dispatch
      agt-e56165): `scripts/plan-hygiene/fix_prosewrap_padding.py` automates exactly this repair for a given set of
      files — run it on the live-flagged list, then verify with the gate. Read its docstring first (it encodes the
      `--only`-mode trap, the anchor-indent rule, and the formatter-mangling trap).** **Known narrow overlap
      (na-eligibility-audit 2026-08-03, conflict-check § 3): `cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md`
      carries its own P3 todo to hand-fix ONE of these 82 files
      (`issues/sports_stats_delayed_live_capture_still_dead_post_fix_2026_07_29.md`, still flagged as of this run's live
      check). Not treated as a blocking conflict — both fixes converge on the identical whitespace-only repair, so
      whichever lands first makes the other a no-op; skip re-touching that file if batch3's todo has already landed by
      the time this todo executes.** (repo: unified-trading-pm)
- [x] ✅ [BACKEND] P3. **DONE — verified 2026-08-20.** `scripts/plan-hygiene/prosewrap_padding_baseline.yaml` reads
      `violation_count: 0`; live `check_prosewrap_padding.sh` run confirms 0 violations against baseline 0 — target
      plateau reached. (repo: unified-trading-pm)
- [ ] [OPERATOR] P2. DEFERRED-BY-DESIGN — D117 ruling (2026-08-21, issues_corpus_completion_dispatch_2026_08_21.md
      ledger): accept option (c), continuous hand-repair + the ratchet as a rate-limiter; fleet-wide prettier/config
      patch blast radius is disproportionate to a cosmetic whitespace bug. Ratchet holds the corpus at 0 (verified
      2026-08-20). No further source-level investment planned; re-open only if the ratchet climbs materially again.

## Progress Log

- 2026-08-03 (slot 11, backend_engineer): filed while completing
  `prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md`'s first todo — the fix
  (`check_prosewrap_padding.sh`) required a corpus-wide calibration scan that surfaced this much larger existing-debt
  scope, which is out of that todo's bounded remit (reproduce + build the gate) and tracked here instead per the
  findings-closure rule. `assigned_vm: NA` per the ASK-BEFORE-CREATING default; operator/na-eligibility-audit can
  reclassify to `planning` if this precisely-scoped mechanical remediation should be AO-dispatched.

- **context-scout 2026-08-03**: populated context_scope (4 entries).

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-03 (cross-cutting tranche)**: RECLASSIFY, conflict-check CLEAR — this doc's own
  Progress Log explicitly invited reclassification, and the sole open todo is bounded/mechanical (run an existing
  script, collapse whitespace per its output, verify content-only via `git diff -w`) with a stated done-when. Cleared
  against the shared conflict-check protocol: the only overlap found is a narrow, single-file one with
  `cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md`'s hand-fix todo (noted inline above, not blocking — an
  idempotent mechanical fix). No finalize-plan companion needed (`doc_type: issue`, structurally exempt per
  `check_finalize_plan_coverage.py`). Flipped `assigned_vm: NA -> planning`, `execution_scope` to `orchestrator-agent`.

- **plan_reconciler 2026-08-10 (cross-cutting tranche, dispatch `agt-33a6ec`)**: refining the trigger condition while
  hand-fixing several NEW instances this run (unrelated to this doc's own todos — found while adding my own notes to
  other plan docs). Confirmed concretely: the corruption is NOT random — it specifically triggers on a multi-paragraph
  note **nested as a continuation of a checkbox list item** (2+ levels of list/checkbox indent), and gets WORSE on each
  successive `prettier --write` pass on the same content (non-idempotent, monotonically increasing indent — matches
  `check_prosewrap_padding.sh --only`'s own doc comment about this). Repro'd live: writing the identical prose as a
  **top-level blockquote** (`> **...**` immediately before the checkbox, not nested under it) survives repeated
  `prettier --write` passes with zero padding growth — 0 violations both before and after. Practical takeaway for any
  agent hand-authoring a multi-paragraph annotation near a checkbox: use a top-level blockquote banner (matching the
  style already used elsewhere in this corpus for dated correction banners), not a nested checkbox-continuation
  paragraph, or expect to re-fight this bug on every commit attempt.
- **Re-measured 2026-08-12 (slot 3, hit while shipping an unrelated cloudbuild change) — ON THIS DOC'S OWN METRIC, the
  corpus is IMPROVING.** `bash scripts/plan-hygiene/check_prosewrap_padding.sh` (no args, the comparable measurement):
  **2808 violating lines against a baseline of 3655**, itself already ratcheted down from the 4472 seeded on 08-03. So
  remediation is landing: 4472 -> 3655 -> 2808. Current worst single line in the ACTIVE corpus is **1150 leading spaces
  in a 1257-char line (~91% padding)** in
  `/plans/archive/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md`. This doc's headline "1290
  spaces" instance is gone from the active corpus by ARCHIVAL, not repair — its file now sits at
  `/plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`.

  **Correcting my own first version of this entry (shipped `unified-trading-pm@d6026f40dc`), which claimed "82 -> 100
  docs affected, count went UP".** That was a CLAIM > MEASUREMENT error: I counted checkbox-continuation lines indented

  > =10 across `plans/**` + `codex/**`, whereas this doc's 82 came from `check_prosewrap_padding.sh` at its own
  > INDENT_THRESHOLD of 14 and over a different file set (it includes `plans/epics/`). Two different metrics, so the
  > comparison never supported a trend — and on the metric that IS comparable the direction is the opposite one. The
  > same error applied to "worst case DOWN 1290 -> 1150": different files, and the drop is archival rather than repair.
  > **Rule this re-teaches: when re-measuring someone else's number, run THEIR tool, not your own approximation of it.**

- **Hand-repair has a measured half-life of exactly one commit — quantifying "temporary".** Dedented one doc's
  continuation block from 26 spaces to the 6-space list-content indent, verified word-content byte-identical, and
  shipped it. On the very next prettier pass (the same ship) it came back at **10**. Growth per pass is +4 and the
  reflow is non-idempotent regardless of where you start, so dedenting does NOT establish a fixed point — it only resets
  the accumulator. Correcting a claim I made in that commit message (`unified-trading-pm@017bdf4901`), which said the
  dedent gave "the formatter a fixed point": it does not, and the measurement above disproves it. The only durable fix
  is the one this doc already recommends — author the annotation as a top-level blockquote so there is no nested
  continuation for the printer to re-indent.

- **Re-opened 2026-08-15 (slot 3) — confirmed live, this is the predicted recurrence from the 2026-08-03 note above
  ("re-open this doc if the ratchet baseline climbs again").** A `unified-trading-pm` promote-PR streak
  (`quality-gates-v2`) failed continuously from 06:45Z for 4.5+ hours, root-caused to this exact gate. Measured directly
  against `origin/live-defi-rollout` tip (via a disposable `git worktree`, not a possibly-stale local checkout): **2324
  violating lines vs baseline 2011 (313 excess), up from 2217 (206 excess) just ~10 minutes earlier on a slightly-behind
  snapshot.** This is real, currently-growing corpus debt — not a false-positive or a stale-snapshot artifact — driven
  by the mechanism this doc already predicted: `prettier-autostage.sh` reformats a commit's own staged files (confirmed
  by reading it — it is NOT a whole-tree reformat, it's scoped to `"$@"`, the pre-commit-handed file list), so any
  ordinary edit that happens to touch an already-marginally-corrupted `plans/active/*.md` file (the busiest file class
  in the repo — nearly every todo-flip commit lands on one) can push existing near-threshold prose further over
  `INDENT_THRESHOLD` via the non-idempotent reflow bug. `check_prosewrap_padding.sh --only`'s rec-(A) logic deliberately
  does NOT flag this at precommit (a pre-existing-text-just-reflowed hit is intentionally treated as debt, not this
  commit's new problem — the correct call, since blocking ordinary edits on someone else's stale prose would be worse),
  so the corpus-wide count is the only place this growth is ever visible, and it accumulates across many concurrent
  sessions' otherwise-unrelated commits faster than serial hand-repair converges it (this session's own 2026-08-14
  73-line/20-file repair, `unified-trading-pm@20b7132823`, was fully absorbed within hours). **Separately found and
  fixed while investigating this**: `check_prosewrap_padding.sh` gained a `--diff-base <ref>` mode on 2026-08-11
  (identical signature-set-comparison shape to reference-paths/archive-candidates/effort-ratchet/ na-corpus/ag-closeout)
  but `run_hygiene_sweep.sh`'s `run_check` call for it was never actually passed the shared `DIFF_BASE_REF`, unlike its
  5 siblings — a real wiring gap, now closed (`unified-trading-pm@5d497d7736`). This does **not** fix the promote-PR
  streak above: `DIFF_BASE_REF` is deliberately empty on `promote/*` heads and the `live-defi-rollout` dispatch (the
  2026-08-10 double-jeopardy/deadlock design, `run_hygiene_sweep.sh` lines ~350-385), so promote-path behavior for this
  check is unchanged by the wiring fix — it only affects the rare "normal PR into main" CI path. Confirmed via direct
  measurement that baseline+buffer mode is doing its job correctly here; this is genuine debt, not an architecture bug.
  **Not attempted, and not something a single session should do unilaterally**: patching `prettier-autostage.sh` or
  `.prettierrc` itself to stop the generative reflow (the only fix that would actually stop new debt at the source,
  rather than reactively repairing it) — that tooling is shared fleet-wide, and a change to it is exactly the kind of
  cross-cutting, SSOT-level call CLAUDE.md reserves for an explicit operator decision, not a mid-poll-tick patch. Left
  as an explicit open todo below rather than actioned.

- **Resolved 2026-08-15 (cicd escalation agt-f4b815, slot 19) — same recurrence, this time via the `ldr_qg_failure` path
  (promote PR #3180, wall `ldr_main_qg_failure`).** Corpus count had climbed to 2118 (baseline 1639, +479).
  Hand-repaired every currently-flagged file via `fix_prosewrap_padding.py` (content-preserving, `git diff -w` empty
  confirmed) and lowered the baseline to 340 (corrected from this entry's original "329", which didn't match the committed
  `prosewrap_padding_baseline.yaml` value — verified via `git show d71059effe`) — `unified-trading-pm@d71059effe`.
  **6 files were deliberately excluded**
  from this pass because they are already over the hard 1000-line plan cap (`check_line_caps.sh`) and staging them at
  all (even a whitespace-only diff) trips that separate hard gate: `data_completion_defi_2026_07_15.md` (1033L),
  `data_pipeline_check_mdps_features_2026_07_20.md` (1002L), `data_pipeline_reconciliation_skill_2026_07_20.md` (1003L),
  `github_actions_operator_gated_followups_2026_07_17.md` (1006L),
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` (1003L), and
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` (1001L, which also independently trips `check_reference_paths`
  on a pre-existing dangling reference to a `predictions_other_bucket_and_ui_drilldown` doc that no longer resolves).
  Those 6 files' prosewrap debt (329 lines total) remains in the baseline — split them below the line cap first, then
  repair + re-lower the baseline in the same pass.

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-20**: refreshed context_scope (6 entries).

- **2026-08-21 — ruling D117 (proseWrap non-idempotency)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Accept the ratchet — it holds the corpus at 0; fleet-wide prettier blast radius is
  disproportionate to a cosmetic bug. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
  Applied: retagged the sole remaining `[OPERATOR]` todo above to DEFERRED-BY-DESIGN.
