---
doc_type: issue
title:
  Tradfi catalogue roll-up re-contaminates from the USD@LIN sweep own .bak backups (and old-layout
  futures_contracts.parquet)
summary: >-
  build_instrument_catalogue.py by_date walk (_iter_by_date_snapshots) ingests EVERY *.parquet under the by_date prefix
  (endswith '.parquet'). The 2026-07-18 tradfi USD@LIN sweep left ~2,634 days of pre-sweep RAW-id
  instruments.usdlin.*.bak.parquet backups (0% canonical) co-located with the swept instruments.parquet (100%
  canonical). A --mode full roll-up therefore reads BOTH the canonical snapshot AND its raw backup for every instrument,
  producing raw+canonical TWINS. Measured — a clean walk (instruments.parquet only) is 100.0% canonical / 0 twins; the
  shipped walk over the SAME window is 49.70% canonical / 142 twin underlyings. A full rebuild now would REGRESS the
  served catalogue from 82.90% toward ~50% and roughly double F/O rows with twins. The by_date sweep itself is CORRECT
  and durable; the roll-up cannot realise it until the .bak backups (plus old-layout futures_contracts.parquet) are
  excluded from the walk or removed from the prefix.
status: resolved
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [tradfi, catalogue, canonicalization, usd-lin, by-date, backup-contamination, monotonic-guard, data-quality]
related:
  [
    instruments-service/scripts/build_instrument_catalogue.py,
    instruments-service/scripts/canonicalize_tradfi_catalogue_usd_lin_2026_07_18.py,
    codex/02-data/data-pipeline-correctness-hard-rule.md,
    codex/02-data/availability-manifest-and-data-status.md,
    codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-07-20
parent_epic: infrastructure_master
priority: P1
source: tradfi catalogue rebuild + durability verification 2026-07-20 (agent task)
assigned_vm:
resolved_by: instruments-service@1a73082e
locked_by: live-defi-rollout
audited_scope: data-correctness
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Tradfi catalogue roll-up re-contaminates from the sweep's own `.bak` backups

## The defect

`_iter_by_date_snapshots` (`scripts/build_instrument_catalogue.py`, ~line 2726) selects by_date snapshots with
`if not name.endswith(".parquet"): continue` — i.e. it reads **every** parquet under `instrument_availability/by_date/`,
not just the canonical `instruments.parquet`.

The 2026-07-18 USD@LIN sweep (`canonicalize_tradfi_catalogue_usd_lin_2026_07_18.py`, shipped
`instruments-service@feb0bef4`) rewrote the canonical `instruments.parquet` snapshots to `-USD@LIN` form (full census
99.8317% canonical) but, running with `--by-day`, first wrote a **pre-sweep backup** of each file:
`instruments.usdlin.<ts>.bak.parquet`. Those backups (RAW ids, 0% canonical) live in the **same** `day=/venue=`
directory the roll-up walks.

By_date prefix inventory (50,613 blobs total):

- 27,100 `instruments.parquet` — SWEPT, canonical (the sweep's denominator)
- ~19,567 `instruments.usdlin.*.bak.parquet` — pre-sweep RAW backups (~2,634 days)
- 3,946 `futures_contracts.parquet` — old-layout legacy files (no instrument-id column; every such day also has an
  `instruments.parquet`)

## Evidence (measured, read-only)

Same `day=2020-01-01/venue=CME`:

- `instruments.parquet`: 34,860 F/O rows, **100.0% canonical** (`CME:OPTION:GASOLINE-USD@LIN-20200821-16400-P`)
- `instruments.usdlin.*.bak.parquet`: SAME 34,860 rows, **0.0% canonical** (`CME:OPTION:OBQ0 P16400`)

Bounded-window roll-up through the REAL aggregation path (`build_catalogue_dataframe`), window since 2026-07-12:

- Shipped walk (all `.parquet`): total 295,143 / F/O 289,100 / **canon 49.70%** / **142 twin underlyings**
- Clean walk (`instruments.parquet` only): total 148,397 / F/O 142,359 / **canon 100.0000%** / **0 twins**

Three id generations coexist in the contaminated walk for one instrument: `CBOE:FUTURE:VIX-USD@LIN-20260722` (canonical,
from swept file) + `CBOE:FUTURE:VIX@LIN-20260722` (intermediate @LIN-no-USD) + `CBOE:FUTURE:VX/F7` (raw, from backup).

## Impact

- A **`--mode full`** rebuild (the weekly self-heal, and any cold start) REGRESSES the served catalogue from 82.90%
  toward ~50% F/O canonical and roughly DOUBLES F/O rows with raw twins.
- The **daily incremental** partially re-contaminates every day whose window overlaps a `.bak` file (the current 82.90%
  served artifact already carries the twins — 226,846 non-canonical F/O rows, of which the UAC oracle classifies 225,571
  as convertible-raw and only 1,275 as genuine `QUARANTINE_UNPARSEABLE`).
- The clean rebuild produces FEWER rows than the current twinned catalogue (twins collapse), so it would trip the
  monotonic guard and require `--allow-catalogue-shrink`.

## Recommended fix (operator/owning-workstream decision — options)

- **A [recommended]: tighten the walk filter** to `name.endswith("/instruments.parquet")` in `_iter_by_date_snapshots`
  (mirrors the prediction iterator, which already filters `endswith("instruments.parquet")`). Blast radius: shared by
  cefi/defi/tradfi — must confirm cefi/defi by_date carry no legitimately-named non-`instruments.parquet` snapshots
  before shipping. Durable (survives future sweeps that leave backups).
- **B: delete the `.bak` backups** (+ retire old-layout `futures_contracts.parquet`) from the prod by_date prefix.
  Human-gated prod-bucket delete (5-part proof, `gcs-and-manifest-delete-safety-protocol.md`). Not durable on its own —
  the next sweep would reintroduce backups unless the sweep also cleans up.
- **C: both** — filter the walk (durable guard) AND clean up the litter (immediate correctness) + add a `.bak`-cleanup
  step to the sweep script's post-run contract.

After the fix, run `build_instrument_catalogue.py --asset-group tradfi --mode full --allow-catalogue-shrink` and
re-verify F/O canonical lands ~99.83%.

## Why the sweep census (99.83%) and the served catalogue (82.90%) disagreed

Denominator mismatch, as suspected: the sweep counts ROWS in the 27,100 `instruments.parquet` files (correctly swept);
the roll-up counts INSTRUMENTS aggregated from EVERY parquet in the prefix (swept + raw backups + old files). The sweep
did its job; the roll-up's over-broad file selection re-injects the raw ids the sweep removed.

## RESOLUTION (2026-07-20) — shipped Option A + verified

Fix shipped `instruments-service@1a73082e`: `_iter_by_date_snapshots` now filters `endswith("/instruments.parquet")` (+
regression test asserting `.bak`/`futures_contracts.parquet` litter excluded, `instruments.parquet` included).
Blast-radius verified read-only for all asset groups before shipping — only tradfi's `futures_contracts.parquet` is a
legitimately-written non-`instruments.parquet` snapshot and it carries NO instrument-id column (`_row_id` -> None,
already dropped by `build_catalogue_dataframe`), so excluding it is a strict no-op; cefi/defi carry only
`instruments.parquet` (+ `.bak` litter); sports/prediction use their own iterators (prediction already filtered
`instruments.parquet`).

Re-ran `build_instrument_catalogue.py --asset-group tradfi --mode full --allow-catalogue-shrink` (the shrink override is
a ONE-TIME need to drop the old raw twins; subsequent runs are stable/growing). SERVED `prod/catalog.parquet`
(generation 1784577660080452, 2026-07-20T20:01:00):

- Rows 1,391,725 -> **836,956** (the 226k+ raw twins collapsed onto their canonical instrument).
- F/O canonical **82.9006% -> 99.8359%** (770,694 / 771,961); **0 raw+canonical twins**.
- Residual non-canonical = **1,267 rows, ALL `QUARANTINE_UNPARSEABLE`** (the legitimate quarantine-by-design floor).
- KRX display names now populate on the served artifact (Samsung Electronics / SK Hynix / Hyundai Motor).

Durable: the filtered walk means future nightly incremental + weekly full runs re-derive only from the swept
`instruments.parquet`, so the 99.83% holds — the `.bak` litter can be left in place as harmless storage (no prod delete
needed).
