---
title: "B-015 Smoke (c) — features-onchain VM ran past infra; calculator + orchestrator bugs surfaced"
created: 2026-05-17
author: ikenna-slot-3
resolved: 2026-05-17
resolution: SHIPPED — both follow-up bugs fixed by slot-1-main at `features-service@d687df7d` (macro_sentiment now skipped in batch mode; `_process_groups` exception catch broadened from ValueError-only to Exception so subsequent feature_groups continue on failure). VM 8 (`features-onchain-defi-20260517-025847`) wrote real parquets for all 5 days × lst_yields — B-015 paper-trade gate UNBLOCKED.
locked_by: live-defi-rollout
locked_since: 2026-05-17
severity: P0 — was blocking B-015 paper-trade gate; resolved 2026-05-17 02:08 UTC
---

# B-015 Smoke (c) — VM 5 (`features-onchain-defi-20260517-005747`) findings

**Setup pin/routing fix WORKED**: deployment-service@b3b4691 (features-backfill → --no-deps) +
risk-and-exposure-service@83b10e0 (UAC pin) + ml-training-service@876f0e5 (UTL pin) together unblock the VM startup.
Service installed, bootstrapped, and ran.

**Result**: VM started + ServiceBootstrap STARTED + 11 feature groups identified for DEFI. Stopped after 7s only
processing 2 of 11 feature groups for 1 of 5 dates.

## Per-feature-group outcomes

| Feature group   | Date       | Outcome                | Detail                                                                    |
| --------------- | ---------- | ---------------------- | ------------------------------------------------------------------------- |
| macro_sentiment | 2026-04-15 | FEATURE_WRITE_REJECTED | `LookaheadBiasError: observation at 2026-04-19 is after as_of=2026-04-16` |
| lending_rates   | 2026-04-15 | empty_or_failed        | 0 rows, no FEATURE_WRITE_REJECTED. Cause unclear from events.             |
| (other 9)       | —          | not attempted          | VM STOPPED after lending_rates                                            |

## Findings

1. **LookaheadBiasError in macro_sentiment** — DefiLlama TVL API returns current data; the calculator fetches it as-of
   2026-04-19+, but the as_of cutoff is 2026-04-16 (next-day for 2026-04-15 batch row). The calculator needs to filter
   or fetch historical (point-in-time) TVL data. Slot 2 (features-service onchain owner) should fix.
2. **Early-exit after first feature-group "empty_or_failed"** — VM stopped after lending_rates processed 0 rows for
   2026-04-15. Either:
   - Orchestrator exits on any "empty_or_failed" (anti-pattern — should continue to next group)
   - The "stop after first group" is intended (each backfill VM runs only 1 feature_group at a time? doesn't match the
     `--feature-group ALL` arg)
   - There's a separate exception not surfaced as an event
3. **B-015 chain step (c) STILL BLOCKED** by these two features-service issues, not by infra anymore.

## Action items

- [x] ✅ **[BUG] P0. macro_sentiment lookahead bias FIXED** — slot-1-main 2026-05-17 02:50 UTC at `features-service@d687df7d`. Orchestrator now emits `FEATURE_GROUP_SKIPPED_BATCH_INCOMPATIBLE` when `start_date.date() < today`. Backfill no longer attempts the impossible (live-only data sources have no historical archive). Live mode unaffected.
- [x] ✅ **[BUG] P0. Early-exit ROOT-CAUSED + FIXED** — slot-1-main 2026-05-17 02:50 UTC at `features-service@d687df7d`. `process_feature_group` re-raises `(TypeError, KeyError, AttributeError, RuntimeError)` but outer `_process_groups` only caught `(ConnectionError, TimeoutError, OSError, ValueError)`. Any of the re-raised types from one group killed the loop. Broadened catch to `Exception` with `EnhancedError` logging per CLAUDE.md shard-isolation rule.
- [ ] [VERIFY] P1. (after slot-2 fixes) Re-launch VM via consolidated launcher and verify 11 groups × 5 dates all
      process.

## Cross-references (added by slot-1-main 2026-05-17 02:10 UTC)

This focused 2-bug doc captures the highest-priority slot-2 work for B-015 unblock. Slot-1-main's consolidated
escalation at `plans/active/issues/defi_features_pipeline_not_run_2026_05_14.md` § "CONSOLIDATED ESCALATION" adds
3 more compounding issues that surfaced in VM 6 + VM 7 runs:

3. **macro_sentiment also fails 95%-NaN write_gate** (separate from LookaheadBias — depends on which feature path
   runs first). 3 derived columns hit NaN cap.
4. **Workflow iterates 1 day per VM invocation** despite `--end-date` arg (independent of the early-exit bug).
5. **Days 17-19 lending-indices initially looked phantom-skipped** — turned out to be misdiagnosis: data exists at
   the NEW canonical path (`raw_tick_data/by_date/`), my one-shot phantom-flip incorrectly probed only the LEGACY
   path. Corrected at slot-1-main 01:56 UTC — 39 rows unflipped. Lending-indices B-015 window is now fully populated.

**Net infra state**: lending-indices bucket has real data for ALL 5 days (2026-04-15..19) at the new canonical path.
slot-2's fixes for the 2 calculator bugs here + the 3 additional issues in the consolidated escalation will unblock
harsh-slot-9's Phase 2 paper-trade rerun.
