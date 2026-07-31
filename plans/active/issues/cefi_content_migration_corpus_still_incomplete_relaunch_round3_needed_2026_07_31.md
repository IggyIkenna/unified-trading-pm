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
- [ ] [OPERATOR] P1. **Shards 16, 17, 21, 41 are now over `RB-INFRA-RELAUNCH`'s `≤2/(vm-prefix,day)` budget** (queried
      live via `DeploymentsRegistry.list_recent_archive(days=1)` 2026-07-31T13:35Z: shard 16=2, shard 21=2 archived
      today — AT cap; shard 17=3, shard 41=3 archived today — OVER cap) and were correctly NOT relaunched this round.
      All four died again on their most recent (pre-round-3) attempt showing the SAME symptom — repeated
      `WARNING No progress in the last poll window — N files still outstanding (possible wedged worker)` immediately
      before death, despite already running on `e2-standard-16` with both the pyarrow-pool-release fix
      (`market-tick-data-service@9f4098b1`) and the stall-timeout fix (`@55d051bd`) live. Shard 17 in particular has now
      died on its 3rd post-fix attempt (`-050700`, per the parent doc's own DP-VM-003 agt-ad6632 finding:
      `host_metrics_window.mem_pct` climbed to 91.4% before the reaper found it gone) — the two shipped fixes close a
      wedge/freeze class and a slow leak respectively, but something is still exhausting this specific VM's headroom on
      these 4 large shards specifically. Needs an operator decision before a 4th relaunch attempt today: (a) bump
      `MACHINE_TYPE` further for just these 4 shards (e.g. `e2-standard-32`) to test whether it's a raw-memory ceiling,
      (b) cross-reference against the sibling
      `cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md` root-cause investigation
      (same symptom class — worth checking whether that doc's fix, once shipped, closes this too before spending more
      relaunch budget), or (c) wait for tomorrow's budget reset and relaunch cleanly. **Done when**: operator picks
      (a)/(b)/(c) and shards 16/17/21/41 get their round-4 relaunch (or are confirmed covered by the sibling doc's fix).

      **Corroborating signal 2026-07-31 13:56Z (review agt-8ce066, gcloud-verified — a DIFFERENT shape than the
                  same-shard-memory-death pattern above):** shards 43 + 44, freshly relaunched this round at 13:39:58Z / 13:40:22Z,
                  were BOTH preempted at 13:51:37Z / 13:51:38Z — ~12 min after launch and only ~2 min after their own T+10 alive-check
                  (13:49:30Z), confirmed via `gcloud compute operations list` `compute.instances.preempted` (ops
                  `systemevent-1785505897347-…` / `systemevent-1785505907671-…`), not inference; 11/13 relaunched shards remain
                  running. A FRESH launch dying fast points to SPOT-capacity pressure in `asia-northeast1-c` today (fleet-wide), NOT a
                  shard-specific memory/data issue — so the operator decision should ALSO weigh (d) a zone/capacity check or a
                  one-shot `--on-demand` fallback (env `ON_DEMAND=true`) for the next relaunch, not only the memory-ceiling options
                  (a)/(b). Non-blocking: 43/44 are idempotent SPOT shards and should re-run cleanly on round-4.

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
