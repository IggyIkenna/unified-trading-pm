---
doc_type: issue
title:
  deployment-service's claimed empty-string-fallback baseline ratchet (91→89) never actually landed in
  no_empty_string_fallback_baseline.yaml — repo is still at count 91
summary: >-
  mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md's 2026-07-28 Progress Log entry claims "Ratchet
  remaining 4 baselines DOWN — ALL 4 NOW DONE 2026-07-28" including "deployment-service 91→89", but a fleet-wide
  `--update-baseline` re-run + `git log -S deployment-service -- scripts/quality_gates/
  no_empty_string_fallback_baseline.yaml` show the repo's committed baseline has only ever been `count: 91` (the
  original 2026-07-08 seed value) — no commit ever wrote `89`. Not currently blocking (deployment-service is `[OK] ==
  baseline` at the live count of 91), so this is a doc-accuracy / provenance gap, not a live gate failure. Most likely
  lost to the shared-clone concurrent-git-commit race documented in
  /plans/archive/issues/shared_clone_concurrent_commit_message_swap_2026_07_28.md (a commit landing with a swapped
  message, or a stash/pop race silently dropping a small YAML edit), rather than a fabricated claim.
status: resolved
nature: issue
asset_group: [meta, infrastructure]
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer]
tags: [quality-gates, empty-string-fallback, baseline, provenance, doc-accuracy]
related:
  [
    /plans/archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
    /plans/archive/issues/shared_clone_concurrent_commit_message_swap_2026_07_28.md,
  ]
created: 2026-07-28
parent_epic: infrastructure_master
priority: P3
source:
  "Noticed while closing mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md's commit-anchor todo via a
  fleet-wide --update-baseline sweep — deployment-service reported at count 91, not the 89 the doc's own Progress Log
  claimed was already banked."
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: NA
drift_direction: advance-code
depends_on: []
resolved_by:
  "2026-07-30 re-verification — deployment-service genuinely still at count 91 (== baseline); the 2026-07-28 '91→89'
  Progress Log claim is confirmed unsubstantiated, nothing to fix, record corrected"
locked_by:
supersedes:
superseded_by:
---

# deployment-service empty-string-fallback ratchet claim never landed

> **🟢 ARCHIVED 2026-07-30** (`/plan-reconcile` autonomous sweep) — status=resolved, the single P3 todo is done.
> Re-verified 2026-07-30: `check_no_empty_string_fallback.py --scope deployment-service` reports
> `[OK] deployment-service: 91 (== baseline)`, so the repo is not gate-blocked and the live count never dropped to 89.
> The finding stands as a record-correction (the 2026-07-28 Progress Log claim was wrong); there is no code or baseline
> change to make.

## What I found

`check_no_empty_string_fallback.py --workspace-root <ws>` (no `--scope`, full fleet) reports `deployment-service`
`[OK] == baseline` at the LIVE count of 91. `git show HEAD:scripts/quality_gates/no_empty_string_fallback_baseline.yaml`
confirms the committed baseline row is `count: 91` — and
`git log -S deployment-service -- scripts/quality_gates/ no_empty_string_fallback_baseline.yaml` shows only the original
2026-07-08 seeding commit (`13f17c203`) ever touched this file's deployment-service entry; no later commit set it to 89.

This contradicts `mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`'s own 2026-07-28 Progress Log
entry: "Ratchet remaining 4 baselines DOWN — ALL 4 NOW DONE 2026-07-28... deployment-service 91→89, instruments-service
366→361, ml-service 8→6, trading-agent-service 2→1" (the other 3 DID land — their rows carry `commit:` anchors + the
claimed counts; only deployment-service's claim is unsubstantiated).

## Why it matters

Low severity — deployment-service is not currently gate-blocked (91 == baseline 91). This is a provenance/trust gap: a
Progress Log entry claimed a ratchet-down that never actually shipped, discovered only because this session happened to
re-run the checker fleet-wide. If deployment-service's live count later drifts down to 89 genuinely, a future
`--update-baseline` run will correctly bank it — no data is at risk. The gap is purely "the doc said something happened
that didn't."

## Todos

- [x] [SCRIPT] P3. **DONE 2026-07-30 — re-verified, still at 91.**
      `check_no_empty_string_fallback.py --scope     deployment-service` reports
      `[OK] deployment-service: 91 (== baseline)` today — genuinely still 91, not 89. Per this todo's own instruction,
      that means DONE-as-is: nothing to fix (the repo isn't gate-blocked), record corrected — the 2026-07-28 Progress
      Log's "91→89" claim remains unsubstantiated/incorrect, the live count never dropped.

## Progress Log

- 2026-07-28 (slot-4): Filed while closing out `mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`'s
  commit-anchor todo via a fleet-wide `--update-baseline` sweep. Not investigated further (out of scope for that
  dispatch — agent-orchestrator-focused); filing here per the "every follow-up is a todo, not prose" rule instead of
  burying it in that doc's Progress Log.
