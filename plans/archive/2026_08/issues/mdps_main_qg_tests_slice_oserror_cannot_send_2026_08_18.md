---
doc_type: issue
title: "market-data-processing-service main branch quality-gates-v2 FAILED — QG_SLICE=tests, single OSError signature (2026_08_18)"
summary: >-
  /ci-reconcile's mandatory pre-report re-poll of #ci-failures (2026-08-18) surfaced a CRITICAL
  from ci-status-update at 09:45Z: market-data-processing-service regressed MAIN_GREEN -> FAILING
  on push to `main` (sha ffd2278ea73160a36fe0add79a2aa7c8a8f510b2, run 32122593759). The `checks`
  and `typecheck` legs both passed; only QG_SLICE=tests failed, with a single visible error just
  before the selector-failed marker: `OSError: cannot send (already closed?)`. TEST_IMPACT_GATE
  ran the FULL suite (`RUN_FULL_SUITE=true reason="no HEAD~1 diff available or no .py files
  changed"` — itself odd for a push that presumably did change files). No repo working tree was
  touched. A re-run of the failed job (`gh run rerun 32122593759 --failed`) was dispatched to test
  whether this is a transient async-resource-cleanup race (a common shape for this exact error
  string — a mock server/session closed while a response was still in flight) vs a genuine
  regression, but the outcome was not observed before this session closed out (out of scope for
  the /ci-reconcile pass that found it; the original ask was 4 specific, unrelated alerts, all
  resolved separately).
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [market-data-processing-service]
scope: [engineer, admin]
tags: [ci-reconcile, quality-gates-v2, flaky-test, main-regression]
related: []
created: "2026-08-18"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
assigned_role: infra
drift_direction: none
source: >-
  /ci-reconcile interactive run, 2026-08-18 (this session) — mandatory pre-report re-poll of
  #ci-failures via scripts/dev/slack-read-channel.py surfaced the ci-status-update CRITICAL;
  gh run view --log/--log-failed on run 32122593759 read directly to isolate the failure signature.
resolved_by: >-
  Confirmed one-off flake: `gh run rerun 32122593759 --failed` (dispatched ~09:58Z) came back
  conclusion=success on re-check (same run id, same sha ffd2278ea73160a36fe0add79a2aa7c8a8f510b2) —
  https://github.com/IggyIkenna/market-data-processing-service/actions/runs/32122593759
locked_by:
depends_on: []
---

# market-data-processing-service main QG regression — single OSError, cause unconfirmed

> **ARCHIVED**: resolved via `gh run rerun` confirmation, 2026-08-18 (interactive /ci-reconcile session).
> Successor: none (confirmed one-off flake; no follow-up work unless it recurs).

## What I found

`ci-status-update` posted a CRITICAL at 2026-08-18 09:45Z: market-data-processing-service's
`ci_status` flipped `MAIN_GREEN` -> `FAILING`. Ground-truthed via `gh run list`/`gh run view`:

- Run [32122593759](https://github.com/IggyIkenna/market-data-processing-service/actions/runs/32122593759),
  push to `main`, sha `ffd2278ea73160a36fe0add79a2aa7c8a8f510b2`, created 2026-08-18T09:37:43Z.
- `QG slice (checks)` — PASSED (`typecheck` and `lint-codex` both green; 9 basedpyright errors are
  pre-existing warn-only, not new).
- `QG slice (tests)` — FAILED. `TEST_IMPACT_GATE` chose `RUN_FULL_SUITE=true` with
  `reason="no HEAD~1 diff available or no .py files changed"`. The only error visible in the log
  immediately before `##[error]QG selector 'tests' FAILED (leg=tests, exit=1)` is:
  ```
  OSError: cannot send (already closed?)
  ```
  No pytest short-summary/FAILURES section was captured in `--log-failed` output — either it's
  further up in the full step log than was pulled this session, or the failure is happening in
  teardown/fixture-close rather than inside an individual test body (consistent with the error
  text: a socket/session already closed when something tried to send on it).
- No other repo in the fleet-wide sweep this session was red; this looks isolated to MDPS.

## Why it matters

`main` deploys nothing directly (CLAUDE.md: "landing on main DEPLOYS NOTHING"), so this is not an
outage — but `ci_status=FAILING` on main is the Firestore-SSOT signal several other mechanisms key
off (dependency-alignment checks, the fleet's green/red dashboards). Left FAILING, it will keep
paging `#ci-failures` on every subsequent `ci-status-update` dispatch until someone looks at it.

## What's NOT yet confirmed

- Whether `OSError: cannot send (already closed?)` is a flaky async-teardown race (single
  occurrence, `RUN_FULL_SUITE=true` on a push whose reason string suggests the diff-detection
  itself may be misbehaving) or a genuine new regression in test/fixture code.
- Whether `gh run rerun 32122593759 --repo IggyIkenna/market-data-processing-service --failed`
  (dispatched this session, ~09:58Z) came back green (self-healed flake) or red again (real
  regression needing a root-cause fix) — check `gh run list --repo IggyIkenna/market-data-processing-service
  --branch main --limit 3` for the rerun's outcome before doing anything else here.

## Recommended decision

1. Check the rerun's outcome first (cheap, decides everything else).
2. If green: mark `status: resolved`, `resolved_by:` (rerun evidence) — an intermittent flake,
   worth a follow-up only if it recurs a second time (per this workspace's own "harden the class"
   rule for a checker/test that fires falsely more than once).
3. If red again with the SAME `OSError`: pull the full (not `--log-failed`-filtered) step log for
   `QG slice (tests)`, find which test/fixture actually raises it, and fix the resource-lifecycle
   bug (repo: market-data-processing-service) — this is a real regression, not noise.

## Todos

- [x] ✅ [SCRIPT] P2. Check the outcome of the `gh run rerun 32122593759 --failed` dispatched
      2026-08-18 ~09:58Z (repo: market-data-processing-service) — DONE. Rerun came back
      conclusion=success; `main`'s `ci_status` is back to `MAIN_GREEN`. Confirmed one-off flake, not
      a real regression — no code fix needed. Per this workspace's "harden the class" rule, only
      worth a deeper fix if `OSError: cannot send (already closed?)` recurs a second time on this
      repo's test suite.
