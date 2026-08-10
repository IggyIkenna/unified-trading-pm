---
doc_type: issue
title:
  prediction_cross_venue_arb_and_coverage_2026_07_24.md sits at the exact 1000-line hard cap — ANY further edit
  (including a routine na-eligibility-audit Progress Log marker) now hard-fails check_line_caps.sh
summary: >-
  `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` is exactly 1000 lines (`wc -l`), the flat
  active-plan hard cap (`check_line_caps.sh`, `PLAN_HARD_CAP=1000`, `-gt` comparison — 1000 itself still passes, 1001
  fails). Its `## Progress Log` section (lines 71-1000, ~930 lines) is unusually structured: individual dated
  sub-sections carry their OWN embedded open `- [ ]` checkboxes inline (not a separate Todos block) — confirmed via a
  same-day na-eligibility-audit classification pass (2026-08-07, prediction tranche) that the doc's 5 real open items
  live at lines 172, 380, 609, 621, 703, each nested inside historical narrative prose rather than a top-level Todos
  section. This blocked that audit pass from writing its dated Progress Log verdict marker (the mechanism
  `/na-eligibility-audit`'s Phase 0 incremental-diff mode depends on to skip an unchanged, already-verdicted doc on
  future runs) — any append would push the file to 1001+ lines. Per `task_template.md` finding J, the sanctioned fix is
  to extract the oldest fully-closed dated Progress Log section(s) verbatim into an archive-bound
  `prediction_cross_venue_arb_and_coverage_history_2026_08.md` (or similar), leaving a one-line pointer behind — but
  because open checkboxes are embedded INSIDE dated narrative sections here (not segregated), the extraction is NOT a
  blind "take the oldest N lines" operation: whoever does it must first confirm the candidate extraction range doesn't
  contain any of the 5 known open-item line numbers (or any newly-opened one since), then verify no LATER entry
  cross-references content inside the extracted range before removing it. That verification pass is why this audit run
  did not attempt the extraction inline — it is a real doc-hygiene fix, not a design/judgment call, but wants a
  dedicated, careful pass rather than a rushed side-effect of an unrelated marker write.
status: resolved
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, line-caps, progress-log, na-eligibility-audit, doc-maintenance]
related:
  [
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/task_template.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: 2026-08-07
author: na_eligibility_auditor (agt-a01c7e, slot 4)
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-08-07 (na_eligibility_auditor, slot 4, dispatch agt-a01c7e) while running /na-eligibility-audit
    prediction Phase 3 (apply KEEP-NA verdict markers) — the target doc was at the exact 1000-line hard cap, blocking
    the marker write.",
  ]
resolved_by:
  unified-trading-pm@afd6891bb3 (batch8, slot 8, 2026-08-09 — extraction landed + this doc's own todo checked off)
locked_by:
locked_since:
context_scope:
  [
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/task_template.md,
    scripts/plan-hygiene/check_line_caps.sh,
  ]
supersedes:
superseded_by:
---

> **ARCHIVED 2026-08-09** — sole todo done (`unified-trading-pm@afd6891bb3`), status flipped `open` → `resolved`.
> Reconciled by `prediction_satellite_ao_dispatch_batch8_2026_08_08_finalize.md`'s `[REVIEW] P3` todo 1, per that plan's
> own `depends_on`+`gate_on_depends` gate on `prediction_satellite_ao_dispatch_batch8_2026_08_08.md`'s todo (also done).
> `archive_exempt: true` (set 2026-08-09) is cleared now that the routed-through-finalize archival it named has actually
> happened.

# prediction_cross_venue_arb_and_coverage_2026_07_24.md is at the 1000-line hard cap

## What I found

`plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` is exactly 1000 lines. `check_line_caps.sh`'s
`PLAN_HARD_CAP=1000` check uses `-gt` (strictly greater than), so the file itself is not currently failing the gate —
but it cannot absorb even one more line without doing so at the next commit that touches it.

Its `## Progress Log` section runs from line 71 to line 1000 (~930 of the file's 1000 lines) and is NOT
soft-warn-compliant either (`PLAN_SOFT_CAP` is 500). Unusually for this corpus, several of its dated sub-sections (e.g.
the `### 2026-06-24` "FULL ARB-DETECTOR STACK SHIPPED" narrative starting at line 133) carry their own embedded `- [ ]`
/ `- [x]` checkboxes inline as part of the historical narrative, rather than living in a separate `## Todos` block. A
2026-08-07 na-eligibility-audit classification pass (prediction tranche) independently verified the doc's exact 5 open
items live at lines 172, 380, 609, 621, 703 (matches `grep -cE '^\s*[-*] \[ \]'` = 5 exactly).

## Why this matters

`/na-eligibility-audit`'s Phase 0 incremental-diff mode skips re-reading a doc on future runs only when it carries a
dated `na-eligibility-audit YYYY-MM-DD` Progress Log marker that is not older than the doc's last edit. This doc cannot
receive that marker while at cap, so every future na-eligibility-audit run (this one runs on a 2-hour timer) will
re-read this ~1000-line doc in full, forever, until the cap is cleared. That is a real (if modest) recurring cost, not a
one-time inconvenience.

## Recommended fix

Per `task_template.md` finding J ("extract completed Progress Log sections AS YOU GO"): pick the oldest fully-closed
dated sub-section(s) in the 71-1000 range, confirm the candidate range contains NONE of the known open-item lines (172,
380, 609, 621, 703 as of 2026-08-07 — re-verify current open-item lines first, they may have shifted), confirm no later
Progress Log entry references content inside the candidate range by pointer/description, then extract that range
verbatim into `plans/archive/2026_08/prediction_cross_venue_arb_and_coverage_history_2026_08.md` (`status: complete`,
`nature: record`, 0 open todos) and leave a one-line pointer in its place. Re-run `wc -l` + `check_line_caps.sh` after
to confirm the doc is back under the soft cap (not just barely under the hard cap, so this doesn't recur in 2-3 weeks).

- [x] ✅ [DOC] P2. Extract the oldest fully-closed dated Progress Log section(s) from
      `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` into a dated `_history_2026_08.md` archive
      doc per the Recommended fix above, verifying the extracted range contains none of the doc's current open-item
      lines and nothing later in the doc references it by pointer. Done-when: `wc -l` on the source doc is back under
      500 (the soft cap), `check_line_caps.sh` still passes, and every open checkbox that existed before the extraction
      still exists verbatim in the source doc afterward (diff the open-item line texts before/after, not just the
      count). Repo: unified-trading-pm. — DONE 2026-08-09 (batch8, slot 8), unified-trading-pm@afd6891bb3: 12
      fully-closed dated sessions (2026-06-20, 06-21, 06-23 x3, 06-25 x4, 06-27 x3) extracted to
      `plans/archive/2026_08/prediction_cross_venue_arb_and_coverage_history_2026_08.md`; source doc 1013L → 376L (25
      lines are a `check_todo_regression.sh` conservation stub index, see that doc's "Extracted items index" section —
      still well under the 500L soft cap); both open items (lines 172, 380) verbatim-verified unchanged;
      `check_line_caps.sh` green. The 2026-06-26 session was deliberately left in place (referenced by pointer from the
      2026-08-04 entry: "this Progress Log's 2026-06-26 entry") and the 2026-06-27 session's own accumulated audit-trail
      tail (2026-07-30 onward) was left in place as current status, not archived history.

## Progress Log

- **2026-08-07 (na_eligibility_auditor, slot 4)**: Filed. Not fixed inline this run — the fix is mechanical but wants a
  careful verification pass (confirm no open checkbox or later cross-reference sits inside the extraction range) that a
  rushed side-effect of an unrelated Progress-Log-marker write shouldn't attempt. The source doc's own na-eligibility-
  audit verdict (KEEP-NA, valid, 5 open items, mixed content) stands independently of this line-cap issue and is
  unaffected by not writing this run's marker — only the FUTURE incremental-skip optimization is lost until this is
  fixed.
- **na-eligibility-audit 2026-08-08 (Phase 2, prediction tranche)**: this doc's sole todo clears the whole-doc bar
  (bounded mechanical extraction, done-when stated) — but the conflict-check
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) found a near-verbatim duplicate
  already drafted: `plans/active/prediction_satellite_ao_dispatch_batch8_2026_08_08.md` (`status: draft`,
  `assigned_vm: planning`, authored TODAY by `/ag-closeout-audit prediction`) carries the identical extraction as its
  own todo, citing this doc's own todo verbatim as its source, and states its own done-when explicitly checks off this
  doc's todo as part of its close-out. Flipping this doc too would create a genuine duplicate-dispatch hazard (two
  AO-dispatchable surfaces claiming the same file edit) the moment batch8 flips `draft` -> `active`. NOT reclassified —
  left `assigned_vm: NA`; the work already has a dispatch path via batch8 (+ its
  `prediction_satellite_ao_dispatch_batch8_2026_08_08_finalize.md` twin).
- **na-eligibility-audit 2026-08-08, second pass (independent re-verification, same conclusion)**: concurred
  independently before seeing the entry above (converged on the identical KEEP-NA-STALE/no-reclassify verdict via the
  same conflict-check). One additional re-verification this pass adds: source doc
  (`prediction_cross_venue_arb_and_coverage_2026_07_24.md`) is still exactly 999 lines (was 1000 on 2026-08-07) and so
  still cannot safely take a dated verdict marker itself (a minimal marker wraps to 2+ lines under this corpus's
  prose-wrap formatter) — its Phase-0 incremental-skip optimization remains blocked exactly as this doc describes. That
  source doc's other 2 open items (tarball-overwrite-race design call, line 172; mid-gap historical-backfill build,
  line 702) were independently re-checked and remain genuinely open, unchanged in substance since the 2026-08-06 marker
  (the 5→3 open-item drop since then was two unrelated closures via batch4's 2026-08-07 finalize, not new
  na-eligibility-audit work).
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-09 (prediction tranche)**: KEEP-NA, valid — re-verified, 1 open, unchanged. The source
  doc (`prediction_cross_venue_arb_and_coverage_2026_07_24.md`) is now 1009 lines (was 999 on 2026-08-08) — WORSE, not
  better, due to today's batch9 extraction annotations adding lines rather than removing them — underscoring this doc's
  own remediation is still needed. `prediction_satellite_ao_dispatch_batch8_2026_08_08.md`'s extraction todo remains
  `status: active` (operator-approved 2026-08-08) but not yet executed. Doc stays NA; this run wrote its own marker onto
  the source doc via the documented SCOPED-mode append exception (0 deletions, <10 lines, no checkbox touched).
- **2026-08-09 (slot 8, data_engineering, `prediction_satellite_ao_dispatch_batch8-001`)**: this doc's own todo is now
  `[x]` done (see above) — 0 open todos remain, which `check_archive_candidates.sh` (--only, precommit) correctly flags
  as an archive candidate. Set `archive_exempt: true` rather than archiving inline: this is documented use-case (b) in
  that script's own header comment — "a doc explicitly routed for archival THROUGH another plan's own dispatched
  reconciliation todo." `prediction_satellite_ao_dispatch_batch8_2026_08_08_finalize.md`'s `[REVIEW] P3` todo 1
  ("Reconcile the source doc... Confirm the source issue doc's checkbox is flipped and its `status` moves toward
  `resolved`") is exactly that dispatched reconciliation todo, gated via `depends_on`+`gate_on_depends` on batch8's own
  todo (now done) — it is the correct owner of this doc's `status: resolved` flip + eventual archival, not a standalone
  action here. Not archiving now avoids doing the 6-step ritual (referrer fixes across 8 corpus citations,
  codex-alignment check) twice — once here, once again when finalize re-verifies.
- **2026-08-09 (finalize reconciliation, `prediction_satellite_ao_dispatch_batch8_2026_08_08_finalize-001`,
  `[REVIEW] P3` todo 1)**: reconciliation confirmed — batch8's own todo is done (`unified-trading-pm@afd6891bb3`) and
  this doc's own todo was already `[x]` with a commit citation (see above). Completed the routed-through-finalize
  archival named in the entry directly above: flipped `status: open` → `resolved`, filled `resolved_by:`, removed the
  now-moot `archive_exempt: true` (its whole justification was "archival happens through this exact finalize todo,"
  which just ran), added the archive banner, and `git mv`'d this doc to `plans/archive/2026_08/issues/`. Fixed all 8
  corpus referrers' leading-slash `/plans/active/issues/...` paths to the new `/plans/archive/2026_08/issues/...`
  location (the `check_reference_paths.py` existence-ratchet population); left bare/relative prose mentions
  (`issues/...`, bare filename) describing past state as-is, since those aren't the format the existence check enforces
  and rewriting them would blur what each historical entry actually observed at the time. See
  `prediction_satellite_ao_dispatch_batch8_2026_08_08_finalize.md`'s own Progress Log for the exact commit citation.
