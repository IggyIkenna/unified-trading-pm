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
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md,
    /plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md,
  ]
created: "2026-07-28"
last_updated: "2026-08-04"
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
    /plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md,
    instruments-service/scripts/migration_orphan_sweep.py,
    instruments-service/scripts/backfill_orphan_class_e.py,
    features-service/features_service/cefi/calculators/perp_funding_corpus.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
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
      **DeFi** bucket. Comparison-checked: the identical `(day, pipeline_mode, asset_group, venue,     instrument_type)`
      prefix ALSO exists correctly in `market-data-tick-cefi-prd-...` — this looks like a **duplicate write to both
      buckets**, not data stranded only in the wrong place, so a cleanup of the DeFi-bucket copies is unlikely to lose
      data (not independently verified row-for-row). The literal `chain="FUTURES"` manifest value is the `-FUTURES`
      suffix of the glued `{EXCHANGE}-FUTURES` venue strings (e.g. `BITFINEX-FUTURES`) being run through a DeFi-style
      `PROTOCOL-CHAIN` venue/chain splitter that doesn't validate the suffix against `KNOWN_CHAINS` before splitting —
      the SAME bug _class_ as the already-fixed EXTENDED-STARKNET/LIGHTER-ZKSYNC "-CHAIN-suffix" split
      (`instruments_cefi_g1_g5_gate_execution_2026_07_24.md`), hitting the "-FUTURES" venue family this time instead of
      an on-chain-perp-CLOB chain suffix. **Splitter location FOUND (slot-15, concurrent session, see Progress Log
      below) — it is NOT MTDS-side as this entry originally guessed; it's
      `instruments-service/scripts/     migration_orphan_sweep.py:253`'s `shard_key_from_segments()`, missing the
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
      `paper(W) ==     batch-rerun(W)` epsilon=0 depends on this exact physical data being present. **Deleting these
      objects would not be a redundant-duplicate cleanup — it would silently remove data a live, determinism-critical
      strategy path reads today, with no fallback to the cefi-bucket copy.** This is confirmed by direct code read (not
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
- [ ] [DATA] P3. **NEW 2026-08-04.** Fold historical `instrument_type=POOL` (uppercase) defi manifest rows to canonical
      lowercase `pool` — confirmed pure historical residue via direct code read (both `write_defi_rows()`
      `canonical_write.py:260/314/334/353` and `websocket_runner.py:112` already lowercase before persistence; no live
      writer emits uppercase). NOT currently badged non-canonical (the `(defi, instrument_types)` case-insensitive
      comparison exception in `deployment-api/deployment_api/routes/data_status/_distinct_values.py` already silences
      it), so this is a cosmetic/hygiene data migration, not a correctness fix — P3, not urgent. Recipe: bounded
      manifest read filtered to `instrument_type=="POOL"`, verify the lowercase canonical twin either already exists
      (fold, Part-5 legacy-copied-not-moved invariant) or doesn't (straight case-rename, no content risk since it's the
      same rows) before any manifest rewrite; mirror the `register_defi_fold_manifest.py`/dex_pools-fold precedent. Not
      executed this session — flagged, not yet scoped with live row counts.

## Progress Log

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
