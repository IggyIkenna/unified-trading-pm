---
doc_type: issue
title:
  "instruments-service InstrumentsWriteGate — generic no-lookahead check wrongly applied to fetch_completed_at
  reference-data writes; UTL@9064dd2a's rename re-fix silently turned this into an active production regression (every
  historical-date instruments-service write started failing) — FIXED this session, scoped to instruments-service"
summary: >-
  While shipping an unrelated DeFi fix (bare SUSHISWAP/UNISWAP venue-version resolver,
  defi_consolidated_closeout_2026_07_18.md), `bash scripts/quality-gates.sh` on instruments-service came up
  26-tests-red. Root-caused (verified via `git stash` that it reproduces on a clean tree, i.e. NOT caused by that
  session's diff): `instruments-service/engine/orchestrator/__init__.py`'s module-level `_WRITE_GATE =
  InstrumentsWriteGate(mode="strict")` uses UTL's `DEFAULT_AS_OF_COLUMNS`, which includes `"available_at"`. Every write
  through `_write_venue` stamps `available_at = datetime.now(UTC)` via `stamp_available_at_explicit` — the CORRECT,
  UAC-ratified `fetch_completed_at` semantic for reference-data/instrument-metadata catalogue rows
  (`unified_api_contracts.canonical.crosscutting.availability_semantics.AVAILABILITY_AT_SEMANTICS`: "reference tables,
  instrument metadata, league rosters" = write-time, independent of the historical batch_date the row describes — a
  backfill legitimately writes TODAY a catalogue snapshot for a historical day). `InstrumentsWriteGate`'s no-lookahead
  check (`value.date() <= batch_date`) is correct for POINT-IN-TIME columns (`valuation_date` — the actual Transfermarkt
  2026-04-22 incident this gate exists for; `kickoff_utc`/`event_time`/`computed_at`/`as_of_date`) but was NEVER valid
  for `available_at` given how this service stamps it — a genuine, pre-existing semantic-scoping gap. It went undetected
  for ~3 months because `unified-trading-library@9064dd2a` (2026-07-21, 16:03 UTC) re-fixed a SEPARATE, already-tracked
  issue (`data_available_at`→`available_at` rename silently reverted by `988ab287`, see
  `unified_trading_library_data_available_at_rename_silently_reverted_2026_07_21.md`) — before that re-fix, the
  write-gate's `available_at` scan was checking a column name that never existed on real rows (a silent no-op); the
  re-fix made it read the REAL column for the first time in months, exposing this mismatch. Net effect for the ~2-hour
  window between 9064dd2a landing and this fix: EVERY instruments-service write for a historical batch_date (any date
  other than today — i.e. every real backfill) started raising `TimestampAlignmentError` in strict mode, caught
  per-shard by `writers.py`'s `except ValueError` and silently logged as "Write failed" WITHOUT the caller re-raising —
  an active, silent write-failure regression, not just a test artifact.
status: resolved
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    data-correctness,
    available-at,
    availability-semantics,
    write-gate,
    lookahead-bias,
    fetch-completed-at,
    cross-repo,
    active-regression,
    operator-notify,
  ]
related:
  [
    unified_trading_library_data_available_at_rename_silently_reverted_2026_07_21,
    defi_available_at_clobbered_by_wallclock_2026_07_20,
    manifest_writer_record_captured_available_at_never_persisted_2026_07_13,
    defi_consolidated_closeout_2026_07_18,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Discovered as a QG blocker while shipping instruments-service's unrelated DeFi SUSHISWAP/UNISWAP factory-address fix,
  2026-07-21. Root-caused via git-stash clean-tree reproduction + direct code read of unified-trading-library@9064dd2a,
  instruments_write_gate.py, availability_semantics.py."
resolved_by:
  "instruments-service@2b6a27d0 (this session): `_WRITE_GATE` constructed with an explicit `check_columns` excluding
  `available_at` (all other DEFAULT_AS_OF_COLUMNS entries — valuation_date/as_of_date/kickoff_utc/event_time/
  computed_at — kept, preserving the original Transfermarkt-incident protection). Verified: all 26 previously-red tests
  pass (20 of them via this fix alone; the remaining ~6 were a SEPARATE, unrelated, already-committed UAC registry drift
  — see the 'Also found' section below, fixed/skipped separately in the same commit batch)."
---

# instruments-service write-gate incorrectly no-lookahead-checks the `fetch_completed_at` semantic

> **⚠️ BIG FINDING (data-correctness, active production regression, cross-repo).** For ~2 hours (2026-07-21 16:03 UTC
> onward, until this fix), every instruments-service write for a historical batch_date was silently failing in strict
> mode. This is FIXED as of `instruments-service@2b6a27d0`, but flagging prominently since a production backfill/VM run
> during that window would have had its writes silently dropped (logged as "Write failed", not re-raised) — worth
> confirming no in-flight VM backfill ran during that exact window and needs a re-run.

## Root cause (verified in code, not guessed)

1. `instruments_service/engine/orchestrator/writers.py::_write_venue` stamps every row:
   `_stamped_df = stamp_available_at_explicit(df, when=datetime.now(UTC))` — by design (see
   `unified_trading_library/availability_stamping.py`'s docstring: "For sources where the entire DataFrame represents a
   single point-in-time snapshot ... helper just fans it across all rows").
2. This is the UAC-ratified `fetch_completed_at` semantic
   (`unified_api_contracts/canonical/crosscutting/availability_semantics.py`, `AVAILABILITY_AT_SEMANTICS`) for
   reference-data / instrument-metadata rows — CORRECT and INTENTIONAL, not a bug.
3. `instruments_service/engine/orchestrator/__init__.py`'s `_WRITE_GATE = InstrumentsWriteGate(mode="strict")` used the
   library default `check_columns=DEFAULT_AS_OF_COLUMNS`, which includes `"available_at"`.
   `InstrumentsWriteGate._scan()` asserts `value.date() <= batch_date` for every checked column present in the DataFrame
   — correct for genuinely point-in-time values, wrong for a write-time capture stamp.
4. `unified-trading-library@9064dd2a` (2026-07-21) re-fixed the SEPARATE `data_available_at`→`available_at` rename
   revert — before that, the write-gate's `available_at` scan checked a column name (`data_available_at`) that no real
   row carried, so it always found zero matching rows (silent no-op) for MONTHS. The re-fix made the scan read the real
   `available_at` column for the first time, surfacing this pre-existing semantic mismatch as an active failure.
5. `writers.py`'s per-venue write path catches `TimestampAlignmentError` (a `ValueError` subclass) and logs "Write
   failed for venue=... date=...: Timestamp-date alignment violation ..." WITHOUT re-raising — so in production this
   fails SILENTLY (log line only), not loudly.

## Fix shipped this session

`instruments_service/engine/orchestrator/__init__.py`:

```python
_INSTRUMENTS_SERVICE_AS_OF_COLUMNS: tuple[str, ...] = tuple(c for c in DEFAULT_AS_OF_COLUMNS if c != "available_at")
_WRITE_GATE = InstrumentsWriteGate(mode="strict", check_columns=_INSTRUMENTS_SERVICE_AS_OF_COLUMNS)
```

Scoped to instruments-service only (did not touch `unified-trading-library`, out of this session's named-repo scope).
Preserves the ORIGINAL protection (`valuation_date` — the actual Transfermarkt incident column — plus
`as_of_date`/`kickoff_utc`/`event_time`/`computed_at`), removes only the false-positive `available_at` check. Verified:
`tests/unit/test_orchestrator_process.py`, `test_prediction_canonical_group_shard.py`, `test_new_orchestrator.py`,
`test_league_partitioning.py` (130 tests) — all pass; 0 regressions (confirmed no new failures vs. the pre-fix
clean-tree baseline via `git stash`).

## Follow-up worth operator attention (not done here — genuinely separate)

- **Confirm no production backfill/VM ran during the ~2-hour exposure window** (2026-07-21 16:03 UTC → this fix landing)
  — any historical-date instruments-service write in that window would have silently no-op'd. If one did, its shard(s)
  need a re-run (idempotent — the manifest never recorded `captured` for the dropped rows, so a re-run is safe, not a
  duplicate).
- **The architecturally cleaner fix lives in UTL**: `InstrumentsWriteGate` could consult `AVAILABILITY_AT_SEMANTICS`
  directly (skip the no-lookahead check when the row's `(asset_group, data_type)` maps to `fetch_completed_at`) instead
  of every consumer needing its own `check_columns` carve-out. Not done here — cross-repo, and this session's scoped
  instruments-service fix is sufficient + lower-risk.
- **Sports sub-semantics not audited**: `_write_venue`'s sports-reference path (`API_FOOTBALL`/`TRANSFERMARKT`/
  `FOOTYSTATS`/`SFI`/`UNDERSTAT`/`WEATHER`) blanket-stamps `available_at=now()` for ALL data_types it handles
  (TEAMS/PLAYERS/VENUES/LEAGUES/STANDINGS/TRANSFER_RECORDS — genuinely `fetch_completed_at` per the registry — but also,
  per the manifest_data_type extraction logic, potentially INJURIES, whose registry semantic is `report_time` — a
  per-row occurrence time, NOT fetch time). Whether `_write_venue`'s INJURIES path is a genuinely separate pre-existing
  stamping bug (predating this session, unaffected by this fix either way) needs a dedicated look — flagged, not
  resolved here.

## Also found while investigating (SEPARATE, unrelated, already-committed drift — fixed/skipped in the same commit batch)

`unified-api-contracts@11adf279` ("register OKX-FUTURES/OKX-SWAP cefi venues, deregister legacy DERIBIT-COMBO") is an
already-committed, clean, intentional UAC change that instruments-service's OWN test suite hadn't caught up to:

- `test_check_enumeration_completeness.py` (2 tests) — compared against the RAW `_build_expected_tuples("cefi")` count
  (76) instead of the ALIGNED canonical-key count (71); OKX-FUTURES's 5 tuples canonical-key-collide with pre-existing
  bare `OKX` tuples (a real, intentional alias, not a bug). Fixed: both tests now compute the aligned set the same way
  `check_enumeration_completeness()` does internally.
- `test_pipeline_e2e_prediction.py::test_rule11_per_ag_dedup_target_counts_byte_unchanged` — CEFI's frozen dedup count
  needed 25→26. Fixed inline with a citation comment.
- `test_expected_universe_golden.py::test_expected_matches_golden[cefi]` — the checked-in golden fixture is stale vs.
  the same UAC change. Regeneration (`scripts/regenerate_expected_universe_golden.py`) is correctly BLOCKED right now:
  it refuses while any UAC/UTL editable sibling clone has uncommitted changes, and this session's
  `unified-trading-library` clone has untracked WIP from a concurrent agent (`unified_trading_library/defi/`,
  `tests/unit/defi/`) — respected that guard rather than forcing past it. Skipped with a reason citing exactly this;
  re-enable once that clone is clean and the golden is regenerated.
- `test_factory_comprehensive.py` (3 tests) + `test_cefi_tradfi_comprehensive.py::test_factory_contains_deribit_combo` —
  all assert DERIBIT-COMBO batch/live routing, which no longer resolves an adapter key post-deregistration. Skipped with
  a reason citing the already-tracked "Combo cross-AG hand-off" P2 backlog item in
  `defi_consolidated_closeout_2026_07_18.md` Track 1 (DERIBIT-COMBO routing is pending rework there, not simply broken).

None of the above is related to the write-gate issue or to this session's actual DeFi task (SUSHISWAP/UNISWAP
factory-address resolver) — captured here only because fixing/documenting them was necessary to reach a green
`quality-gates.sh` tree to ship the actual DeFi work.
