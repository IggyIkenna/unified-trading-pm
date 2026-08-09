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
last_updated: 2026-08-08
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
claim" discipline. One plan doc (`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s Progress Log, 2026-06-25
entry — **corrected 2026-08-09, plan_reconciler agt-a3e83c**, was "two independent plan docs" but only this one is
quoted/named below) states:

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
      Repo: instruments-service.
- [ ] [INFRA] P2. **Once the filter above ships + is verified (dry-run a manual regen, confirm the 4 legs stay
      excluded), re-enable both schedulers** (`gcloud scheduler jobs resume`). Do not re-enable before the filter lands.
- [ ] [DIAG] P2. **Determine WHEN the daily job actually got re-enabled** (was it ever truly paused via the Scheduler
      API, or did the 2026-06-25 session pause it manually out-of-band via a mechanism that didn't persist — e.g. a
      `gcloud` command that failed silently, or a subsequent Terraform apply/redeploy that reset it to its
      Terraform-declared default state). `gcloud logging read` for
      `resource.type="cloud_scheduler_job"     resource.labels.job_id="lifecycle-catalogue-regen-tradfi-daily"` over a
      longer window (90d) would show the actual pause/resume history if Cloud Audit Logs retention covers it. This
      determines whether the root cause is "the pause never took" or "something later silently re-enabled it" —
      different fixes (a script bug vs. a deploy-time reset gap in whatever pauses schedulers).
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
