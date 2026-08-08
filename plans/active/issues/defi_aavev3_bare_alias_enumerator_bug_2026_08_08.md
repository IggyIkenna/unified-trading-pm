---
doc_type: issue
title: AAVEV3 bare-alias phantom venue — instruments-service pre-launch enumerator bug (root-caused + fixed)
summary: >-
  46,300 manifest rows with bare venue=AAVEV3 (no chain split, capture_status=empty_confirmed, dated
  2018-01-01..2023-01-26, single bulk written_at=2026-08-05T04:08:15Z) traced to a real code defect:
  unified-api-contracts/chain_env.py's PROTOCOL_LAUNCH_DATES carries a literal duplicate dict key ("ETHEREUM","AAVEV3")
  alongside the canonical ("ETHEREUM","AAVE_V3") entry ("alias: no-underscore form used by some callers");
  instruments-service/scripts/enumerate_expected_universe.py::_yield_v2_defi_pre_launch_rows iterated
  PROTOCOL_LAUNCH_DATES.items() with venue_label = protocol.upper() and zero alias canonicalisation, so the alias key
  seeded its own full pre-launch placeholder sweep as an independent phantom venue. Dormant historical batch artifact (0
  GCS objects backing it, not a live/growing writer — capped by the fixed 2023-01-27 launch-date window, already fully
  seeded) but the code defect was live and would re-materialise on any future re-enum, and the same class of bug (an
  un-canonicalised alias key + naive .upper() iteration) could reproduce for any other protocol given a bare-spelling
  alias in PROTOCOL_LAUNCH_DATES. Root-caused by a dispatched sub-agent (read-only investigation); code fix applied same
  session (instruments-service canonicalises venue_label via VenueMapping._canonicalise_defi_protocol_spelling + dedups
  the (chain, venue) pair before emitting, mirroring the identical fix already applied to the per-instrument v2 path in
  the same file at line ~1542).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [defi, aavev3, canonical-naming, enumerator, phantom-venue, expected-universe]
related:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: "2026-08-08"
author: interactive session (/autonomous)
priority: P2
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md AAVEV3 row, sub-agent root-cause dispatch, 2026-08-08",
  ]
drift_direction: advance-code
context_scope:
  [
    instruments-service/scripts/enumerate_expected_universe.py,
    unified-api-contracts/unified_api_contracts/registry/chain_env.py,
    unified-api-contracts/unified_api_contracts/registry/venue_mapping.py,
  ]
---

## Finding

Sub-agent read-only investigation (full detail in the tracker doc's Progress Log, 2026-08-08 entry) confirmed:

- All 46,300 `venue=AAVEV3` manifest rows: `capture_status=empty_confirmed`, `chain=ETHEREUM`, dated
  2018-01-01→2023-01-26 (the day before AAVE_V3-ETHEREUM's registered 2023-01-27 launch), 25 `data_type` values × 1,852
  rows each, single identical `written_at=2026-08-05T04:08:15.957401+00:00` (one bulk batch write),
  `service_name=instruments-service`.
- 0 GCS objects under any `AAVEV3` path — pure manifest bookkeeping, no backing data.
- Mechanism: `unified-api-contracts/unified_api_contracts/registry/chain_env.py:199` carries
  `("ETHEREUM", "AAVEV3"): "2023-01-27"` as a literal duplicate dict key beside the canonical `("ETHEREUM", "AAVE_V3")`
  entry (line 198). `instruments-service/scripts/enumerate_expected_universe.py:: _yield_v2_defi_pre_launch_rows`
  (~line 1469) iterates `PROTOCOL_LAUNCH_DATES.items()` directly with `venue_label = protocol.upper()` — no alias
  canonicalisation — so the alias key seeded its own full pre-launch placeholder sweep as an independent phantom venue.
- Rules out both originally-framed hypotheses: not a live writer (population is capped by a fixed historical launch-date
  window, not growing) and not the `canonical-migration-defi-rebuild-20260806-223130` VM surfacing old GCS objects
  (chronologically impossible — the rebuild started 2026-08-06, a day after these rows' `written_at`, and 0 GCS objects
  exist to surface anyway).

## Fix (shipped this session)

`instruments-service/scripts/enumerate_expected_universe.py::_yield_v2_defi_pre_launch_rows`: canonicalises
`venue_label` via `VenueMapping._canonicalise_defi_protocol_spelling(protocol.upper())` — the identical fix already
applied to the per-instrument v2 path in the same file (line ~1542) — and tracks emitted `(chain, venue_label)` pairs so
the canonical and alias dict keys (which now both resolve to the same `venue_label`) don't double-emit every pre-launch
row for that venue. Regression test added:
`tests/unit/scripts/test_enumerate_expected_universe_v2.py::test_defi_v2_pre_launch_alias_key_not_duplicated`.

Deliberately NOT touched: `chain_env.py`'s `PROTOCOL_LAUNCH_DATES` dict itself — the `AAVEV3` key's own comment says
"alias: no-underscore form used by some callers," implying other consumers may do a direct dict lookup by the bare
spelling; removing the key blind risked breaking them. The enumerator-side canonicalisation fix is scoped to the actual
defect (phantom-venue emission) without touching a registry other code may depend on.

## Impact / what's still open

- **Not urgent, not paging** — the bad data is a bounded, dormant historical artifact (zero real captured rows at risk),
  and the code fix prevents it from ever re-materialising on a future re-enum.
- **Historical row purge is `[OPERATOR]`-gated, not done here** — the existing 46,300 `empty_confirmed` manifest rows
  still need a human-gated `--apply` purge (same `gcs-and-manifest-delete-safety-protocol.md` path already used for the
  gas_fees/GMX purges) once someone confirms no twin-exists collision against real `AAVE_V3` pre-launch rows for the
  same window.
- **`chain_env.py`'s alias-dict-key pattern itself is unaddressed** — the same class of bug (a bare-spelling alias key
  in `PROTOCOL_LAUNCH_DATES` + naive `.upper()` iteration elsewhere) could reproduce for any future protocol given a
  similar alias entry. A design question (should `PROTOCOL_LAUNCH_DATES` keep alias dict-keys at all, vs. resolving
  aliases inside a `get_protocol_launch_date()` accessor), not resolved here.

## Todos

- [x] [CODE] P2. Canonicalise `venue_label` + dedup emitted `(chain, venue)` pairs in `_yield_v2_defi_pre_launch_rows` —
      `instruments-service` (this session, uncommitted pending QG/quickmerge).
- [ ] [OPERATOR] P2. Purge/re-key the 46,300 bare-`AAVEV3` `empty_confirmed` manifest rows via the human-gated `--apply`
      delete path (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`), after confirming no twin-exists
      collision against real `AAVE_V3`-ETHEREUM pre-launch rows for the same 2018-01-01..2023-01-26 window.
- [ ] [DESIGN] P3. Decide whether `chain_env.py`'s `PROTOCOL_LAUNCH_DATES` should keep alias dict-keys at all vs.
      resolving aliases inside a `get_protocol_launch_date()`-style accessor, removing the defensive- canonicalisation
      burden from every future iterator-style consumer of the raw dict.

## Progress Log

- **2026-08-08 (interactive session, `/autonomous`)**: sub-agent root-caused (see Finding); this session applied the
  code fix + regression test directly (bounded, low-risk, mirrors an already-shipped identical fix in the same file)
  rather than only filing the finding, per the operator's "finish everything" directive. QG + quickmerge pending as of
  this entry — see the parent tracker doc's Progress Log for the shipped SHA once landed.
