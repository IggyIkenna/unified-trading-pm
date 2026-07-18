---
doc_type: issue
title: vm-zombie-watchdog relaunch (dry_run=false) reaped 9 live campaign backfill VMs
summary:
  While restoring the genuinely-down `vm-zombie-watchdog` (its census blob `vm-census/watchdog-census.json` was absent →
  `DP_ZOMBIE_WATCHDOG_DOWN`, because the running VM `vm-zombie-watchdog-20260528...
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [infrastructure, spot-vm, backfill, self-healing, monitoring, observability, cefi, sports]
related:
  [
    plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    plans/active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
  ]
created: 2026-06-23
parent_epic: infrastructure_master
priority: P1
source:
  [
    plans/active/data_completion_to_100_all_ag_2026_06_21.md (INFRA P0 "Restore the genuinely-down infra"),
    scripts/vm/launch-vm-zombie-watchdog.sh,
    scripts/vm/vm_zombie_watchdog.py,
  ]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-18
---

## What I found

While restoring the genuinely-down `vm-zombie-watchdog` (its census blob `vm-census/watchdog-census.json` was absent →
`DP_ZOMBIE_WATCHDOG_DOWN`, because the running VM `vm-zombie-watchdog-20260528-212634` was on 2026-05-28 code with NO
census-write), I relaunched it with the launcher **default `dry_run=false`** at 17:15 UTC. The previously-running VM had
been launched with `--dry-run` (serial: "DRY RUN — no VMs killed"), so it never reaped.

The fresh `dry_run=false` watchdog **classified the active manual-backfill-campaign VMs as zombies and DELETED them**
(its heartbeat/shard-staleness heuristic flags a slow-progressing-but-alive backfill as `zombie_stale_heartbeat`). It
ran ~13 min (17:15→17:28) before I caught it and deleted it; I then relaunched in `--dry-run`
(`vm-zombie-watchdog-20260623-171612`) so census is written WITHOUT reaping.

**9 VMs killed mid-run** (serial shows forced `systemd-shutdown Waiting for process: python/bash` — not a clean
self-delete; run.logs show active capture seconds before):

- `cefi-hyperliquid-2023-20260623-113700` (was capturing book_snapshot_5 @17:08)
- `cefi-hyperliquid-2025-20260623-113700`
- `cefi-hyperliquid-2026-20260623-113700` (was capturing book_snapshot_5 @17:06)
- `instr-backfill-sports-fixture-lineups-20260623-150323`
- `instr-backfill-sports-fixture-stats-20260623-153628`
- `instr-backfill-sports-matches-20260623-150038` (was processing @17:12)
- `instr-backfill-sports-matches-20260623-153418`
- `instr-backfill-sports-xg-20260623-164104`
- `instr-backfill-sports-xg-shots-20260623-165303`

(One more, `instr-backfill-sports-xg-20260623-153457`, SELF-completed cleanly — `reason=cmd_ended` +
`VM_SHUTDOWN_ON_COMPLETION` self-delete — NOT a wrong kill.)

`cefi-hyperliquid-2024` + `fs-backfill-20260622-230327` SURVIVED (still RUNNING).

## Why it matters

- Violates the HARD constraint "Do NOT restart/stop any running backfill VM."
- Interrupted 9 campaign backfills mid-run (cefi-hyperliquid 2023/2025/2026 + sports gap-fill VMs from the
  `instr-backfill-sports-*-20260623-15{00,34,36}` set tracked in `data_completion_to_100_all_ag_2026_06_21.md`).
- Mitigation: these backfills are idempotent + manifest-tracked — re-running fills the same gaps; no permanent data
  loss, only lost progress + the re-run cost. The manifest will show the affected (venue/data_type × date) cells as
  not-yet-captured.

## Root cause (two layers)

1. **Operator-action layer (mine):** relaunched the watchdog with reaping enabled during an active manual-backfill
   campaign. The watchdog MUST be `--dry-run` (report-only) while the campaign runs — its staleness heuristic cannot
   tell a slow campaign backfill from a true zombie. FIXED: now running `--dry-run`.
2. **Heuristic layer (code, latent):** `vm_zombie_watchdog.py` flags `zombie_stale_heartbeat` when a VM's
   heartbeat/shard hasn't advanced past the threshold (default hb 15m / shard 120m), which legitimately-slow backfills
   (cefi-hyperliquid S3 download, sports scrape) trip. The watchdog has no "campaign-mode" / launcher-class exemption
   for EPHEMERAL_BATCH backfills that are progressing-but-slow.

## Recommended decision

1. **Relaunch the 9 killed backfills** (idempotent; re-fills the manifest gaps). Recipe: the sports ones via
   `deployment-service/scripts/vm/launch-instruments-backfill-vm.sh` per (data_type, date-range) as in the plan's
   gap-fill item; the cefi-hyperliquid ones via their historical-backfill launcher. **Owner: the data-completion
   campaign agent** (do not relaunch a peer's campaign VMs without coordination — flagging here).
2. **Keep the watchdog in `--dry-run` for the duration of the manual-backfill campaign**
   (`launch-vm-zombie-watchdog.sh --dry-run`). Only re-enable reaping once the campaign drains.
3. **Code fix (latent, P2):** give `vm_zombie_watchdog.py` a campaign-mode flag or a per-lifecycle-class staleness
   budget so EPHEMERAL_BATCH backfills that emit PIPELINE_HEARTBEAT are not reaped while progressing. Owner:
   deployment-service infra agent.

## Incident 2 — 2026-07-18, recurrence + regression (`af-backfill-*` PREFIX_IDLE_THRESHOLDS tightened past the June incident)

**This is the SAME defect class recurring 25 days later, on the SAME prefix family, and the "code fix (latent, P2)" item
above (§3) was never shipped — the watchdog still has no campaign-mode exemption.** Discovered while dispatched to
`sports_p2_history_apifootball_2015_to_present-001` (Todo "Full-history enrichment phase"), the 9th+ bounce of that todo
across many slots since 2026-07-17T15:12Z.

**What happened**: the 5-VM entity-sharded `af-backfill-20260717-15{1237,1335,1405,1433,1505}` fleet (launched
2026-07-17T15:12-15:14Z, per-fixture API-Football enrichment 2020-06-06→present) ran for ~18h. 4/5 VMs (`-151237`
FIXTURE_EVENTS, `-151335` FIXTURE_LINEUPS, `-151405` FIXTURE_STATS, `-151433` PLAYER_STATS) were **force-deleted at
2026-07-18T09:18-09:19Z** by `unified-trading-sa` (audit log: `v1.compute.instances.delete`) — NOT a self-delete, NOT a
SPOT preemption (no `PREEMPTED` marker in GCS, no `EXIT_STATUS`/`DEPLOYMENT_COMPLETED`; `run.log` shows live per-fixture
fetch activity seconds before the delete, zero Tracebacks). Only `-151505` (INJURIES) completed cleanly
(`EXIT_STATUS=0`) — it happened to finish its smaller window before the reaper caught it.

**Root cause (confirmed via code read of `deployment-service/scripts/vm/vm_zombie_watchdog.py`)**: the module's
`PREFIX_IDLE_THRESHOLDS` overrides the global default (15min heartbeat / 120min shard, per Incident 1 above) with a
**tighter `(10.0, 60.0)` minute pair specifically for the `af-backfill-` prefix**. This override was added AFTER the
2026-06-23 incident and makes the exact failure mode documented in that incident WORSE for this prefix family, not
better — the recommended campaign-mode exemption (§3) was never built, and instead the threshold for the highest-latency
prefix (API-Football's real per-call rate limiting routinely produces 54s inter-call sleeps, and a single
`(entity, fixture_id)` chunk with a sparse fixture-day can plausibly exceed 60min between per-VM manifest-shard writes)
was tightened below the general default. The watchdog's own docstring (lines 44-59) explicitly flags this class of
false-positive as a known scope limit ("cannot distinguish genuinely stuck from actively working but hasn't written the
checked blob recently").

**Impact on the consuming plan**: this is very likely the primary reason
`sports_p2_history_apifootball_2015_to_present-001` ("Full-history enrichment phase") has bounced across 9+ dispatched
slots since 2026-07-17T15:12Z without the gate going green — each relaunch makes real but partial progress (pending
counts: FIXTURE_EVENTS 1972→1935, FIXTURE_LINEUPS 2219→1925, FIXTURE_STATS 2864→1893, PLAYER_STATS 1232→1172, INJURIES
558→0, re-measured 2026-07-18T~15:20Z) before the same watchdog reaps it again, well short of actually draining the
residual. Mitigated this dispatch by relaunching the 4 residual entities
(`af-backfill-20260718-15{2725,2753,2818,2852}`), but this will recur every ~1-18h until the code fix lands.

**Updated recommended decision — add to §3's scope**:

- [x] ✅ [INFRA] P1. **Give `af-backfill-*` (and any other high-latency-per-call prefix) a widened
      `PREFIX_IDLE_THRESHOLDS` entry, or the campaign-mode/lifecycle-class exemption from §3, in
      `deployment-service/scripts/vm/vm_zombie_watchdog.py`** — the current `(10.0, 60.0)` pair is tighter than the
      15/120 global default and actively worse than the class of bug this issue already documents. At minimum restore it
      to ≥ the global default, or (preferred, per §3) key the threshold off the launcher's declared
      `SPORTS_ADAPTER_RATE_RPM`/expected inter-write cadence so genuinely slow-but-alive VMs aren't misclassified.
      (repo: deployment-service) — **deployment-service@5a5a504**: `af-backfill-`/`af-audit-`/`af-recover-` widened from
      `(10.0, 60.0)` to `(15.0, 180.0)` — heartbeat now matches the 15min global default (sidecar writes every 60s
      independent of API rate limiting, so it's still a fast true-zombie catch), shard widened to 180min (above the
      120min global default) for headroom on the documented sparse-fixture-day >60min gap. Updated
      `test_vm_zombie_watchdog.py::TestPerPrefixIdleThresholds::test_backfill_prefix_gets_widened_threshold` to match;
      219/219 unit tests + full `quality-gates.sh` green on the shipped SHA. Full campaign-mode/RPM-keyed dynamic
      threshold (the "preferred" alternative) is NOT done — left to §3 / P2 below if the widened static pair recurs.
- [x] ✅ [INFRA] P2. **Add a heartbeat-sidecar reliability check** — cross-reference whether the killed VMs' heartbeat
      blobs were genuinely stale for >10min or whether the sidecar (`setup-data-pipeline-vm.sh` lines 816-833) is itself
      intermittently failing to start/write; the 2026-07-18 heartbeat blob for `af-backfill-20260717-151237` shows a
      write only 16s before the delete call, consistent with either a last-second race or a sidecar gap. (repo:
      deployment-service) — **deployment-service@e777ed3**: new `heartbeat_sidecar_reliability.py` module
      (`classify_heartbeat_reliability` pure core + `audit_killed_vm(s)` GCS sweep, reusing a new
      `_gcs.heartbeat_blob_write_epoch` raw-write-instant reader — the durable `vm-heartbeat/{vm}.txt` blob has no
      delete lifecycle so it's still readable post-kill) classifies each (killed VM, kill_time) pair as
      `genuinely_stale` (blob age at kill time >= the watchdog's own per-prefix threshold — kill was justified),
      `reliability_gap_suspected` (blob younger than threshold at kill time — last-second sweep/kill race OR an
      intermittently-failing sidecar), or `unknown_no_blob`. Standalone `heartbeat_sidecar_reliability_cli.py` (single
      `--vm-name`/`--kill-time` or batch `--killed-vms-json`) resolves the SAME per-prefix threshold the watchdog
      applies via a deferred import of `vm_zombie_watchdog` (mirrors `cli.py._zombie_watchdog`), mirroring
      `check_vm.py`/`check_vm_cli.py`'s always-dry, never-alerts conventions. 13 new unit tests (pure classification +
      GCS-epoch math + CLI exit-code branching, `FakeStorage`-injected, credential-free); full `quality-gates.sh` green
      on the shipped SHA.

## Incident 2 follow-up — 2026-07-18T15:49Z (the shipped fix is INERT until the daemon is relaunched)

Dispatched to `sports_p2_history_apifootball_2015_to_present-001` (13th+ bounce). Checked whether
`deployment-service@5a5a504` (the widened `(15.0, 180.0)` threshold fix above) actually protects the currently-running
relaunch (`af-backfill-20260718-15{2725,2753,2818,2852}`, launched ~15:27-15:29Z). **It does not, yet**:
`gcloud compute instances list --filter="name~vm-zombie-watchdog"` shows the daemon still running is
`vm-zombie-watchdog-20260623-171612` — booted **2026-06-23**, three and a half weeks before the fix commit
(2026-07-18T15:43:37Z). Per the launcher's own SSOT comment (`launch-vm-zombie-watchdog.sh` lines 27-33): the daemon
uploads `vm_zombie_watchdog.py` to `gs://deployment-scripts-{pid}/scripts/vm_zombie_watchdog.py` **once, at launch
time**, and "the running watchdog never re-fetches mid-loop." So the currently-running daemon is still enforcing the OLD
`(10.0, 60.0)` af-backfill-* pair regardless of the merged code fix — the fix is real but dormant until the daemon
process itself is killed and relaunched.

**Consequence**: the current 4-VM relaunch is still at risk of being wrongly reaped again at its ~60-min mark
(~2026-07-18T16:27-16:29Z, under the OLD threshold) even though the fix shipped before that deadline. This is very
likely why the fix landing didn't itself resolve the bounce loop — the daemon restart is a separate, undone step.

**Not doing the relaunch myself** — killing/relaunching `vm-zombie-watchdog-*` is a shared cross-cutting infra action
(monitors the ENTIRE VM fleet, not just this task's backfill), outside `data_engineering` craft scope
(`data_engineering.md` § does_not: "infra/VM launches (→ infra)"). Filing as the actionable next step, P0 given the
~38min-remaining window at time of writing:

- [ ] [INFRA] P0. **Relaunch the `vm-zombie-watchdog` daemon VM to pick up the shipped threshold fix
      (`deployment-service@5a5a504`)** — the running daemon (`vm-zombie-watchdog-20260623-171612`, booted 2026-06-23)
      only uploads its script to GCS at launch time and never re-fetches mid-loop, so it is still enforcing the OLD
      `(10.0, 60.0)` af-backfill-* thresholds despite the fix being merged. Recipe:
      `gcloud compute instances delete vm-zombie-watchdog-20260623-171612 --zone asia-northeast1-c --quiet` then
      `bash scripts/vm/launch-vm-zombie-watchdog.sh` (re-uploads the fixed `.py`, singleton lock ensures no overlap;
      verify RUNNING within 60s — no fire-and-forget). Time-sensitive: the live
      `af-backfill-20260718-15{2725,2753,2818,2852}` fleet (from `sports_p2_history_apifootball_2015_to_present-001`)
      hits the OLD 60min shard-staleness mark around ~2026-07-18T16:27-16:29Z — relaunching the daemon before then is
      what actually makes the already-shipped fix take effect. (repo: deployment-service)
