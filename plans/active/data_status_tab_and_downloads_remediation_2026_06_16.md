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
> instruments CSV **downloads** (P0 below), (2) instruments/MTDS **migration-to-100%** (owned by
> `instruments_manifest_canonicalisation_2026_06_01.md` — see § Cross-plan blockers, do NOT re-implement here). Backend
> = deployment-api (Python QG); frontend = deployment-ui (tsc/ESLint/Vitest/Playwright — `[UI]` + `pw:L2 ✓` + regression
> spec required before ticking). Each worker reads `SUB_AGENT_MANDATORY_RULES.md` cold-start.

## Phase 0 — Download path-drift (BLOCKER: downloads) + all-asset-group smoke test

- [ ] [DATA] P0. **Smoke-test instrument/shard CSV download for a representative AVAILABLE shard per asset_group**
      against prod (`https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app`, `DISABLE_AUTH=true`): DeFi (aave_v3 + a
      Solana protocol, with chain), CeFi (binance-futures), TradFi, Sports (with league_id), Prediction. Record HTTP
      code + whether bytes returned. Establishes the before-state + which axes break. — deployment-api
- [ ] [CODE] P0. **Fix DeFi download path-drift** (audit §A): thread `chain` from `download_shard_csv`
      (`_downloads.py:407`) into `build_instruments_shard_csv_export` and reconstruct the **combined** DeFi venue token
      for the `venue=` GCS segment (`f"{venue}-{chain}"`, matching `canonicalize_defi_venue_combined`) in
      `services/data_status_drilldown/_csv_export.py:307-339`; mirror in the drilldown reader `_instruments.py:62-70`.
      Verify against the writer truth (`instruments-service/.../engine/orchestrator/writers.py:77-91,181`). —
      deployment-api
- [ ] [CODE] P0. **Apply the same fix to any MTDS chain/protocol-partitioned download path** if the smoke test shows
      MTDS DeFi shards 502 the same way (operator: "fix them globally so for MTDS too"). — deployment-api
- [ ] [TEST] P0. Regression: a download-path unit test that builds the GCS object path for a DeFi shard and asserts it
      matches the writer's combined-venue/chain shape (guards the split-venue drift from recurring). — deployment-api

## Phase 1 — Scope + venue-filter correctness

- [ ] [CODE] P1. **instruments-service "out of scope" fix** (audit §B): in `breakdowns_core.py:673` short-circuit
      `scope_in=True` (skip out_of_scope) when `service` ∈ `_PER_VENUE_DAY_BUNDLE_SERVICES` (reference data has no
      market-data scope policy), OR add a reference-data scope registry in UAC `expected_coverage.py`. — deployment-api
- [ ] [CODE] P1. **Venue filter — backend**: add a `venue: list[str] | None` param to the manifest path
      (`_status_core.py:139` + `services/data_status/manifest.py:114`), include it in `any_row_filter` (`:149-151`) and
      mask `_build_venue_breakdown` (`:589`) so venue narrows server-side. — deployment-api
- [ ] [UI] P1. **Venue filter — frontend**: add a `useEffect` that re-invokes `fetchData` when
      `selectedVenues`/`selectedFolders`/`selectedDataTypes` change, guarded to fire only after the first manual load
      and not while `loading` (mirror the manifest-mode effect at `DataStatusTab.tsx:807-814`). — deployment-ui `[UI]` +
      `pw:L2 ✓` + regression spec.

## Phase 2 — UI clarity (duplicate panels, pagination)

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

## Phase 3 — CeFi universe extension (BLOCKER-adjacent: instruments completeness + EigenLayer dust)

- [ ] [CONFIG] P1. **Extend `CEFI_BASE_ASSET_UNIVERSE`** (audit §G) in
      `unified-api-contracts/.../registry/cefi_instrument_universe.py:19` — add `EIGEN` (EigenLayer rewards dust) +
      `AAVE, ALGO, AXS, CHZ, COMP, DASH, ENJ, EOS, FIL, GALA, ICP, MANA, SAND, THETA, XLM, ZEC`. Single frozenset edit;
      all three adapters (tardis/hyperliquid/aster) import it. Confirm with operator whether the curated-subset cap
      (~28→~45 coins) is intended before widening. — unified-api-contracts
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

## Phase 4 — TradFi canonical naming + Deribit options coverage (instruments-service / UAC)

- [ ] [DESIGN] P1. **TradFi human-canonical naming** (audit §I): use the EXISTING-but-unused UAC mapping
      (`tradfi_instrument_universe.py` `DatabentoInstrumentDef.base_asset`/`EXCHANGE_CODE_TO_NAME`) in the Databento
      adapter `_parse_row_to_record` (`adapters/tradfi/databento/adapter.py:637-709`) to set a human-canonical product
      root as `base_asset` (`ES→SP500`) + a canonical `underlying`, while keeping `raw_symbol` raw. Also parse the
      spaced-option root (`E5AH0 …`) so the fallback stops emitting the per-contract code. — instruments-service
- [ ] [SCHEMA] P1. **Add canonical instrument-id + base/root fields to `InstrumentRecord`** (audit §I/§2): additive
      optional fields `canonical_instrument_id` + `product_root`/`canonical_base` in UAC
      `internal/reference/instrument.py:90` (1:1 into `INSTRUMENTS_PARQUET_SCHEMA`; not in the CeFi-only
      `model_validator` `:318`). Populate from Phase-4 DESIGN above; downstream (CSV download, options↔future bundling)
      reads the canonical fields. — unified-api-contracts (+ instruments-service writer/serializer)
- [ ] [DATA] P1. **Verify Deribit options coverage** (audit §J): run-verify whether BTC/ETH Deribit options are present
      in the batch catalogue for a representative day (the dedicated `DeribitOptionsReferenceDataAdapter` is NOT in
      `_CEFI_VENUES`; batch options come only via Tardis DERIBIT, filtered to BTC/ETH; check the Tardis endpoint tier
      didn't drop option metadata). Spot is legitimately absent (Deribit derivatives-only) — not a bug. —
      instruments-service
- [ ] [CODE] P2. **(operator-gated) Full Deribit option/combo batch coverage**: if BTC/ETH-only is insufficient, add
      `DERIBIT-OPTIONS` to `_CEFI_VENUES` (`engine/orchestrator/venue_core.py:90`) to run the dedicated adapter, and/or
      widen `CEFI_OPTIONS_UNDERLYINGS` beyond `{BTC,ETH}`. Confirm desired underlyings with operator first. —
      instruments-service / unified-api-contracts

## Success criteria

- All-asset-group download smoke test green (200 + non-empty CSV) for DeFi/CeFi/TradFi/Sports/Prediction.
- instruments-service drilldown rows no longer all "out of scope"; venue filter narrows results (UI + API).
- No duplicate available/available-dates panels; pagination selector works; QG green per repo; UI todos carry
  `pw:L2 ✓` + regression spec.
- EIGEN + requested bases present in a downloaded binance-spot/hyperliquid instruments CSV (after re-capture).
- TradFi instruments carry a human-canonical base/root + instrument-id (not raw `ESM0`); Deribit BTC/ETH options present
  in the catalogue (or operator-confirmed scope).
