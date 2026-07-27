---
doc_type: issue
title: >-
  cefi Script-1 canonical-migration campaign: 10/42 GCE VMs silently hung (GCE reported RUNNING, actual workload stalled
  1-2.5h+) — caught only by a manual staleness sweep, not any automatic system
summary: >-
  Found live during /plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md's Script-1 corpus-wide
  content-backfill campaign (42-VM fan-out), 2026-07-27. 10 of the 42 VMs were reported RUNNING by GCE but their actual
  migration workload had stalled 1-2.5+ hours with zero heartbeat/progress — caught only via a manual
  staleness-vs-wallclock sweep by the operator/agent during interactive `/autonomous` monitoring, not by any automatic
  system. Direct code-read this session confirms THREE independent, already-shipped mechanisms that should have caught
  this each have a gap that let it through: (1) deployment-api's composite health classifier DOES compute a real
  `"hung"` state off heartbeat staleness, but `"hung"` is never a member of the alert-paging set — it is structurally
  excluded, not bugged; (2) the generic in-VM stall-watchdog script defaults to raw log-byte-growth (content-blind,
  30min timeout) and is never even invoked by this specific launcher (VM-side execution goes through a different
  GCE-metadata + `bash -c` path instead); (3) the fleet-wide heartbeat/run-log stall watcher's backfill-vs-live naming
  heuristic does not match the `canonical-migration-*` prefix, so these VMs get treated as live-capture
  (heartbeat-blob-only liveness) instead of backfill (run-log-freshness liveness), despite being a batch workload that
  logs continuously. This is a monitoring/observability gap, not a data-correctness issue — no data was lost, the
  migration was simply invisible while wedged. Per operator ruling this is human-prioritized work, not
  agent-orchestrator-dispatched, for now.
status: open
nature: issue
asset_group: [infrastructure, cefi]
stage: [data, meta]
repos: [deployment-api, deployment-service]
scope: [engineer]
tags:
  [
    vm-monitoring,
    hung-vm,
    fleet-auto-kill,
    stall-detection,
    heartbeat,
    canonical-migration,
    deployment-observability,
    script-1,
    cefi-migration,
  ]
related:
  [
    /plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /plans/active/issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md,
    /plans/active/issues/vm_fleet_preemption_autorecovery_gap_2026_07_23.md,
    /plans/active/issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md,
    /plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P2
estimate_class: infra
assigned_role: infrastructure
source:
  "Found live during interactive `/autonomous` session monitoring of the cefi Script-1
  (migrate_cefi_content_instrument_id_catalogue_2026_07_17.py) corpus-wide --apply campaign under
  /plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md, 2026-07-27 — 10/42 VMs found hung only via a
  manual staleness-vs-wallclock sweep of the fleet. All code-path claims in this doc were independently re-verified this
  session by direct file read (not trusted from any prior summary)."
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# cefi Script-1 canonical-migration campaign: 10/42 GCE VMs silently hung — no automatic detection

> Investigation-only record (this doc). No code was changed, no alert states were added, no watcher regex was modified,
> no VMs were killed or relaunched while authoring this doc. Per operator directive this is human- prioritized planning
> work — `assigned_vm: NA`, `execution_scope: local-only` — a human decides when to pick up the fix todos below; nothing
> here is agent-orchestrator-dispatched.

## What I found

During the cefi Script-1 42-VM content-backfill migration fan-out
(`/plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md`), 10 of the 42 GCE VMs were reported
`RUNNING` by GCE's own instance status the entire time, but their actual migration workload had stalled 1-2.5+ hours
with no heartbeat/progress advancing. This was caught only by a manual staleness-vs-wallclock sweep run by the
operator/agent during interactive `/autonomous` monitoring — comparing each VM's last-observed progress timestamp
against wall-clock time by hand. No automatic system (dashboard alert, Slack page, fleet auto-kill) flagged any of the
10 stuck VMs on its own.

Re-reading the actual monitoring code this session (not trusting any prior summary) shows this is not a bug in one
system — it's three separate, already-shipped mechanisms each having a gap that, in combination, left this class of
failure completely unmonitored.

## Gap 1 — the "hung" classifier is computed correctly, but is structurally excluded from paging

`deployment-api/deployment_api/routes/_vm_health.py`:

- Line 19: `_STALE_HEARTBEAT_MINUTES = 15`, with the docstring at line 18: "A running VM whose heartbeat is older than
  this is stale/hung."
- `composite_health_status(...)` (lines 71-132), the relevant body at lines 111-116:
  ```python
      if entry.status != "running":
          return None
      if control_plane_running is False:
          return "dead"
      if hb_age_seconds is not None and hb_age_seconds > _STALE_HEARTBEAT_MINUTES * 60:
          return "hung"
  ```
  So `"hung"` is a real, live, actively-computed state today: GCE status `running` + heartbeat older than 15 minutes.

`deployment-api/deployment_api/routes/deployments_inventory.py`:

- Line 362: `_ALERT_HEALTH_STATES = frozenset({"oom-risk", "stalled"})`.
- The paging gate, `_alert_on_health_transition()` (lines 706-724), fires `_persist_alert(...)` only when
  `status in _ALERT_HEALTH_STATES` on a fresh transition (called at line 1981 per inventory item).
- `"hung"` is not a member of that frozenset. A repo-wide grep (`grep -n '"hung"' deployment_api/routes/*.py`) shows
  `"hung"` referenced only where it is produced (`_vm_health.py`) and never in `deployments_inventory.py` at all — it is
  never added to the alert set nor mentioned near the gate. The full state enum is documented at
  `deployments_inventory.py` line 431: `dead|hung|disk-full|oom-risk|working|stalled|workload-dead|unknown`.
- Net effect: a VM can sit in `composite_health_status == "hung"` indefinitely and never trigger a single alert. This is
  not a race or an edge case — it is the literal, permanent shape of the hardcoded set.
- Side note also confirmed: `"stalled"` (the other alertable state) only fires for the BATCH umbrella today — LIVE/PAPER
  degrade to `"unknown"` per `_vm_health.py` lines 83-91 — so in practice this path pages almost exclusively on
  `"oom-risk"` transitions right now.

## Gap 2 — the generic in-VM stall-watchdog is content-blind by default, and this launcher doesn't even invoke it

`deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh`:

- Line 192: `STALL_TIMEOUT_SEC="${STALL_TIMEOUT_SEC:-1800}"` (30 min default).
- Line 208: `STALL_PROGRESS_REGEX="${STALL_PROGRESS_REGEX:-}"` — empty/unset by default.
- Default-mode branch (lines 270-276) resets the stall clock purely on `stat -c %s` raw log-byte-growth, not on any
  content match — the file's own comment (lines 194-199) states this explicitly: raw size grows on ANY output
  (heartbeats, empty-date "no events" lines), so a worker that hangs on a network call while the log keeps emitting
  noise is NOT caught by the default mode. Content-aware matching only activates when a caller sets
  `STALL_PROGRESS_REGEX` (lines 254-264).

`deployment-service/scripts/vm/launch-canonical-migration-vm.sh`:

- `grep -n "STALL_TIMEOUT_SEC\|STALL_PROGRESS_REGEX\|STALL"` → zero matches.
- `grep -n "vm-exec-with-gcs-tee"` → zero matches — this launcher does not invoke that watchdog script at all.
- Instead, VM-side execution runs through a `VM_MIGRATION_CMD` GCE-instance-metadata value (line 1230:
  `md="${md},VM_MIGRATION_CMD=${cmd}"`), executed per the file's own comment (line 266) via
  `bash -c "$VM_MIGRATION_CMD"` — a wholly separate mechanism from `vm-exec-with-gcs-tee.sh`'s watchdog subshell.
- Net effect: canonical-migration workers get neither the (weak, size-only) 30-min default from this script, nor any
  content-aware stall detection — whatever in-VM stall protection exists for them, if any, is not this script.

## Gap 3 — the fleet-wide heartbeat/run-log stall watcher's naming heuristic doesn't match this launcher's prefix

`deployment-service/deployment_service/data_pipeline_monitors/heartbeat_stall_watcher.py`, `_is_backfill_vm()` (lines
113-126):

```python
def _is_backfill_vm(vm_name: str) -> bool:
    lowered = vm_name.lower()
    if "-live-" in lowered or lowered.endswith("-live"):
        return False
    return "backfill" in lowered or "-bf-" in lowered or lowered.startswith(("tradfi-bf", "tm-backfill", "fs-backfill"))
```

- A name like `canonical-migration-<tag>` contains no `-live-`/`-live` (doesn't early-out False for that reason), but
  also contains no substring `backfill`, no substring `-bf-`, and starts with none of the three hardcoded literal
  prefixes. Every branch of the OR chain fails → `_is_backfill_vm("canonical-migration-...")` returns `False`.
- Per the function's own docstring, that routes canonical-migration VMs into the **live-capture liveness path**
  (heartbeat-blob freshness only) instead of the **backfill liveness path** (run-log-freshness,
  `DEFAULT_RUN_LOG_STALL_MINUTES=90`, meaningful because backfill VMs log continuously per date/chunk) — even though a
  canonical-migration VM is actually a batch job with continuous progress-per-chunk logging, i.e. exactly the shape this
  watcher's run-log-freshness signal is designed for.
- `grep -n "canonical" heartbeat_stall_watcher.py` → zero hits. No special-case handling exists anywhere in the file.

## Net effect (what actually happened this session)

10/42 canonical-migration VMs sat hung for 1-2.5+ hours with GCE reporting them `RUNNING`. None of the three mechanisms
above caught it automatically: Gap 1 means even if heartbeat staleness were the detection signal, the resulting `"hung"`
state doesn't page. Gap 2 means this launcher's workers aren't protected by the generic in-VM watchdog at all. Gap 3
means the fleet-wide log-freshness watcher misclassifies these VMs as live-capture and doesn't apply its
run-log-staleness check to them. The only thing that caught the 10 stuck VMs was a human/agent manually comparing
timestamps to wall-clock time.

## What this is NOT

- **Not a duplicate of the SPOT-preemption detection gap.** `/codex/05-infrastructure/spot-vms-for-backfill.md`'s HARD
  RULE section (lines 136-160) and `/plans/active/issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md` are
  scoped specifically to "is this VM preempted" — a distinct question from this doc's, which is about VMs GCE still
  reports as genuinely `RUNNING` whose workload is simply wedged (hung, not preempted). Preemption detection being
  manual for one-off VMs does not imply anything about hung-but-running detection; they are different failure modes with
  different (also-gapped) mechanisms.
- **Not a claim that migration VMs get zero fleet coverage.**
  `/plans/active/issues/vm_fleet_preemption_autorecovery_gap_2026_07_23.md` shows canonical-migration-* VMs ARE
  registered in `launcher_registry.py`/`vm_prefix_registry.py` for preemption-signal purposes, and
  `/plans/active/issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md` shows the `DP_VM_GONE_NO_CAPTURE`
  hung/stall alert DID fire once against a canonical-migration-* VM (albeit miscategorized). Coverage is partial and
  buggy in places, not structurally absent everywhere — this doc documents three specific, verified gaps (paging
  exclusion of `"hung"`, this launcher's stall-watchdog non-invocation, and the fleet watcher's naming-regex miss), not
  a blanket "migration VMs are unmonitored" claim.
- **Not itself a fix.** No code was changed while authoring this doc — see the banner above.

## Current workaround (does not fix the underlying gap)

A manual staleness-vs-wallclock sweep during interactive `/autonomous` monitoring of the Script-1 campaign — comparing
each VM's last observed progress against wall-clock time by hand, once per check-in. This is not scheduled, not
automatic, and depends entirely on someone deciding to look and knowing to look at ALL 42 VMs rather than trusting GCE's
`RUNNING` status at face value.

## What's NOT done / follow-up needed

- [ ] [HUMAN] P1. **Add `"hung"` to `deployments_inventory.py`'s `_ALERT_HEALTH_STATES` (currently
      `frozenset({"oom-risk", "stalled"})`), or wire an equivalent dedicated paging path for it.** Weigh whether "hung"
      at 15-minute heartbeat staleness pages too eagerly for legitimately-quiet workloads before flipping it on for the
      whole fleet (may need a per-VM-class threshold, not just adding the literal to the set). Done when: a VM whose
      `composite_health_status` transitions into `"hung"` produces a `_persist_alert(...)` call (verified via a
      deliberately-induced stale-heartbeat test VM or a unit test around `_alert_on_health_transition`), with no new
      false-positive-page complaint from a legitimately-quiet live/paper VM in the following week of operation.
- [ ] [HUMAN] P1. **Wire `canonical-migration-*` (and any other one-off migration VM prefixes launched via
      `deployment-service/scripts/vm/launch-*-vm.sh` that behave like backfill VMs) into `heartbeat_stall_watcher.py`'s
      `_is_backfill_vm()` matching**, so the run-log-freshness liveness signal applies to them instead of the
      heartbeat-blob-only live-capture path. Done when: `_is_backfill_vm("canonical-migration-<anything>")` returns
      `True`, and a deliberately-frozen `run.log` on a canonical-migration test VM trips the
      `DEFAULT_RUN_LOG_STALL_MINUTES` alert within its configured window.
- [ ] [HUMAN] P2. **Determine what (if anything) actually enforces a stall-timeout on `VM_MIGRATION_CMD`-executed
      workers** launched by `launch-canonical-migration-vm.sh`, given Gap 2 shows `vm-exec-with-gcs-tee.sh` is never
      invoked by this launcher at all. Done when: either (a) a stall-enforcement mechanism is identified and confirmed
      live for this launcher's VM-side execution path, or (b) it's confirmed there is none, and a decision is recorded
      on whether to route this launcher through `vm-exec-with-gcs-tee.sh` (with `STALL_PROGRESS_REGEX` set) or build an
      equivalent in-VM watchdog for the `bash -c "$VM_MIGRATION_CMD"` path.
- [ ] [HUMAN] P2. **If routing `launch-canonical-migration-vm.sh` through `vm-exec-with-gcs-tee.sh`, set a content-aware
      `STALL_PROGRESS_REGEX`** matching this migration script's real per-chunk/per-object progress log line (not just
      byte-growth), so a wedged network call inside an otherwise-noisy log gets caught within `STALL_TIMEOUT_SEC`. Done
      when: a deliberately-induced hang-on-network-call test run (log still emitting non-progress noise) trips the
      stall-kill within the configured timeout, where it previously would not have under the size-growth-only default.
- [ ] [HUMAN] P3. **Audit other one-off launcher scripts under `deployment-service/scripts/vm/` for the same three-gap
      pattern** (paging-set exclusion is fleet-wide so N/A per-launcher, but the stall-watchdog non-invocation and
      backfill-naming-regex miss are per-launcher-name issues) — not just `launch-canonical-migration-vm.sh`. Done when:
      every `launch-*-vm.sh` script under that directory is checked against `_is_backfill_vm()`'s matching rules and
      against whether it invokes `vm-exec-with-gcs-tee.sh`, with results recorded (either already covered, or added as a
      new todo here/in a follow-up plan).

## Evidence / how to reproduce

```bash
# Gap 1 — the "hung" state exists but is excluded from paging
grep -n '_STALE_HEARTBEAT_MINUTES\|def composite_health_status' \
  deployment-api/deployment_api/routes/_vm_health.py
grep -n '_ALERT_HEALTH_STATES\|def _alert_on_health_transition\|"hung"' \
  deployment-api/deployment_api/routes/deployments_inventory.py deployment-api/deployment_api/routes/_vm_health.py

# Gap 2 — the generic stall-watchdog defaults + this launcher's non-use of it
grep -n 'STALL_TIMEOUT_SEC\|STALL_PROGRESS_REGEX' deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh
grep -n 'STALL_TIMEOUT_SEC\|STALL_PROGRESS_REGEX\|vm-exec-with-gcs-tee' \
  deployment-service/scripts/vm/launch-canonical-migration-vm.sh   # expect: zero matches

# Gap 3 — the fleet stall watcher's backfill-naming heuristic
grep -n 'def _is_backfill_vm\|canonical' \
  deployment-service/deployment_service/data_pipeline_monitors/heartbeat_stall_watcher.py   # "canonical": zero hits
```

10/42-hung and the 1-2.5h+ stall durations were observed operationally during this session's manual fleet sweep during
the Script-1 campaign — there is no separate artifact/log file cited for that count beyond the campaign's own Progress
Log entries in `/plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md`.
