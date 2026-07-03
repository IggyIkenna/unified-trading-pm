---
doc_type: plan
title: schema_versioning_health_matrix_combos
summary:
status: DONE
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: 2026-03-06
overview: 'Three complementary schema enhancements: (1) Combo/parlay bet support with negative-price handling for American moneyline and options combos; (2) Provider API version manifest + SVG health matrix; (3) CI schema validation (Option B) owned by interface repos that hold VCR cassettes and API auth.

  '
---

# Schema Versioning, Health Matrix & Combo Bets Plan

## Context

During the schema gap normalizer sprint (Session 10) three deficiencies were identified beyond the five normalizer gaps
that were closed:

1. **No combo/parlay support** — `CanonicalBetOrder` is single-leg only; American moneyline odds (negative = favorite,
   e.g. -110) are silently dropped; options combos (1×2 = buy call + sell put, risk reversals, straddles) can carry
   negative net premium.
2. **No provider API version pinning** — `canonical-dependency-manifest.json` tracks PyPI packages only. If Betfair or
   Binance releases a breaking API change there is no machine-readable record of which raw schema snapshot maps to which
   API version.
3. **No live schema health signal** — coverage (does a normalizer exist?) is tracked by `SCHEMA_AUDIT_MATRIX.md` (STEP
   5.15) but freshness (is the schema still valid against the live API?) is not tracked anywhere.

---

## Phase 1 — Combo Bets + Negative Prices

**Owner:** `unified-api-contracts`

### 1.1 New canonical types in `domain.py`

Add to `unified_api_contracts/unified_normalised_contracts/domain.py`:

```python
class CanonicalComboLeg(BaseModel, frozen=True):
    """Single leg of a parlay / multi-leg combo bet."""
    venue: str
    market_id: str
    selection_id: str
    side: Literal["back", "lay"]
    decimal_odds: Decimal
    american_odds: int | None = None          # negative = favorite (e.g. -110)
    stake: Decimal

class CanonicalComboBet(BaseModel, frozen=True):
    """Parlay / accumulator / options-combo order."""
    venue: str
    order_id: str
    legs: list[CanonicalComboLeg]
    combined_decimal_odds: Decimal             # product of leg decimal odds
    total_stake: Decimal
    net_premium: Decimal | None = None         # for options combos; MAY BE NEGATIVE
    status: str
    timestamp: datetime
```

### 1.2 Add `american_odds` field to `CanonicalBetOrder`

```python
american_odds: int | None = None  # negative allowed (favorite in moneyline markets)
```

### 1.3 `OddsFormat` enum actually used

Currently `OddsFormat.AMERICAN` exists but normalizers always produce decimal and discard the source format. Add a
`odds_format: OddsFormat = OddsFormat.DECIMAL` field to `CanonicalBetOrder` and `CanonicalComboLeg` so callers know how
the odds were originally expressed.

### 1.4 Conversion utilities

Add to a new `unified_api_contracts/unified_normalised_contracts/odds.py`:

```python
def american_to_decimal(american: int) -> Decimal:
    """Convert American odds (positive or negative) to decimal."""
    if american > 0:
        return Decimal(american) / 100 + 1
    return Decimal(100) / Decimal(-american) + 1

def decimal_to_american(decimal_odds: Decimal) -> int:
    if decimal_odds >= 2:
        return int((decimal_odds - 1) * 100)
    return int(-100 / (decimal_odds - 1))
```

### 1.5 Negative price scope documentation

Document in `docs/NEGATIVE_PRICES.md`:

- **American moneyline favorites**: -110, -300, etc. — always an integer
- **Options combos**: 1×2 (buy call + sell put), risk reversal, straddle — net premium is `Decimal` and CAN be negative
  when the short leg exceeds the long leg cost
- **NOT negative**: decimal odds (always ≥ 1.01), Betfair SP, fractional odds

### Todos

| id                        | description                                                         | status                   |
| ------------------------- | ------------------------------------------------------------------- | ------------------------ |
| combo-canonical-types     | Add `CanonicalComboLeg` + `CanonicalComboBet` to domain.py          | **completed 2026-03-09** |
| combo-american-odds-field | Add `american_odds: int \| None` to `CanonicalBetOrder`             | **completed 2026-03-09** |
| combo-odds-format-field   | Add `odds_format: OddsFormat` field to order + leg canonicals       | **completed 2026-03-09** |
| combo-odds-utils          | Create `odds.py` with `american_to_decimal` + `decimal_to_american` | **completed 2026-03-09** |
| combo-negative-price-docs | Create `docs/NEGATIVE_PRICES.md`                                    | **completed 2026-03-09** |
| combo-tests               | Unit tests for conversion utils + negative price round-trips        | **completed 2026-03-09** |

---

## Phase 2 — Provider API Version Manifest + SVG Health Matrix

**Owner:** `unified-api-contracts`

### 2.1 `provider_api_versions.yaml`

Create `unified_api_contracts/provider_api_versions.yaml`:

```yaml
# Provider API version manifest — updated manually when schemas are refreshed.
# status: green = validated, yellow = unverified, red = known breaking change
providers:
  binance:
    api_version: "v3"
    spec_url: "https://binance-docs.github.io/apidocs/spot/en/"
    last_verified: "2026-03-06"
    status: green
    schemas:
      - BinanceOrderResponse
      - BinanceTrade
  betfair:
    api_version: "2.1"
    spec_url: "https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0d/API+Overview"
    last_verified: "2026-03-06"
    status: green
    schemas:
      - BetfairMarket
      - BetfairRunner
  # ... all 63 providers ...
```

### 2.2 `__api_version__` metadata on raw schema files

Each external schema file should declare its version at the top:

```python
# unified_api_contracts/unified_api_contracts_external/binance/schemas.py
__api_version__ = "v3"  # matches provider_api_versions.yaml
__api_spec_url__ = "https://binance-docs.github.io/apidocs/spot/en/"
```

### 2.3 `scripts/generate_schema_version_matrix.py`

Reads `provider_api_versions.yaml` and each schema module's `__api_version__` attribute. Outputs:

- `docs/SCHEMA_VERSION_MATRIX.md` — table: Provider | API Version | Schema Version | Last Verified | Status
- `docs/schema_health.svg` — 8×8 colour grid (green/yellow/red cells) similar to the workspace manifest SVG; one cell
  per provider; hover text shows version + last verified date

Script logic:

```
for each provider in yaml:
  import schema module
  compare __api_version__ with yaml api_version
  if mismatch → status = red
  if last_verified > 90 days ago → status = yellow (unless already red)
  else → status from yaml
```

### 2.4 STEP 5.16 quality gate

Add to `unified-api-contracts/scripts/quality-gates.sh` (and codex SSOT template):

```bash
if [ -f "unified_api_contracts/provider_api_versions.yaml" ]; then
  echo "STEP 5.16: Checking provider API version manifest..."
  RED_PROVIDERS=$(python3 scripts/generate_schema_version_matrix.py --count-red 2>/dev/null || echo "0")
  if [ "$RED_PROVIDERS" -gt 0 ]; then
    log_fail "STEP 5.16: $RED_PROVIDERS provider(s) have red schema status (breaking change detected)"
    exit 1
  else
    log_success "STEP 5.16: All provider schemas green or yellow"
  fi
fi
```

### Todos

| id                         | description                                                                     | status                   |
| -------------------------- | ------------------------------------------------------------------------------- | ------------------------ |
| versioning-yaml            | Create `unified_api_contracts/provider_api_versions.yaml` with all 63 providers | **completed 2026-03-09** |
| versioning-schema-metadata | Add `__api_version__` to all 63 external schema files                           | **completed 2026-03-09** |
| versioning-matrix-script   | Create `scripts/generate_schema_version_matrix.py` (MD + SVG output)            | **completed 2026-03-09** |
| versioning-svg-matrix      | SVG health matrix output (green/yellow/red grid)                                | **completed 2026-03-09** |
| versioning-quality-gate    | Add STEP 5.16 to quality-gates.sh + codex SSOT template                         | **completed 2026-03-09** |
| versioning-tests           | Unit tests for matrix script with mock yaml + schema modules                    | **completed 2026-03-09** |

---

## Phase 3 — CI Schema Validation (Option B — Interface Repos)

**Owner:** Interface repos (`unified-market-interface`, `unified-sports-execution-interface`, etc.)

### Rationale

Interface repos are the correct owner because:

- They hold VCR cassettes (recorded real API responses) per provider
- They hold API keys for sandbox/testnet environments
- They already run integration tests against provider adapters
- UAC should not own live credentials — UAC is a pure schema/contract library

### 3.1 CI integration test structure per interface repo

```
unified-market-interface/
  tests/
    schema_validation/
      test_binance_schema.py       # calls Binance testnet, validates against BinanceOrderResponse
      test_okx_schema.py
      test_bybit_schema.py
      conftest.py                  # VCR cassette config + skip-if-no-key markers
```

Each test:

1. Makes a real (or VCR-replayed) API call to provider sandbox
2. Parses response with the raw Pydantic schema
3. Asserts no `ValidationError` — if Pydantic rejects it, the schema is stale
4. On failure: marks provider cell red in `docs/SCHEMA_AUDIT_MATRIX.md` via a CI artifact

### 3.2 CI artifact update flow

```
Interface repo CI fails schema_validation test
  → writes {provider}_schema_health.json artifact: {"status": "red", "provider": "binance", "reason": "..."}
  → UAC repo reads artifacts in its own CI (cross-repo artifact download)
  → regenerates schema_health.svg with updated statuses
  → commits updated docs/schema_health.svg to UAC main branch
```

### 3.3 Provider sandbox coverage

| Provider group      | Interface repo                            | Sandbox available                                 |
| ------------------- | ----------------------------------------- | ------------------------------------------------- |
| Crypto spot/futures | `unified-market-interface`                | Yes (Binance testnet, OKX sandbox, Bybit testnet) |
| Sports betting      | `unified-sports-execution-interface`      | Partial (Betfair API sandbox)                     |
| Betdaq, Smarkets    | `unified-sports-execution-interface`      | API keys required (Phase 4 blocker)               |
| Matchbook, 1xBet    | `unified-sports-execution-interface`      | API keys required (Phase 4 blocker)               |
| IBKR                | `unified-market-interface` (IBKR adapter) | TWS paper trading (MagicMock(spec=IB))            |

### 3.4 Blocked providers

Providers that need Phase 4 API keys (see `api_keys_and_auth.md` § `phase-4-blockers`):

- betdaq, smarkets, matchbook, onexbet — schema validation tests created but skipped until keys added

### Todos

| id                     | description                                                                                 | status                   |
| ---------------------- | ------------------------------------------------------------------------------------------- | ------------------------ |
| ci-umi-schema-tests    | Add `tests/schema_validation/` to `unified-market-interface` for crypto providers           | **completed 2026-03-09** |
| ci-usei-schema-tests   | Add `tests/schema_validation/` to `unified-sports-execution-interface` for sports providers | **completed 2026-03-09** |
| ci-artifact-protocol   | Define CI artifact schema (`{provider}_schema_health.json`) + UAC reader script             | **completed 2026-03-09** |
| ci-svg-update-job      | UAC CI job that downloads interface artifacts + regenerates SVG                             | **completed 2026-03-09** |
| ci-vcr-cassettes       | Record initial VCR cassettes for Binance testnet, OKX sandbox, Bybit testnet                | **completed 2026-03-09** |
| ci-blocked-sports-keys | Create skip markers for Phase 4 key-blocked providers                                       | **completed 2026-03-09** |

---

## Dependencies

| This plan depends on                        | Why                                                      |
| ------------------------------------------- | -------------------------------------------------------- |
| `uac_schema_normalization_complete.md`      | All raw schemas must exist before versioning them        |
| `api_keys_and_auth.md` § `phase-4-blockers` | Sports provider sandboxes need credentials               |
| `orphan-contracts-utilization.md`           | Ensures all schemas reachable before health matrix built |

---

## Execution Order

```
Phase 1 (UAC — no external deps):
  combo-canonical-types → combo-american-odds-field → combo-odds-format-field
  combo-odds-utils → combo-tests → combo-negative-price-docs

Phase 2 (UAC — no external deps):
  versioning-yaml → versioning-schema-metadata → versioning-matrix-script
  → versioning-svg-matrix → versioning-quality-gate → versioning-tests

Phase 3 (interface repos — after Phase 2 SVG format stabilised):
  ci-artifact-protocol → ci-umi-schema-tests + ci-usei-schema-tests (parallel)
  → ci-vcr-cassettes → ci-svg-update-job
  ci-blocked-sports-keys (parallel — add skip markers early)
```

Phases 1 and 2 are independent and can run in parallel. Phase 3 should start after Phase 2 SVG format is stable (avoid
format churn).
