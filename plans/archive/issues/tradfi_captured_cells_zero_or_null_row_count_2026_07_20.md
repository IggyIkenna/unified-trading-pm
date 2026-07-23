---
doc_type: issue
title: "70% of TRADFI `captured` manifest cells carry row_count = 0 or null (1,135,339 of 1,615,859)"
summary: >-
  A backfill-readiness sweep measured 1,135,339 of 1,615,859 TRADFI `captured` availability cells (70.3%) with
  `row_count` either 0 or null — spanning CME / NYSE / NASDAQ `ohlcv_*` and FX, where ALL 4,266 FX `ohlcv_24h` captured
  cells are zero. Exactly one of two things is true and they need opposite fixes — either (A) `row_count` is not
  reliably stamped at the per-instrument shard atom (a manifest-metadata defect, the data is fine but the coverage
  numbers lie), or (B) these are genuinely empty parquets recorded as `captured` (a HARD-RULE honest-absence violation,
  "empty placeholder rows that look populated"). Both are P1 — (A) makes every coverage/ETA number untrustworthy, (B) is
  banned-pattern data corruption. A peer independently confirmed `row_count` is unreliable and `capture_status` is the
  correct predicate, which makes (A) the leading hypothesis. The counts were snapshotted WHILE the canonical-path
  migration was running, so step 1 is a re-measure on a quiesced bucket before any conclusion.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, unified-api-contracts, deployment-api]
scope: [engineer, admin]
tags:
  [
    manifest,
    row-count,
    honest-absence,
    data-correctness,
    capture-status,
    shard-atom,
    honest-coverage,
    backfill-readiness,
  ]
related:
  [
    tradfi_consolidated_closeout_2026_07_18,
    tradfi_canonical_path_migration_design_2026_07_19,
    tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20,
  ]
created: 2026-07-20
priority: P1
parent_epic: tradfi_master
source: "Backfill-readiness manifest sweep, 2026-07-20 (snapshot taken during the in-flight canonical-path migration)"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by:
---

# TradFi `captured` cells with row_count = 0 or null

> **🟡 MEASUREMENT CAVEAT (read first).** The numbers below were snapshotted while the 20-shard canonical-path migration
> and a catalogue sweep were running against the tradfi tick bucket. A migration in flight can produce transiently
> double-counted or half-written index rows. **Re-measure on a quiesced bucket before concluding anything or shipping
> any fix.** The re-measure is todo 1 and it gates every other todo in this doc.

## The measurement

| Slice                         | Captured cells | row_count 0-or-null |     % |
| ----------------------------- | -------------: | ------------------: | ----: |
| TRADFI total                  |      1,615,859 |           1,135,339 | 70.3% |
| FX `ohlcv_24h`                |          4,266 |               4,266 |  100% |
| CME / NYSE / NASDAQ `ohlcv_*` |    (remainder) |         (remainder) |     — |

**Re-measured 2026-07-20 (tick 26) on a post-force-rebuild manifest — the defect is CONFIRMED and slightly worse on the
MVP slice.** Snapshot T1 `2026-07-20T14:47:40Z`, re-measured T2 `2026-07-20T15:09:03Z` (peer force-rebuild landed
between; both agree): restricted to the MVP data types `{ohlcv_1m, ohlcv_1s, ohlcv_24h}`, **680,088 of 919,180
`captured` cells = 74.0%** carry `row_count` 0/null. So the defect is not an artifact of the in-flight canonical-path
migration the original snapshot was taken during — it survives a full manifest rebuild unchanged, which **retires the
"re-measure on a quiesced bucket first" caveat** and promotes hypothesis (A) further.

**Scope correction — this issue does NOT invalidate the tradfi backfill ETA.** The tick-22 remaining-work inventory was
audited at tick 26 and already used `capture_status ∈ {expected_unattempted, attempted_failed}` as its predicate;
`row_count` appears nowhere in that derivation. Re-running it reproduced 638,446 todo / 182,407 below-floor / 456,039
backfillable against the reported 638,440 / 182,407 / 456,033 (delta +6 cells from intervening writes). The ETA was
superseded at tick 26 for an unrelated reason (the `resolved[:cap]` denominator truncation + a measured per-date cost
model) — see `tradfi_consolidated_closeout_2026_07_18` tick 26. What this issue DOES still invalidate is any
coverage/completeness percentage computed from `row_count`.

FX `ohlcv_24h` at a clean 100% is the most diagnostic slice in the table: a uniform 100% is the signature of a CODE PATH
that never stamps the field, not of a market that happened to be empty. A genuine-absence explanation would have to
argue that every FX daily candle ever captured had zero rows, which is false on its face — FX daily candles are the one
tradfi shard that is essentially never empty on a weekday.

## Independent corroboration (peer finding, 2026-07-20) — hypothesis (A) is now the leading one

A peer agent independently reached the same conclusion from a different direction while auditing the write path:
**`row_count` is NOT a reliable predicate for "this cell has data" — `capture_status` is the correct predicate.** That
is exactly hypothesis (A) below, arrived at without reference to this measurement, which makes (A) substantially more
likely than (B) as the dominant class.

Two consequences worth stating explicitly, because they change what other agents should do TODAY, before this issue is
resolved:

1. **Any coverage / completeness / remaining-work query must filter on `capture_status`, not on `row_count > 0`.** A
   `row_count`-based query silently under-counts captured data by up to the 70% measured here. Treat any ETA or coverage
   % already computed off `row_count` as invalid until re-derived.
2. **A `row_count=0` on a NON-captured row is correct and honest, not a bug.** Sibling issue
   `mdps_derivative_ticker_candle_schema_violation_2026_07_20.md` records 140 `attempted_failed` /
   `SCHEMA_VALIDATION_FAILED` cells at `row_count=0` — that is the honest-absence contract working as designed. The
   defect in THIS doc is specifically `row_count` 0-or-null on rows whose `capture_status` is **`captured`**, which is a
   contradiction in terms. Do not conflate the two when triaging.

This does not close the doc: (A) still needs the writer-side fix and the corrective re-stamp, and the direct object
check below is still required to rule out a (B) subset hiding inside the 70%.

## The two hypotheses (mutually exclusive, opposite fixes)

**(A) `row_count` is not stamped at the per-instrument shard atom.** The writer records `capture_status=captured` but
leaves `row_count` unset / 0 for some writer paths. The parquets on GCS are fine; the manifest metadata is incomplete.
Consequence: every honest-coverage %, every "cells remaining" figure, and every backfill ETA derived from `row_count` is
wrong. This is the hypothesis the FX 100% slice most supports.

**(B) Genuinely empty parquets recorded as `captured`.** The shard wrote a 0-row parquet and the writer called
`record_captured` on it. This is the explicitly BANNED "empty placeholder rows that look populated" pattern (CLAUDE.md §
banned patterns; `codex/02-data/honest-absence-downstream-handling.md`) — an empty shard must go through `record_empty`
/ `record_failed` with a typed reason and fetch-evidence, never `record_captured`.

The two are distinguishable by a direct object check: sample N cells that report `row_count` 0-or-null, resolve each to
its GCS parquet, and read the ACTUAL row count off the file.

- Parquet has rows → hypothesis **(A)**, a metadata-stamping defect.
- Parquet has zero rows (or is absent) → hypothesis **(B)**, an honest-absence violation.

A mixed result means both defects are live and both need fixing; do not stop at the first one found.

## Why this is P1

Per CLAUDE.md, data-pipeline correctness is the heartbeat, and a RED data audit FREEZES layer-N+1 work
(foundation-completion-gate). Under **(A)** the tradfi MVP backfill cannot be honestly declared complete because the
completion metric itself is unreliable. Under **(B)** the corpus contains cells that claim data they do not have, which
silently corrupts every downstream consumer (features → ML → strategy) with no loud failure. Either way this gates the
tradfi MVP-backfill-ready call in `tradfi_consolidated_closeout_2026_07_18`.

## Todos

- [ ] [DATA] P0. **Re-measure on a quiesced bucket.** Wait for the canonical-path migration + catalogue sweep to finish,
      then recount `captured` cells with `row_count` 0-or-null, broken out by (venue, data_type, source, pipeline_mode).
      Record the numbers here. If the 70% does not reproduce, close this doc with the corrected measurement and a note
      on what the migration artefact was — do NOT leave it open on stale numbers.
- [ ] [DATA] P0. **Disambiguate (A) vs (B) by direct object check.** Sample >=200 zero/null-`row_count` cells stratified
      across CME / NYSE / NASDAQ / FX, resolve each to its GCS parquet, and read the real row count off the object.
      Report the (A)/(B)/mixed split with per-slice counts. This is the finding that decides every todo below, so do it
      before writing any fix.
- [ ] [BACKEND] P1. **If (A) — make `row_count` mandatory at the shard atom.** Find every `record_captured` callsite
      that can omit a real count and require it, mirroring the existing `source=` crosscutting treatment. A captured row
      with no row_count should be a LOUD writer-side error, not a silent 0.
- [ ] [BACKEND] P1. **If (B) — route empty shards to `record_empty` with typed reason + fetch-evidence,** never
      `record_captured`. Then file the corrective reclassification pass over the affected cells; a wrong
      `capture_status` is not fixed by the next backfill because the freshness-skip treats it as already done.
- [ ] [DATA] P1. **Backfill/repair the affected cells** once the class is known, and re-verify the counts drop. "Fixed
      the writer" is not done — the existing wrong rows stay wrong until they are re-stamped.
- [ ] [BACKEND] P2. **Add the regression guard.** A QG/gate assertion that a `captured` cell carries a positive
      `row_count`, ratcheted so the baseline can only go DOWN.

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — 4-state `capture_status`, shard-atom identity.
- `codex/02-data/honest-absence-downstream-handling.md` — the honest-absence contract; empty must never look captured.
- `codex/02-data/data-pipeline-correctness-hard-rule.md` — audits fixed in FULL; RED freezes layer N+1.
- `codex/02-data/honest-coverage-model.md` — the coverage denominator this measurement feeds.
