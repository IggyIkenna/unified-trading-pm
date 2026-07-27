---
doc_type: issue
title:
  "CME combo/chain underlying= garbage (numeric 12/13/23 + garbled roots) — pre-existing extraction defect, 88%
  Databento-side"
summary:
  ~14.6K tradfi chain objects carry a non-resolvable underlying= (purely-numeric 12/13/23 or garbled 2-4-char fragments
  DB/XT/IB/…) with instrument_id NULL — legacy raw values baked in by an older writer/ingestion path, carried forward by
  the v9 migrator. 88% are batch_databento (9,974) vs 12% batch_massive (1,321), so the Massive purge does NOT fix it.
  These cannot resolve to a real product root, so they block canonical per-underlying bundling for combo/chains and are
  QUARANTINED (loud, never fake-canonicalized) by the canonical-path migration.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [canonical-id, underlying-extraction, combo, data-correctness, quarantine, databento]
related:
  [tradfi_canonical_path_migration_design_2026_07_19, databento_future_option_blank_instrument_id_shard_atom_2026_07_19]
created: 2026-07-19
priority: P1
parent_epic: tradfi_master
source: "Massive-removal scoping (workflow wlixucotm) + migration dry-run (mtds@e16705db), 2026-07-19"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
assigned_vm: planning
resolved_by: mtds@f645ea02+uac@7e179ae8 (recovery+guard, 2026-07-20); root-cause doc uac@8080b645+mtds@377dd90c
  (2026-07-26) # all 3 Remediation items now struck through/done; locked_by blocks archival — leave status/lock as-is
---

# CME combo/chain `underlying=` garbage — pre-existing extraction defect

## Finding

The full physical enumeration + manifest analysis found tradfi chain objects whose `underlying=` partition value is
**not a real product root**:

- **Purely-numeric**: `underlying=12`, `13`, `23` (literal GCS folders, e.g.
  `…/instrument_type=combo/data_type=ohlcv_1m/underlying=12/ticks.parquet`).
- **Garbled 2-4-char fragments**: `DB`, `XT`, `IB`, `BX`, `3P`, `C12`, `CSG`, `GT`, `CO`, `3C`, `HO`, `IC`, `SG`, `GN`,
  `VT`, `CRR`, `BO`, `ST`, `CGN`, `RR`, `3W`, … — not CME product roots.
- **`instrument_id` is NULL** on every one of these rows — they were never resolved to a canonical instrument.

**Scope (venue=CME only):** purely-numeric-underlying rows = **9,974 `batch_databento` + 1,321 `batch_massive`** (~88% /
12%). The migration's disposition classifier tags the broader class (numeric + empty underlying) as
`QUARANTINE_GARBAGE_UL` = **14,633 objects** on the full 2.73M-object corpus.

## Why it exists (not current code)

The current `market_tick_data_service/engine/orchestrator/symbol_rules.py::_extract_underlying` (combo branch: split on
`-`, match `_CME_ROOT_PATTERN`/`_CEFI_UNDERLYING_PATTERN` on the first leg) returns `""` (empty) — NOT a numeric string
— for an unparseable symbol. So a bare `"12"` is a **pre-existing raw value** from an older writer/ingestion path,
before today's `databento_classifier.py` symbol-text combo parsing existed. The v8→v9 migrator
(`scripts/migrate_tradfi_to_v9_canonical.py`) **carries the `underlying=` value forward verbatim** (does not recompute),
so the garbage survives migrations rather than being freshly written.

## Why the Massive purge does NOT fix it

88% (9,974 of 11,295 numeric-underlying rows) are `batch_databento`, NOT Massive. Purging `pipeline_mode=batch_massive/`
removes only the 12% Massive slice. The Databento-side majority is a separate, larger, pre-existing
underlying-extraction / legacy-garbage defect that this ticket owns.

## Impact

Blocks the operator's canonical per-underlying-bundle ruling for FUTURE/OPTION/combo: a bundle keyed on `underlying=12`
can never resolve to a real canonical id (`CME:...:<ROOT>-USD@LIN`). The canonical-path migration (`mtds@e16705db`) does
the SAFE thing — it QUARANTINES these to a `_quarantine/` prefix (never deletes, never fake-canonicalizes into a "real"
bucket). But they remain uncanonicalized until the root can be recovered.

## Remediation (needs its own work — NOT fixed by the migration or the Massive purge)

1. ~~**Recover the real root from CONTENT** where possible: the per-row leg symbols / instrument metadata inside the
   parquet may carry a resolvable human ticker (e.g. `ESM4-ESU4` → `ES` → `SP500`). Re-derive via
   `unified_api_contracts/external/databento/databento_classifier.py` combo logic; rewrite `underlying=` + populate
   `instrument_id`.~~ **DONE 2026-07-20** —
   `market-tick-data-service/scripts/recover_tradfi_garbage_underlying_2026_07.py` (mtds@f645ea02):
   content-authoritative recovery pass — categories B/C (named-spread + newly-recognised real roots) kept in place,
   category D (options `underlying=E` / root-qualified UD) rebundled under the CONTENT-recovered real root, category A
   (numeric/opaque UD with no recoverable root) quarantined + `attempted_failed`.
2. ~~**Root-cause the older writer/ingestion path** that stamped numeric `underlying` so no NEW data reproduces it (the
   write-time canonical guard added in the chain shard-atom change should REJECT a numeric/empty `underlying=` on a
   tradfi chain write — fold that rule in).~~ **DONE 2026-07-26** (root-caused + verified guard already covers combo,
   not just chain). Root cause: `classify_databento_symbol`'s CBOE `UD:1V:` regex was widened (`mtds@c4dc28b4451da`,
   2026-04-18) from `[A-Z]{2,4}` to `[A-Z0-9]{1,4}` to accept CBOE's numeric Globex strategy codes — with NO downstream
   check that the captured code resolved to a real product root, so every numeric (`12`/`13`/`23`) or opaque-alpha
   (`GN`/`VT`/`3W`) UD combo was stamped verbatim as `underlying=` for ~3 months until the fix below. That fix
   (2026-07-20, `mtds@f645ea02` + `uac@7e179ae8`) already closed the gap at BOTH layers: `_classify_row`
   (`market-tick-data-service/.../databento_enrichment.py`) drops the row when
   `is_recognized_tradfi_underlying(underlying)` is `False`, AND the write-time
   `canonical_path_violations`/`_tradfi_path_violations` guard (`unified-api-contracts/.../partition_paths.py`)
   independently rejects any leftover/future numeric-or-empty `underlying=` at the GCS-path level — covering BOTH chain
   (`futures_chain`/`options_chain`) and `combo` bundles (verified: `_get_writer` in
   `market_tick_data_service/engine/orchestrator/partitioned_writer.py` calls the guard unconditionally for every tradfi
   write, not just chain types). Existing regression tests already prove numeric/empty rejected + a valid root passing:
   `tests/unit/test_partitioned_writer_tradfi_filename_canonical.py::test_tradfi_chain_numeric_underlying_write_raises`
   - `::test_assert_canonical_chain_path_rejects_numeric_and_empty_underlying` (MTDS),
     `tests/unit/test_partition_path_is_canonical.py::test_tradfi_chain_numeric_underlying_rejected` +
     `::test_tradfi_combo_opaque_ud_underlying_rejected` (UAC). Dated root-cause comments added at the classifier call
     site (`uac@8080b645`) and the enrichment call site (`mtds@377dd90c`) documenting this history in place, per
     `plans/active/tradfi_satellite_ao_dispatch_batch3_2026_07_26.md` item 4.
3. **Truly-unrecoverable rows** (numeric ID with no resolvable content) → keep in `_quarantine/` + record
   `attempted_failed` in the manifest (honest absence), never silently dropped. **DONE** — same 2026-07-20 recovery pass
   (item 1) quarantines category A (genuinely unrecoverable) with `attempted_failed`.

## Cross-refs

- Migration design + disposition map: `tradfi_canonical_path_migration_design_2026_07_19.md` (QUARANTINE_GARBAGE_UL).
- Executor (quarantines these): `market-tick-data-service/scripts/migrate_tradfi_canonical_2026_07.py`.
- Extraction SSOT: `market_tick_data_service/engine/orchestrator/symbol_rules.py::_extract_underlying`.
- Combo classifier: `unified_api_contracts/external/databento/databento_classifier.py`.
