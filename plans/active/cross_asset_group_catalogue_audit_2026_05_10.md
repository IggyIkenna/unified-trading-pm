---
name: cross-asset-group-catalogue-audit
overview: Cross-asset-group SSOT cleanup (UAC dual-prediction module pick / Spark+Radiant SSOT consolidation / GMX+DRIFT dual-classification / TradFi ETF list SSOT) + per-asset-group manifest coverage % UI surface + measure_honest_coverage.py script + per-CeFi-venue zero-activity-bar verification (writegate Wave 3.M dependency). May-23 cutover scope per all-in operator directive.
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
   `LST_TOKEN_TO_PROTOCOL_ASSET` location unverified; `GAS_FEE_CHAIN_START_DATES` referenced but not located;
   3-way mev-protection.md codex drift; case-folding drift between `VENUES_BY_ASSET_GROUP` (uppercase) and
   `_BASE_VENUES_BY_ASSET_GROUP` (lowercase).
2. **Manifest health % per asset_group** (E5 finding): no central honest-coverage % UI surface; coverage logic
   exists at row level (`deployment-api/tests/unit/test_capture_status_csv_bodies.py` + sibling tests) but no
   aggregate per-(asset_group, venue, data_type) coverage report.
3. **`measure_honest_coverage.py` script absent** (referenced in CLAUDE.md memory 2026-05-07 evening but not
   located in repo).
4. **Per-CeFi-venue zero-activity-bar verification** (E1 finding): writegate Phase 3.D.5 Wave 3.M adapter audit
   PENDING — some CeFi venues may still emit legacy NaN placeholder bars instead of zero-activity bars (D-category).

Per all-in-scope directive 2026-05-10: all of these are P0-P1 May-23 scope. This plan owns the cross-asset-group
half of the catalogue work; per-protocol DeFi catalogue lives in
[`defi_catalogue_chain_primitives_2026_05_10.md`](defi_catalogue_chain_primitives_2026_05_10.md).

## Pre-audit reference

Question doc § Block A1 (canonical SSOTs per asset_group) + § Block A3 (manifest health %) + § Block E1-E5 (cross-
asset-group catalogue gap-check) + § "Codex doc inventory + ambiguity" + § "Items NOT verified in this audit pass".
Concrete pre-audit deltas:

- **A1 — UAC dual-prediction modules**: `canonical/domain/prediction/__init__.py` + `canonical/domain/predictions/__init__.py`
  both exist. Latter is canonical per `predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`.
- **A1 — Case-folding drift**: `VENUES_BY_ASSET_GROUP` (uppercase, e.g. `BINANCE-SPOT`) vs
  `_BASE_VENUES_BY_ASSET_GROUP` (lowercase, `binance / okx / bybit`).
- **Cat-2 — Spark ghost**: `defi_venue_capabilities.py:115` declares Spark live (Ethereum 2024-01-01); zero
  instruments-service / MTDS / connector. Cat-2 — Radiant orphan: `instruments-service/reference_data/adapters/defi/radiant.py`
  exists but no UAC entry.
- **Cat-5 — GMX + DRIFT dual classification**: in both UAC `defi_venue_capabilities.py:130-131` AND
  `VENUES_BY_ASSET_GROUP["cefi"]`.
- **E2 — TradFi ETF list**: not at single SSOT, distributed across Databento converter + VIX layering rule + ETF
  list (location unconfirmed).
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

> **🔴 BIG FINDING 2026-05-12 — Phase 1A as originally written is WRONG; re-framed below.** The catalogue
> audit found `canonical/domain/prediction/` (singular) and `canonical/domain/predictions/` (plural) are NOT
> redundant duplicates — singular = cross-venue mapping (`PredictionMarketMapper` etc.), plural =
> canonical-question-group taxonomy. Executing "delete the singular module" breaks
> `instruments-service/.../adapters/prediction/polymarket.py:25` and loses the cross-venue-mapping feature.
> (Already independently caught on the DeFi side — `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1F.)
> 1A re-scoped to "keep both + fix the one deep-import consumer + optional post-cutover rename". Operator
> flagged in chat 2026-05-12 + `plans/active/_agent_pings.md`.

Five per-asset-group catalogue drift reports landed (`plans/active/issues/catalogue_audit_{asset_group}_2026_05_12.md`),
each cross-referencing UAC capability declarations / coverage-start windows / instruments-service adapters / MTDS
adapters / execution connectors. Aggregate: **69 findings** (1×P0, ~21×P1, ~40×P2, ~7×P3).

| asset_group | issue doc | # findings | Headline drift | Fan-out → |
| ----------- | --------- | ---------- | -------------- | --------- |
| defi | [`catalogue_audit_defi_2026_05_12.md`](issues/catalogue_audit_defi_2026_05_12.md) | 20 (DF-1..DF-20) | GMX/DRIFT dual-classified (P0, DF-3); euler_v2/radiant/venus/benqi in `MTDS_DEFI_VENUES`+instruments-service but ZERO UAC `PROTOCOL_CAPABILITIES`/`DEFI_VENUE_DATA_TYPE_CAPABILITIES` rows → phantom-row risk (DF-2); "22 chains" claim matches no list (`MAINNET_CHAIN_IDS`=19 / `CHAIN_GENESIS_DATES`=21 / `CHAIN_CONFIGS`=35 / `GAS_FEE_CHAIN_START_DATES`=14, DF-7) | Phase 1C (GMX/DRIFT + DF-10 GMX-shape), Phase 1D (`SOLBLAZE`/`BLAZESTAKE`, `TRADER_JOEV2`/`TRADERJOEV2`, `sDAI` split), Phase 1F (chain-set SSOT + "22 chains" wording); `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1A (euler/radiant/venus/benqi UAC back-fill) + Phase 2-3 (9 vault primitives + `vault_share_price`); `defi_master_2026_05_07.md` (`ORACLE_COVERAGE_START["chainlink"]`) |
| cefi | [`catalogue_audit_cefi_2026_05_12.md`](issues/catalogue_audit_cefi_2026_05_12.md) | 16 (CF-1..CF-16) | **Wave 3.M zero-activity-bars 0% started** — all 21 CeFi venues still on legacy `empty_confirmed` (Cat A) path; no Cat-D zero-activity bars; UTL `zero_activity_bars` + `get_prior_ltp` helpers don't exist yet (CF-15); `BINANCE` vs `BINANCE-SPOT` coverage-start/data_type-capability key mismatch silently skips ≥8 cefi venues in honest-coverage % (CF-4/7/8); GMX/DRIFT cefi-side ghosts (CF-1/2/9/10, composes with DF-3); 1 banned-pattern (`try/except ImportError` + `# type: ignore` Drift fallback in execution-service, CF-16) | Phase 3 (consumes Wave 3.M; this plan's Phase 3 was already scoped to it); Phase 1C/1D (GMX/DRIFT + case-folding); `writegate_honest_coverage_endtoend_2026_05_06.md` Wave 3.M (callout added); `cefi_master_2026_05_07.md` (coverage-key + data_type rows + instruments-id reconcile); execution-service QG (CF-16) |
| tradfi | [`catalogue_audit_tradfi_2026_05_12.md`](issues/catalogue_audit_tradfi_2026_05_12.md) | 10 (TF-1..TF-10) | E2 confirmed + fully located: ETF universe fragmented across **4** files (`KNOWN_ETFS` `tradfi_symbology.py:459` / `ETF_TICKERS` `tradfi_ticker_universe.py:295` / `_BTC_SPOT_ETFS`+`_ETH_SPOT_ETFS` `tradfi_instrument_universe.py:151` / `TRADFI_TICKER_COVERAGE_START` ETF subset) with divergent membership; futures-roots across **3** (`TRADFI_INSTRUMENTS` / `TRADFI_DATABENTO_INSTRUMENTS` / hard-coded `SUPPORTED_UNDERLYINGS` in `databento_cme_converter.py:57`); VIX-15m constants live in `registry/data_source_continuity.py` NOT `canonical/crosscutting/honest_coverage.py` as CLAUDE.md claims (TF-7); no `futures_chain` data_type for any TradFi venue + `options_chain` only at CME despite OPRA coverage-start (TF-6) | Phase 5A (`tradfi_etfs.py`), Phase 5B (`tradfi_roots.py`), Phase 5C (`asset_group_registry.py`), Phase 7 (codex + CLAUDE.md VIX-pointer fix); `tradfi_master_2026_05_07.md` (`futures_chain`/OPRA options, `CFE`-vs-`CBOE`, `ICE` missing from coverage dict) |
| sports | [`catalogue_audit_sports_2026_05_12.md`](issues/catalogue_audit_sports_2026_05_12.md) | 12 (SP-1..SP-12) | URDI / sports-execution adapter layer (~20 sportsbook/exchange/aggregator keys) NOT checked out in any worktree → error-classification + typed-empty-reason + cluster-validation + capability-vs-method reconciliation all unverified (SP-12); venue-id casing drift spans 5 sports SSOTs (SP-3, wider than Phase 1D's current scope); `KNOWN_COVERAGE_GAPS = {}` contradicts the 2026-05-11 phantom-recon STANDINGS/SFI_LEAGUES/INJURIES pre-launch clusters (SP-6); no `LINEUPS_PRE/POST` split confirmed clean (SP-9) | Phase 1D (widen to cover SP-3); `sports_master_2026_05_07.md` (SP-1/2/4/5/6/7/10); **new URDI-side reconciliation owner needed** (SP-12 + URDI half of SP-10) — flag to operator |
| prediction | [`catalogue_audit_prediction_2026_05_12.md`](issues/catalogue_audit_prediction_2026_05_12.md) | 11 (PR-1..PR-11) | **Phase 1A mis-framed** (PR-1 — see BIG FINDING banner above); `prediction_canonical_question_group` + `MARKET_LIFECYCLE` are live manifest-emitting data_types but absent from `DATA_TYPES_BY_ASSET_GROUP["prediction"]` (only `["trades"]`) → coverage-% aggregators under-count prediction shards (PR-3/PR-4); `MARKET_LIFECYCLE` instruments→MTDS parquet wiring + `PREDICTION_GROUPS` cluster registry are still open temporary-states (PR-5/PR-6); MANIFOLD orphan key (PR-7) | Phase 1A (re-word + fold in PR-3/PR-4); `predictions_master_2026_05_07.md` (PR-4/PR-6/PR-7/PR-11); `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1F (cross-link the keep-both decision) |

**Cross-cutting drift surfaced by ≥2 sub-agents** (highest-leverage fixes): (1) **GMX/DRIFT dual-classification** —
flagged on both the defi side (DF-3, P0) and cefi side (CF-1/CF-2); Phase 1C owns it but is unstarted. (2)
**venue-id casing drift** — `VENUES_BY_ASSET_GROUP` (uppercase) vs `_BASE_VENUES_BY_ASSET_GROUP` (lowercase) vs
per-source capability dicts (lowercase) hits cefi (CF-3), sports (SP-3), and the defi venue-keyed dicts in a
different form (DF-4/5/17); Phase 1D should ship a `to_canonical_venue()` helper + a test that enumerates *every*
venue-keyed dict across all asset_groups and asserts no key drift. (3) **coverage-start key mismatch** — denominator
dicts keyed by a venue spelling the manifest doesn't use silently zero out the expected shard count for those venues
(cefi CF-4/7/8, sports SP-6, defi DF-8); the Phase 2 `measure_honest_coverage.py` script must validate key-set
parity between the capability dict and the venue list before computing %.

Stale-claim reconciliation across all 5: of the 2026-05-08 pre-audit deltas — **2 fully RESOLVED** (`LST_TOKEN_TO_PROTOCOL_ASSET`
located at `internal/domain/defi/lst.py:37`; `GAS_FEE_CHAIN_START_DATES` located at `chain_env.py:61`), **~4
PARTIALLY-RESOLVED** (Spark ghost → now instruments+UAC done, MTDS-generic, no connector; Radiant orphan → now in
`ALL_DEFI_VENUES`+`DEFI_VENUE_PHASE`+`MarginModel` but not `PROTOCOL_CAPABILITIES`; case-folding drift → still open in
multiple forms; Tardis coverage dates → BITGET pinned, others TODO/missing), **~3 STILL-OPEN** (GMX/DRIFT
dual-classification; "22 chains"; TradFi ETF SSOT — `tradfi_etfs.py`/`tradfi_roots.py`/`asset_group_registry.py`
confirmed NOT to exist, so Phase 5 is genuinely unimplemented). Phase 1A's premise (delete singular `prediction/`)
is REJECTED. Each sub-agent's `## Stale-claim reconciliation` section has the per-delta detail.

## Phase 1 — UAC SSOT cleanup (SEQUENTIAL gate; ~3-5 AI-days)

Owner: ikenna (cross-cutting design); harsh implements + downstream consumer updates.

- [ ] [AGENT] P0. **1A — UAC dual-prediction module RECONCILE (re-scoped 2026-05-12 — NOT a delete).** Per
      [`catalogue_audit_prediction_2026_05_12.md`](issues/catalogue_audit_prediction_2026_05_12.md) PR-1/PR-2 +
      `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1F: `canonical/domain/prediction/` (singular,
      cross-venue mapping — `PredictionMarketMapper` etc.) and `canonical/domain/predictions/` (plural,
      canonical-question-group taxonomy) are BOTH canonical and non-redundant. **Sub-todos (each its own shippable
      unit; needs a venv-equipped checkout — the slot-8 worktree has no per-repo `.venv`, so QG-verify in main or hand
      to a slot with one):**
      - [x] [SCRIPT] P0. **1A.a — KEEP BOTH** (no-op confirmation; `prediction/` is NOT deleted). Mark the original
            "delete singular" instruction VOID. (confirmed by prediction sub-agent 2026-05-12 — no code change needed)
      - [x] [SCRIPT] P0. **1A.b — facade-import fix (PR-2).** `instruments-service/instruments_service/reference_data/adapters/prediction/polymarket.py:25-27`: (instruments-service@`ca8a019` 2026-05-12)
            `from unified_api_contracts.canonical.domain.prediction import (PredictionMarketMapper,)` → `from
            unified_api_contracts.prediction import (PredictionMarketMapper,)` (the facade `unified_api_contracts/prediction.py`
            does `from unified_api_contracts.canonical.domain.prediction import *`, and `PredictionMarketMapper` is a
            non-underscore re-export → resolves clean; QG `check_uac_import_surface` then passes for this consumer).
            **Note (out of 1A scope, file separately)**: the same file lines 28-36 also have deep `canonical.domain.sports`
            imports (`build_*_prediction_id`, `POLYMARKET_MARKET_TO_CANONICAL`, `_slug`, ...) — those are a *separate*
            UAC-import-surface violation; route to `sports_master_2026_05_07.md` or a `plans/active/issues/` doc, not here
            (sports facade re-export coverage needs checking first; don't break it as a side-effect of the prediction fix).
      - [x] [DESIGN P0 — operator-directed] **1A.d — PR-3/PR-4.** (UAC@`89f63b7` 2026-05-12 — operator directed Sonnet continuation to ship despite gotcha; grain-segregation comment added inline; downstream completion_pct aggregators must not mix with instrument-day grain)
            🟡 **GOTCHA found on deeper read (slot 8, 2026-05-12) — contradicts the earlier "no operator gate" framing.**
            `DATA_TYPES_BY_ASSET_GROUP["prediction"]` is `["trades"]` and the in-code comment there explicitly records
            *why* `book_snapshot_5` was removed 2026-04-19: leaving a not-actually-emitted-per-(venue,day) data_type in
            that list **phantom-inflated PREDICTION `completion_pct` (35k expected vs 5.7k observed)**. `prediction_canonical_question_group`
            is **cluster-grain** (parquet key `(asset_group=prediction, venue, data_type, canonical_question_group, day)`)
            and `MARKET_LIFECYCLE` is **market_id-grain** (per `market_id`, written by instruments-service) — neither is
            instrument-day grain like `trades`. Naïvely appending them to `DATA_TYPES_BY_ASSET_GROUP["prediction"]` would
            re-introduce the exact phantom-inflation the comment warns against, and would break `is_expected("prediction",
            "POLYMARKET", "prediction_canonical_question_group")` semantics (`test_data_status_registries.py` asserts the
            `trades` form). The *real* fix the prediction sub-agent's PR-3/PR-4 was pointing at: the honest-coverage
            denominator for cluster-grain / market_id-grain prediction data_types must be computed against the
            **`PREDICTION_GROUPS` cluster registry** (`honest_coverage.py:471` `CLUSTER_VALIDATION_DATA_TYPES["prediction_canonical_question_group"]="PREDICTION_GROUPS"`)
            and the per-`market_id` lifecycle bounds — NOT a flat venue×day grid. That registry is **still a placeholder
            awaiting full seeding (PR-6, a documented temporary-state)**, so 1A.d is **gated on PR-6** + an ikenna
            coverage-aggregator-grain decision. Re-tagged: PRE_CUTOVER, gated; **NOT shippable as a quick dict edit**.
            Compose with Phase 2 (`measure_honest_coverage.py` must handle non-venue×day grains).
      - [ ] [SCRIPT] P2. **1A.c — OPTIONAL POST_CUTOVER** — rename `canonical/domain/prediction/` →
            `canonical/domain/prediction_mapping/` for clarity (singular-vs-plural is a footgun); file as a post-cutover
            issue doc, not in this plan.
      Drop the original "paste downstream-consumer table in commit message" — the consumer table is in the prediction
      catalogue-audit issue doc's `## prediction/ → predictions/ migration table` (exactly 1 real deep-import consumer).
- [ ] [AGENT] P0. **1B — Spark + Radiant SSOT consolidation**. (a) Build out Spark instruments-service adapter +
      MTDS adapter + execution connector per `defi_catalogue_chain_primitives_2026_05_10.md` Phases 2/3/4 (this
      plan owns the SSOT decision; that plan owns the implementation). (b) Add UAC `defi_venue_capabilities.py`
      entry for Radiant matching the existing `instruments-service/reference_data/adapters/defi/radiant.py`. Both
      end-states: every protocol exists in both UAC and downstream layers — no ghosts, no orphans.
- [ ] [AGENT] P0. **1C — GMX + DRIFT dual-classification resolution**. **Decision** (operator-greenlit if not yet):
      keep classification under `VENUES_BY_ASSET_GROUP["cefi"]` per the comment "On-chain CLOBs reclassified from
      DEFI - CLOB-style data like CeFi". Remove from `defi_venue_capabilities.py:130-131` (or keep with explicit
      `axis_override: "cefi"` field). Workspace-grep audit + downstream consumer verification.
- [ ] [AGENT] P0. **1D — Case-folding drift**. Decide canonical case (recommendation: keep
      `VENUES_BY_ASSET_GROUP` uppercase as the canonical user-facing identifier; lowercase elsewhere is for
      Python-symbol use). Add a `to_canonical_venue(venue_id: str) → str` helper in UAC; update consumers.
- [x] [AGENT] P0. **1E — `LST_TOKEN_TO_PROTOCOL_ASSET` SSOT verification + canonicalisation**. **DONE-AT-DIFFERENT-PATH
      2026-05-12 (slot 8 catalogue-audit pass DF-12)** — exists at `unified-api-contracts/unified_api_contracts/internal/domain/defi/lst.py:37`
      as `LST_TOKEN_TO_PROTOCOL_ASSET: dict[str, tuple[str, str]]` mapping LST token symbol → `(protocol, base_asset)`.
      Initial todo predicted `canonical/domain/onchain/lst_protocol_mapping.py`; actual placement under `internal/`
      reflects the Citadel internal-vs-canonical separation (LST→protocol mapping is internal-resolver scope, not a
      contract-facing schema). Helpers `iter_lst_tokens_for_protocol()` + `resolve_lst_protocol_asset()` re-exported via
      `__all__`. No code action needed; canonical pick stands.
- [x] [AGENT] P0. **1F — `GAS_FEE_CHAIN_START_DATES` location (audit half)**. **DONE-AT-DIFFERENT-PATH 2026-05-12
      (slot 8 catalogue-audit pass DF-13)** — exists at `unified-api-contracts/unified_api_contracts/registry/chain_env.py:61`
      as `GAS_FEE_CHAIN_START_DATES: dict[int, str]` (int-keyed by `chain_id`; values are ISO date strings) +
      `GAS_FEE_SOLANA_START_DATE: str = "2021-01-01"` at line 80. Audit half (does it exist?) → ✅ YES; placement at
      `registry/` (not `canonical/domain/onchain/` as the original todo predicted) matches the registry layer for
      chain-environment lookups. No code action needed for the audit half.
- [ ] [AGENT] P1. **1F-extend — chain-set fragmentation reconciliation (extend half).** Catalogue-audit DF-7 still
      open: `MAINNET_CHAIN_IDS=19` / `CHAIN_GENESIS_DATES=21` (adds SCROLL+ZKSYNC) / `_defi_chain_data.py:CHAIN_CONFIGS=35`
      (mainnet+testnet, adds UNICHAIN/WORLDCHAIN/ABSTRACT/INK/ZORA not in `MAINNET_CHAIN_IDS`) / `GAS_FEE_CHAIN_START_DATES=14`
      (missing BLAST/MODE/GNOSIS which have chain IDs + genesis dates). Inclusion is violated both ways. The "22 chains"
      claim cited in CLAUDE.md + this plan's Phase 1 Full-execution criterion + per-protocol plans matches NO list.
      Enforce: `MAINNET_CHAIN_IDS ⊇ CHAIN_GENESIS_DATES keys ⊇ GAS_FEE_CHAIN_START_DATES keys` + correct the "22 chains"
      wording workspace-wide + add a QG ratchet (cross-asset Phase 6A scope or a `check_chain_set_inclusion.py` QG step).
      **PRE_CUTOVER; owner=ikenna (cross-cutting closed-set decision on chain universe).**
- [ ] [AGENT] P0. **1G — UAC QG green** post-Phase-1.

**Codex SSOT update (Phase 1 boundary)**:

- [ ] [AGENT] P0. **1H — Update `codex/02-data/contracts-scope-and-layout.md`** with the 6 cleanup items + their
      resolution (canonical pick, deletions, additions).

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

- [ ] [AGENT] P0. **2A — `measure_honest_coverage.py`** at `instruments-service/scripts/` or
      `unified-trading-library/scripts/`. Reads canonical manifest; computes per-asset-group + per-(asset_group,
      venue) + per-(asset_group, venue, data_type, day) coverage % using
      `captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)`. Outputs CSV + JSON for
      UI consumption. Runs same-region GCE VM (per CLAUDE.md memory "operator-run measure-honest-coverage.py on
      same-region GCE VM").
- [ ] [AGENT] P0. **2B — Cron VM** to run 2A daily at midnight UTC; output to GCS bucket
      `gs://central-element-323112-honest-coverage/{YYYY-MM-DD}/coverage.json`. Launcher
      `deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh` per CLAUDE.md "VM launcher script SSOT".
      Singleton-locked.
- [ ] [AGENT] P0. **2C — Deployment-api endpoint** at `GET /api/data-status/honest-coverage` returning the
      latest 2B output + per-asset-group + per-venue + per-data_type drilldowns.
- [ ] [AGENT] P0. **2D — Deployment-ui surface**. Per-asset-group coverage % card at top of each asset_group's
      data-status tab + drilldown chart: per-venue / per-data_type / per-day stacked-bar (captured /
      empty_confirmed / attempted_failed / expected_unattempted). Composes with existing data-status tab
      (deployment-stack at port 5183).

**Codex SSOT update (Phase 2 boundary)**:

- [ ] [AGENT] P0. **2E — Update `codex/02-data/availability-manifest-and-data-status.md`** with the new
      measurement script + UI surface contract.
- [ ] [AGENT] P0. **2F — New `codex/03-deployment/data-status-ui-surface.md`** documenting the per-asset-group
      coverage UI's data contract + which back-end endpoint feeds which widget.

**Full-execution criterion**:

- ✅ `measure_honest_coverage.py` runs end-to-end against production manifest + outputs JSON.
- ✅ Daily cron VM has run ≥ 1 day end-to-end with STARTED + STOPPED events emitted (per "No fire-and-forget VM
  launches" rule).
- ✅ Deployment-ui surface visible at `http://localhost:5183/data-status` showing per-asset-group %.
- ✅ Per-asset-group coverage % matches manual probe of canonical manifest.

## Phase 3 — Per-CeFi-venue zero-activity-bar verification + remediation (PARALLEL with 1; ~5-10 AI-days)

Owner: harsh + parallel agent. Composes with `writegate_honest_coverage_endtoend_2026_05_06.md` Wave 3.M adapter
audit.

Pre-audit: writegate Wave 3.M is PENDING. Some CeFi venues may still emit legacy NaN placeholder bars (Category C
"reader / schema-drift bug" or older Category A "_create_empty_output()" pattern) instead of zero-activity bars
(Category D "tradeable-but-illiquid" with O=H=L=C=prior_LTP, volume=0, trade_count=0).

- [ ] [AGENT] P0. **3A — Per-CeFi-venue adapter audit** across the ~21 venues in `VENUES_BY_ASSET_GROUP["cefi"]`.
      For each venue × each data_type:
      1. What does the adapter emit on source-zero-response? Category A (record_empty), B (UpstreamTimestampBiasError),
         C (MalformedTickFieldError), or D (zero-activity bar)?
      2. If catalogue says alive + venue market hours yes + source returns zero → must be Category D (zero-activity
         bar). Verify per CLAUDE.md "Four-category empty-output decision".
      3. NO `_create_empty_output()` in any base adapter (banned per writegate Phase 2.A).
- [ ] [AGENT] P0. **3B — Per-venue remediation tickets**. For each venue still emitting legacy NaN placeholders,
      file an issue doc at `plans/active/issues/cefi_<venue>_zero_activity_bar_2026_05_<date>.md` with the audit
      finding + remediation owner.
- [ ] [AGENT] P0. **3C — Reconciler script** `instruments-service/scripts/reconcile_legacy_nan_placeholder_bars.py`
      to convert existing NaN-placeholder rows in production manifests to either Category A `record_empty` (typed
      reason) or Category D zero-activity bar per the catalogue-aware rule.
- [ ] [AGENT] P0. **3D — Workspace-wide grep** for `_create_empty_output` / `_handle_empty_tick_data` — confirm
      banned-pattern AST sweep (writegate Phase 2.A) is complete; if not, complete here.

**Codex SSOT update (Phase 3 boundary)**:

- [ ] [AGENT] P0. **3E — Update `codex/02-data/honest-absence-downstream-handling.md`** with per-CeFi-venue audit
      results + Category D coverage status.

**Full-execution criterion**:

- ✅ Per-CeFi-venue audit complete; every venue × data_type cell has documented Category-A/B/C/D classification.
- ✅ Workspace-grep for `_create_empty_output` returns zero hits in non-test code.
- ✅ Reconciler runs against ≥ 1 month historical CeFi manifest data + flips legacy rows correctly.

## Phase 4 — Codex doc consolidation: 3 mev-protection.md drift (PARALLEL with 1; ~1-2 AI-days)

Owner: harsh.

> **STATUS 2026-05-12 — Phase 4 already largely shipped pre-2026-05-12; closeout verified by slot 8 this turn.**
> The 3-way consolidation landed back in 2026-05-10 (catalogue_audit_strategy_2026_05_12 ST-15 confirms the structure
> is correct: `07-security/` = 54-line redirect stub, `04-architecture/` = 431-line canonical, `09-strategy/.../cross-cutting/` =
> 156-line scope-narrowed strategy-side narrative with explicit cross-link to canonical). 4A-4D walk below show the
> verify-and-close steps; 4E adds the ST-15 nit reconciliation (UAC `MevSubmissionMode` enum vs both doc tables).

- [x] [AGENT] P0. **4A — Audit content drift**: read all three. **DONE 2026-05-10 (consolidation) + 2026-05-12 (verify slot 8)** —
      `07-security/mev-protection.md` (54 lines) is a redirect stub with explicit `## Where to find what` pointer
      table; `04-architecture/mev-protection.md` (431 lines) is the canonical (threat model + provider factory + RPC
      URL SSOT + provider implementations + operational run-book + UAC `MevSubmissionMode` table); `09-strategy/architecture-v2/cross-cutting/mev-protection.md`
      (156 lines) carries the strategy-side narrative (per-strategy MEV policy YAML, per-chain rules, per-action-type
      mapping, monitoring metrics) with a top-of-file "CANONICAL location" banner pointing back at `04-architecture/`.
      Three docs, three scopes, zero overlap in the implementation surface; cross-references walk both directions.
- [x] [AGENT] P0. **4B — Pick canonical**: `codex/04-architecture/mev-protection.md`. **DONE 2026-05-10** — verified
      by slot 8 2026-05-12 that the canonical doc carries (a) threat model, (b) provider selection factory matrix
      mapping `chain_id → provider class`, (c) protected RPC URLs SSOT, (d) provider implementations (NoProtection /
      PrivateMempool / Flashbots / Jito), (e) UAC `MevSubmissionMode` enum table, (f) operational run-book — the
      complete spec. The other two carry nothing the canonical doesn't.
- [x] [AGENT] P0. **4C — Convert non-canonical to redirects**. **DONE 2026-05-10** — `07-security/mev-protection.md`
      is a redirect stub with `## Where to find what` lookup table for 4 common reader entry points. The
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
- [x] [AGENT] P0. **4E — ST-15 nit: UAC `MevSubmissionMode` enum reconciliation.** **DONE 2026-05-12 (slot 8 this turn)** —
      canonical doc (`04-architecture/mev-protection.md:201`) was missing `CUSTOM_PRIVATE_RPC` row; strategy-side doc
      (`09-strategy/architecture-v2/cross-cutting/mev-protection.md:28-35`) was missing `JITO_BUNDLE` row. Both tables
      now mirror the UAC `MevSubmissionMode` enum (6 active modes + 1 removed: PUBLIC_MEMPOOL / FLASHBOTS_PROTECT /
      MEV_BLOCKER / MANIFOLD / CUSTOM_PRIVATE_RPC / JITO_BUNDLE; BLOXROUTE marked removed in both). Strategy doc
      header now cross-links UAC enum source-of-truth + canonical for implementation. Closes ST-15 carry-over.

**Phase 4 carry-over (out-of-scope NICE-TO-HAVE)**:

- **NICE-TO-HAVE — `codex/09-strategy/strategy-summary.md` vscode-webview link artefacts**. 71 occurrences of
  `vscode-webview://` URL prefix across the file (editor-paste artefact when authoring via VS Code preview); link
  targets all resolve correctly but the URLs are noisy and break preview rendering in some viewers. Follow-up:
  global s/vscode-webview:\/\/[^\/]+\/unified-trading-system-repos\/unified-trading-pm\///g + workspace-grep test
  to confirm no other strategy/codex doc has the same artefact. Filed inline (NICE-TO-HAVE, not blocking; not a
  P3 plan-todo since the link content is intact and resolution works).

**Full-execution criterion**:

- ✅ Canonical `04-architecture/mev-protection.md` includes 100% of unique content from the other 2 — verified
  slot 8 2026-05-12.
- ✅ Other 2 docs either redirect-only or scope-narrowed with cross-link — verified slot 8 2026-05-12 (54-line
  redirect stub + 156-line scope-narrowed strategy narrative with top-banner cross-link).
- ✅ Zero broken links across the workspace — verified slot 8 2026-05-12 (16 incoming files; all targets resolve;
  EX-8/EX-20 already shipped @`0fc4b3fd`).

## Phase 5 — TradFi ETF list SSOT + canonical asset-group registry (PARALLEL with 1; ~3-5 AI-days)

Owner: harsh.

- [ ] [AGENT] P0. **5A — TradFi ETF list SSOT**. New file
      `unified-api-contracts/unified_api_contracts/canonical/domain/derivatives/tradfi_etfs.py` declaring
      `TRADFI_ETFS: dict[str, ETFMetadata]` (ticker → metadata: underlying / issuer / expense_ratio / launch_date
      / source). Currently distributed across Databento converter + ad-hoc references.
- [ ] [AGENT] P0. **5B — TradFi root product SSOT**. Similar file
      `unified-api-contracts/unified_api_contracts/canonical/domain/derivatives/tradfi_roots.py` declaring
      `TRADFI_ROOTS: dict[str, RootMetadata]` for ES / MBT / MET / VIX / etc. with venue + data_types + cluster
      bundling rules.
- [ ] [AGENT] P0. **5C — Cross-asset-group registry index**. New file
      `unified-api-contracts/unified_api_contracts/canonical/asset_group_registry.py` providing:
      ```python
      def get_canonical_inventory(asset_group: str) -> AssetGroupInventory:
          """Return canonical inventory: venues, instruments, data_types, source coverage windows."""
      ```
      Single function returning the full canonical surface for any asset_group. Resolves the question doc § A1
      problem (no central "give me everything for asset_group X" surface).

**Codex SSOT update (Phase 5 boundary)**:

- [ ] [AGENT] P0. **5D — Update `codex/02-data/contracts-scope-and-layout.md`** with the new asset-group registry
      index entry-point.

**Full-execution criterion**:

- ✅ `TRADFI_ETFS` + `TRADFI_ROOTS` declared + tested.
- ✅ `get_canonical_inventory("cefi")` returns 21 venues + ~hundreds of instruments + ~10 data_types per venue.
- ✅ Same call works for defi / tradfi / sports / prediction.

## Phase 6 — Validation: workspace-wide grep audits + downstream consumer verification (~2-3 AI-days)

Owner: ikenna for sign-off + harsh for runs.

- [ ] [AGENT] P0. **6A — Workspace-grep audit** post-Phase-1: for each deletion / rename / dual-source
      consolidation, grep the entire workspace for downstream consumers; verify no broken imports / references.
      Per CLAUDE.md § 6 extension to non-library refactors.
- [ ] [AGENT] P0. **6B — Per-asset-group coverage % validation** post-Phase-2: probe canonical manifest manually
      for 5 random (asset_group, venue, data_type) cells; verify the dashboard number matches.
- [ ] [AGENT] P0. **6C — End-to-end smoke**: run `measure_honest_coverage.py` against production manifest, view
      result in deployment-ui at `http://localhost:5183/data-status`, drill down to per-(asset_group, venue,
      data_type, day) cell, verify the underlying capture state in GCS matches the UI's coverage state.
- [ ] [AGENT] P0. **6D — All Phase 1-5 QGs green** across UAC + instruments-service + market-tick-data-service +
      deployment-api + deployment-ui.

**Full-execution criterion**:

- ✅ Workspace-grep audit clean: zero broken imports.
- ✅ Coverage % validation: 5/5 random cells match.
- ✅ End-to-end smoke green.
- ✅ All QGs green on origin.

## Phase 7 — Codex SSOT updates (continuous + final lock)

Per Post-Plan-Phase Codex Audit HARD RULE:

- [ ] [AGENT] P0. **7A — `codex/02-data/contracts-scope-and-layout.md`** (UPDATE; Phase 1H + 5D).
- [ ] [AGENT] P0. **7B — `codex/02-data/availability-manifest-and-data-status.md`** (UPDATE; Phase 2E).
- [ ] [AGENT] P0. **7C — `codex/03-deployment/data-status-ui-surface.md`** (NEW; Phase 2F).
- [ ] [AGENT] P0. **7D — `codex/02-data/honest-absence-downstream-handling.md`** (UPDATE; Phase 3E).
- [ ] [AGENT] P0. **7E — `codex/04-architecture/mev-protection.md`** (CONSOLIDATED; Phase 4).
- [ ] [AGENT] P0. **7F — Each per-asset-group epic refreshed** (`cefi_master` / `tradfi_master` / `sports_master`
      / `predictions_master` + `defi_master`) with the new canonical inventory entry-point + coverage % surface.

## Cross-plan dependencies

- **`defi_catalogue_chain_primitives_2026_05_10.md`** Phase 1A (UAC entries for the 26 protocols) shares the UAC
  SSOT cleanup gate with this plan's Phase 1; coordinate so the entries land before this plan's Phase 1G QG check.
- **`writegate_honest_coverage_endtoend_2026_05_06.md`** Wave 3.M is the upstream owner of zero-activity-bar
  remediation; this plan's Phase 3 either consumes or completes the wave.
- **All 5 per-asset-group masters** (cefi/tradfi/sports/predictions/defi) consume the Phase 5C canonical inventory
  entry-point.

## Risk register

| Risk | Mitigation |
| ---- | ---------- |
| Deleting `canonical/domain/prediction/` breaks downstream consumers we missed | Phase 1A + Phase 6A workspace-grep audits cover; if missed, fail-loud at next QG run on consumer repos |
| `measure_honest_coverage.py` cron VM cost in GCS reads | Once-daily cadence; ~30MB read per run; negligible |
| Phase 3 per-CeFi-venue audit might surface 10+ remediation tickets | Each ticket is small (per-adapter migrate to record_empty / Category D); spread across parallel agents |
| 3 mev-protection.md docs migration loses unique content | Phase 4A explicit diff before consolidation |

## Done definition

- ✅ Phase 1-7 all checkboxes flipped.
- ✅ Phase 6D all QGs green on origin.
- ✅ Codex SSOTs locked durable.
- ✅ Per-asset-group coverage % surface visible in production deployment-ui.
- ✅ Zero workspace-grep broken-link findings.

Plan archives post-cutover with deferred-work audit per Plan Archival HARD RULE.

## DONE block

### DONE-2026-05-12 — slot 8 (harsh-catalogue-audit-tab) — per-asset-group catalogue audit pass (groundwork)

| Phase / item | Status as of 2026-05-12 EOD | Evidence / successor / blocker |
|---|---|---|
| Catalogue audit pass (5-way fan-out) | ✅ DONE | `plans/active/issues/catalogue_audit_{cefi,defi,tradfi,sports,prediction}_2026_05_12.md` (69 findings; 1×P0) — PM@`dc89abed`; reconciliation table + fan-out dispatch + cross-cutting drift summary + stale-claim reconciliation in `## Per-asset-group catalogue audit pass (2026-05-12)` section — PM@`920ec94c` |
| Phase 1A (dual-prediction module) | 🔁 RE-SCOPED + 🟡 PENDING OPERATOR | premise (delete singular `prediction/`) REJECTED — both modules non-redundant; re-scoped to "keep both + fix 1 deep-import consumer (`instruments-service/.../adapters/prediction/polymarket.py:25`) + fold in PR-3/PR-4 (`prediction_canonical_question_group`+`MARKET_LIFECYCLE` → `DATA_TYPES_BY_ASSET_GROUP["prediction"]`)"; ready to implement (no operator decision needed for the keep-both + facade-fix; the optional rename is POST_CUTOVER) |
| Phase 1B (Spark + Radiant SSOT consolidation) | ☐ TODO | Spark now PARTIALLY done (instruments+UAC; no MTDS-dedicated/connector); Radiant PARTIALLY done (in `ALL_DEFI_VENUES`+`MarginModel`; not `PROTOCOL_CAPABILITIES`); + euler_v2/venus/benqi same shape — fan-out to `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1A per DF-2; PLASMA orphan keys (DF-9) need register-or-delete |
| Phase 1C (GMX/DRIFT dual-classification) | ☐ TODO — 🟡 OPERATOR-GREENLIT NEEDED | P0; confirmed still dual in UAC `_defi.py`+`defi_protocol_registry.py` AND `VENUES_BY_ASSET_GROUP["cefi"]` AND routed via DEX adapter (DF-3/DF-10/CF-1/CF-2); decision per plan body; escalated in `_agent_pings.md` |
| Phase 1D (case-folding drift) | ☐ TODO | widen to cover SP-3 (sports, 5 SSOTs) + DF-4/5/17 (defi venue-keyed dicts) + CF-3/4 (cefi) — ship `to_canonical_venue()` + an all-asset-group venue-key-parity test |
| Phase 1E (`LST_TOKEN_TO_PROTOCOL_ASSET`) | ✅ ALREADY EXISTS (different path) | at `unified-api-contracts/.../internal/domain/defi/lst.py:37` (not `canonical/domain/onchain/` as the todo predicted; `internal/` placement looks correct) — DF-12; should be marked done-with-different-path by the plan owner |
| Phase 1F (`GAS_FEE_CHAIN_START_DATES`) | ✅ ALREADY EXISTS — but extend | at `chain_env.py:61` (int-keyed) + `GAS_FEE_SOLANA_START_DATE` — DF-13; **extend** to reconcile the chain-set fragmentation (`MAINNET_CHAIN_IDS`=19 / `CHAIN_GENESIS_DATES`=21 / `CHAIN_CONFIGS`=35 / `GAS_FEE_CHAIN_START_DATES`=14 / "22 chains" claim matches none — DF-7) + correct the "22 chains" wording in CLAUDE.md + per-protocol plans |
| Phase 2 (manifest health script + UI) | ☐ TODO | `measure_honest_coverage.py` confirmed NOT to exist; must validate venue-key↔capability-dict parity before computing % (CF-4/SP-6/DF-8 — coverage-start key mismatch silently zeros expected shards) |
| Phase 3 (per-CeFi-venue zero-activity-bar verify) | ☐ TODO | Wave 3.M is 0% started (all 21 cefi venues on legacy `empty_confirmed`; no Cat-D bars; UTL helpers don't exist) — callout added to `writegate_honest_coverage_endtoend_2026_05_06.md`; the cefi sub-agent's per-venue Cat-A/B/C/D matrix in `catalogue_audit_cefi_2026_05_12.md` seeds the audit |
| Phase 4 (3 mev-protection.md consolidation) | ✅ DONE 2026-05-12 (slot 8 closeout) | 3-way consolidation already landed 2026-05-10; slot 8 verified structure (54-line redirect + 431-line canonical + 156-line scope-narrowed strategy narrative) + reconciled UAC `MevSubmissionMode` enum drift (canonical missing CUSTOM_PRIVATE_RPC; strategy missing JITO_BUNDLE) — both tables now mirror UAC's 6-mode enum. EX-8/EX-20 sibling fix already shipped @`0fc4b3fd`. 1 NICE-TO-HAVE carried inline (71 vscode-webview links in `strategy-summary.md`). Phase 4 close-out commit: PM@<next> |
| Phase 5 (TradFi ETF/roots SSOT + asset_group_registry) | ☐ TODO | `tradfi_etfs.py` / `tradfi_roots.py` / `asset_group_registry.py` confirmed NOT to exist; SSOT-fragmentation fully mapped — ETF list across 4 files, futures-roots across 3, VIX constants in `data_source_continuity.py` not `honest_coverage.py` (TF-1/TF-2/TF-7); `canonical/domain/derivatives/` has only `__init__.py`+`options.py` |
| Phase 6 (validation) | ☐ TODO | |
| Phase 7 (codex SSOT updates) | ☐ TODO | incl. CLAUDE.md VIX-15m pointer fix (TF-7), `contracts-scope-and-layout.md` venue-class taxonomy (DF-19), the 6 cross-asset cleanup items |

**Carry-forward for next slot-8 session**: Phase 1A facade-fix + PR-3/PR-4 (no operator gate); Phase 1C operator greenlight then implement; Phase 1D `to_canonical_venue()` + parity test; mark 1E/1F done-with-different-path + extend 1F for the chain-set fragmentation; then Phases 2-5. Coordinate Phase 1B fan-out with slot 2 (`defi_catalogue_chain_primitives` Phase 1A) — slot 8 ping already sent.
