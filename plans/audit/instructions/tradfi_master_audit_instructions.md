---
name: tradfi_master_audit_instructions
type: audit-instructions
epic: tradfi_master
assigned_vm: vm-tradfi
tier: L0
last_updated: 2026-06-01
---

# TradFi Master — Audit Instructions

## Epic Scope

TradFi adapters (Databento + MASSIVE — the dual-source pair; Polygon.io is a REMOVED TradFi provider per CLAUDE.md, do
not reference it), CME dated futures, options pricing, VIX 15m feed (Yahoo + Barchart layering), and TradFi archetypes:
S&P prediction (CME) and price arbitrage (CME futures + ETFs). Credential-gated adapters expected since subscriptions
are required — audit for scaffold completeness, not live data. Both vendors co-mingle on the same hive drop and are
disambiguated by a row-level `source` column (see § "Dual-source provenance").

## Triggers

- Weekly (minimum cadence)
- After Databento or Polygon.io API version changes
- When strategy-service reports missing TradFi feature data
- After any new instrument type is added to the TradFi universe

## Checklist

- [ ] (a) **Databento adapter scaffold**: adapter file exists with correct UAC schema, auth shape, retry/backoff,
      rate-limit, and error classification. Find: `rg "databento" market-tick-data-service/ --include="*.py" -l`

- [ ] (b) **MASSIVE adapter scaffold**: same requirements as Databento (REST connector per
      `tradfi_massive_dual_source_2026_05_28.md` Phase 4). Find:
      `rg -i "massive" market-tick-data-service/ --include="*.py" -l`. (Polygon.io is removed — if any `polygon` TradFi
      data reference remains, RED-flag it for removal.)

- [ ] (c) **Credential-gated tests marked**: integration tests for both adapters have
      `@pytest.mark.requires_credentials` and are skipped by default in CI. Grep:
      `rg "requires_credentials" market-tick-data-service/tests/ --include="*.py"`

- [ ] (d) **VIX 15m implementation**: Barchart preload path + Yahoo Finance rolling 60d + honest gap documented. Grep:
      `rg "VIX|vix" market-tick-data-service/ --include="*.py"` — verify all 3 paths present Check: UAC constants in
      `registry/data_source_continuity.py` are current

- [ ] (e) **CME dated contract roll logic**: roll logic follows codex specification (no hardcoded expiry dates). Read:
      relevant adapter + verify against codex/09-strategy/architecture-v2/archetypes/ TradFi archetype docs

- [ ] (f) **No hardcoded bucket names**: `resolve_bucket_name()` used for all TradFi GCS operations. Run: QG STEP 5.69
      passes for all TradFi adapters

- [ ] (g) **Credential asks filed**: any adapter without live credentials has a `BLOCKED-CREDENTIALS` ping in
      `ikenna_orchestrator/pings/` with vendor, tier, cost estimate, and unblocks listed.

### Dual-source provenance (the `source` column + SOURCE_PRIORITY)

> Codified 2026-06-01. TradFi cells may be populated by more than one vendor over time (`databento` + `massive`, plus
> `yahoo` / `barchart` for VIX 15m). The design (SSOT: `tradfi_massive_dual_source_2026_05_28.md` Phase 3 +
> `codex/02-data/contracts-scope-and-layout.md` § "TradFi canonical schema — dual-source `source` column"): **same hive
> drop, vendors disambiguated by a row-level `source` column + per-source manifest row — NOT by a `source=` path key.**
> Every item below is **data-state verifiable, NOT constant-verifiable** — read actual rows, never trust
> `MANIFEST_SCHEMA_VERSION`. (Reference incident: manifest-v8, where the constant said 8 while 0% of 7.4M prod rows were
> v8.)

- [ ] (h) **`source` column present + non-NULL on prod TradFi parquets** (DATA-STATE, not constant). Sample real prod
      parquets across each `(venue, data_type)` TradFi cell and read the actual `source` column value distribution. RED
      if any TradFi parquet has a missing / NULL / empty `source` column. Report the per-cell source-value histogram
      (how many rows `databento` vs `massive` vs blank). Do NOT infer GREEN from `MANIFEST_SCHEMA_VERSION==9`.

- [ ] (i) **Manifest `source` field populated for every TradFi row**. Query consolidated manifest rows where
      `asset_group=tradfi`; assert `source` ∈ closed set `{databento, massive, yahoo, barchart}` with zero blank.
      Confirm the write-time gate is live: `MissingSourceError` raised when `category=="tradfi"` and `source==""`
      (`unified-trading-library/.../manifest_writer.py`), and QG STEP 5.64
      (`check_tradfi_source_explicit_at_record_captured.py`) exits 0.

- [ ] (j) **`source` is a column, NOT a hive partition key**. Verify no `source=` segment crept into any TradFi GCS path
      — both vendors share `day=…/asset_group=tradfi/venue=…/data_type=…/`. Grep the writer path construction +
      `bucket_naming.py`: `rg "source=" market-data-processing-service/ market-tick-data-service/ --include="*.py"` must
      show no path-key usage (only the kwarg / column).

- [ ] (k) **SOURCE_PRIORITY registry covers every multi-vendor TradFi cell**. For every `(tradfi, <data_type>)` that has
      ≥2 possible vendors, an ordered entry exists in
      `unified-api-contracts/.../canonical/crosscutting/source_priority.py`; the source strings exactly match the
      adapter constants (closed set, no typos); ordering reflects the intended preference (live-emitter /
      broader-coverage wins).

- [ ] (l) **Read-time reconciliation is WIRED in consumers** (the downstream-smoothness check). Read the canonical read
      path (`unified-trading-library/.../manifest_reader_fallback.py` `read_manifest_with_source_priority()`) AND at
      least one real consumer (features-service). Confirm that when both vendor parquets co-mingle in one folder, the
      consumer resolves via the `source` column + `select_primary_available_source()` — it does NOT blindly glob+concat
      both files (silent double-count) nor pick arbitrarily. Construct a 2-source fixture (same instrument+timestamp
      from `databento` and `massive`) and assert the consumer emits exactly one resolved row per (instrument, ts).

- [ ] (m) **Conflict detection runs, never silently drops**. `detect_dual_source_conflicts()` is invoked at
      consolidation / audit time; `DUAL_SOURCE_DUPLICATE` / `VALUE_DIVERGENCE` / `COVERAGE_DIVERGENCE` are emitted to
      the manifest / divergence report (not swallowed). Verify on a divergent 2-source fixture that the divergence is
      surfaced.

- [ ] (n) **`available_at` parity across sources (batch = live)**. Historical rows from EITHER vendor are timestamped
      with the `available_at` we'd have in live mode for the SOURCE_PRIORITY top entry (per `source_priority.py`
      header), not the slower archive time of whichever vendor wrote them. Sample rows from each source and compare
      `available_at` derivation — divergent per-source `available_at` for the same cell breaks batch-live symmetry.

- [ ] (o) **Backfill provenance complete** (BLOCKED on Phase 5 / `MASSIVE_API_KEY`). Pre-Phase-3 TradFi parquets stamped
      `source='databento'` via the backfill script; zero NULL-`source` rows post-backfill; manifest re-consolidated with
      `source` populated. Status stays `BLOCKED-CREDENTIALS` until the key lands — but item (h) still RED-flags any
      blank source found in the meantime (it is a real data gap, not a pass).

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

- [ ] (consolidation-health) **Per-group manifest consolidation health**: this asset_group's consolidated
      `_index/availability_index.parquet` (resolve the bucket via `resolve_bucket_name(...)` — never hardcode `gs://`)
      is fresh (mtime advances ~per consolidator cycle) and its per-VM shards consolidate without OOM. Cross-ref the
      shared engine + 24h OOM/freshness recipe in `manifest_master_audit_instructions.md` (h2/h3) +
      `manifest_consolidator_duckdb_memory_fix_2026_05_26.md` (the DuckDB memory-bound merge is UTL Tier-0, shared by
      every asset_group).

## Canonical-form coverage (CF-1…CF-12)

> Cites the SSOT `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md`. Run CF-1…CF-12 against the
> `market-data-tick-tradfi-prd-…` `_index` + objects (DATA-STATE — the live `_index` reads **v8** despite the v9
> constant; CF-1 is RED until re-consolidated). Remediation owner = `tradfi_manifest_canonicalisation_2026_06_01.md`
> (absorbs `tradfi_massive` -031). CF-4 (`source` column = databento/massive/yahoo/barchart) covered by the Dual-source
> provenance section above.

- [ ] (CF-1/2/3/8/9/12) SSOT checks on `market-data-tick-tradfi-prd-…`: schema_version=v9 (data-state — currently v8) ·
      `asset_group=` not `category=` · `pipeline_mode=` partition (`batch_databento`/`batch_massive`) · honest
      `available_at` · env-split bucket · batch=live. GREEN = all data-state.
- [ ] (CF-5 tradfi reasons) every empty tradfi cell typed: `EXPECTED_KNOWN_SOURCE_GAP` / genuine `SOURCE_RETURNED_ZERO`;
      0 blank.
- [ ] (CF-7 tradfi names) underscore data_type
      (`trades`/`tbbo`/`ohlcv_1m`/`ohlcv_15m`/`options_chain`/`futures_chain`) + canonical ticker/exchange-symbol
      `venue`.

## Success Criteria

- All scaffold checklist items (a)–(g) GREEN (adapters scaffold present even if credentials are BLOCKED-CREDENTIALS)
- All dual-source provenance items (h)–(n) GREEN against ACTUAL prod data-state (not constants); (o) GREEN or explicitly
  `BLOCKED-CREDENTIALS` with a live ping
- Every prod TradFi parquet + manifest row carries a non-blank `source` from the closed set (item h/i) — zero blank
- A 2-source fixture proves the consumer resolves to exactly one row per (instrument, ts) via SOURCE_PRIORITY, with no
  silent double-count and divergences surfaced (items l/m)
- Unit tests against mocks pass; integration tests skip by default
- QG exits 0 for MTDS (TradFi adapter files) — including STEP 5.64 (TradFi `source` kwarg enforcement)
- e2e batch audit produces signals for ≥1 MVP archetype using mock upstream data (CLOUD_MOCK_MODE=true green)
- Paper trading goal post: ≥1 archetype runs ≥7 continuous paper days without silent failures

## Output Format

Result file at `plans/audit/results/tradfi_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
