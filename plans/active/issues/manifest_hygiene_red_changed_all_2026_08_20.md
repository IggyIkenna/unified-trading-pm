---
doc_type: issue
title: "Manifest hygiene RED — 4 AG(s) with findings (2026_08_20)"
summary: "Daily manifest-hygiene-vs-GCS audit (--mode changed) found non-empty candidate lists across cefi/tradfi/sports/prediction (schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk) — needs worker triage of real gap vs code bug. No slug was pre-filed (2026-08-18 ruling: the ephemeral Cloud Run Job never commits); filed by the dispatched data_pipeline_failure worker from the raw finding payload per STEP 1 of its boot prompt."
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, e2e-testing]
scope: [engineer, admin]
tags: [manifest-hygiene, data-pipeline, honest-coverage, boilerplate-bug]
related:
  [
    /plans/active/issues/manifest_hygiene_red_all_2026_08_19.md,
    /plans/active/issues/manifest_hygiene_daily_ag_list_boilerplate_bug_2026_08_19.md,
    /plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md,
  ]
created: 2026-08-20
parent_epic: observability_master
priority: P1
assigned_vm: planning
author: data_pipeline_failure (escalation agt-56f0d4, slot-33)
resolved_by: slot-33 (e2e-testing@0a43d0ec70)
source:
  - manifest_hygiene_daily.py
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
locked_by: live-defi-rollout
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    e2e-testing/scripts/audit/manifest_hygiene_daily.py,
    /plans/active/issues/manifest_hygiene_daily_ag_list_boilerplate_bug_2026_08_19.md,
    /plans/active/issues/manifest_hygiene_red_all_2026_08_19.md,
  ]
---

# Manifest hygiene RED — 4 AG(s) with findings (2026_08_20)

> Filed by the `data_pipeline_failure` escalation worker (agt-56f0d4) from a raw finding
> payload — the daily audit's own Cloud Run Job never writes/commits an issue doc itself
> (2026-08-18 operator ruling, `/codex/05-infrastructure/data-pipeline-alerts.md` § "Never
> raw-`git commit` a finding from an ephemeral/untracked runner"). See
> `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily manifest-hygiene-vs-GCS orchestrator (`manifest_hygiene_daily.py --mode changed`)
found non-empty candidate lists for: cefi, defi, prediction, sports, tradfi. Finding-classes
named in the escalation payload: schema_version_not_v9, oracle_expects_but_empty,
noncanonical_path_on_disk, phantom_captured_no_parquet, shard_4pillar_fail.

Candidate list(s) referenced by the escalation payload (written to the Cloud Run Job's own
ephemeral filesystem — never committed anywhere; not readable from this worktree, same gap
as every prior day's filing since the 2026-08-18 architecture change):

- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_cefi_changed_2026_08_20.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_tradfi_changed_2026_08_20.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_sports_changed_2026_08_20.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_prediction_changed_2026_08_20.csv`

**Diagnosis (this session): the "What I found" prose above is itself the still-open bug,
not new evidence of a 5th (defi) or two extra (phantom/4pillar) finding.** This is a live
recurrence of `manifest_hygiene_daily_ag_list_boilerplate_bug_2026_08_19.md` todo 1
(confirmed still `- [ ]` open) plus a second, closely related half of the same root cause
found independently in this session:

1. **AG-list half (the already-tracked bug).** `manifest_hygiene_daily.py`'s `what_i_found`
   sentence was built from `ag_results` (every AG the invocation *ran*), not from the AGs
   that actually produced a non-empty `candidate_csvs` entry. defi is named in the prose
   above with **zero corresponding CSV** — exactly the shape already documented in the
   2026-08-19 bug doc for the 08-17/08-18 runs.
2. **Finding-classes half (found this session, same root cause, same function).**
   `manifest_hygiene_daily.py:749-754` (pre-fix) hardcoded the finding-classes sentence to
   always list `phantom_captured_no_parquet` and `shard_4pillar_fail` — but this run used
   `--mode changed` (the daily-cron default), which **scopes those two checks out entirely**
   (`hygiene_for_ag()`: `if mode == "full": ... phantom/4pillar ... else: SCOPED OUT`, logged
   explicitly). Those two classes could not possibly have fired today; the sentence named
   them anyway, on every `--mode changed` run, unconditionally.

## Why it matters

Each real class (schema_version_not_v9 / oracle_expects_but_empty / noncanonical_path_on_disk)
is a genuine data-correctness signal per `/codex/05-infrastructure/data-pipeline-alerts.md` —
non-v9 rows are pre-canonicalisation stragglers; oracle-expects-but-empty is a candidate C1
misclassification (real gap vs code bug); non-canonical paths break selective reads. But the
boilerplate prose itself actively misleads triage: a worker reading only the sentence (not
the attached CSV list) would waste time chasing a defi finding with no evidence, or a
phantom/4-pillar finding that was structurally impossible to have computed in `--mode
changed` — exactly the failure mode the 2026-08-19 doc's finding #1 already called out
("one triaging from the prose sentence (wrong) wastes time chasing a [] finding that has no
attached evidence").

## Recommended decision

Two independent things to close:

1. **Fix the boilerplate bug at its root** (this session) — derive both the AG-list and the
   finding-classes list in `manifest_hygiene_daily.py::run()` from the AGs/finding-names that
   actually produced a candidate row, not from `ag_results` (every AG run) or a hardcoded
   5-class literal.
2. **Triage the 3 real finding-classes** (cefi/tradfi/sports/prediction, per the attached CSV
   list) per the standard "real gap vs code bug vs intentional new venue" judgment — deferred:
   the candidate CSVs themselves are unreadable from any durable checkout (written only to the
   ephemeral Cloud Run Job's local filesystem, per the 2026-08-18 architecture — this is a
   standing corpus-wide gap affecting every `manifest_hygiene_red_*` doc since that change, not
   specific to today's finding). A future daily run, once the boilerplate fix below lands,
   will re-surface any still-real candidates with an honest AG/finding-class list.

Per `data_pipeline_hardening_self_monitoring_2026_06_22.md` Phase 3/5.

## Todos

- [x] ✅ [SCRIPT] P1. Fix `manifest_hygiene_daily.py::run()`'s `what_i_found` sentence to name
      only AGs with an actual non-empty `candidate_csvs` entry (not every AG run) and only the
      finding-class names actually present in `rows` (not a hardcoded 5-class literal spanning
      both `--mode changed` and `--mode full`). Added regression test
      (`test_run_what_i_found_names_only_actual_findings`). Repo: e2e-testing. —
      e2e-testing@0a43d0ec70
- [ ] [DATA] P2. Once the boilerplate fix (above) is live, re-triage the 3 real finding-classes
      (schema_version_not_v9 / oracle_expects_but_empty / noncanonical_path_on_disk) across
      cefi/tradfi/sports/prediction from a fresh daily run's honest CSV list. Repo:
      market-tick-data-service.

## Progress Log

**2026-08-20 (slot-33, escalation agt-56f0d4)** — Filed this doc from the raw escalation
payload (no pre-filed slug — the 2026-08-18 architecture change means the daily Cloud Run Job
never writes/commits an issue doc itself). Diagnosed: this is a live recurrence of
`manifest_hygiene_daily_ag_list_boilerplate_bug_2026_08_19.md` todo 1 (AG-list half, still
open) plus a second half of the same root cause (finding-classes hardcoded regardless of
`--mode`) found independently this session. Fixed both halves in
`e2e-testing/scripts/audit/manifest_hygiene_daily.py::run()` by deriving the AG-list and
finding-class-list from the AGs/rows that actually contributed a candidate CSV entry, instead
of `ag_results` (every AG run) / a hardcoded literal. Added regression test
`test_run_what_i_found_names_only_actual_findings`. QG green, shipped
`e2e-testing@0a43d0ec70` (verified ancestor of `origin/live-defi-rollout`). The 3 real
finding-classes (schema_version_not_v9/oracle_expects_but_empty/noncanonical_path_on_disk)
across cefi/tradfi/sports/prediction were NOT individually triaged this session — the
candidate CSVs referenced by the escalation payload are unreadable (never committed,
ephemeral-container-only per the 2026-08-18 change); tracked as the remaining P2 todo above,
to be re-run against a fresh, honest daily output once the fix lands.
