---
doc_type: issue
title:
  Sports fixtures_schedule — 6,678 rows across 485 leagues under raw af_league_id folders; 99.6% are for leagues NOT in
  the registry at all (corrects the original "registry-growth timing lag" theory)
summary: >-
  Originally — 86 in-window, registry-member blank-round rows sit under non-canonical `league=<raw_af_league_id>`
  (numeric-string) folders instead of the canonical `league=<CANONICAL_ID>` folder, invisible to the canonical-folder-
  scoped round-derivation backfill. A 2026-07-24 corpus-wide manifest census (single read, not a walk) found the REAL
  population is far larger — 6,678 rows / 485 distinct league_ids — and, critically, only 2 of those 485 leagues are
  explained by the original "registry hadn't caught up yet" theory; the other 483 (99.6% of rows) are af_league_ids that
  are STILL not in the UAC registry today, meaning fixtures are being fetched/written for leagues far outside the
  tracked scope — a fetch-side scoping question, not just a write-side canonicalization timing bug.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, data-correctness, canonical-naming, fixtures-schedule, non-canonical-path]
related:
  [
    /plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md,
    /plans/active/issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md,
  ]
created: 2026-07-24
assigned_vm: planning
parent_epic: sports_master
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
source: discovered live while running the round-derivation residual backfill (sports_closeout_batch1_ao_ready-008)
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# Sports fixtures_schedule — non-canonical raw-af_league_id folders hold unreachable blank-round rows

## How this was found

Running the round-derivation residual backfill (`sports_closeout_batch1_ao_ready-008`), a corpus census reported 486
in-window (season>=2019), registry-member blank-`round` rows across 10 (af_league_id, season) pairs. Running
`backfill_sports_fixture_round_2026_07_17.py --apply` against all 10 pairs applied **zero** fills despite genuine API
fetches succeeding for most pairs (e.g. 309/557/558 fixtures fetched per pair). Direct inspection of the canonical
`league=CHINA_SUPER_LEAGUE` folder (af_league_id=169) showed all 9 of its rows for season=2026 already fully populated —
the reported blanks for that pair didn't live there at all.

A targeted concurrent scan for `af_league_id==169, season==2026` across **every** folder (not just the canonical one)
found the real blanks: 36 rows, **100% under `league=169`** — a folder named with the raw numeric `af_league_id` instead
of the canonical string (`CHINA_SUPER_LEAGUE`). Example paths:

```
sports_reference/by_date/day=2026-05-05/pipeline_mode=batch_api_football/entity=fixtures_schedule/league=169/fixtures_schedule.parquet
sports_reference/by_date/day=2026-05-06/pipeline_mode=batch_api_football/entity=fixtures_schedule/league=169/fixtures_schedule.parquet
```

Re-running the full corpus census with a canonical-vs-non-canonical split (folder name is purely numeric, or the
day-level bare/multi-league parquet) confirmed this is not isolated to one league: **86 of the 486 reachable blanks sit
under non-canonical folders**, leaving 400 in genuinely canonical folders (of which 393 are honest-absence — `J2_LEAGUE`
season 2026 not yet published — and 7 are ordinary fetch-miss residue, both matching the exact terminal- state
categories the 2026-07-19 sweep already established as acceptable).

## Why this is a bug, not a naming variant

`backfill_sports_fixture_round_2026_07_17.py`'s `_league_blob_index()` groups blobs by the `/league=<X>/` path segment
and only ever queries `X` values present in its `universe` dict, which is built from the UAC registry
(`get_leagues_by_classification` over `prediction`/`reference`/`features`) keyed by **canonical** league_id strings
(e.g. `CHINA_SUPER_LEAGUE`). A raw numeric folder name (`league=169`) is never a canonical id, so it is silently
excluded from every scoped run — not because the league is out of registry scope (169 IS a registered af_id, just under
the wrong path), but because the **path itself** was written wrong. The round-derivation day-pool script
(`derive_sports_fixture_round_2026_07_18.py`) is folder-agnostic (groups by the `af_league_id` **column**, not the
path), so it WOULD close these if a canonical-folder sibling existed for the same day — but for the dates observed, no
canonical sibling exists that day, so even the folder-agnostic mechanism can't help.

This is the same defect CLASS as the day=2026-04-14 wrong-schema finding
(`sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`) but a different manifestation: a writer occasionally
resolves the canonical league_id lookup to the raw af_id instead, and writes the shard there.

## Scope measured (2026-07-24, two independent corpus census runs agree exactly)

| population                                                                                                                                |    rows | reachable by existing mechanism?                          |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ------: | --------------------------------------------------------- |
| in-window, registry-member, canonical folder, honest absence (`J2_LEAGUE` 99:2026, season not yet published)                              |     393 | yes — attempted, correctly 0-filled                       |
| in-window, registry-member, canonical folder, fetch-miss residue (`EREDIVISIE` 88:2025, 7 specific fixtures not in the bulk season fetch) |       7 | yes — attempted, correctly 0-filled                       |
| **in-window, registry-member, NON-canonical folder (raw af_league_id or bare)**                                                           |  **86** | **no — structurally invisible to `_league_blob_index()`** |
| **total reachable (registry-member, in-window)**                                                                                          | **486** | —                                                         |

Confirmed `league=169` (CHINA_SUPER_LEAGUE) alone accounts for 36 of the 86; the remaining ~50 are spread across the
other affected pairs (not yet individually enumerated — see todo below).

## Root-cause conclusion (2026-07-24, slot 5)

**Confirmed: a registry-growth / write-time-lookup-miss bug, not a runtime race or a code defect in the canonicalizer's
logic itself — the canonicalizer behaves exactly as designed, but "designed" includes a silent, non-loud fallback that
this bug exploits.**

The write path is `instruments_service.engine.orchestrator.sports_reference_fixtures.py:692`
(`partition={"entity": entity_name, "league": _orch._canonical_league_id(_pf_lid_str)}`), which calls
`_canonical_league_id()` (`instruments_service/engine/orchestrator/sports.py:57-85`):

```python
def _canonical_league_id(lid_raw: object) -> str:
    s = str(lid_raw).strip()
    # Pass 1: numeric -> canonical via api_football id lookup
    if s and s.isdigit():
        league = _orch.get_league_by_api_football_id(int(s))
        s = league.league_id if league is not None else s   # <-- SILENT FALLBACK
    # Pass 2: strip provider-id suffix via UAC canonicalizer
    return _orch._uac_canonicalize_league_id(s)
```

When `get_league_by_api_football_id(int(s))` returns `None` (a lookup miss), `s` is left as the **raw numeric string**,
UNCHANGED — no exception, no log, no retry. Pass 2 (`_uac_canonicalize_league_id`) cannot rescue it either: a bare
numeric string has no provider-id suffix to strip, so it also passes through unchanged. The unresolved numeric string is
then used directly as the GCS partition's `league=` path segment — this is the exact mechanism that produces
`league=169` instead of `league=CHINA_SUPER_LEAGUE`.

`get_league_by_api_football_id()` (`unified_api_contracts/canonical/domain/sports/league_data.py:424-429`) is a **plain,
static, in-process dict lookup** (`_API_FOOTBALL_ID_TO_LEAGUE.get(api_football_id)` → `LEAGUE_REGISTRY.get(lid)`) built
once at import time from whatever UAC package version is installed in that process — there is no cache-warming delay, no
async race, nothing time-dependent about the lookup itself. The only way it returns `None` for an af_id that IS
registered **today** is if the WRITING PROCESS was running an **older UAC version whose registry did not yet contain
that league** at the moment of the write.

**This is exactly what happened, with a dated, git-verifiable proof**: `CHINA_SUPER_LEAGUE` (`api_football_id=169`) was
added to the UAC registry in `unified-api-contracts@beec78aa` ("feat(sports): add China Super League + Russia Premier
League to the canonical registry"), committed **2026-07-21**
(`unified_api_contracts/canonical/domain/sports/league_data_other.py:290-299`). The non-canonical `league=169` shards
this issue doc found are dated `day=2026-05-05` and `day=2026-05-06` — **nearly 2 months BEFORE the registry gained this
league**. At write time, `get_league_by_api_football_id(169)` legitimately returned `None` (169 was not yet in
`LEAGUE_REGISTRY`), so `_canonical_league_id` silently fell through to `"169"`, and the shard landed under the wrong
path. Writes for the SAME af_id AFTER 2026-07-21 correctly resolve to `league=CHINA_SUPER_LEAGUE` (consistent with the
doc's own finding that the canonical folder for this pair is "already fully populated"), which is why the corpus is
split between the two path shapes for the exact same league.

**Generalizes to every affected (league, season) pair, not just CHINA_SUPER_LEAGUE**: any af_league_id added to the UAC
registry AFTER fixtures_schedule writes had already occurred for that league will show this same split — a non-canonical
`league=<raw_id>` folder holding the pre-registration writes, and a canonical `league=<CANONICAL_ID>` folder holding
everything written after. The registry growing over time (new leagues added as coverage expands) is routine and
expected; the bug is that the writer has no mechanism to correct ALREADY-WRITTEN shards once a league joins the
registry, and no loud signal (log/metric/exception) fires at write time to surface that a lookup missed — so this class
of split silently recurs every time a new league is onboarded mid-corpus.

**Unblocks todo 3 (the fix)**: the writer's silent-fallback-to-raw-id branch needs to fail loud (or trigger a
documented, tested re-resolution/migration hook) instead of quietly writing under a divergent path — see the `[CODE] P1`
todo below.

## Recommended decision

1. Enumerate every non-canonical `league=<numeric>` / bare-day folder in the fixtures_schedule corpus (single walk, not
   per-pair) to size the full non-canonical population beyond the 10 pairs this task happened to sample.
2. Root-cause why the writer sometimes resolves to the raw af_id instead of the canonical league_id string — likely a
   registry lookup miss/fallback in the write path that silently uses the raw id rather than failing loud.
3. Fold the non-canonical shards into their canonical counterparts (merge by `af_fixture_id`, keep whichever content is
   more complete, same snapshot-then-merge pattern already used for the `dex_pools`/`lending_indices` DeFi fold), then
   delete the non-canonical originals — same class of migration as the DeFi canonical folds already completed.
4. Fix the writer so it never falls back to a raw-id folder again; add a regression test.

## Todos

- [x] ✅ [DIAG] P1. Root-cause why the sports fixtures_schedule writer sometimes resolves the canonical league_id lookup
      to the raw `af_league_id` instead of the registered string, and writes the shard under `league=<raw_id>` (repo:
      instruments-service). **Done when**: a written conclusion cites the specific writer code path and the
      lookup-miss/fallback condition that triggers it. — See "Root-cause conclusion (2026-07-24, slot 5)" above. Writer
      code path: `instruments_service/engine/orchestrator/sports.py:57-85`'s `_canonical_league_id()`, called from
      `sports_reference_fixtures.py:692`. Condition: a silent fallback in Pass 1 — when
      `get_league_by_api_football_id()` (a static UAC registry dict lookup) misses, the raw numeric af_league_id string
      is used unchanged as the `league=` path segment, no exception/log/retry. Root cause of the MISS: registry growth
      over time — dated proof via `unified-api-contracts@beec78aa` (2026-07-21, added `CHINA_SUPER_LEAGUE` af_id=169 to
      the registry) vs. the non-canonical `league=169` shards dated `day=2026-05-05`/`2026-05-06` (~2 months earlier,
      when 169 legitimately wasn't registered yet). Generalizes to every affected pair: any league added to the registry
      AFTER writes had already occurred for it produces this same split, with no mechanism to correct already-written
      shards and no loud signal when a lookup misses.
- [x] [DIAG] P2. ✅ Corpus-wide census done via a single MANIFEST read (not a raw GCS walk — cheaper and satisfies the
      single-walk requirement): downloaded `_index/availability_index.parquet` once
      (`instruments-store-sports-prd-central-element-323112`, 5,526,420 total rows), filtered to
      `data_type IN (FIXTURES, FIXTURES_SCHEDULE)` (394,922 rows), then filtered to rows whose `league_id` is a bare
      numeric string (the non-canonical marker, since the writer's silent fallback writes the raw `af_league_id` as the
      manifest `league_id` too, not just the GCS partition — same bug, same value, both surfaces). **Result: 6,678
      non-canonical rows across 485 distinct numeric league_ids** — far larger than the 86-row/10-pair sample this task
      happened to find; `capture_status` is 100% `captured` (no partial/failed non-canonical rows). Date range
      `2026-05-04` → `2026-07-06`; every affected row's calendar year is 2026 (the manifest schema has no dedicated
      `season` column — sports "season" is a domain concept derived elsewhere, not a manifest field, so this reports
      calendar-year-of-write, not the domain season label; flagging that distinction rather than conflating them). Full
      list of the 485 affected numeric league_ids is in this session's tool output, not reproduced inline here (too
      large for the line-cap budget) — re-derivable in ~10s via the exact census query above if todo 4 (the fold) needs
      the enumerated list again.

      **🔴 CORRECTS the prior "registry-growth timing lag" root cause — that mechanism accounts for <0.4% of this
                                                  population, not the bulk.** Cross-checked all 485 affected league_ids against
                                                  `get_league_by_api_football_id()` LIVE (the exact function the writer calls): only **2 of 485** ids
                                                  (25 of 6,678 rows) are NOW resolvable in the registry — consistent with the CHINA_SUPER_LEAGUE
                                                  timing-lag story (a league added to the registry after writes had already occurred, self-healing on the next
                                                  write). The other **483 league_ids (6,653 rows, 99.6%) are STILL unresolvable today** — these are not a
                                                  registry catching up, they are af_league_ids that were fetched and WRITTEN despite never being registered at
                                                  all. This means the writer (or something upstream of it) is fetching fixtures for leagues far outside the
                                                  ~100 PREDICTION-tier registry scope this workspace is supposed to track — a fetch-side scoping gap, not (only)
                                                  a write-side canonicalization timing bug. **This is a bigger, different, and more actionable finding than the
                                                  todo's own done-when asked for** — filed as a new follow-up todo below rather than silently folded into the
                                                  "fix the writer" todo, since the fix for THAT todo (fail loud on lookup-miss) would not address why these 483
                                                  leagues are being fetched in the first place.

- [x] ✅ [DIAG] P1. **NEW (2026-07-24, slot-6)** — investigate why fixtures_schedule fetches are happening for 483
      af_league_ids that are NOT in the UAC sports league registry at all (confirmed live via
      `get_league_by_api_football_id()` — 0 hits for any of them), accounting for 6,653 of the 6,678 non-canonical rows
      found by the census above. Candidates: (a) the fetch layer pulls a broader league set than the registry scopes
      (e.g. a bulk "all leagues in a country" call not filtered down to the PREDICTION tier before fetching), (b) these
      leagues were deliberately fetched for a reason not reflected in the current registry (a stale/removed scope), or
      (c) a genuine bug letting arbitrary af_league_ids through. **Done when**: a written conclusion identifies the
      actual fetch-scoping mechanism and states whether these 483 leagues should be (i) added to the registry (if
      genuinely in-scope), (ii) have their fetches stopped (if genuinely out-of-scope, wasting API quota), or (iii)
      something else — with the reasoning, not a guess. (repo: instruments-service)

      **Conclusion (2026-07-24, slot 5): answer is (iii) — a now-closed write-side leak, not a fetch-scoping problem
                              needing a change today. Candidate (a) confirmed as the mechanism, with a precise fix date.**

                              The FETCH itself is deliberately unscoped by design: the "ensure canonical fixtures" path
                              (`sports_reference_fixtures.py:160`, `await _adapter.get_fixtures_with_raw(date)`) calls the api_football
                              adapter with NO `league_ids` filter — it fetches every league the vendor API returns for that date. This is
                              intentional: this path builds the canonical `entity=fixtures/` SSOT that other entities (fixture_stats,
                              standings, etc.) derive their league mapping FROM, so it must see the full vendor universe, not just the
                              ~100-league PREDICTION-tier registry subset. This is candidate (a)'s "broader league set than the registry
                              scopes" — confirmed, and correct/by-design, not a bug.

                              The actual gap was on the WRITE side: `_write_fixtures_per_league()` (`sports_fixtures.py:354`), which splits
                              the broad fetch's rows into per-league partitions (including `entity=fixtures_schedule/league=<L>/`), has a
                              `_is_in_canonical_write_universe()` gate (line ~429) meant to drop any league outside the tracked registry
                              before writing — but **`git log -L` on that exact gate shows it was added in
                              `instruments-service@acfd5acf` ("fix(sports): add canonical write-universe gate to all per-league write paths
                              (G1)"), dated 2026-06-27.** Before that date, this write path had no such filter at all: every league the
                              broad fetch returned — registered or not — got a per-league partition written, which is exactly how 483
                              never-registered af_league_ids accumulated 6,653 rows.

                              **Live-verified the gate is effective TODAY** (not just trusting manifest metadata — the census's
                              `attempted_at` column turned out to be unusable for pre/post-gate dating: all 6,678 affected rows show
                              `attempted_at` clustered around 2026-07-22, which is a later bulk manifest re-consolidation touch, not the
                              original write time, so it can't date-order these writes against the 2026-06-27 gate commit). Direct test
                              instead: called the real `_write_fixtures_per_league()` with a 2-row DataFrame — one row `af_league_id=999999`
                              (deliberately unregistered) and one `af_league_id=39` (EPL, registered) — and confirmed exactly ONE write
                              occurred, for `league=EPL`; nothing was written for the bogus id. The gate correctly filters unregistered
                              leagues today.

                              **Disposition**: (i) NOT added to the registry — nothing suggests these 483 leagues are genuinely in scope,
                              they were never deliberately curated; (ii) fetches are NOT stopped — the broad fetch is correct/necessary for
                              the canonical fixtures SSOT and is unrelated to the leak; (iii) **the fix already shipped** (the 2026-06-27
                              write-universe gate) — the only remaining work is DATA cleanup of the pre-gate historical residue, already
                              tracked as the `[DATA] P2` fold/purge todo below. No new CODE todo needed here. **Unblocks the `[DATA] P2` todo's
                              own gating question below**: the 483 leagues are confirmed out-of-scope, so their shards should be (ii)
                              confirmed-out-of-scope-and-deleted, NOT folded (there is no canonical folder for them and none should be
                              created) — only the 2 registry-growth-timing-lag leagues (`CHINA_SUPER_LEAGUE`, `RUSSIA_PREMIER_LEAGUE`) have a
                              real canonical fold target.

- [x] ✅ [CODE] P1. Fix the writer so it never falls back to writing under a raw-id folder — fail loud (or resolve via a
      documented, tested fallback) instead (repo: instruments-service). **Done when**: a regression test reproduces the
      old lookup-miss condition and asserts the fix. — instruments-service@48e12eb9. `_canonical_league_id()`
      (`sports.py`) now logs a `CANONICAL_LEAGUE_ID_LOOKUP_MISS` WARNING (citing the raw af_league_id) on every Pass-1
      registry-lookup miss, instead of silently passing the numeric id through with no trace. The non-lossy passthrough
      RETURN VALUE is unchanged (CF-7 design invariant, still asserted by the existing
      `test_unknown_numeric_passthrough`) — only the silence is fixed. Two new regression tests in
      `test_orchestrator_sports_pipeline.py::TestCanonicalLeagueIdCF7`: `test_numeric_lookup_miss_logs_warning`
      (reproduces the miss via `caplog`, asserts the warning fires and cites the raw id) and
      `test_resolved_numeric_does_not_log_warning` (a successful lookup does NOT log, so the signal stays
      rare/actionable rather than noise). **Scope note (per slot 6's corpus-wide census above)**: this closes the
      "registry growth timing lag" mechanism this todo was scoped against (the ~2-of-485/<0.4% case, e.g.
      CHINA_SUPER_LEAGUE) — it does NOT address the separate, much larger 483-league/6,653-row "fetched but never
      registered" finding, which is correctly tracked as its own gated `[DIAG] P1` todo above (different root cause,
      different fix). This todo's own done-when (a regression test reproducing the lookup-miss + asserting the fix) is
      fully met regardless of that broader scope question.

- [x] [DATA] P2. ✅ **Narrow scope EXECUTED 2026-07-24 (slot 9) — instruments-service@4412e576.** The 483-league portion
      remains correctly NOT executable (unchanged — see below); the narrow, verified-safe 12-shard portion is done.

      **Correction to this todo's own prior count**: re-verified live before executing — the FIXTURES_SCHEDULE-specific
                      GCS objects (this todo's actual scope; `entity=fixtures_schedule` only, not the sibling `entity=fixtures`/
                      `entity=fixtures_outcomes`) number **12** (date, league) pairs, not 13: `af_id=169` → `CHINA_SUPER_LEAGUE` across
                      11 dates (`2026-05-05, 05-06, 05-19, 05-20, 05-29, 05-30, 06-26, 06-27, 06-28, 07-03, 07-04`) + `af_id=235` →
                      `RUSSIA_PREMIER_LEAGUE` on 1 date (`2026-05-20`). The manifest carries a `FIXTURES` (not `FIXTURES_SCHEDULE`) row
                      for `day=2026-07-05`/`league_id=169` with no matching GCS object under `entity=fixtures_schedule/league=169/` for
                      that date — the prior "23 rows"/"13 pairs" count evidently summed across the FIXTURES-family data_types
                      (FIXTURES + FIXTURES_OUTCOMES + FIXTURES_SCHEDULE share the same league resolution bug and likely have their own
                      analogous non-canonical shards — NOT folded here, out of this todo's stated `entity=fixtures_schedule` scope;
                      flagging as a new adjacent-scope todo below rather than silently expanding this one's blast radius).

                      **Executed via** `instruments-service/scripts/fold_china_russia_league_raw_id_folders_2026_07_24.py` (dry-run
                      validated against live GCS first — confirmed 0 aborts, no canonical sibling existed for any of the 12 pairs —
                      then `--apply`d). Recipe per shard (this bucket has **NO soft-delete**,
                      `retentionDurationSeconds=0` confirmed live via `bucket.soft_delete_policy` — unlike the market-data-tick bucket
                      precedent this todo cited, so an explicit backup copy is the real safety net, not soft-delete): describe source →
                      describe canonical target (absent, confirmed) → `gcs_copy_object` to canonical path → verify size+crc32c parity →
                      download+parse canonical object (non-empty, confirmed) → `ManifestWriter.record_captured()` per canonical
                      `(date, FIXTURES_SCHEDULE, league_id=<CANONICAL_ID>)` row_key via a single shared per-VM-shard writer → backup-copy
                      the raw-id original to `sports_reference/_purge_backups/2026_07_24_league_fold/` → verify backup parity →
                      `gcs_delete_object` the raw-id original → verify it's gone.

                      **Independently verified post-run** (separate ad-hoc GCS listing, not just the script's own internal checks): all
                      12 canonical objects present (`league=CHINA_SUPER_LEAGUE`/`league=RUSSIA_PREMIER_LEAGUE`), all 12 raw-id objects
                      (`league=169`/`league=235`) gone across every affected date, 12 backup snapshots present under
                      `_purge_backups/2026_07_24_league_fold/`. The per-VM manifest shard (`_index/per_vm/league-fold-20260724.parquet`)
                      carries all 12 `captured` rows.

                      **The 483-league portion remains correctly NOT executed** — the P1 DIAG above already concluded (2026-07-24,
                      slot 5/6) that those leagues are out-of-scope residue from a write-side leak closed by the 2026-06-27
                      `_is_in_canonical_write_universe()` gate, with NO canonical fold target to create; this todo's done-when for that
                      portion is `(ii) confirmed-out-of-scope`, tracked as its own disposition in that DIAG conclusion — not re-opened
                      or re-litigated here.

- [ ] [DATA] P2. BLOCKED-OPERATOR-DECISION — the sibling `entity=fixtures` and `entity=fixtures_outcomes` GCS objects
      for the SAME 2 leagues (af_id=169/235) also sit under non-canonical `league=169`/`league=235` folders for at least
      `day=2026-05-05` (confirmed live: `entity=fixtures/league=169/fixtures.parquet` size=34593,
      `entity=fixtures_outcomes/league=169/fixtures_outcomes.parquet` size=10000, both exist) — same root-cause writer
      bug (`_canonical_league_id()`'s registry-lookup-miss fallback), different entity, not touched by the
      `entity=fixtures_schedule`-scoped fold above. Deliberately NOT expanded into that todo's scope (it was already
      reviewed/verified narrowly for `fixtures_schedule` only) — tracked here instead. **Done when**: the full (date,
      entity, league) population for `entity IN (fixtures, fixtures_outcomes)` × `league IN (169, 235)` is enumerated
      (single manifest read, not a fresh GCS walk — `data_type IN (FIXTURES, FIXTURES_OUTCOMES)` filtered to
      `league_id IN (169, 235)` against the same `_index/availability_index.parquet`), then folded via the identical
      backup-copy-record_captured-delete recipe as the `fixtures_schedule` fold above (repo: instruments-service).
      **STATUS 2026-07-24 (worker)**: census done (21 rows: 12 `FIXTURES` + 9 `FIXTURES_OUTCOMES`, matches the same
      12-date/2-league cohort as the already-folded `fixtures_schedule` sibling). Fold script written + dry-run verified
      against real prod GCS (21/21 sources found, 21/21 canonical targets absent — pure move, zero overwrite risk) and
      shipped as code: `instruments-service@1511b672`
      (`scripts/fold_china_russia_league_raw_id_folders_fixtures_siblings_2026_07_24.py`). **Blocked on `--apply`**:
      posted `/blocked` (`BLK-4c0c944b`) asking whether a consolidator cron pause is needed first — main's initial
      guidance was to hold pending operator input. Follow-up research (this session) found the actual sibling precedent
      (`instruments-service@4412e576`, `entity=fixtures_schedule`) used the per-VM-shard writer with NO cron pause at
      all (I had wrongly conflated it with a _different_ todo — the FIXTURES-legacy restamp, `e92efc78` — which DID need
      a pause because it wrote directly to the canonical index); this fold's per-VM-shard write pattern is structurally
      disjoint from the canonical index and cannot race the consolidator, and the general TOCTOU race class is
      separately fixed fleet-wide (`unified-trading-library@14301571`). Reported this back via progress update,
      requesting go-ahead to `--apply` without a pause — no response received after an extended wait (other slots
      actively draining the backlog in parallel, so the system itself is healthy; this one question is simply
      unanswered). Marking BLOCKED-OPERATOR-DECISION and releasing the slot rather than continuing to hold; the very
      next step (once answered) is a single `--apply` run + verification, no further design work needed. See
      `BLK-4c0c944b` in the dashboard for the full exchange.
