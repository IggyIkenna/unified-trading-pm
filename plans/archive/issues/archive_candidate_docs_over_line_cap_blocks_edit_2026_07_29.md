---
doc_type: issue
title:
  Two archive-candidate docs are genuine "prose-only remaining work" traps (100% checkboxes checked, real open work
  described only in prose/tables) AND already exceed the 1000-line hard cap, so neither can be safely edited to fix
  either problem without a split first
summary: >-
  While resolving cicd escalation agt-c3b939 (plan_health archive-candidates gate), 14 checkbox-complete docs were
  deep-read individually (not trusted by checkbox count — this corpus has confirmed prose-only-remaining-work traps). 12
  were genuine traps; 10 were safely fixed (a real `- [ ]` todo added, all under the 1000-line hard cap). The other 2
  are ALSO traps (real remaining work exists only in a "Deferred work" table row / prose, invisible to
  `check_archive_candidates.sh`'s checkbox count) but are already over the `check_line_caps.sh` 1000-line hard cap
  (1011L / 1509L) — the prek `--precommit` rule is absolute for a file a commit touches ("a file THIS commit touches
  must not be over its tier's cap, full stop", no ratchet exemption), so adding the missing todo would itself become
  uncommittable. Left untouched this pass; the archive-candidates gate stays green regardless (2 candidates vs baseline
  11), but the underlying prose-trap defect in both docs is real and not yet fixed.
status: resolved
nature: issue
asset_group: [tradfi, defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, line-caps, archive-candidates, prose-trap, split-needed]
related:
  [
    /plans/archive/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md,
    /plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-07-29
last_updated: "2026-08-02"
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
source: [cicd escalation agt-c3b939 (plan_health gate), archive-candidates deep-read, 2026-07-29]
drift_direction: worsening-slowly
depends_on: []
locked_by:
resolved_by: "both target docs archived via the zero-open-todo ritual (2026-08-02); no split needed per the 2026-07-30 ruling"
context_scope:
  [
    /plans/archive/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md,
    /plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Two archive-candidate docs need a split before their prose-trap can be fixed

> **🟢 RESOLVED 2026-08-02** — premise superseded by the 2026-07-30 operator ruling (an over-cap doc archives without a
> split once it hits 0 open todos). Both halves discharged: `mtds_backfill_vm_startup_oom_rc137_2026_07_14` archived;
> the sole remaining referrer (`tradfi_backfill_throughput_followups_2026_07_24.md` line ~676) repointed in the same
> commit.

## What I found

Resolving the `check_archive_candidates.sh` hard gate (14 candidates vs baseline 11), I deep-read all 14 flagged docs
instead of trusting the 0-open-checkbox heuristic. 12 turned out to be genuine traps — checkbox-complete but with real
remaining work described only in prose, a "Deferred work" table row, or a banner. 10 of those were fixed cleanly (a real
`- [ ]` todo added, converting the invisible prose gap into tracked work). These 2 could not be:

1. **`tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`** (1011 lines, over the 1000L hard cap).
   Every checkbox is `[x]`, but the "## Deferred work after 2026-07-26" table's last row reads: _"New P2 todo — re-run
   the ES/MES backfill a THIRD time now that the empty-day-listing retry mitigation is live | Not done (slot 4,
   2026-07-26)... | Nobody — launch one more `launch-mdps-backfill-vm.sh` pass + re-measure the `1d` hit rate"_ — real,
   named, unowned remaining work with no corresponding open checkbox anywhere in the doc.
2. **`mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`** (1509 lines, over the 1000L hard cap). Every checkbox is
   `[x]`, but the doc's own closing sections leave two threads explicitly open: the
   `uts-prod-manifest-consolidator-market-data-defi` DuckDB consolidator crash / cron scheduler stays **PAUSED**
   ("resuming it... remains operator+backend-owned and will be decided on its own evidence, not unblocked by this
   verdict alone"), and the Morpho `lending_indices` backfill live-verify section ends "Not yet a full close for this
   handler — the backfill was still running at the time this entry was written."

Both are ALSO over `check_line_caps.sh`'s 1000-line hard cap. That check has NO ratchet exemption for a file the current
commit touches ("a file THIS commit touches must not be over its tier's cap, full stop" —
`scripts/plan-hygiene/check_line_caps.sh`'s own doc comment) — so adding even one line (the missing todo) to either doc
would make it uncommittable via the normal path. Fixing the prose-trap here requires a real split (same pattern the
operator already ratified for `sports_consolidated_closeout_2026_07_19.md` in
`autonomous_session_operator_decisions_2026_07_25.md` entry #9: a trimmed coordination-index parent + N child plans
under cap, wired via `depends_on`/`gate_on_depends`), not a mechanical one-line add — genuinely open-ended judgment
about what goes where, not something to guess at here.

## Why it matters

The `check_archive_candidates.sh` gate stays green regardless (2 candidates vs baseline 11, well under) — this is NOT
currently blocking anything. But both docs' real remaining work stays invisible to every mechanical hygiene check
(checkbox count AND the archive-candidates heuristic) until split, which means it will keep silently NOT happening
unless someone reads the full doc by hand again.

## Recommended next step (not done here — needs real design judgment, not a mechanical fix)

For each doc: split into a trimmed index/summary doc (kept under the 1000L cap, the historical investigation + Progress
Log content) + extract the ONE real open item into a small, clean, dispatchable child doc/todo. Suggested child-doc
content:

- tradfi_mdps doc → extract: "launch one more `launch-mdps-backfill-vm.sh` ES/MES pass, re-measure the `1d` hit rate
  against the 454/2398 baseline, and pursue the `_list_instrument_files` listing-consistency lead if the hit rate is
  still flat" as a standalone `- [ ]` todo in a new, small, under-cap doc.
- mtds_backfill doc → extract: "confirm the DuckDB consolidator crash root cause is fully resolved, decide whether
  `uts-prod-manifest-consolidator-market-data-defi-cron` can be un-paused, and confirm the Morpho `lending_indices`
  backfill's live-verify actually completed with no rc=137 recurrence" as a standalone `- [ ]` todo.

## Todos

- [x] ✅ [DOC] P2. **OBSOLETE — resolved by ARCHIVAL instead of a split, closed 2026-08-02
      (`/na-eligibility-audit     defi`).** Do NOT split
      `tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`. Verified live this pass: that doc is
      already at `/plans/archive/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md` with
      `status: resolved`, **0 open todos**, 1100 lines — i.e. it took exactly the path this doc's own 2026-08-02
      Progress Log entry predicted ("its own todo may be equally obsolete if that doc also reaches zero open todos — it
      should be re-checked against the same ruling rather than split reflexively"). The governing ruling is the same one
      that closed the sibling `mtds_backfill` half: **a zero-open-todo doc archives via the normal 6-step ritual
      regardless of how far over cap it is**, and "never delete content from a done plan just to get it under a cap"
      (operator 2026-07-30; SSOT
      [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md)
      § "The line-cap does NOT block archival of an already-done doc", also codified in
      `scripts/plan-hygiene/check_line_caps.sh`'s header comment). Archival moved it out of the capped globs entirely —
      the outcome the split was only ever a workaround for. **Both halves of this issue are now discharged; this doc has
      zero open todos and is ARCHIVE-READY** (see the Progress Log entry below for the one referrer that must be fixed
      at archival time).
- [x] ✅ [DOC] P2. **OBSOLETE — resolved by ARCHIVAL instead of a split, 2026-08-02 (operator ruling 2026-07-30).** Do
      NOT split `mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`. That ruling added a documented exception to
      `check_line_caps.sh` for exactly this doc: **a zero-open-todo doc archives via the normal 6-step ritual regardless
      of how far over cap it is**, and it explicitly forbids the alternative this todo proposed — "never delete content
      from a done plan just to get it under a cap" (SSOT:
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § "The line-cap does NOT block archival of
      an already-done doc"; this 1509-line doc IS the case the ruling was written about). The doc is now at
      `/plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md` — out of the capped globs entirely, which
      is the outcome the split was only ever a workaround for. **Both "real open items" this todo named were discharged
      at archival, not dropped**: (1) _consolidator cron un-pause decision_ — **MOOT, verified**:
      `uts-prod-manifest-consolidator-market-data-defi-cron` is not paused at all; it is ENABLED and running every 1
      minute per `/plans/active/defi_consolidated_closeout_2026_07_18.md` (2026-07-22 check), and both underlying causes
      are resolved + archived (`defi_manifest_consolidator_duplicate_race_2026_07_10.md`,
      `defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`); (2) _Morpho `lending_indices` live-verify /
      rc=137 non-recurrence_ — migrated into a real tracked `- [ ]` todo (`[VERIFY] P3`, broadened to all 7
      not-yet-live-verified DeFi handlers) in
      `/plans/active/issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`. The sibling `tradfi_mdps` split
      todo above is untouched and still open.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - doc's own text declares the index/history split an open-ended
  judgment call about what goes where
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-02** (tranche=defi, autonomous, scheduled): **ARCHIVE (ready, not executed this run)**
  — re-read end to end (1 open item at entry). That item is MOOT: its target doc
  `tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md` is already archived, `status: resolved`, 0
  open todos — closed by citation above. **This doc now has zero open todos and both halves discharged, so it qualifies
  for the standard 6-step archival ritual.** The move was deliberately NOT executed in this run for a concurrency
  reason, not a correctness one: the ritual requires fixing every corpus referrer, and this doc's only ACTIVE referrer
  is `/plans/active/tradfi_backfill_throughput_followups_2026_07_24.md` (line ~668) — an `assigned_vm: NA` doc **owned
  by the `tradfi` tranche**, which a sibling worker is auditing concurrently in this same sharded fire. Editing it would
  violate the primary-owner rule
  ([`/cursor-configs/skills/na-eligibility-audit/SKILL.md`](/cursor-configs/skills/na-eligibility-audit/SKILL.md) Phase
  0, "only the owning tranche writes"), which exists precisely to stop the N-way marker-conflict storm. **Next actor**:
  whoever archives this fixes that one referrer plus the already-archived
  `/plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md` mention in the same commit. `locked_by:` is
  blank, so no `[unlock-plan]` is needed.
- **2026-08-02**: this doc's premise is now half-obsolete. It was written 2026-07-29 on the assumption that an over-cap
  archive-candidate must be SPLIT before it can be edited/archived; the operator ruled the opposite on 2026-07-30 and
  the exception is now codified in both `scripts/plan-hygiene/check_line_caps.sh` (header comment) and
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`. The `mtds_backfill_vm_startup_oom_rc137` half
  is closed by archival (see its todo above); the `tradfi_mdps_build_continuous_mismatches_2_and_4_still_open` half is
  still genuinely open, but note that its own todo may be equally obsolete if that doc also reaches zero open todos — it
  should be re-checked against the same ruling rather than split reflexively.
