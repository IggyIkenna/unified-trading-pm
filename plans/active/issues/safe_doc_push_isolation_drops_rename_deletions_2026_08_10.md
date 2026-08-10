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
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-10 — the assertion existed but was structurally blind; coverage widened.**
      `scripts/plan-hygiene/check_create_only_archive_commits.py` (added `43e88b720d`, already wired into
      `run_hygiene_sweep.sh` as a HARD check) did assert the both-sides shape — but only for `plans/archive/issues/`
      against `plans/active/issues/`, via a path substitution. **Real archivals land in DATED directories**
      (`plans/archive/2026_08/issues/X.md`, `plans/archive/2026_08/X.md`), which that substitution never matched, so the
      guard reported a clean corpus while **10 live duplicate pairs sat on origin**. Rewritten to match by BASENAME
      across all of `plans/archive/**` vs `plans/active/**`, with two exemptions that keep the signal honest:
      `ALLOWED_DUPLICATE_STEMS` (a shrinking ratchet of pre-existing pairs, each carrying a recorded verdict — a pair
      NOT listed fails immediately, so no new duplicate can hide behind a shrinking count) and `_is_redirect_stub()` (an
      INTENDED pair). Verified: flags exactly the 2 genuinely-stale pairs, exempts the other 8, `ruff check` +
      `ruff format --check` clean.
- [x] ✅ [REVIEW] P2. **DONE 2026-08-10 — full sweep run; 10 pairs found, each given a verdict** (table below). 2
      reconciled here by deleting the strictly-stale active copy (16 referrer repoints across 10 docs); 1 is an
      intentional redirect stub; the remaining 7 are carried on the ratchet with per-pair verdicts and the 3 follow-up
      todos below. Sweeping by basename across every archive subdirectory — rather than by the mirrored path the old
      guard assumed — is what surfaced the 8 pairs beyond the 2 recorded here earlier.
- [ ] [SCRIPT] P1. **Stop `/ag-closeout-audit` re-creating an already-archived slug.** Root cause of 3 of the 10 pairs:
      the skill writes its per-tranche parked report to
      `plans/active/issues/ag_closeout_audit_<tranche>_parked_<date>.md` without checking whether that exact slug is
      already archived, so a later run resurrects it at the active path — `42247c0405`, `064019f77f` and `6b7ddb7944`
      each `A`-added a doc an earlier commit had archived. **Done when**: the skill checks `plans/archive/**` for the
      slug before writing and either appends to the archived doc or picks a distinct slug, and the 3 stems come off
      `ALLOWED_DUPLICATE_STEMS`.
- [ ] [OPERATOR] P2. **Two LOCKED docs were archived without an unlock.** `plan_reconciler_findings_2026_08_06.md`
      (`locked_by: plan_reconciler — run in progress`) and `plan_reconciler_findings_tradfi_2026_08_09.md`
      (`locked_by: plan_reconciler (agt-642862) since 2026-08-09T16:00:00Z`) each still carry their lock in the ACTIVE
      copy while an archived copy sits at `status: resolved`. Archiving a locked plan is human-only, so deleting the
      active copy would silently complete an unauthorised unlock — left untouched deliberately. The `[unlock-plan]` ask
      is already tracked in `/plans/active/issues/ag_closeout_audit_tradfi_parked_2026_08_10.md`. **Done when**: the
      operator rules on the unlock, the surviving copy is reconciled, and both stems come off the ratchet.
- [ ] [DOCS] P3. **Merge the 2 content-diverged pairs.** `ao_satellite_ao_dispatch_batch2_2026_07_30.md` (the active
      copy carries 30 lines of unique verification detail with shas, plus `archive_exempt: true`) and
      `infra_satellite_ao_dispatch_batch7_2026_08_04.md` (active carries 2 extra `related:` refs + `superseded_by`).
      Neither active copy is a stale duplicate, so neither may be deleted. **Done when**: the unique content is merged
      into the archived copy, the active copy removed, and both stems come off the ratchet.

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

## Full sweep — 10 duplicate pairs on origin, with a verdict each (closes todo 5)

An earlier pass here recorded only 2 pairs, found via `scripts/plan-hygiene/archive_completed_parked_reports.py`. **That
count was wrong, and the reason matters**: both that tool and the `check_create_only_archive_commits.py` guard compared
a mirrored path (`plans/archive/issues/` ↔ `plans/active/issues/`). Real archivals land in DATED directories, so the
mirrored-path assumption was blind to the majority of the corpus. Re-running the sweep by **basename across every
`plans/archive/**` subdirectory** found 10:

| pair (basename)                                              | verdict                                                                                       |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`          | **RECONCILED** — active strictly stale (2 open todos are `[x]`+evidence in archive); deleted  |
| `tradfi_satellite_ao_dispatch_batch6_2026_08_01_finalize.md` | **RECONCILED** — same shape, 3 stale open todos; deleted                                      |
| `promote_ref_orphaned_on_manual_pr_close_2026_08_06.md`      | **INTENDED** — active is a documented redirect stub (`title: MOVED —`, `status: blocked`)     |
| `plan_reconciler_findings_2026_08_06.md`                     | **OPERATOR-GATED** — active still `locked_by`; archiving a locked plan is human-only          |
| `plan_reconciler_findings_tradfi_2026_08_09.md`              | **OPERATOR-GATED** — same                                                                     |
| `ag_closeout_audit_cefi_parked_2026_08_10.md`                | **SKILL DEFECT** — active is a NEWER, independent audit report re-created at an archived slug |
| `ag_closeout_audit_prediction_parked_2026_08_10.md`          | **SKILL DEFECT** — same                                                                       |
| `ag_closeout_audit_tradfi_parked_2026_08_10.md`              | **SKILL DEFECT** — same                                                                       |
| `ao_satellite_ao_dispatch_batch2_2026_07_30.md`              | **MERGE** — active holds 30 lines of unique verification detail; not a stale copy             |
| `infra_satellite_ao_dispatch_batch7_2026_08_04.md`           | **MERGE** — active holds 2 extra `related:` refs + `superseded_by`                            |

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
