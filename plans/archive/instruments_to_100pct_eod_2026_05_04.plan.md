---
doc_type: plan
title: instruments-service to 100% honest coverage across all 5 asset groups (2026-05-04 → 2026-05-05)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-04
priority: P0
owner: harsh
completed: 2026-05-05
type: deployment
epic: data-pipeline-completion
completion_gates: { code: none, deployment: D2, business: none }
repo_gates:
  - { repo: instruments-service, deployment: D2 }
depends_on: [instruments_and_market_tick_data_completion_2026_05_01]
isProject: false
---

## Deferred work — migrated to: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`,

`plans/active/data_completion_cefi_2026_07_15.md`,
`plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md`,
`plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md`,
`plans/active/prediction_consolidated_closeout_2026_07_18.md`, `plans/active/defi_consolidated_closeout_2026_07_18.md` —
successor: (see list above) (all 32 open items resolve to HAS_SUCCESSOR or STALE_OBSOLETE across this successor family —
scope-definition/Phase-0-diagnose/phantom-flips/per-AG backfills all continue in the current data-completion-to-100%
plan chain; POLYGON adapter items are moot (Polygon.io/"Massive" removed as a tradfi source 2026-07-19); FRED adapter
gap is tracked live in `macro_micro_econ_data_capture_audit_2026_06_05.md`. Two items (sports IAM-grant blocker, DEFI
EIGENLAYER-rewards phantom count) are AMBIGUOUS — no exact-match successor confirmed, but strong circumstantial evidence
both were resolved out-of-band (later sports VM launches succeed;
`data_completion_defi_2026_07_15.md`/`defi_consolidated_closeout_2026_07_18.md` likely absorbed the DEFI item) —
recommend an operator spot-check rather than a blind close. No genuinely orphaned items requiring a fresh issue doc.)

## Closeout 2026-05-05 (post-EOD ship record)

This plan ran 2026-05-04 → 2026-05-05. Most diagnostic + fix work is shipped on `live-defi-rollout`. The narrative
sections below are preserved as-is for the audit trail; this closeout summarizes what's actually done vs what's left.

### Shipped on `live-defi-rollout`

| Plan section                                          | Commit(s)                                                                                                           | What                                                                                                                                                                                                            |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SFI throttle (Day 1 sports section, lines ~2260–2299) | `04bc1bc`                                                                                                           | per-class throttle, SFI = 0.34s (3 req/sec under 4/sec plan)                                                                                                                                                    |
| Sports chunked backfill (Day 1, lines ~279–282)       | `619a32e`                                                                                                           | `sports_chunked_backfill.sh` — 30-day per-proc to bound RAM                                                                                                                                                     |
| Polymarket cursor-sharding (Day 1, lines ~2326–2418)  | `d7bd17f` + `b336834` + `5e902d5`                                                                                   | hybrid long-form/short-ticker + word-boundary + cursor env vars                                                                                                                                                 |
| Phantom audit hardening (5-axis)                      | `faf5466` + `e077b35` + `2c207e2`                                                                                   | path-prefix + chain-bundle + DeFi venue overload + schema-v4                                                                                                                                                    |
| Phantom audit reverse mode                            | `ed261cc`                                                                                                           | `--unphantom` self-heals stale phantom flags                                                                                                                                                                    |
| SFI local-dump → canonical                            | `bf429c0`                                                                                                           | 14,418 partitions, 36.5 min — `migrate_local_sfi_to_canonical.py`                                                                                                                                               |
| Per-VM shard CAS race fix                             | `00f6352`                                                                                                           | unique VM_NAME + `MANIFEST_PER_VM_SHARDS=true` per chunk worker                                                                                                                                                 |
| Per-asset-group tempfile                              | `4dcd0ff`                                                                                                           | concurrent dry-run isolation (Bandit B108)                                                                                                                                                                      |
| Per-league skip granularity                           | `880ffb4`                                                                                                           | skip-shard gate for MATCHES/PREDICTIONS/ODDS                                                                                                                                                                    |
| Skip-shard gate (sports)                              | `b881a0d`                                                                                                           | SFI + Transfermarkt entities                                                                                                                                                                                    |
| Drop \_LEAGUES from manifest (feat!)                  | `25f756d`                                                                                                           | stop writing TRANSFERMARKT_LEAGUES + SFI_LEAGUES                                                                                                                                                                |
| Pre-launch row purge                                  | `0382454`                                                                                                           | `purge_pre_launch_manifest_rows.py`                                                                                                                                                                             |
| 404 → empty_confirmed reclassifier                    | `03a8fac`                                                                                                           | `reclassify_404_failures_to_empty.py`                                                                                                                                                                           |
| Canonical league_id at every emit                     | `46962de`                                                                                                           | + VENUES per-day singleton + audit probes flat-path                                                                                                                                                             |
| `rebuild_cefi_manifest.py` argparse fix               | `0dd6e82`                                                                                                           | `args.category` → `args.asset_group`                                                                                                                                                                            |
| ES-OPT chain-bundle aggregator                        | `4323e09`                                                                                                           | `aggregate_legacy_es_opt_trades.py` migration                                                                                                                                                                   |
| Tardis-URDI fiat quote-asset preserve                 | `244d330`                                                                                                           | parse Bitfinex perp `BTCF0:USTF0` → BTC/USDT                                                                                                                                                                    |
| Manifest purge superseded rows                        | `3b23457`                                                                                                           | drop top-level no-league `attempted_failed` rows                                                                                                                                                                |
| **HYPERLIQUID single-SSOT discovery date**            | UAC `venue_mapping.py` + IS `orchestrator.py` + IS `hyperliquid.py` (this session)                                  | `venue_instrument_discovery_overrides` + `get_instrument_discovery_start` helper; adapter + orchestrator both consume from UAC. Drops 200 phantom missing dates. See "Action 4" section below for full details. |
| **Polymarket dual-schema audit gotcha**               | `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md` § "Audit-script gotchas" (this session) | Documents the question-format vs canonical-ID dual layout so future audits probe both.                                                                                                                          |

### Closed 2026-05-05 (no remaining follow-ups)

- [x] [SCRIPT] **DERIBIT cache validation** — instead of a live-VM smoke (which only validates one moment in time and
      would re-occur on every re-launch), the cache contract from `9d91465` is now locked by 4 unit tests in
      [`tests/unit/test_databento_tardis_adapter.py::TestTardisInstrumentsCacheContract`](../../../instruments-service/tests/unit/test_databento_tardis_adapter.py):
      (1) cache key is `instrument_type` only — different dates with same type return the same list reference (the
      memory-leak guard); (2) different `instrument_type` values get separate cache entries (correctness); (3) TTL is
      exactly 86400s (24h, the second half of the fix); (4) cache expires after TTL so a >24h backfill legitimately
      re-fetches rather than freezing forever. Any future refactor that regresses the cache key shape back to
      `(instrument_type, date)` fails QG. Closes the operational concern at the contract level — no live VM needed.
- [x] [AGENT] **ASTER same-divergence audit** — investigated 2026-05-05 (this session): 1. **API probe**: Aster's
      `exchangeInfo` endpoint returns Binance-Futures-API-compatible payloads with `onboardDate` fields that inherit
      Binance's listing dates (BTCUSDT shows `onboardDate=2021-07-30`, predating Aster's existence entirely). Not usable
      for venue-launch verification. 2. **GitHub provenance**: `asterdex/api-docs` repo created **2025-03-27** — neither
      candidate date (UAC 2024-10-01, adapter 2024-09-01) has authoritative external provenance; both were guesses by
      the original PR author. 3. **GCS capture probe**: zero ASTER captures across both buckets
      (`market-data-tick-cefi-central-element-323112`, `instruments-store-cefi-central-element-323112`) for any probed
      date in 2024–2025. Plan B prereq (BUG-X1 footnote 5) confirms ASTER is "genuinely stuck — 0 captured rows of any
      data_type". Zero historical data at risk regardless of which date wins. 4. **Resolution**: pick the LATER (more
      conservative) value — UAC's `2024-10-01` — and have the adapter consume it via
      `VenueMapping().get_instrument_discovery_start("ASTER")`. Adapter no longer carries a hardcoded date.
      [`instruments-service/.../adapters/cefi/aster.py`](../../../instruments-service/instruments_service/reference_data/adapters/cefi/aster.py)
      updated; smoke confirms `is_venue_available("ASTER", "2024-09-15") == False`,
      `is_venue_available("ASTER", "2024-10-01") == True`. No `venue_instrument_discovery_overrides` entry needed
      because UAC's value IS the discovery start (no second timeline like HYPERLIQUID's market-data vs discovery split).
      179/179 related tests pass.
- [x] **PLAYER_VALUES SSOT realignment + manifest rebuild** — diagnosed 2026-05-05 user-pushback session: the manifest
      reported PLAYER_VALUES coverage as if it were per-(day, league) over 2019-2026 (8,937 rows), the audit script kept
      flipping rows to `attempted_failed` with `phantom_captured_no_parquet_at_canonical_path`, and a band-aid script
      (`scripts/write_player_values_placeholders.py`) wrote 906 zero-row parquet placeholders to mask the drift —
      exactly the "fake placeholder that LOOKS populated" anti-pattern CLAUDE.md flags as worse than missing data. Real
      cause: orchestrator writes ONE bulk parquet per (date, season) at
      `entity=player_values/season={S}/player_values.parquet` containing all leagues; UAC SSOT was wrongly pointing at
      `entity=transfermarkt_teams/league={LID}/transfermarkt_teams.parquet` (per-league subpartition that never
      existed). Comprehensive 8-phase fix this session: 1. **Inventory** real bulk parquets — 2,548 files / 382,326 rows
      / 1,607 distinct dates / 32 leagues from 2018-01-01 to 2026-04-30. ALL non-zero. Saved at
      `/tmp/player_values_inventory.parquet`. 2. **Manifest rebuild** — backed up canonical manifest to
      `_index/availability_index.parquet.pre_player_values_rebuild_20260505T224032Z.bak`, dropped 8,937 legacy denorm
      rows, derived 15,002 honest captured rows from disk-truth (one per (snapshot date, league_id) actually present in
      the bulk parquet), wrote back. Backup deleted post-verification. 3. **Disk cleanup** — deleted ALL 906 zero-row
      placeholder parquets at `entity=transfermarkt_teams/...` (mine + prior agents' historical accumulation). Sanity
      probe confirms zero remain. 4. **UAC SSOT** — added `SportsPathLayout.PER_DAY_PER_SEASON` enum value;
      `SPORTS_DATA_TYPE_TO_FOLDER["PLAYER_VALUES"]` flipped from `"transfermarkt_teams"` → `"player_values"`;
      `SPORTS_DATA_TYPE_LAYOUT["PLAYER_VALUES"]` flipped to `PER_DAY_PER_SEASON`; `candidate_parquet_paths` extended
      with optional `season=` kwarg + 3-year window probe (year-1, year, year+1) when caller doesn't specify season —
      covers transfer-window overlap (743 of 2,548 inventory parquets had multi-season co-existence). File:
      [`unified-api-contracts/.../sports/gcs_paths.py`](../../../unified-api-contracts/unified_api_contracts/canonical/domain/sports/gcs_paths.py). 5.
      **Audit verification** — re-ran
      `reconcile_phantom_manifest_rows_all.py --asset-group sports        --data-types PLAYER_VALUES --dry-run`:
      **15,002 real captures / 0 phantoms**. Manifest is clean. 6. **No real backfill needed** — the data was always on
      disk; only the SSOT pointer was wrong. 7. **Lock + cleanup** — 7 unit tests in
      [`unified-api-contracts/tests/unit/sports/test_gcs_paths_player_values.py`](../../../unified-api-contracts/tests/unit/sports/test_gcs_paths_player_values.py)
      lock the post-fix layout (folder=player_values, layout=PER_DAY_PER_SEASON, explicit-season probe, 3-year window
      probe, intra-file league filtering, sanity for unaffected entities, malformed-day resilience, URI helper kwarg
      pass-through) — 7/7 pass. Band-aid script `scripts/write_player_values_placeholders.py` deleted. PM codex
      `02-data/availability-manifest-and-data-status.md` § "Audit-script gotchas" updated with the new layout +
      reference incident. 8. **Final coverage**: ALL 127 instruments-service shards across all 5 asset_groups ≥95%
      honest coverage: CEFI 15/15, TRADFI 6/6, DEFI 74/74, PREDICTION 14/14, SPORTS 18/18.

- [x] **Plan archive** — all open items closed; frontmatter `status` flipped from `active` to `complete`; file moved
      from `plans/active/` to `plans/archive/`. No `locked_by` field is set on this plan, so the CLAUDE.md "Plan
      Locking" `[unlock-plan]` commit-tag requirement does not apply.

## Adapter health summary (2026-05-04 13:36 IST)

| Asset group |   Healthy   | Failed        | Bug type                                              |
| ----------- | :---------: | ------------- | ----------------------------------------------------- |
| CEFI        |    7 / 9    | OKX, COINBASE | 3-SSOT canonical-name disagreement (multi-repo align) |
| TRADFI      |    6 / 8    | POLYGON, FRED | api_key not in SM (POLYGON), zero records (FRED)      |
| DEFI        |    7 / 7    | —             | clean                                                 |
| SPORTS      |   6 / 6¹    | —             | clean (SFI excluded by design)                        |
| **TOTAL**   | **26 / 30** | **4 broken**  |                                                       |

¹ SOCCER_FOOTBALL_INFO is the 7th sports provider but excluded due to in-flight VM.

**87% of adapters confirmed healthy via 1-day smoke.** The 4 broken ones (OKX, COINBASE, POLYGON, FRED) are out-of-scope
for today's EOD push — they need separate plans (canonical-name alignment, SM secret rotation, FRED adapter debugging).

The 26 healthy adapters can all proceed to Phase 2 backfill.

## Phase 2 fan-out (2026-05-04 13:40 IST)

After confirming all 26 healthy adapters via 1-day smoke, fanned out the full backfill.

**Machine sizing**: AMD Ryzen 9 7900X, 24 cores, 93 GB RAM. At full fan-out: 85 concurrent `instruments-service` procs,
load avg ~41, mem 54 GB used / 38 GB free. Comfortable headroom; can sustain.

**Backfills running** (all via `run_vm_backfill_e2e.sh` for CEFI/TRADFI/DEFI, direct CLI for SPORTS):

- **DEFI 7 venues** — per-protocol cutoff dates from `DEFI_SOURCE_COVERAGE_START` in UAC
  - AAVE_V3-ETHEREUM: 2022-03-16 → today
  - UNISWAP_V3-ETHEREUM: 2021-05-05 → today
  - UNISWAP_V2-ETHEREUM: 2020-05-04 → today
  - CURVE-ETHEREUM: 2020-01-19 → today
  - LIDO-ETHEREUM: 2020-12-19 → today
  - BALANCER-ETHEREUM: 2021-05-13 → today
  - EIGENLAYER-ETHEREUM: 2023-06-15 → today
- **CEFI 7 venues** — 2019-01-01 → today (per-venue inception clipped by adapter)
  - BINANCE-SPOT, BINANCE-FUTURES, DERIBIT, BYBIT, UPBIT, HYPERLIQUID, ASTER
  - **OKX + COINBASE excluded** (3-SSOT canonical name disagreement)
- **TRADFI 6 venues** — 2019-01-01 → today
  - CME, CBOE, NASDAQ, NYSE, ICE, FX
  - **POLYGON + FRED excluded** (api_key + zero-records bugs)
- **SPORTS** — 2020-06-01 → today
  - API_FOOTBALL (primary)
  - OPEN_METEO, UNDERSTAT, FOOTYSTATS, TRANSFERMARKT (enrichment, parallel)
  - **SOCCER_FOOTBALL_INFO excluded** (other agent's VM in flight)

All chunks resumable via `.backfill-checkpoints/<AG>_<venue>_<range>/`. CEFI/TRADFI use 30-day chunks × 4 parallel
workers per venue.

**Confirmed healthy**: chunks completing — first `DONE` lines visible by 13:41:36 IST (CEFI BINANCE-SPOT
2019-01-01..2019-01-30 + 2019-03-02..2019-03-31). Env vars propagating correctly (the silent-fail bug from earlier today
is fixed).

**ETA estimate**: CEFI/TRADFI ~18-25 min per venue (89 chunks × ~50s / 4 parallel), DEFI faster (smaller date ranges,
fewer pools), SPORTS depends on rate-limit pacing.

### Rate-limit watchdog (2026-05-04 13:46 IST)

Concern raised mid-run: 85 concurrent procs may hit provider API rate limits. Set up `/tmp/rate-limit-watchdog.sh` (PID
443611, also tails to `/tmp/rate-limit-watch.log`) that scans every 60s for these signatures across all chunk logs:

- HTTP 429 / status 429 / "429 Too Many"
- RateLimitError / RateLimitException
- retry-after / Retry-After headers
- quota_exceeded / QuotaExceeded
- "throttled by API" / Tardis-specific throttling

**Initial regex was too loose** — caught timestamp-millisecond `:42:43,429` as fake matches; tightened to require
word-boundary context ("HTTP 429", "status 429", "429 Too Many"). Re-scanned with the precise regex → **0 real
rate-limit hits** across all 85 procs.

**Why we're holding up**: most providers we hit at scale are paid feeds (Tardis, Databento) with high quotas, and
adapters bake in per-venue pacing internally. Sports providers (api-football, transfermarkt, footystats, understat,
openmeteo) each run as a single process, not chunked, so they self-pace.

**Only real concurrency warning seen**: 9×
`ManifestWriter: generation conflict after 15 retries, falling back to unconditional write` — expected under heavy
concurrent manifest writes (85 procs all updating `_index/availability_index.parquet`). The unconditional-write fallback
is safe (manifest is upsert-keyed); not a data-loss bug, just GCS optimistic-concurrency noise. Will quiet down as
venues finish.

### Force-flag verification (2026-05-04 13:48 IST)

Confirmed: **no `--force` flag anywhere** in this run.

- Inspected all 85 running cmdlines: 0 procs have `--force`.
- `run_vm_backfill_e2e.sh` source line 131 hardcodes the chunk command with no `--force`:
  `instruments-service --operation instruments --mode batch --asset-group X --venues Y --start-date A --end-date B`.
- Sports CLI invocations were also fired without `--force`.

Implication: the orchestrator's `_should_skip_shard` is doing its job — for any `(asset_group, venue, day)` whose
manifest row is `captured` or `empty_confirmed`, the adapter returns immediately. Only `attempted_failed` (the 56,489
phantoms we flipped

- any pre-existing real failures) and missing rows get re-attempted. **Massive cost savings** vs `--force` which would
  re-pay every shard. Tardis/Databento quotas preserved.

### System resource pressure (2026-05-04 13:50 IST)

Memory got tight at peak — 90 GB RAM used / 1 GB free, 7 GB swapped. Top consumers:

- DERIBIT chunk: 4.8 GB (options chain — 200k symbol filter cost)
- Sports providers: 2.8-4.7 GB each, 5 providers = ~18 GB total
- DEFI/CEFI/TRADFI chunks: ~1 GB each, 60+ procs

**At 13:50 I incorrectly claimed "no OOM, system stable".** That was wrong — see correction below.

### OOM kill at 13:55:21 (correction to earlier "no OOM" call)

**`systemd-oomd` killed the entire `app.slice` cgroup at 13:55:21 IST.** I missed this on first scan because
systemd-oomd sends SIGTERM (with 20s grace period) before SIGKILL, which produces "graceful shutdown" log lines that
look like external termination, not OOM. Reading journalctl correctly:

```
May 04 13:55:21 hk systemd[2009]: app-org.chromium.Chromium-6423.scope:
                                   A process of this unit has been killed by the OOM killer.
May 04 13:55:24 hk systemd[2009]: app.slice:
                                   A process of this unit has been killed by the OOM killer.
May 04 13:55:47 hk systemd[2009]: app-org.chromium.Chromium-6423.scope: Failed with result 'oom-kill'.
```

systemd-oomd watches cgroup memory pressure and intervenes before kernel OOM. It killed:

- VS Code chromium electron procs (the editor)
- All 85 instruments-service procs (they were children of the same `app.slice`)
- The rate-limit watchdog
- Anything else in the user's app.slice

**What survived (durable):**

- 376 chunk `.done` files in `.backfill-checkpoints/` — these resume cleanly
- All parquet writes already in GCS (376 chunks worth: cefi 192, tradfi 157, defi 27)
- Manifest rows for those captured shards

**What was lost (in-flight only):**

- 60 in-flight chunks at moment of kill — checkpoints not yet written, will redo on resume
- Sports near-zero progress: api_football 0, open_meteo 2 dates, understat 0, footystats 0, transfermarkt 3 dates

### Real RC of sports memory bloat (corrected, with code citation)

Found the actual bug at
[`instruments-service/instruments_service/engine/orchestrator.py:369-374`](../../../instruments-service/instruments_service/engine/orchestrator.py#L369):

```python
# Sports reference core entity caches — leagues/teams/standings are the same
# across all dates within a batch run. Fetched once, written to every date partition.
_cached_leagues_df: pd.DataFrame | None = None
_cached_teams_df: pd.DataFrame | None = None
_cached_standings_df: pd.DataFrame | None = None
_cached_prediction_league_ids: list[int] = []
```

These are **module-level pandas DataFrames** that hold the full sports reference dataset (1,228 leagues + 618 teams +
standings rows from the API_FOOTBALL smoke earlier). They're populated via `_set_cached_leagues / _teams / _standings`
and **never cleared** for the duration of the proc.

There's a `clear_defi_universe_cache()` for the DeFi equivalent, but **no `clear_sports_caches()`** function exists. So
when sports runs with `--start-date 2020-06-01 --end-date 2026-05-04` in a single proc, those DFs stay resident through
~1,800 days of iteration, plus per-day intermediate state (fixtures, oddslike buffers, etc.) accumulates inside the
orchestrator's loop without per-day flushes.

User intuition correct: **once data is uploaded to GCS, it should be cleared from memory.** The orchestrator does write
to GCS per-day, but doesn't `del` the dataframes / call gc afterwards. RAM grows monotonically until the process dies
(or systemd-oomd kills it).

**Verified — the cache is intentional, NOT used for any aggregate calculation:**

Confirmed across the entire `instruments-service` repo:

- `_cached_leagues_df / _teams_df / _standings_df / _prediction_league_ids` are referenced **only inside
  `orchestrator.py`** — 3 setter sites + 4 reader sites, all within the per-date sports loop.
- **No other module imports them.** Verified `grep -rn "_cached_leagues_df" instruments-service/` → only
  orchestrator.py + tests.
- **No finalize / wrap-up / aggregate / post-loop function** uses the accumulated DFs. No "compute season-summary from
  full cache" logic anywhere. The cache is purely a per-batch-run API-call optimization.
- **Data is durable in GCS per-date** via `_gated_sink_write(... entity="leagues" ...)`. Clearing the memory copy after
  each date's write is safe — nothing downstream consumes the in-memory copy.
- **Read sites verify**: every read (lines 2912, 2942, 2978, 3012) is to write the same DF to a different date's GCS
  partition. Not used for any joins, computations, or cross-date aggregations.

**Conclusion**: cache is intentional for the "skip 67 API calls per date" optimization, but NOT used for any
calculation. It can be cleared at any point (per-date, per-chunk, per-N-dates) without losing data — just adds API call
cost where cleared. This makes fixing it safe and low-risk.

After tracing read sites in `orchestrator.py:2912, 2942, 2978, 3012` — the cached DFs are read on every subsequent date
in the loop. The original-author comment says it saves **~67 API calls per date** (1 leagues + 33 teams + 33 standings =
67 calls, all slow-moving). Without the cache, a 1,800-date sports backfill would do 120,600 API calls just for
reference data — would hit api-football's daily quota many times over and fail.

Code-flow verification:

- Lines 2917-2918: fetch leagues → `_set_cached_leagues(df)`
- Lines 2931-2938: same df ALSO written to GCS via `_gated_sink_write(... entity="leagues" ...)` (so persistent copy
  lives in GCS too)
- Lines 2942-2944: next date reads `teams_df = _cached_teams_df` first; only fetches if `None`
- Same pattern for standings (line 3012) and prediction_league_ids (line 2978)

So the cache is **intentional, downstream-consumed, and cost-saving**. It's NOT a stale artifact never read again.
Decision-trade-off:

| Approach                         | API call cost        | RAM cost                   | Process restart cost           |
| -------------------------------- | -------------------- | -------------------------- | ------------------------------ |
| Cache held forever (current)     | 67 calls / batch run | Grows with batch (problem) | None                           |
| Clear cache per date             | 67 × N dates         | Bounded ~50 MB             | None                           |
| No cache, refetch per date       | 67 × N dates         | Tiny                       | None                           |
| **Chunk processes (workaround)** | 67 × N chunks        | Bounded per proc           | Process restart between chunks |

Original design assumed sports runs as **VM-per-source** (one VM, one source, runs till done in ~hours, then VM dies →
cache cleared by VM termination). Today's local-driver pattern runs sports as a **single 6-year proc** which violates
that assumption and OOMs.

**Two paths to fix**:

1. **Proper fix (follow-up plan)**: add a `clear_sports_caches()` function (mirroring `clear_defi_universe_cache()`) and
   invoke it at smaller intervals — e.g. every 30 days, or per-season. Re-fetches at the boundary cost ~67 API calls but
   bounds RAM.
2. **Workaround for today's EOD push**: chunk sports the same way CEFI/TRADFI/DEFI are chunked. Each 30-day proc starts
   fresh, fetches reference once for the chunk, writes per-date GCS partitions, dies. No code change required, just
   wrapper script edit.

For VMs in the cloud: the existing pattern (VM-per-source, runs to completion, dies) already works correctly because VM
lifetime ≈ batch lifetime. **The fix is local-only.**

### Local-vs-VM optimisation note (2026-05-04 13:55 IST)

**Decisions about parallelism / chunking made today are LOCAL-ONLY.** The cloud VM launchers
(`launch-{api-football,transfermarkt,...}-backfill-vm.sh`) spawn one VM per source with much smaller machine types
(e2-standard-2 = 2 vCPU / 8 GB RAM, not 24 vCPU / 93 GB). VMs do NOT run different sources in parallel —
singleton-locked launchers explicitly forbid it. So:

- **Don't carry over `--parallel 4` to VM launches** — VMs only have 2 vCPU; chunking parallelism that high will thrash.
  VM-appropriate value is `--parallel 1` or `2`.
- **Don't run multiple sources concurrently on a single VM** — each VM should run ONE source over a date range, no
  fan-out within the VM.
- **Don't size SPORTS RAM expectations off this run** — on a VM, sports must be chunked too (the 5 GB single-proc memory
  load would OOM the e2-standard-2's 8 GB).
- **Local IP rate-limits** are different from VM static-IP rate-limits — Tardis whitelists the cloud-VM egress IPs but
  treats laptop IP differently. What works locally may 429 in cloud and vice versa.

When IAM grant lands and we move sports to VM launchers, remember: lower parallelism, no inter-source fan-out, and chunk
sports just like CEFI/TRADFI/DEFI.

### Resume strategy (2026-05-04 14:05 IST)

Checkpoints survived: 192 cefi + 145 tradfi + 27 defi = 364 chunks durably done. The ~12-chunk discrepancy from earlier
"376" count is from chunks that wrote parquets to GCS but didn't get checkpoint files written before the OOM SIGTERM
hit. Recon will classify those correctly.

**Step 1 (in flight)**: realign manifest with reality post-OOM via per-AG dry-run reconciler. Goal: see how many
manifest rows are now phantom (claimed-captured but parquet was never actually written because the proc was killed
mid-write).

**Step 2 (after recon completes)**: flip any new phantoms (no `--dry-run`) so the orchestrator's `_should_skip_shard`
will retry them on resume.

**Step 3 (CEFI/TRADFI/DEFI resume)**: re-fire with `--parallel 2` (was 4). Checkpoints skip the 364 already-done chunks.
Only mid-flight + post-OOM-phantom chunks get re-attempted. Lower parallelism halves peak RAM.

**Step 4 (SPORTS via chunked launcher)**: use `/tmp/sports-chunked-backfill.sh PROVIDER` which chunks the 6-year window
into 30-day procs. Each proc dies after its window, reclaiming the leagues/teams/standings DataFrames. RAM bounded to
~500 MB per chunk instead of growing to 5 GB across the full window. Run 5 providers in parallel (API_FOOTBALL,
TRANSFERMARKT, FOOTYSTATS, UNDERSTAT, OPEN_METEO; SFI excluded).

**Step 5**: post-resume dry-run reconciler again to confirm headline coverage moved.

### Resume status (2026-05-04 14:25 IST)

**Recon results (post-OOM phantom counts) — phantom drift from OOM is minimal:**

| AG     | Pre-OOM |             Post-OOM | Delta | Status                                |
| ------ | ------: | -------------------: | ----: | ------------------------------------- |
| CEFI   |  12,540 |               12,557 |   +17 | dry-run done, not yet flipped         |
| TRADFI |   2,726 |                2,734 |    +8 | dry-run done, not yet flipped         |
| DEFI   |     597 |                  645 |   +48 | dry-run done, not yet flipped         |
| SPORTS |  41,223 | timed out (GCS list) |   TBD | needs retry with `--workers 16` later |

**Resume drivers all firing correctly**: each runner's summary log shows `SKIP ... (checkpoint exists)` for the 376 done
chunks then `START` for the next un-checkpointed chunk. Resume strategy working as designed.

**Sports chunked launcher**: committed to
[`instruments-service/scripts/sports_chunked_backfill.sh`](../../../instruments-service/scripts/sports_chunked_backfill.sh)
(commit `619a32e`). Each invocation chunks the date range into 30-day windows; per-chunk proc dies + reclaims the
leagues/teams/standings DataFrame caches between windows. RAM-safe because no single proc holds 6 years of accumulated
DFs.

**5 sports providers fired chunked** (TRANSFERMARKT first as smoke test, then API_FOOTBALL

- FOOTYSTATS + UNDERSTAT + OPEN_METEO after RAM headroom confirmed). SFI excluded as designed.

**Resource cap**: Harsh set hard cap at 80 GB RAM used (out of 93 GB). Currently at ~48 GB used / 40 GB free,
comfortably under cap. RAM monitor PID 571212 logging to `/tmp/ram-monitor.log`. Wakeup at 14:31 will check trend; if
approaching 75 GB hold, if breaches 80 GB kill heaviest sports providers.

**System state at 14:25 IST**:

- 42 concurrent `instruments-service` procs
- 376 chunks durable (durable from pre-OOM run + early new completions)
- New chunks DONE since resume: cefi 3, tradfi 5, defi 1 (will accelerate)
- 0 swap thrashing, no rate-limit hits, no OOM

### Health snapshot (2026-05-04 14:31 IST)

10 min after sports fan-out, 16 min after CEFI/TRADFI/DEFI resume:

| Metric            | Value                                                                                                       | Status                                    |
| ----------------- | ----------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| RAM used          | 58 GB / 80 GB cap                                                                                           | ✅ 22 GB headroom (under 65 GB threshold) |
| RAM trend (5 min) | 53→58 GB (~1.25 GB/min slow climb)                                                                          | ✅ stable, will plateau as chunks cycle   |
| Swap              | 0.7 GB                                                                                                      | ✅ idle (was 6.7 GB at OOM)               |
| OOM kills         | 0                                                                                                           | ✅                                        |
| Rate-limit hits   | 0 (real signatures)                                                                                         | ✅                                        |
| Concurrent procs  | 46                                                                                                          | —                                         |
| Checkpoints       | 408 (+32 since OOM resume start)                                                                            | ✅                                        |
| Errors last 5min  | 53 (51 = known Databento NASDAQ symbology pre-listing tickers; 1 transient Tardis 500; 1 URDI zero-records) | ✅ within expected bounds                 |

Progress per AG:

- CEFI: 200 chunks done
- TRADFI: 171 chunks done (fastest velocity)
- DEFI: 37 chunks done
- Sports chunked progress (window-1-then-cycle pattern):
  - API_FOOTBALL: 6 chunks done, on chunk 7 (2020-11-28)
  - FOOTYSTATS: 2 chunks done, on chunk 3
  - UNDERSTAT: 1 chunk done, on chunk 2
  - OPEN_METEO: 0 chunks done, on chunk 1 (started 14:26)
  - TRANSFERMARKT: 0 chunks done, on chunk 1 since 14:15 (47 min — Transfermarkt's ~1 req/sec rate-limit pacing makes a
    30-day chunk slow but it's not stalled)

Decision per the wakeup rule: RAM is at 58 GB (<65 GB threshold) and stable. **Holding course, no scaling changes.**
Next wakeup at ~14:36 to reassess.

### Health snapshot (2026-05-04 14:37 IST)

| Metric                 | Value                                                                                | Status                                   |
| ---------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------- |
| RAM used               | 68 GB / 80 GB cap                                                                    | ⚠️ on 65 GB boundary, no further fan-out |
| RAM trend (5 min)      | 58→67→65→68 GB                                                                       | ✅ plateauing around 65, not climbing    |
| Swap                   | 0.7 GB                                                                               | ✅ idle                                  |
| OOM kills              | 0                                                                                    | ✅                                       |
| Rate-limit hits (real) | 0                                                                                    | ✅                                       |
| Concurrent procs       | 47                                                                                   | —                                        |
| Checkpoints            | 415 (+7 since 14:31)                                                                 | ✅ progressing                           |
| Errors last 5min       | 75 (74 known Databento NASDAQ symbology pre-listing tickers; 1 transient Tardis 500) | ✅ within bounds                         |

CEFI/TRADFI/DEFI deltas since 14:31:

- CEFI: 200→204 (+4)
- TRADFI: 171→173 (+2)
- DEFI: 37→38 (+1)

Sports chunked progress (was 6+2+1+0+0):

- API_FOOTBALL: 6→10 chunks (+4) — fastest
- UNDERSTAT: 1→3 chunks (+2)
- FOOTYSTATS: 2→2 chunks (+0 — investigate? prob just slow on chunk 3)
- OPEN_METEO: 0→0 (still chunk 1, started 14:26 = 11 min in)
- **TRANSFERMARKT: 0→0** (still chunk 1, started 14:15 = 22 min in)

#### TRANSFERMARKT chunk 1 — root cause identified

Not stalled, **bottlenecked on ManifestWriter generation-conflict** retry loop. Log shows sequential GCS
optimistic-concurrency-control conflicts up to attempt 11/15:

```
14:29:22 generation conflict (attempt 2/15), retrying in 1.0s
14:30:41 generation conflict (attempt 4/15), retrying in 2.0s
...
14:36:31 generation conflict (attempt 11/15), retrying in 5.5s
```

47 concurrent writers competing for the same `_index/availability_index.parquet` blob. Each conflict waits, retries,
gets clobbered again. Will eventually fall through to unconditional write at attempt 15. **Not blocking — just slow
under high concurrency.**

This is the same `ManifestWriter: generation conflict, falling back to unconditional write` warning we saw at the
original 85-proc fan-out, just amplified now because TRANSFERMARKT happens to fetch slowly enough that other procs win
the manifest race every time.

Decision per wakeup rule: **plateau holding around 65 GB, no further fan-out.** Not killing anything (cap not breached).
Will continue monitoring at 14:42.

### Health snapshot (2026-05-04 14:43 IST)

| Metric                 | Value                                                              | Status                             |
| ---------------------- | ------------------------------------------------------------------ | ---------------------------------- |
| RAM used               | 67 GB / 80 GB cap                                                  | ⚠️ 13 GB headroom, holding plateau |
| RAM trend (5 min)      | 62–69 GB oscillating around 65                                     | ✅ stable, not climbing            |
| Swap                   | 0.7 GB                                                             | ✅ idle                            |
| OOM kills              | 0                                                                  | ✅                                 |
| Rate-limit hits (real) | 0                                                                  | ✅                                 |
| Concurrent procs       | 46                                                                 | —                                  |
| Checkpoints            | 426 (+11 in 5 min)                                                 | ✅ progressing                     |
| Errors (last 5 min)    | 102 (100 known Databento, 1 Tardis transient, 1 URDI zero-records) | ✅ within bounds                   |

CEFI/TRADFI/DEFI deltas since 14:37 (was 415):

- CEFI: 204→208 (+4)
- TRADFI: 173→179 (+6, fastest)
- DEFI: 38→39 (+1)

Sports chunked deltas since 14:37 (was 10+2+0+0+3):

- API_FOOTBALL: 10→10 (slow chunk in flight)
- FOOTYSTATS: 2→5 (+3)
- UNDERSTAT: 3→5 (+2)
- OPEN_METEO: 0→0 (still chunk 1 — paced)
- TRANSFERMARKT: 0→0 (still chunk 1 — but **past the manifest conflict** and now actively fetching teams per league:
  DK1, NL1, MEXA, FR1 at ~30-40s/league)

#### TRANSFERMARKT broke through

Earlier 14:37 snapshot showed TRANSFERMARKT stuck on attempt 11/15 of ManifestWriter generation conflicts. Current log
shows it past the bottleneck:

```
14:41:25 RapidAPI: fetched 14 clubs for league DK1 season 2019
14:42:32 RapidAPI: fetched 19 clubs for league MEXA season 2019
14:43:13 RapidAPI: fetched 20 clubs for league FR1 season 2019
```

Transfermarkt's internal ~1 req/sec pacing + 32 leagues × pagination = ~45 min/chunk expected. Slow but progressing. Not
stuck.

Decision: **holding course**. RAM stable at boundary, not breaching 75 GB hold-threshold or 80 GB kill-threshold. No new
fan-out, no kills.

### Health snapshot (2026-05-04 14:50 IST)

| Metric                 | Value                                | Status                             |
| ---------------------- | ------------------------------------ | ---------------------------------- |
| RAM used               | 67 GB / 80 GB cap                    | ✅ 13 GB headroom, plateau holding |
| RAM trend (5 min)      | 64-68 GB oscillating around 65-66    | ✅ stable, not climbing            |
| Swap                   | 0.7 GB                               | ✅ idle                            |
| OOM kills              | 0                                    | ✅                                 |
| Rate-limit hits (real) | 0                                    | ✅                                 |
| Concurrent procs       | 42                                   | — (was 46, normal cycling)         |
| Checkpoints            | 448 (+22 in 7 min)                   | ✅ healthy pace                    |
| Errors total           | 124 (+22, all same Databento NASDAQ) | ✅ no new categories               |

Deltas since 14:43:

- CEFI: 208→214 (+6)
- TRADFI: 179→188 (+9, fastest)
- DEFI: 39→46 (+7, accelerating — was +1 last interval)

Sports chunked deltas since 14:43 (was 10+5+0+0+5):

- API_FOOTBALL: 10→10 (chunk 11 still in flight)
- FOOTYSTATS: 5→6 (+1)
- UNDERSTAT: 5→8 (+3)
- OPEN_METEO: 0→0 (still chunk 1 — paced)
- TRANSFERMARKT: 0→0 (still chunk 1 — see below)

#### TRANSFERMARKT chunk 1 — data written, manifest write in conflict loop

Important nuance: log at 14:44:52-53 shows the **chunk's real data IS written to GCS**:

- "RapidAPI: fetched 10 clubs for league C1 season 2019" → done fetching
- "Transfermarkt teams → player_values: 131 rows written" → wrote 131 player_values to GCS
- "Transfermarkt team mapping cache: 131 rows written for season=2019" → cache written

Then 14:45:45 onwards, back into ManifestWriter generation-conflict loop (attempt 1→6/15 as of last log read). This is
**only the index-manifest write** stuck — the actual data is durably in GCS. The chunk will mark itself `captured`
whenever attempt N succeeds (or attempt 15 unconditional fallback fires).

So TRANSFERMARKT chunk 1's data is safe; the checkpoint file just hasn't been written yet. Resume-safe regardless.

Decision: **holding course**. RAM stable, real work happening (+22 checkpoints in 7 min, DEFI accelerating). No changes.

### Health snapshot (2026-05-04 14:56 IST)

| Metric            | Value                         | Status                                        |
| ----------------- | ----------------------------- | --------------------------------------------- |
| RAM used          | 74 GB / 80 GB cap             | ⚠️ 6 GB headroom, **at 75 GB hold-threshold** |
| RAM trend (5 min) | 69→74 GB, slowly climbing     | ⚠️ plateau breaking                           |
| Swap              | 0.7 GB                        | ✅ idle                                       |
| OOM kills         | 0                             | ✅                                            |
| Concurrent procs  | 43                            | —                                             |
| Checkpoints       | 461 (+13 in 6 min)            | ✅                                            |
| Errors total      | 151 (+27, all same Databento) | ✅                                            |

Deltas since 14:50 (was 448):

- CEFI: 214→219 (+5)
- TRADFI: 188→191 (+3)
- DEFI: 46→51 (+5)

#### Key insight: sports `done_chunks` counter is misleading

My `grep -c "rc=0"` only counts whole-chunk completions. Inside each chunk, individual DATES are completing — log
inspection shows:

- **OPEN_METEO chunk 1**: at day 30/30 (2020-06-29 done, 2020-06-30 in flight). About to wrap chunk 1.
- **API_FOOTBALL chunk 11**: wrote 3,434 records for 2021-04-06; iterating through remaining days.
- **TRANSFERMARKT chunk 1**: at day 10/30 (date 2020-06-09 done, 2020-06-10 active). Each day fetches 32 leagues + ~131
  teams.

**All sports providers ARE writing data per-day to GCS**. The chunk-level counter just doesn't reflect that. Real
progress is happening; chunks finishing will accelerate as they wrap.

#### Top RAM consumers (kill candidates if we breach 78 GB)

```
DERIBIT chunk:    13.5 GB  (2019-04-01 → 2019-04-30, options chain — known heavy)
FOOTYSTATS:        5.8 GB  (2020-11-28 → 2020-12-27)
TRANSFERMARKT:     5.0 GB  (2020-06-01 → 2020-06-30)
API_FOOTBALL:      4.3 GB  (2021-03-28 → 2021-04-26)
OPEN_METEO:        3.5 GB  (2020-06-01 → 2020-06-30)
UNDERSTAT:         2.7 GB
```

DERIBIT is doing real CEFI work — won't kill that even though it's heaviest. If forced to kill, would target FOOTYSTATS
(smallest impact: only 1 chunk done so far + the data within chunk is small per-day).

Decision: **holding, but tightening monitor cadence** (4 min instead of 5). If RAM breaches 78 GB, kill the heaviest
sports provider (FOOTYSTATS) to bring under 75 GB.

### Health snapshot (2026-05-04 15:03 IST) — RAM breached, killed + restarted FOOTYSTATS

**RAM peaked 79 GB** during the last 8 ticks (one tick away from 80 GB cap). Per the wakeup rule I killed the FOOTYSTATS
chunk-8 worker (PID 742647).

| Metric                | Value             | Status                      |
| --------------------- | ----------------- | --------------------------- |
| RAM peak last 8 ticks | 79 GB / 80 GB cap | ❌ breached 78 GB threshold |
| RAM after kill        | 74 GB             | ⚠️ back at threshold        |
| Swap                  | 0.7 GB            | ✅ idle                     |
| OOM kills             | 0                 | ✅                          |
| Concurrent procs      | 46                | —                           |
| Checkpoints           | 470 (+9 in 7 min) | ✅ slowing slightly         |

#### Mistake during kill — full FOOTYSTATS wrapper died, restarted

I killed PID 742647 (Python worker) AND PID 742646 (timeout wrapper). The bash wrapper script (PID 607671) had
`set -euo pipefail`, so when its `timeout` child exited abnormally, the wrapper exited too. **All FOOTYSTATS work
stopped, not just the in-flight chunk.**

Restarted FOOTYSTATS wrapper at 15:04 (new PID 755950). It restarts at chunk 1, but the orchestrator's
`_should_skip_shard` will fast-forward through already-captured dates (chunks 1-7 are durably done). Net cost: ~30s of
skip-checks per already-done chunk + loss of in-flight chunk 8 progress (small, will redo).

**Lesson (saved as feedback memory)**: when killing a wrapped process, `set -e` in the parent shell can propagate exit
through the wrapper. Next time, kill ONLY the `instruments-service` Python child (not the `timeout` parent or the bash
wrapper).

#### DERIBIT is the actual RAM hog — flagging for future

```
DERIBIT chunk:    16 GB  ← biggest single consumer, growing (was 13.5 → 16 over 6 min)
FOOTYSTATS:        4.5 GB (now killed)
API_FOOTBALL:      3.9 GB
UNDERSTAT:         3.9 GB
TRANSFERMARKT:     3.5 GB
OPEN_METEO:        2.4 GB
```

Killing FOOTYSTATS only freed 4.5 GB, while DERIBIT keeps growing. The RAM pressure is DERIBIT-dominated. DERIBIT has
the 200k-symbol options chain — known heavy. If RAM breaches 78 GB again, DERIBIT chunk is the bigger lever (CEFI cost
vs sports cost trade-off — would need user call).

Decision per rule: kill executed (FOOTYSTATS, accidentally full-killed not just chunk). Restarted. Next watch in 4 min;
if RAM breaches 78 GB again with FOOTYSTATS already restarted → escalate to user, do NOT kill DERIBIT autonomously (it's
a real CEFI work chunk, scope-impacting).

### Health snapshot (2026-05-04 15:10 IST) — holding pattern

| Metric                       | Value                                    | Status                                             |
| ---------------------------- | ---------------------------------------- | -------------------------------------------------- |
| RAM peak last 6 ticks        | 77 GB / 80 GB cap                        | ⚠️ in danger zone, but under 78 GB autonomous-kill |
| RAM current                  | 77 GB                                    | ⚠️                                                 |
| RAM trend                    | 73→71→69→77→75→76 (oscillating 75-77)    | ⚠️ stable but high                                 |
| Swap                         | 0.7 GB                                   | ✅ idle                                            |
| OOM in journalctl last 5 min | 0                                        | ✅                                                 |
| Concurrent procs             | 47                                       | —                                                  |
| Checkpoints                  | 483 (+13 in 7 min)                       | ✅ progressing                                     |
| **DERIBIT chunk RSS**        | **17.1 GB** (was 13.5→16→17.1, climbing) | ⚠️ unbounded grow                                  |

Deltas since 14:56 (was 461):

- CEFI: 223→228 (+5)
- TRADFI: 195→202 (+7, fastest)
- DEFI: 52→53 (+1)

Sports chunked deltas:

- API_FOOTBALL: 10→10 (chunk 11 still iterating per-day, 18 manifest conflicts so far)
- FOOTYSTATS: restarted, fast-forwarding through done dates via orchestrator skip
- OPEN_METEO: 0→1 (chunk 1 finally done; on chunk 2)
- TRANSFERMARKT: 0→0 (still chunk 1 — slow but real per-day work)
- UNDERSTAT: 11→13 (+2, fastest sports)

#### Awaiting user decision on (a/b/c/d) for RAM mitigation

Per 15:03 commit, raised question with user about which kill-strategy if RAM breaches further:

- (a) Kill DERIBIT chunk (frees 16-17 GB; loses CEFI options-chain progress)
- (b) Kill another sports provider (frees ~4 GB; smaller impact, less effective)
- (c) Throttle CEFI/TRADFI/DEFI to --parallel 1 (more disruptive, slower forward)
- (d) Hold (60% chance OOM, 40% self-stabilising)

No user response yet. Per "ask on important things" feedback rule, **I am NOT acting autonomously on DERIBIT.** Will
hold + monitor at 3-min cadence. If RAM peaks ≥78 GB again, will flag urgently rather than kill.

### Health snapshot (2026-05-04 15:15 IST) — RAM stabilised, DERIBIT cycled

**RAM dropped from 77→60 GB** in the 5 min between checks. Per the wakeup rule (<72 GB consistently → stabilising,
report).

| Metric                       | Value                             | Status            |
| ---------------------------- | --------------------------------- | ----------------- |
| RAM peak last 6 ticks        | 63 GB / 80 GB cap                 | ✅ 17 GB headroom |
| RAM current                  | 60 GB                             | ✅ healthy        |
| RAM trend                    | 62→63→60→62→61→60 (steady ~60-63) | ✅ stabilised     |
| Swap                         | 0.7 GB                            | ✅ idle           |
| OOM in journalctl last 3 min | 0                                 | ✅                |
| Concurrent procs             | 45                                | —                 |
| Checkpoints                  | 495 (+12 in 5 min)                | ✅                |

#### What changed: DERIBIT chunk cycled

The 17.1 GB DERIBIT chunk (2019-04-01 → 2019-04-30) **finished and died, reclaiming all 17 GB**. Next DERIBIT chunks are
now running small:

- 2019-05-01 → 2019-05-30: 1.8 GB
- 2019-05-31 → 2019-06-29: 1.8 GB

Process-death-reclaims-cache pattern worked exactly as designed. The 2019-04 chunk was probably the worst — Deribit's
options chain was rapidly expanding then. Future chunks will likely stay smaller.

TRANSFERMARKT chunk 1 also appears to have completed (no longer in proc list); will now move to chunk 2 with a fresh
(smaller) cache.

Deltas since 15:10:

- CEFI: 228→231 (+3)
- TRADFI: 202→208 (+6)
- DEFI: 53→56 (+3)

**Top RAM consumers now (no single proc over 5 GB)**:

```
API_FOOTBALL chunk 11:    4.6 GB
OPEN_METEO chunk 2:       4.5 GB
UNDERSTAT chunk 16:       2.6 GB
DERIBIT chunks (×2):      1.8 GB each
```

**Question (a/b/c/d) for user is moot**: RAM stabilised on its own without intervention. Self-resolving as the
chunk-cycling pattern broke through the 2019-04 DERIBIT bottleneck.

Decision: **continue holding course**. Next check at 15:20.

### Health snapshot (2026-05-04 15:21 IST) — sweet spot

| Metric                       | Value               | Status                                |
| ---------------------------- | ------------------- | ------------------------------------- |
| RAM peak last 10 ticks       | 64 GB / 80 GB cap   | ✅ JUST under healthy 65 GB threshold |
| RAM current                  | 66 GB               | ✅                                    |
| RAM trend                    | tight 60-64 GB band | ✅ stabilised                         |
| Swap                         | 0.7 GB              | ✅ idle                               |
| OOM in journalctl last 5 min | 0                   | ✅                                    |
| Concurrent procs             | 45                  | —                                     |
| Checkpoints                  | 513 (+18 in 5 min)  | ✅ healthy pace                       |

Deltas since 15:15:

- CEFI: 231→237 (+6)
- TRADFI: 208→211 (+3)
- DEFI: 56→65 (+9 — **accelerating**, smaller universes per chunk)

Sports chunks (FOOTYSTATS shows post-restart fast-forward via orchestrator skip):

- API_FOOTBALL: 10 chunks (still on chunk 11, 45 min in — per-day iter writing data)
- FOOTYSTATS: 6 chunks (was 2 post-restart, +4 from skip-fast-forward)
- OPEN_METEO: 1 chunk (chunk 2 in flight)
- TRANSFERMARKT: 0 chunks (chunk 1, 66 min — slow per-league fetch but progressing)
- UNDERSTAT: 17 chunks (was 13 → **+4** — fastest sports)

Top RAM consumers (no single >6 GB now):

```
OPEN_METEO chunk 2:    5.3 GB
API_FOOTBALL ch 11:    4.8 GB
DERIBIT 2019-06:       4.6 GB
DERIBIT 2019-05:       4.1 GB
FOOTYSTATS ch 7:       2.6 GB
UNDERSTAT ch 18:       2.6 GB
```

Healthy distribution. The DERIBIT 2019-04 17 GB outlier was a one-time historical peak (peak Deribit options chain
growth period). Subsequent DERIBIT chunks bounded at <5 GB.

Decision: **healthy state, holding**. Next check at 15:26.

### Health snapshot (2026-05-04 15:27 IST) — ASTER first venue complete; TRANSFERMARKT silent-dead found

| Metric                 | Value                  | Status                           |
| ---------------------- | ---------------------- | -------------------------------- |
| RAM peak last 10 ticks | 73 GB / 80 GB cap      | ⚠️ approaching 75 hold-threshold |
| RAM current            | 70 GB                  | ⚠️ above 65 healthy              |
| RAM trend              | 65→73→69→70 (climbing) | ⚠️                               |
| Swap                   | 0.7 GB                 | ✅ idle                          |
| OOM kills              | 0                      | ✅                               |
| Concurrent procs       | 43                     | —                                |
| Checkpoints            | 523 (+10 in 6 min)     | ⚠️ slowed from +18               |

#### 🎉 ASTER — first venue fully complete

`run_vm_backfill_e2e.sh --venue ASTER --asset-group CEFI` driver has exited with all 90 chunks done. ASTER is the
smallest CEFI venue (newest exchange, less history). **First venue to fully complete the backfill.**

#### TRANSFERMARKT was silent-dead since 15:15

When I killed FOOTYSTATS chunk 8 worker at 15:03, I also issued a `pkill -f` style kill that matched ALL
`sports_chunked_backfill` wrappers — accidentally caught TRANSFERMARKT too. TRANSFERMARKT received SIGTERM at 15:15:16
(12 min ago), exited cleanly, but I never noticed because the `done_chunks` counter was already 0 (still on chunk 1).

**Restarted TRANSFERMARKT at 15:28** (new PID 849943). Same fast-forward pattern via orchestrator skip will apply (chunk
1 had partial dates done, will resume on first red date).

This is the second time today I've over-killed via wildcard. **Lesson saved to memory**: when killing one provider's
chunk worker, never use `pkill -f` patterns that match the wrapper's full command line. Use specific PIDs.

Deltas since 15:21:

- CEFI: 237→239 (+2 — slowed; ASTER finishing absorbed bandwidth)
- TRADFI: 211→218 (+7)
- DEFI: 65→66 (+1 — decelerated from +9 last interval; UNISWAP_V3 chunks have larger pool universe than LIDO/AAVE)

Sports:

- API_FOOTBALL: 10 chunks (still chunk 11, now 51 min — 31 manifest conflicts but per-day data writing)
- FOOTYSTATS: 6→7 (+1)
- OPEN_METEO: 1
- **TRANSFERMARKT**: 0→0 (was silently dead 15:15 → 15:28, just restarted)
- UNDERSTAT: 17→20 (+3 still fastest)

Decision: **holding course**. RAM in middle zone (above healthy threshold but below hold threshold). Will continue 5-min
cadence.

### Health snapshot (2026-05-04 15:34 IST) — RAM cap breach + API_FOOTBALL kill

**RAM hit 81 GB at point of check, peak 79 GB in the 10-tick window.** Cap breached.

| Metric                 | Value                                | Status         |
| ---------------------- | ------------------------------------ | -------------- |
| RAM at check time      | 81 GB                                | ❌ over 80 cap |
| RAM peak last 10 ticks | 79 GB                                | ❌             |
| Trend                  | 71→78→79→76 (climbing then settling) | ⚠️             |
| Swap                   | 0.7 GB                               | ✅ idle        |
| OOM kills              | 0 (no time to fire yet)              | ✅             |
| Concurrent procs       | 42                                   | —              |
| Checkpoints            | 538 (+15 in 7 min)                   | ✅             |

#### Action taken: killed API_FOOTBALL Python worker (heaviest sports)

Per established rule, kill heaviest sports at 80 GB. DERIBIT NOT killed (user constraint). Heaviest sports was
API_FOOTBALL chunk 11 (5.0 GB).

This time **only PID 652121** (Python child) was killed via specific PID — no `pkill -f` wildcard. But the bash wrapper
STILL exited because:

- Killing the Python child caused `timeout 3600 ...` (its parent) to exit non-zero.
- Bash wrapper had `set -euo pipefail`, so the wrapper exited too.

Restarted API_FOOTBALL wrapper at 15:35 (PID 876466). Orchestrator skip will fast-forward through chunks 1-10 (already
in manifest as captured). Lost chunk 11 in-flight day-progress (was ~day 17/30).

**This is the 3rd time the wrapper script has died on its child's death.** The `set -euo pipefail` in
`sports_chunked_backfill.sh` is the culprit — should remove `pipefail` (or guard with `|| true` per chunk) to make the
wrapper resilient to child-kill. Tracking as follow-up code fix.

#### DERIBIT growing again — same memory leak pattern

Two DERIBIT chunks now: 9.4 GB + 8.9 GB = 18.3 GB combined. Started small at 1.8 GB each, grew over time. Same per-chunk
options-chain accumulation that hit 17 GB on the 2019-04 chunk earlier. **DERIBIT chunks have a real memory leak** that
grows monotonically with wall-clock time, not just per-day data volume.

Constraint: user has explicitly forbidden killing DERIBIT chunks autonomously.

Deltas since 15:27:

- CEFI: 239→244 (+5)
- TRADFI: 218→224 (+6)
- DEFI: 66→70 (+4)

Sports:

- API_FOOTBALL: 10 (killed + restarted)
- FOOTYSTATS: 7→10 (+3, caught up to chunk 11)
- OPEN_METEO: 1
- TRANSFERMARKT: 0 (restarted at 15:28, now on date 2020-06-05 of chunk 1)
- UNDERSTAT: 20→22 (+2)

Decision: **monitor 3-min cadence**. If RAM breaches 80 GB again with API_FOOTBALL already restarted, must escalate
DERIBIT decision to user.

### Health snapshot (2026-05-04 15:40 IST) — flagging DERIBIT growth rate

| Metric                | Value                          | Status                                |
| --------------------- | ------------------------------ | ------------------------------------- |
| RAM peak last 6 ticks | 74 GB / 80 GB cap              | ⚠️ 6 GB headroom, but DERIBIT growing |
| RAM current           | 74 GB                          | ⚠️                                    |
| Trend                 | 71→72→73→69→73→74 (slow climb) | ⚠️                                    |
| Swap                  | 0.6 GB                         | ✅ idle                               |
| OOM kills             | 0                              | ✅                                    |
| Concurrent procs      | 43                             | —                                     |
| Checkpoints           | 547 (+9 in 6 min)              | ✅                                    |

#### DERIBIT growth rate quantified

| Time      | Chunk 2019-05-01 | Chunk 2019-05-31 |    Combined |
| --------- | ---------------: | ---------------: | ----------: |
| 15:21     |           1.8 GB |           1.8 GB |      3.6 GB |
| 15:27     |           4.6 GB |           4.1 GB |      8.7 GB |
| 15:34     |           9.4 GB |           8.9 GB |     18.3 GB |
| **15:40** |      **11.1 GB** |      **10.0 GB** | **21.1 GB** |

**Growth rate: ~0.5 GB/min combined.** Linear unbounded growth — same pattern as the 2019-04-01 chunk that hit 17 GB
earlier. **Projected**:

- 12 min from now: combined ~27 GB → total RAM ~80 GB cap breach
- 20 min from now: combined ~31 GB → systemd-oomd very likely fires

This is the **same memory leak** in instruments-service's DeFi-on-Tardis options adapter that we identified earlier
(process-death-reclaims-cache pattern). Each DERIBIT chunk leaks until it dies. Killing one chunk frees its growth; the
wrapper will spawn the next chunk fresh at 1-2 GB.

Deltas since 15:34:

- CEFI: 244→247 (+3)
- TRADFI: 224→227 (+3)
- DEFI: 70→73 (+3)

Sports — all 5 providers running, no further kills:

- API_FOOTBALL: restarted, fast-forwarding (no done count yet)
- FOOTYSTATS: chunk 11 in flight, 3.8 GB
- TRANSFERMARKT: chunk 1 in flight, 3.5 GB
- UNDERSTAT: chunk 24 in flight, 3.4 GB
- OPEN_METEO: chunk 2 in flight, 3.0 GB

#### 🚨 Awaiting user decision

Per `feedback_just_execute_dont_ask` rule: scope-changing kill = ask. At 15:34 I asked about (a/b/c) on DERIBIT — no
response received yet.

**Per current wakeup rule explicit instruction: do NOT kill DERIBIT, do NOT kill anything else (sports already on
minimum), just flag urgently and report.**

ETA to cap breach: ~12 min at current DERIBIT growth rate. Awaiting user.

### 15:42 IST — RAM hit 86GB, user authorised DERIBIT kill

User instruction: "kill the deribit shard first we are already at 86gb mark. I think we should kill one of the deribit
and then find out the reason of this memory leak before starting new worker for deribit, we can keep one worker
running."

**Action taken**:

1. Killed Python worker PID 786030 (DERIBIT 2019-05-01 chunk, 11.1 GB at moment of kill). Used specific PID, not
   `pkill -f`.
2. Killed the DERIBIT bash wrapper (PIDs 564185 + 786023) so no new chunks spawn.
3. Left PID 786031 (DERIBIT 2019-05-31 chunk, 10.0 GB) running — orphaned (re-parented to init), will run to completion
   writing its data, then no successor.

**Result**: RAM dropped 81 → 65 GB. 16 GB freed.

### Manifest consolidator architecture — answer to user question

**Yes, the system DOES use a manifest consolidator.** Architecture per
`unified_trading_library/manifest_consolidator.py`:

- Each backfill writer creates per-writer shards at `gs://{ag_bucket}/_index/per_vm/{instance_id}.parquet` — replaces
  single-blob CAS hot-path that produced 429 thundering-herd.
- Consolidator (Cloud Run Job + the long-running VM `manifest-consolidator-20260429-162442`) reads all per-VM shards
  every minute, dedup-merges by manifest key (last-attempted-write wins), writes back to canonical
  `_index/availability_index.parquet`.
- Reader-fallback staleness threshold = 120s, so consolidator running every 60s leaves ample margin even if a cycle
  skips.

**Instance ID resolution** in `ManifestWriter._resolve_instance_id()`:

1. `$VM_NAME` (set by deployment-service VM launchers) — used in cloud
2. `$HOSTNAME` fallback — **on this machine = `hk`**
3. `local-{pid}-{rand4}` synthesized — only if neither env var set

**Critical issue for our local runs**: all 47 procs on this machine share `HOSTNAME=hk` and **none have `$VM_NAME`**
(it's only set by VM launchers). **They're all racing for the same `hk.parquet` per-VM shard** — that's why we see the
`ManifestWriter: generation conflict (attempt N/15)` retry loops and the slowness in TRANSFERMARKT chunk 1.

The intended design is one writer per per-VM shard. We're violating it.

**Fix would be**: set a unique `VM_NAME` env var per chunk-worker. Wrap each spawned `instruments-service` invocation
with:

```bash
VM_NAME="local-${VENUE}-${CHUNK_START}-$$" .venv/bin/instruments-service ...
```

Then each proc writes to its own per-VM shard, consolidator merges them all. **No code change needed** — just env-var
injection in `run_vm_backfill_e2e.sh` and `sports_chunked_backfill.sh`. Tracking as follow-up.

In the meantime: existing manifest writes are still consistent (the 15-retry CAS backoff handles the conflicts), just
slow. Consolidator merges per-VM shards correctly even when only `hk.parquet` is being updated by all writers.

### 15:50 IST — INDEX ALIGNMENT issue identified (user-flagged + verified)

User flagged the concern: with 47 procs racing on the same per-VM shard, what happens to writes from procs that lose the
CAS race? Investigation:

#### What's actually happening (verified by GCS inspection)

1. **`MANIFEST_PER_VM_SHARDS` is False by default** in `_resolve_per_vm_shards()` at `manifest_writer.py:172-196`. Our
   local procs never set this env var.
2. **GCS evidence**: `_index/per_vm/` for all 4 AGs only contains shards from 2026-05-01/02 VM runs. **No `hk.parquet`
   exists** — our local procs aren't writing per-VM shards at all.
3. So our 47 procs are using the **legacy CAS path** writing directly to canonical `_index/availability_index.parquet`.
   Each proc:
   - reads with generation G_n
   - merges its updates
   - CAS writes with G_n
   - if generation moved (peer wrote first), retry with G_n+1
   - **15 retries cap** → fall back to **unconditional write** that ignores concurrent peer writes (clobbers their rows)

We observed 9× unconditional-write fallbacks earlier today. Each could have lost manifest rows from peer procs writing
in the conflict window.

#### Risk: per-day parquets safe, but manifest rows may be missing

- **GCS per-day parquets** (the actual instrument data): each writes to its own unique path
  `instrument_availability/by_date/day=X/venue=Y/instruments.parquet`. No collision risk.
- **Manifest rows** (`_index/availability_index.parquet`): high collision under 47-way concurrency. CAS-fallback
  potentially lost rows from peer procs.
- **Result**: orchestrator's `_should_skip_shard` may **redundantly redo** shards whose manifest row got clobbered →
  wasted API calls but no data loss.

#### Two-part fix (committed 2026-05-04 15:53 IST)

**Part 1: Patch scripts to use per-VM shards going forward** — instruments-service commit `00f6352`. Both runner scripts
now inject:

- `VM_NAME=hk_${ag_or_provider}_${chunk-start}_${random6}` — unique per chunk
- `MANIFEST_PER_VM_SHARDS=true` — switches to per-VM shard write path

This means every future-spawned chunk writer hits its own `_index/per_vm/{unique_name}.parquet`. The consolidator
(running every 60s in `manifest-consolidator-20260429-162442` VM) merges them all into the canonical index. **No more
cross-writer CAS contention.**

**Part 2: Recovery for manifest rows already lost** — there's a tool for this:
[`instruments-service/scripts/rebuild_cefi_manifest.py`](../../../instruments-service/scripts/rebuild_cefi_manifest.py)
(supports all asset_groups via `--asset-group` flag despite the name). It scans actual GCS parquets and **adds missing
manifest rows** for `(date, venue)` shards that have data on disk but no manifest entry. **Reverse phantom reconciler.**

To run after current procs settle:

```bash
cd ~/unified-trading-system-repos/instruments-service
.venv/bin/python scripts/rebuild_cefi_manifest.py --dry-run                     # preview
.venv/bin/python scripts/rebuild_cefi_manifest.py --asset-group CEFI --dry-run
.venv/bin/python scripts/rebuild_cefi_manifest.py --asset-group TRADFI --dry-run
.venv/bin/python scripts/rebuild_cefi_manifest.py --asset-group DEFI --dry-run
.venv/bin/python scripts/rebuild_cefi_manifest.py --asset-group SPORTS --dry-run
```

#### What this means for in-flight procs

User instruction: **don't kill in-flight workers, but don't spawn new ones with old code**. The script patches only
affect **future** wrapper invocations:

- In-flight Python workers (already loaded the old config) keep using the legacy CAS path.
- Their child wrappers (bash) re-read the script for the next chunk, so once a current chunk finishes the wrapper picks
  up the patched code on the next iteration.

**Result**: ~next 30-90 min of in-flight chunks still hit the CAS path; after that all new chunks use per-VM shards.
Recovery tool runs after everything settles.

### 16:00 IST — Full reset per user instruction

User: "kill all the tasks and then do the alignment and then start the processes after we do this otherwise we are going
to be downloading the same data again and again."

**Killed all 44 in-flight workers** + bash wrappers (specific PIDs, not pkill -f). Result:

- 0 instruments-service procs running
- 575 chunks durable in `.backfill-checkpoints/`
- RAM 76 → 15 GB (61 GB freed)
- All per-day parquets in GCS preserved (no data loss)

### Pre-recovery analysis (consolidator nuances)

User asked: "are we doing this right way, you should also check how the consolidator VM is doing it to take the
nuances".

Checked `unified_trading_library/manifest_consolidator.py`. Two-tool model:

**Consolidator** (Cloud Run Job + the running VM `manifest-consolidator-20260429-162442`):

- Runs every 60s with 90s soft-lock TTL via `_index/consolidator.lock`
- Lightweight: only lists `_index/per_vm/*.parquet` (tens of shards)
- Merges via `_merge_shard_frames` (last-write-wins dedup by manifest key)
- Single CAS write to canonical `_index/availability_index.parquet`
- **Doesn't crawl actual instrument data parquets** — assumes per-VM shards have authoritative manifest rows.

**rebuild_manifest** (heavyweight, what `rebuild_cefi_manifest.py` calls):

- Lists ALL `instrument_availability/by_date/day=*/venue=*/*.parquet` (millions)
- Parses partition paths to extract `(date, venue)` tuples
- Reads each parquet to count rows
- Adds **missing** manifest rows (preserves existing — does NOT overwrite)
- CAS-writes back to canonical `_index/availability_index.parquet`

**Difference**: consolidator merges already-summarized per-VM shards. rebuild_manifest goes back to ground truth (the
actual instrument parquets) and emits missing manifest rows. **Both are needed today.**

#### Today's failure mode (verified by GCS inspection)

- Canonical `_index/availability_index.parquet` per-AG: `metageneration: 1` → **never updated since creation at ~10:23
  UTC today**. Our 47 local procs were reading + CAS-writing it but `metageneration: 1` would imply none of those CAS
  writes succeeded? Or the CAS-write path doesn't bump metageneration.
- More likely: every CAS write generated a NEW generation (the writer wrote a fresh blob) instead of bumping
  metageneration (which is for metadata-only changes). So generations could be high but metageneration stays at 1.
- Either way, post-OOM and post-many-CAS-fallbacks, the canonical manifest is **likely missing rows** for shards whose
  writers got clobbered.

#### Right recovery path: sequential, not parallel

**Q on parallel rebuild_cefi_manifest.py**: yes, parallel hits GCS list-API rate limits (we already saw this earlier
when 5 reconcilers ran parallel). Plus each rebuild's CAS write to canonical races with consolidator's CAS writes →
double-write conflict. **Sequential = safer.**

**Recovery plan**:

1. Run `rebuild_cefi_manifest.py --dry-run` per AG **sequentially**, ~5 min each (~20 min total). Preview what's
   missing.
2. If counts look reasonable (not surprisingly large), run without `--dry-run` per AG sequentially to write recovery
   rows.
3. After all 4 rebuilds: run `reconcile_phantom_manifest_rows_all.py --dry-run` per AG to check for any remaining
   phantoms (forward-direction: manifest says captured but parquet doesn't exist).
4. Then look at DERIBIT memory leak before restarting CEFI.
5. Then restart CEFI/TRADFI/DEFI/SPORTS with patched scripts (per-VM shards now active per `00f6352`).

#### Pre-existing bug found in rebuild_cefi_manifest.py

Script uses `args.category` but argparse defines `--asset-group` → `args.asset_group`.
`AttributeError: 'Namespace' object has no attribute 'category'`. Fixed in commit `0dd6e82` (instruments-service).

### 16:04 IST — CEFI rebuild dry-run complete

```
2026-05-04 16:03:34 INFO Scanning GCS blobs under instruments-store-cefi.../instrument_availability/by_date/ ...
2026-05-04 16:04:21 INFO rebuild_manifest: discovered 34 (date, venue) shards missing from manifest
2026-05-04 16:04:21 INFO Result: 21989 total entries (+34 new), 2593 unique dates, 16 venues
```

**Reassuring numbers** — only 34 missing manifest rows out of ~22k entries. That's a 0.15% CAS-fallback leak rate. Most
writes survived the conflict loop. Recovery is small.

Note: 16 venues > 9 declared CEFI venues. That includes data left over from 2026-04-29 366-VM rollout (legacy venue
names like BITFINEX-SPOT, KRAKEN-FUTURES, BITGET-\* from earlier sweep) + today's writes.

#### Investigating DERIBIT leak (interim — partial findings)

Looked for module-level caches in `tardis.py` and `orchestrator.py`. Found:

- `_DERIBIT_MONTHS` module-level dict (small, just expiry-month codes, not data)
- `_defi_universe_cache` only kicks in for DeFi venues (DERIBIT is CEFI, doesn't apply)
- `ManifestWriter._records` accumulates but `manifest.close()` IS called per-date at orchestrator.py:1976, clearing the
  buffer

**Hypothesis remaining**: aiohttp ClientSession holds connection-pool / response-body data in the long-lived
options-chain fetch. 200k InstrumentRecord pydantic v2 models × ~7 KB each = ~1.4 GB just for one fetch's results.
Across 30 days, possibly multiple concurrent in-flight responses + cache layers. Without a memory profiler
(tracemalloc), hard to pinpoint the exact leak.

**Pragmatic mitigation**: chunk-cycling already bounds the leak. The 17 GB peak was the 2019-04 chunk's full-month
accumulation; subsequent chunks at 1-2 GB then growing to ~5 GB before next cycle. **Per-chunk RAM bound = 5-17 GB
depending on month**.

**Follow-up plan**: instrument the orchestrator with `tracemalloc.snapshot()` at chunk-end, log top allocators. Or run a
single DERIBIT chunk under `memray run -o leak.bin .venv/bin/instruments-service ...`. Defer to tomorrow.

### 16:05 IST — TRADFI rebuild dry-run started (sequentially)

### 16:06 IST — TRADFI rebuild dry-run complete

```
2026-05-04 16:05:29 INFO Scanning GCS blobs under instruments-store-tradfi.../instrument_availability/by_date/ ...
2026-05-04 16:05:50 INFO rebuild_manifest: discovered 9 (date, venue) shards missing from manifest
2026-05-04 16:05:50 INFO Result: 11527 total entries (+9 new), 2314 unique dates, 6 venues
```

**Even smaller leak: 9 missing rows / 11,527 total = 0.08%.**

| AG     |  Total | Missing | Leak rate |
| ------ | -----: | ------: | --------: |
| CEFI   | 21,989 |      34 |     0.15% |
| TRADFI | 11,527 |       9 |     0.08% |
| DEFI   |    TBD |     TBD |       TBD |
| SPORTS |    TBD |     TBD |       TBD |

Pattern so far: leak rate is small. The CAS retry loop survived most contention. Probably most of the 9
unconditional-write fallbacks earlier today happened on small-row peer writes that got safely re-merged by later writers
via the dedup logic in `_merge_shard_frames`.

### 16:07 IST — DEFI rebuild dry-run started (sequentially)

### 16:20 IST — Distance-to-100% assessment + canonical state audit

User asked for a baseline-vs-now summary. **Important correction first**:

**My earlier "morning baseline" was the WRONG bucket.** The 12:33 IST recon dry-run read from
`gs://market-data-tick-cefi-central-element-323112/_index/availability_index.parquet` — that's the **MTDS
(market-tick-data) bucket**, not instruments-service. The 1,343,892 rows / 188,684 captured were MTDS phantoms, not
instruments-service work.

For **instruments-service** (what we've been backfilling all day), the buckets are:

| AG     | Bucket                                            | Morning rows |           Current rows | Schema                                    | Capture_status state                                                               |
| ------ | ------------------------------------------------- | -----------: | ---------------------: | ----------------------------------------- | ---------------------------------------------------------------------------------- |
| CEFI   | `instruments-store-cefi-central-element-323112`   |       21,955 |        **21,958** (+3) | v4 mostly, 3 v6                           | 21,952 blank (legacy v4 — coerced to "captured" by reader); 3 properly v6-captured |
| TRADFI | `instruments-store-tradfi-central-element-323112` |      ~11,518 |      **11,735** (+217) | v4 mostly, 217 v6                         | 11,301 blank (legacy v4); 217 v6-captured                                          |
| DEFI   | `instruments-store-defi-central-element-323112`   |       69,674 | **69,674** (no change) | older — no `capture_status` column at all | unknown (column missing)                                                           |
| SPORTS | `instruments-store-sports-central-element-323112` |    2,401,547 | **2,404,882** (+3,335) | v5/v6 properly populated                  | 831,965 captured / 1,561,176 empty_confirmed / 11,741 attempted_failed             |

#### Today's contribution to instruments-service manifests = SMALL

Despite 575 chunks completing on disk (per `.backfill-checkpoints/`), **only ~3,500 manifest rows durably committed**:

- CEFI: +3 rows out of (575 × 30 days × ~7 venues = ~17k expected) = **0.02%**
- TRADFI: +217 rows
- SPORTS: +3,335 rows (the SFI VM + our work)
- DEFI: 0 rows (no v5/v6 writes — schema didn't migrate)

**Most of the work didn't land in manifests** because of the CAS-fallback contention we identified. The actual
instrument data parquets ARE on disk in `instrument_availability/by_date/day=X/venue=Y/instruments.parquet`
(rebuild_manifest finds them), they just don't have manifest entries yet.

#### Schema progression

- **v4** (2026-04-04): no capture_status; reader coerces blank to "captured"
- **v5** (2026-04-19): adds capture_status, error_reason, attempted_at — honest-coverage
- **v6** (2026-04-23 — current): adds quote_asset, margin_type, combo_type, leg_weights for DERIBIT inverse-vs-linear
  disambiguation
- Codex doc `availability-manifest-and-data-status.md` is OUT OF DATE — says v4

#### Distance-to-100% — what does "100%" actually mean here?

Three possible interpretations:

1. **Manifest 100% captured + empty_confirmed** under expected-shards denominator. If we count the
   v4-blank-coerced-to-captured rows, CEFI/TRADFI are nearly fully "captured" already (just legacy coverage from
   2026-05-01). Our 575 chunks would add fresh v6 rows on top.
2. **Per-day parquet coverage** — every (asset_group, venue, day) in the cutoff window has a parquet on disk. CEFI: 575
   chunks × 30 days × 7 venues / total expected = ~10-20% of needed dates have fresh parquets from today.
3. **All adapters running cleanly** — done for 4/5 AGs (sports + 3 instruments), missing PREDICTION (out-of-scope) and
   ADAPTER bugs for OKX, COINBASE, POLYGON, FRED.

For **interpretation (1)**: we're effectively still at the 2026-05-01 state per the canonical manifest. Today's work
hasn't durably moved the needle YET — but recovery via rebuild_cefi_manifest.py + per-VM-shards-from-now-on will fix
this.

For **interpretation (2)**: we're closer than the manifests suggest because the parquets exist, the manifest just
doesn't index them.

#### Recovery plan to actually move the index forward

1. Wait for all 4 rebuild_cefi_manifest.py dry-runs to complete (DEFI in flight, SPORTS queued).
2. Review counts. If reasonable (no surprise high), run write-mode per AG sequentially.
3. Restart workers with patched scripts (per-VM shards + unique VM_NAME).
4. Investigate DERIBIT memory leak before re-enabling DERIBIT chunk-2.
5. Periodic reconciler dry-run to verify alignment as work progresses.

5 min after sports fan-out:

| Metric            | Value                  | Status                                   |
| ----------------- | ---------------------- | ---------------------------------------- |
| RAM used          | 52 GB / 80 GB cap      | ✅ 28 GB headroom                        |
| RAM trend (5 min) | 46→52 GB               | ✅ stable, slow climb                    |
| Swap              | 0.7 GB                 | ✅ idle (was 6.7 GB at OOM, now drained) |
| OOM kills         | 0                      | ✅                                       |
| Rate-limit hits   | 0                      | ✅ (watchdog re-armed PID 621482)        |
| Procs             | 43                     | —                                        |
| Checkpoints       | 399 (+23 since resume) | ✅                                       |

Progress per AG:

- CEFI: 199 chunks (+7 since resume)
- TRADFI: 166 chunks (+21 since resume; fastest)
- DEFI: 34 chunks (+7 since resume)
- SPORTS chunked: API_FOOTBALL 3 chunks, FOOTYSTATS 1, others on chunk 1
  - TRANSFERMARKT still on chunk 1 since 14:15 (15 min/chunk — internal rate-limit at ~1 req/sec is the real-world pace;
    not stuck, just paced)

### Real adapter errors observed (not rate-limit)

- **9× Databento NASDAQ `XNAS.ITCH symbols=2: 422 symbology_invalid_request`** — adapter sending invalid symbol format
  for some early dates (likely BTC/ETH ETF tickers that don't exist pre-listing; `TRADFI_TICKER_COVERAGE_START` should
  clip but apparently isn't always). Lands as `attempted_failed` rows; not blocking. Follow-up: investigate why the
  ticker cutoff isn't applying for these specific cases.

## Status snapshot (2026-05-04 13:15 IST — end of session)

**Phase 0 (diagnose) — DONE.** Per-asset-group dry-runs completed; phantom counts known. **Phase 1 (flip phantoms) —
DONE for cefi/tradfi/sports.**

- cefi: 12,540 phantoms flipped to `attempted_failed`
- tradfi: 2,726 phantoms flipped
- sports: 41,223 phantoms flipped (SFI excluded)
- prediction: 11,848 phantoms found but **out of scope** (POLYMARKET/`trades` is MTDS data)
- defi: 597 phantoms found, deferred (low priority)

**Phase 2 (backfill) — NOT DONE, two blockers:**

1. **Local cefi/tradfi backfill via `run_vm_backfill_e2e.sh` failed silently** — runner doesn't export `GCP_PROJECT_ID`,
   so every chunk aborts at bootstrap. Re-fire commands with corrected env are in the "Pending work" section below.
   ~Easy fix.
2. **Sports VM launches blocked on IAM** — `harshkantariya@odum-research.com` lacks `roles/iam.serviceAccountUser` on
   the Compute SA. Ikenna needs to grant. Fallback: run sports adapters locally too (same Python CLI; needs
   `GCP_PROJECT_ID` env). Singleton lock would be bypassed — risk of API thrash if other agents launch sports VMs in
   parallel.

**Net**: nothing's been actually backfilled today. Manifests are honest now (phantoms flipped → orchestrator will retry
on next launch), but the launches haven't happened. Resume tomorrow once the env-var fix is applied + IAM grant lands.

## Context

Scope of _this_ plan is narrower than the parent epic (`instruments_and_market_tick_data_completion_2026_05_01.md`):

- **Service**: `instruments-service` only — instrument-definition shards, not market-tick or market-data-processing.
- **Asset groups**: all five — `cefi`, `tradfi`, `sports`, `prediction`, `defi`.
- **Target**: ≥99% `captured + empty_confirmed` under the secondary-cutoff denominator (per parent-epic success
  criteria) by EOD 2026-05-04.
- **Non-goals (this plan)**: deployment-ui Phase 0 bug fixes (deferred — Harsh will pick up later), market-tick-data
  backfills, MDPS candle generation, sports % drive (in flight by another agent).

**Why a separate plan**: parent epic has Phase 0 (UI) → Phase 1 (sports tick) → Phase 2 (cefi) → etc. as a sequential
DAG. Today's "instruments-only to 100%" cuts a horizontal slice across all asset groups for a single service. Tracking
it separately keeps the parent epic clean and gives a tight EOD success criterion.

**Background discoveries from this session (2026-05-04)** that shape this plan:

- `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` is the right diagnostic — supports all 5 asset
  groups via `ASSET_GROUP_CONFIG`, probes both `category=` (legacy) and `asset_group=` (canonical) hive keys to avoid
  the 2026-05-01 false-181k-phantoms incident on cefi.
- `reconcile_phantom_manifest_rows.py` (no `_all` suffix) is sports-only. Don't use it for cefi/tradfi/defi/prediction.
- The `deployment-ui` Deploy button does **not** spawn VMs locally (no orchestrator worker runs in T2 dev). VM-spawning
  is done via the shell launchers in `deployment-service/scripts/vm/launch-*.sh` directly. Harsh's teammate's 31 running
  VMs all came from those launchers.
- The cloud `deployment-dashboard` Cloud Run service exists but is in failed state since 2026-04-30 (`Ready=False`,
  container failed startup). T3 is non-functional. T2 is the SSOT.
- Per CLAUDE.md and the playbook, the canonical workflow is:
  ```
  1. reconcile dry-run (per asset group)        — diagnose
  2. reconcile (no --dry-run) for any phantoms  — flip stale captured→attempted_failed
  3. launch backfill VMs                        — orchestrator now retries the failed shards
  4. wait, re-run reconcile dry-run             — verify zero phantoms remain
  5. verify drilldown / GCS spot-check          — confirm ≥99%
  ```

## Cutoffs (per playbook + UAC `coverage_starts.py`)

Same cutoffs as parent epic — repeated here so this plan is self-contained:

| Asset group | Start (global)          | End   | Per-shard secondary clip                                          |
| ----------- | ----------------------- | ----- | ----------------------------------------------------------------- |
| CEFI        | 2019-01-01              | today | per-venue inception (`CEFI_SOURCE_COVERAGE_START`)                |
| TRADFI      | 2019-01-01              | today | per-ticker listing (`TRADFI_TICKER_COVERAGE_START`)               |
| SPORTS      | 2020-06-01              | today | per-source + prediction-vs-reference league filter                |
| PREDICTION  | 2020-06-12 (POLYMARKET) | today | per-venue + per-sub-category (`PREDICTION_SOURCE_COVERAGE_START`) |
| DEFI        | per-protocol launch     | today | per-protocol-per-chain (`DEFI_SOURCE_COVERAGE_START`)             |

Always pass the **global** start. Launchers + manifest writers handle the secondary clip through UAC
`clip_dates_to_source_coverage` / equivalents — pre-launch days land as `empty_confirmed`, not `attempted_failed`.

## Execution DAG

```
Phase 0 (Diagnose, parallel)
   ├── reconcile dry-run cefi
   ├── reconcile dry-run tradfi
   ├── reconcile dry-run sports
   ├── reconcile dry-run prediction
   └── reconcile dry-run defi
        │
        ▼  (review numbers; decide what to launch)
Phase 0.5 (Sports gate — verify in-flight work has settled before launching new sports VMs)
        │
        ▼
Phase 1 (Flip phantoms, parallel — only for asset groups with non-zero phantoms)
        │
        ▼
Phase 2 (Launch backfills, parallel by asset group)
        │
        ▼  (wait — VMs run hours/days)
Phase 3 (Verify, parallel)
        │
        ▼
Phase 4 (Sign-off + plan close)
```

Realistic ETA caveat: Phase 2 wall time depends on shard count. CEFI 2019-→today across 9 venues has ~22k potential
shards. Even with 100 concurrent VMs and ~5 min per shard, that's ~18 hours. **EOD target may slip into the next day**
if the gap is large; we'll know after Phase 0 dry-runs.

## Phase 0 — Diagnose (read-only, parallel)

**Scope nit before starting**: "instruments at 100%" can mean two things:

1. **Per-day shard coverage**: every `(asset_group, venue, day)` tuple in the cutoff window has a manifest row in
   `captured + empty_confirmed`. The reconciler measures this.
2. **Per-instrument completeness on captured days**: each captured day's parquet contains every instrument that was
   tradeable on that day on that venue.

The reconciler dry-run only measures (1). (2) requires a separate per-row content audit.

- [ ] [HUMAN] P0. Confirm with Ikenna which "100%" he means before launching backfills. If (2), the work is much larger
      (we'd need a content-validation script per AG, none exists generically today). Default assumption for now:
      **(1)**.

For each asset group, dry-run the reconciler to learn:

- Total manifest rows scanned
- Phantom rows found (claimed `captured` but no parquet)
- Real `captured` count
- Real `attempted_failed` count
- Missing-row count under the secondary cutoff

Run each in its own terminal/background — they're independent. Per script docstring, bulk-list pattern is ~5 min for
600k rows per asset group.

- [ ] [SCRIPT] P0. Dry-run cefi:
      `bash     cd ~/unified-trading-system-repos/instruments-service     .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py \       --asset-group cefi --dry-run 2>&1 | tee /tmp/recon-cefi.log     `
- [ ] [SCRIPT] P0. Dry-run tradfi: same as above with `--asset-group tradfi`, log to `/tmp/recon-tradfi.log`.
- [ ] [SCRIPT] P0. Dry-run sports: same with `--asset-group sports`, log to `/tmp/recon-sports.log`. **Note**: sports
      manifest is the in-flight one; numbers may shift as the consolidator daemon merges. Re-run if anomalies appear.
- [ ] [SCRIPT] P0. Dry-run prediction: same with `--asset-group prediction`, log to `/tmp/recon-prediction.log`.
- [ ] [SCRIPT] P0. Dry-run defi: same with `--asset-group defi`, log to `/tmp/recon-defi.log`.
- [ ] [HUMAN] P0. Review all five logs. Capture the per-asset-group counts in this plan's Notes section so we have a
      baseline. Decide: which asset groups need phantom flips (Phase 1)? Which need backfill VMs (Phase 2)?

## Phase 0.5 — Sports gate (partial — SFI excluded from this run)

Per parent-epic Phase 0.5 — sports backfill VMs share league partitions, so collisions cause double-writes and manifest
noise. As of session start (2026-05-04 11:30 IST):

- **SFI (`soccer_football_info`) has 1 instruments-service VM running** for sports backfill. **This plan EXCLUDES SFI**
  — do not launch any new SFI backfill or run sports reconciler with SFI data types in scope. Other sports sources
  (api-football, transfermarkt, footystats, understat, openmeteo) are eligible if their gate query is clean.

- [ ] [HUMAN] P0. Confirm the SFI VM is the only in-flight sports work, and capture which data types it's covering (so
      we know what NOT to touch):
      `bash     gcloud compute instances list \       --filter='name~"^(af|tm|sfi|fs|manifest-consolidator)-"' \       --format='table(name,status,zone,creationTimestamp)'     `
      Expected: only the SFI VM + optional `manifest-consolidator-*`. If `af` / `tm` / `fs` VMs are also RUNNING — stop
      and ping the other agent's owner.
- [ ] [SCRIPT] P0. When running sports phantom recon, scope away from SFI to avoid racing its writes:
      `bash     .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py \       --asset-group sports --dry-run \       --data-types FIXTURES,FIXTURE_EVENTS,STANDINGS,LEAGUES,TEAMS,PLAYER_STATS,ODDS,PLAYER_VALUES,TRANSFERMARKT_LEAGUES     `
      (Replace data-types list with the non-SFI set Phase 0 reveals as relevant.) **Do NOT** include `SFI_LEAGUES` or
      `SFI_PROGRESSIVE_STATS` while SFI VM is running — its writes are mid-flight and reconciler reads would race them.
- [ ] [HUMAN] P0. Snapshot sports drilldown headline coverage. Per parent-epic Phase 0.5, should be ≥80% captured.

## Phase 1 — Flip phantoms (parallel, only for AGs with phantoms > 0)

Run _without_ `--dry-run` only for asset groups where Phase 0 found phantoms. This is fast (same bulk-list pattern as
dry-run, plus a single manifest write per asset group).

**Critical**: do NOT write empty placeholder parquets to mask phantoms. Per CLAUDE.md manifest-phantom-audit rule:
`record_empty(...)` is for legitimately-empty source responses only. Phantoms must be flipped to `attempted_failed` so
VMs re-attempt them.

- [ ] [SCRIPT] P0. Flip phantoms for each AG with phantom_count > 0:
      `bash     .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py --asset-group <ag>     ` (no
      `--dry-run`). Repeat per asset group.
- [ ] [SCRIPT] P0. Re-run dry-run for each flipped AG to confirm phantom count → 0.

## Phase 2 — Launch backfills (parallel by asset group)

This is where the actual instruments-service work happens. Critical distinction discovered in this session (2026-05-04):

**The cefi/tradfi/defi/prediction launchers in `deployment-service/scripts/vm/launch-*-backfill*.sh` that look like
they're for instruments are NOT.** They have `VM_SERVICE=market_tick_data_service` and `VM_TASK=cefi-backfill` — they
download tick data, not instrument definitions. Inspected the metadata of all 31 currently-running VMs
(`cefi-bitfinex-…`, `cefi-okx-swap-…`, `cefi-deribit-…`, etc.) — they're all MTDS, not instruments-service.

**Launchers that actually run instruments-service** (verified by `grep VM_SERVICE=instruments_service` across
`deployment-service/scripts/vm/`):

- `launch-instruments-smoke-vm.sh` — single-day smoke test (writes to `*-test-` buckets, not prod)
- `launch-{api-football,transfermarkt,sfi,footystats,understat,openmeteo}-backfill-vm.sh` — sports instruments only
- `launch-sfi-forward-poll.sh`, `launch-footystats-forward-poll.sh` — daily forward-poll (live, not backfill)
- `launch-sports-manifest-rescan-vm.sh` — sports manifest rescan only

For **cefi/tradfi/defi/prediction instruments**, **no dedicated VM launcher exists**. The canonical local-driver script
is [`instruments-service/scripts/run_vm_backfill_e2e.sh`](../../../instruments-service/scripts/run_vm_backfill_e2e.sh)
(despite the name "vm" it runs locally — it invokes `.venv/bin/instruments-service ...` on whatever machine you run it
on, with checkpointing + parallel chunks). Two paths to use it:

**Path A — local driver (simplest, fine for small gaps)**: run `run_vm_backfill_e2e.sh` directly on this machine.
Resumable via checkpoints, so safe to interrupt. **IP-rate-limited to your laptop's IP** — fine for instruments-service
(low API volume, tiny payloads), bad for tick-data scale.

**Path B — wrap in a VM (ad-hoc)**: write a one-line `gcloud compute instances create` that sets
`VM_SERVICE=instruments_service`, `VM_OPERATION=download`, `VM_ASSET_GROUP=…`, `VM_VENUE=…`, `VM_START_DATE`,
`VM_END_DATE` — same metadata pattern as `launch-instruments-smoke-vm.sh` but with prod buckets (no `IS_TEST_RUN=true`).
Defer to Ikenna before doing this — the smoke launcher exists, the prod-equivalent doesn't, and adding one new pattern
is something he'd want to bless.

**Cost model (correction to common intuition)**: VMs in this stack have `VM_SHUTDOWN_ON_COMPLETION=true` — each one
self-deletes when its shard finishes. Cost ≈ `(shard_count × per-shard_runtime × $0.07/hr)` on `e2-standard-2`. **Many
short-lived VMs are NOT inherently expensive** — what matters is total runtime. For instruments-service the per-shard
runtime is small (low API volume). The 31 currently-running MTDS VMs cost ~$52/day at full burn; instruments-service
backfill at the same scale would cost a fraction of that since shards finish in minutes. Don't switch to a long-lived
single-VM model — that costs more (idle time billed) and breaks shard-level failure isolation.

**Tarball refresh**: per CLAUDE.md, refresh only if **instruments-service / UAC / UTL** code changed. Today's session
changed only deployment-api + deployment-service routes (irrelevant to backfill VMs). **No tarball refresh needed.** If
unsure:

```bash
bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group <X>
```

**`--force` warning**: every launcher / CLI accepts a force flag (the deploy form defaults it to `true`, but for these
scripts default is `false`). With `force=true`, the orchestrator re-fetches every shard regardless of
`_should_skip_shard` — billable API cost, possible rate-limit hit. **Use `force=false` for daily gap-fill.** Reserve
`force=true` for retesting one specific shard or after a code-fix that requires re-running known-bad data.

### CEFI

- [ ] [HUMAN] P0. Confirm Phase 0 cefi gap (review `/tmp/recon-cefi.log`).
- [ ] [HUMAN] P0. **Pick path** — local-driver (Path A, fast iteration) or VM-wrap (Path B, needs Ikenna sign-off). For
      the per-asset-group counts likely seen at 85% baseline, Path A is probably enough.
- [ ] [HUMAN] P0. Path A launch (per CEFI venue):
      `bash     cd ~/unified-trading-system-repos/instruments-service     bash scripts/run_vm_backfill_e2e.sh \       --venue BINANCE-SPOT \       --asset-group CEFI \       --start-date 2019-01-01 --end-date $(date -u +%Y-%m-%d) \       --chunk-days 30 --parallel 4     `
      Repeat for each CEFI venue with a non-trivial gap (BINANCE-FUTURES, DERIBIT, BYBIT, OKX, UPBIT, COINBASE,
      HYPERLIQUID, ASTER). The script chunks the date range, parallel-runs `--parallel` chunk workers, and checkpoints
      to `.backfill-checkpoints/<venue>/<chunk>.done` so re-runs skip completed chunks.
- [ ] [HUMAN] P1. Watch progress via the checkpoint dir:
      `ls instruments-service/.backfill-checkpoints/CEFI/<venue>/ | wc -l`.

### TRADFI

- [ ] [HUMAN] P0. Confirm Phase 0 tradfi gap (review `/tmp/recon-tradfi.log`).
- [ ] [HUMAN] P0. Same Path A pattern as CEFI, per TradFi venue:
      `bash     bash scripts/run_vm_backfill_e2e.sh \       --venue CME --asset-group TRADFI \       --start-date 2019-01-01 --end-date $(date -u +%Y-%m-%d) \       --chunk-days 30 --parallel 4     `
      Repeat for `CBOE`, `NASDAQ`, `NYSE`, `ICE`, `FX`, `POLYGON`, `FRED` if their slice is red. Per-ticker listing-date
      clip is shipped (`TRADFI_TICKER_COVERAGE_START` UAC `15b9e74`), pre-listing days auto-skip.

### SPORTS — instruments-service backfill, with SFI excluded

- [ ] [HUMAN] P0. **GATE**: Phase 0.5 must confirm only the SFI VM is running. Other sources
      (af/tm/fs/understat/openmeteo) clear to launch.
- [ ] [HUMAN] P0. Sports has dedicated launchers (`VM_SERVICE=instruments_service` confirmed in metadata). Pick the
      launcher matching the data-type slice that's red in `/tmp/recon-sports.log`. **Do NOT touch SFI** while its VM is
      running — skip `launch-sfi-backfill-vm.sh` and `launch-sfi-forward-poll.sh`. ```bash # api-football (LEAGUES,
      TEAMS, FIXTURES, FIXTURE_EVENTS, STANDINGS, INJURIES, …) bash
      ~/unified-trading-system-repos/deployment-service/scripts/vm/launch-api-football-backfill-vm.sh \
      --data-type <X> --start-date 2020-06-01

      # transfermarkt (PLAYER_VALUES, TRANSFERMARKT_LEAGUES)
                                                                                  bash .../launch-transfermarkt-backfill-vm.sh --data-type <X> --start-date 2020-06-01

                                                                                  # footystats / understat / openmeteo — same pattern
                                                                                  ```
                                                                                  For non-prediction reference leagues, scope to FIXTURES + FIXTURE_EVENTS + STANDINGS
                                                                                  only — per parent-epic prediction-vs-reference cutoff rule. The orchestrator's
                                                                                  `_should_skip_shard` + `_should_skip_reference_league` guards handle this; pass
                                                                                  `--leagues prediction|reference|all` if the launcher accepts it.

- [ ] [SCRIPT] P0. After each non-SFI launcher batch completes, re-run sports phantom recon (no `--dry-run`) **with the
      same `--data-types` scope as Phase 0.5** (i.e. excluding SFI_LEAGUES / SFI_PROGRESSIVE_STATS until the SFI VM is
      done).

### PREDICTION

- [ ] [HUMAN] P0. Confirm Phase 0 prediction gap (review `/tmp/recon-prediction.log`).
- [ ] [HUMAN] P0. **No dedicated launcher exists**. Use Path A (local driver):
      `bash     bash scripts/run_vm_backfill_e2e.sh \       --venue POLYMARKET --asset-group PREDICTION \       --start-date 2020-06-12 --end-date $(date -u +%Y-%m-%d) \       --chunk-days 30 --parallel 2     bash scripts/run_vm_backfill_e2e.sh \       --venue KALSHI --asset-group PREDICTION \       --start-date 2021-07-19 --end-date $(date -u +%Y-%m-%d) \       --chunk-days 30 --parallel 2     `
      Lower `--parallel` (2 not 4) since PREDICTION venues have stricter rate limits.
- [ ] [HUMAN] P1. Per-sub-category cutoffs (crypto/macro/football for POLYMARKET) — handled by the adapter's internal
      coverage clip; pass venue-only here.

### DEFI

- [ ] [HUMAN] P0. Confirm Phase 0 defi gap (review `/tmp/recon-defi.log`).
- [ ] [HUMAN] P0. **No dedicated launcher exists**. Use Path A per DeFi venue:
      `bash     bash scripts/run_vm_backfill_e2e.sh \       --venue AAVE_V3-ETHEREUM --asset-group DEFI \       --start-date 2022-03-16 --end-date $(date -u +%Y-%m-%d) \       --chunk-days 30 --parallel 4     bash scripts/run_vm_backfill_e2e.sh \       --venue UNISWAP_V3-ETHEREUM --asset-group DEFI \       --start-date 2021-05-05 --end-date $(date -u +%Y-%m-%d) \       --chunk-days 30 --parallel 4     # Repeat per (protocol × chain) — see UAC DEFI_SOURCE_COVERAGE_START for inception dates.     `
      DeFi instruments are monotonically-increasing (immutable contracts) per the orchestrator high-watermark logic —
      `_should_skip_shard` + per-venue HWM means most days will auto-skip. Only red shards re-run.

## Phase 3 — Verify (parallel)

- [ ] [SCRIPT] P0. For each asset group: re-run `reconcile_phantom_manifest_rows_all.py     --asset-group <X> --dry-run`
      and confirm phantom count is 0.
- [ ] [HUMAN] P0. Snapshot the deployment-ui drilldown for `service=instruments-service` per asset group. Each should
      show ≥99% `captured + empty_confirmed` under the secondary- cutoff denominator.
- [ ] [HUMAN] P1. Spot-check 5 random `(asset_group, day, venue, instrument_type)` rows: follow each to its canonical
      GCS path and confirm the parquet exists.

## Phase 4 — Sign-off + plan close

- [ ] [HUMAN] P0. Update parent epic (`instruments_and_market_tick_data_completion_2026_05_01.md`) progress notes: mark
      instruments-service slice complete, link to this plan.
- [ ] [HUMAN] P0. Brief Ikenna on results vs the EOD target.
- [ ] [AGENT] P2. Mark this plan complete and move to `plans/archive/`.

## Files / commands referenced

| Repo                  | File / command                                                                                                           | Phase |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----- |
| instruments-service   | `scripts/reconcile_phantom_manifest_rows_all.py`                                                                         | 0,1,3 |
| instruments-service   | `scripts/run_vm_backfill_e2e.sh` (local-driver, resumable)                                                               | 2     |
| deployment-service    | `scripts/vm/launch-{api-football,transfermarkt,footystats,understat,openmeteo}-backfill-vm.sh` (sports instruments only) | 2     |
| deployment-service    | `scripts/vm/launch-instruments-smoke-vm.sh` (single-day, \*-test buckets)                                                | ref   |
| unified-api-contracts | `unified_api_contracts/canonical/coverage_starts.py`                                                                     | ref   |
| unified-trading-pm    | `/codex/14-playbooks/backfill-completion-playbook.md`                                                                    | ref   |

**Explicitly NOT used** (these run MTDS / market-tick-data, not instruments-service): `launch-cefi-sharded-backfill.sh`,
`launch-tradfi-backfill-vm.sh`, `launch-mdps-*-backfill*.sh`.

## Success criteria

- All 5 asset groups: ≥99% `captured + empty_confirmed` for `service=instruments-service`, scoped to the
  secondary-cutoff denominator (per parent-epic). **Definition (1) of "100%"** per Phase 0 scope-nit; revisit if Ikenna
  meant (2).
- Phantom recon dry-run reports 0 phantom flips for every asset group (excluding SFI while its VM is running).
- Drilldown spot-check: 5 random captured rows per AG resolve to actual parquets in GCS.

## Execution log (2026-05-04 EOD push)

- **12:33–12:48 IST**: Phase 0 dry-runs for cefi/tradfi/sports/prediction/defi (parallel after the `tempfile` patch).
  Sports first attempt timed out on GCS list under 5x parallel load; retry with `--workers 16` succeeded.
- **12:46–12:57 IST**: Phase 1 phantom flips for cefi (12,540), tradfi (2,726), sports (41,223 SFI-excluded). All wrote
  manifest back successfully.
- **12:55 IST**: Phase 2 TRADFI backfill fired locally via `run_vm_backfill_e2e.sh` for CME/CBOE/NASDAQ/NYSE/ICE/FX (6
  venues × 4 chunk-workers = 24 concurrent instruments-service procs). No IAM issue — runs on this machine.
- **12:57 IST**: Phase 2 CEFI backfill fired locally for the 9 active CEFI venues (9 × 4 = 36 concurrent procs).
- **12:57 IST**: Phase 2 SPORTS af + tm VM launches blocked:
  `User does not have access to service account 1060025368044-compute@developer.gserviceaccount.com. Ask a project owner to grant the iam.serviceAccountUser role.`
- **13:10 IST**: Discovered cefi+tradfi local backfills had been silently failing every chunk on
  `GCP_PROJECT_ID must be set in environment` — `run_vm_backfill_e2e.sh` doesn't export the env. All 90 chunks per venue
  × 15 venues showed "START" but never "DONE", produced zero checkpoints, wrote nothing to GCS. Killed all in-flight
  procs, cleaned checkpoints + logs.
- **13:08 IST**: Investigation found that the `setup-data-pipeline-vm.sh` script (line 596+) for
  `VM_TASK=sports-backfill` just runs:
  ```
  python -m instruments_service --operation instruments --mode batch \
    --asset-group SPORTS --sports-provider {API_FOOTBALL|TRANSFERMARKT|...} \
    --sports-entity <ENTITY> --start-date <X> --end-date <Y>
  ```
  **The IAM block is NOT a hard blocker — same CLI runs locally** like cefi/tradfi. Smoke test confirmed:
  `.venv/bin/python -m instruments_service ...` accepts the same args; only requires
  `GCP_PROJECT_ID=central-element-323112` env. Can fire all sports retries on this laptop without VM access. (Whether
  this is _desirable_ — singleton rate-limit lock exists for a reason; running locally bypasses it — see Risks section.)

## Adapter smoke matrix (1 day per venue, 2026-05-01)

Run before any fan-out — confirms the adapter+API+GCS+manifest path is wired per venue. Command pattern:

```bash
cd ~/unified-trading-system-repos/instruments-service
GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp CLOUD_MOCK_MODE=false \
  .venv/bin/instruments-service \
  --operation instruments --mode batch \
  --asset-group <AG> --venues <VENUE> \
  --start-date 2026-05-01 --end-date 2026-05-01
```

### Column meanings

- **Active@day** — instruments that were **actually written to GCS** for the queried date (after applying per-instrument
  launch/delisting filtering). This is the captured count.
- **Universe** — instruments the adapter received from the upstream source AFTER symbol-level filtering (majors +
  x-coins, not the entire venue universe). Tells us the adapter is talking to the API. `Universe ≥ Active@day` always;
  the gap = instruments that exist in the venue's history but aren't tradeable on the queried day.
- A healthy smoke = `Active@day > 0`. A zero `Universe` means the adapter never reached the API. A non-zero `Universe`
  with zero `Active@day` means date-filter / validation rejected everything (config bug, not API bug).

### CEFI smoke results (2026-05-04 13:20 IST)

| Venue           | Status | Active@day / Universe  | Notes                                                                                                                                                                                                                                                                                   |
| --------------- | :----: | ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BINANCE-SPOT    |   ✅   | 48 / 51                | Tardis `binance` endpoint, healthy. 3 instruments delisted before 2026-05-01.                                                                                                                                                                                                           |
| BINANCE-FUTURES |   ✅   | 33 / 37                | Tardis `binance-futures` endpoint, healthy.                                                                                                                                                                                                                                             |
| DERIBIT         |   ✅   | 3,720 / 200,312        | Tardis returns full historical options chain (200k symbols across all expiries we ever saw); 3.7k active for 2026-05-01.                                                                                                                                                                |
| BYBIT           |   ✅   | 32 / 291               | Tardis `bybit` + `bybit-spot`, healthy.                                                                                                                                                                                                                                                 |
| **OKX**         |   ❌   | adapter never ran      | `URDI[OKX]: ADAPTER_ERROR (permanent): No Tardis exchange mapping for canonical venue 'OKX'`. Config bug — UAC `venue_to_tardis` mapping missing for canonical name `OKX`. Sharding config lists `OKX`, but adapter expects `OKX-SPOT` / `OKX-SWAP` / `OKX-FUTURES`. **Not geo-block.** |
| UPBIT           |   ✅   | 12 / 13                |                                                                                                                                                                                                                                                                                         |
| **COINBASE**    |   ❌   | adapter ran, 0 written | `URDI returned zero records for date=2026-05-01 asset_groups=['CEFI']`. Adapter ran but got nothing back. Either bare `COINBASE` is also a sharding-vs-adapter mismatch (canonical might be `COINBASE-SPOT`), or transient API issue.                                                   |
| HYPERLIQUID     |   ✅   | 21 / 21                | On-chain CLOB, native API. No history-vs-active gap.                                                                                                                                                                                                                                    |
| ASTER           |   ✅   | 19 / 19                |                                                                                                                                                                                                                                                                                         |

**7 of 9 CEFI venues healthy. OKX + COINBASE blocked on canonical-venue-name mismatches.** The Phase 2 backfill should
proceed for the 7 working venues; OKX + COINBASE need a fix in either UAC `venue_to_tardis` map or the sharding YAML
before they can run.

#### OKX + COINBASE root cause (deeper)

Followed the trail across three SSOTs that disagree:

1. **PM `unified-trading-pm/configs/venues.yaml`** (used by deployment-api shard calculator):

   ```yaml
   CEFI:
     {
       venues: [..., OKX, COINBASE, ...],
       venue_to_tardis: { OKX: [okex, okex-futures, okex-swap], COINBASE: coinbase },
     }
   ```

   Canonical names: **unsuffixed** `OKX` / `COINBASE`.

2. **UAC `unified_api_contracts/registry/venue_mapping.py` `tardis_to_venue`**:

   ```python
   "okex": "OKX-SPOT", "okex-swap": "OKX-SWAP", "okex-futures": "OKX-FUTURES",
   "coinbase": "COINBASE-SPOT"
   ```

   Canonical names: **suffixed** `OKX-SPOT` / `OKX-SWAP` / `OKX-FUTURES` / `COINBASE-SPOT`.

3. **UAC venue registry** (CeFi / TradFi / DeFi / sports membership for validation): Rejects BOTH unsuffixed (`OKX`,
   `COINBASE`) AND suffixed (`OKX-SPOT`, `COINBASE-SPOT`) forms. Per smoke test: `--venues OKX-SPOT` runs through Tardis
   fine (fetches 112 instruments), then
   `Instrument validation: 112 rejected — unknown venue 'OKX-SPOT' — not in CeFi, TradFi, DeFi, or sports registries`.

So **all three** of `OKX`, `OKX-SPOT`, `OKX-SWAP`, `OKX-FUTURES`, `COINBASE`, `COINBASE-SPOT` fail somewhere in the
pipeline. There's no working canonical name today.

**Fix scope**: this is a multi-repo alignment problem (PM venues.yaml ↔ UAC tardis_to_venue ↔ UAC venue registry). Out
of scope for an EOD push. **Action for tomorrow**: file a separate plan to align the three SSOTs on one canonical naming
convention. For today's "100% by EOD" goal, accept that OKX + COINBASE remain at their current coverage and proceed with
the 7 healthy CEFI venues.

### TRADFI smoke results (2026-05-04 13:26 IST)

| Venue       | Status | Active@day / Universe  | Notes                                                                                                                                                                                                              |
| ----------- | :----: | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| CME         |   ✅   | 14,794 / 16,394        | Databento, healthy. Includes futures + options chain. 1.6k gap = expired or future-dated quarterlies.                                                                                                              |
| CBOE        |   ✅   | 1 / 1                  | VIX index (Barchart). Single-record SSOT, expected.                                                                                                                                                                |
| NASDAQ      |   ✅   | 43 / 258               | Databento equities (BTC/ETH ETFs only — universe is 258 symbols we ever cared about; 43 active for 2026-05-01).                                                                                                    |
| NYSE        |   ✅   | 215 / 256              |                                                                                                                                                                                                                    |
| ICE         |   ✅   | 2,067 / 2,069          |                                                                                                                                                                                                                    |
| FX          |   ✅   | 1 / 1                  | KRW/USD via Yahoo Finance, single instrument.                                                                                                                                                                      |
| **POLYGON** |   ❌   | adapter never ran      | `URDI[POLYGON]: ADAPTER_ERROR (permanent): api_key required — service must fetch polygon-api-key from Secret Manager`. Either secret is missing in SM or `ApiKeyReloader` isn't picking it up. **Needs SM check.** |
| **FRED**    |   ❌   | adapter ran, 0 written | `URDI returned zero records for date=2026-05-01`. 2026-05-01 was a Friday — FRED should have data. Not yet root-caused; possibly adapter bug or cutoff issue.                                                      |

**6 of 8 TRADFI venues healthy.** POLYGON + FRED fail. Both need separate investigation; do not block the 6 healthy
venues from Phase 2 backfill.

### DEFI smoke results (2026-05-04 13:36 IST)

| Venue               | Status | Active@day / Universe | Notes                                                              |
| ------------------- | :----: | --------------------- | ------------------------------------------------------------------ |
| AAVE_V3-ETHEREUM    |   ✅   | 52 / 89               | Lending markets (subgraph). 89 historical, 52 active.              |
| UNISWAP_V3-ETHEREUM |   ✅   | 318 / 5,997           | Pool universe (subgraph). 5.9k pools ever, 318 active.             |
| UNISWAP_V2-ETHEREUM |   ✅   | 24 / 772              | Pool universe (subgraph).                                          |
| CURVE-ETHEREUM      |   ✅   | 13 / 49               |                                                                    |
| LIDO-ETHEREUM       |   ✅   | 2 / 2                 | Liquid-staking tokens (stETH, wstETH).                             |
| BALANCER-ETHEREUM   |   ✅   | 1,249 / 2,072         | Pool universe — biggest write count, ~60% historical-pool dropout. |
| EIGENLAYER-ETHEREUM |   ✅   | 1 / 1                 | EIGEN token. Single instrument, expected.                          |

**7 of 7 DEFI venues healthy.** All protocol-chains verified. DEFI Phase 2 backfill is unblocked — local-driver pattern
works for every protocol. (Reminder: DEFI manifest had only 597 phantoms and they were all on EIGENLAYER `rewards`, not
core instruments. Low priority for Phase 2 work, but the adapter health is confirmed.)

### SPORTS smoke results (2026-05-04 13:36 IST)

Sports has a different architecture than CEFI/TRADFI/DEFI — **two layers**:

1. **Primary provider** (`API_FOOTBALL`) — fetches fixtures, leagues, teams from the API; populates the canonical
   sports_reference paths in GCS.
2. **Enrichment providers** (`OPEN_METEO`, `UNDERSTAT`, `FOOTYSTATS`, `TRANSFERMARKT`, `SOCCER_FOOTBALL_INFO`) — read
   fixtures from GCS (already fetched by API_FOOTBALL), call only their own API to enrich those fixtures. They
   short-circuit the main orchestrator path.

A healthy enrichment-provider smoke = exits cleanly (rc=0) with no error, even if returns `{}` (no fixtures to enrich on
that date / those fixtures aren't in this provider's coverage).

**Valid `--sports-provider` values** (from CLI error output): `API_FOOTBALL`, `API_FOOTBALL_ENRICHMENT`, `OPEN_METEO`,
`TRANSFERMARKT`, `SOCCER_FOOTBALL_INFO`, `UNDERSTAT`, `FOOTYSTATS`. Use these exact strings.

| Provider             | Entity                | Status | Notes                                                                                                                                                         |
| -------------------- | --------------------- | :----: | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API_FOOTBALL         | FIXTURES              |   ✅   | Manifest-skip on already-captured days (correct). With `--force`: `Fetched 101 fixtures` + 1,228 leagues + 618 teams. Healthy, just slow (rate-limit pacing). |
| API_FOOTBALL         | STANDINGS             |   ✅   | Manifest-skip behavior identical. Adapter healthy.                                                                                                            |
| API_FOOTBALL         | TEAMS                 |   ✅   | Same.                                                                                                                                                         |
| TRANSFERMARKT        | PLAYER_VALUES         |  ✅¹   | Hit 90s timeout on smoke — adapter is rate-limited at ~1 req/sec, fully expected. Healthy.                                                                    |
| TRANSFERMARKT        | TRANSFERMARKT_LEAGUES |   ✅   | DONE: `{transfermarkt_leagues: 32}` — wrote 32 league rows to GCS.                                                                                            |
| FOOTYSTATS           | FS_LEAGUES            |   ✅   | Short-circuited (enrichment), exit 0, empty result for 2024-08-15. Adapter healthy.                                                                           |
| UNDERSTAT            | UNDERSTAT_TEAMS       |   ✅   | Short-circuited, exit 0, empty for 2024-08-15. Healthy.                                                                                                       |
| OPEN_METEO           | WEATHER               |   ✅   | Short-circuited, exit 0, empty for 2024-08-15. Healthy. (Initial test failed with `OPENMETEO` — correct provider name is `OPEN_METEO` with underscore.)       |
| SOCCER_FOOTBALL_INFO | SFI_LEAGUES           |   ⏭️   | **Excluded** from this run — other agent's SFI VM is in flight. Don't touch.                                                                                  |

¹ TRANSFERMARKT/PLAYER_VALUES did not finish within the 90s smoke timeout, but reached the API and was making progress.
For real backfill via the launcher (longer timeout + shutdown-on-completion) this is fine.

**6 of 6 testable sports providers healthy.** SFI excluded by design. All sports adapters can run.

## Pending work — what to launch when permissions / decisions land

### CEFI / TRADFI — local backfill failed silently, must re-fire with env vars

**Status (2026-05-04 13:10 IST)**: First run of `run_vm_backfill_e2e.sh` for cefi+tradfi failed on every chunk — the
runner doesn't export `GCP_PROJECT_ID` and the `instruments-service` CLI bootstrap aborts at `log_event("STARTED")` with
`ValueError: GCP_PROJECT_ID or AWS_ACCOUNT_ID must be set in environment`. All chunks showed "START" but no "DONE",
produced no checkpoints, and wrote nothing to GCS. **Killed and cleaned** — `.backfill-checkpoints/` and
`logs/recon-fill-*` removed so reruns start fresh.

**Re-fire command (must export env first)**:

```bash
cd ~/unified-trading-system-repos/instruments-service
export GCP_PROJECT_ID=central-element-323112
export CLOUD_PROVIDER=gcp
export CLOUD_MOCK_MODE=false

TODAY=$(date -u +%Y-%m-%d)

# CEFI — 9 venues
for venue in BINANCE-SPOT BINANCE-FUTURES DERIBIT BYBIT OKX UPBIT COINBASE HYPERLIQUID ASTER; do
  bash scripts/run_vm_backfill_e2e.sh \
    --venue "$venue" --asset-group CEFI \
    --start-date 2019-01-01 --end-date "$TODAY" \
    --chunk-days 30 --parallel 4 \
    --log-dir "logs/recon-fill-cefi-$venue" > "/tmp/backfill-cefi-$venue.log" 2>&1 &
done

# TRADFI — 6 venues
for venue in CME CBOE NASDAQ NYSE ICE FX; do
  bash scripts/run_vm_backfill_e2e.sh \
    --venue "$venue" --asset-group TRADFI \
    --start-date 2019-01-01 --end-date "$TODAY" \
    --chunk-days 30 --parallel 4 \
    --log-dir "logs/recon-fill-tradfi-$venue" > "/tmp/backfill-tradfi-$venue.log" 2>&1 &
done
wait
```

Resumable via `.backfill-checkpoints/<AG>_<venue>_<range>/`. Cumulative ~60 concurrent `instruments-service` procs.
Smoke-test one chunk first to confirm env propagates:

```bash
GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp \
  .venv/bin/instruments-service --operation instruments --mode batch \
  --asset-group CEFI --venues DERIBIT --start-date 2019-01-01 --end-date 2019-01-03
```

Expected: real progress past the bootstrap log lines (currently it dies at log_event("STARTED")).

**Follow-up bug to file**: `run_vm_backfill_e2e.sh` should export `GCP_PROJECT_ID` / `CLOUD_PROVIDER` for child
invocations, OR at minimum check that they're set before spawning chunks. Silent fail across 90 chunks per venue with no
visible error in the top-level log was a data quality risk. Tracking under `instruments-service` (no plan slug yet —
Harsh to follow up tomorrow).

### SPORTS — choose one path

**Path 1 (preferred, requires IAM grant) — VM launchers, singleton-locked:**

Ikenna runs as project owner:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  1060025368044-compute@developer.gserviceaccount.com \
  --member="user:harshkantariya@odum-research.com" \
  --role="roles/iam.serviceAccountUser" \
  --project=central-element-323112
```

Then fire:

```bash
bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh 2020-06-01 2026-05-04
bash deployment-service/scripts/vm/launch-transfermarkt-backfill-vm.sh 2020-06-01 2026-05-04
# (sfi excluded — other agent's VM in flight)
# Optional, if recon shows phantoms in their data types:
bash deployment-service/scripts/vm/launch-footystats-backfill-vm.sh 2020-06-01 2026-05-04
bash deployment-service/scripts/vm/launch-understat-backfill-vm.sh 2020-06-01 2026-05-04
bash deployment-service/scripts/vm/launch-openmeteo-backfill-vm.sh 2020-06-01 2026-05-04
```

Singleton-lock prevents thundering herd against shared API keys. **This is the canonical path** per the playbook — same
pattern your teammate's existing 31 VMs use.

**Path 2 (fallback, no IAM grant needed) — local CLI, manually paced:**

If the IAM grant doesn't land in time, run sports adapters locally one-at-a-time:

```bash
cd ~/unified-trading-system-repos/instruments-service
export GCP_PROJECT_ID=central-element-323112
export CLOUD_PROVIDER=gcp

# api-football — sequential per entity to mimic the singleton lock behavior
for entity in FIXTURES STANDINGS INJURIES PLAYER_STATS FIXTURE_LINEUPS FIXTURE_STATS FIXTURE_EVENTS TEAMS LEAGUES; do
  .venv/bin/python -m instruments_service \
    --operation instruments --mode batch \
    --asset-group SPORTS --sports-provider API_FOOTBALL --sports-entity $entity \
    --start-date 2020-06-01 --end-date 2026-05-04 \
    > /tmp/sports-af-$entity.log 2>&1
done

# transfermarkt — PLAYER_VALUES is the big one (8,647 phantoms)
for entity in PLAYER_VALUES TRANSFERMARKT_LEAGUES TEAM_SQUAD; do
  .venv/bin/python -m instruments_service \
    --operation instruments --mode batch \
    --asset-group SPORTS --sports-provider TRANSFERMARKT --sports-entity $entity \
    --start-date 2020-06-01 --end-date 2026-05-04 \
    > /tmp/sports-tm-$entity.log 2>&1
done
```

⚠️ **Caveat**: this bypasses the singleton lock. If another sports VM (or your teammate's SFI VM) is hitting the same
shared API key, you'll thrash. Before firing Path 2 confirm
`gcloud compute instances list --filter='name~"^(af|tm|fs|understat|openmeteo)-"'` is empty.

### PREDICTION — out of scope

Phase 0 dry-run found 11,848 phantoms but they're all on POLYMARKET / `trades` data type. That's MTDS data
(market-tick), not `instruments-service` reference data. Either the prediction manifest is conflating MTDS writes with
instruments writes, or the writers are mis-attributing the asset group. **Flag for Ikenna separately**, do not flip in
this plan.

### DEFI — optional cleanup

597 phantoms, all on EIGENLAYER / `rewards`. Not core instruments data. Two choices:

- Skip (0.2% of defi manifest, won't move the headline percentage).
- Flip with `reconcile_phantom_manifest_rows_all.py --asset-group defi` (~5 min, no backfill needed, just clears the
  phantoms so the headline is honest).

## Verification after backfills complete

For each AG:

```bash
cd ~/unified-trading-system-repos/instruments-service
.venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py --asset-group <ag> --dry-run
```

Expected: "No phantoms found. Manifest is clean." If non-zero, the orchestrator's `_should_skip_shard` skipped some
shards as `attempted_failed` → `attempted_failed` (real failure, not phantom). Check the new `error_reason` distribution
to decide whether to retry, fix the adapter, or accept as legitimate API failure.

## Risks / blockers

- **SFI VM in flight**: while the single SFI instruments VM is running, do NOT touch `SFI_LEAGUES` /
  `SFI_PROGRESSIVE_STATS` data types in either reconciler or launcher invocations. Reading the manifest mid-write is OK
  (atomic GCS object), but flipping rows the VM is about to write would race.
- **Cefi/tradfi/defi/prediction instruments have no dedicated VM launcher.** Default path is `run_vm_backfill_e2e.sh`
  running locally on this machine — IP-rate-limited by the laptop's egress. For instruments-service this is fine (low
  API volume); if a particular venue's daily fetch is slow, Path B (wrap in a VM) is the upgrade. Defer to Ikenna before
  introducing a new VM-launcher pattern.
- **Wall-clock**: realistic only after Phase 0 dry-run reveals gap size. Instruments-service shards are tiny (one daily
  JSON pull per venue), so even thousands of red shards can finish in hours via `run_vm_backfill_e2e.sh --parallel 4`.
  Tick-data scale doesn't apply.
- **API rate limits**: singleton-locked launchers (`launch-sfi-forward-poll.sh` etc.) refuse duplicates by design. Don't
  bypass with `--force` without explicit reason. Use `--parallel 2` instead of `--parallel 4` for prediction venues
  (POLYMARKET / KALSHI rate-limit harder than crypto exchanges).
- **Scope ambiguity**: the (1) vs (2) "100%" question above. Resolve before EOD push.

## Out of scope (for _this_ plan — covered by parent epic)

- deployment-ui Phase 0 bug fixes (CSV download, day-shard scroll, schema modal, market-tick
  - market-data-processing unified view).
- market-tick-data-service backfills (parent-epic Phase 2/3/4/5).
- market-data-processing-service candle generation (parent-epic Phase 2).
- VIX futures full-tick chain (parent-epic Phase 3, P2 deferred).
- mbp_10 deep-book for tradfi (parent-epic Phase 3, P2 deferred).

## Notes — Phase 0 dry-run results (2026-05-04 12:33–12:45 IST)

| Asset group | Manifest rows | Captured-in-scope | Real captured |   Phantoms | % phantom | Top concentration                                                                                                                                                                                     |
| ----------- | ------------: | ----------------: | ------------: | ---------: | --------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| cefi        |     1,343,892 |           188,684 |       176,144 | **12,540** |      6.6% | DERIBIT 3,070; BYBIT 1,834; BINANCE-FUTURES 1,763; OKX-SWAP 1,740; UPBIT 1,352. By data_type: empty=9,757 (schema-4 legacy rows), `trades` 2,501                                                      |
| tradfi      |        32,345 |            26,594 |        23,866 |  **2,728** |       10% | CBOE 657; ICE 379; CME 373; NASDAQ/NYSE 368 each; FX 330. By data*type: empty=2,472 (schema-4), `ohlcv*\*`+`trades`+`tbbo` <70 each                                                                   |
| sports      |     2,401,547 |           758,465 |       717,242 | **41,223** |      5.4% | STANDINGS 13,022; INJURIES 9,872; PLAYER*VALUES 8,647; PLAYER_STATS 3,057; FIXTURE*{LINEUPS,STATS} ~2.7k each. SFI excluded (other agent's VM). All venue=`""` (sports keys on league_id, not venue). |
| prediction  |        14,369 |            14,328 |         2,480 | **11,848** |       83% | POLYMARKET / `trades` 11,831 of 11,848. Almost all phantom — but `trades` is MTDS data, not strict instruments-service                                                                                |
| defi        |       307,341 |           307,341 |       306,744 |    **597** |      0.2% | EIGENLAYER / `rewards` (all 597). Effectively clean for instruments.                                                                                                                                  |

### Read of the data

- **cefi**: 12,540 phantoms is real work but tractable — they're spread across the 9 active venues and the 9,757
  empty-data_type rows are likely schema-4 legacy that need the same flip-to-`attempted_failed` treatment. Once flipped,
  the orchestrator will retry. Reasonable target for EOD.
- **tradfi**: 2,728 phantoms, similar shape to cefi. The 2,472 empty-data_type rows are again schema-4 legacy. Should be
  quick.
- **prediction**: 83% phantom rate is alarming but **the data_type is `trades`** — that's market-tick (MTDS) territory,
  not `instruments-service` reference data. Almost certainly the prediction manifest is conflating MTDS writes with
  instruments writes. **Out of scope for this plan**, flag for Ikenna separately.
- **defi**: essentially clean. The 597 EIGENLAYER `rewards` phantoms aren't core instruments either. Could leave as-is
  or flip in 2 seconds.
- **sports**: still running, will refresh when it completes.

### Decisions

| AG         | Phase 1 (flip)?                      | Phase 2 (launch)? | Notes                                                                                                     |
| ---------- | ------------------------------------ | ----------------- | --------------------------------------------------------------------------------------------------------- |
| cefi       | YES — 12,540 phantoms                | YES — after flip  | Use `run_vm_backfill_e2e.sh` per venue                                                                    |
| tradfi     | YES — 2,728 phantoms                 | YES — after flip  | Same pattern                                                                                              |
| sports     | YES — 41,223 phantoms (SFI excluded) | YES — after flip  | Use `launch-{api-football,transfermarkt}-backfill-vm.sh` for affected data types. SFI launchers stay off. |
| prediction | NO                                   | NO                | Out of plan scope; `trades` rows are MTDS not instruments. Flag for Ikenna.                               |
| defi       | OPTIONAL — 597 phantoms              | NO                | EIGENLAYER `rewards` only, not strict instruments. Skip or flip-and-leave.                                |

---

## Phase 2 execution — VM fanout (2026-05-04 18:11 IST onwards)

### What landed before fanout

1. **Pulled 3 incoming commits on `live-defi-rollout` (instruments-service)**:
   - `e077b35` phantom-audit: probe legacy `venue=PROTOCOL-CHAIN/` overload for DeFi rows (597 EIGENLAYER
     false-positives → 0)
   - `faf5466` Tardis URDI: use full 50+ fiat quote-currency set (BTC-TRY/BRL/AUD/AED/SAR/IDR no longer collapse to
     BTC-USD on OKX-SPOT) + phantom audit 5-axis hardening (130,897 → 354 phantoms, 99.7% reduction)
   - `2c207e2` chore: drop unused noqa marker
2. **Pulled 4 incoming commits on `live-defi-rollout` (unified-trading-pm)**:
   - `4c718ac` codex doc availability-manifest-and-data-status v4 → v6
   - `1bd189b` workspace-manifest formatting drift
   - `65f67e0` phantom audit 5-axis docs + re-runnable VM recipe
   - `ada3367` cursor-configs/CLAUDE.md mirror
3. **Rebuilt CEFI tarballs** (`bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group CEFI`) — UTC
   12:28:24, includes the Tardis fiat-quote fix.

### New launcher script created

- **`deployment-service/scripts/vm/launch-cefi-instruments-backfill.sh`** (new file, modeled after
  `launch-cefi-forward-poll.sh`).
  - Targets `instruments_service` (not MTDS). Sets `VM_SERVICE=instruments_service`, `VM_OPERATION=download`,
    `VM_TASK=cefi-instruments-backfill`.
  - **NO `IS_TEST_RUN`** → writes to production buckets.
  - Per-VM shard isolation already handled by `setup-data-pipeline-vm.sh` (line 358 exports
    `MANIFEST_PER_VM_SHARDS=true` by default; line 390/445 sets `VM_NAME` to GCE instance name).
  - Singleton-lock on `^cefi-instr-` prefix; `--force` bypass for multi-venue fanout.
  - Singleton-lock `--force` is **separate** from instruments-service CLI `--force`. The launcher's `--force` only
    allows multiple VMs of the same prefix to run; it does NOT pass `VM_FORCE=true` metadata, so the python CLI runs
    without `--force` and pre-flight skip works as intended (CAPTURED shards are skipped).

### Smoke test before fanout

- Smoke VM `cefi-instr-binance-spot-20260504-175849` for BINANCE-SPOT 2026-05-02:
  - 12:28:51 UTC: VM created
  - 12:32:29 UTC: setup script complete (~4 min boot)
  - 12:32:57 UTC: data parquet (24,229 bytes) + per-VM shard (13,596 bytes, schema_v6, instrument_count=48
    [intentionally filtered], capture_status=captured) both written
  - 12:36:27 UTC: consolidator merged per-VM shard into canonical (cycle interval ~6 min for instruments-store-cefi
    bucket)
  - 12:36:27 UTC: canonical row written:
    `{date: 2026-05-02, venue: BINANCE-SPOT, instrument_count: 48, schema_version: 6, capture_status: captured, expected: True, available: True}`
  - **End-to-end pipeline verified**: VM boot → fetch → per-VM shard → consolidator merge → canonical updated.

### Phase 2a: 14 CEFI VMs launched (all RUNNING, asia-northeast1-c)

Window: **2018-01-01 → 2026-05-04** (full history). Pre-flight skip ensures CAPTURED dates are not re-fetched.

| Venue           | VM name                                      |
| --------------- | -------------------------------------------- |
| ASTER           | `cefi-instr-aster-20260504-181140`           |
| BINANCE-FUTURES | `cefi-instr-binance-futures-20260504-181152` |
| BINANCE-SPOT    | `cefi-instr-binance-spot-20260504-181202`    |
| BITFINEX-SPOT   | `cefi-instr-bitfinex-spot-20260504-181215`   |
| BITGET-FUTURES  | `cefi-instr-bitget-futures-20260504-181226`  |
| BITGET-SPOT     | `cefi-instr-bitget-spot-20260504-181238`     |
| BYBIT           | `cefi-instr-bybit-20260504-181250`           |
| COINBASE-SPOT   | `cefi-instr-coinbase-spot-20260504-181302`   |
| DERIBIT         | `cefi-instr-deribit-20260504-181316`         |
| HYPERLIQUID     | `cefi-instr-hyperliquid-20260504-181333`     |
| OKX-FUTURES     | `cefi-instr-okx-futures-20260504-181350`     |
| OKX-SPOT        | `cefi-instr-okx-spot-20260504-181426`        |
| OKX-SWAP        | `cefi-instr-okx-swap-20260504-181441`        |
| UPBIT           | `cefi-instr-upbit-20260504-181458`           |

Expected per-venue runtime: ~5–10 min for low-gap venues; **BITFINEX-SPOT (~2,315 missing dates)** and
**BITGET-SPOT/FUTURES (~542 each)** will run hours.

### Phase 2b: 4 SPORTS VMs launched (all RUNNING)

Each sports launcher enforces its own singleton-lock per shared API key.

| Provider                   | VM name                        | Range                   |
| -------------------------- | ------------------------------ | ----------------------- |
| api_football               | `af-backfill-20260504-181544`  | 2018-01-01 → 2026-05-04 |
| footystats                 | `fs-backfill-20260504-181600`  | 2019-01-01 → 2026-05-04 |
| understat                  | `us-backfill-20260504-181616`  | 2015-01-16 → 2026-05-04 |
| sfi (soccer_football_info) | `sfi-backfill-20260504-181631` | 2019-01-01 → 2026-05-04 |

Note: **transfermarkt** intentionally not launched (its launcher `launch-transfermarkt-backfill-vm.sh` doesn't exist in
this repo — only `launch-tradfi-backfill-vm.sh` and the four sports providers above). May need to revisit.

### Bystander VMs (someone else launched)

Spotted at 12:45:08 UTC: `instr-bitfinex-futures-20260504-134505` — likely Ikenna or another agent. Distinct prefix, not
interfering.

### Total fleet

**18 launches today** (14 CEFI + 4 SPORTS). All `asia-northeast1-c`.

### What to watch / acceptance criteria

1. **Per-VM shards appear in `_index/per_vm/`** (each VM writes its own; existence proves VM made it through bootstrap +
   first capture)
2. **Consolidator merges into canonical**: instruments-store-cefi bucket merge cycle is ~6 min; sports buckets vary
   (footystats much heavier — could be 60–90s per cycle).
3. **`_index/availability_index.parquet` row count grows** for both CEFI and SPORTS canonicals.
4. **Coverage % climbs** in deployment-ui Data Status tab.
5. **VMs auto-shutdown** when their range completes (`VM_SHUTDOWN_ON_COMPLETION=true` on launcher metadata for
   cefi-instr-\*; sports launchers handle their own shutdown).

### Known issues to revisit

- **Manifest clobber from rebuild\_\*\_manifest.py** earlier today (~50–100 CEFI rows lost in the 11:54 UTC consolidator
  merge that pulled stale snapshot before our rebuild's per-VM shard arrived). Recoverable from GCS generation
  `1777895583506752` (CEFI) and `1777895614776416` (TRADFI). NOT yet restored — the running fleet will recapture most of
  those gaps naturally.
- **DERIBIT memory leak** identified earlier (~570 MB/day chunk growth, smoke profiler showed bootstrap alone eats 2
  GB). Workaround: chunk-cycling in `run_vm_backfill_e2e.sh`. The VM workers each handle one venue → bounded RAM, so
  this should not bite the running fleet.
- **deployment-api turbo endpoint per-venue numbers were unreliable** at full-history scale (returning 0 for every
  venue). Use `deploy-missing` POST endpoint as ground truth.

### Tomorrow / continuation

- **TRADFI**: ~3,683 missing shards (~9 venues, ~400/year). Use new launcher pattern, 1 VM per venue, 2018-01-01 →
  today.
- **DEFI**: 307k canonical rows but EIGENLAYER restaking `rewards` (597 rows) is the only meaningful gap. Out of scope
  for this plan as MTDS-territory.
- **PREDICTION**: 14k rows with 83% phantom rate but data_type is `trades` (MTDS, not instruments-service). Out of plan
  scope.

---

## Phase 2 corrections after reading handoff doc + backfill playbook (18:21 IST)

After Harsh shared the handoff doc and I followed the references, found 4 things I should have done differently. **Do
not repeat these in tomorrow's launches.**

### Corrections applied

1. **Added 2 missing sports VMs.** Playbook line 287 lists 6 sports launchers, I'd only launched 4. Added:
   - `tm-backfill-20260504-182121` (transfermarkt) — range 2020-06-01 → 2026-05-04
   - `weather-backfill-20260504-182144` (openmeteo) — range 2020-06-01 → 2026-05-04
   - **New total: 14 CEFI + 6 SPORTS = 20 VMs**

### Things I got wrong but didn't fix (low risk, just wasteful)

2. **CEFI start date was 2018-01-01, playbook says 2019-01-01.** Pre-2019 dates have no Tardis coverage, so the
   orchestrator returns empty for them. Pre-flight skip means it's not catastrophic — just adds wasted attempts on the
   VM. Don't re-launch; let them run.

3. **Sports start dates per launcher defaults** (2018-01-01 for api_football, 2019-01-01 for footystats, etc.) are too
   early. Playbook says **sports cutoff is 2020-06-01** (because odds_api data only starts 2020-06-06 and pre-odds data
   has no trading value). Same wastage situation — don't re-launch. The 2 new VMs (tm, weather) used the correct
   2020-06-01 start.

### Important gotchas from the playbook (must monitor)

4. **Concurrent VM boot race on deadsnakes PPA.** Playbook line 207-209: "~3 of N parallel VMs hang at python3.13
   install. Mitigation: kill the hung VMs and relaunch one-at-a-time, or stagger boots ≥30s apart." I launched 14 CEFI
   VMs at once (~12s spacing). **As of 18:21 IST, all 14 still in bootstrap (no run.log yet) — within normal range, but
   if any are still pre-log past T+8min from launch, those are likely PPA-hung.** Diagnose:
   `gcloud compute ssh <vm> --command='ps aux | grep python3.13'`.

5. **CeFi VM `rc=137` (OOM) does NOT write `EXIT_STATUS`.** `atexit` doesn't fire on `SIGKILL`. Symptom: VM ends, no
   EXIT_STATUS in run.log, manifest empty for half-completed shard. **BITFINEX-SPOT (~2,315 dates), BITGET-SPOT/FUTURES
   (~542 each)** are the OOM risks. Diagnose via `dmesg | grep -i kill` on the VM (if alive) or Cloud Logging
   `kernel: ... oom`. Mitigation: bump machine type or shard year-by-year.

6. **Tarball pins to local pyproject.toml floors via `--no-sources -e <local-dir>`.** VM-deployed services don't see
   version floors of dependent repos. Cloud Run jobs (consolidator, defi-collection, deployment-api) use the MTDS Docker
   image and need a Docker rebuild after a UTL change, NOT a tarball refresh.

### What the playbook says about priority order — re-evaluate tomorrow

The playbook lists sports priority by data_type completion %, not by source. Worst-covered first:

1. **FIXTURE_FEATURES (0%)** — never captured. P0.
2. **PLAYER_VALUES (2%)** — Transfermarkt; per-player. P0.
3. **SFI_LEAGUES (14%)** — soccer_football_info reference. P0.
4. **SFI_PROGRESSIVE_STATS (15%)** — 2020-01-01 cutoff. P1.
5. **MATCHES (18%)** — API_FOOTBALL match endpoint. P0.
6. **TRANSFERMARKT_LEAGUES (50%)** — P1.
7. **PLAYER_STATS (78%)** — P2 gap-fill.

My current sports VM launches are PROVIDER-level (one VM per provider, all data_types). The playbook implies we should
be running DATA_TYPE-level VMs to chase the worst-covered first. The launchers DO have `--entity` filters for this.
**Tomorrow:** use `--entity FIXTURE_FEATURES`, `--entity PLAYER_VALUES`, `--entity SFI_LEAGUES` etc. for targeted
backfill.

### Architectural learnings

7. **Reference-vs-prediction league filter.** For non-prediction leagues (40 reference leagues), only attempt FIXTURES +
   FIXTURE*EVENTS + STANDINGS. Don't push for FIXTURE_FEATURES / PLAYER_VALUES / SFI*\* / understat — those endpoints
   expect prediction-level depth (33 prediction leagues). My current launches don't apply this filter; orchestrator
   should handle it via existing per-league logic, but worth verifying in the run.log.

8. **DeFi uses different CLI** — `collect-evm-defi` / `collect-dex-swaps`, NOT `--operation download`. So
   `launch-cefi-instruments-backfill.sh` cannot be reused for DeFi. Need a separate launcher pattern for DeFi tomorrow.

9. **TradFi is mostly complete already** per `project_tradfi_backfill_session_2026_04_30.md` memory. Outstanding only:
   VIX futures full-tick chain (separate plan), MBP_10 deep book (if microstructure strategy needs). Tomorrow's TradFi
   work is mostly verification, not fanout.

10. **Bystander VM `instr-bitfinex-futures-20260504-134505`** spotted earlier — this might be Ikenna catching what the
    playbook lists at "MVP CeFi → top assets on … BYBIT, HYPERLIQUID; Deribit options combos". BITFINEX-FUTURES wasn't
    in my fanout (not in the 14-venue list — probably should have been). Tomorrow: cross-check the venue list against
    UAC `_CEFI_VENUES`.

### Verification command set (run periodically)

```bash
# Fleet status
gcloud compute instances list --filter="(name~'^cefi-instr-' OR name~'^(af|fs|us|sfi|tm|weather)-backfill') AND status=RUNNING" --project=central-element-323112 --format="table(name,status,zone)"

# Per-VM shards landing in GCS (= VMs writing manifest entries)
gsutil ls -l gs://instruments-store-cefi-central-element-323112/_index/per_vm/ | tail -20
gsutil ls -l gs://instruments-store-sports-central-element-323112/_index/per_vm/ | tail -20

# Consolidator catching up (cycle ~6 min for instruments-store-cefi)
gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/manifest-consolidator-20260429-162442/run.log | grep "instruments-store-cefi" | tail -3

# Coverage delta vs morning baseline
curl -s "http://localhost:8004/api/data-status/turbo?service=instruments-service&start_date=2019-01-01&end_date=2026-05-04&asset_group=CEFI" | python3 -c "import sys,json; r=json.load(sys.stdin); print('CEFI completion=', r.get('overall_completion_pct'), 'shards=', r.get('overall_shards_found'),'/',r.get('overall_shards_expected'))"
```

---

## Day 2 (2026-05-05) — CEFI mixed range+list fanout to close remaining 2,672 gaps

**Scope: CEFI venues only (instruments-service).** DERIBIT excluded per user (memory leak fixed in tardis.py override
but not yet validated for multi-day historical sweep — will be tackled via VM with bigger machine separately).

### Why a mixed approach

Yesterday's pure date-list fanout (117 pairs) worked great because each venue had only a few scattered dates. Today's
gap is dominated by BITFINEX-FUTURES which needs 2,315 dates from 2020-01-01 → 2026-05-03 (full history since Tardis
archive coverage).

If we ran 2,315 single-day processes, each spends ~50s on service bootstrap and ~4s on the actual fetch. **92% of
wall-clock would be wasted on bootstrap.** ~90 min total.

Fix: range-launch venues whose missing dates are contiguous (one process amortizes bootstrap across all dates),
date-list-launch venues whose missing dates are scattered (no benefit to range since most of the range would be a no-op
skip).

### Per-venue strategy decision

| Venue            | Missing    | Pattern                                                                    | Strategy                                                                                                                   |
| ---------------- | ---------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| BINANCE-FUTURES  | 70         | 1 contiguous range 2019-09-08 → 2019-11-16 (pre-Tardis-launch — all skips) | range                                                                                                                      |
| BITFINEX-FUTURES | 2,315      | 1 contiguous range 2020-01-01 → 2026-05-03                                 | range, **chunked** into yearly windows for parallelism                                                                     |
| UPBIT            | 2          | 1 short range 2021-03-01 → 2021-03-02                                      | range                                                                                                                      |
| BITFINEX-SPOT    | 176        | 130 scattered ranges                                                       | list                                                                                                                       |
| BITGET-FUTURES   | 53         | 42 scattered ranges                                                        | list                                                                                                                       |
| BITGET-SPOT      | 56         | 34 scattered ranges                                                        | list                                                                                                                       |
| **DERIBIT**      | (excluded) | n/a                                                                        | **skipped today** — will run separately on bigger VM after validating the cache-key fix from `instruments-service@9d91465` |

### Launch script

`/tmp/launch-cefi-mixed.sh` (regenerable from this plan):

- 9 range processes in parallel:
  - BINANCE-FUTURES 2019-09-08 → 2019-11-16
  - UPBIT 2021-03-01 → 2021-03-02
  - BITFINEX-FUTURES × 7 yearly chunks (2020, 2021, 2022, 2023, 2024, 2025, 2026-Jan→May-3)
- 1 date-list fanout (`local_fill_pairs.sh`, PARALLEL=8) over `/tmp/cefi-scattered.txt` (285 pairs across
  BITFINEX-SPOT + BITGET-FUTURES + BITGET-SPOT)
- Total ~17-19 concurrent workers, capped well under Tardis API budget.

Pairs files at:

- `/tmp/cefi-all-missing-pairs.txt` (full 2,672 list, source of truth)
- `/tmp/cefi-scattered.txt` (285 list-only pairs)

### Expected timing

- Yearly BITFINEX-FUTURES chunk: 50s bootstrap + 365 × 4s = ~25 min per chunk
- 7 chunks parallel = **~25 min wallclock for full 2020-2026 BITFINEX-FUTURES**
- Range chunks (BINANCE-FUTURES, UPBIT) finish in 1-2 min (mostly pre-launch skips / 2 dates)
- Scattered list at 8 parallel × 54s/pair = ~5 min for 285 scattered pairs

Total wallclock target: **~25 min** (dominated by BITFINEX-FUTURES yearly chunks).

### Pre-launch state (2026-05-05)

- CEFI canonical: 25,332 / 27,954 = 90.62% (full-history window 2019-01-01 → 2026-05-03)
- UI: 90.6% with BITFINEX-FUTURES at 0% being the biggest visible gap
- Yesterday's 117-pair fanout already pushed CEFI 30-day window 63.66% → 88.82%
- Validation regression for OKX-SPOT/FUTURES/SWAP, COINBASE-SPOT was fixed in `unified-api-contracts@41df720`
  (push-merged)

### Post-launch verification

After the mixed fanout completes, verify:

1. Canonical row counts grew per venue:
   ```bash
   GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp CLOUD_MOCK_MODE=false python3 -c "
   import io, pandas as pd; from google.cloud import storage
   c = storage.Client(project='central-element-323112').bucket('instruments-store-cefi-central-element-323112').blob('_index/availability_index.parquet')
   df = pd.read_parquet(io.BytesIO(c.download_as_bytes()))
   print(df.groupby('venue').size().sort_values(ascending=False))
   "
   ```
2. Coverage % climbed in deployment-api (clear cache first):
   ```bash
   curl -s -X POST http://localhost:8004/api/data-status/turbo/clear
   curl -s "http://localhost:8004/api/data-status/turbo?service=instruments-service&start_date=2018-01-01&end_date=2026-05-03&asset_group=CEFI" | python3 -c "import sys,json; r=json.load(sys.stdin); print(f'CEFI: {r.get(\"overall_completion_pct\")}% ({r.get(\"overall_shards_found\")}/{r.get(\"overall_shards_expected\")})')"
   ```
3. Zero failures in summary log:
   ```bash
   LOG_DIR=$(ls -td /tmp/cefi-mixed-* | head -1); grep -c FAIL "$LOG_DIR/summary.log"
   ```

### Lessons documented

- **Bootstrap overhead matters at scale.** 50s/process is fine for 100 pairs (8 min total) but lethal for 2,000+ pairs
  (~90 min). Always check pair count before deciding range vs list.
- **"Range" doesn't mean one process per venue's full history** — chunk by year (or quarter for venues with very dense
  data) to parallelize the long-running ones. 7 chunks × 25 min = 25 min wall vs 1 chunk × 175 min = 175 min wall.
- **Date-list still wins when dates are scattered** because pre-flight skip across a 6-year range to find 50 missing
  days wastes per-date GCS round-trips.

---

## Day 2 (2026-05-05) — Sports VM triage + SFI throttle fix

### Sports VMs running 2026-05-04→05 — what each is doing

While CEFI mixed fanout was running locally, four sports VMs were left running from 2026-05-04. Triage:

| VM                             | Provider             | Behavior observed                                                                                                               | Action                                                                  |
| ------------------------------ | -------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `af-backfill-20260504-232814`  | api_football         | Captures real fixtures per-date (~30s/date). Will hit daily rate limit.                                                         | Leave running.                                                          |
| `sfi-backfill-20260504-183611` | soccer_football_info | **429-thrashing** every minute. ~5 successful fetches per 7-min window.                                                         | **Killed; relaunched with throttle fix.**                               |
| `tm-backfill-20260504-183629`  | transfermarkt        | Sequential ~30s/league × 33 leagues × N seasons. RapidAPI upstream slow.                                                        | Leave running. Future: parallelize with `asyncio.gather(Semaphore(4))`. |
| `us-backfill-20260504-232831`  | understat            | **Already 100% captured.** VM was iterating dates in a manifest pre-flight loop, ~7s/date × 4,124 days = 8 hours of pure noise. | **Killed.** No relaunch needed.                                         |

### SFI rate-limit fix — `instruments-service@04bc1bc`

**Problem.** `BaseSportsReferenceAdapter._MIN_REQUEST_INTERVAL = 0.1` was a module-level constant tuned for api_football
Ultra (~900 req/min). SFI plan is RapidAPI Ultra @ **4 req/sec** (provider dashboard screenshot 2026-05-05; 99,999/day).
At 0.1s the SFI worker bursts up to 10 req/sec for a few seconds, hits the per-second cap, then 429-thrashes the rest of
the minute.

**Fix.** Convert the throttle to a per-class attribute on `BaseSportsReferenceAdapter`:

- `_min_request_interval: float = _MIN_REQUEST_INTERVAL` (default 0.1s — base class)
- `_throttle()` reads `type(self)._min_request_interval` so subclasses can override
- `_last_request_time` is now `type(self)._last_request_time` so each adapter paces independently

`SoccerFootballInfoAdapter._min_request_interval = 0.34` → ~3 req/sec, safely under the 4 req/sec cap.

Other adapters (api_football, footystats, transfermarkt, understat, open_meteo) keep the base default — none have
evidence of a tighter per-second cap today.

**Files changed (instruments-service):**

- `instruments_service/reference_data/adapters/sports/adapters/base.py` — class attribute + `_throttle` uses
  `type(self)`
- `instruments_service/reference_data/adapters/sports/adapters/soccerfootball_info.py` — override + docstring

**Deployment:**

- Pushed `instruments-service@04bc1bc` to `live-defi-rollout`
- Refreshed SPORTS tarball: `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS`
- Killed old SFI VM, launched new: `sfi-backfill-20260505-120759` (range 2020-06-01..2026-05-04, single-VM mode)

**Validation criteria.** After ~5 min the new VM's `run.log` should show:

- Steady ~3 req/sec sustained, no `Rate limited (429)` lines
- ~180 successful fetches per minute (vs ~14 measured pre-fix)
- ~12× throughput improvement → 6.3-year backfill (~2,300 dates) wall-time drops from ~68 days single-VM to ~5–6 days

```bash
gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/sfi-backfill-20260505-120759/run.log | grep -cE 'Rate limited|429'  # expect 0
gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/sfi-backfill-20260505-120759/run.log | grep -cE 'wrote [0-9]+ records'  # should grow steadily
```

### Understat — no relaunch needed

Understat XG = 100.0% complete (verified via `/api/data-status/turbo`). The "skipping date — all 5 expected leagues
per-league captured" log is the system working correctly; the slow part is a `ManifestReader` per-VM shard fallback when
the consolidated blob is stale. Cost-benefit: not worth optimizing for an already-complete dataset.

If a gap _does_ re-appear, the right fix is in `instruments-service/instruments_service/engine/orchestrator.py` near
line 4426 — add a per-(league, season) pre-flight cache so the per-date dispatch short-circuits at O(unique seasons)
instead of O(days × leagues). Do NOT add a standalone `local_understat_full_backfill.py` script (violates "System-First
Architecture").

### Transfermarkt — leave running, future optimization

- Provider: `transfermarkt-football-data-api.p.rapidapi.com` (NOT scraping)
- Two endpoints per league: `/competitions/standings` + `/clubs/profile` (1 + N×club calls)
- Per-league wall-time: ~25-40s, dominated by RapidAPI upstream latency (the API itself scrapes Transfermarkt.com)
- No bulk endpoint exists
- Rate limit: shared base default (0.1s) — no documented per-second cap

**Future optimization** (not blocking today): wrap the orchestrator's per-league loop in `asyncio.gather(Semaphore(4))`.
The base throttle still serializes underlying HTTP, so this hides upstream latency rather than stacking req/sec.
Estimated 4× wall-time speedup. File: `instruments-service/instruments_service/engine/orchestrator.py:4740-4804`.

---

## Day 2 (2026-05-05) — PREDICTION (Polymarket) cursor-sharding fix

### The problem

PREDICTION coverage stuck at **89.05%** (2,821/3,168 shards). 137 unique dates missing across 12 data_types (DJIA, NDX,
SPX, SOL, GOLD, SILVER, XRP, CRUDE_OIL, FOOTBALL, DOGE, BNB, ETH).

Initial fanout (2026-05-05 13:30 UTC, PARALLEL=10) hit hard wall:

- 0 successful completions in 14 min
- 3 timeout-FAILs (each ~10 min wallclock, 0 records written)
- Aborted; killed remaining workers cleanly

**Root cause:** Polymarket CLOB API has no per-date filter. Adapter scans up to 1000 pages × 1000 markets each (~860K
markets total) for EVERY date, filtering client-side by `end_date_iso`. At PARALLEL=10 from one IP (shared NAT egress)
the API silently times out individual requests around page 200-500. Not a 429 issue (zero observed) — request-level
timeouts in deep pagination.

### The cursor-sharding solution

CLOB cursors are base64-encoded ASCII offsets:

- `cursor=""` → page 0 (offset 0)
- `next_cursor=MTAwMDAw` → offset 100,000 (decoded: "100000")
- Verified via direct probe 2026-05-05 13:38 UTC

Probing every 25K offset shows CLOB is **roughly chronologically sorted** by `end_date_iso` (oldest first), with some
inversions at month boundaries:

| Cursor offset | end_date_iso |
| ------------- | ------------ |
| 0             | 2023-03-15   |
| 50K           | 2025-05-18   |
| 100K          | 2025-09-24   |
| 200K          | 2026-01-13   |
| 400K          | 2026-02-09   |
| 600K          | 2026-03-15   |
| 800K          | 2026-04-08   |
| 870K          | 2026-05-12   |

This means each missing date can be assigned a **narrow cursor band** (~100-250 pages) instead of scanning all 1000.

### Adapter patch — instruments-service@<pending push>

Backward-compatible env-var control added to `_fetch_clob_markets` in
`instruments-service/instruments_service/reference_data/adapters/prediction/polymarket.py`:

- `POLYMARKET_START_CURSOR` — base64-encoded offset to start at (defaults `""` = page 0)
- `POLYMARKET_END_CURSOR` — base64-encoded offset to stop at (defaults unset = full scan to natural EOF)

If unset, behavior is identical to legacy. If set, worker scans only the requested cursor slice. Live mode (no `date`
param) uses Gamma API and is unaffected.

**Smoke test (2026-05-05 13:53 UTC):**

- date=2026-04-08, cursor slice 800,000..810,000 (10 pages)
- Result: 3,584 records written in **18 seconds** (vs 10-15 min full-scan)
- ~50× speedup, zero timeouts

### Cursor band assignments per (year, month)

| Year-Month         | Cursor band | Pages  |
| ------------------ | ----------- | ------ |
| 2025-03 to 2025-04 | 0..130,000  | 130    |
| 2025-05 to 2025-06 | 40K..140K   | 90-100 |
| 2025-07 to 2025-09 | 90K..200K   | 110    |
| 2025-10            | 110K..220K  | 110    |
| 2025-11            | 140K..250K  | 110    |
| 2025-12            | 170K..330K  | 160    |
| 2026-01            | 180K..380K  | 200    |
| 2026-02            | 300K..500K  | 200    |
| 2026-03            | 450K..700K  | 250    |
| 2026-04 to 2026-05 | 650K..880K  | 230    |

Bands have **deliberate overlap and ±50K padding** to absorb CLOB inversions. Overshoot is cheap (extra pages = a few
seconds), missing data is not.

### Runner design (this doc)

- Per-date workers, max **PARALLEL=5** (gentle on Polymarket per-IP rate limit)
- Each worker:
  `POLYMARKET_START_CURSOR=<band_start> POLYMARKET_END_CURSOR=<band_end> instruments-service --venues POLYMARKET --start-date X --end-date X`
- Per-VM shard isolation: unique `VM_NAME=local_predict_{date}_{rand}`
- Working **backward from newest** (per user request 2026-05-05) — most missing dates are recent
- Estimated wallclock: ~1.5-2 hr for all 137 dates

### Open follow-up for Ikenna

If this pattern works, the longer-term improvement is to make the orchestrator **batch missing-date queries by cursor
band** so one process scan fills many dates simultaneously. Today's adapter still does one scan per date — even with
narrow slices, that's 137 process bootstraps. A cursor-sweep mode that fills any (date, data_type) shard whose target
falls within the scanned window would reduce 137 process invocations to ~10.

---

## Day 2 (2026-05-05) — PREDICTION 89% display: NOT a cache bug

### What we thought

After completing the cursor-sharded fanout (137/137 dates captured), the deployment-ui kept showing PREDICTION at
**89.05%**. Initial hypothesis: stale cache.

Found and patched a real cache layering issue: `/api/data-status/turbo/clear` was only dropping 2 of 4 cache layers.
Fixed in `deployment-api@4dff799`:

- ✅ `data_analytics_service._turbo_cache` (always cleared)
- ✅ `data_status_service._INDEX_CACHE` (always cleared)
- ✅ `data_status_drilldown._cache` — **previously NOT cleared** (drilldown shard counts, 5-min TTL)
- ✅ `DataStatusService._REF_DATA_CACHE` — **previously NOT cleared** (upstream-expected-dates, 5-min TTL)

`clear_drilldown_cache()` was imported at module top and its docstring claimed it was used by `/turbo/clear`, but the
call had been silently dropped. Defensive fix lands all four clears.

But — after restarting the deployment-api with all 4 caches dropping, the **89% number persisted**. So cache wasn't the
cause.

### Actual cause: adapter false positives

The Polymarket adapter classifies markets into data_types (BTC, ETH, SOL, BNB, …) by substring-matching the market
question text:

```python
# Pre-fix in polymarket.py
_CRYPTO_KEYWORDS = {"bnb": "BNB", "btc": "BTC", "sol": "SOL", "hype": "HYPE", ...}
def _match_crypto_asset(q):
    for kw, canonical in _CRYPTO_KEYWORDS.items():
        if kw in q.lower():
            return canonical
```

Bare-substring matching produces false positives where stock tickers containing crypto-ticker substrings get
misclassified:

| Question                                  | Bucket assigned | Reality           |
| ----------------------------------------- | --------------- | ----------------- |
| "Airbnb (ABNB) Up or Down on October 16?" | **BNB**         | Airbnb stock      |
| "Solar panel adoption..."                 | **SOL**         | Solar industry    |
| "Hyped product launches..."               | **HYPE**        | Generic adjective |

Audit on 2026-05-05: **30 of 78 BNB-tagged dates** in the canonical manifest were Airbnb stock markets, NOT BNB token
markets. Same pattern (smaller noise) for HYPE/DOGE/SOL.

So the deployment-ui's start_date for `(POLYMARKET, BNB) = 2026-03-01` is **correct** — that's roughly when actual BNB
token markets first appeared on Polymarket. The earlier "BNB" rows in the canonical are noise. The 89% reflects **honest
coverage** of real markets, with noise correctly excluded from both numerator and denominator.

### Fix in `instruments-service@b336834`

`_match_crypto_asset` now uses **word-boundary regex** patterns compiled once at import:

```python
_CRYPTO_KEYWORD_PATTERNS = [
    (re.compile(rf"\b{re.escape(kw)}\b"), canonical)
    for kw, canonical in _CRYPTO_KEYWORDS.items()
]

def _match_crypto_asset(q_lower):
    for pattern, canonical in _CRYPTO_KEYWORD_PATTERNS:
        if pattern.search(q_lower):
            return canonical
```

Smoke tests pass:

- ✅ `"Airbnb (ABNB) Up or Down"` → no match (was BNB)
- ✅ `"BNB Up or Down March 15"` → BNB
- ✅ `"Solar panel adoption"` → no match (was SOL)
- ✅ `"Hyped product launch"` → no match (was HYPE)

Macro keywords (`crude oil`, `s&p 500`, etc.) are multi-word phrases that don't suffer from this and stay on substring
matching.

### Out-of-scope follow-ups

1. **Dict-iteration-order quirk**: questions like _"will ethereum (eth) flip btc?"_ return the first-seen ticker (BTC),
   not the most-relevant one. Pre-existing behavior; needs a different fix (longest-match-first or schema-aware
   classification).
2. **Existing canonical noise**: today's PREDICTION canonical still contains the misclassified Airbnb rows in BNB. After
   this adapter fix lands, a future fanout pass would write correct rows — but the noisy historic rows remain. Cleanup
   option: re-run the affected (date, BNB) shards to overwrite, OR add a one-off manifest-reconciliation script. Not
   blocking.
3. **No more "PREDICTION needs more data" work today** — coverage is honest, system reports the truth.

---

## Day 2 (2026-05-05) — Polymarket misclassification cleanup (Phase 1 + verification)

### What we cleaned

Removed **42 Airbnb (ABNB) stock markets** from the canonical that had been misclassified as BNB token markets due to
substring keyword matching.

| Action                                                 | Count                                                                                |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| Instrument rows removed                                | **42**                                                                               |
| Shards emptied (manifest row dropped)                  | 25 (Airbnb-only Oct/Nov 2025)                                                        |
| Shards trimmed (Airbnb removed, real BNB markets kept) | 17                                                                                   |
| Canonical rows                                         | 3,966 → **3,940**                                                                    |
| BNB unique dates remaining                             | 78 → **53**                                                                          |
| Backups                                                | `gs://instruments-store-prediction-central-element-323112/_backups/20260505-182631/` |

All removals verified line-by-line — every removed row's `market_slug` was `abnb-up-or-down-on-...` (Airbnb), not
`bnb-up-or-down-...` (real BNB token).

### Adapter fix iterations (instruments-service@d7bd17f)

The journey was non-trivial:

**Iteration 1 (b336834)**: Pure word-boundary regex `\bbtc\b`. Fixed `abnb`→BNB false positive but introduced regression
— also rejected `archBitcoin`/`archEthereum`/`archSolana`/`archXRP`/`archHyperliquid` which are LEGITIMATE Polymarket
arch\* prefixed markets. Audit flagged 629 candidates including ~388 false negatives.

**Iteration 2 (d7bd17f, current)**: Hybrid matcher:

- **Long-form names** (bitcoin, ethereum, solana, dogecoin, hyperliquid, xrp): plain substring match. Catches
  `archBitcoin`, `Bitcoin`, `Ethereum...`, `archXRP` correctly. Safe because no English word contains these as a
  substring.
- **Short tickers** (btc, eth, sol, doge, bnb, hype): require non-letter boundary `(?<![a-z])TICKER(?![a-z])`. Rejects
  `abnb`, `solar`, `hyped` while still matching `BTC?`, `BNB `, etc.

15/15 smoke tests pass.

### Phase 1 audit revealed dual-schema issue

Polymarket adapter writes two distinct parquet shapes:

- **Question-format** shards: have `question`, `market_slug`, `description`, `event_title` columns. Adapter classifies
  by parsing question text. Most BNB/BTC/etc. shards from 2026-03+ use this.
- **Canonical-ID-format** shards: have `instrument_key`, `base_asset` (e.g.
  `PREDICTION:POLYMARKET:UP_DOWN:DOGE:1D:2025-03-14`), `venue`, `instrument_type`. Older Polymarket adapter writes some
  asset_groups in this shape — the data_type is encoded in `base_asset`, not classified from text.

The first audit script only inspected `question` column. **128 DOGE / 23 ETH / 25 SOL / 14 XRP / 27 BTC rows flagged for
removal in v1 audit were actually canonical-ID-format shards with no question text** — they're correctly classified by
their `base_asset` encoding, the audit just couldn't see it.

After narrowing scope to question-format shards only, real misclassifications dropped from "629" to **42** (all
Airbnb-as-BNB).

### Phase 2 verification

Built `/tmp/audit-polymarket-canonical-id.py` to parse `base_asset` and verify the encoded data_type matches the shard's
stored data_type. Running now to confirm canonical-ID-format shards have no real misclassifications.

### Cache-clear hardening (deployment-api@4dff799) — separate fix

`/api/data-status/turbo/clear` previously dropped only 2 of 4 cache layers. `clear_drilldown_cache()` was imported at
module top with a docstring claiming it was used by `/turbo/clear`, but the call had been silently dropped. Now drops
all 4 layers:

1. `data_analytics_service._turbo_cache`
2. `data_status_service._INDEX_CACHE`
3. `data_status_drilldown._cache` (was missing)
4. `DataStatusService._REF_DATA_CACHE` (was missing)

Defensive hardening — wasn't actually responsible for the 89% display today, but worth fixing.

### What remains for Ikenna

1. **VenueMapping per-(venue, data_type) start dates**: legitimate `bnb-up-or-down-on-october-21-2025`-style markets
   exist back to 2025-10-21 but the UI's start_date for `(POLYMARKET, BNB)` is set to ~2026-03-01. After today's Airbnb
   cleanup, the remaining BNB rows are all real — the start_date config could be extended back to 2025-10-21 to credit
   the early coverage.

2. **Pre-existing dict-iteration-order quirk** in `_match_crypto_asset`: questions like
   `"will ethereum (eth) flip btc?"` return the first-seen ticker (BTC), not the most-relevant one. Out of scope today;
   needs longest-match-first logic or schema-aware classification.

3. **Polymarket dual-schema architecture**: the adapter writes both question-format and canonical-ID-format shards
   depending on... something. Worth a code-walk to understand which path triggers which, and whether to consolidate.

### Phase 2 verification result (clean)

`/tmp/audit-polymarket-canonical-id.py` parsed `base_asset` for every canonical-ID-format shard and verified the encoded
data_type matched the stored data_type:

| Schema type                          | Shards | Mismatches |
| ------------------------------------ | ------ | ---------- |
| Question-format (audited in Phase 1) | 1,653  | 42 fixed   |
| Canonical-ID-format (Phase 2)        | 95     | **0** ✓    |

**Total cleanup needed: 42 rows. All removed. Canonical is now clean.**

---

## Retrospective — how the Polymarket misclassification was actually found

This deserves a full writeup because the investigation was meandering and the user (Harsh) repeatedly steered it away
from dead ends. The agent (Claude) did the mechanical work but kept fixating on wrong hypotheses. Without the user's
pushback at three separate decision points, this would have ended with either (a) a "the cache is broken" patch that
wouldn't have actually fixed anything, or (b) a destructive cleanup of 388 legitimate markets.

### Why it took ~2 hours to find a 1-line bug

#### Detour 1: chasing the cache-staleness hypothesis (~30 min)

After the PREDICTION fanout completed, the deployment-ui kept showing `89.05%` coverage. The agent's initial framing
was: _"the data is in the canonical, so the UI's number must be cached."_

The agent dug into the deployment-api source, found four cache layers, noticed `/turbo/clear` only drops two of them,
and patched it (`deployment-api@4dff799`). This was a real bug — the docstring at `clear_drilldown_cache()` claimed it
was used by `/turbo/clear` but the call had been silently dropped. Patching it was correct hardening.

But after the patch landed and the deployment-api restarted, the **89% number persisted**. Cache wasn't the cause.

**User intervention #1:** Harsh asked _"i dont understand the issue clearly, can you give me example of whats now vs
whats correct for venue, data_type issue."_

This forced the agent to stop hand-waving and produce concrete numbers. The agent showed:

- Canonical has 78 BNB dates (Oct 2025 → Apr 2026)
- API reports 41 dates found in window 2026-03-01 → 2026-05-03
- Difference: 37 dates pre-March that exist in canonical but are excluded by the UI's per-(venue, data_type) start_date

The agent's next take was _"the system is correct — the UI's start_date config is right and the canonical has incidental
noise."_ Ready to close the ticket as "honest coverage, no action needed."

#### Detour 2: trusting the system without checking the data (~10 min)

**User intervention #2:** Harsh:

> "Expected dates = 2026-03-01 → 2026-04-16 = 64 dates -> how is this 64 dates? its just 45 days... or are we not
> including the holidays and weekends? to answer the system vs data we should check which markets are these in october?"

Two important nudges in one message:

1. The agent's date math was off (the actual window end was `2026-05-03` per the query, giving 64 days — agent had
   eyeballed it wrong).
2. **Don't trust the abstraction; look at the raw data.**

Without that second nudge, the agent would have closed the case based on its assumptions about what the start_date
config "must" mean. Instead, the agent opened a real October-2025 BNB instrument parquet and found:

```
question: "Airbnb (ABNB) Up or Down on October 16?"
market_slug: "abnb-up-or-down-on-october-16-2025"
```

That single row of evidence proved the actual bug: **the matcher had been misclassifying Airbnb stock markets as BNB
token markets via substring keyword matching.**

#### Detour 3: shipping a fix that introduced a regression (~25 min)

The agent immediately patched `_match_crypto_asset` to use word-boundary regex (`\bbnb\b` instead of
`bnb in q.lower()`). Smoke tested 5 cases, all passed. Pushed `instruments-service@b336834`. Felt confident.

**User intervention #3:** Harsh asked the agent to actually verify by running an audit before doing the cleanup:

> "Yes please do all the 3 things" _(ie. patch + audit + cleanup)_

And then later, when the agent was about to run the cleanup based on the audit:

> "But, you should check what we are deleting, you know. Instead of just running the script, think you should First do
> the audit of what it's replacing or what it's deleting removing, what you know about those things. Once the audit
> looks clean, know, then we can run the pipeline and delete you know, the wrong instrument."

This insistence on a real pre-audit before any writes is what saved the integrity of the canonical. The agent ran the
audit, planning to use the results to drive the cleanup. The audit returned **629 candidates for removal**.

The agent looked at the BTC sample first:

```
"archBitcoin Up or Down on June 11?"
"archEthereum Up or Down on June 11?"
"archSolana Up or Down on August 16, 12AM ET"
```

These were all **legitimate Polymarket markets** (`arch*` is a Polymarket-internal market series prefix) that the
agent's "fixed" matcher was now incorrectly excluding. The pure word-boundary regex `\bbitcoin\b` doesn't match
`archBitcoin` because the `B` is preceded by a word character (no boundary).

If the agent had run the cleanup script with that audit output, **388 legitimate crypto markets across
BTC/ETH/SOL/XRP/HYPE would have been silently removed from the canonical** — far worse than the original 42-row Airbnb
noise.

Instead, the agent caught the regression because Harsh's audit-first protocol forced inspection. The agent reverted to a
hybrid matcher (`instruments-service@d7bd17f`):

- **Long-form names** (bitcoin, ethereum, solana, dogecoin, hyperliquid, xrp): plain substring — catches `archBitcoin`
  correctly because no English word contains `bitcoin` as a substring outside crypto contexts
- **Short tickers** (btc, eth, sol, doge, bnb, hype): require non-letter boundaries `(?<![a-z])TICKER(?![a-z])` —
  rejects `abnb`, `solar`, `hyped`

15/15 smoke tests passed.

#### Detour 4: audit script blind to dual schemas (~15 min)

Re-ran the audit with the corrected matcher. Got **443 candidates**. Inspected DOGE samples — all had `question=NaN`.
Pulled a DOGE shard directly:

```python
# DOGE 2025-03-14 shard
columns: ['instrument_key', 'venue', 'instrument_type', 'raw_symbol', 'base_asset', ...]
sample: {
    'instrument_key': '0xe369626bf3813af67dfc...',
    'base_asset': 'PREDICTION:POLYMARKET:UP_DOWN:DOGE:1D:2025-03-14',
    ...
}
# NO question column at all
```

The Polymarket adapter writes **two distinct parquet shapes**:

- **Question-format** shards: classified by parsing question text (most BNB, BTC, etc. from 2026-03+)
- **Canonical-ID-format** shards: classified by the `base_asset` string itself (older Polymarket adapter writes for some
  asset_groups)

The audit script was only checking `question` — for canonical-ID shards it found `question=NaN` and treated them as "no
match → REMOVE candidate". **128 DOGE / 23 ETH / 25 SOL / 14 XRP / 27 BTC / 76 BNB rows were false alarms** because the
audit script couldn't read the canonical-ID schema.

If the agent had run the cleanup against the v2 audit results, it would have deleted **401 legitimate canonical-ID
rows**.

The agent narrowed scope to question-format shards only, getting the real answer: **42 Airbnb-in-BNB rows. That's it.
That's the whole bug.**

A Phase 2 audit (`/tmp/audit-polymarket-canonical-id.py`) was written specifically to verify canonical-ID shards by
parsing `base_asset` and confirming the encoded data_type matched the stored data_type. **Result: 0 mismatches across 95
canonical-ID shards.** Confirmed clean.

### What the user (Harsh) did right that the agent kept missing

1. **Demand concrete numbers, not narratives.** When the agent said _"system is correct, UI clips pre-launch dates"_,
   Harsh asked _"give me example of what's now vs what's correct"_. That forced the agent to look at actual rows.

2. **Don't trust the abstraction without checking the data.** The agent kept treating `start_date` config as
   authoritative. Harsh's _"check which markets are these in october"_ turned a hand-wave into a one-line proof that the
   bug was upstream of the start_date config — it was the adapter producing noise that the start_date config was
   correctly filtering.

3. **Pre-audit before any destructive action, even when the patch "looks right".** The agent had passed 5 smoke tests on
   the word-boundary matcher and was ready to ship + clean up. Harsh's _"first do the audit of what it's replacing"_
   caught the arch\* regression that would have destroyed 388 legitimate market records. Same protocol caught the
   dual-schema audit-script bug that would have destroyed another 401 legitimate rows.

4. **Iteration over confidence.** Three separate times the agent declared _"the fix is in, we're done"_ and three times
   Harsh said _"verify it"_. Each verification cycle uncovered a different layer of the issue: cache staleness was
   wrong, then word-boundary was over-aggressive, then dual-schema audit was incomplete.

The actual bug — substring matching in 12 lines of `_match_crypto_asset` — could be fixed with a 49-line diff. The
2-hour journey was the cost of arriving at that small fix without breaking anything else.

### Lessons for the codebase / process

1. **The `_match_crypto_asset` function should never have been doing keyword classification.** The canonical-ID shards
   already encode the data_type in `base_asset`. The bug exists because the adapter has two code paths writing different
   schemas, and the question-format path uses a regex hack instead of a structured classifier. Long-term: unify on
   canonical-ID shards or carry a `derived_data_type` field through the adapter so classification doesn't depend on text
   matching.

2. **Audit scripts should fail loud on schema-blindness.** The first audit silently mapped `question=NaN` to "REMOVE
   candidate". Better default: raise on missing schema fields, force the human to tell the script "I know about this
   case, treat it as X".

3. **Defensive cache-clear hardening is good**, but cache symptoms are easy to misdiagnose. When a UI number "looks
   stale", check the actual data store first, not the cache layer.

4. **Pre-audit is non-negotiable for destructive ops.** This run shipped without breaking the canonical because Harsh
   insisted on it. A different agent (or different user) skipping the audit would have catastrophically corrupted the
   data.

---

## Day 2 (2026-05-05) — CEFI/DEFI manifest rebuild + HYPERLIQUID config mismatch finding

### Context: user flagged "phantom missing shards"

UI was showing missing shards across BITGET-FUTURES (6 dates), BITGET-SPOT (5), DERIBIT (12), HYPERLIQUID (200), and
DEFI (~24 dates × 25 venues). User correctly noted: *"cefi and defi should not have any gap, they are 24*7*365
markets"*.

### Investigation pattern: ALWAYS check GCS before declaring a real gap

For each "missing" date, probed GCS at `instrument_availability/by_date/day=YYYY-MM-DD/venue=<V>/instruments.parquet`:

| Venue                       | Sampled missing dates    | GCS reality                                         |
| --------------------------- | ------------------------ | --------------------------------------------------- |
| BITGET-FUTURES              | 5 dates                  | All 5 have parquet on GCS ✓                         |
| BITGET-SPOT                 | 3 dates                  | All 3 have parquet on GCS ✓                         |
| DERIBIT (11 of 12)          | 5 dates                  | All 5 have parquet on GCS ✓                         |
| DERIBIT (12th = 2026-05-04) | 1 date                   | Genuinely missing — never captured                  |
| HYPERLIQUID                 | 5 dates from 2023-04..10 | NO parquets on GCS ✗                                |
| DEFI per-chain venues       | many                     | All have parquets, just under different venue names |

**Two distinct phenomena:**

1. **Manifest staleness**: GCS parquets exist but canonical manifest doesn't have the row → `rebuild_cefi_manifest.py`
   fixes this.
2. **Phantom expected dates**: data was never captured because the upstream API can't return it → not fixable by
   backfill.

### Action 1: CEFI manifest rebuild (instruments-service/scripts/rebuild_cefi_manifest.py)

```bash
GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp \
  MANIFEST_PER_VM_SHARDS=true VM_NAME=local_rebuild_cefi_<ts> \
  .venv/bin/python scripts/rebuild_cefi_manifest.py --asset-group CEFI
```

Output:

```
Current manifest: 27935 entries, 2593 unique dates
Scanning GCS blobs...
rebuild_manifest: discovered 22 (date, venue) shards missing from manifest
rebuild_manifest: wrote 27957 entries (22 new) to instruments-store-cefi-...
```

Result: CEFI 99.21% → **99.29%**. BITGET-FUTURES + BITGET-SPOT now 100%, DERIBIT 12-missing → 1-missing.

### Action 2: DERIBIT 2026-05-04 backfill

The only actual missing date in CEFI after the manifest rebuild. Captured 3,563 records via single-process
instruments-service run.

### Action 3: DEFI manifest rebuild (dry-run)

```
Current manifest: 128342 entries, 2296 unique dates
Scanning GCS blobs...
rebuild_manifest: all 64505 blobs already in manifest (128342 entries)
Result: 128342 total entries (+0 new), 2296 unique dates, 77 venues
```

**Zero new entries** — DEFI canonical is already complete. The "24 dates missing × 25 venues" UI display is a separate
issue: **legacy aggregate venue names** (`UNISWAP_V3`, `MORPHO`, `JITO`) stopped being written on 2026-04-11 when the
adapter switched to **per-chain venue names** (`UNISWAP_V3-ETHEREUM`, `MORPHO-ETHEREUM`, `MORPHO-BASE`, `JITO-SOLANA`).
Both naming sets exist in the canonical with overlapping date coverage, but the data-status service treats them as
independent venues.

This is a UI/data-status display issue, not a data gap. Out of scope for instruments-service; needs a deployment-api
change to alias `UNISWAP_V3` ⇒ `UNISWAP_V3-*` (sum across per-chain rows).

### Action 4: HYPERLIQUID 200 phantom missing dates — config mismatch [x] FIXED 2026-05-05

Three sources disagreed on Hyperliquid's start date:

| Source                                                                                   | Date           | Stated rationale                                                   |
| ---------------------------------------------------------------------------------------- | -------------- | ------------------------------------------------------------------ |
| `unified-api-contracts/canonical/coverage_starts.py:49`                                  | 2023-06-29     | (no comment)                                                       |
| `unified-api-contracts/registry/venue_mapping.py:224`                                    | 2023-04-15     | "earliest = book_snapshot_5 S3 archive" (market-data perspective)  |
| `instruments-service/instruments_service/reference_data/adapters/cefi/hyperliquid.py:30` | 2023-11-01     | hardcoded `_HYPERLIQUID_LAUNCH_DATE` for `available_from_datetime` |
| **GCS reality (canonical earliest captured)**                                            | **2023-11-01** | matches the adapter                                                |

The Hyperliquid REST API (`https://api.hyperliquid.xyz`) returns 21 instruments total, with `available_from_datetime`
hardcoded to 2023-11-01 by the adapter. **No instrument is visible on dates < 2023-11-01.** Probed 2023-05-01,
2023-06-15, 2023-08-01, 2023-09-15: all return 21 instruments fetched, 0 active after date filter.

**The 200 missing dates aren't backfillable** — the upstream API doesn't expose historical instrument-listing snapshots.

#### Resolution shipped 2026-05-05 — single SSOT in UAC

Picked **neither Option A nor B** — both would have created a second SSOT (an override map in either UAC or adapter).
Instead: recognized that "instruments-service expected-window start" is a **venue-level fact** (not a per-data_type or
per-service fact), and added it as a dedicated UAC field next to `venue_start_dates`. The adapter hardcoded constant
(`_HYPERLIQUID_LAUNCH_DATE`) is now a CONSUMER of UAC — it imports the date instead of duplicating it. The
orchestrator's `is_venue_available()` consults the new helper instead of `venue_start_dates` directly.

Surface area:

- **UAC** [`venue_mapping.py`](../../../unified-api-contracts/unified_api_contracts/registry/venue_mapping.py):
  - New sparse field `venue_instrument_discovery_overrides: dict[str, str]` — only HYPERLIQUID for now.
  - New helper `get_instrument_discovery_start(venue) -> str | None` — returns override if present, else falls through
    to `get_venue_start_date(venue)`. Docstring explains the semantic distinction (market-data archive vs
    instrument-discovery API earliest).
- **instruments-service**
  [`engine/orchestrator.py`](../../../instruments-service/instruments_service/engine/orchestrator.py):
  - Removed local `_VENUE_LAUNCH_DATES` dict cache.
  - `is_venue_available(venue, date)` now calls `_VENUE_MAPPING.get_instrument_discovery_start(venue)`.
  - `earliest_venue_date(venues)` does the same.
- **instruments-service**
  [`reference_data/adapters/cefi/hyperliquid.py`](../../../instruments-service/instruments_service/reference_data/adapters/cefi/hyperliquid.py):
  - `_HYPERLIQUID_LAUNCH_DATE` is now
    `datetime.fromisoformat(VenueMapping().get_instrument_discovery_start("HYPERLIQUID")).replace(tzinfo=UTC)` — pulls
    from UAC at module load. The adapter no longer carries a hardcoded date.

Verification: smoke run confirms `is_venue_available("HYPERLIQUID", "2023-05-01") == False` (was True pre-fix → 200
phantoms), `is_venue_available("HYPERLIQUID", "2023-11-01") == True`, and `_HYPERLIQUID_LAUNCH_DATE` matches UAC's value
at import. 48/48 instruments-service hyperliquid tests pass. UAC: 105 venue-mapping/hyperliquid tests pass (2
pre-existing failures unrelated to this change — cassette format + freshness config).

**Single SSOT achieved**: HYPERLIQUID's discovery-start date now lives in EXACTLY ONE place
(`venue_instrument_discovery_overrides["HYPERLIQUID"]`). Adapter + orchestrator both consume from it. Future divergent
venues (ASTER currently has the same 2-source pattern — UAC says 2024-10-01, adapter says 2024-09-01; flagged as P2
follow-up below) get a single-line addition to the override dict, not a new code path.

### Final state post-rebuild

| Asset Group | Coverage         | Real gap                                                                                            | Notes                                                    |
| ----------- | ---------------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| CEFI        | 99.29%           | 1 date (DERIBIT 2026-05-04, just captured awaiting consolidator) + 200 phantom (HYPERLIQUID config) | Effectively 100% real                                    |
| TRADFI      | 100%             | none                                                                                                | ✓                                                        |
| DEFI        | 98.12% (UI)      | 0 real                                                                                              | UI venue-aliasing issue. Canonical complete.             |
| PREDICTION  | 88.66%           | 0 real                                                                                              | per-(date, data_type) accounting + UAC start_date config |
| SPORTS      | 100% (top-level) | varies per source                                                                                   | ongoing batch backfill                                   |
