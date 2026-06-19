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

1. **Phase 1 — single declarative feed-SLA SSOT.** Today every feed's freshness expectation lives in a different file.
   There is no one place that answers "what feeds exist, what is each feed's `max_age_seconds`, and how critical is it
   to trading?" Blue Flame has `data_feed_sla.yaml`; we will have a **typed `DATA_FEED_SLA` registry in UAC** (operator
   decision 2026-06-19: typed code SSOT, not loose YAML — matches the workspace SSOT-in-UAC + no-loose-config
   conventions, same shape as the existing `ALERT_THRESHOLDS`).
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

| Doc                                                     | Change                                                                                                                          |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `codex/03-observability/data-feed-sla-registry.md`      | **NEW** — the `DATA_FEED_SLA` schema, criticality tiers, how each consumer reads it, migration-from-scattered-thresholds map    |
| `codex/04-architecture/autonomous-recovery-matrix.md`   | Add the `refetch-feed` Layer-0 action row + its decision-tree branch (stale critical feed → refetch attempt → escalate on fail) |
| `codex/03-observability/alerting.md`                    | Note `tick_staleness` / per-feed thresholds now resolve from `DATA_FEED_SLA`, not per-rule literals                             |
| `codex/05-infrastructure/manifest-consolidator-ssot.md` | Cross-ref: consolidator staleness is one feed in the registry; same criticality semantics                                       |

## Phase 1 — `DATA_FEED_SLA` registry (the SSOT)

### Pre-audit (DONE 2026-06-19 — scattered threshold sites to consolidate)

- UAC `MARKET_TICK_FRESHNESS` contracts (per-venue tick freshness)
- UAC `ALERT_THRESHOLDS[*].tick_staleness` (per-venue alert thresholds — 8 still `NEEDS-LIVE` per observability_master
  P3)
- UTL `unified_trading_library/monitors/freshness_monitor.py` (`FreshnessMonitor.check_and_emit`)
- UTL `core/health_router.py` `data_freshness` callback + `streaming/streaming_health.py` `StreamingHealthSnapshot`
- execution-service + strategy-service `validation/freshness_gate.py` (the order-blocking gate)
- MDPS `monitors/feature_freshness.py` (`FeatureFreshnessChecker`)

- [ ] [SCRIPT] P1. **Define the typed `DATA_FEED_SLA` registry in UAC** — one row per feed with: `feed_id` (stable key),
      `data_path` / manifest row-key shape, `max_age_seconds`, `criticality` (closed StrEnum — map to existing
      `AlertSeverity`: `critical`→blocks trading, `important`→degrade+warn, `nice`→DEBUG), `asset_group`, `source`, and
      `refetch_action` (the Phase-2 re-fetch binding id, nullable). Place beside `ALERT_THRESHOLDS`; export via the
      `unified_api_contracts` facade. Repo: unified-api-contracts.
- [ ] [SCRIPT] P1. **Seed the registry** from the pre-audit sites above (enumerate the live feeds — start with the
      `critical` tier: `live_*` market ticks, account/positions snapshots, recon-age — then `important`
      curve/IV/options, then `nice` weather/Kpler/ENTSO-E equivalents). Each row's `max_age_seconds` migrates the
      existing literal; no new numbers invented without a cited source row.
- [ ] [SCRIPT] P1. **Point `FreshnessMonitor` + `freshness_gate` (execution + strategy) + `FeatureFreshnessChecker` at
      the registry** — they read `DATA_FEED_SLA[feed_id].max_age_seconds` / `.criticality` instead of per-call literals.
      No double SSOT: delete the inline thresholds they replace (Delete-deprecated-code rule). Repos: UTL,
      execution-service, strategy-service, MDPS.
- [ ] [SCRIPT] P1. **Resolve alerting `tick_staleness` thresholds from the registry** — `ALERT_THRESHOLDS` per-venue
      `tick_staleness` reads `DATA_FEED_SLA` so a feed's freshness expectation has exactly one home. Repo:
      unified-api-contracts + alerting-service.
- [ ] [VERIFY] P1. **No-orphan-feed CI gate** — a PM/UAC quality-gate check asserts every feed a freshness monitor or
      freshness gate watches has a `DATA_FEED_SLA` row (and vice-versa: every registry row is consumed). Fails loud on a
      feed with no SLA. Repo: unified-api-contracts (or PM `quality_gates/`).
- [ ] [VERIFY] P1. Unit tests: registry round-trips; criticality→AlertSeverity mapping; a `critical` feed past
      `max_age_seconds` flips `freshness_gate.should_block`; an `important` feed degrades-not-blocks; a `nice` feed is
      DEBUG-only.

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
- Re-baselining the 8 `NEEDS-LIVE` alert thresholds (that is observability_master P3, auto-resumes when live feeds are
  up); this plan only relocates where those thresholds are _declared_.
