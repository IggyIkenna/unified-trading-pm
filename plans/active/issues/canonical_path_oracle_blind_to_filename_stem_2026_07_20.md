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
  (colon-guard fail-loud on build_instrument_id + defi ID_FORM widening, § 7 items 2+4); residual followups tracked in §
  7 (P1 surface-A re-run; P2 quarantine disposition) and the batch=live divergence issue"
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
> `plans/active/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md`.

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
`plans/active/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md`.

## 7. Residual risk / open work

- [x] [SERVICE] P0. Remove the `_sanitize_symbol` call from `live_tick_blob_path` + `_microstructure_blob_path` so live
      filenames carry the literal-colon canonical id (matching batch) — `market-tick-data-service@953679de`
      (`sanitize_file_stem`). Migration population measured 0 (§ 6.1a); reader tolerates the legacy form (§ 6.1b).
- [x] [SERVICE] P0. Remove the silent `build_instrument_id(venue, itype, symbol)` catalogue-miss fallback that mints the
      double-wrapped `VENUE:ITYPE:<raw wire>` ids — tolerance is the mechanism that polluted the corpus. (Provenance:
      operator ruling 2026-07-20. Tracked in the batch=live divergence issue doc.) **DONE
      `unified-api-contracts@502ef57e`**: the actual mechanism lives in the SHARED builder, not any one caller — the
      real caller (`market-tick-data-service/.../adapters/cefi/tardis_shared.py::derive_row_instrument_id`'s bare
      `return build_instrument_id(venue, instrument_type, symbol)` fallback, `[SERVICE]`-tagged as a MTDS file, out of
      this session's repo scope) was left untouched, but `build_instrument_id` itself now FAILS LOUD (`ValueError`) on
      any `symbol` carrying an embedded `:` for every asset group except sports/prediction (whose `symbol` is itself a
      pre-built domain id that legitimately embeds colons) — `:` is the builder's own top-level `VENUE:TYPE:SYMBOL`
      delimiter, so a colon-bearing symbol (e.g. Bitfinex's own wire notation `ADAF0:USTF0`) is never well-formed input
      regardless of which repo's caller supplies it. This closes the defect at the shared root dependency: MTDS's
      catalogue-miss fallback will now raise instead of silently minting `BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0`,
      surfacing as a proper per-shard `record_failed` via the existing shard-isolation machinery rather than a silent
      corrupt write. Regression tests: `tests/internal/unit/test_canonical_id_builder.py::TestSymbolColonGuard`.
- [ ] [DATA] P1. Re-run CeFi surface-A reconciliation with the fixed oracle and restate the verdict; every
      pre-2026-07-20 surface-A verdict is structure-only. (The 1,697 colon_wire live objects in § 6.1a are now flagged.)
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
- [ ] [DATA] P2. The legitimately-unresolvable objects need a quarantine / honest-absence disposition (separate design).
      **NOT resolved by this session's work** — noting state found while investigating: a STANDALONE building block
      already exists (`unified_api_contracts/canonical/quarantine.py` — `is_quarantined_instrument_id` /
      `ResolutionEvidence` / `QUARANTINE_REGISTRY` / `classify_id_form`, `unified-api-contracts@989e9d16`), shipped
      against a DIFFERENT, more recent design doc:
      `plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md`. Per that module's own docstring it is
      "standalone — nothing here is wired into any write or read guard"; the design doc's own §7 todo list (Stage 0
      OBSERVE / Stage 1 WRITE ENFORCE / Stage 2 MANIFEST CLASSIFY / Stage 3 READ ENFORCE) is a materially larger,
      separately-gated program (3 adversarially-CONFIRMED gaps in its own §5 must close before write-enforce ships) —
      out of scope for this session. This item stays open until that program's registry-gated enforcement actually wires
      a disposition for the legitimately-unresolvable population.

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
