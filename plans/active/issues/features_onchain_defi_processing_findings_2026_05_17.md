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

- [ ] [BUG] P0. (slot-2) Fix macro_sentiment lookahead bias — calculator needs as-of-aware TVL fetch.
- [ ] [BUG] P0. (slot-2) Diagnose early-exit after `lending_rates / 2026-04-15 / 0 rows`. Either fix the orchestrator to
      continue on empty_or_failed, or document the expected behavior.
- [ ] [VERIFY] P1. (after slot-2 fixes) Re-launch VM via consolidated launcher and verify 11 groups × 5 dates all
      process.
