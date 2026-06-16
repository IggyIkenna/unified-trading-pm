---
title: features-service VM launch + verification runbook
status: active
audience: operator / dev
last_updated: 2026-05-08
scope: [engineer, admin]
execution:
  owner: operator (ad-hoc per backfill / per-asset_group cutover)
  cadence: per-deploy
  verifier: event-stream STARTED + per-instrument progress + STOPPED + manifest spot-check
  last_executed: NEVER
---

# features-service VM launch + verification runbook

## What this is

The operator-runnable recipe for launching a features-service VM (any of the 8 sub-package families across any viable
asset_group) **and** the event-stream + manifest verification protocol that turns each launch into a non-fire-and-forget
operation per the workspace "[No fire-and-forget VM launches](../../cursor-configs/CLAUDE.md#L139)" HARD RULE.

Consolidated launcher:
[`deployment-service/scripts/vm/launch-features-vm.sh`](../../../deployment-service/scripts/vm/launch-features-vm.sh)
(Phase 8A of
[`features_repo_consolidation_2026_05_08.md`](../../plans/active/features_repo_consolidation_2026_05_08.md)). This
single launcher supersedes the legacy per-family `launch-features-<family>-*.sh` scripts. Any reference to a per-family
launcher is stale — redirect to `--feature-family <name>`.

## Pre-launch checklist

Before invoking the launcher, verify:

1. **Code tarball is fresh**

   ```bash
   bash deployment-service/scripts/vm/create-code-tarballs.sh --all
   ```

   `--all` is the safest invocation; bare `create-code-tarballs.sh` only re-tars CORE (UAC/UTL/MTDS/deployment-service)
   and skips features-service. Forgetting `--all` is the #1 silent stale-code failure mode.

2. **`live-defi-rollout` is the active branch** in [`workspace-manifest.json`](../../../workspace-manifest.json)
   `active_feature_branch`. VMs pull tarballs from that branch; mismatch = stale code on the VM.

3. **Watchdog prefix registered.** `features-` is registered as heartbeat-only in
   [`deployment-service/scripts/vm/vm_zombie_watchdog.py:329`](../../../deployment-service/scripts/vm/vm_zombie_watchdog.py)
   covering all 8 families' VMs. No per-family entry needed; verify the dict still has `"features-": None` and the
   watchdog VM is RUNNING in `asia-northeast1-c`.

4. **Deploy-Missing UI registry pointer is correct.**
   [`deployment-api/deployment_api/services/deploy_missing.py:62`](../../../deployment-api/deployment_api/services/deploy_missing.py)
   `_SERVICE_LAUNCHER_SCRIPTS` contains `features-service` + every legacy `features-<family>-service` slug pointing at
   `launch-features-vm.sh`. Verified shipped pre-this-runbook.

5. **`--feature-family × --asset-group` cell is viable.** The launcher's `_is_viable_cell()` rejects unviable
   combinations. The 8-cell matrix:
   - `calendar` → CEFI / TRADFI / GLOBAL (GLOBAL = calendar-family special case)
   - `commodity` → TRADFI only
   - `cross_instrument` → CEFI / TRADFI / PREDICTION
   - `delta_one` → CEFI / DEFI / TRADFI / PREDICTION
   - `multi_timeframe` → CEFI / DEFI / TRADFI
   - `onchain` → DEFI only
   - `sports` → SPORTS only
   - `volatility` → CEFI / TRADFI

## Launch command

Standard form (per-family + per-asset_group cell):

```bash
bash deployment-service/scripts/vm/launch-features-vm.sh \
    --feature-family <name> \
    --asset-group <CEFI|DEFI|TRADFI|SPORTS|PREDICTION|GLOBAL> \
    --start-date YYYY-MM-DD \
    --end-date YYYY-MM-DD \
    --mode batch \
    --operation compute \
    --launch-mode full
```

Concrete examples:

```bash
# delta_one features for CEFI, full 6-year backfill
bash deployment-service/scripts/vm/launch-features-vm.sh \
    --feature-family delta_one --asset-group CEFI \
    --start-date 2020-01-01 --end-date 2026-04-18 --launch-mode full

# onchain features for DeFi (Solana + EVM chains)
bash deployment-service/scripts/vm/launch-features-vm.sh \
    --feature-family onchain --asset-group DEFI \
    --start-date 2020-01-01 --end-date 2026-04-18 --launch-mode full

# calendar (global; no --asset-group passed to underlying CLI)
bash deployment-service/scripts/vm/launch-features-vm.sh \
    --feature-family calendar --asset-group GLOBAL \
    --start-date 2020-01-01 --end-date 2026-04-18 --launch-mode full

# sports (per-league filter via FEATURE_GROUP env not supported for sports;
# see features_service/sports/cli for narrower selectors)
bash deployment-service/scripts/vm/launch-features-vm.sh \
    --feature-family sports --asset-group SPORTS \
    --start-date 2020-01-01 --end-date 2026-04-18 --launch-mode full
```

VM-name pattern: `features-{family-dashed}-{asset_group_lower}-{YYYYMMDD-HHMMSS}` (e.g.
`features-delta-one-cefi-20260508-141500`, `features-calendar-global-20260508-141500`).

`--launch-mode dry` only prints the gcloud invocation; `--launch-mode full` runs it. Use `dry` first when iterating on
arguments.

## Verification protocol (mandatory — per workspace HARD RULE)

`STATUS=RUNNING` from gcloud only means the VM is alive — NOT that the workload is making progress. Every launch is
paired with an active event-stream verification cycle. Skipping verification = fire-and-forget = banned.

### T+90s — STARTED event must exist

```bash
VM_NAME="features-delta-one-cefi-20260508-141500"   # whatever the launcher echoed
TODAY="$(date -u +%Y-%m-%d)"
PID="central-element-323112"

gcloud storage ls "gs://${PID}-events/events/features-service/${TODAY}/${VM_NAME}/" 2>&1
# Expected: at least one `hour=*/` partition listed.

# Read first JSONL, assert event=="STARTED"
gcloud storage cat "gs://${PID}-events/events/features-service/${TODAY}/${VM_NAME}/hour=*/events-*.jsonl" 2>&1 \
    | head -1 | python3 -c "import json,sys; e=json.loads(sys.stdin.read()); assert e['event']=='STARTED', e; print('OK', e)"
```

If the directory doesn't exist after 90s OR the first event is not `STARTED`: SSH the VM
(`gcloud compute ssh ${VM_NAME} --zone=asia-northeast1-c`), tail `/var/log/syslog` for boot errors, then
`gcloud compute instances delete ${VM_NAME} --zone=asia-northeast1-c --quiet` and diagnose the stack-trace. Common
boot-failure causes: stale tarball, missing UAC/UTL dep, missing GOOGLE_APPLICATION_CREDENTIALS, viability-cell typo
passed through the env.

### T+10–15min and onwards — per-instrument progress events

features-service adapters MUST emit per-instrument / per-feature_group progress events with row counts. Silent-success
with zero output is the empty-OHLC-bar failure mode (reference: 2026-05-05 MDPS 1440 NaN bars/day) — manifest says
`captured` but parquet is garbage. Per-instrument progress events make this detectable from the event stream alone.

```bash
# Look for INSTRUMENT_PROCESSED / FEATURE_GROUP_COMPUTED events with row_count > 0
gcloud storage cat "gs://${PID}-events/events/features-service/${TODAY}/${VM_NAME}/hour=*/events-*.jsonl" \
    | grep -E '"event":"(INSTRUMENT_PROCESSED|FEATURE_GROUP_COMPUTED|SHARD_WRITTEN)"' \
    | tail -20
```

If no progress events appear after 15min OR the events fire but `row_count` is consistently 0 across multiple shards:
the workload is silently broken. Kill the VM and inspect the last event's `metadata.details` for the diagnostic.

Recheck cadence: every 10–15min while the VM is running. Stalled progression = silent-broken. Production observability
runs through the [`unified-events-interface` UI](https://events.unified-trading-system.com); SSH-tailing logs is a dev
crutch.

### T+exit — STOPPED or FAILED with non-empty metadata

```bash
# After auto-shutdown (VM_SHUTDOWN_ON_COMPLETION=true), verify final event
gcloud storage cat "gs://${PID}-events/events/features-service/${TODAY}/${VM_NAME}/hour=*/events-*.jsonl" \
    | tail -1 | python3 -c "
import json, sys
e = json.loads(sys.stdin.read())
assert e['event'] in ('STOPPED', 'FAILED'), e
assert e.get('metadata', {}).get('details'), e
print('OK', e['event'], e['metadata']['details'])
"
```

If the final event is `FAILED`: read `metadata.details.error_class` + `error_reason` + `correlation_id`. Map error to a
workspace-recognised classification (UAC `classify_venue_error()`); decide retry vs root-cause-fix per the error code.

## Manifest verification — the operational truth

Event stream tells you WHAT the VM did; manifest tells you WHAT actually landed on disk. Both must be checked — passing
events with empty manifest = the silent-zero pattern (reference: 2026-05-07 RED ALERT, 5 CeFi VMs writing 96-100% empty
rows). Passing manifest with empty parquet = the empty-placeholder pattern (reference: 2026-05-05 MDPS 1440 NaN bars).

### Step 1 — manifest has captured rows for the run window

```bash
# Per-feature_family availability index lives in the canonical features bucket
gcloud storage ls "gs://${PID}-features-data/" | head -10

# For a given (asset_group, feature_family, day), confirm captured rows exist:
python3 -c "
from unified_trading_library.manifest import read_availability_index
df = read_availability_index('${PID}-features-data')
sub = df[(df['asset_group']=='cefi') & (df['feature_family']=='delta_one') & (df['day']>='2020-01-01') & (df['day']<='2020-01-31')]
print('captured rows:', (sub['capture_status']=='captured').sum())
print('empty_confirmed:', (sub['capture_status']=='empty_confirmed').sum())
print('attempted_failed:', (sub['capture_status']=='attempted_failed').sum())
print('expected_unattempted:', (sub['capture_status']=='expected_unattempted').sum())
"
```

Coverage % = `captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)`. The denominator is the
full universe (catalog × dates × data_types). Anything < 100% on a fully-completed backfill = investigate the
non-captured rows by class.

### Step 2 — sample a parquet, validate it isn't a placeholder

```bash
# Pick a random (asset_group, feature_family, day) shard from the run
SAMPLE_URI="gs://${PID}-features-data/asset_group=cefi/feature_family=delta_one/day=2020-01-15/<feature_group>/<instrument>.parquet"

python3 -c "
import pandas as pd
df = pd.read_parquet('${SAMPLE_URI}')
print('rows:', len(df))
print('columns:', df.columns.tolist())
print('available_at non-null:', df['available_at'].notna().sum(), '/', len(df))
print('NaN ratio per column:', df.isna().sum() / len(df))
print(df.head())
"
```

Sanity invariants per the workspace [`Honest absence vs fake placeholders`](../../cursor-configs/CLAUDE.md) HARD RULE:

- `len(df) > 0` — empty DataFrame would have triggered `record_empty(reason=<typed>)`, not `record_captured`.
- `available_at` populated (non-null) on every row — null means the writer skipped UTL's `assert_available_at_present`
  guard, which would normally raise `LookaheadBiasError` at write-time.
- NaN ratio per feature column < threshold (per-feature-group threshold; the 4 write-gate pillars).
- Schema columns match UAC `FeatureFamily` declaration (no extra columns, no missing required columns).

If any sanity invariant fails on a sample: the manifest is dishonest and the VM run did NOT actually complete. Open a
findings issue per the [`Findings Triage Discipline`](../../cursor-configs/CLAUDE.md#L1100) HARD RULE, classify as
case-5-big (data-correctness break for ≥1 asset_group), and notify the operator immediately.

## Downstream sample read

Final smoke: confirm a downstream consumer (ml-training-service / strategy-service) can actually consume the produced
features. This catches schema-drift bugs that manifest sanity-checks miss.

```bash
# ml-training-service feature provider sample
cd ml-training-service
python3 -c "
from ml_training_service.app.core.cloud_feature_provider import CloudFeatureProvider
provider = CloudFeatureProvider(asset_group='cefi', feature_family='delta_one')
df = provider.read_window(start_date='2020-01-15', end_date='2020-01-15', instruments=['BTC-USD'])
assert len(df) > 0, 'no rows'
assert 'available_at' in df.columns
print('OK:', len(df), 'rows')
"
```

Schema mismatches here = features-service writer + consumer reader drift. Either the writer dropped a column the
consumer needs, or the consumer expects a column the writer doesn't emit. Trace via the UAC `FeatureFamily` enum +
`FEATURE_GROUP_TO_FAMILY` registry — both sides must agree.

## Troubleshooting

| Symptom                                         | Likely cause                                                                                                                     | Fix                                                                                                                                                          |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Launcher rejects `--feature-family X`           | Typo or unviable cell                                                                                                            | Refer to viable matrix above; `_is_viable_cell` is the SSOT                                                                                                  |
| VM boots but no STARTED event in 90s            | Stale code tarball, missing dep, ServiceBootstrap import error                                                                   | SSH + tail syslog; rebuild tarball with `--all` flag                                                                                                         |
| STARTED fires but no progress events            | Adapter doesn't emit per-instrument progress events (silent-success risk)                                                        | Audit the family's adapter — every per-shard write should emit `INSTRUMENT_PROCESSED` or `SHARD_WRITTEN` with `row_count`                                    |
| Progress events fire with `row_count=0`         | Upstream dependency gap (MTDS / instruments-service didn't capture the date) OR reader schema drift                              | Run instruments-service phantom audit; re-run upstream backfill for missing dates per `Honest absence vs fake placeholders` rule (3-category model)          |
| Manifest shows `captured` but parquet is empty  | Writer lacks 4-pillar validation (row count + NaN ratio + schema + cluster coverage)                                             | Verify UTL `record_captured` is called with the df + cluster validation kwargs (mandatory for bundled data_types per `Cluster validation MANDATORY` rule)    |
| Downstream consumer ImportError                 | Stale `from features_<family>_service ...` import (banned post-consolidation per features-service-architecture.md anti-patterns) | Rewrite to `from features_service.<family> ...`. Workspace-grep audit per Phase 0 of features_repo_consolidation plan                                        |
| `feature_family` column missing from manifest   | UTL `ManifestWriter` not given `feature_family=` kwarg at write site                                                             | Use `add(feature_family=FeatureFamily.X, ...)` form. UAC `FEATURE_GROUP_TO_FAMILY` is the resolver; deployment-api also stamps via `_resolve_feature_family` |
| Deploy-Missing UI says "no launcher registered" | `_SERVICE_LAUNCHER_SCRIPTS` missing slug                                                                                         | Add slug → `launch-features-vm.sh` in deployment-api per workspace VM launcher SSOT                                                                          |

## Auto-recovery on FAILED

`features-service` adapters MUST classify errors through UAC `classify_venue_error()` and emit `ADAPTER_FETCH_FAILED`
events. Per the workspace `Shard-level failure isolation` rule, no per-shard failure should crash the whole run; the
adapter loop continues with other shards.

If the final event is `FAILED` rather than `STOPPED`:

1. Read `metadata.details.error_class` from the FAILED event.
2. Map to the failure category:
   - **Transient** (network / 429 / 5xx) → re-launch the VM with the same `--start-date / --end-date`. Manifest CAS
     skips already-`captured` rows; only the missed shards are retried.
   - **Schema drift** (calculator received unexpected upstream column shape) → fix the calculator + UAC schema
     declaration in lockstep; do NOT re-launch until both sides match.
   - **Upstream gap** (instruments-service or MTDS hasn't captured the dependency for that date) → run the upstream
     backfill first per the `Unexpected upstream-pipeline gap` rule (DependencyError fail-fast at the boundary).
   - **Lookahead bias** (`LookaheadBiasError` raised by the UTL gate) → audit the calculator's `available_at`
     consumption against the UAC `feature_group → required_inputs` DAG; the input-row's
     `available_at > target_ts - horizon` is the bug.
3. Re-launch only after the root cause is fixed. Repeated re-launches against the same broken root cause = wasted
   compute + manifest pollution.

## Cross-references

- [features-service architecture (codex/04-architecture)](../04-architecture/features-service-architecture.md) — the
  consolidated package layout + CLI dispatch contract + Health-API aggregator + UAC enum SSOT.
- [VM launcher SSOT (codex/05-infrastructure)](../05-infrastructure/launcher-script-ssot.md) — every launcher under
  `deployment-service/scripts/vm/`; tarball / sibling-clone / image deploy modes.
- [VM tarball deployment (codex/05-infrastructure)](../05-infrastructure/vm-tarball-deployment.md) — `--all` flag,
  refresh cadence.
- [Live-pipeline architecture (codex/05-infrastructure)](../05-infrastructure/live-pipeline-architecture.md) —
  features-asset-scoped vs features-cross-cutting cluster topology; live = batch principle.
- [Availability manifest + data status (codex/02-data)](../02-data/availability-manifest-and-data-status.md) — v5
  schema + 4-state taxonomy + `feature_family` column.
- [Honest absence downstream handling (codex/02-data)](../02-data/honest-absence-downstream-handling.md) — NaN
  tolerances + per-consumer pre-flight gates.
- [Plan-of-record (PM/plans/active)](../../plans/active/features_repo_consolidation_2026_05_08.md) — full consolidation
  plan with Phase 8A launcher commit + Phase 10 QG sweep result.

## Reviewer enforcement

Per workspace [`Runbook Execution-Owner SSOT`](../../cursor-configs/CLAUDE.md) HARD RULE, every periodic execution of
this runbook updates the `last_executed:` field above with the operator's evidence (event-stream link, VM name, sample
parquet URI). PRs that bump `last_executed:` without showing actual run evidence are review-blocked.
