---
doc_type: issue
title:
  sports league_id namespace — canonicalise-at-write SHIPPED; 214,842 historical rows still raw, 75,432 of them on an
  ambiguous name
summary: >-
  The sports manifest stored raw api-football display names as league_id (PREMIER_LEAGUE, 2._BUNDESLIGA) while every
  consumer keys on the canonical LEAGUE_REGISTRY slug (EPL, BUNDESLIGA_2) — 214,842 rows joined to nothing. Operator
  chose canonicalise-at-write (2026-07-20); shipped in mtds@ad4f1872 resolving by NUMERIC api_football_id. Measurement
  proved that choice necessary: six raw names are ambiguous and a name-keyed alias map would MERGE distinct leagues
  (SERIE_A = Italian + Brasileirao). History is NOT yet migrated — the manifest carries no numeric id, but the
  underlying parquet carries home_team/away_team, which resolves every sampled collision.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [sports, canonical, league-id, namespace, manifest, coverage, migration]
related:
  [
    ../sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_consolidated_audit_2026_07_19.md,
    /plans/archive/issues/sports_curated_universe_domestic_selection_remaining_2026_07_25.md,
  ]
created: "2026-07-20"
author: unknown
source: operator decision 2026-07-20 (canonicalise at the write path)
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-data-processing-service/scripts/reprocess_sports_odds.py,
    market-tick-data-service/scripts/sports/league_id_relocation/census_footystats_orphan_content_2026_07_25.py,
    market-data-processing-service/market_data_processing_service/app/core/orchestration_scanner.py,
    deployment-service/scripts/rebuild_sports_manifest.py,
  ]
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# sports `league_id` namespace — write path canonical, history still raw

## The defect

The availability manifest stored the RAW api-football display name as `league_id`, produced by `OddsApiAdapter` as
`league_cls.name.upper().replace(" ", "_")` — `PREMIER_LEAGUE`, `PRIMERA_DIVISION`, `2._BUNDESLIGA`, `FIRST_DIVISION_A`.
Every consumer keys on the canonical `LEAGUE_REGISTRY` slug — `EPL`, `ARGENTINA_PRIMERA`, `BUNDESLIGA_2`, `JUPILER_PRO`
— so those rows **joined to nothing**: absent from the coverage denominator, invisible to the gates, mis-bucketed in the
data-status UI.

Measured in the live sports manifest (1,974,679 rows): **214,842 rows carry a non-canonical `league_id`** across 60
distinct values. Top offenders: `CHAMPIONSHIP` 27,887 · `PREMIER_LEAGUE` 27,761 · `PRIMERA_DIVISION` 26,587 ·
`FIRST_DIVISION_A` 23,745 · `2._BUNDESLIGA` 22,127 · `SUPER_LEAGUE` 20,958 · `SUPERLIGA` 20,168 · `PREMIERSHIP` 16,404.

## Why canonicalise-at-write, not an alias map (the measurement that decided it)

Six raw display names are **genuinely ambiguous** — one name, two real leagues:

| raw name           | resolves to                                  |
| ------------------ | -------------------------------------------- |
| `BUNDESLIGA`       | `BUNDESLIGA` + `AUSTRIAN_BUNDESLIGA`         |
| `SERIE_A`          | `SERIE_A` + `BRASILEIRAO`                    |
| `SERIE_B`          | `SERIE_B` + `BRASILEIRAO_SERIE_B`            |
| `CHAMPIONSHIP`     | `ENG_CHAMPIONSHIP` + `SCOTTISH_CHAMPIONSHIP` |
| `PRIMERA_DIVISION` | `ARGENTINA_PRIMERA` + `CHILE_PRIMERA`        |
| `SUPER_LEAGUE`     | `GREEK_SUPER_LEAGUE` + `SWISS_SUPER_LEAGUE`  |

**A name-keyed alias map cannot resolve these — it would silently MERGE distinct leagues** (Italian Serie A with the
Brasileirão). Only the numeric `api_football_id` separates them, and that id is in hand at write time. This is the
concrete justification for the operator's choice.

## What shipped (write path — DONE)

`market-tick-data-service@ad4f1872`. `_canonical_league_id()` resolves via `get_league_by_api_football_id()`:

- **All 30 write-path prediction leagues resolve; 0 unresolved.** 13 of 30 change value.
- Unresolvable id → falls back to the raw name, so an unregistered league still captures (honest absence) rather than
  aborting the fetch loop.
- The `--leagues` filter now accepts BOTH the raw and canonical form. Without that, every existing launcher/runbook
  invocation (which passes the old raw name) would have silently fetched nothing — a change that fails closed and
  quietly.
- 3 regression tests, including one asserting the six collisions resolve to DISTINCT slugs (i.e. that the numeric id
  genuinely separated them rather than collapsing them).

## What remains: the historical migration

**The manifest has no numeric id.** Its only other provenance column is `venue` (a bookmaker: `ODDS_API`, `SKYBET`,
`BETVICTOR`), which cannot identify a league. So for the **75,432 rows sitting on an ambiguous name**, the manifest
alone is insufficient.

**But the underlying parquet resolves it.** `fixture_id` is empty and `sport_key` is only the display name, however
`home_team` / `away_team` ARE populated, and colliding leagues have disjoint squads. Sampled 2026-07-20:

| raw `league_id`    | teams found in the shard                                       | unambiguous league   |
| ------------------ | -------------------------------------------------------------- | -------------------- |
| `CHAMPIONSHIP`     | Barnsley, Birmingham City, Blackburn Rovers, Brentford, Fulham | `ENG_CHAMPIONSHIP`   |
| `PRIMERA_DIVISION` | Argentinos Juniors, San Lorenzo, Vélez Sarsfield, Huracán      | `ARGENTINA_PRIMERA`  |
| `SUPER_LEAGUE`     | BSC Young Boys, FC Zürich                                      | `SWISS_SUPER_LEAGUE` |

**Proposed migration** (not yet executed):

1. For the 139,410 UNAMBIGUOUS non-canonical rows, map raw name → canonical slug directly (a name-keyed map is safe
   precisely because those names have exactly one referent).
2. For the 75,432 AMBIGUOUS rows, resolve per `(day, league_id, venue)` shard by reading the parquet's team set and
   matching it against the reference team registry for each candidate league. Require a decisive majority match; leave
   unresolved shards UNTOUCHED and log them (never guess).
3. Snapshot the manifest before any write; the same `_index/snapshots/` mechanism already in use.
4. **GCS path exposure** — `league_id=` is a live Hive partition segment in the raw-tick bucket
   (`.../venue={BM}/league_id={L}/...`) and transitively in the MDPS `processed/` derivation. Canonicalising the
   manifest without relocating the objects would desynchronise path and manifest, so the migration is a **relocation**,
   not a manifest rewrite. Size the object count before committing to an approach.

## Related surface not covered by the shipped fix

The instruments-service per-fixture path (`sports_reference_fixtures.py:224-229`) has an independent instance of the
same defect: the `fx.league.league_id` branch always wins over the numeric-id `elif`, making the id-based resolution
dead code, and `build_league_id()` falls back to a bare slug when `country` is empty. Live evidence of leakage already
on disk: `.../entity=injuries/league=235/` — a bare numeric id sitting as a real partition value. Needs the same
treatment.

## Consumer-breakage survey (2026-07-20) — three design constraints + one live pre-existing bug

A read-only consumer sweep (one agent; the adversarial verifier did not complete — findings below are marked CONFIRMED
where I independently re-measured, REPORTED where they rest on the agent's cited file:line + the codebase's own
comments). These change the migration design, so they gate execution even though the operator has signed off on the
relocation in principle.

**Constraint 1 — the relocation MUST delete the old raw-keyed manifest rows, not just add canonical ones (CONFIRMED).**
The live manifest consolidator dedups on a key that INCLUDES `league_id`
(`unified-trading-library/.../manifest_consolidator.py:525`). Writing canonical-keyed rows via the normal shard path
without removing the old raw-keyed rows makes the consolidator treat old-raw and new-canonical as two distinct groups →
the same shard is **double-counted** in `_index/availability_index.parquet`. The codebase already documents this exact
failure mode: `deployment-service/scripts/rebuild_sports_manifest.py:200-201` — _"Without this, old non-canonical
league_id values persist alongside new canonical ones because the ManifestWriter dedup key includes league_id."_ So the
migration must rewrite-in-place (delete-old + write-new atomically per shard), and reuse that script's
`_clean_stale_league_entries` rather than reinventing it.

**Constraint 2 — a path-only relocation is insufficient; the `league_id` COLUMN inside the parquet must move too
(CONFIRMED).** MDPS derives its OWN output partition from `df["league_id"][0]` — the row-CONTENT column of the raw
ticks, not the GCS path segment (`market-data-processing-service/.../canonical_writer_shaping.py:467`
`_infer_league_id`). So if we `gcs_copy_object` to a canonical path but leave the parquet's `league_id` column raw, MDPS
re-derivation keeps emitting processed output under the OLD raw partition. The relocation must rewrite the content
column, and any already -materialised MDPS `bucketed.parquet` for historical days needs MDPS reprocessing (it is not
touched by an MTDS-only move).

**Constraint 3 — combine with the K1 casing migration (CONFIRMED — same object path).** `league_id=`,
`instrument_type=odds`, and `data_type=trades` are all segments of the SAME ~2M objects. Doing casing and league_id as
separate relocations copies the same objects twice. One combined relocation to the final canonical target halves the
copy and the exposure window. (Cross-ref the K1 ordering correction in the closeout plan: the MDPS scanner's exact
substring match means a dual-accept read must ship BEFORE any of these segments flip.)

**LIVE PRE-EXISTING BUG (independent of the relocation) — coverage gate misclassifies every canonical league (CONFIRMED
by my own measurement).** The sports v2 sentinel calls `is_bookmaker_league_covered(bm, _canon_lid)` with a CANONICAL
league id (`market-tick-data-service/.../sentinels.py:319`), but the coverage registry `BOOKMAKER_LEAGUE_COVERAGE`
(`unified-api-contracts/.../registry/sports_bookmaker_league_coverage.py`) is keyed on RAW display names. Measured
directly: `EPL in values == False`, `PREMIER_LEAGUE in values == True`, and
`is_bookmaker_league_covered("BETFAIR_EX_EU", "EPL") == False` while `…("BETFAIR_EX_EU", "PREMIER_LEAGUE") == True`. So
**every not-yet-captured (bookmaker, canonical-league, fixture) shard on the LIVE write path is currently mis-stamped
`EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE`** instead of surfacing as a real gap — a standing false-negative in coverage
reporting TODAY. The fix is to canonicalise that registry (re-run
`refresh_sports_bookmaker_league_coverage_2026_06_21.py` AFTER the manifest is canonical, or regenerate the JSON from
`ODDS_API_DISPLAY_TO_CANONICAL` now). Filed as its own follow-up todo in the closeout plan.

**Ambiguity gap in the existing name→canonical table** — `ODDS_API_DISPLAY_TO_CANONICAL`
(`unified-api-contracts/.../provider_league_ids.py:655-697`) has **no entry for `FIRST_DIVISION_A`** (23,745 rows) and
resolves `Championship`/`Super League` unconditionally to ONE side (English/Swiss), and relies on accent
(`Primera Division` vs `Primera División`) to split Argentina/Chile — a signal the manifest's `upper().replace(" ","_")`
DESTROYS. This corroborates the team-name disambiguation path as the only reliable route for the ambiguous set, and
means the name→canonical table CANNOT be trusted for the six collisions.

Evidence: `scratchpad/ns_coverage.py`, `scratchpad/collisions.py`, `scratchpad/hist_disambig.py`,
`scratchpad/parquet_provenance.py`, `scratchpad/team_disambig.py`; consumer sweep
`subagents/workflows/wf_664f7ed4-df6/journal.jsonl` (2026-07-20).

## VERIFIED EXECUTION PLAN — 9-agent adversarial workflow (2026-07-20)

> Produced by a 4-survey / 4-verify / 1-synthesis workflow (1.7M tokens; verifiers independently re-measured every claim
> and OVERRODE the surveyors in several material places, noted inline). Full transcript:
> `subagents/workflows/wf_664f7ed4-df6/journal.jsonl`. This SUPERSEDES the "Proposed migration" sketch above.

### Material corrections this workflow made to the earlier sketch

1. **`sport_key` is the PRIMARY disambiguation route, not team-roster matching.** The tick parquet carries a
   100%-populated `sport_key` country-qualified label (`"Serie A - Italy"` vs `"Brazil Série A"`, `"Bundesliga
   - Germany"`vs`"Austrian Football
     Bundesliga"`, etc.) that cleanly splits 4 of the 6 collisions with ZERO fuzzy matching. Team-roster matching is the FALLBACK only. Do NOT build fuzzy matching where `sport_key`
     already answers.
2. **CHAMPIONSHIP and SERIE_B are effectively single-league in the observed data.** A venue-stratified re-walk over
   148 + 1,263 shards plus a whole-bucket distinct-value grep (76 raw values) found NO Scottish- or
   Brazilian-B-flavoured value anywhere. Those two collisions are almost certainly not real in the data — but keep a
   per-shard `sport_key` tripwire rather than asserting it blind.
3. **Constraint-2 function name CORRECTED**: MDPS derives its output partition from `reprocess_sports_odds.py:454`
   `groupby(["league_id","horizon_name"])`, NOT `canonical_writer_shaping.py:467 _infer_league_id` (a different candle
   path). The content-not-path conclusion stands; the exact site was wrong.
4. **Two peripheral buckets are contaminated with a DIFFERENT vocabulary from an untraced writer** —
   `features-sports-prd` (30 objects) + `instruments-store-sports-prd` (9,733 objects) carry `ENGLAND_PREMIER_LEAGUE` /
   `LA_LIGA_2` / `UNKNOWN`. They must NOT be folded into this relocation. Filed separately:
   `sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`.

## 1. Verdict: GO-WITH-CAVEATS

**The disambiguation data needed to resolve the 6 ambiguous names EXISTS, so no subset is data-blocked.** The tick
parquet carries a `sport_key` column (100%-populated in every sampled shard, both schema variants) that is a
country-qualified league label and cleanly bifurcates 4 of the 6 collisions on its own (`"Bundesliga - Germany"` vs
`"Austrian Football Bundesliga"`, `"Serie A - Italy"` vs `"Brazil Série A"`, `"Primera División - Argentina"` vs
`"…- Chile"`, `"Swiss Superleague"` vs `"Super League - Greece"`) — with **zero** team-name fuzzy-matching required. As
a fallback, the `entity=teams` roster exists in GCS for all 12 candidate leagues (verifier confirmed all 12 dirs present
at `day=2026-07-15`), with disjoint squads. This is a material correction I am carrying forward from the disambiguation
verifier: the issue-doc/closeout plan propose team-set roster matching as the primary route; **the verifier proved
`sport_key` is the primary route and roster-matching is only the fallback** — do not build fuzzy matching where
`sport_key` already answers.

**Executable now:**

- **Unambiguous set** — 139,410 manifest rows / 64,100 raw-shape objects: GO via a completed name-map.
- **4 of 6 ambiguous names** (BUNDESLIGA, SERIE_A, PRIMERA_DIVISION, SUPER_LEAGUE): GO — split per-shard by `sport_key`;
  both sides genuinely occur (Austrian variant in 38/69 BUNDESLIGA shards, Brazilian in ~11 SERIE_A shards —
  verifier-measured).
- **CHAMPIONSHIP and SERIE_B**: GO, but treat as **effectively single-league in the observed data** (→
  `ENG_CHAMPIONSHIP` and Italian `SERIE_B`). The disambiguation verifier attacked this negative result hardest — found
  and corrected a real lexicographic sampling bias in the surveyor's method, re-ran venue-stratified across 148 shards +
  1,263 `batch_footystats` shards, and grepped the entire-bucket distinct-value list (76 raw values, all history): **no
  Scottish- or Brazilian-B-flavoured value exists anywhere, even under the correct canonical spelling.** So these two
  collisions are almost certainly not real in the data — but keep a per-shard `sport_key` tripwire (STOP conditions §5)
  rather than asserting it blind.

**Not part of this GO (explicitly deferred, not silently dropped):** two peripheral buckets the gcs-sizing _verifier_
proved contaminated after the _surveyor_ wrongly cleared them from 2-3-date spot checks — `features-sports-prd` (30
objects, ~1.9 MB) and `instruments-store-sports-prd` (9,733 objects, ~0.75% of bucket). These carry a **different
non-canonical vocabulary** (`ENGLAND_PREMIER_LEAGUE`, `LA_LIGA_2`, `UNKNOWN`) from a different/untraced writer — root
cause UNVERIFIED. They must not be folded into this relocation; file them as separate findings with the corrected counts
below.

---

## 2. Measured scope (verifier-confirmed exact unless noted)

**Bucket:** `market-data-tick-sports-prd-central-element-323112` — raw ticks **and** MDPS `processed/` output live in
the same bucket (confirmed; `market-data-candles-sports-…` / `market-data-processed-sports-…` do not exist).

Three contaminated path shapes, **true scope** (includes the hidden BUNDESLIGA/SERIE_A/SERIE_B that a naive "not in
`LEAGUE_REGISTRY`" test wrongly buckets as canonical — they are string-identical to real keys but ambiguous):

| Shape                                                                                                               |     Objects |             Bytes |      GiB |
| ------------------------------------------------------------------------------------------------------------------- | ----------: | ----------------: | -------: |
| raw `league_id=` (`pipeline_mode=batch_odds_api`)                                                                   |     139,155 |     2,249,709,561 |     2.10 |
| processed `league_id=` (MDPS `odds_horizon_bucket`, both legacy + `batch_mdps_…`)                                   |     110,023 |     2,237,189,667 |     2.08 |
| raw `league=` (`pipeline_mode=batch_footystats`, note key is `league=`, venue=`ODDS_API`, `instrument_type=` empty) |       7,776 |       409,889,527 |     0.38 |
| **TOTAL relocation scope**                                                                                          | **256,954** | **4,896,788,755** | **4.56** |

**The sizing driver is object count (~257K small objects, avg ~19 KB), not volume** — 4.56 GiB copies trivially;
per-object copy/rewrite API overhead is the cost.

Within the raw `league_id=` shape (139,155 objects):

- **Unambiguous: 64,100 objects** → name-map.
- **Ambiguous (6 names): 75,055 objects / 1.14 GiB** → `sport_key` split. Breakdown: SERIE_A 18,981 · CHAMPIONSHIP
  12,920 · PRIMERA_DIVISION 11,555 · BUNDESLIGA 11,257 · SERIE_B 10,541 · SUPER_LEAGUE 9,801. This is within 0.5% of the
  context's 75,432 ambiguous manifest rows — cross-validation, not a contradiction.

**Manifest rows (context, treated as established fact):** 214,842 non-canonical (139,410 unambiguous + 75,432 ambiguous)
across 60 distinct values. Object count ≠ manifest row count — the manifest spans both `trades` and
`odds_horizon_bucket` data_types (e.g. `CHAMPIONSHIP` = 35,738 manifest rows = 28,952 `trades` + 6,786
`odds_horizon_bucket`). Sports manifest is `_index/availability_index.parquet`, 5,377,883 rows, **42 columns** (verifier
corrected surveyor's 41).

**Two unreconciled deltas — stated, not smoothed:** (a) GCS gives **59** distinct non-canonical values, manifest **60**
— this is a GCS-object-state vs manifest-state gap that neither surveyor nor verifier could resolve from a GCS-only read
path; (b) I have no manifest-DB read path in this session, so the 214,842 / 139,410 / 75,432 manifest figures are
inherited from context, not independently re-measured here.

**Deferred out-of-scope contamination (verifier-found, different axis):** `features-sports-prd` 30 objects
(`ENGLAND_PREMIER_LEAGUE` 16, `BRAZIL_SERIE_A` 2, `ARGENTINA_PRIMERA_NACIONAL` 12, contamination ongoing to 2026-07-11);
`instruments-store-sports-prd` 9,733 objects / 172 distinct values across 6 pipeline_modes. Also a benign measurement
fix: `batch_footystats` no-league count is **1,814 not 1,822** (arithmetic reconciles exactly to the 284,569
`raw_tick_data/` total only at 1,814).

---

## 3. Ordered procedure (reuses the established relocation/delete-safety protocol — nothing invented)

Governing SSOT: `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (five-part proof, COPY-not-MOVE, disposition
vocabulary, human-only hard stops). Order is **COPY → content-verify → manifest-swap → human-gated delete. Never
manifest-first, never delete-first.** Every step before the final delete is reversible; the final delete is the single
irreversible operation and is human-gated.

**STEP 0 — Pre-migration drain (verify: VMs stopped both clouds).** Stop all sports VMs on GCP + AWS, run the manifest
consolidator, snapshot the manifest to `_index/snapshots/`. Per delete-safety §5 + vm-launcher-runbook. The live write
path is already canonical (`mtds@ad4f1872`), so this only prevents a concurrent writer racing the migration.
_Verification:_ `kill -0`/fleet check shows zero running sports writers; snapshot object exists and is restorable.

**STEP 1 — Ship dual-accept readers FIRST (code; BEFORE any object moves).** Extend the DeFi-DEX dual-accept pattern
already in the codebase (`_DEFI_DEX_DATA_TYPE_ONDISK_SEGMENTS`, MDPS
`market_data_processing_service/app/core/orchestration_scanner.py:102`) to sports `league_id` **and** the K1 casing
segments, so a scanner matching `orchestration_scanner.py:248` (`f"data_type={data_type}/" in blob_name`, exact
case-sensitive substring — this is why a naked flip is a silent-zero-rows outage) accepts BOTH `league_id=CHAMPIONSHIP`
and `league_id=ENG_CHAMPIONSHIP`, both `trades`+`TRADES`, `odds`+`ODDS`. _(Repo-name correction from the mdps verifier:
this scanner is in market-data-processing-service, NOT market-tick-data-service.)_ features-service `gcs_reader.py`
lists by date-prefix only and is immune — no change there. _Verification:_ unit test that a canonical request matches
both on-disk forms; the prior fail-closed class (the `--leagues` filter in `ad4f1872`) is the precedent this prevents.

**STEP 2 — Complete + validate the unambiguous name-map (code/data; BEFORE moves).** `ODDS_API_DISPLAY_TO_CANONICAL`
(`unified-api-contracts/.../provider_league_ids.py:655-697`) has **no entry for `FIRST_DIVISION_A`** (~10,725 objects /
23,745 manifest rows — a large unambiguous group) and one-sidedly resolves the collisions — so it **must not be trusted
for the 6 ambiguous names**. Complete it for every unambiguous distinct value. _Verification:_ assert every one of the
59/60 distinct non-canonical values minus the 6 collisions has exactly one canonical target;
`FIRST_DIVISION_A → JUPILER_PRO` present.

**STEP 3 — Resolve each shard's canonical target (read-only classification).** Per `(day, venue, raw_league_id)` shard:
unambiguous → name-map (Step 2). Ambiguous → read parquet `sport_key` → canonical slug (splits 4 of 6).
CHAMPIONSHIP/SERIE_B → majority side, asserting `sport_key` is the single expected value; if a shard's `sport_key` is
the minority side, route it there. Where `sport_key` is absent/undecided → fallback team-set match against the
`entity=teams` roster **nearest the shard's own date** (rosters drift with promotion/relegation — verifier confirmed FC
Vaduz present 2021-05-11, absent 2022-01-15). **Any shard not resolving to one candidate by a decisive majority → leave
UNTOUCHED, log, never guess.** _Verification:_ per-shard decision log (`sport_key`→slug or team-vote→slug); explicit
untouched list.

**STEP 4 — COPY to the combined canonical target (reversible).** Per Constraint 3, do `league_id` + K1 casing in ONE
copy (avoids copying the same ~257K objects twice): `gcs_copy_object` (server-side, no egress) to
`.../league_id={CANON}/instrument_type=ODDS/data_type=TRADES/ticks.parquet`, **and rewrite the parquet's `league_id`
CONTENT column** to the canonical value. Content rewrite is mandatory (Constraint 2): MDPS derives its output partition
from the row content (`reprocess_sports_odds.py:454` `groupby(["league_id","horizon_name"])` — mdps-verifier correction:
NOT `canonical_writer_shaping.py:467 _infer_league_id`, which is a different candle path; the qualitative "content not
path" conclusion is confirmed). Shape precedent: `migrate_sports_league_partition.py` (write-then-delete, never
reverse). _Verification:_ `gcs_describe_object(twin_uri)` returns `BlobMetadata` (five-part-proof Part 1); read copy's
`league_id` column == canonical. _Reversible:_ old object untouched; delete the copy to revert.

**STEP 5 — Content-verify (reversible gate).** Row-key intersection source∩copy, **not** object count/existence
(five-part-proof Part 2 — the R5 precedent: paths looked duplicated, content was 32 high-TVL pools short; a blind delete
would have destroyed them). _Verification:_ intersection == 100% of source row-keys.

**STEP 6 — Atomic manifest swap (reversible via snapshot).** Delete the old raw-keyed rows AND write the canonical-keyed
rows **in the same pass**, reusing `deployment-service/scripts/rebuild_sports_manifest.py::_clean_stale_league_entries`
(Constraint 1 — the consolidator dedups on a key that **includes** `league_id`,
`unified-trading-library/.../manifest_consolidator.py:525`; an additive write makes old-raw and new-canonical two dedup
groups → the shard **double-counts** in `availability_index.parquet`). This is the load-bearing constraint the consumers
_surveyor missed and the verifier flagged_ as a material omission. _Verification:_ post-swap reconcile shows zero
`league_id=<RAW>` manifest rows for migrated shards and no row-count inflation from the consolidator; snapshot
restorable. _Reversible:_ restore `_index/snapshots/`.

**STEP 7 — Regenerate the processed surface via MDPS reprocess (AFTER raw is canonical).** Do NOT blind-copy the 110,023
`processed/` objects — instead re-run `market-data-processing-service/scripts/reprocess_sports_odds.py` for the
historical days; now that the raw content column is canonical, MDPS emits `bucketed.parquet` under the canonical
`league_id=` partition. **DURING-window hazard (flagged explicitly):** features-service `read_bucketed_odds` lists by
date-prefix and concatenates _every_ `bucketed.parquet` it finds — so if old-raw and new-canonical processed objects
coexist for a day, features double-counts. Mitigate by doing processed reprocess+stale-delete inside the drained window
per day, not as a slow background copy. _Verification:_ processed objects present under canonical partition; a features
read for a migrated day returns a single (non-doubled) row set.

**STEP 8 — Refresh the coverage registry (AFTER manifest canonical).** Re-run
`refresh_sports_bookmaker_league_coverage_2026_06_21.py` to regenerate `sports_bookmaker_league_coverage.json`
canonically — fixing the standing LIVE bug (below). _Verification:_ `is_bookmaker_league_covered("BETFAIR_EX_EU","EPL")`
flips `False → True`.

**STEP 9 — Human-gated delete of the old objects (irreversible; HUMAN-ONLY HARD STOP).** Only after Steps 4-6
twin-confirm per shape: emit the five-part-proof checklist (twin URI probed, content result, writer grep+READ, reader
grep+READ, twin-coverage %); the agent **suggests** with disposition `yes-twin-confirmed`; **a human executes**
`gcs_delete_object`. Any prod-bucket delete is a delete-safety §3 hard stop — no confidence level authorizes an
autonomous prod delete.

---

## 4. Consumer-breakage list (with land-order)

**BEFORE the flip (must ship first, or silent-zero / wrong-target):**

- **MDPS dual-accept scanner** (`orchestration_scanner.py`, in market-data-processing-service) — exact case-sensitive
  substring match; a naked flip reads ZERO sports ticks and reports success. BEFORE.
- **`ODDS_API_DISPLAY_TO_CANONICAL` completion** (add `FIRST_DIVISION_A`; do not trust for the 6 collisions). BEFORE.

**DURING the per-shard relocation:**

- **Parquet `league_id` content-column rewrite** (raw ticks) — Constraint 2; MDPS reads content not path.
- **Atomic manifest delete-old+write-new** via `_clean_stale_league_entries` — Constraint 1; consolidator double-count.

**AFTER (regenerate once the manifest/raw is canonical):**

- **MDPS `reprocess_sports_odds.py`** — regenerates the 110,023 processed objects canonically (with the features
  double-count hazard mitigated in-window).
- **`sports_bookmaker_league_coverage.json` refresh** — fixes the **LIVE standing bug** (independent of, but resolved
  by, this migration): sports v2 sentinel calls `is_bookmaker_league_covered(bm, _canon_lid)` with a canonical id
  (`market-tick-data-service/.../sentinels.py:319`) against a raw-keyed registry → the committed JSON is measured **27
  bookmakers / 51 tokens / 0 canonical slugs**, so every not-yet-captured (bookmaker, canonical-league) cell is
  currently mis-stamped `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE` — a standing coverage false-negative today.
- **`enumerate_expected_universe.py` coverage denominator** — recovers automatically once captured `league_id` is
  canonical (it joins the manifest set against the canonical catalogue). AFTER; no code change.
- **`classify_sports_empty_reason`** (`canonical_writer_manifest.py:217`) — recovers once content column is canonical
  (it reads content, degrades to `SOURCE_RETURNED_ZERO` on raw).

**Structurally immune / no change:** path-regex parsers (`league_id=(?P<…>[^/]+)` captures any string —
`audit_legacy_paths.py`, `reconcile_market_tick_manifest.py`, `merge_migrated_odds…`); features-service `gcs_reader.py`
(date-prefix listing); UI pass-through fields (`use-sports-live-updates.ts`, `HierarchicalShardDrilldown.tsx`).

**Dormant (not live today — do not be misled into thinking they gate this):** `check_shard_freshness(league_id=…)` —
grepped, zero call sites pass `league_id`; `check_calculator_coverage` in features `coverage_gate.py` — **verifier
correction: the surveyor's `should_run_calculator` name does not exist anywhere**; the real function's two call sites
never pass `league_id`, so its league branch is dead, i.e. "compliant because unexercised," not "compliant because
correct."

**Must NOT be blind-re-run:** the ~95 dated instruments-service one-off scripts referencing `league_id` (surveyor said
"~15+"; verifier counted 95) — several assume the specific migration state they were written for; each needs per-script
review before any re-run.

---

## 5. STOP conditions (abort/escalate if observed mid-run)

1. **Undecidable-shard rate spikes** — if shards where neither `sport_key` nor team-set resolves by a decisive majority
   exceed ~1% of the ambiguous set, STOP: the `sport_key` assumption is breaking. (Baseline expectation: near-zero —
   `sport_key` was 100%-populated in all sampled shards.)
2. **CHAMPIONSHIP/SERIE_B minority side appears at volume** — any `sport_key` resolving to Scottish Championship or
   Brazilian Série B at material count contradicts the strengthened verified single-league finding; STOP and re-scope
   (route those shards, don't fold them into the majority).
3. **Content-verify intersection < 100%** (Step 5) — source∩copy row-keys not fully covered → STOP, do NOT delete (R5
   destroy-32-pools class).
4. **Manifest double-count / row-count regression** — post-swap `availability_index.parquet` shows both
   `league_id=<RAW>` and `league_id=<CANON>` for a migrated shard, or total row count moves the wrong way → STOP: the
   atomic delete-old+write-new isn't holding (Constraint 1 breach).
5. **Concurrent live writer detected** — any running sports writer mid-migration (drain failed) → STOP (race corrupts
   both surfaces).
6. **Snapshot missing/unrestorable** before the first manifest write → STOP.
7. **features double-count on processed** — a features read for a migrated day returns inflated/doubled odds (old+new
   `bucketed.parquet` both read) → STOP the processed track and tighten the reprocess+delete window.
8. **A large unambiguous value missing from the completed name-map** (e.g. `FIRST_DIVISION_A`) → STOP: would route to
   fallback/wrong slug.
9. **Any prod-bucket delete reached without a human** → HARD STOP — never autonomous.

---

## 6. What must NOT be attempted, and why

- **A name-keyed alias map for the 6 ambiguous names** — it MERGES distinct leagues (Italian `SERIE_A` with
  `BRASILEIRAO`). This is the exact measurement that made the operator choose canonicalise-at-write; corroborated by
  `ODDS_API_DISPLAY_TO_CANONICAL` having no `FIRST_DIVISION_A` entry and one-sidedly resolving the collisions.
- **A path-only relocation** (leaving the parquet `league_id` content column raw) — MDPS re-derives its partition from
  row content and would re-emit historical output under the OLD partition (Constraint 2, confirmed against a live prod
  parquet).
- **An additive manifest write** (canonical rows without deleting the raw rows) — the consolidator dedup key includes
  `league_id`, so the shard double-counts (Constraint 1).
- **Manifest-first or delete-first ordering** — manifest-first yields live 404s under a manifest that claims `captured`;
  delete-first performs the one irreversible step before content-verify (delete-safety opening invariant + R5).
- **An autonomous prod-bucket delete** — delete-safety §3 human-only hard stop, at any confidence.
- **Two separate passes for `league_id` and K1 casing** — copies the same ~257K objects twice and doubles the exposure
  window (Constraint 3); combine into one copy to the final canonical form.
- **Guessing on undecidable shards** — leave untouched + logged; a wrong league assignment is silent, permanent data
  corruption.
- **Folding the `features-sports` (30 obj) / `instruments-store` (9,733 obj) contamination into this move** — different
  vocabulary, likely different/untraced writer, unverified root cause; track as separate findings with the corrected
  counts, don't smuggle them in.

## ⚠️ CRITICAL CORRECTION 2026-07-21 — objects are ROW-MIXED; migration is a per-row SPLIT, not a relocation

Direct measurement (stratified sampling, 150 objects/league) found that the verified 9-step plan's premise — "classify
each shard to ONE canonical target, then relocate the object" — is **WRONG for the 4 real-collision leagues**. A large
fraction of their objects contain rows for BOTH sides of the collision in a single file, because the OLD capture adapter
wrote all odds for a colliding raw name into one object per `(day, venue, raw_league_id)`:

| collision league | single-league objects | **ROW-MIXED objects (both leagues in one file)** |
| ---------------- | --------------------: | -----------------------------------------------: |
| BUNDESLIGA       |              94 (63%) |                                     **56 (37%)** |
| SERIE_A          |             118 (79%) |                                     **32 (21%)** |
| PRIMERA_DIVISION |             109 (73%) |                                     **41 (27%)** |
| SUPER_LEAGUE     |             107 (71%) |                                     **43 (29%)** |

Example: `day=2023-02-12/…/venue=VIRGINBET/league_id=BUNDESLIGA/…/ticks.parquet` contains BOTH `Bundesliga - Germany`
AND `Austrian Football Bundesliga` rows. Relocating that object wholesale to either target mis-attributes half its rows.

**Consequence for the executor:** `sport_key` is a **per-ROW** oracle, not a per-object one. The correct operation for
EVERY object is: read it → compute each row's canonical `league_id` from its `sport_key` → GROUP rows by canonical
`league_id` → write each group to its canonical path (splitting a mixed object into 2 target objects). This uniformly
handles single-league, mixed, and unambiguous objects; the content-column rewrite is inherently per-row.
`gcs_copy_object` (object rename) is INSUFFICIENT for the mixed objects — they require read-partition-write.

**Measured sport_key → canonical for the 4 real collisions (both sides confirmed present):**

| sport_key                      | canonical slug        |
| ------------------------------ | --------------------- |
| `Bundesliga - Germany`         | `BUNDESLIGA`          |
| `Austrian Football Bundesliga` | `AUSTRIAN_BUNDESLIGA` |
| `Serie A - Italy`              | `SERIE_A`             |
| `Brazil Série A`               | `BRASILEIRAO`         |
| `Primera División - Argentina` | `ARGENTINA_PRIMERA`   |
| `Primera División - Chile`     | `CHILE_PRIMERA`       |
| `Swiss Superleague`            | `SWISS_SUPER_LEAGUE`  |
| `Super League - Greece`        | `GREEK_SUPER_LEAGUE`  |

Independently reconfirmed the two NON-collisions: `SERIE_B` = only `Serie B - Italy` (120/120), `CHAMPIONSHIP` = only
`Championship` (120/120) — single-league in the data, as the workflow found. Evidence: `scratchpad/sportkey_probe.py`,
`scratchpad/mixed_probe.py` (2026-07-21).

## Scope refinement 2026-07-21 — 267K objects, 3 vocabularies, and the true classification shape

A controlled walk of the whole `league_id=` surface (read-only) measured the real scope, larger than the workflow's
raw-only figure:

- **267,614 objects** carry a `league_id=` segment (the workflow's 139,155 counted only `pipeline_mode=batch_odds_api`;
  the rest are the MDPS `processed/` odds_horizon_bucket objects, which ALSO carry `league_id=` and must migrate too).
- **76 distinct raw league_id values across THREE coexisting naming schemes**: api-football display names (`BUNDESLIGA`,
  `PREMIER_LEAGUE`), `SOCCER_`-prefixed machine keys (`SOCCER_SPAIN_LA_LIGA`), and `soccer_`-lowercase (`soccer_epl`).
  The `sport_key` column likewise appears as both a display label (`Denmark Superliga`) and a machine slug
  (`soccer_epl`).
- **51 distinct sport_key values.**

**The classification shape (this is what the executor implements):**

1. **The 6 collision raw names** (`BUNDESLIGA` / `SERIE_A` / `SERIE_B` / `CHAMPIONSHIP` / `PRIMERA_DIVISION` /
   `SUPER_LEAGUE`) — classify PER ROW by `sport_key` (10-entry map, all their sport_keys resolved; handles the 21-37%
   row-mixed objects via split-and-rewrite).
2. **The other ~70 raw league_id values are UNAMBIGUOUS** — one raw name → one canonical, so a raw-name map suffices and
   `sport_key` is not needed. The "22 unresolved sport_keys" from the registry-derived pass are ALL of this kind
   (`'EPL'`→`EPL`, `'La Liga - Spain'`→`LA_LIGA`, `'Bundesliga 2 - Germany'`→`BUNDESLIGA_2`,
   `'Premiership - Scotland'`→`SCOTTISH_PREMIERSHIP`, …) — unresolved only because the registry's `odds_api_name` uses a
   different display string than the parquet, NOT because they are ambiguous.

Verified map artifact (executor input): `scratchpad/sportkey_map.json` (29 auto-resolved + 10 collision entries; 22
unambiguous residuals to add to the raw-name map, each with a single clear target).

## Where the IRREVERSIBLE line is (execution discipline, even with operator migrate+delete permission)

The operator authorised migrate+delete. The reversible steps (build the verified maps, COPY to canonical targets +
content-rewrite, content-verify, snapshot, atomic manifest-swap) proceed autonomously. The **irreversible delete of the
old objects** runs ONLY when BOTH hold: (a) the executor is proven in a full DRY-RUN that emits a per-shard decision
manifest with ZERO undecidable rows, and (b) all sports VMs are drained (the 4 features re-run VMs still read the tick
bucket — relocating mid-run corrupts their odds features). Both are execution-safety gates, not permission gates; the VM
drain is hours away (watchdog `bu8zw4ei2` fires on completion). This is the correct order regardless of permission: copy
→ verify → swap → (drained + dry-run-proven) → delete.

Evidence: `scratchpad/registry_map.py`, `scratchpad/sportkey_map.json`, `scratchpad/full_map.py` (2026-07-21).

## Classification COMPLETE + registry-verified 2026-07-21 (executor input ready)

Built the full `raw_league_id → canonical` map from the SSOT (each classification-registry entry's `odds_api_name`
machine key + numeric-id resolution to the canonical slug) and verified every target exists in `LEAGUE_REGISTRY`. Result
over all 76 distinct raw values:

- **66 resolve deterministically to a canonical slug** — the `SOCCER_`/`soccer_` machine keys are country-qualified so
  they carry no ambiguity (`SOCCER_GERMANY_BUNDESLIGA`→`BUNDESLIGA`, `SOCCER_AUSTRIA_BUNDESLIGA`→`AUSTRIAN_BUNDESLIGA`,
  `soccer_epl`→`EPL`, …), and the bare display names map via the write-path resolver (`PREMIER_LEAGUE`→`EPL`,
  `2._BUNDESLIGA`→`BUNDESLIGA_2`, `FIRST_DIVISION_A`→`JUPILER_PRO`, `PREMIERSHIP`→`SCOTTISH_PREMIERSHIP`,
  `SUPERLIGA`→`DANISH_SUPERLIGA`).
- **6 are the bare collisions** → per-row `sport_key` (map verified, both sides present).
- **2 leagues genuinely UNRESOLVED** (4 raw values across two casings): **`SOCCER_CHINA_SUPERLEAGUE` /
  `soccer_china_superleague`** and **`SOCCER_RUSSIA_PREMIER_LEAGUE` / `soccer_russia_premier_league`** — they have NO
  `LEAGUE_REGISTRY` entry. Left UNTOUCHED by the migration.

Artifact (executor input): `scratchpad/classification.json` (raw → canonical, with `AMBIGUOUS`/`UNRESOLVED` markers).

### OPERATOR DECISION NEEDED — China Super League + Russia Premier League

These two leagues appear in the captured odds data but are not in the canonical trading universe (`LEAGUE_REGISTRY`).
Either (a) they ARE intended to be in-universe → add canonical slugs to `LEAGUE_REGISTRY` and include them in the
migration, or (b) they are out-of-universe → leave untouched now, and dispose of them under the delete-safety protocol
separately. Default until decided: **left untouched** (never guess a canonical target for an unregistered league).

## EXECUTOR SPEC + verified maps 2026-07-21 (operator-authorised: migrate+delete, gated on dry-run success + VM drain)

Operator ruled China + Russia in-universe → added to the registry (`unified-api-contracts`: `league_data_other.py`
CHINA_SUPER_LEAGUE af=169 / RUSSIA_PREMIER_LEAGUE af=235, + classification_data_b.py). Shipped-code write-path
(id-based) verified unaffected: EPL(39)→EPL. **After this, 0 raw league_id values are UNRESOLVED.**

**Classify by PER-ROW `sport_key`, never by raw name** — proven necessary: adding Russia's registry display name
"Premier League" made a naive raw-name resolver map the bare corpus value `PREMIER_LEAGUE` to RUSSIA_PREMIER_LEAGUE, but
in the corpus bare `PREMIER_LEAGUE` is ENGLISH (→EPL); Russia only ever appears as the machine key
`soccer_russia_premier_league`. sport_key is unambiguous per row.

**Verified `sport_key → canonical` map (55 entries; every target confirmed in LEAGUE_REGISTRY; all 51 corpus sport_keys
covered):** collisions — `Bundesliga - Germany`→BUNDESLIGA · `Austrian Football Bundesliga`→AUSTRIAN_BUNDESLIGA ·
`Serie A - Italy`→SERIE_A · `Brazil Série A`→BRASILEIRAO · `Serie B - Italy`→SERIE_B · `Championship`→ENG_CHAMPIONSHIP ·
`Primera División - Argentina`→ARGENTINA_PRIMERA · `Primera División - Chile`→CHILE_PRIMERA ·
`Swiss Superleague`→SWISS_SUPER_LEAGUE · `Super League - Greece`→GREEK_SUPER_LEAGUE. Both the display-label and
`soccer_*` machine-slug forms map to the same canonical (e.g. `soccer_epl`/`EPL`→EPL,
`soccer_china_superleague`→CHINA_SUPER_LEAGUE, `soccer_russia_premier_league`→RUSSIA_PREMIER_LEAGUE,
`soccer_uefa_champs_league`→UCL).

**Executor** (`market-tick-data-service` scripts home; per-row split):

1. DRY-RUN (default, read-only): list every `league_id=` object, classify by path, emit a per-object decision manifest,
   HARD-FAIL if any raw league_id is unmapped. Dispositions: RELOCATE(raw→canon) · PER-ROW-SPLIT(6 collisions) ·
   already-canonical(skip) · UNRESOLVED-untouched(now 0).
2. APPLY (refused while any `features-sports-sports-*` VM is RUNNING — they read the tick bucket): per object, read →
   map EACH ROW's `sport_key` → canonical → GROUP by canonical → write each group to
   `.../league_id={CANON}/instrument_type=ODDS/data_type=TRADES/ticks.parquet` (rewriting the `league_id` CONTENT column
   - UPPER casing segments). Mixed objects SPLIT into 2. crc/row-verify each copy.
3. Manifest atomic-swap (delete old raw-keyed rows + write canonical, reusing
   `rebuild_sports_manifest.py::_clean_stale_league_entries`) then MDPS reprocess of the processed/ surface, then
   coverage-registry refresh, then — gated on a clean dry-run + drain — the delete of the old objects (snapshot first;
   GCS soft-delete safety net).

Session-local map artifacts (to be committed with the executor to the mtds scripts home before apply):
`scratchpad/sportkey_canon_final.json`, `scratchpad/classification.json`, `scratchpad/relocate_league_id.py`.

## STATUS 2026-07-21 — reversible+verified work DONE; irreversible apply gated on drain

- ✅ **China + Russia added to the canonical registry** — `unified-api-contracts@beec78aa` (football universe 94→96;
  count-pinned tests updated; shipped write-path verified unaffected). **0 raw league_ids now UNRESOLVED.**
- ✅ **Classification validated end-to-end** — full-corpus DRY-RUN over all 267,605 `league_id=` objects PASSED with
  ZERO unresolved: 128,450 already-canonical (skip) · 75,055 per-row-split (6 collisions) · 64,100 relocate (raw→canon).
- ⏳ **Executor APPLY machinery** (per-row split + copy + content-rewrite + crc-verify + manifest-swap + delete) — NOT
  YET BUILT; the dry-run cut deliberately stubs `--apply`. To be built as a focused effort + committed to the mtds
  scripts home, then run behind BOTH gates: dry-run success (met) AND all `features-sports-sports-*` VMs drained (they
  read the tick bucket). Delete authorised by the operator on those two conditions.

## READY TO EXECUTE 2026-07-21 — verified executor committed; runs as a monitored migration job

The executor is adversarially verified (Ultracode 6-agent workflow) and committed to the durable mtds scripts home:
`market-tick-data-service@b2a49317` →
`scripts/sports/league_id_relocation/migrate_sports_league_id_casing_2026_07_21.py` (+ `sportkey_canon_final.json`,
`classification.json` beside it).

**Verification (workflow `wf_1e73121f-e1c`):** 4 adversarial reviewers found 4 REAL defects, all fixed + re-proven: (A)
a TOCTOU write race → fixed with a compare-and-swap loop (`if_generation_match`), so a concurrent writer's rows can
never be clobbered with a false verify=PASS; (B) the no-clobber proof was skipped on the merge-into-existing path → now
always computed + tracks the pre-existing target's rows; (C) `classification.json` had `PREMIER_LEAGUE→RUSSIA`
(confirmed 12,847 objects are all EPL) → fixed at the root + an operator-override pin + an opt-in `--sample-check`; (D)
~32% of the corpus was silently unexamined → now an explicit OUT-OF-SCOPE census. Full-corpus dry-run PASSED: 266,408
objects / 34,228 units, 0 unknown raws; all validation PASS / 0 FAIL. Verdict: **GO** (VMs drained).

**Run as a MONITORED migration job (NOT inline — it is ~139K raw-shape objects, multi-hour).** Sequence:

1. `--apply-prod` (no `--confirm-prod-write`) once, WITHOUT `--index`, for the live out-of-scope census + VM-guard +
   PLAN.
2. `--apply-prod --confirm-prod-write --index scripts/.../raw_index.tsv` — copies+CAS-verifies the raw
   `batch_odds_api/odds/trades` shape to canonical paths (`league_id=<CANON>/instrument_type=ODDS/data_type=TRADES/`).
   COPY-ONLY: never deletes; refuses while any `features-sports-sports-*` VM is non-terminal.
3. THEN the deferred shapes (127,488 objects — `odds_horizon_bucket` 109,312 · `batch_footystats` 16,970 · … — the "then
   extend" passes) must be handled before any bucket-wide delete or "complete" claim.
4. THEN the atomic manifest-swap (reuse `rebuild_sports_manifest.py::_clean_stale_league_entries`), THEN MDPS reprocess
   of the processed surface, THEN the coverage-registry refresh.
5. **ONLY THEN the SEPARATE, irreversible delete** of the old non-canonical objects (operator-authorised on dry-run
   success — which is met — snapshot first; GCS soft-delete safety net). This step is deliberately NOT started at
   extreme session depth; it warrants a fresh, monitored context + a final at-scale content re-verify.

Caveats the operator must hold (from the workflow): the raw-content `data_type` casing is rewritten but path-casing on
the deferred shapes is a later pass; the one earlier-incident PROD object at
`2020-06-11/PINNACLE/.../LA_LIGA/ODDS/TRADES` is idempotent-safe (SKIP). NO-GO trigger: any `features-sports-sports-*`
VM non-terminal, or a `--sample-check` mismatch.

## DURABLE ARTIFACT LOCATIONS (2026-07-21 — corrects the scratchpad references above)

The executor + its classification maps are COMMITTED (they are NOT session-local — earlier `scratchpad/…` references
above are superseded by this):

- **`market-tick-data-service@b2a49317`** →
  `scripts/sports/league_id_relocation/migrate_sports_league_id_casing_2026_07_21.py` (+ `sportkey_canon_final.json` =
  the verified 55-entry sport_key→canonical map, + `classification.json` = raw→canonical), all beside the script. Run it
  from there (`--apply-prod --confirm-prod-write`), not from any scratchpad copy. The `scratchpad/*.py|*.sh` names in
  the "Evidence:" lines above were session-local one-off probes (corpus walks, sport_key enumeration, sizing). They are
  NOT committed and will vanish at session end — their MEASURED RESULTS are stated inline in this doc and are what
  matters; re-derive with a fresh probe if a number needs refreshing (each carries a 2026-07 date).

## STATUS 2026-07-25 — manifest swap had silently reverted; re-applied + verified stable

The 2026-07-22 manifest swap (`manifest_swap_2026_07_22.py`, raw `TRADES`/`batch_odds_api` shape) was found to have
silently reverted (260,298 stale raw rows back, byte-identical to pre-swap) — its CAS write predated the TOCTOU
consolidator-race fix (`unified-trading-library@14301571`, 2026-07-24) by 2 days. Re-applied and verified stable across
5 consolidator cycles (~7.5 min). Full detail:
`/plans/archive/issues/sports_league_id_swap_silently_reverted_toctou_2026_07_25.md`. **Still genuinely outstanding**:
`odds_horizon_bucket` (109,312 objects, needs MDPS `reprocess_sports_odds.py` Step-7) + `batch_footystats` (16,970
objects, needs its own copy+swap pass) + the coverage-registry refresh + the human-gated final delete.

## MERGED TRACKING 2026-07-27 — `LEAGUE_ID_TO_TIER` mapping + 28-unmapped-`league_id` gap analysis (from `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`)

Per `sports_closeout_track_x_hygiene_2026_07_25.md` todo 2 (the canonical-form conflict between that plan and this
closeout's Track V) — **this section is now the single settled location** for the two open gap-analysis items that
plan's own "P1 — gap-analysis follow-ups" section tracks as its own todos 1-2. This is a tracking merge only: it does
not implement the mapping, and the source plan's todos stay open there (still the execution home for that work) — this
section exists so the mapping + gap list are visible from the league_id-migration tracking, not only from the
originating plan.

**⚠️ Vocabulary flag (the actual conflict this merge resolves):** the source plan's own text labels raw api-football
display strings (`PREMIER_LEAGUE`, `BUNDESLIGA`, `SERIE_A`, `LA_LIGA`, …) plus the odds_api-native `SOCCER_*` machine
keys as its **"canonical namespace"** (`sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` § "Input from P1c
golden-window audit"). That label describes only the raw _observed_ league-id vocabulary from that plan's own 2026-06-27
golden-window audit — it is **NOT** this closeout's canonical form. Per the Canonical target section above and this
doc's own write-path fix (`mtds@ad4f1872`), the UAC `LEAGUE_REGISTRY` slug (`EPL`, `BUNDESLIGA`, `BUNDESLIGA_2`, …) is
canonical; every raw display string and every `SOCCER_*` key is exactly the non-canonical `league_id` population this
doc's relocation (§§1-9 above) already has a verified mapping for (`sportkey_canon_final.json` / `classification.json`,
committed at `market-tick-data-service@b2a49317:scripts/sports/league_id_relocation/`). When the `LEAGUE_ID_TO_TIER`
mapping (below) is eventually built, it should route both raw and `SOCCER_*` forms to the SAME canonical target already
resolved there, not re-derive a second, parallel tier taxonomy keyed on non-canonical strings.

**Coverage-tier mapping result (23 of 51 observed league_ids mapped, from the 2026-06-27 P1c Todo 4 cluster-validation
audit)** — static validation against `sports_bookmaker_league_coverage.json` (27 bookmakers × 51 leagues):

- `tier_1_domestic` (10 leagues): BUNDESLIGA, LA_LIGA, LIGUE_1, PREMIER_LEAGUE, SERIE_A, SOCCER_EPL,
  SOCCER_FRANCE_LIGUE_ONE, SOCCER_GERMANY_BUNDESLIGA, SOCCER_ITALY_SERIE_A, SOCCER_SPAIN_LA_LIGA — expected bookmakers
  (pinnacle, betfair_ex_uk, williamhill, unibet_uk) ALL PRESENT.
- `tier_1_international` (1 league): SOCCER_UEFA_CHAMPS_LEAGUE — expected bookmakers (pinnacle, betfair_ex_uk,
  williamhill) ALL PRESENT.
- `tier_2_domestic` (12 leagues): 2._BUNDESLIGA, CHAMPIONSHIP, EREDIVISIE, FIRST_DIVISION_A, LIGUE_2, PRIMEIRA_LIGA,
  PRIMERA_DIVISION, SEGUNDA_DIVISION, SERIE_B, SOCCER_BELGIUM_FIRST_DIV, SOCCER_NETHERLANDS_EREDIVISIE,
  SOCCER_PORTUGAL_PRIMEIRA_LIGA — expected bookmakers (pinnacle, betfair_ex_uk) ALL PRESENT.

**The 28 unmapped `league_id`s (no tier definition in UAC `EXPECTED_BOOKMAKER_MARKET_SETS`)**: A-LEAGUE, ALLSVENSKAN,
EKSTRAKLASA, ELITESERIEN, J1_LEAGUE, K_LEAGUE_1, LIGA_MX, MLS, PREMIERSHIP, SOCCER_ARGENTINA_PRIMERA_DIVISION,
SOCCER_AUSTRALIA_ALEAGUE, SOCCER_AUSTRIA_BUNDESLIGA, SOCCER_CHINA_SUPERLEAGUE, SOCCER_DENMARK_SUPERLIGA,
SOCCER_GREECE_SUPER_LEAGUE, SOCCER_JAPAN_J_LEAGUE, SOCCER_KOREA_KLEAGUE1, SOCCER_MEXICO_LIGAMX,
SOCCER_NORWAY_ELITESERIEN, SOCCER_POLAND_EKSTRAKLASA, SOCCER_RUSSIA_PREMIER_LEAGUE, SOCCER_SWEDEN_ALLSVENSKAN,
SOCCER_SWITZERLAND_SUPERLEAGUE, SOCCER_TURKEY_SUPER_LEAGUE, SOCCER_USA_MLS, SUPERLIGA, SUPER_LEAGUE, SUPER_LIG.
**Overlap note**: SOCCER_CHINA_SUPERLEAGUE and SOCCER_RUSSIA_PREMIER_LEAGUE are 2 of these 28 — both were the "genuinely
UNRESOLVED" leagues in this doc's own relocation work above, until the operator added them to `LEAGUE_REGISTRY`
(`unified-api-contracts@beec78aa`, § "STATUS 2026-07-21"); they remain unmapped for the cluster-validation tier purpose
tracked here, a separate, still-open gap from the relocation's own (now-resolved) registry-membership gap.

**Required follow-up actions** (`sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` P1 todos 1-2, execution stays
in that plan):

1. Add a `LEAGUE_ID_TO_TIER` mapping (function or dict) to UAC routing each of the 51 observed league_ids to a
   `LeagueTier` key in `EXPECTED_BOOKMAKER_MARKET_SETS`
   (`unified_api_contracts/canonical/crosscutting/_honest_coverage_clusters.py` — `EXPECTED_BOOKMAKER_MARKET_SETS`
   already exists there; `LEAGUE_ID_TO_TIER` does not yet, confirmed by a repo grep 2026-07-27). Without it, runtime
   cluster-validation code cannot determine which expected bookmaker set applies to a given manifest row.
2. Extend `EXPECTED_BOOKMAKER_MARKET_SETS` to cover the 28 unmapped league_ids above (or add a `tier_3_global` /
   `no_expectation` tier for non-EU leagues the empirical audit determines have inconsistent bookmaker coverage).

Cross-reference: `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` § "Gap analysis from P1c Todo 4 cluster
validation" + § "P1 — gap-analysis follow-ups".

## Adjacent finding 2026-07-27 (slot-14) — 2 raw-league_id shards manifest-unregistered, missed by the EXCHANGE_ODDS/FIXED_ODDS GCS move

While verifying `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` todo 7 (MDPS `dependency_checker` hive-token
check against the post-move bucket state), a direct GCS listing for `day=2020-07-07` found 2 objects still under the
legacy `venue=PINNACLE/instrument_type=ODDS/data_type=TRADES` partition, keyed on the raw (non-canonical) `league_id`
values this doc already tracks: `CHAMPIONSHIP` and `PREMIER_LEAGUE`. Neither appears in `read_availability_index()`'s
output for that date/venue (the manifest enumerates only the canonical `ENG_CHAMPIONSHIP` etc. for PINNACLE that day) —
so these 2 shards are manifest-UNREGISTERED, exactly this doc's core defect class, not a new one. Because the
EXCHANGE_ODDS/FIXED_ODDS fork's GCS-move tooling is manifest-driven by design (single-walk discipline — never a live GCS
walk), it correctly could not and did not enumerate these 2 shards; they were left untouched under the legacy
`instrument_type=ODDS` partition. Out of scope to fix here (not this doc's todo, not the fork plan's todo) — flagging so
whichever future pass migrates this doc's 214,842 non-canonical-`league_id` rows also re-partitions any of them still
sitting under the legacy sports `odds` instrument_type into `exchange_odds`/ `fixed_odds` per the fork's now-shipped
venue→class mapping (PINNACLE → FIXED_ODDS). Not re-running the fork's migration tool against a live GCS walk to catch
these — that would violate single-walk discipline for a 2-object find; they'll be swept up naturally once this doc's own
manifest-registration fix lands and re-enumeration includes them.

## LIVE-PROBE 2026-07-28 (slot-11) — CONFIRMS non-registry rows still remain; blocks Track H's denominator todo

`sports_consolidated_native_ao_extract_2026_07_25.md`'s Track H todo ("implement the registry-aware honest-coverage
denominator in `compute_coverage_for_bucket()`") requires, as its own stated first step, a live manifest census
confirming 0 sports manifest rows still carry a non-registry-form `league_id` before shipping the denominator change —
explicitly added because the source todo's "largely executed" framing couldn't be trusted at face value. Ran that probe
today rather than shipping on the strength of this doc's 2026-07-25 status note.

**Method**: single bounded, column-pruned read of the consolidated `market-data-tick-sports-prd-central-element-323112`
availability index (`read_availability_index(bucket, columns=["league_id", "pipeline_mode"])` — the same reader every
other data-status endpoint uses, no fresh GCS walk), `league_id` values compared against the full UAC `LEAGUE_REGISTRY`
key set (390 entries, `unified_api_contracts.canonical.domain.sports.league_data`).

**Result — NOT zero, denominator change did NOT ship**:

- Total manifest rows: 516,196.
- Non-registry `league_id` rows: 57,942, of which 2,782 are a blank/`NaN`-coerced `"None"` sentinel (a separate
  honest-absence question, not this migration's canonicalisation gap) — so **55,160 rows are genuine non-canonical
  `league_id` strings**, confirming this doc's own 2026-07-25 status note ("still genuinely outstanding:
  `odds_horizon_ bucket` + `batch_footystats`") is still accurate 3 days later, live.
- By `pipeline_mode` (matches the doc's own named deferred shapes): `batch_mdps_odds_horizon_bucket` 42,652 ·
  `batch_footystats` 14,668 · `batch_instruments_service` 606 · `batch_odds_api` 16.
- Top raw values (unchanged cast of characters from the original 2026-07-20 measurement): `PRIMERA_DIVISION` 8,794 ·
  `CHAMPIONSHIP` 7,222 · `FIRST_DIVISION_A` 7,119 · `PREMIER_LEAGUE` 7,107 · `2._BUNDESLIGA` 6,114 · `SUPER_LEAGUE`
  5,645 · `SUPERLIGA` 5,536 · `PREMIERSHIP` 4,329 · `A-LEAGUE` 924, plus a long tail of the 28 unmapped
  `SOCCER_*`/lower- case `soccer_*` keys from the "MERGED TRACKING 2026-07-27" section above (each present in BOTH
  casings — the parse-bug residue that section's venue-vocabulary-cleanup todo already tracks separately).

**Disposition**: Track H's denominator todo correctly did NOT ship — its own STOP condition fired exactly as designed.
No code changed. This section exists so a future dispatch, once the `odds_horizon_bucket` MDPS reprocess +
`batch_ footystats` copy+swap pass + coverage-registry refresh land (this doc's own "Still genuinely outstanding" list,
STATUS 2026-07-25 above), can re-run the same probe rather than re-deriving the method, and can cite this dated
measurement as evidence the denominator change was correctly withheld on 2026-07-28.

## RE-DISPATCH CHECK 2026-07-28 (slot-7, same day, no new probe needed) — 1 of 3 blockers now closed

Track H's denominator todo re-dispatched to a second slot the same day. Rather than re-running the slot-11 live-probe
(nothing suggested the manifest state had moved in a few hours), checked the shipped-status of the three items this
doc's own "Still genuinely outstanding" list (STATUS 2026-07-25) names as the gate:

- **Coverage-registry refresh — DONE.** `unified-api-contracts@8e8d2e5b` (2026-07-22) + `@804858c9` (2026-07-27,
  "canonicalise BOOKMAKER_LEAGUE_COVERAGE league ids," fixed 358/1129 double-keyed raw-vs-canonical pairs). Confirmed
  closed in `sports_satellite_ao_dispatch_batch7_2026_07_27.md:153-160`.
- **`odds_horizon_bucket` MDPS reprocess (Step 7) — still outstanding.** No commit in market-data-processing-service
  reruns `reprocess_sports_odds.py` against this migration's canonical league_id shape.
- **`batch_footystats` copy+swap — still outstanding.** No apply/swap script exists yet in market-tick-data-service
  beyond the read-only `census_footystats_orphan_content_2026_07_25.py`;
  `/plans/archive/issues/sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md:191-196` confirms
  this shape "was never in this swap's scope and remains genuinely un-migrated."

**Net: 2 of 3 blockers remain open, so the STOP condition still holds and the denominator change still must not ship.**
No code changed here either. Narrowing this to the exact 2 remaining blockers (rather than 3) is the only new
information — a future dispatch can skip re-verifying the coverage-registry piece and go straight to checking whether
the MDPS reprocess + footystats copy+swap have landed before re-running the full manifest census.

## RE-DISPATCH CHECK 2026-07-28 (slot-10, same day, 3rd dispatch) — both remaining blockers still unshipped

Track H's denominator todo dispatched a THIRD time the same day. Same shortcut as slot-7 (checked shipped-status of the
2 remaining blockers rather than re-running the full manifest census):

- **`odds_horizon_bucket` MDPS reprocess (Step 7)** — `market-data-processing-service` git log for
  `reprocess_sports_odds.py` most recent commit is `6f7422e` (2026-07-27T18:15, a venue-stamp fix on
  `odds_horizon_bucket` fine manifest rows — unrelated to re-running the script against this migration's canonical
  `league_id` shape). No commit does the actual Step-7 re-run. **Still outstanding.**
- **`batch_footystats` copy+swap** — grepped `market-tick-data-service` for any apply/swap script for this shape beyond
  the known read-only `census_footystats_orphan_content_2026_07_25.py`; none exists (the
  `manifest_swap_venue_restamp_ 2026_07_27.py` / `migrate_sports_league_id_casing_2026_07_21.py` scripts found in the
  repo are different migrations — venue casing and the raw `batch_odds_api` shape respectively, not this shape). **Still
  outstanding.**

**Net: unchanged — both blockers remain open, STOP condition still holds.** Flagging the dispatch pattern itself (not
just the blocker): this is the 3rd consecutive same-day worker dispatch to hit this identical, already-well-documented
STOP condition, each one correctly declining to ship but re-spending a full task cycle on the same negative-result
check. Filed a `/blocked` recommending the backlog task be PARKED (`unified-trading-pm/agents/RULES.md` § "Park a task")
until the 2 real prerequisite items above land — they are tracked here, not as todos in the dispatching plan
(`sports_consolidated_native_ao_extract_2026_07_25.md`), so nothing currently causes the denominator todo to stop being
offered to the queue once these are the only real blockers.

## Todos

- [ ] [DATA] P1. **Ship Track H's registry-aware honest-coverage denominator once its 2 remaining blockers land** — the
      `odds_horizon_bucket` MDPS reprocess (Step 7 re-run of `reprocess_sports_odds.py` against this migration's
      canonical `league_id` shape) and the `batch_footystats` copy+swap apply script (neither exists yet) are the only
      two prerequisites left; the STOP condition holds until both ship (re-verified 2026-07-28, slot-10 — see
      "RE-DISPATCH CHECK" sections above).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — the sole open todo is explicitly gated — 'ship
  Track H's registry-aware honest-coverage denominator ONCE its 2 remaining blockers land' — and the doc's own
  2026-07-28 re-dispatch checks (slot-7, then slot-10) confirm both blockers still unshipped. It also carries an
  unanswered 'OPERATOR DECISION NEEDED — China Super League + Russia Premier League' section
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — swapped the now-shipped
  `migrate_sports_league_id_casing_2026_07_21.py` executor for the two files the sole remaining open todo actually
  targets: `market-data-processing-service/scripts/reprocess_sports_odds.py` (Step-7 re-run) and
  `census_footystats_orphan_content_2026_07_25.py` (the existing census; its apply/swap counterpart still doesn't
  exist).
- **2026-08-03 (slot 16, data_engineering) — near-miss caught, flagging here for cross-reference**: while working
  `sports_curated_universe_domestic_selection_remaining_2026_07_25.md`'s residual out-of-curated-universe drop decision
  (BLK-aa587dbf), found the SAME raw-name population this doc tracks (`PRIMERA_DIVISION`/`PREMIER_LEAGUE`/
  `CHAMPIONSHIP`/`2._BUNDESLIGA`/`SUPER_LEAGUE`/etc., still 74,058 rows post-dedup) was about to be miscategorized as
  "out-of-universe junk" eligible for `--drop-out-of-universe --apply` by that todo's own script
  (`instruments-service/scripts/canonicalize_sports_league_id_schema_2026_06_24.py`) — that script has no awareness of
  THIS doc's already-ruled canonicalise-at-write decision or its still-open history-migration blockers, so it would have
  destroyed real `odds_horizon_bucket`/`trades` rows for major/ambiguous-but-real leagues awaiting migration, not
  removed junk. Corrected before any drop executed (urgent `/progress` sent + the other doc updated with a full
  correction); no code/data changed here. Cross-linked both docs' `related:`. No change to this doc's own open todo or
  status — flagging purely so a future reconciliation sweep sees the connection and so
  `canonicalize_sports_league_id_ schema_2026_06_24.py`'s `--drop-out-of-universe` gains an exclusion for this doc's
  tracked raw-name population before anyone runs it again.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged. Fingerprint match:
  `sports_curated_universe_domestic_selection_remaining_2026_07_25.md` — matched literal: the raw league-name population
  (`PRIMERA_DIVISION`/`PREMIER_LEAGUE`/`CHAMPIONSHIP`/`2._BUNDESLIGA`/`SUPER_LEAGUE`) and
  `canonicalize_sports_league_id_schema_2026_06_24.py` (already cross-linked in this doc's own 2026-08-03 entry above,
  not a fresh find).

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid (sports tranche) — re-verified, unchanged since 2026-07-30. The
  sole open todo (Track H's honest-coverage denominator) remains gated on 2 prerequisites that don't exist yet
  (`odds_horizon_bucket` MDPS reprocess re-run, `batch_footystats` copy+swap apply script) — confirmed still outstanding
  per this doc's own 2026-07-28 re-dispatch checks, no newer evidence contradicts that.

- **round11 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA, valid — re-checked against today's accumulated
  precedents. The sole open todo (ship Track H's denominator once its 2 blockers land) is already tracked via the
  dedicated `sports_track_h_denominator_gated_2026_07_28.md` / `sports_track_h_denominator_prereqs_2026_07_28.md` pair,
  itself dependency-gated on an unrelated `market-tick-data-service` QG-red repo-blocker (`RB-166e706f`) not yet
  confirmed cleared — per `plans/active/issues/ag_closeout_audit_sports_parked_2026_08_09.md`'s "Parked —
  dependency-gated" entry (today). That same ledger separately flags this doc's own untracked residual (the human-gated
  final delete of ~256,954 old non-canonical objects) for a future dedicated delete-safety pass, not a batch todo — a
  new finding, not a reason to flip. No flip, no extraction (would duplicate the tracked prereqs pair).
