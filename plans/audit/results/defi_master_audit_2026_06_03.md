---
type: audit-result
title: DeFi Master — Audit Result 2026-06-03 (acquisition-mechanics pass)
epic: defi_master
auditor: harsh + claude (opus-4-8, 1M)
date: 2026-06-03
status: complete
instructions_ref: plans/audit/instructions/defi_master_audit_instructions.md
also_covers:
  - plans/audit/instructions/instruments_master_audit_instructions.md
  - plans/audit/instructions/mtds_mdps_master_audit_instructions.md (item k — new)
  - plans/audit/instructions/batch_live_symmetry_master_audit_instructions.md (item k — new)
  - plans/audit/instructions/strategy_master_audit_instructions.md
dimension: acquisition-mechanics + batch/live wiring + downstream propagation (CODE-VERIFIED)
not_covered: data-state corpus coverage (defi items o–z, CF-1…12) — requires prod GCS/manifest reads; separate run
---

# DeFi Master — Audit Result 2026-06-03 (acquisition-mechanics pass)

## Scope of THIS run

Operator framing (Harsh, 2026-06-03): _"how are we grabbing instruments + market tick data for DeFi/CeFi venues — which
APIs and methods, batch and live — and how it flows into MDPS + strategy."_ This is the **acquisition-mechanics +
batch/live + downstream-wiring** dimension, code-verified end-to-end (instruments-service → MTDS → MDPS →
features-onchain → strategy) on `live-defi-rollout`. It does **NOT** cover the data-state corpus-coverage dimension
(defi items o–z / CF-1…12) — those need prod GCS/manifest reads and are a separate pass.

Motivated the two new everlasting audit items shipped this run (PM@a2baf04ed, push held on benign alignment gate):
`mtds_mdps_master` (k) per-venue acquisition-method registry, `batch_live_symmetry` (k) different-source equivalence.

## Adversarial verification (2026-06-03) — findings reclassified

After this report, an independent adversarial-refutation pass re-checked every gap item against caller chains, config,
registries, and codex. The fix plan `plans/active/data_pipeline_acquisition_remediation_2026_06_03.md` acts ONLY on the
survivors:

- **CONFIRMED (fix-now)**: `dex_swaps` 5k/day truncation (P0/P1); orca/raydium no live WS (P1).
- **PARTIAL (narrower than stated)**: hardcoded hosts (P2 — QG does NOT flag them; 3 bare literals, varying severity);
  DeFi live `--trigger` stub (P2 — unwired forward-flag; live works via `--mode live`, not a breakage).
- **REFUTED (out of scope — do NOT action)**: `(DEFI,liquidations)` no-adapter (name conflation — DeFi venues declare
  `liquidation_events`, skip unreachable); `dex_swaps` generic bucket (codex-intended home, not a defect);
  `mid_price_<venue>` "missing" (runtime widening seam, archetype not blocked); `funding_rate_apy_bps` 0-producer
  (FACTUALLY WRONG — produced by 2 calculators); `usdc_idle_yield_apy_bps` (reporting-only, not in `net_carry` — not a
  correctness bug).

## Method

Four code-verified sub-agent passes (3a instruments, 3b MTDS tick, 3c MDPS+features-onchain, 3d strategy), each
returning real `file:line` evidence; key findings independently spot-verified by the auditor (no fabricated refs).

## Verdict by stage

| Stage                                   | Verdict       | Headline                                                                                                             |
| --------------------------------------- | ------------- | -------------------------------------------------------------------------------------------------------------------- |
| 3a instruments-service DeFi acquisition | **GREEN-ish** | Acquisition aligned; fetch-failure routing honest; subgraph IDs from UAC. Live `--trigger` dispatcher stubbed.       |
| 3b MTDS DeFi tick acquisition           | **AMBER**     | Sound methods + dedicated buckets, but `dex_swaps` 5k/day truncation, orca/raydium no live WS, 3 hardcoded hosts.    |
| 3c MDPS bypass + features-onchain       | **AMBER**     | Bypass-scope matches codex; batch=live compute shared; `(defi,liquidations)` no-adapter silent-skip.                 |
| 3d strategy archetype consumption       | **AMBER**     | No batch=live signal-branch violation; but `usdc_idle_yield_apy_bps` 0-producer + `mid_price_*` producer unverified. |

## Checklist results (items exercised this run)

- **instruments (a,b,c,e) — IS→MTDS contract**: GREEN — handlers read IS catalogue before fetch
  (`_instruments_metadata.py`); archive venues use `source_archive_url_template`, others use UAC registry
  (`get_solana_protocol_url`/`SUBGRAPH_IDS`). Per IS→MTDS codex contract, `source_record_types`/`coverage` being
  Drift-family-mostly is **by design** (archive-replay venues only), not a hole.
- **instruments (h) / mtds (i) — fetch-failure swallow**: GREEN (audited venues) — raise → `VenueError` →
  `record_failed`; no swallow-to-empty found in uniswap*v3/curve/jito/marinade/lido top-levels. \_Not exhaustive across
  all 52 adapters.*
- **defi (j/k) — data_type names canonical**: GREEN —
  `dex_pool_swaps`/`dex_pool_state`/`lending_indices`/`perp_funding`/ `lst_rates`/`oracle_prices`/`vault_share_price`;
  no legacy `swap_events`/`funding_rates`.
- **defi (l) — dedicated buckets**: AMBER — lst/lending/oracle/perp/dex-pools write dedicated buckets; **`dex_swaps`
  writes generic `market-data-tick-defi`** (`dex_swaps_handler.py:370`) — inconsistent.
- **defi (h) — removed providers**: GREEN — bloxroute removed (`mev_events_handler.py:40-41`).
- **mtds (k, NEW) — per-venue acquisition-method registry**: AMBER — see registry in 3b; `dex_swaps` pagination gap + 3
  hardcoded hosts are the misses.
- **batch_live (k, NEW) — different-source equivalence**: AMBER — Solana DEX batch(RPC/S3)-vs-live(WS) + curve/jito
  subgraph/RPC-vs-poll are by-design; **orca/raydium batch-only (no live WS) is an undocumented divergence**; morpho
  batch-skip is documented (accepted).
- **strategy (f) — batch=live code-path identity**: GREEN — no `if mode=="live"` in signal logic; `_pnl_mode` branches
  tag PnL metadata only.

## Gap items (ready to wire into active plans — dedup against `plans/active/` + `issues/` first)

- [ ] [DATA-CORRECTNESS] P1. MTDS `dex_swaps` silently truncates at 5,000 swaps/day/pool (`for page in range(5)`,
      `market-tick-data-service/.../cli/handlers/dex_swaps_handler.py:569`) — high-volume pools lose trades with no
      `record_failed`/warning; biases the `arbitrage_price_dispersion` DEX leg. Fix = full pagination (skip-loop until
      `len(df)<1000`) or explicit cap + honest-absence flag. — parent_epic: mtds_mdps_master
- [ ] [BATCH-LIVE] P1. Orca + Raydium have batch acquisition but **no live WebSocket connector** in
      `market-tick-data-service/.../live/connectors/` — `arbitrage_price_dispersion` has no live DEX ticks for them.
      Either add live connectors or record an accepted-divergence register entry (batch_live item k). — parent_epic:
      defi_master
- [ ] [CONTRACT] P1. Hardcoded venue hosts not UAC/IS-derived: `curve_adapter.py:118` (`api.curve.finance`),
      `_solana_defi_fetch.py:36` (`lite-api.jup.ag`, not wrapped in `get_solana_protocol_url`), `morpho_defi_ws.py:41` /
      `liquidations_handler.py:745` (`blue-api.morpho.org`). Register in UAC like the kamino/orca/raydium pattern. —
      parent_epic: mtds_mdps_master
- [ ] [STUB] P1. instruments-service DeFi live `--trigger` dispatcher absent — `--trigger` parsed→stored→logged only
      (`instruments_handler.py:145`), CLI help advertises `defi.token_lists.refresh` but `triggers/` has only the sports
      module; no dispatch. Live DeFi works via `--mode live` (HWM-guarded fresh fetch), so not broken — but the
      advertised per-asset-group trigger taxonomy is unimplemented for defi. — parent_epic: instruments_master
- [ ] [L3-GAP] P2. `usdc_idle_yield_apy_bps` consumed by `carry_staked_basis` (`staked_basis.py:292`) but produced by
      **no features service** — silently defaults to `0.0` ("wire when calculator lands"), so the idle-yield leg
      contributes nothing. Either implement the calculator (features-onchain) or document the leg as intentionally-off.
      — parent_epic: features_and_ml_master
- [ ] [L3-GAP] P2. `arbitrage_price_dispersion` consumes `mid_price_<venue>` columns (`price_dispersion.py:24`) but the
      **producing calculator was not found** — trace whether MDPS `market_state`/`fx_rates` candles are renamed to
      `mid_price_<venue>` by the GCS feature provider, or whether this feature is unimplemented (would block the
      archetype). — parent_epic: defi_master
- [ ] [CODE-BUG] P2. `(DEFI, liquidations)` is in `DATA_TYPES_BY_ASSET_GROUP['defi']` with
      `needs_candle_processing=True` but has **no MDPS adapter** (only `(CEFI, liquidations)`) → silent skip returns
      `[]` (`orchestration_service.py:631`), no honest-absence row. Either register a defi liquidations adapter or set
      `needs_candle_processing=False` for it. — parent_epic: mtds_mdps_master
- [ ] [CODE-BUG] P2. `dex_swaps` writes generic `market-data-tick-defi` bucket while peers use dedicated `dex-*-*`
      (`dex_swaps_handler.py:370`) — inconsistent with the dedicated-bucket pattern (defi item l). — parent_epic:
      defi_master
- [ ] [CLEANUP] P3. 5 orphan DeFi adapter files unreachable via the IS factory (pyth/phoenix/meteora/jupiter/lifinity in
      `instruments-service/.../reference_data/adapters/defi/`) — read body + git log before delete (delete-criteria);
      may be MTDS-side or future. — parent_epic: instruments_master
- [ ] [CODE-BUG] P3. `factory.py:357` labels curve `"rpc"` but it uses Curve REST (`curve.py:30`) — cosmetic (curve
      takes no api_key) but misleading provenance label. — parent_epic: instruments_master

## Tracked (already has named successor — note, do not re-file)

- `carry_staked_basis` hedge-leg `funding_rate_apy_bps` is onchain-DeFi (Hyperliquid/ETH-PERP) only, not the 7-venue
  CeFi perp set the coverage matrix names → tracked in `plans/active/funding_rate_apy_bps_multi_venue_2026_06.md`.

## Aligned / positive (no action)

- Fetch-failure → `attempted_failed` routing honest (audited venues); subgraph IDs from UAC `SUBGRAPH_IDS`; Drift
  Velocity API proper `meta.nextPage` pagination; bloxroute removed; canonical data*type names; dedicated per-data_type
  buckets (except dex_swaps); morpho batch-skip documented; features-onchain batch/live share the same
  `compute*\*`; strategy batch=live single code path (no signal-mode branch); MDPS bypass-scope matches codex (`needs_candle_processing()`);
  vault adapters are DefiLlama-backed (not stubs, but current-snapshot only).

## Phase-0 contradiction resolved

EVM/lending/LST/oracle batch acquisition is **handler-driven** (`cli/handlers/*`), NOT the `market_interface/factory.py`
`VENUE_REGISTRY` (which feeds IS-discovery + live-feed adapters). Solana DEXs likewise route through dedicated
handlers + Solana RPC. The two earlier high-level explorers conflated the registry with the handler layer.

## What was NOT covered (next passes)

1. **Data-state corpus coverage** (defi o–z / CF-1…12): per-venue/chain captured% with IS∩UAC denominators,
   schema-version distribution, phantom-grid reconciliation — needs prod GCS/manifest reads.
2. **Exhaustive swallow audit** across all 52 IS adapters + all MTDS handlers (this run spot-checked representatives).
3. **CeFi end-to-end** (Phase 4) — same acquisition-mechanics trace for the CeFi leg.
4. `dex_swaps` real-world >5k/day exceedance confirmation (needs a GCS row-count sample).

## Archive condition

Archives when all gap items above are `- [x]` in their parent active plans.

## Linked

Instruction file Linked Results row to add on filing: `2026-06-03 | this file | acquisition-mechanics pass (AMBER)`.
