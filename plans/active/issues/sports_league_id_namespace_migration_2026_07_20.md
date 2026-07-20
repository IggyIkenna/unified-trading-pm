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
related: [../sports_consolidated_closeout_2026_07_19.md, ../sports_consolidated_audit_2026_07_19.md]
created: "2026-07-20"
source: operator decision 2026-07-20 (canonicalise at the write path)
resolved_by:
locked_by:
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

Governing SSOT: `codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (five-part proof, COPY-not-MOVE, disposition
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
