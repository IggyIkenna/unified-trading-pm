---
doc_type: issue
title:
  Corpus-wide re-verify of the cefi content-canonicalisation fleet shows ZERO net progress in ~5h — 17/44 shards still
  incomplete, fleet fully empty, relaunch round 3 needed
summary: >-
  Split out of `cefi_content_migration_fleet_half_incomplete_2026_07_26.md` (at its 996/1000-line hard cap) to avoid
  breaching it, mirroring how the shard-13 and memory-freeze docs were split out earlier the same day. Re-ran that doc's
  own corpus-wide `run.log` grep (dispatched task `cefi_content_migration_fleet_half_incomplete-002`) at
  2026-07-31T13:04Z: fleet confirmed fully empty (`gcloud compute instances list`, zero
  `canonical-migration-cefi-content-*` VMs running), fetched all 392 `run.log`-directory objects (16-way parallel),
  grepped each for the terminal `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner. Result is IDENTICAL to the prior check at
  2026-07-31T08:05Z (slot-15): still 27/44 confirmed, same 17 shards incomplete (13, 15, 16, 17, 18, 19, 20, 21, 22, 23,
  24, 25, 40, 41, 42, 43, 44) — zero net forward progress across ~5 hours despite every one of those 17 shards having at
  least one more relaunch attempt in that window (all died again).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [cefi, migration, canonicalisation, vm-fleet, incomplete, data-correctness]
related:
  [
    cefi_content_migration_fleet_half_incomplete_2026_07_26,
    cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31,
    cefi_content_migration_shard13_network_error_and_checkpoint_resume_bug_2026_07_31,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
  ]
created: 2026-07-31
priority: P2
parent_epic: cefi_master
source:
  "worker, slot 12, 2026-07-31, cefi_content_migration_fleet_half_incomplete-002 -- re-running the parent doc's
  corpus-wide run.log grep per that todo's own text"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# CeFi content-canonicalisation fleet: still 17/44 incomplete, zero progress since 08:05Z, relaunch round 3 needed

## What I found

Fixed `gcloud` active-identity poisoning (drifted to `github-actions-deploy`, same recurring issue as
`orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`) back to `unified-trading-sa` before any GCS/compute
read. Confirmed via `gcloud compute instances list` the fleet is genuinely empty — zero
`canonical-migration-cefi-content-*` VMs running anywhere.

Fetched all 392 `run.log`-directory objects under
`gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-content-*/` (16-way parallel
`gcloud storage cat`, same method as every prior audit in the parent doc) and grepped each for the terminal
`SCRIPT 1 CONTENT MIGRATION SUMMARY` banner.

**Result: IDENTICAL to the 2026-07-31T08:05Z check — 27/44 confirmed complete, 17 shards still incomplete: 13, 15, 16,
17, 18, 19, 20, 21, 22, 23, 24, 25, 40, 41, 42, 43, 44.** Zero net forward progress in ~5 hours, despite every one of
these 17 shards having at least one more relaunch attempt land and die in that window — checked each shard's most-recent
attempt directly (not just the grep miss):

- 13 (`-032349`): died ~04:57Z, network `ConnectionResetError`/`SSLEOFError` on GCS upload (matches the shard-13 doc).
- 15 (`-032349`): no `run.log` object at all — VM died before any log write.
- 16 (`-035409`): died ~04:07:50Z mid-progress (4,200/157,328 files).
- 17 (`-063040`): died ~06:52:35Z mid-progress (7,400/157,497 files) — a THIRD dead attempt today, post stall-timeout
  fix (`55d051bd`).
- 21 (`-052154`): died ~05:45:46Z (7,400/131,776 files).
- 41 (`-055259`): died ~06:35:01Z (20,200/69,630 files).
- 17 (`-050400`), 24 (`-065001`), 41 (`-054648`): zero `run.log` ever written — VM died before the python process
  started/logged (instance-create or startup-script failure, not a migration-script failure).
- 18, 19, 20, 22, 23, 24, 25, 40, 42, 43, 44: latest attempt for each also dead, no progress reaching the terminal
  summary.

Not attempting a further root-cause diagnosis — the memory-freeze/registry-reap investigation is already tracked in the
sibling doc `cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md`; this doc's scope
is the re-verify + status update only, per the dispatched todo's own text.

**Separate observation, not a new finding**: the corpus-wide `run.log` fetch also picked up 55 objects under a DIFFERENT
naming scheme, `canonical-migration-cefi-content-apply-055803-cs<N>-...`, dated 2026-07-27 and covering pre-2024 date
ranges (e.g. `cs1` = 2019-03-30..2019-12-21) — outside the 44-shard fleet's date coverage entirely. Confirmed this is an
already-tracked, separate, archived effort
(`plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` references the same `055803` batch)
— excluded from the 44/44 count, same treatment as the original unsharded pilot the parent doc already excludes.

**Also flagging as likely-stale (not fixed here — parent doc is at its line cap, no room to safely edit)**: the parent
doc's open `[OPERATOR] P0` item ("Break the `-006`/`-002` dispatch deadlock") describes `-002` holding a slot for 4h20m+
while `-006` starved — but `-006` has since completed and shipped (`market-tick-data-service@9f4098b1`, per the parent
doc's own "2026-07-30 root cause + fix shipped" section), and this session's `-002` dispatch completed in under an hour
without holding anyone up. Worth a human/main-agent look at whether that item should be retagged resolved.

## Why it matters

Same as the parent doc: ~39% of the corpus (17/44 shards) remains un-migrated, and the parent doc's own `# Delete-when:`
gate on `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` cannot be satisfied. Critically, **no relaunch is
currently in flight for any of the 17 remaining shards** (fleet fully empty) — this is not a wait-it-out situation, it
needs an explicit next relaunch round, and none is currently dispatched.

## Recommended decision

- [ ] [SCRIPT] P2. **Relaunch round 3** for the 17 still-incomplete shards (13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
      25, 40, 41, 42, 43, 44). Recover each shard's exact `--start-date`/`--end-date` (or its `PROGRESS.json` checkpoint
      frontier where `monotonic=true`, per the checkpoint-aware-resume HARD RULE) from its own most-recent
      `run.log`/`PROGRESS.json` — do NOT re-derive/guess. Launch on the current tarball
      (`market-tick-data-service@55d051bd` or later, to include both the pyarrow-pool-release fix and the stall-timeout
      fix) via `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`, `MACHINE_TYPE=e2-standard-16`,
      SPOT default per HARD RULE. No `[OPERATOR]` gate needed (same reasoning as the parent doc's original P1/P2
      relaunch todos — ordinary backfill relaunch, AO-dispatchable by default). Respect `RB-INFRA-RELAUNCH`'s
      `≤2 relaunches/(vm-prefix,day)` budget per shard — query `DeploymentsRegistry.list_recent_archive`, not just
      recent `gcloud compute operations list` (the parent doc's own documented undercounting trap). **Done when**: all
      17 shards' `run.log` show the terminal summary (feeds back into the parent doc's `-002` corpus-wide re-verify
      todo).

## Progress Log

- 2026-07-31T13:04Z (worker, slot 12, `cefi_content_migration_fleet_half_incomplete-002`): filed after re-running the
  parent doc's corpus-wide re-verify grep and confirming zero forward progress since the 08:05Z check. Did not relaunch
  shards myself — out of this dispatched todo's scope (re-verify only) and consistent with the parent doc's own
  established policy (slot-15's self-correction entry) of deferring manual relaunch actions to a dedicated todo/the
  `data_pipeline_failure` fleet-monitor rather than doing it ad hoc while just re-verifying.
