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
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
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
      `instruments-service@2b2e9f124`, QG-verified + regression test added.
- [ ] [OPERATOR] P2. Purge the 46,300 bare-`AAVEV3` `empty_confirmed` manifest rows via the human-gated `--apply` delete
      path (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) against bucket
      `market-data-tick-defi-prd-central-element-323112`. **Twin-exists-collision precondition CONFIRMED SATISFIED
      2026-08-09** (see Progress Log) — full-population live-manifest check found 0 of the 46,300 bare cells lacking a
      correct-key `AAVE_V3`-ETHEREUM twin; this is a pure duplicate-row purge, not a re-key. Still needs the operator's
      `--apply` run (Part 1 "0 backing GCS objects" not independently re-verified this session — re-confirm fresh per
      §3a before executing, or cite the original investigation's finding).
- [ ] [DESIGN] P3. Decide whether `chain_env.py`'s `PROTOCOL_LAUNCH_DATES` should keep alias dict-keys at all vs.
      resolving aliases inside a `get_protocol_launch_date()`-style accessor, removing the defensive- canonicalisation
      burden from every future iterator-style consumer of the raw dict.

## Progress Log

- **2026-08-08 (interactive session, `/autonomous`)**: sub-agent root-caused (see Finding); this session applied the
  code fix + regression test directly (bounded, low-risk, mirrors an already-shipped identical fix in the same file)
  rather than only filing the finding, per the operator's "finish everything" directive. Shipped
  `instruments-service@2b2e9f124` (QG-green, `test_defi_v2_pre_launch_alias_key_not_duplicated` added). Remaining work
  is genuinely open (not this session's to do): the `[OPERATOR]`-gated historical row purge, and the `[DESIGN]` question
  on `PROTOCOL_LAUNCH_DATES`'s alias-key pattern — status stays `open`, not `resolved`, until both clear.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (3 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- Root-cause + code fix already shipped
  (instruments-service@2b2e9f124). 2 remaining open items both explicitly gated: an `[OPERATOR]` human-executed
  manifest-row purge (46,300 rows, delete-safety hard-stop) and a `[DESIGN]` judgment call on alias dict-keys.
  Corroborated by sibling doc `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`. Doc stays
  `assigned_vm: NA`.
- **2026-08-09 (interactive session, twin-collision confirmation — read-only, no `--apply` run)**: dispatched to answer
  the `[OPERATOR]` todo's blocking precondition ("confirm no twin-exists collision against real `AAVE_V3`-ETHEREUM
  pre-launch rows"). **Verdict: CONFIRMED SAFE — no collision, purge is unblocked for operator go-ahead on `--apply`.**

  **Bucket correction**: the 46,300 rows do NOT live in `instruments-store-defi-prd-{pid}` (checked first, 0 hits —
  `enumerate_expected_universe.py`'s `service_name=instruments-service` attribution refers to the WRITER, not the
  bucket). The actual manifest is `market-data-tick-defi-prd-central-element-323112` — `_default_bucket_for("defi")`
  resolves `resolve_bucket_name(kind="market-data", asset_group="defi")` for the DeFi v2 pre-launch pass
  (`instruments-service/scripts/enumerate_expected_universe.py:392-419`).

  **Live re-confirmation of the 46,300 figure**: read `_index/availability_index.parquet` directly (3,003,002,411 bytes,
  generation 1786282240969913, last_modified 2026-08-09T13:30:40Z) via `gcs_describe_object` +
  `gcs_read_object_with_generation` — row-group-filtered
  `pyarrow.parquet.read_table(filters=[("venue","in", ["AAVEV3","AAVE_V3"])])`, no whole-corpus walk.
  `venue=AAVEV3, chain=ETHEREUM, capture_status=empty_confirmed` = exactly 46,300 rows, live, today — the doc's figure
  is current, not stale.

  **Twin-collision check — FULL POPULATION, not a sample** (cheap enough once the parquet was fetched: 1,208,829
  matching rows total). Built `(date, data_type)` cell sets: bare `AAVEV3` = 46,300 unique cells; correct
  `AAVE_V3`+`chain=ETHEREUM` = 53,506 unique cells (superset spanning full historical + post-launch range). **Bare cells
  lacking a correct-key twin: 0.** Every one of the 46,300 bare `(date, data_type)` cells already has a matching
  correct-key `AAVE_V3`-ETHEREUM row.

  **Content-verify (delete-safety Part 2, not just existence)**: restricting correct-key rows to exactly the bare cells'
  `(date, data_type)` set gives 48,176 rows — `capture_status=empty_confirmed`: **exactly 46,300**, a perfect 1:1 match
  against the bare rows. The remaining 1,876 are `capture_status=captured` (real data) for a subset of cells —
  specifically `data_type=lending_indices` on dates late Dec 2022/early Jan 2023, `written_at=2026-08-07*` — i.e.
  genuine early capture success shortly before the registered 2023-01-27 launch date, filed under the CORRECT key and
  entirely untouched by any purge of the wrong-key duplicates (worth a separate note that `PROTOCOL_LAUNCH_DATES`'s
  2023-01-27 AAVE_V3-ETHEREUM date may be a few weeks conservative for `lending_indices` specifically — not a
  delete-safety concern, not filed as a new todo since it doesn't block or need this purge). **Root-cause
  corroboration**: the correct-key `empty_confirmed` rows' `written_at` set includes `2026-08-05T04:08:15.957401+00:00`
  — the IDENTICAL bulk-write timestamp as the 46,300 bad bare rows. This directly confirms the original root-cause
  mechanism: the pre-fix enumerator run iterated BOTH the canonical `("ETHEREUM","AAVE_V3")` and alias
  `("ETHEREUM","AAVEV3")` `PROTOCOL_LAUNCH_DATES` entries in the SAME pass, correctly seeding the real pre-launch
  placeholders AND erroneously seeding the duplicate bare sweep in one shot — the "twin" is the sibling of the very same
  buggy run, not a coincidence or later backfill.

  **Why this means SAFE, not just "twin exists"**: manifest rows are keyed independently — deleting a row at the WRONG
  key (`venue=AAVEV3`) cannot affect a row at a DIFFERENT key (`venue=AAVE_V3`); the correct-key rows stay untouched
  regardless of the bare-key purge. Since every bare cell's data is already fully and correctly represented under the
  right key (both `empty_confirmed` pre-launch placeholders 1:1, and, where applicable, real `captured` data), the purge
  is a **pure duplicate-row delete, not a re-key** — nothing needs migrating first.

  **Independent re-verification of the "fix shipped" claim (task step 4, not just trusting the doc)**:
  `git merge-base --is-ancestor instruments-service@2b2e9f124 HEAD` → yes, ancestor of current HEAD (`56243ea1`). Read
  the LIVE `_yield_v2_defi_pre_launch_rows` (lines 1411-1505,
  `instruments-service/scripts/enumerate_expected_universe.py`): canonicalises
  `venue_label = VenueMapping._canonicalise_defi_protocol_spelling(protocol.upper())` and dedups via an
  `_emitted_chain_venues: set[tuple[str,str]]` guard before emitting, with an inline comment citing this doc by name.
  Ran the regression test directly (not just confirmed it exists):
  `pytest tests/unit/scripts/test_enumerate_expected_universe_v2.py::test_defi_v2_pre_launch_alias_key_not_duplicated` →
  **1 passed**. Confirmed `chain_env.py:198-199` still carries both `("ETHEREUM","AAVE_V3")` and `("ETHEREUM","AAVEV3")`
  exactly as documented (deliberately kept). Grepped every live `PROTOCOL_LAUNCH_DATES.items()` consumer workspace-wide:
  only 3 hits — the now-fixed enumerator, a `derive_protocol_launch_dates.py` validation script (not a manifest writer),
  and a `chain_env.py` internal ghost-alias-to-canonical dict-normalization comprehension (not a manifest writer
  either). No other live writer at risk of reproducing this specific bug. (The broader "any future protocol given a
  similar alias key" risk is the still-open `[DESIGN]` todo below — untouched, out of scope here.)

  **Informational, for the eventual `--apply` (not used this session — read-only, no delete executed)**:
  `gcs_bucket_soft_delete_retention_seconds("market-data-tick-defi-prd-central-element-323112")` → `604800`s (7 days,
  fresh-checked 2026-08-09) — qualifies for the §3a reversibility carve-out if the operator wants an agent-autonomous
  execution path; re-check fresh at actual `--apply` time per §3a discipline, never reuse this session's number.

  **Caveat — what this session did NOT do**: did not independently re-verify "0 live GCS objects back the bare `AAVEV3`
  path" (Part 1 of the 5-part proof for the bare side) — relied on the original 2026-08-08 investigation's finding. That
  is a different question from the twin-collision check this session was scoped to answer (which is about the CORRECT
  side), so it doesn't block this precondition's SATISFIED verdict, but the operator's `--apply` run should still
  independently confirm it fresh (or explicitly cite the 2026-08-08 finding) before executing, per the delete-safety
  doc's "fresh, never assumed" discipline.

  Sanctioned mechanics only: `gcs_describe_object`, `gcs_read_object_with_generation`,
  `gcs_bucket_soft_delete_retention_seconds` (all from `unified_trading_library.cloud_interface`); no
  `gcs_delete_object`/`gcs_conditional_delete` call made; no `gsutil`/`gcloud storage` subprocess.
