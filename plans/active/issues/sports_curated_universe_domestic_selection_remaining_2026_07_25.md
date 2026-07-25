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

**2026-07-25 (slot 8), first verified domestic batch shipped** (`unified-api-contracts@162e51a3`): 15 new
`LeagueDefinition` entries (top league + division below + primary domestic cup) for 5 countries — Ukraine, Croatia,
Morocco, Serbia, Egypt. Each country's tier structure verified via WebSearch against a real external source (Wikipedia)
before being added — not derived from the catalog's bare `name` field, not recalled from training knowledge. All
`in_mvp_scope=False` (none of the 5 have real captured odds data). Zero `api_football_id` collisions with the existing
registry; `_mvp_football_league_ids()` count stayed exactly 96. This batch is the TEMPLATE for the region batches below
— resolved BLK-46511b79's question of whether the 145-country todo should be re-scoped: main's answer confirmed
WebSearch-with-citations IS the reliable per-country source this doc's "What unblocks this" section asked for, so the
remaining ~138 countries are now split into 11 confederation-grouped batch todos rather than one monolith (see Todos
below) — small enough to be independently reviewable, large enough to make real progress per dispatch.

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

## What unblocks this (RESOLVED 2026-07-25, BLK-46511b79)

**No longer parked.** The 2026-07-25 slot-8 batch proved WebSearch-with-citations against a real external source
(Wikipedia, or an equivalent structured reference) IS the reliable per-country tier source this section originally asked
for — main confirmed this explicitly answering BLK-46511b79: "your WebSearch-with-citations method IS the reliable
per-country source I said was required — that is precisely the difference between research and guessing."

The remaining constraint is SCALE, not source-availability: 138 countries × 3 leagues each is too much for one dispatch
to verify carefully in one pass, so it is split into the 11 region batches below (Todos section). Per-batch contract,
inherited from the first shipped batch:

- Every entry backed by a real citation (WebSearch or equivalent) — never guessed from the catalog `name` field alone,
  never recalled from training knowledge without verification.
- A country you cannot verify with a citation is SKIPPED and listed as unverified in the batch's evidence, never guessed
  to hit a completeness target.
- Apply BOTH near-miss rules below at every step (the type-bug check and the name-is-a-candidate-not-a-decision rule).

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

- [x] ✅ [DATA] P1. ~~Resolve the domestic top+below+cup selection for the 145 uncovered catalog countries~~ —
      SUPERSEDED-BY-DECOMPOSITION 2026-07-25 (BLK-46511b79, main-approved). First verified batch shipped
      (unified-api-contracts@162e51a3, 5 countries / 15 entries); the remaining 138 countries are decomposed into the 11
      region-batch todos below rather than completed as one monolith — see the blockquote immediately below for the
      shared contract every batch inherits.

> **Decomposed 2026-07-25 (BLK-46511b79, main-approved)**: the original single 145-country todo is replaced by the 11
> confederation-grouped batches below. Each batch is a DIFFERENT set of `LEAGUE_REGISTRY` rows, so all 11 are
> independent and safe to dispatch concurrently (`sequential: false` — no shared file/row overlap between batches). The
> shared done-when contract for every batch: for each country in the list, resolve top league + the division directly
> below + the primary domestic cup, EACH backed by a real citation (WebSearch or equivalent structured reference); a
> country you cannot verify with a citation is SKIPPED and listed as unverified in the shipping evidence, never guessed
> to hit completeness. Add the `LeagueDefinition` entries to
> `unified_api_contracts/canonical/domain/sports/league_data_other.py`'s `REFERENCE_LEAGUES`, `in_mvp_scope=False`
> unless verified against real captured odds data (check the pre-pruning backup parquet per the first-batch pattern).
> Apply BOTH near-miss rules from "Near-miss error classes" above at every step — direct `api_football_id` membership
> check before adding (not just generated-key lookup), and treat every name/keyword match as a candidate needing
> independent confirmation, never a decision. Verify `_mvp_football_league_ids()` count stays 96 (or moves intentionally
> with evidence). `quality-gates.sh` green before shipping each batch.

- [ ] [DATA] P1. **Western Europe / small nations (UEFA)** — Andorra, Cyprus, Estonia, Faroe Islands, Finland,
      Gibraltar, Iceland, Ireland, Latvia, Liechtenstein, Lithuania, Luxembourg, Malta, Northern Ireland, San Marino,
      Wales (16 countries). (repo: unified-api-contracts). **Done when**: per the shared contract above, for this
      country list.
- [ ] [DATA] P1. **Eastern Europe (UEFA)** — Albania, Armenia, Azerbaijan, Belarus, Bosnia, Bulgaria, Crimea, Czech
      Republic, Georgia, Hungary, Kosovo, Macedonia, Moldova, Montenegro, Romania, Slovakia, Slovenia (17 countries).
      Note: Crimea's political/federation status is genuinely contested — verify which football federation the catalog's
      data actually reflects before adding, or skip as unverifiable. (repo: unified-api-contracts). **Done when**: per
      the shared contract above, for this country list.
- [ ] [DATA] P1. **Central Asia (AFC)** — Kazakhstan, Kyrgyzstan, Tajikistan, Turkmenistan, Uzbekistan (5 countries).
      (repo: unified-api-contracts). **Done when**: per the shared contract above, for this country list.
- [ ] [DATA] P1. **South America (CONMEBOL)** — Bolivia, Colombia, Ecuador, Paraguay, Peru, Uruguay, Venezuela (7
      countries). (repo: unified-api-contracts). **Done when**: per the shared contract above, for this country list.
- [ ] [DATA] P1. **North/Central America + Caribbean (CONCACAF)** — Antigua and Barbuda, Aruba, Barbados, Belize,
      Bermuda, Canada, Costa Rica, Cuba, Curacao, Dominican Republic, El Salvador, Grenada, Guadeloupe, Guatemala,
      Haiti, Honduras, Jamaica, Nicaragua, Panama, Suriname, Trinidad and Tobago (21 countries — largest batch, consider
      splitting further if a worker finds the citation-research load too heavy for one dispatch). (repo:
      unified-api-contracts). **Done when**: per the shared contract above, for this country list.
- [ ] [DATA] P1. **West Africa (CAF)** — Benin, Burkina Faso, Cameroon, Congo, DR Congo, Gabon, Gambia, Ghana, Guinea,
      Ivory Coast, Liberia, Mali, Mauritania, Nigeria, Senegal, Togo (16 countries). (repo: unified-api-contracts).
      **Done when**: per the shared contract above, for this country list.
- [ ] [DATA] P1. **North/East/Southern Africa (CAF)** — Algeria, Angola, Botswana, Burundi, Eswatini, Ethiopia, Kenya,
      Lesotho, Libya, Malawi, Mauritius, Namibia, Rwanda, Somalia, South Africa, Sudan, Tanzania, Tunisia, Uganda,
      Zambia, Zimbabwe (21 countries — largest batch, consider splitting further if a worker finds the citation-research
      load too heavy for one dispatch). (repo: unified-api-contracts). **Done when**: per the shared contract above, for
      this country list.
- [ ] [DATA] P1. **Middle East (AFC/WAFF)** — Bahrain, Iran, Iraq, Israel, Jordan, Kuwait, Lebanon, Oman, Palestine,
      Qatar, Saudi Arabia, Syria, United Arab Emirates, Yemen (14 countries). Note: Saudi Arabia has 3 catalog cup
      competitions (Crown Prince Cup, King's Cup, Super Cup) — verify which is genuinely "the" primary domestic cup
      before picking one, per the near-miss rules. (repo: unified-api-contracts). **Done when**: per the shared contract
      above, for this country list.
- [ ] [DATA] P1. **South Asia (AFC)** — Bangladesh, Bhutan, India, Maldives, Nepal, Pakistan (6 countries). (repo:
      unified-api-contracts). **Done when**: per the shared contract above, for this country list.
- [ ] [DATA] P1. **East/Southeast Asia (AFC)** — Cambodia, Chinese Taipei, Hong Kong, Indonesia, Laos, Macao, Malaysia,
      Mongolia, Myanmar, Philippines, Singapore, Thailand, Vietnam (13 countries). (repo: unified-api-contracts). **Done
      when**: per the shared contract above, for this country list.
- [ ] [DATA] P1. **Oceania (OFC)** — Fiji, New Zealand (2 countries). (repo: unified-api-contracts). **Done when**: per
      the shared contract above, for this country list.
- [ ] [DATA] P2. Once ALL 11 domestic-selection batches above land (not just one), run step 2 (curated-universe
      backfill, API-Football fixtures + enrichment 2019→, gated + honest-empty for no-enrichment leagues, burn budget
      per the resolved per-source caps) then step 3 (drop residual out-of-curated rows/objects, snapshot-first,
      twin-verified). (repo: instruments-service). **Done when**: backfill complete for the curated set with
      honest-empty handling; residual rows dropped snapshot-first; re-measured honest-coverage recorded.

## Codex SSOTs

No new durable contract — this executes Directive A/B from
`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`, already the SSOT for the selection rules
themselves.
