---
doc_type: plan
title: "ao_open_work_consolidated_tracker — Track 4 (Infra / VM / host hygiene) extracted history"
summary: >-
  Fully-closed Track 4 section extracted verbatim from
  /plans/active/ao_open_work_consolidated_tracker_2026_08_14.md to bring that still-active tracker back under
  its 1000-line hard cap (2026-08-19, was at 1001 lines after real DB-pool-P3 + NVIDIA-concurrency-baseline
  evidence appends). Every item here was already [x] DONE at extraction time — nothing here changes any todo's
  done-when status. Pure archival record, per the plan-authoring template's finding J (extract oldest
  fully-closed sections as you go).
status: complete
nature: record
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, infra, vm, host-hygiene, history, extracted]
related: [/plans/active/ao_open_work_consolidated_tracker_2026_08_14.md]
created: "2026-08-19"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
assigned_role: infra
drift_direction: none
resolved_by: extraction-only, no new resolution
locked_by:
depends_on: []
source: >-
  Verbatim extraction from ao_open_work_consolidated_tracker_2026_08_14.md's Track 4 section (lines 343-477 as
  they stood 2026-08-19), done to relieve that file's 1000-line hard cap breach.
context_scope: [/plans/active/ao_open_work_consolidated_tracker_2026_08_14.md]
---

# `ao_open_work_consolidated_tracker` — Track 4 (Infra / VM / host hygiene) extracted history

- [x] [CREDS] P0. **DONE — CONFIRMED ALREADY IN SYNC, 2026-08-15 (this session, direct SSM check).** The staged write
      was never needed: vm-0's live `ORCHESTRATOR_JWT_SECRET` and the `ORCHESTRATOR_ENV_LOCAL` SM blob already matched
      at check time (compared equal without printing either value), confirmed authoritatively via
      `bash scripts/refresh_env_from_sm.sh` dry-run on vm-0: `add=0 replace=0 keep=7`,
      `DRY-RUN: in sync, nothing to do`, JWT included. No write performed — this item is genuinely closed, not deferred.
      Source: `/plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md` — checkbox flipped there too.
- [x] [BACKEND] P0. **DONE — LIVE FIX APPLIED 2026-08-16 (this session, direct SSM).** `planning`'s own
      `orchestrator.service` (`.env.local`, `EnvironmentFile=-`) was missing `ORCHESTRATOR_VM_ID` entirely — confirmed
      by `env` on the live `MainPID` (empty) vs. the still-running `deepseek_native_proxy_server` process (up since
      2026-08-13, environ carried `ORCHESTRATOR_VM_ID=planning`), proving the line existed before and dropped out of
      `.env.local` sometime between then and orchestrator.service's most recent restart (08:54:18Z today). Effect:
      `server_url()`'s `is_standalone()` guard (the 2026-07-29 local-pilot-incident fix) fired on **every** escalation
      dispatch fleet-wide — confirmed via `GET /api/escalations/active`: `agt-09c955` (instruments-service,
      `cloud_build_failure`) stuck at 238 failed attempts, `agt-95ede4` (market-tick-data-service,
      `data_pipeline_failure`) at 313 attempts / 5 re-escalations, both `last_error: "server_url unresolved: ...
      standalone instance (vm_id='')"`. Restored `ORCHESTRATOR_VM_ID=planning` to `.env.local` (backed up first) and
      `systemctl restart orchestrator` (`KillMode=process` — tmux workers unaffected); verified new `MainPID`'s environ
      carries the value, `/api/backlog` returns 200, and `agt-95ede4` flipped to `status: dispatched, last_error: null`
      on the next retry tick (~90s later) — confirmed live, not just code-read. No source doc existed for this before
      today; tracked here per the operator's "plug into the 14th consolidated tracker, don't file a new doc" direction.
- [x] ✅ [DIAG] P1. **Root-cause found + preventive fix shipped 2026-08-17 (slot-6, infra worker,
      `ao_satellite_ao_dispatch_batch21`).** Mechanism confirmed had NEW forensic evidence: `planning` accumulated 6
      `.env.local.bak.*` files by 2026-08-16 (2 pre-existing + 4 new same-day); exactly ONE
      (`.env.local.bak.1786877088`) carries **zero** `ORCHESTRATOR_*` keys at all — every other backup, before and
      after, carries them normally. That is the exact signature of `bootstrap_vm.sh` STEP 5b's raw `echo ... >
      ${ENV_LOCAL}` overwrite (correct only for a FRESH VM per the step's own header comment) having run WITHOUT
      reaching the identity-var re-add (`_upsert_env ORCHESTRATOR_VM_ID`, STEP 5b-append) a few lines later in the SAME
      `else` block — only reproducible by a partial/killed run, or any caller invoking just the SM-blob-fetch logic in
      isolation, against an already-provisioned host. The exact trigger (which process/redeploy path ran it) is NOT
      identified — no root crontab visibility and no `.bash_history` hits from this sandboxed worker's vantage point —
      but the mechanism itself is now pinned to a specific, evidenced code path rather than the prior best-guess.
      **Preventive fix shipped** (`agent-orchestrator@bc9835a38d`): STEP 5b now checks whether `${ENV_LOCAL}`
      already exists and already declares `ORCHESTRATOR_VM_ID` (= an already-provisioned host) — if so it UPSERTS the
      Secret-Manager blob's keys in place (same technique `refresh_env_from_sm.sh` already uses) instead of the
      destructive overwrite, so no VM-specific key can be dropped by this step again regardless of what triggers it or
      whether the run completes. A genuinely fresh VM (no prior `ORCHESTRATOR_VM_ID`) still gets the original
      overwrite-then-upsert path unchanged.
- [x] [BACKEND] P0. **DESIGN RESOLVED 2026-08-15 (this session, operator discussion) — no longer operator-blocked, now
      bounded implementation work.** Design the dirty-worktree resolution policy (Ikenna, Slack 2026-06-12). Operator
      confirmed the revision directly in-session: keep steps 1-2 unchanged (QG-green→quickmerge /
      fixable→fix+quickmerge), **replace steps 3-4 (hand to operator / operator-sanctioned hard-reset) with a single
      step 3: not-easily-fixable → `git stash` and proceed with the next task, never block on a human** — reasoning: an
      operator response won't arrive fast enough, so the slot just sits idle until something else times it out and kills
      it anyway; better to let the slot resolve itself. **New finding from this discussion**: stashing must be paired
      with a bounded-retention sweep (age out stash/`wip-preserve/*` refs past ~7 days) — the accumulation risk is not
      hypothetical, this session directly observed 47 autostash entries piling up on this exact host with nothing
      pruning them. Full resolved spec + both required deliverables (worker prompt template + dispatch hook; retention
      sweep) written into the source doc. Source: `/plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md` — checkbox
      flipped there too.
- [x] ✅ [DIAG] P2. Best-effort root-cause the 49.3G/16G-swap peak — DONE 2026-08-17 (slot 10, batch21 todo 5; reconciled
      batch21_finalize todo 2). Original peak best-effort-exhausted (predates resource-watchdog); redirected to
      resource-watchdog's own kill corpus — 187 kills/7d, 25 >10GB RSS, all tracing to 4 unbounded CEFI-manifest scripts
      in `market-tick-data-service/scripts/` (new follow-up filed there). Source:
      `/plans/archive/2026_08/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md`.
- [x] [REVIEW] P2. **DONE — confirmed live 2026-08-15 (this session, direct SSM check).** Zero kernel OOM-killer hits
      host-wide in the last 30 days (`journalctl -k`, no root needed — the orchestrator's own service user,
      `ubuntu`/group `adm`, can already read this). Ruled out cleanly. Source: same doc.
- [x] [BACKEND] P2. **DONE — shipped `agent-orchestrator@3b4a329`** (2026-08-15). New `ReadinessWatchdog`
      (`server/readiness_watchdog.py`), mirroring `DiskSpaceCanary`'s shape: polls the same `select(1)` probe
      `/api/readiness` already runs, every 30s; after 5 consecutive failures (~2.5min) calls `os._exit(1)` — confirmed
      no `systemd-notify`/`sd_notify` convention exists anywhere in this repo, and `orchestrator.service` is
      `Type=simple` with `Restart=on-failure`/`RestartSec=10` already declared, so a process exit is the correct
      trigger. Wired into `server.py`'s lifespan; new `notify_readiness_watchdog_restart` Slack alert. Source:
      `/plans/archive/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` — flip its checkbox too.
- [x] [BACKEND] P3. **DONE 2026-08-19 — design fork resolved, tracker entry was stale.** The "batch/serialise
      per-slot git-status writes" alternative was implemented: `agent-orchestrator@996e98ef73` (+ stale-comment
      follow-up `agent-orchestrator@da056d128e`) routes every `POST /api/slots/{id}/git-status` write through a new
      single-worker `ThreadPoolExecutor` (`_GIT_STATUS_WRITER`, `server/routes/git_health.py`), so at most ONE DB
      connection is ever held for that route regardless of concurrent slot fan-in. New
      `tests/test_git_status_write_serialized.py` proves `max_active == 1` under 12 concurrent threads on a
      `threading.Barrier`. Source doc `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` is itself now
      `status: resolved` + archived (all 5 of its own todos closed) — this tracker (dated 2026-08-14) simply hadn't
      caught up. Found + fixed while triaging this exact item for the operator, 2026-08-19, this session.
- [x] [BACKEND] P2. **DONE (backend) — shipped `agent-orchestrator@ca6603a`** (2026-08-15). New
      `cgroup_memory_snapshot()` in `host_resources.py`: cgroup v2 preferred (`memory.current/high/max/swap.current`,
      confirmed via `cgroup.controllers`), v1 fallback (`usage_in_bytes`/`limit_in_bytes`/`memsw.usage_in_bytes`, v1's
      finite-sentinel "unlimited" handled distinctly from v2's literal `"max"`), `None` when neither exists — never
      raises. Wired into `snapshot()` → `HostResources` (`cgroup_available`/`cgroup_mem_pct` + raw byte fields), which
      `resource_history.py`'s sampler already serializes wholesale, so `/ws/vm-resources` picks it up with no further
      wiring. **A dashboard UI tile is explicitly NOT built** (out of scope for this pass, backend-only) — remains a
      genuine follow-up if the operator wants the data surfaced visually, not just available over the WS feed. Source:
      `/plans/archive/issues/orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`.
- [x] ✅ [DATA] P2. Audit `unified-trading-system-repos/` (157G) for cleanup headroom — DONE 2026-08-17 (slot 6, batch21
      todo 6; reconciled batch21_finalize todo 2). Found ~57.2G confirmed-dead `.tmp/` scratch across 5 repo worktrees
      (audit-only, no deletes — gated by `block_destructive_commands.py`). Full manifest in the issue doc. Source:
      `/plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md`.
- [x] ✅ [DATA] P2. Investigate `/home/ubuntu/mdps_bench_data_fullmonth/` (3.8G) — DONE 2026-08-17 (slot 18, batch21
      todo 7; reconciled batch21_finalize todo 2). Owned by the already-closed full-month MDPS engine benchmark
      (`mdps_engine_comparison_2026_05_28`); results durably persisted. Disposition: safe to archive/delete. Source:
      same doc.
- **[SCRIPT] P3. CANCELLED — SUPERSEDED 2026-08-15 (reconciliation sweep, this session).** Was: bump `PYRIGHT_TIMEOUT`
  if a QG kill recurs. Already closed 2026-08-12 by `/plan-reconcile`: the kill DID recur (9 occurrences,
  `pytest_timeout_60s_flaky_under_contention*` doc-chain) but that investigation explicitly rejected a timeout bump
  ("same capacity-side root cause, not a per-repo timeout raise") — the real, already-adopted fix is the
  resource-reservation admission governor (`/plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`, active),
  matching the fleet's "QG concurrency is RESOURCE-based" policy. Source:
  `/plans/archive/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md`.
- [x] [REVIEW] P3. **DONE — shipped `agent-orchestrator@426e8cf55` TODAY (2026-08-15).** New `server/host_tombstone.py`:
      `is_host_tombstoned()`/`tombstoned_since()`, `ip-172-31-0-185` hardcoded as a fail-safe floor + live AWS EC2
      existence check for future ghost hosts. Resolved the design fork as tombstone-never-prune (row stays for audit
      trail); wired into `models/git_health.py` + `routes/git_health.py:361,428` to exclude tombstoned hosts from
      fleet-wide stale/drift totals. Verified 2026-08-15 (reconciliation sweep, this session, same day as the shipping
      commit). Source: `/plans/archive/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` — flip its
      checkbox too.
- [x] ✅ [OPERATOR] P2. **DONE 2026-08-16 (interactive session, operator-approved quiet moment — only 1 task actively
      dispatched fleet-wide).** Dry-run + live-apply both completed cleanly against the content-derived-task-id
      migration: 2037 rows renamed, hazard-2 gate 0 unexplained across 673 references, 0 dispatched rows touched,
      `REFUSING to reset` count 0 immediately post-apply. Full evidence in the source doc's own flipped checkboxes.
      Source: `/plans/archive/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md` (tracked live in
      `/plans/active/content_derived_backlog_task_ids_2026_08_08.md`, do not duplicate there).
- [x] [REVIEW] P2. **DONE — shipped `agent-orchestrator@c6d43ac`** (2026-08-14).
      `worktree_clean_check/_ahead_push.py::push_or_preserve_ahead_commits` (lines 262-283): on a rejected push,
      re-verifies against the new HEAD, restamps the sentinel (`_restamp_sentinel_at_head`), and emits a distinct
      `ahead_push_rejected_and_stale` event. Regression:
      `test_sweep_rejected_push_restamps_sentinel_and_flags_rejected`. Verified 2026-08-15 (reconciliation sweep, this
      session). Source:
      `/plans/archive/issues/ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md` — flip + archive
      if now 0 open todos.
- [x] [REVIEW] P2. Per-occurrence audit of the ~14 `BLOCKED-PREREQ` files in the active corpus (external-gate-mislabel
      vs. same-corpus-dependency), then re-grep-and-confirm as a follow-up. Source:
      `/plans/active/issues/blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md`. **DONE
      2026-08-14** — the ~14-file population had shrunk to exactly 2 files / 6 live occurrences by re-check time (rest
      already fixed/archived independently since 2026-07-28). All 6 classified as genuine case-(b) same-corpus
      dependencies (none mislabeled-external), confirmed still genuinely blocked as of 2026-08-14, full disposition
      table in the source doc's Progress Log. Both of the source doc's own todos closed; spawned 1 new tracked follow-up
      (`[BACKEND] P3`, the residual `agent-orchestrator` design question) — doc correctly stays open, not archived (real
      design work remains).
- [x] [REVIEW] P3. **DONE — shipped `agent-orchestrator@2c8302c`** (2026-08-14). `_upstream_plan_open_on_disk()`
      (`server/regen_backlog_from_plan.py:2483-2516`) is now the single shared definition used by BOTH
      `_wire_gate_on_depends_prereqs` and `gate_on_depends_unmet_upstreams_on_disk`, including the checkbox-scan
      fallback (`_plan_has_any_unchecked_checkbox`) this todo asked for. Verified 2026-08-15 (reconciliation sweep, this
      session). Source: `/plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` — flip
      its checkbox too.
