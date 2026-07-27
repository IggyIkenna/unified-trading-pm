---
doc_type: issue
title:
  TradFi instrument_type casing re-drift found 2026-07-27 — the 2026-07-25 100% directive is no longer literally true
summary: >-
  A fresh live read of the tradfi availability_index (2026-07-27), taken while closing an adjacent semantic-relabel
  todo, found ~63,143 tradfi manifest rows still carrying a lowercase instrument_type — materially more than the
  45,428-row residual migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py closed (and self-verified 0 residual on)
  the same day. Either an active writer path still bypasses canonicalize_tradfi_manifest_itype, or the earlier
  self-verify sampled a stale consolidator-merge window. Diagnose via written_at freshness before re-running the casing
  script blindly.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [tradfi, casing, instrument-type, manifest, re-drift, data-correctness]
related:
  [
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-27
priority: P1
parent_epic: tradfi_master
author: agent-orchestrator worker slot-9
assigned_vm: planning
source: [tradfi_manifest_content_recovery_completion_2026_07_24.md]
resolved_by:
locked_by:
---

## What I found

While closing `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s semantic-mislabel/null-blank todo
(mtds@132ea6b1), a fresh live read of the tradfi `availability_index.parquet` (2026-07-27) found ~63,143 tradfi rows
still carrying a LOWERCASE `instrument_type`:

| value     |  count |
| --------- | -----: |
| equity    | 28,914 |
| combo     | 23,428 |
| future    |  4,307 |
| etf       |  5,372 |
| index     |    790 |
| spot_pair |    316 |
| FUTURES   |     16 |
| UNKNOWN   |  2,902 |

This is materially larger than the 45,428-row residual `migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py` was
built to close (and did close, per that script's own fresh live re-verification the same day: "SELF-VERIFY:
4,988,822/4,988,822 UPPERCASE" — 0 non-UPPERCASE residual at that point).

## Why it matters

`cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md` set a literal-100% UPPERCASE bar for tradfi. Either the
writer-side fix (`_tradfi_manifest_canon.py::canonicalize_tradfi_manifest_itype`, wired into `venue_fetch.py` +
`sentinels.py`) has a gap some capture path still bypasses, or a third write path (not covered by either prior audit) is
re-introducing lowercase rows. This directly affects: (a) the semantic-relabel script this issue was found alongside —
those lowercase rows are OUTSIDE its `_TOUCHABLE_STORED_TYPES` scope (which matches exact-case
`{FUTURE, OPTION, COMBO, ...}` — a `future`/`combo` typed row is silently skipped by that script too, not just the
casing script); (b) any downstream consumer trusting the UPPERCASE-enum contract.

## Recommended decision

Diagnose the source before re-running the casing script blindly a third time (which would fix the symptom again without
closing the actual re-drift gap):

1. Check `written_at` on a sample of the lowercase rows — if recent (post the 2026-07-25 writer fix ship), it is an
   ACTIVE re-drift (writer bug not yet found); if old, it's evidence the 2026-07-25 self-verify sampled a
   consolidator-merge window that hadn't caught up to the full corpus yet (a staleness artifact, not a new bug).
2. If active: find the write path that still bypasses `canonicalize_tradfi_manifest_itype` (grep every
   `record_captured`/`ManifestWriter.add` call site for tradfi that doesn't route through it) and fix it there, THEN
   re-run the casing restamp for the residual.
3. If stale: just re-run `migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py --apply` again (idempotent,
   already-proven-safe) to close the residual.

- [ ] [DATA] P1. Diagnose the tradfi instrument_type casing re-drift per the recommended decision above (check
      `written_at` freshness, find/fix any writer path still emitting lowercase, re-run the casing restamp for the
      residual). (repo: market-tick-data-service)
