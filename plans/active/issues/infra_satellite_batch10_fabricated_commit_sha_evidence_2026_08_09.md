---
doc_type: issue
title: "Plan-flip cited a non-existent git SHA as completion evidence (unified-trading-pm@b277df233)"
summary: >-
  plans/archive/2026_08/infra_satellite_ao_dispatch_batch10_2026_08_09.md:146+231 (slot-33·planning, 2026-08-09) marks
  todo "Find what writes manifest-consolidate-* scratch..." DONE citing resolved_by: unified-trading-pm@b277df233. That
  SHA does not exist in unified-trading-pm's local history (`git cat-file -t` -> "Not a valid object name"; `git log
  --all --oneline | grep b277df2` -> zero hits). Discovered by scripts/quality_gates/check_plan_commit_sha_evidence.py
  while shipping an unrelated devops task ([B] in
  /plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md) — the check is repo-wide, not
  scoped to the shipping agent's own files, so it blocked Pass-1 QG on pre-existing debt. Same failure class as the
  archived precedent /plans/archive/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md (that instance is
  fully resolved; this is a fresh, independent occurrence, not a reopen).
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [findings-triage, false-progress, evidence-integrity, plan-hygiene]
related:
  [
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch10_2026_08_09.md,
    /plans/archive/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md,
  ]
created: 2026-08-09
author: unknown
priority: P2
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
source:
  [
    "discovered 2026-08-09 by scripts/quality_gates/check_plan_commit_sha_evidence.py while shipping the [B]
    registry_value_changed devops task, unrelated repo",
  ]
resolved_by:
locked_by:
---

# infra_satellite_ao_dispatch_batch10_2026_08_09 todo cited a non-existent commit SHA

## What I found

`plans/archive/2026_08/infra_satellite_ao_dispatch_batch10_2026_08_09.md` lines 146 and 231 both cite
`unified-trading-pm@b277df233` as the evidence commit for the "Find what writes `manifest-consolidate-*` scratch to the
orchestrator VM and stop it" todo, marked `- [x] ✅` and "DONE 2026-08-09". That SHA is not resolvable in this repo's
local clone by any means (`git cat-file -t b277df233` -> `fatal: Not a valid object name`; `git log --all --oneline` has
zero matches). The check's own ratchet baseline was raised 0 -> 1 in this same commit to unblock Pass-1 QG for an
unrelated devops task — see the baseline file's git history for the exact commit.

## Why it matters

Per CLAUDE.md's Governance HARD RULE ("Runtime verification — never 'done' without running the code; a `- [x]` ... claim
MUST cite Evidence: ... that resolves"), the actual work behind this todo is now unverifiable from the citation alone.
Either the real commit landed under a different (mistyped/truncated) SHA and just needs correcting, or the work was
never actually shipped and the checkbox is a false-progress flip — the same failure class as the archived
`mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md` precedent.

## Recommended decision

Whoever owns `infra_satellite_ao_dispatch_batch10_2026_08_09.md` (or the fix-worker this todo dispatches to) should:

1. Search unified-trading-pm's reflog/GitHub for a near-matching SHA (typo/truncation) and correct the citation if
   found.
2. If no matching commit exists anywhere, re-verify the underlying claim (does the manifest-consolidate-* scratch fix
   actually exist on `origin/live-defi-rollout`?) and either re-cite the real commit or reopen the todo.

## Todos

- [ ] [INFRA] P2. Investigate `unified-trading-pm@b277df233` cited at
      `plans/archive/2026_08/infra_satellite_ao_dispatch_batch10_2026_08_09.md:146,231` — find the real commit
      (typo-correct) or reopen the todo if the underlying work was never actually shipped.

## Progress Log

- **2026-08-09** — Discovered while shipping an unrelated devops task; the repo-wide `check_plan_commit_sha_evidence.py`
  ratchet blocked Pass-1 QG. Verified pre-existing (introduced by slot-33's `3e3d7145a2`, landed on origin before this
  session's work started) and non-fabricated-by-me. Re-baselined `fabricated_sha_citation_baseline` 0 -> 1 per the
  check's own printed guidance ("re-baseline with --baseline-write after confirming it is pre-existing, non-fabricated
  drift") to unblock, and filed this issue doc so the actual citation gets investigated rather than silently absorbed
  into the baseline forever.
