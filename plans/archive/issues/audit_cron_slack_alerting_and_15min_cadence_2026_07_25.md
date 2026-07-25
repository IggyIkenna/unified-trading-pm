---
doc_type: issue
title: >-
  Tighten audit-stale-gate-references/audit-false-done to a 15-min cadence and add open/close Slack alerting
summary: >
  Direct operator follow-up instruction (2026-07-25, same session as
  gate_completed_tasks_trusts_stale_done_after_checkbox_unflip_2026_07_25.md, which shipped the two audit scripts +
  their hourly/4h systemd timers): since each real script run measures ~5.4-5.6 s live on the orchestrator VM, tighten
  both timers to a 15-min cadence, and add Slack alerting that fires ONLY on a state transition — an OPEN alert the tick
  a finding first appears, a ✅ CLOSE alert the tick it clears, silence on every unchanged tick in between. Filed as its
  own issue doc (not appended to the now-`status: resolved`/archived parent) because the parent is closed and this is
  new, not-yet-done work — appending an open item to an archived doc would recreate the exact dual-tracking anti-pattern
  `/codex/11-project-management/issue-doc-lifecycle.md` exists to prevent. Not yet implemented — this doc was filed as
  part of a `/pre-compact` context checkpoint, before implementation started.
status: resolved
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [orchestrator, backlog, audit, slack, alerting, cron, systemd]
related:
  [
    /plans/archive/issues/gate_completed_tasks_trusts_stale_done_after_checkbox_unflip_2026_07_25.md,
    /codex/04-architecture/agent-orchestrator-backlog-state-alignment.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: 2026-07-25
parent_epic: agent_operating_framework_master
priority: P2
source: >-
  Interactive Claude Code session, operator instruction 2026-07-25: "yeah they should alert to slack only if there is an
  issue and also alert when its resolved. since they take seconds make then fire every 15 mins."
assigned_vm: NA
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
last_updated: 2026-07-25
locked_by:
resolved_by: >-
  agent-orchestrator@0643c1f (wrapper + slack.py + dedup_state), unified-trading-pm@804191951 + @27abe3155
  (enable_slack_alerts.sh generalization + operator-credential fix). Both timers verified live at 15-min cadence; both
  units' webhook env verified live via `systemctl show`; transition logic verified via 10 passing regression tests.
depends_on: []
---

# Tighten audit-cron cadence to 15 min + add open/close Slack alerting

> **✅ ARCHIVED 2026-07-25 — RESOLVED.** Both todos shipped in the same session that filed this doc: cadence tightened
> to 15 min (verified live via `systemctl list-timers`), and the open/close Slack notifier built + wired + verified (10
> passing regression tests + live webhook-env confirmation on the VM). See each todo's evidence line below.

## What's needed

Currently shipped (`agent-orchestrator@d266e7e`): `audit-stale-gate-references.timer` (hourly) and
`audit-false-done.timer` (every 4 h), both read-only, both measured ~5.4-5.6 s per real run on the live orchestrator VM.
The operator's follow-up instruction, given the low runtime, is:

1. **Tighten both to a 15-min cadence** — `OnUnitActiveSec=900` on `scripts/audit-stale-gate-references.timer` and
   `scripts/audit-false-done.timer` (currently 3600 / 14400).
2. **Add Slack alerting on state TRANSITIONS only** — not every tick:
   - An **OPEN** alert the tick a script's exit code goes `0 → nonzero` (a finding first appears).
   - A **✅ CLOSE** alert the tick it goes `nonzero → 0` (the finding clears).
   - **Silence** on every tick where the state is unchanged from the previous tick (an ongoing finding does NOT re-page
     every 15 min; nor does a persistently-clean run).

## Design notes (not yet built — for whoever implements this)

- Mirrors the dedup-by-state-transition convention already established for `agent-orchestrator-alerts`/`ci-failures`
  (`/codex/04-architecture/agent-orchestrator-alerting.md` — "standing conditions dedup by state-transition (fire on
  change / RESOLVED / re-remind), never every tick" and "every actionable alert that paged an OPEN gets a ✅ CLOSE
  bookend in-channel"). Reuse that webhook/notifier pattern rather than inventing a new one — check
  `server/notifications/slack.py` for an existing dedup-state helper (the codebase already has one for
  `activity_log_growth_alarm`, `notify_slot_blocked_answered`, etc. — read those before building a new primitive).
- Needs a persisted last-known-exit-code (or last-known-finding-count) per script, since each `systemd` invocation is a
  fresh process with no memory of the prior tick. Candidates: a small state file under
  `/var/lib/orchestrator/audit-cron-state/<name>.json`, or the existing `prerequisites`/dedup-state SQLite table if one
  already fits this shape — check `dedup_state.py` (referenced from the `activity_log_growth_alarm` precedent) before
  building a new storage mechanism.
- Both scripts already emit machine-parseable `--json` output (`stale_gate_references`/`false_done` counts + full
  per-finding detail) — the wrapper should capture that and put the actual finding list in the Slack message body, not
  just "something changed."
- This is a wrapper/notifier problem, not a runtime-budget problem — the underlying scripts are unaffected and stay
  exactly as they are (~5-6 s, read-only, no `--fix` mode).
- `SLACK_CI_WEBHOOK_URL` / `agent-orchestrator-alerts` webhook config — confirm which channel this belongs in
  (`agent-orchestrator-alerts`, described as actionable-only per CLAUDE.md, seems right — a stale gate reference or a
  false-done row is exactly the "worker BLOCKED question"-adjacent actionable class, not a routine lifecycle event).

## Todos

- [x] [INFRA] P2. ✅ **Change both timer cadences to 15 min** (`OnUnitActiveSec=900`) in
      `scripts/audit-stale-gate-references.timer` + `scripts/audit-false-done.timer` — `agent-orchestrator@0643c1f`.
      Re-ran `scripts/install-audit-crons.sh --operator ubuntu --start` on the live VM (`i-0c9b283b31d6b5ca7`).
      **Evidence**: live `systemctl list-timers` (2026-07-25 22:52 UTC) shows both timers with `LEFT 12min` off a
      `LAST ... 2min 53s ago` tick — matches the 15-min cadence exactly.
- [x] [INFRA] P2. ✅ **Built the open/close Slack notifier wrapper** — `agent-orchestrator@0643c1f`
      (`scripts/orchestrator/audit_cron_notify.py` + 4 new `notify_audit_*_breach`/`_resolved` functions in
      `server/notifications/slack.py` + 2 new bool-sentinel paths in `server/dedup_state.py`, reusing the existing
      dedup-by-state-transition + webhook pattern — no parallel mechanism invented) + `unified-trading-pm@804191951` and
      `@27abe3155` (generalized `enable_slack_alerts.sh` to wire the webhook into the two new systemd units, fixing a
      real root-vs-operator-credential mismatch discovered live: the VM's root instance-role lacks
      `secretsmanager:GetSecretValue` on this secret, so the script now runs as the operator user with internally
      `sudo`-prefixed privileged writes, mirroring `install-audit-crons.sh`'s identical pattern). Both `.service` units'
      `ExecStart` now routes through the wrapper (`--audit stale-gate-references` / `--audit false-done`). **Verified
      via a constructed test** (10 passing cases in `tests/test_audit_cron_notify.py` +
      `tests/test_slack_notifications.py`, exercising 0→nonzero fires-breach-once, nonzero→nonzero silent, nonzero→0
      fires-resolved-once, a full 4-tick lifecycle sequence, and a malformed-child-output crash path that deliberately
      does NOT page) **and confirmed live**: `systemctl show <unit> --property=Environment` on the VM confirms
      `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` is now genuinely present for both units (was previously absent — the units' own
      `EnvironmentFile=.env.local` line never carried it, a gap this work also closed). Did not fire a synthetic test
      page into the live `agent-orchestrator-alerts` channel — the constructed-test coverage plus the live env-var
      confirmation already meet this todo's done-when, and the channel is shared/human-monitored.
