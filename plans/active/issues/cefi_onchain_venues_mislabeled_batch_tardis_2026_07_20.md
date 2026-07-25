---
doc_type: issue
title:
  "CeFi on-chain venues under pipeline_mode=batch_tardis — EXTENDED-STARKNET carries 35,882 objects of FABRICATED Tardis
  provenance (fully duplicating the native lane with DIFFERENT content); LIGHTER/PACIFICA are separate, smaller cases"
summary:
  Investigated the premise that EXTENDED-STARKNET / LIGHTER-ZKSYNC / PACIFICA-SOLANA are on-chain venues wrongly
  partitioned under pipeline_mode=batch_tardis. The premise holds for ONE venue and is WRONG for the others.
  EXTENDED-STARKNET is machine-verified NOT a Tardis exchange yet has 35,882 objects under batch_tardis (2026-01-01 →
  ~2026-06-04) that DUPLICATE all 67 native batch_extended instruments with DIFFERENT content (differing md5 + size),
  plus 28 instruments and an entire ohlcv_1m data_type present ONLY in the fabricated lane. LIGHTER-ZKSYNC IS a real
  Tardis exchange (slug "lighter", coverage from 2026-04-17) so its post-cutover batch_tardis objects are CORRECTLY
  labelled — only a ~1k-object pre-2026-02 ohlcv_1m tail is mis-stamped. PACIFICA-SOLANA is a dropped venue (source
  removed 2026-07-16, zero manifest rows) and is a quarantine, not a re-partition (CORRECTED — see C3 below; the sibling
  finding + the cefi consolidated-closeout plan's tracked disposition both land on quarantine, not purge).
  Recommendation is NOT a blanket re-partition — it is per-venue, and EXTENDED needs CONTENT reconciliation before any
  object move.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, unified-api-contracts]
scope: [engineer, admin]
tags: [pipeline-mode, canonical-path, manifest, data-correctness, provenance, duplicate-objects, catalogue-gap, tardis]
related:
  [
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-20
priority: P1
parent_epic: cefi_master
source:
  "Track B investigation — cefi on-chain venue pipeline_mode audit, 2026-07-20 (measured against prod GCS +
  availability_index)"
execution_scope: local-only
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
last_updated: 2026-07-20
---

# CeFi on-chain venues under `pipeline_mode=batch_tardis`

> **Scope note.** This doc is an INVESTIGATION result, not a migration authorisation. No GCS object was written, moved
> or deleted; no manifest row was touched. Every number below is measured against prod
> (`market-data-tick-cefi-prd-central-element-323112` + its `_index/availability_index.parquet`, 10,263,779 rows, pulled
> 2026-07-20).

## TL;DR — the premise is one-third right

| Venue                 | Verdict                                                                      | Scale                                 | Disposition                               |
| --------------------- | ---------------------------------------------------------------------------- | ------------------------------------- | ----------------------------------------- |
| **EXTENDED-STARKNET** | 🔴 **CONFIRMED mislabel + full content-divergent DUPLICATION**               | **35,882 objects** under batch_tardis | Reconcile CONTENT first, then dispose     |
| **LIGHTER-ZKSYNC**    | 🟡 **Mostly CORRECT** — Tardis genuinely archives this venue from 2026-04-17 | ~1,050-object legacy ohlcv_1m tail    | Small re-partition to `batch_lighter_api` |
| **PACIFICA-SOLANA**   | 🟢 **Not a lane problem** — venue DROPPED 2026-07-16, zero manifest rows     | ~5 objects/day, 2025-07 → 2025-12     | Quarantine, not re-partition or purge     |

The framing "three on-chain venues mislabeled as batch_tardis" merges three unrelated causes. Treating them as one
migration would move correctly-labelled Tardis data (LIGHTER), resurrect a deliberately-dropped venue (PACIFICA), and
paper over a content-divergence problem (EXTENDED) that an object move cannot fix.

---

## 1. Empirical confirmation

### 1.1 Which `pipeline_mode` partitions actually hold these venues' objects

Probed by direct prefix listing (`day=<D>/pipeline_mode=<M>/asset_group=cefi/venue=<V>/`), counting `.parquet` leaves.
Object counts per day:

| Day        | EXTENDED `batch_extended` | EXTENDED `batch_tardis` | LIGHTER `batch_lighter_api` | LIGHTER `batch_tardis` | PACIFICA `batch_tardis` |
| ---------- | ------------------------- | ----------------------- | --------------------------- | ---------------------- | ----------------------- |
| 2025-07-15 | —                         | —                       | —                           | 5                      | 2                       |
| 2025-08-15 | 46                        | —                       | —                           | 5                      | 4                       |
| 2025-10-15 | 59                        | —                       | —                           | 5                      | 5                       |
| 2025-11-05 | 60                        | —                       | —                           | 5                      | 5                       |
| 2025-12-28 | 61                        | **—**                   | —                           | 5                      | 5                       |
| 2026-01-02 | 61                        | **134**                 | —                           | 5                      | —                       |
| 2026-01-15 | 62                        | 136                     | —                           | 5                      | —                       |
| 2026-02-15 | 64                        | 156                     | **5**                       | —                      | —                       |
| 2026-04-10 | 67                        | 190                     | 5                           | —                      | —                       |
| 2026-04-17 | 67                        | 192                     | 5                           | **130**                | —                       |
| 2026-05-01 | 69                        | 198                     | 5                           | 134                    | —                       |
| 2026-06-01 | 69                        | **203**                 | —                           | 145                    | —                       |
| 2026-06-05 | 69                        | **—**                   | —                           | 149                    | —                       |
| 2026-07-15 | 134                       | —                       | —                           | —                      | —                       |

Bolded cells are the window boundaries, bisected to the day.

**Measured windows:**

- **EXTENDED-STARKNET `batch_tardis`: 2026-01-01 (±1d) → ~2026-06-04 (±3d).** Total **35,882 objects** (full
  `day=*/pipeline_mode=batch_tardis/.../venue=EXTENDED-STARKNET/**` enumeration). Absent before and after.
- **EXTENDED-STARKNET `batch_extended`**: continuous from 2025-07 to present — i.e. the two lanes **OVERLAP** for the
  entire batch_tardis window. This is duplication across lanes, not a temporal handover.
- **LIGHTER-ZKSYNC**: `batch_tardis` at 5 obj/day (2025-07 → ~2026-01, `ohlcv_1m`) → `batch_lighter_api` at 5 obj/day
  (~2026-02 → ~2026-05, `ohlcv_1m`) → `batch_tardis` at 130-150 obj/day **starting exactly 2026-04-17**
  (`derivative_ticker`). Two distinct lanes for two distinct data_types.
- **PACIFICA-SOLANA**: `batch_tardis` only, 2-5 obj/day `ohlcv_1m`, ending ~2025-12/2026-01. Never appeared under any
  other mode.

### 1.2 Is the data duplicated, or solely mislabeled?

**EXTENDED-STARKNET is duplicated — and the duplicates DISAGREE.** On `day=2026-04-15`,
`instrument_type=perpetual/data_type=derivative_ticker`:

```
batch_tardis stems:  95     batch_extended stems:  67
OVERLAP (same stem in BOTH lanes):  67
tardis-ONLY:  28            native-ONLY:  0
```

`batch_extended` is a strict **subset** of `batch_tardis`. The 28 tardis-only stems are Extended's equity/pre-IPO perps
(`AAPL_24_5-USD@LIN`, `AMD_24_5-USD@LIN`, `AMZN_24_5-USD@LIN`, `1000BONK-USD@LIN`, …). The fabricated lane also carries
a data_type the native lane did not have at the time — on 2026-04-15 it is 95 `derivative_ticker` **+ 95 `ohlcv_1m`**,
while `batch_extended` was `derivative_ticker`-only until ~2026-07 (2026-07-15 shows 67 `derivative_ticker` + 67
`trades`).

The overlapping objects are **not byte-identical**. Same logical shard (`day=2026-04-15`, `EXTENDED-STARKNET`,
`perpetual`, `derivative_ticker`, `AAVE-USD@LIN`):

| Lane             | size  | md5                        | crc32c     |
| ---------------- | ----- | -------------------------- | ---------- |
| `batch_tardis`   | 6,888 | `rNl1RiYtrBpHfFe5GIew8Q==` | `FivwCw==` |
| `batch_extended` | 8,951 | `hHPf6mgfuJK1vEq98q+y+g==` | `rlmo/Q==` |

This rules out the benign explanation (a v9 COPY-migration twin). These are **two independent writes of the same shard
with different content**, which means the question "which lane is authoritative?" is open and an object move cannot
answer it.

**LIGHTER-ZKSYNC is NOT duplicated** — the two lanes carry disjoint data_types (`ohlcv_1m` native vs `derivative_ticker`
Tardis) and are temporally disjoint per data_type.

**PACIFICA-SOLANA is NOT duplicated** — single lane, and it has **zero rows in the availability manifest** (see 1.3), so
its objects are unmanifested residue.

### 1.3 Manifest cross-check (`_index/availability_index.parquet`)

`capture_status` breakdown for the four cefi on-chain CLOB venues:

```
EXTENDED-STARKNET  batch_extended     captured  22,364   empty_confirmed  67,682
                   batch_tardis       captured   1,107   empty_confirmed   4,717   expected_unattempted  55,760
LIGHTER-ZKSYNC     batch_lighter_api  captured     475
                   batch_tardis       captured       0   empty_confirmed  42,193   expected_unattempted 120,538
HYPERLIQUID        batch_hyperliquid  captured  84,544   ...
                   batch_tardis       captured       0   empty_confirmed   7,102   expected_unattempted  93,056
ASTER              batch_aster        captured 115,767   ...
                   batch_tardis       captured       0   empty_confirmed  68,986   expected_unattempted 163,104
PACIFICA-SOLANA    (no rows at all)
```

Three things fall out:

1. **The large `batch_tardis` row counts for these venues are honest-absence bookkeeping, not data.** LIGHTER, ASTER and
   HYPERLIQUID have **zero** `captured` rows under `batch_tardis` — those 162k / 232k / 100k rows are
   `empty_confirmed` + `expected_unattempted`. ASTER and HYPERLIQUID are the workspace's _correctly_-labelled reference
   venues and they exhibit the identical pattern, which confirms it is the expected `cefi → BATCH_TARDIS` asset_group
   fallback used when stamping absence rows — **not** a mislabel. A manifest-only audit would have flagged all four
   venues and been wrong about three of them.
2. **EXTENDED's manifest and its objects diverge badly.** The manifest records 1,107 `captured` rows under
   `batch_tardis`; GCS holds **35,882 objects**. ~97% of the fabricated lane is **unmanifested** — invisible to coverage
   accounting, phantom-audit and data-status alike.
3. **The 1,107 manifested rows carry `source=tardis`.** The provenance fabrication reached the manifest, not just the
   path key.

---

## 2. Root cause

### 2.1 What the `{mode}_{source}` convention requires

Per [`/codex/02-data/pipeline-mode-partition.md`](/codex/02-data/pipeline-mode-partition.md) §"Source-aware modes +
transport", `pipeline_mode = {mode}_{source}[_{transport}]` where **`source` is the VENDOR only**. The doc's own
anti-pattern list forbids gluing transport into the source and requires every batch `PipelineMode` to round-trip with a
`SOURCE_PRIORITY` entry.

The question the task poses — _do these on-chain venues have a vendor at all?_ — is answered **yes**, and the registry
already answers it per venue. These are not vendorless: a **self-archiving venue is its own vendor** (the ratified
`hyperliquid` / `aster` pattern). UAC registers exactly that:

- `extended` → `PipelineMode.BATCH_EXTENDED` (`pipeline_mode.py:111`)
- `lighter_api` → `PipelineMode.BATCH_LIGHTER_API` (`pipeline_mode.py:119`)
- `pacifica` → **removed 2026-07-16** (`pipeline_mode.py:120-124`), venue dropped by operator ruling.

So the correct mode is **`batch_extended`** for EXTENDED, **`batch_lighter_api`** for LIGHTER's native `/candles`
`ohlcv_1m`, and — critically — **`batch_tardis` IS correct** for LIGHTER's `derivative_ticker`/`trades`/`book`, because
Tardis genuinely archives that venue.

### 2.2 Machine-verified: which venues are actually Tardis exchanges

Evaluated against the live UAC registry (`VenueMapping`):

```
all_tardis_exchanges: binance, binance-delivery, binance-futures, bitfinex, bitfinex-derivatives,
                      bitget, bitget-futures, bybit, bybit-spot, coinbase, coinbase-international,
                      cryptofacilities, deribit, kraken, lighter, okex, okex-futures, okex-swap, upbit

EXTENDED-STARKNET: tardis_exchange=None      →  NOT a Tardis exchange
LIGHTER-ZKSYNC:    tardis_exchange='lighter' →  IS a Tardis exchange
PACIFICA-SOLANA:   tardis_exchange=None      →  NOT a Tardis exchange
ASTER:             tardis_exchange=None
HYPERLIQUID:       tardis_exchange='hyperliquid'
```

`unified_api_contracts/registry/venue_mapping.py:78-82, 219-222, 929` documents the LIGHTER mapping explicitly:
_"Lighter (zkSync L2) — Tardis coverage from 2026-04-17. Pre-2026-04-17 falls through to REST /candles in MTDS adapter.
Tardis exchange slug is `lighter` (confirmed via /v1/exchanges/lighter)."_ The measured lane-switch date **2026-04-17
matches this to the day** — strong independent corroboration that LIGHTER's post-cutover `batch_tardis` objects are
correct.

`unified_api_contracts/canonical/crosscutting/_source_priority_data.py:548-552` states for EXTENDED: _"uses its own
public REST API (api.starknet.extended.exchange) — **NOT Tardis-archived**."_ Therefore **all 35,882 `batch_tardis`
EXTENDED objects assert a provenance that cannot exist.**

### 2.3 The defect that produced it — file:line

**`unified-trading-library/unified_trading_library/pipeline_mode_resolver.py:39-99`** — the `_VENUE_OVERRIDES` map is
keyed by venue string, and both lookup sites normalise with `venue.upper().replace("-", "_")`:

- `pipeline_mode_resolver.py:186` — `normalized = venue.upper().replace("-", "_")` (write-time `resolve_pipeline_mode`)
- `pipeline_mode_resolver.py:307` — same normalisation (`derive_pipeline_mode_for_row`, the backfill/manifest path)

The override key was originally the **hyphenated** `"EXTENDED-STARKNET"`, which can never match the
underscore-normalised lookup. The in-code confession at **`pipeline_mode_resolver.py:56-61`** states it plainly:

> _"KEY MUST BE UNDERSCORE-NORMALIZED (2026-07-18): both lookup sites normalize the venue via
> `venue.upper().replace("-", "_")`, so "EXTENDED-STARKNET" → "EXTENDED_STARKNET"; the old hyphenated key NEVER matched
> and rows silently fell through to batch_tardis (fabricated Tardis provenance on a self-archived venue)."_

The fall-through lands at **`pipeline_mode_resolver.py:345-354`**:

```python
_ASSET_GROUP_FALLBACKS: dict[str, PipelineMode] = {
    "cefi": PipelineMode.BATCH_TARDIS,
    ...
}
```

Every cefi venue without a matching override silently becomes `batch_tardis`. The failure mode is **silent fabrication,
not an error** — which is why 35,882 objects accumulated for five months unnoticed.

**The same class hit LIGHTER** (`pipeline_mode_resolver.py:62-68`): a dead `"LIGHTER"` key that never matched
`"LIGHTER_ZKSYNC"`, removed 2026-07-18 and replaced by a source-blind honest-absence guard at
`pipeline_mode_resolver.py:325-326` returning `None` for `(LIGHTER_ZKSYNC, ohlcv_1m)` rather than fabricating.

### 2.4 Fix status — the fabrication path is CLOSED for EXTENDED, still OPEN for the general case

Verified by running the live resolver (`derive_pipeline_mode_for_row`, `source=None`):

```
EXTENDED-STARKNET  derivative_ticker  -> batch_extended     ✅
EXTENDED-STARKNET  ohlcv_1m           -> batch_extended     ✅
LIGHTER-ZKSYNC     derivative_ticker  -> batch_tardis       ✅ (correct — real Tardis archive)
LIGHTER-ZKSYNC     ohlcv_1m           -> None               ✅ (honest not-derivable)
PACIFICA-SOLANA    ohlcv_1m           -> batch_tardis       🔴 STILL FABRICATES
```

Two commits closed the EXTENDED path, and **both postdate the entire batch_tardis write window** (2026-01-01 →
~2026-06-04):

- `market-tick-data-service@356457c2` (2026-07-12) —
  `feat(cefi): wire PACIFICA-SOLANA/EXTENDED-STARKNET into OnchainPerpBatchHandler`, which pins
  `_VENUE_PIPELINE_MODE["EXTENDED-STARKNET"] = PipelineMode.BATCH_EXTENDED`
  (`market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py:127`).
- `unified-trading-library@08662724` (2026-07-18) — the underscore-key fix.

**No treadmill for EXTENDED**: the mis-stamping writer stopped ~2026-06-04, and no current code path can re-emit it. The
residue is a fixed, bounded historical set.

**Residual live defect (P2, in scope for this doc's remediation):** `PACIFICA-SOLANA` still resolves to `batch_tardis`
because `BATCH_PACIFICA` was removed without a corresponding guard — the generic `cefi` fallback catches it. The venue
is dropped so nothing writes today, but the fallback remains a fabrication generator for **any future cefi venue added
without an override**. The honest-absence guard pattern already used for LIGHTER (`pipeline_mode_resolver.py:325-326`)
is the shipped remedy; it should be generalised, or the `cefi → BATCH_TARDIS` fallback should fail loud for venues that
`VenueMapping` says are not Tardis exchanges.

**Adjacent smell (not a defect — documented workaround):**
`market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py:115-122` sets
`_VENUE_SOURCE["LIGHTER-ZKSYNC"] = "tardis"` with the comment that `"lighter"` is not a registered UAC source and fails
manifest-write validation. That means LIGHTER's **pre**-2026-04-17 honest-absence rows also assert `source=tardis` for a
period Tardis provably did not cover. Cosmetic today (absence rows, no objects), but it is the same fabrication shape
and should be resolved by registering the source rather than borrowing Tardis's name.

---

## 3. Blast radius of a re-partition

### 3.1 Path resolution — SAFE

`deployment-api/deployment_api/utils/storage_facade.py:46-51` codifies the contract: _"Readers PREFIX-MATCH `batch_*` /
`live_*` / `replay_*` — never the coarse literal."_ Confirmed by the regex at the same site
(`_PIPELINE_MODE_RE = re.compile(r"pipeline_mode=(?:batch|live|replay)_")`). Moving an object from `batch_tardis` to
`batch_extended` therefore **does not break reader path resolution** — both are `batch_*`.

### 3.2 Coverage accounting — SAFE, and the current duplication is NOT inflating it

`deployment-api/deployment_api/services/data_status/breakdowns_domain.py:392-408` de-duplicates on the shard atom
`(venue, data_type, instrument_id, date)` — **`pipeline_mode` is explicitly NOT part of the shard atom**, with an inline
comment that a raw `len()` would double-count a shard carrying both a batch and a live row. So:

- The EXTENDED duplication does **not** inflate today's honest-coverage numbers.
- A re-partition will **not** move the coverage number either — it is provenance hygiene, not a coverage fix.

Anyone proposing this work as a coverage improvement is mistaken; it should be justified on correctness grounds only.

### 3.3 Read-time source selection — 🔴 THE SHARP EDGE

`unified_api_contracts/canonical/crosscutting/_source_priority_data.py:149`:

```python
("cefi", "derivative_ticker"): ["tardis", "aster", "hyperliquid", "extended"],
```

**`tardis` is first.** For EXTENDED-STARKNET `derivative_ticker` in the 2026-01→2026-06 window, a consumer resolving by
`SOURCE_PRIORITY` will prefer the **fabricated** `batch_tardis` copy over the native `batch_extended` one — and the two
copies have different content. MTDS partially mitigates this: `market-tick-data-service/reader.py:836-838` lifts
`pipeline_mode` from the captured manifest row, and the manifest holds 22,364 `batch_extended` rows vs 369
`batch_tardis` `derivative_ticker` rows, so manifest-driven reads mostly land on the native copy.

**Not determined by this investigation:** whether any downstream artifact (MDPS candles, features) was actually derived
from the fabricated copy. That requires reading both parquets and diffing content, and is the first task of any
remediation.

### 3.4 Manifest implications

Manifest rows are keyed **including** `pipeline_mode`. A physical object move without a coordinated manifest rewrite
turns every moved row into a phantom. Two standing hazards apply:

- **Phantom-audit `--apply` hazard** (`/codex/02-data/pipeline-mode-partition.md` §"Why `--apply` is dangerous"): the
  Axis-10 class of bug. `ASSET_GROUP_CONFIG[ag]["prefix_tpls"]` must cover the new shape _before_ any `--apply`, or real
  `captured` rows flip to `attempted_failed`.
- **GCS delete-safety invariant** (same doc, 🔴 HARD RULE): never delete a legacy object without
  `gcs_describe_object`-verifying a canonical twin. Here the twin exists but is **content-divergent**, so the
  invariant's usual "twin verified ⇒ safe to delete" logic **does not apply unmodified** — byte-difference means
  deleting either copy loses data the other does not have.

### 3.5 Cost / mechanics

35,882 + ~1,050 objects is a small move by workspace standards (cf. the 2.35M-object tradfi migration). Mechanically
cheap; the expense is entirely in the content-reconciliation decision, not the copy.

### 3.6 Dependency on the catalogue-gap work — 🔴 SEQUENCING CONSTRAINT

EXTENDED-STARKNET is one of the 0%-catalogue-resolve venues (26,721 objects in the census; the batch_tardis lane
measured here at 35,882 is the larger figure, suggesting the census scoped a subset). The 28 tardis-only instruments are
precisely the exotic equity/pre-IPO perps (`AAPL_24_5-USD@LIN`, `AMD_24_5-USD@LIN`) most likely to be **absent from the
rolled-up catalogue** that `_cefi_canonical_resolver_migration_2026_07_18.py` builds its maps from.

**Re-partitioning before the catalogue gap closes would move objects that still resolve to nothing** — two touches of
the same objects, and the second (a rename/canonicalisation pass) would have to re-walk the moved prefixes. The
catalogue gap must close **first**, or at minimum the two passes must be bundled into a single object rewrite.

---

## 4. Options + recommendation

### Option A — Blanket re-partition all three venues out of `batch_tardis` ❌ NOT RECOMMENDED

Rejected on the evidence. It would move LIGHTER's post-2026-04-17 `derivative_ticker` objects, which are **correctly**
labelled (Tardis genuinely archives `lighter`), actively _introducing_ a mislabel. It would also treat EXTENDED's
content divergence as a naming problem, silently picking a winner between two disagreeing copies.

### Option B — Accept `batch_tardis` as a historical artifact, document, move on ❌ NOT RECOMMENDED

Cheap and non-destructive, and defensible for a pure naming wart. But it does not survive contact with two facts: (i)
`SOURCE_PRIORITY` puts `tardis` first, so the fabricated copy is _preferentially selected_ by read-time source
resolution (§3.3) — this is a live read-path hazard, not a cosmetic one; and (ii) ~97% of the lane is **unmanifested**,
so "documented artifact" would leave 34,775 objects invisible to every audit surface. The data-pipeline-correctness HARD
RULE does not permit parking a known provenance fabrication of this size.

### Option C — Per-venue disposition, content reconciliation before any move ✅ **RECOMMENDED**

Treat the three venues as the three separate problems they are, sequenced behind the catalogue gap.

**C1 — EXTENDED-STARKNET (P1, blocked on catalogue gap).** The object move is the _last_ step, not the first.

1. **Reconcile content before deciding anything.** Read both copies for a stratified sample (≥3 days × ≥10 instruments
   spanning the window) and characterise the divergence: row counts, column sets, time ranges, value agreement on
   overlapping timestamps. The size asymmetry (6,888 vs 8,951 bytes) suggests different row counts or schema, not noise.
2. **Determine the authoritative copy per (data_type, window).** Note the fabricated lane is the **richer** one — it has
   28 more instruments and an entire `ohlcv_1m` data_type. "Delete the fake-provenance lane" would therefore **destroy
   data that exists nowhere else**. The likely correct outcome is _keep the content, fix the label_.
3. **Then** re-partition the surviving objects to `pipeline_mode=batch_extended` with a coordinated manifest rewrite,
   bundled with the catalogue-gap canonicalisation pass so the objects are touched once.
4. Backfill the ~34,775 unmanifested objects into the availability manifest (or prove them redundant), so the lane stops
   being invisible.
5. Gate: `prefix_tpls` verified to cover the new shape, `--dry-run` phantom count zero, before any `--apply`.

**C2 — LIGHTER-ZKSYNC (P2, independent, small).** Re-partition **only** the pre-~2026-02 `ohlcv_1m` objects (~5/day ×
~210 days ≈ 1,050) from `batch_tardis` to `batch_lighter_api`, matching what the native `/candles` adapter already
writes post-2026-02. **Leave every `derivative_ticker` object under `batch_tardis` untouched** — it is correct.
Unambiguous, no content divergence, no catalogue dependency.

**C3 — PACIFICA-SOLANA (P3, quarantine not migration or purge — CORRECTED 2026-07-25).** The venue was dropped by
operator ruling 2026-07-16, its UAC source was removed, and it has zero manifest rows. Re-partitioning would mean
inventing a `batch_pacifica` mode that was deliberately deleted. **This doc originally recommended routing these objects
to the purge path (`purge_drift_pacifica_solana_perp_2026_07_16.py`); that recommendation conflicted with the sibling
finding `/plans/active/issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` (same venue, same 2026-07-20
investigation window), which recommends QUARANTINE (register in the fail-hard quarantine set, keep the data, do not
delete) — orphan data from a culled venue, not a re-partition target.** The corpus has since converged on quarantine as
the tracked disposition: `plans/active/cefi_consolidated_closeout_2026_07_18.md` carries the open todo "Register
PACIFICA-SOLANA (265) in the fail-hard quarantine set" (also re-extracted into
`plans/active/cefi_4surface_migration_execution_log_2026_07_24.md` and indexed in
`plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`), dated 4 days after this doc and never
mentioning a purge. Follow that todo instead of the purge script — no `--apply`/deletion of these objects without a
fresh, explicit operator decision reopening the purge-vs-quarantine question.

**C4 — Close the residual live defect (P2, code-only, no data).** Make the `cefi → BATCH_TARDIS` asset_group fallback at
`pipeline_mode_resolver.py:346` **fail loud** (or return `None`) for any venue that `VenueMapping` reports is not a
Tardis exchange, generalising the LIGHTER honest-absence guard at `pipeline_mode_resolver.py:325-326`. This is the only
change that prevents the _next_ venue from silently repeating the whole incident. Ship independently of the data work.

**Recommended sequencing:** C4 (no dependencies, prevents recurrence) → C2 (small, independent) → C3 (quarantine
registration, no deletion — see corrected C3 above) → C1 (behind the catalogue gap, bundled with its canonicalisation
pass).

---

## 5. What this investigation did NOT establish

Stated explicitly so no downstream reader over-reads the evidence:

- **Which EXTENDED copy is authoritative.** Confirmed only that they differ (md5 + size on a sampled shard). No parquet
  content was read.
- **Whether any downstream artifact consumed the fabricated copy.** `SOURCE_PRIORITY` makes it _reachable_ and
  _preferred_ (§3.3); no MDPS/features lineage was traced.
- **Which specific job wrote the 35,882 objects.** The _mechanism_ is established (hyphen-key normalisation mismatch →
  cefi fallback → `BATCH_TARDIS`, confessed in-code at `pipeline_mode_resolver.py:56-61`) and the window is bounded, but
  the producing run/VM was not identified.
- **Exact boundary dates.** Bisected to ±1d (start) and ±3d (end). Sufficient for scoping, not for a date-parameterised
  migration — re-bisect before authoring one.
- **Whether the census's 26,721 EXTENDED figure and this doc's 35,882 measure the same set.** They differ; scope
  reconciliation is needed before either number is used as a migration denominator.

## 6. Codex SSOTs consulted

- [`/codex/02-data/pipeline-mode-partition.md`](/codex/02-data/pipeline-mode-partition.md) — `{mode}_{source}`
  convention, reader prefix-match rule, GCS delete-safety invariant, phantom-audit `--apply` hazard.
- [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) —
  4-state `capture_status`, shard-atom definition.
