---
doc_type: codex-ssot
title: Disaster Recovery -- RTO/RPO Targets
summary:
  RTO/RPO recovery targets per environment (prod < 30 min RTO / < 5 min RPO) + the Tier 0-3 recovery methods (Cloud Run
  revision rollback → manifest-pinned redeploy → full manifest restore + SIT → cross-region failover), the
  manifest-restore procedure, GCS backup locations (via resolve_bucket_name), and the SEV1-4 incident protocol +
  dependency-failure matrix.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [infrastructure, disaster-recovery, runbook, escalation]
related:
  [
    /codex/04-architecture/recovery-defence-in-depth-layers.md,
    /codex/04-architecture/incident-gateway-state-machine.md,
    /codex/15-runbooks/physical-pager-layer.md,
    /codex/15-runbooks/alerting/audit-acknowledgement-flow.md,
  ]
created: 2026-03-13
authoritative_for:
  [disaster-recovery RTO/RPO targets + Tier 0-3 recovery methods + manifest-restore procedure + GCS backup locations]
referenced_by: [/codex/04-architecture/recovery-defence-in-depth-layers.md]
owner:
last_reviewed: 2026-05-23
code_refs:
---

# Disaster Recovery -- RTO/RPO Targets

> **2026-05-23 SCOPE EXTENSION**: this doc owns RTO/RPO + Tier 0-3 recovery + manifest-restore + GCS backup locations.
> The broader **incident operating model** (5-layer defence-in-depth, incident state machine, audit-ack SLA, LLM
> recovery-audit-signoff, physical pager) lives in:
>
> - `/codex/04-architecture/recovery-defence-in-depth-layers.md` — the 5+1 layer model
> - `/codex/04-architecture/incident-gateway-state-machine.md` — 13-state incident lifecycle
> - `/codex/15-runbooks/physical-pager-layer.md` — Layer-4 device comparison + webhook
> - `/codex/15-runbooks/alerting/audit-acknowledgement-flow.md` — Layer-5 6h ack SLA + escalation ladder
> - `plans/active/issues/disaster_recovery.md` — operator-supplied target operating model (sections 1-22)
> - `plans/audit/results/observability_disaster_recovery_audit_2026_05_23.md` — gap audit of target model vs prod
>
> The 11 active plans under `parent_epic: observability_master` close the gap surfaced in the 2026-05-23 audit.

## Recovery Targets by Environment

| Environment     | RTO (Recovery Time) | RPO (Data Loss Tolerance) | Notes                                                                |
| --------------- | ------------------- | ------------------------- | -------------------------------------------------------------------- |
| **Production**  | < 30 minutes        | < 5 minutes               | Trading systems must resume within 30min; max 5min of data loss      |
| **Staging**     | < 1 hour            | < 1 hour                  | Staging can tolerate longer recovery; SIT re-validates after restore |
| **Development** | < 4 hours           | Best effort               | Dev environments are ephemeral; rebuild from manifest if needed      |

## Recovery Tiers

| Tier   | Scope                    | RTO Target   | Method                                      |
| ------ | ------------------------ | ------------ | ------------------------------------------- |
| Tier 0 | Single service rollback  | < 5 minutes  | Cloud Run revision rollback                 |
| Tier 1 | Multi-service rollback   | < 15 minutes | Manifest-pinned version redeploy            |
| Tier 2 | Full environment restore | < 30 minutes | Manifest restore + SIT validation           |
| Tier 3 | Cross-region failover    | < 1 hour     | Secondary region activation (if configured) |

## Restore Procedure from Manifest State

The `workspace-manifest.json` is the SSOT for all repo versions. To restore the full system to a known-good state:

1. **Identify target state**: Check `main_commits.history` in manifest for the last successful promotion
2. **For each repo in `versions` map**:
   ```bash
   VERSION=$(python3 -c "import json; m=json.load(open('workspace-manifest.json')); print(m['versions']['<repo>'])")
   cd <repo> && git checkout "v${VERSION}"
   ```
3. **Redeploy services**: Use deployment-service with the manifest-pinned versions
4. **Validate**: Run SIT against the restored state

## Single Service Rollback (Tier 0)

```bash
# List recent revisions
gcloud run revisions list --service <service> --region asia-northeast1 --limit 5

# Route 100% traffic to previous revision
gcloud run services update-traffic <service> \
  --region asia-northeast1 \
  --to-revisions <previous-revision>=100
```

## Artifact Registry Image Rollback

```bash
# List available tags for a service
gcloud artifacts docker tags list \
  asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-services/<service>

# Deploy a specific previous version
gcloud run deploy <service> \
  --image asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-services/<service>:v<VERSION> \
  --region asia-northeast1

# Verify the rollback
gcloud run services describe <service> \
  --region asia-northeast1 \
  --format='value(status.traffic[0].revisionName)'
```

For batch services (Cloud Build jobs), update the image tag in the Cloud Build trigger config.

## GCS Backup Locations

> **Bucket-name SSOT (O-3 reconciliation 2026-05-12).** The legacy hardcoded bucket names previously listed here
> (`unified-trading-manifests` / `unified-trading-configs` / `unified-market-data` / `unified-ml-models` /
> `unified-audit-logs`) **do not exist** in the canonical SSOT. Every bucket lookup goes through
> `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud=..., kind=..., asset_group=..., env=...)`
> per `deployment-service/configs/cloud-providers.yaml`. See CLAUDE.md § "Bucket-name SSOT (b+)" + the
> `bucket_name_ssot_canonicalisation_2026_05_10.md` plan. Region-pinned: GCP `asia-northeast1`, AWS `ap-northeast-1`.
> The watchdog dict (`deployment-service/scripts/vm/vm_zombie_watchdog.py` § `VM_PREFIX_TO_BUCKET`) is the live registry
> of which bucket pattern serves which VM-prefix.

| Data | Canonical bucket kind (resolve via `resolve_bucket_name(kind=...)`) | Path | Retention | | ------------------ |

| -------------------------------------------------------------------------------------------         |
| --------------------------------------------------------------------------------------------------- |
| --------------------------------------------------------------------------------------------------- | ----------                                                                   |                            |
| Manifest snapshots                                                                                  | `manifest` (asset-group-scoped where applicable; see `cloud-providers.yaml`) |
| `snapshots/YYYY-MM-DD/workspace-manifest.json`                                                      | 90 days                                                                      |                            | Service configs            | `configs` (env-tier: dev / staging / prod |
| via `${DEPLOYMENT_ENV}`)                                                                            | `<service>/config.json`                                                      | 30 days (versioned bucket) |                            | Market data                               | `market-data-tick`      |
| (per asset_group — `cefi` / `defi` / `tradfi` / `sports` / `prediction`)                            |
| `pipeline_mode=<batch                                                                               | live>/asset_group=<ag>/<venue>/<instrument>/YYYY/MM/DD/`                     |
| (`pipeline_mode` in PATH, not bucket name)                                                          | Indefinite                                                                   |                            | ML models                  | `ml-models`                               | `<model>/<version>/`    | Indefinite |
| (tagged)                                                                                            |                                                                              | Audit logs                 | `audit-logs` (per service) | `<service>/YYYY/MM/DD/`                   | 1 year                  |            | Events | `events` (per |
| service / per cloud)                                                                                | `events/<service>/{YYYY-MM-DD}/{correlation_id}/hour={H}/*.jsonl`            | 90 days (per retention     |
| policy)                                                                                             |                                                                              | Kill-switch audit          | `kill-switch-audit`        | `audit/kill_switch/{YYYY-MM-DD}/`         | Indefinite (regulatory) |

## Communication Protocol During Incidents

### Severity Levels

| Severity | Description                       | Response Time     | Channel                            |
| -------- | --------------------------------- | ----------------- | ---------------------------------- |
| **SEV1** | Production trading halted         | Immediate         | Telegram alert + direct escalation |
| **SEV2** | Degraded trading (partial outage) | < 15 min          | Telegram alert                     |
| **SEV3** | Staging/CI broken                 | < 1 hour          | Telegram alert (automated)         |
| **SEV4** | Non-critical (dev env, docs)      | Next business day | GitHub issue                       |

### Incident Response Steps

1. **Detect**: Automated alerts (dead man switch, starvation detector, health checks)
2. **Acknowledge**: Respond in Telegram within response time SLA
3. **Triage**: Determine severity; check if automated recovery is possible
4. **Mitigate**: Rollback if needed (image rollback, manifest restore)
5. **Resolve**: Fix root cause; deploy fix through normal pipeline
6. **Post-mortem**: Document in `unified-trading-pm/plans/ops/post-mortems/` within 48h for SEV1/SEV2

## Dependency Failure Matrix

| Dependency        | Impact if Down                     | Mitigation                                      |
| ----------------- | ---------------------------------- | ----------------------------------------------- |
| GitHub Actions    | No CI/CD, no version cascade       | Manual deploy from local; pre-built images      |
| GCP Cloud Run     | Services unreachable               | Multi-region if configured; manual VM fallback  |
| Artifact Registry | Cannot pull images for new deploys | Cached images on existing revisions still serve |
| Pub/Sub           | Event delivery stalled             | Services queue locally; replay on recovery      |
| BigQuery          | Analytics/reporting delayed        | Non-critical path; services continue trading    |
| Telegram          | No alert delivery                  | GitHub Issue fallback via `notify_critical()`   |

## Testing DR Procedures

DR restore should be tested quarterly:

1. Pick a non-production environment (staging preferred)
2. Simulate failure: scale service to 0 replicas
3. Execute Tier 0 rollback; measure actual RTO
4. Execute Tier 2 manifest restore; measure actual RTO
5. Document results in `plans/ops/dr-test-results/`
