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

- [x] ✅ [DIAG] P1. Identify the batch job/writer that ran for `day=2026-04-14` and produced instrument-catalogue-shaped
      output under the `entity=fixtures_schedule` path (repo: instruments-service). **Done when**: a written root-cause
      conclusion cites the specific writer code path and why its target resolved to the fixtures_schedule prefix.
      **RESOLVED (2026-07-24, slot 11)** — see the full causal chain below: the specific writer code path is
      `instruments_service/engine/orchestrator/writers.py:254-257` (`_write_venue`), and it resolved to the
      fixtures_schedule prefix because that ONE shared choke point maps `venue=="API_FOOTBALL"` to
      `data_type=FIXTURES_SCHEDULE` regardless of whether the payload is a real fixture or a generic `InstrumentRecord`
      — reachable whenever `api_football` (registered as a plain generic venue in UAC's `venue_adapter_keys.py`) appears
      in a run's top-level `venues` list outside the dedicated sports fixture flow. The exact historical CLI invocation
      that triggered it on 2026-07-16 is unrecoverable (no GCS Data Access audit logging on this bucket), but the
      mechanism is fully explained and structurally closed by the CODE todo below. **ATTEMPTED, DEAD END (2026-07-24,
      slot 5)**: checked the current `_write_fixture_entity_per_league` / `_gated_sink_write` write path — it faithfully
      writes whatever `df` it's given, so the bug (if still present) would be in a CALLER passing the wrong DataFrame,
      not this function itself. Checked `scripts/migrate_sports_per_league.py` (landed `instruments-service@6b5952ba`,
      2026-04-15 — the day AFTER the incident date, plausible timing) — but its `ALL_ENTITIES` list never includes
      `fixtures`/`fixtures_schedule`, so it cannot be the direct writer either. `git log` on the affected files/callers
      around 2026-04-10..04-18 shows no commits — the code active on 2026-04-14 predates the later
      `engine/orchestrator.py` cohesion-module split, and no archived run logs from that exact day are available
      in-session. Could not pin the exact historical call site with the tools available; NOT closing this todo — leaving
      it open for whoever has access to that era's deployment/run logs. The CODE P1/P2 todos below don't depend on
      finding it: a structural guard that rejects this CLASS of mix-up regardless of cause was shipped instead (see
      below). **FOLLOW-UP (2026-07-24, slot 12) — the premise "incident date = 2026-04-14" is WRONG; the actual write
      happened 2026-07-16, not April.** `git log`-based investigation (above) necessarily assumed the corrupted objects
      were WRITTEN around their `day=` partition value. They were not — GCS object metadata
      (`gcs_describe_object`/`list_blobs` via UTL, read-only, no corpus walk — single-day, single-league bounded
      listings) tells a different story: - All 85 corrupted `league=<L>/fixtures_schedule.parquet` objects under
      `day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures_schedule/` carry `updated` timestamps clustered
      in a **<1-second window**: `2026-07-16T09:59:21.462Z` through `2026-07-16T09:59:22.039Z` (verified by listing all
      117 objects under that day's `entity=fixtures_schedule/` prefix and sorting by `updated`). Sizes are uniform
      (~8.0–9.5 KB), consistent with the instrument-catalogue shape, not the ~26 KB real fixtures shape seen elsewhere
      in the same listing. - A 118th object (`league=WORLD_WORLD_CUP_WOMEN_QUALIFICATION_EUROPE`, not in the original
      85-count sample) is ALSO instrument-catalogue-shaped (confirmed by downloading + `pd.read_parquet` — same
      `instrument_key`/ `tick_size`/`venue`/... columns), written even earlier at `2026-07-12T23:10:14Z` — so the true
      affected count for this one day is at least 86, and the corruption event was not a single atomic write. - A
      <1-second burst writing 85 files is not a live production writer (no api-football HTTP calls would clear that
      fast, even with zero rate-limiting) — this is the signature of an **in-memory script/migration loop** that
      iterated something league-shaped and wrote the same (or per-item) instrument-catalogue-derived DataFrame to each
      `league=` partition, not the real per-league fixtures fetch path. -
      `instruments_service/reference_data/adapters/sports/__init__.py:21` has a literal `date="2026-04-14"` — but it's a
      **module-docstring usage example**, not executable code; several unit tests
      (`test_sports_dependency_enforcement.py`, `test_sports_dependency_bucket.py`) also hardcode this exact date as a
      fixture-parameter constant, always paired with an explicit `-test-` bucket. None of these are wired to run against
      the prod bucket, so none is directly implicated — but the shared literal supports the theory that `2026-04-14` is
      an arbitrary/canonical **test-fixture date**, not evidence of a real April incident. - Checked
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
      section assumes, and should inform anyone else picking this up. **IN PROGRESS (2026-07-24, slot 11)**: picked up
      from slot 4's "recommended next step" — dispatched a read-only Explore sub-agent to search the full workspace
      (current code + `git log --all -S` history) for the "COUNTRY_LEAGUENAME" full-name convention
      (`ENGLAND_CHAMPIONSHIP`, `SAUDI_ARABIA_PRO_LEAGUE`, etc.). **MECHANISM FOUND (2026-07-24, slot 11) — resolves the
      "why do the 85 folder names not match any UAC registry" mystery, verified by direct code read (not just the
      sub-agent's report):** 1. `unified-api-contracts/.../canonical_ids.py::build_league_id(country, league_name)`
      returns `f"{_slug(country)}_{_slug(league_name)}"` — a straight uppercase-slug concatenation, **never an
      abbreviation**. Its own docstring example (`"England"` → `"ENG"`) is simply WRONG on its face — `_slug("England")`
      == `"ENGLAND"`. There is no abbreviation step anywhere in this function. 2.
      `unified-api-contracts/.../external/api_football/normalize.py:137` feeds this function the RAW vendor
      `country`/`league.name` strings (`build_league_id(raw.league.country, raw.league.name)`) for EVERY normalized
      fixture — so `CanonicalFixture.league.league_id` is BORN as `"ENGLAND_CHAMPIONSHIP"`-shaped, never the abbreviated
      `ENG_CHAMPIONSHIP` UAC-registry form (`league_data_prediction.py:33`). The 85 folder names are not a mystery
      convention at all — they're this exact, always-unabbreviated computation, which is why they never appear as a
      literal string anywhere in code/git history (confirmed clean by the sub-agent's `git log --all -S` sweep) — the
      string is COMPUTED at runtime, never hardcoded. 3.
      `instruments-service/.../adapters/sports/adapters/api_football_reference.py::_canonical_fixture_to_instrument()`
      converts a `CanonicalFixture` (carrying that raw league_id) into an `InstrumentRecord` with fields
      `instrument_key, venue="API_FOOTBALL", raw_symbol, instrument_type, base_asset, quote_asset, status,        tick_size, min_size, contract_size, expiry, available_from_datetime, available_to_datetime, strike,        option_type`
      — **column-for-column identical to the corrupted shards' schema.** 4.
      `instruments-service/.../engine/orchestrator/writers.py:254-257` (the SHARED generic instrument-catalogue write
      path, `_write_venue`/`_gated_sink_write` — the same choke point the real fixtures_schedule writer
      `sports_fixtures.py` also funnels through) explicitly maps `venue == "API_FOOTBALL"` →
      `data_type =        FIXTURES_SCHEDULE`. So this ONE shared writer cannot distinguish "a real API-Football
      fixtures_schedule write" from "an API-Football-venue `InstrumentRecord` write" — both resolve to the identical
      `data_type=FIXTURES_SCHEDULE` target. If `ApiFootballReferenceDataAdapter.get_instruments()`'s output (or any
      DataFrame shaped like it) was ever routed through `_write_venue`, this mapping alone would silently misfile it
      into the fixtures_schedule GCS path — exactly the corruption observed, exact schema, exact venue-derived
      data_type.

      **FULL CAUSAL CHAIN TRACED (2026-07-24, slot 11)**: `unified-api-contracts/registry/venue_adapter_keys.py:191`
                  registers `"API_FOOTBALL": "api_football"` in the SAME generic venue→adapter-key registry crypto/defi/tradfi
                  venues use — `api_football` is not a sports-only special case, it's a first-class generic venue. Top-down:
                  `process.py:150` computes `active_venues = [v for v in venues if is_venue_available(v, date)]` from the
                  top-level `venues` param → `process_fetch.py`'s fetch stage splits `active_venues` into `defi_active`
                  (`v in defi_venue_names`) vs. `non_defi_active` (**everything else, unconditionally** — line 125, no
                  sports/prediction exclusion) → `non_defi_active` (line 172) calls `fetch_instruments_for_all_venues(...)` →
                  `urdi_reference_provider.py` resolves the adapter via `get_adapter_for_canonical_venue()` and calls
                  `.get_instruments()` → for `api_football` this is `ApiFootballReferenceDataAdapter.get_instruments()`, returning
                  `InstrumentRecord`s built by `_canonical_fixture_to_instrument()` (item 3 above) → these records flow back into
                  `process_fetch.py`'s generic instrument pipeline and eventually reach `_write_venue`/`_gated_sink_write`, which
                  (item 4 above) maps `venue=="API_FOOTBALL"` to `data_type=FIXTURES_SCHEDULE` — landing exactly at the corrupted
                  path. **The bug is structural, not a one-off typo**: if the top-level `venues` list for ANY run ever includes
                  `"api_football"` (or `"API_FOOTBALL"`) OUTSIDE the dedicated sports fixture flow
                  (`_orch._fetch_sports_reference_data`, the CORRECT writer confirmed in `process_fetch.py:253` — takes its own
                  separate `api_football_key` path and writes via `record_captured_from_counts`, never touching `_write_venue`),
                  this exact corruption reproduces. **Still not pinned down**: which specific CLI invocation / cron / script
                  populated the top-level `venues` param with `api_football` on 2026-07-16 (and 07-12 for the 118th file) — that
                  requires either historical run logs (already confirmed unavailable — no GCS Data Access audit logging on this
                  bucket, per slot 12's finding) or finding a config/registry state where `api_football` was reachable from a
                  non-sports-scoped `--asset-group` selection at that time. The regression guard shipped for the CODE todo below
                  (`_assert_not_cross_domain_contamination`) makes this class of mix-up impossible going forward regardless of
                  which exact caller triggered it historically — closing the loop even without the historical "who".

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
      read with the correct fixtures schema. **BLOCKED — new finding (2026-07-24, slot 4), see below; NOT attempted
      against PROD.**

## New finding — the 85 "affected league" folder names are not registered UAC canonical league_ids at all (2026-07-24, slot 4)

Built `scripts/recover_fixtures_schedule_wrong_schema_day_2026_04_14.py` (dry-run only, no PROD write) to re-fetch
`api_football`'s real fixtures for `day=2026-04-14` (single day-level call, mirroring
`_ensure_canonical_fixtures_for_override`'s pattern) and filter to the 85 affected leagues. The live dry-run fetch
succeeded broadly (substantial real fixture data returned across many leagues, confirmed via the fixed
`CANONICAL_LEAGUE_ID_LOOKUP_MISS` warning firing repeatedly for OTHER numeric ids resolving to real data) — but
**matched 0 of the 85 target leagues, 0 fixture rows total.**

Investigated whether this is genuine honest-absence (plausible on its face — many of the 85 are reserve/U18-U20/
regional lower-division leagues) vs a bug, by checking the UAC registry directly for 3 of the 85 (all major,
should-obviously-be-tracked leagues): `get_league("ENGLAND_CHAMPIONSHIP")`, `get_league("ITALY_SERIE_B")`,
`get_league("SAUDI_ARABIA_PRO_LEAGUE")` — **all three return `None`.** A workspace-wide grep of `unified-api-contracts/`
for the literal string `"ENGLAND_CHAMPIONSHIP"` returns **zero hits anywhere** — the actual registered prediction-tier
canonical id for this league is the abbreviated `ENG_CHAMPIONSHIP` (`league_data_prediction.py:33`), a materially
different string shape (`ENGLAND_CHAMPIONSHIP` vs `ENG_CHAMPIONSHIP` — not a case/whitespace variant, a different
abbreviation convention entirely).

**Conclusion: the 85 "affected league" strings extracted directly from the bad shards' `league=<X>` folder names are not
UAC `api_football` canonical league_ids under ANY tier/registry function checked — they use an entirely different,
longer "COUNTRY_LEAGUENAME" naming convention.** This means:

1. My dry-run's "0 of 85 covered" result is NOT evidence of honest-absence — it's a naming-convention mismatch in the
   filter itself (`_canonical_league_id()` on a real af_league_id would never produce e.g. `ENGLAND_CHAMPIONSHIP`, only
   `ENG_CHAMPIONSHIP`), so the filter could never match regardless of whether real fixtures exist.
2. The wrong-schema shards' partition names are therefore NOT derived from a normal `_canonical_league_id()` call at all
   — reopens the still-unresolved DIAG P1 todo above (which writer produced this content) with a NEW clue: the
   partition-name generator for these 85 bad writes used a naming scheme that exists nowhere in the current registry,
   which may narrow down which historical code path is responsible (or point to a different provider's own internal
   league-naming convention — SoccerFootballInfo/Understat/Transfermarkt/FootyStats all have their own adapters and
   could plausibly use a fuller "COUNTRY_LEAGUE" convention, consistent with the issue's own "wrote its OTHER product to
   the fixtures_schedule path" hypothesis).
3. **Not safe to proceed with the re-fetch-and-write recovery as scoped** until this is resolved: writing real fixtures
   data keyed to a canonical league_id would land in a DIFFERENT partition (the correctly-canonicalized one, e.g.
   `league=ENG_CHAMPIONSHIP`) than the currently-broken one (`league=ENGLAND_CHAMPIONSHIP`) — so even a successful
   fetch+write would NOT fix the shard this todo names; it would create a new, correctly-schemaed shard elsewhere while
   leaving the bad one exactly as broken as before.

**Recommended next step (superseded by slot 11's mechanism finding above — see the `[DIAG] P1` todo)**: slot 11
confirmed the 85 folder names are NOT a fixtures-domain naming convention at all — they're the raw, unabbreviated
`build_league_id(country, league_name)` string a `CanonicalFixture.league.league_id` is born with, misrouted through the
SHARED `_write_venue`/`_gated_sink_write` choke point's `venue=="API_FOOTBALL" → data_type=FIXTURES_SCHEDULE` mapping
when fed an `InstrumentRecord`-shaped DataFrame instead of real fixtures data. **This means the recovery model in this
todo (re-fetch fixtures and write them under these 85 literal names) is wrong regardless of naming — these 85 objects
were never meant to exist as fixtures_schedule shards under ANY name; they are contamination, not misfiled-but-real
fixtures data.** The correct remediation is now more likely: (1) verify whether real fixtures_schedule data for
`day=2026-04-14` already exists under each affected league's CORRECT canonical folder (`league=ENG_CHAMPIONSHIP` etc. —
the normal daily writer may be unaffected by this contamination bug and already have it), (2) only backfill via a normal
re-fetch for any CANONICAL-folder gaps found, scoped to real canonical ids (not this doc's 85-name list), (3) delete the
85 contaminated objects once their canonical counterparts are confirmed complete (same snapshot-before-delete discipline
as any other prod object removal). The recovery script built this session
(`scripts/recover_fixtures_schedule_wrong_schema_day_2026_04_14.py`, dry-run-only, `--apply` never run, no PROD object
touched/snapshotted) implements the WRONG model (step 4 of its docstring, "writes real fixtures under the 85 literal
names") and needs rewriting against this corrected understanding before any `--apply` run — do not treat it as
ready-to-run without that fix.

## Deferred work after 2026-07-24 (slot 4 session end)

| Item                                                                                        | State / why deferred                                                                                                                                                               | Blocked on                                                                                                                                    |
| ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `[DATA] P2` — remediate the 85 contaminated `day=2026-04-14` shards                         | **Not done, not attempted against PROD.** Recovery model itself was wrong (see above) until slot 11's mechanism finding landed mid-session — needs a rewrite, not just an unblock. | Real work — pick up with the corrected 3-step remediation above once someone has capacity.                                                    |
| `[DIAG] P1` — find the exact caller that fed `get_instruments()` output into `_write_venue` | **Not done**, but the MECHANISM is now fully understood (slot 11) — only the specific calling job/script is still unidentified.                                                    | Real work — trace `ApiFootballReferenceDataAdapter.get_instruments()` callers workspace-wide (named as the concrete next action in the todo). |

**Recommended next item**: the DIAG P1 caller-trace (cheap, bounded, unblocks nothing else urgent) or the DATA P2 step-1
canonical-folder verification (also cheap — a manifest/GCS check, no write) are both good next picks; the actual
re-fetch+delete (steps 2-3) should wait until whichever of those two is done, so the blast radius of any write is fully
understood first.

## Main's ruling on BLK-7e0a3faa (2026-07-24, slot 4)

Main answered slot 4's `/blocked` question (options A: park / B: resolve myself / C: write under both paths) with
**Decision A — park, re-scope later; C explicitly REJECTED** (writing real fixtures under the literal bad-shard folder
name targets a non-canonical partition and would multiply the exact duplicate/divergent-shard problem slot 12 already
found — never write real data to a partition known to be wrong). B was also declined: slot 12 owns the deeper DIAG in
this same doc with live findings already in hand, so slot 4 defers to that investigation rather than racing it. DATA P2
stays **BLOCKED**, gated on slot 12's DIAG resolving (a) the burst-write root cause, (b) the authoritative
alias→canonical mapping, and (c) whether canonical-folder data already exists — no write or delete happens before all
three are answered. `instruments-service@a6cb0439` (the recovery script) is fine to keep as scaffolding; it needs its
target partition corrected once the mapping is authoritative, per the corrected 3-step model above. Slot 4 is moving on
to other backlog work per this ruling.

- [x] ✅ [CODE] P2. Add a schema assertion (column-set check) at the fixtures_schedule writer so a future mismatch fails
      loud instead of silently producing an unreadable-by-projection shard (repo: instruments-service). **Done when**: a
      unit test feeds a wrong-schema DataFrame into the writer and asserts a loud failure. — Same commit as the P1 todo
      above (`instruments-service@b3cb6f8c`) — the guard + its regression test satisfy both todos; not duplicating the
      work under a second commit.
