---
title:
  "Hard schema enforcement at instruments-service write boundary — base/quote currency required for TradFi+DeFi+CeFi,
  instrument_id required everywhere, full-column capture for sports (audit beyond api_football to
  footystats/SFI/understat/transfermarkt/openmeteo/odds_api), per-row record_failed(SCHEMA_VALIDATION_FAILED) instead of
  venue-wide shard fail-all"
created: 2026-05-08
author: ikenna
source:
  - unified-api-contracts/unified_api_contracts/canonical/domain/market/tradfi.py:10-47 (currency optional/missing)
  - unified-api-contracts/unified_api_contracts/internal/__init__.py (InstrumentRecord)
  - instruments-service/instruments_service/engine/orchestrator.py:1997-2045 (validate_instrument_records venue-shard
    fail-all)
  - unified-api-contracts/unified_api_contracts/external/api_football/normalize.py:372-395 (minimal flattening)
  - plans/active/api_football_minimal_flattening_removal_2026_05_07.md (api_football only)
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md:80-82,96,104-106 (4-pillar gate at record_captured)
  - operator directive 2026-05-08:
      "you wouldn't even drop instruments_service if it was to not have those columns. It would fail schema validation,
      and that source of truth is held in unified API contracts ... we should be grabbing every column of the schema and
      enforcing that we have every column when we save"
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Hard schema enforcement at instruments-service write boundary

> **Severity**: P0 — workspace-wide silent data quality holes; affects every asset_group; root-cause for compounding
> lookahead / partial-bundle / minimal-flattening bugs. **Blast radius**: UAC (every domain schema must mark required
> fields explicitly) + instruments-service write path + every external adapter normalizer (full-column capture) +
> manifest writer (per-row `record_failed(SCHEMA_VALIDATION_FAILED)` pattern). **Suggested owner**: cross-cuts every
> asset_group master. Recommend a workspace-wide sub-plan `hard_schema_enforcement_2026_05_08.md` owned at
> infrastructure level (`infrastructure_master_2026_05_07.md`).

## What I found

Five-question audit; the **only fully-enforced lifecycle schema in the workspace is prediction markets**
(`MarketLifecycle` per
[predictions/lifecycle.py:43-79](../../../unified-api-contracts/unified_api_contracts/canonical/domain/predictions/lifecycle.py#L43-L79)).
Every other asset_group has gaps.

### Q1 — base_currency / quote_currency: SCHEMA-PRESENT-BUT-NOT-ENFORCED

[market/tradfi.py:10-47](../../../unified-api-contracts/unified_api_contracts/canonical/domain/market/tradfi.py#L10-L47):

```python
class CanonicalYieldCurvePoint(BaseModel):
    currency: str | None = None     # nullable

class CanonicalBondData(BaseModel):
    currency: str | None = None     # nullable

class CanonicalCdsSpread(BaseModel):
    # NO currency field at all
    ...
```

For DeFi: `InstrumentRecord` schema in UAC internal declares `base_currency` / `quote_currency` but the orchestrator's
validation pattern (Q2) makes the fields effectively optional in practice — missing values fail the entire venue shard
rather than the specific row.

For CeFi spot/perp: similar — schema declares but doesn't hard-gate at write time. Workspace lacks an explicit "for
asset_group=cefi/defi/tradfi, base_currency + quote_currency MUST be non-null" rule with runtime enforcement.

### Q2 — Write-path validation: PARTIAL (venue-shard fail-all, not per-row record_failed)

[orchestrator.py:1997-2045](../../../instruments-service/instruments_service/engine/orchestrator.py#L1997-L2045):

```python
records = await adapter.fetch_instruments(...)
validated = validate_instrument_records(records)  # line 2001
if len(validated) < len(records):
    # Some rows rejected — but venue-wide handler at line 2018 fails ENTIRE shard
    raise InstrumentValidationError(...)
```

When ONE row is missing a required field, the **entire (venue, date) shard is rejected** — manifest gets nothing, no
`record_failed(SCHEMA_VALIDATION_FAILED)` per-row entry, no operator signal beyond the venue-wide failure. Operator
can't tell:

- "We tried for 1000 instruments, 1 had bad currency field, we lost all 1000" (current behaviour)
- "We tried for 1000 instruments, 999 captured, 1 marked record_failed(SCHEMA_VALIDATION_FAILED,
  missing_fields=['quote_currency'])" (correct behaviour)

### Q3 — Sports adapters full-column capture: GAP across api_football; OTHERS NOT AUDITED

api_football confirmed (per `api_football_minimal_flattening_removal_2026_05_07.md`):

- FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES — minimal flattening, drops 18-30+ columns per data_type.
- [normalize.py:372-395](../../../unified-api-contracts/unified_api_contracts/external/api_football/normalize.py#L372-L395)
  — normalizers literally `return dict(raw)` with `fixture_id` stamped.

**Other sports adapters NOT YET AUDITED**: footystats, soccer_football_info (SFI), understat, transfermarkt, open_meteo,
odds_api. Their normalize functions live under
`instruments-service/instruments_service/reference_data/adapters/sports/adapters/` (not under UAC `external/`); none
have been audited for the same minimal-flattening anti-pattern.

The user's directive: "we know their schemas, we shouldn't be just grabbing a few representative things. We should be
grabbing every column of the schema and enforcing that we have every column when we save, so we know we're getting the
full data." Need a sweep across every sports adapter parallel to the api_football plan.

### Q4 — Plan coverage: PARTIAL with workspace-wide rule MISSING

- [writegate_honest_coverage_endtoend_2026_05_06.md:80-82,96,104-106](../writegate_honest_coverage_endtoend_2026_05_06.md#L80-L82)
  — defines the 4-pillar gate at `record_captured` (row count > 0, NaN ratio, schema match, cluster coverage). Schema
  match is pillar 3 but the **specific shape of the gate (pre-row Pydantic validation + per-row
  `record_failed(SCHEMA_VALIDATION_FAILED)` on rejection) is not codified** — pillar 3 is currently aspirational.
- `api_football_minimal_flattening_removal_2026_05_07.md` — covers only api_football's 4 data_types.
- No workspace-wide rule "every adapter at write boundary MUST validate against UAC schema; failures route to
  `record_failed(SCHEMA_VALIDATION_FAILED, missing_fields=...)` per-row, not venue-wide shard fail-all."

### Q5 — instrument_id enforcement: SCHEMA-PRESENT-BUT-ENFORCEMENT-IMPLICIT

`InstrumentRecord` declares `instrument_id: str` as required; validation at orchestrator:2001 rejects rows without it.
But:

- Rejection is venue-shard-scoped, not row-scoped (same Q2 problem).
- Manifest `row_key` shape per CLAUDE.md "Per-asset-group shard-key matrix" requires `instrument_id` for per-instrument
  shards (cefi spot/perp, tradfi ETFs, defi, prediction). No runtime check that the row_key shape matches the
  asset_group's shard atom.
- A normalizer that accidentally omits `instrument_id` from a row → silent venue-wide failure → no per-row signal.

## Why it matters

- **Silent data quality holes compound**: minimal flattening (Q3) + nullable required fields (Q1) + venue-shard fail-all
  (Q2) produce parquets that LOOK populated to the manifest but are missing the columns features need. Reference
  incident pattern: 2026-05-05 MDPS 1440 NaN OHLC bars — same class.
- **Cross-source verification breaks**: cross-source ODDS arbitrage / FIXTURES status verification (per
  `fixtures_postponed_cancelled_lifecycle_2026_05_08.md`) requires currency / instrument_id consistency.
  Schema-present-but-not-enforced means cross-source comparison silently drops rows.
- **Currency conversion features blocked**: any feature that needs to convert (USD-quoted ES futures price → EUR for
  European-strategy comparison) requires `quote_currency`. Today's nullable schema means downstream code defaults to USD
  silently — wrong by ~1.05x for EUR-quoted instruments.
- **Operator visibility lost**: venue-shard fail-all (Q2) hides per-row failure modes. Operator sees "venue X failed"
  not "venue X had 999 successes and 1 schema-validation-failed-row with missing quote_currency."
- **`Live = batch` violation**: live mode would naturally validate per-tick (single-row scope) and route invalid ticks
  to a typed error. Batch's venue-shard fail-all is incompatible with the principle.

## Recommended decision

Workspace-wide sub-plan + per-asset-group sweep:

### Phase 1 — UAC schema audit + hard-required field markup

For every domain schema in UAC `canonical/domain/`:

- Audit which fields are nullable vs required; per asset_group, declare HARD-REQUIRED set.
- Hard-required for ALL asset_groups: `instrument_id`, `data_available_at`.
- Hard-required for **CeFi/DeFi/TradFi** instruments: `base_currency`, `quote_currency`. Add `settlement_currency` for
  derivatives (futures/options/perps where margining ≠ quoting).
- Hard-required for **DeFi** specifically: `chain_id`, `base_token.contract_address`, `base_token.decimals`,
  `quote_token.contract_address`, `quote_token.decimals`.
- Hard-required for **TradFi futures**: `expiry_date`, `last_trading_date` (per
  `instruments_lifecycle_and_fixtures_endtime_cascade_2026_05_08.md` Phase 1).
- Hard-required for **TradFi options**: `expiry_date`, `strike_price`, `option_right`, `underlying_id` (same issue).
- Hard-required for **prediction markets**: `market_created_at`, `resolution_time`, `settlement_time` (already done — Q3
  PRESENT — gold standard).
- Hard-required for **sports**: `fixture_id` (sports' instrument_id equivalent), source-specific data_type required
  column sets per UAC contract.

Migrate Pydantic / dataclass declarations: `field: str | None = None` → `field: str` (no default) for hard-required.

### Phase 2 — Per-row schema validation gate at instruments-service write boundary

Refactor `orchestrator.py:1997-2045`:

```python
records = await adapter.fetch_instruments(...)
captured_rows: list[InstrumentRecord] = []
failed_rows: list[(dict, ValidationError)] = []
for raw_row in records:
    try:
        validated_row = InstrumentRecord.model_validate(raw_row)
        captured_rows.append(validated_row)
    except ValidationError as exc:
        failed_rows.append((raw_row, exc))

# Write captured rows to parquet
write_parquet(captured_rows)
manifest.record_captured(
    row_key={...},
    parquet=...,
    expected_root_clusters=...,
    cluster_extractor=lambda r: r.instrument_id,
)

# Per-row failures → manifest record_failed
for raw_row, exc in failed_rows:
    manifest.record_failed(
        row_key={..., instrument_id: raw_row.get("instrument_id", "UNKNOWN_NO_ID")},
        error=SchemaValidationError(missing_fields=exc.missing_fields(), invalid_fields=exc.invalid_fields()),
        error_reason="SCHEMA_VALIDATION_FAILED",
        attempted_at=poll_run_started_at,
    )
```

Add `SCHEMA_VALIDATION_FAILED` to `EMPTY_CONFIRMED_REASONS` / `ATTEMPTED_FAILED_REASONS` typed taxonomy.

### Phase 3 — Sports adapter full-column capture audit + sweep

Parallel to api_football minimal-flattening plan, audit + fix:

- footystats — every data_type's response columns vs on-disk schema. Quote upstream API doc per data_type.
- soccer_football_info (SFI) — including SFI_PROGRESSIVE_STATS structure.
- understat — xG, shot-quality, per-player stats.
- transfermarkt — player_values, market_values.
- open_meteo — weather forecast columns (forecast_issue_time, target_time, all weather variables).
- odds_api — bookmaker-specific columns (already partially scoped in `odds_fixture_anchored_nan_fill_2026_05_08.md`).

For each: extend UAC contract to declare every source column; update normalizer to capture all of them; backfill /
re-process where critical.

### Phase 4 — Manifest row_key shape validation at runtime

UTL `ManifestWriter.record_captured` adds runtime check: `row_key` shape must match the asset_group's shard atom per
CLAUDE.md "Per-asset-group shard-key matrix." Missing `instrument_id` for per-instrument data_type →
`MissingShardKeyComponentError`, fail loud.

### Phase 5 — QG step 5.65 (new): grep for nullable required fields

base-service.sh adds a new QG step that statically walks UAC schemas and asserts: any field declared in the
asset_group's hard-required set MUST be non-nullable in the Pydantic / dataclass declaration. Catches drift at PR-time.

## Acceptance criteria

- [ ] UAC schema audit complete; hard-required sets declared per asset_group.
- [ ] All hard-required fields marked non-nullable in UAC Pydantic / dataclass declarations.
- [ ] instruments-service `orchestrator.py` refactored to per-row validate + per-row
      `record_failed(SCHEMA_VALIDATION_FAILED, missing_fields=...)` on failure (no more venue-shard fail-all).
- [ ] `SCHEMA_VALIDATION_FAILED` typed `error_reason` added to closed-set taxonomy.
- [ ] All sports adapters audited (footystats, SFI, understat, transfermarkt, open_meteo, odds_api) for full-column
      capture; minimal-flattening anti-pattern eliminated.
- [ ] UTL `ManifestWriter.record_captured` validates row_key shape against shard-atom matrix.
- [ ] base-service.sh QG step 5.65 enforces nullable-vs-required at PR-time.
- [ ] Smoke test: feed a deliberately-malformed row (missing `quote_currency`) through instruments-service → verify
      per-row `record_failed(SCHEMA_VALIDATION_FAILED)` manifest entry + 999 other rows still captured normally.
- [ ] deployment-ui drilldown shows per-row `SCHEMA_VALIDATION_FAILED` rows with missing-fields detail.

## Open questions

- For partial-row recovery: if a row is missing ONLY `quote_currency` but has everything else, do we (a) reject the row
  entirely, or (b) accept with NULL + flag for re-fetch? Default per workspace honest-absence rule = (a) reject. But for
  high-volume venues with rare bad rows, (b) might be operationally cheaper.
- Migration scope: how many existing parquets have rows that would fail post-Phase-1 hard-required? Need a one-time
  scan + count before rolling out the gate.
- For prediction markets: schema is already gold-standard; verify enforcement is actually wired (the fields are required
  in the dataclass; is the runtime gate present?).
- Composability with `instruments_lifecycle_and_fixtures_endtime_cascade_2026_05_08.md`: that issue's Phase 1 (futures
  expiry hard-required) is a SUBSET of this issue's Phase 1. Should fold into a single coordinated migration to avoid
  two breaking-change waves.
- Sports adapter normalizers live in instruments-service repo (not UAC `external/`) — does Phase 3 require moving them
  to UAC `external/{source}/normalize.py` per the api_football precedent, or extend the normalizers in-place at
  instruments-service?
- Workspace import rule: "Services use `from unified_api_contracts.{domain} import X`" — Phase 1's hard-required schema
  migration is technically a breaking API change for downstream consumers. Need version-bump coordination.
