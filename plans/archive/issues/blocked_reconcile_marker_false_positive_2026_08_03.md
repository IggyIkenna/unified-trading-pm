---
doc_type: issue
title:
  blocked_reconcile's marker-window heuristic auto-answered a genuinely-open [OPERATOR] gate from a worker's own
  unrelated comment
summary: >-
  A worker's own frontmatter comment on an issue doc (documenting a plan-hygiene fix, mentioning a BLK id and separately
  using the word "resolved" in an unrelated sentence, both within the 12-line context window) caused
  agent-orchestrator's blocked_reconcile.py reconciler to auto-answer a BLOCKED question gating a risky
  mass-manifest-mutation todo, even though no actual operator decision existed anywhere in the plans corpus. The
  reconciler nudged the worker to "resume" based on this false positive. Caught before any migration ran; not a
  data-correctness incident, but a real gap in a safety-relevant auto-resolution path.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, blocked-queue, false-positive, safety, reconciler]
related: [/plans/active/issues/tradfi_combo_casing_direction_ssot_contradiction_2026_08_03.md]
created: 2026-08-03
priority: P2
parent_epic: infrastructure_master
assigned_vm: planning
source: [tradfi_combo_casing_direction_ssot_contradiction_2026_08_03.md]
resolved_by: agent-orchestrator@209cd00
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_role: backend_engineer
context_scope:
  [
    agent-orchestrator/server/blocked_reconcile.py,
    /plans/archive/issues/ao_blocked_queue_operator_ruling_sync_gap_2026_07_13.md,
    /plans/active/issues/tradfi_combo_casing_direction_ssot_contradiction_2026_08_03.md,
  ]
---

> **🟢 ARCHIVED 2026-08-03** — `status: resolved`, zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> ACKED-INTO-CODE trigger. Fix: `find_resolution_in_plans()` (`agent-orchestrator/server/blocked_reconcile.py`) now
> requires the resolution marker on the SAME line as the `BLK-xxxxxxxx` mention (option 1 of the recommended decision
> below) — `agent-orchestrator@209cd00`, verified on `origin/live-defi-rollout`, 16/16 tests passing, full repo
> `quality-gates.sh` green.

## What I found

Working `tradfi_combo_casing_direction_ssot_contradiction-003`, I filed a BLOCKED question (BLK-17ef2351) asking whether
to proceed with a risky manifest `--apply` given an unresolved `[OPERATOR]` P0 casing-direction todo (`-001`, still
`status: blocked` in the live backlog). While waiting, I added a frontmatter comment to the same issue doc explaining a
`sequential: true` plan-hygiene fix, which happened to mention `BLK-17ef2351` and, five lines later in an unrelated
sentence, the standalone word "resolved" ("...only makes sense once -001..-003 are resolved").

`agent-orchestrator/server/blocked_reconcile.py`'s periodic sweep scans the plans corpus for any line mentioning a
`BLK-xxxxxxxx` id, then checks a `+/-12` line window around it for one of four marker words (`answered`,
`operator ruling`, `operator ruled`, `resolved`). My comment satisfied both conditions — the BLK id and, within the
window, the bare word "resolved" — despite the doc containing zero actual decision content. The reconciler called
`answer_blocked()`, unblocked my slot, and tmux-nudged me: "Operator ruling synced from the plans corpus answered your
BLOCKED question (BLK-17ef2351) — check your messages now and resume." I verified via `GET /api/backlog` that `-001` was
still `status: blocked, done_sha: null` — no real ruling exists — and did not resume the migration.

## Why it matters

This reconciler exists specifically to auto-resolve BLOCKED questions from plan-doc prose
(`ao_blocked_queue_operator_ruling_sync_gap_2026_07_13`), and its own docstring already acknowledges the false-positive
risk it is trying to bound ("Deliberately conservative matching... a bare mention of a BLK id never matches — only a
mention that ALSO carries a resolution marker"). The bound is a 12-line proximity window with 4 fairly common words, not
adjacency to the BLK id itself — and a worker's own routine progress-note prose (discussing the SAME unresolved gate the
BLK id was filed for) can easily contain one of those 4 words within 12 lines, exactly because workers narrate
pending/unresolved state using words like "resolved"/"ruling". In this instance the gated action was a mass
manifest-casing rewrite already flagged in its own issue doc as having been blindly re-run twice in opposite directions
— a worker with less caution than "verify -001's live backlog status before trusting the nudge" would have executed a
THIRD blind flip of ~1.3M production rows based on a false signal.

## Recommended decision

Tighten `find_resolution_in_plans()` (agent-orchestrator/server/blocked_reconcile.py) so proximity alone is insufficient
— options, not mutually exclusive:

1. Require the marker on the SAME line as the BLK id mention (not a 12-line window), or
2. Require an explicit compound pattern immediately adjacent to the BLK id (e.g. `BLK-xxxxxxxx ANSWERED` /
   `ANSWERED — BLK-xxxxxxxx`, mirroring the convention the docstring already cites:
   `"BLK-d48acae4 ANSWERED — checkbox flipped"`), rather than any one of 4 generic words anywhere nearby.

Either tightens the false-positive rate without reintroducing the original sync gap (an operator still writes one line
near the BLK id; workers narrating unrelated pending state stop tripping it).

- [x] ✅ [BACKEND] P2. Tighten `find_resolution_in_plans()`'s marker-matching in
      `agent-orchestrator/server/blocked_reconcile.py` per the recommended decision above (same-line requirement, or an
      explicit `BLK-xxxxxxxx ANSWERED` / `ANSWERED — BLK-xxxxxxxx` compound pattern) — add a regression test asserting a
      nearby-but-unrelated use of "resolved"/"answered"/"operator ruling"/"operator ruled" does NOT auto-answer an open
      BLK id. (repo: agent-orchestrator) — `agent-orchestrator@209cd00`.

## Progress Log

- 2026-08-03 (slot-8): filed after `tradfi_combo_casing_direction_ssot_contradiction-003`'s own BLOCKED question
  (BLK-17ef2351) was auto-answered by this exact mechanism from my own unrelated comment; corrected the triggering
  comment in that doc (removed the standalone "resolved" near the BLK id mention) in the same commit. No
  agent-orchestrator code changed yet — this doc only.
- 2026-08-03 (slot-14): implemented option 1 (same-line requirement) — `find_resolution_in_plans()` now requires the
  resolution marker on the SAME line as the `BLK-xxxxxxxx` mention; the +/-12 line window is kept only for assembling
  the displayed context text, not for match detection. Verified against the live plans corpus (grepped real `BLK-` usage
  across `plans/active/`) that this preserves every genuine same-line match convention already in use
  (`BLK-xxxx ANSWERED`, `operator ruling BLK-xxxx`, etc.) while closing the cross-line false-positive. Updated
  `test_matches_operator_ruling_marker_within_window` (renamed, expectation flipped to non-match — that test validated
  exactly the loose-window behavior being removed) and added a dedicated regression test reproducing the live incident
  shape (BLK id + unrelated "resolved" 5 lines later). Full suite: 16/16 passed locally; `agent-orchestrator@209cd00`
  shipped via quickmerge, verified on `origin/live-defi-rollout`. Full repo `quality-gates.sh` green (2271 passed, 2
  skipped; dashboard tsc/vitest green).
- **context-scout 2026-08-03**: populated context_scope (3 entries) — the reconciler source file (fix target), the issue
  doc that originally built this mechanism (design-intent context for the recommended tightening), and the triggering
  doc where the false positive fired.
