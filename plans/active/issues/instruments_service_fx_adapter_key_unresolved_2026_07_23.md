---
doc_type: issue
title: >-
  instruments-service quickmerge fully blocked -- UAC 0.72.0's new VENUE_TO_ADAPTER_KEY["FX"] has no adapter class in
  factory._ADAPTERS
summary: >-
  A same-day dependency re-pin (`unified-api-contracts@0.72.0`, commit 6546a147, "major/breaking floor") added a new
  venue key `FX: "fx"` to `VENUE_TO_ADAPTER_KEY`, but `instruments_service/reference_data/factory.py`'s `_ADAPTERS`
  registry has no corresponding class. This fails 4 tests unconditionally for ANY commit on the current tree
  (`test_adapter_routing_uac_invariant.py::test_every_uac_adapter_key_resolves_to_a_class`,
  `test_factory_comprehensive.py::TestCanonicalVenueMapping::test_adapter_data_sources_covers_all_adapters`, and 2 in
  `test_silent_absent_fixes.py::TestZeroRecordsNoAdapterYetVenueDoesNotCrash`), which blocks `quickmerge.sh`'s Re-gate
  step for every instruments-service ship attempt, not just the one that surfaced it. Confirmed unrelated to the CeFi
  catalogue-enumeration-gap script this was discovered while shipping (a brand-new, isolated file) -- reproduced the
  same 4 failures on a re-run with no code changes present.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [quickmerge-blocker, tradfi, fx, adapter-registry, dependency-bump, cross-repo]
related: []
created: "2026-07-23"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source:
  [
    "surfaced 2026-07-23 while shipping instruments-service scripts/measure_cefi_catalogue_enumeration_gap_2026_07_23.py
    via quickmerge --agent -- Re-gate failed on the full suite, isolated to 4 pre-existing adapter-registry-invariant
    tests unrelated to the shipped diff",
  ]
resolved_by: "instruments-service@f9be7ec7 (FxReferenceDataAdapter, concurrent sibling session)"
locked_by:
---

## RESOLVED — 2026-07-23 ~17:20Z

A concurrent sibling session shipped `instruments-service@f9be7ec7` ("feat(tradfi): add FxReferenceDataAdapter -- static
FX_SPOT_PAIRS-derived instrument-list adapter, no vendor call. Registers venue key 'fx' in factory.py, ...")
independently of this issue doc. Confirmed the fix: rebased my own blocked commit
(`scripts/measure_cefi_catalogue_enumeration_gap_2026_07_23.py`) onto the new origin HEAD, re-ran the 2 previously-
failing invariant tests directly (`test_every_uac_adapter_key_resolves_to_a_class`,
`test_adapter_data_sources_covers_all_adapters`) -- both pass now -- then ran the full quickmerge Re-gate, which passed
clean. Landed at `instruments-service@f6f16785`. No further action needed.

# instruments-service Re-gate blocked: UAC's new `FX` venue key has no adapter class

## Reproduction

```
cd instruments-service
.venv/bin/pytest tests/unit/test_adapter_routing_uac_invariant.py::TestAdapterRoutingUACInvariant::test_every_uac_adapter_key_resolves_to_a_class -q
```

```
AssertionError: UAC VENUE_TO_ADAPTER_KEY entries with no adapter CLASS in factory._ADAPTERS: {'FX': 'fx'}. Add the
class to _ADAPTERS or fix the key in UAC.
```

Reproduced twice (two separate quickmerge attempts, ~5 min apart), same 4 failures both times, zero relation to the diff
being shipped in either attempt:

- `test_adapter_routing_uac_invariant.py::TestAdapterRoutingUACInvariant::test_every_uac_adapter_key_resolves_to_a_class`
- `test_factory_comprehensive.py::TestCanonicalVenueMapping::test_adapter_data_sources_covers_all_adapters`
- `test_silent_absent_fixes.py::TestZeroRecordsNoAdapterYetVenueDoesNotCrash::test_sole_no_adapter_yet_venue_returns_zero_counts_cleanly`
- `test_silent_absent_fixes.py::TestZeroRecordsNoAdapterYetVenueDoesNotCrash::test_no_adapter_yet_venue_mixed_with_real_tradfi_venue_excluded_from_calendar_check`

## Root cause

`git log` on instruments-service's `live-defi-rollout` shows, immediately before these failures started:

```
5ea5ee93 chore(deps): re-pin unified-trading-library to 0.56.0 (major/breaking floor)
6546a147 chore(deps): re-pin unified-api-contracts to 0.72.0 (major/breaking floor)
```

`unified-api-contracts@0.72.0` added `FX` to `VENUE_TO_ADAPTER_KEY` (a "major/breaking floor" bump — an intentional
breaking change per this workspace's semver-agent convention, not an accident).
`instruments_service/reference_data/ factory.py`'s `_ADAPTERS` dict has not been updated to add a class for
`adapter_key="fx"`, so the invariant test that asserts every non-`NO_ADAPTER_YET` UAC key resolves to a registered class
fails. The other 3 failures are downstream of the same gap (factory venue-coverage check, and the "no-adapter-yet venue
doesn't crash" tests presumably now hitting a genuinely-unhandled key instead of the expected sentinel path).

## Impact

**Blocks `quickmerge.sh`'s Re-gate step for EVERY instruments-service commit right now** — same class of blocker as the
earlier-tonight `mtds_rule11_defi_shard_count_stale_baseline_2026_07_22.md` (a real-but-unrelated test failure prevents
the QG sentinel from ever refreshing, regardless of the actual diff being shipped). My own
`scripts/measure_cefi_catalogue_enumeration_gap_2026_07_23.py` is fully committed, verified, and safely backed up
(`backup-catalogue-gap-script-2026-07-23` branch, sha `bc53bafe`) but cannot land via quickmerge until this clears.

## Fix

Either: (a) add an `"fx": FxAdapter` (or similar) entry to `factory.py`'s `_ADAPTERS`, backed by a real or stub FX
reference-data adapter, matching whatever `FX` is meant to represent in the new UAC registry (likely a TradFi
foreign-exchange asset class — check `unified-api-contracts`'s own changelog/PR for `0.72.0` for what `FX` is supposed
to resolve to before building the class); or (b) if `FX` was added to UAC prematurely / by mistake, fix it at the source
(UAC) to use `NO_ADAPTER_YET` until instruments-service is ready. This is TradFi-domain work, out of scope for the CeFi
session that found it — filing rather than fixing blind.

## Status of the work this was blocking

Not urgent to unblock immediately — `scripts/measure_cefi_catalogue_enumeration_gap_2026_07_23.py` is a new, isolated,
already-adversarially-verified read-only measurement script with zero relation to this failure. It will land as soon as
this clears (re-attempt quickmerge, no further action needed on the script itself).
