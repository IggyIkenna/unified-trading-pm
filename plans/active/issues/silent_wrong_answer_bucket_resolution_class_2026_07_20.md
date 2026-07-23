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

- **`aave_rate_impact` has never been produced.** `strategy-service` reads `feature_group=aave_rate_impact` for
  projected supply APYs. `AaveRateImpactCalculator` exists in features-service and is registered in UAC, but the group
  is absent from the bucket — the seven live groups are flash_loan_availability, health_factor, lending_rates,
  liquidation_events, lst_yields, rewards, risk_params. The path fix landed; the **backfill has not been run**, so that
  read still returns `{}`. It is now a loud absence rather than a silent one, but the projected-APY scaling is still not
  happening.
- **A stray empty bucket exists**: `market-data-tick-prediction-test-{pid}` (0 objects), created by the string-mangling
  smoke harness. Deletion is a prod-adjacent operation and is left for an operator decision under
  `bucket_estate_consolidation_to_sub100_2026_07_13`.
- **23 sports cells exist in PROD but are absent from the UAC enumeration** (BETMGM, BETONLINEAG, BETRIVERS, BETSSON,
BETVICTOR, BETWAY, BOVADA, CASUMO, CORAL, LADBROKES_UK, LIVESCOREBET, MATCHBOOK, PADDYPOWER, SKYBET, SMARKETS, SPORT888,
UNIBET/\_EU/\_UK, VIRGINBET, WILLIAMHILL, + 2 ARBITRAGE_OPPORTUNITY cells), surfaced by the smoke run's
`_augment_with_observed_cells`. Same blind-spot class as the earlier OKX-FUTURES / volatility_index discovery: the
matrix reports a clean sweep over cells it never enumerated.
</content>
