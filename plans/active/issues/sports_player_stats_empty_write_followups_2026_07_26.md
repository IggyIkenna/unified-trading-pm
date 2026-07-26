---
doc_type: issue
title:
  Follow-up hardening from the self-caused player_stats empty-write incident — GCS retention gap + audit sibling scripts
summary: >-
  Two unacked follow-up items carried over while archiving
  `sports_player_stats_normalize_empty_write_incident_2026_07_26.md` (RESOLVED — 240/240 objects remediated via live
  api_football re-fetch, root cause fixed in the normalization script). Splitting these into their own UNACKED issue doc
  rather than leaving them stranded in the now-archived incident doc, since `plans/active/issues/` docs archive on ack
  per `/codex/11-project-management/issue-doc-lifecycle.md` and the incident's own parent batch plan
  (`sports_satellite_ao_dispatch_batch5_2026_07_26.md`) is already at its 1000-line hard cap with no room to absorb
  them. (1) the affected bucket has no GCS object versioning / soft-delete retention, which is why the original 240
  objects were unrecoverable and had to be remediated via external re-fetch rather than restore — an infra/operator
  decision on cost vs blast-radius reduction. (2) the root-cause bug class (a script builds a `pd.DataFrame(records)`
  from a possibly-empty `records` list and writes it without checking for an empty result) may exist in other one-off
  canonical-rewrite scripts in `instruments-service/scripts/` — needs an audit pass.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [sports, data-correctness, player-stats, follow-up, infra, audit]
related:
  [
    /plans/archive/issues/sports_player_stats_normalize_empty_write_incident_2026_07_26.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
  ]
created: 2026-07-26
priority: P2
parent_epic: sports_master
source:
  "Carried over from sports_player_stats_normalize_empty_write_incident_2026_07_26.md's Follow-up todos at archival time
  (cicd plan_health wall fix, escalation agt-d65e83)"
execution_scope: local-only
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
---

# Follow-up hardening from the player_stats empty-write incident

## What I found

While archiving the resolved incident doc (mechanical fix for the `check_terminal_status_archived.py` plan-hygiene gate
— resolved issues must not sit in `plans/active/issues/`), it carried two open `- [ ]` follow-up todos that would
otherwise be stranded in `plans/archive/` (invisible to the backlog derivation, which only reads `plans/active/*.md`).
Filing them here as their own UNACKED issue so they stay dispatchable.

## Todos

- [ ] [OPERATOR] P2. Consider enabling GCS object versioning (or a bucket-level soft-delete retention window) on
      `instruments-store-sports-prd-central-element-323112` (and, if the same gap exists, its sibling prd sports
      buckets) — the empty-write incident was recoverable only because the source was a re-fetchable external API; a
      similar accidental-empty-write bug against internally-derived (non-re-fetchable) canonical data would have been a
      PERMANENT loss under the current zero-retention policy. Needs an infra/operator decision on cost vs. blast-radius
      reduction. Repo: instruments-service / terraform-canonical infra.
- [ ] [SCRIPT] P3. Grep other one-off canonical-rewrite scripts in `instruments-service/scripts/` for the same missing
      "refuse to write an empty/0-row result" guard that caused the incident (any script that builds a
      `pd.DataFrame(records)` from a possibly-empty `records` list before a CAS write is a candidate). Audit and add the
      same guard wherever missing. Repo: instruments-service. **Done when**: every matching script either has the guard
      or is confirmed not to need it, with a one-line note per script.

## Progress Log

- 2026-07-26 (cicd, slot 6): Filed while archiving the parent incident doc to clear the `plan_health` hygiene-sweep hard
  failure (`check_terminal_status_archived.py`); no code change, doc-only split.
