---
doc_type: plan
title: market-tick-data-service to 100% honest coverage across all 5 asset groups
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-05
priority: P0
owner: harsh
type: deployment
epic: data-pipeline-completion
completion_gates: { code: none, deployment: D2, business: none }
repo_gates:
  - { repo: market-tick-data-service, deployment: D2 }
depends_on: [instruments_to_100pct_eod_2026_05_04, instruments_and_market_tick_data_completion_2026_05_01]
isProject: false
---

## Deferred work — migrated to: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`,

`plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md`,
`plans/active/sports_master_closeout_2026_07_21.md` — successor: data_completion_to_100_all_ag_2026_06_21,
instruments_mtds_subset_consistency_remediation_2026_06_17, sports_master_closeout_2026_07_21 (all 90 open items — the
largest plan in this batch — resolve to HAS_SUCCESSOR, predominantly the umbrella
`data_completion_to_100_all_ag_2026_06_21.md`, or STALE_OBSOLETE (dead superseded-in-text UTL work, self-referential
tracking checklists, one-time diagnostic gates from 2026-05). The SPORTS per-AG launch cluster is additionally moot on
substance — it predates the operator-ruled 2020-06-06 sports data floor. No genuinely orphaned items found.)

## Final session summary (2026-05-05 — comprehensive audit complete)

**Total commits this session**: 14 to MTDS scripts + 30+ to plan doc.

**Audit script work shipped**:

- `reconcile_market_tick_manifest.py` — patches FIX-1, FIX-2, FIX-3, FIX-4, FIX-7, FIX-8, FIX-11, FIX-12. 6 path-shape
  variants + per-day prefix listing + case-insensitive comparison + DeFi venue-key normaliser
  - chain= optional in canonical + axis-4 both forms.
- `audit_legacy_paths.py` — created from scratch with FIX-9, FIX-10, FIX-12, FIX-axis-6, FIX-axis-11. 6 axis patterns
  (4, 6, 8, 9, 10, 11) + raw_tick_data/ prefix scope.
- `audit_structural_checks.py` — created from scratch. 6 cross-cutting checks (schema_version, written_at chronology,
  bucket drift, per-VM staleness, schema parity stub, empty/failed accuracy).

**Total findings**: 30 distinct (F1-F30 + F2-CEFI + F3-disambiguation + F11-detail + F30a/b).

**Closed as benign / handled by FIX-6 rebuild / closed as recon-bug-not-data**: F3, F6, F11, F11-detail, F13, F14, F18,
F19, F20 (recon-side fix), F21.

**Open / needs action**:

- 9 Q&A items for Ikenna (top of doc).
- F1, F2, F2-CEFI, F7 — schema-v4 residue (FIX-6 rebuild closes).
- F4, F5 — stale test buckets retire.
- F10, F12 — leaked-text rows (rebuild overwrites).
- F15 — sports recon support (FIX-2 LANDED).
- F16, F17, F22, F23, F24, F25, F28 — disk-layout drift. **Migration scripts already exist** (Q&A 10).
- F8, F8', F9 — per-VM shard backlog (consolidator throughput, not blocking).
- F26 — PREDICTION coverage_start mismatch.
- F27 — sports pre-coverage-start phantoms.
- F29 — UTL rebuild*manifest_from_canonical_paths skips \_migrated*\* files.
- F30 — prediction second layout + blank-venue phantoms.

**Per-AG audit results** (DRY-RUN, no production manifest writes):

| AG         | Manifest rows | Matched |       Forward Phantoms | Missing Rows |     True Gap Days |
| ---------- | ------------: | ------: | ---------------------: | -----------: | ----------------: |
| PREDICTION |        14,369 |   2,804 |                    420 |           26 | 1,752/2,154 (81%) |
| SPORTS     |        17,288 |   3,649 |                    603 |            0 |   37/2,165 (1.7%) |
| DEFI       |       313,365 |  21,487 |                   0 ✅ |          278 |       1,295/2,317 |
| CEFI       |     2,229,282 | 105,723 | 14,131 (mostly v4 mix) |          452 |   89/2,682 (3.3%) |
| TRADFI     |        73,316 |  21,424 |                  5,562 |        1,735 | 368/2,682 (13.7%) |

**Critical insight**: Most "missing" coverage is reader blindness, not real data gaps. Disk migration scripts
(`migrate_*_canonical.py`) already exist in MTDS — running them collapses F16/F17/F22/F23/F24/F25 and reduces phantoms
to near-zero.

## Session summary (2026-05-05 — TL;DR for when Harsh is back)

**14 commits to MTDS scripts** + **15+ commits to plan doc** + **28 distinct findings** captured. No backfill VMs
launched. No production manifest writes. Full audit-tooling pass — recon + legacy-paths now correctly handle the layout
zoo across all 5 asset groups.

### Big-picture outcome

Confirmed Ikenna's 2026-05-05 hypothesis at scale: **most "missing" coverage on the data-status UI is reader blindness,
not real data gaps**. Audit found:

- 6+ distinct on-disk path shapes coexisting across the 5 buckets (canonical, hive vocab variants, DeFi venue-overload,
  prediction 10-segment, 4 sports layouts, TRADFI dash one-off).
- Schema-v4 manifest residue causing reader misclassification (sports 100% v4, prediction 99.5% v4, tradfi 23% v4).
- Per-AG-specific quirks (F19 case mismatch, F20 venue-key mismatch, F26 coverage_start mismatch).

The audit-tooling (recon + legacy-paths) is now the system-of-record for actual coverage. **Before any backfill VM
launches, that tooling is the truth.**

### Audit scripts hardened

- `scripts/reconcile_market_tick_manifest.py` — 6 path-shape variants + per-day prefix listing (~100x speedup)
  - sports/defi case-insensitive normaliser + DeFi venue-key collapse + chain= optional in canonical.
- `scripts/audit_legacy_paths.py` — 6 axis patterns + raw_tick_data/ prefix scope + companion CSV findings.
- `scripts/audit_structural_checks.py` — 6 cross-cutting checks (schema-version, written_at chronology, bucket drift,
  per-VM staleness, schema parity stub, empty-vs-failed accuracy).

### Open decisions for Harsh

See **Questions for Harsh** section above (9 items). Most consequential:

- **FIX-5 design**: disk migration vs reader-side multi-layout vs canonical+suffix (Q&A 1).
- **FIX-6 design**: rebuild scope, error_reason preservation (Q&A 2 + design section).
- **F26 PREDICTION coverage_start mismatch**: UAC says 2020-06-12, disk has 2025-03-14+ (Q&A 9).
- **F25 TRADFI 100k non-hive blobs**: migrate or archive (Q&A 7).

### Next moves (queued, not started — pending design calls)

1. Wait for full-range recons to finish (in flight; ETA <30 min). Per-AG match/phantom/missing/gap numbers go into the
   per-AG result table.
2. After Q&A: implement FIX-5 decision (likely Option B reader-side multi-layout).
3. After Q&A: implement FIX-6 manifest rebuild — order PREDICTION → SPORTS → DEFI → TRADFI → CEFI, with regex-based
   rebuild_mtds_manifest.py rewrite per FIX-6 design section.
4. Re-run audits to confirm <1% phantom + <1% missing-row across all AGs.
5. Only THEN evaluate genuine remaining gaps and launch any paid backfills.

## Decisions log (Q&A queue — all 10 items RESOLVED 2026-05-06)

The original "Questions for Harsh" queue + the live decisions made 2026-05-05/06 are kept here as audit trail. Every
item now carries RESOLVED status + decision + the Phase 1.5a sub-section that executes the decision. When this plan
archives, every Q&A item is closed.

1. **FIX-5 design decision** — **RESOLVED 2026-05-05**: Option A (disk migration to canonical + writer lock to UAC
   `build_*_partition_path`). See `## FIX-5` section below + Phase 1.5a-2 (NormalisingManifestWriter chokepoint) and
   Phase 1.5a-4 (run existing `migrate_*_canonical.py` scripts).

2. **Manifest rebuild — proceed with what data?** — **RESOLVED 2026-05-06**: rebuild from disk truth, no inclusion
   filter. Per CLAUDE.md "honest absence vs fake placeholders", manifest = disk truth, not aspirational. The PREDICTION
   ~70× expansion is correct: numerator + denominator scale together → UI % stays meaningful. Aspirational denominators
   belong in deployment-api `data_status_service.py` (per_league_periodic etc.), not in the manifest. Executes inside
   Phase 1.5 main rebuild.

3. **F20 DeFi venue-key mismatch (`AAVE_V3` vs `AAVE_V3`)** — **RESOLVED 2026-05-06**: premise was partially wrong. Both
   manifest writer (`_defi_manifest.py`) and disk writer (`write_defi_rows`) store `(venue, chain)` separately and ARE
   aligned. The audit false-flag is a CASING+ALIAS issue handled by FIX-7+8 (already shipped — recon script normaliser).
   Verify with a post-Phase-1.5 audit re-run. No new code change needed beyond what's shipped.

4. **F21 DeFi vault_share_price aliases** (FRAX/MAKER/MORPHO_VAULTS/YEARN_V3) — **RESOLVED 2026-05-06**: these are
   architecturally distinct protocols (Morpho Blue lending ≠ MetaMorpho curated vaults; YearnV3, Frax, Maker are
   standalone yield protocols). Currently emitted by `vault_share_price_handler.py` but undeclared in UAC
   `ALL_DEFI_VENUES`. Decision: declare canonically as `MORPHOVAULTS-ETHEREUM`, `YEARN_V3-ETHEREUM`, `FRAX-ETHEREUM`,
   `MAKER-ETHEREUM` (matches existing no-underscore pattern AAVE_V3/UNISWAP_V3/COMPOUND_V3); add
   `LEGACY_DEFI_VENUE_ALIASES` mapping; update vault_share_price_handler to emit canonical. Executes in Phase 1.5a-1.

5. **F4/F5 stale test buckets** — **RESOLVED 2026-05-06**: live `gcloud storage ls` probe on all 4 candidate buckets
   (legacy `test-tradfi`, legacy `test-defi`, canonical `tradfi-test`, canonical `defi-test`) returned ZERO entries. No
   bucket-lifecycle action needed. Any stale manifest rows pointing at test-bucket names get cleaned up by Phase 1.5
   rebuild as a side-effect.

6. **F10/F11 BUG-X2 leaked-text rows** — **RESOLVED 2026-05-06**: live data shows ~76k of 86k CEFI `attempted_failed`
   rows are pollution (29,492 "Response payload not completed" + 23,568 "FUTURE row requires expiry_date" + 16,260
   "OPTION row requires..." + ~7k "In CSV column #N" + 9k other). Decision: one-shot flip to `VENUE_FETCH_FAILED` BEFORE
   Phase 1.5 rebuild — 30-second op, makes data-status honest immediately, reduces cognitive load. Executes in Phase
   1.5a-3.

7. **F25 TRADFI 100k non-hive `day-` blobs** — **RESOLVED 2026-05-06**: live probe confirms blobs exist with path-dates
   extending to `day-2026-01-04`; **zero `grep` hits for `day-` (hyphen) path templates anywhere in current MTDS
   source** → writer is gone (frozen pre-hive legacy). Decision: run existing `migrate_tradfi_to_hive.py` (server-side
   `gsutil mv`, ~5-min metadata op for ~100k blobs). Executes in Phase 1.5a-4.

8. **F18+F19+F20+F22+F23+F24 cluster — UTL write-time normaliser** — **RESOLVED 2026-05-06**: ship as
   `NormalisingManifestWriter` wrapper in UTL with **STRICT-FAIL** mode (any non-canonical `gcs_path=` raises
   `ValueError` at write-time). UAC `build_{cefi,defi,tradfi,prediction}_partition_path` are the canonical builders;
   wrapper validates incoming `gcs_path` against builder output and rejects mismatches. ~1-day refactor. This IS the
   FIX-5 Option A "writer lock-down" committed to in Q&A 1. Executes in Phase 1.5a-2.

9. **F26 PREDICTION coverage_start** — **RESOLVED 2026-05-06**: Polymarket Gamma API live probe returns ZERO markets for
   `start_date_min=2020-06-12`; UAC `external/polymarket/schemas.py:5` confirms "Available: November 21, 2022 (CLOB
   launch) onwards." Pre-CLOB on-chain LMSR markets exist on Polygon but require a separate on-chain indexer adapter
   (out of current scope). Decision: update UAC to **2022-11-21** (CLOB launch). Add `KNOWN_COVERAGE_GAPS` entry for the
   2020-06-12..2022-11-20 LMSR window (documented exclusion, not a backfill TODO). Executes in Phase 1.5a-1.

10. **MAJOR — existing disk migration scripts** — **RESOLVED 2026-05-05**: confirmed `migrate_sports_canonical.py`,
    `migrate_polymarket_canonical.py`, `migrate_tradfi_canonical.py`, `migrate_defi_canonical.py` all exist in MTDS; not
    yet run at scale. Decision: run them per-AG in Phase 1.5a-4 BEFORE the main Phase 1.5 manifest rebuild. Cheapest
    path to closing F16/F17/F22/F23/F24/F25.

## Phase 1.5a — Pre-rebuild Q&A operational follow-ups (gate for Phase 1.5 main rebuild)

Q&A items 4, 6, 7, 8, 9 each ship a discrete operational change before the main manifest rebuild runs. Order matters:
SSOT changes first (UAC), then writer enforcement (UTL), then one-shot manifest cleanups, then disk migrations, THEN the
existing Phase 1.5 rebuild (which operates on the now-canonical disk + manifest). Each step is gated on the prior step
passing.

### Phase 1.5a-1 — UAC SSOT alignment (Q&A 4 + Q&A 9)

- [x] [SCRIPT] P0. **UAC** `unified_api_contracts/registry/defi_venues.py`: - Add to `ALL_DEFI_VENUES`:
      `MORPHOVAULTS-ETHEREUM`, `YEARN_V3-ETHEREUM`, `FRAX-ETHEREUM`, `MAKER-ETHEREUM` (no-underscore canonical form per
      Q&A 4 decision). - Add to `LEGACY_DEFI_VENUE_ALIASES`: `MORPHO_VAULTS → MORPHOVAULTS-ETHEREUM`,
      `YEARN_V3 → YEARN_V3-ETHEREUM`, `FRAX → FRAX-ETHEREUM`, `MAKER → MAKER-ETHEREUM`. Audit-script normaliser
      auto-handles the legacy form via these aliases until the handler change in Phase 1.5a-2 lands. **Done 2026-05-06
      UAC `a901e91`** (CosmicTrader).
- [x] [SCRIPT] P0. **UAC** `unified_api_contracts/canonical/domain/prediction/coverage_starts.py` (or wherever
      `PREDICTION_COVERAGE_START` lives — verify location): change `POLYMARKET = "2020-06-12"` →
      `POLYMARKET = "2022-11-21"` (CLOB launch). Per Q&A 9. **Done 2026-05-06 UAC `a901e91`** — actual location was
      `canonical/coverage_starts.py` (the `(or wherever)` fallback in the original todo).
- [x] [SCRIPT] P0. **UAC** add `KNOWN_COVERAGE_GAPS` entry:
      `("polymarket", "*"): [(date(2020, 6, 12), date(2022, 11, 20))]` documenting the on-chain LMSR window as a
      provider-side exclusion (not a backfill TODO). Affects data-status denominator clipping. **Done 2026-05-06 UAC
      `a901e91`** — shipped as `PREDICTION_KNOWN_COVERAGE_GAPS` keyed `("POLYMARKET", "*")` (uppercase to match the
      per-asset-group dict pattern in `coverage_starts.py`).
- [x] [SCRIPT] P0. **MTDS** `cli/handlers/vault_share_price_handler.py`: emit canonical venue names (`MORPHOVAULTS`,
      `YEARN_V3`, `FRAX`, `MAKER`) instead of legacy `MORPHO_VAULTS` / `YEARN_V3`. **Done 2026-05-06 MTDS `8bf742a`**
      (CosmicTrader).
- [ ] [HUMAN] P0. UAC + MTDS quality-gates pass; commit + push (UAC first → wait for AR `:latest` to land per CLAUDE.md
      UTL→consumer race rule → then MTDS). **Operator-verify**: both repos pushed to origin/live-defi-rollout per
      `a901e91` + `8bf742a`; explicit QG run not yet logged.
- [x] [SCRIPT] P0. Lock-test: extend `tests/unit/sports/test_gcs_paths_player_values.py` pattern with a
      `tests/unit/defi/test_vault_venue_canonical_names.py` asserting the 4 canonical venues are in `ALL_DEFI_VENUES`
      and the legacy forms are in `LEGACY_DEFI_VENUE_ALIASES`. Regression-proof. **Done 2026-05-06 UAC `a901e91`** —
      shipped at `tests/unit/test_vault_venue_canonical_names.py` (1 dir higher than the original todo target; asserts
      identical guarantees).

### Phase 1.5a-2 — UTL NormalisingManifestWriter (Q&A 8) — **SUPERSEDED 2026-05-06**

> **Superseded by `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md` (commit `d591416d`)**, which folds the
> same write-time validation into `ManifestWriter.record_captured` directly via the 4-pillar write-gate (row-count > 0,
> NaN ratio < threshold, schema match, cluster coverage ≥ expected) rather than a separate `NormalisingManifestWriter`
> wrapper. Per the HANDOVER's coordination rule: "Don't build a parallel mechanism — once the UTL change lands, services
> just need to pass the clusters dict for any shard that's a bundle."
>
> The wrapper-vs-in-class trade-off was decided in favour of in-class because (a) every consumer needs the gates, not
> just opt-in callers; (b) keeps the manifest API surface single; (c) the cluster-coverage check generalises naturally
> beyond `gcs_path` validation. The original Phase 1.5a-2 todos below are kept as historical record but are no longer
> actionable on this plan — track the supersession in the HANDOVER.

- [ ] [SCRIPT] P0. ~~**UTL** new module `unified-trading-library/unified_trading_library/manifest_writer_normalising.py`
      wrapping `ManifestWriter`.~~ **Superseded** — replaced by in-class write-gates per HANDOVER Item 1.
- [ ] [SCRIPT] P0. ~~**UTL** `unified_trading_library/__init__.py`: export `NormalisingManifestWriter` alongside
      `ManifestWriter`~~. **Superseded** — no separate class; `ManifestWriter.record_captured` gains
      `expected_root_clusters` + `cluster_extractor` params instead.
- [ ] [SCRIPT] P0. ~~**UTL** unit tests: 4 cases~~. **Superseded** — write-gate tests will live alongside the existing
      `ManifestWriter` test suite per the new HANDOVER.
- [ ] [HUMAN] P0. ~~UTL quality-gates pass; commit + push.~~ **Superseded**.
- [ ] [SCRIPT] P0. ~~**MTDS** swap all production `ManifestWriter` instantiations to `NormalisingManifestWriter`~~.
      **Superseded** — no swap needed; existing callsites get the gates for free once UTL ships them. Per-service work
      reduces to passing the cluster dict for bundled shards (`options_chain`, `futures_chain`, prediction
      canonical-question groups, sports per-fixture aggregates).
- [ ] [HUMAN] P0. ~~MTDS quality-gates pass; commit + push.~~ **Superseded**.

### Phase 1.5a-3 — One-shot manifest cleanups (Q&A 6)

- [x] [SCRIPT] P0. **CEFI manifest BUG-X2 leaked-text flip**: 30-second script. For each row in
      `gs://market-data-tick-cefi-central-element-323112/_index/availability_index.parquet` where
      `capture_status='attempted_failed'` AND `error_reason` matches one of: `"Response payload is not completed"`,
      `"FUTURE row requires 'expiry_date'"`, `"OPTION row requires 'expiry_date'"`, `"In CSV column #*"`,
      `"StreamingParquetWriter pre-write validation failed"` → set `error_reason='VENUE_FETCH_FAILED'`.
      Backup-then-write pattern (mirror Phase 2 PLAYER_VALUES rebuild). Expected: ~76k rows touched of 86k
      attempted_failed. **Done 2026-05-05 MTDS `57b3da3`** — `scripts/flip_cefi_bug_x2_leaked_text.py` shipped with
      backup-then-write semantics; production run is the operator action below.
- [x] [SCRIPT] P0. **Vault venue manifest rename** (Q&A 4 follow-up): for each row in
      `gs://market-data-tick-defi-central-element-323112/_index/availability_index.parquet` where
      `data_type='vault_share_price'` AND `venue ∈ {MORPHO_VAULTS, YEARN_V3}` → rewrite venue to canonical form
      (MORPHOVAULTS, YEARN_V3). FRAX + MAKER already canonical (no underscore in source). Backup-then-write. **Done
      2026-05-05 MTDS `bf81219`** — `scripts/rename_vault_venue_canonical.py` shipped; production run is the operator
      action below.
- [x] [HUMAN] P0. **Production run — CEFI BUG-X2 flip done 2026-05-06T10:15:42Z** (executed via inline equivalent of
      `flip_cefi_bug_x2_leaked_text.py`; same backup-then-write semantics). - Backup:
      `gs://market-data-tick-cefi-central-element-323112/_index/availability_index.parquet.pre_bugx2_flip_20260506T101542Z.bak`
      (deleted post-verify). - **Result**: 83,924 rows flipped to `error_reason='VENUE_FETCH_FAILED'`; remaining BUG-X2
      leak rows = **0**. capture_status distribution unchanged: captured 1,024,362 / empty_confirmed 1,132,988 /
      attempted_failed 85,556. VENUE_FETCH_FAILED count rose from 54 → 83,978. - Patterns flipped: 29,472 "Response
      payload is not completed" + 23,498 "FUTURE row requires expiry_date" + 16,240 "OPTION row requires..." + 3,220
      "StreamingParquetWriter pre-write validation failed" + 11,494 "In CSV column #N".
- [ ] [HUMAN] P0. **Production run — vault venue rename** (DeFi manifest) via `rename_vault_venue_canonical.py`.
      Coordinate with concurrent stream; one-shot backup-then-write. Still operator-pending.
- [x] [HUMAN] P0. Re-read manifest sanity-check done — VENUE_FETCH_FAILED dominates the attempted_failed bucket
      post-flip; row counts and capture_status distribution intact.
- [x] [HUMAN] P0. Backup blobs deleted (both `pre_bugx2_flip_*` blobs removed via `gcloud storage rm`; manifest
      `_index/` listing shows zero `.bak` files).

### Phase 1.5a-4 — Disk migrations (Q&A 7 + Q&A 10)

> **Scripts confirmed ready 2026-05-06**: all 5 migrate scripts exist and were wrapped in `run_lifecycle` this session
> (MTDS `3e65dfb` + `3a5de78` + `8177955`). Phase is operator-gated; nothing to ship.
>
> **Path-template fix shipped 2026-05-06 MTDS `eeb03c3`**: `migrate_tradfi_to_hive.py` writes to canonical
> `day={D}/asset_group=tradfi/...` (not legacy `category=tradfi/`) per CLAUDE.md "Asset-group vocabulary" rule. Without
> this, the migration would have written to a legacy-vocab path requiring a second migration to re-key.
>
> **Shard-granularity coordination required (CRITICAL — 2026-05-06)**: dry-run revealed that `migrate_tradfi_to_hive.py`
> wrote at **per-day-aggregate** granularity (one `ticks.parquet` per `(date, venue, data_type)`, ~10k rows each) — but
> per CLAUDE.md "Shard-granularity SSOT" the canonical writer for TradFi splits at instrument-level (per-instrument for
> ETFs, per-root for futures+options bundles). Running the migration as-was would produce a SHARD ATOM that doesn't
> match writer atomicity / manifest row key / data-status display.
>
> **Rewrite shipped 2026-05-06 MTDS `b92e866`** — `migrate_tradfi_to_hive.py` now writes per-shard-atom output matching
> the v5 shard-key matrix:
>
> - TradFi futures: `(asset_group=tradfi, venue, data_type, instrument_type, root, day)` — bundled per root.
> - TradFi ETFs: `(asset_group=tradfi, venue, data_type, instrument_type, instrument_id, day)` — per-instrument.
> - TradFi options: `(asset_group=tradfi, venue, data_type, options_chain, root, day)` — bundled per root, 11-cluster
>   ES.OPT taxonomy.
>
> Output paths now match UAC `build_tradfi_partition_path` shape:
> `day={D}/asset_group=tradfi/venue={V}/instrument_type={IT}/data_type={DT}/{stem}.parquet` where `{stem}` is per-shard
> (ticker for ETFs, root for futures/chain bundles, symbol for indices/spot). The `output_dt` collapse that folded
> `futures_chain` and `options_chain` data_types is dropped — `instrument_type` and `data_type` are orthogonal axes per
> UAC SSOT. Inline `write_manifest_entries` (v2-schema) is disabled with rationale; the Phase 1.5 main rebuild
> reconstructs `availability_index` from on-disk truth at full v5 granularity post-migration.
>
> Coordination with `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`: the per-shard-atom output is stable
> today. Once Stream A's `ManifestWriter.record_captured` gains `expected_root_clusters` + `cluster_extractor` params, a
> follow-up patch will wire ManifestWriter v5 row writing into this script and pass cluster dicts for ES.OPT 11-cluster
>
> - futures-chain by-root. **DO NOT RUN before that follow-up lands** — running with manifest writes disabled means the
>   orchestrator's pre-flight skip won't see the new files until Phase 1.5 main rebuild completes; safe but creates a
>   transient gap in data-status visibility.
>
> Inventory of legacy data (verified 2026-05-06): 100,698 source files across 12 `day-` directories spanning 2025-11-02
> to 2026-02-01. Sample per date: 82 NASDAQ + 426 NYSE ohlcv_1m equities + 40 CME options_chain + 10k+ CME trades. Real
> unique data — NOT duplicates of canonical day=\*/asset_group=tradfi/ contents (probed ABBV/IBIT/AUD on 2025-11-02 —
> none in canonical).

- [ ] [HUMAN] P0. **TRADFI legacy `day-` migration** (Q&A 7): run
      `cd market-tick-data-service && .venv/bin/python scripts/migrate_tradfi_to_hive.py --dry-run` first. Verify the
      script touches ~100k blobs and the per-shard output paths match
      `day={D}/asset_group=tradfi/venue={V}/instrument_type={IT}/data_type={DT}/{stem}.parquet` (where `{stem}` is
      ticker for ETFs, root for futures/chain bundles, symbol for indices/spot). Then `--apply`. **Script-side ready
      2026-05-06 MTDS `b92e866`** — per-shard-atom rewrite shipped; gated on Stream A's `ManifestWriter.record_captured`
      cluster-coverage params landing before production run so manifest gets v5 rows alongside the disk writes.
- [ ] [HUMAN] P0. **Per-AG canonical migrations** (Q&A 10): same pattern for each existing migrate script. Order
      smallest-first to fail-fast on regressions: - PREDICTION: `scripts/migrate_polymarket_canonical.py` - SPORTS:
      `scripts/migrate_sports_canonical.py` - DEFI: `scripts/migrate_defi_canonical.py` - TRADFI:
      `scripts/migrate_tradfi_canonical.py` (separate from `migrate_tradfi_to_hive.py` above — verify before running) -
      CEFI: covered by existing per-VM shard pattern; no separate migrate script needed. **All 4 scripts ready** —
      verified at `market_tick_data_service/scripts/migrate_*_canonical.py`; each emits paired RUN_STARTED +
      RUN_COMPLETED|FAILED via the new `run_lifecycle` helper for traceability.
- [ ] [HUMAN] P0. Re-run `audit_legacy_paths.py` per AG → expected non-canonical count ≈ 0.

### Phase 1.5a-5 — Hive vocab audit on migration writers (added 2026-05-06)

Before any per-AG canonical migration runs, all writer-side `category=` (legacy) hive vocab in migration scripts needed
flipping to canonical `asset_group=` (per CLAUDE.md "Asset-group vocabulary" SSOT
`raw_tick_hive.RAW_TICK_ASSET_GROUP_HIVE_KEY`). Without this, every migration would write to a non-canonical path that
would itself need a second migration to re-key — entirely defeating the purpose of running them.

**Audit scope (2026-05-06)**: ripgrep across all repos for code constructing `category=` paths. 8 hits identified.
Per-script classification:

| Script                                                                 | Site                                                  | Category                                                             | Action                                                                                          |
| ---------------------------------------------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `_migrate_tradfi_classifier.py`                                        | `_canonical_key()` line 253                           | WRITER                                                               | **fixed** MTDS `037c3bb`                                                                        |
| `migrate_polymarket_canonical.py`                                      | `canonical_key()` line 377 (outer) + line 381 (inner) | WRITER (outer) + collision (inner)                                   | **fixed** MTDS `037c3bb` (see polymarket-specific block below)                                  |
| `migrate_sports_canonical.py`                                          | `_canonical_key()` line 201                           | WRITER                                                               | **fixed** MTDS `037c3bb`                                                                        |
| `migrate_cefi_instrument_types.py`                                     | 3 `new_path` sites (lines 208, 265, 288)              | WRITER                                                               | **fixed** MTDS `037c3bb`                                                                        |
| `migrate_deribit_margin_split_v6.py`                                   | `prefix_tardis` line 234                              | READER (legacy probe)                                                | leave as-is — correct fallback                                                                  |
| `migrate_to_per_instrument.py`                                         | `search_prefix` lines 145, 147                        | READER + in-place WRITER                                             | leave as-is — splits at SAME hive prefix, doesn't move between vocab                            |
| `restructure_tradfi_files.py`                                          | `target_path` lines 132, 215                          | In-place WRITER (same hive prefix)                                   | leave as-is — same in-place pattern                                                             |
| `deployment-service/.../data_status_checkers.py`                       | `calendar/category={fg}/` line 437                    | Different namespace (calendar feature-group, not raw_tick_data hive) | leave as-is — separate SSOT                                                                     |
| `deployment-api/.../*` (drilldown, storage_facade, shard_detail, mock) | many                                                  | READER fallback                                                      | leave as-is — correct per CLAUDE.md "Readers must try canonical first then fall back to legacy" |

**Polymarket-specific 2026-05-06 (canonical_key 6-dim layout)**:

The polymarket migration's "canonical" 6-dim layout had a NAMING COLLISION with the MTDS hive vocab:

- Outer partition (asset-group axis): was `category=prediction` → now `asset_group=prediction` (canonical hive vocab).
- Inner partition (Polymarket market category — CRYPTO_PRICE / POLITICS_US / ...): was `asset_group=BTC` → now
  `market_class=BTC`. Without this rename, the new outer-canonical path would read like
  `asset_group=prediction/.../asset_group=BTC/` — same partition key with two different values, breaking hive semantics
  entirely.
- Renamed all 8 in-script sites: function param, DataFrame column (`df["asset_group"]` → `df["market_class"]`), path
  partition string, `_CANONICAL_PATH_MARKER` (was `/asset_group=` → now `/market_class=`), shard_cols list, docstring.
- Test file (`test_migrate_polymarket_canonical.py`): 11 sites updated (DataFrame col, kwargs, output path strings,
  canonical-marker fixture). 15/15 polymarket tests pass; 16/16 tradfi tests pass.

**Polymarket intermediate-canonical re-migration (one-off, NEW item)**:

- [ ] [HUMAN] P1. **Re-migrate intermediate-canonical Polymarket files** — earlier runs of
      `migrate_polymarket_canonical.py` wrote to the now-deprecated intermediate canonical path:
      `category=prediction/data_source=POLYMARKET_CLOB/.../asset_group=BTC|ETH|.../market_type=*/...{cid}.parquet`.
      After the 2026-05-06 vocab + collision fixes, these files match neither (a) the legacy `_SOURCE_PATH_RE` (which
      targets the original BNB-overload pattern) nor (b) the new `_CANONICAL_PATH_MARKER = "/market_class="`. They will
      be silently skipped by future migrate runs. - **Action**: write a one-off re-migration script (or extend
      `migrate_polymarket_canonical.py` with `--re-migrate-intermediate-canonical` flag) that: 1. Detects files at
      `category=prediction/.../asset_group={CRYPTO_PRICE|POLITICS_US|...}/...{cid}.parquet` via a dedicated regex (the
      OLD inner `asset_group=` was always the categorisation token, not BTC/ETH — i.e. it matched the value space
      CRYPTO_PRICE/POLITICS_US/MISC/etc). 2. For each match: rename the path to the new canonical:
      `asset_group=prediction/.../market_class={CAT}/...{cid}.parquet` via server-side `bucket.copy_blob` + original
      delete (cheap GCS metadata op, no row reads). 3. Manifest is rebuilt from disk truth in the existing Phase 1.5
      main rebuild — no inline manifest writes. - **Inventory** (must run before scripting):
      `gcloud storage ls --recursive       gs://market-data-tick-prediction-central-element-323112/raw_tick_data/by_date/day=*/category=prediction/.../asset_group=*/`
      and exclude false-positive matches where the inner `asset_group=` value is `prediction` (which would mean the
      OUTER hive partition was already canonical and the path is mis-shaped — different bug). - Estimated scope: any
      polymarket data ever migrated by a prior run of this script (likely 0–N days, operator probe required to
      confirm). - Tracked in
      [`shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`](shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md)
      as a per-service migration-verify item.

### Phase 1.5a — exit gate

- [ ] [HUMAN] P0. Confirm all four 1.5a sub-phases (1/2/3/4) green:
  - UAC canonical venues + PREDICTION_COVERAGE_START shipped, lock-tests pass.
  - UTL NormalisingManifestWriter shipped, MTDS callers swapped, no validation errors at QG.
  - CEFI manifest BUG-X2 flip done; vault venue rename done.
  - All disk migrations apply'd; `audit_legacy_paths.py` shows ~0 non-canonical paths.
- [ ] [HUMAN] P0. ONLY THEN proceed to the existing Phase 1.5 main manifest rebuild below.

## Live operations log (newest first — read this to know what's happening RIGHT NOW)

This section is the operating surface. Every audit run, finding, fix decision, and background-agent dispatch lands here
with timestamp + status. If you're checking on the work, start here. The phase scaffolding below is the framework; this
log is the ground truth.

| Timestamp (UTC) | Phase        | What                                                                                                                                                                                                                                                                    | Status      | Output / link                        |
| --------------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------ |
| 2026-05-05      | DISCOVERY-0  | Plan restructure to live-ops format                                                                                                                                                                                                                                     | done        | commit `41ace8c`                     |
| 2026-05-05      | DISCOVERY-1  | UAC registry survey — VENUES_BY_ASSET_GROUP, DATA_TYPES_BY_ASSET_GROUP, VENUE_DATA_TYPE_CAPABILITIES, partition_paths.py, raw_tick_hive                                                                                                                                 | done        | see "Registry SSOT cheatsheet" below |
| 2026-05-05      | DISCOVERY-2  | **Found existing audit script — `market-tick-data-service/scripts/reconcile_market_tick_manifest.py`** does forward+inverse phantom detection. Approach pivots: USE this script, don't write a new one. Add a companion probe for drift axes its PATH_RE doesn't cover. | done        | finding below                        |
| 2026-05-05      | DISCOVERY-3  | Build companion legacy-path probe + structural-checks scripts                                                                                                                                                                                                           | done        | commits `8ca5e67`, `d04941e`         |
| 2026-05-05      | DISCOVERY-4  | Run 6 structural cross-cutting checks across 4 AGs (CEFI still running)                                                                                                                                                                                                 | done        | findings F1-F9 below                 |
| 2026-05-05      | DISCOVERY-5  | Smoke recon on PREDICTION/DERIBIT — found scaling bug (full-bucket list)                                                                                                                                                                                                | done        | finding F14                          |
| 2026-05-05      | FIX-1        | Patch recon: per-day prefix listing — 100x speedup                                                                                                                                                                                                                      | done        | commit `24b38ed`                     |
| 2026-05-05      | FIX-2        | Patch recon: add SPORTS to ASSET_GROUP_BUCKETS dict (was missing)                                                                                                                                                                                                       | done        | finding F15, commit pending          |
| 2026-05-05      | DISCOVERY-6  | Spot-check real DeFi/Sports paths during full-range recon → CRITICAL findings F16+F17                                                                                                                                                                                   | done        | findings F16, F17                    |
| 2026-05-05      | DISCOVERY-7  | F6 DeFi 0% attempted_failed closed as observation (wiring is correct)                                                                                                                                                                                                   | done        | F6 closed                            |
| 2026-05-05      | FIX-3+4+F18  | Extend recon PATH_RE for DeFi/Sports layouts + handle schema-v4 manifests                                                                                                                                                                                               | done        | commit `6b1a2f5`                     |
| 2026-05-05      | DISCOVERY-8  | Smoke patched recon → F19 (sports case mismatch) + F20 (DeFi venue-key mismatch)                                                                                                                                                                                        | done        | findings F19, F20                    |
| 2026-05-05      | NEXT         | FIX-7: case-insensitive comparison in recon (covers F19)                                                                                                                                                                                                                | next        | TBD                                  |
| 2026-05-05      | NEXT         | FIX-8: DeFi venue-key normaliser in recon (covers F20)                                                                                                                                                                                                                  | next        | TBD                                  |
| 2026-05-05      | DISCOVERY-9  | Smoke patched recon → F19 (sports case mismatch) + F20 (DeFi venue-key)                                                                                                                                                                                                 | done        | findings F19, F20                    |
| 2026-05-05      | FIX-7+8      | Case-insensitive compare + DeFi venue-key normaliser                                                                                                                                                                                                                    | done        | commit `c335eba`                     |
| 2026-05-05      | FIX-10       | audit_legacy_paths: scope to raw_tick_data/ prefix only                                                                                                                                                                                                                 | done        | commit `b159b1b`                     |
| 2026-05-05      | DISCOVERY-10 | Spot-check during prediction legacy-paths → F22 (10-segment) + F23 (8-segment sports)                                                                                                                                                                                   | done        | findings F22, F23                    |
| 2026-05-05      | FIX-9        | Add F22 + F23 path patterns to recon + audit_legacy_paths                                                                                                                                                                                                               | done        | commit `e096185`                     |
| 2026-05-05      | FIX-11       | \_CANONICAL_PATH_RE allows optional `chain=` for DeFi (98% of DeFi disk is canonical+chain)                                                                                                                                                                             | done        | commit `37d78f2`                     |
| 2026-05-05      | F11-detail   | All 3220 CEFI schema-validation rejects are ASTER (BUG-X1 stale sentinels)                                                                                                                                                                                              | done        | committed                            |
| 2026-05-05      | F25          | TRADFI ~100k blobs at non-hive `day-data_type-` layout (NEW finding)                                                                                                                                                                                                    | logged      | needs Ikenna call                    |
| 2026-05-05      | FIX-12       | AXIS4 regex matches BOTH literal-empty (`instrument_type=/`) and absent-segment forms                                                                                                                                                                                   | done        | commits `d2ec7e8` + `f50d5ac`        |
| 2026-05-05      | NOW          | Full-range recon + legacy-paths audit running across all 5 AGs (9 parallel via wrapper scripts)                                                                                                                                                                         | in_progress | TBD                                  |
| 2026-05-05      | NEXT         | Aggregate findings + design FIX-5 / FIX-6 from results                                                                                                                                                                                                                  | pending     | TBD                                  |

## Findings F1-F9 — structural-check audit (2026-05-05)

Output: `/tmp/mtds-audit/structural/check{1-6}-{ag}.csv` + `SUMMARY.txt`.

### F1 — SPORTS manifest is fully schema-v4

- 17,288 rows, **all `schema_version=4`**. Manifest is now v6 (per UTL `MANIFEST_SCHEMA_VERSION`).
- Manifest **lacks `capture_status`, `error_reason`, `attempted_at` columns** — readers backfill them as `captured` /
  `""` / `""` for any v4 row.
- Implication: **every sports row currently looks "captured" to data-status readers**, even those that genuinely failed
  or were empty. We literally cannot tell honest coverage for sports without a rebuild to v5+.
- Root cause: sports MTDS writers either haven't been updated to v5+ (or never were the path) OR no rebuild has run
  since the v4→v5 migration.
- Severity: **HIGH** — blocks honest-coverage measurement for sports.
- Fix candidate: rebuild sports manifest (Phase 1.5 in this plan) using `rebuild_mtds_manifest.py` with v6 schema.

### F2-CEFI — CEFI manifest also has mixed-itype rows (v4/v6 coexistence)

Sampled CEFI manifest by (venue, instrument_type, data_type):

```
OKX-SPOT       spot_pair  trades            154,981  (v6 with itype populated)
OKX-FUTURES    perpetual  trades            105,143  (v6)
COINBASE-SPOT  spot_pair  trades             90,490  (v6)
OKX-SWAP       perpetual  trades             65,792  (v6)
KRAKEN-SPOT    ''         trades             56,411  (v4 — empty itype!)
KRAKEN-SPOT    ''         book_snapshot_5    56,411  (v4)
BINANCE-SPOT   ''         trades             51,074  (v4)
BINANCE-SPOT   ''         book_snapshot_5    50,722  (v4)
COINBASE-SPOT  ''         book_snapshot_5    48,659  (v4)
BINANCE-SPOT   spot_pair  trades             47,773  (v6)
BINANCE-SPOT   spot_pair  book_snapshot_5    46,609  (v6)
```

So **same venue (BINANCE-SPOT) has BOTH v6 rows (with itype=spot_pair) AND v4 rows (with empty itype)**. That's the
16,224 v4 rows from F2 distributed across multiple venues. Recon should be matching these because the canonical PATH_RE
accepts empty itype (after FIX-12 / d2ec7e8). But these manifest rows also need to be tied to disk via tuple comparison
— and disk has `instrument_type=spot_pair` not empty.

**This means recon on CEFI WILL show false phantoms** for the v4 rows: manifest claims captured with empty itype, disk
has captured at `spot_pair`. Same shape, different itype field. Will be ~16k phantoms.

The fix is recon's `_normalise_key` for CEFI — collapse instrument_type to "" so v4-vs-v6 matches. Currently the
normaliser only does this for DEFI. **Adding TBD as FIX-13** for after CEFI recon completes and confirms the impact.

### F2 — TRADFI manifest mixes v4 + v6 schemas (23% v4)

- Distribution: **v4=16,656 (23%) + v6=55,724 (77%)** of 72,380 rows.
- v4 rows lack `capture_status` → readers see them as captured by default.
- Implication: 23% of TRADFI rows can't be classified honestly — frozen as `captured` even if data is gone.
- Severity: **MEDIUM** — partial corruption, manageable via rebuild for the v4 slice.
- Fix candidate: rebuild on `schema_version=4` rows only, OR full TRADFI rebuild.

### F3 — Chronology: 53-81% of rows have `written_at` 365+ days AFTER data date

| AG         | 365+ days "suspicious" | % of total rows |
| ---------- | ---------------------: | --------------: |
| SPORTS     |        14,072 / 17,288 |         **81%** |
| TRADFI     |        54,175 / 72,380 |         **75%** |
| DEFI       |      164,612 / 313,365 |         **53%** |
| PREDICTION |           681 / 14,369 |          **5%** |

- Three possible interpretations to disambiguate:
  - (a) **Benign** — recent rebuild scripts overwrote `written_at` to the rebuild time. Sports rebuild logic copies a
    fresh `written_at`. Verify by checking if `written_at` clusters around a rebuild date.
  - (b) **Late real-time write** — adapter wrote the row long after the data date. Means the orchestrator was catching
    up on a backlog, not a bug.
  - (c) **Manifest written for data that doesn't exist** — drift bug. Cross-check against capture_status: a `captured`
    row with no parquet on disk is a phantom (already detected by `reconcile_market_tick_manifest.py`).
- Severity: **MEDIUM** — observability concern, not necessarily a bug. Need disambiguation.
- Fix candidate: spot-check 20 random "365+" rows per AG: compare `written_at` cluster vs GCS object creation timestamp;
  if `written_at >> ctime`, that's a rebuild signature (benign-ish). If `written_at < ctime`, manifest is lying.

### F4 — TRADFI has 3 buckets (canonical + 2 test-name variants)

- `market-data-tick-tradfi-central-element-323112` (canonical)
- `market-data-tick-test-tradfi-central-element-323112` (legacy test naming `test-{ag}`)
- `market-data-tick-tradfi-test-central-element-323112` (canonical test naming `{ag}-test`)
- Root cause: bucket-naming convention drifted from `test-{ag}` to `{ag}-test`; the legacy bucket was never cleaned up.
- Severity: **LOW** for the legacy test bucket (probably empty / unused), but worth confirming + retiring.
- Fix candidate: `gsutil ls -l gs://market-data-tick-test-tradfi-central-element-323112/` to confirm empty; if so,
  retire it. Same drift on DeFi (`market-data-tick-test-defi-` vs `market-data-tick-defi-test-`).

### F5 — DEFI test bucket drift mirrors F4

Same drift: `market-data-tick-defi-test-` (canonical) + `market-data-tick-test-defi-` (legacy). Same severity + fix.

### F6 — DEFI manifest has 0% attempted_failed and 0.2% empty_confirmed

- 313,365 rows total. **312,680 captured + 685 empty_confirmed + 0 attempted_failed.**
- For a long-tail of 30 protocols × 11 chains × 20 data_types over multiple years, **expected** to see many
  legitimately-empty cells (pre-launch dates, paused protocols, chain not yet supported by protocol).
- 0 `attempted_failed` is suspicious — even healthy adapters hit transient errors at scale.
- Possibilities:
  - (a) DeFi adapters don't call `record_empty()` / `record_failed()` correctly.
  - (b) DeFi adapter wraps every error as a successful empty (lying) — silent failures.
  - (c) DeFi orchestrator pre-skips most cells via coverage_starts so the writer never gets called.
- Severity: **MEDIUM-HIGH** — blocks empty-vs-failed accuracy for DeFi.
- Fix candidate: grep DeFi adapters for `record_empty` and `record_failed` usage; cross-check against the orchestrator
  pre-skip logic in `coverage_starts.py`.

### F7 — PREDICTION manifest mixes v4/v5/v6 (99.5% v4)

- 14,296 v4 + 2 v5 + 71 v6 of 14,369 rows.
- Same problem as F1 (sports) but at smaller scale.
- Severity: **HIGH** — 99.5% of prediction rows can't carry honest-coverage state.
- Fix candidate: rebuild prediction manifest at v6.

### F8 — TRADFI per-VM shard backlog: 268 shards, none stuck-stale

- Distribution: 95 (1d-7d), 167 (1h-24h), 4 (5m-1h), 2 (<5m). 0 in 30d+.
- Reading: consolidator IS running, but not aggressively merging. 95 1-day-old shards is a backlog.
- Severity: **LOW** — readers fall back to per-VM merge after 120s staleness; they'll see fresh data.
- Verify: check `manifest-consolidator-*` VM is RUNNING in `asia-northeast1-c`.

### F9 — Sports per-VM shard: 1 shard 1-7 days old, never merged

- Single per-VM shard, 1-7 days old. May be a stuck shard the consolidator can't merge (sports manifest is v4 →
  consolidator may reject v4-to-canonical merges).
- Severity: **MEDIUM** — could be the why behind F1 (sports stuck at v4).
- Fix candidate: check consolidator log for sports merge errors.

### CEFI structural-check additions

#### F1' — CEFI mostly v6 (healthy)

- Distribution: **v6=2,179,658 (97.9%) + v5=30,749 (1.4%) + v4=16,224 (0.7%)** of 2,226,631 rows.
- Much healthier than sports/prediction. Small v4/v5 residue could be cleaned up but not blocking.

#### F3' — CEFI: 82% of rows have written_at 365+ days suspicious

- 1,831,164 / 2,226,631. Consistent with a recent rebuild scenario more than a bug.
- Same disambiguation needed as F3.

#### F3 disambiguation result (2026-05-05) — BENIGN rebuild signature, NOT a bug

Sampled 1.83M CEFI late rows. The `written_at` distribution clusters around very recent dates:

- 2026-05-04: 951k rows (52%)
- 2026-04-29: 530k rows (29%)
- 2026-05-01: 181k rows
- 2026-04-30: 51k rows
- 2026-05-05: 41k rows

The data dates these rows reference span 2019-2024. So the writers ran in late April / early May 2026 and wrote manifest
rows for years-old data. That's **the 2026-04-29 366-VM rollout** + **2026-05-04 backfill VMs** populating the manifest
from disk truth (or from a fresh fetch).

**Conclusion**: F3 is the rebuild-write timestamp signature, not phantom rows or a writing-without-data bug. The data IS
captured (recon shows 99.7% match rate for CEFI). The high "365+ day" count just means the rebuild stamped
`written_at = rebuild_time` on rows that originally referred to data from years ago.

**Closed as observed-and-explained**, not actionable. If we want a "true ingest time" later, we'd need to preserve the
original write timestamp — which would require a writer change. Not worth doing for the audit purpose.

#### F6' — CEFI capture_status distribution

- captured: 1,021,335 (45.9%)
- empty_confirmed: 1,119,274 (50.3%) — high but explainable via pre-launch / pre-listing date clipping
- attempted_failed: 86,022 (3.9%) — matches BUG-X1 cluster from prerequisite section

#### F8' — CEFI per-VM shard backlog: 1,249 shards (none stuck-stale)

- 1,156 (1d-7d) + 83 (1h-24h) + 7 (5m-1h) + 3 (<5m). 0 in 30d+.
- Consolidator running but heavily lagged. Worth investigating why merges queue this deep on CeFi.

### F10-F13 — error_reason cluster analysis (CEFI + TRADFI)

#### F10 — CEFI: 29,513 rows of `Response payload is not completed` error

- Tardis/HTTP transport error. Distinct from BUG-X1 — these are real fetch failures.
- BUG-X2 fix in MTDS `fe5cc2c` writes generic `VENUE_FETCH_FAILED` for new failures, but **these old rows still have the
  raw exception text** in `error_reason`.
- Severity: **MEDIUM** — these are real failed shards that should be re-attempted. Do NOT need a code fix; a manifest
  rebuild will overwrite them with fresh error classifications. Or: backfill VMs will retry them.
- Fix candidate: leave in place; phase 2 backfill will retry them via `_should_skip_shard` doing the right thing.

#### F11 — CEFI: 3,220 rows of `StreamingParquetWriter pre-write validation failed`

- Write-time schema validation rejected the parquet. The writer was called but the row data didn't conform to the
  registered SchemaDefinition.
- This is the **schema-validation-before-write** invariant correctly firing — caught bad rows, didn't write bad data to
  disk.
- Severity: **MEDIUM** — need to break down which (venue, data_type) is producing rejected rows. If it's a consistent
  pattern (e.g. one venue's adapter producing bad shape), that's a fix at the adapter level.
- Fix candidate: query CEFI manifest where `error_reason LIKE 'StreamingParquetWriter%'` group by (venue, data_type).
  Document the breakdown, then fix the adapter producing bad rows.

#### F12 — CEFI: ~7,000 rows leaking raw CSV-column error text (`In CSV column #N`)

- Tardis CSV parser hit bad rows, raised `pyarrow` (or pandas) exception, exception text leaked into `error_reason`.
  Same BUG-X2 pattern as the original DERIBIT cluster.
- BUG-X2 fix in `fe5cc2c` covers this for NEW failures but the old rows persist.
- Severity: **LOW** — manifest carries verbose error strings instead of a clean classification.
- Fix candidate: rebuild manifest to overwrite, OR confirm `classify_venue_error()` now catches these (BUG-X2 patch).

#### F13 — TRADFI: 94% of attempted_failed rows are recon-script-flipped phantoms

- 254 / 270 have `error_reason=phantom_captured_no_parquet_at_canonical_path`. These were flipped by a prior
  `reconcile_market_tick_manifest.py --commit` run.
- Other 16 are `StreamingParquetWriter pre-write validation failed`.
- Severity: **NONE** — expected, recon working correctly. Documents the prior recon run.

### F14 — PREDICTION axis-4 phantoms (schema-v4 instrument_type empty)

Surfaced by smoke run of patched recon on PREDICTION 2025-12-01..2025-12-07.

- 14 forward phantoms across 7 days. Pattern: every day has the same 2 row shapes claiming `captured` with no parquet on
  disk:
  - `('YYYY-MM-DD', 'POLYMARKET', '', 'trades')` — empty `instrument_type` (schema-v4 vestige)
  - `('YYYY-MM-DD', 'POLYMARKET', 'prediction_market', 'trades')` — canonical
- Disk has the same shape captured at canonical path; manifest **double-counts** because of the schema-v4
  empty-instrument-type axis 4.
- Reading: schema-v4 sentinel rows from older runs are now phantoms. Phase 1.5 manifest rebuild will eliminate them by
  re-keying canonically.
- Severity: **MEDIUM** — confirms the F1/F7 schema-mix problem is producing reader-visible phantoms.
- This is exactly the failure mode Ikenna described: "data exists but the manifest claims missing/wrong because schema
  mixed."

### F15 — `reconcile_market_tick_manifest.py` doesn't support SPORTS

- `ASSET_GROUP_BUCKETS` dict has CEFI/TRADFI/DEFI/PREDICTION but **omits SPORTS**.
- `--asset-group SPORTS` raises `argparse error: invalid choice`.
- Combined with F1 (sports manifest 100% schema-v4) and F9 (sports stuck per-VM shard), sports has been invisible to the
  reconciler since it was added.
- Severity: **MEDIUM** — gap in tooling coverage. Quick fix landing in same patch as FIX-1.
- Fix: add `"SPORTS": f"market-data-tick-sports-{PROJECT_ID}"` to the dict. **LANDED commit `9005917`.**

### F16 — DeFi paths skip `instrument_type` + `data_type` segments entirely (CRITICAL)

Surfaced by GCS spot-check during full-range recon:

```
gs://market-data-tick-defi-central-element-323112/raw_tick_data/by_date/day=2024-06-15/asset_group=defi/venue=AAVE_V3-ETHEREUM/ticks_migrated_20260418T132205Z.parquet
```

The DeFi disk layout has:

- `asset_group=defi` ✅
- `venue=AAVE_V3-ETHEREUM` ❌ (legacy venue overload — chain baked in, no separate `chain=` segment — axis 6)
- ❌ NO `instrument_type=` segment at all
- ❌ NO `data_type=` segment at all
- File is `ticks_migrated_<TIMESTAMP>.parquet` (suggests last-touched-by-migration provenance)

**Implications**:

- Recon canonical PATH_RE needs `instrument_type=` AND `data_type=` AND chain= (or via venue overload). DeFi disk
  matches **none of those** — the entire DeFi bucket is invisible to recon.
- Manifest claims for DeFi go through bucket-write but disk is at a non-canonical path → **manifest forward-phantom
  count is over-reported** (recon thinks all DeFi captured rows have no parquet) AND **reverse phantoms are
  under-reported** (recon doesn't see DeFi parquets exist) — manifest disagreement is bidirectional.
- The `_migrated_<TS>` suffix suggests the 2026-04-18 migration ran but didn't fully canonicalise paths.
- Severity: **CRITICAL** — DeFi audit/recon is fundamentally broken until either disk layout is fixed OR audit script
  knows about this DeFi-specific shape.

### F17 — SPORTS disk layout uses `category=sports` (legacy hive vocab) AND empty `instrument_type=` (CRITICAL)

Surfaced by GCS spot-check:

```
gs://market-data-tick-sports-central-element-323112/raw_tick_data/by_date/day=2024-06-15/category=sports/venue=ODDS_API/instrument_type=/data_type=odds/ticks.parquet
```

- `category=sports` ❌ (legacy hive vocab — should be `asset_group=sports`, axis 1)
- `instrument_type=` literally empty ❌ (axis 4 — empty segment between `=` and next `/`)
- The PATH_RE uses `instrument_type=(?P<itype>[^/]+)/` which requires NON-EMPTY content between `=` and `/`. **An empty
  segment matches NEITHER** the canonical PATH_RE nor any of audit_legacy_paths.py's drift-axis regexes — this is in
  fact a **NEW axis (axis 4 variant) we haven't fully encoded**.

**Implications**:

- 100% of SPORTS disk data is invisible to the canonical recon PATH_RE.
- F1 (sports manifest 100% schema-v4) is consistent with F17: writers wrote both empty-instrument_type rows and legacy
  `category=` paths, never updated to v5+.
- Severity: **CRITICAL** — sports audit/recon fundamentally broken.
- **Confirms Ikenna's hypothesis from 2026-05-05**: data IS on disk but manifest/UI can't see it because of schema/path
  drift.

### F18 — recon crashes on schema-v4 manifests (KeyError: 'capture_status')

- Recon `main()` did `df_slice[df_slice["capture_status"] == "captured"]` unconditionally.
- Sports manifest is schema-v4 (F1) — no `capture_status` column → KeyError.
- **Fix landed in `6b1a2f5`**: if column missing, treat all rows as `captured` (matches UTL `read_availability_index`
  backfill behaviour).

### F19 — Sports `data_type` case mismatch (manifest UPPERCASE vs disk lowercase)

Surfaced by smoke run of patched recon on SPORTS 2024-06-15:

- Manifest claim: `('2024-06-15', 'ODDS_API', '', 'ODDS')` — **uppercase `ODDS`**
- Disk truth: `('2024-06-15', 'ODDS_API', '', 'odds')` — **lowercase `odds`**

Same shape as the known instrument_type-casing axis (axis 3) but on `data_type`. Recon's tuple-key compare is
case-sensitive → manifest claim and disk truth never match. Result: every captured shard becomes BOTH a phantom AND a
missing_row simultaneously.

- Severity: **MEDIUM** — inflates phantom + missing-row counts equally on sports.
- Fix candidate: add case-insensitive comparison on data_type AND instrument_type when reconciling. Better: write-time
  normalisation — UTL ManifestWriter should lowercase before persisting.

### F22 — PREDICTION uses 10-segment path layout (NEW axis discovered 2026-05-05)

```
raw_tick_data/by_date/day=2025-03-14/
  category=prediction/
  data_source=POLYMARKET_CLOB/
  venue=POLYMARKET/
  chain=POLYGON/
  market_category=CRYPTO_PRICE/
  underlying=BTC/
  market_type=binary/
  resolution_period=monthly/
  data_type=trades/
  0x796f....parquet
```

10 segments instead of canonical 6. Discovered when audit_legacy_paths reported 39,235 of 40,000 raw_tick_data blobs as
UNKNOWN axis. Adapter is emitting prediction-specific dimensions (data_source, market_category, underlying, market_type,
resolution_period) as path segments.

- Severity: **CRITICAL** — entire PREDICTION raw_tick_data layer is invisible to recon's canonical PATH_RE.
- Fix: added `_PREDICTION_DEEP_PATH_RE` to recon variants. After fix: PREDICTION 1-day smoke went from 8 matched / 2
  phantom to 9 matched / 1 phantom (most blobs now visible).

### F21 — RESOLVED — DEFI vault_share_price residual phantoms were a recon bug, not a data issue

Earlier DEFI 1-day smoke (2024-06-15, before FIX-11 landed) reported 4 phantoms: `FRAX, MAKER, MORPHO_VAULTS, YEARN_V3`
× `vault_share_price`.

After FIX-11 (`_CANONICAL_PATH_RE` allows optional `chain=`):

```
Total DEFI vault_share_price rows: 5036
By venue:   MORPHO_VAULTS=1008, ETHENA=1007, FRAX=1007, MAKER=1007, YEARN_V3=1007
By chain:   ETHEREUM=5036
capture_status: captured=4469, empty_confirmed=567, attempted_failed=0
```

All 5 venues are valid DeFi protocols on Ethereum chain. Manifest tracks them correctly. The earlier "phantom"
classification was caused by recon's canonical PATH_RE not allowing the `chain=` segment, so it failed to match the disk
paths even though the data was there.

**F21 closed as false alarm. Bug was in recon, not in data.** FIX-11 resolved it.

### F11-detail — ALL 3,220 CEFI schema-validation reject rows are ASTER

Investigation result. F11 surfaced 3,220 `StreamingParquetWriter pre-write validation failed` rows in CEFI manifest.
Breakdown by (venue, data_type):

```
ASTER  book_snapshot_5      920
ASTER  derivative_ticker    920
ASTER  trades               920
ASTER  liquidations         460
```

100% ASTER. 7 rows/day across 4 data_types.

**Cross-reference with BUG-X1 prerequisite section**: ASTER doesn't have `book_snapshot_5` capability per UAC's
`VENUE_DATA_TYPE_CAPABILITIES`. Per the section: "ASTER (no book_snapshot_5 capability) seeded book sentinels anyway,
creating 14 false-miss rows per day." That matches the pattern here perfectly.

**Reading**: these 3220 rows are **stale sentinel artefacts** from before the BUG-X1 fix landed. The Tier-3 sentinel
fan-out was emitting per-instrument rows for capabilities ASTER doesn't have. Pre-write validation correctly rejected
them (no real data → empty parquet → fails Schema Definition contract).

- Severity: **LOW** (already-diagnosed, BUG-X1 fix prevents new ones).
- Action: leave in place; FIX-6 manifest rebuild will overwrite them.

### PREDICTION recon DONE (2026-05-05 21:05)

```
matched (manifest+disk both have it): 2,804
PHANTOMS (manifest captured, disk empty): 420
MISSING ROWS (disk has, manifest doesn't): 26
TRUE GAP DAYS (no capture either way): 1,752 / 2,154 expected days
```

**Reading**:

- 81% of expected days are true gaps (1,752 of 2,154) — entirely consistent with F26: disk starts 2025-03-14, manifest
  tracks back to 2020-06-12 per UAC. The "true gap" days are pre-fetch.
- 420 phantoms — manifest claims captured but disk empty. Sample includes `(2025-03-14, '', '', 'trades')` (BLANK
  venue!) and `(2025-03-13, POLYMARKET, '', 'trades')` (real day-before-launch phantom).
- **26 missing rows** — disk has data, manifest doesn't claim it. These are F30.

### F30 — PREDICTION has a SECOND on-disk layout AND blank-venue phantoms

Two distinct findings from PREDICTION recon:

**(a) Two parallel disk layouts on the same day for prediction**:

```
day=2025-03-27/category=prediction/data_source=POLYMARKET_CLOB/...     (axis-8 deep, ~hundreds of thousands)
day=2025-03-27/category=prediction/venue=POLYMARKET/instrument_type={BTC|ETH|OTHER}/data_type=prediction_trades/ticks_migrated_*.parquet  (canonical with semantic-wrong itype, 26 rows)
```

The second layout uses **`instrument_type=BTC` etc. — but BTC is the underlying asset, NOT the instrument_type**.
Semantically wrong field usage. Files are `_migrated_*` named (2026-04-19 migration). 26 parquets total.

These match my canonical PATH_RE (technically valid hive layout). Manifest doesn't have rows for these tuples because
manifest uses different keys (no per-underlying instrument_type).

Severity: **MEDIUM** — 26 small-volume parquets, but indicates a migration step that put underlyings into the itype slot
and never reconciled with manifest.

**(b) Blank-venue manifest phantoms**:

```
sample phantoms: ('2025-03-14', '', '', 'trades') — venue is BLANK string, not 'POLYMARKET'
                 ('2025-03-14', 'POLYMARKET', '', '') — data_type is BLANK
                 ('2025-03-14', 'UNKNOWN', '', 'trades') — venue literally 'UNKNOWN'
```

Manifest has rows with empty venue, empty data_type, and venue literal `UNKNOWN`. These are **schema-validation failures
or pre-write sentinel rows that leaked into manifest**. Probably the BUG-X1 / BUG-X2 cluster extension to PREDICTION.

Severity: **LOW-MEDIUM** — small population (≤20 rows), but confirms the sentinel-row leak pattern is cross-AG, not just
CeFi.

### F29 — UTL `rebuild_manifest_from_canonical_paths` skips `_migrated_*` files

Found in `unified-trading-library/unified_trading_library/manifest_writer.py:2905`:

```python
if not name.endswith(".parquet") or "_migrated_" in name:
    continue
```

The `_migrated_*` exclusion was likely added to avoid double-counting during the 2026-04-18 migration that created files
with names like `ticks_migrated_20260418T132205Z.parquet`. But many of these files are the only copy of the data (the
migration didn't delete the source — it only copied + renamed).

Combined with F16: the DeFi `venue=AAVE_V3-ETHEREUM/ticks_migrated_*.parquet` files are real data on disk. UTL rebuild
silently drops them.

**Severity**: HIGH — UTL rebuild will under-count DeFi by ~5-7% (the F16 axis-6 venue-overload population, all named
`_migrated_*`).

Action: review the `_migrated_*` filter condition. Either:

1. Remove the filter (treat migrated files as canonical disk truth).
2. Match `_migrated_*` only when there's a non-migrated sibling (i.e. dedup not exclude).

Logged for FIX-6 design — do NOT run rebuild before resolving this.

### Other UTL rebuild gaps surfaced during audit

`rebuild_manifest_from_canonical_paths` requires both `day=` and `venue=` segments to match (regex `.search`). Won't
match:

- **Axis 11 (sports pre-pre-old)** — has neither `category=` nor `venue=`. Silently skipped.
- **F25 (TRADFI dash format)** — uses `day-` not `day=`. day_pat regex fails.

For full rebuild correctness, UTL helper needs the same PATH_RE_VARIANTS that recon now uses. Logged in FIX-6 design.

### F28 — SPORTS pre-pre-old path layout (axis 11)

Discovered when sports legacy-paths re-run after FIX-12 still reported 3,818 unknowns. Sample:

```
raw_tick_data/by_date/day=2022-03-07/source=ODDS_API/league=LA_LIGA/ticks.parquet
                                     ^^^^^^^                  ^^^^^^
                                     no category=/asset_group= no venue=
```

NO `category=`/`asset_group=` segment, NO `venue=` segment. Just `source=` and `league=`. Earliest sports adapter
version, predates the hive-vocab introduction.

Sports now has **4 distinct disk layouts** coexisting:

- axis-4 (empty instrument_type, no league)
- axis-9 (8-segment per-bookmaker per-league)
- axis-10 (old per-league with venue=ODDS_API + empty itype)
- axis-11 (pre-pre-old, no venue, no category)

Severity: **MEDIUM** — adds to layout zoo. FIX-5 design call (Q&A 1) needs to address all 4 sports shapes. Action: added
to audit_legacy_paths.py axis-11 (commit `c103ec6`); recon comparison logic needs same axis-11 pattern if we want full
sports recon coverage.

### F27 — SPORTS has 603 forward phantoms for dates pre-Jun-06-2020

Recon sample shows `(2020-06-01, ODDS_API, '', 'ODDS')` through `2020-06-05` and similar. Manifest claims captured but
disk has no parquets at those dates (sports raw_tick_data first day is 2020-06-06). UAC
`SPORTS_SOURCE_COVERAGE_START['odds_api'] = 2020-06-06`, so dates BEFORE that should have been clipped out of the
manifest. The 603 phantoms are pre-coverage-start rows the writer somehow emitted anyway.

Severity: **LOW** — small population (603 / 17288 = 3.5%), easy to flip via recon `--commit`. Action: leave for FIX-6
rebuild to overwrite, OR run sports recon with `--commit` to flip these to attempted_failed (mark them honest).

### F26 — PREDICTION coverage_start in UAC vs disk reality

UAC `PREDICTION_SOURCE_COVERAGE_START` declares:

```
POLYMARKET: 2020-06-12
KALSHI: 2021-07-19
MANIFOLD: 2022-01-01
```

But disk has zero PREDICTION raw_tick_data before **2025-03-14**. The manifest agrees — 14,368 of 14,369 rows are on or
after 2025-03-14 (only 1 row at 2025-03-13).

This means the data-status UI is inflating the PREDICTION "missing" count by including 4+ years of pre-fetch days where
data was never captured. The denominator from UAC says we should have data going back to 2020-06-12; reality says we
don't.

Two options:

1. **Update UAC** to reflect actual MTDS backfill start (~2025-03-14 for POLYMARKET).
2. **Document as deferred backfill** — we'll go back to 2020-06-12 later via VM-driven backfills, keep UAC aspirational.

Severity: **MEDIUM** — affects coverage % on UI and Phase 2 backfill scope. Needs Ikenna call.

### F25 — TRADFI has ~100k blobs at NON-HIVE layout with `day-` separator (NEW finding 2026-05-05)

Sampled at TRADFI legacy-paths audit run. 100,698 of ~600k blobs are at:

```
raw_tick_data/by_date/day-2025-11-02/data_type-ohlcv_1m/equities/NYSE/NYSE:EQUITY:ABBV-USD.parquet
                       ^^^         ^^^         ^^^^^^^^^^                     ^
                       dash         dash         no-hive-vocab                colon-separated id
```

Notable shape differences:

- `day-` (dash) instead of `day=` (equals) — not hive-partitioned at all.
- `data_type-` (dash).
- No `category=` / `asset_group=` segment.
- Sub-folders `equities/`, `etf/`, `futures_chain/` instead of `instrument_type=*` hive segment.
- Filename uses colon-separated canonical instrument_id format.

Real files (sampled `NYSE:EQUITY:ABBV-USD.parquet`: 4251 bytes, written 2026-02-17). Active data, not stale.

Hypotheses (refined 2026-05-05 after spot-check):

- **(a) One-off bulk import — confirmed**. Top-level prefixes show only 3 days: `day-2025-11-02`, `day-2025-11-08`,
  `day-2026-01-01`. Each holds ~33k parquets. Storage class is **NEARLINE** (cold storage). Sample creation time:
  2026-02-17 12:49:43Z. Pattern fits a one-time Yahoo Finance / Barchart bulk-import that used an older path convention
  and was never migrated to the canonical hive layout.
- **(b) Not active**: NO new files written since 2026-02-17. Live TradFi adapters (Databento) write canonical hive
  paths.

Severity: **LOW-MEDIUM** — 100k blobs are real but isolated (only 3 days, NEARLINE cold storage). Not blocking audit
progress. Easy to migrate or document-as-archived.

Investigation needed: (i) which adapter writes this? (ii) is the manifest tracking these or are they all phantoms? (iii)
is downstream reading them or ignoring them?

NOT adding a regex pattern to recon/audit yet — needs Ikenna's input on whether to:

- Treat as legacy and migrate to hive layout.
- Add a third path-shape variant for active multi-source TradFi.

### F23 — SPORTS uses 8-segment path layout (NEW axis discovered 2026-05-05)

```
raw_tick_data/by_date/day=2024-06-15/
  category=sports/
  data_source=ODDS_API/
  venue=BETFAIR_EX_EU/
  league_id=J1_LEAGUE/
  instrument_type=odds/
  data_type=trades/
  ticks.parquet
```

8 segments. Audit-legacy reported 20,876 of 20,876 sports blobs as UNKNOWN axis. Sports adapter is emitting
`data_source=` AND `league_id=` segments between venue and instrument_type.

- Severity: **CRITICAL** — entire SPORTS raw_tick_data layer is invisible.
- Fix: added `_SPORTS_LEAGUE_PATH_RE` to recon variants. After fix: SPORTS 1-day smoke went from 1 matched / 0 phantom
  to 23 matched / 0 phantom (full per-bookmaker per-league bundles now visible).

### F20 — DeFi manifest-vs-disk venue-keying mismatch (CRITICAL)

Surfaced by smoke run of patched recon on DEFI 2024-06-15:

- Manifest claims (sample, 20 phantoms): `('2024-06-15', 'AAVE_V3', 'a_token', 'oracle_prices')`,
  `('2024-06-15', 'CURVE', 'pool', 'dex_pool_state')`, etc. — **canonical split** form (venue=PROTOCOL, instrument_type
  populated, data_type populated).
- Disk truth (sample, 8 missing-rows): `('2024-06-15', 'AAVE_V3-ETHEREUM', '', '')`,
  `('2024-06-15', 'CURVE-ETHEREUM', '', '')`, etc. — **overload** form (venue=PROTOCOL-CHAIN, no instrument_type, no
  data_type).

**The manifest writer and the on-disk path writer disagree about how to identify a DeFi shard.**

This is fundamentally different from the path-shape axes:

- Path-shape axes are about WHERE the file lives.
- F20 is about HOW the shard is keyed in the manifest.

A canonical-form manifest claim CANNOT match an overload-form disk row by tuple equality — the venue, instrument_type,
data_type columns all differ. This means even after FIX-3+4 made both forms VISIBLE to recon, the comparison stage still
produces "phantom" + "missing" pairs for the SAME logical shard.

- Severity: **CRITICAL** — DeFi manifest has 313k captured rows (per F6 structural check); if the writer-vs-disk key
  mismatch is universal, the entire DeFi manifest is unreconcilable until normalised.
- Fix candidate: add a `_normalise_defi_shard_key(venue, instrument_type, data_type) -> tuple` helper that collapses
  both forms to a canonical key. Applied symmetrically to manifest rows and disk rows before comparison. The "right"
  form depends on which side we declare canonical (see fix-5 design decision).

### F6 closure — DeFi recorder wiring is correct

After investigation: every DeFi handler (bridge, dex_pools, dex_swaps, eigenlayer_rewards, evm_defi, flash_loan_events,
gas_fee, governance_events, lending_indices, liquidation_events, liquidations, lst_rates, mev_events, oracle_prices,
perp_funding, position_data, solana_defi, staking_yields, token_transfers, vault_share_price) uses
`DefiManifestRecorder` and calls all three of `record_captured` / `record_empty` / `record_failed`. The recorder
delegates to `ManifestWriter._record_status` correctly.

The 0% `attempted_failed` count for DeFi is real: DeFi adapters genuinely don't fail at scale (RPC + TheGraph are
robust, plus orchestrator pre-skip clips most pre-launch dates as `empty_confirmed`). Combined with F16 (DeFi paths
non-canonical), there's a subtler concern: DeFi rows might be written to manifest under a different key shape than the
disk layout, but the recorder code path looks structurally correct.

**Status**: closed as **observation**, not bug. Could reopen if a DeFi VM run shows manifest writes succeeding for
captured shards but failing silently for the failure path — needs runtime telemetry, not static analysis.

## Fix manifest (live tracking — landed + pending)

| #       | Fix                                                                            | Repo                                                  | File                                                                      | Drift axis closed             | Commit    | Status                                    |
| ------- | ------------------------------------------------------------------------------ | ----------------------------------------------------- | ------------------------------------------------------------------------- | ----------------------------- | --------- | ----------------------------------------- |
| FIX-1   | Per-day prefix listing in recon (~100x speedup)                                | market-tick-data-service                              | scripts/reconcile_market_tick_manifest.py                                 | enables laptop audit          | `24b38ed` | LANDED                                    |
| FIX-2   | Add SPORTS to ASSET_GROUP_BUCKETS                                              | market-tick-data-service                              | scripts/reconcile_market_tick_manifest.py                                 | F15                           | `9005917` | LANDED                                    |
| FIX-3   | Recon PATH_RE supports DeFi venue-overload layout (no itype/dtype segments)    | market-tick-data-service                              | scripts/reconcile_market_tick_manifest.py                                 | F16                           | `6b1a2f5` | LANDED                                    |
| FIX-4   | Recon PATH_RE accepts `instrument_type=` empty segment                         | market-tick-data-service                              | scripts/reconcile_market_tick_manifest.py                                 | F17                           | `6b1a2f5` | LANDED                                    |
| F18-fix | Recon handles schema-v4 manifests (no capture_status column)                   | market-tick-data-service                              | scripts/reconcile_market_tick_manifest.py                                 | F18                           | `6b1a2f5` | LANDED                                    |
| FIX-5   | Sports/DeFi disk-layout migration vs reader-side multi-layout — DESIGN call    | TBD (UTL writer or MTDS adapters or migration script) | TBD                                                                       | F16, F17, F19, F20 root cause | —         | DESIGN                                    |
| FIX-7   | Case-insensitive comparison in recon (data_type + instrument_type)             | market-tick-data-service                              | scripts/reconcile_market_tick_manifest.py                                 | F19                           | —         | NEXT                                      |
| FIX-8   | DeFi venue-key normaliser in recon (collapse overload+canonical to common key) | market-tick-data-service                              | scripts/reconcile_market_tick_manifest.py                                 | F20                           | —         | NEXT                                      |
| FIX-9   | Add SPORTS axis-9 + PREDICTION axis-8 path layouts to recon + audit            | market-tick-data-service                              | scripts/reconcile_market_tick_manifest.py + scripts/audit_legacy_paths.py | F22, F23                      | `e096185` | LANDED                                    |
| FIX-10  | audit_legacy_paths: scope to raw_tick_data/ prefix (skip processed_candles)    | market-tick-data-service                              | scripts/audit_legacy_paths.py                                             | scope correctness             | `b159b1b` | LANDED                                    |
| FIX-6   | Manifest rebuild for sports/prediction (v4 → v6)                               | market-tick-data-service                              | scripts/rebuild_mtds_manifest.py                                          | F1, F7, F14                   | —         | PENDING (after full audit)                |
| (skip)  | F6 DeFi 0% attempted_failed                                                    | —                                                     | —                                                                         | —                             | —         | CLOSED — wiring correct, observation only |
| (TBD)   | Schema-validation reject breakdown by (venue, data_type)                       | market-tick-data-service                              | analysis                                                                  | F11                           | —         | INVESTIGATING                             |
| (TBD)   | Stale test-bucket retirement                                                   | deployment-service                                    | scripts/cleanup-test-buckets.sh                                           | F4, F5                        | —         | PENDING                                   |
| (TBD)   | F3 disambiguation (rebuild signature vs real bug)                              | tooling                                               | analysis script                                                           | F3                            | —         | PENDING                                   |

## Critical insight (2026-05-05 19:50 IST audit reveals)

**Ikenna's 2026-05-05 hypothesis is confirmed.** Data exists on disk, but manifest+UI can't see it because:

1. **DeFi (F16)**: disk uses `venue=PROTOCOL-CHAIN` venue-overload + NO `instrument_type=` / `data_type=` segments. The
   2026-04-18 migration tagged files as `_migrated_<TS>` but didn't restructure the path layout.
2. **Sports (F17)**: disk uses `category=sports` (legacy hive vocab) AND `instrument_type=` literal-empty.
3. **Prediction (F14)**: schema-v4 manifest rows persist with empty `instrument_type` claiming captured.
4. **All AGs (F3)**: 53-82% of manifest rows have written_at 365+ days after data date — the 2026-04 migrations ran but
   did NOT canonicalise everything.

**This is exactly the failure mode "the manifest can't read its own canonical layout because writers and readers have
diverged"**. Re-running backfill VMs would burn quota fetching data that's already on disk at non-canonical paths. **The
fix is path-layout reconciliation, not redownload.**

Net plan now has 3 prongs:

- **Audit tooling** (FIX-3/4): teach recon to find data at all known disk shapes.
- **Disk reconciliation** (FIX-5): either move data to canonical paths OR teach all readers (manifest, UI, downstream
  services) to handle multiple layouts. Decision: **teach readers** because moving 313k DeFi parquets is expensive.
- **Manifest rebuild** (FIX-6): once readers accept all shapes, rebuild manifest from disk truth so capture_status is
  honest.

## Post-audit summary (will be filled in once full-range recons complete — partial now)

### Discovered + closed (no longer blockers)

- **F1, F7**: schema-v4 manifests for sports/prediction → fix is FIX-6 manifest rebuild.
- **F2**: TRADFI 23% v4 → fix is FIX-6 rebuild.
- **F3**: 53-82% rows have written_at lag — disambiguated as benign rebuild signature.
- **F4, F5**: stale test buckets — confirm + retire later.
- **F6**: DeFi 0% attempted_failed — observation, recorder wiring is correct.
- **F8, F8'**: per-VM shard backlogs — within tolerance.
- **F9**: 1 stuck per-VM shard sports — likely consolidator can't merge v4; will resolve when v4→v6 rebuild lands.
- **F10**: 29k Tardis transport-error leakage — BUG-X2 fix prevents new ones; rebuild overwrites old.
- **F11/F11-detail**: 3,220 ASTER schema-validation rejects = BUG-X1 stale sentinels.
- **F12**: 7k CSV-parse-error leakage — BUG-X2 fix.
- **F13**: TRADFI recon-flipped phantoms — expected, recon working correctly.
- **F14**: PREDICTION axis-4 phantoms — closed by FIX-12.
- **F15**: SPORTS missing from recon dict → fixed by FIX-2 (commit `9005917`).
- **F16, F17, F22, F23, F24**: path-shape drifts → fixed by FIX-3, FIX-4, FIX-9, FIX-10 (recon variants).
- **F18**: recon crashed on schema-v4 manifests → fixed.
- **F19**: case-mismatch on data_type → fixed by FIX-7.
- **F20**: DeFi venue-key mismatch → fixed by FIX-8 normaliser (recon-side compromise; FIX-5 design pending).
- **F21**: DeFi vault_share_price residual phantoms → recon bug, fixed by FIX-11.

### Open (need Ikenna call)

- **F25**: TRADFI ~100k blobs at non-hive `day-data_type-` layout → migrate vs add-pattern (Q&A 7).
- **F26**: PREDICTION coverage_start (UAC says 2020-06-12, disk has 2025-03-14+) → update UAC vs deferred backfill (Q&A
  9).
- **FIX-5 design call**: disk migration vs reader-side multi-layout vs canonical+suffix (Q&A 1).
- **FIX-6 design call**: rebuild scope/order, error_reason preservation (Q&A 2 + design section below).

### Empty-itype-captured-rows per AG (the v4 schema residue)

These are manifest rows with `capture_status='captured'` AND `instrument_type=''`. They cause phantom noise in recon
comparison because disk has proper `instrument_type=spot_pair` etc. — manifest tuple keyed at empty itype, disk keyed at
populated itype, no match.

| AG         | Total manifest rows | Empty-itype captured | % v4-residue |
| ---------- | ------------------- | -------------------- | ------------ |
| CEFI       | 2,229,282           | 13,046               | 0.6%         |
| TRADFI     | 73,316              | 5,545                | 7.6%         |
| DEFI       | 313,365             | 169                  | 0.05%        |
| SPORTS     | 21,055              | **17,289**           | **82%**      |
| PREDICTION | 14,369              | 433                  | 3.0%         |
| **Total**  | 2,651,387           | **36,482**           | 1.4%         |

**Reading**: Sports is dominantly v4 (F1 confirmed). CEFI's 13k predicted CEFI recon's actual 14k phantoms (F2-CEFI
confirmed). DEFI is clean — only 169 v4-residue rows. PREDICTION + TRADFI are minor.

These rows DON'T need re-fetching. They need either:

- (a) FIX-7 normaliser-side empty-as-wildcard match (recon does this already; data-status UI doesn't).
- (b) FIX-6 manifest rebuild with proper itype reconstructed from disk paths.

### Recon outcome per AG (filled-in)

| AG         | Manifest rows | Disk blobs (raw_tick_data)                                                                                                                                            | Match rate                                                                                      | Forward phantoms                                                   | Missing rows                                          | True gap days                      | Notes                                                                        |
| ---------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------- |
| PREDICTION | 14,369        | 573,451 raw_tick_data + 26 canonical-with-BTC-itype                                                                                                                   | 81% of expected days TRUE GAP (F26)                                                             | 420 (some blank-venue F30b)                                        | 26 (F30a — _migrated_\* second layout)                | 1,752 / 2,154 (pre-fetch)          | Disk starts 2025-03-14 (F26); F30 finds new layout                           |
| SPORTS     | 17,288        | 25,709 raw_tick_data: 15,155 axis-10 + 4,921 axis-9 + 1,815 axis-4 + 3,818 axis-11 unmatched (F28); recon matched 3,649 / phantoms 603 / missing 0 / true-gap 37 days | 86% match                                                                                       | **603** (mostly 2020-06-01..05 — F27)                              | **0**                                                 | 37 (recent — forward-poll lapse)   | 100% v4 manifest (F1); 4 distinct disk layouts (axis-4/9/10/11)              |
| TRADFI     | 73,316        | 1,786,848 raw_tick_data: 1,478,899 canonical + 206,141 axis-4 + 101,808 F25 dash                                                                                      | matched=21,424 (29% of manifest)                                                                | **5,562** (empty-itype v4 mix — F2-TRADFI)                         | 1,735 (disk-has-canonical, manifest-has-v4)           | 368/2682 (13.7%)                   | F25 dash + axis-4 disk-side both present. Migration scripts exist (Q&A 10)   |
| DEFI       | 313,365       | 312k canonical + 5,332 axis-6                                                                                                                                         | matched=21,487 (~7% of manifest, but DEFI manifest tracks per-instrument while disk is bundled) | **0**                                                              | 278                                                   | 1,295 / 2,317                      | F16 → 1.7% legacy. Missing rows include UNISWAP_V4-ETHEREUM with empty itype |
| CEFI       | 2,226,631     | 1,224,121 raw_tick_data (1,217,195 canonical / 65,066 unique tuples)                                                                                                  | 99.4% disk match                                                                                | **14,131** (mostly empty-itype empty-dtype v4 — F2-CEFI confirmed) | 452 (BITFINEX/KRAKEN-FUTURES — manifest didn't track) | 89/2682 (3.3% — CEFI well-covered) | Mostly canonical; 14k phantoms = v4 schema mix predicted                     |

### F27 — SPORTS has 603 forward phantoms for dates pre-Jun-06-2020

Recon sample shows `(2020-06-01, ODDS_API, '', 'ODDS')` through `2020-06-05` and similar. Manifest claims captured but
disk has no parquets at those dates (sports raw_tick_data first day is 2020-06-06). UAC
`SPORTS_SOURCE_COVERAGE_START['odds_api'] = 2020-06-06`, so dates BEFORE that should have been clipped out of the
manifest. The 603 phantoms are pre-coverage-start rows the writer somehow emitted anyway.

Severity: **LOW** — small population (603 / 17288 = 3.5%), easy to flip via recon `--commit`. Action: leave for FIX-6
rebuild to overwrite, OR run sports recon with `--commit` to flip these to attempted_failed (mark them honest).

## MAJOR DISCOVERY (2026-05-05 21:15) — disk migration scripts already exist!

While waiting for TRADFI recon, fetched MTDS and discovered FOUR canonical migration scripts already in the repo (since
2026-04-18, `78657fd`):

```
market_tick_data_service/scripts/migrate_sports_canonical.py        — sports OLD per-league → 8-segment
market_tick_data_service/scripts/migrate_polymarket_canonical.py    — Polymarket adapter changes + path
market_tick_data_service/scripts/migrate_tradfi_canonical.py        — F25 hyphen → equals rewrite
market_tick_data_service/scripts/migrate_defi_canonical.py          — DeFi venue-overload split
```

Plus `launch-canonical-migration-vm.sh` already supports `prediction`, `sports`, `tradfi`, `defi`, and `all` flags.

**This changes the FIX-5 design call entirely.** Option A (disk migration) infrastructure is already built — Ikenna's
team has been preparing for this. Latest sports migration commit was today (`ce9b069`, 2026-05-05), suggesting these
scripts are being prepped for production execution.

### Implication for FIX-5

The design conversation shifts from "do we migrate or not?" to "have these migrations been RUN against production
buckets?":

- If **NO**: schedule the run. The audit findings F16/F17/F22/F23/F24/F25 will all collapse once these migrations
  execute. Most of the layout zoo evaporates.
- If **PARTIALLY** (e.g. sports migrated but tradfi pending): document which buckets are clean and which aren't. Run the
  remaining ones.
- If **YES**: the legacy paths the audit found are residual leftovers — the migrations didn't catch every blob.
  Investigate why.

Audit evidence suggests **migrations have NOT been run yet at scale**:

- F16: 5,332 axis-6 venue-overload blobs still on disk in DeFi (would be 0 if migrated).
- F17/F23/F24: ~25k sports blobs at 4 different shapes (would converge to canonical if migrated).
- F22: 573k prediction axis-8 deep blobs on disk (would be canonical if migrated).
- F25: 100k TRADFI dash-format blobs (would be canonical if migrated).

Recommendation: **prioritise running these existing migration scripts** over implementing FIX-5 Option B (reader-side
multi-layout). Talk to Ikenna about scheduling the migrations. They're a one-time cost; FIX-5 Option B is permanent
reader-side complexity.

Documented as Q&A item 10.

## FIX-6 design — manifest rebuild approach (after FIX-7+8+11+12 + reader updates)

After Option B (reader-side multi-layout) lands, the manifest should be rebuilt from disk truth so that `capture_status`
is honest for every shard.

### Existing rebuild infrastructure

`market-tick-data-service/scripts/rebuild_mtds_manifest.py` already exists. It:

- Lists `raw_tick_data/by_date/` per AG
- Parses `(date, venue, instrument_type, data_type)` from canonical paths
- Writes a per-VM shard with `capture_status="captured"` rows
- Consolidator merges within ~60s

### Rebuild script limitations (audit-discovered 2026-05-05)

`rebuild_mtds_manifest.py` does NOT use a regex; it does prefix-walk:

1. List `day=*` prefixes.
2. For each day, list `category=*/venue=*/...` subdirectories.
3. Walk `instrument_type=*/data_type=*/`.

This means it CANNOT discover paths at:

- **F22 (prediction 10-segment)**: uses `data_source=` after `category=`, not `venue=`.
- **F23 (sports 8-segment)**: same `data_source=` first.
- **F25 (TRADFI dash format)**: uses `day-` not `day=`, so the first `list_blobs(prefix="day=")` misses these 100k blobs
  entirely (NEARLINE storage, one-off bulk import — see F25).
- **F28 (sports pre-pre-old)**: uses `source=` directly under `day=`, no `category=` segment.

So FIX-6 manifest rebuild as currently written **will NOT cover sports / prediction / TRADFI-dash properly**. Two paths:

**(a) Rewrite rebuild_mtds_manifest.py to use PATH_RE_VARIANTS like recon does** — list every parquet under
`raw_tick_data/by_date/`, regex-classify, emit per-axis. Slower because no early-pruning but more correct.

**(b) Add per-AG specialised walkers** — keep the prefix-walk for canonical/CeFi/TradFi, add separate prefix walkers for
prediction (`data_source=*`), sports (multiple), TRADFI-dash (skip — leave for archive).

Recommended: **(a)**. The regex-classify approach already works in recon; reuse it. The prefix-walk optimisation matters
less here since rebuilds are batch jobs, not interactive.

### What needs to change for FIX-6

The existing rebuild script uses **only canonical PATH_RE** — same root cause as the recon issues we just fixed. For
FIX-6 to land correctly:

1. **Update rebuild_mtds_manifest.py** to use the same `PATH_RE_VARIANTS` list as recon (adapter would be to expose it
   as a shared module, but for now copy-paste is acceptable per workspace rules — small surface, single reader, easy to
   keep in sync).
2. **Decide instrument_type/data_type mapping for non-canonical paths**:
   - axis-6 (DeFi venue-overload, no itype/dtype on disk): rebuild has no info to fill these. Either drop the row or
     leave itype/dtype empty. Empty matches the existing manifest shape for these venues; recommended.
   - axis-9 (sports new): full info available, populate canonically.
   - axis-10 (sports old per-league): no instrument_type info on disk; populate empty. The `league` segment becomes
     `league_id` column.
   - axis-8 (prediction deep): full info, populate canonically.
3. **Run rebuild PER AG with `MANIFEST_PER_VM_SHARDS=true`** to avoid CAS contention with the consolidator.
4. **Force-merge** after each rebuild via `python -m unified_trading_library.manifest_consolidator --bucket ...`.
5. **Re-run recon** to confirm phantom + missing-row counts drop to <1%.

### Rebuild order (smallest first to validate)

1. PREDICTION — only ~14k existing manifest rows + ~250k disk blobs at axis-8. Smallest impact.
2. SPORTS — ~17k manifest + ~21k disk at axis-9/10/4. Sports manifest is 100% schema-v4 → rebuild lifts it to v6.
3. DEFI — ~313k manifest + ~317k disk. Mostly canonical, ~5k axis-6 overload.
4. TRADFI — ~72k manifest + ~600k disk + ~100k axis-F25. Need F25 disposition first (Q&A 7).
5. CEFI — ~2.2M manifest + ~600k+ disk per CEFI. Largest. Save for last.

### Risks

- **Loss of error_reason** — rebuild from disk truth doesn't know historical failures. Existing `attempted_failed` rows
  from BUG-X1 / BUG-X2 / Tardis transport errors get overwritten with `captured`. We LOSE the failure history. Option:
  rebuild only writes `captured` rows; leave `attempted_failed` rows untouched. The reader-side merge handles the union.
- **Rebuild capacity vs disk reality** — rebuild can only emit what's on disk. If disk is missing genuine days (e.g.
  PREDICTION pre-2025-03-14 per F26), rebuild won't fix that. Those still need a fetch backfill.
- **Consolidator races** — must use `MANIFEST_PER_VM_SHARDS=true` per UTL/SSOT or `manifest_consolidator` will drop our
  writes (see prior 2026-05-02 incident: 80k rows lost during a rebuild without per_vm shards).

## FIX-5 — disk migration to canonical + writer lock to UAC SSOT (Option A, Q&A-confirmed 2026-05-05)

The audit found **6 distinct on-disk path shapes** for raw_tick_data across the 5 asset groups, all coexisting:

| Axis                          | Layout                                                                                           | AGs affected       | Rough rows                            | Status of writers       |
| ----------------------------- | ------------------------------------------------------------------------------------------------ | ------------------ | ------------------------------------- | ----------------------- |
| 1 (canonical)                 | `raw_tick_data/by_date/asset_group=*/venue=*/instrument_type=*/data_type=*/day=YYYY-MM-DD/...`   | all 5 (target)     | majority of CeFi/TradFi               | current SSOT shape      |
| 2 (rogue root)                | `day=*/...` (no `raw_tick_data/by_date/` prefix)                                                 | DeFi (historical)  | should be 0 post 2026-04-18 migration | migration script exists |
| 4/17 (empty itype)            | `instrument_type=/data_type=*/...`                                                               | sports OLD adapter | minor                                 | adapter retired?        |
| 6/16 (defi venue overload)    | `venue=PROTOCOL-CHAIN/<file>.parquet` (no itype/dtype)                                           | DeFi               | ~313k manifest rows                   | live writer             |
| 8/22 (prediction 10-segment)  | `data_source/venue/chain/market_category/underlying/market_type/resolution_period/data_type/...` | PREDICTION         | ~99% of raw_tick_data                 | live writer             |
| 9/23 (sports 8-segment)       | `data_source/venue/league_id/instrument_type/data_type/...`                                      | SPORTS new         | ~91 sample blobs                      | live writer             |
| 10/24 (sports old per-league) | `venue=ODDS_API/instrument_type=/data_type=*/league=*/...`                                       | SPORTS old         | ~99% of raw_tick_data                 | adapter retired?        |

**Decision (2026-05-05 Q&A confirmed): Option A — disk migration to canonical + writer lock to UAC SSOT.**

Rejected alternatives (kept here as the audit trail):

- **Option B (reader-side multi-layout)** would have left writers free to keep producing variant shapes — reader
  complexity grows unbounded with every adapter drift. Violates one-location SSOT. Audit-script polish cannot substitute
  for a single canonical write path.
- **Option C (canonical 4-segment + flexible suffix)** still requires one-time migration to populate the canonical
  prefix on every parquet, and still needs writers to be locked to the new shape. Adding a per-AG suffix dimension
  doesn't materially reduce the migration cost; we'd still pay it AND keep some layout drift in the suffix space.

### Why Option A is achievable now (not a multi-week project)

Migration scripts already exist in MTDS — discovery surfaced this 2026-05-05:

- `market_tick_data_service/scripts/migrate_defi_canonical.py`
- `market_tick_data_service/scripts/migrate_sports_canonical.py`
- `market_tick_data_service/scripts/migrate_polymarket_canonical.py`
- `market_tick_data_service/scripts/migrate_tradfi_canonical.py` — F25 hyphen → equals rewrite
- `market_tick_data_service/scripts/migrate_rogue_root_to_raw_tick_data.py` (proof: 604 of 604 DeFi rogue parquets
  relocated server-side 2026-05-02 with 0 failures, captured in project memory
  `project_partition_path_full_prefix_2026_05_02.md`).
- `instruments-service/scripts/migrate_rogue_root_to_raw_tick_data.py` for cefi (proof: 2,314 rogue day folders + 75
  residual parquets relocated via `gsutil mv` 2026-05-04, captured in `feedback_phantom_audit_five_drift_axes.md`).

The launcher `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` already supports
`--asset-group prediction|sports|tradfi|defi|all`. Migration is a one-time GCS list+server-side-copy cost — bounded by
disk-size of each AG, NOT by API quota.

UAC `build_*_partition_path` already returns the FULL bucket-relative canonical prefix (post-2026-05-02
`partition_path_full_prefix` work — UAC commits `77abd56` + MTDS `2a479ef` + instruments-service `df36829`). Writers
just need to consume `from unified_api_contracts.market import build_cefi_partition_path` etc. — no new SSOT to build.

### Phase 1.5 sub-section — Disk migrate + writer lock-down (replaces deferred decision)

The work splits into three SEQUENTIAL sub-steps. Each AG runs through all three before that AG's Phase-2 launches.

**Pre-flight (run once, on a same-region GCE VM in `asia-northeast1-c`)**:

- [ ] [HUMAN] P0. Per-AG dry-run of the existing migration scripts to size the work and surface any pre-migration drift
      not yet covered: `bash deployment-service/scripts/vm/launch-canonical-migration-vm.sh --asset-group all --dry-run`
      Reports per-AG: parquets at canonical / parquets at each variant axis / candidates needing copy. Cross-check
      against the F16/F17/F22/F23/F24/F25 row-counts in this plan's "Findings table" so the migration size matches.

**Sub-step (a) — disk-migrate to canonical**:

- [ ] [SCRIPT] P0. Run the migrations per AG (sequential to avoid GCS-write contention on the manifest):
      `bash deployment-service/scripts/vm/launch-canonical-migration-vm.sh --asset-group prediction` →
      `--asset-group sports` → `--asset-group tradfi` → `--asset-group defi` → `--asset-group cefi`. Order: smallest
      first so failures surface quickly without weeks of disk-copy in flight. **Pair every launch with event-stream
      verification** (see CLAUDE.md "no fire-and-forget VM launches"; the migration VMs use the `mtds-migrate-` prefix
      already in `VM_PREFIX_TO_BUCKET`).

**Sub-step (b) — audit returns 0 non-canonical**:

- [ ] [SCRIPT] P0. Per-AG: `python3 market-tick-data-service/scripts/audit_legacy_paths.py --asset-group <AG>` — assert
      axis-counts at non-canonical layouts (axis 6 / 8 / 9 / 10 / 16 / 17 / 22 / 23 / 24 / F25-dash) all drop to 0.
      Anything residual is a migration-script bug — fix the script, re-run, do not paper over with reader-side
      multi-layout.

**Sub-step (c) — writer lock-down to UAC SSOT (one-time enforcement, prevents re-drift)**:

- [ ] [AGENT] P0. Add a QG check: any new MTDS adapter or rebuild script writing a raw-tick parquet path that does NOT
      come from a UAC `build_*_partition_path` call is a QG fail. The check is a `rg -n` for inline path construction
      patterns in `market-tick-data-service/market_tick_data_service/` (excluding tests + scripts/ that already use
      UAC). Pre-audit shows the surfaces are: `market_interface/adapters/{cefi,tradfi,defi,prediction,sports}/*.py` plus
      `engine/orchestrator.py` `PartitionedTickWriter` dispatch (cefi already uses `build_cefi_partition_path`; tradfi +
      prediction emit byte-equivalent paths inline as a known temporary; defi/prediction handlers had double-prepend
      bugs that got fixed by `migrate_defi_canonical.py` precedent). The writer-side cleanup is the forcing function —
      without it, FIX-5 turns into a treadmill.
- [ ] [AGENT] P0. Update `tradfi/tradfi_shared.py` + `defi/*_handler.py` + `prediction/polymarket_*` writers to consume
      `unified_api_contracts.market.build_{tradfi,defi,prediction}_partition_path` directly (drop the inline
      byte-equivalent code paths). Mirror the cefi pattern. Add a unit test per writer asserting the emitted path
      matches `build_*_partition_path` output for a fixed input.
- [ ] [AGENT] P0. Once (a)+(b)+(c) green, delete the migration scripts from MTDS `scripts/` (they were one-shot tools;
      keeping them around invites accidental re-runs that write to the legacy shapes again). Document in
      `/codex/02-data/availability-manifest-and-data-status.md` § "Path layout history" as the closure record.

**Why this sequencing**: writer lock-down without disk migration leaves the legacy parquets stranded (correct, they just
stop accumulating new drift). Disk migration without writer lock-down is the treadmill. The audit-loop
`audit_legacy_paths` is the gate between (a) and (c) — it tells us whether the writers really stopped emitting variant
shapes after the lock.

### Cleanup once Option A lands

The audit-script multi-layout reader code in `reconcile_market_tick_manifest.py` (FIX-1 through FIX-12 worked around the
layout zoo) becomes redundant once disk is canonical. Schedule a follow-up to collapse `PATH_RE_VARIANTS` to just the
canonical regex, leaving the legacy variants as a comment-only ledger. Rebuild script's `PATH_RE_VARIANTS` similarly
collapses, closing the FIX-6 rebuild-vs-recon regex-drift gap (F29).

### Findings table (live — fixes pending)

| Axis                      | Description                                                    | Known/New      | AGs affected                                                 | Rows affected   | Severity            | Root-cause repo                            | Fix dependency                  | Status    |
| ------------------------- | -------------------------------------------------------------- | -------------- | ------------------------------------------------------------ | --------------- | ------------------- | ------------------------------------------ | ------------------------------- | --------- |
| Schema-mix                | Manifest v3/v4/v5/v6 mixed; v4 rows can't carry capture_status | known          | sports (100%), prediction (99.5%), tradfi (23%), cefi (0.7%) | ~48k v4 rows    | HIGH                | UTL writer + rebuild scripts               | rebuild per AG                  | DIAGNOSED |
| Late writes               | 53-82% rows have written_at 365+ days after data date          | new (severity) | all 5 AGs                                                    | ~2M rows        | MED (observability) | TBD                                        | Disambiguate vs rebuild_at      | DIAGNOSED |
| Bucket drift              | Two test-bucket name conventions coexist                       | known          | tradfi, defi, cefi                                           | 3 stale buckets | LOW                 | deployment-service / cloud_constants       | retire stale                    | DIAGNOSED |
| DeFi 0% failed            | DeFi has 0 attempted_failed across 313k rows                   | new            | defi                                                         | ~313k           | MED-HI              | MTDS DeFi adapters                         | grep record_failed/empty        | DIAGNOSED |
| Per-VM stuck shard        | Sports 1 unmerged shard                                        | new            | sports                                                       | 1               | MED                 | UTL consolidator                           | check consolidator logs         | DIAGNOSED |
| Per-VM backlog            | CEFI 1,249 shards in queue (1d-7d age)                         | new            | cefi                                                         | 1,249 shards    | LOW                 | UTL consolidator throughput                | investigate                     | DIAGNOSED |
| Tardis transport errors   | 29,513 rows leak `Response payload is not completed`           | new            | cefi                                                         | 29,513          | MED                 | MTDS Tardis adapter (BUG-X2 fixed for new) | rebuild + retry                 | DIAGNOSED |
| Schema validation rejects | StreamingParquetWriter rejected ~3,236 writes                  | new            | cefi (3,220) + tradfi (16)                                   | ~3,236          | MED                 | adapter producing bad rows                 | breakdown by (venue, data_type) | DIAGNOSED |
| CSV parse error leak      | ~7,000 rows leak `In CSV column #N`                            | new            | cefi                                                         | ~7,000          | LOW                 | MTDS CSV parser                            | BUG-X2 patch covers new         | DIAGNOSED |
| Recon-flipped phantoms    | TRADFI 254 phantoms flipped previously                         | none           | tradfi                                                       | 254             | NONE                | recon working                              | —                               | EXPECTED  |

### Findings table (live — fixes pending)

| Axis                  | Description                                                          | Known/New      | AGs affected                                    | Rows affected      | Severity            | Root-cause repo                      | Fix dependency                  | Status    |
| --------------------- | -------------------------------------------------------------------- | -------------- | ----------------------------------------------- | ------------------ | ------------------- | ------------------------------------ | ------------------------------- | --------- |
| Schema-mix            | Manifest holds v3/v4/v5/v6 mixed; v4 rows can't carry capture_status | known          | sports (100%), prediction (99.5%), tradfi (23%) | ~48k v4 rows total | HIGH                | UTL writer + rebuild scripts         | —                               | DIAGNOSED |
| Late writes           | 53-81% of rows have written_at 365+ days after data date             | new (severity) | sports, tradfi, defi                            | ~233k rows         | MED (observability) | TBD                                  | Disambiguate vs rebuild_at      | DIAGNOSED |
| Bucket drift          | Two test-bucket name conventions coexist                             | known          | tradfi, defi                                    | ~3 buckets         | LOW                 | deployment-service / cloud_constants | —                               | DIAGNOSED |
| Empty/Failed accuracy | DeFi has 0 attempted_failed across 313k rows                         | new            | defi                                            | ~313k              | MED-HI              | MTDS DeFi adapters                   | grep record_empty/record_failed | DIAGNOSED |
| Per-VM stuck shard    | Sports has 1 unmerged per-VM shard                                   | new            | sports                                          | 1                  | MED                 | UTL consolidator                     | check consolidator logs         | DIAGNOSED |

## Discovery audit — 2026-05-05+ (the actual current work)

**Why this exists**: Ikenna's 2026-05-05 callout (manifest/UI/GCS three-layer disagreement) + Harsh's instruction to
treat this as a **systematic discovery exercise across the whole MTDS surface** — find every disagreement, not just the
ones we already know about. The phases below (0 → 4) describe an idealised flow; this section captures what we are
actually doing day-by-day.

### Goal

Build a complete picture of where MTDS manifest, MTDS GCS-truth, and MTDS data-status UI disagree across **every**
`(asset_group, venue, data_type, instrument_type)` cell — then fix the underlying writers/readers/schemas/UIs at the
root, then rebuild manifests, then (and only then) launch paid backfills for genuinely-missing data.

### Approach (overview)

1. **Enumerate the audit matrix** — every cell from UAC's
   `VENUES_BY_ASSET_GROUP × DATA_TYPES_BY_ASSET_GROUP × instrument_types`, with a representative instrument per cell.
   Output: a JSON cell list consumed by the audit script.
2. **Build the cell-probe audit script** — for one cell + one date, query the manifest (what API/manifest say), then
   probe GCS at every known legacy path shape (the 8 drift axes), record what's on disk, classify the disagreement.
   **Critically**: flag any path it finds that doesn't match a known axis — that's a _new_ drift axis we don't know
   about.
3. **Smoke the script** on 1-2 cells manually before fanning out, to verify the probing logic.
4. **Fan out 10-15 background agents in parallel** (Opus 4.6 first while we calibrate, then Sonnet/Opus per workload).
   Each agent owns a chunk of cells, runs the audit script per cell × 15 sample dates (5 captured + 5 missing + 5
   attempted_failed), writes CSV findings.
5. **Run 6 cross-cutting structural checks** in parallel: schema-version drift, written_at chronology, bucket name
   drift, per-VM shard staleness, schema-vs-SchemaDefinition parity, empty-vs-failed classification accuracy. These
   catch failure modes that don't show up as per-cell GCS path mismatches.
6. **Aggregate findings here** — drift axes (known + new) with severity, AGs affected, root-cause repo, fix
   dependencies.
7. **Land fixes in dependency order** across UTL / UAC / MTDS / deployment-api / deployment-ui / recon script / rebuild
   scripts. Quickmerge `--agent` per repo. Cross-repo fixes get aligned commits so we don't leave the stack
   half-migrated.
8. **Re-run audit matrix** to confirm inverse-phantom rate <1% per cell and the data-status UI stops lying. Only then
   evaluate genuine gaps and launch paid backfills.

### Background-agent rate-limit hygiene

We're dispatching 10-15 parallel agents. Three rate-limit ceilings to respect:

| Ceiling          | Limit                            | Mitigation                                                                                  |
| ---------------- | -------------------------------- | ------------------------------------------------------------------------------------------- |
| GCS list ops     | ~1000 list_blobs/sec per project | Each agent runs `list_blobs(prefix=...)` not full bucket scans; cap workers per agent at 4. |
| Anthropic API    | per-org tokens/min               | Stagger agent dispatch in waves of 5; Opus 4.6 first wave for calibration, then scale.      |
| Tardis/Databento | paid quotas                      | **Audit phase is read-only against GCS + manifest only — no venue API calls.**              |

Each background-agent prompt includes: the goal of the audit, the 8 known drift axes with provenance, the cell-probe
script path + invocation, the "if you find a new path shape NOT matching any known axis, STOP and report it" rule, and a
write-only-to-CSV-do-not-modify-anything restriction. Agents return CSVs; main session aggregates.

### Registry SSOT cheatsheet (2026-05-05 discovery)

All registries live in UAC + UTL + MTDS. Audit scripts and background agents source from here, never hard-code.

| What                                                                                       | File                                                                                     | Symbol                                                                                                                                    |
| ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Venues per AG                                                                              | `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:155-214` | `VENUES_BY_ASSET_GROUP`                                                                                                                   |
| Data_types per AG                                                                          | `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:96-152`  | `DATA_TYPES_BY_ASSET_GROUP`                                                                                                               |
| Per-venue capability matrix (which data_types each venue actually publishes + start dates) | `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:422-611` | `VENUE_DATA_TYPE_CAPABILITIES`                                                                                                            |
| MVP seed instruments (canonical IDs per (venue, data_type))                                | `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:744-942` | `_SPOT_MVP_SEED_INSTRUMENTS`, `_PERP_MVP_SEED_INSTRUMENTS`, `_OPTION_FUTURE_MVP_SEED_UNDERLYINGS`, `get_expected_instruments_for_venue()` |
| GCS bucket naming                                                                          | `unified-trading-library/unified_trading_library/core/cloud_constants.py:173-212`        | `get_bucket_name(domain, asset_group, project_id)` → `market-data-tick-{ag}-{pid}`                                                        |
| Canonical partition paths                                                                  | `unified-api-contracts/unified_api_contracts/canonical/partition_paths.py`               | `build_cefi_partition_path()`, `build_defi_partition_path()`, `build_tradfi_partition_path()`                                             |
| Hive key SSOT (canonical vs legacy)                                                        | `market-tick-data-service/market_tick_data_service/raw_tick_hive.py`                     | `RAW_TICK_ASSET_GROUP_HIVE_KEY = "asset_group"` (canonical), `..._LEGACY = "category"`                                                    |
| Instrument types per AG                                                                    | `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md:136-142`      | doc table — no code-level enum                                                                                                            |

**Canonical MTDS write path** (from `partition_paths.py`):

```
raw_tick_data/by_date/day={YYYY-MM-DD}/asset_group={AG}/venue={V}/instrument_type={IT}/data_type={DT}/{SYMBOL}.parquet
```

DeFi adds `/chain={C}/` between venue and instrument_type. Chain bundles use `/underlying={U}/ticks.parquet`.

### Finding 1 (DISCOVERY-2): existing recon script already does most of the audit

`market-tick-data-service/scripts/reconcile_market_tick_manifest.py` (343 lines) already implements forward + inverse
phantom detection:

- **Forward phantoms**: manifest says `captured`, no parquet on disk → flips to `attempted_failed`.
- **Missing rows (inverse phantoms)**: parquet on disk, no manifest row → adds `captured` row.
- **True gaps**: neither manifest nor disk has data on a date → real backfill candidate.
- Writes per-VM shard (`MANIFEST_PER_VM_SHARDS=true`-equivalent path) so the consolidator merges correctly.
- `--dry-run` for read-only audit; `--commit` to actually write the per-VM shard.

**What it does NOT do** (the gaps we still need to cover):

The script's `PATH_RE` only matches the canonical layout:

```python
r"raw_tick_data/by_date/day=(?P<day>\d{4}-\d{2}-\d{2})/"
r"(?:category|asset_group)=(?P<ag>[^/]+)/"  # ✅ axis 1: hive vocab handled
r"venue=(?P<venue>[^/]+)/"
r"instrument_type=(?P<itype>[^/]+)/"
r"data_type=(?P<dtype>[^/]+)/"
r"(?:underlying=(?P<underlying>[^/]+)/)?"  # ✅ axis 5: chain bundles handled
r"(?P<filename>[^/]+\.parquet)$"
```

Drift axes the canonical PATH_RE won't catch:

- **Axis 2 (path prefix)**: legacy top-level `day=YYYY-MM-DD/...` (no `raw_tick_data/by_date/` prefix). Per CLAUDE.md,
  UAC `77abd56` + MTDS `2a479ef` standardised this; pre-existing rogue data was supposed to be relocated by
  `instruments-service/scripts/migrate_rogue_root_to_raw_tick_data.py`. **Need to confirm migration completed** for MTDS
  bucket, and probe both shapes if not.
- **Axis 3 (instrument_type casing)**: manifest may hold `PERPETUAL` / `perpetual`; disk only has lowercase. PATH_RE is
  case-sensitive, will only match disk casing. The mismatch is on the manifest side — when `_filter_manifest` filters by
  user-provided `instrument_type`, case mismatches drop the manifest row from the slice. **Need to confirm this
  comparison is case-insensitive or normalize before comparing.**
- **Axis 4 (empty `instrument_type`)**: schema-v4 manifest rows omit the segment. PATH_RE requires `instrument_type=` to
  match. **Manifest rows with empty `instrument_type` will be in `manifest captured` but no disk match exists** (because
  disk paths always have a non-empty segment) → falsely classified as forward phantom.
- **Axis 6 (DeFi venue overload)**: legacy `venue=PROTOCOL-CHAIN/` (no chain= segment). PATH_RE expects canonical
  `venue=PROTOCOL/chain=CHAIN/...` for DeFi. **DeFi-specific finding — need to verify which form on disk.**
- **Axis 7 (DeFi no-asset-group hive segment)**: legacy DeFi paths that omit the AG segment entirely. Canonical PATH_RE
  requires `(?:category|asset_group)=`.
- **Axis 8 (Polymarket 9-segment layout)**: prediction layout has `sub_category=` and `market=` segments PATH_RE doesn't
  expect.

**Approach pivot**: instead of writing a brand-new audit script, run `reconcile_market_tick_manifest.py --dry-run`
across the full matrix AND write a small companion `audit_legacy_paths.py` that probes the 5 missing drift axes (2, 3,
4, 6, 7, 8) on a sample of "missing" rows from the recon output.

**Companion script spec**:

- Input: a sample of `(asset_group, venue, data_type, day)` tuples that the canonical recon flagged as `true_gaps`.
- For each tuple, probe GCS at all 5 missing-axis path shapes.
- Output: per-tuple classification (`legacy_axis_2_top_level_prefix` / `legacy_axis_4_empty_itype` / `genuine_gap`).
- Writes findings to CSV — never modifies anything.

**Other small fixes spotted in `reconcile_market_tick_manifest.py`**:

- Schema version hard-coded as 5 (line 307, 323). Manifest is now v6 (per UTL `manifest_writer.py`
  `MANIFEST_SCHEMA_VERSION = 6`). New rows written by the recon script will be v5 → coexist with v6 rows but miss
  `quote_asset` / `margin_type` / `combo_type` / `leg_weights` columns. **Fix candidate** — bump to 6 and populate the
  new columns where applicable (DERIBIT inverse vs linear esp.).

### Cell enumeration

Total cells (denominator for matrix audit, after `VENUE_DATA_TYPE_CAPABILITIES` filtering):

| AG         | Venues                           | Data_types    | Cells (venue × data_type, capability-filtered)                                         |
| ---------- | -------------------------------- | ------------- | -------------------------------------------------------------------------------------- |
| CEFI       | ~20                              | 6             | ~60-80 (varies — many spot venues lack derivative_ticker/liquidations/options/futures) |
| TRADFI     | ~8                               | 5             | ~30                                                                                    |
| DEFI       | ~30 protocols × ~11 chains       | ~20           | ~150-200 (most protocols only on 1-3 chains)                                           |
| SPORTS     | ~6 bookmakers (per MTDS layer 2) | ~4            | ~20                                                                                    |
| PREDICTION | 2                                | 1 (canonical) | 2                                                                                      |
| **Total**  |                                  |               | **~260-330 cells**                                                                     |

For each cell we audit a sample of 15 dates (5 captured + 5 missing + 5 attempted_failed in the manifest), total ~4-5k
probes. At ~12 prefixes/sec from laptop = ~7 min minimum if perfectly serial, more like 20-30 min parallel. **Will not
need a GCE VM** at this scale — laptop-side is fine.

### Findings table (per drift axis — fill in as audit completes)

| Axis | Description                                       | Known/New | AGs affected | Rows affected (est.) | Severity | Root-cause repo | Fix dependency | Status |
| ---- | ------------------------------------------------- | --------- | ------------ | -------------------- | -------- | --------------- | -------------- | ------ |
| 1    | Hive vocab `category=` ↔ `asset_group=`           | known     | TBD          | TBD                  | TBD      | TBD             | —              | TBD    |
| 2    | Path prefix top-level vs `raw_tick_data/by_date/` | known     | TBD          | TBD                  | TBD      | TBD             | —              | TBD    |
| 3    | `instrument_type` casing                          | known     | TBD          | TBD                  | TBD      | TBD             | —              | TBD    |
| 4    | Empty `instrument_type` (schema-v4 vestige)       | known     | TBD          | TBD                  | TBD      | TBD             | —              | TBD    |
| 5    | Chain-bundle equivalence (option ↔ options_chain) | known     | TBD          | TBD                  | TBD      | TBD             | —              | TBD    |
| 6    | DeFi venue overload `PROTOCOL-CHAIN/` vs split    | known     | DEFI         | TBD                  | TBD      | TBD             | —              | TBD    |
| 7    | DeFi no-asset-group hive segment                  | known     | DEFI         | TBD                  | TBD      | TBD             | —              | TBD    |
| 8    | Polymarket 9-segment layout vs flat               | known     | PREDICTION   | TBD                  | TBD      | TBD             | —              | TBD    |
| 9+   | NEW — discovered during this audit                | new       | TBD          | TBD                  | TBD      | TBD             | TBD            | TBD    |

### Fix manifest (one row per fix that needs to land — fill in as findings drive it)

| #   | Fix                           | Repo | File | Drift axis closed | Commit | PR  | Status |
| --- | ----------------------------- | ---- | ---- | ----------------- | ------ | --- | ------ |
| —   | (TBD — populated after audit) |      |      |                   |        |     |        |

### Background-agent dispatch log

| Wave | Time (UTC)                                 | Agents | AGs/venues covered | Model | Result | Notes |
| ---- | ------------------------------------------ | ------ | ------------------ | ----- | ------ | ----- |
| —    | (TBD — populated as agents are dispatched) |        |                    |       |        |       |

### Cross-cutting structural checks

| #   | Check                                                      | Status | Output / finding |
| --- | ---------------------------------------------------------- | ------ | ---------------- |
| 1   | Schema-version distribution per AG                         | TBD    |                  |
| 2   | `written_at` chronology vs GCS object creation             | TBD    |                  |
| 3   | Bucket name drift (manifest references vs `gsutil ls`)     | TBD    |                  |
| 4   | Per-VM shard staleness (`_index/per_vm/*.parquet` backlog) | TBD    |                  |
| 5   | Schema columns vs registered SchemaDefinition parity       | TBD    |                  |
| 6   | empty_confirmed/attempted_failed classification accuracy   | TBD    |                  |

### Commit cadence

Every natural milestone gets a commit + push to `live-defi-rollout`. Targets in order:

- [ ] Plan restructure (this commit) — `chore: restructure MTDS plan as live-ops surface for discovery audit`
- [ ] Audit cell enumeration JSON written + script committed
- [ ] First wave of agent findings aggregated into Findings table
- [ ] Each drift-axis fix lands as its own commit/PR
- [ ] Final audit re-run + sign-off commit

PM repo doc-only fast-path: plan changes target `main` directly (per workspace CLAUDE.md PM/Codex doc-only fast-path).

---

## Context

Sibling plan to [`instruments_to_100pct_eod_2026_05_04.md`](instruments_to_100pct_eod_2026_05_04.md). Same shape,
different service.

- **Service**: `market-tick-data-service` only — raw tick downloads. Not instruments-service (covered by sibling), not
  market-data-processing-service (downstream candle generation, separate plan).
- **Asset groups**: all five — `cefi`, `tradfi`, `sports`, `prediction`, `defi`.
- **Target**: ≥99% `captured + empty_confirmed` for `service=market-tick-data-service` under the secondary-cutoff
  denominator. "Honest" means manifest row in `{captured, empty_confirmed}` AND parquet present at the canonical GCS
  path.
- **Batch only.** Live forward-poll is the next milestone (out of scope here). Forward-poll launchers are referenced for
  context but not driven from this plan.
- **Non-goals (this plan)**: instruments-service backfill (sibling plan owns it), MDPS candle generation, deployment-ui
  drilldown bug fixes (parent epic Phase 0), feature-service / ML re-runs.

**Why a separate plan**: instruments-service is a prerequisite for MTDS — the universe of instruments per
`(asset_group, venue, day)` is what MTDS iterates over to download ticks. Tracking MTDS as its own plan keeps the
instruments-side pacing visible (sibling plan) and gives MTDS its own EOD-style success criterion. The two plans share
Phase 0 phantom-recon mechanics but write to different buckets:

| Service                  | Manifest path                                                         |
| ------------------------ | --------------------------------------------------------------------- |
| instruments-service      | `gs://instruments-store-{ag}-{pid}/_index/availability_index.parquet` |
| market-tick-data-service | `gs://market-data-tick-{ag}-{pid}/_index/availability_index.parquet`  |

The phantom recon script (`reconcile_phantom_manifest_rows_all.py`) reads the `instruments-store-*` bucket — for MTDS
shards we need a different verification path. See Phase 0 below.

## 2026-05-05 prerequisite — read this before launching any MTDS work

Two compounding orchestrator bugs were diagnosed + fixed during the Phase 2 CeFi gap audit and they materially change
how this plan should be executed. Sibling plan with the full diagnosis:
[`cefi_phase2_gap_audit_2026_05_01.md`](cefi_phase2_gap_audit_2026_05_01.md) § "2026-05-05 fix landed — BUG-X1 +
BUG-X2".

### BUG-X1 — instrument_id vocabulary mismatch (Tier-3 sentinel false-positives)

**Symptom in the manifest**: ~40k DERIBIT + 3k ASTER + 2k BYBIT `attempted_failed` rows on per-instrument data_types
(`trades` / `book_snapshot_5` / `derivative_ticker`) where the `instrument_id` column was the UAC canonical form
(`BTC-PERP`, `ADA-PERP` etc.) and `error_reason` was `"OPTION row requires 'expiry_date'..."`. Pattern was identical
counts across all 10 perps per data_type — a smell that revealed they were sentinel fan-out rows, not real fetch
attempts.

**Root cause**: the orchestrator's `captured_per_instrument_shards` set was populated with the writer's wire-format
symbol (`BTC-PERPETUAL`, `BTCUSDT`, `BTC-USDT-SWAP`, `ADA_USDC-PERPETUAL`, `BTCF0:USTF0`). UAC's MVP seed table
(`_PERP_MVP_SEED_INSTRUMENTS`) emits canonical IDs (`BTC-PERP`). The set-diff at the Tier-3 sentinel comparison never
matched on perp venues — every captured shard re-emitted as a sentinel `attempted_failed` row even on dates where the
data was successfully captured.

**Fix shipped**:

- **MTDS commit `fe5cc2c`** on `live-defi-rollout`: added `_canonicalize_captured_instrument_id(venue, raw_symbol)`
  helper in `market_tick_data_service/engine/orchestrator.py`. Maps wire→canonical at the captured-side write into
  `captured_per_instrument_shards`. Driven by the existing `_VENUE_INSTRUMENT_TYPE` dict so adding a new perp venue
  updates one place. Never mutates the parquet `file_stem` or manifest `instrument_id` column — those keep wire form as
  the immutable downstream-reader contract. 28 unit tests in `tests/unit/test_orchestrator_canonicalize_captured.py`
  lock the per-venue rules. PR #106 (target staging).
- **UAC commit `82d7d50`** on `live-defi-rollout`: fixed three sub-bugs in `get_expected_instruments_for_venue`'s
  default seed path (`unified_api_contracts/registry/market_data_categories.py`):
  1. `-FUTURES` venues (BITFINEX-FUTURES, BITGET-FUTURES, KRAKEN-FUTURES, OKX-FUTURES) fell through to SPOT branch and
     seeded `BTC-USDT` instead of `BTC-PERP`.
  2. `derivative_ticker` returned PERP seeds unconditionally — even for spot-only venues (BINANCE-SPOT, OKX-SPOT,
     COINBASE-SPOT, UPBIT, \*-SPOT) that physically can't publish derivative_ticker.
  3. `trades` / `book_snapshot_5` ignored the venue's `VENUE_DATA_TYPE_CAPABILITIES` entry — ASTER (no `book_snapshot_5`
     capability) seeded book sentinels anyway, creating 14 false-miss rows per day. All three closed by consulting
     `VENUE_DATA_TYPE_CAPABILITIES` as the SSOT before emitting any seed. PR #44 (target staging). 5 new tests under
     `TestSeedDispatcherVenueClassification`.

### BUG-X2 — venue-level error fanned out as if per-instrument (manifest lying)

**Symptom**: a single row in a Tardis bundle missing `expiry_date` raised `ValueError`, the exception was caught at the
venue level (`failed_shards[venue] = "OPTION row requires..."`), and the Tier-3 sentinel stamped that 80-char exception
text onto **every** per-instrument sentinel row for that (venue, date, dt). Made it look like every perp failed schema
validation when in fact one option row in the bundle did. Same pattern in the sports Tier-2 fan-out.

**Fix shipped**: MTDS commit `fe5cc2c` (same commit as X1). When `classify_venue_error` cannot bucket the exception, the
sentinel writes the generic code `VENUE_FETCH_FAILED` instead of leaking exception text. Descriptive message stays in
logs; manifest stops lying. Applied symmetrically to the CeFi Tier-3 path and the sports Tier-2 fan-out.

### BUG-X3 — Databento per-schema silent-drop (manifest claimed empty, was attempted-and-failed)

**Symptom**: 1004 (root, date) pairs across MES / BTC / ETH / ES in MTDS manifest carried `capture_status=captured` with
zero ohlcv_1m rows on disk for dates where the bundled `--data-types ohlcv_1m;trades` CME parent symbology run had only
successfully captured `trades`. The manifest looked clean; downstream feature pipelines computed garbage on empty bars;
root not surfaced until hand-inspection of the parquet contents on 2026-05-05.

**Root cause**: in `market_tick_data_service/market_interface/adapters/tradfi/databento_adapter.py`, `download_batch_df`
ran `for data_type in data_types: for dataset in by_dataset:` and the per-schema loop body had two silent-drop branches:

```python
if dbn_store is None:
    continue                                     # silent — no manifest signal
...
except Exception as exc:
    logger.warning("DatabentoAdapter: %s/%s failed: %s", dataset, data_type, exc)
    continue                                     # silent — no manifest signal
```

Concurrent-VM 429 contention on the shared Databento account exhausted the adapter's retry budget for `ohlcv_1m` while
`trades` succeeded. The `continue` masked the failure; the orchestrator's `_fetch_one_venue` saw the call return
successfully with the partial-success `trades` DataFrame and never set `failed_shards[venue]`. The sentinel pass at the
end-of-date pass then iterated `expected_dts` and emitted `record_empty` for the missing `ohlcv_1m` shards (the existing
code path: "venue did not raise → assume empty is genuine").

**Recovery already done**: `/tmp/fill_missing_ohlcv.py` (serial direct-Databento, 0.5s sleep, exp backoff up to 60s
on 429) recovered all 1004 silently-dropped (root, date) pairs → all four roots returned to ≥99% ohlcv_1m coverage.

**Fix shipped (2026-05-05, no longer deferred)**:

- **MTDS** `market_tick_data_service/market_interface/adapters/tradfi/databento_adapter.py`:
  - New `_PerSchemaFailure` dataclass + `_classify_databento_exception()` helper (maps `BentoHttpError.http_status` or
    message text → `429` / `RATE_LIMIT` / `AUTH_FAILURE` / `CONNECTION_RESET` / `NOT_FOUND` / `SERVER_ERROR` /
    `DATABENTO_FETCH_FAILED`).
  - `download_batch_df` accepts a new optional `failed_per_dt: dict[str, str]` out-dict. Each silent-drop branch appends
    a `_PerSchemaFailure`, emits an `ADAPTER_FETCH_FAILED` event with
    `(venue, data_type, dataset, error_code, error_message)` (per CLAUDE.md adapter-error rule), and continues so
    partial successes are preserved. After the per-schema loop, any data_type that ended with zero captured rows AND at
    least one failure is written to `failed_per_dt[dt]` with the most-common error_code.
- **MTDS** `market_tick_data_service/adapters/umi_tick_provider.py`: `fetch_tick_data_for_venue` accepts and threads
  `failed_per_dt` through to `db_adapter.download_batch_df`.
- **MTDS** `market_tick_data_service/engine/orchestrator.py`:
  - `_fetch_one_venue` accepts `failed_per_dt` and threads it through.
  - The per-venue caller builds a `failed_per_dt_by_venue: dict[str, dict[str, str]]` and merges per-venue dicts after
    each `_fetch_one_venue` call. **Partial successes are preserved**: the writer's already-streamed `trades` rows
    survive into `shard_counts` / `captured_dts_here` exactly as before.
  - Sentinel pass: when iterating `expected_dts`, `failed_per_dt_by_venue.get(venue, {}).get(dt)` is checked first; a
    populated entry takes precedence over the venue-wide `failed_reason_raw` so the missing `(venue, data_type)` shard
    lands as `attempted_failed` with the classified code (not `empty_confirmed`).
- **Tests** `tests/market_interface/unit/test_databento_adapter_logic.py::TestDatabentoAdapterPerSchemaFailureSurfacing`
  — 3 cases lock the contract: (a) every dataset attempt 429s → `failed_per_dt = {"ohlcv_1m": "429"}`; (b)
  `_fetch_timeseries_range` returns None → `failed_per_dt = {"ohlcv_1m": "DATABENTO_NULL_RESPONSE"}`; (c) trades
  succeeds + ohlcv_1m 429s → trades captured AND `failed_per_dt = {"ohlcv_1m": "RATE_LIMIT"}`.

This makes the bundled `--data-types ohlcv_1m;trades` CME parent symbology run honest: a 429 on one schema flips the
manifest to `attempted_failed` for that data_type, the deployment-UI gap surfaces immediately, and the next backfill run
targets only the genuinely-missing window.

### What this means for execution of this plan

1. **Do NOT trust the current manifest's `attempted_failed` numbers as ground truth for which shards genuinely failed.**
   A large chunk of the 86k attempted_failed CeFi rows (39k of them — Cluster B `expiry_date` errors) are stale sentinel
   artefacts from the 2026-04-29/30 366-VM rollout, not real per-instrument failures. The corresponding parquets were
   either captured successfully (under wire-form `instrument_id`) or genuinely never attempted. Phase 0.1 inverse-audit
   catches both.
2. **Phase 1.5 manifest rebuild is the right primary tool for these stale rows.** A rebuild walks GCS and re-keys
   manifest rows under canonical IDs (post fix); sentinel scans now correctly suppress duplicates. **Re-attempting
   instead of rebuilding burns Tardis API quota for no benefit.**
3. **VM relaunches must include the fix.** Rebuild tarballs after pulling `live-defi-rollout` head (or `main` once PR
   #106 lands) so launched VMs run with the canonicalize helper. Bare `create-code-tarballs.sh` re-tars CORE only; pass
   `--all` for full coverage of UAC + MTDS changes.
4. **No CeFi venue needs to be excluded.** The capture path was always working — only the manifest accounting was wrong.
   Going forward, captured shards will register correctly against UAC seeds.
5. **ASTER is genuinely stuck.** 0 captured rows of any data_type in the manifest. Unclear whether Tardis has archive
   coverage for ASTER or the wire-symbol format passed by the launcher is wrong. **Investigate before launching ASTER
   VMs**; the X1 fix covers ASTER's vocabulary mismatch but won't help if the upstream archive is genuinely empty.
6. **BUG-X2 fix is incremental data-quality**: existing manifest rows with leaked exception text don't auto-update; new
   venue-level failures will write `VENUE_FETCH_FAILED` instead. Phase 1.5 rebuild will overwrite the stale rows.

### Affected venue list (for cross-reference with Phase 2 launches)

X1 vocabulary mismatch had non-zero blast radius on every per-instrument CeFi venue:

- DERIBIT (perp + linear perp + options chains): wire `BTC-PERPETUAL` / `ADA_USDC-PERPETUAL` etc. → canonical `BTC-PERP`
  / `ADA-PERP`.
- BINANCE-FUTURES, BYBIT, OKX-SWAP, ASTER, HYPERLIQUID: packed/wire forms → `BASE-PERP`.
- BITFINEX-FUTURES (margin pair `BTCF0:USTF0`), BITGET-FUTURES, KRAKEN-FUTURES, OKX-FUTURES: packed → `BASE-PERP`.
- BINANCE-SPOT, COINBASE-SPOT, OKX-SPOT, BITFINEX-SPOT, BITGET-SPOT, KRAKEN-SPOT, UPBIT: packed/dash → canonical
  `BASE-QUOTE`.

After the fix lands, Phase 0.1 inverse-audit per AG will quantify how many of the "missing" rows are X1 stale-sentinel
rows vs genuinely-missing.

### Cross-reference

- Diagnosis + fix detail: [`cefi_phase2_gap_audit_2026_05_01.md`](cefi_phase2_gap_audit_2026_05_01.md) § "2026-05-05 fix
  landed — BUG-X1 + BUG-X2".
- MTDS commit: `fe5cc2c` on `live-defi-rollout` (PR #106 to staging).
- UAC commit: `82d7d50` on `live-defi-rollout` (PR #44 to staging).

## Hard rule before launching ANY backfill: GCS truth check

**Per Ikenna 2026-05-05**: "missing in data-status UI" ≠ "actually missing in GCS". Three independent layers can
disagree, and have all drifted before:

1. **GCS truth** — parquets physically on disk.
2. **Manifest** (`_index/availability_index.parquet`) — schema has been through v3 → v4 → v5 → v6. Older runs may have
   written under older schemas / older path conventions; newer reads may not understand them.
3. **Data-status UI / API** — reads the manifest with its own caching. Built concurrently with the manifest evolving; at
   one point predated the manifest entirely. Caches: `_turbo_cache`, `_INDEX_CACHE`, `_drilldown._cache`,
   `_REF_DATA_CACHE` (5-min TTL).

When any two layers disagree, the UI shows "missing" even though data is on disk. **Re-downloading in that state is
wasted spend.** Cost ladder (most expensive first): Databento, DeFi RPCs (Alchemy/Infura/etc.), Tardis, sports odds-API.
**CeFi (Binance/Bybit/OKX/etc. public) and Prediction (Polymarket/Kalshi) are the only ~free sources** outside VM cost.

**Known drift causes seen before** (expect them again):

- **Hive vocab change** — `category=` (legacy) vs `asset_group=` (post-2026-04 rename) coexist on disk.
- **Bucket / path-prefix change** — top-level `day=*/...` (legacy Tardis writer) vs `raw_tick_data/by_date/day=*/...`
  (post-2026-04 unified writer). UAC `77abd56` + MTDS `2a479ef` standardised this; pre-existing rogue data still on disk
  at the old prefix.
- **Sharding shape change** — options moved from single-file-per-strike to bundled-per-underlying (the 2026-04-30
  combo-bundling migration: ~13M legacy files → ~36k bundled `ticks.parquet`). Old data on disk in old shape; new data
  in new shape; manifest may only know one.
- **`instrument_type` casing** — `PERPETUAL` vs `perpetual`; manifest holds either, disk only has lowercase.
- **Empty `instrument_type`** — schema-v4 manifest rows omit the segment.
- **Chain-bundle equivalence** — manifest `instrument_type=option` / `future` (row-level) vs disk `options_chain` /
  `futures_chain` (writer bundles them per `tardis_shared.finalise_rows_and_path`).
- **Interrupted runs** — example: 12-hour download cut out at 6h. Half the data is on disk; manifest never caught up
  (consolidator didn't merge, or the rebuild was abandoned). UI shows missing; disk has it.

**`reconcile_phantom_manifest_rows_all.py` only catches one direction** — manifest-claims-captured-but-no-parquet (the
forward phantom). It does NOT catch the inverse: parquet-on-disk-but-no-manifest-row (or `attempted_failed` row). The
inverse case is what causes wasted re-downloads. **Phase 0 below adds the inverse check.**

**Decision rule** for each AG after Phase 0:

| Phase 0 result                                   | Action                                                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------------- |
| Forward phantoms only (manifest claims, no disk) | Phase 1 flip → Phase 2 backfill (existing path)                                 |
| Inverse phantoms ≥5% of "missing" sample         | **Manifest rebuild first** (`rebuild_*_manifest.py` for that AG), THEN backfill |
| Both, inverse dominant                           | Manifest rebuild first; re-run Phase 0 after rebuild settles                    |
| Genuinely missing (probed all legacy paths)      | Phase 1 flip → Phase 2 backfill                                                 |

The rebuild path is **far cheaper** than re-downloading — it scans GCS and writes canonical manifest rows; no API spend.

## Prerequisites (instruments-side gate)

MTDS download requires the instruments-service catalogue to be honest for the `(asset_group, venue, day)` shards we're
about to backfill. If the catalogue is incomplete or wrong, MTDS will either skip valid days (catalogue says no
instruments tradeable) or fan out against bad symbols (catalogue lists instruments that never traded).

- [ ] [HUMAN] P0. Confirm sibling [`instruments_to_100pct_eod_2026_05_04.md`](instruments_to_100pct_eod_2026_05_04.md)
      Phase 3 verification has passed for the asset groups we're about to backfill (CEFI/TRADFI/DEFI/PREDICTION/SPORTS
      each ≥99% under secondary-cutoff). If an AG is still red on instruments-side, defer that AG's MTDS backfill until
      it's clean — running MTDS against an incomplete catalogue burns API quota for nothing.

## Cutoffs (per playbook + UAC `coverage_starts.py`)

Same cutoffs as the parent epic and sibling plan — repeated here so this plan is self-contained:

| Asset group | Start (global)          | End   | Per-shard secondary clip                                          |
| ----------- | ----------------------- | ----- | ----------------------------------------------------------------- |
| CEFI        | 2019-01-01              | today | per-venue inception (`CEFI_SOURCE_COVERAGE_START`)                |
| TRADFI      | 2019-01-01              | today | per-ticker listing (`TRADFI_TICKER_COVERAGE_START`)               |
| SPORTS      | 2020-06-01              | today | odds-API launch + per-bookmaker availability                      |
| PREDICTION  | 2020-06-12 (POLYMARKET) | today | per-venue + per-sub-category (`PREDICTION_SOURCE_COVERAGE_START`) |
| DEFI        | per-protocol launch     | today | per-protocol-per-chain (`DEFI_SOURCE_COVERAGE_START`)             |

Always pass the **global** start; adapter + manifest writer apply the secondary clip via UAC
`clip_dates_to_source_coverage`. Pre-launch days land as `empty_confirmed`, not `attempted_failed`.

## Schema + bundling invariants (do not violate)

These are MTDS-specific and have bitten us before. Carrying them inline so this plan is self-contained.

- **Single bundled file per `(day × underlying × data_type)`** for chains/combos. Options chains, futures combos land as
  one parquet keyed by underlying — never per-contract or per-strike. Combo bundling fix shipped 2026-04-30 + 5
  year-sharded migration VMs. Do not regress.
- **`record_empty(row_key=...)`** for source-returned-200-with-zero-rows.
  **`record_failed(row_key=..., error=classify_venue_error(exc))`** for exceptions. Never write empty placeholder
  parquets to mask phantoms.
- **DERIBIT v6 manifest needs `quote_asset` + `margin_type`** so inverse vs linear bundles don't collide on the same
  underlying (BTC-PERPETUAL vs BTC_USDC-PERPETUAL).
- **Per-VM manifest shards** (`MANIFEST_PER_VM_SHARDS=true`) are required for any 10+ concurrent VM fleet. The
  consolidator daemon merges per-VM shards into the canonical view every ~60s. Confirm `manifest-consolidator-*` VM is
  `RUNNING` before fanning out.
- **Hyperliquid / Aster perpetuals-only guard**: `BaseOnchainPerpAdapter` raises `UnsupportedCapabilityError` for
  `instrument_type=OPTION|FUTURE`. Do not expect option/futures shards for these venues; the UAC
  `get_expected_data_types_for_venue()` registry returns only perpetuals-compatible types — denominator is correct by
  construction.

## Execution DAG

```
Phase 0   (Diagnose — manifest read per AG)
            │
            ▼
Phase 0.1 (GCS-truth check — inverse phantom detection per AG)
   ├── sample N "missing" rows from manifest
   ├── probe ALL legacy GCS paths for each
   └── classify: forward-phantom / inverse-phantom / genuinely-missing
            │
            ▼  (decision branch)
            ├──────────────────────────────────────────┐
            │ inverse phantoms ≥5% of sample           │ inverse phantoms <5% of sample
            ▼                                          ▼
Phase 1.5 (Manifest rebuild for affected AG)   Phase 0.5 (Cross-checks — consolidator alive,
   ├── rebuild_*_manifest.py for AG               in-flight VM scan, tarball freshness)
   ├── consolidator merges per_vm shards                  │
   └── re-run Phase 0 + 0.1 to confirm                    ▼
            │                                  Phase 1 (Flip forward phantoms, parallel by AG)
            └──────────────────────────────────────────┐
                                                       │
                                                       ▼
                              Phase 2 (Launch MTDS backfills, parallel by asset_group)
                                 ├── CEFI       — launch-cefi-sharded-backfill.sh
                                 ├── TRADFI     — launch-tradfi-backfill-vm.sh (singleton-locked)
                                 ├── DEFI       — launch-mtds-{gas-fees,lst-rates,vault-share-price}-backfill-vm.sh
                                 ├── PREDICTION — launch-mtds-prediction-backfill-vm.sh (singleton-locked)
                                 └── SPORTS     — mostly MDPS-side (separate plan); fetch only if raw GCS empty
                                                       │
                                                       ▼  (wait — VMs run hours/days)
                              Phase 3 (Verify, parallel — manifest re-scan + drilldown spot-check)
                                                       │
                                                       ▼
                              Phase 4 (Sign-off + plan close)
```

Realistic ETA caveat: Phase 2 wall-time is dominated by CEFI (Tardis archive, 2019-→today × 9 venues × multiple
data_types per venue). Even with 100 concurrent VMs at ~20 min/shard, full re-run is days. **This is a multi-day push,
not EOD.** Ratchet the scope to the worst-covered slice first; full sweep can run in the background.

## Phase 0 — Diagnose (read-only, parallel)

For each asset group, query the MTDS manifest to learn baseline coverage. Two paths:

**Path A — direct manifest read** (cheapest, runs locally with ADC):

```bash
gsutil cp gs://market-data-tick-{ag}-central-element-323112/_index/availability_index.parquet /tmp/mtds-{ag}.parquet
.venv/bin/python -c "
import pandas as pd
df = pd.read_parquet('/tmp/mtds-{ag}.parquet')
print('total rows:', len(df))
print(df.groupby(['venue','data_type','capture_status']).size().head(50))
"
```

**Path B — deployment-api `/api/data-status/manifest`** (when the API is up — gives the same view the UI uses):

```bash
curl -sS "http://localhost:8004/api/data-status/manifest?service=market-tick-data-service&asset_group=cefi" | jq
```

- [ ] [SCRIPT] P0. Path A read for cefi MTDS bucket → log to `/tmp/mtds-recon-cefi.log`. Capture per-venue,
      per-data_type breakdown of `capture_status` counts.
- [ ] [SCRIPT] P0. Same for tradfi → `/tmp/mtds-recon-tradfi.log`.
- [ ] [SCRIPT] P0. Same for sports → `/tmp/mtds-recon-sports.log`. **Note**: sports MTDS rows are per-bookmaker
      (PINNACLE, BETFAIR_EX, DRAFTKINGS, …), not per-source. The bookmaker is the venue.
- [ ] [SCRIPT] P0. Same for prediction → `/tmp/mtds-recon-prediction.log`.
- [ ] [SCRIPT] P0. Same for defi → `/tmp/mtds-recon-defi.log`. DeFi MTDS data_types include
      `swaps, liquidity, rate_indices, oracle_prices, utilization, rewards, risk_params, gas_fees, lst_rates, perp_funding, tvl`
      — expect long-tail per `(protocol × chain × data_type)`.
- [ ] [HUMAN] P0. **Phantom audit on MTDS buckets**. The reconciler script
      (`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`) was originally designed for
      `instruments-store-*` buckets but `ASSET_GROUP_CONFIG` covers MTDS-style hive layouts too — verify by reading the
      script and confirming the prefix template targets `market-data-tick-{ag}-{pid}` for MTDS, or whether a separate
      bucket flag is needed. If the script does NOT cover MTDS buckets, add a `--bucket` override and run it on the MTDS
      bucket before claiming Phase 0 is done. (Path SSOT cross-ref:
      [`02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) §
      "Phantom audit — re-runnable recipe".)
- [ ] [HUMAN] P0. Review the five `/tmp/mtds-recon-*.log` snapshots. Capture the per-AG counts in the **Notes** section
      below. **Do NOT decide on Phase 2 yet** — Phase 0.1 below must run first. The decision is forward-phantom vs
      inverse-phantom vs genuinely-missing, and Phase 0 only sees one of those three.

## Phase 0.1 — GCS truth check (inverse phantom detection — MANDATORY before Phase 2)

This is the new gate Ikenna asked us to add (2026-05-05). For each AG, we sample rows the manifest claims are missing or
`attempted_failed`, and physically check GCS at every known legacy path shape. If parquets exist, the AG needs a
manifest rebuild — NOT a backfill. Skipping this phase risks paying Databento / Tardis / DeFi RPC / odds-API to re-fetch
data we already have on disk.

**Cost ladder (most expensive first)** — informs how aggressively to sample per AG:

| AG         | API cost                         | Sample size recommendation          |
| ---------- | -------------------------------- | ----------------------------------- |
| TRADFI     | Databento (paid)                 | ≥200 missing rows per venue         |
| DEFI       | RPC + The Graph                  | ≥200 missing rows per (proto,chain) |
| CEFI       | Tardis (paid)                    | ≥200 missing rows per venue         |
| SPORTS     | odds-API (paid)                  | ≥100 missing rows per bookmaker     |
| PREDICTION | ~free (Polymarket/Kalshi public) | ≥50 missing rows per venue          |

CeFi public endpoints (Binance/Bybit/OKX/etc. raw) are free, but Tardis (which we use for the historical archive) is
paid — so CeFi's cost row is "Tardis", not "venue". Treat all 5 AGs as paid for sampling purposes.

### Legacy path shapes to probe per `(ag, venue, data_type, day)` tuple

For every "missing" row sampled, probe ALL of these GCS path shapes before classifying as genuinely-missing. Five known
drift axes (already encoded in `reconcile_phantom_manifest_rows_all.py` in the forward direction; need them encoded in
inverse direction too):

1. **Hive vocab** — `category={ag}/...` (legacy) AND `asset_group={ag}/...` (canonical).
2. **Path prefix** — top-level `day=YYYY-MM-DD/...` AND `raw_tick_data/by_date/day=YYYY-MM-DD/...`.
3. **`instrument_type` casing** — both upper (`PERPETUAL`) and lower (`perpetual`).
4. **Empty `instrument_type`** — schema-v4 rows with no segment.
5. **Chain-bundle equivalence** — manifest `instrument_type=option`/`future` (per-row) vs disk
   `instrument_type=options_chain`/`futures_chain` (bundled per-underlying). For the bundled case, the path is
   `instrument_type=options_chain/data_type={dt}/underlying={base}/ticks.parquet` regardless of how the manifest names
   the per-row instrument_type.

Plus DeFi-specific:

6. **Legacy DeFi venue overload** — `venue=PROTOCOL-CHAIN/` (e.g. `venue=AAVE_V3-ETHEREUM/`) where canonical splits to
   `venue=AAVE_V3/chain=ETHEREUM/`.
7. **No-asset-group hive segment** — old DeFi writes that omit the AG segment entirely.

Plus prediction-specific:

8. **Polymarket 9-segment layout** — `venue=POLYMARKET/sub_category=.../market=.../...` vs flat venue path.

### Tooling

Two paths — pick one, both are acceptable:

**Path A — extend `reconcile_phantom_manifest_rows_all.py`** to support `--mode inverse` that walks GCS and reports
parquets without manifest rows. Cleaner long-term — same drift axes are already encoded for the forward direction. The
script lives in `instruments-service/scripts/`.

**Path B — one-off audit script** under `market-tick-data-service/scripts/audit_inverse_phantoms.py` that reads a sample
of "missing" rows from the manifest, builds the legacy-path probe list per drift axis, runs `gsutil ls` (or
`storage_client.list_blobs(prefix=...)`) per probe, and emits a CSV of
`(ag, venue, data_type, day, found_at_path, classification)`. Faster to ship for this one-time gate; Path A is the
proper fix to land afterwards.

- [ ] [HUMAN] P0. Pick Path A or Path B with Ikenna. **Default**: Path B for this push (faster), Path A as a follow-up
      todo to land the inverse mode in the canonical reconciler.
- [ ] [HUMAN] P0. **MUST run on a same-region GCE VM** — cross-region GCS listing is 18× slower (~12 prefixes/sec from
      laptop vs 222/sec on `asia-northeast1-c`). Spin up `e2-standard-4` in `asia-northeast1-c` for the audit. Same
      pattern as the phantom audit recipe in
      [`02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) §
      "Phantom audit — re-runnable recipe".
- [ ] [SCRIPT] P0. Run the inverse audit per AG, with sample size from the cost-ladder table above. Output:
      `/tmp/mtds-inverse-cefi.csv /tmp/mtds-inverse-tradfi.csv /tmp/mtds-inverse-sports.csv /tmp/mtds-inverse-prediction.csv /tmp/mtds-inverse-defi.csv`
      Each CSV row: `ag, venue, data_type, day, classification, found_at_path`. Classifications:
      `inverse_phantom_axis_<N>` (parquet found at one of the 8 legacy paths), `genuinely_missing` (no parquet at any
      probed path).
- [ ] [HUMAN] P0. **Per AG, compute inverse-phantom rate** = inverse_phantom rows ÷ sample size. Apply the decision
      rule:
  - **<5%** → drift is noise. Proceed to Phase 0.5 → Phase 1 → Phase 2 (existing flow).
  - **≥5%** → AG needs Phase 1.5 manifest rebuild BEFORE backfill. Capture which drift axis dominates (axis 1, 2, 5,
    etc.) — that tells us which rebuild script flag to use.
  - **≥20%** → escalate to Ikenna before any further action. Suggests a recent path/schema change wasn't migrated;
    flagging early avoids re-running the rebuild on shifting ground.
- [ ] [HUMAN] P0. Capture the per-AG decision in the Notes section: rebuild-first vs backfill-first.
- [ ] [HUMAN] P1. **Sanity-check sampling**: pick 5 random `inverse_phantom` rows per AG and manually `gsutil ls` the
      reported `found_at_path` to confirm the parquet really exists and isn't a 0-byte placeholder or directory-marker.
      Audit script bugs are more dangerous than backfill VMs — a false-positive inverse phantom sends us down a rebuild
      path that never lands.

## Phase 0.5 — Cross-checks before fanning out

Before launching any new MTDS backfill VM:

- [ ] [HUMAN] P0. **Manifest consolidator alive.** Per-VM manifest shards aren't mergeable without it.
      `bash gcloud compute instances list --filter='name~"^manifest-consolidator-"' --format='table(name,status,zone)' `
      Should be exactly one `RUNNING`. If absent, launch via
      `bash deployment-service/scripts/vm/launch-manifest-consolidator-vm.sh` before Phase 2.
- [ ] [HUMAN] P0. **In-flight MTDS VM scan.** Don't collide with VMs already running.
      `bash gcloud compute instances list \ --filter='name~"^(cefi-|tradfi-|mtds-|mdps-)"' \ --format='table(name,status,zone,creationTimestamp)' `
      For any RUNNING shard that overlaps the scope you're about to launch, let it finish (or coordinate with the
      operator). Singleton-locked launchers (`launch-tradfi-backfill-vm.sh`, `launch-mtds-prediction-backfill-vm.sh`,
      `launch-sfi-forward-poll.sh`) will refuse to start; non-locked launchers will race.
- [ ] [HUMAN] P0. **Tarball freshness.** If MTDS / UAC / UTL code changed since last backfill run, refresh tarballs:
      `bash bash deployment-service/scripts/vm/create-code-tarballs.sh --all ` Bare invocation only re-tars CORE;
      `--all` is safest for any cross-repo state. Verify with
      `gsutil ls -l gs://deployment-scripts-central-element-323112/code/` — timestamps should be post your last relevant
      commit.
- [ ] [HUMAN] P0. **Zombie-watchdog dict check.** Before launching any new VM-name prefix, confirm the prefix is in
      `VM_PREFIX_TO_BUCKET` in `deployment-service/scripts/vm/vm_zombie_watchdog.py`. New prefix → add it + relaunch the
      watchdog VM (the running watchdog only fetches the Python at boot). Reference incident: 2026-05-05 — 5 prefixes
      silently zombied because launchers were added without dict updates.
- [ ] [HUMAN] P0. **Secret Manager check.** For any venue whose API key isn't in `central-element-323112` SM, ping
      Ikenna before launching. Common ones for MTDS: `tardis-api-key`, `databento-api-key`, `polymarket-api-key`,
      `kalshi-api-key`. `ApiKeyReloader` (UTL) fetches at runtime — missing key = silent failure (validates as empty
      dict if venue-name typo, see Known Gotchas below).

## Phase 1 — Flip phantoms / re-attempt failed shards (parallel by AG)

Run only for asset groups where Phase 0 found phantoms or where `attempted_failed` rows are stuck across runs.

**Critical**: phantoms (`captured` claim, no parquet on disk) must be flipped to `attempted_failed` so the
orchestrator's `_should_skip_shard` lets the next backfill VM retry them. Do NOT write empty placeholder parquets to
mask phantoms — that fudges data quality. Per CLAUDE.md manifest-phantom-audit rule: `record_empty()` is for
legitimately-empty source responses only.

- [ ] [SCRIPT] P0. For each AG with phantoms > 0, run the reconciler against the MTDS bucket (assumes the script
      supports a `--bucket` override or `--service market-tick-data-service` flag — confirm in Phase 0):
      `bash cd ~/unified-trading-system-repos/instruments-service .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py \ --asset-group <ag> --service market-tick-data-service \ 2>&1 | tee /tmp/mtds-flip-<ag>.log `
      No `--dry-run` — actually flip phantoms.
- [ ] [SCRIPT] P0. Re-run the dry-run to confirm phantom count → 0 for each flipped AG.

## Phase 1.5 — Manifest rebuild (only for AGs flagged in Phase 0.1)

Run only for AGs where Phase 0.1 found inverse-phantom rate ≥5%. The rebuild script re-scans canonical GCS paths and
writes manifest rows for parquets that exist on disk but have no `captured` manifest row. **Cheaper and faster than a
backfill** — no API spend, just GCS list operations.

**Per-service rebuild scripts** (the right one depends on which manifest needs the rebuild — these target the MTDS
manifest at `market-data-tick-{ag}-{pid}/_index/availability_index.parquet`):

| AG         | Rebuild script (verify before running — paths drift)                        |
| ---------- | --------------------------------------------------------------------------- |
| CEFI       | `market-tick-data-service/scripts/rebuild_cefi_manifest.py` (or equivalent) |
| TRADFI     | `market-tick-data-service/scripts/rebuild_tradfi_manifest.py`               |
| SPORTS     | `market-tick-data-service/scripts/rebuild_sports_manifest.py`               |
| PREDICTION | `market-tick-data-service/scripts/rebuild_prediction_manifest.py`           |
| DEFI       | `market-tick-data-service/scripts/rebuild_defi_manifest.py`                 |

If any of these don't exist, the alternative is a generic UTL rebuild via the manifest_consolidator's full re-scan mode
— confirm with Ikenna which is canonical for MTDS today before running.

- [ ] [HUMAN] P0. Verify the right rebuild script exists for each affected AG. If absent, **stop and ping Ikenna** — do
      not improvise a rebuild script for production manifests.
- [ ] [HUMAN] P0. **Pre-flight**: tarball refresh + run on same-region VM. Rebuilds list every parquet in the bucket —
      same 18× perf cliff as the audit. Use the phantom-audit recipe pattern from the codex doc.
- [ ] [HUMAN] P0. **Pass `per_vm_shards=True`** when running rebuild — without it, the rebuild's writes fight the
      consolidator daemon's CAS retries and most rebuild output gets dropped. Reference incident: 2026-05-02 DeFi
      rebuild lost 80k rows compacted to 12k canonical because of CAS contention. SSOT:
      [`02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) §
      "Per-VM shard layout".
- [ ] [SCRIPT] P0. Run the rebuild for each affected AG:
      `bash cd ~/unified-trading-system-repos/market-tick-data-service VM_NAME=rebuild-mtds-{ag}-$(date +%Y%m%d-%H%M%S) MANIFEST_PER_VM_SHARDS=true \ .venv/bin/python scripts/rebuild_{ag}_manifest.py 2>&1 | tee /tmp/mtds-rebuild-{ag}.log `
      Each unique `VM_NAME` writes its own per-VM shard so concurrent runs don't collide.
- [ ] [SCRIPT] P0. **Force-merge** after each rebuild so readers see the canonical view immediately:
      `bash .venv/bin/python -m unified_trading_library.manifest_consolidator \ --bucket market-data-tick-{ag}-central-element-323112 `
      Idempotent + safe to run concurrently with the scheduled cycle.
- [ ] [HUMAN] P0. **Re-run Phase 0 + 0.1 for the rebuilt AG.** Verify:
  - Forward phantoms (claim-no-disk) ≈ 0.
  - Inverse phantoms (disk-no-claim) ≈ 0.
  - "Missing" denominator dropped by roughly the inverse-phantom count from Phase 0.1. Capture the delta in the Notes
    section. If the inverse-phantom rate stays ≥5%, the rebuild script doesn't cover the dominant drift axis — escalate
    to Ikenna; do NOT proceed to Phase 2 for that AG.
- [ ] [HUMAN] P0. Only after the rebuilt AG's Phase 0/0.1 numbers are clean does it become eligible for Phase 2.

## Phase 2 — Launch MTDS backfills (parallel by asset group)

**Gate**: each AG must have completed Phase 0.1 (and Phase 1.5 if it was flagged) before its Phase 2 launches. AGs in
different states proceed independently — e.g. PREDICTION can backfill while CEFI is mid-rebuild, since they hit
different buckets.

This is where the actual MTDS download work happens. Unlike instruments-service, MTDS **does have dedicated VM launchers
per asset_group** (instruments-service falls back to a local-driver script — that asymmetry caused confusion in the
sibling plan). All MTDS launchers route through `setup-data-pipeline-vm.sh` with `VM_TASK=cefi-backfill` /
`tradfi-backfill` / etc. and write per-VM manifest shards (consolidator merges).

**Force-flag warning**: every launcher accepts `--force`. With `force=true`, the orchestrator re-fetches every shard
regardless of `_should_skip_shard` — billable Tardis/Databento API cost. **Use `force=false` for gap-fill.** Reserve
`force=true` for retesting one specific shard or after a code-fix that requires re-running known-bad data.

### CEFI

Tardis-backed venues + Hyperliquid/Aster on-chain. The 2026-04-29 366-VM rollout (`run-ts=20260429-154202`) covered most
of the space; gap-fill is what's left.

**Singleton lock added 2026-05-05** (`launch-cefi-sharded-backfill.sh` `FORCE=1` env-var bypass): refuses re-launch if
any prior `^(cefi|tradfi)-.*-(heavy|light)-` sharded VM is RUNNING in the zone. Same shared-account contention class as
the 2026-05-05 Databento silent-drop incident — Tardis rate-limits per-account and the project egress NAT is shared.

- [ ] [HUMAN] P0. Confirm Phase 0 cefi MTDS gap (review `<tmpdir>/mtds-recon-cefi.log`; tmpdir resolves via
      `tempfile.gettempdir()` per Bandit B108).
- [ ] [HUMAN] P0. For any year × venue × instrument_type slice still showing `attempted_failed`, re-launch via:
      `bash deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh` (defaults shard the configured venue universe
      across years). The singleton lock will refuse to launch if any prior `cefi-*-heavy-*` / `cefi-*-light-*` /
      `tradfi-*-heavy-*` / `tradfi-*-light-*` VM is RUNNING. Use `FORCE=1 bash …` only if you've confirmed the prior VMs
      are genuinely zombied. Verify the launcher's flags by reading the script header before running — flag names drift.
- [ ] [HUMAN] P0. **Verify event stream after launch (every cefi shard VM)** — within 90s of the launch fan-out, run
      `gcloud storage ls gs://central-element-323112-events/events/market-tick-data-service/$(date -u +%Y-%m-%d)/cefi-*-*-*/`
      and confirm each new shard VM has an `hour=*` partition with at least one JSONL line where `event=="STARTED"`.
      Re-check every 10–15min for new progress events with row counts (`INSTRUMENT_PROCESSED` etc. per CLAUDE.md "no
      fire-and-forget VM launches"). Stalled shards == silently-broken; kill via
      `gcloud compute instances delete cefi-<venue>-<year>-<group>-<run-ts> --zone=asia-northeast1-c --quiet` and
      diagnose via the last event's `metadata.details`. The 2026-05-05 MDPS incident (21 VMs ran clean STARTED + STOPPED
      but emitted 1440 empty bars/day) is the canonical reason this active-verification step is mandatory.
- [ ] [HUMAN] P0. **DERIBIT options chain** — bundled per-underlying, not per-strike. Verify by sampling any captured
      day: should be `instrument_type=options_chain/data_type=trades/underlying=BTC/ticks.parquet` (bundled), no
      per-contract files. If you see per-contract files post-2026-04-30, that's a regression — flag to Ikenna.
- [ ] [HUMAN] P1. **DERIBIT v6 inverse/linear split** — manifest must populate `quote_asset` + `margin_type` for DERIBIT
      chain shards. Verify by sampling a DERIBIT row: both columns non-empty (e.g.
      `quote_asset=USD, margin_type=inverse` for BTC-PERPETUAL; `quote_asset=USDC, margin_type=linear` for
      BTC_USDC-PERPETUAL).
- [ ] [HUMAN] P1. **OOM watch** — CeFi VMs occasionally `rc=137` (SIGKILL by systemd OOM-killer) on heavy
      instrument_types (DERIBIT options chain especially). No `EXIT_STATUS` written for rc=137. Diagnose via Cloud
      Logging kernel OOM query (see
      [`05-infrastructure/vm-tarball-deployment.md`](/codex/05-infrastructure/vm-tarball-deployment.md) § "Exit codes").
      Bump machine type or shard year-by-year.

### TRADFI

**MVP universe (2026-05-05 scope cut, Q&A-confirmed)** — only the 8 instruments that the date-futures arb archetype
needs:

| Root        | Venue  | Instrument-id        | Data path                                       | Notes                                              |
| ----------- | ------ | -------------------- | ----------------------------------------------- | -------------------------------------------------- |
| ES          | CME    | `CME:FUTURE:ES.FUT`  | Databento                                       | E-mini S&P futures                                 |
| MES         | CME    | `CME:FUTURE:MES.FUT` | Databento                                       | Micro E-mini S&P futures                           |
| ES options  | CME    | `CME:OPTION:ES.OPT`  | Databento                                       | Bundled per-underlying options chain               |
| BTC futures | CME    | `CME:FUTURE:BTC.FUT` | Databento                                       | CME-listed BTC futures                             |
| ETH futures | CME    | `CME:FUTURE:ETH.FUT` | Databento                                       | CME-listed ETH futures                             |
| IBIT        | NASDAQ | `NASDAQ:ETF:IBIT`    | Databento (XNAS.ITCH)                           | iShares Bitcoin ETF — most liquid US BTC spot ETF  |
| ETHA        | NASDAQ | `NASDAQ:ETF:ETHA`    | Databento (XNAS.ITCH)                           | iShares Ethereum ETF — most liquid US ETH spot ETF |
| VIX index   | CBOE   | `CBOE:INDEX:VIX`     | **NOT Databento** — CBOE direct, ohlcv_15m only | Already captured 1,585 days; do not re-fetch       |

**Dropped (do NOT add back without a follow-up plan)**: FBTC / ARKB / FETH (Cboe BZX = BATS) and GBTC / ETHE / BITO
(NYSE Arca). The date-futures arb only needs CME futures + Deribit (same last-Friday-of-month expiry); IBIT + ETHA on
NASDAQ cover spot exposure. Re-adding requires UAC instrument def + ARCA / BATS venue entries +
`launch-tradfi-backfill-vm.sh` case branches together — the launcher's `valid_roots` regex is currently
`ES|ES_OPT|MES|BTC|ETH|IBIT|ETHA`. SSOT for the cut: project memory
`project_tradfi_mvp_etf_scope_reduction_2026_05_05.md`.

- [ ] [HUMAN] P0. Confirm Phase 0 tradfi MTDS gap (review `/tmp/mtds-recon-tradfi.log`). Compare to MVP universe above —
      anything outside the 8 rows is out-of-scope and should NOT be backfilled in this push.
- [ ] [HUMAN] P0. For ES / MES futures, ES options chain, BTC / ETH futures, or IBIT / ETHA ETF gaps, re-launch via the
      singleton-locked launcher (constrained to the MVP universe):
      `bash deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh --start-date 2019-01-01 --end-date $(date -u +%Y-%m-%d) --instrument-ids 'CME:FUTURE:ES.FUT;CME:FUTURE:MES.FUT;CME:OPTION:ES.OPT;CME:FUTURE:BTC.FUT;CME:FUTURE:ETH.FUT;NASDAQ:ETF:IBIT;NASDAQ:ETF:ETHA' --data-types ohlcv_1m,trades,tbbo`
      The singleton lock refuses to launch if any `tradfi-bf-*` VM is RUNNING. Use `--force` only if the prior VM is
      genuinely zombied. **Per-VM event verification is mandatory** (see paired checkbox below).
- [ ] [HUMAN] P0. **Verify event stream after launch** — within 90s, run
      `gcloud storage ls gs://central-element-323112-events/events/market-tick-data-service/$(date -u +%Y-%m-%d)/tradfi-bf-*/`,
      assert the directory exists with an `hour=*` partition; read the first JSONL and assert `event=="STARTED"`.
      Re-check every 10–15min for new progress events with row counts (see CLAUDE.md "no fire-and-forget VM launches").
      Stalled progression == silently-broken; kill via
      `gcloud compute instances delete tradfi-bf-<run-ts> --zone=asia-northeast1-c --quiet` and diagnose via the last
      event's `metadata.details`.
- [ ] [HUMAN] P0. **Post-fix Databento honesty check** — BUG-X3 (silent-drop fix shipped 2026-05-05) means a 429 on
      `ohlcv_1m` for any (root, date) now writes `attempted_failed` instead of `empty_confirmed`. After the run, query
      the manifest for
      `service=market-tick-data-service AND asset_group=tradfi AND error_reason IN ('429','RATE_LIMIT')` — any rows are
      genuinely-failed Databento attempts that need a serial gap-fill (cf. `/tmp/fill_missing_ohlcv.py` pattern from the
      2026-05-05 recovery). Pre-fix these would have appeared as zero-row "captured" parquets.
- [ ] [HUMAN] P1. **VIX index already done** — do not re-fetch. 1,585 days at
      `asset_group=tradfi/venue=CBOE/instrument_type=index/data_type=ohlcv_15m/VIX.parquet`. **VIX is on CBOE direct,
      NOT Databento** — does not share the Databento per-account quota. If a strategy needs <15m granularity, that's a
      separate sourcing question — flag to Ikenna.
- [ ] [HUMAN] P2. **VIX futures full-tick chain — deferred**. UAC `_CBOE_INSTRUMENTS = []` placeholder. Out of scope for
      this plan; needs separate plan + declarative VX contract calendar.

### DEFI

Per-protocol-per-chain inception dates from `DEFI_SOURCE_COVERAGE_START`. DeFi MTDS uses `collect-evm-defi` /
`collect-dex-swaps` CLI handlers (NOT the `download` operation — DeFi venues are in `VENUE_TO_ASSET_GROUP['defi']`).

- [ ] [HUMAN] P0. Confirm Phase 0 defi MTDS gap (review `<tmpdir>/mtds-recon-defi.log`).
- [ ] [HUMAN] P0. **Cloud Run DeFi collection job** is the canonical batch path for swaps/liquidity (NOT a VM). Verify
      it's healthy + re-trigger any failed runs. Cross-check with the consolidated DeFi pipeline plan
      ([`consolidated_defi_data_pipeline_2026_04_15.md`](consolidated_defi_data_pipeline_2026_04_15.md)) for the
      canonical operations workflow.
- [ ] [HUMAN] P0. **Cloud Run Jobs `:latest` pin gotcha** — Cloud Run Jobs lock onto an AR digest at create time and
      ignore subsequent `:latest` pushes. After any MTDS image push, run
      `gcloud run jobs update <NAME> --image=...:latest --region=...` for each affected job to force the new digest (per
      project memory `feedback_cloud_run_jobs_latest_pin.md`). Detection: `gcloud run jobs describe <NAME>`'s `image:`
      field shows `@sha256:...` — compare to AR's current `:latest` updateTime. Without this, the DeFi job can sit on
      stale image silently for 30+ min after a push.
- [ ] [HUMAN] P0. Specialised MTDS launchers for the long-tail DeFi data_types (one VM per data_type per protocol — they
      hit a shared chain RPC pool, so launch SEQUENTIALLY not in parallel; verify launcher flags before running):
      `bash deployment-service/scripts/vm/launch-mtds-gas-fees-backfill-vm.sh --start-date <protocol-launch>`
      `bash deployment-service/scripts/vm/launch-mtds-lst-rates-backfill-vm.sh --start-date <protocol-launch>`
      `bash deployment-service/scripts/vm/launch-mtds-vault-share-price-backfill-vm.sh --start-date <protocol-launch>`
- [ ] [HUMAN] P0. **Verify event stream after each DEFI launch** — within 90s, run
      `gcloud storage ls gs://central-element-323112-events/events/market-tick-data-service/$(date -u +%Y-%m-%d)/mtds-{gas-fees,lst-rates,vault}-*/`
      and confirm `event=="STARTED"`. Re-check every 10–15min for progress events. Per CLAUDE.md, the launch + monitor
      pair is ONE todo — launching a `mtds-gas-fees-` VM without scheduling event-tail polling is fire-and-forget.
- [ ] [AGENT] P0. **Singleton-lock follow-up for the three launchers** — gas-fees / lst-rates / vault-share-price all
      hit a shared chain RPC pool (Alchemy / Infura per UAC `CHAIN_RPC_TEMPLATES`). The 2026-05-05 silent-drop class
      argument applies: concurrent VMs hammering the same RPC endpoint exhaust per-key quotas with no per-call manifest
      signal. Either add the singleton-lock pattern to each (copy from `launch-mtds-prediction-backfill-vm.sh`) or
      document why each is exempt. Tracked as a P0 follow-up — do NOT run multiple in parallel until landed.
- [ ] [HUMAN] P1. **`validate_api_keys_for_venues` venue-name gotcha** — passes canonical venue names
      (`UNISWAP_V3-ETHEREUM`, `AAVE_V3-ETHEREUM`), NOT data-source slugs (`thegraph`). Returns empty dict silently on
      wrong shape; downstream adapters silently fail. If a DeFi VM logs "missing key" on a venue you know has the
      secret, suspect this first.

### PREDICTION

POLYMARKET (from 2020-06-12) + KALSHI (from 2021-07-19). Singleton-locked because Polymarket gamma rate-limits per-IP
and the project egress NAT is shared.

- [ ] [HUMAN] P0. Confirm Phase 0 prediction MTDS gap (review `<tmpdir>/mtds-recon-prediction.log`).
- [ ] [HUMAN] P0. Launch via the singleton-locked launcher (sequential — Polymarket then Kalshi; the lock refuses a
      second `mtds-prediction-*` VM in the zone):
      `bash deployment-service/scripts/vm/launch-mtds-prediction-backfill-vm.sh 2020-06-12 $(date -u +%Y-%m-%d)`
      (default venue=POLYMARKET / data_types per launcher header). Then for KALSHI run with the venue override
      documented in the launcher source. Use `bash <launcher> --force <dates>` only if the prior VM is genuinely zombied
      per the launcher's own ERROR message.
- [ ] [HUMAN] P0. **Verify event stream after each PREDICTION launch** — within 90s, run
      `gcloud storage ls gs://central-element-323112-events/events/market-tick-data-service/$(date -u +%Y-%m-%d)/mtds-prediction-*/`
      and confirm `event=="STARTED"`. Re-check every 10–15min for progress events. POLYMARKET runs are 10–25 min so a
      single check + completion check is usually enough; KALSHI similar. Stalled progression == kill via
      `gcloud compute instances delete mtds-prediction-<run-ts> --zone=asia-northeast1-c --quiet`.
- [ ] [HUMAN] P1. **Polymarket cursor-sharding** — instruments-side cursor bands per (year, month) shipped 2026-05-05
      (`POLYMARKET_START_CURSOR` / `POLYMARKET_END_CURSOR` env vars per project memory). MTDS may want the same trick if
      download throughput is timeout-bound. Defer until Phase 0 numbers come in; bare launcher is the first attempt.

### SPORTS

**Mostly downstream of MDPS, not a fresh fetch.** Per the playbook: "a large fraction of the missing manifest rows for
`ODDS_HORIZON_BUCKET` and similar are already fetched into raw GCS but not yet processed through MDPS into the canonical
per-league partitions. The lift is mostly MDPS-side, not fetch-side."

- [ ] [HUMAN] P0. Confirm Phase 0 sports MTDS gap (review `<tmpdir>/mtds-recon-sports.log`). The "venue" axis here is
      bookmaker (PINNACLE, BETFAIR_EX, DRAFTKINGS, …), not source.
- [ ] [HUMAN] P0. **Sample raw odds-API GCS bucket** for any date the manifest claims missing. If raw data exists, this
      is an MDPS processing gap (out of scope here, separate MDPS plan). If raw data is genuinely missing, then a fresh
      odds-API fetch is needed.
- [ ] [HUMAN] P0. **If a sports backfill VM IS launched from this plan** (rare — sports is mostly MDPS-side), pair it
      with event-stream verification within 90s of launch:
      `gcloud storage ls gs://central-element-323112-events/events/{instruments-service|market-tick-data-service}/$(date -u +%Y-%m-%d)/{af|fs|tm|sfi|us|weather}-backfill-*/`.
      Sports launchers use source-keyed prefixes (`af-`, `fs-`, `tm-`, `sfi-`, `us-`, `weather-` per CLAUDE.md "VM
      Naming Convention") — make sure the prefix is the one in `VM_PREFIX_TO_BUCKET` for the chosen launcher.
- [ ] [HUMAN] P1. For genuine fetch gaps, the odds-API has its own backfill path — coordinate with the sports-side agent
      / sibling plan. **Do not** launch parallel sports VMs while
      [`instruments_to_100pct_eod_2026_05_04.md`](instruments_to_100pct_eod_2026_05_04.md) sports work is mid-flight;
      partition collisions will cause manifest noise.

## Phase 3 — Verify (parallel)

Verification has to cover **both directions** now, not just forward phantoms:

- [ ] [SCRIPT] P0. **Forward phantom check** — for each AG, re-read the MTDS manifest and confirm forward-phantom count
      is 0 + `attempted_failed` count has dropped substantially since Phase 0 baseline.
- [ ] [SCRIPT] P0. **Inverse phantom check** — for each AG, re-run the Phase 0.1 inverse audit on a fresh sample.
      Inverse-phantom rate should be <1% (down from whatever Phase 0.1 found). If it ticks back up post-backfill, the
      backfill writer is producing parquets without manifest rows — flag immediately, don't claim done.
- [ ] [HUMAN] P0. Snapshot the deployment-ui drilldown for `service=market-tick-data-service` per asset_group. Each
      should show ≥99% `captured + empty_confirmed` under the secondary-cutoff denominator.
- [ ] [HUMAN] P0. **Cache-clear the deployment-api before reading the drilldown** — UI is backed by 4 cache layers
      (`_turbo_cache`, `_INDEX_CACHE`, `_drilldown._cache`, `_REF_DATA_CACHE`, all 5-min TTL). Hit
      `/api/data-status/turbo/clear` (sibling-plan Day 2 fix landed all 4 clears) before sampling, else you may read
      stale numbers from before Phase 1.5 / Phase 2.
- [ ] [HUMAN] P1. Spot-check 5 random `(asset_group, day, venue, instrument_type, data_type)` rows per AG: follow each
      to the canonical GCS path and confirm the parquet exists. Specifically check chain-bundled cases: DERIBIT options
      chain (`underlying=BTC|ETH`), CME ES options chain (`underlying=ES`), futures combos.
- [ ] [HUMAN] P1. Schema validation parity — the View Schema modal in the UI for any MTDS data_type returns the same
      columns as the registered `SchemaDefinition` in the service code. Sibling plan / parent epic Phase 0 covers
      drilldown bug fixes; this verifies write-time validation actually fired.

## Phase 4 — Sign-off + plan close

- [ ] [HUMAN] P0. Update parent epic
      ([`instruments_and_market_tick_data_completion_2026_05_01.md`](instruments_and_market_tick_data_completion_2026_05_01.md))
      progress notes: mark MTDS slice ≥99% under secondary-cutoff. Link to this plan.
- [ ] [HUMAN] P0. Brief Ikenna on results + any gotchas surfaced (likely candidates: new phantom drift axes, schema
      mismatches, missing SM secrets, launcher flag drift).
- [ ] [HUMAN] P1. If any per-AG gap remained at <99% for legitimate reasons (provider outage, bookmaker shutdown, etc.),
      document it in
      [`02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)
      under "Known coverage gaps" so future runs don't chase it.
- [ ] [AGENT] P2. Mark this plan complete and move to `plans/archive/`.

## Files / commands referenced

| Repo                     | File / command                                                                                  | Phase         |
| ------------------------ | ----------------------------------------------------------------------------------------------- | ------------- |
| instruments-service      | `scripts/reconcile_phantom_manifest_rows_all.py` (with `--bucket` / `--service`)                | 0,1,3         |
| instruments-service      | `scripts/reconcile_phantom_manifest_rows_all.py --mode inverse` (Path A — to be added)          | 0.1,3         |
| market-tick-data-service | `scripts/audit_inverse_phantoms.py` (Path B — one-off audit script)                             | 0.1,3         |
| market-tick-data-service | `scripts/rebuild_{cefi,tradfi,sports,prediction,defi}_manifest.py` (verify exists per AG)       | 1.5           |
| unified-trading-library  | `python -m unified_trading_library.manifest_consolidator --bucket <X>` (force-merge)            | 1.5           |
| deployment-service       | `scripts/vm/launch-cefi-sharded-backfill.sh`                                                    | 2-CEFI        |
| deployment-service       | `scripts/vm/launch-tradfi-backfill-vm.sh` (singleton-locked)                                    | 2-TRADFI      |
| deployment-service       | `scripts/vm/launch-mtds-prediction-backfill-vm.sh` (singleton-locked)                           | 2-PRED        |
| deployment-service       | `scripts/vm/launch-mtds-gas-fees-backfill-vm.sh`                                                | 2-DEFI        |
| deployment-service       | `scripts/vm/launch-mtds-lst-rates-backfill-vm.sh`                                               | 2-DEFI        |
| deployment-service       | `scripts/vm/launch-mtds-vault-share-price-backfill-vm.sh`                                       | 2-DEFI        |
| deployment-service       | `scripts/vm/launch-manifest-consolidator-vm.sh`                                                 | 0.5           |
| deployment-service       | `scripts/vm/create-code-tarballs.sh --all`                                                      | 0.5           |
| deployment-service       | `scripts/vm/vm_zombie_watchdog.py` (`VM_PREFIX_TO_BUCKET` dict)                                 | 0.5           |
| deployment-api           | `POST /api/data-status/turbo/clear` (drops all 4 cache layers)                                  | 3             |
| unified-api-contracts    | `unified_api_contracts/canonical/coverage_starts.py`                                            | ref           |
| unified-trading-pm       | `/codex/14-playbooks/backfill-completion-playbook.md`                                           | ref           |
| unified-trading-pm       | `/codex/02-data/availability-manifest-and-data-status.md` § Phantom audit + Per-VM shard layout | 0,0.1,1,1.5,3 |
| unified-trading-pm       | `/codex/05-infrastructure/vm-tarball-deployment.md`                                             | 0.5,1.5,2     |

**Explicitly NOT used** (these run instruments-service or MDPS, not MTDS):
`launch-{api-football,transfermarkt,sfi, footystats,understat,openmeteo}-backfill-vm.sh` (instruments-side, sibling plan
owns), `launch-mdps-backfill-vm.sh` / `launch-mdps-sharded-backfill.sh` (downstream candle generation).

## Success criteria

- All 5 asset groups: ≥99% `captured + empty_confirmed` for `service=market-tick-data-service`, scoped to the
  secondary-cutoff denominator.
- Forward phantom recon dry-run on each MTDS bucket reports 0 phantoms (manifest-claims-no-disk).
- **Inverse phantom audit reports <1% rate per AG** (disk-no-manifest-row). This is the new criterion from Ikenna's
  2026-05-05 callout — proves we didn't waste API spend re-downloading data already on disk.
- Drilldown spot-check: 5 random `(asset_group, day, venue, instrument_type, data_type)` rows per AG resolve to actual
  parquets in GCS, including chain-bundled cases (DERIBIT options, ES options, futures combos).
- DERIBIT v6 manifest rows have `quote_asset` + `margin_type` populated.
- No `manifest-consolidator-*` zombie / outage observed during the backfill window.
- **Cost discipline check**: total API spend during this push (Tardis + Databento + DeFi RPC + odds-API) reported back
  to Ikenna with a per-AG breakdown. Phase 0.1 manifests as a line item — "rows we did NOT re-download because the
  inverse audit caught them" — so we have evidence that the gate worked.

## Out of scope (for _this_ plan — covered by sibling plans / parent epic)

- instruments-service backfill ([`instruments_to_100pct_eod_2026_05_04.md`](instruments_to_100pct_eod_2026_05_04.md)).
- MDPS candle generation / odds-horizon-bucket processing (separate plan; many sports gaps live there).
- deployment-ui drilldown bug fixes (parent epic Phase 0 — CSV download, day-shard scroll, schema modal, unified
  MTDS+MDPS view).
- VIX futures full-tick chain — deferred (separate plan + UAC declarative VX contract calendar needed).
- mbp_10 deep book for tradfi — deferred (microstructure strategy not yet requesting it).
- Live forward-poll for any AG — next milestone, not part of this work. Forward-poll launchers
  (`launch-cefi-forward-poll.sh`, `launch-tradfi-forward-poll.sh`, `launch-sfi-forward-poll.sh`,
  `launch-footystats-forward-poll.sh`) are referenced for context only.

## Known gotchas (from playbook + handoff doc — re-stated for self-containment)

- `validate_api_keys_for_venues` wants canonical venue names (`UNISWAP_V3-ETHEREUM`), not data-source slugs
  (`thegraph`). Returns empty dict silently on wrong shape.
- CeFi VM `rc=137` (OOM-kill) writes no `EXIT_STATUS` and no `DEPLOYMENT_FAILED` event — atexit handlers don't fire on
  SIGKILL. Diagnose via Cloud Logging kernel OOM query.
- Tardis bulk grouped `FUTURES` request returns empty silently. Adapter must enumerate per-instrument and fan out.
- Concurrent VM boots can race the deadsnakes PPA (~3 of N hang at python3.13 install). Stagger boots ≥30s if launching
  many at once.
- Tarball install pins the VM to local `pyproject.toml` floors via `uv pip install --no-sources -e <local-dir>`. Version
  floors in dependent repos' pyproject.toml are irrelevant for VM-deployed services. After a UTL change, refresh
  tarballs (`--all`); after a Cloud Run code change (consolidator, DeFi collection, deployment-api), rebuild the Docker
  image instead.
- GCS sentinel-lock needs proactive stale cleanup. `if_generation_match=0` deadlocks against any preexisting blob; if
  you're copying the consolidator pattern, ensure the freshness check `blob.delete()`s before falling through to
  acquire.

## Notes (Phase 0 + 0.1 baseline — TBD)

Capture per-AG baseline + decision here so the team can see what each AG's path through the DAG was.

### Per-AG state table (fill in as Phase 0 + 0.1 runs)

| AG         | Phase 0: forward phantoms | Phase 0: missing rows | Phase 0.1: inverse-phantom rate | Decision (rebuild-first vs backfill-first) | Dominant drift axis |
| ---------- | ------------------------- | --------------------- | ------------------------------- | ------------------------------------------ | ------------------- |
| CEFI       | TBD                       | TBD                   | TBD                             | TBD                                        | TBD                 |
| TRADFI     | TBD                       | TBD                   | TBD                             | TBD                                        | TBD                 |
| SPORTS     | TBD                       | TBD                   | TBD                             | TBD                                        | TBD                 |
| PREDICTION | TBD                       | TBD                   | TBD                             | TBD                                        | TBD                 |
| DEFI       | TBD                       | TBD                   | TBD                             | TBD                                        | TBD                 |

### Phase 0 raw logs

```
# CEFI MTDS — /tmp/mtds-recon-cefi.log    (TBD — fill in after Phase 0 runs)
# TRADFI MTDS — /tmp/mtds-recon-tradfi.log (TBD)
# SPORTS MTDS — /tmp/mtds-recon-sports.log (TBD)
# PREDICTION MTDS — /tmp/mtds-recon-prediction.log (TBD)
# DEFI MTDS — /tmp/mtds-recon-defi.log    (TBD)
```

### Phase 0.1 inverse-audit CSVs

```
# /tmp/mtds-inverse-cefi.csv       (TBD)
# /tmp/mtds-inverse-tradfi.csv     (TBD)
# /tmp/mtds-inverse-sports.csv     (TBD)
# /tmp/mtds-inverse-prediction.csv (TBD)
# /tmp/mtds-inverse-defi.csv       (TBD)
```

### Phase 1.5 rebuild deltas (only if any AG was flagged)

| AG  | Pre-rebuild missing | Post-rebuild missing | Delta (rows recovered without download) | API spend avoided ($) |
| --- | ------------------- | -------------------- | --------------------------------------- | --------------------- |
| TBD | TBD                 | TBD                  | TBD                                     | TBD                   |

## Risks / blockers

- **Tardis quota** — heavy backfills can exhaust Tardis daily quota. Adapter pacing helps; avoid `--force` on large
  windows.
- **Databento contract-exceeded** — TRADFI singleton lock exists for this reason. Don't bypass.
- **Polymarket per-IP rate limit** — singleton lock + cursor-sharding (sibling plan Day 2) are the mitigations.
- **systemd-oomd on local machine** — if any phase ends up running locally instead of on VMs, watch RAM (cap ~80 GB).
  See sibling plan execution log for the 2026-05-04 incident.
- **Manifest consolidator outage** — per-VM shards stay un-merged; reader's 120s freshness fallback truncates to per-VM
  view. Daemon has a singleton lock; if it dies, relaunch ASAP.
- **Phantom drift axes not yet covered by `reconcile_phantom_manifest_rows_all.py`** — five known axes are encoded
  (hive-vocab, casing, empty instrument_type, path-prefix, chain-bundle equivalence). New axis = false-positive phantom
  flips. If post-flip phantom count is anomalous (>5% of captured), suspect a new drift axis and stop before re-running.
- **Inverse-audit (Phase 0.1) script has its own bug surface.** A false-positive inverse phantom sends an AG down a
  rebuild path that never lands; a false-negative leaves us re-downloading. Sanity-check via the [HUMAN] P1 step in
  Phase 0.1 (manually `gsutil ls` 5 random `inverse_phantom` rows) before trusting the numbers at scale.
- **Rebuild output silently dropped without `per_vm_shards=True`** — 2026-05-02 DeFi rebuild lost 80k rows compacted to
  12k canonical because of CAS contention with the consolidator. Always set `MANIFEST_PER_VM_SHARDS=true` on rebuild
  runs and force-merge after.
- **Cost-of-rebuild vs cost-of-redownload** — rebuilds list every parquet in the bucket; for buckets at scale that's
  millions of objects. Same-region VM keeps it tractable (~222 prefixes/sec), cross-region from laptop is 18× slower.
  Don't run rebuilds from a laptop on a non-trivial AG.

## Absorbed from sibling plans (2026-05-06)

- `cefi_phase2_gap_audit_2026_05_01` (archived) — 29 open todos / root-cause clusters A/B/C/D for CeFi 90,991
  attempted_failed rows. Superseded by this 2026-05-05 plan's fresh 30-finding audit + concrete F1-F30 fix list. The
  earlier audit's analysis survives as archive context; operational fix list lives here.
