---
doc_type: issue
title:
  "safe-doc-push isolated-worktree mode silently DROPS file deletions — every archival `git mv` committed through it
  lands CREATE-ONLY, leaving a live duplicate at the old plans/active path"
summary: >-
  Reproduced live 2026-08-10: `8ac88720e6` archived 17 `ag_closeout_audit_*_parked_*.md` reports through
  `scripts/dev/safe-doc-push.sh` and landed **create-only** — all 17 `plans/archive/2026_08/issues/` paths show `A`, and
  not one `plans/active/issues/` path shows `D`. Every archived doc was left duplicated at its old active path, which
  the fleet (including the AO dispatch backlog, derived from `plans/active/**` open todos) still reads as live work.
  This is the failure class already ruled 2026-08-08 in
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § "The archival commit itself must not drop the
  rename's delete side" — but reached by a NEW mechanism that rule explicitly does not cover. That SSOT names
  safe-doc-push as the **preferred, safe** shape precisely because it does a full-staged-set commit rather than a
  path-scoped `git commit --only`. What it predates: isolated-worktree mode (default on laptop since 2026-08-10) syncs
  by **copying each `--files` entry from the caller tree into a private worktree**, and a deleted file has nothing to
  copy — the run prints `isolation: named file not present in caller tree, skipping copy: <path>` and the deletion is
  dropped. So the documented-safe path is now create-only for ANY rename, and the SSOT's advice is actively wrong under
  the new default.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [safe-doc-push, isolated-worktree, archival-ritual, rename-deletion, create-only-commit, ship-discipline]
related:
  [
    /plans/archive/issues/safe_doc_push_isolation_rewrites_slot_commit_identity_2026_08_10.md,
    /plans/archive/issues/git_commit_only_drops_rename_deletions_create_only_archive_2026_08_06.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: infra
effort: high
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /scripts/dev/safe-doc-push.sh,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/issues/safe_doc_push_isolation_rewrites_slot_commit_identity_2026_08_10.md,
  ]
source: >-
  Found during the 2026-08-10 autonomous ag-closeout close-out (slot 1) while verifying commit `8ac88720e6` against
  origin rather than trusting the ship script's exit code. `git show --name-status` showed 17 `A` and zero `D`.
---

# safe-doc-push isolated mode drops deletions → create-only archival commits

## What happened (measured, not inferred)

```
$ git show --name-status 8ac88720e6 --format=''
M   plans/active/issues/operator_action_items_consolidated_2026_08_08.md
A   plans/archive/2026_08/issues/ag_closeout_audit_cefi_parked_2026_08_10.md
A   plans/archive/2026_08/issues/ag_closeout_audit_defi_parked_2026_08_08.md
...   (17 × A, zero D)
```

The working tree had a clean `git mv` for all 17 (both sides staged). The commit kept only the add side. Origin then
carried **both** copies: `git ls-tree -r FETCH_HEAD plans/active/issues/ | grep parked` returned 27 where it should have
returned 10.

## Root cause

`safe-doc-push.sh` isolated-worktree mode (line ~180, default-on for `laptop` per `_sdp_isolation_default`) builds its
commit in a private worktree and populates it by **copying each `--files` path out of the caller tree**. A path that was
deleted (the old side of a `git mv`) does not exist in the caller tree, so the copy step skips it — visibly, in the log:

```
isolation: named file not present in caller tree, skipping copy: plans/active/issues/ag_closeout_audit_ui_parked_2026_08_10.md
```

There is no corresponding "propagate deletion" step, so the private index never learns the file should be removed. The
commit is therefore structurally incapable of expressing a deletion, for any caller, silently.

**Why this is worse than the 2026-08-06 `git commit --only` instance**: that one was a known-sharp tool the ritual warns
against. This one is the tool the ritual tells you to use _instead_, so following the documented-safe path is now the
way to reproduce the bug — and it fails silently with exit 0.

## Why it matters beyond tidiness

`regen_backlog_from_plan.py` derives the AO dispatch backlog from open `- [ ]` todos under `plans/active/**`. A
duplicate left at the old active path keeps feeding todos into the backlog for work that is archived and done, and the
two copies diverge on the next edit to either one — the 2026-08-06 incident found 5 diverged pairs from the analogous
mechanism.

## Recovery applied this session

Re-committed the 17 deletions using the documented `SDP_ISOLATED=0` shared-index escape hatch. Verified beforehand that
all 17 pairs were byte-identical, so no divergence had accumulated.

## Todos

- [x] ✅ [SCRIPT] P1. **Make isolated mode propagate deletions.** — unified-trading-pm@18ae9a4312. Fix in
      `safe-doc-push.sh` lines 321-342: when a named file is absent from the caller tree but present at
      `origin/$BRANCH`, rm it from the isolated worktree so `git add` stages the deletion. Regression test:
      `tests/test_safe_doc_push_isolated_deletion_propagates.bats` (4 tests, all passing via `npx bats`).
- [x] ✅ [SCRIPT] P1. **Fail loudly instead of skipping silently.** — unified-trading-pm@37bbd172be. The `skipping copy`
      branch (isolated copy loop, `safe-doc-push.sh`) now distinguishes the two cases: a named path absent from the
      caller tree but PRESENT at `origin/$BRANCH` is a deletion (propagated — `18ae9a4312`); a named path absent from
      the caller tree AND absent from `origin/$BRANCH` is a caller error and now **exits non-zero (2) with a message
      naming the path**, instead of logging at info level and silently no-op'ing (which dropped the path from the commit
      while still reporting success). Regression: `tests/test_safe_doc_push_isolated_deletion_propagates.bats` — the
      "absent AND untracked" case now asserts exit 2 + a path-naming message (24/24 bats tests pass; full
      `quality-gates.sh` green).
- [x] ✅ [DOCS] P1. **Correct the archival-ritual SSOT.** — unified-trading-pm@2f9efbcfaf.
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § "must not drop the rename's delete side"
      updated: safe-doc-push option-1 now carries an isolation caveat — documents that isolated-worktree mode previously
      dropped deletions silently (pre-`18ae9a4312`), the fix now propagates them, pre-fix checkouts need
      `SDP_ISOLATED=0` for archival commits with a rename. Cites this issue doc.
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-10 — `unified-trading-pm@689e10d281`** (QG green, post-push ancestry verified) —
      the assertion existed but was structurally blind; coverage widened.
      `scripts/plan-hygiene/check_create_only_archive_commits.py` (added `43e88b720d`, already wired into
      `run_hygiene_sweep.sh` as a HARD check) did assert the both-sides shape — but only for `plans/archive/issues/`
      against `plans/active/issues/`, via a path substitution. **Real archivals land in DATED directories**
      (`plans/archive/2026_08/issues/X.md`, `plans/archive/2026_08/X.md`), which that substitution never matched, so the
      guard reported a clean corpus while **10 live duplicate pairs sat on origin**. Rewritten to match by BASENAME
      across all of `plans/archive/**` vs `plans/active/**`, with two exemptions that keep the signal honest:
      `ALLOWED_DUPLICATE_STEMS` (a shrinking ratchet of pre-existing pairs, each carrying a recorded verdict — a pair
      NOT listed fails immediately, so no new duplicate can hide behind a shrinking count) and `_is_redirect_stub()` (an
      INTENDED pair). Verified: flags exactly the 2 genuinely-stale pairs, exempts the other 8, `ruff check` +
      `ruff format --check` clean. Confirmed green against origin after the push:
      `no create-only archive/active     duplicate pairs at HEAD`.
- [x] ✅ [REVIEW] P2. **DONE 2026-08-10 — full sweep run; 10 pairs found, each given a verdict** (table below). 2
      reconciled here by deleting the strictly-stale active copy (16 referrer repoints across 10 docs); 1 is an
      intentional redirect stub; the remaining 7 are carried on the ratchet with per-pair verdicts and the 3 follow-up
      todos below. Sweeping by basename across every archive subdirectory — rather than by the mirrored path the old
      guard assumed — is what surfaced the 8 pairs beyond the 2 recorded here earlier.
- [x] ✅ [SCRIPT] P1. **DONE 2026-08-10 — skill gate added; the 3 existing pairs stay on the ratchet.** Root cause of 3
      of the 10 pairs: the skill wrote its per-tranche parked report to
      `plans/active/issues/ag_closeout_audit_<tranche>_parked_<date>.md` and its "APPEND to a same-day doc if one
      already exists" rule only ever looked at `plans/active/issues/` — so a doc archived EARLIER THE SAME DAY was
      invisible and the write re-created it (`42247c0405`, `064019f77f`, `6b7ddb7944` each `A`-added a doc an earlier
      commit had archived that morning). `cursor-configs/skills/ag-closeout-audit/SKILL.md` § "Every parked finding
      lands in a durable doc" now carries a HARD pre-write `git ls-tree … plans/archive/` check with the exact command,
      and the two sanctioned responses (deliberately un-archive with a banner, or write a distinct `_run2` slug citing
      the archived doc). **Scope note**: this closes the RECURRENCE. The 3 already-existing pairs each hold two
      genuinely different reports and still need a per-doc merge decision — they stay on `ALLOWED_DUPLICATE_STEMS` until
      that happens — now tracked as the last [DOCS] P3 todo below, deliberately not bundled here.
- [x] ✅ [OPERATOR] P2. **RESOLVED 2026-08-10 — `[unlock-plan]` GRANTED by direct operator ruling** (recorded in
      `/plans/active/issues/ag_closeout_audit_tradfi_parked_2026_08_10.md` § "Finding 3", where the ask was tracked; the
      granted ruling is also stamped in each archived doc's banner). `plan_reconciler_findings_2026_08_06.md`
      (`locked_by: plan_reconciler — run in progress`) and `plan_reconciler_findings_tradfi_2026_08_09.md`
      (`locked_by: plan_reconciler (agt-642862) since     2026-08-09T16:00:00Z`) each still carried their lock in the
      ACTIVE copy while an archived copy sat at `status: resolved` — so the archival had already been performed on the
      strength of an unlock nobody had issued. Both archived copies carried a banner asserting the `[unlock-plan]` had
      already been granted that same day; no such grant existed until 2026-08-10, which is precisely why the locked live
      copies survived and the pairs persisted. (Paraphrased deliberately — quoting that sentence verbatim trips
      `scripts/quality_gates/check_plan_operator_ruling_evidence.py`, which matches the literal phrase and cannot tell a
      quotation from an assertion. Same shape as `check_conflict_markers.sh`: with literal-string gates, describe the
      bad text, never reproduce it.) With the ruling now given: both banners corrected to cite the REAL ruling and to
      record that the claim originally ran ahead of its authority, the `related:` ref the archive copy of `2026_08_06`
      had lost (`[]` vs the active copy's `tradfi_consolidated_closeout_2026_07_18.md`) carried forward, both stale
      active copies deleted (`unified-trading-pm@f989e49532`). The matching `ALLOWED_DUPLICATE_STEMS` shrink is written
      and verified green locally but is NOT yet on origin — see the [SCRIPT] P2 todo below for why and what is left.
- [x] ✅ [DOCS] P3. **DONE 2026-08-10 — and the premise of this todo was wrong; correcting it is the finding.** Neither
      pair was content-diverged. `diff` reported 30 lines "only in the active copy" of
      `ao_satellite_ao_dispatch_batch2_2026_07_30.md`, and I recorded that as unique verification detail — it was the
      SAME text reflowed inside a wide markdown table cell. Under `diff -w -B` the whole pair differs by exactly two
      frontmatter lines (`status: active` + `archive_exempt: true` on the active side) against the archive's
      `status: resolved` + `resolved_by:` + ARCHIVED banner: the archive is a strict superset and the active copy was
      simply stale. For `infra_satellite_ao_dispatch_batch7_2026_08_04.md` I had it backwards too — the "2 extra
      `related:` refs" on the active side were the CORRECTED ones (pointing at `plans/archive/2026_08/issues/…`), while
      the ARCHIVE copy still carried the pre-archival `plans/active/issues/…` paths, both now dangling. So the merge was
      the reverse direction of what this todo described: fix the archive copy's 2 refs, then delete the active copy.
      **Lesson**: a raw `diff` line count is not a measure of content divergence in a prose corpus that reflows — check
      `diff -w -B` before calling two documents different, or a reformat reads as 30 lines of lost work.
- [ ] [DOCS] P3. **Reconcile the last 3 pairs — the `ag_closeout_audit_{cefi,prediction,tradfi}_parked_2026_08_10.md`
      slug collisions.** These are the ONLY entries left on `ALLOWED_DUPLICATE_STEMS` besides the intentional
      `INDEX.md`. Unlike the other seven, both sides here are REAL, independently-authored audit reports that happen to
      share a slug: the archive copy is the earlier same-day run, the active copy a later one (cefi 61L vs 151L,
      prediction 172L vs 115L, tradfi 95L vs 302L — note the size relationship is not consistent, so there is no "the
      bigger one wins" shortcut). Verify with `diff -w -B` first (a raw `diff` overstates divergence here, per the todo
      above). The RECURRENCE is already closed — the skill now checks `plans/archive/**` before writing a slug
      (`unified-trading-pm@ced0ff96b9`) — so this is bounded cleanup of 3 existing docs, not an open-ended class. **Done
      when**: each pair is either merged into one doc or split onto distinct slugs, both sides' findings are preserved
      (neither run's findings may be dropped on the grounds that the other exists), referrers are repointed, and all 3
      stems come off `ALLOWED_DUPLICATE_STEMS` leaving only `INDEX.md`.
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-10 — `unified-trading-pm@843df70447` (LDR, post-push ancestry verified; whole-tree
      re-gate green). Land the `ALLOWED_DUPLICATE_STEMS` 8→4 shrink** in
      `scripts/plan-hygiene/check_create_only_archive_commits.py` (drop `plan_reconciler_findings_2026_08_06.md`,
      `plan_reconciler_findings_tradfi_2026_08_09.md`, `ao_satellite_ao_dispatch_batch2_2026_07_30.md`,
      `infra_satellite_ao_dispatch_batch7_2026_08_04.md` — all four pairs reconciled in
      `unified-trading-pm@f989e49532`). The edit is written and verified locally (`ruff` clean; the guard reports
      `no create-only archive/active duplicate pairs at HEAD` with the shrunk list), but **three failures unrelated to
      it blocked the quickmerge re-gate**, which validates the whole current tree rather than just the named files — and
      in a shared checkout that tree carries other sessions' in-flight work: (1) the QG duration budget, twice, under 12
      concurrent QG runs / load 38; (2) a peer's UNCOMMITTED `cursor-configs/CLAUDE.md` edit pushing it 3 B over the
      40,960 B cap while `HEAD` sat comfortably under at 40,804 B; (3) the unresolvable-sha regression filed as a
      recurrence on `/plans/active/issues/plan_commit_sha_evidence_unresolvable_0f9b8a65ca_2026_08_10.md`. None of the
      three recurred on this landing: the whole-tree re-gate passed within the duration budget, no peer
      `cursor-configs/CLAUDE.md` cap breach, and the unresolvable-sha recurrence was fixed by its owner. **Done when**:
      the shrink is on origin and the guard's list is the 3 `ag_closeout` stems + `INDEX.md`. ✅ **DONE — verified on
      origin**: guard reports `no create-only archive/active duplicate pairs at HEAD` with the shrunk list.

## Progress Log

- **2026-08-10** — Found and root-caused during the autonomous ag-closeout close-out. The 17 duplicates were recovered
  the same session via `SDP_ISOLATED=0`. Filed rather than fixed in-line because the fix touches a fleet-wide ship
  script every repo and every agent depends on, which wants its own regression test and blast-radius check (rule 11)
  rather than a same-session patch buried in a docs close-out.
- **slot-29 2026-08-10 (infra, todo 2, SHIPPED)**: "Fail loudly instead of skipping silently" — the isolated copy loop's
  `skipping copy` branch now exits 2 with a path-naming message when a named file is absent from the caller tree AND
  absent from `origin/$BRANCH` (a caller error), instead of logging at info level and silently dropping the path from
  the commit. Deletion case (absent here, tracked on origin) already handled by `18ae9a4312`. Shipped
  `unified-trading-pm@37bbd172be` via quickmerge; regression test updated
  (`tests/test_safe_doc_push_isolated_deletion_propagates.bats` now asserts exit 2 + path-naming for the caller-typo
  case), 24/24 bats tests + full `quality-gates.sh` green.
- **slot-1 2026-08-10 (todos 4+5, SHIPPED)** — The deletion-propagation fix was exercised live for the first time by
  this session's Kaiko archival (`c62dc42470`): the log printed `isolation: propagating deletion of …` and both docs
  landed as `R` renames with no surviving twin. That is the end-to-end proof the original defect is closed on the happy
  path. Widening `check_create_only_archive_commits.py` from mirrored-path to basename matching then exposed 8 further
  pairs; see the sweep table. **A caution for whoever picks up the 3 remaining todos**: the guard is now the corpus's
  only mechanical duplicate detector, and its `ALLOWED_DUPLICATE_STEMS` ratchet is the ONLY record that those 7 pairs
  are known-and-triaged rather than unnoticed. Removing a stem without actually reconciling the pair re-hides it.
- **slot-1 2026-08-10 (ship log — two blockers hit, both worth knowing before the next attempt)**. The guard landed as
  `unified-trading-pm@689e10d281` only on the THIRD quickmerge attempt, and neither earlier failure was in the change:
  (a) **timing** — `❌ Quality gates must complete in <600s (took 724s work + 814s governor queue-wait = 1538s wall)`;
  the gate counts the governor's own admission queue-wait, so a throttled run fails for having been throttled (filed as
  a todo on `/plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`). It passed once bats parallelization
  (`974dfc2de9`, 663s→115s) landed from another session and brought the work side under budget. (b) **conflict-markers**
  — quickmerge's own internal `pull --rebase --autostash` popped a stale autostash over two files a concurrent
  safe-doc-push of mine had just landed, leaving git conflict markers in the tree that failed its post-gate check
  (writing that marker literally here, even fenced in backticks, trips `check_conflict_markers.sh` — it matches the raw
  string on purpose, so describe it, never quote it). **Do not run a safe-doc-push touching other files while a
  quickmerge is mid-flight in the same checkout** — they share one working tree and one stash stack. Also measured, and
  NOT this change's fault: PM's bats suite has ~37-60 failing tests on macOS (`sed -i` BSD-vs-GNU and similar) that pass
  on the Linux AO VM where they were authored; they are non-blocking for the gate but make "is my change green?"
  genuinely hard to read from the log.

## Full sweep — 10 duplicate pairs on origin, with a verdict each (closes todo 5)

An earlier pass here recorded only 2 pairs, found via `scripts/plan-hygiene/archive_completed_parked_reports.py`. **That
count was wrong, and the reason matters**: both that tool and the `check_create_only_archive_commits.py` guard compared
a mirrored path (`plans/archive/issues/` ↔ `plans/active/issues/`). Real archivals land in DATED directories, so the
mirrored-path assumption was blind to the majority of the corpus. Re-running the sweep by **basename across every
`plans/archive/**` subdirectory** found 10:

| pair (basename)                                              | verdict                                                                                           |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`          | **RECONCILED** — active strictly stale (2 open todos are `[x]`+evidence in archive); deleted      |
| `tradfi_satellite_ao_dispatch_batch6_2026_08_01_finalize.md` | **RECONCILED** — same shape, 3 stale open todos; deleted                                          |
| `promote_ref_orphaned_on_manual_pr_close_2026_08_06.md`      | **INTENDED** — active is a documented redirect stub (`title: MOVED —`, `status: blocked`)         |
| `plan_reconciler_findings_2026_08_06.md`                     | **RECONCILED** — `[unlock-plan]` granted 2026-08-10; lost `related:` ref restored, active deleted |
| `plan_reconciler_findings_tradfi_2026_08_09.md`              | **RECONCILED** — `[unlock-plan]` granted 2026-08-10; active deleted                               |
| `ag_closeout_audit_cefi_parked_2026_08_10.md`                | **SKILL DEFECT** — active is a NEWER, independent audit report re-created at an archived slug     |
| `ag_closeout_audit_prediction_parked_2026_08_10.md`          | **SKILL DEFECT** — same                                                                           |
| `ag_closeout_audit_tradfi_parked_2026_08_10.md`              | **SKILL DEFECT** — same                                                                           |
| `ao_satellite_ao_dispatch_batch2_2026_07_30.md`              | **RECONCILED** — NOT diverged; the 30 lines were reflowed table text. Archive superset; deleted   |
| `infra_satellite_ao_dispatch_batch7_2026_08_04.md`           | **RECONCILED** — the ARCHIVE copy held the 2 stale refs; fixed there, then active deleted         |

**Three lessons this sweep paid for, worth more than the pair count:**

1. **"Duplicate" was three different failure modes wearing one name.** Only 2 of 10 were the create-only shape this doc
   was filed about. Three were a _later_ audit run re-creating an already-archived slug (a forward-writing defect, not a
   dropped deletion); two were archivals of a LOCKED doc; one was deliberate. A sweep that had blind-deleted "the
   duplicate" would have destroyed newer content, completed an unauthorised unlock, and broken a link the stub exists to
   keep alive.
2. **The blast radius of a duplicate is not the duplicate.** The 2 reconciled pairs were feeding **5 phantom open
   todos** into the AO dispatch backlog for work already flipped `[x]` with evidence — agents were being dispatched to
   redo finished work. Deleting them also required repointing **16 references across 10 docs**, debt the original
   create-only archival commit silently deferred.
3. **A guard reporting zero is not evidence of zero.** This one printed a clean `✅` for the entire window while all 10
   pairs sat on origin. The correct reading of a green check is "the condition it actually tests is absent" — confirm
   the test's scope matches the claim before trusting it.

The archival tool now REFUSES to `git mv` onto an existing destination and reports an identical-vs-diverged verdict
instead — before hardening it raised `CalledProcessError` mid-run, having already written `status: resolved` into the
source doc (that partial write was reverted, not committed).
