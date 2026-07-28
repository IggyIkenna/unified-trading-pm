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
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [data-pipeline, features, commodity, external-api, 403, networking, gcp-vm]
related: [/plans/active/data_pipeline_check_mdps_features_2026_07_20.md]
created: 2026-07-27
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
locked_by:
locked_since:
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
- [ ] [DATA] P3. **operator** — if the header fix doesn't resolve it, check whether `central-element-323112`'s egress IP
      range is on any of EIA/CFTC/Baker Hughes' block-lists (unlikely to be operator-actionable beyond routing through a
      different egress path); not urgent — commodity is a P1/lower-priority family, not currently gating anything else
      in the matrix.
