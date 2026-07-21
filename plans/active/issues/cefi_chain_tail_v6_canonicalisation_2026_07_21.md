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
    features_by_date_root_canonicalisation_2026_07_21.md,
    instrument_availability_hive_canonicalisation_2026_07_21.md,
    tradfi_canonical_path_migration_design_2026_07_19.md,
    ../../../codex/02-data/cross-asset-canonical-target-ssot.md,
    ../../../codex/02-data/canonical-cutover-register.md,
    ../../../codex/02-data/non-canonical-path-inventory.md,
    ../../../codex/02-data/shard-granularity-cefi.md,
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

- [ ] 1. [DATA] P1. Enumerate which native-REST cefi venues emit `options_chain`/`futures_chain` and via which writer
      (W1 `PartitionedTickWriter` vs W2 Tardis lane) — determine whether W1's cefi-chain path is reachable in prod and
      size the live v5 cefi migration blast radius. Gate the rest of this doc's migration scope on the answer.
- [ ] 2. [DATA] P1. Fix W1 `partitioned_writer.py:291-292` to derive `quote`/`margin` for **cefi** chains as well as
      tradfi (mirror the tradfi branch; use the cefi quote/margin derivation, not `_tradfi_chain_partition_dims`), so W1
      emits the v6 tail. Keep combo EXCLUDED.
- [ ] 3. [DATA] P1. Widen the write-time guard `_assert_canonical_tradfi_path` (`partitioned_writer.py:83`) to cefi (+
      prediction chains) — rename/generalise it so a regressing cefi/prediction backfill fails LOUD via
      `canonical_path_violations(..., require_pipeline_mode=True)` exactly as tradfi does.
- [ ] 4. [REVIEW] P1. Confirm the shard-atom (manifest key) and `available_at` bookkeeping key on the SAME v6
      `(underlying, quote, margin)` tuple in W1 as they already do in W2/UAC — no desync between object path and
      manifest row.
- [ ] 5. [DATA] P1. PROVE the fixed W1 emits v6 for a cefi chain on one real day (write + reader round-trip via the
      v6-first probe at `reader.py:402`), with the guard raising on a synthetic v5 path.
- [ ] 6. [DATA] P1. Migrate existing v5 cefi chain objects → v6 (copy → content-verify → human-only purge of v5),
      recording any v5 collisions where two logical chains overwrote one object as unrecoverable rather than silently
      merging.
- [ ] 7. [DATA] P1. Re-sync the manifest / data-status render for the migrated cefi chain cells so all four canonical
      surfaces agree post-migration.
- [ ] 8. [REVIEW] P1. On W1 ship, record the cefi chain-tail v6 cutover date in
      `codex/02-data/canonical-cutover-register.md` (repo@sha) and update the §7 summary cefi `chain tail` cell from
      "v5/v6 dual hazard" to the ruled v6 (migration_pending → EXECUTED).
