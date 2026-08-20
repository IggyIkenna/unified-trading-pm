---
doc_type: issue
title: instruments-service — most Category-1 migration scripts hardcode stale bucket names missing the -prd- tier segment
summary: >-
  While fixing the 15 Category-1 GCS-client files (broken `upload_from_string`/`.reload()`/`.generation`/`bucket.name`
  calls on UTL's read-only `GCSBlobHandle`), live `.exists()` probes found that nearly every one of these files'
  hardcoded bucket-name constants is STALE -- missing a `-prd-` tier segment (and for prediction, using the wrong stem
  `prediction` instead of the real `pred`). Every non-`-prd-` candidate 404s; every `-prd-` candidate exists. This is
  the SAME bug class already flagged as pre-existing/out-of-scope for one file
  (`purge_bitget_phantom_null_rows.py`, in `/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md`)
  but is far more widespread than that single file -- confirmed present in at least 8 of the 15 Category-1 files plus
  4 CLI-docstring usage examples. Not fixed -- needs its own per-file live-verification pass (same methodology the
  source doc used for `reclassify_kalshi_other_historical.py`) to confirm the correct bucket per script before any
  fix lands, since asset-group naming may not follow a uniform `+"-prd-"` insertion rule.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [gcs, bucket-naming, stale-config, data-correctness, migration-scripts]
related:
  [
    /plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md,
    /plans/archive/2026_08/migration_script_canonicalization_into_deployment_service_2026_08_18.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-18
last_updated: "2026-08-20"
# was: infrastructure_master (renamed 2026-08-18, epic-taxonomy restructure; corrected cross-epic sweep 2026-08-19)
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.7
assigned_role: worker # was: data (not a valid agents/*.md registry entry; corrected na-eligibility-audit 2026-08-19)
effort: medium
resolved_by:
drift_direction: advance-code
depends_on:
context_scope:
  [
    /plans/archive/2026_08/migration_script_canonicalization_into_deployment_service_2026_08_18.md,
    instruments-service/scripts/,
  ]
supersedes:
superseded_by:
source:
  [
    "Surfaced 2026-08-18 while a sub-agent fixed the 15 Category-1 GCS-client files (Phase 1 of
    migration_script_canonicalization_into_deployment_service_2026_08_18.md) -- doing a safe, read-only .exists()
    probe on each file's literal hardcoded bucket-name constant before attempting a scratch-object round trip found
    every non--prd- candidate 404s. Shipped instruments-service@ae66f2147c fixed the GCS METHOD-CALL bug (verified
    against the real -prd- buckets instead), but did not touch the stale constants themselves -- different bug
    class, flagged not fixed per scope discipline.",
  ]
locked_by:
locked_since:
---

# instruments-service — stale (non-`-prd-`) hardcoded bucket names across Category-1 migration scripts

## What was found

Fixing the 15 Category-1 files' broken GCS SDK method calls required determining each file's REAL target bucket to
do a safe scratch-object round-trip verification (never running the scripts themselves — several are live prod purge
scripts). The literal hardcoded `BUCKET_NAME`-shaped constants in most of these files **404'd** on a plain
`.exists()` probe. The buckets that DO exist all carry a `-prd-` tier segment the hardcoded constants are missing
(and, for prediction-domain files, the correct stem is `pred`, not `prediction`).

This exact bug class was already flagged once, narrowly, in the source triage doc — for
`purge_bitget_phantom_null_rows.py` specifically ("the script's own hardcoded `BUCKET_NAME` (no `-prd-` segment)
resolves to a bucket that doesn't exist today — a separate, pre-existing stale-bucket-name bug ... unrelated to the
upload_from_string bug"). This doc generalizes that single-file observation: it is NOT isolated to that one file —
confirmed present across most of the 15-file Category-1 population.

## Why this matters

Any of these scripts, if actually re-run with its literal hardcoded bucket name (rather than the `-prd-` bucket this
investigation manually substituted for verification purposes), would target a bucket that doesn't exist — the script
would either crash immediately (loud failure, safe) or, if guarded, silently no-op (the exact silent-failure shape
the broader GCS-client investigation this doc descends from was originally about). Either way, none of these
scripts' write paths can be trusted to hit the real production bucket without this being resolved first — a
material caveat on top of the GCS-method-call fix that already shipped.

## What's NOT done here

- No per-file correct-bucket-name determination beyond what was needed for THIS investigation's own scratch
  round-trip test (which grouped files by asset-group domain, not by exact per-file correct constant).
- No fix applied to any of the 15 files' actual `BUCKET_NAME` constants.
- No check on whether the `-prd-` insertion rule is uniform across asset groups, or whether prediction's `pred` vs
  `prediction` stem mismatch is the only naming exception or one of several.
- No check of the ~4 CLI-docstring usage examples that also reference the stale names (lower priority — cosmetic
  vs. functional, but still misleading to a future reader copy-pasting the example).

## Todos

- [ ] [DATA] P2. Per-file live `.exists()`-probe verification pass across all 15 Category-1 files to determine each
      file's correct `-prd-` bucket name, confirming whether the `-prd-` insertion + `pred`/`prediction` stem
      exception is uniform across asset groups or file-specific, then fix each file's hardcoded `BUCKET_NAME`
      constant to the verified value. Done when: all 15 files' constants are verified live and corrected, with the
      per-AG naming-rule pattern documented in this doc.
- [ ] [DOCS] P3. Fix the ~4 CLI-docstring usage examples in the same files that reference the stale (non-`-prd-`)
      bucket names, matching the corrected constants from the todo above. Done when: a grep confirms no CLI
      docstring in these files references a non-`-prd-` bucket name.

## Progress Log

- **2026-08-18**: filed while shipping the 15 Category-1 GCS-client fixes (`instruments-service@ae66f2147c`) — the
  investigating sub-agent found this while determining target buckets for live scratch-round-trip verification, out
  of scope for the method-call fix itself. `assigned_vm: NA` pending a dedicated per-file bucket-name verification
  pass.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): RECLASSIFY whole-doc — 0 checkboxes existed (prose-only
  remaining work, a HARD RULE violation on its own), but the "What's NOT done here" section describes real, bounded,
  entirely machine-checkable work (bucket exists-or-doesn't + mechanical constant fix), confirmed not a duplicate of
  the citing parent doc's own DONE checkbox. Converted prose to 2 tracked todos above and flipped
  `assigned_vm: NA -> planning`. Companion:
  `instruments_service_stale_prd_bucket_names_2026_08_18_finalize_2026_08_19.md`.
- **context-scout 2026-08-20**: populated context_scope (2 entries).
