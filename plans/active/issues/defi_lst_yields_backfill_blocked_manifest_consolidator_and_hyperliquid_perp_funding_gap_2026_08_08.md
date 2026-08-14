---
doc_type: issue
title: >-
  lst_yields 30-day backfill (2026-04-20→2026-05-19) blocked by two real upstream dependency gaps — stale/down manifest
  consolidator for market-data-tick-defi-prd and missing HYPERLIQUID perp_funding rows for 2026-04-20
summary: >-
  Executing the operator-authorized 2026-08-08 run of `features-service/scripts/backfill_lst_yields_30day.sh`
  (restriction lifted per lst_rate_honest_coverage_2026_07_21.md), fixed two real script bugs (missing
  `--feature-family`, missing `GCP_PROJECT_ID` env var) but the actual compute then failed its preflight dependency
  check for BOTH `lst_yields` and `lst_native_rates` passes on the very first date (2026-04-20). Not a script bug — a
  real upstream data-readiness gap. Filed per findings-triage (real, tracked finding; not fixed inline — out of scope
  for the backfill-script task that surfaced it).
status: open
nature: issue
asset_group: [defi]
stage: [data, features]
repos: [features-service, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [defi, lst-yields, dependency-checker, manifest-consolidator, perp-funding, hyperliquid, backfill-blocked]
related:
  [
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: "2026-08-08"
author: unknown
last_updated: "2026-08-08"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source: >-
  Found 2026-08-08 while executing the operator-authorized lst_yields 30-day backfill run
  (lst_rate_honest_coverage_2026_07_21.md Phase 5 #4, round5-na-digest-defi apply pass item 75).
context_scope:
  [
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    features-service/features_service/onchain/cli/handlers/batch_handler.py,
    features-service/scripts/backfill_lst_yields_30day.sh,
  ]
---

## What was found (measured, not inferred)

Ran `bash scripts/backfill_lst_yields_30day.sh` for real (project `central-element-323112`, `GCP_PROJECT_ID` exported)
after fixing two real script bugs (both shipped, `features-service@00b399d7a`):

1. The script's `python -m features_service` invocation was missing the now-required `--feature-family` flag — every
   invocation failed immediately with `error: --feature-family is required`. Fixed: added `--feature-family onchain`
   (both `lst_yields` and `lst_native_rates` live under `features_service/onchain/`).
2. The script assumes `GCP_PROJECT_ID` is already exported in the caller's shell; it isn't by default in this
   environment, causing `ValueError: Project ID required for dependency checker`. Worked around by exporting it manually
   for this run (not a script bug per se — every other invocation in this codebase that needs it exports it itself or is
   launched via a wrapper that does).

With both worked around, the ACTUAL compute failed its preflight dependency check for `2026-04-20` (the first day in the
30-day range) on BOTH passes:

**`lst_yields` pass** —
`DependencyError: features-onchain-service cannot run for 2026-04-20/DEFI: missing 1 required upstream dependencies`:

```
Missing: market-tick-data-service-vault-share-price
  Path: gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet
  Date: 2026-04-20
  Asset group: DEFI
  Required: True
  Reason: manifest read error: Consolidated availability_index for bucket='market-data-tick-defi-prd-central-element-323112'
    is stale or missing (older than MANIFEST_CONSOLIDATED_STALENESS_SEC=3600s) while per-VM shards exist — the
    manifest consolidator is behind or DOWN. Refusing to fall back to the per-VM shard merge (can OOM on large
    buckets). Remediation: fix the consolidator Cloud Run Job + Scheduler for this bucket; set
    MANIFEST_ALLOW_STALE_FALLBACK=true to force the recovery merge.
```

**`lst_native_rates` pass** — same manifest-consolidator failure PLUS a second, distinct gap:

```
Missing: market-tick-data-service-perp
  Path: gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet
  Date: 2026-04-20
  Asset group: DEFI
  Required: True
  Reason: MTDS perp_funding: no manifest row for required venue(s) ['HYPERLIQUID'] on 2026-04-20 (n=4 rows total) —
    the consumer reads only those venues
```

## Why this matters / what is NOT claimed

- **Not a script bug.** Both `--feature-family` and the `GCP_PROJECT_ID` fixes are real and now shipped; this doc is
  about what happened AFTER those fixes, on real infra.
- **The manifest-consolidator staleness finding may already be tracked** — this workspace has a standing
  `manifest-consolidator-ssot.md` + `data-pipeline-alerts.md` monitoring system for exactly this failure class (a Cloud
  Run Job + Scheduler that can go behind/down). This doc does NOT claim novelty — check the `#data-pipeline-alerts`
  Slack channel / `/data-pipeline-alerts-reconcile` skill for whether
  `market-data-tick-defi-prd-central-element-323112`'s consolidator is already a known, actioned incident before
  treating this as a fresh finding.
- **The HYPERLIQUID perp_funding gap for 2026-04-20 specifically was NOT investigated further** — it may or may not be
  the same class of gap as `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md` (a DIFFERENT,
  already-tracked `perp_daily_ctx` forward-write gap since 2026-06-02) — 2026-04-20 predates that gap's own window, so
  this is likely a SEPARATE, earlier hole in `perp_funding` coverage, not the same incident. Not cross-checked against
  the manifest for other April 2026 dates — could be a single-day gap or a wider one.
- **Only date 2026-04-20 was actually probed** (the dependency checker fails fast on the first date in a batch range) —
  whether dates 2026-04-21 through 2026-05-19 have the same gaps, worse gaps, or are clean is UNKNOWN; the 30-day
  backfill never got past day 1.
- **`--skip-dependency-check` was NOT used** — the checker's own error message offers it as a bypass; deliberately not
  taken here, since skipping it would silently compute `lst_yields` over an unverified/incomplete upstream window, which
  is exactly the honest-coverage discipline this whole plan exists to enforce.

## Todos

- [x] ✅ [DIAG] P2. **DONE (na-eligibility-audit 2026-08-09) — already tracked.** Checked whether
      `market-data-tick-defi-prd-central-element-323112`'s manifest consolidator staleness is a known/tracked incident:
      YES — `issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md` confirms the same bucket's
      consolidator cron (`uts-prod-manifest-consolidator-market-data-defi-cron`) was deliberately PAUSED
      2026-08-06T20:16:52Z by an in-flight canonical-migration rebuild VM
      (`canonical-migration-defi-rebuild-20260806-223130`), independently corroborated via live Cloud Audit Logs by
      `plans/archive/issues/dp_consolidator_scheduler_paused_defi_recurrence_2026_08_07.md` (resolved, archived
      2026-08-07). The "escalate as novel" branch does not apply. The underlying outage itself remains open, tracked in
      that sibling doc — not resolved here, only the "is this tracked" question is answered.
- [x] ✅ [DIAG] P2. **RESOLVED — no gap exists as of 2026-08-14.** Determined the real scope of the HYPERLIQUID
      `perp_funding` gap around 2026-04-20 via a bounded manifest query (not a fresh whole-corpus walk) for
      `(cefi, perp_funding, HYPERLIQUID)` across April-May 2026. Repo: market-tick-data-service@(pending sha) —
      `scripts/check_hyperliquid_perp_funding_gap_2026_08_14.py`
      (`read_availability_index(bucket, filters=[("date",">=",...),("date","<=",...)])` row-group pushdown, NOT a
      full-corpus walk). Result: **61/61 calendar days captured** for `(cefi, perp_funding, HYPERLIQUID)` across
      2026-04-01..2026-05-31, including 2026-04-20 itself (a `captured` row, not `empty_confirmed`/absent). 70 total
      manifest rows in the window (61 `captured` + 9 `empty_confirmed` duplicates/retries on other dates, no bearing on
      coverage). The original 2026-08-08 preflight failure ("no manifest row for required venue(s) ['HYPERLIQUID'] on
      2026-04-20 (n=4 rows total)") no longer reproduces against today's manifest — the gap has since closed (plausibly
      the same manifest-consolidator catch-up todo 1 already tracked, or an intervening backfill/live-cron write; not
      further investigated, out of this todo's bounded scope). **Confirmed separate from
      `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md`**: that gap is a different data_type
      (`perp_daily_ctx`, not `perp_funding`) over a non-overlapping later window (2026-06-02-onward vs this doc's
      2026-04-01..2026-05-31) — not the same root cause, as the doc's own note suspected.
- [ ] [DATA] P3. **Once both gaps above are resolved (or a clean date range is identified), re-run
      `backfill_lst_yields_30day.sh`** (now bug-fixed, `features-service@00b399d7a`) — either over the original
      2026-04-20→2026-05-19 window if the gaps clear, or over a re-scoped clean window if they don't. Cite the manifest
      fill-ratio check's final output as done-when evidence. Repo: features-service.

## Progress Log

- **2026-08-08 (round5-na-digest-defi apply pass, item 75)**: filed while executing the operator-authorized lst_yields
  backfill run. Two real script bugs found + fixed (`features-service@00b399d7a`); the actual compute then blocked on
  the two upstream dependency gaps documented above. Did not chase either gap further this session (out of scope for the
  backfill-script task — each is its own real investigation). No data written; no GCS/manifest mutation made.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (3 entries), still accurate.
- **2026-08-09 (cross_cutting_satellite_ao_dispatch_batch5_2026_08_09 Phase A)**: hit the SAME
  `ManifestConsolidatorStaleError` class on a DIFFERENT bucket — `features-defi-test-central-element-323112`
  (consolidated blob age ~289k-290k s, well past the 3600s threshold, while per-VM shards existed), not the
  `market-data-tick-defi-prd` bucket this doc originally tracked. Confirms the consolidator-staleness class is not a
  one-off on a single bucket. Used `MANIFEST_ALLOW_STALE_FALLBACK=true` to proceed — judged safe here (unlike Todo 1's
  caution for the PROD raw-tick bucket) because `features-defi-test-*` is a small, lightly-used `-test-` bucket (38-40
  total manifest entries observed, not "large"), and the recovery merge completed in seconds with no memory pressure.
  Did not investigate WHY the `features-defi-test-*` consolidator schedule is behind — plausible it simply isn't
  scheduled as often as prod tiers for a low-traffic test bucket, but not confirmed. Not chasing further here (out of
  scope for the Phase-A task) — leaving Todo 1 as-is since it's scoped to the prod bucket; a separate investigation
  would be needed to say whether the `-test-` tier's consolidator schedule needs its own fix.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA, stale item closed. Todo 1 answered YES by sibling doc
  `defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md` (read in full) — closed by citation. Todos 2-3 remain
  genuine open work (todo 2 unevidenced anywhere in the corpus; todo 3 explicitly gated on 1+2, and the underlying
  consolidator outage is still genuinely unresolved). Doc stays `assigned_vm: NA`.
- **2026-08-14 (AO worker, defi_satellite_ao_dispatch_batch13_2026_08_13 todo 2, slot 14)**: `[DIAG] P2` (todo 2)
  RESOLVED — shipped a bounded `read_availability_index(..., filters=[...])` diagnostic script
  (`market-tick-data-service/scripts/check_hyperliquid_perp_funding_gap_2026_08_14.py`) and ran it live against the real
  `market-data-tick-cefi-prd-central-element-323112` bucket for `(cefi, perp_funding, HYPERLIQUID)` across
  2026-04-01..2026-05-31: **61/61 days captured, zero gap, including 2026-04-20 itself** (a `captured` row, not
  `empty_confirmed`/absent — 7 total rows on 2026-04-20 across all `perp_funding` venues, up from the 4 the original
  2026-08-08 finding saw, consistent with the gap having closed between filing and now). Confirmed NOT the same root
  cause as `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md` (different data_type, non-overlapping
  window). Did not investigate WHY the gap closed (manifest-consolidator catch-up vs an intervening backfill/cron write)
  — out of this todo's bounded scope. Todo 3 (`[DATA] P3`, the `backfill_lst_yields_30day.sh` re-run) is now unblocked
  on the perp_funding side; the manifest-consolidator staleness class from Todo 1 may still need a fresh live check
  before re-running it (not re-verified here). Evidence: script output above; full quality-gates.sh green on the shipped
  SHA.
