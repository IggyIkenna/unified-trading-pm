---
doc_type: issue
title: expected_window_completeness_pct range drift — UAC says 0-1 fraction, codex says 0-100 percentage
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-11
resolved: 2026-05-11
author: ikenna-slot-6
resolution: option-a-rename-to-fraction
resolution_commits: [unified-api-contracts@76f950a]
source:
  [
    "unified_api_contracts/canonical/crosscutting/manifest_schema.py:EXPECTED_WINDOW_COMPLETENESS_PCT_COLUMN docstring
    (UAC@174f401)",
    "/codex/02-data/availability-manifest-and-data-status.md:253",
    "/codex/02-data/availability-manifest-and-data-status.md:344",
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

# `expected_window_completeness_pct` range drift — Case-5 SSOT contradiction

> **✅ RESOLVED 2026-05-11** — operator picked option (a) rename. Shipped at UAC@`76f950a`: column renamed from
> `expected_window_completeness_pct` → `expected_window_completeness_fraction`; value range stays `[0.0, 1.0]`; constant
> name `EXPECTED_WINDOW_COMPLETENESS_PCT_COLUMN` → `EXPECTED_WINDOW_COMPLETENESS_FRACTION_COLUMN`; `V8_NEW_COLUMNS`
> tuple + `V8_COLUMN_DEFAULTS` dict + root facade `__all__` updated; tests + docstring naming-history note shipped.
> Codex docs (`availability-manifest-and-data-status.md`, `service-output-emission-semantics.md`) + plan body
> (`manifest_schema_final_gate_2026_05_09.md` Phase 1.C) updated in same logical unit at PM@<follow-up>. Rename window
> was free (zero on-disk writes had shipped); the `_pct` constant name is banned post-`76f950a`. Original analysis
> preserved below for audit trail.

> **Severity**: P1 — silent correctness risk; not blocking 2026-05-15 freeze but **must** resolve before downstream
> consumers (deployment-api drilldowns, Phase 4 sweep, batch-vs-live recon) start reading the column at runtime.
>
> **Blast radius**: UAC + codex + every future v8 manifest writer + every downstream reader. Three layers (UAC schema
> declaration, codex SSOT doc, column-name convention) currently disagree about whether the column is a 0-1 fraction or
> a 0-100 percentage.
>
> **Suggested owner**: operator triage → either Ikenna slot 1 (workspace-SSOT decision) or
> `manifest_schema_final_gate_2026_05_09.md` Phase 1 owner (slot 6 has shipped; can flip via follow-up commit if
> operator picks 0-1 fraction).

## What I found

Three layers disagree about the canonical range for the v8 `expected_window_completeness_pct` column:

### Layer 1 — UAC `manifest_schema.py` (shipped at UAC@174f401 by slot 6 this session)

```python
EXPECTED_WINDOW_COMPLETENESS_PCT_COLUMN: Final[str] = "expected_window_completeness_pct"
"""Manifest column name for the v8 expected-window completeness fraction.

Value type: ``float | None`` in the closed interval ``[0.0, 1.0]``. Sibling
to UTL ``publish_with_policy`` 's ``completeness_fraction`` argument — ...
"""
```

UAC declares **0.0 to 1.0 fraction**.

### Layer 2 — codex `availability-manifest-and-data-status.md:253`

```
**`expected_window_completeness_pct`** (0.0-100.0 fraction of the expected per-row window that was actually populated;
denominator-aware coverage metric).
```

Codex declares **"0.0-100.0 fraction"** — internally inconsistent (the word "fraction" conventionally means 0-1; "0-100"
conventionally means a percentage).

### Layer 3 — codex `availability-manifest-and-data-status.md:344` (AvailabilityRecord dataclass snippet)

```python
expected_window_completeness_pct: float | None = None  # 0.0-100.0 fraction of expected per-row window populated
```

Same 0-100 fraction wording; same internal inconsistency.

### Layer 4 — column NAME

The column is named `expected_window_completeness_pct` — the `_pct` suffix conventionally implies **percentage
(0-100)**.

### Net

- **UAC says** 0-1 fraction. (Citadel-grade convention: fractions are 0-1.)
- **Codex says** "0-100 fraction" (oxymoron).
- **Column name says** percentage (0-100).
- **UTL `publish_with_policy.completeness_fraction` arg** is documented as 0-1 (`emission_publisher.py:75-78`:
  `"0.0 <= x <= 1.0"`).

Three of four signals agree on 0-1 (UAC + UTL `completeness_fraction` + codex word "fraction"). One signal (column name

- codex range text) agrees on 0-100.

## Why it matters

- **Silent correctness bug at runtime**. A writer that reads UAC's `EXPECTED_WINDOW_COMPLETENESS_PCT_COLUMN` docstring
  writes 0.97 for a 97% complete window. A reader that reads the codex doc expects 97.0 for the same window. The
  downstream consumer (deployment-api drilldown / batch-vs-live recon delta calc / per-row alert threshold) computes
  `1 - 0.97 = 0.03` (3% gap) under one convention and `1 - 97.0 = -96.0` (nonsense) or `(100 - 97.0)/100 = 0.03` under
  the other. The first writer-reader pair to disagree will produce confidently-wrong analytics with no error trace.
- **Phase 4 (workspace consumer sweep) is the natural blast point.** When MTDS / MDPS / features-\* adapters start
  threading the kwarg through to `record_captured(...)` in Phase 4, each callsite picks ONE convention. Drift between
  them is exactly the failure mode the v8 schema-bump was designed to prevent. Need to resolve BEFORE Phase 4 starts.
- **2026-05-15 freeze gate.** Per `manifest_schema_final_gate_2026_05_09.md` § "UAC enums frozen for the window", schema
  changes are locked 2026-05-09 → 2026-05-23. A range-renaming change is technically additive (the column type stays
  `float | None`), so it's reversible IF caught before any writer ships rows. Catching it now is cheap; catching it
  post-cutover is expensive (every parquet on disk would need a re-emit + the manifest reader needs a coerce path).

## Recommended decision

Operator picks ONE convention. Three options:

### Option (a) — Keep 0-1 fraction; rename the column

Rename `expected_window_completeness_pct` → `expected_window_completeness_fraction` (or
`expected_window_completeness_frac` / `expected_window_completeness`). UAC docstring stays as-is. Codex doc updates to
"0.0-1.0 fraction" (drops the "100"). UTL `completeness_fraction` arg name stays consistent.

- **Pro**: matches UTL convention, matches workspace "fraction" semantics, matches my UAC declaration as-shipped.
- **Con**: rename is a schema-version-bump-shaped change (column rename = breaking for any reader already grepping the
  column name). Currently zero on-disk writes have shipped (Phase 2 UTL `record_captured` extension is `[ ]`), so the
  rename is free TODAY.

### Option (b) — Keep `_pct` name; multiply by 100 (percentage 0-100)

UAC docstring updates to "0.0-100.0 percentage". Codex doc fixes the "fraction" wording to "percentage". UTL writer
multiplies `completeness_fraction` × 100 at write time (or the kwarg API gets a second
`expected_window_completeness_pct` arg the caller passes in pre-scaled).

- **Pro**: column name stays stable, on-disk shape matches the name.
- **Con**: introduces a `× 100` scaling step at every callsite that bridges UTL `completeness_fraction` (0-1) → manifest
  `_pct` column (0-100). Foot-gun-shaped (every Phase 4 callsite must remember to multiply OR call a helper). Codex doc
  "0-100 fraction" wording is a sign someone has already been confused.

### Option (c) — Codex was wrong; UAC + the name + the word "fraction" all coexist by declaring 0-1 stored as a `_pct`-named float

UAC stays 0-1. Codex doc fixes the range text to "0.0-1.0 fraction" + adds a "(yes, the column is named `_pct` but the
stored value is a 0-1 fraction; legacy naming, do not multiply by 100)" footnote. UTL passes through
`completeness_fraction` as-is.

- **Pro**: zero code change post-`174f401`; minimal codex tightening.
- **Con**: leaves a permanent naming foot-gun on disk — any future reader that doesn't read the footnote will assume
  percentage and divide by 100. The column-name convention "`_pct` = percentage" is broadly assumed across the
  workspace; violating it locally is technical debt.

**Slot-6 recommendation**: option (a) — rename to `expected_window_completeness_fraction`. The window for a free rename
is open today (no writers yet); it's closed forever after the first row writes the column under one convention.

## Composes with

- `manifest_schema_final_gate_2026_05_09.md` Phase 1 (v8 schema column declaration owner; UAC@`174f401` shipped slot 6).
- `manifest_schema_final_gate_2026_05_09.md` Phase 2 (UTL `ManifestWriter.record_captured` extension; **not started**;
  blocks if not resolved).
- `manifest_schema_final_gate_2026_05_09.md` Phase 4 (workspace consumer sweep; **not started**; every callsite that
  threads the kwarg picks ONE convention).
- `/codex/02-data/availability-manifest-and-data-status.md` lines 253 + 344 (the codex side that needs updating).
- `unified_trading_library/emission_publisher.py:75-78` (UTL `completeness_fraction` arg; canonical 0-1).
- CLAUDE.md "No double SSOT in data-saving methodology" — three-way drift is the explicit anti-pattern this rule
  targets.

## Audit cadence

Reviewers reject any Phase 4 callsite that passes `expected_window_completeness_pct=` without operator-confirmed range
convention. The Phase 4 P0 grep-verify item (`record_captured.*pipeline_mode`) should extend to grep
`record_captured.*expected_window_completeness_pct` once the convention is locked.
