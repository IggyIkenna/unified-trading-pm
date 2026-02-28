# Schema Ownership Migration — Master Checklist

**Link:** [schema_ownership_three_tiers plan](../cursor-plans/schema_ownership_three_tiers_267ab636.plan.md)

---

## Phase 1 — api-contracts restructure

- [ ] Create `api_contracts_external/` and `unified_normalised_contracts/` subpackages
- [ ] Move existing files; update imports
- [ ] Add re-exports so existing `from api_contracts.internal import X` still works (no breaking changes)
- [ ] Add `tests/test_normalization.py` (per-venue + property-based)
- [ ] Update api-contracts README, CONTRIBUTING

---

## Phase 2 — unified-internal-contracts extract

- [ ] Create unified-internal-contracts repo with full setup
- [ ] Move `ml.py`, `risk.py`, `features.py`, `events.py`, `pubsub.py` from api-contracts
- [ ] Services update imports to `from unified_internal_contracts import X`
- [ ] Remove internal schemas from api-contracts after consumer migration
- [ ] Add unified-internal-contracts README, ARCHITECTURE; update api-contracts
- [ ] Add cursor rule: import internal schemas from unified-internal-contracts

---

## Phase 3 — BasePosition pattern

- [ ] Add BasePosition, BaseOrder (if needed) to api-contracts `unified_normalised_contracts/`
- [ ] UMI, UTEI, UPI implement extensions (ExecutionPosition, MarketDataPosition, CanonicalPosition)
- [ ] Update codex schema-governance.md, extension pattern
- [ ] Add cursor rule: extend base schemas from api-contracts; do not duplicate
