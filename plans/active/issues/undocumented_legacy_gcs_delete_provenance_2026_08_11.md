---
doc_type: issue
title: Undocumented ~2.88M-object / 168.72 GB legacy GCS delete (defi/tradfi/sports/pred) — confirm who/when executed it
summary: >-
  Migrated from a prose-only "Open follow-up for the operator" paragraph in
  `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (2026-07-13 fresh-audit section) that was never
  turned into a tracked todo before that doc's archival — per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 2 ("every follow-up is a canonical todo, never
  prose"). The 2026-07-13 fresh audit found the certified SAFE-TO-DELETE legacy-object population for defi/tradfi/sports/
  pred (2,877,901 objects / 168.72 GB, byte-for-byte matching the 2026-06-18 sizing) already gone from live GCS, with no
  corresponding commit or plan checkbox in this repo's history for defi/tradfi/pred (unlike sports's fully-documented
  `e2e-testing@0f1d761 delete_sports_legacy_twinned_2026_06_19.py`). The outcome exactly matches the certified
  SAFE-TO-DELETE list, so this reads as a correct-but-undocumented operator-authorized cleanup, not a runaway/accidental
  deletion — but the audit-trail gap itself is worth a closed-loop check. Process-hygiene, not data-safety.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, e2e-testing]
scope: [engineer, admin]
tags: [issue, process-hygiene, gcs, delete-audit-trail, archival]
related:
  [
    /plans/archive/2026_08/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-11"
author: slot-17
source: [instruments_mtds_consistency_remediation_residuals_2026_07_24.md "Fresh audit 2026-07-13" section, migrated at archival time]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P4
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.24
parent_epic: instruments_master
assigned_role: data_engineering
drift_direction: none
depends_on:
locked_by:
locked_since:
resolved_by:
---

# Undocumented legacy GCS delete — confirm who/when

## What I found

The 2026-07-13 fresh audit in the (now-archived) instruments/MTDS residuals doc found the defi/tradfi/sports/pred legacy
duplicate-object counts collapsed from 352,234/1,706,332/252,318/573,451 → 5,332/1,102/0/0 — a reduction that
byte-for-byte matches the previously-certified SAFE-TO-DELETE population (2,877,901 objects, 168.72 GB) from the
2026-06-18 sizing table. No commit or plan checkbox in this repo (or `e2e-testing`'s git history) documents who ran that
delete or when, for defi/tradfi/pred specifically — sports has a fully-documented equivalent
(`e2e-testing@0f1d761 delete_sports_legacy_twinned_2026_06_19.py`).

## Why it matters

Not a data-safety issue — the deleted population is exactly the certified-safe set, and no coverage/orphan regression
has been observed since. But a ~169 GB delete against prod buckets with no audit trail in the owning plan is a process
gap: if it recurs on a population that ISN'T pre-certified safe, there would be no record to catch it either.

## Recommended decision

A bounded, deterministic investigation — not a design/judgment call — so it's AO-dispatchable:

1. Check GCS bucket audit logs (Cloud Audit Logs — Admin Activity + Data Access, if Data Access logging was enabled on
   the affected buckets) for delete events in the days before 2026-07-13 against the defi/tradfi/pred legacy object
   prefixes.
2. Cross-reference against `git log --all` in `e2e-testing`, `market-tick-data-service`, and `deployment-service` for
   any script invocation or session note around that window that isn't already captured in the archived plan.
3. If logs have since expired (Cloud Audit Log retention is commonly 30-400 days depending on log type/config) or no
   record is found, that is itself a valid, bounded resolution — document "unrecoverable, logs expired" rather than
   leaving the todo open indefinitely.

## Todos

- [ ] [AUDIT] P4. Check Cloud Audit Logs (Admin Activity + Data Access) for the defi/tradfi/pred market-data-tick prod
      buckets for delete events in the window before 2026-07-13, and cross-reference `git log --all` across
      `e2e-testing`/`market-tick-data-service`/`deployment-service` for any matching script run. Record findings (who/when,
      or "unrecoverable — logs expired") in this doc's Progress Log, then close this issue. (repo: e2e-testing)

## Progress Log

- **2026-08-11 (slot 17)**: Filed — migrated from a prose-only deferral in
  `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (2026-07-13 fresh-audit section) that was about to
  be lost on that doc's archival. No investigation performed yet.
