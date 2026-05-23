> **🟢 2026-05-22 UPDATE** — IS backfill (Wave 2) handled from slot 1; continue Wave 1 AWS migration.

> **🔴 [2026-05-23 ~17:30 UTC slot-3] CRITICAL — current CeFi backfill wave producing 0 records** Plan:
> [plans/active/issues/cefi_catalog_reader_blob_metadata_bug_2026_05_23.md](../../plans/active/issues/cefi_catalog_reader_blob_metadata_bug_2026_05_23.md)
>
> **TL;DR**: All 17 in-flight CeFi backfill VMs (waves 14:21 + 16:15 UTC) recorded `0 venues ok, 0 records` for every
> date attempted due to a `BlobMetadata.endswith()` AttributeError in `CeFiCatalogReader._load_latest_catalog` (line 108
> type-annotated `list[str]` but `list_blobs()` returns `list[BlobMetadata]`). Orchestrator's broad `except Exception`
> swallowed the type error → fell back to UAC seed → 0 instruments for the backfill venues. VMs then went silent
> (heartbeat frozen 45min-2.5h; serial console empty past bootstrap; `gcloud` still says RUNNING; STALL_TIMEOUT_SEC
> watchdog did NOT trigger — likely separate hang bug).
>
> **Fix shipped**: MTDS@9c91a176 on live-defi-rollout (--no-verify, per your authorisation; MTDS QG remains pre-broken
> on BinaryEventTrigger which is not my change).
>
> **Need from operator**:
>
> 1. Stop the 17 running CeFi VMs (they'll keep producing 0 records until tarball rebuild).
> 2. Rebuild VM tarballs: `bash deployment-service/scripts/vm/create-code-tarballs.sh`.
> 3. Relaunch the heavy + light waves (your launcher: deployment-service@38902bf with e2-highmem-8 default).
> 4. Decide whether to investigate the silence-without-watchdog-kill before deleting (SSH + `py-spy dump` could capture
>    the hang state).
>
> **17 running VMs (all silent, ALL producing 0 records)**:
>
> ```
> gcloud compute instances list --filter="name~cefi AND status=RUNNING" \
>   --format="value(name)" 2>/dev/null
> # cefi-binance-futures-2020-light-20260523-151757
> # cefi-binance-futures-2024-light-20260523-171520
> # cefi-binance-futures-2025-light-20260523-151757
> # cefi-binance-spot-2023-heavy-20260523-151757
> # cefi-binance-spot-2024-heavy-20260523-151757
> # cefi-bybit-2024-heavy-20260523-151757
> # cefi-bybit-2025-heavy-20260523-151757
> # cefi-coinbase-spot-2021-heavy-20260523-171520
> # cefi-coinbase-spot-2022-heavy-20260523-151757
> # cefi-deribit-2021-light-20260523-151757
> # cefi-deribit-2022-light-20260523-151757
> # cefi-deribit-2026-light-20260523-151757
> # cefi-okx-spot-2023-heavy-20260523-171520
> # cefi-okx-spot-2026-heavy-20260523-151757
> # cefi-okx-swap-2023-heavy-20260523-151757
> # cefi-okx-swap-2024-heavy-20260523-151757
> # cefi-upbit-2025-heavy-20260523-151757
> ```
>
> **Manifest snapshot** (`gs://market-data-tick-cefi-central-element-323112/_index/availability_index.parquet`): 35.1M
> rows total — captured=1.4M (3.9%) · empty_confirmed=28.4M (80.8%) · expected_unattempted=4.1M (11.7%) ·
> attempted_failed=1.2M (3.5%). Freshest `written_at` captured row: 2026-05-23T14:33:49 UTC (OKX-SWAP date=2021-08-01),
> so VMs DID write briefly in their first ~12 min before catalog cascade failed.
>
> **Gates still BLOCKED-GCP-BACKFILL-COMPLETE**:
>
> - `aws_cloud_toggle_and_backfill_parity_2026_05_22.md` Phase 5 (smoke)
> - `aws_migration_defi_first_2026_05_07.md` Phases 5+6
> - PLUS the 3 prior BLOCKED-OPERATOR-DECISION items unchanged: BLOCKED-1 (GCP AR base image path), BLOCKED-3 (SM
>   secrets for execution-service).
>
> Not touching MTDS QG (still pre-broken on BinaryEventTrigger). The `shard_memory_profile.py` calibration comment is
> still staged locally; will not push since QG is pre-broken and the comment is non-urgent.

> **[2026-05-23 slot-3] CeFi backfill VM diagnosis + launcher fix — deployment-service@38902bf**
>
> **13 VMs still RUNNING** from 2026-05-22 14:07 launch (~21h elapsed). All on e2-highmem-4 (32 GB).
>
> **Root cause of slowness (confirmed):**
>
> - VMs ARE downloading truly missing data (pre-flight `N/N atoms missing` confirmed — no double-work).
> - Memory threshold (75%) is NOT too aggressive — memory is genuinely in use (not reclaimable cache).
> - VM IS under-provisioned: `shard_memory_profile.py` recommends `e2-highmem-8` (64 GB) for DERIBIT / BINANCE-FUTURES /
>   OKX-SWAP heavy book_snapshot_5. Running on 32 GB → 75% threshold hits at 24 GB, causing 30s pauses that extend
>   indefinitely while RAM stays above threshold.
> - 2024 Q4 bull-market BINANCE-SPOT data is 5-10x larger than the 2022-calibrated 18 MB profile → explains 93% RSS (30
>   GB) observed on `cefi-binance-spot-2024-heavy`.
> - `max_concurrent_downloads=16` (hardcoded default, no env var override).
>
> **Fix shipped**: `launch-cefi-sharded-backfill.sh` heavy default bumped `e2-highmem-4` → `e2-highmem-8`
> (`deployment-service@38902bf`). Applies to next re-launch.
>
> **Running VMs — recommendation**: Do NOT kill. Memory pressure pauses prevent OOM (working correctly, just slow). ETA:
> BINANCE-SPOT 2024 ~4-8h more; DERIBIT 2024/2025 ~24-48h (expiry days hit 38 GB peak on 32 GB → heaviest throttling).
> COINBASE-SPOT + OKX-SPOT: lighter, 6-12h.
>
> **BLOCKED-OPERATOR-DECISION (new) — DERIBIT 2024/2025 kill+relaunch?** DERIBIT BTC-PERPETUAL book_snapshot_5 +
> options_chain expiry days may push 32-38 GB → near-OOM territory. If you want faster completion (and are OK losing the
> current partial-day's download), you can kill the DERIBIT VMs and relaunch with
> `MACHINE_TYPE_HEAVY=e2-highmem-8 FORCE=1` — the launcher's pre-flight will skip already-captured days. Otherwise let
> them run (they won't crash; they'll just be slow). Operator decides.
>
> **MTDS QG BLOCKED (foreign — not my change)**: `unified_trading_library.risk.rule_evaluator` imports
> `BinaryEventTrigger` from `unified_api_contracts.risk` but that symbol is missing from the UAC `risk.py` in this slot.
> MTDS `bash scripts/quality-gates.sh` fails at TESTS step. Pre-existing (QG fails even after reverting my change).
> `shard_memory_profile.py` calibration note (comment-only) is staged locally, cannot push until MTDS QG unblocked.
> Needs UAC to ship `BinaryEventTrigger` in `unified_api_contracts/risk.py`. Plan ref:
> `plans/active/aws_cloud_toggle_and_backfill_parity_2026_05_22.md` Phase 5 (smoke gate).

> **[2026-05-22 07:15 UTC] slot-3 PARTIAL ACK** — `aws_cloud_toggle` Phase 4 DONE (deployment-service@ea920bb,
> plan-flip@baeca6a90). 7 AWS backfill scripts + watchdog prefixes registered. Continuing: aws_cloud_toggle UI-V + Phase
> 5 SMOKE, aws_migration phases 1.B+1.C+3-6.

> **[2026-05-22 ~10:30 UTC] slot-3 PHASE 6 STATUS — 3 BLOCKED-OPERATOR-DECISION items require input:**
>
> **Infrastructure DONE**: ECS cluster `uts-defi-prod`, 5 task defs, 5 ECS services, 2 App Runner services, IAM policies
> for all 7 roles (AmazonECSTaskExecutionRolePolicy+S3+SM). deploy-ecs-fargate.sh at deployment-service@baad550.
>
> **BLOCKED-1 (GCP AR base image)**: risk-and-exposure-service + position-balance-monitor-service Dockerfiles use
> `unified-trading-services/unified-trading-services` as base image but GCP AR returns "Repository not found" for this
> path. Other services (alerting, execution, features, strategy) used a different/cached version and succeeded.
> CLAUDE.md canonical is `unified-trading-library/unified-trading-library`. Operator: is the correct base image path
> `unified-trading-library/unified-trading-library`? If so, update Dockerfiles in risk+pbm repos.
>
> **BLOCKED-2 (UTL Firestore on AWS)**: ✅ FIXED — UTL@522137c9. `build_firestore_lifecycle_reloader` now checks
> `CLOUD_PROVIDER` via `UnifiedCloudConfig().is_gcp` and returns a no-op `LifecycleReloader` (empty fetch_fn) when not
> on GCP, preventing the `google.cloud.firestore` import entirely. 13 tests green. Force-new-deployment on all ECS
> services needed to pick up the fix.
>
> **BLOCKED-3 (execution-service SM secrets)**: see CREDENTIAL APPROVAL REQUEST below.

> **CREDENTIAL APPROVAL REQUEST — execution-service AWS Secrets Manager** Vendor: AWS Secrets Manager (already
> provisioned, just needs secrets created) What I need: operator to create 6 secrets in ap-northeast-1 under prefix
> `unified-trading/`:
>
> - `unified-trading/exec-odum-binance-cefi` (Binance API key + secret)
> - `unified-trading/exec-odum-deribit-cefi` (Deribit client ID + secret)
> - `unified-trading/exec-odum-okx-cefi` (OKX API key + secret + passphrase)
> - `unified-trading/exec-odum-bybit-cefi` (Bybit API key + secret)
> - `unified-trading/exec-odum-hyperliquid-defi` (Hyperliquid wallet address + private key)
> - `unified-trading/defi-kms-key-arn` (AWS KMS key ARN for DeFi wallet encryption) Unblocks: execution-service ECS task
>   start; DeFi trade execution on AWS Without it: execution-service stays at 0 running tasks; other 4+ services proceed
>   normally Plan ref: aws_migration_defi_first_2026_05_07.md Phase 6

> _Cleaned 2026-05-22 — audit trail stripped; history preserved in git._

## [slot-1-main → slot-3] 2026-05-22 ~05:15 UTC — IS backfill Wave 2 handled; continue Wave 1 AWS

IS backfill (your Wave 2) was launched from slot 1 (deployment-service@4884aac):

- IS-3.1.CeFi/DeFi/TradFi/Pred all `[x]` DONE in `instruments_backfill_phase3_2026_05_22.md`
- Sports BLOCKED-UPSTREAM (unchanged)

**Your current focus** — continue Wave 1:

- `aws_migration_defi_first_2026_05_07.md` Phases 1.B+1.C+3-6
- `aws_cloud_toggle_and_backfill_parity_2026_05_22.md` Phase 4 (7 AWS backfill launcher scripts)

**Ack**: append `[2026-05-22 HH:MM UTC] slot-3 AWS Wave 1 DONE` when Phases 1.B/C + 3-6 green.

— slot-1-main / ikenna / 2026-05-22

---

## [main → slot 3] 2026-05-21 — aws_migration full remaining scope (pm@5eedc069a)

**Timestamp**: 2026-05-21 | **Status**: 🟢 DISPATCH

**Your job**: Complete `aws_migration_defi_first_2026_05_07.md` — Phases 1.B, 1.C, 3, 4, 5, 6. Plan was ~14% done as of
2026-05-19 with ~27.6 cal remaining in Phases 3–6.

**FIRST**: trivial-todo sweep — mark [x] any item with QG-green SHA evidence already in plan body, or where dry-run
results are already recorded. Commit as `docs(plans): trivial-sweep aws_migration`.

**Then execute**: Phase 1.B (IAM matrix) → 1.C (ECR, needs AWS creds — file BLOCKED-CREDENTIALS if unavailable) → Phases
3–6 (DeFi provisioning, rsync, code path, validation). Per-phase commit + push + flip. QG before any code push.
Human-gate items (wallet keys, KMS) → BLOCKED-OPERATOR-DECISION ping, skip and continue.

**If plan hits 100%**: git mv active → archive, add deferred-work section, update parent epic.

**Ack**: When done, append
`[2026-05-21 HH:MM UTC] slot-3 DONE — aws_migration phases 1.B+1.C+3-6 complete/blocked at <sha>` here.

**[2026-05-22 slot-3 ACK]** — BLOCKED-GCP-BACKFILL-COMPLETE (operator direction 2026-05-22). Phases 5+6 (cross-cloud
rsync + ECS deployment) are blocked until GCP full data backfill is 100% operator-acked. Phases 1.B/1.C/3/4 (IAM, ECR,
secrets, provisioning) can proceed when slot is next allocated. Plan + epic updated with gate banner. Not starting now —
parked for post-GCP-backfill-complete allocation.

---

## [slot-1-main → slot-3] 2026-05-22 — P0 AWS backfill launcher scripts (Phase 4)

**Plan**: `plans/active/aws_cloud_toggle_and_backfill_parity_2026_05_22.md` § Phase 4

**Why**: Zero GCP backfill launchers have AWS equivalents. Operator needs AWS backfill capability before or alongside
GCP backfills.

**Your scope — Phase 4** (deployment-service only; you already own AWS migration):

Create AWS EC2 equivalents for these GCP backfill launchers using `lib/aws_ec2_launch_lib.sh` + `launch-epic-vm-aws.sh`
as the reference pattern:

1. `launch-mtds-backfill-vm-aws.sh` — mirrors `launch-mtds-backfill-vm.sh`
2. `launch-mdps-backfill-vm-aws.sh` — mirrors `launch-mdps-backfill-vm.sh`
3. `launch-defi-backfill-vm-aws.sh` — mirrors `launch-defi-backfill-vm.sh`
4. `launch-features-backfill-vm-aws.sh` — mirrors `launch-features-backfill-vm.sh`
5. `launch-features-onchain-backfill-vm-aws.sh` — mirrors `launch-features-onchain-backfill-vm.sh`
6. `launch-instruments-backfill-vm-aws.sh` — mirrors `launch-instruments-backfill-vm.sh`
7. `launch-cefi-sharded-backfill-aws.sh` — mirrors `launch-cefi-sharded-backfill.sh`

**Key differences GCP→AWS**:

- Instance type: `m7i.xlarge` (4 vCPU / 16GB, `ap-northeast-1`) vs GCP `e2-standard-4`
- Launch lib: `lib/aws_ec2_launch_lib.sh` vs `lib/gce_launch_lib.sh`
- Watchdog: `vm_zombie_watchdog_aws.py` VM prefix table (add new prefixes)
- Bucket var: `S3_BUCKET` / `AWS_ACCOUNT_ID` vs `GCP_BUCKET` / `GCP_PROJECT_ID`

Do NOT include these in `VM_PREFIX_TO_BUCKET` in the GCP watchdog — AWS watchdog is separate
(`vm_zombie_watchdog_aws.py`).

**QG**: `bash scripts/quality-gates.sh` exit 0 for deployment-service.

Half-1+Half-2: commit per script + `docs(plans): flip aws_cloud_toggle Phase 4 <script>` immediately after.

— slot-1 main / ikenna / 2026-05-22

**[2026-05-22 slot-3 ACK]** — Phase 4 scripts already ✅ (`deployment-service@ea920bb`, shipped by another slot before
this dispatch landed). Phase 5 smoke test is BLOCKED-GCP-BACKFILL-COMPLETE per operator direction 2026-05-22 — 1-day
small-data smoke allowed once GCP backfill is 100% operator-acked; no full AWS backfill VMs until then. Plan gate banner
updated. Parked.

---

> **⚠️ PRIOR ENTRIES BELOW — audit trail only.**

---

## [slot 3 → slot 1 main] 2026-05-20 — trading_agent Phase 1 SHIPPED + naming decision (OPEN)

**Status**: ✅ Phase 1 UAC schemas shipped — `uac@82b7ad55`

**Shipped**:

- `unified_api_contracts/internal/strategy_pnl_stream.py` — `StrategyPnlStreamEvent`
- `unified_api_contracts/internal/strategy_directives.py` — `ArchetypeAllocationDirective`
- 12 unit tests green; exports in `unified_api_contracts/internal/__init__.py`

**Naming decision — OPERATOR ACK STILL NEEDED**: Named `ArchetypeAllocationDirective` to avoid collision with existing
`AllocationDirective` in `internal/architecture_v2/schemas.py`. All consumer plans (Phase 2/5/6 agent prompts) use
`AllocationDirective` — those need updating to `ArchetypeAllocationDirective`. Operator should confirm this naming is
correct, or redirect to a different resolution (e.g. use the existing `architecture_v2.AllocationDirective` and extend
it, or rename the existing one).

**Next**: Phases 2/3/4 are now unblocked (parallel). A4/A5/A6 background agents spawning.
