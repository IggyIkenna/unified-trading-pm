---
title:
  "instruments-service write-gate — fail loud on batch-date vs row-timestamp misalignment (catch §5 data-crimes at
  source)"
priority: P1
status: active
owner: agent
created: 2026-04-22
locked_by: live-defi-rollout
locked_since: 2026-04-22
type: code
epic: none
completion_gates:
  code: C5
  deployment: none
  business: none
repo_gates:
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
depends_on: []
isProject: false
---

## Context

On 2026-04-22 we killed VM `tm-backfill-20260421-231758` after 18 hours of wasted compute because:

1. The orchestrator's Transfermarkt short-circuit passed `season=None`, defaulting to `datetime.now(UTC).year` (= 2026)
   for every historical batch date.
2. The Transfermarkt adapter stamped `valuation_date = datetime.now(UTC).strftime(...)` when the API omitted the field —
   today's wall-clock on every historical-backfill row.

Both are direct §5 data-crimes per codex `02-data/sports-scheduling-and-sharding.md` ("never write today's value onto a
2018 fixture"). Both landed on HEAD and ran for 18h on a VM before being caught **by visual inspection of logs**, not by
any automated guardrail. Fixes in FSS commit `cdded95`.

**The architectural gap**: UTL has three layers of point-in-time validation (`validate_timestamp_date_alignment`,
`PointInTimeEnforcer`, `validate_pit_safety`), but **instruments-service bypasses all of them**. Grep confirmed zero use
in `instruments-service/instruments_service/engine/orchestrator.py`. Only `features-sports-service` write-gate uses
them. So the raw-data layer has no fail-loud at write time for batch-date vs row-timestamp misalignment — the very
invariant §5 cares about.

This plan closes that gap: every raw-data sink write in instruments-service goes through a UTL write-gate that asserts
`row.timestamp_like_column` aligns with the batch `date` partition before the parquet lands on GCS. When misaligned,
emit `DATA_ALIGNMENT_VIOLATION`, fail the write, and (configurable) either abort the shard or record_failed in the
manifest.

## Blast radius

| Repo                                                                                     | Scope                                                                                               |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| unified-trading-library                                                                  | Extend existing `validate_timestamp_date_alignment` to cover the `as_of_date` / `valuation_date` /  |
| `data_available_at` column families used by raw-data adapters (not just feature writes). |
| instruments-service                                                                      | Every `sink.write(...)` in `orchestrator.py` gates through the new write-gate call. ~30 call sites. |
| unified-trading-pm                                                                       | Codex `06-coding-standards/validation-patterns.md` adds the write-gate rule.                        |

## PRE-AUDIT-FINDINGS (2026-04-22 — agent)

### Existing UTL validators + their current callers

- [`unified_trading_library/point_in_time.py`](../../../unified-trading-library/unified_trading_library/point_in_time.py):
  `PointInTimeEnforcer`, `enforce_point_in_time`, `validate_pit_safety`. Filter-based; suits feature writes.
- [`unified_trading_library/feature_service_base/write_gate.py`](../../../unified-trading-library/unified_trading_library/feature_service_base/write_gate.py)
  L322: calls `validate_timestamp_date_alignment` — but only via `FeatureWriteGate` in feature services.
- **Zero callers in instruments-service** (grep confirmed 2026-04-22).

### Raw-data adapters already emit batch-date-aligned timestamps (sometimes)

Most sports adapters write parquets with a `data_available_at` column — but it's typically stamped with
`datetime.now(UTC)` at write time, not derived from the batch date. Going forward, the rule should be:

> For every raw-data parquet written at `by_date/day={D}/entity={E}/...`, every row-level date / timestamp column
> (valuation_date, as_of_date, data_available_at, kickoff_utc, event_time, etc.) MUST satisfy
> `row.timestamp.date() <= D` (no-lookahead). Writes that violate this fail at the gate.

### Two deployable shapes

1. **Strict mode (default)**: misalignment raises `TimestampAlignmentError` → caller's per-shard try/except catches it
   and records `attempted_failed` in the manifest. No parquet written. Forces adapter fix.
2. **Warn mode**: log + emit `DATA_ALIGNMENT_VIOLATION` event + proceed with write. Useful during migration when some
   adapters aren't yet compliant.

Rollout: warn-mode first to measure violation volume; strict-mode once all adapters are clean.

## Pre-audit manifest

| File / thing to find                                                                          | Purpose                                                                       | Expected outcome                                                                              |
| --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `unified_trading_library/feature_service_base/write_gate.py`                                  | Reference impl of `FeatureWriteGate` for feature writes.                      | Mirror shape for instruments write-gate.                                                      |
| `unified_trading_library/canonical/domain/timestamp_alignment.py` (if exists, else new)       | Where `validate_timestamp_date_alignment` lives.                              | Extend to accept `column_candidates=["valuation_date", "as_of_date", ...]` list + batch date. |
| `instruments-service/instruments_service/engine/orchestrator.py` `sink.write(...)` call sites | Count + classify writes: per-date raw adapter writes vs summary/index writes. | ~30 call sites expected. Each gets a `validate_and_write(df, partition, batch_date)` wrapper. |
| UTL `events` registry                                                                         | Add `DATA_ALIGNMENT_VIOLATION` event def.                                     | Payload: `{venue, entity, date, column, offending_value, row_count}`.                         |
| Codex `06-coding-standards/validation-patterns.md`                                            | Document the rule.                                                            | Add a §Timestamp-Alignment-Gate subsection.                                                   |

## Success criteria

- UTL: `InstrumentsWriteGate.validate_and_write(df, partition, batch_date)` helper ships. Unit-tested with positive
  (compliant) + negative (wall-clock row on historical batch) cases.
- instruments-service: every `sink.write(...)` in `orchestrator.py` goes through the gate. Warn-mode enabled in prod;
  count of `DATA_ALIGNMENT_VIOLATION` events over 1 week baselines the cleanup scope.
- Codex: §Timestamp-Alignment-Gate subsection added, cross-referenced from §5 lookahead-bias rules.
- Regression test: a simulated adapter return with `datetime.now(UTC)` stamped row on a 2023-03-16 batch emits
  `DATA_ALIGNMENT_VIOLATION`, blocks the write (strict mode), and `record_failed`s the shard.

## Phases

### Phase 0: Audit sink.write call sites + existing UTL validator [SEQUENTIAL]

- [x] [AGENT] P0. Grep `instruments_service/engine/orchestrator.py` for `sink.write(`. ~40 sites: - A (per-date, gate
      applies): TM player_values L4563, SFI_LEAGUES L4719, SFI_STANDINGS L4835, SFI progressive_stats L4898,
      API-Football predictions L1676/L1728/L3643/L3679, api-football teams/standings/injuries L2691/L2744/L2807,
      footystats matches/odds L3881/L4044, understat xG L4237/L4251, fixtures L3002, predictions-empty L1349,
      api-football leagues L4380. ~30 Category A. - B (mapping/index, no `day=` partition — gate no-ops safely):
      team_mapping L3278, fixture_mapping L3331, league_team_mapping L3403/L3469, venues L2421.

- [x] [AGENT] P0. `validate_timestamp_date_alignment` in UTL `domain/timestamp_validation.py:169` is feature-specific
      (single `timestamp_col` kwarg with auto-detect). Extending it would break downstream FeatureWriteGate. New
      dedicated module `unified_trading_library/instruments_write_gate.py` built instead, with `check_columns`
      parameter. SSOT decision: library ships the gate; the old validator stays specialised for FSS.

- [x] [AGENT] P0. `datetime.now(UTC)` grep across adapters produced 33 hits. Sports-adapter wall-clock stamps (most
      likely §5 data-crime shapes): `transfermarkt.py:224` (season fallback — orchestrator `cdded95` fix guards at the
      call site but adapter still has it), `footystats.py:161` (identical shape:
      `effective_season = season if season is not None else datetime.now(UTC).year`), `api_football.py:73`
      (reference_date default — benign if always passed), `open_meteo.py:84/210` (90-day cutoff — operational, not
      data-stamp). Live-mode adapters (tradfi/cefi/prediction `updated_at=datetime.now(UTC)`) emit current-universe
      asset metadata by design, not historical per-date data — out of scope for this gate.

### Phase 1: UTL InstrumentsWriteGate [SEQUENTIAL, depends on Phase 0]

- [x] [AGENT] P0. `unified_trading_library/instruments_write_gate.py` ships
      `InstrumentsWriteGate.validate_and_write(sink, data, partition, filename, venue, entity, ...)` +
      `TimestampAlignmentError`. Checks `DEFAULT_AS_OF_COLUMNS` =
      (`as_of_date, valuation_date,     data_available_at, kickoff_utc, event_time, computed_at`) for
      `value.date() <= batch_date`. Shipped in UTL `c1987760`.

- [x] [AGENT] P0. `DATA_ALIGNMENT_VIOLATION` event registered in `events/event_types.py` + re-exported in
      `events/__init__.py`. Shipped in UTL `c1987760`.

- [x] [AGENT] P0. 15 unit tests in `tests/unit/test_instruments_write_gate.py`: compliant, none-values, empty-df,
      no-`day=`-partition, timezone-aware, TM-incident warn/strict, multi-column misalignment, custom `check_columns`,
      frozen `ColumnViolation` dataclass, malformed `day=` partition, default-column-family guardrail. 15/15 green.

### Phase 2: Wire instruments-service [SEQUENTIAL after Phase 1]

- [x] [AGENT] P0. Added module-level `_WRITE_GATE = InstrumentsWriteGate(mode="warn")` +
      `_gated_sink_write(sink, *, data, partition, filename, venue, entity)` helper in `engine/orchestrator.py`.
      Replaced the 4 highest-risk §5 data-crime seats with the helper: TM PLAYER_VALUES (L4560), SFI_LEAGUES (L4719),
      SFI_STANDINGS (L4835 — currently unreachable, guarded for future re-enable), SFI progressive_stats (L4898).
      Shipped in instruments-service `454cca3`. Remaining ~26 Category-A sites (API-Football
      predictions/odds/injuries/matches/xg, footystats, understat) deferred to Phase 3 follow-up — warn-mode volume will
      tell us which adapters still wall-clock-stamp.

- [ ] [AGENT] P1. Extend per-shard try/except blocks to catch `TimestampAlignmentError` explicitly +
      `manifest.record_failed(row_key=..., error="ALIGNMENT_VIOLATION", ...)`. Not critical while warn mode is the
      default (no raises happen); required before Phase 3 strict-mode flip.

- [x] [AGENT] P0. 6 regression tests in `tests/unit/test_orchestrator_write_gate.py` cover module-level gate shape,
      compliant pass-through, TM-incident warn-mode emit-but-write, SFI progressive_stats kickoff+timer_seconds
      compliance, mapping-partition no-op, strict-mode raise+skip. 6/6 green (shipped in instruments-service `454cca3`).

### Phase 3: Measurement + codex [SEQUENTIAL — operator + follow-up]

- [x] [AGENT] P1. Expanded warn-mode coverage from 4 → 25 sites in instruments-service `d049d8b`. Every sports per-date
      `sink.write(...)` now goes through `_gated_sink_write`: API-Football
      leagues/teams/standings/injuries/fixtures/per*fixture*\* (14 sites), FootyStats predictions/matches/odds (9
      sites), Understat xG (3 sites), Transfermarkt leagues (1 site; PLAYER_VALUES was 454cca3), SFI
      leagues/standings/progressive_stats (3 sites, 454cca3), OpenMeteo weather (1 site), plus 4 instrument-universe
      per-date writes (DeFi/CeFi/TradFi/Prediction; gate no-ops today but catches future `computed_at` /
      `data_available_at` schema drift). 8 new TestVenueParityCases tests added, 14/14 green. Mapping / index / cache
      writes (no `day=` partition) intentionally left plain — gate would no-op.

- [ ] [AGENT] P1. After ≥ 1 week of warn-mode in prod, query `events.jsonl` for `DATA_ALIGNMENT_VIOLATION` count per
      `venue` + `entity` + `column`. Document baseline here.

- [ ] [AGENT] P1. Fix adapters surfaced by warn-mode baseline. Known candidates from Phase 0 grep:
      `transfermarkt.py:224` + `footystats.py:161` both still carry
      `effective_season = season if season is not None else datetime.now(UTC).year`. Harden the adapter-side fallback
      even though orchestrator `cdded95` guards the call site.

- [ ] [AGENT] P1. Flip default to `mode="strict"` in `_WRITE_GATE`. Per-shard try/except catches
      `TimestampAlignmentError` → `manifest.record_failed(..., error="ALIGNMENT_VIOLATION")`.

- [x] [AGENT] P1. Shipped codex §Timestamp-Alignment-Gate in
      [`/codex/06-coding-standards/validation-patterns.md`](/codex/06-coding-standards/validation-patterns.md).
      Cross-ref §5.1 added in
      [`02-data/sports-scheduling-and-sharding.md`](/codex/02-data/sports-scheduling-and-sharding.md) (§5.1).

### Phase 4: QG + quickmerge [SEQUENTIAL]

- [x] [AGENT] P0. UTL 15/15 new unit tests + typecheck clean on added files.
- [x] [AGENT] P0. instruments-service 6/6 new unit tests + 160 basedpyright errors are pre-existing (none introduced by
      the gate wiring).
- [x] [AGENT] P0. Commit + push in dep order: UTL `c1987760` + `c397ab56` → instruments-service `454cca3` → PM (this
      commit). `quickmerge --agent` skipped due to concurrent-agent dirty deps (see CLAUDE.md); used
      `git commit --no-verify + git push` with scoped `git add <files>` per the dirty-deps feedback rule.
- [ ] [HUMAN] P0. Approve unlock once strict-mode has run in prod for ≥ 3 days with zero alignment violations.

## Dependency graph

```
Phase 0 (audit sink.write + validator + wall-clock grep) [SEQUENTIAL]
      │
      └─► Phase 1 (UTL InstrumentsWriteGate)            [SEQUENTIAL]
             │
             └─► Phase 2 (Wire instruments-service)    [SEQUENTIAL]
                    │
                    ├─► Phase 3 (Measure + clean up + strict-mode + codex)
                    │
                    └─► Phase 4 (QG + quickmerge + HUMAN unlock)
```

## SSOT cross-refs

- Lookahead-bias rule: codex `02-data/sports-scheduling-and-sharding.md` §5.
- Existing FSS write-gate: `unified-trading-library/unified_trading_library/feature_service_base/write_gate.py`
  - `feature_service_base/`.
- Point-in-time enforcement: `unified_trading_library/point_in_time.py`.
- Observed violation commits (both fixed): instruments-service `cdded95` (TM season-derivation + valuation_date
  None-pass-through).

## Out of scope

- MTDS + features-\* services — they already use `FeatureWriteGate` through feature_service_base. No new work.
- External-venue adapters (CeFi / DeFi / TradFi market data) — they have their own validation patterns (candle-time
  alignment is already checked in MTDS). This plan is scoped to sports reference-data adapters in instruments-service.
- Cross-repo enforcement of the rule via SIT / pre-commit hook — Phase 3 leaves this as a follow-up if warn-mode reveals
  systemic non-compliance.
