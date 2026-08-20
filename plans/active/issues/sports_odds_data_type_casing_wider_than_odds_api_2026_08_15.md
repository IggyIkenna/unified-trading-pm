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
related: [sports_odds_api_data_type_casing_standardization_2026_08_15, sports_consolidated_closeout_2026_07_19]
parent_epic: sports_master
source: interactive-session
created: 2026-08-15
last_updated: 2026-08-17
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_08/sports_odds_api_data_type_casing_standardization_2026_08_15.md,
    /plans/active/sports_satellite_ao_dispatch_batch14_2026_08_16.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/betfair_adapter.py,
    unified-api-contracts/unified_api_contracts/registry/data_type_capability.py,
  ]
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

## Todos

- [x] ✅ [DIAG] P2. Measure whether `footystats.py`'s `canonical_sports_is_data_type("ODDS") or "ODDS"` fallback is
      actually hit in practice. **RESOLVED by static proof, no runtime measurement needed**: every one of
      footystats.py's ~14 call sites passes the hardcoded string literal `"ODDS"`, and
      `SPORTS_IS_DATA_TYPE_LOWERCASE_FORM` (`unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py:303`)
      is built as `{key: key.lower() for key in SPORTS_DATA_TYPE_TO_SOURCE}` — `"ODDS"` IS a key of
      `SPORTS_DATA_TYPE_TO_SOURCE` (line 228: `"ODDS": "footystats"`), so it is unconditionally also a key of the
      lowercase-form dict. `canonical_sports_is_data_type("ODDS")` therefore always returns `"odds"` (truthy) — the
      `or "ODDS"` fallback is dead code for this call site, not merely rare. footystats.py writes lowercase `"odds"`
      to the manifest on every call; it is NOT a live uppercase-row source. (repo: instruments-service)
- [ ] [DIAG] P3. Determine whether `betfair_adapter.py`'s uppercase `"ODDS"` write represents a real,
      currently-accruing population or a phantom write (same class as the two already-resolved phantom-uppercase
      populations found 2026-07-26 and 2026-08-14). **Partially narrowed, not resolved**: confirmed via static
      analysis that `BetfairAdapter` is a live, registered adapter (`market-tick-data-service`'s
      `market_interface/factory.py:197` — `"betfair": ("sports", BetfairAdapter)` — and wired into
      `adapters/umi_tick_provider.py:215`), i.e. NOT dead/unregistered code the way a phantom write would typically
      be. Confirming whether it has an actual accruing row population requires a live manifest census (row counts,
      `attempted_at` recency) — out of scope this session under the standing "docs only, no writes" constraint,
      which explicitly bars production queries, not just writes. (repo: market-tick-data-service)
- [ ] [DECISION][OPERATOR] P2. Given MDPS already treats `["odds","trades","ODDS","TRADES"]` as accepted-equivalent,
      decide whether full casing unification (rewrite every uppercase writer) is the right end-state, or whether the
      ecosystem already has a working case-insensitive normalization layer that makes "there are two casings" a
      non-problem in practice — in which case the real fix is just making the few remaining exact-match consumers
      (like the odds_api-specific ones already fixed) case-tolerant, not rewriting every writer. This is a scope
      decision, not a measurement.
- [x] ✅ [DIAG] P3. Confirm whether `unified_api_contracts/registry/schema_spec.py:434`'s separate `data_type="ODDS"`
      entry is a real, used, exact-match consumer. **RESOLVED — confirmed real and live**: `find_schema()`
      (`schema_spec.py`) is an exact-match lookup, called from `generate_instrument_catalogue.py:112` as
      `find_schema(capability.asset_group, capability.data_type)`, where `capability` is a `DataTypeCapability`
      entry. `data_type_capability.py`'s two SPORTS `DataTypeCapability` entries for ODDS (lines 1143 and 1159) are
      STILL declared as uppercase `data_type="ODDS"` — unchanged, not touched by the odds_api plan's Phase 0 (that
      plan only touched the live manifest write path, not this static capability-registry declaration). Since both
      the capability entry and the `schema_spec.py:434` registry entry use the SAME uppercase literal, this is a
      currently-matching, live exact-match pair — `find_schema(SPORTS, "ODDS")` succeeds today. **Consequence for
      any future casing decision**: `data_type_capability.py`'s two ODDS entries and `schema_spec.py:434` must be
      changed TOGETHER, in the same change — flipping one without the other would make `find_schema()` return
      `None` for SPORTS ODDS and silently break `generate_instrument_catalogue.py`'s schema lookup. (repo:
      unified-api-contracts)

## What NOT to assume

- Do not assume this is "the same fix, just more files" — footystats.py is a different SERVICE (instruments-service)
  with its own capture pipeline, and betfair_adapter.py is a different VENUE with potentially different downstream
  consumers. Each needs its own scoping pass, not a blind extension of the odds_api plan's phases.
- Do not conflate this with the `instrument_type=="ODDS"`/`data_type=="TRADES"` axis from the K1/K2 incident — different
  fields, different meaning, already has its own (troubled) history.

## Progress Log

- 2026-08-16 (slot-2, data_engineering, "docs only, no writes" session): Found while sweeping unread sports-domain
  issue docs for orphaned findings — this doc's "Open questions for whoever picks this up" section was bare numbered
  prose, never converted to `- [ ]` todos (the workspace HARD RULE this exact ritual exists to catch). Converted all
  4 questions into tracked `- [ ] [DIAG]`/`[DECISION][OPERATOR]` todos with priority + repo, no content change beyond
  format. No measurement/investigation performed this session (docs-only scope) — the underlying questions remain
  unanswered, only now trackable.
- 2026-08-16 (slot-2, data_engineering, "docs only, no writes" session, second pass): Resolved 2 of the 4 todos by
  read-only static code analysis (no production queries, no writes to code): (1) footystats.py's uppercase fallback
  is proven dead code — `"ODDS"` is always a key of `SPORTS_DATA_TYPE_TO_SOURCE`/`SPORTS_IS_DATA_TYPE_LOWERCASE_FORM`
  by construction, so `canonical_sports_is_data_type("ODDS")` always returns truthy `"odds"`; footystats.py is
  confirmed NOT a live uppercase-row source. (2) `schema_spec.py:434`'s `data_type="ODDS"` entry is confirmed a
  real, live, exact-match consumer — `data_type_capability.py`'s two SPORTS ODDS `DataTypeCapability` entries
  (lines 1143, 1159) are still uppercase and feed `find_schema()` via `generate_instrument_catalogue.py:112`; both
  must move together in any future casing change or `find_schema()` breaks. Narrowed (not resolved) the betfair_adapter
  todo: confirmed `BetfairAdapter` is a live, registered, wired adapter (`factory.py:197`,
  `umi_tick_provider.py:215`) — not obviously dead code — but confirming an actual accruing row population needs a
  live manifest census, which is a production query, out of scope this session. The DECISION todo remains
  operator-owned, untouched.
- 2026-08-16 (cicd agt-abeafe, slot 14, `ldr_qg_failure` escalation on live-defi-rollout): this doc was the sole
  `check_ag_closeout_linkage` orphan (asset_group=[sports], no reachable path to `sports_consolidated_closeout_2026_07_19.md`)
  blocking `quality-gates-v2`'s `checks` slice. Added `sports_consolidated_closeout_2026_07_19` to `related:` —
  verified `check_ag_closeout_linkage.py --only <this doc>` now reports 0 new orphans, and the full corpus sweep
  reports 0 orphans (baseline 0). No content change. `check_reference_paths` (the escalation's other named failure)
  had already self-healed via a later concurrent commit before this dispatch — verified 34 dangling refs == baseline
  34, no action needed there.
- **na-eligibility-audit 2026-08-17** [body-hash:10630b9891d84b9a]: KEEP-NA-STALE (already-duplicated) — item 1 (betfair_adapter.py uppercase ODDS census) already extracted verbatim into sports_satellite_ao_dispatch_batch14_2026_08_16.md (status:draft, not yet active); item 2 is an explicit [OPERATOR][DECISION] casing-unification-end-state item, batch14 explicitly excludes it from extraction. Do not reclassify — would duplicate batch14 once it activates.
- **context-scout 2026-08-17**: populated context_scope (0 entries -- lean-frontmatter doc, no context_scope key).
- **context-scout 2026-08-17** (re-scout, same day): populated context_scope (4 entries) — supersedes the entry
  immediately above. The doc's body names multiple concrete, still-open source targets (`betfair_adapter.py`,
  `data_type_capability.py`) plus the two docs this exact finding is scoped against
  (`sports_odds_api_data_type_casing_standardization_2026_08_15`, the plan this doc's title is "wider than"; and
  `sports_satellite_ao_dispatch_batch14_2026_08_16`, where item 1 was already extracted per the audit entry above) —
  "lean frontmatter" is not one of this skill's code-free exemptions (dispatch-batch coordinator / finalize gate /
  design-proposal / meta-audit-of-docs), so the prior 0-entry verdict was an under-scout, not a correct minimal
  result.
