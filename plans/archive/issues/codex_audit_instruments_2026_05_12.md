---
doc_type: issue
title: Codex audit — Instruments area (Phase 1.G)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-12
author: harsh-codex-audit-instruments-tab (slot 8 sub-agent)
source:
  [
    plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md Phase 1.G,
    plans/active/issues/catalogue_audit_cefi_2026_05_12.md,
    plans/active/issues/catalogue_audit_defi_2026_05_12.md,
    plans/active/issues/catalogue_audit_tradfi_2026_05_12.md,
    plans/active/issues/catalogue_audit_sports_2026_05_12.md,
    plans/active/issues/catalogue_audit_prediction_2026_05_12.md,
    plans/active/issues/codex_audit_data_2026_05_12.md (sibling — manifest schema / honest-absence taxonomy generic
    findings; this doc does NOT re-derive those),
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/defi-venue-protocol-catalogue.md,
    /codex/02-data/defi-data-types-catalog.md,
    /codex/02-data/defi-data-type-taxonomy.md,
    /codex/02-data/instrument-pipeline-defi.md,
    /codex/02-data/venue-availability.md,
    /codex/02-data/data-catalogue-schema.md,
    /codex/02-data/per-instrument-sentinel-rollout.md,
    /codex/02-data/operation-capability-registry.md,
    /codex/02-data/contracts-scope-and-layout.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    instruments-service/scripts/reconcile_phantom_manifest_rows_all.py,
    "instruments-service/instruments_service/reference_data/factory.py + adapters/{cefi,defi,tradfi,sports,prediction}/",
    "unified-api-contracts/unified_api_contracts/registry/{defi_venues.py,defi_venue_capabilities.py,venue_mapping.py,market_data_categories.py}",
    unified-trading-library/unified_trading_library/manifest_writer.py,
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# Codex audit — Instruments area (Phase 1.G)

> **Severity**: P1 — pre-cutover audit per `codex_vs_citadel_infrastructure_audit_2026_05_10.md` Phase 1.G. **Scope
> (codex-doc layer)**: catalogue completeness docs · reference-data adapter docs · per-asset*group coverage docs ·
> manifest v5+/v8 schema & 4-state `capture_status` (instruments-side only — generic manifest findings are in sibling
> `codex_audit_data_2026_05_12.md`) · honest-absence taxonomy as it touches instruments · cluster validation for bundled
> data_types · `available_at` semantics · the phantom-audit reconciler. **Non-goal**: re-running the per-asset_group
> catalogue reconciliation — the 5 sibling `catalogue_audit**\_2026_05_12.md` docs own that. This doc audits whether the
> **codex docs** about instruments/reference-data/catalogue/manifest are accurate vs the code AND vs those catalogue
> findings; where a catalogue finding has a codex-doc implication it is *elevated\* here (cited as `DF-N` / `CF-N` /
> `TF-N` / `SP-N` / `PR-N`). **Owner**: Harsh T8 slot 8 sub-agent; operator review for dispositions before Phase 3 ship.

## Methodology

Read every Instruments-area codex surface in `codex/02-data/` (anchor list of ~14 docs + cross-referenced sweeps). For
each rule / claim / SSOT pointer: cite file:line, classify KEEP / LIFT / CONSOLIDATE / DELETE / ADD + a 1-line reason +
suggested disposition (IMMEDIATE / PRE_CUTOVER / POST_CUTOVER). Cross-checked against UAC registry source
(`defi_venues.py`, `defi_venue_capabilities.py`, `venue_mapping.py`, `market_data_categories.py`), instruments-service
`reference_data/factory.py` + the 5 adapter sub-dirs (cefi/defi/tradfi/sports/prediction), UTL `manifest_writer.py`, and
the 5 catalogue_audit issue docs. Several findings come from grep-then-READ (the catalogue audit's GHOST/ORPHAN rows
were verified against the codex docs' SSOT-pointer chains, not just literal-grep).

## Cross-reference to catalogue audit

The 5 catalogue audits produced ~67 catalogue-layer findings (case-folding drift, GHOST venues, ORPHAN adapters,
DUAL-classified venues, MISSING-DT coverage windows). A subset has a **codex-doc implication** — i.e. a codex SSOT
either makes a wrong claim about the catalogue, fails to document a known fragmentation, or points at a non-existent
file. Specifically: (a) `defi-venue-protocol-catalogue.md`'s 2026-05-12 refresh banner asserts
`defi_venue_capabilities.py` "does not exist" — but it does, and `catalogue_audit_defi` (DF-2/DF-3/DF-8/DF-14/DF-18)
actively uses it as the per-(venue,data_type) start-date SSOT → **IN-1**, the highest-blast-radius finding in this doc;
(b) `venue-availability.md` documents `VenueMapping`/`VenueEntry` as the "primary SSOT" but the actual per-asset_group
venue lists live in `market_data_categories.py:VENUES_BY_ASSET_GROUP` + `defi_venues.py:ALL_DEFI_VENUES` (the
case-folding / dual-classification findings CF-1..CF-3, DF-3, SP-3, PR-1 all anchor on those, not on `venue_mapping.py`)
→ **IN-2/IN-3**; (c) `instrument-pipeline-defi.md` lists 6 stale DeFi adapter paths (`adapters/eigenlayer.py` etc.) but
there are now 25 adapters under `adapters/defi/` (DF-1 Spark + DF-11 Radiant + DF-2 euler/venus/benqi all shipped
adapters since the doc was written) → **IN-4**; (d) no codex doc documents the "execution-only / no-instrument-universe
venue class" (Jupiter/bridges — DF-19) or the "SourceCapability ≠ market-data venue" two-axis distinction that
CF-12/TF-4/TF-5/SP-2 keep re-flagging → **IN-9**; (e) the codex catalogue docs use `category=` legacy hive vocab while
the canonical is `asset_group=` (DF migration scripts `migrate_defi_bare_to_asset_group.py` exist) → **IN-7**; (f)
cluster-validation MANDATORY for bundled data_types (SP-10, PR-6, TF-6) is documented in `defi-data-type-taxonomy.md`
but with no QG-step cross-link → **IN-11**.

## Findings

### Tier 1 — codex doc vs implementation/catalogue drift

| # | Finding (KEEP/LIFT/CONSOLIDATE/DELETE/ADD) | Disposition (IMMEDIATE/PRE_CUTOVER/POST_CUTOVER) | Owner | Evidence
(file:line) | | ----- |
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| ------------------------------------------------------- |
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| ------- |
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| ----------- | ---------------------------------- |
---------------------------------------------------------------------------------------------------------- | | IN-1 |
**DELETE the wrong "correction"** — `defi-venue-protocol-catalogue.md` 2026-05-12 refresh banner (lines 12-13, 46-47,
and the Axis-legend Note) asserts `defi_venue_capabilities.py` "does not exist; canonical lives at `defi_venues.py`".
**Both files exist** (`defi_venue_capabilities.py` = 178 LOC holding `DEFI_VENUE_DATA_TYPE_CAPABILITIES` — the
per-(venue,data_type) start-date dict merged into `VENUE_DATA_TYPE_CAPABILITIES` at load time; `defi_venues.py` = 482
LOC holding `ALL_DEFI_VENUES`/`DEFI_VENUE_PHASE`/`MTDS_DEFI_VENUES`). They are DIFFERENT SSOTs. `catalogue_audit_defi`
cites `defi_venue_capabilities.py` in DF-2, DF-3, DF-8, DF-14, DF-18 as the live coverage-window SSOT. The codex doc's
"stale-reference correction" is itself a drift-introducing error — an agent reading it will delete valid references.
RESTORE the `defi_venue_capabilities.py` axis + remove the "does not exist" claim. | IMMEDIATE ✅ DONE @959ca3fc (slot 8
main pre-batch — defi-venue-protocol-catalogue.md axis-legend restored; "does not exist" claim removed) | Ikenna
(governance) + defi-catalogue maintainer | `/codex/02-data/defi-venue-protocol-catalogue.md:12-13,46-47` vs
`unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py:1-178` + `defi_venues.py:1-482`;
cross-ref `catalogue_audit_defi_2026_05_12.md` DF-2/DF-3/DF-8 | | IN-2 | **CONSOLIDATE** —
`venue-availability.md:20-26,114,124` claims `unified_api_contracts.registry.venue_mapping.VenueMapping`/`VenueEntry` is
the "primary SSOT" for which venues exist at a historical date. The actual per-asset*group venue catalogue lives in
`market_data_categories.py:VENUES_BY_ASSET_GROUP` (21 cefi / 8 tradfi / 2 prediction / ~10 sports venue ids) +
`defi_venues.py:ALL_DEFI_VENUES` (~70 defi venue ids) + `venue_launch_dates.py` (launch dates) + `coverage_starts.py`
(source-coverage windows). `venue_mapping.py` still exists but is a \_helper* (`get_venue_start_date`,
`get_expected_trading_dates` — used by `availability-manifest-and-data-status.md:544-547`), not the venue _registry_.
The case-folding (CF-3, SP-3) + dual-classification (CF-1, CF-2, DF-3) catalogue findings all anchor on
`VENUES_BY_ASSET_GROUP` / `ALL_DEFI_VENUES`, NOT `venue_mapping.py`. Re-point `venue-availability.md` to the real
venue-registry SSOTs + clarify `venue_mapping.py`'s role as a date-helper. | IMMEDIATE ✅ DONE @71d24b2e (slot 8
sub-agent — venue-availability.md "Where Availability Lives" section rewritten to 4 per-asset_group SSOTs;
`defi_venue_capabilities.py` added to Key Files; venue_mapping.py reframed as date-helper; Adding-a-New-Venue checklist
updated) | UAC maintainer + Ikenna | `/codex/02-data/venue-availability.md:20-26,114,124` vs
`unified-api-contracts/.../registry/market_data_categories.py:163-222` + `defi_venues.py:ALL_DEFI_VENUES`; cross-ref
`catalogue_audit_cefi_2026_05_12.md` CF-1/CF-2/CF-3 + `catalogue_audit_defi` DF-3 | | IN-3 | **ADD** — No codex doc
records the **case-folding contract** that the 5 catalogue audits keep re-discovering: `VENUES_BY_ASSET_GROUP` ids are
UPPERCASE (`BINANCE-SPOT`, `ODDS_API`, `POLYMARKET`); `_BASE_VENUES_BY_ASSET_GROUP` / `SourceCapability.source` /
`*_SOURCE_COVERAGE_START` keys / instruments-service adapter registries are lowercase (`binance`, `odds_api`). No
`to_canonical_venue()` helper exists yet (CF-3 / SP-3 / cross-asset Phase 1D). Until that helper ships,
`availability-manifest-and-data-status.md` and `venue-availability.md` should document the "uppercase = user-facing
venue identifier / lowercase = python-symbol + secret-key" split so honest-coverage clip joins (CF-4: `BINANCE-SPOT`
never matches `CEFI_SOURCE_COVERAGE_START["BINANCE"]`) don't silently skip venues. | PRE_CUTOVER | Ikenna (closed-set
decision — cross-asset Phase 1D) | cross-ref `catalogue_audit_cefi_2026_05_12.md` CF-3/CF-4, `catalogue_audit_sports`
SP-3; no codex doc currently documents the split | | IN-4 | **CONSOLIDATE** — `instrument-pipeline-defi.md:18`
"Adapters: eigenlayer.py, ethfi.py, lido.py, etherfi.py, binance.py, hyperliquid.py" + the "Key Files" table (lines
201-205) reference `instruments_service/reference_data/adapters/eigenlayer.py` (no `defi/` subdir) and list 6 adapters.
Reality: the DeFi adapters live under `reference_data/adapters/defi/` (25 files: aave_v3, balancer, benqi, compound_v3,
curve, drift, eigenlayer, ethena, etherfi, ethfi, euler_v2, fluid, jito, kamino, lido, marinade, morpho, orca, radiant,
raydium, spark, uniswap_v2/v3/v4, venus); `binance.py`/`hyperliquid.py` are CeFi adapters at `adapters/cefi/`. Spark
(DF-1), Radiant (DF-11), euler_v2/venus/benqi (DF-2) all shipped adapters since this doc was last touched. UPDATE the
adapter list + fix the paths. | PRE_CUTOVER | instruments-service maintainer |
`/codex/02-data/instrument-pipeline-defi.md:18,201-205` vs
`ls instruments-service/instruments_service/reference_data/adapters/defi/` (25 files) + `adapters/cefi/`; cross-ref
`catalogue_audit_defi` DF-1/DF-2/DF-11 | | IN-5 | **CONSOLIDATE** — `data-catalogue-schema.md` uses `category:` (legacy
vocab) as a required field name
(`category: cefi                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | tradfi                                                                                                                                                                                                                                                                          | defi                                                    | sports                                                                                                                                                                                                                                                        | altdata | prediction`—
lines 14, 38) and includes`altdata` which is not in the canonical asset_group key set
(`cefi`/`defi`/`tradfi`/`sports`/`prediction`per CLAUDE.md "Asset-group vocabulary").
The`data-catalogue.{service}.yaml`schema should rename`category`→`asset_group`and drop`altdata`(or document it as a
sixth domain if real). Also`schema_ref: unified_api_contracts.internal.domain.instruments.InstrumentsSchema`— verify
that import path exists (the data-area audit D-7 flagged a sibling non-existent-module reference
in`schema-governance.md`). | PRE_CUTOVER | data-catalogue maintainer + Ikenna |
`/codex/02-data/data-catalogue-schema.md:14,17,38` vs `cursor-configs/CLAUDE.md` § "Asset-group vocabulary" | | IN-6 |
**ADD** — `availability-manifest-and-data-status.md:660-700` documents the phantom-audit reconciler
(`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`, 7 drift axes) but carries **no Runbook
Execution-Owner block** (the CLAUDE.md "Runbook Execution-Owner SSOT" HARD RULE requires
`execution: owner / cadence / verifier / last_executed`). The doc says "Always run on same-region GCE VM" + shows the
`gcloud compute instances create cefi-phantom-audit-...` command (line 699) but no named Tab / cron owns the recurring
run; given the 5 catalogue audits found GHOST/ORPHAN venues across every asset_group, a stale phantom-audit cadence is a
live correctness risk. ADD the execution block + cite which work-split Tab runs it pre-cutover. | PRE_CUTOVER |
manifest-evolution maintainer + Ikenna (Tab assignment) |
`/codex/02-data/availability-manifest-and-data-status.md:660-700` (no `execution:` block) | | IN-7 | **CONSOLIDATE** —
`defi-data-types-catalog.md:19-22` GCS path convention shows `category=defi/` (legacy hive key) in the canonical path
template; same `category=` legacy form appears in `data-catalogue-schema.md` and `data-lineage-MTDS-features-ml.md` (the
latter already flagged in data-area audit D-15). Per CLAUDE.md "Asset-group vocabulary" + the GCS hive-key SSOT
(`market_tick_data_service/raw_tick_hive.py`: `asset_group=` canonical, `category=` legacy preserved on disk), and given
instruments-service ships `migrate_defi_bare_to_asset_group.py` + `migrate_defi_legacy_venue_chain.py`, the codex
catalogue docs should show `asset_group=defi/` as canonical with a one-line "legacy `category=defi/` data coexists until
<migration plan> deletes it" note. | PRE_CUTOVER | bucket-naming maintainer |
`/codex/02-data/defi-data-types-catalog.md:19-22` vs `cursor-configs/CLAUDE.md` § "Asset-group vocabulary";
`instruments-service/scripts/migrate_defi_bare_to_asset_group.py` | | IN-8 | **CONSOLIDATE** — `venue-availability.md`
opening "See also" banner (lines 4-7) says the manifest is "v7 — current; `MANIFEST_SCHEMA_VERSION = 7`" while
`availability-manifest-and-data-status.md:244` header says "Schema v8 (current; ratified 2026-05-09)" with a
transitional-constant footnote (`MANIFEST_SCHEMA_VERSION = 7` until Phase 4.DEFAULT-REMOVAL — lines 260-274). Two
instruments-area codex docs give different headline version numbers for the same schema. Align `venue-availability.md`'s
banner to the v8-column-shape / v7-transitional-constant phrasing. (Sibling data-area audit D-3 covers the broader v7/v8
docs sweep — this is the instruments-side instance.) | PRE_CUTOVER | manifest-evolution maintainer |
`/codex/02-data/venue-availability.md:4-7` vs `availability-manifest-and-data-status.md:244,260-274`; cross-ref
`codex_audit_data_2026_05_12.md` D-3 | | IN-9 | **ADD** — No codex doc documents the **"SourceCapability ≠ market-data
venue ≠ instruments-service adapter" three-axis distinction** that the catalogue audits keep re-flagging as confusing:
CF-12 (`_cefi.py` lists `bitstamp`/`huobi`/`kucoin`/`mexc` SourceCapabilities not in `VENUES_BY_ASSET_GROUP`), TF-4
(`_tradfi.py` declares FRED/POLYGON/ECB/OPENBB/OFR/REGULATORY SourceCapabilities with no venue entry), TF-5 (Polygon
instruments adapter with no venue), SP-2 (`open_meteo` adapter+venue with no SourceCapability), DF-19 (Jupiter/bridges =
execution-only, no instrument universe). ADD a short "venue-class taxonomy" section in `venue-availability.md` (or a new
`/codex/02-data/venue-class-taxonomy.md`) enumerating: market-data venue · refdata-only source · execution-only
connector · API-capability source · combinations — so future audits stop re-flagging these as drift. | PRE_CUTOVER |
Ikenna (closed-set call) | cross-ref `catalogue_audit_cefi` CF-12, `catalogue_audit_tradfi` TF-4/TF-5,
`catalogue_audit_sports` SP-2, `catalogue_audit_defi` DF-19; no codex doc currently covers it | | IN-10 |
**CONSOLIDATE** — `defi-venue-protocol-catalogue.md` § status legend defines ✅ PRODUCTION as "manifest coverage ≥ 99%"
but the 2026-05-12 refresh banner already flips multiple ◐ rows to ✅ based on UAC-commit-shipped (e.g. Renzo/KelpDAO
LST mapping rows, Solana MEV cell) without a manifest-coverage check. Per CLAUDE.md "Plans Run To Actual Completion" +
"Grep-Then-Read, Not Grep-Then-Conclude" — UAC-symbol-shipped ≠ data-flowing. Either tighten the ✅ criterion to "UAC +
adapter + manifest ≥ X%" consistently or split into ✅ (data flowing) vs 🟢 (code shipped, awaiting first backfill).
Several catalogue findings (DF-6 "live"-labelled vault venues with no adapter/handler/capability anywhere; DF-20
MARGINFI/SOLEND "live" but true ghosts) are exactly this mislabel class. | PRE_CUTOVER | defi-catalogue maintainer |
`/codex/02-data/defi-venue-protocol-catalogue.md` § "Status legend" + 2026-05-12 refresh deltas; cross-ref
`catalogue_audit_defi` DF-6/DF-20 |

### Tier 2 — instruments/manifest governance gaps

| #     | Finding (KEEP/LIFT/CONSOLIDATE/DELETE/ADD)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Disposition (IMMEDIATE/PRE_CUTOVER/POST_CUTOVER) | Owner                                     | Evidence (file:line)                                                                                                                                                                                                                  |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| IN-11 | **ADD** — `defi-data-type-taxonomy.md` documents the cluster-validation rule per bundled data*type (`options_chain`, `futures_chain`, `dex_pools` clusters, prediction `canonical_question_group`, sports per-fixture bundles) but has **no cross-link to the QG step that statically enforces it** (CLAUDE.md says "QG STEP 5.64 enforces statically"; "QG STEP 5.64" + the script `unified-trading-pm/scripts/quality_gates/check*\*.py`). Catalogue audits SP-10 (sports bundle writers — 0 hits for `expected_root_clusters`/`cluster_extractor` in MTDS+instruments sports adapters), PR-6 (`PREDICTION_GROUPS`cluster registry is a documented empty placeholder), TF-6 (no`futures_chain`row for any TradFi venue despite per-root cluster extraction in`databento_cme_converter.py`) all need the codex doc to point at the enforcing check so a violating callsite is caught at PR time. ADD the QG-step cross-reference + a "which adapters MUST pass cluster kwargs" table. | PRE_CUTOVER                                      | QG maintainer + defi-catalogue maintainer | `/codex/02-data/defi-data-type-taxonomy.md` (no QG path link); cross-ref `catalogue_audit_sports` SP-10, `catalogue_audit_prediction` PR-6, `catalogue_audit_tradfi` TF-6; CLAUDE.md § "Manifest + honest absence" cluster-validation |
| IN-12 | **ADD** — `availability-manifest-and-data-status.md` § "4-state `capture_status`" (`captured` / `empty_confirmed` / `attempted_failed` / `expected_unattempted`) documents the per-asset_group empty-rule asymmetry (sports/prediction CAN have `empty_confirmed` at instrument-day grain; cefi/defi/tradfi CANNOT — only venue-level HOLIDAY/WEEKEND/PRE_LAUNCH legit) but does NOT enumerate which **reference-data** data_types (instruments-service side, not MTDS) are exempt — e.g. sports `STANDINGS` / `INJURIES` / `FIXTURE_LINEUPS` cadence-driven refdata. Catalogue audit SP-6 surfaced the 2026-05-11 sports phantom-recon finding big `STANDINGS`/`SFI_LEAGUES`/`INJURIES` clusters "smelling like un-clipped pre-launch rows" with `KNOWN_COVERAGE_GAPS = {}` empty. The codex doc should document the reference-data-side empty/expected-unattempted rules per asset_group + cross-ref `sports-data-source-coverage-matrix.md`.                                        | PRE_CUTOVER                                      | manifest-evolution maintainer             | `/codex/02-data/availability-manifest-and-data-status.md` § "4-state capture_status"; cross-ref `catalogue_audit_sports` SP-6                                                                                                         |
| IN-13 | **ADD** — No codex doc documents the **instruments-service `reference_data/factory.py` auto-registration mechanism** (`CANONICAL_VENUE_TO_ADAPTER` is mutated at module-load by `_SUBGRAPH_VENUE_PREFIX_TO_PROTOCOL` + `_ADAPTERS` per `factory.py:180-181`). The catalogue audits had to grep-then-read this to discover CF-2 (`DRIFT-SOLANA` mapped, bare `DRIFT` not), CF-9 (`GMX`→`uniswap_v3` adapter key), DF-10 (`gmx`→`uniswap_v3` DEX-shape vs UAC `_PERPS` perp-shape mismatch). A codex doc (`instrument-pipeline-defi.md` is the closest home) should describe: how `canonical_venue` → `adapter_key` → adapter-class resolves, the subgraph-prefix fallback, and the `_PROTOCOL_TO_ADAPTER_KEY` indirection — so the next auditor doesn't re-derive it.                                                                                                                                                                                                                   | PRE_CUTOVER                                      | instruments-service maintainer            | `instruments-service/instruments_service/reference_data/factory.py:65,180-181,324-346`; cross-ref `catalogue_audit_cefi` CF-2/CF-9, `catalogue_audit_defi` DF-10; no codex doc covers it                                              |
| IN-14 | **ADD** — `per-instrument-sentinel-rollout.md` § 2 "Rollout tiers" table cites `_DEFAULT_PER_INSTRUMENT_SENTINEL_CAP = 50` (MVP) → 200 (Expanded) → 10000 (Full) and says "Expanded and Full are operator-driven" — but carries **no Runbook Execution-Owner block** for the tier-promotion (CLAUDE.md HARD RULE requires owner/cadence/verifier/last_executed for any operator-runnable promotion). It documents the "observability gates the human operator must check" (§ 3) but no named Tab/cron owns the promotion checkpoints. ADD the execution block.                                                                                                                                                                                                                                                                                                                                                                                                                         | PRE_CUTOVER                                      | MTDS sentinel maintainer + Ikenna         | `/codex/02-data/per-instrument-sentinel-rollout.md:§2,§3` (no `execution:` block)                                                                                                                                                     |
| IN-15 | **CONSOLIDATE** — `defi-data-types-catalog.md` (last updated 2026-04-24, "14 distinct data types") and `defi-data-type-taxonomy.md` (last updated 2026-05-10) and `defi-venue-protocol-catalogue.md` (2026-05-12) form a 3-doc set with overlapping "what data_types exist for DeFi" content but inconsistent counts (the taxonomy doc names data_types like `vault_share_price` / `staking_yields` / `liquidation_events` / `flash_loan_events` / `bridge_events` that catalogue audit DF-14/DF-15/DF-16/DF-19 found are declared-but-have-no-venue-capability-row). The 3 docs should declare one canonical "DeFi data_type ↔ venue capability ↔ adapter ↔ handler" matrix and the other two reference it; today an auditor must reconcile 3 docs + `defi_venue_capabilities.py` + `market_data_categories.py:NEEDS_CANDLE_PROCESSING` to know whether a data_type is real.                                                                                                          | PRE_CUTOVER                                      | defi-catalogue maintainer                 | `/codex/02-data/defi-data-types-catalog.md:7-13` vs `defi-data-type-taxonomy.md:7-16` vs `defi-venue-protocol-catalogue.md`; cross-ref `catalogue_audit_defi` DF-14/DF-15/DF-16                                                       |
| IN-16 | **ADD** — `availability-manifest-and-data-status.md` documents the phantom-audit's 7 drift axes but does NOT cross-reference the **40+ instruments-service one-off reconciler scripts** (`instruments-service/scripts/`: `reconcile_blank_error_reason_rows.py`, `reconcile_legacy_blank_to_typed_reason.py`, `reconcile_expected_absence_reasons.py`, `flip_phantom_to_attempted_failed.py`, `purge_pre_launch_manifest_rows.py`, `dedupe_manifest_schema_drift.py`, `fix_manifest_venue_casing.py` — the last one is exactly the CF-3/SP-3 case-folding remediation). These are operator-runnable but un-owned per CLAUDE.md "Runbook Execution-Owner SSOT". ADD a "manifest-remediation script index" table to the codex doc with per-script execution owner/cadence + flag the one-shot ones for deletion-after-run.                                                                                                                                                               | PRE_CUTOVER                                      | manifest-evolution maintainer             | `ls instruments-service/scripts/reconcile_*.py purge_*.py flip_phantom*.py fix_manifest*.py`; `/codex/02-data/availability-manifest-and-data-status.md` (no script index)                                                             |

### Tier 3 — stale / superseded / currency

| # | Finding (KEEP/LIFT/CONSOLIDATE/DELETE/ADD) | Disposition (IMMEDIATE/PRE_CUTOVER/POST_CUTOVER) | Owner | Evidence
(file:line) | |
--------------------------------------------------------------------------------------------------------- |
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| ------------------------------------------------ | ------------------------------------------------------- |
------------------------------------------------------------------------------------------------------------------------------------------------------

| ------------------------- |
------------------------------------------------------------------------------------------------------ | | IN-17 |
**LIFT** — `instrument-pipeline-defi.md` § "Per-Strategy Instrument Requirements" table lists strategy archetypes
`DEFI_STAKED_BASIS` / `DEFI_STAKED_BASIS_LIDO` / `DEFI_RECURSIVE_BASIS` (lines ~52-56) but the master plan's lead DeFi
archetype is `carry_staked_basis` (+ `leveraged_funding_arb`) per CLAUDE.md "Master Plan". The archetype names in this
doc predate the archetype canonicalisation (sibling Phase 1.B Strategy audit owns the full archetype-name sweep). LIFT
to current archetype vocabulary OR add a "superseded by `codex/09-strategy/...`" pointer. | PRE_CUTOVER | strategy
maintainer (defer to Phase 1.B) | `/codex/02-data/instrument-pipeline-defi.md:§ Per-Strategy Instrument Requirements` vs
`cursor-configs/CLAUDE.md` § "Master Plan" | | IN-18 | **CONSOLIDATE** — `data-catalogue-schema.md:17`
`gcp_path: gs://instruments-cefi-batch/...` + `aws_path: s3://instruments-cefi-batch/...` are hardcoded inline
bucket-name examples. Per CLAUDE.md "Bucket-name SSOT (b+)" + the data-area audit D-5 finding
(bucket-naming-and-config.md fully superseded by `resolve_bucket_name(...)`), the codex example should show the
canonical pattern via `resolve_bucket_name(cloud=..., kind="instruments", asset_group="cefi", env=...)` rather than a
literal `gs://`. The schema-validator that reads `data-catalogue.*.yaml` should also be checked against QG STEP 5.69. |
PRE_CUTOVER | bucket-naming maintainer | `/codex/02-data/data-catalogue-schema.md:17,38` vs `cursor-configs/CLAUDE.md` §
"Bucket-name SSOT (b+)"; cross-ref `codex_audit_data_2026_05_12.md` D-5 | | IN-19 ✅ FILED @
`plans/active/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md` (Sweep 1) | **LIFT** —
`defi-data-types-catalog.md` "Last updated: 2026-04-24" + `instrument-pipeline-defi.md` (no `Last verified`
front-matter) + `data-catalogue-schema.md` (no `Last verified`) — three instruments-area docs lacking currency stamps.
Per the Master Plan continuous-verification discipline, every codex doc touching a cutover-critical surface should carry
a `Last verified: <date>` line. ADD front-matter currency stamps + a "verify against UAC registry on next refresh" note.
| POST_CUTOVER | codex governance | `/codex/02-data/defi-data-types-catalog.md:6-7`; `instrument-pipeline-defi.md:1-3`;
`data-catalogue-schema.md:1-9` | | IN-20 ✅ FILED @
`plans/active/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md` (Sweep 3) | **CONSOLIDATE** —
`defi-venue-protocol-catalogue.md` and the catalogue_audit_defi findings disagree on whether several Solana DeFi
protocols (Kamino/Raydium/Orca/Marinade/Jito) have a "dedicated MTDS adapter" — the codex doc marks rows ✅ PRODUCTION;
DF-20 found they flow via the generic `solana_defi_handler.py` / `solana_lst_archival.py`, not a dedicated adapter. The
codex doc's ✅ is defensible (data flows) but the "MTDS adapter" axis column is misleading (no
`market_interface/adapters/defi/<protocol>.py` exists). Either change the axis column to "MTDS capture path (dedicated |
generic-solana | generic-subgraph)" or footnote each generic-routed row. | POST_CUTOVER | defi-catalogue maintainer |
`/codex/02-data/defi-venue-protocol-catalogue.md` § Solana rows; cross-ref `catalogue_audit_defi` DF-20 |

### Tier 4 — additions worth shipping

| #     | Finding (KEEP/LIFT/CONSOLIDATE/DELETE/ADD)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Disposition (IMMEDIATE/PRE_CUTOVER/POST_CUTOVER) | Owner                  | Evidence (file:line)                                                                                                                                                |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| IN-21 | **ADD** — A `/codex/02-data/catalogue-completeness-runbook.md` (or a section in `availability-manifest-and-data-status.md`) that names the **catalogue-reconciliation tooling chain end-to-end**: (1) the 5 `catalogue_audit_*` issue docs as the per-asset_group finding ledger; (2) the phantom-audit reconciler (`reconcile_phantom_manifest_rows_all.py`); (3) the UAC registry SSOTs per asset_group (`market_data_categories.py` / `defi_venues.py` / `*_instrument_universe.py` / `*_SOURCE_COVERAGE_START`); (4) the instruments-service `factory.py` adapter-registry consistency check; (5) the `verify_instrument_manifest_coverage.py` script. Today there is no single doc that tells a future auditor "run X then Y then Z to check the catalogue is complete" — which is why this Phase 1.G audit had to reverse-engineer it. | PRE_CUTOVER                                      | Ikenna (codex SSOT)    | new doc; anchors: 5 `catalogue_audit_*_2026_05_12.md` + `instruments-service/scripts/{reconcile_phantom_manifest_rows_all,verify_instrument_manifest_coverage}.py`  |
| IN-22 | **ADD** — A QG ratchet (new STEP 5.7x) that statically asserts **every venue id in `VENUES_BY_ASSET_GROUP[ag]` (and `ALL_DEFI_VENUES`) has at least one of: (a) an instruments-service adapter mapping in `CANONICAL_VENUE_TO_ADAPTER`, OR (b) a documented "no-instrument-universe" exemption** (per the IN-9 venue-class taxonomy). This is the static enforcement that would have caught the GHOST findings CF-9/CF-10 (bare `GMX`/`DRIFT` cefi venues with no adapter), DF-6 (vault venues marked "live" with nothing wired), DF-20 (MARGINFI/SOLEND "live" ghosts), SP-1 (`manifold` declared in capability but no venue/adapter), PR-7 (`MANIFOLD` orphan). The codex doc for the QG step should cite the catalogue audits as the motivating incidents.                                                                                | PRE_CUTOVER                                      | QG maintainer + Ikenna | cross-ref `catalogue_audit_cefi` CF-9/CF-10, `catalogue_audit_defi` DF-6/DF-20, `catalogue_audit_sports` SP-1, `catalogue_audit_prediction` PR-7; no QG step exists |

## Disposition counts

| Disposition  | Count  | Finding ids                                                                                                           |
| ------------ | ------ | --------------------------------------------------------------------------------------------------------------------- |
| IMMEDIATE    | 2      | IN-1, IN-2                                                                                                            |
| PRE_CUTOVER  | 16     | IN-3, IN-4, IN-5, IN-6, IN-7, IN-8, IN-9, IN-10, IN-11, IN-12, IN-13, IN-14, IN-15, IN-16, IN-17, IN-18, IN-21, IN-22 |
| POST_CUTOVER | 3      | IN-19, IN-20, (and IN-19/IN-20 currency items)                                                                        |
| **Total**    | **22** | IN-1 … IN-22                                                                                                          |

> Note: count by row = 22 findings (IN-1..IN-22). By disposition: 2 IMMEDIATE / 17 PRE_CUTOVER / 3 POST_CUTOVER (IN-17
> PRE_CUTOVER defers execution to Phase 1.B Strategy). Catalogue-audit findings elevated to codex-doc fixes:
> DF-1/DF-2/DF-3/DF-6/DF-8/DF-10/DF-11/DF-14/DF-15/DF-16/DF-18/DF-19/DF-20 (→ IN-1, IN-4, IN-10, IN-13, IN-15, IN-22),
> CF-1/CF-2/CF-3/CF-4/CF-9/CF-10/CF-12 (→ IN-2, IN-3, IN-13, IN-22), TF-4/TF-5/TF-6 (→ IN-9, IN-11),
> SP-1/SP-2/SP-3/SP-6/SP-10 (→ IN-3, IN-9, IN-11, IN-12, IN-22), PR-1/PR-6/PR-7 (→ IN-2, IN-11, IN-22).

## PRE_CUTOVER batch shipped 2026-05-12 (slot 8 sub-agent)

Per the slot 8 sub-agent (`ikenna-precutover-batch-data-instruments-strategy-execution`), 13 Instruments-area
PRE_CUTOVER findings landed in commit `38748f36 docs(codex): PRE_CUTOVER batch — 13 Instruments-area findings` (IN-17 +
IN-21 + IN-22 also shipped as part of the same commit batch):

| Finding | Disposition                   | Brief                                                    |
| ------- | ----------------------------- | -------------------------------------------------------- |
| IN-3    | PRE_CUTOVER ✅ DONE @38748f36 | Case-folding contract section (venue-availability.md)    |
| IN-4    | PRE_CUTOVER ✅ DONE @38748f36 | DeFi adapters list refreshed to 25 under adapters/defi/  |
| IN-5    | PRE_CUTOVER ✅ DONE @38748f36 | data-catalogue-schema.md `asset_group:` canonical key    |
| IN-6    | PRE_CUTOVER ✅ DONE @38748f36 | Phantom-audit reconciler `execution:` block              |
| IN-7    | PRE_CUTOVER ✅ DONE @38748f36 | defi-data-types-catalog.md `asset_group=defi/` canonical |
| IN-8    | PRE_CUTOVER ✅ DONE @38748f36 | venue-availability.md v8/v7 reconciliation banner        |
| IN-9    | PRE_CUTOVER ✅ DONE @38748f36 | Venue-class taxonomy section (5 classes)                 |
| IN-10   | PRE_CUTOVER ✅ DONE @38748f36 | defi-venue-protocol-catalogue ✅/🟢 split                |
| IN-11   | PRE_CUTOVER ✅ DONE @38748f36 | QG STEP 5.64 cluster-validation cross-link               |
| IN-12   | PRE_CUTOVER ✅ DONE @38748f36 | Per-asset-group + refdata empty-rule asymmetry           |
| IN-13   | PRE_CUTOVER ✅ DONE @38748f36 | factory.py auto-registration documented                  |
| IN-14   | PRE_CUTOVER ✅ DONE @38748f36 | sentinel-rollout tier-promotion `execution:`             |
| IN-15   | PRE_CUTOVER ✅ DONE @38748f36 | DeFi 3-doc reconciliation banner                         |
| IN-16   | PRE_CUTOVER ✅ DONE @38748f36 | Manifest-remediation script index                        |
| IN-17   | PRE_CUTOVER ✅ DONE @38748f36 | Archetype-name supersession note                         |
| IN-21   | PRE_CUTOVER ✅ DONE @38748f36 | Catalogue-completeness end-to-end runbook                |
| IN-22   | PRE_CUTOVER ✅ DONE @38748f36 | Venue-id-must-be-wired QG ratchet description            |

POST_CUTOVER tier (IN-19 currency stamps, IN-20 Solana DeFi adapter axis) remain for backlog.

IMMEDIATE tier (IN-1, IN-2) already DONE per prior slot 8 batches (@959ca3fc / @71d24b2e).
