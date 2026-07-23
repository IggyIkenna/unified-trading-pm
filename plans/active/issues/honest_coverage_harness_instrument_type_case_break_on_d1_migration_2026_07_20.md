---
doc_type: issue
title: Honest-coverage v2 harness reads instrument_type lowercase — the D1 UPPERCASE migration will zero-match it
summary:
  The v2 honest-coverage harness reads the manifest `instrument_type` column at its current LOWERCASE writer grain
  (`spot`, `perpetuals`, `pool`, `lending`, …), documented as SSOT in honest-coverage-model.md. The 2026-07-20 D1 ruling
  makes the canonical manifest `instrument_type` COLUMN UPPERCASE. When the D1 migration flips the writers to the
  UPPERCASE enum, the harness's lowercase reads/matches will silently zero-match every migrated shard unless it
  normalises case. This is a latent correctness hazard gated on the D1 migration — not a live break today.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [features-service, deployment-api, unified-trading-library]
scope: [engineer, admin]
tags: [honest-coverage, instrument-type, case, d1-ruling, migration-pending, coverage-harness, ssot-contradiction]
related:
  [
    ../data_pipeline_reconciliation_skill_2026_07_20.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /codex/02-data/canonical-cutover-register.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on:
source:
  found by the /data-pipeline-reconciliation post-phase consistency audit (todo 19), 2026-07-20 — reported as the one
  substantive contradiction it refused to blind-fix
---

# Honest-coverage v2 harness reads `instrument_type` lowercase — D1 UPPERCASE migration will zero-match it

> **⚠️ BIG FINDING (SSOT contradiction + latent data-correctness).** Operator-notified 2026-07-20. Not a live break
> today; it arms when the D1 `instrument_type`-column UPPERCASE migration runs.

## The contradiction

- `/codex/02-data/honest-coverage-model.md:154-157` states, as CK3-certified SSOT for the v2 coverage harness's read
  grain: _"`instrument_type` is a **real lowercase writer-grain column** (`spot`, `perpetuals`, `options_chain`,
  `futures_chain`, `pool`, `lending`, `prediction_market`, …) — **NOT the UPPERCASE catalogue enum**. The v2 harness
  MUST read `instrument_type`…"_
- The 2026-07-20 **D1** ruling (`plans/active/data_pipeline_reconciliation_skill_2026_07_20.md` § D1 +
  `/codex/02-data/cross-asset-canonical-target-ssot.md` §7/§11) makes the canonical manifest `instrument_type` **COLUMN
  UPPERCASE** (catalogue enum wins).

These describe the **same column** in opposite cases. Both are internally right for their moment: honest-coverage
describes **current reality** (writers emit lowercase today), D1 describes the **target**. The gap between them is the
`migration_pending` window.

## Why it is a hazard, not just drift

The harness matches manifest rows by `instrument_type` value. It reads lowercase. When the D1 migration flips the
writers (and rewrites the historical column) to the UPPERCASE enum, every migrated shard's `instrument_type` stops
matching the harness's lowercase expectation → the shard is counted as **not covered** → coverage silently craters for
migrated asset_groups while the data is fully present. Same fail-closed / silent-zero class as the other case-sensitive
matchers found in this campaign (the sports MDPS `data_type={data_type}/` substring match; the MTDS `--leagues` filter).

## Correct resolution (do NOT blind-flip the doc)

Flipping honest-coverage-model.md to UPPERCASE now would break the harness against **today's** lowercase data (the exact
OOM/zero-match risk the consistency audit flagged). The resolution is case-robustness across the migration, not a doc
flip:

1. Make the v2 harness's `instrument_type` read/compare **case-insensitive** (normalise both sides to a single case at
   read time) so it is correct in BOTH the pre- and post-D1-migration states.
2. Add a `migration_pending`-window note to `honest-coverage-model.md:154-157`: the column is lowercase **today** (what
   the harness reads); the D1 **target** is UPPERCASE; the harness normalises case so the D1 migration does not zero it.
3. Sequence: this normalisation must land **before** the D1 `instrument_type`-column migration flips any writer/history
   — otherwise coverage craters on the first migrated asset_group.

## Todos

- [ ] 1. [DATA] P1. Confirm the exact harness read/compare site(s) for `instrument_type` (grep the v2 coverage harness +
      `read_availability_index` callers that filter/group by `instrument_type`); enumerate every case-sensitive match.
- [ ] 2. [CODE] P1. Make those reads/compares case-insensitive (normalise at read); add a regression test that a shard
      whose column is UPPERCASE and a shard whose column is lowercase both count as covered.
- [ ] 3. [DATA] P1. Add the `migration_pending`-window note to `honest-coverage-model.md:154-157` (today lowercase /
      target UPPERCASE / harness normalises), with a dated annotation and a pointer to this issue.
- [ ] 4. [REVIEW] P1. Gate: this normalisation lands + is proven green BEFORE the D1 `instrument_type`-column migration
      flips any writer or rewrites history. Cross-link this issue from the D1 migration todo so the ordering is
      enforced.
