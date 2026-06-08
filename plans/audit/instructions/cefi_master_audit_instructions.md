---
name: cefi_master_audit_instructions
type: audit-instructions
epic: cefi_master
assigned_vm: vm-cefi
tier: L0
last_updated: 2026-06-01
---

# CeFi Master — Audit Instructions

> **🔄 ALIGNED 2026-06-08 — pre-apply readiness audit + source-aware/Era-B model (SSOT wins where this differs).**
> Data-form SSOT = `canonical_form_cross_service_audit_checklist.md` (**CF-1…CF-14**, incl. **CF-13** source-aware
> `pipeline_mode={mode}_{source}[_{transport}]` + **CF-14** IS-catalogue could-exist root) + the **①–⑫ pre-apply
> readiness audit** in `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` (esp. ⑩ **Era-B**:
> `options_chain`/`futures_chain`=instrument_type+`data_type=trades`; ⑪ **batch=live / no-regression**; ⑧ catalogue
> completeness; ⑫ rollback snapshot). Any text below assuming coarse `pipeline_mode=batch`, `data_type=options_chain`,
> or a non-source-aware manifest is STALE — audit against the SSOT.

## Epic Scope

CeFi adapters for all supported venues, CCXT adapter layer, CEFFU custody (June-1), perp funding adapters, spot price
adapters, and the perp hedge legs used in DeFi+CeFi hybrid archetypes.

Key venues: Binance, Bybit, OKX, Deribit, Hyperliquid, Aster, Kraken (7+ venues). Key code surfaces: venue adapters in
MTDS, perp funding readers, spot price readers, CeFi archetype definitions.

## Triggers

- Weekly (minimum cadence)
- After any venue API version bump (Binance API v4, OKX v5, etc.)
- When perp funding data shows manifest gaps (`empty_confirmed` without valid reason for cefi rows)
- When `instruments_master` adds or removes a venue from the universe
- After CEFFU custody provider integration changes

## Checklist

- [ ] (a) **Error classification wired**: all 7+ CeFi venues have `classify_venue_error()` called in their adapters.
      Grep: `rg "classify_venue_error" market-tick-data-service/ --include="*.py"` — verify each venue handler present

- [ ] (b) **ADAPTER_FETCH_FAILED emitted**: every adapter emits `ADAPTER_FETCH_FAILED` event on error path. Grep:
      `rg "ADAPTER_FETCH_FAILED" market-tick-data-service/ --include="*.py"`

- [ ] (c) **No hardcoded venue universe**: QG `no_hardcoded_venue_universe.sh` passes. Run:
      `bash scripts/quality-gates/no_hardcoded_venue_universe.sh`

- [ ] (d) **IS→MTDS contract honored**: CeFi MTDS handlers derive venue URLs from instruments-service, not hardcoded.
      Run: `bash scripts/quality-gates/no_hardcoded_venue_urls.sh` Verify: `no_silent_absence_handlers.sh` passes

- [ ] (e) **Perp funding + spot batch/live parity**: all 7+ venue funding adapters have both `--mode batch` and
      `--mode live` implemented. Check: `a6_batch_live_adapter_parity.py` output for cefi rows — batch count == live
      count per venue

- [ ] (f) **CEFFU custody codex alignment**: `codex/04-architecture/custody-providers.md` describes CEFFU correctly.
      Verify the June-1 timeline is documented and code reflects the May-23 `CLOUD_KMS_ENCRYPTED` path.

- [ ] (g) **DeFi+CeFi hybrid hedge leg**: perp hedge leg for `carry_staked_basis` archetype wires correctly to the CeFi
      execution path. Read: `codex/09-strategy/architecture-v2/archetypes/` — verify hybrid architecture description
      matches code

- [ ] (h) **No banned reasoning for missing venues**: every venue in the universe has an adapter or a
      `BLOCKED-CREDENTIALS` ping filed. No silent deferrals. Check: `human_led_audit_pool_2026_05_21.md` +
      `instruments-service` universe list

### Dual-source provenance (the `source` column + SOURCE_PRIORITY)

> Codified 2026-06-01 (crosscutting plan: `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`).
> **Provenance is UNIVERSAL: every CeFi cell stamps its `source` NOW, even though CeFi has only one source today
> (`tardis`).** Operator 2026-06-01: "I may find an alternative for Tardis, so it's the same issue." If you only stamp
> once a 2nd source appears, the existing Tardis corpus is unlabelled and indistinguishable after the swap. Design: same
> hive drop, disambiguated by a **row-level `source` column** + a per-source manifest row, resolved downstream via UAC
> `SOURCE_PRIORITY` when >1. **Current state (audit 2026-06-01): CeFi writes `source=""` → RED.** Data-state verifiable,
> not constant-verifiable.

- [ ] (i) **Writers stamp `source="tardis"` on EVERY CeFi cell now**: CeFi adapter writes pass `source=`;
      `record_empty_for_shard` / `record_failed_for_shard` accept + forward `source`.
      `market-data-processing-service/.../core/canonical_writer.py`. Read ACTUAL prod CeFi rows — **RED on any blank
      `source`** (not just multi-source cells). No `SOURCE_PRIORITY` change needed yet (`tardis` already declared).
- [ ] (j) **Expand `SOURCE_PRIORITY` only when an alternative lands**: when a live per-venue path or a Tardis
      replacement is actually added, append it to the entry (e.g. `["<venue>_live", "tardis"]`) — at which point
      resolution (item l) engages. `unified-api-contracts/.../canonical/crosscutting/source_priority.py:152-160`.
- [ ] (k) **`source` is a column, not a path key**: no `source=`/`data_source=` hive segment in CeFi GCS paths — both
      sources co-mingle on `day=…/asset_group=cefi/venue=…/data_type=…/`.
- [ ] (l) **Read-time reconciliation wired**: 2-source fixture (Tardis + venue_live, same instrument+ts, co-mingled in
      one folder) → consumer emits exactly ONE resolved row via `select_primary_available_source()`; no silent
      double-count.

### E2E Batch, Paper, and Live Verification

- (e2e-batch) **Batch e2e**: For the MVP archetypes of this domain, run a dry-run batch audit using mock upstream
  fixtures (`CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local`) — confirm signals are generated end-to-end from adapter output
  through strategy. If real upstream unavailable, synthetic fixtures from `tests/e2e/fixtures/` suffice; the test MUST
  exercise the downstream code regardless of upstream readiness.
- (e2e-paper) **Paper trading audit** (once paper is running): confirm paper PnL events flow from strategy → execution →
  PnL calculator for ≥1 MVP archetype in this domain. Check manifest for strategy_output rows with
  `capture_status=captured` for the date range. If paper not yet running, verify the code path is wired (not
  BLOCKED-CREDENTIALS level — code exists, paper not started).
- (e2e-live) **Live trading audit** (once live is running): verify live execution produces execution_record rows in
  manifest with no DIVERGENT_EMPTY. Alert thresholds fire within SLA. PnL reported correctly.
- (mock-upstream) **Mock upstream pattern**: this domain's audit MUST be runnable WITHOUT live upstream data. Document
  the exact `pytest` fixtures or `CLOUD_MOCK_MODE=true` invocation in `## Output Format` so any slot can run the
  downstream-only audit independently.

- [ ] (consolidation-health) **Per-group manifest consolidation health**: cefi's consolidated
      `gs://market-data-tick-cefi-prd-<pid>/_index/availability_index.parquet` is fresh (mtime advances ~per
      consolidator cycle) and its per-VM shards consolidate without OOM. cefi is the largest asset_group and was the
      genesis of the DuckDB memory-bound rewrite. Cross-ref the engine + 24h OOM/freshness recipe in
      `manifest_master_audit_instructions.md` (h2/h3) + `manifest_consolidator_duckdb_memory_fix_2026_05_26.md`. Check:
      `gcloud storage objects describe gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet --format='value(updated)'`
      within minutes of now.
- [ ] (enumerator-reseed) **One-time — MIGRATED FROM `manifest_consolidator_duckdb_memory_fix_2026_05_26.md`**: re-run
      the cefi expected-universe enumerator
      (`instruments-service/scripts/enumerate_expected_universe.py --asset-group cefi`) so the `slot4-cefi-c*`
      denominator shards carry the full v8+ schema. The NULL-`schema_version` enumerator fix shipped (IS@9f831578); the
      re-run itself is still pending — without it the expected-universe (coverage denominator) for cefi is under-seeded
      relative to the captured numerator.

## Canonical-form coverage (CF-1…CF-12)

> Cites the SSOT `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md`. Run CF-1…CF-12 against the
> `market-data-tick-cefi-prd-…` `_index` + objects (DATA-STATE). Remediation owner =
> `cefi_manifest_canonicalisation_2026_06_01.md`. CF-4 (`source` column = `tardis`, swap-resilient) covered by the
> Dual-source provenance section above.

- [ ] (CF-1/2/3/8/9/10/12) SSOT checks on `market-data-tick-cefi-prd-…`: schema_version=v9 (data-state) · `asset_group=`
      not `category=` (paths+rows) · `pipeline_mode=` partition (`batch_tardis`/`live_websocket`) · honest
      `available_at` · env-split bucket · no phantom captured · batch=live. GREEN = all data-state.
- [ ] (CF-5 cefi reasons) every empty cefi cell typed: `EXPECTED_KNOWN_SOURCE_GAP` (documented outage) / genuine
      `SOURCE_RETURNED_ZERO`; 0 blank/mislabeled.
- [ ] (CF-7 cefi names) underscore data*type
      (`book_snapshot_5`/`trades`/`derivative_ticker`/`liquidations`/`ohlcv*\*`) +     flat venue (`BINANCE-SPOT`/`UPBIT`/`COINBASE-SPOT`/…)
      canonical.

## CeFi-specific standing checks (added 2026-06-08) — Era-B chains + venue source model

- [ ] (cefi-erab) **Era-B on disk** — byte-probe a recent DERIBIT/OKX chain shard in `market-data-tick-cefi-prd`:
      `options_chain`/`futures_chain` appear ONLY as `instrument_type=`, with `data_type=trades`, and
      `data_type=(options_chain|futures_chain)` count = 0. The live writer (`tardis_shared.py` `_LEGAL_DATA_TYPES`)
      raises on `data_type=options_chain`.
- [ ] (cefi-grain) **venue-aware bundle-grain (F2)** — `options_chain`/`futures_chain` enumerate ONE could-exist
      candidate per UNDERLYING (`data_type=trades`), NOT per-leaf OPTION/COMBO; venues that bundle (DERIBIT/OKX) vs any
      per-contract venue handled correctly; DERIBIT no longer dominates the candidate count.
- [ ] (cefi-source) **source model** — batch `source` = `tardis` (the archive); live/replay `source` = the venue
      (binance/okx/deribit/kraken/bybit/hyperliquid/aster). Tardis = {batch, live}, NO replay (academic licence). Every
      cell carries a non-blank `source` from `SOURCE_PRIORITY`.
- [ ] (cefi-venues) **MVP venue coverage** — perp funding + spot across
      binance/bybit/okx/deribit/hyperliquid/aster/kraken either green or `BLOCKED-CREDENTIALS` with a named ask (no
      silent drop).

## Success Criteria

- All 8 scaffold checklist items (a)–(h) GREEN
- Dual-source provenance items (i)–(l) GREEN against actual prod data-state (zero blank `source` on any multi-source
  CeFi cell; 2-source fixture resolves to one row, no double-count)
- `a6_batch_live_adapter_parity.py` shows 100% parity for `asset_group=cefi` rows
- Manifest divergence A3: zero `MISSING_EXPECTED` for cefi asset_group
- QG exits 0 for MTDS + instruments-service
- e2e batch audit produces signals for ≥1 MVP archetype using mock upstream data (CLOUD_MOCK_MODE=true green)
- Paper trading goal post: ≥1 archetype runs ≥7 continuous paper days without silent failures

## Output Format

Result file at `plans/audit/results/cefi_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
