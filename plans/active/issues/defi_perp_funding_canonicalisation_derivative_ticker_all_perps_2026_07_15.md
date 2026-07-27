---
doc_type: issue
title:
  Perp funding canonicalisation — derivative_ticker for ALL perps + perp_funding schema conformance + cross-source
  parity
summary:
  Operator ruling 2026-07-15 — derivative_ticker at the highest source resolution is the canonical home of RAW funding
  for every perp venue (capture it even where the source has no open interest; OI fields nullable); perp_funding stays
  the per-interval canonical view (annualized_rate is fine) but the Drift-only funding_rate_24h/7d/30d window aggregates
  are a schema divergence to remove; and a cross-data_type funding parity check (perp_funding vs derivative_ticker
  settlements) must run once the DRIFT backfill grind completes.
status: open
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [defi, perp-funding, derivative-ticker, canonicalisation, funding-rates, data-correctness, parity]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/issues/defi_perp_funding_mvp_scope_contradiction_2026_06_29.md,
  ]
created: 2026-07-15
parent_epic: defi_master
priority: P1
source: [operator ruling 2026-07-15 (main session), funding dual-capture investigation same session]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-15
locked_since:
---

> 🟡 **PARTIAL SUPERSEDE — DRIFT leg only (2026-07-16, operator ruling, verbatim):** "kill drift entirely from our whole
> system it's pointless — Jupiter is the main one let's just use that. kill all other solana perp dex's. uac, code,
> adaptors, manifest, gcs, everything. no instruments no mvp nothing." DRIFT-SOLANA (and PACIFICA-SOLANA) removed
> entirely -- the DRIFT-specific rows/todos in this doc (the derivative_ticker DRIFT-SOLANA enumeration row, the
> `[CODE] P1` "DRIFT derivative_ticker funding endpoint is DEAD (403)" todo, and the `[VERIFY] P1` cross-source
> funding-parity todo's DRIFT-SOLANA leg) are now MOOT — there is no DRIFT adapter or venue left to fix or verify. The
> REST of this doc (Hyperliquid/Aster/GMX/Lighter derivative_ticker canonicalisation) is UNAFFECTED and remains active.
> SSOT for the removal: `/codex/04-architecture/solana-defi-coverage.md` (tombstone banner).

> 🟡 **FURTHER SUPERSEDE — GMX leg (2026-07-25, operator decision):** GMX removed platform-wide (its captured
> `perp_funding` history turned out to be a synthetic OI-imbalance proxy, not real funding-rate data — the native
> subgraph query never worked). The GMX-ARBITRUM/GMX-AVALANCHE `derivative_ticker` dual-write shipped by todo 2 below is
> being removed along with the rest of GMX support; GMX drops out of the "surviving venues" set referenced elsewhere in
> this doc (todo 4's MOOT note, the open `[DESIGN] P1` demote-to-derived-view todo). SSOT:
> `plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`.

# Perp funding canonicalisation — derivative_ticker for all perps (2026-07-15)

> **Operator ruling (verbatim intent, 2026-07-15):** "Annualising funding rates is fine, but the highest-resolution
> derivative_ticker data should be run for ALL perps — even if they don't have OI at the data source — for
> canonicalisation of where raw funding is. Aggregations into 7d, 30d etc. for Drift alone seems like a weird
> divergence."

## Established facts (verified this session)

- `perp_funding` is the canonical DeFi funding data_type (`defi-data-types-catalog.md` §4): schema
  `symbol, ts_event, venue, chain, funding_rate, annualized_rate`; one row per market per funding interval; MVP gate
  data_type on `mvp_backfill_defi_onchain_v10`.
- `derivative_ticker` carries the same funding at settlement/tick grain for several defi perp venues — Drift's adapter
  docstring: "one row per funding-rate settlement with funding_rate/mark_price"
  (`market-tick-data-service/.../adapters/drift_adapter.py:16,147-165`); HYPERLIQUID verified capturing both legs
  (derivative_ticker WS + perp_funding REST, 2026-07-14); ASTER/PACIFICA/EXTENDED/LIGHTER have derivative_ticker paths.
  CeFi perps use `derivative_ticker` as their ONLY funding source (`data-lineage-MTDS-features-ml.md`).
- Divergence: the Drift `perp_funding` writer adds `funding_rate_24h/7d/30d` window aggregates no other venue writes
  (`cli/handlers/solana_defi_drift.py:105-107`) — raw-layer aggregation, one venue special-cased.
- No documented cross-check exists that `perp_funding` and `derivative_ticker` agree for the same (venue, market,
  interval).

## Derivative_ticker coverage table (2026-07-15, todo 1 — read-only pass)

Grep-then-READ against `market-tick-data-service` (MTDS code) + `unified-api-contracts` (UAC capability registry).
"Declared" = has an entry in `VENUE_DATA_TYPE_CAPABILITIES`/`DEFI_VENUE_DATA_TYPE_CAPABILITIES`
(`unified_api_contracts/registry/market_data_categories.py` + `.../defi_venue_capabilities.py`), which gates whether the
standing daily enumerator schedules the (venue, derivative_ticker) cell at all. "Wired" = real MTDS fetch code exists
and is actually called by the live/batch routing path (`umi_tick_provider.py` or the relevant CLI handler) — verified by
reading the call site, not just grepping the adapter file (Lighter's native-REST adapter has zero funding code, but the
venue IS covered via a separate Tardis-routing branch — grep-then-conclude on the adapter file alone would have wrongly
flagged this venue MISSING).

| Venue                                     | Live path                                             | Batch path                                                      | Source resolution                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | OI at source                                                                                                                                    | Wired?                                                                                                                                                 | Declared in UAC?                                                                                                                                                                                                                                                                                  | Evidence                                                                                                                                                                                                      | Verdict                                                                                                                                                                                                                                                                                                                                                                                         |
| ----------------------------------------- | ----------------------------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DRIFT-SOLANA                              | `fetch_drift_data` via `umi_tick_provider.py:607-611` | same fn, `_fetch_funding_api` (Drift Data API `/fundingRates`)  | Per-settlement raw funding record, **only for `date >= 2025-01-01`** (`_DRIFT_API_START`) — no S3-era funding fetch exists in this adapter                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | No (mark_price only)                                                                                                                            | YES                                                                                                                                                    | **NO** — `defi_venue_capabilities.py:180` declares only `perp_funding`+`dex_pool_swaps`, no `derivative_ticker` key                                                                                                                                                                               | `adapters/drift_adapter.py:141-167` (`_parse_funding_row`, `data_type="derivative_ticker"`), `:315-341` (`want_funding and use_api` gate)                                                                     | **MISSING cell — registry-only fix.** Code already produces derivative*ticker rows; the enumerator just never schedules it. Honest start date = 2025-01-01 (not perp_funding's 2022-01-01 — that floor is served by a \_different* data_type/path, the S3 `fundingRateRecords` archive, which this adapter does not read for pre-2025 dates).                                                   |
| HYPERLIQUID                               | `hyperliquid_s3.py` REST fallback                     | `fetch_asset_ctxs` (S3 `hyperliquid-archive/asset_ctxs/`)       | Per-settlement, real `open_interest` field from S3; REST fallback zeroes OI                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Yes (S3), No (REST fallback, `open_interest=0.0`)                                                                                               | YES                                                                                                                                                    | YES — `market_data_categories.py:1252-1256`, start `2023-05-20`                                                                                                                                                                                                                                   | `adapters/hyperliquid_s3.py:308-561` (`_build_funding_ticker`, `open_interest` at :555/:719)                                                                                                                  | **Already correct.** No action.                                                                                                                                                                                                                                                                                                                                                                 |
| ASTER                                     | `_umi_aster.py` REST                                  | same (`_fetch_aster_coin`, unconditional — no Tardis date-gate) | Per-settlement via `/fapi/v1/fundingRate` REST                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | No                                                                                                                                              | YES                                                                                                                                                    | YES — `market_data_categories.py:1272-1277`, start `2023-07-22`                                                                                                                                                                                                                                   | `adapters/_umi_aster.py:96-129`                                                                                                                                                                               | **Already correct.** No action.                                                                                                                                                                                                                                                                                                                                                                 |
| GMX-ARBITRUM / GMX-AVALANCHE              | none (no live connector)                              | `_collect_gmx` (The Graph subgraph, per-chain)                  | `fundingRateChangedEvents` — **event-driven** (fires on-chain rate-parameter change, not a fixed interval); Messari `financialsDailySnapshots` fallback only when native schema unreachable (daily-aggregate OI proxy, not raw)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | No on the native query (no OI field on the entity at all); Messari fallback has daily-aggregate USD OI but is a **fallback only**, not additive | **NO — genuine gap.** Rows are fetched but written ONLY as `data_type="perp_funding"`; no derivative_ticker write path exists anywhere in the handler. | NO — `defi_venue_capabilities.py:176-177` declares `perp_funding` only                                                                                                                                                                                                                            | `cli/handlers/_perp_funding_gmx.py:115-130` (`_GMX_FUNDING_QUERY`, no OI field), `:213-224` (`validate_before_write(...,"perp_funding",...)` + `write_defi_rows(..., data_type="perp_funding")` — sole write) | **ACTION: wire it.** Highest resolution GMX genuinely offers = the SAME `fundingRateChangedEvents` rows already being fetched for perp_funding — dual-write them under `derivative_ticker` too (no new API calls), OI/mark/index left null. This is the "GMX via The Graph may not have OI" case the ruling anticipated — confirmed true, OI nullable per ruling.                               |
| PACIFICA-SOLANA                           | `_route_pacifica` (unconditional REST)                | same                                                            | Per-settlement via `/funding_rate/history` REST                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | No                                                                                                                                              | YES                                                                                                                                                    | YES — `market_data_categories.py:1363-1367`, start `2025-06-01`                                                                                                                                                                                                                                   | `adapters/_umi_pacifica.py:236-288`                                                                                                                                                                           | **Already correct.** No action.                                                                                                                                                                                                                                                                                                                                                                 |
| EXTENDED-STARKNET                         | `_route_extended` (unconditional REST)                | same                                                            | Per-settlement (hourly) via `/info/{symbol}/funding` REST                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | No                                                                                                                                              | YES                                                                                                                                                    | YES — `market_data_categories.py:1368-1372`, start `2024-10-01`                                                                                                                                                                                                                                   | `adapters/_umi_extended.py:210-280`                                                                                                                                                                           | **Already correct.** No action.                                                                                                                                                                                                                                                                                                                                                                 |
| LIGHTER-ZKSYNC                            | `_route_lighter` — Tardis for `date >= 2026-04-17`    | same (batch=live, same routing fn)                              | Tardis `datasets.tardis.dev/v1/lighter/derivative_ticker/...` — real `funding_rate`/`mark_price`/`index_price`/`open_interest` fields, confirmed live 2026-07-07 (comment in code). Native REST adapter (`_umi_lighter.py`) has **zero** funding code — only trades/book_snapshot_5/candles — so pre-2026-04-17 dates have NO funding source via this venue at all. A separate public unauthenticated snapshot endpoint (`GET mainnet.zklighter.elliot.ai/api/v1/funding-rates`, verified live via curl this session — returns `exchange="lighter"` rows with a `rate` field) exists but is NOT wired anywhere and has no historical depth or per-row timestamp (current-snapshot only) — dead end, Tardis is the real production path. | Yes (Tardis)                                                                                                                                    | YES (via Tardis, date-gated)                                                                                                                           | **YES but WRONG DATE** — `market_data_categories.py:1373-1377` declares start `2024-08-01`, but that predates Tardis's actual coverage-start (`2026-04-17`) for this exchange+dataType by ~20 months; the enumerator would schedule dates in that window against a source with nothing to return. | `adapters/umi_tick_provider.py:356-405` (`_route_lighter`, Tardis gate `if date >= "2026-04-17"` at :380, comment at :379-390); `adapters/_umi_lighter.py` full-file grep = zero funding hits                 | **ACTION: registry-only fix — correct the start date** `2024-08-01` → `2026-04-17`. No new capture code (already wired via Tardis).                                                                                                                                                                                                                                                             |
| MANGO-SOLANA / ZETA-SOLANA / FLASH-SOLANA | none                                                  | none                                                            | No MTDS adapter of ANY kind exists (not trades, not book, not derivative_ticker) — only a URDI reference-data adapter key (`venue_adapter_keys.py:224-226`) for instrument-universe resolution, zero market-data capture footprint                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Unknown (no source integration attempted)                                                                                                       | NO                                                                                                                                                     | NO                                                                                                                                                                                                                                                                                                | grep across `market-tick-data-service` for MANGO/ZETA/FLASH_TRADE = 0 hits; grep across UAC `VENUES_BY_ASSET_GROUP`/`DEFI_VENUE_DATA_TYPE_CAPABILITIES`/`market_data_categories.py` = 0 hits                  | **OUT OF SCOPE for this issue.** This is not a "missing derivative_ticker" gap — it's a from-scratch full-adapter build (unknown source API shapes, no in-repo precedent) for 3 venues with zero existing capture infrastructure. Flagging as a separate future finding rather than actioning here (matches "External data is always available" — build-the-scaffold-later, not silently drop). |
| KALSHI-PERP / POLYMARKET-PERP             | n/a                                                   | n/a                                                             | n/a                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | n/a                                                                                                                                             | n/a                                                                                                                                                    | n/a                                                                                                                                                                                                                                                                                               | `registry/venue_constants.py:604-605` (PERP_TRADE capability only)                                                                                                                                            | **Out of scope by venue-list.** CFTC-regulated prediction-platform perp CLOBs (cefi asset_group), not on-chain DeFi perp DEXes — structurally distinct product, not named in the operator ruling's on-chain-settlement framing. Not actioned.                                                                                                                                                   |

**Scope pinned by this table (todo 2):** GMX-ARBITRUM/GMX-AVALANCHE get real new capture code (dual-write
derivative_ticker from the existing `fundingRateChangedEvents` fetch). DRIFT-SOLANA and LIGHTER-ZKSYNC get
UAC-registry-only fixes (declare/correct the capability cell; the capture code already exists and works).
HYPERLIQUID/ASTER/PACIFICA-SOLANA/EXTENDED-STARKNET need no changes. MANGO/ZETA/FLASH-SOLANA and
KALSHI-PERP/POLYMARKET-PERP are out of scope (documented above, not silently dropped).

## Todos

- [x] [SCRIPT] P1. Enumerate derivative_ticker coverage per DeFi perp venue (DRIFT-SOLANA, HYPERLIQUID, ASTER, GMX,
      PACIFICA, EXTENDED, LIGHTER, + any other `instrument_type=perpetual` venue in the registry): live + batch capture
      paths present or missing, source's available resolution (settlement events / tick stream / poll), whether the
      source exposes OI. Append the coverage table here. Repo: market-tick-data-service (read-only pass). — DONE
      2026-07-15, unified-trading-pm (this doc, table above); no code changed, pure enumeration.
- [x] [CODE] P1. Wire `derivative_ticker` capture for every perp venue missing it, at the highest resolution the source
      offers — per the ruling this INCLUDES venues with no OI at the source (OI/mark/index fields nullable;
      funding_rate + ts_event mandatory). Update UAC expected-coverage/registry so the manifest expects the new (venue,
      derivative_ticker) cells; enumerator picks them up via the standing daily crons. Live=batch: same code path both
      modes. Repo: market-tick-data-service + unified-api-contracts. — DONE 2026-07-15,
      unified-api-contracts@2170b388d8901a22f17cc2b59245a4b9894671e4 +
      market-tick-data-service@5f659c12b4eeed348aea2abe657714c2c9b226df. GMX-ARBITRUM/GMX-AVALANCHE: real new code
      (`_perp_funding_gmx.py` dual-writes derivative_ticker from the SAME `fundingRateChangedEvents` fetch used for
      perp_funding — zero extra API calls; per-(chain, data_type) freshness/manifest recording so one data_type being
      fresh never masks the other) + new `DEFI_PERPETUAL_DERIVATIVE_TICKER` SchemaContract (write_defi_rows was raising
      `SchemaContractNotFoundError` — no contract existed for defi+derivative_ticker at all) +
      capability/expected-coverage declarations (start dates match the existing perp_funding floor — same source).
      DRIFT-SOLANA + LIGHTER-ZKSYNC: registry-only fixes — code was ALREADY wired (drift_adapter.py's
      `fetch_drift_data`/Tardis respectively) but the UAC capability cell was missing (Drift) or wrong (Lighter,
      declared 2024-08-01, corrected to 2026-04-17 — the real Tardis coverage-start). Evidence:
      `quality-gates.sh --no-fix` green on both repos (MTDS: 6110 passed, 1 pre-existing unrelated WARN filed as
      `mtds_solana_defi_drift_adapter_contract_baseline_stale_2026_07_15.md`; UAC: full PASS). New unit tests:
      `test_perp_funding_handler.py::TestGmxCanonicalWrite::test_derivative_ticker_dual_write_row_shape` + updated
      freshness/failure-fanout assertions in `test_perp_funding_handler_coverage.py`.
- [x] [CODE] P2. Remove the Drift-only `funding_rate_24h/7d/30d` aggregates from the `perp_funding` write path (keep
      `funding_rate` + `annualized_rate` per the canonical schema — annualizing is explicitly fine). Aggregation windows
      belong downstream (features), not in raw capture. Decide + document disposition of already-written rows carrying
      the extra columns (reader tolerance vs restamp; prefer tolerance if readers project columns). DO NOT disrupt the
      currently-running backfill VM — land for future runs. Repo: market-tick-data-service. — DONE 2026-07-15,
      market-tick-data-service@5f659c12b4eeed348aea2abe657714c2c9b226df. `_collect_drift` (solana_defi_drift.py) now
      emits `funding_rate` (= the 24h window, the finest-grained field `/stats/markets` offers) + `annualized_rate`
      (`funding_rate * 365` — a unit conversion of ONE rate, not a window average) instead of the three window columns.
      Verified this does NOT touch the currently-running `mtds-solana-drift-backfill` VM: that VM launches with
      `VM_TASK=solana-drift-backfill` → `--solana-drift-backfill` → routes to `_backfill_drift_s3_date`/
      `_backfill_drift_helius_date`, a genuinely separate function in the same file that this edit does not touch —
      `_collect_drift` is only reached by the handler's DEFAULT (non-backfill) branch. Disposition: READER TOLERANCE —
      `schema_validation.py`'s `perp_funding` required-columns spec already accepts `funding_rate_24h` as an alternative
      to `funding_rate` (pre-existing, kept as-is for legacy/Helius-placeholder rows), so old + new rows both validate;
      no historical GCS restamp. Test: `test_solana_defi_handler.py::TestCollectDrift::test_parses_drift_response`
      updated to assert the new fields + absence of the retired ones.
- [x] [VERIFY] P1 — **MOOT 2026-07-16** (operator ruling: DRIFT-SOLANA removed entirely, all Solana perp DEXes dropped
      except Jupiter, not integrated). The DRIFT-gating condition can never resolve — no DRIFT backfill exists anymore.
      Cross-source funding parity for the SURVIVING venues (HYPERLIQUID/ASTER/GMX/...) is not gated and can be re-scoped
      as a fresh todo if still wanted. Original: (GATED on the DRIFT perp_funding backfill completing its
      2025-01→2026-07 grind). Cross-source funding parity: per (venue, market, funding interval),
      `perp_funding.funding_rate` vs the `derivative_ticker` settlement row within ε; DRIFT-SOLANA/HYPERLIQUID/ASTER
      first; honest report (match %, divergence distribution, worst offenders) appended here; genuine divergences filed
      per findings-triage. Repo: market-tick-data-service (read-only analysis script with lifecycle marker).
- [x] [DOCS] P2. Codex updates recording the ruling: `defi-data-type-taxonomy.md` + `defi-data-types-catalog.md` §4 (+
      derivative_ticker section) + `data-lineage-MTDS-features-ml.md` — derivative_ticker = canonical raw-funding home
      for ALL perps (highest resolution, OI-optional); perp_funding = the per-interval canonical view with
      annualized_rate; no venue-specific raw-layer aggregates. Repo: unified-trading-pm. — DONE 2026-07-15 (this
      commit): `defi-data-type-taxonomy.md` (Perp family + new per-venue derivative_ticker coverage table in the "Perp
      (DeFi-side...)" section), `defi-data-types-catalog.md` (§4 perp_funding rewritten for the retirement +
      divergence-removal + reader-tolerance disposition; new §4a derivative_ticker entry),
      `data-lineage-MTDS-features-ml.md` (new Layer-1 defi-axis derivative_ticker row + bypass-types table row).

- [ ] [DESIGN] P1 [GATE NO LONGER SATISFIABLE AS WRITTEN — see note]. **Decide: demote `perp_funding` from a captured
      raw type to a DERIVED interval view.** Note (2026-07-25 reconciliation): this todo was originally gated on "todo
      4's parity results", but todo 4 (the cross-source funding-parity `[VERIFY]` item, above) closed `[x]` as **MOOT
      2026-07-16** with no parity check ever run — it explicitly states parity for the surviving venues "is not gated
      and can be re-scoped as a fresh todo if still wanted." No parity data exists or is queued, so this gate can never
      resolve as literally written. Before executing this DESIGN decision, either (a) file the re-scoped cross-source
      parity todo (HYPERLIQUID/ASTER/…; GMX removed 2026-07-25, see
      `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md` — drop it from the venue set) that todo 4's MOOT
      note anticipates and gate on ITS results, or (b) route straight to an operator decision on whether parity evidence
      is still required before demoting `perp_funding`. Rationale (operator discussion 2026-07-15): with
      derivative_ticker now the canonical raw funding home for ALL perps, `perp_funding` is derivable everywhere — for
      interval-native sources (Hyperliquid REST, GMX events) the two are literally the same rows written twice (the GMX
      dual-write in todo 2 proves it: same rows, zero extra API calls); for event-native sources (Drift) perp_funding is
      an aggregate of the settlements. No perp venue class structurally requires a separate funding capture (no defi
      perp venue is an AMM in the Uniswap sense — Drift/Hyperliquid are CLOBs; GMX is pool-as-counterparty but still
      emits funding as EVENTS). If todo 4's parity holds within ε, the dual-capture is pure redundancy + a permanent
      parity-policing burden. **Scope of the decision** (do NOT execute before the parity evidence exists): (a) migrate
      features-onchain's `perp_funding` BYPASS read (`data-lineage-MTDS-features-ml.md`) to the derived view or to
      derivative_ticker directly; (b) re-home the `mvp_backfill_defi_onchain_v10` MVP gate accounting — perp_funding is
      one of its 6 gate data_types with months of manifest history, so the shard atom + coverage denominator
      implications must be worked through, not hand-waved (honest-coverage model: a retired data_type's historical rows
      stay, they don't vanish); (c) stop capturing perp_funding raw once (a)+(b) land. If parity FAILS, this todo closes
      as "keep both — parity report explains why". Repos: market-tick-data-service, features-service,
      unified-api-contracts. **Gated on the new re-scoped parity todo directly below (resolved
      `autonomous_session_operator_decisions_2026_07_25.md` entry #4, option A) — do not execute until it reports.**
- [x] [VERIFY] P2. **Re-scoped cross-source funding-parity check** (replaces the original todo-4 parity check, which
      closed MOOT 2026-07-16 with no data collected). Surviving venue set per the 2026-07-25 removals: HYPERLIQUID,
      ASTER only (GMX removed 2026-07-25 — `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`; DRIFT/PACIFICA
      already removed prior). Per (venue, market, funding interval): compare `perp_funding.funding_rate` against the
      `derivative_ticker` settlement row within ε; append an honest report here (match %, divergence distribution, worst
      offenders). This is the sole gate for the DESIGN todo above — resolves it whichever way the evidence points
      (parity holds → proceed with the demote scope; parity fails → close DESIGN as "keep both", explain why). Repo:
      market-tick-data-service (read-only analysis script with lifecycle marker). — already covered by
      defi_satellite_ao_dispatch_batch1_2026_07_25.md (see that doc for execution).
- [x] ✅ [OPERATOR-DECISION] P2. MANGO-SOLANA / ZETA-SOLANA / FLASH-SOLANA are half-onboarded (IS reference-data
      adapters + factory registration + tests exist; zero MTDS capture; not in the venues list /
      `VENUES_BY_ASSET_GROUP`). Decide: (A) complete onboarding, or (B) delete the whole vertical slice. — **RULED (B)
      DELETE, operator 2026-07-15**: _"OK so let's kill them all — clear them from everything, delete any data from them
      and catalogue/MVP/manifest entries. They are useless. Without exception."_ EXECUTED + VERIFIED:
      **`instruments-service@9f7ffb27`** (3 adapters + factory imports/registrations + 3 metadata test files deleted;
      cases pruned from the 3 shared test files; docs updated; QG green) · **`unified-api-contracts@70e7a697`**
      (`venue_adapter_keys.py` 3 venue keys + `_defi_chain_data.py` 3 `SOLANA_DEFI_PROTOCOLS` entries removed, with
      tombstone comments carrying the ruling + evidence so they cannot be silently re-added; QG green 310s, sentinel ==
      HEAD `7754661a`) · **codex `unified-trading-pm@fbe7d7941`** (5 docs) · **data side
      `unified-trading-pm@dba7a5545`** (VERIFIED-ZERO: catalogue 10,387 rows / manifest 27,955,143 rows / bounded raw
      tick scan / BigQuery — nothing existed to purge; no purge script needed). **Verification** (coordinator,
      2026-07-15 18:3x): live-code blast-radius grep across all 6 code repos = **ZERO hits** (only the intended
      tombstone COMMENTS remain); the 3 adapter files confirmed absent from disk;
      `from instruments_service.reference_data.factory import *` → `factory imports OK` (no dangling imports).
      **Token-vs-venue guard HELD**: `ZETA` still present in `cefi_instrument_universe.py` and the data agent confirmed
      14 legitimate MNGO/ZETA **token** rows across 9 CeFi venues (BINANCE-FUTURES/BYBIT/HYPERLIQUID/KRAKEN/ OKX/…)
      untouched — every query scoped to the `venue` column, never a symbol substring. `FLASHBOTS` (distinct MEV relay)
      and a coincidental base58 address containing "Zeta" also correctly preserved.

- [x] [CODE] P1 — **MOOT 2026-07-16** (operator ruling: DRIFT-SOLANA removed entirely, all Solana perp DEXes dropped
      except Jupiter, not integrated). `drift_adapter.py` itself was deleted in the same landing
      (`market-tick-data-service` sibling task) — there is no adapter left to repoint to the working CSV path. Original
      finding, kept for record: **DRIFT derivative_ticker funding endpoint is DEAD (403) — measured 2026-07-16.** The
      endpoint `market-tick-data-service/market_tick_data_service/adapters/drift_adapter.py:12` documents and uses —
      `GET https://data.api.drift.trade/fundingRates?marketName={SYMBOL}-PERP&limit=2400` — now returns **HTTP 403
      `{"message":"Forbidden"}`** (probed live, both with and without `limit`). WORKING replacement found in the same
      probe: the per-day CSV form
      `GET https://data.api.drift.trade/market/{MARKET}/fundingRates/{YYYY}/{MM}/{DD}?format=csv` → HTTP 200 with real
      data (e.g. SOL-PERP 2025-01-09 → 6,956 B), covering genesis 2022-11-04 → ~2026-03-31. Repo:
      market-tick-data-service.

## Progress log

- 2026-07-15 (coordinator, autonomous close-out) — **CI-verified fleet-green; one real ordering defect found + fixed.**
  The consumer-first ship order I dispatched (instruments-service BEFORE unified-api-contracts) INVERTED the cross-repo
  invariant `UAC VENUE_TO_ADAPTER_KEY ⊆ IS factory._ADAPTERS`: is@9f7ffb27 removed the adapter classes at 17:48 while
  UAC still declared the 3 venue keys, so instruments-service CI run 29440517050 (sha 1aeb5e3c, 18:26Z) went RED on
  `test_adapter_routing_uac_invariant::test_every_uac_adapter_key_resolves_to_a_class` +
  `test_factory_comprehensive::test_adapter_data_sources_covers_all_adapters` for a ~50-minute window. Root cause was
  the ORDER, not the deletion: for a "provider declares, consumer implements" invariant the PROVIDER (UAC) must shed the
  declaration FIRST, or both repos must land inside one promotion. Closed by uac@70e7a697 (18:40Z); verified directly
  (`VENUE_TO_ADAPTER_KEY` ∩ {MANGO,ZETA,FLASH} = ∅; only the pre-existing `__no_adapter_yet__` sentinels remain, which
  the tests allowlist via known_gaps), then the SAME failing run's workflow was manually re-dispatched (rule 10) → run
  29441021802 sha 1aeb5e3c **conclusion=success**. unified-api-contracts CI green both runs. **Lesson for the next venue
  removal** (worth honouring, this class recurs): ship the UAC registry deletion FIRST, then the IS adapter deletion —
  or accept a red consumer window and say so up front.

- 2026-07-15: Filed from the operator's ruling in the main session, following the funding dual-capture investigation
  (perp_funding vs derivative_ticker). Parity check deliberately gated on the DRIFT backfill grind finishing so it
  compares complete data.
- 2026-07-15 (main session, operator Q): "Why does perp_funding need to exist whilst derivative_ticker exists?" —
  answered + captured as the new parity-gated [DESIGN] P1 todo above (demote-to-derived-view decision). Also asked why
  MANGO/ZETA/FLASH-SOLANA appeared in the coverage table when they are not in the venues list: they surfaced because the
  todo-1 sweep was scoped to "any perpetual venue in the registry" and those three have `venue_adapter_keys.py` entries.
  **Correction to a claim the coordinator made in chat**: those keys are NOT dead/orphan pointers — a blast-radius audit
  found REAL instruments-service reference-data adapters behind them
  (`reference_data/adapters/defi/{mango,zeta,flash_trade}.py`, ~8-9 KB each, registered in `reference_data/factory.py`
  :137/150/182, with unit tests). The true state is a **half-onboarded vertical**: IS reference-data (instrument
  universe) exists; MTDS market-data capture and venues-list membership do not. Deleting only the adapter keys would
  break the IS factory. Operator decision pending (see the `[OPERATOR-DECISION] P2` todo above) — nothing deleted.
- 2026-07-15: Todos 1/2/3/5 completed (todo 4 stays gated per its own condition — the DRIFT backfill grind). Coverage
  table (todo 1) pinned scope before any code was written. Shas:
  unified-api-contracts@2170b388d8901a22f17cc2b59245a4b9894671e4,
  market-tick-data-service@5f659c12b4eeed348aea2abe657714c2c9b226df. Side-finding filed (pre-existing, unrelated,
  warn-only): `plans/archive/issues/mtds_solana_defi_drift_adapter_contract_baseline_stale_2026_07_15.md`.
- 2026-07-15 (operator ruling, verbatim): "OK so let's kill them all — clear them from everything, delete any data from
  them and catalogue/MVP/manifest entries. They are useless. Without exception." This resolves the
  `[OPERATOR-DECISION] P2` todo above to **option (B) — delete the whole vertical slice.** Split across two agents: CODE
  side (IS adapters + UAC registry + codex) owned by a sibling agent; **DATA/STATE side (this entry) verified every
  GCS/BQ surface read-only and found NOTHING to purge** — the "half-onboarded" framing was accurate: IS reference-data
  adapters existed in code but were never actually invoked (not in `VENUES_BY_ASSET_GROUP`, so the standing orchestrator
  never scheduled them), so zero rows were ever written anywhere. Full surface-by-surface evidence:
  - **Instrument catalogue** (`instruments-store-defi-prd-central-element-323112`): downloaded + duckdb-queried the LIVE
    canonical `prod/catalog.parquet` (env=`prod`, per `build_instrument_catalogue.py`'s `DEPLOYMENT_ENV` default;
    updated 2026-07-15T01:01:36Z, 10,387 rows) —
    `select distinct venue from catalog where upper(venue) like '%MANGO%' or '%ZETA%' or '%FLASH%'` → **0 rows**.
    Cross-checked the stale `prd/catalog.parquet` (7,223 rows, updated 2026-06-28) and the legacy
    `reference_data/instruments/asset_group=defi/written_at=2026-05-23T13:03:49Z/ all.parquet` snapshot (9,820 rows) —
    both **0 rows** too. **VERIFIED ZERO — no purge.**
  - **Availability manifest** (`market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`,
    downloaded to a uniquely-named scratchpad file per this session's namespace-collision note, updated
    2026-07-15T16:58:47Z, 27,955,143 rows spanning 2020-01→2026-07): checked both glued (`MANGO-SOLANA` etc.) and bare
    (`MANGO`/`ZETA`/`FLASH`/`FLASH_TRADE`) venue spellings, exact-match and substring — **0 rows** for all three
    targets. The only substring hit was `FLASHBOTS` (24,777 `empty_confirmed` rows, asset_group=defi, chain=ETHEREUM,
    data_types incl. dex_pool_swaps/oracle_prices/perp_funding) — a genuinely distinct MEV-relay venue, **not** Flash
    Trade; left untouched. Also confirmed this manifest partitions `venue`+`chain` separately (bare protocol name, e.g.
    `DRIFT`+`SOLANA`, not glued `DRIFT-SOLANA`) — the exact-match query covered both conventions. **VERIFIED ZERO — no
    purge.**
  - **Raw tick data** (`market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/...`): two literal
    recursive wildcard walks (`day=*/pipeline_mode=*/asset_group=defi/venue=<X>/**`) timed out (>90s / >2min each) —
    correctly abandoned rather than forced through, since that is exactly the whole-corpus GCS walk the single-walk
    discipline flags as review-blocking. Substituted a bounded, targeted scan: queried the manifest for which
    `pipeline_mode` values real Solana perp-DEX peers (DRIFT, PACIFICA) actually use
    (`batch_hyperliquid`/`batch_onchain_rpc`/`batch_onchain_subgraph`/`batch_pyth_hermes`/`batch_solana_rpc` — pipeline
    modes here name the SOURCE MECHANISM, not the venue, so venue-named-directory guessing would have been wrong), then
    listed `asset_group=defi/` under each of those 5 modes on 7 sample days spanning 2025-01-15→2026-07-14 (incl. today)
    — **0 venue=MANGO/ZETA/FLASH matches on any sampled day/mode combo.** Also fully enumerated the small legacy
    `dex_pools/` (kamino, orca, raydium) and `lending_indices/` (kamino, solend) namespaces — **0 matches**. **VERIFIED
    ZERO (bounded evidence, not a full walk) — no purge.**
  - **Other state** (workspace-wide, bounded): `rg` across every non-IS, non-PM-codex repo (deployment-api,
    deployment-service, deployment-ui, market-tick-data-service, market-data-processing-service,
    unified-trading-system-ui, ml-service, execution-service, strategy-service, features-service) for the 3 venue
    strings (glued + bare, quoted literals) — **0 hits** anywhere in code or `.yaml`/`.yml`/`.json` config. BigQuery:
    `bq ls` across `market_tick`/`market_tick_asia`/`market_data`/`features`/`market_data_candles_derivative_ticker` —
    **0 matching table names.** One coincidental false-positive investigated: `_cache/ solana_creation_timestamps.json`
    (instruments-store-defi bucket, a generic on-chain-address→creation-timestamp cache, NOT venue-keyed) contains the
    key `ooXZetAXMwzvbQ4fJrv8KjCkhb2JkbdDeVMBWjHTg6B` — a Solana account/pool address whose base58 encoding happens to
    contain the 4-char substring "Zeta"; this is NOT the real Zeta Markets program ID and is unrelated to the
    ZETA-SOLANA venue — left untouched (correctly not purged; recorded here so it is not re-flagged as a miss). The only
    real references to the 3 venues anywhere in the workspace are
    `unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py` (sibling's file — confirmed via
    `git status` mid-edit, `M` not yet committed at time of this check) and PM `codex/` docs (sibling's to update) plus
    2 archived plans (historical, no action).
  - **Scope-guard sanity check** (confirms MNGO/ZETA-as-token rows were never at risk): queried the CeFi instruments
    catalogue (`instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`) for
    `base_asset in ('MNGO','ZETA')` — found **14 legitimate rows across 9 real CeFi venues** (BINANCE-FUTURES,
    BITFINEX-SPOT, BITGET-FUTURES/SPOT, BYBIT/BYBIT-SPOT, COINBASE-FUTURES/SPOT, HYPERLIQUID, KRAKEN-FUTURES/SPOT,
    OKX-SPOT/SWAP, UPBIT) — all untouched, as expected, since every purge-surface query in this pass was scoped strictly
    to the `venue` column (never a `base_asset`/`raw_symbol` substring match).
  - **Purge script: NONE WRITTEN** — every surface came back verified-zero, so per the task's own instruction ("If
    NOTHING needs purging, write NO script") there is nothing to purge, snapshot, or roll back. The
    `_index/ snapshots/pre_<slug>_<ts>.parquet` / consolidator-pause / dry-run/apply ICE-purge precedent
    (`market-tick-data-service/market_tick_data_service/scripts/purge_tradfi_ice_non_24h_2026_07_14.py`) was read as
    reference but not needed — it applies when rows are FOUND, not when the surface is already clean.
  - **Net effect**: the operator's "kill them all... delete any data... catalogue/MVP/manifest entries" ruling is
    ALREADY fully satisfied on the data/state side — there was never any data to delete. Completion of the overall
    ruling is gated only on the sibling agent's CODE-side deletion (IS adapters + UAC registry + codex), which was
    observed mid-flight (staged `git rm` on
    `instruments-service/instruments_service/reference_data/adapters/defi/ {mango,zeta,flash_trade}.py` + their tests,
    `unified-api-contracts/unified_api_contracts/registry/ venue_adapter_keys.py` modified, both uncommitted) at the
    time of this check — not committed/shipped by this agent, per the collision-avoidance instruction to not touch the
    sibling's repos.
