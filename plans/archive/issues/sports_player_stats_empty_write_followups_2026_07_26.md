---
doc_type: issue
title:
  Follow-up hardening from the self-caused player_stats empty-write incident — GCS retention gap + audit sibling scripts
summary: >-
  Two unacked follow-up items carried over while archiving
  `sports_player_stats_normalize_empty_write_incident_2026_07_26.md` (RESOLVED — 240/240 objects remediated via live
  api_football re-fetch, root cause fixed in the normalization script). Splitting these into their own UNACKED issue doc
  rather than leaving them stranded in the now-archived incident doc, since `plans/active/issues/` docs archive on ack
  per `/codex/11-project-management/issue-doc-lifecycle.md` and the incident's own parent batch plan
  (`sports_satellite_ao_dispatch_batch5_2026_07_26.md`) is already at its 1000-line hard cap with no room to absorb
  them. (1) the affected bucket has no GCS object versioning / soft-delete retention, which is why the original 240
  objects were unrecoverable and had to be remediated via external re-fetch rather than restore — an infra/operator
  decision on cost vs blast-radius reduction. (2) the root-cause bug class (a script builds a `pd.DataFrame(records)`
  from a possibly-empty `records` list and writes it without checking for an empty result) may exist in other one-off
  canonical-rewrite scripts in `instruments-service/scripts/` — needs an audit pass.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [sports, data-correctness, player-stats, follow-up, infra, audit]
related:
  [
    /plans/archive/issues/sports_player_stats_normalize_empty_write_incident_2026_07_26.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
  ]
created: 2026-07-26
priority: P2
parent_epic: sports_master
source:
  "Carried over from sports_player_stats_normalize_empty_write_incident_2026_07_26.md's Follow-up todos at archival time
  (cicd plan_health wall fix, escalation agt-d65e83)"
execution_scope: local-only
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by: cross-repo quick-fix batch, 2026-07-28
---

> **🟢 RESOLVED 2026-07-28.** Both follow-ups closed: (1) GCS soft-delete retention verified fleet-wide 2026-07-27
> (already `[x]`); (2) the empty-write-guard audit across `instruments-service/scripts/` found ONE genuine gap
> (`recover_fixtures_from_truthset.py::_write_per_league_parquet`) and fixed it — `instruments-service@696921d3`. Every
> other candidate script already had an equivalent guard (row-count invariants, `if x.empty:` checks, or a
> structurally-safe write model) — see the todo below for the full per-script verdict list.

# Follow-up hardening from the player_stats empty-write incident

## What I found

While archiving the resolved incident doc (mechanical fix for the `check_terminal_status_archived.py` plan-hygiene gate
— resolved issues must not sit in `plans/active/issues/`), it carried two open `- [ ]` follow-up todos that would
otherwise be stranded in `plans/archive/` (invisible to the backlog derivation, which only reads `plans/active/*.md`).
Filing them here as their own UNACKED issue so they stay dispatchable.

## Todos

- [x] ✅ [OPERATOR] P2. **RESOLVED 2026-07-27** — fresh-checked via
      `gcloud storage buckets describe gs://<bucket> --format="value(soft_delete_policy.retentionDurationSeconds)"`
      against all 3 `-prd-` sports buckets: `instruments-store-sports-prd-central-element-323112` = `604800`,
      `features-sports-prd-central-element-323112` = `604800`, `market-data-tick-sports-prd-central-element-323112` =
      `604800` (all 7-day soft-delete retention, none disabled). This is the exact fix
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a's fleet baseline records as having been applied to
      this exact bucket on 2026-07-26 (the sole fleet exception at audit time, fixed same day via
      `gcloud storage buckets update ... --soft-delete-duration=7d`) — this todo's ask is now satisfied fleet-wide for
      the sports asset_group; no further action needed. No code change, an infra-state verification only.
- [x] [SCRIPT] P3. ✅ **DONE 2026-07-28 — `instruments-service@696921d3`.** Audited every candidate script under
      `instruments-service/scripts/` that writes canonical GCS output (narrowed via `conditional_upload_bytes`/
      `upload_bytes`/`to_parquet` grep, then a `pd.DataFrame(records)`-from-a-list-construction filter). One-line
      verdict per script: - `normalize_nested_player_stats_2026_07_26.py` — already guarded (this incident's own fix). -
      `remediate_empty_player_stats_incident_2026_07_26.py` — read-back-verifies every write; N/A. -
      `recover_fixtures_from_truthset.py::_write_per_league_parquet` — **GAP FOUND, FIXED**: builds `pd.DataFrame(rows)`
      from a list param with no defensive check; the sole caller's `defaultdict(list)` structurally prevents an empty
      call today, but the function itself had zero protection. Added `if not rows:       raise ValueError(...)` matching
      the incident's own fix pattern. - `backfill_asset_group_blank_repair_2026_07_15.py` /
      `backfill_is_source_blank_and_available_at_null_2026_07_26.py` — in-place column-patch on an existing non-empty
      target, row-count invariant (dry-run explicitly logs `len(tgt)==len(new_df)`); not vulnerable. -
      `delete_cefi_blank_data_type_orphan_rows_2026_07_15.py` / `dereg_purge_24_leagues_2026_07_13.py` /
      `drop_out_of_universe_league_dirs_14231_315_2026_07_25.py` — gold-standard: pre-write backup + hard-abort
      row-count/league-count invariant asserts; not vulnerable. - `dedup_canonical_player_stats_2026_07_25.py` —
      `keep="first"` dedup can't zero out data structurally; not vulnerable. -
      `delete_cross_ag_phantom_rows_sports_manifest_2026_07_27.py` /
      `reconcile_mdps_odds_horizon_bucket_eu_grain_       2026_07_13.py` / `..._venue_grain_2026_07_14.py` — targeted
      small-subset deletes from a large existing catalog, `n_deleted==0`-guarded; not vulnerable. -
      `migrate_orphaned_mtds_odds_api_bucket_rows_2026_07_13.py` — `if src.empty:` guard present. -
      `fixtures_eu_truthset_flip_2026_07_13.py` / `fixtures_trickle_resolution_2026_07_13.py` — `if flip.empty:` guard
      present. - `validate_datapoint_schema_id.py::_flush_shard` — `if not rows: return` guard present. -
      `backfill_teams_61_leagues_2026_07_13.py` — upstream `if rows:` guard before any write. -
      `backfill_spot_asset_population_2026_07_16.py` / `backfill_orphan_class_e.py` — append-only merge (can't shrink to
      zero) + pre-write backup; per-object `if n_rows == 0: SKIPPED_JUNK` guard before transform. -
      `repair_tradfi_instrument_type_counts_2026_07_17.py` — `if df.empty:` input guard. -
      `restamp_fixtures_manifest_legacy_atom_2026_07_24.py` — explicit row-count-invariant hard check (never adds/drops
      rows). - `recency_masked_adjudication_2026_07_13.py` / `gw_false_empty_repair_2026_07_14.py` /
      `recon_dereg_collisions_2026_07_13.py` / `audit_instruments_store_legacy_gcs_delete_list.py` — write LOCAL report
      files or a fresh derived audit artefact, not an in-place canonical rewrite; an empty write here doesn't destroy
      existing canonical data. Out of the incident's bug class. - `enumerate_expected_universe.py` —
      `Lifecycle: permanent` (not a one-off script per this todo's own scope); left untouched, out of scope. Repo:
      instruments-service. Done-when criterion met: every matching script has the guard or is confirmed not to need it,
      one-line note per script (above).

## Progress Log

- 2026-07-26 (cicd, slot 6): Filed while archiving the parent incident doc to clear the `plan_health` hygiene-sweep hard
  failure (`check_terminal_status_archived.py`); no code change, doc-only split.
- 2026-07-28 (cross-repo quick-fix batch): Audited every candidate `instruments-service/scripts/` canonical-rewrite
  script for the same missing empty-write guard. Found one genuine gap (`recover_fixtures_from_truthset.py`), fixed it
  (`instruments-service@696921d3`), confirmed via `quality-gates.sh --no-fix` full green (5009 passed). Both todos now
  closed; archiving.
