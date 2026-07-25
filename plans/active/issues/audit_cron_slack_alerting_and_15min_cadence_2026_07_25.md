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
  `codex/11-project-management/issue-doc-lifecycle.md` exists to prevent. Not yet implemented — this doc was filed as
  part of a `/pre-compact` context checkpoint, before implementation started.
status: open
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
resolved_by:
depends_on: []
---

# Tighten audit-cron cadence to 15 min + add open/close Slack alerting

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
  (`codex/04-architecture/agent-orchestrator-alerting.md` — "standing conditions dedup by state-transition (fire on
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

- [ ] [INFRA] P2. **Change both timer cadences to 15 min** (`OnUnitActiveSec=900`) in
      `scripts/audit-stale-gate-references.timer` + `scripts/audit-false-done.timer`, re-run
      `scripts/install-audit-crons.sh --operator ubuntu --start` on the live VM (`i-0c9b283b31d6b5ca7`) to pick up the
      change, and verify via `systemctl list-timers` that the new cadence is live. Done-when: both timers show a ≤15-min
      `LEFT` value in `systemctl list-timers` after the next tick.
- [ ] [INFRA] P2. **Build the open/close Slack notifier wrapper** per the design notes above (reuse the existing
      dedup-by-state-transition + webhook pattern from `agent-orchestrator-alerting.md`/`slack.py` — do not invent a
      parallel mechanism). Wire it as the `ExecStart` for both `.service` units (or a shared wrapper script both call)
      so a state-transition fires the appropriate Slack message; ship with a regression test exercising the 0→nonzero,
      nonzero→nonzero (no page), and nonzero→0 transitions. Done-when: a synthetic forced-finding run pages once on
      first detection, stays silent on a repeat detection, and posts a ✅ CLOSE the tick it's cleared — verified live or
      via a constructed test, not just code-reviewed.
