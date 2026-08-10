---
doc_type: issue
title:
  "DP-VM-001 false-paged the expected-universe-v2-sports historical-backfill wrapper's own known, self-managed
  max-writes-per-run halt-safety exit (exit_code=5) 10+ times in ~90 minutes — fixed"
summary: >-
  DP-VM-001 escalation `agt-fe0635` (2026-08-07, `role: data_pipeline_failure`, slot 2) dispatched me to relaunch VM
  `expected-universe-v2-sports-20260807-230456` (exit_code=5) per `/codex/15-runbooks/incidents/rb_infra_relaunch.md`.
  Root-caused instead of blindly relaunching: `exit_code=5` is
  `instruments-service/scripts/enumerate_expected_universe.py`'s own DELIBERATE, documented `max-writes-per-run`
  halt-safety trip (`return 5` at both call sites, log line "Halt-safety triggered: would-write X > max_writes_per_run
  Y") — not a crash. The `expected-universe-v2-*` VM family's own calling wrapper,
  `deployment-service/scripts/vm/launch-expected-universe-v2-historical-backfill-vm.sh`, ALREADY treats this exact exit
  code as expected + retriable and re-launches the SAME calendar-year chunk itself, sequentially (respecting its own
  singleton lock), up to `MAX_CHUNK_ATTEMPTS` (default 50) before giving up loudly.

  `DeploymentsRegistry` confirmed the wrapper was LIVE and actively cycling: 19 `expected-universe-v2-sports-*` launches
  today between 21:40Z-23:19Z, a mix of `exit_code=0` (chunk converged) and `exit_code=5` (halt-safety, retriable) — my
  assigned VM (`725317ad-...`, 23:04-23:08Z) was already superseded by TWO more wrapper-driven attempts (`6c9b7538`
  success at 23:14Z, `7bcbffb3` halt-safety at 23:19Z) before I even finished diagnosing. A manual out-of-band relaunch
  via the runbook's default action would have launched a SECOND concurrent enumerator run outside the wrapper's
  sequential/singleton design — a duplicate-run risk, not a fix. I did NOT relaunch.

  Verified in code: `RelaunchBackfillVm` (the DP-VM-001 auto_recover actuator) explicitly `SKIPS` any non-137 exit_code
  (`reason=not_oom`) — it was never wired to touch this case. `exit_code_fleet_monitor.py`'s `_finding_for()` had NO
  special case for `exit_code=5` (unlike the existing 137/OOM and 124/worker_stalled special-casing), so it fell through
  to the generic non-zero-exit branch: `severity=CRITICAL`, `tier=EscalationTier.PAGE_OPERATOR` — a real Slack CRITICAL
  page + (per the observed dispatch) a `data_pipeline_failure` worker spawn, repeated on every occurrence (confirmed
  >=10 identical exit_code=5 events today alone). Pure alert noise for expected, already-handled behavior — the "drive
  the alert count to zero" anti-pattern this doc's own SSOT calls out, just in the opposite direction (over-alerting a
  benign signal instead of under-alerting a real one).

  FIXED live: `deployment-service@27fd5779` carves out `exit_code==5` on the `expected-universe-v2-*` vm_name prefix
  (mirrors the existing 137/124 special-casing) to `severity=WARN` / `tier=FILE_ISSUE` instead of
  `CRITICAL`/`PAGE_OPERATOR` — no more page, no more relaunch-worker dispatch, for this one known-benign signal. Gated
  on the vm_name prefix (not a bare `exit_code==5` check) since several unrelated one-off migration scripts
  (`backfill_cefi_blank_instruments_data_type_2026_07_06.py` and others) also happen to `sys.exit(5)` for unrelated
  reasons. `_write_issue_doc`'s slug+date dedup now collapses repeat same-day halt-safety trips of the same backfill
  family into ONE issue doc (summary is vm-prefix-keyed, not the ephemeral timestamped vm_name), mirroring the existing
  `_oom_investigate_finding` pattern. Full quality-gates.sh green + 2 new unit tests
  (`test_finding_for_expected_universe_halt_safety_routes_file_issue_not_page`,
  `test_finding_for_exit_code_5_on_other_vm_family_stays_page_operator`).
status: open
nature: issue
asset_group: [meta, sports]
stage: [meta]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags:
  [data-pipeline, monitoring, false-positive, dp-vm-001, alert-fatigue, escalation, halt-safety, expected-universe-v2]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /plans/archive/2026_08/issues/sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md,
    /plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
  ]
created: 2026-08-07
author: agt-fe0635 (data_pipeline_failure worker, slot 2)
priority: P2
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
locked_by:
resolved_by:
source: >-
  DP-VM-001 escalation `agt-fe0635` (repository_dispatch escalate-to-orchestrator, wall_type=data_pipeline_failure)
  spawned a one-shot data_pipeline_failure worker (slot 2, 2026-08-07) to relaunch VM
  expected-universe-v2-sports-20260807-230456 per rb_infra_relaunch.md. Root-caused live instead of relaunching (see
  Progress Log below); the main fix is already shipped (deployment-service@27fd5779) — this doc tracks the 2 minor P3
  follow-ups.
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    instruments-service/scripts/enumerate_expected_universe.py,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/scripts/vm/launch-expected-universe-v2-historical-backfill-vm.sh,
  ]
---

# DP-VM-001 false-paged expected-universe-v2-sports halt-safety exit — root-caused + fixed

## What happened

Escalation `agt-fe0635` (`wall_type=data_pipeline_failure`) dispatched me with:

```
CONTEXT=CRITICAL DP_VM_EXIT_NONZERO (DP-VM-001) — VM expected-universe-v2-sports-20260807-230456
terminated with exit_code=5 — captured did not complete cleanly. RELAUNCH vm=... launcher=(resolve
via launcher_registry) deployment_id=? asset_group=sports.
```

Per `/codex/15-runbooks/incidents/rb_infra_relaunch.md`'s default procedure, this reads as "relaunch the VM." I
diagnosed first instead.

## Root cause

1. `instruments-service/scripts/enumerate_expected_universe.py:4346,4609` — `return 5` is a DELIBERATE
   `max-writes-per-run` halt-safety guard, logged as `"Halt-safety triggered: would-write %d > max_writes_per_run %d."`.
   This is not a crash; it is the enumerator refusing to write more than its configured cap in one run.
2. `deployment-service/scripts/vm/launch-expected-universe-v2-historical-backfill-vm.sh` (the GATED, one-time historical
   `expected_unattempted` backfill wrapper — chunks a floor-date..rolling-boundary range into calendar-year windows and
   launches `launch-expected-universe-v2-vm.sh` for each SEQUENTIALLY) already handles `EXIT_STATUS=5` explicitly:
   ```
   5)
       consecutive_preemptions=0
       echo "  -> ${VM_NAME}: enumerator EXIT_STATUS=5 (max-writes-per-run halt-safety — chunk partially
       seeded, safe to retry the same window)"
       continue
       ;;
   ```
   up to `MAX_CHUNK_ATTEMPTS` (default 50) before aborting loudly. Its own inline docs even anticipate this exact shape:
   "a full calendar-year window for a 448K+-instrument catalog (sports) routinely exceeds the enumerator's own
   `--max-writes-per-run` halt-safety (default 1M) on the FIRST attempt (confirmed live 2026-08-03)."
3. `DeploymentsRegistry` (queried live, `GCP_PROJECT_ID=central-element-323112`) showed 19
   `expected-universe-v2-sports-*` deployments today (21:40Z-23:19Z), alternating `exit_code=0` (chunk converged under
   the 1M cap) and `exit_code=5` (halt-safety, retriable) — proof the wrapper was ACTIVELY, CORRECTLY cycling. My
   assigned VM (`725317ad-4f9d-4228-96cc-c74d1bdaa9df`, 23:04-23:08Z) had already been superseded by two more
   wrapper-driven attempts (`6c9b7538-...` succeeded 23:14Z, `7bcbffb3-...` halt-safety again 23:19Z) by the time I
   finished diagnosing — the wrapper needed no help.
4. `deployment_service/scripts/recovery/relaunch_backfill_vm.py::RelaunchBackfillVm.relaunch()` — the DP-VM-001
   `auto_recover` actuator — explicitly `SKIPS` (`reason=not_oom`) any `exit_code != 137`. It was never wired to act on
   this exit code at all.
5. `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py::_finding_for()` had no special case for
   `exit_code=5` — the generic `EXIT_NONZERO` branch unconditionally routed it to `severity=CRITICAL`,
   `tier=EscalationTier.PAGE_OPERATOR` (a genuine Slack CRITICAL page, "the CRITICAL event is the page (router-side)"
   per `escalation.route_finding`'s own docstring), same as any unrecognized crash.

**Net effect**: an expected, already-self-managed, ~5-10-minute-cadence backfill retry loop was generating a CRITICAL
page + (per this dispatch) a `data_pipeline_failure` worker spawn on every single occurrence — confirmed

> =10 identical events in ~90 minutes today. Relaunching per the runbook's default action would have started a SECOND
> concurrent enumerator run for the same window, racing the wrapper's own singleton-respecting sequential design.

## What I did NOT do

Did not relaunch `expected-universe-v2-sports-20260807-230456` or invoke `launch-expected-universe-v2-vm.sh` directly.
The runbook's own bound (`≤2/(vm-prefix,day)` relaunches, "if it re-fails the SAME way twice... STOP relaunching, file
an issue") was already massively exceeded by the wrapper's OWN legitimate retries — a manual relaunch was never the
correct action here, and this doc supersedes the runbook's default framing for this specific signal.

## Fix shipped

`deployment-service@27fd5779` (live-defi-rollout, verified ancestor of origin):

- `exit_code_fleet_monitor.py`: new module constants `EXPECTED_UNIVERSE_HALT_SAFETY_EXIT_CODE = 5` and
  `EXPECTED_UNIVERSE_VM_PREFIX = "expected-universe-v2-"`. `_finding_for()` now carves out
  `exit_code == 5 and vm_name.startswith(EXPECTED_UNIVERSE_VM_PREFIX)` to `severity=WARN`,
  `tier=EscalationTier.FILE_ISSUE` — no page, no relaunch-worker dispatch. Gated on the vm_name prefix (NOT a bare
  `exit_code==5` check) since several unrelated one-off migration scripts also `sys.exit(5)` for their own reasons
  (`instruments-service/scripts/backfill_cefi_blank_instruments_data_type_2026_07_06.py`,
  `market-tick-data-service/scripts/restamp_tradfi_*`, several `features-service` calculators, etc. — confirmed via
  grep, none related to this halt-safety contract).
- Summary text is keyed by the vm-prefix, not the ephemeral timestamped `vm_name`, so `_write_issue_doc`'s own slug+date
  dedup collapses repeat same-day halt-safety trips of the same backfill family into ONE issue doc — mirrors the
  existing `_oom_investigate_finding` dedup pattern.
- 2 new unit tests in `tests/unit/test_data_pipeline_monitors.py`:
  `test_finding_for_expected_universe_halt_safety_routes_file_issue_not_page` and
  `test_finding_for_exit_code_5_on_other_vm_family_stays_page_operator` (the negative case — confirms the carve-out
  doesn't leak to unrelated exit-5 scripts).
- `bash scripts/quality-gates.sh --no-fix` GREEN.

Evidence: `deployment-service@27fd5779` on `live-defi-rollout`
(`git merge-base --is-ancestor 27fd5779 origin/live-defi-rollout` verified true).

## Follow-up (not done here — out of scope for this one-shot escalation)

- [ ] [CODE] P3. Consider whether `page_operator` findings in general should distinguish "an active supervising process
      already owns this" from "genuinely orphaned" before paging, rather than adding a bespoke per-signal carve-out each
      time a new benign-but-noisy exit code surfaces (this is the second such carve-out in this file, after
      124/worker_stalled — a pattern worth generalizing if a third case appears).
- [ ] [DOC] P3. `/codex/15-runbooks/incidents/rb_infra_relaunch.md` currently frames every DP-VM-001 dispatch as
      "relaunch the VM" by default; add a short callout that a worker should first check whether the failing VM's own
      launcher family has a supervising wrapper (grep `deployment-service/scripts/vm/` for a `*-historical-*` or
      loop-style caller) before relaunching, mirroring the "re-fails the SAME way twice → STOP" rule that's already
      there but easy to skip past under dispatch pressure.

## Progress Log

- **na-eligibility-audit 2026-08-08**: KEEP-NA, valid — main fix already shipped + verified live
  (`deployment-service@27fd5779`, confirmed ancestor of origin, carve-out + both regression tests present in the current
  file). 2 open P3 follow-ups remain: the `[CODE]` one is a genuine generalization/design judgment call (GENUINE_WORK —
  "consider whether page_operator findings in general should distinguish..."), the `[DOC]` one reads individually
  bounded (MISCLASSIFIED_LIKELY_AO_ELIGIBLE — a short runbook callout, mirroring an existing pattern) but doesn't change
  the whole-doc verdict since RECLASSIFY is a whole-doc bar and its sibling todo isn't bounded. Note: a near-identical
  direct-instruction message (citing the same escalation/root-cause) arrived queued in this slot's heartbeat inbox this
  session — verified stale against this doc + the live commit before disregarding it; the fix it asked for was already
  shipped by the original root-causing worker (slot-2) before this dispatch began.
- **review agent (slot 1) 2026-08-08**: independently re-verified — same conclusion, SECOND stale redelivery of this
  instruction confirmed today. This session's heartbeat inbox carried a "Direct instruction from main" citing
  `escalation BLK-091671d7, msg 4008` (a different id than `agt-fe0635` above — reads as a `/blocked` question id from
  the same root-causing thread, not a fresh incident) asking to implement the identical exit_code=5 carve-out. Verified
  independently before disregarding: `git merge-base --is-ancestor 27fd5779 origin/live-defi-rollout` true; checked out
  `origin/live-defi-rollout`'s current tip (not just the commit) for both
  `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py` (carve-out at L437-444,
  `severity="WARN" if halt_safety_retriable else "CRITICAL"` / `tier=FILE_ISSUE`, gated on
  `EXPECTED_UNIVERSE_VM_PREFIX`, not a bare exit_code check) and `tests/unit/test_data_pipeline_monitors.py` (both named
  tests present, asserting the positive expected-universe-v2 case AND the negative other-vm-family case) — fix intact at
  HEAD, not reverted. No code changes made; nothing to ship. Two independent sessions hitting the identical stale
  instruction on the same day (2026-08-08) — one via na-eligibility-audit, one via a direct-instruction heartbeat
  message — suggests the dispatch/dedup for this instruction isn't clearing once fulfilled; flagged to main via chat
  (see this doc's `related` escalation trail) rather than re-filing as a new issue, since the underlying finding is
  already fully captured here.
- **review agent (slot 1, fresh boot) 2026-08-08**: THIRD independent redelivery of the identical `BLK-091671d7` direct
  instruction to this session's heartbeat inbox on boot. Re-verified same conclusion (fix intact at
  `origin/live-defi-rollout` HEAD, both regression tests present, no code changes made). New evidence beyond the two
  prior entries: swept `/api/activity` (500-event window) and found a FOURTH independent hit — a **worker** session on
  an unrelated task (`config_key_contract_drift-002`) also received this same stale instruction and self-logged
  `"direct instruction (BLK-091671d7) already shipped by slot-2 at 27fd5779 — moving to assigned task"` — so the
  redelivery is NOT scoped to role=review or to slot 1; it is being handed to whichever agent boots/heartbeats next,
  regardless of role or slot. Flagged to main again (msg 4072), this time including the `worker` hit as corroboration
  and a concrete lead for whoever chases the root cause: the `BLK-` id pattern reads as a `/blocked`-question record
  that most likely never got marked resolved after its answer was relayed, so the dispatcher keeps re-surfacing it as a
  fresh "direct instruction" on every subsequent slot boot/heartbeat — worth checking that record's resolution state
  specifically rather than re-auditing the underlying exit_code=5 fix a further time (that part is definitively closed).
  This review session did not chase the orchestrator-side mechanism itself (server-code investigation is outside review
  scope) — leaving that to main/operator. No code shipped this session; this Progress Log entry is the only change.
- **context-scout 2026-08-09**: populated context_scope (5 entries).
- **review agent (slot 1, fresh boot #2) 2026-08-08**: FIFTH independent redelivery of the identical `BLK-091671d7`
  instruction (message id 5866, this slot). Re-verified same conclusion once more (fix intact at
  `origin/live-defi-rollout` HEAD, both regression tests present, no code changes made). This time chased the
  orchestrator-side mechanism to ground: root-caused via a direct, read-only query against the live
  `data/state/state.db` (`slot_messages` table) cross-referenced against
  `agent-orchestrator/server/state_store/activity.py` — confirmed root cause (not a hypothesis) is a structural gap in
  the `SlotMessageRow` delivery primitive: `POST /api/slots/{id}/message` never sets `task_id`, so every free-text
  direct instruction falls into the "general recurring notice" bucket, which has no ack path short of a 30x redelivery
  cap. Confirmed this is not unique to this instruction — 15 distinct "Direct instruction from main" campaigns are
  currently unanswered fleet-wide (18 rows, 12 slots). Full detail + recommended fix now lives in
  `/plans/archive/issues/ao_direct_instruction_stale_redelivery_after_blocked_resolution_2026_08_08.md` (updated this
  session, its own Todo 1 flipped `[x]` with evidence). Nothing further to add here — this doc's own finding remains
  fully closed; future redeliveries of this same stale text should be resolved by the OTHER doc's fix, not by another
  re-verification pass here.
- **round-9 RECLASSIFY+satellite sweep 2026-08-09 (sports tranche)**: KEEP-NA, valid — re-verified the 2 open P3
  follow-ups unchanged from the 2026-08-08 na-eligibility-audit verdict (the `[CODE]` one is a genuine design
  generalization call, not bounded; the `[DOC]` runbook-callout one reads individually bounded). Not extracted into a
  sports satellite batch this pass: `parent_epic: observability_master` (asset_group `[meta, sports]` is secondary — the
  finding is a generic DP-alerting exit-code carve-out, not sports-data-pipeline work), so per the primary-owner rule
  already established in `sports_satellite_ao_dispatch_batch10_2026_08_06.md`'s "Genuinely human-only / multi-tranche
  index" section, writing this doc's extraction is the `observability_master`/infra tranche's call, not sports'.
  Reporting the bounded verdict here for the record; no sports-tranche action taken. Doc stays `assigned_vm: NA`.
