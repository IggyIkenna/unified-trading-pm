---
doc_type: issue
title: "Manifest consolidator for market-data-tick-cefi stuck on a phantom lock since ~2026-08-18T02:14Z — 40+ hourly cycles skipped, zero alerts fired"
summary: >-
  LIVE, ONGOING P0 (as of 2026-08-19T19:50Z). The `uts-prod-manifest-consolidator-market-data-cefi` Cloud Run job IS
  running on its documented hourly schedule and reporting `Completed / True` every cycle — this is NOT a job-down
  incident. Its own Cloud Logging output shows every cycle short-circuits on `error=locked` ("fresh lock present —
  sibling cron still running") and writes ZERO rows while still exiting 0. The canonical
  `market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` has not changed (same
  generation/last_modified) in ~41.6h against an 86400s/24h budget. This is the actual, currently-live root cause of
  why the liquidations wrong-inverse-notional re-derive (data_pipeline_alert_storm_root_cause_batch_2026_08_10.md P0)
  died with `ManifestConsolidatorStaleError`-class failures on 2026-08-18 — NOT the margin_type/contract_size bugs
  previously tracked (all fixed, see cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md). Blocks ANY
  market-data-tick-cefi backfill/reprocess hitting the loud-fail read guard, not just liquidations. Zero
  CONSOLIDATOR_DOWN/CONSOLIDATOR_STALE/MANIFEST_CONSOLIDATION_FAILED alerts found in #data-pipeline-alerts across the
  full 72h window despite a documented dedicated liveness watchdog that should catch exactly this.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [unified-trading-library, deployment-service, market-data-processing-service]
scope: [engineer, admin]
tags: [manifest, consolidator, infrastructure, data-correctness, stuck-lock, cefi, incident]
related:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    /plans/active/issues/cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md,
  ]
context_scope:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    unified-trading-library/unified_trading_library/manifest_consolidator.py,
    unified-trading-library/unified_trading_library/manifest_writer/_state.py,
    /plans/active/issues/cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md,
  ]
created: 2026-08-19
author: claude-agent
source: "plan_reconciler sports-tranche run (agt-07473e), live-status check ordered by operator ruling BLK-7d1f4a2d"
priority: P0
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# Manifest consolidator for market-data-tick-cefi stuck on a phantom lock — 2026-08-19

## What's confirmed (all measured live, this session, 2026-08-19T19:4x-19:5xZ)

1. **Canonical index frozen.** UTL `get_storage_client().get_blob_metadata('market-data-tick-cefi-prd-central-element-323112', '_index/availability_index.parquet')` →
   `last_modified='2026-08-18T02:13:57.708000+00:00'`, `generation=1787019237694916`, `metadata=None`. Current time at
   measurement: `2026-08-19T19:50:38Z` → **staleness ≈ 149,801s (~41.6h)**, vs the documented 86400s/24h loud-fail
   budget (`manifest-consolidator-ssot.md` § "Liveness + health contract").
2. **The Cloud Run job itself is healthy and on-schedule — this is NOT a "job not running" incident.**
   `gcloud run jobs executions list --job=uts-prod-manifest-consolidator-market-data-cefi --region=asia-northeast1
   --project=central-element-323112 --limit=15` shows clean hourly firings all through 2026-08-19 (12:00, 13:00,
   13:34, 14:00, 15:00, 15:35, 15:49, 16:00, 16:34, 17:00, 18:00, 19:00, 19:34), every one `status.conditions[0].status=True
   "Execution completed successfully"` — matching the documented hourly `0 * * * *` schedule for the `market-data-cefi`
   category (`manifest-consolidator-ssot.md` line ~76-82). Two executions ran anomalously long vs the typical ~1min:
   `rsgbc` 13:34:59→15:36:14 (2h1m15s) and `nfgs5` 16:34:58→18:33:05 (1h58m7s) — every other execution both before and
   after these two completed in 50s-2min as normal.
3. **Root cause, direct from Cloud Logging** (most recent completed execution,
   `uts-prod-manifest-consolidator-market-data-cefi-wx25q`, 2026-08-19T19:00:53Z→19:01:26Z):
   ```
   19:00:53 INFO Event logging initialized: mode=live, service=manifest-consolidator
   19:01:02 INFO ManifestConsolidator: skipping cycle for bucket=market-data-tick-cefi-prd-central-element-323112 — fresh lock present (sibling cron still running)
   19:01:18 manifest-consolidator bucket=market-data-tick-cefi-prd-central-element-323112 success=True shards=0 rows_in=0 rows_out=0 dedup_dropped=0 legacy_seeded=False pruned_shards=0 latency_ms=25371.0 error=locked at=2026-08-19T19:01:18.886709+00:00
   19:01:20 Container called exit(0).
   ```
   **Every hourly cycle reports `success=True` while doing ZERO work (`shards=0 rows_in=0 rows_out=0`) because it
   believes a sibling cron is still running and defers to it.** This is why the job "completing successfully" every
   hour (point 2) is fully consistent with the canonical index never actually moving (point 1) — the job isn't failing,
   it's perpetually no-op'ing on a lock it never clears.
4. **Direct causal chain to the operator's original question** (BLK-7d1f4a2d, answered decision A: "dispatch a
   live-status check now"). The liquidations re-derive VM `mdps-backfill-cefi-20260816-162418` (relaunched 2026-08-16
   16:24 UTC, `--date-concurrency 2`, tracked in
   `cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md`'s "Still open" P0 monitor-to-completion item) ran its
   full 2223-date range to completion (`🏁 Date range complete: 2020-01-01..2026-01-31`) but exited
   `Handler returned non-zero exit code: 1` at 2026-08-18T02:04:52Z, `VM_SHUTDOWN_ON_COMPLETION=true` self-deleted it
   immediately after. Its own `run.log` tail (read via UTL `gcs_read_object_range`, bucket
   `deployment-scripts-central-element-323112`, `vm-logs/mdps-backfill-cefi-20260816-162418/run.log`, last 60KB) shows
   **every date from at least 2026-01-22 through 2026-01-31 failed identically**:
   `Error processing cefi: Manifest consolidator appears DOWN for bucket='market-data-tick-cefi-prd-central-element-323112':
   consolidated _index/availability_index.parquet heartbeat is 96769s old (> 86400s budget) while per-VM shards exist.`
   — staleness climbing 96769s→96824s across the tail (consistent with the canonical having last genuinely updated
   ~2026-08-16T23:11Z, i.e. **before** the one write this doc's point 1 canonical shows at 02:13:57 on 08-18 — meaning
   the phantom lock most likely first armed sometime shortly after that 02:13:57 write, and has held continuously
   since). `PROGRESS.json`'s own checkpoint (`last_completed_date="2023-05-13"`, `updated="2026-08-17T23:06:51Z"`)
   froze there because it only advances on genuine success — the job kept iterating dates for another ~3h afterward
   with zero further progress, all absorbed by this same consolidator-stale guard, before the handler gave up.
   **This is a NEW root cause, distinct from and downstream of everything already fixed in
   `cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md`** (contract_size, margin_type, shard-isolation,
   NaN-warning — all genuinely shipped and correct). The margin_type/contract_size population itself has NOT been
   re-verified against a fresh, uncorrupted-by-this-outage re-derive attempt.
5. **Zero alerting found.** `scripts/dev/slack-read-channel.py data-pipeline-alerts 72` (7,584 alert lines, 2026-08-16
   through 2026-08-19) has **zero** hits for `CONSOLIDATOR_DOWN`, `CONSOLIDATOR_STALE`, `ManifestConsolidatorStale`,
   `consolidator appears down`, or `MANIFEST_CONSOLIDATION_FAILED` — despite `manifest-consolidator-ssot.md` §
   "Liveness + health contract" documenting a dedicated `uts-prod-consolidator-liveness-watchdog` Cloud Run Job +
   `*/2 * * * *` Cloud Scheduler cron specifically built to emit `CONSOLIDATOR_DOWN` (ERROR severity) on exactly this
   condition, "Live since 2026-06-01 — executions complete 1/1 every 2 min." Either that watchdog isn't actually
   catching this bucket/condition, or its alert isn't reaching `#data-pipeline-alerts` — not independently checked
   this pass (see Next steps).

## Not yet confirmed — needs someone reading the lock's own code path

- **What/where the lock actually is** (a metadata field on the canonical blob, a separate sentinel object, an
  in-memory/Cloud-Run-concurrency assumption) and **why it never expires/clears** — `manifest_consolidator.py`'s lock
  acquire/release logic was not read this pass (outside this role's `plans/**`-only write scope; this is a code-reading
  task for whoever picks this up, not a plans-doc question).
- **Whether either of the two abnormally-long executions today** (`rsgbc` 2h1m, `nfgs5` 1h58m — see point 2) **is the
  lock's actual holder**, still technically live per Cloud Run's own bookkeeping (a hung/zombie container not yet
  reaped) rather than a purely stale/never-released marker. This is the single cheapest thing to check next — if one
  of those executions is provably still running or was force-terminated without cleanup, that's a simpler, more
  contained explanation (and fix — cancel the zombie) than a code bug in the lock's release path.
- The blob's `metadata=None` (point 1) is suggestive of — but not proof of — the exact "marker-strip" incident class
  `manifest-consolidator-ssot.md` already documents as a past, fixed incident. UTL's `get_blob_metadata()` wrapper may
  simply not surface custom object metadata the same way `gcloud storage objects describe --format="value(custom_fields...)"`
  does; this needs the `custom_fields` read specifically, not re-derived from `get_blob_metadata()` alone.
- Whether this same phantom-lock condition affects any of the OTHER 12 hourly-scheduled consolidator categories
  (`instruments-{cefi,tradfi,defi,prediction}`, `features-{cefi,defi,tradfi,calendar}`, `strategy`, `execution`,
  `ml-training-artifacts`) or is scoped to `market-data-cefi` alone — not checked this pass.

## Todos

- [x] [SCRIPT] P0. ✅ **Check whether either of the two abnormally-long executions today is the phantom lock's holder** —
      `gcloud run jobs executions describe uts-prod-manifest-consolidator-market-data-cefi-rsgbc` and `-nfgs5`
      (`--region=asia-northeast1 --project=central-element-323112`; the two runs from point 2 above, 13:34:59→15:36:14
      and 16:34:58→18:33:05, both ~2h vs the normal ~1min). If either is still shown as running, or was force-cancelled
      without releasing its lock, that is the (contained, code-free) explanation — reap/clear it and re-verify point 1
      (canonical blob `generation` advances on the next hourly cycle). Done when: confirmed cause either way.
      **CONFIRMED 2026-08-19T20:55Z (slot-4) — cause = PERPETUAL LOOP, not a single zombie. Both rsgbc AND nfgs5 WERE
      lock holders (each acquired the lock, then got SIGKILLed by the 7200s Cloud Run task timeout mid-full-merge,
      orphaning the lock via the bypassed `finally: _release_lock`), but NEITHER is the current holder — `rdlhn`
      (19:34:52Z start, STILL RUNNING) is. Loop: missing `consolidator_content_write_at` marker (canonical
      `metadata=None`) → fail-closed full merge of all ~172k shards (30M-row canonical) → >7200s → timeout kill →
      orphaned lock blocks ~9000s (`CONSOLIDATOR_LOCK_TTL_SECONDS`) → next cycle clears + re-runs the SAME doomed
      merge. 4× 2h executions today: 10:51, rsgbc, nfgs5, rdlhn. Canonical still frozen gen=1787019237694916 /
      02:13:57Z; 20:00 cycle `error_reason=locked`. Reap not applicable (current holder is live; clearing under it is
      unsafe + the loop re-arms anyway) — the fix is the todo-2 code change.**
- [x] [SCRIPT] P0. ✅ **If the zombie-execution check doesn't explain it, read `unified_trading_library/manifest_consolidator.py`'s
      lock acquire/release + staleness-check code**, confirm whether it has any TTL/expiry at all, and fix the gap
      (this workspace's own `manifest-consolidator-ssot.md` already documents a structurally similar "no fallback /
      fails closed" fix for the content-write-marker — the lock most likely needs the same kind of TTL-based
      self-healing, so a crashed/killed holder can't wedge every future cycle forever). Ship via quickmerge, gate
      green. Done when: the fix is live and a fresh hourly cycle genuinely merges (not just reports `success=True`).
      **SHIPPED 2026-08-19T21:4xZ — `unified-trading-library@af783d92e4` (QG green: tests + typecheck + codex PASS;
      sentinel + post-push ancestry verified). Premise CONTRADICTED by measurement: the lock ALREADY has TTL
      (`_LOCK_TTL_SECONDS` 300s default / 9000s cefi) — the real gap was the missing-marker → doomed-full-merge →
      timeout-SIGKILL → orphan → re-arm loop. Fix: `_UNPROVABLE_MERGE_MAX_SHARDS` (env
      `CONSOLIDATOR_UNPROVABLE_MERGE_MAX_SHARDS`, default 50000) — the cron refuses a corpus-wide unprovable merge
      over that size and skips-with-loud-alert (`success=False` → CLI exit 1 + `MANIFEST_CONSOLIDATION_FAILED`
      severity=ERROR) instead of wedging. Regression test
      `test_unprovable_cutoff_oversized_merge_skips_instead_of_doomed_full_merge` (QG's initial red was a hardcoded
      prod bucket name in that test — fixed to `-prd-test-project`). Deploy to the cron image (MTDS BASE_IMAGE_DIGEST
      bump + rebuild) + the marker-restore recovery + "fresh hourly cycle genuinely merges" verification = todo 3.**
- [x] [SCRIPT] P0. ✅ **Verify recovery end-to-end**: confirm the canonical
      `market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` blob's `generation`/
      `last_modified` has advanced (via UTL `get_storage_client().get_blob_metadata(...)`, never a subprocess
      `gcloud storage`/`gsutil` call — QG-enforced) past `2026-08-18T02:13:57.708000+00:00` /
      `generation=1787019237694916`. If not yet cleared naturally, `gcloud run jobs execute
      uts-prod-manifest-consolidator-market-data-cefi --region=asia-northeast1 --project=central-element-323112`
      (documented SAFE in the SSOT) after the above fix lands. Once confirmed, **re-launch the liquidations re-derive**
      (`cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md`'s own P0 monitor-to-completion item) — the
      contract_size/margin_type fixes are already shipped and correct; this outage was the only remaining blocker.
      **VERIFIED 2026-08-19T22:2xZ — RECOVERY SUCCEEDED (canonical ADVANCED).** Safe marker-restore (per operator
      BLK-f5a54e00 → A): paused cron → cleared rdlhn orphan lock (holder confirmed Completed 21:15:37Z) → metadata-only
      restamp (`consolidator_content_write_at=2026-08-16T22:00:00Z` conservative + `consolidator_run_at=now`, content
      untouched — same gen) → resumed → `gcloud run jobs execute` → execution `6cfs6` completed successfully (46m06s):
      `rows_in=35,898,764 → rows_out=31,103,171`, `dedup_dropped=4,795,593`, `pruned_shards=2000`, `error=-`,
      `incremental=true`, `verdict=produced` (latest.json). Canonical `generation 1787019237694916 →
      1787177809821805`, `last_modified 08-18T02:13:57Z → 08-19T22:16:49Z`, size 443.8→484.7MB; markers freshly
      re-stamped by the merge (native: `consolidator_content_write_at=2026-08-19T21:31:47Z`,
      `consolidator_run_at=22:16:42Z`); lock released. **WEDGE LOOP BROKEN — the consolidator self-healed.** REMAINING
      final step: **re-launch the liquidations re-derive** (`cefi_inverse_contract_size...`'s P0 monitor item) via
      `deployment-service/scripts/vm/launch-mdps-backfill-vm.sh` — known params from the prior launch:
      `cefi 2020-01-01 2026-01-31`, `--data-types liquidations`, `--date-concurrency 2`, `e2-standard-4`; confirm the
      exact prior command from the 2026-08-16 launch record before running a ~2-3 day VM.
- [x] [SCRIPT] P1. ✅ **Investigate why the dedicated liveness watchdog (`uts-prod-consolidator-liveness-watchdog`) did
      not alert** on this 41+-hour outage despite being documented live/healthy (point 5 above) — either fold into
      this fix or file as its own follow-up once root-caused; a watchdog that misses the exact condition it exists
      for is itself a gap.
      **ROOT-CAUSED + FIXED 2026-08-19T~23:1xZ (slot-10) — `unified-trading-library@53abdf72f3`.** Deployed reality
      first (both confirmed live, not from docs): the fast/slow-tier split (`consolidator_liveness_scheduler.tf`) IS
      applied — `uts-prod-consolidator-liveness-watchdog-{fast,slow}-cron`, both ENABLED; `market-data-tick-cefi` is
      on the **slow** tier (hourly-cadence buckets, `15,45 * * * *`, `cycle_sec=3600 cycles_grace=2` → 7200s DOWN
      threshold) since it's one of the 12 categories `manifest_consolidator_schedule` widened to `0 * * * *`. Cloud
      Logging on the slow-tier job at `2026-08-19T21:45:45Z` (mid-outage, canonical frozen since 08-18T02:13:57Z per
      this doc's point 1) shows: `consolidator-liveness: market-data-tick-cefi-prd-central-element-323112 -> ok` —
      **direct proof the watchdog was silently fooled, not merely mis-scheduled.** Traced to
      `unified_trading_library/manifest_writer/_state.py::_consolidator_heartbeat_age_sec`, which PREFERS
      `_consolidator_latest_run_age_sec` (reads `_index/latest.json`'s `last_run_at`) over the canonical blob's own
      mtime. `_index/latest.json` is written on **every** consolidator cycle — including the lock-skip no-op this
      incident's todo 1/2 diagnosed (`success=True, no_op_lock=True, error_reason="locked"`) — by design, per
      `_write_latest_run_summary`'s own docstring ("written on EVERY run … so `last_run_at` always reflects
      liveness"), a 2026-08-18 fix for a DIFFERENT false-positive (`sports_odds_vm_consolidator_stale_stall_2026_08_18.md`,
      a migrator tool bumping the canonical blob's mtime without the consolidator running). That fix's premise —
      "any latest.json write proves liveness" — is false for a locked no-op: the process fired but produced nothing,
      and the SAME lock blocks the next cycle too, so `last_run_at` refreshes forever while the canonical stays
      frozen — exactly this incident (41.6h, zero `CONSOLIDATOR_DOWN` alerts). **Fix**: `_consolidator_latest_run_age_sec`
      now returns `None` (composite reader falls through to the genuinely-stale canonical blob mtime) whenever the
      latest run's own `no_op` + `error_reason=="locked"` — every other no-op shape (idle-touch, unchanged) is
      unaffected, preserving the 2026-08-18 fix's intent. This also restores `assert_consolidator_healthy`'s
      read-path loud-fail for the same condition (shared function). Regression:
      `tests/unit/test_manifest_writer_consolidator_latest_run_locked_noop.py` (3 tests: locked no-op excluded,
      non-locked no-op still counts, composite reader falls back to blob mtime end-to-end — mirrors the exact
      measured contradiction above). QG green (full run, sentinel + post-push ancestry verified). The watchdog's
      running Cloud Run job image has not yet picked up this source change — same MTDS image-rebuild step tracked
      as its own todo below (shared with todo 2's fix; no Cloud Build has been triggered for either yet, so no
      `cloudbuild=<id>` evidence exists to cite here).
- [ ] [INFRA] P2. **Rebuild the `market-tick-data-service:latest` image (MTDS `BASE_IMAGE_DIGEST` bump) so BOTH
      shipped fixes reach their running Cloud Run jobs** — todo 2's `_UNPROVABLE_MERGE_MAX_SHARDS` cutoff (currently
      only live via the manual marker-restore recovery, not the deployed cron image) and this todo's
      `_consolidator_latest_run_age_sec` locked-no-op exclusion (currently live nowhere — the watchdog's Cloud Run
      job still runs the pre-fix image). One rebuild event closes both; cite `Evidence: cloudbuild=<id>` on this
      checkbox once triggered and resolved SUCCESS.

## Progress Log

- **2026-08-19T19:5xZ (plan_reconciler, agt-07473e)**: filed, live-measured as above, alerted via `/blocked` (see
  `plan_reconciler_findings_sports_2026_08_19.md`'s Filed section for the escalation id) and cited into
  `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`'s Progress Log answering the operator's BLK-7d1f4a2d
  live-status-check order.
- **2026-08-19T20:00:32Z**: `BLK-336884f2` answered by operator — **A** (dispatch an engineer/session to
  investigate+fix the consolidator lock now). Doc flipped `assigned_vm: NA` → `assigned_vm: planning` +
  `execution_scope: orchestrator-agent` this same edit, options above converted to tracked `- [ ]` todos, so AO
  backlog regen picks this up per the operator's decision rather than it sitting as inert prose.
- **2026-08-19T20:55Z (slot-4 worker, todo-1 investigation)**: **CONFIRMED the phantom-lock cause — it is a PERPETUAL
  full-merge-timeout-orphan loop, not a single zombie execution.** Both abnormal executions investigated via
  `gcloud run jobs executions describe` + Cloud Logging: `rsgbc` (13:34:59→15:36:14) and `nfgs5` (16:34:58→18:33:05)
  each completed (`succeededCount=1`, `retriedCount=1`) — Cloud Run reaped them, neither is still running. Their logs
  prove each WAS a lock holder: rsgbc cleared a stale lock (age 9812s) and acquired at 13:35:35; nfgs5 cleared rsgbc's
  orphaned lock (age 10790s > 9000s TTL) and acquired at 16:35:25. Both then hit the SAME shape: the canonical carries
  NO `consolidator_content_write_at` marker (`metadata=None`; log "canonical ... has NO consolidator_content_write_at
  marker ... merging all 171620/171781 shard(s)") → fail-closed FULL merge of the 30M-row canonical + ~76M shard rows →
  exceeds the 7200s Cloud Run task timeout → SIGKILL (rsgbc: "Terminating task because it has reached the maximum
  timeout of 7200 seconds"; nfgs5: "Container terminated on signal 9") → SIGKILL bypasses `finally: _release_lock` →
  lock orphaned → every cycle skips with `error=locked` until the lock ages past the 9000s
  `CONSOLIDATOR_LOCK_TTL_SECONDS` override → next cycle clears it, re-acquires, and re-runs the SAME doomed merge.
  **Current holder (measured 20:49Z via UTL `get_storage_client().download_bytes`): `_index/consolidator.lock` PRESENT,
  `started_at=2026-08-19T19:35:23.243115+00:00`, `instance=1-b5a4d4fa` — matches `rdlhn` (19:34:52Z start, STILL
  RUNNING, `Completed: Unknown`), which will hit its 7200s timeout ~21:34Z and orphan the lock a 4th time (prior 2h
  executions today: 10:51→12:52, rsgbc, nfgs5).** Canonical still frozen: `get_blob_metadata` →
  `generation=1787019237694916`, `last_modified=2026-08-18T02:13:57Z`, `metadata=None`; `_index/latest.json` at 20:01Z
  = `verdict=empty, no_op=true, error_reason=locked`. **Conclusion: the simple "reap the zombie" path is NOT
  applicable/safe (the current holder is a live, legitimately-running execution; clearing its lock mid-merge is unsafe
  and the loop re-arms regardless). The durable fix belongs to todo 2 (TTL-based self-healing for the lock AND making
  the missing-marker full merge fit within the 7200s timeout / not re-arm the loop), and todo 3 verifies recovery
  end-to-end after that fix lands.**
- **2026-08-19T21:2xZ (slot-4 worker, todo-2 fix)**: **Code fix shipped-as-commit `unified-trading-library@d8f05a5d` —
  the todo-2 premise is CONTRADICTED by measurement: the lock DOES have TTL/expiry (`_LOCK_TTL_SECONDS`, 300s default,
  9000s override for cefi). The REAL gap is the missing-marker → doomed-full-merge → kill → orphan → re-arm loop.**
  Fix: `_UNPROVABLE_MERGE_MAX_SHARDS` (env `CONSOLIDATOR_UNPROVABLE_MERGE_MAX_SHARDS`, default 50000) — when the
  unprovable-cutoff (missing `consolidator_content_write_at`) merge spans more than that many per-VM shards, the cron
  REFUSES the doomed corpus-wide merge and skips-with-loud-alert instead (`success=False` → CLI exit 1 +
  `MANIFEST_CONSOLIDATION_FAILED` severity=ERROR → pages), so a killed holder's orphan clears after the TTL and never
  re-arms a wedge. Regression test `test_unprovable_cutoff_oversized_merge_skips_instead_of_doomed_full_merge` added.
  **BLOCKED ON SHIP**: unified-trading-library `quality-gates.sh` is red on a PRE-EXISTING codex-py schema-provenance
  violation (not from this commit; offender files at HEAD~1). Filed
  `/plans/active/issues/utl_codex_schema_provenance_qg_red_2026_08_19.md` + declared repo-blocker `qg_red`. Ship via
  quickmerge once green. **Recovery data measured for todo 3** (via UTL native list_blobs, 2026-08-19 ~21:00Z):
  172,028 per-VM shards; **10,717 newer than the last genuine merge (~08-16T23:11Z)**; 1,982 newer than the strip
  rewrite (08-18T02:13:57Z); newest shard mtime 08-19T21:00Z (writers still active). A safe marker-restore recovery is
  VIABLE: restore `consolidator_content_write_at` to the last genuine merge's LISTING time (recoverable from Cloud
  Logging ~08-17T21:18 / 23:50 `phase=shards_listed` lines — the canonical's gen was 1786921866108814 then, rewritten
  to 1787019237694916 at the 08-18T02:13:57 strip), pause cron → cancel/kill holder → restamp (metadata-only) → resume →
  next cycle does an incremental merge of only ~10.7k shards (~10 min, fits the 7200s budget) and re-stamps the marker.
  Current holder at filing: `rdlhn` (19:34Z, still running, will hit its 7200s timeout ~21:34Z and orphan the lock a 4th
  time).**
- **2026-08-19T21:3xZ (slot-4 worker, todo-2 fix — CORRECTION)**: the "BLOCKED ON SHIP: pre-existing schema-provenance"
  claim in the entry above was a **first-person misdiagnosis**. The codex-py `schema-provenance` check is a `log_warn`
  in `base-library.sh` — it does NOT fail `quality-gates.sh`. The actual QG red was the "Hardcoded prod project ID in
  tests" check, tripped by my OWN regression test's bucket name (`market-data-tick-cefi-prd-central-element-323112`).
  Fixed by renaming to `market-data-tick-cefi-prd-test-project` → amended commit `unified-trading-library@af783d92`.
  QG re-run in progress; repo-blocker RB-959c7b8d was resolved via watcher_green and is moot. `/plans/active/issues/
  utl_codex_schema_provenance_qg_red_2026_08_19.md` corrected + demoted to P2 (schema-provenance mis-application to a
  library repo is a quality-of-life warning, not a blocker). Ship via quickmerge once QG is green.
- **2026-08-19T21:4xZ (slot-4 worker, todo-2 ship)**: **Fix SHIPPED `unified-trading-library@af783d92e4` via quickmerge —
  QG green (tests + typecheck + codex PASS, sentinel + ancestry verified), landed on LDR.** The initial QG red was my
  own test's hardcoded prod bucket name (`market-data-tick-cefi-prd-central-element-323112` → tripped "Hardcoded prod
  project ID in tests"); renamed to `-prd-test-project` in the amended commit. **Remaining for the done-when's "fix is
  live + fresh hourly cycle genuinely merges"** (tracked in todo 3): (1) deploy the UTL fix to the cron image — MTDS
  `BASE_IMAGE_DIGEST` bump + rebuild (`market-tick-data-service:latest`), then the consolidator job picks up the new
  digest on its next execution; (2) the safe marker-restore recovery (restore `consolidator_content_write_at` to the
  last genuine merge's LISTING time from Cloud Logging, pause cron → cancel/kill holder → metadata-only restamp →
  resume → next cycle merges only the ~10.7k newer shards, fits the 7200s budget).**
- **2026-08-19T22:2xZ (slot-4 worker, todo-3 — RECOVERY EXECUTED + VERIFIED)**: Operator confirmed the conservative
  marker `2026-08-16T22:00Z` (BLK-f5a54e00 → A) with the guardrail to confirm rdlhn's terminal state first. Executed
  the full recovery: paused the cron (`gcloud scheduler jobs pause`), confirmed rdlhn `Completed` 21:15:37Z (dead),
  cleared its orphaned `_index/consolidator.lock`, metadata-only restamped the canonical
  (`consolidator_content_write_at=2026-08-16T22:00:00Z`, `consolidator_run_at=now`; content untouched — same
  generation), resumed the cron, and `gcloud run jobs execute`d the recovery merge. **Execution `6cfs6` completed
  successfully (46m06s, `succeededCount=1`)** — incremental path confirmed (`phase=shards_downloaded shards=10803`
  vs the doomed 172k), `rows_in=35,898,764 → rows_out=31,103,171`, `dedup_dropped=4,795,593`, `pruned_shards=2000`,
  `error=-`, `verdict=produced` (latest.json `no_op=false`). **Canonical ADVANCED: generation 1787019237694916 →
  1787177809821805, last_modified 08-18T02:13:57Z → 08-19T22:16:49Z, size 443.8→484.7MB; markers freshly re-stamped
  by the merge (native: `consolidator_content_write_at=2026-08-19T21:31:47Z`, `consolidator_run_at=22:16:42Z`); lock
  released. The wedge loop is BROKEN and the consolidator self-healed — readers no longer loud-fail.** REMAINING
  final step (todo-3 done-when's second half): re-launch the liquidations re-derive (`mdps-backfill-cefi` via
  `deployment-service/scripts/vm/launch-mdps-backfill-vm.sh`; known params `cefi 2020-01-01 2026-01-31`,
  `--data-types liquidations`, `--date-concurrency 2`, `e2-standard-4`) — confirm the exact prior launch command from
  the 2026-08-16 record before running the ~2-3 day VM; tracked in `cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md`'s
  P0 monitor item (do not babysit hourly). The UTL guard fix (`af783d92e4`) reaches the cron on the next MTDS image
  rebuild.
- **2026-08-19T21:5xZ (slot-4 worker, todo-3 — verification done; recovery NOT executed, documented for a focused
  follow-up)**: **Read-only verification complete — the canonical is STILL frozen and the loop is STILL active.**
  Measured 21:4xZ via UTL: `_index/availability_index.parquet` `generation=1787019237694916`,
  `last_modified=2026-08-18T02:13:57Z`, `metadata=None` (no content-write marker — unchanged); `_index/consolidator.lock`
  PRESENT, `started_at=2026-08-19T19:35:23` (rdlhn's orphaned lock — rdlhn completed 21:15:37; holder dead), age ~6.5k s
  (< the 9000s TTL, so it blocks cycles until ~22:05Z); `_index/latest.json` `last_run_at=21:15:32`,
  `verdict=empty, no_op=true, error_reason=locked` (rdlhn's retry skipped on its own orphan); executions 20:00 (`th9nd`),
  21:00 (`j79t4`) all skipped-on-lock ~1min. **Recovery NOT executed this session — see handoff below.**
  **RECOVERY PROCEDURE for the executing worker (do this with full attention + confirm the marker value first):**
  (1) **Determine the last GENUINE (marker-present) merge's `phase=shards_listed` listing time** from Cloud Logging
  (before the strip — the doomed attempts from 08-17T21:18 onward already log "NO consolidator_content_write_at marker";
  the issue's ~08-16T23:11Z is an inference; the canonical's pre-strip gen was 1786921866108814). The marker MUST be
  that listing time (or earlier) — a `now`-stamp would classify the ~10.7k unmerged newer shards as "settled" and let the
  next no-op prune DELETE them unmerged (silent loss). (2) PAUSE the cron
  (`gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-cefi-cron --location=asia-northeast1`).
  (3) Clear the orphaned lock (`_index/consolidator.lock`; rdlhn's holder is dead since 21:15Z — safe to delete).
  (4) Metadata-only restamp of `_index/availability_index.parquet` — `consolidator_content_write_at` = the
  last-genuine-listing time (NOT now), `consolidator_run_at` = now; content bytes UNCHANGED (blob.patch(), never a
  re-upload; a CAS re-upload that strips markers would re-arm the loop). (5) RESUME the cron. (6) `gcloud run jobs
  execute uts-prod-manifest-consolidator-market-data-cefi --region=asia-northeast1 --project=central-element-323112`
  (documented SAFE) to trigger the incremental merge of the ~10.7k newer shards (~10 min, fits the 7200s budget) →
  verify `get_blob_metadata` shows a NEW generation. (7) Then re-launch the liquidations re-derive
  (`cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md`'s P0 monitor-to-completion item — VM launch, infra
  territory). **Note: the UTL guard fix (`af783d92e4`) is NOT yet deployed to the cron image** (needs MTDS
  `BASE_IMAGE_DIGEST` bump + rebuild) — but the marker-restore recovery works with the CURRENT image (after restamp the
  incremental path runs normally), and the guard becomes active on the cron once the image is rebuilt.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)

- **2026-08-20T08:04Z (data_pipeline_alerts_reconciler, slot 29, dispatch agt-88ddd3)**: reconciliation re-confirmed
  this remains an alerting/infra follow-up rather than a quiet-channel result. The 24-hour channel read contained 2,609
  messages; live dp-alerting-subscriber errors still recorded repeated Consolidator DOWN and Manifest consolidation
  STALLED messages for CEFI and TradFi market-data buckets. The CEFI consolidator job was enabled and executing on
  schedule, so this is the documented locked/no-op or stale-index class, not a scheduler-dead job. The MTDS image rebuild
  in P2 remains the unresolved deploy-chain step. The earlier 2026-08-19T21:5xZ handoff saying recovery was not
  executed is superseded by the later 22:2xZ entry documenting execution 6cfs6 and canonical-index advancement; retain
  that later entry as authoritative.
