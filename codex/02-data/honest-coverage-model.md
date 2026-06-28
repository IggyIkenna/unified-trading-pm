---
scope: [engineer, admin]
last_reviewed: 2026-06-28
---

# Honest Coverage v2 — Two Layers, Two Views, Instrument Gates Download

> **This is the SSOT for the Honest Coverage v2 model.** It is the durable reference for the two-layer / two-view /
> instrument-gate architecture. Plans and agents cross-reference this doc; they do not re-explain it.

---

## Why v1 was not enough

The v1 model measured Layer-2 (data-download coverage) against a denominator it never independently verified. If the
instrument-enumeration skeleton was incomplete — missing a whole `instrument_type`, a whole `data_type`, or an entire
venue — the coverage % looked fine while large swaths of the expected universe were simply absent from the denominator.

> You cannot have honest download coverage on top of a dishonest instrument denominator.

v2 makes the denominator audit first-class and **gates** download-coverage reporting on it.

---

## Two layers (the gate)

### Layer 1 — Instrument coverage (denominator audit)

**Question answered:** is the could-exist universe itself complete?

Layer 1 checks whether the `IS catalogue × UAC expected-data-type matrix` enumerates **every
`(venue, instrument_type, data_type)` tuple that should exist**, bounded by instrument listing windows.

The two axes:

| Axis                          | Source                                                                                      |
| ----------------------------- | ------------------------------------------------------------------------------------------- |
| Instruments in the universe   | IS catalogue (`build_instrument_catalogue.py` lifecycle roll-up; `mvp` is a stamped column) |
| Data types expected per venue | UAC `DATA_TYPES_BY_ASSET_GROUP` / `get_expected_data_types_for_venue`                       |

A **Layer-1 hole** is any `(venue, instrument_type, data_type)` that UAC says _should_ exist but the skeleton
(`enumerate_expected_universe.py` output) does not contain. Examples: the entire `options_chain` data_type for a venue,
an `instrument_type` the writer silently skipped, a new data_type added to UAC but not yet wired into the enumerator.

**Layer 1 is measured BEFORE Layer 2.** Its completeness fraction is reported independently.

### Layer 2 — Data-download coverage

**Question answered:** for the Layer-1-verified denominator, how many shards were actually captured?

Layer 2 applies the 4-state `capture_status` accounting against the denominator Layer 1 verified:

| State                    | Meaning                                                                                    |
| ------------------------ | ------------------------------------------------------------------------------------------ |
| `captured`               | Real parquet on disk at the canonical GCS path                                             |
| `empty_confirmed[typed]` | Source returned 200 + zero rows, OR known expected gap — MUST carry a typed `error_reason` |
| `attempted_failed`       | Exception during fetch; classified via UAC `classify_venue_error()`                        |
| `expected_unattempted`   | Downstream service skipped shard — upstream empty/failed or instrument outside scope       |

**`empty_confirmed` MUST be typed.** A blank `error_reason` on an `empty_confirmed` row is a measurability violation
(the Phase 0 fix); see
[availability-manifest-and-data-status.md](./availability-manifest-and-data-status.md#proof-of-honest-absence).

---

## When is Layer-2 coverage trustworthy?

**Only when Layer-1 = 100%.**

The system NEVER reports "downloads look good" while the instrument denominator has holes. Until Layer-1 reaches 100%
for an asset_group, the Layer-2 % for that asset_group is displayed with a `⚠ DENOMINATOR INCOMPLETE` flag and
interpreted as a lower bound, not a real coverage number.

This gate is enforced in `measure_honest_coverage.py`: when Layer-1 completeness for an AG < 100%, the
`instrument_gates_download: true` flag is set in the output, and the Layer-2 headline for that AG is annotated
accordingly.

---

## Two views (exposed at both layers)

### View A — day-by-day (time axis)

For each day in the window, are all expected shards for that day present?

- Catches: missed a whole day, missed a date range, a data_type that went missing for 2 weeks.
- Rendered as a calendar heat-map or time-series coverage %.

### View B — shard-breakdown (entity axis)

For each `(venue × instrument_type × data_type)` combination, is it complete across its full active lifetime?

- Catches: "we never captured `options_chain` at all," "PERPETUALS for KRAKEN are missing an entire data_type."
- Rendered as a table ranked by worst-coverage shards.

Both views exist for both Layer 1 and Layer 2.

---

## Drill-down / roll-up hierarchy

One headline number at the top expands downward:

```
asset_group
  └── venue
        └── instrument_type
              └── data_type
                    └── day
```

This is the canonical drill-down hierarchy for both layers. Any UI or CLI that surfaces coverage numbers follows this
order. The `coverage.json` output schema (see below) carries `coverage_pct` + `all_shards_coverage_pct` at every node.

---

## Coverage formula

```python
reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)
```

`empty_confirmed` rows (legitimate absence, either source-returned-zero or known-gap) are **excluded from the
denominator** — they represent cells the system knowingly does not expect data for. Including them would deflate
coverage for venues with known non-trading days, pre-launch windows, etc.

> Compare to v1 formula: `coverage = (captured + empty_confirmed) / expected_universe` — this mixed legitimate-absence
> with the numerator, masking real holes.

---

## Measurability requirements (Phase 0)

v2 can only report real numbers if these six bugs are resolved. They are tracked in
`plans/active/honest_coverage_v2_instrument_denominator_2026_06_28.md` Phase 0.

| #   | Requirement                                                                                                      | Why it matters                                                                                                                                     |
| --- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Bucket selection: prefer freshest `written_at` / most-recent capture activity; LOUD-LOG which bucket won**     | Stale non-prd bucket was selected over live prd → 4× under-count (cefi reported 11.68% off a 20-day-stale manifest)                                |
| 2   | **prd/non-prd union: harness must union skeleton from non-prd + captures from prd** until Phase 2.6 consolidates | prd has captures but no `expected_unattempted` skeleton; non-prd has skeleton but stale captures — neither alone gives a trustworthy denominator   |
| 3   | **`instrument_type` canonical-uppercase, no data_type leakage, no blanks** (shard atom rule)                     | ~44% blank `instrument_type` in live cefi; `FUTURE` vs `futures_chain` etc. leak data_type values in; shard-breakdown view is unusable until fixed |
| 4   | **Failures resolved to real buckets via UAC `classify_venue_error()`** — NOT opaque `VENUE_FETCH_FAILED`         | 79% of 610K cefi `attempted_failed` rows carry the opaque catch-all; real cause unknowable                                                         |
| 5   | **`empty_confirmed` must carry typed `error_reason` — no blank absence**                                         | 11% of cefi empty cells (194K rows) untyped; violates honest-absence contract                                                                      |

The Phase 0 items are PREREQUISITES. v2 does not report numbers until they pass.

---

## Output format

`coverage.json` written to `gs://{PROJECT}-honest-coverage/{YYYY-MM-DD}/coverage.json`

Schema:

```json
{
  "generated_at": "2026-06-28T00:00:00Z",
  "layer_1": {
    "by_asset_group": {
      "<ag>": {
        "instrument_gates_download": true,
        "coverage_pct": 97.3,
        "missing_tuples": [{ "venue": "DERIBIT", "instrument_type": "OPTION", "data_type": "options_chain" }]
      }
    }
  },
  "layer_2": {
    "by_asset_group": {
      "<ag>": {
        "denominator_complete": false,
        "coverage_pct": null,
        "reachable_coverage_pct": 84.2,
        "by_venue": {
          "<venue>": {
            "coverage_pct": 91.5,
            "all_shards_coverage_pct": 88.0,
            "by_venue_data_type": {
              "<data_type>": {
                "coverage_pct": 95.0,
                "all_shards_coverage_pct": 92.0
              }
            }
          }
        }
      }
    }
  }
}
```

Key fields at each node:

- `coverage_pct` — reachable coverage for that node (formula above)
- `all_shards_coverage_pct` — coverage including `empty_confirmed` in the denominator (for completeness view)
- `instrument_gates_download: true` — Layer-1 is NOT 100%; Layer-2 is a lower bound only
- `denominator_complete: false` — same flag for Layer-2 node, drives the `⚠ DENOMINATOR INCOMPLETE` UI annotation

---

## Where the axes live (canonical)

| Axis                                                              | Canonical location                                                                     |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Instruments in the universe                                       | IS catalogue (`build_instrument_catalogue.py`; `mvp` is a stamped column)              |
| Data types expected per venue                                     | UAC `DATA_TYPES_BY_ASSET_GROUP` / `get_expected_data_types_for_venue`                  |
| MVP filter (which instruments are in-scope for the current phase) | UAC `mvp_scope.py`                                                                     |
| Shard atom per AG                                                 | `codex/02-data/availability-manifest-and-data-status.md` § per-asset-group shard atoms |

**Do NOT derive the expected universe from the manifest.** The manifest is the write ledger; the expected universe is
the IS catalogue × UAC matrix. Treating the manifest as both numerator and denominator circular-references honest
coverage.

---

## Relationship to existing manifest model

Layer 2 in Honest Coverage v2 is the 4-state model that already exists in the manifest (see
[availability-manifest-and-data-status.md](./availability-manifest-and-data-status.md)). v2 does NOT change the manifest
schema or write contract. It adds:

1. **Layer 1** as a first-class gate on top of Layer 2.
2. **Two views** (day-by-day + shard-breakdown) surfaced explicitly.
3. **A coverage formula** that correctly excludes `empty_confirmed` from the denominator.
4. **A structured output** (`coverage.json`) that carries both layers, both views, and the instrument-gates-download
   flag.

---

## Codex SSOTs

| Topic                                                     | SSOT                                                            |
| --------------------------------------------------------- | --------------------------------------------------------------- |
| 4-state `capture_status` write contract + manifest schema | `codex/02-data/availability-manifest-and-data-status.md`        |
| Honest absence — downstream handling (read side)          | `codex/02-data/honest-absence-downstream-handling.md`           |
| IS as SSOT for instrument universe                        | `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` |
| Data pipeline correctness hard rule                       | `codex/02-data/data-pipeline-correctness-hard-rule.md`          |
| Coverage baseline ratchet (v1 numbers, May 2026)          | `codex/02-data/honest_coverage_baseline_2026_05.md`             |
| Pipeline mode / source partitioning                       | `codex/02-data/pipeline-mode-partition.md`                      |
