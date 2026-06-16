---
scope: [admin, engineer]
last_reviewed: 2026-05-16
type: runbook
execution:
  owner: "Operator (Ikenna or Harsh; whichever side initiates the cutover window)"
  cadence: "one-shot, scheduled cutover (target window 2026-05-15 → 2026-05-19; 18–27h wall-clock)"
  verifier: |
    Each wave has its own GO/NO-GO check (see § "Wave verify" sections below). Final verifier:
    every flat bucket archived per Step 2.6.5 + zero callers reference flat names per
    QG STEP 5.69 baselines all at 0 + deployment-api smoke green post-redeploy.
  last_executed: "NEVER (runbook codified 2026-05-16; first execution pending operator GO)"
---

# Phase 2.6 — Bucket-name SSOT Cutover Runbook

> **gap-2.6.E** of `plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`. Operator-runnable runbook for
> the 18–27h cutover window that flips the workspace from flat bucket names (`market-data-tick-{ag}-{pid}`) to
> env-tiered names (`market-data-tick-{ag}-{env}-{pid}`). Codifies the 7-wave gating protocol with per-wave GO/NO-GO
> checklists.
>
> **Pre-requisites** (must be green before T0):
>
> 1. **Phase 1 freeze gate fired** — see `plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md` § "Phase 1
>    freeze gate". Confirmed 2026-05-15.
> 2. **gap-2.6.A `launch-bucket-rsync-vm.sh`** shipped + tested on a canary bucket (small, low-value).
> 3. **gap-2.6.B `verify_flat_to_env_tiered_drift.py`** shipped + invoked against canary, returns drift ≤0.01%.
> 4. **gap-2.6.C `verify_env_tiered_buckets_provisioned.py`** shipped + reports zero missing for all (kind, asset_group,
>    env, cloud) tuples per `deployment-service/configs/cloud-providers.yaml`.
> 5. **gap-2.6.D `vm_zombie_watchdog.py` env-tier re-point PR** prepared (committed to a branch; lands in Wave 6).
> 6. **No backfill VMs running** — check `gcloud compute instances list --filter="status=RUNNING"`; halt any in-flight
>    backfill before T0.

---

## Wave structure overview

| Wave | Window        | Step                   | Action                                                                               |
| ---- | ------------- | ---------------------- | ------------------------------------------------------------------------------------ |
| 1    | T-1h → T0     | Phase 2.0 + Step 2.6.1 | Pre-drain final consolidate + write-pause confirm + env-tiered bucket provisioning   |
| 2    | T0 → T+4h     | Step 2.6.2 (Tier 1-3)  | Rsync canary + static reference + features cross-asset (8 parallel VMs)              |
| 2v   | T+4h → T+5h   | Verify Wave 2          | `verify_flat_to_env_tiered_drift.py` per bucket; operator GO/NO-GO                   |
| 3    | T+5h → T+10h  | Step 2.6.2 (Tier 4-5)  | Rsync features per-asset_group + ML stores (6 parallel VMs)                          |
| 3v   | T+10h → T+11h | Verify Wave 3          | drift-verify + operator GO/NO-GO                                                     |
| 4    | T+11h → T+17h | Step 2.6.2 (Tier 6)    | Rsync strategy + execution (4 parallel VMs)                                          |
| 4v   | T+17h → T+18h | Verify Wave 4          | drift-verify + operator GO/NO-GO                                                     |
| 5    | T+18h → T+24h | Step 2.6.2 (Tier 7)    | Rsync market-data large tier (4-8 parallel `n2-standard-16` VMs)                     |
| 5v   | T+24h → T+25h | Verify Wave 5          | drift-verify + operator GO/NO-GO                                                     |
| 6    | T+25h → T+26h | Step 2.6.4             | Delegate-flip workspace-wide PR + deployment-api redeploy + smoke test               |
| 7    | T+26h → T+27h | Step 2.6.3 LIFT        | Write-pause LIFT — Phase 3 backfill VMs cleared to launch against env-tiered buckets |

**Hard rule**: if ANY wave verify fails, STOP. Diagnose. Decide (a) re-run that wave, (b) extend the write-pause window,
or (c) rollback the wave + recover from snapshot per Phase 2.1 Step F. NEVER proceed to the next wave with an unresolved
verify failure — data-correctness blast radius compounds.

---

## Wave 1 — Pre-drain + provisioning (T-1h → T0)

### Pre-checks (operator-runnable, all must return ✅)

```bash
# 1. Phase 1 freeze gate fired
grep "Phase 1 freeze gate.*✅" plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md

# 2. Manifest consolidator caught up (per-VM shards drained to canonical)
python3 -c "from unified_trading_library.manifest_consolidator import status; status()"

# 3. No backfill VMs running
gcloud compute instances list --project=central-element-323112 \
    --filter='status=RUNNING AND name~"backfill|smoke"' --format='value(name)' | wc -l   # MUST be 0

# 4. Cross-cloud parity (AWS DeFi-first migration) complete
bash plans/active/aws_migration_defi_first_2026_05_07.md  # check Phase 5 freeze gate

# 5. Env-tiered bucket provisioning script ready
test -x unified-trading-pm/scripts/migration/verify_env_tiered_buckets_provisioned.py && echo "✅ gap-2.6.C exists"
```

### Action

1. Run the bucket provisioner (creates every (kind × asset_group × env × cloud) bucket per
   `deployment-service/configs/cloud-providers.yaml` SSOT):

   ```bash
   python3 unified-trading-pm/scripts/migration/verify_env_tiered_buckets_provisioned.py --provision-missing
   ```

2. Engage the operator write-pause (no backfill / live writer launches during T0 → T+27h). Document in
   `plans/active/_agent_pings.md` cross-side ledger.

### GO/NO-GO

- All env-tiered buckets exist with proper IAM (`verify_env_tiered_buckets_provisioned.py` → exit 0).
- Write-pause confirmed in cross-side ping ledger.
- No backfill VMs running.
- Phase 2.5 (`--apply-flips` rescan) freeze gate fired.

If any ❌: extend Wave 1, fix the gap, re-verify before proceeding to Wave 2.

---

## Wave 2 — Tier 1-3 rsync (T0 → T+4h)

### Action

Launch 8 parallel rsync VMs per tier. Tier ordering = minimal blast radius first:

- **Tier 1 (canary)**: `manual-audit-*` bucket + 1 small low-traffic bucket (test the launcher pattern).
- **Tier 2 (static reference)**: catalogue / config-store / unified-deployment-state buckets.
- **Tier 3 (features cross-asset)**: features cross-asset / multi-timeframe.

For each tier:

```bash
for flat in <list-of-flat-buckets-for-this-tier>; do
  env_tiered="${flat/-${PROJECT_ID}/-prod-${PROJECT_ID}}"  # env tier insert
  bash deployment-service/scripts/vm/launch-bucket-rsync-vm.sh \
    --source-bucket "gs://${flat}" \
    --dest-bucket "gs://${env_tiered}" \
    --workers 16 \
    --vm-name "bucket-rsync-${flat}-$(date +%s)"
done
```

Singleton-lock per source-bucket — re-launch against the same flat bucket returns the running VM.

### Wave 2 verify (T+4h → T+5h)

```bash
for env_tiered in <list-of-env-tiered-buckets-for-tier-1-3>; do
  flat="${env_tiered/-prod-/-}"
  python3 unified-trading-pm/scripts/migration/verify_flat_to_env_tiered_drift.py \
    --source "gs://${flat}" --dest "gs://${env_tiered}" \
    --sample-parquets 100 --max-drift 0.0001
done
```

### GO/NO-GO

- Drift ≤0.01% for EVERY Tier 1-3 bucket.
- Random-sample parquet read returns matching schema + row count.
- No rsync VMs in FAILED state (`gcloud compute instances list --filter='name~"^bucket-rsync-" AND status=TERMINATED'`).

If any ❌: re-run that bucket's rsync (additive — no flat-side delete yet), re-verify, repeat. After 2 failed re-tries:
escalate to operator decision per "Hard rule" above.

---

## Wave 3 — Tier 4-5 rsync (T+5h → T+10h)

Same shape as Wave 2 but for 6 parallel VMs:

- **Tier 4 (features per-asset_group)**: features-delta-one / features-onchain / features-volatility / features-calendar
  / features-commodity per asset_group.
- **Tier 5 (ML stores)**: ml-configs-store / ml-models-store / ml-features-store.

Wave 3 verify + GO/NO-GO at T+10h → T+11h: same form as Wave 2.

---

## Wave 4 — Tier 6 rsync (T+11h → T+17h)

4 parallel VMs:

- **Tier 6 (strategy + execution)**: strategy-store-{cefi,tradfi,defi} + execution-store + risk-store + pnl-store.

Wave 4 verify + GO/NO-GO at T+17h → T+18h.

---

## Wave 5 — Tier 7 rsync (T+18h → T+24h) — LARGEST

4-8 parallel `n2-standard-16` VMs:

- **Tier 7 (market-data large tier)**: `market-data-tick-{cefi,tradfi,defi,sports,prediction}-*` + `instruments-store-*`
  per asset_group.

These are the largest buckets (100GB-2TB each per `code_freeze_migrate_backfill_sequencing` § "Per-bucket sizing").
Allow the full 6h window.

Wave 5 verify + GO/NO-GO at T+24h → T+25h.

---

## Wave 6 — Delegate-flip + redeploy (T+25h → T+26h)

### Action

1. Land the delegate-flip PR (workspace-wide): every reader calls
   `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)`. No inline `gs://` f-strings remain
   (QG STEP 5.69 baselines all at 0 post-flip).
2. Land the **gap-2.6.D** `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` env-tier re-point in the same PR.
3. Land the `cloud-providers.yaml` flag flip — env-tiered bucket names become the canonical resolution target.
4. Redeploy `deployment-api` Cloud Run service (env-tiered bucket reads are now live).
5. Smoke test:
   - `/api/data-status/manifest` returns rows for every asset_group.
   - `/api/data-status/honest-coverage` returns the daily JSON (per gap-2.6.D watchdog cron).
   - Random parquet read via deployment-api proxy returns the same row count as Wave 5 verify.

### GO/NO-GO

- Delegate-flip PR merged + workspace-wide CI green (QG STEP 5.69 all 0).
- Watchdog dict re-point landed; `vm_zombie_watchdog.py`
  `python3 -c "import deployment_service.scripts.vm.vm_zombie_watchdog"` clean import.
- deployment-api smoke green on env-tiered reads.
- No `gs://` URI errors in Cloud Run logs (last 30 min).

If any ❌: this is the highest-blast-radius wave. Operator decision required:

- (a) Quick fix + redeploy (if the bug is well-scoped).
- (b) Rollback the delegate-flip PR + extend write-pause to T+30h+; diagnose; retry.

---

## Wave 7 — Write-pause LIFT (T+26h → T+27h)

### Action

1. Operator confirms Wave 6 smoke green for 1h.
2. LIFT the write-pause — Phase 3 backfill VMs cleared to launch against env-tiered buckets.
3. Cross-side ping the all-clear: `plans/active/_agent_pings.md` "Phase 2.6 COMPLETE — env-tiered live".

### GO/NO-GO

- Phase 3 backfill VMs launch + emit STARTED + first PROGRESS event lands within 60s, all writes target env-tiered
  buckets (verify via `_index/per_vm/{vm_name}.parquet` write target).
- Manifest consolidator picks up env-tiered shards correctly (no stale flat-bucket references).

---

## Post-cutover (T+27h → T+30 days)

### Step 2.6.5 — Archive flat buckets

After 7 days of stable operation on env-tiered (no rollback triggered):

1. Mark flat buckets read-only via IAM.
2. After 30 days (audit window for any retrospective drift discovery): delete flat buckets entirely.

Per `code_freeze_migrate_backfill_sequencing_2026_05_10.md` § Step 2.6.5 detail.

### Plan-flip closeout

Once Wave 7 confirmed + 7-day soak complete:

- Flip `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md` Done-def #6 (workspace-wide grep audit table).
- Flip `plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2.6 freeze gate.
- Ratchet down the QG STEP 5.69 baselines per repo (deployment-api 27 → 0, execution 33 → 0, UTL 23 → 0, etc.).

---

## Rollback decision tree

Each wave has its own rollback shape per the additive-rsync property:

- **Waves 2-5 (rsync)**: rollback = re-run that wave (no flat-side delete yet; idempotent). Cost: 1 wave wall-clock.
- **Wave 6 (delegate flip)**: rollback = revert the workspace PR; deployment-api re-deploy; flat buckets are still
  active so writes resume. Cost: ~1h.
- **Wave 7 (write-pause LIFT)**: rollback = re-engage write-pause; investigate diverging writes. Cost: ~30min +
  manifest-state diff.

NEVER skip a verify; NEVER proceed to the next wave with an unresolved failure (per "Hard rule" above).

---

## Resolver domain-string contract (HARD RULE, codified 2026-06-01)

`resolve_bucket_name(domain, ...)` performs an exact lookup against the `_DOMAIN_TO_YAML_KIND` mapping in UTL
`cloud_interface/bucket_naming.py`. The `domain` argument **must** match the key in that dict verbatim.

**Valid examples**: `"market_data"`, `"instruments"`, `"features_delta_one"`.

**Invalid examples that silently fall through to the legacy flat name**:

- `"market-data-tick-cefi"` (hyphen-separated, asset-group suffix) — no match → falls back to the pre-env-tiered flat
  bucket name, bypassing the resolver entirely.
- Any free-form string not present as a key in `_DOMAIN_TO_YAML_KIND`.

**Why it matters**: a writer that bypasses the resolver via a malformed domain string will write to the _legacy flat_
bucket even after the env-tiered cutover, creating dual-write divergence that is invisible to QG STEP 5.69 (which only
checks inline `gs://` strings, not malformed domain arguments).

**2026-06-01 incident**: `market-tick-data-service` was passing `f"market-data-tick-{asset_group}"` as the domain
argument. The resolver found no match and silently returned the flat name; writers continued populating the old bucket
post-cutover. Fix: market-tick-data-service@0b575651 — changed callers to pass `"market_data"` (the canonical key).

**Rule**: when adding a new call to `resolve_bucket_name`, verify the domain string against `_DOMAIN_TO_YAML_KIND`
before merging.
`grep "_DOMAIN_TO_YAML_KIND" unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py` is the
source of truth.

---

## References

- Master plan:
  [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](../../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md)
  § Phase 2.6
- Bucket-name SSOT:
  [`plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`](../../plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md)
- Yaml SSOT:
  [`deployment-service/configs/cloud-providers.yaml`](../../../deployment-service/configs/cloud-providers.yaml)
- QG STEP 5.69 (inline-URI ratchet): `scripts/quality-gates-base/base-service.sh:1578-1623`
- VM watchdog:
  [`deployment-service/scripts/vm/vm_zombie_watchdog.py`](../../../deployment-service/scripts/vm/vm_zombie_watchdog.py)
  — `VM_PREFIX_TO_BUCKET` dict
