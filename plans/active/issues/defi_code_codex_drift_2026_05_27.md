---
doc_type: issue
title: DeFi pipeline — code↔codex drift (audit 2026-05-27)
summary: >-
  Actionable tracker for 13 code↔codex drifts (D1–D13) found re-reading the actual DeFi pipeline Python
  (MTDS/MDPS/UAC/features-service) against codex SSOTs — stale data-type names, legacy bucket prefixes, an unimported
  adapter, catalog gaps, banned-provider references, and more; full record in the companion audit-result doc.
status: open
nature: process
asset_group:
  [defi] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag:
  # "DeFi pipeline -- code<->codex drift" audit, parent_epic is defi_master -- content is defi-only

stage: [meta]
repos: [features-service, market-data-processing-service]
scope: [engineer, admin]
tags: [defi, data-correctness, ssot-audit, mdps, mtds, uac, canonicalisation, catalogue]
related:
  [
    plans/audit/results/defi_pipeline_code_codex_drift_2026_05_27.md,
    /codex/02-data/defi-data-pipeline.md,
    /codex/02-data/defi-data-types-catalog.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md,
  ]
created: 2026-05-27
author: unknown
parent_epic: defi_master
priority: P2
source:
  [
    /codex/02-data/defi-data-pipeline.md,
    /codex/02-data/data-lineage-MTDS-features-ml.md,
    /codex/02-data/defi-data-types-catalog.md,
  ]
assigned_vm: planning
resolved_by:
archive_exempt: true # BRIDGE 2026-08-12: clearing the stale locked_by:live-defi-rollout placeholder (operator ruling, option B, see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md) immediately surfaces this doc as 0-open-todos archive-eligible. Per that ruling's explicit scope ("do NOT auto-archive in this same pass"), archival is deferred to a separate follow-on pass. Bridged via the sanctioned flip-then-mv two-commit pattern documented in scripts/plan-hygiene/check_archive_candidates.sh -- drop this line + git mv to plans/archive/[issues/] in that follow-on pass.
locked_by:
master:
  defi_manifest_canonicalisation_2026_06_01.md (DeFi vertical orchestrator — slot-2 owns; §A writers + §F docs/SSOT
  close these drift items. Asset-group slot split, 2026-06-03)
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/audit/results/defi_pipeline_code_codex_drift_2026_05_27.md,
    /plans/archive/2026_08/hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
last_updated:
  '2026-07-10 (was: 2026-06-27 — verify-rerun-2 finding 50, corrected 2026-07-14 — body''s D10 todo documents "RESOLVED
  2026-07-10 (operator decision #9...)"; frontmatter never bumped)'
---

# DeFi pipeline — code ↔ codex drift (audit 2026-05-27)

## What I found

Re-read the actual Python (MTDS / MDPS / UAC / features-service) on 2026-05-27 and cross-checked GCS, comparing against
the codex SSOTs. **Comprehensive audit record (13 findings D1–D13, audit-result format):**
[`plans/audit/results/defi_pipeline_code_codex_drift_2026_05_27.md`](../../audit/results/defi_pipeline_code_codex_drift_2026_05_27.md).
In-codex summary: [`/codex/02-data/defi-data-pipeline.md`](/codex/02-data/defi-data-pipeline.md) §1. This issue doc is
the **actionable tracker** — todos below. The first pass surfaced 5 architectural drifts (D1–D5); a broadening pass
added D6–D13 (catalog completeness, venue drift, banned `bloxroute` relay, RADIANT unbacked, infura, governance dup).

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

- **Now (codex-doc, safe):** update [`defi-data-types-catalog.md`](/codex/02-data/defi-data-types-catalog.md) headings +
  instrument-type map to canonical `data_type=` names (D1). (D5 rewrite stays under the existing ML-14 item.)
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
- [x] ✅ [CODE] P2. D10 (generalized) — **RESOLVED 2026-07-10 (operator decision #9: "add the missing
      capability-registry entries, don't downgrade").** The original "no PROTOCOL_CAPABILITIES/SUBGRAPH_IDS" premise
      (filed 2026-05-27) was already stale — `unified-api-contracts@cd65ff76` (2026-06-02) had already registered real
      `PROTOCOL_CAPABILITIES`/`SUBGRAPH_IDS` for EULER_V2/VENUS/BENQI/RADIANT, and MARGINFI/SOLEND already had real
      capability entries + real captured production data (verified against the prod availability manifest). The
      GENUINELY missing registry was a third one, `DEFI_VENUE_DATA_TYPE_CAPABILITIES`
      (`unified_api_contracts/registry/defi_venue_capabilities.py` — the honest-coverage denominator's actual
      per-(venue,data_type) capability gate) — added entries for RADIANT-ETHEREUM/EULER_V2-ETHEREUM/EULER_V2-ARBITRUM/
      VENUS-BSC/VENUS-ETHEREUM/BENQI-AVALANCHE (real `PROTOCOL_LAUNCH_DATES`-sourced start dates, minimal real capture
      surface). `DEFI_VENUE_PHASE` deliberately left `pipeline` for these 4 EVM protocols (NOT flipped to `live`) — the
      prod manifest shows ZERO real captured rows for ANY of them, ever, and a live network probe found the EULER_V2
      Goldsky subgraph ~38 days stale; the real root cause is an already-tracked orchestrator-wiring gap
      (`mtds_is_full_adapter_smoketest_findings_2026_07_07.md` P1), not a registry gap — flipping phase now would
      recreate the phantom-capacity dishonest-coverage class the data-pipeline-correctness HARD RULE bans. Shipped
      `unified-api-contracts@f0032d171b89ff38aafcea0d9d28882ccca2b991`
      (`fix(defi,cefi): D10 defi lending capability     entries + DERIBIT-COMBO test coverage`, 2026-07-10, confirmed on
      origin/live-defi-rollout; corrects the earlier `5626079e` citation, which does not resolve to a real commit —
      likely a mistyped/stale short sha). Full evidence trail in this doc's Progress Log. **The 3 inverse venues
      (SOLAYER/PICASSO/CAMBRIAN: capability-without-venue) are RESOLVED — fully removed 2026-06-02 (operator decision,
      no usable/decodable data source); UAC capabilities + IS adapters wiped. SSOT:
      `plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md`.**
- [x] ✅ D14 — RESOLVED / REVERSED 2026-06-08. **This finding's premise is STALE — canonical is `dex_pool_state`, NOT
      `dex_pools`.** The operator-locked `/codex/02-data/defi-canonical-naming-ssot.md` (2026-06-01) reversed the
      direction: `dex_pool_state`/`dex_pool_swaps` is canonical at EVERY surface (path + column + manifest + handler
      const). Live code is consistent end-to-end — `dex_pools_handler.py` writes `dex_pool_state` to BOTH path and
      manifest (the 2-layer split is retired), `migrate_defi_full_v9_canonical.py` stamps `dex_pool_state` with NO
      remap, features read `data_type=dex_pool_state`. **The walk bakes `dex_pool_state` and code reads `dex_pool_state`
      — matched, no pre-apply block.** ⚠️ Do NOT "fix" this back to `dex_pools` — the `mtds_mdps_master.md` Phase 9
      `dex_pool_state→dex_pools` rename is a SUPERSEDED dead-letter (banner added there 2026-06-08). Defi audit guard
      (`defi-dexpool-name`) pins the canonical name. (reversed per SSOT; verified end-to-end by the 2026-06-08 sweep.)
- [x] ✅ [DATA] P2. D15 — HYPERLIQUID + ASTER classification. **Resolved at this item's scope 2026-08-02** (this
      checkbox tracked "scope + schedule the migration as its own tracked plan" — that deliverable is now done; the
      migration's own execution is tracked in the new plan, not here). **Partially resolved (corrected 2026-07-27):**
      the phase-label contradiction this item originally flagged is moot — both venues were removed entirely from
      `ALL_DEFI_VENUES`/`DEFI_VENUE_PHASE` on 2026-06-21 (commit `0d0e00a89`, fixing a 48.5k `attempted_failed`
      regression) and `perp_funding_handler` itself was retired 2026-07-08. **Operator decision (2026-07-27, pre-June-1
      stale-plans audit):** keep both venues pure CEFI (do not dual-classify in UAC, despite the 2026-07-07
      `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` "intentional hybrid" note, which was never
      reconciled against the 06-21 fix) — but the frozen legacy GCS/manifest corpus still sitting under
      `asset_group=defi` (HYPERLIQUID/HYPERLIQUID: 3.77M rows through 2026-05-31; ASTER/BSC: 1.07M rows through
      2026-05-31) must be migrated into `asset_group=cefi` so data agrees with the code-level classification.

      **CLEAR for dispatch (2026-07-30, conflict-check)** — no other active doc claims this migration. **Flagging, not
                                      blocking**: `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` still carries an unretracted
                                      "intentional hybrid CEFI+DEFI" classification note for these venues that this doc itself calls out as "never
                                      reconciled" against the later 06-21 operator ruling — worth a quick operator confirmation before/while scoping the
                                      migration plan, not a hard block.

                                      **Migration plan filed 2026-08-02** (this item's remaining action):
                                      `plans/archive/2026_08/hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md` (archived 2026-08-07;
                                      was `status: draft`, `assigned_vm: NA` per ask-before-creating default; mirrors
                                      `solana_defi_legacy_migration_2026_05_27`'s gate pattern — Phase 1 audit+script, Phase 2 VM execution, Phase 3
                                      manifest reconcile, Phase 4 operator-gated delete). Re-verified live 2026-08-02: legacy `asset_group=defi` corpus
                                      confirmed still present (bounded per-day GCS checks, not a whole-corpus walk), writes stopped between 2026-06-05
                                      and 2026-06-20 (frozen, no live-write race to coordinate a migration around). **The GCS/manifest migration itself
                                      has NOT executed yet — that work now lives in the new plan's own todos, not here.**
                                      **Migration COMPLETE 2026-08-06** — all 5 phases of the migration plan executed and verified: 7,599 objects
                                      migrated defi→cefi (parity-verified, zero mismatches) + `asset_group=defi` originals deleted. Evidence:
                                      market-tick-data-service@55d88025 (delete script + Phase 4/5 close-out). D15 is fully RESOLVED end-to-end.

- [x] ✅ [CODE] P3. D7 — **SHIPPED** MTDS@d3e02228
      (`fix(mev): remove banned bloxroute relays + stale .bak from     mev_events_handler`): the 2 bloxroute URLs are
      gone from `mev_events_handler.py` `MEV_BOOST_RELAYS` (Flashbots / agnostic / ultra_sound retained, comment cites
      this finding) and `mev_events_handler.py.bak` is deleted — verified on `origin/live-defi-rollout`. Usage audit
      found **nil active downstream consumption** of bloxroute/`mev_events` relay data (bloxroute already removed as the
      mempool feed; `sandwich_theoretical.py` is a theoretical-only tracer). — 2026-06-09.
- [x] ✅ [CODE] P3. D8 — **SHIPPED 2026-06-09** — Starknet `infura_compatible` RPC template removed from UAC
      `_defi_chain_data.py` (UAC@8a117153, on LDR; no consumer referenced the key) + `gas_fee_handler.py` paid-RPC
      comment de-Infura'd (MTDS@8fffc73b, on LDR). Infura is a removed provider (decommissioned workspace-wide
      2026-05-22). The pre-existing blockers that initially gated this (ci_incident Finding 5) were all remediated to
      ship it: (a) UAC version-aligned to 0.3.0 across main/LDR/staging (operator-authorized admin); (b) UAC
      backward-compat shims driven to **0** + 0 basedpyright baseline (deleted the `instruction.py` re-export stub,
      reworded 8 false-positive docstrings/comments, genericized the `gcs_paths` project-id) + `fear_greed` stub
      cassette allowlisted; (c) the `base-library.sh` SHA-sentinel gap (blocked all library agent-quickmerges) fixed
      (PM@091378337); (d) the diverged MTDS slot reconciled — `01fda7ce` (migrator gas-fees+liquidations → defi coverage
      6→8, rebuild `--bucket`) rebased onto LDR + shipped, redundant test mappings dropped (LDR already had them).
- [x] [CODE] P3. **DECIDED 2026-05-27 → KEEP** D13 — `governance_proposals` is an intentional unregistered scaffold for
      the Phase-4B simulation harness (not wired in `cli/main.py`), so it is NOT an active parallel path vs
      `governance_events`. No change; documented in the catalog § "Additional data types".
- [x] ✅ [INFRA] P3. D2 — delete legacy `lst_rates/`/`lending_indices/`/`dex_pools/` prefixes in
      `market-data-tick-defi-prd` (via `gcs_delete_object`) after dedicated buckets confirmed authoritative.
      `lst_rates/` **DONE 2026-05-28**: 1,200 date-prefix parquets deleted; 64,373 stale manifest rows pruned.
      `lending_indices/` + `dex_pools/`: deferred until Gate 2 Solana migration completes (canonical buckets must be
      confirmed superset first). Solana instrument_types added to codex — PM@(Gate 6 commit). Cited: UAC@7e9f4ad9 +
      UAC@90b2bb9d + MTDS@c38d1ca3 + MTDS@896d5c9 (Gate 5). — **CLOSED 2026-05-28 leg + FOLDED+DELETED 2026-07-21 for
      the remaining two, re-verified 2026-07-28.** The `lending_indices/`/`dex_pools/` deferral resolved: those two
      prefixes were folded to canonical and operator-prod-deleted 2026-07-21, re-probed at 0 objects. Re-verified this
      pass (re-reading, not re-deriving): `/codex/02-data/non-canonical-path-inventory.md:96` — "The DO-NOT-DELETE below
      is HISTORY. The safe fold→repoint→delete order was executed 2026-07-21";
      `/plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md` frontmatter `status: resolved`; its
      spawned residual `/plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md` also
      `status: resolved`; CLAUDE.md's "`dex_pools/` + `lending_indices/` — FOLDED + DELETED 2026-07-21" line. All three
      legs of D2 (`lst_rates/`, `lending_indices/`, `dex_pools/`) are now closed. Per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`, this checkbox flip is read-only bookkeeping — no GCS
      delete run in this pass (the prod delete already happened 2026-07-21, operator-executed). Source/cross-ref:
      `plans/archive/2026_07/defi_satellite_ao_dispatch_batch4_2026_07_26.md` todo 1.

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (5 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — every tracked drift is `[x]` resolved, so swapped
  in the D15 residual's actual migration plan for the stale "mirrors" cross-reference; no source path (closed-out
  process audit, all code fixes already shipped elsewhere).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (4 entries), unchanged — all 15 drift items remain
  `[x]` resolved (D15's HYPERLIQUID/ASTER migration plan, still the correct cross-reference, itself completed
  2026-08-06).
- **2026-08-12** — `locked_by`/`locked_since` cleared (corpus-wide fix, operator ruling Option B, interactive session
  2026-08-12; see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md). This doc has
  0 open todos, so clearing the placeholder lock immediately makes it archive-eligible. Per the ruling's explicit scope
  ("do NOT auto-archive in this same pass"), archival itself is deferred to a separate follow-on pass; bridged with
  `archive_exempt: true` (the sanctioned flip-then-mv two-commit pattern documented in
  `scripts/plan-hygiene/check_archive_candidates.sh`) so this commit doesn't trip the archive-candidates pre-commit
  gate. The follow-on pass should drop `archive_exempt` and `git mv` this doc to `plans/archive/[issues/]`.
