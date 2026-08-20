---
doc_type: issue
title: "Second recurrence: plan-flip cited fabricated/non-existent market-tick-data-service SHAs (5ea59b90, 926f9b20)"
summary: >-
  check_plan_commit_sha_evidence.py (ratchet baseline 0) flagged 2 unresolvable `<repo>@<sha>` citations found while
  this session was fast-forward-pulling origin/live-defi-rollout for an unrelated task: (1)
  plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md:302 cites `market-tick-data-service@5ea59b90`
  (landed in commit 0d22090ed, "flip F6-reframed TradFi options_chain item"), (2)
  plans/active/issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md:199
  cites `market-tick-data-service@926f9b20` (landed in commit fb6681294, "flip zombie-tick purge todo"). Neither SHA
  resolves in the local market-tick-data-service clone (`git cat-file -e` → exit 128, "Not a valid object name") — same
  failure shape as the archived `/plans/archive/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md`
  incident (short/truncated or invented SHA cited as completion evidence). Not caused by, or related to, this session's
  own task (an unrelated AO-dispatch-visibility-gate triage) — discovered only because these two commits landed on
  origin between this session's boot and its own commit, and were pulled in via the mandatory fresh-pull step.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer, admin]
tags: [findings-triage, false-progress, evidence-integrity, plan-hygiene, agent-trust]
related:
  [
    /plans/archive/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md,
    /plans/active/issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md,
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
  ]
created: 2026-08-09
author: slot-3-infra
priority: P2
parent_epic: agent_operating_framework_master
source: "slot-3, infra, 2026-08-09 — surfaced by check_plan_commit_sha_evidence.py while shipping an unrelated flip"
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
  "slot-3, infra, 2026-08-09 — both citations resolved (1 independently by slot-8, 1 by another session), baseline back
  to 0"
locked_by:
context_scope:
  [
    scripts/quality_gates/check_plan_commit_sha_evidence.py,
    scripts/quality_gates/plan_commit_sha_evidence_baseline.yaml,
    /plans/archive/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md,
  ]
---

# Second recurrence — fabricated market-tick-data-service commit-SHA citations in plan flips

> **ARCHIVED (2026-08-09) — all 3 todos done, unlocked.** Both fabricated citations resolved independently by other
> concurrent sessions (one by slot-8's `plan_commit_sha_evidence_unresolvable_citations_block_qg_2026_08_09.md`, one by
> an unattributed session's `unified-trading-pm@bfb0f738e`); this doc's own contribution was surfacing the regression +
> a temporary re-baseline while the real fixes landed, then confirming and lowering the baseline back to 0.
> `check_plan_commit_sha_evidence.py` reports 0 unresolvable citations fleet-wide.

## What I found

`check_plan_commit_sha_evidence.py` regressed from baseline 0 to 2 unresolvable citations, both citing
`market-tick-data-service@<8-char-sha>` that does not exist in the local MTDS clone under any branch:

- `plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md:302` — `market-tick-data-service@5ea59b90`
  (checkbox claims a "CAS re-stamp" script shipped under this SHA; landed via unified-trading-pm@0d22090ed, slot unknown
  from this session's vantage point).
- `plans/active/issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md:199` —
  `market-tick-data-service@926f9b20` (landed via unified-trading-pm@fb6681294).

Both were on `origin/live-defi-rollout` before this session's fast-forward pull — i.e. already shipped by whichever slot
authored them. This session did not author either checkbox and has no further context on what the real SHA (if any)
should be.

## Why it matters

Identical failure shape to the archived 2026-07-30 incident: a plan-flip's `<repo>@<sha>` evidence citation doesn't
resolve to a real commit, which is exactly the false-completion-evidence pattern `check_plan_commit_sha_evidence.py`
exists to catch. A short/truncated SHA or a SHA from an unpushed local commit both produce this same symptom from the
checker's point of view.

## Recommended decision

- [x] ✅ [SCRIPT] P2. **DONE (independently, by a different session working the same root cause).** The
      `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md:302` citation was fixed by slot-8 (infra) via
      `market-tick-data-service@b9f41a49` (documented in
      `/plans/archive/issues/plan_commit_sha_evidence_unresolvable_citations_block_qg_2026_08_09.md`, filed and resolved
      independently the same session, discovered via a quickmerge post-gate block rather than this session's
      fresh-pull). Confirmed via `check_plan_commit_sha_evidence.py --workspace-root <ws>`: 0 unresolvable citations,
      down from 2662 checkable / 0 unresolvable. Repo: unified-trading-pm.
- [x] ✅ [SCRIPT] P2. **DONE (independently, before this session finished its own closing sweep).** The
      `sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md:199` citation was fixed
      by `unified-trading-pm@bfb0f738e` ("fix unresolvable commit-SHA citation blocking QG (unrelated pre-existing
      drift)") — the checkbox now cites the real `market-tick-data-service@c2dda59a7`, explicitly noting it corrects the
      unresolvable `926f9b20`. Confirmed via `check_plan_commit_sha_evidence.py`: only the
      `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md:302` citation remains unresolvable. Repo:
      unified-trading-pm.
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-09 (slot-3, infra).** Re-baseline `plan_commit_sha_evidence_baseline.yaml` — raised
      0 -> 2 (citing this issue doc) so the ratchet didn't block unrelated commits while these 2 items were
      investigated, then lowered back to 0 once both were confirmed independently resolved (see the two todos above).
      Final state: `fabricated_sha_citation_baseline: 0`, `source:` reverted to the original
      `mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md` doc since no citations remain. Repo:
      unified-trading-pm.

## Progress Log

- **2026-08-09 (slot 3, infra)** — Filed while shipping an unrelated closing sweep on
  `ao_dispatch_visibility_gate_accidental_exclusions_2026_08_08.md`; the fast-forward pull step pulled in the two
  culprit commits (`0d22090ed`, `fb6681294`) moments before this session's own commit, tripping the ratchet on content
  this session did not author. Re-baselined to unblock; the 2 resolution todos above are separate, unblocked follow-up
  work for whichever session picks this doc up next.
