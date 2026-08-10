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
- [ ] [SCRIPT] P1. **Fail loudly instead of skipping silently.** The `skipping copy` branch currently logs at info level
      and proceeds. A named file that is absent from the caller tree AND absent from HEAD is a caller error; absent from
      the caller tree but PRESENT in HEAD is a deletion. Distinguish the two and never silently no-op a named path.
      **Done when**: the ambiguous case exits non-zero with a message naming the path.
- [ ] [DOCS] P1. **Correct the archival-ritual SSOT.**
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § "must not drop the rename's delete side"
      currently presents safe-doc-push as the preferred safe shape with no isolation caveat. Until the fix above ships,
      it must say that isolated mode drops deletions and that a rename needs `SDP_ISOLATED=0` (or a verified both-sides
      commit). **Done when**: the section names the isolation caveat and cites this doc.
- [ ] [SCRIPT] P2. **Add a post-commit assertion to the ritual.** After any archival commit, assert
      `git show --name-status <sha>` contains a `D`/`R` for every `plans/active/**` path named. A create-only archival
      commit should fail the ship script, not reach origin. **Done when**: the check exists and is wired into the same
      place the provenance check runs.
- [ ] [REVIEW] P2. **Sweep for other create-only archival commits since isolation went default (2026-08-10).** Any
      archival routed through safe-doc-push in that window has the same defect. **Done when**: every commit touching
      `plans/archive/**` since isolation shipped is checked for a missing delete side, and any duplicate pair found is
      reconciled (compare both copies first — reconcile divergence, do not blind-delete).

## Progress Log

- **2026-08-10** — Found and root-caused during the autonomous ag-closeout close-out. The 17 duplicates were recovered
  the same session via `SDP_ISOLATED=0`. Filed rather than fixed in-line because the fix touches a fleet-wide ship
  script every repo and every agent depends on, which wants its own regression test and blast-radius check (rule 11)
  rather than a same-session patch buried in a docs close-out.

## Sweep result — TWO diverged pairs found 2026-08-10 (feeds todo 5)

Running `scripts/plan-hygiene/archive_completed_parked_reports.py` (promoted from this session's scratchpad) surfaced
two live duplicate pairs beyond the 17 already recovered in `1653006e52`:

| doc                                                 | state                                                                                            |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `ag_closeout_audit_prediction_parked_2026_08_10.md` | exists at BOTH `plans/active/issues/` and `plans/archive/2026_08/issues/`, contents **DIVERGED** |
| `ag_closeout_audit_tradfi_parked_2026_08_10.md`     | exists at BOTH paths, contents **DIVERGED**                                                      |

Neither was touched. Divergence means the archived copy is NOT automatically authoritative — the two have taken
different edits since the split, exactly the drift the 2026-08-06 incident documented (5 diverged pairs). Reconciling
them is a per-doc read-and-merge, not a delete, so it belongs to todo 5 rather than being done blind here.

The script now REFUSES to `git mv` onto an existing destination and reports the pair with an identical-vs-diverged
verdict instead — before hardening it raised `CalledProcessError` mid-run, having already written `status: resolved`
into the source doc (that partial write was reverted, not committed).
