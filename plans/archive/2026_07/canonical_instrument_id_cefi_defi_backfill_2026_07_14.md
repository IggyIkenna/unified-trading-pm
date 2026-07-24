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
status: complete # (was: active) 2026-07-15 plan-reconcile §6: remnant folded out to its target (operator ruling); zero open todos
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
    /plans/archive/2026_07/prediction_canonical_identity_migration_2026_07_08.md,
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
assigned_role: backend_engineer
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
- [x] ✅ [DATA] P1. Ran `build_instrument_catalogue.py --asset-group cefi --mode full` against real prod GCS — monotonic
      guard ACCEPTED (no durability landmine on CeFi, unlike DeFi). Verified 358,439/358,439 rows (100%) with
      `canonical_instrument_id` populated, correctly mirroring `instrument_key`.
- [x] ✅ [DATA] P1. **Attempted `build_instrument_catalogue.py --asset-group defi --mode full` — BLOCKED by the
      monotonic-shrink guard (correctly), redirected to a targeted in-place patch instead.** The full rebuild produced
      9,456 rows vs the live 10,372 and was rejected. Root-caused: unrelated pre-existing durability gap in
      `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md`'s Stage 4 (a catalog-only migration not
      reproducible from `by_date`) — see that doc's 2026-07-14 Progress Log entry for the full mechanism. Nothing was
      promoted; live catalogue untouched. `--mode full` is not currently safe for DeFi until that gap is closed.
- [x] ✅ [DATA] P1. **Corrected approach, executed**: wrote + dry-ran + applied
      `instruments-service/scripts/backfill_defi_canonical_id_and_glued_prefix_2026_07_14.py` (same dry-run/backup/
      `--apply` pattern as the lending migration) directly against `prod/catalog.parquet` — (a) backfilled
      `canonical_instrument_id = instrument_id` wherever blank (mechanically always-correct: for non-pool rows the
      catalog's own `instrument_id` already IS the resolved instrument_key; for POOL rows `instrument_id` is BY
      DEFINITION `pool_address.lower()`, which is also exactly `canonical_instrument_id`'s pool-row definition — no
      recomputation needed, verified `canonical_instrument_id == instrument_id` for all 10,372 rows post-patch); (b)
      fixed `glued_pair_id`'s venue-chain prefix in-place (same idempotent regex `_insert_version_underscore` uses,
      applied only to the existing prefix segment — no quote_asset/fee recomputation needed). Backup:
      `prod/catalog.20260714-042725.canonicalidgluedprefix.bak.parquet`. **Verified live**: 10,372 rows (unchanged),
      canonical_instrument_id 0 blank / 10,372 backfilled, glued_pair_id 3,502/7,145 pool rows had their prefix fixed, 0
      remaining no-underscore prefixes catalog-wide.
- [x] ✅ [VERIFY] P2. Confirmed deployment-api's `instrument_coverage.py` (the identified live consumer of
      `prod/catalog.parquet`) matches purely on `instrument_id` — never reads `canonical_instrument_id` or
      `glued_pair_id` — confirmed schema-compatible/additive-only via direct code read, no code change needed.
- [x] [BACKEND] P3. Post-phase codex audit — check whether `/codex/02-data/defi-canonical-naming-ssot.md` or
      `/codex/04-architecture/instrument-universe-registry-consolidation.md` document the (now-corrected) glued_pair_id
      polarity or canonical_instrument_id's CeFi/DeFi scope; update/SUPERSEDED-banner if they assert the old (wrong)
      state. — **FOLDED OUT** to plans/epics/instruments_master.md (2026-07-15, plan-reconcile §6 operator ruling);
      tracked there, not here.

## Progress Log

- **2026-07-14** — Investigated (see summary + §1-3 above), operator decisions obtained interactively for both open
  questions (CeFi canonical_instrument_id semantics; glued_pair_id prefix direction), implemented + unit-tested across
  `unified-api-contracts` (1 file + 1 test file) and `instruments-service` (62 adapter files +
  `build_instrument_catalogue.py` + its test file). Full `instruments-service` quality-gates run: one pre-existing,
  unrelated failure (`test_expected_universe_golden.py::test_expected_matches_golden[tradfi]`, a stale TradFi golden
  fixture — confirmed via `git stash` that it fails identically without this plan's changes; not touched here, out of
  scope). Shipping + the real prod catalog regens are the remaining todos above.
- **2026-07-14 (catalog regens)** — CeFi `--mode full` ran clean (guard ACCEPT), 358,439/358,439 rows verified
  populated. DeFi `--mode full` was correctly BLOCKED by the shrink guard — root-caused to an unrelated pre-existing
  durability gap (the 2026-07-13 lending A_TOKEN/DEBT_TOKEN migration patches the catalog directly and isn't
  reproducible from `by_date`; documented in `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md`). Redirected
  to a targeted in-place patch script instead of forcing the shrink through — both fixes (canonical_instrument_id
  backfill, glued_pair_id prefix) turned out to be simple, always-correct transforms on existing catalog columns, no
  by_date rebuild needed. Applied + fully verified: 10,372/10,372 rows have canonical_instrument_id, 0 rows have a
  no-underscore glued_pair_id prefix remaining. Remaining: P3 codex audit only.
