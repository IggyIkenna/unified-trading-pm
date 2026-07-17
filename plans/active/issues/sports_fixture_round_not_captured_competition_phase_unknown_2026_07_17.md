---
doc_type: issue
title:
  Sports fixture `round` is never captured — `competition_phase` is UNKNOWN and `is_promotion_relegation` is silently
  False for ~97% of every fixture ever rolled up, blinding ML training to relegation/playoff/knockout dynamics
summary:
  The _flatten_fixture writer (instruments-service engine/orchestrator/sports.py line 280) builds each fixtures parquet
  row from CanonicalFixture, which carries no round field - so getattr(fx, "round", "") or "" defaults a
  required-non-null SchemaContract column to the empty string on essentially every row. round is the SOLE input to
  classify_competition_phase, the thing that separates relegation six-pointers, championship splits, playoffs, knockouts
  and dead rubbers from ordinary regular-season games - that module's own header calls it "critical for ML training data
  filtering". Measured on the live rolled-up catalogue, round is populated on only 545 of 17,064 fixture rows (3.2%),
  and every one of those falls in a single window (2025-12-01 to 2025-12-30), so this is a REGRESSION, not a permanent
  structural gap - the pipeline demonstrably produced real values ("Round of 16", "Quarter-finals", "Final", "Regular
  Season - 17") for that month and then stopped. Downstream, UAC features_sports declares round_name / competition_phase
  / is_promotion_relegation; with an empty round the classifier returns (UNKNOWN, None, False), so
  is_promotion_relegation is a WRONG value (False) rather than an honest null on ~16.5k fixtures - and ~136k once the
  full-history rollup lands. Recovery is NOT a per-fixture refetch - the api_football adapter already fetches in bulk
  per (league, season) with no date param, and _fetch_season_fixtures_with_raw keeps the raw response carrying
  league.round, so the whole 2019-2026 corpus is roughly 89 leagues x ~8 seasons = ~600-700 calls.
status: open
resolved_by:
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    sports,
    fixtures,
    round,
    competition-phase,
    relegation,
    ml-features,
    data-correctness,
    big-finding,
    regression,
    api-football,
  ]
related: [data_status_page_ux_and_canonicalisation_2026_07_16.md]
created: 2026-07-17
source:
  - Operator questions 2026-07-17 ("why isnt round populating how are we gonna get that retrospectively for each fixture
    hard no", "what is round is that used to separate relegation games etc") - the second question is what surfaced the
    real severity. I had triaged round as a cosmetic UI field and was about to ship it as a documented blank; the
    operator's instinct that it separates relegation games was correct and led straight to competition_phase.py, which
    reframes this as an ML training-data correctness bug, not a display nit.
  - Operator challenge on scale ("only 17k fixtures since 2020 are you sure about that") - correctly identified that the
    catalogue held ONE season, not eight; see the sibling 400d-truncation finding now fixed by --since @4a795c24.
assigned_vm: NA
assigned_role: data_engineering
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
drift_direction: advance-code
parent_epic: infrastructure_master
execution_scope: local-only
depends_on: []
last_updated: 2026-07-17
locked_by:
locked_since:
---

# Sports fixture `round` is never captured → `competition_phase` UNKNOWN everywhere

## ⏭️ HANDOFF — launch the round-FIXTURES backfill when the shared api-football key frees up

> **For the agent running `af-backfill-20260717-151237` (the FIXTURE_EVENTS backfill), or whoever next owns the shared
> api-football key.** The writer fix is SHIPPED (instruments-service@19ae5890) so new captures are correct; the
> historical fill is ready but cannot run while your VM holds the key.

**Trigger:** your FIXTURE_EVENTS VM (`--sports-entity FIXTURE_EVENTS`, 2020-06-06→2026-07-17) has STOPPED/completed —
confirm no api-football VM is running: the launcher will `ERROR: API-Football VM already running` if one is.

**Do NOT `--force` a concurrent VM.** api-football rate-limits per KEY; two VMs thrash on 429s and produce corrupted
`attempted_failed` rows, not faster data (the 2026-04-19 SFI incident the launcher cites). One VM at a time on this key.

**Steps (from a slot checkout with ADC):**

```bash
# 1. Bake the writer fix into the VM's code tarball. The launcher verifies the tarball SHA against
#    origin/live-defi-rollout HEAD and ABORTS if stale — this is what puts @19ae5890 on the VM.
bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS

# 2. Launch the round backfill. entity=FIXTURES is REQUIRED — that is the schedule grain that carries league.round.
#    (FIXTURE_EVENTS, what your VM did, is a different grain and does NOT carry round.) SPOT is the default.
bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh --entity FIXTURES 2019-01-01 2026-07-17
```

**Verify (no fire-and-forget):** STARTED <60s; at T+10min tail `run.log` and read a sampled 2019/2020 day-parquet —
`entity=fixtures/.../fixtures.parquet` should now have `round` populated (e.g. "Regular Season - N", "Quarter-finals").
The VM re-captures via the live code path, so `round` is written from the raw `af_response` (`league.round`).

**After the VM completes:**

1. Re-run the sports catalogue rollup so the catalogue picks up round across full history:
   `bash instruments-service/scripts/build_instrument_catalogue.py --asset-group sports --since 2019-01-01` (or wait for
   the weekly `lifecycle-catalogue-full-sports` job, deployment-service@b48f6a4, Sat 07:00).
2. Verify downstream (issue todos 5): `competition_phase` distribution stops being ~100% UNKNOWN and
   `is_promotion_relegation` becomes a real signal, not a constant `False`.

**Alternative (round-ONLY, lower blast radius, if a full re-capture is undesirable):** the surgical script
`instruments-service/scripts/backfill_sports_fixture_round_2026_07_17.py --apply` (@9d039e47) fills only blank `round`
cells, snapshots each parquet, idempotent — but it ALSO needs the shared key, so it is blocked by the same VM.

## What is wrong

`instruments_service/engine/orchestrator/sports.py::_flatten_fixture` builds each `entity=fixtures` parquet row from a
`CanonicalFixture` (`fx`). That canonical model has **no `round` field**, so line 280 is:

```python
"round": getattr(fx, "round", "") or "",   # getattr default → "" on ~every row
```

The function's own docstring states it outright:

> _"Returns the full flat schema (43 columns). **Defaults required-non-null columns the canonical model doesn't carry
> (`round`, `status_long`)**."_

So `round` exists as a column purely to satisfy the `SPORTS_FIXTURES` SchemaContract's required-non-null constraint, and
is filled with `""`. (`status_long` is defaulted the same way, to `"Unknown"` — likely the same class of bug, not
investigated here.)

## Why it matters — this is not a display field

`round` is the **only** input to
`instruments_service/reference_data/adapters/sports/competition_phase.py::classify_competition_phase`. That module's
header:

> _"Classifies API-Football league.round values into canonical competition phases. **Critical for ML training data
> filtering — different phases (playoffs, dead rubbers, relegation battles) have fundamentally different dynamics.**"_

Measured behaviour of the classifier against what we actually write (run 2026-07-17):

| `round` value            | → `classify_competition_phase`            |
| ------------------------ | ----------------------------------------- |
| `''` ← **what we write** | `(UNKNOWN, None, False)`                  |
| `'Regular Season - 30'`  | `(NORMAL_LEAGUE, None, True)`             |
| `'Relegation Round'`     | `(LEAGUE_SPLIT, **'RELEGATION'**, False)` |
| `'Championship Round'`   | `(LEAGUE_SPLIT, 'CHAMPIONSHIP', False)`   |
| `'Semi-finals'`          | `(TOURNAMENT, None, False)`               |

Downstream, UAC `unified_api_contracts/internal/domain/features_sports/__init__.py` declares:

```
round_name              : "Round name (e.g. 'Regular Season - 10')"
matchday                : int | None
competition_phase       : "group_stage | knockout | final | regular | playoff"
is_promotion_relegation : bool | None
```

So with `round=""`:

- `competition_phase` = **UNKNOWN** for ~16.5k fixtures (~136k after the full-history rollup)
- `is_promotion_relegation` = **`False`** — a **wrong value, not an honest null**. Relegation six-pointers and dead
  rubbers are currently indistinguishable from mid-table regular-season games in ML training data. This violates the
  never-silent-placeholders rule (`codex/02-data/honest-absence-downstream-handling.md`): an absent value is being
  rendered as a confident `False`.

## Evidence — it is a REGRESSION, not a structural impossibility

Live `prod/catalog.parquet` (sports), read 2026-07-17 after the roll-up began carrying the field
(instruments-service@684a1b2b):

```
fixtures with round populated : 545 / 17,064   (3.2%)
populated rows date span      : 2025-12-01 -> 2025-12-30      <- ONE MONTH
blank rows date span          : 2025-06-09 -> 2026-07-17      <- everything else
real values present           : 'Round of 16', 'Quarter-finals', 'Final', 'Regular Season - 17'
leagues carrying round        : ENG_NATIONAL_LEAGUE 46, COPA_DEL_REY 43, TFF_FIRST_LEAGUE 40, UECL 36, ...
```

The pipeline **demonstrably produced real, correct round values** — including exactly the knockout/phase labels the
classifier needs — for December 2025, then stopped. The `getattr` default is the _mechanism_; something was threading
real values through for that window. **Root-causing what changed around 2025-12 is todo 1 below** — do not assume the
canonical model was always the blocker.

Corroborating: sampled raw `entity=fixtures` snapshots directly — `round` is present-but-`''` across LA_LIGA,
BUNDESLIGA, ENG_CHAMPIONSHIP, DANISH_SUPERLIGA, ALLSVENSKAN, ELITESERIEN on 2026-05-01 / 2026-06-15 / 2026-07-12 (0/62
populated).

## Why retrospective recovery is CHEAP (the operator's "hard no" premise does not hold)

The instinct that this needs a per-fixture refetch (17k+ calls) is what makes it look prohibitive. It does not:

`instruments_service/reference_data/adapters/sports/adapters/api_football.py::_fetch_season_fixtures_with_raw`:

> _"Fetch **ALL fixtures for a (league, season) pair** and cache the result. API endpoint:
> `GET /fixtures?league=<id>&season=<year>` (**no `date=`**) ... cuts fixtures quota by 5-10x for multi-date backfills"_

So the whole 2019→2026 corpus is **~89 leagues × ~8 seasons ≈ 600-700 bulk calls**, not 17k — an ordinary backfill.
`_with_raw` already retains the response carrying `league.round`, and `_flatten_fixture` already receives it as
`af_response` (it reads Q5/Q6 lifecycle columns off it via `_lifecycle_columns_from_af_response`). The raw is in hand at
write time; nothing new needs fetching for NEW captures at all.

## Todos

- [ ] [DATA] P1. Root-cause the 2025-12 regression window — what populated `round` for 2025-12-01..30 and stopped?
      (candidate: a writer/adapter path change, or a backfill run that threaded `af_response` differently). Do NOT skip
      to the fix: understanding what regressed determines whether `status_long` and other defaulted columns are affected
      the same way, and whether the fix belongs in the adapter or the flattener.
- [x] ✅ **[BACKEND] P1 — DONE 2026-07-17.** Writer fixed: `_flatten_canonical_fixture_for_disk` now reads
      `league.round` from the raw `af_response` via new helper `_round_from_af_response` (mirrors
      `_lifecycle_columns_from_af_response` — same source, same pattern, no new fetch); `""` on any absence, never a
      `"None"` placeholder. Went with the flatten-from-raw approach (not the heavier UAC `CanonicalFixture` +
      adapter-mapping option) since it matches the established Q5/Q6 precedent in the same function and is what the
      backfill re-fetch also uses. — instruments-service@19ae5890 + Evidence: QG green (119s); +5 tests. Fixes all NEW
      captures + any re-capture.
- [ ] [DATA] P1. **Backfill 2019→2026 — READY, BLOCKED on the shared api-football key.** Operator chose (2026-07-17) the
      registered VM launcher `deployment-service/scripts/vm/launch-api-football-backfill-vm.sh` (re-capture via the SAME
      live code path — now carrying the writer fix @19ae5890 — so it WRITES `round`; built for multi-year runs, SPOT by
      default). **Exact command (entity=FIXTURES — the schedule grain that carries `round`; NOT FIXTURE_EVENTS):**
      `bash scripts/vm/launch-api-football-backfill-vm.sh --entity FIXTURES 2019-01-01 2026-07-17`. **BLOCKER
      (2026-07-17 15:1x):** an api-football backfill VM is ALREADY running — `af-backfill-20260717-151237`, another
      agent's **FIXTURE_EVENTS** backfill
      (`--sports-entity FIXTURE_EVENTS     --start-date 2020-06-06 --end-date 2026-07-17`). api-football rate-limits
      per-KEY and the launcher **refuses a concurrent VM** (concurrent VMs thrash on 429s → no useful data, the
      2026-04-19 SFI incident); `--force` is NOT justified (it degrades BOTH backfills). So the round-FIXTURES VM must
      launch **AFTER** that VM completes (or the operator re-prioritises). **Pre-launch:** rebuild the code tarball so
      the fix is on the VM — `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS` (the
      launcher verifies tarball freshness vs `origin/live-defi-rollout` HEAD, which has @19ae5890, and ABORTS if stale).
      Then verify no fire-and-forget (STARTED <60s + ≥1 progress/hr + STOPPED/FAILED; T+10min a sampled 2019 day-parquet
      shows `round` populated). **Low-blast-radius fallback** if a full re-capture is undesirable: the surgical
      round-only script `instruments-service/scripts/backfill_sports_fixture_round_2026_07_17.py@9d039e47` (PROVEN: EPL
      2024 = 380/380 fetch, apply-pilot `day=2024-12-26/…/EPL` → 8/8 filled "Regular Season - 18", snapshot + verify) —
      but it ALSO needs the shared key, so it is blocked by the same running VM.
- [ ] [DATA] P2. Re-run the sports catalogue rollup (`--since 2019-01-01`, @4a795c24) after the backfill so the
      rolled-up catalogue carries round across the full corpus.
- [ ] [DATA] P2. Verify downstream: `competition_phase` distribution stops being ~100% UNKNOWN and
      `is_promotion_relegation` becomes a real signal rather than a constant `False`. Quantify how much ML training data
      was mislabelled.
- [ ] [DATA] P3. Audit the sibling defaulted column `status_long` (`"Unknown"` default, same mechanism, same docstring)
      — likely the same bug class, unverified.

## Related — sibling finding, already FIXED

The sports catalogue held only **~13 months** (17,064 fixtures = exactly ONE season across 89 leagues) because the FTP
roll-up's window start was hardcoded to `today - SPORTS_FTP_WINDOW_DAYS` (400d) with **no CLI override** — `--mode full`
did not help (sports is exempt from the generic incremental engine), and the frozen-tail merge can only preserve rows
already present, never recover history never rolled up. Raw is complete 2019→2026 (verified every year). Fixed by
`--since` (instruments-service@4a795c24); full-history rollup (~375k blobs, ~3h, target ~136k rows) run 2026-07-17.
Per-league counts verified correct within the window (EPL=380, LA_LIGA=380, SERIE_A=380, BUNDESLIGA=308≈306,
ENG_CHAMPIONSHIP=558≈552) — the capture was never missing fixtures, the roll-up was just windowed.
