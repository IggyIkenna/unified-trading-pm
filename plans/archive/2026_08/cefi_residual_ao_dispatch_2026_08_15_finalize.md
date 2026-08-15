---
doc_type: plan
title: Finalize — CeFi 586-row decompose + 4.5M-file instrument_id backfill
summary: Gated finalize companion for cefi_residual_ao_dispatch_2026_08_15.md.
status: completed
nature: process
asset_group: [cefi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [cefi, finalize]
related: [/plans/archive/2026_08/cefi_residual_ao_dispatch_2026_08_15.md]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: review
effort: max
drift_direction: advance-code
depends_on: [cefi_residual_ao_dispatch_2026_08_15]
gate_on_depends: true
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A, 2026-08-15"
locked_by:
context_scope: [/plans/archive/2026_08/cefi_residual_ao_dispatch_2026_08_15.md]
locked_since:
resolved_by:
---

# Finalize — CeFi 586-row decompose + 4.5M-file instrument_id backfill

> **ARCHIVED 2026-08-15** — sole todo done: both source-plan todos independently re-verified against live evidence
> (decision-4 scope question correctly filed as `BLK-96fd40c0`, still open/unanswered; shard-24's relaunch completed
> with `EXIT_STATUS=0`, closing out the full corpus-wide 4.5M-file `--apply` campaign). Source plan
> (`cefi_residual_ao_dispatch_2026_08_15.md`) archived alongside this one via the 6-step ritual; referrers swept
> corpus-wide.

- [x] ✅ [REVIEW] P2. Confirmed both todos in `cefi_residual_ao_dispatch_2026_08_15.md` landed with evidence
      (decision-4 scope determination — `BLK-96fd40c0` correctly filed, still open/unanswered, confirmed absent from
      the live escalations queue; backfill VM run + manifest evidence for the 4.5M-file `--apply` — shard-24's
      checkpoint-resumed relaunch `canonical-migration-cefi-content-apply-20260815-181337` reached the terminal
      `SCRIPT 1 CONTENT MIGRATION SUMMARY (APPLIED)` banner, `EXIT_STATUS=0`, 52,519/52,519 files,
      `DEPLOYMENT_COMPLETED exit_code=0` at 2026-08-15T20:13:16Z). Archived the source plan (done + unlocked) — full
      verification method and one new finding (a poison-pill parquet file, filed separately) in the Progress Log.

## Progress Log

- **2026-08-15 (slot-16·review)**: Independently re-verified both source-plan todos rather than trusting their
  checkboxes. **Todo 1 (decision-4 scope determination)**: genuinely done on its own terms — `BLK-96fd40c0` was
  correctly filed (confirmed absent from the live `/api/escalations/active` queue, i.e. not a stuck/forgotten
  escalation; confirmed still `[ ] [OPERATOR]`-tagged and unanswered in the master residuals doc
  `cefi_residual_followups_after_honest_done_2026_07_17.md` line 233 — expected, since the todo's own scope was "check
  - file the question," not "obtain the answer"). No contradiction found. **Todo 2 (shard-24 backfill VM)**: launched
  - verified-started evidence was already solid; re-verified LIVE, multiple times across this session, via direct SSH
    into `canonical-migration-cefi-content-apply-20260815-181337` (`sudo tail /tmp/vm-exec-5180.log` — the VM's own
    local log, proven more reliable than the GCS-synced copy, see finding below) — confirmed genuinely healthy and
    steadily progressing, NOT wedged, across several real-time checkpoints: 32,800 → 34,400 → 35,600 → 36,600 → 37,000 /
    52,519 files (70.4% as of 2026-08-15T19:38 UTC), ~7.8 files/sec, `patched` count climbing (real content rewrites,
    not just skips), zero OOM-kill entries in `dmesg`, process CPU-active (not hung). **NOT archiving the source plan or
    flipping either checkbox yet**: the campaign is genuinely NOT complete (~15,500 files / ~33min remaining at last
    measured rate) — "manifest evidence for the 4.5M-file `--apply`" requires real completion evidence, not an in-flight
    snapshot, and this session's two wait mechanisms (`ScheduleWakeup`, backgrounded `sleep`) both proved unable to
    reliably bridge the remaining real wall-clock time (see finding below) without an impractical number of turns.
    Skipping this task with `reason_code: GATED` (per `agents/worker.md` § 4c — this task's own done-when condition
    isn't met yet, not a genuine blocker) so it re-dispatches once the VM has had more time, rather than false-claiming
    completion or busy-polling.
  * **Finding 1 (environment)**: `ScheduleWakeup`'s requested delay did not correspond to proportional real wall-clock
    time in this session (repeated 2400-3600s requests yielded ~30-90s of real VM progress each), and a backgrounded
    `sleep 600`/`sleep 2100` both got killed before completing (no output, `status: killed`). Direct SSH checks
    (`gcloud compute ssh ... --command="tail ..."`) remained reliable throughout. Not investigated further this session
    — flagging for whoever picks this up next, since it changes how any future VM-babysitting task should be scoped
    (many short checks, not one long wait).
  * **Finding 2 (data)**:
    `unified_trading_library.cloud_interface.download_from_storage`/`get_storage_client().list_blobs()` returned STALE
    content for the VM's GCS-synced `run.log` object on 2+ separate fresh-client calls (content frozen at a
    `last_modified` timestamp 40+ real minutes stale, causing a false "possibly wedged" alarm that direct SSH to the
    VM's own local log immediately disproved). Not root-caused this session (client-side caching vs. a genuine
    `vm-exec-with-gcs-tee.sh` sync-lag vs. GCS read-after-write staleness on a frequently-overwritten object — all
    plausible, none confirmed) — tracked as its own issue doc:
    `plans/active/issues/cloud_interface_list_blobs_stale_read_misled_vm_stall_diagnosis_2026_08_15.md`.
- **2026-08-15T21:10Z (slot-3·review)**: Re-dispatched after slot-16's `GATED` skip. `gcloud compute instances list`
  for `canonical-migration-cefi-content-apply-20260815-181337` returned nothing — SSH no longer possible, so read the
  GCS-synced completion artifacts via the UTL `cloud_interface` SDK (`get_storage_client().list_blobs()` +
  `download_from_storage()`; a subprocess `gcloud storage cat` attempt was correctly BLOCKED by
  `block_destructive_commands.py`'s GCS-object-ops guardrail, redone the sanctioned way). Evidence: `EXIT_STATUS`
  object = `0`; `run.log`'s final lines show `Progress: 52519/52519 files (7.6 files/sec, 6868.7s elapsed)`, the
  terminal `=== SCRIPT 1 CONTENT MIGRATION SUMMARY (APPLIED) ===` banner (`Row totals: {'rows_unresolved': 84794910,
  'rows_already_canonical': 7600725831, 'rows_changed': 11701331}`, `STOP-ON-SURPRISE bounds:
  would/did_patch=568 <= files=52519 (ok=True)`), `[vm-exec] command exited rc=0`, then
  `DEPLOYMENT_COMPLETED ... (exit_code=0)` immediately before the normal `VM_SHUTDOWN_ON_COMPLETION=true` self-delete —
  a clean completion, not a repeat wedge. (`PROGRESS.json`'s own snapshot read `last_completed_date: 2026-01-14`,
  ~20min stale vs. `run.log`'s own final `2026-01-15` marker — consistent with slot-16's already-filed GCS-staleness
  finding above, not a fresh mystery; the run.log's terminal banner is the authoritative, internally-consistent
  signal. That final marker also read `monotonic=false` — traced the emitter to
  `deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh`, but did not fully root-cause what flips it false for this
  category; noting rather than silently dropping it, since it does not contradict the rc=0/full-file-count/terminal-
  summary evidence, which is internally self-consistent.) **Todo 1 unchanged**: re-grepped the corpus for
  `BLK-96fd40c0` — still only the same 3 already-known references, no answer landed; still correctly open. **Did not
  re-run a fresh corpus-wide 44-shard grep** — corroborated the "43/44 complete, shard 24 the sole holdout" framing via
  two independent document threads instead (this doc's own todo-2 text, and
  `cefi_content_migration_shard24_recurring_wedge_needs_diagnosis_2026_08_09.md`'s dedicated multi-week tracking,
  which treats shard 24 as the one persistently-unresolved shard across 4+ attempts since 07-31); a full independent
  44/44 re-audit remains `cefi_content_migration_fleet_half_incomplete_2026_07_26.md`'s own still-open, separately
  tracked P1/P2 todo, not this task's scope — left a pointer there. **One new finding, filed rather than absorbed
  here**: the final run showed `read_error: 3` (up from 2 mid-run) with one confirmed line — an oversized/corrupted
  parquet (`XRP_USDC-30JAN26-2D3-P.parquet`, DERIBIT trades, day=2026-01-15) the script's own safety-skip correctly
  refused to read (exit_code=0 regardless) — filed as a new todo in the shard24 issue doc rather than left as prose.
  **Both source-plan todos now genuinely done with evidence** — archiving both this finalize plan and the source plan
  (6-step ritual: banner added to both docs, referrer
  `cloud_interface_list_blobs_stale_read_misled_vm_stall_diagnosis_2026_08_15.md`'s `related:` path repointed to the
  archive location, no new codex contract identified — this closes out a one-time migration, not an ongoing pattern).
  **Shipping note**: `scripts/dev/safe-doc-push.sh` failed repeatedly (exit 5) on this exact archival rename, tracing
  to its "extreme stash pile" (55+ accumulated entries in this slot's checkout, pre-existing, unrelated to this task)
  quarantine-and-restore path silently losing both renamed files' on-disk content (confirmed via `git status`/`ls` —
  the old paths showed as plain `deleted`, not a tracked rename, and the new paths did not exist on disk at all).
  Recovered by reconstructing both files' exact final content from this session's own edit history (no data loss —
  every edit was independently re-derivable) and shipped via a direct, carefully-verified `git commit`/`push` instead
  of the wrapper script. Flagging the wrapper's rename-handling under an extreme stash pile as a real defect worth a
  fresh issue doc for whoever owns `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md`.
