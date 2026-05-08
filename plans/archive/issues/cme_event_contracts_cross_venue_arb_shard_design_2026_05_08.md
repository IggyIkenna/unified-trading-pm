---
title:
  "CME event contracts (ECES/ECNQ/ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E/ECBTC) — captured-as-OPTION but NOT linked to
  canonical_question_group; cross-venue arb (CME ↔ Polymarket binary outcomes) blocked by asset_group / shard-atom
  classification ambiguity + missing dedicated InstrumentType.EVENT_CONTRACT"
created: 2026-05-08
author: ikenna
source:
  - unified-api-contracts/unified_api_contracts/registry/tradfi_instrument_universe.py:237-264 (_CME_EVENT_CONTRACTS — 9
    roots, classified as OPTION, Databento coverage start 2025-09-28)
  - unified-api-contracts/unified_api_contracts/registry/tradfi_instrument_universe.py:277 (TRADFI_DATABENTO_INSTRUMENTS
    aggregate includes event contracts implicitly)
  - market-tick-data-service/.../adapters/tradfi/databento_classifier.py (DatabentoClassification.instrument_type — no
    EVENT_CONTRACT entry)
  - unified-api-contracts/unified_api_contracts/canonical/domain/predictions/canonical_groups.py (CanonicalQuestionGroup
    enum — Polymarket-side canonical for SPX_UP_DOWN_DAILY etc.)
  - deployment-service/scripts/vm/vm_zombie_watchdog.py (comment "CME event-contract backfill (TradFi)" — anticipated
    but no plan)
  - operator directive 2026-05-08:
      "do we have instrument definitions for the event markets for CME through Data Bento? the binary option stuff which
      we could arb with polymarket even though its new and illiquid"
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# CME event contracts cross-venue arb shard design

> **Severity**: P1 — captured today (Databento via OPTION shard atom) but not arb-strategy-ready; blocks any CME ↔
> Polymarket binary-outcome arb because the two venues' canonical question groups don't currently link. Doesn't strictly
> block May 23 cutover if first archetypes don't trade event contracts, but the data IS flowing — wiring it up correctly
> costs little vs the option value of cross-venue arb later. **Blast radius**: UAC tradfi instrument universe (dedicated
> `InstrumentType.EVENT_CONTRACT`) + UAC predictions canonical_groups (link CME event-contract roots to existing
> canonical groups OR introduce TradFi-side canonical-group equivalents) + instruments-service TradFi adapter
> (per-cluster expiry handling for daily binary contracts) + MTDS Databento path (binary-outcome shard atom + cluster
> validation per (root, expiry-day)) + MDPS (binary-outcome OHLCV / mid-price candle treatment) + strategy-service
> (cross-venue arb archetype declaration with CME + Polymarket as paired legs) + execution-service (CME ClearPort
> connector for the TradFi leg). **Suggested owner**: split between `tradfi_master_2026_05_07.md` (dedicated
> InstrumentType + arb-leg metadata) and `predictions_master_2026_05_07.md` (canonical_question_group linkage).
> Recommend a **shared sub-plan** since the value lives at the boundary.

## What I found

The 2026-05-08 audit (Q1-Q5 of the prediction-markets follow-up) confirmed CME event contracts ARE in the workspace
registry but classified as `OPTION` with no link to prediction's canonical_question_group taxonomy.

### Q1 — UAC has 9 CME event-contract roots, but classified as OPTION

[tradfi_instrument_universe.py:237-264](../../../unified-api-contracts/unified_api_contracts/registry/tradfi_instrument_universe.py#L237-L264):

```python
# CME Event Contracts — binary YES/NO settlement on macro/financial underliers.
# Same shape as Polymarket / Kalshi / Opinion binary markets
# Databento classifies them as OPTIONS (parent symbology with `.OPT` suffix).
# Coverage on Databento: 2025-09-28 onward
_CME_EVENT_CONTRACTS: list[DatabentoInstrumentDef] = [
    DatabentoInstrumentDef("ECES.OPT",  "CME", "OPTION", "GLBX.MDP3", "parent", "SP500",       "equity",    "ECES"),
    DatabentoInstrumentDef("ECNQ.OPT",  "CME", "OPTION", "GLBX.MDP3", "parent", "NASDAQ100",   "equity",    "ECNQ"),
    DatabentoInstrumentDef("ECRTY.OPT", "CME", "OPTION", "GLBX.MDP3", "parent", "RUSSELL2000", "equity",    "ECRTY"),
    DatabentoInstrumentDef("ECYM.OPT",  "CME", "OPTION", "GLBX.MDP3", "parent", "DOW",         "equity",    "ECYM"),
    DatabentoInstrumentDef("ECGC.OPT",  "CME", "OPTION", "GLBX.MDP3", "parent", "GOLD",        "commodity", "ECGC"),
    DatabentoInstrumentDef("ECCL.OPT",  "CME", "OPTION", "GLBX.MDP3", "parent", "CRUDE",       "commodity", "ECCL"),
    DatabentoInstrumentDef("ECNG.OPT",  "CME", "OPTION", "GLBX.MDP3", "parent", "NATGAS",      "commodity", "ECNG"),
    DatabentoInstrumentDef("EC6E.OPT",  "CME", "OPTION", "GLBX.MDP3", "parent", "EUR",         "fx",        "EC6E"),
    DatabentoInstrumentDef("ECBTC.OPT", "CME", "OPTION", "GLBX.MDP3", "parent", "BTC",         "crypto",    "ECBTC"),
]
```

**Captured but indistinguishable from vanilla options at the type level.** `instrument_type=OPTION` is shared with
ES.OPT / SPX.OPT / etc. Every downstream feature / strategy that filters by `instrument_type` either:

- Treats event contracts as if they were vanilla options (wrong — payoff is binary, not piecewise-linear; greeks don't
  apply the same way).
- Has a special-case branch on root prefix `EC*` (brittle, scattered).

The comment "Same shape as Polymarket / Kalshi / Opinion binary markets" explicitly acknowledges the cross-venue
equivalence but doesn't wire the canonical link.

### Q2 — instruments-service captures via standard Databento adapter, no event-contract gating — but per-strike CATALOG ROWS DO flow

The TradFi Databento adapter iterates `TRADFI_DATABENTO_INSTRUMENTS` (line 277 of the same file). Event contracts flow
through implicitly. No explicit "this is a binary contract" branch. Means cluster validation for event contracts uses
options-style assumptions (per-root expiry tree with strikes) which doesn't match event contracts' actual structure
(per-root, per-day-of-resolution, per-strike-threshold YES/NO pair).

**Important confirmation (2026-05-08 follow-up audit)**: per-strike catalog rows ARE flowing today.
[databento.py:719-774](../../../instruments-service/instruments_service/reference_data/adapters/tradfi/databento.py#L719-L774)
fetches with `stype_in="parent"` for `ECBTC.OPT` etc., which expands to all child symbols. Each child returns its own
strike + expiry + outcome metadata via
[`_parse_row_to_record`](../../../instruments-service/instruments_service/reference_data/adapters/tradfi/databento.py#L811)
(line 811) → unique `instrument_key=f"{venue}:{type}:{raw_symbol}"` (line 1022). For ECBTC daily binary with 4 strikes
(60K, 65K, 70K, 75K) × 2 outcomes (YES/NO), instruments-service writes 8 InstrumentRecords per resolution date.

So **the catalog backing is in place** — what's missing is the SEMANTIC layer (instrument_type = EVENT_CONTRACT instead
of OPTION, linked_canonical_question_group cross-link, binary-outcome-shaped cluster validation). The data IS there;
downstream consumers just can't reason about it correctly because it's labelled as a vanilla option.

### Q3 — MTDS pulls GLBX.MDP3 for event contracts; standard TradFi shard key

Shard atom: `(asset_group=tradfi, venue=CME, data_type, instrument_type=OPTION, root=ECES/ECBTC/etc., day)`. Bundles by
root per the existing options-chain bundling rule (CLAUDE.md "Per-asset-group shard-key matrix" `tradfi options` row).
Cluster validation uses 11-cluster ES.OPT taxonomy precedent — wrong for binary contracts whose cluster shape is
`(root, resolution_date, strike_threshold)`.

### Q4 — Asset_group classification is DECISION-PENDING

CME event contracts have:

- **Venue**: CME ClearPort (regulated TradFi exchange)
- **Source**: Databento GLBX.MDP3 (TradFi data feed)
- **Payoff**: Binary YES/NO on underlying close level — identical to Polymarket BTC_UP_DOWN_DAILY / SPX_UP_DOWN_DAILY

The CLAUDE.md shard-key matrix forces a single `asset_group` per row. Three options:

- **Option A — Pure TradFi**: keep `asset_group=tradfi`, `instrument_type=OPTION`. Add `is_binary_outcome: bool` flag on
  the instrument schema. Cross-venue arb features compute by joining
  `(tradfi BTC event contract, polymarket BTC_UP_DOWN canonical_group)` via underlying + resolution_date.
- **Option B — Pure Prediction**: re-classify under `asset_group=prediction`, treat CME as a venue alongside POLYMARKET
  / KALSHI / OPINION. Sub-shard by canonical_question_group. Means TradFi compliance / settlement layer (CME ClearPort
  cleared products are CFTC-regulated US-domestic-eligible) is awkwardly attached to a prediction shard.
- **Option C — Dual-shard**: write to BOTH shard atoms (tradfi for compliance + prediction for strategy routing).
  Manifest carries 2x rows for the same source data. Maintenance overhead but clean separation of concerns.

**Recommended: Option A + soft cross-link.** Keep the tradfi shard atom for capture, add a new
`InstrumentType.EVENT_CONTRACT` (distinct from OPTION), AND add a
`linked_canonical_question_group: CanonicalQuestionGroup | None` field on the instrument schema that points to the
equivalent Polymarket canonical group. Strategy-service archetype pre-flight resolves both legs through the link.

### Q5 — Backfill NEVER RUN — adapter exists but instruments-service catalog is EMPTY for event contracts (CRITICAL)

The 2026-05-08 follow-up audit confirmed: **adapter existence ≠ catalog populated**. Despite UAC declaring coverage
start `2025-09-28` and Databento parent-stype expansion logic being in place, **no backfill VM has ever been launched
targeting CME event contracts**.

Evidence:

- **Zero git log references**: workspace search 2026-01-01 → 2026-05-08 finds zero commits mentioning `ECBTC`,
  `event contract`, `_CME_EVENT_CONTRACTS` in instruments-service backfill / VM-launch context.
- **No TradFi instruments forward-poll**: unlike CeFi which has
  [`launch-cefi-instruments-backfill.sh`](../../../deployment-service/scripts/vm/launch-cefi-instruments-backfill.sh)
  running daily across Hyperliquid + standard exchanges, **TradFi instruments-service has NO equivalent forward-poll
  launcher**. Each TradFi backfill is ad-hoc; no automation has run for ECBTC etc.
- **`launch-targeted-options-chain-backfill.sh`**
  ([commit a52f209 2026-05-05](../../../deployment-service/scripts/vm/launch-targeted-options-chain-backfill.sh))
  targets `options_chain` market-data — NOT instruments-service reference data. Different layer.
- **Operator confidence: LOW**. CME event contracts likely have ZERO rows in the instruments-service catalog today. If a
  strategy looks up `(venue=CME, root=ECBTC, resolution_date=2026-05-09)` for instrument metadata (strikes / expiry /
  settlement spec), the lookup fails.

### End-to-end chain failure — what data-status / manifest derivations look like today

The backfill chain has 4 layers; all 4 are broken downstream of the missing-backfill root cause:

| Layer                                                                   | Status                | What's broken                                                                                                                                                                                                                                                                                                                                                                                    |
| ----------------------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1. UAC `SOURCE_COVERAGE_START`/equivalent for tradfi Databento          | ✓ declared 2025-09-28 | (correct)                                                                                                                                                                                                                                                                                                                                                                                        |
| 2. instruments-service catalog rows per (root, expiry, strike, outcome) | ✗ EMPTY               | Backfill never run; adapter exists but unexercised                                                                                                                                                                                                                                                                                                                                               |
| 3. Manifest's `expected_universe` for tradfi event contracts            | ✗ missing             | Writegate v2 enumerator (Phase 3.D.5 Wave 3) derives from catalog × dates × data_types — empty catalog → empty expected universe → no `expected_unattempted` rows pre-populated                                                                                                                                                                                                                  |
| 4. data-status deployment-api derivations                               | ✗ wrong denominator   | [`data_status_service.py`](../../../deployment-api/deployment_api/services/data_status_service.py) computes `coverage % = captured / (captured + empty + failed + expected_unattempted)`. With catalog empty: numerator 0 (no MTDS rows captured for tradfi event contracts either), denominator 0 → either renders "N/A" OR shows phantom "100% captured" of 0 expected → misleading either way |

**The user's framing is correct**: UAC says "this should exist from 2025-09-28" but the rest of the chain (catalog /
manifest / data-status) shows nothing because backfill never ran. From a deployment-ui drilldown today, CME event
contracts are silently invisible — not even rendering as "out of scope" because the venue exists in the registry, but no
per-root drilldown is possible.

### Q6 — No active plan owns this

Plans searched — `tradfi_master`, `predictions_master`, `mtds_databento_path_streaming`,
`strategy_system_citadel_master` — none have an event-contract-specific todo. Single comment in `vm_zombie_watchdog.py`
("CME event-contract backfill (TradFi)") implies anticipated work but no owner. This is a clear gap.

## Why it matters

- **Cross-venue arb option value lost while data flows for free**: we're already capturing event-contract data via
  Databento (cost = $0 marginal beyond existing TradFi feed). Without the canonical link, the data sits unusable for
  arb. The link costs ~5 lines in UAC + a JOIN at strategy-service compute time.
- **Polymarket vs CME spread is a real edge**: Polymarket pricing is retail-driven, often deviates from fair value. CME
  event-contract pricing is institutional, tight to underlying. When they diverge, arb either side. Especially valuable
  for SPX / NDX / BTC — which have BOTH liquid Polymarket markets AND captured CME event contracts in the screenshot's
  top categories.
- **Settlement-rule equivalence verifiable**: both venues settle on the underlying's close per a published spec. CME
  event-contract settlement is exchange-determined (no oracle dispute risk); Polymarket UMA is dispute-prone (issue 14
  covers `umaBond / oracle_address` capture). Knowing the equivalence is structural lets strategy treat them as a paired
  hedge legitimately.
- **`Live = batch` for arb features**: live mode gets the same data via the same Databento path. Backtest
  reproducibility is preserved. The arb shape is identical batch-vs-live.
- **Compounds with other 2026-05-08 issues**: composes with issue 14 (predictions canonical_question_group + lifecycle),
  issue 8 (instruments lifecycle hard-required — event contracts have explicit settlement_time = exchange close), issue
  9 (per-row schema validation: `linked_canonical_question_group` non-null required for binary-outcome instruments).
- **Liquidity caveat (your framing)**: "even though it's new and illiquid" — yes, event contracts launched 2022-2023
  with thin liquidity. Volume is growing but spread is wide. The arb edge widens accordingly. Risk-managed sizing
  required (small clip per leg).

## Recommended decision

### Phase 0 (P0 — immediate) — Run the backfill, verify the end-to-end chain

Before any of the structural fixes (InstrumentType, cross-link, cluster validation), the **backfill must actually run**:

1. **Launch instruments-service Databento backfill VM** for `[2025-09-28, today]` window targeting all 9 event-contract
   roots. New launcher needed under `deployment-service/scripts/vm/launch-tradfi-instruments-backfill.sh` (paralleling
   `launch-cefi-instruments-backfill.sh` shape). Or extend the existing CeFi launcher to dispatch TradFi via
   `--asset-group tradfi`.
2. **Verify catalog rows written**: read
   `gs://{pid}-instruments/canonical/by_asset_group/asset_group=tradfi/venue=CME/...` after run. Expect ~8 rows per
   (root, resolution_date) for daily binaries with 4 strikes × YES/NO. Spot-check ECBTC.
3. **Verify writegate v2 expected-universe enumerator picks up the new catalog rows**: re-run
   `instruments-service/scripts/reconcile_expected_absence_reasons.py --asset-group tradfi --apply-flips` (or the Wave 3
   v2 enumerator) → verify manifest now has `expected_unattempted` or `captured` rows for ECBTC × dates 2025-09-28 →
   today.
4. **Verify data-status deployment-api derivation**: hit the endpoint for tradfi/CME drilldown → should now render ECBTC
   at the proper grain with correct denominator. NOT "N/A" or "0/0".
5. **Establish forward-poll cadence**: ship a TradFi instruments forward-poll launcher (daily cron equivalent of CeFi
   forward-poll) so new ECBTC daily-resolution dates get captured incrementally going forward.

This Phase 0 unblocks downstream phases AND gives us a working baseline to layer the structural fixes on top of. Without
it, fixing `InstrumentType.EVENT_CONTRACT` operates on an empty catalog — the type-rename has no rows to apply to.

### Phase 1 — Dedicated `InstrumentType.EVENT_CONTRACT`

UAC `unified_api_contracts.canonical.domain.tradfi.instrument_type` (or wherever the InstrumentType enum lives):

```python
class InstrumentType(StrEnum):
    SPOT = "SPOT"
    PERPETUAL = "PERPETUAL"
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    EVENT_CONTRACT = "EVENT_CONTRACT"  # NEW — binary outcome contracts (CME ECBTC, ECES, etc.)
    ETF = "ETF"
    # ...
```

Update `tradfi_instrument_universe.py:237-264` to use `EVENT_CONTRACT` instead of `OPTION`:

```python
DatabentoInstrumentDef("ECES.OPT",  "CME", "EVENT_CONTRACT", "GLBX.MDP3", "parent", "SP500",       "equity",    "ECES"),
# ...
```

Update Databento classifier to map `.OPT` parent symbols with `EC*` prefix to `EVENT_CONTRACT` instead of `OPTION` per
Databento native classification override.

### Phase 2 — `linked_canonical_question_group` cross-venue link

Add field to InstrumentRecord (TradFi side):

```python
@dataclass(frozen=True)
class InstrumentRecord:
    # existing fields...
    linked_canonical_question_group: CanonicalQuestionGroup | None = None  # only required when instrument_type == EVENT_CONTRACT
```

Per-root mapping (UAC `tradfi/event_contract_links.py` new SSOT):

```python
CME_EVENT_CONTRACT_TO_CANONICAL_GROUP: dict[str, CanonicalQuestionGroup] = {
    "ECES":  CanonicalQuestionGroup.SPX_UP_DOWN_DAILY,
    "ECNQ":  CanonicalQuestionGroup.NDX_UP_DOWN_DAILY,
    "ECRTY": CanonicalQuestionGroup.RUT_UP_DOWN_DAILY,   # needs new canonical group (issue 14 Phase 5 backfill)
    "ECYM":  CanonicalQuestionGroup.DJIA_UP_DOWN_DAILY,  # needs new canonical group (issue 14 Phase 5 backfill)
    "ECGC":  CanonicalQuestionGroup.GOLD_UP_DOWN_DAILY,  # needs new canonical group (issue 14 Phase 5 backfill)
    "ECCL":  CanonicalQuestionGroup.CRUDE_OIL_UP_DOWN_DAILY,  # ditto
    "ECNG":  CanonicalQuestionGroup.NATGAS_UP_DOWN_DAILY,  # ditto
    "EC6E":  CanonicalQuestionGroup.EUR_UP_DOWN_DAILY,  # ditto
    "ECBTC": CanonicalQuestionGroup.BTC_UP_DOWN_DAILY,  # already exists
}
```

Hard schema enforcement (issue 9 pattern): row with `instrument_type=EVENT_CONTRACT` AND
`linked_canonical_question_group=NULL` →
`record_failed(SCHEMA_VALIDATION_FAILED, missing_fields=["linked_canonical_question_group"])`.

### Phase 3 — Cluster validation per (root, resolution_date, strike_threshold)

Event contracts cluster differently from vanilla options. For each `(root, expiry_date)`, the universe is a pair of
YES/NO contracts at each strike threshold (e.g. ECBTC daily for 2026-05-09 has strikes at 60K, 65K, 70K, 75K — each with
YES + NO). Cluster validation kwargs at `record_captured`:

```python
manifest.record_captured(
    row_key={..., root: "ECBTC", date: "2026-05-09"},
    expected_root_clusters=expected_strikes_for_ecbtc_on_date(date),  # {60000: 2, 65000: 2, ...} = 2 contracts per strike (YES+NO)
    cluster_extractor=lambda r: f"{r.strike_threshold}:{r.outcome}",  # "60000:YES" / "60000:NO"
)
```

New helper SSOT in UAC for per-root strike-set discovery (Databento parent symbol enumerates available strikes per
expiry).

### Phase 4 — Strategy archetype: paired leg declaration

New strategy archetype `cme_polymarket_binary_arb` declared with explicit paired legs:

```python
@dataclass(frozen=True)
class PairedLegArchetype(StrategyArchetype):
    long_leg: VenueInstrumentRef   # e.g. ("CME", "ECBTC", strike, expiry, outcome)
    short_leg: VenueInstrumentRef  # e.g. ("POLYMARKET", canonical_question_group, market_id)
    fair_value_link: CanonicalQuestionGroup  # the underlying equivalence (BTC_UP_DOWN_DAILY)
    max_clip_usd: Decimal  # per-trade size cap (small for thin liquidity)
```

Pre-flight: archetype activation requires both legs' instrument-discovery + lifecycle + capture rows present +
`linked_canonical_question_group` resolved on the TradFi side.

### Phase 5 — Execution-service CME ClearPort connector

If we don't already have CME order routing in execution-service (likely not — DeFi-first to date), wire a CME ClearPort
connector for the TradFi leg. Polymarket leg uses the existing connector. Out of scope for May 23 cutover — track as
Phase 5 follow-up.

## Acceptance criteria

- [ ] **Phase 0 P0**: TradFi instruments-service backfill VM launched + completed for [2025-09-28, today] across all 9
      event-contract roots. Catalog rows verified > 0 in canonical GCS path.
- [ ] **Phase 0 P0**: writegate v2 expected-universe enumerator picks up new catalog rows; manifest renders ECBTC ×
      dates with `expected_unattempted` or `captured` per shard.
- [ ] **Phase 0 P0**: data-status deployment-api drilldown for tradfi/CME shows ECBTC with non-zero denominator +
      correct coverage % derivation. NOT "N/A".
- [ ] **Phase 0 P0**: TradFi instruments forward-poll launcher shipped (daily cadence, paralleling
      `launch-cefi-instruments-backfill.sh`).
- [ ] UAC `InstrumentType.EVENT_CONTRACT` enum value shipped.
- [ ] `_CME_EVENT_CONTRACTS` registry updated to `EVENT_CONTRACT` instrument_type.
- [ ] Databento classifier maps `EC*.OPT` parent symbols to `EVENT_CONTRACT`.
- [ ] `InstrumentRecord.linked_canonical_question_group` field added; per-row schema validation gate.
- [ ] `CME_EVENT_CONTRACT_TO_CANONICAL_GROUP` SSOT shipped + linked to existing + new canonical groups.
- [ ] Cluster validation per `(root, resolution_date, strike_threshold)` for event-contract bundles.
- [ ] Smoke test: capture ECBTC for 2025-09-28 (first available) through 2026-05-08; verify shard rows have
      `instrument_type=EVENT_CONTRACT` + `linked_canonical_question_group=BTC_UP_DOWN_DAILY` + cluster validation
      passes.
- [ ] Cross-venue arb readiness: data-status drilldown shows ECBTC under TradFi/CME WITH a "linked:
      prediction/POLYMARKET/BTC_UP_DOWN_DAILY" cross-link visible.
- [ ] Manifest cleanup (issue 12 mandate): existing event-contract captured rows re-classified from
      `instrument_type=OPTION` to `EVENT_CONTRACT`; legacy OPTION-classified event-contract manifest rows purged.
- [ ] (Optional Phase 5) CME ClearPort execution connector + paired-leg archetype + first paper-trade arb signal
      generated.

## Open questions

- For ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E underlyings: do equivalent Polymarket canonical_question_groups exist today, or are
  they part of issue 14's Phase 5 backfill? Most likely the latter — `RUT_UP_DOWN_DAILY` etc. need to be added before
  linkage is meaningful. Sequence: issue 14 Phase 5 backfill → THIS issue Phase 2 link.
- Databento coverage start `2025-09-28` is recent — we have ~7 months of history. Does that satisfy ML training
  requirements for an arb model? Probably yes for high-frequency arb; insufficient for slower mean-reversion strategies.
- Do CME event contracts emit funding-style intraday cash flows or pure binary settle-at-close? (Affects backtest
  fidelity.) Per CME spec: binary settle-at-close, no intraday cash flows.
- Strike-threshold equivalence: CME event-contract strikes are pre-set by exchange; Polymarket strikes are
  market-defined per market_id. Linking at strike grain may require fuzzy matching ("CME ECBTC 70K resolves the same as
  Polymarket BTC > $70K market_id"). Default: link at canonical_group grain (both venues' "BTC_UP_DOWN_DAILY");
  per-strike alignment is strategy-side fair-value computation, not instrument-discovery.
- Asset_group decision: stay with Option A (TradFi + cross-link) per recommendation; revisit if Option B (re-classify as
  prediction) becomes cleaner once the prediction asset_group's deployment-ui drilldown ships (issue 14 Phase 5).
- Coordination with issue 14: this issue's Phase 2 link depends on issue 14's Phase 5 canonical-groups backfill.
  Sequence carefully.
- Coordination with issue 13: CME event-contract roots + first-trade dates are on-chain-immutable-equivalent
  (exchange-listed contracts have deterministic listing dates). The `derive_event_contract_first_listed.py` SSOT script
  pattern applies — first-trade-date in Databento is the empirical truth, replaces any hardcoded date.
