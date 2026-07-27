---
doc_type: issue
title:
  The 44-way sharded cefi content-canonicalisation --apply fleet did NOT complete corpus-wide — 21 of 44 shards died
  partway through (1.2%-99.9% done), only 23/44 confirmed complete
summary: >-
  Verified corpus-wide completion of the ~44-way date-range-sharded `canonical-migration-cefi-content-NN-20260719-*`
  `--apply` fleet (launched 2026-07-19 to run `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` against the
  full cefi content corpus, superseding an earlier unsharded dry-run pilot). Fetched every `run.log` (100 files across
  44 shards + their retry/resumption attempts) from `gs://deployment-scripts-central-element-323112/vm-logs/`. Only
  23/44 shards (01-12, 27, 30-39) show the terminal `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner in any attempt. The
  other 21 shards (13-26, 28, 29, 40-44) have NO attempt that reached the terminal summary — every attempt's log simply
  stops mid-`Progress:` line (VM killed, several with explicit `exit_code=137`/SIGKILL), at completion percentages
  ranging from 1.2% (shard 14) to 99.9% (shard 29, 1 file short) with most clustered 2-70%. This is a genuinely
  incomplete, silently-stalled migration, not a false negative from log-tail truncation (verified against full logs, not
  just tails, for the ambiguous cases).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, migration, canonicalisation, vm-fleet, incomplete, data-correctness, phantom-vm]
related:
  [
    /plans/active/issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md,
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch2_2026_07_26.md,
  ]
created: 2026-07-26
priority: P1
parent_epic: cefi_master
source:
  "worker, slot 6, 2026-07-26, defi_satellite_ao_dispatch_batch2-007 -- verifying whether the sharded --apply fleet
  completed before deciding whether to delete the migration script"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# CeFi content-canonicalisation fleet: 21/44 shards never finished

## What I found

`cefi_satellite_ao_dispatch_batch2_2026_07_26.md`'s todo asked me to confirm the sharded `--apply` fleet
(`canonical-migration-cefi-content-NN-20260719-*`, ~44 shards, launched 2026-07-19 to replace the killed unsharded
pilot) completed corpus-wide, then delete `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` per its own
`# Delete-when:` marker if so.

Listed every object under `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-content-*/` —
100 distinct `run.log` files across the 44 numbered shards (many shards have 2-9 retry/resumption attempts, suffixed
`-c<HHMMSS>`, `-od<HHMMSS>`, `-r<HHMMSS>`, `-nrw<HHMMSS>`, or `-repin<HHMMSS>`). Fetched and grepped every one for the
script's terminal `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner.

**23/44 shards confirmed COMPLETE** (summary found in at least one attempt): 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11,
12, 27, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39.

**21/44 shards NEVER reached the terminal summary in ANY attempt**: 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
26, 28, 29, 40, 41, 42, 43, 44. Best-known progress per shard (max across all its attempts, from the full log not just a
tail, so this is not a truncation artifact):

| Shard | Best progress     | %     | Note                                                                |
| ----- | ----------------- | ----- | ------------------------------------------------------------------- |
| 13    | 85,400 / 135,588  | 63.0% | 3 attempts; latest ends mid-`Progress:`, no exit status             |
| 14    | 3,200 / 271,376   | 1.2%  | Largest shard by file count; barely started                         |
| 15    | 5,600 / 138,077   | 4.1%  |                                                                     |
| 16    | 2,800 / 136,921   | 2.0%  |                                                                     |
| 17    | 7,600 / 141,670   | 5.4%  |                                                                     |
| 18    | 4,600 / 135,324   | 3.4%  |                                                                     |
| 19    | 4,800 / 136,539   | 3.5%  |                                                                     |
| 20    | 7,000 / 138,207   | 5.1%  |                                                                     |
| 21    | 11,600 / 137,156  | 8.5%  | 5 attempts, none finished                                           |
| 22    | 16,400 / 133,629  | 12.3% | 3 attempts, ALL exit_code=137 (SIGKILL) after SIGTERM               |
| 23    | 10,400 / 142,453  | 7.3%  | Also logged 1 `read_error`                                          |
| 24    | 10,200 / 135,828  | 7.5%  |                                                                     |
| 25    | 11,000 / 141,256  | 7.8%  |                                                                     |
| 26    | 40,000 / 134,739  | 29.7% | 9 attempts, none finished                                           |
| 28    | 97,200 / 137,243  | 70.8% | Closest to done besides 29; log stops there                         |
| 29    | 138,800 / 138,919 | 99.9% | 1 file short, likely killed seconds from finishing (footnote below) |
| 40    | 8,400 / 69,630    | 12.1% |                                                                     |
| 41    | 3,800 / 67,254    | 5.7%  |                                                                     |
| 42    | 3,000 / 67,831    | 4.4%  |                                                                     |
| 43    | 4,800 / 65,664    | 7.3%  |                                                                     |
| 44    | 2,400 / 63,453    | 3.8%  |                                                                     |

Shard 29's log ends on a heartbeat with "1 files still outstanding" and no final summary — likely killed seconds before
completion. A later `canonical-migration-cefi-content-29-20260720-repin113734` retry exists but covers only ~11,598
files, not obviously the same 1-file residual — not confirmed as this shard's completion.

Every dead attempt's log ends abruptly mid-`Progress:` line or with an explicit `exit_code=137` (SIGKILL, e.g. shard
22's all 3 attempts) — consistent with the SAME monitoring/alerting gap already diagnosed in
`cefi_content_migration_vm_wedged_worker_2026_07_23.md` (`classify_no_capture_reason()` can't recognize this script's
progress vocabulary, so a genuinely-dying VM in this family produces a `SILENT`/misclassified signal rather than a
correctly-triaged page) — these 21 dead VMs likely never generated an actionable alert distinguishing "still running
slowly" from "actually dead," which is consistent with nobody having relaunched them in the ~1 week since.

## Why it matters

This is a real, large, silently-stalled content-canonicalisation migration — roughly half the cefi content corpus (by
shard count; the incomplete shards range from small to the single LARGEST shard, #14 at 271k files) never got
canonicalised by this fleet. The migration's own `# Delete-when:` marker on
`migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` explicitly requires corpus-wide completion before deletion
— deleting it now would remove the only known tool for finishing this work, with no indication anyone is tracking that
~half the corpus is still un-migrated.

## Recommended decision

- [ ] [SCRIPT] P1. **No `[OPERATOR]` gate needed** — VM launches are AO-dispatchable by default per
      `/codex/05-infrastructure/vm-launcher-runbook.md` (only
      `launch-disaster-drill-cron-vm.sh`/`launch-dr-drill-cutover-vm.sh` and `launch-strategy-live-vm.sh` require
      explicit human sign-off; ordinary backfill/migration relaunches do not). This is a bounded, checkable relaunch of
      21 NAMED dead/incomplete shards (13-26, 28, 29, 40-44) via an EXISTING idempotent script
      (`already_canonical_skipped` counter design), not a new design/scope decision — the original `[OPERATOR]` tag's
      own justification ("a new VM-launch decision... not a bounded verification outcome") misapplied the runbook's
      default posture. Resume from each shard's own checkpoint/progress state if the script supports it, otherwise
      re-run those date ranges from scratch. **Done when**: all 21 shards' `run.log` show the terminal summary (feeds
      directly into the P2 todo below).
- [ ] [SCRIPT] P2. Once relaunched shards complete, re-run this same corpus-wide `run.log` grep to confirm all 44/44
      show the terminal summary, THEN delete `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` per its own
      `# Delete-when:` marker. Repo: market-tick-data-service.
- [ ] [BACKEND] P2. Cross-reference with `cefi_content_migration_vm_wedged_worker_2026_07_23.md`'s Recommendation item 1
      (give `classify_no_capture_reason()` a "task never writes the manifest" exemption for this script family) — these
      21 dead VMs are a second, larger, concrete instance of exactly the alerting gap that doc already diagnosed from
      one VM; worth citing as corroborating evidence when that fix is prioritized.

## Progress Log

- 2026-07-26 (worker, slot 6, `defi_satellite_ao_dispatch_batch2-007`): Filed after confirming corpus-wide completion
  was NOT reached — script left in place (NOT deleted) per the batch2 todo's own instruction for this case. Full
  evidence above; log data fetched via `gcloud storage cat` against
  `gs://deployment-scripts-central-element-323112/vm-logs/`.
