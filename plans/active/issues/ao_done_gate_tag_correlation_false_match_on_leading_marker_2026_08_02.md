---
doc_type: issue
title:
  "AO /done M3 tag-correlation fallback false-matched an unrelated checked todo when a checkbox is retagged with a
  leading BLOCKED-<TOKEN> marker"
summary: >-
  agent-orchestrator/server/verify.py's `_brief_is_checked_by_tag_in_text` (the M3 plan-flip verification's
  tag+priority-correlated fallback) requires a task's `brief` string to start with the exact `[TAG] P<n>.` prefix
  (`_TODO_TAG_PRIORITY_RE = re.compile(r"^\[(.+?)\]\s+P(\d+)\.")`). When a checkbox is retagged with a marker placed
  BEFORE the tag (e.g. `- [ ] BLOCKED-UPSTREAM-DESIGN [DATA] P2. ...` — the convention slot-12 used, non-standard vs.
  this corpus's usual marker-AFTER-tag placement), two independent bugs surface: (1) for the ORIGINAL pre-retag task,
  the fallback spuriously correlates against ANY OTHER checked `[x] [TAG] P<n>.` line sharing the same tag+priority
  anywhere in the doc, even if it's a completely unrelated todo — confirmed live: task
  `canonical_path_oracle_blind_to_filename_stem-002`'s `/done` (slot-12, `unified-trading-pm@5f00baeed`, retag-only
  commit, checkbox correctly left `[ ]`) was accepted as `checkbox_checked_tag_correlated` solely because the SAME doc
  has an unrelated `- [x] [DATA] P2. Decide the id grammar for defi...` line at L304 sharing the `[DATA] P2.` prefix — a
  false-positive completion signal, not a real correlation to THIS todo. (2) for the NEXT regen'd task off the SAME
  already-retagged checkbox, the fallback (and its `_marker_disposition_in_text` sibling) can never fire AT ALL, because
  the newly-dispatched task's OWN `brief` now starts with `BLOCKED-UPSTREAM-DESIGN ` (not `[DATA]`), breaking
  `_TODO_TAG_PRIORITY_RE`'s leading-anchor match — confirmed live: task
  `canonical_path_oracle_blind_to_filename_stem-003` (slot-6) hit a hard `409
  cross_repo_pm_file_touched_no_checkbox_flip` on this same checkbox despite the underlying disposition being identical
  (still gated, still correctly unflipped) to -002's accepted case. No plan-doc edit can fix case (2) — `brief` is
  captured at dispatch time, not re-read from the doc.
status: open
nature: issue
asset_group:
  [ao] # corrected 2026-08-04 (ag-closeout-audit ao tranche run) -- was [meta]. Genuinely AO server code
  # (agent-orchestrator/server/verify.py M3 tag-correlation fallback), not a generic process doc.
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [ao-server, m3-verification, done-gate, tag-correlation, false-positive, regen-churn]
related: [canonical_path_oracle_blind_to_filename_stem_2026_07_20]
created: 2026-08-02
author: unknown
assigned_vm: planning
execution_scope: ao-dispatched
priority: P2
parent_epic: agent_operating_framework_master
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: none
source: [worker-session]
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/verify.py,
    agent-orchestrator/tests/test_done_gate_plan_flip_hard_reject.py,
    /plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
---

# AO `/done` M3 tag-correlation fallback: false-match + leading-marker blind spot

## What I found

While closing `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`'s §7 "quarantine/honest-absence disposition"
todo's redispatch churn (separately fixed: `agent-orchestrator@2b0b9e9` added `UPSTREAM-DESIGN` to
`regen_backlog_from_plan.py`'s `_BLOCKED_TOKEN_RE` so the checkbox stops re-entering the backlog), I hit a
`409 cross_repo_pm_file_touched_no_checkbox_flip` on `/done` for task `canonical_path_oracle_blind_to_filename_stem-003`
even though the checkbox is legitimately, deliberately staying `[ ]` (same disposition slot-12's predecessor task `-002`
was accepted for minutes earlier).

Root-caused via `server/verify.py`'s `_brief_is_checked_by_tag_in_text` / `_marker_disposition_in_text`, both gated on
`_TODO_TAG_PRIORITY_RE.match(brief.strip())` matching `brief`'s LEADING characters against `^\[TAG\]\s+P<n>\.`:

- Task `-002`'s `brief` was captured pre-retag:
  `"[DATA] P2. The legitimately-unresolvable objects need a quarantine / honest-absence disposition (separate design)."`
  — starts cleanly with `[DATA]`, so the tag+priority extraction succeeds (`tag="DATA", priority="2"`). The fallback
  then scans the CURRENT doc for any `- [x] [DATA] P2. ...` line — finds exactly one, at L304
  (`"Decide the id grammar for defi..."`, a fully unrelated, genuinely-completed todo) — and reports `hits==1` →
  `checkbox_checked_tag_correlated: True`. This is WRONG: it correlated task -002 to a different todo's completion, not
  evidence that -002's own line changed state.
- Task `-003`'s `brief` was captured post-retag:
  `"BLOCKED-UPSTREAM-DESIGN [DATA] P2. The legitimately-unresolvable objects need a quarantine / honest-absence"` — the
  leading `BLOCKED-UPSTREAM-DESIGN ` token breaks `_TODO_TAG_PRIORITY_RE`'s anchor, so `m` is `None` and the fallback
  returns `(False, False, False)` / `False` immediately, regardless of anything in the doc. Every diff-based check
  (`_diff_flips_checkbox`, `_diff_blocks_checkbox`, etc.) also legitimately fails (the commit that ships the durable fix
  touches a DIFFERENT repo — `agent-orchestrator` — and the PM commit in the same session only appended a Progress Log
  entry, correctly not re-touching the already-retagged checkbox line). Net: a `409`, un-resolvable by any plan-doc
  edit, since `brief` is fixed at dispatch time.

## Why it matters

- **False positive (case 1)** silently accepts a `/done` whose cited commit did NOT actually establish the claimed
  disposition for THAT todo — exactly the failure class `ao_backlog_regen_integrity_2026_07_20.md`'s "checkbox state =
  truth" principle exists to prevent, via an accidental same-tag-priority collision the tag-correlation fallback wasn't
  designed to guard against for this direction (it already fails CLOSED on >1 hit — this is 1 hit, but the WRONG line).
- **False negative (case 2)** blocks a legitimate `/done` for a todo whose disposition is genuinely, correctly unflipped
  — forcing the worker into `/skip-current-task` (this session's resolution) even when real, valuable, shipped work was
  done. Every FUTURE todo retagged with a leading `BLOCKED-<TOKEN>` marker (an increasingly common convention —
  `ao_residuals_after_dispatch_hardening_2026_07_17.md`, `ao_open_issues_consolidated_close_out_2026_07_17.md` use the
  same leading-marker placement) will hit this identical wall.

## Recommended decision

Not a judgment call — this is a mechanical fix to `agent-orchestrator/server/verify.py`, but not one to speculatively
widen without care (loosening `_TODO_TAG_PRIORITY_RE` to tolerate a leading marker would also widen case (1)'s
false-positive surface). Recommend, in order:

1. Fix `_TODO_TAG_PRIORITY_RE` to optionally skip a leading `BLOCKED-[A-Z-]+\s+` / `CANCELLED\s+` / etc. token before
   anchoring on `[TAG] P<n>.` — closes the case-2 blind spot for the (now-common) leading-marker convention.
2. Separately harden `_brief_is_checked_by_tag_in_text` / `_marker_disposition_in_text` against case-1's false positive:
   correlate on a snippet of `brief`'s OWN distinguishing text (not just tag+priority) when more than one
   same-tag-priority line exists in EITHER state (checked or marker) — or, simpler, additionally require the
   checked/marker line's TEXT to share some non-trivial substring with `brief` beyond the shared tag+priority prefix,
   since tag+priority alone is not unique across a doc (this issue doc alone has 6+ `P2.` todos).
3. Add regression tests mirroring both live cases above (same-tag-priority collision against an unrelated checked line;
   a `brief` with a leading BLOCKED-<TOKEN> marker).

## Todos

- [ ] [INFRA] P2. NEW FINDING (2026-08-09, slot 22): `_brief_is_checked_by_tag_in_text` still fails CLOSED (correctly,
      by current design, but too conservatively) when a plan doc has **multiple genuinely different,
      independently-completed** `- [x] [TAG] P<n>.` lines sharing the same tag+priority — `matches` has `len > 1`, so
      the function returns `False` unconditionally at `return len(matches) == 1 and ...` without ever reaching the
      2026-08-02 `_shares_distinguishing_content` hardening (that check only fires when `hits == 1`). Confirmed live:
      `/done` on `defi_dex_pool_swaps_733_row_indexer_health_findings-c4893c5446f8` (task
      `defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md`'s final P2 todo, a genuine self-archival flip
      bundled with the `git mv` per the standard 6-step ritual) 409'd with `cross_repo_pm_file_touched_no_checkbox_flip`
      even though the checkbox WAS genuinely flipped (`market-tick-data-service@5d633923` landed, verified ancestor of
      origin) — the doc has **7** separate `- [x] [DATA] P2.` lines (a large, long-running investigation doc with many
      independently-closed P2 findings), so `_archival_rename_disposition`'s `_brief_is_checked_by_tag_in_text` call on
      the destination blob saw `len(matches)==7` and returned `False` before content-matching could disambiguate.
      **Proposed fix**: when `len(matches) > 1`, apply `_shares_distinguishing_content` against EACH match (not just
      skip straight to `False`) and accept only if EXACTLY ONE match shares distinguishing content with `brief` — same
      fail-closed guarantee on a genuine ambiguity (0 or 2+ content-matching candidates), but stops rejecting a real
      flip just because OTHER, unrelated same-tag-priority todos in the same doc also happen to be checked. Resolution
      for this specific occurrence: no self-service override exists (per the sibling
      `ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md` finding — this class requires an
      operator/main manual DB patch); the underlying work (code shipped + checkbox flipped + doc archived) is
      independently verified via `git merge-base --is-ancestor` on both the code repo and the PM repo, so `/done`
      recovery is a bookkeeping-only gap, not a work-completeness gap. (repo: agent-orchestrator)
- [ ] [INFRA] P2. Widen `_TODO_TAG_PRIORITY_RE` (or add a preprocessing strip) so a `brief`/plan line with a leading
      `BLOCKED-<TOKEN>` (or similar) marker before `[TAG] P<n>.` still extracts tag+priority correctly. Add a regression
      test using a brief like `"BLOCKED-FOO [DATA] P2. ..."` (an arbitrary marker-shaped token — the bug is about
      position relative to `[TAG] P<n>.`, not the specific token's semantics). (repo: agent-orchestrator)
- [x] ✅ [INFRA] P2. **DONE 2026-08-02 (slot-6) — `agent-orchestrator@3511af4`.** Hardened both
      `_brief_is_checked_by_tag_in_text` and `_marker_disposition_in_text`: a `hits == 1` tag+priority correlation now
      also requires at least one shared length->=6 word between `brief`'s own text and the matched line's text (both
      taken after the shared `[TAG] P<n>.` prefix) via a new `_shares_distinguishing_content` helper. Falls back to the
      prior accept-on-`hits==1` behavior when `brief` itself carries no such word (e.g. the test suite's generic
      `"do the thing"` fixtures), so no regression to the existing self-archival / paragraph-reword acceptance tests
      (full `test_done_gate_plan_flip_hard_reject.py` suite green, 35/35, including all pre-existing tag-correlation
      cases). Added 2 new regression tests: `test_done_rejects_cross_repo_when_tag_correlation_matches_unrelated_todo`
      (mirrors the live L304/`canonical_path_oracle_blind_to_filename_stem-002` false positive — must 409) and
      `test_done_accepts_cross_repo_when_tag_correlation_content_matches` (genuine reworded+annotated correlation still
      accepts). Full `quality-gates.sh` green (2228 passed), verified on origin/live-defi-rollout.
- [x] ✅ [INFRA] P3. **Guard /done's reported sha against the evidence-text's own cited commit (is-ancestor alone is not
      enough).** — agent-orchestrator@0d449c6. Fix already landed: `verify.resolve_sha_in_worktree()` +
      `sha_evidence_mismatch` warning in `done_slot`, cross-checks evidence-cited `<repo>@<sha>` against reported sha, +
      200-line regression test (`test_done_gate_sha_evidence_mismatch.py`). Originated from slot-8's orphaned `3080fec`,
      cherry-picked + QG'd to LDR as `0d449c6`. Review (Tick 10, 2026-08-03, chat msg 3423) found task
      defi_consolidated_native_ao_extract-003 (slot 7) self-reported /done sha=77c0206, which was actually a DIFFERENT
      slot's unrelated commit (slot 12's infra_satellite_ao_dispatch_batch2-001, landed 28s later, same repo). The
      durable record was CORRECT (slot 7's real work at 72ea669, author=slot-7, content matches the evidence text, and
      the plan-flip cites 72ea669), so this was contained to the raw /done API payload's sha field. Blind spot: 77c0206
      is a genuinely valid origin ancestor, so the M3 is-ancestor check alone silently PASSES on the wrong commit.
      Harden /done to cross-check the reported sha against the commit cited in the evidence text and/or an
      author==reporting-slot check, not just is-ancestor. Low severity (no incident; durable record was right). Repo:
      agent-orchestrator. Source: review Tick 10.

## Progress Log

- **slot-6 2026-08-02**: filed after hitting the case-2 blind spot closing
  `canonical_path_oracle_blind_to_filename_stem-003`; empirically reproduced case-1's false positive by re-running
  `verify.check_plan_flip` against slot-12's real `unified-trading-pm@5f00baeed` commit. Resolved my own session via
  `/skip-current-task` (task correctly stays un-completable via `/done` as scoped; the substantive churn-fix is already
  shipped and logged in `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`'s Progress Log).
- **slot-6 2026-08-02**: dispatched todo 2 (`ao_done_gate_tag_correlation_false_match_on_leading_marker-001`). Shipped
  `agent-orchestrator@3511af4` — see the flipped checkbox above for the fix summary. Todo 1 (widen
  `_TODO_TAG_PRIORITY_RE` for a leading marker) remains open, unassigned to this task.
- **context-scout 2026-08-03**: populated context_scope (3 entries).
- **context-scout 2026-08-03 (re-pass, updated methodology)**: added
  `agent-orchestrator/tests/test_done_gate_plan_flip_hard_reject.py` (the regression-test home both remaining `[INFRA]`
  todos need to extend, per the shipped todo 2's own evidence line) — now 4 entries.

- [x] ✅ [INFRA] P3. **Land the orphaned commit that already IMPLEMENTS the `[INFRA] P3` guard-/done-sha-vs-evidence
      todo — agent-orchestrator@0d449c6 above — do NOT re-implement it.** Dead slot-8 (died 2026-08-04T09:11:01Z) left
      `agent-orchestrator@3080fecd7da9` "feat(done): cross-check /done reported sha against evidence-cited commit" — the
      full fix (`verify.resolve_sha_in_worktree()` + a ~200-line regression test), preserved on origin at
      `refs/heads/wip-preserve/orchestrator-slot-8-3080fec` (also still in `.tabs/8/agent-orchestrator`, clean tree,
      ahead=1). Its `Quickmerge:agent` trailer is pre-stamped but Pass-1 QG never actually ran on it
      (`.qg_last_passed_sha` = parent `2e5792b`, not `3080fec`), so `quickmerge --agent` will refuse until QG re-runs.
      Action for a worker (NOT main — this is code, and main cannot push code): either inherit slot-8's dead worktree
      per the LIVENESS-gated inherited-dirty-WIP rule (dead claim, safe) or cherry-pick the wip-preserve ref, run a
      fresh Pass-1 `quality-gates.sh`, then `quickmerge.sh --agent`. Once landed, flip the `[INFRA] P3` guard-/done-sha
      todo above to `[x]` and **unpark `ao_done_gate_tag_correlation_false_match_on_leading_marker-002`** (main parked
      it 2026-08-04 to stop a fresh worker duplicating this exact fix — condition
      `auto_unpark__ao_done_gate_tag_correlation_false_match_on_leading_marker-002`). Repo: agent-orchestrator.

- **2026-08-04 (main agt-1756f6, from review #3680)** — Orphan-WIP dedup. Review flagged that dead slot-8's unpushed
  `3080fec` already implements the `[INFRA] P3` guard-/done-sha todo above, while its originating task
  `ao_done_gate_tag_correlation_false_match_on_leading_marker-002` had `resume_decision=requeue` (back in the backlog) —
  a fresh worker would duplicate or collide with it. Verified read-only: slot-8 dead, `3080fec` present in
  `.tabs/8/agent-orchestrator` (clean, ahead=1) AND preserved on origin at `wip-preserve/orchestrator-slot-8-3080fec`
  (so the work is SAFE, not lost — the watchdog preserve-half fired). Main PARKED task `-002` (`/api/backlog/.../park`,
  condition `auto_unpark__…-002`) to stop the duplication — within main's authority (RULES.md §4). Did NOT land
  `3080fec` (code — main never pushes code); filed the landing as the tracked `[INFRA]` todo above for a worker to pick
  up.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate.
