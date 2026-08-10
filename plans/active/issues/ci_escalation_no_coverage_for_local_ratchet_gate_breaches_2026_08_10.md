---
doc_type: issue
title:
  "AO escalation/CI-role machinery has NO coverage for a local quickmerge ratchet-gate breach — structural signal-path
  gap, not a bug"
summary: >-
  Investigated why `agent-orchestrator`'s escalation queue / CI-failure-watcher machinery never caught the
  `market-tick-data-service` TID251 ratchet breach (`mtds_tid251_ratchet_breach_blocks_all_quickmerges_2026_08_09.md`)
  fleet-wide-blocking incident. Finding: `server/escalation.py`'s `WALL_TYPES` is a CLOSED set (`merge_conflict,
  label_mismatch, sit_failure, stuck_promotion_pr, ldr_qg_failure, ldr_main_qg_failure, main_ci_red, plan_health,
  sit_retry_cap`, + a data-pipeline wall) and every one of them is keyed on a GitHub Actions run CONCLUSION for a pushed
  branch/PR (`repo_ldr_qg_conclusion()` in `server/ci_reconcile.py` polls the GH Actions runs API). QG STEP 5.95 (the
  DTZ/TID251 ratchet) runs INSIDE `quality-gates.sh`'s Pass 1, entirely LOCAL, BEFORE any `git push` — a failure there
  means the commit never reaches origin, so no PR, no GH Actions run, and structurally NOTHING for the escalation queue
  to observe. This is not a bug in an existing mechanism; it is a class of failure with no detection surface in the
  current design. Confirmed empirically: the one remediation that DID happen (`e72feb7c`, "shorten TID251 noqa to
  survive ruff's line-length formatter") was authored by the SAME slot (`slot-3·planning`) that had landed the breaking
  commit (`8c40ca8d`) ~1h earlier, in a normal sequence of unrelated fixes across repos (`32fd7ed7`, `8c40ca8d`,
  `ff6c2f4a`, `e72feb7c`, `fc9e36cd`) — ordinary worker self-correction on hitting its own wall on a LATER unrelated
  quickmerge, per the standing "findings triage: in your file → fix in same commit" rule, NOT a dispatched CI-incident
  response. A live AO backlog query for `market-tick-data-service` (6 matching tasks) shows zero tasks referencing
  TID251/ratchet. Filed as its own issue per the task's instruction not to build a new escalation integration inline —
  wiring ratchet-breach detection into the escalation machinery is real, separately-scoped infra work.
status: open
nature: issue
asset_group: [cross-cutting, meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [escalation, ci, quality-gates, ratchet, coverage-gap, ci-failure-watcher, P2]
created: 2026-08-10
author: unknown
priority: P2
parent_epic: escalation_and_disaster_recovery_master
source: >-
  Part B of the investigation into `mtds_tid251_ratchet_breach_blocks_all_quickmerges_2026_08_09.md` — that issue asked
  whether the AO escalation/CI-role mechanism should have auto-caught/auto-fixed the incident, and if not, why not.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-infra
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
context_scope:
  [
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/ci_reconcile.py,
    unified-trading-pm/scripts/quality_gates/check_ruff_rule_ratchet.py,
    plans/archive/2026_08/issues/mtds_tid251_ratchet_breach_blocks_all_quickmerges_2026_08_09.md,
  ]
related: [/plans/archive/2026_08/issues/mtds_tid251_ratchet_breach_blocks_all_quickmerges_2026_08_09.md]
---

## Evidence

### 1. The escalation queue's wall-type set is entirely GH-Actions-run-conclusion-based

`agent-orchestrator/server/escalation.py` `WALL_TYPES` (a closed `frozenset`):

```
merge_conflict, label_mismatch, sit_failure, stuck_promotion_pr, ldr_qg_failure,
ldr_main_qg_failure, main_ci_red, plan_health, sit_retry_cap, (+ a DP_* data-pipeline wall)
```

Every code-quality wall in that set (`ldr_qg_failure`, `ldr_main_qg_failure`, `main_ci_red`, `sit_failure`,
`sit_retry_cap`) is driven by `server/ci_reconcile.py`'s `repo_ldr_qg_conclusion()` / `is_genuine_qg_failure()`, which
poll the **GitHub Actions runs API** for a pushed branch/PR (`_qg_runs_endpoint`, `_latest_qg_run_id`, `_run_jobs`).
There is no wall type for "a contributor's local `quality-gates.sh` run failed before they ever pushed."

### 2. QG STEP 5.95 (the DTZ/TID251 ratchet) runs entirely local, pre-push

Per `unified-trading-pm/codex/06-coding-standards/quality-gates.md` and directly observed running
`bash scripts/quickmerge.sh` twice on `market-tick-data-service` in this session: STEP 5.95 is Pass 1 of
`quality-gates.sh`, invoked from the contributor's own machine/VM **before** `quickmerge.sh` Stage 5 ever pushes/opens a
PR. A failure here means the commit is never pushed — no PR is opened, no GitHub Actions workflow ever runs for it, so
`ci_reconcile.py`'s GH-run-polling has nothing to observe. This is a structurally different signal path from every wall
type the escalation queue understands, confirmed by reading the wall-type set and its trigger functions directly (not
inferred).

### 3. The one remediation that happened was ordinary self-correction, not incident response

`git log --author=slot-3 --oneline` on `market-tick-data-service`, 2026-08-09 15:00-19:00 UTC window:

```
e72feb7c fix(one-offs): shorten TID251 noqa to survive ruff's line-length formatter
ff6c2f4a fix(tradfi): harden migrate_tradfi_canonical_2026_07.py against 2 confirmed recurrence risks
8c40ca8d perf(defi): size the GCS storage client's HTTP connection pool to --workers ...
32fd7ed7 perf(defi): parallelize rebuild_defi_manifest's per-day GCS scan (--workers) ...
fc9e36cd fix(sports): restore BetfairAdapter deleted as dead code
```

`8c40ca8d` (the commit that introduced the ratchet breach) and `e72feb7c` (the fix) were authored by the **same slot**
(`ikennaigboaka [slot-3·planning]`), ~53 minutes apart, interleaved with unrelated fixes in other domains (tradfi,
sports). This is the shape of one AO worker grinding through a normal sequence of plan todos, hitting its own earlier
regression on a later unrelated `quickmerge.sh` re-gate, and self-triaging per the standing HARD RULE ("Findings triage:
in your file → fix in same commit") — not a centrally-dispatched CI-incident-response role reacting to a detected
failure.

Empirically verified `e72feb7c`'s fix was itself CORRECT (a single-line
`from google.cloud import storage  # noqa: TID251 -- ...` anchors the noqa on the diagnostic's own line, vs. the prior
multi-line form which put the noqa on a continuation line ruff does not associate with the diagnostic — the actual root
cause of the 8c40ca8 breach, per `quality-gates.md`'s own documented caveat: "a parenthesized-import continuation line
does NOT suppress"). Ran `ruff check --isolated --select TID251` directly against `e72feb7c`'s version of the file: `[]`
(zero violations) — the fix would have restored the ratchet to baseline on its own, had every slot's local checkout
picked it up before their own next quickmerge attempt.

### 4. No standing task tracks this failure class

Live AO backlog query (`agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh market-tick-data-service`,
read-only via SSM): 6 matching tasks, none referencing TID251, the ratchet, or quality-gates ceiling breaches. Confirms
no existing plan/role is watching for this.

## Root-cause classification

Per the task's own taxonomy: this is **(c) — no CI/CICD AO role actually watches this failure class at all**, compounded
by **(a) — the underlying signal never reaches a GitHub Actions run in the first place** (local pre-push gate, by
design). It is explicitly **not** (b) — nothing sat "queued but unactioned" in the escalation queue, because nothing was
ever enqueued; the wall-type set has no slot for it.

A second-order effect worth naming: even if a slot's own quickmerge self-corrects the ratchet (as `e72feb7c` did), every
OTHER slot with an already-stale local checkout (cloned/fetched before the fix landed) independently rediscovers the
SAME blocking wall on their own next quickmerge attempt, because `quickmerge.sh`'s STAGE 0.4 fetch+rebase only
reconciles at THAT moment — there is no push-time notification telling other slots "a shared ratchet baseline was just
breached, don't bother re-diagnosing it." This session's own start is an instance of that: the local checkout read the
pre-`e72feb7c` (still-broken) file content before quickmerge's own fetch+rebase pulled the fix in, causing a genuine
merge conflict against an independently-authored, deeper fix (extending
`unified_trading_library.cloud_interface.StorageClient` to support generation-pinned range reads, resolved in favor of
the deeper fix — see the parent issue doc).

## Why this is filed, not fixed inline

Per this task's explicit instruction: a real fix here — wiring ratchet-breach detection into the existing escalation
machinery — is a genuinely separate, non-trivial piece of infrastructure work, not a small clearly-scoped gap:

- It needs a NEW detector (e.g., a post-quickmerge or scheduled sweep that runs
  `check_ruff_rule_ratchet.py`/`check_no_fallback_imports.py`/`check_no_empty_string_fallback.py` fleet-wide against
  `origin/live-defi-rollout` HEAD per repo, independent of any one contributor's local run).
- It needs a NEW wall type (or a generalized "local-gate ceiling breach" class) plumbed through `server/escalation.py`'s
  `enqueue()`/dedup/cooldown machinery, since none of the existing GH-run-based wall types fit.
- It should probably also close the second-order staleness gap above (some way to tell an in-flight slot "the wall
  you're about to hit was already fixed upstream, pull before re-diagnosing") — plausibly Slack
  `agent-orchestrator-alerts`-channel-adjacent, per `/codex/04-architecture/agent-orchestrator-alerting.md`'s
  actionable-only + dedup-by-state-transition pattern, but that is a design call for whoever scopes this, not this
  filing.

## Resolution options

1. **Scope + build a fleet-wide ratchet/baseline-ceiling detector + escalation wall type** as its own plan
   (AO-dispatched, `assigned_vm: planning`, once scoped — ask the operator per the "AO plan or human plan?" hard rule
   before authoring).
2. **Accept the gap as a known, bounded cost**: this class of incident is self-limiting (the FIRST slot to
   next-quickmerge the affected repo either self-fixes it — as observed — or files an issue, both of which already
   happened here within ~1h and ~few hours respectively) and operator may judge the infra cost of building dedicated
   detection isn't worth it relative to its actual blast radius/frequency.

## Status

Open — a genuine, evidenced coverage gap, filed for operator/planning triage per this task's instruction not to build
the fix inline. Does not block anything currently (the originating incident is resolved — see
`/plans/archive/2026_08/issues/mtds_tid251_ratchet_breach_blocks_all_quickmerges_2026_08_09.md`).
