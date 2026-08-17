---
doc_type: issue
title: data_completion_tradfi_2026_07_15.md sits exactly AT the 1000L hard cap — even a marker-only append is blocked
summary: >-
  na-eligibility-audit (tradfi tranche, 2026-08-16) verified that data_completion_tradfi_2026_07_15.md's E7 todo
  (verify-then-delete legacy market-data-tick-tradfi) was already extracted to a real, live, active
  tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16.md doc — the checkbox should close. But the source doc is
  EXACTLY 1000 lines (git show HEAD, 2026-08-16), the hard cap, not over it. check_line_caps.sh's marker-only and
  link-repoint SCOPED-mode carve-outs both require the file to be "already over the hard cap before this commit" —
  a doc sitting exactly AT the boundary does not qualify, so even a 5-line, zero-deletion, no-new-checkbox append
  was refused (`plan-hygiene` pre-commit, `check_line_caps`). This is a real, previously undocumented gap in that
  carve-out's boundary condition: any doc that reaches exactly 1000 lines becomes permanently frozen against even
  the cheapest maintenance edit (a dated audit marker) until someone runs a real split — worse than the "over cap"
  case, which at least has the marker carve-out.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, plan-hygiene, line-cap, check_line_caps, na-eligibility-audit, blocked-mechanical]
related:
  [
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
parent_epic: tradfi_master
source: "na-eligibility-audit, tradfi tranche, dispatch agt-45ad7b, 2026-08-16 — hit live while trying to close a
  verified-stale E7 item"
assigned_vm: NA
created: 2026-08-16
resolved_by:
locked_by:
locked_since:
priority: P2
execution_scope: local-only
drift_direction: advance-docs
depends_on: []
context_scope: [/plans/active/data_completion_tradfi_2026_07_15.md, scripts/plan-hygiene/check_line_caps.sh, /codex/12-agent-workflow/plan-completion-and-archival-discipline.md]
---

# data_completion_tradfi_2026_07_15.md is AT (not over) the 1000L hard cap — blocks even a marker-only edit

## What happened

Verified live that `data_completion_tradfi_2026_07_15.md`'s E7 todo ("verify CF-1..CF-12 GREEN, then delete legacy
`market-data-tick-tradfi` + bulk-delete 12 placeholder prefixes") was extracted to
`/plans/active/tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16.md` — that doc exists, `status: active`,
`assigned_vm: planning`, and its own todo cites `Source: data_completion_tradfi_2026_07_15.md E7 (line 211)`. The
E7 checkbox should close to match.

`git show HEAD:plans/active/data_completion_tradfi_2026_07_15.md | wc -l` = exactly **1000** lines — the hard cap,
not over it. A minimal, zero-deletion, no-new-checkbox, 5-line marker append (checkbox flip reverted to a pure
blockquote note, plus one short Progress Log line) still pushed the file to 1003-1013 lines depending on how
compact the note was, and `check_line_caps.sh`'s SCOPED mode refused every attempt.

Re-reading the carve-out rules in `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (the
marker-only append and same-line link-repoint sections): both explicitly require **"The file must already be over
the hard cap before this commit (a doc newly crossing the cap is NOT covered)."** A file sitting exactly at 1000 is
not "over" — it is AT the boundary — so neither carve-out's precondition is met, and the very first line added
(regardless of content) is "newly crossing the cap." This is a real gap: a doc at the boundary is effectively
WORSE off than one already over it, since the over-cap case at least has an escape hatch for cheap maintenance
edits.

## What was NOT done

Did not force the edit through, did not delete unrelated content just to make room, did not split the doc myself
(a real content decision about how to divide 1000L of dense tradfi history, better suited to a dedicated
`/plan-reconcile` or manual split pass than an incidental fix inside an unrelated audit run). Reverted all edits to
this file cleanly (`git checkout --`, verified clean, 1000L).

## Recommended decision

1. **Split `data_completion_tradfi_2026_07_15.md`** the same way `tradfi_consolidated_closeout_2026_07_18.md` was
   split on 2026-07-24 (see `plan_line_cap_remediation_2026_07_23.md`) — it is a similarly dense, long-running
   tradfi tracker and a natural candidate. Once split, each child will have headroom for ordinary maintenance
   markers again.
2. **Separately, consider whether `check_line_caps.sh`'s carve-out preconditions should read `>= 1000` instead of
   `> 1000`** so a doc sitting exactly at the boundary isn't worse-positioned than one already over it — a design
   call for whoever owns that script, not decided here.
3. **Once either fix lands**, close `data_completion_tradfi_2026_07_15.md`'s E7 checkbox (line 211) citing
   `tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16.md` — the underlying fact (extraction is real and live) is
   already verified, only the mechanical flip is blocked.

## Todos

- [ ] [DOC] P2. Split `data_completion_tradfi_2026_07_15.md` (or fold its content into a fresh child the same way
      the 2026-07-24 line-cap remediation did for its sibling `tradfi_consolidated_closeout_2026_07_18.md`), so it
      has headroom under the 1000L hard cap again. Done when: the doc (or its split children) are back under 1000L
      and the E7 checkbox closes citing `tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16.md`.
- [ ] [SCRIPT] P3. Confirm with the `check_line_caps.sh` owner whether the marker-only/link-repoint carve-outs'
      "already over the hard cap" precondition should be `>=` instead of `>` the cap, so a doc sitting exactly at
      the boundary isn't blocked from even the cheapest maintenance edit. Not decided here — a design call.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): **KEEP-NA, valid — both items re-read,
  no change.** Item 1 (split the source doc) remains genuine content-judgment work, now more overdue (the source
  doc, `data_completion_tradfi_2026_07_15.md`, is now 1014 lines, up from 1000 at this issue's filing). Item 2
  (`>=` vs `>` design call) is LIKELY already answered in the live script — `check_line_caps.sh`'s
  `SMALL_MARKER_APPEND` (line ~238) and `SINGLE_TODO_FLIP` (line ~270) carve-out preconditions both already use
  `-ge`, landed via commits `1f65e146466` (2026-08-09) and `2efd6f0ca17` (2026-08-15) respectively — both predating
  this issue's 2026-08-16 filing. Not closing item 2 unilaterally here (this audit did not independently re-attempt
  the original blocked edit to confirm live), but flagging this as a strong, evidenced lead: whoever next touches
  this doc should attempt a live-reproduction test (a single-hunk marker-append or single-todo-flip against
  `data_completion_tradfi_2026_07_15.md`, now well over the 1000L cap) before routing item 2 to the script owner
  for a fresh design decision — the design call reads as already made and shipped, only the "confirm it live and
  close" step is missing.
