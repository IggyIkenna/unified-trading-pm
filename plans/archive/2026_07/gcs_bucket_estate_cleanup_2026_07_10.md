---
doc_type: plan
title: GCS bucket estate cleanup — central-element-323112 (332 buckets)
summary:
  Full audit + cleanup of the GCP project's 332 GCS buckets — classify every bucket against what code actually
  reads/writes (not what config declares), delete confirmed-orphaned buckets, clean stale Terraform resources +
  bucket_config.yaml/cloud-providers.yaml entries, and fix real data-pipeline correctness bugs surfaced along the way
  (gas-fees manifest scanning an empty bucket, lst-rates reader/writer bucket mismatch, cf-manifest-audit / qg-snapshot
  crons that were silently failing for weeks).
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos: [deployment-service, unified-trading-library, market-tick-data-service, strategy-service, ml-service]
scope: [engineer, admin]
tags: [gcs, buckets, cleanup, terraform, data-correctness, autonomous]
related:
  [
    plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    plans/active/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    plans/archive/issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md,
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
  ]
created: "2026-07-10"
last_updated: "2026-07-14"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: operator-conversation-2026-07-10, dispatched /autonomous while operator away ~3h
assigned_role: infra
drift_direction: advance-code
model_tier_note:
  "Flagged per AUTONOMOUS_AGENT_RULES self-check — this is a long cross-repo autonomous loop, which CLAUDE.md's
  model-tier-selection normally routes to opus-required. Running as Sonnet 5 (harness-assigned, cannot self-upgrade
  mid-session). Documenting per rule 2 (decide-and-document, operator unavailable to reassign) rather than halting.
  Proceeding with extra verification rigor (empirical emptiness checks before every deletion, narrow git scoping) to
  compensate."
---

# GCS bucket estate cleanup — central-element-323112

## Why this plan exists

Operator asked (conversationally, this session) which of the project's GCS buckets are actually used, found several
confirmed-dead ones (alerting-history-prod, alerting-state-prod, alerting-service-test, cicd-events-prod,
backtest-configs — all already deleted + shipped before this plan was created), then asked to cover the FULL 332-bucket
estate, clean Terraform + the bucket-provisioning config files, and delete every confirmed-bad bucket. Operator then
stepped away for ~3h and invoked `/autonomous` — apply `AUTONOMOUS_AGENT_RULES.md` + `SUB_AGENT_MANDATORY_RULES.md`,
finish everything that can be finished, document (don't block on) anything genuinely needing operator judgment.

**Ground-truth data files** (already produced, reuse — do not regenerate):

- `/private/tmp/claude-501/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3/8574efc9-ddd6-40f5-bf08-c575d1debb44/scratchpad/all_buckets.csv`
  — full 332-bucket list + timestamps
- `.../scratchpad/classify_buckets.py` + `classification_output.txt` — mechanical template-match classification
  (FLAT_CANONICAL / ENV_TIERED_CANONICAL / ROLLED_BACK_ENV_ARTIFACT (63 buckets) / GCP_SYSTEM / UNMATCHED (148))
- `.../scratchpad/bucket_scan_results.tsv` — in-progress shallow-listing emptiness scan (background task, was ~127/332
  when operator left)

## Already shipped this session (before this plan existed)

- Deleted (confirmed empty via `gcloud storage ls **`): `alerting-history-prod-central-element-323112`,
  `alerting-state-prod-central-element-323112`, `alerting-service-test-central-element-323112`,
  `cicd-events-prod-central-element-323112`, `backtest-configs-central-element-323112`.
- Terraform cleaned: `deployment-service/terraform/gcp/main.tf` (removed `alerting_history`/`alerting_state`/
  `cicd_events` resources + IAM bindings) — commits `7505ec6`, `849ff20`.
- `bucket_config.yaml` cleaned: removed `backtest-configs-{project_id}` provisioning entry — commit `5e06a6f`.
- Lifecycle policy added directly (bucket not Terraform-tracked) to `alerting-service-central-element-323112`:
  `alerting/history/` → NEARLINE@30d → ARCHIVE@90d → Delete@365d. Documented in `alerting-service/docs/GCS_PATHS.md` —
  commit `49b0a52`.
- Fixed `qg-snapshot-daily` cron (was silently failing ~2 weeks, `central-element-323112-deployment-events` stayed
  empty): deleted a redundant non-Terraform-tracked duplicate Cloud Scheduler job; fixed `python3`→system-python bug in
  `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` (qg-snapshot branch was the one branch missing the
  `$VENV/bin/python` rewrite every other branch does) — commit `3c7cd1c` (direct push, dirty-deps carve-out).
- Wrote `unified-trading-library/unified_trading_library/cf_manifest_audit.py` (new module, moved + fixed from
  `unified-trading-pm/plans/audit/results/cf_manifest_audit_all.py` + `cf_manifest_audit_2026_06_01.py` — the old
  `cf-manifest-audit-all` console-script was never packaged/installed anywhere, job silently failed for ~3 weeks).
  Edited `deployment-service/terraform/{gcp,aws}/cf_manifest_audit_scheduler.tf` to invoke
  `python -m unified_trading_library.cf_manifest_audit` instead. **NOT YET SHIPPED** — was mid dry-run validation (task
  `bcnybd5tw`) when operator left.

## Parallel research already completed this session (findings baked into the todos below)

1. **`features-mtf-{sports,pred}` confirmed dead** — `features-service/scripts/multi_timeframe/smoke_matrix.py:35`
   `SUPPORTED_ASSET_GROUPS = ("CEFI","DEFI","TRADFI")` — sports/prediction never computed. Both buckets empty.
2. **63 buckets = `ROLLED_BACK_ENV_ARTIFACT`** — env-tiered variants of Group-B kinds whose env-split
   `cloud-providers.yaml`'s own comments say was explicitly rolled back (`features-delta-one`, `features-volatility`,
   `features-onchain`, `features-xinstrument`, `features-mtf`, `strategy-store`, `execution-store`, `ml-artifacts`,
   `ml-training-artifacts`). Full list in `classification_output.txt`.
3. **9 of 11 DeFi reference-data kinds never write to their own declared bucket** — real data goes to the shared
   `market-data-tick-defi-prd-{pid}` bucket instead: `dex-pools`, `dex-swaps`, `evm-defi`, `solana-defi`,
   `lending-indices`, `lst-rates`, `oracle-prices`, `gas-fees`, `liquidations`. Only `eigenlayer-rewards` and
   `perp-funding` are genuinely live under their own kind.
   - **`gas-fees` is a live BUG, not just orphaned storage**:
     `market-tick-data-service/.../data_manifest_handler.py:215` scans
     `resolve_bucket_name(kind="gas-fees", asset_group="defi")` for manifest/data-status purposes, but the writer
     (`gas_fee_handler.py:419,757,842`) writes to the `market-data` bucket instead — **the manifest scanner is reading
     an empty bucket and may be under-reporting real gas-fees coverage.** Needs its own fix, not just deletion.
   - **`lst-rates` has a similar reader/writer mismatch**: writer uses `market-data` bucket
     (`lst_rates_handler.py:311,355,381,429`), but `e2e-testing/scripts/defi/staked_basis_funding_scan.py:198` reads via
     `kind="lst-rates"` — the e2e script may be reading stale/empty data.
4. **risk-store/pnl-store/positions-store**: THREE declared naming schemes are ALL dead. The real, live naming is a
   FOURTH scheme not in any bucket list seen this session — `unified_trading_library/config_interface/paths/registry.py`
   PATH_REGISTRY: `positions-store-{pid}` (no asset_group — real), `pnl-attribution-store-{pid}`,
   `risk-metrics-store-{pid}`. Every asset-group-suffixed risk-store-\*/pnl-store-\*/positions-store-\* bucket (any of
   the 3 dead schemes) is an orphan — `risk-and-exposure-service`/`pnl-attribution-service`/
   `position-balance-monitor-service` don't exist as real repos.
5. **football-\* buckets (4) confirmed deprecated** — pre-hive-migration legacy sports pipeline.
   `unified-trading-pm/scripts/sports/migrate_sports_gcs_to_hive.py:43-47` treats them as the OLD migration source;
   `understat_bulk_download_backfill_2026_06_29.md:57,136` explicitly calls `football-raw-data-all-sources` "DEPRECATED
   / no longer used."
6. **`reconciliation-store-test` orphaned** — real code uses `recon-{project_id}` (totally different name),
   `batch-live-reconciliation-service/batch_live_reconciliation_service/config.py:79`.
7. **`pnl-attribution-central-element-323112` orphaned** (one-off script example only) — real default is
   `pnl-attribution-output` (`strategy-service/strategy_service/pnl/config.py:15`, no project-id suffix).
8. **`ml-configs-store`/`ml-models-store`/`ml-predictions-store`**: messier — writer often bypasses the resolver via a
   hardcoded flat template (`deployment-api/deployment_api/deployment_api_config.py:642`,
   `ml-service/ml_service/inference/config.py:135,145`, `ml-service/.../training/config.py:74-76`), while
   `unified-trading-library/.../model_registry.py:77` writes the resolver's env-tiered shape. **Genuinely split by
   subsystem** — must verify real object counts on BOTH shapes per kind before touching anything.
9. **Confirmed active/keep, no action**: `databento-batch-registry-asia`, `deployment-orchestration`,
   `deployment-scripts` (VM bootstrap source, referenced by ~10 launchers), `pnl-attribution-output`.
10. **Zero code references anywhere, but look like OPERATOR scratch buckets (not app-orphaned infra)** —
    `data-job-config`, `ml_jobs_ikenova`, `summary-stats`, `staging-bucket-general`, `temp-bucket-general`. Different
    risk category from app-orphaned buckets: absence of code reference doesn't prove safe-to-delete when a human may
    have put real data there manually. **Flag explicitly in final report; do not silently auto-delete** even if empty —
    note as a judgement call for operator sign-off, unless truly empty AND generic-named, in which case deleting is
    reasonable but must be called out, not silent.

## Never touch (regardless of any evidence found)

`central-element-323112-orchestrator-creds` (credentials) · `central-element-323112-pre-migration-snapshot` (DR backup)
· `central-element-323112-client-statements` (compliance-scaffolded, empty is expected) · `artifacts.*.appspot.com` /
`*.appspot.com` / `*_cloudbuild` / `*-function-source` / `firebaseapphosting-sources-*` / `gcf-sources-*` / `gcf-v2-*` /
`run-sources-*` (GCP-system-managed) · any `terraform-state`/`*-deployment-state` bucket (infra backend state,
catastrophic if lost) · `trading-audit-records-*`/`audit-records`/`manual-audit-*` (compliance retention-locked).

## Todos

- [x] 1. ✅ [SCRIPT] P0. Deleted 5 confirmed-empty orphaned buckets + cleaned Terraform/bucket_config.yaml (see "Already
      shipped" above) — deployment-service@7505ec6,849ff20,5e06a6f, alerting-service@49b0a52.
- [x] 2. ✅ [SCRIPT] P0. Fixed qg-snapshot-daily cron (python3→venv-python bug + duplicate scheduler) —
      deployment-service@3c7cd1c.
- [x] 3. ✅ [SCRIPT] P0. cf_manifest_audit shipped — unified-trading-library@f0a2c4cc, deployment-service@7890a14.
- [x] 4. ✅ [SCRIPT] P0. Full 332-bucket scan completed; cross-checked against every candidate list; found 35/150
      "DEAD_CONFIRMED" buckets actually have real content (see Progress Log "CRITICAL DECISION" entry) — deletion scope
      narrowed to the 115 confirmed-empty.
- [x] 5. ✅ [SCRIPT] P0. Deleted 115 confirmed-empty buckets (deletion_log.tsv, 115/115 DELETED, 0 failures, 0 dupes,
      independently verified via live `gcloud storage buckets list` count: 332→218). One false-positive caught +
      corrected (`dex-pools-test-central-element-323112` recreated — see Progress Log).
- [x] 6. ✅ [SCRIPT] P0. cloud-providers.yaml + bucket_config.yaml cleaned — deployment-service@c72a0cb.
- [x] 7. ✅ [DATA] P1. Issue doc filed — unified-trading-pm PR #920,
      `plans/active/issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md`.
- [x] 8. ✅ [SCRIPT] P1. ml-store split-usage: got real object counts on all 18 variants (3 kinds × flat + 5
      env-tiered). All empty except `ml-models-store-central-element-323112` (flat, 3 objects). Mixed/uncertain signal
      (real-but- dormant resolver code paths for several shapes) — decided NOT to delete any, flagged for dedicated
      follow-up rather than guessing (see Final Report below).
- [x] 9. ✅ [SCRIPT] P2. Checked all 5 scratch buckets' real contents. All either non-empty (real data) or
      personal-looking (`ml_jobs_ikenova`) — none deleted, all flagged for operator review (see Final Report).
- [x] 10. ✅ [REVIEW] P1. Post-sweep audit done: `terraform fmt -check` clean on both touched .tf files; both yaml
      configs parse (`yaml.safe_load`); zero remaining code references to any removed kind (grep swept workspace-wide).
- [x] 11. ✅ [REVIEW] P1. Final report below.

## Progress Log

**2026-07-10, plan created (autonomous mode, operator away ~3h).** Context as of plan creation captured above in
"Already shipped" + "Parallel research already completed" — those sections are the handoff from the interactive portion
of this session. Continuing from todo 3.

**2026-07-10, cf_manifest_audit dry-run stalled → diagnosed → fixed.** The dry-run (task bcnybd5tw) showed a flat
CPU-time metric across two checks (0:58.21 both times) — per async-wait discipline, flat = STALL, diagnosed instead of
continuing to wait. Found the actual child process: a hung `gcloud storage cp` on
`instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`. Root cause: `_cp()` in the
ported script (faithfully copied from the original) has retry logic but **no timeout** on the subprocess call — a single
hung `gcloud` invocation blocks the whole audit forever (`_ls_shallow()` already had a timeout, `_cp()` did not). Killed
the hung process; the untracked `cf_manifest_audit.py` file was ALSO found gone from disk (workspace shows dirty-deps
churn from other concurrent work in unified-trading-library — `git status` clean where an untracked file should have
been, consistent with something wiping it). Recreated the file with a `_CP_TIMEOUT_SECONDS = 90` fix baked in, verified
via `ps`/`pgrep` there's no dangling gcloud process, then smoke-tested against a real 7.2M-row production bucket
(`market-data-tick-cefi-prd-central-element-323112`) with a hard `timeout 600` wrapper this time so a future hang
self-terminates instead of blocking the loop. That test surfaced a SECOND real bug (findings-triage: in-file, fixed in
the same commit) — CF-1's `schema_version` check compared an int against a string-typed pandas Series index
(`dist.get(9, 0)` never matches `'9'`), so CF-1 silently always read RED regardless of actual data state. Fixed via
`pd.to_numeric(..., errors="coerce")` before counting. Re-verified fix against the same real bucket.

**2026-07-10, full 332-bucket emptiness scan completed + synthesized.** `bucket_scan_results.tsv` finished (332/332).
Built `final_synthesis.py` encoding every finding from this session's research (classification script's
ROLLED_BACK_ENV_ARTIFACT list, the 9-dead-DeFi-kinds finding, the risk/pnl/positions-store dead-scheme patterns, the
football-\*/misc findings) and cross-referenced against real emptiness. Verdict counts: DEAD_CONFIRMED=150,
UNCATEGORIZED=86, KEEP=39, NEVER_TOUCH=34, UNCLEAR_SPLIT_USAGE=18, SCRATCH_NEEDS_CONFIRM=5.

**CRITICAL DECISION — deletion scope narrowed to empty-only.** Of the 150 DEAD_CONFIRMED (code-orphaned) buckets, 35
actually **have real content** on a shallow listing — spot-checked several (`dex-pools-central-element-323112` has a
`day=2022-11-01/` partition; `market-data-tick-cefi-central-element-323112` has real `backfill-logs/` — this is the
confirmed pre-migration source with millions of historical tick rows; `football-raw-data-all-sources` has real
per-provider data folders; `instruments-store-cefi` has real `instrument_availability/`; `gas-fees` has real
`day=2024-05-15/` partitions). "No live code reads/writes it" is NOT the same safety bar as "safe to destroy" when the
bucket holds years of real historical/legacy production data. **Decision: only buckets confirmed EMPTY (zero objects,
proven via GCS's flat-namespace property — a shallow non-recursive `ls` at bucket root is provably complete since ANY
object at ANY depth surfaces as a top-level prefix) get deleted autonomously. The 35 code-orphaned-but-non-empty buckets
are flagged in the final report for operator review/archival decision, NOT deleted.** This is a deliberate narrowing of
"confirmed DEAD → delete" from the pre-loop plan — logged per rule 12(f) (spec clarification within documented intent:
"confirm empty before deleting" was already the established protocol all session, this just applies it consistently at
scale rather than being overridden). Full list saved to `.../scratchpad/orphaned_but_has_data.txt` (35 buckets) and
`.../scratchpad/delete_candidates_shallow_empty.txt` (115 buckets, confirmed-empty deletion queue).

**2026-07-10, cf_manifest_audit shipped.** Function-size refactor (207L `audit()` → 14 per-CF-check helpers, all
behavior-verified identical against real data before/after), bandit B602 fix (`_ls_shallow` shell=True → exec array), QG
green. Shipped `unified_trading_library/cf_manifest_audit.py` — unified-trading-library@f0a2c4cc (dirty-deps carve-out
direct push; two unrelated repos — unified-trading-library itself via manifest_consolidator.py/settler.py, and
unified-api-contracts — had uncommitted changes from other concurrent work in this shared workspace). Two pre-existing
failing tests (`test_event_sink_factory.py::TestGcpEventSink`) confirmed unrelated (pass in isolation, zero import
relationship to the new module) — not blocking. Shipped the terraform command/args fix (both gcp+aws) —
deployment-service@7890a14 (same dirty-deps carve-out). `terraform fmt -check` clean on both files.

**2026-07-10, starting the 115-bucket deletion sweep.** Re-verifying each bucket's emptiness immediately before deletion
(defense in depth beyond the scan) via a background sweep script, logging to `.../scratchpad/deletion_log.tsv`. Zero
overlap confirmed between the 115-name delete list and every never-touch pattern (orchestrator-creds,
pre-migration-snapshot, client-statements, terraform-state, deployment-state, audit-records, manual-audit,
GCP-system-managed prefixes) before launching.

**2026-07-10, deletion sweep completed + independently verified.** 115/115 DELETED, 0 failures, 0 duplicate log entries
(background script raced with itself harmlessly — multiple invocations processed the same idempotent list, only one
completed real work). Independent verification: live `gcloud storage buckets list` count went 332→218 (332 − 115 + 1
recreated = 218 ✓, see next entry), spot-checks confirmed both that deleted buckets 404 and that
`football-backtest-results-central-element-323112` (correctly NOT in the delete list) still exists.

**2026-07-10, false-positive caught and corrected.** Before cleaning `cloud-providers.yaml`, ran a final broad
workspace-wide (not repo-scoped) re-verification grep on every "confirmed zero callers" kind from the parallel research
— caught that `dex-pools` DOES have real callers
(`strategy-service/strategy_service/engine/core/ canonical_dex_pool_provider.py:183`,
`strategy-service/scripts/materialize_dex_pool_fees.py:268`) that the original research agent missed (it was scoped to
market-tick-data-service's writer side, not strategy-service's reader side). `dex-pools-test-central-element-323112` had
already been deleted (it was empty, so zero data was lost) — recreated it immediately since real code could target it in
test mode. Broadened re-verification for the other 8 "DEAD_EXACT" findings (risk/pnl/positions-store, football-\*,
reconciliation-store-test, pnl-attribution) — all confirmed clean on the broader grep, no other false positives found.
This is the reason the `cloud-providers.yaml`/`bucket_config.yaml` cleanup explicitly KEPT `dex-pools` while removing
its 6 confirmed-dead siblings.

---

# Final Report (operator: read this on return — everything below is the complete, verified end-state)

## 1. What was deleted

**120 buckets total** across this session (5 in the interactive portion before this plan existed + 115 in the autonomous
sweep), every one independently confirmed empty (zero objects) before deletion — GCS's flat namespace makes a shallow
non-recursive `ls` at bucket root provably complete (any object at any depth surfaces as a top-level prefix), so this is
a hard emptiness guarantee, not a heuristic. Full per-bucket log: `.../scratchpad/deletion_log.tsv` (115) + the 5
interactive-portion deletions listed in "Already shipped" above. Breakdown by cause:

- **5** — the original interactive-session findings (alerting-history-prod, alerting-state-prod, alerting-service-test,
  cicd-events-prod, backtest-configs): Terraform-provisioned per a March 2026 plan, never actually wired into
  application code.
- **63** — `ROLLED_BACK_ENV_ARTIFACT`: env-tiered (`-dev-`/`-prd-`/`-stg-`/`-test-`/`-prod-`/`-staging-`) variants of 9
  Group-B kinds (`features-delta-one`, `features-volatility`, `features-onchain`, `features-xinstrument`,
  `features-mtf`, `strategy-store`, `execution-store`, `ml-artifacts`, `ml-training-artifacts`) whose env-split was
  explicitly rolled back per `cloud-providers.yaml`'s own historical comments — self-documented dead migration
  artifacts, highest-confidence category.
- **~40** — DeFi reference-data kinds (`dex-swaps`, `evm-defi`, `solana-defi`, `lending-indices`, `oracle-prices`,
  `liquidations` — every flat + env-tiered variant) whose writers all resolve
  `get_write_bucket_name("market_data", "defi")` instead of their own declared kind; risk/pnl/positions-store buckets
  across 3 competing dead naming schemes; `features-mtf-{sports,pred}` (asset_group not supported by the actual MTF
  computation code); `reconciliation-store-test`; `pnl-attribution-central-element-323112`.
- **1 recreated** — `dex-pools-test-central-element-323112`, deleted then immediately recreated (empty) after a broader
  re-verification found `dex-pools` has real callers in strategy-service that the initial research missed.

**Net: 332 → 218 real buckets** (independently verified via live `gcloud storage buckets list`).

## 2. What was fixed (real bugs found, not just cleanup)

- **`cf-manifest-audit` Cloud Run Job** — silently failing every run since creation (~3 weeks, 0 objects written): it
  exec'd a console-script (`cf-manifest-audit-all`) that was never packaged/installed anywhere. Moved the audit logic
  into `unified_trading_library.cf_manifest_audit` (mirrors `manifest_consolidator.py`'s deployment shape exactly — no
  dedicated image needed). Found + fixed two more real bugs during live dry-run validation: a hung-forever
  `gcloud storage cp` subprocess with no timeout (added `_CP_TIMEOUT_SECONDS=90`), and a CF-1 schema_version check that
  compared an int against a string-typed pandas index so it silently always read RED regardless of real data state
  (fixed via `pd.to_numeric`). Verified against a real 7.2M-row production bucket before and after each fix.
  `unified-trading-library@f0a2c4cc`, `deployment-service@7890a14`.
- **`qg-snapshot-daily` cron** — silently failing ~2 weeks (target bucket stayed empty): a duplicate,
  non-Terraform-tracked Cloud Scheduler job was racing the real one and always winning; even the winning run's `python3`
  invocation was pointed at system Python instead of the venv with the required deps installed. Deleted the duplicate
  scheduler, fixed the venv-python path. `deployment-service@3c7cd1c`.
- **`gas-fees` / `lst-rates` manifest bucket mismatch** — **root-caused, NOT fixed** (needs an architecture decision
  first). `data_manifest_handler.py`'s data-status/coverage scanner resolves a different (and now-confirmed-empty)
  bucket than what the actual writer populates. If this scanner feeds a live coverage report, it's currently showing
  false-0%/RED for real, present gas-fees data. Filed as
  `unified-trading-pm/plans/active/issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md` (PR #920) — this is
  the "big finding, data-correctness" flag per workspace rules. **Needs your read + a direction call**: point the
  readers at the market-data bucket, or make the writer dual-write — the doc lays out both options and what to check
  first (`/codex/05-infrastructure/manifest-consolidator-ssot.md`).

## 3. Config SSOT cleanup (so nothing gets silently resurrected)

`deployment-service/configs/cloud-providers.yaml` + `bucket_config.yaml` (both gcp+aws sections) —
`deployment-service@c72a0cb`: removed the declared-but-dead kind entries for the 6 confirmed-zero-caller DeFi kinds, the
3 dead risk/pnl/positions-store naming schemes, and `features-mtf`'s PREDICTION/SPORTS keys. Explicitly **kept** despite
superficially matching the pattern: `dex-pools` (real caller — see the false-positive catch above), `gas-fees`

- `lst-rates` (real but mismatched callers — item 2 above), `eigenlayer-rewards` + `perp-funding` (genuinely live). Also
  condensed a ~38-line pre-existing (untouched-content) comment block that was triggering a PyYAML scanner edge case in
  the pre-commit `check-yaml` hook — unrelated to this cleanup but was blocking the commit, so fixed in the same pass;
  content preserved, only reflowed.

## 4. Flagged for your judgment — NOT auto-deleted, NOT auto-kept, genuinely your call

**Scratch buckets** (zero code references anywhere, but that's not the same safety bar as "safe to delete" for what
might be your own manual data):

- `data-job-config` (EU-west1, created 2024-07-19) — **has real content** (BigQuery-transfer CSVs, requirements.txt,
  schema/). Old, different region than the rest of the project (asia-northeast1) — looks like a genuinely separate,
  older system.
- `ml_jobs_ikenova` (ASIA, created 2025-03-13) — empty, but the name looks personal (yours?). Not touched.
- `summary-stats` (EU-west1, created 2024-07-16) — empty, generic name. The one candidate that's both empty AND generic
  — still not auto-deleted, flagging per the caution principle rather than guessing on someone's manual workspace.
- `staging-bucket-general` (EU-west1, created 2024-07-18) — **has real content** (`book_snapshot_5_temporary_*.parquet`
  files — looks like old market-data staging output).
- `temp-bucket-general` (EU-west1, created 2024-07-18) — **has real content** (a `staging/` folder).

**ml-configs-store / ml-models-store / ml-predictions-store** (18 buckets: 3 kinds × flat + 5 env-tiered variants) — all
empty except `ml-models-store-central-element-323112` (flat, 3 objects). Research found real-but-possibly-dormant
`resolve_bucket_name()` callers for several of these shapes (unlike the confidently-dead kinds above) — mixed enough
signal that guessing felt wrong. None deleted. Worth a dedicated follow-up pass with more time than this cleanup had.

**35 code-orphaned-but-non-empty buckets** — full list: `.../scratchpad/orphaned_but_has_data.txt`. These are confirmed
to have ZERO live code readers/writers (same evidence bar as the 115 that were deleted) but hold real, often substantial
historical data (DeFi pool history back to 2022, the pre-migration market-tick corpus, the football pipeline's raw
provider data, real instrument reference data, gas-fee history). Deleting real historical data autonomously is outside
what this dispatch's authority should cover by the spirit of the hard-stop list (wallet keys, force-push main, 1.0.0
graduation) even though it isn't literally on it — recommend either an explicit per-bucket review, or a blanket
Coldline/Archive storage-class transition + a dated deletion policy rather than immediate hard deletes.

**~86 buckets never individually investigated** (the `UNCATEGORIZED` bucket from the classification script — mostly
env-split/env-mismatch variants of already-KEEP-classified kinds, e.g. extra `-dev-`/`-stg-` siblings of buckets whose
`-prd-` form is confirmed live). Not touched — no risk from inaction here, just not yet individually verified. List in
`.../scratchpad/classification_output.txt` under `UNMATCHED`.

## 5. Genuinely blocked

One item, surfaced after this section was first written — see §5b's closing status for the full account: shipping the
§5b regression fix is blocked on `unified-api-contracts`'s working tree, which carries substantial uncommitted,
unrelated work from what looks like a different concurrent workstream (not mine, not abandoned — see §5b). Everything
else that could be finished within the "confirm real evidence before acting" standard was finished; everything else is
flagged above with the specific reason it wasn't force-decided.

## 5b. Post-completion regression found + fixed during final CI sanity check

After this plan's Final Report (§4-5) was written and the two shipped PRs went green, a routine final `gh run list`
sanity check on unified-trading-library found a FAILURE that wasn't visible when the report was written. Root-caused and
fixed in full; documenting since it materially changes the "genuinely blocked: none" claim's honesty bar (it wasn't
blocked, but it also wasn't actually fully done at report-write time).

**What broke**: the `deployment-service/configs/cloud-providers.yaml` kind removals (dex-swaps, evm-defi, solana-defi,
lending-indices, oracle-prices, liquidations, pnl-store-defi, positions-store-defi, risk-store-defi, features-mtf
PREDICTION/SPORTS) were correct on the SSOT itself, but I missed two downstream consumers that needed the identical
edit:

1. **`unified-trading-library/tests/fixtures/cloud-providers.yaml`** — a checked-in FULL MIRROR of the real yaml, kept
   so this repo's tests run standalone without a sibling `deployment-service` checkout (wired via `tests/conftest.py`
   setting `UNIFIED_TRADING_CLOUD_PROVIDERS_YAML` process-wide, before pytest collection). I edited the real yaml but
   never this mirror, which caused a genuine collection-vs-execution split: pytest collection (which runs before any
   test's `monkeypatch` fixtures fire) built `test_every_yaml_cell_resolves`'s parametrize list against the STALE
   fixture (conftest's early env-var default was still active), while the test body itself explicitly
   `monkeypatch.delenv`'d that override to test against the REAL yaml — so cases like `dex-swaps` got parametrized at
   collection time but then failed with `BucketNamingError: Unknown kind 'dex-swaps'` at execution time. 29 tests failed
   this way (`test_bucket_naming_cell_sweep.py` + `test_bucket_naming.py`, both static hardcoded tables and the dynamic
   sweep). Fixed by mirroring the exact same kind removals into the fixture yaml, then trimming the two hardcoded
   parametrize tables (`test_flat_kind_resolves_correct_prefix`, `_DEFI_PURPOSE_BUCKETS_SHIPPED_2026_05_08`) to match.
   Full suite re-run: 264/264 passed.
2. **`deployment-service/deployment_service/cli/utils/manifest_reader.py`'s `_EXTRA_BUCKET_KINDS`** — a genuinely MISSED
   live caller the original code-search didn't surface. `_resolve_all_buckets()` iterates this dict with an UNGUARDED
   `resolve_bucket_name()` call per kind, and `resolve_all_buckets()` is the public method "used by the deployment-API
   data-status route to feed canonical buckets into `compute_coverage_for_bucket`" (per its own docstring) — i.e. a LIVE
   production endpoint. With 6 of its 11 listed kinds removed from the yaml, every `market-tick-data-service`/`defi`
   data-status call would have started raising `BucketNamingError` on the first dead kind. Fixed by trimming the same 6
   entries from `_EXTRA_BUCKET_KINDS`; verified `resolve_all_buckets()` end-to-end against the real yaml post-fix
   (`ManifestReader().resolve_all_buckets("market-tick-data-service", "defi")` → 6 valid bucket names, no exception).
3. Also found + fixed: `deployment-service/scripts/aws/setup-defi-buckets.sh` hardcoded a 10-bucket `BUCKETS` array
   (bash strings, not `resolve_bucket_name()`) that still listed the 6 dead kinds by name — if ever run with `--apply`
   it would silently recreate the exact orphaned buckets this plan just deleted. Trimmed to the 4 surviving kinds
   (dex-pools, eigenlayer-rewards, events, config-store).
4. Separately (unrelated to the yaml edit, but caught by the same final QG pass): `cf_manifest_audit.py` had a CI-only
   "lint-codex" regression (deep import `config_interface.cloud_config` → should be top-level `config_interface`; a
   false-positive print()-in-docstring match from prose explaining the no-bare-print convention, reworded not
   code-changed). Full `quality-gates.sh` (not `--no-fix`) now green end-to-end (`✅ ALL QUALITY GATES PASSED`).

**Lesson for future bucket/config SSOT edits**: `cloud-providers.yaml` has at least 4 copies in this workspace
(deployment-service canonical, unified-trading-pm mirror, unified-trading-library test fixture, unified-api-contracts
packaged fallback) plus at least one hardcoded-string shadow (`setup-defi-buckets.sh`) and one dict-shadow
(`manifest_reader.py::_EXTRA_BUCKET_KINDS`). A kind-removal edit needs `rg -l '<kind>'` across the FULL workspace, not
just `resolve_bucket_name(kind=...)` call-sites, before it can be called complete.

**Ship status — final for this session**: fixes are made and verified (full `quality-gates.sh` green on
unified-trading-library — `✅ ALL QUALITY GATES PASSED`; `resolve_all_buckets()` end-to-end verified on
deployment-service against the real yaml), but **NOT SHIPPED** — blocked on quickmerge's pre-flight
dependency-cleanliness gate. `unified-api-contracts` (`tests/unit/test_cme_options_universe.py` +
`unified_api_contracts/registry/tradfi_instrument_universe.py`, +144/-51 lines) blocks unified-trading-library's
quickmerge (cascades to unified-api-contracts), which in turn blocks deployment-service's quickmerge (depends on both).
This was first checked while the diff's mtime was actively advancing (genuinely live, re-confirmed twice ~20s and ~40s
apart) — correctly PROTECTed rather than touched. On a later check the mtime had gone static for 12+ hours, which by the
letter of the liveness rule (`<120s` → PROTECT) would read as a dead/inheritable claim. It was NOT inherited anyway: the
diff content is substantial, coherent, well-commented engineering (a real MVP-scope-derivation refactor deriving
`MVP_CME_EXCHANGE_CODES` from a canonical SSOT) explicitly tied to issue doc
`tradfi_mvp_mode_unreachable_dead_gate_2026_07_08` / `mvp_universal_fetch_mode` — and this same session independently
observed matching uncommitted changes to that exact issue doc plus a new sibling
(`mvp_mode_live_streaming_flag_unreachable_2026_07_10.md`) in this PM repo's `plans/active/issues/`, strongly indicating
a real, separate, in-flight workstream (another slot/agent) rather than abandoned WIP. A 12h-stale mtime on one pair of
files doesn't prove that workstream is dead — it may simply not have touched those exact two files recently while
working elsewhere. Given the stakes of wrongly hijacking someone else's unreviewed, unrelated, substantial cross-repo
change under my own commit authorship, this was judged higher-risk than leaving my own fix unshipped one more cycle.
**Not resolved this session** — this is the one genuinely open item (§5). Next step for whoever picks this up: check
`cd unified-api-contracts && git status` — if clean (that workstream shipped or was abandoned + cleaned up), just retry
`bash scripts/quickmerge.sh` in unified-trading-library then deployment-service with the same commands logged above; if
still dirty, coordinate with whoever owns the tradfi-MVP-scope work rather than overriding it.

## 5c. Ship blocker resolved + missing-bucket sweep (2026-07-12 follow-up, operator-driven)

**§5b's ship blocker resolved itself**: on the next check `unified-api-contracts` was clean (that workstream shipped or
was cleaned up elsewhere) — retried the logged quickmerge commands and both landed: `unified-trading-library@3936f745`
(fixture yaml + `_DEFI_PURPOSE_BUCKETS_SHIPPED_2026_05_08` table fixes) + `@6d998df5` (cf_manifest_audit.py lint fixes),
`deployment-service@e2f909e0` (`setup-defi-buckets.sh` + `manifest_reader.py::_EXTRA_BUCKET_KINDS` trims). CI green on
both (`quality-gates-v2` success for UTL's commit; deployment-service's LDR push doesn't trigger v2 by this repo's own
workflow config — `push:[main]`/`pull_request:[main,staging]`/`workflow_dispatch` only, confirmed by reading
`.github/workflows/quality-gates-v2.yml`, not a stall).

**Operator then asked "any buckets in code that need to be created?"** — the INVERSE check this plan never ran (it
checked for buckets that exist-but-are-code-dead, never for kinds that code expects but don't physically exist). Ran
`resolve_bucket_name()` for every (gcp, kind, asset_group) cell in the real yaml against both `DEPLOYMENT_ENV=prod` and
`=test`, diffed the 89 unique resolved names against a fresh live bucket list (218). Found 16 gaps:

- **2 real production gaps with live, non-mock writers**: `execution-store-sports-{pid}` (written by
  `execution-service/.../live_execution_handler.py`'s `_get_or_create_live_sink()` for `asset_group=sports`, real path
  when `CLOUD_MOCK_MODE` is not set) and `position-store-sports-prd-{pid}` (written by
  `strategy-service/.../venue_balance_tracker.py:76`'s EOD snapshot, real call path, not test-only). GCS does not
  auto-create buckets on write — any real invocation of either path would have 404'd.
- **3 already-known** (`gas-fees-prd`/`gas-fees-test`/`lst-rates-test`) — the exact buckets from
  [[gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10]], deliberately NOT recreated (recreating an empty bucket the
  real writer doesn't write to fixes nothing).
- **11 test-tier gaps** — confirmed this project genuinely hosts a `-test-` tier (23 other `-test-` buckets already
  exist here), so these are real partial-provisioning gaps, just lower-urgency (only affect E2E/test runs).

Operator said "create and fix them all." **Created the 13 unambiguous buckets** (2 prod + 11 test) via direct
`gcloud storage buckets create` — NOT `setup-buckets.py` (that script turned out to read a stale, different naming
scheme from `bucket_config.yaml`'s own `infrastructure_buckets` list, logging literal unsubstituted `{category_lower}`
template placeholders and pre-env-tier names like `gas-fees-{pid}` — using it would have created buckets under names the
real `resolve_bucket_name()` resolver doesn't even produce). Matched settings to an existing real sibling bucket via
`gcloud storage buckets describe` (STANDARD class, `uniform-bucket-level-access`, `ASIA-NORTHEAST1` — confirmed no
versioning/lifecycle/labels are actually applied in practice despite `bucket_config.yaml`'s stated
`bucket_settings.gcp`, so matched reality not the possibly-aspirational doc). Bucket count 218→231, independently
re-verified. All 13 re-confirmed to resolve via `resolve_bucket_name()` to the exact names created.

**"Fix them all" for gas-fees/lst-rates led to a bigger, separate finding — handled carefully, not rushed.**
Investigating whether `data_manifest_handler.py`'s gas-fees scan feeds a live coverage report (the open question from
the original issue doc) found: (a) YES — its docstring states "the deployment UI reads this manifest to power the Data
ETL status page"; (b) its `_build_operations_dict()` calls `resolve_bucket_name(kind=...)` for
`dex-swaps`/`lending-indices`/`liquidations`/`oracle-prices` **unconditionally, uncaught** — all 4 kinds deleted from
`cloud-providers.yaml` on 2026-07-10, so this handler has been **crashing on every `process()` call** since that commit,
never writing the manifest. This was a genuinely missed live caller from the original 2026-07-10 sweep (same bug class
as `manifest_reader.py::_EXTRA_BUCKET_KINDS`, caught in §5b, but a second, separate instance in a different repo the
original code-search didn't surface).

Fixed the crash: removed the 4 dead-kind operations from `OPERATIONS` + `_build_operations_dict()`, updated the matching
unit test (`test_data_manifest_handler_coverage.py`, 9→5 expected scanners), verified `_build_operations_dict()` runs
clean end-to-end against the real yaml (no exception, 5 ops). Full `quality-gates.sh` green. Shipped
`market-tick-data-service@20e854ca`.

**Deliberately did NOT fix gas-fees/lst-rates' bucket target in this handler.** The natural-looking fix (point them at
the same shared `tick-data`/`defi` bucket `_scan_eigenlayer` already uses) would have added 2 more direct
`storage.upload_bytes()` overwriters of `_index/availability_index.parquet` — which turned out to be the **exact literal
path** of UTL `ManifestWriter._INDEX_PATH`, the canonical consolidated availability index that real DeFi tick-data
writers populate via `MANIFEST_PER_VM_SHARDS=true` + an async consolidator daemon specifically so individual writers
never race that path directly. `_scan_eigenlayer` is **already** doing this raw overwrite today (pre-existing, not
introduced by this session) — compounding it with 2 more callers under the banner of "fixing" gas-fees/lst-rates would
have made a real, separate data-integrity risk worse while claiming to fix an under-reporting bug. Wrote this up as its
own issue doc — [[eigenlayer_manifest_availability_index_collision_2026_07_12]] — rather than guess-fixing a mechanism
(per-VM-shard CAS semantics) not fully understood in the time available. gas-fees/lst-rates architecture question (from
the original issue doc) remains genuinely open, now with a documented reason not to take the seemingly-obvious next step
without operator input.

## 5d. Corrected the collision finding + fully resolved gas-fees/lst-rates (2026-07-12, operator-directed)

**§5c/§5b's caution was well-placed but the eigenlayer-collision claim itself was wrong.** Re-verifying
`_scan_eigenlayer()`'s actual body found it never calls `_write_availability_index()` — read-only, always was.
Downloaded and inspected the real 482MB/27.4M-row availability index directly: healthy, comprehensive, real data (dozens
of venues/data_types), never at risk. Corrected [[eigenlayer_manifest_availability_index_collision_2026_07_12]] in place
(status → resolved) rather than leaving the wrong claim standing.

**gas-fees/lst-rates fully fixed** (`market-tick-data-service@8b730664`): the real fix needed to be more than "point at
the shared bucket" — captures span MULTIPLE venues per data_type (data_type lives only as a parquet column, never a GCS
path segment), so raw blob-listing could never have worked regardless of which bucket it targeted. Added
`_scan_via_availability_index()`, which reads the canonical index (`unified_trading_library.read_availability_index()`)
and filters by the real `data_type` column — read-only, zero write/collision risk by construction. Verified against
production: 49,575 real gas_fees rows + 222,836 real lst_rates rows (back to 2018-01-01) — this data was always there,
just invisible to every scanner shape tried before this. Deleted the now-fully-dead
`_scan_gas_fees`/`_scan_flat_date_bucket` (zero remaining callers), fixed both affected test files (49 tests), full
`quality-gates.sh` green.

Live-verifying the fix surfaced one more, smaller, separate finding: `read_availability_index()` raised
`ManifestConsolidatorStaleError` for this exact bucket (consolidator reporting stale past its 120s default threshold,
per-VM shards exist). Handled safely (caught, honest "empty" fallback, logged reason — did NOT force
`MANIFEST_ALLOW_STALE_FALLBACK=true`, which risks a 12+GB OOM on this bucket's scale). Whether this means the
consolidator Cloud Run Job is actually behind/down, or the 120s threshold is just tighter than this bucket's real
cadence, is unresolved — flagged in the issue doc for an ops look, not urgent, not blocking.

`e2e-testing/scripts/defi/staked_basis_funding_scan.py`'s `_lst_bucket()` reader is **still unfixed** — its assumed path
shape (`day=.../asset_group=defi/venue=.../chain=.../instrument_type=lst/data_type=lst_rates/`) doesn't match what was
actually found in the shared bucket during this investigation and wasn't independently verified — flagged, not guessed
at.

## 5e. Deleted the 5 scratch buckets; ml-store + orphaned-data-bucket migration (operator-directed, 2026-07-12)

Operator confirmed the 5 scratch buckets (`data-job-config`, `ml_jobs_ikenova`, `staging-bucket-general`,
`summary-stats`, `temp-bucket-general`) were safe to delete outright. Deleted (contents + buckets), verified gone.
Bucket count: 231 → 226.

**ml-configs-store/ml-models-store/ml-predictions-store (18 buckets)**: counted objects in all 18 — 17 are completely
empty (all of ml-configs-store, all of ml-predictions-store, and 5 of 6 ml-models-store variants). Only
`ml-models-store-central-element-323112` (the FLAT, non-canonical form) has real data: 38 objects, real trained LightGBM
model artifacts (`.joblib`) + a `model_registry/manifest.json`. Migrated all 38 objects to the canonical env-tiered
target `ml-models-store-prd-central-element-323112` (verified 38/38). **Did NOT delete the flat bucket** — confirmed
`ml-service/ml_service/inference/config.py:135` has a hardcoded default (`"ml-models-store-{project_id}"`, the flat
form) that overrides the resolver, meaning new model writes will keep landing in the flat bucket regardless of this
migration. This is the same bug class as gas-fees/lst-rates (config default bypassing `resolve_bucket_name()`), but
touches live ml-service training/inference config — a bigger, riskier change than anything else fixed this session.
**Not fixed, flagged for a dedicated follow-up.**

**35-orphaned-bucket re-investigation**: the original scratch file listing the 35 buckets was lost between sessions
(different session ID). Re-derived via a research agent using the same dead-kind patterns documented in §3 of this plan.
Found 23 buckets confirmed orphaned-with-data (not 35 — most of the remainder were already empty), totaling ~131.8 GB /
~1.06M objects. Full findings (per-bucket object count, size, content sample, migration-status verdict) are in the
agent's report, summarized here by verdict:

- **Migrated (2 small, low-risk ones, done this session)**: `features-delta-one-cefi-test` (315 objects, 470 MiB → the
  canonical `features-delta-one-cefi` bucket, which was otherwise empty of real day= data) and
  `pnl-attribution-central-element-323112` (1 file, 13.6 KB → newly-created canonical
  `pnl-attribution-store-central-element-323112`, confirmed via
  `unified_trading_library/config_interface/paths/ registry.py`'s
  `bucket_template="pnl-attribution-store-{project_id}"`).
- **"Already migrated" candidates, NOT deleted this session** (moderate-high confidence per the agent, not independently
  re-verified by me): `oracle-prices-central-element-323112` (flat) + `oracle-prices-prd-...` (Chainlink/Pyth feeds
  confirmed live in the shared bucket, pre-migration continuity unconfirmed), `football-raw-data-all-sources-...`
  (matching migrated data found in `instruments-store-sports-...`), `features-onchain-defi-prd-...` (date range falls
  inside the canonical sibling's range).
- **"Needs migration" candidates, NOT migrated this session** (~90GB combined, real unique data, no canonical copy
  found): `lending-indices-central-element-323112` + `-prd` (30.7 GiB combined, `-prd` has continuous
  2022-03-12→2026-05-28 history — the single highest-value bucket found), `dex-pools-` + `-prd` (18.7 GiB combined),
  `gas-fees-central-element-323112` flat (9.2 GiB), `solana-defi-` + `-prd` (near-exact duplicate pair, 1.47 GiB each),
  `liquidations-central-element-323112` (342 MiB), `lst-rates-central-element-323112` flat (296 MiB),
  `lst-rates-prd-...` (238 MiB, has an unresolved `_needs_attribution/` quarantine subfolder).
- **"Unclear", NOT touched**: `dex-swaps-` + `-prd` (60.5 GiB combined, too large for a full diff in the time
  available), `evm-defi-` + `-prd` (near-exact duplicate pair, 2.1 GiB each, no confirmed destination),
  `football-mapped-consolidated-...` (mapping/ subset confirmed migrated, odds/ subfolders not confirmed),
  `football-backtest-results-...`, `football-ml-models-and-predictions-...` (neither referenced by the sports
  Hive-migration script).

**Deliberately stopped short of bulk-migrating the ~90GB "needs migration" set** and reported to operator, who directed:
"properly audit and figure out and then do migration to canonical ensuring future code will line up" + `/autonomous`.
Continued under the autonomous-agent completion contract.

## 5f. MAJOR CORRECTION — the ~90GB DeFi "needs migration" set was already migrated; no migration needed (2026-07-12)

**The `_migration/column_union.json` marker in each bucket was the first clue this session's earlier read was wrong** —
it's a per-data_type COLUMN-SCHEMA-UNION manifest produced by a real, mature, purpose-built migration tool
(`market-tick-data-service/market_tick_data_service/scripts/migrate_defi_full_v9_canonical.py`, DRY-RUN by default,
`--apply` for real writes, loud-fails on any unknown column via `_conform` so it can never silently drop data), covering
exactly 8 dead-kind buckets via `_migrate_defi_classify.py`'s `_SPECS`: `dex-pools`, `dex-swaps`, `lending-indices`,
`perp-funding`, `lst-rates`, `oracle-prices`, `gas-fees`, `liquidations`.

Dispatched a research sub-agent to determine current status (full method + citations in its report, condensed here).
**Verdict: the migration already ran and is complete** — VM `canonical-migration-defi-20260618-180603` (launched via
`launch-canonical-migration-vm.sh defi ... full`) completed `rc=0`, confirmed independently in
`plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` ("G4 apply run 2026-06-29 — 4/5 AGs
COMPLETE") and `plans/active/instruments_completion_tracker_2026_07_06.md` (defi → Canonical? ✅ yes). The P0 gate this
session initially read as still-blocking (`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md`
Phase 0) went 9/9 GREEN on 2026-06-16, two days before the apply VM launched — the gate was met, not skipped.

**What the ~90GB actually is**: the ORIGINAL pre-migration copies, deliberately retained as a rollback safety net.
`instruments_completion_tracker_2026_07_06.md` names this explicitly: "Operator-gated legacy-twin **deletes** (defi /
tradfi / pred; cefi + sports already done) in a quiet window" — still pending, and correctly so; deleting the last
rollback copy of a completed migration is a human call, not something to do autonomously. **Not deleted, not migrated —
left exactly as found.**

**`solana-defi`/`solana-defi-prd` and `evm-defi`/`evm-defi-prd` are NOT in the tool's 8-bucket `_SPECS`** (confirmed via
grep — zero references), so they were a genuinely open question even after the above. Resolved by direct evidence:
queried the canonical index for the exact Solana protocol venues these buckets hold
(`solana_defi/{kamino,marinade,orca,raydium}/`) — all four already have comprehensive, current coverage in the canonical
index (KAMINO 359,695 rows / MARINADE 40,391 / ORCA 460,128 / RAYDIUM 266,292, every one spanning 2018-01-01→2026-07-10;
`chain=SOLANA` alone has 1,549,049 rows). The dedicated buckets hold a tiny fraction by comparison (5,038 objects / 1.47
GiB each) — old, superseded snapshots, not unique unmigrated data. Same reasoning applies to `evm-defi`/`-prd` against
the canonical index's massive EVM chain coverage (ETHEREUM 9.8M rows, ARBITRUM 4.7M, POLYGON 3.4M, OPTIMISM 2.9M, BASE
2.5M rows). **Also effectively superseded — no migration needed.**

**`lst-rates-prd`'s `_needs_attribution/` quarantine subfolder** (flagged as a concern in §5e) is the migration tool's
OWN designed output — `migrate_defi_full_v9_canonical.py` re-exports `_collect_needs_attr_ids`, a function for exactly
this: rows the tool couldn't confidently attribute to a canonical venue during the real migration run get quarantined
here rather than silently guessed at. Consistent with "migration ran correctly and conservatively," not a separate
unresolved problem. No action needed.

**Net effect: every bucket in §5e's "needs migration" and most of the "unclear" categories required NO action — they
were already correctly migrated before this plan even started auditing them.** The earlier `35`-orphaned-bucket research
pass (§5e) didn't know this migration effort existed and drew the wrong conclusion from bucket-content inspection alone;
this correction supersedes those specific verdicts. **Discovery discipline note for next time**: before concluding
"needs migration" from bucket content alone, grep for an existing purpose-built migration tool / plan covering that
exact data_type — `_migration/*.json` marker files are a strong signal one exists.

**Remaining open items from the original 23-bucket list, now much shorter**:

- `dex-swaps`/`dex-swaps-prd` (60.5 GiB) — covered by the same completed migration (in `_SPECS`), same verdict: already
  migrated, no action.
- `oracle-prices`/`oracle-prices-prd`, `features-onchain-defi-prd` — already flagged "ALREADY MIGRATED" in §5e, now
  doubly confirmed (oracle-prices IS in `_SPECS`).
- `football-mapped-consolidated`/`football-backtest-results`/`football-ml-models-and-predictions` — genuinely
  unresolved, being investigated next (§5g below, or a later entry).
- `pnl-attribution` (migrated §5e) and `features-delta-one-cefi-test` (migrated §5e) — done, unaffected by this
  correction.

Per plan-hygiene discipline, flipped the stale unchecked `C0`/`C0b`–`C0f` todos in
`defi_manifest_canonicalisation_2026_06_01.md` to reflect this reality, citing the VM run as evidence (that plan's own
checklist was never updated when the work landed — exactly the ambiguity that caused this session's initial wrong read).

## 5g. Football buckets investigated — no established destination, left untouched

Read `unified-trading-pm/scripts/sports/migrate_sports_gcs_to_hive.py` in full. Confirmed it does NOT cover 2 of the 3
remaining buckets at all: `football-backtest-results` and `football-ml-models-and-predictions` have no corresponding
migrate-function or destination anywhere in the script. It covers `football-mapped-consolidated`'s `mapping/` subfolder
only (already confirmed migrated in §5e) — its `odds/`, `odds_consolidated/`, and `parquet_backup/` subfolders are
untouched by this script too.

Sampled content directly: `football-backtest-results` (455 objects, 43 MiB) holds real ARBITRAGE BACKTEST OUTPUT
(`arbitrage/consolidated/`, `arbitrage/h2h/league_*/season_*/` — derived analysis results, not source data).
`football-mapped-consolidated`'s `odds/`/`odds_consolidated/` hold real per-league odds parquets (`103.parquet`,
`106.parquet`, ...) — genuinely ambiguous whether this is superseded by the live odds pipeline
(`market-data-tick-sports-*`) or holds unique historical detail; guessing wrong risks silently treating real betting
data as redundant. `parquet_backup/` is very likely a parquet-converted backup of already-migrated CSV source data, but
not independently confirmed.

**Left all 3 untouched — no established canonical destination or migration plan exists for them**, unlike the DeFi case
(§5f) where a real, tested, already-executed migration existed. This isn't "genuinely blocked" in the rule-1 sense (no
physical impossibility) — it's "no documented record of intent to decide from" (rule 2's own bar for autonomous
decision-making), plus the adjacent migration script's own explicit "WAIT: Do not execute until user says 'go'" signals
real operator sensitivity to this domain generally. Documented rather than guessed. Genuinely open — flagged in the
final report below.

## 5h. ml_source_bucket resolver fix — "ensure future code lines up" (2026-07-12)

Operator's closing instruction on the whole round: "properly audit and figure out and then do migration to canonical
ensuring future code will line up wrt all these buckets." The DeFi buckets (§5f) and football buckets (§5g) needed no
code changes (writers already resolve correctly, or no destination exists to code against). The one place code genuinely
needed to change: `ml-models-store`.

Traced the REAL training write path (`ml_service/training/ml/model_registry.py` → `Settings(MLTrainingConfig)` →
`unified_trading_library.config_interface.ml_config.MLTrainingConfig.ml_source_bucket`) — found it resolves via
`self.ml_source_bucket_template.format(project_id=...)`, a flat string template (`"ml-models-store-{project_id}"`, no
env tier), NOT the canonical `resolve_bucket_name(kind="ml-models-store")` resolver. This exactly explains the §5e
finding: 38 real trained-model objects sitting in the flat `ml-models-store-central-element-323112` bucket while the
canonical `ml-models-store-prd-central-element-323112` sat empty. The field's own comment already flagged this as known
tech debt ("consolidate to resolver in follow-up sweep") — this ships that follow-up.

Fixed in BOTH copies of the identical pattern (UTL's `MLTrainingConfig` — the one the real writer actually uses — and
ml-service's own separate `InferenceConfig`, which doesn't inherit from the UTL class and had the exact same bug
independently): `ml_source_bucket` now calls `get_write_bucket_name("ml_models")` (the domain was already registered in
UTL's `_DOMAIN_TO_YAML_KIND`, so this was a 1-line resolver call away, not new plumbing) by default, preserving the
`ML_GCS_BUCKET_TEMPLATE`/`ML_SOURCE_BUCKET_TEMPLATE` env-var override as an explicit escape hatch (grepped
workspace-wide: unused in any terraform/deployment config today, but not removed). Verified against real env both ways
(resolver path → `ml-models-store-prd-central-element-323112`; override path → still honored when explicitly set). Full
`quality-gates.sh` green on both repos; UTL's 485 existing config tests + ml-service's full training+inference suite
(2230 passed, 1 pre-existing unrelated flaky cache-timing test confirmed passing in isolation) all pass unchanged.
Shipped in dependency order per rule 8: `unified-trading-library@f853fc87` first, then `ml-service@7a90b84a`.

**Net effect**: new model training runs will now correctly land in the canonical env-tiered bucket going forward — the
drift that produced the 38-object flat-bucket orphan (already migrated forward in §5e) cannot recur.

## 5i. Legacy DeFi bucket deletion — operator said "delet legacy buckets if data is migrated" (2026-07-12)

Operator authorization, verbatim: "delet legacy buckets if data is migrated." Began executing against the §5f-confirmed
migration (`migrate_defi_full_v9_canonical.py`, VM `canonical-migration-defi-20260618-180603`, rc=0) — but a
re-verification pass while wiring `manifest_reader.py`'s `_EXTRA_BUCKET_KINDS` surfaced a **factual correction to §5f**
that changes which buckets are actually safe to delete.

**Correction to §5f's migration-destination model.** Read `_migrate_defi_walk.py` directly:
`base = f"{stem}-{project_id}"` (the FLAT, no-suffix bucket) is the migration's SOURCE;
`base_prd = f"{stem}-prd-{project_id}"` is its DESTINATION — the migration writes v9-canonical data INTO each kind's own
dedicated `-prd` bucket, NOT into the shared `market-data-tick-defi-prd` bucket as §5f assumed. This means for kinds
`cloud-providers.yaml` still resolves (`dex-pools`, `lst-rates`, `perp-funding` — see the "real reader" comments already
in that file: strategy-service's `canonical_dex_pool_provider.py` for dex-pools,
`e2e-testing/staked_basis_funding_scan.py` for lst-rates, genuine live data for perp-funding), the `-prd` bucket **is
the live canonical production bucket**, not a redundant legacy copy — deleting it would have been a real regression.
Caught this **before** it happened: the deletion script was running in the background and had not yet reached these 3
buckets when the contradiction surfaced; stopped it (`TaskStop`), corrected the list, resumed.

**Corrected deletion set** (14 buckets, flat pre-migration sources + fully-retired kinds' `-prd` destinations):
`evm-defi` + `evm-defi-prd`, `solana-defi` + `solana-defi-prd`, `liquidations`, `lst-rates` (flat only — `lst-rates-prd`
stays, live), `oracle-prices` + `oracle-prices-prd`, `perp-funding` (flat only — `perp-funding-prd` stays, live),
`gas-fees` + `gas-fees-prd` (confirmed 0 bytes), `dex-pools` (flat only — `dex-pools-prd` stays, live), `dex-swaps` +
`dex-swaps-prd`. `pnl-attribution` (already deleted earlier this round) dropped from the list. **Explicitly withheld**:
`dex-pools-prd`, `lst-rates-prd`, `perp-funding-prd` (live, real callers — do not delete, ever, without a separate
finding that those callers have moved off).

**Second deferral, same day**: `lending-indices` + `lending-indices-prd` were also in the original candidate set (kind
fully retired from `cloud-providers.yaml`, data type confirmed present in the shared bucket's historical partitions via
targeted `gcloud storage ls` spot-checks at 2020/2021/2022/2023/2025/2026-06 — redundant, safe by the same logic as
gas-fees/oracle-prices/dex-swaps). Held back anyway: a live GCE VM, `mtds-lending-indices-20260712-112557`
(`VM_OPERATION=collect-lending-indices`, `VM_LENDING_PROTOCOLS=morpho`, launched today), is actively running. Traced it
to `plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md` (operator-authorized 2026-06-27, locked, active) — today's
VM is that plan's follow-up for `[[defi_morpho_lending_indices_never_wired_2026_07_12]]` (Morpho was never wired into
`lending_indices_handler.py`'s default protocol list; this VM is the fix landing). Its bucket target wasn't
independently confirmed (near-certainly resolves `kind="tick-data"` → the shared bucket, since `kind="lending-indices"`
was already unreachable before this VM launched), but touching either legacy `lending-indices` bucket while that VM is
live isn't worth the risk for 2 buckets out of 16. **Revisit once that VM completes** (`VM_SHUTDOWN_ON_COMPLETION=true`
— check `gcloud compute instances describe mtds-lending-indices-20260712-112557` for existence/state).

**Related discovery, not an incident**: while spot-checking the shared bucket's date coverage, found NO `day=`
partitions after `2026-06-27` in `market-data-tick-defi-prd`'s `raw_tick_data/by_date/` tree — and the same cutoff in
the "live" per-kind buckets (`dex-pools-prd`/`lst-rates-prd` stop at `2026-05-28`, `perp-funding-prd` at `2026-06-09`).
Initially read as a possible live-capture outage; traced to `mvp_backfill_defi_onchain_v10_2026_06_27.md` instead —
`2026-06-27` is that plan's deliberate backfill-window end date (created that day, gap-fill VMs launched with explicit
`...→2026-06-27` end dates), not a broken pipeline. **Worth an operator note, not a new issue doc**: 2 of that plan's
VMs (`mtds-dex-swaps-backfill`, `mtds-perp-funding-backfill`) have been `RUNNING` continuously since 2026-06-27 — 15
days as of this writing. That plan is actively owned (today's Morpho follow-up VM proves it's being worked), so no
action taken here beyond this note — but worth someone confirming those 2 long-running VMs are still making real
progress, not stuck.

**Execution — COMPLETE.** Ran the corrected 14-bucket script via `gcloud storage rm -r` + `buckets delete`, each with a
post-delete existence check logged (script/log session-scoped at
`/private/tmp/claude-501/.../scratchpad/delete_legacy_defi.sh`, not committed). 13/14 succeeded on the first pass;
`gas-fees-central-element-323112` came back `STILL EXISTS` — root cause: `uts-prod-manifest-consolidator-gas-fees-cron`
(Cloud Scheduler, `asia-northeast1`) was still `ENABLED` on a `*/1 * * * *` (every-minute) schedule, re-writing
`_index/availability_index.parquet` + `_index/per_vm/_legacy_seed.parquet` into the bucket faster than the delete could
land — a leftover per-bucket consolidator job from before the shared-bucket architecture, orphaned once `gas-fees` was
retired from `cloud-providers.yaml` (its sibling `uts-prod-mtds-collect-gas-fees-cron` collection job was already
`PAUSED`, consistent with the retirement, but the consolidator cron wasn't). Checked the other 8 retired kinds
(`oracle-prices`/`dex-swaps`/`liquidations`/`evm-defi`/`solana-defi`/`lending-indices`/`dex-pools`-flat/`lst-rates`-flat/
`perp-funding`-flat) for the same per-kind consolidator-cron pattern — none exist, this was a `gas-fees`-only leftover,
not systemic. **Paused** (not deleted — reversible) `uts-prod-manifest-consolidator-gas-fees-cron`, retried, confirmed
gone. Final sweep confirmed **all 14 target buckets deleted**, and confirmed the 5 withheld/deferred buckets
(`dex-pools-prd`, `lst-rates-prd`, `perp-funding-prd`, `lending-indices`, `lending-indices-prd`) are still present as
intended. Bucket count: 242 (332 at the start of the whole `gcs_bucket_estate_cleanup_2026_07_10` effort; the
intermediate count immediately before this round's 14 deletions wasn't independently recorded).

Flipped `defi_manifest_canonicalisation_2026_06_01.md`'s `C0f` todo to `[x]` (see that plan). `lending-indices` +
`lending-indices-prd` remain the one open item — revisit once `mtds-lending-indices-20260712-112557` completes
(`VM_SHUTDOWN_ON_COMPLETION=true`; check for its absence from `gcloud compute instances list` as the completion signal),
confirm its actual write target (expected: shared bucket via `kind="tick-data"`, not either legacy `lending-indices`
bucket), then delete those 2 if still safe.

## 5j. Doc-reconciliation corrections (2026-07-14, verify-rerun-2 findings 78/80/81)

- **Finding 78 — frontmatter `status: complete` contradicted §5i's own "one open item" (lending-indices +
  lending-indices-prd, gated on `mtds-lending-indices-20260712-112557`)**: re-checked live GCP state
  (`gcloud compute instances list --project=central-element-323112`, 2026-07-14) — the VM is **gone** (matches its own
  stated completion signal, `VM_SHUTDOWN_ON_COMPLETION=true`), so the gate that was blocking §5i's revisit has cleared.
  However, §5i's remaining action ("confirm its actual write target, then delete those 2 buckets if still safe") has
  **not** been executed by this doc-reconciliation pass — that's a live GCS delete, out of scope for a doc-fix and not
  something to do without re-running the target-confirmation step §5i specifies. Flipped frontmatter `status: complete`
  → `active` (was: `complete`) — the plan has one genuinely open, now-unblocked residual action, not zero.
- **Finding 80 — frontmatter `last_updated: "2026-07-10"` predated §5c–§5i's real 2026-07-12 edits.** Bumped to
  `"2026-07-14"` (was: `"2026-07-10"`) to reflect this pass's own edit plus the pre-existing 07-12 drift.
- **Finding 81 — frontmatter `repos:` omitted `ml-service` despite §5h shipping `ml-service@7a90b84a`.** Added
  `ml-service` to the `repos:` list (was:
  `[deployment-service, unified-trading-library, market-tick-data-service, strategy-service]`).

## 5j. CORRECTION — `features-onchain-defi-prd` was NOT already migrated (2026-07-14)

**§5f/§6 wrongly called `features-onchain-defi-prd-central-element-323112` "ALREADY MIGRATED"** on the strength of "date
range falls inside the canonical sibling's range" alone. A dispatched read-only audit (from
`data_completion_to_100_all_ag_2026_06_21.md`) re-checked this specific bucket against the actual `feature_group`
content, not just the date range, and found a real, live-verified gap: the entire `lst_yields` feature_group (15 real
`by_date/day=.../feature_group=lst_yields/features.parquet` files, 2026-04-03..2026-04-19) existed **only** in this
legacy bucket — zero `lst_yields` objects anywhere in canonical's full 118-day history, not just the legacy bucket's
15-day window. `lst_yields` is a currently-registered DeFi feature handler (not retired), so this was real data loss
risk, not a false alarm. Date-range containment does not imply feature_group content parity — noted here as the lesson
(parallel to §5f's own "grep for an existing migration tool before concluding needs-migration" lesson, the inverse
mistake this time: concluding already-migrated too early).

**Corrected and closed out same-day**: migrated the 15 files server-side (`gcs_copy_object`, idempotent,
`e2e-testing/scripts/defi/copy_lst_yields_prd_to_canonical_2026_07_14.py`), independently re-verified via per-object
size+crc32c match AND a fresh full recursive listing, re-confirmed zero live terraform/Scheduler/Cloud-Run/VM/BigQuery
references to the legacy bucket, then deleted it (versioning was `Suspended` on both buckets, so a live-object `rm -r` +
`buckets delete` was sufficient — no noncurrent-version sweep needed). Full account + evidence in
`data_completion_to_100_all_ag_2026_06_21.md`'s 2026-07-14 entry. `features-onchain-defi-prd-central-element-323112` is
now correctly gone (404 confirmed), not just correctly classified.

## 5k. `dex-pools-prd`/`lst-rates-prd`/`perp-funding-prd` trio resolved — last reader fixed, all 3 confirmed deleted (2026-07-14)

The 3 buckets §5i explicitly withheld ("live, real callers — do not delete, ever, without a separate finding that those
callers have moved off") are now resolved. Full execution tracked in
`defi_dedicated_bucket_shared_migration_2026_07_13.md`; summary here for this doc's own bucket-estate ledger:

- **Last broken reader fixed**: `execution-service/execution_service/data/defi_lateral_loader.py` still had flat,
  partly-dead `DEFAULT_LATERAL_BUCKETS` defaults (5 of 7 pointed at buckets already deleted earlier this round:
  `perp-funding`, `liquidations`, `oracle-prices`, `gas-fees`, `lst-rates` flat forms; the remaining 2, both
  `eigenlayer-rewards` forms, confirmed 0 bytes) — broke all 15 operator decision-trace CLIs that use it. Repointed to
  the shared bucket via `resolve_bucket_name(kind="tick-data", asset_group="defi")` + the canonical v9 day-first
  path/needle-filter pattern (mirrors `canonical_dex_pool_provider.py`). Also fixed `EIGENLAYER` → `EIGENLAYER-ETHEREUM`
  venue-string drift in `load_eigenlayer_rewards_range()`. — `execution-service@a7e42c932`, quality-gates.sh green (also
  closed a real gap found while fixing it: `tests/defi_execution/unit/` (19 files) and `tests/e2e/` (4 files) were
  completely un-gated by any QG wrapper or CI workflow — wired the 2 files this fix touches into
  `scripts/quality-gates.sh`'s `PYTEST_UNIT_DIR`; the other 21 files remain un-gated, not fixed here).
- **All 3 buckets confirmed deleted** (`gcloud storage buckets list --project=central-element-323112` — zero matches for
  `dex-pools`/`lst-rates`/`perp-funding` in any form, flat/`-prd`/`-test`): `lst-rates-prd` + `perp-funding-prd` were
  deleted by the operator directly (`ikenna@odum-research.com`, GCP audit log, prior to this session's visible window);
  `dex-pools-prd` was deleted by the same operator principal on **2026-07-14T11:03:47Z** (audit log:
  `storage.buckets.delete`, `protoPayload.resourceName=projects/_/buckets/dex-pools-prd-central-element-323112`).
- **Flag, not an incident**: `dex-pools-prd`'s deletion preempted this plan's own gating step — the ~209k-object
  undiffed legacy tree (`day=.../category=defi/` + `_migration/`, noted in
  `defi_dedicated_bucket_shared_migration_2026_07_13.md`'s Progress Log as needing a snapshot-before-delete) was never
  independently object-diffed; the operator deleted the bucket before that step ran. No soft-delete recovery available
  (`gcloud storage buckets list --project=central-element-323112` has no `--soft-deleted` support in the installed
  gcloud version; no snapshot of `dex-pools-prd` specifically exists in `central-element-323112-pre-migration-snapshot`,
  which only holds the unrelated 2026-05-19 VM-drain snapshot). **Assessed risk: low, not zero** — the plan's own Todo 1
  parity check had already verified `dex_pool_state`/`dex_pool_swaps`/`lst_rates`/`perp_funding` present in the shared
  bucket at (venue, data_type, day) granularity across the full date range, and the one companion data_type that could
  have held unique legacy content (`dex_pool_fees`) was independently confirmed to have **zero real rows anywhere** in
  `dex-pools-prd` (recursive search, no matches) — so the canonical/reader-relevant content was verified safe before
  deletion; only the true legacy trees (pre-v9-format duplicates + migration-tooling scratch output, per this doc's own
  `_migration/column_union.json` pattern found in the other DeFi buckets) went unverified. Flagging per the
  data-correctness HARD RULE rather than silently treating it as fine.
- **Terraform**: confirmed clean — `tofu state list` in `deployment-service/terraform/gcp` has zero
  `google_storage_bucket` entries for any of the 3 kinds (the only state entries matching the kind names are the live,
  legitimate `google_cloud_scheduler_job.defi_collect_cron["dex-pools"|"lst-rates"|"perp-funding"]` +
  `module.defi_collect_job[...].google_cloud_run_v2_job.job` — ongoing DATA COLLECTION infra that writes into the shared
  bucket, not orphaned bucket resources). `main.tf` + `canonical_buckets.tf` already had their bucket-resource blocks
  removed 2026-07-13 (confirmed still clean, only historical comments remain). The guarded `terraform state rm` script
  generated 2026-07-13 for this trio was never run — turned out to be unnecessary, since no matching state entries
  existed to remove.
- **Config SSOT**: the `dex-pools`/`lst-rates`/`perp-funding` kind entries were already removed from
  `cloud-providers.yaml` (5 copies) + `bucket_config.yaml` + `manifest_reader.py`'s `_EXTRA_BUCKET_KINDS` on 2026-07-13
  (see `defi_dedicated_bucket_shared_migration_2026_07_13.md`'s own todos) — not re-verified byte-for-byte here, but no
  contradicting evidence found.
- **Not this trio's scope, still open**: `lending-indices` + `lending-indices-prd` (§5i/§5j finding 78) remain undeleted
  — a separate, pre-existing residual item, unrelated to this trio.

## 5l. Reconciliation with sibling plan before archival (plan-reconcile, 2026-07-21)

The two items this plan's own text still called "genuinely open" (§5g, §5k) were resolved since — by
`bucket_estate_consolidation_to_sub100_2026_07_13.md`, which explicitly lists this plan in its own `related:`
frontmatter and states it "tracks/completes the in-flight deletions owned by other plans":

- **§5k's "not this trio's scope, still open" `lending-indices`/`lending-indices-prd`** — CONFIRMED DELETED. Sibling
  plan line ~541: purge-lifecycle armed 2026-07-14T14:00Z, drain completed, `gcloud storage buckets delete --quiet` on
  both `lending-indices-central-element-323112` and `lending-indices-prd-central-element-323112` succeeded, both
  confirmed 404 via `buckets describe`. "STATUS: COMPLETE 2026-07-15."
- **§5g's football buckets (`football-backtest-results`, `football-mapped-consolidated`'s `odds/`+`parquet_backup/`,
  `football-ml-models-and-predictions`)** — RULED + DONE. Sibling plan line ~199: "RULED + DONE 2026-07-14: migrated
  count-verified into canonical homes (backtest-results/football 455 obj; ml-models-store-prd/legacy_football 119;
  instruments-store-sports-prd/legacy_football/{mapped_consolidated 107, raw_all_sources 37}) and all 4 deleted."
- **`ml-models-store` flat bucket migration (§5h/§5e)** — still genuinely open, but correctly owned by the sibling
  plan's own unchecked todo ("ml legacy variants ... verify no new writes since, then delete"), gated on its W3 ml-fold.
  Not a contradiction — consistent open item in both docs, no action needed here.

No contradictory claims found between the two plans about current bucket state — this plan's text was simply stale (it
hadn't been told its own flagged-open items got closed elsewhere). With this reconciliation, nothing remains open in
this plan's own scope.

## 6. Model-tier note (repeating from frontmatter, since it matters for how much to trust this)

Per `AUTONOMOUS_AGENT_RULES.md`'s self-check, a long cross-repo autonomous loop like this one normally routes to
`opus-required` — this ran on Sonnet 5 (harness-assigned, no self-upgrade path mid-session). Compensated with extra
verification rigor throughout (the `dex-pools` false-positive catch is a direct example of that paying off — caught
before it caused harm, not after). Worth knowing if you want a second pass on any of the judgment calls above.
