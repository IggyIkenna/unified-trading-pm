---
title: "Data-feed SLA registry (single SSOT) + active feed self-healing"
created: 2026-06-19
parent_epic: observability_master
assigned_vm: vm-cross-cutting
status: active
priority: P1
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3.0
source:
  - operator direction 2026-06-19 (comparison vs external "Operation Blue Flame" SLA architecture — two gaps where Blue
    Flame is tighter than this workspace)
  - verification 2026-06-19 — `rg "data_feed_sla|feed_sla|FEED_SLA"` returns 0 hits; freshness thresholds are scattered
    across UAC `MARKET_TICK_FRESHNESS` + `ALERT_THRESHOLDS[*].tick_staleness`, UTL `freshness_monitor.py`,
    execution/strategy `freshness_gate.py`, MDPS `feature_freshness.py`
locked_by: live-defi-rollout
locked_since: 2026-06-19
---

# Data-feed SLA registry + active feed self-healing

**Goal**: close the two gaps surfaced by the Blue Flame comparison while reusing — not duplicating — what already exists
here (freshness monitors, freshness gates, the autonomous-recovery-matrix, the Incident Gateway, the alerting escalation
ladder, the 4-state honest-absence manifest).

1. **Phase 1 — single declarative feed-SLA SSOT.** A typed registry **already exists** and is the right SSOT to
   CONSOLIDATE ONTO, not replace (verified by reading the code 2026-06-19 — building a new `DATA_FEED_SLA` would be a
   double-SSOT): `unified_api_contracts/internal/reference/data_freshness.py` defines `DataFreshnessContract` (fields:
   `source`, `asset_group`, `max_age_seconds`, `warn_age_seconds`, `expected_cadence_seconds`,
   `criticality ∈ {critical, important, informational}`) + the dicts `MARKET_TICK_FRESHNESS` (~22 venues) /
   `FEATURE_FRESHNESS` / `ML_FRESHNESS` aggregated into `ALL_FRESHNESS_CONTRACTS` (flat O(1) lookup).
   `execution-service` + `strategy-service` `freshness_gate.py` and MDPS `feature_freshness.py` ALREADY read it (no
   re-declared literals). So Phase 1 is three precise fixes, not a greenfield build:
   - **(1a) Close the coverage gap — add the MOST trading-critical feeds, which are currently MISSING**:
     `account_snapshot`, `positions_snapshot`, `reconciliation_age` (Blue Flame's `critical` tier — verified absent from
     `data_freshness.py`). These are account/execution STATE, not a market-data domain, so the `asset_group` Literal
     needs one new value — **operator design call flagged below** (`execution` vs broadening the field's meaning).
   - **(1b) Collapse the two parallel UAC freshness SSOTs into one** — `ALL_FRESHNESS_CONTRACTS` (data_freshness.py) and
     `ALERT_THRESHOLDS["tick_staleness_seconds"]` (`canonical/crosscutting/alerting/thresholds.py:340`) today agree only
     by a hand-written comment ("300s matches tick_staleness_seconds"), not code. Make the alert threshold DERIVE from
     the contract (or add a cross-validation check) so a feed's freshness number has exactly one home.
   - **(1c) Add the Phase-2 binding field** — an optional `refetch_action: str | None` on `DataFreshnessContract` so a
     stale feed can name its re-fetch action (nullable; `informational`/`nice` feeds leave it None).
2. **Phase 2 — active self-healing.** Today recovery is passive (circuit-breaker backoff + HALF_OPEN probe + manifest
   consolidator stale-fallback). Blue Flame actively maps a stale feed → a specific re-fetch method → a repair run. We
   will add a **deterministic `refetch-feed` recovery action** to the autonomous-recovery-matrix Layer-0 closed set,
   keyed off the Phase-1 registry, that fires the feed's bound re-fetch invocation before/while escalating.

> **Not gaps (reuse, do not rebuild)**: the order-blocking trading gate already exists
> (`execution-service/execution_service/validation/freshness_gate.py` + the strategy-service mirror); the escalation
> tiers already exist (AlertSeverity → PagerDuty/Telegram + the audit-ack ladder); the silent-death watchdog already
> exists (`assert_consolidator_healthy` / `CONSOLIDATOR_DOWN` + `WorkerLivenessWatchdog`). This plan UNIFIES the inputs
> those consume and adds the one missing recovery verb (active re-fetch). It does not duplicate any of them.

## Codex SSOT updates (mandatory — enumerated per Citadel rule §6)

| Doc                                                     | Change                                                                                                                                                                                          |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `codex/03-observability/data-feed-sla-registry.md`      | **NEW** — document the EXISTING `DataFreshnessContract` / `ALL_FRESHNESS_CONTRACTS` registry as the feed-SLA SSOT: schema, criticality tiers, who reads it, the account-state feeds added in 1a |
| `codex/04-architecture/autonomous-recovery-matrix.md`   | Add the `refetch-feed` Layer-0 action row + its decision-tree branch (stale critical feed → refetch attempt → escalate on fail)                                                                 |
| `codex/03-observability/alerting.md`                    | Note `tick_staleness_seconds` now derives from / is cross-validated against `MARKET_TICK_FRESHNESS` — one freshness home                                                                        |
| `codex/05-infrastructure/manifest-consolidator-ssot.md` | Cross-ref: consolidator staleness is one feed in the registry; same criticality semantics                                                                                                       |

## Phase 1 — consolidate onto the existing freshness registry

### Pre-audit (DONE 2026-06-19 — read the code, not just grep)

- **SSOT today** = `unified-api-contracts/unified_api_contracts/internal/reference/data_freshness.py`
  (`DataFreshnessContract` + `MARKET_TICK_FRESHNESS`/`FEATURE_FRESHNESS`/`ML_FRESHNESS` → `ALL_FRESHNESS_CONTRACTS`).
- **Consumers already reading it** (no re-declared literals — confirmed): execution-service
  `validation/freshness_gate.py` (`assert_market_data_fresh` reads `MARKET_TICK_FRESHNESS`), strategy-service
  `validation/freshness_gate.py`, MDPS `monitors/feature_freshness.py`, UTL `monitors/freshness_monitor.py` (wraps a
  `DataFreshnessContract`).
- **The second SSOT to reconcile** = `ALERT_THRESHOLDS["tick_staleness_seconds"]` in
  `canonical/crosscutting/alerting/thresholds.py:340` (coupled to the contract only by a comment).
- **Missing critical feeds** (verified absent): `account_snapshot`, `positions_snapshot`, `reconciliation_age`.

- [x] ✅ [DECIDED] P1. **`asset_group` label for account-state feeds** — `DataFreshnessContract.asset_group` is a closed
      Literal of market-data domains. Account/positions/recon feeds are execution STATE, not a market domain.
      **Proceeded with option (a): add `"execution"` to the Literal** (additive, local to this one model, reversible —
      keeps the field one-dimensional). Rejected (b) "widen the field's semantics" as muddying. Operator may revisit.
- [ ] [SCRIPT] P1. **(1a + 1c) Extend `DataFreshnessContract` + add the missing `critical` feeds** — add optional
      `refetch_action: str | None = None` (Phase-2 binding) + `"execution"` to the `asset_group` Literal + a new
      `ACCOUNT_STATE_FRESHNESS` dict (`account_snapshot` 120s, `positions_snapshot` 120s — Blue-Flame critical values;
      `reconciliation_age` warn=1200s/max=2400s from the shipped recon-age SEV1/SEV0 bands) folded into
      `ALL_FRESHNESS_CONTRACTS`. Additive, non-breaking. Repo: unified-api-contracts.
- [ ] [SCRIPT] P1. **(1b) Single freshness home** — make `ALERT_THRESHOLDS["tick_staleness_seconds"]` derive from (or a
      QG cross-validation assert against) `MARKET_TICK_FRESHNESS`, replacing the hand-written "300s matches" comment
      coupling. Repo: unified-api-contracts.
- [ ] [VERIFY] P1. **No-orphan-feed CI gate** — a UAC/PM quality-gate check asserts every venue/feed a freshness gate or
      monitor looks up has an `ALL_FRESHNESS_CONTRACTS` entry, and the two UAC freshness SSOTs agree. Fails loud on a
      feed with no contract. Repo: unified-api-contracts.
- [ ] [VERIFY] P1. Unit tests: `refetch_action` round-trips + defaults None; the new account-state contracts resolve; a
      `critical` feed past `max_age_seconds` raises `DataStalenessError` in `freshness_gate`; `important`
      warns-not-blocks; `informational` logs only; the tick_staleness↔contract cross-validation holds.

## Phase 2 — active self-healing (`refetch-feed` recovery action) — depends on Phase 1

- [ ] [SCRIPT] P1. **Add `refetch-feed` to the Layer-0 deterministic recovery closed set** in
      `deployment-service/scripts/recovery/` — given a stale `feed_id`, look up `DATA_FEED_SLA[feed_id].refetch_action`
      and invoke the bound service-CLI re-fetch (the existing `<svc> --operation ... --shard-key ...` shard-targeted
      fetch — reuse the MTDS/IS CLI shard-targeting flags from infrastructure_master B.2 Phase 5, do NOT build a new
      fetch path). Emit a structured `AgentActionEvent` like every other Layer-0 script. Repo: deployment-service.
- [ ] [SCRIPT] P1. **Wire the refetch into the recovery decision tree** — stale `critical` feed → (a) freshness_gate
      already blocks orders, (b) fire `refetch-feed` (Blue Flame's SILENT_RETRY), (c) on repeated failure escalate
      through the existing AlertSeverity ladder (WARNING_ALERT → CRITICAL_ALERT) and the audit-ack SLA, (d) sustained
      failure → advisory position-reduction recommendation (the existing drawdown/liquidation advisory path, not a new
      one). Map the escalation cadence to `criticality`. Repo: alerting-service + deployment-service recovery.
- [ ] [SCRIPT] P1. **Bind `refetch_action` for each `critical`/`important` feed** in the Phase-1 registry to its actual
      re-fetch CLI invocation (the "map stale feed → specific method" table). `nice` feeds get no refetch binding.
- [ ] [VERIFY] P1. Synthetic smoke (live-mode only — recovery is disabled in batch): age a `critical` feed past its SLA
      → assert `refetch-feed` fires + emits `AgentActionEvent`; force the refetch to fail twice → assert escalation
      steps through WARNING→CRITICAL + audit-ack queued; assert orders stay blocked until the feed recovers.
- [ ] [VERIFY] P1. **Idempotency + storm guard** — refetch for the same `feed_id` is rate-limited (cooldown, like the
      circuit-breaker `auto_cooldown`) so a persistently-stale feed does not spawn a refetch storm; cap per feed per
      window; never refetch a feed whose breaker is OPEN (let the breaker own it).

## Success criteria

- One typed SSOT (`DATA_FEED_SLA`) answers "feeds × max_age × criticality"; every freshness consumer reads it; no inline
  threshold literals remain (grep-verified); the no-orphan-feed CI gate is green.
- A stale `critical` feed in live mode triggers an active mapped re-fetch, escalates on failure through the existing
  ladder, and keeps the order gate closed until recovery — verified by synthetic smoke.
- Codex SSOTs above updated in the same closing phase (Post-Plan-Phase Codex Audit rule).

## Non-goals / out of scope

- Rebuilding the trading gate, the escalation ladder, or the silent-death watchdog (all exist — reuse).
- A second/parallel fetch path — `refetch-feed` reuses the service CLIs.
- Re-baselining the 8 `NEEDS-LIVE` alert thresholds (that is observability*master P3, auto-resumes when live feeds are
  up); this plan only relocates where those thresholds are \_declared*.
