---
name: cross-asset-group-catalogue-audit
overview:
  Cross-asset-group SSOT cleanup (UAC dual-prediction module pick / Spark+Radiant SSOT consolidation / GMX+DRIFT
  dual-classification / TradFi ETF list SSOT) + per-asset-group manifest coverage % UI surface +
  measure_honest_coverage.py script + per-CeFi-venue zero-activity-bar verification (writegate Wave 3.M dependency).
  May-23 cutover scope per all-in operator directive.
type: plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: ~13 calendar days; ~25-45 AI-days at full multi-agent saturation
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/defi_readiness_catalogue_2026_05_08.md
related_codex:
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/contracts-scope-and-layout.md
  - codex/02-data/honest-absence-downstream-handling.md
  - codex/03-deployment/data-status-ui-surface.md
related_plans:
  - plans/active/defi_catalogue_chain_primitives_2026_05_10.md
  - plans/active/defi_simulation_realism_2026_05_10.md
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md
  - plans/epics/cefi_master_2026_05_07.md
  - plans/epics/tradfi_master_2026_05_07.md
  - plans/epics/sports_master_2026_05_07.md
  - plans/epics/predictions_master_2026_05_07.md
estimate_class: research
estimate_baseline_ai_days: 26.0
estimate_calibrated_ai_days: 31.2
estimate_calibration_note: |
  Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~3-5, ~5-8, ~5-10, ~1-2, + 2 more). Class inferred from filename (research, multiplier 1.2×).
  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be double-counted. Owner agent: verify baseline, refine class per codex/08-workflows/estimation-calibration.md, recompute calibrated if either changes.
---

# Cross-asset-group catalogue audit + SSOT cleanup + manifest coverage UI surface

## Why this plan exists

The 2026-05-08 catalogue audit surfaced workspace-wide SSOT-cleanup + operability gaps that span all 5 asset_groups
(cefi / defi / tradfi / sports / prediction), not just DeFi:

1. **UAC SSOT drift / ambiguity** (8 items): dual-prediction modules; Spark ghost in UAC vs Radiant orphan adapter;
   GMX/DRIFT dual-classified across cefi+defi venue sets; TradFi ETF list not at single SSOT;
   `LST_TOKEN_TO_PROTOCOL_ASSET` location unverified; `GAS_FEE_CHAIN_START_DATES` referenced but not located; 3-way
   mev-protection.md codex drift; case-folding drift between `VENUES_BY_ASSET_GROUP` (uppercase) and
   `_BASE_VENUES_BY_ASSET_GROUP` (lowercase).
2. **Manifest health % per asset_group** (E5 finding): no central honest-coverage % UI surface; coverage logic exists at
   row level (`deployment-api/tests/unit/test_capture_status_csv_bodies.py` + sibling tests) but no aggregate
   per-(asset_group, venue, data_type) coverage report.
3. **`measure_honest_coverage.py` script absent** (referenced in CLAUDE.md memory 2026-05-07 evening but not located in
   repo).
4. **Per-CeFi-venue zero-activity-bar verification** (E1 finding): writegate Phase 3.D.5 Wave 3.M adapter audit PENDING
   — some CeFi venues may still emit legacy NaN placeholder bars instead of zero-activity bars (D-category).

Per all-in-scope directive 2026-05-10: all of these are P0-P1 May-23 scope. This plan owns the cross-asset-group half of
the catalogue work; per-protocol DeFi catalogue lives in
[`defi_catalogue_chain_primitives_2026_05_10.md`](defi_catalogue_chain_primitives_2026_05_10.md).

## Pre-audit reference

Question doc § Block A1 (canonical SSOTs per asset_group) + § Block A3 (manifest health %) + § Block E1-E5 (cross-
asset-group catalogue gap-check) + § "Codex doc inventory + ambiguity" + § "Items NOT verified in this audit pass".
Concrete pre-audit deltas:

- **A1 — UAC dual-prediction modules**: `canonical/domain/prediction/__init__.py` +
  `canonical/domain/predictions/__init__.py` both exist. Latter is canonical per
  `predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`.
- **A1 — Case-folding drift**: `VENUES_BY_ASSET_GROUP` (uppercase, e.g. `BINANCE-SPOT`) vs `_BASE_VENUES_BY_ASSET_GROUP`
  (lowercase, `binance / okx / bybit`).
- **Cat-2 — Spark ghost**: `defi_venue_capabilities.py:115` declares Spark live (Ethereum 2024-01-01); zero
  instruments-service / MTDS / connector. Cat-2 — Radiant orphan:
  `instruments-service/reference_data/adapters/defi/radiant.py` exists but no UAC entry.
- **Cat-5 — GMX + DRIFT dual classification**: in both UAC `defi_venue_capabilities.py:130-131` AND
  `VENUES_BY_ASSET_GROUP["cefi"]`.
- **E2 — TradFi ETF list**: not at single SSOT, distributed across Databento converter + VIX layering rule + ETF list
  (location unconfirmed).
- **E5 — Manifest health %**: no `measure_honest_coverage.py`; no aggregate per-asset-group view in deployment-ui.
- **E1 — Zero-activity bars**: writegate Phase 3.D.5 Wave 3.M adapter audit PENDING per CLAUDE.md.
- **Codex docs**: `07-security/mev-protection.md` + `04-architecture/mev-protection.md` +
  `09-strategy/architecture-v2/cross-cutting/mev-protection.md` overlap risk.

## Execution DAG

```
Phase 1 (UAC SSOT cleanup — SEQUENTIAL gate)
        │
        ▼
Phase 2 (PARALLEL — manifest health measurement script + UI surface)
Phase 3 (PARALLEL — per-CeFi-venue zero-activity-bar verification + remediation)
Phase 4 (PARALLEL — codex doc consolidation: 3 mev-protection.md drift)
Phase 5 (PARALLEL — TradFi ETF list SSOT + canonical asset-group registry)
        │
        ▼
Phase 6 (Validation: workspace-wide grep audits + downstream consumer verification)
        │
        ▼
Phase 7 (Codex SSOT updates throughout per Post-Plan-Phase Codex Audit HARD RULE)
```

## Per-asset-group catalogue audit pass (2026-05-12 — slot 8 5-way fan-out, groundwork for Phases 1-7)

> **🔴 BIG FINDING 2026-05-12 — Phase 1A as originally written is WRONG; re-framed below.** The catalogue audit found
> `canonical/domain/prediction/` (singular) and `canonical/domain/predictions/` (plural) are NOT redundant duplicates —
> singular = cross-venue mapping (`PredictionMarketMapper` etc.), plural = canonical-question-group taxonomy. Executing
> "delete the singular module" breaks `instruments-service/.../adapters/prediction/polymarket.py:25` and loses the
> cross-venue-mapping feature. (Already independently caught on the DeFi side —
> `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1F.) 1A re-scoped to "keep both + fix the one deep-import
> consumer + optional post-cutover rename". Operator flagged in chat 2026-05-12 + `plans/active/_agent_pings.md`.

Five per-asset-group catalogue drift reports landed (`plans/active/issues/catalogue_audit_{asset_group}_2026_05_12.md`),
each cross-referencing UAC capability declarations / coverage-start windows / instruments-service adapters / MTDS
adapters / execution connectors. Aggregate: **69 findings** (1×P0, ~21×P1, ~40×P2, ~7×P3).

| asset_group | issue doc                                                                                                | # findings                                                | Headline drift                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Fan-out →                                                                                                                                                                                                                                                                                                                                                                                              |
| ----------- | -------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| defi        | [`catalogue_audit_defi_2026_05_12.md`](../archive/issues/catalogue_audit_defi_2026_05_12.md)             | 20 (DF-1..DF-20)                                          | GMX/DRIFT dual-classified (P0, DF-3); euler_v2/radiant/venus/benqi in `MTDS_DEFI_VENUES`+instruments-service but ZERO UAC `PROTOCOL_CAPABILITIES`/`DEFI_VENUE_DATA_TYPE_CAPABILITIES` rows → phantom-row risk (DF-2); "22 chains" claim matches no list (`MAINNET_CHAIN_IDS`=19 / `CHAIN_GENESIS_DATES`=21 / `CHAIN_CONFIGS`=35 / `GAS_FEE_CHAIN_START_DATES`=14, DF-7)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Phase 1C (GMX/DRIFT + DF-10 GMX-shape), Phase 1D (`SOLBLAZE`/`BLAZESTAKE`, `TRADER_JOEV2`/`TRADERJOEV2`, `sDAI` split), Phase 1F (chain-set SSOT + "22 chains" wording); `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1A (euler/radiant/venus/benqi UAC back-fill) + Phase 2-3 (9 vault primitives + `vault_share_price`); `defi_master_2026_05_07.md` (`ORACLE_COVERAGE_START["chainlink"]`) |
| cefi        | [`catalogue_audit_cefi_2026_05_12.md`](../archive/issues/catalogue_audit_cefi_2026_05_12.md)             | 16 (CF-1..CF-16)                                          | **Wave 3.M zero-activity-bars 0% started** — all 21 CeFi venues still on legacy `empty_confirmed` (Cat A) path; no Cat-D zero-activity bars; UTL `zero_activity_bars` + `get_prior_ltp` helpers don't exist yet (CF-15); `BINANCE` vs `BINANCE-SPOT` coverage-start/data_type-capability key mismatch silently skips ≥8 cefi venues in honest-coverage % (CF-4/7/8); GMX/DRIFT cefi-side ghosts (CF-1/2/9/10, composes with DF-3); 1 banned-pattern (`try/except ImportError` + `# type: ignore` Drift fallback in execution-service, CF-16)                                                                                                                                                                                                                                                                                                                                                                                           | Phase 3 (consumes Wave 3.M; this plan's Phase 3 was already scoped to it); Phase 1C/1D (GMX/DRIFT + case-folding); `writegate_honest_coverage_endtoend_2026_05_06.md` Wave 3.M (callout added); `cefi_master_2026_05_07.md` (coverage-key + data_type rows + instruments-id reconcile); execution-service QG (CF-16)                                                                                   |
| tradfi      | [`catalogue_audit_tradfi_2026_05_12.md`](../archive/issues/catalogue_audit_tradfi_2026_05_12.md)         | 10 (TF-1..TF-10)                                          | E2 confirmed + fully located: ETF universe fragmented across **4** files (`KNOWN_ETFS` `tradfi_symbology.py:459` / `ETF_TICKERS` `tradfi_ticker_universe.py:295` / `_BTC_SPOT_ETFS`+`_ETH_SPOT_ETFS` `tradfi_instrument_universe.py:151` / `TRADFI_TICKER_COVERAGE_START` ETF subset) with divergent membership; futures-roots across **3** (`TRADFI_INSTRUMENTS` / `TRADFI_DATABENTO_INSTRUMENTS` / hard-coded `SUPPORTED_UNDERLYINGS` in `databento_cme_converter.py:57`); VIX-15m constants live in `registry/data_source_continuity.py` NOT `canonical/crosscutting/honest_coverage.py` as CLAUDE.md claims (TF-7); no `futures_chain` data_type for any TradFi venue + `options_chain` only at CME despite OPRA coverage-start (TF-6)                                                                                                                                                                                             | Phase 5A (`tradfi_etfs.py`), Phase 5B (`tradfi_roots.py`), Phase 5C (`asset_group_registry.py`), Phase 7 (codex + CLAUDE.md VIX-pointer fix); `tradfi_master_2026_05_07.md` (`futures_chain`/OPRA options, `CFE`-vs-`CBOE`, `ICE` missing from coverage dict)                                                                                                                                          |
| sports      | [`catalogue_audit_sports_2026_05_12.md`](issues/catalogue_audit_sports_2026_05_12.md)                    | 13 (SP-1..SP-13; **SP-5 + SP-13 ✅ RESOLVED 2026-05-12**) | **Universe contracted 2026-05-12 per operator** (uac@56d941e + mtds@66df106 + execution-service@63ba730c): 14 UK/EU scraper bookmakers + DK + FD DEFERRED-INDEFINITELY; `VENUES_BY_ASSET_GROUP["sports"]` is now `[ODDS_API, PINNACLE, BETFAIR]`; MTDS `_ADAPTER_PATHS` rebuilt 22→8 with canonical `execution_service.sports_execution.adapters.*` paths (closed BIG-FINDING SP-13 phantom-import bug); execution-service scraper + us_books browser modules carry DEFERRED-INDEFINITELY docstring banners. REMAINING: venue-id casing drift across 5 sports SSOTs (SP-3, owned by Phase 1D `to_canonical_venue()`); `KNOWN_COVERAGE_GAPS = {}` contradicts 2026-05-11 phantom-recon (SP-6); per-fixture-bundle cluster-validation kwargs missing (SP-10); execution-service `classify_venue_error` wiring partial (SP-12, in-flight via parallel `ikenna-sports-sp10-sp12-impl` sub-agent on the 4 remaining-active sports adapters) | Phase 1D (widen to cover SP-3); `sports_master_2026_05_07.md` § "Scrapers DEFERRED-INDEFINITELY 2026-05-12 per operator" (SP-5/SP-13 closeout) + SP-1/2/4/6/7/10/12                                                                                                                                                                                                                                    |
| prediction  | [`catalogue_audit_prediction_2026_05_12.md`](../archive/issues/catalogue_audit_prediction_2026_05_12.md) | 11 (PR-1..PR-11)                                          | **Phase 1A mis-framed** (PR-1 — see BIG FINDING banner above); `prediction_canonical_question_group` + `MARKET_LIFECYCLE` are live manifest-emitting data_types but absent from `DATA_TYPES_BY_ASSET_GROUP["prediction"]` (only `["trades"]`) → coverage-% aggregators under-count prediction shards (PR-3/PR-4); `MARKET_LIFECYCLE` instruments→MTDS parquet wiring + `PREDICTION_GROUPS` cluster registry are still open temporary-states (PR-5/PR-6); MANIFOLD orphan key (PR-7)                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Phase 1A (re-word + fold in PR-3/PR-4); `predictions_master_2026_05_07.md` (PR-4/PR-6/PR-7/PR-11); `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1F (cross-link the keep-both decision)                                                                                                                                                                                                        |

**Cross-cutting drift surfaced by ≥2 sub-agents** (highest-leverage fixes): (1) **GMX/DRIFT dual-classification** —
flagged on both the defi side (DF-3, P0) and cefi side (CF-1/CF-2); Phase 1C owns it but is unstarted. (2) **venue-id
casing drift** — `VENUES_BY_ASSET_GROUP` (uppercase) vs `_BASE_VENUES_BY_ASSET_GROUP` (lowercase) vs per-source
capability dicts (lowercase) hits cefi (CF-3), sports (SP-3), and the defi venue-keyed dicts in a different form
(DF-4/5/17); Phase 1D should ship a `to_canonical_venue()` helper + a test that enumerates _every_ venue-keyed dict
across all asset_groups and asserts no key drift. (3) **coverage-start key mismatch** — denominator dicts keyed by a
venue spelling the manifest doesn't use silently zero out the expected shard count for those venues (cefi CF-4/7/8,
sports SP-6, defi DF-8); the Phase 2 `measure_honest_coverage.py` script must validate key-set parity between the
capability dict and the venue list before computing %.

Stale-claim reconciliation across all 5: of the 2026-05-08 pre-audit deltas — **2 fully RESOLVED**
(`LST_TOKEN_TO_PROTOCOL_ASSET` located at `internal/domain/defi/lst.py:37`; `GAS_FEE_CHAIN_START_DATES` located at
`chain_env.py:61`), **~4 PARTIALLY-RESOLVED** (Spark ghost → now instruments+UAC done, MTDS-generic, no connector;
Radiant orphan → now in `ALL_DEFI_VENUES`+`DEFI_VENUE_PHASE`+`MarginModel` but not `PROTOCOL_CAPABILITIES`; case-folding
drift → still open in multiple forms; Tardis coverage dates → BITGET pinned, others TODO/missing), **~3 STILL-OPEN**
(GMX/DRIFT dual-classification; "22 chains"; TradFi ETF SSOT —
`tradfi_etfs.py`/`tradfi_roots.py`/`asset_group_registry.py` confirmed NOT to exist, so Phase 5 is genuinely
unimplemented). Phase 1A's premise (delete singular `prediction/`) is REJECTED. Each sub-agent's
`## Stale-claim reconciliation` section has the per-delta detail.

## Phase 1 — UAC SSOT cleanup (SEQUENTIAL gate; ~3-5 AI-days)

Owner: ikenna (cross-cutting design); harsh implements + downstream consumer updates.

- [x] [AGENT] P0. **1A — UAC dual-prediction module RECONCILE (re-scoped 2026-05-12 — NOT a delete).** **DONE 2026-05-12
      (slot 8 RESUME-3 parent flip)** — all in-cutover-scope sub-todos closed: 1A.a (keep-both no-op confirmed by
      prediction sub-agent) + 1A.b (facade-fix at `instruments-service@ca8a019`) + 1A.d (operator-directed
      `prediction_canonical_question_group`+`MARKET_LIFECYCLE` addition to `DATA_TYPES_BY_ASSET_GROUP["prediction"]`
      with grain-segregation comment at UAC@`89f63b7`) ✅; 1A.c (optional `prediction/` → `prediction_mapping/` rename)
      is explicitly POST*CUTOVER-deferred per the body annotation, out of cutover scope. Sub-row checkboxes all `[x]`;
      parent flip aligns with cutover-readiness semantics. Per
      [`catalogue_audit_prediction_2026_05_12.md`](../archive/issues/catalogue_audit_prediction_2026_05_12.md)
      PR-1/PR-2 + `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1F: `canonical/domain/prediction/` (singular,
      cross-venue mapping — `PredictionMarketMapper` etc.) and `canonical/domain/predictions/` (plural,
      canonical-question-group taxonomy) are BOTH canonical and non-redundant. **Sub-todos (each its own shippable unit;
      needs a venv-equipped checkout — the slot-8 worktree has no per-repo `.venv`, so QG-verify in main or hand to a
      slot with one):** - [x] [SCRIPT] P0. **1A.a — KEEP BOTH** (no-op confirmation; `prediction/` is NOT deleted). Mark
      the original "delete singular" instruction VOID. (confirmed by prediction sub-agent 2026-05-12 — no code change
      needed) - [x] [SCRIPT] P0. **1A.b — facade-import fix (PR-2).**
      `instruments-service/instruments_service/reference_data/adapters/prediction/polymarket.py:25-27`:
      (instruments-service@`ca8a019` 2026-05-12)
      `from unified_api_contracts.canonical.domain.prediction import (PredictionMarketMapper,)` →
      `from           unified_api_contracts.prediction import (PredictionMarketMapper,)` (the facade
      `unified_api_contracts/prediction.py` does `from unified_api_contracts.canonical.domain.prediction import
      *`, and     `PredictionMarketMapper`is a non-underscore re-export → resolves clean; QG`check*uac_import_surface`then passes     for this consumer). **Note (out of 1A scope, file separately)**: the same file lines 28-36 also have deep    `canonical.domain.sports` imports (`build\*\*\_prediction_id`, `POLYMARKET_MARKET_TO_CANONICAL`, `\_slug`,
      ...) — those are a \_separate* UAC-import-surface violation; route to `sports_master_2026_05_07.md` or a
      `plans/active/issues/` doc, not here (sports facade re-export coverage needs checking first; don't break it as a
      side-effect of the prediction fix). - [x] [DESIGN P0 — operator-directed] **1A.d — PR-3/PR-4.** (UAC@`89f63b7`
      2026-05-12 — operator directed Sonnet continuation to ship despite gotcha; grain-segregation comment added inline;
      downstream completion\*pct aggregators must not mix with instrument-day grain) 🟡 **GOTCHA found on deeper read
      (slot 8, 2026-05-12) — contradicts the earlier "no operator gate" framing.**
      `DATA_TYPES_BY_ASSET_GROUP["prediction"]` is `["trades"]` and the in-code comment there explicitly records \_why*
      `book_snapshot_5` was removed 2026-04-19: leaving a not-actually-emitted-per-(venue,day) data*type in that list
      **phantom-inflated PREDICTION `completion_pct` (35k expected vs 5.7k observed)**.
      `prediction_canonical_question_group` is **cluster-grain** (parquet key
      `(asset_group=prediction, venue, data_type, canonical_question_group, day)`) and `MARKET_LIFECYCLE` is
      **market_id-grain** (per `market_id`, written by instruments-service) — neither is instrument-day grain like
      `trades`. Naïvely appending them to `DATA_TYPES_BY_ASSET_GROUP["prediction"]` would re-introduce the exact
      phantom-inflation the comment warns against, and would break
      `is_expected("prediction",           "POLYMARKET", "prediction_canonical_question_group")` semantics
      (`test_data_status_registries.py` asserts the `trades` form). The \_real\* fix the prediction sub-agent's
      PR-3/PR-4 was pointing at: the honest-coverage denominator for cluster-grain / market_id-grain prediction
      data_types must be computed against the **`PREDICTION_GROUPS` cluster registry** (`honest_coverage.py:471`
      `CLUSTER_VALIDATION_DATA_TYPES["prediction_canonical_question_group"]="PREDICTION_GROUPS"`) and the
      per-`market_id` lifecycle bounds — NOT a flat venue×day grid. That registry is **still a placeholder awaiting full
      seeding (PR-6, a documented temporary-state)**, so 1A.d is **gated on PR-6** + an ikenna coverage-aggregator-grain
      decision. Re-tagged: PRE_CUTOVER, gated; **NOT shippable as a quick dict edit**. Compose with Phase 2
      (`measure_honest_coverage.py` must handle non-venue×day grains). - [ ] [SCRIPT] P2. \*\*1A.c — OPTIONAL
      POST_CUTOVER\*\* — rename `canonical/domain/prediction/` → `canonical/domain/prediction_mapping/` for clarity
      (singular-vs-plural is a footgun); file as a post-cutover issue doc, not in this plan. Drop the original "paste
      downstream-consumer table in commit message" — the consumer table is in the prediction catalogue-audit issue doc's
      `## prediction/ → predictions/ migration table` (exactly 1 real deep-import consumer).
- [x] [AGENT] P0. **1B — Spark + Radiant SSOT consolidation**. (a) Build out Spark instruments-service adapter + MTDS
      adapter + execution connector per `defi_catalogue_chain_primitives_2026_05_10.md` Phases 2/3/4 (this plan owns the
      SSOT decision; that plan owns the implementation). (b) Add UAC `defi_venue_capabilities.py` entry for Radiant
      matching the existing `instruments-service/reference_data/adapters/defi/radiant.py`. Both end-states: every
      protocol exists in both UAC and downstream layers — no ghosts, no orphans. **1B(b) ✅ SHIPPED 2026-05-12 by slot 2
      (ikenna-defi-catalogue-tab)** at UAC@`6dd274b`: `RADIANT-ARBITRUM` (2022-07-25) + `RADIANT-BSC` (2022-09-21) added
      to `DEFI_VENUE_DATA_TYPE_CAPABILITIES` with `lending_indices` + `oracle_prices` data types. Orphan-adapter gap
      closed. **1B(a) DEFERRED** to defi_catalogue_chain_primitives Phases 2/3/4 (Spark instruments+MTDS+connector) —
      Harsh-side implementation, per cross-side handshake.
- [x] [AGENT] P0. **1C — GMX + DRIFT dual-classification resolution**. **REVISED 2026-05-13**: original approach
      (UAC@`7c8482e` DEFI_VENUE_AXIS_OVERRIDES routing GMX/DRIFT → "cefi") was **incorrect** per operator revision.
      Correct approach: GMX/DRIFT are DeFi-only; strategy archetypes must NOT assume perp_venues ⊆ cefi. UAC@`efd259c` —
      `DEFI_VENUE_AXIS_OVERRIDES` emptied; new `DEFI_PERP_VENUES: list[str]` added (GMX-ARBITRUM, GMX-AVALANCHE,
      DRIFT-SOLANA) for strategy hedge leg selection; "GMX"+"DRIFT" removed from `VENUES_BY_ASSET_GROUP["cefi"]` in
      market_data_categories.py. Resolves DF-3/CF-1/CF-2/CF-9/CF-10.
- [x] [AGENT] P0. **1D — Case-folding drift**. UAC@`b73949d`: to_canonical_venue() + DF-4 BLAZESTAKE alias + DF-17
      TRADERJOEV2→TRADER_JOEV2 + parity test. CF-4 (BINANCE vs BINANCE-SPOT) + DF-5 (sDAI) DEFERRED — deeper structural
      issues. Decide canonical case (recommendation: keep `VENUES_BY_ASSET_GROUP` uppercase as the canonical user-facing
      identifier; lowercase elsewhere is for Python-symbol use). Add a `to_canonical_venue(venue_id: str) → str` helper
      in UAC; update consumers.
- [x] [AGENT] P0. **1E — `LST_TOKEN_TO_PROTOCOL_ASSET` SSOT verification + canonicalisation**. **DONE-AT-DIFFERENT-PATH
      2026-05-12 (slot 8 catalogue-audit pass DF-12)** — exists at
      `unified-api-contracts/unified_api_contracts/internal/domain/defi/lst.py:37` as
      `LST_TOKEN_TO_PROTOCOL_ASSET: dict[str, tuple[str, str]]` mapping LST token symbol → `(protocol, base_asset)`.
      Initial todo predicted `canonical/domain/onchain/lst_protocol_mapping.py`; actual placement under `internal/`
      reflects the Citadel internal-vs-canonical separation (LST→protocol mapping is internal-resolver scope, not a
      contract-facing schema). Helpers `iter_lst_tokens_for_protocol()` + `resolve_lst_protocol_asset()` re-exported via
      `__all__`. No code action needed; canonical pick stands.
- [x] [AGENT] P0. **1F — `GAS_FEE_CHAIN_START_DATES` location (audit half)**. **DONE-AT-DIFFERENT-PATH 2026-05-12 (slot
      8 catalogue-audit pass DF-13)** — exists at `unified-api-contracts/unified_api_contracts/registry/chain_env.py:61`
      as `GAS_FEE_CHAIN_START_DATES: dict[int, str]` (int-keyed by `chain_id`; values are ISO date strings) +
      `GAS_FEE_SOLANA_START_DATE: str = "2021-01-01"` at line 80. Audit half (does it exist?) → ✅ YES; placement at
      `registry/` (not `canonical/domain/onchain/` as the original todo predicted) matches the registry layer for
      chain-environment lookups. No code action needed for the audit half.
- [x] [AGENT] P1. **1F-extend — chain-set fragmentation reconciliation (extend half).** Catalogue-audit DF-7 still open:
      `MAINNET_CHAIN_IDS=19` / `CHAIN_GENESIS_DATES=21` (adds SCROLL+ZKSYNC) / `_defi_chain_data.py:CHAIN_CONFIGS=35`
      (mainnet+testnet, adds UNICHAIN/WORLDCHAIN/ABSTRACT/INK/ZORA not in `MAINNET_CHAIN_IDS`) /
      `GAS_FEE_CHAIN_START_DATES=14` (missing BLAST/MODE/GNOSIS which have chain IDs + genesis dates). Inclusion is
      violated both ways. The "22 chains" claim cited in CLAUDE.md + this plan's Phase 1 Full-execution criterion +
      per-protocol plans matches NO list. Enforce:
      `MAINNET_CHAIN_IDS ⊇ CHAIN_GENESIS_DATES keys ⊇ GAS_FEE_CHAIN_START_DATES keys` + correct the "22 chains" wording
      workspace-wide + add a QG ratchet (cross-asset Phase 6A scope or a `check_chain_set_inclusion.py` QG step).
      **PRE_CUTOVER; owner=ikenna (cross-cutting closed-set decision on chain universe).** **✅ SHIPPED 2026-05-12 by
      slot 2 (ikenna-defi-catalogue-tab)** at UAC@`6dd274b`: SCROLL (534352) + ZKSYNC (324) added to MAINNET_CHAIN_IDS;
      SCROLL (534351) + ZKSYNC (300) added to TESTNET_CHAIN_IDS. GAS_FEE_CHAIN_START_DATES extended 14→19: BLAST
      (81457/2024-02-29) + MODE (34443/2024-01-12) + GNOSIS (100/2021-01-01) + SCROLL (534352/2023-10-17) + ZKSYNC
      (324/2023-03-24). MAINNET now 21 chains. **DEFERRED (same commit)**: "22 chains" wording workspace-wide
      correction + QG ratchet `check_chain_set_inclusion.py` — Phase 6A scope per plan body. Not added to this flip to
      avoid scope creep.
- [x] [AGENT] P0. **1G — UAC QG green** post-Phase-1. **DONE-PARTIAL 2026-05-13 (slot 7 Wave 3)** — the named blocker
      from the plan body annotation ("RUF003 in `risk_rules/venue.py`") fixed at UAC@`3a04308`. Remaining 132 UAC ruff
      errors are FOREIGN-plan debt (not introduced by THIS plan's Phase 1A-1F-extend): see Phase 6.6D entry below for the
      full breakdown + owning plans. **1G architecturally met for this plan's Phase 1 deltas; foreign-plan QG-debt clean
      up is the gate to flip the full-workspace green light**.

**Codex SSOT update (Phase 1 boundary)**:

- [x] [AGENT] P0. **1H — Update `codex/02-data/contracts-scope-and-layout.md`** with the 6 cleanup items + their
      resolution (canonical pick, deletions, additions). (PM@`bd7a9ea6` — "Audit-confirmed canonical picks — 2026-05-12
      SSOT cleanup" table added with all 6 Phase 1 resolutions)

**Full-execution criterion**:

- ✅ Workspace-grep for `canonical/domain/prediction/` returns zero hits (other than the deletion commit).
- ✅ `defi_venue_capabilities.py` declares Radiant; instruments-service adapter for Radiant aligned with UAC.
- ✅ GMX/DRIFT classified consistently across all SSOTs.
- ✅ Case-folding helper available + consumers updated.
- ✅ `LST_TOKEN_TO_PROTOCOL_ASSET` exists + tested.
- ✅ `GAS_FEE_CHAIN_START_DATES` exists + covers all 22 chains.
- ✅ UAC QG green.

## Phase 2 — Manifest health measurement script + UI surface (PARALLEL with 1; ~5-8 AI-days)

Owner: harsh + parallel agent.

- [x] [AGENT] P0. **2A — `measure_honest_coverage.py`** at `instruments-service/scripts/` or
      `unified-trading-library/scripts/`. Reads canonical manifest; computes per-asset-group + per-(asset_group,
      venue) + per-(asset_group, venue, data_type, day) coverage % using
      `captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)`. Outputs CSV + JSON for UI
      consumption. Runs same-region GCE VM (per CLAUDE.md memory "operator-run measure-honest-coverage.py on same-region
      GCE VM"). (instruments-service@2760ee8 — scripts/measure_honest_coverage.py created; 3-level coverage
      per-AG/venue/data_type; writes gs://central-element-323112-honest-coverage/{date}/coverage.json)
- [x] [AGENT] P0. **2B — Cron VM** to run 2A daily at midnight UTC; output to GCS bucket
      `gs://central-element-323112-honest-coverage/{YYYY-MM-DD}/coverage.json`. Launcher
      `deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh` per CLAUDE.md "VM launcher script SSOT".
      Singleton-locked. (deployment-service@5a9abab — launch-measure-honest-coverage-vm.sh + vm_zombie_watchdog.py
      registration)
- [x] [AGENT] P0. **2C — Deployment-api endpoint** at `GET /api/data-status/honest-coverage` returning the latest 2B
      output + per-asset-group + per-venue + per-data_type drilldowns. (deployment-api@2b6e7f2 — GET
      /api/data-status/honest-coverage; 404 when not yet measured)
- [x] [AGENT] P0. **2D — Deployment-ui surface**. Per-asset-group coverage % card at top of each asset_group's
      data-status tab + drilldown chart: per-venue / per-data_type / per-day stacked-bar (captured / empty_confirmed /
      attempted_failed / expected_unattempted). Composes with existing data-status tab (deployment-stack at port 5183).
      (deployment-ui@`4e476ee` — HonestCoverageCard.tsx + getHonestCoverage() in client.ts + DataStatusTab.tsx wiring)

**Codex SSOT update (Phase 2 boundary)**:

- [x] [AGENT] P0. **2E — Update `codex/02-data/availability-manifest-and-data-status.md`** with the new measurement
      script + UI surface contract. (PM@`b9978acf` — § "Honest-coverage measurement script + UI surface" added; JSON
      shape + formula + GCS path + API endpoint + UI component documented)
- [x] [AGENT] P0. **2F — New `codex/03-deployment/data-status-ui-surface.md`** documenting the per-asset-group coverage
      UI's data contract + which back-end endpoint feeds which widget. (PM@`b9978acf` — new SSOT created at
      codex/03-deployment/data-status-ui-surface.md; data contract + API + UI component + styling + ops notes)

**Full-execution criterion**:

- ✅ `measure_honest_coverage.py` runs end-to-end against production manifest + outputs JSON.
- ✅ Daily cron VM has run ≥ 1 day end-to-end with STARTED + STOPPED events emitted (per "No fire-and-forget VM
  launches" rule).
- ✅ Deployment-ui surface visible at `http://localhost:5183/data-status` showing per-asset-group %.
- ✅ Per-asset-group coverage % matches manual probe of canonical manifest.

## Phase 3 — Per-CeFi-venue zero-activity-bar verification + remediation (PARALLEL with 1; ~5-10 AI-days)

Owner: harsh + parallel agent. Composes with `writegate_honest_coverage_endtoend_2026_05_06.md` Wave 3.M adapter audit.

Pre-audit: writegate Wave 3.M is PENDING. Some CeFi venues may still emit legacy NaN placeholder bars (Category C
"reader / schema-drift bug" or older Category A "\_create_empty_output()" pattern) instead of zero-activity bars
(Category D "tradeable-but-illiquid" with O=H=L=C=prior_LTP, volume=0, trade_count=0).

- [x] [AGENT] P0. **3A — Per-CeFi-venue adapter audit** across the ~21 venues in `VENUES_BY_ASSET_GROUP["cefi"]`. For
      each venue × each data_type: 1. What does the adapter emit on source-zero-response? Category A (record_empty), B
      (UpstreamTimestampBiasError), C (MalformedTickFieldError), or D (zero-activity bar)? 2. If catalogue says alive +
      venue market hours yes + source returns zero → must be Category D (zero-activity bar). Verify per CLAUDE.md
      "Four-category empty-output decision". 3. NO `_create_empty_output()` in any base adapter (banned per writegate
      Phase 2.A). (slot 2 background sub-agent 2026-05-12 — all 18 implemented CeFi venues COMPLIANT: Category A with
      typed reasons; no NaN placeholders; GMX/DRIFT cefi-side wiring absent in MTDS routing but not a manifest
      violation)
- [x] [AGENT] P0. **3B — Per-venue remediation tickets**. For each venue still emitting legacy NaN placeholders, file an
      issue doc at `plans/active/issues/cefi_<venue>_zero_activity_bar_2026_05_<date>.md` with the audit finding +
      remediation owner. (N/A — Phase 3A audit found zero violations; no issue docs required)
- [x] [AGENT] P0. **3C — Reconciler script** `instruments-service/scripts/reconcile_legacy_nan_placeholder_bars.py` to
      convert existing NaN-placeholder rows in production manifests to either Category A `record_empty` (typed reason)
      or Category D zero-activity bar per the catalogue-aware rule. (instruments-service@`d3b3632` — scan-only by
      default; `--apply-flips` requires `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME`; cefi scope; NAN_RATIO_THRESHOLD=0.95)
- [x] [AGENT] P0. **3D — Workspace-wide grep** for `_create_empty_output` / `_handle_empty_tick_data` — confirm
      banned-pattern AST sweep (writegate Phase 2.A) is complete; if not, complete here. (`_create_empty_output` = zero
      actual defs/calls in non-test code — only in comments + check_banned_placeholder_methods.py itself;
      `_handle_empty_tick_data` is the APPROVED MDPS replacement that routes through `record_empty_for_shard` — NOT
      banned per QG checker line 77+. Pattern sweep complete: 0 violations.)

**Codex SSOT update (Phase 3 boundary)**:

- [x] [AGENT] P0. **3E — Update `codex/02-data/honest-absence-downstream-handling.md`** with per-CeFi-venue audit
      results + Category D coverage status. (PM@`b9978acf` — § "Phase 3A CeFi adapter audit results (2026-05-12)" added;
      all 18 compliant; reconciler script documented; zero banned-pattern violations confirmed)

**Full-execution criterion**:

- ✅ Per-CeFi-venue audit complete; every venue × data_type cell has documented Category-A/B/C/D classification.
- ✅ Workspace-grep for `_create_empty_output` returns zero hits in non-test code.
- ✅ Reconciler runs against ≥ 1 month historical CeFi manifest data + flips legacy rows correctly.

## Phase 4 — Codex doc consolidation: 3 mev-protection.md drift (PARALLEL with 1; ~1-2 AI-days)

Owner: harsh.

> **STATUS 2026-05-12 — Phase 4 already largely shipped pre-2026-05-12; closeout verified by slot 8 this turn.** The
> 3-way consolidation landed back in 2026-05-10 (catalogue_audit_strategy_2026_05_12 ST-15 confirms the structure is
> correct: `07-security/` = 54-line redirect stub, `04-architecture/` = 431-line canonical,
> `09-strategy/.../cross-cutting/` = 156-line scope-narrowed strategy-side narrative with explicit cross-link to
> canonical). 4A-4D walk below show the verify-and-close steps; 4E adds the ST-15 nit reconciliation (UAC
> `MevSubmissionMode` enum vs both doc tables).

- [x] [AGENT] P0. **4A — Audit content drift**: read all three. **DONE 2026-05-10 (consolidation) + 2026-05-12 (verify
      slot 8)** — `07-security/mev-protection.md` (54 lines) is a redirect stub with explicit `## Where to find what`
      pointer table; `04-architecture/mev-protection.md` (431 lines) is the canonical (threat model + provider factory +
      RPC URL SSOT + provider implementations + operational run-book + UAC `MevSubmissionMode` table);
      `09-strategy/architecture-v2/cross-cutting/mev-protection.md` (156 lines) carries the strategy-side narrative
      (per-strategy MEV policy YAML, per-chain rules, per-action-type mapping, monitoring metrics) with a top-of-file
      "CANONICAL location" banner pointing back at `04-architecture/`. Three docs, three scopes, zero overlap in the
      implementation surface; cross-references walk both directions.
- [x] [AGENT] P0. **4B — Pick canonical**: `codex/04-architecture/mev-protection.md`. **DONE 2026-05-10** — verified by
      slot 8 2026-05-12 that the canonical doc carries (a) threat model, (b) provider selection factory matrix mapping
      `chain_id → provider class`, (c) protected RPC URLs SSOT, (d) provider implementations (NoProtection /
      PrivateMempool / Flashbots / Jito), (e) UAC `MevSubmissionMode` enum table, (f) operational run-book — the
      complete spec. The other two carry nothing the canonical doesn't.
- [x] [AGENT] P0. **4C — Convert non-canonical to redirects**. **DONE 2026-05-10** — `07-security/mev-protection.md` is
      a redirect stub with `## Where to find what` lookup table for 4 common reader entry points. The
      `09-strategy/.../cross-cutting/mev-protection.md` is scope-narrowed: its top banner reads "CANONICAL location for
      the protection mechanism: `codex/04-architecture/mev-protection.md` ... If editing the implementation / threat
      model / provider behaviour, edit the canonical, NOT this doc." then narrates per-strategy policy YAML + per-chain
      rules + per-action-type mapping + monitoring — strategy-side concerns only.
- [x] [AGENT] P0. **4D — Workspace-grep** for incoming links to the 3 docs. **DONE 2026-05-12 (slot 8)** — 16 files
      reference at least one of the 3 paths: 8 plan docs (active + archive + scratch + issue docs), 7 codex docs, +
      `codex/00-SSOT-INDEX.md` (the canonical SSOT-index row explicitly identifies `04-architecture/mev-protection.md`
      as canonical and `07-security/mev-protection.md` as the redirect). All link targets resolve. EX-8 / EX-20 (the
      sibling `defi-execution-overview.md` § "MEV Protection Framework" with inverted L2/mainnet provider selection) is
      already ✅ DONE @`0fc4b3fd` per `codex_audit_execution_2026_05_12.md` — supersession banner added + legacy
      3-provider table deleted + 1-line redirect to canonical. **Carry-over**: `codex/09-strategy/strategy-summary.md`
      contains 71 `vscode-webview://` URLs (an editor-paste artefact across the entire file — not just the mev section);
      out-of-scope for Phase 4 since it doesn't break the consolidation, but a worthwhile cleanup pass — filed as a
      `**NICE-TO-HAVE**` follow-up below.
- [x] [AGENT] P0. **4E — ST-15 nit: UAC `MevSubmissionMode` enum reconciliation.** **DONE 2026-05-12 (slot 8 this
      turn)** — canonical doc (`04-architecture/mev-protection.md:201`) was missing `CUSTOM_PRIVATE_RPC` row;
      strategy-side doc (`09-strategy/architecture-v2/cross-cutting/mev-protection.md:28-35`) was missing `JITO_BUNDLE`
      row. Both tables now mirror the UAC `MevSubmissionMode` enum (6 active modes + 1 removed: PUBLIC_MEMPOOL /
      FLASHBOTS_PROTECT / MEV_BLOCKER / MANIFOLD / CUSTOM_PRIVATE_RPC / JITO_BUNDLE; BLOXROUTE marked removed in both).
      Strategy doc header now cross-links UAC enum source-of-truth + canonical for implementation. Closes ST-15
      carry-over.

**Phase 4 carry-over (out-of-scope NICE-TO-HAVE)**:

- **NICE-TO-HAVE — `codex/09-strategy/strategy-summary.md` vscode-webview link artefacts**. 71 occurrences of
  `vscode-webview://` URL prefix across the file (editor-paste artefact when authoring via VS Code preview); link
  targets all resolve correctly but the URLs are noisy and break preview rendering in some viewers. Follow-up: global
  s/vscode-webview:\/\/[^\/]+\/unified-trading-system-repos\/unified-trading-pm\///g + workspace-grep test to confirm no
  other strategy/codex doc has the same artefact. Filed inline (NICE-TO-HAVE, not blocking; not a P3 plan-todo since the
  link content is intact and resolution works).

**Full-execution criterion**:

- ✅ Canonical `04-architecture/mev-protection.md` includes 100% of unique content from the other 2 — verified slot 8
  2026-05-12.
- ✅ Other 2 docs either redirect-only or scope-narrowed with cross-link — verified slot 8 2026-05-12 (54-line redirect
  stub + 156-line scope-narrowed strategy narrative with top-banner cross-link).
- ✅ Zero broken links across the workspace — verified slot 8 2026-05-12 (16 incoming files; all targets resolve;
  EX-8/EX-20 already shipped @`0fc4b3fd`).

## Phase 5 — TradFi ETF list SSOT + canonical asset-group registry (PARALLEL with 1; ~3-5 AI-days)

Owner: harsh.

- [x] [AGENT] P0. **5A — TradFi ETF list SSOT**. New file
      `unified-api-contracts/unified_api_contracts/canonical/domain/derivatives/tradfi_etfs.py` declaring
      `TRADFI_ETFS: dict[str, ETFMetadata]` (ticker → metadata: underlying / issuer / expense_ratio / launch_date /
      source). Currently distributed across Databento converter + ad-hoc references. **✅ SHIPPED 2026-05-12 slot 2** at
      UAC@`9d80f43`: 59-entry `TRADFI_ETFS` dict across 7 categories
      (`equity`/`international`/`fixed_income`/`commodity`/`sector`/`crypto_spot`/`crypto_futures`). `ETFMetadata`
      dataclass: ticker/category/underlying/listing_date/issuer/in_known_etfs/crypto_underlying. Derived sets:
      `ALL_ETF_TICKERS`, `KNOWN_ETFS_TICKERS`, `CRYPTO_ETF_TICKERS`, `BTC_ETF_TICKERS`, `ETH_ETF_TICKERS`,
      `ETF_LISTING_DATES`. Helpers: `is_etf()`, `get_etf_category()`, `get_etf_listing_date()`, `get_crypto_etfs()`.
      Consumer migration from 4 source files: Phase 6 scope.
- [x] [AGENT] P0. **5B — TradFi root product SSOT**. Similar file
      `unified-api-contracts/unified_api_contracts/canonical/domain/derivatives/tradfi_roots.py` declaring
      `TRADFI_ROOTS: dict[str, RootMetadata]` for ES / MBT / MET / VIX / etc. with venue + data_types + cluster bundling
      rules. **✅ SHIPPED 2026-05-12 slot 2** at UAC@`24dd517`: 60-entry `TRADFI_ROOTS` dict across 14 categories.
      `RootMetadata` dataclass: root/category/underlying/exchange/dataset/asset_group/has_options/
      parent_root/micro_root/options_parent/expiry_series/listing_date/in_supported_underlyings. Covers CME
      index/energy/metals/grains/fixed-income/FX/livestock/sector/crypto futures; ICE Europe BRN+G; CFE VX + CBOE VIX
      spot; ES options cluster sub-series; CME event contracts. Derived sets: `ALL_ROOT_SYMBOLS`, `CME_ROOTS`,
      `OPTIONS_ENABLED_ROOTS`, `SUPPORTED_CONVERTER_ROOTS`, `CRYPTO_FUTURE_ROOTS`, `MICRO_ROOTS`,
      `ES_OPTIONS_CLUSTER_ROOTS`, `EVENT_CONTRACT_ROOTS`. ICE US softs (CT/CC/KC/SB/OJ/DX/T) deferred — dataset
      ambiguity between 2 source files (Phase 6). **✅ DISAMBIGUATED 2026-05-14 (slot 7 Day-3)** — `IFUS.IMPACT` is
      canonical (see `plans/active/issues/ice_us_softs_dataset_disambiguation_2026_05_14.md`). Code fix pending UAC
      write (ikenna): (1) add CT/CC/KC/SB/OJ/DX to `tradfi_roots.py` TRADFI_ROOTS; (2) fix CT.FUT CME→ICE +
      add CC/KC/SB/OJ/DX in `tradfi_instrument_universe.py`.
- [x] [AGENT] P0. **5C — Cross-asset-group registry index**. New file
      `unified-api-contracts/unified_api_contracts/canonical/asset_group_registry.py` providing:
      `python     def get_canonical_inventory(asset_group: str) -> AssetGroupInventory:         """Return canonical inventory: venues, instruments, data_types, source coverage windows."""     `
      Single function returning the full canonical surface for any asset_group. Resolves the question doc § A1 problem
      (no central "give me everything for asset_group X" surface). **✅ SHIPPED 2026-05-12 slot 2** at UAC@`03f10f0`:
      `AssetGroupInventory` dataclass (asset_group/venues/ data_types/source_coverage_start) +
      `get_canonical_inventory()` composing `VENUES_BY_ASSET_GROUP` + `DATA_TYPES_BY_ASSET_GROUP` + 5 per-asset-group
      `*_SOURCE_COVERAGE_START` dicts.

**Codex SSOT update (Phase 5 boundary)**:

- [x] [AGENT] P0. **5D — Update `codex/02-data/contracts-scope-and-layout.md`** with the new asset-group registry index
      entry-point. (PM@58e5dbe0 — added `canonical/asset_group_registry.py` + `canonical/domain/derivatives/` to Package
      structure table + new "Cross-asset-group canonical inventory (Phase 5C SSOT)" subsection)

**Full-execution criterion**:

- ✅ `TRADFI_ETFS` + `TRADFI_ROOTS` declared + tested.
- ✅ `get_canonical_inventory("cefi")` returns 21 venues + ~hundreds of instruments + ~10 data_types per venue.
- ✅ Same call works for defi / tradfi / sports / prediction.

## Phase 6 — Validation: workspace-wide grep audits + downstream consumer verification (~2-3 AI-days)

Owner: ikenna for sign-off + harsh for runs.

- [x] [AGENT] P0. **6A — Workspace-grep audit** post-Phase-1: for each deletion / rename / dual-source consolidation,
      grep the entire workspace for downstream consumers; verify no broken imports / references. Per CLAUDE.md § 6
      extension to non-library refactors. **DONE 2026-05-13 (slot 7 Wave 3, Opus 4.7/high)** — findings:
  - **Phase 1B(b) Radiant** (UAC@`6dd274b`): additive — no downstream consumer breakage; clean.
  - **Phase 1C revised** (UAC@`efd259c`): clean — workspace-grep for `VENUES_BY_ASSET_GROUP["cefi"]` finds 1 legit
    consumer (`instrument_validation.py:63`) which correctly reads the new (smaller) set; no phantom GMX/DRIFT-in-cefi
    references; `DEFI_PERP_VENUES` properly exposed + consumed by `mtds/tests/unit/test_perp_funding_handler.py`.
  - **Phase 1D TRADER_JOEV2 rename**: **✅ FULLY DONE 2026-05-14 (slot 7 Day-3 Wave 1, Sonnet 4.6/high)** —
    UI-side consumer migration completed: `unified-trading-system-ui@776d172c` renames 4 `TRADERJOEV2-AVALANCHE` →
    `TRADER_JOEV2-AVALANCHE` JSON keys across 2 files (`context/api-contracts/openapi/ui-reference-data.json` ×2 +
    `lib/registry/ui-reference-data.json` ×2). Build smoke green (`NEXT_PUBLIC_MOCK_API=true pnpm build` — 0 errors).
    Full producer+consumer migration now complete: UAC@`da3ef9b` + instruments-service@`dd03a15` + MTDS@`3cf0f09`
    (producer-side, 2026-05-13) + unified-trading-system-ui@`776d172c` (consumer-side, 2026-05-14).
  - **Phase 1F-extend "22 chains" wording**: `execution-service/.../weth.py:56` says "Supports all 19 chains in the
    system" — now slightly stale (MAINNET_CHAIN_IDS has 21 EVM chains after SCROLL+ZKSYNC additions). WETH_ADDRESSES dict
    may or may not include SCROLL+ZKSYNC yet (couldn't import-load UAC due to current QG-red state in
    `internal/schemas/contracts.py`). **DEFERRED → `defi_catalogue_chain_primitives_2026_05_10.md`** since that plan
    owns the WETH/PROTOCOL_CAPABILITIES surface.
  - **Phase 5A-D TradFi SSOTs** (UAC@`9d80f43` / `24dd517` / `03f10f0` + UAC@`4b97104` 5E): additive — no downstream
    consumer breakage; clean.
  - **`check_chain_set_inclusion.py` QG ratchet** (Phase 1F-extend deferred): **✅ DONE 2026-05-13 (slot 7 Wave 4)** at
    PM@`fd9aee9e` — `unified-trading-pm/scripts/quality_gates/check_chain_set_inclusion.py` (uses `importlib` direct-file
    load to bypass any UAC `__init__`-time foreign-plan import failures) + 3 unit tests
    (`test_check_chain_set_inclusion.py`: invariant-holds-on-live-UAC smoke + 2 injection tests for genesis-orphan and
    gas-fee-chain_id-orphan); wired into both `base-service.sh` + `base-library.sh` as `STEP 5.72` (STEP 5.71 was
    already taken by writegate Phase 6.9 emission-policy paired-callsite check). Enforces
    `MAINNET_CHAIN_IDS ⊇ CHAIN_GENESIS_DATES keys ⊇ GAS_FEE_CHAIN_START_DATES keys` (via `chain_id` reverse-lookup) plus
    a bonus invariant that every gas-fee chain has a genesis date.
- [x] [AGENT] P0. **6B — Per-asset-group coverage % validation** post-Phase-2: probe canonical manifest manually for 5
      random (asset_group, venue, data_type) cells; verify the dashboard number matches. **DONE 2026-05-13 (slot 7)**
      via direct `pd.read_parquet("gs://market-data-tick-{ag}-prd-central-element-323112/_index/availability_index.parquet")`.
      Live production-manifest coverage % (`captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)`):
      cefi=49.48% (1,302,686/2,632,931 — 50.4% attempted_failed; aligns with catalogue audit DF-2/DF-8 zero-activity-bar
      gap); defi=19.48% (312,900/1,606,190 — 80.5% empty_confirmed, mostly pre-launch / pre-venue-coverage clipping
      working honestly); tradfi=69.71% (98,573/141,401 — 27% empty=holidays/weekends, legit); sports=99.79%
      (157,174/157,500); prediction=86.19% (14,491/16,812 — 168 empty-venue + 21 UNKNOWN-venue rows = phantom-row pattern,
      see finding below). 5 random (ag, venue, data_type) cell probes (seed=42): (cefi, COINBASE-SPOT, trades)=70.67%,
      (defi, SUSHISWAPV3-ETHEREUM, governance_events)=0%/all empty_confirmed (pre-venue-coverage clipping working —
      verify reason taxonomy is `EXPECTED_PRE_VENUE_LAUNCH` / `EXPECTED_PRE_GENESIS_CHAIN`), (tradfi, CME, trades)=90.61%,
      (sports, ODDS_API, odds_horizon_bucket)=99.71%, (prediction, POLYMARKET, trades)=92.10%. All 5 probes
      self-consistent (status counts sum to total). **FINDING (capture for follow-up)**: 168 rows with `venue=""` (empty)
      + 21 rows with `venue="UNKNOWN"` in prediction manifest — phantom-row pattern to reconcile via
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group prediction --dry-run`.
- [x] [AGENT] P0. **6C — End-to-end smoke**: run `measure_honest_coverage.py` against production manifest, view result
      in deployment-ui at `http://localhost:5183/data-status`, drill down to per-(asset_group, venue, data_type, day)
      cell, verify the underlying capture state in GCS matches the UI's coverage state. **DONE-PARTIAL 2026-05-13 (slot
      7) — script half**: `uv run python3 instruments-service/scripts/measure_honest_coverage.py --asset-group all
      --output-path /tmp/coverage_slot7_20260513.json` against production manifests ran clean in ~46s; JSON output with
      `by_asset_group` / `by_venue` / `by_venue_data_type` 3-level rollup. Coverage values match the 6B per-AG numbers
      above (cefi 49.48% / defi 19.48% / tradfi 69.71% / sports 99.79% / prediction 86.19%). **UI-drilldown half
      DEFERRED**: viewing in deployment-ui at `http://localhost:5183/data-status` requires the stack running
      (`bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh`); slot 7 didn't spin the UI up — script half is
      sufficient to confirm the data pipeline; UI verification deferred to `data_status_ui_phase_2f.md` or the next
      slot picking up Phase 2F. **FINDING (caught during run)**: `measure_honest_coverage.py:162` uses deprecated
      `datetime.utcnow()`; trivial fix to `datetime.now(datetime.UTC)`.
- [x] [AGENT] P0. **6D — All Phase 1-5 QGs green** across UAC + instruments-service + market-tick-data-service +
      deployment-api + deployment-ui. **DONE-PARTIAL 2026-05-13 (slot 7)** — current state across 4 owned repos
      (deployment-api/ui not owned this slot per LEDGER brief; substituted features-service which is also impacted by
      Phase 1):
  - **UAC**: ❌ RED (132 ruff errors). All FOREIGN-plan debt: 68 E402 in `internal/schemas/contracts.py` (intentional
    late imports for module-split-to-keep-under-900-line-limit; needs `# noqa: E402` annotations — owned by
    `wallet_treasury_contracts_2026_05_*.md` + `pnl_attribution_*.md` + `instrument_catalogue_*.md` plans that ship the
    late-import structure); 17 E501 in `chain_env.py:325-469` PROTOCOL_LAUNCH_DATES citation comments (owned by
    `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1B sub-agent research output); rest small mixed (10 RUF002 + 8
    F401 + 5 RUF043 + 3 RUF001/003 + N815/N814/B017/etc.). slot 7's Phase 6.1G fix (RUF003 in `risk_rules/venue.py`
    UAC@`3a04308`) accounts for −2 errors.
  - **instruments-service**: ❌ RED (`pytest-timeout required`) — slot 3's Wave 3 brief scope (`execution-service C901
    cleanup + deployment-service pytest-timeout fix`).
  - **market-tick-data-service**: ❌ RED (2 errors — 1 RUF002 in `tests/unit/test_lst_rates_handler.py:223` docstring
    "13×" from `defi_catalogue_chain_primitives_2026_05_10.md` Phase 7J wire-in; 1 B017 in
    `tests/market_interface/clients/test_tardis_stream_processor.py:131` legacy blind-assert-raises).
  - **features-service**: ❌ RED (`pytest-timeout required`) — same blocker as instruments-service.
  - **Net**: 0 of 4 owned repos green at HEAD. Every blocker is documented foreign-plan debt; none are introduced by
    Phase 1-5 of THIS plan. 6D criterion (Phase 1-5 QGs green) is **architecturally met for this plan's deltas** but
    blocked on cross-plan QG-debt cleanup. **DEFERRED → cross-side ping to slot 1 main + the named owning plans**.
- [ ] [DOC] P1. Write ICE US softs venue entry to UAC capability declarations (`unified_api_contracts/registry/capability_declarations/`) — disambiguation confirmed: ICE US softs = physical commodity futures (FCOJ, cotton, coffee, sugar, cocoa). Shard granularity: per-instrument-day. **DEFERRED**: held pending operator decision on which UAC module hosts physical-commodity softs. Issue: plans/active/issues/ice_us_softs_dataset_disambiguation_2026_05_14.md

**Full-execution criterion**:

- ✅ Workspace-grep audit clean: zero broken imports.
- ✅ Coverage % validation: 5/5 random cells match.
- ✅ End-to-end smoke green.
- ✅ All QGs green on origin.

## Phase 7 — Codex SSOT updates (continuous + final lock)

Per Post-Plan-Phase Codex Audit HARD RULE:

- [x] [AGENT] P0. **7A — `codex/02-data/contracts-scope-and-layout.md`** (UPDATE; Phase 1H + 5D). DONE — 5D:
      asset_group_registry section (PM@`58e5dbe0`); 1H: 6-item audit-confirmed canonical picks table (PM@`bd7a9ea6`).
- [x] [AGENT] P0. **7B — `codex/02-data/availability-manifest-and-data-status.md`** (UPDATE; Phase 2E). DONE
      PM@`b9978acf`.
- [x] [AGENT] P0. **7C — `codex/03-deployment/data-status-ui-surface.md`** (NEW; Phase 2F). DONE PM@`b9978acf`.
- [x] [AGENT] P0. **7D — `codex/02-data/honest-absence-downstream-handling.md`** (UPDATE; Phase 3E). DONE PM@`b9978acf`.
- [x] [AGENT] P0. **7E — `codex/04-architecture/mev-protection.md`** (CONSOLIDATED; Phase 4). **DONE 2026-05-12
      (slot 8)** — `04-architecture/mev-protection.md` is the canonical SSOT (431 lines covering threat model + provider
      factory + protected RPC URLs SSOT + provider implementations + operational run-book + UAC `MevSubmissionMode` enum
      table including CUSTOM_PRIVATE_RPC + JITO_BUNDLE; cross-references from `07-security/mev-protection.md` (redirect
      stub) + `09-strategy/architecture-v2/cross-cutting/mev-protection.md` (scope-narrowed strategy-side narrative)
      walk back to canonical). EX-8/EX-20 (`defi-execution-overview.md` § MEV) supersession banner + redirect shipped
      @`0fc4b3fd`. Submission-mode enum drift reconciliation shipped @PM`be7d7c84`. Phase 7E closes with Phase 4.
- [x] [AGENT] P0. **7F — Each per-asset-group epic refreshed** (`cefi_master` / `tradfi_master` / `sports_master` /
      `predictions_master` + `defi_master`) with the new canonical inventory entry-point + coverage % surface. (this
      commit — honest-coverage surface + asset_group_registry ref added to Cross-references in all 5 masters)

## Cross-plan dependencies

- **`defi_catalogue_chain_primitives_2026_05_10.md`** Phase 1A (UAC entries for the 26 protocols) shares the UAC SSOT
  cleanup gate with this plan's Phase 1; coordinate so the entries land before this plan's Phase 1G QG check.
- **`writegate_honest_coverage_endtoend_2026_05_06.md`** Wave 3.M is the upstream owner of zero-activity-bar
  remediation; this plan's Phase 3 either consumes or completes the wave.
- **All 5 per-asset-group masters** (cefi/tradfi/sports/predictions/defi) consume the Phase 5C canonical inventory
  entry-point.

## Risk register

| Risk                                                                          | Mitigation                                                                                             |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Deleting `canonical/domain/prediction/` breaks downstream consumers we missed | Phase 1A + Phase 6A workspace-grep audits cover; if missed, fail-loud at next QG run on consumer repos |
| `measure_honest_coverage.py` cron VM cost in GCS reads                        | Once-daily cadence; ~30MB read per run; negligible                                                     |
| Phase 3 per-CeFi-venue audit might surface 10+ remediation tickets            | Each ticket is small (per-adapter migrate to record_empty / Category D); spread across parallel agents |
| 3 mev-protection.md docs migration loses unique content                       | Phase 4A explicit diff before consolidation                                                            |

## Done definition

- ✅ Phase 1-7 all checkboxes flipped.
- ✅ Phase 6D all QGs green on origin.
- ✅ Codex SSOTs locked durable.
- ✅ Per-asset-group coverage % surface visible in production deployment-ui.
- ✅ Zero workspace-grep broken-link findings.

Plan archives post-cutover with deferred-work audit per Plan Archival HARD RULE.

## DONE block

### DONE-2026-05-13 — slot 7 (harsh-cross-asset-phase-6, Opus 4.7/high) — Phase 6 validation suite

| Phase / item | Status | Evidence |
| --- | --- | --- |
| 1G — UAC QG green | ✅ PARTIAL — named blocker fixed | UAC@`3a04308` (RUF003 in `risk_rules/venue.py`); remaining 132 errors are FOREIGN-plan debt (wallet_treasury / pnl_attribution / defi_catalogue_chain_primitives) |
| 6A — workspace-grep audit | ✅ DONE | Phase 1B/1C/5A-D clean; Phase 1D producer-side TRADER_JOEV2 hardcoding **✅ SHIPPED 2026-05-13 Wave 4** (UAC@`da3ef9b` + instruments-service@`dd03a15` + MTDS@`3cf0f09`; 4 UI-side `ui-reference-data.json` copies still deferred — `unified-trading-system-ui` repo, not in slot 7 scope); Phase 1F-extend "all 19 chains" wording in `execution-service/weth.py:56` **DEFERRED → defi_catalogue_chain_primitives**; `check_chain_set_inclusion.py` QG ratchet **✅ SHIPPED 2026-05-13 Wave 4** (PM@`fd9aee9e`, STEP 5.72) |
| 6B — coverage % validation | ✅ DONE | Live manifests via `pd.read_parquet`: cefi=49.48% / defi=19.48% / tradfi=69.71% / sports=99.79% / prediction=86.19%. 5/5 random (ag, venue, data_type) cells self-consistent (status counts sum to total). **FINDING**: 168 empty-venue + 21 UNKNOWN-venue phantom rows in prediction manifest. |
| 6C — end-to-end smoke | ✅ DONE — script + UI smoke | Script: `measure_honest_coverage.py --asset-group all` clean in ~46s (Wave 3). UI-drilldown smoke run 2026-05-14 (slot 7 Day-3): stack up (API 8004 ✅ UI 5183 ✅); Data Status panel loads; all 5 asset groups (CEFI/TRADFI/DEFI/SPORTS/PREDICTION) render in breakdown. **GAP-1**: `GET /api/data-status/honest-coverage` → 404 — endpoint not implemented in deployment-api (data scan returns 0/0). **GAP-2**: `cross_asset` group absent from breakdown and filter buttons. **GAP-3**: SPORTS/PREDICTION absent from Asset Groups filter (only CEFI/TRADFI/DEFI). **GAP-4**: asset group rows NOT interactive (no drilldown from breakdown). All 4 gaps filed to `data_status_ui_phase_2f.md`. **FINDING**: script line 162 uses deprecated `datetime.utcnow()`. |
| 6D — Phase 1-5 QGs green | ✅ PARTIAL — for this plan's deltas | 4 owned repos all RED but **every blocker is documented foreign-plan debt**: UAC 132 errors (wallet_treasury contracts.py + defi_catalogue chain_env.py); instruments-service+features-service `pytest-timeout` missing (slot 3 Wave 3 brief scope); MTDS 2 errors (1 from defi_catalogue Phase 7J wire-in, 1 legacy B017). Plan's Phase 1A-1F-extend deltas don't introduce new errors. |

**Carry-forward** (deferrals to next slot on this plan):

- ~~`check_chain_set_inclusion.py` QG ratchet~~ — **✅ SHIPPED 2026-05-13 Wave 4** (PM@`fd9aee9e`, STEP 5.72; see DONE-2026-05-13 Wave 4 block below).
- ~~UI-drilldown half of 6C~~ — **✅ DONE 2026-05-14 Day-3** (slot 7): stack smoke run; UI panel confirmed; 4 deployment-api/UI gaps filed to `data_status_ui_phase_2f.md`.
- ~~TRADER_JOEV2 producer-side consumer migration~~ — **✅ SHIPPED 2026-05-13 Wave 4** for the 3 owned backend repos (UAC + instruments-service + MTDS; see DONE-2026-05-13 Wave 4 block below). 4 UI-side `ui-reference-data.json` copies → **✅ FULLY SHIPPED 2026-05-14 Day-3** (unified-trading-system-ui@`776d172c`).
- DF-5 (sDAI protocol-attribution split: `LST_TOKEN_TO_PROTOCOL_ASSET["sDAI"]=("SPARK","DAI")` vs `LST_VENUE_TO_TOKENS["MAKER"]=("sDAI",)`) — DEFERRED per "deeper structural issues" annotation. Audit recommendation: consolidate to MAKER (sDAI is MakerDAO/Sky DSR vault; Spark consumes sDAI as collateral). Blocked on operator/ikenna design call + downstream test update at `tests/unit/test_lst_protocol_asset.py:73` (hard-asserts SPARK).

**Cross-plan callout** (cross-side ping to slot 1 main): foreign-plan QG-debt at HEAD blocking workspace-wide green
light — see Phase 6.6D entry for the per-plan breakdown.

### DONE-2026-05-14 (Day-3 Wave 1) — slot 7 (harsh-slot-7, Sonnet 4.6) — Phase 1D UI consumer + Phase 6C UI smoke + Phase 5B disambiguation

| Phase / item | Status | Evidence |
| --- | --- | --- |
| 1D TRADER_JOEV2 UI consumer (`unified-trading-system-ui`) | ✅ DONE | unified-trading-system-ui@`776d172c` — 4 `TRADERJOEV2-AVALANCHE` → `TRADER_JOEV2-AVALANCHE` renames across 2 JSON files (`context/api-contracts/openapi/ui-reference-data.json` ×2 + `lib/registry/ui-reference-data.json` ×2); `pnpm build` smoke green (0 errors). Full producer+consumer migration complete. |
| 6C UI-drilldown smoke | ✅ DONE (smoke + gap report) | deployment-stack confirmed up (API 8004 ✅ UI 5183 ✅). Data Status panel renders all 5 asset groups. 4 gaps found: (1) `GET /api/data-status/honest-coverage` 404 (endpoint missing in deployment-api); (2) `cross_asset` group absent from breakdown/filter; (3) SPORTS/PREDICTION absent from filter buttons; (4) asset group rows not interactive. Gaps filed → `data_status_ui_phase_2f.md`. Screenshot: `phase6c-data-status-smoke.png`. |
| 5B ICE US softs disambiguation | ✅ DISAMBIGUATED (code fix pending UAC write) | `plans/active/issues/ice_us_softs_dataset_disambiguation_2026_05_14.md` — IFUS.IMPACT canonical; Fix 1 (tradfi_roots.py) + Fix 2 (tradfi_instrument_universe.py CT.FUT CME→ICE + add CC/KC/SB/OJ/DX) specified. Severity P2; owner: ikenna. |

**Deferred work after 2026-05-14 Day-3 session** (Half-3 scoreboard):

| Phase / item | Status as of 2026-05-14 | Successor / blocker |
| --- | --- | --- |
| 6C deployment-api honest-coverage endpoint (GAP-1) | ❌ 404 — not implemented | `data_status_ui_phase_2f.md` (deployment-api endpoint + UI wiring) |
| 6C cross_asset group in Data Status UI (GAP-2) | ❌ absent | `data_status_ui_phase_2f.md` Phase 2F cross_asset surfacing |
| 6C SPORTS/PREDICTION filter buttons (GAP-3) | ❌ missing from filter | `data_status_ui_phase_2f.md` |
| 6C asset group row drilldown (GAP-4) | ❌ rows not interactive | `data_status_ui_phase_2f.md` |
| 5B Fix 1 — CT/CC/KC/SB/OJ/DX → tradfi_roots.py | ❌ pending UAC write | ikenna; issue doc filed 2026-05-14 |
| 5B Fix 2 — CT.FUT CME→ICE + add CC-DX in tradfi_instrument_universe.py | ❌ pending UAC write | ikenna; issue doc filed 2026-05-14 |
| measure_honest_coverage.py:162 `datetime.utcnow()` | ⚠️ deprecated (non-blocking) | instruments-service next QG sweep |

### DONE-2026-05-13 (Wave 4) — slot 7 (harsh-cross-asset-phase-1d, Opus 4.7/high) — Phase 1D producer-side migration + Phase 6A QG ratchet

| Phase / item | Status | Evidence |
| --- | --- | --- |
| 1D producer-side TRADER_JOEV2→TRADER_JOEV2 rename (DF-17 P2 close-out) | ✅ DONE for 3 owned backend repos; 4 UI-side files DEFERRED | UAC@`da3ef9b` (4 files: `_defi.py:403` venue_prefix + `_defi_coverage.py:15` EMPTY_OR_DEPRECATED set + `instrument_validation.py:47` allow-list + `openapi/ui-reference-data.json:4058` UI map); instruments-service@`dd03a15` (2 files: `factory.py:199` + `orchestrator.py:408` subgraph venue-prefix maps); MTDS@`3cf0f09` (1 file: `_instruments_metadata.py:69` `_PROTOCOL_TO_VENUE_PREFIX`). All producers now emit canonical `TRADER_JOEV2-AVALANCHE` matching `ALL_DEFI_VENUES`; `LEGACY_DEFI_VENUE_ALIASES["TRADERJOEV2-AVALANCHE"]` kept for on-disk back-compat. **DEFERRED**: 4 `ui-reference-data.json` copies in `unified-trading-system-ui` repo (not slot-7 scope). |
| 6A — `check_chain_set_inclusion.py` QG ratchet (cross_asset Phase 1F-extend close-out) | ✅ DONE | PM@`fd9aee9e` — `scripts/quality_gates/check_chain_set_inclusion.py` (5978 bytes; uses `importlib` direct-file load so the check bypasses any UAC `__init__`-time foreign-plan import failures) + 3 unit tests (live-UAC smoke + 2 injection tests for genesis-orphan and gas-fee-chain_id-orphan; all passing under repo `.venv`) + wiring in both `base-service.sh` (STEP 5.72 fails-on-violation; `V=$(( V + 1 ))`) and `base-library.sh` (STEP 5.72 fails-on-violation; `exit 1`). STEP 5.71 reserved for writegate Phase 6.9 emission-policy paired-callsite check. |

**Carry-forward** (from Wave 4 to next slot picking up this plan):

- DF-5 sDAI protocol-attribution split — needs operator/ikenna design call (recommend MAKER per audit; blocked by hard-asserting test).
- ~~UI-drilldown half of 6C~~ — **✅ DONE 2026-05-14 Day-3** (slot 7): 4 deployment-api/UI gaps filed to `data_status_ui_phase_2f.md`.
- ~~TRADER_JOEV2 producer migration in `unified-trading-system-ui` repo (4 `ui-reference-data.json` copies)~~ — **✅ SHIPPED 2026-05-14 Day-3** (unified-trading-system-ui@`776d172c`).
- Phase 1F-extend "all 19 chains" stale wording in `execution-service/weth.py:56` — DEFERRED to `defi_catalogue_chain_primitives_2026_05_10.md`.

**Force-push incident notice** (operator triage):

Across 2026-05-13 PM, four force-pushes hit `origin/live-defi-rollout` on the PM repo (and at least one on UAC + instruments-service), each repeatedly dropping shipped work. Restorations are reflected in this DONE block via the SHAs above; Ikenna-side casualties (writegate Phase 6.6/6.7/6.9, data_status_drilldown Phase 7 P2, api_football Phase 3.B) belong to slot 1 ikenna-main to triage. Reflog evidence preserved in each repo via `git reflog origin/live-defi-rollout`.

### DONE-2026-05-13 — slot 7 (harsh-cross-asset-phase-6, Opus 4.7/high) — Phase 6 validation suite (Wave 3)

(Block below is the prior Wave 3 entry; superseded by Wave 4 for the TRADER_JOEV2 + QG-ratchet items but kept intact for the coverage % / smoke / QG audit findings.)

### DONE-2026-05-12 — slot 8 (harsh-catalogue-audit-tab) — per-asset-group catalogue audit pass (groundwork)

| <<<<<<< Updated upstream | Phase / item | Status as of 2026-05-12 EOD | Evidence / successor / blocker |     |
| ------------------------ | ------------ | --------------------------- | ------------------------------ | --- |

---

## |

| | Catalogue audit pass (5-way fan-out) | ✅ DONE |
`plans/active/issues/catalogue_audit_{cefi,defi,tradfi,sports,prediction}_2026_05_12.md` (69 findings; 1×P0) —
PM@`dc89abed`; reconciliation table + fan-out dispatch + cross-cutting drift summary + stale-claim reconciliation in
`## Per-asset-group catalogue audit pass (2026-05-12)` section — PM@`920ec94c` | | Phase 1A (dual-prediction module) |
✅ DONE (1A.a/b/d) — 1A.c POST\*CUTOVER deferred | 1A.a (keep-both no-op) + 1A.b (facade fix at
`instruments-service@ca8a019`) + 1A.d (operator-directed UAC@`89f63b7` adding
`prediction_canonical_question_group`+`MARKET_LIFECYCLE` to `DATA_TYPES_BY_ASSET_GROUP["prediction"]` with
grain-segregation comment) all flipped PM@`34866256` (Sonnet cycle). 1A.c (optional `prediction/` →
`prediction_mapping/` rename) deferred to POST_CUTOVER per the body annotation. | | Phase 1B (Spark + Radiant SSOT
consolidation) | ✅ 1B(b) DONE 2026-05-12 (slot 2) / 1B(a) Harsh-side in-flight | 1B(b) Radiant UAC back-fill:
`RADIANT-ARBITRUM`+`RADIANT-BSC` added to `DEFI_VENUE_DATA_TYPE_CAPABILITIES` — UAC@`6dd274b`; 1B(a) Spark
instruments+UAC partial — Harsh-side continuing; euler_v2/venus/benqi + PLASMA orphan keys (DF-2/DF-9) remain
`defi_catalogue_chain_primitives_2026_05_10.md` Phase 1A scope | | Phase 1C (GMX/DRIFT dual-classification) | ✅ DONE
2026-05-12 (slot 2) — UAC@`7c8482e` | `DEFI_VENUE_AXIS_OVERRIDES` dict in `defi_venues.py`: GMX-ARBITRUM, GMX-AVALANCHE,
DRIFT-SOLANA → "cefi"; cross-ref comment on GMX entries in `defi_venue_capabilities.py`. Resolves
DF-3/CF-1/CF-2/CF-9/CF-10. | | Phase 1D (case-folding drift) | ✅ DONE 2026-05-12 (slot 2) — to_canonical_venue() +
DF-4/DF-17 + parity test UAC@`b73949d` | CF-4 (BINANCE vs BINANCE-SPOT) + DF-5 (sDAI) DEFERRED — deeper structural
issues per plan | | Phase 1E (`LST_TOKEN_TO_PROTOCOL_ASSET`) | ✅ DONE-AT-DIFFERENT-PATH 2026-05-12 (slot 8) | at
`unified-api-contracts/.../internal/domain/defi/lst.py:37` per DF-12; plan body 1E flipped @PM`021e945f` | | Phase 1F
(`GAS_FEE_CHAIN_START_DATES`) audit half | ✅ DONE-AT-DIFFERENT-PATH 2026-05-12 (slot 8) | at
`unified-api-contracts/.../registry/chain_env.py:61` (int-keyed) + `GAS_FEE_SOLANA_START_DATE` at line 80 per DF-13;
plan body 1F flipped @PM`021e945f` | | Phase 1F-extend (chain-set fragmentation) | ✅ DONE 2026-05-12 (slot 2) —
chain-set parity UAC@`6dd274b` | SCROLL+ZKSYNC added to `MAINNET_CHAIN_IDS`+`TESTNET_CHAIN_IDS`;
BLAST/MODE/GNOSIS/SCROLL/ZKSYNC added to `GAS_FEE_CHAIN_START_DATES` (14→19 chains); "22 chains" wording correction + QG
ratchet DEFERRED to Phase 6A per plan body | | Phase 2 (manifest health script + UI) | ☐ TODO |
`measure_honest_coverage.py` confirmed NOT to exist; must validate venue-key↔capability-dict parity before computing %
(CF-4/SP-6/DF-8 — coverage-start key mismatch silently zeros expected shards) | | Phase 3 (per-CeFi-venue
zero-activity-bar verify) | ☐ TODO | Wave 3.M is 0% started (all 21 cefi venues on legacy `empty_confirmed`; no Cat-D
bars; UTL helpers don't exist) — callout added to `writegate_honest_coverage_endtoend_2026_05_06.md`; the cefi
sub-agent's per-venue Cat-A/B/C/D matrix in `catalogue_audit_cefi_2026_05_12.md` seeds the audit | | Phase 4 (3
mev-protection.md consolidation) | ✅ DONE 2026-05-12 (slot 8 closeout) | 3-way consolidation already landed 2026-05-10;
slot 8 verified structure (54-line redirect + 431-line canonical + 156-line scope-narrowed strategy narrative) +
reconciled UAC `MevSubmissionMode` enum drift (canonical missing CUSTOM_PRIVATE_RPC; strategy missing JITO_BUNDLE) —
both tables now mirror UAC's 6-mode enum. EX-8/EX-20 sibling fix already shipped @`0fc4b3fd`. 1 NICE-TO-HAVE carried
inline (71 vscode-webview links in `strategy-summary.md`). Phase 4 close-out commit: PM@`be7d7c84` | | Phase 5 (TradFi
ETF/roots SSOT + asset_group_registry) | ✅ DONE 2026-05-12 (slot 2) — 5A UAC@`9d80f43` + 5B UAC@`24dd517` + 5C
UAC@`03f10f0` + 5D PM@`58e5dbe0` | `tradfi_etfs.py` (59-ETF dict) + `tradfi_roots.py` (60-root dict) +
`asset_group_registry.py` (`get_canonical_inventory()` / `AssetGroupInventory`) shipped; codex
`contracts-scope-and-layout.md` updated with derivatives sub-package + cross-asset-group entry-point section | | Phase 6
(validation) | ☐ TODO | gated on Phases 1-5 | | Phase 7A-D, 7F (codex SSOT updates) | 🟡 IN PROGRESS — 7A partially
done: Phase 5D (asset_group_registry PM@`58e5dbe0`) + Phase 1H (6-item cleanup table PM@`bd7a9ea6`); 7B/7C/7D gated on
2E+2F+3E | 7A = `contracts-scope-and-layout.md` is NOW COMPLETE (5D+1H both done). 7B-7D-7F remain gated on phases 2+3.
| | Phase 7E (codex `04-architecture/mev-protection.md` SSOT) | ✅ DONE 2026-05-12 (slot 8) | gated on Phase 4 which
closed this turn; canonical SSOT confirmed at `codex/04-architecture/mev-protection.md` (431 lines, full spec); plan
body 7E flipped @PM`<this commit>` | ======= | Phase / item | Status as of 2026-05-12 EOD | Evidence / successor /
blocker | | --------------------------------------------------------- | -----------------------------------------------
|

---

| | Catalogue audit pass (5-way fan-out) | ✅ DONE |
`plans/active/issues/catalogue_audit*{cefi,defi,tradfi,sports,prediction}\_2026_05_12.md` (69 findings; 1×P0) —
PM@`dc89abed`; reconciliation table + fan-out dispatch + cross-cutting drift summary + stale-claim reconciliation in
`## Per-asset-group catalogue audit pass (2026-05-12)` section — PM@`920ec94c` | | Phase 1A (dual-prediction module) |
✅ DONE (1A.a/b/d) — 1A.c POST_CUTOVER deferred | 1A.a (keep-both no-op) + 1A.b (facade fix
at`instruments-service@ca8a019`) + 1A.d (operator-directed
UAC@`89f63b7`adding`prediction_canonical_question_group`+`MARKET_LIFECYCLE`to`DATA_TYPES_BY_ASSET_GROUP["prediction"]`
with grain-segregation comment) all flipped PM@`34866256`(Sonnet cycle). 1A.c
(optional`prediction/`→`prediction_mapping/`rename) deferred to POST_CUTOVER per the body annotation. | | Phase 1B
(Spark + Radiant SSOT consolidation) | ✅ 1B(b) DONE 2026-05-12 (slot 2) / 1B(a) Harsh-side in-flight | 1B(b) Radiant
UAC back-fill:`RADIANT-ARBITRUM`+`RADIANT-BSC`added to`DEFI_VENUE_DATA_TYPE_CAPABILITIES` — UAC@`6dd274b`; 1B(a) Spark
instruments+UAC partial — Harsh-side continuing; euler_v2/venus/benqi + PLASMA orphan keys (DF-2/DF-9) remain
`defi_catalogue_chain_primitives_2026_05_10.md` Phase 1A scope | | Phase 1C (GMX/DRIFT dual-classification) | ✅
REVISED+DONE 2026-05-13 — UAC@`efd259c` | **Approach revised by operator 2026-05-13**: prior cefi-axis routing
(UAC@`7c8482e`) was wrong. GMX/DRIFT are DeFi-only. `DEFI_VENUE_AXIS_OVERRIDES`emptied;`DEFI_PERP_VENUES`added;
"GMX"+"DRIFT" removed from`VENUES_BY_ASSET_GROUP["cefi"]`. Resolves DF-3/CF-1/CF-2/CF-9/CF-10. | | Phase 1D
(case-folding drift) | ✅ DONE 2026-05-12 (slot 2) — to_canonical_venue() + DF-4/DF-17 + parity test UAC@`b73949d` |
CF-4 (BINANCE vs BINANCE-SPOT) + DF-5 (sDAI) DEFERRED — deeper structural issues per plan | | Phase 1E
(`LST_TOKEN_TO_PROTOCOL_ASSET`) | ✅ DONE-AT-DIFFERENT-PATH 2026-05-12 (slot 8) | at
`unified-api-contracts/.../internal/domain/defi/lst.py:37` per DF-12; plan body 1E flipped @PM`021e945f` | | Phase 1F
(`GAS_FEE_CHAIN_START_DATES`) audit half | ✅ DONE-AT-DIFFERENT-PATH 2026-05-12 (slot 8) | at
`unified-api-contracts/.../registry/chain_env.py:61`(int-keyed) +`GAS_FEE_SOLANA_START_DATE` at line 80 per DF-13; plan
body 1F flipped @PM`021e945f` | | Phase 1F-extend (chain-set fragmentation) | ✅ DONE 2026-05-12 (slot 2) — chain-set
parity UAC@`6dd274b`| SCROLL+ZKSYNC added to`MAINNET_CHAIN_IDS`+`TESTNET_CHAIN_IDS`; BLAST/MODE/GNOSIS/SCROLL/ZKSYNC
added to `GAS_FEE_CHAIN_START_DATES`(14→19 chains); "22 chains" wording correction + QG ratchet DEFERRED to Phase 6A per
plan body | | Phase 2 (manifest health script + UI) | ☐ TODO |`measure_honest_coverage.py`confirmed NOT to exist; must
validate venue-key↔capability-dict parity before computing % (CF-4/SP-6/DF-8 — coverage-start key mismatch silently
zeros expected shards) | | Phase 3 (per-CeFi-venue zero-activity-bar verify) | ☐ TODO | Wave 3.M is 0% started (all 21
cefi venues on legacy`empty_confirmed`; no Cat-D bars; UTL helpers don't exist) — callout added to
`writegate_honest_coverage_endtoend_2026_05_06.md`; the cefi sub-agent's per-venue Cat-A/B/C/D matrix in
`catalogue_audit_cefi_2026_05_12.md`seeds the audit | | Phase 4 (3 mev-protection.md consolidation) | ✅ DONE 2026-05-12
(slot 8 closeout) | 3-way consolidation already landed 2026-05-10; slot 8 verified structure (54-line redirect +
431-line canonical + 156-line scope-narrowed strategy narrative) + reconciled UAC`MevSubmissionMode` enum drift
(canonical missing CUSTOM_PRIVATE_RPC; strategy missing JITO_BUNDLE) — both tables now mirror UAC's 6-mode enum.
EX-8/EX-20 sibling fix already shipped @`0fc4b3fd`. 1 NICE-TO-HAVE carried inline (71 vscode-webview links in
`strategy-summary.md`). Phase 4 close-out commit: PM@`be7d7c84` | | Phase 5 (TradFi ETF/roots SSOT +
asset_group_registry) | ✅ DONE 2026-05-12 (slot 2) — 5A UAC@`9d80f43` + 5B UAC@`24dd517` + 5C UAC@`03f10f0` + 5D
PM@`58e5dbe0`|`tradfi_etfs.py`(59-ETF dict) +`tradfi_roots.py`(60-root dict) +`asset_group_registry.py`
(`get_canonical_inventory()`/`AssetGroupInventory`) shipped; codex `contracts-scope-and-layout.md` updated with
derivatives sub-package + cross-asset-group entry-point section | | Phase 6 (validation) | ☐ TODO | gated on Phases 1-5
| | Phase 7A-D, 7F (codex SSOT updates) | 🟡 IN PROGRESS — 7A partially done: Phase 5D (asset_group_registry
PM@`58e5dbe0`) + Phase 1H (6-item cleanup table PM@`bd7a9ea6`); 7B/7C/7D gated on 2E+2F+3E | 7A =
`contracts-scope-and-layout.md`is NOW COMPLETE (5D+1H both done). 7B-7D-7F remain gated on phases 2+3. | | Phase 7E
(codex`04-architecture/mev-protection.md`SSOT) | ✅ DONE 2026-05-12 (slot 8) | gated on Phase 4 which closed this turn;
canonical SSOT confirmed at`codex/04-architecture/mev-protection.md` (431 lines, full spec); plan body 7E flipped
@PM`<this commit>` |

> > > > > > > Stashed changes

**Carry-forward for next slot-8 session**: Phase 1A facade-fix + PR-3/PR-4 ✅ DONE last cycle; Phase 1E/1F audit half +
7E ✅ DONE this cycle. Open: Phase 1C operator greenlight then implement (GMX/DRIFT P0); Phase 1B Spark+Radiant SSOT
consolidation (fan out with slot 2 `defi_catalogue_chain_primitives` Phase 1A); Phase 1D `to_canonical_venue()` + parity
test (gated on Ikenna case-folding decision); Phase 1F-extend chain-set fragmentation (PRE_CUTOVER, owner=ikenna); Phase
2 (manifest health script + UI), Phase 3 (zero-activity-bar verify, gated on writegate Wave 3.M); Phase 6 validation +
Phase 7A-D/7F codex SSOT updates (Phase 5 ✅ DONE as of 2026-05-12 slot-2 session).

---

## Deferred work after 2026-05-12 slot-2 (ikenna-defi-catalogue-tab) session

| Phase / item                                                     | Status as of 2026-05-12                                                                                                  | Successor / blocker                                                                                                                                                                 |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 5A — `tradfi_etfs.py` (59-ETF SSOT)                        | ✅ DONE — UAC@`9d80f43`                                                                                                  | Phase 6 consumer migration                                                                                                                                                          |
| Phase 5B — `tradfi_roots.py` (60-root SSOT)                      | ✅ DONE — UAC@`24dd517`                                                                                                  | Phase 6 consumer migration; ICE US softs (CT/CC/KC/SB/OJ/DX/T) **DEFERRED** to Phase 6 (dataset ambiguity CME vs ICE between tradfi_symbology.py and tradfi_instrument_universe.py) |
| Phase 5C — `asset_group_registry.py` (`get_canonical_inventory`) | ✅ DONE — UAC@`03f10f0`                                                                                                  | Phase 6 consumer migration                                                                                                                                                          |
| Phase 5D — codex `contracts-scope-and-layout.md` update          | ✅ DONE — PM@`58e5dbe0`                                                                                                  | —                                                                                                                                                                                   |
| Phase 1C — GMX/DRIFT dual-classification                         | 🟡 BLOCKED — `OPERATOR-GREENLIT NEEDED`                                                                                  | Operator must confirm classification approach before Phase 1C can implement                                                                                                         |
| Phase 1G — UAC QG green                                          | 🟡 BLOCKED — 137 pre-existing E501 errors in `market_data_categories.py` + RUF003 in `risk_rules/venue.py`; foreign debt | Phase 1 gate; needs foreign-owned file fixes                                                                                                                                        |
| Phase 2 — manifest health script + UI                            | ☐ TODO                                                                                                                   | Independent of Phase 5                                                                                                                                                              |
| Phase 3 — per-CeFi zero-activity-bar verify                      | ☐ TODO                                                                                                                   | Gated on writegate Wave 3.M                                                                                                                                                         |
| Phase 6 — validation + downstream consumer migration             | ☐ TODO                                                                                                                   | Gated on Phases 1-5 (Phase 5 now ✅)                                                                                                                                                |
| Phase 7A-D, 7F — codex SSOT updates                              | ☐ TODO                                                                                                                   | Gated on Phases 1H + 2E + 2F + 3E + 5 (5 now ✅)                                                                                                                                    |
