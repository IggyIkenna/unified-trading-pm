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

- **2026-07-30 (interactive session, incidental discovery)**: `scripts/migrate_legacy_gas_fees_venue_2026_07_30.py` (the
  migration script slot-7 is executing this todo through) has a confirmed unbounded memory leak — killed TWICE in ~15
  minutes after ballooning to 42-45GB RSS each time, both times taking down the whole orchestrator API (fleet-wide, not
  scoped to this task). Root-cause isolation + full detail:
  `/plans/active/issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md`. **This todo cannot safely
  proceed until that leak is fixed** — do not re-run the script as-is.

- **2026-07-30 (slot-7, data_engineering) — scoping complete, leak fixed, migration in progress**:
  - **Scoping (step a)**: bounded manifest-only read (`read_availability_index`, filtered `data_type=gas_fees`, no GCS
    walk) found real legacy history under only **10 of the 14** listed legacy venues — `ETHEREUM` (1857 shard-days,
    2020-01-01..2026-07-21), `OPTIMISM` (797), `BSC` (1611), `POLYGON` (1697), `BASE` (739), `ARBITRUM` (1272),
    `AVALANCHE` (1565), `LINEA` (767), `MANTLE` (763), `AURORA` (1357) — **12,425 total legacy manifest rows**.
    `FANTOM`, `CELO`, `SOLANA`, `BITCOIN` have **zero** historical manifest rows (FANTOM/CELO are live-only per code
    comments; BTC collection is hardcoded disabled; Solana requires an explicit flag never passed in prod) — nothing to
    migrate for those 4. One exact collision found: `chain=ETHEREUM date=2026-07-21` has BOTH a legacy captured row AND
    a post-fix `venue=ALCHEMY` captured row (same calendar day straddling the fix's deploy time) — the migration script
    skips that one pair to avoid duplicating/clobbering the already-canonical object.
  - **Root cause of the memory leak** (full detail in the linked doc): the script's `ManifestWriter(...)` omitted
    `per_vm_shards=True`, so every flush took the legacy path that reads/writes the ENTIRE consolidated DeFi manifest
    index (~14.86 GiB / 27M+ rows) instead of a small per-host shard. **Fixed** (`market-tick-data-service@8016c7e4`),
    verified safe under a `ulimit -v` memory cap with a real (throwaway) probe write.
  - **Migration (step b) IN PROGRESS**: with the fix applied, RSS holds stable at ~1.2GB (vs 40+GB before) under a
    protective `ulimit -v 8000000` (8GB) wrapper — re-verified real-world; a 4GB cap was too tight (crashed pyarrow's
    own virtual-address-space reservations with `std::system_error`, unrelated to the actual leak). As of this note,
    ~3800/12,424 legacy rows processed (chains ARBITRUM, AURORA complete; AVALANCHE in progress), zero memory growth
    trend, running as a background process (not tied to this chat session — survives compaction).
  - **Step c (stage, do not execute, the delete-safety proof)** not yet started — genuinely blocked on step b's
    completion, not on any decision.
  - **Lessons for whoever resumes**: (1) `ManifestWriter` constructed directly (outside a deployed service with
    `MANIFEST_PER_VM_SHARDS=true` in its env) silently defaults to the expensive legacy full-index path — always pass
    `per_vm_shards=True` explicitly in a one-off script. (2) `ulimit -v` is a virtual-memory cap, not RSS — pyarrow/
    pandas reserve large virtual address space regardless of actual usage, so a tight cap (e.g. 3-4GB) will false-crash
    even correct code; 8GB was the smallest cap that didn't trip on legitimate work in this case. (3) Pre-existing
    legacy objects sometimes have a byte-identical duplicate under a second leaf-name convention (`GAS.parquet` +
    `_migrated_gas_fees_<start>_<end>.parquet`, both from an earlier per-instrument migration) — harmless, the
    idempotent `blob_exists` check on the shared target path naturally de-dupes them.

## Deferred work after 2026-07-30

| Item                                                                                                     | State / why deferred                                                                                                                                | Blocked on                                                                                   |
| -------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Full migration completion (~12,424 legacy rows → `venue=ALCHEMY`)                                        | Cannot be done yet — background process running, needs real elapsed wall-clock time (observed rate ≈ linear, ETA another ~40-50 min from this note) | Time elapsing; check `ps aux \| grep migrate_legacy_gas_fees` / manifest row counts directly |
| Stage (not execute) the 5-part delete-safety proof for the 10 legacy prefixes                            | Not started — genuinely next step, not a decision gap                                                                                               | Migration completion + verification that all 10 prefixes are fully copied                    |
| Flip this doc's todo checkbox                                                                            | Correctly withheld — work isn't done yet                                                                                                            | Migration completion + verification                                                          |
| `ManifestWriter.__init__` safety-check follow-up (P1, filed in the linked memory-leak doc)               | Not started — separate, smaller follow-up task                                                                                                      | Nobody yet; open item, not gating this migration                                             |
| Audit sibling `scripts/` for the same `per_vm_shards` omission (P2, filed in the linked memory-leak doc) | Not started — separate follow-up task                                                                                                               | Nobody yet; open item, not gating this migration                                             |

**Recommended next action**: check whether the background migration process (see script + log path in this session's
scratchpad, or just re-run the script — it is fully idempotent/resumable via its fast `blob_exists` pre-check) has
completed; if so, verify final written+skipped counts against the 12,424-row worklist (minus the 1 known collision),
update this doc with final numbers, flip the checkbox, ship, and `/done`. If the process died again, check
`ps`/`dmesg`/host memory BEFORE assuming a regression — this host runs many concurrent agent slots and a
non-migration-related host-memory event could still kill it even with the fix in place.
