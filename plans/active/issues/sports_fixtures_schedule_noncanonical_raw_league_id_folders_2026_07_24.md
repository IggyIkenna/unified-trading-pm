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

- [ ] [DIAG] P1. **NEW (2026-07-24, slot-6)** — investigate why fixtures_schedule fetches are happening for 483
      af_league_ids that are NOT in the UAC sports league registry at all (confirmed live via
      `get_league_by_api_football_id()` — 0 hits for any of them), accounting for 6,653 of the 6,678 non-canonical rows
      found by the census above. Candidates: (a) the fetch layer pulls a broader league set than the registry scopes
      (e.g. a bulk "all leagues in a country" call not filtered down to the PREDICTION tier before fetching), (b) these
      leagues were deliberately fetched for a reason not reflected in the current registry (a stale/removed scope), or
      (c) a genuine bug letting arbitrary af_league_ids through. **Done when**: a written conclusion identifies the
      actual fetch-scoping mechanism and states whether these 483 leagues should be (i) added to the registry (if
      genuinely in-scope), (ii) have their fetches stopped (if genuinely out-of-scope, wasting API quota), or (iii)
      something else — with the reasoning, not a guess. (repo: instruments-service)
- [ ] [CODE] P1. Fix the writer so it never falls back to writing under a raw-id folder — fail loud (or resolve via a
      documented, tested fallback) instead (repo: instruments-service). **Done when**: a regression test reproduces the
      old lookup-miss condition and asserts the fix.
- [ ] [DATA] P2. Fold every non-canonical shard's rows into its canonical counterpart (merge by `af_fixture_id`,
      snapshot first, delete the non-canonical original after verification), same pattern as the DeFi
      `dex_pools`/`lending_indices` fold (repo: instruments-service). **Done when**: a post-fold corpus census shows
      zero non-canonical `league=<numeric>`/bare fixtures_schedule shards remain, and every previously non-canonical row
      is present (verified by `af_fixture_id`) in its canonical folder.
