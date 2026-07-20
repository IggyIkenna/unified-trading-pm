---
doc_type: issue
title:
  "DeFi catalogue available_to false-delisting — source-set/TVL pool drop-outs stamped as delistings (contradicts
  foundation-completeness §1.3)"
summary: >-
  Measured on the live prod instruments-store catalogues: cefi spot/perp available_to is HONEST (delistings spread
  across 2020-2026, no recent cluster — the §7.3 thin-day fix holds). DeFi is NOT. build_instrument_catalogue.py's
  available_to roll-up has no DeFi TVL/source-set carve-out, so any pool that drops below its venue's last-full-day
  frontier is stamped available_to=last_day (branch 4) — even when the pool contract is still live on-chain and merely
  fell below the top-N/TVL capture threshold or was dropped by a subgraph/seed pool-set change. Signature is decisive:
  the SAME date 2026-06-26 is a delisting cluster across FOUR unrelated protocols (TRADER_JOE_V2 305, PANCAKESWAP_V3
  243, AAVE_V3 116, MORPHO 6), and MORPHO shows 1,718 long-lived markets dropping on 2026-07-06/08 — four independent
  protocols do not organically delist on one day. This directly contradicts codex
  instruments-foundation-and-catalogue-completeness §1.3 (a DeFi TVL-drop is EXPECTED_NOT_ENOUGH_TVL, NOT a delisting,
  and must NOT set available_to). Downstream harm is real: UTL instrument_date_filter EXCLUDES the pool from the
  universe for every day after the false available_to, and legacy_reason_classifier stamps its post-date absence
  EXPECTED_INSTRUMENT_DELISTED — so the pool silently leaves the honest-coverage denominator while still live on-chain.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-trading-library, market-tick-data-service, deployment-api]
scope: [engineer, admin]
tags:
  [
    data-correctness,
    defi,
    catalogue,
    available_to,
    false-delisting,
    honest-coverage,
    ssot-contradiction,
    not-enough-tvl,
  ]
related:
  [
    instruments_foundation_and_catalogue_completeness,
    defi-completeness-oracle,
    defi_consolidated_closeout_2026_07_18,
    defi_master,
  ]
created: 2026-07-20
priority: P1
parent_epic: instruments_master
source: "Live prod catalogue measurement (slot-3, 2026-07-20) — instruments-store-{cefi,defi}-prd catalog.parquet"
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
---

# DeFi catalogue `available_to` false-delisting

## Why this exists (provenance, 2026-07-20)

Surfaced from an operator Q&A about what the deployment-UI data-status page's `available_to` means for spot/perp, then a
measurement of the live prod catalogues to verify the claim "for spot/perp, `available_to` is `None` when active and a
real last-seen only for a genuine delisting." The dispatched check was: **does non-blank `available_to` on non-expiring
instruments correspond to genuine delistings only?** Answer: **cefi yes, DeFi no.**

Reader background (deployment-UI thread): the catalogue `available_to` is a 3-way overloaded value — expiry (dated
FUTURE/OPTION/COMBO) / `None` (active) / last-seen (delisting). It is set by
`instruments-service/scripts/build_instrument_catalogue.py` and consumed as the per-instrument lifecycle upper bound.

## The finding

`build_instrument_catalogue.py:1534-1541` decides `available_to`:

```python
if agg.delisted_at is not None:      available_to = agg.delisted_at   # never populated (0 rows workspace-wide)
elif agg.expiry is not None:         available_to = agg.expiry        # None for pools/perp/spot
elif venue_full_day and agg.last_day >= venue_full_day: available_to = None   # active
else:                                available_to = agg.last_day      # <-- branch 4: "delisted"
```

The only liveness test is §7.3 "present on the venue's last FULL trading day" (`_venue_last_full_day`, thin-day-aware).
That guard defends against a thin/partial _latest day_ mass-false-delisting a venue. It does **NOT** defend against a
**subset** of a venue's pools dropping out on a genuinely-full day. For DeFi, that subset drop-out is routine and
non-delisting: a pool falls below the top-N/TVL capture threshold, or a subgraph/seed pool-set regeneration changes the
returned pool list. Every such pool falls to branch 4 and is stamped `available_to = last_day` → **classified as a
delisting**. There is no TVL / on-chain-existence check in this decision (the `force_include` TVL-exempt marker at
:349/:3450 is a separate column, not part of the `available_to` liveness decision).

## Evidence (measured, live prod, 2026-07-20)

Source: `instruments-store-{cefi,defi}-prd-central-element-323112/prod/catalog.parquet`. Non-expiring = instrument_type
∉ {FUTURE, OPTION, COMBO} (i.e. SPOT_PAIR / PERPETUAL / DeFi pools+markets).

### cefi — HONEST (control; the §7.3 fix works)

- 13,817 spot/perp rows; 30.9% carry non-blank `available_to`.
- Recency of those: **87.5% are >90 days old**, only **0.5% (20 rows) land on the latest scanned day** (2026-07-18).
- Per high-delist venue, `available_to` spans **years**, no recent cluster: BITFINEX-SPOT 428/568 spanning
  2020-11-16..2026-07-04 (0 at 0d, 0 at 1-3d); OKX-SPOT 514/1,398 spanning 2020-10-11..2026-07-03; BYBIT-SPOT 440/959
  spanning 2022-02-17..2026-07-17.
- Verdict: genuine spot-pair churn. The "everything expires on the last capture day" failure mode does **not** occur for
  cefi.

### DeFi — FALSE-DELISTING (the finding)

Cross-protocol single-date clusters of **long-lived** pools:

| venue          | delisted / total (spot·perp·pool) | cluster date(s)                         | n at date   | first-seen span of the clustered rows |
| -------------- | --------------------------------- | --------------------------------------- | ----------- | ------------------------------------- |
| TRADER_JOE_V2  | 305 / 609                         | **2026-06-26** (100% of its delistings) | 305         | 2021-11-10 .. 2025-11-27              |
| PANCAKESWAP_V3 | 436 / 929                         | **2026-06-26** / 2026-07-06             | 243 / 131   | 2020-01-20 .. 2026-07-14              |
| AAVE_V3        | 125 / 292                         | **2026-06-26**                          | 116         | 2022-03-11 .. 2026-03-30              |
| MORPHO         | 1,845 / 2,723                     | 2026-07-06 / 2026-07-08                 | 1,287 / 431 | 2023-12-28 .. 2024-06-18              |

Two independent tells that these are NOT organic delistings:

1. **`2026-06-26` is a shared cluster date across four unrelated protocols.** Independent DeFi protocols do not
   organically delist on the same calendar day. That is a pipeline/capture event (a pool-set regeneration / subgraph
   provider change / seed refresh on that date), not 664 pools independently dying.
2. **The clustered pools are long-lived** (first-seen back to 2020-2021), yet all share one last-seen date. Organic pool
   death spreads across time; a shared last-seen date is a feed drop.

The venues remain captured after the cluster date (each still has hundreds of `available_to=None` active rows), so this
is a _subset_ pool-set change — exactly the case the §7.3 thin-day guard does not cover.

## SSOT contradiction

`codex/02-data/instruments-foundation-and-catalogue-completeness.md` §1.3 (**HARD**):

> a DeFi **pool** leaving the active set because its TVL fell below threshold is a **legitimate
> `EXPECTED_NOT_ENOUGH_TVL` day, NOT a delisting and NOT a capture bug**. … the DeFi active-drop reason space is
> `{delisting (available_to set), TVL-below-threshold (NOT_ENOUGH_TVL)}`.

The intended model: a TVL/threshold/source-set drop keeps the pool **listed** (`available_to=None`) with a per-day
`NOT_ENOUGH_TVL` reason. The roll-up instead **sets `available_to`** for these pools — collapsing the two-outcome space
into "delisting" and losing the `NOT_ENOUGH_TVL` distinction. Code contradicts the documented SSOT model.

## Downstream harm (confirmed consumers)

`available_from → available_to` is the per-instrument lifecycle window (codex §193: it defines the EXPECTED coverage
window). Consumers in UTL:

- `unified_trading_library/domain/instrument_date_filter.py`:
  `if available_to is not None and target_utc > available_to:` → the instrument is **excluded from the universe** for
  every day after `available_to`.
- `unified_trading_library/legacy_reason_classifier.py`: days after `available_to` → **`EXPECTED_INSTRUMENT_DELISTED`**
  → the pool's post-date absence is scored _legitimately absent_ in honest-coverage, not a real gap.

Net: a pool false-delisted on 2026-06-26 (a) disappears from the enumerated universe after that date, and (b) its
missing data is counted as "expected (delisted)". Coverage reads complete while a still-live pool has been silently
dropped — the exact honest-coverage violation §1.3 exists to prevent.

## Certainty + the one remaining verification

CONFIRMED: the measurement, the mechanism (code-read), the SSOT contradiction, and the consumer harm. The cross-protocol
shared date alone makes "these are not organic delistings" essentially certain. The single remaining upgrade from
strongly-evidenced → gold-standard is an **on-chain spot-check**: pick ~10 TRADER_JOE_V2 pools stamped
`available_to=2026-06-26` and confirm via the factory/subgraph that the pool contract still exists (and/or still has
TVL) after that date. `codex/02-data/defi-completeness-oracle.md` §12 already defines the Tier-A factory / Tier-B RPC
truth probes to do this.

## Proposed fix directions (operator/architecture decision — do NOT silently mutate available_to semantics fleet-wide)

The blast radius spans universe filtering + coverage denominators + manifest reason classification across
instruments-service / UTL / MTDS / deployment-api, so the approach is an operator/design call:

- **A (codex-faithful) — never derive `available_to` for a DeFi pool from last-seen.** Keep `available_to=None` for
  pools unless there is on-chain/venue truth that the pool contract was removed; route below-threshold / source-set
  drop-outs to the per-day `NOT_ENOUGH_TVL` reason (the model §1.3 already prescribes). Removes branch-4 for DeFi
  entirely.
- **B (truth-gated delisting)** — only stamp `available_to` for a pool when the §12 factory/registry probe confirms the
  pool contract no longer exists on-chain; otherwise `None` + `NOT_ENOUGH_TVL`. Most correct, adds a probe dependency to
  the roll-up.
- **C (cluster guard, minimal)** — detect a same-day drop-out cluster exceeding a per-venue threshold (a pool-set
  change) and refuse to delist that cohort (leave `available_to=None`), analogous to the §7.3 thin-day guard but for
  subset drops. Cheapest, purely heuristic, does not fix the TVL-vs-delisting classification.

Recommendation: **A** — it matches the documented §1.3 model directly and is the smallest correctness surface; layer B's
on-chain gate later where genuine delisting truth is needed.

## Resolution — Option A shipped (2026-07-20, operator-approved "A by default unless truth-gated B")

**Code fix — `instruments-service@c37d4f96`** (`scripts/build_instrument_catalogue.py` +
`tests/unit/scripts/test_build_instrument_catalogue.py`; QG green, 4668 tests pass):

- `build_catalogue_dataframe` gained an `asset_group` kwarg + a DeFi carve-out branch: for `asset_group == "defi"` a
  drop-out that fails the venue-last-full-day liveness check keeps `available_to=None` (never stamps last-seen). The
  duplicate close in `_merge_incremental` Branch 3 is gated identically so full-rebuild and incremental stay in lockstep
  (guarded by `test_incremental_matches_full_rebuild_defi`). Both prod call sites in `run_rollup` pass `asset_group`.
- **Truth-gate seam preserved (this IS the "B when available" hook):** branches 1-2 (`delisted_at` / `expiry`) are
  untouched, so a genuine venue-/on-chain-declared removal still closes a DeFi pool. Option B just needs to FEED
  `delisted_at` from the §12 probe.
- **Gate is `asset_group == "defi"`, NOT `instrument_type == "pool"`** — a critical correction found by re-measuring
  prod: the false-delisting clusters are overwhelmingly `SPOT_ASSET` / `LENDING` / `A_TOKEN` / `DEBT_TOKEN` rows (0 of
  TRADER_JOE_V2's 305, 0 of MORPHO's, 0 of AAVE_V3's are `POOL`), so a pool-only predicate would have fixed almost
  nothing. DeFi has zero dated instrument types, so the asset_group gate is unambiguous and future-proof.

**Probe status (Option B):** the §12 on-chain factory/RPC probe is NOT implemented — codex `defi-completeness-oracle`
§12 labels it "a follow-on plan item" and there is no callable probe outside the sports agentwork checkout. So B is a
tracked follow-on below; A ships now as the correct default with the truth-gate seam ready.

**Verified on real prod data (2026-07-20, in-memory A/B, no prod write):** ran the fixed `build_catalogue_dataframe`
over 2,292 live defi `by_date` snapshots (since 2026-06-20), `asset_group="defi"` vs `"cefi"`. Non-expiring rows
carrying a non-blank `available_to`: LEGACY (cefi) **1,037** (947 on the 06-26/07-06/07-08 cluster dates) → FIXED (defi)
**4** (0 on cluster dates). The 4 residual are genuine `delisted_at`/`expiry` truth-gate rows, correctly retained.
MORPHO 858→0, PANCAKESWAP_V3 74→0 on cluster dates. The carve-out converts the false-delistings to `None` and preserves
the truth-gate exactly as designed. (Prod `catalog.parquet` still carries the stamps until the `--mode full` regen below
runs.)

## Follow-on work (tracked)

- [x] ✅ [DEPLOY] P1. **DONE — prod defi catalogue CORRECTED + verified (2026-07-20).** Ran the `--mode full` regen
      locally at `c37d4f96` against prod: 11,827 rows, **monotonic guard ACCEPT (new=11827 current=11827** — the fix
      changes `available_to` VALUES, not row count), `CATALOGUE_PROMOTED` →
      `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet`, exit_code=0. **Discovery — the
      regen alone was NOT sufficient:** the full rebuild's frozen-tail merge (`close_absent=False`) copies through
      UNCHANGED every prev row absent from the `by_date` corpus (log: "9482 walked rows + 11827 prev → 11827
      preserved"), so 2,345 rows kept their PRE-FIX stamps. Post-regen measurement: 2,349 non-blank `available_to`, of
      which **2,244 (95.5%) sat on the three proven-false cluster dates**. Fixed with a targeted one-off
      `scripts/purge_defi_false_available_to_2026_07_20.py --apply` (clears ONLY the three proven-false cluster dates;
      leaves the 105 non-cluster rows alone as possibly-genuine; row count unchanged; backup →
      `prod/catalog.20260720-122732.falsedelist.bak.parquet`). **VERIFIED FINAL STATE:** non-blank `available_to` 2,349
      → **105**, and **0 on the cluster dates**; the residual 105 spread across many dates (38 / 30 / then 2-4 each) — a
      healthy genuine-delisting distribution with NO cross-protocol single-date cluster. The false-delisting is gone
      from prod.
- [x] ✅ [DATA] P1. **DONE (half) — manifest UN-DELIST applied + VERIFIED on prod (2026-07-20).** Wrote the inverse
      script `instruments-service/scripts/undelist_defi_false_postdelist_eu_2026_07_20.py` (the exact mirror of
      `reclassify_defi_postdelist_eu_2026_06_24.py`, which has NO `--revert`). Selection is purely "manifest says
      `empty_confirmed(EXPECTED_INSTRUMENT_DELISTED)` **and** the CORRECTED catalogue says the instrument is LIVE on
      that cell's date" — so it is **instrument_type-AGNOSTIC** (covers the SPOT_ASSET/A_TOKEN/DEBT_TOKEN/LENDING
      majority the POOL-only `validate_defi_no_delisted_on_live_pool` gate cannot see) while genuinely-closed rows
      (`date > available_to`) are correctly LEFT delisted. **MEASURED RESULT (live `_index`, 45,815,198 rows):
      `EXPECTED_INSTRUMENT_DELISTED` 219,738 → 3,874** — the 215,864 false cells reset to `expected_unattempted` + blank
      `error_reason` (honest-pending, NOT skip-worthy so a re-capture will re-attempt them), and the ~3,874
      genuinely-delisted rows correctly retained. Backup →
      `_index/availability_index.20260720-132755.undelist.bak.parquet`. **GOTCHA worth keeping (cost one failed run):
      the manifest `expected` column is parquet type `string` (`'true'`/`'false'`/null), NOT bool.** Writing a Python
      `True` raises `ArrowTypeError: Expected bytes, got a 'bool' object` at `to_parquet` time. The backup-then-write
      ordering meant the live `_index` was never overwritten (failed SAFE — verified prod unchanged at 219,738 before
      the re-run). The script now derives the literal from the frame itself (`_expected_true_value`) so the encoding
      can't drift again. NOTE `reclassify_defi_postdelist_eu_2026_06_24.py:94` writes `expected = False` (a bool) and
      carries the SAME latent bug.
- [ ] [DATA] P1. **REMAINING half — resolve the 215,864 re-seeded pending-EU cells to a terminal honest state.** They
      are honest-pending now (visible, drags the denominator down) which is strictly better than the false DELISTED, but
      not terminal. **Known scope gap:** `record_catalogue_residual_empty` → `EXPECTED_NOT_ENOUGH_TVL`
      (`_dex_swaps_queries.py:124-163`) is keyed **per POOL** (`instrument_id=pool_address.lower()`,
      `instrument_type='pool'`) and wired only into `dex_pools_handler`/`dex_swaps_handler` — but the un-delisted
      majority is NON-POOL (SPOT_ASSET 1,389 / A_TOKEN 473 / DEBT_TOKEN 469 / LENDING). So a dex re-capture resolves
      only the POOL slice. Open question under investigation: whether a non-POOL residual-empty path exists, and whether
      SPOT_ASSET/A_TOKEN/DEBT_TOKEN even HAVE a per-day capture path (if not, their honest terminal state is a reason —
      or they should not be seeded expected at all — not an indefinite pending EU). The catalogue reset to `None` alone
      does not fix data already written: the defi manifest `_index` still carries `EXPECTED_INSTRUMENT_DELISTED`
      empty_confirmed rows for the clustered dates. **Un-delist script WRITTEN** (`instruments-service/scripts/`
      `undelist_defi_false_postdelist_eu_2026_07_20.py`) — the exact inverse of
      `reclassify_defi_postdelist_eu_2026_06_24.py` (which has NO `--revert`), instrument_type-AGNOSTIC, selects
      "manifest says DELISTED **and** post-regen catalogue says live-on-that-date", resets → pending EU (blank
      `error_reason` = NOT skip-worthy), backup-then-write, `--dry-run`/`--apply`. **Order is load-bearing**: regen →
      un-delist → re-capture → validate (manifest-freshness SKIPS `empty_confirmed`, so un-delist MUST precede
      re-capture). Scope measured: 4 protocols × 19 (venue,chain,date) tuples = 2,519 rows, ~12-24 day forward window.
      **⛔ SUPERSEDED — the "convert to `NOT_ENOUGH_TVL`" remedy above is WRONG. Do NOT do it.** Investigation
      `w3y86f5z8` (2026-07-20) established: `EXPECTED_NOT_ENOUGH_TVL` is a member of `OUT_OF_COVERAGE_WINDOW_REASONS`
      (`_honest_coverage_empty_reasons.py:531`) — the **SAME clipped-from-denominator bucket as
      `EXPECTED_INSTRUMENT_DELISTED` (:530)**. Re-stamping the un-delisted cells with it would REMOVE them from the
      denominator again, reproducing the exact honest-coverage distortion this issue exists to fix, just under an
      honest-sounding name. It also established that (a) no non-POOL residual emitter exists anywhere (the machinery is
      pool-only at all three layers, incl. the `catalogue_pool_ids_for_shard` provider that hard-filters to
      `instrument_type=='pool'`), and (b) SPOT_ASSET/A_TOKEN/DEBT_TOKEN are reference-only HOLDINGS rows with NO per-day
      capture path under their protocol venue — so their cells are structurally unsatisfiable and a re-capture can never
      flip them to `captured`. **The un-delist remains CORRECT and is the completion of THIS issue** (blank- reason EU
      is byte-for-byte the IS enumerator's own seed state; the gap is now visible + scored instead of hidden). Choosing
      the terminal state for those cells is a separate architecture decision, tracked in its own issue:
      `issues/defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md`.
- [ ] [DEFI] P2. **Option B truth-gate — BUILT (ship pending tree-green).** `instruments_service/oracle/`
      `defi_removal_probe.py` + `scripts/run_defi_removal_probe.py` + roll-up integration (`_apply_defi_removals` /
      `_load_defi_removal_map` applied to the FINAL frame of BOTH `build_catalogue_dataframe` and `_merge_incremental`,
      so full/incremental never disagree) + `tests/unit/oracle/` + deployment (`deployment-service`
      `cloud_run_job_registry` `defi-removal-probe` + `terraform/gcp/defi_removal_probe_scheduler.tf`, daily 00:30 UTC
      before the 01:00 catalogue regen). CONSERVATIVE: records a removal ONLY on a positive `eth_getCode`-absent
      confirmation; unresolvable RPC / non-EVM / error → stays live, so it can never re-create a false delisting. Reuses
      `evm_creation_resolver` primitives; writes `_cache/defi_removals.json` (mirrors the genesis
      `_cache/*_creation_timestamps.json` seam). **RUNTIME-VERIFIED on prod 2026-07-20**: 11,827 catalogue rows → 30
      live EVM targets probed via Alchemy → **0/30 confirmed gone** (correct — DeFi contracts persist on-chain, so
      Option A stays and the truth-gate fires only on a genuine SELFDESTRUCT). My tests pass in the QG (4675 passed);
      SHIP is blocked only by an unrelated fleet UAC drift (`unified-api-contracts@6bcff215` narrowed the defi
      denominator → 5 pre-existing golden/producer-set failures another agent is reconciling).

## Blocked: Option B ship is gated on a tree-green that is NOT this issue's defect (2026-07-20)

The Option B code is built, QG-clean **in its own right** (its tests are in the 4,675 passing), and runtime-verified —
but it cannot ship because `instruments-service` `quality-gates.sh` is red on **foreign** failures. Attribution, so the
next agent does not re-diagnose:

1. **`test_expected_matches_golden[sports]` + `test_every_canonical_venue_has_a_uac_entry`** — 20 sports **web
   bookmakers** (BETMGM/BOVADA/BETWAY/BETRIVERS/CORAL/PADDYPOWER/SKYBET/UNIBET/WILLIAMHILL…) are IS canonical venues
   with no UAC `VENUE_TO_ADAPTER_KEY` entry. **Operator ruling 2026-07-20: these are PURE PRICING SOURCES** — odds
   ingested via the aggregator, never order-routed; they must NOT be registered in execution-service for trading.
   Registry confirms: all sit in `SPORTS_BOOKMAKER_WEB_VENUES` (63 members, web-only/no direct API), vs MATCHBOOK in
   `SPORTS_EXCHANGE_VENUES` and NOVIG/PROPHETX in `SPORTS_PREDICTION_MARKET_VENUES`. **Disambiguation:**
   `VENUE_TO_ADAPTER_KEY` is UAC's _reference-data adapter routing_ (which IS adapter discovers instruments), NOT
   execution registration — PINNACLE/DRAFTKINGS/FANDUEL/BETFAIR already sit there with the `NO_ADAPTER_YET` sentinel and
   are not tradeable by virtue of it. So the real question is upstream of the test: **should web-only bookmakers be IS
   "canonical venues" at all, or an odds DIMENSION inside the odds-api feed?** If the latter, the fix is NOT 20
   `NO_ADAPTER_YET` entries — it is not treating them as canonical venues. Operator decision, deliberately untouched
   here.
2. **`test_defi_set_equals_uac_denominator_drift_guard` + `test_rule11_per_ag_dedup_target_counts_byte_unchanged`** —
   pre-existing UAC/IS defi drift.

## Finding: the 4-adapter registration is a COORDINATED change, not a one-liner (2026-07-20)

Diagnosis (workflow `wqdk5dejb`): UAC `VENUE_TO_ADAPTER_KEY` names `meteora`/`lifinity`/`phoenix`/`pyth`, whose adapter
CLASSES exist and are ctor-compatible, but the `factory._ADAPTERS` registration half was never landed — so
`TestAdapterRoutingUACInvariant` is red fleet-wide. (`chainlink` was the 5th and is a genuinely MISSING artifact — no
`adapters/defi/chainlink.py` exists anywhere; another agent has since correctly un-declared it with a documented "no
entry + pipeline phase" interim state, ref BLK-0c7b82fe.)

**I applied the registration, measured the blast radius, and REVERTED it** — because registering 4 venues legitimately
WIDENS the IS-producible set and therefore requires an ATOMIC 4-part landing:

1. `factory._ADAPTERS` + `ADAPTER_DATA_SOURCES` (+5 entries each) — turns
   `test_every_uac_adapter_key_resolves_to_a_class` and `test_adapter_data_sources_covers_all_adapters` green.
   **Verified: both invariants compute clean with it applied.**
2. **`tests/unit/scripts/goldens/expected_universe/defi.json` regen** (+5 rows:
   `LIFINITY/METEORA/PHOENIX-SOLANA pool/dex_pool_state` + `PYTH-SOLANA spot_asset|spot_pair/oracle_prices`) via
   `scripts/regenerate_expected_universe_golden.py`. **Currently BLOCKED** — the regenerator deliberately refuses while
   UAC/UTL (editable path-deps) are dirty, so another agent's in-flight edits can't be baked into the golden. UAC had 8
   and UTL 3 dirty files at the time.
3. **`test_rule11_per_ag_dedup_target_counts_byte_unchanged`** DEFI expected count **89 → 93**.
4. **The IS venue-PRODUCER set** — a DIFFERENT mechanism from `_ADAPTERS` (the drift guard still reported the 4 as
   "UAC-only" WITH the registration applied), living in `scripts/enumerate_expected_universe.py`, which another agent
   currently owns dirty.

Shipping only part 1 would repeat EXACTLY the half-landed-commit defect this issue documents (UAC declaring venues whose
IS half never landed), and violates the rule-11 blast-radius rule (never widen a gate without proving the fleet in the
SAME change). Hence the revert. Land parts 1-4 atomically once UAC/UTL are clean.

## Scope boundary

- **cefi / tradfi**: NOT affected — verified clean for cefi; tradfi non-expiring rows are negligible (mostly dated
  FUTURE/OPTION). This is DeFi-specific.
- The `available_to` overload itself (expiry / None / last-seen) is fine for cefi/tradfi; the defect is applying the
  last-seen branch to DeFi pools without the TVL/on-chain distinction §1.3 requires.

## Reproduction

```
GCP_PROJECT_ID=central-element-323112 instruments-service/.venv/bin/python <<script>>
# read instruments-store-defi-prd .../prod/catalog.parquet; for non-expiring rows, group
# non-blank available_to by (venue, date). A single date carrying a whole cohort of
# long-lived pools across multiple protocols == the false-delisting signature.
```

(Measurement scripts used: slot-3 scratchpad `measure_available_to.py` / `drill_venue_recency.py` /
`defi_cluster_classify.py`, 2026-07-20 — not committed; one-off analysis.)
