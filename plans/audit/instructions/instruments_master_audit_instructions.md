---
name: instruments_master_audit_instructions
type: audit-instructions
epic: instruments_master
assigned_vm: vm-cefi
tier: L1
last_updated: 2026-05-22
---

# Instruments Master — Audit Instructions

> **🔄 ALIGNED 2026-06-08 — pre-apply readiness audit + source-aware/Era-B model + IS-catalogue could-exist ROOT.** IS
> is the foundation of ⑥/⑦/⑧: the `(instrument_type × data_type)` validity matrix + bundle-grain guard impossible cells,
> and `build_instrument_catalogue` + `enumerate_expected_universe` define the could-exist denominator (⊇ manifest
> present-set). The instruments-store `_index` migrates to v9 via `migrate_instruments_store_v9.py` (source-aware
> `pipeline_mode={mode}_{source}[_{transport}]`, Era-B instrument_types). SSOT =
> `canonical_form_cross_service_audit_checklist.md` (**CF-1…CF-14**, esp. **CF-14**) + the **①–⑫ pre-apply readiness
> audit** in `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` (esp. ⑥
> validity/bundle-grain, ⑧ catalogue completeness). Any text below assuming coarse `pipeline_mode=batch`,
> `options_chain`-as-data_type, or a non-catalogue denominator is STALE — audit against the SSOT.

## Epic Scope

instruments-service as the reference data SSOT: venue URL ownership, instrument universe management, `InstrumentRecord`
schema, and the IS→MTDS contract enforced by QG STEP 5.70 (three scripts). MTDS handlers derive all venue URLs and
universes from IS — never hardcoded.

Codex SSOT: `codex/04-architecture/instruments-service-as-ssot-for-mtds.md`

## Triggers

- Weekly (minimum cadence)
- When a new venue is added to MTDS (IS must be updated first)
- After any `InstrumentRecord` schema change in UAC
- When `reconcile_phantom_manifest_rows_all.py` shows phantom rows for any asset_group

## Checklist

- [ ] (a) **QG STEP 5.70 — no_silent_absence_handlers.sh**: passes for all MTDS handler files. Run:
      `bash scripts/quality-gates/no_silent_absence_handlers.sh`

- [ ] (b) **QG STEP 5.70 — no_hardcoded_venue_urls.sh**: passes for all MTDS handler files. Run:
      `bash scripts/quality-gates/no_hardcoded_venue_urls.sh`

- [ ] (c) **QG STEP 5.70 — no_hardcoded_venue_universe.sh**: passes for all MTDS handler files. Run:
      `bash scripts/quality-gates/no_hardcoded_venue_universe.sh`

- [ ] (d) **InstrumentRecord coverage**: IS universe covers all active venues in the trading system. Check:
      `instruments-service` universe manifest vs MTDS handler list — no gaps Grep:
      `rg "venue" instruments-service/instruments_service/ --include="*.py" -l`

- [ ] (e) **MTDS handlers derive URLs from IS**: no MTDS handler file constructs a venue URL directly. Grep:
      `rg "http[s]?://" market-tick-data-service/ --include="*.py"` — should be 0 hits in handler business logic (test
      fixtures and config schema excluded)

- [ ] (f) **Zero phantom manifest rows**: `reconcile_phantom_manifest_rows_all.py` returns zero phantoms. Run:
      `python3 instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run` Run:
      `python3 instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run`

- [ ] (g) **No URDI references**: `URDI` (phantom name) does not appear anywhere in the codebase. Grep:
      `rg "URDI" --include="*.py"` — should be 0 hits

- [ ] (h) **Fetch-failure → `attempted_failed`, never `empty_confirmed` — PER-ADAPTER swallow audit (codified
      2026-06-01)**: every instruments-service reference-data adapter doing external I/O (vendor REST/SDK, RPC,
      subgraph) must route a fetch error to `record_failed` (`attempted_failed`), NOT swallow it
      (`except: … return     []/None`) into a `record_empty` (`empty_confirmed`) — a swallowed timeout/auth/RPC error
      mislabeled as honest-empty pollutes the IS manifest, which then propagates wrong `expected_unattempted`/skip
      decisions downstream (MTDS reads the IS manifest). Grep:
      `rg -U "except\b[^\n]*:\s*\n(\s*[^\n]*\n)?\s*return (\[\]|None|\{\}|pd\.DataFrame\(\))" instruments-service/ --include="*.py" -g '!*test*'`
      then read each adapter's outer fetch try/except. **Closed per-adapter checklist — check EVERY adapter.** Full
      spec: `defi_master_audit_instructions.md` item (aa).

### Batch vs Live Parity

- (batch-live) **Batch adapter output**: confirm each adapter in scope produces manifest rows with
  `capture_status=captured` for a known date range using the batch invocation path (`--mode batch`). Run against mock
  data if real upstream is unavailable (`CLOUD_MOCK_MODE=true`).
- (live-adapter) **Live adapter parity**: for each batch adapter, confirm the live adapter exists, accepts the same
  schema, and emits `available_at` at write-time (not read-time). Confirm no `DIVERGENT_EMPTY` rows for live mode.
- (mock-upstream) **Mock upstream pattern**: audits for this data layer MUST be runnable without hitting real APIs.
  Document fixture paths and `CLOUD_MOCK_MODE=true` invocations so downstream services can be audited independently.

## Canonical-form cross-service audit coverage (CF-1…CF-12)

SSOT: `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` (the 12 canonical data+manifest
invariants the 2026-06-01 canonicalisation programme enforces). Per the ownership matrix in that SSOT,
**`instruments_master` OWNS the live check for ALL of CF-1…CF-12** — instruments-service is the I/O input service
(reference data, `InstrumentRecord`, fixtures, the `instruments-store-{ag}` data buckets + reference `_index`), so its
manifest+data are the canonical-form root that MTDS/MDPS/features/strategy/execution propagate from. Read DATA-STATE
(distribution reads from prod `_index` + sampled parquets), **never trust a code constant** (the manifest-v8 lesson: a
constant said v8 while 0% of 7.4M rows were v8).

- [ ] (CF-1) **schema_version = v9 in ACTUAL rows**: read the `schema_version` distribution from every
      `instruments-store-{ag}` (defi/cefi/tradfi/sports/prediction) `_index` + a sample of reference parquets. GREEN =
      100% of live rows are `v9` (no v4–v8 / NULL-schema-version stragglers). Do NOT read `MANIFEST_SCHEMA_VERSION` —
      read the column distribution per bucket.

- [ ] (CF-2) **`asset_group=` not `category=`** on BOTH object paths AND manifest rows: path-list the
      `instruments-store-{ag}` object keys for any `category=` hive segment; read the `_index` rows for a `category`
      field. GREEN = zero `category=` path segments + zero `category` columns across all 5 AG stores; the canonical
      `asset_group=` hive key + column is present on every object + row.

- [ ] (CF-3) **`pipeline_mode=` hive PARTITION on object paths** (not just a column): path-list the
      `instruments-store-{ag}` keys for a `pipeline_mode=batch*` / `pipeline_mode=live*` partition segment. GREEN = the
      partition segment exists in the object path on every reference object (column-only presence is RED — CF-3 demands
      the path partition).

- [ ] (CF-4) **`source` COLUMN on every external cell** (column, NOT a path key — co-mingled, same read path): read the
      `source` column distribution in each `instruments-store-{ag}` `_index`; assert zero blank `source` on every
      external reference cell. **Sports FIXTURES is the multi-source case → 2 rows** (one per source, e.g. footystats +
      the-odds-api), union semantics downstream; `source` is a COLUMN not a path segment. GREEN = every external cell
      carries a non-blank `source` column value, multi-source fixtures materialise as separate rows, and `source` never
      appears as a hive path key. (Pure computed/derived reference outputs are exempt per the SSOT — but instruments
      rows are predominantly external ingest, so expect near-total coverage.)

- [ ] (CF-5) **Typed `EmptyConfirmedReason` on every empty cell** (no blank / mislabeled `SOURCE_RETURNED_ZERO`): read
      the empty-reason histogram per `instruments-store-{ag}` `_index`; assert 0 blank/untyped reasons (a blank raises
      `LegacyBlankErrorReasonError` at write — verify the data-state too). For the **sports** reference store the typed
      reasons are the schedule-driven set — `EXPECTED_NO_FIXTURE` / `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON` /
      `EXPECTED_OUTSIDE_TRANSFER_WINDOW` (fixture / season / transfer-window) etc. (oracle:
      `clip_dates_to_source_coverage()` / `is_in_known_gap()`). GREEN = 0 blank reasons + reasons drawn from the closed
      `EmptyConfirmedReason` set. **Note**: the sports-specific RELABEL of mislabeled empties is owned by the sports
      plan (`sports_manifest_canonicalisation_2026_06_01`) — instruments asserts the IS-reference empties are typed; the
      MTDS/MDPS sports tick relabel is cross-referenced there, not duplicated here.

- [ ] (CF-6) **`expected_unattempted` 4th state materialised**: instruments-service is the manifest the downstream
      writer/orchestrator pre-flight READS to compute owed cells, so its own owed cells must materialise too. Run a prod
      batch on post-Phase-1+2 code; confirm owed reference rows generate with `EXPECTED_OUTSIDE_PROCESSING_SCOPE` /
      `EXPECTED_UPSTREAM_EMPTY`. GREEN = the 4th `capture_status` state is present in the `_index` (not just the 3 of
      captured/empty_confirmed/attempted_failed).

- [ ] (CF-7) **Canonical names**: underscore `data_type` · flat `venue` + populated `chain` · `{VENUE}_V{N}`
      underscore-canonical; no hyphen / `VENUE-CHAIN` / glued `_V{N}` drift. Grep instruments-service handler
      `data_type=` / `_DATA_TYPE` literals AND read the corpus venue/data_type strings from the `_index`. GREEN = no
      hyphenated data_types, no `VENUE-CHAIN` glued venue strings, `chain` populated where applicable, version suffixes
      are `{VENUE}_V{N}` canonical. (Cross-ref: this is the reference-side companion of the MTDS market-side CF-7 in
      `mtds_mdps_master`.)

- [ ] (CF-8) **`available_at` per-row, preserve-or-honest-derive; never lookahead / migration-time / read-time**: read
      `available_at` vs the day boundary on a sample of `instruments-store-{ag}` rows; assert batch=live derivation
      parity (the top `SOURCE_PRIORITY` entry's live `available_at`). GREEN = every row carries a per-row write-time
      `available_at`, none is at midnight-migration-time or read-time, and batch/live derive it identically.
      **Cross-reference**: the Batch vs Live Parity `(live-adapter)` item above already asserts write-time
      `available_at` for the live adapter — CF-8 extends it to a data-state distribution read across all AG stores.

- [ ] (CF-9) **env-split bucket `{kind}-{env}-{project}`** via `resolve_bucket_name()`: confirm every
      `instruments-store-{ag}` lookup resolves through
      `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)` and is env-tiered
      (`-prd`/`-test`). Grep instruments-service for inline `gs://` f-strings (QG STEP 5.69 ratchet). GREEN = 0 inline
      `gs://` builds + every bucket is env-split canonical.

- [ ] (CF-10) **No phantom / date-impossible `captured`** (object-backed): captured-vs-objects walk per (chain/venue,
      date) on each `instruments-store-{ag}` — every `captured` row must have a backing reference object; no pre-genesis
      / pre-venue-launch `captured` with no object. This is the data-state companion of item (f)
      (`reconcile_phantom_manifest_rows_all.py`) — CF-10 GREEN = item (f) returns zero phantoms across ALL 5 AGs (not
      just cefi+defi) AND every `captured` row is object-backed. Relabel any object-less `captured` row honestly.
      **Cross-reference**: item (f) above.

- [ ] (CF-11) **fetch-failure → `attempted_failed`, never `empty_confirmed`** (no `except: return []` swallow): this is
      already covered in full by item **(h)** above — the per-adapter swallow audit. CF-11 GREEN = item (h) GREEN for
      every instruments-service reference-data adapter. **Cross-reference**: item (h) (do NOT duplicate — run (h)).

- [ ] (CF-12) **batch = live symmetry**: diff the batch-vs-live schema + `data_type` set per AG for instruments-service;
      confirm one code path, identical fields, no live-only reference data_types, `available_at` not derived at
      read-time. GREEN = batch and live emit identical schema/data_types per AG. **Cross-reference**: composes with the
      Batch vs Live Parity subsection above (`(batch-live)` / `(live-adapter)`) — CF-12 is the schema/data_type-set
      equality assertion across the whole reference corpus, those items are the per-adapter parity checks.

## CF-13/CF-14 + validity-matrix + catalogue — recurring regression checks (added 2026-06-08; instruments is the could-exist ROOT)

> instruments-service now also owns **CF-13** (source-aware pipeline_mode) + **CF-14** (IS-catalogue could-exist root).
> SSOT: `canonical_form_cross_service_audit_checklist.md`.

- [ ] (CF-13) instruments-store `_index` carries source-aware `pipeline_mode=batch_<source>` (path + column) post
      `migrate_instruments_store_v9`; 0 coarse `batch`/blank.
- [ ] (CF-14) **`build_instrument_catalogue` is a superset of the manifest present-set** per AG (no missing
      instruments/leagues → honest denominator); the daily catalogue scheduler is wired for EVERY AG (not just cefi).
- [ ] (validity) the UAC `(instrument_type × data_type)` validity matrix REJECTS impossible cells (e.g. PERPETUAL ×
      options_chain, pre-genesis); `enumerate_expected_universe` emits NO impossible or over-fanned cell.
- [ ] (bundle-grain) options_chain/futures_chain enumerate ONE candidate per UNDERLYING (instrument_type +
      `data_type=trades`), NOT per-leaf OPTION/COMBO; sports = league-grain; prediction = per-cqg. Re-run the enumerate
      dry-run; confirm the candidate count is plausible (no single-venue domination).
- [ ] (expected) instrument-exists-but-data-not-backfilled → `expected_unattempted` (via `was_instrument_alive` +
      genesis/launch), never silently absent.

## Success Criteria

- All 7 checklist items GREEN (especially QG STEP 5.70 triple-pass)
- Zero phantom manifest rows for cefi + defi asset groups
- QG exits 0 for instruments-service and market-tick-data-service

## Output Format

Result file at `plans/audit/results/instruments_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
