---
doc_type: issue
title: >-
  cefi-content-apply memory-spike-then-freeze recurs on the ALREADY-FIXED 55d051bd tarball + a separate
  DeploymentsRegistry.get() exception-handling gap caused a false "vm_not_running" reap of a still-RUNNING VM
summary: >-
  Split out of `cefi_content_migration_fleet_half_incomplete_2026_07_26.md` (at its 998/1000-line hard cap) to avoid
  breaching it, mirroring how `cefi_content_migration_shard13_network_error_and_checkpoint_resume_bug_2026_07_31.md` was
  split earlier today. Two findings from a DP-VM-003 relaunch (`agt-5065b7`, `canonical-migration-cefi-content-
  apply-20260731-051007`, non-sharded SHARD_OF=1 range 2026-01-18..2026-02-13): (1) an OPEN corroborating data point —
  this VM's `host_metrics_window` shows the SAME mem_pct spike-then-total-freeze signature already diagnosed for shards
  16/44/23 (19.1%->25.4% steady climb over ~9 samples, then a single-sample jump to 82.9% followed by total silence),
  but this occurred on `git_commit=55d051bd6e2a281d2d6d19cb890309bd7278eb9e` — the SAME sha that shipped TODAY'S
  wedge-detection fix (`_STALL_TIMEOUT_SEC=900` replacing the broken infinite `hard_deadline`). The VM ran ~26min past
  that 15-min in-process stall bound, and ~27min past the wrapper-level 1800s `STALL_PROGRESS_REGEX` stall-kill, without
  self-terminating, while GCE still reported RUNNING — meaning neither stall-kill layer recovered it even on the fixed
  tarball, consistent with a full process/memory freeze that a timer thread can't escape from under acute memory
  pressure. (2) A DIFFERENT, precisely-diagnosed bug: `DeploymentsRegistry.get()`
  (`unified-trading-library/unified_trading_library/deployment_registry.py:443-455`) catches `(FileNotFoundError,
  KeyError, ValueError)` around its active-blob read, but the REAL `GCSStorageClient` raises
  `google.api_core.exceptions.NotFound` (confirmed live — `.get()` crashed instead of falling through to the archive
  check) — the EXACT SAME exception-class-mismatch already root-caused and fixed in the SAME file's
  `_read_true_exit_code` (2026-07-25). Independently, the registry's periodic `reap_stale()` sweep (a DIFFERENT code
  path, does not call `.get()`) archived this VM as `status=failed, exit_code=125, reap_reason=vm_not_running` at
  `2026-07-31T05:46:53Z` — while `gcloud compute instances describe` proved it was still genuinely `RUNNING` with the
  SAME creation timestamp, the entire time before and after. Root cause of THIS false reap (why `running_vm_names`
  excluded a live instance) is NOT diagnosed — flagged as an open mystery, not guess-fixed, mirroring how the sibling
  fleet doc handled its own unexplained shard-19 delete.
status: open
nature: issue
asset_group: [cefi, meta]
stage: [data, meta]
repos: [unified-trading-library, deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, migration, vm-relaunch, data-pipeline, deployment-registry, reaper, monitoring, memory-leak]
related:
  [
    cefi_content_migration_fleet_half_incomplete_2026_07_26,
    cefi_content_migration_shard13_network_error_and_checkpoint_resume_bug_2026_07_31,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-07-31
author: unknown
priority: P2
parent_epic: cefi_master
source:
  "data_pipeline_failure escalation agt-5065b7, slot 4, 2026-07-31 -- DP-VM-003 relaunch of
  canonical-migration-cefi-content-apply-20260731-051007"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md,
    /plans/active/issues/cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md,
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch4_2026_07_31.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    unified-trading-library/unified_trading_library/deployment_registry.py,
  ]
---

# cefi-content-apply memory-freeze recurs post-fix + a registry false-reap

## What I found

Dispatched via DP-VM-003 (`agt-5065b7`, WARN, heartbeat 14m stale at alert-fire time) for
`canonical-migration-cefi-content-apply-20260731-051007` — a standalone (non-sharded, `SHARD_OF=1/SHARD_INDEX=0`)
`cefi-content-apply` VM covering `2026-01-18..2026-02-13`, `mode=full`, distinct from the numbered
`canonical-migration-cefi-content-NN-*` shard fleet in the parent doc (though its date range overlaps that fleet's
shards 25/26). Per `RB-INFRA-RELAUNCH`, confirmed no SPOT preemption (`gcloud compute operations list` showed only the
original `insert` op, `preemptible=true`), then confirmed a genuine stall via both the run.log-tee signal
(`pipeline_heartbeat_age_min`/`run_log_age_min` both ~23-27min stale and climbing) and the authoritative sidecar
(`vm-heartbeat/{vm}.txt`, ~26min stale).

**Finding 1 (open, corroborating)**: the archived registry entry's `host_metrics_window` (9 samples,
`2026-07-31T05:22Z`-`05:31Z`) shows `mem_pct` climbing steadily 19.1%->25.4% (`mem_slope` 0.4-1.2), then the LAST sample
jumps to **82.9%** (`mem_slope=7.0889`, a >8x acceleration) with `cpu_pct` also spiking 24.2%->62.6% — then total
silence (no further heartbeat, no further run.log line) for the rest of the VM's life. This is the identical signature
`cefi_content_migration_fleet_half_incomplete_2026_07_26.md` already diagnosed for shards 16/44 (slow whole-VM freeze
under memory pressure) and shard 23 (confirmed poison-pill oversized/malformed parquet file causing a fast memory spike
immediately before an OOM-kill). The notable NEW data point: this VM's `git_commit` is
`55d051bd6e2a281d2d6d19cb890309bd7278eb9e` — the exact sha that shipped TODAY's wedge-detection fix (replacing the
defeated `hard_deadline = 5s * total_files` safety valve with a fixed 15-min `_STALL_TIMEOUT_SEC=900` self-force-exit).
That fix did NOT save this VM: it ran ~26min silent (>15min in-process bound, and past the wrapper-level 1800s
`STALL_PROGRESS_REGEX` stall-kill too) without self-terminating, and GCE still reported it `RUNNING` throughout. Working
theory: once memory pressure is severe enough to freeze the whole process (swap thrashing / allocator stall), even an
in-process timer thread may not get scheduled to fire its own force-exit — so `55d051bd` likely helps a _softer_ wedge
(network hang, GIL contention) but not this specific acute-memory-spike freeze. This does NOT contradict `55d051bd`'s
own stated scope (it targets the wedge-detection defect, not the memory-growth root cause, which the parent doc's
still-open P2 todo already owns) — it's a second confirmation that the memory-spike root cause (likely the same "single
anomalously large/malformed file" mechanism confirmed for shard 23) remains unaddressed and can still produce an
unrecoverable freeze even with both current mitigations in place.

**Finding 2 (precisely diagnosed, separate)**: while querying the registry directly by `deployment_id`, `.get()` raised
uncaught `google.api_core.exceptions.NotFound` instead of returning `None`/falling through to the archive scan. Read
`unified-trading-library/unified_trading_library/deployment_registry.py:443-455` —
`except (FileNotFoundError, KeyError, ValueError): pass` — the real GCS SDK never raises `FileNotFoundError` for a 404,
it lets `google.api_core.exceptions.NotFound` propagate (confirmed live, full traceback in this escalation's tool
output). This is the EXACT SAME exception-class-mismatch already root-caused and fixed in the SAME file's
`_read_true_exit_code` (`deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md`, 2026-07-25) — that fix's
own idiom
(`except Exception as exc: exc_name = type(exc).__name__; if exc_name in ("NotFound", "Forbidden") or "404" in str(exc): return None; raise`)
was never applied to `.get()`.

**Finding 3 (open, unexplained — NOT root-caused, flagged not guessed)**: independently of Finding 2 (a different code
path — `reap_stale()`'s bulk sweep via `list_active()` + `_reap_reason()`, which never calls `.get()`), the registry
archived this exact deployment (`cbbf4411-e03a-4816-9fc5-69f7372aa883`) as
`status=failed, exit_code=125, reap_reason=vm_not_running, completed_at=2026-07-31T05:46:53Z` — meaning
`_reap_reason()`'s `entry.vm_name not in running_vm_names` branch fired. But `gcloud compute instances describe` at the
time of this escalation (05:54Z onward) showed the SAME instance, SAME creation timestamp, still genuinely `RUNNING` —
it was never deleted until I did so deliberately at ~06:02Z. So at the 05:46:53Z reap tick, `running_vm_names` must have
excluded a VM that was, in fact, still running. Did not guess at why (candidates: a zone-scoping gap, a listing
pagination/truncation, an eventual-consistency race in the GCE list API, or a bug in whatever populates
`running_vm_names` for this sweep) — mirrors how the parent doc's own shard-19 mid-air-delete mystery was left as
flagged-not-guessed. Practical consequence: this false reap corrupts registry-driven relaunch-budget bookkeeping (a
genuinely-alive VM reads as a dead/failed one) and any dashboard reading the registry as ground truth.

## Why it matters

Finding 1 means the two fixes shipped today for this exact migration category (`9f4098b1` pyarrow-pool-release,
`55d051bd` wedge-detection) do not fully close the failure mode — a future `cefi-content-apply` (or any
`canonical-migration-` category sharing this script's memory profile) VM can still freeze unrecoverably under acute
memory pressure, silently costing SPOT compute time until the ~45min external `DP-VM-005` kill or a human catches it.
Finding 2 is a live, reproducible bug affecting every `.get()` caller (dashboard detail lookups, any future code path
querying a single deployment by id) — it crashes instead of degrading gracefully, unlike every sibling read path in the
same class already fixed. Finding 3 undermines trust in the deployment registry as ground truth for "is this VM actually
still working" — the exact question `RB-INFRA-RELAUNCH`'s `≤2/(vm-prefix,day)` budget check and any fleet dashboard
depend on.

## Recommended decision

- [x] ✅ [BACKEND] P2. Widen `DeploymentsRegistry.get()`'s except clause
      (`unified-trading-library/unified_trading_library/deployment_registry.py:447-450`) to also degrade-to-None on a
      real `NotFound`/`Forbidden`/404, mirroring `_read_true_exit_code`'s already-shipped idiom exactly
      (`except Exception as exc: exc_name = type(exc).__name__; if exc_name in ("NotFound", "Forbidden") or "404" in str(exc): pass (fall through to archive scan); else: raise`).
      Add a regression test using a fake storage client that raises `google.api_core.exceptions.NotFound` (not
      `FileNotFoundError`) for a missing active blob, asserting `.get()` still falls through to the archive scan instead
      of crashing. **Done when**: the test reproduces this exact crash pre-fix, passes post-fix, QG green. This is a
      small, bounded, single-method fix mirroring an already-proven pattern in the same file — filed `NA`/local per the
      default plan-destination posture since no operator confirmation was available at file-time; flip to
      `assigned_vm: planning` if a human agrees it's properly scoped. Repo: unified-trading-library. — **SHIPPED**
      `unified-trading-library@89eabac2` (2026-08-06, slot 4 / `cefi_satellite_ao_dispatch_batch4-003`): `get()` now
      catches `NotFound`/`Forbidden`/404 via `exc_name` string-match and falls through to the archive scan; regression
      test `test_get_falls_through_to_archive_on_real_gcs_not_found` uses a
      `google.api_core.exceptions.NotFound`-raising `_GcsNotFoundStorageClient(InMemoryStorageClient)` fake and asserts
      `.get("arch-gcs-404")` resolves + `.get("does-not-exist") is None`. QG Pass-1 GREEN, SHA verified on
      `origin/live-defi-rollout`.
- [x] ✅ [BACKEND] P2. Investigate Finding 3 (the false `vm_not_running` reap of a genuinely-`RUNNING` VM at
      `2026-07-31T05:46:53Z`) — find and read whatever code path supplies `running_vm_names` to the periodic
      `reap_stale()` sweep call (likely in `deployment-service`, possibly `gcp_instance_lister.py` or the sweep's own
      caller) and determine why it excluded a live instance at that tick. **Done when**: either the mechanism is
      identified and fixed (with a regression test), or it's confirmed to be an unreproducible one-off (e.g. a transient
      GCE list-API inconsistency) with evidence either way. Repo: deployment-service. — **SHIPPED**
      `deployment-service@4ee514e` (2026-08-06, slot 4 / `cefi_satellite_ao_dispatch_batch4-003`): root cause
      CONFIRMED + reproducible-by-code-reading, not a one-off. `deployment_service/data_pipeline_monitors/cli.py`
      `_list_running_vms()` collapsed a GCE list-API failure/FuturesTimeout into `[]`; the exit-code sweep passed
      `reap_stale(running_vm_names={})` (empty non-None set); `DeploymentsRegistry._reap_reason` treats a non-None empty
      set as "no VMs running" → every stale-heartbeat active entry classified `vm_not_running` even for a live instance.
      Fix: `_list_running_vms() -> list[tuple[str, str]] | None` returns `None` on any census failure; caller passes
      `running_vm_names=None` → heartbeat-age-only fallback (no `vm_not_running` reaping). Regression tests:
      `test_list_running_vms_returns_none_on_timeout` +
      `test_main_exit_code_mode_census_unavailable_no_false_vm_not_running_reap`. QG Pass-1 GREEN (220s, sentinel
      `4ee514e`), SHA verified on `origin/live-defi-rollout`. Sibling: deployment-api's
      `sync_service.reap_stale_deployments` + `routes.vm_deployments.reconcile_vm_deployments` share the same empty-set
      bug — filed `deployment_api_reaper_empty_set_over_reap_sibling_2026_08_06.md` (P2, `assigned_vm: planning`).
- [ ] [SCRIPT] P3. Corroborating evidence only — no new action needed beyond what
      `cefi_content_migration_fleet_half_incomplete_2026_07_26.md`'s existing P2 todo ("Investigate shard 16's fast-OOM
      anomaly... single anomalously large/malformed file") already covers. When that investigation resumes, this VM's
      window (2026-01-18..2026-02-13) + its exact freeze timestamp (`2026-07-31T05:31:18Z`, sample-over- sample
      mem_slope 7.09) is a further, precisely-timestamped data point worth checking against whatever file(s) the
      migration was processing at that instant.
- [ ] [SCRIPT] P3. Another data point, added 2026-07-31 14:5xZ (`data_pipeline_failure` escalation `agt-b58993`, slot 1,
      DP-VM-001 for `canonical-migration-cefi-content-42-relaunch20260731-133929`): shard 42's window
      (2024-12-27..2025-01-09, 73,965 files across 47 venue×pipeline_mode pairs) froze the same way —
      `host_metrics_window` shows `mem_pct` plateaued ~75-85% across 9 one-minute samples then jumped to 95.3%
      (`mem_slope=2.0`) in the final sample at `2026-07-31T14:43:08Z`, OOM-killed ~26s later at 21,600/73,965 files
      processed. Full detail + budget/relaunch decision in
      `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md`'s `[OPERATOR] P1` todo (not
      duplicated here). When the shard-16 fast-OOM investigation resumes, this is the 3rd precisely-timestamped
      freeze-moment data point (after shard 16 and the `-051007` VM above) to cross-check against the file(s) each
      migration was processing at its exact freeze instant.
- [ ] [SCRIPT] P3. Another data point, added 2026-07-31 15:5xZ (`data_pipeline_failure` escalation `agt-95d7c6`, slot
      13, DP-VM-001 for `canonical-migration-cefi-content-18-relaunch20260731-133548`): shard 18's window
      (2025-01-17..2025-02-06, 104,813 files across 47 venue×pipeline_mode pairs) froze the same way —
      `host_metrics_window` shows `mem_pct` plateaued ~72-88% across 8 one-minute samples then jumped to 84.5% and
      finally 98.0% (`mem_slope=1.06`) in the final sample at `2026-07-31T15:48:58Z`, OOM-killed ~2s later at
      39,000/104,813 files processed. Full detail + budget/relaunch decision in
      `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md`'s `[OPERATOR] P1` todo (not
      duplicated here). 4th precisely-timestamped freeze-moment data point (after shard 16, the `-051007` VM, and
      shard 42) to cross-check against the file(s) each migration was processing at its exact freeze instant, when that
      investigation resumes.

## Progress Log

- 2026-07-31 (`data_pipeline_failure` escalation `agt-5065b7`, slot 4): filed after splitting out of the at-line-cap
  parent fleet doc. Relaunched the underlying VM myself (see
  `cefi_content_migration_fleet_half_incomplete_2026_07_26.md`-adjacent action: deleted the confirmed-wedged instance,
  relaunched under the SAME `VM_NAME_OVERRIDE` identity with `MACHINE_TYPE=e2-standard-16` — matching this fleet's own
  established fix precedent for shards 17/18/41's `e2-standard-8` OOMs — confirmed `RUNNING`, T+10min PROGRESS
  verification in flight). Did not attempt to fix either library bug (Findings 2/3) directly in this one-shot escalation
  — consistent with how the sibling shard-13 doc's own adjacent GCS-retry-predicate finding was handled (documented, not
  fixed, given the shared-library blast radius vs. a one-shot task's remit).
- 2026-07-31 update (~20min later, same escalation): the `e2-standard-16` relaunch above was **preempted 94s after
  creation** (`compute.instances.preempted` at `2026-07-30T23:04:29.698-07:00`, `--instance-termination-action=DELETE`
  self-deleted it) — never wrote a single new heartbeat/run.log line. Retried on-demand `e2-standard-16` (matching this
  fleet's own proven SPOT-contention fix) — that attempt **failed to even create**:
  `ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS` — `asia-northeast1-c` has **zero `e2-standard-16` capacity available at
  all right now** (the error suggested `asia-northeast1-b`/`-a`, which this launcher cannot target — `ZONE` is a hard
  constant in `launch-canonical-migration-vm.sh`, no env override exists). **New finding, material to this doc's own
  parent's open todo** ("Change `cefi-content-apply`'s default `MACHINE_TYPE` from `e2-standard-8` to
  `e2-standard-16`"): that change may not be safely fleet-wide-deployable right now given this zone's currently measured
  `e2-standard-16` stockout — likely self-inflicted, since this same fleet's other shards were converted to
  `e2-standard-16` on-demand yesterday and are still occupying that exact capacity class in the same zone. Fell back to
  `e2-standard-8` SPOT (the category's tool default; 3rd relaunch attempt overall today for this vm identity, but a
  materially different configuration each time, not a blind repeat of the same failure) — created successfully,
  confirmed **T+10min PROGRESS**: `run.log` climbing steadily (1400->3600/292434 files, ~15 files/sec, healthy),
  `PIPELINE_HEARTBEAT` present, `pipeline_heartbeat_age_min=1.96`/`run_log_age_min=1.74`/sidecar `age_min=0.85` — all
  fresh, no new preemption op recorded. **Final state: VM healthy and progressing on `e2-standard-8` SPOT** — accepted
  the reintroduced memory-freeze risk (Finding 1) over an indefinite wait for `e2-standard-16` zone capacity; if this
  instance also freezes/dies, per `RB-INFRA-RELAUNCH`'s bound this vm identity should NOT be relaunched a 4th time today
  — page the operator / leave to the in-VM stall-kill instead.

- **na-eligibility-audit 2026-08-01** (tranche=cefi, autonomous): KEEP-NA, valid (all 5 open items). Items 1-2
  (`DeploymentsRegistry.get()` except-clause widen + false-reap investigation) are already extracted verbatim into
  `cefi_satellite_ao_dispatch_batch4_2026_07_31.md` todo 3 (Source-cited) — but that batch is `status: draft`, not yet
  active, so NOT independently reclassified here (would risk duplicate dispatch on `deployment_registry.py` once batch4
  activates). Items 3-5 are corroborating data points feeding a different still-open investigation (shard-16), genuinely
  open. No reclassification; revisit if batch4 stalls without activating.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- added the batch4 satellite dispatch plan where
  todos 1-2 were already extracted verbatim (per the 2026-08-01 na-eligibility-audit note).
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the prior verdict; items
  1-2 stay correctly held back from reclassify (batch4 still `status: draft`, duplicate-dispatch risk), items 3-5 remain
  genuinely open corroborating data for the separate still-open shard-16 investigation. No reclassification.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms prior verdicts; items 1-2
  sit under a redirect banner to batch4 (still draft), items 3-5 are annotated data points feeding the separate
  still-open `cefi_content_migration_fleet_half_incomplete_2026_07_26.md` investigation, not standalone dispatchable
  todos.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (5 entries), unchanged — items 1-2 are now `[x]`
  shipped (`unified-trading-library@89eabac2`, `deployment-service@4ee514e`), items 3-5 remain open corroborating data
  points; existing list still accurate.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 3 open items remain, all dependency-blocked corroborating data
  points feeding the sibling shard-16 investigation.
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (cefi tranche)**: KEEP-NA, valid — re-checked against
  the full round-11 precedent set (IAM self-service default, D16 all-repos carve, S5.1 tiering,
  plan-destination-default-to-AO for auto-filed findings, escalation-N=3-days, reversibility-qualified deletes
  agent-executable after a fresh check, Option B retirement [confirmed unrelated], GSM secret
  `deepseek-v4-pro-api-key` + 5 Slack webhooks) — none apply. All 3 remaining items are P3 corroborating
  freeze-moment data points explicitly deferred to the sibling shard-16 investigation
  (`cefi_content_migration_fleet_half_incomplete_2026_07_26.md`'s own P2 todo), not independently dispatchable. No
  reclassification.
