---
doc_type: issue
title:
  "PROTOCOL_CAPABILITIES lending declarations (aave_v3/spark/compound_v3/morpho/venus/benqi/solend) still declare
  instrument_types=[LENDING] — never updated for the 2026-07-09/07-13 A_TOKEN/DEBT_TOKEN retrofit, causing 'unmapped
  instrument_type' warnings and imprecise expected-universe enumeration for every A_TOKEN/DEBT_TOKEN instrument on these
  protocols"
summary: >-
  Discovered while confirming the second done-when criterion of a CeFi-orphan-blob-purge task (a fresh
  enumerate_expected_universe dry-run for asset_group=defi) — the run logged dozens of "G1-ENUM: unmapped
  instrument_type='A_TOKEN'/'DEBT_TOKEN' for asset_group='defi' ... falling back to all data_types. Add a matrix entry
  to unified_api_contracts.registry.market_data_categories to suppress" warnings, for instruments on MORPHO-BASE,
  SOLEND-SOLANA, SPARK-ETHEREUM, VENUS-BSC, and VENUS-ETHEREUM (and by extension AAVE_V3/COMPOUND_V3/ BENQI, which share
  the identical declaration pattern). Root cause traced to
  unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py: every one of these lending
  protocols' PROTOCOL_CAPABILITIES entry declares `instrument_types=_LENDING` where `_LENDING = [_IT.LENDING.value]` (a
  single generic value) — but a SEPARATE, already-shipped session (canonical_id_p0_defi_adapter_type_filter_bug_
  2026_07_08.md's fix wave, 2026-07-09 through 2026-07-13, plus this session's canonical_id_builder_retrofit_checklist
  _2026_07_08.md todo 2 confirmation) retrofitted these SAME protocols' actual adapters to emit the real, narrower
  `A_TOKEN`/`DEBT_TOKEN` pair as their instrument_key/instrument_type — the capability-declaration registry was never
  updated in lock-step, so the market_data_categories validity matrix (built FROM PROTOCOL_CAPABILITIES for defi) has no
  entry for what these adapters actually emit.
status: resolved
nature: issue
asset_group: [defi]
stage: [data, meta]
repos: [unified-api-contracts]
scope: [engineer]
tags: [defi, instrument-type, capability-declarations, market-data-categories, lending, a-token, debt-token, enumerator]
related:
  [
    /plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md,
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: instruments_master
source:
  "slot-11 (data_engineering), discovered while confirming cefi_satellite_ao_dispatch_batch1_2026_07_25.md's
  purge-orphaned-blobs todo done-when criteria (fresh enumerate_expected_universe dry-run for asset_group=defi)"
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
drift_direction: advance-code
resolved_by: "unified-api-contracts@cb9e97dfd"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
---

> **🟢 ARCHIVED 2026-07-28** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule.

# PROTOCOL_CAPABILITIES lending declarations never updated for the A_TOKEN/DEBT_TOKEN retrofit

## What I found

`unified_api_contracts/registry/capability_declarations/_defi.py`:

```python
_LENDING = [_IT.LENDING.value]
...
"aave_v3": _ProtocolCapability(..., instrument_types=_LENDING, ...),
"spark": _ProtocolCapability(..., instrument_types=_LENDING, ...),
"compound_v3": _ProtocolCapability(..., instrument_types=_LENDING, ...),
"morpho": _ProtocolCapability(..., instrument_types=_LENDING, ...),
"venus": _ProtocolCapability(..., instrument_types=_LENDING, ...),
"benqi": _ProtocolCapability(..., instrument_types=_LENDING, ...),
"solend": _ProtocolCapability(..., instrument_types=_LENDING, ...),  # (line ~791, not re-checked this pass)
```

`valid_data_types_for_instrument_type()` (`market_data_categories.py`) builds its DeFi validity matrix by unioning
`cap.data_types` across every `PROTOCOL_CAPABILITIES` entry whose `instrument_types` contains the queried type — since
none of these entries list `a_token`/`debt_token`, any A_TOKEN or DEBT_TOKEN instrument on these 7 protocols resolves to
`None` (unmapped), which `enumerate_expected_universe.py` logs as a warning and handles by falling back to ALL canonical
data_types for that row (not silently dropped, but imprecise — the enumerator can't narrow to the protocol's REAL
declared data_types for these rows the way it does for every correctly-mapped instrument_type).

## Evidence

Live `enumerate_expected_universe.py --asset-group defi` dry-run, 2026-07-27 (7-day window,
`gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet`, 12,220 instruments loaded) logged this
warning for (non-exhaustive, first occurrences observed):

- `MORPHO-BASE:A_TOKEN:ACBBTC-USDC:0x125081`
- `SOLEND-SOLANA:A_TOKEN:AmSOL`, `:AstSOL`, `:AtBTC`, `:AwstETH` (+ `DEBT_TOKEN:DEBT*` siblings, ~15+ instruments)
- `SPARK-ETHEREUM:A_TOKEN:ACBBTC`, `:ALBTC`, `:APYUSD`, `:AUSDC`, `:AUSDT`, `:AWEETH`, `:AWETH`, `:AWSTETH` (+
  `DEBT_TOKEN:DEBT*` siblings)
- `VENUS-BSC:A_TOKEN:ABNB-USDC`, `:AUSDT-USDC` (+ `DEBT_TOKEN` siblings)
- `VENUS-ETHEREUM:A_TOKEN:AWETH-USDC` (+ `DEBT_TOKEN` sibling)

AAVE_V3/COMPOUND_V3/BENQI share the identical `instrument_types=_LENDING` declaration pattern and were confirmed
retrofitted to A_TOKEN/DEBT_TOKEN in the same 2026-07-09/07-13 fix wave
(`canonicalize_defi_lending_atoken_debttoken_catalog_2026_07_13.py`), so they very likely trigger the same warning for
their own instruments too — not directly observed in this run's grep output (may have been outside the 7-day window's
catalog slice, or logged and simply not distinct-checked), worth re-confirming when this is fixed.

## Why it matters

- Not a correctness bug in the sense of dropping data or crashing — the fallback is safe-by-design (all data_types,
  never fewer than warranted). But it defeats the PURPOSE of the DeFi protocol-narrowing layer
  (`uac_data_type_validity_combinator_fragmentation_2026_07_07.md`'s two-layer redesign) for every A_TOKEN/DEBT_TOKEN
  instrument on 7 protocols — potentially inflating `expected_unattempted`/`EXPECTED_REFERENCE_ONLY_NO_CAPTURE_PATH`
  counts for these rows with data_types the protocol never actually supports, which is exactly the "hybrid protocol
  data_types leak to every instrument of that type" failure mode the narrowing layer exists to prevent.
- Directly connected to this session's other work (`canonical_id_builder_retrofit_checklist_2026_07_08.md` todo 2) — the
  A_TOKEN/DEBT_TOKEN retrofit was declared complete there, but this finding shows the retrofit's downstream
  capability-registry wiring was never closed out.

## Recommended decision

Update each affected protocol's `instrument_types` in `_defi.py` from `_LENDING` (`[LENDING]`) to declare
`[A_TOKEN, DEBT_TOKEN]` (or a shared `_LENDING_ATOKEN_DEBTTOKEN` constant, mirroring the existing `_LENDING` pattern),
matching what the adapters actually emit today. Verify this doesn't silently narrow `data_types` for any
currently-passing consumer that relies on the `LENDING` generic value being present (grep all callers of
`PROTOCOL_CAPABILITIES[...].instrument_types` before changing, not just the enumerator path this issue was found
through).

## Todos

- [x] [DATA] P2. Update `instrument_types=_LENDING` to the real `[A_TOKEN, DEBT_TOKEN]` pair for aave_v3, spark,
      compound_v3, morpho, venus, benqi, and solend in
      `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py`. Check every other
      consumer of these entries' `instrument_types` field before changing (not just the enumerator). **Done when**: a
      fresh `enumerate_expected_universe.py --asset-group defi` dry-run over a window covering instruments on all 7
      protocols logs ZERO "unmapped instrument_type=... A_TOKEN/DEBT_TOKEN" warnings; `quality-gates.sh` green. (repo:
      unified-api-contracts) — **DONE 2026-07-28**: added `_LENDING_ATOKEN_DEBTTOKEN` shorthand, updated all 7
      protocols; verified radiant/euler_v2/fluid/marginfi (same `_LENDING` pattern, not part of this retrofit) left
      untouched, and no other `PROTOCOL_CAPABILITIES[...].instrument_types` consumer hardcodes an expectation on the old
      value. Shipped unified-api-contracts@cb9e97dfd, `quality-gates.sh` green.
