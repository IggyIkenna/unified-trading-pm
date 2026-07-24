---
doc_type: issue
title:
  Sports fixtures_schedule day=2026-04-14 — 85 league shards carry an instrument-catalogue schema, not fixtures data
summary:
  85 `entity=fixtures_schedule` parquet shards under `day=2026-04-14` (across 85 distinct leagues) fail to read with the
  fixtures schema (`af_league_id`, `season`, `round`, ...) and instead resolve to an instrument-catalogue/registry
  schema (`instrument_key`, `venue`, `instrument_type`, `raw_symbol`, `base_asset`, `quote_asset`, `tick_size`, ...).
  Discovered incidentally while scanning the sports fixtures corpus for the round-derivation residual backfill.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, data-correctness, schema-mismatch, fixtures-schedule]
related: [/plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md]
created: 2026-07-24
assigned_vm: planning
parent_epic: sports_master
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
source: discovered live while running the round-derivation residual census (sports_closeout_batch1_ao_ready-008)
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# Sports fixtures_schedule day=2026-04-14 — wrong-schema shards (instrument-catalogue content in a fixtures path)

## How this was found

While running a corpus-wide census of `sports_reference/by_date/.../entity=fixtures_schedule/` parquets (single walk,
projecting `af_league_id`/`season`/`round`) to scope the round-derivation residual backfill
(`sports_closeout_batch1_ao_ready-008`), 85 of 45,032 files raised a pyarrow column-projection error instead of reading
normally:

```
No match for FieldRef.Name(af_league_id) in instrument_key: string
venue: string
instrument_type: string
raw_symbol: string
base_asset: string
quote_asset: string
status: string
available_from_datetime: timestamp[us, tz=UTC]
...
tick_size: decimal128(2, 2)
min_size: decimal128(1, 0)
contract_size: decimal128(1, 0)
...
```

This is not a malformed/corrupt parquet — the file reads fine, it just carries a **completely different schema**: an
instrument-catalogue/registry shape (`instrument_key`, `venue`, `instrument_type`, `raw_symbol`, `base_asset`,
`quote_asset`, `tick_size`, `min_size`, `contract_size`, `available_from_datetime`/`available_to_datetime`,
`asset_class`, `option_type`/`underlying`/`margin_type`/`legs` for derivatives, `regular_open_utc`/`holiday_calendar`
for trading-calendar data, `available_at`, plus pyarrow dataset bookkeeping columns `__fragment_index`, `__batch_index`,
`__last_in_fragment`, `__filename`). None of that matches sports fixtures data
(`af_fixture_id`/`af_league_id`/`season`/`round`/team names/scores/kickoff time).

## Scope measured

**All 85 affected files share exactly one `day=` partition: `day=2026-04-14`.** Confirmed via the same corpus census —
zero other days showed this failure across the full 45,032-file walk. Affected leagues span a wide, unrelated set
(sampled: `ARGENTINA_RESERVE_LEAGUE`, `ARMENIA_FIRST_LEAGUE`, `ARUBA_DIVISION_DI_HONOR`, `AUSTRIA_REGIONALLIGA_OST`,
`ENGLAND_CHAMPIONSHIP`, `ENGLAND_LEAGUE_TWO`, `EGYPT_PREMIER_LEAGUE`, `HUNGARY_NB_I`, and many more — 85 total, no
obvious pattern by region/tier that would explain a legitimate content match). All paths follow the pattern:

```
sports_reference/by_date/day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures_schedule/league=<LEAGUE>/fixtures_schedule.parquet
```

## Why it matters

- Any reader that projects only the columns it expects (as the round-derivation script and this census both do) will
  silently skip these 85 shards as "unreadable" rather than surfacing the corruption loudly — a `honest-absence`
  violation risk if a downstream consumer instead does a blanket `pd.read_parquet(path)` and gets back an
  instrument-catalogue DataFrame it doesn't validate the shape of.
- This blocks the round-derivation residual backfill (and any other content-dependent job) from ever closing gaps for
  these 85 (league, day) shards — they can't be scanned for `round` at all.
- The failure mode (identical wrong schema across 85 unrelated leagues, one single day) points at a **write-path bug**,
  not per-league data quality — most likely a batch job that, for this one day's run, wrote its OTHER product
  (instrument catalogue / registry snapshot) to the fixtures_schedule path instead of (or in addition to) the real
  fixtures payload — e.g. a bucket/path variable reused across two write calls in the same batch run.

## Recommended decision

1. Confirm the write-path bug: find whichever batch job ran for `day=2026-04-14` and produced an instrument-catalogue
   shape, and trace how its target path resolved to `sports_reference/.../entity=fixtures_schedule/league=<L>/...`
   instead of wherever the catalogue actually belongs.
2. Snapshot the 85 objects (GCS soft-delete already provides a 7-day window; snapshot to `.bak` before touching, same
   convention as the round-derivation scripts) then re-fetch/re-derive `day=2026-04-14`'s real fixtures content for
   these 85 leagues once the write-path bug is fixed — do not leave a hole for this day.
3. Add a schema assertion at the writer (or a post-write validation step) so this class of mix-up fails loud instead of
   silently producing an unreadable-by-projection shard.

## Todos

- [ ] [DIAG] P1. Identify the batch job/writer that ran for `day=2026-04-14` and produced instrument-catalogue-shaped
      output under the `entity=fixtures_schedule` path (repo: instruments-service). **Done when**: a written root-cause
      conclusion cites the specific writer code path and why its target resolved to the fixtures_schedule prefix.
      **ATTEMPTED, DEAD END (2026-07-24, slot 5)**: checked the current `_write_fixture_entity_per_league` /
      `_gated_sink_write` write path — it faithfully writes whatever `df` it's given, so the bug (if still present)
      would be in a CALLER passing the wrong DataFrame, not this function itself. Checked
      `scripts/migrate_sports_per_league.py` (landed `instruments-service@6b5952ba`, 2026-04-15 — the day AFTER the
      incident date, plausible timing) — but its `ALL_ENTITIES` list never includes `fixtures`/`fixtures_schedule`, so
      it cannot be the direct writer either. `git log` on the affected files/callers around 2026-04-10..04-18 shows no
      commits — the code active on 2026-04-14 predates the later `engine/orchestrator.py` cohesion-module split, and no
      archived run logs from that exact day are available in-session. Could not pin the exact historical call site with
      the tools available; NOT closing this todo — leaving it open for whoever has access to that era's deployment/run
      logs. The CODE P1/P2 todos below don't depend on finding it: a structural guard that rejects this CLASS of mix-up
      regardless of cause was shipped instead (see below). **FOLLOW-UP (2026-07-24, slot 12) — the premise "incident
      date = 2026-04-14" is WRONG; the actual write happened 2026-07-16, not April.** `git log`-based investigation
      (above) necessarily assumed the corrupted objects were WRITTEN around their `day=` partition value. They were not
      — GCS object metadata (`gcs_describe_object`/`list_blobs` via UTL, read-only, no corpus walk — single-day,
      single-league bounded listings) tells a different story: - All 85 corrupted `league=<L>/fixtures_schedule.parquet`
      objects under `day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures_schedule/` carry `updated`
      timestamps clustered in a **<1-second window**: `2026-07-16T09:59:21.462Z` through `2026-07-16T09:59:22.039Z`
      (verified by listing all 117 objects under that day's `entity=fixtures_schedule/` prefix and sorting by
      `updated`). Sizes are uniform (~8.0–9.5 KB), consistent with the instrument-catalogue shape, not the ~26 KB real
      fixtures shape seen elsewhere in the same listing. - A 118th object
      (`league=WORLD_WORLD_CUP_WOMEN_QUALIFICATION_EUROPE`, not in the original 85-count sample) is ALSO
      instrument-catalogue-shaped (confirmed by downloading + `pd.read_parquet` — same `instrument_key`/
      `tick_size`/`venue`/... columns), written even earlier at `2026-07-12T23:10:14Z` — so the true affected count for
      this one day is at least 86, and the corruption event was not a single atomic write. - A <1-second burst writing
      85 files is not a live production writer (no api-football HTTP calls would clear that fast, even with zero
      rate-limiting) — this is the signature of an **in-memory script/migration loop** that iterated something
      league-shaped and wrote the same (or per-item) instrument-catalogue-derived DataFrame to each `league=` partition,
      not the real per-league fixtures fetch path. - `instruments_service/reference_data/adapters/sports/__init__.py:21`
      has a literal `date="2026-04-14"` — but it's a **module-docstring usage example**, not executable code; several
      unit tests (`test_sports_dependency_enforcement.py`, `test_sports_dependency_bucket.py`) also hardcode this exact
      date as a fixture-parameter constant, always paired with an explicit `-test-` bucket. None of these are wired to
      run against the prod bucket, so none is directly implicated — but the shared literal supports the theory that
      `2026-04-14` is an arbitrary/canonical **test-fixture date**, not evidence of a real April incident. - Checked
      `scripts/smoke_matrix.py` (an instrument-catalogue-cell smoke-test harness that DOES iterate many cells fast,
      matching the burst signature) — it resolves its target via `resolve_test_bucket()` (always a `-test-`-suffixed
      bucket name), so it is not an obvious match either, though a silent test-bucket-resolution fallback to prod was
      not exhaustively ruled out. - Cloud Logging: `resource.type="gcs_bucket"` Data Access entries for this bucket in
      the `2026-07-16T09:58–10:01Z` window returned **zero entries** — Data Access audit logging is not enabled for this
      bucket, so the calling identity/job cannot be recovered from GCP audit trail. This is a genuine dead end for
      identifying WHO ran it, not just an exhausted search. - **Separately** (worth a follow-up, not this todo's scope):
      the SAME `day=2026-04-14/entity=fixtures_schedule/` prefix also holds 11 correctly-fixtures-shaped (~26 KB),
      CORRECTLY-shaped objects under duplicate ALIAS league codes (`ENG_CHAMPIONSHIP` vs `ENGLAND_CHAMPIONSHIP`, `UCL`
      vs `WORLD_UEFA_CHAMPIONS_LEAGUE`, `SERIE_B` vs `ITALY_SERIE_B`, etc.), written even later — a slower burst
      spanning `2026-07-19T04:23–06:22Z` (~1 write/minute, consistent with a real per-league re-fetch). This looks like
      a SEPARATE bug (duplicate/legacy league-code writes) coexisting in the same prefix; not investigated further here
      — flagging so it isn't mistaken for part of THIS incident's fix scope. - Net: real root cause (the specific
      script/job) still not found — leaving this todo open, as slot 5 did — but the corrected timeline
      (write=2026-07-16, not April) is a materially different fact than what the issue doc's "Recommended decision"
      section assumes, and should inform anyone else picking this up.
- [x] ✅ [CODE] P1. Fix the write-path bug so no future run can write a non-fixtures schema under
      `entity=fixtures_schedule/` (repo: instruments-service). **Done when**: a regression test reproduces the old
      bad-path resolution and asserts the fix. — Could not pin the EXACT historical bug (see the DIAG todo above), so
      implemented the structural fix instead: `instruments-service@b3cb6f8c` adds
      `_assert_not_cross_domain_contamination()` at `_gated_sink_write` (the single choke point every sports_reference
      entity write funnels through), scoped via UAC's `_SPORTS_ENTITY_TO_PIPELINE_MODE` registry so it only fires for
      genuine sports entities (NOT the shared choke point's other callers — the real CeFi/TradFi/DeFi
      instrument-catalogue writers, whose rows legitimately carry these same columns; the first, unscoped cut of this
      broke `test_orchestrator_process.py`/`test_orchestrator_futures_contracts.py`/`test_new_orchestrator.py`, caught
      by the full `quality-gates.sh` run before shipping). Regression test
      `tests/unit/test_sports_reference_cross_domain_contamination_guard.py` replays the exact day=2026-04-14 shape
      (`instrument_key`/`tick_size`/`base_asset`/... columns) through `_gated_sink_write` for `entity=fixtures_schedule`
      and asserts it raises before reaching the sink, plus asserts real fixtures data still passes and non-sports
      entities remain unaffected. `quality-gates.sh` green.
- [ ] [DATA] P2. Snapshot + re-fetch the real `day=2026-04-14` fixtures content for the 85 affected leagues (repo:
      instruments-service). **Done when**: all 85 `league=<L>/fixtures_schedule.parquet` shards for `day=2026-04-14`
      read with the correct fixtures schema.
- [x] ✅ [CODE] P2. Add a schema assertion (column-set check) at the fixtures_schedule writer so a future mismatch fails
      loud instead of silently producing an unreadable-by-projection shard (repo: instruments-service). **Done when**: a
      unit test feeds a wrong-schema DataFrame into the writer and asserts a loud failure. — Same commit as the P1 todo
      above (`instruments-service@b3cb6f8c`) — the guard + its regression test satisfy both todos; not duplicating the
      work under a second commit.
