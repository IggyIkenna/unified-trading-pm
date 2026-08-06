---
doc_type: issue
title: >-
  DEFI:onchain benchmark blocked on two dep-check failures — BLAZESTAKE attempted_failed rows in lst_rates (persists
  every date), lending_indices stalled after 2026-07-31
summary: >-
  DEFI:onchain VM (features-e2e-defi-20260806-025432-onch5, start_date=2026-07-27) failed exit_code=1: DependencyChecker
  found 3 deps failing. Root-cause analysis: (1) lst_rates — BLAZESTAKE venue has `attempted_failed` rows on every date;
  `_evaluate_manifest_rows` treats ANY attempted_failed row as a dep failure (no known-outage exemption for BLAZESTAKE
  in `_KNOWN_OUTAGE_VENUES_BY_SVC`). A blazestake→SOLBLAZE-SOLANA canonical-migration shard (2026-08-06T02:45Z) adds
  SOLBLAZE-SOLANA captured rows but does NOT delete the old BLAZESTAKE attempted_failed rows — so the dep check still
  fails post-merge. (2) lending_indices — stalled after 2026-07-31; no captured data for 2026-08-01+. Net: no single
  date satisfies BOTH (dates ≤2026-07-31 fail lst_rates, dates ≥2026-08-01 fail lending_indices). (3) perp_funding
  (HYPERLIQUID/CEFI bucket) — captured 2026-07-30+ (passes), was fine once the cefi-bucket path fix shipped (Option B,
  2026-08-01 issue). TRADFI:volatility is under a SEPARATE issue doc.
status: open
nature: issue
asset_group: [defi]
stage: [data, features]
repos: [features-service, market-tick-data-service]
scope: [engineer, admin]
tags: [defi, onchain, dep-check, lst-rates, lending-indices, blazestake, data-availability]
related:
  [
    /plans/archive/issues/defi_onchain_perp_funding_permanently_unsatisfiable_dependency_2026_07_31.md,
    /plans/active/issues/defi_oracle_prices_capture_stalled_since_2026_07_22.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
  ]
created: 2026-08-06
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
resolved_by:
source: >-
  slot-5 (data_engineering), 2026-08-06: post-VM log analysis for data_pipeline_check_mdps_features-056
---

## Finding summary

**VM**: `features-e2e-defi-20260806-025432-onch5`, start_date=2026-07-27, exit_code=1

**3 failing deps on date 2026-07-27:**

| Service key                      | data_type       | Failure reason                                                   |
| -------------------------------- | --------------- | ---------------------------------------------------------------- |
| market-tick-data-service-lst     | lst_rates       | 1 attempted_failed shard (BLAZESTAKE) — re-run MTDS              |
| market-tick-data-service-lending | lending_indices | 6 attempted_failed shards (2026-07-27); stalled after 2026-07-31 |
| market-tick-data-service-perp    | perp_funding    | no HYPERLIQUID row on 2026-07-27                                 |

**Note**: vault_share_price and oracle_prices passed for 2026-07-27. perp_funding passes for dates ≥2026-07-30
(HYPERLIQUID captured from 2026-07-30).

## Root cause: lst_rates / BLAZESTAKE

`_evaluate_manifest_rows` (dependency_checker.py:142): ANY `attempted_failed` row causes failure, even if 33 other rows
are `captured`. `_KNOWN_OUTAGE_VENUES_BY_SVC` only exempts `POLYMARKET_PERP`/`BINANCE-DELIVERY` for
`market-tick-data-service-perp` — no exemption for BLAZESTAKE.

BLAZESTAKE (venue `BLAZESTAKE`, instrument `blazestake-solana:lst:bsol`) has `attempted_failed` lst_rates on:
2026-07-28, 2026-07-29, 2026-07-30, 2026-07-31, 2026-08-04, 2026-08-05.

A canonical-migration shard (`canonical-migration-defi-blazestake-retire-20260806-024520.parquet`) adds
`SOLBLAZE-SOLANA/bSOL/captured` rows for historical dates but does NOT delete/overwrite the old
`BLAZESTAKE/blazestake-solana:lst:bsol/attempted_failed` rows — they have different (venue, instrument_id) keys in the
dedup index.

## Root cause: lending_indices stall

DEFI MTDS capture for `lending_indices` stalled after 2026-07-31. The per_vm shards directory has NO lending_indices
shard newer than the pre-2026-08-01 index. Root cause of the stall is out of scope for this issue (separate MTDS capture
investigation needed).

## No-overlap constraint

- Dates ≤2026-07-31: lst_rates fails (BLAZESTAKE attempted_failed on 28th/29th/30th/31st)
- Dates 2026-08-01+: lending_indices missing (stalled); also lst_rates missing for 2026-08-01 to 2026-08-03

There is no date where BOTH lst_rates AND lending_indices pass the dep check.

## Resolution options

**Option A (code fix, recommended)**: Add `BLAZESTAKE` to `_KNOWN_OUTAGE_VENUES_BY_SVC` for
`market-tick-data-service-lst` in `dependency_checker.py`. BLAZESTAKE is being retired (canonical migration 2026-08-06)
— its `attempted_failed` rows represent the retirement transition, not a data gap relevant to the onchain feature
consumer (which reads `bSOL` staking yields, now under SOLBLAZE-SOLANA in canonical form). After Option A, the effective
date range shrinks to 2026-07-29+ (where lending_indices+lst_rates both pass).

**Option B (manifest fix)**: Set BLAZESTAKE's attempted_failed rows to `empty_confirmed` in the DEFI MTDS index.
Requires a one-off manifest manipulation script — more invasive than Option A.

**Option C (MTDS fix)**: Resume `lending_indices` capture past 2026-07-31. Unblocks 2026-08-01+ dates (subject to
BLAZESTAKE still blocking — Option A still needed).

**Operator decision needed**: Confirm Option A (code fix to dep checker for BLAZESTAKE known-outage) or Option B
(manifest cleanup). This is `BLOCKED-OPERATOR-DECISION` until confirmed.

## Todos

- [ ] [OPERATOR] P1. **Confirm resolution path for BLAZESTAKE blocking lst_rates dep check** — Option A (add BLAZESTAKE
      to known-outage exemption in `dependency_checker.py`) is recommended; BLOCKED until operator signs off (affects
      dep-check behavior).
- [ ] [DATA] P1. **Implement chosen option and relaunch DEFI:onchain benchmark VM** — once dep check passes for any
      date, relaunch `launch-features-vm.sh FAMILY=onchain ASSET_GROUP=DEFI start_date=<clean_date>` and capture
      throughput numbers for -056. Target date: 2026-07-29 or 2026-07-30 (if Option A ships + lending_indices present
      through 2026-07-31).
- [ ] [DATA] P2. **Investigate lending_indices capture stall (post-2026-07-31)** — diagnose why DEFI MTDS isn't writing
      lending_indices rows for 2026-08-01+; may require a separate issue in MTDS.

## Progress Log

- **2026-08-06 (slot-5, data_engineering)**: diagnosed from VM exit_code=1 log. Filed this issue. BLAZESTAKE
  attempted_failed + lending_indices stall = no valid date for the dep check. Recommended Option A (known-outage
  exemption code fix). BLOCKED-OPERATOR-DECISION.
