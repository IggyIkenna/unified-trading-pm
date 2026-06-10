---
name: manifest_master_audit_instructions
type: audit-instructions
epic: manifest_master
assigned_vm: vm-defi
tier: L1
last_updated: 2026-06-01
---

# Manifest Master — Audit Instructions

> **🔄 ALIGNED 2026-06-08 — pre-apply readiness audit + source-aware/Era-B model (SSOT wins where this differs).** The
> v9 manifest now carries source-aware `pipeline_mode={mode}_{source}[_{transport}]` (path key + column), `source` +
> `transport` columns, the 4-state with `expected_unattempted` seeded from the IS×UAC could-exist universe, and Era-B
> instrument_type/data_type. SSOT = `canonical_form_cross_service_audit_checklist.md` (**CF-1…CF-14**, incl. **CF-13**
> source-aware + **CF-14** catalogue root) + the **①–⑫ pre-apply readiness audit** in
> `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`. Any text below assuming coarse
> `pipeline_mode=batch`/blank or a non-source-aware `_index` is STALE — audit against the SSOT.

## Epic Scope

Manifest **v9** schema (`MANIFEST_SCHEMA_VERSION = 9` — v9 added the tradfi `source` column), 4-state `capture_status`
(`captured`/`empty_confirmed`/`attempted_failed`/`expected_unattempted`), honest absence (the `EmptyConfirmedReason`
closed set in UAC — **32 members** as of 2026-06-01: 28 `EXPECTED_*` + `SOURCE_RETURNED_ZERO` + `NO_INPUT_AVAILABLE` +
`LEG_ABSENT_LEFT` + `LEG_ABSENT_RIGHT`; always read the enum, never trust this count), cluster validation at
`record_captured()`, `available_at` semantics, single-walk discipline, and the manifest consolidator (Cloud Run + Cloud
Scheduler).

Codex SSOTs: `codex/02-data/availability-manifest-and-data-status.md`,
`codex/02-data/honest-absence-downstream-handling.md`, `codex/05-infrastructure/manifest-consolidator-ssot.md`

## Triggers

- Weekly (minimum cadence)
- After every writegate phase change
- When A3 manifest divergence scan shows RED (any `DIVERGENT_EMPTY` or `MISSING_EXPECTED`)
- After any new `EmptyConfirmedReason` is added to UAC
- After manifest consolidator infrastructure changes (Cloud Run revision, Cloud Scheduler config)
- **Per-service `capture_status` write-path calibration (run as each producer service matures / BEFORE it backfills at
  scale)** — see the dedicated section below. Re-run on any producer when its emission paths change. Auditing the _code_
  before the corpus fills means the backfill writes correct statuses; auditing after means reconciling a manifest with
  baked-in wrong statuses.

## Checklist

- [ ] (a) **Schema version in actual PROD data**: read actual `schema_version` column from prod manifest (not code
      constant). Must be ≥ 95% at **v9** (`MANIFEST_SCHEMA_VERSION = 9`) across all asset_groups. Do NOT trust the
      constant — read the data. Run: `python3 plans/audit/results/a4_manifest_v9_compliance.py` or equivalent query

- [ ] (b) **All EmptyConfirmedReason values present**: the full closed set exists in UAC (32 members as of 2026-06-01 —
      28 `EXPECTED_*` + `SOURCE_RETURNED_ZERO` + `NO_INPUT_AVAILABLE` + `LEG_ABSENT_LEFT` + `LEG_ABSENT_RIGHT`; **count
      the enum, don't trust this number**). Read:
      `unified_api_contracts.canonical.crosscutting.honest_coverage.EmptyConfirmedReason` — count members

- [ ] (c) **No blank reason strings**: no `record_empty(reason="")` or `record_empty(reason=None)` anywhere. Grep:
      `rg 'record_empty\(reason=""' --include="*.py"` — must be 0 hits Grep:
      `rg 'record_empty\(reason=None' --include="*.py"` — must be 0 hits

- [ ] (d) **LegacyBlankErrorReasonError not suppressed**: no `except LegacyBlankErrorReasonError: pass` or equivalent.
      Grep: `rg "LegacyBlankErrorReasonError" --include="*.py"` — verify it is raised, not silently caught

- [ ] (e) **Cluster validation at record_captured() — QG STEP 5.64**: cluster\_\* kwargs present at every bundled
      `record_captured()` call. UTL raises `MissingClusterValidationError` if absent — verify this fires in tests. Run:
      QG STEP 5.64 passes for all services

- [ ] (f) **available_at is write-time per-row**: no service derives `available_at` at read time. Grep:
      `rg "available_at.*datetime.now\|available_at.*utcnow" --include="*.py"` — should be 0 hits at read paths Verify:
      UTL `record_captured` asserts presence internally

- [ ] (g) **Single-walk discipline**: no plan or code change proposes a new whole-corpus GCS walk without
      migration-window operator ack. Grep: `rg "walk.*gcs\|gcs.*walk" plans/active/ --include="*.md"` — review any hits
      for compliance

- [ ] (h) **Manifest consolidator runtime**: Cloud Run + Cloud Scheduler running (10 jobs, `*/1 * * * *`). Check:
      `gcloud run jobs list --region asia-northeast1` — verify consolidator jobs present Verify: legacy GCE VM launcher
      (`launch-manifest-consolidator-vm.sh`) does NOT exist. Grep:
      `rg "launch-manifest-consolidator-vm" --include="*.sh"` — should be 0 hits

- [ ] (i) **`source` column populated on EVERY cell — UNIVERSAL gate, all asset groups (codified 2026-06-01,
      operator)**: v9 added the `source` column but enforcement (`MissingSourceError`) fires ONLY for
      `category=="tradfi"` (`manifest_writer.py`). `source` is the SSOT for which provider produced a shard's rows.
      **Provenance is universal: every captured cell stamps its source NOW, even single-source ones** — operator
      2026-06-01: "I may find an alternative for Tardis, so it's the same issue." Stamping only at multi-source onset
      leaves the existing single-source corpus unlabelled and unresolvable after a swap. `source` is a **column, not a
      hive path key** (for batch=live symmetry). Generalise + verify: - **Gate is universal, not cardinality-gated**:
      raise `MissingSourceError` when `source` is **blank OR not a member of**
      `SOURCE_PRIORITY[(asset_group, data_type)]`, for **every** cell, all asset groups (cefi `tardis`, prediction
      `polymarket_clob`, etc. included). `SOURCE_PRIORITY` validates the allowed string + drives resolution when >1; it
      does NOT decide whether to stamp. A cell with no `SOURCE_PRIORITY` entry = a registry gap to fix, not a pass. NOT
      a hardcoded asset_group list. - **Column populated in actual PROD rows** (DATA-STATE, not the constant): read the
      `source` distribution per `(asset_group, venue, data_type)`; **zero blank `source` on ANY cell**. (manifest-v8
      lesson: constant ≠ data — 0% of 7.4M rows were v8 despite the bump.) - **Two rows per multi-source cell**: when >1
      source runs for one cell, the manifest holds TWO rows distinguished by `source`, each with its own
      `capture_status`. Union semantics downstream: cell is `captured` if ≥1 source row is `captured`;
      `attempted_failed` only when all source rows failed. - **Closed-set source strings** mirror `SOURCE_PRIORITY`; any
      blank/unknown source on any cell is RED. SSOT:
      `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`; consumer policy:
      `codex/02-data/honest-absence-downstream-handling.md` § multi-source; write-time gate: `mtds_mdps_master` item
      (j).

## CF-13 + CF-14 + Era-B — recurring regression checks (added 2026-06-08)

> The canonical set is now **CF-1…CF-14** (the section below still says CF-1…CF-12). CF-13 = source-aware pipeline_mode,
> CF-14 = IS-catalogue could-exist root. SSOT: `canonical_form_cross_service_audit_checklist.md`.

- [ ] (CF-13) **source-aware pipeline_mode is a PATH KEY, not coarse.** Every `_index` carries
      `pipeline_mode=batch_<source>` (not coarse `batch`/blank) in BOTH the object-path partition AND the column;
      `source_string_for(pm) == source`. Read the `pipeline_mode` distribution per AG `_index` → 0 coarse `batch`/blank.
- [ ] (CF-14) **could-exist denominator from the IS catalogue.** `expected_unattempted` is seeded from
      `build_instrument_catalogue` × UAC (genesis/launch/coverage), and the catalogue is a superset of the manifest
      present-set (no under-count → no falsely-high coverage). Verify the seed exists and the catalogue covers the
      present-set per AG.
- [ ] (erab) **Era-B in the `_index`:** no `data_type=options_chain`/`futures_chain` rows; chains carry
      `instrument_type=options_chain`/`futures_chain` plus `data_type=trades`.
- [ ] (transport) **`transport` column present** alongside `source` on every external cell.

## 4-state condition handling + pre-flight — recurring regression checks (added 2026-06-08)

> The FORM checks (CF-1…CF-14) guard the schema; THESE guard the BEHAVIOUR — that each of the four manifest conditions
> is WRITTEN to the right state and HANDLED correctly by every consumer. These regress silently (a consumer counts
> `expected_unattempted` as failed; a writer mislabels a timeout as `empty_confirmed`). Run weekly + on any
> writer/consumer change. Consumer policy SSOT: `codex/02-data/honest-absence-downstream-handling.md`.

WRITE-SIDE — the producer routes each absence shape to the right 4th-state + typed reason:

- [ ] (w-1) **captured** requires row-count > 0 OR an explicit `record_empty` — never a silent placeholder; cluster
      validation fires at `record_captured` for bundled data_types.
- [ ] (w-2) **empty_confirmed carries a TYPED, data-type-dependent reason**: zero-volume → `SOURCE_RETURNED_ZERO`;
      pre-genesis / pre-launch → `EXPECTED_PRE_*` (DeFi via `record_zero_rows`, venue-launch-date-aware);
      out-of-coverage → `EXPECTED_OUTSIDE_*`; no-input → `NO_INPUT_AVAILABLE`; sports fixture/season/transfer-window
      reasons; all-NaN / stale-last-price route to their typed reason, not a blank. Zero blank reasons
      (`LegacyBlankErrorReasonError` raised, never caught).
- [ ] (w-3) **attempted_failed is NEVER mislabeled empty_confirmed**: every external-I/O FETCH FAILURE
      (timeout/auth/RPC/DNS) routes to `record_failed` (`attempted_failed`), never swallowed (`except: return []`) into
      `empty_confirmed`. The per-adapter swallow audit (CF-11) is green across MTDS + IS.
- [ ] (w-4) **expected_unattempted is MATERIALISED by the writer/pre-flight, never re-derived**: the IS pre-flight +
      `enumerate_expected_universe` seed `expected_unattempted` at shard grain for IS-listed-but-not-yet-backfilled
      cells (the could-exist universe). Confirm it is WRITTEN to the manifest, not computed per-consumer.

PRE-FLIGHT — every service IS → MTDS → MDPS → features → strategy → execution:

- [ ] (pf-1) each service's pre-flight READS the manifest 4-state on its real buckets before running, and LOUD-FAILS on
      a stale/missing consolidated index (`ManifestConsolidatorStaleError`) instead of silently proceeding.
- [ ] (pf-2) the pre-flight decision (skip / run / honest-gap) is driven by the 4-state READ — NOT a per-service
      re-derivation of genesis/launch/IS rules.

READ-SIDE — every downstream consumer handles each of the four states per policy:

- [ ] (r-1) **denominator = captured + empty_confirmed + attempted_failed + expected_unattempted**; coverage % never
      counts `expected_unattempted` as "failed" nor drops it (deployment-api/UI G3 union + strategy/features
      pre-flight).
- [ ] (r-2) `empty_confirmed` = honest-absent (not a gap-to-backfill, not a failure); `attempted_failed` = a real
      failure to retry/alert; `expected_unattempted` = owed-backfill (instrument exists, data not yet run). Each
      consumer matches the per-service/per-reason policy in the honest-absence codex.
- [ ] (r-3) **multi-source UNION**: a cell is `captured` if ≥1 source row is captured; `attempted_failed` only when ALL
      source rows failed (`select_primary_available_source`).

## Canonical-form cross-service audit coverage (CF-1…CF-12) — manifest SSOT home

> **This epic is the cross-cutting HOME of the canonical-form checklist at the manifest layer.** The master list is the
> SSOT [`canonical_form_cross_service_audit_checklist.md`](./canonical_form_cross_service_audit_checklist.md) — it
> enumerates all 12 canonical data+manifest invariants (CF-1…CF-12) plus the (service × CF) ownership matrix. **Each
> per-service audit-instruction file owns its slice** of that matrix (see the SSOT's "Per-service audit ownership"
> table); the union of the per-service audits proves the whole pipeline is in canonical form. **A CF column with no
> owning service audit is a coverage gap and is review-blocking** — file the missing check in the most-relevant service
> audit before declaring the SSOT checklist green.
>
> **`manifest_master` owns the MANIFEST-LEVEL check** for CF-1, CF-2, CF-3, CF-4, CF-5, CF-6, CF-8, CF-9, CF-10, CF-11,
> CF-12 (per the SSOT matrix row `manifest_master (cross-cutting SSOT home)`). CF-7 (canonical venue / data_type names)
> lives with MTDS / instruments — see the one-line cross-ref below.
>
> **Audit method for every item below: read the DATA-STATE, never a code constant.** Walk the prod manifest `_index`
> across ALL asset_groups (`defi`/`cefi`/`tradfi`/`sports`/`prediction`) and read the actual column distributions. **The
> manifest-v8 lesson**: the `MANIFEST_SCHEMA_VERSION` constant said v8 while **0% of 7.4M prod rows** were v8 (and 1.3M
> rows carried a NULL schema_version). A bumped constant is NOT evidence — the row distribution is. Where an item below
> is already covered under a lettered checklist item above, it cross-references rather than duplicates.

- [ ] **(CF-1) schema_version = v9 in actual `_index` rows** — read the `schema_version` column distribution from the
      prod manifest `_index` per asset_group (NOT the `MANIFEST_SCHEMA_VERSION` constant); must be ≥95% at **v9** with
      zero NULL-schema-version rows across every asset_group. **Cross-ref**: same check as lettered item (a) — that is
      the concrete query (`a4_manifest_v9_compliance.py`); this CF row is its canonical-form alias. Green: v9 ≥95% every
      AG, 0 NULL, 0 rows < v9 outside a documented in-flight migration window.

- [ ] **(CF-2) `asset_group=` not `category=` — on BOTH paths and `_index` rows** — read the `_index` rows for any
      surviving `category` field/value and grep object paths for a `category=` hive segment; the canonical key is
      `asset_group=` (lowercase `cefi`/`defi`/`tradfi`/`sports`/`prediction`). Green: zero `category=` path segments,
      zero `category` field in any `_index` row, every row carries a canonical lowercase `asset_group`. (CODE side
      already emits `asset_group=` per archived `venue_axis_asset_group_vocabulary` — this audits the DATA-STATE that no
      legacy `category=` rows/paths survive.)

- [ ] **(CF-3) `pipeline_mode=` hive partition materialised** — confirm the `pipeline_mode=` partition SEGMENT exists on
      object paths (`pipeline_mode=batch*` / `pipeline_mode=live*`), not merely that a `pipeline_mode` column was added
      to the schema. List paths per asset_group and assert the segment is present on captured cells. Green: every
      captured cell's object path carries a `pipeline_mode=` segment; manifest `_index` reflects the same partition
      value. (Applies to mtds · mdps · instruments · features producers.)

- [ ] **(CF-4) `source` is a COLUMN (not a path key), populated on every external cell** — read the `source` column
      distribution per `(asset_group, venue, data_type)` in the `_index`; assert **zero blank `source` on any external
      cell**, every value a member of `SOURCE_PRIORITY[(asset_group, data_type)]`, and multi-source cells held as TWO
      rows distinguished by `source` (union semantics: cell `captured` if ≥1 source row `captured`). Confirm `source` is
      a manifest column, NOT a hive path segment (batch=live symmetry). **Cross-ref**: this is the manifest-level
      expression of lettered item (i) — the universal registry-driven gate (`MissingSourceError` when blank or not in
      `SOURCE_PRIORITY`, all asset_groups). Write-time gate lives in `mtds_mdps_master` item (j). Green: 0 blank
      `source` on any external cell, all asset_groups; computed/service outputs (features/strategy/execution) exempt.

- [ ] **(CF-5) typed `EmptyConfirmedReason` on every empty cell** — read the empty-reason histogram from the `_index`
      across all asset_groups; assert 0 blank / 0 untyped / 0 mislabeled `SOURCE_RETURNED_ZERO` (the AG-specific reason
      sets — defi `EXPECTED_PRE_GENESIS_CHAIN`, sports `EXPECTED_NO_FIXTURE`/`EXPECTED_PRE_SEASON`/…, cefi/tradfi/pred
      `EXPECTED_KNOWN_SOURCE_GAP` — are owned by the per-AG audits; this row is the cross-cutting manifest data-state
      check). **Cross-ref**: composes with lettered items (b) (enum closed-set present in UAC), (c) (no blank reason
      strings in code), (d) (`LegacyBlankErrorReasonError` not suppressed). Green: empty-reason histogram is 100% typed
      members of the UAC closed set, 0 blank, every AG.

- [ ] **(CF-6) `expected_unattempted` 4th state materialised in rows** — run a prod batch on post-Phase-1+2 code and
      confirm the writer/orchestrator pre-flight reads the IS manifest and **records owed cells** as
      `expected_unattempted` with `EXPECTED_OUTSIDE_PROCESSING_SCOPE` / `EXPECTED_UPSTREAM_EMPTY` — rather than a
      reflexive `empty_confirmed` (the owed-data lie). Read the `capture_status` distribution and confirm the 4th state
      is present and non-zero where cells are genuinely owed. **Cross-ref**: composes with the Per-Service write-path
      calibration's "Anti-pattern 1 — reflexive `empty_confirmed`" below (the code-side audit) — this CF row is its
      data-state counterpart. Green: owed cells appear as `expected_unattempted`, never `empty_confirmed`. (mtds · mdps
      · features downstream-propagate.)

- [ ] **(CF-7) canonical venue / data_type names** — **CROSS-REF ONLY**: owned by `mtds_mdps_master` +
      `instruments_master` (underscore data_type · flat `venue` + populated `chain` · `{VENUE}_V{N}`
      underscore-canonical, no hyphen / `VENUE-CHAIN` / glued `_V{N}` drift). The manifest carries whatever names the
      producers stamp — if those audits are RED, the manifest `_index` venue/data_type strings will be RED too; do NOT
      duplicate the check here.

- [ ] **(CF-8) `available_at` per-row write-time, honest** — read the `available_at` distribution vs the day boundary in
      the `_index`; assert no lookahead / migration-time / read-time derivation, and batch=live derivation parity (the
      top `SOURCE_PRIORITY` entry's live `available_at`). **Cross-ref**: same invariant as lettered item (f) (no
      read-time derivation in code; UTL `record_captured` asserts presence). This CF row reads the DATA-STATE
      distribution rather than grepping code. Green: every row's `available_at` ≥ its data's logical close and < a
      lookahead bound; batch and live derive identically.

- [ ] **(CF-9) env-split bucket `{kind}-{env}-{project}`** — confirm every manifest `_index` lives in an env-tiered
      canonical bucket (`-prd` / `-test`) resolved via `resolve_bucket_name()`; read which buckets actually hold
      `_index` objects per asset_group. **Cross-ref**: composes with QG STEP 5.69 (no inline `gs://` f-strings) and
      `manifest_master`'s consolidator-runtime item (h) (jobs read/write the env-tiered buckets). Green: every `_index`
      object resides in a canonical env-split bucket; zero non-canonical / flat-legacy buckets still being written.

- [ ] **(CF-10) no phantom / date-impossible `captured`** — captured-vs-objects walk per (chain/venue, date): assert no
      `captured` row that is pre-genesis / pre-venue-launch with no backing object, and every post-launch `captured` row
      is object-backed. **Cross-ref**: the existing phantom reconciler
      (`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --dry-run`) is the tooling; do NOT write
      empty parquets to mask phantoms (relabel honestly to `empty_confirmed`/`expected_unattempted`). Green: zero
      object-less `captured` rows; zero date-impossible captured rows across all asset_groups. (mtds · instruments.)

- [ ] **(CF-11) fetch-failure → `attempted_failed`, never `empty_confirmed`** — per-adapter trace from a swallow pattern
      (`except … return []` / `return {}`) to the `record_*` call; a fetch error must land as `attempted_failed` (+
      `stack_trace`), never a silent `empty_confirmed`. Read the `_index` for `attempted_failed` rows actually appearing
      on adapter-error branches (defi A7 precedent). **Cross-ref**: composes with the Per-Service write-path
      calibration's "Anti-pattern 2 — silent no-row skip" below. Green: no adapter error path resolves to
      `empty_confirmed`; error branches produce `attempted_failed` rows visible in the `_index`.

- [ ] **(CF-12) batch = live symmetry** — diff the batch vs live manifest schema + data_type set per asset_group from
      the actual `_index` rows; confirm identical schema / data_types / fields, `available_at` not derived at read-time,
      and no live-only data_types (one code path). **Cross-ref**: this is the manifest-data-state expression of the
      `### Batch vs Live Parity` section below (which audits the adapter invocation paths). Green: batch and live
      `_index` rows carry the identical schema + data_type set per AG; zero live-only data_types; zero `DIVERGENT_EMPTY`
      between modes.

### Canonical-form coverage CF-15…CF-21 — manifest_master owns CF-15 / CF-17 / CF-21 (added 2026-06-10)

> Concrete, re-runnable steady-state checks for the migration-verification / orphan-safety CF items added by
> `migration_verification_orphan_safety_2026_06_10.md` (V7). Written to audit a corpus that has ALREADY migrated to v9 —
> "assert the v9 corpus holds X", so a future regression (a new writer creating orphans, a hand-maintained `prefix_tpls`
> list drifting from the templates, a delete-without-twin) is caught by re-running this checklist. The full CF table is
> the SSOT (`canonical_form_cross_service_audit_checklist.md`) — these are the manifest-layer concrete checks, not a
> duplicate of that table. CF-16/CF-18/CF-19/CF-20 are owned by `instruments_master` / `mtds_mdps_master` /
> `deployment_and_user_management_master` (cross-ref only here).

- [ ] **(CF-15) possible-manifest registry is the single could-exist SSOT** — assert
      `unified_api_contracts/registry/possible_manifest.py` exists and is the ONLY import for could-exist enumeration:
      `python -c 'from unified_api_contracts import enumerate_possible_shard_keys, is_valid_shard_key, canonical_path_templates'`.
      Grep-verify the consumers derive from it with NO hand-maintained cross-product:
      `reconcile_phantom_manifest_rows_all.py` derives `prefix_tpls` from `canonical_path_templates(asset_group)` (no
      literal prefix list); `enumerate_expected_universe.py` reads the registry's validity matrix; the deployment-api
      denominator reads `get_chain_genesis_date` / `get_protocol_launch_date` from UAC (no bespoke genesis/launch
      cross-product). Green: module is the single import, `rg "prefix_tpls\s*=\s*\["` / bespoke cross-products return 0
      hits across instruments-service · mtds · mdps · deployment-api.

- [ ] **(CF-17) bidirectional manifest ≡ GCS + bucket prefix taxonomy + sizing** — per asset*group run the orphan sweep
      `migration_orphan_sweep.py --asset-group <ag>` (GCS→manifest) AND the phantom reconciler
      `reconcile_phantom_manifest_rows_all.py --asset-group <ag> --dry-run` (manifest→GCS); assert `orphan_class_E==0`
      (real data with no manifest row) AND `phantom_count==0`. Assert the bucket prefix taxonomy reports **0 `unknown`
      prefixes** (every top-level prefix labelled {service-data, manifest-infra, logs, run-artifact, terraform,
      tarball}); assert the sizing rollup parquet
      `\_index/audit/data_sizing*<ag>.parquet`was produced (bytes + object-count per    `(asset_group, data_type, venue,
      pipeline_mode)`). **Class (E) → `record_captured`backfill, NEVER delete** (it is     the "v10 hole"); non-data paths (VM logs, terraform, tarballs) are understood + NEVER deleted. Green: both counts     0, 0`unknown`
      prefixes, sizing published, every AG.

- [ ] **(CF-21) verified-delete safety for legacy/duplicate objects** — dry-run the legacy-twin cleanup
      `cleanup_legacy_twins_<ag>.py --asset-group <ag> --dry-run`; assert EVERY delete candidate passes the gate: its
      canonical twin is in the manifest as `captured` AND `crc32c(legacy)==crc32c(canonical)`. Assert 0 deletes of class
      (C) manifest-infra / (C2) non-data / (E) orphan-real-data (never delete the only copy of real data). After a
      `--apply`, re-run the CF-17 orphan sweep and assert `orphan_class_E==0` still holds. Green: 0 candidates fail the
      in-manifest + crc32c-identity gate; 0 class-(C)/(C2)/(E) deletes; orphan-E still 0 post-apply.

### Batch vs Live Parity

- (batch-live) **Batch adapter output**: confirm each adapter in scope produces manifest rows with
  `capture_status=captured` for a known date range using the batch invocation path (`--mode batch`). Run against mock
  data if real upstream is unavailable (`CLOUD_MOCK_MODE=true`).
- (live-adapter) **Live adapter parity**: for each batch adapter, confirm the live adapter exists, accepts the same
  schema, and emits `available_at` at write-time (not read-time). Confirm no `DIVERGENT_EMPTY` rows for live mode.
- (mock-upstream) **Mock upstream pattern**: audits for this data layer MUST be runnable without hitting real APIs.
  Document fixture paths and `CLOUD_MOCK_MODE=true` invocations so downstream services can be audited independently.

### Per-Service `capture_status` Write-Path Calibration (run per-service, as each matures)

**Purpose**: this is a CODE write-path audit, not a manifest data-search — so it is valid regardless of how much data is
backfilled. Run it per producer service so the code writes the rule-correct status BEFORE that service backfills at
scale (a status-writing bug, left unfixed, bakes wrong statuses across millions of rows; fixing the code first makes the
ongoing/remaining backfill correct as it fills). Re-runnable any time a service's emission paths change.

**Producer services in scope** (audit each as it is run / matures): instruments-service · market-tick-data-service
(MTDS) · market-data-processing-service (MDPS) · features-service (delta_one / volatility / cross_instrument /
multi_timeframe / onchain / calendar / sports) · any other service that calls `record_captured` / `record_empty` /
`record_failed` / `record_empty_for_shard`.

> Maturity note (2026-06-01): the 3 upstream data services (IS / MTDS / MDPS) are mostly calibrated — **re-check** them.
> Downstream + less-exercised services are audited **as they are run**, before each backfills at scale.

**The decision rule (encode per write-path):**

| Real situation                                                                | Correct status                                                        | Notes                                                          |
| ----------------------------------------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------- |
| Data genuinely absent (holiday, no source coverage, contract not listed)      | `empty_confirmed` + typed `EmptyConfirmedReason`                      | **LAST resort** — only after all other possibilities ruled out |
| Upstream produced nothing but SHOULD have (not downloaded yet, dep not ready) | NOT `empty_confirmed` → dependency-gate skip / `expected_unattempted` | data is **owed**: retry / backfill, never confirm-empty        |
| Attempted and errored (fetch / backfill error)                                | `attempted_failed` (+ `stack_trace`)                                  | transient/real failure, not an absence                         |
| Wrote rows                                                                    | `captured`                                                            | normal                                                         |

**Per-service procedure:**

- [ ] **Enumerate every emission path** in the service — every `record_captured` / `record_empty` / `record_failed` /
      `record_empty_for_shard` call AND every code path that returns without writing any manifest row. Grep:
      `rg "record_(captured|empty|failed|empty_for_shard)" <service>/ --include="*.py"`.
- [ ] **Anti-pattern 1 — reflexive `empty_confirmed`**: for each `record_empty` callsite, confirm the code has _ruled
      out_ "data owed" first (dependency present? source actually returned zero vs not-yet-downloaded?). A
      `record_empty` reached on a missing-upstream / not-backfilled branch is a **silent correctness lie** → must be a
      dependency-gap skip / `attempted_failed` instead.
- [ ] **Anti-pattern 2 — silent no-row skip**: any in-scope shard that can `return` / `continue` without writing a
      manifest row is indistinguishable from a crash → must write a typed status (no silent skips).
- [ ] **Spot+future corollary**: a future cannot exist without a spot for its underlying. For paired features
      (`futures_basis` etc.), "future present, spot absent" is a contradiction (bug); the only legitimate absence is
      "spot present, future absent" (future not listed for that underlying in that window → `empty_confirmed`, typed).
- [ ] **Typed reason check**: every `empty_confirmed` carries a real `EmptyConfirmedReason` (never blank — composes with
      checklist (c)/(d) above).
- [ ] **Wire a QG guard where feasible**: a silent no-row for an in-scope shard should fail QG for that service.
- [ ] **Record findings** per producer in the result file; fix the real bugs in the owning service repo before/while it
      backfills.

Known live instances (genesis of this audit, 2026-05-27): delta_one 4h/24h missing-1h-dependency (now correctly
fast-fails — textbook "data owed" ≠ empty); volatility `futures_basis` silent-skip when future leg absent (features now
emits `empty_confirmed(SOURCE_RETURNED_ZERO)` on no-input — verify the listed-vs-not-downloaded distinction). Genesis:
operator-raised 2026-05-27; principle + instances folded inline above (this section is the everlasting home).

## Success Criteria

- All checklist items (a)–(i) GREEN
- `source` column populated (closed-set, zero blank) on every multi-source cell in actual prod rows; registry-driven
  gate enforced across all asset groups (item i)
- Per-service `capture_status` write-path calibration GREEN for every producer that has been run/matured (no reflexive
  `empty_confirmed` on owed-data branches, no silent no-row skips)
- A3 manifest divergence: zero `DIVERGENT_EMPTY` + zero `MISSING_EXPECTED` across all asset_groups
- QG exits 0 for all services (cluster validation step passes everywhere)

## Output Format

Result file at `plans/audit/results/manifest_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date       | Result file                                                                                                         | Status                                                                                                                         |
| ---------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 2026-06-01 | [manifest_master_capture_status_audit_2026_06_01.md](../results/manifest_master_capture_status_audit_2026_06_01.md) | per-service write-path: 23 raw → **18 confirmed** (adversarially verified; 5 false-positives) — P0:3 P1:9 P2:6 — fixes pending |
