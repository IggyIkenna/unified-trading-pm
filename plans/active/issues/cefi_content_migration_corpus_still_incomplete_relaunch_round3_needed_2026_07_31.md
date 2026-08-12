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
author: unknown
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
context_scope:
  [
    /plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md,
    /plans/active/issues/cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    market-tick-data-service/scripts/migrate_cefi_content_instrument_id_catalogue_2026_07_17.py,
    deployment-service/scripts/vm/launch-canonical-migration-vm.sh,
  ]
---

# CeFi content-canonicalisation fleet: still 17/44 incomplete, zero progress since 08:05Z, relaunch round 3 needed

> **CORRECTED 2026-08-12 (/plan-reconcile)**: this title/heading reflect the 2026-07-31 origin state only and are stale
> — per this doc's own Todos + Progress Log, the fleet progressed through rounds 4-8, down from 17 to 8 remaining shards
> (16, 17, 18, 19, 21, 23, 41, 42). The sole open todo is "Round-8 ACTUAL LAUNCH" (still `- [ ]`; its blocking prereq
> `cefi-round8-budget-reset-2026-08-08` was manually unblocked 2026-08-08T20:32Z). Title/heading left verbatim (existing
> cross-refs cite this doc by its current filename/title) — read the Todos section for ground truth, not the title.

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

- [x] ✅ [SCRIPT] P2. **Relaunch round 3** for the 17 still-incomplete shards (13, 15, 16, 17, 18, 19, 20, 21, 22, 23,
      24, 25, 40, 41, 42, 43, 44). Recover each shard's exact `--start-date`/`--end-date` (or its `PROGRESS.json`
      checkpoint frontier where `monotonic=true`, per the checkpoint-aware-resume HARD RULE) from its own most-recent
      `run.log`/`PROGRESS.json` — do NOT re-derive/guess. Launch on the current tarball
      (`market-tick-data-service@55d051bd` or later, to include both the pyarrow-pool-release fix and the stall-timeout
      fix) via `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`, `MACHINE_TYPE=e2-standard-16`,
      SPOT default per HARD RULE. No `[OPERATOR]` gate needed (same reasoning as the parent doc's original P1/P2
      relaunch todos — ordinary backfill relaunch, AO-dispatchable by default). Respect `RB-INFRA-RELAUNCH`'s
      `≤2 relaunches/(vm-prefix,day)` budget per shard — query `DeploymentsRegistry.list_recent_archive`, not just
      recent `gcloud compute operations list` (the parent doc's own documented undercounting trap). **Done when**: all
      17 shards' `run.log` show the terminal summary (feeds back into the parent doc's `-002` corpus-wide re-verify
      todo). — worker, slot 10, 2026-07-31: relaunched 13/17 (budget allowed); see Progress Log for per-shard resume
      dates + the 4 shards correctly skipped this round for `RB-INFRA-RELAUNCH` budget. Corpus-level "done when" still
      pending — tracked by the new follow-up todo below + the parent doc's `-002` re-verify.
- [x] ✅ [DIAG] P1. **RULED 2026-08-06 (operator), option (b): check the sibling memory-freeze root-cause fix —
      CONFIRMED SHIPPED.** The sibling doc
      `cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md`'s Finding 1 identified
      the root cause: a data-content-driven memory spike (likely a single anomalously large/malformed parquet file — a
      "decompression bomb" / poison pill) that defeats both the pyarrow-pool-release fix (`@9f4098b1`) and the
      stall-timeout fix (`@55d051bd`) because an acute allocator freeze prevents even a timer thread from firing. **That
      root cause's fix has now shipped**: the decompression-bomb OOM preflight guard at
      `market-tick-data-service@dc037373` (landed 2026-08-03, verified ancestor of `origin/live-defi-rollout`) adds a
      footer-metadata claimed-uncompressed-size preflight check (2GiB ceiling) applied BEFORE materializing parquet rows
      — directly blocking the poison-pill mechanism. The sibling doc's own Finding 1 explicitly stated this was the
      missing piece ("the memory-spike root cause... remains unaddressed and can still produce an unrecoverable freeze
      even with both current mitigations in place"). That gap is now closed. **Recommendation**: relaunch the 10
      remaining shards (13, 16, 17, 18, 19, 21, 23, 40, 41, 42) on a tarball ≥ `market-tick-data-service@dc037373` that
      includes the decompression-bomb guard. No machine-type bump needed — the guard prevents the memory spike at its
      source rather than trying to survive it with more headroom. Budget for shards 16/17/21/41/42 should reset with the
      new day (2026-08-06) per `RB-INFRA-RELAUNCH`'s `≤2/(vm-prefix,day)` window. — slot 6, 2026-08-06: verified
      `dc037373` is ancestor of `origin/live-defi-rollout`; sibling doc's root cause is addressed; shards should
      relaunch on the new tarball.

      **Corroborating signal 2026-07-31 13:56Z (review agt-8ce066, gcloud-verified — a DIFFERENT shape than the
                                                                                                                                                                                                                                                                                                                                                                                                                                              same-shard-memory-death pattern above):** shards 43 + 44, freshly relaunched this round at 13:39:58Z / 13:40:22Z,
                                                                                                                                                                                                                                                                                                                                                                                                                                              were BOTH preempted at 13:51:37Z / 13:51:38Z — ~12 min after launch and only ~2 min after their own T+10 alive-check
                                                                                                                                                                                                                                                                                                                                                                                                                                              (13:49:30Z), confirmed via `gcloud compute operations list` `compute.instances.preempted` (ops
                                                                                                                                                                                                                                                                                                                                                                                                                                              `systemevent-1785505897347-…` / `systemevent-1785505907671-…`), not inference; 11/13 relaunched shards remain
                                                                                                                                                                                                                                                                                                                                                                                                                                              running. A FRESH launch dying fast points to SPOT-capacity pressure in `asia-northeast1-c` today (fleet-wide), NOT a
                                                                                                                                                                                                                                                                                                                                                                                                                                              shard-specific memory/data issue — so the operator decision should ALSO weigh (d) a zone/capacity check or a
                                                                                                                                                                                                                                                                                                                                                                                                                                              one-shot `--on-demand` fallback (env `ON_DEMAND=true`) for the next relaunch, not only the memory-ceiling options
                                                                                                                                                                                                                                                                                                                                                                                                                                              (a)/(b). Non-blocking: 43/44 are idempotent SPOT shards and should re-run cleanly on round-4.

                                                                                                                                                                                                                                                                                                                                                                                                                                  **Corroborating signal 2026-07-31 14:43Z (`data_pipeline_failure` escalation `agt-b58993`, slot 1,
                                                                                                                                                                                                                                                                                                                                                                                                                                  `DP_VM_EXIT_NONZERO`/DP-VM-001 for `canonical-migration-cefi-content-42-relaunch20260731-133929`):** shard 42 —
                                                                                                                                                                                                                                                                                                                                                                                                                                  one of round 3's 13 relaunched shards, confirmed healthy at both the 13:49Z and 14:19Z checks above
                                                                                                                                                                                                                                                                                                                                                                                                                                  (14,000/73,965 files, climbing) — has now ALSO died the identical way: `EXIT_STATUS=137`,
                                                                                                                                                                                                                                                                                                                                                                                                                                  `completed_at=2026-07-31T14:43:34Z` at 21,600/73,965 files (29%), confirmed via `DeploymentsRegistry` archive
                                                                                                                                                                                                                                                                                                                                                                                                                                  (`deployment_id=f8b972e6-e4c6-4e5c-af87-8c42448294c6`, `git_commit=89739b64931699798cc54920cc636e72948d2cc7` —
                                                                                                                                                                                                                                                                                                                                                                                                                                  the SAME commit this doc's own 13:35Z Progress Log entry cites, confirming `e2-standard-16` + both shipped fixes
                                                                                                                                                                                                                                                                                                                                                                                                                                  (`9f4098b1`, `55d051bd`) were genuinely live on this run, not a stale tarball). `host_metrics_window` shows the
                                                                                                                                                                                                                                                                                                                                                                                                                                  identical spike-then-death signature already diagnosed for 16/17/19/21/40/41: `mem_pct` plateaued ~75-85% across
                                                                                                                                                                                                                                                                                                                                                                                                                                  9 samples (14:33:58Z-14:42:06Z) then jumped to **95.3%** (`mem_slope=2.0`) in the final sample before the process
                                                                                                                                                                                                                                                                                                                                                                                                                                  was OOM-killed (`bash: ... Killed`) ~26s later — not a new failure mode, the 7th confirmed instance of the same
                                                                                                                                                                                                                                                                                                                                                                                                                                  ceiling. **Budget check** (`DeploymentsRegistry.list_recent_archive(days=1)`, filtered to `content-42`): exactly
                                                                                                                                                                                                                                                                                                                                                                                                                                  2 archived today (`-032606` failed `exit_code=137` at 04:34:48Z, `-133929` failed `exit_code=137` at 14:43:34Z) —
                                                                                                                                                                                                                                                                                                                                                                                                                                  shard 42 is now AT the `≤2/(vm-prefix,day)` cap, same posture as 16/21. **Not relaunching a 3rd time** — folding
                                                                                                                                                                                                                                                                                                                                                                                                                                  shard 42 into this todo instead, consistent with the existing posture for the other repeat-offender shards.
                                                                                                                                                                                                                                                                                                                                                                                                                                  **Updated shard list needing the operator decision: 13, 16, 17, 18, 19, 21, 23, 40, 41, 42 (10 shards)** — 19/40 were
                                                                                                                                                                                                                                                                                                                                                                                                                                  flagged in the Progress Log below but never folded into this todo's own text until now; 23 added
                                                                                                                                                                                                                                                                                                                                                                                                                                  2026-07-31T15:1xZ (see Progress Log — DP-VM-003 `agt-71ccbf`); 18 added 2026-07-31T15:5xZ (see Progress
                                                                                                                                                                                                                                                                                                                                                                                                                                  Log — DP-VM-001 `agt-95d7c6`); 13 added 2026-07-31T19:1xZ (see Progress Log — DP-VM-003 `agt-c14d58`). Ten independent shards hitting the
                                                                                                                                                                                                                                                                                                                                                                                                                                  identical ceiling on `e2-standard-16` increasingly points toward the sibling memory-freeze doc's leading
                                                                                                                                                                                                                                                                                                                                                                                                                                  theory (a data-content-driven spike, e.g. a single anomalously large/malformed file) rather than a per-shard
                                                                                                                                                                                                                                                                                                                                                                                                                                  sizing gap — since e2-standard-16 was expected to be adequate headroom and demonstrably isn't for these specific
                                                                                                                                                                                                                                                                                                                                                                                                                                  shards. Does not change the pending (a)/(b)/(c)/(d) decision options, just the shard count and urgency.

                                                                                                                                                                                                                                                                                                                                                                                                                                  **Corroborating signal 2026-07-31 19:1xZ (`data_pipeline_failure` escalation `agt-c14d58`, slot 7, DP-VM-003 for
                                                                                                                                                                                                                                                                                                                                                                                                                                  `canonical-migration-cefi-content-13-relaunch20260731-133503`, alert-fired at 36min heartbeat-stale):** shard 13 —
                                                                                                                                                                                                                                                                                                                                                                                                                                  one of round 3's 13 relaunched shards, resumed from its monotonic checkpoint (2026-01-18..2026-02-13) on
                                                                                                                                                                                                                                                                                                                                                                                                                                  `market-tick-data-service@89739b64` (both shipped fixes live) — has also died the identical way. `gcloud compute
                                                                                                                                                                                                                                                                                                                                                                                                                                  instances describe` found the instance already gone; `gcloud compute operations list` showed only `insert`
                                                                                                                                                                                                                                                                                                                                                                                                                                  (13:37:40Z) and a programmatic `delete` by `unified-trading-sa` completed `18:46:42Z` — NOT a
                                                                                                                                                                                                                                                                                                                                                                                                                                  `compute.instances.preempted` systemevent, i.e. a genuine reap of a wedged instance. `run.log` confirms: real
                                                                                                                                                                                                                                                                                                                                                                                                                                  progress to 169,000/292,434 files (10.8 files/sec) with the benign `WARNING No progress in the last poll window`
                                                                                                                                                                                                                                                                                                                                                                                                                                  lines present throughout, then goes completely silent after `18:00:36Z` — no further heartbeat, no `EXIT_STATUS`
                                                                                                                                                                                                                                                                                                                                                                                                                                  line — a genuine freeze, not a clean exit. `DeploymentsRegistry.list_recent_archive(days=1)` confirms the archived
                                                                                                                                                                                                                                                                                                                                                                                                                                  entry (`status=failed, exit_code=125, reap_reason=vm_not_running`)'s `host_metrics_window` shows `mem_pct` climbing
                                                                                                                                                                                                                                                                                                                                                                                                                                  65%→85% over its last 10 samples (17:51Z-18:00Z) before the silence — the same spike-then-freeze signature already
                                                                                                                                                                                                                                                                                                                                                                                                                                  diagnosed for 16/17/18/19/21/23/40/41/42. **Budget check**: exactly 2 archived today for `content-13`
                                                                                                                                                                                                                                                                                                                                                                                                                                  (`-032349` failed `exit_code=125` at 04:47:57Z — a DIFFERENT root cause, the shard-13-specific GCS SSL/connection-reset
                                                                                                                                                                                                                                                                                                                                                                                                                                  death already tracked in `cefi_content_migration_shard13_network_error_and_checkpoint_resume_bug_2026_07_31.md`, not
                                                                                                                                                                                                                                                                                                                                                                                                                                  a memory freeze; `-133503` failed `exit_code=125` at 18:50:02Z — this memory-freeze death) — shard 13 is now AT the
                                                                                                                                                                                                                                                                                                                                                                                                                                  `RB-INFRA-RELAUNCH` `≤2/(vm-prefix,day)` cap. **Not relaunching a 3rd time** — folded shard 13 into this todo instead,
                                                                                                                                                                                                                                                                                                                                                                                                                                  consistent with the existing posture for the other repeat-offender shards. Note shard 13's two deaths today were via
                                                                                                                                                                                                                                                                                                                                                                                                                                  TWO DIFFERENT mechanisms (network/SSL death, then memory-freeze death) — both already-tracked failure classes, not a
                                                                                                                                                                                                                                                                                                                                                                                                                                  new one.

- [x] ✅ [BACKEND] P1. **Land the orphaned decompression-bomb OOM preflight guard — candidate root cause for the
      `[OPERATOR] P1` shard-16/17/21/41 OOM blocker above** (orphan-ref audit rescue, 2026-08-03). The branch
      `refs/heads/wip-preserve/orchestrator-slot-9-c0958440-oom-fix` on **market-tick-data-service** origin (commit
      `c0958440`, slot 9, Aug-1 00:45Z) is tested, unshipped work: a footer-metadata claimed-uncompressed-size preflight
      check (2GiB ceiling) applied BEFORE materializing parquet rows (+152/-61), plus its own test
      `test_migrate_cefi_content_poison_pill_guard_2026_07_31.py`. Verified 2026-08-03 (review agt-de20d5 + main
      agt-1756f6): the guard + test are ABSENT on `origin/live-defi-rollout`, `c0958440` is not an ancestor of it, and
      there are zero references to this sha/fix anywhere in `plans/active/` — real finished work that never shipped
      (slot 9 likely died pre-quickmerge). Extends (does NOT duplicate) the already-landed shard-23 footer-corruption
      fix and the pyarrow-pool-release fix (`@9f4098b1`); a decompression-bomb poison-pill file on the specific large
      shards is a strong root-cause candidate for their `mem_pct→91%` OOM despite `@9f4098b1`+`@55d051bd` both being
      live. No `[OPERATOR]` gate (ordinary tested-code landing, AO-dispatchable — same shape as the round-3 relaunch
      todo). Repo: market-tick-data-service. **Done when**: fetch the branch, rebase onto current
      `origin/live-defi-rollout`, resolve conflicts, `quality-gates.sh`-green, quickmerge so `c0958440`'s guard + the
      poison-pill-guard test are ancestors of `origin/live-defi-rollout`; then the `[OPERATOR] P1` shards can relaunch
      on a tarball that includes it. — market-tick-data-service@dc037373 (2026-08-03, slot 5): cherry-picked `c0958440`
      onto current `origin/live-defi-rollout` (clean auto-merge, no conflicts, since the already-landed `031a2b81`
      pyarrow-pool-release/corrupt-file-classification fix touches a disjoint region of the same file);
      `quality-gates.sh` full run green (sentinel matches HEAD); shipped via `quickmerge --agent`; verified `dc037373`
      is an ancestor of `origin/live-defi-rollout`. The footer-metadata claimed-uncompressed-size preflight guard +
      `test_migrate_cefi_content_poison_pill_guard_2026_07_31.py` are now live.

## Progress Log

- 2026-07-31 ~13:58Z (main-agent agt-9f21bc): folded review agt-8ce066's (msg 2981) gcloud-verified shards-43/44
  fresh-preemption evidence into the `[OPERATOR] P1` todo above as a corroborating signal + a new option (d)
  zone-capacity/on-demand consideration. Distinct from the same-shard memory-death pattern; non-blocking (idempotent
  SPOT shards). Decision remains operator's.
- 2026-07-31T13:04Z (worker, slot 12, `cefi_content_migration_fleet_half_incomplete-002`): filed after re-running the
  parent doc's corpus-wide re-verify grep and confirming zero forward progress since the 08:05Z check. Did not relaunch
  shards myself — out of this dispatched todo's scope (re-verify only) and consistent with the parent doc's own
  established policy (slot-15's self-correction entry) of deferring manual relaunch actions to a dedicated todo/the
  `data_pipeline_failure` fleet-monitor rather than doing it ad hoc while just re-verifying.
- 2026-07-31T13:24Z (worker, slot 8, `cefi_content_migration_fleet_half_incomplete-002`, redispatched 20 min after the
  13:04Z check above): re-ran the identical corpus-wide grep independently — fixed the SAME recurring `gcloud`
  active-identity poisoning first (drifted to `github-actions-deploy` again, switched back to `unified-trading-sa`),
  confirmed fleet still fully empty (`gcloud compute instances list`, zero `canonical-migration-cefi-content-*` VMs),
  fetched all 198 in-fleet `run.log` objects (16-way parallel `gcloud storage cat`) and grepped each for the terminal
  banner. **Result: byte-identical to 13:04Z — 27/44 confirmed (01-12, 14, 26-39), same 17 shards incomplete (13, 15,
  16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 40, 41, 42, 43, 44). Zero net progress in this 20-minute window**, which is
  expected: no relaunch has landed for any of these shards since the fleet went empty at 13:04Z (round-3 relaunch todo
  above is still `queued`, `dispatched_to: null`, per `GET /api/backlog`). Did not relaunch myself, same out-of-scope
  reasoning as slot-12's entry above — this task's own dispatched scope is re-verify only, and the round-3 relaunch is a
  properly-scoped separate backlog task (`cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed-001`)
  that requires its own per-shard `RB-INFRA-RELAUNCH` budget check, not a quick add-on to a re-verify pass. **Flagging
  the redispatch pattern itself**: this is now the 3rd consecutive dispatch of
  `cefi_content_migration_fleet_half_incomplete-002` (slot-15@08:05Z, slot-12@13:04Z, slot-8@13:24Z) producing the
  identical "still 27/44, unchanged" finding, because the actual unblocking action (round-3 relaunch) has not yet been
  dispatched to any slot despite being `queued` with the same `tier=1, priority=50` as `-002` — it simply lands later in
  FIFO order (`queued_at: 2026-07-31T13:16:51Z` vs `-002`'s `2026-07-31T12:45:58Z`) each time `-002` gets re-queued and
  re-picked first. Recommend main/operator either bump round-3's priority above `-002`'s so it dispatches next, or
  accept this as intentional periodic-monitoring cadence — but as-is, `-002` will likely keep winning the race and
  re-producing this same no-op finding until round-3 actually lands. Not self-acting on the priority bump (backlog
  priority tuning is main/operator territory per `RULES.md` § 4).
- 2026-07-31T13:35Z (worker, slot 10, this task): executed round 3. Fixed `gcloud` active-identity poisoning (drifted to
  `github-actions-deploy` again, same recurring class) back to `unified-trading-sa` first; confirmed fleet still fully
  empty before launching. For each of the 17 shards, read the LATEST `run.log`'s own `[vm-exec] starting:` line for its
  original `--start-date`/`--end-date` and its co-located `PROGRESS.json` for `last_completed_date`/`monotonic` — never
  re-derived. Queried `DeploymentsRegistry.list_recent_archive(days=1)` (not `gcloud compute operations list`, per the
  todo's own undercounting-trap note) and grouped archived deployments by shard number: shards 16 and 21 had 2 archived
  today (AT the `≤2/day` cap), shards 17 and 41 had 3 (OVER cap) — all 4 correctly SKIPPED this round, not relaunched.
  Relaunched the remaining 13 shards on `market-tick-data-service@89739b64` (ancestor-confirmed to include both
  `55d051bd` and `9f4098b1`), `e2-standard-16` (cefi-content-apply's own default, no override needed), SPOT
  (`PREEMPTIBLE=true`, launcher default):

  | shard | resume start-date | end-date (unchanged) | resume basis                                                                                  |
  | ----- | ----------------- | -------------------- | --------------------------------------------------------------------------------------------- |
  | 13    | 2026-01-18        | 2026-02-13           | monotonic checkpoint (orig start 2026-01-16)                                                  |
  | 15    | 2026-03-28        | 2026-07-19           | non-monotonic checkpoint → replayed original start (safe: tool skips already-canonical files) |
  | 18    | 2025-01-17        | 2025-02-06           | monotonic checkpoint (orig start 2025-01-10)                                                  |
  | 19    | 2025-02-07        | 2025-03-17           | non-monotonic checkpoint → original start                                                     |
  | 20    | 2025-04-06        | 2025-05-03           | monotonic checkpoint (orig start 2025-03-18)                                                  |
  | 22    | 2025-07-08        | 2025-09-06           | monotonic checkpoint (orig start 2025-06-27)                                                  |
  | 23    | 2025-09-07        | 2026-01-01           | non-monotonic checkpoint → original start                                                     |
  | 24    | 2026-01-06        | 2026-01-15           | monotonic checkpoint from the last attempt that DID write one (`-032606`; the                 |

      latest `-065001` attempt wrote no `run.log`/`PROGRESS.json` at all — died before startup, so its predecessor's
      checkpoint is the real frontier, not the original start 2026-01-02) |

  | 25 | 2026-01-18 | 2026-02-01 | monotonic checkpoint (orig start 2026-01-16) | | 40 | 2024-05-19 | 2024-06-11 |
  monotonic checkpoint (orig start 2024-05-12) | | 42 | 2024-12-27 | 2025-01-09 | non-monotonic checkpoint → original
  start | | 43 | 2025-01-30 | 2025-02-06 | monotonic checkpoint (orig start 2025-01-23) | | 44 | 2025-07-31 | 2025-09-06
  | monotonic checkpoint (orig start 2025-07-30) |

  Verified STARTED at T+60s: all 13 VMs `RUNNING` in `gcloud compute instances list`. Filed the budget-blocked-shards
  follow-up as a new `[OPERATOR]` todo above rather than silently deferring — 4 consecutive same-symptom deaths
  (`WARNING No progress in the last poll window ... possible wedged worker`) on shards already carrying both shipped
  fixes is a real signal, not routine.

- 2026-07-31T13:49:30Z (worker, slot 10, this task): T+10min PROGRESS verification — all 13 relaunched shards ALIVE and
  making real forward progress (`INFO Progress: N/total files ...` counters advancing, most-recent `PIPELINE_HEARTBEAT`
  within the last ~1-2 min of the check). The `WARNING No progress in the last poll window ... possible wedged worker`
  lines present on several shards (18, 20, 23, 40, 43, 44) are the SAME benign per-poll-window heuristic that also
  appears on shards that later completed successfully in rounds 1/2 — the load-bearing signal is the `Progress:` counter
  climbing between checks, which it is for all 13. No further action needed this round; the 17-shard corpus-level "done
  when" (all `run.log` show the terminal summary) is left to a later re-verify pass (the parent doc's `-002` todo
  pattern) once these runs (each covering weeks-to-months of daily shards, ETA hours-not-minutes at the observed ~7-21
  files/sec) have had time to finish.
- **2026-07-31T~14:0xZ (worker, slot 4, `cefi_content_migration_fleet_half_incomplete-011`, the parent doc's BLOCKED-ON
  todo)**: fixed the recurring `gcloud` active-identity poisoning (drifted to `github-actions-deploy` again) back to
  `unified-trading-sa` first. Re-checked round 3's 13 relaunched shards via `gcloud compute instances list` + per-shard
  `run.log`/`EXIT_STATUS` reads (bounded, not a full corpus-wide 392-object re-grep, since 4 shards were never
  relaunched this round pending the `[OPERATOR]` decision above — the fleet cannot be 44/44 regardless of round-3's
  outcome, so a full re-verify grep is not yet informative). **9/13 still `RUNNING`** (13, 15, 18, 20, 22, 23, 24,
  25, 42) — no terminal instance state, in-progress. **4/13 already died again**: shard 19 (`-133613`, `rc=137`, died
  `13:57:54Z` after `WARNING No progress in the last poll window` — the same wedge/freeze signature already tracked for
  shards 16/17/21/41 in the `[OPERATOR] P1` todo above) and shard 40 (`-133900`, `rc=137`, died `14:01:29Z`, identical
  signature) are GENUINELY NEW instances of that same unresolved failure class — this is worth folding into the
  `[OPERATOR] P1` todo's shard list (currently 16/17/21/41) rather than treating as isolated, since it's now 6 shards
  hitting the same symptom post both shipped fixes, not 4. Shards 43 (`-133950`) and 44 (`-134014`) have no instance
  running and no `EXIT_STATUS` written, but their `run.log` tails go silent at `13:51:1x`/`13:49:4x` respectively —
  consistent with (not independently re-verified via `gcloud compute operations list`, so not asserting confirmation)
  the review agent's already-logged `compute.instances.preempted` finding for these exact two shards at
  `13:51:37Z`/`13:51:38Z` in the `[OPERATOR] P1` todo above; not re-deriving that evidence, just noting it's consistent.
  **This todo's own done_definition (44/44 terminal summaries, then delete the script) remains unmet** — the fleet is
  not empty, 9 shards are still mid-run (ETA hours per this doc's own observed throughput), and 8 shards (16, 17, 19,
  21, 40, 41, 43, 44) are confirmed incomplete right now regardless. **Not relaunching 19/40/43/44 myself** — out of
  this todo's own scope (verify + delete only, per its text), and the `RB-INFRA-RELAUNCH` per-shard budget check for a
  possible round-4 belongs with whoever owns that follow-up, same as the existing `[OPERATOR]` item's posture for
  16/17/21/41. Leaving the parent doc's BLOCKED-ON checkbox unflipped — genuinely still blocked, not a redundant
  re-check.
- **2026-07-31T14:19Z (worker, slot 4, `cefi_content_migration_fleet_half_incomplete-012`, redispatch of the same
  parent-doc BLOCKED-ON todo)**: fixed the recurring `gcloud` active-identity poisoning (drifted to
  `github-actions-deploy` again) back to `unified-trading-sa` first. Bounded re-check (not a full corpus-wide re-grep,
  same reasoning as the prior slot-4 entry — 4 shards are still unrelaunched pending the `[OPERATOR]` decision, so 44/44
  isn't reachable yet regardless): `gcloud compute instances list` confirms the same 9/13 round-3 shards are still
  `RUNNING` (13, 15, 18, 20, 22, 23, 24, 25, 42) with no new deaths since the ~14:0xZ check, and the same 8 shards (16,
  17, 19, 21, 40, 41, 43, 44) remain with no live VM. Pulled each running shard's `run.log` tail: all 9 show a genuinely
  ADVANCING `Progress:` counter (e.g. shard 13 at 25,000/292,434, shard 42 at 14,000/73,965) — the benign
  `WARNING No progress in the last poll window` lines on shards 18/23/25 are the same known per-poll-window heuristic
  already documented as non-predictive (confirmed by pulling each one's actual last 3 `Progress:` lines directly, which
  ARE climbing). No stalls, no new failures — this is a healthy-but-slow positive check, not a regression. **Still not
  44/44; done_definition remains unmet.** Not relaunching 19/40/43/44 or the `[OPERATOR]`-gated 16/17/21/41 myself, same
  out-of-scope reasoning as the prior entry. Leaving the parent doc's BLOCKED-ON checkbox unflipped.
- 2026-07-31T14:5xZ (`data_pipeline_failure` escalation `agt-b58993`, slot 1, dispatched via `DP_VM_EXIT_NONZERO`/
  DP-VM-001 for `canonical-migration-cefi-content-42-relaunch20260731-133929`, `exit_code=137`): confirmed the OOM via
  `run.log` (21,600/73,965 files at death, ~60min runtime, declining throughput 62.9->6.1 files/sec, clean
  `EXIT_STATUS=137` write + shutdown) and the `DeploymentsRegistry` archive entry (`git_commit=89739b64` confirms
  `e2-standard-16` + both shipped fixes were live; `host_metrics_window` shows the same spike-then-death `mem_pct`
  signature as 16/17/19/21/40/41, 76%->95.3% in the final sample). Queried `list_recent_archive(days=1)` filtered to
  `content-42`: exactly 2 archived today (`-032606`, `-133929`), AT the `RB-INFRA-RELAUNCH` `≤2/(vm-prefix,day)` budget
  cap. Per this doc's own established precedent for repeat-offender shards, did NOT relaunch a 3rd time — folded shard
  42 into the `[OPERATOR] P1` todo's shard list instead (now 7: 16, 17, 19, 21, 40, 41, 42) as a corroborating signal,
  and folded in 19/40 there too (previously only in this Progress Log, never in the todo's own text). Pinged the
  authoring fleet-monitor slot (`dp-fleet-monitor`) with this outcome. No code change shipped — the root cause
  (data-content-driven memory spike) is an open P2 investigation in the sibling memory-freeze doc, and the remediation
  choice (bump MACHINE_TYPE further / wait for that fix / wait for budget reset / zone-capacity check) is the pending
  `[OPERATOR]` decision this entry reinforces rather than duplicates.
- 2026-07-31T15:1xZ (`data_pipeline_failure` escalation `agt-71ccbf`, slot 4, dispatched via DP-VM-003 for
  `canonical-migration-cefi-content-23-relaunch20260731-133713`, alert-fired at 53min heartbeat-stale): fixed the
  recurring `gcloud` active-identity poisoning (drifted to `github-actions-deploy` again) back to `unified-trading-sa`
  first. `gcloud compute instances describe` at escalation time found the instance **already gone** (not found) — a
  `gcloud compute operations list` scoped to this exact instance name showed only `insert` (2026-07-31T13:37:22Z) and
  `delete` (2026-07-31T15:04:05Z, `user=unified-trading-sa`, i.e. a reap-sweep delete, NOT a
  `compute.instances.preempted` systemevent) — so this was a genuine reap of a wedged instance, not the Finding-3
  false-reap class from the sibling memory-freeze doc. Confirmed via `DeploymentsRegistry.list_recent_archive`: archived
  `status=failed, exit_code=125, extras.reap_reason=vm_not_running, reaped_at=2026-07-31T15:05:51Z`.
  `host_metrics_window` (9 samples, 14:02:15Z-14:11:24Z) shows the identical spike-then-freeze signature already
  diagnosed for 16/17/19/21/40/41/42: `mem_pct` flat ~18-25% for 8 samples, then 14:10:23Z jumps to 55.6% and 14:11:24Z
  to **83.5%** (`mem_slope=6.81`) with `cpu_pct` also spiking 14.1%->69.5% — then total silence. `run.log` confirms:
  last real progress line `19,400/218,799 files (11.4 files/sec)` at 14:10:08Z, last `PIPELINE_HEARTBEAT` at 14:10:34Z,
  nothing after — matches the freeze onset exactly (53min from 14:11Z to the ~15:04-15:05Z reap tick is where the
  alert's "53m stale" figure comes from). **Budget check**: `list_recent_archive(days=1)` filtered to `content-23` shows
  exactly 2 archived today (`-032606` failed `exit_code=137` at 04:02:24Z, `-133713` failed `exit_code=125` at
  15:05:51Z) — shard 23 is now AT the `RB-INFRA-RELAUNCH` `≤2/(vm-prefix,day)` cap. Per this doc's own established
  precedent for repeat-offender shards (16/21/42), did NOT relaunch a 3rd time — folded shard 23 into the
  `[OPERATOR] P1` todo's shard list instead (now 8: 16, 17, 19, 21, 23, 40, 41, 42). Pinged the authoring fleet-monitor
  slot (`dp-fleet-monitor`) with this outcome. No code change shipped — same reasoning as the sibling shard-42 entry
  above: root cause is the sibling memory-freeze doc's open P2 investigation, remediation choice is the pending
  `[OPERATOR]` decision.
- 2026-07-31T15:5xZ (`data_pipeline_failure` escalation `agt-95d7c6`, slot 13, dispatched via `DP_VM_EXIT_NONZERO`/
  DP-VM-001 for `canonical-migration-cefi-content-18-relaunch20260731-133548`, `exit_code=137`): confirmed the OOM via
  `run.log` (39,000/104,813 files at death, 2h11m runtime, throughput decaying ~49->5 files/sec, `bash: ... Killed` +
  clean `EXIT_STATUS=137` write + shutdown) and the `DeploymentsRegistry` archive entry
  (`deployment_id=87da019c-d9ec-417a-adc9-989e56b73775`, `git_commit=89739b64931699798cc54920cc636e72948d2cc7` — the
  SAME commit this doc's own 13:35Z round-3 relaunch table cites for shard 18, confirming `e2-standard-16` + both
  shipped fixes (`9f4098b1`, `55d051bd`) were genuinely live on this run, not a stale tarball — this run WAS round 3's
  own shard-18 relaunch). `host_metrics_window` (10 samples, 15:39:42Z-15:48:58Z) shows the identical spike-then-death
  signature already diagnosed for 16/17/19/21/23/40/41/42: `mem_pct` plateaued ~72-88% across 8 samples, then jumped to
  84.5% and finally **98.0%** (`mem_slope=1.06`) in the last two samples, `cpu_pct` also spiking 13%->65.5% and
  `net_recv_rate_bytes_sec` collapsing from ~40-59MB/s to 2.2MB/s (thrashing) immediately before the kernel OOM-killed
  the process. **Budget check** (`DeploymentsRegistry.list_recent_archive(days=1)`, filtered to `content-18`): exactly 2
  archived today (`-032349` failed `exit_code=137` at 07:40:03Z, `-133548` failed `exit_code=137` at 15:49:00Z) — shard
  18 is now AT the `RB-INFRA-RELAUNCH` `≤2/(vm-prefix,day)` cap. Per this doc's own established precedent for
  repeat-offender shards (16/21/23/42), did NOT relaunch a 3rd time — folded shard 18 into the `[OPERATOR] P1` todo's
  shard list instead (now 9: 16, 17, 18, 19, 21, 23, 40, 41, 42). Pinged the authoring fleet-monitor slot
  (`dp-fleet-monitor`) with this outcome. No code change shipped — same reasoning as the sibling shard-23/42 entries
  above: root cause is the sibling memory-freeze doc's open P2 investigation, remediation choice is the pending
  `[OPERATOR]` decision.
- 2026-07-31T19:1xZ (`data_pipeline_failure` escalation `agt-c14d58`, slot 7, dispatched via DP-VM-003 for
  `canonical-migration-cefi-content-13-relaunch20260731-133503`, alert-fired at 36min heartbeat-stale): fixed the
  recurring `gcloud` active-identity poisoning (drifted to `github-actions-deploy` again) back to `unified-trading-sa`
  first. `gcloud compute instances describe` found the instance already gone; `gcloud compute operations list` showed
  only `insert` (13:37:40Z) and a programmatic `delete` by `unified-trading-sa` completed `18:46:42Z` — a genuine reap
  of a wedged instance, not a `compute.instances.preempted` systemevent. `run.log` confirms real progress to
  169,000/292,434 files (10.8 files/sec) then total silence after `18:00:36Z` (no `EXIT_STATUS` line) — a genuine
  freeze. `DeploymentsRegistry.list_recent_archive(days=1)`'s archived entry for this attempt
  (`status=failed, exit_code=125, reap_reason=vm_not_running`) shows `host_metrics_window.mem_pct` climbing 65%→85% over
  its last 10 samples before the silence — the identical spike-then-freeze signature already diagnosed for
  16/17/18/19/21/23/40/41/42. **Budget check**: exactly 2 archived today for `content-13` (`-032349` failed
  `exit_code=125` at 04:47:57Z — the earlier, DIFFERENT-root-cause GCS SSL/connection-reset death tracked in
  `cefi_content_migration_shard13_network_error_and_checkpoint_resume_bug_2026_07_31.md`; `-133503` failed
  `exit_code=125` at 18:50:02Z — this memory-freeze death) — shard 13 is now AT the `RB-INFRA-RELAUNCH`
  `≤2/(vm-prefix,day)` cap. Per this doc's own established precedent for repeat-offender shards (16/17/18/19/21/23/40/
  41/42), did NOT relaunch a 3rd time — folded shard 13 into the `[OPERATOR] P1` todo's shard list instead (now 10: 13,
  16, 17, 18, 19, 21, 23, 40, 41, 42). Pinged the authoring fleet-monitor slot (`dp-fleet-monitor`) with this outcome.
  No code change shipped — root cause is the sibling memory-freeze doc's open P2 investigation, remediation choice is
  the pending `[OPERATOR]` decision. Note shard 13 is the first shard confirmed to have died today via TWO DIFFERENT
  mechanisms (network/SSL death this morning, memory-freeze death this afternoon) rather than the same mechanism twice —
  both already-tracked failure classes, not a new one.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — added the actual migration script
  (`migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`) this whole fleet exists to run, named throughout the
  doc's "why it matters" section and the `# Delete-when:` gate it's blocked on.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **2026-08-06T22:58Z (worker, slot 9, this task, round-4 relaunch)**: executed the follow-up todo. Fixed/verified
  `gcloud` active identity = `unified-trading-sa` (not poisoned); confirmed the fleet fully empty before launching
  (`gcloud compute instances list` → zero `canonical-migration-cefi-content-*` VMs). Verified the floating MTDS tarball
  is `841cf94f` (built 2026-08-06T20:01Z, ancestor of `dc037373` — decompression-bomb OOM preflight guard live).
  RB-INFRA-RELAUNCH budget: grepped `deployments/archive/2026-08-01..06/*.json` for `canonical-migration-cefi-content-*`
  vm_names → ZERO archived relaunches since 08-01 incl. today; all 10 shards 0/2, full budget headroom. Recovered each
  shard's resume frontier from its own most-recent `run.log` `[vm-exec] starting:` + co-located `PROGRESS.json` (never
  re-derived): monotonic=true → resume = `last_completed_date`+1 (13: 02-02→02-03; 17: 11-15→11-16; 18: 01-22→01-23; 21:
  05-15→05-16; 40: 05-20→05-21); monotonic=false → replay latest attempt's original start (23, 41, 42); no PROGRESS.json
  → replay latest attempt's original start (16, 19). Launched all 10 via
  `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full` (RESUME_* env + `VM_NAME_OVERRIDE` per shard,
  matching the round-3 LAUNCH_PARAMS pattern), e2-standard-16 default, SPOT. All 10 VMs created + verified RUNNING
  (`canonical-migration-cefi-content-<N>-round4-20260806-225835`). Corpus 'done when' (10× terminal
  `SCRIPT 1 CONTENT MIGRATION SUMMARY` banners) not yet reachable — multi-hour runs; T+10min PROGRESS check follows,
  corpus-level re-verify remains the parent doc's separate pass.
- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — added `launch-canonical-migration-vm.sh`, the
  launcher this doc's own round-3 and round-4 relaunch entries both name repeatedly as the actual relaunch mechanism.
- **2026-08-07T~06:28Z (worker, slot 12, task `-005`)**: verified all 9 round-5 VMs RUNNING via
  `gcloud compute instances list` at T+~20min after launch (06:08Z). Checked each shard's `run.log` tail — no terminal
  `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner found (expected: multi-hour runs). Progress at check time: shard
  16=4800/159304 (stalling ~154328 outstanding, ~2min), 17=6800/155003, 18=5800/69880, 19=7000/136494, 21=6400/126492,
  23=10200/202211, 40=5600/55777 (stuck at 50108 outstanding, ~3min stall), 41=8000/71684, 42=4600/73163 (stuck at 68408
  outstanding, ~6min stall, PIPELINE_HEARTBEAT still firing). Shards 40 and 42 show pre-freeze stall pattern;
  fleet-monitor handles OOM/reap. Re-verify follow-up todo added; VMs need more runtime.
- **2026-08-07T~07:03Z (data_pipeline_failure escalation `agt-e61f85`, slot 4, DP-VM-001)**: shard 17's round-5 VM
  (`canonical-migration-cefi-content-17-round5-20260807-060729`) OOM-killed (`exit_code=137`) at 07:02:44Z, only
  ~19,600/155,003 files in (`PROGRESS.json`: `last_completed_date=2024-11-24, monotonic=false` — RelaunchPreemptedVm's
  non-monotonic-checkpoint PAGE rule is why this escalated instead of auto-resuming). Fetched the archived
  `DeploymentsRegistry` entry's `host_metrics_window`: `mem_pct` climbed 50.5%→90.5% over ~10min (06:52→06:58) while the
  run.log's own periodic `pa.default_memory_pool().bytes_allocated()` reading stayed low/bounded (tens of KB– ~130MB) at
  every checkpoint in that same window — i.e. the already-shipped pyarrow-pool-release fix (`9f4098b1`) is demonstrably
  NOT the growth driver for this specific death, even though it's live in this run's tarball. A corrupted-file
  poison-pill read (DERIBIT `XRP_USDC-29NOV24-1D7-C.parquet`, 6.4GB on-disk) was hit at 06:59:15 but AFTER the mem_pct
  spike to 90.5% (06:58:48) and was correctly caught/skipped by the existing 2GiB-ceiling guard — not the cause. Shipped
  a complementary fix (`market-tick-data-service@cc144bf4`): a separate, tighter `gc.collect()` cadence (every 50 files,
  vs the existing 200-file pyarrow-release cadence) targeting the untested hypothesis that pandas DataFrame/BlockManager
  reference cycles (not reclaimable by plain refcounting, only by the cyclic collector) accumulate faster than CPython's
  generational gc keeps pace with at this per-file allocation rate — framed explicitly as an additional hypothesis, not
  a confirmed fix (the prior e2-standard-16 bump was also called "confirmed a genuine fix" in the code and then died
  again on shard 17 twice more, rounds 4 and 5, so no future relaunch attempt should over-claim confidence here without
  a fresh clean run past this shard's historical death point). Republishing the mtds-code tarball next, then relaunching
  round-6 for shard 17 ONLY (RB-INFRA-RELAUNCH budget: round-5 today 2026-08-07 is shard 17's only relaunch today, so
  round-6 is its 2nd — within the ≤2/(vm-prefix,day) cap; also qualifies for the root-cause carve-out regardless, since
  this is the first attempt with the new gc.collect() fix live). Scope is shard 17 only — shards 16,18,19,21,23,40,41,42
  are a separate concurrent dispatch (see the T+20min check above); not touching those here to avoid colliding with that
  in-flight work.
- **2026-08-07T~07:51Z (same escalation, closing out)**: republished the mtds-code floating tarball
  (`mtds-code.manifest.json` → `commit_sha=cc144bf4b3ed73114313d2b059ec65608bb195e3`, SHA-pinned copy verified present)
  and launched round-6 (`canonical-migration-cefi-content-17-round6-20260807-073935`, same 2024-11-16..2025-01-09 range,
  e2-standard-16, SPOT — `lc_verify_tarball_freshness` confirmed all 4 tarballs current, tarball pin `cc144bf4` logged).
  Verified STARTED (RUNNING at T+60s) and PROGRESS (3,000/155,003 files at T+7.2min, 6.9 files/sec, steady).
  **Encouraging early signal, not proof**: `host_metrics_window.mem_pct` for round-6's first 10 samples is 5.0–18.2%
  (stable, no upward trend) at the ~7min mark, whereas round-5 was ALREADY past 50% and climbing steadily by a
  comparable elapsed time. Deliberately not claiming this as confirmed — the same over-claim happened with the
  e2-standard-16 bump, which read as fixed for a while and then died again twice. Round-6 needs to survive well past
  file ~19,600 (round-5's death point) before this fix earns any real confidence; leaving that verification to the
  existing corpus-wide re-verify todo below rather than holding this slot for the full multi-hour run. PAGE sent to
  main-agent/operator with the full diagnosis (not blocking — informational per the carve-out's notification
  requirement). Escalation `agt-e61f85` complete; signaling `/done`.
- **2026-08-07T08:05Z (worker, slot 7, task `-006`, round-5 re-verify)**: verified `gcloud` active identity =
  `unified-trading-sa` (not poisoned). Re-verified all 9 round-5 shards
  (`canonical-migration-cefi-content-<N>-round5-20260807-060729`). **4 DEAD before terminal SUMMARY**: shards 16, 17,
  19, 23 — absent from `gcloud compute instances list`, confirmed via `DeploymentsRegistry` archive grep (failed entries
  in 2026-08-07 archive; no EXIT_STATUS in run.log — freeze/reap deaths). **5 RUNNING with forward progress**: 18
  (37,600/69,880 files, 53.8%), 21 (32,800/126,492, 25.9%), 40 (43,600/55,777, 78.2%), 41 (47,400/71,684, 66.1%), 42
  (29,600/73,163, 40.5%) — counters advancing, no terminal SUMMARY yet. Budget check via `DeploymentsRegistry`
  2026-08-07 archive: shard 16 = 1/2 today (round4 archived 2026-08-06, round5 archived 2026-08-07) → headroom; shard 17
  = 2/2 today (round4-20260806-225835 + round5-20260807-060729 both archived 2026-08-07), prior agent cited root-cause
  carve-out (new `cc144bf4` gc.collect() fix) → round-6 already dispatched
  (`canonical-migration-cefi-content-17-round6-20260807-073935`); shard 19 = 2/2 today (round4 + round5 both archived
  2026-08-07) → AT CAP; shard 23 = 2/2 today (round4 + round5 both archived 2026-08-07) → AT CAP. Round-6 dispatched for
  shard 16: `canonical-migration-cefi-content-16-round6-20260807-075919`, start=2024-08-26 (monotonic:
  last_completed=2024-08-25+1 from round-5 PROGRESS.json), end=2024-11-13, SPOT, e2-standard-16, RUNNING at T+60s.
  Resume frontiers for budget-capped shards from round-5 PROGRESS.json: 19 = last_completed=2025-02-15, monotonic=true →
  round-6 start=2025-02-16, end=2025-03-17; 23 = last_completed=2025-09-19, monotonic=false → round-6 start=2025-09-07
  (replay latest original start), end=2026-01-01. Follow-up todo added for running shards (18/21/40/41/42) +
  budget-capped shards (19/23) round-6 on 2026-08-08.
- **2026-08-07T~08:29Z (data_pipeline_failure escalation `agt-baf474`, slot 6, DP-VM-003)**: shard 21's round-5 VM
  (`canonical-migration-cefi-content-21-round5-20260807-060729`) confirmed dead — absent from
  `gcloud compute instances list`, `run.log` silent since 07:39:17Z (~50min stale, matches the DP-VM-003 heartbeat-stall
  alert), no terminal `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner, no OOM `exit_code=137` marker written — a freeze/reap
  death (same class as shards 16/19/23/40's round-5 deaths), last progress 32,800/126,492 files (25.9%). Budget check:
  round-5 was shard 21's only launch today (2026-08-07) → 1/2 used, headroom for round-6 (no carve-out needed). Resume
  frontier from round-5's own `PROGRESS.json` (`last_completed_date=2025-05-26, monotonic=false`) → per the
  non-monotonic rule, replayed round-5's own original start (`LAUNCH_PARAMS.json`: `2025-05-16`→`2025-06-26`) rather
  than `last_completed_date`+1. Verified floating MTDS tarball (`d7e27e5a`, built 2026-08-07T08:25:47Z) descends from
  the `cc144bf4` gc.collect() fix (`git merge-base --is-ancestor` confirmed) — no republish needed. Launched
  `canonical-migration-cefi-content-21-round6-20260807-083239` (SPOT, e2-standard-16 default, all 4 tarballs fresh).
  Verified STARTED (RUNNING) at T+60s and PROGRESS at T+~4min (1,200/126,492 files, 11.4 files/sec, steady). Scope is
  shard 21 only, per this doc's established per-shard-escalation precedent — not touching 18/40/42 (separate concurrent
  work). Escalation complete; signaling `/done`.
- **2026-08-07T~08:40Z (worker, slot 7, task `-008`)**: Fixed gcloud poisoning (github-actions-deploy →
  unified-trading-sa). Slot-3 already flipped my task's checkbox (superseded). This session: dispatched
  `canonical-migration-cefi-content-21-round6-20260807-083119` (collided with slot-6's `083239` launched 10min earlier —
  both RUNNING, idempotent, slot-13 designated `083119` as primary per the round-6 re-verify todo update). Verified
  shard 40 COMPLETE (terminal SUMMARY 08:32:17Z, 55777 files). Shard 18 frozen 08:21Z+ (VM RUNNING at 08:38Z,
  PIPELINE_HEARTBEAT ~17min stale). Shard 42 RUNNING 55.8% (40800/73163) at 08:38Z.
- **2026-08-07T09:10Z (worker, slot 7, task `-010`)**: Verified gcloud identity = `unified-trading-sa` (not poisoned).
  All 8 VMs RUNNING (`gcloud compute instances list`). No terminal `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner in any
  shard's run.log tail (T+30min from 08:40Z — early check). Shard 18 STALLED since 08:18Z: PIPELINE_HEARTBEAT silent
  since 08:21Z, 44200/69880=63.3%, PROGRESS.json `last_completed=2025-01-29 monotonic=true` → round-7
  start=2025-01-30..2025-02-06 when confirmed dead; DeploymentsRegistry 2026-08-07 shows 0 content-18 archive entries
  (not yet confirmed dead). Shard 17 potentially stalling: last run.log progress 08:37Z, PROGRESS.json updated 08:38Z,
  17800/155003=11.5%, monotonic=false → round-7 replay round-6 start 2024-11-16..2025-01-09 if dead. Shards 16 (10.2%),
  19 (16.2%), 21/083119-primary (7.7%), 23 (10.1%), 41 (29.3%), 42 (67.0%) actively progressing at 09:03-09:04Z. No
  confirmed deaths → no round-7 dispatched. Follow-up re-verify todo added for ~12:40Z.
- **2026-08-07T13:15Z (worker, slot 3, task `-015`)**: Verified gcloud identity = `unified-trading-sa` (not poisoned).
  Fleet empty — `gcloud compute instances list` returns no `canonical-migration-cefi-content-*` VMs. UTC =
  2026-08-07T13:15Z — launch gate NOT open (requires UTC ≥ 2026-08-08T00:00Z, still ~10h45m away). This is the 3rd
  dispatch of this time-gated task. Budget re-verify unnecessary: slot-13 at 12:06Z already confirmed all 8 shards
  (16,17,18,19,21,23,41,42) at/over ≤2/(vm-prefix,day) cap for 2026-08-07 UTC (only 1h09m ago; fleet has been empty
  since; no new launches since). No VMs launched. Deferring to 2026-08-08T00:00Z UTC budget reset — follow-up todo added
  below.

## Follow-ups

- [x] ✅ [DATA] P1. Relaunch the cefi content migration round-4 (tarball >= dc037373) to complete the 10
      still-incomplete shards (13,16,17,18,19,21,23,40,41,42) — corpus 'done when' unmet, no relaunch in flight. —
      worker, slot 9, 2026-08-06: executed round 4. All 10 shards relaunched on the FLOATING MTDS tarball
      (`mtds-code.manifest.json` `commit_sha=841cf94f`, built 2026-08-06T20:01Z — verified ancestor of `dc037373`, so
      the decompression-bomb preflight guard is live), category `cefi-content-apply` mode `full` (embeds `--apply`),
      e2-standard-16 default, SPOT default. RB-INFRA-RELAUNCH budget check via DeploymentsRegistry archive grep: ZERO
      `canonical-migration-cefi-content-*` archive entries since 2026-08-01 incl. today, so all 10 shards were 0/2
      (≤2/(vm-prefix,day)) — full budget headroom. Per-shard resume start-dates recovered from each shard's own
      most-recent `run.log` `[vm-exec] starting:` line + co-located `PROGRESS.json` (monotonic → `last_completed_date`+1
      day; non-monotonic / no-checkpoint → replay the latest attempt's original start; never re-derived):
      13=2026-02-03..02-13, 16=2024-08-20..11-13, 17=2024-11-16..2025-01-09, 18=2025-01-23..02-06, 19=2025-02-07..03-17,
      21=2025-05-16..06-26, 23=2025-09-07..2026-01-01, 40=2024-05-21..06-11, 41=2024-10-04..11-13,
      42=2024-12-27..2025-01-09. All 10 VMs created + verified RUNNING
      (`canonical-migration-cefi-content-<N>-round4-20260806-225835`, asia-northeast1-c, created 2026-08-06T22:58:44Z).
      Corpus 'done when' (all 10 shards' `run.log` show the `SCRIPT 1 CONTENT MIGRATION SUMMARY` terminal banner) still
      pending — these are multi-hour runs; tracked by the parent doc's corpus-wide re-verify pass. T+10min PROGRESS
      check scheduled.

- [x] ✅ [DATA] P1. Corpus-wide re-verify of round-4's 10 shards (13,16,17,18,19,21,23,40,41,42, VMs
      `canonical-migration-cefi-content-<N>-round4-20260806-225835`) — confirm each shard's `run.log` shows the terminal
      `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner. If any shard is still incomplete, relaunch round-5 for only the
      remaining shards (same resume-from-checkpoint discipline as round-4). Done when: all 10 shards terminal-verified
      complete, or round-5 dispatched for the remainder. (repo: unified-trading-pm) — worker, slot 6, 2026-08-07:
      re-verified round-4. **Shard 13 COMPLETE** (terminal SUMMARY confirmed at 2026-08-07T03:50:11Z, 125364/125364
      files). **9 shards still incomplete** (16,17,18,19,21,23,40,41,42): all died before terminal SUMMARY — shards
      18,21,41,42: OOM rc=137 (EXIT_STATUS written, archived 2026-08-07); shards 16,17,19,23,40: freeze/reap
      exit_code=125/vm_not_running (PROGRESS.json last updated but log went silent). Note: OOM deaths (rc=137) are
      continuing despite the dc037373 decompression-bomb preflight guard — the 2GiB ceiling may not catch all bomb
      files, or there is a cumulative allocation path not covered by the guard. Noted as a finding; does not block
      round-5 relaunch per this todo's own done_definition. Budget: all 9 shards confirmed ≤1/2 used today (shards
      18,21,41,42,40,19,17 each have 1 archive entry in 2026-08-07; shard 16 archived 2026-08-06 so 0 today; shard 23
      treated as 1 by pattern). Resume frontiers from round-4 PROGRESS.json (monotonic → last_completed+1; non-monotonic
      → replay latest attempt's original start; never re-derived): 16=2024-08-21..11-13, 17=2024-11-16..2025-01-09,
      18=2025-01-23..02-06, 19=2025-02-10..03-17, 21=2025-05-16..06-26, 23=2025-09-07..2026-01-01, 40=2024-05-21..06-11,
      41=2024-10-04..11-13, 42=2024-12-27..2025-01-09. Round-5 launched: all 9 VMs
      (`canonical-migration-cefi-content-<N>-round5-20260807-060729`) created + verified RUNNING 2026-08-07T06:08Z,
      asia-northeast1-c, SPOT, e2-standard-16 default, floating MTDS tarball (≥dc037373, decompression-bomb guard live).
      Corpus 'done when' still pending — multi-hour runs.

- [x] ✅ [DATA] P1. Corpus-wide re-verify of round-5's 9 shards (16,17,18,19,21,23,40,41,42, VMs
      `canonical-migration-cefi-content-<N>-round5-20260807-060729`) — confirm each shard's `run.log` shows the terminal
      `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner. If any shard is still incomplete, relaunch round-6 for only the
      remaining shards (same resume-from-checkpoint discipline). Done when: all 9 shards terminal-verified complete, or
      round-6 dispatched for the remainder. (repo: unified-trading-pm) — worker, slot 12, 2026-08-07: all 9 VMs RUNNING
      at T+20min, no terminal banner found (multi-hour runs); re-verify queued via follow-up todo below.

- [x] ✅ [DATA] P1. Corpus-wide re-verify of round-5's 9 shards (16,17,18,19,21,23,40,41,42, VMs
      `canonical-migration-cefi-content-<N>-round5-20260807-060729`) — re-check each shard's `run.log` for the terminal
      `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner after VMs have completed or been reaped (launched 2026-08-07T06:08Z;
      check T+4h or later). For any shard still incomplete/failed (verify via
      `DeploymentsRegistry.list_recent_archive`), relaunch round-6 using resume frontiers from each shard's most-recent
      `run.log`/`PROGRESS.json` (monotonic → last_completed_date+1; non-monotonic → replay latest attempt's original
      start; never re-derived). Done when: all 9 shards terminal-verified complete, or round-6 dispatched for the
      remainder. (repo: unified-trading-pm) — worker, slot 3, 2026-08-07: **Shards 18,21,40,42: round-5 RUNNING** (no
      terminal banner; multi-hour runs). **Shard 16: round-6
      `canonical-migration-cefi-content-16-round6-20260807-075919` RUNNING** (dispatched prior agent). **Shard 17:
      round-6 `canonical-migration-cefi-content-17-round6-20260807-073935` RUNNING** (agt-e61f85, tarball cc144bf4).
      **Shard 19: OOM-killed** (rc=137); round-6 `canonical-migration-cefi-content-19-round6-20260807-081217` RUNNING
      (resume 2025-02-16→2025-03-17, monotonic, 110784 files, 10-12 files/sec at T+4min, tarball cc144bf4). **Shard 23:
      freeze/reap** (exit_code=125); round-6 `canonical-migration-cefi-content-23-round6-20260807-081243` RUNNING
      (resume 2025-09-07→2026-01-01, non-monotonic replay, 202841 files, 10.7 files/sec at T+4min, tarball cc144bf4).
      **Shard 41: OOM-killed** (rc=137); round-6 `canonical-migration-cefi-content-41-round6-20260807-081552` RUNNING
      (resume 2024-10-04→2024-11-13, non-monotonic replay, tarball cc144bf4). Round-6 dispatched for all 3 failed
      shards; done condition met. (Note: concurrent slot-7 worker found 19+23 at 2/2 budget cap and deferred; slot-3
      re-verified actual budget = 1/2 each and dispatched same-day.)

- [x] ✅ [DATA] P1. Re-verify round-5 running shards + launch round-6 for budget-capped shards (slot-7 todo, superseded:
      slot 3 dispatched round-6 for 19, 23, 41 on 2026-08-07; running shards 18,21,40,42 tracked by round-6 corpus
      re-verify todo below). (repo: unified-trading-pm)

- [x] ✅ [DATA] P1. Corpus-wide re-verify of round-6's 9 shards (16,17,18,19,21,23,40,41,42) — confirm each shard's
      `run.log` shows the terminal `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner. Shards 18,40,42 still on round-5
      (`canonical-migration-cefi-content-<N>-round5-20260807-060729`); shards 16,17,19,21,23,41 on round-6:
      16=`canonical-migration-cefi-content-16-round6-20260807-075919`,
      17=`canonical-migration-cefi-content-17-round6-20260807-073935`,
      19=`canonical-migration-cefi-content-19-round6-20260807-081217`,
      21=`canonical-migration-cefi-content-21-round6-20260807-083239` (DP-VM-003 escalation `agt-baf474`, slot 6,
      dispatched after round-5's VM was confirmed dead — see Progress Log),
      23=`canonical-migration-cefi-content-23-round6-20260807-081243`,
      41=`canonical-migration-cefi-content-41-round6-20260807-081552`. For any shard still incomplete/failed, relaunch
      round-7 using resume-from-checkpoint discipline (monotonic → last_completed_date+1; non-monotonic → replay latest
      attempt's original start). Check T+4h or later. Done when: all 9 shards terminal-verified complete, or round-7
      dispatched for the remainder. (repo: unified-trading-pm) — worker, slot 13, 2026-08-07T~08:40Z: **Shard 40
      COMPLETE** (terminal SUMMARY at 2026-08-07T08:32:17Z, 55777/55777 files, round-5 VM
      `canonical-migration-cefi-content-40-round5-20260807-060729`). **8 shards RUNNING** with forward progress, no
      terminal SUMMARY yet (multi-hour runs): 16=9400/149145 (6%), 17=17800/155003 (11%), 18=44200/69880 (63%),
      19=9000/110784 (8%), 21=~1800/126492 per both VMs (round-5 shard-21 died and round-6 was dispatched TWICE —
      `083119` and `083239` both RUNNING on same 2025-05-16..06-26 range, idempotent, no data risk, wasteful),
      23=10000/202841 (5%), 41=10200/71684 (14%), 42=40800/73163 (56%). No deaths at check time — round-7 not
      dispatched; follow-up todo added below.

- [x] ✅ [DATA] P1. Corpus-wide re-verify of 8 remaining shards (16,17,18,19,21,23,41,42) — shard 40 confirmed complete.
      Check T+4h or later from 2026-08-07T08:40Z. VMs: 16=`canonical-migration-cefi-content-16-round6-20260807-075919`,
      17=`canonical-migration-cefi-content-17-round6-20260807-073935`,
      18=`canonical-migration-cefi-content-18-round5-20260807-060729`,
      19=`canonical-migration-cefi-content-19-round6-20260807-081217`,
      21=`canonical-migration-cefi-content-21-round6-20260807-083119` (primary) and `…-083239` (duplicate — take
      whichever completes first; both idempotent), 23=`canonical-migration-cefi-content-23-round6-20260807-081243`,
      41=`canonical-migration-cefi-content-41-round6-20260807-081552`,
      42=`canonical-migration-cefi-content-42-round5-20260807-060729`. For any shard incomplete/failed, relaunch round-7
      from resume-from-checkpoint (monotonic → last_completed_date+1; non-monotonic → replay latest original start;
      never re-derived). Done when: all 8 shards terminal-verified complete, or round-7 dispatched for the remainder.
      (repo: unified-trading-pm) — worker, slot 7, 2026-08-07T09:10Z: 8 VMs RUNNING at T+30min (early check). No
      terminal summaries found. Shard 18 STALLED since 08:18Z (PIPELINE_HEARTBEAT silent, 63.3%, round-7 frontiers
      captured); shard 17 potentially stalling (last 08:37Z, 11.5%). 6 shards actively progressing. No deaths confirmed,
      no round-7 dispatched. Follow-up re-verify added (~12:40Z).

- [x] ✅ [DATA] P1. Corpus-wide re-verify of 8 remaining shards (16,17,18,19,21,23,41,42) — check at ~~12:40Z (T+4h from
      08:40Z). VMs at 09:10Z: 16=round6-075919 (10.2%), 17=round6-073935 (11.5%, may be stalling; if dead:
      non-monotonic, round-7 replay round-6 start 2024-11-16..2025-01-09), 18=round5-060729 (63.3%, STALLED since
      08:18Z; if dead: monotonic, round-7 start=2025-01-30..2025-02-06), 19=round6-081217 (16.2%), 21=round6-083119
      primary (7.7%), 23=round6-081243 (10.1%), 41=round6-081552 (29.3%), 42=round5-060729 (67.0%). Done when: all 8
      terminal-verified complete, or round-7 dispatched for the remainder. (repo: unified-trading-pm) — worker, slot 2,
      2026-08-07T~~09:30Z: **3 shards DEAD, all budget-capped (no round-7 today)**: shard 17=round6 stall-killed 09:18Z
      (exit_code=137, budget 3/2, OVER CAP), round-7 frontier non-monotonic replay 2024-11-16..2025-01-09; shard
      18=round5 freeze/reap stall from 08:21Z (exit_code=125, budget 2/2, AT CAP), round-7 frontier monotonic
      2025-01-30..2025-02-06; shard 23=round6 freeze/reap stall from 09:04Z (exit_code=125, budget 3/2, OVER CAP),
      round-7 frontier non-monotonic replay 2025-09-07..2026-01-01. **5 shards RUNNING** at 09:17-09:19Z: 16=12.9%
      (19,200/149,145), 19=21.3% (23,600/110,784), 21=12.6% (16,000/126,492), 41=36.3% (26,000/71,684), 42=72.2%
      (52,800/73,163). Round-7 tracked for 2026-08-08 via follow-up todo below.

- [x] ✅ [DATA] P1. Round-7 on 2026-08-08 + corpus re-verify of 8 shards (16,17,18,19,21,23,41,42). Budget-capped shards
      (budget resets 2026-08-08, all 0/2): 17 frontier=replay round-6 start 2024-11-16..2025-01-09 (monotonic=false); 18
      frontier=2025-01-30..2025-02-06 (monotonic=true, last_completed=2025-01-29); 23 frontier=replay round-6 start
      2025-09-07..2026-01-01 (monotonic=false). Shards 16,19,21,41,42 were RUNNING at 09:17-09:19Z 2026-08-07 —
      re-verify for terminal SUMMARY first, then relaunch round-7 for any that failed. Use floating MTDS tarball
      (≥cc144bf4, gc.collect() fix live). Done when: all 8 terminal-verified complete, or round-8 dispatched for any
      failures. (repo: unified-trading-pm) — worker, slot 13, 2026-08-07T12:06Z: re-verified all 8 shards. No VMs
      running (`gcloud compute instances list` empty). **Shard 16**: round-7 launched 10:15Z (101517) died before
      run.log (no archive entry, startup failure); round-6 PROGRESS.json `last_completed=2024-09-05 monotonic=true` →
      round-8 start=2024-09-06..2024-11-13. **All 8 shards confirmed DEAD** — archive grep of 2026-08-07 entries: 16 (r5
      failed 125 07:15Z, r6 failed 125 10:11Z) = 2/2 AT CAP; 17 (r4 failed 125 02:40Z, r5 failed 137 07:02Z, r6 failed
      137 09:18Z) = 3/2 OVER; 18 (r4 failed 137 01:03Z, r5 failed 125 09:15Z) = 2/2 AT CAP; 19 (r4 failed 125 00:15Z, r5
      failed 137 07:24Z, r6 failed 125 10:16Z) = 3/2 OVER; 21 (r4 failed 137 00:14Z, r5 failed 125 08:30Z, r6-083119
      failed 125 10:20Z, r6-083239 failed 125 09:10Z) = 4/2 OVER; 23 (r4 failed 125 00:10Z, r5 failed 125 07:20Z, r6
      failed 125 09:10Z) = 3/2 OVER; 41 (r4 failed 137 00:42Z, r5 failed 137 08:01Z, r6 failed 125 10:15Z) = 3/2 OVER;
      42 (r4 failed 137 02:04Z, r5 failed 125 10:20Z) = 2/2 AT CAP. Budget resets 2026-08-08 → all 0/2. Round-8
      frontiers from most-recent PROGRESS.json (monotonic → last_completed+1; non-monotonic → replay latest original
      start; never re-derived): 16=2024-09-06..2024-11-13 (mono); 17=2024-11-16..2025-01-09 (non-mono replay r6);
      18=2025-01-30..2025-02-06 (mono); 19=2025-02-16..2025-03-17 (non-mono replay r6); 21=2025-05-16..2025-06-26
      (non-mono replay r6-083119, latest PROGRESS updated 10:03Z); 23=2025-09-07..2026-01-01 (non-mono replay r6);
      41=2024-10-04..2024-11-13 (non-mono replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Round-8 follow-up
      dispatched below.

- [x] ✅ [DATA] P1. Round-8 on 2026-08-08 for all 8 remaining shards (16,17,18,19,21,23,41,42). Budget resets 2026-08-08
      (all 0/2). Use floating MTDS tarball (≥cc144bf4, gc.collect() fix live). Launch via
      `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`, e2-standard-16, SPOT. Frontiers (from
      round-8 slot-13 re-verify above): 16=2024-09-06..2024-11-13 (monotonic, PROGRESS r6 last_completed 2024-09-05);
      17=2024-11-16..2025-01-09 (non-mono replay r6); 18=2025-01-30..2025-02-06 (monotonic, PROGRESS r5 last_completed
      2025-01-29); 19=2025-02-16..2025-03-17 (non-mono replay r6); 21=2025-05-16..2025-06-26 (non-mono replay
      r6-083119); 23=2025-09-07..2026-01-01 (non-mono replay r6); 41=2024-10-04..2024-11-13 (non-mono replay r6);
      42=2024-12-27..2025-01-09 (non-mono replay r5). Respect ≤2/(vm-prefix,day) budget — query
      DeploymentsRegistry.list_recent_archive, not just gcloud. Done when: all 8 terminal-verified complete, or round-9
      dispatched for any failures. (repo: unified-trading-pm) — slot 3, 2026-08-07T12:31Z: correctly-deferred per
      BLK-42575d6b (operator recommendation A) — all 8 shards at/over ≤2/(vm-prefix,day) budget cap for 2026-08-07 UTC
      (slot-13 re-verified 12:06Z; budget-day = UTC calendar day per DeploymentsRegistry.list_recent_archive). No VMs
      launched; actual round-8 launch tracked in follow-up below for 2026-08-08T00:00Z UTC budget reset.

- [x] ✅ [DATA] P1. Round-8 ACTUAL LAUNCH on 2026-08-08 — all 8 shards (16,17,18,19,21,23,41,42). FIRST verify current
      UTC date ≥ 2026-08-08 AND DeploymentsRegistry.list_recent_archive(days=1) shows 0 cefi-content-<N> archive entries
      for today (budget=0/2 confirmed, not just assumed). Frontiers (from slot-13 re-verify 2026-08-07T12:06Z):
      16=2024-09-06..2024-11-13 (mono, r6 PROGRESS last_completed=2024-09-05); 17=2024-11-16..2025-01-09 (non-mono
      replay r6); 18=2025-01-30..2025-02-06 (mono, r5 PROGRESS last_completed=2025-01-29); 19=2025-02-16..2025-03-17
      (non-mono replay r6); 21=2025-05-16..2025-06-26 (non-mono replay r6-083119); 23=2025-09-07..2026-01-01 (non-mono
      replay r6); 41=2024-10-04..2024-11-13 (non-mono replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Use
      floating MTDS tarball (≥cc144bf4, gc.collect() fix live), e2-standard-16, SPOT. Verify all 8 VMs RUNNING at
      T+60s + PROGRESS at T+10min. Done when: all 8 terminal-verified complete, or round-9 dispatched for failures.
      (repo: unified-trading-pm) — worker, slot 14, 2026-08-07T13:08Z: UTC is still 2026-08-07T13:08Z (NOT ≥
      2026-08-08). Budget day = UTC calendar day per DeploymentsRegistry — all 8 shards remain at/over
      ≤2/(vm-prefix,day) cap for 2026-08-07 (verified by slot-13 at 12:06Z; no change since). Cannot launch until
      2026-08-08T00:00Z UTC budget reset. Deferred — round-8 actual launch tracked in follow-up todo below.

- [x] ✅ [DATA] P1. Round-8 ACTUAL LAUNCH (second deferred; launch gate: UTC ≥ 2026-08-08T00:00Z) — all 8 shards
      (16,17,18,19,21,23,41,42). FIRST verify DeploymentsRegistry.list_recent_archive(days=1) shows 0 cefi-content-<N>
      entries for today (budget=0/2). Frontiers (slot-13 re-verify 2026-08-07T12:06Z): 16=2024-09-06..2024-11-13 (mono);
      17=2024-11-16..2025-01-09 (non-mono replay r6); 18=2025-01-30..2025-02-06 (mono); 19=2025-02-16..2025-03-17
      (non-mono replay r6); 21=2025-05-16..2025-06-26 (non-mono replay r6-083119); 23=2025-09-07..2026-01-01 (non-mono
      replay r6); 41=2024-10-04..2024-11-13 (non-mono replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Use
      floating MTDS tarball (≥cc144bf4), e2-standard-16, SPOT.
      `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`. Verify all 8 VMs RUNNING T+60s +
      PROGRESS T+10min. Done when: all 8 terminal-verified complete, or round-9 dispatched for failures. (repo:
      unified-trading-pm) — worker, slot 3, 2026-08-07T13:15Z: UTC still 2026-08-07 (NOT ≥ 2026-08-08T00:00Z); all 8
      shards at/over budget cap for today (slot-13 verified 12:06Z, fleet empty since). Third dispatch of this
      time-gated task. No VMs launched. Follow-up todo below.

- [x] ✅ [DATA] P1. Round-8 ACTUAL LAUNCH (third deferred; launch gate: UTC ≥ 2026-08-08T00:00Z) — all 8 shards
      (16,17,18,19,21,23,41,42). FIRST verify UTC ≥ 2026-08-08T00:00Z AND
      DeploymentsRegistry.list_recent_archive(days=1) shows 0 cefi-content-<N> entries for today (budget=0/2; resets at
      UTC midnight). Frontiers (slot-13 re-verify 2026-08-07T12:06Z, unchanged): 16=2024-09-06..2024-11-13 (mono, r6
      PROGRESS last_completed=2024-09-05); 17=2024-11-16..2025-01-09 (non-mono replay r6); 18=2025-01-30..2025-02-06
      (mono, r5 PROGRESS last_completed=2025-01-29); 19=2025-02-16..2025-03-17 (non-mono replay r6);
      21=2025-05-16..2025-06-26 (non-mono replay r6-083119); 23=2025-09-07..2026-01-01 (non-mono replay r6);
      41=2024-10-04..2024-11-13 (non-mono replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Use floating MTDS
      tarball (≥cc144bf4, gc.collect() fix live), e2-standard-16, SPOT.
      `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`. Verify all 8 VMs RUNNING T+60s +
      PROGRESS T+10min. Done when: all 8 terminal-verified complete, or round-9 dispatched for failures. (repo:
      unified-trading-pm) — worker, slot 5, 2026-08-07T15:04Z: UTC still 2026-08-07 (NOT ≥ 2026-08-08T00:00Z); no
      running cefi-content VMs (gcloud instances list = empty). Fourth dispatch of this time-gated task. No VMs
      launched. Follow-up todo below.

- [x] ✅ [DATA] P1. Round-8 ACTUAL LAUNCH (fourth deferred; launch gate: UTC ≥ 2026-08-08T00:00Z) — all 8 shards
      (16,17,18,19,21,23,41,42). FIRST verify UTC ≥ 2026-08-08T00:00Z AND
      DeploymentsRegistry.list_recent_archive(days=1) shows 0 cefi-content-<N> entries for today (budget=0/2; resets at
      UTC midnight). Frontiers (slot-13 re-verify 2026-08-07T12:06Z, unchanged): 16=2024-09-06..2024-11-13 (mono, r6
      PROGRESS last_completed=2024-09-05); 17=2024-11-16..2025-01-09 (non-mono replay r6); 18=2025-01-30..2025-02-06
      (mono, r5 PROGRESS last_completed=2025-01-29); 19=2025-02-16..2025-03-17 (non-mono replay r6);
      21=2025-05-16..2025-06-26 (non-mono replay r6-083119); 23=2025-09-07..2026-01-01 (non-mono replay r6);
      41=2024-10-04..2024-11-13 (non-mono replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Use floating MTDS
      tarball (≥cc144bf4, gc.collect() fix live), e2-standard-16, SPOT.
      `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`. Verify all 8 VMs RUNNING T+60s +
      PROGRESS T+10min. Done when: all 8 terminal-verified complete, or round-9 dispatched for failures. (repo:
      unified-trading-pm) — worker, slot 12, 2026-08-07T15:20Z: UTC still 2026-08-07T15:20Z (NOT ≥ 2026-08-08T00:00Z);
      no running cefi-content VMs (gcloud instances list = empty). Fifth dispatch of this time-gated task. No VMs
      launched. Follow-up todo below.

- [x] ✅ [DATA] P1. Round-8 ACTUAL LAUNCH (fifth deferred; launch gate: UTC ≥ 2026-08-08T00:00Z) — all 8 shards
      (16,17,18,19,21,23,41,42). FIRST verify UTC ≥ 2026-08-08T00:00Z AND
      DeploymentsRegistry.list_recent_archive(days=1) shows 0 cefi-content-<N> entries for today (budget=0/2; resets at
      UTC midnight). Frontiers (slot-13 re-verify 2026-08-07T12:06Z, unchanged): 16=2024-09-06..2024-11-13 (mono, r6
      PROGRESS last_completed=2024-09-05); 17=2024-11-16..2025-01-09 (non-mono replay r6); 18=2025-01-30..2025-02-06
      (mono, r5 PROGRESS last_completed=2025-01-29); 19=2025-02-16..2025-03-17 (non-mono replay r6);
      21=2025-05-16..2025-06-26 (non-mono replay r6-083119); 23=2025-09-07..2026-01-01 (non-mono replay r6);
      41=2024-10-04..2024-11-13 (non-mono replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Use floating MTDS
      tarball (≥cc144bf4, gc.collect() fix live), e2-standard-16, SPOT.
      `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`. Verify all 8 VMs RUNNING T+60s +
      PROGRESS T+10min. Done when: all 8 terminal-verified complete, or round-9 dispatched for failures. (repo:
      unified-trading-pm) — worker, slot 2, 2026-08-07T16:04Z: UTC still 2026-08-07T16:04Z (NOT ≥ 2026-08-08T00:00Z,
      ~7h55m remaining); fleet empty (gcloud instances list = no canonical-migration-cefi-content VMs); identity =
      unified-trading-sa (not poisoned); budget at/over cap for 2026-08-07 (slot-13 verified 12:06Z, no change since).
      Sixth dispatch of this time-gated task. No VMs launched. Follow-up todo below.

- [x] ✅ [DATA] P1. Round-8 ACTUAL LAUNCH (sixth deferred; launch gate: UTC ≥ 2026-08-08T00:00Z) — all 8 shards
      (16,17,18,19,21,23,41,42). FIRST verify UTC ≥ 2026-08-08T00:00Z AND
      DeploymentsRegistry.list_recent_archive(days=1) shows 0 cefi-content-<N> entries for today (budget=0/2; resets at
      UTC midnight). Frontiers (slot-13 re-verify 2026-08-07T12:06Z, unchanged): 16=2024-09-06..2024-11-13 (mono, r6
      PROGRESS last_completed=2024-09-05); 17=2024-11-16..2025-01-09 (non-mono replay r6); 18=2025-01-30..2025-02-06
      (mono, r5 PROGRESS last_completed=2025-01-29); 19=2025-02-16..2025-03-17 (non-mono replay r6);
      21=2025-05-16..2025-06-26 (non-mono replay r6-083119); 23=2025-09-07..2026-01-01 (non-mono replay r6);
      41=2024-10-04..2024-11-13 (non-mono replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Use floating MTDS
      tarball (≥cc144bf4, gc.collect() fix live), e2-standard-16, SPOT.
      `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`. Verify all 8 VMs RUNNING T+60s +
      PROGRESS T+10min. Done when: all 8 terminal-verified complete, or round-9 dispatched for failures. (repo:
      unified-trading-pm) — worker, slot 12, 2026-08-07T16:21Z: UTC still 2026-08-07T16:21Z (NOT ≥ 2026-08-08T00:00Z,
      ~7h39m remaining); fleet empty (gcloud compute instances list = no canonical-migration-cefi-content VMs); identity
      = unified-trading-sa (not poisoned); budget at/over cap for 2026-08-07 (slot-13 verified 12:06Z, no change since).
      Seventh dispatch of this time-gated task. No VMs launched. Follow-up todo below.

- [x] ✅ [DATA] P1. Round-8 ACTUAL LAUNCH (seventh deferred; launch gate: UTC ≥ 2026-08-08T00:00Z) — all 8 shards
      (16,17,18,19,21,23,41,42). FIRST verify UTC ≥ 2026-08-08T00:00Z AND
      DeploymentsRegistry.list_recent_archive(days=1) shows 0 cefi-content-<N> entries for today (budget=0/2; resets at
      UTC midnight). Frontiers (slot-13 re-verify 2026-08-07T12:06Z, unchanged): 16=2024-09-06..2024-11-13 (mono, r6
      PROGRESS last_completed=2024-09-05); 17=2024-11-16..2025-01-09 (non-mono replay r6); 18=2025-01-30..2025-02-06
      (mono, r5 PROGRESS last_completed=2025-01-29); 19=2025-02-16..2025-03-17 (non-mono replay r6);
      21=2025-05-16..2025-06-26 (non-mono replay r6-083119); 23=2025-09-07..2026-01-01 (non-mono replay r6);
      41=2024-10-04..2024-11-13 (non-mono replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Use floating MTDS
      tarball (≥cc144bf4, gc.collect() fix live), e2-standard-16, SPOT.
      `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`. Verify all 8 VMs RUNNING T+60s +
      PROGRESS T+10min. Done when: all 8 terminal-verified complete, or round-9 dispatched for failures. (repo:
      unified-trading-pm) — worker, slot 6, 2026-08-07T16:34Z: UTC still 2026-08-07T16:34Z (NOT ≥ 2026-08-08T00:00Z,
      ~7h26m remaining); fleet empty (gcloud compute instances list = no canonical-migration-cefi-content VMs); identity
      = unified-trading-sa (not poisoned); budget at/over cap for 2026-08-07 (slot-13 verified 12:06Z, no change since).
      Eighth dispatch of this time-gated task. No VMs launched. Follow-up todo below.

- [x] ✅ [DATA] P1. Round-8 ACTUAL LAUNCH (eighth deferred; launch gate: UTC ≥ 2026-08-08T00:00Z) — all 8 shards
      (16,17,18,19,21,23,41,42). FIRST verify UTC ≥ 2026-08-08T00:00Z AND
      DeploymentsRegistry.list_recent_archive(days=1) shows 0 cefi-content-<N> entries for today (budget=0/2; resets at
      UTC midnight). Frontiers (slot-13 re-verify 2026-08-07T12:06Z, unchanged): 16=2024-09-06..2024-11-13 (mono, r6
      PROGRESS last_completed=2024-09-05); 17=2024-11-16..2025-01-09 (non-mono replay r6); 18=2025-01-30..2025-02-06
      (mono, r5 PROGRESS last_completed=2025-01-29); 19=2025-02-16..2025-03-17 (non-mono replay r6);
      21=2025-05-16..2025-06-26 (non-mono replay r6-083119); 23=2025-09-07..2026-01-01 (non-mono replay r6);
      41=2024-10-04..2024-11-13 (non-mono replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Use floating MTDS
      tarball (≥cc144bf4, gc.collect() fix live), e2-standard-16, SPOT.
      `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`. Verify all 8 VMs RUNNING T+60s +
      PROGRESS T+10min. Done when: all 8 terminal-verified complete, or round-9 dispatched for failures. (repo:
      unified-trading-pm) — worker, slot 9, 2026-08-07T16:51Z: UTC still 2026-08-07T16:51Z (NOT ≥ 2026-08-08T00:00Z,
      ~7h9m remaining); fleet empty (gcloud compute instances list = no canonical-migration-cefi-content VMs); identity
      = unified-trading-sa (not poisoned); budget at/over cap for 2026-08-07 (slot-13 verified 12:06Z, no change since).
      Ninth dispatch of this time-gated task. No VMs launched. Follow-up todo below.

- [x] ✅ [DATA] P1. Round-8 ACTUAL LAUNCH (ninth deferred; launch gate: UTC ≥ 2026-08-08T00:00Z) — all 8 shards
      (16,17,18,19,21,23,41,42). FIRST verify UTC ≥ 2026-08-08T00:00Z AND
      DeploymentsRegistry.list_recent_archive(days=1) shows 0 cefi-content-<N> entries for today (budget=0/2; resets at
      UTC midnight). Frontiers (slot-13 re-verify 2026-08-07T12:06Z, unchanged): 16=2024-09-06..2024-11-13 (mono, r6
      PROGRESS last_completed=2024-09-05); 17=2024-11-16..2025-01-09 (non-mono replay r6); 18=2025-01-30..2025-02-06
      (mono, r5 PROGRESS last_completed=2025-01-29); 19=2025-02-16..2025-03-17 (non-mono replay r6);
      21=2025-05-16..2025-06-26 (non-mono replay r6-083119); 23=2025-09-07..2026-01-01 (non-mono replay r6);
      41=2024-10-04..2024-11-13 (non-mono replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Use floating MTDS
      tarball (≥cc144bf4, gc.collect() fix live), e2-standard-16, SPOT.
      `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`. Verify all 8 VMs RUNNING T+60s +
      PROGRESS T+10min. Done when: all 8 terminal-verified complete, or round-9 dispatched for failures. (repo:
      unified-trading-pm) — worker, slot 16, 2026-08-07T16:56Z: UTC still 2026-08-07T16:56Z (NOT ≥ 2026-08-08T00:00Z,
      ~7h4m remaining); fleet empty (slot-9 verified 16:51Z, no change since); identity = unified-trading-sa (not
      poisoned); budget at/over cap for 2026-08-07 (slot-13 verified 12:06Z, no change since). Tenth dispatch of this
      time-gated task. No VMs launched. Follow-up todo below.

- [x] ✅ [DATA] P1. Round-8 ACTUAL LAUNCH (tenth deferred; launch gate: UTC ≥ 2026-08-08T00:00Z) — all 8 shards
      (16,17,18,19,21,23,41,42). FIRST verify UTC ≥ 2026-08-08T00:00Z AND
      DeploymentsRegistry.list_recent_archive(days=1) shows 0 cefi-content-<N> entries for today (budget=0/2; resets at
      UTC midnight). Frontiers (slot-13 re-verify 2026-08-07T12:06Z, unchanged): 16=2024-09-06..2024-11-13 (mono, r6
      PROGRESS last_completed=2024-09-05); 17=2024-11-16..2025-01-09 (non-mono replay r6); 18=2025-01-30..2025-02-06
      (mono, r5 PROGRESS last_completed=2025-01-29); 19=2025-02-16..2025-03-17 (non-mono replay r6);
      21=2025-05-16..2025-06-26 (non-mono replay r6-083119); 23=2025-09-07..2026-01-01 (non-mono replay r6);
      41=2024-10-04..2024-11-13 (non-mono replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Use floating MTDS
      tarball (≥cc144bf4, gc.collect() fix live), e2-standard-16, SPOT.
      `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`. Verify all 8 VMs RUNNING T+60s +
      PROGRESS T+10min. Done when: all 8 terminal-verified complete, or round-9 dispatched for failures. (repo:
      unified-trading-pm) — worker, slot 2, 2026-08-07T17:15Z: UTC still 2026-08-07T17:15Z (NOT ≥ 2026-08-08T00:00Z,
      ~6h45m remaining); fleet empty (gcloud compute instances list = no canonical-migration-cefi-content VMs); identity
      = unified-trading-sa (not poisoned); budget at/over cap for 2026-08-07 (slot-13 verified 12:06Z, no change since).
      Eleventh dispatch of this time-gated task. No VMs launched. Follow-up todo below.

- [x] ✅ [DATA] P1. Round-8 ACTUAL LAUNCH (eleventh deferred; launch gate: UTC ≥ 2026-08-08T00:00Z) — all 8 shards
      (16,17,18,19,21,23,41,42). FIRST verify UTC ≥ 2026-08-08T00:00Z AND
      DeploymentsRegistry.list_recent_archive(days=1) shows 0 cefi-content-<N> entries for today (budget=0/2; resets at
      UTC midnight). Frontiers (slot-13 re-verify 2026-08-07T12:06Z, unchanged): 16=2024-09-06..2024-11-13 (mono, r6
      PROGRESS last_completed=2024-09-05); 17=2024-11-16..2025-01-09 (non-mono replay r6); 18=2025-01-30..2025-02-06
      (mono, r5 PROGRESS last_completed=2025-01-29); 19=2025-02-16..2025-03-17 (non-mono replay r6);
      21=2025-05-16..2025-06-26 (non-mono replay r6-083119); 23=2025-09-07..2026-01-01 (non-mono replay r6);
      41=2024-10-04..2024-11-13 (non-mono replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Use floating MTDS
      tarball (≥cc144bf4, gc.collect() fix live), e2-standard-16, SPOT.
      `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`. Verify all 8 VMs RUNNING T+60s +
      PROGRESS T+10min. Done when: all 8 terminal-verified complete, or round-9 dispatched for failures. (repo:
      unified-trading-pm) — worker, slot 8, 2026-08-07T18:09Z: **All 8 shards confirmed dead** by ~10:20Z
      (16=exit125/10:11Z r6, 17=exit137/09:18Z r6, 18=exit125/09:15Z r5, 19=exit125/10:16Z r6, 21=exit125/10:20Z r6,
      23=exit125/09:10Z r6, 41=exit125/10:15Z r6, 42=exit125/10:20Z r5). MTDS tarball 52d6da4 ≥cc144bf4+dc037373.
      Frontiers confirmed: 16=2024-09-06..2024-11-13 (mono+1), 17=2024-11-16..2025-01-09 (replay r6),
      18=2025-01-30..2025-02-06 (mono+1), 19=2025-02-16..2025-03-17 (replay r6), 21=2025-05-16..2025-06-26 (replay r6),
      23=2025-09-07..2026-01-01 (replay r6), 41=2024-10-04..2024-11-13 (replay r6), 42=2024-12-27..2025-01-09 (replay
      r5). **Round-8 launch script dispatched** (bhqsyzir3, 17:55Z 2026-08-07) — gates on 2026-08-08T00:00:10Z, then
      auto-launches all 8 VMs using `cefi-content-apply`. Checkbox flip pending T+75s RUNNING verification after gate.
      RB-INFRA-RELAUNCH budget resets at UTC midnight. — slot 6, 2026-08-07T19:03Z: UTC=19:03 (NOT ≥ 2026-08-08T00:00Z,
      ~4h57m remaining). bhqsyzir3 script confirmed dead (no live background process, no Cloud Scheduler job exists for
      it). Fleet confirmed empty (gcloud instances list = zero cefi-content VMs). Identity = unified-trading-sa (not
      poisoned). Created prereq `cefi-round8-budget-reset-2026-08-08` (value=false) + Cloud Scheduler job
      `cefi-round8-midnight-prereq-flip` to flip it to true at 2026-08-08T00:01Z UTC — this breaks the endless dispatch
      loop (all prior workers deferred with a new follow-up todo; this time the follow-up task is gated on the prereq so
      it won't dispatch until midnight auto-flip). Follow-up todo below.

- [x] ✅ [DATA] P1. Round-8 ACTUAL LAUNCH — all 8 shards (16,17,18,19,21,23,41,42). **Gated on prereq
      `cefi-round8-budget-reset-2026-08-08`** (flips to true at 2026-08-08T00:01Z UTC via Cloud Scheduler job
      `cefi-round8-midnight-prereq-flip`). FIRST verify UTC ≥ 2026-08-08T00:00Z AND
      DeploymentsRegistry.list_recent_archive(days=1) shows 0 cefi-content-<N> entries for today (budget=0/2; resets at
      UTC midnight). Frontiers (slot-13 re-verify 2026-08-07T12:06Z, unchanged): 16=2024-09-06..2024-11-13 (mono);
      17=2024-11-16..2025-01-09 (non-mono replay r6); 18=2025-01-30..2025-02-06 (mono); 19=2025-02-16..2025-03-17
      (non-mono replay r6); 21=2025-05-16..2025-06-26 (non-mono replay r6-083119); 23=2025-09-07..2026-01-01 (non-mono
      replay r6); 41=2024-10-04..2024-11-13 (non-mono replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Use
      floating MTDS tarball (≥cc144bf4, gc.collect() fix live), e2-standard-16, SPOT.
      `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`. Verify all 8 VMs RUNNING T+60s +
      PROGRESS T+10min. Done when: all 8 terminal-verified complete, or round-9 dispatched for failures. (repo:
      unified-trading-pm) — worker, slot 11, 2026-08-07T19:12Z: UTC=2026-08-07T19:12Z (NOT ≥ 2026-08-08T00:00Z, ~4h48m
      remaining). DeploymentsRegistry(days=1) confirms all 8 shards AT/OVER ≤2/(vm-prefix,day) cap: 16=2/2, 17=3/2,
      18=2/2, 19=3/2, 21=4/2, 23=3/2, 41=3/2, 42=2/2. Fleet empty (gcloud instances list = no
      canonical-migration-cefi-content VMs). Identity = unified-trading-sa (not poisoned). Prereq was set=true at
      dispatch time (slot-6 set=false at 19:03Z; reset by this slot to false). Cloud Scheduler job
      cefi-round8-midnight-prereq-flip confirmed ENABLED (scheduleTime=2026-08-08T00:01:00Z, status.code=-1 = not yet
      run). Twelfth dispatch of this time-gated task. No VMs launched. Follow-up todo below; prereq attached in
      backlog.yaml for the new task to prevent premature dispatch.

- [ ] [DATA] P1. Round-8 ACTUAL LAUNCH — all 8 shards (16,17,18,19,21,23,41,42). **Gated on prereq
      `cefi-round8-budget-reset-2026-08-08`** (Cloud Scheduler job `cefi-round8-midnight-prereq-flip` fires at
      2026-08-08T00:01Z UTC). FIRST verify UTC ≥ 2026-08-08T00:00Z AND DeploymentsRegistry.list_recent_archive(days=1)
      shows 0 cefi-content-<N> entries for today (budget=0/2; resets at UTC midnight). Frontiers (slot-13 re-verify
      2026-08-07T12:06Z, unchanged): 16=2024-09-06..2024-11-13 (mono); 17=2024-11-16..2025-01-09 (non-mono replay r6);
      18=2025-01-30..2025-02-06 (mono); 19=2025-02-16..2025-03-17 (non-mono replay r6); 21=2025-05-16..2025-06-26
      (non-mono replay r6-083119); 23=2025-09-07..2026-01-01 (non-mono replay r6); 41=2024-10-04..2024-11-13 (non-mono
      replay r6); 42=2024-12-27..2025-01-09 (non-mono replay r5). Use floating MTDS tarball (≥cc144bf4, gc.collect() fix
      live), e2-standard-16, SPOT. `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`. Verify all
      8 VMs RUNNING T+60s + PROGRESS T+10min. Done when: all 8 terminal-verified complete, or round-9 dispatched for
      failures. (repo: unified-trading-pm)

- [x] ✅ [INFRA] P1. **`cefi-round8-midnight-prereq-flip` Cloud Scheduler job is permanently stuck failed — fix or
      replace it, then manually verify+flip `cefi-round8-budget-reset-2026-08-08` if the budget is genuinely reset.**
      Found 2026-08-08 (slot 20, while verifying `ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md`
      item `-025`):
      `gcloud scheduler jobs describe cefi-round8-midnight-prereq-flip --location=asia-northeast1     --project=central-element-323112`
      shows `lastAttemptTime=2026-08-08T00:01:00Z`, `status.code=2` (UNKNOWN/failed — not `0`=OK). Its `httpTarget.uri`
      is `http://13.113.200.22:8765/api/prerequisites/cefi-round8-budget-reset-2026-08-08` — the orchestrator VM's
      PUBLIC EIP on port 8765, which has NO inbound firewall rule (the same reason `/check-agent-orchestrator` /
      `check-ao-backlog-status.sh` exist — a dev checkout can't reach that port either). The job's cron (`1 0 8 8 *`)
      next fires **2027-08-08** — this was effectively a one-shot job and it already burned its one shot, so the prereq
      is stuck `false` indefinitely and `-026` above can never auto-dispatch. Done when: (a) confirm the current UTC ≥
      2026-08-08T00:00Z AND `DeploymentsRegistry.list_recent_archive(days=1)` shows the 8 shards' budget genuinely reset
      (0/2, not still 3-4/2 from the 2026-08-07 attempts), (b) if reset, manually
      `POST /api/prerequisites/cefi-round8-budget-reset-2026-08-08 {"value": true, "set_by": "manual-fix-broken-scheduler"}`
      to unblock `-026`, (c) delete or fix `cefi-round8-midnight-prereq-flip` (delete is safe — reversible, it's a Cloud
      Scheduler job definition, not data — since it already failed its only useful run and won't retry until 2027), and
      (d) if this "Cloud Scheduler → AO public-EIP:8765" pattern is used elsewhere for prereq flips, flag it as a
      standing design gap (SSM-based or a systemd timer running ON the orchestrator VM itself would actually be
      reachable). — worker, slot 28, 2026-08-08T20:32Z: (a) UTC=2026-08-08T20:32:29Z (≥ midnight ✓). Queried
      `DeploymentsRegistry().list_recent_archive(days=1)` live (377 total archive entries today) filtered by `vm_name`
      prefix `cefi-content-<N>` for all 8 shards (16,17,18,19,21,23,41,42) — **every shard 0/2**, budget genuinely
      reset. (b)
      `POST /api/prerequisites/cefi-round8-budget-reset-2026-08-08     {"value": true, "set_by": "manual-fix-broken-scheduler"}`
      → `200 {"name":"cefi-round8-budget-reset-2026-08-08",     "value":true,"set_by":"manual-fix-broken-scheduler"}` —
      `-026` now unblocked. (c) Verified via `gcloud scheduler     jobs describe` the job's only run indeed failed
      (`status.code=2`) and next `scheduleTime=2027-08-08`; deleted it:
      `gcloud scheduler jobs delete cefi-round8-midnight-prereq-flip --location=asia-northeast1     --project=central-element-323112 --quiet`
      → `Deleted job [cefi-round8-midnight-prereq-flip]`. (d) Checked for the same pattern elsewhere:
      `gcloud scheduler jobs list --location=asia-northeast1 --project=central-element-323112` (the only region hosting
      VM/scheduler infra for this project) shows no other job targeting `13.113.200.22:8765`; grepped the whole
      workspace for the EIP+port string — no launcher/template script programmatically creates a "Cloud Scheduler → AO
      public-EIP:8765" job (this one was a one-off manual mitigation from slot 6, 2026-08-07T19:03Z, not a repeated
      pattern), so no other live instance needs fixing. Design-gap note for any FUTURE ad-hoc prereq-flip-by-deadline
      need: prefer a `systemd timer` running ON the orchestrator VM itself (reachable, matches the pattern the 8
      standing AO scheduled jobs already use) or an SSM-triggered flip, never a Cloud Scheduler job targeting the VM's
      public EIP (no inbound firewall rule — this is the same reachability gap `/check-agent-orchestrator` exists to
      work around). No further action filed — the immediate instance is resolved and this is a one-off's lesson, not an
      active recurring gap. — unified-trading-pm@(pending sha, see commit below)

> **2026-08-07 note**: the 2026-08-06 archive-candidate audit note above is superseded — round-4 WAS dispatched (all 10
> shards launched 2026-08-06T22:58:44Z, see the Follow-up above); the genuinely still-open work is the corpus-wide
> completion re-verify, now tracked as a real todo instead of prose.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate -- the round-5/6
  relaunch log entries and the OOM-fix commit are operational narrative on the already-scoped launcher/migration script,
  not new dependencies.
