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
    honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
  ]
created: 2026-07-07
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
- `trades`: **REAL code, structurally can't backfill** — the adapter's `/info/markets/{symbol}/trades` endpoint
  (`_umi_extended.py:284`) takes no `startTime`/`endTime` param at all (unlike Extended's candles/funding endpoints,
  which do), only a descending cursor. 0 rows of any capture_status exist. Plausible but not confirmed that deep
  historical cursor-walking can't reach old dates.
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
      market_id resolution + corrects data_type mapping to derivative_ticker.
- [x] [FIX] P0. ✅ **LIGHTER-ZKSYNC: fix the separate native-trades `limit=500` bug** —
      `_fetch_lighter_trades_for_symbol` hardcodes `"limit": "500"` on `GET /recentTrades`; Lighter rejects this with
      `HTTP 400`. Confirmed live: `limit≤100` returns real trades immediately. This is independent of the Tardis-slug
      bug above — it breaks the NATIVE (pre-2026-04-17) trades path specifically. One-line fix. —
      market-tick-data-service@0c4000a02 changes `_umi_lighter.py` limit param from "500" to "100".
- [ ] [FIX] P1. **LIGHTER-ZKSYNC: fix the `pipeline_mode_resolver.py:58` venue-key mismatch**
      (`_VENUE_OVERRIDES["LIGHTER"]` never matches the real normalized key `"LIGHTER_ZKSYNC"`) — also correct the
      override's own comment ("Solana perp" → zkSync) — and investigate why native `ohlcv_1m` capture stopped after
      2026-05-05.
- [ ] [FIX] P1. **EXTENDED-STARKNET: fix `_fetch_extended_book_for_symbol`'s date bug** (`_umi_extended.py:415`, uses
      `datetime.now(tz=UTC)` instead of the target backfill `date`) — this is why `book_snapshot_5` has zero rows ever
      despite otherwise-real code; re-run a backfill for a past day post-fix to confirm real rows land.
- [ ] [FIX] P1. **EXTENDED-STARKNET: fix the `pipeline_mode_resolver.py:56` override not applying** — real
      Extended-native data is currently mislabeled `pipeline_mode=batch_tardis, source=tardis` at every captured row;
      find why the declared `_VENUE_OVERRIDES["EXTENDED-STARKNET"]` override isn't reaching the real write path and fix
      the resolution, not just the override declaration.
- [ ] [VERIFY] P2. **HYPERLIQUID: root-cause the batch-trades zero-rows gap** — suspected field-name mismatch in
      `_parse_node_fills` (`hyperliquid_s3.py:403-408`) against the real S3 `node_fills` payload shape; confirm against
      a real downloaded S3 object before assuming this is the cause, then fix.
- [ ] [FIX] P2. **HYPERLIQUID: fix the manifest false-negative** flagging 373/540 real `live_hyperliquid` shards as
      `phantom_captured_no_parquet_at_canonical_path` when the parquet demonstrably exists at the canonical path —
      likely a phantom-audit path-construction bug specific to this pipeline_mode; scope may extend beyond this one
      venue, check other `live_*` pipeline_modes too.
- [ ] [CODE] P3. **HYPERLIQUID: delete the dead stub** `HyperliquidAdapter._download_trades_from_tardis()`
      (`hyperliquid_adapter.py:424-427`) — confirmed never called by the real batch pipeline; leaving a known-broken
      method around is a trap for a future engineer who assumes it's live.
- [x] [DECISION] P1. ✅ **DECIDED (operator 2026-07-18): KEEP MVP + BLOCKED-CREDENTIALS scaffold.** Per the
      external-data-always-available rule — do NOT descope PACIFICA-SOLANA/LIGHTER-ZKSYNC; build the adapter scaffold,
      mark the live connectors `BLOCKED-CREDENTIALS`, and flip `live_capable` honestly (see the P3 `live_capable` todo
      below). This UNBLOCKS the remaining FIX/VERIFY todos in this doc (they no longer wait on the MVP-scope call).
- [ ] [FIX] P2. **PACIFICA-SOLANA: resolve the `derivative_ticker`/standalone-`perp_funding` duplicate-source risk**
      (`_umi_pacifica.py:227-276` and `_perp_funding_pacifica_lighter.py:125-175` both hit the same
      `/funding_rate/history` endpoint under two different canonical `data_type` labels) before either pipeline is ever
      turned on for real — same class of SSOT-ambiguity risk as the now-resolved MTDS/MDPS order-book-imbalance
      duplication ([[mtds_mdps_order_book_imbalance_duplicated_2026_07_07]]).
- [ ] [FIX] P3. **PACIFICA-SOLANA: correct UAC's `live_capable=True` declaration** (`data_type_capability.py:598-608`)
      for trades/book_snapshot_5/derivative_ticker to reflect that the live connector is a `BLOCKED-CREDENTIALS` stub,
      not a working live path — either flip to `False` until real credentials land, or build the real connector.
- [ ] [VERIFY] P3. **EXTENDED-STARKNET: check whether any downstream consumer reads
      `asset_group=defi/data_type=perp_funding`** for this venue specifically, rather than `cefi/derivative_ticker`
      where the real funding data actually lives — if one exists, it would incorrectly conclude Extended has no funding
      coverage.
- [ ] [VERIFY] P3. **HYPERLIQUID: review why `perp_funding` is classified under the `defi` manifest bucket** rather than
      `cefi`, given HYPERLIQUID is otherwise tracked as an MTDS/CeFi-style venue for its other 3 data_types — confirm
      whether this is deliberate or a classification drift.

## Progress Log

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
