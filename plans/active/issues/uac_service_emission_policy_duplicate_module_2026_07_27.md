---
doc_type: issue
title:
  unified-api-contracts carries BOTH a flat service_emission_policy.py module AND a service_emission_policy/ package
  with the same public symbols
summary: >-
  Discovered incidentally while tracing MDPS's candle-manifest emission path (mdps_cefi_candle_manifest_never_emitted
  investigation, 2026-07-26): `unified_api_contracts/canonical/crosscutting/service_emission_policy.py` (34,693 bytes,
  last modified 2026-06-27) and `unified_api_contracts/canonical/crosscutting/service_emission_policy/` (a package with
  `__init__.py` + `_enums.py`/`_functions.py`/`_policies.py`, `_policies.py` last modified 2026-07-26 — actively being
  maintained) coexist in the same directory with overlapping symbols (`SERVICE_OUTPUT_POLICIES`, `get_emission_policy`,
  `ServiceEmissionPolicy`). Confirmed at runtime the PACKAGE wins Python's import resolution (verified via
  `service_emission_policy.__file__` resolving to the package's `__init__.py`), so this is NOT currently causing wrong
  behavior — but it is a real "two SSOT copies, one stale" hygiene violation, and the flat module being 34KB (clearly
  not a stub) suggests an in-progress, never-finished package-extraction migration rather than a deliberate design.
status: open
nature: issue
asset_group: [meta]
stage: [data]
repos: [unified-api-contracts]
scope: [engineer]
tags: [uac, dead-code, duplicate-module, service-emission-policy, hygiene]
related: [/plans/archive/issues/mdps_cefi_candle_manifest_never_emitted_2026_07_26.md]
created: 2026-07-27
priority: P3
parent_epic: infrastructure_master
source: >-
  slot-12, data_engineering, found while tracing unified_api_contracts.canonical.crosscutting.service_emission_policy
  import resolution during mdps_cefi_candle_manifest_never_emitted_2026_07_26's root-cause investigation.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# UAC service_emission_policy: duplicate flat-module + package

## What I found

Both exist simultaneously in `unified_api_contracts/canonical/crosscutting/`:

- `service_emission_policy.py` — 34,693 bytes, mtime 2026-06-27
- `service_emission_policy/` (package) — `__init__.py`, `_enums.py`, `_functions.py`, `_policies.py` (22,305 bytes,
  mtime **2026-07-26**, i.e. edited MORE RECENTLY than the flat module)

Both define `SERVICE_OUTPUT_POLICIES`, `get_emission_policy`, `ServiceEmissionPolicy` — the same public surface.
Verified at runtime
(`python3 -c "from unified_api_contracts.canonical.crosscutting import service_emission_policy as sep; print(sep.__file__)"`)
that Python resolves to the PACKAGE's `__init__.py`, and the package's `SERVICE_OUTPUT_POLICIES` returns the correct,
expected policy values (e.g. `("market-data-processing-service", "ohlcv_1m:historical")` → `partial_ok`, matching what
the live manifest data confirms actually happens). So the flat module is currently DEAD — shadowed, never imported — not
a live bug, but real tech debt: whoever is actively maintaining the package's `_policies.py` (edited 2026-07-26, same
day as this discovery) may not realize the old flat module still exists and could diverge silently if anyone ever
imports from it directly by a different path, or if the package is ever removed without also removing the flat file.

## Why it matters

- Low urgency (confirmed non-live, package correctly wins resolution) but a genuine "two SSOT copies" smell the
  workspace's own conventions warn against. Whoever finishes the package migration should delete the flat module in the
  same change, not leave it as silent dead weight.

## Recommended fix path

- [ ] [CLEANUP] P3. **Delete the orphaned flat `unified_api_contracts/canonical/crosscutting/service_emission_policy.py`
      module once confirmed dead**, after a corpus-wide grep confirms no import resolves specifically to the flat-file
      shape in a way the package wouldn't also satisfy (Python's normal package-over-module resolution should already
      guarantee this, but confirm no `importlib`/`sys.path` trick bypasses it anywhere). Repo: unified-api-contracts.
      **Done when**: the flat module is deleted, `quality-gates.sh` green, and no import errors surface anywhere in the
      fleet's CI.
