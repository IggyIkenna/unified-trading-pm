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
    /plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md,
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
      the finding.
- [x] ✅ [DIAG] P1. **ROOT-CAUSED 2026-07-30.** The `chain="FUTURES"` values (+ the 5 cefi-exchange-shaped `defi.venues`
      values BITFINEX/BITGET/BYBIT/KRAKEN/OKX, plus BINANCE which the census undercounted) are confirmed **genuine
      cross-AG bleed** (candidate class 2) — and it is a PHYSICAL GCS bucket misfile, not just a manifest-index cosmetic
      issue. Live evidence: all matching rows share one narrow signature — `data_type=perp_daily_ctx`,
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
      an on-chain-perp-CLOB chain suffix — but the actual splitter code path for THIS bucket is MTDS-side
      (`market-tick-data-service`), not the `instruments-service/writers.py::_canonical_manifest_venue_chain` guard read
      for this doc's earlier EXTENDED-STARKNET finding (that guard already null-checks `KNOWN_CHAINS` and would NOT
      reproduce "FUTURES" as a chain — confirmed by reading it — so the MTDS-side equivalent is the next trace target,
      not yet located to an exact line).
- [ ] [DATA] P2. **Scope now much narrower than "fix + re-stamp the whole finding":** (a) locate + fix the MTDS-side
      venue/chain splitter that treats a `-FUTURES` suffix as if it were a `KNOWN_CHAINS` member (repo:
      market-tick-data-service) — this is a pure forward-looking code fix, no `--apply` needed; (b) decide + execute
      cleanup of the ~42-row / 7-venue / 1-week (2026-05-16→2026-05-22) DUPLICATE CeFi objects physically stored in the
      DeFi bucket (`market-data-tick-defi-prd-...`) — **[OPERATOR]** requires sign-off per delete-safety-protocol before
      any GCS delete/move (the na-eligibility-audit's 2026-07-30 CONTESTED VERDICT below already flagged this exact
      gap); confirm row-for-row duplication (not just prefix-existence) against the cefi bucket copy FIRST; (c) decide
      whether `gas_fees`'s venue==chain shape (candidate-class-1 finding, NOT cross-AG, NOT a writer bug in the "wrong
      data" sense) needs a `("venues","defi")` accepted-exception registry entry (mirroring `_ACCEPTED_EXCEPTIONS` in
      `deployment-api/deployment_api/routes/data_status/_distinct_values.py`) so it stops badging as drift, OR a schema
      change to leave `venue=""` for chain-only data_types — this is a design decision, not a bug fix, and belongs to
      whoever owns the gas_fees writer + the distinct-values panel's exception policy. Source: this doc,
      na-eligibility-audit 2026-07-30 tranche=defi CONTESTED VERDICT below.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY -> `assigned_vm: planning` (in place, name
  unchanged). all 3 todos are bounded manifest-row sampling traces with stated discriminants; conflict-check clear
  (`cross_cutting_satellite_ao_dispatch_batch1` only records the finding, does not claim the fix). Shared conflict-check
  protocol: `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` sect.3 - CLEARED.
- **na-eligibility-audit 2026-07-30** (tranche=cross-cutting, autonomous): RECLASSIFY NA → planning — the two [DIAG] P1
  todos state their own sampling method (read the actual manifest rows' venue/chain/source/pipeline_mode together) and
  the P2 fix is gated on their outcome. `cross_cutting_satellite_ao_dispatch_batch1`'s `[x]` todo FILED this doc — it
  does not claim its todos. (Same doc independently verdicted by the cefi tranche above; both reached RECLASSIFY — this
  is the multi-tranche overlap recorded in
  `/plans/active/issues/sharded_per_tranche_audit_stash_race_and_multitranche_marker_gap_2026_07_30.md`.)
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
