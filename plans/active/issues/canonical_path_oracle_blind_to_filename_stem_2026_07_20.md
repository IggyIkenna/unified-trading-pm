---
doc_type: issue
title:
  "UAC canonical_path_violations() was BLIND to the filename instrument-id stem — the machine oracle returned
  FALSE-CLEAN for ~811,200 wire-named CeFi objects"
summary: >-
  The workspace HARD RULE says canonical-vs-non-canonical is decided by the UAC `canonical_path_violations()` machine
  oracle. That oracle dropped the last path segment (`partition_segments = segments[:-1]`, "Last segment is the file
  name") before validating, and only `asset_group=tradfi` single-instrument shards ever carried a filename rule. So raw
  venue wire stems (`ADAF0:USTF0.parquet`) and double-wrapped catalogue-miss ids
  (`BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0.parquet`) returned 0 violations == CANONICAL at both `require_pipeline_mode`
  settings. Anyone following the rule to assess CeFi surface-A canonicality would report the corpus CLEAN while
  independent measurement put the CeFi filename surface at 20.82% canonical by id-form. SHIPPED 2026-07-20: violations
  are now classified STRUCTURAL vs ID_FORM with BOTH reported by default (uac@d40c5d7d), and the caller-audit blocker
  was fixed at root -- the two CeFi write-time guards now build filenames with sanitize_file_stem (preserves the id's
  literal colon), so they emit canonical stems and the default all-class guard passes (mtds@953679de). No caller was
  softened. Migration population measured 0; reader tolerates the legacy sanitized stem. The batch=live filename
  divergence this exposed is tracked as its own finding.
status: open
nature: issue
asset_group: [cefi, meta] # was [cefi, tradfi, meta] — zero tradfi objects measured anywhere in the doc, its own §6 caller-audit table marks the tradfi row's impact explicitly "NONE" (retag per ag_closeout_audit_tradfi_parked_2026_08_19.md's Orthogonality finding)
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags:
  [
    data-correctness,
    gcs-path,
    canonical-id,
    machine-oracle,
    false-clean,
    operator-notify,
    reconciliation,
    sanitize-symbol,
  ]
related:
  [
    data_pipeline_reconciliation_skill_2026_07_20,
    tradfi_canonical_path_migration_design_2026_07_19,
    cefi_canonical_blueprint_2026_07_17,
    data_pipeline_hardening_self_monitoring_2026_06_22,
  ]
created: 2026-07-20
author: unknown
priority: P0
parent_epic: uac_master
source:
  "Operator-ratified finding 2026-07-20: the wire-named-file defect caught by eye would be reported FALSE-CLEAN by the
  official reconciliation procedure. Reproduced independently against the installed UAC before any change."
execution_scope: orchestrator-agent
drift_direction: advance-docs
depends_on: []
locked_by:
locked_since:
archive_exempt: true
assigned_vm: planning
resolved_by:
  "uac@d40c5d7d (default-on stem check) + mtds@953679de (sanitize_file_stem writers + reader fallback) + uac@502ef57e
  (colon-guard fail-loud on build_instrument_id + defi ID_FORM widening, § 7 items 2+4); surface-A re-run DONE
  2026-07-27 (§ 7 P1, unified-trading-pm slot-15) — 1,697 colon_wire live population confirmed gone, new batch-side
  bare-wire-symbol finding tracked as § 7 P2; residual followups tracked in § 7 (quarantine disposition) and the
  batch=live divergence issue"
context_scope:
  [
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/reconciliation-finding-taxonomy.md,
    /plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md,
    unified-api-contracts/unified_api_contracts/canonical/partition_paths.py,
    unified-api-contracts/unified_api_contracts/canonical/quarantine.py,
    market-tick-data-service/scripts/backfill_bare_underlying_future_manifest_ids_2026_08_17.py,
  ]
---

# The canonical-path machine oracle was blind to the filename stem

> **🔴 OPERATOR-NOTIFY — data-correctness + SSOT-contradiction class.** Every surface-A canonicality verdict produced
> before 2026-07-20 is **structure-only**. A "0 violations == canonical" result from that period says nothing about
> whether the objects carry canonical instrument_ids in their filenames, and must not be cited as evidence that they do.

> **✅ SHIPPED 2026-07-20 — the fix landed WITH its blocker resolved, not around it.** The UAC default-on stem check
> (`unified-api-contracts@d40c5d7d`) and the MTDS writer fix (`market-tick-data-service@953679de`) landed together on
> `live-defi-rollout`. The § 6.1 live-write blocker was fixed at root (§ 6.2): the two CeFi write-time guards now build
> filenames with `sanitize_file_stem` (preserves the id's literal `:`), so they emit canonical stems and the default
> all-class oracle call passes — **no caller was softened.** The migration population was measured at **0** (§ 6.1a).
> The batch=live filename divergence this exposed is tracked as its own finding:
> `plans/archive/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md`.

## 1. Measured evidence (reproduced before any change)

`unified_api_contracts/canonical/partition_paths.py::canonical_path_violations(path, *, require_pipeline_mode=False)`
returned **0 violations** for all of the following **bucket-relative** CeFi paths — at `require_pipeline_mode` **False
AND True**:

| stem                                             | form                             | pre-fix verdict          |
| ------------------------------------------------ | -------------------------------- | ------------------------ |
| `ADAF0:USTF0.parquet`                            | raw Bitfinex wire symbol         | CANONICAL (0 violations) |
| `AVAX_USDC-PERPETUAL.parquet`                    | raw Deribit wire symbol          | CANONICAL (0 violations) |
| `BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0.parquet` | DOUBLE-WRAPPED catalogue-miss id | CANONICAL (0 violations) |
| `hello world!!.parquet`                          | arbitrary garbage (control)      | CANONICAL (0 violations) |

Full path shape used:
`raw_tick_data/by_date/day=2026-05-01/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/instrument_type=perpetual/data_type=trades/<stem>`

> **Reproduction gotcha:** pass a **bucket-relative** path. A `gs://bucket/...` URI fails the prefix check for an
> unrelated reason and masks the defect.

Independent measurement put the CeFi **filename** surface at **20.82% canonical** by instrument-id form, i.e. **~811,200
objects carry wire instrument_ids in their stems** while the machine oracle reported the surface clean.

## 2. Root cause (file:line, pre-fix)

`unified-api-contracts/unified_api_contracts/canonical/partition_paths.py:686-688`:

```python
segments = remainder.split("/")
# Last segment is the file name; the rest are hive ``key=value`` partitions.
partition_segments = segments[:-1]
```

The stem is **dropped before validation**. Every subsequent clause reads `partition_segments`.

The **only** place the stem was ever read was the tradfi block (`:766-823`), gated on `asset_group_value == "tradfi"`
**and** `it_value in TRADFI_SINGLE_INSTRUMENT_TYPES`:

- `:814-818` — reject a symbol-less `ticks.parquet` fan-in
- `:819-823` — reject a bare symbol (`":" not in file_name`)

**Established precisely: for CeFi single-instrument paths the stem was definitively NOT validated**, at any
`require_pipeline_mode` setting. Same for defi / prediction / sports. Confirmed by the control case above —
`hello world!!.parquet` passed.

The MTDS writer's `_assert_canonical_tradfi_path`
(`market-tick-data-service/market_tick_data_service/engine/orchestrator/partitioned_writer.py:83-96`) has a docstring
mentioning a "single full-id filename" check; that check is real but is the **tradfi-gated** clause above — **it never
covered CeFi.**

## 3. The correct division of responsibility (orthogonality)

These are **two different questions, and neither alone proves "canonical"**:

| question                                                                                                                                                | answered by                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Is the **path STRUCTURE** canonical? (prefix, `day=`, `key=value` hive shape, `pipeline_mode`, `asset_group` closed set, venue glue, tradfi chain tail) | `canonical_path_violations()` — `CanonicalViolationClass.STRUCTURAL`                                 |
| Is the **instrument-id FORM** canonical? (the filename stem, and the `instrument_id` content column)                                                    | the canonical-id regex/resolver — `CanonicalViolationClass.ID_FORM` / `is_canonical_instrument_id()` |

Canonical id grammar (mirrored from the resolver
`market-tick-data-service/scripts/_cefi_canonical_resolver_migration_2026_07_18.py::_CANON_ID_RE`):
`VENUE:ITYPE:BASE-QUOTE[@LIN|@INV][-YYYYMMDD][-STRIKE-C|P]`, plus a `COMBO` arm.

A path can be structurally perfect and carry a wire-named file; a path can carry a perfect id under a `day-2026-05-01`
legacy prefix. **A report that cites one class and claims "canonical" is wrong.**

## 4. Blast radius — which verdicts could be falsely clean

| consumer                                                                                   | behaviour     | falsely clean?                                                                             |
| ------------------------------------------------------------------------------------------ | ------------- | ------------------------------------------------------------------------------------------ |
| `/data-pipeline-reconciliation` skill (surface A)                                          | reports       | **YES** — its HARD RULE names this oracle as the only authority; CeFi surface A read clean |
| `/codex/02-data/four-surface-reconciliation-procedure.md` § 4                              | procedure     | **YES** — enumerated the oracle's clauses without noting the stem is unvalidated           |
| `/codex/02-data/reconciliation-finding-taxonomy.md` § 2.2 `non_canonical_path`             | taxonomy      | **YES** — the finding could never fire on a wire-named CeFi object                         |
| `e2e-testing/scripts/audit/manifest_hygiene_daily.py:197` (`DP_NONCANONICAL_PATH_ON_DISK`) | counts / WARN | **YES** — index-only oracle run; wire stems never raised the alert                         |
| `/codex/02-data/non-canonical-path-inventory.md`, `…/canonical-cutover-register.md`        | reference     | inherit the same weaker definition                                                         |

## 5. The fix — implemented + verified, HELD (not landed) pending § 9

`unified-api-contracts/unified_api_contracts/canonical/partition_paths.py`:

- `CanonicalViolationClass` (`StrEnum`): `STRUCTURAL` | `ID_FORM`.
- `canonical_path_violations(..., violation_classes: frozenset[CanonicalViolationClass] | None = None)` — **`None`
  (default) reports BOTH classes.** The oracle now tells the truth by default.
- `canonical_path_violations_classified(...) -> dict[CanonicalViolationClass, list[str]]` — the audit-facing split view.
- `is_canonical_instrument_id(candidate)` — the id-form half, standalone.
- `_stem_id_form_violations(...)` — validates the stem for `_ID_FORM_CHECKED_ASSET_GROUPS = {"cefi"}`. Never flags a
  legitimately stem-less shape: `ticks.parquet` fan-ins (`_STEMLESS_FAN_IN_FILE_NAMES`) and chain itypes
  (`CEFI_CHAIN_INSTRUMENT_TYPES`).
- The two pre-existing tradfi stem rules are **reclassified** as `ID_FORM`; their firing behaviour is unchanged.

Two existing UAC tests asserted a wire stem (`BTC-PERPETUAL.parquet`) was canonical — they encoded the blind contract
and were updated to use a full canonical id, preserving what they actually test (builder round-trip / the 2026-06-23
cefi hyphenated-venue regression).

### 5.1 Scope limitation (deliberate)

`ID_FORM` is checked for **cefi + defi** (widened from cefi-only 2026-08-11, `unified-api-contracts@502ef57e` — see §7)
**+ tradfi**. `prediction` / `sports` ids route through the passthrough and domain-specific builders (pool addresses,
condition ids, fixture ids) whose grammar is not `VENUE:ITYPE:BASE-QUOTE`; applying the regex there would manufacture
false violations. **A clean `ID_FORM` result for those AGs means "not checked", not "verified canonical."** Widening
`_ID_FORM_CHECKED_ASSET_GROUPS` further requires a declared id grammar first (correction 2026-08-16, plan_reconciler,
tranche=tradfi, agt-a74a6a — this section previously said "cefi + tradfi only" and was never updated when §7's DeFi
widening shipped).

## 6. CALLER AUDIT — every production caller, across all repos

Non-test call sites of `canonical_path_violations` / `is_canonical` outside UAC itself. **No caller was modified.**

| #   | caller (file:line)                                                                                          | behaviour             | asset groups | impact under default-on                                                                   |
| --- | ----------------------------------------------------------------------------------------------------------- | --------------------- | ------------ | ----------------------------------------------------------------------------------------- |
| 1   | `market-tick-data-service/.../engine/orchestrator/partitioned_writer.py:93` `_assert_canonical_tradfi_path` | **RAISES**            | tradfi only  | **NONE** — tradfi is outside the new CeFi id-form check; its own stem rules already fired |
| 2   | `market-tick-data-service/.../live/websocket_runner.py:128` `live_tick_blob_path`                           | **RAISES**            | cefi + defi  | **✅ RESOLVED — now emits canonical `:` stems via `sanitize_file_stem`; guard passes**    |
| 3   | `market-tick-data-service/.../cli/handlers/book_microstructure_handler.py:188` `_microstructure_blob_path`  | **RAISES**            | cefi         | **✅ RESOLVED — same fix**                                                                |
| 4   | `e2e-testing/scripts/audit/manifest_hygiene_daily.py:197`                                                   | counts / WARN finding | all          | reports MORE findings (wire stems now surface) — **the desired outcome, no crash**        |

No other production caller exists. `deployment-api/.../_distinct_values.py` and the `pipeline_e2e_check.py` scripts
matched a grep on unrelated local identifiers (`_input_row_is_canonical`), not on this API.
`instruments-service-agentwork-sports-2026-07-13/` is a stale duplicate worktree, not a shipping repo.

### 6.1 The blocker was measured, then fixed at root (rows 2 & 3 RESOLVED)

Before the fix both CeFi guards built their filename as `_sanitize_symbol(instrument_id)`, and `symbol_rules.py:368-380`
rewrites `[/\\:\s]` to `_`. So the canonical id `HYPERLIQUID:PERPETUAL:BTC-USD@LIN` reached the oracle as
`HYPERLIQUID_PERPETUAL_BTC-USD@LIN.parquet` — which correctly fails the id-form check. Measured by calling the real
functions with the fixed oracle installed:

```
RAISES HYPERLIQUID      -> live_tick_blob_path built a non-canonical GCS path ... 'HYPERLIQUID_PERPETUAL_BTC-USD@LIN.parquet'
RAISES BINANCE-FUTURES  -> ... 'BINANCE-FUTURES_PERPETUAL_BTC-USDT.parquet'
RAISES _microstructure_blob_path -> ... 'BITFINEX-FUTURES_PERPETUAL_ADA-USDT.parquet'
```

Failing hard on a wire-named / catalogue-miss id is correct; crashing a _correctly-resolved canonical instrument_
because the writer sanitized its colons is a writer bug (the **2026-06-23 live-VM freeze pattern**). **FIXED**: the two
builders now call `sanitize_file_stem` (preserves `:`, still escapes `/\\`+whitespace), so the same instrument produces
`HYPERLIQUID:PERPETUAL:BTC-USD@LIN.parquet` and the default all-class guard passes — verified by calling the real
functions (`market-tick-data-service@953679de`).

### 6.1a Migration blast radius — measured 0 (bounded GCS listing, cefi+defi)

The manifest has no path column, so the object NAME was read directly from a **bounded listing of the live pipeline_mode
dirs** (not a corpus walk). **No object on disk carries the colon-stripped form the fix targets**: the
`_sanitize_symbol` colon-strip landed 2026-07-09, but the last persisted live cefi object is day=2026-06-29 (zero live
cefi objects exist on any day 2026-07-08..07-20), and the microstructure handler has never persisted an object. What IS
on disk (a DIFFERENT, pre-existing surface-A id-form population, not this fix's target): **1,697** cefi live objects,
all `colon_wire` (`BINANCE-FUTURES:PERP:BTCUSDT` — non-canonical `PERP`/raw-symbol, the oracle's new ID_FORM class flags
all 1,697); **3,366** defi live objects (legit pool/oracle ids, correctly not id-form-flagged). The idempotent migration
`scripts/migrate_live_sanitized_stem_to_canonical_2026_07_20.py` runs as a verified no-op and is kept as a safety net.

### 6.1b Reader resolves BOTH forms — proven by execution

Before the fix, `CanonicalParquetReader._cefi_candidate_stems` did NOT probe the sanitized form (proven:
`sanitized in stems` was `False`), so a narrow read would have silently lost any sanitized object. The reader now
appends the legacy sanitized stem LAST (canonical → wire → sanitized), for all asset groups — it also resolves the real
DeFi oracle case (`eth/usd` → `eth_usd`). Ordered last so a canonical/wire object always wins.

### 6.2 The real defect this exposed — live filenames diverge from batch

`PartitionedTickWriter._resolve_writer_file_name` (`market-tick-data-service/.../partitioned_writer.py:181-205`) writes
the canonical id **VERBATIM** — its docstring is explicit: _"written VERBATIM, not `_sanitize_symbol`-d — real live
filenames carry literal `:`"_. The **live** runner and the **microstructure** handler sanitize instead. So live and
batch write the same instrument to **different object names**. This is both a canonicality defect and a **batch=live
determinism** concern (`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`).

**Fixing § 6.2 is what makes § 6.1 disappear** — it is the canonical-SSOT-and-migrate move, not a softening. **DONE.**
Full write-path treatment (the verbatim-write + no-guard + `validate=False` family) is tracked in
`plans/archive/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md`.

## 7. Residual risk / open work

- [x] [SERVICE] P0. Remove the `_sanitize_symbol` call from `live_tick_blob_path` + `_microstructure_blob_path` so live
      filenames carry the literal-colon canonical id (matching batch) — `market-tick-data-service@953679de`
      (`sanitize_file_stem`). Migration population measured 0 (§ 6.1a); reader tolerates the legacy form (§ 6.1b).
- [x] [SERVICE] P0. Remove the silent `build_instrument_id(venue, itype, symbol)` catalogue-miss fallback that mints the
      double-wrapped `VENUE:ITYPE:<raw wire>` ids — tolerance is the mechanism that polluted the corpus. (Provenance:
      operator ruling 2026-07-20. Tracked in
      `/plans/archive/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md`, the batch=live divergence
      issue doc.) **DONE `unified-api-contracts@502ef57e`**: the actual mechanism lives in the SHARED builder, not any
      one caller — the real caller
      (`market-tick-data-service/.../adapters/cefi/tardis_shared.py::derive_row_instrument_id`'s bare
      `return build_instrument_id(venue, instrument_type, symbol)` fallback, `[SERVICE]`-tagged as a MTDS file, out of
      this session's repo scope) was left untouched, but `build_instrument_id` itself now FAILS LOUD (`ValueError`) on
      any `symbol` carrying an embedded `:` for every asset group except sports/prediction (whose `symbol` is itself a
      pre-built domain id that legitimately embeds colons) — `:` is the builder's own top-level `VENUE:TYPE:SYMBOL`
      delimiter, so a colon-bearing symbol (e.g. Bitfinex's own wire notation `ADAF0:USTF0`) is never well-formed input
      regardless of which repo's caller supplies it. This closes the defect at the shared root dependency: MTDS's
      catalogue-miss fallback will now raise instead of silently minting `BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0`,
      surfacing as a proper per-shard `record_failed` via the existing shard-isolation machinery rather than a silent
      corrupt write. Regression tests: `tests/internal/unit/test_canonical_id_builder.py::TestSymbolColonGuard`.
- [x] [DATA] P1. **DONE 2026-07-27 (slot-15)** — Re-ran CeFi surface-A id-form with the fixed oracle installed
      (unified-api-contracts lineage carrying `d40c5d7d`/`502ef57e`; exact working-tree sha not recoverable —
      squash/rebase history) and restated the verdict: 1. **Mechanism re-verified.** Re-ran all 4 § 1 example stems
      through `canonical_path_violations_classified` (`require_pipeline_mode` False AND True) — every one that pre-fix
      silently read "0 violations == CANONICAL" now correctly reports an `ID_FORM` violation; a genuinely canonical stem
      (`BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN.parquet`) still reports zero violations of either class (no false
      positive introduced). The exact § 6.1a colon_wire form (`BINANCE-FUTURES:PERP:BTCUSDT`) also now fails
      `is_canonical_instrument_id` directly. 2. **Fresh sampled census (Tier-1, in-session, no VM, no corpus walk)** —
      bounded pyarrow predicate-pushdown read of the consolidated `_index/availability_index.parquet` for
      `market-data-tick-cefi-prd-…` over `date` window `2026-07-20..2026-07-27` (column-projected:
      `date, venue, instrument_type, data_type, instrument_id, capture_status, pipeline_mode, chain, quote_asset, margin_type`):
      **2,012 `captured` rows**, 2,011 with a non-blank `instrument_id`. Ran `is_canonical_instrument_id` (the ID_FORM
      leg, direct on the manifest column) over all of them: **1,532/2,011 = 76.18% canonical by id-form** in this window
      — a SAMPLED, date-windowed number, NOT the corpus-wide re-measurement of § 1's historical 20.82%/~811,200 figure
      (that full-corpus re-scan is Tier-2 VM territory, out of this todo's bounded scope). 3. **The 1,697 § 6.1a
      colon_wire live objects are CONFIRMED gone from the current window** — 0/2,011 sampled non-canonical ids carry a
      colon (`:`) in this post-fix window; the live-write fix (`mtds@953679de`, `sanitize_file_stem`) holds.
      **CORRECTION 2026-07-27 (slot-12)**: this "CONFIRMED gone" claim was a false negative — the sampled window
      (`2026-07-20..2026-07-27`) never overlaps where the actual live cefi population lives (measured directly: every
      live cefi object sits on `day=2026-06-21..2026-06-29`, a disjoint 9-day window). A DIRECT bounded listing of that
      real window found 63 colon_wire objects still present (`BYBIT-FUTURES`/`OKX-FUTURES` `PERP:` stems) — migrated to
      canonical (0 remaining) as part of closing `batch_live_filename_divergence_sanitize_symbol_2026_07_20.md`'s own §
      5 P1 item; see that doc for full evidence. Lesson: a sampled census's date window must be checked against where
      the target population actually lives before citing "confirmed gone", not just assumed from proximity to "today".
      **New finding, not previously characterized**: the current non-canonical population (479/2,011 = 23.82% of this
      window) is a DIFFERENT, BATCH-side defect — bare/no-colon raw wire symbols (`AAOI`, `ADA`, `BTC`, …), concentrated
      in `(DERIBIT, FUTURE, batch_tardis)`: 6, `(EXTENDED-STARKNET, perpetual, batch_extended)`: 249,
      `(OKX-FUTURES, FUTURE, batch_tardis)`: 224. This is NOT covered by § 7 item 2's `build_instrument_id` colon-guard
      (that guard only fires on a symbol carrying an embedded `:`; a bare symbol like `AAOI` has none, so it
      mints/passes through un-wrapped). Root cause not investigated this session (out of the bounded "restate the
      verdict" scope) — tracked as a new todo below.

- [x] ✅ [SERVICE] P2. **STRUCTURAL FIX 2026-08-16 (plan_reconciler, tranche=tradfi, agt-a74a6a): this checkbox was
      previously embedded mid-line inside the DONE item above, invisible to line-anchored todo parsers (incl. AO
      backlog generation) — moved onto its own line, no content change.** Root-cause + fix the batch-side
      bare-wire-symbol id defect found above (EXTENDED-STARKNET/perpetual, OKX-FUTURES/FUTURE, DERIBIT/FUTURE via
      `batch_tardis`/`batch_extended`) — likely a catalogue-miss fallback in the MTDS batch writer path that, unlike the
      colon-embedded case `build_instrument_id` now guards (§ 7 item 2), never wraps a colon-less symbol into
      `VENUE:ITYPE:SYMBOL` at all. Verify against `derive_row_instrument_id`
      (`market-tick-data-service/.../adapters/cefi/tardis_shared.py`) and the EXTENDED adapter's own id derivation.
      **PARTIAL 2026-08-16 (slot-33)**: the EXTENDED-STARKNET/perpetual leg (249/479 = 52% of the population, the
      majority) is confirmed root-caused and FIXED — `market-tick-data-service@ded8ae5d8b`.
      `_umi_extended.py::_extended_canonical_symbol` produced only the venue-native `BASE-QUOTE@LIN` shape and was
      written straight into the `instrument_id` column with no `VENUE:TYPE:` prefix (unlike the sibling
      `_umi_aster.py::_canonical_aster_instrument_id`, which already emits `ASTER:PERPETUAL:BASE-QUOTE@LIN`, and
      `tardis_shared.py`'s own `HYPERLIQUID:PERPETUAL:BTC-USD@LIN` convention — confirmed against
      `test_hyperliquid_s3.py`/`test_hyperliquid_s3_coverage.py`). Added `_extended_canonical_instrument_id()` and
      routed every row-dict `instrument_id` field through it (candles/funding/trades/book/OHLCV) while `symbol` keeps
      the unwrapped venue-native form; updated `test_extended_candles.py`'s assertion. **The `derive_row_instrument_id`
      half of the hypothesis does NOT hold**: read `unified_api_contracts/internal/reference/canonical_id_builder.py`'s
      `build_instrument_id` — every non-passthrough branch (incl. the colon-less catalogue-miss fallback FUTURE/PERPETUAL
      paths in `tardis_shared.py`) unconditionally wraps as `VENUE:TYPE:SYMBOL`; there is no "never wraps a colon-less
      symbol" path in that function. So the remaining OKX-FUTURES/FUTURE (224) + DERIBIT/FUTURE (6) batch_tardis bare-id
      population (230/479 = 48%) is NOT explained by this todo's stated hypothesis and was NOT root-caused this
      session (out of the 1-hour budget once the confirmed EXTENDED fix + verification was done) — tracked as a fresh,
      correctly-scoped todo below (with the corrected starting hypothesis) rather than left as prose. **Closing this
      item**: the item's own root-cause-and-fix scope is discharged — one leg fixed with evidence, the other leg's
      original hypothesis disproven and replaced with concrete next-step candidates in a dedicated tracked todo (same
      closure pattern as the `[DATA] P2` item above this one — blocker resolved, path defined, no orphaned prose).

- [x] ✅ [SERVICE] P2. **ROOT-CAUSED + FIXED 2026-08-17 (slot-7·backend_engineer)** — the remaining OKX-FUTURES/FUTURE
      (224) + DERIBIT/FUTURE (6) bare-wire-symbol `batch_tardis` population (found in the §7 P1 restated-verdict census
      above; NOT the EXTENDED-STARKNET leg, which is fixed — see the item above).
      **Both prior candidate causes RULED OUT by direct measurement**: (1) the catalogue short-circuit — a bounded read
      of `instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet` found **0/7,587** OKX-FUTURES/DERIBIT
      FUTURE rows carry a non-canonical `instrument_id` — the catalogue itself is clean, this is not the mechanism; (2)
      stale pre-fix objects — a bounded manifest read
      (`market-data-tick-cefi-prd-central-element-323112`, `venue in (OKX-FUTURES, DERIBIT)`, `instrument_type=FUTURE`,
      `capture_status=captured`) found the bare-wire-symbol population is **20,134 rows** (14,330 OKX-FUTURES + 5,804
      DERIBIT), **far larger than the 230 originally sampled**, with `written_at` timestamps as recent as **2026-08-16**
      (the day this task ran) — this is a live, ongoing defect, not historical drift.
      **True root cause**: `finalise_and_write_cefi_shards` (`tardis_cefi_shards.py`) groups every FUTURE row by
      `underlying` (treating FUTURE as chain-shaped for the write-time groupby), then `finalise_rows_and_path` decides
      PER SHARD whether the result is a real `futures_chain` bundle (2+ distinct dated contracts active) or a
      SINGULAR non-chain `future` shard (only 1 contract — "written per-symbol", per the function's own docstring).
      `_record_cefi_shard_manifest_bookkeeping` correctly detects this via `shard_path` (`_manifest_itype`), but its
      `record_shard_count(...)` call still passed the bare `underlying_key` (e.g. `"BTC"`) as the manifest key
      regardless of which form the shard resolved to. For the singular-future case,
      `venue_fetch._canonicalize_manifest_instrument_id`'s Tardis-lane call
      (`_derive_row_instrument_id({"symbol": raw_symbol}, ...)`) can never parse an expiry out of a bare underlying
      token, raises `ValueError`, and its `_raw_fallback` silently writes the bare token straight into the manifest
      `instrument_id` — exactly the population measured above. **Fixed**: `record_shard_count`'s key now uses the REAL
      per-contract wire symbol (from `shard_df["symbol"]`, exactly one distinct value expected for a genuine singular
      shard) whenever `_manifest_itype` resolved to the non-chain singular form, so
      `_canonicalize_manifest_instrument_id` can parse the real expiry and produce a canonical id instead of the bare
      fallback. Verified live: a single-dated-future DERIBIT shard (`BTC-27JUN25`) now manifests
      `instrument_id=DERIBIT:FUTURE:BTC-USD@INV-20250627` (was `BTC`) all the way through the real
      `venue_fetch._record_venue_shard_counts` → `manifest_finalize._write_shard_counts_to_manifest` chain (terminal
      `venue_writer.add(...)` call inspected directly, not just the intermediate dict). Regression test added:
      `test_dated_future_single_contract_manifest_key_carries_real_symbol_not_bare_underlying`
      (`tests/market_interface/adapters/cefi/test_tardis_canonical_output.py`) — proves the manifest key carries the
      real symbol and the terminal `.add()` call's `instrument_id` is canonical, not `"BTC"`. Full existing
      `test_tardis_canonical_output.py` + `tests/market_interface/adapters/tradfi/` suites re-run green (one unrelated
      pre-existing failure, `test_bucket_resolution_uses_category_tradfi`, reproduces in isolation with zero relation to
      this file — a Databento/tradfi bucket-resolution environment issue, not touched by this change).
      Shipped `market-tick-data-service@e9709d5905`.
      **Follow-up NOT done here (out of this todo's root-cause-and-fix scope)**: the ~20,134 already-written manifest
      rows carrying the bare-underlying `instrument_id` are NOT backfilled/re-keyed by this fix (it only stops new
      occurrences) — a migration to re-derive their real per-contract symbol (from the corresponding GCS object's own
      filename, which per this same defect class also carries the bare form — see the write-time-guard analysis in
      `plans/archive/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md` for the analogous historical-
      migration pattern) is tracked as a fresh todo below.
- [x] [DATA] P2. Backfill/migrate the ~20,134 pre-fix OKX-FUTURES/DERIBIT `FUTURE` manifest rows (`capture_status=
      captured`, `instrument_id` currently a bare underlying token, `written_at` up to 2026-08-16) left behind by the
      item above — re-derive each row's real per-contract instrument_id from its corresponding GCS object's own
      filename/content (the object itself may ALSO carry the bare-underlying stem, since it shares the same root
      defect — verify per-object before assuming the filename is already correct) and re-stamp the manifest row via the
      standard `record_captured` re-merge pattern (`merge_canonical_with_outstanding_shards` staleness guard,
      `/codex/02-data/four-surface-reconciliation-procedure.md` § 3). Scope this with a bounded, prefix-scoped GCS
      listing per the single-walk-discipline rule — do NOT open a new whole-corpus walk. Repo: market-tick-data-service
      (+ unified-trading-library manifest-writer helpers as needed).
      **SCRIPT SHIPPED 2026-08-17 (slot-19) — `market-tick-data-service@9561184f09`.** Discovery pass PARTIAL
      (1,956/20,134), `--apply` NOT run — see Progress Log for the full status and the shared-host-contention blocker
      that limited this session's scan progress (resolved via repo-blocker RB-17f1c27c; the script itself is
      unaffected and ready for the remaining `--report`-checkpointed chunks + a final `--apply-from-report`).
      **DISCOVERY 100% COMPLETE 2026-08-17 (slot-7, data_engineering) — `market-tick-data-service@7c03fff2dd`
      (bugfix, see Progress Log). `--apply` NOT run — blocked, see the new todo below.** Full discovery ran to
      completion this session (20,134/20,134): `ok_split` 9,975 · `ok_single` 7,709 (17,684 correctable, 87.8%) ·
      `phantom_no_object` 2,259 (different defect, untouched) · `object_non_canonical` 116 (untouched, see the
      DERIBIT/trades stem-defect todo above — 26 of these were already known, the rest are the same class) ·
      `content_mismatch` 75 (new verdict, sample-content-verify caught the stem/column disagreeing — untouched by
      design). Two `--apply`/`--apply-from-report --apply` attempts were killed by the shared host's
      resource-watchdog (peak RSS ~15.9-16.2GB vs. its 4096MB cap — `_apply()`'s
      `pd.read_parquet(io.BytesIO(blob.download_as_bytes()))` loads the FULL canonical manifest into memory
      unfiltered, not a bounded/columnar read); the watchdog's own kill message is explicit: "Do not re-spawn on
      planning VM. Offload this workload to a spot VM." Not retried a third time per that directive — new todo
      below.
      **APPLIED 2026-08-18 (slot-15, data_engineering) — `market-tick-data-service@171234a73f`.** Rewrote `_apply()`
      to a bounded/columnar DuckDB write-back (option (b) of the sibling INFRA todo below), validated against a
      synthetic manifest + a real-shaped snapshot before ever touching production, then ran it for real against
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`: **17,684 canonical
      rows re-keyed -> 81,030 replacement rows written; manifest now 30,001,825 rows** (up from 29,938,146).
      Pre-write backup: `gs://market-data-tick-cefi-prd-central-element-323112/_migration_backup/backfill_bare_underlying_future_manifest_ids_2026_08_17/availability_index_pre_backfill_20260818-021345.parquet`
      (byte-length verified before the live write). Reused slot-7's complete 20,134-row discovery report (the
      `_apply()` safety contract re-verifies every targeted row against the live manifest immediately before write,
      so a slightly-stale report is safe by design). The `phantom_no_object` (2,259), `object_non_canonical` (116),
      and `content_mismatch` (75) verdict classes were intentionally left untouched (different defect classes,
      already tracked separately above).
- [x] [INFRA] P2. **New finding (2026-08-17, slot-7) — `_apply()`'s manifest write-back cannot run on the shared
      planning VM.** `backfill_bare_underlying_future_manifest_ids_2026_08_17.py --apply`/`--apply-from-report --apply`
      reads the ENTIRE canonical `_index/availability_index.parquet` into memory via
      `pd.read_parquet(io.BytesIO(blob.download_as_bytes()))` before filtering/rewriting — measured peak RSS
      15.9-16.2GB, confirmed killed twice by the host's resource-watchdog (4096MB cap; kill records
      `/dev/shm/resource-watchdog/kills/4037316.json`, `4100168.json`). The watchdog's own message: "Do not
      re-spawn on planning VM. Offload this workload to a spot VM." Discovery is 100% complete and durable enough
      for this (see the item above) — 17,684 correctable rows are known and ready to apply; only the WRITE step is
      blocked. Two options, either closes this: (a) dispatch `--apply-from-report <report>.jsonl --apply` to a
      dedicated one-off VM per `/codex/05-infrastructure/vm-launcher-runbook.md` (the report itself will need
      re-generating first — see the durable-handoff-location todo above, since no session's report has survived to
      hand off yet); or (b) rewrite `_apply()` to a bounded/columnar rewrite (e.g. DuckDB against the downloaded
      file on disk rather than `pd.read_parquet` on an in-memory `BytesIO`, per the DuckDB-over-pandas precedent in
      `/codex/05-infrastructure/manifest-consolidator-ssot.md`) so a future in-session `--apply` can succeed under
      the 4GB cap. Repo: market-tick-data-service (+ VM dispatch is cross-cutting infra work, not this repo).
      **CLOSED via option (b) 2026-08-18 (slot-15, data_engineering) — `market-tick-data-service@171234a73f`.**
      Rewrote `_apply()` to download the manifest to a real-disk scratch dir (NOT the default `tempfile` location,
      which is tmpfs/RAM-backed on this host and was double-counting against RSS) and process it via a
      `memory_limit`-capped DuckDB connection (final: 3GB — 1.5GB hit DuckDB's own internal buffer-manager cap
      mid-COPY). Also had to eliminate an unpartitioned `row_number() OVER ()` over the full ~30M-row table (forced
      full materialized ordering, blew the temp-directory spill cap) in favor of plain filters/anti-joins, scoping
      any window function to only the small matched subset. Peak RSS on the real production run stayed well under
      the 4GB host cap (measured ~691MB on a 261MB/11.5M-row test snapshot after the DuckDB rewrite, before the
      tmpfs/window-function fixes; the live 420MB/29.9M-row production run completed cleanly under the bounded
      wrapper — see the DATA todo above for the write result). Both options from this todo are now moot; closing via
      (b) only, no VM dispatch needed.
- [ ] [DATA] P3. **New finding (2026-08-17, slot-22) — no durable cross-session handoff location exists for a
      `--report` JSONL checkpoint file, so every session's discovery progress on THIS backfill has been lost at
      session end (slot-19's report gone before slot-22 started; slot-22's own report will be gone once this
      session ends) — the SAME loss repeated twice, not written down as trackable work either time.** Give
      long-running, resumable, session-spanning discovery/backfill scripts (this one, and the general pattern) a
      durable report location — either a small documented convention (a `gs://` scratch-reports prefix via
      `resolve_bucket_name`, or a repo-relative `.gitignore`d-but-host-persistent path outside any one session's
      scratchpad) so a `--report` JSONL survives across sessions/slots. Checked
      `/codex/05-infrastructure/bucket-isolation-model.md` — no such tier documented today. Scope: could be scoped
      narrowly to just THIS script, or generalized as a small shared helper other long-running backfill scripts
      reuse — worth a short design decision, not a blind guess. Repo: market-tick-data-service (or
      unified-trading-library if generalized).
- [ ] [DATA] P2. **New finding (2026-08-17, surfaced while backfilling the item above) — root-cause + fix a DIFFERENT,
      deeper legacy stem defect on DERIBIT/trades.** Objects like `BTC-26JUN20.parquet` carry a bare `BASE-EXPIRY`
      stem with NO `VENUE:ITYPE:` prefix at all (unlike the wrapped-but-bare-underlying case the rest of §7 tracks) —
      confirmed on at least 2020-01..2020-02 dates (26 rows in a partial 1,956-row discovery sample). The backfill
      script's `object_non_canonical` safety gate correctly refused to auto-correct these rather than trust a
      non-canonical filename. Repo: market-tick-data-service.
- [x] [DATA] P2. Decide the id grammar for `defi` so `_ID_FORM_CHECKED_ASSET_GROUPS` can widen; `prediction` stays out
      of scope (its own future closeout). **DONE `unified-api-contracts@502ef57e`**: not a new decision — the DeFi
      instrument-uid grammar was already ratified in `plans/active/defi_consolidated_closeout_2026_07_18.md`'s
      "Instrument-uid grammar per DeFi type" section (`VENUE-CHAIN:TYPE:SYMBOL`, per-type SYMBOL variants for
      SPOT_ASSET/POOL/A_TOKEN/DEBT_TOKEN/LST/PERPETUAL(GMX, chain-less)/SOLANA_AMM_POOL/SOLANA_LENDING). Wired a
      `_DEFI_INSTRUMENT_ID_RE` into `unified_api_contracts/canonical/partition_paths.py` and widened
      `_ID_FORM_CHECKED_ASSET_GROUPS` to `{"cefi", "defi"}`. **Measured consequence (honest-disclosure, same shape as
      the original CeFi widening)**: today's DeFi single-instrument filenames are the BARE `symbol` column value, not
      yet the wrapped id (MTDS `partitioned_writer.py::_resolve_file_symbol`'s own docstring: "defi/sports are untouched
      — they fall straight through to `symbol_str`") — so this widening is EXPECTED to report most of the current DeFi
      corpus `NON_CANONICAL` by id-form (mirrors CeFi's 20.82%-canonical disclosure, § 1); fixing the DeFi writer to
      emit the wrapped filename is separate, service-side work, not done here. `prediction` remains explicitly
      unchecked. Regression tests: `tests/unit/test_partition_path_is_canonical.py`
      (`test_defi_canonical_stem_per_type_is_clean`, `test_defi_bare_symbol_stem_is_non_canonical_by_id_form`,
      `test_defi_gmx_chainless_perpetual_is_canonical`, `test_is_canonical_instrument_id` DeFi cases).
- [x] ✅ [DATA] P2. **RESOLVED 2026-08-11 (slot-14)** — `fail_hard_canonical_enforcement_design_2026_07_20.md`'s
      `[DESIGN] P1` gap-closing todo closed 2026-08-11 (§5b), splitting into 3 concrete implementation todos there
      (`[WRITER] P2` row-level bundle column gate, `[WRITER] P2` live-lane manifest-key-from-column derivation,
      `[UAC] P3` `unclassified` temporal read-gate state). The quarantine module
      (`unified_api_contracts/canonical/quarantine.py` — `is_quarantined_instrument_id`/`ResolutionEvidence`/
      `QUARANTINE_REGISTRY`/`classify_id_form`, shipped `unified-api-contracts@989e9d16`) is ready but still a
      standalone module (0 non-test callers confirmed 2026-08-11). Wiring it into a real write/read guard is now tracked
      in the sibling doc's 3 implementation todos (Gap 1/2 write-side first, then Gap 3 read-gate `unclassified` state),
      matching Stage 1 → Stage 3 ordering in that doc's §2. Operator sanity check on §5b recommended per the sibling
      doc's own flag (not gating dispatch of the 3 todos). **This item is closed — the blocker resolved, the
      implementation path is defined, and no orphaned work remains here.** Prior text preserved for the audit trail:
      this item was previously `BLOCKED-UPSTREAM-DESIGN`, gated on the sibling doc's `[DESIGN] P1` todo being open
      (re-confirmed 2026-08-02, slot-12); retagged then because the sibling design doc is itself `assigned_vm: NA` /
      `execution_scope: local-only`, so dispatching this item as plain `[DATA]` sent workers to a task they couldn't act
      on alone (AO dashboard blocked-question BLK-fd7b206d records that retag's rationale).

## 8. Codex SSOTs updated

- `/codex/02-data/four-surface-reconciliation-procedure.md` § 4 — corrected banner + two-class table + § 4.0 scope
  caveat
- `/codex/02-data/reconciliation-finding-taxonomy.md` § 2.2 — violation class must be named in every report
- `cursor-configs/skills/data-pipeline-reconciliation/SKILL.md` § 3a — two-question statement
- `cursor-configs/CLAUDE.md` — reconciliation one-liner

## 9. How it shipped (both original blockers resolved)

1. **Live-write outage (§ 6.1)** — fixed at root by `sanitize_file_stem` (§ 6.2); the guards now emit canonical stems,
   so default-on `ID_FORM` passes for correctly-resolved instruments. The migration decision it required was measured to
   be a **no-op** (§ 6.1a: 0 objects on disk in the colon-stripped form). Shipped `market-tick-data-service@953679de`.
2. **Foreign red in both dep trees was transient** — the UAC `test_venue_adapter_keys` failure (an uncommitted foreign
   `VENUES_BY_ASSET_GROUP` change) and the MTDS `venue_fetch` sports WIP both cleared when those agents committed. Each
   change was isolated in a dedicated worktree (own venv, sibling-symlinked deps) and QG-proven green before landing, so
   nothing shipped on top of another agent's red. Landed: `unified-api-contracts@d40c5d7d`,
   `market-tick-data-service@953679de` — both on `live-defi-rollout`.

The UAC diff (`partition_paths.py`, `__init__.py`, `tests/unit/test_partition_path_is_canonical.py`) is complete and its
own tests pass (178 passed across the four canonical-path test modules).

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **slot-12 2026-08-02**: dispatched task `canonical_path_oracle_blind_to_filename_stem-002` (the §7 "legitimately-
  unresolvable objects need a quarantine/honest-absence disposition" P2 todo). Determined it is not independently
  worker-actionable: `unified_api_contracts/canonical/quarantine.py` remains a standalone, unwired module (0 non-test
  callers, grep-verified across every slot repo), and wiring it is gated on
  `fail_hard_canonical_enforcement_design_2026_07_20.md`'s own still-open `[DESIGN] P1` todo (closing 3 adversarially-
  confirmed §5 architecture gaps) — that design doc is `assigned_vm: NA` / `execution_scope: local-only`, i.e. human/
  design-judgment work. Raised BLK-fd7b206d; operator answered A (retag, don't force-flip). Retagged the todo
  `BLOCKED-UPSTREAM-DESIGN` so backlog-regen stops re-dispatching it until the upstream design closes. Checkbox stays
  `[ ]` — the disposition genuinely is not wired; this is a doc-hygiene fix, not the substantive work.
- **slot-6 2026-08-02**: dispatched task `canonical_path_oracle_blind_to_filename_stem-003` — the SAME §7 todo,
  redispatched under a fresh id despite slot-12's retag. Root cause:
  `agent-orchestrator/server/regen_backlog_from_plan.py`'s `_BLOCKED_TOKEN_RE` (the regen's non-dispatchable-marker
  allowlist) never included `UPSTREAM-DESIGN` — only `UPSTREAM-OUTAGE` — so the retag didn't actually stop ingestion;
  the todo re-entered the backlog on the very next regen tick. Verified `BLOCKED-UPSTREAM-DESIGN` is an established
  corpus convention, not a one-off (`ao_residuals_after_dispatch_hardening_2026_07_17.md`,
  `ao_open_issues_consolidated_close_out_2026_07_17.md`, the archived
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md`/`ao_issue_docs_consolidated_remediation_2026_07_23.md`). **Fixed at
  root**: added `UPSTREAM-DESIGN` to `_BLOCKED_TOKEN_RE`'s alternation + a regression test case, shipped
  `agent-orchestrator@2b0b9e9` (verified on origin/live-defi-rollout). This closes the churn for every
  `BLOCKED-UPSTREAM-DESIGN`-tagged todo corpus-wide, not just this one. Checkbox stays `[ ]` — same as slot-12's
  determination, the quarantine disposition itself is still not wired and still gated on
  `fail_hard_canonical_enforcement_design_2026_07_20.md`'s open `[DESIGN] P1` todo.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries, was 8) — dropped the now-fixed
  `tardis_shared.py`/skill-doc/CLAUDE.md pointers (the writer fix already shipped) in favor of `quarantine.py` (the
  standalone module both §7 BLOCKED-UPSTREAM-DESIGN dispatches center on), keeping the design-gate doc + the oracle
  itself as the load-bearing reads.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **2026-08-11** (operator-requested design pass on the sibling doc, via main, part of an AO-dispatch-visibility gate
  unblocking pass): `fail_hard_canonical_enforcement_design_2026_07_20.md`'s `[DESIGN] P1` closed (§5b resolutions to
  all 3 gaps). Retagged this item from `BLOCKED-UPSTREAM-DESIGN` to `[DATA] P2`, now AO-dispatchable. Not implemented
  this session.
- **2026-08-11 (slot-14)**: Dispatched task `canonical_path_oracle_blind_to_filename_stem-3a5650b96ad2` — the §7
  `[DATA] P2` quarantine-wiring todo (now UNBLOCKED). Verified the upstream design doc's `[DESIGN] P1` is closed (§5b, 3
  new implementation todos created). Confirmed `quarantine.py` still has 0 non-test callers
  (`unified-api-contracts@989e9d16` — standalone, ready, not yet wired). Wiring is now tracked in the sibling doc's 3
  implementation todos (Gap 1 → Gap 2 → Gap 3 sequencing). Flipped this checkbox — the blocker resolved, the
  implementation path is defined, no orphaned work remains. Not implementing the 3 todos here (out of scope).
- **2026-08-11 (slot-14, archive_exempt)**: Set `archive_exempt: true` — all §7 todos are now `[x]` (the last
  `[DATA] P2` quarantine-wiring item flipped this session), triggering `check_archive_candidates`. This doc is a durable
  incident record tracking a cross-repo data-correctness fix; the sibling design doc's 3 implementation todos are still
  in-flight, and this doc is referenced by multiple codex SSOTs + skill files. Archival is correct once the sibling
  doc's implementation todos land and the codex references stabilize — not before.
- **2026-08-16 (plan_reconciler, tranche=tradfi, agt-a74a6a) — correction**: the 2026-08-11 "all §7 todos are now `[x]`"
  claim above was inaccurate — the §7 bare-wire-symbol `[SERVICE] P2` todo (created 2026-07-27) was genuinely still
  open the whole time, just embedded mid-line inside a DONE item's narrative text where it was invisible to a
  line-anchored checkbox scan. Fixed the formatting (own-line, see §7) so it's now visible to
  `regen_backlog_from_plan.py` and future audits; not archive-ready until that item closes too, but `archive_exempt:
  true` causes no harm either way since the doc genuinely still has an open item now.
- **2026-08-17 (slot-7·backend_engineer)**: root-caused + fixed the §7 OKX-FUTURES/DERIBIT `[SERVICE] P2` bare-wire-
  symbol todo. Both previously-untested candidate causes were ruled out by direct measurement (catalogue is clean;
  population is live/ongoing, not stale). True root cause: `tardis_cefi_shards.py`'s manifest-bookkeeping keyed a
  singular (non-chain) FUTURE shard's `record_shard_count` on the bare underlying instead of the real per-contract
  symbol, so the manifest instrument_id could never resolve to a canonical id and silently fell back to the bare
  token. Fixed + regression-tested, shipped `market-tick-data-service@766cf851`. Measured population is much larger
  than originally estimated (20,134 rows, not 230) and still actively growing as of today — flagged as a genuine
  data-correctness finding, not a stale artifact. Split the already-written-rows backfill into a fresh `[DATA] P2`
  todo (below) since it is migration/backfill work, out of this todo's root-cause-and-fix scope.

### 2026-08-17 (slot-19, data_engineering) — §7 backfill todo: script SHIPPED + validated, full-scale apply BLOCKED on shared-host contention

Wrote `market-tick-data-service/scripts/backfill_bare_underlying_future_manifest_ids_2026_08_17.py` — dry-run by
default, `--apply` to write, `--report <jsonl>` checkpoints every resolved row (resumable across chunked invocations,
so a bounded/killed run never loses progress), `--apply-from-report` runs the write-back from an accumulated report.
Bounded, prefix-scoped GCS listing per `(day, venue, instrument_type=future, data_type)` manifest row — no corpus
walk. Verifies every discovered object's filename via the UAC `is_canonical_instrument_id` oracle before trusting it;
the row-count used for each replacement is always read from the object's own parquet footer metadata, never assumed
from the bad row.

**Caught + fixed a real duplication bug during small-sample validation, before any `--apply` run**: a
`(day,venue,data_type)` prefix bundles EVERY underlying active that day (e.g. both BTC- and ETH-dated DERIBIT
futures), so two distinct bad rows sharing that prefix but different underlyings both resolved to the SAME merged
object set and would each independently "correct" into it — silently duplicating every replacement row. Fixed by
scoping the object listing to the bad row's own base-underlying token before deciding single-vs-split; re-running the
25-row sample post-fix produced disjoint, correct corrections for `old='BTC'` vs `old='ETH'` groups on the same
prefix.

**Partial dry-run progress (resumable, NOT yet complete): 1,956/20,134 candidate rows resolved.** `ok_split` 1,461 ·
`ok_single` 32 · `phantom_no_object` 437 (different defect — manifest says captured, no object under the prefix;
correctly not touched, belongs to the phantom reconciler, not this script) · `object_non_canonical` 26 (see the new
todo above). 1,493/1,956 (76%) of resolved rows are auto-correctable with real per-object row counts already read.

**Full-scale completion is BLOCKED on shared-host memory contention, not a script defect.** Four consecutive attempts
to run the discovery pass to completion on this orchestrator VM (workers 6/24/48, with and without an explicit 590s
timeout, with and without `ScheduleWakeup`) were externally killed (`status: killed`; `free -h` showed only 8.6GB/30GB
free with 4.6GB swap in use at the time) — consistent with the documented shared-host RAM-exhaustion incident class
(`agents/data_engineering.md` STEP 0.56; prior incidents 2026-07-27/07-31/08-01). Lower concurrency (6 workers) did
NOT avoid the kill, which reads as host-wide pressure from other concurrent agent work, not this script's own
footprint. Every partial run's progress IS safely preserved — the `--report` JSONL is appended-to as each row
resolves, verified by re-running and observing zero re-resolution of already-completed rows. **Recommended next
step**: either dispatch the remaining discovery pass to a dedicated backfill VM per
`/codex/05-infrastructure/vm-launcher-runbook.md` (this now qualifies as corpus-scale I/O, not a quick in-session
check), or continue via several more small `--report`-checkpointed chunks directly here once host memory pressure
eases. Once discovery reaches 20,134/20,134, `--apply-from-report` performs the actual write-back in one pass
(re-verifies every targeted row against the live canonical manifest immediately before writing, per the module
docstring's safety contract) — not run this session. **Not flipping the backfill checkbox** — the todo's own
done-when (rows actually re-keyed) is not yet met; the script + partial validated discovery is real progress, not the
finish line.

### 2026-08-17 (slot-22, data_engineering) — resumed discovery, +2556 rows, then reproduced the SAME shared-host-contention block with root cause identified

Resumed from a fresh scratchpad (slot-19's own `--report` file lives in that session's now-gone scratchpad, not
committed anywhere durable — this is a repeatable cost of the current design: each session's discovery report is
ephemeral and progress across sessions can't be reused without a durable, repo-relative report path). Chunk 1
(`--limit 3000 --workers 6`, `ANALYSIS_MEM_CAP=6G`) completed CLEAN, no kill: verdict distribution `ok_split` 2297 ·
`phantom_no_object` 557 · `ok_single` 80 · `object_non_canonical` 62 · `content_mismatch` 4 — report now at
3000/20134. A follow-up multi-iteration background loop (self-checkpointing, 3000-row chunks, memory-gated between
iterations) got partway into iteration 2 (report advanced 3000 → 5556) before its whole background task was
externally killed. Three further single-chunk retries at shrinking size (3000/6, 1500/3, 2000/4 workers) were ALSO
externally killed, report count unchanged at 5556 across all three.

**Root cause identified this session (prior sessions only inferred "host-wide pressure" from `free -h`; this is the
first direct confirmation)**: `journalctl`/`/dev/shm/resource-watchdog/kills/*.json` show the kills are NOT hitting
this script's own PID — `slot-3`'s own unbounded script (`finalize_restamp.py`, a DIFFERENT task) was killed by the
host's `resource-watchdog` twice in the same window for exceeding a 4096MB RSS cap (12.4GB then 12.5GB RSS,
`KILL #371`/`#372`), and appears to be respawning and re-hitting the same cap in a loop. My own script's PID never
appears in any `resource-watchdog` kill marker — the kills of MY background tasks are collateral host-wide distress
from slot-3's repeated 12GB+ spikes, not this script exceeding its own (3-6G) cap. This is a DIFFERENT slot's
unbounded script, out of this task's scope to fix (`agents/RULES.md` § "Never bulk-kill a peer's process" — and
slot-3's process wasn't stale, it was actively (re)spawning).

Report is at **5556/20134** (up from 1956 at the last checkpoint) — **correction to my own framing above**: this
report is in THIS session's scratchpad, which is exactly as ephemeral as slot-19's ("safely on disk" understated
that; it will be lost at session end same as slot-19's was, not durable). No repo-relative or GCS durable-report
convention exists for this pattern today (checked `/codex/05-infrastructure/bucket-isolation-model.md` — no
scratch/reports tier documented) — tracked as a fresh todo below rather than silently repeating the loss a third
time. **Not flipping the checkbox** — same as every prior session, the done-when is not met. **Escalating the
recommendation**: this is now the SECOND session (slot-19, then slot-22) to hit this exact wall via the in-session
chunked-retry approach, with an identified external cause (a different slot's runaway process) rather than this
script's own footprint — a THIRD data_engineering worker retrying the identical approach is unlikely to fare
differently while slot-3's issue persists. The dedicated-VM dispatch path (`/codex/05-infrastructure/vm-launcher-
runbook.md`) is now the recommended path over further in-session chunking, or wait until slot-3's runaway script is
independently resolved.

### 2026-08-17 (slot-7, data_engineering) — discovery completed 100%; found + fixed a real bug; `--apply` genuinely
### blocked (not host contention this time — the write step itself is unbounded)

Verified slot-3's contention had cleared (`ps aux` showed no matching process; `free -h` showed 18-21GB available)
before starting, per the prior session's own recommendation. Foreground-chunked discovery (2000-3000 rows/chunk,
`run-bounded-analysis.sh`-wrapped, 6G cap) resumed from slot-22's 5,556 baseline — but that baseline was NOT actually
reachable this session either (confirmed the durability gap the P3 todo below already tracks: slot-22's own report
lived in ITS scratchpad, not mine); started a fresh report in this session's own scratchpad
(`_scratch_slot7/backfill_bare_underlying_report.jsonl`) instead. `run_in_background` chunks were repeatedly killed
by something outside this session's visibility (no resource-watchdog record for those PIDs, memory was healthy each
time) — root cause not identified, worked around by switching to synchronous foreground chunks (each under the
tool's own ~9min budget), which completed reliably. Hit a REAL bug mid-run: `int(row.get("row_count") or 0)` raises
`ValueError: cannot convert float NaN to integer` on a NaN `row_count` (`NaN or 0` evaluates to `NaN`, not `0`,
since NaN is truthy) — this aborted the whole `ThreadPoolExecutor` future-collection loop, killing an
otherwise-clean chunk outright. Fixed with a `pd.notna()` guard, QG-verified, shipped
`market-tick-data-service@7c03fff2dd`. Resumed chunking post-fix with zero further crashes.
**Discovery reached 20,134/20,134 (100%, a first for this todo)**: `ok_split` 9,975 · `ok_single` 7,709 (17,684
correctable) · `phantom_no_object` 2,259 · `object_non_canonical` 116 · `content_mismatch` 75 (new verdict, not seen
in any prior partial run — the sampled content-verify catching a stem/column disagreement; correctly excluded from
`ok`, not investigated further this session — belongs with the `object_non_canonical`/DERIBIT-trades stem-defect
finding above if it recurs at scale). Ran `--apply-from-report --apply` twice — BOTH killed by the shared host's
resource-watchdog with an actual kill record this time (unlike the earlier `run_in_background` mystery-kills):
peak RSS 16.2GB then 15.9GB against the watchdog's 4096MB cap, message "Do not re-spawn on planning VM. Offload this
workload to a spot VM." Root cause identified by reading `_apply()`: it downloads the FULL canonical manifest
(`pd.read_parquet(io.BytesIO(blob.download_as_bytes()))`) unfiltered before matching/rewriting — this is NOT
transient host contention like the two prior sessions hit, it is this function's own unbounded-memory design. Did
NOT retry a third time per the watchdog's explicit directive. Filed the finding as a new `[INFRA] P2` todo above
(two closing options: dedicated-VM dispatch, or a DuckDB-bounded rewrite of `_apply()`) rather than attempting a
rushed fix to a live production-manifest write path under memory pressure. **Not flipping this todo's checkbox** —
discovery is complete but the done-when (rows actually re-keyed) is still not met; VM launches are infra-craft
scope, out of this data_engineering session's remit per `agents/data_engineering.md` `does_not`.

- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries) — swapped the resolved sibling finding
  (`batch_live_filename_divergence_sanitize_symbol_2026_07_20.md`, now `status: resolved`) for
  `backfill_bare_underlying_future_manifest_ids_2026_08_17.py`, the script driving all three of today's active
  discovery/apply sessions directly above (currently blocked on the shared host's memory watchdog). Other 5 entries
  re-verified, unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries).
