---
scope: [engineer]
status: stable
last_reviewed: 2026-05-17
last_reviewed_note: "Phase 9 audit 2026-05-15"
---

# VM launcher script SSOT — `deployment-service/scripts/vm/`

The deployment-UI is the workspace's single SSOT for **how do we launch a VM**. Every script that runs
`gcloud compute instances create` (or the AWS `aws ec2 run-instances` equivalent) MUST live under
[`deployment-service/scripts/vm/`](../../../deployment-service/scripts/vm/). No exceptions.

## Why this rule exists

1. **One registry the UI can render.** The Deploy-Missing button + the operational dashboards both read from
   `_SERVICE_LAUNCHER_SCRIPTS` in
   [`deployment_api/services/deploy_missing.py`](../../../deployment-api/deployment_api/services/deploy_missing.py).
   Scattered launchers can't be rendered by the UI; operators end up cargo-culting copies of bash that drift in shape
   over time.
2. **Workspace conventions land in one place.** Every launcher must set `MANIFEST_PER_VM_SHARDS=true`, a unique
   `VM_NAME=<unique-tag>`, `RUN_TS="$(date +%Y%m%d-%H%M%S)"`, and register the prefix in `VM_PREFIX_TO_BUCKET`
   (CLAUDE.md "VM Naming Convention"). Forgetting any of these breaks per-VM shard isolation, the zombie watchdog, or
   the manifest concurrency protocol.
3. **Parallel-agent reasoning.** When two operators / agents launch at the same time, every launcher in
   `deployment-service/scripts/vm/` follows the same patterns; an agent reading any one knows the contract.

## Scope: what counts as a "VM launcher"

| Pattern                                                                                                                      | Move to `deployment-service/scripts/vm/`?                                 |
| ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `gcloud compute instances create ...`                                                                                        | **Yes** — the canonical case.                                             |
| `gcloud beta compute instances create ...`                                                                                   | **Yes**.                                                                  |
| `aws ec2 run-instances ...`                                                                                                  | **Yes** — same SSOT, parallel `launch-*-ec2.sh` shape.                    |
| Cloud Build job that launches a VM as a side effect                                                                          | **Yes** — wrap the `gcloud` call in a launcher.                           |
| Local script (e.g. `instruments-service/scripts/local_fill_pairs.sh`) that runs in-process                                   | **No** — pure local-process orchestration; no VM.                         |
| Service-repo orchestration script (e.g. `run_vm_backfill_e2e.sh`) that **invokes** a launcher but doesn't itself create a VM | **No** — let it stay; just ensure it `bash`-execs the canonical launcher. |
| `setup.sh` / `run_local.sh` / `smoke_matrix.py`                                                                              | **No** — local dev / test scaffolding.                                    |

## How the script reaches the VM (4 modes; UI exposes a toggle)

When a launcher runs, the **VM at boot** needs the launcher's transitive dependencies (UAC / UTL / service source). Four
modes resolve this; the UI's Deploy-Missing flow exposes the first two as a radio toggle.

### 1. Tarball (default / production)

`gs://deployment-scripts-${PID}/code/<tarball>.tar.gz` → `setup-data-pipeline-vm.sh` extracts at boot → launcher
invoked. Refresh via:

```bash
bash deployment-service/scripts/vm/create-code-tarballs.sh --all
```

(or the per-asset_group variant). Stale tarball = stale code on the VM. Operators must remember to refresh when they
push fixes; the [`deploy_missing_auto_launch_2026_05_07`](../../plans/archive/deploy_missing_auto_launch_2026_05_07.md)
successor plan adds an automatic refresh step.

### 2. Tarball-from-local (developer path; Deploy-Missing UI mode toggle)

The UI's `DeployMissingButton` exposes a radio toggle:

- **preview** (default) — launcher invocation against the GCS tarball that's currently in the bucket. Safe in any
  environment; operator copies + runs from their authenticated terminal.
- **tarball-from-local** — pairs the launcher with `create-code-tarballs.sh --all` via `&&` so the VM boots the
  OPERATOR'S LOCAL working tree (uncommitted edits included). **ONLY works from the operator's workstation**, never from
  the deployment-api Cloud Run pod / CI runners / shared shells. The endpoint emits a `LOCAL-ONLY + UNCOMMITTED CHANGES`
  warning, surfaced in the UI as a prominent amber panel above the command.

Implementation:
[`deployment-api/deployment_api/services/deploy_missing.py`](../../../deployment-api/deployment_api/services/deploy_missing.py)

- [`deployment-ui/src/components/DeployMissingButton.tsx`](../../../deployment-ui/src/components/DeployMissingButton.tsx).

### 3. Sibling-clone (local-stack dev)

The operator's workstation has every service repo cloned as siblings under `${WORKSPACE_ROOT}` per the
workspace-manifest pattern. Local launches assume `deployment-service` exists at
`${WORKSPACE_ROOT}/deployment-service/scripts/vm/...`. CI / Cloud Run pods do NOT have sibling clones; they read from
the tarball.

### 4. Image (post-cutover — not yet shipped)

> **[DELTA 2026-05-22]** **Current state:** Image-based launcher delivery is NOT shipped. VM tarball
> (`create-code-tarballs.sh` + `launch-*.sh`) is the live path for all launchers. **Planned delta:** Image-based
> launcher tracked under `plans/epics/infrastructure_master.md`. **Target architecture:** Deployment-api pulls + runs
> per-shard launch container from Artifact Registry / ECR rather than `gcloud compute instances create`.

Bake the launcher set into a Docker image cached in Artifact Registry / ECR. The deployment-api would pull + run a
per-shard launch container rather than `gcloud compute instances create`-ing a fresh VM each time. Tracked in
[`deploy_missing_auto_launch_2026_05_07.md`](../../plans/archive/deploy_missing_auto_launch_2026_05_07.md); out of scope
post-cutover.

## Adding a new launcher

1. **File** — `deployment-service/scripts/vm/launch-{asset_group}-{flavor}-vm.sh` (or `launch-{operation}-vm.sh` for
   cross-asset ops).
2. **VM-name prefix** — register in
   [`VM_PREFIX_TO_BUCKET`](../../../deployment-service/scripts/vm/vm_zombie_watchdog.py) (CLAUDE.md "VM Naming
   Convention" rule). After the dict edit, **relaunch the watchdog VM** so it picks up the new prefix.
3. **Deploy-Missing registry** — add to
   [`_SERVICE_LAUNCHER_SCRIPTS`](../../../deployment-api/deployment_api/services/deploy_missing.py) if the launcher
   should be reachable from the Deploy-Missing UI button.
4. **Tarball inclusion** — if the launcher depends on code outside CORE (`UAC` / `UTL` / `MTDS` / `deployment-service`),
   add an `--include <repo>` line in `create-code-tarballs.sh` or use `--asset-group X` to include the right scope.

### Codified governance gaps (PRE_CUTOVER backlog, codified 2026-05-12)

Today every step above is **reviewer-discipline-only** — no automated check enforces a launcher registration. Two known
foot-guns:

- **Step 2 gap** — a new prefix added to `VM_PREFIX_TO_BUCKET` without a watchdog VM relaunch leaves the prefix
  un-watched. Reference incident 2026-05-05 (5 prefixes silently un-watched → zombie burn). **Proposed QG check**:
  correlate `git log -p deployment-service/scripts/vm/vm_zombie_watchdog.py | grep VM_PREFIX_TO_BUCKET` against the
  watchdog VM relaunch event in `gs://...vm-logs/vm-zombie-watchdog-*/EXIT_STATUS`. **Status**: design-gated;
  scaffolding policy codified below (§ "QG check policy"). Owner: governance + slot 11 (launcher-consolidation owner).
- **Step 3 gap** — a new launcher under `launch-*.sh` without a `_SERVICE_LAUNCHER_SCRIPTS` registration silently
  degrades the Deploy-Missing UI button to "no launcher registered" (per "What goes wrong" enumeration further down this
  doc). **Proposed QG check**: static dual-list parity check — every file matching `launch-*.sh` must appear in the dict
  (or in an explicit allowlist of "intentionally non-Deploy-Missing-reachable" launchers like internal-tooling /
  one-off-audit launchers). **Status**: design-gated; scaffolding policy codified below (§ "QG check policy"). Owner:
  governance + slot 11.

Both QG checks ship under the canonical **warning-with-baseline** policy (§ next). Tracked as PRE_CUTOVER backlog in
`plans/archive/issues/codex_audit_ops_2026_05_12.md` findings O-7 + O-8.

### QG check policy — warning-with-baseline pattern (codified 2026-05-12)

**Canonical policy for every NEW launcher-governance QG check** (and every NEW QG ratchet workspace-wide): ship as
**warning-with-baseline**, NOT auto-fail-on-day-1. Auto-fail would block every PR the moment the check lands because the
workspace inevitably has CURRENTLY-KNOWN occurrences that don't violate intent but trip the literal pattern.
Warning-with-baseline lets the check land green on day 1, then ratchet tighter as fixes ship.

**The shape** (each check has these 5 parts):

1. **Detection** — AST-walk (preferred) or grep with documented false-positive boundary. The check identifies every
   `(repo, file, line)` triple that matches the violation pattern.
2. **Baseline YAML** — `scripts/quality_gates/<check_name>_baseline.yaml` enumerates every CURRENTLY-KNOWN occurrence
   with a `status:` slot from a closed taxonomy + a `successor:` plan reference. Bootstrapped at check-introduction by a
   full workspace sweep.
3. **Behaviour** — for each detection: if `(repo, file, line)` is in baseline → WARNING (informational, exit-clean).
   Else → ERROR + `file:line` + the `successor:` from the baseline → exit 1. New occurrences fail; the existing tail
   doesn't.
4. **Clear cadence** — baseline entries are **DELETED** (not re-statused) as fixes land. The baseline shrinks toward
   zero. When the file is empty, the check is fully ratcheted and the warning surface disappears.
5. **Inline allowlist** — a documented inline marker (e.g. `# QG-allow: <reason>` on the same line) bypasses the check
   for the rare legitimate exception (test fixture / `**dict` kwargs / etc.). The marker is part of the contract, not an
   escape hatch.

**Exemplars in workspace** (read these before designing a new check):

- [`scripts/quality_gates/check_banned_placeholder_methods.py`](../../scripts/quality_gates/check_banned_placeholder_methods.py)
  with companion `check_banned_placeholder_methods_baseline.yaml` — the original warning-with-baseline scaffolding
  pattern.
- [`scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py`](../../scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py)
  with companion `pipeline_mode_explicit_baseline.yaml` — slot 8 shipped 2026-05-12 (Phase 4.GREP-VERIFY). AST-walk
  detection; per-method baseline tagged with `status: pending_phase_4_mtds | pending_phase_4_features`; `successor:`
  plumbed per entry; clear cadence by DELETE. Direct template for the O-7 + O-8 checks.

**Allowlist taxonomy (closed set)**: every baseline-YAML entry's `status:` field draws from a **closed set** of values
named per check (typically `pending_<phase>_<area>` shape) — never a free-form string. The taxonomy mirrors the
"successor plan" surface: each `status:` value names the active plan / phase that owns clearing it. Entries are
**deleted** (not re-statused) when the owning phase ships; the YAML is append-only at bootstrap, delete-only thereafter.
This shape matches the writegate plan's Phase 4.GREP-VERIFY ratchet idiom.

**Wiring**: each check is invoked from a numbered `STEP 5.NN` block in `scripts/quality-gates.sh` (and the per-repo
`scripts/quality-gates.sh` for service-scoped checks); a non-zero exit fails the gate. Until the day-1 baseline is
populated, the check MUST NOT be wired — green-on-introduction is the contract that prevents the check from being
disabled in frustration.

**Applies to**: O-7 (watchdog dict relaunch correlation) + O-8 (launcher → Deploy-Missing dict parity) per
`plans/archive/issues/codex_audit_ops_2026_05_12.md`. Both checks ship under this policy; the operator-design-gate is
the day-1 baseline payload (which currently-unwatched prefixes / unregistered launchers count as "known tolerated state
vs latent bug"), not the warning-vs-error toggle. Future launcher-governance checks (e.g. a
`MANIFEST_PER_VM_SHARDS=true` presence check across every `launch-*.sh`) ship under the same policy.

## features-service consolidation (2026-05-08)

The pre-2026-05-08 layout had 8 per-family launchers (`launch-features-onchain-vm.sh`,
`launch-features-volatility-vm.sh`, `launch-features-cross-instrument-vm.sh`, `launch-features-sports-vm.sh`,
`launch-features-calendar-vm.sh`, `launch-features-commodity-vm.sh`, `launch-features-delta-one-vm.sh`,
`launch-features-multi-timeframe-vm.sh`).

Per [`features_repo_consolidation_2026_05_08`](../../plans/active/features_repo_consolidation_2026_05_08.md) Phase 8A,
those 8 launchers collapse to a single `deployment-service/scripts/vm/launch-features-vm.sh` parameterised by
`--feature-family` + `--asset-group`. The consolidated launcher:

1. Reads `--feature-family` from its argv + validates against the UAC `FeatureFamily` StrEnum (8 members).
2. Reads `--asset-group` per the workspace VM-Naming convention.
3. Composes the VM name as `features-{asset_group_lower}-{feature_family}-{ts}` — e.g.
   `features-defi-onchain-20260508-152400`. The `features-` prefix is registered ONCE in `VM_PREFIX_TO_BUCKET`,
   replacing the 8 per-family prefixes that would otherwise be needed.
4. Boots with `python -m features_service --feature-family <X> ...` per the dispatcher contract in
   [`../04-architecture/features-service-architecture.md`](../04-architecture/features-service-architecture.md).

**Tarball impact**: `create-code-tarballs.sh --asset-group X` includes the single `features-service/` repo (rather than
the 8 prior `features-*-service` repos). The consolidated tarball is smaller (deduplicated boilerplate + shared common/
directory) and faster to refresh.

**Architecture SSOT**:
[`../04-architecture/features-service-architecture.md`](../04-architecture/features-service-architecture.md).

## Migration status (2026-05-10): 10 shipped Tab 11 + 20 deferred

The pre-2026-05-08 baseline of 29 ad-hoc VM launchers + 1 dashboard launcher outside `deployment-service/scripts/vm/`
has been substantially migrated. Per
[`plans/active/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`](../../plans/archive/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md)
DONE-2026-05-08 block: **10 launchers shipped Tab 11** (with 17 new VM_PREFIX_TO_BUCKET entries + watchdog VM relaunch);
the remaining **20 launchers are deferred** per documented per-launcher reasons (duplicates of canonical launchers,
collision-risk with in-flight tabs, partial supersession by canonical equivalents).

Source repo bucket counts (baseline 30):

| Source                                      | Count  | Pattern                                                |
| ------------------------------------------- | ------ | ------------------------------------------------------ |
| `e2e-testing/scripts/common/`               | 4      | `launch_*_vm.sh`                                       |
| `e2e-testing/scripts/defi/`                 | 10     | `launch_*_vm.sh`                                       |
| `e2e-testing/scripts/prediction/`           | 4      | `launch_*_vm.sh` + `setup-backfill-vm.sh`              |
| `e2e-testing/scripts/sports/`               | 10     | `launch_*_vm.sh` + sweep wrappers                      |
| `features-service (sports family)/scripts/` | 1      | `launch_parallel_backfill.sh`                          |
| `deployment-service/scripts/`               | 1      | `deploy-dashboard-gce-vm.sh` (move into `scripts/vm/`) |
| **Total**                                   | **30** |                                                        |

### Shipped 2026-05-08 (Tab 11 — 10 launchers)

| #   | Old path                                                               | New canonical path under `deployment-service/scripts/vm/` | Status + commit                                                |
| --- | ---------------------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------- |
| 1   | `e2e-testing/scripts/common/launch_mtds_category_backfill_vm.sh`       | `launch-mtds-backfill-vm.sh`                              | shipped — deployment-service@76f4ecc + e2e-testing@8daba1a     |
| 2   | `e2e-testing/scripts/common/launch_instruments_backfill_vms.sh`        | `launch-instruments-backfill-vm.sh`                       | shipped — deployment-service@fbb3673 + e2e-testing@2da6867     |
| 3   | `features-service (sports family)/scripts/launch_parallel_backfill.sh` | `launch-features-sports-parallel-backfill-vm.sh`          | shipped — deployment-service@0215086 + features-sports@06f6b30 |
| 4   | `e2e-testing/scripts/sports/launch_mtds_backfill_vm.sh`                | `launch-mtds-sports-odds-backfill-vm.sh`                  | shipped — deployment-service@2e1d967 + e2e-testing@deff088     |
| 5   | `e2e-testing/scripts/sports/launch_instruments_reference_v3.sh`        | `launch-sports-instruments-reference-vm.sh`               | shipped — deployment-service@fc9211e + e2e-testing@db7ace3     |
| 6   | `e2e-testing/scripts/defi/launch_dex_pools_vm.sh`                      | `launch-mtds-dex-pools-backfill-vm.sh`                    | shipped — deployment-service@5778811 + e2e-testing@43d8e49     |
| 7   | `e2e-testing/scripts/defi/launch_eigenlayer_rewards_vm.sh`             | `launch-mtds-eigenlayer-rewards-backfill-vm.sh`           | shipped — deployment-service@5778811 + e2e-testing@43d8e49     |
| 8   | `e2e-testing/scripts/defi/launch_solana_drift_vm.sh`                   | `launch-mtds-solana-drift-backfill-vm.sh`                 | shipped — deployment-service@5778811 + e2e-testing@43d8e49     |
| 9   | `e2e-testing/scripts/common/launch_cefi_migration_vm.sh`               | `launch-cefi-migration-vm.sh`                             | shipped — deployment-service@ce99d43 + e2e-testing@4f1f92b     |
| 10  | `e2e-testing/scripts/common/launch_defi_backfill_vm.sh`                | `launch-defi-backfill-vm.sh`                              | shipped — deployment-service@ce99d43 + e2e-testing@4f1f92b     |

**Migration shape** (each row): copy source → canonical destination, rename to canonical form, deprecation banner on old
path, register new prefix in `VM_PREFIX_TO_BUCKET`, smoke-test `--dry-run` (or `bash -n` syntax check), single-relaunch
of watchdog VM at end of cycle. **Watchdog VM** relaunched as `vm-zombie-watchdog-20260508-121344` after all 17 new
prefix entries landed.

### Deferred (20 launchers — documented reasons)

| Old path                                                          | Deferred reason                                                                                                                                        |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `e2e-testing/scripts/defi/launch_gas_fees_vm.sh`                  | DEFERRED — duplicate of canonical `launch-mtds-gas-fees-backfill-vm.sh`; reconcile in delete-vs-merge follow-up.                                       |
| `e2e-testing/scripts/defi/launch_gas_fees_fleet.sh`               | DEFERRED — duplicate (fleet wrapper) of canonical `launch-mtds-gas-fees-backfill-vm.sh`.                                                               |
| `e2e-testing/scripts/defi/launch_lst_rates_vm.sh`                 | DEFERRED — duplicate of canonical `launch-mtds-lst-rates-backfill-vm.sh`.                                                                              |
| `e2e-testing/scripts/defi/launch_lending_indices_vm.sh`           | DEFERRED — duplicate of canonical `launch-mtds-lending-indices-backfill-vm.sh`; **Tab 9 (`lending-indices-relaunch-tab`) in flight** — collision risk. |
| `e2e-testing/scripts/defi/launch_perp_funding_vm.sh`              | DEFERRED — duplicate; canonical `mtds-perp-funding-` prefix already in watchdog.                                                                       |
| `e2e-testing/scripts/defi/launch_solana_gas_vm.sh`                | DEFERRED — defer post-cutover.                                                                                                                         |
| `e2e-testing/scripts/defi/launch_liquidations_vm.sh`              | DEFERRED — defer post-cutover.                                                                                                                         |
| `e2e-testing/scripts/prediction/launch_prediction_backfill_vm.sh` | DEFERRED — **Tab 10 (`predictions-phase1-ingestion-tab`) in flight** on prediction surface; collision risk.                                            |
| `e2e-testing/scripts/prediction/launch_prediction_features_vm.sh` | DEFERRED — collision with Tab 10 in flight on prediction surface.                                                                                      |
| `e2e-testing/scripts/prediction/launch_prediction_pipeline_vm.sh` | DEFERRED — collision with Tab 10 in flight on prediction surface.                                                                                      |
| `e2e-testing/scripts/prediction/setup-backfill-vm.sh`             | DEFERRED — collision with Tab 10 in flight on prediction surface.                                                                                      |
| `e2e-testing/scripts/sports/full_api_football_sweep.sh`           | DEFERRED — orchestrator that wraps other launchers; defer.                                                                                             |
| `e2e-testing/scripts/sports/full_sports_entity_sweep.sh`          | DEFERRED — orchestrator that wraps other launchers; defer.                                                                                             |
| `e2e-testing/scripts/sports/launch_fss_features_v3.sh`            | DEFERRED — partially superseded by canonical `launch-features-sports-backfill-vm.sh`; reconcile in follow-up.                                          |
| `e2e-testing/scripts/sports/launch_fss_features_vm.sh`            | DEFERRED — partially superseded by canonical `launch-features-sports-backfill-vm.sh`; reconcile in follow-up.                                          |
| `e2e-testing/scripts/sports/launch_fss_phase3_backfill.sh`        | DEFERRED — partially superseded by canonical `launch-features-sports-backfill-vm.sh`; reconcile in follow-up.                                          |
| `e2e-testing/scripts/sports/launch_instruments_reference_vm.sh`   | DEFERRED — superseded by v3 form (#5 above).                                                                                                           |
| `e2e-testing/scripts/sports/launch_mdps_phase3_bucketing.sh`      | DEFERRED — partially superseded by canonical `launch-mdps-sports-bucket-vm.sh`; reconcile in follow-up.                                                |
| `e2e-testing/scripts/sports/launch_mdps_reprocess_vm.sh`          | DEFERRED — partially superseded by canonical `launch-mdps-sports-bucket-vm.sh`; reconcile in follow-up.                                                |
| `e2e-testing/scripts/sports/launch_oddspapi_vm_backfill.sh`       | DEFERRED — odds API specific; defer post-cutover.                                                                                                      |

**Intra-repo move not in the e2e-testing list** (separate item): `deployment-service/scripts/deploy-dashboard-gce-vm.sh`
→ `deployment-service/scripts/vm/launch-dashboard-vm.sh`. DEFERRED — already inside deployment-service repo so callsite
drift risk is contained; intra-repo move ships in a follow-up cycle.

**Per-asset-group rename intentions for follow-up cycles** (canonical-shape patterns; not single migrations):

| Old path                                                             | New path under `deployment-service/scripts/vm/`        | Status                                    |
| -------------------------------------------------------------------- | ------------------------------------------------------ | ----------------------------------------- |
| `e2e-testing/scripts/launch-cefi-backfill.sh`                        | `launch-cefi-{venue}-{flavor}-vm.sh`                   | per-venue migration pattern               |
| `e2e-testing/scripts/launch-tradfi-backfill.sh`                      | `launch-tradfi-{root}-{flavor}-vm.sh`                  | per-root migration pattern                |
| `e2e-testing/scripts/launch-sports-backfill.sh`                      | `launch-sports-{source}-vm.sh`                         | shipped (canonical sports launchers)      |
| `e2e-testing/scripts/launch-prediction-backfill.sh`                  | `launch-prediction-{venue}-vm.sh`                      | shipped (canonical prediction launchers)  |
| `e2e-testing/scripts/launch-defi-backfill.sh`                        | `launch-defi-{chain}-{flavor}-vm.sh`                   | per-chain migration pattern               |
| `features-service (onchain family)/scripts/launch-*.sh`              | `launch-features-onchain-vm.sh` (or asset-scoped)      | folds into features-service consolidation |
| `features-service (volatility family)/scripts/launch-*.sh`           | `launch-features-volatility-vm.sh`                     | folds into features-service consolidation |
| `features-service (cross-instrument family)/scripts/launch-*.sh`     | `launch-features-cross-instrument-vm.sh`               | folds into features-service consolidation |
| `features-service (sports family)/scripts/launch-*.sh`               | `launch-features-sports-vm.sh`                         | folds into features-service consolidation |
| `features-service (prediction family)/scripts/launch-*.sh`           | `launch-features-prediction-vm.sh`                     | folds into features-service consolidation |
| `deployment-service/scripts/deploy-dashboard-gce-vm.sh` (intra-repo) | `deployment-service/scripts/vm/launch-dashboard-vm.sh` | intra-repo move (deferred)                |

> **Folded in from `launcher-script-consolidation-2026-05-07.md`** (deleted by `codex_refactor_2026_05_08.md` Phase
> C.3).

Once a row is migrated:

1. The new launcher under `deployment-service/scripts/vm/` is canonical.
2. Its VM-name prefix is registered in `VM_PREFIX_TO_BUCKET`
   ([`vm-zombie-watchdog.py`](../../deployment-service/scripts/vm/vm_zombie_watchdog.py)).
3. The script is registered in `_SERVICE_LAUNCHER_SCRIPTS` in `deployment-api/deployment_api/services/deploy_missing.py`
   so the UI's Deploy-Missing button surfaces it.
4. The old path is removed from its home repo.
5. Tarballs are refreshed via `bash deployment-service/scripts/vm/create-code-tarballs.sh --all` so the new launcher's
   payload reaches the VM at boot.

### Why per-asset-group launchers (post features-service consolidation)

The features-service consolidation
([`../04-architecture/features-service-architecture.md`](../04-architecture/features-service-architecture.md)) collapses
5–6 features-\* repos into a single repo with sub-packages. The per-asset-group launchers (e.g.
`launch-features-cefi-vm.sh` for the colocated cefi cluster) replace the 5–6 per-repo launchers with one launcher per
deployment-cluster shape (asset-scoped vs cross-cutting).

### What goes wrong without this consolidation

- **Deploy-Missing UI button** can't render for unregistered services — operators run the ad-hoc script manually,
  bypassing the dashboard.
- **Watchdog blindness** — VMs with prefixes not in `VM_PREFIX_TO_BUCKET` zombie forever burning money on a network
  partition. (Reference 2026-05-05 incident: 5 prefixes silently zombied.)
- **Workspace conventions drift** — ad-hoc launchers forget `MANIFEST_PER_VM_SHARDS=true`, leading to manifest race bugs
  when concurrent VMs run.

Plan:
[`plans/ai/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`](../../plans/archive/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md).

Until the plan ships:

- Deploy-Missing UI button degrades to "no launcher registered" for services whose launcher hasn't migrated yet.
  Operators run the ad-hoc script manually from their terminal.
- Source-repo callsites (Makefiles / READMEs / GHA workflows) keep their current paths; the migration plan updates them
  in lockstep with each move.

## Strategy paper + live launchers (2026-05-12)

Added in Phase 1 of `promote_workflow_may23_cli_path_2026_05_10.md`:

| Launcher                      | VM prefix         | Purpose                                   |
| ----------------------------- | ----------------- | ----------------------------------------- |
| `launch-strategy-paper-vm.sh` | `strategy-paper-` | Tenderly paper-trade (no real capital)    |
| `launch-strategy-live-vm.sh`  | `strategy-live-`  | Copper MPC live-trade (real capital gate) |

Both prefixes registered in `VM_PREFIX_TO_BUCKET` (heartbeat-only). Watchdog VM bounced 2026-05-12 to pick up the new
prefixes (`vm-zombie-watchdog-20260512-184112`).

Full shape + tarball routing + known gaps: [`strategy-vm-launcher-shape.md`](strategy-vm-launcher-shape.md).

## Hardcoded-name vs prefix-{ts} naming patterns (O-19, added 2026-05-13)

Two naming patterns exist in `deployment-service/scripts/vm/` launchers with different watchdog + singleton
implications:

| Pattern                        | Example                                                    | Use case                                                                                                                     | Watchdog behaviour                                                                  | Singleton-lock behaviour                                                               |
| ------------------------------ | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **`prefix-{ts}`** (default)    | `mtds-cefi-backfill-20260508-152400`                       | Most backfill / one-shot VMs                                                                                                 | Watchdog kills idle VMs matching the prefix after timeout; multiple parallel VMs OK | None — concurrent runs allowed                                                         |
| **Hardcoded name** (singleton) | `vm-zombie-watchdog`, certain `strategy-paper-{archetype}` | Singleton services that MUST NOT run as duplicates (shared API keys, per-IP rate-limited adapters, kill-switch coordinators) | Watchdog skips kill-by-prefix (would self-terminate)                                | Launcher refuses launch if same-name VM RUNNING in zone; `--force` bypass for operator |

**Implications when adding a new launcher:**

1. **Choose the right pattern**: hardcoded name only for genuine singletons (shared rate-limited API, kill-switch
   coordinator, zombie-watchdog). Anything else → `prefix-{ts}`.
2. **Hardcoded-name singletons** still register their bare name as a prefix in `VM_PREFIX_TO_BUCKET` so the watchdog
   routes their logs correctly — but the watchdog's idle-kill logic must skip them (look at `vm_zombie_watchdog.py`
   skip-list).
3. **Singleton-lock check** lives in the launcher script itself — pattern from `launch-sfi-backfill-vm.sh` (SFI
   thundering-herd 2026-04-19 reference incident): query
   `gcloud compute instances list --filter='name=<hardcoded-name> AND status=RUNNING'`; if non-empty AND `--force` not
   passed → exit 1 with the running VM's creation timestamp + zone.
4. **Cross-ref**: CLAUDE.md "Singleton-locked launchers" rule + "No fire-and-forget VM launches" rule.

Reference: Sweep 3 of `codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md` (O-19 finding).

---

## Expected universe v2 launcher (2026-05-15, deployment-service@7313a39)

Added in Phase 2 of
[`expected_universe_v2_design_2026_05_08.md`](../../plans/active/expected_universe_v2_design_2026_05_08.md):

| Launcher                            | VM prefix               | Purpose                                             |
| ----------------------------------- | ----------------------- | --------------------------------------------------- |
| `launch-expected-universe-v2-vm.sh` | `expected-universe-v2-` | Instrument-grain expected universe enumeration (v2) |

**VM prefix** registered in `VM_PREFIX_TO_BUCKET` with value `None` (heartbeat-only; same pattern as v1
`expected-universe-enum-`). Watchdog bounces required after dict edit per plan Phase 2.

**Positional arg**: `asset_group` (cefi|defi|tradfi|sports|prediction). Optional: `--apply-write`, `--max-writes`,
`--catalog-gs-path`, `--force`, `--env`.

**Sharding**: cefi shards by venue (7 VMs × 1 venue each); sports/prediction/defi/tradfi run as one VM each (~10 VMs
total per full production launch).

**Status**: launcher shipped; Phase 4 (VM launches) blocked on G4 v8 schema landing + operator backfill approval (≥1
week GCS write). Phase 4 sequenced under `manifest_evolution_SUPERSEDED_2026_05_21` gate G3.

---

## B-011 blindspot audit — 8 prefixes registered (2026-05-15)

B-011 identified 8 VM name prefixes that existed in `launch-*.sh` launchers but were absent from `VM_PREFIX_TO_BUCKET`.
All 8 were missing heartbeat-only (bucket=`None`) entries — none use `MANIFEST_PER_VM_SHARDS`, so no shard-parquet path
check is needed. Registered in
[`deployment-service@97298f3`](https://github.com/IggyIkenna/deployment-service/commit/97298f3):

| Prefix                    | Launcher                              | Rationale                                                           |
| ------------------------- | ------------------------------------- | ------------------------------------------------------------------- |
| `defi-fwd-`               | `launch-defi-forward-poll.sh`         | DeFi on-chain forward poll, heartbeat-only                          |
| `prediction-fwd-`         | `launch-prediction-forward-poll.sh`   | Polymarket/Kalshi forward poll, heartbeat-only                      |
| `footystats-fwd-`         | `launch-footystats-forward-poll.sh`   | FootyStats entity poll, heartbeat-only                              |
| `sfi-fwd-`                | `launch-sfi-forward-poll.sh`          | SFI (SoccerFootballInfo) entity poll, heartbeat-only                |
| `sports-manifest-rescan-` | `launch-sports-manifest-rescan-vm.sh` | Covers coord+chunk VMs via `startswith()` check                     |
| `strategy-test-`          | `launch-strategy-test-vm.sh`          | CI strategy validation, heartbeat-only                              |
| `ml-train-`               | `launch-ml-training-vm.sh`            | ML model training, heartbeat-only                                   |
| `sports-scheduler-`       | `launch-sports-scheduler-vm.sh`       | Fixture trigger daemon; `_is_daemon()` exempts via `tier=scheduler` |

Post-audit state: `VM_PREFIX_TO_BUCKET` has 0 known blindspots. `test_vm_zombie_watchdog.py`
`_KNOWN_UNREGISTERED_PREFIXES` emptied; all 6 unit tests pass. Watchdog relaunched:
`vm-zombie-watchdog-20260515-110711`.

Reference: `plans/active/issues/b011_vm_prefix_watchdog_blindspots_2026_05_13.md`.

## Cloud Scheduler trigger SSOT (2026-05-15)

### Primary SSOT: Terraform

All Cloud Scheduler jobs are defined in `deployment-service/terraform/gcp/`:

| Terraform file                        | Scheduler job           | Cadence         |
| ------------------------------------- | ----------------------- | --------------- |
| `honest_coverage_scheduler.tf`        | `honest-coverage-daily` | 00:30 UTC daily |
| `qg_snapshot_scheduler.tf` (if wired) | `qg-snapshot-daily`     | 06:00 UTC daily |
| `catalogue_regen_scheduler.tf`        | catalogue regeneration  | periodic        |
| `manifest_consolidator_scheduler.tf`  | manifest consolidation  | periodic        |
| `t1_batch_scheduler.tf`               | T1 batch trigger        | daily           |
| others                                | see terraform/gcp/\*.tf | —               |

### `setup-*-scheduler.sh` scripts: IAM-exception pattern only

`setup-*-scheduler.sh` scripts exist ONLY when the Terraform plan cannot be applied by `harshkantariya@` due to
`cloudscheduler.jobs.create` requiring the owner account (Ikenna). One script exists:

- `setup-honest-coverage-scheduler.sh` — one-shot; requires `ikenna@odum-research.com`.

**Standard Cloud Scheduler → Cloud Run Job → GCE VM pattern:**

```
Cloud Scheduler (cron expression, UTC)
    └── Cloud Run Job: {name}-launcher
            └── GCE VM: {prefix}-{ts}  (launched via launch-{name}-vm.sh from GCS)
                    └── actual workload (measure_honest_coverage.py, snapshot.sh, etc.)
                            └── GCS output
```

**Template for new setup-\*-scheduler.sh** (copy from `setup-honest-coverage-scheduler.sh`):

- `PROJECT="central-element-323112"` + `REGION="asia-northeast1"`
- Verify Cloud Run Job exists before creating scheduler (fail-fast guard)
- `--dry-run` + `--update` flags
- `run()` helper that respects `$DRY_RUN`
- `--attempt-deadline="60s"`, `--oauth-service-account-email=cloud-scheduler@${PROJECT}.iam.gserviceaccount.com`
- IAM note in script header: who must run it and why

### Honest-coverage cron VM (2026-05-15)

```
Cloud Scheduler (30 0 * * * UTC)
    └── Cloud Run Job: honest-coverage-daily-launcher
            └── GCE VM: honest-coverage-{ts}
                    └── instruments-service/scripts/measure_honest_coverage.py
                            └── gs://central-element-323112-honest-coverage/{date}/coverage.json
```

**Terraform SSOT**: `deployment-service/terraform/gcp/honest_coverage_scheduler.tf`

**Launchers** (two — complementary, not duplicates):

- `launch-honest-coverage-vm.sh` — Cloud Scheduler-targeted; always `--asset-group all`; VM prefix `honest-coverage-`
- `launch-measure-honest-coverage-vm.sh` — ad-hoc; supports `--asset-group <filter>`; VM prefix
  `measure-honest-coverage-`

Both are uploaded to GCS at `gs://deployment-scripts-central-element-323112/vm/`.

**IAM note**: Cloud Scheduler creation requires `cloudscheduler.jobs.create` (Ikenna/owner territory). Operator setup:
`bash deployment-service/scripts/vm/setup-honest-coverage-scheduler.sh` (as ikenna@odum-research.com).
BLOCKED-OPERATOR-DECISION pending Ikenna confirmation (pings/slot_2.md 2026-05-15 05:30 UTC).

**VM prefixes registered in `VM_PREFIX_TO_BUCKET`** (both heartbeat-only, bucket=`None`):

- `honest-coverage-` — cron launcher prefix (registered 2026-05-15)
- `measure-honest-coverage-` — ad-hoc launcher prefix (registered 2026-05-10)

`VM_SHUTDOWN_ON_COMPLETION=true`. Machine: `e2-standard-2`, 50 GB.

**When to use this pattern** vs bare launcher: when the VM must be triggered on a schedule (cron) rather than
operator-launched. Cloud Scheduler → Cloud Run Job → GCE VM is the canonical path; Cloud Workflows was explored but
rejected (requires `workflows.workflows.create`, broader IAM surface, harder to audit).

## launcher_common.sh DRY library (Phase 8.A, 2026-05-15)

`deployment-service/scripts/vm/lib/launcher_common.sh` provides 6 shared functions extracted from repeated boilerplate
across 83+ launchers. Every **new** launcher MUST source this library and use these functions.

```bash
# Required at top of every new launcher:
# shellcheck source=lib/launcher_common.sh
source "$(dirname "$0")/lib/launcher_common.sh"
```

| Function                        | Purpose                                                                                                    |
| ------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `lc_validate_env VARS…`         | Asserts required env vars are non-empty; exits 1 with helpful message if any missing                       |
| `lc_singleton_check NAME`       | Exits 1 if a VM named `NAME` is RUNNING in the target zone; use for hardcoded-name singletons              |
| `lc_gcloud_create …`            | Thin wrapper around `gcloud compute instances create` — adds standard labels, retries, and dry-run support |
| `lc_code_bucket`                | Returns `deployment-scripts-${PROJECT}` — canonical `CODE_BUCKET` variable (no hardcoding)                 |
| `lc_run_ts`                     | Returns `$(date +%Y%m%d-%H%M%S)` — canonical `RUN_TS` value                                                |
| `lc_write_startup_file CONTENT` | Writes a startup script to a temp file + registers `EXIT` trap for cleanup; avoids manual `rm`             |

**Shipped**: deployment-service@d07576f. Three proof-of-concept launchers refactored: `launch-qg-snapshot-vm.sh` (−18
lines), `launch-canonical-smoke-vm.sh`, `launch-instruments-smoke-vm.sh`.

### Startup script templates (Phase 8.A, 2026-05-15)

Two canonical startup-script patterns extracted to `deployment-service/scripts/vm/templates/`:

| Template                         | Pattern                                                                 | Used by (approx) |
| -------------------------------- | ----------------------------------------------------------------------- | ---------------- |
| `startup-gcs-url.sh.tmpl`        | `startup-script-url=gs://${CODE_BUCKET}/vm/setup-data-pipeline-vm.sh`   | ~61 launchers    |
| `startup-inline-heredoc.sh.tmpl` | Inline HEREDOC startup script (for launchers that customise boot logic) | ~31 launchers    |

New launchers that customise startup logic MUST copy and fill the appropriate template rather than inventing ad-hoc
heredocs. **Shipped**: deployment-service@68a9943 (`lc_write_startup_file` + templates +
`launch-amm-golden-fixture-validation-vm.sh` refactored).

**Rule**: launchers that inline raw `gcloud compute instances create` without `lc_gcloud_create` are **review-blocking**
(no automated QG gate yet — future STEP candidate).

---

## Cloud Run launchers

Cloud Run deploy scripts are NOT VM launchers (they run `gcloud run deploy`, not `gcloud compute instances create`) and
do NOT need a `VM_PREFIX_TO_BUCKET` entry or watchdog registration. They live under
`deployment-service/scripts/cloud-run/` and follow the shape of `deploy-ui.sh`:

- `--env` flag required (rejects missing; supports `--env=prod|uat`)
- Triggers `docker buildx build` (local) or `gcloud builds submit` (Cloud Build) + `gcloud run deploy`
- Optional `firebase deploy --only hosting` at P2 (agent-orchestrator) or always (odum-portal)
- Note: `agent-orchestrator` has NO frontend in its Docker image (Vite dashboard served by Firebase Hosting at P2).
  `config/docker-build.env.{production,uat}` in the agent-orchestrator repo document runtime env vars only;
  `--set-env-vars` is used directly at deploy time rather than a build-arg file.

| Script                         | Target service            | Region       | Status  |
| ------------------------------ | ------------------------- | ------------ | ------- |
| `deploy-ui.sh`                 | unified-trading-system-ui | europe-west4 | shipped |
| `deploy-agent-orchestrator.sh` | agent-orchestrator        | europe-west4 | shipped |

`deploy-agent-orchestrator.sh` shipped at Phase 1 of
`plans/active/agent_orchestrator_cloud_run_deployment_2026_05_19.md`. Architecture SSOT:
`codex/04-architecture/agent-orchestrator-overview.md`.

---

## References

- CLAUDE.md "VM launcher script SSOT" rule (cursor-configs/CLAUDE.md, codified 2026-05-07).
- CLAUDE.md "VM tarball deployment" — `create-code-tarballs.sh --all` + boot path.
- CLAUDE.md "VM Naming Convention" — `VM_PREFIX_TO_BUCKET` registry.
- [`codex/05-infrastructure/vm-tarball-deployment.md`](vm-tarball-deployment.md) — tarball mechanics.
- [`codex/05-infrastructure/strategy-vm-launcher-shape.md`](strategy-vm-launcher-shape.md) — paper + live launcher SSOT.
- [`plans/ai/deploy_missing_auto_launch_2026_05_07.md`](../../plans/archive/deploy_missing_auto_launch_2026_05_07.md) —
  preview → auto-launch successor.
- [`plans/active/aws_migration_defi_first_2026_05_07.md`](../../plans/active/aws_migration_defi_first_2026_05_07.md) —
  bigger AWS S3 / ECR / EC2-launcher work.
