---
doc_type: plan
title: Fix 23 DeFi adapters' broken instrument_type filter — lowercase literals never match the real uppercase enum
summary: >-
  7 lending adapters (Euler_V2/Fluid/Radiant/Venus/Benqi/Morpho/Compound_V3) and 16 yield-bearing/LST adapters
  (Lido/EtherFi/JitoRestaking/Idle/KelpDAO/Karak/RocketPool/SolBlaze/Symbiotic/Sanctum/Convex/Ethena/Renzo/Pendle/
  Puffer/Yearn) guard get_instruments(instrument_type=...) against lowercase snake_case literals ("lending_market",
  "yield_bearing") that never match the real InstrumentType StrEnum values ("LENDING", "YIELD_BEARING"). Any
  canonical-form type-filtered fetch across most of the DeFi universe silently returns an empty list. Only aave_v3.py
  and spark.py check the enum correctly.
status: active
nature: notes
asset_group: [defi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [instrument-id, instrument-type, bug-fix, p0, defi]
related:
  [
    ../audit/results/canonical_instrument_id_audit_2026_07_08.md,
    issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
model_tier: sonnet-doable
thinking_tier: medium
source:
  "Canonical instrument-id audit, 2026-07-08 (canonical_instrument_id_audit_2026_07_08.md, finding #3) — confirmed via
  direct file reads of all 23 adapters plus the 2 correct reference implementations (aave_v3.py, spark.py)."
---

> **Live functional bug, not naming drift.** Any caller that type-filters these 23 adapters using the canonical
> uppercase value gets an empty list back today, silently — no error, just missing data. `aave_v3.py`/`spark.py` already
> do this correctly and are the reference pattern to copy.

## Root cause

23 DeFi adapters guard `get_instruments()` with `if instrument_type not in (None, "lending_market")` or
`if instrument_type not in (None, "yield_bearing")` — lowercase snake_case literals. `InstrumentType.LENDING`'s real
StrEnum value is `"LENDING"`; `InstrumentType.YIELD_BEARING`'s is `"YIELD_BEARING"`
(`unified-api-contracts/unified_api_contracts/_instrument_enums.py:53,55`). Real callers pass the canonical uppercase
form (confirmed at `instruments_service/reference_data/__init__.py:20`,
`get_instructions(instrument_type="PERPETUAL")`-style calls, passed through unmodified by `base_adapter.py:259-261`).
`"LENDING" != "lending_market"` — the filter guard is comparing against the wrong casing/spelling entirely.

**7 lending adapters**:
`instruments_service/reference_data/adapters/defi/{euler_v2,fluid,radiant,venus,benqi,morpho, compound_v3}.py`. **16
yield-bearing/LST adapters**:
`.../defi/{lido,etherfi,jito_restaking,idle,kelpdao,karak, rocket_pool,solblaze,symbiotic,sanctum,convex,ethena,renzo,pendle,puffer,yearn}.py`.
**Correct reference**: `.../defi/{aave_v3,spark}.py` (already check `InstrumentType.LENDING` directly).

## Todos

- [ ] [DATA] P0. **Fix all 23 adapters' `instrument_type` guard** to compare against the real canonical enum value
      (`InstrumentType.LENDING` / `InstrumentType.YIELD_BEARING`, or the exact matching uppercase string), matching
      `aave_v3.py`/`spark.py`'s existing correct pattern. One mechanical fix repeated 23 times — same shape everywhere.
- [ ] [VERIFY] P0. **Add a regression test that would have caught this** — a single parametrized test across all 23
      adapters asserting `get_instruments(instrument_type=<real enum value>)` returns non-empty when instruments exist,
      so this exact bug class can't silently reappear on adapter #24.
- [ ] [VERIFY] P1. **Confirm real production impact** — check whether any real production caller has actually been
      hitting this empty-result path (grep for call sites passing `instrument_type=` into these 23 adapters), to
      determine if this is currently degrading real captured data or is dead-code-adjacent (unreached in practice).
- [ ] [SCRIPT] P1. **Ship via quickmerge**, quality-gates green.

## Progress Log

- **2026-07-08** — Filed from the canonical instrument-id audit's P0 finding #3. All 23 broken adapters + the 2 correct
  reference implementations identified with file:line precision. No fix applied yet.
