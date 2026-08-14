---
doc_type: issue
title: deployment-api quickmerge blocked fleet-wide by 2 pre-existing, unrelated test failures
summary: >-
  Discovered while shipping an unrelated fix (register the new CI-escalation-runner VM's classification prefix):
  quickmerge's re-gate step fails on the current deployment-api tree due to 2 pre-existing, unrelated test failures —
  not caused by the classification change (confirmed via git stash — both fail identically on the clean tree). This
  blocks ANY commit to deployment-api via quickmerge right now, not just this one.
status: resolved
nature: issue
asset_group: [ui]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: [quickmerge, test-failure, deployment-api, blocking]
related: [/plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md]
created: 2026-08-04
author: unknown
priority: P1
parent_epic: infrastructure_master
source: "interactive session, 2026-08-04 — discovered shipping a VM-classification fix, not this issue's own scope"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
  "deployment-api@59f5cbe8 (both P1 fixes) + deployment-api@e4072fb (VM-classification re-ship); all ancestor-verified
  on origin/live-defi-rollout"
locked_by:
locked_since:
context_scope:
  [
    deployment-api/deployment_api/services/data_query_service.py,
    deployment-api/tests/unit/test_data_query_service_helpers.py,
    deployment-api/tests/unit/test_route_data_status_distinct_values.py,
    /plans/archive/2026_08/sports_instrument_type_market_token_ssot_gap_2026_07_28.md,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
  ]
---

# deployment-api quickmerge blocked by 2 pre-existing unrelated test failures

> **🟢 ARCHIVED 2026-08-07** — all 3 todos done: both P1 fixes landed same-day (`deployment-api@59f5cbe8`), and the
> deferred VM-classification re-ship landed independently (`deployment-api@e4072fb`) — fleet-wide quickmerge unblock
> confirmed.

## What I found

Ran `quality-gates.sh --no-fix` on a clean `deployment-api` tree (confirmed via `git stash` — same 2 failures with my
changes removed): `5228 passed, 2 failed`. quickmerge's own internal re-gate step treats this as a hard block regardless
of which files changed — **any commit to `deployment-api` right now fails to ship via quickmerge**, not just the one I
was trying to land.

- **`tests/unit/test_data_query_service_helpers.py::test_venue_to_category_cefi_match`** — `_venue_to_category("OKX")`
  returns `None`, expected `"CEFI"`. `BYBIT` and `binance-spot` (lowercase) both correctly map to CEFI; `OKX`
  specifically does not. Looks like a genuine gap in the venue→category mapping (`data_query_service.py`), not a test
  bug — but I did not investigate whether OKX is intentionally excluded or simply missing.
- **`tests/unit/test_route_data_status_distinct_values.py::TestGrainAwareCanonicalCompare::test_sports_market_token_instrument_types_are_accepted_exceptions_not_findings`**
  — asserts `len(SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES) == 30`, actual is `34`. The docstring cites
  `sports_instrument_type_market_token_ssot_gap_2026_07_28.md` and an operator ruling (2026-07-30) pinning the count
  at 30. Either the registry (`unified_api_contracts.registry`) grew by 4 entries since that ruling without the test
  being updated (a stale hardcoded count — likely the simple fix), or the growth itself is the bug. Did not investigate
  which.

## Why this wasn't fixed here

Both are unrelated to what I was shipping (a VM-classification registry entry for a newly-launched EC2 instance,
`deployment_api/routes/deployments_inventory/__init__.py`) and require real domain judgment (is OKX supposed to be CEFI?
is the 34-count growth intentional?) rather than a mechanical fix — out of scope for that task per the findings-triage
ladder ("ambiguous → diagnose both sides," not "fix blind").

## Todos

- [x] [DATA] P1. Investigate `_venue_to_category("OKX")` returning `None` — determine whether OKX should map to CEFI
      (add it to the mapping) or the test's expectation is wrong, then fix whichever is actually broken. Gate:
      `test_venue_to_category_cefi_match` passes for the right reason. — **Already fixed, no new work needed.**
      Confirmed via `unified-api-contracts`'s `VENUES_BY_ASSET_GROUP["cefi"]` (market_data_categories.py:361-370): bare
      `"OKX"` was **deliberately removed** (operator decision 2026-08-04, `unified-api-contracts@d67a226f`) — never MVP,
      2,475+ permanently-failing capture attempts; `OKX-SPOT`/`OKX-SWAP`/`OKX-FUTURES` are the real, actively-captured
      venues that cover every MVP OKX product and are each still present in the registry. So `_venue_to_category("OKX")`
      returning `None` is CORRECT current behavior, not a bug — the registry is right, the test's expectation was stale.
      The test itself was already corrected same-day in `deployment-api@59f5cbe8` (2026-08-04,
      `ikennaigboaka [slot-2·planning]`) to assert `OKX-SPOT -> "CEFI"` and `OKX -> None`; that commit is already on
      `live-defi-rollout` HEAD. Independently re-verified live: `.venv` import shows `'OKX' in VENUE_TO_ASSET_GROUP` is
      `False`, `VENUE_TO_ASSET_GROUP.get('OKX-SPOT')` is `'cefi'`. Evidence:
      `deployment-api@59f5cbe8bc831e3d02ab037019b1a7ff06fda31e` (already-landed fix, verified not new).
- [x] [DATA] P1. Investigate `SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES` growing from 30 to 34 —
      confirm whether this is intentional registry growth since the 2026-07-30 ruling (update the test's hardcoded
      count) or an unintended regression (fix the registry). Gate: the test passes for the right reason, and the
      2026-07-30 ruling doc is updated if the accepted count genuinely changed. — **Already fixed, no new work needed;
      registry has since grown further to 39 (not just 34), also already accounted for.** The growth is intentional,
      dated, and documented in the registry's own comments: the original 30 (2026-07-28/07-30 ruling,
      `sports_instrument_type_market_token_ssot_gap_2026_07_28.md`) grew +4 via `unified-api-contracts@161b0c0c`
      (2026-08-04 sports census) and +5 via `unified-api-contracts@cb545bef` (2026-08-04, folds the
      previously-separately-tracked lowercase `odds`/`exchange_odds`/`fixed_odds` + bare `ASIAN_HANDICAP`/`OVER_UNDER`
      residue into the accepted-exception set itself) = 39 total. The test's hardcoded count was already updated to
      match in the SAME `deployment-api@59f5cbe8` commit as the OKX fix above. Independently re-verified live: `.venv`
      import shows `len(SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES)     == 39`, matching the test's
      assertion exactly. The `sports_instrument_type_market_token_ssot_gap_2026_07_28.md` ruling doc is already ARCHIVED
      (2026-08-03) and its own historical narrative (documenting the 30→34 step, with its own commit evidence) remains
      accurate for its scope — the further 34→39 growth happened via later, separately-dated, already-cited commits
      after that doc's archival, so no edit to the archived doc is needed (it is a frozen historical record of the 30→34
      decision, not a living tracker of the registry's current size). Evidence:
      `deployment-api@59f5cbe8bc831e3d02ab037019b1a7ff06fda31e` (already-landed fix, verified not new). **Sports
      cross-reference note (added on retag, 2026-08-14):** this todo's fix operates on
      `SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES` — a `sports`-domain registry in
      `unified-api-contracts` — even though this doc's own `asset_group` is now `[ui]` (dominant owner: the
      `deployment-api` repo, both broken tests, and the re-ship target). See
      `sports_instrument_type_market_token_ssot_gap_2026_07_28.md` for the sports-side ruling the accepted count derives
      from.
- [x] ✅ [INFRA] P2. Once both above are fixed, re-attempt shipping
      `deployment_api/routes/deployments_inventory/__init__.py` + its test (the CI-escalation-runner VM classification
      fix, currently sitting locally uncommitted in this session's `.tabs/2/deployment-api` checkout) via quickmerge.
      Gate: `unified-trading-pm@<sha>`-style evidence citing the actual landed commit. — **NOT done, left open.** This
      session's checkout is `.tabs/4/deployment-api`, not the `.tabs/2/deployment-api` checkout referenced above — that
      other session's local uncommitted WIP is not accessible from here. Whoever owns (or next inherits) that checkout
      still needs to re-attempt the ship now that the block is confirmed cleared (see Progress Log below).

## Progress Log

- **2026-08-04**: Filed while working `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`'s deployment-ui
  visibility follow-through (operator asked why the new VM isn't visible anywhere; found + fixed the real classification
  gap, but landing it is blocked by this separate, pre-existing issue). Change is tested and correct
  (`test_build_aws_inventory_classifies_ci_escalation_runner_as_live` passes) but not yet shipped.
- **context-scout 2026-08-05**: populated context_scope (5 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **2026-08-06** (`.tabs/4/deployment-api` session): Investigated both P1 todos for real. Finding: **both were already
  fixed same-day** by `deployment-api@59f5cbe8bc831e3d02ab037019b1a7ff06fda31e` (2026-08-04,
  `ikennaigboaka [slot-2·planning]`, commit message explicitly cites this issue doc + "both P1 todos") — that fix is
  already an ancestor of current `live-defi-rollout` HEAD (`37d6f14`). The commit landed the code fix but this issue doc
  was never flipped (the Commit+Push+Flip "Half 2" was missed in that session). No new code changes were needed or made
  in `deployment-api` or `unified-api-contracts` this session — both repos pulled clean/up-to-date (`git status` clean,
  `git pull --ff-only` no-op). Verified fleet-wide-unblock directly: ran the exact re-gate command quickmerge uses
  (`bash scripts/quality-gates.sh --no-fix`) on a clean tree from scratch (deleted stale sentinels first) —
  **`5222 passed, 17 skipped, 0 failed` — "ALL QUALITY GATES PASSED"**, sentinel written at HEAD
  `37d6f143bf78c432e6c6b49313849057dfe873cf`. Also independently re-verified both assertions via direct `.venv` import
  (not just pytest): `VENUE_TO_ASSET_GROUP` has no `'OKX'` key (`OKX-SPOT`→`cefi` still present), and
  `len(SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES) == 39`. **deployment-api quickmerge is confirmed
  unblocked fleet-wide again** — no quickmerge invocation was performed since there was no code delta to ship in this
  repo. Todo 3 (re-ship the VM-classification fix) left open — that fix lives in a different session's
  `.tabs/2/deployment-api` local checkout, not reachable from this `.tabs/4` checkout. **Status stays `open`** (not all
  3 todos done) — flip to `resolved` once todo 3's owner re-ships and cites evidence.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — sole remaining todo scopes to re-shipping a DIFFERENT
  interactive session's (.tabs/2) uncommitted local WIP, structurally unreachable from an AO-dispatched worker under
  this workspace's per-slot-worktree isolation — an access/environment gate, not a judgment one.
- **na-eligibility-audit 2026-08-07 (cross-cutting tranche)**: KEEP-NA, stale items — closed the sole remaining todo:
  the CI-escalation-runner VM classification fix shipped independently as `deployment-api@e4072fb`, ancestor-verified on
  `origin/live-defi-rollout`. `git merge-base --is-ancestor e4072fb origin/live-defi-rollout` confirms. Test
  `test_build_aws_inventory_classifies_ci_escalation_runner_as_live` present in
  `deployment-api/tests/unit/test_route_deployments_inventory_aws.py`. All 3 todos now done — flagged ARCHIVE CANDIDATE
  in this audit's report (not archived here).
- **2026-08-14 (retag, `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md` Item A)**: retagged
  `asset_group: [cross-cutting]` → `[ui]` — dominant owner is the `deployment-api` repo (both broken tests plus the
  re-ship target all live there), per `ag_closeout_audit_cross_cutting_parked_2026_08_06.md`'s `[WORKER REC]` and
  `plan_reconciler_findings_cross_cutting_2026_08_10.md`'s Item A. Added a `sports` cross-reference note to todo 2 (its
  fix touches a sports-domain registry in `unified-api-contracts` even though the doc itself is now tagged `ui`).
