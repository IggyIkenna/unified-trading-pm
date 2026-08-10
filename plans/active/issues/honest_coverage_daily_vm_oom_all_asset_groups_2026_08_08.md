---
doc_type: issue
title: >-
  honest-coverage-daily VM OOM-killed 2 consecutive days (08-06, 08-07) — rollup stale ~50h for ALL 5 asset groups; peak
  RSS nearly doubled (8.20GB → ~15.4GB) in the 5 days since the 2026-08-01 per-AG streaming fix
summary: >-
  The `honest-coverage-daily` Cloud Scheduler job (00:30 UTC) fires correctly and its Cloud Run Job
  `honest-coverage-daily-launcher` reports "Completed successfully" every day — but the launcher only launches a GCE VM
  (`measure-honest-coverage-<date>`) and exits; it never waits for or checks the VM's own terminal state. The VM itself
  has been silently OOM-killed 2 days running: `measure-honest-coverage-20260806-003030` (anon-rss 15,352,788kB) and
  `measure-honest-coverage-20260807-003039` (anon-rss 15,411,360kB), both killing the `measure_honest_coverage.py
  --asset-group all` process ~2 minutes after launch, confirmed via GCE serial-console logs (`gcloud logging read` on
  `compute.googleapis.com/resource_name`). Result: `gs://central-element-323112-honest-coverage/` has no `2026-08-06/`
  or `2026-08-07/` directory — the latest `coverage.json` is still `2026-08-05T22:19:12Z`, ~50h stale at time of
  writing, for ALL 5 asset groups (cefi/defi/tradfi/sports/prediction), not just cefi. This was found during the
  scheduled `cefi_reconciliation_auditor` daily spot-check (cefi is the trigger, the bug is cross-cutting). The VM's own
  launcher script docstring (`launch-measure-honest-coverage-vm.sh:48-66`) records that a 2026-08-01 fix
  (instruments-service@12825e81) made `measure_honest_coverage.py` stream one asset_group's manifest at a time (bounding
  peak RSS to the single-largest AG's read) and empirically re-verified e2-standard-4 (16 GiB) safe at a peak of 8.20 GB
  RSS that same day. Five to six days later the measured peak has grown to ~15.35-15.41 GB — nearly double — right at
  the 16 GiB ceiling, both days landing within 60MB of each other (suspiciously reproducible, not obviously "random"
  growth). Whether this is organic manifest growth outpacing the 08-01 right-sizing, or a regression since (leak in the
  per-AG `del`+`gc.collect()` loop, a new column/computation added to the read, a burst of new rows in one AG right
  before 08-06) is NOT established — the script already ships an `--oom-monitor` flag (`oom-hang-monitor.sh`,
  ps/free/dmesg peak-RSS capture) built for exactly this right-sizing-verification scenario; that is the sanctioned next
  diagnostic step, not a blind machine-type bump. An immediate manual unblock (`--machine-type e2-highmem-4` override,
  already supported) is available if the operator wants the rollup un-stale before the investigation completes.
  Secondary, minor finding: the VM's own instance metadata self-labels `TASK=features-backfill` (a stale/generic
  launcher-template default) instead of something honest-coverage-specific — cosmetic, but would mislead a future
  log-grep by TASK.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags: [honest-coverage, oom, vm-launcher, monitoring-gap, cross-asset-group, fire-and-forget, capacity-planning]
related:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/deployment-observability.md,
    /plans/audit/results/data_pipeline_reconciliation_cefi_2026_08_09.md,
    /plans/audit/results/data_pipeline_reconciliation_cefi_2026_08_08.md,
    /plans/audit/results/data_pipeline_reconciliation_cefi_2026_08_07.md,
  ]
created: "2026-08-08"
author: cefi_reconciliation_auditor (scheduled role, slot 3, dispatch agt-9dc091)
priority: P1
parent_epic: infrastructure_master
source:
  "Discovered read-only during the scheduled cefi_reconciliation_auditor daily spot-check (2026-08-08) while
  re-verifying the honest-coverage rollup freshness todo carried from the 2026-08-07 report §7. Root-caused via gcloud
  logging read against the VM's own serial console (kernel OOM-killer trace), not previously diagnosed — the 08-07
  report only knew the cycle was missing, not why."
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: none
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh,
    instruments-service/scripts/measure_honest_coverage.py,
    deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py,
  ]
---

# honest-coverage-daily VM OOM — 2 consecutive missed cycles, cross-asset-group

## Evidence

**Scheduler fired on time, launcher reported success, VM died silently:**

```
$ gcloud scheduler jobs describe honest-coverage-daily --project=central-element-323112 --location=asia-northeast1
schedule: 30 0 * * *
state: ENABLED
lastAttemptTime: 2026-08-07T00:30:01.880359Z

$ gcloud run jobs executions list --job=honest-coverage-daily-launcher --project=central-element-323112 --region=asia-northeast1 --limit=5
honest-coverage-daily-launcher-fsllf  2026-08-07T00:30:05Z  2026-08-07T00:30:58Z  Completed  True  Execution completed successfully in 53.1s.
honest-coverage-daily-launcher-4qk6c  2026-08-06T00:30:06Z  2026-08-06T00:30:47Z  Completed  True  Execution completed successfully in 41.1s.
```

The launcher's own log (Cloud Run Job stdout) shows it only launches the VM and exits — it never polls the VM's terminal
state:

```
VM launched: measure-honest-coverage-20260807-003039
Output (when complete): gsutil cat gs://central-element-323112-honest-coverage/2026-08-07/coverage.json
Events: gsutil ls gs://central-element-323112-events/events/instruments-service/2026-08-07/measure-honest-coverage-20260807-003039/
Delete when done: gcloud compute instances delete measure-honest-coverage-20260807-003039 --zone=asia-northeast1-c --quiet
Container called exit(0).
```

**Both VMs' serial console shows the same OOM-killer signature**, ~2 minutes after the Python process starts:

```
# measure-honest-coverage-20260806-003030 (2026-08-06T00:35:35Z, script launched 00:33:2x-ish)
Out of memory: Killed process 7176 (python) total-vm:20932720kB, anon-rss:15352788kB, ...
systemd[1]: google-startup-scripts.service: A process of this unit has been killed by the OOM killer.

# measure-honest-coverage-20260807-003039 (2026-08-07T00:35:29Z, script launched 00:33:33Z)
Out of memory: Killed process 4841 (python) total-vm:21153608kB, anon-rss:15411360kB, ...
```

Both VMs booted `e2-standard-4` (4 vCPU / 16 GiB), ran
`/home/ikennaigboaka/venv/bin/python /home/ikennaigboaka/workspace/instruments/scripts/measure_honest_coverage.py --asset-group all`,
and both died within ~60MB of each other on anon-rss — consistent and reproducible, not a one-off blip.

**Bucket confirms no output landed:**

```
$ gsutil ls gs://central-element-323112-honest-coverage/ | tail -5
.../2026-08-01/  .../2026-08-02/  .../2026-08-04/  .../2026-08-05/
```

No `2026-08-06/` or `2026-08-07/` — latest `coverage.json` is still the 2026-08-05T22:19:12Z rollup (~50h stale at time
of writing, 2026-08-08T00:26Z). Its content is internally consistent (formula re-derives byte-exact against the raw
counts, matching the prior 2 daily audit reports), confirming this is genuinely the same stale snapshot re-read, not new
data landing under an unexpected path.

## Root cause

1. **Fire-and-forget launcher (structural gap, not new this run)**: `honest-coverage-daily-launcher`'s job is to launch
   the VM and it does; nothing downstream verifies the VM reached a terminal SUCCESS state (no polling of
   `_index`/output object, no re-alert on VM self-terminating via OOM vs `VM_SHUTDOWN_ON_COMPLETION` after genuine
   success). This is the exact "no fire-and-forget" pattern `/codex/05-infrastructure/vm-launcher-runbook.md` warns
   against, applied to a _launcher-of-a-launcher_ — the outer Cloud Run Job's own "success" only proves the `insert` API
   call for the VM succeeded, not that the VM's payload succeeded.
2. **Capacity regression since the 2026-08-01 right-sizing.** Per `launch-measure-honest-coverage-vm.sh:48-66` (comment,
   verbatim history): a 2026-08-01 fix (`instruments-service@12825e81`) made `measure_honest_coverage.py` stream one
   asset_group's manifest at a time instead of holding all 5 simultaneously, and was empirically re-verified the same
   day: e2-highmem-4 (32 GiB) control peaked 7.53 GB RSS, e2-standard-4 (16 GiB) test (same commit, same
   `--asset-group all`) peaked **8.20 GB RSS**, no OOM — downsized back to e2-standard-4 on that evidence. Five to six
   days later the measured peak is **~15.35–15.41 GB** — within ~7 GB of the ceiling headroom consumed, roughly double
   the 08-01 measurement. **Not established which of these it is:**
   - organic manifest growth (more historical + live-captured rows since 08-01) pushing the single-largest AG's
     column-pruned read past budget, or
   - a regression in the per-AG loop's memory release (the `del df, ag_coverage; gc.collect()` pattern not fully
     returning memory to the OS between AGs — Python/pandas/pyarrow fragmentation can make `gc.collect()` insufficient),
     or
   - a data-shape change (e.g. a large backfill landing a burst of new rows in one AG shortly before 08-06, inflating
     that AG's read past its 08-01 baseline).

   The script already ships the right tool for this: `--oom-monitor` (`oom-hang-monitor.sh`, opt-in ps/free/dmesg
   peak-RSS capture) exists specifically for right-sizing verification runs (per the launcher's own usage comment) —
   that is the next diagnostic step, not a blind machine-type bump. A bump alone (e.g. `--machine-type e2-highmem-4`,
   already a supported override) would unblock the symptom immediately but risks masking a genuine leak that OOMs again
   at the bigger size once data grows further, per this codebase's own established practice of empirically re-verifying
   sizing rather than guessing (see the 08-01 methodology this same script's history demonstrates).

## What I did not resolve

- Which of the three hypotheses above (organic growth / loop leak / data-shape burst) actually explains the ~2x jump —
  needs a fresh `--oom-monitor` run (or profiling `measure_honest_coverage.py` per-AG with `tracemalloc`/
  `resource.getrusage` checkpoints between AGs) to pin down which asset_group's read is now the peak and why.
- No fix shipped. This is a cross-asset-group job (`--asset-group all`), not cefi-scoped, and picking between "bump the
  VM" vs "fix a leak" vs "both" needs the diagnostic above first — attempting a guess-fix here risks masking the real
  issue exactly as the 2026-06-16 mis-sized downsize did for weeks (same launcher script's own documented history).
- Whether the launcher should be hardened to verify VM terminal state (poll the output object / VM exit code, page if
  absent after N minutes) instead of trusting "VM launched" as "job succeeded" — a real gap, but a separate, larger
  change to `honest-coverage-daily-launcher` / the data-pipeline-monitors framework.

## Suggested next steps (not executed — needs owner decision + the diagnostic run)

- [ ] [DIAG] P2. Run `launch-measure-honest-coverage-vm.sh --oom-monitor --force` (or equivalent) for a fresh
      right-sizing verification; identify which asset_group's read is now the RSS peak and whether it matches organic
      growth or looks like a leak. Repo: instruments-service / deployment-service.
- [ ] [OPERATOR] P1. **Escalated 2026-08-09 (was P2) — now 4 consecutive missed cycles (08-06/07/08/09), ~86h stale, 0
      remediation attempts recorded.** Decide immediate unblock: re-launch now with `--machine-type e2-highmem-4` to get
      a fresh `coverage.json` written while the diagnostic above runs, given the rollup is now stale for all 5 asset
      groups across 4 consecutive daily cycles with an unchanging (not self-healing) OOM signature. Repo:
      deployment-service.
- [x] ✅ [INFRA] P3. **DONE 2026-08-10 — shipped via `cross_cutting_satellite_ao_dispatch_batch6_2026_08_09.md` todo 1
      (`deployment-service@b44166be`, verified on origin).** Harden `honest-coverage-daily-launcher` to not report
      success until it confirms the VM reached a real terminal state (output object exists, or VM exit code / OOM marker
      checked) — the current "VM launched ⇒ Container called exit(0)" pattern is structurally blind to this exact
      failure mode. (repo: deployment-service)
- [x] ✅ [INFRA] P3. **DONE 2026-08-10 — shipped via `cross_cutting_satellite_ao_dispatch_batch6_2026_08_09.md` todo 2
      (`deployment-service@10df4a3c7`, verified on origin).** Fix the VM's own metadata `TASK=features-backfill`
      self-label (should be honest-coverage-specific) — cosmetic, but misleads future log-grep-by-TASK debugging. (repo:
      deployment-service)

## 2026-08-09 update — 3rd consecutive IDENTICAL OOM, rollup now 4 cycles / ~86h+ stale, no remediation applied yet

Re-checked read-only during today's scheduled `cefi_reconciliation_auditor` run (dispatch agt-91ada6, slot 4). Nothing
in this update changes the root-cause analysis below; it confirms the condition is still live and adds one analytically
useful data point.

- **Bucket still stuck at `2026-08-05/`** — `gsutil ls gs://central-element-323112-honest-coverage/` shows no
  `2026-08-06/`, `2026-08-07/`, or `2026-08-08/` dir. At this audit (2026-08-09T~02:15Z) the rollup is **~86h stale**
  (was ~50h when filed 08-08).
- **`honest-coverage-daily-launcher` fired again today and again reported blind success**: execution
  `honest-coverage-daily-launcher-54j5c`, `2026-08-09T00:30:07Z → 00:30:55Z`, `Completed / True`, "Execution completed
  successfully in 48.52s" — same fire-and-forget pattern, unchanged.
- **The VM it launched (`measure-honest-coverage-20260809-003041`) OOM-killed again**, confirmed via serial console:
  `Out of memory: Killed process 4857 (python) total-vm:22012596kB, anon-rss:15396828kB, ...` at 00:35:41Z (VM created
  00:30:41Z, python process killed ~5 min after launch — same shape as 08-06/08-07).
- **New signal: anon-rss is now FLAT across all 3 measured days, not still climbing** — 08-06: 15,352,788kB; 08-07:
  15,411,360kB; 08-09: 15,396,828kB (today's cycle; no VM ran for 08-08 per the launcher's own once-daily schedule, so
  this is the 3rd measured occurrence, not the 4th). All three sit within **~59,000kB (~0.06GB) of each other** — this
  is evidence AGAINST the "organic manifest growth" hypothesis (which would show a continuing upward trend) and favours
  either a deterministic ceiling (one AG's read has stopped growing, e.g. its backfill/capture completed) or a leak that
  maxes out at a size independent of day-to-day data volume. Still **not established** which — the `--oom-monitor`
  diagnostic run (todo 1 below) remains the right next step to pin down which AG's read is the peak.
- **No remediation has been applied**: machine type is still `e2-standard-4` (inferred from the OOM ceiling itself —
  `e2-highmem-4`'s 32GiB would not OOM at ~15.4GB; not independently confirmed via an `instances.insert` audit-log read
  this run). Todo 2 (`[OPERATOR]` — decide immediate unblock) is still unresolved 1 day later.
- **Not re-fixed inline this run either** — same reasoning as 08-08: this is a cross-asset-group (`--asset-group all`)
  job outside cefi-only scope, and the remediation choice (bump vs. diagnose-first) is an explicit operator decision
  already correctly gated, not a mechanical fix this role should apply unilaterally.

**Escalation note**: this is now a 4-cycle-and-counting miss (08-06/07/08/09) on a rollup that feeds all 5 asset groups'
honest-coverage numbers, with zero remediation attempts recorded since the 08-08 diagnosis. Flagging for operator
visibility per CLAUDE.md's "big finding" (cross-cutting data-correctness) criterion — carried forward via this issue
doc + today's `data_pipeline_reconciliation_cefi_2026_08_09.md` report rather than a new duplicate doc.

## Codex SSOTs referenced

- `/codex/02-data/honest-coverage-model.md` — the formula this rollup implements (unaffected; this is a
  staleness/availability issue, not a formula-correctness issue).
- `/codex/05-infrastructure/vm-launcher-runbook.md` — "no fire-and-forget" principle this launcher violates one level
  removed (Cloud Run Job → VM, not the operator → VM case the doc's examples usually cover).

## Progress Log

- **na-eligibility-audit 2026-08-08 (cross-cutting tranche)**: KEEP-NA, valid — doc filed same-day; todo 2 is explicitly
  `[OPERATOR]`-tagged (decide immediate machine-type bump vs. wait for the diagnostic, no ruling on record), alone
  keeping the whole doc NA; todo 3 is self-described in-doc as needing an owner decision on the detection mechanism
  before implementation.
- **cefi_reconciliation_auditor 2026-08-09 (dispatch agt-91ada6, slot 4)**: re-confirmed condition still live, 3rd
  identical OOM (see update above). No status change — still `open`, still NA-appropriate (same `[OPERATOR]`-gated todo
  2 blocking), still no fix applied. Escalating visibility given now 4 missed cycles, not 2.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **round9-cross-cutting-sweep 2026-08-09**: satellite-extracted the 2 bounded `[INFRA] P3` items (harden the launcher
  to verify VM terminal state; fix the stale `TASK=` metadata label) into
  `cross_cutting_satellite_ao_dispatch_batch6_2026_08_09.md`. Whole-doc RECLASSIFY not applied — the `[OPERATOR] P1`
  immediate-unblock decision (machine-type bump vs. diagnose-first tradeoff) and the `[DIAG] P2` oom-monitor run stay
  here, genuinely tied to that operator decision.
- **finalize reconciliation 2026-08-10 (slot 7, review)**: flipped both EXTRACTED `[INFRA] P3` items to done — shipped
  via `cross_cutting_satellite_ao_dispatch_batch6_2026_08_09.md` todos 1+2 (`deployment-service@b44166be`,
  `deployment-service@10df4a3c7`, both verified on origin). Doc stays open — `[DIAG] P2` + `[OPERATOR] P1` remain
  genuinely open (operator-gated unblock decision + oom-monitor diagnostic).
