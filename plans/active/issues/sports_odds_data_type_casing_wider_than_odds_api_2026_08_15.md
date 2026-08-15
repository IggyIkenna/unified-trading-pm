---
doc_type: issue
title: "The uppercase/lowercase 'ODDS'/'odds' data_type split is wider than just odds_api"
status: open
priority: P2
assigned_vm: NA
execution_scope: local-only
tags: [sports, data-correctness, casing, scope-finding]
supersedes: NA
resolved_by:
summary:
  "While executing sports_odds_api_data_type_casing_standardization_2026_08_15.md's Phase 0 (fix ONE adapter's casing),
  found the same uppercase 'ODDS' pattern live in betfair_adapter.py and extensively in instruments-service's
  footystats.py, plus MDPS adapters that already explicitly declare BOTH casings as accepted-equivalent. Explicitly NOT
  touched by that plan — it's scoped to odds_api only. This doc tracks the wider finding for a future decision."
nature: process
asset_group: sports
stage: [data]
repos: [market-tick-data-service, instruments-service, market-data-processing-service]
scope: [engineer, admin]
related: [sports_odds_api_data_type_casing_standardization_2026_08_15]
parent_epic: sports_master
source: interactive-session
created: 2026-08-15
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

# The uppercase/lowercase "ODDS"/"odds" data_type split is wider than just odds_api

## What happened

While implementing Phase 0 of `sports_odds_api_data_type_casing_standardization_2026_08_15.md` (fix the odds_api
adapter's `data_type` casing from uppercase `"ODDS"` to lowercase `"odds"`, matching the canonical
`DATA_TYPES_BY_ASSET_GROUP["sports"]` convention), a grep for other exact-match `"ODDS"` consumers across the workspace
(beyond the two already known and handled — `data_type_capability.py`, `generate_instrument_catalogue.py`) turned up a
much wider pattern than the plan scoped:

- **`market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/betfair_adapter.py:373`** — a
  COMPLETELY DIFFERENT venue also writes `"data_type": "ODDS"` uppercase. Not touched — not in scope for the
  odds_api-specific plan.
- **`instruments-service/instruments_service/engine/orchestrator/footystats.py`** (many lines, e.g. 953, 1096, 1102,
  1132, 1158, 1162, 1185, 1190, 1207, 1211, 1229, 1234, 1263, 1268) — footystats's own odds-entity capture path
  extensively uses `canonical_sports_is_data_type("ODDS") or "ODDS"` as its live data_type, i.e. it ALREADY routes
  through a canonicalization function with an uppercase literal fallback. This is a THIRD, independent source of
  uppercase "ODDS" rows, in a different service (instruments-service, not market-tick-data-service).
- **`unified-api-contracts/unified_api_contracts/registry/schema_spec.py:434`** — another registry (distinct from
  `data_type_capability.py`) also declares `data_type="ODDS"`.
- **`market-data-processing-service`'s sports adapters** (`odds_movement_adapter.py:36`,
  `bucket_assignment_adapter.py:705`, `odds_snapshot_adapter.py:36`) — ALL THREE independently declare
  `related_data_types: list[str] = ["odds", "trades", "ODDS", "TRADES"]`. This is significant: MDPS has ALREADY had to
  accept both casings as legitimate/equivalent inputs, suggesting the mixed-casing reality is not purely an
  odds_api-specific bug but a known, already-worked-around ecosystem-wide condition.
- **A distinct, separate axis found in the same grep, do NOT conflate**: several one-off scripts
  (`census_venue_restamp_scope_2026_07_27.py`, `manifest_swap_bookmaker_venue_restamp_2026_07_27.py`, the K1/K2
  casing-revert scripts) reference `instrument_type == "ODDS"` combined with `data_type == "TRADES"` — this is a
  DIFFERENT field (`instrument_type`, not `data_type`) and a DIFFERENT value pairing entirely, tied to the documented
  K1/K2 casing-revert incident (`sports_satellite_batch2_casing_direction_contradicts_k1k2_revert_2026_07_25.md`). Do
  not assume this is the same bug/fix as the `data_type` casing question — it isn't, even though both involve the
  substring "ODDS".

## Why this is a separate doc, not folded into the odds_api plan

The `sports_odds_api_data_type_casing_standardization_2026_08_15.md` plan was explicitly scoped (title, summary, and
every phase) to **odds_api's** adapter and its ~17K historical rows. Silently expanding that plan's execution to also
rewrite `betfair_adapter.py` and `footystats.py` — different venues, one in a different SERVICE entirely — would be a
real, unreviewed scope expansion, not "finishing the same task." Per this workspace's scope-change discipline, a genuine
scope change that goes beyond the documented plan gets logged and left for a real decision, not silently absorbed into
an in-flight dispatch.

## Open questions for whoever picks this up

1. Is `footystats.py`'s `canonical_sports_is_data_type("ODDS") or "ODDS"` pattern already normalizing correctly in most
   cases (the function call succeeding), with the uppercase literal only a fallback for something that should never
   happen in practice? Or is the fallback actually hit often, meaning footystats has its OWN uppercase-row population as
   real as odds_api's? **Not measured — this doc is a scoping flag, not an audit.**
2. Does `betfair_adapter.py`'s uppercase write represent a real, currently-accruing population, or could it be phantom
   (same class of finding as the two already-resolved phantom-uppercase populations found 2026-07-26 and 2026-08-14)?
3. Given MDPS already treats `["odds","trades","ODDS","TRADES"]` as accepted-equivalent — is a full casing unification
   actually the right end-state, or does the ecosystem already have a working case-insensitive normalization layer that
   makes "there are two casings" a non-problem in practice, and the real fix is just making the FEW remaining
   exact-match consumers (like the odds_api-specific ones already fixed) case-tolerant, rather than rewriting every
   writer?
4. `unified_api_contracts/registry/schema_spec.py:434`'s separate `data_type="ODDS"` entry — same question as the
   `data_type_capability.py` one already resolved for odds_api: is this entry a real, used, exact-match consumer, and
   does it need the same live-check treatment before any casing decision is made for it?

## What NOT to assume

- Do not assume this is "the same fix, just more files" — footystats.py is a different SERVICE (instruments-service)
  with its own capture pipeline, and betfair_adapter.py is a different VENUE with potentially different downstream
  consumers. Each needs its own scoping pass, not a blind extension of the odds_api plan's phases.
- Do not conflate this with the `instrument_type=="ODDS"`/`data_type=="TRADES"` axis from the K1/K2 incident — different
  fields, different meaning, already has its own (troubled) history.
