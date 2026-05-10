---
title: "Bucket-name SSOT triple-drift — yaml SSOT vs service config templates vs UTL bucket_naming resolver"
created: 2026-05-10
author: agent-arb-fundrate-c2
source:
  - deployment-service/configs/cloud-providers.yaml (workspace bucket SSOT)
  - features-service/features_service/{family}/config.py (per-family bucket templates)
  - unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py (UTL resolver)
locked_by: live-defi-rollout
locked_since: 2026-05-10
---

# Bucket-name SSOT triple-drift — three sources of truth disagree

> **Severity**: P1 — silent operational failure surface. The disagreement caused 7 of 55 deleted-but-needed empty
> buckets in the 2026-05-10 features-bucket cleanup session (recovered by re-provisioning; zero data lost). Future
> consolidated-service launches will fail first-write if any of the three layers drifts further. **Blast radius**: every
> bucket-writing service (features-service + downstream consumers, MTDS, instruments-service, pnl-attribution) + every
> bucket-provisioning script (Terraform / setup-defi-buckets.sh / etc.). **Suggested owner**: a UTL/UAC infra agent —
> the fix is a one-direction lift-resolver-into-config canonicalisation.

## What I found

Three layers each claim to be the bucket-name SSOT; each produces a *different* canonical name for the same
`(service, asset_group)` pair.

### Layer 1 — `deployment-service/configs/cloud-providers.yaml` (workspace yaml SSOT)

```yaml
gcp:
  storage:
    features-delta-one:
      CEFI: "features-delta-one-cefi-${DEPLOYMENT_ENV}-${GCP_PROJECT_ID}"
      TRADFI: "features-delta-one-tradfi-${DEPLOYMENT_ENV}-${GCP_PROJECT_ID}"
```

Canonical name shape: `features-delta-one-cefi-${DEPLOYMENT_ENV}-${pid}` — **includes a `${DEPLOYMENT_ENV}` env suffix
(`dev`/`staging`/`prod`/`test`)**.

### Layer 2 — Consolidated `features-service` per-family `config.py` (Python templates)

```python
# features-service/features_service/delta_one/config.py:154
output_bucket_template: str = Field(
    default="features-delta-one-{asset_group_lower}-{project_id}",
    ...
)
```

Canonical name shape: `features-delta-one-cefi-{pid}` — **no DEPLOYMENT_ENV suffix**. Drops the env axis entirely.

Same pattern across all 8 family configs:

| File | Template |
| ---- | -------- |
| `calendar/config.py:42` | `features-calendar-{project_id}` (no asset_group, no env) |
| `cross_instrument/config.py:130,136` | `features-delta-one-{asset_group_lower}-{project_id}` + `features-cross-instrument-{asset_group_lower}-{project_id}` (no env) |
| `delta_one/config.py:154` | `features-delta-one-{asset_group_lower}-{project_id}` (no env) |
| `multi_timeframe/config.py:167,172` | `features-delta-one-{asset_group_lower}-{project_id}` + `features-multi-timeframe-{asset_group_lower}-{project_id}` (no env) |
| `onchain/config.py:76,89` | `features-onchain-{project_id}` + `features-onchain-defi-{project_id}` (asymmetric: both project-wide AND asset-keyed) |
| `volatility/config.py:47` | `features-volatility-{asset_group_lower}-{project_id}` (no env) |
| `sports/.../*.py` | `features-sports-{project_id}` (no asset_group, no env) |

### Layer 3 — `unified_trading_library.cloud_interface.bucket_naming` (UTL resolver)

Per module docstring (file:1):

> Workspace-wide audit (2026-05-08) flagged ``70+`` inline ``f"gs://{bucket}/..."`` and ``f"s3://{bucket}/..."``
> formatters scattered across services. Each consumer hardcoded its own bucket-name template, which silently drifted
> from the yaml SSOT every time a new asset_group / data_kind landed (e.g. ``dex-pools``, ``evm-defi``, ``solana-defi``,
> ``events``, ``config-store`` were added to the yaml but never propagated to ``constants.BUCKET_PREFIXES``). This
> module is the canonical resolver consumers should use; the legacy ``cloud_interface.constants.get_bucket_name`` will
> be migrated to delegate into it as a follow-up step.

The resolver READS the yaml (Layer 1) — so by-construction it matches Layer 1's shape with `${DEPLOYMENT_ENV}`. But
features-service `config.py` templates (Layer 2) DO NOT go through this resolver — they hardcode their own non-env-
suffixed templates. So at runtime, features-service writes to `features-delta-one-cefi-{pid}` while the yaml + UTL
resolver claim the canonical name is `features-delta-one-cefi-{env}-{pid}`.

## Why it matters

**Reference incident 2026-05-10**: workspace-wide features-bucket cleanup deleted 55 empty buckets sourced from the
yaml SSOT shape (`-prod-`, `-staging-`, `-test-`, `-dev-` variants — all 0 bytes because no service writes through the
yaml shape). Then cross-referenced against features-service `config.py` templates and found 7 of those 55 were
*actually* referenced by the service config under a *different* name shape. The deleted buckets were re-provisioned
manually under the service-template name; total 7-minute recovery, zero data lost.

Future failure modes if drift goes unrepaired:

- **New consolidated-service VM launches fail first-write** when the yaml-provisioned bucket name disagrees with the
  service-template bucket name. Operator has to triangulate three SSOTs to figure out which name the running pod is
  trying to write to.
- **Workspace bucket-provisioning scripts** (`setup-defi-buckets.sh`, Terraform modules, etc.) provision buckets per
  yaml SSOT → service config doesn't see them → blank-write-failures → operator-time to debug.
- **UTL resolver claims canonical authority** in its docstring but isn't actually wired into features-service writes.
  Either lift the templates to use the resolver OR document that features-service deliberately bypasses it.
- **Cleanup ops are unsafe** — workspace-grep "what buckets do I actually need?" returns three different answers
  depending on which file you grep. Same shape as the `setup-defi-buckets.sh` / `constants.BUCKET_PREFIXES` /
  `UnifiedCloudConfig` drift flagged 2026-05-08 (handover doc:
  [`plans/active/issues/aws_phase_1_smoke_blockers_2026_05_08.md`](aws_phase_1_smoke_blockers_2026_05_08.md)).

## Recommended decision

Three paths, in order of preference:

- **(a)** Lift features-service `{family}/config.py` templates to call
  `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)` at config-load time. UTL resolver
  becomes single-direction SSOT; yaml is the on-disk truth; service config defers to UTL. Same shape as the
  `unified_trading_library` lift discipline used for `BroadcastSink` / `LiveDataSource` / `ModeHandler` in the
  features-repo-consolidation plan.
- **(b)** Remove the `${DEPLOYMENT_ENV}` suffix from the yaml SSOT to match what services actually use. Simpler but
  loses the env axis (dev/staging/prod can no longer share a project_id without colliding).
- **(c)** Document the asymmetry (yaml = provisioning shape; service config = runtime shape) and add a CI check that
  enforces drift-free relationships. Worst-of-three because the drift persists; just makes it visible.

**(a) is the right shape per workspace "lift to UTL" discipline.** The yaml SSOT already exists and the resolver
already reads it; finishing the loop is the small remaining step.

## Composes with

- `features_repo_consolidation_2026_05_08.md` — same "lift to UTL" pattern; this issue extends the same discipline to
  bucket-naming.
- `aws_phase_1_smoke_blockers_2026_05_08.md` — same SSOT-triple-drift shape; that issue covered AWS-side smoke
  blockers, this one covers GCS-side bucket-name drift.
- `arb_price_dispersion_phase_b_data_blockers_2026_05_10.md` — the cleanup that exposed this issue.

## Reference evidence (file:line citations)

- `deployment-service/configs/cloud-providers.yaml` — yaml SSOT (Layer 1)
- `features-service/features_service/calendar/config.py:42`
- `features-service/features_service/onchain/config.py:76,89`
- `features-service/features_service/delta_one/config.py:154`
- `features-service/features_service/volatility/config.py:47`
- `features-service/features_service/cross_instrument/config.py:130,136`
- `features-service/features_service/multi_timeframe/config.py:167,172`
- `features-service/features_service/sports/{app/pubsub/subscriber.py:60,cli/batch_write.py:74,cli/handlers/batch_handler.py:445,cli/handlers/live_handler.py:77}`
- `unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py` — UTL resolver (Layer 3)
