---
doc_type: issue
title:
  "Sports ODDS ownership: registry split-brain (`SOURCE_PRIORITY` has NO `(sports, ODDS)` entry) + 127,018 bogus
  api_football×ODDS denominator rows re-seeded nightly + a still-open DOCS todo that encodes the operator-REVERSED
  odds=MTDS decision"
summary:
  "READ-ONLY audit (2026-07-15) answering an operator challenge on odds/player_values ownership + volumes. The two
  ownership rules CHECK OUT — footystats ODDS legitimately lives in instruments-service and PLAYER_VALUES is
  transfermarkt-only, both per SSOT + the operator's own 2026-06-27 reversal. But three real defects sit around them.
  (A) REGISTRY SPLIT-BRAIN: `SPORTS_DATA_TYPE_TO_SOURCE['ODDS'] = 'footystats'` (UAC league_data.py:171) but
  `SOURCE_PRIORITY` has NO `('sports','ODDS')` key at all — `has_source_priority('sports','ODDS')` returns False at
  runtime, so every gate/consumer keyed on SOURCE_PRIORITY treats the IS-owned ODDS data_type as unowned. The active
  plan sports_data_sources_canonical_completion_2026_07_13.md:928 asserts the opposite ('the generic ODDS data_type
  (which SOURCE_PRIORITY reserves for footystats)') — that claim is factually wrong and a decision was taken on it. (B)
  BOGUS DENOMINATOR: the live IS sports index carries 127,018 `source=api_football` ODDS rows across 94 leagues (82,509
  expected_unattempted with BLANK reason + 22,740 EXPECTED_POST_SEASON + 21,769 EXPECTED_PRE_SEASON) for a (source,
  data_type) pair that canonically CANNOT exist — codex is explicit that api_football `/odds` is NOT used by
  instruments-service and the adapter's get_odds() is a deprecated stub. They are re-seeded nightly (w_max
  2026-07-15T01:31:01Z = the 01:30 UTC expected-universe-v2 cron). A PARKED plan misreads them as a fetchable gap
  ('api_football ... ODDS eu=89,073 — awaiting P2a enrichment coordinator'), so the live af-backfill-* enrichment fleet
  may be chasing odds api_football will never serve. The 2026-07-12 verify SAW them ('a naive query ... showed a false
  84,768 eu here') and declared them out of scope; nothing has owned them since. (C) STALE-DECISION LANDMINE:
  sports_golden_window_attempted_failed_remediation_2026_06_24.md:143 still carries an OPEN `[DOCS] P3` todo instructing
  codex to state 'odds=MTDS-domain (the footystats exception in IS is PREDICTIONS, not ODDS)' — the exact decision the
  operator REVERSED on 2026-06-27. Its two sibling todos were correctly cancelled; this one was missed. If executed it
  writes the reversed (wrong) rule into codex, contradicting sports-data-types-catalog.md:48-52."
status: open
priority: P1
nature: notes
asset_group: [sports, meta]
stage: [meta]
repos: [unified-api-contracts, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    sports,
    odds,
    footystats,
    api_football,
    transfermarkt,
    player_values,
    source-priority,
    manifest,
    data-correctness,
    honest-coverage,
    ssot-contradiction,
  ]
related:
  [
    ../sports_data_sources_canonical_completion_2026_07_13.md,
    ./sports_golden_window_attempted_failed_remediation_2026_06_24.md,
    ../sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md,
  ]
created: 2026-07-15
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
source:
  "READ-ONLY audit agent, 2026-07-15, answering an operator challenge ('odds isn't MTDS unless it's footystats odds;
  player values sounds like Transfermarkt — but check against canonical, I'm sure we have MORE data than cited').
  Measured against a single snapshot of the live indices (instruments-store-sports-prd-central-element-323112
  _index/availability_index.parquet, 5,432,782 rows, pulled 2026-07-15T17:21Z; market-data-tick-sports-prd 1,958,499
  rows; plus both legacy no-env buckets) via DuckDB, deduped with the canonical consolidator key
  (manifest_consolidator.py:522 _BASE_DEDUP_COLS + _OPTIONAL_DEDUP_COLS, null-sentinel normalised)."
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
last_updated: 2026-07-15
---

# Sports ODDS ownership — registry split-brain + bogus api_football denominator + a stale-decision DOCS landmine

> **Scope note.** This issue does NOT dispute the ownership rules themselves — the audit CONFIRMED both. It records the
> three defects found sitting around them. All measurements are one 2026-07-15 snapshot; an enrichment fleet
> (`af-backfill-*`) and a P0 index-repair agent were live at read time, so cell counts move.

## 0. What the audit confirmed (no action needed)

| Claim                                          | Verdict       | SSOT                                                                                                                                                     |
| ---------------------------------------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Odds are MTDS-owned **unless** footystats odds | **CONFIRMED** | `codex/02-data/sports-data-types-catalog.md:48-52`; `codex/02-data/sports-data-source-coverage-matrix.md` §4; operator reversal 2026-06-27 (below)       |
| `PLAYER_VALUES` is transfermarkt               | **CONFIRMED** | UAC `canonical/domain/sports/league_data.py:189`; `canonical/crosscutting/_source_priority_data.py:59` → `('sports','PLAYER_VALUES'): ['transfermarkt']` |

Operator ruling, `plans/archive/2026_07/sports_p0_sourcing_and_honest_coverage_correctness_2026_06_27.md:92-97` —
**"footystats `ODDS` STAY in IS — operator decision 2026-06-27 (#6 REVERSED) … RAW bookmaker TICK odds = odds-api
(MTDS); footystats' _predictive_ odds + `PREDICTIONS` = IS reference."** That is verbatim the rule the operator restated
in this audit's prompt.

## A. Registry split-brain — `SOURCE_PRIORITY` has no `('sports','ODDS')`

Runtime-verified (`instruments-service/.venv`):

```
('sports','ODDS') in SOURCE_PRIORITY: False
has_source_priority('sports','ODDS'):  False
ODDS-ish keys: [('sports','ODDS_SNAPSHOT'), ('sports','ODDS_MOVEMENT'), ('sports','ODDS_HORIZON_BUCKET')]
```

Two registries disagree about the SAME data_type:

| Registry                                                                    | `ODDS` owner          |
| --------------------------------------------------------------------------- | --------------------- |
| UAC `canonical/domain/sports/league_data.py:171` SPORTS_DATA_TYPE_TO_SOURCE | `"footystats"`        |
| UAC `canonical/crosscutting/_source_priority_data.py` SOURCE_PRIORITY       | **absent — no entry** |

`ODDS_SNAPSHOT` / `ODDS_MOVEMENT` / `ODDS_HORIZON_BUCKET` all have SOURCE_PRIORITY entries; the bare `ODDS` — the one
data_type the operator ruled IS-owned — is the only odds member missing. Any gate or consumer keyed on
`has_source_priority` therefore treats IS-owned ODDS as unowned.

**This is also a live plan-correctness defect.**
`plans/active/sports_data_sources_canonical_completion_2026_07_13.md:928` reasons from the opposite premise — _"the
generic `ODDS` data_type (which `SOURCE_PRIORITY` reserves for footystats)"_ — and closes a finding on it (**"not a
defect to patch"**). The premise is false; the decision rests on it.

- [ ] [CODE] P1. Add `("sports", "ODDS"): ["footystats"]` to UAC `_source_priority_data.py` so both registries agree,
      **or** rule explicitly that `ODDS` is deliberately SOURCE_PRIORITY-exempt and document why at both sites. Gate:
      `has_source_priority("sports","ODDS")` is True (or a codex note explains the exemption); closed-set round-trip
      test still passes; `quality-gates.sh` green.
- [ ] [DOCS] P2. Correct the false premise at `sports_data_sources_canonical_completion_2026_07_13.md:928` and re-check
      the 6-row `attempted_failed` decision that rests on it.

## B. 127,018 bogus `api_football × ODDS` rows — an impossible denominator, re-seeded nightly

Measured on the live IS sports index, `data_type='ODDS'` grouped by `(source, capture_status, error_reason)`:

| source           | capture_status         | error_reason                    |       rows | leagues | date range               |
| ---------------- | ---------------------- | ------------------------------- | ---------: | ------: | ------------------------ |
| footystats       | `empty_confirmed`      | `EXPECTED_NO_FIXTURE`           |    103,249 |      46 | 2019-01-01 .. 2026-07-15 |
| **api_football** | `expected_unattempted` | **(blank)**                     | **82,509** |  **94** | 2019-01-01 .. 2026-07-15 |
| footystats       | `captured`             |                                 |     27,748 |      31 | 2019-01-01 .. 2026-07-15 |
| **api_football** | `empty_confirmed`      | `EXPECTED_POST_SEASON`          | **22,740** |  **94** | 2019-01-01 .. 2026-07-15 |
| **api_football** | `empty_confirmed`      | `EXPECTED_PRE_SEASON`           | **21,769** |  **94** | 2019-01-01 .. 2026-07-15 |
| footystats       | `empty_confirmed`      | `EXPECTED_NO_PROVIDER_COVERAGE` |      4,158 |      42 | 2026-01-13 .. 2026-06-23 |

**api_football ODDS total = 127,018 rows across 94 leagues.** Canonically this pair cannot exist:

> "**api_football `/odds` is NOT used by instruments-service.** The footystats_odds adapter has `get_odds()` defined as
> a deprecated stub that logs 'use get_fixture_odds_snapshot() instead' — there is no api_football odds path." —
> `codex/02-data/sports-data-source-coverage-matrix.md` §4

The league counts are the tell: footystats ODDS spans **46** leagues (matching the codex footystats denominator of 46);
the api_football ODDS rows span **94** — the api_football league universe cross-producted against a data_type
api_football does not serve.

**They are actively re-seeded.** `w_max = 2026-07-15T01:31:01Z` on the 82,509 `expected_unattempted` rows — the 01:30
UTC `expected_universe_v2_scheduler` cron (`codex/02-data/availability-manifest-and-data-status.md` § "Materialisation
WIRED + recurring"). This is not a frozen historical artifact; it regenerates nightly.

**Nobody owns them, and one plan actively misreads them as fetchable:**

- `plans/archive/2026_07/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md:232` SAW them and scoped
  them OUT: _"a naive query without `source=` filtering showed a false 84,768 'eu' here — those rows are
  `source=api_football`, not footystats, and outside this plan's 6-source scope"_.
- `plans/active/sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md:178` counts them as a **real gap awaiting
  a fetch**: _"api_football 542,912 (dominated by TEAMS eu=194,331 + **ODDS eu=89,073** … — awaiting P2a enrichment
  coordinator)"_. That task is `[PARKED]`, priority 999.

Risk: the live `af-backfill-*` enrichment fleet is the P2a enrichment coordinator's fleet. A blank-reason
`expected_unattempted` is the "pending_fetch" class; 82,509 of them are pointed at a source with no odds endpoint. This
also depresses every ODDS honest-coverage ratio by ~4.6× on the denominator.

- [ ] [DATA] P1. Rule on the 127,018 api_football×ODDS rows: they should almost certainly be
      `EXPECTED_SOURCE_DOES_NOT_PROVIDE` (or not seeded at all), never blank-reason `expected_unattempted`. Decide
      remove-vs-retype **before** any fleet spends credits fetching them.
- [ ] [CODE] P1. Stop the nightly re-seed at source: the v2 enumerator must not cross-product a league's `data_sources`
      against data_types that `SPORTS_DATA_TYPE_TO_SOURCE` assigns to a different source. Gate: a post-cron read shows 0
      blank-reason `source=api_football` `ODDS` rows. (Depends on **A** — the enumerator needs a registry that actually
      answers "who owns ODDS".)
- [ ] [DOCS] P2. Un-park / re-scope `sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md:178` so ODDS
      eu=89,073 is not carried as an api_football fetch target.

## C. Stale-decision landmine — an OPEN DOCS todo encoding the REVERSED rule

`plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md` §#6 correctly cancelled its two
destructive todos on the 2026-06-27 reversal:

```
- [x] CANCELLED-BY-OPERATOR-REVERSAL 2026-06-27 (decision #6 REVERSED …) — do NOT execute
      (was: `Drop "ODDS": "footystats" from UAC SPORTS_DATA_TYPE_TO_SOURCE …`)
- [x] CANCELLED-BY-OPERATOR-REVERSAL 2026-06-27 (… ) — do NOT execute
      (was: `Wipe the existing IS footystats ODDS (194,789 manifest rows + the 29,701 captured cells' GCS objects) …`)
```

…but the third was missed and is **still open** (`:143`):

```
- [ ] [DOCS] P3. Codex: state odds=MTDS-domain (the footystats exception in IS is PREDICTIONS, not ODDS) in
      `tradfi-databento-sourcing-ssot`-style sports SSOT + `instruments-foundation-and-catalogue-completeness.md`
      (sports universe = fixtures + reference + enrichment + footystats PREDICTIONS; NOT odds).
```

That instruction is the REVERSED decision. Executing it writes "the footystats exception in IS is PREDICTIONS, **not
ODDS**" into codex — directly contradicting `sports-data-types-catalog.md:48-52`, the §4 coexistence ruling, and the
operator's own 2026-06-27 words ("footystats' _predictive_ odds **+** `PREDICTIONS` = IS reference"). The doc is
`status: open` with `execution_scope: orchestrator-agent` — an agent can pick it up.

Precedent for the danger: the first pass of decision #6 **wiped the footystats ODDS GCS objects on 2026-06-25, two days
before the reversal** — 29,129 "captured" rows became phantom and 26,220 flipped to `attempted_failed`
(`sports_p0_sourcing_and_honest_coverage_correctness_2026_06_27.md:99-108`); a re-fetch VM
(`fs-backfill-20260629-043218`) had to re-pull 2019→present. This todo is the same decision's last live thread.

- [ ] [DOCS] P1. Cancel the `[DOCS] P3` todo at `sports_golden_window_attempted_failed_remediation_2026_06_24.md:143`
      with the same `CANCELLED-BY-OPERATOR-REVERSAL 2026-06-27` marker as its two siblings, **or** rewrite it to state
      the rule as actually ruled: RAW bookmaker tick odds = odds-api/MTDS; footystats predictive `ODDS` + `PREDICTIONS`
      = IS reference.

## D. Volume reference (measured 2026-07-15, canonical dedup key)

Recorded so the next reader does not re-derive it. Captured cells, deduped per `manifest_consolidator.py:522`; `UNION` =
distinct `(league_id, date)` across all four surfaces.

| data_type / source              | IS-prd | IS-legacy | MTDS-prd | MTDS-legacy | UNION distinct | cited 2026-07-12 |
| ------------------------------- | -----: | --------: | -------: | ----------: | -------------: | ---------------: |
| `ODDS` / footystats             | 27,748 |    27,566 |   22,009 |      17,282 |     **39,340** |           30,928 |
| `PLAYER_VALUES` / transfermarkt | 47,094 |    15,194 |        — |           — |     **48,387** |           58,028 |
| `trades` / odds_api             |      — |         — |  198,413 |      35,368 |              — |          185,341 |

Notes for whoever picks this up:

- **footystats ODDS is under-counted by single-surface reads.** The union across surfaces is **39,340** vs the 30,928
  usually cited — +27%. IS-legacy holds 3,895 `(league,date)` cells absent from IS-prd **and reaches back to
  2018-01-01** (IS-prd starts 2019-01-01); MTDS-prd holds a further 7,596 absent from IS-prd. Migration is incomplete in
  both directions; no single bucket is the whole picture.
- **The IS sports index was wholesale rewritten on 2026-07-13** — no `ODDS`/`PLAYER_VALUES` row in the snapshot has
  `written_at` earlier than 2026-07-13. Every pre-07-13 figure (incl. the 58,028 / 30,928 / 185,341 baselines quoted
  across the sports plans) was measured against a different index generation and is **not comparable** to a post-07-13
  read. `PLAYER_VALUES` captured reads 47,094 post-rewrite vs 58,028 pre-rewrite; 0 keys flipped captured→empty, so the
  delta is rows the rebuild did not re-emit — **whether that is phantom-correction or loss is unresolved and needs a
  GCS-vs-manifest reconcile** (out of scope for a read-only audit).
- **IS-prd `_index` carries MTDS-owned rows**: 561,048 `trades` + 350,713 `odds_horizon_bucket` cells — while the
  `instruments-store-sports-prd` bucket has **no `raw_tick_data/` prefix at all** (verified by `gcloud storage ls`). The
  parquets live in the MTDS bucket; these are manifest-only rows. Data placement is CORRECT; the index is contaminated.
  Additionally the same logical shard is recorded under **3 different `service_name` values** (`instruments-service` |
  `market-tick-data-service` | `market-data-processing-service`, identical counts — e.g. 14,330 / 12,021 apiece) and
  `service_name` IS in the dedup key, so those cells multi-count ~3× (this is what turns `trades`/odds_api from 198,413
  real cells into a 362,742 headline). Believed in-flight under
  `sports_data_sources_canonical_completion_2026_07_13.md`; flagged here, not claimed.

- [ ] [VERIFY] P2. Reconcile the post-07-13 rebuild delta (`PLAYER_VALUES` −10,934, `ODDS` −3,180 captured cells vs the
      2026-07-12 verified state) against real GCS objects — phantom-correction or data loss. Gate: per-key
      manifest-vs-GCS diff for the missing keys.
