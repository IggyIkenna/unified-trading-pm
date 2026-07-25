---
doc_type: issue
title:
  Sports curated-universe expansion — continental majors shipped, domestic top+below+cup selection for 145 new countries
  remains
summary: >-
  Spun off from `sports_satellite_ao_dispatch_batch2_2026_07_24.md` (that plan file is near its 1000-line hard cap from
  concurrent slot activity) to avoid further growth there. Consolidates one session's full investigation of the
  "Curated-universe definition → backfill → residual drop" todo (Directive A/B,
  `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`). Continental/international majors (11
  entries) are shipped and verified. The domestic selection (top league + division below + domestic cup, per country,
  for the ~145 of 171 catalog countries not yet in `LEAGUE_REGISTRY`) is NOT done — it needs real per-country tier
  research, not something to fabricate.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-api-contracts, instruments-service]
scope: [engineer]
tags: [sports, curated-universe, league-registry, mvp-scope, directive-a-b]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
  ]
created: 2026-07-25
priority: P1
parent_epic: sports_master
source: "[DATA] slot-2, one session's full investigation of sports_satellite_ao_dispatch_batch2-007"
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# Sports curated-universe expansion — what's shipped, what remains (2026-07-25)

## What I found + shipped this session

**Data located** (all real, verified, no guessing):

- `gs://instruments-store-sports-prd-central-element-323112/_index/_backups/availability_index.20260505T132209Z.pre-leagues-retire.parquet`
  — 375 leagues with real already-captured API-Football data (pre-pruning snapshot, before the 2026-05 cutdown to 94).
- `gs://instruments-store-sports-prd-central-element-323112/sports_reference/by_date/day=2024-01-15/pipeline_mode=batch_instruments_service/entity=leagues/leagues.parquet`
  (object timestamp 2026-06-24, recent) — the **full raw API-Football leagues catalog**: 1,228 rows, columns
  `league_id, name, country, league_type, logo_url`, 776 `League` / 452 `Cup`, 171 distinct countries, zero null
  countries. `country="World"` (176 entries, 175 `Cup`) is exactly Directive A/B's "continental cups + majors" bucket,
  cleanly separated from the 171 real countries' domestic entries.

**Architecture gap found + fixed**: `_mvp_football_league_ids()` (feeds the sports `is_mvp()` predicate) had NO
`classification` filter — any new `sport=="FOOTBALL"` registry entry silently expanded MVP/prediction scope regardless
of intent. The "obvious fix" (filter to `classification=="Prediction"`) would have wrongly SHRUNK MVP scope from 96 to
33 (the 96-baseline mixes Prediction/Features/Reference classifications). **Resolved**: added
`LeagueDefinition.in_mvp_scope: bool = True` (default preserves all 107 pre-existing entries unchanged) and repointed
the derivation function to filter on it. Verified numerically before shipping (MVP count stayed exactly 96, zero
pollution).

**Shipped** (`unified-api-contracts@7b13196e`): 11 continental/international majors — `WORLD_CUP`, `EURO_CHAMPIONSHIP`,
`FIFA_CLUB_WORLD_CUP`, `COPA_AMERICA`, `OFC_CHAMPIONS_LEAGUE`, `CONCACAF_CHAMPIONS_LEAGUE`,
`AFC_CHAMPIONS_LEAGUE_ELITE`, `AFC_CHAMPIONS_LEAGUE_TWO`, `UEFA_NATIONS_LEAGUE`, `CAF_CHAMPIONS_LEAGUE`,
`CONCACAF_NATIONS_LEAGUE` — all `in_mvp_scope=False`, `classification="Reference"`, `tier=0`. Post-ship cross-check
against real captured `ODDS` data confirmed zero overlap, consistent with the 5 pre-existing continental cups
(`UCL`/`UEL`/`UECL`/`COPA_LIBERTADORES`/`COPA_SUDAMERICANA`, `in_mvp_scope=True`) which DO have real odds data.
`season_months` on the 11 new entries is a **hemisphere-based placeholder** (operator-approved: UEFA/CONCACAF/AFC →
Northern (8,5); CONMEBOL/CAF/OFC → Southern (2,11)) — NOT researched per-competition, flagged with an explicit code
TODO. Several are quadrennial (World Cup, Euros, Copa America), not annual.

**Dead end, caught before shipping**: attempted the domestic-cups slice for the 26 countries already in
`LEAGUE_REGISTRY` (FA Cup, DFB Pokal, Coppa Italia, etc.). A string-vs-int type bug in my own filter made 25
already-registered cups look like new candidates — confirmed via direct `LEAGUE_REGISTRY` lookup before writing any code
that all 25 already exist under different key names (`FA_CUP`, `COPA_DEL_REY`, `DFB_POKAL`, ...). Nothing to add here;
the 26 already-covered countries' cups are done.

## What remains (real work, not more discovery)

The domestic top-league + division-below + domestic-cup selection for the **145 of 171 catalog countries** not yet in
`LEAGUE_REGISTRY` at all. This needs real per-country football knowledge (which division is genuinely "top", which is
"the division below" — not determinable from the catalog's `league_type`/`name` fields alone; several near-miss traps
already found this session: `Erste Liga Cup` uncertain tier for Switzerland, Mexico's cup naming churned across
`Copa MX`/`Copa por México`/`Campeón de Campeones` with real uncertainty about which is current). Fabricating this
per-country is worse than not doing it — a wrong tier assignment baked into the write-gate is expensive to unwind and
silently wrong.

**Recommended approach for whoever picks this up**:

1. Join `leagues.parquet` (1,228 rows) against the 375-already-captured list (already-paid-for API cost) — prioritize
   countries where real data already exists over brand-new API spend.
2. For each of the 145 uncovered countries, resolve top-division + division-below + domestic-cup via a reliable external
   reference (not guessed from the `name` field alone) — this is the part that needs real research.
3. Apply the resolved per-source caps from this session's measurement (Understat 18, footystats 30, ODDS 30
   [operator-confirmed real number over the ~20 estimate], SFI 33 — all already within API-Football coverage).
4. Ship new entries the SAME way this session did: `in_mvp_scope=False` unless a league genuinely has real
   odds-API-captured data (verify via the same backup-parquet query pattern before setting `True`), snapshot/QG before
   each batch, verify the MVP-scope count doesn't move unexpectedly.
5. THEN steps 2 (backfill, ~6M API-Football calls over weeks per Directive A) and 3 (residual drop, snapshot-first) of
   the original 3-step todo.

## What unblocks this (the specific missing input, not a vague "needs research")

This todo is parked — not stalled — pending ONE of:

- A **reliable per-country football-league-tier reference source** (e.g. a licensed/structured football-data provider's
  league-hierarchy endpoint, Wikipedia's per-country league pyramid articles cross-checked against `leagues.parquet`'s
  `api_football_id`s, or an operator-provided authoritative list) that can resolve "which division is genuinely
  top-tier, which is the division below" for each of the 145 countries WITHOUT guessing from the catalog's bare `name`
  field alone. The catalog's `name` field is NOT sufficient on its own — this session hit real, confirmed ambiguity even
  on well-known competitions (see "Near-miss error classes" below).
- OR an **operator-provided explicit country/league list** (sidesteps the research requirement entirely — the operator
  names the leagues, the worker just resolves `api_football_id`s and ships).

Whoever picks this up should NOT attempt per-country research from general/training knowledge alone and self-verify via
spot-checks — that is exactly the pattern that produced 2 near-misses this session even with careful verification. Get
the reliable source first.

## Near-miss error classes this session hit (inherit this verification bar)

1. **Data-matching / type bugs that silently produce false "new candidate" results.** `catalog['league_id']` is STRING
   dtype; comparing it against a `set()` of INTEGER `api_football_id`s from `LEAGUE_REGISTRY` silently never matches —
   every entry looks "not yet in registry" even when 100% are already present. Caught via a direct
   `LEAGUE_REGISTRY.get(key)` lookup before writing any code, not by trusting the filtered candidate list. **Rule for
   next session**: before adding ANY entry, do a direct membership check by `api_football_id` (not just by generated key
   name) against the live registry.
2. **Uncertain-competition-identity ambiguity that superficial keyword/name matching does not catch.** Two examples: (a)
   a keyword filter for "continental majors" matched `Kings World Cup Nations` and `AGCFF Gulf Champions League` — both
   excluded on inspection as not genuinely "major" despite passing the filter; (b) Switzerland's `Erste Liga Cup` and
   Mexico's `Copa MX`/`Copa por México`/`Campeón de Campeones` all had real, unresolved ambiguity about which one is the
   current/correct primary competition — excluded rather than guessed. **Rule for next session**: a name/keyword match
   is a CANDIDATE, never a decision — every inclusion needs independent confirmation it's the genuinely correct,
   current, primary competition for that country/tier.

## Todos

- [ ] [DATA] P1. Resolve the domestic top+below+cup selection for the 145 uncovered catalog countries (real per-country
      tier research from a reliable source — see "What unblocks this" above — not fabricated, not guessed from
      training-knowledge recall) and add the corresponding `LeagueDefinition` entries to
      `unified_api_contracts/canonical/domain/sports/league_data_other.py`'s `REFERENCE_LEAGUES` (or a new
      curated-universe-specific dict, worker's call), `in_mvp_scope=False` unless verified against real captured odds
      data per this session's pattern. Apply both near-miss rules above at every step. (repo: unified-api-contracts).
      **Done when**: every genuinely-selectable country from Directive A/B's rules has its top league + division-below +
      domestic cup added, verified via `_mvp_football_league_ids()` count staying at 96 (or intentionally moving, with
      evidence, if a league is confirmed to belong in MVP scope), `quality-gates.sh` green.
- [ ] [DATA] P2. Once the domestic selection lands, run step 2 (curated-universe backfill, API-Football fixtures +
      enrichment 2019→, gated + honest-empty for no-enrichment leagues, burn budget per the resolved per-source caps)
      then step 3 (drop residual out-of-curated rows/objects, snapshot-first, twin-verified). (repo:
      instruments-service). **Done when**: backfill complete for the curated set with honest-empty handling; residual
      rows dropped snapshot-first; re-measured honest-coverage recorded.

## Codex SSOTs

No new durable contract — this executes Directive A/B from
`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`, already the SSOT for the selection rules
themselves.
