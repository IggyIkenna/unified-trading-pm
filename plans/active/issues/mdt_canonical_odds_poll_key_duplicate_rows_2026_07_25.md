---
doc_type: issue
title:
  30/200 sampled canonical sports MDT (market-tick-data) odds objects carry duplicate rows on the poll key (event,
  market, outcome, bm_time, price, fetch_utc) — independent of the OR-5b legacy→canonical cutover
summary: >-
  During the OR-5b legacy→canonical MDT investigation, a 200-object sample of canonical
  `market-data-tick-sports-prd-central-element-323112` odds objects found 30/200 (15%) already carry duplicate rows on
  the poll key `(event, market, outcome, bm_time, price, fetch_utc)`. This is a pre-existing data-quality defect in
  canonical's own captured population, unrelated to the legacy-bucket recovery the investigation was scoped around — the
  32-day legacy→canonical recovery that would have de-duplicated ON WRITE for its own merged rows (step 2 of that
  procedure) has since been ABANDONED (operator ruling 2026-07-25, source legacy bucket deleted 2026-07-17 before
  recovery ran — see `mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`), so no mechanism currently plans to
  touch the 30/200 sampled duplicates or the wider canonical population they were sampled from. This doc exists purely
  to track the standalone finding + the still-open remediation now that the only planned dedup path is gone.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [mdt, sports, odds, duplicate-rows, poll-key, data-correctness, canonical]
related:
  [
    /plans/active/issues/mdt_legacy_canonical_row_gap_2026_07_16.md,
    /plans/archive/issues/mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
priority: P3
parent_epic: sports_master
source:
  "Loose-end #5 of the OR-5b legacy→canonical MDT investigation (mdt_legacy_canonical_row_gap_2026_07_16.md, 2026-07-16
  read-only pass), documented per that doc's own triage as requiring a standalone issue doc; filed as
  sports_satellite_ao_dispatch_batch2-013 (2026-07-25, slot 9)."
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# Canonical sports MDT odds objects — 30/200 sampled carry duplicate rows on the poll key

## What I found

While investigating the OR-5b legacy→canonical MDT row gap (see `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`), a
200-object sample of **canonical** (`market-data-tick-sports-prd-central-element-323112`) odds objects found **30/200
(15%) already carry duplicate rows** on the poll key `(event, market, outcome, bm_time, price, fetch_utc)` — i.e. more
than one row sharing the same event/market/outcome/bookmaker-timestamp/price/fetch-timestamp tuple within the same
object.

This is **independent of the legacy→canonical cutover** the parent investigation was scoped around: the duplicates are
already present in canonical's own captured population, not something the (now-abandoned) 32-day recovery merge would
have introduced. The parent doc's step 2 spec ("de-dup on write on the poll key `(event,market,outcome,bm_time,price)`")
would only have de-duplicated the _newly merged_ rows for that specific 32-day recovery — it never covered the
already-existing duplicates in the wider canonical population this 200-object sample was drawn from.

**The only planned remediation path for this finding is now gone.** The 32-day legacy→canonical recovery has been
**ABANDONED** (operator ruling 2026-07-25 — the source legacy bucket was deleted 2026-07-17T17:05:17Z before STEP 1 ever
ran; see `issues/mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`). That recovery's step 2 was the only concrete
dedup-on-write mechanism named anywhere in the investigation, and it will never execute.

## Why it matters

- Duplicate rows on the poll key double-count identical price observations in any per-book/per-market aggregate
  (dispersion, spread, book-depth-adjacent stats) that reads these objects without its own dedup step — a data-quality
  defect for downstream consumers, not just a storage inefficiency.
- 15% of a 200-object sample is not a rounding artifact; it implies a real fraction of the canonical odds corpus is
  affected, though the true population-wide rate and root cause (writer-side retry double-write? multiple capture passes
  merged without a dedup step? a genuine re-poll landing on an identical price?) were never diagnosed — the parent
  investigation was scoped to the legacy/canonical row-count gap, not to root-causing this defect.
- Without a fix, any future writer/merge into this population risks perpetuating or compounding the duplication (the
  same failure mode the abandoned recovery's step 2 was meant to guard against for its own writes).

## Recommended decision

1. **Root-cause the duplication mechanism** on a fresh sample (the original 30/200 sample was not preserved as a
   reproducible artifact) — determine whether it's a writer-side retry/multi-write defect (in which case the writer
   needs a dedup-on-write guard, mirroring the `player_stats` writer-side de-dup fix shipped in
   `instruments-service@210d4567` for a structurally similar defect) or a merge-time artifact from an unrelated prior
   campaign.
2. **Measure the population-wide rate** via the availability manifest (single-walk discipline — do not re-walk the
   corpus ad hoc) to size the actual scope before committing to a full backfill-style de-dup rewrite.
3. **If population-wide de-dup is warranted**, it is a scoped rewrite job analogous to the `player_stats` de-dup rewrite
   (`instruments-service@210d4567`, `scripts/dedup_canonical_player_stats_2026_07_25.py`) — read affected objects,
   de-dup on the poll key, re-write, verify by content (0 duplicates remain).
4. This is a genuinely separate, currently-unowned piece of work now that the recovery plan it was folded into is
   abandoned — recommend a new `[DATA]` fix todo be picked up against this doc rather than assuming it is covered
   elsewhere.

- [ ] [DATA] P3. **Root-cause + measure the population-wide rate** of poll-key duplicate rows in canonical sports MDT
      odds objects (repo: market-tick-data-service). **Done when**: a fresh reproducible sample (or manifest-driven
      population measurement) confirms the duplication mechanism and reports the true affected-object rate/count.
- [ ] [DATA] P3. **De-dup canonical sports MDT odds objects on the poll key**
      `(event, market, outcome, bm_time, price,     fetch_utc)`, if the population-wide measurement above shows material
      scope (repo: market-tick-data-service — new one-off script mirroring
      `instruments-service/scripts/dedup_canonical_player_stats_2026_07_25.py`'s safe-no-op-on-clean-objects pattern).
      **Done when**: a re-run over the affected population confirms 0 poll-key duplicates remain.

## Progress Log

**2026-07-25 (slot 9)** — Filed per `sports_satellite_ao_dispatch_batch2-013` (this todo is documentation-only; the fix
todos above are new, standalone work, not yet dispatched or claimed by any other plan).
