---
doc_type: issue
title: B21 defi venues — 5 genuinely unregistered perp-DEX / product venues need phase-classification (ASTER, EXTENDED, HYPERLIQUID, KAMINO_LENDING, LIGHTER)
summary: >-
  Follow-up from b21_distinct_values_noncanonical_live_2026_08_18.md item 1's root-cause: of the 34 flagged defi
  non-canonical venue entries, 5 are genuinely NOT in ALL_DEFI_VENUES or LEGACY_DEFI_VENUE_ALIASES at all (unlike the
  other 29, which were a comparison-logic bug or known aliases, both fixed in unified-api-contracts@1c14d7aafc /
  deployment-api's _distinct_values.py same session). These 5 need real registry-phase judgment calls (live vs
  pipeline; correct full venue name) that a mechanical fix would risk getting wrong, per the D1b/CHAINLINK-* precedent
  this same file's docstring already warns about.
created: 2026-08-19
author: data_engineering (slot 33)
assigned_vm: planning
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, market-data-processing-service]
scope: [engineer]
parent_epic: security_and_cross_cutting_master
priority: P2
tags: [b21, distinct-values, canonical-drift, defi, perp-dex]
related:
  [
    /plans/active/issues/b21_distinct_values_noncanonical_live_2026_08_18.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md,
    /plans/active/data_pipeline_completion_2026_08_21.md,
  ]
locked_by:
resolved_by:
source: >-
  b21_distinct_values_noncanonical_live_2026_08_18.md item 1 ("Root-cause the 34 defi non-canonical venue entries")
  — the residual 5/34 this session's programmatic classification could not safely resolve mechanically.
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/issues/b21_distinct_values_noncanonical_live_2026_08_18.md,
    /plans/active/data_pipeline_completion_2026_08_21.md,
    unified-api-contracts/unified_api_contracts/registry/defi_venues.py,
    unified-api-contracts/unified_api_contracts/registry/perp_funding_cadence.py,
  ]
---

# B21 defi venues — 5 genuinely unregistered perp-DEX / product venues

## What I found

Root-causing the 34 flagged defi `venues`-axis entries (b21 item 1) via a programmatic classification against the
live UAC registry (`ALL_DEFI_VENUES`, `LEGACY_DEFI_VENUE_ALIASES`, `MAINNET_CHAIN_IDS`) found 3 distinct classes:

1. **26/34 — comparison-logic bug**: the raw manifest value is a LITERAL, EXACT member of `ALL_DEFI_VENUES` in its
   full composite `PROTOCOL-CHAIN` form (e.g. `BALANCER-ARBITRUM`, `UNISWAP_V3-ETHEREUM`, `KAMINO-SOLANA`,
   `SOLEND-SOLANA`), but `_comparison_set`'s `_defi_bare_venue_bases` only compared against the STRIPPED bare-base
   form, discarding the valid literal-composite match. **Fixed** — `_comparison_set` now compares against the union
   of bare bases and the full `ALL_DEFI_VENUES` set (`deployment-api@<see this session's commit>`).
2. **2/34 — known aliases**: `AAVEV3` / `BLAZESTAKE` are `LEGACY_DEFI_VENUE_ALIASES` keys already folded by
   `normalize_defi_venue`, just never consulted by this panel. **Fixed** — added
   `DEFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES` (`unified-api-contracts@1c14d7aafc`), wired into
   `_ACCEPTED_EXCEPTIONS[("venues", "defi")]`.
3. **1/34 — dead residue**: `GMX` was removed from `ALL_DEFI_VENUES` 2026-07-25 (operator ruling,
   `defi_gmx_venue_removal_2026_07_25.md`, unreliable historical funding data); repo-wide grep confirms zero live
   MTDS/instruments-service adapter code stamps it any more — pure historical manifest residue. **Fixed** — added
   `DEFI_VENUE_ACCEPTED_DEAD_RESIDUE` (same UAC commit), wired into the same `_ACCEPTED_EXCEPTIONS` entry.
4. **5/34 — genuinely unregistered, THIS ISSUE's scope**: `ASTER`, `EXTENDED`, `HYPERLIQUID`, `KAMINO_LENDING`,
   `LIGHTER` are not in `ALL_DEFI_VENUES` or `LEGACY_DEFI_VENUE_ALIASES` in any form (bare or composite). Per-value
   evidence (repo-wide grep, `unified-api-contracts` registry files):

   - **HYPERLIQUID / ASTER**: real, live DEX-perp venues — registered as BARE names (no chain suffix) across several
     UAC registries used for capability/adapter/endpoint purposes (`venue_constants.py`, `cefi_perp_venue_endpoints.py`,
     `data_type_capability.py` has explicit `venue="HYPERLIQUID"`/`"ASTER"` DeFi capability entries,
     `venue_instrument_config.py`, `venue_mapping.py`, `expected_coverage.py`, `data_availability.py`) but were
     **never added to `ALL_DEFI_VENUES`** (`DEFI_PERP_VENUES` — the dedicated defi-perp list — is currently an EMPTY
     `list[str] = []`, per a comment explaining GMX/DRIFT were both removed from it and nothing replaced them). This
     looks like a genuine registration gap, not a naming-drift issue — real captured data, unregistered venue.
   - **EXTENDED**: `market-tick-data-service`... `perp_funding_cadence.py`'s module docstring states, with cited
     live-verification evidence (2026-07-28), that this venue's canonical `venue` value is **ALWAYS** the compound
     `"EXTENDED-STARKNET"` string — "never a bare `EXTENDED` anywhere in the codebase" — because `-STARKNET` is a
     CHAIN suffix (parallel to `LIGHTER-ZKSYNC`), not an instrument-type suffix that gets stripped. The b21 rollup
     (source_date=2026-08-18, i.e. NEWER than that 2026-07-28 claim) shows a bare `"EXTENDED"` value in the live defi
     `by_venue` map — either (a) the perp_funding_cadence.py claim is stale/wrong, (b) a DIFFERENT writer path (not
     the one that doc verified) stamps a truncated form, or (c) the rollup itself has a normalization step somewhere
     that strips the chain. Needs a live trace of which writer produced this row before registering anything.
   - **LIGHTER**: same doc names `LIGHTER-ZKSYNC` as the parallel compound-venue pattern to `EXTENDED-STARKNET`, but
     unlike EXTENDED, `LIGHTER`/`LIGHTER-ZKSYNC` is not registered ANYWHERE in `ALL_DEFI_VENUES` at all (EXTENDED at
     least has the cadence-registry entry). Same open question as EXTENDED: is the true canonical form
     `LIGHTER-ZKSYNC`, and does the writer actually stamp that or a bare `LIGHTER`?
   - **KAMINO_LENDING**: distinct from the already-registered `KAMINO-SOLANA` (Kamino's vault product). Kamino is a
     multi-product protocol (Vaults / Lend / Multiply) — this could be a genuinely separate product needing its own
     `KAMINO_LENDING-SOLANA` registration, or a writer-side naming variant of the same protocol. Not yet traced to a
     specific adapter/writer.

## Why it matters

B21 (`data_pipeline_completion_2026_08_21.md`, Friday 2026-08-21 gate) needs the defi `venues` axis at zero
non-canonical entries. This issue's 5 residual values need the SAME phase-classification discipline the
`_comparison_set` docstring already documents as a live incident precedent: a premature `live`-phase registration
flip on `CHAINLINK-*` broke the LDR→main promotion gate 2026-07-20 because it asserted IS-producibility that wasn't
actually there (`uac@83f17c46` reverted it). Registering these 5 without confirming adapter/IS-producibility for
each risks the same regression — hence filed separately rather than folded into the mechanical fix that resolved
the other 29/34.

## Recommended decision

Per-value, in priority order:

- [ ] [DATA] P2. **HYPERLIQUID / ASTER — add to `ALL_DEFI_VENUES`** (repo: unified-api-contracts,
      `unified_api_contracts/registry/defi_venues.py`). Confirm phase (`live` if an IS/MTDS adapter genuinely
      produces the captured rows behind the b21 finding — the `perp-funding-{pid}` bucket table in
      `/codex/02-data/availability-manifest-and-data-status.md` already lists HYPERLIQUID/ASTER as observed DEX-perp
      venues there, suggesting real capture exists; `pipeline` if not yet IS-producible). Done-when: both registered
      with the correct phase, `DEFI_PERP_VENUES` updated to match, and this pair drops off the b21 defi venues count.
- [ ] [DATA] P2. **EXTENDED — trace the writer stamping bare `"EXTENDED"`** (repo: market-tick-data-service /
      instruments-service, whichever adapter/`record_captured*` call feeds the `perp-funding` bucket for this
      venue). Confirm whether the real writer stamps `"EXTENDED-STARKNET"` (per `perp_funding_cadence.py`'s
      documented invariant — in which case the b21 rollup's bare form is itself a bug elsewhere, e.g. a stale
      pre-2026-07-28 manifest row, and this is dead residue not a registration gap) or genuinely stamps bare
      `"EXTENDED"` (in which case `perp_funding_cadence.py`'s docstring claim is now stale and needs correcting, AND
      `ALL_DEFI_VENUES`/`DEFI_PERP_VENUES` needs the real canonical form registered). Done-when: root cause
      confirmed and either the writer/doc is fixed or the registry gains the correct entry.
- [ ] [DATA] P2. **LIGHTER — confirm true canonical venue form + register** (repo: unified-api-contracts +
      whichever writer produces LIGHTER rows). Determine whether the real writer stamps bare `LIGHTER` or the
      documented parallel form `LIGHTER-ZKSYNC`; register `ALL_DEFI_VENUES`/`DEFI_PERP_VENUES` accordingly (mirrors
      the EXTENDED-STARKNET precedent — chain suffix, not instrument-type suffix). Done-when: registered with the
      confirmed correct form + phase.
- [ ] [DATA] P3. **KAMINO_LENDING — confirm product identity + register or fold** (repo: unified-api-contracts).
      Trace which adapter/data_type stamps `venue="KAMINO_LENDING"` and confirm whether it is a genuinely distinct
      Kamino product (needs its own `KAMINO_LENDING-SOLANA` registration) or a writer-side naming variant of the
      already-registered `KAMINO-SOLANA` (needs a `LEGACY_DEFI_VENUE_ALIASES` fold entry instead). Done-when:
      classified and either registered or folded.

## Progress Log

- **2026-08-19 (filed — slot-33)**: Filed as the residual scope of `b21_distinct_values_noncanonical_live_2026_08_18.md`
  item 1 after fixing the other 29/34 values mechanically this same session (comparison-logic fix + 2 accepted-
  exception registries). These 5 need real registry-phase/writer-trace judgment calls, out of the parent item's
  read-only-audit-safe scope.
- **context-scout 2026-08-20**: populated context_scope (5 entries)
