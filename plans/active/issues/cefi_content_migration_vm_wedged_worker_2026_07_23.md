---
doc_type: issue
title:
  "DP_VM_GONE_NO_CAPTURE false-paged a dry-run cefi content-canonicalisation VM that structurally never writes the
  manifest -- classifier has no non-capturing-task-type exemption, and the alert re-fired ~10x/45min 3 days after the
  VM's actual death"
summary: >-
  `canonical-migration-cefi-content-20260719-121302` ran `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`
  (Script 1, a parquet-CONTENT `instrument_id` canonicalisation pass) in its DRY-RUN default (no `--apply` on the
  command line, confirmed by its own "Mode: DRY-RUN" log line) over the WHOLE unsharded 2019-03-30..2026-07-19 cefi
  corpus (4,126,927 files), sustained only ~4.6-6.3 files/sec on 12 workers because file discovery is fully serial and
  each file needs a full GCS download + parquet parse -- an unsharded single-VM pass at that rate would need roughly 10
  days to just read the corpus once. A human (`ikenna@odum-research.com`) `gcloud compute instances delete`'d it 81
  minutes in (13,000/4,126,927 files done, 0.31%), reasonably reading the 78 repeated "possible wedged worker" WARNING
  lines as a hang, though that warning is a routine byproduct of a 30s poll timeout against bursty per-file I/O latency,
  not the script's own (never-triggered) genuine-hang detector. Root cause of the alert itself: this script never calls
  anything that increments the availability-manifest `captured` counter, in EITHER dry-run or `--apply` mode (verified
  by reading the full 560-line script) -- so `captured=0->0` is invariant to this task's success/failure, and
  `classify_no_capture_reason()`'s regex vocabulary (`_PROGRESS_RE`/`_HONEST_ABSENCE_RE`/ `_RATE_LIMIT_RE`) has zero
  overlap with this script's actual log vocabulary ("would_patch"/ "already_canonical_skipped"/"Progress: N/M files"),
  so it mechanically falls through to SILENT -> CRITICAL DP_VM_GONE_NO_CAPTURE for any VM running this script, healthy
  or not. Secondary finding: the VM's own `deployments/active/<id>.json` registration was never archived/reconciled
  (still `status: running`, `completed_at: null` 4 days later) and `DP_VM_GONE_NO_CAPTURE` is deliberately excluded from
  `_RECURRING_ALERT_COOLDOWNS` (assumed one-shot) -- consistent with, but not fully pinned down as, why the SAME VM's
  identical alert re-fired ~10 times over 45 minutes, 3 days after its actual GCE deletion.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, alerting-service, market-tick-data-service]
scope: [engineer]
tags: [vm-hang, alerting, canonical-migration, cefi, dp-vm-gone-no-capture, dry-run, false-positive]
related:
  - plans/archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md
  - plans/active/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md
  - plans/active/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md
  - /codex/05-infrastructure/data-pipeline-alerts.md
created: 2026-07-23
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.7
estimate_calibrated_ai_days: 0.28
assigned_role: data-engineer
drift_direction: none
depends_on: []
locked_by:
locked_since:
source: >-
  data-pipeline-alerts Slack channel, DP_VM_GONE_NO_CAPTURE, fired repeatedly 2026-07-22 23:16 through 2026-07-23 00:02
resolved_by:
---

## What happened (VERIFIED, not inferred)

All of the below is from direct reads of the live run.log, GCE operations history, the live deployment registry, and the
actual `.py`/`.sh` source -- commands + exact output cited.

**1. The VM's run.log (full 2918 lines pulled via
`gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-content-20260719-121302/run.log`)**:

- Line 1:
  `[vm-exec] starting: bash -c ( ... heartbeat ... ) & ... /home/ikennaigboaka/venv/bin/python scripts/migrate_cefi_content_instrument_id_catalogue_2026_07_17.py --workers 12`
  -- **no `--apply` flag anywhere on the command line.**
- `2026-07-19 11:15:32,645 INFO Mode: DRY-RUN | Workers: 12` -- the script's own log confirms dry-run.
- `2026-07-19 11:15:32,565 INFO Discovery scope: 42 (venue, pipeline_mode) cefi pairs from manifest` and
  `Days: 2669 (2019-03-30 .. 2026-07-19)` -- the WHOLE corpus, unsharded, no `--venue`/`--sample-days` filter (the
  script's own `--start-date`/`--end-date` defaults span the full corpus history to "today").
- `2026-07-19 11:48:43,792 INFO Discovery complete: 4126927 in-scope files across 2669 days x 42 (venue,pm) pairs (1991.1s)`
  -- discovery alone took 33.2 minutes (all serial, see below).
- First `Progress:` line: `11:50:07,846 INFO Progress: 200/4126927 files (2.4 files/sec, 84.1s elapsed) ...`.
- Last line in the file:
  `2026-07-19 12:36:15,778 WARNING No progress in the last poll window — 4113800 files still outstanding (possible wedged worker)`,
  preceded by
  `12:35:25,637 INFO Progress: 13000/4126927 files (4.6 files/sec, 2801.8s elapsed) stats={... 'would_patch': 5664}`.
  **13,000/4,126,927 files = 0.31% done** when the log stops.
- `grep -c "No progress"` = **78** occurrences across the run. `grep -ni "error\|traceback\|exception\|CRITICAL"` =
  **zero hits**. `grep -ni "DONE\|complete\|finished\|shutdown"` = only the `Discovery complete` line above -- the
  script's own terminal summary block (`_report()`, `"=== SCRIPT 1 CONTENT MIGRATION SUMMARY ==="`) **never appears** --
  the process did not reach a normal exit.

**2. No `EXIT_STATUS` file**: `gsutil cat .../canonical-migration-cefi-content-20260719-121302/EXIT_STATUS` →
`CommandException: No URLs matched`. `gsutil ls` of the VM's log directory shows only `run.log` — no other artifact.

**3. The VM was manually deleted, not preempted**:
`gcloud compute instances describe canonical-migration-cefi-content-20260719-121302 --zone=asia-northeast1-c` →
`ERROR: ... was not found` (confirms "drained").
`gcloud compute operations list --filter="targetLink~canonical-migration-cefi-content-20260719-121302"` shows exactly
two operations: `insert` (DONE, `2026-07-19T04:13:07.790-07:00` = 11:13:07 UTC) and `delete` (DONE,
`2026-07-19T05:37:10.498-07:00` = **12:37:10 UTC — one minute after the log's last line**), both
`user ikenna@odum-research.com`. **This is a direct `gcloud compute instances delete`, not a preemption** (no
`compute.instances.preempted` operation exists) and not the script's own graceful self-delete-on-completion (which would
have gone through the vm-exec EXIT trap and written an `EXIT_STATUS`).

**4. The VM's deployment registration was never archived — still live 4 days later**:
`gsutil cat gs://deployment-scripts-central-element-323112/deployments/active/f1afb75d-11ab-4758-8833-4ceabac7b1cc.json`
(the deployment id from the run.log's `registered deployment f1afb75d-... (CEFI, full)` line) still returns
`"status": "running", "completed_at": null, "exit_code": null, "workload_alive": true, "last_heartbeat_at": "2026-07-19T12:37:33Z"`
— a heartbeat timestamp landing seconds AFTER the recorded `delete` operation's own completion (`12:37:10Z`), i.e. one
final flush during VM teardown, after which nothing further ever touched this record.
`gsutil ls gs://deployment-scripts-central-element-323112/deployments/archive/ | grep f1afb75d` → no match. As of this
investigation (2026-07-23), the record is **still sitting in `active/`**, 4 days after the VM it describes stopped
existing.

**5. The script's own source
(`market-tick-data-service/scripts/migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`, read in full, 560
lines)**:

- `--apply` is `action="store_true"` (default `False`); the docstring states `DRY-RUN IS THE DEFAULT` and `--apply` is
  hard-gated behind a green "Phase -1 catalogue verify gate" (`sys.exit(3)` if red).
- In dry-run, `migrate_one_file()` (lines 293-335) does exactly one `storage.download_bytes()` (a full-object GET, not a
  metadata HEAD) + `pd.read_parquet` + the per-row resolve loop, then returns `"would_patch"` **before** any write path
  is reached (line 323-324: `if not apply: return "would_patch"`).
- **The ONLY manifest interaction anywhere in the file is a single READ** in `discover_scope_pairs()` (line 169-185) —
  one download of `_index/availability_index.parquet` to enumerate `(venue, pipeline_mode)` pairs. There is no
  `record_captured`, no manifest write, anywhere in this script — in dry-run OR `--apply`. Confirmed by a full read of
  the file, not a grep-and-conclude.
- `run()` (lines 343-437) is two phases: (a) discovery —
  `for day in days: for venue, pm in scope_pairs: all_files.extend(discover_day_scope(...))` (lines 355-357), **fully
  serial in the main thread, before the `ThreadPoolExecutor` is even created** — `--workers` has zero effect on this
  33-minute phase; (b) migration — `ThreadPoolExecutor(max_workers=workers)` (line 384) over all discovered files at
  once.
- The `"No progress in the last poll window ... (possible wedged worker)"` warning (lines 416-420) fires whenever
  `as_completed(pending, timeout=min(30.0, remaining_budget))` (line 394) times out — i.e. **zero of the pending futures
  completed in the last ≤30s window**. This is a soft, non-terminal, and inherently noisy signal given 12 threads each
  doing a several-MB download + full parquet parse + per-row Python resolve — it does **not** by itself mean a thread is
  stuck. The script's own actual "genuinely wedged" detector is a SEPARATE `hard_deadline`
  (`t1 + max(60.0, len(all_files) * 5.0)` seconds, line 387) which, on expiry, logs
  `"Hard deadline reached ... likely wedged GCS connections ... NOT waiting for them"` and force-exits non-zero
  (`os._exit(1)`, lines 552-556). **That branch never fired in this run** — the process was killed externally before
  ever reaching its own hang-detection deadline.
- `--workers 12` (the script's own default) is a **deliberate**, documented pool-safety choice (lines 485-497): a prior
  12-day dry-run at `--workers 32` against the then-default shared `urllib3` pool (`pool_maxsize=10`) produced ~27%
  "Connection pool is full" transient errors.

**6. Corroborating context (via a parallel Explore sub-agent's independent read of the plan-history doc
`plans/active/cefi_consolidated_closeout_2026_07_18.md` — not independently re-verified by me in this pass, flagged as
such)**: the actual production migration was carried out by a separate, later, ~44-48-way DATE-RANGE-SHARDED fleet
(`canonical-migration-cefi-content-01-20260719-134124` .. `-44-...`, this time run WITH `--apply`), launched roughly an
hour after this VM was deleted. **I independently confirmed the existence of that fleet myself**:
`gsutil ls gs://deployment-scripts-central-element-323112/vm-logs/ | grep cefi-content` lists dozens of
`canonical-migration-cefi-content-NN-20260719-*` VMs, and one of them's run.log
(`canonical-migration-cefi-content-01-20260719-134124/run.log`) shows `stats={..., 'patched': N}` (not `would_patch`) —
i.e. that later fleet ran in `--apply` mode. This VM (`...-20260719-121302`, no shard suffix, full unsharded corpus,
dry-run) reads as the unsharded pilot/reconnaissance pass that was abandoned in favor of the sharded `--apply` fleet,
not as one shard of that fleet.

## Root cause

**Primary — DP_VM_GONE_NO_CAPTURE is a category error for this task type, independent of what actually happened to the
VM.** `deployment-service/deployment_service/data_pipeline_monitors/_gcs.py::classify_no_capture_reason()` (lines
737-758) returns `SILENT` (→ `TerminationVerdict.GONE_NO_CAPTURE` → CRITICAL `page_operator`, registry id `DP-VM-002`)
unless the run.log matches one of three regexes: `_RATE_LIMIT_RE` (429/throttle text), `_PROGRESS_RE` (literal
`"Wrote N rows/records"`, `record_captured`, `CATALOGUE_PROMOTED`, or `captured=<nonzero>`), or `_HONEST_ABSENCE_RE`
(`empty_confirmed`, `expected_unattempted`, `honest_absence`, etc.). This script's actual log vocabulary
(`"Progress: %d/%d files (%.1f files/sec...) stats=%s"`, `"would_patch"`, `"already_canonical_skipped"`,
`"No progress in the last poll window"`) matches **none** of the three — verified by reading both the regex source and
the log content directly, not inferred. Combined with finding 5 above (the script structurally never calls anything that
moves the manifest `captured` counter, in either mode), `captured_before == captured_after` is **unconditionally true
for every VM running this script**, so `classify_no_capture_reason()` is mechanically forced to `SILENT` regardless of
whether the run succeeded, is still progressing normally, or genuinely crashed. The monitor's only non-manifest-writing
exemption (`exit_code_fleet_monitor.py`'s `is_live_vm` check, `umbrella=="live"`) does not apply either — this VM's
prefix `canonical-migration-cefi-` resolves via `deployment_service/vm_prefix_registry.py:813`
(`VmPrefixSpec(bucket=_TICK_CEFI, lifecycle_class=LifecycleClass.EPHEMERAL_BATCH)`) to `EPHEMERAL_BATCH`, not `live`.

**Secondary, operationally real but separate from the alert bug — the unsharded single-VM design cannot finish.** At the
observed sustained rate (4.6-6.3 files/sec on 12 workers, bottlenecked by one full download + one full parquet parse per
file, not a lightweight metadata check), reading the full 4,126,927-file corpus once would take roughly 4,126,927 / 5 ≈
825,000s ≈ **9.5-10 days** on a single VM. The 78 "possible wedged worker" WARNING lines are real but misleadingly
labeled — they are a routine artifact of a 30-second poll timeout against bursty multi-thread I/O latency, not proof of
an actual stuck thread (the script's own genuine-hang detector, the `hard_deadline` branch, never fired). A human
reasonably read the repeated warnings plus the plainly-infeasible ETA and killed the VM via a direct
`gcloud compute instances delete` — a correct call given the throughput, just not literally "a hang was detected and
handled" the way the warning text implies.

**Tertiary, unresolved with full confidence — the repeated re-firing.** Two verified code facts point in different
directions and I could not fully reconcile them in this read-only pass:

- `exit_code_fleet_monitor.py`'s census mechanism is designed as a present→gone **state-transition** detector (diffs the
  running-VM set each `*/5 * * * *` tick, per
  `deployment-service/terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf:200`), and `alerting-service`'s
  `AlertDeduplicator` hashes `vm_name` as part of the alert identity — so, by design, a single VM's `GONE_NO_CAPTURE`
  classification should fire once, not repeatedly.
- Against that: `DP_VM_GONE_NO_CAPTURE` is **explicitly excluded** from `_RECURRING_ALERT_COOLDOWNS`
  (`alerting-service/alerting_service/notifiers/router.py:76-87`) by a design comment stating it is assumed
  "one-shot/flappy" and should keep the bare `AlertDeduplicator(ttl_seconds=60.0)` default rather than a longer cooldown
  — and this VM's `deployments/active/` record (finding 4) was never reconciled/archived, 4+ days after the VM itself
  stopped existing. The **identical failure class** — a CRITICAL DP_\* event assumed one-shot but whose underlying
  condition is actually a static, never-clearing signal that gets re-derived every sweep — was already found and fixed
  for a _different_ event (`DP_RUN_MOSTLY_EMPTY`) on 2026-07-15
  (`plans/archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md`), which explicitly named
  `DP_VM_GONE_NO_CAPTURE` as one of the events the prior (2026-06-23) flood-triage pass covered but did not re-audit for
  this specific gap.
- I did not directly read `exit_code_fleet_monitor.py`'s `CENSUS_BLOB` persistence/write-ordering to determine whether
  it can re-classify the same already-alerted VM as a "fresh" transition on a later tick (e.g. if the census snapshot
  never captured this VM as "present" while it was alive, given how many ephemeral migration VMs were cycling that week,
  its absence on every subsequent census read could plausibly re-trigger "newly gone" each tick). This is the most
  likely proximate mechanism given the observed facts (3-day-delayed first alert, ~10 identical fires in 45 minutes, for
  what the task brief states is one VM with one unchanging trace) but is flagged as an **unconfirmed hypothesis**, not a
  verified root cause — a direct follow-up read of that file is the fastest way to settle it.

## Recommendation

1. **[deployment-service] Give `classify_no_capture_reason()` / `exit_code_fleet_monitor.py` a "task never writes the
   manifest" exemption**, analogous to the existing `is_live_vm` exemption. Cheapest correct signal: recognize this
   script's own summary vocabulary (`would_patch`/`patched`/`already_canonical_skipped` in a `stats=` dict, or the
   literal `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner) as a PROGRESS-equivalent, mirroring how `_PROGRESS_RE` already
   recognizes `record_captured`/`CATALOGUE_PROMOTED` for other non-`Wrote N rows` shapes. A more durable fix is a small
   allowlist/registry of `task=`/script-name patterns known to be content-audit-only (never manifest-writing) that
   short-circuits `GONE_NO_CAPTURE` entirely for that class, since new one-off `canonical-migration-*` scripts will keep
   recurring here (this is at least the second content-canonicalisation script in this family — see
   `tradfi-cid`/`rewrite_tradfi_content_id_2026_07_21` in `launch-canonical-migration-vm.sh`, which likely has the
   identical gap and wasn't checked in this pass).
2. **[deployment-service] Reconcile orphaned `deployments/active/*.json` records whose GCE instance no longer exists** —
   this VM's record is proof the vm-exec wrapper's own EXIT-trap archival path is skipped entirely by an external
   `gcloud instances delete` (vs. the script's own graceful self-delete), leaving a permanently stale "running" record.
   A periodic reaper (or a check inside the existing `*/5` census sweep) that archives an `active/` record once its
   instance is confirmed gone would close both the registry-hygiene gap and remove whatever is causing the tertiary
   re-fire behavior above.
3. **[alerting-service] Re-audit whether `DP_VM_GONE_NO_CAPTURE` truly qualifies for the "one-shot" 60s-TTL bucket**,
   given this concrete counter-example. If a VM's `GONE_NO_CAPTURE` classification can be re-derived on a later tick
   (pending the finding-3 investigation above), it needs the same treatment `DP_RUN_MOSTLY_EMPTY` got on 2026-07-15 — a
   cadence-aware cooldown entry (`_RECURRING_ALERT_COOLDOWNS["DP_VM_GONE_NO_CAPTURE"] = <cooldown>`) is a fast, low-risk
   mitigation even before the root cause in finding 3 is fully nailed down.
4. **[market-tick-data-service, low priority, not verified]** If the sharded `--apply` fleet (finding 6) did in fact
   carry the cefi content-canonicalisation corpus to completion, this script's own docstring header already declares its
   lifecycle (`# Lifecycle: oneoff`,
   `# Delete-when: cefi content instrument_id catalogue-canonicalisation applied + verified corpus-wide`) — worth a
   follow-up to confirm completion and delete it per that marker. Not investigated further here (out of this issue's
   scope; flagging only since it's directly adjacent). — **FOLLOWED UP 2026-07-26 (worker, slot 6)**: it did NOT
   complete — only 23/44 shards reached the terminal summary; 21 shards died partway through (1.2%-99.9% done, several
   with `exit_code=137`/SIGKILL, exactly this doc's alerting gap in action at fleet scale). Script left in place, NOT
   deleted. Full evidence: `/plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md`.
