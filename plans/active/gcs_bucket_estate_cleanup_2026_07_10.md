---
doc_type: plan
title: GCS bucket estate cleanup — central-element-323112 (332 buckets)
summary:
  Full audit + cleanup of the GCP project's 332 GCS buckets — classify every bucket against what code actually
  reads/writes (not what config declares), delete confirmed-orphaned buckets, clean stale Terraform resources +
  bucket_config.yaml/cloud-providers.yaml entries, and fix real data-pipeline correctness bugs surfaced along the way
  (gas-fees manifest scanning an empty bucket, lst-rates reader/writer bucket mismatch, cf-manifest-audit / qg-snapshot
  crons that were silently failing for weeks).
status: complete
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos: [deployment-service, unified-trading-library, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: [gcs, buckets, cleanup, terraform, data-correctness, autonomous]
related: []
created: "2026-07-10"
last_updated: "2026-07-10"
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
  first (`codex/05-infrastructure/manifest-consolidator-ssot.md`).

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

None. Everything that could be finished within the "confirm real evidence before acting" standard was finished;
everything else is flagged above with the specific reason it wasn't force-decided.

## 6. Model-tier note (repeating from frontmatter, since it matters for how much to trust this)

Per `AUTONOMOUS_AGENT_RULES.md`'s self-check, a long cross-repo autonomous loop like this one normally routes to
`opus-required` — this ran on Sonnet 5 (harness-assigned, no self-upgrade path mid-session). Compensated with extra
verification rigor throughout (the `dex-pools` false-positive catch is a direct example of that paying off — caught
before it caused harm, not after). Worth knowing if you want a second pass on any of the judgment calls above.
