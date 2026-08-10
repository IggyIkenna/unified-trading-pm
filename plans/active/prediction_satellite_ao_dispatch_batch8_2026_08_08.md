---
doc_type: plan
title:
  Prediction satellite AO batch 8 — the one genuinely new orphan since batch7 (line-cap remediation for
  prediction_cross_venue_arb_and_coverage's Progress Log)
summary: >-
  Eighth AO-dispatch batch for prediction, produced by the `/ag-closeout-audit prediction` scheduled run 2026-08-08
  (ag_closeout_auditor, slot 4, dispatch agt-15e876). Live re-run of `generate_ag_closeout_audit_candidates.py --tranche
  prediction --json` found `total_members=38` (down from 41 on 2026-08-07 — 3 previously-covered docs archived/resolved
  in the interim, including the just-archived `candle_feature_canonical_path_divergence_2026_07_20.md` that had sat in
  the never-cited list since 07-31), `never_cited_count=13` (unchanged headline count — the same 12 prior basenames
  minus 1 archived, plus 1 new). Cheap frontmatter re-verification confirmed all 12 carryover candidates unchanged (same
  multi-AG `asset_group` markers, same `status`) — genuinely cross-cutting, correctly excluded again, no full Phase-1
  re-read needed per the skill's iterative-drain guidance. A fresh independent Phase-1 classification (one agent) on the
  single genuinely new candidate —
  `/plans/archive/2026_08/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md` (filed 2026-08-07 by a
  concurrent na-eligibility-audit pass, one day after the last full audit, so no prior round could have seen it) — found
  it singly-tagged `asset_group: [prediction]` (not multi-AG), zero coverage in any of the 11 covering plans or
  elsewhere in the corpus, and a bounded AO-eligible fix (extract a closed Progress Log section from
  `prediction_cross_venue_arb_and_coverage_2026_07_24.md` to clear the 1000-line hard cap it's sitting at). The
  classifying agent's first-pass verdict leaned `exclude_cross_cutting` on a "generic tooling, not domain work"
  substance argument; this run overrode that to `orphaned_never_touched` because — unlike the 12 carryover exclusions,
  which all carry 4-6 real `asset_group` markers and so remain visible to several OTHER tranches' own audits even when
  prediction's excludes them — this doc carries only the single `prediction` tag, so excluding it here would make it
  invisible to every tranche's candidate discovery permanently (no `cross-cutting`/`ao`/`ci`/`infrastructure` tag for
  any other tranche to pick it up on), which is exactly the invisible-orphan failure the skill's own Orthogonality HARD
  CHECK exists to prevent. Conflict-checked clean (nothing else claims this exact fix — one adjacent doc merely
  cross-references it as "already independently tracked... needs an operator/committer to execute it"). `status: draft`
  — a skill-drafted AO batch is never auto-shipped; flipping to `active` to dispatch is an operator decision.
status: active
nature: process
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-8, plan-hygiene, line-caps]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch8_2026_08_08_finalize.md,
    /plans/archive/2026_08/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_satellite_ao_dispatch_batch7_2026_08_04.md,
    /plans/archive/issues/ag_closeout_audit_prediction_parked_2026_08_08.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_08/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/task_template.md,
    scripts/plan-hygiene/check_line_caps.sh,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit prediction` scheduled run 2026-08-08 (ag_closeout_auditor, slot 4, dispatch agt-15e876). Phase 0
  re-ran `generate_ag_closeout_audit_candidates.py --tranche prediction --json` (38 members, 13 never_cited, net +1 new
  vs the 2026-08-07 baseline after 1 carryover archived off the list). Phase 1: cheap frontmatter re-verification of the
  12 carryover exclude_cross_cutting docs (all unchanged) + one independent-agent classification of the 1 genuinely new
  candidate, whose verdict this run corrected from the agent's own `exclude_cross_cutting` to `orphaned_never_touched`
  (see summary for why — the single-AG-tag visibility argument). Phase 3 conflict-checked the one genuine orphan against
  all 11 covering docs plus the one adjacent doc that name-drops it
  (`context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md`, which defers execution rather than claiming it).
---

# Prediction satellite AO batch 8 — line-cap remediation for `prediction_cross_venue_arb_and_coverage`

> **APPROVED 2026-08-08 (operator, interactive) — flipped `status: draft` → `active`.** Now ingested and dispatchable.
> Drafted autonomously 2026-08-08 by the scheduled `ag_closeout_auditor` role; see `## Operator approval gate` below for
> what approving this meant.

## Why this batch exists

Every prior round (batch1-7, native_ao_extract, the 4 Phase A-E children) has already triaged and either dispatched or
correctly deferred the rest of prediction's corpus — this run's own re-audit confirms the same 12 `never_cited`
carryover candidates (11 unchanged since 07-31 + 1 unchanged since 08-04/08-06/08-07) are still, unchanged, genuinely
cross-cutting multi-AG docs (owned by no single tranche's batch, correctly excluded — see this run's own
`ag_closeout_audit_prediction_parked_2026_08_08.md` for the full per-doc reasoning). The corpus is well-drained. The ONE
new gap is a single doc created 2026-08-07 — the day after the last full audit ran (2026-08-06/07) — so no prior round
could plausibly have seen it, plus it is genuinely singly-tagged `[prediction]` so no other tranche's audit will ever
discover it either (see the frontmatter summary's reasoning on why this classifies `orphaned_never_touched`, not
`exclude_cross_cutting`, despite the fix mechanism being domain-agnostic doc surgery).

## Todos

- [x] ✅ [DOC] P2. **Extract the oldest fully-closed dated Progress Log section from
      `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` into a dated `_history_2026_08.md` archive
      doc**, clearing the 1000-line hard cap it is currently sitting at (999 lines as of 2026-08-08, `wc -l` — it was
      1000 exactly on 2026-08-07; re-measure current line count and current open-item line numbers first, they shift
      commit-to-commit). As of 2026-08-08 the doc's 3 open checkboxes live at lines 172 (`[OPS] P2` tarball-overwrite
      race), 380 (`[DESIGN] P1` fixture-pairing residual), and 702 (`[SCRIPT] P1` e2e-testing series-scoped historical
      backfill) — re-verify via `grep -nE '^\s*[-*] \[ \]'` before picking an extraction range, since these are stale
      the moment any edit lands. Per `task_template.md` finding J: pick the oldest fully-closed dated Progress Log
      sub-section(s) in the doc's `## Progress Log` range, confirm the candidate range contains NONE of the current
      open-item lines, confirm no LATER Progress Log entry references content inside the candidate range by
      pointer/description, then extract that range verbatim into
      `plans/archive/2026_08/prediction_cross_venue_arb_and_coverage_history_2026_08.md` (`status: complete`,
      `nature: record`, 0 open todos) and leave a one-line pointer in its place. **Done when**: `wc -l` on the source
      doc is back under 500 (the soft cap, not just barely under the 1000 hard cap — so this doesn't recur in 2-3
      weeks), `bash scripts/plan-hygiene/check_line_caps.sh` still passes for both the source doc and the new history
      doc, every open checkbox that existed before the extraction still exists verbatim in the source doc afterward
      (diff the open-item line texts before/after, not just the count — 3 items in, 3 items out, byte-identical text),
      and `/plans/archive/2026_08/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md`'s own todo is
      checked off with a commit citation. Repo: unified-trading-pm. Source:
      `/plans/archive/2026_08/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md` (its own todo,
      verbatim).

## Deferred

None — every other `never_cited` candidate this run either re-confirmed `exclude_cross_cutting` (the 12 carryover, all
carrying 4-6 `asset_group` markers spanning multiple/all 5 AGs, none exclusively prediction-scoped in content) or was
already covered. Full per-doc reasoning: `ag_closeout_audit_prediction_parked_2026_08_08.md`.

## Findings surfaced during extraction that are NOT todos here

- **Classification judgment call, resolved in-run (not escalated).** The independent Phase-1 agent's first-pass verdict
  on the source doc was `exclude_cross_cutting` (reasoning: the fix mechanism is generic markdown surgery, not
  prediction-domain work, and two precedent docs with the identical "plan at line cap" problem shape are tagged
  `[meta]`/`[tradfi, prediction]` rather than a single AG). This run overrode that to `orphaned_never_touched` because
  the override criterion the skill actually cares about is VISIBILITY, not domain-relevance-of-mechanism: the 12
  legitimate `exclude_cross_cutting` docs in this tranche all carry enough peer-AG tags that excluding them from
  prediction's batch still leaves them visible to (and correctly handled by) at least one other tranche's own audit.
  This doc carries only `asset_group: [prediction]` — excluding it here would have made it invisible to literally every
  tranche's candidate discovery, forever, which is the exact invisible-orphan failure class the skill's Orthogonality
  HARD CHECK section exists to prevent (it just usually manifests as a dual-tag mistag rather than an under-tag; this is
  the under-tag flavor of the same bug). No operator escalation needed — this was resolvable from the skill's own stated
  design intent, not a genuine two-sided judgment call.
- **Possible retag worth a future look, not actioned here.** If a future audit round wants to reduce recurrence of this
  exact judgment call, `/plans/archive/2026_08/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md`
  could arguably carry an additional `meta` or `ci`/`infra` tag alongside `prediction` (mirroring how
  `mtds_available_at_cross_asset_backfill_2026_07_31.md`-shaped docs get dual-tagged) — but retagging is outside this
  skill's remit (ag-closeout-audit classifies and drafts batches; it does not itself rewrite frontmatter tags except for
  the Orthogonality HARD CHECK's own dual-tag-mistag case, which this isn't). Not filed as a separate issue — low
  stakes, purely a future-convenience note.

## Operator approval gate

Approving this plan means: flip `status: draft` → `active` here (the finalize plan ships `active` from the start — see
`task_template.md` §4's no-double-gate rule). Until then nothing here is ingested or dispatched (`plans/PLAN_FORMAT.md`
— `status: draft` is not ingested). Before flipping, note:

1. **This is a single-todo batch**, mirroring batch7's precedent (also 1 todo) — the prediction corpus is well-drained
   after 7 prior rounds, so a small batch here reflects genuine corpus state, not incomplete triage.
2. **The todo is careful-but-mechanical, not a design call** — the worker must verify (via grep/read) that its chosen
   extraction range excludes the doc's then-current open-item lines and isn't referenced later, but does not need to
   make any judgment about WHICH fix to apply; the fix itself is fully specified by `task_template.md` finding J.
3. **No GCS delete, no VM launch, no wallet/credential action** — pure markdown file surgery inside `unified-trading-pm`
   (create one archive file, trim one active file, verified by `wc -l` + `check_line_caps.sh`). No `[OPERATOR]` tag
   needed under CLAUDE.md's delete-safety rule (nothing irreversible; both files remain in git history regardless).

## Codex SSOTs

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — Phase 3 dispatch-scope eligibility test + conflict-check
  protocol this batch applied.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3 — the shared conflict-check
  protocol.
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual the finalize plan
  will apply once this todo lands (not to this doc yet — it still has open work).
- `/plans/active/task_template.md` finding J — the Progress-Log-extraction recipe this todo follows verbatim.

## Progress Log

- 2026-08-08 (slot 4, ag_closeout_auditor, dispatch agt-15e876): drafted by the `/ag-closeout-audit prediction`
  scheduled run. Phase 0: `generate_ag_closeout_audit_candidates.py --tranche prediction --json` → 38 members / 13
  never-cited (12 carryover + 1 new; 1 prior carryover — `candle_feature_canonical_path_divergence_2026_07_20.md` —
  dropped off the list because it was archived in the interim, confirmed via `find`). Phase 1: cheap frontmatter
  re-verification of all 12 carryover candidates (asset_group array + status byte-identical to the 2026-08-07 snapshot)
  - one independent Agent classification of the 1 fresh candidate (verdict overridden from the agent's own
    `exclude_cross_cutting` to `orphaned_never_touched` — see "Findings surfaced" above for the full reasoning). Phase
    3: conflict-checked the one orphan against all 11 covering docs (0 basename hits for the issue doc itself; the
    source doc's own basename appears in 6 covering docs but always about unrelated substantive prediction-domain todos,
    never the Progress-Log-extraction fix) plus the one adjacent doc that name-drops it
    (`context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md`, which explicitly defers execution — "needs an
    operator/committer to execute it" — rather than claiming it). Extracted the 1 conflict-clear bounded todo. Left
    `status: draft` per the autonomous-mode safety rail — operator flips to `active` to dispatch.
- **2026-08-09 (slot 8, data_engineering, backlog `prediction_satellite_ao_dispatch_batch8-001`)**: todo executed.
  Re-verified premise first (per the todo's own re-verify instruction): source doc was 1013L with only 2 open items
  (lines 172, 380) — the 3rd open item cited in the todo text (line 702, series-scoped historical backfill) had already
  been extracted to `prediction_satellite_ao_dispatch_batch9_2026_08_09.md` earlier the same day, so this run is
  2-in/2-out, not the 3-in/3-out the todo text anticipated. Computed section boundaries for all 15 dated `###` Progress
  Log sub-sections; found 13 fully-closed (0 open checkboxes) vs. the 2 carrying the known open items. Before
  extracting, found one genuine forward-pointer hazard the naive "oldest first" read would have missed: the doc's own
  top 2026-08-04 entry references "this Progress Log's 2026-06-26 entry" by name, so that fully-closed section was
  deliberately LEFT IN PLACE (not extracted) to avoid orphaning that pointer. Also found the last dated section
  (2026-06-27 ~10:10 UTC) had accumulated a long tail of much-more-recent audit-trail bullets (na-eligibility-audit /
  context-scout entries dated 2026-07-30 through 2026-08-09) appended after its narrative content with no new header —
  trimmed the extraction range to the section's true narrative end (line 979 of the original) and left that tail in
  place as current status. Extracted the remaining 12 fully-closed sections (718→684 lines after the 06-27 trim; 0 open
  checkboxes in the extracted content, verified) verbatim into
  `plans/archive/2026_08/prediction_cross_venue_arb_and_coverage_history_2026_08.md`, left a one-line pointer explaining
  what was kept and why. Source doc: 1013L → 339L before the todo-conservation stub index, 376L final (well under the
  500L soft cap). Verified both pre-existing open checkboxes exist byte-identical post-extraction (set-equality check,
  not just count). `check_line_caps.sh`: green (0 new violations; baseline unchanged at 17). **Hit a same-day gate gap
  on first commit attempt**: `check_todo_regression.sh` (migrated into the `safe-doc-push.sh` precommit fast path THIS
  SAME DAY, per its own header) counts TOTAL `- [ ]`/`- [x]` lines and has no exemption for a Finding-J archival
  extraction — moving 25 already-`[x]` items to the archive read as `lost=25`. Same root cause as
  `issues/todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md` (filed same day, different
  trigger) — appended a finding there rather than re-filing. Workaround (not a real fix): appended a 25-line "Extracted
  items index" stub section (one-line `- [x]` pointer per moved item, clearly labeled as a todo-conservation mechanism,
  not live work) so the doc's total checkbox count matches origin (27); source doc final size 376L, still well under the
  500L soft cap. **Also hit + recovered from a `safe-doc-push.sh` patch-loss bug**: the script's prek-patch
  stash/restore (for unstaged files outside the commit scope) saved a patch on its SECOND commit attempt but never
  restored it after the retry succeeded, silently dropping this doc's + the issue doc's checkbox-flip edits from the
  working tree — recovered via `git apply` on the orphaned patch file
  (`~/.cache/prek/patches/1786283053921-3898887.patch`) before this commit. Shipped: unified-trading-pm@afd6891bb3
  (source split + archive doc + stub index); this docs(plans) commit flips this doc's own todo + the source issue doc's
  own todo.
