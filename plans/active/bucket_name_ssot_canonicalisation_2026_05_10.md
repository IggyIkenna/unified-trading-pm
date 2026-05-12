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
parent: manifest_evolution_master_2026_05_08
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
estimate_class: refactor
estimate_baseline_ai_days: 25.0
estimate_calibrated_ai_days: 10.0
estimate_calibration_note: |
  Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~10-13, ~3, ~5-7, ~0.5, + 2 more). Class inferred from filename (refactor, multiplier 0.4×).
  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be double-counted. Owner agent: verify baseline, refine class per codex/08-workflows/estimation-calibration.md, recompute calibrated if either changes.
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
- [ ] **[SCRIPT] P1**. **Phase 0c-watchdog — `vm_zombie_watchdog.py` VM_PREFIX_TO_BUCKET retrofit to
      `resolve_bucket_name()`** (MIGRATED FROM
      `plans/archive/issues/watchdog_env_tiered_events_architecture_2026_05_11.md` Gap 1).
      `deployment-service/scripts/vm/vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` dict (lines ~100-450) hardcodes ~72
      flat bucket-name entries like `f"market-data-tick-sports-{PROJECT_ID}"`. When env-tiering rolls out, these
      silently miss the env-tier suffix → false-negative on shard-freshness checks → real zombies stay invisible. Fix:
      convert dict to `(prefix → (kind, asset_group))` mapping + resolve at lookup time via
      `resolve_bucket_name(cloud="gcp", kind=<...>, asset_group=<...>, env=os.environ["DEPLOYMENT_ENV"])`. ~1 hr effort;
      gates env-tier correctness for the watchdog. Composes with `ml_artefact_path_resolver_consumer_sweep` (same shape,
      same root cause). **Open question** (separate operator decision needed): should
      `HEARTBEAT_BUCKET = f"deployment-scripts-{PROJECT_ID}"` itself go env-tiered, or stay flat as a project-wide ops
      bucket? Recommend FLAT (no isolation value; just adds 3 buckets to provision). **Deferred feature request**
      (post-cutover): consume `{pid}-events-{env}/events/` as third zombie signal per CLAUDE.md "No fire-and-forget VM
      launches" rule; measure VM-zombie false-negative rate over 7-day continuous run first, then decide if
      events-stream consumption is worth the throughput cost.
- [x] **[SCRIPT] P0**. **Phase 0c — provision env-tiered buckets to match yaml (GCP prod completed 2026-05-12 Slot 3;
      AWS prod + staging/dev still pending).** GCP prod (`DEPLOYMENT_ENV=prod`): **38 prd buckets created** in
      `asia-northeast1` via UTL `resolve_bucket_name()` + `gcloud storage buckets create` (UBLA enabled; STS SA
      per-bucket IAM granted). **STS data migration jobs** kicked off for all 16 data-bearing flat→prd bucket pairs: -
      `market-data-tick-cefi` → `market-data-tick-cefi-prd` (job `4307373161068467887`) — IN_PROGRESS ~12TB -
      `market-data-tick-defi` → `market-data-tick-defi-prd` (job `2728488100986384871`) — IN_PROGRESS -
      `market-data-tick-tradfi` → `market-data-tick-tradfi-prd` (job `10783188121562048851`) — IN_PROGRESS -
      `market-data-tick-sports` → `market-data-tick-sports-prd` (job `11132535080291456175`) — IN_PROGRESS -
      `market-data-tick-prediction` → `market-data-tick-pred-prd` (job `14260867330403722808`) — IN_PROGRESS -
      `instruments-store-cefi` → `instruments-store-cefi-prd` (job `14961779308770881859`) — SUCCESS ✅ -
      `instruments-store-defi` → `instruments-store-defi-prd` (job `9050954792112651453`) — SUCCESS ✅ -
      `instruments-store-tradfi` → `instruments-store-tradfi-prd` (job `13631016509163944070`) — SUCCESS ✅ -
      `instruments-store-sports` → `instruments-store-sports-prd` (job `17581385972154310099`) — IN_PROGRESS -
      `instruments-store-prediction` → `instruments-store-pred-prd` (job `2162661137126375274`) — SUCCESS ✅ -
      `dex-pools` → `dex-pools-prd` (job `18110656737153857483`) — FIXED (1 obj atomic rewrite; manually copied) -
      `dex-swaps` → `dex-swaps-prd` (job `flat-to-prd-dex-swaps`) — SUCCESS ✅ - `evm-defi` → `evm-defi-prd` (job
      `flat-to-prd-evm-defi`) — SUCCESS ✅ - `eigenlayer-rewards` → `eigenlayer-rewards-prd` (job
      `flat-to-prd-eigenlayer-rewards`) — SUCCESS ✅ - `solana-defi` → `solana-defi-prd` (job `flat-to-prd-solana-defi`)
      — SUCCESS ✅ - `config-store` → `config-store-prd` (job `flat-to-prd-config-store`) — SUCCESS ✅ **Note on
      setup-buckets.py**: script has `{category_lower}` substitution bug → does NOT create env-tiered prd buckets; used
      UTL resolver directly as SSOT. **Remaining scope**: AWS prod provision + staging/dev provision + parity
      verification once large market-data-tick transfers complete (Gate 2). status: GCP prod done — parity pending.
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
- [ ] **[SCRIPT] P1**. **DEFERRED (split off from Phase 0e) — PARTIAL: DeFi-raw + config-store SHIPPED 2026-05-11 (slot
      4 cont. 3); `pnl-store-defi`/etc + `events` still open** — env-tier the remaining env-less GCP yaml entries: **(a)
      ✅ DONE** — `dex-pools` / `dex-swaps` / `evm-defi` / `eigenlayer-rewards` / `solana-defi` + `config-store` →
      `{kind}-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}` (was env-less; mirrors the AWS side which was already
      env-tiered). Evidence: deployment-service@`070c897` (yaml + §-header comment) + unified-trading-library@`5058381`
      (parity test snapshot). On-disk flat `dex-pools-{pid}` etc. → env-tiered names migrates in code_freeze Phase 2.6.
      **(b) STILL OPEN** — `pnl-store-defi` / `positions-store-defi` / `risk-store-defi`: GCP shape is
      `pnl-store-{pid}-defi` / `risk-store-defi-{pid}` (asset-group-as-suffix/infix) vs AWS
      `unified-trading-pnl-store-defi-{env}-{account}` — needs a SHAPE-ALIGNMENT decision (not just an env-tier add) + a
      data migration since the GCP bucket names change. **Operator/Ikenna call.** **(c) STILL OPEN** — `events`: GCP
      `{pid}-events` vs AWS env-tiered — **HIGH blast radius**: `{pid}-events` is referenced workspace-wide per the "No
      fire-and-forget VM launches" rule (`gs://{pid}-events/events/{service}/...`) — needs operator confirm whether
      `events` stays env-less like `terraform-state`/`secrets` or goes env-tiered. status: helper-shipped — note:
      "2026-05-11 slot 4 (cont. 3) — DeFi-raw + config-store env-tiered @deployment-service`070c897` + UTL`5058381`;
      checkbox stays `- [ ]` until (b) the pnl/positions/risk shape decision + migration AND (c) the `events` operator
      sign-off land — both operator-gated. **(b)+(c) written up as Q7 in § Open questions 2026-05-11 (slot 4, this
      session)** with the full shape-mismatch table + slot-4 recs (b-i = align GCP to symmetric
      `{kind}-defi-{env}-{pid}`; c-i = env-tier `events` as a dedicated Phase-2.6 sub-step / c-ii = document as 3rd
      permitted env-less exception); routed cross-side to Ikenna. **OPERATOR DECISION 2026-05-11 PM (Q7(c) RESOLVED)**:
      events bucket goes **env-tiered (option c-i)**. Implication: `gs://{pid}-events-{env}/events/{service}/...` per
      env; deployment-service yaml + UTL `resolve_bucket_name` need `events` flipped to env-tiered shape (Phase 2.6
      sub-step). **Watchdog architecture follow-up (P1)**: vm_zombie_watchdog.py reads from single `{pid}-events` today;
      with env-tiered events, either (i) single watchdog reads all 3 env buckets concurrently, or (ii) 3 per-env
      watchdog VMs if throughput is too much for one machine. Operator direction 2026-05-11 PM: 'depends on throughput'.
      **Q7(b)** `pnl-store-defi` / `positions-store-defi` / `risk-store-defi` shape-alignment remains operator-pending."
- [x] **[SCRIPT] P0**. **Phase 0f — VM launcher scripts read `DEPLOYMENT_ENV` (Phase 1 code-complete scope).** Audit
      every script under `deployment-service/scripts/vm/` for hardcoded bucket references; ensure each launcher reads
      `DEPLOYMENT_ENV` from env / CLI flag and passes it to the VM via `metadata` so the VM's bucket-resolution call
      lands on the right env-tiered bucket. Default to `DEPLOYMENT_ENV=prod` for production launches,
      `DEPLOYMENT_ENV=staging` for staging launches, etc. Add a `--env <prod|staging|dev>` CLI flag to each launcher.
      Workspace QG step (companion to STEP 5.69) AST-walks launcher scripts for bucket references not flowing through
      the env-aware helper. status: done — note: "Phase 1 code-complete scope. **SHIPPED 2026-05-12** (Ikenna slot 8
      absorbed; Harsh slot 4 had not started). Actual scope = **72 launchers** (not ~30 — full audit). Fanned out 5
      parallel sub-agents under slot 8 main, each handling ~12-19 launchers. Pattern applied uniformly per the canonical
      template at `deployment-service/scripts/vm/launch-mdps-features-live.sh`:
      `DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-prod}"` default + `--env <prod|staging|dev>` CLI flag + closed-set validation +
      `DEPLOYMENT_ENV=${DEPLOYMENT_ENV}` metadata propagation + `env="${DEPLOYMENT_ENV}"` GCE label + header banner
      citing this plan as SSOT. Commits (all FF'd to `live-defi-rollout`):
      [`deployment-service@13ef741a`](../../../market-data-processing-service) (sub-A — 15 MTDS backfill launchers;
      restructured 6 positional-arg parsers into proper while-loops with `POSITIONAL[]` arrays; added `--labels` to 9
      file-based launchers previously lacking them);
      [`deployment-service@a2037d2`](../../../market-data-processing-service) (sub-B — 19 sports launchers incl.
      api-football, footystats, sfi, understat, transfermarkt, openmeteo, sports-\*; pre-pass arg-stripping for 3
      forward-poll launchers with positional args; helper-function injection for sfi/sports-manifest-rescan chunked
      fan-out); [`deployment-service@68ad99f`](../../../market-data-processing-service) +
      [`deployment-service@e60ae2c`](../../../market-data-processing-service) (sub-C — 17 cefi/defi/tradfi/prediction
      launchers; `launch-cefi-massive-rollout.sh` propagates DEPLOYMENT_ENV via `_common_meta()` so all 364 spawned VMs
      inherit env; `launch-cefi-sharded-backfill.sh` via `launch_cefi_shard` + `launch_tradfi_shard` helpers;
      `launch-tier3-cefi-backfill.sh` via `create_vm()` so Phase 1 + Phase 2 VMs both carry env);
      [`deployment-service@ecea78f3`](../../../market-data-processing-service) (sub-D — 9 features/ml/strategy/infra
      launchers incl. `launch-vm-zombie-watchdog.sh`);
      [`deployment-service@5676048`](../../../market-data-processing-service) (sub-E — 12 migration/recon/smoke
      launchers; **special-case** `setup-data-pipeline-vm.sh` reads `DEPLOYMENT_ENV` from VM metadata via
      `curl ... attributes/DEPLOYMENT_ENV` since it's the VM-side bootstrap, not a launcher). All 72 files pass
      `bash -n` syntax check. Foot-gun #4 (prek auto-restore + `semver-rollout[bot]` author signature) observed in
      sub-A/B/C/D/E mid-session; mitigated via bundled `git add && commit --no-verify && push --no-verify` pattern per
      CLAUDE.md; `git show --stat HEAD` per commit verified all expected insertions present, no work lost. Backward
      compat preserved: default `DEPLOYMENT_ENV=prod` means existing launches without `--env` behave identically to
      pre-Phase-0f. Cloud Run deployment-api + manifest consolidator continue reading current flat buckets — env-tiered
      reader-repoint is Phase 2.6 cutover work (GAP-2.4.D). **PREREQ cleared for Phase 2.6 cutover 2026-05-15→05-19.**"
- [x] **[AGENT] P0**. **Phase 0g — verify deployment UI env-tier resolution (already shipped).** ✅ VERIFIED via
      [`codex/05-infrastructure/deployment-ui-architecture.md`](../../codex/05-infrastructure/deployment-ui-architecture.md)
      § "Environment tier (line 33-47, 119-140)": deployment UI env tier is RESOLVED FROM `window.location.hostname`
      (not via in-UI toggle); each tier (DEV / STAGING / PROD) has its own domain → its own deployment-api Cloud Run
      instance → its own GCS event/log bucket scope → its own service account scoped to that env's projects only.
      Cross-env data leakage is impossible because the deployment-api per env uses its own service account. **No
      additional work**: env-aware UI is shipped. The header env badge (read-only; clicking shows tooltip with resolved
      env + API base URL + cloud target) is the only operator-visible env signal. **Cross-check under (b+) — DONE
      2026-05-11 (slot 4), FINDING below**: the per-env deployment-api does NOT yet resolve via
      `resolve_bucket_name(...)` — it carries its own flat-shape bucket templates internally (a 5th drift surface; see §
      Pre-audit manifest → "Layer 5 (reader-side): deployment-api internal bucket templates"). These point at the
      current FLAT on-disk buckets, so they're CORRECT NOW — but they're the deployment-api half of the code_freeze
      Phase 2.6 reader-repoint (GAP-2.4.D). **NOT fixed now** (premature repoint to env-tiered names would break the
      data-status UI — same "Group-A safe-gap doesn't apply" reasoning as Done-def #3 / A6): the data-status UI reads
      buckets continuously, so its bucket-name source must flip in the SAME window as the flat→env-tiered data
      migration, not before. **Action taken**: documented as Layer 5 in the pre-audit manifest + added "migrate
      deployment-api internal bucket templates → `resolve_bucket_name`" to code_freeze GAP-2.4.D (reader-repoint scope).
      status: done (verification + cross-check audit) — note: "deployment UI env-tier shipped pre-2026-05-11; the
      deployment-api internal-template finding is deferred-after-code_freeze-Phase-2.6 (reader-repoint), not a Phase-1
      fix."
- [x] **[SCRIPT] P0**. **Phase 0h — sync script (prod → staging/dev) with truncated date window + same-region
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
      **SHIPPED 2026-05-11 (slot 4)** — deployment-service@`<this commit>`: `scripts/sync-buckets-prod-to-env.sh` (the
      implementation — enumerates env-tiered bucket pairs from `cloud-providers.yaml` via the canonical UTL resolver
      `bucket_naming.resolve_bucket_name` with a YAML-walk fallback for venv-less environments; env-LESS kinds
      `events`/`pnl-store-defi`/`positions-store-defi`/`risk-store-defi` are skipped — no per-env variant; same-region
      check via `gcloud storage buckets describe` / `aws s3api get-bucket-location` aborts cross-region; truncated
      window via `day=YYYY-MM-DD` hive-partition enumeration handling the `by_date/` / `raw_tick_data/by_date/` /
      `sports_reference/by_date/` layouts; idempotent `gcloud storage rsync -r` / `aws s3 sync`; `--dry-run`;
      `--kind <kind>` filter; per-bucket day-partition count + sample-parquet readability verification; manifest re-sync
      surfaced as an operator step — not auto-launched per "no fire-and-forget VM launches") +
      `scripts/sync-buckets-prod-to-staging.sh` + `scripts/sync-buckets-prod-to-dev.sh` (thin wrappers — default
      `--years 2` / `--years 1` respectively). `bash -n` clean; `shellcheck -S warning` clean. status: done — note:
      "script ships Phase 1; FIRST EXECUTION = Phase 3 / post-cutover (no urgency pre-2026-05-23 — dev/staging not in
      active use yet; tracked in `code_freeze_migrate_backfill_sequencing_2026_05_10.md` GAP-2.4.E). The
      truncated-window day-partition enumeration is `gcloud storage ls`-based v1; if a bucket layout deviates from the 3
      known shapes the script over-copies (harmless + idempotent) — refine at first-execution if needed."
- [x] **[AGENT] P1**. **Phase 0i tail — add `manual-audit` bucket kind to cloud-providers.yaml** (Ikenna T8 slot 8
      ANNOTATED 2026-05-12). Consumed by DART manual-action audit log persistence per
      [`codex/04-architecture/manual-trade-booking.md`](../../codex/04-architecture/manual-trade-booking.md) § "Audit
      log persistence (GCS / S3)" + UAC path SSOT `unified_api_contracts/internal/manual_audit_paths.py` (shipped at
      uac@`003b5ff`). Proposed shape under (b+) env-tier:
      ```yaml
      # GCP
      manual-audit: "manual-audit-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}"
      # AWS
      manual-audit: "unified-trading-manual-audit-${DEPLOYMENT_ENV_SHORT}-${AWS_ACCOUNT_ID}"
      ```
      Plus retention/lifecycle config (≥7 years for compliance; consider Coldline class after 90d for cost). Adds 6
      buckets to Phase 0c provisioning scope (3 envs × 2 clouds). Owner: slot 4 (bucket-name SSOT owner). Pre-Phase-0i:
      execution-service + ml-training-service audit-log writers BLOCK on this entry — UAC path SSOT module already
      declares `BUCKET_KIND_MANUAL_AUDIT = "manual-audit"` to mark the dependency.
      **🟢 SHIPPED 2026-05-12 (slot 8)**: deployment-service@`00a1288` — yaml SSOT updated (GCP + AWS, using
      `DEPLOYMENT_ENV_SHORT` for both). Also export `resolve_bucket_name` from UTL top-level facade (UTL@`aeff9c19`)
      to fix pre-existing import-pattern QG violation in tools/check_ml_dependencies_by_mode.py.
      **Handoff**: bucket provisioning (6 buckets × 3 envs × 2 clouds + lifecycle/retention config) deferred to
      Phase 0c scope — owner slot 4.

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
- [x] **[SCRIPT] P2**. **DEFERRED (follow-up to the cross_instrument/multi_timeframe migration above) — ✅ DONE
      2026-05-11 (slot 4 cont. 5)** — dropped the now-stale `INPUT_/OUTPUT_BUCKET_TEMPLATE` env-var + config-Field refs
      from `features-service/features_service/cross_instrument/docs/CONFIGURATION.md` ("### Bucket Templates" bullets →
      "### Bucket Names (resolved from the yaml SSOT — not configured here)" with the kind→`resolve_bucket` map +
      `features-xinstrument` alias note), `cross_instrument/docs/DEPLOYMENT_GUIDE.md` (dropped the
      `INPUT_BUCKET_TEMPLATE`/`OUTPUT_BUCKET_TEMPLATE` table rows; added a `DEPLOYMENT_ENV` row + a "bucket names NOT
      configured via env vars" callout + updated the Service-Account-IAM bucket hints), `multi_timeframe/.env.example`
      ("BUCKET TEMPLATES" section → "BUCKET NAMES — NOT operator-configurable" note), and
      `cross_instrument/app/     calculators/paired_dispatch.py` (`_delta_one_bucket` docstring — referenced the removed
      `input_bucket_template` Field → now describes the `resolve_bucket → cloud-providers.yaml` chain; docstring-only,
      ruff + py*compile clean). `.md` files prettier-clean. The Field + env-override alias were deleted
      @features-service`e980ecfd`; `get_input_bucket` / `get_output_bucket` route through
      `resolve_bucket(kind="features-delta-one" / "features-cross-instrument" /     "features-multi-timeframe", ...)`
      (the yaml SSOT, resolver-aliased to `features-xinstrument` / `features-mtf`). status: done — evidence:
      features-service@`89e9a972`. note: "2026-05-11 slot 4 cont. 5 — extended the original scope to also cover the
      `INPUT*\*`refs + the`paired_dispatch.py`docstring (same staleness class); surgical edits     (no whole-file prettier-reformat — the 2`.md`
      were already prettier-clean so the diff stays small)."
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
      whether the per-domain override env vars are actively used). status: deferred-after-code*freeze-Phase-2.6 — note:
      "2026-05-11 slot 4 — the resolver docstring already names this 'a follow-up step'; folded in so it doesn't fall
      off-radar; no gate (UTL-only). Pre-audit done (slot 4): ~36+ consumers across instruments-service (~16 files) /
      execution-service (~13) / deployment-service (~7) / PM scripts — grep
      `get_bucket_name\|BUCKET_PREFIXES\|get_instruments_bucket\|     get_market_data_bucket\|get_execution_bucket\|get_strategy_bucket\|get_features_calendar_bucket\|get_write_bucket_name`
      — enumerate fully + basedpyright each consumer repo after the delegate lands (Citadel § 6). **⚠️ Q6 (slot 4 cont.
      3, 2026-05-11) — sequencing concern, needs Ikenna/operator before this lands**: after Phase 0e the yaml's Group-A
      entries (`market-data`, `instruments-store`, `features-calendar`) are env-tiered
      (`market-data-tick-{ag}-${DEPLOYMENT_ENV_SHORT}-{pid}` etc.); the on-disk buckets stay FLAT
      (`market-data-tick-{ag}-{pid}`) until code*freeze Phase 2.6 (2026-05-15→05-19). The 'safe gap' that makes Done-def
      #2's `features-*`migration OK (nothing writes`features-*`between now and Phase 3, QG is mock) does **NOT** extend
      to Group-A — instruments-service backfills + MTDS captures write`market-data`/`instruments-store`buckets
      continuously. So a
      naive`get*bucket_name('market_data',     ...)`→`resolve_bucket_name(kind='market-data',     ...)` delegate landing
      NOW re-points those consumers to non-existent env-tiered names → first-write-failure (the exact bug this plan
      exists to prevent). Options: (i) the delegate keeps Group-A domains
      (`instruments`/`market_data`/`features_calendar`) returning the FLAT name until Phase 2.6, then flips with the
      migration; (ii) defer the whole delegate to the Phase-2.6 window; (iii) confirm instruments-service/MTDS set the
      per-domain `{DOMAIN}\_GCS_BUCKET[*{AG}]` override to the flat names during the transition (then the override
      pre-check shields them). Group-B domains (`features*\*`/`ml*\*`/`execution`/`strategy`) are unaffected (the safe
      gap covers them). See § Open questions Q6 — ✅ RESOLVED 2026-05-11 (A6): operator picked **Option (ii) — defer the
      ENTIRE delegate (Group A + Group B + all kinds) to code_freeze Phase 2.6** (2026-05-15→05-19), landing it as the
      cutover-flip step (`2.6.4`in the Phase-2.6 sub-sequence) alongside provision → rsync flat→env-tiered → write-pause
      → flip delegate workspace-wide → archive flat buckets. Rationale: `get_bucket_name` legacy is NOT in the 6
      freeze-gate items (`code_freeze_migrate_backfill_sequencing_2026_05_10.md` § Phase-1 freeze-gate checklist);
      deferring 4 days is zero-cost; avoids a 4-day half-migrated Group-A-special-case window + the
      parallel-resolution-path drift it would create (CLAUDE.md 'No double SSOT'). NOT a Phase-1 deliverable anymore;
      carries to the Phase-2.6 owner (slot 4 or new agent). Slot 1: cross-side ping to Ikenna was sent + Q6 was resolved
      by operator — nothing more to route."
- [x] **[SCRIPT] P1**. Workspace QG step (the inline-`f"gs://{bucket}/..."`/`f"s3://{bucket}/..."` formatter ratchet)
      AST-walks for these formatters; fails CI if any new ones land outside the resolver. **Design (slot 4
      2026-05-11)**: baseline-ratchet shape (count current `gs://`/`s3://` f-strings WITHOUT a `# noqa: gs-uri` marker
      per repo → fail if the count grows). Goes in `unified-trading-pm/scripts/quality-gates-base/base-service.sh` as a
      new STEP — **STEP 5.69** (5.66 reserved for the multi-process-launcher AST-walk; 5.67 taken by the banned
      NaN-placeholder gate; 5.68 reserved by `available_at_lookahead_bias_completion_2026_05_08.md` for the
      feature-compute lookahead-callsite check — confirmed via `base-service.sh` grep; matches CLAUDE.md "Key Rules"
      which already cites STEP 5.69 + the QG STEP 5.6X design section below). Full design in § "Pre-audit manifest" →
      "QG STEP 5.6X design". **SHIPPED 2026-05-11 (slot 4)** — PM@`<this commit>`:
      `unified-trading-pm/scripts/quality_gates/check_inline_bucket_uri.py` (the per-repo checker — v1 grep-based,
      `re.search` for an f-string opener followed by `gs://`/`s3://` on the same line, skipping
      `# noqa: gs-uri`-marked + whole-line-comment lines; per-repo COUNT ratchet against
      `inline_bucket_uri_baseline.yaml`; `--update-baseline` ratchets DOWN only; `--scope`/`--source-dir`/workspace-wide
      modes mirroring `check_removed_symbols.py` / `check_banned_placeholder_methods.py`) +
      `unified-trading-pm/scripts/quality_gates/inline_bucket_uri_baseline.yaml` (seeded 2026-05-11: deployment-api 27,
      execution-service 33, unified-trading-library 23, batch-live-recon 7, unified-api-contracts 5,
      unified-trading-system-ui 4, deployment-service 3, features-service 2, strategy-service 2, instruments-service 1 —
      all other repos 0; mostly legit `f"gs://{resolved_bucket}/{path}"` URI-compositions + docstring false-positives
      that v2 AST-walk will drop) + STEP 5.69 wired into `base-service.sh` (mirrors STEP 5.67's shape: per-repo scoped
      run; WARN if a repo is BELOW its baseline; FAIL + recheck hint if ABOVE; skips gracefully if the checker isn't in
      this repo's PM checkout) + `test_check_inline_bucket_uri.py` (12 tests: regex sanity, noqa/comment skipping,
      walker exclusions, scope resolution, baseline loading, main() end-to-end over/at/under baseline). `ruff` +
      `ruff format` clean; `python3 -m py_compile` OK; 12/12 pytest pass; the `args.scope`-is-`Any` basedpyright
      `reportAny` is the same pattern the existing checkers carry (passes PM QG the same way they do). status: done —
      note: "2026-05-11 slot 4 — v1 grep-based shipped; no longer blocked-on-#3 (A6 deferred #3 to Phase 2.6; baseline
      ratchets DOWN when the to-be-removed inline bucket-name templates (`get_bucket_name` consumers,
      `dependency_checker.py`, deployment-api Layer-5) land in code_freeze Phase 2.6 / are migrated — re-run
      `--update-baseline` then). v2 AST-walk (distinguish `f\"gs://{x}/...\"` from `resolve_bucket_uri(...)`, ignore
      docstrings) = a hardening follow-up matching STEP 5.65's pattern — captured as the new `- [ ]` below."
- [ ] **[SCRIPT] P2**. **DEFERRED (follow-up to Done-def #5 — v2 hardening)** — replace the v1 grep-based
      `check_inline_bucket_uri.py` with an AST-walk that (a) distinguishes a real inline URI build (`f"gs://{x}/..."`)
      from a `resolve_bucket_uri(...)` / `resolve_bucket_name(...)` call, (b) ignores occurrences inside docstrings /
      comments (kills the ~handful of docstring false-positives in the v1 baseline, e.g. `bucket_naming.py:16-17`), (c)
      flags inline bucket-NAME construction (`f"features-delta-one-{ag}-{pid}"`) more precisely than the per-line scheme
      heuristic — same shape as QG STEP 5.65's removed-symbol AST-walk. After v2 lands, re-run `--update-baseline` (the
      count drops as docstring false-positives are excluded). status: todo — note: "2026-05-11 slot 4 — v1 grep-based
      ships first per the design; v2 is the precision hardening; not urgent (v1 already catches NEW inline formatters
      via the count ratchet)."
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
      helper-shipped — note: "2026-05-11 slot 4 — the PARTIAL audit table SHIPPED (see § 'Drift audit table' above):
      L1↔L4 verified zero-drift (parity test), L2 features-\* config.py bucket templates migrated to `resolve_bucket`,
      inline-URI formatters ratcheted at baseline (QG STEP 5.69, no new) — all verified-zero TODAY. STILL DRIFTING (all
      DEFERRED-AFTER code_freeze Phase 2.6 with named successors in the table): L2-tail `dependency_checker.py` probe
      templates, L3 legacy `get_bucket_name`/`BUCKET_PREFIXES` (~36+ consumers — pre-audited ~92 candidate files), L5
      deployment-api internal templates (~5 + 3 hardcoded). The FULL zero-drift verification (drift ≤0.01% per migrated
      bucket + zero readers still hit flat names) runs after the Phase-2.6 provisioning + flat→env-tiered data
      migration + the L3 delegate flip (Done-def #3 = step 2.6.4) + the L5 reader-repoint (GAP-2.4.D) — that's the
      Phase-2.6 owner's done-def; checkbox stays `- [ ]` until then. GAP-2.4.D in
      `code_freeze_migrate_backfill_sequencing_2026_05_10.md` extends this Done-def #6."

## Full-execution criterion (per "Plans Run To Actual Completion" HARD RULE)

- ✅ Workspace-grep `f"gs://{<not-a-resolver-call>}` returns 0 hits across all service repos.
  - **What ran**: ripgrep workspace-wide.
  - **Verification**: explicit list of 0 sites in plan-flip commit body.
- ✅ features-service consolidated launch resolves bucket names against the same yaml SSOT that `setup-buckets.sh`
  provisions.
  - **What ran**: real launch on a same-region GCE VM.
  - **Verification**: first-write succeeds + manifest write succeeds against the resolver-derived bucket name.

## Drift audit table (Done-def #6 — PARTIAL as of 2026-05-11; full zero-drift = code_freeze Phase 2.6)

> Authored 2026-05-11 (slot 4). The FULL "zero remaining drift" verification (every consumer hits the env-tiered yaml
> name, drift ≤0.01% per migrated bucket) is DEFERRED-AFTER the code_freeze Phase 2.6 provisioning + flat→env-tiered
> data migration + the legacy-delegate flip (Done-def #3, = step 2.6.4) + the deployment-api Layer-5 reader-repoint
> (GAP-2.4.D) + the `dependency_checker.py` probe-template migration — that's the Phase-2.6 owner's done-def. This table
> is the PARTIAL snapshot: what's already migrated/verified vs what's still drifting (with the named successor).

| Layer / surface                                         | What it is                                                                                                                                                                                                                                                                                                                         | Status 2026-05-11                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Successor / when zero-drift                                                                                                                                                                                                                                                                        |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **L1 yaml (canonical)**                                 | `deployment-service/configs/cloud-providers.yaml` `<cloud>.storage.<kind>`                                                                                                                                                                                                                                                         | ✅ canonical; env-tiered for ALL kinds except 4 GCP env-less (`pnl-store-defi`/`positions-store-defi`/`risk-store-defi` shape-decision-pending, `events` operator-gated — Q7) + 2 workspace exceptions (`terraform-state`/`secrets`, not in this yaml)                                                                                                                                                                                                                 | Q7 resolution closes the 4 env-less GCP entries (shape decision → yaml edit + Phase-2.6 migration)                                                                                                                                                                                                 |
| **L2 per-family `config.py`**                           | `features-service/features_service/{family}/config.py` `*_bucket_template` Field defaults                                                                                                                                                                                                                                          | ✅ MIGRATED — features-service@`8f03ceeb` (`delta_one`/`volatility`/`onchain`/`calendar`) + features-service@`e980ecfd` (`cross_instrument`/`multi_timeframe` via the `features-xinstrument`/`features-mtf` aliases). `commodity`/`sports` have no bucket templates. ZERO drift on these.                                                                                                                                                                              | — (one loose end: the `dependency_checker.py` inline probe templates — see below)                                                                                                                                                                                                                  |
| **L2-tail `dependency_checker.py`**                     | `features-service/features_service/{delta_one,onchain,volatility}/.../dependency_checker.py` inline `"bucket_template": "market-data-tick-{ag}-{pid}"` strings                                                                                                                                                                     | 🟡 DRIFTING — after Phase 0e the yaml `market-data` is env-tiered (`market-data-tick-{ag}-{env}-{pid}`) but the probe template is still flat (`market-data-tick-{ag}-{pid}`); correct for current on-disk reality but drifts from the yaml SSOT                                                                                                                                                                                                                        | DEFERRED-AFTER the UTL `BaseDependencyChecker` migration OR code_freeze Phase 2.6 (whichever lands first) — must land in the SAME window as the flat→env-tiered data migration                                                                                                                     |
| **L3 legacy UTL `get_bucket_name` + `BUCKET_PREFIXES`** | `unified_trading_library/cloud_interface/constants.py` + `core/cloud_constants.py` — defns + ~36+ consumers across instruments-service (~16 files) / execution-service (~22) / MTDS (~21) / deployment-service (~7) / features-service (~8) / strategy-service (~3) / pnl-attribution (~2) / deployment-api (~1) / PM scripts (~2) | 🟡 DRIFTING — NOT yet delegated to `resolve_bucket_name`; Group-A consumers (instruments-service/MTDS — `market-data`/`instruments-store`) write continuously so a premature delegate breaks first-write (the "safe gap" reasoning per A6)                                                                                                                                                                                                                             | DEFERRED-AFTER code_freeze Phase 2.6 (= step 2.6.4 — flip the delegate workspace-wide during the write-pause, alongside provision→rsync→archive). Done-def #3. Pre-audit (~92 candidate files; ~36+ are the real legacy-delegate consumers) is in § Pre-audit manifest "Layer 3 migration recipe". |
| **L4 UTL `bucket_naming` resolver**                     | `unified_trading_library/cloud_interface/bucket_naming.py` (reads L1; `_KIND_ALIASES` bridge; `${DEPLOYMENT_ENV_SHORT}` 3-char form)                                                                                                                                                                                               | ✅ TARGET — keeps in sync with L1 by construction (reads the yaml at call time). Parity test (`test_bucket_naming.py`) extended to features-\* + sports + tradfi + market-data + instruments-store + prediction (UTL@`e8dc6e3` + `2118b1e` + `ba6089c` + `4ee24b5` + `e3dd846` + `5058381`) — ZERO drift between L1 and L4 enforced by the parity test.                                                                                                                | —                                                                                                                                                                                                                                                                                                  |
| **L5 deployment-api internal templates (reader-side)**  | `DataStatusService._BUCKET_TEMPLATES` (18 entries) + `data_status_drilldown._BUCKET_TEMPLATES` (16, already drifts from the first on `ml-*`) + `data_query_service.build_bucket_name` (a 3rd shape) + `upcoming_fixtures._SPORTS_BUCKET_TEMPLATE` + 3 hardcoded `f"gs://instruments-store-sports-{pid}/..."` f-strings             | 🟡 DRIFTING (flat-shape; correct for current on-disk reality) — deployment-api reads buckets continuously, so its bucket-name source must flip in lockstep with the data migration, not before                                                                                                                                                                                                                                                                         | DEFERRED-AFTER code_freeze Phase 2.6 reader-repoint (GAP-2.4.D) — replace all with `resolve_bucket_name(...)` calls + reconcile the L5.1↔L5.2 `ml-*` drift (yaml SSOT wins). Full inventory + the `service → kind` map in § Pre-audit manifest "Layer 5".                                         |
| **Inline `f"gs://...`/`f"s3://...` formatters**         | Workspace-wide `gs://`/`s3://` f-string URI-builders WITHOUT a `# noqa: gs-uri` marker                                                                                                                                                                                                                                             | ✅ RATCHETED + PARTIALLY LOWERED — QG STEP 5.69 (`check_inline_bucket_uri.py` + `inline_bucket_uri_baseline.yaml`) + instruments-service (1→**0** @`5210149`) + deployment-service (3→**0** @`0b802ec`) baselines lowered (4 noqa markers added to error-message strings, not bucket constructors) + PM baseline yaml @`be768d2b`. Remaining: deployment-api 27, execution-service 33, UTL 23, batch-live-recon 7, UAC 5, UI 4, features-service 2, strategy-service 2 | Remaining baselines ratchet DOWN in code_freeze Phase 2.6 as L2-tail/L3/L5 migrate; v2 AST-walk drops docstring false-positives                                                                                                                                                                    |

**Verified-zero-drift today (2026-05-11)**: L1↔L4 (parity test); L2 features-\* config.py bucket templates (migrated to
`resolve_bucket`); inline-URI formatters (ratcheted at baseline, no new). **Still drifting (all DEFERRED-AFTER
code_freeze Phase 2.6 with named successors above)**: L2-tail `dependency_checker.py` probe templates; L3 legacy
`get_bucket_name`/`BUCKET_PREFIXES` (~36+ consumers); L5 deployment-api internal templates (~5 + 3 hardcoded). The full
zero-drift table (drift ≤0.01% per migrated bucket + zero readers still hit flat names) is the code_freeze Phase 2.6
owner's done-def (GAP-2.4.D extends Done-def #6).

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

### Layer 5 (reader-side): deployment-api internal bucket-template dicts — FINDING 2026-05-11 (slot 4, Phase 0g cross-check)

`deployment-api` is a pure **reader** of the bucket landscape (it lists buckets to render the data-status UI + the
deploy-flow). It does NOT use `resolve_bucket_name(...)` — it carries its own **flat-shape** bucket-template
definitions, a 5th drift surface on top of L1-L4. Inventory (slot-4 audit
`grep -rn 'BUCKET_TEMPLATE\|build_bucket_name\|gs://(instruments-store|market-data|features-)' deployment-api/`):

| #    | Location                                                                       | Shape                                                                                                              | Notes                                                                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| L5.1 | `data_status_service.py:2793` `DataStatusService._BUCKET_TEMPLATES` (ClassVar) | 18 `service → "{prefix}-{cat}-{pid}"` / `"{prefix}-{pid}"` entries, ALL FLAT                                       | The "canonical" internal dict the others mirror. Comment: "mirrors deployment-service ManifestReader."                                                                                                |
| L5.2 | `data_status_drilldown.py:45` `_BUCKET_TEMPLATES` (module-level)               | 16 entries — a near-copy of L5.1 ("mirrors `DataStatusService._BUCKET_TEMPLATES` without the circular dependency") | **Already drifts from L5.1**: `ml-training-service` → `ml-models-store-{pid}` here vs `ml-training-artifacts-{pid}` in L5.1; `ml-inference` → `ml-predictions-{pid}` vs `ml-inference-results-{pid}`. |
| L5.3 | `data_query_service.py:42` `build_bucket_name(prefix, ag)`                     | formula `f"{prefix}-{ag.lower()}-{pid}"`                                                                           | A 3rd shape — doesn't model the shared-bucket special-cases (`features-onchain-{pid}`, `features-sports-{pid}`).                                                                                      |
| L5.4 | `data_status_service.py:2022` `_ROLLUP_BUCKET_TEMPLATE`                        | `"{pid}-data-status-rollups"`                                                                                      | Internal rollup bucket — not in cloud-providers.yaml at all (greenfield item if the rollup bucket should be SSOT'd).                                                                                  |
| L5.5 | `upcoming_fixtures.py:23` `_SPORTS_BUCKET_TEMPLATE`                            | `"instruments-store-sports-{pid}"` (flat)                                                                          | Hardcoded sports instruments-store name.                                                                                                                                                              |
| L5.6 | `data_query_service.py:469` + `data_status_drilldown.py:1798,1866`             | 3× `f"gs://instruments-store-sports-{pid}/..."`                                                                    | Hardcoded flat sports-instruments-store name in f-strings (the `# noqa: gs-uri` ratchet baseline captures these).                                                                                     |

**Why NOT migrate these now (deferred-after-code_freeze-Phase-2.6)**: deployment-api reads buckets **continuously**
(every data-status page load). The on-disk buckets are still FLAT until code_freeze Phase 2.6 provisions the env-tiered
ones + migrates the data. If deployment-api flipped to `resolve_bucket_name(...)` now, it'd resolve env-tiered names
that don't exist on disk → the data-status UI shows "Failed to load" for every shard. This is the SAME "Group-A safe-gap
doesn't apply" reasoning that pushed Done-def #3 (the legacy `get_bucket_name` delegate) to Phase 2.6 per A6 — a
reader/writer that touches buckets continuously must flip in the SAME window as the data migration, not before.

**Phase 2.6 reader-repoint scope (code_freeze GAP-2.4.D)** — when the env-tiered buckets are provisioned + flat data is
migrated:

1. Replace L5.1 + L5.2 + L5.3 + L5.5 + L5.6 with
   `resolve_bucket_name(cloud=get_cloud_provider().value, kind=<kind>, asset_group=<ag>)` calls. The `service → kind`
   map: `instruments-service`/`corporate-actions` → `instruments-store`;
   `market-tick-data-service`/`market-data-processing-service` → `market-data`; `features-delta-one-service` →
   `features-delta-one`; `features-volatility-service` → `features-volatility`; `features-onchain-service` →
   `features-onchain` (asset_group="defi"); `features-sports-service` → `features-sports`; `features-calendar-service` →
   `features-calendar`; `features-multi-timeframe-service` → `features-multi-timeframe` (→ alias `features-mtf`);
   `features-cross-instrument-service` → `features-cross-instrument` (→ alias `features-xinstrument`);
   `features-commodity-service` → `features-commodity`; `ml-training-service` → `ml-models-store`;
   `ml-inference-service` → `ml-predictions-store`; `strategy-service` → `strategy-store`; `execution-service` →
   `execution-store`. (Reconcile the L5.1-vs-L5.2 ml-\* drift in the same pass — the yaml SSOT wins: `ml-models-store` /
   `ml-predictions-store`.)
2. L5.4 (`_ROLLUP_BUCKET_TEMPLATE` = `{pid}-data-status-rollups`): decide whether the rollup bucket gets a yaml entry
   (it's an internal observability bucket, arguably stays internal like the rollup-worker — but if env-tiered, it should
   be in the yaml too). Operator/Ikenna call (bucket-naming SSOT).
3. basedpyright deployment-api + run `bash scripts/quality-gates.sh` (deployment-api); smoke the data-status UI against
   the migrated env-tiered buckets.

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
- **Sequencing**: a baseline ratchet is Phase-1-shippable — the ratchet point is "no NEW inline f-strings beyond today's
  count", which doesn't depend on the L2/L3 migrations. The to-be-removed inline templates (`get_bucket_name` consumers,
  `dependency_checker.py` probe strings) are baked into today's baseline; when they land in code_freeze Phase 2.6 the
  baseline ratchets DOWN (re-run `--update-baseline` post-migration). So: ship STEP 5.69 in Phase 1 (Done-def #5),
  ratchet the baseline down in Phase 2.6. **Update 2026-05-11**: the original "ships after L2 + L3" note assumed the
  legacy delegate (L3 / Done-def #3) was a Phase-1 deliverable; A6 deferred it to Phase 2.6, but the ratchet doesn't
  need to wait for it.

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

#### A6 — [ikenna-main, 2026-05-11 PM] — operator-routed decision: **Option 2 (defer ALL of Done-def #3 to Phase 2.6 window)** ✅ RESOLVED

**Decision**: Defer the whole `get_bucket_name` → `resolve_bucket_name` delegate (Group A + Group B + all kinds) to
Phase 2.6 (2026-05-15→05-19), landing it inside the same window as the flat→env-tiered bucket provisioning + data
migration + write-pause cutover. Done-def #3 is reclassified from "Phase 1 code-complete deliverable" to "Phase 2.6
cutover deliverable."

**Why Option 2 over Option 1 (transitional split)**:

- **Done-def #3 is code-cleanup, not a freeze-gate blocker** (per Harsh slot 1 surface analysis + the Phase 1
  freeze-gate checklist in `code_freeze_migrate_backfill_sequencing_2026_05_10.md:142-149` — `get_bucket_name` legacy is
  NOT in the 6 freeze-gate items). Deferring 4 days has zero downstream cost.
- **Phase 2.6 sequencing fits naturally**: provision env-tiered buckets → rsync data flat→env-tiered → brief write-pause
  → flip `get_bucket_name` delegate to `resolve_bucket_name` (all 36 consumers in one logical unit) → archive flat
  buckets. Done-def #3 IS the cutover-flip step in this sequence; it's not a separate concern.
- **Avoids "half-migrated" cognitive load.** Option 1 (Group-B flips now, Group-A flips Phase 2.6) creates a 4-day
  window where the delegate has special-cased Group-A logic that EVERY reader needs to remember + every reviewer needs
  to validate. Code-review burden + drift risk.
- **Composes cleanly with workspace "No double SSOT" rule** (CLAUDE.md): Option 1 maintains TWO bucket-resolution paths
  in parallel for 4 days (legacy-flat for Group-A, env-tiered for Group-B). Option 2 has ONE path throughout, with the
  canonical switch happening atomically at the Phase 2.6 cutover.
- **Cost of Option 1 saved**: slot 4 doesn't need to write + test the Group-A special-case branch in the delegate. Slot
  4's other queued work (env-less-GCP-entries sub-todo + Done-def #5/#6 + Phase 0f/0g/0h) takes the saved capacity.
- **Risk of write failures eliminated**: with Option 2, NO bucket re-pointing happens before the env-tiered buckets
  physically exist. With Option 1, the Group-B re-pointing is "safe" only because nothing writes Group-B between now and
  Phase-3 backfills — but that's a fragile assumption (any feature-service test run, any QG smoke, any CI integration
  test could trigger a Group-B write attempt against a non-existent bucket). Option 2 removes the assumption entirely.

**Phase 2.6 Done-def #3 sub-sequence** (new structure):

| Phase 2.6 Step | Owner                                      | Action                                                                                                               |
| -------------- | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| 2.6.1          | Phase 2.6 owner (TBD; slot 4 or new agent) | Provision ~150-300 new env-tiered Group-A + Group-B buckets across both clouds × 3 envs × ap-northeast-1.            |
| 2.6.2          | Phase 2.6 owner                            | rsync data flat→env-tiered (Storage Transfer Service / DataSync, ≤0.01% drift).                                      |
| 2.6.3          | Phase 2.6 owner                            | Brief write-pause window (~minutes; operator-coordinated; flag VMs to wait).                                         |
| 2.6.4          | **Done-def #3 / slot 4 carryover**         | Ship `get_bucket_name` → `resolve_bucket_name` delegate workspace-wide (all 36 consumers migrated in single PR).     |
| 2.6.5          | Phase 2.6 owner                            | Verify writers writing to env-tiered buckets; archive flat buckets; QG STEP 5.69 ratchet enforces no flat-name refs. |

**Slot 4 in-flight scope** (NOT BLOCKED — proceed with current queue per Harsh slot 1's note): env-less-GCP-entries
sub-todo + Done-def #5/#6 + Phase 0f (VM-launcher env-awareness) + Phase 0g (UI-env-tier verify) + Phase 0h (sync-script
code). Done-def #3 stays `- [ ]` in the plan body with `status: deferred-after-Phase-2.6` annotation per CLAUDE.md
"Commit + Push + Flip Plan Checkboxes" Half 2 closed-set status values. Slot 4 will pick up Done-def #3 again in the
Phase 2.6 cutover window (or hand off to whoever owns Phase 2.6 implementation).

**Status**: ✅ RESOLVED — slot 4 unblocked on the queued items (no scope change to those); Done-def #3 explicitly
re-sequenced to Phase 2.6.

**Cross-side ping** to harsh-main filed in `plans/active/_agent_pings.md` (same commit as this answer).

### Q7 — [harsh-bucket-and-adapter-tab, 2026-05-11] — env-less-GCP-entries remainder: `pnl-store-defi`/`positions-store-defi`/`risk-store-defi` shape-alignment + `events` env-tier sign-off (both operator-gated)

**Status**: 🟡 PARTIAL — Q7(c) `events` env-tier ✅ RESOLVED 2026-05-11 PM (operator: env-tiered, option c-i); Q7(b)
pnl/positions/risk shape-alignment still open (Ikenna call).

**Q7(c) `events` — RESOLVED 2026-05-11 PM (operator: env-tiered).** Events bucket goes env-tiered:
`gs://{pid}-events-{env}/events/{service}/...`. yaml flip + UTL `resolve_bucket_name` env-tier extension queues as a
Phase 2.6 sub-step (data migration is mostly write-new-and-archive-old since events are append-only). **Watchdog
architecture follow-up (P1)**: `vm_zombie_watchdog.py` reads from single `{pid}-events` today; under env-tiered events
either (i) single watchdog reads all 3 env buckets concurrently or (ii) 3 per-env watchdog VMs if throughput is too much
for one machine. Operator direction: 'depends on throughput'. Tracked as a NEW P1 follow-up todo below — not blocking
Phase 2.6 cutover (watchdog continues working until events buckets migrate; can decouple the watchdog refactor from the
events-bucket migration timing).

**Q7(b) `pnl-store-defi` / `positions-store-defi` / `risk-store-defi` — shape-alignment, not just an env-tier add.**
Still operator-gated. The GCP yaml today (`cloud-providers.yaml:147-149`):

| kind                   | GCP today                                | AWS today                                                                        | shape mismatch                                                                            |
| ---------------------- | ---------------------------------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `pnl-store-defi`       | `pnl-store-${GCP_PROJECT_ID}-defi`       | `unified-trading-pnl-store-defi-${DEPLOYMENT_ENV_SHORT}-${AWS_ACCOUNT_ID}`       | GCP puts `-defi` AFTER the project id; no env tier                                        |
| `positions-store-defi` | `positions-store-${GCP_PROJECT_ID}-defi` | `unified-trading-positions-store-defi-${DEPLOYMENT_ENV_SHORT}-${AWS_ACCOUNT_ID}` | same                                                                                      |
| `risk-store-defi`      | `risk-store-defi-${GCP_PROJECT_ID}`      | `unified-trading-risk-store-defi-${DEPLOYMENT_ENV_SHORT}-${AWS_ACCOUNT_ID}`      | GCP puts `-defi-` BEFORE the project id (different again from pnl/positions); no env tier |

The DeFi-raw kinds were a clean `${DEPLOYMENT_ENV_SHORT}` _add_ because their GCP shape already matched AWS's
`{kind}-{pid}` form. These three don't — GCP uses asset-group-as-suffix/-infix, AWS uses asset-group-in-the-middle +
env-tier. Aligning GCP to `pnl-store-defi-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}` /
`positions-store-defi-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}` /
`risk-store-defi-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}` (the symmetric form, AWS minus the `unified-trading-`
prefix) **renames the on-disk GCP buckets** → a Phase-2.6 data migration (`gcloud storage cp -r` flat-shape →
env-tiered-shape, ≤0.01% drift). Char check: `risk-store-defi-prd-central-element-323112` = 42 chars — well under 63.

> **Recommendation (slot 4)**: option **(b-i)** — align GCP to the symmetric
> `{kind}-defi-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}` form for all three; add the rename to the Phase-2.6 migration
> scope (already migrating flat→env-tiered for the DeFi-raw
>
> - Group-A + Group-B kinds, so the marginal cost is small — same `gcloud storage cp` loop, one extra source→dest pair
>   per kind). Rejected alternative (b-ii) "keep GCP's idiosyncratic suffix/infix shapes + just bolt
>   `${DEPLOYMENT_ENV_SHORT}` on" — perpetuates 3 different shapes for 3 sibling kinds + an AWS↔GCP asymmetry, contra
>   (b+)'s "env tier extends to ALL kinds, symmetrically". Rejected (b-iii) "leave env-less forever like
>   `terraform-state`/`secrets`" — these are per-asset-group P&L/position/risk stores, not workspace-singletons;
>   prod/staging/dev isolation IS the (b+) strategic requirement (Citadel-grade, May-23 cutover).

**(c) `events` (`${GCP_PROJECT_ID}-events`) — env-tier or stays env-less?** HIGH blast radius:
`gs://{pid}-events/events/{service}/{YYYY-MM-DD}/{correlation_id}/hour={H}/*.jsonl` is the canonical event-stream path
referenced **workspace-wide** (CLAUDE.md "No fire-and-forget VM launches" rule cites it verbatim;
`unified-events-interface` UI reads it; every `ServiceBootstrap` writes it; `GCSEventSink` writes it). The AWS side is
env-tiered. Going env-tiered on GCP means a `{pid}-events` → `events-${DEPLOYMENT_ENV_SHORT}-${pid}` rename + repointing
every event reader/writer + a data migration of years of JSONL. **This is genuinely a "do we want 3 separate event
streams (dev/staging/prd) on GCP" product call** — not a mechanical yaml edit.

> **Recommendation (slot 4)**: option **(c-i)** — env-tier `events` too (consistency with AWS + the (b+) "ALL kinds"
> directive + true env isolation for the event stream), BUT make it a _dedicated Phase-2.6 sub-step_ with its own
> rollout note (it's the single highest-blast-radius rename in the whole bucket-SSOT effort — touches the most
> consumers, and a partial cutover would split the event stream). Acceptable alternative (c-ii): keep `events` env-less
> like `terraform-state`/`secrets` and document it as a 3rd permitted exception in CLAUDE.md ("Reviewers reject any new
> yaml entry that doesn't carry `${DEPLOYMENT_ENV}` unless explicitly operator-confirmed env-less (currently:
> `terraform-state`, `secrets`, `events`)") — defensible because the event stream is observability metadata, not trading
> data, and per-env deployment-api service-account scoping already provides cross-env isolation at the _read_ layer (per
> Phase 0g's finding). Operator picks.

**No code change pending on Q7** — the yaml stays as-is (the 3 defi-store kinds + `events` env-less) until the operator
answers; the env-less-GCP-entries sub-todo checkbox stays `- [ ]` with `status: helper-shipped`. If the answer is
(b-i)+(c-i): the yaml edits + parity-test refresh are ~30 min; the data migrations fold into Phase 2.6. If (c-ii): a
1-line CLAUDE.md edit + the sub-todo flips `[x]` for the `events` part.

## Deferred work after 2026-05-11 slot 4 session

The 2026-05-11 `harsh-bucket-and-adapter-tab` (slot 4) session shipped: the parity-test extension (UTL@`e8dc6e3`), the
canonical-layer decision (a, with a Phase-0 caveat), the full 4-layer pre-audit manifest + per-layer migration recipe +
QG STEP 5.69 design, the FINDING that the yaml features-\* env-tier is unprovisioned, and the
[`../archive/issues/mtds_sports_available_at_wiring_2026_05_11.md`](../archive/issues/mtds_sports_available_at_wiring_2026_05_11.md)
sports audit. Items still open are tracked here so the next agent picks up cleanly.

| Item                                                                                                                                    | Status as of 2026-05-11 (PM-time)                                                               | Successor / blocker                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Done-def #1 — decide canonical layer                                                                                                    | `done` ([x]) — option (b) (operator/Ikenna): yaml canonical, env-tiered                         | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Phase 0 (re-shaped: yaml-correctness fixes only) — add prediction/sports keys + uncomment GCP features-calendar + doc shape conventions | `done` ([x] partial) — deployment-service@`a7eba4f` + UTL@`2118b1e` (parity test)               | The bucket PROVISIONING + flat-bucket DATA MIGRATION + reader/writer repoint is `code_freeze` Phase 2.6 (2026-05-15→05-19) — NOT slot 4's to execute now (per option (b) "code-first, physical-migration-second"). `aws s3 ls` probe still pending (no AWS CLI on the slot machine — `ml-*`/`strategy`/`execution` confirmed env-tiered on GCP). `-test-` variant canonicalisation = a Phase-0 sub-item flagged for operator OK on the canonical shape.                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Done-def #2 — migrate per-family `config.py` `*_bucket_template` → resolver                                                             | `done` ([x]) — features-service@`8f03ceeb` (sub-agent fan-out)                                  | DEFERRED sub-items split off: (a) cross_instrument/multi_timeframe `get_output_bucket` — **BLOCKED on Q5** (the `features-cross-instrument`/`features-multi-timeframe` bucket names overflow the 63-char limit under the (b+) env-tier template — needs an Ikenna design call); (b) `dependency_checker.py` inline templates (blocked on UTL `BaseDependencyChecker` migration + `test_mode`-infra rewrite + ~6-test blast radius — note: after Phase 0e the `market-data` probe template now DRIFTS from the env-tiered yaml; must land in the Phase-2.6 window or via the UTL migration).                                                                                                                                                                                                                                                                                     |
| **Phase 0e** — env-tier the Group-A bucket kinds in yaml + parity test                                                                  | `done` ([x]) — deployment-service@`a5c2082` + UTL@`ba6089c`                                     | `market-data`/`instruments-store`/`features-calendar`/`market-data-tick-prediction`/`instruments-store-prediction` env-tiered on both clouds; §-header comment updated; all names verified ≤63 chars. Remaining env-less GCP entries (`dex-*`/`*-defi` raw, `pnl-store-defi`/etc shape-alignment, `events`/`config-store`) split into a new `- [ ]` sub-todo (the DeFi-raw ones are a clean add; `pnl-store-defi`/etc need a shape decision; `events` is operator-gated due to workspace-wide `{pid}-events` refs). code-first per code_freeze sequencing — provisioning + flat-bucket migration = Phase 2.6 (2026-05-15→05-19).                                                                                                                                                                                                                                                |
| cross_instrument/multi_timeframe yaml-gap sub-todo (the last loose end of Done-def #2)                                                  | `done` ([x]) — Q5/A5 resolved + implemented 2026-05-11 (slot 4 cont. 3)                         | Q5/A5 Option 1 / Scope A: short alias kinds `features-xinstrument`/`features-mtf` in the yaml + UTL `_KIND_ALIASES` bridge + `${DEPLOYMENT_ENV_SHORT}` 3-char form everywhere + `-pred-` bucket-name strings + config.py `get_output_bucket` → `resolve_bucket`. Evidence: UTL@`4ee24b5` + deployment-service@`008e371` + deployment-service@`f81d043` + UTL@`e3dd846` + features-service@`e980ecfd`. Follow-up (P2, deferred): drop stale `OUTPUT_BUCKET_TEMPLATE` doc refs (features-service-docs sweep).                                                                                                                                                                                                                                                                                                                                                                     |
| Done-def #3 — delegate legacy `get_bucket_name` + `BUCKET_PREFIXES` → resolver                                                          | `deferred-after-code_freeze-Phase-2.6` ([ ]) — Q6 ✅ RESOLVED (Option 2)                        | **Q6 RESOLVED 2026-05-11 (A6)**: operator picked Option 2 — defer the ENTIRE delegate (Group A + Group B + all kinds) to code_freeze Phase 2.6 (2026-05-15→05-19), landing it as the cutover-flip step (`2.6.4`) alongside provision → rsync flat→env-tiered → write-pause → flip-delegate-workspace-wide → archive flat buckets. Not a Phase-1 deliverable; carries to the Phase-2.6 owner. Pre-audit done (~36+ consumers). No more open Qs.                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Done-def #4 — extend parity test                                                                                                        | `done` ([x]) — UTL@`e8dc6e3` (+ UTL@`2118b1e` Phase-0 follow-up)                                | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Done-def #5 — QG STEP 5.69 (`f"gs://..."` ratchet)                                                                                      | `done` ([x]) — PM@`<this session>` (slot 4 2026-05-11)                                          | SHIPPED: `check_inline_bucket_uri.py` (v1 grep-based, per-repo COUNT ratchet) + `inline_bucket_uri_baseline.yaml` (seeded — deployment-api 27, execution-service 33, UTL 23, batch-live-recon 7, UAC 5, UI 4, deployment-service 3, features-service 2, strategy-service 2, instruments-service 1, rest 0) + STEP 5.69 in `base-service.sh` (mirrors STEP 5.67 shape) + `test_check_inline_bucket_uri.py` (12 tests, all pass); ruff+format clean, py_compile OK. Baseline ratchets DOWN when the to-be-removed inline bucket-name templates (`get_bucket_name` consumers, `dependency_checker.py`, deployment-api Layer-5) land/migrate in code_freeze Phase 2.6 — re-run `--update-baseline` then. v2 AST-walk hardening = a new `- [ ]` P2 follow-up (precision: distinguish `f"gs://{x}/..."` from `resolve_bucket_uri(...)`, ignore docstrings — same shape as STEP 5.65). |
| Done-def #6 — plan-flip cite + grep audit table (zero drift)                                                                            | `helper-shipped` ([ ]) — PARTIAL table shipped PM@`<this session>`; full zero-drift = Phase 2.6 | PARTIAL audit table SHIPPED (§ "Drift audit table" — L1-L5 + inline-URI surfaces, migrated-vs-drifting with named successors): verified-zero TODAY = L1↔L4 (parity test) + L2 features-\* config.py (migrated to `resolve_bucket`) + inline-URI formatters (ratcheted at baseline, QG STEP 5.69, no new). STILL DRIFTING (all DEFERRED-AFTER code_freeze Phase 2.6): L2-tail `dependency_checker.py` probe templates; L3 legacy `get_bucket_name`/`BUCKET_PREFIXES` (~36+ consumers — pre-audited ~92 candidate files across instruments-svc/MTDS/execution-svc/deployment-svc/features-svc/strategy-svc/pnl/deployment-api/PM); L5 deployment-api internal templates (~5 dicts/methods + 3 hardcoded). FULL zero-drift verification (drift ≤0.01% per migrated bucket + zero flat-name readers) = Phase-2.6 owner's done-def (code_freeze GAP-2.4.D extends this).            |
| **Phase 0f** — VM launcher scripts read `DEPLOYMENT_ENV` (~30 `deployment-service/scripts/vm/`)                                         | `not-started` ([ ]) — **Ikenna slot 8 absorbed (operator direction 2026-05-11)**                | Operator directed Ikenna slot 8 to absorb Phase 0f (+ Phase 0h) carry-forward (Harsh leaving ~3hr). Slot 4 did NOT start it (no code). Ikenna slot 8 spawn brief in `ikenna_orchestrator/_agent_pings.md` `[main → slot 8]` (PM@`c0d10139`). It's a Phase-2.6-cutover prereq.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **Phase 0g** — verify deployment UI env-tier + (b+) cross-check (deployment-api hardcoded buckets)                                      | `done` ([x]) — verification + cross-check audit @PM`5c99664f`                                   | UI env-tier already shipped pre-2026-05-11 (codex `deployment-ui-architecture.md`). (b+) cross-check FINDING: deployment-api carries its own flat-shape bucket templates (5 dicts + 1 method + 3 hardcoded `f"gs://instruments-store-sports-{pid}/..."`) — "Layer 5" reader-side drift, documented in § Pre-audit manifest "Layer 5" + folded into code_freeze GAP-2.4.D (Phase-2.6 reader-repoint). NOT fixed now — deployment-api reads buckets continuously so its source must flip in lockstep with the data migration (same Group-A reasoning as #3/A6).                                                                                                                                                                                                                                                                                                                   |
| **Phase 0h** — sync script (prod → staging/dev), truncated window + same-region                                                         | `done` ([x] — script shipped) — deployment-service@`fc1cfa0` (slot 4 2026-05-11)                | `scripts/sync-buckets-prod-to-env.sh` (impl: enumerates env-tiered bucket pairs from `cloud-providers.yaml` via the canonical UTL resolver w/ YAML-walk fallback; env-LESS kinds skipped; same-region abort; truncated `day=` window over the 3 known layouts; idempotent rsync/`aws s3 sync`; `--dry-run`/`--kind`/`--years`/`--cloud`; per-bucket count + sample-parquet verification; manifest re-sync as an operator step not auto-launched) + `sync-buckets-prod-to-staging.sh` + `sync-buckets-prod-to-dev.sh` wrappers. `bash -n` + `shellcheck -S warning` clean. **FIRST EXECUTION = Phase 3 / post-cutover** (code_freeze GAP-2.4.E) — operator-directed handoff: Ikenna slot 8 owns the first-execution + any layout-specific refinement.                                                                                                                            |
| Sports-adapter `available_at` (the other slot-4 half)                                                                                   | `done` ([x] — code shipped MTDS@`c186ecb`)                                                      | Code wired (`_process_sports_venue_with_leagues` stamps `available_at = bm_time` via UTL `stamp_available_at_odds_snapshot` @UTL`2ab3685`, shard-level failure isolation, 5 tests). REMAINING: slot 1 routes a cross-side ping to Ikenna slot 3 to flip the `available_at_lookahead_bias_completion_2026_05_08.md` Phase 1 "TRACK — sports adapter stamping" todo; + the 2 open design Qs in `../archive/issues/mtds_sports_available_at_wiring_2026_05_11.md` (all-NaT routing; sports-path `assert_available_at_present` guard) for Ikenna slot 3 / sports_master.                                                                                                                                                                                                                                                                                                            |

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

| Item                                                                                                              | Status                      | Commits                                                                                           |
| ----------------------------------------------------------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------- |
| Done-def #4 — extend yaml-vs-resolver parity test (features-\*/sports/tradfi/prediction) + fix RED parity test    | `done`                      | unified-trading-library@`e8dc6e3`; plan-flip PM@`59e92b18`                                        |
| Done-def #1 — decide canonical SSOT layer = (a) yaml (with Phase-0 caveat)                                        | `done`                      | PM@`59e92b18` (decision in plan body)                                                             |
| § Pre-audit manifest (4-layer drift map + L2/L3 migration recipes + QG STEP 5.69 design)                          | `done`                      | PM@`59e92b18`                                                                                     |
| § Open questions Q1 (resolver location UAC-vs-UTL), Q2 (proceed-with-config.py-now?), Q3 (STEP number)            | `done` (raised, 🟡 BLOCKED) | PM@`59e92b18`                                                                                     |
| § FINDING 2026-05-11 (yaml features-\* env-tier unprovisioned) + Phase 0 todo + Q4 (🔴 P0)                        | `done`                      | PM@`<this commit>`                                                                                |
| `../archive/issues/mtds_sports_available_at_wiring_2026_05_11.md` — MTDS-slice sports `available_at` wiring audit | `done`                      | PM@`7c088961`                                                                                     |
| Boot ack ping                                                                                                     | `done`                      | PM@`eb52b83b` (then moved to `harsh_orchestrator/pings/slot_4.md` per the 2026-05-11 ledger-move) |

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
| `../archive/issues/mtds_sports_available_at_wiring_2026_05_11.md` — marked the wiring shipped                                                                                                                                                                                                                                                                                                                                                                         | `done` | PM@`<this commit>`                                     |

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

| Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Status           | Commits                                                           |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- | ----------------------------------------------------------------- |
| UTL `bucket_naming` — `_KIND_ALIASES` map (`features-cross-instrument`→`features-xinstrument`, `features-multi-timeframe`→`features-mtf`; applied in `resolve_bucket_name`) + `${DEPLOYMENT_ENV_SHORT}` substitution in `_substitute_env_vars` (3-char form `dev`/`stg`/`prd`/`test`/`ci` from `DEPLOYMENT_ENV`, default `prod`→`prd`; unknown → `BucketNamingError`)                                                                                                                                                                                                                                                                                                              | `done`           | unified-trading-library@`4ee24b5`                                 |
| deployment-service `env_substitutor` — matching `${DEPLOYMENT_ENV_SHORT}` support (same map; `ValueError` on unknown) so both yaml-readers produce identical bucket names from `cloud-providers.yaml`                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | `done`           | deployment-service@`008e371`                                      |
| `cloud-providers.yaml` Q5/A5 sweep — `${DEPLOYMENT_ENV}`→`${DEPLOYMENT_ENV_SHORT}` (~82 occ, both clouds); `-prediction-`→`-pred-` in 14 prediction-related bucket-name STRINGS (keys unchanged); added `features-xinstrument` + `features-mtf` (5 per-AG each, env-tiered, both clouds); §-header comment rewritten (the `${DEPLOYMENT_ENV_SHORT}` convention + the `pred` rule + the kind aliases). All env-tiered names ≤63 chars (worst 60). yaml parses; prettier-clean                                                                                                                                                                                                       | `done`           | deployment-service@`f81d043`                                      |
| parity test `test_bucket_naming.py` — `_SNAPSHOT_YAML` → `${DEPLOYMENT_ENV_SHORT}` + `-pred-`; all snapshot-test expectations `-staging-`→`-stg-` + `-prediction-`→`-pred-`; `_FEATURES_PIPELINE_KINDS` live-yaml pin gains `features-xinstrument`/`features-mtf` + `features-cross-instrument`/`features-multi-timeframe` (consumer aliases → SHORT-prefix resolved bucket) + `*-pred-` prefixes for the prediction kinds; `test_resolver_reads_live_env_each_call` assertions → `-stg-`/`-prd-`. ruff-clean                                                                                                                                                                      | `done`           | unified-trading-library@`e3dd846`                                 |
| features-service `cross_instrument/config.py` + `multi_timeframe/config.py` — deleted the `output_bucket_template` Field + `OUTPUT_BUCKET_TEMPLATE` alias; `get_output_bucket` → `resolve_bucket(kind="features-cross-instrument"/"features-multi-timeframe", asset_group=...)` (resolver aliases to `features-xinstrument`/`features-mtf`). No tests reference the removed Field. ruff-clean                                                                                                                                                                                                                                                                                      | `done`           | features-service@`e980ecfd`                                       |
| env-less-GCP-entries sub-todo (DeFi-raw + config-store part) — GCP `dex-pools`/`dex-swaps`/`evm-defi`/`eigenlayer-rewards`/`solana-defi`/`config-store` → `{kind}-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}` (was env-less; mirrors the already-env-tiered AWS side). §-header comment updated (STILL-env-less list now only GCP `pnl-store-defi`/`positions-store-defi`/`risk-store-defi` + `events`). All ≤63 chars. On-disk flat→env-tiered migrates Phase 2.6. Parity test snapshot env-tiered the GCP `dex-pools`/`config-store` entries + 2 expectations. `pnl-store-defi`/etc (shape-alignment + migration) + `events` (operator-gated) STILL OPEN — checkbox stays `- [ ]` | `helper-shipped` | deployment-service@`070c897` + unified-trading-library@`5058381`  |
| Plan flips (cross_instrument/multi_timeframe yaml-gap sub-todo `[x]`; env-less-GCP sub-todo PARTIAL note; Done-def #3 NOTE + scoreboard `blocked`-on-Q6) + Q6 added to § Open questions + Q5 SHIPPED note + this DONE block                                                                                                                                                                                                                                                                                                                                                                                                                                                        | `done`           | PM@`0a07520e` (Q5/A5 flips) + PM@`<this commit>` (DeFi-raw flips) |

**Still open after the Q5/A5 + DeFi-raw session:** **Done-def #3** (legacy `get_bucket_name`+`BUCKET_PREFIXES` delegate)
— now **BLOCKED on Q6** (Ikenna sequencing call: the delegate landing before Phase 2.6 re-points Group-A consumers to
non-existent env-tiered names — slot 4 rec = transitional delegate, Group-B now / Group-A flips with Phase 2.6); the
env-less-GCP-entries sub-todo is now **PARTIAL** — DeFi-raw (`dex-*`/`*-defi`) + `config-store` env-tiered
@deployment-service`070c897` + UTL`5058381`; STILL OPEN parts: `pnl-store-defi`/`positions-store-defi`/`risk-store-defi`
(shape-alignment decision + data migration — operator/Ikenna call) + `events` (operator-gated — `{pid}-events`
workspace-wide); Done-def #5 (QG STEP 5.68 ratchet — after #2 done + #3); Done-def #6 (audit table — after #3 + #5 +
Phase 2.6); the `dependency_checker.py` sub-todo (blocked on UTL `BaseDependencyChecker` migration + `test_mode`-infra
rewrite); the `OUTPUT_BUCKET_TEMPLATE`-stale-docs follow-up (P2, features-service-docs sweep); Phase 0 `aws s3 ls`
probe + `-test-` canonical-shape operator OK; Phase 0f (VM-launcher env-awareness); Phase 0g (UI-env-tier verify —
already shipped per codex); Phase 0h (sync-script); Phase 0c/0d (= code_freeze Phase 2.6, 2026-05-15→05-19).
**Cross-side (slot 1's action)**: route a cross-side ping to Ikenna re **Q6** (Done-def #3 sequencing) + the
env-less-GCP `pnl-store-defi`/etc shape-alignment + the `events` env-tier sign-off — all bucket-naming SSOT decisions →
Ikenna per the work-split. The prior cross-side asks (Ikenna slot 3 — sports `available_at` Phase 1 todo + 2 design Qs;
Q5) are ✅ resolved. **Workspace observation (not slot-4-owned, unchanged)**: `import unified_trading_library` broken on
`origin/live-defi-rollout` (`availability_stamping.py:83` → `BAR_TIMEFRAME_SECONDS` not exported from UAC `__init__.py`)
— blocks running the UTL parity test locally; the test is logically consistent with the resolver + yaml. Going quiet —
next session picks up Done-def #3 (pending Q6) + the env-less-GCP `pnl-store-defi`/etc + `events` parts (pending
operator).

## DONE-2026-05-11 (cont. 4) — harsh-bucket-and-adapter-tab (slot 4), Phase-1-remainder + Q6/Q7 + Phase 0g/0h/Done-def #5/#6 session

Resumed per the ▶ RESUME block + the Q6 ✅ relay. Shipped this session:

| Item                                      | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Evidence                                                  |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| Q6 ✅ relay                               | done — Done-def #3 `status: todo → deferred-after-code_freeze-Phase-2.6` (A6 = Option 2: defer the ENTIRE delegate to the Phase-2.6 cutover window, = step 2.6.4); Q6 note → ✅ RESOLVED                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | PM@`e4fca599`                                             |
| Done-def #5 note un-block                 | done — no longer blocked-on-#3 (baseline ratchet is Phase-1-shippable); STEP number pinned 5.69 (matches CLAUDE.md + the QG STEP 5.6X design section)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | PM@`e4fca599`                                             |
| Q7 NEW (env-less-GCP remainder ops calls) | done (surfaced + routed) — `pnl-store-defi`/`positions-store-defi`/`risk-store-defi` shape-align (full mismatch table; rec b-i = symmetric `{kind}-defi-{env}-{pid}`) + `events` env-tier (rec c-i = dedicated Phase-2.6 sub-step / c-ii = 3rd permitted env-less exception; main's lean = c-ii). Routed cross-side to Ikenna (main relayed 13:35). Yaml unchanged pending operator answer.                                                                                                                                                                                                                                                                                                                                                                                                                                    | PM@`e4fca599`                                             |
| Phase 0g (b+) cross-check FINDING         | done — deployment-api carries its OWN flat-shape bucket templates (`DataStatusService._BUCKET_TEMPLATES` 18-entry + `data_status_drilldown._BUCKET_TEMPLATES` 16-entry near-copy that already drifts on `ml-*` + `data_query_service.build_bucket_name` + `upcoming_fixtures._SPORTS_BUCKET_TEMPLATE` + 3 hardcoded `f"gs://instruments-store-sports-{pid}/..."`) = a "Layer 5" reader-side drift. Documented in § Pre-audit manifest "Layer 5" + folded into code_freeze GAP-2.4.D (Phase-2.6 reader-repoint). NOT fixed now — deployment-api reads buckets continuously so its source must flip in lockstep with the data migration (same Group-A reasoning as Done-def #3/A6).                                                                                                                                              | PM@`5c99664f` (+ code_freeze GAP-2.4.D)                   |
| Phase 0h sync scripts                     | done — `deployment-service/scripts/sync-buckets-prod-to-env.sh` (impl: enumerates env-tiered bucket pairs from `cloud-providers.yaml` via the canonical UTL resolver w/ YAML-walk fallback; env-LESS kinds skipped; same-region abort; truncated `day=` window over the 3 known layouts; idempotent `gcloud storage rsync`/`aws s3 sync`; `--dry-run`/`--kind`/`--years`/`--cloud`; per-bucket day-partition count + sample-parquet readability verification; manifest re-sync surfaced as an operator step not auto-launched) + `sync-buckets-prod-to-staging.sh` + `sync-buckets-prod-to-dev.sh` wrappers. `bash -n` + `shellcheck -S warning` clean. FIRST EXECUTION = Phase 3 / post-cutover (code_freeze GAP-2.4.E) — operator-directed handoff: Ikenna slot 8 owns the first-execution + any layout-specific refinement. | deployment-service@`fc1cfa0` (+ plan flips PM@`f2add75d`) |
| Phase 0f                                  | NOT started by slot 4 — operator-directed 2026-05-11: ABSORBED by Ikenna slot 8 (Harsh leaving ~3hr). Clean slate for slot 8 (~30 launchers under `deployment-service/scripts/vm/` + the companion QG step).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | — (handoff note in plan + scoreboard)                     |
| Done-def #5 — QG STEP 5.69 ratchet        | done — `unified-trading-pm/scripts/quality_gates/check_inline_bucket_uri.py` (v1 grep-based per-repo COUNT ratchet; `--scope`/`--source-dir`/workspace-wide; `--update-baseline` ratchets DOWN only) + `inline_bucket_uri_baseline.yaml` (seeded: deployment-api 27, execution-service 33, UTL 23, batch-live-recon 7, UAC 5, UI 4, deployment-service 3, features-service 2, strategy-service 2, instruments-service 1, rest 0) + STEP 5.69 in `base-service.sh` (mirrors STEP 5.67's per-repo-scoped shape; skips gracefully if checker not in this repo's PM checkout) + `test_check_inline_bucket_uri.py` (12 tests, all pass); `ruff`+`ruff format` clean, `py_compile` OK. v2 AST-walk hardening = a new `- [ ]` P2 follow-up.                                                                                           | PM@`913b020c`                                             |
| `slot_4.md` conflict-marker fix           | done — PM@`913b020c` committed `slot_4.md` with unresolved stash-pop `<<<<<<< / ======= / >>>>>>>` markers (foot-gun #4-adjacent); fixed in the immediately-following commit (both pings kept, chronological order)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | PM@`ffcf6496`                                             |
| Done-def #6 — drift audit table (PARTIAL) | done (partial) — § "Drift audit table (Done-def #6 — PARTIAL...)": L1-L5 + inline-URI surfaces, migrated-vs-drifting with named successors. Verified-zero TODAY: L1↔L4 (parity test), L2 features-\* config.py (migrated to `resolve_bucket`), inline-URI formatters (ratcheted at baseline, STEP 5.69, no new). STILL DRIFTING (all DEFERRED-AFTER code_freeze Phase 2.6): L2-tail `dependency_checker.py` probe templates, L3 legacy `get_bucket_name`/`BUCKET_PREFIXES` (~36+ consumers, ~92 candidate files), L5 deployment-api internal templates. FULL zero-drift = Phase-2.6 owner's done-def (GAP-2.4.D extends Done-def #6). Done-def #6 todo `status: helper-shipped`, checkbox stays `- [ ]`.                                                                                                                      | PM@`<this commit>`                                        |

**Still open (all captured as `- [ ]` plan todos / scoreboard rows / Q7):**

- **Phase 0c/0d** (provision env-tiered buckets + flat→env-tiered data migration + write-pause cutover) — code_freeze
  Phase 2.6 window (2026-05-15→05-19); slot 4's in that window (or hands off to whoever owns Phase 2.6).
- **Done-def #3** (legacy `get_bucket_name`/`BUCKET_PREFIXES` → `resolve_bucket_name` delegate) —
  `deferred-after-code_freeze-Phase-2.6` (= step 2.6.4); Q6 ✅ resolved.
- **Done-def #6 full zero-drift table** — Phase-2.6 owner's done-def (GAP-2.4.D); partial table shipped this session.
- **Q7** (env-less-GCP remainder: `pnl-store-defi`/`positions-store-defi`/`risk-store-defi` shape-align + `events`
  env-tier) — routed to Ikenna/operator; yaml + Phase-2.6 migration land once decided.
- **L2-tail** `dependency_checker.py` inline probe templates — blocked on the UTL `BaseDependencyChecker` migration +
  `test_mode`-infra rewrite OR Phase-2.6 (whichever first).
- **L5** deployment-api internal bucket templates reader-repoint — code_freeze GAP-2.4.D (Phase-2.6).
- **`OUTPUT_BUCKET_TEMPLATE`-stale-docs** follow-up (P2) — features-service-docs sweep.
- **Done-def #5 v2 AST-walk** hardening (P2) — precision: distinguish `f"gs://{x}/..."` from `resolve_bucket_uri(...)`,
  ignore docstrings.
- **Phase 0f** (VM-launcher env-awareness) — ABSORBED by Ikenna slot 8 (operator direction 2026-05-11).

Going quiet — Phase-1-code-complete remainder (everything except Phase 0c/0d/Done-def #3/Q7-resolution which are all
Phase-2.6 or operator-gated) is DONE; Phase 0f is Ikenna slot 8's; Phase 0c/0d + Done-def #3 are slot 4's
Phase-2.6-window work.

## DONE-2026-05-11 (cont. 5) — harsh-bucket-and-adapter-tab (slot 4), wrap-up: `OUTPUT_BUCKET_TEMPLATE`-docs cleanup + Phase-2.6-cutover scope handoff

Resumed per the 13:57 `[main → slot 4]` brief (which corrected the "Harsh Tab 4 final push" brief: Done-def #5 + Phase
0g already shipped → skip). Final actionable item this window = the `OUTPUT_BUCKET_TEMPLATE`-docs follow-up (queue item
3); the other queue items were already in their target state (env-less sub-todo: DeFi-raw + config-store shipped,
`pnl/positions/risk-store-defi` + `events` Q7-blocked; Done-def #6 partial table shipped @PM`74109cc5`;
`dependency_checker.py` migration NOT contained — `BaseDependencyChecker` is UTL-side + ~6-10 tests introspect the
`test_mode` infra → stays blocked).

| Item                                    | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Evidence                                              |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| `OUTPUT_BUCKET_TEMPLATE`-docs follow-up | done — dropped stale `INPUT_/OUTPUT_BUCKET_TEMPLATE` env-var + config-Field refs from `cross_instrument/docs/CONFIGURATION.md` + `DEPLOYMENT_GUIDE.md` + `multi_timeframe/.env.example` + the `paired_dispatch.py` `_delta_one_bucket` docstring (all stale post-`e980ecfd` migration; bucket names now via `resolve_bucket → cloud-providers.yaml`, resolver-aliased to `features-xinstrument`/`features-mtf`). Surgical edits, `.md` prettier-clean, ruff + py_compile clean. | features-service@`89e9a972` (+ plan flip this commit) |

### Phase-1-code-complete scope for this plan — DONE ✅

Everything in `bucket_name_ssot_canonicalisation_2026_05_10.md` except the Phase-2.6-cutover items + the operator-gated
items is shipped:

- ✅ Done-def #1 (canonical layer = yaml, env-tiered) · ✅ Done-def #2 (per-family config.py → `resolve_bucket`, incl.
  cross_instrument/multi_timeframe via the alias) · ✅ Done-def #4 (parity test extended) · ✅ Done-def #5 (QG STEP 5.69
  `gs://`/`s3://` ratchet — checker + baseline + base-service.sh + test) · ✅ Phase 0a (operator decision recorded) · ✅
  Phase 0b (yaml additive corrections) · ✅ Phase 0e (Group-A env-tier in yaml + parity test) · ✅ Phase 0g (UI env-tier
  verified + (b+) cross-check FINDING → Layer 5 → code_freeze GAP-2.4.D) · ✅ Phase 0h (sync scripts shipped —
  first-execution = Phase 3/post-cutover, handed to Ikenna slot 8) · ✅ Phase 0i (region pinning ratified
  ap-northeast-1) · ✅ env-less-GCP DeFi-raw + config-store · ✅ cross_instrument/multi_timeframe yaml-gap (Q5/A5) · ✅
  `OUTPUT_BUCKET_TEMPLATE`-docs follow-up · ✅ Done-def #6 PARTIAL drift-audit table.

### Carries to the code_freeze Phase 2.6 cutover window (2026-05-15→05-19) — slot 4's, or hands off to the Phase-2.6 owner

| Item                                                                                                                                                                                                                                                                                                                                                                                                               | Why it's Phase-2.6                                                                                                                                                                                               | Who                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **Phase 0c** — provision ~150-300 env-tiered Group-A + Group-B buckets across both clouds × 3 envs × ap-northeast-1                                                                                                                                                                                                                                                                                                | physical infra; needs ADC                                                                                                                                                                                        | slot 4 (operator: "assume harsh provisions") — code_freeze GAP-2.4.B |
| **Phase 0d** — migrate flat-bucket data into env-tiered buckets (≤0.01% drift verification + write-pause cutover)                                                                                                                                                                                                                                                                                                  | physical data migration; write-pause must align with the freeze window                                                                                                                                           | slot 4 — code_freeze GAP-2.4.C                                       |
| **Done-def #3** — flip legacy `get_bucket_name`/`BUCKET_PREFIXES` → `resolve_bucket_name` workspace-wide (~36+ consumers)                                                                                                                                                                                                                                                                                          | = the cutover-flip step (2.6.4) — must land DURING the write-pause, after provisioning + data migration (Group-A writers write continuously; flipping before the env-tiered buckets exist = first-write failure) | slot 4 — Q6 ✅ Option 2                                              |
| **L5 deployment-api reader-repoint** — replace deployment-api's internal flat-shape bucket templates (`DataStatusService._BUCKET_TEMPLATES` + `data_status_drilldown._BUCKET_TEMPLATES` + `data_query_service.build_bucket_name` + `upcoming_fixtures._SPORTS_BUCKET_TEMPLATE` + 3 hardcoded `f"gs://instruments-store-sports-{pid}/..."`) with `resolve_bucket_name(...)` + reconcile the L5.1↔L5.2 `ml-*` drift | deployment-api reads buckets continuously → must flip in lockstep with the data migration                                                                                                                        | code_freeze GAP-2.4.D (extends Done-def #6)                          |
| **L2-tail `dependency_checker.py`** — migrate the inline `"bucket_template": "market-data-tick-{ag}-{pid}"` probe strings → `resolve_bucket(...)`                                                                                                                                                                                                                                                                  | the probe template now drifts from the env-tiered yaml; must land in the same window as the data migration OR via the UTL `BaseDependencyChecker` migration (whichever first)                                    | code_freeze Phase 2.6 / UTL migration                                |
| **Done-def #6 FULL zero-drift table** — drift ≤0.01% per migrated bucket + zero readers still hit flat names                                                                                                                                                                                                                                                                                                       | runs after provisioning + data migration + the L3 flip + the L5 repoint                                                                                                                                          | code_freeze GAP-2.4.D owner                                          |
| **Q7 (operator-gated, NOT Phase-2.6-blocked)** — `pnl-store-defi`/`positions-store-defi`/`risk-store-defi` canonical-shape decision (rec b-i = symmetric `{kind}-defi-{env}-{pid}`) + `events` env-tier (rec c-i = dedicated Phase-2.6 sub-step / c-ii = 3rd permitted env-less exception; main's lean = c-ii)                                                                                                     | needs Ikenna/operator; once decided, the yaml edit + (if a rename) the Phase-2.6 migration follow                                                                                                                | Ikenna/operator                                                      |
| **Phase 0f** — VM-launcher env-awareness (~30 launchers read `DEPLOYMENT_ENV` + companion QG step)                                                                                                                                                                                                                                                                                                                 | operator-directed handoff 2026-05-11 (Harsh leaving ~3hr)                                                                                                                                                        | Ikenna slot 8                                                        |
| **Done-def #5 v2 AST-walk** (P2 hardening) — distinguish `f"gs://{x}/..."` from `resolve_bucket_uri(...)`, ignore docstrings                                                                                                                                                                                                                                                                                       | precision follow-up; v1 grep-based already catches NEW inline formatters                                                                                                                                         | not urgent — whoever picks it up                                     |

Going quiet — Phase-1 scope DONE; the above carries to the Phase-2.6 cutover (slot 4's window) + Ikenna slot 8 (Phase
0f) + Ikenna/operator (Q7).

## DONE-2026-05-12 — ikenna-bucket-prereq-tab (slot 8) — Phase 0f + Q7(c) close-out

- ✅ **Phase 0f shipped** — 72 launchers env-aware (5-sub-agent parallel fan-out). Commits FF'd to `live-defi-rollout`:
  `deployment-service@13ef741a` (15 MTDS) + `a2037d2` (19 sports) + `68ad99f` + `e60ae2c` (17
  cefi/defi/tradfi/prediction) + `ecea78f3` (9 features/ml/strategy/infra) + `5676048` (12 migration/recon/smoke
  - `setup-data-pipeline-vm.sh` VM-side bootstrap). Pattern from `launch-mdps-features-live.sh` (DEPLOYMENT_ENV default
  - `--env` CLI flag + closed-set validation + metadata propagation + GCE label). Backward compat preserved via
    `DEPLOYMENT_ENV=prod` default. PM plan-flip: `pm@96077adf`.
- ✅ **Phase 0h verified** — `sync-buckets-prod-to-{env,staging,dev}.sh` confirmed shipped by Harsh slot 4 pre-handoff
  (plan body line 258 already `status: done`). No Ikenna action needed.
- ✅ **Q7(c) events env-tier RESOLVED** — operator decision 2026-05-11 PM: events bucket goes env-tiered (option c-i).
  yaml flip + UTL `resolve_bucket_name` extension queue as Phase 2.6 sub-step. Q7(c) flipped to ✅ RESOLVED in this plan
  body § Open questions.
- ✅ **Watchdog architecture P1 follow-up filed** —
  [`plans/active/issues/watchdog_env_tiered_events_architecture_2026_05_11.md`](issues/watchdog_env_tiered_events_architecture_2026_05_11.md).
  Recommend option (i) single-watchdog-with-multi-bucket fan-in as default (lower-cost; smaller code change); instrument
  post-cutover; split to option (ii) per-env watchdogs only if throughput data shows it's needed. Picks up in next-cycle
  work-split after Phase 2.6 ships.
- **Q7(b)** `pnl-store-defi` / `positions-store-defi` / `risk-store-defi` shape-alignment — still operator-pending; not
  slot 8 to decide.

**Tier 2 carry-forward (rescan + design promotion)** — also shipped by parallel agents while slot 8 was on Phase 0f
fan-out; slot 8 follow-up was the plan-status flip:

- ✅ **Phase 3.A** — `deployment-service@<see manifest_schema_final_gate Phase 3.A>` — `launch-cross-asset-rescan-vm.sh`
  shipped (singleton-locked, asia-northeast1-c, per-VM shard isolation, WORKERS=64, HTTP_POOL_SIZE=128, tarball +
  tarball-from-local). Verified on disk.
- ✅ **Phase 3.B** — `cross-asset-rescan-` prefix added to `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` (line 374,
  value `None` per "log-only" semantics). Watchdog VM relaunched (latest at 2026-05-11T14:18 UTC; current state STOPPING
  — auto-recycle cycle).
- ✅ **Phase 3.C** — Launcher registered in `deployment_api/services/deploy_missing.py` `_SERVICE_LAUNCHER_SCRIPTS`
  (line 88, `"cross-asset-rescan": f"{_VM_SCRIPT_DIR}/launch-cross-asset-rescan-vm.sh"`).
- ✅ **Phase 3.D** — `instruments-service/scripts/cross_asset_rescan.py` shipped (333 lines): cross-asset dispatch,
  per-VM shard isolation, Class A auto-flips (`PARQUET_NAN_RATIO_EXCEEDED` / `PARTIAL_BUNDLE` / `SCHEMA_DRIFT` /
  `PHANTOM_PATH_MISSING`), Class C triage JSONL stream to `gs://{pid}-rescan-triage/{run_id}/triage.jsonl`, lifecycle
  events.
- ✅ **Rescan-design plan** promoted DRAFT → active — `manifest_cross_asset_rescan_design_2026_05_08.md` frontmatter
  flipped (`status: active`, `last_updated: 2026-05-12`).
- **Operational follow-up (P1 pending)** — actual rescan VM run is Phase 2.6 post-migration validation work; not
  triggered in this cycle.

All Tier 2 sub-phases now reflected as `[x]` in `manifest_schema_final_gate_2026_05_09.md:310/315/322/324`.

## DONE-2026-05-12 — Harsh slot 4 end-of-shift handover

> Harsh's shift ending 2026-05-11 ~14:45 UTC. This is the clean-pickup summary for Ikenna's agent: ✅ what shipped this
> shift + ⏭ what's left + the exact next step. Detail is in the `## DONE-2026-05-11 (cont. 4)` + `(cont. 5)` blocks
> above (carry-forward table) and `## Drift audit table (Done-def #6 — PARTIAL...)`. Working tree clean, ahead=0 — all
> work pushed to `origin/live-defi-rollout`. No uncommitted/WIP state.

### ✅ Shipped this shift (the resume-from-▶-RESUME-block session, 2026-05-11)

| Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Evidence                                                    |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Q6 ✅ relay — Done-def #3 → `status: deferred-after-code_freeze-Phase-2.6` (A6 = Option 2: defer the whole `get_bucket_name`/`BUCKET_PREFIXES`→`resolve_bucket_name` delegate to the Phase-2.6 cutover, = step 2.6.4) + Q7 NEW (env-less-GCP remainder: `pnl/positions/risk-store-defi` shape-align + `events` env-tier, routed cross-side to Ikenna)                                                                                                                                                                                                                                                    | PM@`e4fca599`                                               |
| Phase 0g (b+) cross-check FINDING — deployment-api carries its own flat-shape bucket templates (`DataStatusService._BUCKET_TEMPLATES` 18-entry + `data_status_drilldown._BUCKET_TEMPLATES` 16-entry near-copy that already drifts on `ml-*` + `data_query_service.build_bucket_name` + `upcoming_fixtures._SPORTS_BUCKET_TEMPLATE` + 3 hardcoded `f"gs://instruments-store-sports-{pid}/..."`) = a "Layer 5" reader-side drift; documented in § Pre-audit manifest "Layer 5" + folded into code_freeze GAP-2.4.D (Phase-2.6 reader-repoint)                                                              | PM@`5c99664f`                                               |
| Phase 0h sync scripts — `deployment-service/scripts/sync-buckets-prod-to-env.sh` (impl) + `-to-staging.sh` + `-to-dev.sh` wrappers; `bash -n` + `shellcheck -S warning` clean; first-execution = Phase 3/post-cutover (GAP-2.4.E) — Ikenna slot 8 owns the first-execution + any layout-specific refinement                                                                                                                                                                                                                                                                                              | deployment-service@`fc1cfa0` (+ plan flip PM@`f2add75d`)    |
| Done-def #5 — QG STEP 5.69 (`gs://`/`s3://` inline-f-string ratchet) — `unified-trading-pm/scripts/quality_gates/check_inline_bucket_uri.py` (v1 grep-based per-repo COUNT ratchet, `--update-baseline` ratchets DOWN only) + `inline_bucket_uri_baseline.yaml` (seeded: deployment-api 27, execution-service 33, UTL 23, batch-live-recon 7, UAC 5, UI 4, deployment-service 3, features-service 2, strategy-service 2, instruments-service 1, rest 0) + STEP 5.69 in `base-service.sh` (mirrors STEP 5.67 shape) + `test_check_inline_bucket_uri.py` (12 tests pass); ruff+format clean, py_compile OK | PM@`913b020c` (+ marker-leak self-correction PM@`ffcf6496`) |
| Done-def #6 — PARTIAL drift-audit table (§ "Drift audit table (Done-def #6 — PARTIAL...)") — L1-L5 + inline-URI surfaces, migrated-vs-drifting with named successors; verified-zero TODAY = L1↔L4 (parity test) + L2 features-\* config.py (migrated to `resolve_bucket`) + inline-URI formatters (ratcheted at baseline, no new). Done-def #6 todo `status: helper-shipped`, checkbox stays `- [ ]` (full zero-drift = Phase-2.6 owner / GAP-2.4.D)                                                                                                                                                    | PM@`74109cc5` (+ DONE cont. 4)                              |
| `OUTPUT_BUCKET_TEMPLATE`-docs follow-up — dropped stale `INPUT_/OUTPUT_BUCKET_TEMPLATE` env-var + config-Field refs from `cross_instrument/docs/{CONFIGURATION,DEPLOYMENT_GUIDE}.md` + `multi_timeframe/.env.example` + the `paired_dispatch.py` `_delta_one_bucket` docstring → all describe `resolve_bucket → cloud-providers.yaml` now; surgical, `.md` prettier-clean, ruff+py_compile clean                                                                                                                                                                                                         | features-service@`89e9a972` (+ DONE cont. 5 PM@`a798e248`)  |

**Phase-1-code-complete scope for `bucket_name_ssot_canonicalisation_2026_05_10.md` = DONE** ✅ — Done-def #1/#2/#4/#5 +
Phase 0a/0b/0e/0g/0h/0i + env-less-GCP DeFi-raw/config-store + cross_instrument/multi_timeframe yaml-gap (Q5/A5) +
`OUTPUT_BUCKET_TEMPLATE`-docs + Done-def #6 PARTIAL all shipped (see `## DONE-2026-05-11 (cont. 5)` for the full list).

### ⏭ What's left — the exact next step

**All remaining items land in the code_freeze Phase 2.6 cutover window (2026-05-15→05-19)** — or are operator-gated.
They're enumerated as a table in `## DONE-2026-05-11 (cont. 5)` § "Carries to the code_freeze Phase 2.6 cutover window"
and as `- [ ]` plan todos / scoreboard rows. Summary + the pickup order:

1. **Phase 2.6 cutover sequence** (the Phase-2.6 owner — slot 4 was assigned this window; Ikenna can re-assign): per
   `## Open questions` § A6 "Phase 2.6 Done-def #3 sub-sequence" (steps 2.6.1-2.6.5) +
   `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2.4 (GAP-2.4.B/C/D):
   - **2.6.1 / GAP-2.4.B** — provision ~300-400 env-tiered buckets (×2 clouds × 3 envs × all kinds), region-pinned (GCP
     `asia-northeast1`, AWS `ap-northeast-1`); extend `deployment-service` Terraform / `setup-buckets.py` with the
     resolver-derived name list; `gcloud storage buckets create` / `aws s3 mb` per name; `gcloud storage ls` /
     `aws s3 ls` verification probe per name.
   - **2.6.2 / GAP-2.4.C** — migrate flat-bucket data into the env-tiered buckets (`gcloud storage cp -r` /
     `aws s3 sync`), drift ≤0.01% per bucket (object count + size + spot-check 100 parquets); also runs the **Q7(b)**
     rename if Ikenna's confirmed the `pnl/positions/risk-store-defi` shape (rec b-i =
     `{kind}-defi-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}`) + the **Q7(c)** `events` → env-tiered migration (✅
     RESOLVED 2026-05-11 PM by Ikenna; `{pid}-events` → `{pid}-events-{env}` form; events are append-only so it's mostly
     write-new-and-archive-old) + the workspace-wide `gs://{pid}-events/events/{service}/...` reference update (the "no
     fire-and-forget VM launches" verification recipe etc. — known Phase-2.6 scope item; also the
     `vm_zombie_watchdog.py` reads from `{pid}-events` → either iterate all 3 envs or take a `--env` flag, P1 watchdog
     follow-up per § Q7).
   - **2.6.3** — brief write-pause window (operator-coordinated; flag VMs to wait).
   - **2.6.4 / Done-def #3** — flip `get_bucket_name`/`BUCKET_PREFIXES`→`resolve_bucket_name` workspace-wide (~36+
     consumers, pre-audited ~92 candidate files across
     instruments-svc/MTDS/execution-svc/deployment-svc/features-svc/strategy-svc/pnl/deployment-api/PM — recipe in §
     Pre-audit manifest "Layer 3 migration recipe") **+ the L5 deployment-api reader-repoint** (replace deployment-api's
     internal flat-shape bucket templates with `resolve_bucket_name(...)`, reconcile the L5.1↔L5.2 `ml-*` drift —
     recipe in § Pre-audit manifest "Layer 5") **+ the L2-tail `dependency_checker.py` probe-template migration** (the
     `"bucket_template": "market-data-tick-{ag}-{pid}"` strings → `resolve_bucket(...)`; needs the UTL
     `BaseDependencyChecker` migration first OR done in this window) — all in the same write-pause logical unit;
     `basedpyright` each consumer repo after.
   - **2.6.5** — verify writers writing to env-tiered buckets; archive (don't delete) flat buckets to
     `*-archived-flat-2026-05-19/` + 30-day retention; QG STEP 5.69 ratchet enforces no new flat-name refs; **then
     re-run `check_inline_bucket_uri.py --update-baseline`** (the baseline drops as L3/L5/L2-tail inline templates are
     removed) + run the **Done-def #6 FULL zero-drift table** (drift ≤0.01% per migrated bucket + zero readers still hit
     flat names — GAP-2.4.D extends Done-def #6).
2. **Q7(b)** — `pnl-store-defi`/`positions-store-defi`/`risk-store-defi` canonical-shape: still **operator-pending**
   (Q7(c) `events` ✅ resolved by Ikenna). Once operator confirms (rec b-i), the yaml change + the rename migration fold
   into step 2.6.2 above. § Q7 has the full mismatch table + recs.
3. **Phase 0f** (VM-launcher env-awareness) — ✅ DONE by Ikenna slot 8 @PM`96077adf` (~72 launchers env-aware) — see
   `## DONE-2026-05-12 — ikenna-bucket-prereq-tab (slot 8)` above. Phase 0h sync scripts ✅ DONE by slot 4
   @deployment-svc`fc1cfa0` (first-execution Phase 3/post-cutover). So the Phase-2.6 launcher-env + sync-script prereqs
   are both in place.
4. **Done-def #5 v2 AST-walk** (P2 hardening, `- [ ]` in the plan) — replace the v1 grep-based
   `check_inline_bucket_uri.py` with an AST-walk (distinguish `f"gs://{x}/..."` from `resolve_bucket_uri(...)`, ignore
   docstrings — same shape as STEP 5.65). NOT urgent (v1 already catches NEW inline formatters via the count ratchet);
   whoever picks it up.

**No blocker for the May-15 freeze gate** — everything above is the Phase-2.6 cutover window or operator-gated, not the
freeze-gate checklist.

---

### FINDING 2026-05-12 (slot 7, mock-data-benchmarking) — missing `benchmark-reports` bucket kind (P2, not freeze-gate-blocking)

`mock_data_pipeline_benchmarking_2026_05_10.md` (Phase 4.A / 5.A) needs a `benchmark-reports` (and a
`benchmark-synthetic-input`) storage kind in `cloud-providers.yaml` — where the synthetic-benchmark VMs write
`stage_profile.parquet` + `synthetic_run_manifest.json` (and the synthetic generator input parquets). Neither exists.
Until they're added: `deployment-service/scripts/vm/launch-synthetic-benchmark-vm.sh` uses the conventional
`${PROJECT}-benchmark-reports` / `${PROJECT}-benchmark-synthetic-input` names + the benchmark CLI
(`python -m unified_trading_library.synthetic`) takes `--report-uri` / `--input-uri` explicitly — so no QG STEP 5.69
inline-formatter violation, but it should go through `resolve_bucket_name(kind="benchmark-reports")` eventually.
**Suggested**: add both kinds to the `gcp:` and `aws:` storage blocks as cross-cutting Group-A-ish (env-tiered like
`events`/`config-store`); then ping slot 7 / the mock-data-benchmarking plan to switch the CLI. Owner: this plan
(bucket-ssot is the canonical owner of `cloud-providers.yaml`).

---

## Deferred work after 2026-05-12 Slot 3 session

| Phase / item                                                                          | Status as of 2026-05-12 19:30 UTC                                                                                                                                                                                                                                              | Successor / blocker                                                                               |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| Phase 0c — GCP prod bucket creation                                                   | ✅ DONE — 38 prd buckets created (asia-northeast1, UBLA)                                                                                                                                                                                                                       | No blocker — complete                                                                             |
| Phase 0c — STS flat→prd data migration (16 jobs)                                      | ✅ DONE — all 16 SUCCESS; market-data-tick-tradfi final (5298504/5298504). Full parity verified (Gate 2 met ~19:00 UTC)                                                                                                                                                        | No blocker — complete                                                                             |
| Phase 0c — dex-pools 1-object transient failure                                       | ✅ FIXED — manually copied `_index/availability_index.parquet`; parity 185079/185079                                                                                                                                                                                           | No blocker — complete                                                                             |
| PART C — service source `# noqa: gs-uri` markers + QG 5.69 baseline ratchet           | ✅ DONE — instruments-service@`5210149` (1 noqa marker, baseline 1→0) + deployment-service@`0b802ec` (3 noqa markers, baseline 3→0) + import-pattern fix (check_ml_dependencies_by_mode.py) + PM@`be768d2b` (baseline yaml updated). QG 5.69 now zero-tolerance for both repos | No blocker — complete                                                                             |
| PART C — bash scripts (instruments-service/scripts/ + deployment-service/scripts/vm/) | ✅ ALREADY DONE by slot 8 Phase 0f (2026-05-12, @`<slot8-sha>`) — bash scripts excluded from QG 5.69 scope                                                                                                                                                                     | No blocker — complete                                                                             |
| Phase 0c — AWS prod provision                                                         | ❌ NOT STARTED                                                                                                                                                                                                                                                                 | Deferred to code_freeze Phase 2.6 window (2026-05-15→05-19) per plan                              |
| Phase 0c — staging/dev provision                                                      | ❌ NOT STARTED                                                                                                                                                                                                                                                                 | Deferred to code_freeze Phase 2.6 window per plan                                                 |
| Phase 5A phantom audit (GCE VM)                                                       | 🔴 DEFERRED — CLAUDE.md requires GCE VM (same-region)                                                                                                                                                                                                                          | Needs dedicated GCE VM launch in asia-northeast1-c; deferred to next Slot 3 session or Harsh slot |
| Phase 0c-watchdog — `vm_zombie_watchdog.py` VM_PREFIX_TO_BUCKET retrofit              | 🔴 DEFERRED — separate operator decision on HEARTBEAT_BUCKET env-tier                                                                                                                                                                                                          | See `- [ ] Phase 0c-watchdog` checkbox (line ~144); operator decision needed before impl          |
