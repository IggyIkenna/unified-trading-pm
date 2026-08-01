---
doc_type: issue
title:
  C0-RD5/C0-RD5b legacy-orphan-sweep todos stranded unchecked inside an archived plan, unreachable from any active doc
summary: >-
  Byproduct discovery from a 2026-07-31 na-eligibility-audit checkbox-citation fix (closing
  defi_dedicated_bucket_shared_migration_2026_07_13.md's last open todo, now archived). That todo's own text cited an
  "ambiguous Delete-when — a different, still-open C0-RD5b sweep exists in the archived governing plan" as the reason ~9
  dead-code campaign scripts were left in place rather than deleted (confirmed independently by
  defi_satellite_ao_dispatch_batch2_2026_07_26.md's 2026-07-26 audit AND defi_satellite_ao_dispatch_batch6_2026_07_30's
  2026-07-30 triage, both reaching the same conclusion). Tracing the citation: `plans/archive/2026_07/
  defi_manifest_canonicalisation_2026_06_01.md` (archived 2026-07-13) still carries two UNCHECKED `- [ ]` todos — C0-RD5
  ("delete ALL legacy... after C0-RD4 GREEN") and C0-RD5b ("orphan sweep of pre-existing legacy-FORM objects already in
  -prd") — that never migrated forward into any live plan when that doc archived, per
  /codex/12-agent-workflow/plan-completion-and-archival-discipline.md step 1 ("migrate any DEFERRED item into a real
  tracked todo"). They are the ONLY remaining evidence this specific legacy-orphan question was ever open; nothing in
  the active corpus currently tracks it.
status: open
nature: notes
asset_group: [defi]
stage: [data, meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [defi, archival, orphan-sweep, legacy-bucket, plan-hygiene, stranded-todo]
related:
  [
    /plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  na-eligibility-audit 2026-07-31 (tranche=defi, autonomous) — surfaced while fixing a stale checkbox citation on
  defi_dedicated_bucket_shared_migration_2026_07_13.md's P3 housekeeping todo; filed per the findings-triage HARD RULE
  ("outside every plan → plans/active/issues/<slug>_<date>.md") rather than chased to full resolution, since resolving
  it requires a live-GCS orphan sweep this audit's scope doesn't cover.
context_scope:
  [
    /plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# C0-RD5/C0-RD5b legacy-orphan-sweep todos stranded in an archived plan

## What's actually open here (likely little-to-nothing — needs a quick live check, not a design call)

Two `- [ ]` todos in the archived `defi_manifest_canonicalisation_2026_06_01.md` (lines ~1230-1237 there):

- **C0-RD5** — delete ALL legacy DeFi buckets/paths, gated on C0-RD4 GREEN.
- **C0-RD5b** — orphan sweep of legacy-FORM objects pre-seeded in the `-prd` buckets before the v9 canonical migration
  wrote its own paths there (risk: double-counting in the C0e consolidator rebuild, or a non-`pipeline_mode`-aware
  reader reading stale rows).

Both are dated 2026-06-02/06-07 in origin. Substantial DeFi bucket work has landed since then that plausibly already
subsumes them:

- `gcs_bucket_estate_cleanup_2026_07_10.md` deleted 12 of 14 legacy kind-dedicated DeFi buckets.
- `defi_dedicated_bucket_shared_migration_2026_07_13.md` (archived today) migrated + deleted the remaining 3
  (`dex-pools-prd`/`lst-rates-prd`/`perp-funding-prd`).
- `defi_dex_pools_delete_order_stale_2026_07_20.md` + the 2026-07-21 dex_pools/lending_indices fold (per workspace
  CLAUDE.md: "FOLDED + DELETED 2026-07-21 — legacy prefixes now 0 objects") directly addressed the "legacy-form objects
  still present" risk class C0-RD5b describes, for at least those two data_types.

**Hypothesis, not verified**: C0-RD5/RD5b are most likely stale/superseded by this later, more specific work — but this
was not confirmed against live GCS state (that would require the kind of bucket-sweep this audit's scope doesn't cover)
and the archived host doc's own text never got a closing note when the later work landed, so the hypothesis should be
checked, not assumed.

## Todos

- [ ] [SCRIPT] P3. Live-check whether any of the 8 legacy DeFi bucket-stems still hold pre-canonical legacy-FORM objects
      (`day=/category=defi/venue=...` or bare `date=` shapes, no `pipeline_mode=`) in the surviving `-prd` buckets
      today. If zero found (likely, given the deletions cited above), close C0-RD5/C0-RD5b as
      superseded-and-verified-moot with the live evidence, and note the closure back on
      `defi_manifest_canonicalisation_2026_06_01.md` (an archived doc — edit its own checkboxes directly per the
      corpus's existing precedent of retroactively correcting archived-doc checkboxes when evidence surfaces, do not
      re-open/unarchive it). If any are found, draft a proper scoped todo in an active plan (this doc, upgraded, or a
      fresh one) — do not leave them stranded a second time.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
