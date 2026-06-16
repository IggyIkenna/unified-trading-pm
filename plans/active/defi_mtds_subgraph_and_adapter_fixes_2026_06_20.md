---
title:
  "DeFi MTDS subgraph schema rewrites + adapter fixes (DEX-swaps / Compound V3 / Hyperliquid OHLCV / Extended-Starknet)"
parent_epic: defi_master
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 3.2
locked_by: live-defi-rollout
locked_since: 2026-06-20
related_plans:
  - ../epics/defi_master.md
  - ./defi_manifest_canonicalisation_2026_06_01.md
---

> **Provenance**: extracted 2026-06-20 from the inline `defi_master` epic body (§§ "988-missing-dates audit residuals",
> "Chain coverage + CLOB-on-chain venues", "Lending-indices Bug 2") during the asset-group-umbrella restructure. The
> umbrellas carried stale May-08 inline todos the backlog regen never scanned. This plan is the genuinely net-new,
> unowned **adapter / subgraph-schema rewrite** workstream — the DEX-swaps subgraph schema-mismatch query rewrites, the
> Compound V3 Messari schema rewrite, the Hyperliquid historical-OHLCV stub, and the Extended-Starknet unblocking +
> asset_group classification decision.
>
> **Explicitly NOT in scope (owned elsewhere — do NOT duplicate, the regen would dispatch two VMs to race):**
>
> - LIGHTER `perp_funding` adapter fix (A5, root-cause diagnosed) →
>   [`defi_manifest_canonicalisation_2026_06_01.md`](./defi_manifest_canonicalisation_2026_06_01.md) A5.
> - DeFi per-chain / per-venue launch dates (`DEFI_VENUE_LAUNCH_DATES` population) → same plan (A2a / C-walk).
> - Solana LST MTDS coverage gap (jitoSOL/mSOL ~monthly granularity) → archived named successors
>   `plans/archive/issues/lst_apr_sourcing_method_validated_2026_05_14.md` +
>   `plans/archive/solana_restaking_rewards_coverage_2026_05_13.md`; the manifest coverage/source side rides
>   `defi_manifest_canonicalisation_2026_06_01.md`.
> - `source=` provenance stamping for DeFi →
>   [`data_source_provenance_all_asset_groups_2026_06_01.md`](./data_source_provenance_all_asset_groups_2026_06_01.md).

## Context

The `defi_988_missing_dates` audit found ~13.6k actionable (non-legit) missing rows; the remaining adapter-level fixes
are subgraph-schema mismatches where the protocol responds but the canonical field set isn't extractable (a 2024-indexer
field rename), plus two perp/OHLCV adapter stubs. Each fix must per-row `record_failed(SCHEMA_DRIFT)` where the response
shape deviates (never write garbage) and lock the new shape with a cassette-parity test. The DeFi single-walk +
manifest-correctness layer is the coordinator's (`defi_manifest_canonicalisation_2026_06_01`); this plan only fixes the
adapters that feed it.

## P0 — subgraph schema rewrites

- [x] [SCRIPT] P0. **DEX-swaps subgraph schema-mismatch fix.** Per-protocol: PancakeSwap V3 (BSC/Ethereum/Arbitrum),
      SushiSwap V3 (Ethereum/Polygon/Arbitrum/Optimism), Aerodrome (Base), Camelot (Arbitrum). For each: probe the
      current Messari subgraph endpoint shape; rewrite the query if the schema drifted (most likely a pool-entity field
      rename since the 2024 indexer upgrade); per-row `record_failed(SCHEMA_DRIFT)` for rows where the protocol
      responded but the canonical field set isn't extractable; cassette-parity test locks the new shape. ~1.8k
      blank-reason rows clear once the fix lands.
      — shipped mtds@90175f9 2026-06-16: `_SubgraphSchemaDriftError` + `_is_schema_drift_error()` detect
        "has no field"/"Cannot query field" GraphQL fingerprints; `_execute_subgraph_query` raises on drift; `_run_cascade`
        catches per-step (fall-through) then raises labeled `_SubgraphSchemaDriftError` if all fail → `record_failed(SCHEMA_DRIFT)`;
        `_MESSARI_LP_SWAPS_QUERY` + `_MESSARI_LP_SWAPS_FROM_QUERY` handle post-2024 `liquidityPool` field rename; cascade
        extended with `messari_lp`/`messari_lp_from` variants for all affected protocols; 10 cassette-parity tests added;
        pre-existing Kalshi/Polymarket test assertions fixed (UAC `OTHER` update); semver-agent.yml comment escaped.
- [x] [SCRIPT] P0. **Bug 2 — Messari Compound V3 subgraph query rewrite.** Probe the current schema of the Compound V3
      subgraph endpoint per chain (Ethereum, Base, others); identify the field renames since the indexer upgrade that
      the current MTDS query depends on. Rewrite the query; add per-row `record_failed(SCHEMA_DRIFT)` for any row where
      the response shape deviates from the canonical contract (so we never write garbage). Cassette-parity test locks
      the new shape. Smoke 1 day per chain post-rewrite.
      — shipped mtds@1515372 2026-06-12: `_COMPOUND_V3_FLAT_QUERY` (promoted fields, post-2024 indexer),
        null-accounting guard in `_parse_compound_v3_custom` (skip rows, not write zeros), 3-step cascade
        custom→flat→messari, `_parse_compound_v3_flat` parser, 3 cassette-parity tests.

## P0 — adapter stubs + venue unblocking

- [ ] [SCRIPT] P1. **Fix the HYPERLIQUID adapter stub** — currently raises `NotImplementedError` for
      `fetch_historical_ohlcv`. Wire it to the real Hyperliquid Info API endpoint. (Not on the critical path for the
      paper-trade cutover — the perp hedge leg uses Binance/Bybit/OKX first — but the stub is a latent gap. Issue:
      `plans/active/issues/emerging_perp_venue_adapters_broken_2026_05_13.md`.)
- [ ] [SCRIPT] P1. **Phase 5 — Extended-Starknet unblocking.** Starknet RPC template (`STARKNET_RPC_TEMPLATES` now in
      UAC `_defi_chain_data.py`) + OHLCV adapter for Extended. Two sub-paths in priority order: (1) re-read
      `docs.extended.exchange` for the documented historical endpoint (may be auth-gated); (2) failing that, build a
      Starknet event subgraph against the Extended Settlement contract (Settlement contract address/ABI research). Falls
      back to forward-poll only if both paths fail. Gated on the asset_group classification decision below.
- [ ] [HUMAN] P1. **Phase 4 — asset_group classification decision (operator) for CLOB-on-chain venues.** Lighter /
      Pacifica / Extended sit at the DeFi (on-chain settlement) vs CeFi (centralised order-book matching) boundary. Two
      options: (a) extend the DeFi asset_group to include them (current default; minor mental tension); (b) a new
      `clob_dex` asset_group (clean separation but workspace-wide vocabulary churn across UAC `VENUES_BY_ASSET_GROUP`,
      MDPS bucket layouts, deployment-ui drilldown). The source issue recommended option (b). **Decision needed before
      the Extended Phase 5 ships.** Status: **BLOCKED-OPERATOR-DECISION.**

## Success criteria

- DEX-swaps + Compound V3 subgraph queries are rewritten against the live schema; cassette-parity tests lock the shapes;
  a schema-deviating response routes to `record_failed(SCHEMA_DRIFT)`, never a garbage write; ~1.8k + ~the-Compound
  blank-reason rows clear.
- The Hyperliquid `fetch_historical_ohlcv` stub returns real bars from the Info API; the Extended OHLCV path is either
  wired or honestly recorded as forward-poll-only pending the operator classification.
- `bash scripts/quality-gates.sh` green on `market-tick-data-service` (+ `instruments-service` for any discovery-adapter
  touch) before each commit; cassette parity (`pytest tests/test_cassette_schema_parity.py`) green.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): each rewritten subgraph query is smoked
against the live endpoint for ≥1 day per chain and the rows land `captured` (or honestly `record_failed`) in the
manifest; the Hyperliquid OHLCV fetch returns real bars verified non-NaN.
