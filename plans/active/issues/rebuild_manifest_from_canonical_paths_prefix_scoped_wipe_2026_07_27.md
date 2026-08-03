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
repos:
  [
    unified-trading-library,
    market-tick-data-service,
    market-data-processing-service,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [data-correctness, manifest, gcs, mdps, mtds, candle, orphan, data-loss-risk, operator-notify]
related:
  [
    /plans/archive/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md,
    /plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/issues/mdps_backfill_cefi_trades_gap_fill_completion_2026_07_28.md,
    /plans/active/sports_satellite_ao_dispatch_batch6_2026_07_26.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-30"
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
context_scope:
  [
    unified-trading-library/unified_trading_library/manifest_writer/_maintenance.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md,
    market-tick-data-service/scripts/rebuild_mtds_manifest.py,
  ]
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

1. **`plans/archive/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`** (RESOLVED 2026-07-31, about
   to be archived — its own reconciliation goal was closed as a byproduct of a DIFFERENT, already-shipped tool
   (`backfill_candle_manifest.py`'s corpus-wide campaign, `mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md`
   todo 2); the corrected recipe below was never actually invoked against prod) recommended exactly this unsafe call:
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

- [x] 1. ✅ [DATA] P0. **VERIFIED DONE 2026-07-27 (slot-15)** — **Fix the sibling reconciliation doc's recommended
      remediation** — do NOT invoke `rebuild_manifest_from_canonical_paths` scoped to
      `prefix="processed_candles/by_date"` on a co-located tick bucket. Confirmed the fix is already in place: the
      sibling doc's "Recommended fix path" section (see `related:` above) carries both the "CORRECTED 2026-07-27" banner
      (blocking the original unsafe recipe) and the "UNBLOCKED 2026-07-27" banner (pointing the recipe at
      `merge_manifest_from_canonical_paths`, shipped by todo 2). Independently re-verified rather than trusting the
      doc's own claim: (1) grepped + read `merge_manifest_from_canonical_paths` in `_maintenance.py` (line 757) —
      confirmed genuinely additive (concatenates new rows onto the existing index, never replaces it wholesale); (2)
      confirmed it is exported from both `manifest_writer/__init__.py` and the top-level
      `unified_trading_library/__init__.py`; (3) confirmed both cited regression tests exist in
      `tests/unit/test_manifest_v4_migration.py` (`test_merge_from_canonical_paths_preserves_rows_outside_prefix`,
      `test_merge_from_canonical_paths_is_idempotent_no_duplicate_rows`). No further doc edit needed — the corrected
      recipe was already written into the sibling doc when todo 2 shipped; this todo's own text just hadn't been flipped
      to reflect it. Repo: unified-trading-pm (verification only, no code change).
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
- [x] 3. ✅ [SCRIPT] P1. **DONE 2026-07-27 (slot-2)** — `market-tick-data-service@de0ed32f`. Routed
      `rebuild_mtds_manifest.py::rebuild_from_canonical()` (the `--from-canonical` call site, risk site 2) through UTL's
      additive `merge_manifest_from_canonical_paths` — the same fix todo 2 shipped for the MDPS side — instead of the
      wholesale-replacing `rebuild_manifest_from_canonical_paths`. Existing rows outside `raw_tick_data/by_date` (i.e.
      market-data-processing-service's co-located `processed_candles/` rows) now survive untouched; updated the function
      docstring + `--from-canonical` CLI help text to describe the additive (not wholesale-replace) semantics. Added 2
      regression tests (`tests/unit/scripts/test_rebuild_mtds_manifest_from_canonical_safe.py`) pinning that the safe
      merge function is called (never the wholesale-replacing sibling) and that the call scopes to this script's own
      prefix. Full `quality-gates.sh` green (529s, 7162 passed).
- [x] 4. ✅ [DATA] P2. **DONE 2026-07-30 (slot-3)**. Grepped the full corpus (`*.py` across all repos, VM-launcher shell
      scripts, and `plans/active/**/*.md` prose) for other callers/recommenders of
      `rebuild_manifest_from_canonical_paths`, and empirically checked all 4 co-located tick buckets' manifest
      `written_at` distributions for a mass-drop signature. Full findings: § "Fourth risk site" below. Summary: found
      and fixed one LIVE code landmine (`launch-mdps-backfill-vm.sh`), found and fixed one more doc leading-indicator
      (sports features launcher hint), found and tracked one more live-but-currently-inert code site
      (`launch-features-sharded-backfill.sh`, new todo 5), and confirmed via direct manifest read — **no evidence of a
      past wipe on any of the 4 co-located tick buckets** (cefi/defi/tradfi/prediction all show healthy, near-row-unique
      `written_at` timestamps for both MTDS and MDPS spanning months, the opposite signature of a wholesale-replace
      event).

- [ ] 5. [CODE] P3. **Swap `launch-features-sharded-backfill.sh`'s post-backfill reminder to the additive merge
      function.** Same bug shape as todo 4's other findings: the reminder (near end of file) calls
      `rebuild_manifest_from_canonical_paths(resolve_bucket_name(cloud='gcp', kind='features', asset_group=...), service_name='features-service')`
      with no `prefix=` — defaults to `"raw_tick_data/by_date"`, which doesn't exist in a features bucket, so today this
      is a harmless no-op (0 blobs discovered → the function's own empty-guard returns before writing anything). Still
      worth closing: swap to `merge_manifest_from_canonical_paths` (same args, but `prefix` is REQUIRED — pick the real
      per-family object-key prefix, e.g. `delta_one/by_date` confirmed live at
      `features-service/features_service/cross_instrument/cli/handlers/batch_handler.py:223`; calendar and sports need
      their own real prefixes, do NOT assume `${FAMILY}/by_date` is uniform — verify each family's actual writer path
      before hardcoding, per the SAME file's own existing "do NOT hardcode a prefix" comment). Lower priority than todo
      4's other sites because it is non-destructive today regardless (wrong prefix ⇒ 0 discovered ⇒ early return,
      verified by reading `_maintenance.py:648-651`'s `if rebuilt.empty: return` guard) — this is a defense-in-depth
      close, not an active-risk fix. Repo: deployment-service. No `[OPERATOR]` gate needed (same hint-text-only
      justification as the sports todo above — no VM launch, no GCS write/delete). `launch-features-backfill-vm.sh`
      carries the identical unsafe-function text but is DEPRECATED (2026-05-08, superseded by `launch-features-vm.sh`)
      and the block is dead code — the file `exec`s into the consolidated launcher unconditionally once its required
      args are present, so the legacy reminder only fires on a malformed partial invocation; not worth fixing, noted
      here so it isn't rediscovered as a false new finding.

## Fourth risk site found 2026-07-30 (todo 4's own corpus sweep) — one live fix, one more doc fix, one tracked, all clear on past execution

**Corpus grep (`*.py`, all repos)**: zero callers beyond the function definition itself and its own 5 regression tests
in `test_manifest_v4_migration.py`. Confirmed both risk-site-1/2 callers now delegate to the safe
`merge_manifest_from_canonical_paths` (verified by reading `rebuild_mtds_manifest.py:253-259` directly, not just
grepping) — todos 1-3's fix held.

**VM-launcher plain-text grep (the "`VM_BACKFILL_CMD` metadata string" blind spot this todo named at creation)** —
`grep -rln "rebuild_manifest_from_canonical_paths" --include="*.sh" --include="*.yaml" --include="*.yml" .` surfaced 5
files the `*.py` grep structurally cannot see (the calls live inside `echo`'d post-backfill reminder text, not
importable Python):

1. **`launch-mdps-sharded-backfill.sh`** — already safe (already cites `merge_manifest_from_canonical_paths`, fixed in
   the same 2026-07-27 session as todos 1-3, confirmed by direct read). No action.
2. **`launch-mdps-backfill-vm.sh`** — **LIVE LANDMINE, FIXED THIS SESSION** (`deployment-service`, this todo). This is
   the primary, currently-canonical MDPS backfill launcher (registered in `vm_prefix_registry.py`'s
   `mdps-backfill-{cefi,tradfi,defi,prediction,sports}-` prefixes, wired into `deployment-api`'s `deploy_missing.py`,
   invoked verbatim in currently-active dispatch plans `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` and
   `tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`, last touched 2026-07-30 for an unrelated fix — not stale, not
   superseded). Its post-backfill reminder printed the exact risk-site-1 recipe
   (`rebuild_manifest_from_canonical_paths('market-data-tick-${ASSET_GROUP}-central-element-323112', service_name='market-data-processing-service', prefix='processed_candles/by_date')`)
   against the real co-located tick bucket, with a real, populated, existing `processed_candles/by_date` prefix (NOT a
   0-discovery no-op like the features cases below — this recipe would genuinely have destroyed the bucket's raw-tick
   manifest rows if copy-pasted and run). Fixed to call `merge_manifest_from_canonical_paths` instead, mirroring
   `launch-mdps-sharded-backfill.sh`'s already-shipped, already-reviewed fix pattern verbatim (same warning comment,
   same call shape). Not yet shipped as of this write-up — ships via quickmerge in this same session, see evidence
   below.
3. **`launch-features-vm.sh`** — unsafe function present but currently non-destructive (omits `prefix=`, defaults to
   `"raw_tick_data/by_date"` which doesn't exist in a features bucket ⇒ 0 discovered ⇒ early-return no-op, per
   `_maintenance.py:648-651`). Already has an open, correctly-scoped fix todo
   (`sports_satellite_ao_dispatch_batch6_2026_07_26.md`, sourced from
   `sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md` § Y) that — as originally scoped — fixed only
   the bucket-name-404 bug and would have left the wholesale-replacing function in place, now pointed at a bucket that
   resolves (turning a harmless 404 into a live risk). Amended both docs in place (2026-07-30) to require the function
   swap in the same edit as the bucket/prefix fix. Did not implement the fix myself — it is already assigned scope in an
   active plan; duplicating it risks a conflicting edit to the same lines.
4. **`launch-features-backfill-vm.sh`** — DEPRECATED, dead-code reminder (see todo 5).
5. **`launch-features-sharded-backfill.sh`** — same non-destructive-today shape as `launch-features-vm.sh`, live and
   current (not deprecated), not covered by any existing todo. New todo 5 above.

**`plans/active/**/*.md` prose grep** (per the Third-risk-site addendum's own recommendation to re-check this
periodically): 8 files matched. `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` (risk site 1) and
`mdps_backfill_cefi_trades_gap_fill_completion_2026_07_28.md` (risk site 3) are already corrected. Three more matches
are the two sports docs above (now amended) and this doc's own text/todo 4 wording (expected — it names the function to
warn about it). The remaining match, **`cefi_satellite_ao_dispatch_batch1_2026_07_25.md`**, is Progress-Log narrative
(not a live recipe) — a 2026-07-26 session recorded "post-completion steps: (1) run the launcher's own reminder —
`rebuild_manifest_from_canonical_paths('market-data-tick-cefi-central-element-323112', ...)`" as its _planned_ next step
after launching an MDPS candle backfill, predating both this issue doc's discovery (2026-07-27) and the safe function's
existence. The todo it belongs to (`-001`) was flipped `[x]` the same day via GCS-direct verification that explicitly
did **not** depend on the manifest reconciliation step running (`RollingAdvReader` reads candles directly off GCS,
bypassing the manifest entirely) — the doc gives no direct confirmation the reconciliation step was ever actually run.
Resolved empirically instead of by further doc archaeology: see the written_at check below. Historical Progress Log
entries are not rewritten (append-only record); no edit made to that doc.

**Manifest `written_at` mass-drop check (direct read, not a corpus walk — one slim-projected read of each bucket's
existing single consolidated index object, `columns=["service_name","written_at","date"]`)**, for all 4 co-located tick
buckets this doc's `asset_group:` frontmatter scopes to. A wholesale-replace event would show as either a service's rows
vanishing entirely, or surviving rows collapsing to one/few uniform `written_at` values at the moment of the replace.
Measured 2026-07-30:

| bucket (real name incl. env/pred-infix quirk)                                                                                                                                                | market-tick-data-service rows | written_at span         | distinct written_at | market-data-processing-service rows |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------: | ----------------------- | ------------------: | ----------------------------------: |
| `market-data-tick-cefi-prd-central-element-323112`                                                                                                                                           |                     6,124,758 | 2026-04-14 → 2026-07-30 |           6,124,685 |                             509,049 |
| `market-data-tick-defi-prd-central-element-323112`                                                                                                                                           |                    27,642,709 | 2026-07-22 → 2026-07-29 |          27,627,088 |                           1,486,537 |
| `market-data-tick-tradfi-prd-central-element-323112`                                                                                                                                         |                     4,199,707 | 2026-04-06 → 2026-07-28 |           1,325,450 |                              49,536 |
| `market-data-tick-pred-prd-central-element-323112` (NOT `-prediction-` — confirmed via `bucket-isolation-model.md`, an earlier probe against the wrong name misread as an empty/wiped index) |                     1,596,905 | 2026-04-05 → 2026-07-28 |           1,596,896 |                              18,646 |

Every bucket: both services' row counts are large, `written_at` values are near-1:1-unique with the row count (i.e.
genuine incremental per-shard writes accumulated over months), and MTDS rows are intact everywhere. **This is the
opposite signature of a wholesale replace** (which would show 0 rows or a handful of uniform recent timestamps for the
wiped service). **Conclusion: no evidence of a past incident on any of the 4 buckets** — matches this doc's original
"not urgent" framing; now confirmed rather than assumed.

## Third risk site found 2026-07-30 (ag-closeout-audit cefi) — a doc, not a past execution

`plans/active/issues/mdps_backfill_cefi_trades_gap_fill_completion_2026_07_28.md`'s sole open todo (created 2026-07-28,
one day AFTER this doc's fix landed, but independently drafted the same unsafe recipe rather than reusing the corrected
one) still prescribed the wholesale-replacing `rebuild_manifest_from_canonical_paths(...)` call against this exact
co-located `market-data-tick-cefi-prd-central-element-323112` bucket. Not executed (still `[ ]`, heavy-I/O VM-gated,
same as risk site 1 was before its catch) — corrected in place to cite `merge_manifest_from_canonical_paths` instead,
same fix pattern as todo 1 above. This confirms the fix (todos 1-3) closed the two ORIGINAL call sites but did not
prevent a THIRD, independently-authored doc from re-introducing the same unsafe recipe by name — todo 4's corpus grep
should also periodically re-check `plans/active/**/*.md` prose (not just `*.py` callers) for the unsafe function name,
since a plan/issue doc recommending it is a leading indicator that catches the mistake before it ever executes.

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
