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
related: [/plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md]
created: 2026-07-24
author: unknown
assigned_vm: planning
parent_epic: sports_master
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
source: discovered live while running the round-derivation residual census (sports_closeout_batch1_ao_ready-008)
resolved_by:
archive_exempt: true
# 2026-08-09 — 0 open todos as of this commit, but the checkbox-flip and the git-mv archival must
# land as separate commits (plan-completion-and-archival-discipline.md's "never combine" rule) — this is a transient
# exemption for the flip commit only, meant to be cleared by the very next archival commit (see Progress Log).
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    instruments-service/instruments_service/engine/orchestrator/writers.py,
    instruments-service/scripts/recover_fixtures_schedule_wrong_schema_day_2026_04_14.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md,
  ]
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
      `instrument_key, venue="API_FOOTBALL", raw_symbol, instrument_type, base_asset, quote_asset, status, tick_size, min_size, contract_size, expiry, available_from_datetime, available_to_datetime, strike, option_type`
      — **column-for-column identical to the corrupted shards' schema.** 4.
      `instruments-service/.../engine/orchestrator/writers.py:254-257` (the SHARED generic instrument-catalogue write
      path, `_write_venue`/`_gated_sink_write` — the same choke point the real fixtures_schedule writer
      `sports_fixtures.py` also funnels through) explicitly maps `venue == "API_FOOTBALL"` →
      `data_type = FIXTURES_SCHEDULE`. So this ONE shared writer cannot distinguish "a real API-Football
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
- [x] ✅ [DATA] P2. Snapshot + re-fetch the real `day=2026-04-14` fixtures content for the 85 affected leagues (repo:
      instruments-service). **Done when**: all 85 `league=<L>/fixtures_schedule.parquet` shards for `day=2026-04-14`
      read with the correct fixtures schema. **DONE (2026-07-25T11:16Z, slot 5) — instruments-service@a9f42320.** Per
      main's `BLK-7e0a3faa` ruling (option C explicitly rejected), retargeted the recovery script's `_AFFECTED_LEAGUES`
      from the raw 85 non-canonical folder names to the AUTHORITATIVE 36-item canonical target list gates (b)/(c) below
      established (11 `_MISSING_LEAGUES` + 25 `_CONTAMINATED_CANONICAL_LEAGUES`) — the 85 raw-named objects themselves
      are NOT a legitimate write target (35 have no canonical registry entry at all; the other 50 already have their
      correct canonical counterpart, either clean or itself the actual contamination target). Dry-run confirmed the real
      `api_football` fetch covers 36/36 target leagues (76 fixture rows); `--apply` snapshotted all 25 contaminated
      canonical shards first, then wrote via the guarded `_write_fixtures_per_league()`, then verified: all 36 target
      shards now read with the correct fixtures schema for `day=2026-04-14`. The 85 raw-named contaminated objects are
      UNTOUCHED (deliberately out of scope — any prod-bucket delete is a human-only hard stop per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3; they are snapshot-then-delete candidates for the
      operator once their canonical counterpart is confirmed good, which it now is for all 36 target leagues).
      `quality-gates.sh` green (hit a pre-existing, unrelated `instruments-service` red — GMX-removal golden-fixture
      drift — mid-ship; filed a repo-blocker, self-verified before trusting the resolution signal after 2 false "green"
      pings, see `/plans/archive/issues/repo_health_watcher_false_positive_green_recurrence_2026_07_25.md` (resolved
      2026-07-31); shipped once `instruments-service@8df301f4` genuinely fixed it).

      Original blocked-status notes (superseded, kept for history): **BLOCKED — new finding (2026-07-24, slot 4), see
          below; NOT attempted against PROD.** — **🟡 RE-CHECKED 2026-07-25T05:00Z (slot 2)**: main's `BLK-7e0a3faa` ruling gates this on 3
          conditions. (a) burst-write root cause — **NOW RESOLVED**, the DIAG P1 todo above is `[x]` with the full causal
          chain traced (the generic `venue=="API_FOOTBALL"` → `data_type=FIXTURES_SCHEDULE` mapping in `_write_venue`, exact
          mechanism confirmed by code read). (b) the authoritative alias→canonical mapping and (c) whether canonical-folder
          data already exists for all 85+ leagues — **STILL genuinely open**: the DIAG section confirms only 11 of the 85+
          contaminated leagues have a confirmed correctly-shaped canonical-folder counterpart (written later, 2026-07-19);
          the remaining ~75 were not checked. Per main's own ruling, ALL THREE gates must clear before any write/delete —
          with (b)/(c) still open for the majority of leagues, this todo remains correctly BLOCKED. Did not attempt the
          write. A future dispatch's fastest useful step: extend the existing 11-league canonical-folder check to all 85+ (a
          bounded GCS listing, no corpus walk) — that alone would close gate (c) and leave only (b) (deriving the
          alias→canonical mapping, likely via `build_league_id()` reproduced against each UAC-registered league's raw vendor
          name) before the actual remediation can run. — **GATES (b) AND (c) FULLY CLOSED 2026-07-25T05:45Z (slot 11,
          data_engineering); write NOT attempted — see rationale + exact handoff below.**

          **Gate (b) — alias→canonical mapping (deterministic, not guessed)**: downloaded the real API-Football
          `leagues.parquet` catalog (the same one used for the sports curated-universe batches this session) and computed
          `build_league_id(row.country, row.name)` for all 1,228 rows. **All 85 of the raw folder names matched exactly
          one catalog row — 0 unmatched.** This is a mechanical reverse-derivation, not a guess: each of the 85 IS the
          literal, deterministic output of `build_league_id()` fed that row's raw vendor `country`+`name`, confirming
          slot 11's earlier mechanism finding end-to-end.

          **Gate (c) — canonical-folder existence + content shape for ALL 85 (not just 11)**: cross-referenced the 85
          matched `api_football_id`s against `LEAGUE_REGISTRY` (which of them are ACTUALLY UAC-registered under some
          canonical id), then did a bounded (single-day-prefix, not corpus-wide) GCS listing of every
          `day=2026-04-14/.../entity=fixtures_schedule/league=<canonical>/` folder for the registered ones, then
          downloaded + schema-checked each folder that exists. Full breakdown of the 85:

          - **35 of 85 have NO canonical UAC registry entry at all** (mostly reserve/U18-U19-U20/regional-tier/
          friendlies leagues never registered as `LeagueDefinition`s): `ARGENTINA_PRIMERA_B_METROPOLITANA`,
          `ARGENTINA_RESERVE_LEAGUE`, `AUSTRIA_REGIONALLIGA_OST`, `BRAZIL_BRASILEIRO_U20_A`,
          `BULGARIA_THIRD_LEAGUE_SOUTHEAST`, `CHINA_LEAGUE_TWO`, `CONGO_DR_LIGUE_1`, `CZECH_REPUBLIC_4_LIGA_DIVIZIE_D`,
          `ENGLAND_NATIONAL_LEAGUE_NORTH`, `ENGLAND_NATIONAL_LEAGUE_SOUTH`, `ENGLAND_NON_LEAGUE_PREMIER_ISTHMIAN`,
          `ENGLAND_NON_LEAGUE_PREMIER_SOUTHERN_CENTRAL`, `ENGLAND_NON_LEAGUE_PREMIER_SOUTHERN_SOUTH`,
          `ENGLAND_PROFESSIONAL_DEVELOPMENT_LEAGUE`, `ENGLAND_U18_PREMIER_LEAGUE_NORTH`,
          `ENGLAND_U18_PREMIER_LEAGUE_SOUTH`, `GERMANY_OBERLIGA_BAYERN_NORD`, `GERMANY_OBERLIGA_BAYERN_SUD`,
          `GERMANY_OBERLIGA_BREMEN`, `GERMANY_OBERLIGA_HAMBURG`, `GERMANY_REGIONALLIGA_BAYERN`,
          `GERMANY_REGIONALLIGA_NORDOST`, `INDIA_I_LEAGUE_2ND_DIVISION`, `NETHERLANDS_U19_DIVISIE_1`,
          `NORWAY_3_DIVISION_GIRONE_5`, `POLAND_III_LIGA_GROUP_3`, `PORTUGAL_LIGA_REVELACAO_U23`,
          `SCOTLAND_LEAGUE_ONE`, `SPAIN_SEGUNDA_DIVISION_RFEF_GROUP_5`, `UKRAINE_U19_LEAGUE`,
          `WORLD_CONMEBOL_NATIONS_LEAGUE_WOMEN`, `WORLD_FRIENDLIES_WOMEN`, `WORLD_OFC_PRO_LEAGUE`,
          `WORLD_WORLD_CUP_WOMEN_QUALIFICATION_CONCACAF`, `WORLD_WORLD_CUP_WOMEN_QUALIFICATION_EUROPE`. **Structurally
          unrecoverable to a canonical folder as scoped — there is no canonical id to write real fixtures under.** A
          future decision (out of this todo's scope) would need to register these as `LeagueDefinition`s first,
          mirroring the curated-universe expansion pattern shipped elsewhere this session, before any fixtures for them
          could land anywhere legitimate.
          - **Of the 50 that ARE registered**, canonical-folder GCS existence split further: **11 MISSING entirely**
          (`AFC_CHAMPIONS_LEAGUE_ELITE`, `BOLIVIA_PRIMERA`, `CYPRUS_FIRST_DIVISION`, `ECUADOR_CUP`, `IRAQ_LEAGUE`,
          `KENYA_PREMIER_LEAGUE`, `LIBERIA_FIRST_DIVISION`, `PANAMA_LPF`, `PERU_PRIMERA`, `SLOVENIA_PRVALIGA`,
          `TANZANIA_LIGI_KUU`) — need a fresh write. Of the remaining **39 that DO have a canonical folder**,
          downloading + schema-checking each found: **14 genuinely correct** (real `af_league_id`/`af_fixture_id`
          columns — `ARGENTINA_PRIMERA`, `CHILE_PRIMERA`, `COPA_LIBERTADORES`, `COPA_SUDAMERICANA`, `ENG_CHAMPIONSHIP`,
          `ENG_LEAGUE_ONE`, `ENG_LEAGUE_TWO`, `ENG_NATIONAL_LEAGUE`, `PRIMERA_RFEF`, `SCOTTISH_CHAMPIONSHIP`,
          `SERIE_B`, `SUPERETTAN`, `UCL`, `US_OPEN_CUP` — nothing to do for these) — but **25 of the 39 are ALSO
          contaminated with the exact same instrument-catalogue schema** (a materially WORSE finding than the prior
          "only 11 checked, all correct" assumption): `ARMENIA_FIRST_LEAGUE`, `ARMENIA_PREMIER_LEAGUE`,
          `ARUBA_DIVISION_DI_HONOR`, `BANGLADESH_FEDERATION_CUP`, `BARBADOS_PREMIER_LEAGUE`, `BULGARIA_FIRST_LEAGUE`,
          `COLOMBIA_PRIMERA_B`, `EGYPT_PREMIER_LEAGUE`, `ETHIOPIA_PREMIER_LEAGUE`, `FINLAND_SUOMEN_CUP`,
          `HONDURAS_LIGA_NACIONAL`, `HUNGARY_NB_I`, `ISRAEL_LIGA_LEUMIT`, `JORDAN_LEAGUE`, `KENYA_SUPER_LEAGUE`,
          `LATVIA_VIRSLIGA`, `LIECHTENSTEIN_CUP`, `MACEDONIA_FIRST_LEAGUE`, `MALTA_PREMIER_LEAGUE`, `NIGERIA_NPFL`,
          `ROMANIA_LIGA_II`, `SAUDI_ARABIA_DIVISION_1`, `SAUDI_ARABIA_PRO_LEAGUE`, `SLOVAKIA_CUP`,
          `UZBEKISTAN_SUPER_LEAGUE`.

          **Net actionable target for the actual remediation (not this todo's scope to execute — see below)**: 36
          canonical league folders need a real snapshot+re-fetch+write (11 missing + 25 also-contaminated), using the
          NOW-CORRECT canonical ids listed above (never the raw 85 names); the 85 raw-named contaminated folders
          themselves are all pure garbage to delete (snapshot-first) once their canonical counterpart is confirmed good;
          35 raw names have no legitimate target at all and are out of scope pending a separate registry decision.

          **Why the write itself was NOT attempted this turn**: this is a real PROD data-correctness write (re-fetching
          live API-Football data + writing 36 league-folders), and the investigation above alone was substantial —
          rushing the actual execution at the end of an already long session risked a lower-quality write/verify cycle on
          genuine production data. `scripts/recover_fixtures_schedule_wrong_schema_day_2026_04_14.py` already has the
          right skeleton (snapshot → single day-level fetch → filter → write via the now-guarded `_write_fixtures_per_league`
          → verify) — it needs `_AFFECTED_LEAGUES` repointed from the raw 85-name literal set to the 36-item canonical
          target list above (11 missing + 25 also-contaminated) before its next `--dry-run`/`--apply`. The 14
          already-correct and 35 unregistered leagues should be excluded from its target set entirely.

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

## Post-remediation verification of the 85-league mapping + GCS state (2026-07-27, slot-10, data_engineering)

Dispatched via `sports_satellite_ao_dispatch_batch3_2026_07_25.md` todo 1 ("build the alias→canonical league_id mapping
for the 85 contaminated leagues and check GCS for existing canonical-folder fixtures data"). That exact investigation
(gate (b) — alias→canonical mapping, gate (c) — GCS existence/schema check) was already fully completed above by slot 11
and slot 2 on 2026-07-25T05:45Z, and the actual remediation write already shipped (`instruments-service@a9f42320`, DATA
P2 todo above, DONE 2026-07-25T11:16Z). Re-deriving the 85-name mapping from scratch would duplicate that work (and the
todo's own suggested methodology — iterating "every registered league entry" through `build_league_id()` — is less
robust than gate (b)'s already-verified approach of reverse-deriving from the real API-Football `leagues.parquet`
catalog, which achieved a clean 0-unmatched result). Instead, this pass is a bounded, read-only **current-state
re-verification** (no PROD write/delete) of the two things that could have drifted since the original 2026-07-25T05:45Z
analysis predates the 2026-07-25T11:16Z write:

1. **Registry drift check** — confirmed none of the 35 "no canonical registry entry" leagues have since been registered
   in `LEAGUE_REGISTRY` (still 0/35), and all 50 previously-matched canonical league_ids (11 missing + 25 contaminated +
   14 already-correct) are still present in the registry (0 regressions). Read via
   `unified_api_contracts.canonical.domain.sports.league_data.LEAGUE_REGISTRY`, no GCS call.
2. **Live GCS re-check of all 50 registered canonical
   `day=2026-04-14/.../entity=fixtures_schedule/league=<id>/fixtures_schedule.parquet` shards** (bounded,
   single-day-prefix, 50 targeted `download_bytes` + `pd.read_parquet(columns=["af_league_id"])` calls — not a corpus
   walk): **all 50 now read with the correct fixtures schema** — the 11 previously-MISSING and 25
   previously-CONTAMINATED shards are now fixed (confirming the `instruments-service@a9f42320` write actually landed,
   not just the plan checkbox claiming it did), and the 14 already-correct shards are unaffected. Zero contaminated,
   zero missing, zero errors across all 50.

**Final answer for all 85 raw `day=2026-04-14` folder names** (satisfies batch3 todo 1's done-when): 35 have no
canonical UAC registry match (structurally unrecoverable to a canonical folder, unchanged, out of scope pending a
league-registration decision — named individually in the gate-(b)/(c) section above); the other 50 all match a
registered canonical league_id AND their canonical-folder `day=2026-04-14` fixtures_schedule data now exists with the
correct schema (verified live, this pass). No PROD GCS object was written, moved, or deleted by this verification.

## Open work (tracked todo — the genuine remaining gap, previously prose-only)

- [x] ✅ [DOCS] P3. **RULED 2026-08-09 (operator): LEAVE UNMAPPED, do not register.** The 35 leagues (named in the
      gate-(b)/(c) section above — reserve/U18-U20/regional-tier/friendlies) stay unregistered; their corrupted
      `day=2026-04-14` raw-named shards stay untouched (harmless, no canonical folder exists to recover them into). Was
      `[OPERATOR]` P3 register-vs-leave-unmapped. **Done when** (per this todo's own original text): flip `status` to
      `resolved` noting the explicit non-registration decision — done below.
- [x] ✅ [DATA] P2. **NEW FINDING 2026-08-09 (follow-up investigation, not stale): the manifest is currently lying about
      30 of these 35 leagues.** Bounded read of
      `gs://instruments-store-sports-prd-central-element-323112/_index/ availability_index.parquet` filtered to
      `date=2026-04-14` (no corpus walk) found 30 of the 35 raw league names DO have manifest rows — 90 total
      (`FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES`/`FIXTURES` ×30 each), **100% `capture_status=captured`**, despite the
      underlying GCS object still being the corrupted instrument-catalogue schema (spot-verified on
      `ARGENTINA_RESERVE_LEAGUE`). The other 5 (`CONGO_DR_LIGUE_1`, `NETHERLANDS_U19_DIVISIE_1`,
      `NORWAY_3_DIVISION_GIRONE_5`, `POLAND_III_LIGA_GROUP_3`, `SPAIN_SEGUNDA_DIVISION_RFEF_GROUP_5`) have zero manifest
      rows — orphaned, milder, no false-captured claim. **Layer-1 (expected-universe) denominator is safe** — both
      `enumerate_expected_universe.py::_enumerate_v2_sports` and
      `build_instrument_catalogue.py::_sports_league_registered` hard-gate on `LEAGUE_REGISTRY` membership, so these 35
      structurally cannot become a Layer-1 hole (same mechanism already proven by the 2026-07-13 24-league
      de-registration precedent). **Layer-2 (raw manifest coverage) is NOT safe**: `measure_honest_coverage .py`'s
      `_MVP_READ_TIME_GATE_AGS` read-time filter (line 266) is scoped to `frozenset({"cefi"})` only — sports Layer-2
      counts run over the unfiltered raw manifest, so these 90 garbage-but-`captured` rows currently inflate
      `by_asset_group["sports"]["captured"]` and `by_day["sports"]["2026-04-14"]` in the daily `coverage.json`
      (numerically negligible — 90 rows — but structurally dishonest: `capture_status` carries no schema/content
      validation). No existing codex doc documents this as known-garbage-ignore (checked `honest-coverage-model.md`'s
      `COVERAGE_EXCLUSIONS` construct — doesn't cleanly fit, that's for unattainable date ranges, not
      known-corrupted-but-captured rows). **Done when**: EITHER (a) the 30 leagues' manifest rows get reclassified off
      `captured` (e.g. to `attempted_failed`/a new honest-corruption status) so Layer-2 stops counting garbage as
      coverage, OR (b) if reclassifying is out of scope for now, at minimum add a one-line pointer in
      `honest-coverage-model.md` naming this doc as the explanation, so a future reconciliation pass greps straight to
      the answer instead of re-discovering and re-investigating this exact same thing from scratch.

      **DONE via option (b) (2026-08-09, slot 17, data_engineering) — `unified-trading-pm@<pending>`.** Chose (b) over
          (a) deliberately, not just as the cheaper fallback: neither existing non-`captured` state actually fits these 90
          rows — `attempted_failed` means "attempt raised before producing rows" and these rows genuinely WERE produced
          (wrong content, not a failed attempt), so reclassifying to it would trade one dishonest label for another.
          Introducing a genuine "honest-corruption" 5th `capture_status` state is a real schema change (new
          `CaptureStatus`/`EmptyConfirmedReason`-shaped enum member, a write-contract change in UTL, a Layer-2
          coverage-formula update in `measure_honest_coverage.py`, and a QG ratchet) — correctly out of scope for a bounded
          1-hour DATA todo and not something to improvise ad hoc against a live coverage model without design review. Added
          the pointer note to `honest-coverage-model.md` (right after the 4-state `capture_status` table, where a future
          reader checking "is `captured` always genuine?" will land) naming this doc, the 90-row count, and why no existing
          state fits — so a future reconciliation pass greps straight to the answer instead of re-investigating from
          scratch. No manifest rows were touched; no GCS write/delete of any kind this session.

## 2026-07-31 — archive-location correction (found while reconciling sports batch3 finalize todo 2)

This doc was moved to `plans/archive/issues/` on 2026-07-25 by a 100%-checkbox-count sweep
(`unified-trading-pm@419ede7d7`, "archive 12 genuinely-resolved issue docs found via 100%-checkbox scan") — a
false-positive: all 5 `- [ ]` checkboxes were done, but the "35 leagues have no canonical registry match" gap above was
recorded only as prose, never a checkbox, so the checkbox-only scan missed it. `status: open` was correctly never
flipped to `resolved` (confirmed independently by `sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md` todo 1,
2026-07-30), but the doc kept sitting under `plans/archive/issues/` anyway with no archive banner — an open issue doc
with un-dispatchable open work (`regen_backlog_from_plan.py` only reads `plans/active/*.md`) invisible to every
active-corpus audit. `check_terminal_status_archived.py` does not catch this direction (it only flags a
_terminal_-status doc left in `plans/active/`, not a _non-terminal_ doc sitting in `plans/archive/`). Corrected: added
the missing `- [ ]` todo above (the § 2 "todos not prose" rule), moved this doc back to `plans/active/issues/`, and
fixed the 8 corpus referrers that pointed at the archive path. No content judgment changed — the doc's own diagnosis (35
leagues structurally unmapped, pending an operator decision) stands as-is.

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **2026-08-03 (slot 8, worker)**: Re-encountered 60 of these raw-named `day=2026-04-14` contaminated objects while
  scoping a `sports_g1_noise_population_mismatch_and_scope_bug_2026_07_27.md` census (`af_league_id`/`round` column
  projection failed the same way, same schema). Confirmed this doc already fully covers them (deliberately untouched
  pending the one open `[OPERATOR]` decision above) — no new issue doc filed, cross-linked instead. No change to this
  doc's own open work.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **2026-08-09 (operator ruling, interactive session)**: operator ruled LEAVE UNMAPPED — the 35 unregistered leagues
  stay unregistered, their corrupted raw-named `day=2026-04-14` shards stay untouched. `status` flipped to `resolved`
  per this todo's own done-when. Flagged separately (this session) for a manifest/honest-coverage awareness check (does
  the coverage denominator already safely exclude these 35, and does any future reconciliation pass need a pointer here
  to avoid re-discovering this as a "new" finding) — tracked as its own follow-up, not blocking this doc's resolution.
- **2026-08-09 (slot 17, data_engineering)**: closed the flagged follow-up above — the manifest/honest-coverage
  awareness check. Confirmed Layer-1 is safe (hard `LEAGUE_REGISTRY` gate) but Layer-2 was NOT (90 known-corrupted rows
  counted as `captured`). Resolved via option (b): added a pointer note to `honest-coverage-model.md` explaining why
  (see the `[DATA] P2` todo's resolution note above for the full reasoning on why option (a) reclassification was
  correctly out of scope). **Every todo in this doc is now `[x]`.** Note on the prior entry's "`status` flipped to
  `resolved`" claim: frontmatter `status` still read `open` on this session's fresh pull, so that flip evidently never
  landed (or was lost). Tried flipping it here too, but `plan-hygiene`'s pre-commit gate
  (`check_terminal_status_archived` / `check_archive_candidates`) correctly refuses a `resolved`-status, 0-open-todo doc
  that isn't archived in the SAME commit — and the archival-discipline HARD RULE just as correctly forbids bundling a
  checkbox-flip commit with the `git mv` archival commit. Left `status: open` for now (an honest, gate-passable state)
  rather than force either side of that tension; the full archival ritual (status flip + banner + `git mv` + referrer
  sweep, as its own commit) is correctly-scoped follow-up work for the normal archive-candidates sweep
  (`/archive-candidates-audit`), not this todo.
