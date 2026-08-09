---
doc_type: issue
title:
  Tardis "impossible combinations" (symbol not archived / date outside listing) return HTTP 400 and are recorded as
  attempted_failed — they corrupt the coverage denominator AND are retried forever
summary:
  Tardis answers two structurally-impossible requests with HTTP 400 + a distinguishing JSON code - code=300 "Invalid
  'symbol' param" (the symbol is not in Tardis's archive at all) and code=140 "Requested dataset is not available for
  <date>" (the symbol IS archived but the date is outside its availableSince..availableTo). Neither is a fetch failure,
  but tardis_csv_transport only treats 404 as honest absence and RAISES everything else, so the per-shard runner routes
  both to record_failed -> attempted_failed. That is in the honest-coverage denominator (so phantom combos permanently
  depress measured coverage) and it reads as retryable (so every future run re-requests known-impossible shards). The
  live VM walks 2020->2026 across 17 venues while e.g. bybit AAVEUSDT only lists from 2021-05-13 and AAVEPERP from
  2025-04-30, making code=140 a large systematic multiplier. Tardis's own catalog supplies the exact 3-tuple to gate on
  (symbol x dataTypes x availableSince..availableTo) - the fix is a vendor-catalog intersection, NOT a symbol mapping
  change (the mapping is correct - AAVEUSDC is a genuine Bybit symbol Tardis simply never archived).
status: open
resolved_by:
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, instruments-service]
scope: [engineer, admin]
tags:
  [cefi, tardis, honest-coverage, denominator, attempted-failed, impossible-combinations, data-correctness, big-finding]
related:
  [
    /plans/archive/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md,
    /plans/archive/issues/databento_default_executor_dns_starvation_risk_2026_07_17.md,
  ]
created: 2026-07-17
author: unknown
source:
  - Operator questions 2026-07-17 ("is it doing data that doesnt exist or is it just skipping", "why you looking for
    wrong symbol dont we have a converter / mapping", "is it the date (available for and to?)") - all three proved
    correct against live measurement; the date hypothesis in particular surfaced a class I had missed.
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
drift_direction: advance-code
parent_epic: cefi_master
depends_on: []
last_updated: 2026-07-17
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_csv_transport.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_batch_download.py,
    market-tick-data-service/scripts/reclass_cefi_tardis_impossible_combinations_400_2026_07_27.py,
    unified-api-contracts/unified_api_contracts/canonical/coverage_exclusions.py,
    /codex/02-data/honest-coverage-model.md,
  ]
---

# Tardis impossible combinations are recorded as `attempted_failed`

## Measured (live, 2026-07-17, real key, on the VM)

| request                                     | Tardis response                                                        | our status          |
| ------------------------------------------- | ---------------------------------------------------------------------- | ------------------- |
| `bybit/book_snapshot_5/2026-02-02/AAVEUSDC` | `400` **`code=300`** — _"Invalid 'symbol' param provided: 'AAVEUSDC'"_ | `attempted_failed`  |
| `bybit/trades/2020-01-02/AAVEUSDT`          | `400` **`code=140`** — _"Requested dataset is not available for …"_    | `attempted_failed`  |
| `bybit/trades/2026-02-02/AAVEUSDT`          | `302` -> Wasabi -> data                                                | `captured` ✓        |
| `bybit/trades/…/<empty day>`                | `200` + 0 rows ("Empty CSV")                                           | `empty_confirmed` ✓ |

Both 400s are **permanent, structural absences**, not fetch failures.

## Why it happens

`tardis_csv_transport.py:514-524` (CF-11, 2026-06-10) treats **only 404** as honest absence and RAISEs everything else
so the runner routes `record_failed` — a design aimed at 5xx/429 outages (correct for those). HTTP 400 was never
distinguished, so it inherits the outage path. `tardis_batch_download.py:237` then records `attempted_failed`; only the
literal `"Empty CSV"` string escapes to `record_zero_rows(SOURCE_RETURNED_ZERO)`.

`_classify_tardis_error` does a code-token extract + `classify_venue_error(venue, token)` lookup, but **UAC registers no
Tardis error codes at all** — so 300/140 fall through as raw tokens and the status is `attempted_failed` regardless.

## Why it matters (two harms, the second is worse)

1. **Denominator corruption.** `attempted_failed` sits in the honest-coverage denominator
   (`captured/(captured+attempted_failed+expected_unattempted)`), so every impossible combo permanently depresses
   measured coverage. This is exactly the class the operator ruled out of scope: _"its the literally impossible
   combinations i dont even need in empty confirmed"_.
2. **Infinite retry.** `attempted_failed` reads as retryable, so **every future run re-requests known-impossible
   shards**. This is the engine behind the measured **87% dud rate** (25 successes vs 95 HTTP 400 + 69 Empty CSV + 7 404
   in one run) and it never decays.

**Systematic multiplier**: the live VM walks **2020 -> 2026** across 17 venues, while bybit `AAVEUSDT` lists from
**2021-05-13** and `AAVEPERP` from **2025-04-30**. Every (symbol x pre-listing date x data_type) is a guaranteed
`code=140`.

**NOT a throughput lever**: duds resolve in milliseconds (6 in the same second, measured) and transfer no bytes. Fixing
this improves coverage ACCURACY and cuts wasted requests; it does not move MB/s. The MB/s fix was the dedicated parse
executor (`market-tick-data-service@2e7c2b5d`).

**NOT a mapping bug**: `AAVEUSDC` is a genuine live Bybit symbol (bybit `/v5/market/instruments-info` returns it).
instruments-service is right; Tardis simply archives a **subset** (1712 bybit symbols, `AAVEUSDC` absent — it has
`AAVEPERP`/`AAVEUSD`/`AAVEUSDT`). The universes differ; no converter can bridge that.

## The fix — intersect with the vendor catalog

`GET https://api.tardis.dev/v1/exchanges/<venue>` -> `datasets.symbols[]`, each carrying exactly the 3-tuple needed:

```json
{ "id": "AAVEUSDT", "type": "spot",
  "dataTypes": ["trades", "book_snapshot_5", ...],
  "availableSince": "2021-05-13T00:00:00.000Z",
  "availableTo": "2026-07-17T00:00:00.000Z" }
```

Gate every request on **symbol ∈ catalog** AND **data_type ∈ symbol.dataTypes** AND **availableSince <= date <=
availableTo**. Anything failing that is an impossible combination: never request it, never record a row for it, keep it
out of the denominator. One cheap cacheable call per venue (the endpoint Tardis's own 400 message points at).

## Todos

- [x] ✅ [CODE] P0. Gate the Tardis request universe on the vendor catalog (symbol x data_type x date-range). Cache the
      per-venue catalog; refresh daily. This is the operator's "impossible combinations" exclusion with the VENDOR as
      the authority — coordinate with the in-flight `coverage_exclusions` work in unified-api-contracts (another agent,
      live as of 2026-07-17). — **DONE**: `market-tick-data-service@8e406dbb` + `market-tick-data-service@07cafbbb`
      (2026-08-08) — new `tardis_vendor_catalog.py` gates every per-symbol request on Tardis's own
      `GET /v1/exchanges/<venue>` `datasets.symbols[]` catalog (symbol-in-catalog AND data_type-in-dataTypes AND
      availableSince<=date<=availableTo), fails open on any fetch/parse error, excluded combinations recorded as honest
      absence (never `attempted_failed`).
- [x] ✅ [CODE] P0. Stop recording impossible combos as `attempted_failed`. Distinguish by Tardis JSON code: `140`/`300`
      -> honest absence / excluded (NOT the denominator); keep 5xx/429/`274` -> `attempted_failed` (genuinely
      transient). The body is ALREADY captured on `TardisHTTPError` (added for the 274 lock) — it is simply discarded on
      the 400 path. — **DONE**: `market-tick-data-service@a7569298` (2026-07-18).
- [x] ✅ [CODE] P1. **Log the Tardis error code.** `tardis_csv_transport.py:523` logs only `"Tardis HTTP %s error"`, so
      `code=300` and `code=140` are indistinguishable in the logs — the split is currently UNMEASURABLE. Log the code
      before anything tries to size this. — **VERIFIED DONE 2026-07-26**: the same commit `a7569298` already added
      `code=%s` to both 400-path log lines (streaming + non-streaming).
- [x] ✅ [DATA] P1. Size the damage: count existing `attempted_failed` rows attributable to 400s, and purge/reclassify
      them (snapshot-first, like the 2026-07-17 eu purge). Expect a real coverage-% correction upward. — **DONE
      2026-08-08** (`market-tick-data-service@46e830c8` fix + `@5a4638f6` cleanup): re-ran the sizing script fresh
      (counts drifted from 5,572 to 5,568 per the doc's own note), re-verified reversibility fresh-same-run
      (`softDeletePolicy.retentionDurationSeconds` = 604800), then `--apply`'d. **5,568 rows** reclassified
      `attempted_failed -> empty_confirmed` (`error_reason -> EXPECTED_TARDIS_STRUCTURAL_ABSENCE_400`) on
      `gs://market-data-tick-cefi-prd-central-element-323112`. Pre-flip snapshot at
      `_index/snapshots/pre_tardis_400_impossible_combination_reclass_20260808T155702Z.parquet`. Gate verified: total
      rows unchanged (10,289,570), `captured` unchanged (4,474,796), `attempted_failed` -5,568 / `empty_confirmed`
      +5,568 exactly. Post-apply fresh dry-run confirms 0 remaining matching rows. See Progress Log for a memory-safety
      finding hit + fixed along the way (the original script OOM-killed against the real 10.3M-row manifest scale) and
      the script's own subsequent deletion (its `Delete-when` condition was met by this apply).
- [x] ✅ [CONTRACT] P2. Register Tardis error codes in UAC (`classify_venue_error` currently knows none), so the
      honest-absence-vs-fetch-failure decision is contract-driven rather than string-matched on `"Empty CSV"`. — **DONE
      2026-07-26**: `unified-api-contracts@c144f975` — `140`/`300` registered as `ErrorAction.SKIP`, 2 new unit tests,
      QG green.
- [x] ✅ [CODE] P2. **Verify the shipped vendor-catalog gate (`tardis_vendor_catalog.py`,
      `market-tick-data-service@8e406dbb`) reads its `dataTypes`/`availableSince`/`availableTo` from the RIGHT array —
      likely reading the wrong one, which silently degrades the data_type dimension of the 3-condition gate to a no-op
      (fail-open-safe, not a correctness bug, but an incomplete implementation of this todo's own spec).** — **DONE**:
      `market-tick-data-service@ca5be7d8` (2026-08-09). **Confirmed live** (unauthenticated
      `GET https://api.tardis.dev/v1/exchanges/bybit`, real response, 2026-08-09): `availableSymbols[]` entries
      carry ONLY `id`/`type`/`availableSince`/`availableTo` — **never** `dataTypes` (checked the union of keys across
      all 1,812 entries) — while `datasets.symbols[]` entries carry all four fields
      (`id`/`type`/`dataTypes`/`availableSince`/ `availableTo`), e.g. `AAVEUSDT`:
      `{"dataTypes": ["trades","incremental_book_L2","quotes","book_snapshot_5", "book_snapshot_25","derivative_ticker","liquidations","book_ticker"], "availableSince":"2021-05-13T00:00:00.000Z", "availableTo":"2026-08-09T00:00:00.000Z"}`.
      This matches finding (2) exactly (`TardisAvailableSymbol` genuinely has no `dataTypes` field) and confirms the
      suspected bug: `_fetch_vendor_catalog` was reading `dataTypes` off an array that never carries it, so
      `entry.data_types` was always an empty frozenset and the `data_type not in entry.data_types` check in
      `is_allowed_by_vendor_catalog` never fired (silently a no-op, exactly as predicted). **Fix**: pointed the fetch at
      `exchange_info["datasets"]["symbols"]` instead of `availableSymbols[]` (the
      `availableSince`/`availableTo`/symbol-presence dimensions were already correct per this todo's own note — no
      change needed there, `datasets.symbols[]` carries the same values). Updated the module docstring +
      `VendorSymbolEntry` docstring to name the corrected array. **Tests**: rewrote the `_BYBIT_PAYLOAD` fixture to the
      real live-verified shape (dataTypes only under `datasets.symbols[]`, not fabricated onto `availableSymbols[]`, per
      finding (3)'s own callout that the old tests validated the code's wrong assumption); added a new regression test
      (`test_reads_datasets_symbols_not_available_symbols`) that plants a `dataTypes` key on `availableSymbols[]` and
      asserts it is IGNORED while the real `datasets.symbols[]` entry governs the gate decision — this pins the fix
      against a future regression back to the wrong array. All 11 unit tests green; full `quality-gates.sh` green (321s,
      sentinel `d6b65e6f`); shipped via quickmerge, verified `ca5be7d8` ancestor-of `origin/live-defi-rollout`.

## Progress Log (append-only)

- 2026-07-17: filed. Found by following three operator questions in sequence — "is it doing data that doesn't exist",
  "don't we have a converter/mapping", and decisively "is it the date (available for and to?)". The first two led to
  code=300; the third surfaced **code=140**, a separate class I had missed and the one with the large systematic
  multiplier given the 2020->2026 walk. All verified live against the real API with the production key, not inferred.
- **2026-07-27 (slot-15, `cefi_satellite_ao_dispatch_batch1-029`) — dry-run sizing script shipped.** Built
  `market-tick-data-service/scripts/reclass_cefi_tardis_impossible_combinations_400_2026_07_27.py` (mirrors the
  established `reclass_*.py` shape: pure `reclassify(df)` function, dry-run default, `--apply` implemented but never
  invoked, snapshot-before-write, before/after row-count gate). 5 unit tests green
  (`tests/unit/scripts/test_reclass_cefi_tardis_impossible_combinations_400.py`); full `quality-gates.sh` green
  (`market-tick-data-service@c36d35d1`).
  - **Identification logic** (verified against the live code, not assumed): pre-fix, `TardisHTTPError._build_message`
    returned the literal string `"Tardis HTTP 400"` with NO JSON code embedded (the code was only parsed/logged starting
    with the `a7569298` fix, and only into the log line). `_classify_tardis_error` extracts the whole string as its
    `code_token` (no `:` to split on) and `classify_venue_error("tardis", "Tardis HTTP 400")` misses (UAC only registers
    numeric `"400"`/`"300"`/`"140"` tokens, never the prefixed string) — so the raw token is stored verbatim as
    `error_reason`. Every historical cefi `attempted_failed` row with `error_reason == "Tardis HTTP 400"` is therefore,
    by construction, one of the two impossible-combination classes. The manifest does not retain the JSON sub-code, so
    the script cannot and does not split code=300 vs code=140 — both get the same reclassification.
  - **Dry-run result against a fresh prod manifest snapshot** (`market-data-tick-cefi-prd-central-element-323112`,
    8,875,243 rows total): **5,572** matching rows (100% `pipeline_mode=batch_tardis`), by venue — DERIBIT 4,362 /
    OKX-SPOT 767 / BYBIT 371 / OKX-FUTURES 33 / BITGET-FUTURES 15 / KRAKEN-SPOT 10 / BINANCE-FUTURES 7 / BYBIT-SPOT 7;
    by data_type — book_snapshot_5 4,867 / trades 515 / derivative_ticker 115 / liquidations 75. Gate verified: total
    row count unchanged, `captured` count unchanged, `attempted_failed` -5,572 / proposed `empty_confirmed` +5,572.
  - **Count discrepancy vs the 2026-07-18 measurement (24,410 rows) — noted, not resolved here.** The live count is now
    5,572, roughly 23% of the earlier figure. Most likely explanation: 9 days of further live/backfill activity
    naturally re-attempted and resolved many of these (symbol, date) shards via normal retries (a captured/other-status
    outcome removes them from this bucket) — this script does not investigate which mechanism actually closed the gap,
    since that is outside this todo's dry-run-only scope. Whoever picks up the `--apply` half of this todo should re-run
    the script fresh (counts drift) rather than trust either historical number.
  - **Target reclassification** (dry-run proposal only): `capture_status: attempted_failed -> empty_confirmed`,
    `error_reason: "Tardis HTTP 400" -> "EXPECTED_TARDIS_STRUCTURAL_ABSENCE_400"`. This reason string is NOT a member of
    UAC's closed-set `EmptyConfirmedReason` enum (no existing member fits "vendor catalog doesn't archive this (symbol,
    date)") — it follows the same precedent as `reclass_tradfi_expected_reason_attempted_failed_2026_07_15.py`'s
    `EXPECTED_SOURCE_NOT_AVAILABLE` (a raw-parquet- write descriptive string, since bulk historical reclass can't go
    through `record_empty()`'s enum-membership check). **Flagging for the operator/whoever applies this**: whether to
    formalize a canonical enum member, or instead route these rows through the in-flight `coverage_exclusions` registry
    (UAC's `EXPECTED_UPSTREAM_OUT_OF_ BOUNDS`, explicitly documented as "REGISTRY-DERIVED ONLY, never hand-stamp at a
    callsite") is a taxonomy decision this script deliberately does NOT make.
  - `--apply` was never invoked — the live manifest is untouched by this todo.

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - the P1 sizing/purge half is
  explicitly operator-gated and snapshot-first; the vendor-catalog gate must coordinate with in-flight
  `coverage_exclusions` work in UAC.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-07-30 verdict. The
  P0 vendor-catalog-gate is still entangled with the unresolved canonical-enum-vs-coverage_exclusions taxonomy decision
  the script explicitly declines to make; the P1 `--apply` purge half is still operator-gated + snapshot- first (counts
  drift). No duplicate-claim risk found (grepped all active cefi_master planning docs — no overlap).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: RECLASSIFY → `assigned_vm: planning`. Both remaining
  items are now bounded. (1) **P1 `--apply` purge** — the doc's own `round5-cefi-question-resolution 2026-08-08` entry
  above already resolved both blockers this round exists to check for: reversibility (fresh same-run
  `softDeletePolicy.retentionDurationSeconds` check = 604800s, qualifying under `task_template.md` finding T) and
  taxonomy (use the `EXPECTED_TARDIS_STRUCTURAL_ABSENCE_400` raw-string precedent, same shape as the cited
  `reclass_tradfi_expected_reason_attempted_failed_2026_07_15.py` pattern — matches cheat-sheet ruling #6 exactly: "a
  doc whose only remaining gate is 'needs a human at the keyboard for an already-approved, reversibility-provable
  delete' may now be reclassifiable"). That resolution session explicitly stopped short of `--apply` itself
  ("documentation-question audit, not an implementation dispatch") — the remaining work is mechanical: re-run the sizing
  script fresh (counts drift per its own note), confirm the gate, `--apply`. (2) **P0 vendor-catalog gate** —
  re-verified the "coordinate with the in-flight `coverage_exclusions` work" blocker this doc has carried since
  2026-07-17: `unified-api-contracts/unified_api_contracts/canonical/coverage_exclusions.py` (git log: created +
  finished same-day 2026-07-17, commit `a1284b3d`, untouched since — genuinely NOT in-flight anymore) is a manually
  curated, evidence-gated registry for permanent historical outage windows (mandatory `evidence_uri`/`verified_by` per
  entry) — a structurally different mechanism from this todo's live, machine-refreshed per-venue Tardis catalog cache
  (`GET /v1/exchanges/<venue>`, refreshed daily, thousands of symbols). The two don't actually intersect; the
  "coordination" concern was a 2026-07-17-vintage hedge that no longer applies now that `coverage_exclusions` has
  shipped as a stable, orthogonal registry. The fix (already-checked `exc.is_structural_absence` classification exists
  at `tardis_csv_transport.py`'s streaming-download 400 handler, confirming the reactive half is live) is a
  self-contained, fully-specified implementation (exact request shape + 3-condition gate given in "The fix" section
  above) — no design call remains. Conflict-check: grepped `plans/active/cefi_satellite_ao_dispatch_batch{9,10}*`,
  `cross_cutting_satellite_ao_dispatch_batch1*`, `defi_satellite_ao_dispatch_batch6*_finalize`, and
  `cefi_consolidated_closeout_2026_07_18.md`/`cefi_consolidated_closeout_aggregated_sources_2026_07_24.md` — all
  mentions are cross-references/rollup listings of this doc's own still-open items, none is an active AO dispatch
  implementing either todo. **Note for whoever reads `cefi_satellite_ao_dispatch_batch10_2026_08_08.md`'s "Deferred —
  human-only" listing for this doc**: that snapshot predates this doc's own `round5-cefi-question-resolution 2026-08-08`
  entry above, which supersedes it. Companion finalize plan:
  `/plans/active/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17_finalize_2026_08_08.md`.

## Progress Log

- **2026-08-08 (slot-13, task `tardis_impossible_combinations_recorded_as_attempted_failed-003`)**: dispatched the SAME
  `[CODE] P0` vendor-catalog-gate todo slot-29/slot-33 already closed below — a THIRD concurrent pickup of this task.
  Built an independent implementation (new `tardis_catalog_gate.py` + a UAC `TardisDatasetSymbol` schema addition for
  `datasets.symbols[]`) before fresh-pulling mid-session and discovering the checkbox was already flipped with shipped
  commits. Discarded this slot's own uncommitted duplicate work entirely (never staged/committed — no conflicting second
  implementation shipped) after verifying the landed code addresses the todo. While building my own version I
  cross-checked the issue doc's own "The fix" spec (`datasets.symbols[]` carries `dataTypes`) against the SHIPPED
  `tardis_vendor_catalog.py`, which instead reads `dataTypes` off `availableSymbols[]` — filed as a new `[CODE] P2` todo
  above (evidenced against the pre-existing `TardisAvailableSymbol` UAC schema, which has no `dataTypes` field, and
  against the shipped code's own test fixtures, which fabricate a `dataTypes` key on `availableSymbols` mocks rather
  than asserting the real API shape). Low severity — fail-open, reactive 400 classification remains the correctness
  backstop — so filed as a follow-up rather than reopening this todo.
- **2026-08-08 (slot-29)**: flipped the `[CODE] P0` vendor-catalog-gate checkbox — the fix landed on
  `origin/live-defi-rollout` via `market-tick-data-service@8e406dbb` (gate) + `@07cafbbb` (file-size-cap follow-up,
  moved manifest emission into `tardis_vendor_catalog.py`), shipped by slot-33 concurrently with this slot's independent
  implementation of the same todo (a genuine dispatch-collision — both slots picked up this task around the same time).
  Verified slot-33's landed code fast-forward-clean on this slot's `market-tick-data-service` worktree and matches the
  todo's spec (3-condition gate, fail-open, honest-absence manifest write) before discarding this slot's own duplicate
  WIP and flipping the checkbox against the ALREADY-SHIPPED commits rather than re-shipping a conflicting second
  implementation.
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — swapped in
  `unified-api-contracts/.../coverage_exclusions.py` (the in-flight UAC work the open `[CODE] P0` vendor-catalog-gate
  todo must coordinate with) for the generic `cefi_master.md` epic pointer.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **2026-08-08 (slot-20, task `tardis_impossible_combinations_recorded_as_attempted_failed-002`)**: completed the
  `[DATA] P1` sizing/purge todo — the `--apply` half. Re-ran the sizing script fresh: **5,568** matching rows (drifted
  down from the 2026-07-27 count of 5,572 — 4 rows resolved via normal retries in the interim, consistent with the doc's
  own note that counts drift). Re-verified reversibility fresh-same-run before touching prod
  (`gcloud storage buckets describe gs://market-data-tick-cefi-prd-central-element-323112 --format="value(softDeletePolicy.retentionDurationSeconds)"`
  → 604800, matching finding T's 7-day floor).
  - **Memory-safety finding + fix (found mid-task, fixed in the same session — not deferred)**: the original script
    (`market-tick-data-service@c36d35d1`, pandas-based) was safe in dry-run but its `--apply` path
    (`reclassify(df.copy())` + re-serializing BOTH the original and reclassified 10.3M-row/42-column DataFrame for the
    snapshot and write uploads) reliably exceeded the shared-host resource-watchdog's 10GB per-slot RSS cap — confirmed
    via `journalctl` (`resource-watchdog[...] KILL #4/#5/#6 ... rss:~11-12GB > 10485760kB`), 2 of my own `--apply`
    attempts SIGTERM-killed before completing a write. Root cause: pandas boxes every string cell as a separate Python
    object (10.3M rows x ~26 string columns is hundreds of millions of objects) — even a bare `pd.read_parquet` load
    alone peaked at 9.4GB RSS, leaving under 1GB of headroom before any mutation/serialization. Fixed in two commits:
    `market-tick-data-service@72c8a756` (first pass: in-place mutation instead of `df.copy()`, reuse raw bytes for the
    snapshot instead of re-serializing) then `@46e830c8` (measured the first fix still only had a shrinking margin —
    9.4GB just to load — and rewrote `main()`'s IO path as fully pyarrow-native: `pq.read_table` +
    `pyarrow.compute`-based mask/mutation via `Table.set_column` + `pq.write_table`, since Arrow's columnar string
    storage has no per-cell object overhead and `set_column` only duplicates the 2 changed columns, not the whole
    frame). Measured: dry-run peak RSS dropped from 9.36GB (pandas) to 5.17GB (pyarrow); the real `--apply` run peaked
    at 5.32GB. `reclassify()` (the pandas pure function backing the script's own unit tests) was left untouched — all 5
    existing unit tests pass unmodified; only `main()`'s IO path changed.
  - **Applied**: `market-tick-data-service@46e830c8` (memory fix) + `@5a4638f6` (script+test deletion, below). 5,568
    rows reclassified `attempted_failed -> empty_confirmed` (`error_reason -> EXPECTED_TARDIS_STRUCTURAL_ABSENCE_400`)
    on `gs://market-data-tick-cefi-prd-central-element-323112`. Pre-flip snapshot at
    `_index/snapshots/pre_tardis_400_impossible_combination_reclass_20260808T155702Z.parquet`. Gate verified live: total
    rows unchanged (10,289,570), `captured` unchanged (4,474,796), `attempted_failed` -5,568 / `empty_confirmed` +5,568
    exactly. A fresh post-apply dry-run confirms **0** remaining `attempted_failed` rows with
    `error_reason == "Tardis HTTP 400"`.
  - **Script deleted** (`market-tick-data-service@5a4638f6`): the script's own header declared
    `# Delete-when: after --apply verified + 0 cefi attempted_failed rows carry error_reason=="Tardis HTTP 400"` — both
    conditions are now met, so deleted `scripts/reclass_cefi_tardis_impossible_combinations_400_2026_07_27.py` and its
    dedicated unit test (which only exercised this script's own `reclassify()`, with no other callsite).
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
- **2026-08-09 (slot-27, task `tardis_impossible_combinations_recorded_as_attempted_failed-a9c2510c68f9`)**: closed the
  final `[CODE] P2` todo — `market-tick-data-service@ca5be7d8` fixes `tardis_vendor_catalog.py` to read `dataTypes` from
  `datasets.symbols[]` instead of `availableSymbols[]`, confirmed live against the real Tardis API (see todo entry above
  for the full diff evidence). **All 6 todos in this doc are now done and it is unlocked** — archiving in the next
  commit per the plan-completion-and-archival-discipline HARD RULE (checkbox flip and `git mv` kept as separate commits,
  per RULES.md § 2's incident note).
