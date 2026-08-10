---
doc_type: issue
title:
  "Smoke test of HYPERLIQUID/PACIFICA-SOLANA/EXTENDED-STARKNET/LIGHTER-ZKSYNC real market-data availability — 4
  independent bugs found, 2 of them fully-broken venues"
summary:
  "Operator asked (drilldown mockup review) whether the data_types declared for these 4 bespoke-API (non-Tardis)
  DEX-perp venues actually line up with what can really be downloaded, since unlike Tardis venues these each hit a
  different native API. A 4-agent smoke test (real adapter code read + live public-API probes + real GCS manifest/object
  cross-check per venue) found: HYPERLIQUID mostly real (2 data_types with billions of real rows) but batch trades has
  zero rows ever despite non-stub code, plus a manifest false-negative bug; PACIFICA-SOLANA has fully real, API-verified
  code for all 4 data_types but ZERO production rows ever captured for any of them — operationally dormant, not broken;
  EXTENDED-STARKNET has a confirmed functional bug in book_snapshot_5 (uses today's date instead of the backfill target
  date, so it silently produces zero rows for any non-today run) plus a provenance bug mislabeling real Extended-native
  data as Tardis-sourced; LIGHTER-ZKSYNC is the most broken — every Tardis call for this venue is rejected outright by
  Tardis (wrong exchange slug hardcoded: `lighter-zksync` vs. the real `lighter`), so 3 of its 4 declared data_types
  have never produced a single real row, and even its one working native data_type (ohlcv_1m) is mislabeled by a
  separate venue-name-normalization bug and stopped being captured after 2026-05-05."
status: open
nature: notes
asset_group: [defi]
stage: [data, meta]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    smoke-test,
    hyperliquid,
    pacifica-solana,
    extended-starknet,
    lighter-zksync,
    dex-perps,
    honest-coverage,
    pipeline-mode,
    data-pipeline-correctness,
  ]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    /plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
  ]
created: 2026-07-07
author: unknown
parent_epic: instruments_master
priority: P0
source:
  'Drilldown mockup review, 2026-07-07 — operator: "The data types you said we have there, do they actually line up with
  the data types that we can download data for?" for HYPERLIQUID/PACIFICA-SOLANA/EXTENDED-STARKNET/ LIGHTER-ZKSYNC
  specifically, since these are bespoke native APIs, not Tardis. 4-agent workflow, real code read + live API probes +
  real GCS manifest cross-check per venue.'
assigned_vm: NA
resolved_by:
locked_by:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/adapters/hyperliquid_s3.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_onchain_perp_batch_symbols.py,
    unified-api-contracts/unified_api_contracts/registry/possible_manifest.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/issues/mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md,
  ]
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 3
last_updated: 2026-07-07
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding — cross-repo data-correctness bugs, one venue (LIGHTER-ZKSYNC) fully non-functional
> for 3 of 4 declared data_types.** None of these are placement/style questions — each is a real defect (wrong external
> identifier, wrong date used, a normalization miss) independently causing zero real data where UAC declares real
> capability.

## Method

Per-venue: (1) read the real adapter code and confirm real vs. stub, (2) hit the venue's real public API live today and
confirm response shapes match the parsing code, (3) read the real GCS `_index/availability_index.parquet` manifest
(respecting single-walk discipline — no whole-corpus walk) plus spot-verify actual objects. No guessing — every verdict
below is backed by a live probe or a real manifest/object read.

## Findings by venue

### 1. HYPERLIQUID — mostly real, one real bug + one manifest bug + one dead stub

- `book_snapshot_5`: **REAL** — `HyperliquidS3Downloader.fetch_l2_book`
  (`market_tick_data_service/adapters/hyperliquid_s3.py:256-293`), wired via `onchain_perp_batch_handler.py:631-642`.
  1.17B real rows, 2024-01-01→2026-01-04.
- `derivative_ticker`: **REAL** — same file, `fetch_asset_ctxs` (L213-254). 13.3M real rows, same window.
- `perp_funding`: **REAL** — `cli/handlers/_perp_funding_hl_aster.py:42-121`. 3.77M real rows, 2023-11-01→2026-05-31 —
  but lives in the **defi** bucket, not cefi, despite being an MTDS/CeFi-venue data type (classification anomaly, not a
  correctness bug — flagged for review).
- `trades`: **MIXED, and this is the real bug**. Live capture works right now — downloaded
  `HYPERLIQUID:PERP:BTC.parquet` for 2026-06-25 and confirmed 244 genuine trade rows. But the **batch/historical path
  has zero rows ever, in ~3 years of manifest history**, despite real (non-stub) code — 12,179 shard-attempts, 100%
  `empty_confirmed`/`SOURCE_RETURNED_ZERO`, including 688 attempts on/after the adapter's own declared
  `S3_TRADES_START=2025-03-22` gate. Suspected root cause (not yet confirmed): a `coin`/`asset` field-name mismatch in
  `_parse_node_fills` (`hyperliquid_s3.py:403-408`) silently matching zero records against the real S3 payload's actual
  field names.
- Separately: `HyperliquidAdapter._download_trades_from_tardis()`
  (`market_interface/adapters/onchain_perps/hyperliquid_adapter.py:424-427`) is a genuine, admitted stub
  (`logger.warning("Tardis integration not implemented..."); return []`) — but it is **dead code, never called by the
  real batch pipeline**, so it doesn't explain the trades gap above.
- **Manifest false-negative bug** (separate from the above): the phantom-audit flags 373 of 540 real `live_hyperliquid`
  shards as `attempted_failed`/`phantom_captured_no_parquet_at_canonical_path`, but the parquet demonstrably exists at
  the canonical path (confirmed by direct download). This is a manifest-side bug, not a data problem.

### 2. PACIFICA-SOLANA — real code + real API, zero production data, operationally dormant

All 4 declared data_types (`trades`, `book_snapshot_5`, `derivative_ticker`, `perp_funding`) have **REAL,
correctly-shaped code** in `market_tick_data_service/adapters/_umi_pacifica.py`, and all 4 were verified **today**
against Pacifica's real, no-auth-required public API (`api.pacifica.fi`) — every endpoint's live response matched the
parsing code exactly.

But `_index/availability_index.parquet` and `_index/expected_universe_ranges.parquet` (cefi bucket) show **zero rows of
any capture_status — not even an attempt — for this venue, ever**. The venue IS enrolled in
`expected_universe_ranges.parquet` (150 rows across 4 data_types × 10 instruments), but every row is
`expected_unattempted` or pre-launch `empty_confirmed`; the enumerator's last run is frozen at 2026-02-19, ~4.5 months
stale vs. the corpus's latest observed partition elsewhere. Sibling venue EXTENDED-STARKNET has 1,209 real manifest rows
by comparison, proving the manifest pipeline itself works fine for this venue class — this is specifically about
Pacifica never having a backfill or live job actually run.

Two secondary findings:

- UAC declares `live_capable=True` for trades/book_snapshot_5/derivative_ticker (`data_type_capability.py:598-608`), but
  the live connector (`live/connectors/pacifica_solana_perp_ws.py`) is an explicit `BLOCKED-CREDENTIALS` stub
  (`_CREDENTIALS_AVAILABLE = False`, never emits a tick) — the capability declaration overstates what's actually wired.
- `derivative_ticker` (`_umi_pacifica.py:227-276`) and the standalone `perp_funding` data_type
  (`_perp_funding_pacifica_lighter.py:125-175`) both hit the identical `/funding_rate/history` endpoint — if both
  pipelines were ever turned on, they'd write the same underlying funding data under two different canonical `data_type`
  labels. Worth resolving before either is switched on for real.

### 3. EXTENDED-STARKNET — one confirmed functional bug, one provenance bug, rest is real-but-sparse

- `book_snapshot_5`: **REAL code, confirmed bug, behaves as fully absent.** `_fetch_extended_book_for_symbol`
  (`_umi_extended.py:415`) stamps the snapshot with `datetime.now(tz=UTC)` instead of the requested backfill `date`,
  then the very next line discards the row unless it falls inside the target day's window — which is always false for
  any day except "today." Manifest confirms 0 rows ever, at any date.
- `trades`: **REAL code, structurally can't backfill — CONFIRMED 2026-07-28 (slot-16, live API probe).** The adapter's
  `/info/markets/{symbol}/trades` endpoint (`_umi_extended.py:284`) takes no `startTime`/`endTime` param at all (unlike
  Extended's candles/funding endpoints, which do; explicit past-day `startTime`/`endTime` values are silently ignored),
  and its `cursor` param is forward-only (ascending toward "now") within a small live rolling buffer (~50-row hard cap
  regardless of `limit`, ~2-7 min of trades) — arbitrarily small cursor values (`0`, `1`, values far below the live id
  range) all resolve to the same near-"now" window rather than the earliest retained trade, proving the underlying store
  has no deeper history to walk back into. No undocumented pagination param (`before`/`toId`/ `fromId`/`endId`/`offset`)
  works either. 0 rows of any capture_status exist, and this is now confirmed CORRECT (honest absence, not a code bug) —
  full probe evidence in the Progress Log below.
- `derivative_ticker`: **REAL, verified working** (downloaded and confirmed real hourly funding-rate rows) — but only
  captured on 4 distinct days across the full window (2024-10-01→present), reading as ad-hoc manual verification runs
  rather than a scheduled pipeline.
- `ohlcv_1m` (not one of the 3 UAC-declared types, but present): **REAL, working**, similarly sparse (17/593 days).
- **Provenance bug**: every real EXTENDED-STARKNET row/object is tagged `pipeline_mode=batch_tardis, source=tardis`,
  contradicting `unified_trading_library/pipeline_mode_resolver.py:56`'s explicit
  `_VENUE_OVERRIDES["EXTENDED-STARKNET"] = PipelineMode.BATCH_EXTENDED` override (whose own comment says "without this
  entry the asset_group fallback returns batch_tardis (wrong)") — exactly the wrong fallback observed. The override
  isn't being applied at the real write path. The data itself is genuinely Extended-native; it's mislabeled, not
  fabricated.
- `perp_funding` (standalone data_type): confirmed **deliberate, documented** design decision
  (`data_type_capability.py:587-591`, `market_data_categories.py:1201-1216` both carry an operator-dated 2026-06-23
  comment) to not give this venue a standalone `perp_funding` row — not a bug. Open question, not yet resolved: whether
  any downstream consumer specifically reads `asset_group=defi/data_type=perp_funding` for this venue rather than
  `cefi/derivative_ticker` (where the real funding data actually lives) — if one does, it would incorrectly conclude
  Extended has no funding data.

### 4. LIGHTER-ZKSYNC — the most broken of the four; 3 of 4 data_types fully non-functional

- **Root cause bug**: the code hardcodes Tardis `exchange="lighter-zksync"` everywhere (`umi_tick_provider.py:243`,
  `venue_mapping.py:60,197,223`, `_perp_funding_pacifica_lighter.py:219`), but Tardis's real identifier for this venue
  is `"lighter"` — confirmed live: `curl https://api.tardis.dev/v1/exchanges/lighter-zksync` →
  `"Invalid 'exchange' param... Did you mean 'lighter'?"`. **Every single Tardis call this codebase makes for this venue
  is rejected outright.**
- Compounding bug: the symbol-format assumption ("bare base-asset symbols like BTC") is also wrong — Tardis's real
  `lighter` exchange uses numeric market-id strings (`"0"`, `"1"`, ...), confirmed live.
- Net effect: `trades`, `book_snapshot_5`, `derivative_ticker`, `perp_funding` — **all 4 are ABSENT in production, zero
  rows at any date, pre- or post- the 2026-04-17 native→Tardis switch date** (the switch date itself is real and
  externally correct per Tardis's own metadata; it just never actually worked once switched to).
- The only real, populated data_type is `ohlcv_1m` (native `/candles`, never routes through Tardis at any date) —
  verified real 1440-row/day files for BTC/ETH/HYPE/SOL/TON — but it's **also mislabeled** as
  `pipeline_mode=batch_tardis` due to a separate bug: `pipeline_mode_resolver.py:58`'s `_VENUE_OVERRIDES["LIGHTER"]`
  never matches the real venue key, which normalizes to `"LIGHTER_ZKSYNC"` (line 176) — the override is dead code for
  this venue. That override's own comment also wrongly says "Lighter DEX (Solana perp)" — Lighter is zkSync, an apparent
  copy-paste from the adjacent Pacifica-Solana override.
- `ohlcv_1m` capture itself stopped entirely after ~2026-05-05 (no folder found through 2026-06-29) — cause not yet
  investigated.

## Why this matters

- Two of these four venues (`PACIFICA-SOLANA`, `LIGHTER-ZKSYNC`) are, for practical purposes, contributing **zero real
  market-tick data today** despite being declared MVP-relevant candidates in the drilldown mockup review — this directly
  bears on whatever MVP-scoping decision the operator makes for them.
- The LIGHTER-ZKSYNC Tardis-slug bug is a one-line-class fix that would unlock 3 of 4 data_types immediately, if Tardis
  actually has usable coverage under the correct `lighter` identifier — worth fixing and re-testing before writing this
  venue off.
- The EXTENDED-STARKNET `book_snapshot_5` bug and both provenance/mislabeling bugs (EXTENDED-STARKNET, LIGHTER-ZKSYNC)
  are real, narrow, high-confidence fixes — not architecture questions.
- HYPERLIQUID's batch-trades gap is the one finding here that looks like an actual field-parsing bug in
  otherwise-working, heavily-used code (1B+ rows elsewhere) — worth root-causing since the adapter is clearly not broken
  in general.

## Todos

- [x] [FIX] P0. ✅ **LIGHTER-ZKSYNC: fix the wrong Tardis exchange slug AND symbol format together — CONFIRMED both
      needed, verified live 2026-07-07.** Fixing only the slug (`lighter-zksync` → `lighter`) at the 4 hardcoded sites
      (`umi_tick_provider.py:243`, `venue_mapping.py:60,197,223`, `_perp_funding_pacifica_lighter.py:219`) gets past
      Tardis's exchange check but then fails on symbol (`HTTP 400`, Tardis wants the numeric `market_id` string like
      `"1"` for BTC, not a bare ticker like `"BTC"`). Fixing both together got a real `HTTP 200` with 238,122 real
      `market_stats`(=derivative_ticker) rows including a populated `funding_rate` (also 591,861 real trades rows, 1.46M
      real book_snapshot_5 rows, same probe) — **this is currently the ONLY path that would give this venue a funding
      floor at all**, since the native adapter has no funding endpoint. Free-tier Tardis key only allows first-of-month
      historical dates — re-verify with a paid key or a first-of-month date before declaring this resolved in
      production. — market-tick-data-service@0c4000a02 fixes lighter exchange fallback slug + adds Tardis numeric
      market_id resolution + corrects data_type mapping to derivative_ticker. **Re-verify DONE 2026-07-30**
      (defi_satellite_ao_dispatch_batch1 finalize reconciliation), see defi_satellite_ao_dispatch_batch1_2026_07_25.md
      todo 47 for full evidence — re-verified live against a real free-tier-compatible first-of-month historical date,
      confirmed real `trades`/`book_snapshot_5`/`derivative_ticker` rows still return under current code; resolved in
      production per this caveat's own bar.
- [x] [FIX] P0. ✅ **LIGHTER-ZKSYNC: fix the separate native-trades `limit=500` bug** —
      `_fetch_lighter_trades_for_symbol` hardcodes `"limit": "500"` on `GET /recentTrades`; Lighter rejects this with
      `HTTP 400`. Confirmed live: `limit≤100` returns real trades immediately. This is independent of the Tardis-slug
      bug above — it breaks the NATIVE (pre-2026-04-17) trades path specifically. One-line fix. —
      market-tick-data-service@0c4000a02 changes `_umi_lighter.py` limit param from "500" to "100".
- [x] [FIX] P1. ✅ **CORE FIXED — `unified-trading-library@d59f14db`** (the CORRECT source-aware fix, NOT the naive
      rename). Deleted the dead `_VENUE_OVERRIDES["LIGHTER"]` key + added a source-blind guard in
      `derive_pipeline_mode_for_row`: `(LIGHTER-ZKSYNC, ohlcv_1m)` with no explicit `source` now returns **None**
      (honest not-derivable) instead of fabricating `batch_tardis` from `SOURCE_PRIORITY[0]` — native `/candles`
      (source=lighter_api) rows never touched Tardis. trades/book/derivative_ticker stay `batch_tardis` (genuinely
      Tardis-archived from 2026-04-17); an explicit `source=` is still honored. +4 unit tests. **DEFERRED (scoped
      follow-ups, NOT blocking correctness):** (a) a positive `BATCH_LIGHTER_API` stamp for native rows — needs a full
      `lighter_api` SourceCapability wiring (real REST endpoint/modes/creds), too much to guess unattended + it hit the
      PipelineMode↔SOURCE_PRIORITY closed-set cascade; (b) threading `source=` through backfill/manifest_writer/rebuild
      (the CORE fix already makes those paths honest None); (c) a `--force` manifest re-stamp of the existing
      `batch_tardis`-mislabeled rows (attended real-infra — read each row's true source/path segment first). The "native
      ohlcv_1m stopped after 2026-05-05" investigation also folds into (c). The `_VENUE_OVERRIDES` "Solana perp" comment
      was removed with the dead key.
- [x] [FIX] P1. ✅ **DEFERRED (a)+(b)+(c) NOW ALL DONE (2026-07-18, attended).** (a) Positive `BATCH_LIGHTER_API` stamp
      SHIPPED — `unified-api-contracts@81bf5e17` (`BATCH_LIGHTER_API` PipelineMode member + `_LIGHTER` SourceCapability
      with the real REST base_url `https://mainnet.zkln.elliot.ai/api/v1` + `SOURCE_PRIORITY`/`SOURCE_MODE_CAPABILITY`/
      emission-latency closed-set entries + 6 tests); the closed-set cascade was resolved fully, not guessed. Lock test
      `unified-trading-library@83350199` asserts
      `derive_pipeline_mode_for_row("LIGHTER-ZKSYNC","cefi","ohlcv_1m",     source="lighter_api") is BATCH_LIGHTER_API`.
      (c) The `--force` re-stamp is DONE as a **re-path + manifest backfill** migration
      `market-tick-data-service@c1da2200` (`scripts/restamp_lighter_ohlcv_batch_tardis_to_lighter_api_2026_07_18.py`,
      DRY-RUN→canary→full apply on real infra): scope measured = **475 objects** (5 instruments
      BTC/ETH/HYPE/SOL/TON-USDC@LIN, days 2026-02-01..2026-05-06, 95×5), NOT the earlier 375-est — the mislabel extends
      20 days PAST the 2026-04-17 Tardis-coverage boundary because Tardis emits NO LIGHTER ohlcv_1m at all (its LIGHTER
      manifest = trades/book/derivative_ticker only). Provenance confirmed native by inspecting pre- and post-04-17
      samples (identical 15-col native candle schema, no source col, 1440 rows/day). All 475 GCS objects moved
      `pipeline_mode=batch_tardis`→`batch_lighter_api` (crc32c-verified copy→delete, idempotent) + 475 captured rows
      backfilled via `ManifestWriter(per_vm_shards=True)` with EXPLICIT `source=lighter_api` (cefi ohlcv_1m is
      multi-source so a blank source raises). **VERIFIED on real infra:** cefi canonical `_index` now carries 475
      `LIGHTER-ZKSYNC ohlcv_1m` rows = `batch_lighter_api`/`lighter_api`/`captured` (95 days 2026-02-01→2026-05-06), and
      **0** `batch_tardis` LIGHTER ohlcv_1m objects remain. The "native ohlcv_1m stopped after 2026-05-06" observation
      is confirmed (no LIGHTER ohlcv_1m objects at either path after 2026-05-06 in the 2026-02..2026-07 scan) — folded
      into (c), no further action. (b) source-threading is satisfied: the CORE fix keeps the source-blind path honest
      (`None`), and this migration is the explicit-source producer for the historical rows.
- [x] [FIX] P1. ✅ **FIXED — `market-tick-data-service@55dac12a`** (the CORRECT honest fix, NOT the naive one). The
      `/orderbook` endpoint is CURRENT-only (no historical params), so a naive "use the target date" would FABRICATE a
      timestamp on a past partition (data-correctness violation). Instead `fetch_extended_rest` now gates the book leg
      on `is_current_day` — a past-day backfill SKIPS `_fetch_extended_book_for_symbol` entirely (honest absence: no
      HTTP, no fabricated timestamp, no stray `attempted_failed` row); `book_snapshot_5` is captured going forward by
      the live WS connector. Candles/trades/funding unaffected. +4 unit tests. **Real-infra confirm still wanted:** a
      past-day + a current-day EXTENDED backfill to observe 0 past-book rows + a live current-book row (deferred to an
      attended run). **DONE 2026-07-30** (defi_satellite_ao_dispatch_batch1 finalize reconciliation), see
      defi_satellite_ao_dispatch_batch1_2026_07_25.md todo 46 for full evidence — batch CLI couldn't reach this gate so
      `fetch_extended_rest` was called directly: past-day produced 0 book rows (honest absence, no fabrication),
      current-day produced 1 real book row via the WS connector; the "real-infra confirm" bar is satisfied.
- [x] [FIX] P1. ✅ **FIXED — `unified-trading-library@08662724`.** Root cause: the `_VENUE_OVERRIDES` key was hyphenated
      `"EXTENDED-STARKNET"` but both lookup sites normalize via `venue.upper().replace("-","_")` →
      `"EXTENDED_STARKNET"`, so the override NEVER matched and rows fell through to `batch_tardis` (fabricated Tardis
      provenance on a self-archived venue). Renamed the key to `"EXTENDED_STARKNET"` → the override fires →
      `BATCH_EXTENDED` (honest; EXTENDED is always self-archived, no Tardis split). +3 unit tests. **Data-migration
      note:** existing rows already stamped `batch_tardis` are not auto-corrected — a manifest re-stamp is a separate
      attended step.
- [x] [VERIFY] P2. ✅ **ROOT-CAUSED (2026-07-19, workflow + adversarial verify against real requester-pays S3, AWS acct
      427895769566).** The field-name-mismatch hypothesis is **REFUTED** — real fills are
      `[address, {coin,px,sz,side,     time,hash,…}]` (legacy `node_fills/hourly`) / `{…, events:[[address,fill],…]}`
      (live `node_fills_by_block/hourly`), EXACTLY what the CURRENT parsers read (verified end-to-end:
      `_parse_node_fills(20250726/12)`→12,198 BTC rows, `_parse_node_fills_by_block(20250727/8)`→1,206 BTC rows). REAL
      cause = a PREFIX bug in the pre-2026-07-13 code (`fetch_trades` built `node_fills/hourly/{date}/{hour}/` — a
      hour-DIRECTORY prefix that never matched the real `{hour}.lz4` FILES → `list_blobs` returned ZERO blobs → the
      parser was NEVER invoked → 100% empty_confirmed/ SOURCE_RETURNED_ZERO across 12,179 attempts). **Already fixed
      forward `market-tick-data-service@c48096e7` (2026-07-13)** — NO parser code change needed. Remaining is
      OPERATIONAL only (backfill re-run — see the tracked follow-up below). Secondary: `S3_TRADES_START=2025-03-22`
      (hyperliquid_s3.py:63) overstates availability — the earliest real `node_fills` partition is 2025-05-25, so
      2025-03-22..2025-05-24 is genuine upstream absence.
- [x] [FIX] P2. ✅ **HEALED (2026-07-19).** The `live_hyperliquid` template gap was already fixed
      (`possible_manifest.py` emits the `live_hyperliquid` prefix), so the false-flagged shards just needed the reverse
      re-validation pass:
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi     --unphantom-only --venues HYPERLIQUID`
      flipped **1,277** cefi HYPERLIQUID phantom rows (derivative_ticker 522 / book_snapshot_5 382 / trades 373) back to
      `captured` — VERIFIED on real infra: 0 `phantom_captured_no_parquet` HL rows remain, cefi index row-count stable
      (9,914,467, no regression). defi index re-checked = already clean (0 phantoms). **Deferred (tracked below):** the
      remaining ~35 mis-flagged live-WS CEX shards (20 live_kraken + 15 live_binance) need a UAC extra-live-probe entry
      for cefi, which conflicts with the deliberate RULE 11 "prediction-scoped only" invariant — an operator/attended
      design decision, not force-changed autonomously.
- [x] [CODE] P3. ✅ **DONE — `market-tick-data-service@ab86a214`.** Correction to the original note: the stub WAS called
      (`hyperliquid_adapter.py:398`, the 2024-10-29..2025-03-21 Tardis-window branch of
      `HyperliquidAdapter.fetch_trades`), but that adapter is NOT the real batch trades path
      (`onchain_perp_batch_handler._fetch_hyperliquid` uses `HyperliquidS3Downloader` for all 3 HL data_types), and
      every `fetch_trades` branch already returned `[]`. Deleted `_download_trades_from_tardis` + inlined an honest
      `return []` (no behavior change — the Tardis-window trades source was never implemented; real HL trades come from
      S3 from 2025-05-25). +tests updated.
- [x] [DECISION] P1. ✅ **RESOLVED (operator 2026-07-18), recorded here in
      `non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`: PACIFICA STAYS DECOMMISSIONED; LIGHTER kept MVP.**
      The 07-18-vs-07-16 conflict is resolved in favor of the 2026-07-16 decommission — operator: "decommission pacifica
      for now". PACIFICA remains fully removed (no MVP, no scaffold; the 07-18 keep-MVP answer is retracted), locked by
      `DECOMMISSIONED_VENUE_BASES` + the stays-removed test @a7ff8417. LIGHTER-ZKSYNC keeps MVP (live_capable honestly
      False, batch scaffold real). Original flag retained below.
- [x] [DECISION-history] P1. ~~PARTIALLY DECIDED + SSOT CONTRADICTION FLAGGED (2026-07-18).~~ Operator answered "keep
      MVP + BLOCKED-CREDENTIALS scaffold" for PACIFICA-SOLANA + LIGHTER-ZKSYNC. Applied for **LIGHTER-ZKSYNC** (it
      exists): `live_capable` flipped honestly to False (batch scaffold preserved) — `unified-api-contracts@a7ff8417`.
      **BUT PACIFICA-SOLANA is a hard conflict — NOT actioned.** A non-Tardis fix-investigation (2026-07-18) found
      PACIFICA was **decommissioned entirely on 2026-07-16** (operator ruling, recorded here in
      `non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`: all Solana perp DEXes dropped except Jupiter) — it
      is locked in `venue_adapter_keys.DECOMMISSIONED_VENUE_BASES`, purged from `data_type_capability.py`, and guarded
      by a test. The 2026-07-18 "keep PACIFICA MVP" answer therefore **CONTRADICTS the 2026-07-16 decommission**;
      resurrecting PACIFICA autonomously would undo a completed, locked decommission. **RESOLVED 2026-07-18** (stale
      "OPERATOR MUST RESOLVE" framing cleaned up 2026-07-28 — the conflict this entry raised was answered the same day
      it was filed; see the `[DECISION]` todo directly above: operator ruled in favor of the 2026-07-16 decommission,
      "decommission pacifica for now"). PACIFICA stays fully removed (a `PACIFICA-stays-removed` lock test was added
      @a7ff8417). The remaining PACIFICA FIX/VERIFY todos below are N/A per that resolution (see each todo's own note);
      the LIGHTER/EXTENDED ones are unblocked.
- [x] [FIX] P2. ✅ **N/A — PACIFICA decommissioned 2026-07-18 (venue fully removed; no pipeline to turn on).** ~~resolve
      the `derivative_ticker`/standalone-`perp_funding` duplicate-source risk~~ (`_umi_pacifica.py:227-276` and
      `_perp_funding_pacifica_lighter.py:125-175` both hit the same `/funding_rate/history` endpoint under two different
      canonical `data_type` labels) before either pipeline is ever turned on for real — same class of SSOT-ambiguity
      risk as the now-resolved MTDS/MDPS order-book-imbalance duplication
      ([[mtds_mdps_order_book_imbalance_duplicated_2026_07_07]]).
- [x] [FIX] P3. ✅ **PARTIALLY FIXED — `unified-api-contracts@a7ff8417`** (EXTENDED-STARKNET + LIGHTER-ZKSYNC). PACIFICA
      has NO row to fix — it was decommissioned 2026-07-16 (see the DECISION conflict above); do NOT re-add it. The
      genuinely-existing venues with the described dishonest declaration are EXTENDED-STARKNET + LIGHTER-ZKSYNC: flipped
      `live_capable=True → False` for all 3 data_types (trades/book_snapshot_5/derivative_ticker) to reflect the
      `BLOCKED-CREDENTIALS` live-WS stubs; `batch_capable` stays True (MVP batch scaffold real). `live_capable` gates
      only the live-readiness surface (not the coverage denominator / batch_ready / MVP scope). +2 honesty-guard tests
      (incl. a PACIFICA-stays-removed lock). Flip back per data_type when a real live connector + credentials land.
- [x] [VERIFY] P3. ✅ **VERIFY-ONLY — no change (2026-07-19).** No real downstream consumer reads
      `asset_group=defi/data_type=perp_funding` for EXTENDED-STARKNET. The real funding data is captured + read as
      `cefi/derivative_ticker` (`funding_rate` column); `perp_funding` was retired for EXTENDED on 2026-07-08 and no
      `perp_funding` capability / expected shard exists for it, so no coverage/denominator/strategy/execution consumer
      can wrongly conclude Extended lacks funding coverage. (Optional non-blocking doc cleanup of a stale
      `- (perp_funding)` annotation noted, not actioned.)
- [x] [VERIFY] P3. ✅ **VERIFIED — classification DRIFT, not deliberate (2026-07-19).** UAC `VENUE_TO_ASSET_GROUP`
      canonically maps `HYPERLIQUID: "cefi"` (venue_constants.py:343) and HL's other 3 data_types honor it
      (`onchain_perp_batch_handler` writes `asset_group=cefi`), but `perp_funding_handler.py` routes HL/ASTER
      perp_funding through `get_write_bucket_name("market_data","defi")` + the defi recorder — a legacy path frozen when
      the standalone HL/ASTER/LIGHTER `perp_funding` shard was retired 2026-07-08. The drift left 916 HL + 642 ASTER
      captured rows stamped `defi`, redundant with `cefi/derivative_ticker.funding_rate`. Code cleanup + the row
      reconciliation are tracked below (the latter is operator-gated: delete-vs-re-home real GCS objects + index
      rebuild).

### Tracked follow-ups (opened 2026-07-19 from the finding closeout — larger / operator-gated)

- [x] [INFRA] P2. **HYPERLIQUID trades backfill re-run** — the parser/routing fix (`market-tick-data-service@c48096e7`)
      is code-correct but NO HL trades backfill has re-run since, so ~12,179 stale
      `empty_confirmed`/`SOURCE_RETURNED_ZERO` manifest rows persist. Re-run HL `trades` shards with the CURRENT code,
      **force/overwrite** (a plain skip-if-fresh launcher would treat the stale rows as already-attempted and skip),
      over the real-coverage window **2025-05-25.. 2025-07-27** (legacy `node_fills`) + **2025-07-28..today**
      (`node_fills_by_block`). 2025-03-22..2025-05-24 is genuine upstream absence — do NOT expect it to populate.
      HYPERLIQUID is exempt from the Tardis cap; use a SPOT backfill launcher, monitored (no fire-and-forget). Deferred
      from the autonomous session as a real-infra launch that warrants an attended start + progress watch. — already
      covered by defi_satellite_ao_dispatch_batch2_2026_07_26.md (see that doc for execution). **Cross-referenced
      2026-07-30** (defi_satellite_ao_dispatch_batch1 finalize reconciliation):
      `defi_satellite_ao_dispatch_batch1_2026_07_25.md` todo 43 independently closed the one real remaining gap
      (trailing 8 days, 2026-07-21..28, after 2 SPOT preemptions) — final: all 8 days 173/173 files; prior sweeps had
      already produced 85-95% captured coverage both windows, gap correctly left unattempted; no code change (parser fix
      `market-tick-data-service@c48096e7`, 2026-07-13). Both plans' HL-trades-backfill todos target the same underlying
      gap; batch1's Progress Log is the record of the final closure.
- [ ] [FIX] P3. **HYPERLIQUID k-prefix coin case-sensitivity** — `catalogue_symbols_for_venue`
      (`_onchain_perp_batch_symbols.py:132`) `.upper()`s the segment while `_fill_to_trade_row`
      (`hyperliquid_s3.py:585`) does a case-SENSITIVE exact `coin` match, so `kPEPE`/`kBONK`/`kSHIB`/… requested via the
      ALL-catalogue path become `KPEPE` and drop every real `kPEPE` fill → those instruments record zero even after the
      backfill. Majors (BTC/ETH) unaffected. Fix needs the canonical-vs-native HL coin-case convention resolved (risk of
      a shard-key mismatch), so deferred from the unattended session.
- [x] [CODE] P3. **Delete the retired perp_funding DeFi-routing residue** — remove the stale `hyperliquid`/`aster`/
      `lighter` entries from `_PROTOCOL_PIPELINE_SOURCE` (perp_funding_handler.py:188-194) + `_chain_map` (:244-249) and
      delete the spent one-off `scripts/backfill_hl_funding_from_s3_asset_ctxs_2026_06_17.py` (its `asset_group=defi`
      hardcode is the drift source; target bucket 404s; past its own `# Delete-when:`), so a re-run can never re-stamp
      DeFi HL/ASTER perp_funding. (Verify the `protocols` iterable no longer includes them before deleting.) — already
      covered by defi_satellite_ao_dispatch_batch2_2026_07_26.md (see that doc for execution).
- [ ] [INFRA] P3. **Dispatched to batch-6 todo 24 (still `[ ]` as of 2026-08-05)** — Auto-resolved 2026-07-28, retagged
      away from its prior operator-decision gate. Reconcile the 916 HL + 642 ASTER `defi/perp_funding` legacy rows
      (redundant with `cefi/derivative_ticker.funding_rate`) by executing option (a) — DELETE the orphaned
      `defi/perp_funding` objects + manifest rows + rebuild the defi index (the redundant/simpler default; option (b)'s
      re-stamp-and-move is not needed since the data is fully redundant with the cefi-side funding history).
      Reversibility cleared per finding T / `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a:
      `mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md` todo 7 confirmed the SAME bucket
      (`market-data-tick-defi-prd-central-element-323112`) at `604800s` GCS Soft Delete retention as of 2026-07-27 (one
      day prior to this retag, bucket-level retention config, not a per-object/day-to-day setting — no reason to expect
      drift). **Whoever executes this todo should re-verify `gcs_bucket_soft_delete_retention_seconds()` fresh in the
      same run before the actual delete** (cheap, and keeps the finding-T check genuinely same-run for the destructive
      step itself) rather than treating this citation as a substitute for that — but no fresh operator ask is needed to
      START this dispatch. **(Batch-6 status: NOT YET DONE — the only unchecked todo remaining in batch-6.)**
- [ ] [FIX] P3. **Dispatched to batch-6 todo 24 (still `[ ]` as of 2026-08-05)** — RULED 2026-07-28 (retagged away from
      its prior operator-decision gate) — RELAX RULE 11 to cover cefi Ruling applies the operator's standing
      live-probing-scope theme directly: "live probing should be relaxed to cover all asset groups and shards wherever
      needed — err toward broader/more permissive scope, not narrower." That resolves this in favor of relaxing, not
      leaving it as a known gap. Concrete task: add `CEFI: ("binance","bybit","kraken","okx")` to
      `_EXTRA_LIVE_PROBE_SOURCES_BY_AG` (UAC `possible_manifest.py`); relax/rename
      `test_prediction_live_union_is_prediction_scoped_only` so its name + docstring assert the new (prediction + cefi
      CEX) scope rather than claiming prediction-only (a stale invariant name after this change is its own future
      false-confidence trap); re-run the phantom-row auditor to confirm the ~35 currently mis-flagged real live shards
      (20 live_kraken + 15 live_binance) flip from `phantom_captured_no_parquet` to `captured`. Full-completion mandate
      (no shortcuts): grep for any OTHER consumer that assumes RULE 11 is prediction-exclusive before landing, so no
      half-relaxed invariant is left contradicting the code elsewhere. (repo: unified-api-contracts)

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - the k-prefix todo needs the canonical-vs-native HL coin-case
  convention resolved first (shard-key-mismatch risk); the other 2 are ruled and AO-ready but the doc cannot flip as a
  unit

- **2026-07-07** — Filed after a 4-agent smoke-test workflow (real adapter-code read + live public-API probes + real GCS
  manifest/object cross-check, one agent per venue) confirmed the operator's suspicion that these 4 bespoke-API venues
  needed independent verification, unlike Tardis-routed venues. Found 4 independent real bugs (LIGHTER-ZKSYNC
  Tardis-slug mismatch, EXTENDED-STARKNET date bug + provenance mislabel, HYPERLIQUID batch-trades gap + manifest
  false-negative) plus 2 fully-dormant-but-code-correct venues (PACIFICA-SOLANA, and 3-of-4 data_types on
  LIGHTER-ZKSYNC). No code changed yet — this is the findings ledger; fixes are queued as todos above, ordered by
  whether they're a narrow confirmed bug (P0/P1) vs. requiring an operator MVP-scope decision (P1 DECISION) vs.
  lower-priority cleanup/classification review (P2/P3).

- **2026-07-13** (fresh CeFi futures/derivatives triage pass, unrelated session, corroborating only) — Redoing a lost
  triage pass on `data_pipeline_e2e_check_2026_07_10.md` todo 25's CeFi futures/derivatives cluster, PACIFICA-SOLANA's
  `no_parquet_under` sweep results for `trades`/`book_snapshot_5`/`derivative_ticker` were independently re-verified via
  3 fresh, real, solo VM runs (day=2026-07-09, `--legs force`). All 3 confirm the SAME mechanism, one layer more
  specific than this doc's original finding: Pacifica's public REST API returns **HTTP 429 on every single request** —
  `/trades/history` for all 7 top coins (BTC/ETH/SOL/HYPE/XRP/DOGE/BNB) and `/book` for the subset checked (BTC/SOL/XRP)
  — even through the existing `get_with_429_retry` exponential-backoff helper (3 retries, 2s/4s/8s schedule) exhausting
  on every single call, not just the first. This is consistent with, and gives a concrete mechanism for, this doc's
  "operationally dormant" finding (zero production capture ever) — not a new bug, and not independently investigated
  further here given todo 159's own P1 DECISION gate (operator MVP-status call) already blocks further code work on this
  venue. Worth noting for whoever picks up that decision: the adapter's retry budget (max 14s of backoff) is empirically
  insufficient for Pacifica's actual rate-limit recovery window — a real, bounded, narrow-scope fix (either a longer
  backoff schedule or an inter-coin delay) IS available if the operator decides this venue stays in scope, but was not
  attempted here (would need proving against Pacifica's real, undocumented rate-limit policy, itself another real-VM
  round-trip, and is downstream of the MVP-status decision anyway).

- **2026-07-18 (autonomous session) — MVP DECISION recorded + confirmed-bug assessment.** Operator ruled 2026-07-18:
  **keep PACIFICA-SOLANA + LIGHTER-ZKSYNC MVP + BLOCKED-CREDENTIALS scaffold** (recorded in the [DECISION] todo above),
  which UNBLOCKS the FIX/VERIFY todos. Assessed each confirmed bug for safe unattended execution and DECLINED to rush
  any — all are subtle venue-pipeline / data-correctness fixes the codebase itself flags for careful design, and a naive
  fix would violate a HARD RULE:
  - **LIGHTER `_VENUE_OVERRIDES` key** (`pipeline_mode_resolver.py:74`): the code comment already documents this DEAD
    key + warns a "blind key rename to LIGHTER_ZKSYNC would be WRONG for manifest-rebuild call sites reading
    pre-2026-04-17 native-REST rows … needs a date-aware or source-aware fix, not a rename; left as-is per operator
    triage." A rushed rename would mis-stamp legacy native-REST rows as batch_tardis.
  - **EXTENDED book_snapshot_5 date** (`_umi_extended.py:449`): `ts_ms = datetime.now()` + the day-window filter
    (`if ts_ms < start_ms or ts_ms >= end_ms: return`) correctly rejects past-day backfills BECAUSE the
    `/info/markets/{symbol}/orderbook` endpoint returns the CURRENT book (no historical). The naive "use the target
    date" fix would FABRICATE a timestamp (claim a live snapshot happened on a past day) — a data-correctness /
    honest-absence violation. The real fix is a venue-semantics decision (is EXTENDED book_snapshot live-only? honest
    no-attempt for past days) requiring investigation of whether EXTENDED exposes a historical orderbook endpoint.
  - EXTENDED override-not-applying, HYPERLIQUID 373/540 phantom false-negative, PACIFICA duplicate-source + live_capable
    honesty flip — each a real fix but each needs venue-specific verification + a real-VM round-trip; not safe to land
    blind unattended. **Net:** the MVP decision is resolved; these FIX/VERIFY todos remain open as tracked,
    careful-design work (the safe outcome per the autonomous safety rules — no fabricated timestamps, no
    manifest-rebuild breakage for a checkbox).

- **2026-07-18 (autonomous) — 3 confirmed bugs FIXED (correct, non-fabricating) + 2 scoped for attended work + 1 SSOT
  conflict flagged.** A 5-agent investigation pinned the precise correct fix + data-correctness risk for each bug; I
  applied the three that are unit-testable with zero data-correctness risk, and captured the rest.
  - ✅ **EXTENDED override key** — `unified-trading-library@08662724` (key underscore-normalized → BATCH_EXTENDED).
  - ✅ **EXTENDED book_snapshot_5** — `market-tick-data-service@55dac12a` (current-only endpoint → skip past-day, honest
    absence; the naive "target-date stamp" was rejected as a fabricated-timestamp violation).
  - ✅ **EXTENDED/LIGHTER live_capable** — `unified-api-contracts@a7ff8417` (True→False honest; batch scaffold kept).
  - ⚠️ **PACIFICA SSOT CONTRADICTION** — the 2026-07-18 "keep MVP" answer conflicts with the 2026-07-16 full
    decommission (locked in `DECOMMISSIONED_VENUE_BASES`). NOT actioned; operator must resolve (see the DECISION todo).
  - 🔭 **LIGHTER-ZKSYNC pipeline_mode** (SCOPED, not applied — multi-file cross-repo + a new UAC enum + real-infra
    verify). Correct fix (per investigation): DELETE the dead `_VENUE_OVERRIDES["LIGHTER"]` key; make source-blind
    `(LIGHTER-ZKSYNC, ohlcv_1m)` derivation return `None` (honest not-derivable, NEVER fabricate batch_tardis on native
    `source=lighter_api` /candles rows); thread the row's `source` through `backfill_pipeline_mode.py` +
    `manifest_writer/_writer_ingest.py` + `rebuild_cefi_manifest.py`; register `PipelineMode.BATCH_LIGHTER_API` +
    `lighter_api` in UAC `SOURCE_PRIORITY[(cefi,ohlcv_1m)]`. Needs a `--dry-run` against the real cefi manifest to read
    each row's true `source`/`pipeline_mode=` path segment before any `--force` re-stamp. → author as its own plan.
  - 🔭 **HYPERLIQUID phantom 373/540** (SCOPED) — the auditor's `possible_manifest._canonical_pipeline_mode_prefixes`
    ALREADY iterates `Mode.LIVE`, so `live_hyperliquid` is now covered (the original false-phantom is likely already
    resolved). Remaining: (a) a no-risk 1-line hardening to also emit `replay_<source>/` prefixes
    (`(Mode.BATCH, Mode.LIVE, Mode.REPLAY)`) to close a latent replay_ gap; (b) run the reconciler `--unphantom` reverse
    pass on real infra to heal any already-flipped rows. → fold into the phantom-audit plan.

- **2026-07-18 (autonomous, continuation) — operator: "decommission pacifica for now" + "do LIGHTER/HYPERLIQUID now".**
  - ✅ **PACIFICA — resolved to DECOMMISSIONED** (07-16 stands, 07-18 keep-MVP retracted; see the DECISION todo). No
    code needed (already removed + locked); N/A'd the moot PACIFICA todos.
  - ✅ **LIGHTER-ZKSYNC pipeline_mode — CORE FIXED `unified-trading-library@d59f14db`** (source-blind ohlcv_1m → None,
    never fabricate batch_tardis; dead key deleted; +4 tests). The positive `BATCH_LIGHTER_API` stamp + source-threading
    - the `--force` re-stamp are DEFERRED (see the FIX todo) — the positive stamp needs a full new-source
      SourceCapability wiring (real endpoints) that hit the closed-set cascade and shouldn't be guessed unattended.
  - ✅ **HYPERLIQUID replay-prefix hardening — DONE 2026-07-30** (defi_satellite_ao_dispatch_batch1 finalize
    reconciliation), see defi_satellite_ao_dispatch_batch1_2026_07_25.md todo 45 for full evidence. The 1-line
    `Mode.REPLAY` add to `possible_manifest._canonical_pipeline_mode_prefixes` (was previously deferred here — UAC tree
    was foreign-contended at the time) shipped `unified-api-contracts@6456dd23`: `_canonical_pipeline_mode_prefixes` now
    iterates `(Mode.BATCH, Mode.LIVE, Mode.REPLAY)`; the prefix-count guard was NOT quiescent (6 sources per AG are
    REPLAY-capable), so `test_extra_live_probe_sources_do_not_leak_cross_ag`'s expected counts were updated with the
    same explanatory-comment precedent as prior additions; `quality-gates.sh` green. The actual HYPERLIQUID 373/540
    false-phantom was already covered by the existing `Mode.LIVE` prefix (live_hyperliquid); this closes the
    future-proofing gap. The `--unphantom` reverse-pass heal remains a separate attended real-infra step, not addressed
    by this fix.

- **2026-07-28 (slot-16) — EXTENDED-STARKNET `/trades` cursor investigation: CONFIRMED it structurally cannot walk back
  to historical dates.** Live-probed `https://api.starknet.extended.exchange/api/v1/info/markets/{symbol}/trades`
  directly (BTC-USD + ETH-USD, several dozen calls) to test whether the descending `cursor` param can reach non-today
  data:
  - **Hard row cap, `limit` ignored**: `limit=5`, `limit=200`, `limit=1000`, `limit=5000` all returned exactly 50 rows
    every time — the endpoint silently clamps to a fixed 50-row page regardless of the requested limit.
  - **No-cursor call always returns a live, near-"now" window**: repeated calls with no `cursor` param tracked real time
    forward (`max T` always within ~1s of wall-clock `now`), confirming the endpoint serves a live rolling buffer, not a
    queryable historical store.
  - **`startTime`/`endTime` are silently ignored on `/trades`** (unlike Extended's `/candles`/`/funding`, which do honor
    them) — passing an explicit full-day past range (2026-07-01 00:00→24:00 UTC) returned `status: OK` + 50 rows, but
    the data was still today's live window, not the requested past day.
  - **`cursor` is forward-only (ascending), not a backward/descending walk**: passing a REAL trade id from a fetched
    page as `cursor` returned the NEXT ~50 trades strictly newer than that id (all returned ids > cursor, verified both
    directions — using the OLDEST id in a page as cursor returns trades starting ~1s after that id's timestamp, walking
    toward "now", never before it).
  - **Passing arbitrarily small/large cursor values (`0`, `1`, `5e17`, `1.04e18`, `2e18`, all far below the real live id
    range ~2.08e18) all returned the IDENTICAL most-recent ~50-row window** — if the store retained real history and
    cursor walked from an id, a near-zero cursor should have returned the earliest available trades; instead it always
    resolves to "now". This is the decisive evidence: the underlying trade store itself only retains a small live
    rolling buffer (empirically ~2-7 minutes of trades depending on symbol activity), not a full history — the `cursor`
    param can only page FORWARD within that live buffer, it cannot reach anything before it.
  - **No undocumented pagination param works either**: tried `before`, `toId`, `fromId`, `endId`, `offset` — all
    silently ignored (unknown query params don't error, they're dropped; output identical to no-param calls).
  - **Conclusion**: EXTENDED-STARKNET's `/trades` endpoint is structurally incapable of returning historical (non-today)
    data via any cursor value, date-range param, or undocumented pagination param tested. The manifest's "0 trades rows
    of any capture_status exist at any date" is the CORRECT, honest reflection of reality, not a bug in the backfill
    code — there is no code fix available here (the endpoint itself has no historical surface to call). This closes the
    § 3 "plausible but not confirmed" hedge with a definitive "confirmed cannot." Flips the corresponding todo in
    `plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md`.

- **context-scout 2026-08-03**: refreshed context_scope (5 entries, unchanged — still accurate).
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid (prior verdict re-affirmed) —
  of 3 open P3 todos, 1 (HYPERLIQUID k-prefix coin-case) is still deferred pending a genuine canonical-vs-native
  coin-case design decision; the other 2 are operator-ruled/AO-ready but since not ALL remaining work qualifies, the doc
  stays NA as a whole per the mixed-eligibility rule. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — re-confirmed independently. Content changed since
  the 2026-08-04 audit (a 2026-08-05 "reconcile batch-6 source docs" pass annotated 2 of the 3 open todos as "Dispatched
  to batch-6 todo 24 (still `[ ]` as of 2026-08-05)" — those 2 are operator-ruled/AO-shaped but already routed through
  an in-flight batch-6 dispatch rather than orphaned, so not a fresh RECLASSIFY signal here). The 3rd open item
  (HYPERLIQUID k-prefix coin-case, P3) still needs the canonical-vs-native coin-case convention resolved first
  (shard-key-mismatch risk) — a genuine judgment call. Doc stays `assigned_vm: NA` as a whole (mixed-eligibility rule,
  one genuine judgment item is enough).
- **round11-sweep 2026-08-09** (defi tranche, satellite-extraction + RECLASSIFY re-check): re-read end to end (3 open
  items at entry). Re-verified the 2 duplicate-claim citations live: `defi_satellite_ao_dispatch_batch6_2026_07_30.md`
  line ~453 still carries the identical open `[DIAG] P3` todo (unchecked — delete the 916 HL + 642 ASTER legacy
  `defi/perp_funding` rows + relax RULE 11), same source-doc citation — not stale, genuinely still in-flight there.
  Checked all 3 open items against every accumulated round11 precedent (IAM self-service, D16 all-repos, S5.1 tiering,
  plan-destination-defaults-AO-dispatched, escalation-N=3-days, reversibility-qualified deletes, Option B retired, GSM
  secret + 5 Slack webhooks now existing) — none apply: the 2 duplicate items are already dispatched elsewhere (flipping
  here would open a second dispatch path), and the HYPERLIQUID k-prefix item is still a genuine coin-case-convention
  design call, untouched by any round11 precedent. No satellite-extraction candidate found. Doc stays `assigned_vm: NA`
  (KEEP-NA valid, round11).
