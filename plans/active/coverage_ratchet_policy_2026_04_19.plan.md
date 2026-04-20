---
title: Coverage Ratchet Policy + Mid/High Tier Uplift
owner: iggy
created: 2026-04-19
status: active
priority: P1
---

# Coverage Ratchet Policy + Mid/High Tier Uplift

## Context

Workspace-wide coverage sweep (2026-04-19) across the 27 service + API + library repos revealed the following tiers:

- **< 80%**: 20 repos (regression risk: new PRs could slide coverage lower without triggering a gate)
- **80–89%**: 4 repos (risk-and-exposure, batch-live-reconciliation, ml-training, unified-api-contracts)
- **≥ 90%**: 3 repos (pnl-attribution, features-multi-timeframe, features-commodity)

User ask (2026-04-19): **"secure regression testing"** — lock in current coverage as a floor so PRs can't regress
silently, then uplift the lowest 5 repos to 80% (tracked separately in
[coverage_uplift_bottom5_2026_04_19.plan.md](coverage_uplift_bottom5_2026_04_19.plan.md)), and walk the middle tier up
over time without "coverage stuffing" (shallow tests that hit lines without asserting behavior — an anti-pattern the
Citadel rules call out).

## Phase 1 — Ratchet current coverage (COMPLETE)

Each repo's `scripts/quality-gates.sh` had its `MIN_COVERAGE` raised to the current `coverage.xml` line-rate rounded
down. Repos below the system floor of 70 also got a `.coverage-floor-exception.md` pointing at this plan.

### Per-repo floor ratchet (2026-04-19)

- [x] `alerting-service` — 76 → **77**
- [x] `batch-live-reconciliation-service` — 70 → **80**
- [x] `client-reporting-api` — 70 → **71**
- [x] `deployment-api` — 70 → **71**
- [x] `deployment-service` — **70** (unchanged; already at current)
- [x] `execution-service` — 30 → **59** + exception file
- [x] `features-calendar-service` — 66 → **67** + exception file
- [x] `features-commodity-service` — **98** (unchanged)
- [x] `features-cross-instrument-service` — **79** (unchanged)
- [x] `features-delta-one-service` — **70** (unchanged)
- [x] `features-multi-timeframe-service` — **96** (unchanged)
- [x] `features-onchain-service` — **66** + exception file (was 66, kept)
- [x] `features-sports-service` — **64** + exception file (was 64, kept)
- [x] `features-volatility-service` — 62 → **77**
- [x] `instruments-service` — 75 → **78**
- [x] `market-data-processing-service` — **70** (unchanged)
- [x] `market-tick-data-service` — 28 → **47** + exception file
- [x] `ml-inference-service` — 70 → **77**
- [x] `ml-training-service` — 80 → **81**
- [x] `pnl-attribution-service` — 88 → **93**
- [x] `position-balance-monitor-service` — 58 → **68** + exception file
- [x] `risk-and-exposure-service` — 74 → **80**
- [x] `strategy-service` — 70 → **74**
- [x] `trading-agent-service` — **57** + exception file (was 57, kept)
- [x] `unified-api-contracts` — 84 → **89**
- [x] `unified-trading-api` — 70 → **77**
- [x] `unified-trading-library` — 65 → **68** + exception file

### Success criterion (Phase 1)

- [x] C4 — Each repo's `bash scripts/quality-gates.sh` either passes the new floor or the QG output documents the gap
      (e.g., a shard is missing tests — the point of ratcheting is that the current number is locked in, not that every
      repo is green).

## Phase 2 — Ratchet-only policy for the middle tier (< 80%, excl. bottom 5)

The 15 repos currently in [67%, 79.4%] (all repos below 80% except the 5 biggest gaps) get a **no-new-test-required**
ratchet policy:

| Repo                                | Current | Next step          |
| ----------------------------------- | ------- | ------------------ |
| `features-calendar-service`         | 67      | +2 per sprint → 80 |
| `unified-trading-library`           | 68      | +2 per sprint → 80 |
| `position-balance-monitor-service`  | 68      | +2 per sprint → 80 |
| `deployment-service`                | 70      | +2 per sprint → 80 |
| `market-data-processing-service`    | 70      | +2 per sprint → 80 |
| `features-delta-one-service`        | 70      | +2 per sprint → 80 |
| `client-reporting-api`              | 71      | +2 per sprint → 80 |
| `deployment-api`                    | 71      | +2 per sprint → 80 |
| `strategy-service`                  | 74      | +2 per sprint → 80 |
| `alerting-service`                  | 77      | +2 per sprint → 80 |
| `features-volatility-service`       | 77      | +2 per sprint → 80 |
| `ml-inference-service`              | 77      | +2 per sprint → 80 |
| `unified-trading-api`               | 77      | +2 per sprint → 80 |
| `instruments-service`               | 78      | +2 per sprint → 80 |
| `features-cross-instrument-service` | 79      | +1 per sprint → 80 |

### Policy

- [ ] Every sprint, run the workspace coverage sweep (same command pattern as `tools/sweep-coverage.sh` or the ad-hoc
      python script in this session — result lives in `coverage.xml` per repo).
- [ ] For each repo in the table above, if `coverage.xml` line-rate is ≥ (current_floor + 2), bump `MIN_COVERAGE` by the
      realised delta (rounded down to integer).
- [ ] Never lower a floor. Lowering requires a signed exception in the same format as the system-floor exception files.
- [ ] New features must come with tests that hold the new floor — this is the regression-testing guarantee, not the
      absolute number.

### Why ratchet-only and not "write tests to hit 80 now"

Writing thousands of lines of "coverage-stuffing" tests (lines touched but no meaningful assertions) produces fake
confidence. The QG goes green but bugs slip through unchanged. The ratchet guarantees we never backslide; real coverage
uplift happens organically via feature work + bug fixes, each of which lands with a targeted test.

## Phase 3 — 80–89% tier to 90%

Four repos live between 80 and 89%. Same ratchet-only policy as Phase 2 but targeting 90%.

| Repo                                | Current | Gap   | Target |
| ----------------------------------- | ------- | ----- | ------ |
| `risk-and-exposure-service`         | 80.0    | +10.0 | 90     |
| `batch-live-reconciliation-service` | 80.4    | +9.6  | 90     |
| `ml-training-service`               | 81.1    | +8.9  | 90     |
| `unified-api-contracts`             | 89.4    | +0.6  | 90     |

- [ ] Same +2/sprint ratchet rule. UAC is one sprint away from 90%.
- [ ] When any of these lands a new module, require ≥90% on the new module (enforce via the diff-coverage rule below).

## Phase 4 — Diff-coverage enforcement (future)

Absolute coverage floors catch _backslide_, but they don't catch _new untested code_. A new feature that lands 500 lines
of code with 40 lines of tests (8% local coverage) can still pass if the overall repo floor holds. Fix: add a
`diff-cover` check to QG.

- [ ] [AGENT] Add `diff-cover >=80` check to `quality-gates-base/base-service.sh` against the PR base ref
      (`origin/live-defi-rollout`). Blocks PRs whose added/changed lines are below 80% covered, regardless of overall
      floor.
- [ ] Rollout via `rollout-quality-gates-unified.py` — same mechanism that distributed the current QG stubs.

## Readiness

- [x] C1 — floors raised in source
- [x] C2 — exception files written for sub-70% repos
- [ ] C3 — workspace sweep re-run confirms all 27 repos pass the new floors (or fail with a clear, pre-existing gap)
- [ ] C4 — diff-cover gate added (Phase 4)
- [ ] B1 — sprint cadence agreed with human for the +2/sprint ratchet

## References

- [coverage_uplift_bottom5_2026_04_19.plan.md](coverage_uplift_bottom5_2026_04_19.plan.md) — concrete file-level uplift
  for MTDS, trading-agent, execution, features-sports, features-onchain
- [PLAN_FORMAT.md](../PLAN_FORMAT.md) — readiness-gate model
- [coverage-floor-guard.sh](../../scripts/coverage-floor-guard.sh) — system floor enforcement (70)
