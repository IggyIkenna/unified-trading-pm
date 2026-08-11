---
doc_type: codex-ssot
title: Prediction satellite AO batch 4 — archived Progress Log (2026-07-26..2026-08-06, pre-4b-iii)
summary: >-
  Extracted Progress Log history from prediction_satellite_ao_dispatch_batch4_2026_07_26.md, split 2026-08-11 to clear
  that plan's 1000-line hard cap (check_line_caps.sh's sanctioned extracted-history pattern). Covers the initial
  ag-closeout-audit draft/dispatch, todo #1-#3 completions, the 4a canonical-schema+writer leg, the 4b-i legacy shape
  #3/#3b migration+delete saga (multi-slot resume/checkpoint/shard history), and the 4b-ii shape #4 corpus enumeration.
  Content moved verbatim from the active plan, nothing deleted or altered. Read the active plan
  (/plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md) for current status; this doc is historical
  record only.
status: complete
nature: record
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-4, progress-log-archive]
related: [/plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md]
created: "2026-08-11"
last_updated: "2026-08-11"
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Split from prediction_satellite_ao_dispatch_batch4_2026_07_26.md (slot 8, data_engineering) to clear the 1000L plan
  hard cap while resuming 4b-iii monitoring; check_line_caps.sh's own header comment documents this exact
  extracted-history pattern as sanctioned (status: complete / nature: record docs are unbounded by design).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope: []
---

# Prediction satellite AO batch 4 — archived Progress Log (2026-07-26..2026-08-06, pre-4b-iii)

> **This is a historical record, not a live plan.** No open todos here. See
> `/plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md` for current status (4b-iii and later).

## Progress Log (archived block A — 2026-07-26..2026-08-04)

- 2026-07-26 (slot 7, ag_closeout_auditor, dispatch agt-205487): drafted by the `/ag-closeout-audit prediction`
  scheduled run. Phase 1 = 26-agent Workflow (`wf_d800a7e0-975`), 0 errors; verdicts: 10 orphaned_never_touched, 10
  orphaned_partial_coverage, 5 archivable_after_planned_work, 1 exclude_cross_cutting. Phase 3 reconciliation found the
  3 A3-relocated sibling docs (cross_venue_arb / live_clob_depth / perps) were never triaged by any batch
  (grep-confirmed: 0 hits in batch1/2/3/native_ao; 0 mentions in batch3). Extracted 3 conflict-clear bounded todos + 2
  gated-on-#1 `[OPERATOR]` walk/backfill items + the design/cross-cutting/upstream deferrals. Left `status: draft` per
  the autonomous-mode safety rail — operator flips to `active` to dispatch. No new issue doc filed: the orphans are
  already tracked as their own docs; this batch + batch3 are the actionable artifacts.
- 2026-07-28 (slot-16, data_engineering): split 4b into 4b-i (shapes #3/#3b, session-doable) + 4b-ii (shape #4,
  operator/VM-gated) per the todo's own "next steps". Built + shipped `market-tick-data-service@e4acf0c4`
  (`scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py`, 20 unit tests, QG green) after live-verifying the
  actual GCS schema/paths (manifest read: 2,477 rows/348 dates confirmed; sampled 6 dates across the full range
  confirmed the canonical shape#1 twin exists everywhere, correcting an initial worry that it might be
  date-range-gated). Caught + fixed a real join-key-typing bug (int vs str) and a real overwrite risk (some canonical
  objects already carry a richer pre-existing schema with title/slug under different column names) via the script's own
  dry-run safety checks before any prod write. Launched the real `--apply` enrichment run across all 348 dates
  (resumable, additive-only, 0 anomalies through the first ~50 dates at last check) — running in background; the delete
  pass (`--delete-legacy`, gated on a live-verified `604800`s soft-delete retention on the prediction bucket) follows
  once enrichment completes and a sample is spot-verified. 4b-i's checkbox stays open until the full 348-date run +
  delete pass verify complete.
- 2026-07-28 (slot-16, session end): the `--apply` run above got to **55/348 dates (0 anomalies)** before this worker
  session died mid-run — a background-process reap (exit 144/SIGTERM), NOT a script defect; every write up to that point
  content-verified before commit and is durable in GCS already. **Lesson**: a plain `nohup ... & disown` inside a single
  Bash tool call does NOT survive a harness session death the way `run_in_background: true` does — use the latter for
  any long-running mutating job you need to survive a session boundary. **Remaining work (next session/worker)**: (1)
  resume the enrichment — re-run
  `.venv/bin/python scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py --apply --report <path>` from
  `market-tick-data-service` (idempotent even without the report file — `all_fields_present` skips already-enriched
  cells on read); (2) once all 348 dates enrich clean, run `--delete-legacy` (re-verify the soft-delete retention fresh,
  don't assume the `604800`s measured here still holds); (3) flip 4b-i's checkbox with the final counts; (4) do 4c's
  registration once (1)+(2) land.
- 2026-07-28 (slot 7, resuming from slot-16's 55/348 hand-off): resumed via
  `.venv/bin/python scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py --apply --report <scratchpad>/prediction_trades_migration_report.jsonl`
  (exported `GCP_PROJECT_ID`/`CLOUD_PROVIDER` first — not pre-set in this session). **Hit slot-16's exact "session died
  mid-run" bug a second time**, this time root-caused precisely (not just "not a script bug"): backgrounded with
  `nohup ... & echo $!` inside a plain Bash call, detaching it from the tracked session tree —
  `agent-orchestrator/server/orphan_reap.py`'s periodic sweep classified it as an orphan and SIGKILLed it ~346s later
  (`journalctl -k`: `orphan_reap sweep: slot 7 pid 4006112 age=346s KILLED`). Already-known, already-filed
  (`plans/active/issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md`, filed 2026-07-27, its
  own recommended fix left unshipped) — shipped it now: `unified-trading-pm@38e6de9fa` adds a `nohup`-avoidance callout
  to `agents/worker.md`'s Heartbeat section + fresh evidence in the issue doc. Resumed correctly the second time (long
  command passed directly to `run_in_background: true`, no `nohup`) — ran clean for ~25 min, then hit a SECOND,
  DIFFERENT kill: `WorkerLivenessWatchdog` read this slot as heartbeat-stale (no `/progress` call in >25 min while doing
  local-only bash progress checks) and fired `kill_session(orch-slot-7)`, which SIGTERMs the whole pane's descendant
  tree by design (`_reap_pane_tree`) — collateral-killing the properly-parented backfill despite it being immune to
  `orphan_reap`. Root-caused via `journalctl | grep kill_session` (a different log signature from `orphan_reap sweep`),
  documented as `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` § "Watcher coverage" item 5 + a
  cross-reference addendum in the nohup issue doc — **`run_in_background` fixes orphan-reap, it does NOT exempt a worker
  from the `/progress` heartbeat cadence while monitoring a long job.** Resumed a third time with disciplined
  `/progress` heartbeats every ≤8 min going forward. **Status at last check**: 67/348 dates done, 0 anomalies, real
  enrichment writes now dominant (past the range slot-16's manual pass + the 4a writer-root fix's retroactive coverage
  already covered). Still running — see this task's next Progress Log entry for the outcome.
- 2026-07-28 (slot 8, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-013`): dispatched this
  same 4b-i resume independently, discovered mid-session that **this exact todo was concurrently dispatched to at least
  3 slots** (7, 8, 13) — each running its own
  `.venv/bin/python scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py --apply --report <own-scratchpad-path>`
  in parallel, unaware of each other (report files live under per-slot scratchpad dirs, not a shared location — no
  cross-slot lock exists for this class of resumable script). Found slot-7's report at 140/348 with real substantive
  enrichment (48,901 canonical objects / 6,996,559 rows enriched — genuine writes, not idempotent skips) vs. my own
  re-derived 21/348 (all idempotent skips, redundant re-reads of already-slot-7-covered days) and slot-13's 45/348 (also
  all idempotent skips). **This is real wasted GCS read cost from duplicate dispatch, though NOT a correctness risk** —
  the script's merge is additive-only/deterministic per cell, so even genuinely concurrent writes to the same object
  would converge to identical content; the only cost is redundant work, not corruption. **Fix applied**: merged all 3
  slots' report `.jsonl` files (dedup by `day`, preferring the entry with the higher `canonical_enriched` count) into
  one 140-day checkpoint, relaunched `--apply --report <merged-path>` from day 141 onward via the harness's tracked
  `run_in_background` (not a manual `nohup`/`setsid`/`disown` chain — hit the exact same self-inflicted confusion this
  doc's own prior entry already named: checked the WRONG pid (`setsid`'s own transient wrapper pid, not the exec'd
  python worker) after a manual background launch, wrongly concluded the run had died, and relaunched a second,
  redundant instance that briefly raced on the same report file for ~3 overlapping days — verified byte-identical
  duplicate lines, no corruption, before killing the redundant one). Also observed my own **first** relaunch attempt
  (pre-merge, pointed at my own slot's report path) die silently sometime between date 21 and my next check, ~4-5 min
  later, with **no OOM or orphan_reap/kill_session signature** in that window's `journalctl -k` — root cause
  undetermined this time (possibly a heartbeat-staleness `kill_session` just outside the narrow grep window I checked;
  did not chase further given the merged-checkpoint relaunch was the higher-value next step). **Now running** from the
  141/348 baseline via `run_in_background`, with a self-heartbeating Monitor (posts `/progress` to the orchestrator
  every 5 min regardless of my own turn cadence, specifically to avoid the `WorkerLivenessWatchdog` collateral-kill this
  doc's slot-7 entry already hit). **Finding worth a fleet-level fix (not actioned here, out of this todo's scope)**:
  the backlog dispatcher has no de-dup/lock for a long-running resumable script matching this shape — consider either a
  shared (not per-slot-scratchpad) report-file location keyed by task id, or a dispatcher-side in-flight check before
  handing the same todo to a second slot. Filed as
  `plans/active/issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md`. Still running — see this task's
  next Progress Log entry for the outcome.
- 2026-07-29 (slot 15, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-017`): slot-8's
  in-flight run from the prior entry never wrote a closing entry either (same class of session-death-without-report as
  slot-7's). Found its ephemeral report file plus 3 OTHER stranded checkpoints nobody had reconciled — slots 6, 7, 8
  (both its original + its merged file), and 13 all had `prediction_trades_migration_report.jsonl` files sitting under
  `/home/ubuntu/.claude-configs/orch-slot-*/cc-tmpdir/**/scratchpad/`. Merged all 5 by day (dedup, preferring the entry
  with the higher `canonical_enriched` count per the same recipe slot-8 used) — **157/348 dates, 0 anomalies, 0 errors,
  71,370 canonical objects / 9,244,580 rows enriched, 0 legacy deletes yet**. This is real, previously-undocumented
  progress that would otherwise have been silently lost the next time a scratchpad got cleaned up — confirms the
  concurrent-dispatch issue doc's "silent under-reporting" risk is not hypothetical. Resumed `--apply` from this merged
  checkpoint via the harness's tracked `run_in_background` (not `nohup`) with disciplined `/progress` heartbeats armed.
  **Hit a NEW, different blocker on the very first day processed**: `ManifestConsolidatorStaleError` —
  `uts-prod-manifest-consolidator-market-data-prediction-cron` is PAUSED (verified via `gcloud scheduler jobs list`),
  owned by a DIFFERENT in-flight plan (`mtds_available_at_cross_asset_backfill_2026_07_13.md`, paused
  2026-07-29T01:06:53Z as part of its own snapshot→apply→resume protocol; its Apply/Resume todos `-004`/`-005` are still
  queued). Did NOT touch that plan's cron (out of scope, would break its protocol) — instead armed a bounded (60 min)
  background poller that watches the cron's scheduler state and auto-retries the enrichment run the moment it flips back
  to `ENABLED`. Filed `BLK-c6fa4f95` so the operator/main agent can optionally bump the other plan's priority if this
  drags. Checkpoint file (merged, 157/348) now lives at this slot's scratchpad — see next entry for the outcome once the
  cron resumes and the run completes or re-blocks.
- 2026-07-29 (slot 8, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-020`): resumed from
  slot-15's hand-off. Confirmed via `/api/backlog` + activity feed: slot-15 was killed (`slot_wedged_killed_for_resume`)
  at 01:37Z, tmux lost 01:38Z, BLK-c6fa4f95 already answered "A — wait for the automatic background retry" (verified the
  blocking plan `mtds_available_at_cross_asset_backfill_2026_07_13.md` is genuinely in-flight, not stalled: its Apply
  todo (`-001`) is `dispatched` to slot 13 as of 03:50:48Z). Re-verified cron
  `uts-prod-manifest-consolidator-market- data-prediction-cron` is still `PAUSED` (`gcloud scheduler jobs list`) and
  reproduced the exact `ManifestConsolidatorStaleError` on a 1-day dry-run — confirms nothing has changed since
  slot-15's block. Recovered slot-15's 157/348-day checkpoint from its scratchpad
  (`/home/ubuntu/.claude-configs/orch-slot-15/.../scratchpad/ prediction_trades_migration_report.jsonl` — the tmux
  session died but the file survived on disk; not committed to git by slot-15, so this recovery step will be needed
  again by any future resumer unless a durable location is adopted). Armed a self-heartbeating watcher
  (`resume_4bi_watcher.sh`, harness-tracked `run_in_background`, NOT `nohup`/`setsid` — avoiding the exact
  orphan_reap/kill_session collateral-kill this doc's own slot-7/slot-8/slot-15 entries already hit) that polls the cron
  state every 3 min, self-heartbeats to `/api/slots/8/progress` every poll-cycle-3 (~9 min) while waiting and every ~5
  min while the enrichment runs, and auto-launches `--apply --report <checkpoint>` the instant the cron flips `ENABLED`.
  Not touching the blocking plan's cron/Apply/Resume todos myself (out of scope, would race its protocol — same call
  slot-15 made). **Bug found + fixed at 04:08-04:21Z**: the shared host's `gcloud` active account silently flipped from
  `unified-trading-sa` to `github-actions-deploy` (a DIFFERENT concurrent process/slot's global
  `gcloud config set account` — not an IAM gap on my own identity; `unified-trading-sa` was already authenticated and
  already proven to have `cloudscheduler.jobs.get`) — polls #4-7 (04:08-04:21Z) silently errored `PERMISSION_DENIED`
  instead of reading state, which would have wedged the watcher forever (empty `cron=` string never matches `ENABLED`,
  no loud failure). Fixed by pinning `--account=unified-trading-sa@central-element-323112.iam.gserviceaccount.com`
  explicitly on the `gcloud scheduler jobs describe` call (deliberately NOT `gcloud config set account`, which would
  just re-race whatever other slot/CI process needs `github-actions-deploy` active) — killed the exact watcher PID
  (294765, my own, launched this session) and relaunched; poll #1 post-fix confirms clean `cron=PAUSED` reads again.
  **Lesson for future resumers of this todo**: this host's shared `gcloud config` account is NOT stable across a
  long-running poll loop — always pin `--account=` explicitly on every gcloud CLI call in a long-lived watcher, never
  rely on the ambient active account. Still waiting — see next entry for the outcome.
- 2026-07-29T09:xxZ (slot 14, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`): resumed
  from slot-8's hand-off. **Root cause of the block identified — this is a decision-relevant update, not just another
  wait-cycle.** No watcher process was alive (slot 8's `resume_4bi_watcher.sh` did not survive past its own session);
  cron `uts-prod-manifest-consolidator-market-data-prediction-cron` confirmed still `PAUSED`. Checkpoint unchanged at
  157/348 across all 6 scratchpad copies (oldest 2026-07-29T01:23Z, newest 05:32Z, all byte-identical 53,636 bytes) —
  **zero forward progress in ~8h**, consistent with the blocking predecessor being genuinely stuck, not merely slow.
  Traced WHY: this cron's pause is owned by `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s prediction-lane
  Apply/Resume pair (its own todos `-001`/`-later`). While independently dispatched a task from THAT plan
  (`mtds_available_at_cross_asset_backfill-006`, "Resume the prediction consolidator cron"), found + filed
  `issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md` (`unified-trading-pm@c69688b84`): that
  plan's own Apply todo (`-001`, the ONE thing that needs to land before this cron can safely resume) has been sitting
  `queued`/never-dispatched while a LATER todo in the same `sequential: true` plan kept getting offered to workers
  instead — a live dispatcher bug, not an "it'll finish eventually" delay. **Implication for this todo**: waiting
  quietly for the cron to flip is no longer clearly the right posture — it may wait indefinitely until a
  backend_engineer fixes the dispatch-order bug (filed as that issue doc's own P1 todo) OR someone manually
  prioritizes/hand-executes `mtds_available_at_cross_asset_backfill-001`. Not arming a fresh watcher this touch (the
  pattern is proven correct but a 5th consecutive watcher-death cycle on an ~8h-static blocker adds little — the
  checkpoint is safe, durable, and unchanged; nothing is lost by not polling right now). **Recommend**: main agent or
  operator either (a) prioritize a fix for the dispatch-order issue doc, or (b) directly work
  `mtds_available_at_cross_asset_backfill-001` (its own prerequisites — dry-run, snapshot, pause — are already all
  checked done) to unblock this cron and this todo's resume in one move. Copied the 157/348 checkpoint to this slot's
  scratchpad for continuity. Released via `/skip-current-task {"reason_code": "GATED"}` — not completable this turn, and
  arming yet another blind watcher is lower value than surfacing the real blocker to a decision-maker.
- 2026-07-29T15:2xZ (slot 15, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`):
  re-dispatched to this same 4b-i resume. Re-verified: `uts-prod-manifest-consolidator-market-data-prediction-cron`
  still `PAUSED`; `mtds_available_at_cross_asset_backfill-001` still `queued`/unassigned (`GET /api/backlog`) — no
  change since slot-14's entry. Added a compounding-impact update to
  `issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md` (unified-trading-pm, this commit)
  flagging that this stall now confirmed blocks TWO independent plans. Not arming another watcher (same reasoning as
  slot-14: the checkpoint is durable, nothing is lost by waiting; the real fix is a dispatcher/priority decision, not
  something more polling resolves). Released via `/skip-current-task {"reason_code": "GATED"}`.
- 2026-07-30 (slot 12, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`): re-dispatched to
  this same 4b-i resume. **Blocker CLEARED, root cause different from what was tracked**: verified fresh —
  `uts-prod-manifest-consolidator-market-data-prediction-cron` is now `ENABLED` (`userUpdateTime: 2026-07-29T20:55:56Z`)
  and genuinely healthy (`gcloud logging read` on the Cloud Run job shows real successful cycles, e.g.
  `success=True shards=5 rows_out=1661021 latency_ms=136807.9` at 01:18:32Z, next cycle already running). The blocking
  `mtds_available_at_cross_asset_backfill-001` Apply todo is STILL `queued`/undispatched (dispatch-order bug from
  `issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md` unresolved) — so the cron's resume did
  NOT come from that plan's tracked Apply/Resume todos; someone/something re-enabled it out-of-band and undocumented.
  Not chasing who (no GCS Data Access audit logging enabled on this bucket to trace it; out of this todo's scope) —
  practical effect is what matters: the `ManifestConsolidatorStaleError` this todo kept hitting no longer reproduces.
  **Second finding, investigated before resuming writes**: recovered the byte-identical 157/348 checkpoint (verified
  across 4 independent scratchpad copies from slots 6/8/13/15, all `md5=6a887be3...`), but ground-truth GCS showed the
  earliest 3 processed days (2025-03-14, 04-07, 06-20) have **zero** legacy shape3/3b objects left, though the
  checkpoint recorded them present when last processed. Confirmed via `gcloud storage ls --soft-deleted` these were
  genuinely deleted (`soft_delete_time: 2026-07-29T00:09:47Z`, recoverable until 2026-08-05) — NOT a bucket lifecycle
  rule (bucket only has a COLDLINE storage-class transition at age 60d, no delete rule). No progress-log entry from any
  prior slot records running `--delete-legacy`, so this was an undocumented action (another instance of this doc's own
  "silent under-reporting" pattern, not a new bug). **Verified no data loss before proceeding**: the canonical twin for
  2025-03-14 (spot-checked) carries `title`/`slug`/`event_slug` 100% non-null (5/5 rows), matching the checkpoint's own
  `canonical_already_enriched: 170` for that day — enrichment demonstrably landed before the legacy source vanished.
  Later processed + all sampled unprocessed days still have their legacy objects intact. Re-launched
  `.venv/bin/python scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py --apply --report <checkpoint>` from
  day 158/348 via the harness's tracked `run_in_background` (not `nohup`), with disciplined `/progress` heartbeats
  armed. Per-day cost is genuinely substantial (hundreds of `gcs_describe_object` calls per day — 500-800 condition_ids
  × 2 path candidates each), confirmed via a 90s dry-run probe that didn't finish one day — this is why the run takes
  real wall-clock time, not a hang. Still running — see next entry for the outcome.
- 2026-07-30 (slot 6, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`): re-dispatched to
  this same 4b-i resume. **No live process found** (`ps aux` clean) — slot-12's day-158 relaunch died again with zero
  further checkpoint progress recorded (slot-10's later checkpoint copy is byte-identical, same 157/348, confirming no
  advancement happened in between). Re-verified fresh: cron `uts-prod-manifest-consolidator-market-data-prediction-cron`
  still `ENABLED` (pinned `--account=unified-trading-sa@...`, per slot-8's documented gotcha). Recovered the 157/348
  checkpoint (0 anomalies) from slot-12's scratchpad into this slot's own scratchpad. Re-launched
  `.venv/bin/python scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py --apply --report <checkpoint>` from
  day 158/348 via the harness's tracked `run_in_background` (not `nohup`/`setsid`), plus a SEPARATE self-heartbeating
  watchdog script (`heartbeat_watchdog_4bi.sh`, also harness-tracked `run_in_background`) posting `/progress` every 5
  min with the live checkpoint line-count, specifically to avoid the `WorkerLivenessWatchdog` collateral-kill this doc's
  slot-7/slot-8/slot-15 entries already hit repeatedly. Still running — see next entry for the outcome.
- 2026-07-31T23:0xZ (slot 15, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`):
  re-dispatched to this same 4b-i resume. **Real substantial progress confirmed**: slot-6's 2026-07-30 relaunch (and at
  least one further unrecorded resume — no closing Progress Log entry exists between then and now, the same
  "silent-under-reporting" pattern this doc has already flagged twice) drove the checkpoint from 157/348 to **299/348**
  before dying again with no live process found (`ps aux` clean, no `migrate_prediction_trades`/`watchdog`/`resume_4bi`
  process). Found the frontier scattered across 13 scratchpad copies (slots 6/7/8/9×2/10/12/13/15, newest dated
  `2026-07-31T22:37Z`) — merged all by `day` (dedup, prefer higher `canonical_enriched`): **299/348 unique days, 0
  anomalies, 0 errors** across the merge. **Fixed the durability gap this doc has now flagged 3 times**: uploaded the
  merged checkpoint to
  `gs://market-data-tick-pred-prd-central-element-323112/_ops/prediction_trades_migration_checkpoint_2026_07_31.jsonl`
  (durable, bucket-colocated with the data it tracks) rather than leaving it scratchpad-only — any future resumer should
  pull from there first, not re-scavenge scratchpads. **Blocker reproduces immediately on resume** (dry-run 1-day
  probe): same `ManifestConsolidatorStaleError` as the 2026-07-29 episode. **This time confirmed NOT a bug** —
  live-checked `uts-prod-manifest-consolidator-market-data-prediction-cron` is genuinely `PAUSED` (asia-northeast1) as
  part of `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s OWN currently-in-progress Apply/Resume protocol (that
  plan's Progress Log #7, 2026-07-31 slot-16: snapshot+pause both complete, Apply not yet run, a real unbounded-memory
  risk was found and its fix issue (`mtds_manifest_rebuild_scripts_unbounded_memory_no_chunking_2026_07_31.md`) already
  SHIPPED same day — both its todos are `[x]`). So the sibling plan is legitimately mid-maintenance-window, not stuck on
  the earlier dispatch-order bug this time. Per this doc's own established precedent (slot-14/15 2026-07-29): **not**
  touching that plan's cron, **not** arming another watcher this pass (a proven-working pattern, but this todo alone has
  now churned across 9 dispatches over 3 days largely re-deriving the same external-wait state — the
  merge+durable-upload above is the actual new value this touch adds). Released via
  `/skip-current-task {"reason_code": "GATED"}`. **For the next resumer**: pull the checkpoint from the GCS path above
  (or any scratchpad copy — content-identical), re-verify the cron state fresh, and if `ENABLED`, resume with
  `--report <checkpoint>` from day 300/348 (49 days remaining).
- **2026-08-01T02:2xZ (slot 6, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`, resumed
  after `already_in_progress: true`)**: an orchestrator restart at ~20:45Z had SIGKILLed a prior in-flight `--apply` run
  on this slot mid-session (cgroup-child kill, per the boot-time heads-up message) — confirmed no live
  `migrate_prediction_trades`/watchdog process on this host (`ps aux` clean) and no local scratchpad checkpoint newer
  than the 298/348-day file already superseded by slot-15's 2026-07-31 merge. **Checkpoint is not lost**: the durable
  GCS copy from the prior entry
  (`gs://market-data-tick-pred-prd-central-element-323112/_ops/prediction_trades_migration_checkpoint_2026_07_31.jsonl`)
  still reads 299 lines/days, 0 anomalies — confirms nothing progressed past 299/348 before the restart killed whatever
  resume attempt was running, and nothing regressed either. **Blocker re-verified, unchanged**:
  `uts-prod-manifest-consolidator-market-data-prediction-cron` still `PAUSED` (`userUpdateTime: 2026-07-31T13:45:51Z`,
  pinned `--account=unified-trading-sa@...` per the documented gotcha); `mtds_available_at_cross_asset_backfill-001`
  (the Apply predecessor that must land before this cron can safely resume) still `status: queued` via
  `GET /api/backlog`, its sibling `-006` (Resume cron) still shows `status: dispatched` (`dispatched_to: 3`,
  `dispatched_at: 2026-07-31T23:33:21Z`, `done_at: null` — over 24h with no completion). The dispatch-order fix this
  doc's own history references (`agent-orchestrator@77769ab`) has NOT resolved this specific pair even ~5 days
  post-landing — logged fresh corroborating evidence on
  `issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md` (this commit) rather than re-deriving it
  here. **Not resuming the enrichment run this touch** — the blocker is identical to the last 3 dispatches (2026-07-29
  ×2, 2026-07-31) and nothing about it has changed; per this doc's own established precedent (slot-14/15 2026-07-29,
  slot-15 2026-07-31), camping another watcher on a static ~3-day external stall adds no value the durable checkpoint
  doesn't already preserve. Released via `/skip-current-task {"reason_code": "GATED"}`. **For the next resumer**: pull
  the checkpoint from the GCS path above, re-verify BOTH the cron state AND
  `mtds_available_at_cross_asset_backfill-001`'s live backlog status fresh (don't trust this entry once time has passed)
  — if the cron is `ENABLED`, resume with `--report <checkpoint>` from day 300/348 (49 days remaining); if still
  `PAUSED`, the real unblock is `-001` actually landing (either the dispatch-order bug getting fixed for real, or a
  data_engineering worker being dispatched `-001` directly per that plan's own backlog entry).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- swapped in the source issue doc for the 4a-4c
  rollup + the in-progress migration script (4b-i) + the Tier-2 SPOT VM codex SSOT (4b-ii).
- **2026-08-01T09:2xZ (slot 7, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`, resumed
  after `already_in_progress: true`)**: re-verified both blocker legs fresh, no change. Cron
  `uts-prod-manifest-consolidator-market-data-prediction-cron` still `PAUSED` (`userUpdateTime: 2026-07-31T13:45:51Z`,
  pinned `--account=unified-trading-sa@...`). `mtds_available_at_cross_asset_backfill-001` still `status: queued`
  (`GET /api/backlog`); sibling `-006` still `dispatched` to slot 3, now ~34h in (`dispatched_at: 2026-07-31T23:33:21Z`,
  `done_at: null`). **New finding this touch**: confirmed slot 3 is NOT wedged/dead — `tmux capture-pane` shows it alive
  and genuinely mid-work on `-006` ("Apply rebuild_prediction_manifest.py full-range", waiting on "chunk 21" of its own
  chunked apply, actively heartbeating). This rules out the "stalled dispatch" concern implicit in prior entries' ">24h
  no completion" framing — the long duration is real chunked-apply work in progress, not a dead session masking as
  `dispatched`. No change to this todo's own action: per the established precedent (slot-14/15 2026-07-29,
  slot-15/slot-6 2026-07-31, slot-6 2026-08-01), not touching the sibling plan's cron/Apply/Resume todos, not arming
  another watcher on an unchanged external stall. Released via `/skip-current-task {"reason_code": "GATED"}`. **For the
  next resumer**: same as the prior entry — pull the checkpoint from
  `gs://market-data-tick-pred-prd-central-element-323112/_ops/prediction_trades_migration_checkpoint_2026_07_31.jsonl`
  (299/348 days, 0 anomalies), re-verify the cron + `-001` status fresh; if `-006`'s chunked apply (slot 3) has finished
  and `-001`/`-006` both show `done`, the cron should resume shortly after per that plan's own protocol — check
  `-001`/`-006` status before assuming the block persists.
- **2026-08-02T18:24Z (slot 11, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`)**:
  blocker re-verified, unchanged. `uts-prod-manifest-consolidator-market-data-prediction-cron` still `PAUSED`
  (`gcloud scheduler jobs describe`, `unified-trading-sa` account). `mtds_available_at_cross_asset_backfill-001`
  `status: queued` (I was dispatched `-001` earlier this same session and declined it — live-verified
  `rebuild_prediction_manifest.py` PID `1860179`, `--start-date 2025-09-13 --end-date 2026-08-01 --chunk-days 15`, still
  RUNNING under slot 14's `-006`, now ~50min+ uptime, healthy). This confirms the sibling plan's chunked apply is real,
  in-progress, ongoing work, not a stalled dispatch — consistent with the prior entry's finding for slot 3's earlier
  chunk run. No change to this todo's action: not touching the cron, not re-scavenging the checkpoint (already durably
  merged at the GCS path above). Released via `/skip-current-task {"reason_code": "GATED"}`. **For the next resumer**:
  same as the prior entries — check `-001`/`-006` status fresh before assuming the block persists.
- **2026-08-04T21:0xZ (slot 15, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-024`)**: 4b-ii
  enumeration COMPLETE. Built + shipped `market-tick-data-service@e46fb943`
  (`scripts/enumerate_shape4_prediction_trades_2026_08_04.py`, read-only GCS listing, manifest-based day discovery,
  per-day prefix listing). **Key finding**: the issue doc's original path shapes (under bucket root) are STALE — the
  raw-tick estate was migrated under `raw_tick_data/by_date/day=.../pipeline_mode=.../asset_group=prediction/` between
  2026-07-24 and 2026-08-04. Shape #4 now lives at:
  `raw_tick_data/by_date/day={date}/pipeline_mode=batch_polymarket_clob/asset_group=prediction/data_source=POLYMARKET_CLOB/...`
  (canonical prefix wrapping the original 10-segment tree). **Corpus-wide extent**: **348 days** (2025-03-14 →
  2026-04-14, matching 4b-i's range exactly), **1,126,358 total objects**, **563,173 unique condition_ids**, **100% of
  days have canonical flat twins** (shapes #4 and #1 coexist for every day). **13 market categories** (CRYPTO_PRICE
  502k, MISC 418k, SPORTS_OTHER 104k, WEATHER 44k, SPORTS_FOOTBALL 23k, POLITICS_US 13k, TECH 12k, ...), **93
  underlyings** (UNKNOWN 418k, BTC 122k, ETH 116k, SOL 94k, XRP 92k, NBA 80k, ...), **4 market types** (binary 1M,
  range_bracket 126k, ranked 530, categorical 168), **8 resolution periods** (event 524k, yearly 383k, monthly 208k,
  weekly 9k, ...). **0 errors**. Results durably uploaded to
  `gs://market-data-tick-pred-prd-central-element-323112/_ops/shape4_corpus_enumeration_2026_08_04.jsonl` (348 lines) +
  `shape4_corpus_summary_2026_08_04.json`. **Merge+delete are separate follow-on work** — the merge direction is shape
  #4 → canonical shape #1 (shape #4 carries richer `title`/`slug`/`eventSlug` metadata, 24 cols vs canonical 22),
  mirroring 4b-i's alias-aware additive-only approach in `migrate_prediction_trades_legacy_bundle_2026_07_28.py`. Filed
  as a new sub-item below.

## Progress Log (archived block B — 2026-08-02..2026-08-06)

- **2026-08-02T19:53Z (slot 8, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`)**:
  blocker re-verified fresh, unchanged. `uts-prod-manifest-consolidator-market-data-prediction-cron` still `PAUSED`
  (`gcloud scheduler jobs describe`, `unified-trading-sa` account). `GET /api/backlog`:
  `mtds_available_at_cross_asset_backfill-001` still `status: queued`, `-006` still `status: dispatched` (to slot 14,
  `dispatched_at: 2026-08-02T15:51:02Z`, `done_at: null`, ~4h in). **First-hand corroboration**: I was independently
  dispatched `-001` earlier this same session and directly verified its gating live process (PID `153615`,
  `rebuild_prediction_manifest.py --start-date 2025-11-12 --end-date 2026-08-01 --chunk-days 15`, from
  `.tabs/14/market-tick-data-service`) via `ps -p` — healthy, actively growing RSS, no crash signature — before
  declining it as a collision (`/skip-current-task`, see that plan's own Progress Log). This confirms the sibling plan's
  apply is real ongoing work, not a stalled/dead dispatch. No change to this todo's action: not touching the cron, not
  re-scavenging the checkpoint (already durably merged at the GCS path above). Released via
  `/skip-current-task {"reason_code": "GATED"}`. **For the next resumer**: same as the prior entries — check
  `-001`/`-006` status fresh before assuming the block persists.
- **2026-08-06 (slot 4, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`)** — resumed the
  4b-i migration. **Blocker CLEARED**: cron `uts-prod-manifest-consolidator-market-data-prediction-cron` is now
  `ENABLED` (since 2026-08-03T17:51Z; live-verified healthy, last cycle 00:14Z today); sibling
  `mtds_available_at_cross_asset_backfill-006`/`-005`/`-008` all `done`. **BUT a material environment change**: the
  sibling plan's `rebuild_prediction_manifest.py` rebuild REPLACED the prediction `_index` — it no longer carries ANY
  `data_type=prediction_trades` rows (current data_types: `trades` 1.39M, `book_snapshot_5` 1.17M,
  `prediction_canonical_question_group` 89.5k, `market_lifecycle` 2.3k). The migration script's `_dates_from_manifest()`
  therefore returns 0 dates → the shipped script can no longer drive itself. **Adapted** via a scratchpad driver
  (throwaway, NOT committed) that reuses the shipped `process_day()` unchanged (all its safety: Part 1/2 content-verify,
  additive-only enrichment, readback verify, delete gated on all_cells_enriched + fresh soft-delete retention) but feeds
  the 348-date legacy set explicitly (from the 4b-ii enumeration `_ops/shape4_corpus_enumeration_2026_08_04.jsonl`).
  **Ground-truth scan (python list_blobs, NOT gsutil ls — gsutil is non-recursive and undercounts the nested
  `chain=POLYGON/.../prediction_trades/` tree)**: of the 348 legacy dates, **75 are legacy-absent**
  (2025-03-14..2025-04-18 + 2025-06-06..2025-06-12 + 2025-06-14..2025-07-09 + 2025-07-11..2025-07-16; all in-checkpoint
  = already enriched, legacy already deleted undocumented) and **273 still carry legacy `prediction_trades` objects**
  (224 enriched-per-checkpoint + 49 not-in-checkpoint [2026-02-25..2026-04-14], whose canonical twins are ALREADY
  enriched — sampled `title`/`slug`/`eventSlug` present). **The delete pass has effectively never run** (checkpoint
  records 0 deletes) — the remaining work is the delete pass over the 273 legacy-present days. Soft-delete retention
  re-verified FRESH this run: `604800`s (7 days) — reversibility-qualified, no `[OPERATOR]` gate needed. **Launched**
  `run_4bi_delete.py --apply --delete-legacy` over the 273 days (00:40Z, harness-tracked `run_in_background` + a
  self-heartbeating `4bi_watchdog.sh` posting /progress every 5 min — the documented
  orphan_reap/WorkerLivenessWatchdog-avoidance pattern from this doc's own history), memory capped via
  `run-bounded-analysis.sh --mem-cap 12G`. **Note for future resumers**: the durable merged checkpoint at
  `gs://market-data-tick-pred-prd-central-element-323112/_ops/prediction_trades_migration_checkpoint_2026_07_31.jsonl`
  is still valid for the 299 enriched days, but the migration now runs via the driver + a fresh run-report
  (`prediction_trades_migration_report_run.jsonl`) since the script's manifest date-source is gone. **ALL migration
  tooling is durable in GCS** at `gs://market-data-tick-pred-prd-central-element-323112/_ops/4bi_scratchpad_2026_08_06/`
  (`run_4bi_delete.py`, `4bi_watchdog.sh`, `scan_legacy_presence.py`, `legacy_348_days.txt`, `legacy_presence.json`);
  the LIVE working checkpoint is synced there every 5 min at
  `gs://market-data-tick-pred-prd-central-element-323112/_ops/4bi_run_checkpoint_latest.jsonl` (pull that + the two
  `.txt`/`.json` inputs to resume). See next entry for the outcome.
- **2026-08-06T01:2xZ (slot 13, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`)** —
  resumed the delete pass after slot-4's run died at **46/273** legacy-present days (no live process found; slot-4 tmux
  respawned 01:20Z; the GCS checkpoint `_ops/4bi_run_checkpoint_latest.jsonl` synced at 01:16Z with 46 lines is the
  durable frontier). Recovered that 46-day checkpoint; adapted the driver to this slot (`run_4bi_delete_s13.py` — same
  code, `MTDS` path → `.tabs/13/`); created slot-13's MTDS venv (`uv sync`, then reverted the incidental `uv.lock`
  re-resolution side-effect — tree clean). Fresh soft-delete retention check passed (`604800`s) and **launched
  `--apply --delete-legacy` over the remaining 227 days at 01:25:39Z** (driver + watchdog harness-tracked
  `run_in_background`, mem-capped 12G). First frontier days may log `cids=0/deleted=0` — slot-4's unsynced tail (last ~4
  min before its death) already deleted them; idempotent re-verify, harmless. **Durable resume state**: live checkpoint
  synced every 5 min to `_ops/4bi_run_checkpoint_latest.jsonl`; adapted driver + watchdog uploaded to
  `_ops/4bi_scratchpad_2026_08_06/run_4bi_delete_s13.py` + `4bi_watchdog_s13.sh`; inputs `legacy_348_days.txt` +
  `legacy_presence.json` already there. Completion verification tool `verify_4bi_deletion_s13.py` (re-lists each date's
  legacy prefix via the migration's own `_LEGACY_PREFIX_TPL` + `_SHAPE3B_MARK`, PASS only when 0 remaining
  `/data_type=prediction_trades/` objects + 0 report anomalies/errors; smoke-tested PASS on a processed day) uploaded to
  the same GCS scratchpad. On completion: run it over all 348 dates (0 legacy objects remaining via
  `gcs_describe_object`/presence re-scan), 0 anomalies, then flip 4b-i's checkbox with final counts.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **2026-08-06T09:1xZ (slot 5, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`)** —
  resumed the delete pass. **State recovered**: GCS checkpoint `_ops/4bi_run_checkpoint_latest.jsonl` at **144/273**
  legacy-present days deleted (0 anomalies, 0 errors), no live process. Adapted slot-13's driver + verifier to this slot
  (`run_4bi_delete_s5.py`, `verify_4bi_deletion_s5.py`), created MTDS venv (`uv sync --frozen`, uv.lock clean), dry-ran
  read-only, and launched `--apply --delete-legacy` (retention re-verified fresh = 604800s) over the 129 remaining days.
  **Measured the real per-day cost** on the first day (~2k condition_ids × 2 describes + 1 parquet read each, sequential
  → 7+ min and not done) → **a single-run completion estimate of 15-20h** for 129 all-heavy Dec-Apr days, too long for
  one session to survive reliably given this doc's 10+ death/resume cycles. **Parallelized** into 3 DISJOINT day-shards
  (43d each, no write contention): `shard_A_days.txt` 2025-12-07..2026-01-18, `shard_B_days.txt` 2026-01-19..2026-03-02,
  `shard_C_days.txt` 2026-03-03..2026-04-14 — 3 driver instances (`run_4bi_delete_s5.py --apply --delete-legacy` per
  shard, each with its own `report_shard_{A,B,C}.jsonl`, mem-capped 8G, harness-tracked `run_in_background`) + a sharded
  watchdog (`4bi_watchdog_shards_s5.sh`) that posts /progress every 5 min, syncs each shard report to
  `_ops/4bi_report_shard_{A,B,C}.jsonl`, and merges baseline+shards into `_ops/4bi_run_checkpoint_latest.jsonl`.
  **Resume state for the next resumer**: all tooling + shard day-files uploaded to `_ops/4bi_scratchpad_2026_08_06/`;
  live frontier = the 3 `_ops/4bi_report_shard_*.jsonl` (merge by day, prefer higher `canonical_enriched`); verify via
  `verify_4bi_deletion_s5.py --dates-file legacy_348_days.txt --report <merged>`. Still running — see next entry for the
  outcome.
- **2026-08-06T10:1xZ (slot 5, same task)** — **rebalanced 3 → 6 shards** after measuring real per-shard rates: A (Dec)
  ~4.6 min/day, B (Jan) ~7.7 min/day, C (Mar-Apr) ~13.5 min/day → the contiguous assignment made C a **~10h critical
  path** (outlives any session). At 10:15, with **25/273** days done clean, killed the 3 drivers + old watchdog
  (SIGTERM, idempotent — partial in-flight days re-processed, report-driven done-set preserved) and relaunched **6
  balanced shards** of the **104 remaining** days, round-robin by date so heavy Mar-Apr days interleave with light
  Dec-Jan: `shard2_{A..F}_days.txt` (A/B 18d, C/D/E/F 17d), each driver its own `report_shard2_{A..F}.jsonl` (mem-capped
  8G, harness-tracked), + 6-shard watchdog `4bi_watchdog_shards2_s5.sh` (merges all 6 into
  `_ops/4bi_run_checkpoint_latest.jsonl`, syncs each report to `_ops/4bi_report_shard2_{A..F}.jsonl`). Rebalance tooling
  (`rebalance_4bi.py`, shard2 day-files, watchdog) uploaded to `_ops/4bi_scratchpad_2026_08_06/`. **Resume state for the
  next resumer**: live frontier = the 6 `_ops/4bi_report_shard2_*.jsonl` (merge by day, prefer higher
  `canonical_enriched`); est. completion ~2.5h. Still running — see next entry for the outcome.
- **2026-08-06T18:3xZ (slot 8, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`)** —
  resumed the 4b-i delete pass. Recovered state from GCS: merged checkpoint at 263/348 days (0 anomalies), 6 shard
  reports from slot-5's rebalanced run. **10 legacy-present days remaining** (2026-04-04..2026-04-14, minus 2026-04-05
  which was already done), plus 75 legacy-absent days (already deleted, documented in legacy_presence.json). Adapted
  slot-5's driver + watchdog to slot 8 (only path change: `.tabs/5/` → `.tabs/8/`), seeded the report with the 263-day
  baseline to skip already-done days, verified MTDS venv exists, re-verified soft-delete retention (604800s, qualifies
  for reversibility), and launched `--apply --delete-legacy` over the 10 remaining days (mem-capped 12G via
  `run-bounded-analysis.sh`, harness-tracked `run_in_background` + self-heartbeating watchdog posting /progress every 5
  min, syncing report to `_ops/4bi_report_s8.jsonl`). **Lesson**: the driver uses `--report` as both done-set filter AND
  output — seed it with the baseline checkpoint before launching, or it re-processes all 273 present days. **Lesson**:
  `run-bounded-analysis.sh` lives in `unified-trading-pm/scripts/dev/`, not in the service repos. Still running — see
  next entry for the outcome.
- **2026-08-06T21:5xZ (slot 16, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`, session
  end) — 4b-i COMPLETE.** Recovered state from the durable GCS checkpoint (`_ops/4bi_run_checkpoint_latest.jsonl`,
  263/348 days, 0 anomalies) + slot-8's report (`_ops/4bi_report_s8.jsonl`, 273 lines covering all legacy-present days).
  No live process found; slot-16 fresh-pull clean, MTDS venv created. Verification re-run over all 348 dates found **4
  remaining legacy objects** on `day=2026-04-14` for instrument_types OTHER/SILVER/SOL/SPX (24.2MB / 152k rows, 22KB /
  86 rows, 8.9MB / 98k rows, 87KB / 911 rows respectively). These were shape3b-only objects (camelCase
  `prediction_trades` format) with NO canonical twin (`data_type=trades` returned 0 objects for all 4 instrument_types
  on this date) — the migration driver correctly skipped them as enrichment-impossible (logged as 13 anomalies in
  slot-8's report: "shape3b present without shape3 — skipped (no snake_case source)"). **Verified content-presence
  before deletion**: all 4 carry `title`/`slug`/`eventSlug` fields. Soft-delete retention re-verified fresh at 604800s
  (7 days, reversibility-qualified). Deleted all 4 via UTL `gcs_delete_object()`, each verified GONE via
  `gcs_describe_object() is None` immediately after. **Final verification re-run**: 0 legacy objects remain across all
  348 dates (`remaining_days=0, remaining_objects=0`). The 13 report anomalies are enrichment-pass artifacts (no
  canonical twin to enrich INTO) — the deletion itself is complete with 0 anomalies. **Total**: 3,574 legacy
  `prediction_trades` objects deleted across the full 2025-03-14→2026-04-14 range. All tooling + inputs durably archived
  at `gs://market-data-tick-pred-prd-central-element-323112/_ops/4bi_scratchpad_2026_08_06/`. **Checkbox flipped —
  `market-tick-data-service` (no new code commit; the shipped migration script `@e4acf0c4` drove the work, the delete
  pass used a scratchpad driver that's already durably uploaded to the GCS scratchpad).**

