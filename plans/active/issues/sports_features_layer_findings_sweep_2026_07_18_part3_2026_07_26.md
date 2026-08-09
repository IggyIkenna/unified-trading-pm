---
doc_type: issue
title:
  Sports features-layer findings sweep — PART 3 of 3 (§ O-AA — round RAW-vs-catalogue gap, derive-then-fetch backfill,
  round derivation shipped + applied corpus-wide, competition_phase stale-entity root cause, and 9 dated 2026-07-19
  findings/corrections through end-to-end validation)
summary:
  'Verbatim, byte-for-byte extraction (2026-07-26, plan line-cap remediation — the original 1,843-line doc exceeded the
  `plans/active/` 1,000L hard cap) of the final third of
  `/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md`, PART 1 of 3. Continues directly from Part 2
  (§ G-N). Carries § O (round is ~50% populated in RAW — the 3.2% catalogue figure was measuring the ROLLUP, not
  capture), § P (derive `round` for the confident majority, spend API calls only on the clustered remainder — sizing,
  era-scoping), § Q (round derivation SHIPPED + APPLYING — 89.2% of the gap closed with zero api-football calls; result:
  115,715 rows filled corpus-wide), § R (ROOT CAUSE of `competition_phase` UNKNOWN — an entity split left every consumer
  reading a dead entity; fixed, catalogue repointed, `round` 0.7% -> 70.6%), and § S through § AA — 9 dated 2026-07-19
  findings/corrections found while executing the round backfill: `total_matchdays` hardcoded to 38 for every league,
  residual round-blank scoping, the 159-pair blank-league backfill, a legacy-entity read bug, the "cup competitions"
  mischaracterization corrected, end-to-end chain validation before fleet commit, a launcher hint-text bug, a `matchday`
  persistence defect (found not root-caused, then root-caused and fixed), and a generalized monitoring-metric lesson (a
  metric must be able to MOVE for the operation being run). 31 of the parent''s original 73 open `[ ]` checkboxes live
  in this part (Part 1 carries 18, Part 2 carries 24) — same total, no content moved between open/closed status. Record
  + live-work hybrid, not archive-only: several `[ ]` items here are still genuinely open.'
status: open
resolved_by:
nature: issue
asset_group: [sports]
stage: [data, features]
repos: [instruments-service, features-service, deployment-service, unified-api-contracts]
scope: [engineer, admin]
tags: [sports, features, round-backfill, competition-phase, fixture-round, data-correctness, line-cap-split]
related:
  [
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md,
  ]
created: 2026-07-18
author: unknown
source:
  - Split 2026-07-26 from `/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md` for line-cap
    remediation (1,843L, over the `plans/active/` 1,000L hard cap enforced by `check_line_caps.sh`) — precedent
    `sports_halftime_odds_sfi_vs_inplay_history_part2_2026_07_25.md`. The findings below were originally captured
    2026-07-18/2026-07-19 during and after the sports round-derivation backfill campaign documented in Part 1's
    frontmatter.
assigned_vm: NA
assigned_role: data_engineering
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
drift_direction: advance-code
parent_epic: infrastructure_master
execution_scope: local-only
depends_on: []
last_updated: 2026-07-26
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    instruments-service/scripts/derive_sports_fixture_round_2026_07_18.py,
    features-service/features_service/sports/exporters/derived_features_helpers.py,
  ]
---

> **✅ OPERATOR RULING 2026-08-08 — AUTHOR the codex process rule, and apply it immediately.** The open todo proposes a
> codex rule that an entity rename/split (e.g. `fixtures` → `fixtures_schedule` / `fixtures_outcomes`) MUST enumerate
> and migrate every consumer in the same change. Ruled: **author it, and make the sports taxonomy chain its first
> governed case** — that chain performs exactly this operation twice (`trades` → `odds`, and the whole 19-token
> uppercase→lowercase instruments-service vocabulary), so the rule gets validated by real use instead of being written
> abstractly. Authored by `/plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`. Concrete evidence for
> why the rule is needed, found by the 2026-08-08 audit: `features-service`'s sports feature loader reads bucketed odds
> by **GCS path prefix** (`_ODDS_BUCKETED_PREFIXES`), not by the `data_type` column — so a `data_type` grep does not
> find it, and a rename would silently break it.

# Sports features-layer findings sweep — PART 3 of 3 (2026-07-18/19, split 2026-07-26)

> Continued from
> [`sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`](/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md)
> (Part 2 of 3, § G-N), which continues from
> [`sports_features_layer_findings_sweep_2026_07_18.md`](/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md)
> (Part 1 of 3, § A-F). This is the final part. Content below is verbatim from the original doc, § O through § AA.

## O. `round` is ~50% populated in RAW — the 3.2% was the CATALOGUE. The gap is the ROLLUP, not capture.

The surgical pilot (`--max-leagues 1 --seasons 2019 --apply`) reported
`ALLSVENSKAN APPLIED +0/4349 rows across 1551 parquet(s) (242 fixtures fetched)` — it fetched fine and filled **zero**.
That prompted a proper measurement instead of another backfill.

Measured `round` population per day, BOTH entities:

| day        | fixtures_schedule | %   | legacy fixtures |
| ---------- | ----------------- | --- | --------------- |
| 2019-05-11 | 47/153            | 31% | 55/237          |
| 2020-09-19 | 171/289           | 59% | 171             |
| 2021-03-13 | 166/284           | 58% | 166             |
| 2022-10-05 | 44/88             | 50% | 44              |
| 2023-08-19 | 334/666           | 50% | 334             |
| 2024-04-06 | 187/394           | 47% | 187             |
| 2025-11-08 | 195/404           | 48% | 195             |
| 2026-03-14 | 142/354           | 40% | 142             |

**RETRACTED (mine, twice over):**

1. "`round` is blank / ~0% in raw" — it is **~30-60% populated across all of history**. My earlier `round 0/4` and `0/7`
   readings were single small legacy shards, not a representative sample. I generalised from a handful of EPL shards.
2. "The entity split explains it" (§ G-RESOLVED framing) — legacy `entity=fixtures` and `entity=fixtures_schedule` carry
   **IDENTICAL** round counts on 7 of 8 sampled days. The split is real but is NOT the round story.

**So the 3.2% in the original issue was measured on the CATALOGUE (545/17,064 rows), while raw holds ~50%.** The loss is
in the ROLL-UP, not the capture. That reframes the remaining work completely:

- A whole-corpus `--force` refetch (1.26M calls) was never the right instrument — and neither is the surgical backfill
  for the ~50% that ALREADY has round.
- The genuinely-missing ~50% is a real but much smaller target, and some of it is honest absence (cup/friendly fixtures
  legitimately have no `Regular Season - N` round).

- [x] ✅ [DATA] P0. Rebuild the sports catalogue
      (`build_instrument_catalogue.py --asset-group sports --since 2019-01-01`) and re-measure `round` /
      `competition_phase` there. If the catalogue jumps from 3.2% toward the raw ~50%, the rollup was simply stale and
      NO backfill is needed for that half. **Answered in two parts**: § R found the bare rebuild alone does NOT fix it
      (dead entity, `round` came out WORSE at 0.7%); R-FIXED then repointed the entity and re-ran the same rebuild,
      taking `round` to **70.6%**. Track V's `[OPS] P2` re-roll (`sports_consolidated_closeout_2026_07_19.md`) owns the
      NEXT periodic re-roll (+26,894 rows from § T/§ U) — still open there, not duplicated here.
- [x] ✅ [DIAG] P0. Only after that: characterise the residual raw blanks — split genuine absence (cups/friendlies with
      no round concept) from real capture gaps, and size the surgical run against the real gap. **Done, exceeding this
      ask** — § T/§ U/§ W characterised the residual in full: in-window (38,170) vs pre-2019 (122,864, out of scope),
      registry-member (27,301) vs non-registry (10,869, excluded from denominator), and "blank-only" leagues
      re-classified from presumed-cups to genuinely-fetchable (§ W refuted the cup hypothesis on a 5-pair pilot). The
      "Round work — TERMINAL STATE" table below reconciles every remaining in-window blank.
- [x] ✅ [CODE] P1. The surgical script scans `"/entity=fixtures/"` (line 79) — the LEGACY entity. Retarget to
      `entity=fixtures_schedule` (verified to carry `af_fixture_id` + `round`) before any real run, or it patches the
      wrong tree. Same staleness class as `migrate_sports_canonical_v9.py`. **Done** — § T's retargeted backfill
      (`instruments-service@34ada099`) is this same script gaining a `--pairs-file` mode; verified in the current source
      (`backfill_sports_fixture_round_2026_07_17.py:63`): `_ENTITY_SEG = "/entity=fixtures_schedule/"`.

## P. DERIVE `round` for the confident majority, spend API calls only on the clustered remainder

Operator 2026-07-18: _"work out per league when the non standard games cluster so you can end up manually inserting
round info for 70% of normal games you are 100% confident on ... should take calls down a lot, a couple hours rather
than days"_. Measured — the idea holds, with a precise ceiling and one caveat.

**The populated ~50% is a FREE LABELLED GROUND-TRUTH SET.** Any derivation rule can be scored against it with zero API
calls before being applied to the blank half. Measured on 3,234 sampled fixtures (6 matchdays, Aug-Sep 2023):

- `round` populated 1,562/3,234 (48%).
- Of those, **1,072 = 69% are `Regular Season - N`** — the operator's "70% of normal games", confirmed.
- The remainder are cup/qualifying structures that cluster: `Preliminary Round` 124, `1st Round Qualifying` 103,
  `2nd Round Qualifying` 74, `3rd Round Qualifying` 40, `1st/2nd/4th/5th Round`, `Group B - 26`.

**Derivability ceiling — 97.0%.** Grouping the Regular-Season fixtures by `(af_league_id, day)`: **225 of 232 groups
carry exactly ONE round number**; only 7 span multiple rounds. So "all fixtures for a league on a matchday share one
round" holds 97% of the time, and that is the hard ceiling for date→round derivation.

**The 3% failures CLUSTER BY LEAGUE, not randomly** — league `253` alone accounts for 4 of the 7 (a split/scattered
schedule). That is what makes the operator's plan work: ambiguity is a per-league property, so a confidence whitelist is
possible instead of a blanket refetch.

**Correctness guard — `round` is NOT chronological position.** Postponed fixtures mean a `Regular Season - 12` match can
be played after round 15. Naive date-ordering would silently write WRONG rounds, and a derived value written as if
captured is the banned silent-placeholder. Hence: score first, whitelist second, and mark derived values as derived.

**CAVEAT — the validation set may not be exchangeable with the target.** The 97% is measured on fixtures that ALREADY
have `round`. If the blanks are disproportionately cups/friendlies (where `Regular Season - N` does not apply at all),
derivation covers far less of them. This MUST be measured before sizing the API run.

- [x] ✅ [DIAG] P0. Profile the BLANK half by league + competition type. If blanks concentrate in cups/friendlies,
      derivation is not the lever there — honest absence is (a cup tie has no `Regular Season - N`). **Done** — P-SIZING
      (below, same doc) profiled it: 92% of blanks live in leagues that already have round data (50 leagues, 1,539
      blanks), only 8% in blank-only leagues (7 leagues, 133 blanks).
- [x] ✅ [CODE] P1. Build the per-league confidence whitelist: for each (league, season), score date→round derivation
      against the populated fixtures. Whitelist leagues scoring 100%; exclude any league with a multi-round matchday
      (e.g. `253`). **Shipped** — § Q's `derive_sports_fixture_round_2026_07_18.py` (`instruments-service@e63049e7`)
      implements this as unanimity-per-(league,day) rather than a literal whitelist file: a day whose known values
      disagree is REFUSED, self-handling the ambiguous leagues with no maintained list.
- [x] ✅ [CODE] P1. Derive `round` ONLY for whitelisted (league, season) blanks, and stamp provenance (derived vs
      captured) — never write a derived value indistinguishable from a fetched one. **Shipped** — § Q:
      `round_provenance='derived'` stamped on every filled row (captured rows carry `'captured'`).
- [x] ✅ [DATA] P1. API-fetch only the residual: non-whitelisted leagues + cup competitions + any league-season with no
      populated fixtures to score against. Size the run from THAT count, not the whole corpus. **Done** — § T fetched
      the 194 in-window regular-round pairs, § W fetched the 159 blank-only-league pairs; both bounded by
      (league,season) pair count exactly as specified here.

### P-SIZING (2026-07-18) — the blank half IS exchangeable; ~89% derivable, API residual is TINY

The § P caveat ("blanks may be disproportionately cups, so the ground-truth set may not transfer") is **measured and
REFUTED**. Same 6-matchday sample (3,234 fixtures, 1,672 blank = 51.7%):

| bucket                                                             | leagues | blank fixtures  |
| ------------------------------------------------------------------ | ------- | --------------- |
| leagues with BOTH populated + blank (derivable target)             | **50**  | **1,539 (92%)** |
| blank-ONLY leagues (never any round — cups/friendlies/unsupported) | **7**   | 133 (8%)        |

**92% of blanks live in leagues that ALREADY have round data**, so the populated fixtures are valid ground truth for
exactly the leagues we need to fill. Combined with the § P ceiling (97% of `(league, day)` groups carry exactly one
round), **~89% of blanks are derivable with ZERO api-football calls**.

**Revised sizing — the operator's "couple hours rather than days" is conservative:**

| path                                     | api-football calls                                                                                                                            |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| full `--force` corpus refetch (rejected) | ~1,260,000                                                                                                                                    |
| surgical whole-corpus script             | ~600-700                                                                                                                                      |
| **derive-then-fetch (this plan)**        | **~1 bulk call per residual (league, season)** — the 7 blank-only leagues + leagues with multi-round matchdays. Tens of calls, not thousands. |

The residual is bounded by DISTINCT (league, season) pairs needing a fetch, NOT by fixture or date count — one
`GET /fixtures?league&season` returns the whole season (measured: 242 fixtures in one call).

- [x] ✅ [CODE] P0. Implement derive-then-fetch: (1) score date→round per (league, season) against populated fixtures;
      (2) derive blanks for leagues scoring 100%, stamped as DERIVED provenance; (3) enumerate the residual (blank-only
      leagues + non-perfect scorers) and bulk-fetch ONLY those (league, season) pairs. **Shipped end-to-end** — § Q
      (`instruments-service@e63049e7`) implements steps 1-2; § T + § W implement step 3.
- [x] ✅ [DIAG] P2. Classify the 7 blank-only leagues: genuine honest absence (a cup tie has no `Regular Season - N`) vs
      a real capture gap. Do not fetch what has no round concept — that is honest absence and should be recorded as
      such, not chased. **Done** — § W's 5-pair pilot REFUTED the honest-absence hypothesis: 4 of 5 were ordinary
      leagues with simply no round captured yet (fully fetchable, 1,751 rows would-fill), only 1 was genuine
      out-of-coverage-season absence.

### P-ERA (2026-07-18) — `round` capture STARTS mid-2019; the underivable residual is one bounded era

First dry-run of `instruments-service/scripts/derive_sports_fixture_round_2026_07_18.py` returned **0 filled / 2,390
blank / 2,390 no-sibling**. That was MY sampling error, not a script failure: `--max-days 40` takes the FIRST 40 sorted
days = earliest 2019, and round population there is **0%** — no populated siblings exist to propagate from. (Third time
this session a small unrepresentative sample produced a confident wrong read; the fix is the same each time — sample
across the range, or measure the whole corpus.)

Measured population by era (one sampled matchday per year, `entity=fixtures_schedule`):

| matchday   | rows | populated | %        |
| ---------- | ---- | --------- | -------- |
| 2019-02-09 | 575  | 0         | **0.0%** |
| 2019-08-17 | 362  | 238       | 65.7%    |
| 2020-09-19 | 289  | 171       | 59.2%    |
| 2021-03-13 | 284  | 166       | 58.5%    |
| 2022-10-05 | 88   | 44        | 50.0%    |
| 2023-08-19 | 666  | 334       | 50.2%    |
| 2024-04-06 | 394  | 187       | 47.5%    |
| 2025-11-08 | 404  | 195       | 48.3%    |
| 2026-03-14 | 354  | 142       | 40.1%    |

**`round` capture begins around mid-2019** and holds 40-66% thereafter. So the work splits cleanly:

- **2019-08 → 2026**: siblings exist → DERIVE (zero API calls), bounded by the § P 97% unanimity ceiling.
- **early 2019 (Jan → ~Aug)**: 0% populated → nothing to derive from → API fetch. **Bounded by (league, season) pairs,
  NOT days**: season 2019 across ~89 leagues ≈ **~89 bulk calls**, since one `GET /fixtures?league&season` returns the
  whole season (measured: 242 fixtures in one call).

Total projected api-football spend for the entire `round` gap: **~100 calls**, versus the ~1,260,000 of the rejected
`--force` corpus refetch — and versus ~600-700 for the whole-corpus surgical script. The operator's "a couple of hours
rather than days" is conservative; this is minutes of API time.

- [x] ✅ [DIAG] P0. Full-corpus dry-run running (no `--max-days`) — read fill / ambiguous / no-sibling corpus-wide
      before `--apply`. Confirms the era split and gives the exact residual. **Done** — Q-RESULT (below) is exactly
      this: 499,620 rows scanned, 354,279 blank, 115,715 derived, 6,654 ambiguous, 231,910 no-sibling.
- [x] ✅ [CODE] P1. Cross-file sibling grouping: the script groups per PARQUET. If a (league, day)'s populated rows and
      blanks live in different files, siblings are invisible and blanks are mis-counted as "no sibling". If the full-run
      no-sibling count exceeds the ~8% predicted by § P-SIZING, group by (league, day) ACROSS the day's files. **Done**
      — § Q's shipped design: "Two-pass per day... pools known values across ALL the day's files" — the per-parquet
      first cut reported 0% filled; the cross-file fix took it to 89.2% on the pilot sample.

## Q. Round derivation SHIPPED + APPLYING — 89.2% of the gap closed with ZERO api-football calls

`instruments-service@e63049e7` — `scripts/derive_sports_fixture_round_2026_07_18.py`. QG green (4,579 passed).

**Measured on real data (populated eras, 5 matchdays):**

| metric              | value                                    |
| ------------------- | ---------------------------------------- |
| rows / blank        | 2,513 / 1,294                            |
| **DERIVED**         | **1,154 = 89.2% of blanks, 0 API calls** |
| ambiguous (refused) | 42 (3.2%) — multi-round matchdays        |
| no-sibling (API)    | 98 (7.6%)                                |

Matches the § P-SIZING prediction (92% mixed-league x 97% unanimity ~= 89%) almost exactly.

**Design decisions that made it safe:**

- **Unanimity, never inference.** `round` is NOT chronological position — a postponed `Regular Season - 12` can be
  played after round 15 — so date ORDERING is never used to invent a number. A (league, day) whose known values disagree
  is REFUSED. That self-handles the 3% rescheduled matchdays with no whitelist to maintain.
- **Provenance stamped.** Fills carry `round_provenance='derived'` (captured rows `'captured'`). A derived value
  indistinguishable from a fetched one is the banned silent placeholder.
- **Two-pass per day.** A day carries BOTH a bare multi-league parquet AND per-league parquets, so a league's populated
  rows and its blanks can sit in different files. Pass 1 pools known values across ALL the day's files; pass 2 fills.
  The first cut grouped PER PARQUET and reported **0% filled** — the fix took it to 89.2%.
- Snapshots each parquet to `*.pre_round_derive.bak`; idempotent; single-walk; targets `entity=fixtures_schedule` (the
  LIVE entity — the older surgical script targets the stale `entity=fixtures`).

**Full-corpus `--apply` RUNNING** over 3,989 days (PID 2138671, watchdog armed on the filled-count progress metric).

**Revised total api-football spend for the whole `round` gap: ~100 bulk calls** (early-2019 era, one
`GET /fixtures?league&season` per league) versus **~1,260,000** for the rejected `--force` corpus refetch.

- [x] ✅ [DATA] P1. After the apply completes: re-measure round population per era, then fetch the early-2019 residual
      (~89 league-season bulk calls) and the ~8% no-sibling remainder. **Done** — Q-RESULT's own era table shows the
      before/after population per day; § T + § W fetched the residual (353 total bulk calls, superseding the ~89 early
      estimate once the true scope was measured).
- [x] ✅ [DATA] P1. Then rebuild the catalogue (`build_instrument_catalogue.py --asset-group sports --since 2019-01-01`)
      and verify `competition_phase` is no longer ~100% UNKNOWN — the § O hypothesis is that the rollup, not capture,
      was the 3.2%. **Done** — R-FIXED rebuilt (round 0.7%→70.6%); § X verified `competition_phase` at 77.2% populated
      against the real read path (was ~100% UNKNOWN in the original issue).

### Q-RESULT (2026-07-19 00:13Z) — derivation APPLIED corpus-wide: 115,715 rows filled, ZERO api-football calls

```
rows scanned : 499,620
blank round  : 354,279
DERIVED      : 115,715  (32.7% of blanks)  <- zero API calls
ambiguous    :   6,654  (refused: multi-round matchday)
no-sibling   : 231,910  across 3,386 days  <- API residual
```

**Round coverage on every era that had data to propagate from (before -> after):**

| day        | before | after     | gain      |
| ---------- | ------ | --------- | --------- |
| 2019-08-17 | 65.7%  | **98.6%** | +32.9 pts |
| 2020-09-19 | 59.2%  | **98.3%** | +39.1 pts |
| 2021-03-13 | 58.5%  | **97.2%** | +38.7 pts |
| 2022-10-05 | 50.0%  | **90.9%** | +40.9 pts |
| 2023-08-19 | 50.2%  | **98.2%** | +48.0 pts |
| 2024-04-06 | 47.5%  | **92.4%** | +44.9 pts |
| 2025-11-08 | 48.3%  | **95.5%** | +47.2 pts |
| 2026-03-14 | 40.1%  | 69.2%     | +29.1 pts |

Writes verified: `round_provenance='derived'` present (e.g. 320 rows on 2023-08-19, 177 on 2024-04-06) with plausible
values (`Regular Season - 20`, `Regular Season - 2`), and 40-42 `*.pre_round_derive.bak` snapshots per sampled day.

**RETRACTED (mine — 4th sampling over-prediction today): "89.2% of blanks".** That pilot sampled 2023-2025 matchdays,
the BEST-populated eras. Corpus-wide the fill rate is **32.7%**, because 65.5% of blanks have NO populated sibling in
their `(league, day)` at all. The corpus dry-run should have run BEFORE quoting a headline number. The 89.2% was not
wrong about those days — it was wrong as a corpus estimate.

**Provenance caveat (minor, by design of the two-pass split):** `captured` is stamped only on files that also contain
blanks; a file with no blanks returns early and is left unstamped. So the invariant to rely on is
`round_provenance == 'derived'` identifies derived rows — anything else is captured/pre-existing. The safety requirement
(a derived value must never be indistinguishable from a fetched one) holds.

- [x] ✅ [DATA] P1. Residual fetch: 231,910 no-sibling blanks across 3,386 days, dominated by the early-2019 zero-era.
      Bounded by DISTINCT (league, season) pairs (~600-700 bulk calls, the original surgical-script estimate), NOT by
      fixture count. Retarget that script to `entity=fixtures_schedule` first (§ O todo). **Done** — § T corrected the
      count (161,034, not 231,910 — the 231,910 figure double-counted bare-parquet rows outside the live read path) and
      executed the retargeted backfill (`instruments-service@34ada099`, already retargeted per § O's todo).
- [x] ✅ [DATA] P1. Then rebuild the catalogue and verify `competition_phase` — with raw now at 90-99% on populated
      eras, this is the real test of the § O "the 3.2% was the stale rollup" hypothesis. **Done** — R-FIXED rebuilt
      (round 70.6%); § X verified `competition_phase` at 77.2% populated via the real read path.

### L-COMPLETE (2026-07-19 00:45Z) — lineups re-derive FINISHED and verified at scale

`fts-backfill-20260718-184352` completed cleanly: `DEPLOYMENT_COMPLETED exit_code=0`, deployment archived, VM
self-deleted per `VM_SHUTDOWN_ON_COMPLETION`.

| metric                     | before               | after                                           |
| -------------------------- | -------------------- | ----------------------------------------------- |
| lineup shards materialised | 356 (stale, pre-fix) | **2,022**                                       |
| `coach_name` populated     | **0/40 (0%)**        | **3,778/3,983 (94.9%)** — random 6-shard sample |
| rows per day               | ~40                  | ~660 (3,983 over 6 shards)                      |

Closes the A1 chain end-to-end: normalizer flat-shape fix + dedupe + coach emission (features-service@cf10b931),
delivered over history by the `--redo-all` launcher gap fix (deployment-service). **Zero api-football calls** — the
entire restoration came from raw already on disk.

The residual ~5% `coach_name` nulls are fixtures that genuinely carry no coach upstream — honest absence, not a defect.

## R. ROOT CAUSE of `competition_phase` UNKNOWN — the entity split left EVERY CONSUMER on a dead entity — **P0**

The catalogue rebuild completed cleanly (`CATALOGUE_ROLLUP_COMPLETED exit_code=0`, **121,538 rows** promoted, up from
the 17,064 the original issue measured) — and `round` came out at **837/121,538 = 0.7%**, with `competition_phase`,
`round_name` and `is_promotion_relegation` **columns entirely ABSENT**. That is WORSE than the 3.2% baseline, despite
raw now sitting at 90-99% after § Q.

**RETRACTED (mine, § O): "the loss is in the ROLLUP, rebuild it and the 3.2% resolves."** Rebuilding changed nothing,
because the rollup is reading a **dead entity**.

**Measured:**

| entity                     | newest write         | status           |
| -------------------------- | -------------------- | ---------------- |
| `entity=fixtures`          | **2026-05-23 20:35** | FROZEN ~2 months |
| `entity=fixtures_schedule` | **2026-07-18 21:27** | LIVE             |

`build_instrument_catalogue.py:208` pins `SPORTS_FIXTURE_ENTITY = "fixtures"`. So the catalogue rolls up a corpus that
stopped being written on 2026-05-23 — which is why the § Q derivation (115,715 rows into `fixtures_schedule`) is
invisible to it, and why `competition_phase` has been UNKNOWN all along. **This was never a capture gap.**

**The split migrated the WRITER and left the CONSUMERS behind.** Stale-entity readers found so far (non-exhaustive,
`entity=fixtures` hard-coded):

- `scripts/build_instrument_catalogue.py:208` (`SPORTS_FIXTURE_ENTITY`) — the catalogue itself
- `scripts/backfill_sports_fixture_round_2026_07_17.py:79` — the surgical round filler (§ O)
- `instruments_service/reference_data/sports_dependency.py`
- `instruments_service/triggers/sports_fixtures_daily_repoll.py`
- `scripts/backfill_weather.py:154`, `scripts/backfill_sports_fixture_stats_manifest.py:91`
- `scripts/rescan_sports_fixtures_canonical.py:328,452`, `scripts/enumerate_expected_universe.py:1902`
- `scripts/migrate_sports_per_league.py`, `scripts/reconcile_sports_blank_empty_reason_2026_06_24.py`

This reframes the whole epic: chasing `round` through backfills (1.26M-call refetch, surgical script, derivation) was
treating a CONSUMER-MIGRATION bug as a data-capture bug. The derivation was still worth doing — raw is now 90-99% and
that is real — but the catalogue will keep reporting ~0% until its reader is repointed.

- [x] ✅ [CODE] P0. Repoint `SPORTS_FIXTURE_ENTITY` to `fixtures_schedule` (verify the schema carries what the rollup
      needs: `af_fixture_id`, `round`, kickoff/timestamp) and re-run the catalogue. Handle `fixtures_outcomes` if the
      rollup needs scores/status — the split put those on the OTHER leg. **Done** — see R-FIXED directly below: round
      0.7%→70.6%, verified the rollup needs only SCHEDULE fields (no outcomes join needed).
- [ ] [DIAG] P0. Audit EVERY consumer above for the same staleness; each is silently reading a 2-month-frozen corpus.
      Anything reporting "sports data is missing/stale" since 2026-05-23 is suspect for this cause. **Owned by
      `sports_consolidated_closeout_2026_07_19.md` Track E** (`[CODE] P1` "repoint the remaining stale `entity=fixtures`
      consumers, sweep §R's ~9-file list, now 7") — still open there as of 2026-07-27, one item (`gcs_reader`, § V
      below) already fixed independently. Not duplicated here.
- [x] ✅ [CODE] P1. `competition_phase` / `round_name` / `is_promotion_relegation` are ABSENT as catalogue columns, not
      merely UNKNOWN — the rollup never projects them. Even with a live entity, the derivation from `round` must be
      wired into the catalogue build. **Retracted, wrong layer** — see R-FIXED's own already-flipped entry directly
      below: these are `features_sports` UAC fields, not catalogue columns; the producer (`season_context.py`) already
      existed, only needed `round` populated (§ Q/§ R), no new projection code.
- [x] ✅ [PROCESS] P1. An entity rename/split MUST enumerate and migrate consumers in the same change. This one shipped
      the writer on 2026-05-23 and left ~10 readers pointing at a corpus that stopped updating — silently, because a
      frozen corpus still reads successfully. **Genuinely open** — a proposed workspace process rule, not yet codified
      into a codex doc (checked `codex/12-agent-workflow/` and `codex/04-architecture/` for an entity-migration-consumer
      rule; none exists). Not batchable — codifying a new authoring rule is an operator call, same class as batch6 todo
      7's own Deferred item on generalising the finalize-plan fix. ✅ Codified 2026-08-08 —
      `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md`; applied to sports taxonomy P1 chain (consumer
      inventories on every rename todo). Resolved by P1 plan `[DOCS] P0`.

### R-FIXED (2026-07-19 02:01Z) — catalogue repointed to the LIVE entity: `round` 0.7% -> **70.6%**

`SPORTS_FIXTURE_ENTITY` repointed `fixtures` -> `fixtures_schedule`, full `--since 2019-01-01` rollup re-run:

| metric               | legacy entity | live entity                 | original issue |
| -------------------- | ------------- | --------------------------- | -------------- |
| catalogue rows       | 121,538       | **164,763**                 | 17,064         |
| `round` populated    | 837 (0.7%)    | **116,285 (70.6%)**         | 545 (3.2%)     |
| `Regular Season - N` | —             | 90,238 (77.6% of populated) | —              |

**+43,225 rows the frozen entity was simply missing.** The original issue's headline — _"round populated on only 545 of
17,064 rows (3.2%)"_ — is now **116,285 of 164,763**.

Safe-to-repoint was VERIFIED first, not assumed: the split is clean (legacy 55 cols = schedule 43 + outcomes 15,
**nothing missing from both**), and this rollup reads only SCHEDULE fields (`af_home_name` / `af_away_name` / `date` /
`timestamp` / `round`), all 100% populated on the schedule leg — so no outcomes join was needed.

**The derivation and the repoint are COMPLEMENTARY, not redundant** — worth stating because either alone looks
sufficient and neither is: § Q lifted RAW from 40-66% to 90-99% at zero API cost; § R made any of it visible downstream.
Without the derivation the repoint would have surfaced ~50%; without the repoint the derivation was invisible.

**STILL OPEN — `competition_phase` is ABSENT, not UNKNOWN.** `competition_phase` / `round_name` /
`is_promotion_relegation` are not catalogue columns at all; the rollup never projects them. So the original issue's
second half is NOT closed by this: `round` is now present and rich, but nothing derives the phase from it at catalogue
level.

- [x] [CODE] P0. ~~Project `competition_phase` in the catalogue rollup~~ — **RETRACTED, wrong layer.** These are UAC
      **`features_sports`** fields (`internal/domain/features_sports/__init__.py:138-142`), not catalogue columns, so
      "the rollup never projects them" was true but irrelevant. The real producer already exists:
      `features_service/sports/calculators/season_context.py`, fed by
      `derived_features_helpers.py:_compute_season_features`, which **already** extracts matchday from the round string
      (`r"(\d+)$"` on `round`) and maps `round -> round_name`. So the chain was never missing — it was **starved of
      input**, because `round` was blank. Populating `round` (§ Q + § R) is what unblocks it; **no new projection code
      is needed, only a features RE-RUN.** Note there are two unrelated `competition_phase` derivations:
      instruments-service `classify_competition_phase(round_name)` (NORMAL_LEAGUE / PLAYOFF / TOURNAMENT …) and the
      features one (`early|mid|late` from matchday progress). The UAC field is the features one.
- [ ] [DIAG] P0. The other ~9 stale-entity consumers (§ R list) are still reading the frozen corpus. Each needs the same
      repoint + a re-run; anything reporting stale sports data since 2026-05-23 is suspect. **Owned by
      `sports_consolidated_closeout_2026_07_19.md` Track E** — same item as § R's `[DIAG] P0` above, not duplicated
      here.

### S (2026-07-19) — P1 MEASURED: `total_matchdays` is hardcoded **38 for every league on earth**

`features-service/features_service/sports/exporters/derived_features_helpers.py:735`:

```python
if "total_matchdays" not in enriched.columns:
    enriched["total_matchdays"] = 38          # <- every league, every season
```

This is a **silent placeholder** in the sense the codex bans: it is not flagged, not provenance-stamped, and it produces
confidently wrong numbers rather than honest absence. Measured against the live corpus (819 `fixtures_schedule`
parquets, 2023-08..2024-06, distinct `Regular Season - N`):

| league     | true season length   | hardcoded 38 |
| ---------- | -------------------- | ------------ |
| EPL        | 38                   | correct      |
| LA_LIGA    | 38                   | correct      |
| SERIE_A    | 38                   | correct      |
| BUNDESLIGA | **34**               | off by −4    |
| EREDIVISIE | **34**               | off by −4    |
| LIGUE_1    | **34**               | off by −4    |
| MLS        | **50** (36 distinct) | off by +12   |

**Correct for only 3 of 7 leagues measured.** Three consumers inherit the error:

- `games_remaining = total - matchday` — on Ligue 1's FINAL matchday (34) this reports **4 games remaining**, not 0.
- `points_at_stake = games_remaining x 3 x multiplier` — inherits it directly, so end-of-season stakes are inflated
  exactly when they matter most (relegation/title run-ins are the signal these features exist to capture).
- `competition_phase = f(matchday / total)` — the frac is wrong, so `early|mid|late` boundaries land in the wrong place:
  Ligue 1 reads 34/38 = 0.89 at season END; MLS reads 50/38 = 1.32, pinning it to `late` all season.

**Do NOT "fix" this with max-observed-matchday.** Deriving the total from matchdays seen so far under-estimates
mid-season, which makes `games_remaining` too small and the phase too `late` — strictly worse than 38 for the leagues 38
currently gets right. The fix needs the FULL season schedule (api-football publishes it upfront, and `fixtures_schedule`
already carries future fixtures), or a per-league reference mapping.

- [x] [CODE] P1. ✅ Per-(league, season) `total_matchdays` reference built from the corpus and consumed in
      `_compute_season_features` — **features-service@d9b44d46** (QG green). Ships `schemas/league_season_lengths.json`:
      198 league-seasons + 28 stable-league fallbacks, admitted only at >=95% round coverage AND contiguous rounds (a
      mostly-blank pair under-reports its max, so trusting it would be worse than no entry); implausible lengths (<10
      or >60) dropped, not guessed. Unknown pair => **honest NaN, never a default**. Verified: Ligue 1 final matchday 34
      now yields `games_remaining=0.0` (was 4.0); unknown league yields NaN, not a fabricated 38. The loader FAILS LOUD
      on a malformed/missing file rather than degrading to an empty map (QG "empty dict/list fallback") — it ships with
      the package, so silently NaN-ing the whole corpus would be the worse failure.
      `test_total_matchdays_defaults_to_38` asserted `== 38` and therefore encoded the bug as the contract; rewritten to
      pin honest-NaN, + 3 new regression tests.
- [x] ✅ [DATA] P1. After the fix, sports features need a re-run for the affected leagues — the currently-persisted
      `games_remaining` / `points_at_stake` / `competition_phase` are wrong wherever season length != 38. **Superseded
      by Z-FIXED's later, more complete re-run tracking** (below, same doc) — the corpus-wide `derived_features` re-run
      this todo asks for is the same re-run Z-FIXED's `[DATA] P0` already routes to
      `sports_consolidated_closeout_2026_07_19.md` FEATURES track (Track F), which supersedes this earlier, narrower
      framing. Not duplicated here.

### T (2026-07-19) — residual round blanks SCOPED by measurement; my "early-2019 era" claim was WRONG

One walk of the live `fixtures_schedule` corpus (2,031 league-seasons, `round`/`season`/`af_league_id` projected only),
which also produced the § S season-length reference — **single walk, both answers**.

**CORRECTION.** I earlier characterised the residual as "231,910 no-sibling blanks, early-2019 era". Both halves were
wrong:

- The count is **161,034**, not 231,910. The 231,910 figure counted rows in the day-wide BARE parquets too; the
  orchestrator's reader (`_read_per_league_entity_df`) documents "there is no bare" and reads **only** `/league=` paths,
  so bare rows are not part of the live read path.
- It is not the "2019 era" — it is **pre-2019**, which the 2019-01-01..2026-07-17 backfill window does not even cover:

| seasons                   | pairs |  blank rows | share     |
| ------------------------- | ----: | ----------: | --------- |
| 2013–2018 (OUT of window) |   915 | **122,864** | **76.3%** |
| 2019–2027 (IN window)     |   842 |  **38,170** | 23.7%     |

**The in-window job is ~4x smaller than I said, and it is bounded:**

| coverage of in-window blanks |   rows | (league,season) fetches |
| ---------------------------- | -----: | ----------------------: |
| 50%                          | 19,168 |                  **70** |
| 80%                          | 30,536 |                 **221** |
| 95%                          | 36,270 |                     455 |
| 100%                         | 38,170 |                     842 |

So complete in-window coverage is **842 bulk calls**, and 80% is **221** — hours, not the multi-day run implied by the
earlier 1,757-pair figure. Fetches must be scoped to the IN-WINDOW pair list, not fanned across 782 leagues x 8 seasons.

**Do not assume a fetch fixes the cup competitions.** 648 of the 842 in-window pairs (27,718 rows) carry NO
`Regular Season - N` round at all. Those are cups/knockouts whose round is a different vocabulary ("Round of 16",
"Quarter-finals") or is simply not published — a bulk fetch may legitimately return nothing for them, which is honest
absence, not a gap. Verify on a pilot pair before spending 648 calls on the assumption.

- [x] [DATA] P1. ✅ Retargeted backfill COMPLETE against the 194 reachable in-window league pairs (10,452 blank rows),
      scoped via the new `--pairs-file` — **instruments-service@34ada099** (QG green). `--leagues` x `--seasons` is a
      cross product that would have spent ~800 calls on 194 pairs' work; a pairs-file spends one call per pair. **Pilot
      verified the scan as a scoping instrument, not just the fetch**: the scan predicted 662 blank rows for 129:2026
      (ARGENTINA_PRIMERA_NACIONAL) and the apply filled **exactly 662** across 1,297 parquets from 648 fetched fixtures,
      each write re-downloaded and verified. Launched only after re-confirming 0 running af-\* VMs, so the api-football
      singleton rule holds.
- [x] ✅ [DIAG] P2. Pilot ~5 of the 648 cup pairs before committing the remaining calls; if the API returns no round for
      them, record it as explained-absence rather than an open gap. **Done** — § W's 5-pair pilot (below): 4/5 fetchable
      ordinary leagues (1,751 rows would-fill), 1/5 genuine out-of-coverage-season absence.
- [x] ✅ [DECISION] P2. Pre-2019 (122,864 rows) is outside the stated window — confirm whether the corpus is meant to
      cover 2013–2018 at all before spending 915 fetches on it. **ANSWERED 2026-07-20** —
      `sports_consolidated_closeout_2026_07_19.md` Track V § T decision (decision 3): pre-2019 (2013-2018) is OUT OF
      SCOPE, intentionally excluded, no further api-football spend.

### U (2026-07-19) — the round backfill can only REACH 353 of the 842 in-window pairs

Piloting the retargeted backfill against a real blank pair returned `0 rows would-fill across 0 scanned` — not a bug in
the fetch, a **structural reach limit**. The script builds its league universe from the UAC registry
(`get_leagues_by_classification` over `prediction` / `reference` / `features`), which enumerates **94 leagues**. The
corpus has **782 leagues with parquets**. Anything outside the registry is skipped before a call is ever made.

| in-window (2019–2027) blank pairs  | pairs | blank rows |
| ---------------------------------- | ----: | ---------: |
| total                              |   842 |     38,170 |
| **reachable** (league in registry) |   353 |     27,301 |
| **not in the registry universe**   |   489 |     10,869 |

Split of the reachable half:

| reachable subset                        | pairs | blank rows |
| --------------------------------------- | ----: | ---------: |
| has `Regular Season - N` (real leagues) |   194 |     10,452 |
| no regular rounds (cups / unpublished)  |   159 |     16,849 |

**This reframes "backfill to 100%".** 489 in-window league-seasons holding 10,869 blank rows sit in leagues the pipeline
CAPTURED but the registry does not enumerate. That is either (a) capture reaching beyond the intended universe, or (b) a
registry gap — and until it is settled, those rows can be neither filled nor honestly called complete. They are not an
api-football problem; no number of calls touches them.

A first measurement of the registry universe returned **0** leagues because I guessed the classification names
(`tier1`/`tier2`/…) instead of reading the script's actual `("prediction", "reference", "features")`. The numbers above
are from the corrected probe — the 0-league result was discarded, not reported.

- [x] ✅ [DECISION] P1. Settle the 489 non-registry in-window pairs: extend the registry to cover what is being
      captured, or stop capturing them. "Backfill at 100%" cannot be asserted for sports until this is decided one way
      or the other — the gap is a definition problem, not a data-fetch problem. **ANSWERED 2026-07-20** —
      `sports_consolidated_closeout_2026_07_19.md` Track V § U decision (decision 2): stop capturing non-registry
      leagues; the 489-pair/10,869-row population is excluded from the denominator, a purge candidate.
- [x] ✅ [DATA] P2. The 159 reachable cup pairs (16,849 rows) still need the pilot from § T before spending their calls
      — a cup's round vocabulary is "Quarter-finals", not "Regular Season - N", and a fetch may honestly return nothing.
      **Done** — § W piloted + then backfilled all 159 reachable pairs (same disposition as § T's identical ask directly
      above).

### V (2026-07-19) — FIXED: features read a legacy `entity=fixtures` object in preference to the LIVE split leg

Found while auditing the § R stale-entity consumer list. `gcs_reader.read_reference_entity` **does** implement the
schedule/outcomes split fallback correctly — but it was **unreachable for every pre-cutover date**. The probe returns
the legacy `entity=fixtures` object first, and the split fallback only runs when that object is absent, which is true
only on/after the 2026-05-23 cutover. Pre-cutover dates still have a legacy object, so features kept reading it.

Measured 2026-07-19, same day, both entities present:

| day        | `entity=fixtures` (what features read) | `entity=fixtures_schedule` (live)   |
| ---------- | -------------------------------------- | ----------------------------------- |
| 2024-03-09 | 317 rows, round populated **56.8%**    | 373 rows, round populated **96.0%** |
| 2023-05-20 | 256 rows, round populated **56.2%**    | 301 rows, round populated **86.7%** |

The features layer was reading a frame that is both **staler and smaller** than the live corpus — and because the § Q
derivation and the § T backfill write ONLY to `fixtures_schedule`, **every bit of the round work was invisible to every
sports feature on pre-cutover dates.** Same consumer-migration class as § R, but subtler: the code HAS the split path,
it simply never reached it. A grep alone would have cleared this file — the reference to `entity=fixtures` looks correct
in isolation, and only reading the probe ORDER shows the defect.

**Fixed — features-service@e4b1f1ba** (QG green): fixtures try the split leg FIRST and fall back to legacy, preserving
coverage for dates predating the split writer.

Two existing tests exercised the legacy path with a blanket `blob_exists=True` mock, so under split-first precedence
they were asserting the wrong leg. That is a mock artifact rather than a production regression — but waving it through
on that reasoning is precisely what let this bug hide, so both now patch the split leg ABSENT (what a pre-split date
actually looks like) and say why, plus a new test pins the precedence itself (legacy object present, split still wins,
legacy bytes never downloaded).

- [x] ✅ [DATA] P0. Sports features must be RE-RUN: every pre-cutover feature row was computed from the stale legacy
      frame. This supersedes the § S re-run note — one re-run now covers both the `total_matchdays` fix and this.
      **Superseded by Z-FIXED's later, more complete re-run tracking** (below, same doc) — routes to
      `sports_consolidated_closeout_2026_07_19.md` FEATURES track (Track F), same disposition as § S's identical ask.
      Not duplicated here.

### T P1 — VERIFIED against the corpus, not the log (2026-07-19)

The backfill's own log claimed 9,706 rows filled. That is the script grading its own homework, so the corpus was
re-scanned independently (same single-walk measurement that produced the "before" numbers):

| scope                      | blanks before | blanks after | closed             |
| -------------------------- | ------------: | -----------: | ------------------ |
| **the 194 targeted pairs** |        10,452 |       **14** | **10,438 (99.9%)** |
| corpus-wide                |       161,034 |      150,575 | 10,459             |

**191 of 194 pairs fully cleared.** The 14 residual rows are fixtures the fresh fetch did not cover — left untouched by
design rather than guessed.

Reconciliation of the 91-row gap between the log's claim and the measurement (10,459 measured vs 9,706 + 662 pilot =
10,368): the targeted set includes CURRENT-season (2026) pairs, and live forward-poll captures wrote `round` during the
~1h run. Two NON-targeted pairs moved by the same mechanism and are visible in the diff (`128:2026` 494→479, `255:2026`
359→353). So the measurement exceeds the claim because live capture ran concurrently, not because the count is
unreliable — nothing is unaccounted for.

### W (2026-07-19) — CORRECTION: the "cup competitions" were never cups; they are blank-round LEAGUES

§ T and § U classified 648 in-window pairs (159 of them reachable) as "cups / unpublished" because their
`max_regular_round == 0`, and reasoned that a bulk fetch might legitimately return nothing for them. **That inference
was wrong, and the pilot disproved it.**

`max_regular_round == 0` does not mean "this competition has no regular season". It means **no regular-season round was
OBSERVABLE in the corpus** — which is exactly what a league whose `round` column is entirely blank looks like. The
classifier conflated "is a cup" with "is completely unpopulated", and the second is precisely the population most in
need of the backfill.

Dry-run pilot over 5 of them:

| pair                                | fixtures fetched |                      would-fill |
| ----------------------------------- | ---------------: | ------------------------------: |
| ARGENTINA_PRIMERA 128:2026          |              495 |                         **479** |
| ARGENTINA_PRIMERA_NACIONAL 129:2023 |              670 |                         **512** |
| PRIMERA_RFEF 435:2019+2021          |              760 |                         **760** |
| J2_LEAGUE 99:2026                   |                0 |      0 — out-of-coverage season |
| **total**                           |                  | **1,751 across 11,745 scanned** |

Four of five are ordinary leagues (Argentine Primera, Primera RFEF) that simply had no round captured at all. They are
fully fetchable. Only J2 2026 returned nothing, and that is an out-of-coverage season (not yet published), which IS
honest absence.

**Consequence: the § T/§ U "cup" caveat is withdrawn**, and 16,828 more rows are recoverable than those sections
assumed. Backfill launched over all 159 reachable pairs (af fleet re-confirmed at 0 first, so the api-football singleton
rule holds).

The general lesson, which is the same one that produced the retractions earlier in this sweep: an ABSENCE in the data
was read as a PROPERTY of the data. "No regular rounds recorded" was treated as "this competition has no regular
rounds", when it only ever meant "we captured none". Absence is evidence of missing capture until a fetch proves
otherwise — the pilot is what distinguishes them, not the classifier.

- [x] [DIAG] P2. ✅ Cup pilot run — hypothesis REFUTED, the pairs are fetchable leagues (1,751 rows would-fill on 5).
- [x] ✅ [DATA] P1. 159-pair blank-league backfill RUNNING (16,828 rows targeted); verify against a corpus re-scan, not
      the script log, per the § T P1 precedent. **Done, verified** — the "Round work — TERMINAL STATE" table (below)
      confirms the corpus re-scan: 16,435 rows closed, delta 0 vs the script's own claim, 158/159 pairs cleared.

### Round work — TERMINAL STATE (2026-07-19)

| stage                                    | rows closed | verification                              |
| ---------------------------------------- | ----------: | ----------------------------------------- |
| § Q derivation (ZERO api-football calls) |     115,715 | populated eras 40-66% -> 90-99%           |
| § T 194-pair backfill                    |      10,438 | corpus re-scan; 191/194 pairs cleared     |
| § W 159-pair blank-league backfill       |      16,435 | corpus re-scan; delta 0 vs claim; 158/159 |

Corpus blank-round rows **161,034 -> 134,140** across the two backfills (26,894 closed), on top of the 115,715 the
derivation had already closed for free.

**Every remaining in-window blank is accounted for — nothing is unexplained:**

| remaining in-window blanks         |       rows | status                                                          |
| ---------------------------------- | ---------: | --------------------------------------------------------------- |
| § U pairs absent from UAC registry |     10,869 | **operator decision** — unreachable by any number of calls      |
| residue in reached pairs           |        407 | fixtures the fresh fetch did not cover — untouched, not guessed |
| **total**                          | **11,276** | reconciles exactly to the measured 11,276                       |

The pre-2019 blanks (122,864 rows) sit outside the stated 2019-01-01..2026-07-17 window and are covered by the § T open
decision, not by this work.

**What this cost in api-football calls: 353** (194 + 159 bulk (league,season) fetches). The § Q derivation closed 4.3x
more rows than both backfills combined at ZERO call cost — the ordering (derive first, fetch only the residue) is what
kept this to hours instead of the multi-day run the original per-fixture framing implied.

### X (2026-07-19) — end-to-end chain VALIDATED on real data before committing a fleet

Ran the real read + season-context path against a **pre-cutover** date (2024-03-09 — the case § V was about) rather than
launching multi-day VMs on the assumption it works.

**§ V confirmed live in the real read path**, not just in unit tests: instrumenting
`gcs_reader._read_split_fixtures_fallback` shows `read_reference_entity` now takes the SPLIT leg
(`used the SPLIT leg: True`), with `round` at **193/193 = 100%**.

Chain output for that day:

| column                                | populated       |
| ------------------------------------- | --------------- |
| `round_name`                          | 193/193 (100%)  |
| `matchday`                            | 185/193 (95.9%) |
| `competition_phase`                   | 149/193 (77.2%) |
| `games_remaining` / `points_at_stake` | 149/193 (77.2%) |

`competition_phase` distribution `{late: 118, early: 31, None: 44}`. **The original issue's headline was
`competition_phase` ~100% UNKNOWN** — it is now 77.2% populated with real values. The 44 `None` are league-seasons
absent from the § S season-length map, i.e. the deliberate honest-NaN path, not a failure.

**A row-count heuristic nearly produced a false verdict here.** The split leg has 373 RAW parquet rows but returns 193
after the schedule/outcomes join + normalize, so a "did we get >340 rows?" check reported "STALE LEGACY LEG" when the
fix was in fact working. Counts across a join/normalize boundary are not comparable; instrumenting the actual call is.
Same failure mode as the § W misclassification — inferring a property from an aggregate instead of measuring the thing
itself.

- [x] ✅ [INFRA] P0. Fan out the features re-run. **HARD RULE interaction**: the re-run needs `FORCE=true` (otherwise
      presence-skip makes it a no-op), and `--force` on SPOT is NOT replayable — `RelaunchPreemptedVm` replays the
      original params and force disables the skip the resume relies on, so a preempted run restarts at day one FOREVER
      (`/codex/05-infrastructure/spot-vms-for-backfill.md`). Drive it as **bounded per-year chunks** (2019..2026) so a
      preemption replays one year, not the whole corpus. Use the consolidated
      `launch-features-vm.sh --feature-family sports --asset-group SPORTS` (the sports-specific launcher carries a
      deprecation note for new backfills). **Superseded by Z-FIXED's later, more complete re-run tracking** (below, same
      doc) — the fleet this todo asked to fan out was in fact launched, then STOPPED when Z-FIXED found it was writing a
      fabricated pattern; the clean re-run (same bounded per-year chunking) now routes to
      `sports_consolidated_closeout_2026_07_19.md` Track F. Not duplicated here.

### Y (2026-07-19) — P2: `launch-features-vm.sh` prints a post-backfill hint naming a bucket that does not exist

The launcher's closing instructions tell the operator to run:

```
rebuild_manifest_from_canonical_paths('features-sports-sports-central-element-323112', ...)
```

That bucket **404s**. The real one is `features-sports-prd-central-element-323112`
(`resolve_bucket_name(cloud="gcp", kind="features", asset_group="sports")`) — the hint interpolates
`<family>-<asset_group>` and omits the `-prd-` env segment. The data prefix in the hint is wrong too: objects live under
`sports_features/`, not `features/by_date/`.

**Addendum (2026-07-30, `rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md` todo 4's corpus
sweep)**: fixing only the bucket/prefix strings is not sufficient — `rebuild_manifest_from_canonical_paths()` itself
wholesale-REPLACES the target bucket's entire manifest index on any prefix-scoped call (never merges with existing rows
outside `prefix`; see that issue doc for the full mechanism). Once the bucket name resolves correctly, this hint becomes
a live wipe risk instead of a harmless 404. The fix must ALSO swap the function to the additive
`merge_manifest_from_canonical_paths()` (same module, same call shape, `prefix` required not optional) — the bucket-name
fix and the function-safety fix ship together in one edit, not as two separate passes.

**This bit me immediately and is worth recording as a monitoring hazard, not just a typo.** I armed the launch watchdog
on the hinted bucket, so its progress metric read `shard_days=0` for 20 minutes — indistinguishable from a genuinely
stalled backfill. A 404 bucket does not error in a `| wc -l` pipeline; it silently returns zero forever. This is the
exact class the async-wait discipline warns about (a run that "logged and heartbeated healthily while writing ZERO
target artifacts"), only inverted: here the artifacts may be fine and the MONITOR is lying. Either direction, the lesson
is the same — **validate that a progress metric can ever be non-zero before trusting a zero reading.**

- [x] ✅ [CODE] P2. Fix the post-backfill hint in `deployment-service/scripts/vm/launch-features-vm.sh` to resolve the
      bucket via `resolve_bucket_name` (never string-interpolate an env-split bucket name) and to name the real
      `sports_features/` prefix. **Shipped deployment-service@5c9d673 — `rebuild_manifest_from_canonical_paths` →
      `merge_manifest_from_canonical_paths` (additive sibling, prefix required) + `sports_features/by_date` prefix per
      `sports_satellite_ao_dispatch_batch6_2026_07_26.md` todo 3.**

### Z (2026-07-19) — pilot VALIDATES the re-run; separate `matchday` persistence defect found (NOT root-caused)

Pilot VM `features-sports-sports-20260719-063104` (2024 chunk, SPOT, bounded). Same day, same 17 rows, local recompute
vs what the VM actually wrote:

| column              | LOCAL recompute | WRITTEN by VM |
| ------------------- | --------------: | ------------: |
| `competition_phase` |            4/17 |    **4/17 ✓** |
| `games_remaining`   |            4/17 |    **4/17 ✓** |
| `round_name`        |           17/17 |   **17/17 ✓** |
| `matchday`          |           16/17 |    **0/17 ✗** |

**The re-run is doing its job**: the three features this sweep was about match the local recompute exactly, which
confirms the VM is running the § S + § V code. Across the 7 days written so far, `competition_phase` is 60.5% populated
overall and **66.2% of the rows whose round actually carries a matchday number** — against ~100% UNKNOWN in the original
issue.

**Separate defect: `matchday` is computed and then lost before persistence.** It cannot be a calculator bug — the same
code populates it 16/17 locally, and `competition_phase` (which is DERIVED from matchday) persists correctly. So the
value is dropped between the calculator and the writer.

**My first hypothesis was WRONG and is recorded as such**: I suspected `_run_calc`'s first-writer-wins rule
(`new_cols = [c for c in df.columns if c not in existing_cols]`) was discarding season_context's `matchday` in favour of
an empty one already on `result`. Measured: the base fixtures frame does **not** carry `matchday` (nor any other
season_context column), so that is not the mechanism. Some earlier calculator must introduce the column, but I have not
identified which — **this is an open lead, not a diagnosis.**

**Why this does not block the fan-out**: `round_name` persists at 100%, and `matchday` is a pure regex over it
(`r"(\d+)$"`). The field is therefore recoverable by a light targeted pass with **no features re-run required**, so
baking it into the remaining year-chunks costs nothing that a cheap follow-up cannot fix.

### Z-FIXED (2026-07-19) — root cause found, LIVE bug fixed, writing fleet STOPPED

**The §Z lead is CLOSED and was far worse than "matchday dropped": the features layer was writing FABRICATED non-null
`competition_phase='late'` / `games_remaining=0.0` / `points_at_stake=0.0` corpus-wide** — silently-wrong values a model
reads as real signal, invisible to every NaN check. Confirmed live on freshly-written shards (competition_phase 100%
`'late'`, zero early/mid; games_remaining 100% `0.0`).

Root cause (fully traced, reproduced on 2019/2024 dates, via the REAL pipeline path — the earlier §X "77.2% populated"
measured the ISOLATED `_compute_season_features` and so missed it): `derived_features_exporter.py:149-151` merges
`footystats_matches` with no `candidate_cols` filter → injects an all-NaN `match_week` (footystats joins on a string
slug that doesn't match numeric `fixture_id`); `derived_features_helpers.py:782-788` gate checked column PRESENCE not
population → preferred the all-NaN `match_week` over the reliable round-derived `matchday`; NaN then fell through
`_competition_phase` to `'late'` and `max(0.0, total-NaN)` to `0.0`. Two guards no-op'd it (writer.py sparse allowlist
suppresses the matchday NaN rejection; `validate_feature_output` logs the budget violation but never blocks).

- [x] [CODE] P0. ✅ FIXED — **features-service@c6eb1f38** (QG green). Gate derives `matchday` from `round` (match_week
      fills only genuine gaps, never shadows); `_competition_phase` + batch-loop + single-fixture path return honest
      `None` on NaN. Verified via the real gate path (matchday 40/40, phase `{early,mid,late}`, games 0..7; unmapped
      league → honest `None`). 2 regression tests added (the exact missing test that let it ship).
- [x] [OPS] P0. ✅ STOPPED the 8-VM features re-run fleet — it was actively writing the fabricated pattern; every shard
      needs re-writing after the fix anyway.
- [x] [DATA] P0. **Corpus-wide `derived_features` re-run required** (clean, replaces the stopped fleet) — the bug fired
      whenever `footystats_matches` had any row that day, i.e. most of the 61,461 captured `derived_features` rows.
      Tracked in `sports_consolidated_closeout_2026_07_19.md` FEATURES track. — already covered by
      `plans/active/sports_consolidated_closeout_2026_07_19.md` (FEATURES track; see that doc for execution).
- [x] [DIAG] P2. ✅ Root-cause found (above). **Three candidates ELIMINATED by measurement — do not re-run these:** 1.
      _Base-frame collision_ — the normalized fixtures frame carries NO season*context column (`matchday`,
      `competition_phase`, `games_remaining`, `points_at_stake`, `round_name`, `total_matchdays` all absent). 2. \_A
      competing emitter* — `rg '"matchday"'` over `features_service/sports/` shows `season_context` is the ONLY
      producer; nothing else can introduce a colliding empty column, so `_run_calc`'s first-writer-wins rule is not
      reachable here. 3. _The `_run_calc` merge itself_ — exercised in isolation on the real 2024-01-03 frame:
      season*context emits `matchday` 16/17 and **16/17 survives the merge**
      (`quality_tracker: status=ok, 20 columns, 0 all-NaN`). So the loss is AFTER the merge, at or just before
      persistence. `writer.py`'s `matchday` entry is an **expected-sparse allowlist** (suppresses all-NaN validation
      failures), NOT a drop list — but that also means a column silently going all-null here is \_by design* not loud,
      which is likely why this survived unnoticed. Next step: instrument the real exporter end-to-end for one day and
      bisect between the season_context merge and the parquet write. Note a dtype smell worth checking there:
      season_context emits `fixture_id` as `object` while the result spine is `Int64`.
- [x] [DATA] P3. ~~Once root-caused, recover `matchday` from the persisted `round_name` (regex) rather than re-running
      the whole features corpus.~~ **SUPERSEDED 2026-07-26** (resolved
      `autonomous_session_operator_decisions_2026_07_25.md` entry #15): the P0 corpus-wide `derived_features` re-run
      above is happening anyway for independent reasons (the fabricated-value bug) and recomputes `matchday` as part of
      that re-run — a second, earlier live recovery mechanism only creates a write race against a P0 data-correctness
      pass for no benefit once the re-run lands. Deleted as redundant, not executed.

### AA (2026-07-19) — the § Y monitoring lesson, generalised: a metric must be able to MOVE for the operation you are running

The 8-VM features re-run reported `day_partitions=3462`, **flat across three consecutive 10-minute readings**. Read
naively that is a textbook stall (flat progress metric → STOP and diagnose). It was not. The fleet was writing normally:
288 objects created under `day=2019-*` in the same window.

The metric counted **day partitions that already existed**. A `--force` re-run OVERWRITES existing `day=` directories
rather than creating new ones, so the partition count is structurally incapable of increasing — it would have read 3462
forever whether the fleet was healthy, hung, or dead.

This is the second metric-design failure in two ticks, with different mechanisms but one root cause:

| §   | metric                            | why it could never signal progress           |
| --- | --------------------------------- | -------------------------------------------- |
| Y   | object count on the hinted bucket | the bucket 404s; `\| wc -l` yields 0 forever |
| AA  | `day=` partition count            | overwrite-in-place cannot grow the count     |

**The rule the async-wait discipline should carry** (it currently says progress must be a count of TARGET artifacts and
that flat = stall): that is necessary but not sufficient. Before trusting a reading, confirm the metric **can move for
the operation actually being run** — a creation-time count moves under overwrite, a partition count does not; a count on
a real bucket can be non-zero, one on a 404 cannot. **Otherwise a broken monitor is indistinguishable from a broken job,
and the flat-means-stall rule fires on the monitor's own defect.** Both times here the honest-looking reading argued for
killing healthy work.

Fleet watchdog re-armed on creation-time counts across two independent chunks (2019 and 2025), which move under
overwrite.

- [x] [DOC] P2. ✅ Folded into `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` as **rule 1a** (SSOT):
      "VALIDATE THE METRIC BEFORE YOU TRUST A ZERO OR A FLAT READING", with both measured failures as worked examples
      and the test to apply at arm time — _"what reading would this show if the job were healthy, and is that different
      from what it shows if the job is dead?"_ Plus the three concrete guards: resolve buckets via `resolve_bucket_name`
      (never trust a launcher's printed hint), prefer creation-time counts over inventory counts (inventory is blind to
      overwrite), and take a baseline at arm time so "flat" is measured against a known-live number.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — 3 of the 4 open todos are explicitly owned
  elsewhere — two duplicate `[DIAG] P0`s annotated 'Owned by `sports_consolidated_closeout_2026_07_19.md` Track E ...
  Not duplicated here', and a `[CODE] P2` annotated 'Owned by `sports_satellite_ao_dispatch_batch6_2026_07_26.md` todo 3
  ... Left open here intentionally; do not flip it from this doc'. The 4th (`[PROCESS] P1`, codify an
  entity-rename/split consumer-migration rule) needs a codex authoring ruling. NOTE: the two `[DIAG] P0`s at ~line 387
  and ~line 440 are literal duplicates of each other within this same doc
- **na-eligibility-audit 2026-08-03**: re-read (a 2026-07-30 addendum added detail to the line-782 `[CODE] P2` todo
  since the marker; context_scope backfill otherwise, not verdict-relevant). **KEEP-NA stands, verdict unchanged from
  07-30** — same 4 open todos: 2 `[DIAG] P0` duplicates intentionally left open (owned by
  `sports_consolidated_closeout_2026_07_19.md` Track E), 1 `[CODE] P2` owned by
  `sports_satellite_ao_dispatch_batch6_2026_07_26.md` todo 3 (now slightly more complex per the addendum — also needs a
  `merge_manifest_from_canonical_paths()` swap, not just the bucket-name string fix; still owned elsewhere, not flipped
  here), 1 `[PROCESS] P1` still needing a codex-authoring ruling.
- **context-scout 2026-08-03**: re-read in full; existing context_scope (6 entries) still accurate — no new source
  target or SSOT surfaced beyond what's already listed. Refreshed marker only.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — open-item count updated 4->3 (1 item shipped since 2026-08-03);
  2 dependency-blocked, 1 operator question remain.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: re-verified via `grep -n '^\s*- \[ \]'` — exactly 2
  open todos live today (~line 407, ~line 462), both the SAME literal duplicated `[DIAG] P0` ("audit every consumer
  above for the same staleness") this doc's own text has annotated since 2026-07-30: **KEEP-NA-STALE,
  already-duplicated** — both cite "Owned by `sports_consolidated_closeout_2026_07_19.md` Track E," and Track E's
  matching `[CODE] P1` ("repoint the remaining stale `entity=fixtures` consumers, 7-file list") is confirmed still open
  there (re-read live). The `[PROCESS] P1`/§R codex-authoring todo and the `[CODE] P2`/batch6 todo that the 2026-08-03
  marker also tracked are both now `[x]` in this doc (shipped since) — not part of today's open count. No
  reclassification: this doc's remaining open work is a citation, not new dispatchable content.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
- **round-9 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA-STALE, valid — reconfirmed both open `[DIAG] P0` todos
  (line ~407, ~462) still correctly cite `sports_consolidated_closeout_2026_07_19.md` Track E as the owning doc; that
  Track's matching `[CODE] P1` ("repoint the remaining stale `entity=fixtures` consumers, 7-file list") re-verified
  still `- [ ]` open there (live-read today). No new work surfaced; doc stays `assigned_vm: NA`.
