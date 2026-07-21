---
doc_type: issue
title:
  instruments-service cefi golden fixture (cefi.json) is stale vs. a same-day UAC correctness fix — BITFINEX-FUTURES
  FUTURE itype removal blocks the whole repo's quality-gates.sh
summary: |
  `bash scripts/quality-gates.sh` (full run, not scoped by --files) fails
  `tests/unit/scripts/test_expected_universe_golden.py::TestGoldenByteIdentical::test_expected_matches_golden[cefi]`
  on a clean instruments-service checkout at LDR HEAD: `golden=76, actual=73`, missing 3 tuples
  (`('BITFINEX-FUTURES', 'future', 'book_snapshot_5')`, `('BITFINEX-FUTURES', 'future', 'derivative_ticker')`,
  `('BITFINEX-FUTURES', 'future', 'trades')`). Root cause: `unified-api-contracts@5b57c2b2 fix(registry): drop
  phantom BITFINEX-FUTURES FUTURE itype (cefi G4 Layer-1)` (landed today, 2026-07-12) removed the
  `("BITFINEX-FUTURES", "FUTURE")` Tardis-exchange mapping and narrowed `venue_constants.INSTRUMENT_TYPES_BY_VENUE
  ["BITFINEX-FUTURES"]` to `{"PERPETUAL"}` only — a legitimate, well-evidenced fix (commit message cites live Tardis
  metadata confirming bitfinex-derivatives serves perpetual-only, zero FUTURE-typed instruments) — but
  instruments-service's own checked-in `cefi.json` golden fixture was never regenerated to match. Same failure class
  as the already-resolved `instruments_service_qg_red_golden_drift_2026_07_10.md` (UAC capability-registry change
  landing ahead of instruments-service's golden regen), just a different tuple set. This blocks EVERY
  instruments-service `quality-gates.sh` run (and therefore every quickmerge --agent ship) workspace-wide until fixed —
  hit while shipping an unrelated P1 fix (`reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12`), confirmed
  byte-identical on a `git stash`-clean tree with that unrelated diff removed.
status: superseded
nature: notes
asset_group: [cefi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [honest-coverage, golden-fixture, qg-red, cross-repo, bitfinex, cefi, duplicate]
related:
  [
    instruments_service_qg_red_golden_drift_2026_07_10.md,
    instruments_service_cefi_golden_bitfinex_futures_drift_2026_07_12.md,
    ../reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12.md,
  ]
created: 2026-07-12
parent_epic: instruments_master
priority: P1
source:
  orchestrator task reconcile_phantom_manifest_rows_stale_read_overwrite-001 (slot 7, data_engineering) — discovered
  while running `bash scripts/quality-gates.sh` for an unrelated reconciler staleness-guard fix; verified pre-existing
  via `git stash` (byte-identical failure on a clean tree)
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
superseded_by: instruments_service_cefi_golden_bitfinex_futures_drift_2026_07_12.md
audited_scope: single-repo-qg-run
---

> **DUPLICATE — superseded by
> [`instruments_service_cefi_golden_bitfinex_futures_drift_2026_07_12.md`](instruments_service_cefi_golden_bitfinex_futures_drift_2026_07_12.md)**,
> filed first (slot-6) for the identical drift. This doc's root-cause finding (`unified-api-contracts@5b57c2b2`) has
> been merged into that doc's Todos. Kept for the investigation record; do not action the todo below separately — track
> the fix via the superseding doc.

# instruments-service cefi golden drift — BITFINEX-FUTURES FUTURE itype removed same-day, golden not regenerated

## What I found

Running `bash scripts/quality-gates.sh` for instruments-service (scoped `--files` to my own unrelated reconciler change)
fails at `[3/6] TESTS`:

```
FAILED tests/unit/scripts/test_expected_universe_golden.py::TestGoldenByteIdentical::test_expected_matches_golden[cefi]
AssertionError: EXPECTED matrix drift for 'cefi':
  golden=76, actual=73
  missing (in golden but not actual, first 10): [('BITFINEX-FUTURES', 'future', 'book_snapshot_5'),
  ('BITFINEX-FUTURES', 'future', 'derivative_ticker'), ('BITFINEX-FUTURES', 'future', 'trades')]
  extra   (in actual but not golden, first 10): []
```

Verified pre-existing (not caused by my diff): `git stash push -u`, re-ran
`.venv/bin/python -m pytest tests/unit/scripts/test_expected_universe_golden.py -k cefi` on the clean tree — byte
identical failure, same 76/73 counts, same 3 missing tuples. `git stash pop` restored my diff cleanly afterward.

Root cause, `unified-api-contracts` git log on `venue_mapping.py` / `venue_constants.py`:

```
5b57c2b2 fix(registry): drop phantom BITFINEX-FUTURES FUTURE itype (cefi G4 Layer-1)
```

landed TODAY (2026-07-12). Diff content confirmed via `git show`/grep:

- `venue_mapping.py` (~line 828): `("BITFINEX-FUTURES", "PERPETUAL"): "bitfinex-derivatives"` kept; the sibling
  `("BITFINEX-FUTURES", "FUTURE")` entry removed, with an inline comment:
  `# ("BITFINEX-FUTURES", "FUTURE") REMOVED 2026-07-12 (cefi G4 Layer-1 gap): live Tardis metadata confirms bitfinex-derivatives serves perpetual only, zero FUTURE-typed instruments`.
- `venue_constants.py` (~line 434): `INSTRUMENT_TYPES_BY_VENUE["BITFINEX-FUTURES"]` narrowed from
  `{"PERPETUAL", "FUTURE"}` to `{"PERPETUAL"}` only.

This is a legitimate, well-evidenced UAC-side correctness fix (removing a phantom capability that never had live data) —
NOT a regression to revert. But `instruments-service/tests/unit/scripts/goldens/expected_universe/cefi.json` (the
checked-in golden `build_expected('cefi')` is diffed against) still expects the 3 now-removed
`('BITFINEX-FUTURES', 'future', *)` tuples, because nobody regenerated it after `5b57c2b2` landed.

Exact same failure CLASS as the already-resolved `instruments_service_qg_red_golden_drift_2026_07_10.md`: a UAC
capability-registry commit lands, instruments-service's golden fixture goes stale, `quality-gates.sh` goes red
workspace-wide for every agent shipping in this repo until someone regenerates the fixture. That issue's resolution
(`instruments-service@23d53f69`) already built the correct tool for this:
`scripts/regenerate_expected_universe_golden.py` — refuses to write unless both `unified-api-contracts` and
`unified-trading-library` sibling path-dependency clones are `git status --porcelain`-clean (prevents baking uncommitted
local state into the checked-in fixture, the root cause of the ORIGINAL 2026-07-10 incident).

I did not run the regeneration myself: at the time of this investigation my own `unified-trading-library` sibling clone
was dirty (my own in-flight, unrelated `reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12` UTL change),
which the script's own safety-check would correctly refuse against.

## Why it matters

Blocks `quality-gates.sh` — and therefore `quickmerge --agent` — for EVERY agent shipping ANY change in
instruments-service, not just cefi/BITFINEX-related work, until the golden is regenerated. Per
`codex/02-data/honest-coverage-model.md` / the golden test's own docstring, a stale EXPECTED-universe golden is "the
single most dangerous failure mode of Honest Coverage v2" — right now it's LOUD (the test is doing its job), but it is a
repo-wide ship-blocker in the meantime.

## Recommended decision

SUPERSEDED — tracked as the (now-closed root-cause, open fix) todo #2 in
`instruments_service_cefi_golden_bitfinex_futures_drift_2026_07_12.md`. Not re-listed as an actionable checkbox here to
avoid a duplicate backlog-derived task.

## Progress Log

- **2026-07-12 (slot-7, data_engineering)** — Filed while shipping an unrelated P1 reconciler fix
  (`reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12`); root-caused to `unified-api-contracts@5b57c2b2`
  via `git log`/`grep` (see "What I found"). Declared a repo-blocker for instruments-service so the backend's
  RepoHealthWatcher notifies waiters on green. Did not attempt the fixture regen myself — out of this task's craft
  scope/time budget, and my own UTL sibling clone was dirty at investigation time (the regen script correctly refuses
  against a dirty path-dependency).
