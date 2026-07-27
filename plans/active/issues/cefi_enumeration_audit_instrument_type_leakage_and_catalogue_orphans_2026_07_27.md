---
doc_type: issue
title: >-
  Post-cutover enumeration audit found 2 findings without an existing ruling: instrument_type carries data_type-shaped
  values on 480 chain-bundle rows, and 31,207 canonical-shaped instrument_ids are orphaned from the IS catalogue
summary: >-
  Filed while flipping the enumeration-audit terminal checkpoint todo in
  `cefi_migration_cutover_and_track8_completion_2026_07_25.md`, post Script-1 corpus-wide `--apply` completion
  (2026-07-27). The census's dominant finding (instrument_id 99.49% canonical, residual = the already-ruled bare-wire
  class) cleanly satisfies that todo's done-when. Two smaller findings surfaced by the SAME run do NOT have an existing
  ruling and are tracked here rather than silently waved through: (1) 480 manifest rows carry `instrument_type` values
  of `futures_chain`/`options_chain` (277+30 rows) plus lowercase `future`/`spot`/`spot_pair`/blank (60+100+12+1) — the
  lowercase-casing subset is already covered by the D1/D2 2026-07-20 ruling (compare case-insensitively, do not flag),
  but `futures_chain`/`options_chain` are NOT case variants of any canonical value — they look like `data_type` values
  leaking into the `instrument_type` column, plausibly a deliberate TradFi-style chain-bundle-shard convention (mtds git
  history shows `_is_bundled_chain_shard` handling exactly this shape for CME/ICE), not yet confirmed as intentional
  here. (2) 31,207 canonical-SHAPED instrument_ids captured in the manifest are NOT members of the instruments-service
  catalogue (429,129-row `prod/catalog.parquet`) — dominated by `DERIBIT:OPTION:*` (29,264 of 31,207) — meaning either
  the catalogue is missing legitimate historical DERIBIT options, or these are captures under an id-form the catalogue's
  builder never produced. Both are read-only findings from a manifest-index audit (no GCS corpus walk, no writes).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [cefi, enumeration-audit, instrument-type, catalogue-orphan, chain-bundle, post-cutover]
related:
  [
    /plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
  ]
created: 2026-07-27
parent_epic: cefi_master
priority: P2
estimate_class: research
assigned_role: data_engineering
source: >-
  Surfaced by re-running `market-tick-data-service/scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`
  (read-only, manifest-index read against `gs://market-data-tick-cefi-prd-central-element-323112`, 8,880,557 rows) as
  the enumeration-audit terminal checkpoint for `cefi_migration_cutover_and_track8_completion_2026_07_25.md`, right
  after Script 1's corpus-wide `--apply` campaign finished (all shards `EXIT_STATUS=0`).
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# Enumeration audit: instrument_type chain-shape leakage + catalogue orphans (2026-07-27)

> Investigation-only record (this doc). No code was changed while authoring this doc. `assigned_vm: NA`,
> `execution_scope: local-only` — a human decides when to pick this up and whether either finding is a bug or a
> known-intentional shape.

## What I found

### Finding 1 — `instrument_type` carries non-canonical, non-casing values on 480 rows

The full distinct-value breakdown (8,880,557 total manifest rows):

```
5,940,519  PERPETUAL
1,936,673  SPOT_PAIR
  563,178  FUTURE
  437,205  OPTION
    1,948  perpetual        ⚠ lowercase — D1/D2 2026-07-20 ruled, migration_pending, do not flag
      554  None             ⚠
      277  futures_chain    ⚠ NOT a casing variant — this is a distinct string
      100  spot             ⚠ lowercase
       60  future           ⚠ lowercase
       30  options_chain    ⚠ NOT a casing variant
       12  spot_pair        ⚠ lowercase
        1  (blank)          ⚠
```

`futures_chain`/`options_chain` (307 rows total) are not case-different from any of the 4 canonical values
(`PERPETUAL`/`SPOT_PAIR`/`FUTURE`/`OPTION`) — they are literally the `data_type` column's own values (see the distinct
`data_type` list from the same run: `futures_chain` 366,162 rows, `options_chain` 122,850 rows), appearing in the
`instrument_type` column instead. `market-tick-data-service`'s own git history
(`8e43da75 fix(tradfi): Phase-D checker matches TradFi FUTURE/OPTION (CME/ICE) shards on underlying... _is_bundled_chain_shard reuses the WRITER's venue->instrument_type SSOT`)
shows a real, deliberate "bundled chain shard" convention exists for TradFi CME/ICE futures/options chains, where a
single manifest row represents an entire chain (not one instrument) and carries different key semantics. **Not yet
confirmed**: whether this SAME convention is deliberately applied to these 307 cefi rows (which venues/dates? DERIBIT
options chains are the most likely candidate given DERIBIT's dated-option structure already discussed elsewhere in this
migration), or whether this is a genuine writer bug that should be setting `instrument_type=OPTION`/`FUTURE` like every
other row.

The other 173 rows (100 `spot` + 60 `future` + 12 `spot_pair` + 1 blank) are lowercase-casing variants already covered
by the existing D1/D2 ruling — no new investigation needed for those.

### Finding 2 — 31,207 canonical-shaped instrument_ids are orphaned from the IS catalogue

Cross-referencing the manifest's captured canonical-shaped ids (49,386 distinct) against the instruments-service
catalogue (`prod/catalog.parquet`, 429,129 rows, 424,619 deduped canonical ids via `canonical_by_wire.values()`):

```
DERIBIT              OPTION         29,264   e.g. DERIBIT:OPTION:BTC-10APR20-4750-C
DERIBIT              FUTURE            721   e.g. DERIBIT:FUTURE:BNB-USDC@LIN
BYBIT                FUTURE            287
KRAKEN-FUTURES       PERPETUAL         256
COINBASE-FUTURES     PERPETUAL         217
HYPERLIQUID          PERPETUAL         167
BITGET-FUTURES       PERPETUAL          87
... (13 venues total, 31,207 orphan ids)
```

DERIBIT OPTION dominates (93.8% of all orphans). Two candidate explanations, NOT distinguished by this audit alone: (a)
the catalogue is missing legitimate historical DERIBIT option series (a catalogue-completeness gap — the builder never
produced these ids, e.g. long-expired dated options outside whatever window the catalogue build covers), or (b) these
captures exist under an id-form variant the catalogue's DERIBIT adapter never emits (a canonicalization mismatch,
similar in spirit to — but distinct from — the DERIBIT missing-quote defect this same plan's todo 1 already fixed).
Given DERIBIT dated-options have already been the root cause of 2 OTHER defects this same migration surfaced (the
missing-quote defect, todo 1; the giant-file OOM class hit during Script 1's `--apply`, this doc's own Progress Log) — a
3rd DERIBIT-options-specific anomaly in the same campaign is plausibly related, not coincidental, but this is a
hypothesis, not a confirmed root cause.

## Net effect

Neither finding blocks the enumeration-audit todo's own done-when (that todo's 4 stated axes —
instrument_id/instrument_type/venue/data_type non-canonical FORMS — are satisfied; catalogue membership is a different,
adjacent axis the same script happens to also report). Both are real, unresolved discoveries that deserve a look, at a
normal (not urgent) priority given their small scale relative to the corpus (480/8.88M = 0.005%; 31,207/8.88M = 0.35%).

## Todos

- [ ] [DATA] P2. Confirm whether `instrument_type ∈ {futures_chain, options_chain}` is a deliberate, already-shipped
      chain-bundle convention for these 307 cefi rows (check which venues/dates carry it, cross-reference against
      `_is_bundled_chain_shard`'s actual cefi-side callers if any) or a genuine writer bug that should emit
      `OPTION`/`FUTURE` like every other row. Repo: market-tick-data-service.
- [ ] [DATA] P2. Investigate the 31,207 catalogue-orphan DERIBIT-dominated ids — is this a catalogue-completeness gap
      (missing legitimate historical option series) or an id-form mismatch between the DERIBIT adapter and what got
      captured? Given DERIBIT has already produced 2 other distinct defects in this same migration (missing-quote,
      giant-file OOM), check whether this is the SAME underlying root cause manifesting a 3rd way, or genuinely
      separate. Repos: instruments-service, market-tick-data-service.
