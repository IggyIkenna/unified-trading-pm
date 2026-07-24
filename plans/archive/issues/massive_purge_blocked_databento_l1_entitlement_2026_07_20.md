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
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
resolved_by:
  "operator-decision (Option C, accepted-permanent-loss, PM@1cc566db6) + executed purge 2026-07-20
  RUN_TS=20260720-193849 (1,701,422 batch_massive objects removed, 0 collateral); slot-1 tick 26"
tags:
  [massive-purge, databento, entitlement, data-correctness, manifest, phantom-rows, blocked-credentials, honest-absence]
related:
  [
    tradfi_canonical_path_migration_design_2026_07_19,
    tradfi_consolidated_closeout_2026_07_18,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
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
---

# Massive purge BLOCKED — the Massive `trades`/`tbbo` corpus is the ONLY copy

## 2026-07-20 RESOLVED (slot-1, tick 26) — purge EXECUTED and VERIFIED, 0 collateral

**The authorized massive-only purge ran to a clean terminal state.** `RUN_TS=20260720-193849`, 20-shard fan-out on
`launch-canonical-migration-vm.sh` with the fixed gated purge path (`TRADFI_PURGE_MASSIVE_ONLY=1`,
`MTDS_TARBALL_SHA=1bdbb4e0` — carries the data-loss fix `5581dcf9` + honest docstring `8d7743cb` + P0 image fix
`21733255`), sentinel staged VM-side at
`gs://deployment-scripts-central-element-323112/canonical-migration-tradfi/sentinels/massive_purge_authorization_2026_07_20.sentinel`.

**Zero-collateral BY CONSTRUCTION**: each VM built a `pipeline_mode=batch_massive`-grep-filtered enumeration, so
non-massive objects were never in the input. Pre-flight local dry-run canary over a sample proved the filtered enum
classifies **100% PURGE_MASSIVE, 0 ORPHAN, 0 other disposition**.

**Terminal evidence (all 20 shards):**

- **1,701,414 objects PURGED** (sum of per-shard `apply COMPLETE — outcomes: {'PURGED': N}`; ~84.4k–85.5k per shard),
  all rc=0, **0 `PURGE_REFUSED_GATED`, 0 ORPHAN** on every shard.
- **+8 `QUARANTINE_CORRUPT` stragglers**: 8 `batch_massive` objects whose path carries a reordered/corrupt Hive shape
  (e.g. `data_type=…/instrument_type=…/venue=…` order + colon-bearing stem) classify QUARANTINE _before_ the
  `batch_massive` branch in `_classify_disposition`, so with `--quarantine` OFF they were left in place. 1,701,414 PURGE
  - 8 QUARANTINE = **1,701,422** = the full physical enumeration. The 8 (all `day=2024-01-01`/`2024-01-02`, all
    unambiguously `pipeline_mode=batch_massive`, operator-authorized scope) were then **deleted directly**
    (`gcloud storage rm`, each verified `batch_massive`), reaching **batch_massive → 0**.

**Phase-2 verification (measured):**

| day        | massive before → after | databento before → after (UNCHANGED) |
| ---------- | ---------------------- | ------------------------------------ |
| 2020-06-15 | 542 → **0**            | 191 → 191                            |
| 2021-06-15 | 539 → **0**            | 187 → 187                            |
| 2022-06-15 | 556 → **0**            | 189 → 189                            |
| 2023-05-23 | 5,360 → **0**          | 597 → 597                            |
| 2024-06-17 | 777 → **0**            | 612 → 612                            |
| 2025-04-08 | 759 → **0**            | 599 → 599                            |
| 2024-01-01 | (stragglers) → **0**   | 57 present                           |
| 2024-01-02 | (stragglers) → **0**   | 1,364 present                        |

- **Zero collateral**: every sampled `batch_databento` count IDENTICAL before/after; `_quarantine/` intact (146,288
  objects, never touched — the 8 stragglers were deleted, not moved); no `_quarantine/`/`batch_databento` object was in
  any delete operation.
- **Reversible**: bucket soft-delete confirmed ACTIVE `retentionDurationSeconds=604800` (7d) after the purge —
  restorable until ~2026-07-27.
- All 20 GCE VMs self-deleted (`VM_SHUTDOWN_ON_COMPLETION=true`).

**Ships that made this correct + honest:** `market-tick-data-service@8d7743cb` (sentinel docstring =
operator-auth-basis, not backfill-only), `deployment-service@2c00c740` (launcher: REJECT silently-dropped
`MIGRATION_EXTRA_ARGS` for `cat=tradfi` + add the gated `TRADFI_PURGE_MASSIVE_ONLY=1` migrate-pass-only path).

## Manifest cleanup (phantom rows + stale massive slice) — STILL OPEN, needs coordinated rebuild

The purge removed the OBJECTS; the availability manifest still carries the stale rows and is being actively rebuilt by a
peer. **Measured post-purge manifest baseline (2026-07-20):** 5,209,585 rows — **686,005 `batch_massive` rows** (objects
now gone) + **16,389 phantom `batch_databento` trades/tbbo `captured` rows** (zero backing objects) + 35.5% blank
`instrument_id` + 0% derivative `-USD@LIN`. **A `consolidate(force=True)` does NOT drop these** — the consolidator
re-scans 100% of the canonical on a full rebuild and a pure DELETION correction "survives trivially" (the documented
deletion-resurrection gap, `manifest_consolidator.py:850-862`). See
`tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md`. Dropping (a)+(b) needs surgical index removal; fixing
(c)+(d) needs the object-walk id re-derivation (`rebuild_tradfi_manifest.py`). Both target a LIVE index a peer is
already rebuilding — coordinate before cutover.

## 2026-07-20 UPDATE (slot-1, tick 25) — authorization GRANTED, but execution BLOCKED on a broken launcher path

**The entitlement blocker below is RESOLVED BY OPERATOR DECISION** (Option C, accepted-permanent-loss) — recorded at
`unified-trading-pm@1cc566db6`. Option A declined, Option B declined. So the _authorization_ question is closed.

**The purge still did NOT run**, because a pre-flight audit of the prescribed execution path found it would do the WRONG
THING destructively. See `tradfi_canonical_migration_launcher_drops_extra_args_2026_07_20.md`. In short:

1. `launch-canonical-migration-vm.sh`'s `tradfi` branch **silently discards `MIGRATION_EXTRA_ARGS`** — so
   `--purge-massive --massive-backfill-verified <sentinel>` never reach the migrate pass. **Zero massive objects would
   be purged.**
2. That same invocation in `full` mode runs the 3-pass canonical migration with `--apply` (+ `--quarantine` on passes
   2/3) over the WHOLE tradfi estate — copy→verify→**delete source** for every non-canonical NON-massive object. That is
   a large unauthorized content migration of exactly the `batch_databento` objects the zero-collateral check exists to
   protect.
3. Independently: the sentinel is checked with `Path(...).is_file()` **on the VM**, so a sentinel written in the repo /
   on the operator laptop does not satisfy the gate — it must be staged onto the VM at the path passed.

Net: the prescribed command would have purged nothing and migrated everything. **Nothing destructive was executed.**

**Shipped anyway (safe, correct regardless):** `market-tick-data-service@8d7743cb` — the `--massive-backfill-verified`
help/docstring + the mapping-manifest target string now describe the gate honestly as an
**operator-authorization-basis** sentinel (a completed backfill **OR** an explicit accepted-loss ruling), instead of
implying a backfill that never happened and never will.

**Measured baseline for the eventual purge (read-only, 2026-07-20):** bucket soft-delete **ACTIVE**,
`retentionDurationSeconds=604800` (7 days). `raw_tick_data/by_date/` holds **2,041** prefixes (2,040 `day=` + 1 legacy
`day-2026-01-01`). Stratified per-day counts — massive/databento/total-parquet: `2020-06-15` 542/191/733 · `2021-06-15`
539/187/726 · `2022-06-15` 556/189/745 · `2023-05-23` 5,360/597/5,957 · `2024-06-17` 777/612/1,389 · `2025-04-08`
759/599/1,358. **On every sampled day `massive + databento == total_parquet` exactly** — the two modes are cleanly
separable at path level with no third mode, so a `pipeline_mode=batch_massive`-filtered enumeration makes
zero-collateral provable BY CONSTRUCTION (non-massive objects are simply not in the input).

## Verdict (original, 2026-07-20 — superseded on the authorization axis only)

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
event. This is a `record_captured` honesty violation (`/codex/02-data/data-pipeline-correctness-hard-rule.md`) and these
rows should be re-stamped `expected_unattempted` / `empty_confirmed`.

> ⚠️ Note the write-side interaction: per the 2026-07-20 operator ruling, `source='massive'` now hard-rejects at the UTL
> manifest writer. Any job re-stamping these rows must not re-write the legacy `batch_massive` rows.

## BLOCKED-CREDENTIALS — the precise entitlement ask

Per `/codex/02-data/external-data-always-available-rule.md`, exhausting the free path is a **credential ask, not a
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
- [ ] [DOCS] P1. If B is chosen, update `/codex/02-data/tradfi-databento-sourcing-ssot.md` — `batch_massive` read
      recognition becomes PERMANENT, not "kept until the purge".
