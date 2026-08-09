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
assigned_vm: NA
execution_scope: local-only
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-07
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

- [ ] [OPERATOR] P1. **Pick a disposition for the PLAYER_VALUES silent-data-loss finding above** — persist per-player
      values (option 1), persist team-level aggregate only (option 2), rename the entity to reflect what it actually is
      today (option 3), or park with no change (option 4). Gates any code fix; this doc had no tracked todo for the
      decision itself before this pass.

## Progress Log

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — genuine operator-gated schema/scope decision, no bounded
  worker-determinable outcome. Added the `[OPERATOR] P1` todo above so the pending decision is tracked, not just prose.
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
