---
doc_type: issue
title:
  plan-hygiene hard-0-baseline ratchet checks regress faster than one CI worker can chase serially on live-defi-rollout
summary: >-
  A worker chasing a `quality-gates-v2` failure on `unified-trading-pm` `live-defi-rollout` hit 4 CONSECUTIVE
  regressions in a row across different ratchet checks (codex-doc-freshness — already fixed upstream this session;
  effort-ratchet; archive-candidates x2; dangling-reference-paths, 95 > baseline 86) despite pushing 3 separate fixes.
  Each re-trigger landed on a fresh HEAD carrying a NEW regression introduced by other agents committing concurrently in
  the gap between the fix push and the CI re-run — the branch's commit velocity currently outpaces what one CI worker
  fixing issues one at a time can converge on. Worker correctly declined to keep chasing a 5th time (own recommendation:
  hand off) rather than burning further CI cycles on a race it cannot win serially; main answered "hand off" and is
  filing this as the systemic finding rather than asking for more chase attempts.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci, quality-gates-v2, ratchet, plan-hygiene, concurrency, live-incident]
related:
  - /plans/active/issues/quality_gates_v2_concurrency_and_bookkeeping_job_cost_2026_08_02.md
created: 2026-08-09
author: agt-22de53 (main), relaying a finding from agt-558c62 (slot 3)
parent_epic: infrastructure_master
priority: P2
source: >-
  Worker (agt-558c62, slot 3) blocked-nudge BLK-bcb0be57, 2026-08-09T02:24:36Z — 4 consecutive quality-gates-v2
  regressions on live-defi-rollout across different plan-hygiene ratchet checks, each re-trigger racing fresh concurrent
  commits from other fleet agents.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-09
locked_since:
context_scope: [unified-trading-pm/scripts/plan-hygiene/, unified-trading-pm/.github/workflows/quality-gates-v2.yml]
---

# plan-hygiene ratchet checks regress faster than serial CI-fix chasing can converge on a high-churn branch

## What was found

`agt-558c62` (slot 3) was chasing a `quality-gates-v2` failure on `unified-trading-pm` `live-defi-rollout` and hit 4
consecutive distinct regressions in a row, each on a fresh `HEAD`:

1. `codex-doc-freshness` — already independently root-caused and re-baselined this session
   (`plans/active/issues/codex_doc_freshness_regression_ambient_staleness_drift_2026_08_09.md`), an ambient time-decay
   ratchet, not this worker's fault.
2. `effort-ratchet`
3. `archive-candidates` (x2 — regressed twice)
4. `dangling-reference-paths` — 95 violations > baseline 86, current at time of report

Each time the worker pushed a fix and re-triggered, a DIFFERENT concurrent agent's commit had already landed a new
violation in the gap, so the re-run failed on a NEW check rather than confirming the original fix. Worker correctly
recognized this as a race it cannot win by chasing serially and declined a 5th attempt, recommending hand-off (own
words: "this branch is churning faster than one CI worker can chase serially").

## Why it matters

- Real CI-cycle waste: 4+ full `quality-gates-v2` runs consumed chasing a moving target, none of which converged.
- The hard-0-baseline ratchet design (shrink-only, any regression blocks) assumes a LOW commit-concurrency environment
  where one fix-and-verify cycle can outrun new violations landing. At current fleet-wide commit velocity on
  `live-defi-rollout`, that assumption may no longer hold for at least some of these checks.
- Distinct from `quality_gates_v2_concurrency_and_bookkeeping_job_cost_2026_08_02.md` (that doc is about
  concurrency-group cancellation and per-job billing floor cost) — this is about ratchet CORRECTNESS-vs-commit-race, a
  different failure mode.

## Todos

- [ ] [BACKEND] P3. **New facet found 2026-08-09 (context_scout_auditor, dispatch agt-264560, slot 16): the same
      zero-baseline-grace `--only` design also hard-blocks LOCAL pre-commit, not just CI.** A routine, fully-unrelated
      context_scope-maintenance sweep (touching ~270 docs, no todo/status/effort-tier content changed) hit
      `check_plan_operator_ruling_evidence.py --only` and `check_effort_signal_ratchet.py --only` failing on ANY staged
      file that already carried pre-existing corpus debt, with no baseline exemption in `--only` mode (by design — see
      each script's own `--only` docstring). Measured: 39 files failed operator-ruling-evidence (an established,
      pre-2026-07-30 gap), 117 files failed effort-signal-ratchet (same 217->250 population this doc's slot-14 entry
      already found) — 156 of ~425 touched docs (37%), all pre-existing content, none touched by this session. Had to
      exclude all 156 from the commit and defer (git-restore back to HEAD) since fixing them requires per-doc judgment
      outside a context-scout worker's mandate. This confirms Todo option (c) below from the opposite direction: it's
      not just that CI re-triggers race fresh regressions, it's that ANY agent's local commit touching a large corpus
      slice — for a reason having nothing to do with these ratchets — is structurally blocked by pre-existing debt the
      `--only` design was explicitly built to NOT grandfather. Repo: unified-trading-pm
      (`scripts/quality_gates/check_plan_operator_ruling_evidence.py`,
      `scripts/plan-hygiene/check_effort_signal_ratchet.py`). Done-when: same structural fix as the P2 todo below
      resolves this facet too (a grandfather/baseline mode for `--only`, or moving these two checks to periodic/batched
      sweep, would both fix it) — track under the same resolution, don't design a separate fix.
- [ ] [BACKEND] P2. Consider one or more structural fixes so ratchet regressions don't outrace serial fixing on a
      high-churn branch: (a) debounce/coalesce the CI re-trigger (e.g. the hourly `ldr-ci-monitor`) so a fix push
      doesn't immediately race a fresh concurrent regression; (b) batch multiple ratchet-fix commits into a single CI
      pass instead of one escalation-and-fix cycle per individual regression; (c) evaluate whether any of the four
      ratchet checks that regressed here (codex-doc-freshness, effort-ratchet, archive-candidates,
      dangling-reference-paths) should move from hard-fail to a periodic/batched sweep instead of per-commit
      enforcement, given they're corpus-wide ambient-drift-prone rather than tied to the committing agent's own diff.
      Repo: unified-trading-pm (`.github/workflows/`, `scripts/quality_gates/`).
- [ ] [REVIEW] P3. Once a structural fix lands, verify by watching the next 2-3 `quality-gates-v2` runs on
      `live-defi-rollout` for whether ratchet regressions still chain the way they did here.

## Progress log

- 2026-08-09 (main agt-22de53): Filed after answering BLK-bcb0be57 "B" (hand off) — worker had already tried 3
  fix-and-retrigger cycles across 4 different regressions with zero convergence. Not attempting a structural fix myself
  this tick; filing for a dedicated pass since the right answer (debounce vs. batch vs. move-to-periodic) needs design
  judgment, not a one-line change.
- 2026-08-09 (cicd agt-558c62, slot 14): Same escalation lineage, fresh dispatch. The `dangling-reference-paths` failure
  this escalation's context pointed at (95 > baseline 86) WAS a genuine, fixable, in-scope defect — 3 active-corpus docs
  citing 3 recently-archived docs via stale `plans/active/...` paths instead of the new `plans/archive/...` location.
  Fixed (path-only, `unified-trading-pm@d2aaf2ad1`), rebased through 1 incoming commit, pushed, and RE-VERIFIED GREEN on
  a fresh `quality-gates-v2` run for that specific check. However the SAME run failed on 2 further NEW regressions that
  landed from other concurrent agents' commits during the ~10 min fix cycle: `effort-signal-ratchet` (217->250, +33
  plans — a large batch of freshly-authored `sports_*`/`cross_cutting_*` satellite-dispatch docs with no declared
  `effort:`/`thinking_tier:`) and `archive-candidates` (0->1, one done-but-unarchived doc). Confirms the systemic
  finding directly: this is now the 6th consecutive distinct-regression-per-retrigger on this one escalation, across two
  separate dispatches. Declining to bulk-fix the effort-ratchet regression myself — 33 docs needing a per-doc
  effort-tier judgment call is audit-scope work (see `/na-eligibility-audit`/`/ag-closeout-audit`-shaped skills), not a
  one-shot CI-wall fix. Handing off again per the existing "B" ruling above rather than re-asking the same
  already-answered question.
- 2026-08-09 (context_scout_auditor, dispatch agt-264560, slot 16): Independently hit the same two ratchets from the
  LOCAL pre-commit angle (not CI) while running the daily `/context-scout` context_scope-maintenance sweep — added todo
  P3 above with the measurement (156/425 touched docs blocked, all pre-existing content). Worked around by excluding the
  156 affected docs from this session's commits rather than attempting per-doc fixes (outside this role's mandate); they
  remain untouched, tracked here for whoever picks up the structural fix.
- 2026-08-09 (slot 30, task `promote_ref_orphaned_on_manual_pr_close-001`): Independent confirmation on a DIFFERENT
  escalation path — `chore(promote): LDR -> main` PR #2648 (head `de1da7c33a`) failed `QG slice (checks)` on a 5th
  distinct ratchet check not yet listed above: `assigned_vm:NA corpus size (docs + open todos, ratchet)`
  (`scripts/plan-hygiene/check_na_corpus_ratchet.py`) — ran locally, confirmed a small overage (367 docs > baseline 365,
  1097 open todos > baseline 1093), consistent with ambient churn from concurrent sessions authoring NA-tagged docs, not
  a real spike. Per this doc's own established precedent, declined to chase it with a fix-and-retrigger cycle or a blind
  `--update-baseline` (remedy requires either an `/na-eligibility-audit`-scale triage pass or a reviewed, justified
  baseline bump — neither is a same-session one-shot fix for a worker not carrying that audit). Continuing to wait for
  `dbaa7b463` to reach `origin/main` via a future green promote cycle rather than intervening. Confirms the systemic
  finding extends to the NA-corpus check as well — 5 distinct ratchet checks now observed regressing under concurrent
  commit load: `codex-doc-freshness`, `effort-signal-ratchet`, `archive-candidates`, `dangling-reference-paths`,
  `assigned_vm:NA corpus size`.
- 2026-08-09 (slot 30, same task, later tick): PR #2648 was superseded (closed unmerged) by a fresh fleet-bot PR #2651
  (head `36541f9c1`, still carries `dbaa7b463`); #2651 also failed `QG slice (checks)` — same race, no new distinct
  check identified this cycle, so not logged as a 6th entry. Tooling note for whoever picks up the P2 structural-fix
  todo: the `qg-slice-failed-checks` artifact GH Actions uploads on failure is **not diagnostic** — it contains only the
  literal string `"checks failed"` (168 bytes), not which check(s) failed; identifying the actual failing check requires
  either `gh run view --log-failed` (verbose, slow) or reading the job's raw log for the checker script's own output.
  `dbaa7b463` still not on `origin/main` as of this tick; continuing to wait rather than intervene.
- 2026-08-09 (cicd agt-558c62, slot 23, 3rd dispatch of this same escalation lineage — after slot 3 and slot 14 both
  declined to keep chasing): triaged the ORIGINAL 2 regressions this escalation's context named (`effort-signal-ratchet`
  217->248, `archive-candidates` 0->1) as genuine, fixable, in-scope defects, not just ambient churn — reviewed each
  flagged doc individually (not a blind baseline bump): archived a fully-resolved TradFi issue doc + its now-obsolete
  line-cap-relief companion pair (3-file `git mv`, corpus referrers repointed), and added explicit `effort:` frontmatter
  to 79 recently-authored satellite AO-dispatch plans (mirroring each doc's own `assigned_role`'s already-deterministic
  role-registry thinking-tier — not a guess). Hit 2 real stash-pop content conflicts along the way (a concurrent
  context-scout sweep's Progress Log entry vs. mine on the same 2 docs) — resolved both as additive unions, not
  force-overwrites. Took roughly a dozen fetch/rebase/restage cycles (this branch's commit velocity is high enough that
  even single-file pulls landed mid-hook) before a commit finally survived long enough to push:
  **`unified-trading-pm@0e87ab46e`, verified ancestor-of-origin.** Re-ran both original checks locally post-push — still
  ✅ green (`effort-signal-ratchet`: 169 ≤ baseline 217; `archive-candidates`: 0 ≤ baseline 0) — confirming the fix
  itself is durable, not reverted. Dispatched a fresh `quality-gates-v2` run (31295043187) to confirm end-to-end: it
  failed again, but on the ALREADY-DOCUMENTED 5th distinct check from this doc (`assigned_vm:NA corpus size`), not on
  either of my 2 targets or a 6th new one — the systemic pattern held exactly as predicted, and my fix is not the cause.
  Per this doc's own established "hand off, don't keep chasing" precedent (already ruled twice on this same escalation
  lineage), declining a further fix-and-retrigger cycle for the NA-corpus regression — same reasoning as the slot-30
  entry above (audit-scale remedy, not a one-shot CI-wall fix). `AUTHORING_SLOT` for this escalation is the
  `ldr-ci-monitor` sentinel (not a numbered slot), so no slot-to-slot ping is applicable per this role's own skip-rule;
  recording the outcome here instead. Completing this dispatch via `/done` — 2 of 5 documented regressions now durably
  fixed and verified, 3 remain (codex-doc-freshness already fixed upstream per the doc header,
  `dangling-reference-paths` currently green per a live local check, so effectively `assigned_vm:NA corpus size` is the
  one live blocker as of this tick).
