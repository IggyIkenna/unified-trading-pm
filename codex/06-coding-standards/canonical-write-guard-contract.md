---
doc_type: codex-ssot
title: Canonical write-guard contract — which write lanes assert canonicality, and which deliberately do not
summary: >-
  The writer-side guard register. Names every GCS write lane that calls UAC `canonical_path_violations()`, the
  `require_pipeline_mode` value it passes, and — for every lane that does NOT guard — the stated posture (guard-pending
  / structurally-exempt). Establishes the requirement that a NEW write lane declares its guard posture in this register
  before it ships. An unguarded lane silently re-drifts after every migration, which is why the same corpus gets
  migrated twice. Also resolves the dangling `canonical-write-conventions.md` codex pointer.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts, market-tick-data-service, e2e-testing, unified-trading-pm]
scope: [engineer]
tags: [canonicalisation, write-guard, gcs-paths, pipeline-mode, ssot, drift-prevention]
related:
  [
    ../02-data/cross-asset-canonical-target-ssot.md,
    ../02-data/pipeline-mode-partition.md,
    ../02-data/four-surface-reconciliation-procedure.md,
    ../02-data/canonical-cutover-register.md,
    ../02-data/non-canonical-path-inventory.md,
  ]
created: 2026-07-20
authoritative_for:
  [
    writer-side canonical guard contract,
    which write lanes call canonical_path_violations and with which require_pipeline_mode,
    guard posture declaration requirement for new write lanes,
  ]
referenced_by: [../../plans/active/data_pipeline_reconciliation_skill_2026_07_20.md]
owner:
last_reviewed: 2026-07-20
code_refs:
  [
    unified-api-contracts/unified_api_contracts/canonical/partition_paths.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/partitioned_writer.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/symbol_rules.py,
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py,
  ]
---

# Canonical write-guard contract

**A write lane that builds a GCS object path is either GUARDED — it calls the UAC machine oracle before any bytes land —
or it is UNGUARDED with a stated reason recorded here. There is no third state.** An unguarded lane with no stated
reason is how a migrated corpus silently re-drifts: the migration lands, nothing asserts the invariant on the write
side, and the next backfill re-creates the shape the migration just removed. This is the mechanism behind repeat
migrations of the same corpus.

The canonical target itself (path grammar, id grammar, shard-atom grain) is **not** restated here — SSOT is
[`codex/02-data/cross-asset-canonical-target-ssot.md`](../02-data/cross-asset-canonical-target-ssot.md). This doc covers
only **who enforces it at write time**.

All `file:line` citations below were read, not grepped, on 2026-07-20.

---

## 0. The dangling `canonical-write-conventions.md` pointer — resolved

`plans/active/issues/_cefi_canonical_blueprint_2026_07_17.md:558` cites, as **codex**, the triple
`chart-candle-delivery-flow.md:274`, `canonical-write-conventions.md:128-134`, `per-asset-group-bucket-layouts.md:135`.

| Cited path                          | Reality                                                                                                                                                  |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `chart-candle-delivery-flow.md`     | EXISTS — `codex/02-data/chart-candle-delivery-flow.md`                                                                                                   |
| `per-asset-group-bucket-layouts.md` | EXISTS — `codex/02-data/per-asset-group-bucket-layouts.md`                                                                                               |
| `canonical-write-conventions.md`    | **Does NOT exist anywhere under `unified-trading-pm/codex/`.** It exists repo-locally as `market-tick-data-service/docs/canonical-write-conventions.md`. |

The pointer is **mis-attributed, not absent**: a repo-local MTDS doc was cited as if it were a workspace codex SSOT.

**Resolution**: for the _guard contract_ — which lanes assert canonicality — **this doc is the SSOT**. For MTDS
adapter-internal write conventions, cite `market-tick-data-service/docs/canonical-write-conventions.md` explicitly as a
repo-local doc, never as `codex/06-coding-standards/…`.

> **UNVERIFIED, flagged for the reader**: the blueprint's characterisation of what
> `canonical-write-conventions.md:128-134` _says_ (a "canonical symbol segment" filename rule) does not match the
> current file. Line 129 of that file opens the heading `On-chain-perp symbol canonicalization (2026-07-09)`. Either the
> line range is stale or the blueprint is paraphrasing a different section. Do not rely on that citation without
> re-reading it.

---

## 1. The machine oracle

`unified_api_contracts.canonical.partition_paths.canonical_path_violations(path, *, require_pipeline_mode=False)`
(`partition_paths.py:661`) returns one human-readable violation string per drift class; empty list == canonical.
`is_canonical()` (`:828`) is a thin boolean wrapper over it (`:837`).

Two properties are load-bearing for the guard contract:

1. **`require_pipeline_mode` defaults `False`** (`:661`). The docstring states the default "accepts the back-compat bare
   paths the builders still emit". A guard that omits the keyword is therefore materially **weaker** than the codex
   declaration in [`pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md). **Every write guard passes
   `require_pipeline_mode=True` explicitly** — all three existing guards do (§2a).
2. **The oracle only understands the `raw_tick_data/by_date/` prefix.**
   `RAW_TICK_DATA_PREFIX = "raw_tick_data/by_date/"` (`partition_paths.py:66`); a path not starting with it returns
   immediately with `"path does not start with the canonical prefix"` (`:681-683`). This determines the sports posture
   (§3c) and dictates _where_ in a lane the guard must sit (§3b).

---

## 2. Guard register

### 2a. GUARDED lanes

| Lane                         | Call site                                                                                                             | `require_pipeline_mode` | On violation       |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------- | ----------------------- | ------------------ |
| **tradfi backfill (W1)**     | `.../engine/orchestrator/partitioned_writer.py:93`, via `_assert_canonical_tradfi_path` (`:83`), called at `:258-259` | `True`                  | `raise ValueError` |
| **live websocket (all AGs)** | `.../live/websocket_runner.py:128`                                                                                    | `True`                  | `raise ValueError` |
| **book microstructure**      | `.../cli/handlers/book_microstructure_handler.py:188`                                                                 | `True`                  | `raise ValueError` |

Note on scope — the tradfi guard is **conditional on asset_group**. `partitioned_writer.py:258` reads
`if self._asset_group == "tradfi": _assert_canonical_tradfi_path(gcs_path)`. The _same writer class_ is therefore
guarded for tradfi and unguarded for cefi and prediction, which flow through the identical `:249` call site. The guard's
docstring (`:85-88`) states the intent: "so a regressing backfill fails LOUD instead of silently re-diverging the
migrated corpus" — an intent that applies verbatim to the other two asset_groups sharing the writer.

### 2b. Compensating READ-side detection (not a write guard)

`e2e-testing/scripts/audit/manifest_hygiene_daily.py:197` runs
`canonical_path_violations(raw, require_pipeline_mode=True)` over the manifest's implied paths (index-only, no walk) and
emits `DP_NONCANONICAL_PATH_ON_DISK`. This **detects** drift after the fact; it does not prevent it, and it only sees
paths that reached the manifest. It is the sole net under every lane in §2c.

### 2c. UNGUARDED lanes

| Lane                                   | Where the path is built                                                                                                                                                                                             | Emits `pipeline_mode=`?                     | Posture                        |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ------------------------------ |
| **cefi batch — PartitionedTickWriter** | `symbol_rules.py:_build_partition_path_for_asset_group` (def `:383`) → `partitioned_writer.py:249`                                                                                                                  | **yes** — inserted at `symbol_rules.py:466` | GUARD-PENDING, unblocked (§3a) |
| **cefi batch — Tardis lane**           | `adapters/cefi/tardis_shared.py:658-662` (hand-rolled, bypasses the UAC builder)                                                                                                                                    | **yes** — `:659`                            | GUARD-PENDING, unblocked (§3a) |
| **prediction batch**                   | `symbol_rules.py:_build_partition_path_for_asset_group` → `partitioned_writer.py:249` (Kalshi/Polymarket adapters stamp columns only — `kalshi_adapter.py:577-578` explicitly delegates filename construction here) | **yes** — `symbol_rules.py:466`             | GUARD-PENDING, unblocked (§3a) |
| **defi batch**                         | `build_defi_partition_path` re-exported at `adapters/defi/canonical_write.py:47`, called `:220`, `:308`                                                                                                             | **yes** — passed explicitly at `:227`       | GUARD-PENDING, unblocked (§3b) |
| **sports**                             | `sports_reference/…` templates, e.g. `engine/sports_catalog_reader.py:15-16, 44`                                                                                                                                    | yes, but outside the oracle's grammar       | EXEMPT (§3c)                   |

---

## 3. Stated posture for each unguarded lane

### 3a. cefi batch + prediction — GUARD-PENDING, and the blocker is smaller than it looks

The obvious-seeming blocker is not real. It is worth stating precisely, because the shallow reading points the opposite
way:

| UAC builder                                | `pipeline_mode` parameter? | Emits the segment?                                   |
| ------------------------------------------ | -------------------------- | ---------------------------------------------------- |
| `build_defi_partition_path` (`:88`)        | **yes** (`:96`)            | yes (`:171`)                                         |
| `build_tradfi_partition_path` (`:287`)     | **yes** (`:294`)           | yes (`:351`)                                         |
| `build_cefi_partition_path` (`:194`)       | **NO**                     | **no** — `:242-244` emits `day=…/asset_group=cefi/…` |
| `build_prediction_partition_path` (`:383`) | **NO**                     | **no** — `:431-433`                                  |

From the builders alone one would conclude cefi and prediction _cannot_ be guarded at `require_pipeline_mode=True`.
**That conclusion is wrong**, because no production write lane uses those two builders raw:

- `symbol_rules.py:_build_partition_path_for_asset_group` calls `build_cefi_partition_path` for cefi and an inline build
  for prediction, then **unconditionally inserts the segment for every asset_group** at `:466`:
  `return base.replace(f"day={day_str}/", f"day={day_str}/pipeline_mode={_pm.value}/", 1)`, with the value derived from
  the same `derive_pipeline_mode_for_row` the migrators and manifest rebuilds use (`:459`).
- the Tardis cefi lane bypasses the builder entirely and emits the segment inline (`tardis_shared.py:659`), also via
  `derive_pipeline_mode_for_row` (`:654`).

So the paths that actually reach GCS on these lanes **already carry `pipeline_mode=` and would pass a
`require_pipeline_mode=True` guard today**. The guard is missing, not blocked. For the PartitionedTickWriter lane it is
a one-line change: widen the `asset_group == "tradfi"` condition at `partitioned_writer.py:258`.

> **The builder gap is still a real latent hazard, just a different one.** Because `build_cefi_partition_path` and
> `build_prediction_partition_path` have no `pipeline_mode` axis, correctness depends on every caller remembering to
> wrap them. A **new** caller that uses either builder directly silently produces a path missing `pipeline_mode=` — and
> that path would be caught only by the after-the-fact manifest sweep (§2b). This is an argument **for** adding the
> guard, not against it. Giving the two builders the axis (matching defi/tradfi) removes the hazard at the source; it is
> not a prerequisite for the guard.
>
> A stale comment compounds this: `tardis_shared.py:646` claims the helper "mirrors UAC `build_cefi_partition_path`
> byte-for-byte". It does not — it adds a `pipeline_mode=` segment the UAC builder cannot emit. Treat that comment as
> incorrect.

### 3b. defi batch — GUARD-PENDING, unblocked, with one placement constraint

`build_defi_partition_path` already accepts and emits `pipeline_mode` and `canonical_write.py:227` passes it, so nothing
prevents a `require_pipeline_mode=True` guard at `canonical_write.py:220` / `:308`. No blocker was found and no intent
has ever been recorded for leaving it off.

**Placement constraint**: defi paths are post-processed by `run_tag_aware_partition_path` (`canonical_write.py`, called
at `:229`). For a non-standard `run_tag` it returns `f"{run_tag}/{partition_path}"` — which no longer starts with
`raw_tick_data/by_date/` and would therefore trip the oracle's prefix check (`partition_paths.py:681-683`) as a false
positive. The guard must run **on the builder output, before the run_tag wrap**, or be explicitly run_tag-aware.

Coverage today is asymmetric in exactly the wrong direction: defi **live** writes are guarded (because
`websocket_runner.py:128` guards every asset_group), defi **batch** writes are not — so defi drift is caught on the live
path and missed on the backfill path, which is where re-drift after a migration actually originates.

### 3c. sports — EXEMPT, structurally outside the oracle's grammar

Sports is the one genuine exemption, and the reason is mechanical rather than a judgement call. Sports objects live
under `sports_reference/by_date/day={D}/…` with **no `asset_group=` key at all**
(`engine/sports_catalog_reader.py:15-16, 44`). The oracle hard-requires the `raw_tick_data/by_date/` prefix
(`partition_paths.py:66`, early return `:681-683`), so calling it on any sports path returns exactly one violation —
`"path does not start with the canonical prefix"` — for **every** sports object, canonical or not. The guard would be
100% false-positive and carry zero signal.

Sports also does not flow through `PartitionedTickWriter` at all: `symbol_rules.py:441-444` raises
`PartitionedTickWriter does not support asset_group={ag!r}` for sports and defi, so there is no shared call site to
extend.

Posture: **exempt from `canonical_path_violations()`**. The exemption is scoped to _this oracle_, not to canonicality —
sports still has a canonical target. Closing it requires either a sports-aware branch inside `canonical_path_violations`
or a separate sports oracle; neither exists today (§5, Q2).

---

## 4. Requirement — a new write lane declares its guard posture

**Every new code path that constructs a GCS object path for persisted pipeline data MUST add a row to §2 before it
ships.** The row states one of exactly three postures:

- **GUARDED** — cite the call site `file:line` and the `require_pipeline_mode` value. `True` is the expectation; `False`
  requires a one-line reason in the row.
- **GUARD-PENDING** — the specific blocker, and the ordered prerequisite that removes it. "Nobody got to it" is not a
  blocker; if there is none, say "unblocked" (as §3a and §3b now do).
- **EXEMPT** — the structural reason the oracle cannot express this lane's grammar (as §3c). "It's a one-off script" is
  not a structural reason; "the oracle's prefix contract does not cover this tree" is.

A lane that reaches review with no row is **review-blocking**. "The pre-existing lanes are unguarded too" is not a
reason to omit the row — it is the observation this register exists to make actionable.

Two corollaries:

- **Guard placement**: the guard asserts the bytes-that-will-land path. If a lane post-processes the builder output
  (run-tag prefixing, `.replace` insertion, bucket-prefix wrapping), state which side of that transform the guard sits
  on and why (§3b is the worked example).
- **Migration ordering**: **do not run a canonicalisation migration over a corpus whose write lane is UNGUARDED without
  first recording the posture here.** The migration lands, the lane re-drifts, and the second migration costs what the
  first one did.

---

## 5. Open questions (UNRULED — stated, not decided)

**Q1 — Should the `partitioned_writer.py:258` guard be widened from tradfi to all asset_groups now?** The §3a evidence
says the paths would pass. But "would pass on the shapes we inspected" is not "will pass on every shape in production" —
a cefi v5/v6 dual chain-tail or a prediction CQG variant could raise mid-backfill.

- _Widen now_: closes cefi-batch and prediction in one line; a raise is loud and immediate.
- _Widen behind a warn-only mode first_: log violations for one backfill cycle, then promote to raise. Costs a cycle;
  removes the risk of a mid-run hard failure on a shape nobody enumerated.
- _Leave tradfi-only_: status quo, with only the after-the-fact manifest sweep (§2b) underneath.

No operator ruling exists. Not decided here.

**Q2 — Should sports get oracle coverage, and where?**

- _Branch inside `canonical_path_violations`_: one oracle, consistent with "the machine oracle is the classifier". Cost:
  the prefix contract (`:681-683`) becomes conditional and every existing caller inherits sports semantics it did not
  ask for.
- _Separate sports oracle_: keeps `canonical_path_violations` single-grammar. Cost: two oracles to keep in sync, and
  `/data-pipeline-reconciliation` must dispatch on asset_group before choosing one.
- _Leave exempt_: status quo; sports canonicality is asserted only by the per-AG reference sheet and human review.

Not decided here.

**Q3 — Should `build_cefi_partition_path` / `build_prediction_partition_path` gain a `pipeline_mode` axis?** Doing so
would let the two lanes drop their external `.replace` / inline compensation and close the new-caller hazard flagged in
§3a. Against: it touches a UAC SSOT signature with callers across repos, and the per-AG cutover dates in
[`canonical-cutover-register.md`](../02-data/canonical-cutover-register.md) would need to gate the default. Independent
of Q1 — the guard does not wait on this. Not decided here.
