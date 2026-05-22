---
name: orchestrator_master_audit_instructions
type: audit-instructions
epic: orchestrator_master
assigned_vm: vm-orchestrator
tier: L5
last_updated: 2026-05-22
---

# Orchestrator Master — Audit Instructions

## Epic Scope

agent-orchestrator multi-VM stack (FastAPI + Vite dashboard), planning VM, Fleet tab dashboard, slot management,
plan-hygiene cron (`0 5 * * *` UTC), orphan-ping audit cron (every 4h), `slot-cron-ff-pull.sh`,
`slot-git-status-report.sh`, `orchestrator_vm_registry.yaml` validation, Claude credentials rotation.

Codex SSOTs: `codex/04-architecture/agent-orchestrator-overview.md`,
`codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md`

## Triggers

- Weekly (minimum cadence)
- After any orchestrator API change or Cloud Run revision
- When Cloud Run revision shows exit(3) or non-zero exit code
- After any slot-cron or plan-hygiene cron change
- When operator laptop is onboarded or re-configured

## Checklist

- [ ] (a) **Cloud Run revision exits 0**: agent-orchestrator Cloud Run deployment is healthy (no exit(3)). Check:
      `agent_orchestrator_cr_revision_exit3_2026_05_21.md` — RESOLVED or being actively diagnosed Run:
      `gcloud run services describe agent-orchestrator --region=asia-northeast1` — verify READY

- [ ] (b) **slot-cron-ff-pull.sh + slot-git-status-report.sh on operator laptop**: both crons installed and ran within
      10 minutes. Run: `bash unified-trading-pm/scripts/verify-slot-host-symmetry.sh` — exit 0 required

- [ ] (c) **Plan-hygiene cron active**: cron at `0 5 * * *` UTC runs daily. Check: `crontab -l` on planning VM — verify
      entry present Verify: last run timestamp in cron log < 25 hours ago

- [ ] (d) **Orphan-ping audit cron active every 4h**: Cloud Scheduler job `uts-prod-orphan-ping-audit` enabled. Run:
      `gcloud scheduler jobs describe uts-prod-orphan-ping-audit --location=asia-northeast1` Verify: schedule is
      `15 2,6,10,14,18,22 * * *` UTC

- [ ] (e) **Orchestrator dashboard accessible**: dashboard at port 8026 locally and at
      `agent-orchestrator.odum-research.com` in prod. Test: `curl -s http://localhost:8026/health` — verify 200 Test:
      Fleet tab shows all 10 VMs

- [ ] (f) **orchestrator_vm_registry.yaml validates**: `regen_vm_registry.py --check` exits 0. Run:
      `python3 scripts/orchestrator/regen_vm_registry.py --check`

- [ ] (g) **Claude credentials rotation staleness resolved**: the in-memory OAuth staleness issue described in
      `claude_credentials_rotation_in_memory_staleness_2026_05_21.md` has an operator-acked implementation plan. Check:
      issue status — BLOCKED-OPERATOR with recommended option documented, or RESOLVED with commit SHA

### E2E Orchestrator Verification

- (e2e-dispatch) **Dispatch flow audit**: spawn a worker slot via `/api/slots/<N>/spawn`, dispatch a task, confirm the
  slot picks it up and posts a result. Use local or staging backend.
- (mock-upstream) **Offline audit**: orchestrator health checks, plan hygiene cron, and slot management MUST be
  auditable without real VM fleet running.

## Success Criteria

- All 7 checklist items GREEN
- All 10 VMs show in Fleet tab dashboard
- Plan-hygiene cron + orphan-ping cron both healthy
- verify-slot-host-symmetry.sh exits 0

## Output Format

Result file at `plans/audit/results/orchestrator_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
