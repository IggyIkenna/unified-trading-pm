---
scope: [engineer, admin]
last_reviewed: 2026-06-27
---

# Prediction Settlement / Availability Convention

**SSOT status**: live — owns the prediction `available_to` boundary rule. **Last updated**: 2026-06-27

---

## Convention (chosen)

`available_to` for a prediction market = the market's **settlement date, inclusive**.

A market that settles on day D has `available_to = D` in the catalogue. The IS enumerator treats a market as active on
day D iff:

```
available_from <= D <= available_to
```

This means:

- **Settlement day D**: market IS active (capturable, counted in manifest).
- **Day D+1**: market is `EXPECTED_INSTRUMENT_DELISTED` (not captured, not counted).

This makes `catalogue-active-on-D == manifest-captured-on-D` an exact, reconcilable equivalence (modulo genuine capture
failures).

---

## Background — the off-by-one that motivated this rule

On 2026-06-27, the operator observed:

| Source                                | KALSHI             | POLYMARKET         | Total  |
| ------------------------------------- | ------------------ | ------------------ | ------ |
| Catalogue "open markets after Jun 27" | 13,865             | 3,223              | 17,088 |
| Manifest "captured Jun 26"            | ~8,093 (cqg grain) | ~1,550 (cqg grain) | ~9,643 |

The 2,177-market difference was caused by prediction markets that:

1. Settled on Jun 26 — so they were **captured in the manifest on Jun 26** (instrument_count++).
2. Had `available_to = Jun 26` in the catalogue (last snapshot day they appeared) — so they were correctly **excluded
   from "active after Jun 27"**.

This was NOT a bug in the counts per se — the settlement-day boundary was already correct for the
`available_to = lc.last_day` fallback path. However, the convention was not explicitly documented, and the
`settlement_time` / `available_to_datetime` fields were not being used to set `available_to`, causing `available_to` to
drift to whatever future snapshot day the market last appeared in (e.g. a market that settles Jun 26 but appears in a
Jun 29 future-dated snapshot would get `available_to = Jun 29` instead of `Jun 26`).

---

## Implementation

### Catalogue builder (`instruments-service/scripts/build_instrument_catalogue.py`)

The `build_prediction_catalogue_dataframe` function's `_emit` inner function now:

1. Reads the settlement date from `lc.settled` (populated from `end_date_iso`, `settlement_time`, or
   `available_to_datetime` — whichever the venue's snapshot carries).
2. If `lc.settled` is non-null, sets `available_to = settlement_date` (venue-declared, inclusive).
3. If `lc.settled` is null (no settlement date in any snapshot), falls back to `lc.last_day` with the open-ended `None`
   rule (`None` when `last_day >= latest_day`).

The `settled` field extraction reads from (in priority order):

- `end_date_iso` — raw Polymarket API format
- `settlement_time` — explicit settlement field
- `available_to_datetime` — IS-normalised KALSHI snapshot format

### Enumerator (`instruments-service/scripts/enumerate_expected_universe.py`)

No changes required. The enumerator already uses the date-range check:

```
date < available_from  → EXPECTED_INSTRUMENT_NOT_LISTED
date > available_to    → EXPECTED_INSTRUMENT_DELISTED
```

which correctly applies the inclusive-settlement-date boundary.

---

## Scope

This rule applies to **prediction markets only** (KALSHI, POLYMARKET).

- **CeFi/DeFi/TradFi**: `available_to` = venue-truth expiry/delisting (§7.3 rule — different semantics, not
  settlement-based). See `build_catalogue_dataframe` `§7.3` logic.
- **Sports**: `available_to` = last league-seen day. Different entity (leagues, not markets).

---

## Logical-reconciliation check

To verify `catalogue-active-on-D == manifest-captured-on-D`, run:

```bash
cd instruments-service
python3 scripts/check_prediction_catalogue_manifest_reconciliation.py \
    --dates 2026-06-25 2026-06-26 2026-06-27 \
    --tolerance 50
```

Or use the unit test:

```bash
PYTEST_UNIT_DIR="tests/" .venv/bin/pytest \
    tests/unit/scripts/test_build_instrument_catalogue.py \
    -k "settlement" -v
```

Expected result after the fix:

- A market with `end_date_iso = 2026-06-26T00:00:00Z` has `available_to = 2026-06-26`.
- Catalogue active on Jun 26 (at cqg grain) ≈ manifest captured on Jun 26 (at cqg grain).
- Same-day-settled markets land CONSISTENTLY on the settlement-day side in both.

---

## Related SSOTs

- `codex/02-data/instruments-foundation-and-catalogue-completeness.md`
- `codex/02-data/availability-manifest-and-data-status.md`
- `instruments-service/scripts/build_instrument_catalogue.py` — `build_prediction_catalogue_dataframe`
- `instruments-service/scripts/enumerate_expected_universe.py` — `_enumerate_v2_prediction`
