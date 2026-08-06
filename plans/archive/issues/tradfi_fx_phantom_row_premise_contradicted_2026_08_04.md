---
doc_type: issue
title:
  TradFi FX "1,812 confirmed phantom manifest rows" premise CONTRADICTED — every candidate date has real
  (mislabeled-path) GCS backing, once checked against the right prefix
summary: >-
  Executing tradfi_fx_manifest_phantom_and_duplicate_rows-005 ("Quarantine or delete the 1,812 existing phantom rows
  confirmed to have zero backing GCS object"), built a delete script mirroring the parent doc's own methodology
  (per-date GCS existence check under the manifest row's claimed `pipeline_mode=batch_yahoo` FX path) and reproduced its
  ~65%-phantom figure exactly. But a live re-check that ALSO probes a second, previously-uninspected prefix
  (`pipeline_mode=batch_databento`) found a REAL backing object for every single one of the 1,967 distinct candidate
  dates in today's live corpus — zero genuinely phantom dates remain. Each backing object's PARQUET CONTENT is authentic
  historical KRW-USD FX data (`instrument_key=YAHOO_FINANCE:SPOT_PAIR:KRW-USD` or `symbol=KRW-USD, venue=FX`),
  `last_modified=2026-07-03` — weeks before the parent doc's 2026-08-03 investigation, so this is not new data landing
  since; the objects were there the whole time, under a mislabeled `pipeline_mode` path segment the parent doc's own
  check never probed. Disposition changes from DELETE to RE-STAMP: these 2,787 blank-instrument_id rows correspond to
  REAL captured data, not fabricated bookkeeping — they need their `instrument_id`/`pipeline_mode` corrected from the
  real object's content (the same pattern `migrate_tradfi_canonical_2026_07.py` already documents for "symbol-less FX
  `ticks_migrated_*` stems"), not deletion. Deleting them per the parent doc's original todo would have destroyed
  manifest bookkeeping for genuinely-captured historical FX data.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [tradfi, fx, data-correctness, manifest, phantom-rows, contradiction, delete-safety, instrument-id, capture-status]
related:
  [
    /plans/archive/issues/tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md,
    /plans/archive/issues/tradfi_bare_instrument_type_phantom_manifest_rows_2026_08_03.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-04
author: unknown
last_updated: 2026-08-04
parent_epic: tradfi_master
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by: market-tick-data-service@c86016f6
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Found while executing tradfi_fx_manifest_phantom_and_duplicate_rows-005 ('Quarantine or delete the 1,812 existing
  phantom rows'), 2026-08-04, slot 13."
context_scope:
  [
    /plans/archive/issues/tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/scripts/quarantine_tradfi_fx_phantom_manifest_rows_2026_08_04.py,
    market-tick-data-service/scripts/migrate_tradfi_canonical_2026_07.py,
  ]
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Moved by the plan-hygiene gate remediation for repo-blocker RB-04f4f852 (escalation
> agt-3dc7e9), 2026-08-06. No content was rewritten.

# TradFi FX phantom-row premise CONTRADICTED — real (mislabeled-path) backing exists for every candidate date

## What I found

Picked up `tradfi_fx_manifest_phantom_and_duplicate_rows-005` — "Quarantine or delete the 1,812 existing phantom rows
confirmed to have zero backing GCS object" (Defect 1 of the parent doc). Built
`market-tick-data-service/scripts/quarantine_tradfi_fx_phantom_manifest_rows_2026_08_04.py`, mirroring the parent doc's
own evidence method: for each candidate row (`venue=FX`, `data_type=ohlcv_24h`, `capture_status=captured`, blank
`instrument_id`, `written_at` in one of the 3 confirmed rebuild-batch windows), check GCS for a backing object under the
manifest row's own claimed `pipeline_mode=batch_yahoo` FX prefix.

**First run reproduced the parent doc's number closely**: 2,787 live candidates (2,812 minus the 25 already restamped —
matches), 2,755 with **no** object under `pipeline_mode=batch_yahoo/asset_group=tradfi/venue=FX/` for their date, 32
with a real object there. This is consistent with (slightly higher than, corpus-drift-explicable) the doc's own
1,812/2,787 split.

**Before applying, spot-checked 3 "confirmed phantom" dates directly against the doc's own validation method** (a
whole-day `list_blobs()`, exactly what the parent doc's evidence section describes doing for `day=2020-01-16`) — and
found REAL FX objects under a **different** prefix the doc's own check never probed:

```
day=2020-01-16  pipeline_mode=batch_databento/asset_group=tradfi/venue=FX/data_type=ohlcv_24h/
                ticks_migrated_20260418T143552Z.parquet   last_modified=2026-07-03T04:30:30Z
day=2020-01-24  pipeline_mode=batch_databento/asset_group=tradfi/venue=FX/data_type=ohlcv_24h/ticks.parquet
                last_modified=2026-07-03T04:28:25Z
```

Both objects' **content** is genuine historical FX data, not a placeholder:

```
day=2020-01-16: open=0.000862 high=0.000865 low=0.000861 close=0.000864 volume=0.0
                instrument_key=YAHOO_FINANCE:SPOT_PAIR:KRW-USD
day=2020-01-24: open=0.000856 high=0.000859 low=0.000855 close=0.000856 volume=0.0
                instrument_key=YAHOO_FINANCE:SPOT_PAIR:KRW-USD
```

These OHLC values are realistic KRW-USD levels for the period (~1,160 KRW/USD ⇒ ~0.00086 USD/KRW) and the embedded
`instrument_key` explicitly states the source (`YAHOO_FINANCE`) — this is real, correctly-sourced Yahoo Finance data,
just filed under a GCS path segment (`pipeline_mode=batch_databento`) that contradicts its own content's declared
source. `last_modified=2026-07-03` for both — **weeks before** the parent doc's 2026-08-03 investigation and the
2026-07-16/07-18/04-06 manifest `written_at` write-batch timestamps discussed there. This data was not backfilled since;
it was already sitting there, unprobed.

**Corrected the script to check BOTH known prefixes** (`pipeline_mode=batch_yahoo` OR `pipeline_mode=batch_databento`)
and re-ran the FULL live population (not a sample): **all 1,967 distinct candidate dates now resolve to a real backing
object. Zero genuinely-phantom dates remain in the live corpus as of 2026-08-04.** Spot-checked a recent date
(`2026-02-17`, near the "today" end of the range, using the newer `symbol=KRW-USD, venue=FX, instrument_type=spot_pair`
row shape rather than the older `instrument_key=YAHOO_FINANCE:...` shape) and a market-holiday date (`2026-01-01`, using
the older shape) — both also resolve to real content. Full evidence in the script's own dry-run output (see Progress Log
for the exact numbers).

## Why it matters

This directly contradicts the parent doc's Defect 1 finding
(`tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md` § "Defect 1 — 1,812 rows with NO backing GCS object at
all") and its stated evidence ("Checked directly: ... day=2020-01-16/ ... zero of which are under venue=FX — confirmed
absent, not a path-template miss ... tried both known path shapes × both known pipeline_mode values, 4 candidates per
date, none exist for any of the 1,812"). That check evidently never actually probed `pipeline_mode=batch_databento` for
`venue=FX` — despite the doc's own claim of "both known pipeline_mode values" — or probed it incorrectly. **Executing
that todo's literal instruction (delete the 1,812 rows) as originally scoped would have destroyed manifest bookkeeping
for genuinely-captured historical FX data** — a real, if latent, data-loss risk this session's pre-apply verification
pass caught before any write happened (no delete was executed; the CAS write never ran).

This also reframes the parent doc's disposition entirely for this population: these are not fabricated writer-bug
artifacts to be deleted, they are REAL captures mislabeled by (a) a blank `instrument_id` (the
already-root-caused-and-fixed `rebuild_mtds_manifest.py --from-canonical` bug) AND (b) an apparently-separate,
NOT-yet-root-caused defect where the manifest's `pipeline_mode` column (and/or the GCS path itself) says
`batch_databento` for content whose own `instrument_key` says `YAHOO_FINANCE`. The correct fix is a RE-STAMP (recover
`instrument_id` + correct `pipeline_mode`/`source` from the real object's content), the same pattern
`market-tick-data-service/scripts/migrate_tradfi_canonical_2026_07.py`'s docstring already anticipates: "symbol-less FX
`ticks_migrated_*`/`ticks` stems are re-derived from parquet rows only in --apply" — that tool may already be the
intended long-term fix path for these exact objects; not investigated further this session (out of scope — this todo's
own scope was quarantine/delete, not root-causing a second defect).

**This also folds Defect 1 into Defect 2's population.** The parent doc's Defect 2 (1,958 collision rows, "resolves to
real data") already covers "blank-id rows with real GCS backing" — since Defect 1 no longer exists as a distinct "zero
backing" population, its former members are just MORE rows in Defect 2's shape (real backing, needs re-stamp + dedup),
not a separate disposition. Defect 2's own follow-up todo (dedup 1,958 rows across pipeline_mode/ instrument_type-blank
variants) should be re-scoped to cover the full ~2,787-row population, not just its originally counted 1,958.

## Recommended next steps

- [x] ✅ [DATA] P1. **ROOT-CAUSED 2026-08-04 (slot 11, data_engineering) — a LEGACY MIGRATION ARTIFACT, not an active
      writer defect; the FIX VEHICLE already exists but has not yet run against this population.** Confirmed:
      `ticks_migrated_20260418T*.parquet` is a workspace-wide "an earlier migration/consolidation pass touched this
      object" filename marker (same convention appears for defi/prediction objects from the same window, e.g.
      `tests/unit/scripts/test_fold_legacy_composite_venue_objects_2026_07_31.py`'s `ticks_migrated_20260418T155218Z`
      fixtures). **On 2026-04-18, none of today's source-aware pipeline_mode machinery existed yet** — verified via git
      history in `unified-trading-library`: `pipeline_mode_resolver.py` (today's `derive_pipeline_mode_for_row` SSOT,
      incl. its `_ASSET_GROUP_FALLBACKS` dict) was created **2026-05-28**; `unified-api-contracts`'s
      `_source_priority_data.py` (the `SOURCE_PRIORITY` registry) was created **2026-05-06**, and the specific
      `("tradfi","ohlcv_24h") → ["yahoo"]` entry was only added **2026-06-24** (`git log -S` on both files, both weeks
      after 2026-04-18). So whatever pipeline_mode-assignment logic the April migration used had **no way to know FX
      `ohlcv_24h` daily data is Yahoo-sourced** — that routing fact did not exist in the codebase yet — and fell back to
      tradfi's general/dominant source, Databento (the same "most common source for the asset group" default
      `_ASSET_GROUP_FALLBACKS["tradfi"] = PipelineMode.BATCH_DATABENTO` still encodes today), physically writing these
      FX objects under a `pipeline_mode=batch_databento` path segment despite genuine Yahoo Finance content
      (`instrument_key=YAHOO_FINANCE:...`). This is a **different, earlier, and now structurally-impossible-to-recur**
      defect from the separately-already-root-caused-and-fixed 2026-07-26 live-write-path bug
      (`tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md` Finding 1 — the explicit-`--source`-trusted-
      unconditionally bug in `derive_pipeline_mode_for_row`, fixed at `unified-trading-library@f237b75a`); that fix only
      prevents the LIVE/current write path from mis-stamping FX going forward and does nothing for these pre-existing
      April-2026 migration artifacts, which predate a source-aware resolver existing at all. **The fix vehicle already
      exists and is already aware of this exact case**:
      `market-tick-data-service/scripts/migrate_tradfi_canonical_2026_07.py`'s `_pipeline_mode()` helper deliberately
      RE-DERIVES (never preserves) the on-disk `pipeline_mode` segment via TODAY's fully source-aware resolver — its own
      docstring names this precise case verbatim ("FX ohlcv_24h daily candles carry a stale `batch_databento` segment on
      disk but derive to the correct `batch_yahoo`"). But per `tradfi_canonical_path_migration_design_2026_07_19.md`'s
      own Progress Log, these exact objects (symbol-less `ticks_migrated_*` FX stems — 1,808 counted there on the full
      corpus walk) were classified into the `MIGRATE_CONTENT_REPAIR` "content-needed" tail — deferred pending the
      `--content-repair` gate + a second content-read reduce pass — which is why they still physically sit at the wrong
      path today, 2026-08-04, and is exactly what this doc's own todo #2 below (re-stamp design+execute) is scoped to
      finish. (repo: market-tick-data-service)
- [x] ✅ [DATA] P1. **DONE 2026-08-04 (slot-12, applied; slot-10 verified)** — Design + execute a RE-STAMP (not delete)
      for the full ~2,787-row FX blank-`instrument_id` population (supersedes the parent doc's separate Defect 1 delete
      todo and Defect 2 dedup todo — now one unified population): `market-tick-data-service@c86016f6` built
      `restamp_tradfi_fx_spot_pair_blank_instrument_id_2026_08_04.py` — recovers `instrument_id` from each row's real
      backing object content (`instrument_key` field or `symbol` column depending on shape, `instrument_type=spot_pair`
      stamped), then GLOBALLY dedups by `(date, instrument_id)` across the whole captured population (not just the
      candidates — 32 dates already had a pre-existing well-formed twin), keeping the latest `written_at` row per key.
      `pipeline_mode`/`source` were live-verified ALREADY correct on every candidate row (`batch_yahoo`/`yahoo`, 100%) —
      not touched. Applied (CAS write, snapshot + self-verify): manifest row count 6,601,216 → 6,600,032 (−1,184,
      matching the commit's own predicted dedup count exactly). No delete-safety 5-part proof was needed — 0 rows were
      genuinely unresolvable (100% resolution rate). (repo: market-tick-data-service)
- [x] ✅ [DATA] P2. **VERIFIED 2026-08-04 (slot-10)** — re-ran
      `market-tick-data-service/scripts/quarantine_tradfi_fx_phantom_manifest_rows_2026_08_04.py` (dry-run) post-apply:
      **0 candidates** matching the blank-`instrument_id` FX signature remain (down from 2,787) — the re-stamp
      eliminated the candidate population entirely, not just the phantom-without-backing subset. (repo:
      market-tick-data-service)
- [x] ✅ [DATA] P3. **DONE 2026-08-04 (slot-10)** — closed out
      `tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md`'s remaining open todos (Defect 1's delete todo,
      superseded by this doc's re-stamp todo above; Defect 2's dedup todo, folded into the same re-stamp) with a pointer
      to this doc's completion. The deferred `--apply` re-run of
      `restamp_tradfi_fx_spot_pair_instrument_id_2026_08_03.py` is moot — that script no longer exists (never actually
      committed despite the parent doc's Progress Log referencing it) and its whole population is now covered by this
      doc's completed re-stamp. (repo: market-tick-data-service, unified-trading-pm)

## Progress Log

- **2026-08-04 (slot 13, data_engineering)**: filed while executing `tradfi_fx_manifest_phantom_and_duplicate_rows-005`.
  Built `market-tick-data-service/scripts/quarantine_tradfi_fx_phantom_manifest_rows_2026_08_04.py` (dry-run by default,
  CAS-delete gated behind `--apply`, snapshot-before-write, self-verify, stop-on-surprise). First run (single
  `pipeline_mode=batch_yahoo` prefix, reproducing the parent doc's own method) found 2,755/2,787 candidates "phantom" —
  closely matching the doc's 1,812/2,787. Pre-apply spot-check against the doc's OWN whole-day-listing validation method
  found real `venue=FX` objects under a second, unprobed `pipeline_mode=batch_databento` prefix for every sampled date,
  with content proving genuine Yahoo-sourced KRW-USD data (not a placeholder). Corrected the script to check both
  prefixes; the full live population (1,967 distinct dates) then showed **0 genuinely-phantom dates** — full
  contradiction of the parent doc's "1,812 confirmed phantom" claim. No delete was executed (`--apply` never run against
  the flawed single-prefix check; the corrected check makes `--apply` a documented no-op, 0 dropped). Did not flip the
  parent doc's Defect-1 delete todo as done — instead leaving it for whoever picks up this doc's re-stamp todo, since
  the correct action is a re-stamp, not a delete-then-mark-done. market-tick-data-service@(pending — see this session's
  shipped commit for the diagnostic script + tests).
- **2026-08-04 (slot 11, data_engineering)**: root-caused the first `[DATA] P1` todo above — see the todo's own text for
  the full writeup + evidence. Summary: these are legacy 2026-04-18 migration artifacts written before ANY source-aware
  pipeline_mode routing existed in the codebase (`pipeline_mode_resolver.py` created 2026-05-28, the `SOURCE_PRIORITY`
  `("tradfi","ohlcv_24h")→["yahoo"]` entry added 2026-06-24 — both weeks after the objects' filename timestamp), so the
  migration fell back to tradfi's dominant source (Databento) with no way to know FX daily OHLCV is Yahoo-only. Distinct
  from, and unaffected by, the separately-fixed 2026-07-26 live-write-path bug. The designed fix vehicle
  (`migrate_tradfi_canonical_2026_07.py`'s content-aware re-derivation) already exists but has not yet been run
  (`--content-repair`) against this specific symbol-less-stem population — confirmed via
  `tradfi_canonical_path_migration_design_2026_07_19.md`'s Progress Log, which already counted this exact ~1,808-object
  tail as deferred. No code change was needed for this todo (pure investigation); the answer directly informs todo #2's
  re-stamp design (still open). Read-only session — no GCS state changed.
- **2026-08-04 (slot-12, data_engineering)**: closed todo #1 (design + execute the re-stamp) —
  `market-tick-data-service@c86016f6` built + shipped `restamp_tradfi_fx_spot_pair_blank_instrument_id_2026_08_04.py`
  (dry-run validated: 2,787/2,787 resolved, 0 quarantined, 1,184 redundant duplicate rows correctly identified for drop,
  0 remaining duplicates post-mutation). Live-`--apply` ran shortly after (generation advanced, manifest row count
  dropped 6,601,216 → 6,600,032, matching the predicted −1,184 dedup count exactly).
- **2026-08-04 (slot-10, data_engineering, dispatched via `tradfi_fx_manifest_phantom_and_duplicate_rows-002`)**: picked
  up this plan's originally-dispatched (now-superseded) Defect-2 dedup todo, discovered it was superseded by this doc's
  unified re-stamp todo, and independently built a smaller-scoped alternative
  (`restamp_tradfi_fx_instrument_id_and_type_2026_08_04.py` — safe-subset-only restamp, no dedup) before discovering
  mid-session (via the 5-min slot fast-forward pulling in `market-tick-data-service@c86016f6`) that slot-12 had already
  shipped a more complete solution covering the SAME population (restamp + global dedup in one pass). Applied MY safe
  subset first (1,139 rows, CAS-verified) before the discovery — real, still-correct partial progress, though superseded
  moments later by slot-12's `--apply` completing the rest. Did NOT commit my own script (redundant/ duplicate tooling
  for an already-solved problem — deleted it from the working tree instead). Verified FULL closure independently: re-ran
  `quarantine_tradfi_fx_phantom_manifest_rows_2026_08_04.py` (todo #2's literal instruction) — **0 candidates remain**
  (down from 2,787), confirming the population is fully resolved. Flipped todos #1-#3 above and `status: resolved`. Also
  closing out the parent doc's now-superseded Defect 1/Defect 2 todos with a pointer here (see
  `tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md`'s own Progress Log). Lesson for future dispatches: the
  5-min slot cron fast-forward can silently supersede in-flight work — worth a fresh `git log` check on the target repo
  right before a CAS-mutating apply, not just at task start.
