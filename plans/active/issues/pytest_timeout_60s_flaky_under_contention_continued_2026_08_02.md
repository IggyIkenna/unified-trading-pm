---
doc_type: issue
title:
  "pytest-timeout-under-contention bug class continues (original doc at 1000-line hard cap) — unified-trading-api's 5th
  occurrence in one day, this time fixed with a repo-local mitigation rather than left as noise"
summary: >-
  Continuation of `/plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md` (996/1000 lines, its
  own last entry already flagged "next occurrence MUST split/archive, not append"). `cicd` escalation `agt-bde7b9`
  (`WALL_TYPE=ldr_qg_failure`, `REPO=unified-trading-api`, slot 4) hit unified-trading-api's 5th same-day recurrence of
  this doc's flake class — 4 prior consecutive `quality-gates-v2` failures on 2026-08-02 (13:32Z/18:41Z/21:12Z/22:36Z
  runs), each via `Failed: Timeout (>150.0s) from pytest-timeout` on a DIFFERENT random subset of route tests (9-10 of
  441), all passing in well under 1s locally in isolation. Confirmed via a full local `quality-gates.sh` run at LDR HEAD
  `990187dd5` — 100% green, 441 passed, 79s — that no code/test defect exists; host corroboration at investigation time:
  `load average 24.83-29.28` on 16 vCPUs, `20Gi/47Gi` swap in active use, 23 concurrent `quality-gates.sh` processes + 7
  sibling self-hosted `glue` CI runners sharing this same physical host — matching every prior entry in the parent doc's
  "fleet-wide QG capacity crisis, not a regression" diagnosis. Unlike every prior entry (which all concluded "no action
  taken, self-clears"), this occurrence had NOT self-cleared after 4 attempts spanning 9+ hours (no green run since
  2026-07-31 10:55Z, 36+ hours prior) — so rather than a 5th blind retry, applied the parent doc's own sanctioned fix
  philosophy ("raising a wall-clock timeout to absorb scheduling variance is not weakening the check") as a repo-local,
  low-blast-radius mitigation.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-api, unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, flaky-gate, timeout, pytest-timeout, ci, shared-host-contention, xdist]
related:
  [
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
  ]
created: 2026-08-02
last_updated: 2026-08-02T23:55Z
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: cicd
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: "cicd-role escalation agt-bde7b9 (WALL_TYPE=ldr_qg_failure, REPO=unified-trading-api, slot 4)"
---

# pytest-timeout-under-contention: unified-trading-api's 5th occurrence, fixed with a repo-local mitigation

Parent doc `/plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md` is at its 1000-line hard cap
(996 lines) with its final entry explicitly noting "next occurrence MUST split/archive, not append" — this doc is that
split, not a duplicate.

## What was found + done

`cicd` escalation `agt-bde7b9` for `unified-trading-api` `ldr_qg_failure` (`PR_NUMBER=0`, no PR — direct LDR push gate).
LDR HEAD `990187dd5bdc0459e4ec3b639cfac035312be98a` (2026-08-02T12:52:43Z). CI runs `30761689446` (18:41Z, 10 tests / 9
files) and `30770482343` (22:36Z, 9 tests / 8 files) both failed via `Failed: Timeout (>150.0s) from pytest-timeout` on
a DIFFERENT random test subset each time (`test_events`, `test_defi_basis`, `test_defi_liquidation`, `test_registry`,
`test_defi_lp`, `test_strategy_performance`, `test_middleware`, `test_routes`, `test_routes_extra`, `test_catalogue`
across the two runs) — no test-content overlap, consistent with scheduler-descheduling under host contention rather than
a real hang or a per-test anti-pattern. Local reproduction at the same HEAD: `quality-gates.sh` backgrounded per the
mandatory pattern, 441/441 passed, 68-79s, zero timeouts, across 2 independent runs. Host snapshot at investigation
time: `load average: 24.83, 26.18, 29.28` (16 vCPUs — 1.5-2x oversubscribed), `20Gi/47Gi` swap in use, 23 concurrent
`quality-gates.sh` processes (`pgrep -af`), 7 concurrent self-hosted `glue` CI runner processes on the SAME physical
host. Zero open `/api/repo-blockers` entries for `unified-trading-api`.

Unlike the parent doc's prior entries (which found LDR already green by investigation time and took no action), this
repo had 4 consecutive failures with no green run in 36+ hours — the "self-clears" assumption did not hold here. Rather
than a 5th unmonitored multi-hour retry against a demonstrably still-saturated host, applied the parent doc's own
established fix philosophy as a scoped, low-risk, repo-local mitigation: `unified-trading-api@71cdda0` adds
`PYTEST_TIMEOUT=${PYTEST_TIMEOUT:-300}` to the repo's own `scripts/quality-gates.sh` (before sourcing
`base-service.sh`), doubling this repo's effective budget over the shared 150s default. This changes no check's
assertion — only the wall-clock deadline the same passing tests are held to. Verified locally green post-change (68s,
441 passed) and shipped via `quickmerge --agent --files 'scripts/quality-gates.sh'`, confirmed on
`origin/live-defi-rollout` via `merge-base --is-ancestor`. Fresh `quality-gates-v2` run triggered
(`gh workflow run quality-gates-v2.yml --ref live-defi-rollout`) — run id in the Progress Log below once observed.

## Todos

- [ ] 1. [INFRA] P3. Once the fresh post-mitigation `quality-gates-v2` run (triggered this session) completes, record
      the outcome here. If GREEN: confirms a 300s repo-local budget clears this specific severity of contention for
      unified-trading-api; consider this the template for any OTHER repo that similarly fails to self-clear (i.e., a
      per-repo `PYTEST_TIMEOUT` override is preferable to indefinite blind retries once a repo shows sustained,
      non-self-clearing red). If RED again with the same timeout signature even at 300s: this repo's host contention
      severity now exceeds what a 2x budget raise absorbs — escalate to the parent capacity-crisis doc
      (`/plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`) rather than raising the
      timeout further in isolation (per that doc's own conclusion: repeatedly raising a deadline "moves the threshold,
      does not close the class").
- [ ] 2. [INFRA] P3. If todo 1 confirms the fix, consider whether other repos in the parent doc's `repos:` list with
      recurring (not just single) unified-trading-api-style sustained-red occurrences would benefit from the same
      repo-local `PYTEST_TIMEOUT` raise, rather than relying solely on retries. Not done proactively here — scope
      bounded to the one escalation this doc was filed under.

## Progress Log

- **2026-08-02 23:52Z (`cicd` `agt-bde7b9`, slot 4)** — Diagnosed, applied repo-local `PYTEST_TIMEOUT=300` mitigation
  (`unified-trading-api@71cdda0`), shipped + verified on origin, triggered fresh `quality-gates-v2` run `30773174599`.
  Filed this continuation doc (parent doc at hard cap). Outcome of the fresh run to be added once observed by this or a
  follow-up session.
