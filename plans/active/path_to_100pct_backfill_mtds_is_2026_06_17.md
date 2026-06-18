---
title: Path to 100% — post-migration backfill across MTDS + instruments-store
created: 2026-06-17
parent_epic: mtds_mdps_master
assigned_vm: vm-operator-ops
status: active
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 20
estimate_calibrated_ai_days: 16
locked_by: live-defi-rollout
locked_since: 2026-06-17
source:
  - operator 2026-06-17 ("after the migration, what's left to have everything backfilled to 100% across MTDS and IS?")
  - depends on plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md (the migration +
    manifest-honesty work)
  - audit: plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md
---

# Path to 100% — post-migration backfill (MTDS + instruments-store)

> **🟡 GATED — starts AFTER the v9 migration lands.** This plan does NOT begin until
> `instruments_mtds_subset_consistency_remediation_2026_06_17.md` has shipped the rebuild-script fixes, regenerated the
> projections, and run `--apply` per-AG. The migration backfills NOTHING — it makes the manifest HONEST + canonical and
> gives a TRUE denominator + accurate gap list. THIS plan then drives the actual data backfill to 100%.

## Definition of 100% (read this first)

**100% = `captured` covers 100% of the COULD-EXIST universe**, i.e. `attempted_failed = 0` AND
`expected_unattempted = 0` per AG. **Honest-empty is EXCLUDED from the denominator** and is NOT a gap: pre-genesis
chains, pre-venue-launch, no-fixture days, weekends/holidays, instrument-not-listed, and documented structural gaps
(e.g. VIX/VX uncovered by Massive → Barchart+Yahoo). Formula (UTL/UI SSOT):
`% = captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)` where the target is to drive
`attempted_failed` and `expected_unattempted` to zero — NOT to eliminate honest `empty_confirmed`.

> **Expectation-setting:** post-migration the % will JUMP vs today's dashboard even before any backfill — today's low
> numbers are inflated-missing by recon-noise (cefi 1.4M "failed" → ~88k real) + honest-empty mis-counted. Size the real
> backfill from the REGENERATED projection, not the current one.

## Step 0 (PREREQUISITE) — materialize the could-exist universe (defines "100%")

- [ ] [DATA] P0. **Run the IS `enumerate_expected_universe.py` v2 enumerator + the MTDS instruments-service pre-flight
      `record_expected_unattempted`** so every IS-listed × post-genesis × post-launch × in-coverage cell is seeded as
      `expected_unattempted` at shard grain, per AG. Until this is correct the denominator is undefined and the backfill
      is unsized. Verify: data-status shows a real `expected_unattempted` count per AG (the precise gap list). —
      instruments-service / market-tick-data-service

## Step 1 — MTDS market-data backfill (the bulk: drive expected_unattempted + genuine failed → captured)

- [ ] [DATA] P0. **CeFi** — backfill every `expected_unattempted` (instrument × venue × data_type × date) + re-fetch the
      ~88k genuine `VENUE_FETCH_FAILED`/`HTTP_429`. Run to completion on real infra; manifest-verified rows. —
      market-tick-data-service
- [ ] [DATA] P0. **DeFi** — backfill the post-launch could-exist (dex*pool_swaps/state, rate_indices, utilization,
      risk_params, swaps_ohlcv*\*) for every listed protocol × chain; re-fetch the genuine failed (~41k pre-de-noise).
      (Most of the 75% "empty" is honest pre-launch/not-listed — backfill only the genuine could-exist.) —
      market-tick-data-service
- [ ] [DATA] P1. **TradFi** — backfill expected_unattempted trades/ohlcv/options_chain/tbbo across venues × instruments
      × dates; re-fetch genuine failed (~6k post-de-noise). — market-tick-data-service
- [ ] [DATA] P1. **Sports** — backfill odds/fixtures/stats for every canonised league × fixture × date in coverage. —
      market-tick-data-service
- [ ] [DATA] P1. **Prediction** — backfill prediction data for every canonised market × date post-genesis (2025-03-14+).
      — market-tick-data-service

## Step 2 — instruments-store backfill (IS = 100% of its could-exist; MTDS↔IS subset exactly equal)

- [ ] [DATA] P1. **Backfill IS historical listings for the venues MTDS has but IS lacks** (Kraken ~6yr,
      LIGHTER/PACIFICA/ EXTENDED, BITGET gap days — the F1/F2 remediation items) + any other IS enumeration holes, so IS
      lists every instrument that could exist on every in-coverage day. Re-run the IS daily CLI per date (never copy
      between dates). Verify: the cefi (venue,date) subset closes; IS captured/could-exist ≈ 100%. — instruments-service

## Step 3 — cross-data_type completeness (every expected data_type per listed instrument)

- [ ] [DATA] P2. **For each listed instrument, capture the FULL expected data_type set**, not just `trades`: cefi
      (trades/book*snapshot_5/derivative_ticker/liquidations/ohlcv*\*), defi (pool_swaps/pool_state/rate_indices/
      utilization), tradfi (trades/ohlcv/options_chain/tbbo), per the per-venue `venue_data_types.yaml`. Flag + backfill
      instruments that have one data_type but not the expected set. — market-tick-data-service

## Step 4 — credential-gated venues (the ONLY operator-gated piece)

- [ ] [DATA] P1. `BLOCKED-CREDENTIALS` — file the credential/subscription asks for any venue/source behind a paid tier
      whose could-exist cells can't be backfilled on free/public access (per external-data-always-available rule:
      Helius/Alchemy, Glassnode/Kaiko, Tardis, Databento, Sportradar/The-Odds-API, …). Build the adapter scaffold + unit
      tests now; status `BLOCKED-CREDENTIALS` with a named ping; backfill once the operator provides creds. This is the
      only step an autonomous agent cannot self-close. — market-tick-data-service

## Step 5 — keep it 100% (live=batch parity + continuous verification)

- [ ] [DATA] P1. **Live capture running for every AG** (batch=live: same code path) so new days land captured forward,
      not re-opening the gap. — market-tick-data-service
- [ ] [INFRA] P1. **Continuous verification green**: manifest consolidator healthy + the data-status dashboard reads
      `captured / could-exist ≈ 100%` per AG as the standing proof; alert on regression. — deployment-api / mtds

## Success criteria

- data-status per AG: `attempted_failed = 0`, `expected_unattempted = 0`, captured = 100% of could-exist (honest-empty
  excluded), for cefi / defi / tradfi / sports / prediction.
- MTDS shard set == IS could-exist set (subset closed both ways).
- Live capture keeping each AG at 100% forward; consolidator green; dashboard is the continuous proof.
- Every credential gap has a named operator ask (the only non-autonomous remainder).
