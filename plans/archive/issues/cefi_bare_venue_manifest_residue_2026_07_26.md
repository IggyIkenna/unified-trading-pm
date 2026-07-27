---
doc_type: issue
title: Bare COINBASE/OKX venue rows in the CEFI instruments-service manifest are stale pre-canonicalization residue
summary: >-
  The deployment-ui Axis Value Census panel (asset_group=cefi) surfaces 2 manifest rows stamped venue=COINBASE and 2
  stamped venue=OKX (bare, no suffix). Investigation confirms both pairs exist ONLY for date in {2026-03-01,
  2026-03-02}, both written at the identical timestamp 2026-04-03T11:26:23Z (a single legacy batch write predating the
  2026-07-06/07-10/07-21 venue-canonicalization work), with blank instrument_type. The canonical twins (COINBASE-SPOT,
  COINBASE-FUTURES, OKX-SPOT, OKX-SWAP, OKX-FUTURES) all have real captured rows AND real GCS objects for the same 2
  dates, written later (2026-06-26) by a canonicalization-era re-run. A scoped GCS prefix listing under the current
  canonical hive path found zero objects for either bare label on either date. No backfill is needed (canonical data
  already exists); the only remaining action is deleting these 4 stray manifest rows. A dry-run/apply purge script is
  ready but not yet executed — see Progress Log.
status: resolved
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [instruments-service, unified-api-contracts, deployment-api]
scope: [engineer, admin]
tags: [cefi, manifest, venue, canonicalisation, delete-safety, data-correctness, axis-census]
related:
  [
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/distinct_values_noncanonical_audit_2026_07_20.md,
  ]
created: 2026-07-26
priority: P3
parent_epic: cefi_master
source: "operator, interactive session, spotted via deployment-ui Axis Value Census panel (asset_group=cefi)"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by: "operator, ran purge_bare_cefi_venue_residue.py --apply from own shell, 2026-07-26T23:41:53Z"
locked_by:
---

# CEFI bare-venue (COINBASE/OKX) manifest residue

> **🟢 ARCHIVED 2026-07-27** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule.

## What happened

The `deployment-ui` Axis Value Census panel
(`GET /data-status/axis-value-census?service=instruments-service&asset_group=cefi`,
`deployment-api/deployment_api/routes/data_status/_axis_census.py`) shows the raw `venue` axis carrying 2 entries that
don't match the current canonical venue vocabulary:

- `COINBASE` — 2 rows
- `OKX` — 2 rows (bare `OKX` IS a currently-declared canonical venue per `VENUES_BY_ASSET_GROUP['cefi']`
  (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:289`), kept as one of two cefi
  `FUTURE_BUNDLE_VENUES` members — but these specific 2 rows are NOT an example of that usage, see below)

## Investigation (read-only, this session)

Targeted read of the consolidated `_index/availability_index.parquet` for
`gs://instruments-store-cefi-prd-central-element-323112` via UTL's `read_availability_index()` (not a full-corpus walk):

```
      date    venue instrument_type   data_type        service_name capture_status              source             pipeline_mode  instrument_count                       written_at
2026-03-01 COINBASE                 instruments instruments-service       captured instruments_service batch_instruments_service                69 2026-04-03T11:26:23.197977+00:00
2026-03-02 COINBASE                 instruments instruments-service       captured instruments_service batch_instruments_service                69 2026-04-03T11:26:23.197977+00:00
2026-03-01      OKX                 instruments instruments-service       captured instruments_service batch_instruments_service                77 2026-04-03T11:26:23.197977+00:00
2026-03-02      OKX                 instruments instruments-service       captured instruments_service batch_instruments_service                77 2026-04-03T11:26:23.197977+00:00
```

Both pairs: same 2 dates, same `written_at` timestamp (one legacy batch run), blank `instrument_type` (a plain
venue-catalog snapshot row, not a `futures_chain`/`combo` bundle — so not the registry's intended future use of bare
`OKX`). Across the full manifest history (2019-03-30 → 2026-07-26, 84,441 rows total for this bucket), these are the
**only** rows ever stamped with either bare label — nowhere else, no other dates.

For the same 2 dates, the canonical venues already have real, later, larger captures (all `capture_status=captured`,
written 2026-06-26):

| venue            | 2026-03-01 | 2026-03-02 |
| ---------------- | ---------- | ---------- |
| COINBASE-SPOT    | 409        | 409        |
| COINBASE-FUTURES | 187        | 187        |
| OKX-SPOT         | 763        | 768        |
| OKX-SWAP         | 304        | 305        |
| OKX-FUTURES      | 20+24      | 20+24      |

A scoped GCS prefix listing (`instrument_availability/by_date/day=2026-03-0{1,2}/`, not a whole-bucket walk) confirmed
real objects exist at the canonical hive path for all 5 canonical venues on both dates, and **zero objects** exist under
`venue=COINBASE/` or `venue=OKX/` (bare) at that same path shape.

**Root cause (inferred, not exhaustively proven):** the bare-labeled rows are a pre-canonicalization writer artifact
from before the `coinbase_bare_name_migration_2026_07_06.md` rekey and the `OKX-SPOT`/`OKX-SWAP`/`OKX-FUTURES` venue
splits (2026-07-10, 2026-07-21). The same 2 calendar dates were correctly re-captured under canonical venue names by a
later run (2026-06-26), making the bare rows redundant residue.

## Five-part delete-safety proof status (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`)

- **Part 1 (canonical twin resolves)**: ✅ confirmed — `capture_status=captured` rows + real GCS objects exist for all 5
  canonical venues on both target dates.
- **Part 2 (content verify, not just existence)**: ⚠️ NOT exhaustively done — did not pull the original April-era object
  (if it still exists under some older, pre-hive-reorder path shape) and diff its instrument-ID list against the June
  canonical catalog. Confidence is `yes-after-verify`, not `yes-twin-confirmed`.
- **Part 3 (no live writer)**: ✅ confirmed — bare `COINBASE` removed from `VENUE_TO_ADAPTER_KEY`/
  `VENUES_BY_ASSET_GROUP['cefi']`; `OKX-SPOT`/`-SWAP`/`-FUTURES` are now their own canonical venues, so no current
  writer emits `venue=COINBASE` or blank-instrument_type `venue=OKX` for a spot/swap/futures capture.
- **Part 4 (no live reader depends on these rows)**: ✅ likely — `expected_universe`/coverage denominators iterate
  `VENUES_BY_ASSET_GROUP` (forward-looking), not historical captured-row literal values; removing 2 historical rows for
  a defunct label shouldn't affect any expected-vs-actual accounting.
- **Part 5 (legacy-copied-not-moved invariant)**: N/A in the strict GCS-migration sense (this is a manifest-row
  question, not an object-migration one), but the same spirit is satisfied by Part 1.

**Disposition: `yes-after-verify`.** Per the protocol, "Human executes; agent suggests" — this doc exists so the
suggestion + evidence trail is durable; the actual `--apply` is a human (or explicitly-authorized) action, not an
autonomous one.

## Ready fix

A dry-run/apply purge script (mirrors `instruments-service/scripts/purge_pre_launch_manifest_rows.py`'s pattern:
CAS-protected write-back via `if_generation_match`, `--dry-run` default-safe) is in the session scratchpad. Dry-run
output matches the investigation above exactly — 4 rows, nothing else:

```
2026-03-01 COINBASE  cefi instruments captured  69  written 2026-04-03T11:26:23Z
2026-03-01 OKX       cefi instruments captured  77  written 2026-04-03T11:26:23Z
2026-03-02 COINBASE  cefi instruments captured  69  written 2026-04-03T11:26:23Z
2026-03-02 OKX       cefi instruments captured  77  written 2026-04-03T11:26:23Z
```

## Progress Log

- 2026-07-26: [OPERATOR] Finding surfaced via deployment-ui Axis Value Census panel. Read-only investigation completed
  (manifest read + scoped GCS prefix listing). Dry-run purge script written and executed (`--dry-run`, confirmed exact
  4-row match, no other rows touched). `--apply` **not yet executed** — pending operator run (or explicit
  in-conversation authorization distinct from the standing hard-stop in
  `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3, which the assisting agent held rather than
  self-authorize past on a verbal claim of a pending policy change — the file on disk at HEAD was verified unchanged,
  last real edit 2026-07-23, unrelated to this rule). Script location: session scratchpad
  (`purge_bare_cefi_venue_residue.py`), not yet committed to this repo.
- 2026-07-26T23:41:53Z: [OPERATOR] `--apply` executed directly by the operator from their own shell (not by the
  assisting agent — the agent held the hard-stop per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3
  through to the end, including after a pasted claim that the doc's § 3a had been quickmerge-updated to add an
  agent-autonomous carve-out; a fresh `git fetch origin` on `unified-trading-pm` at the time showed the remote HEAD for
  that file unchanged since 2026-07-23, so the claim did not check out and the agent declined to write the pasted text
  into the SSOT or act on it). Output: 84,441 → 84,437 rows, CAS write succeeded
  (`if_generation_match=1785109296367778`), zero collateral (script targets only
  `venue in {COINBASE, OKX} AND date in {2026-03-01, 2026-03-02} AND asset_group=cefi`). Post-delete verification
  (read-only `--dry-run` re-run): 0 matching rows remain, 84,437 total rows unchanged. **Resolved.**
