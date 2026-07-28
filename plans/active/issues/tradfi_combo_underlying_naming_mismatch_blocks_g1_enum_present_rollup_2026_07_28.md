---
doc_type: issue
title:
  TradFi COMBO captures carry spelled-out commodity names as ``underlying`` ("HEATING-OIL"/"PLATINUM"/"CRUDE") while the
  catalog/seed side uses short root codes ("HO"/"PL"/"CL") — a naming-convention mismatch the G1-ENUM present-set
  symmetric-rollup fix cannot close, confirmed via a real production quantification
summary: >-
  While quantifying the before/after phantom-cell impact of the G1-ENUM present-set symmetric-rollup fix
  (`instruments-service` `enumerate_expected_universe.py`, `_rollup_present_bundle_grain`), a real production run
  against the live tradfi manifest (`market-data-tick-tradfi-prd-*`, full 2018-01-01..2026-07-28 history) showed ZERO
  change in the `expected_unattempted` count for `combo`/`futures_chain`/`options_chain` bundle types (503,588 before
  and after, byte-identical per-instrument_type breakdown), even though the fix demonstrably works and DOES reduce the
  phantom count for cefi (-32 cells: `futures_chain` -23, `options_chain` -9, same methodology, bounded
  2026-01-01..2026-07-28 window). Root cause for the tradfi null-result: the manifest's real captured `COMBO`
  (uppercase, 1,314,705 rows) and `combo` (lowercase, 23,428 rows) captures carry `underlying` values that are either
  blank (needing derivation) or already populated with SPELLED-OUT commodity names ("HEATING-OIL", "PLATINUM", "CRUDE",
  "NAT-GAS-HH", "COPPER", "GOLD", "SILVER") — while the catalog (and therefore the enumerator's seed, which derives
  `underlying` from the catalog's `underlying` column or via `_derive_underlying()`'s hyphen-split heuristic on the
  catalog's leaf `instrument_id`) uses SHORT ROOT CODES ("HO", "PL", "CL", "NG", "GC", "SI" — Databento/CME-style
  symbology). The present-set rollup fix correctly re-keys these rows to blank-instrument_id + bundle instrument_type,
  but the `underlying` VALUE itself never reconciles with the catalog's convention, so the seed and the rolled-up
  present-set key still never collide. Additionally, the LOWERCASE `combo`-typed rows carry a composite instrument_id
  like `"CME:COMBO:ESU4-ESH5"` (a calendar-spread pair code, not a clean root) — `_derive_underlying()`'s hyphen-split
  heuristic mis-parses this into `"CME:COMBO:ESU4"`, which is also wrong. Both are separate, real mismatches from the
  grain-symmetry bug the shipped fix addresses.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [g1-enum, expected-universe, tradfi, combo, futures_chain, underlying-naming, honest-coverage]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/june_2026_vintage_audit_findings_2026_07_27.md,
  ]
created: 2026-07-28
priority: P2
parent_epic: infrastructure_master
source:
  "autonomous dispatch, G1-ENUM present-set symmetric-rollup task, discovered during before/after production
  quantification, 2026-07-28"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# TradFi COMBO underlying-naming mismatch blocks the G1-ENUM present-set rollup from closing tradfi phantom cells

## What I found

Shipping the G1-ENUM present-set symmetric-rollup fix (option (a), `instruments-service@<see plan for SHA>`,
`_rollup_present_bundle_grain` mirrors `_rollup_bundle_grain`'s LEAF→bundle instrument_type collapse on present/captured
manifest rows), the task's own "quantify first" instruction required a real before/after production run. Both an unfixed
copy (`git show HEAD:scripts/enumerate_expected_universe.py`, the pre-fix version) and the shipped fix were run
scan-only (`--apply-write` NOT passed) against the live prod catalog + manifest:

- **cefi** (bounded 2026-01-01..2026-07-28 window, `market-data-tick-cefi-prd-central-element-323112`): before = 225,429
  blank-reason (`expected_unattempted`) candidates, after = 225,397 — **-32 cells** (`futures_chain`: 804→781, **-23**;
  `options_chain`: 100→91, **-9**). The fix works exactly as designed here.
- **tradfi** (full 2018-01-01..2026-07-28 history, `market-data-tick-tradfi-prd-central-element-323112`): before =
  503,588, after = 503,588 — **0 change**, byte-identical per-instrument_type breakdown (`combo` never even appears in
  either breakdown — only `equity`/`future`/`futures_chain`/`index`/`spot_pair`/`options_chain`).

Direct inspection of the real tradfi manifest (`_index/availability_index.parquet`, columns
`venue/instrument_type/instrument_id/underlying/capture_status`) explains why:

```
instrument_type=combo (lowercase, 23,428 rows, all capture_status=captured):
  instrument_id="CME:COMBO:ESU4-ESH5"  underlying=""      <- composite spread-pair id, BLANK underlying
instrument_type=COMBO (uppercase legacy, 1,314,705 rows, mixed capture_status incl. 246 expected_unattempted):
  instrument_id=None/""                underlying="HEATING-OIL"  <- already blank id, but a SPELLED-OUT name
instrument_type=futures_chain (238,965 rows) / options_chain (196,881 rows):
  already writer-shaped (blank instrument_id + underlying populated) — confirmed PASSTHROUGH under the fix
  (is_leaf=False, since these ARE the bundle type already, not a leaf) — no regression, as designed.
```

The catalog's own `underlying` column (and its leaf `instrument_id` shape, which `_derive_underlying()` falls back to)
uses short root codes: `ES`, `CL`, `HO`, `PL`, `NG`, `GC`, `SI`, etc. (Databento/CME-style). So even after my fix
correctly re-keys a `COMBO`-typed row to `(instrument_type="combo", instrument_id="", underlying=<value>)`, the
`<value>` itself is either:

1. Already-populated with the WRONG naming convention (`"HEATING-OIL"` instead of `"HO"`) — never matches the seed's
   `"HO"`.
2. Derived via `_derive_underlying()`'s hyphen-split from a COMPOSITE writer-side instrument_id (`"CME:COMBO:ESU4-ESH5"`
   → mis-parses to `"CME:COMBO:ESU4"`, not `"ES"`) — never matches either.

This is confirmed via a direct probe (`_rollup_present_bundle_grain` invoked on the real combo/futures_chain/
options_chain manifest slice): 1,132,212 rows had their `instrument_type` corrected (`COMBO`→`combo` casing collapse)
and 23,435 rows had `instrument_id`/`underlying` re-keyed — the fix IS doing real work — but the resulting `underlying`
values still don't line up with what the catalog-derived seed expects, so the set-difference still treats every combo
underlying as absent.

## Why it matters

- The shipped G1-ENUM present-set symmetric-rollup fix is CORRECT and does close real phantom cells (proven for cefi,
  -32; proven via unit tests for the general LEAF→bundle mechanism) — this is a SEPARATE, additional bug it doesn't
  reach, not a defect in the shipped fix.
- TradFi's combo-dominant present-set was flagged in the source finding as "the exposed case" — this issue explains
  precisely why the symmetric-rollup fix alone doesn't move that number: the underlying-naming axis is a DIFFERENT
  mismatch (vocabulary, not grain) layered on top of the grain mismatch the shipped fix targets.
- There is also a live legacy-casing residual: 1.3M `COMBO`-uppercase rows (vs. 23K correctly-lowercase `combo` rows)
  sitting in the manifest, including 246 already-written `expected_unattempted` rows under the wrong casing — a
  pre-2026-06-22 (`_canonical_writer_instrument_type` writer-grain-alignment fix) residual that has never been
  reconciled/cleaned up. Worth a dedicated reconciliation pass independent of this naming-mismatch fix.

## Recommended next step (not done here — genuine design question, not a ≤30 min fix)

Closing this requires an authoritative TradFi commodity root-code ↔ spelled-name mapping (CME/ICE/Databento symbology —
e.g. is the UAC `TRADFI_ROOTS` registry already this table, or does `_derive_underlying()` need a name-normalization
layer before its hyphen-split heuristic runs?). This is a genuine "what should the canonical underlying value BE" design
question — properly scoped as its own todo/plan rather than guessed at here under the present task's time budget (per
the workspace's dispatch-scope-eligibility rule: an open design call is not an AO-dispatchable todo until resolved). Two
candidate directions to evaluate:

1. Normalize the MANIFEST's captured `underlying` value at write time (MTDS `venue_fetch.py`/`manifest_finalize.py`) to
   the catalog's root-code convention — the more correct fix (writer-side SSOT alignment), but requires an
   `instruments-service` + `market-tick-data-service` coordinated change.
2. Extend `_derive_underlying()` / `_rollup_present_bundle_grain` with a spelled-name → root-code lookup table (a new
   UAC registry entry) — a narrower enumerator-only fix, but risks becoming a second source of truth for the mapping if
   the writer itself later needs the same table. Also worth a follow-up: reconcile/backfill the 1.3M-row legacy
   `COMBO`-uppercase residual (including its 246 already-written `expected_unattempted` rows) once the naming mismatch
   is resolved, so the manifest converges on the single lowercase-canonical `combo` instrument_type going forward.
