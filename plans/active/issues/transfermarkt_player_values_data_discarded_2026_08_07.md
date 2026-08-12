---
doc_type: issue
title:
  Transfermarkt PLAYER_VALUES entity never persists any value data — the adapter parses market_value_eur per player, the
  orchestrator drops it before writing
summary: >
  Investigating the operator's question "does PLAYER_VALUES actually change outside transfer windows" (the real test of
  whether the current skip-logic is safe) surfaced a bigger problem: the answer can't be checked from stored data,
  because no value data is stored. `transfermarkt.py` (adapter,
  instruments_service/reference_data/adapters/sports/adapters/transfermarkt.py:407) parses
  `market_value_eur`/`total_market_value_eur` per player and per team from the Transfermarkt API response. But the
  orchestrator's write path (instruments_service/engine/orchestrator/transfermarkt.py:536-541) explicitly discards the
  nested `players` list before writing ("Drop nested players list (serializes as unhelpful string)") and replaces it
  with only a `player_count`. Verified live against the most recent captured snapshot
  (gs://instruments-store-sports-prd-central-element-323112/sports_reference/snapshots/entity=player_values/season=2026/trigger=2026-08-04/player_values.parquet,
  438 rows): every value-bearing column is 100% null — `player_count` is 0/438 non-null, and there is no
  `market_value_eur` / `total_market_value_eur` column at all. The only populated columns are `team_id`, `name`,
  `league_id`, `canonical_league`, `season`, and snapshot metadata — team/league scaffolding, not player values. Despite
  this, the manifest legitimately records these rows as `captured` (this is not the honest-absence /
  EXPECTED_NO_PROVIDER_COVERAGE gap investigated the same day in
  plans/active/issues/sports_af_full_entity_completion_2026_08_03.md — that's a separate, correctly-behaving denominator
  issue; this is captured rows containing no signal). The `total_market_value_eur` team aggregate isn't persisted
  either, so even a coarse per-team value proxy is unavailable.
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [data-correctness, transfermarkt, player-values, silent-data-loss, honest-coverage]
related:
  [
    plans/active/issues/sports_af_full_entity_completion_2026_08_03.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-08-07
author: claude-agent
parent_epic: sports_master
priority: P1
source:
  sports_af_full_entity_completion_2026_08_03 dispatch, operator follow-up on PLAYER_VALUES transfer-window
  investigation
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-12
locked_by:
context_scope:
  [
    instruments-service/instruments_service/engine/orchestrator/transfermarkt.py,
    instruments-service/instruments_service/reference_data/adapters/sports/adapters/transfermarkt.py,
    plans/active/issues/sports_af_full_entity_completion_2026_08_03.md,
  ]
resolved_by:
---

## Finding

`_fetch_transfermarkt_data()` calls `adapter.get_teams(tm_code, season=season)`, which returns each team's roster
including, per player, `market_value_eur` (adapter line 407) and a team-level `total_market_value_eur` (adapter
line 428) — both parsed from Transfermarkt's `marketValue`/`totalMarketValue` fields via `_parse_market_value()`.

The orchestrator then does, per team (`transfermarkt.py:530-541`):

```python
for t in teams:
    row = _orch._coerce_adapter_output(t)
    flat: dict[str, str | None] = {k: str(v) if v is not None else None for k, v in row.items()}
    flat["league_id"] = str(tm_code)
    flat["canonical_league"] = league_def.league_id
    players = row.get("players")
    flat["player_count"] = str(len(players)) if isinstance(players, list) else flat.get("squad_size")
    flat.pop("players", None)  # <-- the per-player market_value_eur list is dropped here
    all_teams.append(flat)
```

`total_market_value_eur` isn't referenced anywhere in the orchestrator write path, so it never survives into `flat`
either (or it's silently absent from `_coerce_adapter_output`'s output — not traced further, since the per-player drop
alone is sufficient to explain the finding).

Live verification (2026-08-07, most recent real snapshot, 438 rows, all captured teams):

| column                                                       | non-null |
| ------------------------------------------------------------ | -------- |
| team_id, name, league_id, canonical_league, season           | 438/438  |
| player_count                                                 | 0/438    |
| short_name, country, founded, logo_url, venue                | 0/438    |
| (no market_value_eur / total_market_value_eur column exists) | —        |

So today's "PLAYER_VALUES" data in GCS is, in practice, a team-id ↔ league-id roster index with zero value signal — and
even the non-value team metadata (country, founded, venue, player_count) is unpopulated, suggesting
`_coerce_adapter_output` / the Apify-backed adapter response itself may be returning partial data separately from the
players-list drop (not investigated here — worth checking if this doc gets picked up).

## Why this matters

This directly undercuts the operator's actual question ("does the value change outside transfer windows, to check
whether skipping fetches outside the window is safe") — there's no historical value series to check it against. It also
means every downstream consumer of `entity=player_values` (features layer, any strategy signal keyed on squad value) has
been getting team/league identifiers with no value payload, silently, since whenever this write path was introduced
(`ITEM 6a`/`6b` per the code's own inline comments — no date given in-repo, not chased further).

This is NOT the same bug as the EXPECTED_NO_PROVIDER_COVERAGE honest-absence gap found the same day in
`sports_af_full_entity_completion_2026_08_03.md` — that one is about _how many rows are captured at all_ (correctly low,
for non-Prediction-tier leagues). This one is about what's _inside_ the rows that genuinely are captured.

## Options (operator decision needed — this is a schema/scope call, not a mechanical fix)

1. **Persist the per-player list.** Keep `market_value_eur` per player (drop only the truly unhelpful nested fields,
   e.g. bio text) — restores the original intent of "PLAYER_VALUES" and enables the transfer-window skip-logic safety
   check the operator asked for. Largest schema change; largest storage growth (roster-sized, not team-sized).
2. **Persist just `total_market_value_eur` per team.** Cheap, small schema addition, answers a coarser version of the
   same question (does aggregate squad value move outside windows) without the per-player storage cost.
3. **Rename the entity to reflect what it actually is** (team/league roster index) and treat "real player values" as a
   separate, not-yet-built entity — if squad value was never actually needed by any current consumer, this may be the
   honest fix rather than backfilling data nobody reads.
4. **Do nothing now, park it** — if this doesn't block anything live today, decide later.

No fix applied. Flagging per this workspace's big-finding triage rule (data-correctness, contradicts the entity's own
name/manifest data_type) rather than picking an option unilaterally, since 1 vs 2 vs 3 changes storage cost, schema, and
possibly a rename that ripples into UAC/manifest data_type naming.

## Todos

- [x] ✅ [CODE] P1. **RULED 2026-08-09 (operator): Option 1 — persist the full per-player `market_value_eur` list**, not
      just the team-level aggregate. Was `[OPERATOR]` P1 pick-a-disposition. Implementation: in
      `instruments_service/engine/orchestrator/transfermarkt.py:530-541`, stop dropping the `players` list — persist
      each player's `market_value_eur` (drop only genuinely unhelpful nested bio-text fields, per option 1's original
      scoping). **Also persist `total_market_value_eur` per team while touching this code** — it's already parsed by the
      adapter (`transfermarkt.py` adapter, line 428) and currently silently lost the same way; keeping it is near-zero
      incremental cost once the per-player schema change lands, and gives a fast team-level aggregate without re-summing
      player rows every read. **Done when**: both fields land in the written schema, a fresh snapshot shows non-null
      `market_value_eur` per player and non-null `total_market_value_eur` per team, and a regression test locks in that
      neither is dropped in future refactors of this write path. — CODE + regression test shipped:
      instruments-service@3e87e99f + a47f4880 (2026-08-09, slot 32). See Progress Log for the root-cause correction +
      implementation detail. Live-snapshot half of done-when tracked separately below (not yet exercised against a real
      fetch).
- [x] ✅ [DATA] P3. **VERIFIED 2026-08-12 — PARTIAL PASS, one half genuinely works, one half doesn't.** A real trigger
      fired 2026-08-11 (K_LEAGUE_1, 12 teams) and confirms: `total_market_value_eur` IS now genuinely populated (12/12
      non-null in the fresh snapshot). `players` (the per-player list) is NOT — 0/12 non-null, despite
      `get_team_squads()`/`_flatten_transfermarkt_squad` being correctly wired and exercised. Confirmed this isn't a
      flatten-logic bug: `player_count` exactly equals `squad_size` for all 12 rows (30=30, 50=50, 33=33, …), which only
      happens via the `else: flat["players"] = None` fallback branch in `_flatten_transfermarkt_squad` — i.e.
      `item.get("players") or item.get("squad")` was not a list at all in the raw parsed response for these teams.
      Traced upstream: `_group_apify_players_into_clubs` (the Apify path) always initializes `players: []` per club, so
      an empty players list from THAT path would show as `"[]"` (non-null), not true null — the true-null result
      observed is only consistent with the RapidAPI backend (`_fetch_clubs_via_rapidapi`) returning club objects with no
      `players`/`squad` key at all for this competition tier. Not confirmed via live request tracing (would need to
      intercept the actual RapidAPI response) — flagged as a genuine, still-open gap, most likely an upstream
      data-coverage limitation (smaller/lower-tier leagues may not carry full squad rosters from this source) rather
      than a bug in this fix's own logic. See new todos below for the fix path.
- [x] ✅ [DATA] P1. **Backfill/coverage-scope finding (2026-08-12)**: the accumulating master table
      (`gs://instruments-store-sports-prd-central-element-323112/sports_reference/master/entity=player_values/master.parquet`,
      5,784 rows across 32 leagues, seasons 2014 + 2018-2026) has only **12/5,784 (0.2%) rows with real
      `total_market_value_eur`** and **0/5,784 (0%) with real `players`** — every row except yesterday's single
      K_LEAGUE_1 trigger is exactly as broken as before the fix, and there is NO backfill mechanism: PLAYER_VALUES only
      refetches a league on its own transfer-window trigger date (`get_leagues_needing_refresh`), so a row captured
      under the OLD (value-discarding) code will not naturally get a corrected re-fetch until that same league's NEXT
      trigger date — up to ~1 season-cycle away, not days. **Operator correction accepted (2026-08-12)**: the raw
      0.2%-of-all-rows framing overstates the gap on its own — player values genuinely don't change outside a real
      transfer window, so most of the 5,772 "stale" rows were never supposed to be re-checked daily in the first place.
      The real, narrower question is: of the (league, trigger-date) observations that WERE captured during an actual
      past transfer window (i.e., a legitimate capture moment, just running the old broken code), how many are now
      missing value data that a corrected re-fetch of THAT SAME historical window would restore? That number is bounded
      by the count of real historical (league, trigger-date) events across ~32 leagues × up to ~9 covered seasons (2014,
      2018-2026) × each country's 1-2 windows/year — materially smaller than "5,772 broken rows", but still 100% of it
      is currently unrecovered without an explicit backfill decision (see new todo below).
- [x] ✅ [DATA] P1. **New finding (2026-08-12): CONFIRMED bug — the orchestrator wrongly applies `transfer_records`'
      window-gating to PLAYER_VALUES, contradicting BOTH SSOTs it should follow, not an ambiguous judgment call.**
      `unified_api_contracts.canonical.domain.sports.transfer_windows.is_transfer_data_expected()`'s own docstring:
      "Whether **transfer_records** data is expected... Player values (squad data) are expected year-round regardless."
      Codex `honest-absence-downstream-handling.md` (lines 616, 1003) independently agrees:
      `EXPECTED_OUTSIDE_TRANSFER_WINDOW` is documented as scoped to `data_type=transfer_records` specifically. But the
      orchestrator (`instruments_service/engine/orchestrator/transfermarkt.py:463-475`) never calls
      `is_transfer_data_expected()` — it reimplements its own gate
      (`is_transfer_window_open(...) or     get_leagues_needing_refresh(...)`) that skips PLAYER_VALUES entirely outside
      windows/trigger dates, incorrectly stamping the `transfer_records`-scoped `EXPECTED_OUTSIDE_TRANSFER_WINDOW`
      reason onto PLAYER_VALUES rows. This is exactly why the 5,772 historical rows above never got the value fix's
      benefit — the gate that should only apply to raw transfer transactions is silently starving squad/value refreshes
      too. This code region already has one documented prior bug of this exact shape (the 2026-05-05 MATCHES
      18%-coverage bundle-vs-per-league skip mismatch, per the inline comment at transfermarkt.py:442-447) — this is a
      second instance of the same class.

- [ ] [CODE] P1. **Fix the window-gating bug**: PLAYER_VALUES must not be skipped outside transfer windows — remove or
      bypass the `_tm_window_open`/`_tm_needs_refresh` skip block (transfermarkt.py:463-475) for PLAYER_VALUES
      specifically (call `is_transfer_data_expected()` properly if `transfer_records` in the same fetch path still needs
      its own gate, or split the two data_types' skip logic apart). Repo: instruments-service. Done when: a forced
      non-window-date PLAYER_VALUES fetch for a league genuinely attempts the API call (no
      `EXPECTED_OUTSIDE_TRANSFER_WINDOW` empty-confirmed) + a regression test locks the two data_types' gating apart so
      this can't silently re-merge.
- [ ] [CODE] P2. **Root-cause the empty `players` per-player list.** Confirm (via live request tracing — is this adapter
      instance on Apify or RapidAPI for `K_LEAGUE_1`?) why `item.get("players") or item.get("squad")` is not a list for
      these teams; if it's a genuine upstream limitation (RapidAPI plan/tier doesn't return full squads for this
      competition), document it as an honest per-source coverage gap rather than leave it silently null; if it's fixable
      (e.g. a second endpoint call needed), fix it. Repo: instruments-service.
- [ ] [OPERATOR] P2. **Backfill decision**, once the window-gating bug above is fixed: force-refetch the historical
      (league, trigger-date) pairs that were captured under the old value-discarding code (recovers real value data for
      real past transfer windows — bounded, not the full 5,772-row count, per the finding above), vs. accept gradual
      natural convergence as each league's future trigger dates land, vs. some hybrid (e.g. only the most recent N
      seasons). Needs a rough cost estimate (API quota / row count) before picking — not scoped here.

## Progress Log

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — genuine operator-gated schema/scope decision, no bounded
  worker-determinable outcome. Added the `[OPERATOR] P1` todo above so the pending decision is tracked, not just prose.
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
- **2026-08-09 (slot 32, data_engineering): implemented Option 1 — real root cause was one layer deeper than this doc's
  original finding, correcting the implementation plan before shipping.** The doc's finding read the drop as happening
  in the orchestrator's flatten step (`transfermarkt.py:530-541`'s `flat.pop("players", None)`), but that pop was
  already a no-op: `adapter.get_teams()` returns `list[CanonicalTeam]` — a frozen cross-source schema
  (`team_id, name, short_name, country, founded, logo_url, venue`) with NO `players`/`squad_size`/
  `total_market_value_eur` fields at all — so `row.get("players")` was always `None` upstream of the pop, which is why
  `short_name`/`country`/`founded`/`venue` were ALSO 0/438 non-null (the doc's own "worth checking" note at the end of
  `## Finding`). The actual normalization drop happens in `normalize_transfermarkt_team_from_squad()`
  (`unified-api-contracts`), which discards everything except `team_id`/`name`. Found UAC already ships a fully-tested,
  unused-in-production companion — `normalize_player_values(squad, league_id) -> list[PlayerValue]`
  (`external/transfermarkt/normalize.py`) — built for exactly this per-player-value extraction but never wired up;
  reusing its sibling data model (`TransfermarktTeamSquad`) rather than reinventing persistence. **Fix**: added
  `TransfermarktAdapter.get_team_squads()` (raw `TransfermarktTeamSquad`, market values intact — `get_teams()` kept
  unchanged/still used, both now share a `_fetch_squads()` core) and `_flatten_transfermarkt_squad()` in the
  orchestrator, which JSON-encodes the per-player list (drops only `player_image_url`, the genuinely-bio-text field) and
  persists `total_market_value_eur` as a scalar column — the same JSON-nested-column convention `process_write.py`
  already uses for `InstrumentRecord.legs` (parquet-safe, avoids nested list<struct> schema risk). Verified via a direct
  interpreter smoke-test (non-null `market_value_eur` per player + `total_market_value_eur` survive the flatten,
  `player_image_url` dropped) and a new regression test file
  (`tests/unit/test_transfermarkt_player_values_persisted.py`, 8 cases) plus fixed 3 pre-existing tests in
  `test_orchestrator_data_fetchers.py` whose mocks stubbed the now-unused `get_teams()` call site (full
  `quality-gates.sh` caught this — the shard-level try/except was silently swallowing the resulting
  `TypeError: object MagicMock can't be used in 'await' expression` as an ordinary per-league failure, so a narrower
  test run missed it). Did NOT live-verify against a real fetch (Transfermarkt only re-fetches on transfer-window
  trigger dates; a forced live fetch would spend real API quota purely for verification) — the "fresh snapshot" half of
  Done-when is confirmed by the next live/triggered fetch, not this session. instruments-service@3e87e99f (fix) +
  a47f4880 (test-fixture fix). QG: `.qg_last_passed_sha=a47f4880`.
- **2026-08-12 (interactive session)**: live-verified the P3 todo against a real trigger (K_LEAGUE_1, 2026-08-11) and
  found the fix only half-works -- total_market_value_eur genuinely persists now, players doesn't (traced to a likely
  upstream RapidAPI squad-data gap, not a flatten-logic bug; see the new P2 code todo). Checked the accumulating master
  table directly (not just the newest snapshot): 5,784 total rows, 12 with real value data -- but per the operator's
  correction mid-session, that raw ratio overstates the gap, since player values genuinely don't change outside real
  transfer windows and most of those rows were never supposed to refresh daily. Re-scoped the finding to the real
  question (historical trigger-date captures under the old broken code, not all rows) and, prompted by the operator
  asking whether codex/UAC already cover this, found the actual root cause: codex
  (honest-absence-downstream-handling.md:616,1003) and UAC's own is_transfer_data_expected() docstring BOTH explicitly
  scope EXPECTED_OUTSIDE_TRANSFER_WINDOW/window-gating to transfer_records only and say PLAYER_VALUES is expected
  year-round -- the orchestrator's skip logic contradicts both SSOTs it should be following, not an ambiguous judgment
  call. This is why the historical backlog never converges naturally. Added 3 new open todos (window-gating fix,
  per-player-list root-cause, backfill decision) -- no code shipped this pass, doc-only per the operator's explicit ask
  to write this up first.
