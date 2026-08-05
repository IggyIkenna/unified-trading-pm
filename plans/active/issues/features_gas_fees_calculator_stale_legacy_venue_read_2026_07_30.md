---
doc_type: issue
title:
  "features-service BlockPriorityGasDistributionCalculator silently read a frozen pre-fix gas_fees snapshot for 8 days
  (venue=chain vs writer's venue=ALCHEMY) — found + fixed"
summary: >-
  Discovered while staging the delete-safety proof for the gas_fees legacy-venue migration
  (`plans/active/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md`): a grep+READ Part-4 ("does
  anything still read the legacy path") turned up
  `features-service/features_service/onchain/app/calculators/block_priority_gas_distribution_calculator.py` building its
  GCS read shards with `venue=chain_name` — the pre-2026-07-22 legacy scheme. The writer
  (`market-tick-data-service@522185a6`, 2026-07-22) moved to `venue="ALCHEMY"` that same day; this reader was never
  updated to match, so from 2026-07-22 onward it silently kept reading the FROZEN pre-fix snapshot (last write under
  `venue=<CHAINNAME>` was ≤2026-07-21 for every chain) instead of live data — 8 days of the
  `block_priority_gas_distribution` feature group (feeding `ArbitrageMevBackrunEngine`'s priority-gas bid sizing)
  silently stale, with no error, no missing-data flag, no exception — just an old snapshot. Fixed same-day
  (`features-service@7f800b45`): repoint the shard spec to `venue="ALCHEMY"`.
status: open
nature: issue
asset_group: [defi]
stage: [features]
repos: [features-service, market-tick-data-service]
scope: [engineer, admin]
tags: [defi, gas-fees, features, stale-data, venue-naming, data-correctness]
related:
  [
    plans/active/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md,
    plans/archive/issues/defi_five_never_captured_venues_fix_2026_07_22.md,
  ]
created: 2026-07-30
author: unknown
parent_epic: defi_master
source: [data_engineering slot-7, 2026-07-30]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: data_engineering
drift_direction: neutral
depends_on: []
last_updated: 2026-07-30
locked_by:
locked_since:
context_scope:
  [
    features-service/features_service/onchain/app/calculators/block_priority_gas_distribution_calculator.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/gas_fee_handler.py,
    /plans/archive/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
supersedes:
superseded_by:
resolved_by:
---

## What I found

While running Part 3/Part 4 of the standard delete-safety proof (grep-then-READ for any code that still writes or reads
the legacy `venue=<CHAINNAME>` gas_fees path, before staging the legacy-prefix delete for the migration above), a
sub-agent search across `market-tick-data-service`, `execution-service`, `features-service`, and
`market-data-processing-service` found:

- **Part 3 (writers): clean.** Every write call site in `gas_fee_handler.py` resolves to the module constant
  `_GAS_FEE_VENUE = "ALCHEMY"` — confirmed by reading all 13 `venue=` occurrences across the EVM/Solana/BTC collection
  paths. (One unrelated dead-code caveat noted: `_collect_latest_fees`/`_write_latest_fees_shard` writes an even-older
  venue-less flat path, but is unreachable in the current prod scheduler wiring — tracked as a separate, non-blocking
  follow-up below, not this doc's main finding.)
- **Part 4 (readers): NOT clean.**
  `features-service/features_service/onchain/app/calculators/ block_priority_gas_distribution_calculator.py::fetch_data()`
  built `CanonicalDefiShard(venue=chain, chain=chain, ...)` for every chain in its own `_GAS_FEE_CHAINS` list — i.e. it
  queries the GCS path by `venue=<CHAINNAME>`, the pre-2026-07-22 legacy scheme, never `venue=ALCHEMY`. The module's own
  docstring (now corrected) stated the stale belief verbatim: _"MTDS gas-fee handler writes one shard per chain with
  venue==chain."_ That was true until 2026-07-22 and has been false since.

**Consequence, concretely**: since the writer fix landed 2026-07-22, this calculator's `read_canonical_defi_parquets`
call has resolved to a GCS prefix (`venue=<CHAINNAME>`) that receives ZERO new writes — every day since has been
silently reading the exact same frozen dataset as of the last legacy write (≤2026-07-21 per chain, confirmed in the
migration doc's scoping data). No error was raised (`read_canonical_defi_parquets` on an empty-going-forward but
non-empty-historically prefix just returns the historical rows it always found), no manifest gap fired (the manifest
correctly shows fresh `captured` rows under `venue=ALCHEMY` — this reader simply never looks there), and
`calculate_features` never saw an empty-input warning because the historical rows it DID read were never empty — just
increasingly out of date. This is the "wrong query, right-shaped answer" failure mode: nothing about the output shape
signals staleness.

**Fixed same-day** (`features-service@7f800b45`): changed `venue=chain` → `venue="ALCHEMY"` in the shard-spec
construction (chain= is unchanged — it's still the correct grouping key downstream in `calculate_features`, which groups
by `chain`, not `venue`), and corrected both stale docstrings (module-level comment + `fetch_data`'s own docstring).
Verified the existing unit tests (`tests/onchain/unit/test_defi_pipeline_extension_calculators.py`) only exercise
`calculate_features`/ `source_name`, never `fetch_data`'s shard construction, so the fix needed no test updates to stay
green.

## Why it matters

- **This is exactly the failure mode "big finding" rules exist for**: a live, silent, ongoing data-correctness gap in a
  production feature feeding a trading-decision engine (`ArbitrageMevBackrunEngine`'s priority-gas bid sizing),
  discovered as a side effect of an unrelated migration's delete-safety diligence — not because anything alerted on it.
- **The venue-naming fix that caused this (`market-tick-data-service@522185a6`, 2026-07-22) only updated the WRITER — no
  corresponding audit of READERS was done at the time.** The migration doc that this fix's history traces through
  explicitly flagged the retroactive-path consequence for HISTORICAL data but never asked "does anything currently read
  by the OLD venue key". This doc closes that specific gap; the general lesson (a venue/path-scheme rename needs a
  reader audit, not just a writer fix + historical migration) is worth keeping in mind for any future rename of this
  shape.
- **The bug was invisible to every existing signal** — no exception, no manifest gap, no empty-DataFrame warning. Worth
  flagging as a pattern: a reader keyed on a hardcoded/stale scheme silently degrades to "stale but shaped like real
  data," which is harder to catch than an outright failure.

## Todos

- [x] [DATA] P1. Repoint `block_priority_gas_distribution_calculator.py`'s shard spec from `venue=chain` to
      `venue="ALCHEMY"`, correct the two stale docstrings. — **Done 2026-07-30**, `features-service@7f800b45`.
- [x] [DATA] P2. ✅ `_GAS_FEE_CHAINS` in this same calculator lists `GNOSIS`, which is not in `gas_fee_handler.py`'s
      `DEFAULT_GAS_FEE_CHAINS` — the calculator silently reads an always-empty shard for that chain. Reconciled the two
      chain lists. — **Done 2026-08-03**, `features-service@09c07ead`. **Scope note**: the reconciliation surfaced a
      second, more consequential drift than this todo's own text described — see Progress Log. (repo: features-service)
- [ ] [DATA] P3. The dead-code `_collect_latest_fees`/`_write_latest_fees_shard` path in `gas_fee_handler.py` (lines
      822-886) writes to an even-older, venue-less flat path (`gas_fees/chain_id={id}/date={d}/...`) that bypasses
      `write_defi_rows` entirely. Confirmed unreachable in the current prod scheduler wiring
      (`defi_collection_scheduler.tf` always passes a date via `BatchPayload`), so not urgent — but it's a landmine if
      any future caller invokes the handler without a date. Consider deleting the dead branch entirely rather than
      leaving it as a latent legacy-path writer. (repo: market-tick-data-service)

## Progress Log

- **2026-07-30 (data_engineering slot-7)**: found via delete-safety Part 4 grep+READ sweep (sub-agent search across 4
  repos, 41 tool calls, full negative-result documentation for the clean repos/paths). Fixed same-day. This finding is
  what changes the delete-safety proof's disposition for the legacy `venue=<CHAINNAME>` gas_fees prefix from a hoped-for
  `yes-twin-confirmed` to `no-migrate-first` UNTIL this fix (now shipped) is confirmed live — see the delete-safety
  proof recorded in `plans/active/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md`.
- **2026-08-03 (data_engineering slot-6)**: closed the P2 todo (`features-service@09c07ead`), and while comparing the
  two chain lists in full (not just the GNOSIS entry the todo named), found the drift was bigger than described in BOTH
  directions: `_GAS_FEE_CHAINS` had `GNOSIS` (never collected by `gas_fee_handler.py`'s `DEFAULT_GAS_FEE_CHAINS` —
  confirmed always-empty read, harmless) AND was separately _missing_ `LINEA`, `FANTOM`, `CELO`, `MANTLE`, `AURORA` —
  five chains `DEFAULT_GAS_FEE_CHAINS` DOES collect gas-fee data for, that `block_priority_gas_distribution_calculator`
  was silently never reading at all. That second half is a real (if lower-severity than the venue-name bug above)
  data-correctness gap in the same feature/engine (`ArbitrageMevBackrunEngine` priority-gas sizing) this doc's main
  finding covers — LINEA in particular is fully backfill-capable per `gas_fee_handler.py`'s own comments, so real
  historical rows for that chain existed and were never picked up by this calculator until now. Fixed in the same commit
  (removed `GNOSIS`, added the five missing chains); repointed the module comment to cite `DEFAULT_GAS_FEE_CHAINS`
  directly as the sync source instead of the vaguer "Tier 1+2" framing, since a cross-repo import isn't allowed here (T4
  forbids features-service -> market-tick-data-service deps) and the old framing is what let this drift happen
  unnoticed. No test hardcoded the list contents, so no test changes were needed
  (`tests/onchain/unit/test_defi_pipeline_extension_calculators.py` only exercises `calculate_features`/`source_name`,
  confirmed by reading it, same as the original 2026-07-30 fix's note).
- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
- **2026-08-05 (data_engineering slot-12)**: P3 started. Code complete + verified (gas_fee_handler.py: removed
  `_collect_latest_fees`/`_write_latest_fees_shard`, rewrote `_collect_one_evm_chain` to always run the date-scoped
  path; test_gas_fee_handler.py + test_gas_fee_handler_coverage.py updated: removed TestCollectLatestFees, repointed
  patches to `_collect_for_date`). Module imports clean, methods confirmed removed. **NOT SHIPPED — blocked.** The diff
  is in the **`market-tick-data-service` WORKING TREE** (3 files: `cli/handlers/gas_fee_handler.py`,
  `tests/unit/test_gas_fee_handler.py`, `tests/unit/test_gas_fee_handler_coverage.py`; the 3
  `tests/schema_artifacts/*.json` trailing-newline regens are regenerable and deliberately excluded). Two blockers,
  fully documented in `plans/active/issues/mtds_qg_red_combined_coverage_shortfall_2026_08_05.md`: (1) MTDS has 2
  PRE-EXISTING test failures on a clean tree (collect_handler_schema `[lending]`, orchestrator tier3_polymarket) that
  block ALL MTDS commits under the green-tree rule — repo-blocker RB (mtds qg_red) declared. (2) **COVERAGE NON-ISSUE
  (corrected 2026-08-05)**: the earlier "this diff drops coverage 80.65%→76.21%" claim was a TRUNCATED-RUN artifact —
  the authoritative full quality-gates.sh run WITH the diff is 80.63% (PASSES the 79% gate, −0.02pt vs clean); no
  compensating coverage needed, P2 in the blocker doc dismissed. The ONLY remaining blocker is the 2 pre-existing
  failures. P3 checkbox NOT flipped (correct — not shipped, green-tree rule holds). The blocker issue doc itself was
  unpushable via quickmerge at filing time because the PM full gate is red on a pre-existing `agent-rules-size-cap`
  (cursor-configs/CLAUDE.md 48 B over cap) and a concurrent session's live edit dirtied the tree — see that doc's
  Progress Log.
- **2026-08-05 (data_engineering slot-12) RB GREEN — UAC removal shipped, MTDS re-gate in progress**: the two
  pre-existing failures were resolved by the UAC-side operator decision — `unified-api-contracts@5f441e0d` removed AAVE
  `collect-rewards` + POLYMARKET `fills` declarations (fleet doc
  `plans/active/issues/mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md`). Blocker RB-04b8981e unblock
  criterion (MTDS QG green on LDR baseline) is being re-checked: full `bash scripts/quality-gates.sh` WITH the gas_fee
  diff running (started ~14:04Z, log `/tmp/qg_green_ship.log`) — the editable-install view now includes `5f441e0d`, so
  the 2 failures should clear. **NEXT STEP (the only remaining work)**: when that QG is green, ship the 3 code files via
  `bash scripts/quickmerge.sh "<msg>" --agent --files "cli/handlers/gas_fee_handler.py tests/unit/test_gas_fee_handler.py tests/unit/test_gas_fee_handler_coverage.py"`
  (quickmerge auto-stamps `Quickmerge: agent`), flip THIS P3 checkbox `[ ]`→`[x]` in the SAME turn with the landed SHA,
  push the docs flip via the PM docs-only carve-out (docs commits are exempt from strict-quickmerge), verify
  `git merge-base --is-ancestor <sha> origin/live-defi-rollout`, then POST /done.
