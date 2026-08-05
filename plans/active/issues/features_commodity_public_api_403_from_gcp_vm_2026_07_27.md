---
doc_type: issue
title:
  features-service `commodity` family — all 3 public/no-auth data sources (EIA, CFTC, Baker Hughes) return
  403/timeout/404 from a GCP VM; NOT a credentials gap, likely IP-blocking or missing User-Agent
summary: >-
  Real VM run of `/data-pipeline-check-features --family commodity --asset-group TRADFI` failed cleanly (exit_code=1,
  `Batch completed: 0/4 succeeded`) — every one of NG/CL × 2 days failed because all 3 external data sources
  (`eia_weekly_storage`, `cftc_cot_report`, `baker_hughes_rig_count`) returned 403 Forbidden / timeout / 404. Each
  adapter's own docstring states "Authentication: None required (public)" — so this is NOT the BLOCKED-CREDENTIALS
  category (no credential exists to provision); the most likely cause is GCP-VM outbound-IP blocking or a
  missing/generic `User-Agent` header these public sites now reject as bot traffic. The manifest's own honest-absence
  guard correctly REFUSED to record this as `empty_confirmed` (no `FetchEvidence` proving a clean 200+empty response) —
  a good defensive catch, not itself a bug.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [data-pipeline, features, commodity, external-api, 403, networking, gcp-vm]
related: [/plans/active/data_pipeline_check_mdps_features_2026_07_20.md]
created: 2026-07-27
author: unknown
parent_epic: infrastructure_master
priority: P2
source:
  [
    "data_pipeline_check_mdps_features_2026_07_20.md todo (commodity cell), dispatched task
    data_pipeline_check_mdps_features-030, slot-7 2026-07-27, real VM features-e2e-tradfi-20260727-083257-974efe",
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
resolved_by:
  features-service@d06919bf (User-Agent header fix) + live GCP VM re-verification 2026-08-05 (slot-16,
  features-commodity-tradfi-20260805-000243, 4/4 succeeded)
locked_by:
locked_since:
context_scope:
  [
    features-service/features_service/commodity/adapters/base_source.py,
    features-service/features_service/commodity/adapters/eia_ng.py,
    features-service/features_service/commodity/adapters/cftc.py,
    /codex/02-data/external-data-always-available-rule.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
  ]
---

# features-service `commodity` — public/no-auth data sources 403ing from a GCP VM

## What I found

Real VM run (`features-e2e-tradfi-20260727-083257-974efe`, `DEPLOYMENT_COMPLETED` → actually
`DEPLOYMENT_FAILED exit_code=1`),
`--family commodity --asset-group TRADFI --start-date 2026-07-04 --end-date 2026-07-05` (`commodities=['NG', 'CL']`).
Every one of the 4 `(commodity, date)` combos failed identically:

- `eia_weekly_storage` (`eia_ng.py`, docstring: "Authentication: None required (public API)") —
  `HTTP Error 403: Forbidden` every time.
- `cftc_cot_report` (`cftc.py`, docstring: "Authentication: None required (public)") — `HTTP Error 403: Forbidden` every
  time.
- `baker_hughes_rig_count` (a static `.xlsx` scrape, no auth at all —
  `https://rigcount.bakerhughes.com/static-files/North-America-Rotary-Rig-Count-Current-Week.xlsx`) — timed out on the
  first 2 attempts, then `HTTP Error 404: Not Found` on the later 2.

Result: `Batch completed: 0/4 succeeded`, `Processing failed`, exit_code=1 — a clean, honest, reproducible failure.
Notably, the manifest write path CORRECTLY refused to paper over this:
`ManifestWriter.record_empty failed: ... requires FetchEvidence proving a clean 200+empty fetch ... This is most likely an auth / rate-limit / 5xx / timeout / exception / missing-credential path masquerading as honest absence — call record_failed instead`
— the honest-absence guard is working as designed here, not a bug.

**Why this is NOT a `BLOCKED-CREDENTIALS` situation**: all 3 sources are explicitly documented (in their own adapter
docstrings) as public, no-authentication APIs — there is no credential to provision. The most plausible explanations:
(a) the GCP VM's outbound IP is being blocked/rate-limited by one or more of these public sites (EIA/CFTC/Baker Hughes
may all apply bot-detection or geographic/cloud-provider IP-range blocking), or (b) the adapters send a generic/missing
`User-Agent` header that these sites now reject. Two DIFFERENT sites (EIA, CFTC) 403ing identically, plus a THIRD
unrelated static-file host (Baker Hughes) also failing, on the SAME VM at the SAME time, is more consistent with an
environment-level cause (VM IP / headers) than 3 independent site outages.

## Why it matters

- The `commodity` family's TRADFI feature pipeline currently cannot produce ANY real output from this compute
  environment — every factor for every commodity fails, so any real backfill attempt from a similarly-provisioned VM
  would also fail 100%.
- Distinguishing this from `BLOCKED-CREDENTIALS` matters for triage: an operator asked to "provision an API key" for a
  source that has none would be stuck; the actual fix path is networking/headers, not credentials.

## Recommended decision

- [x] ✅ [SCRIPT] P2. **features-service** — **DONE 2026-07-28**. `http_get()` (`base_source.py`) now merges a realistic
      Chrome User-Agent + `Accept` header into every request by default (urllib's own default `"Python-urllib/3.x"` is a
      well-known bot signature; caller-supplied headers, e.g. `yahoo_finance.py`'s existing explicit override, still
      take precedence per-key). Added regression tests: the default header is sent and is not the urllib signature, and
      a caller-supplied header still wins. `bash scripts/quality-gates.sh --no-fix` green (17974+ tests). **Re-test from
      a real GCP VM not run this session** (would require launching a VM — see todo below, which stays open pending that
      live re-test). — features-service@d06919bf
- [x] [DATA] P3. **operator** — if the header fix doesn't resolve it, check whether `central-element-323112`'s egress IP
      range is on any of EIA/CFTC/Baker Hughes' block-lists — **NOT NEEDED (2026-08-05): header fix verified working;
      egress IP is not blocked; see Progress Log for live re-verification evidence.**

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).
- **2026-08-05 (slot-16, data_engineering, task `tradfi_satellite_ao_dispatch_batch5-010`) — LIVE RE-VERIFICATION: PASS
  ✅**. Three GCP VM runs against `--family commodity --asset-group TRADFI`:
  1. `features-commodity-tradfi-20260804-235609` (SPOT) — preempted 9s after insert, never ran.
  2. `features-commodity-tradfi-20260804-235831` (SPOT) — ran with `features-service@c8627c64` (which includes the
     header fix `d06919bf` as an ancestor). **Header fix confirmed working**: no 403/timeout/404 from EIA, CFTC, or
     Baker Hughes — the pipeline successfully fetched data, computed the signal, and reached the GCS write stage. Failed
     at `_write_signal_to_gcs()` with a DIFFERENT 403: `uts-prd-sa` lacked `storage.objects.create` on
     `commodity-signals-batch-central-element-323112` — a bucket-level IAM gap, not the original external-API issue.
     Grant applied: `roles/storage.objectCreator` on the bucket.
  3. `features-commodity-tradfi-20260805-000243` (SPOT) — re-ran with the IAM fix in place. **Complete success**:
     `Batch completed: 4/4 succeeded` (NG 2026-07-04, NG 2026-07-05, CL 2026-07-04, CL 2026-07-05),
     `DEPLOYMENT_COMPLETED exit_code=0`. Manifest shard written with 4 entries. VM self-deleted via
     `VM_SHUTDOWN_ON_COMPLETION=true`.

  **Verdict**: `features-service@d06919bf` (Chrome User-Agent + Accept header in `http_get()`) **resolves the issue** —
  EIA, CFTC, and Baker Hughes all respond normally from a GCP VM with the fix. The operator-gated egress-IP block-list
  check (todo below) is NOT needed — the header was the sole root cause. Flipping both remaining checkboxes below.
