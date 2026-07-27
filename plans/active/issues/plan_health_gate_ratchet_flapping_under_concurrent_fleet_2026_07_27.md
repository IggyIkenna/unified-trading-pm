---
doc_type: issue
title:
  "plan_health-agent.yml's PR->main hard gate flaps on the reference-path + NA-corpus ratchets under normal ~10-agent
  concurrent-fleet load, burning shared cicd-escalation capacity repeatedly on largely-benign churn rather than a real
  regression"
summary: >-
  Observed live 2026-07-27: the plan_health gate (`plan-health-gate` job, `.github/workflows/plan-health-agent.yml`,
  triggered on every `pull_request: branches: [main]` — i.e. every LDR->main promotion PR, which fires on the standing
  `*/15` promote cadence) needed a dedicated cicd-escalation worker to fix the SAME two ratchet checks
  (`check_reference_paths.py` format count, `check_na_corpus_ratchet.py` doc+todo count) **five times in ~2.5 hours**
  today (commits 747666e 14:20, 54b28b7 14:50, 34ab78d 14:57, f5cd418 15:40, 88bd16a 16:44 — all titled "clear
  plan_health gate"). Root cause: both ratchets are corpus-wide LIVE counts compared against a static baseline, and with
  ~10 agents concurrently committing plan/issue docs to `live-defi-rollout` (this session alone saw 8 separate
  `git pull --ff-only` fast-forwards land mid-triage, several within under a minute of each other), the live count keeps
  drifting past whatever baseline the last fix set within minutes of it landing — sometimes before the fix's own commit
  even reaches the next promotion PR. My own escalation (agt-684153) needed 3 separate pull-commit-retry cycles just to
  get a green-at-fix-time snapshot committed before `check-branch-drift` rejected it again. The NA-corpus ratchet in
  particular cannot be "fixed" by triage alone in this regime: a real audit-quality archive pass (my one legitimate find,
  `deployment_ui_fleet_tab_removal_2026_07_27.md`, 0 open todos, fully resolved) took real investigation time, while 3
  new genuinely-open NA docs landed from other agents in that same window — the corpus is growing faster than any
  bounded triage pass can shrink it, which is a capacity mismatch, not a hygiene defect in any single doc.
status: open
nature: issue
asset_group: [ao, ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [plan-health, ratchet, ci-cd, concurrency, ci-cost, cicd-escalation, na-corpus, reference-paths, flapping]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/active/issues/na_eligibility_auditor_timer_not_yet_installed_2026_07_27.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
  ]
created: 2026-07-27
last_updated: "2026-07-27"
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: >-
  cicd escalation worker (agt-684153, plan_health wall on unified-trading-pm#1681, 2026-07-27), while triaging: found
  the same two ratchets had already needed fixing 4 times earlier the same day by other cicd escalations, and drifted
  again mid-fix in this session (2 more `check-branch-drift` rejections, 3 more genuinely-new NA docs landing).
locked_by:
resolved_by:
---

# plan_health gate flaps on ratchet checks under concurrent-fleet load

## The pattern (evidenced)

| time (UTC) | commit    | what                                                          |
| ---------- | --------- | -------------------------------------------------------------- |
| 14:20      | 747666e   | clear plan_health gate — reference paths, AG-closeout orphan, NA-corpus ratchet |
| 14:50      | 54b28b7   | clear plan_health gate — reference paths + NA-corpus ratchet    |
| 14:57      | 34ab78d   | clear plan_health gate — reference-path format drift + NA-corpus baseline refresh |
| 15:40      | f5cd418   | clear plan_health gate — reference-path format drift, AG-closeout orphan, NA-corpus reviewed raise |
| 16:15      | c00860d   | lower NA-corpus ratchet baseline 362/1431 -> 360/1421 (a genuine triage pass) |
| 16:44      | 88bd16a   | clear plan_health gate — reference-path format drift + NA-corpus reviewed raise (this escalation, agt-684153) |

Six interventions on the same two checks inside ~2.5 hours. Every one of them found the corpus had already drifted past
whatever the previous fix had just set, because unrelated agents keep landing plan/issue docs on `live-defi-rollout`
throughout the day (this session alone pulled 8 incoming fast-forwards while triaging one wall).

## Why this is a capacity problem, not (only) a hygiene problem

- **Reference-path format check**: a single bare `codex/...` ref anywhere in a freshly-authored doc trips it. With ~10
  agents authoring docs concurrently, the odds that ANY one of them drops the leading slash in ANY commit within a
  15-minute promotion window are non-trivial — and the gate's baseline is a single global counter, so one slip anywhere
  fails the next PR for everyone.
- **NA-corpus ratchet**: by design (see `na_corpus_baseline.yaml`'s own header) most new NA content is legitimate and
  should stay NA — the check is deliberately NOT "drive to zero." But a shrinking ratchet compared against a corpus that
  ~10 agents are actively adding genuinely-open issue docs to, all day, means the count is expected to run ahead of
  triage capacity unless a dedicated `/na-eligibility-audit`-scale sweep runs continuously, which it does not (it is a
  scheduled/on-demand skill, not a 15-minute-cadence process).

## Options for whoever picks this up (operator/plan_reconciler judgment call, not mine to decide unilaterally)

1. **Debounce the gate**: only run `plan-health-gate` on the LDR->main promotion PR if plan/codex files actually changed
   since the last GREEN run of this exact check (skip re-checking on promotion PRs whose diff is pure non-plan code),
   OR only re-evaluate the ratchet baselines once per N minutes instead of on every PR.
2. **Move the two flappy ratchets to the daily digest** (the existing `plan-health` report-only job already runs
   02:00 UTC) instead of the HARD PR gate, since they are corpus-health trends, not per-PR regressions — the
   frontmatter/todo-format/line-cap checks (deterministic, PR-content-local) stay as hard PR gates; the two
   corpus-wide-count ratchets become a tracked trend metric with a slower cadence.
3. **Batch tolerance**: widen these two ratchets' comparison to "current <= baseline + K" where K absorbs single-digit
   concurrent-fleet noise (e.g. K=3-5, calibrated from today's observed drift), so a lone flapping open issue doesn't
   burn a full cicd-escalation cycle — while still catching a genuine large regression.
4. **Status quo + accept the cost**: if 5-6 escalations/day is an acceptable price for the two gates' current strictness,
   no change needed — but that should be a deliberate call, not an emergent one.

None of these are urgent (the gate DOES eventually resolve; no data was lost; no incorrect promotion occurred) — this is
a process-efficiency finding, not a correctness bug.

## Todo

- [ ] [DESIGN] P2. Operator/plan_reconciler: decide whether to debounce/relocate/widen-tolerance the
      `check_reference_paths.py` + `check_na_corpus_ratchet.py` PR-gate checks (options above), given the measured
      5-6x/day escalation cost under current ~10-agent concurrent-fleet load. If no change is wanted, close this issue
      with that explicit rationale.
