---
title:
  "MTDS QG RED on LDR — 6 pre-existing failing unit tests (calendar-boundary future-skip + lighter candles + hyperliquid
  cache TTL)"
created: 2026-06-08
source:
  - "slot-6 tradfi-migration MTDS quality-gate run 2026-06-08 (full suite: 2662 passed / 6 failed / 17 skipped)"
priority: P2
status: active
---

> **✅ RESOLVED 2026-06-10.** All three test fixes landed (calendar ← 14d212a3, rate-limit/cache ← b1360a59, lighter
> OHLCV ← 0aebc2e7); commits are ancestors of main + LDR. ARCHIVE CANDIDATE.
>
> **ACKED-INTO-CODE** → archived 2026-06-10 — fixes shipped in market-tick-data-service@14d212a3 (calendar
> future-date-skip) + mtds@b1360a59 (hyperliquid cache TTL / rate-limit) + mtds@0aebc2e7 (lighter canonical OHLCV
> schema); all verified ancestors of origin/main. Both in-doc todos flipped `- [x] ✅` with SHAs — no deferred work
> migrates.

## What I found

A full `market-tick-data-service` `quality-gates.sh --no-fix` run (2026-06-08, surfaced while gating the tradfi
migration work) ran the **real** MTDS suite (2662 passed) and exposed **6 failing unit tests on LDR** — none related to
the tradfi migration; my changes (`migrate_tradfi_to_v9_canonical` / `attribute_tradfi_needs_attribution` / the UAC
tradfi chain validity-matrix widening) do NOT touch any of these surfaces, and their files were last committed by other
contributors (ComsicTrader 2026-05-15, the lighter bot 2026-05-07):

| Test                                                                                                           | Symptom                                                                                                                                                | Likely owner                                           |
| -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ |
| `test_calendar_boundaries.py::TestFutureDateSkipped::test_same_day_is_future`                                  | future-date-skip returns `{}` not `{"skipped":True,"reason":"future_date"}` (under `@freeze_time` — deterministic, so a real regression not flakiness) | calendar/capture logic (ComsicTrader new-queue item 9) |
| `test_calendar_boundaries.py::TestFutureDateSkipped::test_same_day_still_future_at_2359`                       | same                                                                                                                                                   | same                                                   |
| `test_calendar_boundaries.py::TestEndOfMonthRollover::test_jan_31_still_future_during_jan_31`                  | `assert {} == {"reason":"future_date","skipped":True}`                                                                                                 | same                                                   |
| `test_calendar_boundaries.py::TestEndOfYearRollover::test_dec_31_not_skipped_on_jan_1`                         | `assert {…} != {…}` — Dec 31 2026 wrongly treated as future when frozen-now is Jan 1 2027                                                              | same                                                   |
| `test_adapter_rate_limit_and_cache.py::TestHyperliquidResponseCacheTTLExpiry::test_expired_entry_returns_none` | cache TTL-expiry returns a value when it should be None                                                                                                | adapters/base-client (ComsicTrader new-queue item 10)  |
| `test_lighter_candles.py::test_candles_emits_canonical_ohlcv_schema`                                           | lighter OHLCV canonical-schema assertion fails                                                                                                         | lighter `_fetch_lighter_candles`                       |

> **Note on the hollow-sentinel interaction**: under this host's QG-collection bug (tracked in
> `master_data_canonicalisation_migration_catalogue_2026_06_07.md` § "🔴 LOCAL QG HARNESS collects the WRONG test
> suite") the MTDS QG often collects only PM's 6 integration tests and exits 0 — masking this standing red. This run
> collected the real suite (under host contention) and revealed it.

## Why it matters

- The MTDS commit-quality-boundary is RED on LDR for **every** slot shipping MTDS code — not just the tradfi work. A
  non-hollow `quality-gates.sh` run will not reach green until these 6 are fixed.
- The calendar `future-date-skip` regression is **data-pipeline-adjacent**: if the live capture path no longer skips
  future dates correctly, it could attempt-capture or mis-skip the current/boundary day. Worth a real diagnosis (test
  wrong vs code regressed) by the capture/calendar owner.

## Recommended decision

- Owner = the capture/calendar + adapters maintainer (ComsicTrader's new-queue items 9/10) + the lighter maintainer.
  Diagnose each (test-wrong vs code-regressed — read both sides) and fix on LDR.
- Independent of the tradfi migration: the tradfi migrator + attribution + matrix changes (mtds@51c604a4 / mtds@b56da26a
  / uac@df0acd06) are content-clean (their own tests are in the 2662 passed) and do not touch these surfaces, so they
  ship onto the already-red repo without worsening it.

- [x] ✅ [TEST] P1. Diagnose + fix `test_calendar_boundaries.py` future-date-skip (returns `{}` under freeze_time —
      regression in the future-skip logic OR a stale test). Repo: market-tick-data-service. parent_epic:
      mtds_mdps_master. — mtds@14d212a3 | verified 2026-06-10
- [x] ✅ [TEST] P2. Fix `test_adapter_rate_limit_and_cache.py` hyperliquid cache TTL-expiry + `test_lighter_candles.py`
      canonical OHLCV schema. Repo: market-tick-data-service. parent_epic: mtds_mdps_master. — mtds@b1360a59
      (rate-limit/cache) + mtds@0aebc2e7 (lighter OHLCV) | verified 2026-06-10
