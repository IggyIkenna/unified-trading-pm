---
doc_type: issue
title: DeFi expected_unattempted backlog ≥1M cells — enumerator halt-safety trips on scan; seeding never applied
summary:
  "enumerate_expected_universe --asset-group defi (scan-only) halts with ENUMERATOR_FAILED reason=max_writes_exceeded:
  would-write 1,000,001 > the 1M halt-safety cap. The backlog is PRE-EXISTING (identical count when bounded --end-date
  2026-06-29, i.e. against the pre-incremental catalogue's coverage), meaning ≥1M (shard_key, day) tuples in the defi
  expected universe have NO manifest row at all — the Phase-3.D backward-fill apply-write was evidently never run (or
  never completed) for defi. Until seeded, defi coverage denominators (data-status honest-coverage) silently exclude
  these cells. The enumerator's own halt message gates the fix on operator review of the write volume."
status: open
nature: record
asset_group: [defi]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [manifest, expected-unattempted, enumerator, honest-coverage, defi, backlog]
related: [plans/active/instruments_catalogue_incremental_rollup_2026_06_29.md]
created: 2026-07-03
parent_epic: instruments_master
source: [defi expected_unattempted manifest backlog finding 2026-07-03 — 1.38M rows, operator decision pending]
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: data-pipeline-engineer
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-10
locked_by: live-defi-rollout
locked_since: 2026-07-03
resolved_by:
---

> **🔴 2026-07-10 SUPERSEDING FINDING — the approved 1,380,376-row apply is STALE, DO NOT RUN THE ORIGINAL COMMAND.**
> The v1 (venue-grain) enumerator that produced the reviewed/approved 1,380,376 figure was **retired 2026-07-06**
> (`plans/active/issues/v1_enumerator_dispatch_not_deletable_2026_07_06.md`). v2 (per-instrument grain) is now the ONLY
> enumerator, and it requires `--catalog-path` (missing from the original command below — it will hard-fail with
> `missing_catalog_path` as written). A real re-verification run today (2026-07-10) shows the TRUE current v2 defi
> backlog is **63,876,053 rows — 46× the approved figure — with a materially different composition** (not "99.95% honest
> 2018-2019 docs, 684 actionable rows" any more). See **"2026-07-10 re-verification"** section below before doing
> anything. **No apply-write was executed** — every run in this re-verification was scan-only (zero manifest mutations).

# DeFi expected_unattempted backlog ≥1M — enumerator halt-safety (found 2026-07-03)

## Evidence

Discovered during the incremental-catalogue plan's Phase 4 consumer verification (slot-2, 2026-07-03):

- `enumerate_expected_universe.py --asset-group defi` (scan-only) →
  `ENUMERATOR_FAILED reason=max_writes_exceeded candidates=1000001 cap=1000000` (run_id
  `enum-universe-defi-20260703-152718`); the counter short-circuits at cap+1, so the true backlog is **≥ 1,000,001** and
  unquantified.
- **Pre-existing, NOT caused by the 2026-07-03 incremental catalogue**: re-run with `--end-date 2026-06-29` (restricting
  the expected universe to exactly what the OLD, pre-incremental catalogue covered) trips the identical
  `candidates=1000001` halt.
- Mechanically the enumerator consumed the fresh incremental catalogue fine (manifest 11.77M rows loaded + present-set
  11.23M computed + catalogue cross-join ran) — the halt is the volume guard, not a read failure.

## Why it matters

`expected_unattempted` rows ARE the "remaining to be downloaded" denominator (honest-coverage). ≥1M defi cells with no
manifest row at all means the data-status defi denominators are silently understated — the rollup-vs-drilldown
divergence class the Phase-3.D backward-fill exists to close.

## OPERATOR DECISION REQUIRED (Ikenna) — approve the manifest seeding

The apply-write mutates the availability manifest (~1.38M new rows) and the enumerator gates it on operator review by
design. **What the write actually is**: `record_expected_empty(reason=EXPECTED_*)` honest-absence rows — typed "no data
could ever exist here" documentation. It triggers **zero downloads**; only the 684 recent cells surface as real
outstanding work in data-status afterwards.

**A (RECOMMENDED): approve the FULL apply — all 1,380,376 rows, one run.** The designed Phase-3.D backward-fill;
idempotent per tuple; per-VM-shard isolated (the consolidator merges it); the only option that makes the defi
denominator fully honest AND stops every future scan from tripping the 1M halt. The consolidator already handles a
75M-row cefi canonical — 1.4M metadata rows is well within its envelope.

```bash
cd instruments-service
MANIFEST_PER_VM_SHARDS=true VM_NAME=enum-universe-defi-$(date +%s) \
GCP_PROJECT_ID=central-element-323112 \
python scripts/enumerate_expected_universe.py \
    --asset-group defi --apply-write --max-writes-per-run 1500000
```

Post-apply verification (executor does all three): (1) manifest row-count delta ≈ +1.38M
(`_index/availability_index.parquet` after the next consolidator cycle); (2) a fresh scan-only run reports ~0
candidates; (3) the data-status defi denominator/remaining counts refresh.

**B: seed only 2021→today (684 rows) now, defer the 2018–2019 block.** Smaller manifest, but deep-history denominators
stay dishonest (contradicts the honest-absence model) and every future defi scan keeps halting at the 1M cap. Not
recommended.

**Other**: any custom slice (per-venue / per-year via `--start-date`/`--end-date` chunked runs — idempotent, safe to
split arbitrarily).

## Fix path (operator-gated by design)

The enumerator's halt message is explicit: "Increase `--max-writes-per-run` after operator review." Steps:

- [x] [VERIFY] P1. ✅ Quantify the true backlog: run scan-only with the cap lifted enough to COUNT (still no writes),
      report per-(venue, data*type, year) distribution so the operator can review what's being seeded. — 2026-07-03 run
      `enum-universe-defi-20260703-154354` (scan-only, cap 50M): **1,380,376 candidates**, report CSV
      `/tmp/enum-universe-defi-20260703-154354.csv` (slot-2 host). Distribution: **99.95% is 2018 (695,830) + 2019
      (683,862)** — pre-launch/pre-genesis days for protocols that did not exist yet (AAVE_V3 / PANCAKESWAP_V3 /
      YEARN_V3 / BEEFY etc. all launched years later), i.e. HONEST-ABSENCE documentation rows
      (`record_expected_empty(reason=EXPECTED*\*)`), NOT download work. Only **684 cells across 2021–2025** are
      potentially actionable "remaining to download" rows. Even spread across data_types (~80k each); top venues BEEFY
      96k / BALANCER 86k / PANCAKESWAP_V3 64k. (First attempt hit a transient consolidator read race — 404 on a replaced
      `\_index` generation — retry succeeded; not a defect.)
- [ ] [INFRA] P1. **BLOCKED-OPERATOR-DECISION (RE-OPENED 2026-07-10)** — the 2026-07-03 operator approval was for the v1
      (venue-grain) 1,380,376-row figure; v1 is retired and that command no longer runs. The real v2 (per-instrument
      grain) backlog is **63,876,053 rows** with a different composition (82% honest-absence `empty_confirmed`, but
      **18% / 11,459,259 rows are `expected_unattempted`** — the genuine "remaining to download" denominator — spread
      evenly across 2018-2026, not concentrated in 684 recent cells as previously characterized). Needs a **fresh**
      operator decision at the real scale before any `--apply-write`. See "2026-07-10 re-verification" section for the
      full breakdown + the corrected command (adds the now-mandatory `--catalog-path`). NOT executed — zero manifest
      writes performed by this investigation.
- [x] ✅ [VERIFY] P2. Check the other AGs for the same never-applied backlog (tradfi/cefi/prediction scan-only counts).
      — 2026-07-10 real scan-only runs (all zero-write): **tradfi** catalog 1,098,236 instruments, backlog >5,000,001
      (halted at the 5M safety cap, true count unquantified — same v1→v2 explosion pattern as defi). **cefi** catalog
      361,870 instruments, backlog >5,000,001 (same pattern, halted at 5M cap). **prediction** catalog 2,486,092
      instruments — **scan CRASHES**, does not even reach a candidate count:
      `TypeError: Cannot compare tz-naive and tz-aware timestamps` in `_enumerate_v2_prediction`
      (`instruments-service/scripts/enumerate_expected_universe.py` ~line 1852) — `pd.Timestamp(created_str)` /
      `pd.Timestamp(settled_str)` parse tz-AWARE for catalogue rows whose `market_created_at`/`settlement_time` carry a
      timezone suffix, then get compared against the tz-NAIVE `window_start_ts`/`window_end_ts` built from
      `pd.Timestamp(date_axis[i])` (plain `date` objects, no tz). Data-dependent — only triggers for catalogue rows with
      tz-suffixed timestamp strings, so smaller/older runs likely never hit it. This is a **separate, new, concrete
      bug** (distinct from the already-open `is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md` P0,
      which is the `build_instrument_catalogue.py` Cloud Run catalog-builder job, a different script) — prediction's v2
      EXPECTED-UNIVERSE enumerator cannot currently complete even a scan-only run against the full catalog. Not fixed
      here (out of this task's scope); needs its own fix-worker dispatch. This P2 scan-only investigation is
      complementary to (and updates) `plans/active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md`, whose
      cefi/tradfi/prediction quantum estimates (~1.75M cefi Kraken-6yr, ~818k prediction cqg EU, etc.) were grep-based
      static estimates against the OLD landscape and are now understated by 1-2+ orders of magnitude post the 2026-07-06
      v1→v2 retirement — that doc's per-AG owning-plan todos remain the right home for the fix work, this note is the
      cross-reference. No writes performed (scan-only throughout).

## 2026-07-10 re-verification — real v2 scale is 46× the approved figure, needs FRESH operator review

Dispatched to execute the operator-approved apply verbatim. The literal command from the **OPERATOR DECISION REQUIRED**
section above no longer runs: v2 (per-instrument grain) is now the _only_ `--enumerator-version` (v1 was retired
2026-07-06, `plans/active/issues/v1_enumerator_dispatch_not_deletable_2026_07_06.md`) and v2 hard-requires
`--catalog-path` (`ENUMERATOR_FAILED reason=missing_catalog_path` otherwise). Before running an apply-write of an
unknown size under a stale approval, re-quantified the true backlog:

1. **Scan-only with `--catalog-path gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet`,
   `--max-writes-per-run 3000000`** → halted at `candidates=3000001` (already 2.2× the approved 1,380,376, still
   unquantified beyond the cap).
2. **Raised to `--max-writes-per-run 20000000`** → halted at `candidates=20000001` (14.5× the approved figure, still
   unquantified).
3. **True count**: wrote a read-only diagnostic (`enumerate_expected_universe.py`'s own `enumerate_v2()` +
   catalog/manifest-loading functions, imported verbatim — zero behavior change, zero writes) that tallies the
   generator's output with running `Counter`s instead of materializing 60M+ dataclass instances or a giant CSV. Full run
   (204s, zero writes):

   ```
   FINAL_TOTAL = 63,876,053   (vs. approved 1,380,376 — 46.3×)

   by capture_status: empty_confirmed 52,416,794 (82.1%) | expected_unattempted 11,459,259 (17.9%)
   by reason: EXPECTED_INSTRUMENT_NOT_LISTED 33,325,560 | EXPECTED_PRE_GENESIS_CHAIN 18,764,581 |
              (expected_unattempted, no reason) 11,459,259 | EXPECTED_INSTRUMENT_DELISTED 326,653
   by year: 2018 8.74M | 2019 8.72M | 2020 8.71M | 2021 8.55M | 2022 8.34M | 2023 7.00M | 2024 6.19M | 2025 6.51M |
            2026 1.12M   — roughly EVEN across 2018-2026, NOT concentrated in 2018-2019
   by data_type (top): dex_pool_swaps 18.5M | dex_pool_state 17.2M | position_data 9.9M | lending_indices 3.75M |
            liquidations 3.52M | risk_params 3.52M | liquidation_events 3.38M
   by venue (top): UNISWAP_V3 17.2M | BALANCER 13.5M | MORPHO 13.5M | PANCAKESWAP_V3 3.50M | AAVE_V3 3.37M |
            UNISWAP_V4 2.52M
   by instrument_type: pool 42.2M | lending 16.7M | (blank) 4.27M | perpetual 321K | lst 223K | spot_pair 143K
   ```

**Why this changes the decision, not just the number**: the 2026-07-03 approval's rationale was explicitly "99.95% is
2018-2019 pre-launch documentation… only 684 cells across 2021-2025 are potentially actionable remaining-to-download
rows." That was true for the v1 (55-protocol, venue-grain) enumeration. The v2 (7,895-instrument, per-pool grain)
enumeration is a fundamentally different — and correct, by design — finer unit (the retirement doc + the
`instruments_service_cefi_qg_red_on_ldr_head_2026_07_08` line of work established v2 subsumes every v1 row class), but
it means: (a) the write volume is 46× bigger, (b) **11.46M rows are `expected_unattempted`** — the live "still need to
capture" denominator, not zero-download documentation — spread across every year 2018-2026, not a small recent tail.
Applying this would instantly and massively move the defi honest-coverage denominator system-wide (dashboards,
compliance reporting, Foundation-gate sign-offs) in a way qualitatively different from what was reviewed. This is a "big
finding" (data-correctness, denominator-defining, system-wide-visible) per the workspace findings-triage rule — flagging
for a fresh operator decision rather than auto-applying under the stale approval.

**Minor secondary finding (small volume, separate fix)**: 3 LST instruments (`ETHERFI-ETHEREUM:LST:WEETH`,
`LIDO-ETHEREUM:LST:STETH`, `LIDO-ETHEREUM:LST:WSTETH`) hit `G1-ENUM: unmapped instrument_type='LST'` and fall back to
ALL data_types (documented legacy behavior, not a crash) — adds a matrix entry to
`unified_api_contracts.registry.market_data_categories` to suppress; contributes at most tens of thousands of rows, not
a material driver of the 63.9M total (the grain change is).

**Corrected command** (once a fresh operator decision picks a number/slice — NOT run by this investigation):

```bash
cd instruments-service
MANIFEST_PER_VM_SHARDS=true VM_NAME=enum-universe-defi-$(date +%s) \
GCP_PROJECT_ID=central-element-323112 \
python scripts/enumerate_expected_universe.py \
    --asset-group defi \
    --catalog-path gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet \
    --apply-write --max-writes-per-run <cap ≥ true count, per fresh operator decision>
```

**OPERATOR DECISION REQUIRED (Ikenna) — fresh review, real v2 scale**: A (apply the full 63,876,053 in one run — same
"honest by default" principle as the original decision, now at the real scale); B (apply only the 52.4M
`empty_confirmed` honest-absence rows first — zero denominator/coverage-% impact, defer the 11.46M
`expected_unattempted` rows, which DO move the coverage-% number, to a separate reviewed slice); C (chunk by year/venue
via `--start-date`/`--end-date`, idempotent, safe to split); Other. Not proceeding without this.

Diagnostic script (read-only, zero writes, reuses the production enumerator functions verbatim) was run from the
scratchpad and is not part of any repo — available on request if the count needs independent reproduction; the commands
above are otherwise fully reproducible via the shipped CLI.

## Progress log

- 2026-07-03: Issue filed from the incremental-catalogue plan's Phase 4 verification; pre-existence proven via the
  `--end-date 2026-06-29` bounded re-run. Operator notified in-session.
- 2026-07-10: Dispatched to execute the approved 1,380,376-row apply. Found the command stale (v1 retired 2026-07-06, v2
  now requires `--catalog-path`); re-quantified the real v2 backlog at 63,876,053 (46× approved figure) with a
  materially different composition (11.46M genuine `expected_unattempted` spread across all years, not 684 recent
  cells). **No apply-write executed** — all runs scan-only. Also completed the P2 cross-AG scan-only check: tradfi and
  cefi show the identical v1→v2 explosion pattern (both >5,000,001 uncapped); prediction's v2 enumerator crashes
  outright on a tz-naive/tz-aware comparison bug (new finding, not previously filed). P1 apply re-flagged
  BLOCKED-OPERATOR-DECISION pending a fresh review at the real scale.
