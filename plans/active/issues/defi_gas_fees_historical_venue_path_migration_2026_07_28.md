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
assigned_vm: planning
execution_scope: orchestrator-agent
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

**RULED 2026-07-28 (operator general-theme ruling on remaining gated design-choice decisions, applied here): MIGRATE —
copy the pre-2026-07-22 legacy-prefixed `gas_fees` history to the canonical `venue=ALCHEMY` path; do not leave a
permanent 15-value split.** Reasoning applied from the operator's standing ruling: (a) "Full backfills, full migrations
— as long as an item isn't superseded by more recent work, DO IT" — this migration is not superseded by anything more
recent (the 2026-07-22 rename fix is the most recent relevant work, and it explicitly deferred this exact
follow-through, not cancelled it). (b) "Opt for full completions, no shortcuts, full functionality... if it's about
canonicalisation rather than a hack, do it properly" — this is squarely a canonicalisation question (one venue identity,
`ALCHEMY`, vs. a permanent 14-way legacy-chain-name split that every future reader must remember to check); "leave +
teach every reader to check 15 values" is exactly the cheap-shortcut alternative this ruling rejects, not the
properly-canonicalised one. (c) Cost is not a blocker (<$100 tier) — a GCS copy across 14 chain prefixes for one
data_type's historical volume is comfortably inside that budget even before scoping the exact byte count. Concrete
full-completion mandate for whoever dispatches this next: (1) run the cheap scoping step first (bounded,
single-prefix-per-venue manifest/GCS measurement, NOT a corpus-wide walk) to size the actual historical volume/date
range under all 14 legacy prefixes; (2) copy every legacy-prefixed object to its equivalent `venue=ALCHEMY` path
(`chain=` segment preserved unchanged, exactly as the 2026-07-22 fix left it), re-verifying each copy against the
manifest before treating any prefix as migrated; (3) once ALL 14 prefixes are copied + manifest-verified — no partial
subset — stage the legacy-prefix delete under the standard 5-part delete-safety proof
(`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`); **this final delete step stays a prod-bucket delete and
is human-only regardless of the migrate-vs-leave ruling above** — the ruling authorizes running the migration to
completion, it does not itself authorize the destructive delete, which still needs its own delete-safety sign-off at
that point in the sequence.

## Todos

- [ ] [DATA] P1. **RETAGGED 2026-07-28 (was `[OPERATOR]`) — RULED, see "Recommended decision" above.** Migrate the
      pre-2026-07-22 `gas_fees` historical population (14 legacy `venue=<CHAINNAME>` values:
      `ETHEREUM`/`OPTIMISM`/`BSC`/`POLYGON`/`BASE`/`ARBITRUM`/`AVALANCHE`/`LINEA`/`FANTOM`/`CELO`/`MANTLE`/`AURORA`/
      `SOLANA`/`BITCOIN`) to the canonical `venue=ALCHEMY` path, full completion across all 14 prefixes, no partial
      rollout. Steps: (a) bounded per-venue scoping measurement (volume/date-range, not a corpus walk); (b) copy +
      manifest-verify each of the 14 prefixes; (c) once all 14 are verified migrated, stage — but do NOT execute — the
      legacy-prefix delete under the standard 5-part delete-safety proof; the actual prod-bucket delete remains
      `[OPERATOR]`/human-only regardless of this ruling. (repo: market-tick-data-service; record scoping numbers +
      migration status back into this doc)

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - operator RULED 2026-07-28 (MIGRATE) + retagged from
  [OPERATOR]; copy+verify is non-destructive and the prod delete stays explicitly [OPERATOR]-gated inside the todo

- **2026-07-28 (gated-decision retag sweep)** — Applied the operator's general-theme ruling: migrate the 14 legacy
  `gas_fees` venue prefixes to canonical `venue=ALCHEMY` (full completion, no permanent 15-value split), while keeping
  the actual prod-bucket delete step human-only/`[OPERATOR]`-gated per the standard delete-safety protocol. Retagged the
  decision todo from `[OPERATOR]` to `[DATA]` with the ruling + reasoning + a concrete scope→copy→verify→(gated delete)
  sequence written into the doc. Docs-only, no GCS action taken.
