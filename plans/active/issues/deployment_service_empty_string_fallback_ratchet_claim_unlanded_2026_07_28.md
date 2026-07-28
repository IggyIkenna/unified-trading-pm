---
doc_type: issue
title:
  deployment-service's claimed empty-string-fallback baseline ratchet (91→89) never actually landed in
  no_empty_string_fallback_baseline.yaml — repo is still at count 91
summary: >-
  mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md's 2026-07-28 Progress Log entry claims
  "Ratchet remaining 4 baselines DOWN — ALL 4 NOW DONE 2026-07-28" including "deployment-service 91→89", but a
  fleet-wide `--update-baseline` re-run + `git log -S deployment-service -- scripts/quality_gates/
  no_empty_string_fallback_baseline.yaml` show the repo's committed baseline has only ever been `count: 91`
  (the original 2026-07-08 seed value) — no commit ever wrote `89`. Not currently blocking (deployment-service is
  `[OK] == baseline` at the live count of 91), so this is a doc-accuracy / provenance gap, not a live gate failure.
  Most likely lost to the shared-clone concurrent-git-commit race documented in
  shared_clone_concurrent_commit_message_swap_2026_07_28.md (a commit landing with a swapped message, or a stash/pop
  race silently dropping a small YAML edit), rather than a fabricated claim.
status: open
nature: issue
asset_group: [meta, infrastructure]
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer]
tags: [quality-gates, empty-string-fallback, baseline, provenance, doc-accuracy]
related:
  [
    /plans/archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
    /plans/active/issues/shared_clone_concurrent_commit_message_swap_2026_07_28.md,
  ]
created: 2026-07-28
parent_epic: infrastructure_master
priority: P3
source:
  "Noticed while closing mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md's commit-anchor todo via
  a fleet-wide --update-baseline sweep — deployment-service reported at count 91, not the 89 the doc's own Progress
  Log claimed was already banked."
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: NA
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
supersedes:
superseded_by:
---

# deployment-service empty-string-fallback ratchet claim never landed

## What I found

`check_no_empty_string_fallback.py --workspace-root <ws>` (no `--scope`, full fleet) reports `deployment-service`
`[OK] == baseline` at the LIVE count of 91. `git show HEAD:scripts/quality_gates/no_empty_string_fallback_baseline.yaml`
confirms the committed baseline row is `count: 91` — and `git log -S deployment-service -- scripts/quality_gates/
no_empty_string_fallback_baseline.yaml` shows only the original 2026-07-08 seeding commit (`13f17c203`) ever touched
this file's deployment-service entry; no later commit set it to 89.

This contradicts `mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`'s own 2026-07-28 Progress Log
entry: "Ratchet remaining 4 baselines DOWN — ALL 4 NOW DONE 2026-07-28... deployment-service 91→89, instruments-service
366→361, ml-service 8→6, trading-agent-service 2→1" (the other 3 DID land — their rows carry `commit:` anchors +
the claimed counts; only deployment-service's claim is unsubstantiated).

## Why it matters

Low severity — deployment-service is not currently gate-blocked (91 == baseline 91). This is a provenance/trust gap:
a Progress Log entry claimed a ratchet-down that never actually shipped, discovered only because this session
happened to re-run the checker fleet-wide. If deployment-service's live count later drifts down to 89 genuinely, a
future `--update-baseline` run will correctly bank it — no data is at risk. The gap is purely "the doc said something
happened that didn't."

## Todos

- [ ] [SCRIPT] P3. **Re-verify deployment-service's actual current empty-string-fallback count** (re-run
      `check_no_empty_string_fallback.py --scope deployment-service`) and, if genuinely at or below 89 today, bank it
      via `--update-baseline --scope deployment-service`. If still at 91, this todo is DONE as-is (nothing to fix — the
      repo isn't blocked); just correct the record here.

## Progress Log

- 2026-07-28 (slot-4): Filed while closing out
  `mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`'s commit-anchor todo via a fleet-wide
  `--update-baseline` sweep. Not investigated further (out of scope for that dispatch — agent-orchestrator-focused);
  filing here per the "every follow-up is a todo, not prose" rule instead of burying it in that doc's Progress Log.
