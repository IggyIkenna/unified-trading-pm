---
title: "DeFi pipeline — code↔codex drift (audit 2026-05-27)"
created: 2026-05-27
source:
  - codex/02-data/defi-data-pipeline.md
  - codex/02-data/data-lineage-MTDS-features-ml.md
  - codex/02-data/defi-data-types-catalog.md
locked_by: live-defi-rollout
master:
  defi_manifest_canonicalisation_2026_06_01.md (DeFi vertical orchestrator — slot-2 owns; §A writers + §F docs/SSOT
  close these drift items. Asset-group slot split, 2026-06-03)
status: active
priority: P2
---

# DeFi pipeline — code ↔ codex drift (audit 2026-05-27)

## What I found

Re-read the actual Python (MTDS / MDPS / UAC / features-service) on 2026-05-27 and cross-checked GCS, comparing against
the codex SSOTs. **Comprehensive audit record (13 findings D1–D13, audit-result format):**
[`plans/audit/results/defi_pipeline_code_codex_drift_2026_05_27.md`](../../audit/results/defi_pipeline_code_codex_drift_2026_05_27.md).
In-codex summary: [`codex/02-data/defi-data-pipeline.md`](../../../codex/02-data/defi-data-pipeline.md) §1. This issue
doc is the **actionable tracker** — todos below. The first pass surfaced 5 architectural drifts (D1–D5); a broadening
pass added D6–D13 (catalog completeness, venue drift, banned `bloxroute` relay, RADIANT unbacked, infura, governance
dup).

| #   | Drift                                                                                                                                                                                                                                                     | Side         | Status                           |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | -------------------------------- |
| D1  | `defi-data-types-catalog.md` uses stale names `swap_events`/`pool_state`/`lending_metrics`/`funding_rates`; code writes `dex_swaps`/`dex_pool_state`/`lending_indices`/`perp_funding`                                                                     | codex-doc    | **actionable now**               |
| D2  | Legacy stale prefixes `lst_rates/`,`lending_indices/`,`dex_pools/` inside `market-data-tick-defi-prd` (stop 2026-04-14); canonical data is in dedicated buckets `lst-rates-*`/`lending-indices-*`/`dex-pools-*`                                           | data cleanup | **DEFERRED-UNTIL-PIPELINE-DONE** |
| D3  | `DefiLendingIndicesAdapter` exists + decorator-registered + UAC `needs_candle_processing("lending_indices")=True`, but it's **not imported** in top-level `app/adapters/__init__.py` → silently never runs. Intent is bypass (features read lending raw). | code bug     | **✅ RESOLVED 2026-05-27**       |
| D4  | features-onchain reads bypass types raw from MTDS                                                                                                                                                                                                         | —            | aligned (no action)              |
| D5  | `data-lineage` per-layer paths use legacy `{category}` bucket patterns                                                                                                                                                                                    | codex-doc    | tracked ML-14 (rewrite)          |

## Why it matters

- **D3 is the substantive one.** A lending-candle adapter is wired in two of three places (UAC gate + decorator) but
  disabled by a missing import. Today this is benign (it matches the intended bypass behaviour by accident, and features
  read `lending_indices` raw), but it is a tripwire: anyone who "fixes" the missing import would silently start
  producing unused `lending_ohlcv` candles and flip the gate's behaviour. The three sources (UAC gate, MDPS adapter
  registry, features bypass contract) must agree on ONE answer: lending_indices is bypass ⇒ gate should be `False` and
  the adapter deleted.
- **D1/D5** are documentation drift that misleads downstream consumers reading the catalog/lineage for canonical names
  and bucket patterns.
- **D2** is dead data occupying the canonical bucket; harmless but should be cleaned to avoid confusion during the
  bucket-SSOT consolidation.

## Recommended decision

- **Now (codex-doc, safe):** update [`defi-data-types-catalog.md`](../../../codex/02-data/defi-data-types-catalog.md)
  headings + instrument-type map to canonical `data_type=` names (D1). (D5 rewrite stays under the existing ML-14 item.)
- **After the running backfill completes (code):** for D3, set `needs_candle_processing("lending_indices") = False` in
  UAC `registry/market_data_categories.py`, delete the dead `DefiLendingIndicesAdapter`
  (`market-data-processing-service/.../app/adapters/defi/lending_indices_adapter.py`), and fix the misleading comment in
  `app/adapters/__init__.py`. Single code path, no shim. Re-run QG.
- **After the run (data):** for D2, delete the legacy `lst_rates/`,`lending_indices/`,`dex_pools/` prefixes under
  `market-data-tick-defi-prd` via `gcs_delete_object` once the dedicated buckets are confirmed authoritative.

## Todos

Codex-doc (safe now):

- [x] [DOC] P2. D1 — `defi-data-types-catalog.md` renamed to canonical data_type names
      (`dex_swaps`/`dex_pool_state`/`lending_indices`/`perp_funding`) + instrument-type map + staleness banner. ✅ this
      session.
- [x] [DOC] P2. D6/D12 — `defi-data-types-catalog.md` reconciled: § "Additional data types" added (~12 types:
      `lst_rates`, `vault_share_price`, `liquidations`, `risk_params`, `utilization`, `rewards`, `eigenlayer_rewards`,
      `native_staking_rates`, `aggregator_route`, `protocol_outages`, `governance_proposals`, `dex_pool_swaps`,
      `restaking_*`) + `oracle_prices` (+Pyth) / `lending_indices` (+Spark/Compound V3) / `perp_funding` sources fixed +
      dedicated-bucket note + banner resolved. ✅ this session.
- [x] [DOC] P2. D9/D11 — `defi-venue-protocol-catalogue.md` gained "Registry inconsistencies + pending venues" section
      (EULER_V2/VENUS/BENQI/RADIANT/MARGINFI/SOLEND live-without-capability; SOLAYER/PICASSO/CAMBRIAN
      capability-without-venue; HYPERLIQUID/ASTER phase mismatch). Catalogue was ~90% complete; the gaps are
      code-registry states, documented + cross-linked. ✅ this session.

Code (DEFERRED-UNTIL-PIPELINE-DONE; other agents are correcting code — re-verify current state first):

- [x] ✅ [CODE] P2. D3 — `needs_candle_processing("lending_indices")=False` (UAC@96db70a6, reverts drift 4c98a635) +
      dead `DefiLendingIndicesAdapter` deleted + `app/adapters/__init__.py` comment fixed + bypass test moved to
      `BYPASS_TYPES` (MDPS@5c2b612) + epic DeFi-V note corrected (PM@e5742c656). All three sources now agree:
      lending_indices is bypass. QG green (ruff + basedpyright + `test_defi_bypass_routing` 41/41). — 2026-05-27.
- [ ] [CODE] P2. D10 (generalized) — 6 venues `DEFI_VENUE_PHASE=live` with no `PROTOCOL_CAPABILITIES`/`SUBGRAPH_IDS`
      (EULER_V2, VENUS, BENQI, RADIANT-ETH, MARGINFI, SOLEND): add backing OR downgrade/register. Confirm intent with
      operator/Ikenna. **The 3 inverse venues (SOLAYER/PICASSO/CAMBRIAN: capability-without-venue) are RESOLVED — fully
      removed 2026-06-02 (operator decision, no usable/decodable data source); UAC capabilities + IS adapters wiped.
      SSOT: `plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md`.**
- [x] ✅ D14 — RESOLVED / REVERSED 2026-06-08. **This finding's premise is STALE — canonical is `dex_pool_state`, NOT
      `dex_pools`.** The operator-locked `codex/.../defi-canonical-naming-ssot.md` (2026-06-01) reversed the direction:
      `dex_pool_state`/`dex_pool_swaps` is canonical at EVERY surface (path + column + manifest + handler const). Live
      code is consistent end-to-end — `dex_pools_handler.py` writes `dex_pool_state` to BOTH path and manifest (the
      2-layer split is retired), `migrate_defi_full_v9_canonical.py` stamps `dex_pool_state` with NO remap, features
      read `data_type=dex_pool_state`. **The walk bakes `dex_pool_state` and code reads `dex_pool_state` — matched, no
      pre-apply block.** ⚠️ Do NOT "fix" this back to `dex_pools` — the `mtds_mdps_master.md` Phase 9
      `dex_pool_state→dex_pools` rename is a SUPERSEDED dead-letter (banner added there 2026-06-08). Defi audit guard
      (`defi-dexpool-name`) pins the canonical name. (reversed per SSOT; verified end-to-end by the 2026-06-08 sweep.)
- [ ] [CODE] P3. D15 — HYPERLIQUID + ASTER are `DEFI_VENUE_PHASE=pipeline` but `perp_funding_handler` actively collects
      them; reconcile the phase label (→ live, or confirm cefi-axis classification).
- [x] ✅ [CODE] P3. D7 — **SHIPPED** MTDS@d3e02228 (`fix(mev): remove banned bloxroute relays + stale .bak from
      mev_events_handler`): the 2 bloxroute URLs are gone from `mev_events_handler.py` `MEV_BOOST_RELAYS` (Flashbots /
      agnostic / ultra_sound retained, comment cites this finding) and `mev_events_handler.py.bak` is deleted — verified
      on `origin/live-defi-rollout`. Usage audit found **nil active downstream consumption** of bloxroute/`mev_events`
      relay data (bloxroute already removed as the mempool feed; `sandwich_theoretical.py` is a theoretical-only tracer).
      — 2026-06-09.
- [ ] [CODE] P3. D8 — **EDITS APPLIED & CORRECT, BLOCKED FROM SHIPPING (2026-06-09)** — remove the Starknet
      `infura_compatible` template (`_defi_chain_data.py`, now ~line 711) + de-Infura the `gas_fee_handler.py:78` comment
      (Infura decommissioned workspace-wide 2026-05-22, execution `chain_config.yaml:14`). Both edits are made locally and
      verified safe (UAC: no consumer references the `infura_compatible` key; MTDS: comment-only). **NOT shipped — blocked
      by PRE-EXISTING repo-health issues unrelated to D8** (see ci_incident_findings_2026_06_09 Finding 5): (a) **UAC QG is
      RED on LDR tip** — `STEP 5.86` orphan cassette `fear_greed/mocks/stub.yaml` (fixed locally via allowlist), PLUS
      pre-existing `Hardcoded project ID in production` + `Backward-compat pattern` failures (intentional shims in
      `internal/modes.py` 6-call-site + `registry/chain_env.py` ghost tokens) that need a real refactor + owner judgment;
      (b) **MTDS slot is DIVERGED from LDR** — unpushed feature commit `01fda7ce` (migrator gas-fees/liquidations) + a
      rebase conflict in `tests/unit/test_collect_handler_schema.py` (foreign file). Ship once UAC QG is green on LDR +
      the MTDS slot is reconciled.
- [x] [CODE] P3. **DECIDED 2026-05-27 → KEEP** D13 — `governance_proposals` is an intentional unregistered scaffold for
      the Phase-4B simulation harness (not wired in `cli/main.py`), so it is NOT an active parallel path vs
      `governance_events`. No change; documented in the catalog § "Additional data types".
- [~] [INFRA] P3. D2 — delete legacy `lst_rates/`/`lending_indices/`/`dex_pools/` prefixes in
  `market-data-tick-defi-prd` (via `gcs_delete_object`) after dedicated buckets confirmed authoritative. `lst_rates/`
  **DONE 2026-05-28**: 1,200 date-prefix parquets deleted; 64,373 stale manifest rows pruned. `lending_indices/` +
  `dex_pools/`: deferred until Gate 2 Solana migration completes (canonical buckets must be confirmed superset first).
  Solana instrument_types added to codex — PM@(Gate 6 commit). Cited: UAC@7e9f4ad9 + UAC@90b2bb9d + MTDS@c38d1ca3 +
  MTDS@896d5c9 (Gate 5).
