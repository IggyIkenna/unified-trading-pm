---
doc_type: issue
title: "Massive purge BLOCKED — 1.03M trades/tbbo objects are the ONLY copy (Databento L1 entitlement, never fetched)"
summary:
  Re-derivation before the gated Massive purge found that 1,032,672 of the 1,701,422 live `batch_massive` objects
  (60.69%) are `trades`/`tbbo` — data types Databento has NEVER written to the tradfi bucket, and CANNOT backfill
  because `trades`/`tbbo` are L1 schemas behind a 365-day free window and the billing guard fails closed. Purging
  Massive would permanently destroy over a million objects of unique data. Purge is HELD (option c). Also documents a
  separate data-correctness defect — 16,389 phantom `batch_databento` trades/tbbo `captured` manifest rows over 3,488
  shards, backed by ZERO objects on disk.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags:
  [massive-purge, databento, entitlement, data-correctness, manifest, phantom-rows, blocked-credentials, honest-absence]
related:
  [
    tradfi_canonical_path_migration_design_2026_07_19,
    tradfi_consolidated_closeout_2026_07_18,
    codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-07-20
priority: P0
parent_epic: tradfi_master
source:
  "Pre-purge re-derivation from availability_index.parquet (2026-07-20 12:54Z) + full physical batch_massive enumeration
  (1,701,422 objects, 2040 day-prefixes)"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by:
---

# Massive purge BLOCKED — the Massive `trades`/`tbbo` corpus is the ONLY copy

## Verdict

**(c) NO PURGE.** The gated `--purge-massive` is all-or-nothing over every `pipeline_mode=batch_massive` object. Running
it today would permanently destroy **1,032,672 objects (60.69% of the corpus)** for which no other copy exists and which
Databento cannot supply. The `--massive-backfill-verified` sentinel was **NOT** written — verification did not reach
zero, which is the gate working as designed.

This outcome is explicitly pre-authorized by `tradfi_consolidated_closeout_2026_07_18.md`: _"If the 571 backfill cannot
finish in-window → purge HELD + ETA (never purge-and-lose-data)."_

## The blocking fact — `trades`/`tbbo` are L1, and L1 is a 365-day window

`unified_api_contracts/registry/databento_subscription_allowlist.py`:

| Level | Schemas                                    | Free window | `LEVEL_MAX_LOOKBACK_DAYS` |
| ----- | ------------------------------------------ | ----------- | ------------------------- |
| L0    | `ohlcv-1s`, `ohlcv-1m`, `definition`, …    | ~16 years   | `16*365`                  |
| L1    | **`trades`**, **`tbbo`**, `mbp-1`, `bbo-*` | **1 year**  | **`365`**                 |

`assert_lookback_allowed()` **raises `DatabentoLookbackExceededError`** for any `start` older than the floor — it fails
closed by design so a metered PAYG charge can never fire silently.

**Measured (2026-07-20):** every Massive-only `trades`/`tbbo` shard predates the L1 floor of `2025-07-20`. The newest is
`2025-04-08` — **468 days old**, 103 days beyond the free window.

## Ground truth — Databento has NEVER written a single `trades`/`tbbo` object

This is stronger than the entitlement argument and does not depend on naming conventions. A physical listing of
`pipeline_mode=batch_databento` across 12 days spanning a full year (**all inside** the 365-day free window) found:

```
2026-07-10 … 2025-08-12   trades=0  tbbo=0   (every day)
data_types actually present: ohlcv_1m, ohlcv_1s, ohlcv_24h, futures_chain, options_chain
```

There is no Databento `trades`/`tbbo` data in this bucket at any date, in-window or out. So **no naming convention or
path shape can be hiding a duplicate** — the Massive copy is the only copy.

## Measured corpus split (full physical enumeration, 0 unparsed)

Live `batch_massive` objects: **1,701,422** — reconciles with the migration's `PURGE_MASSIVE = 1,701,414` (delta **+8**)
and the design estimate of 1,696,166 (delta +5,256). Enumerated across all 2,040 `day=` prefixes; **every** object
parsed to a `(venue, data_type, day)` shard (0 unparsed), so the map is total.

| data_type       |     objects |      % | recoverable from Databento?            |
| --------------- | ----------: | -----: | -------------------------------------- |
| `trades`        | **956,256** | 56.20% | ❌ NO — L1, and never fetched at all   |
| `ohlcv_1m`      |     520,052 | 30.57% | ⚠️ partial — L0, but broader universe  |
| `options_chain` |     148,553 |  8.73% | ⚠️ partial                             |
| `tbbo`          |  **76,416** |  4.49% | ❌ NO — L1, and never fetched at all   |
| `ohlcv_1s`      |         144 |  0.01% | ✅ L0                                  |
| `ohlcv_15m`     |           1 |  0.00% | ✅ derivable by aggregation from L0 1m |

- **UNIQUE / unrecoverable (`trades`+`tbbo`): 1,032,672 (60.69%)** — by venue: CME/trades 886,744 · NYSE/tbbo 54,639 ·
  NYSE/trades 54,639 · NASDAQ/trades 14,873 · NASDAQ/tbbo 13,853 · CME/tbbo 7,924.
- Potentially duplicated (L0 bars/chains): 668,750 (39.31%) — but see below, duplication is **partial, not total**.

## Even the L0 slice is not safely duplicated

Per-object comparison over 5 sampled days (8,375 Massive vs 2,136 Databento objects) found **5 exact path-identity
matches**. Massive routinely covers a _broader_ instrument universe than Databento on the same shard:

| day        | venue | data_type       | massive | databento |
| ---------- | ----- | --------------- | ------: | --------: |
| 2023-05-23 | CME   | `options_chain` |   3,692 |         9 |
| 2023-05-23 | NYSE  | `ohlcv_1m`      |     258 |       156 |
| 2023-05-23 | CME   | `ohlcv_1m`      |     541 |        88 |

Naming conventions differ (Massive combos carry garbage numeric roots like `underlying=12`; Databento carries
`underlying=AUDUSD`), so exact-path identity **understates** true content overlap. The honest statement is: **L0
duplication is partial and UNVERIFIED at content granularity.** A partial purge restricted to L0 would still require
per-object content verification that has not been done — and the migrate tool cannot express a shard-scoped purge
anyway.

## Separate data-correctness defect — 16,389 phantom manifest rows

The availability manifest asserts Databento coverage that does not physically exist:

- **16,389** rows with `pipeline_mode=batch_databento`, `data_type ∈ {trades, tbbo}`, `capture_status=captured`
- spanning **3,488** distinct `(venue, data_type, date)` shards
- backed by **ZERO** objects on disk (verified on a 13-shard stratified sample: databento-on-disk = 0 for every one; an
  L0 control group of 4 shards correctly showed 83–158 objects each)

Worked example — `CME/trades/2023-09-12`: manifest says `batch_databento captured` ×1, but a full listing of that day's
`batch_databento` prefix returns 599 objects of which **0** are `trades`/`tbbo`.

**Why this is dangerous beyond the purge:** a naive "is it duplicated in Databento?" check driven off the manifest would
have classified ~826,159 Massive objects as safe-to-delete. That is the exact shape of a silent million-object data-loss
event. This is a `record_captured` honesty violation (`codex/02-data/data-pipeline-correctness-hard-rule.md`) and these
rows should be re-stamped `expected_unattempted` / `empty_confirmed`.

> ⚠️ Note the write-side interaction: per the 2026-07-20 operator ruling, `source='massive'` now hard-rejects at the UTL
> manifest writer. Any job re-stamping these rows must not re-write the legacy `batch_massive` rows.

## BLOCKED-CREDENTIALS — the precise entitlement ask

Per `codex/02-data/external-data-always-available-rule.md`, exhausting the free path is a **credential ask, not a
descope**. To unblock the purge, exactly one of:

- **A (recommended)** — a Databento **historical `trades` + `tbbo` entitlement** (or a budgeted metered PAYG
  authorization) for:
  - `GLBX.MDP3` (CME) — `trades` + `tbbo`, **2020-01-01 → 2025-07-20**
  - `DBEQ.BASIC` (NASDAQ + NYSE) — `trades` + `tbbo`, **2023-04-15 → 2025-07-20** (2023-04-15 = DBEQ.BASIC equity
    archive floor)

  Then raise `LEVEL_MAX_LOOKBACK_DAYS["L1"]` for the authorized window, backfill, verify, and the purge becomes safe.

- **B** — accept Massive as the permanent archive of record for historical `trades`/`tbbo`, and **retain** those
  1,032,672 objects indefinitely. `batch_massive` `PipelineMode` + `possible_manifest` READ recognition must then stay
  permanently (today they are documented as "kept until the purge").

- **C** — operator accepts the permanent loss of all historical tradfi `trades`/`tbbo` and authorizes the full purge in
  writing. **Not recommended** — this is the data-pipeline-correctness heartbeat.

## What was NOT done, deliberately

- **No purge, no deletes, no sentinel.** Nothing destructive was executed.
- **No backfill VMs launched.** The only in-window recoverable shard is `CBOE/ohlcv_15m/2024-01-02` (**1 object**), and
  it is derivable by downstream aggregation from Databento's already-captured L0 `ohlcv_1m` for that date — no vendor
  fetch needed. Launching the tradfi fleet to recover 1 object would not change the purge verdict, so it was not spent.
- Bucket soft-delete policy verified **ACTIVE, 604800s (7 days)** — recorded for whenever a purge is eventually
  authorized.

## Follow-up todos

- [ ] [BACKEND] P0. Re-stamp the 16,389 phantom `batch_databento` trades/tbbo `captured` rows to an honest status; add a
      manifest-vs-disk consistency check so a `captured` row with no object on disk fails loudly. (repo:
      market-tick-data-service)
- [ ] [OPERATOR] P0. Decide the entitlement ask A / B / C above. Purge stays HELD until then.
- [ ] [DOCS] P1. If B is chosen, update `codex/02-data/tradfi-databento-sourcing-ssot.md` — `batch_massive` read
      recognition becomes PERMANENT, not "kept until the purge".
