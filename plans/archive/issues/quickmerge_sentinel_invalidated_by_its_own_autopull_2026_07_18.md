---
doc_type: issue
title:
  quickmerge's STAGE 0.4 auto-pull invalidates the tree-strict sentinel the gate wrote seconds earlier, so shipping
  livelocks whenever peers push faster than a gate run
summary:
  Measured 2026-07-18 across four consecutive shipping attempts in unified-trading-pm. The agent ship path is gate →
  quickmerge, and the gate writes `.qg_last_passed_sha` == HEAD. quickmerge's STAGE 0.4 (Not-Behind Gate) then pulls
  before the STAGE 3 sentinel check, so any peer commit landing between the two moves HEAD and the sentinel now points
  at a superseded tree — quickmerge correctly refuses. On a busy evening PM's live-defi-rollout took a push roughly
  every 2 minutes while a full `quality-gates.sh --no-fix` run takes ~3, so the sequence cannot converge - I lost the
  race three times before recognising the pattern and shipping through the sanctioned PM `scripts/**` carve-out instead.
  This is NOT a logic bug and the sentinel must NOT be weakened - after pulling peer commits the tree really is
  different and typecheck/tests really are whole-program, which is exactly why the sentinel was made tree-strict
  (19606d5ed, same day). It is a THROUGHPUT problem - the ship path has no way to converge under a push rate faster than
  its own gate, and the current failure mode dumps that on the agent as a bare "re-run quality-gates.sh" that will fail
  again for the same reason.
status: resolved
resolved_by: unified-trading-pm@e264b3c9
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cicd, quickmerge, quality-gates, sentinel, multi-agent, shipping, throughput, livelock]
related: [/plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md]
created: 2026-07-18
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: devops
drift_direction: none
locked_by:
source: measured during the 2026-07-18 CI-failure sweep while shipping 7e364ab9e
depends_on: []
---

# quickmerge sentinel vs its own auto-pull

## What was measured

Four consecutive ship attempts in `unified-trading-pm` on 2026-07-18, ~20:40–21:00 UTC:

| attempt | gate | outcome                                                                       |
| ------- | ---- | ----------------------------------------------------------------------------- |
| 1       | pass | quickmerge refused — sentinel invalid, tree moved (peer pushed `4436e59f0`)   |
| 2       | pass | quickmerge refused — sentinel invalid (peer pushed `a7b4cccbf`)               |
| 3       | pass | pre-commit `check-branch-drift` refused — 1 commit behind                     |
| 4       | pass | shipped via the PM `scripts/**` carve-out (direct commit + push), `7e364ab9e` |

## Mechanism

1. `quality-gates.sh` runs green and writes `.qg_last_passed_sha` = HEAD (call it `A`).
2. `quickmerge.sh` **STAGE 0.4 — Not-Behind Gate** (`scripts/quickmerge.sh:513-590`) pulls `--rebase --autostash`. If a
   peer pushed, HEAD becomes `B`.
3. **STAGE 3 — Local Quality Gates** compares the sentinel (`A`) to HEAD (`B`), finds a mismatch, and refuses with
   `Run: bash scripts/quality-gates.sh`.

The pull happens **before** the sentinel check, so the check is evaluated against a tree the gate never saw. Re-running
the gate restarts the same race.

## Why the obvious "fix" is wrong

Do **not** relax the sentinel to a per-file or ancestor check. It was deliberately made tree-strict the same day
(`19606d5ed`) because typecheck and tests are **whole-program** — a peer's edit can break a file you never touched, so a
green gate on tree `A` genuinely says nothing about tree `B`. Refusing is correct. The defect is that the ship path has
no convergence strategy, not that the check is too strict.

## Options (not yet chosen)

1. **Re-gate inside quickmerge after STAGE 0.4.** Closes the loop automatically. Cost: doubles quickmerge wall-clock in
   the common case, and it must re-check the sentinel it just produced. Touches the fleet's most critical shared script.
2. **Bounded retry loop in the ship path** — pull → gate → immediately attempt commit, retry N times, surfacing a
   distinct exit code when the window never opens. Cheapest; makes the existing manual workaround first-class.
3. **Short-circuit for carve-out-only changesets.** A commit touching only `.github/**`, `scripts/**`, `plans/**`,
   `codex/**` (already `CARVE_PREFIX` in `check_strict_quickmerge.py`) cannot be broken by a peer's Python edit, so it
   could ship against a sentinel that predates a docs-only pull. Narrow and safe, but only helps carve-out changes.
4. **Do nothing; document the carve-out as the sanctioned escape.** Zero risk, but every agent re-discovers the
   livelock.

## Recommendation

Option 2, plus option 3 for carve-out-only changesets. Option 1 is the most "correct" but re-architects the shared ship
path, and this was measured on one unusually busy evening — the rate at which this actually bites should be established
before paying that cost.

## Provenance

Found while shipping `7e364ab9e` (major-bump template reconciliation). The tree-strict sentinel it collides with is
`19606d5ed`, shipped by the same session earlier the same day — so this is a self-inflicted interaction, reported here
rather than hot-patched into `quickmerge.sh` at the end of a long session.

## Decision (2026-07-19) — adopt Option 2 + Option 3; sentinel stays tree-strict

Adopt **Option 2 (bounded retry loop in the ship path)** as the primary fix, plus **Option 3 (short-circuit for
carve-out-only changesets)**. The tree-strict sentinel is **kept unchanged** — after a peer pull the tree genuinely
differs and typecheck/tests are whole-program, so refusing is correct (do NOT weaken to per-file/ancestor). The defect
is throughput/convergence, not strictness. Option 1 (re-gate inside quickmerge) is deferred — it re-architects the
fleet's most critical shared script for a rate that was measured on one busy evening; establish the real bite-rate
first.

**Corroborating evidence (2026-07-19).** Re-encountered this exact class shipping the mtds STEP-5.97 citation fix on a
shared, non-isolated working tree with ≥3 concurrent autostashing agents: (a) a peer's `git pull --rebase --autostash`
**clobbered my uncommitted edits mid-gate** (work loss, not just a stale sentinel — worse than the PM case, because the
tree is shared); (b) the pre-commit `check-branch-drift` hook then rejected the commit for being 1 behind; (c) the
sentinel-vs-HEAD race recurred at quickmerge time. Operational workaround that held: **commit the changeset first**
(committed work survives a peer autostash) → gate over the committed tree → quickmerge's committed-ahead path pushes it,
re-gating on drift. This is essentially Option 2 done by hand and argues for making it first-class; it also surfaces a
shared-tree corollary Option 2 should cover — **protect uncommitted work by committing before the long gate**, not only
retry the sentinel.

**Implementation status: DECIDED, not yet implemented** — recorded for operator greenlight rather than hot-patched into
`quickmerge.sh` (fleet-critical) at session end, consistent with the original report's stance.

## Implemented (2026-07-22) — Option 2

`unified-trading-pm@e264b3c9` (hit this exact race live while shipping an unrelated AO plan-checkbox flip on a hot PM
`live-defi-rollout` tonight — direct reproduction, not synthetic). STAGE 0.4's pull logic extracted into
`_qm_stage_0_4_not_behind_gate()`; STAGE 3's AGENT_MODE sentinel check split into `_qm_check_agent_sentinel()` (0/1,
never exits) driven by a bounded `until` retry loop — on a lost race, re-pull + `quality-gates.sh --no-fix` + re-check,
up to 3 attempts with backoff+jitter, before falling back to today's hard-fail message. Sentinel/ancestry stays exactly
tree-strict per this decision — nothing here weakens it. Option 3 (carve-out short-circuit) was NOT implemented —
deferred, since `scripts/**` isn't uniformly safe to fast-path across every repo (PM's own `scripts/` is docs-adjacent,
but other repos' `scripts/` can hold real tested Python) and needs a per-repo-aware design, not a blanket prefix list
reused from `check_strict_quickmerge.py`'s `CARVE_PREFIX`. Verification: `bash -n`, the existing
`test-quickmerge-blocked-contract.sh` (5/5, confirms the STAGE 0.4 extraction test still slices the right block),
`test_check_strict_quickmerge.py` (13/13), an isolated control-flow harness for the retry loop's 3 cases, full PM
`quality-gates.sh` green, and a live re-ship afterward on the same busy branch.
