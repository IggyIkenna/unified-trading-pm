---
doc_type: issue
title:
  "UTL `rebuild_manifest_from_canonical_paths()` wholesale-REPLACES a bucket's ENTIRE consolidated manifest index when
  called with a sub-prefix, on buckets that co-locate multiple services' data — silently destroys the OTHER services'
  manifest rows"
summary: >-
  Found while working data_pipeline_check_mdps_features_2026_07_20.md todo 11 (cross-repo orphan/lineage audit).
  `unified_trading_library.manifest_writer.rebuild_manifest_from_canonical_paths()` builds its output DataFrame purely
  from the GCS blobs discovered under the given `prefix` (plus fresh per-VM shards), then uploads that DataFrame as the
  bucket's SOLE consolidated `_index/availability_index.parquet` — it never merges in existing rows for content outside
  `prefix`. On the market-data-tick-{ag}-prd buckets, `raw_tick_data/` (MTDS) and `processed_candles/` (MDPS) are
  CO-LOCATED in the SAME bucket sharing ONE consolidated index. A prefix-scoped call therefore silently WIPES every
  manifest row for the other prefix's data. Two live risk sites found: (1) a currently-open, not-yet-executed
  reconciliation todo that recommends exactly this unsafe call for CEFI candles (would delete ~10M+ MTDS raw-tick rows
  to backfill a much smaller candle-orphan set — CAUGHT before execution, todo corrected below); (2) an existing
  PERMANENT-lifecycle script (`market-tick-data-service/scripts/rebuild_mtds_manifest.py --from-canonical`) that has the
  identical bug shape and is callable at any time (would silently delete every MDPS candle-manifest row sharing the
  bucket). The SAFE, additive sibling function `rebuild_manifest()` already exists in the same module and does the right
  thing (merges with existing, only adds missing keys) — the fix is to route both call sites through it, or teach
  `rebuild_manifest_from_canonical_paths` to preserve out-of-prefix existing rows.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, prediction]
stage: [data]
repos: [unified-trading-library, market-tick-data-service, market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: [data-correctness, manifest, gcs, mdps, mtds, candle, orphan, data-loss-risk, operator-notify]
related:
  [
    /plans/active/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: advance-code
source: >-
  Surfaced 2026-07-27 (slot-12, infra) while scoping how to execute
  mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md's recommended reconciliation for
  data_pipeline_check_mdps_features_2026_07_20.md todo 11 (cross-repo orphan/lineage audit + migrate to zero orphans).
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# `rebuild_manifest_from_canonical_paths()` wholesale-replaces a shared bucket's manifest on a sub-prefix call

> **🟥 OPERATOR-NOTIFY (data-correctness, cross-repo, potential mass data loss — not yet executed).** No manifest has
> actually been wiped by this — the specific unsafe invocation was caught during scoping, before any VM launched. This
> doc exists so it is never invoked as originally spec'd, and so the one already-shipped script with the same shape
> (`rebuild_mtds_manifest.py --from-canonical`) is not run in this bucket layout until fixed.

## What I found

`rebuild_manifest_from_canonical_paths()`
(`unified-trading-library/unified_trading_library/manifest_writer/_maintenance.py:502-690`):

1. Lists every `.parquet` blob under the caller-given `prefix` only.
2. Parses `(day, venue, chain, instrument_type, data_type)` from each path into `discovered`.
3. Builds `rebuilt = pd.DataFrame(records)` **from `discovered` alone** — `existing` (the full current manifest, read at
   the top of the function) is used ONLY for the diagnostic `drift_report`, never merged into `rebuilt`.
4. Merges in `fresh_shards` (very recent, not-yet-consolidated per-VM shards) — not the full existing index.
5. Uploads `rebuilt` to `_mw.ManifestWriter._INDEX_PATH` — **the bucket's single, whole-bucket consolidated
   `_index/availability_index.parquet`**, confirmed via grep (`_read_index.py`, `_maintenance.py` — every
   `read_availability_index()` caller reads this exact same path, unfiltered by prefix).

**Net effect**: calling this function with `prefix` scoped to a FRACTION of a bucket's real content REPLACES the whole
bucket's manifest with only that fraction — every manifest row for content outside `prefix` is silently deleted from the
index (the underlying GCS objects are untouched; only their manifest visibility is destroyed — `honest coverage`,
`data-status`, and every skip-if-fresh check for that bucket would then read those shards as `expected_unattempted`).

**Why this matters here specifically**: the `market-data-tick-{cefi,defi,tradfi,prediction}-prd` buckets are CO-LOCATED
— `raw_tick_data/by_date/...` (written by market-tick-data-service) and `processed_candles/by_date/...` (written by
market-data-processing-service) share ONE bucket and ONE consolidated index. Any call scoped to only one of those two
prefixes wipes the other's rows.

## The docstring is misleading, not wrong on its own terms

The docstring says "Safe to run post-migration to realign the manifest with GCS reality" — true ONLY if `prefix` is
guaranteed to cover the bucket's ENTIRE manifested content (e.g. a bucket dedicated to one service/prefix). It is FALSE,
and silently destructive, on any bucket shared by multiple prefixes/services — which is exactly this codebase's real
layout for the tick buckets. Nothing in the function signature, docstring, or call site enforces or even checks this
precondition.

## Two live risk sites

1. **`plans/active/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`** (still open, not yet
   executed) recommends exactly this unsafe call:
   `rebuild_manifest_from_canonical_paths(bucket, service_name="market-data-processing-service", prefix="processed_candles/by_date")`
   for the CEFI candle bucket, to backfill an estimated small number of OOM-era-orphaned candle manifest rows. As
   written this would instead **delete essentially the entire CEFI raw-tick manifest** (per this session's own
   measurement of a sibling bucket, DEFI carries millions of `market-tick-data-service` rows in the same index) to fix a
   defect affecting a comparatively tiny number of candle shards — a wildly disproportionate, catastrophic, and silent
   outcome. **Corrected in that doc's own recommended-fix section (see this doc's todo 1).** Confirmed:
   `backfill_orphan_class_e.py`'s VM-launch gating docs / this task's own "safe-idempotent justification, no
   `[OPERATOR]` tag needed" claim is **WRONG** for this specific call — it needs re-justifying against the corrected
   (additive) function or an explicit `[OPERATOR]` gate, not the blanket "only adds rows" claim that was true for a
   different function.
2. **`market-tick-data-service/scripts/rebuild_mtds_manifest.py::rebuild_from_canonical()`** (`Lifecycle: permanent`,
   already shipped, callable via `--from-canonical` at any time by any future operator/agent) calls the same function
   with `prefix=_DATA_PREFIX` = `"raw_tick_data/by_date"` — the MTDS-only prefix. Running this against any of the
   cefi/defi/tradfi/prediction tick buckets today would silently delete every `market-data-processing-service` candle
   manifest row sharing that bucket. Not exercised this session (found by code inspection while root-causing risk site
   1), but it is a standing, already-merged latent hazard — any future `--from-canonical` invocation on these buckets
   reproduces the same class of loss in the opposite direction.

## The safe sibling function already exists

`rebuild_manifest()` (same file, `_maintenance.py:131-262`) does the right thing for this use case: it reads `existing`,
computes `discovered - existing` (only genuinely-missing `(date, venue)` keys), and uploads `existing + new_only` —
**additive, never destructive**, and its own docstring correctly states "Existing entries are preserved (not
overwritten)". It does not carry the richer `(chain, instrument_type, data_type)` key the candle case needs (it keys on
`(date, venue)` only) — extending it, or adding an equivalent additive
`(day, venue, chain, instrument_type, data_type)`-keyed helper, is the real fix for the candle-reconciliation use case;
not a caller-side workaround.

## Recommended fix path

- [ ] 1. [DATA] P0. **Fix `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`'s recommended remediation** —
      do NOT invoke `rebuild_manifest_from_canonical_paths` scoped to `prefix="processed_candles/by_date"` on a
      co-located tick bucket. Blocked until todo 2 below ships an additive alternative, OR an `[OPERATOR]`-gated one-off
      script does a proper merge (read full existing index, union in only genuinely-new candle keys, write back) instead
      of a naive full-prefix-replace. Repo: unified-trading-pm (doc fix — done as part of this issue's own filing, see
      that doc's cross-reference below).
- [x] 2. ✅ [SCRIPT] P0. **DONE 2026-07-27 (slot-12)** — `unified-trading-library@2352e7c8`. Added
      `merge_manifest_from_canonical_paths()` (new function, `_maintenance.py`), an additive
      `(day, venue, chain, instrument_type, data_type)`-keyed sibling of `rebuild_manifest_from_canonical_paths`: walks
      `prefix`, computes only genuinely-missing keys vs the FULL existing index, and uploads `existing + new_only` —
      every row outside `prefix` survives untouched. Exported through `manifest_writer/__init__.py` and the top-level
      `unified_trading_library/__init__.py` (`__all__` updated). 2 new regression tests in
      `tests/unit/test_manifest_v4_migration.py` prove exactly the safety property this doc exists for: a pre-existing
      MTDS row (different prefix/service_name) survives a candle-prefix-scoped merge, verified BOTH in the returned
      frame AND in what actually lands in the stub GCS upload
      (`test_merge_from_canonical_paths_preserves_rows_outside_prefix`), plus an idempotency test
      (`test_merge_from_canonical_paths_is_idempotent_no_duplicate_rows`). Full `quality-gates.sh` green (1144s local +
      266s under quickmerge's sentinel re-verify), shipped via quickmerge --agent, CI `quality-gates-v2` green
      post-push. `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`'s recommended fix path now points at
      this function.
- [ ] 3. [SCRIPT] P1. **Audit `rebuild_mtds_manifest.py --from-canonical`'s existing call site** against the fix from
      todo 2 (or add an explicit docstring/runtime guard refusing a `prefix` narrower than the bucket's full known
      content) so the standing MTDS-side risk (risk site 2 above) is closed, not just the MDPS-side one that prompted
      this doc.
- [ ] 4. [DATA] P2. Grep the corpus for any OTHER caller of `rebuild_manifest_from_canonical_paths` that might already
      have been run against a co-located bucket in the past (this session found none besides the two above via
      `grep -rn "rebuild_manifest_from_canonical_paths(" --include="*.py"`, but a shipped one-off VM script invoked via
      a launcher's `VM_BACKFILL_CMD` metadata string would not show up in that grep) — confirm via manifest `written_at`
      timestamps whether any bucket's index shows a suspicious mass-drop matching this function's known call shape. Not
      urgent (no evidence of a past incident), but worth a bounded check before closing this doc.

## Evidence

- Function body read directly:
  `unified-trading-library/unified_trading_library/manifest_writer/_maintenance.py:502-690`.
- `_INDEX_PATH` confirmed as the single whole-bucket consolidated index via
  `grep -n "_INDEX_PATH" unified_trading_library/manifest_writer/*.py` — every read/write site in the module uses the
  same constant, unfiltered by prefix.
- Only real Python caller found today: `market-tick-data-service/scripts/rebuild_mtds_manifest.py:249`
  (`prefix=_DATA_PREFIX="raw_tick_data/by_date"`).
- Sibling additive function confirmed safe by direct read: `rebuild_manifest()`,
  `unified-trading-library/unified_trading_library/manifest_writer/_maintenance.py:131-262` — merges `existing + new`,
  never replaces wholesale.
- Independently re-measured DEFI's candle-manifest row count with the CORRECT vocabulary (data_type=SOURCE, real
  `timeframe`, per the sibling 2026-07-26 root-cause fix) as part of the same session's audit: 7,913 real
  `market-data-processing-service` candle rows exist in the live DEFI index today — a live, populated index that a naive
  prefix-scoped rebuild would have destroyed had it been run.
