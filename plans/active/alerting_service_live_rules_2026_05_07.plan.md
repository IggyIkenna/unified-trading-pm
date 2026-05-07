---
type: plan
asset_group: cross-cutting
priority: P0
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-07
depends_on: []
gates:
  - master_to_live_defi_2026_05_23:work-stream-E
  - master_to_live_defi_2026_05_23:Group-F
  - master_to_live_defi_2026_05_23:Group-G
status: active
date: 2026-05-07
owner: Ikenna (plan), Harsh (alerting-service code)
---

# Alerting Service Live Rules — Production Rule SSOT + Thresholds + Paging

Closes the "alerting plan does not exist" anomaly flagged by the 2026-05-07 audit (see
`_AUDIT_2026_05_07_dependency_graph.md` operator action item #1). The alerting-**service** itself already exists
(multi-channel routing across Slack/Email/PagerDuty/Telegram, KillSwitchBus subscriber via `7b74ed8`, MarginEvent
consumer via `f4c308f`, Phase 8 QG coverage). The gap is the **rules SSOT + concrete thresholds + production paging
targets + operator playbook + rehearsal procedure** required to enable live trading on 2026-05-23.

## Context

**Existing capability** (verified 2026-05-07):

- Service: `alerting-service/` — Cloud Run + (AWS-ready via `buildspec.aws.yaml`)
- Config: `AlertingSystemConfig` with `routing_rules` default-factory at
  [`config.py:11-199`](alerting-service/alerting_service/config.py#L11-L199)
- KillSwitchBus subscriber wired via UTL (Phase 3c, commit `7b74ed8`)
- E2E test plan:
  [`plans/active/end-to-end-testing/020_alerting_service.md`](unified-trading-pm/plans/active/end-to-end-testing/020_alerting_service.md)
  — covers PubSub subscriptions, downstream commands, frontend API surface
- UAC envelope:
  [`unified_api_contracts/internal/alerting/alerts.py`](unified-api-contracts/unified_api_contracts/internal/alerting/alerts.py)
  has `DefiAlert` BaseModel
- Circuit-breaker config SSOT:
  [`unified_api_contracts/internal/reference/circuit_breaker_config.py`](unified-api-contracts/unified_api_contracts/internal/reference/circuit_breaker_config.py)
- Existing routing patterns (from e2e plan §"Alert Routing Rules"): `KILL_SWITCH_*` / `CIRCUIT_BREAKER_OPEN` /
  `DEFI_HEALTH_FACTOR_CRITICAL` / `DEFI_WEETH_DEPEG` / `DEFI_AAVE_UTILIZATION_SPIKE` / `DEFI_FUNDING_RATE_FLIP` /
  `DEFI_FEATURE_STALE` / `PREFLIGHT_FAILED` / `SERVICE_DEGRADED` / catch-all

**Gap analysis** — what's missing for May-23:

1. UAC alert-type taxonomy is open-ended — only `DefiAlert` envelope, no closed `StrEnum` of alert codes the way
   `EMPTY_CONFIRMED_REASONS` codifies honest-coverage reasons. Routing rules drift between service config + UAC.
2. Threshold values are scattered or absent: AAVE utilization spike threshold, weETH depeg basis-points, funding-rate
   flip magnitude, health-factor critical level, feature-staleness grace window. No registry, no per-rule default +
   per-archetype override.
3. Production paging targets unset: Telegram chat IDs, PagerDuty service keys, Slack channel IDs all absent or
   hard-coded. No Secret Manager wiring for rotation. No on-call rotation policy.
4. No DART integration for the ack/escalate/resolve flow per alert.
5. No operator playbook — for each alert type, what's the diagnosis recipe, what's the resolution path, what's the
   rollback?
6. No live rehearsal procedure — synthetic alert injection + ack flow + escalation + auto-recovery validated end-to-end.
7. No "quietness baseline" — the system has not yet run 24-48h with thresholds tuned; false-positive rate unknown. Live
   trading without a quiet baseline risks alert fatigue → real alerts ignored.

## Pre-audit (blast radius)

Affected files / consumers when shipping:

- [unified-api-contracts/unified_api_contracts/internal/alerting/](unified-api-contracts/unified_api_contracts/internal/alerting/)
  — add taxonomy + threshold registry
- [unified-api-contracts/unified_api_contracts/internal/reference/circuit_breaker_config.py](unified-api-contracts/unified_api_contracts/internal/reference/circuit_breaker_config.py)
  — extend with per-rule thresholds
- [alerting-service/alerting_service/config.py](alerting-service/alerting_service/config.py) — replace inline
  `_default_routing_rules` with UAC SSOT consumption
- [alerting-service/alerting_service/circuit_breaker.py](alerting-service/alerting_service/circuit_breaker.py) — wire
  UAC threshold lookups
- [risk-and-exposure-service/](risk-and-exposure-service/) — emit alerts using UAC closed taxonomy
- [position-balance-monitor-service/](position-balance-monitor-service/) — same
- [execution-service/](execution-service/) — circuit-breaker subscriber + KILL_SWITCH emitter
- [features-onchain/](features-onchain/) — emit `DEFI_HEALTH_FACTOR_CRITICAL`, `DEFI_AAVE_UTILIZATION_SPIKE`,
  `DEFI_FUNDING_RATE_FLIP`, `DEFI_FEATURE_STALE` consumers
- [unified-trading-system-ui/](unified-trading-system-ui/) (DART) — Active Alerts panel, Ack button, Escalate button
  (per e2e plan Frontend API Surface)
- Codex doc: `unified-trading-pm/codex/14-playbooks/alerting/` — new operator playbook directory
- Secret Manager: 4 secret entries for paging credentials (Telegram bot token, Telegram chat IDs, PagerDuty service key,
  Slack webhook URL)

## Phased execution DAG

Phase numbering uses Citadel-grade convention; QG gate between phases.

### Phase 1 — UAC alert taxonomy + threshold SSOT (1 day, **PARALLEL** with Phase 2)

Closed-set taxonomy mirrors `EMPTY_CONFIRMED_REASONS` pattern. Routing rules read from UAC, not from inline
default-factory.

- [ ] [SCRIPT] P0. Add `AlertCode` StrEnum to `unified_api_contracts/internal/alerting/alerts.py` with all
      currently-routed codes (KILL_SWITCH_DEFI_LIQUIDATION_RISK, KILL_SWITCH_PORTFOLIO_DRAWDOWN,
      KILL_SWITCH_VENUE_DISCONNECT, CIRCUIT_BREAKER_OPEN, DEFI_HEALTH_FACTOR_CRITICAL, DEFI_WEETH_DEPEG,
      DEFI_AAVE_UTILIZATION_SPIKE, DEFI_FUNDING_RATE_FLIP, DEFI_FEATURE_STALE, PREFLIGHT_FAILED, SERVICE_DEGRADED,
      BALANCE_DRIFT, ORDER_REJECTION_SPIKE, MARGIN_THRESHOLD_BREACH, POSITION_DRIFT). Closed set.
- [ ] [SCRIPT] P0. Add `AlertSeverity` StrEnum: `CRITICAL` (page now), `HIGH` (page within SLA), `WARN` (notify, no
      page), `INFO` (log only).
- [ ] [SCRIPT] P0. Add `AlertChannel` StrEnum: `PAGERDUTY`, `TELEGRAM`, `SLACK`, `EMAIL`, `LOG_ONLY`.
- [ ] [SCRIPT] P0. Add `AlertRule` Pydantic model:
      `code: AlertCode, severity: AlertSeverity, channels: list[AlertChannel], pattern: str (fnmatch), runbook_doc: str, threshold_key: str | None`.
      Fail-loud on unknown code at construction.
- [ ] [SCRIPT] P0. Add `LIVE_ALERT_RULES: tuple[AlertRule, ...]` SSOT in
      `unified_api_contracts/internal/alerting/live_rules.py`. Lift the 10 patterns from
      `alerting-service/config.py:_default_routing_rules` byte-for-byte, add the 5 new ones (BALANCE_DRIFT etc).
- [ ] [SCRIPT] P0. Add `ALERT_THRESHOLDS: dict[str, AlertThreshold]` registry in
      `unified_api_contracts/internal/alerting/thresholds.py`. Each entry:
      `key, dtype, default_value, per_archetype_overrides, units, source_doc`.
- [ ] [SCRIPT] P0. Threshold defaults seeded with these initial values (verified by Phase 7 quietness baseline; see §
      "Threshold seeding rationale"):
  - `defi_health_factor_critical`: 1.05 (Aave HF; below 1.0 triggers liquidation; 5% buffer)
  - `defi_weeth_depeg_bps`: 50 (0.5% from peg over 5min window)
  - `defi_aave_utilization_spike_bps`: 9500 (95% pool utilization; default-yield drops sharply above)
  - `defi_funding_rate_flip_bps_5m`: 100 (1% APR flip in 5min — could indicate stat-arb regime change)
  - `defi_feature_stale_minutes`: 15 (LST yield read freshness — staked-basis archetype)
  - `balance_drift_usd`: 1000 (notional discrepancy between expected and observed wallet balance)
  - `order_rejection_spike_per_min`: 10 (rolling rate over 5min)
  - `margin_threshold_breach_bps`: 200 (2% from initial-margin-call line; broker-defined)
  - `position_drift_bps`: 100 (1% from target weight; rebalance trigger)
- [ ] [SCRIPT] P0. UAC sanity tests: every `AlertRule.threshold_key` is in `ALERT_THRESHOLDS`; every `AlertRule.pattern`
      matches at least one `AlertCode`; every catch-all is last; no duplicate codes. Failing test == bad config.
- [ ] [QG] P0. UAC quality-gates pass + push.

### Phase 2 — Service migration to UAC SSOT (1 day, **PARALLEL** with Phase 1 once Phase 1 lands)

Replace inline default-factory with UAC consumption. No double-SSOT per workspace "no double SSOT" rule.

- [ ] [AGENT] P0. `alerting-service/alerting_service/config.py` — replace `_default_routing_rules` with
      `from unified_api_contracts.internal.alerting import LIVE_ALERT_RULES`. Default-factory returns
      `[rule.to_routing_dict() for rule in LIVE_ALERT_RULES]`.
- [ ] [AGENT] P0. `alerting-service/alerting_service/circuit_breaker.py` — replace any hard-coded thresholds with
      `ALERT_THRESHOLDS[key].for_archetype(archetype)`.
- [ ] [AGENT] P0. `alerting-service/tests/unit/test_risk_threshold_rules.py` — assert closed-set taxonomy: every alert
      seen during test pass has a code in `AlertCode` and a rule that matches.
- [ ] [QG] P0. `cd alerting-service && bash scripts/quality-gates.sh` pass.
- [ ] [SCRIPT] P0. Coordinate with Harsh before commit (alerting-service is Harsh's per `README.md`). Pair-review the
      migration diff.

### Phase 3 — Producer migration to UAC closed-set codes (2 days, parallel across services)

Every emitter must use `AlertCode` enum, not raw strings. Fail-loud on unknown.

- [ ] [SCRIPT] P0. `risk-and-exposure-service/`: emit `BALANCE_DRIFT`, `MARGIN_THRESHOLD_BREACH`, `CIRCUIT_BREAKER_OPEN`
      using `AlertCode.X`.
- [ ] [SCRIPT] P0. `position-balance-monitor-service/`: emit `BALANCE_DRIFT`, `POSITION_DRIFT`.
- [ ] [SCRIPT] P0. `execution-service/`: emit `KILL_SWITCH_*` from KillSwitchBus + `ORDER_REJECTION_SPIKE` from
      rejection-tracker.
- [ ] [SCRIPT] P0. `features-onchain-service/`: emit `DEFI_HEALTH_FACTOR_CRITICAL` (from Aave health-factor calculator),
      `DEFI_AAVE_UTILIZATION_SPIKE` (from Aave pool-utilization calc), `DEFI_FUNDING_RATE_FLIP` (from perp funding
      calc), `DEFI_FEATURE_STALE` (from feature-staleness watchdog), `DEFI_WEETH_DEPEG` (from LST-peg deviation calc).
- [ ] [SCRIPT] P0. Each emitter: add unit test asserting alert payload conforms to `DefiAlert` envelope + `AlertCode`
      enum value.
- [ ] [QG] P0. Per-service QG pass on each emitter repo.

### Phase 4 — Production paging targets via Secret Manager (1 day)

No hard-coded creds. Rotation via `ApiKeyReloader` per CLAUDE.md.

- [ ] [HUMAN] P0. Operator action: create 4 secrets in GCP Secret Manager (`uts-prod` project):
      `alerting-telegram-bot-token`, `alerting-telegram-chat-ids` (JSON list per severity),
      `alerting-pagerduty-service-key`, `alerting-slack-webhook-url`. Same in AWS Secrets Manager `ap-northeast-1` for
      parity.
- [ ] [SCRIPT] P0. `alerting-service/alerting_service/config.py` — wire `ApiKeyReloader` for the 4 paging credentials.
      No `os.getenv()` per CLAUDE.md.
- [ ] [SCRIPT] P0. Channel-specific dispatchers in
      `alerting-service/alerting_service/dispatchers/{telegram,pagerduty,slack,email}.py` — each consumes
      `ApiKeyReloader.current()` per call. Survives rotation without restart.
- [ ] [SCRIPT] P0. PagerDuty escalation policy: define in PD console `uts-prod-live-trading` service with
      1st-tier=Ikenna, 2nd-tier=Harsh, 30-min auto-escalate. Capture policy ID in
      `unified-trading-pm/codex/14-playbooks/alerting/pagerduty-escalation-policy.md`.
- [ ] [HUMAN] P0. Operator action: send synthetic test alert to each channel + confirm delivery. Capture screenshots in
      handover.

### Phase 5 — DART integration (ack / escalate / resolve UI) (1-2 days, **PARALLEL** with Phase 4)

Wires existing alerting-service API endpoints (`GET /alerts/active`, `POST /alerts/{id}/acknowledge`,
`POST /alerts/{id}/escalate` per e2e plan) into the DART cockpit operator surface.

- [ ] [SCRIPT] P0. `unified-trading-system-ui/`: Active Alerts panel in DART top-bar — fetch `/alerts/active` every 10s,
      badge count = unack-critical. Confirm against e2e plan §"Frontend API Surface".
- [ ] [SCRIPT] P0. Per-alert detail modal: show code + severity + payload + runbook link (deep-link to codex playbook
      doc). Ack button + Escalate button + Resolve button (server-side flow already exists per e2e plan).
- [ ] [SCRIPT] P0. Severity breakdown pie-chart widget (per e2e plan).
- [ ] [SCRIPT] P0. Persona Playwright test: `live-operator` persona walks the ack flow on a synthetic CRITICAL alert.
      Asserts notification bell decrements + alert moves to `acknowledged` state.

### Phase 6 — Per-alert operator playbook (codex docs, 1-2 days, **PARALLEL** with Phases 3-5)

For each `AlertCode`, an operator runbook with: symptom, diagnosis recipe, resolution path, rollback, escalation
criteria.

- [ ] [SCRIPT] P0. Create `unified-trading-pm/codex/14-playbooks/alerting/` directory with frontmatter
      `scope: alerting`. Add `README.md` index of all alert codes.
- [ ] [SCRIPT] P0. One markdown file per alert code: `kill_switch_defi_liquidation_risk.md`,
      `kill_switch_portfolio_drawdown.md`, `kill_switch_venue_disconnect.md`, `circuit_breaker_open.md`,
      `defi_health_factor_critical.md`, `defi_weeth_depeg.md`, `defi_aave_utilization_spike.md`,
      `defi_funding_rate_flip.md`, `defi_feature_stale.md`, `preflight_failed.md`, `service_degraded.md`,
      `balance_drift.md`, `order_rejection_spike.md`, `margin_threshold_breach.md`, `position_drift.md` (15 docs).
- [ ] [SCRIPT] P0. Each playbook MUST include: trigger condition, severity, paging channels, diagnosis steps (with
      concrete commands like `gcloud compute instances describe ...`), resolution paths (auto-recovery / manual
      intervention / kill-switch), rollback procedure, success criteria, escalation criteria + targets. Template in
      `_template.md`.
- [ ] [SCRIPT] P0. Wire `runbook_doc` field in `AlertRule` to point at the markdown file.
      `unified-trading-system-ui/DART` deep-links to
      `https://github.com/IggyIkenna/unified-trading-pm/blob/main/codex/14-playbooks/alerting/{file}.md` from the alert
      detail modal.

### Phase 7 — Quietness baseline + threshold tuning (3-5 days, GATES Phase 8)

Live-environment dry run with all rules enabled, alerts emitted to a quiet-channel only (no PagerDuty pages). Operator
reviews + tunes thresholds.

- [ ] [SCRIPT] P0. Deploy alerting-service to `staging` (no PagerDuty wiring; Telegram → `uts-staging-noise` chat only;
      Slack → `#uts-staging-alerts`).
- [ ] [SCRIPT] P0. Enable all 15 alert rules in staging routing config.
- [ ] [HUMAN] P0. Operator: run for 48h continuous. Record every alert fired (timestamp, code, severity, payload,
      was-it-real?).
- [ ] [HUMAN] P0. Per alert code, compute false-positive rate. Tune threshold: if FP > 10% per 24h, raise threshold by
      50% and re-run 24h. Iterate until FP < 5%/24h.
- [ ] [SCRIPT] P0. Update `ALERT_THRESHOLDS` in UAC with tuned values. Annotate each entry with quietness-baseline-date.
- [ ] [HUMAN] P0. Acceptance criterion: 48h continuous run with 0 PagerDuty-severity false positives, ≤2
      Telegram-severity false positives.

### Phase 8 — Live rehearsal (1 day, GATES May-23 deadline)

Synthetic-alert injection + full operator-flow verification on prod-equivalent env.

- [ ] [SCRIPT] P0. Add `alerting-service/scripts/inject_synthetic_alert.py` — emits a `DefiAlert` with `synthetic=true`
      flag for each `AlertCode`, one at a time.
- [ ] [HUMAN] P0. Rehearsal session: operator runs script for each of 15 alert codes; verifies (a) alert lands in
      correct channel, (b) DART panel shows alert, (c) ack flow works, (d) escalate flow works (synthetic PD page), (e)
      runbook deep-link works, (f) auto-resolve works.
- [ ] [HUMAN] P0. CRITICAL-severity rehearsal: simulate `KILL_SWITCH_DEFI_LIQUIDATION_RISK` end-to-end including
      circuit-breaker propagation to execution-service + strategy-service halt-order subscribers (per e2e plan
      §"Downstream Commands").
- [ ] [HUMAN] P0. Sign-off doc: `unified-trading-pm/codex/14-playbooks/alerting/REHEARSAL_2026_05_<date>.md` listing all
      15 codes + pass/fail per code + operator name + date.

### Phase 9 — Production go-live + 7-day soak (during May-23 trading window)

- [ ] [HUMAN] P0. Flip `alerting-service` to prod paging on 2026-05-23 09:00 UTC, paired with the live-DeFi cutover.
- [ ] [HUMAN] P1. Daily review of fired alerts during 7-day soak. Threshold re-tuning if FP rate drifts.

## Threshold seeding rationale

Initial values in Phase 1 are **starting points**, not validated production values. Phase 7 quietness baseline tunes
them. Citation per value:

- `defi_health_factor_critical=1.05` — Aave docs: HF<1 triggers liquidation; 5% buffer matches industry standard for
  monitoring tools (Tenderly, Hypernative, Gauntlet).
- `defi_weeth_depeg_bps=50` — weETH historical depeg max during normal conditions ≈ 30bps; 50bps catches abnormal events
  without firing on chop. Subject to Phase 7 tuning.
- `defi_aave_utilization_spike_bps=9500` — Aave pool-yield curves inflect sharply at 95%+ utilization (the "kink" in the
  interest-rate model). Above this, default carry strategy assumptions break.
- `defi_funding_rate_flip_bps_5m=100` — 1%-APR flip in 5min == regime-change signal for `leveraged_funding_arb`
  archetype.
- `defi_feature_stale_minutes=15` — `carry_staked_basis` LST yields update on epoch boundary (≈12min Solana, ≈12sec
  Ethereum); 15min is a generous lower bound.
- `balance_drift_usd=1000` — operator-confirmed acceptable noise for the initial wallet (operator action: confirm in
  Phase 4).
- `order_rejection_spike_per_min=10` — sub-noise vs typical CeFi exchange reject rate; spike == venue health
  degradation.
- `margin_threshold_breach_bps=200` — 2% buffer from initial-margin-call. Per-venue overrides via
  `per_archetype_overrides`.
- `position_drift_bps=100` — 1%-from-target rebalance trigger; common industry standard.

## Success criteria

- **Phase 1 + 2**: UAC closed-set taxonomy lands; `alerting-service/config.py` no longer has inline
  `_default_routing_rules` (single SSOT).
- **Phase 3**: Every alert emitter in workspace uses `AlertCode` enum, zero raw-string emissions in test suite.
- **Phase 4**: 4 paging channels deliver synthetic alerts end-to-end (Telegram + PagerDuty + Slack + Email).
- **Phase 5**: DART persona-Playwright passes on ack/escalate/resolve flow.
- **Phase 6**: 15 markdown runbooks land + are deep-linked from DART.
- **Phase 7**: 48h staging dry-run with FP-rate < 5% per 24h.
- **Phase 8**: All 15 codes pass synthetic rehearsal + KILL_SWITCH circuit-breaker propagation verified.
- **Phase 9**: Live go-live on 2026-05-23 with 7-day soak.

## Cross-plan blockers

**Blocked by**: nothing upstream.

**Blocks** (downstream consumers):

- `master_to_live_defi_2026_05_23:work-stream-E` — alerting / kill-switch verification.
- `master_to_live_defi_2026_05_23:Group F` — live trading prereqs include alerting.
- `master_to_live_defi_2026_05_23:Group G` — DART operator UX includes Active Alerts panel.
- `defi_master_2026_05_07:carry_staked_basis live wiring` — needs `DEFI_HEALTH_FACTOR_CRITICAL` + `DEFI_WEETH_DEPEG` +
  `DEFI_FEATURE_STALE` rules live.
- `defi_master_2026_05_07:leveraged_funding_arb` — needs `DEFI_FUNDING_RATE_FLIP`.
- `dart_ux_cockpit_refactor_2026_04_29:Layer-2-badges` — Active Alerts widget shares badges + maturity flags.

## Coordination notes

- **alerting-service is Harsh's repo** per [`README.md`](alerting-service/README.md). All code edits to
  alerting-service/ MUST be pair-coordinated, NOT pushed unilaterally. UAC additions (Phases 1) are owner-neutral and
  can ship without coordination. Producer-emitter migrations (Phase 3) touch services owned by both Ikenna + Harsh —
  coordinate per-service.
- **AWS parity**: `alerting-service` already has `buildspec.aws.yaml` — Phase 4 paging-targets work should land both GCP
  Secret Manager + AWS Secrets Manager entries.
- **No `_create_full_day_empty_output`-style placeholder anti-pattern** in alert taxonomy: `LIVE_ALERT_RULES` is
  closed-set; emitting an `AlertCode` outside the enum raises immediately. This mirrors the `EMPTY_CONFIRMED_REASONS`
  discipline from writegate.

## Anti-patterns + banned approaches

- ❌ Inline alert-code strings in emitters (use `AlertCode.X` enum only).
- ❌ Hard-coded thresholds in service code (use `ALERT_THRESHOLDS` registry).
- ❌ `os.getenv()` for paging creds (use `ApiKeyReloader` per CLAUDE.md).
- ❌ Skipping rehearsal Phase 8 to hit deadline — KILL_SWITCH propagation MUST be verified end-to-end before live.
- ❌ Going live without 48h quietness baseline (Phase 7) — alert fatigue causes real alerts to be ignored.
- ❌ Editing `alerting-service/` without pair-coordinating with Harsh.

## Open questions for operator

1. PagerDuty service tier: shared `uts-prod-live-trading` or per-archetype? (Phase 4)
2. Telegram chat structure: single `uts-prod-alerts` chat or per-severity? (Phase 4)
3. On-call rotation: solo (Ikenna primary, Harsh backup) or formal rotation? (Phase 4)
4. Quietness baseline duration — 48h fixed, or extend if FP rate doesn't converge? (Phase 7)
5. Are there alert codes specific to `carry_staked_basis` we're missing? E.g. `JITOSOL_VALIDATOR_DOWNTIME`,
   `STAKED_BASIS_MEV_REGIME_FLIP`. Defer to v2 or include in Phase 1?
6. SLO/error-budget framework — track alert-MTTR + SLA misses for post-deadline v2 retrospective? (Phase 9)

## Next steps

1. Operator approves plan → unlock branch + start Phase 1.
2. Phase 1 + 2 ship in parallel (1-2 days). Phase 1 needs Harsh's review of `LIVE_ALERT_RULES` taxonomy alignment with
   alerting-service expectations.
3. Phase 3 (producer migration) parallelises across 5 services — 2 days.
4. Phase 4 + 5 + 6 in parallel — 2 days.
5. Phase 7 quietness baseline blocks Phase 8 by 48h floor (3-5 days total given tuning iteration).
6. Phase 8 rehearsal: 1 day (single operator session).
7. Phase 9 go-live aligned with 2026-05-23 cutover.

**Total**: 9-12 days. Fits in the 16-day window with margin if no blockers materialise. Compression possible by
parallelising Phases 3 + 4 + 5 + 6 + Phase 1+2 simultaneously — that brings the floor to 7-8 days assuming clean QG
pass.

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (created at audit synthesis time)
- **Verified**: 0 of N (new plan, all items pending Phase 1 kickoff)
- **In-flight (running VMs)**: none
- **Blocked by**: nothing
- **Blocks**: master_to_live_defi:work-stream-E, master_to_live_defi:Group-F, master_to_live_defi:Group-G,
  defi_master:carry_staked_basis-live, defi_master:leveraged_funding_arb, dart_ux_cockpit:Layer-2-badges
- **Last meaningful commit**: this plan ships as the keystone unblock.
- **Recommendation**: kickoff immediately after Harsh review of Phase 1 taxonomy.
