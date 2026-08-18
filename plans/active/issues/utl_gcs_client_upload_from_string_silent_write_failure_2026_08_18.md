---
doc_type: issue
title: UTL GCS client silent write failure — wrong method names swallowed by a defensive guard, cross-repo
summary: >-
  deployment_service/deployment/state.py called upload_from_string()/download_as_string() on UTL's GCS handle --
  methods that do not exist on the current get_storage_client() factory's GCSBlobHandle. A defensive
  getattr/callable() guard swallowed the AttributeError silently: save_state() logged "Created deployment" and
  returned success while writing NOTHING to GCS. Fixed in state.py (2026-08-18) via the proven upload_bytes/
  download_bytes pattern already correct in wave_launcher.py. Same anti-pattern confirmed still present, unfixed,
  in 3 more deployment-service files, plus 60+ untriaged candidate files fleet-wide.
status: open
nature: design
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-library]
scope: [engineer]
tags: [gcs, data-correctness, silent-failure, cross-repo, utl]
related:
  [
    /plans/active/deployment_service_api_integration_cleanup_2026_08_18.md,
    /codex/05-infrastructure/gcs-object-operations.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-18
last_updated: 2026-08-18
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class:
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
assigned_role: infra
effort: medium
resolved_by:
drift_direction: advance-code
depends_on:
context_scope:
  [
    /plans/active/deployment_service_api_integration_cleanup_2026_08_18.md,
    /codex/05-infrastructure/gcs-object-operations.md,
    deployment_service/deployment/state.py,
    deployment_service/scripts/wave_launcher.py,
  ]
supersedes:
superseded_by:
source:
  [
    "Surfaced 2026-08-18 fixing deployment_service_api_integration_cleanup_2026_08_18.md todo 2 (Deploy Console
    live-broken bug) -- the fix's own end-to-end verification caught save_state() returning false-success while
    writing nothing to GCS. Root cause: StateManager.save_state/load_state/list_deployments called
    client.bucket().blob().upload_from_string()/.download_as_string() -- methods absent from UTL's current
    GCSBlobHandle/GCSBucketHandle (read-only handle, confirmed by introspection) -- guarded by a getattr/callable()
    check that degraded silently instead of failing loud.",
  ]
locked_by:
locked_since:
---

# UTL GCS client silent write failure — wrong method names, cross-repo

## What happened (confirmed, not hypothesized)

Fixing the Deploy Console live-broken-deploy bug (`deployment_service_api_integration_cleanup_2026_08_18.md` todo 2)
required exercising `StateManager.save_state()`/`load_state()`/`list_deployments()` in
`deployment_service/deployment/state.py` end-to-end against the real `unified-deployment-state-central-element-323112`
bucket. First pass: the function returned a clean success JSON — but the object was never actually written to GCS,
caught only by directly checking `blob.exists()` after the call, not by trusting the return value.

**Root cause**: these three methods called `client.bucket().blob().upload_from_string()` /
`.download_as_string()` — methods that do not exist on UTL's `get_storage_client()` factory's returned
`GCSBlobHandle`/`GCSBucketHandle` (confirmed via introspection: the handle is read-only w.r.t. those method names,
no `upload_from_string` at all). A defensive `getattr(...)`/`callable()` guard around the call swallowed the
resulting failure silently instead of raising — `save_state()` logged "Created deployment" and returned a
success-shaped result on every call, while persisting nothing.

**This exact failure mode was already hit and fixed once in this same repo**:
`deployment_service/scripts/wave_launcher.py` uses the correct pattern (`client.upload_bytes(...)` /
`download_as_bytes(...)`) — `state.py` simply never received the same fix when the bug was first found elsewhere.

## Fixed (2026-08-18, as part of the Deploy Console fix)

All three `state.py` methods switched to `upload_bytes`/`download_as_bytes`, matching `wave_launcher.py`'s proven
pattern. ~15 test-mock call sites in `test_deployment_state.py` and `test_deployment_orchestrator.py` updated to
match. Shipped: `deployment-service@c16b1f1407`. Re-verified live: write succeeds, an independent read-back returns
the correct persisted state, no more false-success.

## NOT fixed — still present, confirmed via direct code read (not yet fixed, out of scope for the fix above)

- `deployment_service/monitor.py`
- `deployment_service/orchestrator.py` — **needs separate triage**: `T1Orchestrator.save_plan()` may source its GCS
  client differently (not necessarily via the same UTL factory) — confirm before assuming it shares the exact bug.
- `deployment_service/backends/services/vm_monitoring.py`

## Untriaged — needs a dedicated audit (this doc does not resolve this, it records the finding)

A workspace-wide grep for `upload_from_string`/`download_as_string` turned up **60+ files across many repos**
(at minimum: instruments-service, market-tick-data-service, strategy-service — not an exhaustive list). None of
these are triaged yet for which of two categories they fall into:

1. **Affected** — goes through UTL's `get_storage_client()` factory and calls a method absent from its handle →
   same silent-write-failure class as `state.py`, a genuine data-correctness risk.
2. **A different problem, not this one** — calls the real `google.cloud.storage` SDK's `upload_from_string`/
   `download_as_string` directly (these methods DO exist on the raw SDK's `Blob` class) → not silently broken, but
   itself a violation of this workspace's "no direct `google.cloud`/`boto3`" coding standard (should route through
   `get_storage_client()` instead) — a different fix, lower urgency.

**Why this matters enough to flag now rather than quietly fix opportunistically**: any code hitting category 1 is
currently logging false success while silently not persisting data — exactly the shape of bug that stays invisible
until someone goes looking for the state it should have written and it isn't there (as happened here). Any service
depending on `deployment_service`'s deployment-state persistence — anything reading `list_deployments()` or a
deployment's status — may have been silently getting incomplete/missing state for an unknown duration prior to this
fix.

## Follow-up (not yet scoped as dispatchable todos — this is the open question, not a decided plan)

1. Triage `deployment_service/orchestrator.py`'s actual GCS client source before assuming it shares the bug.
2. Fix `monitor.py` + `vm_monitoring.py` (once orchestrator.py's triage is done, since if the underlying handle is
   the shared culprit, these need the identical `upload_bytes`/`download_as_bytes` fix).
3. Triage the 60+ fleet-wide candidate files into category 1 (affected — real bug) vs category 2 (SDK-direct
   violation, different fix) before deciding scope/priority for a fleet-wide remediation pass. This triage step
   itself is a determinable, precisely-scoped audit ("for file X, does its GCS client trace back to
   `get_storage_client()` or a raw SDK import — cite the import chain") and is a reasonable candidate for an
   AO-dispatched follow-up plan once someone confirms the AO-vs-human split for it (not decided in this doc).

## Progress Log

- **2026-08-18**: Filed while fixing `deployment_service_api_integration_cleanup_2026_08_18.md` todo 2. Root cause
  fixed in `state.py` (shipped `deployment-service@c16b1f1407`), confirmed by direct GCS write+read-back
  verification. Scope of the remaining 3 confirmed files + 60+ untriaged fleet-wide candidates recorded above,
  not yet actioned — `assigned_vm: NA` pending operator triage-scope decision.
