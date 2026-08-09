---
doc_type: issue
title:
  ao-dispatch-visibility gate regressed 26→34 accidental exclusions fleet-wide — blocks every quickmerge, not caused by
  any single owned edit
summary: >-
  `check_ao_dispatch_visibility_gate.py`'s corpus-wide ratchet (disk-vs-backlog todo delta) jumped from its baseline of
  26 accidental (undeclared) exclusions to 34 sometime between 2026-08-09T00:48Z (last confirmed green, my own
  successful quickmerge push at that time) and 2026-08-09T01:1x-ish (first observed red, this doc's filing). The gate is
  corpus-wide and unconditional (runs on every quickmerge regardless of --files scope), so it currently blocks ANY
  slot's ability to ship anything via quickmerge. Confirmed via `git stash` that my own 3 staged files (an unrelated
  archival) contribute ZERO new exclusions — the 8 newly-crossed docs span cefi/ci/defi/infra/sports/prediction/issues
  tranches I don't own, each with its own `[TAG] P<n>.` todo line the parser reads as "excluded" (a BLOCKED-*/DEFERRED-
  BY-DESIGN/stretch-shaped sentence not carrying the actual declared marker token at the start of its own line).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao-dispatch-visibility, ratchet-regression, ci-cd, blocking, quickmerge]
related: [/plans/active/issues/ao_dispatch_visibility_gate_regression_sports_blocked_upstream_marker_2026_08_08.md]
created: 2026-08-09
parent_epic: infrastructure_master
source: cicd-worker-slot30, discovered while shipping unrelated promote_ref_orphaned_on_manual_pr_close archival
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: cicd
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    /scripts/quality_gates/check_ao_dispatch_visibility_gate.py,
    /scripts/quality_gates/ao_dispatch_visibility_baseline.yaml,
  ]
---

# ao-dispatch-visibility gate regression blocks fleet-wide shipping

## Evidence

- Baseline (`ao_dispatch_visibility_baseline.yaml`): 26 accidental exclusions tolerated.
- Live measured (2026-08-09, `python3 scripts/quality_gates/check_ao_dispatch_visibility_gate.py --json`):
  `{"docs": 241, "accidental_exclusions": 34, "declared_exclusions": 12, "zero_dispatchable_docs": 26}` — 34 > 26.
- **Not caused by my own change**: `git stash push -u -- <my 3 files>` then re-running the gate on the resulting
  clean-HEAD tree reproduced the SAME failure — confirming this is pre-existing on `origin/live-defi-rollout` HEAD
  (fetched, 0 behind at time of check), not introduced by anything I staged.
- **Recently regressed, not long-standing**: my own quickmerge push ~15-20 min earlier (commit `9013b7b5a`, the
  codex-doc-freshness fix) ran this exact gate and it printed
  `✅ AO dispatch-visibility gate passed (at-or-below baseline)` — so the corpus crossed from ≤26 to 34 in that short
  window, almost certainly from other slots' concurrent plan-doc commits landing on the shared `live-defi-rollout`
  branch.
- **34 newly/currently-accidental docs span every tranche** (spot-checked via `--json` output): cefi (2), ci (3),
  cross-cutting (2), defi (2), infra (3), prediction (1), sports (6), plus several `issues/` docs (canonical-path,
  capability-wizard, credential-checker, deployment-scripts, deribit, e2e-defi, sports×4, vm-billing) — genuinely
  fleet-wide, not one tranche's fault, not one owner's fix.

## Impact

**Blocking, not cosmetic.** Unlike most of this session's other ratchets, this one is NOT scoped to staged files — it
re-measures the full 241-doc corpus on every quickmerge run regardless of `--files`. Until it's back at/below 26 (or a
reviewed `--update-baseline` lands), no slot can ship ANYTHING through the sanctioned quickmerge path.

## Recommended next step

- [ ] [DEVOPS] P1. Investigate whether this is (a) real drift needing 8 individual doc fixes (declare the marker at the
      start of its own line, or rewrite the todo) — tedious but mechanical, one per flagged doc, see the `--json` list
      in this doc's evidence section for the current 34; or (b) a parser/marker-vocabulary regression similar to the
      sibling doc `ao_dispatch_visibility_gate_regression_sports_blocked_upstream_marker_2026_08_08.md` (a no-space
      `][BLOCKED-` combo the parser doesn't recognize) that's newly affecting MORE docs than that fix covered — re-run
      `check_ao_dispatch_visibility_gate.py --json` and diff the flagged-doc list against this doc's snapshot to see if
      it's still growing (parser bug, fix the regex) or now stable (real backlog of individual doc fixes). Done-when:
      `check_ao_dispatch_visibility_gate.py` exits 0 (accidental_exclusions <= 26) on a fresh `origin/live-defi-rollout`
      pull, OR a reviewed `--update-baseline` lands with each of the 8+ newly-crossed docs' justification named in the
      commit message (never a blind re-baseline).

## Progress Log

- **cicd-worker slot 30, 2026-08-09**: filed while blocked shipping an unrelated archival (promote-ref-orphan issue
  resolution). Did not attempt to fix the 8+ individual docs myself — out of scope (spans tranches I don't own, not
  small/quick per the fix-vs-file-and-wait triage). Retrying my own blocked quickmerge periodically; will update this
  doc if/when it self-resolves (another slot's commit) or note if it needs to be escalated further.
