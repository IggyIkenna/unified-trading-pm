---
doc_type: issue
title:
  deployment-api — test_cefi_venue_axis_keeps_exact_compare fails on HEAD (OKX-FUTURES badges is_canonical=True, test
  expects False)
summary: >-
  Discovered while running deployment-api's full quality-gates.sh for an unrelated coverage-drift-worker change
  (features_sports_deployment_ui_coverage_tab_and_registry_playbook_2026_07_21.md todo 3). Confirmed pre-existing (fails
  identically with my diff stashed out) — not caused by this session's work. UAC registers OKX-FUTURES as a real
  adapter-keyed cefi venue (unified_api_contracts/registry/venue_adapter_keys.py:93), so it is plausible the canonical
  set the distinct-values endpoint compares against legitimately grew to include it and the test is simply stale — but
  this wasn't verified deeply enough to be sure it isn't a real regression in canonical-set derivation. Needs someone
  with venue-canonicalization context to determine which side is wrong and fix it.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [deployment-api, data-status, distinct-values, canonical-compare, test-regression, cefi, venue]
related: []
created: "2026-07-21"
parent_epic: infrastructure_master
priority: P3
assigned_vm: NA
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [features_sports_deployment_ui_coverage_tab_and_registry_playbook_2026_07_21-003]
resolved_by:
locked_by:
depends_on: []
---

# What I found

`deployment-api`'s full `quality-gates.sh` is RED on current `live-defi-rollout` HEAD:

```
FAILED tests/unit/test_route_data_status_distinct_values.py::TestGrainAwareCanonicalCompare::test_cefi_venue_axis_keeps_exact_compare
assert badge["OKX-FUTURES"] is False
E   assert True is False
```

Confirmed pre-existing and unrelated to my diff: reran the single test with my in-progress changes
(`coverage_drift_worker.py`

- its route + tests) `git stash`-ed away — identical failure. Not introduced by
  `features_sports_deployment_ui_coverage_tab_and_registry_playbook_2026_07_21.md` todo 3.

The test (`tests/unit/test_route_data_status_distinct_values.py:298`) asserts `OKX-FUTURES` badges `is_canonical=False`
for the `cefi` asset_group axis via `enumerate_distinct_values()`
(`deployment_api/routes/data_status/_distinct_values.py`). The three most recent commits touching that file are all
canonical-vs-grain fixes (`ea56fff`, `96499dd`, `0d2f6e6`) — this looks like fallout from that work, one way or the
other.

`OKX-FUTURES` IS a real, registered cefi venue in UAC (`unified_api_contracts/registry/venue_adapter_keys.py:93`,
`data_type_capability.py`, `venue_mapping.py`) — so it's plausible the canonical set `enumerate_distinct_values`
compares against legitimately grew to include it (making the TEST stale, not the code), but I did not trace far enough
to rule out the alternative (a real regression in how the canonical set is derived/scoped for the cefi venue axis
specifically, as opposed to the full adapter-key registry).

# Why it matters

`quality-gates.sh` on `deployment-api` is currently RED at HEAD for anyone who runs the full suite (not just a
partial/unit subset) — every subsequent committer sees this same pre-existing failure and has to independently re-verify
it isn't theirs, same class of interruption already logged in this session for the `c8f96e6` regression issue doc.

# Recommended decision

- [x] ✅ [SCRIPT] P3. Determine whether `OKX-FUTURES` legitimately belongs in the cefi canonical-venue set
      `enumerate_distinct_values` compares against (in which case fix the test's expectation) or whether the
      canonical-set derivation regressed for the venue axis specifically (in which case fix
      `deployment_api/routes/data_status/_distinct_values.py`) — trace back through `ea56fff`/`96499dd`/`0d2f6e6` to
      find which changed the comparison grain most recently, then correct whichever side is wrong. (repo:
      deployment-api) — deployment-api@fe8eaf1. **Verdict: the test was stale, not the code.** UAC's
      `VENUES_BY_ASSET_GROUP["cefi"]` (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`)
      already documents the root cause in-line: `OKX-FUTURES`/`OKX-SWAP` were added 2026-07-21 as real,
      actively-captured cefi venues (119,706 + 423,313 captured manifest rows respectively) that had been wholly absent
      from the list — that same comment explicitly names `_distinct_values.py::_canonical_set()` as the consumer that
      was badging them a false-positive drift alarm before the fix. Confirmed via the sibling editable UAC import
      (`.venv/bin/python -c "... VENUES_BY_ASSET_GROUP['cefi']"` → `OKX-FUTURES` is a member) that
      `enumerate_distinct_values` now correctly reports `is_canonical=True` for `OKX-FUTURES` — no regression in
      `_distinct_values.py`, `ea56fff`/`96499dd`/`0d2f6e6` are unrelated canonical-vs-grain fixes to a different code
      path. Fixed `tests/unit/test_route_data_status_distinct_values.py::test_cefi_venue_axis_keeps_exact_compare`:
      `OKX-FUTURES` now asserts `True` (matches the corrected canonical set) and a genuinely non-canonical value
      (`OKX-MARGIN`, not registered under any name) replaces it as the exact-compare negative case so the test still
      proves the comparison isn't loosened. All 12 tests in the file pass; `quality-gates.sh` green.
