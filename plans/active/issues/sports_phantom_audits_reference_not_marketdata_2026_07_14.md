---
doc_type: issue
title:
  Sports phantom audit targets the REFERENCE manifest (instruments-store-sports), not market-data — inconsistent with
  every other AG, splits phantom/reprobe across two cockpit cards, and reports an unverified 44% (721,154) phantom rate
summary:
  'Discovered 2026-07-14 while running phantom + reprobe audits across all consolidators to populate the cockpit audit
  lines. For cefi/defi/tradfi/prediction the phantom reconciler audits the MARKET-DATA manifest (market-data-tick-<ag>),
  the same bucket reprobe audits — so both audit lines land on one card. Sports is the sole exception: phantom''s
  `_BUCKET_KIND_MAP["sports"] = ("instruments-store", "sports")` points it at the REFERENCE manifest
  (instruments-store-sports / sports_reference), while reprobe (via `_dp_common.manifest_bucket`) audits
  market-data-tick-sports. Result: sports phantom lights the `instruments-sports` card (721,154 phantoms) and reprobe
  lights the separate `market-data-sports` card (0 disagreements) — the two signals never appear together, and there is
  NO market-data phantom audit for sports at all. The sports phantom audit is internally CONSISTENT (its `_audit_sports`
  path templates match the instruments-store sports_reference layout — proven by 923,942 real captures matched), so this
  is NOT a wrong-bucket bug and the naive one-line map flip would BREAK it (market-data-tick-sports has no
  `sports_reference/...` paths → ~100% false-flag). The 44% phantom rate (721,154 of 1,645,101 captured) on the
  reference manifest was UNVERIFIED at filing time — since verified (2026-07-14/15 addendum) as 99.8% (719,818 rows)
  confirmed phantom-AUDITOR false positives across two distinct mechanisms (unregistered data_type → empty
  candidate-path list for trades/odds_horizon_bucket; PER_DAY_PER_SEASON path assumes a file per exact day but
  transfermarkt cache-hit design only writes on refresh-trigger days), with ZERO real data loss found — only a
  ~1,335-row (0.19%) residual left unexamined. The two-card audit-split design gap itself remains open. Operator
  decision 2026-07-14: leave code as-is, document only.'
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service, e2e-testing, deployment-api, deployment-ui]
scope: [engineer, admin]
tags:
  [
    sports,
    phantom-audit,
    reprobe,
    manifest,
    bucket-resolution,
    data-correctness,
    cockpit,
    consolidator,
    reference-data,
    unverified-count,
  ]
related:
  [
    /plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
  ]
created: 2026-07-14
parent_epic: observability_master
priority: P2
source:
  Interactive session 2026-07-14 (slot-3·hk) — running phantom+reprobe across all consolidators to populate cockpit
  audit lines; discovered the sports split when the two signals landed on different cards.
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
depends_on: []
---

# Sports phantom audit targets the reference manifest, not market-data

## What was found

While populating the cockpit consolidator audit lines (the `phantoms N` / `reprobe N disagree` rows added by
`consolidator_throughput_backlog_monitor_2026_07_09.md`), I ran the phantom reconciler and the empty re-probe against
all data-capture asset groups. Every group's two signals landed on one card **except sports**, whose phantom and reprobe
landed on two different cards.

### Root cause — the two audits resolve different sports buckets

| audit                                                                     | resolver                                                       | bucket                           | cockpit card         |
| ------------------------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------- | -------------------- |
| phantom (`reconcile_phantom_manifest_rows_all.py`)                        | `_BUCKET_KIND_MAP["sports"] = ("instruments-store", "sports")` | `instruments-store-sports-prd-…` | `instruments-sports` |
| reprobe (`reprobe_new_empty_confirmed.py` → `_dp_common.manifest_bucket`) | market-data                                                    | `market-data-tick-sports-prd-…`  | `market-data-sports` |

For cefi/defi/tradfi/prediction the phantom map uses `("market-data", <ag>)`, i.e. the SAME `market-data-tick-<ag>`
bucket reprobe audits — so both lines share a card. Sports is the only AG mapped to `instruments-store`.

### The buckets hold genuinely different data (verified by reading both indexes 2026-07-14)

- `market-data-tick-sports` (1.96M rows) — market data: `trades` (1.79M), `odds`, `ODDS`, `odds_horizon_bucket`; real
  betting venues (PINNACLE, BETFAIR, KALSHI, POLYMARKET…). This is the true market-data analog of
  `market-data-tick-{cefi,defi,tradfi}`.
- `instruments-store-sports` (5.76M rows) — reference/enrichment data: `TEAMS`, `INJURIES`, `FIXTURES`, `STANDINGS`,
  `XG`, `PLAYER_VALUES`, `PREDICTIONS`; venue mostly blank (4.95M rows). This is the sports instrument universe, owned
  by instruments-service.

Every AG has BOTH bucket types (`market-data-tick-<ag>` + `instruments-store-<ag>`); sports is not structurally special.

## Why this is NOT a simple one-line fix

`_audit_sports` (`reconcile_phantom_manifest_rows_all.py:283`) probes `sports_reference/by_date/day={D}/…` and
`sports_reference/{folder}/{folder}.parquet` paths via `unified_api_contracts.sports.candidate_parquet_paths`. Those
paths MATCH the `instruments-store-sports` layout — confirmed by the audit finding **923,942 real captures** (parquet
present) alongside the 721,154 phantoms. So the current sports phantom audit is internally consistent: correct bucket +
correct path templates for the reference manifest.

Flipping `_BUCKET_KIND_MAP["sports"]` to `("market-data", "sports")` (the naive "make it like the others" fix) would
point the same `_audit_sports` at `market-data-tick-sports`, where no `sports_reference/…` paths exist → it would
false-flag ~100% of captured rows as phantom. **Do not apply that change.**

The real gap is that **no market-data phantom audit exists for sports** — filling it means routing sports market-data
through `_audit_generic` (market-data path templates) against `market-data-tick-sports`, a genuine feature addition, not
a config flip.

## Open sub-items

1. **Design inconsistency (tracked, not urgent):** sports phantom audits reference data; every other AG's phantom audits
   market-data. `market-data-sports` therefore has no phantom line and `instruments-sports` has no reprobe line. Full
   symmetry would require (a) a market-data sports phantom path via `_audit_generic`, and separately (b) reprobe never
   audits any instruments-store manifest, so the reference side is phantom-only by design.
2. **Unverified 721,154 reference phantoms (data-correctness, needs a look before any `--apply`):** 44% of captured rows
   in `instruments-store-sports` have no parquet at the expected `sports_reference` path. This was a `--dry-run`, so
   nothing was mutated. It is either a genuine large reference-data phantom incident or a stale/incomplete
   `candidate_parquet_paths` template. **A sports phantom run with `--apply` would flip ~721k reference rows to
   `attempted_failed` — so the count MUST be verified before anyone applies.**

## Current cockpit state (left intentionally as-is)

- `instruments-sports` card → `phantoms 721154` (amber), no reprobe line — legitimate reference audit output, kept.
- `market-data-sports` card → `reprobe 0 disagree`, no phantom line.
- cefi / prediction / tradfi cards → both lines (phantom + reprobe) on one card.
- defi → both lines (phantom 0 + reprobe 0). The reprobe read-path fragility that originally blocked it
  (`read_manifest_index` single-shot `download_bytes` truncating on defi's large index — `ChunkedEncodingError`
  mis-classified as "index not found" and silently skipping the AG) was **FIXED 2026-07-14** in `_dp_common.py` (narrow
  `_is_not_found` off the blanket `OSError`; retry-with-backoff, raise-not-skip on exhaustion). Verified: defi reprobe
  recovered on retry and wrote its blob.

## Decision

Operator decision 2026-07-14: **leave code as-is, document only.** No bucket-map change, no `--apply`, no market-data
sports phantom path added in this session. This doc tracks the inconsistency and the unverified count for a future
deliberate fix.

## Addendum 2026-07-14 (slot-3, later same day) — the 721,154 unverified count, broken down and mostly explained

Downloaded and analyzed the triage JSONL
(`gs://central-element-323112-phantom-triage/triage_sports_20260714_063147.jsonl`, 721,154 rows, all
`confidence: MEDIUM`) directly. Breakdown by `data_type`:

| data_type             | count   | % of total | disposition                                        |
| --------------------- | ------- | ---------- | -------------------------------------------------- |
| `trades`              | 561,048 | 77.8%      | **confirmed false positive**                       |
| `odds_horizon_bucket` | 143,594 | 19.9%      | **confirmed false positive**                       |
| `PLAYER_VALUES`       | 15,176  | 2.1%       | spot-checked, appears genuine — needs its own look |
| `STANDINGS`           | 460     | <0.1%      | not checked                                        |
| `TEAMS`               | 460     | <0.1%      | not checked                                        |
| `XG`                  | 300     | <0.1%      | not checked                                        |
| `WEATHER`             | 106     | <0.1%      | not checked                                        |
| `MATCHES`             | 7       | ~0%        | not checked                                        |
| `FIXTURES`            | 2       | ~0%        | not checked                                        |

**97.7% (704,642 rows) is a confirmed tool false-positive, not a data problem.** Root cause, read directly from
`unified_api_contracts/canonical/domain/sports/gcs_paths.py::candidate_parquet_paths()`:
`folder = SPORTS_DATA_TYPE_TO_FOLDER.get(data_type); if folder is None: return []`. Neither `"trades"` nor
`"odds_horizon_bucket"` is a registered key in `SPORTS_DATA_TYPE_TO_FOLDER` — they're MTDS/MDPS market-data types that
only started appearing in this REFERENCE bucket (`instruments-store-sports-prd`) because of the manifest-bucket-routing
fixes shipped earlier today (2026-07-13/14, `market-tick-data-service@ad76547c` + the `mdps_odds_horizon_bucket`
migrations). An empty candidate list means the phantom checker's `for c in candidates:` loop never executes, so
`is_real` stays `False` by construction — **every row of an unmapped data_type is flagged phantom regardless of whether
real data exists.** Independently re-verified real data exists for both: `odds_horizon_bucket` captured-row counts and a
specific spot-check (date `2020-06-06`, `venue=ODDS_API`) were directly confirmed against live GCS earlier today during
the MDPS venue-grain-mismatch investigation (see this plan's own Progress Log, same date); `trades` is the raw
`odds_api` ticks, separately confirmed ~100% healthy (561,048 captured / 6 attempted_failed) via direct manifest reads
today.

**Correction/refinement 2026-07-15** — a sharper question ("is `trades` even a legitimate reference-manifest data_type
for sports? doesn't the time-horizon-bucketed odds already come in elsewhere?") forced a re-check, and the
"`SPORTS_DATA_TYPE_TO_FOLDER` needs entries" framing above is **incomplete — that fix alone would not work.** Read the
writers directly (`market-data-processing-service/scripts/reprocess_sports_odds.py:249-297`, both docstrings cite
`sports_manifest_canonicalisation_2026_06_01.md`, decided 2026-06-07):

- **Yes, `trades`/`odds_horizon_bucket` manifest rows in `instruments-store-sports` are 100% legitimate and deliberate —
  not a routing accident.** Sports is a documented, cross-referenced architectural exception: every other asset_group
  splits its availability manifest into a reference bucket + a market-data bucket, but for sports specifically, **one
  canonical manifest** (`instruments-store-sports`) tracks availability for ALL sports data_types — reference (fixtures,
  injuries, standings…) AND market-data (raw odds ticks, bucketed odds-horizon output) alike.
  `_resolve_manifest_bucket()`'s docstring: _"routed ALL of sports' availability manifest to the `instruments-store`
  bucket while the actual tick BYTES ... correctly stay in the per-asset_group `market-data-tick` bucket."_ So
  `_audit_sports()` auditing `instruments-store-sports` for these data_types is auditing the **correct, intended**
  manifest — the phantom flag is not evidence anything is mis-routed.
- **But the real parquet bytes for these two data_types physically live in a different bucket entirely**
  (`market-data-tick-sports-{env}`, resolved via `resolve_bucket_name(kind="market-data", asset_group="sports")`), with
  completely different path shapes than the `sports_reference/by_date/...` layout `candidate_parquet_paths()` assumes:
  - `trades` (raw per-bookmaker odds ticks):
    `raw_tick_data/by_date/day={date}/pipeline_mode={batch_odds_api|live_odds_api}/asset_group=sports/…ticks.parquet`
  - `odds_horizon_bucket`:
    `processed/by_date/day={date}/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/data_type=odds_horizon_bucket/league_id={league_id}/timeframe={horizon}/bucketed.parquet`

  Both templates are lifted verbatim from `reprocess_sports_odds.py` (`_CANONICAL_ODDS_PREFIX_TEMPLATES`,
  `_OUTPUT_PATH_TEMPLATE`) — the actual, current write paths, not a guess.

**Corrected fix suggestion**: simply adding `"trades"`/`"odds_horizon_bucket"` to `SPORTS_DATA_TYPE_TO_FOLDER` would NOT
work — that map's templates are inherently scoped to same-bucket (`instruments-store-sports`) paths, and these two
data_types' real files are in a **different bucket**. The correct fix is a **data_type-aware, cross-bucket branch in
`_audit_sports()`** (`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py:283`): for
`data_type in {"trades", "odds_horizon_bucket"}` (equivalently `source in {"odds_api", "mdps_odds_horizon_bucket"}`),
resolve `market-data-tick-sports-{env}` (not the bucket being audited) and probe the two templates above instead of
`candidate_parquet_paths()`. A plain skip-list (silently excluding these data_types from the phantom check) would be the
lazy alternative — it would just hide the false positive rather than actually re-verify these ~704,642 rows against
their real location, so the cross-bucket probe is the more correct fix if anyone picks this up.

This confirms sub-item 1 in "Open sub-items" above precisely: it's the "no market-data phantom audit for sports" design
gap, manifesting as blanket false positives rather than as an absence.

## RE-TRIAGE (2026-07-23)

**Verdict: STILL OPEN, ACCURATE — confirmed unchanged.** Re-read
`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` directly: `_BUCKET_KIND_MAP["sports"]` is still
`("instruments-store", "sports")` — unchanged from every other AG's `("market-data", <ag>)` pattern, exactly as this doc
documents (the two-card split persists). Also re-read `unified_api_contracts/canonical/domain/sports/gcs_paths.py`'s
`SPORTS_DATA_TYPE_TO_FOLDER`: still has no `trades` or `odds_horizon_bucket` keys (grepped, zero hits) — the
data_type-aware cross-bucket branch this doc's "Corrected fix suggestion" recommends has not been built. This all
matches the operator's 2026-07-14 decision ("leave code as-is, document only") — nothing has drifted since. Separately
worth noting for context (not a change to THIS doc's finding): the live MTDS sports manifest's `trades`/
`odds_horizon_bucket` `source=api_football` population that the 2026-07-14 addendum partly attributed phantom rows to
has since been wiped entirely (`market-tick-data-service@e9d9dec0`, 2026-07-23) — this doesn't touch the reference-side
`instruments-store-sports` phantom audit this doc is actually about, so it does not change the verdict here. No status
change.

**The remaining 2.3% (~16,511 rows) is NOT explained by the above** — these are all registered reference data_types with
real candidate-path templates. Spot-checked one `PLAYER_VALUES` row directly (`day=2021-06-27`,
`manifest_status: captured`, `manifest_capture_time: 2026-07-13T23:49:29Z` — i.e. written only hours before this audit
ran): listed the full `sports_reference/by_date/day=2021-06-27/` tree directly via `gcsfs` — no `entity=player_values`
(or `entity=transfermarkt_teams`) blob exists anywhere, under either the `pipeline_mode=` canonical prefix or the legacy
bare path, at any pipeline_mode folder present for that day (`batch_api_football`, `batch_footystats`,
`batch_instruments_service`, `batch_open_meteo`, `batch_soccer_football_info` — no `batch_transfermarkt` folder exists
for this date at all). This one row looks like a genuine phantom, not a template gap — but it's a single spot-check, not
a full verification of all 15,176. Given the recent `manifest_capture_time`, this may be freshly-introduced by whatever
wrote it in the last day, rather than old debt — worth checking whether it's the same write-without-file pattern class
already found and fixed today for footystats/`open_meteo` (`instruments-service@ed3e75b8`) applied to transfermarkt's
`PLAYER_VALUES` writer, or something PLAYER_VALUES-specific (this exact data_type had a near-identical false-positive
history — see the `gcs_paths.py` code comment on the 2026-05-05 SSOT realignment and the deleted
`write_player_values_placeholders.py` band-aid — so a regression of THAT class is also plausible and should be checked
first).

**Update — PLAYER_VALUES root-caused, also NOT a data-loss problem.** Read the writer directly:
`instruments-service/instruments_service/engine/orchestrator/transfermarkt.py::_fetch_transfermarkt_data` (or equivalent
teams/player_values fetch function, ~lines 440-692). Confirmed `"player_values"` IS correctly registered in UAC's
`_SPORTS_ENTITY_TO_PIPELINE_MODE` → `PipelineMode.BATCH_TRANSFERMARKT` (`pipeline_mode.py:473`) — so this is **not** the
TEAMS/STANDINGS-style pipeline_mode-mislabeling bug, a different mechanism entirely:

- The function has a cache-hit short-circuit (lines 446-496): when the cached team/value roster for the season is still
  fresh (`_cache_is_fresh`) and no league needs a refresh trigger that day (`get_leagues_needing_refresh` returns
  empty), it skips the live API loop and populates `_captured_league_counts` **from the cache** instead (lines 469-475)
  — `all_teams` (the live-fetch accumulator) stays empty.
- The real per-day parquet write (`_gated_sink_write` to the `by_date/day={D}/pipeline_mode=batch_transfermarkt/` sink,
  plus the `master/`-accumulator and `snapshots/`-by-season writes) only happens inside `if all_teams:` (line 570) —
  **which cache-hit days never enter.**
- But the per-league manifest write loop (lines 644-688, `manifest.record_captured_from_counts(...)`) runs
  **unconditionally**, using `_captured_league_counts` regardless of which branch populated it. The code comment at line
  644 confirms this is deliberate: _"Per-league honest-coverage manifest rows — identical between the cache-hit and
  live-fetch branches."_

Net effect: on every cache-hit day (the vast majority of days — refreshes only fire on `get_leagues_needing_refresh`
trigger dates, not daily), the manifest stamps `captured` for that exact `day=D`, but no file is ever written at
`by_date/day={D}/pipeline_mode=batch_transfermarkt/entity=player_values/` for that day — by design, since the underlying
roster/valuation data didn't change and a real file already exists at the season's trigger date(s).
`candidate_parquet_paths()`'s PER_DAY_PER_SEASON template hardcodes `day={day}` (the exact day being checked) with no
allowance for "real file lives at a different trigger day within the same season" — so every cache-hit day false-flags
phantom.

**Confirmed real data is NOT missing** — directly listed the accumulator paths in prod:
`sports_reference/master/entity=player_values/master.parquet` exists, and
`sports_reference/snapshots/entity=player_values/season={Y}/` has real per-season snapshot data for
`Y ∈ {2014, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026}`. The transfermarkt player-values pipeline is healthy
and has been producing real data across its entire history; the 15,176 phantom flags are a **second, distinct class of
phantom-auditor false positive** (audit-path assumes one file per exact day; writer intentionally reuses a season's
trigger-date file across cache-hit days) — layered on top of the first class (unregistered data_type → empty candidate
list). Combined, **both PLAYER_VALUES and the 704,642 `trades`/`odds_horizon_bucket` rows are now confirmed tool false
positives** — together 719,818 of 721,154 rows (99.8%). Only the small remainder (STANDINGS 460, TEAMS 460, XG 300,
WEATHER 106, MATCHES 7, FIXTURES 2 — 1,335 rows, 0.19% of the original count) is unaccounted for and would need its own
spot-check if this is ever picked back up; given the scale, that's low-priority relative to the two confirmed classes
above.

**Still not done, still respecting the operator's "leave code as-is" decision**: no code changed, no `--apply` run, no
bucket-map edit, no change to the transfermarkt cache-hit behavior (which is working as intended — the bug, if any, is
in the phantom auditor's path-matching assumption, not in the writer). This addendum narrows the original "44%
unverified" down to a fully-explained 99.8% (two confirmed tool-limitation classes, zero real data loss found) plus a
~1,335-row (0.19%) residual left unexamined for a future pass.
