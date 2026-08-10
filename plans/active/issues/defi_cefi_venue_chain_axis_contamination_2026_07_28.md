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
  `unified-trading-library@14301571`, shipped 2026-07-24) without executing a fix — this is a genuine cross-repo,
  cross-asset-group data-correctness finding per this workspace's findings-triage rule ("big finding" — NOTIFY OPERATOR
  + issue doc), not investigated to root cause here (read-only audit scope, time-bounded).
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
last_updated: "2026-08-06"
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
      independently corroborated by `/plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`'s own
      2026-07-28 manifest census (line ~273: `BINANCE-FUTURES`/`OKX-SWAP`/`KRAKEN-FUTURES`/`BITGET-FUTURES` captured
      through `2026-05-22`, `BYBIT`/`DERIBIT` through `2026-05-01`) — same population, same cutoff, two independent
      methods (live GCS probe here vs. manifest census there). **Repointing to
      `CanonicalDerivativeTickerFundingProvider` would not fix anything — its source is exactly as stale as
      `CanonicalPerpFundingProvider`'s, because the DeFi-bucket copy is COMPUTED FROM this same CeFi `derivative_ticker`
      corpus** (`perp_funding_corpus.py:254-255`'s own read side). Verified: the DeFi-bucket
      `perp_funding`/`perp_daily_ctx` population for these venues also stops dead on **2026-05-22** (checked 2026-05-20
      present, 2026-05-22 present, 2026-05-23 onward absent through 2026-08-03) — confirming the computed feed dried up
      the same day its raw input did, not independently. **Disposition unchanged**: `no-still-authoritative` stands —
      still do NOT delete the DeFi-bucket copies (no fresher alternative exists to repoint to). **New, more urgent
      implication surfaced**: the live CARRY_BASIS_PERP/CARRY_FUNDING_DISPERSION strategy path has been reading a
      completely frozen (zero new rows since 2026-05-22, over 2 months as of 2026-08-04) funding corpus for all 6
      configured venues — this is a genuine live-data-staleness finding, not just a delete-safety question, and is filed
      as a new todo in the doc that already owns this exact venue population + census
      (`/plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`) rather than duplicated here.

      **ADDITIVE-FALLBACK QUESTION EVALUATED 2026-08-04 (session continuation, data_engineering)** — a DIFFERENT
              question from the repoint question slot-4 already answered NO to above: could `CanonicalPerpFundingProvider`
              gain an ADDITIVE fallback (also check the CeFi-native bucket for these 6 venues, engaging ONLY when the DeFi-
              bucket primary read is empty for that exact (day, venue) — provably unchanged for every day the primary already
              serves) — real, safe progress toward one source of truth without touching the live-strategy read path's proven
              behavior? **Verdict: not achievable safely today — two real, evidenced blockers, not a "didn't get to it."**
              **Updated picture first** (this changes the doc's own prior framing): the underlying data outage IS being fixed
              — `perp_funding_data_semantics_and_cadence_2026_06_16.md`'s CEX-Tardis forward-capture-cron bug was ROOT-CAUSED
              + FIXED 2026-08-04 (slot-6, `deployment-service@fa794a1`) and real captures are confirmed resuming; the
              2026-05-22→2026-08-02 historical hole this outage left is a SEPARATE, already-launched, in-progress backfill
              (`/plans/archive/issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`, VM
              `cefi-fwd-20260804-021235`, running since ~02:12Z 2026-08-04, confirmed actively writing real
              `derivative_ticker` shards as of the last progress-log check). **But raw capture resuming does NOT by itself
              refresh the DeFi-bucket corpus `CanonicalPerpFundingProvider` reads** — that corpus is produced by a SEPARATE
              downstream compute step, `features-service/features_service/cefi/calculators/perp_funding_corpus.py`
              (`compute_cefi_perp_funding_corpus_for_day`), driven ONLY by a manual one-off script
              (`features-service/scripts/run_cefi_perp_funding_corpus.py`) — confirmed via a full repo grep for every caller
              of `compute_cefi_perp_funding_corpus_for_day` (3 hits: the module itself, its unit test, this one script). The
              script's own header literally documents this as temporary: `# Delete-when: CeFi perp_funding corpus compute is
              promoted to a features-service CLI subcommand and scheduled` — it has never been cron-wired, unlike the two
              forward-poll launchers this same investigation thread already fixed. **This is a previously-undocumented, real,
              actionable gap** — grepped the full `plans/`+`codex/` corpus for `run_cefi_perp_funding_corpus`/`perp_funding_
              corpus.*scheduled`/`.*cron`, zero hits before this entry. So even once the raw historical backfill + resumed
              forward cron give the compute step fresh input, the DeFi-bucket corpus will stay frozen at 2026-05-22 forever
              unless someone re-runs (or schedules) this script — see the new todo below.

              **Why the reader-side additive fallback itself is blocked (not just "not yet needed")**: the only same-tier
              candidate to build it from is `CanonicalDerivativeTickerFundingProvider` (already lives in strategy-service, no
              service-to-service import issue) — but its `_VENUE_SYMBOL_TEMPLATE` is a deliberately narrow, explicit
              per-(venue, asset) allowlist (today: `DERIBIT`/`BYBIT` only), and its own docstring requires live-GCS
              filename-shape verification before adding any venue ("Tardis symbol conventions are venue-specific, not
              formula-derivable"). `catalog_carry.py`'s live `_CARRY_BASIS_PERP_VENUE_BUNDLES` (lines ~211-229) configures the
              5 still-unmapped venues (`KRAKEN-FUTURES`/`BINANCE-FUTURES`/`OKX-FUTURES`/`BITFINEX-FUTURES`/`BITGET-FUTURES`)
              against a 13-coin `_CARRY_BASIS_PERP_COINS` universe (BTC/ETH/SOL/AVAX/ARB/LINK/MATIC/OP/NEAR/DOGE/XRP/ADA/BNB,
              lines ~240-253) — up to 65 new (venue, coin) wire-symbol pairs needing individual live verification before this
              provider could safely serve as a generic fallback, not a small patch. The architecturally cleaner alternative —
              reuse `perp_funding_corpus.py`'s own directory-listing + `_coin_from_symbol()` pattern (lists every parquet
              under the day/venue prefix and derives the coin from the filename, needing NO per-coin template) — lives in
              **features-service**, and `strategy-service` is barred by this workspace's tier-and-import-architecture rule
              from depending on another service directly (`/codex/04-architecture/tier-and-import-architecture.md`, T4:
              UTL/UAC/`unified-*-interface` only). Reusing it would mean either duplicating that non-trivial symbol-parsing
              logic inside strategy-service (a NEW two-copies-of-the-same-thing risk — the exact class of problem this
              session is trying to reduce, not add) or first migrating it into UAC as a shared registry helper — a real,
              separate, larger prerequisite change, not part of a same-session additive patch. **Given both paths are
              genuinely blocked (not merely undone), no code was written or shipped this session** — per this doc's own
              mandatory determinism bar, an unverifiable-today "fallback" is worse than an honest stop.

              **The better-sequenced next move** (lower risk, higher leverage, and doesn't touch the live-strategy read path
              at all): once the in-progress historical backfill lands, re-run (or schedule) `run_cefi_perp_funding_corpus.py`
              over the recovered window so the DeFi-bucket corpus — the SINGLE thing `CanonicalPerpFundingProvider` reads
              today — becomes current again at the SOURCE. This is a pure write-side data-freshness fix (zero changes to
              `canonical_perp_funding_provider.py` or any strategy-service read path), so it carries NONE of the determinism
              risk a reader-side fallback would, and it converges toward the operator's one-source-of-truth goal more directly
              than adding a second read path ever would — if the corpus stays fresh going forward, the reader-side fallback
              idea evaluated above may never actually be needed.

- [ ] [DATA] P1. **NEW 2026-08-04.** Once
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
- [ ] [DATA] P1. **NEW 2026-08-04 (operator ruling, interactive session) — supersedes the "no-still-authoritative,
      permanent" framing on the P2(b) checkbox above.** Operator directive: a live-reader dependency is not a reason to
      leave non-canonical/mis-keyed data permanently in place — "live can be reformatted too… batch/live symmetry means
      these bad names shouldn't exist." Concrete, correctly-SEQUENCED path (do not skip ahead — each step is gated on
      the one before it actually landing, not just being started): 1. **Gated on the P1 todo directly above landing**
      (corpus re-run/schedule confirmed fresh — i.e. `CanonicalPerpFundingProvider.funding_window()` returns non-empty
      CURRENT observations for all 6 `catalog_carry.py` venues, not just historically-backfilled ones). Only once the
      live-critical corpus is genuinely current does deleting the stale DeFi-bucket duplicate become safe — deleting
      first would still break the live CARRY_BASIS_PERP/CARRY_FUNDING_DISPERSION path (the P2(b) investigation's finding
      stands: no fresher alternative exists to repoint to today). 2. **The 35 corrupted MANIFEST rows**
      (`venue=BITGET`/etc, `chain=FUTURES` — the `migration_orphan_sweep.py` splitter-bug artifact, splitter itself
      already fixed `instruments-service@f651ff8b` 2026-07-25) are a SEPARATE, lower-risk question from the physical GCS
      duplicate: per this doc's own root-cause trace, the live reader (`canonical_perp_funding_provider.py`) globs raw
      GCS objects directly, not the manifest, and the underlying GCS objects are correctly named
      (`venue=BITGET-FUTURES`, unsplit) — only the MANIFEST registration is corrupted. **Before assuming this
      manifest-only fix is safe, verify that claim directly** (grep+read `canonical_perp_funding_provider.py`'s actual
      glob/read path — confirm it truly never consults the manifest for this data_type) — do not proceed on the doc's
      characterization alone. If confirmed, this manifest-row fix (re-key to the correct
      `venue=BITGET-FUTURES`/`chain=""` twin, or drop if a correct twin already exists) can happen independently of step
      1, with NO live-reader risk. 3. **Physical GCS duplicate cleanup** (the real CeFi Tardis objects sitting in the
      wrong, DeFi, bucket) — once step 1 confirms the live path no longer needs this exact stale copy, re-run the
      standard 5-part delete-safety proof fresh (do not reuse the old one — Part 4 "no live reader" was FALSE at the
      time it was written; it must genuinely re-verify clean this time) before any delete. 4. **HYPERLIQUID residual
      `asset_group=defi` manifest rows** — root cause still open
      (`defi_hyperliquid_residual_manifest_rows_2026_08_04.md`) — must be root-caused before it can be purged; do not
      blind-delete an unexplained residual. **Sequencing note**: do NOT run any new manifest-CAS-rewrite or GCS-delete
      script against `market-data-tick-defi-prd-central-element-323112` concurrently with the in-flight
      `purge_gas_fees_legacy_venue_prefixes_2026_08_04.py --apply` run (same bucket, same manifest index, same
      consolidator cron paused for that run's duration) — sequence AFTER it completes and the cron is resumed +
      verified, to avoid CAS contention / cron-pause confusion between two concurrent prod-mutating operations.
- [x] ✅ [DATA] P2 (c). **RESOLVED 2026-08-03 — investigated, no code/registry change needed; documented below.** The
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
- [x] ✅ [DATA] P3. **DONE 2026-08-05 — `market-tick-data-service@87e9e100` + live manifest fold executed, 0 POOL rows
      remain.** Fold historical `instrument_type=POOL` (uppercase) defi manifest rows to canonical lowercase `pool`.
      Script `scripts/one_offs/fold_pool_instrument_type_casing_2026_08_05.py` (committed
      `market-tick-data-service@87e9e100`) — 2-pass cell-classification design: Pass 1 classifies every legacy POOL
      captured cell as twin-exists vs no-twin; Pass 2 retires twin-exists rows (`capture_status→attempted_failed`) +
      optionally case-folds no-twin rows. Dry-run + live verification (2026-08-05, this session): full 605-row-group /
      74,375,757-row DeFi manifest scanned — **0 `instrument_type=POOL` (uppercase) rows remain** (already clean; prior
      session's `--apply` already completed the fold). Verified via direct manifest read (column-projected pyarrow
      ParquetFile, not inference). 8,214,021 canonical `pool` rows present. No further action needed.

## Progress Log

- **slot-15 2026-08-06 (data_engineering, task `defi_cefi_venue_chain_axis_contamination-015`)**: P2 scheduling/cron
  half SHIPPED — `deployment-service@8eff211` (deployment-service QG green, on origin): new
  `launch-cefi-perp-funding-daily-cron-vm.sh` (fires `launch-features-vm.sh` cefi/CEFI `--launch-mode full` daily 07:00
  UTC) + `vm_prefix_registry.py`/`launcher_registry.py`/`vm_log_archival_cron.py` entries (incl. missed
  `cefi-onchain-fwd-daily-cron-` sync) + `cefi/CEFI` viable-cell. **Gate**: BLK-0ea70dac unanswered → Option A (fix CODE
  landed `market-tick-data-service@467a3cd1`/`@b2cc2742`); no VM launched. `--launch-mode full` REQUIRED (launcher
  defaults dry); copies `lib/launcher_common.sh`.
- **slot-13 2026-08-06 ~12:45Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-015`) — picked up the
  P2 scheduling/cron half of the corpus-compute promotion; GATE CHECK FAILED, prep only, nothing shipped/flipped.** Task
  brief = build the deployment-service cron wiring that fires the (already-shipped) features-service cefi corpus-compute
  CLI daily. **Gate state (fresh evidence 12:45Z, not carried forward):** raw `derivative_ticker` for the 6
  CARRY_BASIS_PERP venues is STILL ~0 objects at the reader-exact path across 2026-07-20→08-06 incl. the resumed
  forward-cron days (08-03→08-06) — re-ran the shipped bounded probe
  `features-service/scripts/probe_cefi_perp_funding_raw_coverage.py --start 2026-07-20 --end 2026-08-06` (list-only;
  only BITFINEX-FUTURES has 101 total objects, on 07-22/07-24). Slot-14 backfill VM `cefi-fwd-20260806-065837` still
  RUNNING (~day 05-25 of the 74-day 05-23→08-05 window, ETA multi-day) and will NOT cover DERIBIT even after it
  terminates (needs the separate DERIBIT-only backfill, tarball@b2cc2742). The RE-OPENED raw-capture fix P1 in
  `/plans/archive/issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md` is still `- [ ]`. However the fix
  CODE (RC1/RC2/RC3: `market-tick-data-service@467a3cd1`/`@b2cc2742`) HAS shipped to LDR and slot-14 has no unshipped
  deployment-service work left (`deployment-service@2f1b36d`/`@c6707cb` already landed). Because the todo's own gate
  ("can ship any time post the raw-capture fix landing") is ambiguous vs this state (fix-code landed vs fix-todo not
  flipped), escalated BLK-0ea70dac (below) rather than unilaterally jumping the gate. **Implementation scope fully
  mapped (read-only) so the build is instant once the gate resolves:** (1) NEW
  `deployment-service/scripts/vm/launch-cefi-perp-funding-daily-cron-vm.sh` — cron-host launcher mirroring
  `launch-cefi-fwd-daily-cron-vm.sh`: prefix `cefi-perp-funding-daily-cron-`, e2-micro, `asia-northeast1-c`,
  `VM_LIFECYCLE_CLASS=SCHEDULED_RECURRING`, cadence **07:00 UTC** (staggered clear of tradfi-fwd 06:00 /
  cefi-onchain-fwd 08:00 / cefi-fwd 09:00 + deribit-options 09:15), daily fire =
  `launch-features-vm.sh --feature-family cefi --asset-group CEFI --start-date <today> --end-date <today>`; (2)
  `deployment-service/deployment_service/vm_prefix_registry.py` — add `"cefi-perp-funding-daily-cron-": None` (near the
  existing cron-host entries ~lines 1182-1203); (3) `deployment-service/scripts/vm/launch-features-vm.sh` — add
  `cefi/CEFI` to `_is_viable_cell()` + the header viable-matrix comment (the family set currently = calendar/commodity/
  cross_instrument/delta_one/multi_timeframe/onchain/sports/volatility — NO `cefi`, so the worker half needs this too,
  not just the cron host). Features-service CLI (already shipped `features-service@b2d14c9d`):
  `python -m features_service --feature-family cefi --operation compute --mode batch --asset-group CEFI --start-date <today> --end-date <today>`.
  **No heavy processes launched this session, nothing OOM-killed** (acknowledging the operator's shared-host directive);
  all work read-only. Probe env trap (re-learn cost): the probe needs `GCP_PROJECT_ID=central-element-323112` + a python
  env with `unified_trading_library`; features-service has NO `.venv` — run it with
  `market-tick-data-service/.venv/bin/python` from the features-service dir.
- **slot-13 2026-08-06 — BLOCKED-OPERATOR-DECISION BLK-0ea70dac (RESOLVED: Option A chosen → P2 todo built + ✅ by
  slot-15).** P2 cron-half gate was ambiguous (fix code shipped, RE-OPENED fix P1 still `- [ ]`); operator chose Option
  A (build now, cron honest-skips until raw lands). Build shipped `deployment-service@8eff211`.
- **slot-5 2026-08-06 (data_engineering, task `defi_cefi_venue_chain_axis_contamination-011`)**: Re-picked up on
  re-dispatch. Re-ran the gate probe (`features-service/scripts/probe_cefi_perp_funding_raw_coverage.py`, list-only at
  the reader-exact path, fresh ~07:40Z) — **gate still NOT met, recompute NOT run, checkbox NOT flipped.** Current
  coverage matrix: (a) pre-gap 05-16→05-22 intact (per-day BINANCE-FUTURES 477-492 / BYBIT 442-447 / OKX-SWAP 297-303 /
  KRAKEN-FUTURES 246-247 / BITGET-FUTURES 279-397 / DERIBIT 2 / BITFINEX-FUTURES 8-46); (b) **day=2026-05-23 now
  landed** for BINANCE-FUTURES (487 objects) + BITGET-FUTURES (436 objects) — slot-14's forced re-run VM
  `cefi-fwd-20260806-065837` is actively writing these (per `run.log` + PROGRESS.json monotonic); (c) day=2026-05-24
  BITGET-FUTURES=24 (VM mid-day); (d) **2026-05-25→2026-08-06 still ~0 objects at the reader path** for all 6
  CARRY_BASIS_PERP venues (only the pre-existing tiny remnants on 06-22→06-27 and BITFINEX-FUTURES 07-22/07-24). The VM
  is on day 2 of its 74-day forced range (05-23→08-05), ~19-24h total runtime expected — so raw input for the full gap
  has NOT landed. Per this todo's own explicit gate ("raw input must land first — no point recomputing over a
  still-honest-absent raw window"), the corpus recompute would today recompute only pre-gap + day-05-23 and
  `CanonicalPerpFundingProvider.funding_window()` would still return empty for recent days, failing the todo's own
  verification — so it is correctly NOT run. **Hold note for the dispatcher/next worker**: do NOT re-dispatch/re-run the
  recompute until slot-14's RE-OPENED P1 todo in `cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md` flips (raw
  `derivative_ticker` for the 6 venues landed across the whole 05-23→08-05 gap + forward cron resuming). The
  features-service promotion half + probe are already shipped (`features-service@b2d14c9d`/`a25990f7`/`e4e4dc93`);
  nothing shippable remains on this P1 until raw lands.
- **slot-9 2026-08-06 (data_engineering, task `defi_cefi_venue_chain_axis_contamination-011`)**: Picked up the P1
  corpus-recompute todo. **Dependency CHECK FAILED despite
  `cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`'s backfill being marked ✅ complete.** Bounded coverage
  probe (reader-exact path
  `raw_tick_data/by_date/day=…/pipeline_mode=batch_tardis/asset_group=cefi/venue={7 mapped}/instrument_type=perpetual/ data_type=derivative_ticker/`,
  83 days 2026-05-16→08-06, list-only, not a corpus walk) shows the raw `derivative_ticker` for the 6 CARRY_BASIS_PERP
  venues is essentially ABSENT across the entire gap window (05-23→08-02) AND post-gap days (08-03→08-06): only tiny
  remnants (a few coins 06-22→06-27; BITFINEX-FUTURES 07-22/07-24). The backfill's own note — "5 venues consistently 404
  on instrument-store (BINANCE-FUTURES/BYBIT/DERIBIT/BINANCE-DELIVERY/OKX)" — explains it: those shards were never
  captured; the resumed forward cron shows the same 0. Pre-gap window (05-16→05-22) retains the original 247-492
  objects/venue. **Therefore the corpus recompute (`run_cefi_perp_funding_corpus.py --start 2026-05-16 --end <today>`)
  would only re-do the already-frozen pre-gap days and honest-skip the gap — `funding_window()` would still return empty
  for recent days, failing the todo's own verification. Per the todo's explicit gate ("raw input must land first — no
  point recomputing over a still-honest-absent raw window"), the compute is NOT run and this checkbox is NOT flipped.**
  Correction + follow-up todo filed in `cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`; escalated via
  /blocked for the raw-capture fix decision.
- **slot-9 2026-08-06 ~05:01Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-011`)**: BLK-af77b2bb
  answered — operator chose **Option A** (dispatch raw-capture fix → re-dispatch corpus once raw input lands). The
  raw-capture fix follow-up (`cefi_tardis_derivative_ticker_historical_gap-002`, re-open todo in the cefi_tardis doc) is
  **dispatched to slot-14** (backlog status `dispatched`, 04:58Z). **Re-verified the gate with a DEFINITIVE full-gap
  re-check** (list-only, all 7 mapped RAW venues × every day 2026-05-23→08-06): raw `derivative_ticker` STILL absent —
  BINANCE-FUTURES = 0 across the ENTIRE gap; BYBIT/OKX-SWAP/KRAKEN-FUTURES = 0 except 2-3-coin remnants 06-22→06-27;
  BITGET-FUTURES 0 except 05-23/05-24; DERIBIT 0 except 06-22/06-23; BITFINEX-FUTURES 0 except 05-23/05-24 +
  07-22/07-24. So the corpus recompute remains correctly gated (would still be a no-op over an honest-absent window).
  Resolution recorded in this doc's BLOCKED-OPERATOR-DECISION entry (marked RESOLVED 2026-08-06, Option A) + the
  `## Deferred work after 2026-08-06` table (raw-capture fix now operator-routed → AO-dispatched). Corpus P1 checkbox
  stays `- [ ]` pending raw input landing + re-dispatch.
- **slot-9 2026-08-06 ~05:45Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-011`)**: **Promotion
  half SHIPPED** — this P1 todo's "or promote it to a scheduled features-service CLI subcommand" branch, executed while
  the corpus recompute stays gated on raw input (operator Option A on BLK-af77b2bb; slot-14 owns the raw-capture fix).
  `features-service@b2d14c9d`: added the `cefi` family to the top-level `--feature-family` dispatcher with a compute
  subcommand (`features_service/cefi/cli/main.py`, batch-only/cefi-only,
  `--operation compute --mode batch --asset-group cefi --start-date --end-date [--dry-run]`) that iterates days through
  the existing `compute_cefi_perp_funding_corpus_for_day`; Phase 4.2 `run(argv)` shim; `cefi` registered in `_FAMILIES`;
  CLI unit tests + dispatch test updated (10 families). Successor to `scripts/run_cefi_perp_funding_corpus.py` (its
  `# Delete-when:` marker names this promotion). **Why**: a scheduled cron can now fire the subcommand daily
  (`--start-date == --end-date == <today>`) so the corpus stays current the instant slot-14's raw capture lands — no
  manual re-run ever needed, and the "staying current" concern that motivated the reader-side fallback idea is resolved
  by the schedule instead. **Scope note**: the scheduling/cron half (mirroring the sibling
  `launch-cefi-fwd-daily-cron- vm.sh` pattern) is a separate deployment-service follow-up — NOT built here (slot-14 is
  actively working deployment-service on the raw-capture fix; VM-launch is operator-gated). **Checkbox still `- [ ]`** —
  the corpus recompute + `funding_window()` non-empty verification require raw input that has NOT landed; promotion
  ships the compute path, it does not substitute for the verification. Evidence: QG green on `b2d14c9d`, verified on
  `origin/live-defi-rollout`.
- **slot-9 2026-08-06 ~06:20Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-011`; pre-compact
  journal)** — **probe promoted + two follow-up ships verified.** (1) The raw-input coverage probe earned a home:
  `features-service@e4e4dc93` — `scripts/probe_cefi_perp_funding_raw_coverage.py` (list-only object counts at the exact
  reader path `compute_cefi_perp_funding_corpus_for_day` globs, for the 7 RAW_TO_STRATEGY_VENUE keys over a window).
  **RE-RUN THIS before re-dispatching the corpus recompute** — the number has a date on it (2026-08-06: all 6
  CARRY_BASIS_PERP venues still ~0 objects across the gap; this probe replaces the deleted session-scratchpad probe and
  is the honest gate check). (2) `features-service@a25990f7` fixed a stale family-count in the CLI help text ("10
  families" after the cefi addition). (3) Scheduling/cron half of the promotion is now a tracked `- [ ]` P2 todo in this
  doc (deployment-service launcher + registry, operator-gated VM launch, gated on raw landing). Final ship-set this
  session: `features-service@b2d14c9d` (cefi CLI promotion) + `features-service@a25990f7` (help-text fix) +
  `features-service@e4e4dc93` (probe) + `unified-trading-pm@759f994f3` (promotion record) +
  `unified-trading-pm@ 1c9990826` (scheduling-half P2 todo). All verified on `origin/live-defi-rollout`, all slot repos
  `ahead=0` dirty=0. Corpus P1 checkbox stays `- [ ]` (gated on raw input landing + funding_window() verification).
- **slot-9 2026-08-06 — BLOCKED-OPERATOR-DECISION (escalated to dashboard as BLK-af77b2bb; recorded here by the
  autonomous pre-compact ritual so a fresh session can see the decision request without the dashboard).** The P1
  corpus-recompute todo is gated on raw input that did NOT land (see entry above). **Options: A (recommended)** —
  dispatch a raw-capture fix: root-cause the instrument-store 404 for the 6-8 CEX-Tardis venues (BINANCE-FUTURES/BYBIT/
  OKX-SWAP/KRAKEN-FUTURES/BITGET-FUTURES/DERIBIT), re-run the backfill 2026-05-23→2026-08-02, verify the resumed cron
  captures them going forward — then re-dispatch this corpus todo once raw input actually lands. **B** — accept the
  corpus stays frozen at 2026-05-22 for the 6 venues; keep this todo gated until the raw capture is fixed (do not re-run
  the compute). **C** — run the corpus compute anyway over the available window (idempotent pre-gap re-run + tiny
  remnant days); expected outcome: `funding_window()` still empty for recent days, checkbox stays unflipped.
  **Recommendation: A. can_continue: false** (the compute would be a no-op for the target venues). Operator/main: answer
  in the dashboard to route next steps. — **RESOLVED 2026-08-06: operator/main answered Option A** in the dashboard:
  dispatch the raw-capture fix (root-cause instrument-store 404 → re-run backfill 2026-05-23→08-02 → verify the resumed
  cron captures them), then re-dispatch THIS corpus todo once raw input actually lands. The corpus checkbox therefore
  stays `- [ ]` (correctly gated); the raw-capture fix is tracked as the follow-up `- [ ]` in
  `cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md` for AO dispatch.
- **interactive session 2026-08-04 (autonomous, operator away 8h, `/autonomous`)** — operator re-raised this exact DEFI
  distinct-values panel drift (screenshot: chain-shaped venues, `FUTURES`/`HYPERLIQUID` chains, GMX still showing as a
  venue, `POOL` vs `pool` instrument_type casing, `dex_pool_fees`/`dex_pools`/`dex_swaps` non-canonical data_types) and
  asked to take it to completion, updating existing tracked docs rather than duplicating. This entry consolidates
  everything found/decided this session (full findings — this doc stays the SSOT, do not re-derive):
  - **P2(b) cross-AG duplicate delete — RE-SCOPED, see the rewritten todo above.** Do not delete; disposition flipped to
    `no-still-authoritative` after finding a live strategy reader depends on this exact data.
  - **Contested `[OPERATOR]` cross-AG architecture question (below) — RESOLVED, see its own checkbox.** The same Part-4
    investigation above independently proves the shared-bucket cross-tagging design is load-bearing for a live strategy
    path today, answering the open question.
  - **GMX residual-code check — FALSE POSITIVE, no fix needed.** Operator flagged "GMX supposed to be gone entirely, yet
    showing up as a venue." Grepped all 6 repos the original `defi_gmx_venue_removal_2026_07_25.md` claimed clean
    (`unified-api-contracts`, `market-tick-data-service`, `instruments-service`, `execution-service`,
    `strategy-service`, `unified-trading-library`) plus `deployment-api`/`features-service`. Two live (non-comment)
    hits, both verified NOT bugs: `unified-api-contracts/unified_api_contracts/registry/defi_reserve_params.py:1159` is
    the **GMX ERC-20 token** as a Compound V3 Arbitrum collateral-reserve entry (unrelated to the GMX DEX venue that was
    removed); `deployment-api/deployment_api/services/data_status/defi.py:80` is a legacy-protocol-prefix filter list
    that CORRECTLY handles residual pre-canonicalisation `GMX-*` composite-venue rows for UI display (defensive code,
    not a bug). The claim in `purge_gmx_venue_removal_2026_07_25.py`'s docstring ("zero live gmx references... across [6
    repos]") independently RE-CONFIRMED true. **The venue's continued appearance in the panel is pure manifest/GCS data
    residue** — 5,374 real historical `venue=GMX` rows (per that script's 2026-07-25 authoring-time census: ARBITRUM
    3,165 / AVALANCHE 2,209; `dex_pool_state` 4,115 / `perp_funding` 1,235 / `derivative_ticker` 16 / `liquidations` 8)
    that the purge script's `--apply` mode was written to remove but has never been run. `--dry-run` launched this
    session against LIVE data to get the current count before deciding next steps — see below/next Progress Log entry
    for the result (long-running: reads the ~52M-row consolidated index + day-sharded GCS discovery, ran in background).
  - **`POOL` (uppercase) vs `pool` (lowercase) `instrument_type` — operator-flagged, confirmed real residual drift, NOT
    a live-writer bug.** `solana_amm_pool`/`solana_vault` are correctly separate canonical values (not part of this
    finding) per `/codex/02-data/defi-canonical-naming-ssot.md`'s "dex_pool_state = EVM + Solana union" section.
    `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1238` confirms lowercase `"pool"` is
    canonical. Grepped live writers: MTDS batch adapters (`uniswapv2_adapter.py`, `curve_adapter.py`,
    `balancer_adapter.py`, `uniswapv4_adapter.py`, `uniswap_v3_adapter.py`) build row dicts with
    `"instrument_type": "POOL"` (uppercase) as an INTERMEDIATE value, but `canonical_write.py::write_defi_rows()` (the
    actual persistence chokepoint, lines 260/314/334/353) always stamps `instrument_type.value.lower()` before writing —
    the uppercase never reaches disk from this path. Live websocket connectors (`phoenix_ws.py`,
    `dex_swap_uniswap_v3_ws.py`, `curve_defi_ws.py`, `orca_defi_ws.py`, `raydium_defi_ws.py`) pass
    `instrument_type="POOL"` into `ReceivedTick`, but `websocket_runner.py:112`
    (`itype_l = (instrument_type or "").lower()`) normalizes before persisting too. **Both batch and live write paths
    already lowercase before persistence — confirmed by direct code read, not inferred.** Conclusion: `POOL` in the
    manifest is 100% historical residue (pre-dates one or both of these normalization chokepoints, or came from a
    since-retired direct-write path), not an active leak. It IS already silenced from the `is_canonical` badge by the
    existing `(defi, instrument_types)` case-insensitive comparison exception in
    `deployment-api/deployment_api/routes/data_status/_distinct_values.py` (operator-ruled 2026-07-22) — so it's not
    mis-flagged, just still cluttering the raw distinct-values enumeration as a genuinely separate historical string.
    **New todo filed below** — this is a real, if low-priority, data-only migration (fold historical `POOL` manifest
    rows to `pool`), not a code fix.
  - **`dex_pool_fees` — operator ruling: do NOT add to canonical registry (my working assumption "registry-completeness
    gap, should be added" was WRONG).** Operator's domain guidance: pool fee-tier is a static, per-pool attribute
    already encoded in the instrument definition/`instrument_id` (the `{fee_rate_bps}BPS`/`TS{tick_spacing}` symbol
    discriminator, see `/codex/02-data/defi-canonical-naming-ssot.md` "Solana AMM pool SYMBOL grammar" — same principle
    applies to EVM `fee_rate_bps` columns already on `dex_pool_state` rows) — fee ACCRUAL (the thing
    `strategy-service/scripts/materialize_dex_pool_fees.py` actually computes, $ revenue = volume × rate) is derivable
    downstream from `dex_pool_state` (rate) × `dex_pool_swaps` (volume), the same "engineer it from what's already
    canonical" principle the operator applied to gas fees (gas cost = gas units, backfilled separately, × static per-tx
    complexity — no separate "total gas fee" corpus needed either). The script's own
    `# Delete-when: the MTDS dex_pool_state writer joins subgraph feesUSD/volumeUSD` marker already anticipated this —
    it was always meant to be temporary. **Disposition: `dex_pool_fees` staying OUT of
    `DATA_TYPES_BY_ASSET_GROUP["defi"]` is CORRECT, not a gap** — the real remaining work is confirming whether
    `dex_pool_state`/`dex_pool_swaps` already carry the columns needed to retire `materialize_dex_pool_fees.py` +
    `canonical_dex_pool_provider.py`'s separate join, which is a strategy-layer (PnL-adjacent) change big enough to
    warrant its own dedicated investigation rather than a same-session code change — filed as a new issue doc rather
    than executed live against strategy fee computation without a dedicated review.
  - **`dex_pools`/`dex_swaps`/`rate_indices` (bare, legacy manifest data_type values, distinct from the already-RESOLVED
    2026-07-21 `dex_pools/` GCS-path-prefix fold) — confirmed real, large historical residue, NOT a live-writer bug**:
    `/codex/02-data/defi-canonical-naming-ssot.md:88` is unambiguous — "the legacy 2-layer split (on-disk
    `dex_pool_state` vs manifest `dex_pools`) is RETIRED — `dex_pool_state`/`dex_pool_swaps` are canonical at every
    layer" (operator-locked 2026-06-01). MTDS handler consts already write canonical names (`dex_pools_handler.py:83` →
    `dex_pool_state`, `dex_swaps_handler.py:92` → `dex_pool_swaps`); MDPS's `orchestration_scanner.py`/`swap_adapter.py`
    treat the bare forms purely as legacy-alias READ compatibility (`swap_adapter.py:59`: "legacy pre-migration MTDS
    backfill files"). `unified-api-contracts/.../_schema_spec_defi.py`'s docstring claiming `dex_pools`/`dex_swaps` are
    "current writers" is STALE relative to the SSOT + actual writer code — flagging for a doc fix, not a data
    implication. Row counts are real and large (2026-07-22 live census, cited in
    `/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_progress_log_history_2026_08_03.md:105-107`):
    `dex_pools` 454,077 / `dex_swaps` 3,458,668 / `rate_indices` 49,096 rows. **Already owned by
    `/plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`** (status: active) — this doc does
    NOT duplicate that ownership; a migration of this size (millions of rows) needs its own dedicated dry-run/apply pass
    and is out of scope to execute inline here. Not re-filed as a new doc.
  - **`perp_daily_ctx`/`perp_mark_price` registration** — confirmed already correctly scoped + unclaimed in the live AO
    backlog (`defi_satellite_ao_dispatch_batch6-010`, `status=queued dispatched_to=None`, verified via
    `check-ao-backlog-status.sh`) — dispatched to a sub-agent this session with the source issue doc's exact scope
    boundary (does NOT touch the live `CanonicalPerpFundingProvider` reader or either writer's row shape; registers the
    data_type + backfills manifest rows for already-migrated historical objects only). Result pending; will be journaled
    here or in `defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md` once complete.
  - **HYPERLIQUID residual `asset_group=defi` manifest rows** — the citation in this doc's own earlier entries (and the
    2026-08-03 cross-tranche census table) attributing this to
    `defi_venue_phase_live_definition_contradiction_2026_07_22.md` does NOT hold up — that doc, read in full, has ZERO
    mentions of HYPERLIQUID (it covers 11 unrelated `phase=="pipeline"`-filtered venues). The real reclassification SSOT
    (`/codex/02-data/defi-canonical-naming-ssot.md` "On-chain perp CLOBs are CeFi, NOT DeFi", codified 2026-06-25) cites
    `plans/active/instruments_foundation_completeness_2026_06_24.md`'s 1,802-row contaminant purge, but that purge
    explicitly names EXTENDED/PACIFICA/LIGHTER, not HYPERLIQUID. **No doc actually explains the HYPERLIQUID residual —
    filed as a new issue doc** rather than left as an uncited assumption (see repo root for the new doc).

  Query:
  `read_availability_index(bucket="market-data-tick-defi-prd-central-element-323112", columns=["venue","chain","source","pipeline_mode"])`,
  filtered to the 14 known-contaminated venue values. Result — **11,697 rows split cleanly into two DISTINCT patterns**
  (grouped by all 4 columns, full breakdown):

  **Pattern A (11,662 rows, the 9 chain-shaped venues)**: `venue == chain` EXACTLY (e.g.
  `venue=ETHEREUM chain=ETHEREUM`, `venue=POLYGON chain=POLYGON`, ... all 9), `source=onchain_rpc`,
  `pipeline_mode=batch_onchain_rpc`. Consistent with the doc's hypothesis 1 ("writer defaults venue to chain when
  unresolved") — a DeFi on-chain-RPC capture writer is stamping the chain name as the venue whenever the real
  protocol/venue can't be resolved, instead of honest-absence/unknown. **NOT yet pinned to an exact file/line** — this
  session ran out of budget mid-investigation (see the new todo above); do not assume it's fixed, this is real remaining
  scope.

  **Pattern B (35 rows, the 5 cefi-exchange-shaped venues) — FULLY ROOT-CAUSED, 3-hop chain across 2 repos, confirmed
  via direct code read (not inference)**:

  1. **`features-service/features_service/cefi/calculators/perp_funding_corpus.py:254-255`** —
     `compute_cefi_perp_funding_corpus_for_day()` reads real CeFi `derivative_ticker` data from the cefi bucket
     (`src_bucket = resolve_bucket_name(..., asset_group="cefi")`) and — BY DESIGN, per its own docstring ("writes ...
     into the shared DeFi tick-data bucket, the bucket `CanonicalPerpFundingProvider` reads") — writes the computed
     `perp_funding`/`perp_daily_ctx` output into the **DeFi** bucket
     (`dst_bucket = resolve_bucket_name(..., asset_group="defi")`), while stamping each row's OWN `asset_group` field
     `"cefi"` (`_OUT_ASSET_GROUP = "cefi"`) and `venue=strategy_venue` (e.g. `"BITGET-FUTURES"`, `"BITFINEX-FUTURES"` —
     a `RAW_TO_STRATEGY_VENUE` mapping) and an explicit empty-string `"chain": ""`. The raw GCS write path
     (`asset_group=cefi/venue=BITGET-FUTURES/instrument_type=perpetual/data_type=perp_daily_ctx/...`) has **no `chain=`
     path segment at all**. This cross-tagging is intentional architecture, not itself the bug (see the new `[OPERATOR]`
     todo above).
  2. **`instruments-service/scripts/migration_orphan_sweep.py:253`**, `shard_key_from_segments()` — when an operator
     runs this generic orphan-sweep tool with `--asset-group defi` against the shared bucket (which now also contains
     the cefi-tagged objects from step 1), it force-stamps every scanned object's `asset_group` to the CLI-level scan
     target (`"defi"`, not the object's own embedded tag) and then does:
     `if asset_group == "defi" and not chain and "-" in venue: venue, _sep, chain = venue.partition("-")` — an
     UNCONDITIONAL split on the first dash, intended for DeFi's legitimate `PROTOCOL-CHAIN` glued-venue overload (e.g.
     `EIGENLAYER-ETHEREUM`), but with **no allowlist guard**. Its sibling
     `market-tick-data-service/scripts/rebuild_defi_manifest.py` does the identical split but GUARDS it with a
     `_KNOWN_DEFI_CHAINS` frozenset — `migration_orphan_sweep.py` is missing that guard. Run against
     `venue="BITGET-FUTURES", chain=""`, this produces `venue="BITGET", chain="FUTURES"` — exactly the corrupted values
     in the manifest.
  3. **`instruments-service/scripts/backfill_orphan_class_e.py`**, `characterize_object()` (~line 279-280) re-derives
     the same (already-corrupted) key via `_sweep.shard_key_from_segments(ag, segments)`, validates venue/chain/
     instrument_type are all non-blank for the `defi` branch (they now ARE, post-split, so it wrongly passes as a
     legitimate orphan instead of escalating), then the recording loop (~line 805) calls
     `writer.record_captured(row_key=..., venue=venue, chain=chain, asset_group=asset_group, ...)` — this is the exact
     call that lands the corrupted `venue=BITGET, chain=FUTURES` row in the manifest. All 35 rows share ONE `written_at`
     timestamp cluster (`2026-07-24T20:06:38`, ~30ms spread) — one `--apply` run of this tool, one pass over `by_cell`,
     confirms this was a single backfill execution, not ongoing/recurring corruption.

  **Generality check (not fully verified, flagged)**: the split has no venue allowlist, so any dash-bearing venue
  landing in the shared bucket without a `chain=` segment would mis-parse the same way. `BINANCE-FUTURES` is in the SAME
  `RAW_TO_STRATEGY_VENUE` map as the 5 affected venues and would be written by the same cross-tagged path, but did NOT
  appear in the 14-value contamination list — most likely incidental (no `derivative_ticker` shard existed for
  BINANCE-FUTURES that specific day, or its cell was already manifested from a prior run) rather than the split logic
  distinguishing it; NOT independently confirmed against the raw `market-data-tick-cefi` bucket for 2026-07-24
  BINANCE-FUTURES presence — a gap for whoever picks up the fix todo to close before declaring the fix complete.

  **Correction to this doc's own original hypotheses**: NEITHER of the two candidate root-cause classes stated in "Why
  it matters" above is exactly right for Pattern B. It is not the TOCTOU manifest-consolidator race (hypothesis 2) — no
  consolidator CAS-write mechanism is involved at all; the corruption happens entirely inside a manual
  orphan-sweep/backfill TOOL run, not the always-on consolidator cron. It is also not simply "a writer defaults venue to
  chain" (hypothesis 1) in the sense the doc meant — the ORIGINAL writer (`perp_funding_corpus.py`) stamps `chain`
  correctly (empty string); the corruption is introduced by a SEPARATE, downstream, one-off maintenance tool that
  mis-parses an already-correct venue string. This is a third, previously-unconsidered mechanism class.

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY -> `assigned_vm: planning` (in place, name
  unchanged). all 3 todos are bounded manifest-row sampling traces with stated discriminants; conflict-check clear
  (`cross_cutting_satellite_ao_dispatch_batch1` only records the finding, does not claim the fix). Shared conflict-check
  protocol: `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` sect.3 - CLEARED.
- **na-eligibility-audit 2026-07-30** (tranche=cross-cutting, autonomous): RECLASSIFY NA → planning — the two [DIAG] P1
  todos state their own sampling method (read the actual manifest rows' venue/chain/source/pipeline_mode together) and
  the P2 fix is gated on their outcome. `cross_cutting_satellite_ao_dispatch_batch1`'s `[x]` todo FILED this doc — it
  does not claim its todos. (Same doc independently verdicted by the cefi tranche above; both reached RECLASSIFY — this
  is the multi-tranche overlap recorded in
  `/plans/archive/issues/sharded_per_tranche_audit_stash_race_and_multitranche_marker_gap_2026_07_30.md`.)
- **⚠️ CONTESTED VERDICT — na-eligibility-audit 2026-07-30** (tranche=defi, autonomous): reached the OPPOSITE verdict
  from the two tranches above — **KEEP-NA, valid**: "2 DIAG todos are bounded but todo 3 is a historical manifest
  re-stamp (`--apply`) carrying no `[OPERATOR]` tag or delete-safety cite; doc cannot flip as a unit." This cites the
  hard AO-authoring rule (an AO todo with an `--apply` needs `[OPERATOR]` + a delete-safety cite OR a stated
  safe-idempotent justification — `/plans/active/task_template.md` finding O). **Not adjudicated by the integrator**:
  three independent tranche runs disagree 2-1 and the dissent invokes a hard rule, so this is a genuine judgment call,
  not an auto-resolvable one. The doc is left in the majority state (`assigned_vm: planning`, as already committed by
  the cefi + cross-cutting tranches) — the integrator made no active change here — and the dissent is recorded rather
  than dropped. **Operator/next-toucher: decide whether the P2 `--apply` re-stamp todo needs an `[OPERATOR]` tag (and
  therefore whether this doc should revert to `assigned_vm: NA`) before a worker picks it up.**
- **interactive session 2026-07-30**: operator confirmed the live DEFI distinct-values panel still shows this exact
  contamination (16 non-canonical venues incl. the 9 chain names + 5 cefi-exchange names; chains 2 non-canonical incl.
  FUTURES) and asked to root-cause + fix, plus check whether the bad names also appear at the GCS-path level (not just
  the manifest). Both [DIAG] P1 todos above are now ROOT-CAUSED via a bounded live-data read (single-object duckdb query
  against the real `_index/availability_index.parquet`, plus a handful of targeted, single-prefix `gsutil ls` probes --
  no corpus walk). Two DISTINCT mechanisms confirmed, not one: (1) `gas_fees`'s venue==chain reuse (a legitimate
  axis-mismatch, not cross-AG bleed) explains the 9 chain-shaped venues; (2) a genuine, PHYSICAL cross-AG GCS bucket
  misfile (real CeFi Tardis `-FUTURES` venue objects duplicated into the DeFi bucket for exactly 2026-05-16 to
  2026-05-22, already stopped, pre-dating the 2026-07-24 TOCTOU fix) explains both the 5 cefi-exchange venues and the
  `chain="FUTURES"` value. **No GCS delete/move or code fix was executed this session** -- root-cause only, per the
  doc's own pre-existing scope boundary and the CONTESTED VERDICT's `[OPERATOR]` gate above. See the rewritten P2 todo
  for the 3-part remaining scope (MTDS splitter fix / duplicate-object cleanup pending operator sign-off / gas_fees
  accepted-exception design decision).
- **2026-07-30 (plans-corpus-reduction-marathon wave 4)**: shipped part (a) of the P2 fix —
  `instruments-service@f651ff8b` (the actual splitter location, `migration_orphan_sweep.py`, not MTDS — corrected from
  an earlier note in this doc that guessed MTDS-side). Parts (b) (physical GCS duplicate-object cleanup) and (c)
  (gas_fees accepted-exception design decision) remain, both correctly gated (operator sign-off / design call) — doc
  stays active/open, not archivable yet. The separate `[OPERATOR] P2` contested-architecture todo also remains open.
- **context-scout 2026-08-01**: populated context_scope (5 entries).
- **slot-2 2026-08-03 — operator-ruling dispatch, todo (c) resolved**: Ruling dispatched PART (c) ONLY of the combined
  (b)+(c) todo (part (b), the physical CeFi-duplicate-object GCS cleanup, stays untouched — no GCS delete/move
  attempted). Investigation (grep+read across market-tick-data-service, unified-api-contracts, deployment-api) found the
  original todo's two-option framing (accepted-exception vs. `venue=""` schema change) was superseded by work that had
  already shipped between this doc's 2026-07-30 root-cause entry and today: `gas_fee_handler.py`'s venue==chain reuse
  was fixed 2026-07-22 (`market-tick-data-service@522185a6`, synthetic `venue=ALCHEMY`) and the pre-fix 12,424-row
  legacy population was migrated to canonical `ALCHEMY` twins 2026-07-30 (`market-tick-data-service@8016c7e4`) — see
  `/plans/archive/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md` (archived, complete). The
  drift-panel non-canonical venues are that doc's own pending, already-staged, `[OPERATOR]`-gated legacy-prefix delete —
  a different, already-tracked cleanup, not a new decision this todo needed to make. Neither accepted-exception nor
  schema-change was applied; ruling + full reasoning recorded on the (c) checkbox above. Doc stays `status: open` (item
  (b) and the separate `[OPERATOR] P2` cross-AG architecture todo both remain open).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — dropped
  `defi_venue_phase_live_definition_contradiction_2026_07_22.md` (tangential to the two remaining `[OPERATOR]` items;
  covered the already-resolved BLAZESTAKE/HYPERLIQUID phase exception, not the physical-duplicate-delete or
  cross-AG-architecture questions still open).
- **slot-4 2026-08-04 (data_engineering, AO dispatch)**: closed the P2(b) todo's remaining "repoint question" — answered
  NO (see the checkbox). Bounded live GCS probes (not a corpus walk) additionally surfaced that the underlying CeFi
  `derivative_ticker` capture for these exact 6-8 Tardis perp venues stopped dead on 2026-05-22 and has not resumed
  through 2026-08-03, independently corroborated by
  `/plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`'s own 2026-07-28 manifest census (same
  cutoff date, same venue population). Filed as a new todo in that doc (which already owns this venue population +
  cross-references the sibling `cefi_onchain_perp_forward_capture_outage_2026_08_03.md` silent-outage precedent) rather
  than duplicated here — see that doc's Progress Log entry same date. No code changed in this doc's own scope;
  disposition (`no-still-authoritative`, do not delete) is unchanged, just now evidenced further.
- **session continuation 2026-08-04 (data_engineering)**: evaluated the P2(b) todo's remaining open question from a
  different angle than slot-4's repoint investigation — could `CanonicalPerpFundingProvider` gain a PROVABLY-safe
  ADDITIVE fallback (CeFi-native read only when the DeFi-bucket primary is empty for that exact day/venue) instead of a
  full repoint? **Verdict: genuinely blocked today, not shipped** — see the new dated entry appended to the P2(b)
  checkbox above for full evidence. Two real blockers: (1) the only same-tier candidate provider
  (`CanonicalDerivativeTickerFundingProvider`) has a narrow per-(venue,asset) symbol-template allowlist needing ~65 new
  live-GCS-verified entries to cover `catalog_carry.py`'s real venue×coin universe; (2) the architecturally cleaner
  generic reader pattern lives in features-service, which strategy-service is tier-barred from importing
  (`/codex/04-architecture/tier-and-import-architecture.md`) — reusing it without duplicating symbol-parsing logic needs
  a UAC-level migration first, out of scope for a same-session additive patch. Also surfaced (previously undocumented,
  corpus-grepped clean before this entry): the DeFi-bucket corpus's OWN compute step
  (`features-service/features_service/cefi/calculators/perp_funding_corpus.py`, driven only by the manual
  `scripts/run_cefi_perp_funding_corpus.py`) has no cron/scheduler wiring at all — so even the already-fixed forward
  capture cron + the already-running historical backfill VM (`cefi-fwd-20260804-021235`, see
  `/plans/archive/issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`) will NOT by themselves refresh
  what `CanonicalPerpFundingProvider` reads. Filed a new sequenced P1 todo above (`depends_on` the historical-gap doc)
  to re-run/schedule that compute step once the raw backfill lands — a write-side-only fix carrying zero risk to the
  live paper(W)==batch-rerun(W) read path, and the better next move before any reader-side fallback is reconsidered. No
  code shipped this session (correctly gated, per this workspace's determinism-invariant bar); disposition on the
  DeFi-bucket copies is unchanged (`no-still-authoritative`, do not delete).
- **slot-9 2026-08-04 ~12:39Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-014`)**: Executed step 2
  of the sequenced P1 cleanup path (the 35/42 corrupted MANIFEST rows). Safety verification: read
  `canonical_perp_funding_provider.py:145-168` directly — confirms `_read_parquets_for_day()` calls
  `self._storage.list_blobs()` + `self._storage.download_bytes()` against raw GCS, never reads the manifest. Live
  manifest query (gcloud-OAuth duckdb, column-projected, bounded single-object read): found **42** corrupted rows (6
  venues BINANCE/BITFINEX/BITGET/BYBIT/KRAKEN/OKX × 7 days 2026-05-16→22, not 35 as originally estimated), all
  `chain=FUTURES`/`venue=<bare-exchange>`/`data_type=perp_daily_ctx`. Correct twins (venue WITH `-FUTURES` suffix,
  chain=empty) confirmed present for all 42, 100% `capture_status` match. CAS rewrite: 42 rows dropped
  (42,192,492→42,192,450), zero corruption remaining, all 42 twins preserved. Consolidator cron
  (`uts-prod-manifest-consolidator-market-data-defi-cron`) was still PAUSED from the earlier GMX purge (~2.5h gap) —
  resumed + triggered catch-up run g8j9r. No code shipped (pure data fix, correctly scoped — no UTL/service change
  needed). Step 2 DONE. Steps 1/3/4 still gated (backfill VM `cefi-fwd-20260804-021235` still RUNNING).
- **slot-4 2026-08-04 ~09:12Z (data_engineering, AO dispatch, task `defi_cefi_venue_chain_axis_contamination-011`)**:
  Picked up the P1 todo (re-run `run_cefi_perp_funding_corpus.py` once the backfill completes). VM
  `cefi-fwd-20260804-021235` confirmed still `RUNNING` at day=2026-06-16/2026-08-02, RSS healthy. Corpus script reviewed
  — reads per-parquet one-at-a-time via Polars GCS, bounded memory, safe on shared host. Armed a harness-tracked
  background watchdog (20-min interval) to detect VM completion. Will run
  `run_cefi_perp_funding_corpus.py --start 2026-05-16 --end 2026-08-04` once VM stops + backfill is manifest-verified,
  then verify `CanonicalPerpFundingProvider.funding_window()` for a recent day per venue, then flip this checkbox.
- **slot-15 2026-08-04 ~09:30Z (data_engineering, AO dispatch, task `defi_cefi_venue_chain_axis_contamination-011`)**:
  Picked up on resume dispatch. VM `cefi-fwd-20260804-021235` still `RUNNING` at day=2026-06-17 (09:23Z). Pace ~9-10
  min/day, ~46 days remaining → estimated completion ~16:30Z. Armed 20-min background watchdog. Will run corpus script
  - verify provider once VM stops and backfill is manifest-verified.
- **context-scout 2026-08-05**: re-scouted; swapped the resolved cross-AG bleed reference + generic delete-safety/
  dispatch-batch entries for the two live blockers the doc's remaining P1 todos actually gate on
  (`cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`,
  `defi_hyperliquid_residual_manifest_rows_2026_08_04.md`) plus the concrete re-run script + reader module; now 6
  entries.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged -- still the correct pair
  of live blockers per the 2026-08-06 raw-capture-gap coverage matrix in this doc's own BLK table.

## Session final report — 2026-08-04 (`/autonomous`, operator away ~8h from ~01:00)

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

## Deferred after 2026-08-09

- **P1 corpus recompute**: historical window landed (confirmed 08-09); blocked on the NEW 08-06+ forward-poll cron gap
  (`[INFRA] P1`), filed in `/plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md`.
