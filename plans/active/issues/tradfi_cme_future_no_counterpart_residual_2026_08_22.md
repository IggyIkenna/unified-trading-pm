---
doc_type: issue
title: >-
  7,926 stale tradfi CME instrument_type=FUTURE manifest rows have NO live bundle-grain counterpart — left
  deliberately untouched by the D2 retire pass, needs its own per-row disposition
summary: >-
  Follow-up split off `tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md` after that doc's D2-approved retire
  todo executed 2026-08-22 (`market-tick-data-service@53e6d971ce`,
  `scripts/one_offs/retire_tradfi_cme_future_stale_manifest_rows_2026_08_22.py --apply`): of the 880,933 stale
  `venue=CME`/`instrument_type=FUTURE`/populated-`underlying`/blank-`instrument_id` rows, 873,007 had a live
  `combo`/`futures_chain`/`options_chain` counterpart at the same `(underlying, data_type, date)` key and were
  retired; **7,926 rows had NO counterpart at all** and were deliberately left in the manifest (content-verify,
  delete-safety Part 2 — a row with no counterpart may be the ONLY record of that cell; dropping it without proof
  would be a real data loss, not a dedup). This population has grown from 649/76,454 combos measured 2026-08-10 to
  7,926/880,933 as of 2026-08-22 (still ~0.90% of the stale population, not an anomaly, but not investigated either).
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tradfi, manifest, data-correctness, cme, instrument_id, blank-id, follow-up]
related:
  [
    /plans/active/issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-22"
author: slot-6 worker
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source:
  [
    "split from tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md's D2-approved retire-todo execution,
    slot-6 worker session 2026-08-22",
  ]
context_scope:
  [
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/scripts/one_offs/retire_tradfi_cme_future_stale_manifest_rows_2026_08_22.py,
  ]
---

# 7,926 stale tradfi CME `instrument_type=FUTURE` rows with no live counterpart

## What I found

Executing the D2-approved retire todo in `tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md`
(`market-tick-data-service@53e6d971ce`), the content-verify pass (build the set of live
`combo`/`futures_chain`/`options_chain` `(underlying, data_type, date)` keys, only retire a stale row if its own key
is in that set) found **7,926 of the 880,933 stale rows have no such counterpart** — up from 649/76,454 combos
measured 2026-08-10 (a different, coarser unit — key-combos vs rows — but the same population). These rows were
LEFT UNTOUCHED by the retire pass (verified: post-apply live-manifest recount = 7,926, matching this residual
exactly).

## Why it matters

A row with no live counterpart is either (a) the ONLY surviving record of that `(date, venue, underlying,
data_type)` cell — in which case it must be repaired in place (populate a real per-row `instrument_id`, or retype it
to the correct bundle-grain `instrument_type` if it genuinely is bundle-grain data that never got a
`combo`/`futures_chain`/`options_chain` counterpart written), never dropped — or (b) a genuinely stale/duplicate row
whose counterpart was itself separately lost/never captured, in which case the underlying gap is the real problem to
fix. Either way, dropping these 7,926 rows without first resolving which case applies would violate delete-safety
Part 1/2 (five-part proof) — this is exactly why the retire script left them untouched rather than guessing.

## Todos

- [ ] [DATA] P3. Sample and classify the 7,926 no-counterpart rows (venue=CME, instrument_type=FUTURE, populated
      underlying, blank instrument_id, no combo/futures_chain/options_chain counterpart at the same
      (underlying, data_type, date)) — determine whether each is case (a) (only surviving record — repair via a real
      per-row instrument_id backfill or a retype) or case (b) (a genuinely-orphaned duplicate whose real counterpart
      was itself never captured or was separately dropped). Repo: market-tick-data-service. **Done when**: a dated
      finding is recorded in this doc's Progress Log with the classification breakdown (case-a count / case-b count)
      and enough detail to scope a fix without re-investigating from scratch.
- [ ] [DATA] P3. Once classified, scope and execute the appropriate fix per case: case-(a) rows get a per-row
      `instrument_id`/retype backfill (never a delete); case-(b) rows get investigated for the missing counterpart's
      true disposition (was it captured elsewhere under a different key shape, or is it a genuine gap needing a
      fresh backfill) before any delete decision — any eventual delete needs its own fresh five-part-proof pass per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`, this doc's D2 disposition does not carry forward
      to this population. Repo: market-tick-data-service. **Done when**: live-manifest recount of this exact
      7,926-row population (or its then-current size) reaches 0, OR each remaining row carries a recorded
      `no-migrate-first`/`no-still-authoritative` disposition explaining why it is not a defect.

## Progress Log

- **slot-6 worker 2026-08-22** (split from the parent D2 retire execution): filed this issue with the measured
  7,926-row residual; population confirmed via the retire script's own round-trip verify
  (`market-tick-data-service@53e6d971ce`), not yet investigated further.
