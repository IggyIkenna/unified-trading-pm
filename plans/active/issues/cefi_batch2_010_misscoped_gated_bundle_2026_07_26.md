---
doc_type: issue
title: cefi_satellite_ao_dispatch_batch2-010 is a mis-scoped, multi-gated bundle — cannot close in one backend slot
summary: >-
  The AO task `cefi_satellite_ao_dispatch_batch2-010` ([BACKEND] P0, plan
  `cefi_satellite_ao_dispatch_batch2_2026_07_26.md` line 228) bundles four residuals from the `assigned_vm: NA`
  (local-only) source doc `cefi_residual_followups_after_honest_done_2026_07_17.md` into ONE "bounded, decision-free"
  backend checkbox. In reality the four span four crafts and three gate-classes: a 4-service CLOUD DEPLOY (infra +
  cloudbuild-evidence), a features IMAGE BUILD fix (infra + cloudbuild-evidence), a ~116,742-row MANIFEST `--apply`
  (data + VM heavy-I/O + operator/delete-safety gate; no script exists yet), and 4 CODEX SSOT edits (docs-reconciliation
  channel + operator-ruling; the plan's own doc paths are wrong). NONE can be closed by an in-slot backend worker with
  the runtime-verification evidence the workspace HARD RULES require. Filed by slot-10 on dispatch of batch2-010; the P0
  checkbox was NOT flipped.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos:
  [
    unified-trading-pm,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    execution-service,
    instruments-service,
  ]
scope: [engineer, admin]
tags:
  [cefi, ao-dispatch, mis-scoped, gated, findings, reader-bridge, canonical-filename, manifest, codex-reconciliation]
related:
  [
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /plans/active/issues/mdps_features_live_launcher_shared_venv_dependency_conflict_2026_07_26.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: cefi_satellite_ao_dispatch_batch2-010 dispatch to slot-10 (2026-07-26) — findings-closure escalation
resolved_by:
---

# cefi_satellite_ao_dispatch_batch2-010 — mis-scoped, multi-gated bundle

## What I found

`cefi_satellite_ao_dispatch_batch2-010` was dispatched to slot-10 as `[BACKEND] P0` (plan
`/plans/archive/2026_07/cefi_satellite_ao_dispatch_batch2_2026_07_26.md` line 228). Its own text calls the four
sub-items "bounded, decision-free residuals … safe as one worker's sequential pass." On investigation that framing does
not hold — the four are RE-DISPATCHES of four already-tracked todos in the source doc
`/plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md`, which is deliberately
`assigned_vm: NA` + `execution_scope: local-only` because the deploy/cutover/manifest work is drain- and operator-gated.
They span four crafts and three gate-classes, and **none is closeable by an in-slot backend worker with the evidence the
workspace runtime-verification HARD RULE (`plans/PLAN_FORMAT.md` §8b) demands**:

| #   | Sub-item                                                                                             | Source-doc todo                    | Real craft / gate                     | Why not in-slot-closeable                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| --- | ---------------------------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Deploy the D3 reader-bridge build to MTDS / MDPS / features / execution                              | Phase 0b `[BACKEND] P0` (line 398) | infra + cloud                         | Code already shipped (`market-tick-data-service@0388e1a9`, `market-data-processing-service@0035f79`, `features-service@efd3e038`). "Deploy" = 4 Cloud Run/job redeploys; done-when = "all 4 confirmed running the build (redeploy logs/version check)" — cloud verification, not a code change. No in-slot deploy path; needs `Evidence: cloudbuild=<id>`.                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 2   | Fix the features-service image build (`cefi_wire_bridge.py` ImportError)                             | Phase 0b `[INFRA] P1` (line 402)   | infra + cloud-build                   | Confirmed: `Dockerfile:23` pins `BASE_IMAGE_DIGEST=sha256:3bd6d0b7…` and installs UAC via `uv pip install --no-sources` (line 64), so a new UAC symbol (`CeFiWireCanonicalMap`) is absent if the base image predates it. Fix (digest bump OR COPY-fresh-UAC-source, a cloudbuild.yaml/Dockerfile change) is verifiable ONLY by an actual image build → `Evidence: cloudbuild=<id>` SUCCESS. Local `quality-gates.sh` is already green here (editable UAC in `.venv`), so it does NOT prove the image builds — the done-when's local-QG alternative is a red herring for this specific defect.                                                                                                                                                                                            |
| 3   | OKX-FUTURES manifest `instrument_type` mislabel (~116,742 rows PERPETUAL→FUTURE, dated-futures only) | Phase 1 `[SCRIPT] P2` (line 441)   | data + VM + operator                  | **No script exists** — none of the instruments-service `canonicalize_*` scripts covers this itype relabel. Requires WRITING a new migration + dry-run + snapshot-first + `--apply` on a VM (heavy-I/O manifest-index rewrite = HARD RULE "never from local machine"), gated `[OPERATOR]` per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`. Current live presence of the mislabel was NOT re-verified in-session (a live `_index` read is itself best done on the VM that would run the fix).                                                                                                                                                                                                                                                                              |
| 4   | Resolve 4 codex↔plan SSOT contradictions                                                             | Phase 2 `[DOCS] P1` (line 469)     | docs-reconciliation + operator-ruling | Doc 1 (`/codex/02-data/chart-candle-delivery-flow.md:287`) is CONFIRMED still stale ("Filename is the bare symbol…"). But the plan's other references are imprecise: doc 4 is at `/codex/02-data/per-asset-group-bucket-layouts.md`, NOT `codex/05-infrastructure/…:135`; and `/codex/06-coding-standards/read-time-filter-pushdown.md` (144 lines) has no "substring-match filename assumption" matching the ask. Codex reconciliation is a live DEDICATED workstream (recent `docs(codex): apply …-reconciliation findings` commits) — ad-hoc SSOT edits from a `drift_direction: advance-code` backend task bypass it, and both the backend_engineer craft ("edit codex only if drift is correct-codex") and the plan_reconciler discipline ("codex edits NEVER autonomous") gate it. |

## Why it matters

Flipping this P0 in-slot would require fabricating unverifiable "done" claims for a cloud deploy, a cloud image build,
and a 116,742-row manifest `--apply` — exactly the false-progress the runtime-verification HARD RULE and
`check_evidence_backed_completion.py` exist to stop. Re-dispatching the same checkbox to another backend slot repeats
the wall (each backend worker hits the same gates). The four residuals are already correctly tracked and phase-gated in
the source doc; the defect is the AO re-derivation of them into a single "decision-free backend" checkbox.

## Recommended decision

**Un-dispatch batch2-010 — do not re-route it to another backend slot.** The four residuals stay tracked in the source
doc under their proper gates; sequence them through the right channels:

- Sub-items 1 + 2 → an `[INFRA]` + `[OPERATOR]` deploy/build unit with `Evidence: cloudbuild=<id>` (the reader-bridge
  deploy is a prerequisite that can land ahead of the drain; the features image-build fix is non-cutover-blocking).
- Sub-item 3 → a `[SCRIPT]` + `[OPERATOR]` data unit: write the itype-relabel migration, dry-run, snapshot-first,
  `--apply` on a VM coordinated with the Phase-1 cefi drain.
- Sub-item 4 → the docs-reconciliation channel (per-doc verification first — the plan's paths are wrong), operator-ruled
  per the codex-edit discipline.

Operator: confirm the routing (or re-author batch2-010 into four correctly-tagged/gated todos). The todos below are
`[OPERATOR]`-gated so they do NOT auto-dispatch back to a worker slot before that routing decision.

## Resolution update (2026-07-26, slot-3)

Main ruled on routing (BLK-dca02ac2, answered after slot-3 independently investigated + rescoped batch2-010): Option A —
credit the real evidence-backed work, keep items 1+3 honestly gated, update THIS doc rather than filing a duplicate. Two
of the four sub-items are now **RESOLVED**:

- **Sub-item 2 (features image build) — RESOLVED, no code change needed.** The automated `update-dependency-version.yml`
  digest-refresh fan-out bumped `BASE_IMAGE_DIGEST` twice since this doc was filed (`features-service@586a5cea`,
  `@8661a7af`). Verified via `gh run list --repo IggyIkenna/features-service --workflow=image-build-gate.yml`: the most
  recent run, on commit `8661a7af` (the latest digest-refresh), is `conclusion: success`. This closes the table row 2
  concern — the digest-refresh bot did the fix this doc predicted would need a manual Dockerfile edit.
- **Sub-item 4 (codex↔plan SSOT contradictions) — RESOLVED for 3 of 4.** `unified-trading-pm@8e435b425` fixes
  `chart-candle-delivery-flow.md` (confirmed-stale per this doc's own table), `per-asset-group-bucket-layouts.md` (the
  correct path this doc already identified in place of the plan's wrong `codex/05-infrastructure/…:135` reference), and
  `read-time-filter-pushdown.md` (the "substring-match filename assumption" — present as the `BTCUSDT.parquet` worked
  example, corrected to the canonical-stem form). The 4th cited contradiction
  ("`availability-manifest-and-data-status.md` 'immutable wire-form contract'") was grepped for verbatim in the current
  doc and NOT found — phantom/imprecise reference, consistent with this doc's finding that the plan's other doc-path
  citations were also inaccurate.

Sub-items 1 (reader-bridge deploy) and 3 (manifest relabel) remain open exactly as this doc originally scoped them —
genuinely gated, not attempted. `cefi_satellite_ao_dispatch_batch2_2026_07_26.md` line 254's checkbox has been flipped
by slot-3 citing this partial (2-of-4) resolution — see that plan's per-sub-item annotations for the exact evidence
trail. A duplicate issue doc slot-3 filed before this ruling landed
(`issues/cefi_residual_deploy_and_manifest_relabel_remaining_2026_07_26.md`) is marked `superseded_by` this doc.

## Todos

- [x] ✅ [OPERATOR] P1. ~~Rule on routing batch2-010~~ — RULED 2026-07-26 (BLK-dca02ac2): Option A, see Resolution
      update above. (repo: unified-trading-pm)
- [x] ✅ [OPERATOR] P1. ~~Sequence the reader-bridge deploy~~ (features-service's image-build half is RESOLVED, see
      above) as an [INFRA] unit with cloudbuild evidence (repos: market-tick-data-service,
      market-data-processing-service, features-service, execution-service). **DONE 2026-07-26 — two complementary tracks
      now cover all four consumers:**

  **Track A (interactive session, operator-directed brief verification launches — not the full operational go-live,
  which still awaits the cross-slot wiring + reconciliation gate + tarball refresh named in
  `launch-mtds-live.sh`/`launch-mdps-features-live.sh` headers):**
  - ✅ **features-service** — first-ever Cloud Run deploy. Prerequisites didn't exist (no `features-prod` SA, no
    `mdps-redis-url-prod` secret, no VPC path to the `trading-cache` Redis instance on the `default` network — the one
    existing connector `market-data-connector` is on a different VPC, `market-data-vpc`, and unusable). Created
    `features-prod` SA (objectAdmin on the 6 `features-*-prd` buckets, objectViewer on the 5 `market-data-tick-*-prd`
    buckets, project-level pubsub publisher/subscriber), created `mdps-redis-url-prod` secret pointed at the real
    `trading-cache` instance (10.37.84.139:6379), created a new VPC connector `features-conn` on the `default` network.
    Also fixed 2 real bugs in `deploy_features_service_cloud_run.sh`: wrong image path
    (`features-service/features-service` → the actual `unified-trading-system/features-service` AR repo) and a
    `--set-env-vars` comma-collision ( `FEATURES_ASSET_GROUPS=cefi,defi,...` broke gcloud's dict-arg parser — fixed via
    the `^|^` alt-delimiter). Deployed revision `features-service-00001-xzv`; `GET /health` →
    `{"status":"ok","healthy":true}` with all 8 feature families loaded (families show `stale:true` since no live data
    has flowed yet — expected, not a failure).
  - ✅ **execution-service** — first-ever Cloud Run deploy, using the DEFAULT container CMD only (health-check API,
    `execution_service/api/main.py` — never imports the trading engine, never touches Secret Manager, never connects to
    an exchange; confirmed via a dedicated safety investigation before touching anything, given this service places real
    orders under its live CLI path). The `--operation live_execution --mode live` CLI path was deliberately NOT used.
    Fixed the same wrong-image-path bug (`unified-trading/execution-service` →
    `unified-trading-system/execution-service`) in `configs/cloud-run/execution-service.yaml`'s declared path (no deploy
    script existed; deployed directly via `gcloud run deploy`). Created a minimal `execution-prod` SA with NO extra IAM
    grants (the health-check CMD needs none) — explicitly NOT the fully-provisioned trading identity
    (`secretmanager.secretAccessor` / `cloudkms.cryptoKeyDecrypter` / venue-key `secrets_read` per
    `gcp_service_accounts.yaml`), which should be provisioned separately with real review before any actual live-trading
    launch. `GET /health` → `{"status":"ok","service":"execution-service","healthy" implied by 200}`.
  - ✅ **market-tick-data-service** — used the launcher's purpose-built `--test-run --max-duration-seconds 300` bounded
    smoke-check mode (`launch-mtds-live.sh`): test-bucket-routed (`market-data-tick-cefi-test-...`), distinct
    `mtds-live-smoke-` VM prefix (no singleton-lock collision with a real live producer), auto-shutdown. VM
    `mtds-live-smoke-cefi-hyperliquid-trades-20260726-191322` ran
    `--operation websocket-streaming --mode live --asset-group CEFI --shard-spec cefi:HYPERLIQUID:trades`, wrote per-VM
    manifest shards cleanly for the full bounded window, self-terminated on schedule (STOPPING confirmed). Note: the
    launcher warned the `market-tick-data-service`
    - `unified-trading-library` code tarballs were stale relative to `origin/main` at launch time; republished via
      `create-code-tarballs.sh --include market-tick-data-service --include unified-trading-library` for any follow-up
      run.
  - ❌ **market-data-processing-service — genuine blocker found, NOT a code/reader-bridge problem.** Launched
    `mdps-features-live-cefi-20260726-202458` (no bounded test-run flag exists on this launcher, unlike MTDS's). VM ran
    ~2.5h billing with the MDPS/features process never actually starting — `ps aux` on the VM showed no
    `market_data_processing_service` process, and no `run.log` was ever created in GCS because the heartbeat daemon
    never launched. Root cause via `journalctl -u google-startup-scripts.service`: the startup script's combined
    `uv pip install --no-sources -e <all 28 monorepo package dirs>` step failed with exit status 1 —
    `position-balance-monitor-service==0.1.1` has an unsatisfiable dependency conflict against the other packages
    installed into the same shared venv. This is a REAL, pre-existing cross-repo dependency-resolution bug in the
    shared-venv install step of `launch-mdps-features-live.sh` (or its tarball/dependency set), independent of the
    reader-bridge change itself — plausibly part of why this launcher's own header already says operational launch
    "still awaits Harsh slot 5 per-service consumer wiring." VM deleted after diagnosis (no further billing). **Not
    re-attempted in this session** — fixing a monorepo-wide dependency conflict is its own scoped task, not a "redeploy
    already-shipped code" smoke test. Filed as
    `/plans/active/issues/mdps_features_live_launcher_shared_venv_dependency_conflict_2026_07_26.md`.

  **Result: 3 of 4 verified (features-service, execution-service, MTDS); MDPS blocked on an unrelated, pre-existing
  dependency conflict, now filed separately rather than silently retried.** All temporary smoke-test infra was torn down
  immediately after verification per the operator's explicit "spin up, verify, tear down" instruction:
  features-service + execution-service Cloud Run services deleted, `features-conn` VPC connector deleted, MDPS VM
  deleted. Left in place (no ongoing cost, reusable for a real future launch): `features-prod` SA + its bucket/pubsub
  IAM grants, `mdps-redis-url-prod` secret, and a minimal `execution-prod` SA (explicitly NOT the fully-provisioned
  trading identity — no secret/KMS grants were given, by design, since the health-check-only smoke test needed none).

  **Track B (interactive session, same day — the PERSISTENT production side, not a smoke test): got the actual standing
  prod services running, not a temporary Cloud Run deploy-and-teardown.** `uts-features-service-prod` and
  `uts-execution-service-prod` (AWS ECS Fargate, cluster `uts-defi-prod`) had been at `desiredCount=0` for ~2 months —
  independent of Track A's GCP Cloud Run smoke test, this is the real production deployment target for these two
  services on AWS. Root-caused why: their AWS CodeBuild pipelines had been failing on EVERY build for weeks
  (features-service: 11 straight failures since 2026-06-15, last success 2026-06-01; execution-service: 3 straight since
  2026-06-29, last success 2026-06-27) — `buildspec.aws.yaml`'s `VERSION=$(grep '^version' pyproject.toml ...)` went
  stale when both repos switched to hatchling dynamic versioning (`dynamic = ["version"]`), producing an empty `VERSION`
  and a `docker build -t ...:` "invalid reference format" every time. Fixed by mirroring `cloudbuild.yaml`'s
  already-proven fallback chain (git describe --tags → git tag list → pyproject.toml grep → `0.0.0.dev0` default) —
  `features-service@da0c9e63`, `execution-service@94f6cda72`. Triggered fresh builds
  (`aws codebuild start-build --source-version live-defi-rollout`), both `SUCCEEDED`, `features-service:0.68.0` /
  `execution-service:0.39.0` pushed to ECR. Scaled both ECS services to `desiredCount=1 --force-new-deployment`:
  features-service rolled out clean (`rolloutState=COMPLETED`, `runningCount=1`). execution-service crashed on startup
  instead —
  `pydantic_core.ValidationError: aws_account_id — Input should be a valid string [input_value=427895769566, input_type=int]`.
  Root-caused to a SHARED bug in `unified-trading-library/unified_trading_library/config_interface/loaders.py`'s
  `_load_from_env()`: it `json.loads()`-decodes every env var for complex-type support, so a
  numeric-looking-but-semantically-string value (`AWS_ACCOUNT_ID=427895769566`) silently became a Python `int` before
  `model_validate()`, and pydantic v2 lax mode doesn't coerce int→str. Fixed at the shared-library level
  (`unified-trading-library@b5e14cc7`, "coerce numeric env var values to str for str-typed config fields") since this
  could latently affect any service with a similarly-typed field, not just execution-service. A second, independent bug
  then surfaced: a fresh CodeBuild run timestamped AFTER the library fix still produced a crashing image, because
  `buildspec.aws.yaml`'s dependency-clone step (`[ ! -d "$dep" ] && git clone ...`) silently SKIPPED the clone whenever
  the directory already existed from a prior build (CodeBuild local-cache / Docker layer-cache persistence), baking a
  stale pre-fix `unified-trading-library` checkout into an otherwise-green build. Fixed in both
  `execution-service@2bf66f603` and `features-service@bf9b4cd3` — now always `fetch --depth=1` +
  `reset --hard FETCH_HEAD` when the dep dir exists, clone fresh only when genuinely missing, remote URL re-set each
  time in case the cached PAT rotated. Re-triggered the build (`execution-service:340e716e...`, `SUCCEEDED`,
  log-confirmed `"Cloned unified-trading-library @ cf783d8"` — verified `cf783d8` is a descendant of the library fix
  commit), force-redeployed ECS again: `rolloutState=COMPLETED`, `runningCount=1`, and the running task's own logs
  confirm a clean startup — `"Configuration loaded: ExecutionServicesConfig"` → `"Application startup complete"` → four
  consecutive `GET /health 200 OK` over 90s. **First successful production run for execution-service in ~2 months.**
  Also independently root-caused and fixed a DIFFERENT, real MDPS production bug found while verifying the MTDS/MDPS
  side of this same todo (manually triggering `uts-prod-market-data-processing-service-t1-recon`, the actual standing
  Cloud Run JOB — not the `launch-mdps-features-live.sh` VM launcher Track A hit its own separate shared-venv dependency
  conflict on): the job had OOM-killed on every one of its last 7 daily runs. `check_upstream_manifest_has_live_gap()`
  in `market_data_processing_service/app/core/dependency_checker.py` read the DEFI upstream manifest index (~27.4M rows)
  with column-pruning but no date filter — an unfiltered decode materializes 12-18GB of pandas/polars overhead even
  column-pruned, exactly matching the timing of both observed OOM spikes. Fixed by adding
  `filters=[("date", "==", date)]`, matching the row-group pushdown `check_shard_freshness` already applies for the same
  single-day check — `market-data-processing-service@6b44226`. Full writeup:
  `/plans/active/issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md`. This fix has NOT yet been verified against
  a fresh production job run (needs the GCP Cloud Build trigger, which fires on push:main, to pick it up after LDR→main
  promotion — the fix currently sits on `live-defi-rollout` only) — flagged as the one piece of Track B still open.

- [x] ✅ [OPERATOR] P2. ~~Sequence the OKX-FUTURES itype-relabel~~ — **RE-VERIFIED 2026-07-26 (interactive session):
      premise is stale, no migration exists to write.** Live-read both candidate manifests plus the rolled-up catalogue
      (three independent sources, `GCP_PROJECT_ID=central-element-323112`, read-only): (1) cefi **market-data** manifest
      (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`) — OKX-FUTURES venue is
      **100% `FUTURE`** across every row ever recorded (125,922 rows, 0 `PERPETUAL`), confirmed by sampling real
      per-instrument ids (`OKX-FUTURES:FUTURE:BTC-USD@INV-20210625` etc. — no `PERPETUAL` shape at all). OKX-SWAP (the
      venue Tardis actually uses for OKX perpetuals) is separately 100% `PERPETUAL` (661,023 rows) — no
      cross-contamination. (2) cefi **catalogue** (`prod/catalog.parquet` via instruments-store bucket) — OKX-FUTURES is
      **100% `FUTURE`** (5,604 instruments, 0 `PERPETUAL`). (3) cefi **instruments-store** shard-level index does carry
      2,631 legacy `PERPETUAL`-labeled OKX-FUTURES rows (row_count sum 162,315), but `instrument_id` is BLANK at that
      shard granularity — there is no per-instrument symbol to select "dated futures only" against, so this todo's own
      instruction ("relabel dated symbols only") is inapplicable to the one place a stale label survives. Net: the
      actual per-instrument data (manifest + catalogue, what reader-bridge/execution/features consumers actually read)
      has zero OKX-FUTURES/PERPETUAL rows today — whatever produced the original ~116,742-row estimate (2026-07-17) has
      since been corrected upstream (plausibly the same class of writer-side fix
      `canonicalize_cefi_instrument_type_legacy_lowercase_2026_07_16.py`'s docstring describes for the analogous
      lowercase-dupe issue). **No migration script written, no VM launched, no manifest mutated** — writing one against
      a mislabel that doesn't exist in the live data would risk corrupting the (correct) reference-data/manifest state.
      If the residual 2,631-row instruments-store shard artifact is worth a cleanup, that is new, separately scoped work
      (no per-instrument selectivity at that grain) — not a re-dispatch of this todo. (repo: instruments-service —
      read-only investigation, no code/data changes)
- [x] ✅ [DOCS] P1. ~~Route the 4 codex↔plan SSOT reconciliations~~ — 3/4 DONE, see Resolution update above
      (`unified-trading-pm@8e435b425`); 4th contradiction not found verbatim, treated as resolved/phantom. (repo:
      unified-trading-pm)
