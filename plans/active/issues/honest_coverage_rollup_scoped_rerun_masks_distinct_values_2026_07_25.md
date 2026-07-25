---
doc_type: issue
title: >-
  A single-asset_group `measure_honest_coverage.py --asset-group X` re-run overwrites the SHARED daily coverage.json,
  making `GET /distinct-values/{asset_group}` silently return false-clean 0/0 for every OTHER asset_group that day
summary: >-
  CONFIRMED (2026-07-25, direct GCS read + code read). `measure_honest_coverage.py::_write_output` does a plain
  `blob.upload_from_string(...)` to `gs://{project}-honest-coverage/{date}/coverage.json` with NO merge against an
  existing file for that date -- so a scoped re-run (e.g. `--asset-group cefi`, observed live today) fully replaces that
  day's rollup with a narrower payload. `_distinct_values.py::_read_honest_coverage_rollup()` picks the NEWEST reachable
  date by `blob_exists` alone, never checking `asset_groups_measured` -- so `GET /distinct-values/{asset_group}` for any
  asset_group NOT in that day's scoped run returns an empty coverage section, which `enumerate_distinct_values()`
  reports as `0 non-canonical / 0 total distinct` -- indistinguishable from "fully canonical, nothing to see" for a
  human or dashboard reading the badge. This is the exact drift-detection panel this plan audits; while the hazard is
  live, the panel is a false negative for every asset_group the day's scoped run excluded, until the next full 5-AG
  nightly run overwrites it.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, deployment-api]
scope: [engineer]
tags: [honest-coverage, distinct-values, data-correctness, false-negative, rollup, race-condition]
related:
  [
    /plans/active/distinct_values_noncanonical_audit_2026_07_20.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/reconciliation-census-and-compute-tiers.md,
  ]
created: "2026-07-25"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
source: >-
  Found while re-running the distinct_values_noncanonical_audit_2026_07_20.md census-refresh todo (2026-07-25): fetching
  the newest coverage.json for a table refresh, the endpoint's own `_read_honest_coverage_rollup()` picked 2026-07-25's
  rollup (newest reachable date) which turned out to be scoped to `asset_groups_requested=['cefi']` only --
  `enumerate_distinct_values(coverage, 'defi')` against that same payload returned 0/0 on every axis, which would read
  as "DeFi is now fully canonical" rather than "no data was measured for DeFi today."
---

## The mechanism, exact code cites

1. `instruments-service/scripts/measure_honest_coverage.py::main()` accepts `--asset-group` (default `all`, but any of
   the 5 individual asset_groups is also a valid choice, line ~856-861) and always writes to the SAME per-date path
   regardless of scope: `_write_output()` (line 837-851) does
   `bucket.blob(f"{run_date}/coverage.json").upload_from_string(blob_bytes, ...)` -- a full overwrite, no read-merge
   against whatever coverage.json already exists at that date.
2. `deployment-api/deployment_api/routes/data_status/_distinct_values.py::_read_honest_coverage_rollup()` (line 233)
   probes `blob_exists` backwards from today for `_COVERAGE_LOOKBACK_DAYS` (8) days and returns the payload for the
   FIRST date where a `coverage.json` exists -- it never inspects `asset_groups_requested` / `asset_groups_measured` /
   `partial` (all three ARE present on the payload, schema_version 2) to check whether the date it picked actually
   covers the asset_group the caller wants.
3. `enumerate_distinct_values(coverage, asset_group)` (line 393) reads `coverage[section_key].get(asset_group)`; when
   that key is entirely absent (asset_group wasn't in that day's scoped run) every axis enumerates to `[]`, and
   `non_canonical_count[axis] = 0` for all four axes -- the SAME numeric shape as "measured today, found zero drift."

## Live confirmation (2026-07-25, this session)

Read `gs://central-element-323112-honest-coverage/{date}/coverage.json` directly for the last 10 days:

| date       | asset_groups_requested                           | generated_at         |
| ---------- | ------------------------------------------------ | -------------------- |
| 2026-07-25 | `['cefi']`                                       | 2026-07-25T22:29:44Z |
| 2026-07-24 | `['cefi','defi','tradfi','sports','prediction']` | 2026-07-24T00:35:09Z |
| 2026-07-23 | `['cefi','defi','tradfi','sports','prediction']` | 2026-07-23T00:35:07Z |
| 2026-07-22 | `['tradfi']`                                     | 2026-07-22T15:39:41Z |
| 2026-07-21 | `['cefi','defi','tradfi','sports','prediction']` | 2026-07-21T00:35:50Z |
| 2026-07-17 | `['defi']`                                       | 2026-07-17T15:02:42Z |
| 2026-07-16 | `['defi']`                                       | 2026-07-16T19:47:34Z |

Scoped same-day re-runs (2026-07-25, 2026-07-22, 2026-07-17, 2026-07-16) are NOT rare -- roughly 4 of the last 10 days
carry a scoped payload. Calling `GET /distinct-values/defi` right now (2026-07-25, before the next full nightly run)
returns `non_canonical_count = {venues: 0, instrument_types: 0, data_types: 0, chains: 0}` -- confirmed by direct
invocation of `enumerate_distinct_values()` against the live 2026-07-25 payload during this session. This is the exact
opposite of the real answer (this plan's own refreshed census the same day, read against 2026-07-24's complete rollup
plus a live manifest-direct cross-check, found 23 real non-canonical DeFi values across all four axes).

## Why this matters (data-correctness, not cosmetic)

`GET /distinct-values/{asset_group}` IS the canonical-drift detector this entire plan
(`distinct_values_noncanonical_audit_2026_07_20.md`) exists to keep honest -- "the panel is a deliberate
non-canonicalising drift detector" per that plan's own Mechanism section. A silent false-clean reading on any day a
narrower rollup happens to be the newest reachable one defeats the panel's entire purpose for every asset_group NOT in
that day's scope, with no visible signal to the operator/dashboard that the reading is stale/incomplete rather than
genuinely clean -- the `0/0` shape is bit-for-bit identical to "measured today, zero drift."

## Not attempted here (needs a design decision, out of this issue's bounded scope)

Two independent remediations exist and the choice between them is a judgment call, not mechanical:

- **A. Reader-side guard**: `_read_honest_coverage_rollup()` (or its caller) checks
  `asset_group in coverage.get("asset_groups_measured", [])` for the picked date; if absent, continues the lookback
  probe to an OLDER date that does cover it (bounded by the existing 8-day window), and the response should say which
  `source_date` was actually used for THIS asset_group (today's endpoint returns one `source_date` for the whole
  payload, which would become misleading once per-axis dates can diverge).
- **B. Writer-side guard**: `measure_honest_coverage.py` never overwrites a wider existing coverage.json with a narrower
  one for the same date -- either merge the new asset_group's section into the existing payload (read-modify- write) or
  write scoped runs to a DIFFERENT path (e.g. `{date}/coverage.{asset_group}.json`) and have the reader union across
  same-day files.

Both are real code changes to a currently-shipped, actively-relied-on endpoint; picking one, plus deciding whether
`source_date` needs to become per-axis in the response contract (a client-facing shape change), needs an operator/owner
call -- not guessed past here.
