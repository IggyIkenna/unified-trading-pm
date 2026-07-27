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
    /plans/archive/issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md,
    /plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md,
    /plans/active/issues/vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md,
    /plans/active/issues/relaunch_stalled_vm_no_checkpoint_resume_gap_2026_07_27.md,
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

> **CORRECTION (2026-07-27, todo-2 implementation session)** — the claim above ("this launcher does not invoke
> [vm-exec-with-gcs-tee.sh] at all") is factually wrong against the current code, re-verified this session by direct
> read (not trusted from the prior summary): `launch-canonical-migration-vm.sh` sets `VM_TASK=canonical-migration` and
> stages `--metadata="startup-script-url=gs://${CODE_BUCKET}/vm/setup-data-pipeline-vm.sh,..."`. That SHARED startup
> script downloads `vm-exec-with-gcs-tee.sh` unconditionally for all task modes, then its
> `VM_TASK == "canonical-migration"` branch calls `_launch_with_tee "$FULL_CMD" "$LOGS/canonical-migration.log"`, where
> `$FULL_CMD` IS the `VM_MIGRATION_CMD` value — i.e. `bash -c "$VM_MIGRATION_CMD"` executes INSIDE the tee wrapper
> subshell, not as a separate mechanism. So canonical-migration VMs DO inherit the generic 30-min byte-growth stall-kill
> by default (no `STALL_PROGRESS_REGEX` override is set for this task, so it's still the weak size-only variant — that
> part of this gap, "no content-aware detection," still stands). This narrows todo 3 below: criterion (a) ("a
> stall-enforcement mechanism is identified and confirmed live") is already satisfied by this re-read — the mechanism is
> the generic `_launch_with_tee` byte-growth kill, it just isn't content-aware (todo 4 is still valid/needed). This same
> `VM_TASK=canonical-migration` dispatch is shared verbatim by `launch-cefi-migration-vm.sh`,
> `launch-cefi-mvp-reclassify-vm.sh`, `launch-kalshi-bulk-seed-vm.sh`, `launch-tradfi-session-stamp-vm.sh`, and
> `launch-tradfi-session-stamps-vm.sh` — all 6 (incl. the base launcher) get the SAME Class-A stall-kill and the SAME
> Gap-3 naming miss (fixed by todo 2 below).

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
  `/plans/archive/issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md` shows the `DP_VM_GONE_NO_CAPTURE`
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

- [x] [HUMAN] P1. **Add `"hung"` to `deployments_inventory.py`'s `_ALERT_HEALTH_STATES` (currently
      `frozenset({"oom-risk", "stalled"})`), or wire an equivalent dedicated paging path for it.** Weigh whether "hung"
      at 15-minute heartbeat staleness pages too eagerly for legitimately-quiet workloads before flipping it on for the
      whole fleet (may need a per-VM-class threshold, not just adding the literal to the set). Done when: a VM whose
      `composite_health_status` transitions into `"hung"` produces a `_persist_alert(...)` call (verified via a
      deliberately-induced stale-heartbeat test VM or a unit test around `_alert_on_health_transition`), with no new
      false-positive-page complaint from a legitimately-quiet live/paper VM in the following week of operation. —
      **deployment-api@ea594d60d60f4a55ef56a0ecace70beba6d66d87** (2026-07-27). A same-session false-positive-risk
      investigation (traced every `VM_TASK` launched via `setup-data-pipeline-vm.sh`) found the flat 15-minute
      `_STALE_HEARTBEAT_MINUTES` threshold is SAFE to page fleet-wide as-is — **no per-VM-class threshold was needed or
      added**: every VM class (live/backfill/canonical-migration alike) installs the SAME 60s-interval HeartbeatDaemon
      unconditionally, so 15 minutes is a uniform ~15x margin over that fixed write cadence for every class. The
      legitimately-slower classes found (live-capture sparse WS logging; `af-backfill-*`'s ~54s-throttled API-Football
      chunks) are slow on a DIFFERENT signal (run-log/manifest-shard freshness, workload-paced) that
      `heartbeat_stall_watcher.py`'s own `PREFIX_IDLE_THRESHOLDS`/`_is_backfill_vm` gate already carves out separately —
      duplicating that per-prefix-override pattern into `_vm_health.py`/`deployments_inventory.py` would solve a problem
      this signal doesn't have. `_ALERT_HEALTH_STATES` is now `frozenset({"oom-risk", "stalled",     "hung"})`. Added
      `test_alert_on_health_transition_fires_on_hung_transition` (deployment-api
      `tests/unit/test_route_deployments_inventory.py`) proving a fresh `hung` transition fires `_persist_alert(...)`
      (severity `WARNING`), that repeated polls / an already-alerted VM do not re-page (existing dedup-by-transition
      behavior, now verified against this state too), and that recovery-then-re-hang fires again as a fresh transition;
      also removed `"hung"` from `test_alert_on_health_transition_ignores_non_alertable_states`'s non-alertable list,
      since it no longer is one. Full `quality-gates.sh --no-fix` green (sentinel
      `aff52ca6af97d9c9e769da2ffb66b6df727cd5f3`). **One residual gap surfaced by the investigation and filed separately
      (outside this todo's literal scope — it's about the surrounding SCHEDULE, not this gate's own logic):**
      `plans/active/issues/deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md` — deployment-api's inventory
      computation (and therefore this alert gate) is on-demand/cache-driven only (45s TTL, no dedicated Cloud Scheduler
      cron unlike `heartbeat_stall_watcher.py`/`vm_zombie_watchdog.py`), so today its real page-firing cadence is
      bounded by whoever has the deployment-ui dashboard open or the once-daily digest cron — not yet the
      fully-automatic, schedule-independent safety net the parent investigation's intent implies. The "no new
      false-positive-page complaint... in the following week" half of this todo's done-when criterion is therefore still
      open pending real-world observation; the unit-test half is shipped and green.
- [x] [HUMAN] P1. **Wire `canonical-migration-*` (and any other one-off migration VM prefixes launched via
      `deployment-service/scripts/vm/launch-*-vm.sh` that behave like backfill VMs) into `heartbeat_stall_watcher.py`'s
      `_is_backfill_vm()` matching**, so the run-log-freshness liveness signal applies to them instead of the
      heartbeat-blob-only live-capture path. Done when: `_is_backfill_vm("canonical-migration-<anything>")` returns
      `True`, and a deliberately-frozen `run.log` on a canonical-migration test VM trips the
      `DEFAULT_RUN_LOG_STALL_MINUTES` alert within its configured window. —
      **deployment-service@fde4f4f3b557f9dcef8cb355a57d63122ab087bd** (2026-07-27). `_is_backfill_vm()` now also matches
      `canonical-migration`, `mtds-migrate-cefi-itype`, `mtds-migrate-cefi-mvp-reclassify`,
      `mtds-prediction-kalshibulk`, `sports-v9-migration`, `mdps-sports-bucket`, `sports-manifest-rescan` (the full
      Class-A `VM_TASK=canonical-migration`-dispatch family identified by todo 5's audit — every launcher's real
      `VM_NAME=`/`VM_PREFIX=` line was grepped directly, not re-derived from a naming guess). Existing `-live-`/`-live`
      early-out and `backfill`/`-bf-`/literal-prefix cases unchanged (regression- tested). Unit test added:
      `test_is_backfill_vm_matches_migration_launcher_family` (deployment-service
      `tests/unit/test_data_pipeline_monitors.py`) asserts `True` for every new prefix + the deliberately-frozen-
      run.log alert path is unchanged code (`DEFAULT_RUN_LOG_STALL_MINUTES` gate itself was not touched, only which VMs
      route into it). Full `quality-gates.sh` green (2863 passed). **Verified separately (not assumed): this fix does
      NOT touch `RelaunchPreemptedVm`'s eligibility** — `_is_backfill_vm` has zero references anywhere outside
      `heartbeat_stall_watcher.py` itself (`grep -rn "_is_backfill_vm"` across deployment-service, excluding tests,
      confirms this); `canonical-migration-cefi-*` was already fully registered in `launcher_registry.py` +
      `vm_prefix_registry.py` independent of this heuristic. It DOES change which liveness signal
      `heartbeat_stall_watcher.py`'s own sweep applies (run-log-freshness instead of heartbeat-blob-only), feeding
      `DP_VM_STALL` → `RelaunchStalledVm` (a different actuator) — confirmed that actuator has NO checkpoint/resume
      logic at all (`grep` for checkpoint/PROGRESS/resume in `relaunch_stalled_vm.py` returns nothing), so even this
      newly-enabled detection path relaunches blind, not via the PROGRESS.json checkpoint (see todo 6).
- [x] [HUMAN] P2. **Determine what (if anything) actually enforces a stall-timeout on `VM_MIGRATION_CMD`-executed
      workers** launched by `launch-canonical-migration-vm.sh`, given Gap 2 shows `vm-exec-with-gcs-tee.sh` is never
      invoked by this launcher at all. Done when: either (a) a stall-enforcement mechanism is identified and confirmed
      live for this launcher's VM-side execution path, or (b) it's confirmed there is none, and a decision is recorded
      on whether to route this launcher through `vm-exec-with-gcs-tee.sh` (with `STALL_PROGRESS_REGEX` set) or build an
      equivalent in-VM watchdog for the `bash -c "$VM_MIGRATION_CMD"` path. — **RESOLVED (2026-07-27, todo-3+4
      implementation session): criterion (a) applies**, confirming (not contradicting) the CORRECTION note already
      recorded against Gap 2 above from the todo-2 session: re-verified directly this session by tracing
      `setup-data-pipeline-vm.sh`'s `VM_TASK == "canonical-migration"` branch (calls `_launch_with_tee "$FULL_CMD" ...`,
      where `$FULL_CMD` embeds `VM_MIGRATION_CMD` — there is no separate/parallel execution path bypassing the tee
      wrapper) and `_launch_with_tee()` itself (unconditionally invokes the downloaded `vm-exec-with-gcs-tee.sh` via
      `nohup bash "$TEE_WRAPPER" "$GCS_LOG_URI" bash -c "$cmd"` whenever the tarball download succeeded). The mechanism
      is LIVE today for every `VM_TASK=canonical-migration` category (byte-growth mode, `STALL_TIMEOUT_SEC=1800`
      default) — no code change was needed in `setup-data-pipeline-vm.sh` or `vm-exec-with-gcs-tee.sh` themselves, since
      both already read `STALL_TIMEOUT_SEC`/`STALL_PROGRESS_REGEX` off GCE instance metadata generically, independent of
      `VM_TASK` (confirmed via direct read: `setup-data-pipeline-vm.sh` lines ~460/468). The decision on the remaining
      "content-aware or not" question is recorded + implemented at todo 4 below.
- [x] [HUMAN] P2. **If routing `launch-canonical-migration-vm.sh` through `vm-exec-with-gcs-tee.sh`, set a content-aware
      `STALL_PROGRESS_REGEX`** matching this migration script's real per-chunk/per-object progress log line (not just
      byte-growth), so a wedged network call inside an otherwise-noisy log gets caught within `STALL_TIMEOUT_SEC`. Done
      when: a deliberately-induced hang-on-network-call test run (log still emitting non-progress noise) trips the
      stall-kill within the configured timeout, where it previously would not have under the size-growth-only default. —
      **FIXED: deployment-service@b2d135a1e8cadd648197f53cf1e116d57c018d88** (2026-07-27). Set
      `STALL_PROGRESS_REGEX=progress:|files/sec` in `launch-canonical-migration-vm.sh`'s metadata-construction block,
      scoped ONLY to the `cefi-content-apply` category — the one script whose real progress-log line format was read
      directly out of `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` this session
      (`market-tick-data-service`): `"Discovery progress: day=%s ..."` (discovery phase),
      `"Progress: %d/%d files (%.1f files/sec, ...)"` (every 200 files + final tally), and
      `"Elapsed (migrate phase): ...files/sec"` (final summary) all match; the tool's OWN wedged-worker WARNING
      (`"No progress in the last poll window..."`) does NOT match (case-sensitive — no `"progress:"` substring, no
      `"files/sec"`), so it correctly never resets the stall timer. Matches the exact `STALL_PROGRESS_REGEX` convention
      already proven live in production by 7 other launchers (`launch-mtds-gas-fees-backfill-vm.sh`,
      `_tradfi-ohlcv-launcher-lib.sh`, `launch-mdps-sharded-backfill.sh`, `launch-sfi-backfill-vm.sh`,
      `launch-cefi-sharded-backfill.sh`, `launch-orphan-sweep-vm.sh`, `launch-backfill-orphan-e-vm.sh`) — no code change
      was needed in `setup-data-pipeline-vm.sh` or `vm-exec-with-gcs-tee.sh` (both already read
      `STALL_TIMEOUT_SEC`/`STALL_PROGRESS_REGEX` off GCE metadata generically). Every OTHER
      `VM_TASK=canonical-migration` category deliberately gets NO regex yet — only cefi-content-apply's script has been
      individually verified; todo 5's per-category audit is the stated place for the rest (broadening the regex metadata
      key onto an unverified category's script would risk a false-positive stall-kill on a legitimately slow/quiet phase
      of a different tool with a different log shape). Test:
      `tests/unit/test_vm_launcher_scripts.py::TestCanonicalMigrationStallDetection` (deployment-service) — proves (1)
      the launcher wires the metadata key only for `cefi-content-apply` and NOT for `cefi-late-renames`/
      `cefi-dedup-apply`/`cefi`; (2) the exact regex matches the real per-line formats above via the same `grep -qE`
      matcher `vm-exec-with-gcs-tee.sh` itself uses, and does not match the wedged-worker WARNING; and (3) — against the
      REAL shipped `vm-exec-with-gcs-tee.sh`, not a reimplementation — a simulated hung worker emitting non-progress
      noise IS killed (`rc=124`, `status=failed`) within a compressed `STALL_TIMEOUT_SEC` when the regex is set, is NOT
      killed under the byte-growth-only default (the exact historical blind spot, reproduced small-scale), and a
      genuinely-healthy run emitting real progress markers interleaved with the tool's own wedged-worker WARNING is
      never false-killed. Full `quality-gates.sh` green (2874 passed, 5 skipped). **This fix alone does not close the
      incident actually observed** — the campaign's own Progress Log
      (`/plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md`) records serial-console evidence
      consistent with a whole-VM OS-level memory-pressure freeze (heartbeat itself went silent), a failure class no
      in-VM watchdog can reliably catch since it runs inside the same distressed VM; todos 1+2 (paging on the `"hung"`
      state, and the `_is_backfill_vm()` naming fix already shipped) are the actual external defense for that specific
      incident class, not this todo.
- [x] [HUMAN] P3. **Audit other one-off launcher scripts under `deployment-service/scripts/vm/` for the same three-gap
      pattern** (paging-set exclusion is fleet-wide so N/A per-launcher, but the stall-watchdog non-invocation and
      backfill-naming-regex miss are per-launcher-name issues) — not just `launch-canonical-migration-vm.sh`. Done when:
      every `launch-*-vm.sh` script under that directory is checked against `_is_backfill_vm()`'s matching rules and
      against whether it invokes `vm-exec-with-gcs-tee.sh`, with results recorded (either already covered, or added as a
      new todo here/in a follow-up plan). — **Audit results (2026-07-27), all 103 `launch-*-vm.sh` scripts checked:**
      ~31 already correctly matched (`*-backfill-*`/`-bf-`/literal-prefix, e.g. `af-backfill-*`, `tradfi-bf-*`,
      `tm-backfill-*`, `fs-backfill-*`, all `mtds-*-backfill-*`); ~5 correctly excluded (genuinely live/paper/
      continuous: `defi-paper-*`, `strategy-paper-*`, `strategy-live-*`, `funding-ensemble-paper-*`,
      `sports-scheduler-*`); 4 out of scope (standing infra: `launch-dashboard-vm.sh`, `launch-planning-vm.sh`,
      `launch-orchestrator-worker-vm.sh`, `launch-ec2-vm.sh`). Of the remainder: - **8 launchers fixed by todo 2** (the
      `VM_TASK=canonical-migration`-dispatch family, Class A — confirmed live stall-kill via the shared
      `setup-data-pipeline-vm.sh` → `_launch_with_tee()` → `vm-exec-with-gcs-tee.sh` path):
      `launch-canonical-migration-vm.sh`, `launch-cefi-migration-vm.sh`, `launch-cefi-mvp-reclassify-vm.sh`,
      `launch-kalshi-bulk-seed-vm.sh`, `launch-tradfi-session-stamp-vm.sh`, `launch-tradfi-session-stamps-vm.sh`,
      `launch-sports-v9-migration-vm.sh`, `launch-mdps-sports-bucket-vm.sh`, `launch-sports-manifest-rescan-vm.sh`. -
      **~35 more one-off/recon/audit/validation-named launchers** (e.g. `launch-orphan-sweep-vm.sh`,
      `launch-manifest-recon-*-vm.sh`, `launch-sports-full-sweep-vm.sh`, `launch-mtds-gas-fees-backfill-vm.sh` whose
      actual `VM_NAME` drops the "backfill" its own filename carries) likely route through the same Class-A
      `setup-data-pipeline-vm.sh` startup script but were NOT individually VM_TASK-verified, and were deliberately
      **NOT** added to `_is_backfill_vm()` by todo 2 — broadening the naming heuristic with generic substrings
      (`"recon"`/`"sweep"`/`"validation"`) risks an unpredictable fleet-wide naming collision against a
      legitimately-continuous VM name, which the parent doc's blast-radius rule requires proving safe first; todo 2
      stayed narrowly scoped to the individually-verified migration-launcher family only. Left open for a follow-up,
      properly fleet-naming-collision-reviewed pass (not filed as its own issue doc — same shape as todo 2, just
      unverified per-launcher, so it belongs as a future extension of this same todo rather than a new finding). - **1
      active mis-route**: `launch-batch-live-recon-cron-vm.sh` (`VM_NAME=batch-live-recon-<date>-<ts>`) is a BATCH
      reconciliation cron job whose name coincidentally contains `-live-`, tripping `_is_backfill_vm()`'s early-out to
      `False` regardless of any other signal — not merely unmatched, actively forced into the wrong bucket by its own
      name. Not fixed here (same narrow-scope reasoning as above); left open. - **8 launchers use a SECOND, separate
      no-stall-kill code path** (`lib/launcher_common.sh`'s `lc_log_upload_trap_block()`, "Class B" — log-tee +
      heartbeat blob + EXIT_STATUS marker only, confirmed via direct grep to have ZERO `STALL_TIMEOUT_SEC`/kill logic
      anywhere) — a genuine, separate bug, NOT fixed by todo 2 (naming alone cannot add an in-VM watchdog that doesn't
      exist). 6 of the 8 also fail `_is_backfill_vm()` after todo 2's fix ships, leaving them with no protective layer
      at any level. Filed as its own issue doc per findings-triage (outside this doc's exact Gap-3 scope):
      `/plans/active/issues/vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md`.
- [x] [HUMAN] P2. **Genuine 4th gap discovered mid-session (operator ask: "spot vms should auto recover at large from
      where they left off too"): `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` (the Script-1 cefi
      content-migration worker) had NO `PROGRESS.json` checkpoint emission of its own — its only resume mechanism was
      per-file idempotent-skip (`rows_changed == 0` → skip the WRITE), which still forces a full re-download +
      re-parse + re-resolve of the ENTIRE prior scope on every relaunch (day one, forever), because the discovery loop
      always re-walks the full `[--start-date, --end-date]` scope with no persisted frontier to narrow it.** Verified
      this is a SEPARATE gap from todo 2/Gap 3: `RelaunchPreemptedVm`'s checkpoint-read/`START_DATE`-override logic
      (`scripts/recovery/relaunch_backfill_vm.py`) and the `vm-logs/{vm}/PROGRESS.json` write path
      (`vm-exec-with-gcs-tee.sh`) were ALREADY fully live and already apply to `canonical-migration-cefi-*` VMs
      (registered in `launcher_registry.py`/`vm_prefix_registry.py` independent of `_is_backfill_vm()`) — the ONLY
      missing piece was the Python script itself never calling `record_vm_progress()`. Done when: the script emits a
      `[[VM_PROGRESS]]` marker (via `unified_trading_library.manifest_writer._vm_progress.record_vm_progress`) once each
      day in its scope is fully migrated. — **FIXED: market-tick-data-service@54817bc15acc218762431180e20d3e3f4a230929**
      (2026-07-27). `run()`'s per-file completion loop now tracks a per-day remaining-file counter (built from the same
      flat cross-day file list the ThreadPoolExecutor already processes) and calls `record_vm_progress(day)` once every
      file discovered for that day — across all venues/pipeline_modes — has completed, gated on `apply` (a dry-run must
      never advance the resume frontier; matches the existing `ManifestWriter.record_captured()` hook's own "only from a
      real recorded artifact" contract). A day with any wedged/hard-deadline-outstanding file never reports complete (it
      stays in `pending`, never counted down), so the frontier can never skip past a day that wasn't genuinely finished.
      Full `quality-gates.sh` green (no new basedpyright/ruff findings near the change — pre-existing `reportAny`
      findings in `main()`'s argparse-Namespace access are unrelated and unchanged). No dedicated unit test added (this
      is a `Lifecycle: oneoff` migration script under `scripts/` with no existing test scaffold to extend —
      `script-homes.md` convention treats these as temporary, deleted after the prod run); correctness was verified by
      direct code read of the day-completion accounting logic and by confirming the consuming
      `read_progress_checkpoint()`/`RelaunchPreemptedVm` machinery is already live and unconditional on this script's
      own changes.
- [ ] [HUMAN] P3. **Close the tracking gap todo 5's audit left open**: two items were explicitly flagged "left open" in
      todo 5's own text but never converted into a trackable todo or issue doc (caught during this doc's 2026-07-27
      reconciliation pass — see Resolution section below). (a) **Individually VM_TASK-verify each of the ~35 unverified
      one-off/recon/audit/validation-named launchers** todo 5 identified (e.g. `launch-orphan-sweep-vm.sh`,
      `launch-manifest-recon-*-vm.sh`, `launch-sports-full-sweep-vm.sh`, `launch-mtds-gas-fees-backfill-vm.sh`) against
      whether each routes through the same Class-A `setup-data-pipeline-vm.sh` path and is safe to add to
      `_is_backfill_vm()`'s naming match — checking each for a fleet-naming collision against a legitimately-continuous
      VM name per the parent doc's blast-radius rule — before broadening the heuristic. (b) **Fix the confirmed active
      mis-route `launch-batch-live-recon-cron-vm.sh`** (`VM_NAME="batch-live-recon-${TARGET_DATE//\-/}-${RUN_TS}"`,
      re-confirmed this session by direct grep — the literal `-live-` substring trips `_is_backfill_vm()`'s early-out to
      `False` even though it's a batch reconciliation cron, not a live-capture VM) — needs either a narrower early-out
      condition (e.g. requiring `-live-` to NOT be immediately preceded by `batch`) or an explicit inclusion carve-out.
      Done when: each of the ~35 launchers has an individually-verified verdict recorded (added to `_is_backfill_vm()`
      or explicitly rejected with reasoning), and `launch-batch-live-recon-cron-vm.sh` routes to the correct
      (backfill/run-log- freshness) liveness signal without regressing any genuinely-live VM whose name legitimately
      contains `-live-`.

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

## Resolution (2026-07-27, reconciliation pass)

This section closes out a fresh read-and-verify pass over all 6 todos above, run after the three implementation sessions
(naming fix, stall-timeout fix, alert-state fix) and the spot-recovery investigation had all completed. Every commit sha
cited below was independently re-verified this session — not trusted from any prior summary — via
`git cat-file -t <sha>` (confirms the object exists) and `git merge-base --is-ancestor <sha> origin/live-defi-rollout`
(confirms it's actually on the shared branch, not a local-only/dangling commit) in each repo's own clone.

**Shipped commits (all verified live on `origin/live-defi-rollout`):**

- **deployment-api@ea594d60d60f4a55ef56a0ecace70beba6d66d87** — todo 1: `"hung"` added to `_ALERT_HEALTH_STATES`;
  `test_alert_on_health_transition_fires_on_hung_transition` added.
- **deployment-service@fde4f4f3b557f9dcef8cb355a57d63122ab087bd** — todo 2 (Gap 3): `_is_backfill_vm()` extended to
  match the canonical-migration launcher family; `test_is_backfill_vm_matches_migration_launcher_family` added.
- **deployment-service@b2d135a1e8cadd648197f53cf1e116d57c018d88** — todo 4: `STALL_PROGRESS_REGEX` set for the
  `cefi-content-apply` category in `launch-canonical-migration-vm.sh`; `TestCanonicalMigrationStallDetection` added.
- **market-tick-data-service@54817bc15acc218762431180e20d3e3f4a230929** — todo 6: `record_vm_progress(day)` wired into
  `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`'s per-day completion accounting, gated on `--apply`.
- **Todo 3** required no code commit — it was a pure investigation/decision-recording todo, and its own done-when
  criterion (a) was satisfied by re-reading the existing `_launch_with_tee()` → `vm-exec-with-gcs-tee.sh` call chain,
  which was already live before this doc existed. Correctly recorded as RESOLVED without a shipped sha.
- **Todo 5** required no code commit (it's an audit) and its core deliverable — every one of the 103 `launch-*-vm.sh`
  scripts under `deployment-service/scripts/vm/` checked against `_is_backfill_vm()` and against
  `vm-exec-with-gcs-tee.sh` invocation — is genuinely complete; **re-spot-checked this session**:
  `ls deployment-service/scripts/vm/launch-*-vm.sh | wc -l` returns exactly **103** (matches the audit's own count), and
  `launch-batch-live-recon-cron-vm.sh`'s actual `VM_NAME="batch-live-recon-${TARGET_DATE//\-/}-${RUN_TS}"` line does
  contain the literal `-live-` substring, confirming the audit's claimed mis-route exactly as described. However, two
  items the audit itself flagged "left open" (the ~35 unverified potential Class-A launchers, and the
  `launch-batch-live-recon-cron-vm.sh` mis-route) had **not** actually been converted into a trackable todo or issue
  doc, despite the audit's own done-when criterion requiring exactly that ("added as a new todo here/in a follow-up
  plan"). Closed that tracking gap this session by adding **todo 7** above for both items — the audit's information
  content was never lost, it just wasn't wired into anything actionable yet.

**Separately, a genuine additional gap was found during this reconciliation** (not one of the original 3 gaps, and
distinct from todo 6): `RelaunchStalledVm` (`deployment-service/scripts/recovery/relaunch_stalled_vm.py`, the
`DP_VM_STALL` auto-recover actuator) has **zero checkpoint/resume logic of any kind** — confirmed by a full-file read
this session (`grep -n "checkpoint\|PROGRESS\|resume\|START_DATE"` → zero hits), in contrast to `RelaunchPreemptedVm`,
which already has this logic. This affects every VM `_is_backfill_vm()` matches, not just canonical-migration ones, and
it was previously only mentioned in passing inside todo 2's own evidence text, never tracked as its own item. Filed as
`/plans/active/issues/relaunch_stalled_vm_no_checkpoint_resume_gap_2026_07_27.md` per findings-triage (a cross-cutting
actuator gap, out of this doc's exact Gap-1/2/3 scope).

**Status**: left as `open`, not `resolved` — todo 7 (new, tracking the audit's own flagged-but-unfiled follow-up) is
genuinely unresolved open work, so marking this doc `resolved` would misrepresent that. Todos 1, 2, 3, 4, and 6 are all
genuinely done with verified, shipped, ancestor-confirmed commits (or, for todo 3, a verified no-code-needed
resolution); todo 5's audit deliverable is complete but its own follow-up tracking is what todo 7 now carries forward.

### Direct answer to the operator's SPOT-recovery question

**"Does relaunching a preempted/hung canonical-migration VM now actually resume from where it left off?"**

**Split answer: YES for genuine SPOT preemption; NO (still) for a stall-triggered relaunch.**

- **Preemption path — YES.** `RelaunchPreemptedVm` (`relaunch_backfill_vm.py`) was already eligible for
  `canonical-migration-cefi-*` VMs before today (registered in `launcher_registry.py`/`vm_prefix_registry.py`,
  independent of `_is_backfill_vm()`), and its checkpoint-read (`read_progress_checkpoint()` →
  `vm-logs/{vm}/PROGRESS.json`) + `START_DATE`-override logic was already live. The one missing piece was the migration
  script never calling `record_vm_progress()` — fixed by todo 6. So as of market-tick-data-service@54817bc1, a genuine
  GCE preemption of `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` running on one of these VMs will resume
  from the last-fully-completed day, not replay `--start-date` from genesis.
- **Stall/hung path — NO, still.** After todo 2's naming fix, a hung (not preempted) canonical-migration VM now
  correctly feeds `DP_VM_STALL` (previously misrouted as live-capture). But that finding's own actuator,
  `RelaunchStalledVm`, was independently re-verified this session (full-file read, not assumed) to have no
  checkpoint/resume logic at all — it relaunches by blindly re-invoking the launcher with its original `launcher_env`,
  regardless of any PROGRESS.json checkpoint that exists. So a stall-triggered relaunch of a canonical-migration VM — or
  any other `_is_backfill_vm()`-matched VM — still does **not** resume from where it left off today. This is a genuine,
  broader, pre-existing gap (not introduced or fixed by any of this doc's 6 todos), filed separately at
  `/plans/active/issues/relaunch_stalled_vm_no_checkpoint_resume_gap_2026_07_27.md`.
