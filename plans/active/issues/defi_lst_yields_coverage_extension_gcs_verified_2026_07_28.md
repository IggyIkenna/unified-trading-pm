---
doc_type: issue
title:
  "features-onchain lst_yields (exactly 15 days GCS-verified) vs MTDS lst_rates raw corpus (multi-year, GCS-verified) —
  confirmed a features-layer backfill gap, not raw-data absence; proposed backfill scope"
summary: >-
  The `pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md` doc flagged `lst_yields` (the
  features-onchain feature group the strategy-service STAKING leg now reads via `CanonicalLstYieldsIndexProvider`,
  shipped `strategy-service@e93902d8`) as "only 15 days total as of 2026-07-23" and deferred filing a coverage-extension
  follow-up until the source of the gap was confirmed. This doc does that confirmation via live, bounded, prefix-scoped
  GCS reads (no whole-corpus walk): `features-defi-prd-central-element-323112`'s `onchain/by_date/*/feature_group=
  lst_yields/` really is exactly 15 day-partitions (2026-04-03..2026-04-19, with a 2-day internal gap on 2026-04-13/14),
  while `market-data-tick-defi-prd-central-element-323112`'s raw `lst_rates` corpus — the sole upstream input
  `compute_lst_features_for_day` reads via `load_oracle_prices` — carries real data for every sampled EVM LST venue
  spanning years before and after that 15-day window (LIDO stETH/wstETH confirmed 2021-08-17..2026-07-27; ETHERFI weETH
  confirmed at least 2024-01-01..2026-07-27; all 11 currently-active EVM LST venues confirmed present on a single
  representative day, 2026-04-10, inside the gap window). This is a features-layer batch-compute/backfill lag, not a
  raw-data absence — the batch orchestrator (`features_service.onchain.cli.main --feature-group lst_yields`) already
  accepts an arbitrary `--start-date`/`--end-date` range and was evidently only ever invoked for this one 15-day window.
  Proposes the concrete backfill scope (owning repo, date range, mechanism) per its own `[DATA]` follow-up todo below;
  does NOT implement the backfill.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, lst_yields, lst_rates, coverage-gap, backfill-scope, features-onchain, gcs-verified]
related:
  [
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: 2026-07-28
parent_epic: infrastructure_master
source: [data_engineering slot-12, 2026-07-28, dispatched via defi_satellite_ao_dispatch_batch1-049]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

# `lst_yields` coverage-extension follow-up — GCS-verified date ranges + proposed backfill scope

## Context

`pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md` shipped the STAKING leg of `carry_staked_basis`
(`strategy-service@e93902d8`) reading `feature_group=lst_yields` via the new `CanonicalLstYieldsIndexProvider`, and
flagged in its own "Lessons"/"Deferred work" sections that `lst_yields` is "only 15 days total as of 2026-07-23" — a
real gap that would silently book zero STAKING PnL on any day outside that window — and deferred filing the coverage-
extension follow-up until "the audit confirms the source" (plausibly a features-layer compute lag rather than the raw
data genuinely being absent). This doc is that confirmation, done via live GCS reads only (no code changed).

## Methodology (bounded, prefix-scoped — no whole-corpus walk)

Every read below is either (a) an exact-prefix `gcloud storage ls` on a fully-known partition path (a single API list
call per date), or (b) a wildcard confined to ONE already-known partition segment (e.g. `day=*` under
`onchain/by_date/`, or `pipeline_mode=*` under one known `day=`), never an unscoped `**` walk of either bucket. The
`onchain/by_date/` delimiter descent (119 day-partitions total) and the `raw_tick_data/by_date/` delimiter descent
(2,400 day-partitions total, 2020-01-01..2026-07-27 — the full DeFi raw-tick corpus across every data_type, not just
`lst_rates`) are both single, cheap, top-level listings; the per-venue/per-day `lst_rates` checks are bounded to a
small, deliberately-chosen sample of anchor dates (corpus start, several multi-year midpoints, the window edges, and
"today"), not an exhaustive per-day walk.

## Finding 1 — `features-onchain lst_yields`: exactly 15 day-partitions, GCS-verified

```
gcloud storage ls "gs://features-defi-prd-central-element-323112/onchain/by_date/*/feature_group=lst_yields/"
```

returns exactly 15 `day=` partitions, contiguous except for one 2-day internal gap:

```
2026-04-03  2026-04-04  2026-04-05  2026-04-06  2026-04-07  2026-04-08  2026-04-09  2026-04-10
2026-04-11  2026-04-12  [2026-04-13 MISSING]  [2026-04-14 MISSING]  2026-04-15  2026-04-16
2026-04-17  2026-04-18  2026-04-19
```

15 days total (10 + 5) — matches the "~15 days total as of 2026-07-23" figure in the source doc exactly. The 2-day gap
(2026-04-13 Monday, 2026-04-14 Tuesday) is NOT a weekend (04-11/04-12 Sat/Sun ARE present) — a genuine, unexplained
2-day hole inside the window, consistent with two separate manual backfill invocations
(`--start-date 2026-04-03 --end-date 2026-04-12` then `--start-date 2026-04-15 --end-date 2026-04-19`) rather than one
continuous run, though the exact cause (two separate manual runs vs. a 2-day write failure) was not traced further — out
of this doc's read-only scope. The wider `onchain/by_date/` corpus (119 day-partitions total, spanning
2026-01-25..2026-05-22 plus one isolated `2026-07-26` partition) confirms `lst_yields` was never computed for ANY other
on-chain feature-compute day either — this is not an `lst_yields`-specific quirk, the whole onchain-features corpus is
sparse, but `lst_yields` specifically is the doc's concern.

## Finding 2 — MTDS `lst_rates` raw corpus: multi-year coverage per EVM LST token, GCS-verified

The sole upstream input: `features_service.onchain.app.core.data_loader.OnChainDataLoader.load_oracle_prices()` reads
directly from MTDS's `oracle_prices` + `lst_rates` bypass buckets via `_resolve_mtds_parquet_files()`, which lists
`{bucket}/raw_tick_data/by_date/day={date}/asset_group=defi/venue=*/chain=*/instrument_type=*/data_type=lst_rates/ {file}.parquet`
(falling back to the pre-77abd56 legacy `day={date}/` prefix) — i.e. it reads the exact GCS layout
`lst_rates_handler.py` writes via `write_defi_rows`/`build_defi_partition_path`. There is no other lst_yields input.

**LIDO (stETH, wstETH) — confirmed present 2021-08-17 through 2026-07-27** (11 sampled anchor dates across the full
span, including the corpus's own earliest day-partition 2021-08-17 and its latest, 2026-07-27 — the day before "today"):

| date       | stETH | wstETH                                               | notes                                                                                                  |
| ---------- | ----- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 2021-08-17 | ✅    | (n/a — wstETH file absent this early, stETH present) | earliest raw_tick_data day-partition in the whole bucket                                               |
| 2023-01-15 | ✅    | ✅                                                   |                                                                                                        |
| 2024-06-01 | ✅    | ✅                                                   |                                                                                                        |
| 2026-01-01 | ✅    | ✅                                                   |                                                                                                        |
| 2026-03-25 | ✅    | ✅                                                   | inside the window's lead-up                                                                            |
| 2026-04-01 | ✅    | ✅                                                   | 2 days before the `lst_yields` window starts                                                           |
| 2026-04-10 | ✅    | ✅                                                   | inside the `lst_yields` window                                                                         |
| 2026-04-20 | ✅    | ✅                                                   | 1 day after the `lst_yields` window ends                                                               |
| 2026-05-01 | ✅    | ✅                                                   |                                                                                                        |
| 2026-06-01 | ✅    | ✅                                                   |                                                                                                        |
| 2026-07-20 | ✅    | ✅                                                   | filename shape shifted to canonical `LIDO-ETHEREUM:LST:stETH.parquet` by this point (see caveat below) |
| 2026-07-27 | ✅    | ✅                                                   | latest raw_tick_data day-partition in the whole bucket                                                 |

**ETHERFI (weETH) — confirmed present at least 2024-01-01 through 2026-07-27**; confirmed ABSENT at 2021-08-17 and
2023-06-01 (genuine absence, not a gap — ether.fi's weETH launched later than Lido's stETH, so a shorter real history is
expected and correct, not a bug).

**All 11 currently-registered EVM LST venues present on a single representative in-window day (2026-04-10)** — one
bounded listing
(`day=2026-04-10/pipeline_mode=*/asset_group=defi/venue=*/chain=*/instrument_type=lst/data_type= lst_rates/`) shows real
`lst_rates` parquets for every EVM token `_EVM_LST_ABI_METADATA`/`LST_TOKEN_TO_PROTOCOL_ASSET` declare: LIDO (stETH,
wstETH), ETHERFI (weETH), ROCKETPOOL (rETH — note: the on-disk `venue=` value is `ROCKETPOOL`, not the UAC
`LST_TOKEN_TO_PROTOCOL_ASSET` dict key `ROCKET_POOL` — a cosmetic underscore mismatch between the raw GCS venue label
and the UAC protocol-name string, not a data gap; any reader keying off the UAC dict's exact string would need to
normalize), COINBASE (cbETH), ANKR (ankrETH), MANTLE (mETH), SWELL (swETH), STADER (ETHx), STAKEWISE (osETH), PUFFER
(pufETH), RENZO (ezETH), KELPDAO (rsETH) — plus the 4 Solana LSTs (JITO/jitoSOL, MARINADE/mSOL, BLAZESTAKE/bSOL,
SANCTUM/sanctumSOL, all confirmed a market-derived DefiLlama proxy for historical dates per the source doc's own
2026-07-23 finding, not genuine on-chain redemption rate — orthogonal to this doc's EVM-focused scope).

## Conclusion

**Confirmed: this is a features-layer batch-compute/backfill lag, not a raw-data absence.** The raw `lst_rates` corpus
for every EVM LST token that feeds `lst_yields` spans years on both sides of the 15-day feature window (LIDO alone: ~5
years vs. 15 days — a >99% gap in relative terms). `compute_lst_features_for_day`/`_process_lst_yields` take an explicit
`start_date`/`end_date` range and impose no windowing of their own
(`del force_reprocess # handled at write time by manifest freshness` — the function has no built-in lookback limit); the
15-day footprint reflects the batch orchestrator only ever having been INVOKED over that one narrow range, not any
structural limitation.

## Proposed backfill scope (NOT implemented in this doc)

- **Owning repo**: `features-service` — no new tooling needed. The existing batch CLI already supports arbitrary
  historical ranges:
  `python -m features_service.onchain.cli.main --mode batch --asset-group DEFI --feature-group lst_yields --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD>`.
- **Date range**: per-token earliest-available `lst_rates` day through today, honest-absence naturally handling any
  token whose own raw history starts later (e.g. ETHERFI/weETH need not backfill before ~2023-2024 — `extract_lst_rates`
  already emits per-token rows only for tokens present that day, so a shorter-history token simply contributes fewer
  rows without any special-casing). A conservative, cheap first cut: mirror the earliest EVM LST genesis already
  confirmed here — 2021-08-17 (LIDO) through today — and let the per-day, per-token honest-absence path in
  `compute_lst_features_for_day` handle every later-launching token correctly.
- **Mechanism**: re-run the existing batch orchestrator over the full range above via its current CLI entry point (no
  new code) — the same mechanism that already produced the 15-day window, just with a wider `--start-date`. This is an
  additive, resumable, idempotent write (per-day `feature_group=lst_yields/features.parquet`, one partition per day,
  WriteGate + emission-policy gated) — not a delete, not a schema change, and does not touch the raw MTDS corpus.

## Todos

- [ ] [DATA] P1. Execute the backfill per the scope above: run
      `features_service.onchain.cli.main --mode batch     --asset-group DEFI --feature-group lst_yields --start-date 2021-08-17 --end-date <today>`
      (chunked into manageable sub-ranges if a single invocation proves impractical), monitored per the
      no-fire-and-forget discipline (progress = new `day=` partitions appearing under
      `onchain/by_date/*/feature_group=lst_yields/`, not just process liveness). Repo: features-service. **Done when**:
      `gcloud storage ls     "gs://features-defi-prd-central-element-323112/onchain/by_date/*/feature_group=lst_yields/"`
      shows day-partitions spanning materially more than the current 15 days (targeting near-full coverage from each
      token's own genesis), and the STAKING leg's honest-absence log rate for `carry_staked_basis` positions drops
      correspondingly. Source: this doc.

## Progress Log

- **2026-07-28 (slot-6)**: Before the backfill could write ANY day, hit two independent bugs that made `lst_yields` (and
  sibling `lst_native_rates`) 100%-unwritable — not historical-data-specific, reproduced even on 2026-04-10 (already
  inside the prior successful window) when re-run under current code. Root-caused + fixed both (see
  `/plans/active/issues/lst_yields_writegate_permanently_blocked_2026_07_28.md` for full detail): (1)
  `lst_native_rate_ts` called `.dt.epoch()` on the raw MTDS `timestamp` column, which is a bare `YYYY-MM-DD` string not
  a Datetime, producing all-null and tripping the WriteGate's 95%-NaN threshold; (2) unmapped tokens (not in UAC
  `LST_TOKEN_TO_PROTOCOL_ASSET`) were left in output with null protocol/asset, dragging `completeness_fraction` below
  1.0 and tripping the `STRICT_FAIL` emission policy for the WHOLE day, not just the unmapped token. Shipped
  `features-service@3e59ea63`. Verified real GCS writes for 2024-01-01..03 (14/16/16 rows). Full features-service test
  suite green (17964 passed) before shipping. Then launched the actual backfill: chunked into 60 monthly sub-ranges
  (2021-08-17 → today), each invocation via `--skip-dependency-check` (required — MTDS has never captured a
  `perp_funding` data_type for DEFI at any date, an unrelated pre-existing dependency-checker gap also flagged in the
  same issue doc as a P2 follow-up; NOT needed for `lst_yields` itself, which only reads `lst_rates`+`oracle_prices`).
  Running as a persistent background supervisor with per-chunk retry (3 attempts) and GCS day-partition-count
  verification after each chunk — that count, not process liveness, is the progress metric. At ~30s/day of real GCS I/O
  (no per-day parallelism in the CLI), the full ~1800-day range is a multi-hour operation; expect this to span multiple
  session turns. If this session ends before the supervisor finishes, the backfill is fully resumable: re-invoking the
  same monthly chunk list is safe because each completed chunk's `start_date` becomes fresh in the manifest
  (skip-if-fresh now works correctly since the underlying write bug is fixed) — only genuinely-incomplete chunks would
  re-run.
