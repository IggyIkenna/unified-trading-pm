---
doc_type: issue
title:
  T6.8 one-off retirement — residual instruments-service/scripts + include_legacy_archive knob need individual review
summary: >-
  T6.8 (sports_legacy_cutover_closeout_tasks_2026_07_24.md) instructed a blanket delete of "~26 legacy-reading
  instruments-service/scripts/** one-offs" plus retiring the `include_legacy_archive` UAC knob to zero hits
  workspace-wide. Per-file verification (git history + import graph, not just the bucket-string grep the ~26 estimate
  was based on) found the blanket premise WRONG for a meaningful subset: 3 files are Lifecycle=permanent (not one-offs
  at all), 2 are gated on a much broader unfinished "all asset_groups" campaign, several were touched with real feature
  commits in the last ~10 days (still active), and `migrate_sports_canonical_v9.py` is still imported by a live
  2026-07-13 migration script -- deleting it as originally instructed would have broken that import (caught before
  shipping). This doc tracks the safely-verified deletions actually shipped vs. the residual that needs dedicated
  follow-up.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [sports, one-off-retirement, false-progress, script-lifecycle, residual]
related:
  [
    /plans/archive/sports_legacy_cutover_closeout_tasks_2026_07_24.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: 2026-07-25
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
drift_direction: worsening-slowly
depends_on: []
source:
  [
    "Found 2026-07-25 while executing T6.8 (sports_satellite_ao_dispatch_batch2-005) -- per-file Delete-when +
    git-history + import-graph verification (not trusting the todo's own '~26, all satisfied once T5.4 landed' summary)
    surfaced a materially different picture than the todo assumed.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# T6.8 one-off retirement — what shipped vs. what's residual

## What I found

T6.8's mechanism claim was: "per each file's own `Delete-when` (all satisfied once T5.4 landed + orphan-sweep = 0 — both
independently verifiable facts, check first)." That claim is TRUE for the 5 explicitly-named files and 6 of the "~26"
instruments-service/scripts one-offs I could independently verify — but FALSE for the rest of the ~26 estimate, which
was grep-derived (every `instruments-service/scripts/**` file matching `sports-central-element-323112`) rather than
individually vetted against each file's actual `Lifecycle`/`Delete-when` header and git history.

### Shipped (verified safe, deleted this session)

**market-tick-data-service** (`market-tick-data-service@<pending-sha>`):

- `market_tick_data_service/scripts/verify_v1_archive_row_coverage_2026_06_27.py` — never run (only "GATE SCRIPT
  SHIPPED" evidence existed); its subject (`sports_reference_v1_archive/`) is now fully deleted (398 objects, DONE
  2026-07-16T09:37Z per `sports_legacy_bucket_cutover_history_2026_07_24.md` T2.1), so this script can never run
  meaningfully again — doubly broken.
- `scripts/migrate_legacy_tick_buckets_to_canonical.py` — Delete-when OR-clause satisfied: E8 deleted
  `market-data-tick-sports-central-element-323112`.
- `scripts/patch_l6_legacy_manifest_mtds_2026_06_29.py` — same OR-clause; also L6-legacy-only confirmed GREEN (0 cells)
  in the archived canonicalisation plan's E8 audit (2026-06-29 re-run).
- `tests/unit/scripts/test_migrate_sports_canonical_v9.py` — unit test OF the (still-present, see below)
  `migrate_sports_canonical_v9.py`; NOT deleted (see residual). Correction: this test was staged for deletion then
  restored once the `migrate_sports_canonical_v9.py` dependency was found — see below.

**instruments-service** (`instruments-service@<pending-sha>`):

- `scripts/patch_l6_legacy_manifest_is_2026_06_29.py` — Delete-when ("L6 gate GREEN on IS surface confirmed")
  independently verified via the archived plan's 2026-06-29 E8 audit re-run:
  `L6-legacy-only ✅ GREEN (0 legacy-only cells, IS L6 migration applied by slot-3)`.
- `scripts/rebuild_sports_manifest.py` — superseded by `market-tick-data-service/.../rebuild_sports_manifest_v9.py` (the
  `--surface {mdps,instruments}` unified v9 rebuild tool the archived plan's E8 log actually used); no recent commits
  beyond the 2026-06-23 lifecycle-stamp pass.
- `scripts/sports_legacy_schema_audit.py` + `scripts/sports_legacy_schema_audit.json` — feeds
  `validate_sports_fixtures_v2_parity.py` (deleted alongside); no independent consumer.
- `scripts/validate_sports_fixtures_v2_parity.py` + `scripts/sports_legacy_parity_report.json` — its own pre-requisite
  check gates `cutover_sports_fixtures_v2_to_canonical.py`, whose own commit message confirms the cutover it validates
  already executed ("Phase 4 cutover EXECUTED — 398 days, zero LEGACY remaining", 2026-04-28) — deleted alongside.
- `scripts/cutover_sports_fixtures_v2_to_canonical.py` + `scripts/sports_legacy_cutover_report.json` — cutover confirmed
  executed per its own commit history, well before the current T5/T6 bucket-deletion work even started.

No test files existed for any of the 5 instruments-service deletions (checked before deleting).

### Residual — NOT deleted, needs dedicated follow-up

**1. The `migrate_sports_canonical_v9.py` cluster (market-tick-data-service)** — T6.8 named this file explicitly for
deletion; I staged it, then found `market_tick_data_service/scripts/migrate_sports_instruments_legacy_gap_2026_07_13.py`
(a 2026-07-13 migration script, itself last touched 2026-07-15) has a REAL
`from market_tick_data_service.scripts.migrate_sports_canonical_v9 import (...)` at line 141 — deleting the base file
would have broken this import. Restored `migrate_sports_canonical_v9.py` + its test before shipping.

- HOWEVER: `migrate_sports_instruments_legacy_gap_2026_07_13.py`'s own Delete-when ("after this migration's --apply has
  run once and the plan's IS L6-legacy-only REAL data-loss slice re-audits to 0") looks SATISFIED per the archived
  canonicalisation plan's "Migration executed + L6 gate re-run (2026-07-15" entry:
  `written_captured=31301 (of 31301 candidate rows)`, `0 dropped`, read-back verified non-empty — and that same entry
  explicitly calls `migrate_sports_instruments_legacy_gap_2026_07_13.py`'s old-floor comment "inert, no behaviour
  depends on them."
- **Recommendation**: delete these 4 together in a follow-up, once someone re-confirms no OTHER caller of
  `migrate_sports_canonical_v9.py` exists (I found none beyond this cluster, but didn't do a full import-graph sweep
  across `deployment-service`/`features-service`/etc. — only within market-tick-data-service):
  `market_tick_data_service/scripts/migrate_sports_canonical_v9.py`,
  `market_tick_data_service/scripts/_migrate_mdps_reconcile.py` (private helper, extracted only to serve the above),
  `market_tick_data_service/scripts/_migrate_sports_reconcile.py` (same), and
  `market_tick_data_service/scripts/migrate_sports_instruments_legacy_gap_2026_07_13.py`. Also check its own 2026-07-13
  sibling cluster before deleting anything further: `write_sports_instruments_legacy_gap_manifest_2026_07_13.py`,
  `fix_sports_fixtures_venue_blank_2026_07_13.py`, `fix_sports_instrument_count_zero_anomaly_2026_07_13.py`, and the
  test `tests/unit/scripts/test_migrate_sports_reconcile_coverage.py` — I did not evaluate these individually.

**2. `include_legacy_archive` knob retirement (unified-api-contracts)** — NOT retired this session.
`instruments-service/scripts/census_fixture_events_schema_variants_2026_07_25.py` (created TODAY, 2026-07-25) calls
`candidate_parquet_paths(..., include_legacy_archive=True)` at line 119 — a genuinely live caller, so ripping the param
out of `unified_api_contracts/canonical/domain/sports/gcs_paths.py` (`candidate_parquet_paths`/`candidate_parquet_uris`)
and the passthrough in `unified_api_contracts/canonical/partition_paths.py` would break it right now.

- HOWEVER: the archive path this knob adds (`sports_reference_v1_archive/...`) is confirmed to have ZERO objects (fully
  deleted 2026-07-16, see above) — so the knob is functionally vestigial for this caller (the extra candidate path will
  never match). Retiring it is safe PROVIDED the caller is fixed in the SAME change.
- **Recommendation**: (a) drop `include_legacy_archive=True` from the `candidate_parquet_paths(...)` call in
  `census_fixture_events_schema_variants_2026_07_25.py`; (b) remove the `include_legacy_archive` parameter + its 2
  `if include_legacy_archive:` blocks from `candidate_parquet_paths`/`candidate_parquet_uris` in
  `unified_api_contracts/canonical/domain/sports/gcs_paths.py`; (c) remove the
  `kwargs.get("include_legacy_archive", False)` passthrough + docstring mention in
  `unified_api_contracts/canonical/partition_paths.py`; (d) re-verify `rg 'include_legacy_archive'` → zero hits
  workspace-wide (not just the narrower `=True` check).

**3. Remaining ~14 instruments-service/scripts files that matched the original bucket-string grep but are NOT safe to
delete as a blanket set** — kept, with reasons:

- `Lifecycle: permanent` (not one-offs — must NOT delete): `reconcile_phantom_manifest_rows.py`,
  `rescan_sports_fixtures_canonical.py`, `rescan_sports_manifest.py`.
- Gated on a MUCH broader unfinished campaign ("instruments-service manifest-canonicalisation complete for all
  asset_groups"), not just sports: `canonicalize_gcs_league_paths.py`, `canonicalize_manifest_league_ids.py`.
- Recent real feature commits (last ~10 days) prove active, non-dead: `reconcile_manifest_from_per_league_parquets.py`
  (2026-07-13), `backfill_sports_per_entity_manifest.py` (2026-06-25), `fill_missing_player_stats.py` (2026-07-15),
  `backfill_per_league_record_empty.py` (2026-07-17).
- Delete-when condition not independently verifiable without deeper manifest inspection than this session did:
  `purge_legacy_unsharded_manifest_rows.py`, `add_canonical_fixture_ids.py`, `backfill_weather.py`,
  `backfill_sports_fixture_stats_manifest.py` (+ its `sports_legacy_migration_report.json` +
  `sports_fixture_stats_manifest_backfill_report.json` outputs), `migrate_bare_to_per_league.py`,
  `migrate_entity_paths.sh`. These all carry a Delete-when phrase like "after prod-run confirmed" or "manifest captured
  count climbed" that needs a live-manifest check (or an operator confirmation) to close honestly, not a grep-based
  inference.
- `sports_per_entity_manifest_backfill_report.json` — tied to `backfill_sports_per_entity_manifest.py` (kept above), so
  kept too.

## Why it matters

T6.8's "~26, all satisfied once T5.4 + orphan-sweep=0" framing would have deleted 3 permanent-lifecycle production tools
and broken a live import chain (`migrate_sports_canonical_v9.py`) if executed literally without per-file verification.
The corrected, narrower scope (11 files actually deleted) is real progress with zero collateral risk; the residual above
is genuine follow-up work, not silently dropped scope.

## Recommended decision

- [ ] [BACKEND] P2. Delete the `migrate_sports_canonical_v9.py` cluster (4 files, see Residual §1) after confirming no
      other caller exists workspace-wide and evaluating the 3 sibling 2026-07-13 scripts + their test. (repo:
      market-tick-data-service)
- [ ] [BACKEND] P2. Fix `census_fixture_events_schema_variants_2026_07_25.py` to drop `include_legacy_archive=True`,
      then retire the `include_legacy_archive` knob entirely from `gcs_paths.py`/`candidate_parquet_uris` +
      `partition_paths.py`'s passthrough; re-verify zero `include_legacy_archive` hits workspace-wide. (repos:
      instruments-service, unified-api-contracts)
- [ ] [DATA] P3. For the 6 Delete-when-unverifiable instruments-service one-offs (§3 third bullet), do a live-manifest
      check per file's stated condition (e.g. "manifest captured count climbed", "purge confirmed in live consolidated
      _index") and delete or keep accordingly. (repo: instruments-service)
