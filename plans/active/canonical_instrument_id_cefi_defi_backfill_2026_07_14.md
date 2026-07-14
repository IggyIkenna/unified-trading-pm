---
doc_type: plan
title: canonical_instrument_id population for CeFi/DeFi + the coupled DeFi glued_pair_id prefix fix
summary:
  InstrumentRecord.canonical_instrument_id was never populated for CeFi/DeFi (0% in both catalogs) — the field's own
  docstring scoped it to TradFi/Databento's raw-exchange-code-to-human-product-root translation, a problem CeFi/DeFi
  don't have (their symbols are already human-readable), so the correct value there is simply instrument_key. Also fixes
  a separate, coupled bug — DeFi's glued_pair_id venue prefix had drifted to the wrong (no-underscore) form on every
  catalog regen because the live UAC helper was never updated after the 2026-07-08/09 operator decision that the
  with-underscore form is canonical.
status: active
nature: design
asset_group: [cefi, defi]
stage: [data]
repos: [unified-api-contracts, instruments-service]
scope: [engineer]
tags: [canonical_instrument_id, instrument-id, canonicalization, cefi, defi, glued_pair_id, uniswap]
related:
  [
    issues/instrument_id_format_canonicalization_2026_07_08.md,
    audit/results/canonical_instrument_id_audit_2026_07_08.md,
    prediction_canonical_identity_migration_2026_07_08.md,
  ]
created: 2026-07-14
last_updated: 2026-07-14
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  "Operator, 2026-07-14: 'Populate canonical_instrument_id for CeFi/DeFi going forward + backfill historical' + 'also
  needs a migration of gcs data if not already done right'. Design decisions made interactively — see Progress Log for
  the exact operator rulings on CeFi semantics and the glued_pair_id prefix direction."
assigned_role: backend-engineer
drift_direction: advance-code
---

# canonical_instrument_id population for CeFi/DeFi + the coupled DeFi glued_pair_id prefix fix

## 1. Background

`InstrumentRecord.canonical_instrument_id`
(`unified-api-contracts/unified_api_contracts/internal/reference/ instrument.py:129-136`) is documented as "populated by
TradFi/Databento adapters from the UAC exchange-code registry... Optional + additive so existing CeFi/DeFi rows... are
unaffected" — i.e. by design, CeFi/DeFi were never meant to populate it. Measured live (2026-07-14): CeFi catalog
(`instruments-store-cefi-prd-...`, 358,273 rows) and DeFi catalog (`instruments-store-defi-prd-...`, 10,360 rows) both
showed 0% real population.

TradFi's use case: raw exchange ticker codes are genuinely opaque (`ESH6` = CME's code for a March-2026 S&P 500 future),
so `canonical_instrument_id` runs the exchange code through a registry (`_resolve_product_root`,
`databento/symbology.py:183`) to surface a human name (`SP500`) distinct from `instrument_key` (which inherits the raw
code verbatim). **CeFi/DeFi have no such gap** — `base_asset` (`BTC`, `ETH`, ...) and DeFi protocol/token names are
already human-readable, so `instrument_key` already IS what TradFi needs a separate field to produce. Operator confirmed
(2026-07-14, after a clarifying back-and-forth about whether CeFi already "bundles by underlying"):
**`canonical_instrument_id := instrument_key` for both CeFi and DeFi** — not a stopgap alias, the actually-correct value
given there's no translation problem to solve.

## 2. The coupled (but independent-scope) glued_pair_id bug

While investigating DeFi's canonical_instrument_id, found `glued_pair_id`'s POOL-row venue prefix (e.g.
`UNISWAP_V3-ARBITRUM`) had drifted: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/defi.py`'s
`glued_venue_prefix()` stripped the version-token underscore (`UNISWAP_V3` → `UNISWAPV3`) on every catalog regen, even
though the 2026-07-08/09 operator decision (`issues/instrument_id_format_canonicalization_2026_07_08.md` finding 2,
`docs/DEFI_INSTRUMENTS.md`) explicitly made the WITH-underscore form canonical and a one-off migration already flipped
6,352 rows to match — `defi.py` was just never updated afterward, so every regen since has been silently reverting rows
back to the wrong form. Measured 2026-07-14: 2,282 rows (87.7%) no-underscore (wrong) vs. 319 rows (12.3%)
with-underscore (correct, and shrinking each regen). Operator confirmed (2026-07-14): with-underscore is correct; the
live code was the bug, not the minority of rows.

**This is a separate field from canonical_instrument_id** (confirmed by reading `build_instrument_catalogue.py`'s
`_defi_pool_dual_form`: for a POOL row, `identity.canonical_instrument_id` is `pool_address.lower()` — a completely
different, machine/manifest concept from `glued_pair_id`'s human-readable display string — and neither one was ever
wired to the catalog's actual `canonical_instrument_id` COLUMN before this plan). Fixing the two together here only
because they were discovered in the same investigation, not because one depends on the other.

## 3. What shipped

**`unified-api-contracts`**: `defi.py`'s `glued_venue_prefix()` now calls `_insert_version_underscore()` instead of
`_strip_version_underscore()` (the latter, now unused, removed) — the glued prefix preserves/self-heals the
with-underscore form. `split_glued_venue_chain()` (the reverse parse) already self-heals legacy no-underscore data via
the same idempotent helper — no change needed there. Docstrings + `tests/unit/test_defi_pool_identity.py` updated to the
corrected polarity (22 tests, all passing).

**`instruments-service` adapters** (62 files: 12 CeFi + 50 DeFi): every `InstrumentRecord(...)` construction site now
sets `canonical_instrument_id=<same value as instrument_key>` (extracting the expression to a local variable first where
it was previously inline, to avoid computing it twice). Deliberately did NOT fix any pre-existing
instrument_key-construction quirks encountered along the way (e.g. `uniswap_v3.py`/`uniswap_v2.py` bypassing the shared
SSOT builder with a manual f-string) — canonical_instrument_id mirrors whatever instrument_key already computes, correct
or not; that's a separate, out-of-scope decision.

**`instruments-service/scripts/build_instrument_catalogue.py`** (`build_catalogue_dataframe`, the shared CeFi/DeFi/
TradFi full+incremental rollup path): `_extract_meta()` now carries `canonical_instrument_id` through from the per-date
row; the row-construction site sets
`"canonical_instrument_id": agg.meta.get("canonical_instrument_id") or agg.meta.get("instrument_key") or ""`. The
fallback is the key design choice: it means a SINGLE catalog regen (no separate migration script) both fixes
glued_pair_id AND fully backfills canonical_instrument_id for every historical row — including rows captured before the
adapter fix ships, since instrument_key is already carried through unconditionally and is, by the policy in §1, the
IDENTICAL value the adapter fix would have set. New tests added covering the carry-through + backfill-fallback +
DeFi-POOL-vs-address distinction.

**GCS migration**: per the operator's explicit ask ("also needs a migration of gcs data if not already done right") —
**no separate by_date-shard migration is needed or planned**. Scope research (2026-07-14) confirmed no live consumer
reads `canonical_instrument_id` off a by_date shard (only `deployment-api`'s `prod/catalog.parquet` read matters), and
the by_date corpus is 2 orders of magnitude larger than the two catalogs (CeFi ~42K live shard files / ~37M rows; DeFi
~179K files / ~10.2M rows) for zero downstream benefit. The catalog-level fallback above is both the correct AND the
complete backfill — running `build_instrument_catalogue.py --mode full` for cefi and defi is the whole migration.

## 4. Todos

- [x] ✅ [BACKEND] P1. Fix `glued_venue_prefix()` polarity + update tests — `unified-api-contracts@9341ac6`.
- [x] ✅ [BACKEND] P1. Add `canonical_instrument_id=instrument_key` to all 12 CeFi adapters —
      `instruments-service@f90d0e0`.
- [x] ✅ [BACKEND] P1. Add `canonical_instrument_id=instrument_key` to all 50 DeFi adapters —
      `instruments-service@f90d0e0`.
- [x] ✅ [BACKEND] P1. Wire `canonical_instrument_id` through `build_instrument_catalogue.py`'s shared CeFi/DeFi rollup
      path (carry-through + instrument_key fallback) + new tests — `instruments-service@f90d0e0`.
- [x] ✅ [SCRIPT] P1. Ship all of the above — `unified-api-contracts@9341ac6` then `instruments-service@f90d0e0`
      (quality-gates-green both, quickmerge). Also fixed 2 unrelated pre-existing QG blockers hit along the way (stale
      golden fixture `instruments-service@bdb2dc6`; empty-string-fallback ratchet `instruments-service@272b012`).
- [ ] [DATA] P1. Run `build_instrument_catalogue.py --asset-group cefi --mode full` against real prod GCS
      (manifest-verified row count, monotonic guard expected to ACCEPT — this is a metadata-only backfill, row count
      should be unchanged or grow, never shrink). Evidence: rows before/after + guard decision.
- [x] ✅ [DATA] P1. **Attempted `build_instrument_catalogue.py --asset-group defi --mode full` — BLOCKED by the
      monotonic-shrink guard (correctly), redirected to a targeted in-place patch instead.** The full rebuild produced
      9,456 rows vs the live 10,372 and was rejected. Root-caused: unrelated pre-existing durability gap in
      `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md`'s Stage 4 (a catalog-only migration not
      reproducible from `by_date`) — see that doc's 2026-07-14 Progress Log entry for the full mechanism. Nothing was
      promoted; live catalogue untouched. `--mode full` is not currently safe for DeFi until that gap is closed.
- [ ] [DATA] P1. **Corrected approach**: write a targeted, safe, in-place one-off migration (same pattern as
      `canonicalize_defi_lending_atoken_debttoken_catalog_2026_07_13.py` — dry-run, timestamped backup, `--apply`) that
      reads the live `prod/catalog.parquet` directly and (a) sets `canonical_instrument_id = instrument_key` wherever
      blank, (b) recomputes `glued_pair_id` for POOL rows using the now-fixed `glued_venue_prefix()`. Does not touch
      `by_date`, does not risk the Stage-4 durability landmine. Evidence: rows before/after, spot-check (a)
      canonical_instrument_id non-blank catalog-wide, (b) glued_pair_id's Uniswap-V3-family prefix 100% with-underscore
      post-patch (re-run the 87.7%/12.3% measurement from §2).
- [ ] [VERIFY] P2. Confirm deployment-api's `instrument_coverage.py` (the one identified live consumer of
      `prod/catalog.parquet`) reads the new field/corrected prefix without needing its own code change (expected — it's
      schema-compatible, additive-only) — a quick read-path check, not a code change unless something's wrong.
- [ ] [BACKEND] P3. Post-phase codex audit — check whether `codex/02-data/defi-canonical-naming-ssot.md` or
      `codex/04-architecture/instrument-universe-registry-consolidation.md` document the (now-corrected) glued_pair_id
      polarity or canonical_instrument_id's CeFi/DeFi scope; update/SUPERSEDED-banner if they assert the old (wrong)
      state.

## Progress Log

- **2026-07-14** — Investigated (see summary + §1-3 above), operator decisions obtained interactively for both open
  questions (CeFi canonical_instrument_id semantics; glued_pair_id prefix direction), implemented + unit-tested across
  `unified-api-contracts` (1 file + 1 test file) and `instruments-service` (62 adapter files +
  `build_instrument_catalogue.py` + its test file). Full `instruments-service` quality-gates run: one pre-existing,
  unrelated failure (`test_expected_universe_golden.py::test_expected_matches_golden[tradfi]`, a stale TradFi golden
  fixture — confirmed via `git stash` that it fails identically without this plan's changes; not touched here, out of
  scope). Shipping + the real prod catalog regens are the remaining todos above.
