---
doc_type: plan
title: "Standardize odds_api's data_type casing to lowercase 'odds' — code + historical GCS migration"
summary:
  "The odds_api adapter writes uppercase 'ODDS' as data_type (both in manifest content AND embedded in the GCS object
  path) while the rest of the sports taxonomy (DATA_TYPES_BY_ASSET_GROUP, VM launcher env, validation) uses lowercase
  'odds'. Operator decision (2026-08-15): standardize on lowercase everywhere — fix the writer AND migrate ~17K
  historical rows. This is a real GCS rename migration, not a metadata edit, in a class that has already caused one
  documented incident (K1/K2 casing revert) — phased, with the risky step operator-gated."
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, instruments-service]
scope: [engineer, admin]
tags: [sports, data-correctness, migration, odds-api, casing]
related:
  [
    sports_honest_coverage_gap_closure_2026_08_14,
    sports_odds_api_scattered_multiyear_gaps_2026_07_27,
    sports_satellite_batch2_casing_direction_contradicts_k1k2_revert_2026_07_25,
    sports_taxonomy_p2_migration_2026_08_08,
    sports_odds_writer_flip_and_trades_path_retirement_2026_08_15,
  ]
parent_epic: sports_master
source: interactive-session
created: 2026-08-15
last_updated: 2026-08-15
drift_direction: advance-code
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py,
    unified-api-contracts/unified_api_contracts/registry/data_type_capability.py,
    unified-api-contracts/scripts/generate_instrument_catalogue.py,
    market-tick-data-service/scripts/sports/purge_footystats_odds_uppercase_phantom_2026_08_14.py,
    market-tick-data-service/scripts/drop_sports_odds_phantom_uppercase_2026_07_26.py,
    market-tick-data-service/scripts/sports/restamp_sports_trades_to_odds_2026_08_12.py,
    market-tick-data-service/scripts/sports/manifest_swap_trades_to_odds_2026_08_12.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
  ]
---

# Standardize odds_api's data_type casing to lowercase "odds"

## Why this exists (read before touching anything)

Two conventions currently coexist for the same concept: the sports taxonomy convention
(`DATA_TYPES_BY_ASSET_GROUP["sports"]`, the VM launcher's `VM_DATA_TYPES=odds`, `validate_data_type_for_venue`) uses
lowercase `"odds"`; the odds_api adapter (`odds_api_adapter.py`, the write statement stamping the capture record) writes
uppercase `"ODDS"`, and this has been true for every historical row it has ever produced (~17K rows carry this literally
in the `instruments-store-sports-prd-central-element-323112` / `market-data-tick-sports-prd` buckets). A
`unified-api-contracts` registry entry (`data_type_capability.py`,
`DataTypeCapability(data_type="ODDS", venue="ODDS_API")`) was found and deliberately left uppercase on 2026-08-15 rather
than "fixed" in isolation, because `generate_instrument_catalogue.py` does an exact-string match against it — re-casing
the registry entry alone would have silently broken that catalogue's coverage count without touching the real underlying
inconsistency. The operator has now ruled: fix it for real, everywhere, including the historical data.

**This is NOT a simple find-and-replace.** A read-only scoping pass (2026-08-15) found:

- `data_type` is embedded in the literal GCS object **path** for MTDS raw tick data (not just a manifest column) —
  standardizing casing means physically copying/renaming GCS objects, confirmed via two prior scripts
  (`purge_footystats_odds_uppercase_phantom_2026_08_14.py`, `drop_sports_odds_phantom_uppercase_2026_07_26.py`) using an
  identical `_candidate_prefixes()` path-construction pattern.
- **This exact migration class has already caused a real incident.** The K1/K2 casing migration
  (`market-tick-data-service` commits `2536b91c`→`f4dd8f8e`) did a copy+verify+CAS-swap of this shape, chose the WRONG
  direction first, and had to be reverted — see
  `sports_satellite_batch2_casing_direction_contradicts_k1k2_revert_2026_07_25.md` for the resulting confusion. **Do not
  repeat that mistake — confirm direction (uppercase→lowercase, not the reverse) explicitly before Phase 3 runs
  anything, and re-read that doc first.**
- **The ~17K count may be substantially phantom.** Two recent, similarly-shaped "uppercase ODDS" populations (a
  `market-data-tick-sports-prd` slice, 22,145 rows; a FOOTYSTATS-venue slice, checked 2026-08-14) both turned out to be
  phantom — no real GCS objects behind the manifest rows — and resolved via a cheap manifest-only purge, no GCS copy
  needed. **Do not assume the ODDS_API-venue population is real without checking it the same way first** — this could
  make the actual migration much smaller (or nonexistent) than it looks.
- **Live collision risk**: `mtds-backfill-odds-1` (launched 2026-08-15 ~04:40Z) is actively writing to this exact
  manifest surface right now. Phase 3 (any real GCS mutation) must not start until that VM reaches a terminal state —
  check `gcloud compute instances describe mtds-backfill-odds-1 --zone=asia-northeast1-c --format='value(status)'`
  before starting Phase 3, not just before Phase 1.

## Phase 0 — safe, isolated, no data touched

- [x] ✅ [SCRIPT] P1. Fix `odds_api_adapter.py`'s write statement (~line 767, `"data_type": "ODDS"`) to emit lowercase
      `"odds"` for all NEW writes going forward — `market-tick-data-service@324cbb59dd`. Confirmed the only occurrence
      in the file (grep). Existing `test_odds_api_live_batch_shard_parity.py` already asserted lowercase `"odds"` at
      multiple call sites (fixture data + a path assertion) — it was silently already covering the post-fix behavior,
      no test change needed. QG green.
- [x] ✅ [SCRIPT] P1. Transition-window handling — shipped as a lowercase SIBLING REGISTRY ENTRY instead of the
      generic case-fold stopgap originally specified here, since the scoping pass found exactly ONE real consumer
      needing this (`generate_instrument_catalogue.py`'s exact-string match against `data_type_capability.py`).
      `unified-api-contracts@3c6d38fe82` — added a second `DataTypeCapability(data_type="odds", venue="ODDS_API")`
      entry alongside the existing uppercase one, so the catalogue counts real rows of either casing during the
      transition. Replaced the now-superseded "must stay uppercase forever" test with
      `test_odds_api_capability_has_both_casings_during_the_lowercase_migration`, asserting both entries exist. QG
      green (after 3 retries — 2 were transient host-RAM-pressure/wall-clock-governor aborts unrelated to content, 1
      hit a genuinely-failing but unrelated LST-token-registry test from a concurrent peer commit that self-resolved
      before the next retry). Also survived a mid-session interruption: the uncommitted edit sat idle across a
      session restart, got correctly parked by a liveness-check hygiene sweep (`stash: "parked: peer odds_api
      casing-migration WIP (dead claim...)"`) rather than lost, and was restored cleanly.

## Phase 1 — live-check the real population (read-only, no mutation)

- [ ] [DATA] P1. BLOCKED-ON:mtds-backfill-odds-1-completion — live-probe the ODDS_API-venue uppercase population in
      `instruments-store-sports-prd-central-element-323112` / `market-data-tick-sports-prd` the same way
      `drop_sports_odds_phantom_uppercase_2026_07_26.py` and `purge_footystats_odds_uppercase_phantom_2026_08_14.py` did
      for their respective slices: for a representative sample (or the full set, if cheap enough) of the ~17K manifest
      rows carrying `data_type="ODDS"` + `venue="ODDS_API"`, check whether the corresponding GCS object at the expected
      path actually exists (`gcs_describe_object` via UTL, never raw gsutil). Do NOT wait for the VM to fully finish if
      it would take unreasonably long — re-check its status; a "not currently running" state (completed OR cleanly
      stopped) is sufficient to proceed, a live-writing state is not. Split the population into: (a) phantom rows
      (manifest entry, no real GCS object) — resolvable via Phase 2; (b) real rows (manifest entry backed by a real
      object) — needs Phase 3. Done-when: exact counts for (a) and (b), written into this plan's Progress Log, with the
      probe script's location cited (follow the shared task-id-keyed checkpoint convention in `task_template.md` §3
      finding X if the probe takes long enough to need resuming).

## Phase 2 — close the phantom subset (manifest-only, no GCS mutation)

- [ ] [SCRIPT] P1. For the phantom subset sized in Phase 1: purge/reclassify the manifest rows only, mirroring
      `purge_footystats_odds_uppercase_phantom_2026_08_14.py`'s pattern exactly (same CAS-based manifest write approach
      used elsewhere this session for the FIXTURES_OUTCOMES backlog close). This is a manifest-content change, not a GCS
      object delete — no `[OPERATOR]` tag needed (read-only-derived, reversibility-qualified per finding T/U in
      `task_template.md`: the source manifest rows are quarantined/backed up before rewrite, same pattern as the
      FIXTURES_OUTCOMES backlog script from 2026-08-14). Done-when: a fresh `read_manifest_index` pull shows zero
      remaining phantom-uppercase-ODDS rows for the checked population, and the row count drop matches Phase 1's
      measured phantom count exactly.

## Phase 3 — migrate the real subset (GCS mutation — [OPERATOR] gated)

- [ ] [OPERATOR] P1. For the real subset sized in Phase 1 (if non-zero): execute a copy→content-verify→CAS-manifest-swap
      migration from the uppercase `ODDS` path/value to lowercase `odds`, following
      `restamp_sports_trades_to_odds_2026_08_12.py` (physical copy) + `manifest_swap_trades_to_odds_2026_08_12.py` (CAS
      manifest swap) as the cleanest recent reusable pattern for this exact class of migration — do NOT reuse the K1/K2
      scripts directly without re-verifying their direction logic first, given that migration's own documented reversal.
      **[OPERATOR] tag justification**: this is genuinely the class of migration finding T/U reserves for operator
      gating — a real, hard-to-reverse GCS object rename with a documented history of direction-confusion in this exact
      codebase, not a reflexive caution on scale alone. Before running: (1) re-confirm `mtds-backfill-odds-1` (or its
      successor) is not actively writing to the same path prefix, (2) re-confirm the copy direction is
      uppercase→lowercase by reading this plan's own Phase 1 findings, not from memory, (3) dry-run against a `-test-`
      bucket first, (4) run the real migration only after the dry-run's row-for-row content-hash verification passes.
      Done-when: zero remaining uppercase-ODDS objects for the migrated population, a fresh manifest read shows only
      lowercase-odds rows for this venue, and no other consumer (features/strategy/execution) shows a gap or
      double-count across the migration window (spot-check via the case-fold stopgap from Phase 0 still being live
      during the cutover).

## Phase 4 — cleanup

- [ ] [SCRIPT] P2. Once Phase 3 is fully done and verified stable for at least one full day (no regression, no
      case-fold-stopgap consumer actually firing on a mixed-case row anymore): the Phase 0 case-fold stopgap can be
      removed as dead code, OR left in place permanently as defensive normalization — operator's call at that point, not
      pre-decided here. Note the decision + reasoning in this plan's Progress Log when made.
- [ ] [DOC] P2. Update `sports_honest_coverage_gap_closure_2026_08_14.md`'s odds_api section to reference this plan's
      outcome once Phase 3 (or Phase 2, if Phase 1 found zero real rows) completes. Archive this plan per the standard
      6-step ritual once every phase above is done or explicitly cancelled.

## Progress Log

- **2026-08-15 (interactive session)**: Plan created per operator decision to standardize odds_api's data_type casing to
  lowercase "odds" everywhere, following a read-only scoping pass that found this is a real GCS-path migration (not a
  metadata edit) in a class with a documented prior incident (K1/K2 revert). Phased to de-risk: safe code fix first
  (Phase 0), live-check before assuming real migration scope (Phase 1), phantom subset closed cheaply (Phase 2), real
  subset migrated only under explicit operator gate (Phase 3). Explicitly sequenced after `mtds-backfill-odds-1`'s
  current run to avoid colliding with live writes to the same manifest surface.
