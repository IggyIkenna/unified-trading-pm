---
doc_type: issue
title:
  "task_template.md's documented CANCELLED/SUPERSEDED non-checkbox disposition format conflicts with
  check_todo_regression.sh's literal checkbox-count invariant"
summary: >-
  `task_template.md` (the `/done`-time disposition markers section) documents converting a dead/re-scoped todo from `- [
  ] <brief>` to a bold non-checkbox bullet `- **[TAG] P<n>. CANCELLED — SUPERSEDED <date> (<who>, per <ref>).**`.
  `scripts/plan-hygiene/check_todo_regression.sh` independently enforces that a staged plan's TOTAL `^- \[[ xX]\]` count
  (open + done) never shrinks vs `origin/live-defi-rollout`, with no special-case for this exact, documented conversion
  — so following task_template.md's own convention hard-fails precommit as a false "todo loss." Found live 2026-08-09
  while cleaning up `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`'s two stale P2 items
  (struck-through SUPERSEDED/DO-NOT, previously left as bare `- [ ] [DEVOPS]` with no ingestion-gate marker) — attempted
  the documented CANCELLED conversion, `check_todo_regression (--only)` failed with `lost=2`. Worked around it by
  keeping the checkbox format and retagging `[DEVOPS]` -> `[OPERATOR]` instead (achieves the same
  backlog-ingestion-gating goal without the format conflict), but the underlying contradiction between the two docs is
  unresolved and will bite the next agent who follows task_template.md's own documented convention literally.
status: open
nature: issue
asset_group: [ci, ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ssot-contradiction, todo-format, quality-gates, plan-hygiene, findings-triage]
related:
  [/plans/active/task_template.md, /plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md]
created: 2026-08-09
author: unknown
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: cicd
drift_direction: none
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Found while recording a 2026-08-09 operator ruling on uac_value_only_config_change_breaks_utl_untested_2026_07_20.md
  and cleaning up that doc's todo-eligibility gaps before an assigned_vm: NA -> planning reclassification."
context_scope:
  [
    /plans/active/task_template.md,
    scripts/plan-hygiene/check_todo_regression.sh,
    /plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md,
  ]
---

# CANCELLED/SUPERSEDED disposition format vs `check_todo_regression.sh`

## What I found

`task_template.md`'s `/done`-time disposition markers section documents, verbatim:

> **`CANCELLED`/`SUPERSEDED`** — the todo is re-scoped or dead, nothing left to complete. Replace the `- [ ] <brief>`
> line with a bold, non-checkbox bullet: `- **[TAG] P<n>. CANCELLED — SUPERSEDED <date> (<who>, per <ref>).**`

`scripts/plan-hygiene/check_todo_regression.sh` counts `grep -cE "^- \[[ xX]\]"` (total open+done checkbox lines) per
staged plan and fails if the current total is less than `origin/live-defi-rollout`'s total for the same file — by
design, per its own header comment, this is meant to catch a genuine todo deletion/collapse, NOT a legitimate CANCELLED
conversion. The script has no special-case for the bold non-checkbox CANCELLED/SUPERSEDED bullet format — converting
even ONE stale `- [ ]` line to that format reads as a 1-todo "loss" and hard-fails the `--only` precommit check with
`LOSS <file> origin=N current=N-k lost=k`.

Live repro (2026-08-09): converted 2 stale struck-through P2 items in
`uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` from
`- [ ] [DEVOPS] ~~...~~ **SUPERSEDED**`/`**DO NOT**` to the documented non-checkbox bold-bullet CANCELLED format.
`check_todo_regression (--only)` failed:
`LOSS uac_value_only_config_change_breaks_utl_untested_2026_07_20.md origin=7 current=5 lost=2`.

## Why it matters

An agent following `task_template.md`'s own documented convention literally, in good faith, hits a hard precommit
failure with a confusing message ("todo loss") that doesn't obviously point back to the CANCELLED-format conversion as
the cause — likely to cost real debugging time, or worse, get "fixed" by reverting to the (non-compliant, still
`- [ ]`-tagged) old format without anyone noticing the two docs disagree.

## Workaround used this session (not a fix)

Kept the checkbox format (`- [ ] [TAG] P<n>. ...`) and retagged `[TAG]` to `[OPERATOR]` instead of converting to the
bold non-checkbox bullet — achieves the same "keep it out of the AO backlog" goal via the `[OPERATOR]` ingestion-gate
marker family (`task_template.md`'s OTHER documented mechanism, the "Non-dispatchable" section) without touching the
checkbox count. This sidesteps the conflict but does not resolve it — the CANCELLED/SUPERSEDED format is still
documented as the correct mechanism in `task_template.md` and still not exempted by the checker.

## Todos

- [x] ✅ [DEVOPS] P2. **Resolve the contradiction — pick one, then fix the other.** Either (a) teach
      `check_todo_regression.sh`'s `_check_one()` to recognize the CANCELLED/SUPERSEDED bold-bullet pattern (e.g. a line
      matching `^- \*\*\[[A-Z]+\] P\d\. CANCELLED`) and count it as equivalent to a retained checkbox line rather than a
      loss, or (b) update `task_template.md`'s CANCELLED/SUPERSEDED convention to keep the checkbox bracket
      (`- [ ] [TAG] P<n>. CANCELLED — SUPERSEDED ...`) instead of converting to a bold non-checkbox bullet, matching
      what `check_todo_regression.sh` already expects. Either fix is small; the risk is leaving them disagreeing.
      Done-when: a fresh conversion of a stale todo to CANCELLED/SUPERSEDED format, per whichever convention wins,
      passes `check_todo_regression.sh --only <file>` cleanly. — Done via
      `ao_satellite_ao_dispatch_batch15_2026_08_09.md` todo 2: `unified-trading-pm@d01cd9ad41` (option (a) shipped —
      `_check_one()` now counts `^- \*\*\[[A-Z]+\] P[0-9]+\. CANCELLED` bullets alongside checkbox lines; verified with
      a scratch-repo before/after repro — old logic flagged a fresh CANCELLED conversion as `lost=1`, fixed logic
      reports 0 violations; a genuine todo deletion still correctly fails. Full QG green). Independently re-verified
      2026-08-10 via `ao_satellite_ao_dispatch_batch15_finalize_2026_08_09.md` todo 1 — confirmed the regex is live in
      the shipped script and re-derived `_check_one()`'s counting logic against synthetic before/after content.
- [x] ✅ [DOC] P3. Grep the corpus for any EXISTING bold non-checkbox `CANCELLED —`/`SUPERSEDED` bullets that may have
      already silently reduced a plan's checkbox total below its origin value without anyone noticing (this check only
      runs `--only` on STAGED files today, so a prior conversion that landed via a path that skipped this hook — e.g.
      `safe-doc-push.sh` before its own recent hardening, or a raw push — could be sitting unnoticed). Not urgent; a
      hygiene sweep item. — Done via `ao_satellite_ao_dispatch_batch15_2026_08_09.md` todo 3:
      `unified-trading-pm@4eb3f143ac` (corpus-wide
      `grep -rnE '^\- \*\*\[[A-Z]+\] P[0-9]+\. (CANCELLED|SUPERSEDED)'     plans/ codex/` found exactly 3 pre-existing
      matches, all `CANCELLED` (no bare-`SUPERSEDED` instances):
      `plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md:90` (active plan),
      `plans/archive/2026_07/data_pipeline_check_mdps_features_history_2026_07_24.md:947` (archived),
      `plans/archive/issues/defi_manifest_no_expected_unattempted_seeder_2026_07_26.md:158` (archived). Ran
      `check_todo_regression.sh --only <file>` against each individually — all 3 report `0 violation(s)` under the
      now-fixed checker, so no currently-undetected silent checkbox-loss exists in the live corpus from this pattern. No
      bulk-fix needed per the todo's own scope). Independently re-verified 2026-08-10 via
      `ao_satellite_ao_dispatch_batch15_finalize_2026_08_09.md` todo 1 — re-ran the exact grep, same 3 matches/lines,
      each individually re-checked as `0 violation(s)`.
- [ ] [DEVOPS] P2. **Second, independently-found trigger for the SAME root cause — Finding-J archival extraction has no
      exemption either.** `check_todo_regression.sh` also has no special-case for `task_template.md` finding J's OTHER
      documented, sanctioned mechanism: extracting a fully-closed dated Progress Log section verbatim into an
      archive-bound companion doc (`plans/archive/<YYYY_MM>/<slug>_history_<date>.md`) and leaving a one-line pointer. A
      legitimate extraction necessarily removes N already-`[x]` checkbox lines from the live doc, which this checker
      reads as `lost=N` — identical failure shape to the CANCELLED-format case above, just a different sanctioned
      workflow tripping it. Live repro 2026-08-09 (`prediction_satellite_ao_dispatch_batch8-001`, slot 8): extracting 12
      fully-closed sessions from `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (1013L → 339L, 25
      already-closed items moved to `plans/archive/2026_08/prediction_cross_venue_arb_and_coverage_history_2026_08.md`)
      failed with `origin=27 current=2 lost=25`. Workaround used (not a fix): appended a 25-line "Extracted items index"
      section to the live doc — one-line `- [x]` conservation stub per moved item, clearly labeled as a mechanical
      index, not live work — so the total checkbox count matches origin (376L final, still well under the 500L soft
      cap). This directly undercuts the whole point of the line-cap remediation workflow (the doc still carries N lines
      of checkbox-shaped content for every extraction, just shorter ones) and will recur on every future Finding-J
      extraction until fixed. **Proposed real fix** (more involved than the CANCELLED case, needs cross-file awareness):
      when `_check_one()` finds `cur_total < gh_total` for a staged plan, check whether the SAME staged changeset also
      touches/creates a `plans/archive/**/*_history_*.md` file that is listed in the plan's own `related:` frontmatter
      and whose OWN checkbox total grew by at least the shortfall — if so, treat as conserved (moved, not lost), not a
      violation. Until fixed, every Finding-J extraction either eats the stub-index tax above or hand-waives the gate
      some other way — worth resolving alongside the CANCELLED-format fix above since both todos touch the same
      function.

## Progress Log

- **2026-08-09**: Filed after hitting this live while cleaning up
  `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`'s two stale P2 items for AO-dispatch eligibility.
  Worked around it in that doc (kept checkbox format, retagged to `[OPERATOR]`) rather than force the CANCELLED
  conversion through; this doc tracks the real fix.
- **2026-08-09 (slot 8, data_engineering, `prediction_satellite_ao_dispatch_batch8-001`)**: independently hit the same
  root cause via a different trigger (Finding-J archival extraction, not CANCELLED-format conversion) while executing
  `prediction_satellite_ao_dispatch_batch8_2026_08_08.md`'s line-cap-remediation todo. Appended the second todo above
  rather than filing a new doc — same script, same function, same underlying gap. Worked around it in
  `prediction_cross_venue_arb_and_coverage_2026_07_24.md` with a stub-index tax (see that doc's own "Extracted items
  index" section for the mechanism); did not attempt the real cross-file fix here — out of this task's scope (a
  data-pipeline plan-hygiene fix isn't this todo's `[DOC]`/`[SCRIPT]` scope, and the proposed fix needs design judgment
  on the cross-file correlation logic, not a mechanical one-liner).
- **na-eligibility-audit 2026-08-09 (round9)**: satellite-extraction, not whole-doc RECLASSIFY — first audit pass on
  this doc (never previously touched by na-eligibility-audit). Of the 3 open items, 2 are extracted to
  `ao_satellite_ao_dispatch_batch15_2026_08_09.md`: the format-contradiction fix (both resolution options are described
  in the doc's own text as small, with a concrete done-when) and the mechanical corpus grep (explicitly "not urgent; a
  hygiene sweep item," zero judgment). The 3rd item (Finding-J archival-extraction trigger) stays KEEP-NA, valid — this
  doc's own text self-flags it as needing "design judgment on the cross-file correlation logic, not a mechanical
  one-liner." Whole-doc RECLASSIFY bar not cleared.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read. Of 3 original
  items, 2 are already extracted to `ao_satellite_ao_dispatch_batch15_2026_08_09.md` (todos 2, 3). The 1 remaining item
  (Finding-J archival-extraction cross-file conservation fix for `check_todo_regression.sh`) is self-flagged in its own
  text as needing 'design judgment on the cross-file correlation logic, not a mechanical one-liner' — genuinely not
  bounded. Agrees with round9's assessment.
- **ao_satellite_ao_dispatch_batch15_finalize 2026-08-10**: reconciled real completion evidence for both extracted todos
  (`[DEVOPS] P2` format-contradiction fix, `[DOC] P3` corpus grep) back into this doc — both were bare `➡️ EXTRACTED`
  redirect pointers, now carry the actual `unified-trading-pm@d01cd9ad41` / `unified-trading-pm@4eb3f143ac` evidence
  plus the finalize plan's own independent re-verification. The 3rd item (Finding-J cross-file fix) is untouched — still
  genuinely NA.
