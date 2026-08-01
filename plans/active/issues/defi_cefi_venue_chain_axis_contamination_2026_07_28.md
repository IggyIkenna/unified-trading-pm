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
last_updated: "2026-07-28"
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
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    instruments-service/scripts/migration_orphan_sweep.py,
    features-service/features_service/cefi/calculators/perp_funding_corpus.py,
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
- [ ] [OPERATOR] [DATA] P2 (b)+(c) remaining, split out from the original combined todo above (part (a) is done): (b)
      decide + execute cleanup of the ~35-42-row / 7-venue / 1-week (2026-05-16→2026-05-22) DUPLICATE CeFi objects
      physically stored in the DeFi bucket (`market-data-tick-defi-prd-...`) — **[OPERATOR]** requires sign-off per
      delete-safety-protocol before any GCS delete/move (the na-eligibility-audit's 2026-07-30 CONTESTED VERDICT below
      already flagged this exact gap); confirm row-for-row duplication (not just prefix-existence) against the cefi
      bucket copy FIRST — note the fix in (a) makes the manifest self-correcting on the NEXT
      `backfill_orphan_class_e.py` sweep, so this remaining part is scoped to the physical GCS duplicate-object cleanup
      only, not a manifest re-stamp; (c) decide whether `gas_fees`'s venue==chain shape (candidate-class-1 finding, NOT
      cross-AG, NOT a writer bug in the "wrong data" sense) needs a `("venues","defi")` accepted-exception registry
      entry (mirroring `_ACCEPTED_EXCEPTIONS` in `deployment-api/deployment_api/routes/data_status/_distinct_values.py`)
      so it stops badging as drift, OR a schema change to leave `venue=""` for chain-only data_types — this is a design
      decision, not a bug fix, and belongs to whoever owns the gas_fees writer + the distinct-values panel's exception
      policy. Source: this doc, na-eligibility-audit 2026-07-30 tranche=defi CONTESTED VERDICT below.
- [ ] [OPERATOR] P2. **Contested cross-AG architecture question**:
      `features-service/features_service/cefi/calculators/perp_funding_corpus.py:254-255` deliberately writes
      CEFI-tagged (`asset_group="cefi"` in the row, `_OUT_ASSET_GROUP`) perp-funding-corpus data into the SHARED
      **DeFi** tick-data bucket (`dst_bucket = resolve_bucket_name(..., asset_group="defi")`, docstring: "writes ...
      into the shared DeFi tick-data bucket (the bucket `CanonicalPerpFundingProvider` reads)") — this is intentional
      architecture (a strategy needs both cefi+defi funding context in one read location), NOT itself a bug. But it
      means any generic manifest/orphan-sweep tool run with `--asset-group defi` against that shared bucket will
      encounter cefi-tagged objects and — per the cross-AG finding above — mis-handle them unless it's cefi-aware.
      Confirm with the operator whether this shared-bucket-cross-tagging design is still wanted (vs. e.g. a dedicated
      cross-cutting bucket `CanonicalPerpFundingProvider` reads from instead), since it is the root ARCHITECTURAL reason
      this bug class is even possible — fixing `migration_orphan_sweep.py` closes THIS instance but not the underlying
      hazard. Not a worker-resolvable design call.

## Progress Log

- **slot-15 2026-07-30 — todo-1 trace, live query + code read (not whole-corpus — targeted `columns=`/filter read of the
  already-consolidated index)**:

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
