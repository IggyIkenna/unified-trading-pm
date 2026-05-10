---
title:
  "Bucket-name SSOT canonicalisation — collapse three-layer drift (yaml + per-family config.py + UTL resolver) to one"
status: active
created: 2026-05-10
deadline: pre-cutover (P1 — silent operational failure surface; first-write failures on new consolidated services)
horizon: 1-2 day scope-bounded
spawned_from: plans/archive/issues/bucket_name_ssot_triple_drift_2026_05_10.md (archived 2026-05-10)
locked_by: live-defi-rollout
locked_since: 2026-05-10
execution:
  owner: UTL/UAC infra agent
  cadence: one-shot
  verifier:
    workspace-grep returns 0 hits for inline f"gs://{bucket}/..." formatters that don't go through UTL resolver;
    features-service + MTDS + instruments-service first-writes resolve via single SSOT
  last_executed: NEVER
---

# Bucket-name SSOT canonicalisation

> **Severity**: P1 — silent operational failure surface. The disagreement caused 7 of 55 deleted-but-needed empty
> buckets in the 2026-05-10 features-bucket cleanup session (recovered by re-provisioning; zero data lost). Future
> consolidated-service launches will fail first-write if any of the three layers drifts further.
>
> **Blast radius**: every bucket-writing service (features-service + downstream consumers, MTDS, instruments-service,
> pnl-attribution) + every bucket-provisioning script (Terraform / `setup-defi-buckets.sh` / `setup-buckets.sh`).
>
> **Suggested owner**: a UTL/UAC infra agent — the fix is a one-direction lift-resolver-into-config canonicalisation.

## Why this plan exists

Spawned 2026-05-10 from the archived issue
[`plans/archive/issues/bucket_name_ssot_triple_drift_2026_05_10.md`](../archive/issues/bucket_name_ssot_triple_drift_2026_05_10.md).

Three layers each claim to be the bucket-name SSOT; each produces a _different_ canonical name for the same
`(service, asset_group)` pair:

1. **`deployment-service/configs/cloud-providers.yaml`** (workspace yaml SSOT) — includes `${DEPLOYMENT_ENV}` suffix
2. **`features-service/features_service/{family}/config.py`** Python templates — drops `${DEPLOYMENT_ENV}` axis
3. **`unified_trading_library.cloud_interface.bucket_naming`** (UTL resolver) — reads yaml so matches Layer 1

The 2026-05-08 partial-mitigation at UTL@`780a9575` shipped the resolver but did NOT migrate Layer 2's per-family
config.py templates onto it. Workspace partially-shifted-but-not-yet-canonicalised state.

## Done definition

- [ ] **[AGENT] P1**. Decide canonical SSOT layer. Options: (a) Yaml is canonical; lift all per-family `config.py`
      templates onto `bucket_naming.resolve_bucket_name()` calls (drops the local templates; `${DEPLOYMENT_ENV}` suffix
      gains universal coverage); (b) Per-family configs are canonical; remove `${DEPLOYMENT_ENV}` from yaml entries
      (drops env axis workspace-wide). Recommendation: (a) — yaml SSOT preserves env axis for prod/staging/dev/test
      isolation.
- [ ] **[SCRIPT] P1**. Migrate per-family `features-service/features_service/{family}/config.py`
      `output_bucket_template` fields to call `bucket_naming.resolve_bucket_name(...)` lazily at runtime (or expose
      template via the resolver).
- [ ] **[SCRIPT] P1**. Workspace QG step `STEP 5.6X` AST-walks for inline `f"gs://{bucket}/..."` /
      `f"s3://{bucket}/..."` formatters; fails CI if any new ones land outside the resolver.
- [ ] **[SCRIPT] P1**. Add yaml-vs-resolver parity unit test (already shipped at UTL@`24f9b2cb` for 10 DeFi bucket
      entries; extend coverage to features-\* + sports + tradfi).
- [ ] **[AGENT] P1**. Plan-flip cite + workspace-wide grep audit table verifying zero remaining drift sites.

## Full-execution criterion (per "Plans Run To Actual Completion" HARD RULE)

- ✅ Workspace-grep `f"gs://{<not-a-resolver-call>}` returns 0 hits across all service repos.
  - **What ran**: ripgrep workspace-wide.
  - **Verification**: explicit list of 0 sites in plan-flip commit body.
- ✅ features-service consolidated launch resolves bucket names against the same yaml SSOT that `setup-buckets.sh`
  provisions.
  - **What ran**: real launch on a same-region GCE VM.
  - **Verification**: first-write succeeds + manifest write succeeds against the resolver-derived bucket name.

## Dependencies / sequencing

- **Pre-req**: features-service consolidation must be far enough along to expose the family `config.py` templates (they
  are post-Phase 4 of `features_repo_consolidation_2026_05_08.md`).
- **Pre-cutover**: this plan SHOULD ship before May-23 cutover; first-write failures on consolidated-service launches
  block the live-pipeline path.

## Composes with

- `aws_migration_defi_first_2026_05_07.md` — AWS yaml has features-calendar entry but GCP doesn't; the parity regression
  test at UTL@`780a9575` fires on this drift. Same canonicalisation surface; do parity sweep here too.
- Workspace foot-gun #1 — surgical staging when editing feature-service config.py files (parallel-agent territory).

## References

- Archived issue:
  [`plans/archive/issues/bucket_name_ssot_triple_drift_2026_05_10.md`](../archive/issues/bucket_name_ssot_triple_drift_2026_05_10.md)
- Existing UTL resolver: `unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py`
  (UTL@`780a9575` — partial mitigation, 10 DeFi buckets routed)
- Existing parity test: `unified-trading-library/tests/cloud_interface/unit/test_bucket_naming.py` (UTL@`24f9b2cb`)
- Yaml SSOT: `deployment-service/configs/cloud-providers.yaml`
