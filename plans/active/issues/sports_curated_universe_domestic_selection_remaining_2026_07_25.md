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

- [x] ✅ [DATA] P1. **Western Europe / small nations (UEFA)** — Andorra, Cyprus, Estonia, Faroe Islands, Finland,
      Gibraltar, Iceland, Ireland, Latvia, Liechtenstein, Lithuania, Luxembourg, Malta, Northern Ireland, San Marino,
      Wales (16 countries). — `unified-api-contracts@a04996fd` (42 entries). Notable finds: Liechtenstein has NO
      domestic league (clubs play in the Swiss system, WebSearch-confirmed) — only its national Cup added, matching the
      catalog's single entry exactly, no league fabricated. Finland's Ykkönen was demoted to tier 3 in 2024 when
      Ykkösliiga launched as the real tier 2 — used Ykkösliiga, not the more obviously-named Ykkönen. Wales's catalog
      "FAW Championship" does not clearly map to the real North/South regional tier-2 split (post-2019 Cymru Leagues
      merger) — excluded rather than guessed. Iceland's catalog "Úrvalsdeild" confirmed as the current top flight under
      its historical name (rebranded "Besta deild karla" for sponsorship, same competition). Zero `api_football_id`
      collisions; `_mvp_football_league_ids()` stayed 96; zero real captured ODDS data for all 42 entries. Landed
      through 3 concurrent-edit collisions (East/Southeast Asia, South Asia, and CONCACAF-remaining batches each landing
      on the same file mid-session) — resolved each via a clean re-split of both batches' blocks (verified zero
      duplicate keys every time) + recomputed the 2 hardcoded-count tests fresh from the live merged registry each time,
      not hand-arithmetic. (repo: unified-api-contracts). **Done when**: per the shared contract above, for this country
      list.
- [x] ✅ [DATA] P1. **Eastern Europe (UEFA)** — Albania, Armenia, Azerbaijan, Belarus, Bosnia, Bulgaria, Crimea, Czech
      Republic, Georgia, Hungary, Kosovo, Macedonia, Moldova, Montenegro, Romania, Slovakia, Slovenia (17 countries). —
      **ALREADY SHIPPED (slot unknown), checkbox flip caught up 2026-07-25T04:30Z (slot 11)**,
      `unified-api-contracts@dbd64914` (49 entries, 16 of 17 countries; Bosnia gets 2 division-below entries for its
      genuinely dual-entity FBiH/RS structure). Crimea SKIPPED per the near-miss rule — no solid citable evidence the
      catalog's "Premier League" entry is a stable, sanctioned competition under any recognized body (contested
      federation status). Two near-miss traps caught: Czech "Tipsport Liga" is an unrelated friendly tournament (Chance
      Liga is the real top flight); Moldova's current top-flight is "Moldovan Liga" not "Liga 1" (Liga 1 is the
      historical rename of the 2nd tier). All `in_mvp_scope=False` (verified via the pre-pruning backup parquet, zero
      real captured ODDS rows). Zero `api_football_id` collisions; `_mvp_football_league_ids()` stayed 96. (repo:
      unified-api-contracts). **Done when**: per the shared contract above, for this country list.
- [x] ✅ [DATA] P1. **Central Asia (AFC)** — Kazakhstan, Kyrgyzstan, Tajikistan, Turkmenistan, Uzbekistan (5 countries).
      `unified-api-contracts@49049b7` (9 entries). Kazakhstan (Premier League/First Division/Cup) + Uzbekistan (Super
      League/Pro League/Cup) got full top+below+cup, each WebSearch-verified. Kyrgyzstan/ Tajikistan/Turkmenistan got
      top-league only — WebSearch confirmed real division-below/cup competitions exist for all three, but the
      api-football `leagues.parquet` catalog carries no `api_football_id` for them (checked directly, not assumed), so
      per the near-miss "never fabricate an id" rule those tiers are omitted rather than guessed. Turkmenistan's catalog
      "Youth League" (829) explicitly excluded as wrong-axis. 0 registry collisions, MVP-scope count unchanged at 96,
      `in_mvp_scope=False` (no captured odds data for any of the 5 countries). quality-gates.sh green.
- [x] [DATA] P1. ✅ **South America (CONMEBOL)** — `unified-api-contracts@4e437004`. 19 entries across 7 countries, each
      WebSearch-verified against Wikipedia before adding. Two deliberate skips (never guessed): Bolivia's division-below
      (the catalog's only 2nd-tier candidate, "Nacional B", was Bolivia's real 2nd tier ONLY 2011-2016, replaced by Copa
      Simón Bolívar in 2016 which isn't in the catalog at all); Peru's cup (Copa Perú is an amateur/promotion
      tournament, not a knockout cup; Copa Bicentenario was dissolved after 2021, defunct — neither is a genuine current
      primary cup). Real near-miss traps beyond this doc's documented list: Paraguay/Uruguay split their top flight into
      Apertura/Clausura HALVES of the same season (not two tiers) — used Apertura as the representative row, did not add
      Clausura as a second entry; Colombia's "Liga Femenina" (women's league) correctly excluded, not a men's-pyramid
      candidate. Zero `api_football_id` collisions; `_mvp_football_league_ids()` stayed 96 (verified directly, not
      assumed); 2 pre-existing hardcoded-count tests updated (126→145 Understat gaps, 35→54 non-MVP football) matching
      the established batch pattern. All 19 confirmed `in_mvp_scope=False` via a live odds-manifest check (zero matches
      for any of the 7 countries). Full per-country citations in the commit message.
- [x] [DATA] P1. ✅ **North/Central America + Caribbean (CONCACAF)** — all 21 countries covered across two concurrent
      slots. A different slot independently landed `unified-api-contracts@dfeef957` for 7 countries (Costa Rica,
      Jamaica, Honduras, Panama, Trinidad and Tobago, Canada, Guatemala) — verified their Canada/Guatemala entries
      exactly matched this slot's own independent WebSearch analysis before treating them as done. This slot then landed
      the remaining 14 countries via `unified-api-contracts@80717936` (Antigua and Barbuda, Aruba, Barbados, Belize,
      Bermuda, Cuba, Curacao, Dominican Republic, El Salvador, Grenada, Guadeloupe, Haiti, Nicaragua, Suriname — 17
      entries, since Dominican Republic/El Salvador/Nicaragua each got a top-league + cup pair). 11 of the 14 carry only
      ONE catalog entry (top league) — division-below and cup genuinely absent from the catalog, no id to cite, skipped
      per the never-fabricate rule. Three had real decisions, WebSearch-verified: Dominican Republic's "Copa LDF"
      confirmed as the sole/primary cup candidate; El Salvador's "Copa Presidente" is typed `League` in the raw catalog
      (a catalog mislabel) but confirmed as the genuine primary knockout cup, used despite the catalog's own coarse type
      tag; Nicaragua's "Liga Primera U20" excluded (wrong axis, youth), "Copa Nicaragua" confirmed primary cup. Required
      re-merging 4x on top of concurrent East/Southeast Asia, South Asia, and Fiji+New Zealand/OFC batches landing on
      the same file mid-session — each resolved via reset-to-clean-HEAD + fresh re-append + live recompute (0 collisions
      each time; `_mvp_football_league_ids()` stayed 96 throughout). Final registry: 347 entries, 335 Understat gaps,
      244 non-MVP football (both hardcoded-count tests updated to match, live-derived not hand-arithmetic).
      `quality-gates.sh` green on the final ship. (repo: unified-api-contracts).
- [x] ✅ [DATA] P1. **West Africa (CAF)** — Benin, Burkina Faso, Cameroon, Congo, DR Congo, Gabon, Gambia, Ghana,
      Guinea, Ivory Coast, Liberia, Mali, Mauritania, Nigeria, Senegal, Togo (16 countries).
      `unified-api-contracts@28bda62a` (16 entries, 13 verifiable countries). Burkina Faso/DR Congo/Ivory Coast SKIPPED
      — zero entries in the api-football leagues catalog, genuinely unverifiable from this source. Cameroon + Ghana got
      full top+below+cup; the other 11 countries got top-league only (real division-below/cup confirmed to exist via
      WebSearch but absent from the catalog — no id to cite, omitted per the never-fabricate rule). Cameroon's/Ghana's
      catalog "Super Cup" entries excluded (secondary exhibitions, not the primary cup). Required re-merging 3x on top
      of concurrent South America, Eastern Europe, and Middle East/AFC-WAFF batches landing on the same file mid-session
      — 0 collisions each time, MVP-scope count unchanged at 96 throughout. quality-gates.sh green.
- [x] [DATA] P1. ✅ **North/East/Southern Africa (CAF)** — `unified-api-contracts@cf06ea48`. 30 entries across 21
      countries. 15 of 21 countries carried only ONE catalog entry (top league only) — division-below and cup correctly
      skipped, no id to cite, no ambiguity. Six countries had real decisions, each WebSearch-verified: Algeria (Coupe
      Nationale = primary, excluded Coupe de la Ligue + Super Cup as secondary, U21 League as wrong axis); Angola (only
      candidate cup is a Super Cup — no genuine primary cup exists in the catalog, skipped rather than mislabel); Kenya
      (FKF Premier League vs Super League confirmed tier order; "Shield Cup" confirmed as the FKF President's Cup under
      an earlier sponsorship name — Kenya's real FA-Cup equivalent); South Africa (generic "Cup" = Nedbank Cup, the
      traditional premier knockout since 1971; "8 Cup" = MTN8, top-8-only, excluded as secondary; Diski Challenge/Shield
      excluded as reserve/youth); Tunisia (Cup = primary, Super Cup excluded). Zero `api_football_id` collisions;
      `_mvp_football_league_ids()` stayed 96; 2 hardcoded-count tests updated. Concurrent-edit note: another slot landed
      a 16-entry West Africa batch to the same file/tests concurrently — resolved via the same
      clean-reappend-against-merged-base approach as the Middle East batch (not a manual hunk merge).
- [x] [DATA] P1. ✅ **Middle East (AFC/WAFF)** — `unified-api-contracts@a0fd391c`. 30 entries across 14 countries, each
      WebSearch-verified against Wikipedia. Saudi Arabia's flagged ambiguity resolved: King's Cup (official title "The
      Custodian of the Two Holy Mosques' Cup") is the CURRENT primary cup; Crown Prince Cup was abolished in 2017 —
      excluded as defunct, not a live competition. 6 countries (Bahrain/Jordan/Lebanon/Oman/Syria/Yemen) have no valid
      catalog 2nd-tier candidate — division-below correctly skipped, not fabricated; 4 (Iraq/Palestine/Syria/Yemen) have
      no cup candidate at all — cup also skipped. Real near-miss traps resolved via search, not guessed: Qatar's 4 cup
      candidates (Emir Cup = primary, open to both divisions; QSL Cup/QFA Cup/Super Cup = secondary); Kuwait's Emir Cup
      vs Crown Prince Cup (Emir Cup confirmed "the premier domestic knockout"); UAE's President's Cup (running since
      1974-75, both divisions) vs League Cup/Super Cup (secondary). Zero `api_football_id` collisions;
      `_mvp_football_league_ids()` stayed 96. Concurrent-edit note: another slot landed a 49-entry Eastern Europe batch
      to the same file/tests at the same time — resolved via a clean re-append against the merged base (not a manual
      hunk-by-hunk merge, too error-prone at 20+ conflict blocks) + recomputed the combined hardcoded-count tests fresh
      from the live registry (224 Understat gaps, 133 non-MVP football) rather than hand-adding deltas.
- [x] ✅ [DATA] P1. **South Asia (AFC)** — Bangladesh, Bhutan, India, Maldives, Nepal, Pakistan (6 countries).
      `unified-api-contracts@a7aa4226` (10 entries, all 6 countries verified). Two real near-miss traps caught via
      WebSearch: (1) Bhutan's naming is INVERTED from the intuitive read — "Premier League" is the top tier, "Super
      League" is the second tier; (2) India's catalog carries 7 entries across 3 unrelated axes (national club pyramid:
      ISL top / I-League second — NOT "I-League 2nd Division", that's tier-3; the Santosh Trophy is an inter-state
      representative competition, wrong axis; IFA Shield + Calcutta Premier Division are Kolkata-regional, sub-national
      scope) — resolved to ISL/I-League/AIFF Super Cup only. 0 registry collisions, MVP-scope unchanged at 96.
      quality-gates.sh green.
- [x] ✅ [DATA] P1. **East/Southeast Asia (AFC)** — Cambodia, Chinese Taipei, Hong Kong, Indonesia, Laos, Macao,
      Malaysia, Mongolia, Myanmar, Philippines, Singapore, Thailand, Vietnam (13 countries).
      `unified-api-contracts@cf4c8491` (21 entries, 11 of 13 countries). Chinese Taipei + Hong Kong SKIPPED — zero
      catalog entries. Indonesia/Thailand/Vietnam got full top+below+cup; the rest top-league only (+ cup where
      genuinely unambiguous). Two real near-miss traps caught via WebSearch, not guessed: (1) Malaysia's catalog
      "Premier League" is DEFUNCT since 2022 (replaced by the A1 Semi-Pro League, not in the catalog) — excluded rather
      than added as a stale division-below; (2) Malaysia has two prestigious cups (Malaysia Cup, historic; FA Cup,
      today's functionally-primary via continental qualification) — picked FA Cup on that evidence, not a coin flip.
      Mongolia's/Thailand's catalog "Super Cup"/"Champions Cup" excluded (verified exhibition matches). 0 registry
      collisions, MVP-scope unchanged at 96. quality-gates.sh green.
- [x] ✅ [DATA] P1. **Oceania (OFC)** — Fiji, New Zealand (2 countries). — `unified-api-contracts@0104c2f2` (6 entries).
      Fiji: catalog carries only the top league (376) -- WebSearch confirmed the real Fiji FA Cup exists but has no
      api_football_id in this catalog, omitted per the never-fabricate rule. New Zealand: catalog's "Premiership" (280)
      confirmed via WebSearch as the pre-2021 name of the current National League (2021 rebrand, same competition, not a
      different one); 2nd tier is genuinely 3 parallel regional leagues (Central/Northern/ Southern, all 3 included,
      mirroring the Bosnia FBiH/RS multi-entity precedent); Chatham Cup (1127) confirmed as the primary cup since 1923.
      Zero `api_football_id` collisions; `_mvp_football_league_ids()` stayed 96; zero real captured ODDS data confirmed
      for all 6 entries. Landed through 2 concurrent-edit collisions (East/Southeast Asia, then South Asia batches
      landing on the same file mid-session) -- resolved both via a clean re-split of each batch's block (verified zero
      duplicate keys each time) + recomputed the 2 hardcoded-count tests fresh from the live merged registry each time,
      not hand-arithmetic. (repo: unified-api-contracts). **Done when**: per the shared contract above, for this country
      list.
- [ ] [DATA] P2. Once ALL 11 domestic-selection batches above land (not just one), run step 2 (curated-universe
      backfill, API-Football fixtures + enrichment 2019→, gated + honest-empty for no-enrichment leagues, burn budget
      per the resolved per-source caps) then step 3 (drop residual out-of-curated rows/objects, snapshot-first,
      twin-verified). (repo: instruments-service). **Done when**: backfill complete for the curated set with
      honest-empty handling; residual rows dropped snapshot-first; re-measured honest-coverage recorded. — **Gate
      condition now MET 2026-07-25 (slot 3, data_engineering)**: all 11 confederation batches above are `[x]` (South
      America, Western Europe, Eastern Europe, Central Asia, CONCACAF, West Africa, N/E/S Africa, Middle East, South
      Asia, East/SE Asia, Oceania — verified via a live checkbox grep of this file, not assumed). **Step 2 launch
      BLOCKED on the af-backfill singleton lock** (`deployment-service/scripts/vm/launch-api-football-backfill-vm.sh` —
      global across ALL `af-backfill-*`/`af-audit-*` VMs regardless of entity, since API-Football rate-limits per-key,
      not per-entity; confirmed via the launcher's own docstring, not assumed). Lock currently held by
      `af-backfill-20260725-032253` (the `fixture_events` canonical re-fetch, `sports_satellite_ao_dispatch_batch2-031`
      / `issues/sports_fixture_events_refetch_progress_2026_07_25.md`), health-checked RUNNING at 2026-07-25T05:10Z,
      genuinely hours from done (359/~2500 dates at that check). Bypassing with `--force`/`--skip-lock` would repeat the
      documented 2026-07-14 GW re-run mistake this exact launcher's comments warn against — not done. **Separately, no
      dedicated "curated-universe backfill" script exists** — step 2 as scoped means running the standard
      `launch-api-football-backfill-vm.sh` mechanism against the ~200+ newly-registered `in_mvp_scope=False` league
      entries across the 11 batches (exact count not yet enumerated this session), which is itself a
      multi-hour-to-multi-day campaign once launched — not completable in one dispatch turn regardless of the lock. Step
      3 (residual row/object drop) is a genuinely destructive, snapshot-first, twin-verified operation that needs its
      own careful scoping once step 2's backfill is real and complete — not something to rush as a sub-step here.
      Released via `/skip-current-task`, not attempted. Next dispatch: re-check
      `gcloud compute instances list --filter='name~"^af-backfill-"'`; once clear, enumerate the exact new-league
      `league_id` list (all `in_mvp_scope=False` entries added across the 11 batches, i.e. everything with
      `created`/added 2026-07-25 in `league_data_other.py`'s `REFERENCE_LEAGUES`) before launching, so the backfill
      command has a concrete scoped target rather than "all leagues." — **RE-CHECKED 2026-07-25 (slot 2,
      data_engineering)**: `af-backfill-20260725-032253` is now `TERMINATED` (confirmed live via
      `gcloud compute     instances list`) — the singleton lock IS clear (it only counts `status=RUNNING`, per the
      launcher's own filter). **Enumeration done**: extracted every `api_football_id=` added across the 14
      curated-universe commits
      (`unified-api-contracts@{7b13196e,162e51a3,a04996fd,dbd64914,49049b7,4e437004,dfeef957,80717936,28bda62a,     cf06ea48,a0fd391c,a7aa4226,cf4c8491,0104c2f2}`,
      i.e. continental majors + all 11 domestic batches) via
      `git show <sha> -- .../league_data_other.py | grep '^\+.*api_football_id='` — **287 unique league_ids**, all
      independently re-verified present in the current file with `in_mvp_scope=False` (0 missing, 0 wrong-scope; the 1
      apparent mismatch on a naive substring check was a false positive — `api_football_id=504`'s comment-line mention 2
      lines above the real field, not a second entry). Reproducible in seconds from the SHA list above — not re-pasting
      the 287-id list inline here to keep this doc lean. **Still NOT launched**: could not verify the API-Football daily
      quota has reset since the 2026-07-25T08:12Z exhaustion incident
      (`issues/sports_fixture_events_refetch_progress_2026_07_25.md`'s CRITICAL entry) — this session's environment has
      no API key loaded (`get_live_quota()` returned `live=False`, registry fallback only, not a real read), and
      guessing the reset time risks repeating the exact silent-corruption failure mode that incident already found once
      today. Released via `/skip-current-task`, not attempted. Next dispatch: obtain a real `/status` read (needs the
      production API key, not available in a bare dev worktree) or operator confirmation the daily quota has reset, THEN
      launch `launch-api-football-backfill-vm.sh` scoped to the 287 enumerated league_ids (regenerate via the SHA list
      above, don't hand-copy) — 2019→ fixtures+enrichment, gated + honest-empty per Directive A/B. — **LAUNCHED
      2026-07-25T12:54Z (slot 11, data_engineering), FIXTURES-only, floor-corrected range**: this session's worktree DID
      have a working `api-football-api-key` (Secret Manager, GCP ADC) —
      `ApiFootballAdapter.get_live_quota(force_refresh=True)` returned
      `live=True daily_limit=150000 daily_remaining=73705` (~12:42Z), i.e. the daily quota from the 08:12Z exhaustion
      incident HAD already reset by mid-day (not confirmed at UTC-midnight; just confirmed live, real, authoritative —
      resolves slot 2's open blocker). **Real-code check, not guessed**: no `--league-ids`-style flag exists on this
      launcher (confirmed reading the arg parser) and none is needed — `sports.py`'s per-league preflight
      (`_is_in_canonical_write_universe` / the per-date "all expected leagues captured" skip) re-derives the expected
      league set LIVE from the current registry every run, so a plain (non-`--force`) re-run correctly detects the 287
      newly-registered leagues as missing on already-processed dates and re-fetches just that date (1 API call/date
      either way, since fixtures-by-date returns all leagues in one call) — no redo_all/`--force` needed, no wasted
      quota re-fetching already-correct old-league data. **Floor-date correction (real finding, not previously caught in
      this doc)**: the "2019→" range in this todo's own text (and repeated in slot 2's note above) CONTRADICTS the
      ratified 2026-07-21 sports data floor (`/codex/02-data/sports-2020-06-data-floor.md` — "every sports artifact
      dated before 2020-06-06 is fabrication-by-construction... DELETE, do not backfill"; that doc's own "What is MOOT"
      section names the pre-2020-06 slice of exactly this api-football reference-expansion effort). Used the CORRECTED
      range `2020-06-06..2026-07-25` for the actual launch, not the stale 2019 start. **Tarball-staleness check
      performed before trusting the launch** (per the near-miss precedent in
      `issues/sports_fixture_events_refetch_progress_2026_07_25.md`): all 4 required tarballs
      (instruments-service/unified-api-contracts/unified-trading-library/deployment-service) were genuinely STALE
      (verified via `gcloud storage cat <tarball>.manifest.json` vs local `git rev-parse HEAD` — `gsutil` itself has
      invalid/broken credentials in this session, same known unrelated issue slot 2/6 hit earlier today on this same
      doc; used `gcloud storage`, an equally-authoritative alternative, throughout). Republished via
      `LC_TARBALL_FRESHNESS=auto` (`create-code-tarballs.sh`); the launcher's own gsutil-based re-verify then false-
      -negatived (MISSING) purely from the same broken-gsutil-credential issue — manually re-confirmed all 4 fresh via
      `gcloud storage` (exact SHA match) before launching with `LC_TARBALL_FRESHNESS=off`. **Launched
      `af-backfill-20260725-125405`** (`--entity FIXTURES 2020-06-06 2026-07-25`, SPOT e2-standard-8,
      `asia-northeast1-c`), deliberately **FIXTURES-only, not full enrichment**: cheap (~1 API call/date, launcher's own
      ~5-30min estimate), a real prerequisite for enrichment (per-fixture stats/events/lineups/player-stats need
      `fixture_id`s to exist first), and enrichment's own budget/cap scoping ("burn budget per the resolved per-source
      caps") is a separate, genuinely larger campaign that deserves its own dispatch once FIXTURES for the new leagues
      actually exists — not rushed into this same launch. **Verified NOT fire-and-forget**: serial-console read at T+90s
      confirmed live boot progress AND, critically, confirmed via the VM's own printed manifest SHAs that ALL 4 repos
      deployed to the VM match this session's exact HEAD (`uac sha=71e757507382`, `utl sha=86abb7ef14a3`,
      `deployment-service sha=4e6ab8ee87bb`, `instruments-service sha=269440d7ed61`) — i.e. the VM genuinely has the
      full 287-league registry, not a stale pre-refresh copy. Not completable this turn (even a fast FIXTURES-only run
      needs health-checking to terminal). Released via `/skip-current-task {"reason_code": "GATED"}`, not
      duplicate-launched. **Follow-up finding (P3, not blocking)**: `launch-api-football-backfill-vm.sh` does not itself
      clamp `START_DATE` to the 2020-06-06 floor the way `launch-sports-entity-sweep-vm.sh` does per the floor doc's
      enforcement-surface list — the venue-epoch skip gate (`get_venue_epoch`) is defense-in-depth against an actual
      fabrication, but this launcher accepting a pre-floor start date silently (no warning) is a real gap an agent could
      trip on again; worth a small follow-up to add the same clamp/warning this launcher's sibling already has. **Next
      dispatch**: health-check `af-backfill-20260725-125405`
      (`gcloud compute instances list --filter='name~"^af-backfill-"'` +
      `gcloud storage cat gs://deployment-scripts-central-element-323112/vm-logs/af-backfill-20260725-125405/run.log`);
      once terminal, spot-verify a sample of the 287 new leagues now show captured `entity=fixtures` rows post-floor,
      THEN scope + launch the separate per-fixture enrichment campaign (budget-capped per Directive A/B) before
      considering step 2 done or touching step 3's destructive residual-drop. — **Health-checked 2026-07-25T13:33Z (slot
      4, data_engineering), STOPPED PROTECTIVELY, NOT terminal-completed**: found this VM was NOT running the cheap
      FIXTURES-only path it was launched for — it hit a live code bug where a stale-not-missing date (schema- version
      re-fetch trigger, not first-time capture) silently escapes the `--sports-entity FIXTURES` scope and falls back to
      unscoped fetch-everything (teams/standings/injuries + per-fixture stats/events/lineups/ player_stats). Measured
      directly via a live `ApiFootballAdapter.get_live_quota()` call: shared daily quota dropped 73705→66788 (~6900
      calls) in under an hour from ONE date (2026-04-18, 1761 fixtures) — more than the entire campaign's intended
      budget. Filed `BLK-aa5efbbb`; main ruled Option A (stop + fix + relaunch-after-fix) and, since the owning worker
      (this slot) stayed on other findings-closure work rather than executing the stop within a tick, main executed
      `gcloud compute instances stop af-backfill-20260725-125405` itself (protective, reversible, zero written-data loss
      — idempotent/skip-aware). Verified STATUS=TERMINATED. Root-caused + tracked in
      `issues/sports_freshness_preflight_stale_scope_escape_burns_shared_quota_2026_07_25.md` (main's canonical filing —
      supersedes an independent duplicate this slot drafted before seeing main's). **Step 2 is now BLOCKED** on that
      doc's `[DATA] P0` fix (`_freshness_preflight()` must fold `stale` into `missing_entities`, or equivalently
      `_fetch_sports_reference_block` must never fall back to unscoped fetch when a CLI `--sports-entity` scope was
      supplied) — do NOT relaunch `launch-api-football-backfill-vm.sh --entity FIXTURES` until that fix ships + is
      quality-gates green (relaunching now would re-hit the same scope-escape on any other stale-not-missing date in the
      2020-06-06..2026-07-25 range and risk exhausting the shared quota again, exactly today's earlier 08:12Z failure
      class). **Next dispatch**: pick up the P0 fix in the linked doc first; once it ships, relaunch FIXTURES-only
      (SPOT, resumes from measured progress, no data lost by the stop), health-check to terminal, THEN resume this
      todo's original spot-verify + enrichment-campaign-scoping sequence. — **P0 FIX SHIPPED 2026-07-25 (slot 7,
      data_engineering): `instruments-service@08387531`**, see the linked issue doc's now-`[x]` P0 todo for the code
      change + regression-test evidence. Step 2 is UNBLOCKED for relaunch. **Still NOT relaunched this turn** — did not
      have a live API-Football quota read available in this session to confirm the daily quota has room (the same
      guardrail slot 11's prior launch note applied), and a relaunch is real infra spend that deserves its own
      health-checked dispatch rather than a rushed same-turn action. **Next dispatch**: obtain a real
      `ApiFootballAdapter.get_live_quota(force_refresh=True)` read (or operator confirmation), confirm the
      `af-backfill-*` singleton lock is clear (`gcloud compute instances list --filter='name~"^af-backfill-"'`), THEN
      relaunch `launch-api-football-backfill-vm.sh --entity FIXTURES 2020-06-06 2026-07-25` (SPOT, resumes from measured
      progress — the fixed code now correctly stays FIXTURES-scoped on stale-not-missing dates), health-check to
      terminal, THEN resume this todo's original spot-verify + enrichment-campaign-scoping sequence. — **RELAUNCHED
      2026-07-25T15:18Z (slot 7, data_engineering)**: live quota confirmed `daily_remaining=64965/150000` (fresh
      `get_live_quota(force_refresh=True)` read, plenty of room); singleton lock confirmed clear (both prior
      `af-backfill-*` VMs `TERMINATED`). **Tarballs were stale** (last built 13:05Z, predating both this session's
      P0-fix commit and the P3 START_DATE-clamp commit) — rebuilt via `create-code-tarballs.sh --asset-group SPORTS`,
      re-verified all 4 required repos' `code/*.manifest.json` `commit_sha` match local HEAD exactly
      (`instruments-service@693280e7`, `unified-api-contracts@0b979239`, `unified-trading-library@b025d0ce`,
      `deployment-service@734fdd5`) via `gcloud storage cat` (gsutil itself still has the same broken-credential issue
      prior sessions hit on this doc — used `LC_TARBALL_FRESHNESS=off` + the manual `gcloud storage` verify instead,
      same pattern as the prior launch). **Launched `af-backfill-20260725-151845`**
      (`--entity FIXTURES 2020-06-06     2026-07-25`, SPOT e2-standard-8, `asia-northeast1-c`) — genuinely NOW carries
      the P0 fix (the VM's own code is the exact HEAD verified above). **Verified NOT fire-and-forget**: serial-console
      read at T+~60s shows clean cloud-init completion (`Up 28.72 seconds`, no errors) and normal systemd service
      startup — no crash/hang signature. Armed a background watchdog (25-min cap) polling VM status + `run.log` for a
      terminal marker (`DEPLOYMENT_COMPLETED`/`DEPLOYMENT_FAILED`/`exit_code=`) or VM self-deletion; not completable
      within this dispatch turn regardless (even the fast FIXTURES-only path needs health-checking to terminal, and this
      is real, ongoing infra spend, not something to rush). Released via `/skip-current-task`, not duplicate-launched.
      **Health-checked to terminal 2026-07-25T16:16Z (slot 7)**: P0 fix CONFIRMED HELD for the VM's entire runtime — the
      run.log shows `Entity-scoped mode: restricting to FIXTURES only` + `0 entities = 0 calls queued` on every single
      date from 2020-06-06 through 2026-06-02 (incl. 2026-04-18, the exact original-bug reproduction date), and live
      quota only dropped ~37 calls in ~27min (vs. the pre-fix ~6900-calls-in-under-an-hour signature) — **no
      scope-escape recurrence anywhere in this run.** However the VM itself then **FAILED**:
      `DEPLOYMENT_FAILED     exit_code=137` (SIGKILL) at 16:14:34Z, backfill incomplete (~53 days short of the
      2026-07-25 end). Root-caused as NOT a scope-escape regression, NOT a SPOT preemption (both explicitly ruled out
      via audit log — the delete that followed was VM self-cleanup after the failure, caller IP = the VM's own; zero
      `PREEMPTED` marker; zero `compute.instances.preempted` events for this instance_id in the 24h window) — suspected
      but unconfirmed OOM (e2-standard-8; VM self-deleted before deeper memory metrics could be pulled). Full evidence +
      next-dispatch relaunch instructions (skip-if-fresh resumes from ~2026-06-02, escalate to a memory-tier bump if it
      repeats) in the freshness-preflight issue doc's own P1 todo — not duplicated here to keep this doc lean. Step 2
      (backfill) remains **incomplete**; step 3 (residual drop) still untouched pending step 2's actual completion.
- [x] ✅ [SCRIPT] P3. Add the same `START_DATE` clamp/warning to `launch-api-football-backfill-vm.sh` that
      `launch-sports-entity-sweep-vm.sh` already has per `/codex/02-data/sports-2020-06-data-floor.md`'s
      enforcement-surface list (item 6) — this launcher silently accepts a pre-2020-06-06 explicit start date with no
      warning (the venue-epoch skip gate is defense-in-depth, not a substitute for the launcher itself
      refusing/clamping). Found 2026-07-25 (slot 11) while launching `af-backfill-20260725-125405` after correcting the
      parent plan's own stale "2019→" range by hand; a future agent without that context could launch a genuinely
      pre-floor range unnoticed. (repo: deployment-service). **Done when**: the launcher clamps or loudly warns on a
      pre-2020-06-06 explicit `START_DATE`, matching its sibling. — `deployment-service@192d1f8`: the three sibling
      launchers named in the codex enforcement-surface list only clamp STRUCTURALLY (hardcoded per-entity/per-window
      start dates baked into their tables — no user-supplied date can go pre-floor), whereas this launcher's
      explicit-mode `<START_DATE> <END_DATE>` positional args are genuinely free-form; added a real runtime check right
      after the existing date-format sanity-check that REFUSES (`exit 1`, loud stderr citing the codex doc) any
      `START_DATE < 2020-06-06`, string-compared (ISO-8601 dates sort lexicographically, same pattern already used in
      `launch-tradfi-backfill-vm.sh`/`launch-cefi-sharded-backfill.sh`). Verified live via `--dry-run`: `2019-01-01`
      refused with the new error + exit 1; the exact boundary `2020-06-06` and a post-floor `2020-07-01` both pass
      through unchanged to VM-launch planning. `quality-gates.sh` green (98s, deployment-service).

## Codex SSOTs

No new durable contract — this executes Directive A/B from
`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`, already the SSOT for the selection rules
themselves.
