---
title: CI false-positive alerts — infra/checkout noise pages #ci-failures indistinguishably from real reds (suppression catalogue seed)
created: 2026-06-05
author: harsh [hk·interactive]
source:
  - deployment-service quality-gates-v2 run 27008990509 (live-defi-rollout promote PR) — actual job-log read
  - per-run "Notify #ci-failures" step conclusions verified via actions/runs/<id>/jobs API
  - live red-board sweep 2026-06-05 across 26 workspace repos
locked_by: live-defi-rollout
---

> Seeded per Ikenna's 2026-06-05 ask ("help diagnose false positives and missed alerts … start verbose, cut when
> working"). This records the FIRST **verified** false-positive class. Scope is deliberately limited to what I confirmed
> from job logs + step conclusions — not hypotheses.

## What I found

**The per-run `#ci-failures` notifier fires on EVERY `quality-gates-v2` failure, including failures that are pure infra
/ checkout noise (not a product or test bug).** Verified the notify side actually fired (not just that it exists):

| Repo                  | Run         | Failure cause (from job log)                                                                                                                                  | Real?                | "Notify" step     |
| --------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- | ----------------- |
| deployment-service    | 27008990509 | `fatal: No url found for submodule path '.claude/worktrees/agent-aa4b436033ef73e2f' in .gitmodules` + `ModuleNotFoundError: No module named 'deployment_api'` | **NO — infra noise** | `success` (paged) |
| unified-api-contracts | 27009399635 | aiohttp `AsyncStreamReaderMixin` (real — see `aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md`)                                                           | yes                  | `success` (paged) |
| instruments-service   | 27010513492 | env-tiered bucket test (real, in-flight fix; tracked as P2 in `#396` plan)                                                                                    | yes                  | `success` (paged) |

So the alerting is **not** missing alerts at the per-run notify layer — it is **over-paging**: a checkout/dep-infra
failure pages the operator channel with the same weight as a genuine red. Across the same 26-repo sweep, roughly half of
the `quality-gates-v2` failures in the last ~24h were infra/config noise rather than code reds.

### Verified noise signatures (the start of a suppression catalogue)

| Signature (regex-able)                                                        | Why it's noise                                                                                                                          | Action                                                                        |
| ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `fatal: No url found for submodule path '.claude/worktrees/…' in .gitmodules` | an agent worktree path leaked into the CI checkout's submodule resolution — nothing to do with the code under test                      | **NEW** — suppress + stop the leak at the checkout/`.gitmodules` hygiene step |
| `ModuleNotFoundError: No module named '<service>'` during QG dep-clone        | CI clones a thin `dep_repos` subset; a transitively-needed service isn't cloned (documented "thin dep_repos" gotcha in `ci-cd-flow.md`) | suppress OR widen the clone set; tag `infra-noise` not a code red             |

Already-tracked noise (do not re-file): UI cross-repo `GH_TOKEN` / `Resource not accessible by integration` /
`missing workload_identity_provider` → `ui_ci_cross_repo_github_token_violations_2026_06_04.md`.

## Why it matters

A channel that pages on infra noise at the same severity as real reds trains operators to skim past it — which is the
exact failure mode that let the original CI/CD promotion rot stay silent for months (the reason `ci-failure-watcher`
exists). Cutting verified false positives is the "cut when it's working" half of Ikenna's verbose-then-trim plan.

## Recommended decision (for Ikenna to convert to a plan)

1. **Classify, don't silence.** Add the two verified signatures above to the per-run notifier / `ci_failure_watcher.py`
   classifier so an infra-noise failure is tagged (or routed to a low-priority lane) rather than paging `#ci-failures`
   at red severity. Grow the catalogue as the red-board is worked.
2. **Fix the cheap root causes** so they stop failing at all: the `.claude/worktrees` submodule leak (a checkout-hygiene
   bug) and the thin-dep-clone `ModuleNotFound` (widen the clone set or skip the import under CI).
3. **Owner**: cicd/dep-security epic (co-locate with the `ci-failure-watcher` / Guard work in
   `cicd_contract_hardening_2026_06_01.md`).

## Explicitly NOT concluded here (to avoid filing a hunch)

- I observed that UAC's authoritative `ci_status` on `origin/main` reads `STAGING_GREEN` despite a live red promote PR,
  and that UAC's run-27009399635 **"Record CI status" step itself failed** (conclusion=`failure`) — so its `FAILING`
  dispatch likely never sent. That is a **lead**, not a root cause: deployment-service / unified-trading-library /
  strategy-service all correctly show `FAILING`, so this is not a systemic SSOT failure. Left for a focused follow-up
  rather than filed as a confident finding.
