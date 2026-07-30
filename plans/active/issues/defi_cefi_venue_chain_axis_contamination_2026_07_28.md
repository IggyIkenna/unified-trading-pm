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

- [x] ✅ [DIAG] P1. Trace which writer/consolidator path produces the 9 chain-shaped and 5 cefi-exchange-shaped values on
      `defi.venues` — sample a handful of the actual manifest rows (venue, chain, source, pipeline_mode columns
      together) to distinguish "writer defaults venue to chain when unresolved" from "cross-AG bleed". Source: this doc.
      — market-tick-data-service@fed5cd97 + see "ROOT-CAUSE TRACE (2026-07-30)" in Progress Log below: the two
      classes are DIFFERENT bugs — 9 chain-shaped venues = confirmed writer mis-stamp; 5 cefi-exchange venues =
      confirmed cross-AG bleed (single ~27ms write burst of genuine cefi rows into the defi bucket's index).
- [ ] [DIAG] P1. Trace which writer stamps `chain="FUTURES"` for defi + cefi rows — sample the actual rows (venue,
      instrument_type, data_type alongside chain) to determine if this is the bundle-grain `futures_chain`/`FUTURES`
      instrument_type leaking into the chain column, or an unrelated mis-stamp. Check whether this is a NEW regression
      of the resolved TOCTOU consolidator bug (re-run the `cross_ag_prediction_rows_bleed` doc's own diagnostic query
      against defi/cefi) before assuming a new mechanism. Source: this doc.
- [ ] [DATA] P2. Once root-caused, fix the writer (if writer bug) or the consolidator (if TOCTOU regression) and
      re-stamp affected historical rows per the paired writer-fix + re-stamp pattern already used for the cefi
      venue-as-chain fix on this same plan. Source: this doc.

## Progress Log

- **ROOT-CAUSE TRACE (2026-07-30, worker slot-11, market-tick-data-service@fed5cd97)**: ran a single-walk sampling
  script (`market-tick-data-service/scripts/audit_defi_cefi_venue_chain_contamination_2026_07_30.py`) against the LIVE
  prod defi (29,082,549 rows) and cefi (9,488,864 rows) availability manifests — one slim `read_availability_index()`
  call per bucket (columns=`venue,chain,source,pipeline_mode,written_at,instrument_type,data_type`), no fresh GCS
  corpus walk. Findings resolve todo-1 and materially advance todo-2:

  **defi.venues, 9 chain-shaped values (ARBITRUM/AURORA/AVALANCHE/BASE/BSC/ETHEREUM/LINEA/OPTIMISM/POLYGON) — CONFIRMED
  wrong-axis writer mis-stamp (candidate class 1), NOT cross-AG bleed.** Every sampled row has `chain` IDENTICAL to
  `venue` (e.g. venue=ETHEREUM, chain=ETHEREUM), `source=onchain_rpc`, `pipeline_mode=batch_onchain_rpc` — pure DeFi
  onchain identity columns, not a cefi shape. 11,662 total rows across the 9 values (739-1,857 rows each), spread over
  a 21-hour window (2026-07-23T13:13:35Z .. 2026-07-24T10:46:21Z) — an ONGOING writer behavior across many capture
  cycles, not one-off historical residue. Root cause: a defi onchain-RPC writer sets `venue` = the chain id itself
  (conflates venue with chain) when the real DeFi protocol/venue is unresolved for these 9 chains. Next step (todo-3,
  P2): find the onchain_rpc writer path that defaults `venue` this way (analogous to the already-fixed
  `onchain_perp_batch_handler.py` venue-as-chain bug, `mtds@accd8aa4`, but that fix was for the CHAIN column on cefi
  rows — this is a DIFFERENT bug: the VENUE column on defi rows) and re-stamp the 11,662 affected rows.

  **defi.venues, 5 cefi-exchange-shaped values (BITFINEX/BITGET/BYBIT/KRAKEN/OKX) — CONFIRMED cross-AG bleed (candidate
  class 2), matching the resolved `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` shape.**
  Exactly 7 rows per venue (35 total) landed in the DEFI bucket's canonical index in a single ~27ms write burst
  (2026-07-24T20:06:38.622716Z .. .649777Z) carrying pure-CEFI identity columns: `chain=FUTURES`, `source=tardis`,
  `pipeline_mode=batch_tardis`, `instrument_type=perpetual`, `data_type=perp_daily_ctx` — Tardis is the CEFI market-data
  vendor (per `/codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap), never a defi source. **BINANCE (also 7
  rows, same microsecond batch, same columns) bled in alongside the 5 flagged values but wasn't in the original
  census's non-canonical list** — worth a follow-up on why the census didn't flag it (possibly a
  `CEFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES` fold quirk masking it in the defi context). This is a genuine, discrete
  cross-bucket leak event — one write, one moment — not gradual/ongoing contamination, consistent with a consolidator
  TOCTOU-class race rather than a per-row writer bug. NOT YET confirmed whether this is a live regression of the
  `unified-trading-library@14301571` fix or residue from before it (the fix shipped 2026-07-24, and this batch is
  timestamped 2026-07-24T20:06:38 — SAME DAY as the fix; needs the Cloud Logging correlation the resolved doc's method
  #4 describes, not done here — time-bounded to this todo's sampling scope).

  **defi.chains "FUTURES" (todo-2 supporting evidence) — SUBSUMED by the cross-AG bleed above, not a separate bug.**
  The 42 defi rows carrying `chain=="FUTURES"` are the EXACT SAME 2026-07-24T20:06:38 batch as the 6 bled cefi venues
  (BINANCE + the 5 flagged exchanges, 7 rows each = 42) — same source/pipeline_mode/instrument_type/data_type. Once the
  cross-AG bleed is fixed/re-stamped, this defi.chains entry resolves as a side effect — no separate defi-side fix
  needed.

  **cefi.chains "FUTURES" (todo-2 supporting evidence) — a SEPARATE, still-live cefi writer defect, NOT the bled rows
  and NOT the already-resolved `onchain_perp_batch_handler.py` fix.** cefi's OWN bucket independently carries 8
  genuinely-native rows: `venue=BITFINEX-FUTURES`, `chain=FUTURES`, `instrument_type=PERPETUAL` (uppercase — cefi's own
  casing convention, per the C2a instrument_type casing ruling), `data_type=trades`/`liquidations`, `source=tardis`,
  `pipeline_mode=batch_tardis`, written 2026-07-27T18:07:13Z..18:16:57Z — a DIFFERENT date than the bleed batch, so
  these are cefi's own writes, not leaked-in defi rows. Root cause not yet found: some cefi/Tardis-futures ingestion
  path is stamping a market-segment-shaped string ("FUTURES") into the `chain` column even though cefi has no chain
  axis (RESULT 3, 2026-07-20). Todo-2's remaining work: find that writer (likely in the cefi Tardis-futures capture
  path handling `BITFINEX-FUTURES`-style venue tokens) — NOT done in this pass (out of todo-1's scope; flagging for the
  next worker on todo-2).

  Script: `market-tick-data-service/scripts/audit_defi_cefi_venue_chain_contamination_2026_07_30.py` (kept per the
  script-homes lifecycle marker until this doc resolves + todo-3's re-stamp ships).

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
