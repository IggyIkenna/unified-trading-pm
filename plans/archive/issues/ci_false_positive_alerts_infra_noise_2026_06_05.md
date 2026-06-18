---
title: CI false-positive alerts — infra/checkout noise pages #ci-failures indistinguishably from real reds (suppression catalogue seed)
created: 2026-06-05
source:
  - deployment-service quality-gates-v2 run 27008990509 (live-defi-rollout promote PR) — actual job-log read
  - per-run "Notify #ci-failures" step conclusions verified via actions/runs/<id>/jobs API
  - live red-board sweep 2026-06-05 across 26 workspace repos
resolved: 2026-06-07
priority: P2
status: RESOLVED
---

> ## ✅ RESOLVED 2026-06-07 — archived (ACKED-INTO-CODE + ACKED-INTO-PLAN)
>
> The truthful-severity classification work (the operator's 2026-06-07 refined ask — verbose-while-debugging, NOT
> suppression) SHIPPED on `unified-trading-pm`: `notify-slack.yml` is now the central truthful-severity authority (a
> `failure`/`startup_failure` conclusion forces ≥CRITICAL `:x:`; `cancelled`/`timed_out`/etc force ≥WARNING; only
> `success`/`neutral` render ✅) — fixing the whole hardcoded-success class in one place; plus the two concrete bugs
> (`staging-to-main.yml` hardcoded "complete"+INFO on a failed promote; `update-repo-version.yml` clean body on failure)
>
> - an audit confirming the rest already pass `conclusion` and inherit the override. The doc's "Still open" infra-noise
>   ROOT-CAUSE reductions (the `.claude/worktrees` submodule leak + the thin-dep-clone `ModuleNotFoundError`) are
>   **MIGRATED to** `plans/active/cicd_contract_hardening_2026_06_01.md` § "CI false-positive / infra-noise root causes"
>   (P3). The UAC `STAGING_GREEN`-despite-red lead is explained by H1 (also migrated there). No codex `SSOTs:` section;
>   no new durable contract.

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

## Recommended decision (REVISED 2026-06-07 per operator — truthful severity, verbose-while-debugging, NOT suppression)

> **Operator refinement (2026-06-07) — this CHANGES the original "suppression catalogue" framing.** The design is NOT a
> silencing/suppression gate. While debugging the operator wants **MORE** alerts, not fewer — keep posting
> success/ran-OK alerts so we know things ran. The fix is **truthful CLASSIFICATION**: every alert's icon + wording +
> severity MUST be truthful to the REAL outcome.
>
> 1. **NEVER render ✅ / green-tick / "success" / "passed" / "complete" / "handled" when the actual conclusion is a
>    warning, error, or failure.** The rendered icon/word/status banner derives from the ACTUAL `conclusion` — a
>    non-green conclusion can never produce the green-tick.
> 2. **Three visibly-distinct severity lanes, all still POSTED** (verbose): real reds → 🔴 CRITICAL (`:x:`); infra /
>    checkout-noise + cancellations + warnings → a DISTINCT lower lane ⚠️/🚫 WARNING (still posted, visibly different);
>    genuine green → ✅ INFO only when truly green.
> 3. **Fix the hardcoded-success class.** Audit every notifier that emits a fixed ✅/INFO/"complete"/"handled" body
>    while passing a `conclusion` that can be `failure` — make the body + severity derive from the real result.

### SHIPPED 2026-06-07 (truthful classification — `unified-trading-pm`)

- **`.github/workflows/notify-slack.yml` — central truthful-severity authority.** The reusable notifier now
  truthful-classifies: a `failure`/`startup_failure` conclusion forces severity ≥ CRITICAL (`:x:`); `cancelled`/
  `timed_out`/`action_required`/`stale` force ≥ WARNING (`:no_entry_sign:`); only `success`/`neutral` render ✅ and
  `skipped` renders skip. A caller's optimistic `severity: INFO` can no longer mask a non-green conclusion. The header
  now carries a truthful "result: FAILED (failure)" status word so an optimistic body can never read as success. This
  fixes the WHOLE class in one place because every caller passes the job's `conclusion`.
- **`.github/workflows/staging-to-main.yml` — the exact 2026-06-07 bug.** `notify-promotion-complete` previously sent a
  hardcoded `"Staging → main promotion complete"` + `severity: INFO` even when `promote-staging-to-main.result` was
  `failure` (a step erroring before `failed_count` is set still satisfies the `failed_count==''` gate). Now the message
  and severity derive from the job result ("did NOT complete cleanly (job result ...)" + CRITICAL on non-success).
- **`.github/workflows/update-repo-version.yml`** — the `Version update: …` notifier (INFO + clean body regardless of
  result) now emits a "FAILED" body + CRITICAL when `update-manifest.result != success`.
- Audited the remaining notifiers: `ldr-to-staging-promote.yml` / `deterministic-promotion-conflict-resolve.yml` /
  `escalate-to-orchestrator.yml` already pass `conclusion: …result` and now inherit the central truthful-severity
  override; `major-bump-approval.yml` is gated `if: result == 'success'` so its INFO/"handled" body is truthful (never
  posts on failure); `ci_failure_watcher.py::build_report` already derives `:x:`/`:white_check_mark:` from the real
  transition kind (FAILING→red, RECOVERED→green) — no false-success path.

### Still open (the infra-noise root causes — separate, lower priority)

1. **Fix the cheap root causes** so they stop failing at all: the `.claude/worktrees` submodule leak (a checkout-hygiene
   bug) and the thin-dep-clone `ModuleNotFound` (widen the clone set or skip the import under CI). (These are noise
   REDUCTION, not the truthful-severity ask — the alerts are now truthful regardless.)
2. **Owner**: cicd/dep-security epic (co-locate with the `ci-failure-watcher` / Guard work in
   `cicd_contract_hardening_2026_06_01.md`).

## Explicitly NOT concluded here (to avoid filing a hunch)

- I observed that UAC's authoritative `ci_status` on `origin/main` reads `STAGING_GREEN` despite a live red promote PR,
  and that UAC's run-27009399635 **"Record CI status" step itself failed** (conclusion=`failure`) — so its `FAILING`
  dispatch likely never sent. That is a **lead**, not a root cause: deployment-service / unified-trading-library /
  strategy-service all correctly show `FAILING`, so this is not a systemic SSOT failure. Left for a focused follow-up
  rather than filed as a confident finding.
