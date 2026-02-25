# Instruments Domain: Design Decisions and Rationale

**Purpose:** Document why we chose this path so future implementations and refactors don't conflict.

> **Source of truth:** `unified-trading-codex/02-data/instruments-and-api-keys-standard.md` and `.cursor/rules/instruments-domain-and-api-keys.mdc`. This plan is historical context; use the canonical docs for implementation.

---

## 1. Single Reader: InstrumentsDomainClient (UDS)

**Decision:** All instrument reads go through `InstrumentsDomainClient` from unified-domain-services. No duplicate `_load_instruments_by_venue`, no direct GCS reads, no service-specific implementations.

**Rationale:**
- One canonical implementation reduces bugs and drift
- Easier to add features (aggregation, caching) in one place
- Services stay thin; domain logic lives in shared library

**Implied:** When migrating a service, add any missing functionality to InstrumentsDomainClient first. No fallbacks, no backward compat layers in services.

---

## 2. No Reduced Functionality: Add to UDS, Not Fallbacks

**Decision:** If moving to InstrumentsDomainClient would reduce functionality for a service, add that functionality to InstrumentsDomainClient (unified-domain-services). Never add fallbacks, bypasses, or backward-compat layers in the service.

**Rationale:**
- Fallbacks create technical debt and two code paths
- Backward compat delays cleanup and causes confusion
- Per codex: "No backward compatibility - fail fast, clean migrations"

**Examples:**
- market-tick-data-handler loads from multiple categories (CEFI+TRADFI+DEFI) → Add `categories` parameter to `get_instruments_for_date`
- market-data-processing-service needs `category` parameter → Add `category` parameter
- market-tick-data-handler populates `market_category` if missing → Add `populate_market_category` logic to UDS (or call `determine_market_category`)

---

## 3. Category-Specific Buckets

**Decision:** Instruments live in category-specific buckets: `instruments-store-{category}-{project_id}` (CEFI, TRADFI, DEFI). InstrumentsDomainClient must support:
- `category: str | None` — single category (uses that bucket)
- `categories: list[str] | None` — multiple categories (loads from each, concatenates). If None and category None, default to all three.

**Rationale:**
- instruments-service writes to category buckets
- market-tick-data-handler downloads across categories
- market-data-processing-service processes one category at a time

---

## 4. By-Venue Structure Only (No Legacy Fallback)

**Decision:** InstrumentsDomainClient reads only from `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet`. No legacy single-file fallback.

**Rationale:**
- instruments-service has written by-venue for a long time
- Legacy fallback in market-data-processing-service is technical debt
- Fail fast: if by-venue doesn't exist, return empty or error — don't silently fall back

---

## 5. Envio: Keep (It Is Used)

**Decision:** Envio remains in API keys and config. Used by instruments-service (UniswapV4Adapter) and features-onchain-service.

**Rationale:** Grep confirmed usage. Do not remove.

---

## 6. API Keys: Secret Manager Only

**Decision:** All API keys via `get_secret_with_fallback`. No `os.environ.get` for API keys in production code or scripts.

**Rationale:** Single source of truth, no credentials in env/code.

---

## 7. Aggregation: instruments-service Owns, UDS Exposes

**Decision:** instruments-service runs `--operation aggregate` (daily batch). UDS `InstrumentsDomainClient.get_aggregated_instruments(category)` reads the result. UTDv3 data-status uses UDS.

**Rationale:** Producer owns aggregation; consumers read via UDS.

---

## 8. Implementation Order

1. Add `category` and `categories` to InstrumentsDomainClient
2. Add `populate_market_category` (or equivalent) if missing
3. Migrate market-data-processing-service (single category)
4. Migrate market-tick-data-handler (multi-category)
5. Remove duplicate `_load_instruments_by_venue` from both services
6. Remove legacy fallback from market-data-processing-service

---

## 9. What NOT to Do

| Don't | Do |
|-------|-----|
| Add fallback in service when UDS lacks feature | Add feature to UDS first |
| Keep legacy single-file read path | By-venue only; fail if missing |
| Use `_load_instruments_by_venue` in services | Use InstrumentsDomainClient |
| Add backward-compat flag (`use_legacy=True`) | Clean migration; remove old path |
| Use `os.environ.get` for API keys in scripts | Use `get_secret_with_fallback` |

---

## 10. Conflict Prevention

When refactoring or adding features:
1. Check this doc before introducing new instrument read paths
2. If a service needs new capability, add to InstrumentsDomainClient
3. Update this doc when adding new decisions
