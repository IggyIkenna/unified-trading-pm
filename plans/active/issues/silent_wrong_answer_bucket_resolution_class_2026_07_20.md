---
doc_type: issue
title: >-
  Silent-wrong-answer class — a bucket-name fallback that fabricated dead buckets, five live consumers that swallowed
  the resulting 404, and two P&L paths that computed ZERO instead of failing
summary: >-
  UTL's get_bucket_name turned ANY unrecognised token into a plausible-but-nonexistent bucket name via
  `prefixes.get(domain, domain)`. Nothing raised. Five live consumers then caught the resulting NotFound and substituted
  an empty value, so the system produced confident wrong numbers instead of stopping — DeFi positions valued with ZERO
  gas cost, Aave lending P&L computed as ZERO, EigenLayer rewards silently replaced by DefiLlama data, and a prediction
  smoke test that verified against an empty bucket it had created itself and reported green. The root cause is fixed
  (unknown domain now raises BucketNamingError), a second disagreeing copy of the same helper was deleted, and all five
  consumers are corrected and shipped. Six tests were found asserting the fabricated names — the suite was defending the
  bug.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos:
  [
    unified-trading-library,
    strategy-service,
    features-service,
    market-tick-data-service,
    market-data-processing-service,
  ]
scope: [engineer]
tags: [buckets, silent-failure, pnl-correctness, data-correctness, false-green, defi]
related:
  [
    /plans/active/issues/pipeline_smoke_sweep_findings_2026_07_20.md,
    /plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    /plans/archive/issues/backfill_vm_disk_starvation_misdiagnosed_as_tardis_quota_2026_07_18.md,
    /plans/active/issues/aave_rate_impact_structural_zero_defillama_borrow_gap_2026_07_26.md,
    /plans/active/distinct_values_noncanonical_audit_2026_07_20.md,
  ]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend
drift_direction: advance-code
depends_on: []
source:
  [
    "found 2026-07-20 while fixing the prediction bucket gate from the cross-asset-group smoke sweep; the first instance
    was a single wrong token, the class was found by asking what else that fallback hid",
  ]
resolved_by:
locked_by:
---

# The silent-wrong-answer class

## 1. The mechanism

`unified_trading_library/core/cloud_constants.py::get_bucket_name` resolved its prefix with:

```python
prefix = prefixes.get(domain, domain)   # unknown token -> use it verbatim as the prefix
```

Any token that was not a known domain key became its own prefix, producing a **syntactically perfect, semantically
dead** bucket name. `"gas-fees"` became `gas-fees-prd-{pid}`. Nothing raised, nothing logged. The name looked exactly
like a real one in a stack trace, a log line, or a code review.

That is only half the failure. A dead bucket name on its own is a loud 404. What made this class invisible is that
**every consumer caught the 404 and substituted an empty value**, so the wrong answer flowed onward wearing the shape of
a right one.

The general form, and the reason it is worth naming as a class:

> A lookup that cannot fail + a caller that cannot fail = a system that cannot tell you it is wrong.

## 2. Confirmed instances (all fixed + shipped)

| #   | Site                                                    | Wrong token / path                                        | What the system actually produced                                                                                                        | Fix                                       |
| --- | ------------------------------------------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| 1   | `strategy-service` `pnl/engine/pnl_input_builder.py:48` | `"gas-fees"` (kind retired 2026-07-12)                    | NotFound swallowed by a bare except, empty frame **cached for the process lifetime** → every DeFi position valued with **ZERO gas cost** | `strategy-service@bd3822e1`               |
| 2   | `strategy-service` `pnl/engine/orchestrator.py:68,115`  | bucket existed in NO env form + missing `onchain/` prefix | `except Exception` → `return {}` → **Aave lending P&L computed as ZERO** on every run                                                    | `strategy-service@af1ced80`               |
| 3   | `features-service` `eigen_rewards_calculator.py:132`    | `"market-data-tick-defi"` (a name fragment)               | 404 → **silently substituted DefiLlama data** for EigenLayer rewards                                                                     | `features-service@dd286fdc`               |
| 4   | `features-service` 4 calculators + canonical reader     | `"gas-fees"` / `"market-data-tick-defi"`                  | empty frames — gas distribution, IL, invariant drift, vault APY all computed on nothing                                                  | `features-service@dd286fdc`               |
| 5   | `market-data-processing-service` `smoke_matrix.py`      | string-mangled `prediction` → long form                   | **provisioned the wrong bucket, verified against it, reported green** — 0 objects, while the real `-pred-` bucket held 18                | `market-data-processing-service@7aa9b267` |

Instance 5 is the one to remember: the harness did not merely fail to detect a problem, it **manufactured the evidence
of its own success** and left a stray bucket behind against the sub-100 estate consolidation.

## 3. The duplicate that made the root-cause fix only half a fix

After fixing `core.cloud_constants`, a second implementation of the same public name was found in
`cloud_interface/constants.py`, exported through a second public door:

```
from unified_trading_library import get_bucket_name                 -> core.cloud_constants          (fixed)
from unified_trading_library.cloud_interface import get_bucket_name -> cloud_interface.constants     (still broken)
```

Executed side by side, **6 of 7 sampled domains disagreed** — no `-prd-` env tier, `prod` where the real name is `prd`,
and `prediction` where the real name abbreviates to `pred`. Every disagreement is a bucket that does not exist. It also
still carried the `prefixes.get(domain, domain)` fallback that had just been removed from the canonical, and
`core/seed_writer.py` imports through that door.

Its `ml FOLD B` comment had patched `prod`→`prd` **for ml domains only** — which is precisely why the breakage stayed
invisible for every other domain: the one place someone looked, they fixed locally instead of asking why the shape was
wrong at all.

Deleted; the name is now re-exported from the canonical so there is one implementation. Verified: same object through
both doors, no import cycle in either import order. `unified-trading-library@f82a159a`.

## 4. The tests were defending the bug

Six assertions pinned the fabricated values, meaning **the suite would have failed against correct code**:

- `assert captured["bucket_domain"] == "gas-fees"` — pinned a retired kind.
- `assert captured["bucket_domain"] == "market-data-tick-defi"` — pinned a name fragment.
- `assert get_market_data_bucket("CEFI") == "market-data-tick-cefi-p"` — pinned the pre-env-tiering name.
- `assert get_instruments_bucket("TRADFI") == "instruments-store-tradfi-p"` — same.
- `assert "features-onchain" in get_features_onchain_bucket()` — asserted a **substring of a bucket shape that exists in
  no env form**, so a fabricated name satisfied it.
- `test_unknown_domain_uses_domain_as_prefix` — a test whose _name_ codified the footgun as intended behaviour,
  asserting `== "unknown_domain-proj"`.

A mock had also drifted: a 1-arg lambda stubbing what is now a 2-arg helper, so the test passed while the real signature
had moved on.

**The lesson for review**: an assertion that a bucket name is _truthy_, or _contains a substring_, proves nothing — a
fabricated name satisfies both. Pin equality against the resolver, and assert that a wrong token RAISES.

## 5. What actually stops recurrence

Deleting the fallback is the fix; the rest is what makes it stay fixed.

1. **`get_bucket_name` raises `BucketNamingError`** on an unknown domain, listing the valid ones and naming the other
   vocabulary — because the two-vocabulary confusion is the honest reason this keeps happening:
   `resolve_bucket_name(kind="market-data", ...)` takes a HYPHENATED kind, `get_bucket_name("market_data", ag)` takes an
   UNDERSCORED domain. Both are correct APIs. Neither is wrong. They are one character apart.
2. **One implementation per public name.** Two doors onto the same concept will drift, and the drift will be invisible
   precisely because both look authoritative.
3. **Probe, do not describe.** `gcloud storage buckets describe` needs `storage.buckets.get`, which `unified-trading-sa`
   does not have — it 403s for every bucket including ones being actively read. A describe-based gate false-negatives
   everything and, followed literally, provisions duplicates. Use object-level `gcloud storage ls`, which distinguishes
   MISSING (404) from EXISTS-but-EMPTY.

## 6. Open

- ✅ **`aave_rate_impact` backfill — RUN 2026-07-26** (`features-service`, data-only, no code change): the group was
  never produced because this calculator is batch-incompatible for any date before today (DefiLlama Yields is a
  live-only source — confirmed in `orchestrator.py`'s own `FEATURE_GROUP_SKIPPED_BATCH_INCOMPATIBLE` skip, live-mode is
  the only path that can ever write it), so "the backfill" can only mean "run it for today." Ran
  `python -m features_service --feature-family onchain --operation compute --mode batch --asset-group DEFI --feature-group rate_impact --start-date 2026-07-26 --end-date 2026-07-26 --force --skip-dependency-check`
  (`--skip-dependency-check` bypasses the blanket onchain MTDS-manifest preflight gate, which this calculator's
  DefiLlama-only `fetch_data` doesn't need). **Result**: 71 rows written to
  `gs://features-defi-prd-central-element-323112/onchain/by_date/day=2026-07-26/feature_group=rate_impact/features.parquet`,
  read back and verified non-empty / zero `NaN`. **But every one of the 4 output columns reads back as a deterministic
  `0`** — DefiLlama's `/pools` endpoint returns `totalBorrowUsd=None` for all 16,092 pools it serves (verified, not
  sampled), which zeroes utilization and, given every UAC rate-model default's `base_rate=0.00`, zeroes both the supply-
  and borrow-side outputs by construction, for every symbol, every day, regardless of real market state — a NEW instance
  of exactly this doc's own silent-wrong-answer class (non-empty/non-NaN but numerically meaningless). Filed, not fixed
  here (the fix is a data-source migration, not a backfill — MTDS `lending_indices` already carries real borrow-side
  fields per the un-executed Step-4 tail of `/plans/archive/issues/aave_irm_slope_capture_dropped_2026_05_12.md`):
  `/plans/active/issues/aave_rate_impact_structural_zero_defillama_borrow_gap_2026_07_26.md`. Separately (already
  tracked there, not re-litigated here): the writer name (`rate_impact`, post-2026-07-21 UAC rename) still doesn't match
  strategy-service's reader (`aave_rate_impact`) per
  `/plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`, so projected-APY
  scaling is still not reaching the P&L engine even with this run done.
- **A stray empty bucket exists**: `market-data-tick-prediction-test-{pid}` (0 objects), created by the string-mangling
  smoke harness. Deletion is a prod-adjacent operation and is left for an operator decision under
  `bucket_estate_consolidation_to_sub100_2026_07_13`.
- ⚠️ **23 sports cells item — NOT actioned, premise superseded by a later operator ruling (checked 2026-07-26, left
unflipped).** Re-read against the current UAC registry: 16 of these 23 names (BETMGM, BETONLINEAG, BETRIVERS, BETSSON,
BETVICTOR, BETWAY, BOVADA, CASUMO, CORAL, LIVESCOREBET, MATCHBOOK, PADDYPOWER, SKYBET, UNIBET, VIRGINBET, WILLIAMHILL)
are 16 of the 20 ODDS_API fan-out bookmakers the operator explicitly ruled OUT of canonical registration two days after
this doc was written — `plans/active/distinct_values_noncanonical_audit_2026_07_20.md` § "Operator decisions — RULED
2026-07-22": _"do NOT add them, in fact remove them everywhere so they don't come up in audit"_ — SHIPPED at
`unified-api-contracts@9908520b` / `deployment-api@5295c76` as `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS` (a
deliberate NON-canonical accepted-exception set, never merged into `VENUES_BY_ASSET_GROUP`). Adding them to the
canonical registry now — the literal ask here — would directly revert that shipped, dated operator decision. The
remaining 7 cells (LADBROKES_UK, SMARKETS, SPORT888, UNIBET_EU, UNIBET_UK, the 2 ARBITRAGE_OPPORTUNITY cells) are NOT
named one way or the other in that audit's own 2026-07-25 refresh (sports venues stood at 7/14 non-canonical, not
individually enumerated there) and sit inside that same actively-in-flight plan's scope, not this one — findings-triage
"fits another plan → annotate it, don't fix (collision risk)" applies. Left unflipped rather than guessed at partially;
the correct owner is `distinct_values_noncanonical_audit_2026_07_20.md`, which already has the live census machinery and
the operator's ear on this exact registry.
</content>
