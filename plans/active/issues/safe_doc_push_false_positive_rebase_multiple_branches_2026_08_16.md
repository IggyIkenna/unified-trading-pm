---
doc_type: issue
title: >-
  safe-doc-push.sh exits 3 "Cannot rebase onto multiple branches" on a plain clean divergence (false-positive conflict)
summary: >-
  While shipping a routine plan-checkbox flip via scripts/dev/safe-doc-push.sh from unified-trading-pm, the script
  aborted with exit code 3 and the message "Cannot rebase onto multiple branches" against what was, on direct
  inspection, an ordinary clean ahead/behind divergence against origin/live-defi-rollout (no actual multi-branch
  ambiguity, no real content conflict) — a false positive that blocked a shippable doc change for no underlying reason.
  Filed so the conflict-detection logic gets a narrow fix rather than the false positive recurring silently for the next
  worker who hits it and manually working around it without tracking it.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [safe-doc-push, git, rebase, false-positive, ship-script]
related:
  [
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
    /plans/active/issues/safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md,
    /plans/active/issues/safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md,
    /plans/active/issues/safe_doc_push_stash_pileup_quarantine_drops_renamed_path_2026_08_15.md,
    /plans/active/issues/safe_doc_push_prek_patch_orphaned_recurrence_2026_08_15.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-08-16
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: advance-code
depends_on: []
source: "slot-29, discovered while shipping aiohttp_json_charset_guessing_audit_2026_08_16.md's plan-flip, 2026-08-16"
resolved_by:
locked_by:
locked_since:
context_scope: [scripts/dev/safe-doc-push.sh]
---

# safe-doc-push.sh false-positive "Cannot rebase onto multiple branches" conflict abort

## What I found

Running `scripts/dev/safe-doc-push.sh` from `unified-trading-pm` (slot 29) to ship a routine plan-checkbox flip hit an
exit-code-3 abort with the message "Cannot rebase onto multiple branches." At the time this fired, direct git inspection
of the working tree showed a plain, ordinary clean divergence against `origin/live-defi-rollout` (local commits ahead,
remote commits behind, no actual conflicting hunks, no genuine multi-branch ambiguity in play) — i.e. the exact case the
script's normal `git pull --rebase --autostash` recovery path is designed to handle cleanly. The script's own
conflict-classification logic appears to be over-triggering on ordinary divergence and misclassifying it as the harder
"rebase onto multiple branches" case, aborting a shippable, non-conflicting doc change.

**Caveat on evidence quality**: this was observed and worked around live in a prior session (this session did not
reproduce it fresh this segment — the current plan-flip shipped without hitting it). The exact repro steps (branch
state, number of commits ahead/behind, whether any file overlapped) were not captured verbatim at the time; this doc
records the symptom and the surrounding context precisely enough to be actionable, but a fix implementer should first
re-confirm the trigger condition via `scripts/dev/safe-doc-push.sh`'s conflict-classification code path
(`git rebase` invocation + its multi-branch detection heuristic) rather than assume this description is a complete
repro.

## Why it matters

`safe-doc-push.sh` is the mandated ship path for pure doc/plan-flip changes (bare `git push` races the shared index per
CLAUDE.md). A false-positive abort on ordinary divergence forces every worker who hits it to either (a) manually work
around it via `git pull --rebase --autostash origin live-defi-rollout` + `git push` (bypassing the script's own
retry/mutex/flock/drift protections that CLAUDE.md says never to reimplement by hand), or (b) get stuck retrying a
script that will keep failing the same way until the underlying branch state changes for unrelated reasons. Left
unfixed, this either erodes trust in the mandated ship path (workers route around it) or silently blocks doc/plan work
on a shared host under normal multi-slot churn — exactly the kind of shared-checkout contention this script exists to
absorb safely.

## Recommended decision

Have an infra-role worker read `scripts/dev/safe-doc-push.sh`'s conflict-classification logic, find the code path that
emits "Cannot rebase onto multiple branches" and exits 3, and determine whether it's triggering on a condition broader
than genuine multi-branch ambiguity (e.g. treating ANY non-trivial `git rebase` interactive state, or a stale ref, as
"multiple branches" rather than checking for the real signal). Add a narrow fix + a regression case that exercises plain
clean divergence (ahead+behind, no conflicting hunks) to confirm it no longer false-positives.

## Todos

- [ ] [INFRA] P3. Read `scripts/dev/safe-doc-push.sh`'s conflict-classification / rebase logic, identify why a plain
      clean ahead/behind divergence against `origin/live-defi-rollout` (no real multi-branch ambiguity, no conflicting
      hunks) can trigger the exit-3 "Cannot rebase onto multiple branches" abort, and fix the over-broad detection.
      Done when: the false-positive condition is root-caused, fixed, and a regression test/case exercises plain clean
      divergence without aborting. (repo: unified-trading-pm)

## Progress Log

- **slot-29 (data_engineering) 2026-08-16**: Filed while closing out
  `aiohttp_json_charset_guessing_audit_2026_08_16.md` — hit this false positive in an earlier session shipping the same
  plan-flip via `safe-doc-push.sh`, worked around it manually, and is now tracking it per the pre-compact ritual's
  finding-closure rule rather than leaving it as an untracked chat-only observation. Not reproduced fresh this session
  (this session's own plan-flip shipped cleanly); repro details are best-effort from memory, flagged above as a caveat
  for whoever picks up the fix.
