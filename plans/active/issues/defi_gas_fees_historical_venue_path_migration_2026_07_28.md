---
doc_type: issue
title:
  "gas_fees venue-naming rename (market-tick-data-service@522185a6, 2026-07-22) fixed paths only forward — pre-existing
  historical gas_fees objects still sit under venue=<CHAINNAME> and won't retroactively move"
summary: >-
  The 2026-07-22 crash-loop + venue-naming fix (`market-tick-data-service@522185a6`) corrected `gas_fee_handler.py` so
  every `write_defi_rows()` call site now passes `venue=_GAS_FEE_VENUE` ("ALCHEMY") instead of `venue=<chain-name>` /
  `venue="SOLANA"` / `venue="BITCOIN"`. That fix changes GCS write paths going forward only — every `gas_fees` object
  written before the commit (2026-07-22 18:07:42 +0100) still sits under its pre-fix `venue=<CHAINNAME>` prefix (14
  distinct chain values across EVM/Solana/Bitcoin) while the manifest recorder has, since the fix, been claiming
  `venue=ALCHEMY` for all new writes — a GCS-path-vs-manifest-identity split between old and new data for the same
  logical venue. Whether to migrate (rewrite/copy the pre-existing objects to `venue=ALCHEMY`) or leave them under the
  legacy per-chain prefixes (and teach readers to look in both places) is an operator decision, not decided or executed
  by this doc.
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [defi, gas-fees, venue-naming, path-migration, honest-absence, operator-gated]
related:
  [
    plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    plans/archive/issues/defi_five_never_captured_venues_fix_2026_07_22.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-07-28
parent_epic: defi_master
source: [data_engineering slot-7, 2026-07-28, dispatched via defi_satellite_ao_dispatch_batch1-017]
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: data_engineering
drift_direction: neutral
depends_on: []
last_updated: 2026-07-28
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

## What I found

`plans/archive/issues/defi_five_never_captured_venues_fix_2026_07_22.md` (§ "ALCHEMY (gas_fees)") root-caused and fixed
a real GCS-vs-manifest identity mismatch in `gas_fee_handler.py`: every `write_defi_rows()` call site wrote
`venue=<chain-name>` (the EVM chain name, or the literal `"SOLANA"` / `"BITCOIN"`) while the manifest recorder
separately claimed `venue="ALCHEMY"` (the venue-agnostic registry key `_GAS_FEE_VENUE`) for the same rows — GCS objects
and their own manifest entries disagreed on which venue wrote them. That doc explicitly flagged, but did not file, the
retroactive-path consequence (line 191-192): _"the rename changes GCS paths going forward — pre-existing historical
objects under the wrong `venue=<CHAINNAME>` prefix won't retroactively move; that's a separate, operator-gated
path-migration concern, filed not folded in."_ This doc is that filing.

**The rename commit, verified against `market-tick-data-service` git history**:

```
commit 522185a6fc4eaa728892eec543392a2bfca70e68
Author: ikennaigboaka [slot-3·laptop] <ikennaigboaka@gmail.com>
Date:   Wed Jul 22 18:07:42 2026 +0100

    fix(mtds): gas_fees crash-loop (bounded freshness warmup) + venue-naming (ALCHEMY)
```

**Exact pre-fix → post-fix diff** (`git show 522185a6 -- market_tick_data_service/cli/handlers/gas_fee_handler.py`), 4
call sites, `chain=` untouched in all 4 (chain granularity was already independent of venue — nothing invented by the
fix):

| Call site                                                             | Pre-fix `venue=`        | Post-fix `venue=`            | `chain=` (unchanged)                       |
| --------------------------------------------------------------------- | ----------------------- | ---------------------------- | ------------------------------------------ |
| `_write_solana_historical_shard` (`_collect_solana_historical_shard`) | `"SOLANA"`              | `_GAS_FEE_VENUE` ("ALCHEMY") | `"SOLANA"`                                 |
| `_write_solana_live_shard`                                            | `"SOLANA"`              | `_GAS_FEE_VENUE` ("ALCHEMY") | `"SOLANA"`                                 |
| `_write_btc_shard` (`_collect_btc_fees` path)                         | `"BITCOIN"`             | `_GAS_FEE_VENUE` ("ALCHEMY") | `"BITCOIN"`                                |
| `_write_defi_date_rows` (EVM, per-chain-shard helper)                 | `chain_name` (variable) | `_GAS_FEE_VENUE` ("ALCHEMY") | `chain_name` (variable, e.g. `"ETHEREUM"`) |

**The 14 distinct pre-fix `venue=<CHAINNAME>` values** this population spans, derived from the current
`DEFAULT_GAS_FEE_CHAINS` chain-id list (`gas_fee_handler.py:75-98`) mapped through `CHAIN_ID_TO_NAME`
(`market_interface/clients/gas_fee_client.py:35-63`) plus the two non-EVM chains handled by dedicated call sites:

- EVM (12, via `CHAIN_ID_TO_NAME`): `ETHEREUM` (1), `OPTIMISM` (10), `BSC` (56), `POLYGON` (137), `BASE` (8453),
  `ARBITRUM` (42161), `AVALANCHE` (43114), `LINEA` (59144), `FANTOM` (250), `CELO` (42220), `MANTLE` (5000), `AURORA`
  (1313161554).
- Non-EVM (2, dedicated call sites): `SOLANA`, `BITCOIN`.

Any `gas_fees` object written before 2026-07-22 18:07:42 +0100 (whenever the crash-loop allowed a successful run — the
same source doc's crash-loop section documents `gas-fees` had a pre-existing, if intermittently-crashing, daily cron
since before this incident) sits under one of these 14 `venue=<CHAINNAME>` prefixes with a manifest row that, pre-fix,
also recorded `venue=<CHAINNAME>` (GCS path and manifest agreed pre-fix — the mismatch is cross-era: old data stays
labeled by chain name, new data is labeled `ALCHEMY`, so a `venue=ALCHEMY` manifest/GCS query today would miss the
entire pre-2026-07-22 historical population for this data_type).

## Why it matters

- **A `venue=ALCHEMY` query (manifest or GCS) today is honest about post-fix data but silently blind to everything
  written before 2026-07-22** — this is exactly the kind of split-population risk the data-pipeline-correctness
  heartbeat exists to catch: no single query surfaces the full `gas_fees` history without knowing to check 15 distinct
  venue values (14 legacy + `ALCHEMY`), and nothing in the manifest schema documents that split today.
- **The fix was deliberately scoped to be forward-only** (source doc, explicit and correct call at the time) — this doc
  is the tracked follow-through on that stated deferral, not a claim that leaving it unmigrated is wrong. Both "migrate"
  and "leave, but document the split" are legitimate outcomes; which one is right depends on how much historical
  `gas_fees` data actually exists pre-fix (volume/date-range unknown as of this doc) and how many consumers query
  `gas_fees` by venue rather than by `chain=` (which was never broken).
- **Any migration would be a prod GCS copy+relabel across up to 14 prefixes** — a nontrivial, delete-adjacent operation
  that the delete-safety protocol and the "heavy I/O never runs from the operator's local machine" rule both gate;
  scoping it correctly (real volume, real date range, real consumer impact) is worth doing before anyone commits to an
  approach.

## Recommended decision

- [ ] [OPERATOR] P1. Decide migrate-vs-leave for the pre-2026-07-22 `gas_fees` historical population currently under
      `venue=<CHAINNAME>` (14 values: `ETHEREUM`/`OPTIMISM`/`BSC`/`POLYGON`/`BASE`/`ARBITRUM`/`AVALANCHE`/`LINEA`/
      `FANTOM`/`CELO`/`MANTLE`/`AURORA`/`SOLANA`/`BITCOIN`):
  - **Migrate**: copy each legacy-prefixed object to the equivalent `venue=ALCHEMY` path (chain granularity preserved
    via the untouched `chain=` field/segment), re-verify against the manifest, then stage the legacy-prefix delete under
    the standard 5-part delete-safety proof (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) — this is a
    prod bucket delete, human-only regardless.
  - **Leave**: keep the legacy `venue=<CHAINNAME>` objects in place permanently and instead teach every `gas_fees`
    reader (and this data_type's manifest-status surface) that a complete history requires querying all 15 venue values,
    not just `ALCHEMY` — documented as a standing exception, not silently absorbed.
  - A first, cheap scoping step either path needs and neither has been done yet: measure the actual historical
    `gas_fees` volume/date-range under the 14 legacy prefixes (a bounded, single-prefix manifest/GCS check per venue —
    not a corpus-wide walk) so the decision is made against real scale, not a guess. Repo: market-tick-data-service (+
    unified-trading-pm to record the decision back into this doc). Source: this doc.
