---
name: shard-utilisation-sweep
description: >-
  Emit a per-axis CONSUMPTION verdict for every declared venue, data_type, instrument_type and chain in the
  already-computed daily coverage.json — "is this manifested axis value consumed by anything?", the opposite
  direction from the existing GCS→manifest orphan sweeps. Closes the `[SKILL] P1` "Shard utilisation / orphan
  sweep" definition-of-done item in /plans/epics/system_readiness_master.md. SAFETY: emits a consumption verdict
  ONLY, never a delete suggestion; reads the real consumer registries rather than inferring from grep counts; and
  prints `unverified` whenever the registry cannot answer, so an absent capability and an unchecked one are never
  collapsed. Reuses shard_universe.py, the same enumeration engine the honest-coverage and readiness dumps share,
  so all three agree on the denominator. Trigger on `/shard-utilisation-sweep`, "is this shard consumed by
  anything", "which venues/data_types/instrument_types/chains does nothing read", "run the orphan consumption
  sweep", "shard utilisation".
---

# Shard-utilisation sweep

## What it answers

The existing sweeps (`instruments-service/scripts/migration_orphan_sweep.py`,
`market-data-processing-service/scripts/candle_orphan_sweep.py`, MTDS's sports fork) walk GCS and ask
**"is this stored object manifested?"**. This asks the opposite: **"is this manifested axis value consumed
by anything?"**

## Safety contract — read this before acting on output

**It never emits a delete suggestion.** A false orphan verdict could send someone deleting live data, so the
tool is built to under-claim:

- **It reads the consumer, never a grep count.** Verdicts come from importing the real registries
  (`VENUE_TO_ASSET_GROUP`, `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`, `KNOWN_CHAINS`). A runtime-resolved
  consumer never appears in a token grep.
- **`unverified` is a first-class verdict**, not a rounding of "no". If a registry cannot be imported, or does
  not model that asset_group, or uses a different vocabulary, the answer is `unverified` with the reason.

Two guards exist because the naive version cried wolf on real data, and both are load-bearing:

1. **DeFi bare-vs-glued venues.** `VENUE_TO_ASSET_GROUP` keys DeFi in the glued `PROTOCOL-CHAIN` form
   (`AAVE_V3-ETHEREUM`); the manifest carries the bare protocol (`AAVE_V3`) with chain in its own column. A bare
   membership test produced **95 false orphan verdicts** on the 2026-08-20 payload, including `AAVE_V3`, `LIDO`
   and `MORPHO` at 50+ live cells each. A bare venue prefixing any glued key is CONSUMED — the mismatch is
   reported as a canonicalisation-cutover finding instead.
2. **Disjoint vocabularies.** The registry must cover a MAJORITY (`_VOCAB_OVERLAP_MIN`, 0.5) of what an
   asset_group's manifest actually carries before a missing value counts as `not_consumed`. Sports' registry
   holds 5 odds-SHAPE types while its manifest carries ~84 MARKET types — 1% overlap, so absence proves nothing.
   `cefi` sits at 100%, so absence there is real. DeFi has NO registry entry at all, which is itself the finding.

## Running it

Needs a venv carrying BOTH `unified_api_contracts` and `unified_trading_library` — use instruments-service's,
same as the sibling dumps (it owns `measure_honest_coverage.py`, which writes the coverage.json this reads).

```bash
cd unified-trading-pm
../instruments-service/.venv/bin/python \
  cursor-configs/skills/shard-utilisation-sweep/scripts/sweep_shard_utilisation.py
# --date YYYY-MM-DD   pin a specific coverage.json (default: latest)
# --json              machine-readable
```

It always exits 0. That is deliberate: a non-zero exit would invite wiring it into CI as a blocker, and a
gate that can produce `unverified` must not fail a build.

## Reading the output

Findings sort first (`not_consumed`, then `unverified`, then `consumed`). Every row carries its shard-cell
count and the reason for its verdict. A `chain axis source` line says whether chain came from the joined
shard-atom projection or the coarser marginal `by_chain` — the joined one only appears once
`by_venue_instrument_type_data_type_chain` is present in that day's payload.
