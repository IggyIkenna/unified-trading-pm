---
title:
  "Bucket-name SSOT canonicalisation — collapse three-layer drift (yaml + per-family config.py + UTL resolver) to one +
  provision env-tiered buckets to match yaml (operator decision option b 2026-05-11)"
status: active
created: 2026-05-10
deadline:
  2026-05-15 freeze gate (Phase 1 code-complete) for SSOT collapse + yaml-add-missing-keys; 2026-05-19 Phase 2 window
  for env-tier provisioning + flat→tiered data migration
horizon: cross-cycle (Phase 1 code-complete in ~2 days, Phase 2 physical migration in 4-day window)
spawned_from: plans/archive/issues/bucket_name_ssot_triple_drift_2026_05_10.md (archived 2026-05-10)
locked_by: live-defi-rollout
locked_since: 2026-05-10
execution:
  owner:
    Harsh slot 4 (provisioning + L2 config.py migration + data migration coordination); Ikenna slot 1 (operator
    decisions, cross-plan banner sweep)
  cadence: one-shot
  verifier:
    workspace-grep returns 0 hits for inline f"gs://{bucket}/..." formatters that don't go through UTL resolver;
    features-service + MTDS + instruments-service first-writes resolve via single SSOT; every yaml-resolver-derived
    bucket name returns 200 from `gcloud storage ls` / `aws s3 ls`; flat-bucket data migrated to env-tiered buckets with
    ≤0.01% drift; flat buckets archived
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

## FINDING 2026-05-11 (slot 4) — the yaml SSOT contradicts the provisioned features-\* infra (migration-blocking)

> **OPERATOR DECISION 2026-05-11 (Ikenna): option (b) — make reality match the yaml.** Provision env-tiered buckets
>
> - migrate flat-bucket data into them + repoint readers/writers via `resolve_bucket_name()`. The yaml STAYS AS-IS as
>   the canonical SSOT (with additions: missing `prediction`/`sports` keys + GCP `features-calendar` uncommented +
>   `-test-` variant canonical shape modeled). The lost prod/staging/dev isolation that motivated the yaml's Group-B
>   env-tier convention IS the architectural target — the system is going live with real money 2026-05-23, env-isolation
>   is a Citadel-grade requirement. The migration cost is high but it's the right architecture; defer the operational
>   complexity to Phase 2 of `code_freeze_migrate_backfill_sequencing_2026_05_10.md` (one-shot physical migration window
>   2026-05-15→05-19). **Slot 4 + Harsh slot 1 had recommended option (a) (drop the env tier from yaml) — operator
>   overrode to (b) per CLAUDE.md "bucket-naming SSOT decisions are Ikenna's human-approval surface."**
>
> **Severity**: P1 / migration-blocking — not a same-day operational outage (the L2 config.py templates are what's
> actually used in prod today, and they match reality), but the resolver-derived names don't exist on disk so any
> consolidated-service launch via `resolve_bucket_name()` will fail first-write until provisioning lands. **Blast
> radius**: every features-\* / ml-\* bucket-writing service + `setup-buckets.sh` + Terraform / IaC + the data inside
> the existing flat buckets (must migrate without loss). **Owner**: Harsh slot 4 implementation per work-split, with
> coordination from Ikenna slot 1 + slot 5 anti-sequencing audit.

GCP probe (2026-05-11, project `central-element-323112`, `gcloud storage buckets list`):

| yaml entry (current)                                                                                                          | resolver would produce (DEPLOYMENT_ENV=prod)             | bucket that ACTUALLY exists                                                                                                                                 | verdict                                                                                                      |
| ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `features-delta-one.CEFI = features-delta-one-cefi-${DEPLOYMENT_ENV}-${GCP_PROJECT_ID}`                                       | `features-delta-one-cefi-prod-central-element-323112` ❌ | `features-delta-one-cefi-central-element-323112` (no env)                                                                                                   | **yaml WRONG** (spurious env tier)                                                                           |
| (yaml has only CEFI/TRADFI/DEFI for `features-delta-one`)                                                                     | —                                                        | also exist: `features-delta-one-prediction-...`, `features-delta-one-sports-...`                                                                            | **yaml MISSING keys**                                                                                        |
| `features-onchain.CEFI = features-onchain-cefi-${DEPLOYMENT_ENV}-${GCP_PROJECT_ID}` / `.DEFI = ...defi-${DEPLOYMENT_ENV}-...` | `features-onchain-cefi-prod-...` ❌                      | `features-onchain-central-element-323112` (FLAT — no AG, no env) + `features-onchain-defi-central-element-323112` (per-AG=defi, no env)                     | **yaml WRONG** (L2's "shared" + "defi" shapes are right)                                                     |
| `features-volatility.CEFI = ...cefi-${DEPLOYMENT_ENV}-...` (CEFI/TRADFI only)                                                 | `features-volatility-cefi-prod-...` ❌                   | `features-volatility-{cefi,defi,prediction,sports,tradfi}-central-element-323112` (per-AG, no env)                                                          | **yaml WRONG + MISSING keys**                                                                                |
| `features-sports = features-sports-${DEPLOYMENT_ENV}-${GCP_PROJECT_ID}`                                                       | `features-sports-prod-...` ❌                            | `features-sports-central-element-323112` (flat, no env)                                                                                                     | **yaml WRONG** (spurious env)                                                                                |
| `features-prediction = features-prediction-${DEPLOYMENT_ENV}-...`                                                             | `features-prediction-prod-...` ❌                        | _(no `features-prediction-*` bucket on GCP at all)_ + `features-cross-instrument-prediction-central-element-323112` exists                                  | **bucket NOT PROVISIONED** / yaml-vs-reality unknown                                                         |
| `features-calendar` (GCP entry commented out)                                                                                 | (raises Unknown kind)                                    | `features-calendar-central-element-323112` (flat) — IT EXISTS                                                                                               | **yaml should UNCOMMENT** (the AWS-only allowlist entry from UTL@`e8dc6e3` is stale once GCP entry is added) |
| `instruments-store.CEFI = instruments-store-cefi-${GCP_PROJECT_ID}` (no env)                                                  | `instruments-store-cefi-central-element-323112` ✅       | `instruments-store-cefi-central-element-323112` ✅ (+ `-test-` variant `instruments-store-cefi-test-...`)                                                   | **yaml CORRECT** (env-less); `-test-` not modelled                                                           |
| `market-data.CEFI = market-data-tick-cefi-${GCP_PROJECT_ID}` (no env)                                                         | `market-data-tick-cefi-central-element-323112` ✅        | `market-data-tick-cefi-central-element-323112` ✅ (+ inconsistent `-test-` variants: `market-data-tick-cefi-test-...` AND `market-data-tick-test-cefi-...`) | **yaml CORRECT** (env-less); `-test-` shapes inconsistent on disk                                            |

**Net**: the yaml's Group-B env-tier convention (`features_*`, `ml_*`, `strategy`, `execution` get `${DEPLOYMENT_ENV}`)
is **aspirational, not provisioned** — at least for the GCP `features-*` buckets, which are all flat. Either the prod
buckets are misnamed (should have a `-prod-` tier) or the yaml is wrong (should drop the tier). For a P1-pre-cutover
migration these MUST agree before the config.py migration lands; the safest fix is to make the yaml match reality (drop
the env tier from GCP `features-*`), since renaming buckets = data migration = much riskier. This is now **Phase 0** of
this plan and **Q4** below (operator decision).

## Done definition

- [x] **[AGENT] P1**. Decide canonical SSOT layer. Options: (a) Yaml is canonical; lift all per-family `config.py`
      templates onto `bucket_naming.resolve_bucket_name()` calls (drops the local templates; `${DEPLOYMENT_ENV}` suffix
      gains universal coverage); (b) Per-family configs are canonical; remove `${DEPLOYMENT_ENV}` from yaml entries
      (drops env axis workspace-wide). **DECISION 2026-05-11 (slot 4): (a) — yaml SSOT is canonical AS THE ARCHITECTURAL
      DIRECTION**. Rationale: (1) keeps the env axis available for prod/staging/dev/test isolation; (2) yaml already
      models GCP↔AWS asymmetries (`tick-` infix on GCP `market-data`, AWS-only `features-calendar`) the per-family
      templates don't; (3) the UTL resolver already reads the yaml — so (a) just _removes_ duplicate layers, no new
      SSOT. Collapse targets: L2 config.py `*_bucket_template` Field defaults → `resolve_bucket_name()`; legacy
      `cloud_interface.constants.get_bucket_name` + `BUCKET_PREFIXES` → delegate to `resolve_bucket_name()`.
- [x] **[AGENT] P0**. **Phase 0a — operator decision on yaml-vs-provisioned-infra mismatch (Q4 below).** OPERATOR
      DECISION 2026-05-11 (Ikenna): **option (b) — make reality match the yaml.** Provision env-tiered features-\* /
      ml-\* / strategy-\* / execution-\* buckets to match the yaml's Group-B convention; migrate existing flat-bucket
      data into the env-tiered buckets; repoint readers/writers via `resolve_bucket_name()`. Yaml stays as-is as the
      canonical SSOT (with additions per Phase 0b). Slot 4 + Harsh slot 1 had recommended option (a) (drop the env tier
      from yaml) on the basis that the env-tier was aspirational-not-provisioned; operator overrode to (b) on the
      strategic basis that prod/staging/dev isolation is a Citadel-grade requirement for May-23 live cutover. See § Q4
      below for full operator answer text + cross-side ping confirmation to Harsh main.
- [x] **[AGENT] P0**. **Phase 0b — yaml additive corrections (NO removals; Phase 1 code-complete scope).** Add the
      missing per-asset_group keys to `deployment-service/configs/cloud-providers.yaml`: `prediction`/`sports` for
      `features-delta-one`/`features-volatility`/`features-onchain`/`instruments-store`/`market-data` (those buckets
      either exist already or will be provisioned per Phase 0c). Uncomment the GCP `features-calendar` entry (the bucket
      `features-calendar-central-element-323112` already exists). Model one canonical `-test-` E2E variant shape in the
      yaml (current on-disk shapes are inconsistent: `instruments-store-cefi-test-{pid}` vs
      `market-data-tick-test-cefi-{pid}` — operator/Harsh slot 4 picks one and migrates the other). Update the parity
      test (UTL@`e8dc6e3`'s `_FEATURES_PIPELINE_KINDS` + `_KNOWN_YAML_ASYMMETRIES`) to match. **SHIPPED
      deployment-service@`a7eba4f` + UTL@`2118b1e` (slot 4 2026-05-11)**: added `PREDICTION`+`SPORTS` to
      `features-delta-one`/`features-volatility` (env-tiered, both clouds); `SPORTS` to
      `market-data`/`instruments-store` per-AG dicts (env-less Group-A — for now; Phase 0e adds the `${DEPLOYMENT_ENV}`
      tier); uncommented GCP `features-calendar` (env-less, both clouds); added a `gcp.storage` §-header comment doc'ing
      the shape conventions (Group A env-less vs Group B env-tier-after-AG; prediction = dedicated `*-prediction` flat
      keys vs sports = `asset_group="sports"` routing; canonical `-test-` shape = `{prefix}-{ag}-test-{pid}` via
      `DEPLOYMENT_ENV=test` substitution for env-tiered kinds — legacy before-AG `market-data-tick-test-*` variants
      deprecated). Parity test: snapshot + tests updated; `_KNOWN_YAML_ASYMMETRIES` emptied (`features-calendar` no
      longer one-cloud-only); new `test_resolve_features_prediction_sports_keys`; 92 tests pass. **Two intentional
      deviations from the literal todo text**: (1) did NOT add `prediction`/`sports` to `features-onchain` — onchain =
      DeFi on-chain metrics (cefi/defi outputs only; no `features-onchain-{prediction,sports}-*` buckets exist on disk);
      (2) did NOT add `prediction` to the `instruments-store`/`market-data` per-AG dicts — prediction has dedicated
      `instruments-store-prediction` / `market-data-tick-prediction` flat yaml keys (avoiding a double-SSOT). status:
      done — note: "the Group-A env-tier ADD is Phase 0e (separate todo); the `-test-` variant on-disk MIGRATION
      (deleting the before-AG `market-data-tick-test-*` buckets) is operationally-pending — they're throwaway E2E
      artefacts."
- [ ] **[SCRIPT] P0**. **Phase 0c — provision env-tiered buckets to match yaml (Harsh slot 4 scope; Phase 2 physical
      migration window 2026-05-15→05-19).** For every yaml entry carrying `${DEPLOYMENT_ENV}`, provision the
      corresponding bucket on both GCP (`gcloud storage buckets create gs://<resolver-derived-name>`) and AWS
      (`aws s3 mb s3://<resolver-derived-name>`) via Terraform / `setup-buckets.sh` extensions. Coverage matrix:
      `(kind, asset_group, env, cloud)` cross-product per yaml. Estimate: ~30-50 new buckets per cloud per env; ~3 envs
      (staging/prod/development) × 2 clouds = ~180-300 new buckets total. Provision via Terraform module
      `deployment-service/terraform/modules/storage_buckets` (or extend `setup-buckets.sh` — operator picks at
      implementation time). Verification: `gcloud storage ls` / `aws s3 ls` returns 200 for every yaml-derived name.
      status: blocked — note: "Harsh slot 4 owns; Phase 2 of code_freeze_migrate_backfill_sequencing umbrella."
- [ ] **[SCRIPT] P0**. **Phase 0d — migrate flat-bucket data into env-tiered buckets (Phase 2 physical migration; data
      preservation critical).** For every existing flat bucket (`features-delta-one-cefi-{pid}`,
      `features-onchain-{pid}`, `features-sports-{pid}`, `features-volatility-{ag}-{pid}`, `features-calendar-{pid}`,
      etc. — extended per Phase 0e to include raw-tick + instruments-store + manifest buckets), copy ALL data into the
      new env-tiered prod bucket (`features-delta-one-cefi-prod-{pid}`, etc.) using
      `gcloud storage cp -r     --preserve-symlinks` (GCP) / `aws s3 sync` (AWS). Drift verification: post-copy object
      count + total size + spot-check 100 random parquets per bucket must match within 0.01%. **Cutover window**: pause
      writes to the flat buckets during the migration (operator-coordinated; ~few hours per asset_group depending on
      volume). Post-migration: archive (don't delete) the flat buckets to a `*-archived-flat-2026-05-19/` prefix +
      retention policy 30 days, then delete after manifest + downstream verification confirms zero readers still hit the
      flat names. status: blocked — note: "DEFERRED-AFTER Phase 0c provisioning; Phase 2 of code_freeze umbrella; Harsh
      slot 4 owns coordinated with operator for the write-pause window."

#### Phase 0e through 0i — full (b+) env-aware bucket architecture extension (operator direction 2026-05-11)

> **OPERATOR DIRECTION 2026-05-11 (Ikenna, extending option b → b+)**: extend the env-tier convention from yaml's
> Group-B-only (features-\* / ml-\* / strategy-\* / execution-\*) to **ALL buckets** (raw-tick / instruments-store /
> manifest / etc.). Add a **prod → staging/dev sync script** with truncated date window (1-2 years) so dev/staging
> aren't full-history (avoids prohibitive storage cost). All buckets in the **same region** (asia-northeast1 on GCP, AWS
> region per yaml) to avoid cross-region egress. **Verified**: deployment UI already env-tiered per
> [`codex/05-infrastructure/deployment-ui-architecture.md`](../../codex/05-infrastructure/deployment-ui-architecture.md)
> § "Environment tier" — no new toggle work needed; resolved from `window.location.hostname`, each env has its own
> domain → its own deployment-api Cloud Run → its own GCS bucket scope → its own service account.

- [x] **[AGENT] P0**. **Phase 0e — extend yaml env tier to the `${DEPLOYMENT_ENV}`-MISSING Group-A bucket kinds (Phase 1
      code-complete scope).** Added `${DEPLOYMENT_ENV}` (after asset_group for per-AG kinds) to: `market-data` (per-AG),
      `instruments-store` (per-AG), `features-calendar` (flat), `market-data-tick-prediction` (flat),
      `instruments-store-prediction` (flat) — both clouds. **SHIPPED deployment-service@`a5c2082` + UTL@`ba6089c`**
      (parity test snapshot + `test_resolve_market_data_per_cloud_shape` /
      `test_resolve_instruments_store_per_asset_group` / `test_resolve_features_prediction_sports_keys` /
      `test_features_calendar_resolves_both_clouds` updated; `market-data-tick-prediction` +
      `instruments-store-prediction` trimmed from the snapshot — covered by the env-tier-agnostic live-yaml pin
      `_FEATURES_PIPELINE_KINDS` — to keep snapshot lines under the 100-char cap). All env-tiered names verified to fit
      the 63-char bucket-name limit on both clouds. §-header comment in `cloud-providers.yaml` updated. **Composes
      with**: `pipeline_mode={batch_databento, live_websocket, live_rest}` hive partition INSIDE the bucket — env tier
      is at the BUCKET NAME level, pipeline_mode at the PATH level; orthogonal axes. status: done — note: "code-first
      per code_freeze sequencing — resolver returns env-tiered names now; Phase 0c provisions + Phase 0d migrates the
      flat data (2026-05-15→05-19). features-service config.py already routes through `resolve_bucket()` (Done-def #2
      @`8f03ceeb`) so it picks up the new shape. The remaining env-less GCP entries are split into the new sub-todo
      below."
- [ ] **[SCRIPT] P1**. **DEFERRED (split off from Phase 0e)** — env-tier the remaining env-less GCP yaml entries that
      Phase 0e did not touch: `dex-pools` / `dex-swaps` / `evm-defi` / `eigenlayer-rewards` / `solana-defi` (DeFi raw
      on-chain — AWS already env-tiered, GCP env-less — clean `${DEPLOYMENT_ENV}` add); `pnl-store-defi` /
      `positions-store-defi` / `risk-store-defi` (GCP shape is `pnl-store-{pid}-defi` asset-group-as-suffix vs AWS
      `unified-trading-pnl-store-defi-{env}-{account}` — needs a SHAPE-ALIGNMENT decision, not just an env-tier add —
      and a data migration since the GCP bucket names change); `config-store` (GCP `config-store-{pid}` vs AWS
      env-tiered — ConfigStore hot-reload bucket, modest blast radius); `events` (GCP `{pid}-events` vs AWS env-tiered —
      **HIGH blast radius**: `{pid}-events` is referenced workspace-wide per the "No fire-and-forget VM launches" rule
      `gs://{pid}-events/events/{service}/...` — needs operator confirm whether `events` stays env-less like
      `terraform-state`/`secrets` or goes env-tiered). status: todo — note: "2026-05-11 slot 4 — surfaced while doing
      Phase 0e; scoped out of Phase 0e because (a) the pnl/positions/risk ones need a shape decision + migration, (b)
      `events` needs operator sign-off given the workspace-wide `{pid}-events` references. The DeFi-raw `dex-*`/`*-defi`
      ones are a clean add (do those first); `config-store` next; `pnl-store-defi`/etc + `events` are operator-gated."
- [ ] **[SCRIPT] P0**. **Phase 0f — VM launcher scripts read `DEPLOYMENT_ENV` (Phase 1 code-complete scope).** Audit
      every script under `deployment-service/scripts/vm/` (~30 launchers per CLAUDE.md "VM launcher script SSOT") for
      hardcoded bucket references; ensure each launcher reads `DEPLOYMENT_ENV` from env / CLI flag and passes it to the
      VM via `metadata` so the VM's bucket-resolution call lands on the right env-tiered bucket. Default to
      `DEPLOYMENT_ENV=prod` for production launches, `DEPLOYMENT_ENV=staging` for staging launches, etc. Add a
      `--env <prod|staging|dev>` CLI flag to each launcher OR centralise via a single helper script that every launcher
      sources. Workspace QG step (companion to STEP 5.69) AST-walks launcher scripts for bucket references not flowing
      through the env-aware helper. status: todo — note: "Phase 1 code-complete scope; ~30 launchers; bulk audit + bulk
      edit."
- [x] **[AGENT] P0**. **Phase 0g — verify deployment UI env-tier resolution (already shipped).** ✅ VERIFIED via
      [`codex/05-infrastructure/deployment-ui-architecture.md`](../../codex/05-infrastructure/deployment-ui-architecture.md)
      § "Environment tier (line 33-47, 119-140)": deployment UI env tier is RESOLVED FROM `window.location.hostname`
      (not via in-UI toggle); each tier (DEV / STAGING / PROD) has its own domain → its own deployment-api Cloud Run
      instance → its own GCS event/log bucket scope → its own service account scoped to that env's projects only.
      Cross-env data leakage is impossible because the deployment-api per env uses its own service account. **No
      additional work**: env-aware UI is shipped. The header env badge (read-only; clicking shows tooltip with resolved
      env + API base URL + cloud target) is the only operator-visible env signal. **Cross-check under (b+)**: confirm
      the per-env deployment-api correctly resolves env-tiered bucket names via
      `resolve_bucket_name(cloud=..., kind=..., asset_group=..., env=...)` once Phase 0c provisioning lands. If the API
      currently hardcodes flat bucket names anywhere (audit at impl time), fix in same logical unit. status: done
      (verification only) — note: "deployment UI env-tier shipped pre-2026-05-11; operator's instinct correct."
- [ ] **[SCRIPT] P0**. **Phase 0h — sync script (prod → staging/dev) with truncated date window + same-region
      enforcement (Phase 1 code-complete scope ships the script; Phase 3 / post-cutover initial execution).** New script
      `deployment-service/scripts/sync-buckets-prod-to-staging.sh` (and `-to-dev.sh` variant). Per `(kind, asset_group)`
      cross-product, copies the last `N` years (default `N=2` for staging, `N=1` for dev; operator-tunable per yaml) of
      data from the prod bucket to the staging/dev bucket. Same-region constraint: enforce
      `--source-region == --dest-region`; abort if mismatch (no cross-region egress). Date window: read parquet hive
      partition `day=YYYY-MM-DD`, copy only `day >= today - N*365` paths. Idempotent: re-running skips already-synced
      files (gsutil `-n` dry-run + diff). Schedule: Cloud Scheduler daily cron (default 02:00 UTC, low activity) — or
      operator-triggered if real-time isn't needed. Manifest sync: also re-run manifest consolidator on staging/dev
      after data sync so the staging/dev manifest matches the truncated window. Verification: post-sync manifest row
      count in staging/dev = (prod row count) for `day >= today - N*365`; spot-check 100 random parquets readable.
      status: todo — note: "Script ships Phase 1; first execution Phase 3 or post-cutover (no urgency pre-2026-05-23
      since dev/staging not yet in active use)."
- [x] **[AGENT] P1**. **Phase 0i — region-pinning audit + enforcement (Phase 1 code-complete scope; OPERATOR RATIFIED
      ap-northeast-1 2026-05-11).** Audit yaml entries for region: GCP entries are all `asia-northeast1` (per
      `${GCS_REGION:-asia-northeast1}`); **AWS now ratified `ap-northeast-1` (Tokyo) per operator decision (a)
      2026-05-11** — matched-region with GCP, zero-cost ratification (the 10 DeFi buckets shipped 2026-05-08 via
      `setup-defi-buckets.sh:28` already default to `ap-northeast-1`). Cross-cloud region: GCP asia-northeast1 ↔ AWS
      ap-northeast-1 = same metro Tokyo (~1ms RTT,
      ~$0.01-0.02/GB cross-cloud egress vs ~$0.09/GB trans-Pacific = ~5×
      cheaper). Within-cloud syncing (Phase 0h) is $0. Bucket provisioning (Phase 0c) creates buckets in canonical
      region; reject any `gcloud storage buckets create --location=<other-region>` / `aws s3 mb --region=<other>`.
      **PM stub yaml** `configs/cloud-providers.yaml:59` updated `${AWS_REGION:-us-east-1}`→`${AWS_REGION:-ap-northeast-1}`.     Decision brief: [`plans/active/issues/aws_region_decision_brief_2026_05_11.md`](issues/aws_region_decision_brief_2026_05_11.md).
      status: done — region pinning canonicalised; Phase 0c bucket provisioning targets ap-northeast-1 on AWS.

**Net scope under (b+) — AI-day budget**: Phase 0a (done, decision recorded) + Phase 0b (~0.5 day) + Phase 0c (~2-3 days
for ~600+ new buckets across both clouds × 3 envs × all kinds) + Phase 0d (~2-3 days for full data migration with
truncated window for dev/staging) + Phase 0e (~1 day yaml extensions) + Phase 0f (~1-2 days launcher script audit +
edits across ~30 scripts) + Phase 0g (✅ done, verification only) + Phase 0h (~1-2 days sync script ship) + Phase 0i
(~0.5 day region audit) + done-def #2 (L2 config.py migration ~1 day, blocked-after Phase 0c) + done-def #3 (legacy
delegate ~0.5 day) + done-def #5 (QG STEP 5.69 ~0.5 day, blocked-after #2) + done-def #6 (audit table ~0.5 day,
blocked-after all). **Total: ~10-13 AI-days under (b+)** vs ~3 under (a). Spans Phase 1 code-complete (deadline
2026-05-15) + Phase 2 physical migration window (2026-05-15→05-19) + Phase 3 backfill resumption verification
(post-2026-05-19).

- [x] **[SCRIPT] P1**. Migrate per-family `features-service/features_service/{family}/config.py` `*_bucket_template`
      Field defaults to call `bucket_naming.resolve_bucket_name(...)` lazily at runtime (delete the
      `Field(default="...")` template + repoint `get_*_bucket(...)` method bodies). **SHIPPED
      features-service@`8f03ceeb` (slot 4 2026-05-11, sub-agent fan-out)** — new
      `features_service.common.resolve_bucket(*, kind, asset_group=None)` wrapper over UTL `resolve_bucket_name` (maps
      `CLOUD_PROVIDER=local→gcp` for test/dev; narrows the str AG to the resolver's `AssetGroup` Literal via `cast`).
      Migrated: `delta_one` (input→`market-data`, output→`features-delta-one`, instruments_store→`instruments-store`),
      `volatility` (input→`market-data`, output→`features-volatility`), `onchain` (input→`market-data`,
      output/io_output→`features-onchain`+`asset_group="defi"` since onchain = DeFi metrics,
      io_input→`instruments-store`+`defi`; + `feature_writer.py` module-level `OUTPUT_GCS_BUCKET` constant deleted →
      resolved lazily in `__init__`), `calendar` (`source_bucket_template` deleted → new `get_source_bucket()`→
      `features-calendar`; 4 consumers repointed). `commodity`/`sports` config.py have no bucket templates (out of
      scope). `tests/conftest.py` (new): `setdefault` `GCP_PROJECT_ID`+`DEPLOYMENT_ENV` (resolver reads
      `${DEPLOYMENT_ENV}` from env directly). 4 test-file fixes (broken-by-deletion). STEP 5.31 "No hardcoded bucket
      name templates" PASSES; basedpyright on the 8 touched source files = 0 NEW errors; ruff clean; scoped pytest = 0
      NEW failures. **DEFERRED sub-items** (split below): cross_instrument/multi_timeframe `get_output_bucket` (yaml
      gap) + the `dependency_checker.py` inline `bucket_template` strings.
- [x] **[SCRIPT] P1**. **DEFERRED (split off from #2) — ✅ DONE 2026-05-11 (slot 4 cont. 3, Q5/A5 resolved)** —
      `cross_instrument` + `multi_timeframe`: (a) added the short alias kinds `features-xinstrument` (for
      `features-cross-instrument`) + `features-mtf` (for `features-multi-timeframe`) to
      `deployment-service/configs/cloud-providers.yaml` — 5 per-AG entries each (CEFI/TRADFI/DEFI/PREDICTION/SPORTS),
      env-tiered with `${DEPLOYMENT_ENV_SHORT}`, both clouds (per Q5/A5 Option 1 / Scope A: the long names overflow the
      63-char GCS/S3 cap under the env-tiered template; aliases live ONLY in bucket templates, workspace vocab
      unchanged); (b) UTL `bucket_naming._KIND_ALIASES` bridges the consumer-facing long kinds → the short yaml keys
      (consumers' call sites unchanged); (c) `${DEPLOYMENT_ENV}` → `${DEPLOYMENT_ENV_SHORT}` (3-char form
      `dev`/`stg`/`prd`) across every env-tiered yaml entry + `-prediction-` → `-pred-` in every prediction-related
      bucket-name STRING (keys unchanged), plus matching `${DEPLOYMENT_ENV_SHORT}` support in BOTH yaml-readers
      (`deployment_service.config.env_substitutor` + UTL `bucket_naming`); (d) `cross_instrument/config.py` +
      `multi_timeframe/config.py` `get_output_bucket()` now
      `return resolve_bucket(kind="features-cross-instrument"/     "features-multi-timeframe", asset_group=...)` — the
      `output_bucket_template` Field + the `OUTPUT_BUCKET_TEMPLATE` env-override alias deleted; (e) parity test
      `test_bucket_naming.py` updated (snapshot `${DEPLOYMENT_ENV_SHORT}` + `-pred-`; `_FEATURES_PIPELINE_KINDS`
      live-yaml pin gains `features-xinstrument`/`features-mtf` + the consumer aliases + the `*-pred-` prefixes; all
      `-staging-` expectations → `-stg-`). All env-tiered names verified ≤63 chars (worst:
      `unified-trading-features-xinstrument-tradfi-stg-{12-digit}` = 60). status: done — evidence: UTL@`4ee24b5`
      (resolver `_KIND_ALIASES` + `${DEPLOYMENT_ENV_SHORT}`) + deployment-service@`008e371` (`env_substitutor`
      `${DEPLOYMENT_ENV_SHORT}`) + deployment-service@`f81d043` (yaml sweep) + UTL@`e3dd846` (parity test) +
      features-service@`e980ecfd` (config.py migration). On-disk flat→env-tiered + the 2 alias-kind renames migrate in
      code_freeze Phase 2.6 (2026-05-15→05-19). **FOLLOW-UP (P2, DEFERRED)**: drop the now-stale
      `OUTPUT_BUCKET_TEMPLATE` refs from
      `features-service/features_service/cross_instrument/docs/{CONFIGURATION,DEPLOYMENT_GUIDE}.md` +
      `features-service/features_service/multi_timeframe/.env.example` (docs only, no code impact — left to a
      features-service-docs sweep so this commit doesn't double-format foreign docs).
- [ ] **[SCRIPT] P2**. **DEFERRED (follow-up to the cross_instrument/multi_timeframe migration above)** — drop the
      now-stale `OUTPUT_BUCKET_TEMPLATE` env-var refs from
      `features-service/features_service/cross_instrument/docs/CONFIGURATION.md` (`output_bucket_template` row) +
      `cross_instrument/docs/DEPLOYMENT_GUIDE.md` (`OUTPUT_BUCKET_TEMPLATE` table row) + `multi_timeframe/.env.example`
      (`# OUTPUT_BUCKET_TEMPLATE=...` line) — the Field + env-override alias were deleted @features-service`e980ecfd`;
      `get_output_bucket` now routes through
      `resolve_bucket(kind="features-cross-instrument"/     "features-multi-timeframe", ...)` (the yaml SSOT). status:
      todo — note: "2026-05-11 slot 4 — docs-only, no code impact (a reader who sets `OUTPUT_BUCKET_TEMPLATE` would just
      have it silently ignored); deferred to a features-service-docs sweep so the migration commit doesn't double-format
      foreign docs (prettier churn on `.md`)."
- [ ] **[SCRIPT] P1**. **DEFERRED (split off from #2)** — migrate the `dependency_checker.py` inline `"bucket_template"`
      strings (`features-service/features_service/{delta_one,onchain,volatility}/.../dependency_checker.py` — the
      `"bucket_template": "market-data-tick-{asset_group_lower}-{project_id}"` etc. + the
      `UPSTREAM_DEPS`/`OUTPUT_BUCKETS` `_TEST` dicts + their `test_mode` infra) onto `resolve_bucket(...)`. status:
      blocked — note: "2026-05-11 slot 4 — deferred with rationale: (a) 2 of 3 extend UTL `BaseDependencyChecker` whose
      `_check_single_dependency` does the `.format(**vars_dict)` — out of features-service scope, needs the UTL
      `BaseDependencyChecker` migration first; (b) the `test_mode` model + `OUTPUT_BUCKETS`/`OUTPUT_BUCKETS_TEST` dicts
      are introspected/asserted by ~6-10 tests (`test_dependency_config_models.py`, `test_volatility_e2e.py`,
      `test_smoke_matrix.py`, `test_defi_data_source_routing.py`, ...) — a clean migration rewrites that infra + those
      tests; (c) the `market-data` probe template was zero-drift vs the (then) env-less yaml `market-data` entry — **but
      as of Phase 0e (2026-05-11) the yaml `market-data` is env-tiered (`market-data-tick-{ag}-{env}-{pid}`), so the
      probe template `market-data-tick-{ag}-{pid}` now DRIFTS from the yaml.** The on-disk buckets stay flat until
      code_freeze Phase 2.6, so the probe is still correct for current on-disk reality — but the dependency_checker
      migration MUST land in the SAME window as the flat→env-tiered data migration (Phase 2.6), or via the UTL
      `BaseDependencyChecker` migration if that lands first, whichever is sooner;
      `dependency_checker.get_output_bucket`/ `OUTPUT_BUCKETS` is a dead-code duplicate of the (now-migrated)
      `config.get_output_bucket` — the actual write path uses config.py's. Resumes after the UTL `BaseDependencyChecker`
      migration + a `test_mode`-infra rewrite plan."
- [ ] **[SCRIPT] P1**. Delegate the legacy `unified_trading_library.cloud_interface.constants.get_bucket_name` +
      `BUCKET_PREFIXES` to `bucket_naming.resolve_bucket_name(...)` (a `{domain}` → `{kind}` translation map + per-cloud
      dispatch). The legacy `{DOMAIN}_GCS_BUCKET[_{ASSET_GROUP}]` env-override shim either (a) survives as a thin
      wrapper in `get_bucket_name`, OR (b) is dropped in favour of the `${DEPLOYMENT_ENV}` axis (decide at impl time per
      whether the per-domain override env vars are actively used). status: todo — note: "2026-05-11 slot 4 — the
      resolver docstring already names this 'a follow-up step'; folded in so it doesn't fall off-radar; no gate
      (UTL-only) but ships after the L2 config.py migration (now done @`8f03ceeb`) so consumers don't briefly see two
      delegating paths. Pre-audit done (slot 4): ~36+ consumers across instruments-service (~16 files) /
      execution-service (~13) / deployment-service (~7) / PM scripts — grep
      `get_bucket_name\|BUCKET_PREFIXES\|get_instruments_bucket\|     get_market_data_bucket\|get_execution_bucket\|get_strategy_bucket\|get_features_calendar_bucket\|get_write_bucket_name`
      — enumerate fully + basedpyright each consumer repo after the delegate lands (Citadel § 6). **⚠️ Q6 (slot 4 cont.
      3, 2026-05-11) — sequencing concern, needs Ikenna/operator before this lands**: after Phase 0e the yaml's Group-A
      entries (`market-data`, `instruments-store`, `features-calendar`) are env-tiered
      (`market-data-tick-{ag}-${DEPLOYMENT_ENV_SHORT}-{pid}` etc.); the on-disk buckets stay FLAT
      (`market-data-tick-{ag}-{pid}`) until code*freeze Phase 2.6 (2026-05-15→05-19). The 'safe gap' that makes Done-def
      #2's
      `features-*`migration OK (nothing writes`features-_`between now and Phase 3, QG is mock) does **NOT**     extend to Group-A — instruments-service backfills + MTDS captures write`market-data`/`instruments-store`buckets     continuously. So a naive`get_bucket_name('market_data',
      ...)`→`resolve_bucket_name(kind='market-data',
      ...)`     delegate landing NOW re-points those consumers to non-existent env-tiered names → first-write-failure (the exact     bug this plan exists to prevent). Options: (i) the delegate keeps Group-A domains     (`instruments`/`market_data`/`features_calendar`) returning the FLAT name until Phase 2.6, then flips with the     migration; (ii) defer the whole delegate to the Phase-2.6 window; (iii) confirm instruments-service/MTDS set the     per-domain     `{DOMAIN}\_GCS_BUCKET[_{AG}]` override     to the flat names during the transition (then the override pre-check shields them). Group-B domains     (`features*\*`/`ml*\*`/`execution`/`strategy`)
      are unaffected (the safe gap covers them). See § Open questions Q6. Slot 1: route a cross-side ping to Ikenna."
- [ ] **[SCRIPT] P1**. Workspace QG step (the inline-`f"gs://{bucket}/..."`/`f"s3://{bucket}/..."` formatter ratchet)
      AST-walks for these formatters; fails CI if any new ones land outside the resolver. **Design (slot 4
      2026-05-11)**: baseline-ratchet shape (count current `gs://`/`s3://` f-strings WITHOUT a `# noqa: gs-uri` marker
      per repo → fail if the count grows). Goes in `unified-trading-pm/scripts/quality-gates-base/base-service.sh` as a
      new STEP — **STEP 5.68** (5.65 = removed-symbol AST-walk; 5.66 reserved for the multi-process-launcher AST-walk;
      5.67 taken by slot 6's banned-placeholder gate; so 5.68 — confirm it's free in `base-service.sh` at impl time per
      slot 1's 2026-05-11 A3/follow-up). Full design in § "Pre-audit manifest" → "QG STEP 5.6X design". status: todo —
      note: "2026-05-11 slot 4 — design written; ships after the L2 config.py migration (done @`8f03ceeb`) + the
      legacy-delegate land (else the ratchet baseline bakes in to-be-removed inline templates)."
- [x] **[SCRIPT] P1**. Add yaml-vs-resolver parity unit test (already shipped at UTL@`24f9b2cb` for 10 DeFi bucket
      entries; extend coverage to features-\* + sports + tradfi). **Shipped UTL@`e8dc6e3` (slot 4 2026-05-11)**:
      `_SNAPSHOT_YAML` extended with `features-volatility` / `features-onchain` (per-asset_group) + `features-sports` /
      `features-prediction` (flat) + `market-data` (per-asset_group; GCP `tick-` infix vs AWS no-infix) +
      `instruments-store` (per-asset_group) + `market-data-tick-prediction` (flat) + `features-calendar` (AWS-only). New
      parametrized tests: per-asset_group features kinds, market-data per-cloud shape, instruments-store
      per-asset_group, sports/prediction flat kinds, features-calendar AWS-only, and a LIVE-workspace-yaml regression
      pin for every features-pipeline kind. **Side-fix**: `test_workspace_yaml_has_gcp_aws_parity_for_core_kinds` was
      RED since ~2026-05-08 (AWS-only `features-calendar` addition) — added a `_KNOWN_YAML_ASYMMETRIES` allowlist with
      documented reasons + a stale-allowlist guard; undocumented drift still fails. 83 tests pass; ruff + basedpyright
      clean.
- [ ] **[AGENT] P1**. Plan-flip cite + workspace-wide grep audit table verifying zero remaining drift sites. status:
      blocked — note: "2026-05-11 slot 4 — final step; runs after the config.py migration + the legacy-delegate + the QG
      STEP all land."

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

- **`code_freeze_migrate_backfill_sequencing_2026_05_10.md`** — this plan's Phase 0a (operator decision) + Phase 0b
  (yaml additive corrections) + #2 (L2 config.py migration) + #3 (legacy delegate) ship in **Phase 1 code-complete**
  (deadline 2026-05-15) of the sequencing umbrella. Phase 0c (env-tiered bucket provisioning) + Phase 0d (flat→tiered
  data migration) ship in **Phase 2 physical migration** (window 2026-05-15→05-19) of the same umbrella alongside
  manifest v8 atomic rename + GCS bundled migration + AWS DeFi-first parity + cross-asset rescan. Operator-coordinated
  write-pause window for Phase 0d aligns with the rest of Phase 2's freeze window so backfills don't race the migration.
- **`aws_migration_defi_first_2026_05_07.md`** — AWS-side env-tier provisioning (Phase 0c half) folds into AWS
  migration's existing scope; the bucket-naming SSOT decision (b) extends AWS migration's bucket creation step from "10
  DeFi buckets" to "all env-tiered Group-B buckets per yaml." AWS yaml has `features-calendar` entry but GCP doesn't;
  the parity regression test at UTL@`780a9575` fired on this drift. **RESOLVED 2026-05-11 (slot 4, UTL@`e8dc6e3`)**: the
  parity test now allowlists the `features-calendar` GCP-missing asymmetry (`_KNOWN_YAML_ASYMMETRIES`, with the
  documented yaml-comment reason) + a stale-allowlist guard. **NEW under (b)**: GCP `features-calendar` entry must be
  uncommented + provisioned per Phase 0b + Phase 0c, then the allowlist entry removed (Phase 0b done-def step).
- **`work_split_2026_05_11_harsh.md` § Slot 4** — slot 4's scope grows under (b): `bucket-name SSOT` was scoped at ~3
  AI-day for option (a); under (b) it's ~5-7 AI-day spanning Phase 1 (code-complete) + Phase 2 (provisioning + data
  migration). Work-split slot 4 entry updated 2026-05-11 to reflect (b) scope.
- **`work_split_2026_05_11_ikenna.md` § Slot 5** — anti-sequencing audit table entry for
  `bucket_name_ssot_canonicalisation` flips from "Phase 1.B ownership; sequenced before Phase 2.4 AWS migration writes"
  to "Phase 1 + Phase 2 split per operator decision (b); Phase 0c provisioning + Phase 0d data migration become Phase
  2.4 sub-steps."
- Workspace foot-gun #1 — surgical staging when editing feature-service config.py files (parallel-agent territory).
- `available_at_lookahead_bias_completion_2026_05_08.md` — sibling plan-of-record for slot 4 this cycle (the per-adapter
  `available_at` stamping half). No shared files; the only overlap is that the QG STEP numbering here (5.69) must not
  collide with that plan's reserved 5.67/5.68 (see § Open questions Q3).

## References

- Archived issue:
  [`plans/archive/issues/bucket_name_ssot_triple_drift_2026_05_10.md`](../archive/issues/bucket_name_ssot_triple_drift_2026_05_10.md)
- Existing UTL resolver: `unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py`
  (UTL@`780a9575` — partial mitigation, 10 DeFi buckets routed)
- Existing parity test: `unified-trading-library/tests/cloud_interface/unit/test_bucket_naming.py` (UTL@`24f9b2cb`,
  extended UTL@`e8dc6e3`)
- Yaml SSOT: `deployment-service/configs/cloud-providers.yaml`
- Legacy resolver to fold in: `unified-trading-library/unified_trading_library/cloud_interface/constants.py`
  (`BUCKET_PREFIXES` dict + `get_bucket_name(domain, asset_group, project_id)`)

## Pre-audit manifest — 4-layer drift map + per-layer migration recipe

> Authored 2026-05-11 (slot 4) during the gated-prep window. This is the executing-agent's reference so the migration
> doesn't need a re-scan. Per CLAUDE.md "Citadel-Grade Planning § 1 Pre-Audit Before Execution".

### The 4 layers (the plan body calls it "triple drift"; there are actually 4 distinct sources)

| #   | Layer                        | Location                                                                                         | `features-delta-one` GCP shape                                   | `features-onchain` GCP shape                                                                 | Has `${DEPLOYMENT_ENV}`? | Status                |
| --- | ---------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------ | --------------------- |
| L1  | **yaml (canonical)**         | `deployment-service/configs/cloud-providers.yaml` `<cloud>.storage.<kind>`                       | `features-delta-one-cefi-${DEPLOYMENT_ENV}-${GCP_PROJECT_ID}`    | per-asset_group: `features-onchain-cefi-${DEPLOYMENT_ENV}-...` / `features-onchain-defi-...` | YES                      | **canonical** — keep  |
| L2  | per-family `config.py`       | `features-service/features_service/{family}/config.py` `*_bucket_template` Field defaults        | `features-delta-one-{asset_group_lower}-{project_id}` (NO env!)  | `output_bucket_template="features-onchain-{project_id}"` (NO env, NO asset_group — "shared") | NO                       | **DELETE** → L1 calls |
| L3  | legacy UTL constants         | `unified-trading-library/.../cloud_interface/constants.py` `BUCKET_PREFIXES` + `get_bucket_name` | `features-delta-one-{cefi}-{env}-{pid}` (Group B — env-isolated) | `features-onchain-{cefi}-{env}-{pid}` (Group B — env-isolated)                               | YES                      | **DELEGATE** → L1     |
| L4  | UTL `bucket_naming` resolver | `unified-trading-library/.../cloud_interface/bucket_naming.py` (reads L1)                        | = L1                                                             | = L1                                                                                         | YES (reads L1)           | **target** — keep     |

**The bug** (the 7-of-55-deleted-buckets incident, 2026-05-10 features-bucket cleanup): L2 drops `${DEPLOYMENT_ENV}` →
`features-delta-one-cefi-myproj` instead of `features-delta-one-cefi-staging-myproj`. So a workload using the L2
template wrote to a _different_ bucket than the one `setup-buckets.sh` (which reads L1) provisioned → looked unused →
got cleaned up → first-write failed on the next run. Worse: `features-onchain` config.py has FOUR shapes within one file
— `output_bucket_template="features-onchain-{project_id}"` (shared, no env, no AG),
`io_output_bucket_template= "features-onchain-defi-{project_id}"` (per-AG=defi, no env),
`input_bucket_template="market-data-tick-{asset_group_lower}-{project_id}"`,
`io_input_bucket_template="instruments-store-defi-{project_id}"`. L1 says `features-onchain` is per-asset_group
(`CEFI`/`DEFI`) WITH env. **Whichever shape the actual on-disk bucket has must be verified at impl time**
(`gcloud storage ls` / `aws s3 ls`) — if the real bucket is `features-onchain-defi-myproj` (no env), then L1's
`features-onchain-defi-${DEPLOYMENT_ENV}-...` is the one that's wrong and the yaml needs a fix-forward, not the
config.py. **This is a triage call the migration must make per-kind** (see Q2).

### Layer 2 migration recipe (per-family `config.py`)

For each `features-service/features_service/{family}/config.py` (`calendar` / `commodity` / `cross_instrument` /
`delta_one` / `multi_timeframe` / `onchain` / `sports` / `volatility`):

1. **Inventory the templates**: `grep -n "bucket_template\|_bucket_template" config.py`. Each
   `*_bucket_template: str = Field(default="...", validation_alias=AliasChoices("...BUCKET_TEMPLATE"))` is a migration
   target.
2. **Map each template → `(kind, per_asset_group?)`** per L1's `cloud-providers.yaml` keys:
   - `input_bucket_template` (`market-data-tick-{ag}-{pid}`) → `kind="market-data"`, per-asset_group ✓
   - `output_bucket_template` for `delta_one` (`features-delta-one-{ag}-{pid}`) → `kind="features-delta-one"`, per-AG ✓
   - `output_bucket_template` for `volatility` → `kind="features-volatility"`, per-AG ✓
   - `output_bucket_template` for `onchain` (`features-onchain-{pid}`) → `kind="features-onchain"`, per-AG ✓ (**but**
     the config.py treats it as shared/no-AG — verify the real bucket; if it really is shared, the yaml needs a flat
     `features-onchain` entry too, or the config.py keeps a no-AG `get_output_bucket()` that resolves
     `kind="features-onchain", asset_group="defi"` since onchain = defi-only data)
   - `output_bucket_template` for `sports` / `prediction` → `kind="features-sports"` / `"features-prediction"`, flat
   - `instruments_store_bucket_template` (`instruments-store-{ag}-{pid}`) → `kind="instruments-store"`, per-AG ✓
   - `io_input_bucket_template` (`instruments-store-defi-{pid}`) → `kind="instruments-store"`, asset_group="defi"
   - `io_output_bucket_template` (`features-onchain-defi-{pid}`) → `kind="features-onchain"`, asset_group="defi"
   - `source_bucket_template` for `calendar` (`features-calendar-service`?? — verify; the real yaml has NO GCP
     features-calendar entry — see § "Composes with" + Q2) → `kind="features-calendar"`, flat (AWS-only today)
3. **Delete the `Field(default="...")` template** + repoint the `get_*_bucket(asset_group)` method body:
   ```python
   # BEFORE
   output_bucket_template: str = Field(default="features-delta-one-{asset_group_lower}-{project_id}", ...)
   def get_output_bucket(self, asset_group: str) -> str:
       return self.output_bucket_template.format(asset_group_lower=asset_group.lower(), project_id=self.gcp_project_id)
   # AFTER  (import at module top: from unified_trading_library.cloud_interface import resolve_bucket_name
   #          and from unified_trading_library.cloud_interface.constants import get_cloud_provider)
   def get_output_bucket(self, asset_group: str) -> str:
       return resolve_bucket_name(cloud=get_cloud_provider().value, kind="features-delta-one", asset_group=asset_group.lower())
   ```
   — `cloud=` comes from `get_cloud_provider().value` (returns `"gcp"`/`"aws"`); `kind=` is the literal from step 2;
   `asset_group=` is lowercase (resolver requires lowercase per CLAUDE.md vocabulary exception). The `${DEPLOYMENT_ENV}`
   / `${GCP_PROJECT_ID}` substitution happens _inside_ `resolve_bucket_name` against the live env — so the config.py no
   longer needs `self.gcp_project_id` for bucket-name purposes.
4. **Decide the per-family `*_BUCKET_TEMPLATE` env-override fate**: the
   `validation_alias=AliasChoices("OUTPUT_BUCKET_TEMPLATE")` let operators redirect via env var. After migration the
   redirect path is `DEPLOYMENT_ENV=test` → `-test-` buckets (the yaml template carries `${DEPLOYMENT_ENV}`). If a
   family genuinely needs a per-family override (e.g. the calendar `route_to_test_bucket` flag), keep a thin wrapper;
   otherwise drop the env vars (one less drift surface).
5. **Update `dependency_checker.py`** — `features-service/features_service/{family}/app/core/dependency_checker.py` (and
   `volatility/core/dependency_checker.py`, `onchain/app/core/dependency_checker.py`) have inline
   `"bucket_template": "market-data-tick-{asset_group_lower}-{project_id}"` strings used for pre-flight checks. Migrate
   those to `resolve_bucket_name(...)` too — same `(kind, asset_group)` mapping.
6. **Smoke**: `cd features-service && bash scripts/quality-gates.sh` (basedpyright catches the import + signature
   changes); plus a `python -c "from features_service.delta_one.config import ...; cfg.get_output_bucket('cefi')"`
   sanity check that returns the env-tiered name.

### Layer 3 migration recipe (legacy `get_bucket_name`)

`unified_trading_library.cloud_interface.constants.get_bucket_name(domain, asset_group=None, project_id=None)` →
delegate to `resolve_bucket_name`. Need a `{domain}` → `{kind}` translation map:
`{"instruments": "instruments-store", "market_data": "market-data", "features_calendar": "features-calendar", "features_delta_one": "features-delta-one", "features_onchain": "features-onchain", "features_volatility": "features-volatility", "execution": "execution-store", "strategy": "strategy-store", "ml_models": "ml-models-store", "ml_predictions": "ml-predictions-store", "ml_configs": "ml-configs-store"}`.
The `cloud=` comes from `get_cloud_provider().value`. The `{DOMAIN}_GCS_BUCKET[_{ASSET_GROUP}]` env-override shim:
either survives as a thin pre-check at the top of `get_bucket_name` (preserves test/dev redirect for repos that use it),
OR is dropped. Pre-audit: `grep -rn "_GCS_BUCKET" --include='*.py' . --exclude-dir='.venv*'` to see how many repos rely
on it before deciding. Then
`grep -rn "get_bucket_name\|get_instruments_bucket\|get_market_data_bucket\|get_execution_bucket\|get_strategy_bucket\|get_features_calendar_bucket\|BUCKET_PREFIXES"`
for the full consumer set; basedpyright on each consumer repo after.

### QG STEP 5.6X design (the `f"gs://..."` ratchet)

- **STEP number**: `5.69` (5.66/5.67/5.68 are reserved — see Q3). Lands in
  `unified-trading-pm/scripts/quality-gates-base/base-service.sh` near STEP 5.65 (the removed-symbol AST-walk), same
  shape: a Python checker invoked per-repo + a workspace-wide cron sweep.
- **What it catches**: NEW `f"gs://..."` / `f"s3://..."` formatters that build a cloud URI by hand instead of going
  through `resolve_bucket_uri()`. The `# noqa: gs-uri` inline marker (already used ~10× in execution-service, plus
  `volatility/core/data_loader.py`, `onchain/app/core/feature_writer.py`, etc. — documented in
  `execution-service/BYPASS_AUDIT.md` + `strategy-service/pyproject.toml`'s external-codes list) is the "grandfathered,
  intentional" exemption. The check skips lines with that marker.
- **Shape**: baseline-ratchet (NOT zero-tolerance from day 1 — there are dozens of legitimate
  `gs://{already_resolved_bucket}/{path}` sites that won't all migrate at once). Count current `gs://`/`s3://` f-strings
  WITHOUT `# noqa: gs-uri` per repo, store the baseline in a small yaml
  (`unified-trading-pm/scripts/quality_gates/gs_uri_baseline.yaml`), fail CI if a repo's count _grows_. Same shape as
  the existing baseline ratchets (e.g. `# type: ignore` ratchet).
- **Implementation note**: a literal `grep`-on-`f"gs://` is enough for v1 (the formatter is always a single-line
  f-string in practice); an AST-walk that distinguishes `f"gs://{x}/..."` from a `resolve_bucket_uri(...)` call is the
  v2 hardening (matches the QG STEP 5.65 AST-walk pattern). v1 ships first.
- **Sequencing**: ships _after_ the L2 + L3 migrations land, so the ratchet baseline doesn't bake in the to-be-removed
  inline templates.

## Open questions

### Q1 — [harsh-bucket-and-adapter-tab, 2026-05-11 07:04 UTC] — resolver location: `unified_api_contracts.bucket_naming` vs `unified_trading_library.cloud_interface.bucket_naming`

**Status**: 🟡 BLOCKED — low-priority clarification (doesn't block the prep work; would block the migration's import
statements)

This plan-of-record (`bucket_name_ssot_canonicalisation_2026_05_10.md` lines 41, 53, 89) consistently names the resolver
`unified_trading_library.cloud_interface.bucket_naming` — and that's where it actually exists today (shipped
UTL@`780a9575`, extended UTL@`e8dc6e3`). But the work-split `work_split_2026_05_11_harsh.md` § "Slot 4" done-definition
(line ~228) and the LEDGER "Repos owned" line both say **`unified_api_contracts.bucket_naming`** — i.e. they imply the
resolver should live in (or be moved to) UAC. The full-execution criterion in the work-split is:
`python -c "from unified_api_contracts.bucket_naming import resolve_bucket_name; print(resolve_bucket_name('cefi', 'tradfi'))"`
— which is a different module path AND a different signature (positional `('cefi', 'tradfi')` vs the current
`resolve_bucket_name(*, cloud=, kind=, asset_group=)`).

**My read**: the plan-of-record is the authoritative SSOT for the design; the work-split is the daily orchestration
surface (its `python -c` line looks like a sloppy paste, not a deliberate "move it to UAC" decision). The resolver
already exists in UTL and is yaml-backed; moving it to UAC would be a strictly bigger refactor (every consumer's import
churns) that this plan doesn't otherwise call for. **Recommendation**: keep the resolver in UTL
(`unified_trading_library.cloud_interface.bucket_naming`); the migration's config.py imports target that path. If slot 1
/ operator instead wants the resolver in UAC (e.g. because "bucket-naming SSOT" is conceptually a contract — and
CLAUDE.md does list "bucket-naming SSOT decisions" as Ikenna's human-approval surface), say so and I'll add a "Phase 0 —
move resolver UTL→UAC" step + re-audit the consumer set. Until then I'm proceeding on the UTL assumption for all prep.

### Q2 — [harsh-bucket-and-adapter-tab, 2026-05-11 07:04 UTC] — proceed with the `features-service/{family}/config.py` migration now (against consolidated state), or wait for slot 2 Phase 4?

**Status**: 🟡 BLOCKED — coordination decision

The work-split gates the L2 migration on "AFTER Harsh slot 2 features-consolidation Phase 4 import-rewrite stabilises
(or runs against the consolidated state)". The features-service IS already in the consolidated layout
(`features_service/{calendar,commodity,delta_one,onchain,...}/config.py` all exist; the skeleton landed @`d3d6e286`).
The recent slot-2 commits (last ~8: UTL ModeHandler adoption, ruff sweeps, BaseFeatureCalculator adoption) are _not_
import-rewrites of `features_*_service.*` → `features_service.*`, and the `config.py` files were last touched by the
original subtree-import commits (`644a519d` / `b0e63608`), not recently. So the collision risk of editing `config.py`
now is low — but slot 2 IS actively in flight on features-service. **Question**: (a) green-light me to do the L2
migration now (I'll `git add -p` only the specific `config.py` + `dependency_checker.py` files, rebase before every
push, and ping slot 2 to coordinate); or (b) hold until slot 2 posts a "Phase 4 done" ping. **Recommendation**: (a) —
the bucket-SSOT migration is a P1 pre-cutover item, the collision surface is small + well-bounded, and the config.py
Field-default edits are orthogonal to whatever import-rewriting slot 2 has left. But it's slot 1's call. Meanwhile I'm
doing the parity test (done, UTL@`e8dc6e3`), the audit (this section), and the sports-adapter audit half.

### Q3 — [harsh-bucket-and-adapter-tab, 2026-05-11 07:04 UTC] — QG STEP number allocation for the `f"gs://..."` ratchet

**Status**: 🟡 BLOCKED — trivial; just need the number

`base-service.sh` currently goes up to STEP `5.65` (removed-symbol AST-walk). CLAUDE.md + plans reserve `5.66`
(multi-process-launcher AST-walk per the "Per-VM shard isolation" rule) + `5.67` (`record_captured` must be preceded by
stamping, per `available_at_lookahead_bias_completion_2026_05_08.md` Phase 8) + `5.68` (feature-compute callsites must
call `assert_no_lookahead_for_feature_group`, same plan). None of 5.66/5.67/5.68 are implemented yet. **Plan**: I'll use
`5.69` for the `f"gs://..."` ratchet unless slot 1 reassigns. (Flagging only so two parallel plans don't both grab the
same number — `available_at_lookahead_bias_completion_2026_05_08.md` is the _other_ slot-4 plan-of-record this cycle so
I can keep them coordinated, but if a third plan also touches base-service.sh numbering, slot 1 should arbitrate.)

### Q4 — [harsh-bucket-and-adapter-tab, 2026-05-11 07:13 UTC] — 🔴 P0: cloud-providers.yaml features-\* env-tier is aspirational, not provisioned — drop the tier from the yaml, or provision the env-tiered buckets?

> **🟡 SUPERSEDED 2026-05-11 by (b+) extension** — operator extended (b) → (b+) the same day after reviewing the initial
> (b) decision shape (PM@7be8593a). (b+) extends env-tier to ALL buckets (Group-A: raw-tick, instruments-store,
> market-data — not just Group-B features-\*/ml-\*/strategy/execution), adds sync script (prod → staging/dev with
> truncated date window + same-region), adds region pinning, adds VM launcher env-aware audit. See **#### ✅ Q4 RESOLVED
> — [ikenna-operator, 2026-05-11] — option (b): make reality match the yaml** below for the full (b+) scope
>
> - Phase 0a-0i breakdown + AI-day budget. The Harsh-shipped (b) version below stays for attribution + git history; the
>   (b+) version is the authoritative.

**Status**: ✅ RESOLVED (initial (b) per Harsh slot 1 PM@7be8593a; superseded by (b+) extension below per operator
direction 2026-05-11) — operator/Ikenna picked **option (b)** 2026-05-11 ("make reality match the yaml" — provision the
env-tiered buckets + migrate the existing flat-bucket data + repoint every reader/writer; high-risk multi-bucket data
migration). **Implications**: (1) the yaml STAYS env-tiered — that's the SSOT now (no change to the `${DEPLOYMENT_ENV}`
shape; do ADD the missing `prediction`/`sports` keys with the same env-tier shape, uncomment GCP `features-calendar`,
pick + model one canonical `-test-` variant shape, and PROBE `ml-*`/`strategy`/`execution` for flat-vs-env-tiered on
disk — if any are flat they need provisioning too). (2) The **L2 config.py → `resolve_bucket_name` migration is
UNBLOCKED** — do it now: the env-tiered names the resolver computes are now "correct" per (b); the buckets don't exist
YET but the physical provisioning + data migration happens in `code_freeze` Phase 2 (item 2.6, window 2026-05-15→05-19),
and nothing writes `features-*` buckets between now and `code_freeze` Phase 3 backfills (QG runs in mock mode, so the
gap is safe). This is the "code first, physical migration second" sequence per the `code_freeze` principle. (3) The
env-tiered-bucket **provisioning + flat-bucket data migration + reader/writer repoint** is now a `code_freeze` **Phase
2.6** physical-migration item — NOT this plan's / slot 4's job to execute now. (4) Phase 0 of this plan is re-shaped:
it's now just the yaml-correctness fixes (missing keys / uncomment `features-calendar` / `-test-` shape / `ml-*` probe),
not "drop the tier vs provision the tier". **NOTE per (b+) extension**: implication (3) updated — `code_freeze` Phase
2.6 became GAP-2.4.B (provision) + GAP-2.4.C (migrate data) + GAP-2.4.D (audit table) + GAP-2.4.E (sync script) +
GAP-2.4.F (region) + GAP-2.4.G (yaml all-buckets extension) + GAP-2.4.H (VM launcher env-aware) + GAP-2.4.I (UI verify
✅ done). Implication (4) extended: Phase 0e (yaml all-buckets env tier)

- Phase 0f (VM scripts) + Phase 0g (UI verify ✅) + Phase 0h (sync script) + Phase 0i (region pinning) added to this
  plan. AI-day budget grows ~3 → ~10-13 under (b+).

GCP probe (2026-05-11, project `central-element-323112`): the `features-*` buckets that ACTUALLY EXIST are FLAT — no
`${DEPLOYMENT_ENV}` tier — but the yaml entries
(`features-delta-one.CEFI = features-delta-one-cefi-${DEPLOYMENT_ENV}-${GCP_PROJECT_ID}`, etc.) carry the tier (the
yaml's "Group B — derived data, per-env" convention). So
`resolve_bucket_name(kind="features-delta-one", asset_group="cefi")` with `DEPLOYMENT_ENV=prod` →
`features-delta-one-cefi-prod-central-element-323112` → **doesn't exist**. The L2 config.py templates
(`features-delta-one-{ag}-{pid}`, no env) are the ones that match the provisioned buckets. Full evidence table in §
"FINDING 2026-05-11" above. Also surfaced: yaml is missing `prediction`/`sports` keys for several kinds (the buckets
exist on disk); GCP `features-calendar` bucket exists but the yaml entry is commented out; the `-test-` E2E variant
naming is inconsistent on disk (`instruments-store-cefi-test-{pid}` vs `market-data-tick-test-cefi-{pid}`).

**Options**: (a) **Make the yaml match reality** — drop `${DEPLOYMENT_ENV}` from the GCP `features-*` (+ `ml-*` if same
issue — not yet probed) entries; add the missing `prediction`/`sports` keys; uncomment GCP `features-calendar`; pick a
canonical `-test-` variant shape + model it. Low-risk (no bucket renames / data migration). Loses the prod/staging/dev
isolation for features-* buckets (but it was never actually provisioned, so nothing changes operationally). (b) **Make
reality match the yaml** — provision the env-tiered buckets (`features-delta-one-cefi-prod-{pid}`, etc.) + migrate the
existing flat-bucket data into them + repoint every reader/writer. High-risk (data migration across N buckets). (c)
**Hybrid** — keep the env tier for *future* env-isolated buckets (ml-models, strategy, execution if those ARE env-tiered
on disk — not yet probed) but drop it for features-* where it's clearly aspirational-only.

**Recommendation**: (a) — match the yaml to reality. The "live = batch, prod/staging/dev isolation" intent is laudable
but the features-_ buckets were never provisioned with the tier, so encoding it in the SSOT is a lie that bites the
moment anything resolves via `resolve_bucket_name`. If env-isolation for features-_ buckets is genuinely wanted later,
that's a separate "provision + migrate" plan, not a blocker for this one. But this is a "bucket-naming SSOT decision"
per the work-split split-principle = operator/Ikenna call. **Until answered**: the L2 config.py migration (done-def
todo) + Phase 0 stay blocked; I've done all the no-gate prep (parity test, pre-audit manifest, this finding,
sports-adapter audit).

#### Answers from main (slot 1) — [2026-05-11 07:34 UTC]

**A1 (resolver location) — RESOLVED: keep the resolver in UTL**
(`unified_trading_library.cloud_interface.bucket_naming`). The plan-of-record is the authoritative design SSOT; the
work-split's `python -c "from unified_api_contracts.bucket_naming import ..."` line was a sloppy paste, not a deliberate
"move to UAC" decision. Slot 1 corrected the work-split § "Slot 4" done-definition + the LEDGER "Repos owned" line to
say `unified_trading_library.cloud_interface.bucket_naming`. (CLAUDE.md lists "bucket-naming SSOT _decisions_" as
Ikenna's human-approval surface — that's about the SSOT _content_ (the yaml), not the resolver's code location. If the
operator later wants the resolver promoted to UAC, that's a separate "move resolver UTL→UAC + re-audit consumers" step,
not a blocker for this plan.)

**A2 (proceed with config.py migration now vs wait for slot 2 Phase 4) — RESOLVED: the slot-2-Phase-4 gate is CLEAR**
(slot 2 shipped Phase 4 import rewrite 4.1-4.5 this cycle; the per-family config.py paths are stable; slot 2 is now on
`features_service_qg_cleanup_2026_05_11.md`, which doesn't churn those paths). **BUT the migration is now blocked on
Q4** — the yaml-vs-provisioned-reality env-tier mismatch MUST be settled before the config.py → `resolve_bucket_name`
migration lands, or it re-creates the first-write-failure bug this plan exists to prevent. So: **proceed with the L2
migration as soon as Q4 is answered**, not before.

**A3 (QG STEP number) — RESOLVED: STEP 5.69 for the inline-`f"gs://{bucket}/..."`-formatter check** (confirm it's free
in `base-service.sh` / the codex QG template when you implement). Note: Harsh slot 6 is adding a separate QG STEP for
the Track-D P0-2 banned-NaN-placeholder / bypass-`record_captured` patterns — that takes the _next_ free number (5.70+);
first to land claims, second adjusts; coordinate via the template.

**A4 (P0 — yaml features-\* env-tier mismatch) — surfaced to the operator 2026-05-11** + added to the cross-side ping to
Ikenna (bucket-naming SSOT is on Ikenna's human-approval surface per CLAUDE.md). Slot 1 endorsed slot 4's recommendation
**(a) make the yaml match reality**. **Operator (Ikenna) overrode to (b) — make reality match the yaml** 2026-05-11. See
✅ A4 RESOLVED below.

#### ✅ Q4 RESOLVED — [ikenna-operator, 2026-05-11] — option (b): make reality match the yaml

**Status**: ✅ RESOLVED. Operator (Ikenna) decision: **option (b) — provision env-tiered buckets + migrate flat-bucket
data + repoint readers/writers via `resolve_bucket_name()`**. Yaml stays as-is (with Phase 0b additive corrections).
High-risk multi-bucket data migration accepted as the cost of the right architectural target.

**Rationale (operator)**: prod/staging/dev/test isolation for features-\* and ml-\* and strategy-\* and execution-\*
buckets is a Citadel-grade requirement for the May-23 live cutover. The yaml's Group-B env-tier convention is the
correct architectural target; it being aspirational-not-provisioned today is a provisioning gap, not a yaml flaw. The
right fix is to close the gap by provisioning + migrating data, not by encoding the gap in the SSOT.

**Re-scoping under (b)**:

- **Phase 0a** (✅ done — this answer): operator decision recorded.
- **Phase 0b** (Phase 1 code-complete scope, deadline 2026-05-15): yaml additive corrections (missing keys + GCP
  features-calendar + canonical -test- variant). NO removals from the yaml. ~0.5 AI-day.
- **Phase 0c** (Phase 2 physical migration scope, window 2026-05-15→05-19): provision ~180-300 new env-tiered buckets on
  GCP + AWS via Terraform / `setup-buckets.sh` extensions. Harsh slot 4 owns. ~1-2 AI-day.
- **Phase 0d** (Phase 2 physical migration scope): migrate ALL flat-bucket data into the new env-tiered buckets via
  `gcloud storage cp -r` / `aws s3 sync`; pause writes during cutover; verify drift ≤0.01%; archive flat buckets after
  manifest + downstream verification. Operator-coordinated for the write-pause window. ~2-3 AI-day depending on data
  volume + parallel transfer.
- **Done-def #2 (L2 config.py migration)**: now happens AFTER Phase 0c provisioning (else first-write fails). Same
  resolver-call shape as before — just resolves to env-tiered names that now exist.
- **Done-def #3 (legacy `get_bucket_name` delegate)**: unchanged.
- **Done-def #5 (QG STEP 5.69 ratchet)**: ships AFTER #2 + Phase 0d (else baseline bakes in pre-migration sites).
- **Done-def #6 (audit table)**: extended to verify Phase 0d data-migration drift ≤0.01% per bucket + zero readers still
  hit flat bucket names.

**Cross-side ping to Harsh main**: lands in `plans/active/_agent_pings.md` confirming option (b) so Harsh slot 4 can
re-scope from "yaml fix-forward" to "provision + migrate." See that file for the timestamped ping.

**Sequencing under code_freeze_migrate_backfill_sequencing_2026_05_10.md**:

- Phase 1 freeze gate (2026-05-15): items #1, #2 (L2 config.py migration repointed to resolver — but resolver still
  returns names that don't exist on disk until Phase 0c provisions them; this is OK because the L2 migration is a CODE
  change, not a runtime exercise; first-write on consolidated-service launches doesn't happen until Phase 3 backfills
  resume), Phase 0a + 0b shipped.
- Phase 2 physical migration window (2026-05-15→05-19): Phase 0c provisioning + Phase 0d data migration. Operator
  coordinates the write-pause window with the master plan's other Phase 2 items (manifest v8 atomic rename + GCS bundled
  migration + AWS DeFi-first parity + cross-asset rescan).
- Phase 3 resume backfills (2026-05-19→05-23): all writes hit env-tiered buckets natively; flat buckets archived;
  done-def #5 QG ratchet enforces no new flat-bucket f-strings.

(Per CLAUDE.md "Plans Run To Actual Completion": "operator-actionable" deferral is NOT allowed for the data migration —
operator authorized agent has ADC admin perms on both clouds, can run the migration end-to-end. Operator coordination is
needed only for the write-pause window timing.)

### Q5 — [harsh-bucket-and-adapter-tab, 2026-05-11 (cont.)] — `features-cross-instrument` / `features-multi-timeframe` bucket names overflow the 63-char limit under the (b+) env-tier template

**Status**: 🟡 BLOCKED — waiting for an operator/Ikenna design decision (work-split: bucket-naming SSOT decisions →
Ikenna). Blocks the `cross_instrument` / `multi_timeframe` yaml-gap sub-todo (= the last loose end of Done-def #2).

The (b+) env-tier convention is `{prefix}-{ag}-${DEPLOYMENT_ENV}-${PROJECT_ID}` (GCP) /
`unified-trading-{kind}-{ag}-${DEPLOYMENT_ENV}-${AWS_ACCOUNT_ID}` (AWS). Both GCS and S3 cap bucket names at **63
chars**. The two outstanding kinds have long names:

- `features-cross-instrument` (25 chars). AWS:
  `unified-trading-features-cross-instrument-prediction-staging-{12-digit-account}` ≈ **73 chars** (over by 10); even
  the shortest combo `...-cefi-prod-...` ≈ 64 (over by 1). GCP:
  `features-cross-instrument-prediction-staging-central-element-323112` ≈ **67** (over); `...-cefi-prod-...` ≈ 58
  (fits).
- `features-multi-timeframe` (24 chars). Same problem (one char shorter — still overflows for
  `prediction`+`staging`/`development`).

Note the EXISTING on-disk buckets are env-LESS (`features-cross-instrument-{ag}-{pid}` per the config.py template — ≈ 59
chars, fits). So adding the env tier is what overflows.

**Options** (pick one — all viable, different tradeoffs):

1. **Shorter bucket name aliased to the kind in the yaml** — e.g.
   `gcp.storage.features-cross-instrument: "features-xinstr-${ag}-${DEPLOYMENT_ENV}-${GCP_PROJECT_ID}"`; consumers still
   call `resolve_bucket(kind="features-cross-instrument")` (the resolver hides the kind→bucket-name map — that's
   literally its job). `features-xinstr-prediction-staging-central-element-323112` ≈ 56 (fits); AWS
   `unified-trading-features-xinstr-prediction-staging-{account}` ≈ 62 (fits, barely). **Cost**: the existing
   `features-cross-instrument-{ag}-{pid}` buckets on disk need a rename + env-tier migration in Phase 2.6 (a bigger
   migration than a pure env-tier add).
2. **Drop the `unified-trading-` prefix for these 2 on AWS** —
   `features-cross-instrument-{ag}-${DEPLOYMENT_ENV}-${AWS_ACCOUNT_ID}` ≈ 53 (fits). **Cost**: breaks the AWS naming
   convention (`unified-trading-` prefix on all AWS buckets).
3. **Keep these 2 env-LESS** like `terraform-state`/`secrets` — `features-cross-instrument-{ag}-{pid}` ≈ 59 (fits), no
   migration. **Cost**: violates the (b+) "env tier on ALL kinds" decision (would need an explicit operator carve-out in
   the §-header comment + the QG ratchet's allowlist).
4. **GCP env-tiered + AWS env-less** — asymmetric; the parity test would need a `_KNOWN_YAML_ASYMMETRIES` entry.

Slot 4's lean recommendation: option 1 (aliased shorter name) — keeps the env axis, hides the rename behind the
resolver, and the on-disk migration is a Phase-2.6 line item anyway. But this is Ikenna's call.

#### A5 — [ikenna-main → slot 4, 2026-05-11] — operator decision: **Option 1 (aliased shorter kind names) — Scope A (bucket-template-only rename)** ✅ RESOLVED

**Operator decision 2026-05-11** (via slot 1 main): Option 1 from the enumerated options — shorter alias for the 2
overflowing kinds in the yaml, resolver hides the rename from consumers. Scope A: rename lives **only in bucket
templates**; workspace vocab stays unchanged (no CLAUDE.md "asset-group vocabulary" rule change, no workspace-wide
`prediction → pred` migration).

**Concrete aliases** (per slot 1 audit + operator approval):

| Original name (consumer-facing kind, unchanged) | Bucket-template alias (yaml on-disk) | Length   | AWS-worst-case (tradfi/sports + stg) |
| ----------------------------------------------- | ------------------------------------ | -------- | ------------------------------------ |
| `features-cross-instrument`                     | `features-xinstrument`               | 20 chars | **61 chars** ✓ (2 char headroom)     |
| `features-multi-timeframe`                      | `features-mtf`                       | 12 chars | **53 chars** ✓ (10 char headroom)    |

**Companion bucket-template-only short forms** (per Scope A — slot 1 audit confirmed all buckets fit ≤63 chars
workspace-wide with this set):

- `${DEPLOYMENT_ENV}` substitution in bucket templates uses **3-char form** (`dev` / `stg` / `prd`) — workspace vocab
  can keep `development` / `staging` / `prod` in env vars + plans + code. Add `${DEPLOYMENT_ENV_SHORT}` env var (or have
  the resolver translate `staging → stg` / `prod → prd` / `development → dev` internally) so yaml templates use the
  short form without forcing the workspace-wide rename.
- Dedicated `*-prediction` yaml keys + per-AG dict's `PREDICTION:` entries use **`pred`** in the bucket-name string —
  but `asset_group="prediction"` stays canonical per CLAUDE.md asset-group rule. Resolver translates
  `asset_group="prediction"` → `pred` in the bucket template substitution.

**Why Scope A (not Scope B / workspace-wide rename)**:

- Solves the actual problem (63-char overflow) with minimum blast radius (~5-10 file changes: yaml + resolver + 2-3
  env-var setters).
- Workspace vocab readability preserved (`prediction` / `staging` / `prod` / `development` everywhere except IN bucket
  names).
- CLAUDE.md "asset-group vocabulary" rule unchanged — `prediction` stays the canonical lowercase identifier; `pred` is
  bucket-template-only.
- Resolver bridges the two — consumers still call
  `resolve_bucket(kind="features-cross-instrument", asset_group="prediction", env="staging")` but the on-disk bucket
  comes out as `unified-trading-features-xinstrument-pred-stg-{account}`.

**Slot 4 implementation scope** (Phase 0e remaining items / yaml-gap sub-todo unblocked):

1. **Yaml updates** (`deployment-service/configs/cloud-providers.yaml`):
   - Rename `features-cross-instrument` yaml key → `features-xinstrument`; add 5 per-AG entries
     (CEFI/TRADFI/DEFI/PREDICTION/SPORTS) following the existing `features-delta-one` shape (env-tiered + per-AG).
   - Rename `features-multi-timeframe` yaml key → `features-mtf`; same 5-AG shape.
   - Switch `${DEPLOYMENT_ENV}` → `${DEPLOYMENT_ENV_SHORT}` in bucket templates (or implement the resolver translation,
     whichever is simpler — your call).
   - For per-AG `PREDICTION` entries + dedicated `*-prediction` flat keys: change the bucket-name string portion from
     `-prediction-` → `-pred-`.
2. **Resolver updates** (`unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py`):
   - Translate consumer-facing `kind="features-cross-instrument"` → yaml key `features-xinstrument` (alias map).
   - Translate consumer-facing `kind="features-multi-timeframe"` → yaml key `features-mtf`.
   - Translate `asset_group="prediction"` → bucket-template string `pred` (when substituting into the bucket name
     string, NOT when looking up the per-AG dict key — dict key stays `PREDICTION` per yaml convention).
   - Translate `env=staging/prod/development` → `stg/prd/dev` when substituting `${DEPLOYMENT_ENV_SHORT}` (or set the
     env var accordingly upstream).
3. **Parity test update** (`unified-trading-library/tests/unit/test_cloud_providers_yaml_parity.py`): refresh snapshot
   to match the new short-form bucket-template values; add new per-AG entries for `features-xinstrument` +
   `features-mtf` (resolves the yaml-gap sub-todo Done-def #2 item (a)).
4. **Phase 2.6 migration (2026-05-15→05-19)**: existing on-disk `features-cross-instrument-{ag}-{pid}` (env-less, ~59
   char names) get renamed + env-tier added during the bundled GCS/S3 migration window. Same migration script that's
   already planned for the (b+) flat→env-tiered transition handles these 2 kinds as additional renames.

**Audit confirmation** (slot 1 audit 2026-05-11): with this aliasing + companion short forms, every bucket name
workspace-wide fits ≤63 chars. Worst-case combos verified: `features-xinstrument-tradfi-stg` = 61 chars (AWS);
`features-mtf-tradfi-stg` = 53 chars; all other env-tiered kinds ≤60 chars; all Group-A non-env-tiered kinds ≤47 chars.
No other overflow risks lurking.

**Cross-side ping to slot 4 filed in `plans/active/_agent_pings.md`** (same commit as this answer).

**Status**: ✅ RESOLVED — slot 4 unblocked on the cross_instrument/multi_timeframe yaml-gap sub-todo (= Done-def #2 item
(a)) + the broader Phase 0e env-tier roll-out. Phase 2.6 migration scope grows by 2 additional kind renames (low
marginal cost since the migration script is already planned).

**SHIPPED 2026-05-11 (slot 4 cont. 3)** — implemented per A5 with `${DEPLOYMENT_ENV_SHORT}` as an explicit yaml var
(both `deployment_service.config.env_substitutor` + UTL `bucket_naming` compute the 3-char form from `DEPLOYMENT_ENV`):
UTL@`4ee24b5` (resolver `_KIND_ALIASES` + `${DEPLOYMENT_ENV_SHORT}` substitution) + deployment-service@`008e371`
(`env_substitutor` `${DEPLOYMENT_ENV_SHORT}`) + deployment-service@`f81d043` (yaml sweep — `${DEPLOYMENT_ENV}`→
`${DEPLOYMENT_ENV_SHORT}` everywhere, `-prediction-`→`-pred-` in bucket-name strings, added `features-xinstrument`/
`features-mtf` 5-per-AG both clouds, §-header rewrite) + UTL@`e3dd846` (parity test) + features-service@`e980ecfd`
(cross_instrument/multi_timeframe `get_output_bucket` → `resolve_bucket`). One deviation from A5 item 2's literal text:
the `asset_group="prediction"` → `pred` translation is done by writing the yaml templates with `pred` directly (not a
resolver-side translation) — simpler + correct (the dict KEY stays `PREDICTION`; only the bucket-name STRING uses
`pred`).

### Q6 — [harsh-bucket-and-adapter-tab, 2026-05-11 (cont. 3)] — Done-def #3 delegate would re-point Group-A bucket consumers to non-existent env-tiered names if it lands before Phase 2.6

**Status**: 🟡 BLOCKED — needs an Ikenna/operator sequencing decision before the Done-def #3 legacy `get_bucket_name`
delegate lands.

After Phase 0e the yaml's Group-A entries (`market-data` →
`market-data-tick-{ag}-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}`, `instruments-store` →
`instruments-store-{ag}-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}`, `features-calendar`) are env-tiered, but the on-disk
buckets stay FLAT (`market-data-tick-{ag}-{pid}` etc.) until code*freeze Phase 2.6 (2026-05-15→05-19, which provisions
the env-tiered buckets + migrates the data). The "safe gap" that makes Done-def #2's
`features-*`migration OK — \_nothing writes`features-_`buckets between now and code_freeze Phase 3 backfills, and QG
runs in mock mode (emulator auto-creates buckets)_ — does **NOT** extend to Group-A: instruments-service backfills +
MTDS captures write`market-data`/`instruments-store`buckets **continuously**.
So`get_bucket_name('market_data', 'CEFI')`/`get_market_data_bucket('cefi')`/`get_instruments_bucket(...)`delegating
to`resolve_bucket_name(...)`NOW would re-point those continuously-running consumers to env-tiered names that don't exist
on disk → first-write-failure (the exact bug this plan exists to prevent). Done-def #2's L2`config.py`migration was safe
because features-service's`features-\*`writes are in the "safe gap"; the legacy`get_bucket_name` consumer base includes
instruments-service + MTDS Group-A writes which are NOT.

**Options** (pick one — Ikenna/operator call per the work-split: bucket-naming SSOT decisions → Ikenna):

1. **Transitional delegate** — the `get_bucket_name` delegate keeps the Group-A domains (`instruments` / `market_data` /
   `features_calendar`) returning the FLAT name (`{prefix}-{ag}-{pid}` / `{prefix}-{pid}`) until Phase 2.6, then a
   follow-up flips them to `resolve_bucket_name` in the SAME window as the flat→env-tiered data migration. Group-B
   domains (`features_*` / `ml_*` / `execution` / `strategy`) delegate to `resolve_bucket_name` now (they're in the safe
   gap; `execution` was already env-tiered via the old `get_bucket_name` Group-B path so no change).
2. **Defer the whole delegate to the Phase-2.6 window** — land the `get_bucket_name` → `resolve_bucket_name` delegate
   (all domains) as part of Phase 2.6, alongside the flat→env-tiered provisioning + data migration + the write-pause
   cutover. Cleaner (one flip, no transitional state) but pushes Done-def #3 from Phase-1-code-complete to Phase 2.6.
3. **Confirm the per-domain env-override shield** — if instruments-service + MTDS already set `INSTRUMENTS_GCS_BUCKET` /
   `MARKET_DATA_GCS_BUCKET[_{AG}]` (or equivalents) to the flat names in their runtime configs, the delegate's
   env-override pre-check (`get_bucket_name` already has it) returns the flat name regardless of the yaml → safe to
   delegate all domains now. Needs a probe of instruments-service + MTDS configs to confirm; fragile if the override
   isn't set everywhere.

Slot 4's lean recommendation: option 1 (transitional delegate) — Group-B delegates now (matches the (b+) "code-first,
physical-migration-second" sequence + the Done-def #2 precedent), Group-A flips with Phase 2.6. But this is Ikenna's
call. **Until resolved, slot 4 does NOT land the Done-def #3 delegate** (the riskiest item; warrants the sequencing
decision first). Slot 1: route a cross-side ping to Ikenna.

#### A6 — [pending Ikenna/operator]

## Deferred work after 2026-05-11 slot 4 session

The 2026-05-11 `harsh-bucket-and-adapter-tab` (slot 4) session shipped: the parity-test extension (UTL@`e8dc6e3`), the
canonical-layer decision (a, with a Phase-0 caveat), the full 4-layer pre-audit manifest + per-layer migration recipe +
QG STEP 5.69 design, the FINDING that the yaml features-\* env-tier is unprovisioned, and the
[`issues/mtds_sports_available_at_wiring_2026_05_11.md`](issues/mtds_sports_available_at_wiring_2026_05_11.md) sports
audit. Items still open are tracked here so the next agent picks up cleanly.

| Item                                                                                                                                    | Status as of 2026-05-11 (PM-time)                                                 | Successor / blocker                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Done-def #1 — decide canonical layer                                                                                                    | `done` ([x]) — option (b) (operator/Ikenna): yaml canonical, env-tiered           | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Phase 0 (re-shaped: yaml-correctness fixes only) — add prediction/sports keys + uncomment GCP features-calendar + doc shape conventions | `done` ([x] partial) — deployment-service@`a7eba4f` + UTL@`2118b1e` (parity test) | The bucket PROVISIONING + flat-bucket DATA MIGRATION + reader/writer repoint is `code_freeze` Phase 2.6 (2026-05-15→05-19) — NOT slot 4's to execute now (per option (b) "code-first, physical-migration-second"). `aws s3 ls` probe still pending (no AWS CLI on the slot machine — `ml-*`/`strategy`/`execution` confirmed env-tiered on GCP). `-test-` variant canonicalisation = a Phase-0 sub-item flagged for operator OK on the canonical shape.                                                                                                                                                                          |
| Done-def #2 — migrate per-family `config.py` `*_bucket_template` → resolver                                                             | `done` ([x]) — features-service@`8f03ceeb` (sub-agent fan-out)                    | DEFERRED sub-items split off: (a) cross_instrument/multi_timeframe `get_output_bucket` — **BLOCKED on Q5** (the `features-cross-instrument`/`features-multi-timeframe` bucket names overflow the 63-char limit under the (b+) env-tier template — needs an Ikenna design call); (b) `dependency_checker.py` inline templates (blocked on UTL `BaseDependencyChecker` migration + `test_mode`-infra rewrite + ~6-test blast radius — note: after Phase 0e the `market-data` probe template now DRIFTS from the env-tiered yaml; must land in the Phase-2.6 window or via the UTL migration).                                      |
| **Phase 0e** — env-tier the Group-A bucket kinds in yaml + parity test                                                                  | `done` ([x]) — deployment-service@`a5c2082` + UTL@`ba6089c`                       | `market-data`/`instruments-store`/`features-calendar`/`market-data-tick-prediction`/`instruments-store-prediction` env-tiered on both clouds; §-header comment updated; all names verified ≤63 chars. Remaining env-less GCP entries (`dex-*`/`*-defi` raw, `pnl-store-defi`/etc shape-alignment, `events`/`config-store`) split into a new `- [ ]` sub-todo (the DeFi-raw ones are a clean add; `pnl-store-defi`/etc need a shape decision; `events` is operator-gated due to workspace-wide `{pid}-events` refs). code-first per code_freeze sequencing — provisioning + flat-bucket migration = Phase 2.6 (2026-05-15→05-19). |
| cross_instrument/multi_timeframe yaml-gap sub-todo (the last loose end of Done-def #2)                                                  | `done` ([x]) — Q5/A5 resolved + implemented 2026-05-11 (slot 4 cont. 3)           | Q5/A5 Option 1 / Scope A: short alias kinds `features-xinstrument`/`features-mtf` in the yaml + UTL `_KIND_ALIASES` bridge + `${DEPLOYMENT_ENV_SHORT}` 3-char form everywhere + `-pred-` bucket-name strings + config.py `get_output_bucket` → `resolve_bucket`. Evidence: UTL@`4ee24b5` + deployment-service@`008e371` + deployment-service@`f81d043` + UTL@`e3dd846` + features-service@`e980ecfd`. Follow-up (P2, deferred): drop stale `OUTPUT_BUCKET_TEMPLATE` doc refs (features-service-docs sweep).                                                                                                                      |
| Done-def #3 — delegate legacy `get_bucket_name` + `BUCKET_PREFIXES` → resolver                                                          | `blocked` ([ ]) — Q6 (sequencing)                                                 | No hard gate (UTL-only) but **now blocked on Q6** (Ikenna sequencing call): a naive delegate landing before Phase 2.6 re-points Group-A consumers (instruments-service / MTDS — `market-data`/`instruments-store`, written continuously) to non-existent env-tiered names → first-write-failure. Options: (i) transitional delegate (Group-B now, Group-A flips with Phase 2.6 — slot 4 rec); (ii) defer whole delegate to Phase 2.6; (iii) confirm per-domain env-override shield. See § Open questions Q6. Pre-audit done (~36+ consumers). Slot 1: route a cross-side ping to Ikenna.                                         |
| Done-def #4 — extend parity test                                                                                                        | `done` ([x]) — UTL@`e8dc6e3` (+ UTL@`2118b1e` Phase-0 follow-up)                  | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Done-def #5 — QG STEP 5.68 (`f"gs://..."` ratchet)                                                                                      | `todo` ([ ])                                                                      | DEFERRED-AFTER #2 (done) + #3 (else ratchet baseline bakes in to-be-removed inline templates); design written in § Pre-audit manifest → "QG STEP 5.6X design"; STEP **5.68** (5.66 reserved for multi-process-launcher, 5.67 taken by slot 6 — confirm 5.68 free in `base-service.sh`).                                                                                                                                                                                                                                                                                                                                          |
| Done-def #6 — plan-flip cite + grep audit table (zero drift)                                                                            | `blocked` ([ ])                                                                   | DEFERRED-AFTER #3 + #5 + the Phase-2.6 provisioning/migration (then verify drift ≤0.01% per bucket + zero readers still hit flat names).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Sports-adapter `available_at` (the other slot-4 half)                                                                                   | `done` ([x] — code shipped MTDS@`c186ecb`)                                        | Code wired (`_process_sports_venue_with_leagues` stamps `available_at = bm_time` via UTL `stamp_available_at_odds_snapshot` @UTL`2ab3685`, shard-level failure isolation, 5 tests). REMAINING: slot 1 routes a cross-side ping to Ikenna slot 3 to flip the `available_at_lookahead_bias_completion_2026_05_08.md` Phase 1 "TRACK — sports adapter stamping" todo; + the 2 open design Qs in `issues/mtds_sports_available_at_wiring_2026_05_11.md` (all-NaT routing; sports-path `assert_available_at_present` guard) for Ikenna slot 3 / sports_master.                                                                        |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **`available_at` per-adapter stamping for CeFi-bar / DeFi / TradFi / Predictions** — open in
  [`available_at_lookahead_bias_completion_2026_05_08.md`](available_at_lookahead_bias_completion_2026_05_08.md) Phase 1
  (CeFi tick stamping shipped MTDS@`4a00bd5`; sports odds shipped MTDS@`c186ecb` this session; the rest are
  TRACKED/owned by the respective `*_master` plans). Not slot-4 scope.
- **The `-test-` E2E bucket variant naming inconsistency** on disk (`instruments-store-cefi-test-{pid}` vs
  `market-data-tick-test-cefi-{pid}`) — Phase 0 sub-item; the canonical shape is `{prefix}-{ag}-test-{pid}`
  (`DEPLOYMENT_ENV=test` substitution for env-tiered kinds); the before-AG `market-data-tick-test-*` variants are
  deprecated test-mode artefacts (documented in the yaml § header comment @`a7eba4f`).
- **features-service codex-compliance backlog (18 violations)** + **F9 org-naming drift** (origin =
  `CosmicTrader/features-service` vs manifest `IggyIkenna`) — slot-2 territory
  (`features_repo_consolidation_2026_05_08.md` Q1 + `features_service_qg_cleanup_2026_05_11.md`); the L2 migration
  commit landed cleanly on top of those (added 0 new codex violations).

## DONE-2026-05-11 — harsh-bucket-and-adapter-tab (slot 4) session

| Item                                                                                                           | Status                      | Commits                                                                                           |
| -------------------------------------------------------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------- |
| Done-def #4 — extend yaml-vs-resolver parity test (features-\*/sports/tradfi/prediction) + fix RED parity test | `done`                      | unified-trading-library@`e8dc6e3`; plan-flip PM@`59e92b18`                                        |
| Done-def #1 — decide canonical SSOT layer = (a) yaml (with Phase-0 caveat)                                     | `done`                      | PM@`59e92b18` (decision in plan body)                                                             |
| § Pre-audit manifest (4-layer drift map + L2/L3 migration recipes + QG STEP 5.69 design)                       | `done`                      | PM@`59e92b18`                                                                                     |
| § Open questions Q1 (resolver location UAC-vs-UTL), Q2 (proceed-with-config.py-now?), Q3 (STEP number)         | `done` (raised, 🟡 BLOCKED) | PM@`59e92b18`                                                                                     |
| § FINDING 2026-05-11 (yaml features-\* env-tier unprovisioned) + Phase 0 todo + Q4 (🔴 P0)                     | `done`                      | PM@`<this commit>`                                                                                |
| `issues/mtds_sports_available_at_wiring_2026_05_11.md` — MTDS-slice sports `available_at` wiring audit         | `done`                      | PM@`7c088961`                                                                                     |
| Boot ack ping                                                                                                  | `done`                      | PM@`eb52b83b` (then moved to `harsh_orchestrator/pings/slot_4.md` per the 2026-05-11 ledger-move) |

**No-gate prep complete (morning slot-4 session). Remaining items gated on Q2/Q4 + slot-3 Track E.**

## DONE-2026-05-11 (cont.) — harsh-bucket-and-adapter-tab (slot 4), post-Q4-resolution + Track-E-ship session

Q4 resolved (operator/Ikenna picked option (b) — yaml canonical, env-tiered; bucket provisioning + data migration =
`code_freeze` Phase 2.6, not slot 4's), and slot 3 shipped wave3x Track E (UTL@`2ab3685` —
`stamp_available_at_odds_snapshot`

- `stamp_available_at_injuries` + `stamp_available_at_post_match_cascade`). Both slot-4 halves became actionable; this
  session shipped:

| Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Status | Commits                                                |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------ |
| Phase 0 — yaml-correctness fixes (prediction/sports keys for features-delta-one/volatility; SPORTS for market-data/instruments-store; uncomment GCP features-calendar; § header doc'ing Group A/B + env-after-AG + canonical `-test-` shape)                                                                                                                                                                                                                          | `done` | deployment-service@`a7eba4f`                           |
| Parity test — Phase-0 follow-up (snapshot + tests match the new yaml; `_KNOWN_YAML_ASYMMETRIES` emptied; `test_features_calendar_resolves_aws_only`→`_both_clouds`; new `test_resolve_features_prediction_sports_keys`; `test_per_asset_group_kind_with_unmapped_asset_group_raises`→features-onchain) — 92 tests pass                                                                                                                                                | `done` | unified-trading-library@`2118b1e`                      |
| Done-def #2 — L2 `features-service/{family}/config.py` `*_bucket_template` → `resolve_bucket()` (new `features_service.common.resolve_bucket` wrapper; delta_one/volatility/onchain/calendar migrated; commodity/sports out-of-scope; cross_instrument/multi_timeframe partial — output Field kept pending yaml kinds; `feature_writer.py` lazy bucket; `tests/conftest.py`; 4 test-file fixes) — STEP 5.31 PASS, basedpyright 0 NEW, ruff clean, 0 NEW test failures | `done` | features-service@`8f03ceeb`                            |
| Sports-adapter `available_at` (other half) — wire `stamp_available_at_odds_snapshot(shard_df, "bm_time")` into `_process_sports_venue_with_leagues` before `StreamingParquetWriter.write_chunk` (shard-level failure isolation → `failed_shards` + continue, not raise; `bm_time` confirmed universal for ODDS_API; 5 new tests in `test_sports_odds_available_at.py`) — 5/5 pass, no regressions, basedpyright 0 NEW                                                 | `done` | market-tick-data-service@`c186ecb`                     |
| Plan-flips + scoreboard refresh + new split-off sub-todos (cross_instrument/multi_timeframe yaml-gap + dependency_checker deferred) + this DONE block                                                                                                                                                                                                                                                                                                                 | `done` | PM@`<this commit>` (this commit; references the above) |
| `issues/mtds_sports_available_at_wiring_2026_05_11.md` — marked the wiring shipped                                                                                                                                                                                                                                                                                                                                                                                    | `done` | PM@`<this commit>`                                     |

**Still open (all are `- [ ]` plan todos above):** Done-def #3 (legacy `get_bucket_name` delegate — UTL, ~36 consumers,
no hard gate, ships after #2 which is now done — next-session candidate); Done-def #5 (QG STEP 5.68 ratchet — ships
after #2 + #3); the cross_instrument/multi_timeframe yaml-gap sub-todo (add
`features-cross-instrument`/`features-multi-timeframe` yaml kinds → finish those 2 `get_output_bucket` migrations); the
dependency_checker.py sub-todo (blocked on UTL `BaseDependencyChecker` migration + `test_mode`-infra rewrite); Done-def
#6 (audit table — ships after #3 + #5 + the Phase-2.6 provisioning/migration); Phase 0 `aws s3 ls` probe + `-test-`
canonical-shape operator OK; cross-side ping to Ikenna slot 3 to flip the available_at Phase 1 sports todo + answer the
2 open design Qs in the sports issue doc.

## DONE-2026-05-11 (cont. 2) — harsh-bucket-and-adapter-tab (slot 4), Phase 0e session

| Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Status     | Commits                                                |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------ |
| Phase 0e — env-tier the Group-A bucket kinds (`market-data`/`instruments-store`/`features-calendar`/`market-data-tick-prediction`/`instruments-store-prediction`) in `cloud-providers.yaml`, both clouds, after asset_group; §-header comment updated; all names verified ≤63 chars                                                                                                                                                                                                                     | `done`     | deployment-service@`a5c2082`                           |
| Phase 0e — parity test (`_SNAPSHOT_YAML` Group-A entries env-tiered; `test_resolve_market_data_per_cloud_shape` / `_instruments_store_per_asset_group` / `_features_prediction_sports_keys` Group-A rows / `_features_calendar_resolves_both_clouds` expectations get `-staging-`; `market-data-tick-prediction`+`instruments-store-prediction` trimmed from snapshot — covered by live-yaml pin); ruff clean. pytest not runnable (origin UTL→UAC `BAR_TIMEFRAME_SECONDS` drift mid-flight — not mine) | `done`     | unified-trading-library@`ba6089c`                      |
| New deferred sub-todo: env-tier the remaining env-less GCP yaml entries (`dex-*`/`*-defi` raw — clean add; `pnl-store-defi`/`positions-store-defi`/`risk-store-defi` — shape-alignment needed; `events`/`config-store` — `events` operator-gated)                                                                                                                                                                                                                                                       | `captured` | (plan todo above)                                      |
| cross_instrument/multi_timeframe yaml-gap sub-todo → flipped to `status: blocked` + Q5 raised (the `features-cross-instrument`/`features-multi-timeframe` 63-char overflow — needs Ikenna design call; 4 options enumerated)                                                                                                                                                                                                                                                                            | `blocked`  | (plan + Q5)                                            |
| `dependency_checker.py` deferred-note updated for the post-Phase-0e `market-data`-probe-template drift                                                                                                                                                                                                                                                                                                                                                                                                  | `done`     | (plan)                                                 |
| Plan-flips (Phase 0e `[x]`) + new sub-todos + scoreboard rows + Q5 + this DONE block                                                                                                                                                                                                                                                                                                                                                                                                                    | `done`     | PM@`<this commit>` (this commit; references the above) |

**Still open after the Phase 0e session:** Done-def #3 (legacy `get_bucket_name`+`BUCKET_PREFIXES` delegate — UTL, ~36
consumers, no hard gate, ships after #2 which is done — **best next-session candidate**); the
cross_instrument/multi_timeframe yaml-gap sub-todo is now **BLOCKED on Q5** (Ikenna design call); the new
env-less-GCP-entries sub-todo (do the DeFi-raw `dex-*`/`*-defi` ones first — clean add; `pnl-store-defi`/etc +
`events`/`config-store` are shape-decision / operator-gated); Done-def #5 (QG STEP 5.68 ratchet — after #2 + #3);
Done-def #6 (audit table — after #3 + #5 + Phase 2.6); Phase 0 `aws s3 ls` probe + `-test-` canonical-shape operator OK;
cross-side ping to Ikenna slot 3 (sports `available_at` Phase 1 todo flip + 2 design Qs) + cross-side ping to Ikenna re
Q5. **Workspace observation (not slot-4-owned)**: `import unified_trading_library` is currently broken on
`origin/live-defi-rollout` — `availability_stamping.py:83` imports `BAR_TIMEFRAME_SECONDS` which
`unified_api_contracts/__init__.py` doesn't export — a UTL→UAC drift mid-flight (almost certainly the `available_at`
bar-boundary work; flagged in slot_4.md ping for visibility). Going quiet — next session picks up Done-def #3 + the
env-less-GCP-entries sub-todo (DeFi-raw first).

## DONE-2026-05-11 (cont. 3) — harsh-bucket-and-adapter-tab (slot 4), Q5/A5 implementation session

| Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Status | Commits                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------- |
| UTL `bucket_naming` — `_KIND_ALIASES` map (`features-cross-instrument`→`features-xinstrument`, `features-multi-timeframe`→`features-mtf`; applied in `resolve_bucket_name`) + `${DEPLOYMENT_ENV_SHORT}` substitution in `_substitute_env_vars` (3-char form `dev`/`stg`/`prd`/`test`/`ci` from `DEPLOYMENT_ENV`, default `prod`→`prd`; unknown → `BucketNamingError`)                                                                                                                                         | `done` | unified-trading-library@`4ee24b5`         |
| deployment-service `env_substitutor` — matching `${DEPLOYMENT_ENV_SHORT}` support (same map; `ValueError` on unknown) so both yaml-readers produce identical bucket names from `cloud-providers.yaml`                                                                                                                                                                                                                                                                                                         | `done` | deployment-service@`008e371`              |
| `cloud-providers.yaml` Q5/A5 sweep — `${DEPLOYMENT_ENV}`→`${DEPLOYMENT_ENV_SHORT}` (~82 occ, both clouds); `-prediction-`→`-pred-` in 14 prediction-related bucket-name STRINGS (keys unchanged); added `features-xinstrument` + `features-mtf` (5 per-AG each, env-tiered, both clouds); §-header comment rewritten (the `${DEPLOYMENT_ENV_SHORT}` convention + the `pred` rule + the kind aliases). All env-tiered names ≤63 chars (worst 60). yaml parses; prettier-clean                                  | `done` | deployment-service@`f81d043`              |
| parity test `test_bucket_naming.py` — `_SNAPSHOT_YAML` → `${DEPLOYMENT_ENV_SHORT}` + `-pred-`; all snapshot-test expectations `-staging-`→`-stg-` + `-prediction-`→`-pred-`; `_FEATURES_PIPELINE_KINDS` live-yaml pin gains `features-xinstrument`/`features-mtf` + `features-cross-instrument`/`features-multi-timeframe` (consumer aliases → SHORT-prefix resolved bucket) + `*-pred-` prefixes for the prediction kinds; `test_resolver_reads_live_env_each_call` assertions → `-stg-`/`-prd-`. ruff-clean | `done` | unified-trading-library@`e3dd846`         |
| features-service `cross_instrument/config.py` + `multi_timeframe/config.py` — deleted the `output_bucket_template` Field + `OUTPUT_BUCKET_TEMPLATE` alias; `get_output_bucket` → `resolve_bucket(kind="features-cross-instrument"/"features-multi-timeframe", asset_group=...)` (resolver aliases to `features-xinstrument`/`features-mtf`). No tests reference the removed Field. ruff-clean                                                                                                                 | `done` | features-service@`e980ecfd`               |
| Plan flips (cross_instrument/multi_timeframe yaml-gap sub-todo `[x]`; Done-def #3 NOTE + scoreboard `blocked`-on-Q6) + Q6 added to § Open questions + Q5 SHIPPED note + this DONE block                                                                                                                                                                                                                                                                                                                       | `done` | PM@`<this commit>` (references the above) |

**Still open after the Q5/A5 session:** **Done-def #3** (legacy `get_bucket_name`+`BUCKET_PREFIXES` delegate) — now
**BLOCKED on Q6** (Ikenna sequencing call: the delegate landing before Phase 2.6 re-points Group-A consumers to
non-existent env-tiered names — slot 4 rec = transitional delegate, Group-B now / Group-A flips with Phase 2.6); the
env-less-GCP-entries sub-todo (DeFi-raw `dex-*`/`*-defi` first — clean `${DEPLOYMENT_ENV_SHORT}` add;
`pnl-store-defi`/etc shape-decision + `events`/`config-store` operator-gated); Done-def #5 (QG STEP 5.68 ratchet — after
#2 done + #3); Done-def #6 (audit table — after #3 + #5 + Phase 2.6); the `dependency_checker.py` sub-todo (blocked on
UTL `BaseDependencyChecker` migration + `test_mode`-infra rewrite); Phase 0 `aws s3 ls` probe + `-test-` canonical-shape
operator OK; Phase 0f (VM-launcher env-awareness); Phase 0g (UI-env-tier verify — already shipped per codex); Phase 0h
(sync-script); Phase 0c/0d (= code_freeze Phase 2.6, 2026-05-15→05-19). **Cross-side (slot 1's action)**: route a
cross-side ping to Ikenna re **Q6** (Done-def #3 sequencing) — bucket-naming SSOT decisions → Ikenna per the work-split.
The prior cross-side asks (Ikenna slot 3 — sports `available_at` Phase 1 todo + 2 design Qs; Q5) are ✅ resolved.
**Workspace observation (not slot-4-owned, unchanged)**: `import unified_trading_library` broken on
`origin/live-defi-rollout` (`availability_stamping.py:83` → `BAR_TIMEFRAME_SECONDS` not exported from UAC `__init__.py`)
— blocks running the UTL parity test locally; the test is logically consistent with the resolver + yaml. Going quiet —
next session picks up Done-def #3 (pending Q6) + the env-less-GCP-entries sub-todo (DeFi-raw first).
