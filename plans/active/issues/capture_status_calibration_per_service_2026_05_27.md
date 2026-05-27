---
title: "Manifest capture_status calibration — per-service write-path audit"
created: 2026-05-27
author: harsh-side (operator-directed)
name: capture_status_calibration
source:
  - plans/active/features_calc_efficiency_and_correctness_2026_05_27.md
  - plans/active/features_service_e2e_pipeline_test_2026_05_26.md
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/honest-absence-downstream-handling.md
  - plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md
locked_by: live-defi-rollout
priority: P1
status: active
---

## What this is

Operator-raised theme (2026-05-27): the manifest `capture_status` values (`captured` /
`empty_confirmed` / `attempted_failed` / `expected_unattempted`) are an **ongoing cross-service concern** that must be
**properly calibrated per service** — for each service + condition, *which status should propagate?*

## The principle (operator, verbatim intent)

> `empty_confirmed` is the **LAST** status — written only after **all other possibilities are ruled out** and we are
> sure the data is **genuinely not present**: a holiday, no coverage from the source, or the instrument/contract simply
> did not exist for that window (e.g. the future was not listed for this underlying at that time).
>
> If the real situation is **"data not yet downloaded"** or **"error during backfill"**, the data **is supposed to be
> there** but is inaccessible for some reason — so we **cannot** say it is genuinely absent and we **must NOT** write
> `empty_confirmed`. That is a different status (the data is owed; it is a dependency / backfill gap, not an absence).

Corollary surfaced same day (operator): a **future cannot exist without a spot** for its underlying — so for
spot+future-pair features (e.g. `futures_basis`), the contradiction is "future present, spot absent"; the legitimate
absence is "**spot present, future absent**" (the future was not listed for that underlying in that window).

## Why it matters

- A wrong `empty_confirmed` is a **silent correctness lie**: downstream (and the Batch-Live Reconciliation Service
  Stage-0 `manifest_reason_check`, which compares batch vs live `capture_status`/`error_reason`) treats it as "we
  checked, there is genuinely nothing" — masking a backfill/dependency gap that should have been retried or flagged.
- A **missing manifest row** (silent skip) is equally wrong — it is indistinguishable from a crash.

## Status decision rule (target — to encode per write-path)

| Real situation | Correct status | Reason / notes |
|---|---|---|
| Data genuinely absent (holiday, no source coverage, contract not listed in window) | `empty_confirmed` | typed `EmptyConfirmedReason` (e.g. `EXPECTED_NO_PAIRED_INSTRUMENT`, `SOURCE_RETURNED_ZERO`, holiday/coverage reasons). LAST resort. |
| Upstream produced nothing but should have (not downloaded yet, dependency not ready) | NOT `empty_confirmed` → `expected_unattempted` / dependency-gate skip | data is **owed**; retry / backfill, do not confirm-empty |
| Attempted and errored (fetch/backfill error) | `attempted_failed` (+ `stack_trace`) | transient/real failure; not an absence |
| Wrote rows | `captured` | normal |

## Live instances (concrete, already found)

1. **delta_one 4h/24h (CeFi)** — does NOT land because MDPS **1h candles are missing for 2026-04-14→04-30** (only
   05-01→05-04 contiguous). This is **"data supposed to be there, not yet backfilled"** → must surface as a
   dependency/backfill gap, **NOT** `empty_confirmed`. The features code now correctly fast-fails. UNBLOCK = MDPS 1h
   backfill (see efficiency plan 1.0b). This is the textbook example of the principle above.
2. **volatility `futures_basis`** — emitted **no parquet AND no manifest row** when the future leg was absent (silent
   skip = violation regardless). Calibration: distinguish "**future never listed for this underlying in this window**"
   (→ `empty_confirmed`, typed reason) from "**future data not downloaded yet**" (→ dependency gap). Do NOT reflexively
   write `empty_confirmed`; determine the cause first.

## The ask (work to scope)

Per-service write-path audit: for each producer service — **instruments-service, MTDS, MDPS, features delta_one /
volatility / cross_instrument / multi_timeframe** — enumerate every emission path and confirm it writes the status the
rule above prescribes, with `empty_confirmed` gated behind genuine-absence confirmation (and a typed reason). Compose
with the existing honest-absence SSOT (`codex/02-data/honest-absence-downstream-handling.md` § Reason taxonomy + §
Per-service consumer-class audit) — extend it with the **producer-side** decision rule, and wire QG checks where
feasible (a silent no-row for an in-scope shard should fail).

**Open scope question for operator:** how wide/deep should the first pass be — (a) just the features services touched
this week, (b) all features + the 3 upstream data services, or (c) workspace-wide producer audit?
