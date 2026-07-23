---
doc_type: issue
title: capability verdict matrix now emits 60 archetypes but 3 tests still hardcode 59 — QG RED on live-defi-rollout
summary: >-
  test_capability_verdict_matrix.py::test_all_57_archetypes_are_blocks,
  ::test_f48_engineless_archetypes_are_not_registered, and test_prospectus_generators.py::test_audit_57_archetypes all
  assert an archetype count of 59 (despite the "57" in their names — already stale from an earlier bump), but
  `build_matrix()`'s archetype source (unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype) now
  yields 60 distinct archetypes. This reds unified-trading-pm's quality-gates.sh on live-defi-rollout for every worker
  trying to ship, independent of what they are shipping.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts]
scope: [engineer]
tags: [quality-gates, qg-red, archetype, capability-verdict-matrix, uac, strategy-archetype, test-drift]
related: []
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: backend_engineer
drift_direction: advance-code
source:
  [
    slot-9,
    2026-07-21,
    discovered while shipping an unrelated notify-slack.yml fix — quality-gates.sh went RED on a fresh rebase with no
    changes of mine touching capability/archetype code,
  ]
resolved_by:
  unified-trading-pm@a85f00a93 (2026-07-21, a peer slot shipped the identical fix — 60th archetype is
  ARBITRAGE_SPORTS_DUTCHING, a real strategy-service-registered engine per
  sports_arb_dutching_engine_not_wired_to_factory_2026_07_21.md, added to _FIXTURE_ENGINE_BACKED, not a bare count
  bump); slot-9 independently arrived at the equivalent fix (commit 191f0d409, superseded/discarded — nothing unique to
  preserve) and confirmed quality-gates.sh green on the peer's shipped version (1318 passed, 0 failed)
locked_by:
locked_since:
depends_on: []
---

# capability verdict matrix archetype count regressed from a test's POV — 60 vs the hardcoded 59

## What I found

While shipping an unrelated single-file fix (`.github/workflows/notify-slack.yml`) via the standard `quality-gates.sh` →
`quickmerge --agent` flow, a fresh `git pull --rebase --autostash origin live-defi-rollout` picked up new commits from
the fleet, and the very next full `quality-gates.sh` run went RED — reproduced identically across two consecutive
rebase-to-latest-tip runs (HEAD `cb733da14` then `363e8a7cc`), confirming this is NOT a transient race, it is a real
regression sitting on `live-defi-rollout`:

```
FAILED tests/unit/test_capability_verdict_matrix.py::test_all_57_archetypes_are_blocks
  assert len(archetypes) == 59
  AssertionError: assert 60 == 59
FAILED tests/unit/test_capability_verdict_matrix.py::test_f48_engineless_archetypes_are_not_registered
  assert all(a.startswith(("VOL_", "MARKET_MAKING")) for a in engineless)
  AssertionError: assert False
FAILED tests/unit/test_prospectus_generators.py::test_audit_57_archetypes
  assert result["total_archetype_ids"] == 59
  AssertionError: Expected 59 archetypes but got 60. Update the plan if new archetypes were added (see F9 in findings tracker).
```

`build_matrix()` (in `scripts/openapi/generate_capability_verdict_matrix.py`) derives its archetype universe from
`unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype` (a UAC enum), NOT from a PM-local list. UAC is
pinned at `0.71.0` in `workspace-manifest.json` on this HEAD. Something (a UAC enum addition, landed in 0.71.0/0.72.0,
or a dependency resolution picking up a newer UAC than the pinned display version) grew `StrategyArchetype` from 59 to
60 members, and the three PM-side tests pinning the OLD count (`59` — their own names still say "57", so this constant
has drifted at least twice without a rename) were never updated to match.

The new `test_f48_engineless_archetypes_are_not_registered` failure additionally suggests the 60th archetype does NOT
start with `VOL_` or `MARKET_MAKING` — i.e. it may be a new engine-backed or otherwise-prefixed archetype that also
needs its OWN capability-matrix classification decided (available/blocked/not_registered), not just a count bump.

## Why it matters

- **Blocks the WHOLE fleet from shipping to `unified-trading-pm`**: `quality-gates.sh` is the mandatory Pass-1 gate
  before `quickmerge --agent` will push anything to `live-defi-rollout`. While this test is RED, no worker — regardless
  of what they are actually changing — can get a passing sentinel. Confirmed unrelated to my own change (single GH
  Actions YAML file, zero overlap with capability/archetype code), and confirmed reproducible on a clean rebase.
- **Silent-scope risk**: if the fix is "just bump 59→60" without first confirming WHAT the 60th archetype is and whether
  it deserves an explicit block/available verdict, the fix could paper over a real capability-registration gap (the same
  class of bug F47/F48 in `d0f66d732`/`362f90404` were fixing).

## Recommended decision

1. Identify the 60th `StrategyArchetype` member (diff
   `unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype` between the previously-pinned UAC version
   and `0.71.0`/current resolved version).
2. Decide its capability-matrix verdict (available / blocked / not_registered) per the existing F47/F48 classification
   rules in `generate_capability_verdict_matrix.py`, not just a blanket "blocked".
3. Update the three hardcoded counts (and the two stale "57"-named tests, while touching them, to "59"/"60" or drop the
   number from the name entirely to stop this recurring) in `tests/unit/test_capability_verdict_matrix.py` and
   `tests/unit/test_prospectus_generators.py` to match the corrected, deliberate classification.
4. Re-run `bash scripts/quality-gates.sh` full to confirm green, then ship via `quickmerge --agent`.

- [x] ✅ [BACKEND] P1. Identify the 60th StrategyArchetype member and its correct capability-matrix verdict; update the
      3 hardcoded archetype-count assertions in `tests/unit/test_capability_verdict_matrix.py` +
      `tests/unit/test_prospectus_generators.py` to match; confirm `quality-gates.sh` green; ship via quickmerge. (repo:
      unified-trading-pm) — unified-trading-pm@a85f00a93. The 60th archetype is `ARBITRAGE_SPORTS_DUTCHING`
      (unified-api-contracts@cf28a962, `SportsArbDutchingEngine` given its own enum value instead of silently colliding
      with `ARBITRAGE_PRICE_DISPERSION`) — real, engine-backed, added to `_FIXTURE_ENGINE_BACKED` (not a blanket block).
      All 3 assertions bumped 59→60; both stale `*_57_*`-named test functions renamed to drop the magic number entirely.
      `quality-gates.sh`: 1318 passed, 0 failed.

## Codex SSOTs

- N/A — no existing codex SSOT names this specific test-drift class;
  `plans/active/capability_wizard_and_manifest_2026_06_11.md` Phase 6A is the owning plan for the verdict-matrix
  generator itself.
