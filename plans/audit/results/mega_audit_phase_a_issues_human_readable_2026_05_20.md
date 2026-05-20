# Mega-audit Phase A — human-readable issues + sampling transparency

> Operator directive 2026-05-20: "I want human-readable summaries of the
> issues so that I can audit what's actually wrong. I want to know where you
> sampled and where you've looked at everything."
>
> This doc explains, per audit, what was scanned exhaustively vs sampled vs
> approximated; the **specific issues** with venue + data_type + time-range
> articulation; and the remediation handoff per issue.

---

## Section 0 — Coverage matrix (sampling vs comprehensive)

| Audit | Inputs walked | What got read | Sampled? | Coverage |
|---|---|---|---|---|
| **A1** code-shape | 25 service repos × every `*.py` file | 8,142 files, full content of each, 10 regex pattern checks per file | **NO — every file** | Comprehensive across the 25 repos. Regex-based heuristics ⇒ may have false positives + negatives. No AST parsing. |
| **A2** oracle function | 5 UAC SSOTs: scope policy + venue launch dates + chain genesis + Phase-4 coverage_start + tradfi calendar | Function composes all 5 deterministically | **N/A — pure code** | Function is exhaustive over the inputs. Known gaps in the *inputs*: sports off-season calendars not encoded; DeFi protocol pauses not encoded. |
| **A2** dump | Every in-scope (asset_group, source, data_type, date) tuple from EXPECTED_COVERAGE_BY_ASSET_GROUP | 429,088 cells materialised | **NO — every in-scope cell** | Comprehensive at (venue, data_type, date) granularity. **DOES NOT** materialise per-symbol cells (operator decision 2026-05-20 to filter by scope); per-symbol divergence requires A3-style read of manifest rows. |
| **A3** manifest divergence | 5 prod MTDS bucket manifest indexes | `gs://market-data-tick-{cefi,defi,tradfi,sports,pred}-prd-central-element-323112/_index/availability_index.parquet` — full reads | **NO for MTDS — every row** (3,968,880 rows) | **GAP**: only MTDS buckets read. Instruments-service (IS) manifest buckets NOT read. Features-service / strategy-service / execution-service manifests NOT read either (do they exist? — not enumerated). Sampling of *services* — only the producer-of-MTDS path covered. |
| **A4** v8 deep — data | 10 buckets (5 MTDS + 5 IS) | Each `_index/availability_index.parquet` `schema_version` column distribution | **NO — every row at the master index** | Master availability_index covered. `_index/per_vm/*.parquet` shards NOT read (these are pre-consolidation per-VM shards; consolidator merges them into master). Theoretically incomplete but the consolidator should make master authoritative. |
| **A4** v8 deep — code | 19 service repos × every manifest-consumer Python file | 235 consumer files (filtered by `MANIFEST_READ_PATTERN` regex) | **YES — only files matching the consumer-detection regex were inspected** | Regex `read.*manifest \| manifest.*read \| availability_index \| read.*_index/` may MISS indirect consumers (e.g. files that read manifest rows via UTL helper without those tokens in source). |
| **A5** dependency-fail propagation | — | **NOT RUN this session** | N/A | **Open** — scaffolded as a follow-up todo in mega-audit tracker. Operator directive raised priority to P0. |
| **A6** batch-live adapter parity | — | **NOT RUN this session** | N/A | **Open** — scaffolded as a follow-up todo. Operator directive raised priority to P0. |

**Explicit additional coverage gaps below A1-A6 entirely:**

- `instruments-service` produces manifest-like state in its own GCS buckets (`instruments-store-*-prd-central-element-323112`) — A4 data-side reads these but A3 (the divergence comparison) does NOT. So IS-side `DIVERGENT_EMPTY` cells are not enumerated.
- `features-service`, `strategy-service`, `execution-service`, `ml-*` services likely have output-manifest paths too (per `service-output-emission-semantics.md` codex SSOT). NOT inventoried.
- AWS-side buckets (per `cloud-providers.yaml` `aws:` block) — every MTDS asset_group has a parallel AWS bucket. **NOT read.** Cross-cloud divergence is invisible to this audit.
- Backup snapshot parquets (`_index/availability_index.20260515-*.bak.parquet`, etc.) — visible in `gsutil ls` but NOT read or correlated.

---

## Section 1 — A1 issues (code-shape compliance) — exhaustive

**What this audit found:** 8,142 files scanned across 25 repos → 1,274 violating
files, 2,593 total violations. Every check has an existing or proposed QG step.

**Per-pattern breakdown (every check, every violation count):**

| # | Pattern | Violations | QG enforcement state | Top offending repos | Remediation owner |
|---|---|---:|---|---|---|
| 1 | `has_log_upload_trap` (launchers must call `lc_log_upload_trap_block`) | 28 | SHIPPED (deployment-service@6b4610c fixed 14 launchers) | execution-service, market-tick-data-service, deployment-service | deployment-service team — verify A1-flagged launchers are all post-fix |
| 2 | `manifest_v8` (no `schema_version=<8` in code) | 6 | PARTIAL — see A4 for the **bigger v8 data-side problem** | unified-trading-library, market-tick-data-service | UTL team — bundle with A4 v8 backfill |
| 3 | `record_emission` (handlers must emit `record_captured/empty/failed`) | 215 | SHIPPED (`no_silent_absence_handlers.sh` + `check_emission_policy_paired_callsites.py`) | market-tick-data-service, features-service, execution-service | per-service handler owner — ratchet to 0 |
| 4 | `typed_empty_reason` (no `record_empty(reason="literal")`) | 81 | **GAP — runtime-only via `LegacyBlankErrorReasonError`** | execution-service, features-service, market-tick-data-service | UTL + per-service migration; new QG step needed |
| 5 | `classify_venue_error` (adapters w/ except blocks must classify + emit `ADAPTER_FETCH_FAILED`) | 302 | SHIPPED (`no_adapter_contract_regression.sh`) | execution-service (227 files violating overall), market-tick-data-service (181 violating overall) | per-venue adapter owner — ratchet existing QG |
| 6 | `resolve_bucket_name` (no inline `gs://` f-string) | 759 | SHIPPED (`check_inline_bucket_uri.py` + `inline_bucket_uri_baseline.yaml`) | unified-trading-library tests (lots of inline gs:// in fixtures), deployment-api, deployment-service | Per-file ratchet via existing baseline yaml. Many test fixtures are legitimate use; needs review-per-file before mass-replace |
| 7 | `lifecycle_class` (`VmPrefixSpec(... lifecycle_class=None)`) | 0 | PARTIAL (declared in `vm_zombie_watchdog.py` — needs CI check) | — | None right now; need CI step to prevent regression |
| 8 | `no_hardcoded_venue_urls` (`_DRIFT_S3_BASE = "https://..."`-style constants) | 189 | SHIPPED (`no_hardcoded_venue_urls.sh`) | features-service, execution-service, market-tick-data-service | per-handler migration to IS-provided URL — see C0 audit |
| 9 | `no_hardcoded_venue_universe` (`SOLANA_LST_TOKENS = [...]`-style constants) | 18 | SHIPPED (`no_hardcoded_venue_universe.sh`) | features-service, market-tick-data-service | per-handler migration to IS — see C0 audit |
| 10 | `uac_import_surface` (`from unified_api_contracts.canonical...` deep imports) | 995 | **GAP — Cursor rule only**, not CI-enforced | execution-service, market-tick-data-service, features-service, unified-trading-library | New QG step `check_uac_import_surface.py` + workspace-wide migration |

**Top 10 violating files (real code, not tests):**

| Rank | File | Violations |
|---|---|---|
| 1 | `instruments-service/instruments_service/engine/orchestrator.py` | 17 |
| 2 | `deployment-api/deployment_api/services/data_status_drilldown.py` | 16 |
| 3 | `market-tick-data-service/market_tick_data_service/engine/orchestrator.py` | 12 |
| 4 | `strategy-service/strategy_service/models/instruction.py` | 13 |
| 5 | `deployment-api/deployment_api/routes/services.py` | 10 |
| 6 | `strategy-service/strategy_service/engine/core/gcs_storage_service.py` | 10 |

(20+ test files have higher raw counts but most test violations are legitimate fixture noise — manual review per file required.)

**Honest A1 caveats — what could have slipped through:**

- AST-based parsing would catch dynamic imports + computed strings that regex misses. A1 is regex-only.
- Some test paths slipped past the "/tests/" exclusion (e.g. test_vcr_*.py files at top level of `tests/market_interface/integration/`).
- Files with `gs://` in *docstrings* (not code) are counted as violations.
- The `uac_import_surface` count (995) likely overstates the real problem because it counts the same file multiple times if it has multiple deep imports; per-file count is in the CSV.

---

## Section 2 — A2 oracle gaps (per asset_group) — exhaustive

The oracle currently **falls through to `SHOULD_HAVE_DATA`** (i.e. assumes data
should exist) in these specific cases that may be wrong:

**CeFi:**
- Pre-Tardis-archive windows for individual (venue, data_type) pairs are NOT
  modelled beyond `venue_launch_dates.py`. Example: BINANCE-FUTURES launched
  2019-09-08 but Tardis archive may begin later for `options_chain` data_type.
  Without `SourceCapability.coverage_start[options_chain]` populated, the
  oracle says SHOULD_HAVE_DATA from 2019-09-08 onward when it should say
  EXPECTED_PRE_SOURCE_COVERAGE_START until the archive starts.
- **Remediation**: extend slot-3 plan Phase 0 — fully populate
  `SourceCapability.coverage_start` per (venue, data_type) for every venue.

**DeFi:**
- No protocol-pause windows encoded. Examples (need operator confirmation):
  - Aave V2 → V3 migration windows on Ethereum (~Q1 2023?).
  - Compound V2 wind-down on most chains (~late 2024).
  - Chain reorgs (Polygon Bor halts, Solana outages, etc.).
- **Remediation**: build `PROTOCOL_PAUSE_WINDOWS: dict[str, list[(date, date)]]`
  in `chain_env.py` + extend oracle. Operator-driven calendar.

**TradFi:**
- Half-day sessions are encoded (HALF_DAY_SESSIONS for NYSE/NASDAQ/CBOE/CME/ICE
  /Eurex). For half-days the oracle returns SHOULD_HAVE_DATA with a partial-volume
  annotation — this is correct (half-days still have data), but downstream
  row-count thresholds may flag them.
- US-only — non-US tradfi venues NOT modelled (Eurex holidays beyond half-day
  list, etc.).
- **Remediation**: extend US_MARKET_HOLIDAYS to per-venue (NYSE vs CBOE may
  diverge on early closes) + add Eurex holiday list.

**Sports:**
- No off-season encoded. The oracle currently says SHOULD_HAVE_DATA for every
  in-scope sports venue × data_type × date once the venue launch passes.
- Empirically the 25,652 sports MISSING_EXPECTED cells in A3 are likely a mix
  of (a) genuine adapter gaps + (b) honest off-season days.
- **Remediation**: instruments-service knows fixtures. Pair A3 with IS fixture
  data rather than build a parallel league-calendar registry.

**Prediction:**
- Polymarket / Kalshi mostly trade 24/7 for crypto-derived markets; financial-
  instrument markets follow US trading days.
- The oracle treats prediction as 24/7. This may overstate SHOULD_HAVE_DATA for
  market types tied to US equities.
- **Remediation**: encode per-market-type calendar in prediction venue
  declarations + extend oracle.

---

## Section 3 — A3 manifest divergence (every venue × data_type with issues)

**Coverage of A3 itself**: only MTDS buckets. IS + features + strategy + execution
manifest divergences are **not enumerated here** and need follow-up.

### 3.1 DeFi (184k MISSING_EXPECTED + 765 DIVERGENT_EMPTY)

**MISSING_EXPECTED (silent gaps — adapter never emitted a row at all):**

| Venue | Data type | Cells missing | Date range affected |
|---|---|---:|---|
| FLUID-ETHEREUM | lending_indices | 2,332 | full window 2020-01-01 → 2026-05-20 |
| FLUID-ETHEREUM | liquidation_events | 2,332 | full window |
| FLUID-ETHEREUM | position_data | 2,332 | full window |
| FLUID-ETHEREUM | risk_params | 2,332 | full window |
| MORPHO-ETHEREUM | (all 4 lending types) | 2,332 each | full window |
| MORPHO-POLYGON | (all 4 lending types) | 2,182 each | window from Polygon launch |
| MORPHO-{ARBITRUM,BASE,OPTIMISM} | (all 4 lending types) | varies by chain genesis | each chain's window |
| CURVE-ETHEREUM | dex_swaps + dex_pools | 2,314 each | full window |
| CURVE-{AVALANCHE,OPTIMISM} | dex_swaps + dex_pools | varies | each chain window |
| BALANCER-{ETHEREUM,ARBITRUM,AVALANCHE,BASE,OPTIMISM,POLYGON} | dex_swaps + dex_pools | varies | each chain window |
| UNISWAPV2-ETHEREUM | dex_swaps + dex_pools | 2,207 each | full window |
| UNISWAPV3-{ARBITRUM,BASE,OPTIMISM,POLYGON} | dex_swaps + dex_pools | varies | each chain window |
| UNISWAPV4-ETHEREUM | dex_swaps + dex_pools | per launch | post-V4 window |
| COMPOUNDV3-{all chains} | (all 4 lending types) | varies | per chain window |
| AAVEV3-{LINEA,BSC} | (5 types — incl. flash_loan_events) | varies | per chain window |
| LIDO/ETHERFI/ETHENA-ETHEREUM | lst_rates + staking_yields | per launch | full window |
| JITO-SOLANA | lst_rates + staking_yields | per launch | Solana window |

**DIVERGENT_EMPTY (manifest says empty_confirmed but oracle says SHOULD_HAVE_DATA — 765 cells):**

Specific (venue, data_type) breakdowns NOT enumerated in this summary doc — they're in the parquet at
`plans/audit/results/manifest_divergence_2026_05_20.parquet`. To enumerate, filter the parquet on
`classification == "DIVERGENT_EMPTY" AND asset_group == "defi"` — 765 rows, all in DeFi. **These are the
Drift-S3-bug class and should be inspected per-cell.**

### 3.2 Sports (25,652 MISSING_EXPECTED across ALL bookmakers ALL data_types)

Every single bookmaker × (odds_snapshot, odds_movement) is missing the entire
window. Every. Single. One.

| Venue | Data types missing | Cells | Status |
|---|---|---:|---|
| BET365 | odds_movement + odds_snapshot | 2,332 + 2,332 | adapter never ran |
| BETFAIR | odds_movement + odds_snapshot | 2,332 + 2,332 | adapter never ran |
| DRAFTKINGS | odds_movement + odds_snapshot | 2,332 + 2,332 | adapter never ran |
| FANDUEL | odds_movement + odds_snapshot | 2,332 + 2,332 | adapter never ran |
| ODDS_API | odds | 2,332 | adapter never ran |
| PINNACLE | odds_movement + odds_snapshot | 2,332 + 2,332 | adapter never ran |

CAVEAT: A2 oracle has no sports off-season encoding, so some of these "missing" cells are honest off-season days. But even adjusting for that, the headline is that sports backfill has NOT been run for ANY of these venues. This is per-bookmaker × per-data_type — all 11 cells are silent.

### 3.3 CeFi (16,171 MISSING_EXPECTED + 17,207 ATTEMPTED_FAILED)

**MISSING_EXPECTED:**
- OKX: trades + book_snapshot_5 + derivative_ticker + liquidations all missing 2,332 cells (the entire window) — adapter never ran or never emitted.
- COINBASE: trades + book_snapshot_5 missing 2,332 each — same.
- UPBIT: trades + book_snapshot_5 missing 450 each — partial.

**ATTEMPTED_FAILED:**
- DERIBIT: futures_chain (2,286) + options_chain (2,283) + liquidations (1,819) — repeated failures, check error_reason
- BINANCE-FUTURES: futures_chain (2,309) + book_snapshot_5 (669)
- BYBIT: futures_chain (2,083) + book_snapshot_5 (589)
- ASTER: ALL 4 data types failed for 563 cells each (likely from launch onward)
- HYPERLIQUID: liquidations (916)

### 3.4 TradFi (7,115 MISSING_EXPECTED + 1,546 ATTEMPTED_FAILED + 1,928 UNEXPECTED_CAPTURED)

**MISSING_EXPECTED:**
- ICE: tbbo (1,254) + trades (1,238)
- CME: tbbo (1,188)
- YAHOO_FINANCE: ohlcv_15m (938) + ohlcv_24h (754)
- NYSE: ohlcv_1m (839)
- NASDAQ: ohlcv_1m (839)

**ATTEMPTED_FAILED:**
- YAHOO_FINANCE: ohlcv_24h (830) + ohlcv_15m (667) — repeated failures (likely rate-limit / rolling-window issues)
- CME: tbbo (22) — minor
- NYSE: ohlcv_1m (14) — minor

**UNEXPECTED_CAPTURED (1,928 cells)**: data exists on dates the oracle said EXPECTED_EMPTY (weekend/holiday). Most likely (a) oracle US_MARKET_HOLIDAYS list is outdated/wrong for some dates, OR (b) a US-trading venue is operating on a non-US calendar. Per-cell inspection needed.

### 3.5 Prediction (3,442 MISSING_EXPECTED)

- KALSHI: trades — 1,756 cells missing
- POLYMARKET: trades — 1,686 cells missing

CAVEAT: Polymarket launched 2020-09-01, Kalshi 2021-07-30. Some pre-launch cells are honest pre-launch but oracle handles that via NOT_YET_LIVE — these 1,756+1,686 are POST-launch cells that should have data.

---

## Section 4 — A4 manifest v8 deep — THE CRITICAL FINDING (every bucket, every asset_group)

**Bottom line: 0% of manifest rows are at v8 in any of the 10 buckets audited.**

| asset_group | bucket | rows | distribution |
|---|---|---:|---|
| cefi | instruments-store-cefi | 30,382 | v4: 12,361 / v6: 18,021 |
| cefi | market-data-tick-cefi | 2,632,931 | v4: 16,224 / v5: 30,704 / **v6: 2,246,785** / v7: 339,218 |
| defi | instruments-store-defi | 127,896 | v4: 69,630 / v6: 58,266 |
| defi | market-data-tick-defi | 1,606,190 | v6: 308,330 / v7: 11,600 / **NULL: 1,286,260** |
| tradfi | instruments-store-tradfi | 20,198 | v4: 11,301 / v6: 8,897 |
| tradfi | market-data-tick-tradfi | 141,401 | v4: 16,656 / v6: 89,272 / v7: 440 / NULL: 35,033 |
| sports | instruments-store-sports | 2,675,696 | v2: 434 / v4: 11,752 / v5: 481,109 / **v6: 1,409,896** / v7: 759,329 / NULL: 13,176 |
| sports | market-data-tick-sports | 157,500 | v4: 17,288 / v6: 140,212 |
| prediction | instruments-store-pred | 3,940 | v4: 3,145 / v6: 795 |
| prediction | market-data-tick-pred | 16,812 | v4: 14,296 / v5: 2 / v6: 234 / NULL: 2,280 |

**Total:** 7,413,946 rows; **none at v8**.

**The NULL rows (DeFi 1,286,260 + TradFi 35,033 + Prediction 2,280 + Sports 13,176)** are even worse than v<8 — they were written by a code path that didn't stamp a schema_version at all. **1,336,749 schema-version-less rows in prod manifest** is itself a critical issue.

**Code side**: scanned 235 manifest-consumer files. Found:
- 3 files with hardcoded `schema_version` < 8 (review-blocking)
- 27 files reference v8 explicitly (good — at least some code is v8-aware)
- 25 files have legacy-fallback patterns (need sunset dates)

**Diagnosis (the operator-flagged issue, confirmed by A4 data)**: the workspace's
`MANIFEST_SCHEMA_VERSION = 8` constant in `unified-trading-library/unified_trading_library/manifest_writer.py`
is set to 8, but writes are landing at v6/v7/NULL. This means EITHER:
1. The writer paths aren't using the canonical constant (older paths still
   hardcode v6/v7).
2. A migration script bumped the constant but never migrated existing rows.
3. Per-VM shards write at older versions + the consolidator doesn't upgrade
   schema.

All three need investigation. **No new manifest data can be considered v8-compliant
until both the writers + a backfill migration have closed this gap.**

---

## Section 5 — Where the audit IS NOT comprehensive (must close before claiming Phase A done)

**Operator directive 2026-05-20 requires every gap below be closed:**

| Gap | What it means | Estimated work |
|---|---|---|
| A3 doesn't read IS buckets | IS manifest divergences not enumerated; only MTDS covered | ~0.5 AI-day to extend A3 to read `instruments-store-*` buckets |
| A3 doesn't read features-service / strategy-service / execution-service / ml-* manifests | If those services have their own manifest indexes (per service-output-emission-semantics), divergences invisible | ~1 AI-day to inventory + read all service-output manifests |
| A3 doesn't read AWS-side buckets | Per `cloud-providers.yaml` every MTDS asset_group has a parallel AWS bucket — cross-cloud divergence unaudited | ~0.5 AI-day to read AWS S3 manifest indexes |
| A4 doesn't read `_index/per_vm/*.parquet` shards | Pre-consolidation per-VM shards may have different versions | ~0.5 AI-day to extend A4 to scan per_vm dir |
| A5 dependency-fail propagation | NOT RUN this session | ~1.5 AI-days |
| A6 batch-live adapter parity | NOT RUN this session | ~1.5 AI-days |
| A2 sports off-season + DeFi protocol pause + per-symbol granularity gaps | Oracle has known gaps that overstate SHOULD_HAVE_DATA | ~1.5 AI-days; some operator input needed for DeFi pause windows |
| A1 regex → AST upgrade | Some patterns may have false positives + negatives | ~1 AI-day to migrate the scanner to AST |

**Total to fully close Phase A:** ~8 AI-days. Of those, 0 days require operator
input that isn't already documented (the DeFi pause windows are the one
operator-judgment input; the rest is implementation work).

---

## Section 6 — Remediation roadmap (what each finding routes to)

Per operator directive: "I want every single issue that we found fully fixed,
bad manifest data migrated, without exception."

The roadmap routes findings into existing PM active plans (no new SSOTs):

| Finding | Existing plan to absorb it | Status |
|---|---|---|
| A1 typed_empty_reason + uac_import_surface QG gaps | `master_to_live_defi_2026_05_23.md` cross-cutting QG ratchet section (item 9 in tracker) | Extend existing |
| A1 lifecycle_class CI gap | `code_freeze_migrate_backfill_sequencing_2026_05_10.md` (VM lifecycle section) | Extend existing |
| A1 hardcoded URLs / universe (in non-allowlisted repos) | `is_mtds_contract_audit_2026_05_20.md` C0 audit (already in audit/) | Use existing |
| A1 record_emission gaps | `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 6.x | Extend existing |
| A2 sports off-season | (no existing plan) — create `sports_offseason_calendar_2026_05_20.md` | NEW plan |
| A2 DeFi protocol pause | Extend `defi_upstream_46day_full_backfill_2026_05_16.md` | Extend existing |
| A2 per-symbol axis | (no existing plan) — create `expected_coverage_per_symbol_2026_05_20.md` | NEW plan |
| A2 SourceCapability.coverage_start gaps | `uac_source_capability_metadata_promotion_2026_05_20.md` Phase 0 | Extend existing |
| A3 DeFi MISSING_EXPECTED (FLUID/MORPHO/CURVE/BALANCER/etc.) | `defi_upstream_46day_full_backfill_2026_05_16.md` | Extend existing |
| A3 DeFi 765 DIVERGENT_EMPTY | (no existing) — extends `is_mtds_contract_audit_2026_05_20.md` remediation | Extend existing |
| A3 Sports MISSING_EXPECTED (all 11 bookmaker×datatype combos) | `epics/sports_master_2026_05_07.md` | Extend existing |
| A3 CeFi MISSING_EXPECTED (OKX/COINBASE/UPBIT) | `epics/tradfi_master_2026_05_07.md` — no, this is CeFi; needs CeFi epic. If no CeFi master epic exists, this should be its own plan. | Possibly NEW plan |
| A3 Prediction MISSING_EXPECTED (KALSHI/POLYMARKET) | `epics/predictions_master_2026_05_07.md` | Extend existing |
| A3 TradFi MISSING_EXPECTED + ATTEMPTED_FAILED | `epics/tradfi_master_2026_05_07.md` | Extend existing |
| **A4 v8 data backfill (1.3M NULL + 5.4M v<8 rows)** | (no current plan exists for this!) — **needs a new dedicated plan** `manifest_v8_full_backfill_2026_05_20.md` | NEW plan |
| A4 v8 code-path gaps | Cross-cutting QG ratchet extension | Extend existing |
| A5 dependency-fail propagation | Needs new plan or extension of `dependency_freshness_*.md` | TBD — operator decide |
| A6 batch-live adapter parity | Extension of each adapter plan + new master `batch_live_parity_2026_05_20.md` | NEW plan |

**Of the existing plans, the ones doing layer-N+1 work that MAY need to be
frozen (per operator's directive about not doubling down on bad code):**

To identify these I need to read each active plan's frontmatter `layer_n` field and
check whether the prior-layer audit is GREEN. That's a follow-up audit I can run
in this same session if you want; for now I've flagged the gap.

---

## Section 7 — What "fully done" looks like

Per operator directive: no exceptions, no cutbacks, no missing venues/asset_groups,
no missing data_types, no missing time ranges. Only allowed deferral: when operator
explicitly articulates the reason.

**Phase A is "done" when:**

1. **A1**: every QG gap (typed_empty_reason, uac_import_surface, lifecycle_class CI)
   has a CI step that fails on regression. Baseline yaml ratchets every violation
   downward week-over-week. AST-based scanner replaces regex.
2. **A2**: oracle handles every named gap (sports off-season via IS fixtures,
   DeFi protocol pauses via operator-confirmed `PROTOCOL_PAUSE_WINDOWS`,
   per-symbol axis via IS catalogue join, US tradfi half-day annotated correctly,
   non-US tradfi venues).
3. **A3**: extended to every manifest-emitting service (IS + features + strategy +
   execution + ml-*) and every cloud (GCP + AWS). Re-run produces zero
   DIVERGENT_EMPTY + zero MISSING_EXPECTED cells that don't have a
   named-operator-acked exception.
4. **A4**: every existing manifest row migrated to v8 (or NULL rows backfilled
   with the correct version). Every code-path writer using the canonical
   `MANIFEST_SCHEMA_VERSION = 8` constant. QG step prevents resurgence.
5. **A5 + A6**: scanners built + run + every violation routed to a plan.

**Estimated total to "fully done":** beyond Phase A, the bulk of work is
operational (backfilling 7.4M manifest rows + filling 237k missing cells). That's
not Phase A audit work — that's the Phase D/E execution that the audit unblocks.

---

## Section 8 — Recommended operator decisions (where I need your input)

1. **Sports off-season calendars**: build registry OR pair with IS fixture data (recommended)?
2. **DeFi protocol pauses**: please enumerate known pause windows so I can build the registry.
3. **AWS-side manifest indexes**: are these still active or deprecated? (Affects A3 extension scope.)
4. **Per-symbol A2 dump**: do you want me to extend A2 to per-symbol granularity now, or after A4 v8 backfill completes (since per-symbol queries hit the same manifest data)?
5. **Slots to freeze**: please confirm which slots are currently doing layer-N+1 work (paper-trade scaffolding, execution-service polish, etc.) that should pause until A1-A6 are GREEN.
6. **CeFi master epic**: does one exist? I see TradFi + Sports + Predictions epics but didn't find a CeFi master.
