---
doc_type: issue
title:
  tradfi catalogue-regen schedulers were silently NOT paused for 6+ weeks despite plan claims — re-baked G1 pollution
  daily
summary: >-
  Discovered 2026-08-08 while executing the operator-approved tradfi §8 4-leg catalogue retirement purge
  (`instruments_completion_tracker_2026_07_06.md`) — `lifecycle-catalogue-regen-tradfi-daily` and
  `lifecycle-catalogue-full-tradfi-weekly` were live `gcloud`-confirmed `ENABLED` (fire logs 2026-08-07/08 01:00 UTC),
  contradicting `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s repeated claim that the daily job was
  "operator-PAUSED" since 2026-06-25. `build_instrument_catalogue.py` has no build-time filter for the retired
  ICE/CBOE-OPRA/VX-spread/VIX-cash rows, so every daily/weekly regen was re-including them from the never-deleted
  historical `instrument_availability/by_date/` source objects — meaning the just-executed catalogue purge would have
  been silently undone at the next scheduled fire had the jobs been left running. Protectively paused both this session;
  a durable fix (build-time exclusion filter) is required before either can be safely re-enabled.
status: open
nature: issue
asset_group: [tradfi]
stage: [data, meta]
repos: [instruments-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, catalogue, scheduler, data-correctness, ssot-drift, g1-retirement]
related:
  [
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-08
author: round5-cross-cutting-audit
last_updated: 2026-08-09
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  [
    "round5-cross-cutting-audit 2026-08-08, id=52 (tradfi §8 4-leg retirement purge execution) — discovered
    mid-execution, not looked for",
  ]
context_scope:
  [
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    instruments-service/scripts/build_instrument_catalogue.py,
  ]
---

# tradfi catalogue-regen schedulers were silently NOT paused for 6+ weeks

## What I found

While executing the operator-approved tradfi §8 4-leg catalogue retirement purge (2026-08-08), I checked live Cloud
Scheduler state before running the purge, per the delete-safety protocol's "verify current state, never assume a prior
claim" discipline. Two independent plan docs (`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s Progress Log,
2026-06-25 entry) state:

> "Tradfi compute STOPPED ... paused **`lifecycle-catalogue-regen-tradfi-daily` (01:00)** +
> **`instrument-catalogue- regen-nightly` (02:00)** at 01:38 UTC — protective, before the 02:00 fire would re-bake the
> §7.3 false-delistings into the tradfi catalogue SSOT."

Live check
(`gcloud scheduler jobs describe lifecycle-catalogue-regen-tradfi-daily --location=asia-northeast1 --project=central-element-323112`)
returned **`state: ENABLED`**, with `gcloud logging read` confirming fires at 2026-08-07T01:00:04Z and
2026-08-08T01:00:02Z UTC (today, hours before this check). `catalog.parquet`'s `last_modified` was
`2026-08-08T05:50:49Z` — consistent with a same-day regen having run. A parallel weekly job,
**`lifecycle-catalogue-full-tradfi-weekly`** (Sat 05:00 UTC, `--mode full`), was ALSO `ENABLED` and was never named in
any pause list in either plan doc — a second, previously-undocumented gap.

`instrument-catalogue-regen-nightly` (the OTHER job named in the 2026-06-25 pause claim) IS correctly `PAUSED` — but per
a same-day `na-eligibility-audit` finding cited in the tradfi tracker doc, that job "never reads a tradfi bucket at
all," so pausing it was always immaterial to the tradfi pollution concern. The job that actually mattered
(`lifecycle-catalogue-regen-tradfi-daily`) was the one left running.

## Why it matters

`build_instrument_catalogue.py`'s `build_catalogue_dataframe` has no build-time filter excluding `venue=ICE`,
`venue=CBOE AND instrument_type IN (OPTION, SPOT_PAIR)`, or the VIX-cash `INDEX` ids — it rolls up from the full
historical `instrument_availability/by_date/day=X/venue={venue}/instruments.parquet` corpus, and those source objects
for the retired venues/types were never deleted (deleting them is a separate, larger, single-walk-disciplined leg
outside this purge's scope). So every daily 01:00 UTC fire (and every Saturday 05:00 UTC full rebuild) has been silently
re-including these already-flagged-for-retirement rows in `catalog.parquet` the entire time the plan believed the job
was paused — **at minimum since 2026-06-25** (the date of the false pause claim), i.e. **6+ weeks** of a scheduled job
silently not honoring an intended freeze. This is exactly the class of SSOT-contradiction finding the workspace's own
findings-triage rule requires surfacing rather than quietly working around.

**Immediate consequence for the 2026-08-08 purge**: had this not been caught, resuming normal operations after the purge
(as the approved "pause→snapshot→filter→resume" procedure literally describes) would have silently undone the purge at
the very next 01:00 UTC fire — the exact "would just get re-seeded" trap this repo has hit before (see
`purge_defi_catalogue_cefi_reclassified_venues_2026_08_04.py`'s docstring, a different but structurally identical
precedent). The purge was executed WITHOUT the resume step for this reason — see the executing todo's own note in
`instruments_completion_tracker_2026_07_06.md`.

## Todos

- [x] ✅ [INFRA] P1. **Protectively paused both live schedulers** (`lifecycle-catalogue-regen-tradfi-daily`,
      `lifecycle-catalogue-full-tradfi-weekly`) via `gcloud scheduler jobs pause`, confirmed `PAUSED` on both,
      2026-08-08. This is the safe/reversible interim state — a paused scheduler is not a data-loss risk, only a
      staleness one, and the tradfi catalogue was already 6+ weeks stale-in-content (re-baking the same known pollution,
      not advancing) so this changes nothing about catalogue freshness for legitimate rows.
- [ ] [INFRA] P1. **Add the durable build-time exclusion filter** to `build_instrument_catalogue.py`
      `build_catalogue_dataframe` (or an equivalent pre-write filter step) excluding `venue=ICE`,
      `venue=CBOE AND instrument_type IN (OPTION, SPOT_PAIR)`, and the 2 VIX-cash `INDEX` ids from every future rebuild
      — this is the fix that makes it safe to re-enable both schedulers without re-baking the just-purged pollution.
      Repo: instruments-service. **CITATION (na-eligibility-audit 2026-08-09, tradfi tranche, dispatch agt-3df41f):**
      this exact filter is already tracked verbatim in
      `/plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` (`status: active`,
      `assigned_vm: planning`, still open there too) — cross-referenced from
      `instruments_completion_tracker_2026_07_06.md` line ~474-478 ("EXTRACTED 2026-08-09 -> ...batch2..."). Track the
      fix THERE, not here, to avoid a double-dispatch; this checkbox stays open as a pointer, not independent scope.
- [ ] [INFRA] P2. **Once the filter above ships + is verified (dry-run a manual regen, confirm the 4 legs stay
      excluded), re-enable both schedulers** (`gcloud scheduler jobs resume`). Do not re-enable before the filter lands.
- [x] ✅ [DIAG] P2. **ANSWERED 2026-08-09** (data_engineering worker, slot 18, via
      `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch10_2026_08_09.md` todo 2): **"something later silently
      re-enabled it" — confirmed, and it was NOT a Terraform/deploy-time reset.** Pulled the Cloud Audit Logs (Admin
      Activity) full history for `lifecycle-catalogue-regen-tradfi-daily` — the `resource.type="cloud_scheduler_job"`
      execution log (the 90d window named in this todo) only carries fire records, not admin state-changes; the real
      history lives under
      `logName="...cloudaudit.googleapis.com%2Factivity" protoPayload.serviceName="cloudscheduler.googleapis.com"     protoPayload.resourceName:"lifecycle-catalogue-regen-tradfi-daily"`:

      ```
                      2026-08-08T12:35:05Z  PauseJob   ikenna@odum-research.com                (this doc's todo 1 protective pause)
                      2026-06-27T19:46:45Z  ResumeJob  unified-trading-sa@...iam.gserviceaccount.com   <-- the silent re-enable
                      2026-06-25T01:39:46Z  PauseJob   ikenna@odum-research.com                (the claimed pause — CONFIRMED REAL)
                      2026-06-23T16:32:23Z  ResumeJob  ikenna@odum-research.com
                      2026-06-14T12:18:26Z  PauseJob   ikenna@odum-research.com
                      2026-06-11T01:36:18Z  ResumeJob  ikenna@odum-research.com
                      2026-06-11T01:36:17Z  CreateJob  ikenna@odum-research.com
                      ```

                      **The 2026-06-25 pause DID genuinely take effect via the real Scheduler API** — ruling out "the pause never
                      took" entirely (2 confirmed `PauseJob` calls, ~0.4s apart — GCP's own audit-log duplication artifact, not 2
                      separate pause attempts; the same doubling pattern appears on every other Pause/ResumeJob pair in this history,
                      confirming it's a logging quirk, not a retry). It stayed paused for exactly 2 days, then was explicitly
                      **RESUMED at 2026-06-27T19:46:44 UTC**, authenticated as `unified-trading-sa` (the ambient identity agent
                      workers run as — not a human's own gcloud session, and not a Terraform service-account identity). Pulling the
                      full audit-log JSON for that event surfaces the smoking gun in `protoPayload.requestMetadata
                      .callerSuppliedUserAgent`: `google-cloud-sdk gcloud/572.0.0 agent-name/claude_code
                      command/gcloud.scheduler.jobs.resume invocation-id/a5f144cd031848748b6ec0cdfa8e79ae ... callerIp/35.76.120.160`
                      — **a Claude Code agent session ran a raw `gcloud scheduler jobs resume` directly against this job.** Widening
                      the query to the surrounding 15-second window shows it was not an isolated action:
                      `uts-prod-manifest-consolidator-instruments-tradfi-cron` was ALSO resumed by the same identity 1.8s earlier
                      (19:46:43-44Z) — i.e. this was a targeted "resume the tradfi jobs" sweep (2 tradfi-scoped jobs, back-to-back;
                      not a blanket all-schedulers resume, and not a single-job mistake). Checked commit history across
                      unified-trading-pm/deployment-service/instruments-service/market-tick-data-service/agent-orchestrator in the
                      surrounding 30-minute window for a task that would explain it — no commit lands at the exact timestamp; the
                      closest correlated activity is unrelated sports-plan-flip churn, so the specific task/plan behind that agent
                      session could not be pinned down further within this todo's diagnostic scope. Notably, 2026-06-27 is also the
                      date CLAUDE.md cites for the single-VM-architecture consolidation — plausible (not confirmed) that a
                      multi-VM-to-single-VM migration/consolidation pass resumed "our" tradfi schedulers as routine post-migration
                      cleanup, unaware the 2026-06-25 pause was protecting a specific in-flight data-correctness concern (the §7.3
                      false-delistings issue, a DIFFERENT and earlier concern than the G1-retirement issue this doc's own todo 1
                      re-paused it for on 2026-08-08 — i.e. this job has now been silently un-paused by an untargeted resume at least
                      once before, for an unrelated reason, which is exactly the "Finding 1" cron-collision failure mode
                      `deployment_service/data_pipeline_monitors/scheduler_maintenance.py`'s docstring was later built to prevent —
                      that module did not exist yet on 2026-06-27).

                      **Root cause classification**: not a script bug (the pause API call succeeded and held), not a deploy-time
                      Terraform reset (`lifecycle_catalogue_scheduler.tf`'s `google_cloud_scheduler_job` resource declares no
                      `paused`/`state` attribute at all, so Terraform doesn't manage or reset this field on `apply`) — it was a raw,
                      untargeted `gcloud scheduler jobs resume` run by an agent session, 2 days after the protective pause, with no
                      visible link to the reason the job was paused. **Practical implication for todo 3** (re-enable once the
                      build-time filter ships): a raw `gcloud scheduler jobs resume` remains exactly as unsafe today as it was on
                      2026-06-27 unless the re-enabling session first checks for/respects an intentional-pause marker — which is
                      precisely what `scheduler_maintenance.py`'s `pause_for_maintenance`/`resume_after_maintenance` (built 2026-07-13,
                      after this incident, per its own docstring) now provides. Todo 3 should use that module rather than a raw
                      `gcloud` resume, though adopting it here is that todo's own scope, not this one's.

- [ ] [SCRIPT] P3. **Consider whether Cloud Scheduler `state` should be asserted in a standing health-check** (similar
      to the fleet's other "assert the intended state actually holds" monitors) for any job a plan explicitly claims is
      paused for data-correctness reasons — this exact silent-drift class (a plan's stated state diverging from live
      infra state, undetected for 6+ weeks) is the kind of thing a cheap periodic assert would have caught on day 2, not
      day 45.

## Progress Log

- **2026-08-08, filed** (round5-cross-cutting-audit, id=52) — discovered mid-execution of the operator-approved 4-leg
  tradfi catalogue purge, not from a dedicated audit. Both schedulers protectively paused same session; the purge itself
  completed successfully (see `instruments_completion_tracker_2026_07_06.md`'s todo for full evidence). This doc tracks
  the residual root-cause fix (build-time filter) + re-enable path, kept separate from the purge todo itself since it's
  a distinct, cross-cutting infra-correctness finding.
- **2026-08-09 (cross-check, this session)**: An operator batch-ruling session tasked filing a NEW issue doc for
  "`lifecycle-catalogue-regen-tradfi-daily` paused sometime between 08-08's run and today, no documented reason found
  anywhere in the corpus (grepped, no hits)" — live-verified `lifecycle-catalogue-regen-tradfi-daily` IS currently
  `PAUSED` while its 4 siblings (prediction/sports/cefi/defi) are `ENABLED`
  (`gcloud scheduler jobs list --location=asia-northeast1 --project=central-element-323112` grep, 2026-08-09), matching
  the premise exactly. But a grep for `lifecycle-catalogue-regen` across `codex/`+`plans/active/` immediately surfaces
  THIS doc, which already documents the identical event in full: both `lifecycle-catalogue-regen-tradfi-daily` and
  `lifecycle-catalogue-full-tradfi-weekly` were protectively paused 2026-08-08 (todo 1 above) as a direct consequence of
  the tradfi §8 4-leg catalogue retirement purge — the reason is not "unexplained," it's the G1-pollution re-baking risk
  described in full above. Filing a second duplicate issue doc would have fragmented this exact finding across two
  trackers; not filed. This doc's own todo 4 (DIAG P2, "determine WHEN the daily job actually got re-enabled") already
  covers the deeper "was the 2026-06-25 pause ever real" question, and todo 3 (re-enable once the build-time filter
  ships) already covers the path back to `ENABLED`. No new tracked work added here — this entry exists so a future
  cold-start agent hitting the same "unexplained pause" premise finds the answer immediately via context_scope/grep
  instead of re-investigating or re-filing.
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-09** (tradfi tranche, dispatch agt-3df41f) [body-hash:5dc4d63f3807f9b1]:
  **KEEP-NA-STALE (already-duplicated), first audit -- 1 citation added.** All 4 open items read end-to-end via a
  dedicated sub-agent hunter; count reconciled (4/4). Item 1 (the build-time exclusion filter) turned out to duplicate
  `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` verbatim (3-way convergence: that plan, this doc, and
  `instruments_completion_tracker_2026_07_06.md`'s own "EXTRACTED 2026-08-09" note all describe the identical fix) --
  citation added so nobody double-dispatches it. Items 2-3 (scheduler resume; 90-day audit-log diagnosis) are genuine
  DEPENDENCY_BLOCKED/GENUINE_WORK, not duplicated anywhere in the corpus -- item 3 in particular is a clean, unblocked,
  bounded diagnostic (MISCLASSIFIED_LIKELY_AO_ELIGIBLE, flagged for a future pass's conflict-check, not promoted this
  run since item 1's citation fix was this pass's priority). Item 4 ("consider whether scheduler state should be
  asserted...") stays a genuine open design/scoping question, not yet a committed bounded task. Doc stays NA --
  whole-doc RECLASSIFY does not apply (items 2-4 remain open scope).
- **2026-08-09 (data_engineering worker, slot 18, via
  `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch10_2026_08_09.md` todo 2)**: todo 4 (DIAG) answered — see
  checkbox evidence above. Root cause: not a script bug, not a Terraform reset; a Claude Code agent session ran a raw
  `gcloud scheduler jobs resume` against this job (+ the tradfi manifest-consolidator cron, back-to-back) on
  2026-06-27T19:46:44Z, 2 days after the 2026-06-25 protective pause, with no traceable link to the pause reason.
  Remaining open count: 3 (todos 2, 3, 5 — the durable filter, the gated re-enable, and the standing-health-check design
  question).
- **na-eligibility-audit 2026-08-10** (tradfi tranche, dispatch agt-a70469) [body-hash:e7434ca03456fd3e]:
  **KEEP-NA-STALE (already-duplicated), re-confirmed.** Fresh full read, 3 open todos. Todo 1 (durable build-time
  exclusion filter) is duplicated verbatim in `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` (status:
  active, `assigned_vm: planning`) -- a 3-way convergence confirmed with
  `instruments_completion_tracker_2026_07_06.md`'s own "EXTRACTED 2026-08-09" note. Todo 2 sequenced behind todo 1; todo
  5 (standing-health-check design question) is GENUINE_WORK, not yet a committed task. `assigned_vm` unchanged.
