---
name: observability_master_audit_instructions
type: audit-instructions
epic: observability_master
assigned_vm: vm-cross-cutting
tier: L4
last_updated: 2026-05-22
---

# Observability Master — Audit Instructions

## Epic Scope

alerting-service, monitoring hooks, telemetry pipeline, 3am-auto-recovery scripts, QG snapshot cron, runbook governance
(owner/cadence/verifier/last_executed fields required). Every service must emit STARTED/STOPPED/FAILED via
`ServiceBootstrap`.

## Triggers

- Weekly (minimum cadence)
- After any recovery script change
- When QG snapshot cron shows stale (last run > 24h ago)
- After any new service added to the workspace (must be wired to alerting)

## Checklist

- [ ] (a) **QG snapshot cron healthy**: Cloud Scheduler job for QG snapshots is ENABLED and last run < 24h ago. Check:
      `qg_snapshot_cron_stale_2026_05_18.md` — if BLOCKED-OPERATOR, verify operator has been pinged Run:
      `gcloud scheduler jobs describe` for relevant job

- [ ] (b) **3am auto-recovery tested**: recovery script runs end-to-end on dev VM without errors. Find:
      `rg "auto.recovery\|3am" unified-trading-pm/scripts/ --include="*.sh" -l` Run: script in dry-run mode if available

- [ ] (c) **alerting-service covers strategy + execution failures**: alerting-service is wired to receive FAILED events
      from strategy-service and execution-service. Grep:
      `rg "alerting\|alert_service" strategy-service/ execution-service/ --include="*.py"` — verify call sites

- [ ] (d) **Telemetry covers ServiceBootstrap events**: STARTED / STOPPED / FAILED events from all services are picked
      up by the telemetry pipeline. Grep: `rg "ServiceBootstrap" --include="*.py"` across all service dirs — every
      service must have it Verify: telemetry sink receives these events in integration test

- [ ] (e) **Runbook fields complete**: every runbook has `owner`, `cadence`, `verifier`, `last_executed` fields. Run:
      `grep -rL "owner\|cadence\|verifier\|last_executed" plans/active/*.md | grep -i "runbook"` — should be 0 hits (or
      use the plan-hygiene script if it covers this)


### E2E Cross-Cutting Verification

- (e2e-batch-live) **Batch-live round-trip**: pick one (venue, data_type) pair, run batch adapter → confirm manifest
  row → run live adapter → confirm same schema row. Requires only one working adapter pair, not all.
- (mock-upstream) **Independent audit**: cross-cutting audits MUST be runnable with `CLOUD_MOCK_MODE=true` to test
  infrastructure, error classification, and isolation patterns without real cloud access.

## Success Criteria

- All 5 checklist items GREEN
- Alerting smoke test passes (inject FAILED event → alert fires within 60s)
- QG snapshot cron ran within last 24h

## Output Format

Result file at `plans/audit/results/observability_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
