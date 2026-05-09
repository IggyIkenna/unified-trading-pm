---
title: "✅ RESOLVED 2026-05-09 — UAC + UTL QG blockers cleared (was: blocked by foreign breakage 2026-05-08 PM)"
created: 2026-05-08
resolved: 2026-05-09
author: tab2-live-pipeline
status: resolved
source:
  - unified-api-contracts/unified_api_contracts/registry/capability_declarations/__init__.py:17,75
  - unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py
  - unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/thresholds.py:60
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

## ✅ RESOLUTION 2026-05-09

Both blockers verified cleared on origin per cluster 9 retry audit 2026-05-09:
- `ORACLE_COVERAGE_START` no longer referenced in `__init__.py`; UAC import succeeds.
- EN DASH at `thresholds.py:60` — fixed in same UAC sweep.

UAC + UTL QG runs collect cleanly. Issue ready for archive.

---

# Original issue (resolved — kept for archaeology)


# UAC + UTL QG blocked by foreign breakage as of 2026-05-08 PM

> **Severity**: P1 — full UAC + UTL test suites cannot collect; blocks any agent running
> `bash scripts/quality-gates.sh` in either repo. **Blast radius**: every consumer that
> imports from UAC at module-load time (UTL, MTDS, MDPS, features-\*, instruments-service,
> deployment-api, etc.). **Suggested owner**: Tab 1 (DeFi launch + UAC drift fixes —
> `_defi.py` is in their workstream).

## What I found

Two independent QG failures, both on code that this Tab 2 session did NOT touch.

### Failure 1 — UAC lint RUF001

```
RUF001 String contains ambiguous `–` (EN DASH). Did you mean `-` (HYPHEN-MINUS)?
  --> unified_api_contracts/canonical/crosscutting/alerting/thresholds.py:60:21
```

Trivial — replace the EN DASH with HYPHEN-MINUS or word "to". One-line fix.

### Failure 2 — UAC import-level breakage of `_defi.py` ↔ `__init__.py`

`unified_api_contracts/registry/capability_declarations/__init__.py:17` re-exports
`ORACLE_COVERAGE_START` from `._defi`, and lists it on line 75 in `__all__`. But the
symbol does NOT exist in `_defi.py` (verified via
`grep -n "ORACLE_COVERAGE_START" unified_api_contracts/registry/capability_declarations/_defi.py`
returns 0 hits).

This breaks at import time — the entire `unified_api_contracts.registry` package fails
to load:

```
ImportError: cannot import name 'ORACLE_COVERAGE_START' from
'unified_api_contracts.registry.capability_declarations._defi'
```

Cascade: pytest's `unified_api_contracts.testing.network_block_plugin` is auto-discovered
on test-collection across UAC + UTL + every downstream consumer that has UAC as a path
dep. The plugin imports `unified_api_contracts.registry` transitively → import error
→ pytest cannot collect → QG step `[3/6] TESTS` fails before running anything.

Verified via:

- `cd unified-api-contracts && bash scripts/quality-gates.sh` → step `[2/6] LINT` fails
  (RUF001) before step 3.
- `cd unified-trading-library && bash scripts/quality-gates.sh` → step `[3/6] TESTS`
  fails on conftest import via UAC chain.
- `cd unified-api-contracts && python -m pytest tests/unit/test_pipeline_mode.py` →
  same import error from network_block_plugin.

## Why it matters

- **Every Tab pushing Python today is pushing without QG validation**, because QG cannot
  complete on UAC or any UAC-consumer repo until the symbol is restored.
- The 2026-05-08 Tab 2 work shipped today (UAC@8bc3f2a PipelineMode, UAC@b643c9a Phase 1
  streaming events, UTL@f24e651b Phase 2A+2C, UTL@8c67df5d Phase 2B,
  UTL@87134364 manifest_writer pipeline_mode kwarg) all passed targeted tests
  pre-commit but were committed before this `__init__.py` ↔ `_defi.py` divergence
  surfaced as a QG blocker. None of those commits introduced the breakage; the
  divergence is on origin/live-defi-rollout already.

## Recommended decision

1. **Tab 1 (DeFi launch / UAC drift fixes) restores `ORACLE_COVERAGE_START` in
   `_defi.py`** — it was likely defined in a draft local edit that didn't get committed,
   OR `__init__.py` was prematurely updated. Search history with
   `git log -S "ORACLE_COVERAGE_START" -- unified_api_contracts/registry/capability_declarations/_defi.py`
   for the original definition; restore the symbol.
2. **Anyone touching UAC** fixes the EN DASH at `alerting/thresholds.py:60` while
   they're already in the file. One char replace.
3. Once both fixed, every dependent repo's QG goes green.

## Related

- CLAUDE.md "Findings Triage Discipline" temporary exception for QG-failure findings on
  someone else's code (active 2026-05-07 → ~2026-05-09 during Ikenna's QG cleanup
  sweep) usually exempts these from the issue-doc requirement, but operator
  direction 2026-05-08 PM ("flag in issues in pm issues/ directory in plans") elevated
  filing this for visibility.
- Tab 2 plan-of-record:
  [`live_pipeline_mtds_mdps_features_2026_05_08`](../live_pipeline_mtds_mdps_features_2026_05_08.md).
- Tab 1 plan-of-record (likely owner): [`defi_master_2026_05_07`](../defi_master_2026_05_07.md).
