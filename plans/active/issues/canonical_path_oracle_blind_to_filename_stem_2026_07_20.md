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
asset_group: [cefi, tradfi, meta]
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
    _cefi_canonical_blueprint_2026_07_17,
    data_pipeline_hardening_self_monitoring_2026_06_22,
  ]
created: 2026-07-20
author: unknown
priority: P0
parent_epic: infrastructure_master
source:
  "Operator-ratified finding 2026-07-20: the wire-named-file defect caught by eye would be reported FALSE-CLEAN by the
  official reconciliation procedure. Reproduced independently against the installed UAC before any change."
execution_scope: orchestrator-agent
drift_direction: advance-docs
depends_on: []
locked_by:
locked_since:
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
    /plans/archive/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md,
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

`ID_FORM` is checked for **cefi + tradfi only**. `defi` / `prediction` / `sports` ids route through the passthrough and
domain-specific builders (pool addresses, condition ids, fixture ids) whose grammar is not `VENUE:ITYPE:BASE-QUOTE`;
applying the regex there would manufacture false violations. **A clean `ID_FORM` result for those AGs means "not
checked", not "verified canonical."** Widening `_ID_FORM_CHECKED_ASSET_GROUPS` requires a declared id grammar first.

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
      `date, venue, instrument_type, data_type,        instrument_id, capture_status, pipeline_mode, chain, quote_asset, margin_type`):
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
      verdict" scope) — tracked as a new todo below. - [ ] [SERVICE] P2. Root-cause + fix the batch-side
      bare-wire-symbol id defect found above (EXTENDED-STARKNET/perpetual, OKX-FUTURES/FUTURE, DERIBIT/FUTURE via
      `batch_tardis`/`batch_extended`) — likely a catalogue-miss fallback in the MTDS batch writer path that, unlike the
      colon-embedded case `build_instrument_id` now guards (§ 7 item 2), never wraps a colon-less symbol into
      `VENUE:ITYPE:SYMBOL` at all. Verify against `derive_row_instrument_id`
      (`market-tick-data-service/.../adapters/cefi/tardis_shared.py`) and the EXTENDED adapter's own id derivation.
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
- [ ] [DATA] P2. **UNBLOCKED 2026-08-11** — `fail_hard_canonical_enforcement_design_2026_07_20.md`'s `[DESIGN] P1`
      gap-closing todo is now done (§5b of that doc), splitting into 3 concrete implementation todos there (row-level
      bundle column gate; live-lane manifest-key-from-column derivation; `unclassified` temporal read-gate state). This
      item's quarantine/honest-absence disposition is now worker-determinable: wire
      `unified_api_contracts/canonical/quarantine.py`'s `is_quarantined_instrument_id`/`ResolutionEvidence`/
      `QUARANTINE_REGISTRY`/`classify_id_form` (still a standalone module, 0 non-test callers as of 2026-08-02) into a
      real write/read guard, following the sibling doc's 3 implementation todos as the sequencing (Gap 1/2's write-side
      fixes land before Gap 3's read-gate `unclassified` state, matching Stage 1 → Stage 3 ordering in that doc's §2).
      Recommend a quick operator/engineering sanity check on the sibling doc's §5b resolutions before this ships, given
      the correctness stakes (flagged there, not gating dispatch). Prior text preserved for the audit trail: this item
      was previously `BLOCKED-UPSTREAM-DESIGN`, gated on the sibling doc's `[DESIGN] P1` todo being open (re-confirmed
      2026-08-02, slot-12); retagged then because the sibling design doc is itself `assigned_vm: NA` /
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
