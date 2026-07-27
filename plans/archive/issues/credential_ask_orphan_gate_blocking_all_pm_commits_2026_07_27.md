---
doc_type: issue
title:
  "credential-ask-orphan QG blocking ALL unified-trading-pm commits repo-wide (2 well-documented findings missing the
  strict ping-citation format)"
summary:
  "check_credential_ask_orphans.py (ratchet mode, baseline=1) is failing on 2 orphan BLOCKED-CREDENTIALS lines — both
  are real, well-documented, dated findings (not careless/vague asks), but neither cites a ping file in the exact format
  the checker requires. Because this check runs against the WHOLE tree on every quickmerge's re-gate (not scoped to the
  committer's own changeset), it is currently blocking every slot's commits to unified-trading-pm, not just the
  finding's own author."
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, credential-ask-orphan, repo-wide-blocker, false-positive-risk]
related: []
created: 2026-07-27
priority: P1
parent_epic: infrastructure_master
source: "4 consecutive PM quickmerge attempts blocked on this same check, 2026-07-27 (slot-3)"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by: unified-trading-pm@bb6a25da7
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **🟢 RESOLVED 2026-07-27** — pings filed for both orphan `BLOCKED-CREDENTIALS` findings
> (`unified-trading-pm@bb6a25da7`); `check_credential_ask_orphans.py` verified at 0 orphans, at-or-below baseline. The
> repo-wide commit block is over. Archived per issue-doc-lifecycle; the P2 scoping-improvement suggestion below stays
> open as a low-priority follow-up.

# credential-ask-orphan gate blocking all PM commits (2026-07-27)

## What's happening

`scripts/quality_gates/check_credential_ask_orphans.py` runs in ratchet mode with baseline=1. As of this writing it
finds 2 orphan lines:

1. `plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md:240` —
   `**BLOCKED-CREDENTIALS 2026-07-27 (slot-12).**` — a real, dated, well-described finding: terraform declares the IAM
   bindings but the active CI credential lacks `resourcemanager.projects.{get,set}IamPolicy` to apply them.
2. `plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md:418` —
   `**FINDING — ICE futures + CME futures-options not on Massive → BLOCKED-CREDENTIALS.**` — also real and documented,
   with an explicit "Operator ask" line.

Neither is vague or careless — both clearly state the ask and the blocker. Neither cites a ping file
(`ikenna_orchestrator/pings/slot_N.md`) in the exact format the checker's regex/parser expects.

## Why this is bigger than either individual finding

`check_credential_ask_orphans.py` scans the **whole tree's current state**, not the committer's own changeset. This
means it is not scoped like most of the other Pass-1 checks — a change to file A can be blocked by an orphan line in
completely unrelated file B, written by a different slot, at a different time, for a different task.

Measured this session: 2 consecutive PM quickmerge attempts (unrelated to either flagged file — shipping a
`data_pipeline_check_mdps_features_2026_07_20.md` todo split + a new issue doc) failed on this exact check, back to
back, with identical output. Until slot-12 (or whoever owns the second finding) adds a proper ping citation or
re-baselines, **every slot's commit to unified-trading-pm is blocked**, regardless of what that commit touches.

## Why I didn't just fix it myself

The checker offers `--baseline-write` as an "if intentional debt" escape hatch, but re-baselining someone else's
just-created finding on their behalf — without knowing whether a ping is already in flight, or whether the missing
citation itself signals something not actually approved — isn't a call I should make unilaterally from an unrelated
task. The finding's owner (or the operator) is better positioned to either file the ping or consciously accept the
ratchet-down.

## Todos

- [x] [OPERATOR] P1. ✅ **RESOLVED 2026-07-27 (already done by another session before this todo was re-surfaced)** —
      `unified-trading-pm@bb6a25da7` filed pings for both findings inline (`ikenna_orchestrator/pings/slot_5.md`,
      "CREDENTIAL APPROVAL REQUEST — 2026-07-27 (slot-5, filed to close a credential-ask-orphan QG regression)").
      Verified live, this session: `python3 scripts/quality_gates/check_credential_ask_orphans.py` →
      `OK — 0 orphan BLOCKED-CREDENTIALS (at-or-below baseline 2)`. The repo-wide commit block is over; this was option
      (a), not a re-baseline. No operator action was actually needed once the pings landed — the [OPERATOR] tag should
      have been closed the moment `bb6a25da7` shipped, not left open for a future dashboard cycle to re-ask.
- [ ] [SCRIPT] P2. Consider scoping `check_credential_ask_orphans.py` to the committer's own `--files` changeset (like
      most other Pass-1 checks) rather than the whole tree, OR moving it to a scheduled/nightly sweep instead of a
      per-commit gate — a repo-wide, unscoped ratchet check that can be tripped by an unrelated slot's finding is a
      structural false-positive risk for every other committer, not just this one incident.
