---
doc_type: issue
title: "market-data-processing-service quality-gates-v2 QG_SLICE=tests OSError signature RECURS a 2nd time (promotion PR #724, 2026-08-19) — harden-the-class trigger"
summary: >-
  cicd escalation agt-f88c44 (WALL_TYPE=ldr_qg_failure, REPO=market-data-processing-service,
  PR_NUMBER=724) hit the IDENTICAL failure signature already documented and closed as a one-off
  flake in `plans/archive/2026_08/issues/mdps_main_qg_tests_slice_oserror_cannot_send_2026_08_18.md`
  (2026-08-18, push to main, run 32122593759): pytest-xdist crashes mid-suite during
  `pytest_sessionfinish` teardown with `OSError: cannot send (already closed?)`, no FAILURES section,
  full suite forced by TEST_IMPACT_GATE. This is now the 2nd occurrence of the EXACT SAME signature
  on the SAME repo within 24h (2026-08-18 09:45Z on main, 2026-08-19 02:04Z on promotion PR #724).
  Per this workspace's "harden the class" rule (a checker/flake that fires falsely more than once
  deserves a deeper fix, not another rerun-and-close), this doc exists to make that 2nd recurrence
  trackable rather than silently re-closed the same way twice.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [market-data-processing-service]
scope: [engineer, admin]
tags: [ci-cd, quality-gates-v2, flaky-test, xdist, harden-the-class, recurrence]
related: [/plans/active/ci_consolidated_closeout_2026_07_25.md]
context_scope:
  [
    /plans/archive/2026_08/issues/mdps_main_qg_tests_slice_oserror_cannot_send_2026_08_18.md,
    scripts/quality-gates-base/base-service.sh,
    /codex/06-coding-standards/quality-gates.md,
    .github/workflows/quality-gates-v2.yml,
  ]
created: "2026-08-19"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
assigned_role: infra
drift_direction: none
source: >-
  cicd escalation agt-f88c44, dispatched via POST /api/escalate (wall_type=ldr_qg_failure) on
  market-data-processing-service#724 (LDR -> main promotion PR), failing run
  https://github.com/IggyIkenna/market-data-processing-service/actions/runs/32207039602.
resolved_by:
locked_by:
depends_on: []
---

# market-data-processing-service QG tests-slice OSError — 2nd recurrence, immediate wall resolved

> **Immediate CI wall is RESOLVED** (PR #724 merged after a green rerun) — this doc tracks the
> RECURRING PATTERN, not an open promotion block. Read
> `plans/archive/2026_08/issues/mdps_main_qg_tests_slice_oserror_cannot_send_2026_08_18.md` first —
> same repo, same error string, same "no FAILURES section, teardown-only" shape, 18h earlier.

## What I found (this session, agt-f88c44)

- Promotion PR `market-data-processing-service#724` (LDR `e6aed01c` -> main) went RED on
  `quality-gates-v2` — specifically `QG slice (tests)` / step "Run quality gates (leg tests)",
  run [32207039602](https://github.com/IggyIkenna/market-data-processing-service/actions/runs/32207039602).
- `checks` slice (typecheck + lint-codex) PASSED; only `tests` failed.
- `TEST_IMPACT_GATE` chose `RUN_FULL_SUITE=true` (reason: a changed file — a since-relocated
  scratch script — "not found on disk (deleted?)").
- pytest+xdist progressed to ~43% (`bringing up nodes...` then dot-progress through `[ 43%]`) then,
  with NO test marked `F`/`E` and no FAILURES/short-summary section anywhere in the step log,
  emitted two `PluggyTeardownRaisedWarning` blocks during `pytest_sessionfinish` hookwrapper
  teardown, each with `OSError: cannot send (already closed?)`, then `##[error]QG selector 'tests'
  FAILED (leg=tests, exit=1)`.
- Grepped the corpus for the exact string `cannot send (already closed` — found ONE prior hit on
  this exact repo, 18h earlier: `plans/archive/2026_08/issues/mdps_main_qg_tests_slice_oserror_cannot_send_2026_08_18.md`
  (push to `main`, run 32122593759, 2026-08-18 09:45Z). That doc's own resolution: `gh run rerun
  --failed` came back `conclusion=success`, closed as one-off flake, EXPLICITLY conditioned on
  "worth a deeper fix only if it recurs a second time."
- Tested the same hypothesis this session: `gh run rerun 32207039602 --failed` → came back
  `conclusion=success` on ALL legs (content sentinel / QG slice checks / QG slice tests /
  quality-gates-v2), confirmed via `gh run view --json status,conclusion,jobs`. PR #724 is now
  `state: MERGED`. No code change was needed or made — the LDR tree was never at fault (the fix,
  if any, is CI-host-level, not repo-code-level).

## Why this is now a harden-the-class trigger, not just another close

The precedent doc's own "What's NOT yet confirmed" section named exactly this fork: confirmed
one-off flake (self-heals, no action) vs genuine regression needing a root-cause fix. It self-healed
BOTH times, so it is not (yet) a code regression — but the *recurrence itself*, on the same repo,
same exact error string, less than a day apart, is the specific trigger this workspace's own
"checker/test that fires falsely more than once" rule names for moving past rerun-and-close. This
doc is the tracked artifact for that — the next occurrence (a 3rd) should not be closed the same way
without first doing the deeper dive below.

## What's NOT yet confirmed (root cause)

- Whether this is host-level resource contention on the shared self-hosted `glue` runner fleet
  (plausible: the job log shows `QG_MEM_CAP=2048M set but systemd-run unavailable on this host →
  running pytest + basedpyright without hard memory cap` — i.e. the intended memory ceiling for this
  exact class of crash is NOT being enforced on whichever runner box picks up the job) vs an
  xdist/pytest-asyncio interaction bug in a specific test's async fixture teardown (the error text
  — "cannot send on an already-closed channel" — is consistent with an xdist worker's IPC pipe being
  torn down while a message was still in flight, which is exactly what an OOM-killed or
  signal-killed worker process would produce).
- Which specific test (if any single one) triggers it — neither occurrence's log captured a
  FAILURES/short-summary section, so the crash point is bracketed only by "somewhere between ~35%
  and ~43% of the full suite," not a named test id. A 3rd occurrence should capture the FULL
  (unfiltered) step log immediately, before any rerun, specifically to get past this gap.
- Whether `QG_MEM_CAP` enforcement (systemd-run) is actually available/working on the `glue`
  self-hosted runner pool generally, or only unavailable on whichever specific runner box handled
  these two runs — if the former, this is a fleet-wide latent capacity risk, not MDPS-specific.

## Todos

- [ ] [SCRIPT] P2. On a 3rd occurrence of this exact `OSError: cannot send (already closed?)`
      signature (any repo, not just market-data-processing-service — grep
      `cannot send (already closed` across #ci-failures / issue docs first to confirm it's the same
      class): before rerunning, pull the FULL (unfiltered) `QG slice (tests)` step log and identify
      the exact test id running when the crash occurs (correlate xdist's per-worker stdout
      interleaving, or re-run locally with `-p no:xdist` / `-n0` to get a single-process trace with
      the real traceback). If a specific test/fixture is implicated, fix its async resource
      lifecycle in that repo. If it remains unlocalizable, escalate to a fleet-wide
      `QG_MEM_CAP`/systemd-run-availability audit on the `glue` self-hosted runner pool (repo:
      unified-trading-pm, `scripts/quality-gates-base/`) instead of continuing to treat it as
      per-repo noise.
- [ ] [SCRIPT] P3. Confirm whether `systemd-run` is expected to be available on the `glue` runner
      pool at all (repo: unified-trading-pm, `.github/workflows/quality-gates-v2.yml` /
      `scripts/quality-gates-base/`) — if the intended memory-cap enforcement path is silently
      unavailable fleet-wide (not just on the two runner boxes that hit this), that's a bigger
      finding worth its own doc per CLAUDE.md's "operator notify" bar for cross-cutting CI findings.

## Progress Log

- **context-scout 2026-08-19**: populated/refreshed context_scope (4 entries).

**na-eligibility-audit 2026-08-21** (ci tranche wave 2, first audit pass — doc filed 2026-08-19): KEEP-NA, valid.
Both open todos are explicitly conditional/investigation work, not bounded specs: todo 1 fires only "on a 3rd
occurrence" of this exact `OSError: cannot send (already closed?)` signature and requires live diagnostic judgment
(correlate xdist worker interleaving or reproduce locally to localize the failing test/fixture) with a fleet-wide
escalation branch if unlocalizable; todo 2 asks to "confirm whether `systemd-run` is expected to be available" on
the `glue` runner pool — an open factual question with no stated resolution path yet. Conflict-checked: grepped
`plans/active/issues/*.md` for "cannot send (already closed" — no other doc has recorded a 3rd occurrence as of this
pass, so todo 1's trigger condition is not yet met. No `assigned_vm` change.
