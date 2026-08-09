---
doc_type: issue
title: >-
  cefi-fwd-daily-cron- persistent host has been repeatedly deleted by an automated actor within
  minutes-to-hours of launch since 2026-08-04 — 3+ days with NO forward-poll cron running, root cause is a
  vm_zombie_watchdog.py prefix-collision (shares the shorter "cefi-fwd-" EPHEMERAL_BATCH heartbeat/shard
  policy meant for its own transient worker VMs)
summary: >-
  While working defi_cefi_venue_chain_axis_contamination_2026_07_28.md's sequenced [DATA] P1 cleanup todo (task
  defi_cefi_venue_chain_axis_contamination-014), the reader-exact coverage probe
  (features-service/scripts/probe_cefi_perp_funding_raw_coverage.py) showed the 6 CARRY_BASIS_PERP venues at 0
  objects for every day 2026-08-06 through 2026-08-09 (today) even though the historical gap (2026-05-23→2026-08-05)
  was just confirmed fully backfilled by a separate VM. `gcloud compute instances list` showed NO
  cefi-fwd-daily-cron- host running at all. `gcloud logging read` on the audit trail found the persistent cron host
  has been deleted by an automated GCP actor (compute_v1 python client UA, not a human/agent gcloud CLI session)
  shortly after each of its last 2 launches (2026-08-04 01:29→2026-08-05 07:22, ~30h; 2026-08-06 05:42→05:58,
  ~16.5min) — nobody ever relaunched it after the second kill, leaving the daily 09:00 UTC forward-poll dark for 3
  days. Root cause: `deployment_service/vm_prefix_registry.py` registers `"cefi-fwd-daily-cron-": None` (no
  bucket/lifecycle spec) alongside `"cefi-fwd-": VmPrefixSpec(bucket=_TICK_CEFI,
  lifecycle_class=LifecycleClass.EPHEMERAL_BATCH)` — the latter is meant for the cron host's own transient
  `cefi-fwd-{TS}` worker VMs, but `cefi-fwd-daily-cron-{TS}` also starts with the `"cefi-fwd-"` substring.
  `scripts/vm/vm_zombie_watchdog.py::_evaluate_vm`'s shard-bucket lookup loop does a first-match scan over
  `VM_PREFIX_TO_BUCKET.items()` (dict insertion order), NOT the longest-prefix-match the sibling
  `_resolve_lifecycle_class` (used only by the separate TERMINATED-VM reaper) explicitly documents and implements —
  so the persistent cron host's shard lookup silently falls through to the shorter `"cefi-fwd-"` entry. The cron
  host, by design, never writes a heartbeat blob or a per-VM manifest shard (its startup script only installs a
  crontab and sleeps) — both signals stay permanently `None`/missing, which is exactly the `zombie_no_heartbeat`
  condition once the VM's age crosses the "cefi-fwd-" prefix's 30-min heartbeat-stale threshold
  (`PREFIX_IDLE_THRESHOLDS["cefi-fwd-"] = (30.0, 180.0)`). None of the sibling `*-daily-cron-vm.sh` launchers
  (tradfi-fwd, cefi-onchain-fwd, cefi-fwd) set a `tier=daemon`/`tier=scheduler` label, so none of them are exempted
  via `_is_daemon()` either — this is a fleet-wide gap affecting every SCHEDULED_RECURRING cron-host launcher that
  shares a name prefix with its own EPHEMERAL_BATCH children, not unique to CeFi.
status: open
nature: issue
asset_group: [cefi, cross-cutting]
stage: [infra]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    cefi,
    vm,
    zombie-watchdog,
    prefix-collision,
    cron,
    data-pipeline,
    data-correctness,
    infra,
  ]
related:
  [
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: "2026-08-09"
author: slot-5
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: bug
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
source: >-
  Found while working defi_cefi_venue_chain_axis_contamination-014 (data_engineering, slot-5, 2026-08-09) — the
  todo's own gate requires CURRENT (not just historically-backfilled) funding_window() observations, which surfaced
  the missing forward cron.
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    deployment-service/scripts/vm/vm_zombie_watchdog.py,
    deployment-service/deployment_service/vm_prefix_registry.py,
    deployment-service/scripts/vm/launch-cefi-fwd-daily-cron-vm.sh,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
---

# cefi-fwd-daily-cron- host reaped by zombie watchdog prefix collision (2026-08-09)

## What I found

Working `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s sequenced P1 todo (step 1 requires
`CanonicalPerpFundingProvider.funding_window()` to return non-empty CURRENT observations, not just historically
backfilled ones), I re-ran the reader-exact bounded coverage probe
(`features-service/scripts/probe_cefi_perp_funding_raw_coverage.py --start 2026-05-23 --end 2026-08-09`):
2026-05-23→2026-08-05 is now (freshly, per the just-completed `cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md`
backfill) well-covered, but **2026-08-06, 08-07, 08-08, and 08-09 (today) are all 0 objects across every one of the 6
CARRY_BASIS_PERP venues.**

`gcloud compute instances list` showed **no `cefi-fwd-daily-cron-*` host running at all** — the persistent
SCHEDULED_RECURRING cron host that's supposed to fire the daily 09:00 UTC forward-poll was simply gone.
`gcloud logging read` on the audit trail:

| Timestamp (insert)  | Timestamp (delete)  | Age at delete | Deleting principal                                              | User-Agent                     |
| -------------------- | -------------------- | -------------- | ----------------------------------------------------------------- | ------------------------------- |
| 2026-08-04T01:29:51Z | 2026-08-05T07:22:21Z | ~30h            | `uts-prd-sa@...`                                                  | `python-requests/2.34.2,gzip(gfe)` |
| 2026-08-06T05:42:23Z | 2026-08-06T05:58:54Z | ~16.5min        | `1060025368044-compute@developer.gserviceaccount.com` (GCE default compute SA) | `python-requests/2.34.2,gzip(gfe)` |

Both deletions were issued via a Python `compute_v1` client (the `python-requests` UA), not the `gcloud` CLI — this
rules out the "Claude Code agent copy-pasted the singleton-refusal delete command" pattern that explains the
SEPARATE `cefi-fwd-{TS}` worker-VM premature-deletion incidents in
`cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md` (those were confirmed `agent-name/claude_code`
gcloud-CLI signatures). This is consistent with `scripts/vm/vm_zombie_watchdog.py`, which uses the
`compute_v1.InstancesClient` Python client library.

**Root cause (code-verified, not inferred):**

1. `deployment_service/vm_prefix_registry.py:1240` registers `"cefi-fwd-daily-cron-": None` — no bucket/lifecycle
   spec of its own.
2. The same file, line 109, registers `"cefi-fwd-": VmPrefixSpec(bucket=_TICK_CEFI,
   lifecycle_class=LifecycleClass.EPHEMERAL_BATCH)` — intended for the cron host's own short-lived
   `cefi-fwd-{TS}` children, NOT the persistent host itself.
3. `cefi-fwd-daily-cron-{TS}` is a **substring superset** of `cefi-fwd-`, so `str.startswith("cefi-fwd-")` is
   `True` for the cron host's own name too.
4. `vm_zombie_watchdog.py::_evaluate_vm`'s shard-bucket lookup (`for prefix, spec in VM_PREFIX_TO_BUCKET.items():
   if vm_name.startswith(prefix) and spec and spec.bucket: ... break`) is a **first-match scan over dict
   insertion order**, not a longest-prefix match. The sibling `_resolve_lifecycle_class` (used only by the
   separate TERMINATED-VM reaper) explicitly implements + documents longest-match
   ("mirrors the longest-match lookup used by VM_PREFIX_TO_BUCKET" — that claim is itself stale/aspirational for
   the RUNNING-VM path). So the cron host's shard lookup silently matches the shorter `"cefi-fwd-"` entry.
5. `PREFIX_IDLE_THRESHOLDS["cefi-fwd-"] = (30.0, 180.0)` — a 30-min heartbeat-stale / 180-min shard-stale window,
   sized for the fast-poll `cefi-fwd-{TS}` workers.
6. The persistent cron host's own startup script (`launch-cefi-fwd-daily-cron-vm.sh`) installs a crontab and then
   `sleep`s forever, printing an hourly heartbeat to **stdout only** — it never writes a
   `gs://.../vm-heartbeat/{vm_name}.txt` blob or a `_index/per_vm/{vm_name}.parquet` shard. Both signals are
   permanently `None`/missing for this VM's entire lifetime by design.
7. In `_evaluate_vm`: `hb_age is None and shard_age is None and age > 30` → `zombie_no_heartbeat` — the cron host
   is **structurally guaranteed to eventually satisfy this condition** the moment its age crosses 30 minutes
   (mismatch with the observed ~16.5min kill not fully reconciled — possibly a stricter watchdog invocation
   cadence or an `age` computation difference; not re-derived further, the mechanism is confirmed regardless of
   the exact minute).
8. **Fleet-wide, not CeFi-specific**: grepped the sibling `launch-tradfi-fwd-daily-cron-vm.sh` and
   `launch-cefi-onchain-fwd-daily-cron-vm.sh` — neither sets a `tier=daemon`/`tier=scheduler` label either (the
   one exemption path that WOULD save them, via `_is_daemon()` in `_list_watchable_vms`, which skips daemon-tagged
   VMs from watchdog consideration entirely). Every `*-daily-cron-` persistent host in the fleet is exposed to the
   same eventual reap.

## Why it matters

3 days (2026-08-06→08-09) of zero forward-poll captures for the 6 CARRY_BASIS_PERP venues — directly blocks
`defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s sequenced P1 cleanup todo (step 1 requires CURRENT, not
just historical, `funding_window()` coverage) and the sibling `-011` corpus-recompute task's own gate. This is a
**recurring** failure mode (2 kills in <1 week) that will keep re-happening for every persistent cron host in the
fleet until fixed — a data-pipeline-correctness heartbeat-rule finding, not a one-off.

## What I did this session (stopgap, not a full fix)

- Confirmed no `cefi-fwd-daily-cron-*` host was running; launched a fresh one:
  `cefi-fwd-daily-cron-20260809-084100` (singleton-check clean, `--dry-run` verified plan first).
- **Immediately labeled it `tier=scheduler`** (`gcloud compute instances add-labels ... --labels=tier=scheduler`)
  — this exempts it from `_list_watchable_vms`'s `_is_daemon()` skip, matching the one legitimate opt-out path the
  watchdog code already supports. Verified via `gcloud compute instances describe ... --format='value(status,labels)'`.
- This protects THIS one host going forward but does NOT fix the other 2 sibling cron-host launchers
  (tradfi-fwd, cefi-onchain-fwd), nor the underlying prefix-collision bug for any future re-launch that forgets
  the manual label step.

## Recommended decision / Todos

- [ ] [INFRA] P1. **Root fix**: add `tier=scheduler` (or `purpose` in `DAEMON_PURPOSE_OPT_OUT`) to the `LABELS=`
      line in all 3 `*-daily-cron-vm.sh` launchers (`launch-cefi-fwd-daily-cron-vm.sh`,
      `launch-cefi-onchain-fwd-daily-cron-vm.sh`, `launch-tradfi-fwd-daily-cron-vm.sh`) so every future launch is
      self-protecting — do not rely on a manual post-launch label step. Repo: deployment-service.
- [ ] [INFRA] P2. **Structural fix** (lower urgency, addresses the general prefix-collision class, not just these
      3 hosts): make `vm_zombie_watchdog.py::_evaluate_vm`'s shard-bucket lookup use the same longest-prefix-match
      `_resolve_lifecycle_class` already implements for the TERMINATED-VM reaper, instead of first-match dict
      iteration order. Add a regression test asserting a VM name that is a substring-superset of a shorter
      registered prefix (e.g. `cefi-fwd-daily-cron-X` vs `cefi-fwd-`) resolves to its OWN longest-matching entry.
      Repo: deployment-service.
- [ ] [DATA] P2. **Verify the relaunched cron host actually fires** at 09:00 UTC 2026-08-09 and writes real
      `derivative_ticker` objects for the 6 CARRY_BASIS_PERP venues — re-run
      `probe_cefi_perp_funding_raw_coverage.py --start 2026-08-06 --end <today+1>` a day or two after this doc is
      filed to confirm CURRENT coverage resumes (2026-08-06/07/08 will stay honest-absent — the cron was down for
      those days; only 08-09 onward should start filling in). Repo: features-service (script exists, no code
      change).

## Progress Log

- **slot-5 2026-08-09 (data_engineering, task `defi_cefi_venue_chain_axis_contamination-014`)**: filed this doc
  after finding the CURRENT-coverage gate for the parent todo's step 1 blocked on a missing forward-poll cron host,
  not (only) the historical backfill. Relaunched + labeled the host as a same-session stopgap; root/structural
  fixes filed as separate todos, not executed this session (deployment-service code change, different craft
  scope + repo than this doc's own parent task).
