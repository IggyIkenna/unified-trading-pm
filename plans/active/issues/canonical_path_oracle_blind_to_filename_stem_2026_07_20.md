---
doc_type: issue
title:
  "UAC canonical_path_violations() was BLIND to the filename instrument-id stem — the machine oracle returned
  FALSE-CLEAN for ~811,200 wire-named CeFi objects"
summary:
  The workspace HARD RULE says canonical-vs-non-canonical is decided by the UAC `canonical_path_violations()` machine
  oracle. That oracle dropped the last path segment (`partition_segments = segments[:-1]`, "Last segment is the file
  name") before validating, and only `asset_group=tradfi` single-instrument shards ever carried a filename rule. So raw
  venue wire stems (`ADAF0:USTF0.parquet`) and double-wrapped catalogue-miss ids
  (`BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0.parquet`) returned 0 violations == CANONICAL at both `require_pipeline_mode`
  settings. Anyone following the rule to assess CeFi surface-A canonicality would report the corpus CLEAN while
  independent measurement put the CeFi filename surface at 20.82% canonical by id-form. A fix classifying violations
  STRUCTURAL vs ID_FORM, with BOTH reported by default, is implemented and verified but NOT LANDED -- the caller audit
  found that the two CeFi write-time guards build filenames with `_sanitize_symbol`, which strips the canonical id's
  literal colon, so default-on ID_FORM makes them raise on EVERY live CeFi write even for correctly-resolved
  instruments. No caller was softened; the impact is reported here for the separate fail-hard enforcement design to
  decide. The docs are corrected NOW so the machine-oracle rule cannot mislead a reconciliation in the meantime.
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
execution_scope: local-only
drift_direction: advance-docs
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
---

# The canonical-path machine oracle was blind to the filename stem

> **🔴 OPERATOR-NOTIFY — data-correctness + SSOT-contradiction class.** Every surface-A canonicality verdict produced
> before 2026-07-20 is **structure-only**. A "0 violations == canonical" result from that period says nothing about
> whether the objects carry canonical instrument_ids in their filenames, and must not be cited as evidence that they do.

> **🛑 THE UAC FIX IS BUILT AND VERIFIED BUT NOT LANDED — two blockers, § 6.1 and § 9.** Default-on `ID_FORM` makes the
> two CeFi write-time guards raise on **every live CeFi write**, including for correctly-resolved canonical instruments,
> because the writers sanitize the id's colons (§ 6.2). **No caller was softened** — per instruction the impact is
> reported, not papered over. Landing the UAC change without first fixing § 6.2 is a live-write outage.

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
| `codex/02-data/four-surface-reconciliation-procedure.md` § 4                               | procedure     | **YES** — enumerated the oracle's clauses without noting the stem is unvalidated           |
| `codex/02-data/reconciliation-finding-taxonomy.md` § 2.2 `non_canonical_path`              | taxonomy      | **YES** — the finding could never fire on a wire-named CeFi object                         |
| `e2e-testing/scripts/audit/manifest_hygiene_daily.py:197` (`DP_NONCANONICAL_PATH_ON_DISK`) | counts / WARN | **YES** — index-only oracle run; wire stems never raised the alert                         |
| `codex/02-data/non-canonical-path-inventory.md`, `…/canonical-cutover-register.md`         | reference     | inherit the same weaker definition                                                         |

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
| 2   | `market-tick-data-service/.../live/websocket_runner.py:128` `live_tick_blob_path`                           | **RAISES**            | cefi + defi  | **🛑 BLOCKER — raises on EVERY live CeFi write** (defi unaffected; not id-form-checked)   |
| 3   | `market-tick-data-service/.../cli/handlers/book_microstructure_handler.py:188` `_microstructure_blob_path`  | **RAISES**            | cefi         | **🛑 BLOCKER — raises on every microstructure shard write**                               |
| 4   | `e2e-testing/scripts/audit/manifest_hygiene_daily.py:197`                                                   | counts / WARN finding | all          | reports MORE findings (wire stems now surface) — **the desired outcome, no crash**        |

No other production caller exists. `deployment-api/.../_distinct_values.py` and the `pipeline_e2e_check.py` scripts
matched a grep on unrelated local identifiers (`_input_row_is_canonical`), not on this API.
`instruments-service-agentwork-sports-2026-07-13/` is a stale duplicate worktree, not a shipping repo.

### 6.1 The BLOCKER, measured against the real functions

Both CeFi guards build their filename as `_sanitize_symbol(instrument_id)`, and
`market-tick-data-service/.../engine/orchestrator/symbol_rules.py:368-380` rewrites `[/\\:\s]` to `_`. So the canonical
id `HYPERLIQUID:PERPETUAL:BTC-USD@LIN` reaches the oracle as `HYPERLIQUID_PERPETUAL_BTC-USD@LIN.parquet` — which
correctly fails the id-form check. Measured by calling the real functions with the fixed oracle installed:

```
RAISES HYPERLIQUID      -> live_tick_blob_path built a non-canonical GCS path ... 'HYPERLIQUID_PERPETUAL_BTC-USD@LIN.parquet'
RAISES BINANCE-FUTURES  -> live_tick_blob_path built a non-canonical GCS path ... 'BINANCE-FUTURES_PERPETUAL_BTC-USDT.parquet'
RAISES ASTER            -> live_tick_blob_path built a non-canonical GCS path ... 'ASTER_PERPETUAL_BTC-USDT.parquet'
RAISES _microstructure_blob_path -> ... 'BITFINEX-FUTURES_PERPETUAL_ADA-USDT.parquet'
```

**This is not the fail-hard the operator asked for.** Failing hard on a wire-named / catalogue-miss id is correct;
crashing a _correctly-resolved canonical instrument_ because the writer sanitized its colons is a writer bug surfacing
as an outage. It is the **2026-06-23 live-VM freeze pattern exactly** (an over-broad write-time guard silently froze the
deribit/hyperliquid/binance live VMs for hours) — see the standing warning comment at `partition_paths.py:740-749`.

### 6.2 The real defect this exposed — live filenames diverge from batch

`PartitionedTickWriter._resolve_writer_file_name` (`market-tick-data-service/.../partitioned_writer.py:181-205`) writes
the canonical id **VERBATIM** — its docstring is explicit: _"written VERBATIM, not `_sanitize_symbol`-d — real live
filenames carry literal `:`"_. The **live** runner and the **microstructure** handler sanitize instead. So live and
batch write the same instrument to **different object names**. This is both a canonicality defect and a **batch=live
determinism** concern (`codex/09-strategy/operational/paper-batch-live-reconciliation.md`).

**Fixing § 6.2 is what makes § 6.1 disappear** — it is the canonical-SSOT-and-migrate move, not a softening.

## 7. Residual risk / open work (owned by the separate fail-hard enforcement design)

- [ ] [SERVICE] P0. Remove the `_sanitize_symbol` call from `live_tick_blob_path` + `_microstructure_blob_path` so live
      filenames carry the literal-colon canonical id (matching batch). Requires a migration decision for already-written
      sanitized live objects. **This unblocks default-on ID_FORM at the write boundary.** (Provenance: caller audit §
      6.1, 2026-07-20.)
- [ ] [SERVICE] P0. Remove the silent `build_instrument_id(venue, itype, symbol)` catalogue-miss fallback that mints the
      double-wrapped `VENUE:ITYPE:<raw wire>` ids — tolerance is the mechanism that polluted the corpus. (Provenance:
      operator ruling 2026-07-20.)
- [ ] [DATA] P1. Re-run CeFi surface-A reconciliation with the fixed oracle and restate the verdict; every
      pre-2026-07-20 surface-A verdict is structure-only.
- [ ] [DATA] P2. Decide the id grammar for `defi` / `prediction` so `_ID_FORM_CHECKED_ASSET_GROUPS` can widen; until
      then those AGs report "not checked".
- [ ] [DATA] P2. The legitimately-unresolvable objects need a quarantine / honest-absence disposition (separate design).

## 8. Codex SSOTs updated

- `codex/02-data/four-surface-reconciliation-procedure.md` § 4 — corrected banner + two-class table + § 4.0 scope caveat
- `codex/02-data/reconciliation-finding-taxonomy.md` § 2.2 — violation class must be named in every report
- `cursor-configs/skills/data-pipeline-reconciliation/SKILL.md` § 3a — two-question statement
- `cursor-configs/CLAUDE.md` — reconciliation one-liner

## 9. Why the UAC change was NOT landed (both blockers are external to the change)

1. **Live-write outage (§ 6.1)** — landing default-on `ID_FORM` before removing the `_sanitize_symbol` call (§ 6.2)
   raises on every live CeFi write. Fixing § 6.2 changes live object NAMES, which is a migration decision, not a
   unilateral one. **Decision required.**
2. **UAC quality gates are RED from another agent's in-flight work** —
   `tests/unit/test_venue_adapter_keys.py:: test_every_canonical_venue_has_an_entry` fails because an uncommitted
   working-tree change adds `VENUES_BY_ASSET_GROUP` sports venues (BETMGM, BETWAY, BOVADA, …) with no
   `VENUE_TO_ADAPTER_KEY` entries. **Proven foreign**: the symbol `VENUES_BY_ASSET_GROUP` does not exist at `HEAD`
   (`AttributeError` on a clean detached worktree), and the failing test does not import `partition_paths` at all. A
   commit cannot be made from a red tree, so quickmerge is blocked until that agent lands or reverts.
   `market-tick-data-service` is separately unshippable — 6 files in an unresolved merge state (`UU`/`UD`).

The UAC diff (`partition_paths.py`, `__init__.py`, `tests/unit/test_partition_path_is_canonical.py`) is complete and its
own tests pass (178 passed across the four canonical-path test modules).
