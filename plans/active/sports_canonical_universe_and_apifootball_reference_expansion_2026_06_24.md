---
title: Sports canonical universe + API-Football reference expansion (curate, don't over-capture)
parent_epic: sports_master
assigned_vm: human-planning
created: 2026-06-24
author: ikennaigboaka [slot-main·human-planning]
estimate_class: design
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 7.2
execution_scope: local-only
locked_by: live-defi-rollout
locked_since: 2026-06-24
---

# Sports canonical universe + API-Football reference expansion

> Captures the operator architecture spec (2026-06-24) after the over-capture diagnosis. Refine the existing codex /
> UAC / code rather than reinvent — this is mostly cleanup + consolidation of forms we already have through migrations.

## The diagnosis (root cause of the "low coverage / numeric keys / failures")
The sports `_index` (4.6M rows) is NOT a numeric-vs-canonical schema split — it's **out-of-universe over-capture**: the
date-wide API-Football adapter calls return the provider's entire **~1,200–2,400-league** universe, but our canonical
trading universe is **94 leagues** (`get_expected_leagues_for_source("api_football")`) / 101 (`LEAGUE_REGISTRY`).
**1,676,612 rows (36%)** are out-of-universe leagues. The "numeric/blank league_id" rows are just the api-football-path
slice of this cross-provider over-capture; the resolvable in-universe numerics (215,881) all have a canonical twin
(100% dedup). Numeric rows are STILL being written (live writer pollution) until the write-gate ships + VMs relaunch.

## Operator decision (2026-06-24): HYBRID — curated reference expansion, then drop residual
- **94 stays the TRADING/downstream universe.** All non-API-Football sources + trading services stay bounded to 94 (or
  less, per each source's eligibility). NOT expanding what we predict/trade.
- **Expand the API-Football *reference* universe** to a curated **~300 leagues** (budget-justified below) — the leagues
  + cups worth holding for reference/features/arb: the 94 + the division below each country + continental cups
  (Champions League, UEFA/UECL, Copa Libertadores/Sudamericana, AFC/CAF equivalents) + major internationals (World Cup,
  Euros, Copa America…). Reference-only; downstream derives nothing new from them unless explicitly promoted.
- **DROP the rows STILL outside the curated set after expansion** (not drop-vs-94) — the truly-junk leagues with no
  prediction/arb/reference value. Snapshot-first; `--drop-out-of-universe` retargeted to "outside curated".

## 6M-call budget (why ~300)
~6M API-Football calls available over the coming weeks (300k/day quota). Per-fixture enrichment dominates:
lineups+stats+events+player_stats ≈ 4 calls/fixture; top league-season ≈380 fixtures → ~1,900 calls/league-season;
2019→2025 ≈7 seasons → ~13k/league full history. 6M ÷ 13k ≈ **~450 leagues** for full enrichment — effectively more
(we already hold many fixtures; lower/cup leagues have few fixtures + often no enrichment → gated honest-empty, no
call). So ~300 curated is comfortable + value-appropriate; ~2,400 would burn the budget on enrichment-less junk.

## Architecture (canonical-everything; mostly cleanup of existing forms in UAC)
1. **Canonical league + cup registry (UAC SSOT)** — every league/cup has: human-readable canonical name, API-Football
   id, other-source ids, **is-league-vs-cup**, **country**, **season start/end per year**, **transfer window**
   (transfermarkt consumes it; we need it for refresh timing + ML training windows). Annual league-id changes
   (footystats / SFI rotate ids per season) → per-season id mapping in UAC.
2. **Per-source league eligibility (UAC SSOT)** — each source's coverage, bounded by API-Football existence (can't get a
   source for a league API-Football doesn't have): understat ~6; footystats/T-stats ~50 (subscription cap); odds-API
   ~20 (+ per-bookmaker-league restriction); SFI its subset; weather = fixture/venue-location-based (bounded by 94).
   Every source CHECKS canonical eligibility + converts canonical→its-query-id. Honest coverage MUST bake these caps in
   so we never mislabel `empty_confirmed` when a source legitimately doesn't cover a league.
3. **Canonical teams / players / fixtures** — API-Football id → human-readable canonical name + other-source mappings.
   Fixture = canonical fixture/event id (instrument-id-like) derived from teams; odds-API derives its pulls from it.
4. **Honest coverage** consumes (1)-(3): denominator = only-eligible (league × source × data_type) cells; everything
   else honest-absence/out-of-window. No mislabeled gaps.

## Execution sequence (phased; fastest-but-safe)
- [x] ✅ [INFRA] P0. Stop live sports deployments (not trading; over-capture pollution) — `mtds-live-sports-*` terminated 2026-06-24.
- [ ] [CODE] P0. **Write-gate to known/eligible leagues** (no random grab) — ship the universe-gate branch
  `instruments-service` `sports-canonical-league-1782283323`@e512713 (gate at the 3 capture-write loops) via a clean
  `quickmerge`, **initially to the 94** (fastest, fewest calls), then widen to the curated set. Rebuild tarball +
  relaunch so live writes stop polluting.
- [ ] [DATA] P0. **Clean + complete the 94-league golden window FIRST** — apply the in-universe canonicalize+dedup
  migration (215,881 numeric + 302,790 suffixed → canonical, collapse 509,227; in-universe numeric→0) in a
  consolidator-coordinated window (brief drain or coordinate; do NOT race the consolidator) + the GCS parquet
  numeric→canonical path-move + phantom-reconcile (the 770 INJURIES / 256 PLAYER_VALUES are path-mismatch phantoms, not
  re-fetches). Then API-Football fixtures (fast) → enrichment for the 94, fix broken, be thorough. Re-measure the
  94-denominator (expected to jump past 64.5%).
- [ ] [CODE] P1. **UAC canonical registry build/refine** — league/cup canonical + ids + is-cup + country + season
  start/end + transfer window; per-source eligibility maps + annual-id-change handling; team/player/fixture canonical +
  mappings. Wire honest-coverage to consume them.
- [ ] [DATA] P1. **Define the curated ~300-league reference set** (94 + below-division + continental cups + majors) +
  widen the write-gate to it.
- [ ] [DATA] P2. **Curated-universe backfill** (API-Football fixtures + enrichment, 2019→, burn ~6M over weeks; gated +
  honest-empty for no-enrichment leagues).
- [ ] [DATA] P2. **DROP residual out-of-curated rows** (snapshot-first) once the curated set is backfilled.
- [ ] [SCRIPT] P3. Delete superseded-buggy `instruments-service/scripts/backfill_fixture_lineups_blank_reason.py`
  (env-less bucket + direct google.cloud SDK).

## Codex SSOT updates
- `codex/02-data/sports-data-source-coverage-matrix.md` — the curated universe + per-source eligibility + caps.
- `codex/02-data/availability-manifest-and-data-status.md` — honest-coverage eligibility rules (per-source league caps).
- New: `codex/02-data/sports-canonical-league-cup-registry.md` — the canonical id/name/season/transfer-window SSOT.

## Operator verbatim directives (2026-06-24) — preserved in full (do NOT lose nuance to summary)

### Directive A — API-Football reference universe + canonical-everything + per-source eligibility
> essentially api football should have as many leagues including continental cups and world cup etc as it can that
> exist for football end of the day thats what exists - with canonical form for league and cup names. it should know
> whats a league and whats a cup i assume that's already there somewhere in leagues mappings/registry in UAC. Even
> though downstream we're not going to use a lot of them, it just allows us to add without always having to keep
> re-querying the API football. We have, like, twenty-something days' worth of 300k calls, so that's like 6 million
> calls to the API football. If you can work out roughly how many leagues and enrichment data we can realistically get
> from the API football with 6 million calls (since, whatever it is, 2019 is it?), then that will give us a good idea of
> how many leagues to include. Include the enrichment stats in that analysis so that we don't overcook it. Obviously, we
> already do have a bunch of fixtures in the API football, so it wouldn't be a full re-backfill. My guess is we can get
> to at least 90 something or 100, maybe even 200.
>
> as much league id mapping that can be done from this canonical to all the other data sources should happen in uac -
> where for some providers league ids change annually we should account for that. i think it was footystats or sfi that
> did that. that way we know all the other data sources can just check canonical league eligibility and convert to the
> query they need to get all the leagues for their data source that are eligible for them. The league to data source
> mapping eligibility, again, should be in UAC.
>
> For Understat, it's simple. We take all the leagues of Understat. We just know that all the leagues of Understat are
> way less than the leagues in API Football, so we're taking fewer leagues. I think it's six that are available. That's
> it. UAC guardrails that. For T-Stats [footystats], we have a hardcoded list of, I think, fifty leagues that we're able
> to use on our subscription because it caps out at fifty... it's around 50, and that's just the max we can do... the
> coverage needs to account for that. For weather, that's more on a fixture basis than league basis, so you can hold off
> on that for a sec. For soccer football info, I think there's a league availability... it should be cut down, and we
> can't be getting something from API Football [we don't have] — can't be trying to get soccer football info for a
> league that doesn't exist in API Football. Same with the odds API, which I think covers twenty leagues also for
> football... that's again just a hard rule.
>
> Everything else with respect to fixtures, teams, players, etc., follows the same concept — it filters from the top and
> it's based on what's actually available. There is this concept of prediction leagues, [and] features leagues. Given
> that we need ultimately odds for a prediction, we pretty much narrow down our prediction leagues to the ones that the
> odds API has data for. The concept of features leagues was just to understand the context around a particular league,
> so cups that might have been played around that league... what teams were relegated/promoted, history in other
> leagues. We try to get the leagues above and beyond... a wider universe of leagues around just the ones we have: world
> cups, euros, champions league, uefa, and the equivalents all over the world, as well as the league above and below the
> leagues we care about. Usually not much above (we take the top league + below for each country), but the one below
> that the odds API has data for is supposed to be included so we have a few extra leagues. That's how we get to an API
> Football baseline. There is a reason to have even more API Football — for arbitrage and things live, where we might
> not have the odds API data but try to pull live odds. Not a primary concern; we can always add leagues.
>
> leagues need info like which country they are in and the season start and end date each year and the transfer window —
> this should be canonical as transfermarket uses it to understand when transfer season is. We need it to understand
> when we need to refresh certain information about those leagues over their seasons. We'll need it to understand
> training windows for our machine learning.
>
> then we need to know which teams are in a league - again, there's canonical and there's matching/conversion. API
> Football gives us canonical in API Football ID, but we have converted that into human-readable canonical team names.
> For all the other data sources, team info we derive from the canonical. We have the mappings.
>
> then for fixtures - API Football gives basic fixture info (kickoff, who's playing, home, away). Since we have the
> teams, we derive the human-readable canonical fixture ID format (almost an instrument/event/fixture ID — canonical),
> and from there the Odds API works out which odds it can pull for those fixtures for the leagues it concerns. The Odds
> API has an extra restriction — certain bookmakers don't cover certain leagues, so there's a bookmaker-league
> restriction. All supposed to be baked into honest coverage so we don't keep assuming we don't have data when we do.

### Directive B — curate (not 2.4k), hybrid drop, drop live, cleanup posture
> i think where i'm at is that 1.2-2.4k leagues is way too much, but since we have 6m api football calls i wanna use
> them so figure out what interesting leagues for prediction and arb we can get for reach this cap over the coming
> weeks. The nice thing is, in the meantime, it doesn't change the fact that 96 [94] remains the universe that other
> data sources care about, or the rest of our services. I'm not suggesting we increase the scope of what we are
> predicting now. I'm suggesting we just, for reference, have a wider universe. As long as our honest coverage,
> denominators, numerators, manifest are set up properly, it doesn't matter — they're just going to expect to be
> deriving from those leagues and the fixtures that come from them. We will need leagues and fixtures... it's not just
> fixtures; basically all the API football enrichment stats around those leagues need to be covered — that's the basic
> starting point, reference information. When it comes to footy stats, soccer football info, understat, weather (mostly
> location-based once we know the home team), that's bounded by the 94 universe. API football would just be more
> exhaustive, burning the 6m credits for its coverage, so they only expect what they expect given all the rules above.
> You don't need to reinvent the wheel. We got a lot of documentation around this already, but you might need to refine
> it in the docs and in the code — codex, PM plans, the code itself, UAC. Let's finally get to the point where we don't
> need to do this as much. I don't know if it costs less API credits to get API football just for 94 leagues fixtures
> rather than more fixtures. If so, then just start with the 94. You've been doing 2.5k+, hence burning a lot of API
> calls. Get the golden window down. If the golden window is not already done, then get API football going for the rest
> for those 94 leagues. Fixtures should be fairly quick, then get the enrichment stats going for the 94 leagues, fix any
> broken... Be thorough. See if [it's] your call/query star and get order mappings in shape so that when things are
> working off those 94 leagues and their own rules (which make it less than 94, like odds API is much less), we're not
> badly labelling it empty confirmed. We are checking that we have good name mappings: leagues, fixtures, players, teams
> — everything should have canonical forms (yes, the API football ID as well as the other data source IDs) — and
> human-readable makes merging/mapping much easier. You have most of the data, it's just been through migrations,
> different canonical forms, different universe denominators over different iterations. A lot of it is just cleanup. We
> can drop live deployments for sports (not trading anything) whilst we fix the bad-data dumping, and migrate them so
> even live we stick to our known league universe — we should know a league we pull from rather than randomly grabbing
> and hoping the code knows about it. (Branding our leagues, tracking/identifiers, and making sure we have the relevant
> info around them in the registry, for use of that 6 million credits if we go to like 2 or 3 or 400 leagues.)

### Directive C — hybrid drop
> so its hybrid we would drop the ones that are left out of universe after universe expansion outside the 94 (api
> football only expansion as mentioned and just to burn those 6m credits)

## Progress Log
- **2026-06-24** — Operator architecture spec (Directives A/B/C above) preserved verbatim; plan registered in
  `sports_master` epic (related_plans + workstream-routing row). PM LDR `9ca66844c`.
- **2026-06-24 — LIVE SPORTS DEPLOYMENTS DROPPED (operator-authorized, Directive B "drop live deployments for sports
  whilst we fix the bad-data dumping").** Deleted the three running un-gated wide-universe writers
  (`instr-backfill-sports-odds-20260623-150204`, `instr-backfill-sports-predictions-20260623-150151`,
  `sports-scheduler-20260624-010804`) and **PAUSED** the recurring crons that relaunch them:
  `uts-prod-sports-scheduler-cron` (`*/5` live poller) + `uts-prod-sports-fixtures-noon-t1-schedule` (12:00 UTC). These
  wrote out-of-universe/numeric rows (the over-capture) + burned the 6M API-Football budget on the full ~2,400-league
  provider universe. They stay paused until the write-gate ships (see Temporary states).

## Temporary states + their canonical follow-up
- **PAUSED sports crons** (`uts-prod-sports-scheduler-cron`, `uts-prod-sports-fixtures-noon-t1-schedule`) — **named
  re-enable gate**: re-enable ONLY after (1) the write-gate branch `sports-canonical-league-1782283323`@e512713
  (`_is_in_canonical_write_universe()` + always-canonical `league_id`) ships via clean quickmerge, AND (2) the VM tarball
  is rebuilt from clean LDR (`create-code-tarballs.sh`) so relaunched VMs carry the gate. Re-enable with
  `gcloud scheduler jobs resume <job> --location=asia-northeast1`. Tracked by this plan's Execution sequence Phase 1.
