---
doc_type: issue
title:
  "instruments-service invariant tests red vs UAC AAVE-oracle venue registration (lst_rate_honest_coverage Phase 1)"
summary: >-
  UAC commit 6bdbc31d (2026-07-21, `lst_rate_honest_coverage_2026_07_21.md` Phase 1) registered a new `AAVE-ETHEREUM:
  aave_oracle` entry in `VENUE_TO_ADAPTER_KEY`, but instruments-service's own `factory._ADAPTERS` has no matching
  `aave_oracle` class yet (the IS-side adapter is the plan's own next todo, tracked as "BUILT-BUT-NOT-SHIPPED" in that
  plan's Progress Log, blocked there on a separate gate issue). 4 instruments-service invariant/e2e tests fail
  deterministically as a result. Discovered as a side-effect while shipping an unrelated, already-tested DeFi
  POOL-adapter change (`defi_consolidated_closeout_2026_07_18.md` Track 1, "eliminate the address/UUID fallback"
  sub-items 2+4) — confirmed via a `git stash` baseline (byte-identical 4 failures with the unrelated diff fully
  removed) that this is 100% pre-existing and unrelated to that change.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [defi, aave-oracle, test-drift, cross-repo, lst-rate]
related: [lst_rate_honest_coverage_2026_07_21.md, instruments_service_deribit_combo_purge_test_drift_2026_07_21.md]
created: 2026-07-21
assigned_vm: planning
source: [discovered while shipping defi_consolidated_closeout_2026_07_18.md Track 1 sub-items 2+4, slot-4]
execution_scope: orchestrator-agent
priority: P1
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
parent_epic: defi_master
resolved_by: slot-9 (2026-07-21) — instruments-service@fd0d12a9, both todos shipped, 4760 passed / 0 failed
---

## What I found

While shipping an unrelated, fully-tested instruments-service DeFi change (wiring the shared UTL token-metadata resolver
into `balancer.py`/`orca.py`/`raydium.py` POOL adapters — `defi_consolidated_closeout_2026_07_18.md` Track 1), a full
local `quality-gates.sh --no-fix` run surfaced **4 deterministic test failures** unrelated to that change:

```
FAILED tests/unit/test_adapter_routing_uac_invariant.py::TestAdapterRoutingUACInvariant::test_every_uac_adapter_key_resolves_to_a_class
FAILED tests/unit/test_factory_comprehensive.py::TestCanonicalVenueMapping::test_adapter_data_sources_covers_all_adapters
FAILED tests/unit/test_orchestrator_helpers.py::TestVenueProducerUACInvariant::test_defi_set_equals_uac_denominator_drift_guard
FAILED tests/unit/test_pipeline_e2e_prediction.py::test_rule11_per_ag_dedup_target_counts_byte_unchanged
```

Root cause: `unified-api-contracts` commit `6bdbc31d` ("feat(defi): register the AAVE oracle venue + verified LST
Chainlink feeds (Phase 1 denominator)", 2026-07-21 18:11:48+0000) added `AAVE-ETHEREUM: aave_oracle` to
`VENUE_TO_ADAPTER_KEY` (per `lst_rate_honest_coverage_2026_07_21.md` Phase 1 — the AAVE oracle `getAssetPrice` RPC
plumbing). instruments-service depends on UAC via an unpinned, editable path dependency
(`unified-api-contracts>=0.33.0,<1.0.0`, `path = "../unified-api-contracts"`), so this slot's clone picked up the new
registry (via the routine FF-pull sync) without the matching `factory._ADAPTERS["aave_oracle"]` class existing yet.
Exact assertion evidence:

```
AssertionError: UAC VENUE_TO_ADAPTER_KEY entries with no adapter CLASS in factory._ADAPTERS: {'AAVE-ETHEREUM': 'aave_oracle'}.
AssertionError: adapter_keys missing from ADAPTER_DATA_SOURCES (not in known_gaps): ['aave_oracle']
AssertionError: DeFi venue producer diverges from the UAC defi denominator (must stay == the IS-producible set P after @6bcff215).
AssertionError: DEFI dedup'd target count drifted: 99 != 98
```

**Confirmed pre-existing, not caused by my diff**: reproduced byte-identical on a `git stash`'d clean tree (my 5 changed
files fully removed) at instruments-service HEAD `57530015a` — same 4 failures, same messages, `4756 passed, 7 skipped`
(vs `4765 passed, 8 skipped` with my diff applied — the delta is exactly my new tests, nothing else moved).

**This repo's own quality-gates.sh was FULLY GREEN immediately prior to this**: HEAD
`35d9e7074088809a3b3011b014178b0cb17466d2` is the exact commit
`instruments_service_deribit_combo_purge_test_drift_2026_07_21.md`'s last todo verified `✅ ALL QUALITY GATES PASSED`,
sentinel matching HEAD, zero failures. The 4 failures above appeared strictly AFTER that commit, once UAC's
`aave_oracle` registration (a separate, unrelated commit) was pulled in — this is a fresh instance of the exact same
drift class that older issue already closed out once (UAC ships a venue registration; instruments- service hasn't caught
up yet), not a regression of anything in this repo.

## Why it matters

- Blocks any further instruments-service `quickmerge --agent` shipping (the agent fast-path requires a genuinely green
  `quality-gates.sh` sentinel matching HEAD; there is no legitimate bypass for a hard invariant test — see
  `test_adapter_routing_uac_invariant.py`'s own docstring: "the ship gate for that split... a silent KeyError between
  the two tables is impossible while this suite is green"). `test_factory_comprehensive.py`'s failure DOES have a
  `known_gaps` escape-hatch set (used previously for `eigenlayer`/`ethfi_governance`), but the other 3 do not — this is
  a deliberate, no-bypass ship gate by design, not an oversight.
- The fix is already the `lst_rate_honest_coverage_2026_07_21.md` plan's own explicit next todo ("[IS] P1. AaveOracle
  reference-data adapter — `adapters/defi/aave_oracle.py` ... register `aave_oracle` in `factory._ADAPTERS` + add
  `AAVE-ETHEREUM` to `orchestrator/defi.py`"), and that plan's Progress Log states the IS-side files were "BUILT-BUT-
  NOT-SHIPPED" (blocked at time of writing on the now-resolved DERIBIT-COMBO gate above) — i.e. an active, owned,
  in-flight track, not an orphaned gap. Searched this slot's instruments-service clone (working tree, all branches, all
  stashes) for `aave_oracle.py` / any related commit: **not present here** — the built-but-unshipped artifact lives in a
  different slot/session's checkout, not this one.
- I did NOT build the `aave_oracle` adapter myself: doing so would duplicate/collide with the already-in-flight,
  plan-owned implementation (real Chainlink/Aave `getAssetPrice` RPC wiring requires the verified reserve addresses the
  plan's own Phase-0 reality-verification already pinned — reproducing that from scratch here risks a second, divergent,
  possibly-wrong implementation landing on top of the real one).

## Recommended decision

Whoever resumes `lst_rate_honest_coverage_2026_07_21.md` (its own "RESUME POINT (pre-compact)" section names this as the
immediate next executable step) should finish + ship the `aave_oracle.py` adapter + `factory._ADAPTERS`/
`orchestrator/defi.py` registration exactly as that plan already specifies; this issue's todos below are that same work
viewed from the instruments-service test-drift angle, not new scope. Once shipped, re-run this repo's `quality-gates.sh`
to confirm all 4 tests above go green (no golden/count updates are anticipated beyond what a correct adapter
registration naturally produces — the `known_gaps`/dedup-count deltas will self-resolve once `aave_oracle` has a real
class + data source).

## Todos

- [x] ✅ [BACKEND] P1. Build/finish + ship `instruments_service/reference_data/adapters/defi/aave_oracle.py` (clone
      `chainlink.py`'s shape per the plan's own guidance; venue `AAVE-ETHEREUM`; enumerate the Phase-0-verified 6
      reserves as `spot_asset`), register `"aave_oracle"` in `factory._ADAPTERS` + `ADAPTER_DATA_SOURCES`, and add
      `AAVE-ETHEREUM` to `orchestrator/defi.py`'s `_STATIC_DEFI_VENUES`. (repo: instruments-service — this is
      `lst_rate_honest_coverage_2026_07_21.md`'s own Phase-1 IS todo; do not duplicate that plan's todo list, just close
      both from the one ship.) — instruments-service@fd0d12a9. All 6 Phase-0-verified reserves
      (wstETH/weETH/rETH/cbETH/rsETH/ezETH) enumerated as SPOT_ASSET under AAVE-ETHEREUM, symbol lower-cased per spec,
      conservative available_from floor (max of AAVE V3 launch + each reserve's own protocol launch).
- [x] ✅ [BACKEND] P2. Once shipped, confirm `test_pipeline_e2e_prediction.py`'s DEFI dedup target count (currently
      hard-coded `98`, observed `99` post-registration) reflects the new, correct steady-state venue count — update the
      magic number only after confirming it's the intended count, not a further symptom of drift (same caution as the
      sibling DERIBIT-COMBO issue's todo 3). (repo: instruments-service) — instruments-service@fd0d12a9. Confirmed 99 is
      exactly +1 (one new static venue registered, dedup is per (asset_group, venue)) — not further drift. QG-verified:
      4760 passed, 0 failed (all 4 originally-red invariant tests now green).

## Codex SSOTs

- `codex/08-workflows/ci-cd-flow.md` § "Local ↔ CI QG parity matrix" (the same tracked local-ahead-of-CI divergence
  class this issue class always falls into).
- `codex/02-data/lst-exchange-rate-surfaces.md` (the four LST exchange-rate surfaces, canonical homes, honest-coverage
  contract that `lst_rate_honest_coverage_2026_07_21.md` implements).
