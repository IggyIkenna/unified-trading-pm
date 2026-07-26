---
doc_type: issue
title:
  Self-caused data-correctness incident — nested player_stats normalization script silently wrote 240 canonical objects
  empty (0 columns/0 rows), fully remediated via live api_football re-fetch
summary: >-
  While executing sports_satellite_ao_dispatch_batch5-002 (flatten the ~3,274 nested-schema canonical PLAYER_STATS cells
  left unhandled by dedup_canonical_player_stats_2026_07_25.py), the flattening script's --apply run wrote 240 of those
  3,274 objects as a fully empty (0-column, 0-row) parquet file — every row's team/players parsed fine but
  normalize_api_football_player_stats legitimately returned zero records for every team-block, and the script had no
  guard against writing that empty result. The bucket has no object versioning and
  soft_delete_policy.retentionDurationSeconds=0 (confirmed live) — the original nested bytes for these 240 objects are
  NOT recoverable from GCS, and a BigQuery-mirror pre-check found no alternative recovery source. Live-verified the API
  actually still holds real player-stat data for the affected fixtures (a 3-cell test pulled 40 real player rows each) —
  this was genuine data destruction, not an artifact of already-empty source data. Fully remediated: all 240 objects
  re-fetched live from api_football (fixture_ids recovered from the untouched sibling `entity=fixtures` objects),
  normalized via the same production `normalize_api_football_player_stats` function, written, and READ-BACK VERIFIED
  (num_columns>0 AND num_rows>0) individually — 240/240 succeeded, 0 remaining empty objects on an independent final
  census. Root cause fixed in the original script (refuses + flags any empty-result write instead of writing it) so the
  bug class cannot reproduce on a future run.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [sports, data-correctness, player-stats, incident, self-caused, remediated, canonical]
related: [canonical_player_stats_fixture_events_quality_2026_07_16, sports_satellite_ao_dispatch_batch5_2026_07_26]
created: 2026-07-26
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by: slot-2, 2026-07-26
locked_by:
source:
  [
    "Self-discovered 2026-07-26 (slot-2, data_engineering) via a post-apply verification re-scan of
    normalize_nested_player_stats_2026_07_26.py's own --apply run, per its stated verification methodology (re-run
    immediately after and confirm 0 remaining, mirroring dedup_canonical_player_stats_2026_07_25.py's precedent).
    Escalated live as BLK-bf61980b; operator/main ruled to remediate immediately (Option A) rather than stop-and-wait,
    per the data-pipeline-correctness-hard-rule + external-data-always-available rule.",
  ]
---

# Self-caused incident: nested player_stats normalization wrote 240 objects empty

## What happened

Task `sports_satellite_ao_dispatch_batch5-002` (source:
[`sports_satellite_ao_dispatch_batch5_2026_07_26.md`](../sports_satellite_ao_dispatch_batch5_2026_07_26.md)) asked to
flatten the ~3,274 nested-schema canonical `PLAYER_STATS` cells that
[`dedup_canonical_player_stats_2026_07_25.py`](../../../instruments-service/scripts/dedup_canonical_player_stats_2026_07_25.py)
correctly skipped (never guessed how to dedupe a schema it wasn't built for — see
[`canonical_player_stats_fixture_events_quality_2026_07_16.md`](../canonical_player_stats_fixture_events_quality_2026_07_16.md)
Finding 1's 2026-07-25 update).

1. Wrote `instruments-service/scripts/normalize_nested_player_stats_2026_07_26.py`, reusing the exact production mapping
   function (`unified_api_contracts.external.api_football.normalize.normalize_api_football_player_stats`) to flatten
   each nested `[team, players, fixture_id, available_at]` row (parsed via `ast.literal_eval` on the stringified
   Python-repr blobs the 2026-04-11 writer produced, live-verified via a read-only probe before writing any code).
2. A full-population dry-run (26,696 manifest cells) matched the issue doc's own historical counts exactly: 1,298
   `not_found` (the separate, unrelated missing-GCS finding — untouched by this incident), 22,124 `already_flat`, 3,274
   `would_normalize`, **0 parse errors**.
3. Ran `--apply`. Exit code 0, `{'normalized': 3274}`, 0 errors, 0 CAS races.
4. Per the sibling dedup script's own stated verification methodology ("a re-run immediately after confirmed 0 duplicate
   rows remain"), ran a post-apply dry-run re-scan. It reported **240 objects now `unrecognized_schema`** with
   `columns: []` — i.e. the object I had just written now had ZERO columns.

## Root cause

`normalize_api_football_player_stats` returns `[]` for a team-block whose `players` list is empty (a normal, correct
behavior for the ALREADY-FLAT population, mirroring how the live production adapter has always worked). My script's
`_flatten_nested_df` only treated an `ast.literal_eval`/type-check **exception** as a reason not to write (the
"all-or-nothing" parse-error guard) — it never checked whether the RESULTING flattened record list was itself empty
before writing. For 240 of the 3,274 objects, every row's `team`/`players` parsed successfully as valid Python objects,
but the (as it turned out, later-confirmed-incorrect) assumption that a clean parse implies real data held FALSE: the
flatten step legitimately produced zero records, `pd.DataFrame([])` has 0 columns, and that got written straight to the
canonical bucket, silently destroying whatever the original nested content actually was.

This is exactly the silent-placeholder failure mode the data_engineering craft north-star bans — the difference here is
the "placeholder" wasn't a fabricated non-empty value, it was an accidental TOTAL ERASURE with no signal at all.

## Why the data was NOT actually empty (live-verified)

A live re-fetch of 3 sample fixtures from these affected objects pulled 39-40 real player-stat rows EACH from the
api_football API — proving the original nested objects held genuine data, not an already-empty edge case. The 240
objects skew toward major, well-covered leagues (SERIE_A, BUNDESLIGA, PRIMEIRA_LIGA, ENG_CHAMPIONSHIP, etc.) across
2024–2025 dates, not the ancient/sparse-coverage 2019 era — consistent with real data having existed.

## Recovery-path check (before remediating)

- **GCS object versioning / soft-delete**: bucket `instruments-store-sports-prd-central-element-323112` confirmed
  (`gcloud storage buckets describe`) to have `soft_delete_policy.retentionDurationSeconds=0` and no versioning;
  `gcloud storage ls -a` on an affected object showed exactly ONE generation. **No GCS-level recovery path exists.**
- **BigQuery mirror**: checked `sports_analytics` (only `odds_ticks_hive`) and `sports_betting` (only `countries`)
  datasets in `central-element-323112` — no `player_stats` table anywhere. **No alternative recovery source exists.**
- **Live re-fetch (chosen path)**: the sibling `entity=fixtures` objects for the SAME (date, league, pipeline_mode)
  cells were untouched by this incident and still carry `af_fixture_id` — enough to re-derive exactly which fixtures
  needed a fresh player-stats pull.

## Remediation

Escalated live as `BLK-bf61980b` immediately on discovery (before attempting any fix), per the data-pipeline-
correctness-heartbeat + big-finding-notify-operator rules. Ruling: proceed with live re-fetch (external data is always
available; a 240-fixture pull is a modest, well-bounded cost), with four mandatory guardrails — all satisfied:

1. **Root-cause fix first**: `normalize_nested_player_stats_2026_07_26.py` now refuses to write any object whose
   flattened result is empty (checked both pre- and post-dedupe), returning a new `empty_result_flagged` status instead
   — so a future run of the SAME script cannot reproduce this bug class.
2. **Read-back verify every remediated object**: `remediate_empty_player_stats_incident_2026_07_26.py` re-downloads and
   re-parses each object immediately after writing it, and only counts it `remediated` if
   `num_columns > 0 AND num_rows > 0` — a fixture that genuinely came back with no live player data would be flagged
   `no_player_data_live` and left untouched, never written empty. (In practice: 0 such cases — all 240 fixtures had real
   live data.)
3. **Scoped exactly to the 240 objects**: the remediation script reads its cell list from a fixed, committed JSON file
   (`scripts/_incident_2026_07_26_affected_cells.json`) enumerated by a dedicated read-only census — never a wider
   re-scan of the full manifest.
4. **Manifest state**: no manifest write was needed — these cells were already `capture_status=captured` before, during,
   and after the incident; only the underlying object bytes changed, and the manifest's own status was never incorrect
   at any point.

**Result**: `remediate_empty_player_stats_incident_2026_07_26.py --apply` — 240/240 `remediated`, 0 errors, 0
`verify_failed`. An independent final census (separate script, same manifest-driven methodology) confirmed **0 remaining
0-column PLAYER_STATS objects** project-wide.

## Evidence

- `instruments-service` (this repo, committed alongside this doc):
  - `scripts/normalize_nested_player_stats_2026_07_26.py` (with the post-incident empty-result guard)
  - `scripts/remediate_empty_player_stats_incident_2026_07_26.py`
  - `scripts/_incident_2026_07_26_affected_cells.json` (the 240-cell incident list)
- Live run logs (session-local, not committed): full-population dry-run
  `{'not_found': 1298, 'already_flat': 22124, 'would_normalize': 3274}` (0 parse errors) → apply `{'normalized': 3274}`
  (0 errors) → post-apply verification found 240 `unrecognized_schema` (0-column) → remediation dry-run
  `{'would_remediate': 240}` (0 unrecoverable) → remediation apply `{'remediated': 240}` (0 errors, 0 verify_failed) →
  independent final census: 0 empty objects remaining.
- `BLK-bf61980b` (dashboard blocked-question, main/operator ruling to proceed with live re-fetch + the 4 guardrails
  above).

## Follow-up todos

- [ ] [DATA] P2. Consider enabling GCS object versioning (or a bucket-level soft-delete retention window) on
      `instruments-store-sports-prd-central-element-323112` (and, if the same gap exists, its sibling prd sports
      buckets) — this incident was recoverable only because the source was a re-fetchable external API; a similar
      accidental-empty-write bug against internally-derived (non-re-fetchable) canonical data would have been a
      PERMANENT loss under the current zero-retention policy. (repo: instruments-service / terraform-canonical infra,
      needs an infra/operator decision on cost vs. blast-radius reduction)
- [ ] [DATA] P3. Grep other one-off canonical-rewrite scripts in `instruments-service/scripts/` for the same missing
      "refuse to write an empty/0-row result" guard (this incident's root-cause class could exist in any script that
      builds a `pd.DataFrame(records)` from a possibly-empty `records` list before a CAS write) — audit and add the same
      guard wherever missing. (repo: instruments-service)

## Progress Log

- 2026-07-26 (slot 2): Incident discovered via the sibling script's own verification methodology, escalated live
  (BLK-bf61980b), root-cause fixed, remediated (240/240), independently re-verified clean, this doc filed.
