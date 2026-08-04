---
doc_type: issue
title: deployment-api quickmerge blocked fleet-wide by 2 pre-existing, unrelated test failures
summary: >-
  Discovered while shipping an unrelated fix (register the new CI-escalation-runner VM's classification prefix):
  quickmerge's re-gate step fails on the current deployment-api tree due to 2 pre-existing, unrelated test failures —
  not caused by the classification change (confirmed via git stash — both fail identically on the clean tree). This
  blocks ANY commit to deployment-api via quickmerge right now, not just this one.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: [quickmerge, test-failure, deployment-api, blocking]
related: [/plans/active/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md]
created: 2026-08-04
priority: P1
parent_epic: infrastructure_master
source: "interactive session, 2026-08-04 — discovered shipping a VM-classification fix, not this issue's own scope"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
---

# deployment-api quickmerge blocked by 2 pre-existing unrelated test failures

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

- [ ] [DATA] P1. Investigate `_venue_to_category("OKX")` returning `None` — determine whether OKX should map to CEFI
      (add it to the mapping) or the test's expectation is wrong, then fix whichever is actually broken. Gate:
      `test_venue_to_category_cefi_match` passes for the right reason.
- [ ] [DATA] P1. Investigate `SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES` growing from 30 to 34 —
      confirm whether this is intentional registry growth since the 2026-07-30 ruling (update the test's hardcoded
      count) or an unintended regression (fix the registry). Gate: the test passes for the right reason, and the
      2026-07-30 ruling doc is updated if the accepted count genuinely changed.
- [ ] [INFRA] P2. Once both above are fixed, re-attempt shipping
      `deployment_api/routes/deployments_inventory/__init__.py` + its test (the CI-escalation-runner VM classification
      fix, currently sitting locally uncommitted in this session's `.tabs/2/deployment-api` checkout) via quickmerge.
      Gate: `unified-trading-pm@<sha>`-style evidence citing the actual landed commit.

## Progress Log

- **2026-08-04**: Filed while working `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`'s deployment-ui
  visibility follow-through (operator asked why the new VM isn't visible anywhere; found + fixed the real classification
  gap, but landing it is blocked by this separate, pre-existing issue). Change is tested and correct
  (`test_build_aws_inventory_classifies_ci_escalation_runner_as_live` passes) but not yet shipped.
