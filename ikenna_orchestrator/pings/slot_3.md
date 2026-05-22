> **🟢 2026-05-22 UPDATE** — IS backfill (Wave 2) handled from slot 1; continue Wave 1 AWS migration.

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
