---
name: Correct Master Plan Errors
overview: "Apply 6 targeted corrections to the master plan file at .cursor/plans/multi-tf_cascade_signal_architecture_3fcd8384.plan.md based on code verification: fix wrong feature group names, add schema migration to percentile fix, complete the HFT done table, redirect geopolitical signal to existing sentiment group, and clarify cross-instrument base class status."
todos:
  - id: fix-calendar-group-names
    content: "Fix wrong calendar feature group names in Section 5 and feed-all-22-groups todo: macro_dxy -> dxy_momentum, news_sentiment + social_sentiment -> sentiment (verified against actual CALCULATOR_REGISTRY decorators in features-calendar-service)"
    status: completed
  - id: add-schema-migration-to-percentile-fix
    content: "Update cross-instrument-fix-percentile-features todo and Section 1 to explicitly require: update output_features in realized_implied_vol.py (line 68), verify no downstream ML consumer breaks on column removal, treat as breaking schema change requiring version bump"
    status: completed
  - id: complete-hft-done-table
    content: "Add missing confirmed-done features to Section 1 HFT done table: spread_breach, imbalance_extreme, extreme_bid_imbalance, extreme_ask_imbalance (binary, auto-generate time_since), time_to_volume_{1000,5000,10000}. Note binary events are candidates for multi-horizon binary expansion."
    status: completed
  - id: remove-geopolitical-calculator
    content: Remove cross-instrument-geopolitical todo. Update Section 2 architecture to remove geopolitical_risk from cross-instrument extensions. Add note that CryptoPanic geopolitical signal is already captured by the sentiment feature group (calendar service, Tier 4 HFT plan).
    status: completed
  - id: clarify-base-class-time-since
    content: "Update Section 0 Rule 2: both delta-one (pandas) and cross-instrument (Polars) base classes already auto-generate raw time_since integers. Multi-horizon binary encoding is a replacement, not filling a gap. Requires adding _add_event_horizon_binaries() to both base class variants."
    status: completed
isProject: false
---

# Corrections to Master Plan

## Target file

`[.cursor/plans/multi-tf_cascade_signal_architecture_3fcd8384.plan.md](.cursor/plans/multi-tf_cascade_signal_architecture_3fcd8384.plan.md)`

## Change 1 — Fix calendar/onchain feature group names (Section 5, line 604-607)

Wrong names will cause silent subscription failures in ml-training-service.

**Remove:**

```python
"macro_dxy", "yield_curve", "news_sentiment", "social_sentiment",
```

**Replace with (verified from `features_calendar_service` CALCULATOR_REGISTRY decorators):**

```python
"dxy_momentum", "yield_curve", "sentiment",  # calendar service actual names
```

Also update the `feed-all-22-groups` todo content to use the corrected names.

---

## Change 2 — Schema migration note for vol_percentile fix (todo + Section 1)

The existing `cross-instrument-fix-percentile-features` todo says "replace" but omits the required follow-on changes. The `output_features` property in `realized_implied_vol.py` (line 68) explicitly lists `vol_percentile_{window}`, and the output schema at `features_cross_instrument_service/schemas/output_schemas.py` defines the `realized_implied_vol` group.

**Update todo to add:**

> After replacing, update `output_features` in `realized_implied_vol.py` (remove `vol_percentile_{window}`, add `vol_high_vs_30d`, `vol_low_vs_30d`, `vol_extreme_high_30d`, `rv_iv_ratio_extreme`, `rv_iv_inverted`). Verify no downstream ML consumer directly indexes by column name on this group — if any do, the column rename is a breaking schema change requiring a version bump.

---

## Change 3 — Complete HFT done table (Section 1)

The Tier 1 delta-one row omits features confirmed present in `microstructure.py`:

**Current row:**

```
Tier 1 delta-one | amihud_illiquidity_*, vpin_*, kyles_lambda_*
```

**Corrected row:**

```
Tier 1 delta-one | amihud_illiquidity_*, vpin_*, kyles_lambda_*, spread_breach,
                   imbalance_extreme, extreme_bid_imbalance, extreme_ask_imbalance
                   (all binary — auto-generate time_since via delta-one base class),
                   time_to_volume_{1000,5000,10000} (volume clock, continuous)
```

Also add a note that `spread_breach`, `imbalance_extreme`, `extreme_bid_imbalance`, `extreme_ask_imbalance` already benefit from the existing `_add_time_since_events()` in the delta-one base class — they will also need multi-horizon binary horizon expansion under the `replace-time-since-with-binary-horizons` todo.

---

## Change 4 — Remove geopolitical_risk calculator, keep signal via sentiment

The `cross-instrument-geopolitical` todo proposes a new keyword-based NLP calculator for CryptoPanic. But:

- CryptoPanic is already integrated as the `sentiment` feature group in `features-calendar-service`
- `"sentiment"` is already in the corrected ML feature list (Change 1)
- The noisy signal is preserved — it just arrives via the existing `sentiment` group rather than a hand-crafted keywords extractor

**Remove** the `cross-instrument-geopolitical` todo from the frontmatter.

**Update** the Layer 3a architecture note (Section 2) to remove `geopolitical_risk` from the "What it still needs" list and the architecture text block.

**Add note** in Section 2: "Geopolitical event risk is captured by the existing `sentiment` feature group (CryptoPanic news feed, already implemented in HFT Tier 4). The ML model learns which sentiment signals are informative in which regime via SHAP. A hand-crafted keyword extractor would add fragility without clear alpha improvement over the general sentiment signal."

---

## Change 5 — Cross-instrument base class clarification (Section 0, Rule 2)

The reviewer claimed the cross-instrument base has no time-since machinery. **This is wrong** — `base_calculator.py` has Polars-based `_add_time_since_events()` confirmed by code verification.

However the valid concern remains: **multi-horizon binary encoding does not exist in either base class**. Both delta-one (pandas) and cross-instrument (Polars) auto-generate raw `time_since_{event}` integers, not horizon-banded binaries.

**Update Rule 2 note** to clarify:

> Both `features_delta_one_service/app/calculators/base.py` and `features_cross_instrument_service/app/calculators/base_calculator.py` already auto-generate raw `time_since_{event}` integers from any binary column. The multi-horizon binary encoding (`{event}_in_last_{1,3,5,10,20,50}_bars`) is a replacement pattern, not filling a missing capability. Implementation requires adding a `_add_event_horizon_binaries()` method to both base classes (pandas and Polars variants), replacing the current `_add_time_since_events()` output, or running both in parallel if raw time_since is wanted for other purposes.

---

---

## Summary of Changes


| #   | Location                    | Change                                                                                                |
| --- | --------------------------- | ----------------------------------------------------------------------------------------------------- |
| 1   | Section 5 code block + todo | Fix calendar group names: `macro_dxy`→`dxy_momentum`, `news_sentiment`+`social_sentiment`→`sentiment` |
| 2   | todo + Section 1            | Add schema migration steps to vol_percentile fix                                                      |
| 3   | Section 1 done table        | Add 4 binary events + time_to_volume to delta-one done row                                            |
| 4   | todo + Section 2            | Remove geopolitical_risk todo; note sentiment covers it                                               |
| 5   | Section 0 Rule 2            | Clarify both base classes have time-since; multi-horizon is a replacement, not filling a gap          |
|     |                             |                                                                                                       |
