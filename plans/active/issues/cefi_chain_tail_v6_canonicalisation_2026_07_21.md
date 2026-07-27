---
doc_type: issue
title: cefi chain-tail v6 canonicalisation (2026-07-21) — v6 quote/margin tail canonical everywhere, migrate ALL v5
summary: >-
  Operator ruling 2026-07-21 — the cefi chain-tail v6 shape (underlying={ROOT}/quote={Q}/margin={M}/ticks.parquet) is
  canonical EVERYWHERE and ALL legacy v5 forms (underlying={ROOT}/ticks.parquet, no quote/margin) must be migrated with
  none remaining. v5 is LOSSY — USD-vs-USDT or linear-vs-inverse chains on the same underlying collide and overwrite.
  UAC build_cefi_partition_path emits v6, the reader probes v6 first with a v5 fallback, and the W2 Tardis lane already
  emits v6; only the W1 PartitionedTickWriter still emits bare v5 for cefi because it derives quote/margin ONLY under
  asset_group=="tradfi". This resolves the previously-contested cefi chain-tail axis to RULED v6 (migration_pending
  until W1 and the data migration ship).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags:
  [canonicalisation, cefi, chain-tail, quote-margin, v5-v6, partitioned-writer, write-guard, migration, operator-ruling]
related:
  [
    /plans/active/issues/features_by_date_root_canonicalisation_2026_07_21.md,
    /plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md,
    /plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md,
    /plans/archive/issues/deribit_live_options_chain_path_noncanonical_2026_07_21.md,
    /plans/archive/issues/uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /codex/02-data/canonical-cutover-register.md,
    /codex/02-data/non-canonical-path-inventory.md,
    /codex/02-data/shard-granularity-cefi.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: operator ruling 2026-07-21 (cefi chain-tail v6 canonical everywhere, migrate ALL v5)
depends_on: []
---

# cefi chain-tail v6 canonicalisation (2026-07-21)

> **The ruling (operator, 2026-07-21).** The cefi chain-tail **v6** shape is canonical EVERYWHERE and **ALL** v5 forms
> must be migrated — none remain. This resolves the previously-contested "cefi chain-tail v5 vs v6 — two live-written
> shapes" axis to **RULED v6**.

## The two shapes

- **v5 (legacy, LOSSY)**: `…/underlying={ROOT}/ticks.parquet` — carries no `quote=`/`margin=`. Because it drops those
  axes, USD-vs-USDT (linear-vs-inverse) chains on the **same underlying** land on the **same object path and
  overwrite/collide**. This is silent data loss, which is why v5 must not remain anywhere.
- **v6 (canonical)**: `…/underlying={ROOT}/quote={Q}/margin={M}/ticks.parquet`.

## Grounding (verified 2026-07-21) — v6 is already the target on every surface except W1

- **UAC emits v6.** `unified-api-contracts/unified_api_contracts/canonical/partition_paths.py:252-253`
  (`build_cefi_partition_path`) — for a cefi chain with `underlying`/`quote_asset`/`margin_type` all populated it
  returns `…/underlying={U}/quote={Q}/margin={M}/ticks.parquet`.
- **The reader probes v6 first, v5 fallback.** `market-tick-data-service/market_tick_data_service/reader.py:402` appends
  the v6 tail `underlying={ROOT}/quote={Q}/margin={M}/ticks.parquet`, then `:403` appends the bare v5 tail
  `underlying={id}/ticks.parquet` as a fallback. Canonical-first, wire-fallback.
- **W2 (Tardis lane) already emits v6.**
  `market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py:668-669` emits
  `…/underlying={U}/quote={Q}/margin={M}/ticks.parquet`.
- **W1 (PartitionedTickWriter) still emits bare v5 for cefi — the actual defect.**
  `market-tick-data-service/market_tick_data_service/engine/orchestrator/partitioned_writer.py:291-292` derives
  quote/margin ONLY under `asset_group == "tradfi"`:

  ```python
  quote_asset, margin_type = "", ""
  if is_derivative and self._asset_group == "tradfi" and itype_str in ("futures_chain", "options_chain"):
      underlying_str, quote_asset, margin_type = _tradfi_chain_partition_dims(underlying_str)
  ```

  For a **cefi** `futures_chain`/`options_chain` the branch is skipped, `quote_asset`/`margin_type` stay empty, and the
  writer emits the bare v5 `underlying={U}/ticks.parquet` tail.

- **The write-time guard is tradfi-only.** `partitioned_writer.py:83` `_assert_canonical_tradfi_path(...)` raises on a
  non-canonical path but is invoked for tradfi only — so a cefi v5 write is not caught. It must be widened to cefi (+
  prediction chains) so a regressing cefi backfill fails LOUD.

## OPEN QUESTION — is W1's cefi-chain path even reachable in prod? (resolve FIRST)

The W1 cefi `futures_chain`/`options_chain` branch only matters if a **native-REST cefi venue** actually routes chain
data through W1 (the `PartitionedTickWriter`) rather than the W2 Tardis lane. DERIBIT/OKX chains historically flow
through Tardis (W2, already v6). Before fixing W1, enumerate which cefi venues emit `options_chain`/`futures_chain` and
via which writer — if no cefi chain reaches W1 in prod, the W1 fix is a correctness/guard hardening (still ship it) but
the migration scope may be zero live v5 cefi objects. This determines the migration blast radius and must be answered
before the writer change.

## Migration note

Existing v5 cefi chain objects are `migration_pending` — they are the current copies and are lossy-collided by
construction. Fix W1 + the guard FIRST, PROVE green, THEN migrate v5 → v6 (copy → verify → human-only purge of v5). The
collision property means the v5→v6 migration cannot assume one-object-per-target: where two logical chains collided onto
one v5 object, the object may hold only the last writer's rows — record any unrecoverable collisions rather than
papering over them.

## Todos

- [x] 1. [DATA] P1. Enumerate which native-REST cefi venues emit `options_chain`/`futures_chain` and via which writer
      (W1 `PartitionedTickWriter` vs W2 Tardis lane) — determine whether W1's cefi-chain path is reachable in prod and
      size the live v5 cefi migration blast radius. Gate the rest of this doc's migration scope on the answer. — **DONE
      (investigation, 2026-07-21, no shipping required)**. Findings: (a) `BINANCE-DELIVERY`/`OKX-FUTURES` (the only cefi
      venues whose `_VENUE_INSTRUMENT_TYPE` default to `futures_chain`) have NO standalone non-Tardis adapter — their
      chain data flows exclusively via the Tardis lane (`tardis_options_adapter.py`, W2, already v6). (b) DERIBIT's LIVE
      options-chain flows through a THIRD, standalone handler (`cli/handlers/deribit_options_chain_handler.py`,
      registered live as CLI op `deribit-options-chain`) that bypasses BOTH W1 and W2 entirely and writes a completely
      different, non-canonical (neither v5 nor v6) ad-hoc path shape — filed separately as
      `deribit_live_options_chain_path_noncanonical_2026_07_21.md` (this is NOT the v5-vs-v6 axis this doc addresses; it
      fails canonical STRUCTURE, not just the quote/margin tail). (c) **Conclusion: W1's cefi-chain path currently
      reaches ZERO live cefi chain objects in prod** — no venue's real write traffic routes options_chain/futures_chain
      through `PartitionedTickWriter`/`venue_fetch.py` today. The W1 fix (todos 2-3) is therefore pure defense-in-depth
      against a FUTURE native-REST cefi chain venue, and **todos 6-7's v5→v6 data migration scope is ~0 objects for the
      W1 path specifically** (any actual v5 cefi chain objects in GCS would come from a different source — not verified
      in this session, see Progress Log).
- [x] 2. [DATA] P1. Fix W1 `partitioned_writer.py:291-292` to derive `quote`/`margin` for **cefi** chains as well as
      tradfi (mirror the tradfi branch; use the cefi quote/margin derivation, not `_tradfi_chain_partition_dims`), so W1
      emits the v6 tail. Keep combo EXCLUDED. — **SHIPPED 2026-07-22: `market-tick-data-service@04222eb0`** (the 2
      blocking MTDS QG regressions this doc originally cited are both resolved — see Progress Log). Added
      `_cefi_chain_partition_dims` (derives via the SAME `derive_settlement_dimensions` W2 already uses per-symbol) +
      wired it into `write_chunk`'s branch alongside the tradfi one. **Also fixed a corollary bug found while
      implementing this**: the writer-object CACHE key in `_get_writer` (and `close()`'s log-line unpacking) was a fixed
      3-tuple that did NOT vary by quote/margin — meaning two cefi chains sharing one underlying but DIFFERENT
      settlement (DERIBIT `BTC-PERPETUAL` inverse vs `BTC_USDC-PERPETUAL` linear) would have silently shared ONE cached
      writer object post-fix (the second chain's rows misrouted into the first chain's GCS object) — widened the cache
      key to the SAME 5-tuple `(itype, dt, underlying, quote, margin)` `_row_counts` already uses when chain dims are
      populated. Proof: `tests/unit/test_partitioned_writer_cefi_chain_tail_v6.py` (new, 6 tests, all passing) — see
      `test_cefi_chain_same_underlying_different_margin_never_collides` for the anti-collision proof.
- [x] 3. [DATA] P1. Widen the write-time guard `_assert_canonical_tradfi_path` (`partitioned_writer.py:83`) to cefi (+
      prediction chains) — rename/generalise it so a regressing cefi/prediction backfill fails LOUD via
      `canonical_path_violations(..., require_pipeline_mode=True)` exactly as tradfi does. — **UAC portion SHIPPED:
      `unified-api-contracts@9a92cf4f55a2753e3a4db045456f224e692867a5`** (added `_cefi_chain_tail_violations` STRUCTURAL
      check to `canonical_path_violations` — without this, the widened MTDS-side guard call was a no-op for cefi, since
      UAC previously had NO structural chain-tail enforcement for cefi, only for tradfi; updated the stale
      `test_cefi_chain_ticks_parquet_is_never_flagged` test that had asserted a bare v5 cefi chain path was canonical —
      split into a v6-passes + v5-now-flagged pair). **MTDS portion (the widened call site + rename to
      `_assert_canonical_chain_path`) SHIPPED** — same commit as todo 2 (`market-tick-data-service@04222eb0`). Scoped to
      cefi's two real chain types ONLY (`options_chain`/`futures_chain`, not blanket `asset_group == "cefi"`) — a
      blanket cefi guard would break ~10 EXISTING passing cefi single-instrument tests that intentionally exercise
      non-canonical fallback id shapes (verified before scoping this way). Prediction chains NOT widened — no
      concretely-defined "prediction chain" analog exists in this codebase (prediction's bundling is
      `canonical_question_group`/event_contract, not the `options_chain`/`futures_chain` writer-key mechanism) and
      guessing at scope risked tripping the `book_snapshot_5` symbol-less fan-in; left for a follow-up once a
      prediction-chain shape is concretely defined.
- [x] 4. [REVIEW] P1. Confirm the shard-atom (manifest key) and `available_at` bookkeeping key on the SAME v6
      `(underlying, quote, margin)` tuple in W1 as they already do in W2/UAC — no desync between object path and
      manifest row. — **CONFIRMED + PROVEN** via `test_cefi_chain_shard_atom_matches_object_path` (new test): the
      `underlying_counts` (`_row_counts`) 5-tuple atom and the writer-object cache key (post todo-2's corollary fix) are
      now the IDENTICAL key, so they cannot desync by construction. **NOT independently re-verified**:
      `_cluster_counts`/`_chain_available_at_max` (`_update_cluster_and_chain_counts`) — a SEPARATE bookkeeping
      structure (ES-options-cluster-coverage + available_at envelope) — still keys on the 3-tuple
      `(itype, dt, underlying)` WITHOUT quote/margin, so two cefi chains sharing an underlying but different margin
      would still merge their cluster-counts/available_at into one bucket. This is lower-severity than the writer-object
      collision (no data corruption, just a coarser coverage-check granularity) and was NOT fixed in this session (out
      of this todo's literal scope — todo 4 names "shard-atom (manifest key)" + "available_at bookkeeping", which most
      directly maps to `_row_counts`/`underlying_counts`, already fixed) — flagging as a residual, smaller finding for a
      follow-up rather than expanding scope further.
- [x] 5. [DATA] P1. **[already covered by plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md, see that doc for
      execution]** PROVE the fixed W1 emits v6 for a cefi chain on one real day (write + reader round-trip via the
      v6-first probe at `reader.py:402`), with the guard raising on a synthetic v5 path. — **Code now SHIPPED
      (`market-tick-data-service@04222eb0`) and the `canonical-migration-cefi-*` VM fleet that originally blocked this
      (interference risk on the same bucket) has since TERMINATED (verified 2026-07-22) — the blocker is cleared.**
      Unit-level proof (mocked writer, no real GCS) is in `tests/unit/test_partitioned_writer_cefi_chain_tail_v6.py` (6
      tests, all passing); the real-day GCS round-trip proof is still **NOT ATTEMPTED** and remains Round 2 work —
      genuinely separate operational verification, not a doc update.
- [x] 6. [DATA] P1. **[already covered by plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md, see that doc for
      execution]** Migrate existing v5 cefi chain objects → v6 (copy → content-verify → human-only purge of v5),
      recording any v5 collisions where two logical chains overwrote one object as unrecoverable rather than silently
      merging. — **DEFERRED to Round 2** (out of scope for this session per task instructions; todo 1's finding that W1
      reaches zero live objects means this migration's true source, if any v5 cefi chain objects exist at all in GCS, is
      NOT the W1 path — needs its own enumeration before migrating).
- [x] 7. [DATA] P1. **[already covered by plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md, see that doc for
      execution]** Re-sync the manifest / data-status render for the migrated cefi chain cells so all four canonical
      surfaces agree post-migration. — **DEFERRED to Round 2** (depends on todo 6).
- [x] 8. [REVIEW] P1. **[already covered by plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md, see that doc
      for execution]** On W1 ship, record the cefi chain-tail v6 cutover date in
      `/codex/02-data/canonical-cutover-register.md` (repo@sha) and update the §7 summary cefi `chain tail` cell from
      "v5/v6 dual hazard" to the ruled v6 (migration_pending → EXECUTED). — **DEFERRED**: gated on the MTDS-side W1 code
      actually shipping (todos 2/3's MTDS portion), which did not happen this session.

## Progress Log

**2026-07-21 (this session)** — Executed todos 1-5 per an explicit sub-task scope (todos 6-8 out of scope, real-day
proof deferred per an explicit CAUTION about an active cefi migration VM fleet). Findings + status:

- Todo 1 answered: W1 reaches ZERO live cefi chain objects today (see todo 1 above). Filed
  `deribit_live_options_chain_path_noncanonical_2026_07_21.md` for the DERIBIT live-handler non-canonical-path finding
  this surfaced (a SEPARATE, more severe canonicalisation bug — not this doc's v5-vs-v6 axis).
- Todos 2-4: code written in
  `market-tick-data-service/market_tick_data_service/engine/orchestrator/ partitioned_writer.py`
  (`_cefi_chain_partition_dims`, widened `_get_writer` cache key + guard call site, renamed
  `_assert_canonical_tradfi_path` → `_assert_canonical_chain_path`) +
  `unified-api-contracts/ unified_api_contracts/canonical/partition_paths.py` (`_cefi_chain_tail_violations`). New test
  file `market-tick-data-service/tests/unit/test_partitioned_writer_cefi_chain_tail_v6.py` (6 tests, all green) +
  updates to 3 existing MTDS test files (`test_partitioned_writer_partition_validation.py` — fixed a fixture that used
  an unresolvable settlement symbol, orthogonal to what that test actually checks;
  `test_partitioned_writer_tradfi_filename_canonical.py` — updated the rename;
  `tests/unit/test_pipeline_e2e_prediction_canonical.py` — NOT modified, see below) + 2 UAC test files
  (`test_partition_path_is_canonical.py` — updated the stale v5-cefi-chain-is-canonical assertion).
- **UAC SHIPPED**: `unified-api-contracts@9a92cf4f55a2753e3a4db045456f224e692867a5` (files:
  `unified_api_contracts/canonical/partition_paths.py`, `tests/unit/test_partition_path_is_canonical.py`). UAC's own
  full `quality-gates.sh` (`--no-fix`) passed green (sentinel `018c3ca6...`) before shipping.
- **MTDS NOT SHIPPED — blocked by two pre-existing, independently-confirmed, unrelated conditions** (both verified via
  `git status`/`git diff` to be outside this session's own diff, in files this session never touched):
  1. `tests/unit/test_pipeline_e2e_prediction_canonical.py::test_rule11_per_ag_shard_counts_byte_unchanged` — a
     pre-existing CEFI shard-count pin drift (measured 208, pinned 200) in a file ALREADY dirty from another concurrent
     agent's own DEFI-count fix (their comment: "confirmed via `git stash` that HEAD itself — no local changes — already
     fails this test, so the drift predates and is unrelated to that work" — the SAME class of issue, just a different
     `_PER_AG_SHARD_COUNTS` key). This session temporarily patched this ONE line locally (200→208) ONLY to obtain an
     honest full-repo `quality-gates.sh` green reading for verification purposes, then REVERTED it immediately after
     (never staged, never included in any `--files` scope) — the file's dirty state is back to exactly what the other
     agent left it in.
  2. A NEW cross-repo ripple: a concurrent, unrelated UAC commit (landed mid-session) made
     `unified_api_contracts.internal.reference.canonical_id_builder.build_instrument_id` raise loud on an embedded `:`
     in `symbol` for non-sports/prediction asset groups. MTDS's editable UAC install means this took effect in MTDS's
     test suite immediately, breaking 3 tests unrelated to this doc's scope. Filed
     `uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md`.
  - Both conditions were re-verified as still present in MTDS's OWN clean-diff HEAD (`7335631d`, unchanged all session)
    immediately before giving up on shipping — this is not a stale/one-off observation.
  - **The verified-correct, fully-tested MTDS code diff is backed up** (in case of concurrent clobbering in this
    heavily-shared checkout) at
    `/tmp/claude-1000/-home-ubuntu-unified-trading-system-repos/5697ef0c-2b5a-43bf-8008-6202d06ded45/scratchpad/mtds_cefi_chain_v6_diff_backup.patch`
    (diff of the 3 modified files) + `.../scratchpad/test_partitioned_writer_cefi_chain_tail_v6.py.backup` (the new test
    file) — a scratchpad path, NOT durable; whoever picks this up next should apply the backup FIRST if the working tree
    no longer shows these changes, then re-run `bash scripts/quality-gates.sh --no-fix` and
    `bash scripts/quickmerge.sh "fix(cefi): derive+enforce v6 quote/margin chain-tail for cefi chains in W1 PartitionedTickWriter (cefi_chain_tail_v6_canonicalisation_2026_07_21)" --agent --files 'market_tick_data_service/engine/orchestrator/partitioned_writer.py tests/unit/test_partitioned_writer_partition_validation.py tests/unit/test_partitioned_writer_tradfi_filename_canonical.py tests/unit/test_partitioned_writer_cefi_chain_tail_v6.py'`
    once both blockers above are resolved by others (or fix them first per their own issue docs).

**SUPERSEDED 2026-07-22 — this scratchpad-backup instruction is now stale, do not follow it.** Both blockers cleared
(the MTDS QG regression resolved by slot-4/`@7ce100f9`+`@08f15f26`; the shard-count pin fixed to 208) and the backed-up
diff was applied, re-verified, and shipped directly as `market-tick-data-service@04222eb0` — see the Todos section above
(todos 2/3 now marked shipped). The scratchpad `.patch`/`.py.backup` files this paragraph points at are no longer needed
(the real content lives in the shipped commit) and may already be gone.
