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
- [ ] 3. [SCRIPT] P0. Finish + ship the cf_manifest_audit fix: confirm the dry-run (task `bcnybd5tw`, or re-run if dead)
      succeeds end-to-end against real buckets; run `quality-gates.sh` on `unified-trading-library` for the new
      `cf_manifest_audit.py` module and fix any violations; ship via quickmerge (or dirty-deps carve-out); ship the
      already-edited `deployment-service/terraform/{gcp,aws}/cf_manifest_audit_scheduler.tf`.
- [ ] 4. [SCRIPT] P0. Let `bucket_scan_results.tsv` finish (background task) or re-run remaining buckets; cross-check
      against every candidate-orphan list above (ROLLED_BACK_ENV_ARTIFACT 63, the 9 DeFi kinds' flat+env buckets,
      risk/pnl/positions-store dead-scheme buckets, football-\*, reconciliation-store-test,
      pnl-attribution-central-element-323112) to confirm each is genuinely empty (recursive `gcloud storage ls **`, not
      just shallow) before deleting.
- [ ] 5. [SCRIPT] P0. Delete every bucket confirmed both (a) zero live code readers/writers AND (b) empty on recursive
      listing. Batch by kind/cluster; log each deletion (bucket name, evidence, empty-check) in the Progress Log below
      as you go — this IS the audit trail if context compresses mid-sweep.
- [ ] 6. [SCRIPT] P0. Clean the corresponding `cloud-providers.yaml`/`bucket_config.yaml` declared-but-dead entries
      (risk-store/pnl-store/positions-store legacy schemes, any DeFi kind confirmed to never resolve its own bucket) so
      `setup-buckets.py`/`resolve_bucket_name()` can't resurrect them. Scope commits tightly — shared config file, only
      touch the lines you've 100% confirmed dead.
- [ ] 7. [DATA] P1. File a proper issue doc for the gas-fees manifest-scan bug
      (`plans/active/issues/ gas_fees_manifest_scan_wrong_bucket_2026_07_10.md`) per CLAUDE.md's
      data-pipeline-correctness rule — this is a live data-status/coverage-reporting bug, not just an orphaned bucket.
      Include root cause (`data_manifest_handler.py:215` vs `gas_fee_handler.py` writer bucket mismatch) and a
      recommended fix (point the manifest scanner at the `market-data` bucket, or make the writer dual-write, whichever
      the actual manifest-consolidator convention expects for DeFi reference data — read
      `codex/05-infrastructure/ manifest-consolidator-ssot.md` before deciding). Do the same for the `lst-rates`
      reader/writer mismatch if it's a distinct root cause. **This is exactly a "big finding — data-correctness" per
      SUB_AGENT_MANDATORY_RULES findings-triage — the issue doc is the notification since the operator is away; flag
      prominently in the final report too.**
- [ ] 8. [SCRIPT] P1. Resolve `ml-configs-store`/`ml-models-store`/`ml-predictions-store` split-usage: get real object
      counts on flat vs every env-tiered variant per kind, determine which side(s) are genuinely live, delete only the
      confirmed-dead side(s), leave ambiguous ones for the final report rather than guessing.
- [ ] 9. [SCRIPT] P2. `data-job-config`, `ml_jobs_ikenova`, `summary-stats`, `staging-bucket-general`,
      `temp-bucket-general` — check real object counts/contents (list only, don't download/print contents). If genuinely
      empty and generically named, delete but flag explicitly in the final report as a judgment call, not silently. If
      they hold real objects, do NOT delete — just report contents summary (file count/names, not content) for operator
      review.
- [ ] 10. [REVIEW] P1. Post-sweep audit: re-run the classification script against the (now smaller) live bucket list to
      confirm no false-positive deletions; verify Terraform `fmt`/`validate` clean on every touched .tf file; verify
      `bucket_config.yaml`/`cloud-providers.yaml` still parse + no dangling kind references in code (grep for any kind
      name you removed).
- [ ] 11. [REVIEW] P1. Write the final report into this plan's Progress Log: every bucket deleted (with evidence), every
      bug found + issue-doc filed, every judgment-call flag (scratch buckets, ml-store split), and anything genuinely
      blocked (should be none, but document if so). This is the artifact the operator reads on return — no separate
      summary doc.

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
