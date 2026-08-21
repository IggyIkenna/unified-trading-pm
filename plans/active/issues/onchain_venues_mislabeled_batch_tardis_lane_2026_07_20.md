---
doc_type: issue
title:
  "Three on-chain CeFi venues carry a mislabeled pipeline_mode=batch_tardis lane — REAL mislabel, but NOT the cause of
  their catalogue-resolve gap"
summary:
  EXTENDED-STARKNET, LIGHTER-ZKSYNC and PACIFICA-SOLANA are self-archiving on-chain venues that UAC `PipelineMode`
  declares are NOT Tardis-sourced, yet a measured GCS walk finds their objects sitting under
  `pipeline_mode=batch_tardis`. For EXTENDED-STARKNET the SAME venue+data_type (`derivative_ticker`) exists in BOTH
  `batch_extended` and `batch_tardis` on the SAME day — a lane split-brain, not just a wrong label. The mislabel is
  therefore CONFIRMED for EXTENDED-STARKNET (303/610 sampled objects), PACIFICA-SOLANA (13/13) and LIGHTER-ZKSYNC's
  pre-2026-04-17 `ohlcv_1m` (20/25); LIGHTER's `derivative_ticker` under `batch_tardis` is CORRECT and declared. BUT the
  lane is NOT the root cause of the ~0% filename resolve rate that prompted this investigation — the shared resolver
  takes no `pipeline_mode` argument at all, and EXTENDED-STARKNET objects sitting in BOTH lanes resolved at 0% in BOTH
  before a resolver fix and 100% in BOTH after it. The lane fix and the resolve fix are independent workstreams.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [data-correctness, pipeline-mode, lane-partition, canonical-id, onchain-venue, split-brain, reconciliation]
related:
  [
    cefi_consolidated_closeout_2026_07_18,
    canonical_path_oracle_blind_to_filename_stem_2026_07_20,
    cefi_canonical_blueprint_2026_07_17,
  ]
created: 2026-07-20
author: unknown
priority: P1
parent_epic: security_and_cross_cutting_master
source:
  "Measured GCS walk of the prod cefi tick bucket (2025-11-05 -> 2026-07-18, 8 sampled days) during the cefi
  catalogue-coverage-gap investigation, cross-read against the UAC PipelineMode declarations."
execution_scope: local-only
drift_direction: advance-docs
depends_on: []
locked_by:
context_scope:
  [
    /codex/02-data/pipeline-mode-partition.md,
    /codex/04-architecture/solana-defi-coverage.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    unified-trading-library/unified_trading_library/pipeline_mode_resolver.py,
  ]
locked_since:
assigned_vm: NA
resolved_by:
---

# On-chain venues under `pipeline_mode=batch_tardis`

## Verdict in one line

**The mislabel is REAL but it is NOT the root cause of the resolve gap.** Both halves of that sentence are measured, and
the second half is the load-bearing one: a lane re-partition would have closed **zero** of the ~82,000 unresolvable
objects.

## Why the lane cannot be the cause (structural proof)

The shared resolver's signature takes no `pipeline_mode`:

`market-tick-data-service/scripts/_cefi_canonical_resolver_migration_2026_07_18.py:433-451`

```python
def _resolve_full(
    venue: str, raw_itype: str, id_or_symbol: str, data_type: str, underlying: str,
    wire_map: CeFiWireCanonicalMap, marker_base: dict[str, str], ...
) -> tuple[str | None, str]:
```

`pipeline_mode` is absent from the parameter list and from every lookup key the function builds
(`wire_map.canonical_for(v, itype, raw)`, `base_quote_map[(venue, itype, bq)]`,
`base_quote_date_map[(venue, itype, bq, date, strike, cp)]`). The lane only selects which GCS prefix the migration
walks; it never reaches the resolution decision.

## Why the lane cannot be the cause (natural experiment)

EXTENDED-STARKNET writes the same instruments into BOTH lanes, which makes it a controlled A/B on the real corpus:

| Lane                         | sampled objects | resolve BEFORE the resolver fix | resolve AFTER |
| ---------------------------- | --------------- | ------------------------------- | ------------- |
| `batch_extended` (correct)   | 307             | 0%                              | 100%          |
| `batch_tardis` (mislabelled) | 303             | 0%                              | 100%          |

Identical failure in the correct lane and the wrong lane; identical recovery. The lane label carried no signal either
way. The actual root cause was a resolver defect (an unpeeled `@LIN`/`@INV` margin marker on the wire stem plus a
canonical-shape regex that rejected catalogue ids whose base carries `_` or `.`).

## Measured lane distribution

Prod bucket `market-data-tick-cefi-prd-central-element-323112`, prefix `raw_tick_data/by_date`, 8 sampled days spanning
2025-11-05 → 2026-07-18. Read-only walk.

| Venue                 | `batch_tardis`                                | declared/native lane               | verdict                      |
| --------------------- | --------------------------------------------- | ---------------------------------- | ---------------------------- |
| **EXTENDED-STARKNET** | 303 (`derivative_ticker` 153, `ohlcv_1m` 150) | `batch_extended` 307               | **MISLABEL** (+ split-brain) |
| **LIGHTER-ZKSYNC**    | 327 (`derivative_ticker` 307, `ohlcv_1m` 20)  | `batch_lighter_api` 5 (`ohlcv_1m`) | **PARTIAL** — see below      |
| **PACIFICA-SOLANA**   | 13 (`ohlcv_1m` 13)                            | none (venue culled)                | **MISLABEL** (moot — culled) |

### EXTENDED-STARKNET — confirmed mislabel, with a split-brain

UAC declares the venue self-archiving with **no Tardis archive**:

`unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py:107-111`

```
# EXTENDED-STARKNET (StarkNet on-chain CeFi perp CLOB) uses its own public REST API
# (api.starknet.extended.exchange/api/v1 — no Tardis archive). Self-archiving venue
# like ASTER/HYPERLIQUID → batch_extended via UTL ``_VENUE_OVERRIDES["EXTENDED-STARKNET"]``.
BATCH_EXTENDED = "batch_extended"
```

So every `batch_tardis` object for this venue is mislabelled by the vendor rule (`source` = VENDOR, and Tardis is not
the vendor here). Worse than a flat mislabel: on 2026-03-15 `derivative_ticker` appears in BOTH lanes (`batch_tardis`
91 + `batch_extended` 66), so the same (venue, data_type, day) shard atom exists twice under two different
`pipeline_mode` values. Any reader that PREFIX-MATCHES the mode (the declared reader contract in
`/codex/02-data/pipeline-mode-partition.md`) will see one of the two and silently miss the other, or double-count across
both.

### LIGHTER-ZKSYNC — mostly CORRECT, do not "fix" it

`batch_tardis` for LIGHTER is **declared and intentional** for trades / book_snapshot_5 / derivative_ticker:

`unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py:112-119`

```
# LIGHTER-ZKSYNC (zkSync L2 perp CLOB) self-archives ohlcv_1m via its own public REST
# /candles endpoint (source=lighter_api, mainnet.zkln.elliot.ai) — NOT Tardis. Gives
# source-aware derivation an HONEST concrete stamp so native rows are batch_lighter_api,
# not fabricated batch_tardis (the bug) nor a bare None. Trades/book_snapshot_5/
# derivative_ticker for LIGHTER use the Tardis archive (from 2026-04-17), so lighter_api
# is a batch-only source (SOURCE_MODE_CAPABILITY = {BATCH}).
BATCH_LIGHTER_API = "batch_lighter_api"
```

The measured `derivative_ticker` 307 under `batch_tardis` on 2026-06/2026-07 days is therefore **correct**. The
mislabelled slice is narrow and specific: **20 `ohlcv_1m` objects under `batch_tardis` on days before 2026-04-17**
(2025-11-05 → 2026-02-25), which is exactly the "fabricated batch_tardis (the bug)" the UAC comment names. Those should
be `batch_lighter_api`, and 5 objects on the same days already are — so this venue ALSO has a split-brain, on
`ohlcv_1m`.

### PACIFICA-SOLANA — mislabelled but moot

All 13 sampled objects are `batch_tardis` / `ohlcv_1m`. Pacifica is a Solana perp DEX with no Tardis archive, so the
label is wrong — but `BATCH_PACIFICA` was **removed** from `PipelineMode` on 2026-07-16 under the operator ruling that
dropped every Solana perp DEX except Jupiter:

`unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py:120-125`

```
# BATCH_PACIFICA removed 2026-07-16 (operator ruling: all Solana perp
# DEXes dropped except Jupiter, not integrated — the "pacifica" source was
# removed from SOURCE_PRIORITY in the same landing ...)
```

There is no correct lane to move these to. They are orphan data from a culled venue and belong in the quarantine set,
not in a re-partition.

## Consequence for fail-hard reads

This is the sequencing point. Fail-hard on `pipeline_mode` must NOT be switched on while the split-brain exists: a
prefix-matching reader that fail-hards on an unexpected lane will reject the `batch_tardis` half of EXTENDED-STARKNET's
`derivative_ticker` — data that is real and captured. Lane fail-hard is gated on the re-partition below; **id-form
fail-hard is a separate gate** and is NOT blocked by this issue (see the resolve-gap closure plan in
`cefi_consolidated_closeout_2026_07_18.md`).

## Closure actions

- [ ] [DATA] P1. Re-partition EXTENDED-STARKNET `batch_tardis` → `batch_extended` (303 sampled; extrapolates to the full
      wire window). MUST de-duplicate against the objects already in `batch_extended` for the same (day, data_type,
      instrument) — this is a MERGE, not a blind move, because the split-brain means both sides can hold the same atom.
- [ ] [DATA] P1. Re-partition LIGHTER-ZKSYNC `ohlcv_1m` under `batch_tardis` on days < 2026-04-17 → `batch_lighter_api`
      (20 sampled), same de-dup requirement. Leave `derivative_ticker` under `batch_tardis` ALONE — it is correct.
- [x] ✅ [DATA] P2. Quarantine PACIFICA-SOLANA (13 sampled, 265 census-wide): no valid lane, no catalogue rows, venue
      culled. Register in the quarantine set so fail-hard can be enabled around it. **CLOSED 2026-08-09
      (stale-check-cefi, staleness re-audit)**: this is the same registration action tracked (and already closed) under
      `cefi_4surface_migration_execution_log_2026_07_24.md`'s parallel "Register PACIFICA-SOLANA (265) in the fail-hard
      quarantine set" todo — done via `unified-api-contracts@989e9d16` (2026-07-21). Live-verified today:
      `unified_api_contracts/canonical/quarantine.py`'s `QUARANTINE_REGISTRY` carries exactly one entry,
      `"PACIFICA-SOLANA"` (`instrument_stem="*"`, reason cites "265 objects... venue culled 2026-07-16" — same figure
      and same venue this todo names), matching "no valid lane, no catalogue rows, venue culled... register in the
      quarantine set" verbatim. This doc's own sibling closure items above already reached the same "the target
      mechanism already exists" pattern (the writer-fix todo cites `unified-trading-library@a4779c8b`); this is the
      remaining half.
- [x] ✅ [DATA] P1. Find the WRITER that stamped `batch_tardis` on a non-Tardis venue and fix the derivation at source,
      before any re-partition — otherwise the next capture re-creates the mislabel. Start from the UTL
      `_VENUE_OVERRIDES` map that `PipelineMode` cites for ASTER / HYPERLIQUID / EXTENDED-STARKNET. **DONE
      unified-trading-library@a4779c8b (2026-08-07, slot-11, batch4 todo P2)**. Root cause: the honest-absence guard for
      LIGHTER-ZKSYNC/ohlcv_1m (returns None for source-blind calls) was correct, but
      `_resolve_pipeline_mode_for_sentinel` in MTDS then fell through SOURCE_PRIORITY[("cefi","ohlcv_1m")] = "tardis" →
      BATCH_TARDIS on every sentinel write. EXTENDED-STARKNET was already fixed 2026-07-18 (hyphenated key in
      `_VENUE_OVERRIDES`). Fix: added `("LIGHTER_ZKSYNC","ohlcv_1m"): PipelineMode.BATCH_LIGHTER_API` to
      `_VENUE_DT_OVERRIDES`; removed dead guard; updated regression test + stale comment. QG green.

## Codex SSOTs

- `/codex/02-data/pipeline-mode-partition.md` — the source-aware `{mode}_{source}` contract and the reader PREFIX-MATCH
  rule this issue violates.
- `/codex/04-architecture/solana-defi-coverage.md` — the Pacifica cull ruling.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - 3 of 4 todos are prod GCS
  pipeline_mode re-partitions requiring de-dup MERGE semantics against a live split-brain; delete/move-safety gated.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries, unchanged — still accurate).
- **context-scout 2026-08-06**: re-scouted; swapped the resolver-migration script for the UTL
  `pipeline_mode_resolver.py` (`_VENUE_OVERRIDES` map — the writer named in the last open todo), still 5 entries.
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-07-30 verdict; 3
  of 4 closure actions are still prod GCS pipeline_mode re-partition/merges against a live split-brain needing
  delete/move-safety gating, and the 4th (find+fix the writer) sequences before them, so the doc stays NA as a unit.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-07-30 verdict; 3
  of 4 closure actions are still prod GCS `pipeline_mode` re-partition/merges against a live split-brain needing
  delete/move-safety gating, and the 4th (find+fix the writer) sequences before them via batch4 (still draft), so the
  doc stays NA as a unit.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — the writer-fix item was already closed today by a concurrent
  session; 3 genuine-work items remain (prod GCS pipeline_mode re-partition/merges against a live split-brain).
- **stale-check-cefi 2026-08-09** (staleness re-check on already-KEEP-NA-marked docs, operator-requested): the
  PACIFICA-SOLANA quarantine-registration todo was stale — already done since `unified-api-contracts@989e9d16`
  (2026-07-21), the same commit closes the parallel todo in `cefi_4surface_migration_execution_log_2026_07_24.md`.
  Flipped with evidence. 2 genuine-work items remain (EXTENDED-STARKNET / LIGHTER-ZKSYNC prod GCS pipeline_mode
  re-partition/merges against a live split-brain) — re-checked, no evidence either has landed since the 2026-08-07
  marker; doc stays `assigned_vm: NA`.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — 2 of 4 original closure actions now
  done (PACIFICA-SOLANA quarantine closed today 2026-08-09; writer-fix closed 2026-08-07). 2 remain: both prod-GCS
  split-brain MERGE operations, single-walk-discipline-sensitive.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirms prior verdicts; the 2 remaining items
  (EXTENDED-STARKNET, LIGHTER-ZKSYNC prod-GCS pipeline_mode re-partition/MERGE operations against a live
  split-brain) stay delete/move-safety-gated, single-walk-discipline-sensitive.
