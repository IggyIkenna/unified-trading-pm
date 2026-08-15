---
doc_type: plan
title: Finalize — CeFi 586-row decompose + 4.5M-file instrument_id backfill
summary: Gated finalize companion for cefi_residual_ao_dispatch_2026_08_15.md.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [cefi, finalize]
related: [/plans/active/cefi_residual_ao_dispatch_2026_08_15.md]
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
context_scope: [/plans/active/cefi_residual_ao_dispatch_2026_08_15.md]
locked_since:
resolved_by:
---

# Finalize — CeFi 586-row decompose + 4.5M-file instrument_id backfill

- [ ] [REVIEW] P2. Confirm both todos in `cefi_residual_ao_dispatch_2026_08_15.md` landed with evidence (decision-4
      scope determination cited, backfill VM run + manifest evidence for the 4.5M-file `--apply`); archive that plan
      once done and unlocked. **GATED, not done — see Progress Log**: todo 2's underlying shard-24 VM is still genuinely
      in-flight (not yet 100% complete); do not archive the source plan or flip this checkbox until it is.

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
