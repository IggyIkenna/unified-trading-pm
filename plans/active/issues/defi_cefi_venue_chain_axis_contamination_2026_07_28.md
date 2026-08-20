---
doc_type: issue
title: >-
  DeFi venues axis carries 14 non-DeFi tokens (9 chain names + 5 CeFi exchange names); defi+cefi chains axis carries a
  shared `FUTURES` contamination — net-new since the 2026-07-25 census refresh, not yet root-caused
summary: >-
  distinct_values_noncanonical_audit_2026_07-20.md's 2026-07-28 census refresh (dispatched via
  cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md's line-191 todo) found defi.venues carrying 16 non-canonical
  values, 14 of which are NOT DeFi-protocol-shaped: 9 are literal chain names (ARBITRUM, AURORA, AVALANCHE, BASE, BSC,
  ETHEREUM, LINEA, OPTIMISM, POLYGON) and 5 are CeFi exchange names (BITFINEX, BITGET, BYBIT, KRAKEN, OKX) — tokens that
  belong on a different axis (chain) or a different asset_group (cefi) entirely, not on the defi venue axis. Separately,
  `defi.chains` and `cefi.chains` both carry a non-canonical `FUTURES` value — cefi has NO chain axis at all per this
  same plan's own RESULT 3 finding (`UAC SHARD_AXIS_MATRIX[(MTDS,cefi)]` has no `chain` axis), and `FUTURES` is a tradfi
  instrument_type spelling, not a chain — suggesting a shared, not-yet-identified cross-axis or cross-asset-group write
  path. This doc catalogues the finding + the two most plausible root-cause classes (wrong-axis writer mis-stamp vs.
  cross-AG manifest-consolidator bleed, the latter matching the shape of the ALREADY-RESOLVED
  `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` TOCTOU bug,
  `unified-trading-library@14301571`, shipped 2026-07-24) — this is a genuine cross-repo, cross-asset-group
  data-correctness finding per this workspace's findings-triage rule ("big finding" — NOTIFY OPERATOR + issue doc).
  **CORRECTED 2026-08-16 (plan_reconciler, tranche=tradfi, agt-a74a6a)**: the original framing above ("without
  executing a fix... not investigated to root cause here, read-only audit scope, time-bounded") is now stale — both
  root causes WERE identified and fixed (writer-defaults-venue-to-chain fixed via `instruments-service@f651ff8b`
  2026-07-30; the cross-AG splitter bug in `migration_orphan_sweep.py` also fixed 2026-07-30) over the 3 weeks since
  this doc was opened; see the Todos/Progress Log below for the full remediation history. Only 2 items remain open,
  both gated on live verification, not a fresh root-cause investigation. **CORRECTED 2026-08-18 (plan_reconciler
  cross-cutting)**: this is now stale too — a P3 POOL-casing regression item was REOPENED 2026-08-16 (a fresh
  0→7.9M-row regrowth whose recurrence mechanism the doc's own text calls UNRESOLVED, not a verification gate). True
  open count is 3 (grep-verified), not 2, and the 3rd is a genuine unresolved root-cause item.
status: open
nature: issue
asset_group: [defi, cefi, tradfi, cross-cutting]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, unified-trading-library, deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    defi,
    cefi,
    cross-asset-group,
    wrong-axis,
    contamination,
    venues,
    chains,
    honest-coverage,
    distinct-values,
    manifest,
    data-correctness,
  ]
related:
  [
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md,
    /plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md,
  ]
created: "2026-07-28"
author: unknown
last_updated: "2026-08-20"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
source: >-
  distinct_values_noncanonical_audit_2026_07_20.md line-191 todo (owning-plan reconciliation of every current
  non-canonical value), dispatched via cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /plans/archive/issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md,
    /plans/archive/2026_08/issues/defi_hyperliquid_residual_manifest_rows_2026_08_04.md,
    features-service/scripts/run_cefi_perp_funding_corpus.py,
    strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py,
    instruments-service/scripts/migration_orphan_sweep.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# DeFi/CeFi venue+chain axis cross-contamination (2026-07-28)

## What I found

Live `GET /distinct-values/{asset_group}` (in-process, `source_date=2026-07-28`) for defi + cefi:

**`defi.venues` (16 non-canonical, up from the 2026-07-25 refresh's already-flagged-but-unclassified set):**

- **2 already-known/tracked**: `BLAZESTAKE`, `HYPERLIQUID` — `phase=="pipeline"` grain exceptions, covered by
  `defi_venue_phase_live_definition_contradiction_2026_07_22.md`.
- **9 NEW — literal chain names, not DeFi protocol venues**: `ARBITRUM`, `AURORA`, `AVALANCHE`, `BASE`, `BSC`,
  `ETHEREUM`, `LINEA`, `OPTIMISM`, `POLYGON`. Every one of these is a real, canonical `MAINNET_CHAIN_IDS` member — they
  belong on the `chain` axis, not `venue`.
- **5 NEW — CeFi exchange names, not DeFi protocol venues**: `BITFINEX`, `BITGET`, `BYBIT`, `KRAKEN`, `OKX`. Every one
  of these is (or resolves to, via `CEFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES` fold) a real cefi venue — they belong in
  the `cefi` asset_group's manifest, not defi's.

**`defi.chains` (2 non-canonical)**: `HYPERLIQUID` (already tracked, cross-refs the venues finding above), `FUTURES`
(NEW — not a chain name at all).

**`cefi.chains` (1 non-canonical)**: `FUTURES`. Per this same plan's RESULT 3 (2026-07-20), `chain` is a MEANINGLESS
axis for cefi (`UAC SHARD_AXIS_MATRIX[("market-tick-data-service","cefi")]` has no `chain` axis) — the
`onchain_perp_batch_handler.py` venue-as-chain bug that caused the ORIGINAL cefi chain contamination was already fixed
(`mtds@accd8aa4`) and re-stamped. `FUTURES` appearing now is either a NEW writer path (not the one RESULT 3 fixed)
independently stamping `chain`, or un-restamped historical residue from a different source.

## Why it matters

Two candidate root-cause classes, neither confirmed:

1. **Wrong-axis writer mis-stamp (cat-3)** — a defi/cefi writer is putting the wrong token in the wrong manifest column
   (e.g. defaulting `venue` to the `chain` value when the real venue is unresolved, or a bundle-grain `instrument_type`
   value like `futures_chain`/`FUTURES` leaking into the `chain` column for cefi/defi rows).
2. **Cross-asset-group manifest bleed (cat-3, cross-AG)** — the CeFi exchange names in `defi.venues` in particular look
   like a cross-AG bleed (cefi rows landing in the defi manifest), the SAME SYMPTOM SHAPE as the already-resolved
   `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` finding (a fleet-wide TOCTOU race in
   `manifest_consolidator.py`'s CAS write path, fixed `unified-trading-library@14301571`, shipped 2026-07-24, "holds"
   per that doc's own ROUND 8 section). Whether this is a NEW instance of the same bug class, un-cleaned residue from
   before the fix, or an unrelated mechanism is NOT determined here.

This is flagged as a **big finding** per this workspace's findings-triage rule (cross-repo, cross-asset-group, plausible
SSOT-adjacent data-correctness issue) — filed for operator visibility + the next investigation, not chased to root cause
in this read-only audit pass (time-bounded scope).

## Recommended decision

- [x] ✅ [DIAG] P1. **ROOT-CAUSED 2026-07-30.** Traced via a bounded, targeted duckdb read of the live
      `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (single bounded object,
      29,093,653 rows, column-projected query — not a corpus walk). The 9 chain-shaped `defi.venues` values
      (ARBITRUM/AURORA/AVALANCHE/BASE/BSC/ETHEREUM/LINEA/OPTIMISM/POLYGON) are **NOT cross-AG bleed** — every one has
      `data_type=gas_fees`, `instrument_type=spot_asset`, `source=onchain_rpc`, `pipeline_mode=batch_onchain_rpc`,
      `venue==chain` (identical value in both columns), real captured rows spanning 2020-01-01→2026-07-21 (739–1,857
      rows per chain). `gas_fees` is a genuine CHAIN-level metric with no protocol/venue concept — the writer had no
      real venue to stamp and reused the chain name, the same "axis mismatch, not garbage" shape as the already-accepted
      `futures_chain`/`options_chain` bundle-grain exceptions. This is a
      **writer-defaults-venue-to-chain-when-unresolved** case (candidate class 1), NOT cross-AG bleed, for this half of
      the finding. **(Independently corroborated 2026-07-30 by a concurrent slot-15 manifest-column trace — see the
      Progress Log entry below — same 11,662-row population, same `venue==chain`/`onchain_rpc`/`batch_onchain_rpc`
      signature, confirmed via a different query path.)**
- [x] ✅ [DIAG] P1. **ROOT-CAUSED 2026-07-30 — COMPLETED with the exact splitter location (see slot-15 Progress Log
      below).** The `chain="FUTURES"` values (+ the 5 cefi-exchange-shaped `defi.venues` values
      BITFINEX/BITGET/BYBIT/KRAKEN/OKX, plus BINANCE which the census undercounted) are confirmed **genuine cross-AG
      bleed** (candidate class 2) — and it is a PHYSICAL GCS bucket misfile, not just a manifest-index cosmetic issue.
      Live evidence: all matching rows share one narrow signature — `data_type=perp_daily_ctx`,
      `instrument_type=perpetual`, `source=tardis`, `pipeline_mode=batch_tardis`, exactly 7 rows/venue, dated
      **2026-05-16 → 2026-05-22 only** (a single week; zero rows before or after — this predates and appears already
      stopped by the 2026-07-24 TOCTOU consolidator fix, `unified-trading-library@14301571`, not a new regression).
      Bounded `gsutil ls` prefix probes (single-date, single-venue — not a corpus walk) confirm the GCS PATH itself
      carries the contamination:
      `gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2026-05-16/pipeline_mode=batch_tardis/asset_group=cefi/`
      physically contains
      `venue={BINANCE-FUTURES,BITFINEX-FUTURES,BITGET-FUTURES,BYBIT-FUTURES,DERIBIT,KRAKEN-FUTURES,OKX-FUTURES}/` — real
      CeFi Tardis dated-futures captures, correctly `asset_group=cefi`-tagged in the path, but physically stored in the
      **DeFi** bucket. Comparison-checked: the identical `(day, pipeline_mode, asset_group, venue, instrument_type)`
      prefix ALSO exists correctly in `market-data-tick-cefi-prd-...` — this looks like a **duplicate write to both
      buckets**, not data stranded only in the wrong place, so a cleanup of the DeFi-bucket copies is unlikely to lose
      data (not independently verified row-for-row). The literal `chain="FUTURES"` manifest value is the `-FUTURES`
      suffix of the glued `{EXCHANGE}-FUTURES` venue strings (e.g. `BITFINEX-FUTURES`) being run through a DeFi-style
      `PROTOCOL-CHAIN` venue/chain splitter that doesn't validate the suffix against `KNOWN_CHAINS` before splitting —
      the SAME bug _class_ as the already-fixed EXTENDED-STARKNET/LIGHTER-ZKSYNC "-CHAIN-suffix" split
      (`instruments_cefi_g1_g5_gate_execution_2026_07_24.md`), hitting the "-FUTURES" venue family this time instead of
      an on-chain-perp-CLOB chain suffix. **Splitter location FOUND (slot-15, concurrent session, see Progress Log
      below) — it is NOT MTDS-side as this entry originally guessed; it's
      `instruments-service/scripts/ migration_orphan_sweep.py:253`'s `shard_key_from_segments()`, missing the
      `_KNOWN_DEFI_CHAINS` allowlist guard its sibling `market-tick-data-service/scripts/rebuild_defi_manifest.py`
      already has.** Timestamp reconciliation: this entry's `day=2026-05-16..22` is the ORIGINAL CAPTURE date (from the
      GCS path partition); the concurrent trace's `written_at=2026-07-24T20:06:38` is the LATER MANIFEST-REGISTRATION
      timestamp (from `backfill_orphan_class_e.py` sweeping + registering these already-misplaced objects into the
      manifest, corrupting venue/chain in the process) — the two are consistent, not contradictory: same underlying 35
      objects, two different lifecycle timestamps. Not independently re-verified that these are literally the SAME 35
      rows (both traces used different query methods) — flagged for whoever executes the fix to spot-check before
      relying on it.
- [x] ✅ [DATA] P2 (a). **DONE 2026-07-30 — `instruments-service@f651ff8b`.** Fixed
      `instruments-service/scripts/migration_orphan_sweep.py::shard_key_from_segments()` — added an allowlist guard
      before the unconditional `venue, _sep, chain = venue.partition("-")` split. Used UAC's own
      `unified_api_contracts.registry.chain_env.MAINNET_CHAIN_IDS` as the allowlist (already imported elsewhere in this
      same repo, e.g. `scripts/enumerate_expected_universe.py`) rather than duplicating a second local
      `_KNOWN_DEFI_CHAINS` frozenset copy of MTDS's — same guard semantics the doc asked to mirror, one fewer
      hand-maintained vocabulary. Regression test added
      (`test_defi_venue_chain_split_guarded_against_unknown_chain_suffix`) pinning the exact `BITGET-FUTURES` →
      `venue="BITGET-FUTURES", chain=""` (unsplit) behavior; existing `test_defi_combined_venue_chain_split`
      (`EIGENLAYER-ETHEREUM` → split) still passes unchanged. Full `quality-gates.sh` green.
- [x] ✅ [DATA] P1. **RE-SCOPED 2026-08-04 (interactive session) — the prior "safe cleanup" framing was WRONG; Part 4 of
      the delete-safety five-part-proof FAILS with direct evidence, not merely unverified. Remaining repoint question
      ANSWERED 2026-08-04 (see the tail of this entry) — no code change, disposition confirmed unchanged.** Live-code
      check (`strategy-service`): `strategy_service/cli/handlers/paper_run_handler.py:1987-1988` — the CARRY_BASIS_PERP
      / CARRY_FUNDING_DISPERSION tick-building path (`GroupBRunner`) instantiates
      `CanonicalPerpFundingProvider().funding_window(window_start, window_end, venue=venue)`, which per
      `strategy_service/engine/core/canonical_perp_funding_provider.py:142-150` reads `data_type=perp_daily_ctx` **ONLY
      from the shared DeFi bucket** (`resolve_bucket_name(kind="tick-data", asset_group="defi")`, no cefi-bucket
      fallback), via an unscoped glob that "picks up whatever `pipeline_mode=`/`venue=` shards the pipeline wrote,
      without hardcoding the source/venue partitions" — i.e. it reads ANY venue physically present at that path, not an
      allowlist. `strategy_service/engine/strategies/v2/target_universe/catalog_carry.py:217-234` configures **exactly 6
      of the 7 contaminated venues** (`KRAKEN-FUTURES`, `BINANCE-FUTURES`, `BYBIT-FUTURES`, `OKX-FUTURES`,
      `BITFINEX-FUTURES`, `BITGET-FUTURES`) as the real CARRY_BASIS_PERP venue universe. This module's own docstring
      states determinism is "a pure function of (bucket corpus, window, venue, coin)" — i.e.
      `paper(W) == batch-rerun(W)` epsilon=0 depends on this exact physical data being present. **Deleting these objects
      would not be a redundant-duplicate cleanup — it would silently remove data a live, determinism-critical strategy
      path reads today, with no fallback to the cefi-bucket copy.** This is confirmed by direct code read (not
      inferred), and it DIRECTLY CONTRADICTS this doc's own prior claim ("a cleanup of the DeFi-bucket copies is
      unlikely to lose data") — that claim was never verified against the actual reader, only against GCS path/prefix
      existence. **Disposition per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`:
      `no-still-authoritative`** (the DeFi-bucket copy is, today, the ONLY thing `CanonicalPerpFundingProvider` reads
      for these venues — not a delete candidate at all until proven otherwise). **Do NOT delete.** Remaining open
      question for whoever picks this up: whether `CanonicalDerivativeTickerFundingProvider` (a separate provider class,
      used elsewhere in `paper_run_handler.py` at line 2364, reading a `derivative_ticker`-shaped cefi-native corpus)
      could be repointed-to instead for these 6 venues — if so, THAT is the correct fix (repoint reader → confirm parity
      → then delete, mirroring the Part-5 "legacy-copied-not-moved" recipe), not a blind delete. Not resolved here;
      flagging as the concrete next step rather than re-opening the original mis-scoped `[OPERATOR]` framing. Checklist:
      Part 1 twin `NOT RE-EVALUATED this session` (prior finding stands: exists in cefi bucket) · Part 2 content
      `NOT RE-EVALUATED this session` · Part 3 writers: no live writer targets this exact path today (TOCTOU bug fixed
      2026-07-24, `instruments-service@f651ff8b`) · **Part 4 readers: FAILS — `paper_run_handler.py:1987-1988` +
      `canonical_perp_funding_provider.py` confirmed live reader, see above** · Part 5 N/A (not a legacy-copy scenario).
      Disposition: `no-still-authoritative`. Hard stop: none crossed (disposition itself blocks action, not an
      operator-approval gate). **REPOINT QUESTION ANSWERED 2026-08-04 (interactive session) — NO, not viable today.**
      Investigated whether `CanonicalDerivativeTickerFundingProvider` (reads `derivative_ticker` from the CeFi bucket)
      could replace `CanonicalPerpFundingProvider` (reads `perp_funding`/`perp_daily_ctx` from the DeFi bucket) for the
      6 `catalog_carry.py` venues, which would make the DeFi-bucket copies deletable per the Part-5 repoint-then-delete
      recipe. Two independent blockers, both confirmed by direct evidence: 1. **Venue coverage gap**:
      `CanonicalDerivativeTickerFundingProvider._VENUE_SYMBOL_TEMPLATE` only maps `DERIBIT`/`BYBIT` — 2 of the 6
      contested venues (`KRAKEN-FUTURES`/`BINANCE-FUTURES`/`OKX-FUTURES`/ `BITFINEX-FUTURES`/`BITGET-FUTURES` have no
      wire-symbol template; the module's own docstring says adding one "requires re-verifying its real GCS filename
      shape"). 2. **The underlying data source is itself gapped since 2026-05-22, not just this doc's original discovery
      window.** Bounded `gsutil ls` prefix probes (single-date, single-venue — not a corpus walk) against the LIVE CeFi
      bucket confirm: on 2026-05-20, all 6 contested venues (+ DERIBIT/BYBIT) have real `derivative_ticker` objects
      under `batch_tardis`; probing 2026-05-25, 2026-06-15, 2026-07-01, 2026-07-15, 2026-08-01, 2026-08-03 finds
      **zero** `derivative_ticker` objects for ANY of the 8 venues on ANY of those dates. This exact cutoff is
      independently corroborated by
      `/plans/archive/2026_08/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`'s own 2026-07-28 manifest
      census (line ~273: `BINANCE-FUTURES`/`OKX-SWAP`/`KRAKEN-FUTURES`/`BITGET-FUTURES` captured through `2026-05-22`,
      `BYBIT`/`DERIBIT` through `2026-05-01`) — same population, same cutoff, two independent methods (live GCS probe
      here vs. manifest census there). **Repointing to `CanonicalDerivativeTickerFundingProvider` would not fix anything
      — its source is exactly as stale as `CanonicalPerpFundingProvider`'s, because the DeFi-bucket copy is COMPUTED
      FROM this same CeFi `derivative_ticker` corpus** (`perp_funding_corpus.py:254-255`'s own read side). Verified: the
      DeFi-bucket `perp_funding`/`perp_daily_ctx` population for these venues also stops dead on **2026-05-22** (checked
      2026-05-20 present, 2026-05-22 present, 2026-05-23 onward absent through 2026-08-03) — confirming the computed
      feed dried up the same day its raw input did, not independently. **Disposition unchanged**:
      `no-still-authoritative` stands — still do NOT delete the DeFi-bucket copies (no fresher alternative exists to
      repoint to). **New, more urgent implication surfaced**: the live CARRY_BASIS_PERP/CARRY_FUNDING_DISPERSION
      strategy path has been reading a completely frozen (zero new rows since 2026-05-22, over 2 months as of
      2026-08-04) funding corpus for all 6 configured venues — this is a genuine live-data-staleness finding, not just a
      delete-safety question, and is filed as a new todo in the doc that already owns this exact venue population +
      census (`/plans/archive/2026_08/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`) rather than
      duplicated here. (The ADDITIVE-FALLBACK investigation from 2026-08-04 — evaluating whether
      `CanonicalPerpFundingProvider` could gain a CeFi-native additive fallback — was moved verbatim to the history doc,
      `/plans/archive/2026_08/defi_cefi_venue_chain_axis_contamination_history_2026_07_28.md`.)

- [x] ✅ [DATA] P1. **DONE 2026-08-10 (slot-8). Pipeline verified; promotion + cron already shipped
      (features-service@b2d14c9d + deployment-service@8eff211); partial historical compute (15/82 days, 100
      perp_funding + 100 perp_daily_ctx objects); remaining days gated on forward-poll cron fix.** Once
      `/plans/archive/issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`'s backfill (VM
      `cefi-fwd-20260804-021235`, `derivative_ticker` for the 8 CEX-Tardis venues, 2026-05-01/22→2026-08-02) completes
      and is manifest-verified: re-run
      `features-service/scripts/run_cefi_perp_funding_corpus.py --start 2026-05-16 --end <today>` (or promote it to a
      scheduled features-service CLI subcommand per its own `# Delete-when:` marker, mirroring the cron pattern already
      shipped for `launch-cefi-onchain-forward-poll.sh`/`launch-cefi-forward-poll.sh` in the two sibling outage docs)
      for the 6 `catalog_carry.py` CARRY_BASIS_PERP venues
      (`KRAKEN-FUTURES`/`BINANCE-FUTURES`/`BYBIT-FUTURES`/`OKX-FUTURES`/`BITFINEX-FUTURES`/`BITGET-FUTURES`), then
      verify `CanonicalPerpFundingProvider.funding_window()` returns non-empty observations for a recent day per venue
      (bounded live check, not a corpus walk). **Depends on**
      `/plans/archive/issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md` (raw input must land first — no
      point recomputing over a still-honest-absent raw window). **Only after** the corpus is verified staying current
      should the reader-side additive-fallback idea (evaluated above, not built) be revisited — if the corpus stays
      fresh via this fix, the fallback may not be needed at all; if scheduling drifts again, this todo's own 2026-08-04
      entry above is the scoping starting point (`CanonicalDerivativeTickerFundingProvider` template extension, ~65
      (venue,coin) pairs to verify, or a UAC-level shared symbol-parsing helper). **Repo: features-service** (script
      re-run/promotion) **+ strategy-service** (verification only, no code change).
- [x] ✅ [DATA] P2. **DONE 2026-08-06 (slot-15) — `deployment-service@8eff211`; scheduling/cron half shipped.** The
      features-service CLI subcommand half SHIPPED (`features-service@b2d14c9d`, see Progress Log 2026-08-06); the
      remaining half is wiring a daily cron that fires it
      (`--feature-family cefi --operation compute --mode batch --asset-group CEFI --start-date <today> --end-date <today>`)
      so the corpus stays current automatically the moment raw input lands. Mirror the sibling SCHEDULED_RECURRING
      cron-host pattern (`deployment-service/scripts/vm/launch-cefi-fwd-daily-cron-vm.sh` /
      `launch-cefi-onchain-fwd-daily-cron-vm.sh` + `vm_prefix_registry.py` entries), cadence staggered clear of the
      06/08/09:00Z hosts. **Repo: deployment-service** (launcher + registry) **+ features-service** (already shipped —
      the subcommand exists). Deliberately NOT built 2026-08-06: slot-14 is actively working deployment-service on the
      raw-capture fix (`cefi_tardis_derivative_ticker_historical_gap-002`), and cron-host VM launch is operator-gated.
      **Gate**: can ship any time post the raw-capture fix landing (the cron is only meaningful once raw flows; until
      then it honest-skips).
- [x] ✅ [DATA] P1. **RESOLVED 2026-08-10 (slot-2) — step-2 verified-resolved (the independently-actionable piece);
      steps 1/3/4 remain gated (step 3 → follow-up todo below; step 1 + step 4 → tracked in their own docs).** (a)
      Reader claim CONFIRMED by direct code read: `canonical_perp_funding_provider.py` reads raw GCS objects only
      (`list_blobs` on `raw_tick_data/by_date/day=…/` + `download_bytes` + `pd.read_parquet`), never `_index/` or the
      availability manifest — a manifest-row fix has zero live-reader risk, exactly as this doc asserted. (b) The 35
      corrupted MANIFEST rows (`venue=BITGET`/etc, `chain=FUTURES`) are **already absent** from the live defi index —
      fresh direct read (2026-08-10T18:08Z, 135,368,465 rows): **0** `chain=FUTURES`, **0** `source LIKE '%tardis%'` /
      `pipeline_mode=batch_tardis`, **0** `venue LIKE '%-FUTURES%'`, every row `asset_group=defi`; the cefi index
      (26,182,681 rows) also **0** non-blank `chain` (the UTL@7684a102 heal + relabel held); the in-flight
      `canonical-migration-defi-rebuild-20260810-204358` per_vm shard is clean too → the clean state is durable, not a
      transient merge artifact. Nothing to re-key or drop → **no code change needed for step 2**. The physical mis-filed
      CeFi-Tardis objects (~35 across 2026-05-16..22, correctly named `venue={…}-FUTURES` unsplit, correct cefi-bucket
      twins verified) remain — that is step 3, gated on corpus-freshness + a fresh 5-part delete-safety proof. Original
      ruling (kept for record): **NEW 2026-08-04 (operator ruling, interactive session — source:
      /plans/archive/2026_08/defi_cefi_venue_chain_axis_contamination_history_2026_07_28.md) — supersedes the
      "no-still-authoritative, permanent" framing on the P2(b) checkbox above.** Operator directive: a live-reader
      dependency is not a reason to leave non-canonical/mis-keyed data permanently in place — "live can be reformatted
      too… batch/live symmetry means these bad names shouldn't exist." Concrete, correctly-SEQUENCED path (do not skip
      ahead — each step is gated on the one before it actually landing, not just being started): 1. **Gated on the P1
      todo directly above landing** (corpus re-run/schedule confirmed fresh — i.e.
      `CanonicalPerpFundingProvider.funding_window()` returns non-empty CURRENT observations for all 6
      `catalog_carry.py` venues, not just historically-backfilled ones). Only once the live-critical corpus is genuinely
      current does deleting the stale DeFi-bucket duplicate become safe — deleting first would still break the live
      CARRY_BASIS_PERP/CARRY_FUNDING_DISPERSION path (the P2(b) investigation's finding stands: no fresher alternative
      exists to repoint to today). 2. **The 35 corrupted MANIFEST rows** (`venue=BITGET`/etc, `chain=FUTURES` — the
      `migration_orphan_sweep.py` splitter-bug artifact, splitter itself already fixed `instruments-service@f651ff8b`
      2026-07-25) are a SEPARATE, lower-risk question from the physical GCS duplicate: per this doc's own root-cause
      trace, the live reader (`canonical_perp_funding_provider.py`) globs raw GCS objects directly, not the manifest,
      and the underlying GCS objects are correctly named (`venue=BITGET-FUTURES`, unsplit) — only the MANIFEST
      registration is corrupted. **Before assuming this manifest-only fix is safe, verify that claim directly**
      (grep+read `canonical_perp_funding_provider.py`'s actual glob/read path — confirm it truly never consults the
      manifest for this data_type) — do not proceed on the doc's characterization alone. If confirmed, this manifest-row
      fix (re-key to the correct `venue=BITGET-FUTURES`/`chain=""` twin, or drop if a correct twin already exists) can
      happen independently of step 1, with NO live-reader risk. 3. **Physical GCS duplicate cleanup** (the real CeFi
      Tardis objects sitting in the wrong, DeFi, bucket) — once step 1 confirms the live path no longer needs this exact
      stale copy, re-run the standard 5-part delete-safety proof fresh (do not reuse the old one — Part 4 "no live
      reader" was FALSE at the time it was written; it must genuinely re-verify clean this time) before any delete. 4.
      **HYPERLIQUID residual `asset_group=defi` manifest rows** — root cause still open
      (`defi_hyperliquid_residual_manifest_rows_2026_08_04.md`) — must be root-caused before it can be purged; do not
      blind-delete an unexplained residual. **Sequencing note**: do NOT run any new manifest-CAS-rewrite or GCS-delete
      script against `market-data-tick-defi-prd-central-element-323112` concurrently with the in-flight
      `purge_gas_fees_legacy_venue_prefixes_2026_08_04.py --apply` run (same bucket, same manifest index, same
      consolidator cron paused for that run's duration) — sequence AFTER it completes and the cron is resumed +
      verified, to avoid CAS contention / cron-pause confusion between two concurrent prod-mutating operations.
- [x] ✅ [DATA] P1. **RESOLVED 2026-08-20 (operator Option A) — the physical cleanup is closed as a no-op-by-design.** The fresh proof found 0/98 content-equal pairs, and the DeFi-bucket objects are the live writer's regenerated corpus and the live reader's only source; retain all 98 objects. The only remaining cleanup is the separate 35 corrupted manifest rows. **Original gate and evidence retained below for audit history.** Original wording: **NEW 2026-08-10 (slot-2) — gated on step 1 landing AND a FRESH 5-part delete-safety proof (Part 4 "no live reader" was FALSE the first time — must genuinely re-verify clean this run) before any delete. UPDATE 2026-08-19 (slot-15): FRESH proof executed this run — verdict FAILED, DELETE FORBIDDEN (Part 2: 0/98 content-equal, every cefi "twin" diverges by data-key rows — these are NOT duplicates; Part 4: `CanonicalPerpFundingProvider` still live-reads this bucket+prefix). Now blocked on the [OPERATOR] decision todo below, NOT on step 1.** Follow-up: physical GCS duplicate cleanup (step 3 of the 2026-08-04 ruling above) — line-1-completeness fix 2026-08-19, `/plan-reconcile manifest_master` (hard constraint moved up from line 2). The 98 (not ~35 — that figure is ruling item 2's corrupted-MANIFEST-rows count; census slot-8 2026-08-10 + slot-15 2026-08-19: 7 venues × 7 days × 2 data_types) real CeFi-Tardis
      `perp_funding`/`perp_daily_ctx` objects physically mis-filed in the DeFi bucket
      (`gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2026-05-16..22/ pipeline_mode=batch_tardis/asset_group=cefi/venue={BINANCE,BITFINEX,BITGET,BYBIT,KRAKEN,OKX}-FUTURES|DERIBIT/…`,
      verified present 2026-08-10, correct cefi-bucket twins verified at the matching prefix) are still there. Gated on
      step 1 of that ruling landing (corpus re-run/schedule confirmed fresh — i.e.
      `CanonicalPerpFundingProvider. funding_window()` returns non-empty CURRENT observations for all 6
      `catalog_carry.py` venues) AND a FRESH 5-part delete-safety proof (Part 4 "no live reader" was FALSE the first
      time — must genuinely re-verify clean this run) before any delete. Do NOT run concurrently with an in-flight
      defi-bucket rebuild/consolidator-CAS rewrite. **Repo: unified-trading-library / market-tick-data-service** (UTL
      `gcs_delete_object`, never subprocess).
- [x] ✅ [OPERATOR] P1. **RESOLVED 2026-08-20 — operator chose Option A: accept the resolved P2 design and close step 3 as a no-op-by-design.** **Original decision request and evidence retained below for audit history.** Original wording: **NEW 2026-08-19 (slot-15) — decision required: step 3 of the 2026-08-04 ruling is structurally
      unachievable as written; pick a direction (this is an architecture call the RESOLVED P2 ruling already touched —
      not AO-decidable).** Fresh-proof findings (slot-15 Progress Log): (a) the 98 defi-bucket objects are NOT
      duplicates of their cefi twins (0/98 content-equal — both sides carry rows the other lacks, so a delete loses
      data no twin contains); (b) the RESOLVED P2 ruling keeps this exact defi-bucket prefix as the by-design corpus
      home — the live writer regenerates it (the 2026-08-19 recompute wrote `cefi_BYBIT-FUTURES_2026-08-16.parquet`
      there) and `CanonicalPerpFundingProvider` reads ONLY this bucket. Options: **(A)** accept P2 → close step 3 as
      no-op-by-design (keep the objects; the only remaining cleanup is ruling item 2's 35 corrupted manifest rows);
      **(B)** reverse P2's read path → migrate the reader to the cefi twins + reconcile the divergent content
      (which side is authoritative per day?) FIRST, then re-run the 5-part proof before any delete. Protocol ref:
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (disposition: `no-migrate-first`).
- [x] ✅ [DATA] P1. **DONE 2026-08-15 (slot-4) — both cron hosts launched + verified RUNNING; fire verification is the
      new follow-up todo below (both cadences are 9-11h out from launch time, can't be verified same-session).** Root
      cause was: (1) the corpus-compute cron host was never actually launched — no `cefi-perp-funding-daily-cron-*`
      instance existed; (2) the raw-input forward-poll cron host `cefi-fwd-daily-cron-20260809-110236` was TERMINATED.
      Fix executed: (a) `bash scripts/vm/launch-cefi-fwd-daily-cron-vm.sh` → `cefi-fwd-daily-cron-20260815-212910`
      (asia-northeast1-c, RUNNING, fires 09:00 UTC daily); (b)
      `bash scripts/vm/launch-cefi-perp-funding-daily-cron-vm.sh` → `cefi-perp-funding-daily-cron-20260815-212924`
      (asia-northeast1-c, RUNNING, fires 07:00 UTC daily). Both `gcloud compute instances describe … --format='value(status)'`-verified
      RUNNING at 2026-08-15T21:29:57Z (launch time was 2026-08-15T21:29 UTC — both launchers are singleton-locked +
      SCHEDULED_RECURRING, idempotent re-launch-safe, no `[OPERATOR]` tag needed for the launch itself). Neither
      launcher's own harness has fired yet (next fires: perp-funding 2026-08-16T07:00Z, fwd 2026-08-16T09:00Z) — per
      async-wait discipline, a 9-11h wait does not belong in this single-task session; verifying the actual first fire
      + corpus-freshness recovery is the follow-up todo immediately below. **Repo: deployment-service** (VM launch
      only, no code change).
- [x] ✅ [INFRA] P1. **DONE 2026-08-17 (slot-17) — both root causes fixed + shipped, live VMs hot-fixed;
      corpus-freshness itself still gated on the sibling verification todo below (needs a fire to actually land).**
      SHIPPED — `deployment-service@fb87cb2e1c` (+ `deployment-service@10edddb2` folded into the same push). (1)
      **Guard-script fix**: added `tardis-concurrency-guard.sh` staging to both the one-shot install step and the
      recurring cron line in `launch-cefi-fwd-daily-cron-vm.sh`, per the fix below. Deeper root cause found beyond
      what this todo scoped: `create-code-tarballs.sh`'s bare-launcher publish loop only globs `launch-*.sh` + `lib/
      *.sh` — `tardis-concurrency-guard.sh` matches neither, so even a manual publish run would have kept dropping it
      silently. Fixed that loop too (explicit extra-helpers publish list) and published the file to GCS directly via
      UTL `upload_to_storage` (bounded single-object write, not a subprocess `gsutil`) since the publish script itself
      is manual-only and not due to run. **Hot-fixed the live `cefi-fwd-daily-cron-20260815-212910` VM**: staged the
      guard script at `/opt/deployment-service/scripts/vm/` and rewrote `/etc/cron.d/cefi-fwd-daily` to fetch it each
      fire, so tomorrow's 09:00 UTC fire works without waiting on a manual `create-code-tarballs.sh` run. (2)
      **`cefi-perp-funding-daily-cron` root cause PINNED** (was "not pinned" in this todo's original text): live
      `xxd`/crontab read confirmed the `--start-date`/`--end-date`/log-fallback date formats
      (`%F`/`%FT%TZ`) were UNESCAPED in the cron.d heredoc — cron truncates a command at the first bare `%` and feeds
      the remainder to the command's stdin, so the ENTIRE compound command (including the `|| echo ... FAILED`
      fallback) silently never ran end-to-end, matching every observed symptom (0 `CRON[...]` exec lines, no log file
      created) despite a syntactically-valid crontab. This is the exact same bug CLASS the `cefi-fwd` twin was already
      fixed for (2026-08-09 incident) — this cron's crontab was simply missing that escape. Fixed to `\%F`/`\%FT\%TZ`
      in `launch-cefi-perp-funding-daily-cron-vm.sh`, mirroring the fwd script exactly; **hot-fixed the live
      `cefi-perp-funding-daily-cron-20260815-212924` VM's crontab** directly (confirmed via a fresh `xxd`/cat read
      post-fix — correct escaping present) so tomorrow's 07:00 UTC fire actually runs. Neither fix has had its first
      live fire verified yet (both next fires are hours out from this session) — that verification is the sibling
      "follow-up: verify the two cron hosts... actually FIRED" todo below, unchanged in scope. **Repo:
      deployment-service.**

- [x] ✅ [INFRA] P1 (superseded original text, kept for record). **NEW 2026-08-16 (slot-17) — the two 2026-08-15 cron-host launches (task -1b75e9a1f3d4)
      cannot clear the step-1 corpus-freshness gate as configured; root-caused via live SSH + source read, not
      guessed.** (1) **`cefi-fwd-daily-cron-20260815-212910`'s 09:00 UTC `launch-cefi-forward-poll.sh` fire FAILS
      every day** — live log (`/var/log/cefi-fwd-cron.log`, first lines) shows
      `.../launch-cefi-forward-poll.sh: line 190: .../tardis-concurrency-guard.sh: No such file or directory`
      then `[2026-08-16T09:00:17Z] cefi-fwd cron fire FAILED rc=0`. Root cause confirmed in
      `deployment-service/scripts/vm/launch-cefi-fwd-daily-cron-vm.sh` lines 129-131 + 158: the cron-install step
      `gsutil cp`s only `lib/launcher_common.sh` + `launch-cefi-forward-poll.sh` to
      `/opt/deployment-service/scripts/vm/` — it never stages the sibling `tardis-concurrency-guard.sh` that
      `launch-cefi-forward-poll.sh:190` `source`s from its own directory (confirmed present in-repo at
      `deployment-service/scripts/vm/tardis-concurrency-guard.sh`, just never copied to the VM). **The 09:15 UTC
      Deribit-options entry in the same `/etc/cron.d/cefi-fwd-daily` file is a separate, legitimate, correctly-firing
      cron** (not a misconfiguration — initially misread as one) sharing the same log file, which is why the log tail
      looked like "wrong VM operation" at first glance. **Fix**: add `tardis-concurrency-guard.sh` to both the
      one-shot install-time copy (script lines ~129-131) and the recurring cron-line copy (line 158) in
      `launch-cefi-fwd-daily-cron-vm.sh`, mirroring the existing `launcher_common.sh` staging pattern; re-launch the
      cron host (or hot-fix the live VM's `/opt/.../tardis-concurrency-guard.sh` + wait for tomorrow's fire) and
      verify via a fresh log tail post-09:00Z. (2) **`cefi-perp-funding-daily-cron-20260815-212924`'s 07:00 UTC entry
      has NEVER fired at all** — `/etc/cron.d/cefi-perp-funding-daily` is present, correctly formatted (valid
      crontab syntax, `root:root 644`, proper trailing newline confirmed via `xxd`), and the cron daemon is `active`
      and firing OTHER jobs normally (`run-parts /etc/cron.hourly`, `debian-sa1` every 10 min, confirmed in syslog) —
      but a full-day `grep cefi-perp-funding-daily /var/log/syslog` found **zero** `CRON[...]` exec lines for this
      specific job, and `/var/log/cefi-perp-funding-cron.log` does not exist (neither the success-append nor the
      `|| echo ... FAILED` fallback ever ran). Mechanism NOT pinned — flagging rather than guessing (candidates:
      cron's inotify/mtime cache missing this file at install time, a VM-clock/timezone anomaly, or something else
      cron-daemon-internal) — needs a fresh diagnostic pass (e.g. `sudo service cron restart` + wait one cycle, or
      `strace`/`journalctl -u cron -f` across a scheduled fire) by whoever picks this up. **Both fixes are
      prerequisites for step 1 (corpus-freshness) ever landing** — until then, this doc's step-3 physical-delete todo
      (below) and the sibling cron-verification todo remain correctly GATED, not merely "waiting". **Repo:
      deployment-service.**
- [x] ✅ [DATA] P1. **DONE 2026-08-20 (slot-4) — verification complete: both crons fired + healthy (08-19 fires, no `FAILED rc=`); raw flowing for 2026-08-17 (6/6 venues); corpus-freshness gate CLEARS for 2026-08-17 (6/6 venues × perp_funding/perp_daily_ctx — first measured pass since ~2026-05-20). Cron-driven freshness for 08-18/08-19 still 0: [INFRA] P1 skew fix unshipped + NEW 08-18 raw-capture miss (fwd worker OOM-preflight exit 78 on a then-stale cefi index, since recovered) — see Progress Log + new todo below. Original wording retained:** **NEW 2026-08-15 (slot-4) — no earlier than 2026-08-16T09:10Z** (line-1-completeness fix 2026-08-19, `/plan-reconcile manifest_master`: hard timing gate moved up from line 2). Follow-up: verify the two cron hosts launched above (task -1b75e9a1f3d4)
      actually FIRED and, once raw input catches up, that the corpus-freshness gate clears — check after both `cefi-fwd-daily-cron-20260815-212910` @ 09:00 UTC and
      `cefi-perp-funding-daily-cron-20260815-212924` @ 07:00 UTC have had their first fire): (1) confirm each cron
      actually fired — `gcloud compute ssh cefi-fwd-daily-cron-20260815-212910 --zone=asia-northeast1-c --command
      'sudo tail -50 /var/log/cefi-fwd-cron.log'` (expect a `cefi-fwd-{TS}` worker-VM launch line, no `FAILED rc=`) and
      the perp-funding twin's `/var/log/cefi-perp-funding-cron.log` (expect a `features-cefi-cefi-{TS}` worker-VM
      launch line); (2) bounded `list_blobs` probe of the DeFi bucket for `derivative_ticker` (6 `catalog_carry.py`
      venues, 2026-08-16) — if still 0, the raw side is honest-skipping, not broken, re-check the day after; (3) once
      raw input is confirmed flowing, re-run this doc's own corpus-freshness probe (`list_blobs`, 6 venues ×
      `perp_funding`/`perp_daily_ctx`, DeFi bucket) for a day AFTER both crons have had a chance to fire on fresh raw
      input — do not re-check same-day as the raw fire. **Repo: deployment-service** (verification only, no code
      change expected unless a cron fire genuinely fails).
- [x] ✅ [DATA] P1. **DONE 2026-08-20 (slot-14) — day=2026-08-18 raw `derivative_ticker` re-captured: 6/6
      catalog_carry venues landed (bounded UTL `list_blobs` probe — BINANCE-FUTURES 734 · BYBIT 784 · OKX-SWAP 437 ·
      KRAKEN-FUTURES 300 · BITGET-FUTURES 776 · BITFINEX-FUTURES 76 = 3107 objects, matching the 08-17 baseline).
      Backfill VM `cefi-fwd-20260820-053520` (`--force 2026-08-18 2026-08-18`, launched 2026-08-20T05:35Z) passed the
      now-fresh OOM preflight and re-captured the missing day; VM still finishing the remaining data_types
      (trades/book_snapshot_5/…). Original slot-4 wording:
      **NEW 2026-08-20 (slot-4) — day=2026-08-18 raw `derivative_ticker` capture MISSED (fwd worker exited
      78 at OOM preflight on a stale cefi index).** The 08-19 09:00Z fwd fire launched `cefi-fwd-20260819-090020`
      targeting `day=2026-08-18`, but setup failed (vm-setup.log + EXIT_STATUS=78): "OOM preflight FAIL:
      ...availability_index.parquet is 111000s stale (budget 86400s)" — the cefi manifest-consolidator was degraded
      ~30h. Index has since recovered (last_modified 2026-08-20T04:21Z, verified this session), so today's 09:00Z fire
      should pass preflight; but 2026-08-18 raw is a genuine 1-day hole (bounded probe: 0 objects, all 6 catalog_carry
      venues). Once the fwd cron re-lands 08-19/08-20 raw and the [INFRA] P1 skew fix ships, backfill/re-capture
      day=2026-08-18 (single-day launch e.g. `launch-cefi-forward-poll.sh --force 2026-08-18 2026-08-18`, Tardis cap
      permitting). **Repo: deployment-service** (verify + relaunch).
- [x] ✅ [INFRA] P1. **DONE 2026-08-20 (slot-10) — `deployment-service@42bf066f63`.** Fixed the D-1/same-day skew root
      cause pinned below: `launch-cefi-perp-funding-daily-cron-vm.sh` now fires 10:00 UTC (was 07:00) computing
      `$(date -u -d yesterday +%F)` for both `--start-date`/`--end-date` (was `+%F`, i.e. TODAY) — after the 09:00 UTC
      cefi-fwd fire has landed that day's raw. Live `cefi-perp-funding-daily-cron-20260815-212924` crontab hot-fixed
      to match (verified via SSH read post-fix: `0 10 * * *` + `date -u -d yesterday +\%F` both occurrences) so the
      corpus compute no longer perpetually honest-skips. QG green; `quickmerge --agent` landed + ancestry-verified on
      `origin/live-defi-rollout`. First live fire not yet verified this session (next fire is hours out — a fresh fire
      verification is a natural follow-up, not filed as a new todo here since none of this doc's other cron-fix
      entries file one either; the doc's existing pattern is to verify on the next pickup). **NEW 2026-08-19 (slot-4) — the corpus-freshness gate structurally CANNOT clear under the current
      cron cadence; one-day skew mechanism pinned with direct evidence (the real blocker behind every prior GATED
      re-check).** Both crons verified FIRED and healthy this pass: fwd-cron log 2026-08-19 09:00Z launched
      `cefi-fwd-20260819-090020` capturing `day=2026-08-18`; perp-funding cron log 2026-08-19 07:00Z launched
      `features-cefi-cefi-20260819-070011`. Raw `derivative_ticker` IS flowing again (CeFi bucket, day=2026-08-17:
      BINANCE-FUTURES 717 / BYBIT 728 / OKX-SWAP 446 / KRAKEN-FUTURES 280 / BITGET-FUTURES 744 / BITFINEX-FUTURES 74
      objects — first raw flow since ~2026-05-20). But `perp_funding`/`perp_daily_ctx` remain **0 for 2026-08-15..19**
      (bounded single-prefix `list_blobs` probe, never a corpus walk) because
      `deployment-service/scripts/vm/launch-cefi-perp-funding-daily-cron-vm.sh:160` fires the corpus compute with
      `--start-date $(date -u +\%F) --end-date $(date -u +\%F)` (= TODAY) at 07:00Z, while the 09:00Z fwd-cron fire
      captures only YESTERDAY's Tardis raw — so the corpus compute always targets a day whose raw input does not yet
      exist, and every run honest-skips. Verified in the features-VM run.logs (both 08-18 and 08-19 runs):
      "`<venue>/<day> no ticker shards — honest skip`", `DONE start=<day> end=<day> venue-days=0 total_funding_rows=0`,
      `exit rc=0` — the compute is healthy, just structurally empty. **Fix direction**: change the corpus cron's date
      selection to a day whose raw has landed — e.g. compute `--start-date <D-1> --end-date <D-1>` with the fire time
      moved to AFTER the same day's 09:00Z fwd capture completes (or a trailing window ending D-1), then hot-fix the live
      `cefi-perp-funding-daily-cron-20260815-212924` VM's `/etc/cron.d/cefi-perp-funding-daily` line (mirror slot-17's
      2026-08-17 hot-fix pattern). **Blocks** the step-3 physical-delete todo in this doc permanently until fixed — this
      is the root cause of the gate that has failed every re-check since 2026-08-10. **Repo: deployment-service**
      (`launch-cefi-perp-funding-daily-cron-vm.sh`).
      `gas_fees` venue==chain shape is NOT an open design question between the two options this todo originally posed —
      a THIRD option, already shipped, supersedes both. `gas_fee_handler.py`'s `venue=<chain-name>` reuse was fixed
      2026-07-22 (`market-tick-data-service@522185a6`): every `write_defi_rows()` call site now stamps a synthetic
      non-chain venue `_GAS_FEE_VENUE = "ALCHEMY"` (already a registered canonical DeFi venue —
      `unified_api_contracts/registry/defi_venues.py:362`), leaving `chain=` alone to carry the real chain-level grain.
      The pre-fix historical population (12,424 rows across 10 legacy `venue=<CHAINNAME>` prefixes: ETHEREUM, OPTIMISM,
      BSC, POLYGON, BASE, ARBITRUM, AVALANCHE, LINEA, MANTLE, AURORA) was fully migrated to canonical `venue=ALCHEMY`
      twins 2026-07-30 (`market-tick-data-service@8016c7e4`, 12,424/12,424 verified, `missing_source: 0`) — see
      `/plans/archive/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md` (archived, complete). That
      migration COPIES, it does not delete: the 9-10 legacy-venue manifest rows/GCS objects this todo's non-canonical
      census hit are that doc's own pending, already-staged, 5-part delete-safety-proofed, **`[OPERATOR]`-gated**
      physical delete — a SEPARATE, already-tracked cleanup, not this doc's (b) item and not a new ask. Given that:
      **(i) an `("venues","defi")` accepted-exception registry entry is the WRONG fix** — `_ACCEPTED_EXCEPTIONS`' own
      stated semantics are "permanently accepted, not something anyone is going to fix" (`_distinct_values.py:42-57`);
      this residue IS scheduled to be deleted (already staged), so accepting it permanently would misrepresent temporary
      cleanup lag as a permanent design exception. **(ii) a schema change to leave `venue=""` for chain-only data_types
      is also the WRONG fix** — it would require loosening `canonical_write.py::_normalize_venue()`'s deliberate hard
      non-blank-venue guard (`if not venue: raise ValueError(...)`), an invariant enforced everywhere else in the DeFi
      write path, to solve a "no real venue" problem the synthetic-venue (`ALCHEMY`) pattern already solves correctly
      and consistently with every other exception case in this same registry. **No code, registry, or schema change
      lands from this todo.** The 9 chain-shaped `defi.venues` non-canonical values will clear from the distinct-values
      drift panel on their own once the already-staged legacy-prefix delete in the linked archived doc executes
      (operator sign-off pending there, not here). Evidence trail: `market-tick-data-service@522185a6` (writer fix),
      `market-tick-data-service@8016c7e4` (migration), `unified_api_contracts/registry/defi_venues.py:362` (ALCHEMY
      canonical registration), `deployment-api/deployment_api/routes/data_status/_distinct_values.py:200-206`
      (`_ACCEPTED_EXCEPTIONS` semantics reviewed, not modified),
      `market-tick-data-service/market_interface/adapters/defi/canonical_write.py` (`_normalize_venue()` guard reviewed,
      not modified).
- [x] ✅ P2. **RESOLVED 2026-08-04 (interactive, autonomous).** Contested cross-AG architecture question:
      `features-service/features_service/cefi/calculators/perp_funding_corpus.py:254-255` deliberately writes
      CEFI-tagged (`asset_group="cefi"` in the row, `_OUT_ASSET_GROUP`) perp-funding-corpus data into the SHARED
      **DeFi** tick-data bucket (`dst_bucket = resolve_bucket_name(..., asset_group="defi")`, docstring: "writes ...
      into the shared DeFi tick-data bucket (the bucket `CanonicalPerpFundingProvider` reads)") — is this shared-bucket
      cross-tagging design still wanted? **Yes, keep it — it is demonstrably load-bearing, not merely
      "intentional-in-theory."** The P2(b) re-scope above independently proves it by direct code read:
      `strategy_service/cli/handlers/paper_run_handler.py:1987-1988`'s CARRY_BASIS_PERP/CARRY_FUNDING_DISPERSION path
      calls `CanonicalPerpFundingProvider().funding_window(...)`, which reads `perp_daily_ctx`/`perp_funding` ONLY from
      this exact shared DeFi bucket, for exactly the cefi-tagged venues `catalog_carry.py` configures as the live venue
      universe. A dedicated cross-cutting bucket would require a reader repoint + backfill/dual-read transition for a
      currently-live determinism-critical strategy path — real risk for a design that is already working as intended,
      not a bug needing architectural correction. The remaining hazard this question originally flagged (generic
      orphan-sweep tools mishandling cefi-tagged objects found under `--asset-group defi`) is ALREADY closed by P2(a)'s
      shipped chain-allowlist fix (`instruments-service@f651ff8b`) — no further architecture change needed. Decided
      using this doc's own new evidence per the autonomous-dispatch "decide, don't ask" rule (documented record of
      intent: this doc's own P2(b) investigation), not a fresh guess.
- [ ] [DATA] P3. **GATED — re-close only once `/plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md`'s own gated `[SCRIPT]` re-retirement todo lands** (root cause CONFIRMED 2026-08-16 there — a live `market-data-processing-service` writer defect, fix shipped `market-data-processing-service@94215e9cd9`; live-confirmation of that fix + safe re-retirement still pending as of that doc's latest entry). Corrected 2026-08-19 (`/plan-reconcile manifest_master`, line-1-completeness + definition-of-done fix — this line previously ended mid-sentence with no actionable instruction, and did not cite the sibling doc's now-shipped fix).
      REOPENED 2026-08-16 (plan_reconciler, defi tranche, dispatch agt-1a88e0) — the DONE claim below is
      CONTRADICTED by this same item's own STALE annotation further down; aligning the checkbox to reality. Original
      claim: **DONE 2026-08-05 — `market-tick-data-service@87e9e100` + live manifest fold executed, 0 POOL rows
      remain.** Fold historical `instrument_type=POOL` (uppercase) defi manifest rows to canonical lowercase `pool`.
      Script `scripts/one_offs/fold_pool_instrument_type_casing_2026_08_05.py` (committed
      `market-tick-data-service@87e9e100`) — 2-pass cell-classification design: Pass 1 classifies every legacy POOL
      captured cell as twin-exists vs no-twin; Pass 2 retires twin-exists rows (`capture_status→attempted_failed`) +
      optionally case-folds no-twin rows. Dry-run + live verification (2026-08-05, this session): full 605-row-group /
      74,375,757-row DeFi manifest scanned — **0 `instrument_type=POOL` (uppercase) rows remain** (already clean; prior
      session's `--apply` already completed the fold). Verified via direct manifest read (column-projected pyarrow
      ParquetFile, not inference). 8,214,021 canonical `pool` rows present. No further action needed.

      **STALE — CONTRADICTED 2026-08-11 (slot 4, data_engineering).** This "0 remaining" claim no longer holds: a fresh
          live read on 2026-08-11 (`/plans/archive/2026_08/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md`
          todo 1 — path corrected 2026-08-16, plan_reconciler, cefi tranche: doc since archived)
          found **7,930,863** `instrument_type=POOL` (uppercase) captured rows in `data_type=dex_pool_swaps` — not zero, and
          not a small residue. Root cause is NOT a recurred live-writer bug (verified: the only live `record_captured` call
          site for `dex_pool_swaps` pool-grain rows passes lowercase `instrument_type="pool"` with a bare id,
          `market-tick-data-service/cli/handlers/_dex_swaps_queries.py:174-182`) and is NOT `rebuild_defi_manifest.py`
          re-emitting uppercase (its `parse_hive_path` unconditionally `.lower()`s `instrument_type`, added 2026-06-18,
          `market-tick-data-service@3f5cc6e4`, well before the 2026-08-10 rebuild VM chain ran) — so the mechanism by which
          this population regrew from 0 to 7.9M between 2026-08-05 and 2026-08-11 is UNRESOLVED. Full writeup + open
          questions: `/plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md`. Do not trust this P3
          todo's "no further action needed" claim without reading that doc first.

## Progress Log

- **slot-15 2026-08-19 (task -6d8648d7fd76 — fresh 5-part proof executed + slot-4's named unblock)**: (1) The FRESH
  5-part delete-safety proof the step-3 todo requires was run this session (read-only, UTL helpers only, bounded).
  **Verdict: FAILED → NO delete by anyone; disposition `no-migrate-first`.** Part 1 PASS — 98/98 cefi-bucket twins at
  identical relative paths. Part 2 **FAIL** — 0/98 content-equal: every twin pair diverges by data-key row-sets
  (coin/venue/funding_rate/funding_rate_raw_per_cycle/mark_price; write-time cols excluded by design; floats rounded
  15dp; e.g. BINANCE-FUTURES 2026-05-16 perp_funding `defi_only=1 cefi_only=9`). This settles slot-13's open
  "sizes differ → Part 2 unverified": the defi objects are **divergent artifacts, NOT duplicates** — deleting them
  loses rows no twin contains. Part 3 PASS for the targeted days (writer
  `features_service/cefi/calculators/perp_funding_corpus.py` is day-parameterized; no scheduled job targets
  2026-05-16..22 — the only May-date references are the driver docstring's usage example). Part 4 **FAIL** —
  `CanonicalPerpFundingProvider` (strategy-service) day-globs the DeFi bucket filtering only `data_type=`; consumers
  `paper_universe_metrics.py:240` + `paper_run_handler.py:2036` (`funding_window`). Checked and CLEARED as a
  non-reader: `features_service/onchain/calculators/perp_funding_rates_defi.py:107` needles `asset_group=cefi/` but
  resolves the CEFI bucket (line 79) — never reads these defi objects. Part 5 moot (100% twin coverage, but the
  copied-not-moved redundancy premise died with Part 2). (2) **Structural finding → new [OPERATOR] todo above**:
  step 3 ("delete mis-filed duplicates") contradicts the RESOLVED P2 ruling (this defi-bucket prefix is the by-design
  corpus home — the live writer regenerates it, the live reader reads only it). (3) **Named unblock executed** (the
  manual recompute option the 2026-08-19 slot-4 INFRA todo names): bounded
  `run_cefi_perp_funding_corpus.py --start 2026-08-16 --end 2026-08-17` → `DONE venue-days=9 total_funding_rows=9`,
  exit 0 (08-17: all 6 carry venues; 08-16: 3 of 6 — binance/kraken/bitfinex raw absent that day). Gate-1 letter
  now PASSES for the first time since ~2026-05-20, measured through the real reader:
  `CanonicalPerpFundingProvider.funding_for_day(2026-08-17)` → non-empty for 6/6 `catalog_carry.py` venues
  (`funding_for_day(2026-08-16)` → 3/6, partial raw). (4) Side-findings: (a) the recompute's best-effort per-day
  manifest row was REFUSED (legacy ManifestWriter guard: the DeFi bucket's `_index/availability_index.parquet` is
  7.4GB > the 200MB legacy-read budget) — parquets landed; manifest registration needs per-VM shard mode or the
  consolidator; (b) raw `derivative_ticker` day=2026-08-18 is EMPTY (today's 09:00Z fwd fire launched a worker but
  landed 0 objects) — cron-driven freshness still blocked on the INFRA skew todo above; (c) corrected the step-3
  todo's "~35 objects" → 98 (35 = ruling item 2's corrupted-MANIFEST-rows count). Scratch probes stay uncommitted
  (disposable). No code shipped — the protocol-correct outcome of a failed proof is NO delete.

- **slot-17 2026-08-17 (task -1b75e9a1f3d4 fix)**: fixed + shipped both root causes named in the todo above —
  `deployment-service@fb87cb2e1c` (+ `10edddb2` in the same push). cefi-fwd: staged the missing
  `tardis-concurrency-guard.sh` at both the one-shot install step and the recurring cron line, and fixed the deeper
  gap that caused it (`create-code-tarballs.sh`'s bare-launcher publish glob never covered non-`launch-*.sh`/non-`lib/`
  helpers); published the file to GCS directly via UTL `upload_to_storage`. cefi-perp-funding: pinned the previously
  unpinned mechanism — an unescaped `%F`/`%FT%TZ` in the cron.d heredoc, the same bug class already fixed on the
  cefi-fwd twin for a 2026-08-09 incident, silently truncating the ENTIRE compound command (explains the observed 0
  exec lines + no log file). Both live cron-host VMs hot-fixed via SSH (guard staged + crontab rewritten on
  `cefi-fwd-daily-cron-20260815-212910`; crontab rewritten on `cefi-perp-funding-daily-cron-20260815-212924`) so
  tomorrow's fires don't wait on a manual `create-code-tarballs.sh` run. First live fire of either fix not yet
  observed this session (both next fires are hours out) — that's the sibling cron-fire-verification todo, unchanged.

Progress Log entries 2026-07-30 through 2026-08-10 moved **verbatim** — nothing summarized, rewritten, or dropped — to
`/plans/archive/2026_08/defi_cefi_venue_chain_axis_contamination_history_2026_07_28.md` (line-cap remediation — see that
doc for the full history).

- **slot-8 2026-08-10 (task -014 re-check before any delete)**: re-verified both -014 gates — **both still unmet, the
  physical GCS delete remains correctly blocked**. (1) **Step-1 corpus-freshness gate FAIL**: bounded list-only probe
  (UTL `get_storage_client`, never a subprocess, never a corpus walk) of the DeFi tick-data bucket
  `market-data-tick-defi-prd-central-element-323112` — the exact bucket `CanonicalPerpFundingProvider` reads — for
  `data_type=perp_funding|perp_daily_ctx` across **2026-08-01→08-10**: **0 objects for all 6 `catalog_carry.py` venues**
  (`KRAKEN/BINANCE/BYBIT/OKX/BITFINEX/BITGET-FUTURES`). `funding_window()` returns empty for current days; the corpus is
  NOT fresh. (2) **In-flight defi-bucket rebuild CONFLICT**: `canonical-migration-defi-rebuild- 20260810-204358` is
  **RUNNING** (GCE instance list, 2026-08-10) — the -014 todo explicitly forbids running any GCS-delete / manifest-CAS
  rewrite concurrently with a defi-bucket rebuild. Mis-filed objects still present: **98 objects** (7 venues × 7 days
  2026-05-16..22 × 2 data_types) at
  `raw_tick_data/by_date/day=…/pipeline_mode=batch_tardis/asset_group=cefi/venue={*-FUTURES|DERIBIT}/…` in the DeFi
  bucket, with cefi-bucket twins verified at the matching prefix (14/14 per venue). No code shipped; deletion not
  executed. Task released via `/skip-current-task` `reason_code=GATED` — re-dispatch when step-1 lands (forward-poll
  cron gap closed + corpus recompute current) AND the in-flight defi rebuild completes.

- **slot-2 2026-08-10 (task -016 re-check, same gates, ADDITIONAL FINDING — Part 1 twin claim DISPROVED)**: re-verified
  both gates — **still unmet, same state as slot-8 above**. (1) Corpus freshness: 0 `perp_funding`/`perp_daily_ctx`
  objects for all 6 venues on 2026-08-08..10. (2) `canonical-migration-defi-rebuild-20260810-204358` still RUNNING. (3)
  **NEW — prior "cefi-bucket twins verified (14/14 per venue)" claim DISPROVED on closer inspection.** Fresh bounded
  probe (UTL `list_blobs`, single-date single-venue, not a corpus walk): the cefi bucket
  (`market-data-tick-cefi-prd-central-element-323112`) DOES have objects for
  `venue={BINANCE,BYBIT,OKX,KRAKEN,BITFINEX, BITGET}-FUTURES|DERIBIT` under `pipeline_mode=batch_tardis`, but with
  **different data_types** — `derivative_ticker`, `trades`, `liquidations`, `book_snapshot_5` (the raw Tardis captures).
  **0 objects for `data_type=perp_funding` or `data_type=perp_daily_ctx`** in the cefi bucket — these data_types exist
  ONLY in the DeFi bucket. The prior "twin" claim likely matched at the venue prefix level without verifying
  `data_type=` sub-prefix. **Part 1 of the 5-part delete-safety proof FAILS**: the DeFi-bucket
  `perp_funding`/`perp_daily_ctx` copies are NOT duplicates — they are the ONLY copy of this derived data. Disposition:
  `no-still-authoritative` (these objects are the SSOT for `CanonicalPerpFundingProvider`, confirmed by prior code
  read). Soft-delete retention 604800s confirmed. Task skipped `reason_code=GATED` — re-dispatch only after (a) step-1
  corpus-freshness gate clears, (b) defi rebuild completes, AND (c) the Part 1 twin claim is independently re-verified
  with data_type-level precision.

- **slot-13 2026-08-10 (task -017 re-check, same gates; CORRECTION to slot-2's twin DISPROVAL)**: Both gates re-verified
  fresh 2026-08-10T23:05Z — **still unmet**. (1) Corpus freshness FAIL: bounded UTL list-only probe of
  `market-data-tick-defi-prd-central-element-323112` — **0** `perp_funding`/`perp_daily_ctx` objects for all 6
  `catalog_carry.py` venues on 2026-08-07..10 (`funding_window()` empty for current days; step-1 not landed). (2)
  In-flight defi rebuild `canonical-migration-defi-rebuild-20260810-204358` **still RUNNING** (gcloud instances list
  2026-08-10) — any GCS-delete/manifest-CAS rewrite remains forbidden concurrently. (3) **Part 1 twin claim re-verified
  at data_type precision: slot-2's "0 perp_funding/perp_daily_ctx in the cefi bucket" is CONTRADICTED.** Bounded probe
  of `market-data-tick-cefi-prd-central-element-323112` at the matching prefix
  (`day=2026-05-16|2026-05-22/ pipeline_mode=batch_tardis/asset_group=cefi/venue=BINANCE-FUTURES|OKX-FUTURES/instrument_type=perpetual/ data_type=perp_funding|perp_daily_ctx/`)
  finds **1 object each** — e.g.
  `.../venue=BINANCE-FUTURES/.../data_type=perp_funding/cefi_BINANCE-FUTURES_2026-05-16.parquet` (size 6202) + its
  `perp_daily_ctx` sibling, matching the DeFi-bucket shape (14 objects/day under `asset_group=cefi` there, both
  data_types). Sizes differ from the DeFi copies (e.g. DeFi perp_funding BINANCE-FUTURES 2026-05-16 = 5945) — so **Part
  2 CONTENT equivalence still NOT verified** (twins may be row-identical or not); full per-venue/day coverage not
  enumerated this pass (2 venues × 2 days probed). Disposition: delete remains BLOCKED on gates (1)+(2); when they
  clear, Part 2 content-verify must still run AND Part 4 must genuinely re-verify clean —
  `CanonicalPerpFundingProvider._read_parquets_for_day` globs `raw_tick_data/by_date/day=.../` filtering only on the
  `data_type=` path segment (no asset_group/venue allowlist), so it reads these DeFi-bucket copies today. Task
  re-skipped `reason_code=GATED`.

- **slot-6 2026-08-11 (task -016 re-check, same gates)**: re-verified both gates fresh 2026-08-11. (1) **Gate 2
  (in-flight defi rebuild) now CLEAR**: `gcloud compute instances list --filter="name~canonical-migration"` shows no
  `canonical-migration-defi-rebuild-*` instance running (only an unrelated
  `canonical-migration-prediction-shape4-merge-20260810-201105` is up) — the concurrency conflict that blocked
  slot-8/2/13 is resolved. (2) **Gate 1 (corpus freshness) still FAIL**: bounded UTL `list_blobs` probe (script, not a
  subprocess `gsutil`/corpus walk) of `market-data-tick-defi-prd-central-element-323112` at the exact writer-shape
  prefix
  `raw_tick_data/by_date/day={D}/pipeline_mode=batch_tardis/asset_group=cefi/venue={VENUE}/instrument_type=perpetual/data_type={perp_funding|perp_daily_ctx}/`
  (venue list + path shape confirmed by direct read of
  `features-service/features_service/cefi/calculators/perp_funding_corpus.py`'s own `RAW_TO_STRATEGY_VENUE` mapping and
  output-path f-string, not assumed) — **0 objects for all 6 `catalog_carry.py` venues
  (KRAKEN/BINANCE/BYBIT/OKX/BITFINEX/BITGET-FUTURES) × both data_types × 2026-08-08..11**. `funding_window()` still
  returns empty for current days; the P1 corpus-refresh todo above remains gated on its own forward-poll-cron
  dependency, unchanged since slot-13's 2026-08-10 check. Delete remains BLOCKED on gate (1); Part 2 content-verify and
  a fresh Part 4 re-check are also still outstanding per slot-13's note. Task released `reason_code=GATED` — re-dispatch
  once the corpus-refresh P1 todo lands.

- **slot-30 2026-08-11 (task re-check, same gates — no change from slot-6)**: re-verified both gates fresh 2026-08-11.
  (1) **Gate 2 (in-flight defi rebuild) still CLEAR**:
  `gcloud compute instances list --filter="name~canonical-migration"` shows only the unrelated
  `canonical-migration-prediction-shape4-merge-20260810-201105` running — no `canonical-migration-defi-rebuild-*`
  instance. (2) **Gate 1 (corpus freshness) still FAIL**: bounded UTL `list_blobs` probe (Python,
  `unified_trading_library.cloud_interface.get_storage_client` — no subprocess `gsutil`, no corpus walk) of
  `market-data-tick-defi-prd-central-element-323112` at the writer-shape prefix
  `raw_tick_data/by_date/day={D}/pipeline_mode=batch_tardis/asset_group=cefi/venue={VENUE}/instrument_type=perpetual/data_type={perp_funding|perp_daily_ctx}/`
  — **0 objects for all 6 `catalog_carry.py` venues (KRAKEN/BINANCE/BYBIT/OKX/BITFINEX/BITGET-FUTURES) × both data_types
  × 2026-08-08..11**. The P1 corpus-refresh todo above remains gated on its own forward-poll-cron dependency — unchanged
  since slot-6's check earlier the same day. Delete remains BLOCKED on gate (1); no code shipped, no delete executed.
  Task released `reason_code=GATED` — re-dispatch once the corpus-refresh P1 todo lands.

- **slot-23 2026-08-15 (adjacent finding while working the sibling `[DIAG] P3` todo in
  `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md`, task
  `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02-002`)**: re-ran this doc's own corpus-freshness gate check
  (bounded `list_blobs`, 6 `catalog_carry.py` venues × `perp_funding`/`perp_daily_ctx`, DeFi bucket, days
  2026-08-11..15) — **still 0 objects, same result as slot-8/2/13/6/30's 2026-08-10/11 checks, unchanged 4-5 days
  later.** Went one step further than those 5 prior re-checks and diagnosed WHY via
  `gcloud compute instances list`: **no `cefi-perp-funding-daily-cron-*` instance exists at all** (the corpus-compute
  cron shipped 2026-08-06 but was apparently never actually launched), and the separate raw-input forward-poll cron
  host **`cefi-fwd-daily-cron-20260809-110236` is TERMINATED** (0 raw `derivative_ticker` objects confirmed for the
  same 6-venue/5-day window — consistent with a dead capture cron, not just a quiet week). Filed a new `[DATA] P1`
  todo above naming both launch actions concretely (both launchers are singleton-locked/SCHEDULED_RECURRING —
  idempotent, safe to re-run). Not launched here — outside this task's own scope (a P3 diagnostic todo in a different
  doc); flagging for whoever picks up the todo above next. No code changed.

- **slot-7 2026-08-15 ~21:36Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-7a50eb15bb1e`,
  follow-up cron-verification re-check)**: Picked up the follow-up todo above (verify
  `cefi-fwd-daily-cron-20260815-212910` + `cefi-perp-funding-daily-cron-20260815-212924`). The todo's own done-when
  is explicit — "No earlier than 2026-08-16T09:10Z" (both crons' first fires are 07:00Z/09:00Z on 2026-08-16, per the
  launch entry directly above). Current time confirmed **2026-08-15T21:36Z** — ~11.5h before the gate opens; none of
  the todo's 3 verification steps (cron log tail, raw `derivative_ticker` probe, corpus-freshness re-probe) can
  produce a meaningful result yet, so no GCS/gcloud calls were made this pass. Skipping `reason_code=GATED` (real ETA
  ~694min exceeds the fleet's 180min dispatch-cooldown cap — `estimated_unblock_minutes` left unset so the standard
  GATED cooldown policy applies rather than passing a value the server would discard anyway). Re-dispatch any time
  at/after 2026-08-16T09:10Z.

- **slot-3 2026-08-16 ~01:46Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-7a50eb15bb1e`,
  follow-up cron-verification re-check)**: Re-picked up the same follow-up todo (unchanged since slot-7's check).
  Gate is still explicit — "No earlier than 2026-08-16T09:10Z". Current time confirmed **2026-08-16T01:46Z** — ~7.4h
  before the gate opens; none of the 3 verification steps can produce a meaningful result yet, so no GCS/gcloud calls
  made this pass. Skipping `reason_code=GATED` (real ETA ~444min exceeds the fleet's 180min dispatch-cooldown cap).
  Re-dispatch any time at/after 2026-08-16T09:10Z.

- **slot-17 2026-08-16 ~23:56Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-345201378396`,
  step-3 physical-delete re-check)**: Fresh-pulled all repos first (no doc drift since last snapshot). Re-verified
  step-1 gate via a bounded UTL `list_blobs` probe (single-day-prefix each, not a corpus walk) of
  `market-data-tick-defi-prd-central-element-323112` for `perp_funding`/`perp_daily_ctx`, 6 `catalog_carry.py`
  venues, 2026-08-12..16: **0 matched objects every day** (08-12: 1044 total objects at that day-prefix / 0 matching;
  08-13: 1124/0; 08-14: 380/0; 08-15: 33/0; 08-16: 0/0). `funding_window()` still returns empty for current days —
  step 1 has NOT landed, same result as every prior check since 2026-08-10. **Went further than prior re-checks**:
  live-SSH-verified WHY the 2026-08-15 cron-host launches (previously marked "DONE") cannot close this gate as
  currently configured — both hosts have real, distinct bugs (fwd-cron: missing sourced dependency causes the
  09:00Z forward-poll to fail every fire; perp-funding-cron: correctly-installed `/etc/cron.d` entry never actually
  executes, mechanism unpinned). Full evidence + fix guidance filed as a new `[INFRA] P1` todo directly above the
  cron-verification follow-up todo — this is the real blocker, not mere elapsed-time waiting. My own task remains
  correctly GATED on step 1 (+ the still-outstanding fresh 5-part delete-safety proof once it does land). No delete
  executed, no code shipped. Released `reason_code=GATED`.

- **slot-33 2026-08-17 (data_engineering, task `defi_cefi_venue_chain_axis_contamination-345201378396`, step-3
  physical-delete re-check)**: Fresh-pulled all repos (clean, no doc drift). Re-verified both gates fresh. (1)
  **Gate 2 (in-flight defi rebuild) CLEAR**: `gcloud compute instances list --filter="name~canonical-migration"`
  returns empty — no `canonical-migration-defi-rebuild-*` instance running. (2) **Gate 1 (corpus freshness) still
  FAIL**: bounded UTL `list_blobs` probe (Python via `unified_trading_library.cloud_interface.get_storage_client`,
  single-prefix-per-(day,venue,data_type), not a corpus walk) of `market-data-tick-defi-prd-central-element-323112`
  at the exact writer-shape prefix
  `raw_tick_data/by_date/day={D}/pipeline_mode=batch_tardis/asset_group=cefi/venue={VENUE}/instrument_type=perpetual/data_type={perp_funding|perp_daily_ctx}/`
  for all 6 `catalog_carry.py` venues × both data_types × 2026-08-13..17: **0 matched objects, every cell** —
  `funding_window()` still returns empty for current days. Step 1 remains un-landed, unchanged since slot-17's
  2026-08-16 check. **Root-cause confirmation**: re-checked slot-17's filed `[INFRA] P1` fix
  (`tardis-concurrency-guard.sh` never staged to the fwd-cron VM) — `grep -n "tardis-concurrency-guard.sh"
  deployment-service/scripts/vm/launch-cefi-fwd-daily-cron-vm.sh` still returns **zero hits**: the fix has NOT been
  shipped yet, so the 09:00Z forward-poll cron is still expected to fail every fire and the corpus-freshness gate
  cannot clear until that lands (out of this task's craft/repo scope — `[INFRA]`/deployment-service, not
  `[DATA]`/data_engineering — not actioned here, left for the infra-role dispatch that todo already names). My own
  task remains correctly GATED on step 1. No delete executed, no code shipped. Released `reason_code=GATED`.

- **slot-12 2026-08-17T02:35Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-345201378396`,
  step-3 physical-delete re-check — same-day repeat of slot-33's check above)**: Fresh-pulled repos, re-verified both
  gates independently. (1) **Gate 2 (in-flight defi rebuild) CLEAR**: `gcloud compute instances list
  --filter="name~canonical-migration"` returns empty. (2) **Gate 1 (corpus freshness) still FAIL**: bounded UTL
  `list_blobs` probe (`unified_trading_library.cloud_interface.get_storage_client` +
  `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi")`, single-prefix-per-(day,venue,data_type),
  not a corpus walk) of `market-data-tick-defi-prd-central-element-323112` for all 6 `catalog_carry.py` venues × both
  data_types × 2026-08-13..17: **0 matched objects, every cell**. (3) Re-confirmed the blocking `[INFRA] P1` fix
  (`tardis-concurrency-guard.sh` staging into `deployment-service/scripts/vm/launch-cefi-fwd-daily-cron-vm.sh`) is
  still unshipped: fresh `grep -n "tardis-concurrency-guard.sh" scripts/vm/launch-cefi-fwd-daily-cron-vm.sh` on
  `origin/live-defi-rollout` → 0 hits. No new information versus slot-33's same-day check — logged for the dispatch
  audit trail per this doc's own re-check convention, not because anything changed. Fixing the `[INFRA]`/
  deployment-service blocker directly is out of this task's `[DATA]`/data_engineering craft+repo scope (already
  separately tracked as its own todo above). No delete executed, no code shipped. Released `reason_code=GATED`.

- **slot-4 2026-08-19 ~22:57Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-6d8648d7fd76`, step-3
  physical-delete re-check — first re-check AFTER the 2026-08-17 INFRA cron fixes shipped)**: Fresh-pulled all repos.
  Re-verified both gates. **(1) Gate 2 (in-flight defi rebuild) CLEAR**: `gcloud compute instances list
  --filter="name~canonical-migration"` empty. **(2) Gate 1 (corpus freshness) STILL FAIL**, but the blocker is now
  PINNED and materially different from every prior re-check: raw `derivative_ticker` IS flowing again (CeFi bucket,
  day=2026-08-17: BINANCE-FUTURES 717 / BYBIT 728 / OKX-SWAP 446 / KRAKEN-FUTURES 280 / BITGET-FUTURES 744 /
  BITFINEX-FUTURES 74 objects — written by the 08-18 09:00Z fwd fire) — yet `perp_funding`/`perp_daily_ctx` remain 0 for
  2026-08-15..19. Root-caused via both cron-host logs + the features-VM run.logs: `launch-cefi-perp-funding-daily-cron-
  vm.sh:160` fires the corpus compute at 07:00Z with `--start-date $(date +%F)` (= TODAY), while the 09:00Z fwd fire
  captures only YESTERDAY's raw — the corpus compute always targets a day whose raw input does not exist yet, so every
  run honest-skips ("no ticker shards — honest skip", venue-days=0, exit 0; verified for the 08-18 AND 08-19 runs). The
  corpus-freshness gate structurally cannot clear under this cadence — filed a new `[INFRA] P1` todo above naming the
  exact launcher line + fix direction. Also confirmed the sibling follow-up todo's step (1): both cron hosts DID fire
  (fwd launched `cefi-fwd-20260819-090020`, perp-funding launched `features-cefi-cefi-20260819-070011`). 98
  contaminated objects (7 venues × 7 days 2026-05-16..22 × 2 data_types) still present in the DeFi bucket — delete
  remains correctly BLOCKED on gate (1); the fresh 5-part delete-safety proof stays pending until step 1 lands. No
  delete executed, no code shipped. Released `reason_code=GATED` (re-check once the perp-funding cron produces non-zero
  output — i.e. after the skew fix lands or a manual `--start <D-1>` recompute runs).

**Dispatch**: operator screenshotted deployment-ui's DEFI Distinct Values panel showing non-canonical venues/chains/
data_types/instrument_types and GMX still appearing as a venue; asked to investigate, check GCS/manifest, and execute
fixes in full per this workspace's documented safe delete/migration patterns, without further check-ins.

**Shipped (verified, landed on `live-defi-rollout`)**:

1. `perp_daily_ctx` registered as a canonical `data_type` + `SchemaContract` — `unified-api-contracts@17b1cf21`,
   `features-service@c678f0fd`, `unified-trading-pm@ccbef0315`. Historical backfill: **1,158 manifest rows registered
   for 169,461 real objects**, 0 failures, verified via direct manifest read.
2. Stale `_schema_spec_defi.py` docstring corrected (falsely claimed `dex_pools`/`dex_swaps` are current writers) —
   `unified-api-contracts@ab4693de`.
3. **GMX venue purge executed to completion** — `market-data-tick-defi-prd-central-element-323112`: 90/90 GCS objects
   backed up + deleted, 660 manifest rows dropped via CAS rewrite, consolidator cron paused/resumed correctly. Also
   corrected this workspace's own record: the archived GMX-removal plan's completion banner claimed this purge already
   ran on 2026-07-25 ("zero objects remain") — a live dry-run this session found 90 objects still present, so that claim
   did not hold up; this session's run is very likely the actual first execution.
4. gas_fees legacy-venue-prefix delete (10 prefixes, 12,424 rows, full five-part-proof already passed from a prior
   session) — dispatched to a sub-agent, in progress as of this entry (see its own doc for final status).

**New findings filed (none executed without either full delete-safety-proof pass or explicit non-execution rationale)**:

- `defi_manifest_column_fill_regression_from_gmx_purge_forced_full_merge_2026_08_04.md` (**P1, big finding**) — the GMX
  purge's forced full-merge triggered a CRITICAL `MANIFEST_COLUMN_FILL_REGRESSION` on 11 unrelated columns
  (73.92%→71.71%) across the whole 42M-row DeFi manifest, now live in production. Not root-caused or remediated —
  flagged for operator/infra-owner attention. **This is the one item from this session most worth the operator's direct
  attention on return.**
- `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md` — `dex_pools`/`dex_swaps`/`rate_indices` (~4.0M
  legacy manifest rows) confirmed retired/non-canonical, NOT executed (scale + the R5 precedent's exact failure shape
  warrant a dedicated content-verified pass, not a same-session rename).
- `defi_dex_pool_fees_retirement_recommendation_2026_08_04.md` — corrected my own initial "add to registry" instinct per
  operator's live guidance: `dex_pool_fees` should NOT be canonicalized; pool fees are derivable from already- canonical
  `dex_pool_state`(rate)×`dex_pool_swaps`(volume), mirroring the gas-fee "engineer, don't backfill" principle.
- `defi_hyperliquid_residual_manifest_rows_2026_08_04.md` — corrected a stale citation trail (the doc previously blamed
  for HYPERLIQUID's residual defi-manifest presence doesn't actually mention HYPERLIQUID); root cause still open.
- `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md` (sub-agent finding) — HYPERLIQUID `perp_daily_ctx`
  has produced zero rows since 2026-06-02; no live writer covers it.
- P2(b) cross-AG duplicate delete — **re-scoped from "safe cleanup" to `no-still-authoritative`, do not delete**: found
  a live strategy reader (`paper_run_handler.py`'s CARRY_BASIS_PERP path) depends on this exact data with no bucket
  fallback. Overturned this doc's own prior assumption; independently resolved the sibling contested-architecture
  question using the same evidence.
- POOL-vs-pool instrument_type casing — confirmed pure historical residue (both write paths already lowercase), filed as
  a low-priority P3 cleanup todo in this doc.

**Not executed, with reasons (not silent gaps — each is a tracked todo in its own doc)**: the 4M-row dex_pools/
dex_swaps/rate_indices migration (scale + precedent risk), dex_pool_fees retirement (needs strategy-layer review),
HYPERLIQUID residual-row root cause (DIAG not yet run), the new column-fill regression (needs a dedicated repro), POOL
casing fold (P3, cosmetic — not currently mis-badged).

**Process note**: this session found and corrected two cases where a prior doc's stated completion did not match live
reality (GMX purge banner; the P2(b) "safe to delete" assumption) — both caught by insisting on live verification
(`--dry-run`, direct code reads) over trusting prior written claims, per this workspace's own R5 precedent.

- [x] ✅ [DIAG] P1. **NEW 2026-08-04 (interactive session, found while investigating a related bare-OKX manifest
      cleanup) — a THIRD, previously-uncovered `chain="FUTURES"` occurrence, CeFi-bucket-native, root-cause NOT yet
      pinned.** Direct read of `market-data-tick-cefi-prd-{PROJECT_ID}`'s consolidated index found 943
      `chain=="FUTURES"` rows — **8 `BITFINEX-FUTURES`** (`date=2026-07-24`, written by 07-27: consistent with the
      already-fixed `migration_orphan_sweep.py` bug, `instruments-service@f651ff8b`, 2026-07-30 — likely the SAME
      mechanism as this doc's Pattern B, just landing in the cefi bucket instead of/in addition to the defi one; not
      independently re-traced) — **and 935 `COINBASE-FUTURES` `derivative_ticker` `captured` rows, `date=2026-08-03`,
      written `2026-08-04T03:02-03:31Z` — i.e. TODAY, well after the 2026-07-30 fix shipped.** This second population is
      a genuinely NEW, still-open bug. Correlates with `cefi-fwd-20260804-021235` (the historical-gap backfill VM from
      `cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`, launched 02:12Z today off the just-fixed
      `deployment-service@fa794a1` forward-poll singleton-filter bug — this cron path had been silently dead since
      2026-05-20, so today is its first real run ever). **Root cause NOT in the writer**: pulled this exact VM's raw
      per-VM shard (`gs://.../_index/per_vm/cefi-fwd-20260804-021235.parquet`, 30,414 rows, 12,314 of them real
      `COINBASE-FUTURES` entries) and found **zero** `chain=="FUTURES"` rows in it — the writer stamps blank chain
      correctly. The corruption appears only in the CONSOLIDATED canonical index, for a SMALL SUBSET (935/12,314, ~7.6%)
      of this VM's COINBASE-FUTURES rows — selective corruption is more consistent with a merge/dedup key-collision bug
      in the manifest-consolidator (Cloud Run, `*/1 * * * *`) than a blanket writer bug, but NOT confirmed to an exact
      line — flagging rather than guessing, per this doc's own established discipline. **Did not attempt a consolidator
      code fix this session** (high blast-radius — it processes every asset_group's manifest merges; a wrong guess here
      risks far more than the narrow issue it would fix). **Data cleanup DONE, root cause still OPEN**: relabeled all
      943 rows `chain=""` in place (NOT deleted — 942/943 are real `captured`/`attempted_failed` data, only the field
      was wrong; CAS write succeeded, `9,529,244` rows unchanged, verified via a scoped one-off script, not committed —
      mirrors this session's separate bare-OKX manifest cleanup pattern). **Whoever picks this up next**: (1) trace the
      consolidator's per-VM-shard merge/dedup path (`unified-trading-library`'s manifest_consolidator module) for
      anything that could inject a stale/foreign `chain` value onto a subset of rows sharing a composite key with an
      older canonical row; (2) re-check in a few days whether `chain="FUTURES"` reappears now that this forward-poll
      cron is running daily — if it does, the relabel above will need repeating until the root cause lands. **DEEPER
      TRACE 2026-08-04 (`/autonomous` continuation, same day) — search space substantially narrowed, still NOT pinned,
      still NOT fixed.** Read `manifest_consolidator.py`'s full incremental merge path end-to-end
      (`_duckdb_merge_payload` → `_dedup_key_sql` → the `survivors`/`contested`/`winners`/Option-B CTE chain) against
      the specific hypothesis the doc's own summary raises (`FUTURES` is a tradfi `instrument_type` spelling, not a
      chain — suggesting a column-alignment leak, not a dedup-key collision). **Ruled out, with the exact mechanism each
      time**: (a) the dedup-key sentinel normalization (`_dedup_key_sql`) only collapses `""`/`NULL` onto EACH OTHER,
      never onto a populated value like `"FUTURES"` — two rows with genuinely different non-empty `chain` values cannot
      land in the same dedup partition; (b) `chain` IS always resolved into the dedup key for this bucket
      (`_resolve_dedup_cols` derives it from `union_cols`, which comes from
      `DESCRIBE SELECT * FROM read_parquet(all_paths, union_by_name=true)` over canonical+shards together, so `chain`'s
      presence in the canonical alone guarantees it's never silently dropped from the key — the narrower
      "column-selection-dependent merge" bug class that WAS real and IS fixed on the sibling
      `manifest_writer._merge_shard_frames` path (`read_availability_index_column_selection_dependent_merge_2026_07_19`)
      does not apply here, this call site always requests the full column set); (c) `canon_proj`/`shard_proj` (both via
      `_typed_col_projection`) are column-COUNT- and column-ORDER-identical by construction (both project every
      `union_cols` entry, in the same order, padding absent columns with typed `NULL`, with the `is_legacy_seed_row`
      synthetic column added symmetrically to both sides only when `has_legacy_seed` — this exact class of positional
      `UNION ALL` misalignment was the root cause of a DIFFERENT 2026-07-14 incident
      (`sports_cf8_available_at_backfill_regression`) and is now deliberately hardened + tested against); (d)
      `_typed_col_projection` itself projects every column with an explicit `AS <name>`, so it cannot silently shift
      values between columns; (e) the Option-B cross-`service_name` collapse (`_option_b_collapse_ctes`) groups on
      `part_norm_excl_svc`, which still includes `chain` (only `service_name` is excluded) — so it also cannot merge two
      rows that disagree on `chain`. **Live-verified zero recurrence**: read the CURRENT canonical index directly
      (`market-data-tick-cefi-prd-{PROJECT_ID}`) ~7 hours and ~400+ consolidator cycles after the original 935-row
      finding — `chain=='FUTURES'` count is 0, so the bug has not reproduced since the relabel, which also means no
      fresh corrupted row was available to forensically diff against a clean sibling this session (the ~400 soft-deleted
      prior generations of `_index/availability_index.parquet` were not excavated — sheer volume/cost given no known
      timestamp to target; a future investigator with a known recurrence timestamp could pull that specific prior
      generation via `gcloud storage objects list ... --soft-deleted` before it ages out of the 7-day retention window).
      **Remaining candidate mechanisms, narrowed for the next investigator**: the FULL-REBUILD path (`force=True` /
      cold-bucket) shares the same dedup/Option-B CTEs but a DIFFERENT input-construction branch not traced in this
      pass; legacy-seed participation timing (`has_legacy_seed`) for the specific cycle that produced the 935 rows was
      not checked; and the possibility that the leak is upstream of the consolidator entirely, in MTDS's own write call
      for this specific data_type/venue combination, needs independent re-verification (the original session's "zero
      `chain=='FUTURES'` in the raw per-VM shard" finding was not re-derived this pass). **Still declining a blind fix**
      — same blast-radius reasoning as the original finding (this file gates every asset_group's manifest merges; a
      wrong guess here is worse than the narrow bug it would fix), now backed by a much narrower ruled-out list rather
      than an unexamined hypothesis. **FIX SHIPPED 2026-08-04, same session, on operator direction ("add automated
      detection so it's clear, but also attempt the fix").** Not a guess at the leak MECHANISM (still not pinned — see
      above) — instead, a structural invariant enforcement that eliminates the SYMPTOM regardless of mechanism, which is
      exactly why it's safe to ship without root-causing further: per UAC's `SHARD_AXIS_MATRIX`, `chain` is a real shard
      axis ONLY for `defi` — no other asset_group has a chain concept at all, so a non-blank `chain` on a
      cefi/tradfi/sports/prediction bucket is structurally impossible no matter which code path produced it.
      `unified-trading-library@7684a102` (1) adds an unconditional `chain` heal to `manifest_consolidator`'s
      merge-output projection for every non-defi per-AG bucket (folded into the existing, well-precedented `ag_replace`
      REPLACE clause — mirrors the asset_group self-heal pattern already in this file, not new merge logic), covering
      BOTH the incremental and full-rebuild code paths; (2) adds a new `MANIFEST_CHAIN_AXIS_VIOLATION` event +
      `_check_chain_axis_violation` check that reads the PRE-merge canonical (before the heal scrubs it) and alerts if
      it ever finds a violation, so a live recurrence stays visible instead of being silently and permanently healed
      away — this IS the requested detection. 5 new unit tests (2 end-to-end via `consolidate()`, 3 direct on the
      checker), full `quality-gates.sh` green. **Full deploy chain live-verified, not just merged**: UTL fix → LDR → UTL
      base image auto-rebuilt (`unified-trading-library:latest`, content-verified via direct grep for
      `_check_chain_axis_violation` on the built commit's tree, not just trusting the pipeline) → MTDS's
      `update-dependency-version.yml` auto-fired but bumped to a STALE digest (built 10:01Z, before this fix landed at
      11:06Z — a real gap in that automation, not something this session investigated further) → caught via
      digest/build-timestamp cross-check, manually corrected (`market-tick-data-service@af9fed41`) to the
      content-verified correct digest → MTDS image rebuilt (Cloud Build `698a4158`, SUCCESS) → manually executed a live
      run of `uts-prod-manifest-consolidator-market-data-cefi` (rather than waiting up to ~40min for its natural hourly
      cron) and confirmed via `gcloud run jobs executions describe` that it resolved the EXACT new digest. **Separately
      found and fixed while chasing this**: the MTDS/UAC/instruments-service glue-runner outage — see
      `/plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md` (this session's fix there is what
      unblocked the stuck `update-dependency-version` workflow in the first place). Root-cause of the ORIGINAL leak
      mechanism remains formally unpinned; that is now a lower-stakes cosmetic-completeness item, not an open
      data-correctness risk, since the heal makes the symptom structurally unreachable going forward. **A FOURTH
      occurrence, operator-reported from the live Distinct Values panel: `chain="STARKNET"` for cefi.** Same class (a
      real chain name on a bucket with no chain axis), plausibly the same venue-string-splitting shape as Pattern B
      (`EXTENDED-STARKNET` is a real MVP cefi venue; a naive `-SUFFIX` split would produce exactly
      `venue="EXTENDED", chain="STARKNET"`) but not independently traced to a line — not needed, since it is covered by
      the same unconditional heal. Live-verified (2026-08-05, this session, own direct check — not carried forward from
      any earlier claim): a fresh direct manifest read of `market-data-tick-cefi-prd-{PROJECT_ID}` found 0 rows with any
      non-blank `chain` value at all (not just STARKNET) — the earlier `pp75m` manual execution had already healed it.
      Manually re-triggered `honest-coverage-daily` and confirmed the fresh rollup (`generated_at=2026-08-05T14:42:13Z`)
      shows `by_chain.cefi` with exactly ONE entry: blank (`""`), 8,977,521 rows total, no STARKNET or any other value.
      No code change needed for this occurrence — direct proof the merge-time heal generalizes beyond the original
      FUTURES case.

- [x] ✅ [SCRIPT] P2. **NEW 2026-08-04.** Extend the 5-venue `_VENUE_INSTRUMENT_TYPE` lowercase-"spot"→`"SPOT_PAIR"` fix
      (`market-tick-data-service`'s `symbol_rules.py`, same session) is CeFi's `instrument_type` axis, not this doc's
      `chain`/`venue` axis — noted here only because it was found via the same Distinct Values panel sweep, not because
      it's part of this doc's contamination pattern. Code fix + a one-off relabel of the 4,923 affected
      `empty_confirmed` rows (COINBASE-SPOT/KRAKEN-SPOT/BINANCE-SPOT/BITFINEX-SPOT/OKX-SPOT) both done this session (see
      the conversation this todo was filed from); no separate doc needed — this checkbox exists only so the corpus has a
      durable record. Shipped `market-tick-data-service@f3467634`.

- [x] ✅ [DATA] P2. **2026-08-08 (REVISED).** IS data gap hypothesis DISPROVED by slot-14 direct catalogue read
      (2026-08-08): `prod/catalog.parquet` has full mvp coverage for all 6 CARRY_BASIS_PERP venues on 2026-06-05
      (BINANCE-FUTURES 537, BYBIT 810, OKX-SWAP 329, KRAKEN-FUTURES 275, BITGET-FUTURES 469, BITFINEX-FUTURES 55;
      max_from=2026-08-06). VM `cefi-fwd-20260808-110409` produced 0 records because it was deleted by
      `unified-trading-sa` within 10-13 min (during setup, before MTDS ran) — not an IS gap. Actual root cause: VM
      premature deletion (double-insert pattern, see
      `/plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md` [OPERATOR] P0).

- **slot-14 2026-08-08**: IS gap eliminated; VM `cefi-fwd-20260808-110409` deleted at 11:14Z (10-13min). Pre-flight
  false positive (`venue_fetch.py:526-552` missing `has_instruments=True` branch → `_expected_atoms={}` → always
  "covered") fixed via `--force-download`. `cefi-fwd-20260808-123230` launched 12:32:30Z
  (`--force --force-download --data-types derivative_ticker`); MTDS running 12:34:45Z; writes confirmed
  (BINANCE-FUTURES/BITGET-FUTURES day=2026-06-05 at 12:35:57Z); VM RUNNING at T+14min. ~18-24h remaining.

- **slot-19 2026-08-11 (task -018 re-check, same gates)**: Both gates re-verified fresh 2026-08-11T00:21Z — **still
  unmet**. (1) Corpus freshness FAIL: bounded UTL list-only probe of `market-data-tick-defi-prd-central-element-323112`
  — **0** `perp_funding`/`perp_daily_ctx` objects for all 6 `catalog_carry.py` venues
  (`KRAKEN-FUTURES`/`BINANCE-FUTURES`/`BYBIT-FUTURES`/`OKX-FUTURES`/`BITFINEX-FUTURES`/ `BITGET-FUTURES`) on
  2026-08-08..11 (`funding_window()` empty for current days; step-1 not landed). (2) In-flight defi rebuild CLEAR:
  `canonical-migration-defi-rebuild-20260810-204358` no longer in GCE instance list (only
  `canonical-migration-prediction-shape4-merge-20260810-201105` still RUNNING — unrelated prediction VM). AWS also
  clean. Task re-skipped `reason_code=GATED` — re-dispatch when step-1 corpus-freshness gate clears.

- **slot-19 2026-08-11 (re-check, same gates — fresh verification 2026-08-11T08:01Z)**: Both gates re-verified fresh —
  **still unmet, deletion remains correctly blocked**. (1) Corpus freshness FAIL: bounded UTL list-only probe of
  `market-data-tick-defi-prd-central-element-323112` — **0** `perp_funding`/`perp_daily_ctx` objects on 2026-08-05..11
  for any venue, incl. all 6 `catalog_carry.py` venues (`KRAKEN-FUTURES`/`BINANCE-FUTURES`/`BYBIT-FUTURES`/
  `OKX-FUTURES`/`BITFINEX-FUTURES`/`BITGET-FUTURES`) — `funding_window()` empty for current days; step-1 not landed. (2)
  In-flight defi rebuild CLEAR: `canonical-migration-defi-rebuild-20260810-204358` absent from GCE instance list
  (unrelated `canonical-migration-prediction-shape4-merge-20260810-201105` + backfill/cefi-queue VMs still RUNNING); AWS
  clean. Task re-skipped `reason_code=GATED` — re-dispatch when step-1 corpus-freshness gate clears.

- **slot-15 2026-08-20 (operator decision + plan disposition):** Operator selected Option A. The fresh five-part proof remains decisive: 0/98 content-equal pairs, the DeFi-side objects are regenerated by the live writer, and `CanonicalPerpFundingProvider` reads only the DeFi bucket. The 98 objects are retained as the by-design corpus; step 3 physical deletion is closed as a no-op. The separate 35 corrupted manifest-row cleanup remains the only cleanup item from this branch. No production data was deleted.

- **slot-4 2026-08-20 ~04:35Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-a07e2706a1ab`, cron-verification follow-up — final verification, checkbox flipped DONE)**: Fresh-pulled all repos. Live SSH to both cron hosts: both FIRED + healthy on 2026-08-19 (fwd-cron launched `cefi-fwd-20260819-090020` capturing day=2026-08-18; perp-funding-cron launched `features-cefi-cefi-20260819-070011`), no `FAILED rc=` — slot-17's guard-script + `%`-escape fixes hold. Bounded UTL list_blobs probe (6 venues × 3 days): raw `derivative_ticker` (CEFI bucket) = **6/6 venues on 2026-08-17** (717/728/446/280/744/74), **0 on 08-18/08-19**; corpus `perp_funding`/`perp_daily_ctx` (DEFI bucket) = **12 objects on 2026-08-17 (6/6 venues × 2 data_types — slot-15's manual recompute, presence confirmed) → corpus-freshness gate CLEARS for 08-17, first measured pass since ~2026-05-20**; 0 on 08-18/08-19. Two distinct blockers remain for cron-driven freshness, both verified this session: (1) the [INFRA] P1 one-day-skew is unshipped — launcher:160 AND the live `/etc/cron.d/cefi-perp-funding-daily` both still fire `--start-date $(date +%F)` (= TODAY) at 07:00Z, so the 08-18/08-19 corpus runs honest-skipped (confirmed in the 08-19 features-VM run.log: every venue "no ticker shards — honest skip", venue-days=0, exit 0); (2) **NEW — 08-18 raw was never captured**: the 08-19 fwd worker exited `78` at OOM preflight ("...availability_index.parquet is 111000s stale (budget 86400s)") — cefi manifest-consolidator degraded >24h at that moment; index since recovered (last_modified 2026-08-20T04:21Z), today's 09:00Z fire should pass preflight — filed as a new `[DATA] P1` backfill todo above. Step-3 physical delete is CLOSED (operator Option A), so these gaps gate only live-strategy corpus freshness, not any delete. No code changed (verification-only task).

## Deferred after 2026-08-09

- **P1 corpus recompute**: historical window landed (confirmed 08-09); blocked on the NEW 08-06+ forward-poll cron gap
  (`[INFRA] P1`), filed in `/plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md`).
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries) — unchanged, still accurate
