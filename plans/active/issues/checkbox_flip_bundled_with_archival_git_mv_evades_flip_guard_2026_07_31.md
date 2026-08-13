---
doc_type: issue
title:
  the cross_repo_pm_file_touched_no_checkbox_flip guard structurally misses a plan/issue checkbox-flip that is bundled
  into the SAME commit as the doc's archival git-mv (rename-similarity pairing masks it)
summary: >-
  The automated `cross_repo_pm_file_touched_no_checkbox_flip` rejection (which enforces the Commit-Push-Flip HARD RULE
  by rejecting a PM-file-touching `/done` that carries no plan checkbox flip) depends on git's default rename-similarity
  heuristic still pairing the old→new path of an archived plan/issue doc. When a worker bundles the checkbox-flip edit
  INTO the same commit as the archival `git mv` (doc moved to `plans/archive/…`), and the combined rename+content diff
  stays above git's ~50% similarity threshold (observed ≥86% both times), git reports it as a single rename and the
  guard reads the flip as "present on the renamed file" — so it never fires. The result: this specific commit-sequencing
  anti-pattern (flip + archival mv in ONE commit) is structurally invisible to `slot_done_rejected_no_plan_flip`
  whenever the archival diff happens to stay small, i.e. the counter can never reliably catch it. Surfaced by the review
  role (msg 2939) after slot 5 did it TWICE in one session (~15-20 min apart: bfd1194dc `sharded_per_tranche` doc, then
  ae19b3fd0 `quickmerge_agent_regate_resets_branch_loses_local_commit` doc) despite a direct peer ping after the first —
  informal coaching demonstrably did not stick within-session. The underlying shipped work was fully correct both times
  (review-verified); this is purely a commit-sequencing-discipline + detection-coverage gap, not a data/correctness
  harm.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer]
tags: [commit-push-flip, plan-hygiene, quality-gates, prek, detection-gap, archival, git-mv, tooling]
related:
  [
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-31
author: unknown
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
drift_direction: advance-code
depends_on: []
source:
  [
    "Flagged 2026-07-31 08:49Z by the review role (msg 2939) to main-agent (agt-9f21bc) as a non-blocking FYI after
    observing slot 5 combine a checkbox-flip with an archival git-mv in one commit twice in a single session (bfd1194dc,
    ae19b3fd0), with the cross_repo_pm_file_touched_no_checkbox_flip guard failing to fire either time (checked
    /api/activity both times) because git's rename-similarity heuristic kept pairing old→new path.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/issues/ao_m3_verify_plan_flip_blind_to_archival_rename_2026_07_26.md,
    agent-orchestrator/server/verify.py,
  ]
---

# checkbox-flip bundled with archival git-mv evades the no-flip guard

## What was found (review role, msg 2939, 2026-07-31 08:49Z)

The `cross_repo_pm_file_touched_no_checkbox_flip` rejection is the mechanical enforcement of the Commit-Push-Flip HARD
RULE (`/codex/12-agent-workflow/commit-push-flip-rule.md`): a slot's `/done` that touches a PM plan/issue file but
carries no plan checkbox flip is rejected (`slot_done_rejected_no_plan_flip`). Its check depends on being able to see
that the flipped file is the one that was touched.

The gap: when a worker **archives** a plan/issue doc (moves it to `plans/archive/…` via `git mv`) AND performs the
checkbox flip **in the same commit**, git represents the change as a single rename-with-modification. As long as the
combined rename+content diff stays above git's default rename-similarity threshold (`git diff` pairs renames at ~50%
similarity; observed ≥86% in both incidents), the guard sees the flip "on the renamed file" and does not fire — even
though the intended separate, auditable flip step never happened as its own unit.

This makes the anti-pattern (flip + archival mv in ONE commit) **structurally undetectable** by the current counter
whenever the archival diff is small enough to keep the rename pairing intact — it is incidental per-diff luck, not
something the HARD RULE ban can rely on.

Observed instances (slot 5, same session, ~15-20 min apart; both underlying shipments **review-verified correct**):

- **bfd1194dc** — `sharded_per_tranche` doc archival. Review pinged slot 5 directly afterward.
- **ae19b3fd0** — `quickmerge_agent_regate_resets_branch_loses_local_commit` doc archival. Review pinged slot 5 again.

Informal coaching did not change the behavior within the session — hence the request for a mechanical check rather than
repeated per-incident coaching.

## Why it matters

- The Commit-Push-Flip rule's mechanical guard has a blind spot that is invisible in the normal case and only shows up
  on archival commits — exactly the commits where flip-accuracy matters (a plan is being closed out).
- It is a detection-coverage gap, not a correctness gap: no data harm, no operator-visible harm, work shipped correctly.
  So it is genuinely low priority — flagged so it is tracked mechanically rather than lost as prose.

## Recommended decision (priority is the operator's / plan-owner's call — this is non-blocking)

- **(A) Mechanical QG/prek rule** — add a check that detects a rename (`git mv` into `plans/archive/…`) combined with a
  content diff to a plan/issue doc in the SAME commit, and either (a) rejects it, requiring the flip to have landed in a
  prior commit before the archival mv, or (b) parses the renamed-file diff hunks to confirm the checkbox actually
  flipped (so the guard no longer relies on the rename pairing being absent). Option (b) closes the detection gap
  without changing the allowed workflow; option (a) additionally enforces flip-before-archive sequencing.
- **(B) Lower `git diff` rename-similarity for the guard's own check** — run the guard's diff with a stricter
  `-M`/`--find-renames` threshold (or `--no-renames`) so a bundled flip+mv no longer reads as a clean rename and the
  existing no-flip logic fires. Cheapest, but may produce false positives on legitimate large-content renames.
- **(C) Accept + document** — if the operator judges the coverage gap not worth a rule, document in the codex
  commit-push-flip SSOT that the guard does not cover flip+archival-in-one-commit, so future readers do not assume it
  does.

## Todos

- [ ] [BACKEND] P3. **DECIDED 2026-08-08 (operator ruling, NA-corpus blocker digest round 5, id=56): option (B)** —
      tighten the `cross_repo_pm_file_touched_no_checkbox_flip` guard's own rename-similarity threshold. Scoped the
      exact fix by reading the live guard (it does NOT live in `unified-trading-pm/scripts/` — the literal string
      `cross_repo_pm_file_touched_no_checkbox_flip` is a `reason` value emitted from `check_plan_flip()` in
      `agent-orchestrator/server/verify.py:1385`, line 1700). **Root mechanism**: four sibling diff-shape checks —
      `_diff_flips_checkbox` (verify.py:865, git call :890), `_diff_cancels_checkbox` (:915/:936),
      `_diff_defers_checkbox` (:961/:976), `_diff_blocks_checkbox` (:1001/:1028) — all run
      `git show --unified=0 --no-color --format= <sha> -- <path>` with NO `-M`/`--find-renames`/`--no-renames` flag, so
      git's default `diff.renames=true` (~50% similarity threshold) pairs a bundled archival-rename+flip commit as a
      clean rename and only prints the changed hunks against the OLD path — a similarity-%-dependent knife-edge, not a
      deterministic check. **Concrete fix**: add `"--no-renames"` to the `git show` argv at verify.py lines 890, 936,
      976, 1028 — forces every archival git-mv+edit commit to present as delete+add regardless of similarity%, routing
      ALL bundled-flip commits through the already-hardened content-based fallback (`_flips_at_path_or_rename` →
      `_same_commit_added_path_matching_basename` → `_archival_rename_disposition`, verify.py:1053-1206) instead of the
      size-dependent hunk-diff path. No existing test currently exercises rename-similarity
      (`agent-orchestrator/tests/test_done_gate_plan_flip_hard_reject.py`) — add one pinning a bundled-rename+flip
      commit is still detected post-fix. **NOT implemented this session** — the actual code change is in
      `agent-orchestrator`, out of this session's edit scope (unified-trading-pm only); filed here as a fully-scoped,
      ready-to-implement todo citing exact file:line targets so the next agent-orchestrator session can ship it
      directly. Confirm the fix against the bfd1194dc / ae19b3fd0 commit shapes once implemented. (repos:
      agent-orchestrator)

## Progress Log

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

- 2026-07-31 08:49Z (main-agent agt-9f21bc): filed from review-role msg 2939. Non-blocking, work shipped correct both
  times, pure detection/sequencing-discipline gap → P3. Set `assigned_vm: NA` per the ASK-BEFORE-CREATING hard rule;
  operator can flip `assigned_vm: planning` + `execution_scope` to auto-dispatch the (precisely-scoped) todo once a
  decision between (A)/(B)/(C) is made — the decision itself is the operator/plan-owner call, so it stays NA until then.
- 2026-07-31 10:20Z (main-agent agt-9f21bc): review role re-confirmed (msg 2948) both incidents via direct
  git-show-at-old-path reproduction and noted the SECOND occurrence (ae19b3fd0) landed ~13 min AFTER a direct coaching
  ping about the first (bfd1194dc) — i.e. a same-session repeat survived verbal mitigation. This strengthens the case
  for option (A) mechanical guard over verbal-only coaching. Priority held at P3 / NA (operator's dispatch call);
  operator NOT re-paged (already noted once). Escalation bar recorded: a THIRD in-session recurrence → bump priority.
- **na-eligibility-audit 2026-08-01**: KEEP-NA, valid -- Full audit rationale: The single open todo explicitly requires
  a prior human/operator decision among three named design options (A/B/C — mechanical QG/prek rule vs. tightened
  rename-similarity threshold vs. accept-and-document) before any implementation step is determinable. The doc's own
  Progress Log states the decision...
- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **context-scout 2026-08-03**: re-verified context_scope (3 entries) — already minimal + source-anchored (`verify.py`
  is confirmed to be the actual guard implementation), left unchanged.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (3 entries), unchanged.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-08-01 (unchanged): sole todo requires an
  operator/plan-owner decision among 3 named options (A/B/C) before the implementation step is determinable.
- **context-scout 2026-08-07**: refreshed context_scope (4 entries, was 3) -- added
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (cited in `related:` but missing from
  context_scope -- this doc is specifically about the archival-git-mv + checkbox-flip interaction, so the archival
  discipline SSOT is as load-bearing as the commit-push-flip one already there).
- **na-eligibility-audit 2026-08-07 (cross-cutting tranche)**: KEEP-NA, valid — reaffirmed, unchanged. Sole open todo
  still requires an operator/plan-owner decision among the 3 named options (A/B/C) before an implementation step is
  determinable; no new information since 2026-08-06.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.
