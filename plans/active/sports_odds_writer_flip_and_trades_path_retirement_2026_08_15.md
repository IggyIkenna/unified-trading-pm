---
doc_type: plan
title: "Flip the sports odds_api writer off data_type=trades onto odds + retire the orphaned old-path GCS objects"
summary: >-
  Odds-api bookmaker quotes are market data (a per-bookmaker odds snapshot, no volume) -- not a TRADE (an actual fill on
  our own book or a market fill with volume+price). The 2026-08-12/13 P2 migration already bulk-relabeled 382K
  historical GCS objects + manifest rows from data_type=trades to odds, but never flipped the live/batch WRITER
  (venue_fetch.py::_build_sports_shard_path() still hardcodes data_type=trades today), so trades rows keep
  re-accumulating on every write. This plan flips the writer, registers the missing SOURCE_PRIORITY entry so the live
  shard can launch under data_type=odds without crashing, sweeps the remaining real consumers, and -- only once the
  writer is confirmed stable -- physically deletes the now-orphaned old-path data_type=trades GCS objects (operator
  ruling 2026-08-15: do the deletion properly, not deferred).
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, instruments-service, deployment-service, deployment-api]
scope: [engineer, admin]
tags: [sports, data-correctness, migration, odds-api, taxonomy, gcs-delete]
related:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/sports_taxonomy_p3_consumers_2026_08_08.md,
    /plans/active/sports_odds_api_data_type_casing_standardization_2026_08_15.md,
    /plans/active/issues/sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md,
    /plans/active/mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14.md,
    /codex/02-data/sports-data-types-catalog.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
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
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py,
    market-tick-data-service/market_tick_data_service/engine/sports_catalog_reader.py,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_sports_manifest_v9.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/sentinels.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_source_priority_data.py,
    unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    market-tick-data-service/scripts/sports/restamp_sports_trades_to_odds_2026_08_12.py,
    market-tick-data-service/scripts/sports/manifest_swap_trades_to_odds_2026_08_12.py,
    market-tick-data-service/scripts/sports/census_sports_trades_to_odds_scope_2026_08_12.py,
  ]
---

# Flip the sports odds_api writer off `data_type=trades` onto `odds`

> **Track**: LOCAL / human plan (`assigned_vm: NA`) -- operator decision 2026-08-15.

## Why this exists (read before touching anything)

Operator ruling (2026-08-15): odds-api bookmaker data is **market data** -- a per-bookmaker odds snapshot, no volume --
fundamentally distinct from a **trade** (an actual fill on our own book, or a market fill, carrying volume+price like
any other fill). Calling this shape `trades` was conceptually wrong from the start, not just a naming inconsistency. The
canonical `data_type` is lowercase `odds` (NOT uppercase `ODDS` -- that key is already reserved by footystats' unrelated
pre-match snapshot reference data in `SOURCE_PRIORITY[("sports","ODDS")]`, restored 2026-07-15 after a prior split-brain
incident; colliding with it is exactly what crashed `live_pipeline_mode_for_venue` when this session tried
`--shard-spec sports:ODDS_API:ODDS` earlier today).

**This is a completion, not a fresh migration.** `sports_taxonomy_p2_migration_2026_08_08.md` already ran the bulk
historical relabel on 2026-08-12/13 (VM `canonical-migration-sports-trades-to-odds-20260812-223215`, exit 0): 382,137
GCS objects physically rewritten (content, not just a path copy) from `data_type=trades` to `odds`, plus 396,115 +
232,098 manifest rows relabeled across both surfaces. UAC's `league_data.py` already carries the exact semantic contract
this plan enacts (`SPORTS_ODDS_DATA_TYPE_CANONICAL_FORM = {"trades": "odds", "ODDS": "odds", "odds": "odds"}`,
`canonical_sports_odds_data_type()`) -- built under P1 (2026-08-08), documented as "deliberately NOT wired into any
writer/reader this phase." **What was never done**: the writer itself (`venue_fetch.py::_build_sports_shard_path()`)
still hardcodes `data_type=trades` in the literal GCS path today, so every row written since the P2 relabel -- and every
row the live VM writes right now -- re-accumulates under the old label. The P2 plan's own manifest_swap script docstring
calls this out as a known, accepted "phased-state caveat"; this plan is that deferred phase.

**Correction to earlier framing in this session**: I told the operator the `"data_type": "ODDS"` field in
`odds_api_adapter.py:759` was "vestigial, never reaches the path" -- true for the raw tick GCS **path** (confirmed:
`_build_sports_shard_path()` ignores it and hardcodes the literal), but **not** true in general -- that same field does
feed a _different_ surface, the manifest capture-record's own `data_type` stamp (~17K rows carry it verbatim). That
casing mismatch (`ODDS` vs the taxonomy's lowercase `odds`) is real, separately-scoped work, tracked in the sibling plan
below. Two different write surfaces, two different open gaps; this plan owns exactly one of them.

**Explicit non-overlap with `sports_odds_api_data_type_casing_standardization_2026_08_15.md`** (parallel, do not merge):
that plan fixes `odds_api_adapter.py`'s row-dict `"data_type": "ODDS"` field (uppercase -> lowercase) which feeds the
**manifest capture-record** surface, plus migrates ~17K existing rows on that surface. This plan fixes
`venue_fetch.py`'s hardcoded literal (`trades` -> `odds`) which owns the **raw tick GCS path** surface, plus retires the
far larger (382K+, still-growing) trades-labeled population on that surface. Both converge on the same final string,
`odds`, from different surfaces -- **do not touch `odds_api_adapter.py`'s row-dict field in this plan**, that edit
belongs exclusively to the sibling plan. The live-VM collision that sibling plan flagged (`mtds-backfill-odds-1`) has
since cleared -- confirmed terminated (`gcloud compute instances describe` returns NOT_FOUND as of 2026-08-15) -- so its
Phase 1 is unblocked too; sequencing between the two plans is now a scheduling convenience, not a hard dependency.

**Also explicit non-duplication**: `sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md` (open issue, P2)
already owns the IS-bucket cross-bucket mirror census/relabel (43,726 `trades` / 32 `TRADES` rows on the
`instruments-store-sports-prd` surface). Referenced below, not repeated. `sports_taxonomy_p2_migration_2026_08_08.md`
still has its own dangling Verification section (four-surface reconciliation, accepted-exception shrinkage,
honest-coverage re-run) -- that plan's own todos, not duplicated here; this plan's Phase 2 explicitly gates on them
completing rather than re-doing them. `sports_taxonomy_p3_consumers_2026_08_08.md` (panel/ML/arb/catalogue/Betfair
consumer wiring) has no overlap with the writer flip -- confirmed via full read, it never touches
`_build_sports_shard_path()`.

## Phase 0 -- code fix (no data touched)

- [ ] [SCRIPT] P1. Register `SOURCE_PRIORITY[("sports", "odds")] = ["odds_api"]` in
      `unified_api_contracts/canonical/crosscutting/_source_priority_data.py` (lowercase key, placed near the existing
      `("sports","ODDS")` entry with a comment cross-referencing this plan so the two are never confused again).
      `get_primary_source`/`has_source_priority` do exact-case dict lookups (confirmed by reading
      `_source_priority_core.py`) so this is additive and cannot collide with the reserved uppercase key. DoD: a unit
      test in `unified-api-contracts/tests/unit/test_source_priority.py` asserts
      `get_primary_source("sports", "odds") == "odds_api"` and that `("sports","ODDS")` is unchanged.
- [ ] [SCRIPT] P1. Flip both hardcoded `instrument_type=odds/data_type=trades/` literals in
      `venue_fetch.py::_build_sports_shard_path()` to `instrument_type=odds/data_type=odds/`. Update the function's
      docstring and any nearby comment referencing "trades" as the shard shape. DoD: `test_venue_fetch*` (whichever test
      module exercises this function -- confirm current name, don't assume) asserts the new path shape; no test still
      asserts the old `data_type=trades` shape for this function specifically (cefi/tradfi/prediction `trades` tests are
      unrelated and MUST NOT change).
- [ ] [SCRIPT] P1. Sweep the real sports-specific consumers of the old literal (per the 2026-08-12 consumer inventory +
      this session's own re-check) and update each to read/write/compare against `odds` instead of `trades`:
      `sports_catalog_reader.py:133` (literal reader query), `rebuild_sports_manifest_v9.py::_source_from_row()`,
      `sentinels.py::_resolve_pipeline_mode_for_sentinel`, `canonical_writer_stamping.py:82,101`,
      `canonical_writer_shaping.py:214,248,787`, `dependency_checker.py:910`, deployment-api's
      `mtds.py:258-259,312,347` + `_schema.py:108`. Confirm MDPS's `bucket_assignment_adapter.py:705` (dual-accepts
      `trades`/`ODDS`/`TRADES` today) already accepts lowercase `odds` too, or extend it -- state which. DoD: each site
      cited with its new behavior; a grep for the old literal in sports-scoped (not cefi/tradfi/prediction) code returns
      zero live (non-historical-migration-script, non-test-fixture) hits.
- [ ] [SCRIPT] P1. Decide UAC's existing `SPORTS_ODDS_DATA_TYPE_CANONICAL_FORM`/`canonical_sports_odds_data_type()` stub
      (`league_data.py`, built under P1, documented as deliberately unwired): wire it into the write path this plan is
      fixing (so future renames route through one helper instead of scattered literals), or confirm this plan's direct
      literal fixes supersede the need for it and mark the stub for removal -- state which and why. DoD: the decision is
      recorded in this plan's Progress Log, not left implicit.

## Phase 1 -- redeploy + verify (no regression)

- [ ] [OPERATOR] P1. Once Phase 0 ships (QG green, quickmerge landed, tarball rebuilt): redeploy the live shard under
      `--shard-spec sports:ODDS_API:odds` (delete-then-relaunch, same pattern as this session's venue-per-bookmaker fix
      deploy) and verify `live_pipeline_mode_for_venue` resolves cleanly (no `ValueError`) and captured rows land under
      `pipeline_mode=live_odds_api`, `data_type=odds`, real bookmaker `venue` values. `[OPERATOR]` because it's a
      live-VM launch/delete per the vm-launcher-runbook gate -- in practice the same operator-directed pattern already
      used earlier this session.
- [ ] [DATA] P1. Verify no downstream regression for at least one full boundary cycle post-flip: MDPS's bucket
      assignment still finds the shard (it already dual-accepts the old+new tokens per Phase 0's finding), features
      pipeline reads continue, and the live-capture staleness monitor (`DP-LIVE-004`) does not false-page on the
      cutover. DoD: cite the specific manifest/event evidence checked, not just "looks fine."

## Phase 2 -- close the dependent verification (reference, do not duplicate)

- [ ] [DATA] P2. `sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md`'s census already ran (slot-29, same
      day) and confirmed the IS-bucket mirror rows ARE fed by this same live writer (19,992 rows written in the last 7
      days as of that census) -- that issue's own `[OPERATOR]` VM-relabel todo is pre-drafted
      (`instruments-service/scripts/restamp_sports_is_bucket_trades_mirror_to_odds_2026_08_15.py`, locally validated,
      not yet run against prod) and explicitly notes it may need a re-run once this plan's Phase 0 lands. Once Phase 0
      ships: confirm with that issue's owner whether to execute its drafted relabel now or wait for this plan's flip to
      stop new `trades` rows first (running it before the flip means re-running it after); update that issue doc, do not
      re-derive its census here.
- [ ] [DATA] P2. Once this plan's Phase 0/1 land, `sports_taxonomy_p2_migration_2026_08_08.md`'s own dangling
      Verification section (four-surface reconciliation, accepted-exception shrinkage, honest-coverage re-run) can
      finally run against a writer that has stopped re-accumulating `trades` -- flag that plan's owner (or pick it up
      directly if unclaimed) rather than duplicating those todos here.

## Phase 3 -- retire the orphaned old-path objects ([OPERATOR]-gated GCS delete)

- [ ] [DATA] P2. Census every remaining `data_type=trades` GCS object in the sports raw-tick bucket as of Phase 1's
      completion, split into: (a) objects whose content was already copied to an `odds`-labeled twin by the 2026-08-12
      restamp (safe to delete -- a real, verified duplicate exists), vs (b) objects written between the 2026-08-12
      restamp and this plan's Phase 0 flip landing that were never relabeled (the re-accumulated ~362K-row population
      the P2 plan's own census found) -- these need restamping FIRST, not direct deletion.
- [ ] [SCRIPT] P2. Re-run `restamp_sports_trades_to_odds_2026_08_12.py` + `manifest_swap_trades_to_odds_2026_08_12.py`
      (or updated copies, if their `--days-out` window needs extending to cover the gap) against population (b) from the
      census above, so 100% of remaining `trades`-labeled content has a verified `odds`-labeled twin before any deletion
      proceeds.
- [ ] [OPERATOR] P2. Physically delete the orphaned `data_type=trades` GCS objects -- gated per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a, following the same reversibility-qualified
      copy-verified-then-delete-source pattern `restamp_sports_trades_inplay_to_odds_2026_08_13.py` already used
      successfully for the `trades_inplay` retirement (1,197 objects folded + sources deleted, VERIFY=0 remaining).
      Pre-conditions: Phase 0's writer flip has been stable and verified for at least the retention window the §3a
      protocol requires; the restamp-first pass above shows 0 unmigrated `trades` objects; a dry-run against a `-test-`
      bucket passes content-hash verification first. DoD: a fresh GCS walk of the sports raw bucket shows zero
      `data_type=trades` objects; both manifest surfaces (tick bucket + IS-bucket mirror, per Phase 2's finding) show
      zero `trades`/`TRADES` rows; `cefi`/`tradfi`/`prediction` `trades` populations are untouched (different, unrelated
      concept sharing the same literal token -- confirmed out of scope by the 2026-08-12 consumer inventory).
- [ ] [SCRIPT] P3. Once Phase 3's delete is verified complete and stable: retire the now-fully-consumed 2026-08-12/13
      one-off scripts (`census_sports_trades_to_odds_scope_2026_08_12.py`,
      `restamp_sports_trades_to_odds_2026_08_12.py`, `manifest_swap_trades_to_odds_2026_08_12.py`,
      `restamp_sports_trades_inplay_to_odds_2026_08_13.py`) and this plan's own scripts per the lifecycle-marker
      convention -- or leave as historical record if the operator prefers a paper trail; state the decision.

## Definition of done for the whole plan

The sports odds_api writer emits `data_type=odds` exclusively (live and batch); no code path -- other than the
lifecycle-marked historical migration scripts themselves -- reads or writes sports `data_type=trades`; zero
`data_type=trades` objects remain in the sports raw-tick GCS bucket; both manifest surfaces show zero `trades`/`TRADES`
rows; the sibling casing-standardization plan's manifest-capture-record surface and this plan's raw-path surface both
converge on the same lowercase `odds` string with no residual mismatch between them.

## Progress Log

- 2026-08-15: Plan created per operator ruling (odds-api data is market-data odds, not a trade) and explicit instruction
  to complete the deletion properly rather than defer it. Investigation (via sub-agent + direct reads) found the bulk
  historical relabel already ran 2026-08-12/13 under `sports_taxonomy_p2_migration_2026_08_08.md` -- this plan is the
  deferred writer-flip + deletion phase that migration's own docstring flagged as a known gap, not a duplicate effort.
  Confirmed no conflict with the parallel `sports_odds_api_data_type_casing_standardization_2026_08_15.md` (different
  write surface, same convergent target) or the open IS-mirror issue (referenced, not duplicated). Confirmed the
  `mtds-backfill-odds-1` VM the casing plan flagged as a collision risk has since terminated.
- 2026-08-15 (execution): Phase 0 todos 1-4 code-complete across `unified-api-contracts`, `market-tick-data-service`,
  `deployment-api` (all pulled ff-clean first). Todo 1: registered `SOURCE_PRIORITY[("sports","odds")]=["odds_api"]` +
  matching `AVAILABILITY_AT_SEMANTICS` entry (a whole-suite QG run surfaced that the two registries must stay symmetric
  -- `era_b_legacy_purge.py`'s purge-safety guard checks it -- fixed, verified via direct import check). Todo 2/3:
  flipped `venue_fetch.py::_build_sports_shard_path` + its `shard_counts` key, `manifest_finalize.py`'s sports
  discriminator, 6 sites in `sentinels.py`, `sports_catalog_reader.py`,
  `rebuild_sports_manifest_v9.py::_source_from_row` (kept `"trades"` alongside new `"odds"` -- historical rows), and --
  found via direct read, not in the original file list -- the LIVE writer's own hardcoded leaf in
  `live/_sports_tick_path.py::sports_live_tick_blob_path` (would have broken live/batch shape parity at Phase 1 deploy
  if missed). deployment-api's `mtds.py`/`_schema.py` flipped. MDPS (`market-data-processing-service`) consumers
  CONFIRMED already dual-accept `"odds"`, zero changes needed there. All touched test fixtures updated in the same pass.
  Todo 4: kept `SPORTS_ODDS_DATA_TYPE_CANONICAL_FORM` stub as-is, NOT wired into the write path -- the direct literal
  fixes above are simpler and already meet the DoD; the helper stays useful for future readers normalizing
  mixed-vocabulary historical data. **Shipping blocked by shared-slot contention, not code correctness**: this machine
  hit load avg 88+ / 15+ concurrent `quality-gates.sh` processes (consistent with the SessionStart collision warning --
  4 other live sessions in this same slot). First UAC `quickmerge.sh` attempt queued 3320s on the QG-governor token then
  failed re-gate on an UNRELATED SIM300 lint violation in another live session's untracked WIP
  (`tests/internal/unit/test_flatten_readiness.py` + siblings, a risk/flatten feature, zero overlap with this plan) --
  left untouched (not owned) and a retry was launched rather than editing/inheriting their in-flight work. This same
  edit was ALSO lost once mid-session (file reverted to its pre-edit committed state with a clean `git status` despite
  an unstaged edit having been made) -- likely another session's concurrent git operation on this shared PM checkout;
  committing this entry immediately via `safe-doc-push.sh` rather than leaving it staged uncommitted, per the measured
  "Write+git add in ONE step" loss pattern in `/codex/05-infrastructure/per-tab-worktrees.md`. Repo@sha ship evidence +
  Phase 0 checkbox flips land in the next entry once each repo's quickmerge actually lands (not yet true as of this
  entry).
