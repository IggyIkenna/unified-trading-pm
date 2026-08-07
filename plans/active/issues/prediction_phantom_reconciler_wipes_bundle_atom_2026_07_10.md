---
doc_type: issue
title:
  "Phantom-manifest reconciler wipes ~15,769 legitimately-captured prediction bundle-atom cells to attempted_failed — it
  has no bundle-aware existence check (synthetic cqg instrument_id has no on-disk path segment)"
summary:
  "Read-only diagnosis of the live pred-prd _index (760,300 rows, 2026-07-10) found ZERO rows anywhere with
  data_type=prediction_canonical_question_group at capture_status=captured — all 71,767 bundle rows are
  empty_confirmed/attempted_failed/expected_unattempted. Root cause traced against live GCS + live code: the
  phantom-manifest reconciler (unified_trading_library/reconcile/manifest.py, _PHANTOM_ERROR_REASON, lifted from
  instruments-service/scripts/reconcile_phantom_manifest_rows_all.py) assumes a PER-OBJECT row-key where instrument_id
  maps to a real GCS path segment. But the v9 prediction bundle atom's instrument_id is a SYNTHETIC
  canonical_question_group label (e.g. BTC_UP_DOWN_DAILY) that never appears as a path segment — the raw objects are
  per-cid `trades` parquets, and NO `data_type=prediction_canonical_question_group/` folder exists on disk by design
  (the bundle is a manifest-only atom, cluster-validated at write time, not object-existence-validated). So the phantom
  prober finds 'no object at canonical path' for EVERY bundle row and demotes 100% of them to
  attempted_failed[phantom_captured_no_parquet_at_canonical_path]. Net: ~15,769 legit captured bundle cells (7,278
  POLYMARKET + 8,491 KALSHI) were wiped. Verified: a real per-cid object parses+classifies to cqg=BTC_UP_DOWN_DAILY,
  envelope resolves, row_count=500 — the rebuild wrote it captured, then the reconciler (written_at
  2026-06-27T09:36:17Z) demoted it. This is the PRIMARY driver of the prediction _index residual, and it falsifies the
  earlier working hypothesis that the schema_version=4 legacy rows are 'superseded by an existing v9 captured bundle' —
  there is NO captured v9 bundle row for any date to supersede them."
status: open
nature: notes
asset_group: [prediction]
stage: [data, meta]
repos: [unified-trading-library, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [manifest, phantom-reconciler, bundle-atom, data-correctness, prediction, canonicalisation, cross-repo]
related: [
    plans/archive/2026_07/prediction_manifest_canonicalisation_2026_06_01.md, # (was: plans/active/... — corrected
    # 2026-07-14, doc-reconciliation finding 175: folded into M-1 + archived 2026-07-13, path no longer resolves)
    plans/archive/2026_07/downstream_services_manifest_canonicalisation_2026_06_01.md, # (was: plans/active/... —
    # same 2026-07-13 fold-in/archive, corrected alongside finding 175)
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-10
author: unknown
parent_epic: mtds_mdps_master
priority: P0
assigned_vm: planning
resolved_by:
locked_by:
source:
  - /autonomous prediction _index residual root-cause diagnosis 2026-07-10 (read-only, live prod GCS
    central-element-323112)
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    unified-trading-library/unified_trading_library/reconcile/manifest.py,
    instruments-service/scripts/reconcile_phantom_manifest_rows_all.py,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_prediction_manifest.py,
    unified-api-contracts/unified_api_contracts/registry/possible_manifest.py,
  ]
---

# Phantom reconciler wipes prediction bundle-atom captured cells (bundle-atom blind spot)

> **Surfaced by the /autonomous prediction `_index` residual root-cause diagnosis (2026-07-10, read-only against live
> prod GCS `central-element-323112`).** Operator-notify-required (data-correctness / cross-repo / contradicts stated
> hypothesis). No prod writes were made during diagnosis.

## The bug (root cause)

The phantom-manifest reconciler demotes a `captured` manifest row to
`attempted_failed[phantom_captured_no_parquet_at_canonical_path]` when it cannot find a GCS object at the row's
canonical path. Its path-existence check (`unified_trading_library/reconcile/manifest.py`, five drift axes: hive-vocab,
instrument_type casing, empty-schema-4, path-prefix, chain-bundle) assumes `instrument_id` is a **per-object** key that
maps to a real path segment.

The v9 prediction **bundle atom** breaks that assumption: its `instrument_id` is a **synthetic
`canonical_question_group`** (e.g. `BTC_UP_DOWN_DAILY`), `data_type=prediction_canonical_question_group`,
`instrument_type=prediction`. The raw objects on disk are per-`conditionId` `data_type=trades` parquets; there is **no**
`data_type=prediction_canonical_question_group/` folder — the bundle is a **manifest-only atom**, validated at
write-time by cluster validation (`observed_clusters={market_id: rows}`), NOT by object existence. So the phantom prober
can never match an object for any bundle row → demotes **100%** of them.

**Impact (measured on the live `_index`):** ZERO `data_type=prediction_canonical_question_group` rows at `captured`
across the whole corpus; ~**15,769** legit captured bundle cells (7,278 POLYMARKET + 8,491 KALSHI) wiped to
`attempted_failed`. This is why E7 CF-verify cannot go GREEN and why the schema_version=4 legacy per-instrument rows may
be the only surviving manifest evidence of real activity for those days.

## Secondary gap (smaller)

The rebuild's canonical-path regex `_CANONICAL_PRED_RE`
(`market_tick_data_service/scripts/rebuild_prediction_manifest.py`) silently drops an older-migration object layout
shaped `venue=…/chain=POLYGON/instrument_type=prediction_market/…/underlying=BTC/…parquet` (~3.3% of objects on the
sampled day) — `parse_canonical_prediction_path` returns `None` for that shape. Not the primary driver, but a real
coverage gap.

## Remediation (ordered — DO NOT purge legacy rows until step 1+2 land)

1. **[CODE, P0, base-tier — blast-radius-gated] Make the phantom reconciler bundle-aware.** In
   `unified_trading_library/reconcile/manifest.py` (+ the IS wrapper `reconcile_phantom_manifest_rows_all.py`): EXEMPT
   bundle-atom data_types (`prediction_canonical_question_group`, and any manifest-only bundle atom) from the
   object-at-canonical-path existence check — their existence is proven by write-time cluster validation, not a path
   segment. Prefer a principled exemption keyed on "manifest-only bundle atom" (mirror the existing `schema_version=4`
   skip pattern), NOT a prediction-only hack. **HARD (rule 11): this reconciler runs against ALL asset groups' manifests
   — verify the exemption does not weaken phantom detection for cefi/tradfi/sports/defi (per-object atoms) before
   shipping; add a regression test that a bundle-atom captured row survives reconcile while a genuinely-phantom
   per-object row is still demoted.**
2. **[CODE, P1] Fix the rebuild `_CANONICAL_PRED_RE`** to also parse the
   `chain=/underlying=/instrument_type=prediction_market` older-migration object shape (or confirm those objects are
   superseded and should be dropped).
3. **[DATA, P0] Re-run `rebuild_prediction_manifest.py`** after 1+2 land → the ~15,769 real bundle cells re-emit as
   `captured`; then re-diagnose whether a captured v9 equivalent now exists per date before touching the legacy rows.
4. **[DATA] Then** re-evaluate the schema_version=4/5 legacy per-instrument rows (9,174), the 189 UNKNOWN/blank-venue
   rows, and the 17 blank-`data_type` phantom aggregate-markers — only after the captured bundle is restored (they may
   be the only evidence today).

## Safe-to-execute-NOW cleanups (independent of the phantom root cause)

- **124 lowercase `venue="kalshi"` duplicate rows** — 100% exact byte-identical collision with canonical
  `venue="KALSHI"` rows (same capture_status/pipeline_mode/source/error_reason, differ only in venue casing), zero
  object-backing on GCS. **Safe, idempotent, zero data-loss** → delete the 124 lowercase rows, keep the uppercase
  (pattern: `scripts/delete_tradfi_aggregate_phantom_markers_2026_07_07.py`). No sign-off needed.
- **27,292 `batch_polymarket_clob` blank-`source` rows** (`written_at ≤ 2026-06-29`, pre the
  `manifest_record_expected_empty_blank_source_2026_07_08` fix) — a rebuild CF-11 re-emit backfills
  `source=polymarket_clob` via the now-fixed `_stamp_producer_source`. Idempotent but heavy (rewrites the whole ~700K
  honest-absence corpus); a surgical direct-writer targeting just this filter is cheaper. (The 639,991 `live_*`
  blank-source rows are EXEMPT by design — producer-source is never back-stamped for live/replay pipeline_modes.)

## Update 2026-07-11 — E7 CF-verify final residual cleanup: steps 1-3 confirmed landed; Class A+C purged; NEW sibling gap found in Class B

> Read-only-then-targeted-write pass against the live prod `_index` (`market-data-tick-pred-prd-central-element-323112`,
> snapshotted first to `_index/snapshots/pre_final_cleanup_2026_07_11.parquet` and again to
> `_index/snapshots/pre_class_a_c_delete_20260711T064016Z.parquet` before any write). Scripts:
> `instruments-service/scripts/{snapshot,diagnose,purge}_prediction_index_*_2026_07_11.py`,
> `instruments-service/scripts/diagnose_class_b_object_existence_2026_07_11.py` (lifecycle: oneoff, delete after this
> cleanup's gate is confirmed GREEN).

**Remediation steps 1-3 above are CONFIRMED LANDED**: the bundle-atom reconciler exemption
(`MANIFEST_ONLY_BUNDLE_DATA_TYPES` in `unified_trading_library/reconcile/manifest.py`) is live and the prediction
manifest rebuild re-ran — the `_index` now holds **17,329 captured v9 `prediction_canonical_question_group` bundle
rows** (KALSHI 10,040 @ `source=kalshi`, POLYMARKET 7,289 @ `source=polymarket_clob`). The "zero captured v9 bundle rows
anywhere" finding from 2026-07-10 no longer holds.

**Class A (schema_version=4/5 legacy per-instrument rows) — RE-DIAGNOSED AND PURGED.** With the bundle now restored,
re-verified: **100% (6,760/6,760)** of the v4/v5 POLYMARKET `trades`/`prediction_trades` blank-`source` `captured` rows
have a same-date captured v9 POLYMARKET bundle row — fully superseded. Deleted via
`purge_prediction_index_final_residuals_2026_07_11.py --apply` (stop-on-surprise re-verified supersession + row-count
range immediately before delete; snapshot-then-write; post-delete gate confirmed 0 residual + captured count dropped by
exactly 6,760 + attempted_failed unchanged). This resolves remediation step 4's "re-evaluate the schema_version=4/5
legacy rows" for the 6,760/9,174 in this predicate (the remaining ~2,414 non-`captured` v4/v5-family rows, if any, were
not in scope of this delete — see gate numbers below).

**124 lowercase `venue="kalshi"` duplicate rows — PURGED** (safe-to-execute-NOW cleanup, unblocked). Re-verified 100%
exact-key match (date/data_type/capture_status/pipeline_mode/source/error_reason/underlying/instrument_type) against
canonical `venue="KALSHI"` rows, 0 `captured` among them, before delete. Same script/run as Class A above (single
combined write). `_index` now: 0 lowercase `kalshi` rows, 160,865 canonical `KALSHI` rows unchanged.

**NEW FINDING (Class B / the 13,292 phantom rows) — the `--unphantom-only` safe-recovery pass found 0 recoverable rows,
but sampled read-only verification shows this is NOT proof of genuine absence — it is a SIBLING gap to this file's root
cause, in the phantom-audit's OWN path-template registry.** `--unphantom-only --apply` (safe-by-construction,
phantom→captured only) ran clean and recovered 0/13,292 — confirmed via direct object-existence sampling (4 rows sampled
from each of the 4 (venue, data_type) phantom groups): **in 3 of 4 groups sampled, the EXACT `instrument_id` + `date`
HAS a real parquet object on GCS** — but only under `pipeline_mode=live_kalshi` / `pipeline_mode=live_polymarket_clob`,
a shape **NOT present** in `unified_api_contracts.canonical_path_templates('prediction')` (which only enumerates
`batch_kalshi` / `batch_polymarket_clob` / `batch_polymarket_gamma_api` / the legacy bare/`category=` shapes). Example
verified 1:1 match: manifest phantom row
`(date=2026-06-23, venue=KALSHI, data_type=book_snapshot_5, instrument_id=KALSHI:PREDICTION_MARKET:KXNASDAQ100-26JUN26H1600-B30750)`
↔ GCS object
`raw_tick_data/by_date/day=2026-06-23/pipeline_mode=live_kalshi/asset_group=prediction/venue=KALSHI/instrument_type=prediction_market/data_type=book_snapshot_5/KALSHI:PREDICTION_MARKET:KXNASDAQ100-26JUN26H1600-B30750.parquet`.
**This means the task's working assumption ("whatever stays attempted_failed is genuine honest-absence") is UNVERIFIED
and likely wrong for a large fraction of the 13,292** — the true genuine-vs-recoverable split cannot be established
until the registry gap is closed. Per CLAUDE.md's data-correctness/cross-repo/SSOT-contradiction big-finding rule this
is escalated to the operator (see the task's final report) rather than silently accepted as "fine, honest absence."

Separately (same sampling pass), a **provenance-mislabeling bug**: all 11,988 KALSHI-venue phantom rows carry
`pipeline_mode=batch_polymarket_clob` / `source=polymarket_clob` — POLYMARKET's provenance stamped on KALSHI rows
(`written_at` clustered at 2026-07-11T05:59-06:00Z, i.e. the just-completed rebuild). This does NOT affect the phantom
audit's own path probing (it tries every template regardless of the row's own `pipeline_mode` value) so it did not
change the Class-B recovery result above, but it is a live CF-4/CF-26 violation (wrong-vendor stamp, not a blank one —
so it passes the practical `audit_canonical_form.py` CF-4 check while still being wrong) that should be root-caused in
the rebuild writer (`market_tick_data_service/scripts/rebuild_prediction_manifest.py`) separately.

**Remediation for the new finding (not executed — out of scope for a residual-cleanup pass, requires the same rule-11
cross-AG regression rigor as the original bundle-atom fix)**:

5. ✅ **[CODE, P1] Add `pipeline_mode=live_kalshi` / `live_polymarket_clob` / `live_polymarket_gamma_api` prefix
   shapes** to the prediction entries in `unified_api_contracts.registry.possible_manifest` (CF-15 SSOT,
   `canonical_path_templates`) so the phantom-audit's `--unphantom-only` pass can actually distinguish
   genuinely-batch-absent from batch-absent-but-live-captured. **HARD (rule 11, same as remediation step 1)**: verify
   this does not weaken phantom detection for other AGs before shipping (the registry is shared cross-AG); confirm
   whether a BATCH manifest row should legitimately be satisfied by LIVE-only evidence (semantics question — a BATCH row
   tracks BATCH backfill completeness specifically; unioning it with LIVE evidence may misrepresent BATCH-path health
   per-se, even though CF-12 batch=live symmetry says the CELL has data either way). Re-run `--unphantom-only --apply`
   after landing; whatever remains attempted_failed AFTER that is the first defensible "genuine honest-absence" number
   for Class B.
   - ✅ **CODE-RESOLVED — `unified-api-contracts@e7ed754e`** ("feat(prediction): af_fixture_id InstrumentRecord fields +
     8 Kalshi aliases + live-mode path-templates (union)"). **Operator decided UNION (2026-07-18)**: a BATCH prediction
     manifest row IS legitimately satisfied by LIVE-only object evidence (CF-12 batch=live cell symmetry), so all three
     `live_*` shapes are now enumerated for prediction. Implemented as a PREDICTION-SCOPED extra live-probe
     (`possible_manifest._EXTRA_LIVE_PROBE_SOURCES_BY_AG`): `live_kalshi` / `live_polymarket_clob` were ALREADY emitted
     by the capability-derived batch+live loop (both LIVE-capable); `live_polymarket_gamma_api` is added as a probe
     prefix **without** claiming gamma_api is live-capable — `SOURCE_MODE_CAPABILITY` keeps it BATCH-only ("market
     metadata; not a tick series"), so the shared `PipelineMode` enum + capability matrix stay honest (no
     `LIVE_POLYMARKET_GAMMA_API` member fabricated). **RULE 11 VERIFIED cross-AG**: cefi/tradfi/defi/sports
     pipeline_mode template counts are byte-for-byte unchanged (16/6/15/0) and `live_polymarket_gamma_api` appears ONLY
     in prediction; regression tests `tests/unit/test_possible_manifest.py`
     (`test_prediction_union_live_prefixes_enumerated`, `test_prediction_live_union_is_prediction_scoped_only`,
     `test_prediction_templates_have_no_duplicate_prefixes`). Per the module's own invariant, adding a probe prefix can
     only REDUCE false-demotion, never introduce one. The `--unphantom-only --apply` re-run against the live prediction
     corpus is the held Phase-B DATA re-emit (a data op, not a UAC code task).
6. **[CODE, P2] Root-cause the KALSHI→`batch_polymarket_clob`/`polymarket_clob` provenance mislabel** in
   `rebuild_prediction_manifest.py`'s writer (a stale/carried-over loop variable is the leading hypothesis given the
   clustered `written_at`); fix at the write site, not via a manifest patch.
   - ✅ **CODE-RESOLVED — `market-tick-data-service@3397e7ae`** ("rebuild_prediction_manifest venue-resolves bundle
     pipeline_mode/source per-venue (was hardcoding POLYMARKET, mis-stamping Kalshi)"). Current write site stamps
     `derive_pipeline_mode_for_row(venue, "prediction", …)` → Polymarket→`polymarket_clob`, Kalshi→`kalshi` (rebuild
     script L543-560). Verified live 2026-07-18 (slot-2, prediction close-out §6, independent git-log + code read). The
     ~11,988 HISTORICAL mislabeled rows self-correct on the next `rebuild_prediction_manifest.py` run — that DATA
     re-emit is part of the held Phase-B prediction migration, not a separate code task.

## Todos (migrated 2026-07-26 from `prediction_satellite_ao_dispatch_batch3_2026_07_26.md` at archival)

`/plans/archive/2026_07/prediction_satellite_ao_dispatch_batch3_2026_07_26.md`'s finalize plan archived that doc; this
todo was its own remaining `[OPERATOR]` residual close-out, migrated here (this doc's own source) rather than left
stranded in `plans/archive/` where the backlog regen (active-plans-only) would never surface it again.

- [x] ✅ [SCRIPT] P1. **Combined residual close-out — all 4 sub-items landed (2026-07-27, slot-11), read-only live
      re-diagnosis found the manifest already MUCH further ahead than this todo's stated baseline (written 2026-07-26
      against a snapshot from the 2026-07-11 close-out).** Fresh full-index read of
      `market-data-tick-pred-prd-central-element-323112`'s `_index/availability_index.parquet` (783,556 rows,
      re-downloaded live, not a cached/prior-session count): - **(a) blank/UNKNOWN-venue rows — ALREADY RESOLVED, 0
      remain.** `df["venue"].value_counts()` shows exactly TWO distinct values across the entire manifest — `POLYMARKET`
      (584,219) and `KALSHI` (199,337) — zero nulls, zero blanks, zero `UNKNOWN`. The 189 rows this todo described are
      gone (superseded by a full rebuild since 2026-07-11, not purged by this task). Nothing to diagnose or delete —
      explicit non-actionable ruling: already clean. - **(b) ~2,414 remaining schema_version=4/5 rows — ALREADY
      RESOLVED, 0 remain.** `df["schema_version"]` is **100% `9`** across all 783,556 rows — no v4/v5 rows of ANY
      `capture_status` exist anywhere in the manifest (not just the non-captured remainder this todo flagged). Confirms
      a full v9 rebuild superseded the entire legacy schema family since the 2026-07-11 partial purge. Nothing to purge
      — explicit non-actionable ruling: already clean. - **(c) Class-B phantom re-validation — RE-RUN, 0 additional
      recoverable, but the base count already collapsed from 13,292 → 51 before this task ran.** `attempted_failed` rows
      carrying `error_reason=phantom_captured_no_parquet_at_canonical_path` are now only **51** (down 99.6% from this
      todo's cited 13,292 — a prior rebuild/reconcile pass already recovered the vast majority independently of this
      specific todo). Ran
      `reconcile_phantom_manifest_rows_all.py --asset-group prediction --unphantom-only       --dry-run` live against
      the 51: re-validated 51/51 — **0 unphantomed** ("Still phantom: 51 ... Unphantomed: 0 ... Manifest is clean"),
      i.e. all 51 genuinely have no parquet at ANY UAC candidate path (including the
      `live_kalshi`/`live_polymarket_clob`/`live_polymarket_gamma_api` union this todo's remediation step 5 added).
      Skipped the real (non-dry-run) write since dry-run already proved it would be a no-op (0 rows to flip) —
      re-running for a guaranteed-identical 0-row write adds no evidence. **First defensible genuine-honest-absence
      count for Class B: 51** (not 13,292 — that number was already stale before this task started). - **(d) KALSHI
      provenance mislabel — the SPECIFIC defect this todo describes (captured rows) is CONFIRMED FIXED, 0 remain; but
      live-probing surfaced a materially larger, DIFFERENT residual, filed as a new todo, not fixed here.** Queried
      `venue=KALSHI` rows whose `pipeline_mode`/`source` still says polymarket: **0 rows** have
      `capture_status=captured` — the exact defect `market-tick-data-service@3397e7ae` (landed 2026-07-10) was written
      to fix has fully self-corrected via subsequent rebuild runs, satisfying this sub-item's stated "verify... expect
      0" literally. However the SAME query across ALL `capture_status` values returns **129,227** rows (not the ~11,988
      this todo cited) — nearly all (128,349) `empty_confirmed` scaffold rows dated as far back as 2018 (years before
      Kalshi's real launch), i.e. NOT the captured-row-at-write-time bug this todo/fix targeted, but an apparently older
      and much larger mislabeling in the coverage-scaffold/expected-row enumeration path (`ManifestWriter`'s
      expected-row seeding, not the rebuild's per-capture write site). Filed as a new P2 todo below rather than fixed
      inline — different code path, needs its own root-cause read, out of this residual-cleanup todo's stated scope
      (which was specifically the captured-row provenance defect, now verified 0). **No writes were needed for any of
      the 4 sub-items** (a/b: already 0 rows to purge; c: dry-run proved a real write would be a no-op; d: the specific
      defect is already 0, the newly-found adjacent issue needs its own investigation before any write) — so the
      reversibility pre-clearance above was not exercised. Repo: market-tick-data-service / instruments-service
      (read-only verification only, no code shipped this task).
- [x] ✅ [DATA] P2. **market-tick-data-service** — investigate the KALSHI-venue scaffold-row provenance mislabel
      surfaced by the P1 close-out above: 129,227 `market-data-tick-pred-prd-central-element-323112` rows carry
      `venue=KALSHI` with `pipeline_mode`/`source` stamped `polymarket_clob`/`polymarket_gamma_api` (128,349
      `empty_confirmed`, 828 `expected_unattempted`, 50 `attempted_failed`; 0 `captured` — this is NOT the captured-row
      defect `market-tick-data-service@3397e7ae` already fixed), spanning dates back to 2018 (pre-dating Kalshi's real
      launch), across `trades`/`book_snapshot_5`/`prediction_canonical_question_group`/ `market_lifecycle` data_types.
      Root-cause where these scaffold/expected rows are seeded (likely the manifest's expected-row enumerator, not
      `rebuild_prediction_manifest.py`'s per-capture write site) and correct the provenance stamp at the write site,
      then re-emit or directly correct the historical rows following the same snapshot-then-write, stop-on-surprise
      precedent as this doc's prior purges. — instruments-service@afdb1ad6 + market-tick-data-service@ce275975 +
      evidence in "Update 2026-08-03" below.
- [x] ✅ [DATA] P3. (found while fixing the todo above) **instruments-service** — audit
      `enumerate_expected_universe.py`'s `_derive_pm_source_transport` for the SAME bug class (venue-blind
      `SOURCE_PRIORITY[0]` stamping) against every OTHER `_VENUE_OVERRIDES` venue outside `asset_group="prediction"`
      (e.g. `tradfi` FRED/ECB/OFR/IBKR, `defi` CHAINLINK/PYTH/AAVE/SOLANA_RPC/HELIUS) — spot-checked live 2026-08-03:
      `_derive("tradfi", "ohlcv_1d", venue="IBKR")` currently returns `batch_fred`/`fred` (wrong — should be
      `batch_ibkr`/`ibkr` per the venue override), an untouched sibling instance of this exact defect, out of scope for
      this P2's prediction-only fix (rule-11 cross-AG verification not yet run for those asset_groups). Verify + fix at
      the source, then backstamp affected historical rows following this todo's
      `restamp_prediction_kalshi_scaffold_     provenance_2026_08_03.py` precedent. — instruments-service@2b165597 + QG
      green (5207 passed), generalized `if ag == "prediction" and venue` → `if venue` so ALL _VENUE_OVERRIDES venues
      resolve correctly. Affected: tradfi (IBKR/ECB/OFR/YAHOO/EIA), cefi (HYPERLIQUID/ASTER/EXTENDED_STARKNET), defi
      (CHAINLINK/PYTH/AAVE/SOLANA_RPC/HELIUS). 6 new unit tests + 5 regenerated golden fixtures. Backstamp of historical
      rows is a follow-on data operation (per-asset_group restamp scripts per the Kalshi precedent).

## Update 2026-07-27 (slot-16) — combined residual-row diagnosis (batch2 todo): both sub-items already resolved, 0 rows to purge/backfill

> Read-only live re-diagnosis against `market-data-tick-pred-prd-central-element-323112`'s
> `_index/availability_index.parquet` (786,644 rows, fresh single-walk read — not cached), per
> `plans/archive/2026_07/prediction_satellite_ao_dispatch_batch2_2026_07_25.md`'s "Combined residual-row diagnosis"
> todo. Script: `instruments-service/scripts/diagnose_blank_data_type_and_polymarket_source_residuals_2026_07_27.py`
> (lifecycle: oneoff, delete after this diagnosis's gate is confirmed GREEN). No writes were made — both predicates
> measured 0 rows, so the snapshot-then-write purge/backfill machinery was never exercised.

- **(a) 17 blank-`data_type` phantom aggregate-marker rows — ALREADY RESOLVED, 0 remain.** `df["data_type"]` has exactly
  5 distinct values across all 786,644 rows (`book_snapshot_5`, `trades`, `prediction_canonical_question_group`,
  `prediction_trades`, `market_lifecycle`) — zero nulls, zero blank strings. The 17 rows this todo described are gone
  (superseded by a subsequent full manifest rebuild — the same pattern as the 2026-07-26/07-27 `slot-11` finding that
  the 189 blank/UNKNOWN-venue rows and the 2,414 v4/v5 rows had already self-resolved via later rebuilds). Nothing to
  diagnose or purge — explicit non-actionable ruling: already clean.
- **(b) `batch_polymarket_clob` blank-`source` rows — ALREADY RESOLVED, 0 remain.** Of 711,544 live
  `pipeline_mode=batch_polymarket_clob` rows, 100% carry `source=polymarket_clob` — zero nulls, zero blank strings. This
  confirms the 2026-07-19 `canonicalize_prediction_manifest_2026_07_18.py --dry-run` measurement (2, down from the
  source issue's original 27,292 on 2026-07-10) has since fully closed to 0 via subsequent rebuild/canonicalize passes.
  No backfill needed — explicit non-actionable ruling: already resolved.

Both sub-items of the combined todo are confirmed closed by live measurement; no code/data change was required beyond
the diagnostic script itself (kept for lifecycle-marker traceability, delete-when as declared in its header).

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (5 entries).
- **data_engineering 2026-08-03 (slot-2)**: closed todo 3 (KALSHI scaffold-row provenance mislabel). Root-caused to
  `instruments-service/scripts/enumerate_expected_universe.py`'s `_derive_pm_source_transport` — it took
  `SOURCE_PRIORITY[("prediction", data_type)][0]` (Polymarket-first) unconditionally instead of venue-resolving, so
  every KALSHI scaffold row was stamped with Polymarket's provenance. Fixed by venue-resolving via
  `derive_pipeline_mode_for_row` FIRST for `asset_group="prediction"` (its `_VENUE_OVERRIDES["KALSHI"] == BATCH_KALSHI`,
  the same table the already-fixed real capture writer uses) — provable safe superset for POLYMARKET rows and every
  other asset_group (unreachable branch there); 5 new unit tests. `instruments-service@afdb1ad6` (corrected 2026-08-03
  from a mis-stated "13" per review spot-check msg #3572 — `afdb1ad6` adds 5, the mtds restamp commit `ce275975` below
  adds 12, so 17 total across both, independently re-counted from the diffs). Then backstamped the live corpus via a new
  `market-tick-data-service/scripts/restamp_prediction_kalshi_scaffold_provenance_2026_08_03.py` (additive per-VM-shard
  write — race-free vs the live per-minute consolidator, since `pipeline_mode`/`source` aren't consolidator dedup-key
  columns): dry-run measured 12,006 live target rows (this todo's originally-cited 129,227 had already collapsed via
  unrelated ongoing corpus maintenance — same churn pattern as this doc's earlier "Class-B... 13,292 -> 51" finding), 0
  captured (confirms scope is disjoint from the already-fixed captured-row defect), applied, consolidator-merge verified
  clean (0 residual mismatched KALSHI rows) 2026-08-03T17:1x. `market-tick-data-service@ce275975` (+`d3260d2f` dropping
  2 unneeded `# type: ignore` the precedent script's pattern didn't actually need here since basedpyright's
  `include=["market_tick_data_service"]` never typechecks repo-root `scripts/`). Also found + fixed a PRE-EXISTING,
  unrelated repo-wide QG false-positive blocking ship (`market-tick-data-service@5893ae3e`): STEP 5.95's naive
  `# type: ignore` text-count ratchet was tripped by a docstring in `scripts/pipeline_e2e_check.py` merely _mentioning_
  the phrase in prose (landed 2026-08-03 in `bccb95ea`, after the 2026-07-30 ratchet freeze) — rephrased, no behavior
  change. Filed a new P3 todo above for the sibling bug class in OTHER `_VENUE_OVERRIDES` venues (spot-checked live:
  `tradfi`/IBKR currently mis-stamps `batch_fred` — out of this P2's scope, needs its own rule-11 cross-AG
  verification).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

## Follow-ups

- [ ] [DATA] P3. Backstamp historical rows for affected non-prediction venues (tradfi IBKR/ECB/OFR/YAHOO/EIA, cefi
      HYPERLIQUID/ASTER/EXTENDED_STARKNET, defi CHAINLINK/PYTH/AAVE/SOLANA_RPC/HELIUS) via per-asset_group restamp
      scripts per the Kalshi precedent

> **2026-08-06 archive-candidate audit**: The [DATA] P3 todo fixed enumerate_expected_universe.py
> (instruments-service@2b165597) but its own completion says 'Backstamp of historical rows is a follow-on data
> operation' - a deferred follow-up not turned into its own todo
