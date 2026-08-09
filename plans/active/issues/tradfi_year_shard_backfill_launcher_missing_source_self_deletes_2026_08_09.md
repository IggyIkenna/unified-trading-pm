---
doc_type: issue
title: >-
  launch-tradfi-backfill-vm.sh's VM_TASK=cefi-backfill matched no dispatch branch — every year-shard VM self-deleted
  within 2-4 minutes, 0 data written; fixed VM_TASK=mtds-backfill + VM_SOURCE=databento
summary: >-
  While executing batch6 todo #2 (ES_OPT launch), 5 freshly-launched `tradfi-bf-es-opt-*` VMs were each deleted by
  `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` within 2-4 minutes of insert, 0 data written. Root cause:
  `launch-tradfi-backfill-vm.sh`'s `_create_vm()` sets `VM_TASK=cefi-backfill`, but `setup-data-pipeline-vm.sh` has no
  dispatch branch for that value at all (verified via full text search — only `mtds-backfill` exists), so every VM fell
  through to the generic fallback, which never appends `--source` to the MTDS CLI. MTDS hard-fails immediately
  ("--source databento is REQUIRED for a TradFi OHLCV download"), writes 0 rows, and the VM self-deletes via its own
  `VM_SHUTDOWN_ON_COMPLETION=true` convention. This is NOT an external killer, NOT a billing kill-switch, and NOT the
  same root cause as `cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md` (that doc's Claude-Code-agent-
  manual-delete finding, principal `unified-trading-sa`, is unrelated — this incident's deleter is `uts-prd-sa`, the
  VM's own attached service account self-terminating per its normal completion contract, just triggered by an immediate
  failure rather than a real completion). Fixed by mirroring the already-shipped pattern in
  `launch-tradfi-forward-poll.sh`: `VM_TASK=mtds-backfill` (the only branch that builds `--source`) +
  `VM_SOURCE=databento`. Fix applied + committed same-session as part of unblocking batch6 todo #2; re-launch confirmed
  VMs surviving past the previous failure window.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [tradfi, vm, backfill, premature-deletion, databento, vm-task-routing, data-pipeline]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
    /plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: "2026-08-09"
author: slot-28
priority: P1
parent_epic: tradfi_master
source: >-
  Discovered live 2026-08-09 while executing tradfi_satellite_ao_dispatch_batch6-002 (ES_OPT launch todo). The singleton
  lock cleared after ~2.5 days; the first launch attempt's 5 VMs all self-deleted within 2-4 minutes. Investigated via
  `gcloud logging read` / `gcloud compute operations list` / a GCS run.log read + a dedicated sub-agent that traced the
  exact code path, confirming `--source` was never appended for VM_TASK=cefi-backfill.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: fix
estimate_class: bug
estimate_baseline: 0.3
calibrated_ai_days: 0.2
assigned_role: infra
resolved_by:
locked_by:
depends_on: []
---

# tradfi year-shard backfill launcher missing --source — self-deletes within minutes

## Evidence

**Deletion timing** (`gcloud compute operations list --filter='targetLink~"tradfi-bf-es-opt"'`):

| VM                                          | Inserted (UTC) | Deleted (UTC) | Elapsed |
| ------------------------------------------- | -------------- | ------------- | ------- |
| tradfi-bf-es-opt-light-2022-20260809-023757 | 02:38:01       | 02:40:48      | 2m47s   |
| tradfi-bf-es-opt-light-2023-20260809-023814 | 02:38:17       | 02:40:59      | 2m42s   |
| tradfi-bf-es-opt-light-2024-20260809-023829 | 02:38:33       | 02:41:14      | 2m41s   |
| tradfi-bf-es-opt-light-2025-20260809-023847 | 02:38:50       | 02:41:26      | 2m36s   |
| tradfi-bf-es-opt-light-2026-20260809-023902 | 02:39:05       | 02:42:59      | 3m54s   |

All 5 deletes authenticated as `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` (the VM's own attached SA per
`lc_tier_service_account()`, `launcher_common.sh:168` — NOT a Claude Code agent, NOT `unified-trading-sa`), each from a
DIFFERENT `callerIp` matching that specific VM's own external IP — confirming 5 independent self-deletes, not one
centralized deleter.

**run.log** (`gs://deployment-scripts-central-element-323112/vm-logs/tradfi-bf-es-opt-light-2022-.../run.log`):
`tick_data_handler.py::_resolve_source` raised `ValueError: --source databento is REQUIRED for a TradFi OHLCV download`,
batch completed "0 results collected", process exited rc=1, `DEPLOYMENT_FAILED`, then
`VM_SHUTDOWN_ON_COMPLETION=true — scheduling self-delete`.

## Root cause

`deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh`'s `_create_vm()` (line ~231, pre-fix) hardcoded
`metadata="VM_TASK=cefi-backfill"`. `setup-data-pipeline-vm.sh` has **no dispatch branch for `cefi-backfill` at all**
(confirmed via `grep -n '"cefi-backfill"'` — zero matches; only `"mtds-backfill"` exists as a real branch, plus a stale
example comment at line 22 that never became real code). Every VM launched via this script therefore fell through to the
generic fallback branch (~line 2776), which builds `CLI_ARGS` WITHOUT `--source` — only the dedicated `mtds-backfill`
branch (line 1642) appends `--source $VM_SOURCE` (line 1728), and only when `VM_SOURCE` metadata is present, which this
launcher also never set.

This is a stale copy-paste bug (`VM_TASK=cefi-backfill` makes no sense for a TradFi launcher) that has likely affected
**every** VM ever launched via this script's year-shard default path (`_legacy_es_default`, used for
ES/ES_OPT/MES/IBIT/ETHA) and the ad-hoc single-window mode — the earlier report of "no active venues" / "--source ...
REQUIRED" failures noted in passing elsewhere in the tradfi corpus may trace back to this same root cause. Not
investigated further here (out of scope for this incident) — flagged as a follow-up below.

## Fix applied

`deployment-service@6b1057cc` (same-session): `VM_TASK=cefi-backfill` → `VM_TASK=mtds-backfill` +
`metadata="${metadata},VM_SOURCE=databento"`, mirroring the identical fix already shipped in
`launch-tradfi-forward-poll.sh` (which carries its own comment documenting this exact failure mode). Re-launch of the 5
ES_OPT VMs with the fixed script confirmed all 5 surviving past the previous 2-4 minute failure window (boot/setup phase
progressing normally at last check).

## Known secondary gap (not blocking, not fixed here)

`VM_FORCE_WINDOW` metadata (this launcher's own `--force-window`/`--no-force-window` flag, default `true`) is only wired
to `--force-window` in the generic fallback branch (line 2782) — the `mtds-backfill` branch this fix now routes through
does NOT read `VM_FORCE_WINDOW` at all (it reads a differently-named `VM_FORCE` for its own `--force` flag, which this
launcher never sets). For THIS incident's launch this is harmless (0 pre-existing ES_OPT rows, so the manifest
pre-flight skip-filter has nothing to skip either way), but it means `--no-force-window` silently has no effect on any
launch routed through `mtds-backfill`. Not investigated/fixed here — see action items.

## Second finding (2026-08-09, same session, post-relaunch) — something reaps VMs ~15-23min into a slow-but-real historical fetch

After the `VM_TASK`/`VM_SOURCE` fix, all 5 re-launched ES_OPT VMs started genuinely fetching data (confirmed via run.log
— no more `--source` error). **All 5 (2022-2026) eventually went silent (both `run.log` AND the separate GCS-blob
heartbeat sidecar froze at the exact same timestamp — this looks like the whole VM stalling, not just the Python
subprocess) and were then externally deleted** ~15-23 minutes after their last log line, none with a
`DEPLOYMENT_FAILED`/`VM_SHUTDOWN_ON_COMPLETION` line — always mid-day, before a `Processed date=...` completion line.
**2026 got furthest** — it processed several real trading days successfully first (`venue=CME: 24180 rows written`,
`Processed date=2026-01-08: 1 venues ok, 0 failed`, RSS cycling ~2.6GiB→9GiB and back down after each write, proving the
memory pattern itself is normal, not a leak) before it too froze on a later date and was reaped ~18 min after its last
log line.

**Corrected hypothesis (superseding an earlier, wrong guess in this doc's edit history — do not trust intermediate git
history for this section, only the current text)**: the in-VM `STALL_TIMEOUT_SEC` log-mtime watchdog
(`vm-exec-with-gcs-tee.sh`) defaults to **1800s (30 min)**, not the 600s this launcher's own header comment claims (that
comment is stale/wrong) — my launcher never overrides it, so 30 min is the actual in-VM threshold, and none of my
observed deaths reached that. The ~15-23 min death window is a much closer match for the SEPARATE, external
`vm_zombie_watchdog.py` (referenced in `cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md`), which polls VM
state from outside and gates on `--min-age` (default 15 min) before considering a VM eligible for reaping — consistent
with every observed death landing at 15-23 min post-last-log-line. **Not yet confirmed** (the VMs are already deleted so
this can't be verified post-hoc for this run) — this is the best-fit hypothesis from timing alone, not a traced code
path. If confirmed, this is a genuine **false-positive zombie classification**: the watchdog can't distinguish
"legitimately silent mid-fetch" from "actually dead," and kills real, live, in-progress work — the same class of bug as
`issues/protected_live_peer_liveness_misclassifies_dead_session_stranded_wip_2026_08_08.md` (a different subsystem, same
underlying pattern: liveness-by-log-silence is not liveness).

## Third finding (2026-08-09T~08:38-09:15Z, slot-22) — manifest count-check query was itself broken (false 0-row absence), true current coverage is far better than "all 5 died" implies

**The done-criteria query baked into `es-opt-backfill-watcher.sh` (and restated in both this doc's own action item below
and `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` todo #2) was wrong and would have returned 0 rows forever,
regardless of real capture state.** It filtered
`instrument_id in [CME:OPTION:ES, EW, EW1, EW2, EW4, E1A, E2A, E3A, E4A, E5A, EOM]` — an 11-item list that greps to ZERO
hits anywhere else in the codebase (confirmed: not a real UAC/IS registry, just an unverified assumption by whoever
first wrote the query). The writer (`market_tick_data_service/engine/orchestrator/partitioned_writer.py:71`,
`_tradfi_chain_partition_dims`) actually resolves ES and every E-mini options variant to ONE aggregate chain shard keyed
`underlying=SP500` / `instrument_id=CME:OPTION:SP500` (`reader.py:362-368` docstring: "pass either the exchange code
(ES) or the product root (SP500) — both resolve to underlying=SP500"). This is the same false-absence trap CLAUDE.md's
reconciliation guidance warns about ("probe the vocabulary the WRITER actually emits").

**Fixed**: `deployment-service@be6d4669` — corrected the filter to `underlying in (SP500, ES)`, added per-date dedup
(the manifest can carry multiple capture attempts per date — an earlier zero-row attempt superseded by a later real
one). QG green, landed + ancestry-verified on `origin/live-defi-rollout`.

**Re-ran the corrected query against a fresh manifest pull (2026-08-09T~08:41Z)** — true current state is dramatically
better than "all 5 died, 0 progress" implies:

| Year | Distinct dates | Dates with real data | Coverage |
| ---- | -------------- | -------------------- | -------- |
| 2020 | 267            | 253                  | 94.8%    |
| 2021 | 252            | 252                  | 100.0%   |
| 2022 | 251            | 251                  | 100.0%   |
| 2023 | 250            | 250                  | 100.0%   |
| 2024 | 253            | 252                  | 99.6%    |
| 2025 | 251            | **0**                | **0.0%** |
| 2026 | 204            | 149                  | 73.0%    |

Total: 1,407 of 1,728 distinct dates (81.4%) already carry real data, 7,391,527 total OHLCV bars. **2020-2024 are
essentially already complete** — most of this was NOT written by the `tradfi-bf-es-opt-*` launcher's two failed attempts
today (which only ran 21-40 min each before dying, per the second finding above); cross-checking `attempted_at`
timestamps shows the bulk of 2021-2024's real data was written well before today, and today's own `tradfi-bf-es-opt-*`
VMs (03:08-03:51Z insert/delete window, confirmed via `gcloud compute operations list`) landed some of the 2026 gain
directly (e.g. **2026-01-08 shows 24,169 rows written at 2026-08-09T03:31:34Z** — matches this doc's own second-finding
claim of "venue=CME: 24180 rows written" exactly). Separately, the general in-scope `tradfi-bf-cme-ohlcv-1m-g01-es-*`
root campaign (part of the MVP-of-MVP-authorized CME full-history futures backfill, unrelated launcher) appears to
incidentally capture the SP500 options chain alongside the ES futures fetch — this is most likely why 2020's coverage
(94.8%) is already high despite no dedicated `es-opt` launch ever targeting 2020 (the issue's launcher only
default-years to 2022-2026 per `cme-expiry-calendars.sh`).

**The real, narrow remaining gap is: 2025 (complete 0% — genuinely never captured, by any mechanism) and finishing 2026
(73%→100%).** Not a full 5-year re-run. Whoever next retries the dedicated launcher should expect years 2022-2024 to
mostly skip-refetch (if the launcher's freshness-check honors already-captured dates — separately flagged as uncertain
by this doc's own known-gap section on `VM_FORCE_WINDOW` not being wired into the `mtds-backfill` branch) and should
watch specifically for 2025 and 2026 progress, not treat a repeat all-5-years launch as starting from zero.

**Also observed live, same session**: the `wave_launcher.py` out-of-scope cron
(`issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md`) recurred again at ~09:00Z
(confirmed 2nd occurrence, ~3h after the first kill) — killed again by exact PID (same narrow precedented action),
tracked in that doc, not duplicated here. It was actively re-growing the singleton lock this task's retry depends on.

## Action items

- [ ] [DATA] P1. **NARROWED 2026-08-09 (see third finding above) — remaining gap is 2025 (0%) + finishing 2026 (73%),
      NOT all 5 years.** The manifest count-check query itself was broken (false 0-row absence, fixed
      `deployment-service@be6d4669`) — 2020-2024 are already 94.8-100% complete via a combination of earlier captures
      and the concurrent in-scope CME root campaign's incidental options capture, confirmed via the corrected query
      against a live manifest pull. Once the singleton lock is next clear (currently held, `wave_launcher.py`
      out-of-scope cron recurring on top of the in-scope CME campaign — see
      `issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md`), retry the launcher
      (idempotent) — but expect 2022-2024 to mostly skip-refetch and watch specifically for 2025/2026 progress, not a
      full 5-year restart. Retrying alone will likely still hit the zombie-watchdog reaper again (next action item,
      unfixed) for whichever year is actively fetching when the lock clears. Re-run the CORRECTED manifest count-check
      (`underlying in (SP500, ES)`, not the old 11-id filter) after any retry to measure the actual delta. Repo:
      unified-trading-pm (progress tracked in `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`, not duplicated here).
- [ ] [INFRA] P1. **RE-INVESTIGATED 2026-08-09 (slot 9, infra) — "false-positive" hypothesis does NOT hold; this was a
      genuine hang on the pre-fix undersized machine type, already root-caused by `deployment-service@391ff7f5`; no
      watchdog-side change is evidenced as needed.** Confirmed `vm_zombie_watchdog.py` IS the actual actor for the
      relevant wave (5 ES_OPT VMs inserted 2026-08-09T03:08-03:09Z, deleted 03:30-03:51Z) — NOT via timing alone: the
      delete audit-log entries' principal (`1060025368044-compute@developer.gserviceaccount.com`) and `callerIp`
      (`35.221.90.79`) match, exactly, the currently-running watchdog VM's own attached service account and external IP
      (`gcloud compute instances describe vm-zombie-watchdog-20260807-075242` → same SA, same NAT IP), and — distinctly
      from a self-delete pattern — all 5 kills share that ONE IP rather than each VM's own unique IP (the self-delete
      wave from this doc's first finding, by contrast, shows 5 DIFFERENT callerIps, one per VM, confirmed via a separate
      `gcloud logging read` pull). But the premise that these 5 were "legitimately slow (not hung)" is contradicted by
      their own `run.log` + heartbeat-blob evidence: all 5 show the SAME signature — RSS climbing from ~500MiB to
      8.4-10.3GiB within ~30-90s of the fetch starting, cpu pinned at ~100%, and then BOTH `run.log` (the
      `ResourceProfiler`/`PIPELINE_HEARTBEAT` emitters) AND the separate heartbeat-sidecar blob (`vm-heartbeat/<vm>.txt`
      — created once at ts, never updated again, confirmed via `gsutil stat`) go silent in lockstep at the same moment,
      not just the main fetch process. A live, merely-slow-but-alive process would not also freeze its own independent
      60s-interval heartbeat subprocess. This is the same OOM/thrash-hang class the doc's own third finding already
      flagged ("MACHINE_TYPE was still the undersized e2-standard-4 default... live-reproduced a 9.2GB RSS climb").
      Confirmed via `git log`: these 5 launches (03:08-03:09Z) predate `deployment-service@391ff7f5` (07:38:54Z same
      day), the commit that bumped `launch-tradfi-backfill-vm.sh`'s `MACHINE_TYPE` default from a hardcoded undersized
      value to `${MACHINE_TYPE:-e2-highmem-4}` specifically so a same-machine OOM relaunch doesn't just re-OOM — so this
      wave ran on the OLD, undersized machine type, not the fixed one. No ES_OPT VM has launched since 07:38Z (checked
      live fleet + `gcloud logging read` for post-fix deletes — zero), so there is no post-fix evidence either way;
      deliberately did NOT relaunch ES_OPT myself to test this (a fresh 5-VM launch here would risk colliding with the
      concurrent in-scope CME root-campaign fleet + singleton-lock activity this same doc's own dual-watcher caution
      warns about, and is out of this action item's narrow scope). Leaving unchecked — narrowed to a real,
      evidence-gated remaining step below — rather than inventing a watchdog `--min-age`/progress-logging change the
      evidence doesn't support. Repo: deployment-service (`vm_zombie_watchdog.py`, investigated only; no code
      changed). - [ ] [DATA] P2. Once the next ES_OPT launch happens post-`e2-highmem-4` fix (2025+2026 gap per the
      third finding), check whether the same RSS-spike/heartbeat-freeze signature recurs. If it does NOT recur, this
      action item closes with "machine-type fix was sufficient, no watchdog change needed." If it DOES recur (even on
      the bigger machine), THEN implement one of the two original remedies (raise `--min-age` for this launcher class,
      or add incremental per-date progress logging) against real post-fix evidence.
- [ ] [INFRA] P2. **PARTIALLY DONE (2026-08-09, separate session, deployment-service@391ff7f5)** — confirmed
      `_tradfi-ohlcv-launcher-lib.sh` (NASDAQ/NYSE/CME-grouped/KRX launchers) was already correctly wired
      (`VM_TASK=mtds-backfill` + `VM_SOURCE`, not affected). A different agent independently found + fixed the SAME bug
      in `launch-targeted-options-chain-backfill.sh` (CME-OPTIONS/CBOE-VIX-OPTIONS shards,
      `deployment-service@acf965d9`) concurrently with this doc's own fix — both landed together after resolving a real
      git stash conflict (identical fix, different comments). Remaining, NOT done: the historical-manifest-provenance
      cross-check (did any already-"captured" ES/BTC/ETH row actually come through this broken launcher). Repo:
      deployment-service + market-tick-data-service (manifest cross-check).
- [ ] [CODE] P3. **Wire `VM_FORCE_WINDOW` into the `mtds-backfill` branch** (or document why it's intentionally scoped
      only to the generic fallback) — currently silently ignored for every `mtds-backfill`-routed launch, including this
      one. Repo: deployment-service, `scripts/vm/setup-data-pipeline-vm.sh`.

## Progress Log

- **2026-08-09, slot-9 (infra)**: Worked the zombie-watchdog P1 action item. Confirmed `vm_zombie_watchdog.py` is the
  actor (SA + callerIp match against the live watchdog VM), but found the "legitimately-slow, not hung" premise is wrong
  for this wave — all 5 ES_OPT VMs show an RSS-spike-to-8-10GiB/cpu-100% signature followed by BOTH run.log and the
  independent heartbeat sidecar going silent together, and the wave predates `deployment-service@391ff7f5`'s
  `e2-highmem-4` machine-type fix. No watchdog-side code change is evidenced as necessary; narrowed the action item to a
  post-fix re-observation step instead of shipping an unsupported change. No code shipped this pass (investigation + doc
  update only). Did not relaunch ES_OPT (out of scope, singleton-lock collision risk with concurrent fleet work).
- **2026-08-09, slot-28**: Discovered + root-caused + fixed live while executing batch6 todo #2. Fix committed
  `deployment-service@6b1057cc`; re-launch in progress, VMs surviving past the previous failure window at time of
  filing.
- **2026-08-09T~04:41Z, slot-28**: Fix landed on `live-defi-rollout` (`deployment-service@c99ab99b8`, rebased SHA of the
  same content — ancestry-verified on origin). QG hit the 600s timing gate 3× standalone (1343s, timeout, 708s) before
  passing clean at 496s once shared-host load dropped (peaked at load-avg 63-67 with 8+ concurrent QG runs fleet-wide,
  well past the "≤2 full QGs at once" norm — a fleet-wide contention issue, not specific to this change). Quickmerge's
  own internal re-gate also hit the same wall once (626s) before a clean run finally shipped. No content changes were
  needed across any of these attempts — every failure was purely the resource-drift timing gate under contention.
- **2026-08-09, separate session (interactive, MVP-of-MVP scope-narrowing work)**: independently rediscovered this exact
  bug via live smoke-testing (per `/plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`'s
  relaunch-verification requirement) — two of my own test launches and a THIRD agent's real ES_OPT dispatch all hit it
  the same way. Also found this launcher's `MACHINE_TYPE` was still the undersized `e2-standard-4` default (never
  received the `e2-highmem-4` bump the exact-same OOM-hang class already got elsewhere, see
  `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`) — live-reproduced a 9.2GB RSS climb within seconds of boot
  on a narrow ad-hoc test before killing it. Fixing this collided with a 4th agent's concurrent fix for the SAME
  `VM_TASK` bug in a SIBLING launcher (`launch-targeted-options-chain-backfill.sh`) via a real git stash conflict
  (`||||||| Stash base` / `Updated upstream` vs `Stashed changes`) — both fixes were functionally identical, resolved
  cleanly, all tests green (including this doc's own regression test class + the sibling's), shipped together:
  `deployment-service@391ff7f5` (parents: `c99ab99b8`, `acf965d9`). Ancestry-verified on `origin/live-defi-rollout`.
- **2026-08-09T~08:38-09:20Z, slot-22, task
  `tradfi_year_shard_backfill_launcher_missing_source_self_deletes-7b183e5e4109`**: worked the P1 verify/retry action
  item. Found and fixed a genuine second bug (see third finding above): the manifest count-check query everyone
  downstream was relying on (this doc's own action item text, `es-opt-backfill-watcher.sh`, batch6 todo#2's
  done-criteria) filtered on a fabricated 11-instrument_id list that matches zero real rows — always returns 0,
  regardless of true state. Fixed `deployment-service@be6d4669` (QG green 277-284s, landed + ancestry-verified on
  origin). Re-ran the corrected query: true coverage is 2020-2024 ~complete (94.8-100%), 2025 a genuine 0% gap, 2026 73%
  (partial year). Did NOT retry the launcher myself this session — slot 21 was already running its own
  wait-for-lock-then-launch watcher (`wait_and_launch_es_opt.sh`, 90-min bound) when I checked; duplicating it would
  risk the documented dual-watcher double-launch race (batch6 plan's lesson #5), so I left that to them and focused on
  the query-correctness fix + accurate baseline instead. Singleton lock was NOT clear at any point I checked this
  session (5-12 `tradfi-bf-*` VMs throughout) — also killed a 2nd live recurrence of the `wave_launcher.py` out-of-scope
  cron (~09:00Z, same PID-kill pattern as the ~06:08Z entry in the scope-violation doc) since it was actively re-growing
  the lock my task depends on. Did not flip this action item's checkbox — the literal ask ("eventually completes across
  all 5 years") is not yet true (2025 is still 0%), and I didn't personally trigger or observe a fresh retry completing.
  Leaving open with the corrected, narrower scope documented for whoever picks this up next (retry should now target
  2025+2026 specifically, not assume a from-scratch 5-year run).
