---
doc_type: issue
title: "Solana perp DEX cull — DRIFT + PACIFICA data/state purge (operator kill ruling 2026-07-16)"
summary: >
  Operator ruling 2026-07-16 (verbatim): "kill drift entirely... kill all other solana perp dex's. uac, code, adaptors,
  manifest, gcs, everything. no instruments no mvp nothing." Jupiter is the only Solana perp kept (not currently
  integrated — verified zero captured rows anywhere). MANGO/ZETA/FLASH were already purged 2026-07-15 (spot-confirmed
  still zero here, not redone). This doc covers the DATA/STATE half of the kill (GCS objects + availability manifests +
  instrument catalogues, both DEFI and — a live finding this task surfaced — CEFI asset groups, since a mislabeled VM
  was writing PACIFICA-SOLANA into the CEFI buckets too) via
  market-tick-data-service/market_tick_data_service/scripts/purge_drift_pacifica_solana_perp_2026_07_16.py. A sibling
  task owns repo CODE/registry/codex (UAC venue registries, MTDS adapter deletion). DATA/STATE half DONE
  2026-07-16T13:01Z (all 4 surfaces x 2 asset groups verified zero, both consolidator crons resumed with confirmed green
  cycles); one CODE-track handoff todo remains (launcher_registry.py self-heal disable).
status: open
nature: record
asset_group: [defi, cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    defi,
    cefi,
    drift,
    pacifica,
    solana,
    perp-dex,
    kill-switch,
    manifest,
    catalogue,
    gcs,
    data-correctness,
    operator-ruling,
  ]
related:
  [
    plans/active/issues/drift_helius_perp_funding_shards_are_zero_valued_signature_noise_2026_07_16.md,
    plans/active/issues/drift_helius_path_obsolete_2026_07_15.md,
    plans/archive/solana_perp_dex_adapters_2026_05_13.md,
  ]
created: 2026-07-16
parent_epic: defi_master
priority: P0
resolved_by:
locked_by:
source: [operator-ruling, solana_perp_dex_cull_drift_pacifica_2026_07_16]
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-18T10:07Z
---

# Solana perp DEX cull — DRIFT + PACIFICA data/state purge (2026-07-16)

## Ruling (operator, verbatim, 2026-07-16, `/autonomous`)

> "kill drift entirely... kill all other solana perp dex's. uac, code, adaptors, manifest, gcs, everything. no
> instruments no mvp nothing." Jupiter is the only Solana perp kept (not currently integrated).

**Kill-set venues**: DRIFT, PACIFICA (bare, manifest-column grain) / DRIFT-SOLANA, PACIFICA-SOLANA (catalogue +
raw-GCS-path + `instrument_id` grain — see the naming-gotcha section below). MANGO/ZETA/FLASH already purged 2026-07-15
— spot-confirmed still zero across every surface below, not redone. **JUPITER is explicitly kept** — verified: it exists
only as a generic-protocol catalogue placeholder (30,382 manifest rows, 100% `empty_confirmed`, including 1,381
`perp_funding` placeholder cells) with **zero captured rows anywhere** — "not currently integrated" is accurate, not
aspirational.

## Task split

This is the **DATA/STATE half**: GCS objects, availability manifests, instrument catalogues. A sibling task owns **repo
CODE/registry/codex** (UAC venue registries `defi_venues.py` / `venue_adapter_keys.py` / `venue_constants.py` /
`venue_launch_dates.py` / `venue_mapping.py` / `_defi_chain_data.py`, MTDS adapter code `drift_v2_historical_handler.py`
/ `drift_v2_onchain_decoder.py`, external mock dirs `unified_api_contracts/external/{drift,pacifica}/` — confirmed via
live `git status` at task start, all dirty/uncommitted, sibling actively mid-edit throughout this session). No repo
source file was touched by this task.

**strategy-service (10th repo, added 2026-07-16 late in the day — caught by a fleet-wide closing grep after the other 9
repos shipped)**: this is the one place the cull changes **STRATEGY BEHAVIOUR**, not just dead code/data. See §
"strategy-service — live strategy behaviour change" below.

## strategy-service — live strategy behaviour change (2026-07-16)

Unlike the other 9 repos, strategy-service's DRIFT/PACIFICA-SOLANA references were **live code paths actively used by
the `CARRY_STAKED_BASIS` / `CARRY_BASIS_PERP` / `CARRY_STAKED_BASIS_DATED` archetype engines** — removing the venue
changes what these strategies can actually do, not just what they're allowed to reference.

**What changed (venue-set before/after)**:

| Constant / table                                                                         | Before                                                  | After                                                                                                                                                        |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `catalog_staked_basis.py::_STAKED_BASIS_SOL_PERP_VENUES`                                 | `("HYPERLIQUID", "DRIFT")`                              | `("HYPERLIQUID",)`                                                                                                                                           |
| `catalog_staked_basis.py::_VENUE_ALIAS_TO_CANONICAL`                                     | `{"GMX": (...), "DRIFT": ("DRIFT-SOLANA",)}`            | `{"GMX": (...)}`                                                                                                                                             |
| `catalog_staked_basis.py::_DERIVATIVE_TICKER_EMBEDS_FUNDING`                             | `{HYPERLIQUID, ASTER, PACIFICA-SOLANA, LIGHTER-ZKSYNC}` | `{HYPERLIQUID, ASTER, LIGHTER-ZKSYNC}`                                                                                                                       |
| `build_carry_staked_basis()` SOL-side slots (jito-drift, marinade-drift × 4 spot venues) | 8 slots                                                 | **0 slots** (no live venue accepts JitoSOL/mSOL as LST_AS_MARGIN collateral)                                                                                 |
| `build_carry_staked_basis()` total catalog slots                                         | 14                                                      | **6** (ETH-side only: DERIBIT/stETH + BYBIT/stETH × 3 spot venues)                                                                                           |
| `build_carry_staked_basis_dated()` — hardcoded `jito-drift-sol-q1` slot                  | present (ungated, unconditional)                        | **removed outright** (no fallback venue for Solana dated futures)                                                                                            |
| `archetype_slots_defi.py::SOL_BASIS` (CARRY_BASIS_PERP)                                  | `perp_venue: drift`                                     | `perp_venue: hyperliquid` — **fully functional**, no LST-margin requirement                                                                                  |
| `archetype_slots_defi.py::SOL_STAKED_BASIS` (CARRY_STAKED_BASIS)                         | `perp_venue: drift` (LST_AS_MARGIN, f=1.0)              | `perp_venue: hyperliquid` — engine's `USDC_MARGIN_BUFFERED` fallback fires (f=0.8 default, less capital-efficient but genuinely functional, NOT a dead slot) |
| `paper_run_handler.py::PAPER_RUN_SPEC_INDICES`                                           | `(0, 6)` — spec[6] was the SOL/DRIFT slot               | `(0, 5)` — both ETH-side now (index 6 would have raised `ValueError: out of range`)                                                                          |

**Proof of no silent empty-universe / no-hedge degrade**: verified directly (not assumed) that (a) `HYPERLIQUID` does
NOT accept JitoSOL/mSOL as collateral (`accepted_perp_collateral("HYPERLIQUID") == ["USDC"]`), so simply keeping
HYPERLIQUID in the SOL perp-venue tuple does NOT restore SOL-side catalog slots — this is documented honestly in the
`build_carry_staked_basis()` / `_resolve_start_token()` docstrings rather than left as a silent zero; (b) the ETH side
of `CARRY_STAKED_BASIS` remains fully live (6 slots, DERIBIT + BYBIT), proving the archetype degrades a leg (loses SOL),
not the whole archetype, per the operator's framing; (c) for the single-slot `archetype_slots_defi.py` table (a
DIFFERENT, non-matrix-gated construction path from the auto-generated catalog), `SOL_STAKED_BASIS` migrated to
HYPERLIQUID DOES produce a genuinely functional slot because `staked_basis.py::_derive_structure()` has a newer
`USDC_MARGIN_BUFFERED` fallback (added 2026-06-17, independent of this cull) that the auto-generated catalog's
`_resolve_start_token()` does not implement — confirmed live via
`_derive_structure(_BasisConfig("marinade","SOL","mSOL","hyperliquid","SOL-PERP","jupiter","USDC"), Decimal("0.20"))` →
`_DerivedStructure(structure='USDC_MARGIN_BUFFERED', perp_margin_token='USDC', ...)`, not `None`.

**Pre-existing catalog/engine gap surfaced (not fixed, flagged for follow-up)**: `catalog_staked_basis.py`'s
`_resolve_start_token()` (used by the auto-generated `build_carry_staked_basis()`) only implements the LST_AS_MARGIN
eligibility check — it does NOT implement the engine's newer `USDC_MARGIN_BUFFERED` fallback. This means the
auto-generated catalog under-emits relative to what the engine can actually run (the single hardcoded `SOL_STAKED_BASIS`
slot works via the fallback; the auto-generated catalog's SOL bundle does not, because it never reaches the fallback
check). This mismatch predates this task (the fallback was added 2026-06-17, the catalog gate was never updated to
match) — this cull just made it visible by removing the one SOL venue that happened to satisfy the STRICTER gate. Not
fixed here (real scope creep beyond "kill the venue"); worth a follow-up plan if the operator wants the ~8
auto-generated SOL-side USDC_MARGIN_BUFFERED slots restored.

**Tests**: 84 RED tests found on task start (`test_target_universe.py` + 83 more across ~26 files — far more than the 1
initially flagged; a fleet-wide sweep of the whole repo, not just the named files, was required), plus 2 more
(`test_paper_universe.py`) and 1 more (`test_archetype_slot_resolver.py`'s HYPERLIQUID re-point) surfaced only by a full
`tests/` sweep after the scoped sweep looked clean. All fixed to match the new reality — no test deleted to force a
pass; every removed test case (pure DRIFT-behaviour duplicates with a still-live equivalent, e.g.
`TestLstAsMarginUnchanged::test_drift_*` in `test_carry_staked_basis_usdc_margin_buffered.py` duplicating
`test_bybit_emits_lst_as_margin_full_size`) carries an explanatory comment. Full `strategy-service` suite green
post-fix: **5056 passed, 354 skipped, 0 failed** (`pytest tests/`). One unrelated pre-existing failure
(`test_carry_recursive_staked_emits_atomic_on_chain_loop`, `BucketNamingError: GCP_PROJECT_ID not set`) reproduces
identically on a clean pre-task HEAD when run in file-isolation — an environment/fixture-ordering artifact of a
DIFFERENT engine (`CarryRecursiveStakedEngine`, no DRIFT reference), not touched by this task, and it passes as part of
the full suite.

**Vacuous-test trap caught by coordinator review (real correctness bug, not just a rename)**: the first-pass
substitution in `test_carry_staked_basis_audit03.py` left the shared `_jito_drift_params()` fixture defaulting to
`perp_venue="DRIFT"` for the F-09 stake_fraction-rejection tests
(`test_stake_fraction_half_rejected`/`_zero_rejected`/`_above_one_rejected`). Since DRIFT is now fully absent from UAC
(`accepted_perp_collateral("DRIFT") == []`), `_derive_structure` resolves every DRIFT-based config to INELIGIBLE
(`None`) — so these 3 tests were passing because the VENUE was rejected before `_resolve_setup` ever reached the
stake_fraction check, not because the stake_fraction rule fired. **The F-09 stake_fraction enforcement rule was
effectively untested** despite green CI. A 4th instance of the identical bug pattern was found independently
(`TestF10FeesTermInNetCarry::test_high_fees_block_entry` — `_preflight` calls `_resolve_setup` first and returns `None`
immediately on venue ineligibility, before net_carry is ever computed, so this test was also vacuously "passing" for the
wrong reason). Per the coordinator's explicit guidance: **re-pointed rather than deleted** — verified live that
LST_AS_MARGIN is genuinely still reachable (BYBIT accepts `stETH`/`wstETH`, OKX accepts `wstETH`, both confirmed via
`accepted_perp_collateral()`), so the shared fixture (renamed `_bybit_lido_params`) now defaults to LIDO/stETH/ETH/BYBIT
— a real LST-margined venue — restoring genuine F-09/F-10 enforcement coverage. The one caller that specifically needs
Solana-chain-gate semantics (`test_jito_solana_chain_allowed`, chain gate is independent of perp-venue collateral
eligibility and `_derive_structure` is mocked there) explicitly overrides back to
`staking_protocol=JITO, native_asset=SOL, lst_asset=JitoSOL` to preserve its Solana-specific test intent. Verified
directly (not just green-trusted): `_derive_structure(BYBIT config) → LST_AS_MARGIN` (non-None, haircut 0.10) vs
`_derive_structure(DRIFT config) → None` — confirming the fixed tests now genuinely reach and exercise the rule under
test.

**Codex updated**: `/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md` (SUPERSEDED banner + stale
venue_universe/matrix references), `carry-staked-basis-dated.md` (SUPERSEDED banner, dated slot removed),
`../families/carry-and-yield.md` (active slot_labels list), `../category-instrument-coverage.md` (Solana coverage rows
marked REMOVED). `mvp-universe-per-asset-group.md` had no DRIFT references (checked, clean).

**Considered and explicitly kept (not a miss)**:
`strategy_service/engine/strategies/v2/migration/legacy_strategy_mapping.yaml` still has `perp_venue: drift` rows under
`DEFI_SOL_BASIS_DRIFT_SCE_1H` / `DEFI_SOL_STAKED_BASIS_DRIFT_SCE_1H` — left AS-IS. This is a static historical audit
table mapping already-archived `_archived_pre_v2` legacy strategy modules to their v2 equivalents (not live code, not
runtime-validated against UAC — `test_legacy_mapping_yaml_loader.py` confirms the loader does zero venue-matrix
validation). Changing it would misrepresent the historical fact of what that legacy (dead) strategy actually ran on.
`strategy_service/scripts/phase_d_gate.py`'s "pre-Pacifica-launch" comment is similarly a historical explanatory note
(why `ARBITRAGE_PRICE_DISPERSION` may legitimately be data-sparse), not a functional PACIFICA reference — left as-is.

## Naming gotcha (measured live, not assumed — the reason a naive purge would silently miss rows)

The venue string is **not one literal** across surfaces or asset groups:

| surface                            | DRIFT literal | PACIFICA literal   |
| ---------------------------------- | ------------- | ------------------ |
| DEFI manifest `venue` column       | `DRIFT`       | `PACIFICA` (bare!) |
| DEFI catalogue `venue` column      | `DRIFT`       | `PACIFICA-SOLANA`  |
| DEFI raw GCS `venue=` path segment | `DRIFT`       | `PACIFICA-SOLANA`  |
| CEFI manifest `venue` column       | (none found)  | `PACIFICA-SOLANA`  |
| CEFI catalogue `venue` column      | (none found)  | `PACIFICA-SOLANA`  |
| CEFI raw GCS `venue=` path segment | (none found)  | `PACIFICA-SOLANA`  |

The `-SOLANA` suffix only appears inside `instrument_id` on the DEFI manifest side (e.g. `DRIFT-SOLANA:PERP:SOL-PERP`),
never in the `venue` column there. Using bare `PACIFICA` against the catalogue or any raw GCS path would have silently
purged **nothing** there (0 objects found, falsely read as verified-zero) — the purge script's constants are
deliberately different literals per surface, documented in its own module docstring.

**Bigger surprise: PACIFICA-SOLANA data also lives in the CEFI asset-group buckets, not only DEFI.** A live VM
(`cefi-pacifica-solana-2026-20260715-190049`) was running the generic `collect-onchain-perp-batch` /
`cefi-hl-aster-backfill` task with `VM_ASSET_GROUP=cefi` but `VM_VENUE=PACIFICA-SOLANA` — writing real captured rows
into `market-data-tick-cefi-prd-...` and `instruments-store-cefi-prd-...` under `pipeline_mode=batch_pacifica`. This was
NOT in the original task scope (which named only the DEFI buckets) — found via a bounded grep for
DRIFT/PACIFICA-venue-keyed stores per the "any other state" instruction, and folded in because "everything" is the
explicit ruling.

## *** SCOPE GUARD *** — verified, not assumed

DRIFT / JUP / PACIFICA are also token tickers trading on OTHER venues. Confirmed via a full distinct-venue read plus an
`instrument_id`-substring cross-check, on BOTH asset groups:

- **DEFI**: **7,430 manifest rows** carry `DRIFT`/`PACIFICA`/`JUP` inside `instrument_id` while `venue` is NOT
  DRIFT/PACIFICA — `EXTENDED-STARKNET:PERP:JUP-USD`, `LIGHTER-ZKSYNC:PERP:JUP`, `KAMINO-SOLANA:VAULT:JUP-BONK:...`, etc.
- **CEFI**: **33,263 manifest rows** carry the same substrings on non-kill-set venues — `BITGET-FUTURES` (4,788),
  `BINANCE-FUTURES` (4,283), `BYBIT` (3,847), `EXTENDED-STARKNET` (2,636), `ASTER` (2,491), `UPBIT` (2,390),
  `KRAKEN-FUTURES` (2,011), `OKX-SWAP` (1,770), `HYPERLIQUID` (1,641), `LIGHTER-ZKSYNC` (1,434), + more.

The purge scripts filter by the `venue` COLUMN (manifest/catalogue) or the `venue=` PATH SEGMENT (raw objects) only —
never by substring — so all 40,693 of these rows survive untouched by construction. Spot-verified post-purge on both
asset groups: none of these rows were touched (the post-purge row counts for every other venue are unchanged from their
pre-purge values — only the kill-set `venue` values' row counts moved).

## Live-writer discovery — the purge would have been whack-a-mole without this

Mid-purge, the DEFI raw-tick delete pass (23,723 objects deleted) failed its own post-delete re-list verification:
objects that had just been deleted **reappeared** on specific historical dates (`day=2025-09-22`, `2025-09-23`, ...).
Root cause: two LIVE VMs were actively re-writing kill-set data throughout the purge window —

- **`mtds-solana-drift-backfill`** (RUNNING since 2026-07-15T19:09:42Z) — the Velocity DRIFT backfill from
  `drift_helius_path_obsolete_2026_07_15.md`, still actively filling `2022-11-04`→`2026-07-16` at the time this task
  started.
- **`cefi-pacifica-solana-2026-20260715-190049`** (RUNNING since 2026-07-15T12:00:51Z) — the CEFI bucket writer
  described above.

Both were **stopped** (`gcloud compute instances stop`, a GCP admin op — not a repo edit) at `~2026-07-16T10:06Z`. Both
instances' own per-VM manifest shards (`_index/per_vm/mtds-solana-drift-backfill.parquet` — 2,292 rows, 100% DRIFT;
`_index/per_vm/cefi-pacifica-solana-2026-20260715-190049.parquet` — 2,780 rows, 100% PACIFICA-SOLANA) were **100%
kill-set** and were deleted outright — left in place, they would have been merged back into the consolidated index on
the next consolidator cycle, silently resurrecting the purge.

**Both VMs are registered in `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py`**
(`"mtds-solana-drift-backfill": "launch-mtds-solana-drift-backfill-vm.sh"`,
`"cefi-pacifica-": "launch-cefi-sharded-backfill.sh"`) — the self-heal watchdog WILL relaunch a stopped/stalled
registered VM. **This task did NOT flip either registry entry to `None`** (that file is squarely repo CODE, the
sibling's lane, and both files were untouched/clean at task start — editing them risked exactly the file-collision this
task's split was designed to avoid). **This is the explicit P0 handoff to the sibling/CODE track**, mirroring the
identical precedent already shipped for the Helius path (`deployment-service@46d6492`, `mtds-drift-sig-walker-` →
`None`): flip both `"mtds-solana-drift-backfill"` and `"cefi-pacifica-"` to `None` in `launcher_registry.py` (+ its
guard test `tests/unit/test_launcher_registry.py`) so the watchdog cannot undo this purge. Until that lands, **do not
restart either VM** — both are left `TERMINATED`/stopped, not deleted, so the sibling's CODE-track removal work can
still reference them if needed.

## Todos

- [x] [CODE] P0. Flip `"mtds-solana-drift-backfill"` and `"cefi-pacifica-"` to `None` in
      `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py` (+ guard test
      `tests/unit/test_launcher_registry.py`) so the self-heal watchdog cannot relaunch either VM this task stopped
      (both left `TERMINATED`, not deleted). Mirrors the identical precedent already shipped for the Helius path
      (`deployment-service@46d6492`, `mtds-drift-sig-walker-` → `None`). Repo: deployment-service. Sibling/CODE-track
      scope — DATA/STATE task (this one) deliberately did not touch this file. **CLOSED 2026-07-18, already satisfied —
      `deployment-service@9b13679`** (landed 2026-07-16T13:15:01Z, i.e. same-day, ahead of this handoff being picked
      up): rather than flipping the two entries to `None`, that commit **removed them outright** from BOTH
      `LAUNCHER_FOR_VM_PREFIX` (`launcher_registry.py`) and the parity-required `VM_PREFIX_TO_BUCKET`
      (`vm_prefix_registry.py`) — a stronger guarantee than the literal instruction: `resolve_launcher_for_vm()`'s
      no-match fail-safe path already returns `None` for any unregistered vm_name (`launcher_registry.py:328-331`), so
      full removal is behaviourally identical to an explicit `None` entry for self-heal purposes, PLUS it strips the VM
      class from deployment-target classification entirely (no `VM_PREFIX_TO_BUCKET` entry either) — closer to the
      operator's "no instruments no mvp nothing" framing than leaving a documented-but-dead `None` placeholder. Verified
      live (2026-07-18, this task): (1) neither `mtds-solana-drift-backfill` nor any `cefi-pacifica-solana-...` VM name
      prefix-matches ANY current key in `LAUNCHER_FOR_VM_PREFIX` (checked programmatically); (2) `vm_prefix_registry.py`
      carries no DRIFT/PACIFICA prefix entries either (only unrelated comment-string hits); (3) the guard test
      `tests/unit/test_launcher_registry.py`'s bidirectional parity checks ((a) every watchdog prefix has a registry
      entry, (c) no registry-only stale prefix) hold because both files were pruned symmetrically; (4) full
      `deployment-service` `quality-gates.sh --no-fix` run clean at current HEAD —
      **`0a811e82b6d01a6b6f20a60f8966f3b56e4c1b2a`** (2664 passed, 5 skipped, ALL QUALITY GATES PASSED, sentinel
      `.qg_last_passed_sha` matches HEAD exactly). No further code edit was needed or made.
- [ ] [DATA] P2. Once the sibling's UAC venue removal + instruments-service adapter removal are fully on `origin` (per
      the coordinator: IS landed `4d65d468`+`b37e9d82`, MTDS deletion still in flight), re-run
      `build_instrument_catalogue.py --asset-group defi` (and `cefi`, if it also derives from a venue-capability
      registry) as a confirmation pass — should be a no-op diff against this task's surgical row-delete purge if both
      sides agree. Not blocking (the row-delete already satisfies "no instruments" today). Repo: instruments-service.
      **Status checked 2026-07-18 (left open, not flipped — see note)**: the pre-conditions are now satisfied on
      `origin` — IS `4d65d468`+`b37e9d82` (2026-07-16) and, per this doc's own COMPLETION RECORD, MTDS
      `market-tick-data-service@2e674d1f` (also 2026-07-16, "55 files, −11,178 lines") — so the "MTDS deletion still in
      flight" caveat above is stale. Beyond that, `instruments-service@ee19f6f3` (2026-07-18, on `origin`,
      `git merge-base --is-ancestor` verified) went further than a one-off confirmation run: it hardens
      `scripts/build_instrument_catalogue.py` itself to structurally EXCLUDE `DRIFT`/`DRIFT-SOLANA`/`PACIFICA`/
      `PACIFICA-SOLANA` (+ MANGO/ZETA/FLASH families, both bare and `-SOLANA`-suffixed spellings) from ever re-minting a
      catalogue row on ANY future regen (`_REMOVED_VENUES` + `_is_removed_venue()`), proven by two new dedicated unit
      tests (`test_rollup_excludes_registry_removed_venues`,
      `test_rollup_is_removed_venue_matches_bare_and_suffixed_forms` in
      `tests/unit/scripts/test_build_instrument_catalogue.py`) — a durable code-level guarantee against the resurrection
      concern this todo was hedging against, stronger than a single manual confirmation pass. **What remains**: no
      evidence found of an actual `--apply` execution of `build_instrument_catalogue.py` against prod GCS
      (`gs://instruments-store-{defi,cefi}-prd-.../prod/catalog.parquet`) post-fix to produce a literal 0-diff
      confirmation artifact — that live-prod regen is instruments-service-repo scope and a prod mutation, both outside
      this closing task's bounds (`deployment-service`-only, no-prod-mutations). Left open as a low-priority,
      non-blocking instruments-service todo for whoever next touches that repo's catalogue pipeline.

## Per-surface counts + purge evidence

### 1. Instrument catalogue

**DEFI** (`gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet`): 10,387 → 10,303 rows. Matched:
`DRIFT`=80, `PACIFICA-SOLANA`=4 (84 total). Backup written `prod/catalog.20260716-100616.driftpacificacull.bak.parquet`
(matches the existing operational precedent already on disk for this bucket, e.g. `catalog.<ts>.venuefix.bak.parquet`).
Post-write verify: 10,303 rows, 0 residual. Query: `df['venue'].isin({'DRIFT','PACIFICA-SOLANA'})` against a full
`pd.read_parquet` (10,387 rows — trivially small, full read is safe). **DONE**, final dry-run re-check 13:00Z: 0
matched.

**CEFI** (`gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`): 424,633 → 424,623 rows.
Matched `PACIFICA-SOLANA`=10. Backup written `prod/catalog.20260716-124430.driftpacificacull.bak.parquet`. Applied
2026-07-16T12:44:31Z, post-write verify: 424,623 rows, 0 residual. **DONE**, final dry-run re-check 13:01Z: 0 matched.

**Catalogue-is-adapter-derived dependency**: `build_instrument_catalogue.py --asset-group defi` regenerates this file
from the UAC protocol/venue registries. This task did the **surgical row-delete now** (immediate purge, matches the
established direct-edit-with-backup pattern already used for prior one-off catalogue fixes) rather than waiting on the
sibling's registry removal + a regen — the row-delete is already sufficient for "no instruments" today. **Follow-up
recommended once the sibling's UAC venue removal + IS adapter removal are on `origin`**: re-run
`build_instrument_catalogue.py --asset-group defi` (and cefi, if it also derives from a venue-capability registry) as a
confirmation pass — should be a no-op diff against this purge if both sides agree.

### 2. Availability manifest

**DEFI** (`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, 28,743,670 rows
live at first measurement): matched `DRIFT`=424,450, `PACIFICA`=5,798 (430,248 total, 1.497% of the index). Breakdown:
DRIFT captured=1,395 (perp_funding=698, perp_trades=697, all `pipeline_mode=batch_onchain_rpc`), attempted_failed=29
(batch_onchain_rpc + batch_hyperliquid), rest empty_confirmed/expected_unattempted catalogue placeholders spanning
2018-01-01→2026-07-16. PACIFICA captured=117 (perp_funding only, `pipeline_mode=batch_hyperliquid`), rest
empty_confirmed/expected_unattempted. Snapshot written
`_index/snapshots/pre_drift_pacifica_solana_perp_purge_2026_07_16.parquet` before write. **Applied twice** — see the
"resurrection" finding below for why: first at 2026-07-16T10:06:12Z (28,743,670 → 28,313,422 rows, verified 0 residual
at the time), then **re-applied** at 2026-07-16T12:54:02Z (28,743,797 → 28,313,549 rows, verified 0 residual) after the
manifest was found to have been overwritten back to its pre-purge state by an out-of-band consolidator write. **Final
state confirmed clean** via a fresh dry-run at 13:00Z (28,313,549 rows, 0 matched) taken AFTER 3+ normal post-resume
consolidator cycles on both jobs — the resurrection has not recurred. Mechanism: row-group-streamed filter
(`pyarrow.parquet.ParquetFile.read_row_group` + incremental `ParquetWriter`) — a naive full-table `pd.read_parquet`
measured 10GB+ peak RSS and pushed this shared 15GB host into swap (confirmed via `free -h`: swap climbed to 9.7GB used
mid-read before the process was killed to protect the host); the streamed version peaked at 1.7GB.

**CEFI** (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, 11,161,090 rows
live at apply time — grew from the 12,014,169/16,932-matched figure measured ~2.5 hours earlier during the cross-repo
import blockage, because the CEFI cron had been silently un-paused in the interim — see Progress Log): matched
`PACIFICA-SOLANA`=16,952 (0 DRIFT rows found — DRIFT never wrote into CEFI). Breakdown: captured=664
(derivative_ticker≈663, trades=1, both `pipeline_mode=batch_pacifica`), rest empty_confirmed/expected_unattempted across
`batch_pacifica`

- `batch_tardis`. Captured dates ran 2026-01-26→2026-07-11 before the writer VM was stopped. Snapshot written
  `_index/snapshots/pre_drift_pacifica_solana_perp_purge_2026_07_16.parquet` (CEFI bucket). **Applied**
  2026-07-16T12:44:28Z: 11,161,090 → 11,144,138 rows, post-write verify 0 residual. **DONE**, final dry-run re-check
  13:01Z: 0 matched, stable across 3+ post-resume consolidator cycles.

### 3. Raw tick data

Bounded prefix scan (manifest-matched dates ∪ a 20-day recent-safety-net window, per venue root × known pipeline modes —
never a whole-corpus walk):

**DEFI**: found DRIFT≈23,187-23,197 objects (`pipeline_mode=batch_onchain_rpc`, ~23.2K;
`pipeline_mode=batch_hyperliquid`, 10 — the `drift_helius_*.parquet` zero-funding-noise shards named in
`drift_helius_perp_funding_shards_are_zero_valued_signature_noise_2026_07_16.md`, whose own separate purge todo this
supersedes per that doc's text), PACIFICA-SOLANA=370 (`pipeline_mode=batch_hyperliquid`). Zero objects found under bare
`venue=DRIFT-SOLANA` or bare `venue=PACIFICA`, and zero under `pipeline_mode=batch_solana_rpc` (the 2026-04+ on-chain
decoder path — consistent with that path's own documented finding of zero successful funding txs in the window it was
tested against). First apply pass (2026-07-16T10:06-10:08Z) deleted 23,723 objects but its own post-delete re-list
caught residual objects on `day=2025-09-22`/`2025-09-23` — root-caused to the live `mtds-solana-drift-backfill` VM (see
above). **Second pass** (after the VM was confirmed stopped) at 2026-07-16T12:46:31-12:47:44Z: found + deleted the
remaining 277 DRIFT stragglers, 0 PACIFICA-SOLANA (already fully clean from pass 1); POST-DELETE RE-LIST: **0 objects
remain**. Total DEFI raw objects deleted across both passes: 23,723 + 277 = **24,000**. **DONE**, final dry-run re-check
13:00-13:01Z (3,119 DRIFT dates × 18,714 prefixes, 948 PACIFICA dates × 5,688 prefixes): 0 found either venue.

**CEFI**: found + deleted **1,286** objects (`pipeline_mode=batch_pacifica`, `asset_group=cefi`,
`venue=PACIFICA-SOLANA`) at 2026-07-16T12:46:02-12:46:08Z. POST-DELETE RE-LIST: 0 objects remain. **DONE**, final
dry-run re-check 13:01Z: 0 found.

### 4. Per-VM manifest shards

**DEFI**: `_index/per_vm/mtds-solana-drift-backfill.parquet` — 2,292 rows, 100% DRIFT — **deleted** manually
~2026-07-16T10:10Z (verified gone via re-list; the script's own `--phase per-vm` dry-run at 12:45Z and again at 13:00Z
confirmed 0 fully-kill-set shards remain). All other DEFI per-VM shards checked clean (0 matched): `_legacy_seed`,
`defi-fwd-dex-pools-poll`, `defi-fwd-dex-swaps-poll`, `defi-fwd-oracle-prices-poll`, `mtds-dex-pools-backfill`,
`mtds-dex-swaps-backfill`, `mtds-eigenlayer-rewards-backfill`, `mtds-gas-fees-20260716-110018`, 5×`local-1-*`.

**CEFI**: `_index/per_vm/cefi-pacifica-solana-2026-20260715-190049.parquet` — 2,780 rows, 100% PACIFICA-SOLANA — found
at ~10:15Z; by the time the script's `--phase per-vm` ran (12:45Z, after the ~2.5h import-fix wait) the shard was
**already gone** — the CEFI consolidator (which ran continuously during the wait, see Progress Log) had already merged
it into the consolidated index and cleaned it up, which is why the manifest purge's matched-row count (16,952) already
fully accounts for it; no separate per-VM delete was needed. `_legacy_seed.parquet` (351,203 rows) checked clean (0
matched) both times.

### 5. Other state (features, BQ)

- `features-onchain-defi-central-element-323112` manifest: 13 rows total, 0 matched.
- BigQuery `central-element-323112`: no `market_data`/`market_data_candles_*`/`features` dataset contains a
  DRIFT/PACIFICA-named table (checked `bq ls` on each relevant dataset).
- `features-service/features_service/cefi/calculators/perp_funding_corpus.py` mentions PACIFICA in a docstring comment
  only (documents historical venue coverage, not a data store) — no action.
- AWS S3: this session's IAM role has no `s3:ListBucket`/`s3:ListAllMyBuckets` grant — could not verify an AWS mirror
  one way or the other. The operator ruling said "manifest, gcs" (not S3); treating AWS as out-of-scope for this pass,
  flagging for an operator/admin-session follow-up if an AWS mirror is later found to exist.

### 6. The DEFI manifest resurrection — a real race, root-caused

After the ~2.5h cross-repo import blockage (see Progress Log) cleared and the CEFI purge landed clean, a final
full-sweep dry-run unexpectedly showed the **DEFI manifest** matching 430,248 DRIFT

- PACIFICA rows again — i.e. **the first purge had been silently undone**. Root-caused via the blob's own GCS object
  metadata:

```
gcloud storage objects describe gs://market-data-tick-defi-prd-.../…/availability_index.parquet --format=json
  creation_time: 2026-07-16T10:23:05+0000
  custom_fields.consolidator_run_at: 2026-07-16T10:22:59.177383+00:00
```

The consolidator wrote this blob at **10:22:59Z** — 17 minutes after my purge landed (10:06:12Z) — even though
`gcloud run jobs executions list --job=...market-data-defi` showed **no execution at all** between 10:04:49Z and the
present (only the scheduled-cron-triggered runs show up there). Two independent pieces of corroborating evidence: (a)
the resurrected row count (430,248) and its DRIFT/PACIFICA breakdown matched the ORIGINAL pre-purge numbers EXACTLY, not
a partial re-merge; (b) by the time of the resurrection, both writer VMs were already stopped and their per-VM shards
already deleted/absorbed, so there was no legitimate NEW source data for a normal shard-merge to have produced this. The
most consistent explanation: an out-of-band consolidator execution (bypassing the scheduler entirely — possibly the
workspace's own liveness/self-heal automation reacting to the paused cron, per
`codex/05-infrastructure/ manifest-consolidator-ssot.md`'s "Confirm all crons enabled" invariant, which my pause
violated) began reading the pre-purge blob before my write landed, ran for an unusually long ~17 minutes, and then
overwrote my purge with its stale-input-based output. Separately, the **CEFI cron** was independently found flipped back
to `ENABLED` (from my earlier `PAUSED`) when checked ~2.5 hours later — the same self-heal class, confirmed via
`gcloud scheduler jobs describe` state.

**Remediation**: re-paused the DEFI cron confirmation, re-applied the DEFI manifest purge fresh (2026-07-16T12:54:02Z,
verified 0 residual — see §2 above), then resumed both crons and watched 3+ full post-resume cycles on each (12:54:42Z
onward) with a dry-run manifest check after each — **stayed clean throughout**, confirming this was a one-time race
during the paused window, not a recurring resurrection risk once the crons are running normally against already-clean
per-VM shards + raw objects.

**Lesson for any future pause-a-consolidator-cron operation on this system**: a `gcloud scheduler jobs pause` is not
sufficient on its own to guarantee no writes land during the pause window — this workspace has self-healing automation
that can both re-enable a paused cron and (apparently) force a write through an out-of-band path. The robust pattern is:
pause → do the write → **immediately, repeatedly re-verify the write held** (not just once) before considering the
surface safely purged, exactly as this task ultimately did.

### 7. Cron / consolidator handling — final state

- `uts-prod-manifest-consolidator-market-data-defi-cron`: paused 2026-07-16T10:05:01Z → (silently bypassed once, see §6)
  → re-confirmed/re-paused before the final re-apply → **resumed 2026-07-16T12:54:42Z**. Post-resume green-cycle proof:
  executions `...-mflnc` (started 12:55:03Z) and `...-qdv4x` (12:56:05Z→12:56:48Z,
  `succeededCount=1 failedCount=0 conditions[Completed]=True`) — manifest re-verified 0 DRIFT/PACIFICA rows immediately
  after (13:00Z). **Left ENABLED at session end.**
- `uts-prod-manifest-consolidator-market-data-cefi-cron`: paused 2026-07-16T10:16Z → found silently `ENABLED` again at
  ~12:42Z (self-heal, see §6) → re-paused 12:43:xxZ for the CEFI purge write → **resumed 2026-07-16T12:54:42Z**.
  Post-resume green-cycle proof: executions `...-8lbnr` (12:55:03Z→12:55:48Z) and `...-rrdjj` (12:56:07Z→12:56:48Z,
  `succeededCount=1 failedCount=0 conditions[Completed]=True`) — the object's own `update_time` advanced to 12:58:45Z (a
  genuine consolidator write cycle) and manifest re-verified 0 PACIFICA-SOLANA rows immediately after (13:01Z). **Left
  ENABLED at session end.**
- `uts-prod-manifest-consolidator-instruments-{defi,cefi}-cron` — NOT paused, never touched. These consolidate each
  bucket's OWN `_index/availability_index.parquet` (instrument-enumeration coverage tracking), a separate blob from
  `prod/catalog.parquet` (the reference-data catalogue this task edited) — no write-path overlap, confirmed by
  inspecting both blobs' distinct paths before deciding not to pause.
- Both writer VMs re-confirmed `TERMINATED` at session end (13:0xZ), no new instances spawned under either name/prefix.

## Scripts + evidence

- `market-tick-data-service/market_tick_data_service/scripts/purge_drift_pacifica_solana_perp_2026_07_16.py` —
  **`market-tick-data-service@788daa2e`** (pushed directly to `live-defi-rollout` per the dirty-deps git-commit flow —
  the repo tree had extensive concurrent sibling edits at push time; committed via the pathspec form
  `git commit -- <path>` so only this new file landed, ruff-clean, basedpyright warn-only per this repo's
  `scripts/`-tier convention — see the script's own docstring for the full mechanism writeup). Covers all 4 phases
  (`manifest`, `catalogue`, `per-vm`, `raw-tick`) × 2 asset groups (`defi`, `cefi`) via a per-asset-group
  `AssetGroupConfig`, dry-run by default, idempotent (`--apply` twice is safe — a 0-match re-run is treated as "already
  clean," not a scope-drift violation).
- Manifest snapshots: `_index/snapshots/pre_drift_pacifica_solana_perp_purge_2026_07_16.parquet` in BOTH
  `market-data-tick-defi-prd-...` and `market-data-tick-cefi-prd-...`.
- Catalogue backups: `instruments-store-defi-prd-.../prod/catalog.20260716-100616.driftpacificacull.bak.parquet`,
  `instruments-store-cefi-prd-.../prod/catalog.20260716-124430.driftpacificacull.bak.parquet`.
- This issue doc: `unified-trading-pm@<see git log>` (`docs(plans):` commit, rebase-autostash per the coordinator's
  instruction since PM is busy with concurrent sibling commits).

## COMPLETION RECORD — cull verified done (coordinator, 2026-07-16)

**Ruling executed in full**: DRIFT-SOLANA + PACIFICA-SOLANA (the only Solana perp DEXes; MANGO/ZETA/FLASH died earlier
the same day) removed from code, registries, schemas, manifests, catalogues, GCS, launchers, UI and docs. Jupiter left
as a clean slate (not integrated — deliberately NOT added).

**Shipped — 13 repos, 24 commits:**

| repo                      | shas                                                                                                                                                                                                                                                                                                                           |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| unified-api-contracts     | `7628dd30` (all registries) · `cb486e42` (orphaned Drift types) · `c5867215` (scenario_overlay schema) · `78334504` (_DEFI_PERP + chain map) · `b0ba2d6d` (TIF test) · `d996e4fe` (**architecture_v2**: 2nd collateral registry, leg specs+seeds, jurisdiction overlay, order semantics, venue tokens, simulation assumptions) |
| unified-trading-library   | `8f6b0a9f` (+follow-up: kill_switch/treasury/custody/withdrawal dead paths) · `69b12982` (venue fee schedule + defi venue list) · `81927d55` (availability stamping + ledger tests)                                                                                                                                            |
| market-tick-data-service  | `2e674d1f` (55 files, −11,178 lines) · `788daa2e` (purge script) · `5a163d02`/`56efdd7d` (pre-cull Kalshi fixes)                                                                                                                                                                                                               |
| instruments-service       | `4d65d468` · `b37e9d82`                                                                                                                                                                                                                                                                                                        |
| deployment-service        | `9b13679` (VM prefixes + launcher registry) · `194deeb` (shell launchers, 2 more py registries, dispatch branches)                                                                                                                                                                                                             |
| execution-service         | `e003cda4`                                                                                                                                                                                                                                                                                                                     |
| strategy-service          | `989557e4` (hedge venue set → `("HYPERLIQUID",)`, F-09 fixture re-point) · `a3883b73`                                                                                                                                                                                                                                          |
| e2e-testing               | `76a1071`                                                                                                                                                                                                                                                                                                                      |
| unified-trading-system-ui | `08998a92` · `70ca4b8c` (KillSwitchId mirror) · `15270ed6` (TreasurySource mirror)                                                                                                                                                                                                                                             |
| deployment-ui             | `26b7159` (operator-facing treasury dropdown, `pw:L2 ✓`)                                                                                                                                                                                                                                                                       |
| unified-trading-pm        | `f3518eec9` (codex tombstones + 5 issue docs superseded) · `6c5cfa812` (adapter baseline + cursor-configs) · `9730ec264`/`5b97d3672` (journals)                                                                                                                                                                                |

**Data purged** (`9730ec264`): 447,200 manifest rows (DEFI 430,248 + CEFI 16,952), 94 catalogue rows, 25,286 GCS
objects, 2 per-VM shards — across BOTH asset groups. Snapshots taken; both consolidator crons paused→resumed with
verified green cycles; both writer VMs (`mtds-solana-drift-backfill`, `cefi-pacifica-solana-*`) TERMINATED.

**KEPT + verified (the guard that mattered):** DRIFT/JUP/PACIFICA **tokens** — 40,693 manifest rows on other venues
(Binance-Futures/Bybit/Hyperliquid/Extended/Kamino/Lighter) plus `cefi_instrument_universe.py` rows plus the **Solana
asset-list `"DRIFT"` token in `utl/config_interface/domain_configs.py:170`** (the coordinator nearly deleted this
mid-sweep — logged as a near-miss). Non-perp Solana venues (JITO/KAMINO/ORCA/RAYDIUM/MARINADE/SANCTUM/SOLBLAZE/
MARGINFI/SOLEND) and all non-Solana perps (HYPERLIQUID/GMX/ASTER/LIGHTER-ZKSYNC/EXTENDED-STARKNET) untouched. Jupiter
(swap aggregator) untouched.

**Bugs the cull EXPOSED (each fixed, none pre-existing to the ruling):**

1. **Vacuous tests** — strategy-service's 11 F-09 stake-fraction tests went green _for the wrong reason_ once DRIFT
   became INELIGIBLE (`accepted_perp_collateral('DRIFT') == []` → every case returns None). Re-pointed the fixture to
   BYBIT (a real LST-margined venue: stETH/wstETH), proven live, so the risk rule is exercised again. Deleting them — or
   forcing HYPERLIQUID (USDC-margined → SPLIT_STAKE, f=0.5 legitimately allowed) — would both have been wrong.
2. **Schema/code divergence** — `scenario_overlay.schema.json` advertised a `KillSwitchId` the enum no longer had.
3. **Operator-facing dead option** — deployment-ui's Treasury dropdown offered `SUB_ACCOUNT_DRIFT`; selecting it would
   have failed. Every remaining option re-verified against UAC's live enum.
4. **Two collateral registries** — the cull cleaned `registry/venue_collateral.py` but
   `architecture_v2/ collateral_registry.py` kept a live `venue_id="drift"` entry (mSOL/JitoSOL @20%), which is why a
   dead-venue test stayed green.
5. **Cross-repo break** — UAC's enum removal broke UTL's treasury/custody/withdrawal imports (found + fixed in-band).
6. **KAMINO mislabel** — the MTDS gate caught a KEPT venue's `pipeline_mode` changing; verified against prod GCS that
   the cull FIXED a `batch_hyperliquid` mislabel (real data is `batch_onchain_subgraph`) — the test had pinned the bug.

**Process lessons (worth honouring next venue cull):**

- **The closing grep caught a missed surface SEVEN times** — deployment-service, its shell scripts, execution-service,
  2-of-4 python registries, strategy-service, e2e-testing, deployment-ui. Every time the coordinator would have declared
  done. Re-run it fleet-wide; never trust the last agent's "zero".
- **Grep case-insensitively.** Uppercase-biased patterns (`DRIFT-SOLANA`, `SUB_ACCOUNT_DRIFT`) were blind to lowercase
  `"drift"` venue ids in UAC/UTL/JSON — that blindness hid an entire `architecture_v2` module footprint for hours.
- **Sweep whole FILES, not the matched pattern.** Two separate files were "fixed" and still dirty (a second
  `_WIRED_VENUES` line; a second enum mirror in the same JSON).
- **Provider-first ordering** for coupled invariants (UAC-key ⊆ IS-adapter; launcher_registry ↔ VM_PREFIX_TO_BUCKET);
  both red-lit a consumer when done backwards. quickmerge's dirty-dep pre-flight is correct — fix the order, not the
  guard.
- **Generated bundles**: do NOT hand-patch. Two filed instead (see
  `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`).

**Open (tracked, not blocking):** the stale generated capability bundles (`capability-manifest.json`,
`capability-verdict-matrix.json`, `ui-reference-data.json`'s ~40 archetype lines) — need the resync tooling, filed.
Stale generated audit artifacts (`orphan-report.txt`, `type_usage_audit.json`) are outputs, not config.

## Progress log

- **2026-07-16T10:00-10:08Z** — Verified live (not assumed) the naming gotcha across all three DEFI surfaces + the
  scope-guard cross-check. Wrote + dry-ran the purge script. Paused the DEFI tick consolidator cron. Applied: DEFI
  manifest purge (424,450 DRIFT + 5,798 PACIFICA rows deleted, verified 0 residual), DEFI catalogue purge (84 rows
  deleted, verified 0 residual), DEFI raw-tick delete (23,723 objects) — **this last step's own post-delete re-list
  caught residual objects that had been re-created mid-purge**.
- **2026-07-16T10:08-10:10Z** — Root-caused the residual to two LIVE writer VMs (`mtds-solana-drift-backfill`,
  `cefi-pacifica-solana-2026-20260715-190049`) still actively writing kill-set data. Stopped both (GCP admin op).
  Found + deleted the DRIFT per-VM manifest shard (100% kill-set, 2,292 rows) that would otherwise have resurrected the
  purge on the next consolidator cycle.
- **2026-07-16T10:10-10:16Z** — Discovered PACIFICA-SOLANA also lives in the **CEFI** asset-group buckets (the stopped
  `cefi-pacifica-solana-*` VM's own task), outside this task's originally-named DEFI-only scope — folded in per the
  operator's "everything" ruling and the "any other state" instruction. Measured CEFI manifest (16,932 rows) + catalogue
  (10 rows) + a 100%-kill-set per-VM shard (2,780 rows). Refactored the purge script to a per-asset-group config
  (`AssetGroupConfig`) covering both DEFI and CEFI uniformly, added a `--phase per-vm` step, and made the drift-check
  idempotent-safe (a 0-count re-run is "already clean," not a scope-drift violation). Paused the CEFI tick consolidator
  cron (confirmed no in-flight execution first).
- **2026-07-16T10:17Z** — **Blocked mid-session**: `import unified_trading_library` started raising
  `AttributeError: type object 'KillSwitchId' has no attribute 'KILL_PER_TREASURY_SUB_ACCOUNT_DRIFT'`. Root cause: the
  sibling's in-progress, UNCOMMITTED UAC edit (`unified_api_contracts/canonical/crosscutting/kill_switch.py`) removed
  that enum member as part of the same operator ruling's CODE-track work — but `unified-trading-library` (a separate,
  clean, committed repo) still imports it at module load time (`unified_trading_library/kill_switch/bus.py:144`). This
  is a transient cross-repo consistency gap in the sibling's mid-flight WIP, not something introduced by this task. Per
  the explicit task-split instruction (never touch repo source outside the DATA/STATE lane) this task did NOT edit
  either file — armed a bounded background poll (15s cadence) waiting for the sibling to land a consistent state,
  continued other read-only verification work in the meantime (JUPITER zero-captured-rows confirmation via a direct
  `gcsfs`+`pyarrow` read that bypasses the broken import, since that's read-only verification not a GCS write; the
  launcher-registry grep; features/BQ "other state" sweep; AWS S3 access-check). [outcome: see next entry].

- **2026-07-16T12:42-12:44Z** — Coordinator confirmed the cross-repo fix landed (`unified-api-contracts@7628dd30`,
  `unified-trading-library@8f6b0a9f` + follow-up deleting the dead
  `TreasurySource.SUB_ACCOUNT_DRIFT`/`KillSwitchId.KILL_PER_TREASURY_SUB_ACCOUNT_DRIFT` references from
  `kill_switch/bus.py` + 3 treasury modules) and to resume without waiting on the background watcher. Verified the
  import works. **Found the DEFI cron still correctly `PAUSED` but the CEFI cron had silently flipped back to
  `ENABLED`** during the ~2.5h wait, and had been running every 1 minute the whole time (harmless while CEFI was still
  un-purged — nothing to corrupt yet) — re-paused it, confirmed no in-flight execution, then ran the full CEFI purge
  (`--asset-group cefi --phase all --apply`): manifest (16,952 rows) + catalogue (10 rows) applied clean on the first
  try. The `per-vm` phase hit a real bug (`list_blobs` returns `BlobMetadata` objects, not bare path strings —
  `AttributeError: 'BlobMetadata' object has no attribute 'endswith'`, exactly what basedpyright had already flagged as
  a warning) — fixed (`b.name` instead of `b`), re-ran clean (found the CEFI per-VM shard had already been absorbed +
  cleaned up by the CEFI consolidator during the wait, 0 left to delete — consistent with the manifest purge's row count
  already reflecting it). CEFI raw-tick: 1,286 objects deleted, 0 residual.
- **2026-07-16T12:53-12:54Z** — Re-ran a full dry-run sweep as a final check and **discovered the DEFI manifest had been
  resurrected** to its pre-purge state (430,248 matched again) despite the cron staying `PAUSED` per
  `gcloud scheduler jobs describe` — root-caused to an out-of-band consolidator write at 10:22:59Z (see
  §6/"resurrection" section above for the full writeup). Re-applied the DEFI manifest purge fresh (12:54:02Z, verified 0
  residual), re-ran the DEFI raw-tick phase to catch the 277 stragglers left by the (now-stopped) live VM from the
  original incomplete pass — 0 residual. Shipped the script (`market-tick-data-service@788daa2e`, direct push per the
  dirty-deps flow, pathspec-committed so no sibling WIP was bundled in).
- **2026-07-16T12:54:42-13:01Z** — Resumed both consolidator crons. Watched 3+ post-resume cycles on each
  (`succeededCount=1 failedCount=0` on the checked executions) and re-verified the manifest after each watch window on
  both asset groups — **stayed fully clean throughout, confirming the resurrection was a one-time race tied to the
  paused window, not a recurring risk**. Ran a final comprehensive `--asset-group all --phase all` dry-run
  (13:00-13:01Z): **0 matched on every surface, both asset groups** (manifest, catalogue, per-VM shards, raw tick).
  Re-confirmed both writer VMs still `TERMINATED`, no new instances spawned. Re-verified the token/scope guard on CEFI
  too (33,263 non-kill-set rows carrying DRIFT/PACIFICA/JUP substrings, all untouched). Finalized this issue doc with
  the complete, accurate final counts. **DATA/STATE half of the operator ruling is DONE** — outstanding handoff to the
  sibling/CODE track: flip `"mtds-solana-drift-backfill"` and `"cefi-pacifica-"` to `None` in
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py` (per § "Live-writer discovery"
  above) so the self-heal watchdog cannot relaunch either stopped VM; the MTDS repo-code deletion the coordinator
  flagged as "still in flight via a sub-agent" will make this doubly moot once it lands (the launcher would have nothing
  to invoke).
- **2026-07-18T10:07Z** — Closing pass (operator-directed, deployment-service-scoped sub-agent). Checked
  `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py` at current
  `origin/live-defi-rollout` HEAD before editing anything: the `[CODE] P0` handoff was **already satisfied** by
  `deployment-service@9b13679` (2026-07-16T13:15:01Z — landed same day, ahead of this handoff being picked up), which
  removed both entries outright rather than nulling them (a stronger fix — see the Todos-section note for the full
  verification). No code edit was required; ran `deployment-service`'s full `quality-gates.sh --no-fix` as evidence
  (green at HEAD `0a811e82b6d01a6b6f20a60f8966f3b56e4c1b2a`, sentinel-matched). Flipped `[CODE] P0` to done with the
  evidence trail. Also checked `[DATA] P2` (instruments-service confirmation-catalogue re-run): pre-conditions (IS +
  MTDS registry removal on origin) are satisfied, and `instruments-service@ee19f6f3` (2026-07-18) has since hardened
  `build_instrument_catalogue.py` to structurally exclude the killed venues from any future regen (unit-tested) — a
  durable guarantee beyond what a one-off confirmation run would give. No evidence found of an actual prod `--apply`
  regen run producing a literal 0-diff artifact; that step is instruments-service-repo scope and a prod mutation, both
  outside this task's bounds, so `[DATA] P2` is left open (non-blocking) with this status noted rather than checked off.
