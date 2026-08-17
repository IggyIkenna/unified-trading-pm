---
doc_type: issue
title: subgraph-health-probe now functional — 28/50 cells alerted on first real sweep, needs triage
summary: >-
  Fixed three root causes (missing GH_PAT IAM, OOM, silent local-pubsub swallow) that meant
  uts-prod-subgraph-health-probe had likely never delivered a real alert since inception. Its first working
  sweep alerted on 28/50 (protocol,chain) cells — needs a follow-up pass to separate genuine silent-data-loss
  from cold-start fingerprint noise before treating it as either "probe found nothing real" or a fire drill.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service, alerting-service]
scope: [engineer]
tags: [data-pipeline, defi, subgraph, data-correctness, dp-watcher-006]
created: "2026-08-16"
related: [/codex/05-infrastructure/data-pipeline-alerts.md, /plans/active/defi_consolidated_closeout_2026_07_18.md]
parent_epic: observability_master
priority: P1
source: escalation agt-686a3e (DP-WATCHER-006 job-failure fix follow-up finding)
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# subgraph-health-probe now functional — 28/50 cells alerted, needs triage

## Context

Escalation `agt-686a3e` (DP-WATCHER-006 / `DP_CLOUD_RUN_JOB_FAILED`, CRITICAL page) reported
`uts-prod-subgraph-health-probe` failing with its last completed execution ~10668min (7.4 days) stale. Root-caused and
fixed live + in terraform (`deployment-service/terraform/gcp/subgraph_health_probe_scheduler.tf`) — three independent
bugs, all present since the job's inception, meaning **this probe has likely never successfully delivered a single real
alert since it was built** (`solana_defi_legacy_migration_2026_05_27.md` § Hardening):

1. **Missing IAM**: `t1_batch_sa` had no `roles/secretmanager.secretAccessor` on `GH_PAT` — every execution failed at
   container startup (the terraform comment claiming it "reuses the hygiene-sweep grant pattern" was aspirational; no
   such grant/pattern ever existed). Fixed: added `google_secret_manager_secret_iam_member.t1_batch_gh_pat_accessor`.
2. **OOM at 1Gi**: `uv pip install -e unified-api-contracts` OOM-killed (exit 137) before the probe ever ran. Bumping to
   2Gi cleared the install but a bare `import unified_trading_library` inside `subgraph_health_probe.py` itself then
   OOM'd — UTL's `__init__.py` eagerly imports its full surface (margin/risk/sports-ml/etc.), not lazy-scoped to the 4
   helpers this script actually uses. Fixed empirically: `cpu=2`/`memory=4Gi` completes cleanly.
3. **Silent alert swallow**: `get_pubsub_client()` defaults to a local in-memory no-op backend unless
   `PROTOCOL_EVENT_BUS_BACKEND=gcp` is set — this job's hand-built env block (it clones raw source + builds its own
   container rather than using the shared deployment-api/deployment-service module) never set it. A fully "successful"
   sweep was silently publishing every finding to nowhere (`msg_id=local-pubsub-msg-N`). Fixed: added the env var.

All three verified live via `gcloud run jobs execute --wait` + log inspection (confirmed real numeric Pub/Sub
`msg_id`s on the post-fix run). Terraform fix shipped via quickmerge in `deployment-service`.

## What I found

The first fully-working sweep (2026-08-16 22:11 UTC) probed 50 (protocol, chain) cells and alerted on **28** — a 56%
hit rate. Signals seen: a mix of `HEAD_LAG`, `EMPTY_YESTERDAY`, and likely `DEPLOYMENT_CHANGED` (fingerprints file was
empty/stale before this run, so `DEPLOYMENT_CHANGED` comparisons had no prior baseline for most cells — expect a
cleaner signal on the NEXT 6h cycle now fingerprints are seeded).

## Why it matters

This is exactly the failure class the probe was built to catch (`AAVE_V3-OPTIMISM` 2026-05-08..05-29 precedent) — and
per item 3 above, it's been structurally incapable of ever paging anyone about it. A 56% alert rate on first real run
is high enough that it's plausibly a mix of (a) genuine silent-data-loss across many DeFi subgraphs that has been
accumulating invisibly, and (b) noise from stale/empty fingerprints on this bootstrap run (no prior deployment_hash to
diff against). Both need a human/agent pass to distinguish before this is dismissed as "probe found nothing real."

## Recommended decision

- Let the `defi_data_quality_alerts` → alerting-service → `#data-pipeline-alerts` route now work normally for the next
  1-2 sweeps (every 6h) — fingerprints will stabilize and `DEPLOYMENT_CHANGED` false-positives from the cold-start
  should clear.
- If the alert rate stays materially >10-15% after 2-3 sweeps, that's a genuine data-correctness finding needing
  per-protocol triage (which lending/DEX subgraphs are actually stale vs. which are schema/query-family
  misclassifications in `_SCHEMA_FAMILIES`) — file as a dedicated follow-up plan at that point, not guessed now.
- No action needed on the job/infra side — that part is fixed and verified.

## Provenance

Escalation: agt-686a3e (DP-WATCHER-006, `wall_type=data_pipeline_failure`). Fix: `deployment-service@<shipped-sha>`
(see quickmerge commit). Filed by the escalation worker per findings-triage (outside-plan, data-correctness class —
notify + issue doc, not silently dismissed).
