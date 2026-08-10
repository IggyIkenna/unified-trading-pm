---
doc_type: issue
title:
  NA-corpus ratchet diff-scoped against origin/main deadlocks LDR→main promotion whenever main lags — positive-feedback
  wall, unconvergeable by serial fixing
summary: >-
  `unified-trading-pm`'s LDR→main promotion stalled 22h (last merged promote PR #2671 at 2026-08-09T09:19Z; main 1180
  commits behind LDR) on a single hard gate: `check_na_corpus_ratchet` run as `--diff-base origin/main` from
  `run_hygiene_sweep.sh`'s shared `DIFF_BASE_REF`. The 2026-08-09 diff-scoping fix (b12d43618) assumed `origin/main` is
  a proxy for "the change under test's own base". That holds only while promotion is FLOWING. Once promotion stalls,
  `origin/main` lags arbitrarily and the diff spans the entire unpromoted backlog instead of the change — and diff-base
  mode has ZERO tolerance (any single new NA doc fails). This is a positive-feedback deadlock: the gate blocks the
  promote → main falls further behind → the measured diff grows → the gate fails harder. Measured directly: the same
  check reported 51 docs/116 todos at the 05:41Z CI run and 53 docs/151 todos ~2h later, while against the integration
  branch (`origin/live-defi-rollout`) it reported ~0. Seventeen AO `sit_failure` dispatches re-polled this wall without
  closing it; nobody touched `run_hygiene_sweep.sh` in the 17h the wall stood, because the failure reads as ordinary
  corpus growth rather than a base-selection bug.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, quality-gates-v2, ratchet, plan-hygiene, promotion, deadlock, live-incident]
related:
  - /plans/active/issues/plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md
  - /plans/active/issues/ci_escalation_no_coverage_for_local_ratchet_gate_breaches_2026_08_10.md
  - /plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md
created: 2026-08-10
author: /ci-reconcile (interactive, slot-2·laptop)
parent_epic: infrastructure_master
priority: P1
source: >-
  /ci-reconcile sweep of #ci-failures since 2026-08-10T00:00Z — 4 python-quality-gates-v2 CRITICAL alerts on
  unified-trading-pm (PRs #2706/#2707/#2708/#2709 + 3 LDR pushes) plus 3 branch-health PROMOTION LAG warnings, all one
  root cause.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-infra
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
last_updated: 2026-08-10
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/scripts/plan-hygiene/check_na_corpus_ratchet.py,
    unified-trading-pm/scripts/plan-hygiene/na_corpus_baseline.yaml,
  ]
---

# NA-corpus ratchet diff-scoped against a lagging `origin/main` deadlocks promotion

## Evidence

- Last merged promote PR: **#2671, 2026-08-09T09:19:48Z**. `gh api compare/main...live-defi-rollout` →
  `ahead_by: 1180, behind_by: 0`.
- Promote PRs **#2706, #2707, #2708, #2709** each opened and were **closed unmerged** (~2.5h cycle), every one red on
  `QG slice (checks)`.
- The failing run's own verdict (`gh run view 31358877638 --log-failed`) named exactly one hard failure:
  `❌ check_na_corpus_ratchet (--diff-base origin/main): 51 new NA-population doc(s); 116 new open todo(s)` →
  `❌ FAIL [hard] assigned_vm:NA corpus size` → `❌ Sweep FAILED`. Independently confirmed by the AO worker in
  `8409d134a4` ("confirms na-corpus is sole live blocker, other 2 checks stale-snapshot") — `VERSION_SPLIT` and
  `VESTIGIAL_SCALAR_DRIFT` in the same log are non-blocking.
- **The growth is the deadlock, measured**: 51 docs/116 todos (05:41Z CI) → **53 docs/151 todos** (07:40Z local, same
  check, same base). Against `origin/live-defi-rollout` instead: **~0**. The number the gate reports is a function of
  how far main has fallen behind, not of any change under test.

## Root cause

`run_hygiene_sweep.sh` sets one shared `DIFF_BASE_REF="origin/main"` in CI mode and hands it to every diff-scoped
ratchet. `origin/main` is only a valid stand-in for "this change's base" while promotion is flowing. It is not a
branch-relative base — it is an arbitrary point that recedes exactly when the gate starts blocking, which is what turns
a normal ratchet into a self-reinforcing wall.

## What shipped (2026-08-10)

1. **`4c964f8447` (slot-23) — promotion PRs skip `--diff-base` for the NA-corpus check.** Independently reached the same
   diagnosis as this doc ("un-convergeable on the promote path") and fixed it more surgically than this doc's first
   draft proposed: rather than dropping the check to baseline mode in ALL CI contexts (which would have discarded the
   2026-08-09 concurrent-agent race fix everywhere it still works), it detects a promote PR via
   `GITHUB_HEAD_REF =~ ^promote/` and falls back to baseline+buffer ONLY there. **That is the correct shape and it
   supersedes this doc's original proposal** — recorded here so the superseded approach is not re-attempted.
2. **Baseline re-measured to 389 docs / 1150 todos** via the sanctioned `--update-baseline` (never a hand-edit).
   Archival could not absorb the growth: `check_archive_candidates.sh` returned exactly one candidate, and that one was
   uncommitted foreign WIP in a shared slot checkout, not corpus content.
3. **The promote gate moved to the shared `DIFF_BASE_REF` so it covers ALL FOUR diff-scoped checks**, not just
   NA-corpus. `4c964f8447` scoped its fix to one consumer, but `check_reference_paths`, `check_archive_candidates` and
   `check_effort_signal_ratchet` read the same `DIFF_BASE_REF` and carry the identical latent bug — and reference-paths
   was already tripping it in production (`check_reference_paths (--diff-base origin/main): 2 NEW violation(s)`
   hard-failed the 11:25Z promote-path run, alongside a prosewrap-padding ratchet). Setting the rule once at the source
   also avoids four copies of one predicate, the shape that rotted the tranche lists (see
   `scripts/scheduled_job_already_ran.py`'s header). Verified: `GITHUB_HEAD_REF=promote/…` ⇒ `DIFF_BASE_REF=''` (all
   four checks baseline mode); a normal PR and a push to LDR both still get full diff-scoping. Post-fix measurement:
   corpus 394 docs / 1151 todos vs the promote-path ceiling 399 / 1180 — passes, but with only 5 docs and 29 todos of
   headroom, which is what the ADMIN todo below is about.

## Todos

- [x] ✅ [BACKEND] P1. Extend the same lag-guard reasoning to the **other** `DIFF_BASE_REF` consumers
      (`check_reference_paths.py`, `check_archive_candidates.sh`, `check_effort_signal_ratchet.py`) — DONE 2026-08-10 by
      moving `4c964f8447`'s promote gate from the NA-corpus wiring up to the shared `DIFF_BASE_REF` assignment, so one
      predicate covers all four consumers. Verified by simulation: `GITHUB_HEAD_REF=promote/…` ⇒ `DIFF_BASE_REF=''`; a
      normal PR and a push to LDR keep full diff-scoping.
- [x] ✅ [BACKEND] P2. The promote gate keys on `GITHUB_HEAD_REF =~ ^promote/`, a NAMING contract with the promote bots
      rather than a structural one — a half-rename would silently revert all four gates with no test failing. DONE
      2026-08-10: `scripts/quality_gates/check_promote_prefix_contract.py` asserts all THREE sites agree (both producers
      — `.github/workflows/ldr-to-main-promote.yml` and `scripts/cicd/ldr_to_main_fleet_promote.sh` — plus the sweep's
      consumer regex), AND that the gate sits on the SHARED `DIFF_BASE_REF` rather than one consumer. Wired into
      `quality-gates.sh`. Verified both directions: renaming the consumer regex OR either producer makes the check exit
      1 naming the exact file; the unmodified tree passes.
- [ ] [BACKEND] P3. The deeper shape is still unaddressed: `origin/main` is a proxy for "this change's base" that is
      only valid while promotion FLOWS. The promote gate handles the one case where that proxy is known-bad, but a
      normal PR opened against a long-stalled main has the same problem in miniature. Preferred end state: resolve the
      diff base to the branch's own last-gated point (`github.event.before` for a push; the integration branch for a PR)
      rather than a fixed `origin/main`. Note the CI checkout is `fetch-depth: 2`
      (`unified-trading-ci/.github/workflows/python-quality-gates-v2.yml`), so any chosen base must either already
      resolve there or be explicitly fetched — a base that silently fails to resolve is fail-UNSAFE (every current
      violation reads as "new"). Repo: unified-trading-pm (`scripts/plan-hygiene/`).
- [ ] [BACKEND] P2. **Promote PRs re-gate already-gated content.** A `chore(promote)` PR is a bot-generated projection
      of LDR content that each already passed the LDR entry gate commit-by-commit; re-running corpus-growth ratchets
      over the aggregate is double jeopardy and is what converts ordinary corpus growth into a promotion blocker. Decide
      (operator call, not a unilateral backend change — it narrows a hard gate) whether corpus-growth ratchets should be
      ENTRY gates only (LDR push / precommit) rather than promotion gates. Repo: unified-trading-pm.
- [ ] [BACKEND] P2. **No detection surface for this failure class.** The wall stood 22h with 17 `sit_failure`
      dispatches, none of which escalated "this gate cannot converge" as distinct from "this gate is red". Add a
      detector for a _non-convergeable_ gate — e.g. the same check failing across N consecutive distinct HEADs with a
      MONOTONICALLY GROWING violation count is definitionally not a fixable regression. Cross-reference
      `/plans/active/issues/ci_escalation_no_coverage_for_local_ratchet_gate_breaches_2026_08_10.md` (adjacent gap:
      local pre-push ratchet breaches) — this one is the opposite side, a remote gate that IS observed but is
      mis-classified as retryable. Repo: agent-orchestrator (`server/escalation.py`, `server/ci_reconcile.py`).
- [ ] [ADMIN] P2. **The NA corpus genuinely outgrew its ceiling** (391 docs vs 372+10; todos 1119 vs 1109+30 passing),
      and this is the third re-baseline in ~2 days. The fleet's own mandated processes (findings-triage "every follow-up
      is a `- [ ]` todo", `/plan-reconcile`, `/ci-reconcile`) create NA docs faster than `/na-eligibility-audit` retires
      them. Decide whether the answer is a higher steady-state ceiling, a faster retirement cadence, or narrowing what
      must become a tracked NA doc — re-baselining on each breach is not a steady state. Owner: operator.

## Progress Log

- **2026-08-10 (/ci-reconcile, slot-2·laptop)** — Root-caused and remediated per the two items under "What shipped".
  Fleet sweep at the same time: 25/26 repos green on `quality-gates-v2`@LDR (`unified-trading-ci` has no such workflow —
  it hosts the reusable one); all 23 GH-Actions standing monitors green except `ldr-docs-gate`; both host-dispatched
  systemd watchdogs verified active and OK via live SSM.
- **2026-08-10 (cicd escalation `agt-cced28`, slot-15)** — Recurrence of the same deadlock on the LDR-branch path:
  `quality-gates-v2` RED on `live-defi-rollout` (workflow_dispatch re-runs) with
  `check_na_corpus_ratchet (--diff-base origin/main)` reporting 57→59 new docs / 185→193 new todos while main slipped to
  1501 commits behind LDR. Root cause: the shared `DIFF_BASE_REF` guard only excluded `promote/*` PRs; a DIRECT
  LDR-branch run has empty `GITHUB_HEAD_REF`, so it still diff-scoped against the lagging `origin/main` and measured the
  whole unpromoted backlog. Fixed by extending the same lag-guard to `GITHUB_REF == refs/heads/live-defi-rollout` (falls
  back to baseline+buffer; current NA corpus 394 docs / 1148 todos, inside the reviewed 409/1350 ceiling). Verified:
  guard unit cases (LDR-wfd→baseline, promote→baseline, feature-PR→diff-scope, push-main→diff-scope) + sweep
  `--ci --no-regen` under LDR env sim EXIT 0 (Hard failures 0). Shipped via quickmerge:
  `scripts/plan-hygiene/run_hygiene_sweep.sh`.
