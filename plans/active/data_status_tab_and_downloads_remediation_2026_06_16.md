---
title: Data-status tab + instruments download remediation (deployment-api / deployment-ui / CeFi universe)
created: 2026-06-16
parent_epic: deployment_and_user_management_master
assigned_vm: vm-operator-ops
status: active
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: 2026-06-16
source:
  - plans/audit/results/data_status_tab_and_instruments_download_audit_2026_06_16.md (root-caused findings A–H,
    file:line)
  - operator 2026-06-16 (data-status tab walkthrough; "blockers to mtds migration and downloads"; smoke-test downloads
    across all asset_groups + fix globally)
---

# Data-status tab + instruments download remediation

> Findings of record + every `file:line`:
> `plans/audit/results/data_status_tab_and_instruments_download_audit_2026_06_16.md`. **Operator-flagged blockers**: (1)
> instruments CSV **downloads** (Phase E — LAST, gated on the migration), (2) instruments/MTDS **migration-to-100%**
> (owned by `instruments_manifest_canonicalisation_2026_06_01.md` — see § Cross-plan blockers, do NOT re-implement
> here). Backend = deployment-api (Python QG); frontend = deployment-ui (tsc/ESLint/Vitest/Playwright — `[UI]` +
> `pw:L2 ✓` + regression spec required before ticking). Each worker reads `SUB_AGENT_MANDATORY_RULES.md` cold-start.

> **🔴 EXECUTION SEQUENCING (operator 2026-06-16) — downloads LAST, after the v9 manifest migration.** This plan sits in
> the migration chain's **TIER 4**. Hard order: **TIER 0** pipeline_mode Phase-0 code foundation
> (`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` — M1 full enum / M3 / M4 resolver /
> manifest-stamp fixes #1·#2·#3 / **GATE 0**) → **TIER 1** cleanup+correctness (catalogue lifecycle, provenance,
> honest-absence, instruments G1 universe/scope, TradFi naming, Deribit-spot — most can land now, independent of the
> migration) → **TIER 2** the real v9 `--apply` migrations per asset_group (gated on GATE 0) → **TIER 3** orphan-safety
> verification → **TIER 4 (this plan's DOWNLOAD work) LAST.** The **download path-drift fix (Phase D below) MUST target
> the FINAL canonical `pipeline_mode=…/venue=…` shape** — fixing it against the current v8 shape is wasted rework once
> the migration changes the path. The UI/scope/universe/naming items here are TIER-1 cleanup and may proceed
> independently; only the download path-fix is gated on the migration landing. Full landscape map:
> `plans/audit/results/data_status_tab_and_instruments_download_audit_2026_06_16.md` § Sequencing.

## Phase A (TIER 1 cleanup) — Scope + venue-filter correctness

- [ ] [CODE] P1. **instruments-service "out of scope" — PROPER fix** (audit §B): NOT the `scope_in=True` short-circuit
      (makes everything in-scope, kills the missing-catalogue signal). Add a reference-data expectation registry
      (`EXPECTED_REFERENCE_COVERAGE_BY_ASSET_GROUP` in UAC, or reuse the IS could-exist universe
      `enumerate_expected_universe` + per-venue genesis
      `data-catalogue.instruments-service.yaml`/`expected_start_dates.yaml`): in-scope ⟺
      `(asset_group, venue[, instrument_type])` ∈ set AND `day ≥ genesis`. Branch `_PER_VENUE_DAY_BUNDLE_SERVICES` in
      `breakdowns_core._classify_data_type_for_venue:673` onto it. Depends on the instrument_type-in-manifest item below
      to scope per type. — deployment-api + unified-api-contracts
- [ ] [DESIGN] P1. **instruments-service manifest carries `instrument_type` (per-type counts)** (audit §K): the writer
      currently records `instrument_type=""` (`engine/orchestrator/writers.py:172`), bundling future/option/spot/
      perpetual/combo into one blank row per venue/day — so derivative-rich venues (CME, Deribit, Binance) have no
      per-type coverage signal (root of the §J "no options visible"). Keep one catalogue parquet per venue/day (storage
      unit) but enrich the manifest row with `instrument_type` as a column with per-type counts. Unlocks per-type scope
      (above) + per-type drilldown in the UI. — instruments-service (+ UAC manifest schema if needed)
- [ ] [CODE] P1. **Venue filter — backend**: add a `venue: list[str] | None` param to the manifest path
      (`_status_core.py:139` + `services/data_status/manifest.py:114`), include it in `any_row_filter` (`:149-151`) and
      mask `_build_venue_breakdown` (`:589`) so venue narrows server-side. — deployment-api
- [ ] [UI] P1. **Venue filter — frontend**: add a `useEffect` that re-invokes `fetchData` when
      `selectedVenues`/`selectedFolders`/`selectedDataTypes` change, guarded to fire only after the first manual load
      and not while `loading` (mirror the manifest-mode effect at `DataStatusTab.tsx:807-814`). — deployment-ui `[UI]` +
      `pw:L2 ✓` + regression spec.

## Phase B (TIER 1 cleanup) — UI clarity (duplicate panels, pagination)

- [ ] [UI] P2. **Collapse duplicate "available" vs "available dates"** (audit §D): gate the legacy "Data Types" block
      (`DataStatusTab.tsx:4897-5045`) with `&& !hasHonestDataTypes` so it renders only when the honest panel is absent
      (preserve the per-day drill chips; eliminate the MTDS double-render). — deployment-ui `[UI]` + `pw:L2 ✓` +
      regression.
- [ ] [UI] P2. **Pagination visible-count selector**: add a `<select>` (50/100/200/1000/2000/All) bound to `DateList`'s
      `limit` state (`DataStatusTab.tsx:245-301,260,290-298`); one change covers all drill sites. Note the static
      server-truncation `+{N} more` labels (`:3891,3911,5386`, `VenuePillList :230`) need a backend `limit` bump to be
      client-pageable — file as a follow-on if the operator wants those expandable too. — deployment-ui `[UI]` +
      `pw:L2 ✓`.
- [ ] [UI] P3. **Rollup-difference clarity** (audit §F, by-design): optional small UI note/tooltip explaining IS is a
      per-venue/day reference bundle (no data_type axis) vs MTDS's 5-axis market-data shards — so the structurally
      different drilldown reads as intentional, not broken. — deployment-ui

## Phase C (TIER 1 cleanup) — CeFi universe extension (instruments completeness + EigenLayer dust)

- [x] ✅ [CONFIG] P1. **Extend `CEFI_BASE_ASSET_UNIVERSE`** (audit §G) — DONE unified-api-contracts@f4f7f8e (operator
      2026-06-16 "add the rest"): added `EIGEN` (EigenLayer rewards dust) +
      `AAVE, ALGO, AXS, CHZ, COMP, DASH, ENJ, EOS,     FIL, GALA, ICP, MANA, SAND, THETA, XLM, ZEC` to the frozenset
      (~28→~45); regression test `tests/test_cefi_universe_coverage.py`; QG green. All three adapters
      (tardis/hyperliquid/aster) import it. — unified-api-contracts
- [ ] [DATA] P1. **Re-enumerate + re-capture** the IS catalogue for the added bases so they appear in the universe +
      downloadable CSV (re-run the IS CLI per affected venue/date; the universe edit alone doesn't backfill past days).
      Cross-links the capture-freeze item below. — instruments-service
- [ ] [TEST] P2. UAC unit test asserting EIGEN + the added bases pass `_passes_asset_filter` for binance-spot (USDT) and
      hyperliquid; guards accidental universe shrink. — unified-api-contracts / instruments-service

## Cross-plan blockers — instruments/MTDS migration to 100% (do NOT re-implement here)

These are **operator-flagged blockers to MTDS migration**, owned by existing plans — a finding callout is being added to
the canon plan; track there, not as duplicate todos:

- v9 `--apply` is 🔴 GATED on `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` Phase-0; then E3–E6
  (drain/run/manifest-rebuild/verify) in `instruments_manifest_canonicalisation_2026_06_01.md:189-194`.
- ~40% cefi `_index` null-`capture_status`-with-count>0 rows + phantoms → honest relabel via the v9 walk (CF-10) +
  `reconcile_phantom_manifest_rows_all.py` (reconcile, recovers most of the missing %).
- Real capture-freeze ~2026-05-21 fleet-wide (defi 05-07; tradfi degraded 16K→2/day then stopped 05-22 — anomalous,
  needs root-cause) → un-freeze IS daily capture + backfill via the IS CLI
  (`proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md:194-212,418`).

## Phase D (TIER 1 cleanup) — TradFi canonical naming + Deribit spot fix (instruments-service / UAC)

- [ ] [DESIGN] P1. **TradFi human-canonical naming — NO Databento dependency** (audit §I; operator 2026-06-16: "convert
      without using databento, we don't have billing perms; infer they're just exchange codes, we know the logic"). The
      conversion needs NO Databento API call — derive purely from the EXISTING UAC exchange-code registry
      (`tradfi_instrument_universe.py` `DatabentoInstrumentDef.base_asset` + `EXCHANGE_CODE_TO_NAME`) in the adapter
      `_parse_row_to_record` (`adapters/tradfi/databento/adapter.py:637-709`): extract the exchange-code root from
      `raw_symbol` (incl. spaced options like `E5AH0 …`) → map to the human product root (`ES→SP500`) for a canonical
      base + canonical `underlying`. **Keep the raw exchange code as `raw_symbol`** (operator: "we do wanna keep
      exchange codes in instrument definitions as raw symbol anyway, just having the canonicals too"). —
      instruments-service
- [ ] [SCHEMA] P1. **Add canonical instrument-id + base/root fields to `InstrumentRecord`** (audit §I/§2): additive
      optional fields `canonical_instrument_id` + `product_root`/`canonical_base` in UAC
      `internal/reference/instrument.py:90` (1:1 into `INSTRUMENTS_PARQUET_SCHEMA`; not in the CeFi-only
      `model_validator` `:318`). `raw_symbol` stays the raw exchange code; canonicals are additive. Downstream (CSV
      download, options↔future bundling) reads the canonical fields. — unified-api-contracts (+ IS writer/serializer)
- [ ] [CODE] P1. **Fix Deribit spot being dropped** (audit §J; operator correction 2026-06-16: Deribit DOES have spot
      now). Remove `deribit` from `_DERIVATIVES_ONLY_EXCHANGES` (`tardis/adapter.py:95-97`) — or make it date-aware
      (spot only post-launch ~2023); the `:719-729` spot-drop + stale `:721` "deribit has no spot" comment must go.
      Validate Tardis returns Deribit spot + it passes `CEFI_BASE_ASSET_UNIVERSE`. — instruments-service
- [ ] [DATA] P2. **Verify Deribit BTC/ETH options present** (audit §J): run-verify a representative day has BTC/ETH
      options in the batch catalogue (Tardis DERIBIT path; check the endpoint tier didn't drop option metadata).
      **Operator 2026-06-16: BTC/ETH underlyings are FINE for now** — do NOT widen `CEFI_OPTIONS_UNDERLYINGS` or wire
      the dedicated `DERIBIT-OPTIONS` adapter. — instruments-service

## Phase E (TIER 4 — LAST, 🔴 GATED on the v9 `--apply` migration) — Download path-drift + all-asset-group smoke test

> **Do NOT start until TIER 2 (the per-AG v9 `--apply` migration) has landed** — the path-fix must target the FINAL
> canonical `pipeline_mode={mode}_{source}/…/venue=…` shape, not the current v8 shape (operator 2026-06-16: downloads
> last). The smoke-test (first item) MAY run earlier to record the before-state, but the path-template fix lands against
> the migrated shape.

- [ ] [DATA] P1. **Smoke-test instrument/shard CSV download for a representative AVAILABLE shard per asset_group**
      against prod (`https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app`, `DISABLE_AUTH=true`): DeFi (aave_v3 + a
      Solana protocol, with chain), CeFi (binance-futures), TradFi, Sports (with league_id), Prediction. Record HTTP
      code + whether bytes returned. Establishes the before-state + which axes break. — deployment-api
- [ ] [CODE] P1. **Fix DeFi download path-drift against the FINAL v9 shape** (audit §A): thread `chain` from
      `download_shard_csv` (`_downloads.py:407`) into `build_instruments_shard_csv_export` and reconstruct the
      **combined** DeFi venue token for the `venue=` GCS segment (`f"{venue}-{chain}"`, matching
      `canonicalize_defi_venue_combined`) in `services/data_status_drilldown/_csv_export.py:307-339`; mirror in the
      drilldown reader `_instruments.py:62-70`. Verify against the **post-migration** writer truth + the new
      `pipeline_mode=…` prefix. — deployment-api
- [ ] [CODE] P1. **Apply the same fix to any MTDS chain/protocol-partitioned download path** if the smoke test shows
      MTDS DeFi shards 502 the same way (operator: "fix them globally so for MTDS too"). — deployment-api
- [ ] [TEST] P1. Regression: a download-path unit test that builds the GCS object path for a DeFi shard and asserts it
      matches the (migrated) writer's combined-venue/chain shape (guards the split-venue drift from recurring). —
      deployment-api

## Success criteria

- All-asset-group download smoke test green (200 + non-empty CSV) for DeFi/CeFi/TradFi/Sports/Prediction.
- instruments-service drilldown rows no longer all "out of scope"; venue filter narrows results (UI + API).
- No duplicate available/available-dates panels; pagination selector works; QG green per repo; UI todos carry
  `pw:L2 ✓` + regression spec.
- EIGEN + requested bases present in a downloaded binance-spot/hyperliquid instruments CSV (after re-capture).
- TradFi instruments carry a human-canonical base/root + instrument-id (not raw `ESM0`); Deribit BTC/ETH options present
  in the catalogue (or operator-confirmed scope).
