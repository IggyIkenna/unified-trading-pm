---
doc_type: issue
title: >-
  HYPERLIQUID still appears in defi.venues/defi.chains distinct-values despite being fully reclassified to cefi — no doc
  explains the residual, root cause not found
summary: >-
  Operator flagged HYPERLIQUID still showing in the DEFI distinct-values panel (venues + chains, 2026-08-02
  honest-coverage-rollup) despite `/codex/02-data/defi-canonical-naming-ssot.md`'s "On-chain perp CLOBs are CeFi, NOT
  DeFi" section (codified 2026-06-25) confirming HYPERLIQUID/ASTER/EXTENDED/LIGHTER are fully reclassified to
  `asset_group=cefi` in the live UAC registry (`VENUES_BY_ASSET_GROUP["cefi"]`; `VENUES_BY_ASSET_GROUP["defi"]` no
  longer contains HYPERLIQUID at all — verified 2026-08-04 by direct code read,
  `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:403,461`). This doc corrects a stale
  citation trail: `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` and the 2026-08-03 cross-tranche census both
  attribute HYPERLIQUID's residual presence to `defi_venue_phase_live_definition_contradiction_2026_07_22.md`, but that
  doc — read in full 2026-08-04 — contains ZERO mentions of HYPERLIQUID; its actual scope is 11 unrelated venues wrongly
  excluded by a `phase=="pipeline"` filter, a mechanism that does not apply to HYPERLIQUID (which was moved OUT of the
  defi venue universe entirely, not merely phase-gated). The genuine reclassification SSOT
  (`instruments_foundation_completeness_2026_06_24.md`) also does not name HYPERLIQUID specifically — its cited
  1,802-row contaminant purge names EXTENDED/PACIFICA/LIGHTER only. No doc explains why `asset_group=defi` manifest rows
  with `venue`/`chain=HYPERLIQUID` still exist. Plausibly benign pre-reclassification historical residue (same shape as
  the already-tracked `gas_fees` legacy-venue-prefix cleanup), but that is inference, not a confirmed root cause — filed
  to close the gap rather than leave it as an uncited assumption.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, cefi, hyperliquid, venue-reclassification, distinct-values, manifest, data-correctness, honest-coverage]
related:
  [
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-04"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
source: >-
  Operator (interactive session 2026-08-04), cross-checking distinct_values non-canonical audit citations while
  investigating defi_cefi_venue_chain_axis_contamination_2026_07_28.md under /autonomous dispatch
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
    /codex/02-data/defi-canonical-naming-ssot.md,
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
  ]
---

# HYPERLIQUID residual `asset_group=defi` manifest rows — root cause not found (2026-08-04)

## What I found

The registry is unambiguous today (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`):

- Line 403: `VENUES_BY_ASSET_GROUP["cefi"]` includes `HYPERLIQUID` (comment: "On-chain CLOBs (reclassified from DEFI —
  CLOB-style data like CeFi)").
- Line 461:
  `VENUES_BY_ASSET_GROUP["defi"] = list(dict.fromkeys(v for v in _ALL_DEFI_VENUES if _DEFI_VENUE_PHASE.get(v) == "live"))`
  — `HYPERLIQUID` is not a member of `_ALL_DEFI_VENUES` at all, so it can never appear here regardless of phase.

Despite this, HYPERLIQUID appears in the live DEFI distinct-values panel's non-canonical `venues` AND `chains` lists
(2026-08-02 honest-coverage-rollup). This means historical `asset_group=defi` manifest rows with `venue=HYPERLIQUID`
(and/or `chain=HYPERLIQUID`) still exist in the DeFi bucket's manifest index.

**The citation trail pointing at a root cause does not hold up.** Two prior docs attribute this to
`defi_venue_phase_live_definition_contradiction_2026_07_22.md` (most recently the 2026-08-03 cross-tranche census table
and `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s original "2 already-known/tracked: BLAZESTAKE,
HYPERLIQUID — `phase=="pipeline"` grain exceptions" line). Read in full 2026-08-04: that doc's actual scope is 11 venues
(ANKR/FRAX/MAKER/STADER/STAKEWISE/SWELL/MANTLE/ACROSS/STARGATE/FLASHBOTS/ALCHEMY) wrongly excluded from the coverage
denominator by a `phase=="pipeline"` filter bug — a mechanism about EXPECTED-COVERAGE DENOMINATOR calculation, unrelated
to HYPERLIQUID's asset_group reclassification. **Zero occurrences of the string "HYPERLIQUID" anywhere in that
document.** The grouping in the census table appears to be a loose "both are DeFi-perp-adjacent oddities" association,
not a substantiated shared root cause.

The genuine reclassification SSOT — `/codex/02-data/defi-canonical-naming-ssot.md` "On-chain perp CLOBs are CeFi, NOT
DeFi" (codified 2026-06-25) — cites `plans/active/instruments_foundation_completeness_2026_06_24.md`'s purge of 1,802
contaminant `_index` rows from the instruments-service capture path (`engine/orchestrator/defi.py`
`_SOLANA_DEFI_VENUES`/`_L2_DEX_PERP_VENUES` had wrongly enumerated some cefi on-chain-CLOB venues as defi). That purge
explicitly names **EXTENDED/PACIFICA/LIGHTER** — not HYPERLIQUID.

## What this is NOT (ruled out)

- Not a live-writer bug: no current code path stamps `asset_group=defi` for HYPERLIQUID (it's absent from
  `_ALL_DEFI_VENUES`).
- Not the `phase=="pipeline"` mechanism (that's a denominator/expected-coverage bug, not a venue-universe-membership
  bug).

## Working hypothesis (not verified — the actual todo)

Most likely: pre-2026-06-25 historical manifest rows from when HYPERLIQUID WAS still defi-classified (before the
CLOB-reclassification), never cleaned up after the reclassification shipped — the same "real historical data, correct at
capture time, now correctly excluded from the current canonical venue universe but still resident in the manifest" shape
as the already-tracked `gas_fees` legacy-venue-prefix migration
(`/plans/archive/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md`). Not independently confirmed —
this doc stops at "the citation is wrong" and flags the real investigation as unstarted.

## Todos

- [ ] [DIAG] P3. Bounded manifest read (single `read_availability_index` call, column-projected, filtered to
      `venue=="HYPERLIQUID"` or `chain=="HYPERLIQUID"` within `asset_group=defi`) — get exact row count, `day=` range,
      `data_type=`/`pipeline_mode=` distribution. Confirm/refute the "pre-2026-06-25 historical residue" hypothesis
      above by checking whether the `day=` range for these rows predates 2026-06-25 (the reclassification date).
- [ ] [DIAG] P3. If historical residue confirmed: is there a canonical cefi-asset_group twin already covering the same
      (venue, day, data_type) cells (per Part 1/2 of the five-part delete-safety proof), such that this is a genuine
      cross-AG duplicate needing a cefi-bucket twin check — analogous to, but NOT the same objects as, the already-found
      `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` Pattern B contamination (that one was a `-FUTURES`
      splitter bug affecting different venues/dates; this is a plain reclassification residue, different mechanism)?
- [ ] [DATA] P3. If confirmed safe (Part 1-5 all pass, including a live-reader check mirroring the one that overturned
      `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s P2(b) assumption — HYPERLIQUID funding data IS
      genuinely read by `CanonicalPerpFundingProvider` per that same doc, so verify whether these SPECIFIC residual
      defi-tagged rows are the reader's only source or whether a cefi-tagged twin already serves the same data):
      migrate/re-tag or delete per whichever disposition the five-part proof yields. Do not assume "safe" — this exact
      class of assumption was just proven wrong for a sibling finding in this same investigation.

## Progress Log

- **interactive session 2026-08-04 (autonomous, `/autonomous`)**: filed this doc after confirming the existing citation
  trail doesn't hold up, per the pre-task plan/issue conflict-check + "0 hits ≠ missing, grep-then-READ" rules. Root
  cause investigation not started (P3, correctly scoped as DIAG-first — no execution without evidence, per the
  P2(b)-reversal lesson from the sibling doc this session).
