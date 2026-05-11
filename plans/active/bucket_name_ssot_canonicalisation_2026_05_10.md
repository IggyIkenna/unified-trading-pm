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

## FINDING 2026-05-11 (slot 4) — the yaml SSOT contradicts the provisioned features-\* infra (migration-blocking)

> **Severity**: P1 / migration-blocking — not a same-day operational outage (the L2 config.py templates are what's
> actually used in prod today, and they match reality), but a naive "migrate config.py onto `resolve_bucket_name` as-is"
> would re-create the exact first-write-failure class this plan exists to prevent. **Blast radius**: every features-\* /
> ml-\* bucket-writing service + `setup-buckets.sh`. **Owner**: needs an operator decision (Q4 below — a "bucket-naming
> SSOT decision" per the work-split split-principle = Ikenna/operator territory).

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
      DIRECTION**, BUT **a Phase 0 yaml-vs-provisioned-infra reconciliation is now a hard prerequisite** — see the
      FINDING below + the new Phase 0 todo. Rationale for (a): (1) keeps the env axis available for
      prod/staging/dev/test isolation; (2) yaml already models GCP↔AWS asymmetries (`tick-` infix on GCP `market-data`,
      AWS-only `features-calendar`) the per-family templates don't; (3) the UTL resolver already reads the yaml — so (a)
      just _removes_ duplicate layers, no new SSOT. **Caveat (FINDING 2026-05-11)**: the on-disk GCP features-_ buckets
      (`features-delta-one-cefi-central-element-323112`, `features-onchain-central-element-323112`,
      `features-sports-...`, `features-volatility-{cefi,defi,...}-...`, `features-calendar-...`) are FLAT — **no
      `${DEPLOYMENT_ENV}` tier** — so the current yaml `features-delta-one-cefi-${DEPLOYMENT_ENV}-${GCP_PROJECT_ID}`
      resolves to a bucket that doesn't exist (`...cefi-prod-...`); the L2 config.py templates
      (`features-delta-one-{ag}-{pid}`, no env) are the ones that match reality. A naive "config.py →
      resolve_bucket_name as-is" migration would re-create the exact first-write-failure bug this plan exists to
      prevent. So (a) holds, but the yaml needs a fix-forward FIRST (drop the spurious env tier from GCP features-_ OR
      provision the env-tiered buckets — operator decision; plus add the missing `prediction`/`sports` keys for
      `features-delta-one`/`features-volatility`/`features-onchain`/`instruments-store`/ `market-data`, add the GCP
      `features-calendar` entry, and resolve the `-test-` variant naming inconsistency
      `instruments-store-cefi-test-{pid}` vs `market-data-tick-test-cefi-{pid}`). Collapse targets unchanged: L2
      config.py `*_bucket_template` Field defaults → `resolve_bucket_name()`; legacy
      `cloud_interface.constants.get_bucket_name` + `BUCKET_PREFIXES` → delegate to `resolve_bucket_name()`. See §
      "Pre-audit manifest" + § "FINDING 2026-05-11" below.
- [ ] **[AGENT] P0**. **Phase 0 — reconcile `deployment-service/configs/cloud-providers.yaml` with the provisioned
      features-\* / instruments-store / market-data infra (NEW — surfaced by the 2026-05-11 slot-4 GCP bucket probe).**
      MUST land before the L2 config.py migration (else the migration produces resolver-derived bucket names that don't
      exist on disk). Steps: (1) probe GCP (done — see § FINDING) + AWS (`aws s3 ls` — couldn't run from slot, needs a
      machine with the AWS CLI / ADC) for the actual bucket names; (2) operator decision: drop the spurious
      `${DEPLOYMENT_ENV}` tier from GCP features-\* yaml entries to match reality, OR provision the env-tiered buckets +
      migrate data to match the yaml (the riskier path; default to (drop)); (3) add the missing per-asset_group keys
      (`prediction`/`sports` for `features-delta-one`/`features-volatility`/`features-onchain`/`instruments-store`/
      `market-data` — those buckets exist on disk but aren't in the yaml); (4) add the GCP `features-calendar` entry
      (the bucket exists: `features-calendar-central-element-323112`; the yaml has it commented out — uncomment + fix);
      (5) decide whether/how the resolver models the `-test-` E2E variant (current on-disk shapes are inconsistent:
      `instruments-store-cefi-test-{pid}` puts `test` after AG, `market-data-tick-test-cefi-{pid}` puts it before AG);
      (6) update the parity test (UTL@`e8dc6e3`'s `_FEATURES_PIPELINE_KINDS` + `_KNOWN_YAML_ASYMMETRIES`) to match; (7)
      verify each resolver-derived name `gcloud storage ls`-exists. status: blocked — note: "2026-05-11 slot 4 —
      surfaced via GCP probe; needs an operator decision on (drop env tier) vs (provision env-tiered buckets) — see §
      Open questions Q4 (🔴 P0)."
- [ ] **[SCRIPT] P1**. Migrate per-family `features-service/features_service/{family}/config.py` `*_bucket_template`
      Field defaults to call `bucket_naming.resolve_bucket_name(...)` lazily at runtime (delete the
      `Field(default="...")` template + repoint `get_*_bucket(...)` method bodies). **GATED** on Harsh slot 2
      features-consolidation Phase 4 import-rewrite stabilising (per work-split `work_split_2026_05_11_harsh.md` § "Slot
      4" — "runs AFTER Phase 4 ... or runs against the consolidated state"). Migration recipe (per-family, exact shapes)
      in § "Pre-audit manifest" below. status: blocked — note: "2026-05-11 slot 4 — recipe + per-family mapping written;
      impl waits on slot 2 Phase 4 ping OR slot-1 green-light to proceed against consolidated state (see § Open
      questions Q2)."
- [ ] **[SCRIPT] P1**. Delegate the legacy `unified_trading_library.cloud_interface.constants.get_bucket_name` +
      `BUCKET_PREFIXES` to `bucket_naming.resolve_bucket_name(...)` (a `{domain}` → `{kind}` translation map + per-cloud
      dispatch). The legacy `{DOMAIN}_GCS_BUCKET[_{ASSET_GROUP}]` env-override shim either (a) survives as a thin
      wrapper in `get_bucket_name`, OR (b) is dropped in favour of the `${DEPLOYMENT_ENV}` axis (decide at impl time per
      whether the per-domain override env vars are actively used). status: todo — note: "2026-05-11 slot 4 — added as
      explicit todo (the resolver docstring already names this 'a follow-up step'; folding it into this plan so it
      doesn't fall off-radar); no gate (UTL-only); ships after the config.py migration so consumers don't briefly see
      two delegating paths."
- [ ] **[SCRIPT] P1**. Workspace QG step `STEP 5.6X` AST-walks for inline `f"gs://{bucket}/..."` /
      `f"s3://{bucket}/..."` formatters; fails CI if any new ones land outside the resolver. **Design (slot 4
      2026-05-11)**: baseline-ratchet shape (count current `gs://`/`s3://` f-strings WITHOUT a `# noqa: gs-uri` marker
      per repo → fail if the count grows). Goes in `unified-trading-pm/scripts/quality-gates-base/base-service.sh` as a
      new STEP — number TBD (5.66/5.67/5.68 are reserved by
      CLAUDE.md/`available_at_lookahead_bias_completion_2026_05_08.md` for multi-process-launcher /
      record_captured-stamping / feature-compute checks respectively, so this lands at **5.69** unless slot 1 reassigns
      — see § Open questions Q3). Full design in § "Pre-audit manifest" → "QG STEP 5.6X design". status: todo — note:
      "2026-05-11 slot 4 — design written; ships after the config.py migration (else the ratchet baseline would bake in
      the un-migrated sites)."
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

- `aws_migration_defi_first_2026_05_07.md` — AWS yaml has `features-calendar` entry but GCP doesn't; the parity
  regression test at UTL@`780a9575` fired on this drift. **RESOLVED 2026-05-11 (slot 4, UTL@`e8dc6e3`)**: the parity
  test now allowlists the `features-calendar` GCP-missing asymmetry (`_KNOWN_YAML_ASYMMETRIES`, with the documented
  yaml-comment reason) + a stale-allowlist guard. Undocumented drift still fails.
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

**Status**: 🟡 BLOCKED — needs an operator decision; **migration-blocking** for the L2 config.py migration; routed via
ping with `🔴 P0` marker.

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

**A1 (resolver location) — RESOLVED: keep the resolver in UTL** (`unified_trading_library.cloud_interface.bucket_naming`).
The plan-of-record is the authoritative design SSOT; the work-split's `python -c "from unified_api_contracts.bucket_naming
import ..."` line was a sloppy paste, not a deliberate "move to UAC" decision. Slot 1 corrected the work-split § "Slot 4"
done-definition + the LEDGER "Repos owned" line to say `unified_trading_library.cloud_interface.bucket_naming`. (CLAUDE.md
lists "bucket-naming SSOT *decisions*" as Ikenna's human-approval surface — that's about the SSOT *content* (the yaml),
not the resolver's code location. If the operator later wants the resolver promoted to UAC, that's a separate
"move resolver UTL→UAC + re-audit consumers" step, not a blocker for this plan.)

**A2 (proceed with config.py migration now vs wait for slot 2 Phase 4) — RESOLVED: the slot-2-Phase-4 gate is CLEAR**
(slot 2 shipped Phase 4 import rewrite 4.1-4.5 this cycle; the per-family config.py paths are stable; slot 2 is now on
`features_service_qg_cleanup_2026_05_11.md`, which doesn't churn those paths). **BUT the migration is now blocked on Q4** —
the yaml-vs-provisioned-reality env-tier mismatch MUST be settled before the config.py → `resolve_bucket_name` migration
lands, or it re-creates the first-write-failure bug this plan exists to prevent. So: **proceed with the L2 migration as
soon as Q4 is answered**, not before.

**A3 (QG STEP number) — RESOLVED: STEP 5.69 for the inline-`f"gs://{bucket}/..."`-formatter check** (confirm it's free
in `base-service.sh` / the codex QG template when you implement). Note: Harsh slot 6 is adding a separate QG STEP for
the Track-D P0-2 banned-NaN-placeholder / bypass-`record_captured` patterns — that takes the *next* free number (5.70+);
first to land claims, second adjusts; coordinate via the template.

**A4 (P0 — yaml features-* env-tier mismatch) — surfaced to the operator 2026-05-11** + added to the cross-side ping
to Ikenna (bucket-naming SSOT is on Ikenna's human-approval surface per CLAUDE.md). Slot 1 endorses slot 4's
recommendation **(a) make the yaml match reality** — drop `${DEPLOYMENT_ENV}` from the GCP `features-*` (+ `ml-*` if same
issue once probed) entries, add the missing `prediction`/`sports` keys, uncomment GCP `features-calendar`, pick + model
one canonical `-test-` variant shape. Low-risk (no bucket renames / data migration); the lost prod/staging/dev features-*
isolation was never actually provisioned, so nothing changes operationally. **Status: AWAITING OPERATOR / IKENNA DECISION** —
the L2 config.py migration + Phase 0 stay blocked until it lands. (Do NOT restore per-package ignores or env-prefix the
config.py templates to "fix" it — the yaml is the SSOT and it must reflect what's provisioned.)


## Deferred work after 2026-05-11 slot 4 session

The 2026-05-11 `harsh-bucket-and-adapter-tab` (slot 4) session shipped: the parity-test extension (UTL@`e8dc6e3`), the
canonical-layer decision (a, with a Phase-0 caveat), the full 4-layer pre-audit manifest + per-layer migration recipe +
QG STEP 5.69 design, the FINDING that the yaml features-\* env-tier is unprovisioned, and the
[`issues/mtds_sports_available_at_wiring_2026_05_11.md`](issues/mtds_sports_available_at_wiring_2026_05_11.md) sports
audit. Items still open are tracked here so the next agent picks up cleanly.

| Item                                                                           | Status as of 2026-05-11                                                  | Successor / blocker                                                                                                                                                                                                                                                                                                                                    |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Done-def #1 — decide canonical layer                                           | `done` ([x]) — (a) yaml canonical + Phase-0 caveat                       | —                                                                                                                                                                                                                                                                                                                                                      |
| Done-def #1.5 — **Phase 0** reconcile yaml ↔ provisioned features-\* infra    | `blocked` ([ ])                                                          | DEFERRED-AFTER-Q4 (operator decision: drop env tier vs provision env-tiered buckets); also needs an `aws s3 ls` probe (no AWS CLI on the slot machine)                                                                                                                                                                                                 |
| Done-def #2 — migrate per-family `config.py` `*_bucket_template` → resolver    | `blocked` ([ ])                                                          | DEFERRED-AFTER Phase 0 + DEFERRED-AFTER Q2 (slot-1 green-light to proceed against consolidated state, or slot-2 "Phase 4 done" ping — slot 2 has now verified Phase 4.1-4.5 done + Phase 7 [x]; the residual blocker is the forward-collision with slot 2's 4.6 codex-cleanup workstream + Q2 not yet answered)                                        |
| Done-def #3 — delegate legacy `get_bucket_name` + `BUCKET_PREFIXES` → resolver | `todo` ([ ])                                                             | No hard gate (UTL-only) but ships after #2 + needs a workspace-consumer pre-audit (~36+ files across instruments-service / execution-service / deployment-service / PM scripts grep `get_bucket_name\|BUCKET_PREFIXES\|get_*_bucket\|get_write_bucket_name` — list in commit body)                                                                     |
| Done-def #4 — extend parity test                                               | `done` ([x]) — UTL@`e8dc6e3`                                             | —                                                                                                                                                                                                                                                                                                                                                      |
| Done-def #5 — QG STEP 5.69 (`f"gs://..."` ratchet)                             | `todo` ([ ])                                                             | DEFERRED-AFTER #2 (else ratchet baseline bakes in un-migrated sites); design written in § Pre-audit manifest → "QG STEP 5.6X design"; STEP number pending Q3                                                                                                                                                                                           |
| Done-def #6 — plan-flip cite + grep audit table (zero drift)                   | `blocked` ([ ])                                                          | DEFERRED-AFTER #2 + #3 + #5                                                                                                                                                                                                                                                                                                                            |
| Sports-adapter `available_at` (the other slot-4 half)                          | `audit-shipped` — `issues/mtds_sports_available_at_wiring_2026_05_11.md` | DEFERRED-AFTER slot-3 wave3x Track E ship (UTL helpers final shape) + Q-A in the issue doc (odds `available_at` = bm_time vs +latency — Ikenna slot 3 / sports_master call). NOT hard-gated on Ikenna slot 3 Phase 0 (that's for MDPS-derived bar data). The wiring itself is small (~few lines in `_process_sports_venue_with_leagues` + ~3-5 tests). |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **`available_at` per-adapter stamping for CeFi-bar / DeFi / TradFi / Predictions** — open in
  [`available_at_lookahead_bias_completion_2026_05_08.md`](available_at_lookahead_bias_completion_2026_05_08.md) Phase 1
  (CeFi tick stamping shipped MTDS@`4a00bd5`; the rest are TRACKED/owned by the respective `*_master` plans). Not slot-4
  scope.
- **The `-test-` E2E bucket variant naming inconsistency** on disk (`instruments-store-cefi-test-{pid}` vs
  `market-data-tick-test-cefi-{pid}`) — folded into this plan's new Phase 0 step (5) above.

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

**No-gate prep complete. Remaining items (#1.5 Phase 0 / #2 config.py migration / #3 legacy-delegate / #5 QG STEP / #6
audit-table / sports wiring) all gated on operator/slot-1 decisions (Q2, Q4) or upstream slots (slot-3 wave3x Track E).
Going quiet — next session picks up once Q2/Q4 answered and/or Track E lands.**
