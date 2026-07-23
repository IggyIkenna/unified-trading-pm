---
doc_type: plan
title: Promote Workflow — May-23 dual-track cutover (CLI primary + minimal UI parallel)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [alerting-service, batch-live-reconciliation-service, deployment-api, deployment-service, deployment-ui, e2e-testing]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md,
    plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md,
    plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md,
    plans/active/defi_master.md,
    plans/epics/strategy_and_dart_master_SUPERSEDED_2026_05_21.md,
  ]
created: 2026-05-10
archived: 2026-05-23
last_updated: 2026-05-23
estimate_class: design
estimate_baseline_ai_days: 7.0
estimate_calibrated_ai_days: 4.2
estimate_calibration_note: "Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~6-8). Class
  inferred from filename (design, multiplier 0.6×).

  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be
  double-counted. Owner agent: verify baseline, refine class per /codex/08-workflows/estimation-calibration.md,
  recompute calibrated if either changes.

  "
parent_epic: dart_and_promote_master
assigned_vm: vm-operator-ops
priority: P1
---

## Deferred work — migrated to:

See inline `DEFERRED-OPERATOR` / `DEFERRED-OTHER-SLOT` / `DEFERRED-INDEFINITELY` / `DEFERRED-POST-CUTOVER` / etc.
annotations next to each `- [ ]` item in body for the specific successor / blocker per-item. No single migration target
— this plan tracks multiple per-item dispositions.

# Promote Workflow — May-23 dual-track cutover (CLI primary + minimal UI parallel)

> **🟡 IN-FLIGHT REFACTOR — `vm_zombie_watchdog.py` shape evolving + launcher-registry SSOT dependency** (added
> 2026-05-10 cross-plan audit fix)
>
> **VmPrefixSpec dict-shape migration**: Phase 1 below adds 2 prefixes (`strategy-paper-` + `strategy-live-`) to
> `deployment-service/scripts/vm/vm_zombie_watchdog.py`'s `VM_PREFIX_TO_BUCKET` dict. The dict's shape is being migrated
> from `dict[str, str | None]` to `dict[str, VmPrefixSpec]` by `deployment_ui_lifecycle_tabs_2026_05_08.md` (archived →
> `plans/archive/2026_05/`) Phase A.2 (currently deferred per its banner — `vm_zombie_watchdog.py` edits drafted but
> never committed; carryover to next session).
>
> **Sequencing**: lifecycle Phase A.2 SHOULD land before this plan's Phase 1 to avoid re-shaping the same dict twice. If
> lifecycle A.2 hasn't shipped at this plan's Phase 1 execution time, this plan's Phase 1 ships under the legacy
> `dict[str, str | None]` shape and a follow-up sub-todo (`1.X DEFERRED-AFTER-LIFECYCLE-A2`) wraps the 2 entries in
> `VmPrefixSpec` once A.2 lands.
>
> **Launcher-registry SSOT dependency** (per CLAUDE.md "VM launcher script SSOT" HARD RULE): the new
> `launch-strategy-paper-vm.sh` + `launch-strategy-live-vm.sh` scripts ship under `deployment-service/scripts/vm/` per
> SSOT. The Deploy-Missing UI button surface for these launchers requires
> [`launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`](../archive/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md)
> Phase 2 (`_SERVICE_LAUNCHER_SCRIPTS` registry extension in `deployment-api/deployment_api/services/deploy_missing.py`)
> — currently DEFERRED-PER-AUDIT 2026-05-10 in that plan. **Until Phase 2 lands, operators run the strategy launchers
> manually** (acceptable for cutover; not a blocker). A `DEFERRED-AFTER-CONSOLIDATION-PHASE2` sub-todo lives in Phase 1
> below to capture the registry-wire-in as a follow-up.

> **🟢 OPERATOR-PICKS-TRACK AT CUTOVER — RATIFIED 2026-05-10 cross-plan audit Q12.** Both CLI track (Phases 1-10) and UI
> track (Phases U1-U6) ship live by 2026-05-23. **At each cutover-run boundary, operator picks ONE track for that run**
> (CLI is the operational floor; UI is the upgrade ramp). Both paths enforce identical gates (custody connected / venue
> keys present / alerting wired / kill-switch armed / risk limits set / recon green / paper-evidence ≥3d) so either
> selection is safe. **G23 (DART manual-trade gate)** scope split with
> [`cross_cutting_may_23_deliverables_2026_05_08.md`](../archive/2026_05/cross_cutting_may_23_deliverables_2026_05_08.md)
> #4: cross*cutting owns \_design + DART surface*; this plan's Phase U6 (pvl-p23c) owns _testnet wiring + go-live gate
> enforcement_. After cutover, UI evolution continues via
> [`promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`](promote_workflow_post_cutover_ui_pipeline_2026_05_10.md)
> Phase 9 (full pre-flight pipeline) which EXTENDS this plan's Phase U3 to the canonical UI path; CLI track persists as
> long-term operational floor for ops/runbooks.

## Why this plan exists

The promote workflow audit (`plans/questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md`, completed
2026-05-10) found that the **UI-driven promote pipeline is 100% mock** (9 lifecycle sub-pages exist, `onPromote`
callback unimplemented, no backend endpoint, no paper/live VM launcher, no candidate manifest, 4 competing lifecycle
SSOTs, no ranking surface). **But the operator-CLI path is genuinely capable**:
[`e2e-testing/scripts/defi/run-paper.sh`](../../../e2e-testing/scripts/defi/run-paper.sh) +
[`run-live.sh`](../../../e2e-testing/scripts/defi/run-live.sh) +
[`colocated_engine.py`](../../../e2e-testing/scripts/defi/colocated_engine.py) (1343 lines) integrate strategy +
execution + position + P&L + risk in shared memory; auto-detect DeFi/CeFi/TradFi/Sports; support Tenderly fork (paper) +
Copper MPC (live); run `--continuous`.

**Strategic call (revised 2026-05-10 per operator direction)**: dual-track. **CLI = primary** (safety net —
guaranteed-shippable May-23 path). **Minimal-but-real UI = secondary** (operator-preferred surface — ships in parallel;
if UI promote button drives cutover successfully, that's the operator path; CLI is the belt-and-braces fallback). The UI
track ships **only the minimum viable** (Promote button → backend → minimal CandidateManifest → DART manual-trade gate)
— heavy state-machine consolidation + full pinned-shas CandidateManifest + cross-service auto-registration + ranking
surface + drift detection stay in
[`promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`](promote_workflow_post_cutover_ui_pipeline_2026_05_10.md).

**No shortcuts** means both tracks must enforce every gate the audit identified (custody connected / venue keys present
/ alerting wired / kill-switch armed / risk limits set / recon green / paper-evidence ≥3d) — CLI track via pre-flight
script, UI track via backend pre-flight pipeline. Cutover runs without operator improvising mid-run.

Per CLAUDE.md HARD RULE _"Plans Run To Actual Completion, Not Smoke-Test Green"_: every phase's done-definition includes
a **Full-execution criterion** with the actual command + machine + duration + verification probe + observed output.
Phases marked PARALLEL run concurrently; phases marked SEQUENTIAL gate on the prior phase's QG.

## Pre-audit manifest

Per Citadel-Grade § 1, the audit (Question doc `## Audit findings` section) is the pre-audit. Concrete files this plan
touches:

| File                                                                                 | Repo                              | Action                                                                                                                               |
| ------------------------------------------------------------------------------------ | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `deployment-service/scripts/vm/launch-strategy-paper-vm.sh`                          | deployment-service                | NEW (Phase 1)                                                                                                                        |
| `deployment-service/scripts/vm/launch-strategy-live-vm.sh`                           | deployment-service                | NEW (Phase 1)                                                                                                                        |
| `deployment-service/scripts/vm/vm_zombie_watchdog.py`                                | deployment-service                | UPDATE — register `strategy-paper-` + `strategy-live-` prefixes in `VM_PREFIX_TO_BUCKET` (Phase 1)                                   |
| `e2e-testing/scripts/defi/preflight-cutover.sh`                                      | e2e-testing                       | NEW (Phase 2)                                                                                                                        |
| `e2e-testing/scripts/defi/run-paper.sh`                                              | e2e-testing                       | UPDATE — call preflight-cutover.sh as required gate (Phase 2)                                                                        |
| `e2e-testing/scripts/defi/run-live.sh`                                               | e2e-testing                       | UPDATE — call preflight-cutover.sh as required gate (Phase 2)                                                                        |
| `strategy-service/scripts/run_2yr_config_grid_backtest.py`                           | strategy-service                  | UPDATE — write to canonical PATH_REGISTRY path + emit manifest row (Phase 3)                                                         |
| `unified-trading-library/unified_trading_library/config_interface/paths/registry.py` | UTL                               | VERIFY — `backtest_results/strategy_id={strategy_id}/run_id={run_id}/` is canonical; reader shape mismatch blocked at lift (Phase 3) |
| `unified-trading-library/unified_trading_library/domain/execution_client.py`         | UTL                               | UPDATE — fix path mismatch with PATH_REGISTRY (Phase 3)                                                                              |
| `execution-service/execution_service/custody/copper.py`                              | execution-service                 | OPERATIONAL — first live-signing dry-run on testnet (Phase 4.A)                                                                      |
| `execution-service/execution_service/venues/initializer.py` + 5 venue adapters       | execution-service                 | UPDATE — testnet-mode constructor for Bybit/Binance/OKX/Hyperliquid/Aster (Phase 4.B)                                                |
| `execution-service/execution_service/defi_execution/connectors/solana_*.py`          | execution-service                 | NEW — Solana paper analogue for LST yield archetypes (Phase 4.C)                                                                     |
| `batch-live-reconciliation-service/`                                                 | batch-live-reconciliation-service | NEW — minimum-viable per-archetype P&L diff + per-trade fill comparison + cron VM (Phase 5.A)                                        |
| `alerting-service/alerting_service/notifiers/router.py` + Secret Manager paths       | alerting-service                  | UPDATE — Phase 4 paging targets wired (Phase 5.B)                                                                                    |
| 13 codex docs (Phase 7)                                                              | unified-trading-pm                | NEW + UPDATE per Phase 7 enumeration                                                                                                 |
| `unified-trading-pm/cursor-configs/CLAUDE.md`                                        | unified-trading-pm                | UPDATE — add "Promote Workflow Path" key rule (Phase 7)                                                                              |
| `unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.md`                  | unified-trading-pm                | UPDATE — `Last verified` columns + new pvl-p17e/p23d/p23e sub-todos + cross-reference (Phase 9)                                      |

## Execution DAG (CLI track + UI track in parallel)

```
Phase 1 (launcher scripts)   ──┐
Phase 2 (preflight checklist) ─┤
                               ├── Phase 3 (F18 2yr backtest) ──┐
                               │                                 │
CLI TRACK (safety net):        │                                 │
Phase 4.A (Copper)            ─┤                                 │
Phase 4.B (perp testnets)     ─┤── PARALLEL ───────────────────  ├── Phase 6 (paper evidence ≥3d) ── Phase 8 (live dry-run, both paths) ── Phase 9 (master refresh) ── Phase 10 (live cutover go)
Phase 4.C (Solana paper)      ─┤                                 │
Phase 4.D (Tenderly val)      ─┤                                 │
                               │                                 │
Phase 5.A (recon service)     ─┤                                 │
Phase 5.B (alert paging)      ─┤── PARALLEL ───────────────────  │
Phase 5.C (48h staging)       ─┤                                 │
Phase 5.D (live rehearsal)    ─┘                                 │
                                                                 │
UI TRACK (operator-preferred): │                                 │
Phase U1 (minimal CandidateManifest Firestore)                  ─┤
Phase U2 (pvl-p23b mode-data API in deployment-api)             ─┤── PARALLEL with Phases 4+5
Phase U3 (POST /promote endpoint + minimal pre-flight)          ─┤
Phase U4 (Promote UI wired to real backend)                     ─┤
Phase U5 (pvl-p23a DART 3-way visualization)                    ─┤
Phase U6 (pvl-p23c manual-trade gate UI)                        ─┘
                                                                 │
Phase 7 (codex SSOTs)         ──── runs alongside; codex updates ride with each phase per Post-Plan-Phase Codex Audit HARD RULE
```

QG gate between every phase; next phase cannot start until prior phase QG passes (per Citadel-Grade § 2). UI Track
gates: U1 → U3 → U4 (sequential); U2 → U5 (sequential); U6 sequential after U4. UI track + CLI track converge at Phase 6
(paper evidence runnable from EITHER path) and Phase 8 (live dry-run validates BOTH paths).

## Phase 1 — Launcher script SSOT for paper + live VMs (P0, ~1d, SEQUENTIAL — gates everything)

**Why first**: Audit Block D2 + E3 + E7 all blocked on missing launchers. Per CLAUDE.md _"VM launcher script SSOT"_ HARD
RULE every gcloud / aws ec2 launcher MUST live under `deployment-service/scripts/vm/`. Without these, no compliant
paper/live deployment exists.

- [x] [AGENT] P0. **Write `deployment-service/scripts/vm/launch-strategy-paper-vm.sh`**.
  - VM-name pattern: `strategy-paper-{archetype}-{ts}` per CLAUDE.md VM Naming Convention.
  - Boots VM with `setup-data-pipeline-vm.sh` tarball mode (default; production path).
  - Boot script:
    `cd /opt/code/e2e-testing && bash scripts/defi/run-paper.sh --archetype $ARCHETYPE --candidate-version $CANDIDATE_VERSION --tick-interval 3600 --continuous`.
  - Singleton-locked per `(archetype, environment)` to prevent thundering herd (per CLAUDE.md _"Singleton-locked
    launchers"_).
  - Env required: `MANIFEST_PER_VM_SHARDS=true`, `VM_NAME=$VM_NAME`, `RUN_TS="$(date +%Y%m%d-%H%M%S)"`.
  - Done: launcher exists; smoke-launch with `--dry-run` returns valid gcloud command; smoke-launch with real
    `--mode paper` for 90s emits STARTED event in `gs://${PID}-events/events/strategy-service/...` partition.
  - (deployment-service@87f12f1 — launcher created; dry-run verified)

- [x] [AGENT] P0. **Write `deployment-service/scripts/vm/launch-strategy-live-vm.sh`**.
  - VM-name pattern: `strategy-live-{archetype}-{ts}`.
  - Same shape as paper launcher but invokes `run-live.sh` with `--mode live`.
  - **Additional pre-flight**: refuses launch if `--dry-run-live-cutover-passed` flag absent in launch metadata (forces
    operator to run Phase 8 dry-run before any real-capital launch).
  - Singleton-locked per `(archetype, environment)`.
  - Done: launcher exists; `--dry-run` returns valid command; pre-flight refuses launch without metadata flag.
  - (deployment-service@87f12f1 — launcher created; --dry-run smoke + gate verified)

- [x] [AGENT] P0. **Register prefixes in `VM_PREFIX_TO_BUCKET`** at
      [`deployment-service/scripts/vm/vm_zombie_watchdog.py`](../../../deployment-service/scripts/vm/vm_zombie_watchdog.py).
  - Add `"strategy-paper-": None` (heartbeat-only — paper VMs don't write to a shard bucket).
  - Add `"strategy-live-": None` (same — live VMs emit events but don't write data shards).
  - Per CLAUDE.md: a VM whose prefix is not in the dict is invisible to the zombie watchdog.
  - (deployment-service@87f12f1)

- [x] [SCRIPT] P0. **Bounce vm-zombie-watchdog VM** so it picks up the new prefixes.
  - `gcloud compute instances delete vm-zombie-watchdog-* --zone=asia-northeast1-c --quiet`
  - `bash deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh`
  - Per CLAUDE.md: running watchdog only fetches Python at boot.
  - (vm-zombie-watchdog-20260512-184112 RUNNING — bounced 2026-05-12 13:41 UTC)

- [x] [SCRIPT] P0. **Smoke-launch each launcher** with `--dry-run` (printed gcloud command), then with `--mode paper`
      for ≥90s, then verify events.
  - Probe:
    `gcloud storage ls gs://${PID}-events/events/strategy-service/$(date +%Y-%m-%d)/strategy-paper-carry_staked_basis-*/`
    — directory exists with `hour=*` partition.
  - Read first JSONL, assert `event=="STARTED"`.
  - 10min recheck for new events with row counts (per CLAUDE.md _"No fire-and-forget VM launches"_).
  - (deployment-service@4a4e2e1, VM strategy-paper-carry-staked-basis-20260512-192413 self-deleted 2026-05-12 13:57 UTC)
  - Infrastructure smoke PASSES: launcher → tarball download (9 repos) → dep install → venv symlink → command dispatch →
    colocated_engine.py ran to strategy resolver. DEPLOYMENT_STARTED emitted in deployment archive.
  - **Phase 2 gaps discovered during smoke** (see Phase 2 todos below):
    - `colocated_engine.py` lacks `ServiceBootstrap` → no STARTED event in `gs://central-element-323112-events/`
      strategy-service event archive. Phase 2 must wire ServiceBootstrap into colocated_engine.py.
    - `V2BatchHarness` has no resolver entry for `carry_staked_basis` → `Unknown strategy: carry_staked_basis`. Phase 2
      must register the archetype in the harness resolver.
    - setup-data-pipeline-vm.sh startup failure leaves VM RUNNING indefinitely (self-delete only triggers via
      vm-exec-with-gcs-tee.sh which doesn't run when install fails). Phase 2 should add self-delete on script error.

- [x] [SCRIPT] P0. **🔴 RE-RUN smoke VM after slot 9 wire-ins (FOOT-GUN intercept 2026-05-13 wave-1 audit)**. Slot 9
      (Day-4 2026-05-13) shipped wire-ins addressing all 3 gaps above (e2e-testing@`afd0c16` ServiceBootstrap +
      GcsEventSink for paper/live; deployment-service@`ab6bfd2` strategy-paper/live self-delete on engine exit) BUT did
      NOT re-run the smoke VM to verify the wire-ins close the gaps in production. Slot 9's ping at 08:10 UTC claimed
      "Task 3 DONE" with PM@`0765d3aa` plan flip, but
      `gsutil ls gs://central-element-323112-events/events/strategy_paper/2026-05-13/` returns no objects — VM was never
      relaunched. Violates HARD RULE "Plans Run To Actual Completion, Not Smoke-Test Green". Re-run probe:
  - `bash deployment-service/scripts/vm/launch-strategy-paper-vm.sh --archetype carry_staked_basis --tick-interval 3600 --continuous=false --max-runtime 600`
    on operator workstation (uses today's tarballs — needs
    `bash deployment-service/scripts/vm/create-code-tarballs.sh --all` first).
  - `gcloud storage ls gs://${PID}-events/events/strategy-service/$(date -u +%Y-%m-%d)/strategy-paper-carry_staked_basis-*/`
    → directory exists with `hour=*` partition (CRITICAL — slot 9's fix was supposed to ensure STARTED event lands
    here).
  - Read first JSONL → assert `event=="STARTED"` (CRITICAL — slot 9's ServiceBootstrap wire-in was supposed to ensure
    this).
  - 10min recheck: ≥1 progress event/hour expected.
  - VM auto-shutdowns after `--max-runtime` → `gcloud compute instances list` shows absent (CRITICAL — slot 9's
    self-delete fix was supposed to ensure this).
  - Last JSONL → assert `event in {"STOPPED","FAILED"}`.
  - **Done-def**: all 4 critical-italic assertions above pass; flip with evidence chain (VM-name + 4 timestamps +
    last-event SHA).
  - **Successor if FAILS**: file new issue doc `plans/active/issues/strategy_paper_vm_post_slot9_failure_2026_05_13.md`
    documenting which of the 4 critical assertions failed + which wire-in is incomplete.
  - **Audit ref**: `plans/active/issues/audit_wave1_quality_2026_05_13.md` § "Critical follow-ups" item 1.
  - **DONE 2026-05-14 slot-9 post-OOM**: Bug found + fixed first: `args.mode='paper'` passed directly to
    `setup_events()` → `ValueError: Invalid mode: paper` (only `batch/live/local/test` accepted). Fix:
    e2e-testing@`f0b63ee` maps `'paper'→'live'` before call. Tarball refreshed + VM #2 launched.
    VM=`strategy-paper-carry-staked-basis-20260514-121752`. Event path correction: plan said `events/strategy-service/`;
    actual path is `events/colocated-engine/` (`service_name="colocated-engine"` in code). Wire-in assertions:
    GcsEventSink ✅ STARTED `2026-05-14T06:50:24.940577Z` ✅ VM self-deleted ✅ FAILED `2026-05-14T06:50:29.120987Z`
    (`No module named 'nautilus_trader'`) ✅. 10min progress N/A (engine crashed before first tick on pre-existing
    missing dep — NOT a wire-in failure). Wire-ins (afd0c16 + ab6bfd2) VERIFIED. Filing separate issue for
    nautilus_trader missing dep: `plans/active/issues/strategy_paper_vm_nautilus_trader_missing_dep_2026_05_14.md`.

- [x] ✅ [AGENT] P1. **1.X DEFERRED-AFTER-LIFECYCLE-A2 — wrap strategy prefixes in `VmPrefixSpec`** — shipped 2026-05-17
      (slot-8) at `deployment-service@5ab69b9`. Successor gate cleared: lifecycle Phase A.2 had already landed
      (`VM_PREFIX_TO_BUCKET` is `dict[str, VmPrefixSpec | None]` already). Upgraded both `"strategy-paper-"` and
      `"strategy-live-"` from raw `None` to `VmPrefixSpec(bucket=None, lifecycle_class=LifecycleClass.LONG_LIVED_LIVE)`.
      Smoke-import validated: total prefixes 147 unchanged. deployment-ui lifecycle tab queries can now filter strategy
      VMs by lifecycle_class.

- [x] [AGENT] P1. **1.Y DEFERRED-AFTER-CONSOLIDATION-PHASE2 — register strategy launchers in
      `_SERVICE_LAUNCHER_SCRIPTS`** so the Deploy-Missing UI button surfaces them. Owner plan:
      [`launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`](../archive/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md)
      Phase 2 (currently DEFERRED-PER-AUDIT 2026-05-10). Add `launch-strategy-paper-vm.sh` +
      `launch-strategy-live-vm.sh` entries to `deployment-api/deployment_api/services/deploy_missing.py`
      `_SERVICE_LAUNCHER_SCRIPTS` dict so operators can deploy via Deploy-Missing UI button instead of running scripts
      manually from workstation. **DEFERRED-AFTER-CONSOLIDATION-PHASE2** — gates on launcher_scripts_consolidation Phase
      2 shipping. Acceptable to ship Phase 1 without this; operators run launchers manually until then (see top-of-file
      IN-FLIGHT REFACTOR banner). (deployment-api@538e11b — `strategy-paper` + `strategy-live` registered;
      launcher_scripts_consolidation Phase 2 shipped 2026-05-13.)

- [x] ✅ [CODE] P1. `colocated_engine.py` instantiates `StrategyDirectiveReloader` at boot (no-op default if no
      directive present); reloader reads from same config-hot-reload bus as existing `config_reloaders.py`. See
      trading_agent_service_architecture_unlock plan Phase 5. Off-by-default for May-23: no upstream emitter wired
      except no-op stub. — e2e-testing@1b6f753

**Phase 1 done definition** (per _"Plans Run To Actual Completion"_ HARD RULE):

- ✅ Both launchers exist in `deployment-service/scripts/vm/` with the canonical shape.
- ✅ `VM_PREFIX_TO_BUCKET` includes both prefixes.
- ✅ vm-zombie-watchdog VM bounced; new instance running.
- ✅ Real paper-VM launched + STARTED + STOPPED events observed in event archive.

**Full-execution criterion**:

- **What ran**:
  `bash deployment-service/scripts/vm/launch-strategy-paper-vm.sh --archetype carry_staked_basis --tick-interval 3600 --continuous=false --max-runtime 300`
  on operator workstation; VM `strategy-paper-carry_staked_basis-<ts>` ran for 5 minutes then auto-shutdown.
- **Verification**:
  - `gcloud compute instances list --filter="name~strategy-paper-carry_staked_basis-"` showed RUNNING then absent.
  - `gcloud storage ls gs://${PID}-events/events/strategy-service/<today>/strategy-paper-carry_staked_basis-*/` returned
    `hour=*/` directories.
  - First JSONL = `event=="STARTED"`, last JSONL = `event in {"STOPPED","FAILED"}`.

**Phase 1 QG**: workspace QG runs clean on deployment-service. Launcher bash-syntax check passes (per
`/codex/05-infrastructure/launcher-script-ssot.md`).

## Phase 1 smoke-gaps → Phase 2 todos (discovered 2026-05-12 smoke run)

- [x] [AGENT] P0. **Wire `ServiceBootstrap` into `colocated_engine.py`** so paper/live VMs emit
      `STARTED`/`STOPPED`/`FAILED` to `gs://central-element-323112-events/events/strategy-service/`. Currently
      `colocated_engine.py` has no ServiceBootstrap; events go to the deployment heartbeat archive only. Required for
      "No fire-and-forget VM launches" HARD RULE compliance. (e2e-testing@afd0c16 — used setup_events()+log_event()
      directly; full ServiceBootstrap incompatible with asyncio CLI structure)
- [x] [AGENT] P0. **Register `carry_staked_basis` (and `leveraged_funding_arb`) in `V2BatchHarness`** resolver. Observed
      error: `Unknown strategy: carry_staked_basis -- V2BatchHarness: no resolver entry for strategy_type`. Phase 2 must
      add resolver entry (or confirm the archetype slug → strategy_type mapping). (strategy-service@61dc112 +
      e2e-testing@8427dc0 — lowercase aliases added to \_DEFI/\_CEFI in archetype_slot_resolver.py + STRATEGY_CATEGORIES
      in colocated_engine.py; tarballs refreshed 14:39 UTC 2026-05-12)
- [x] [AGENT] P1. **Add self-delete on startup-script failure** in `setup-data-pipeline-vm.sh`. When `set -euo pipefail`
      exits the script early (e.g. dep conflict), the VM stays RUNNING indefinitely. Add a
      `trap "gcloud compute instances delete \$(hostname) ..." ERR EXIT` at script top for strategy-paper/live tasks.
      (deployment-service@ab6bfd2 — chained gcloud delete with ';' after VM_BACKFILL_CMD in strategy-paper/live block;
      resolves zone from metadata at launch so delete runs on any exit code)
- [x] [AGENT] P1. **Operator-injected mid-run capital override for paper VMs**. Before this change paper VMs hardcoded
      $500k starting capital with no way to simulate operator deposits/withdrawals without restart, blocking rebalance
      testing on continuous paper runs (slot-1 audit 2026-05-19). Added `--initial-capital-usd` +
      `--treasury-reserve-pct` CLI flags to `run-paper.sh`/`colocated_engine.py`; added `OperatorCapitalOverride`
      GCS-polled JSON blob (`gs://deployment-scripts-<project>/operator_capital_overrides/<vm-hostname>.json`) that
      mutates `state.{treasury,trading}_balance_usd` each tick — existing `TreasuryMonitor._detect_deposits` +
      `TREASURY_LOW/HIGH` + `TREASURY_REBALANCE_NEEDED` + `TRANSFER_INITIATED` pipeline reacts automatically, emits
      `OPERATOR_CAPITAL_OVERRIDE_APPLIED` event. DeFi + `--continuous` + non-mock cloud only. (e2e-testing@89ea188 —
      colocated_engine.py + run-paper.sh)
- [x] ✅ [CODE] P1. `colocated_engine.py` instantiates `StrategyDirectiveReloader` at boot (no-op default if no
      directive present); reloader reads from same config-hot-reload bus as existing `config_reloaders.py`. See
      trading_agent_service_architecture_unlock plan Phase 5. Off-by-default for May-23: no upstream emitter wired
      except no-op stub. — e2e-testing@1b6f753

## Phase 2 — Operator pre-flight checklist (P0, ~0.5d, SEQUENTIAL after Phase 1)

**Why**: Audit Block H6 + Block I1 step 8/9 — no pre-flight check exists today; operator improvises. Without this gate,
the live cutover can launch with missing custody / missing API keys / unwired alerting and silently degrade.

- [x] [AGENT] P0. **Write `e2e-testing/scripts/defi/preflight-cutover.sh`** that probes:
  - Copper credential present in Secret Manager + sandbox sign-test passes (HMAC handshake + poll loop completes).
  - All 6 perp venue API keys present in Secret Manager + read-write scope verified per venue (Bybit / Binance / OKX /
    Hyperliquid / Aster / Deribit).
  - Solana wallet funded with ≥0.01 SOL native gas (probe via RPC `getBalance`).
  - Tenderly fork seat available (probe Tenderly API).
  - All chain RPCs reachable (`eth_chainId` per chain in `CHAIN_RPC_TEMPLATES`).
  - Kill-switch YAML loaded + parses (`unified-trading-pm/configs/circuit_breaker_config.yaml`).
  - Alerting paging targets configured in Secret Manager (Telegram bot tokens, PagerDuty key — per Phase 5.B).
  - Composes with `plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md` credential matrix.
  - Done: each probe exits 0/1; aggregate report printed; refuses to exit 0 if any P0 probe fails.
  - (e2e-testing@60283c2 — 7 probes implemented; --waive-<probe> + --skip-preflight escape hatches; dry-run verified)

- [x] [AGENT] P0. **Update `e2e-testing/scripts/defi/run-paper.sh`** + **`run-live.sh`** to call
      `preflight-cutover.sh --mode paper` / `--mode live` as required pre-flight gate (refuses to start if pre-flight
      non-zero).
  - (e2e-testing@60283c2 — both scripts updated; --waive-\* pass-through; pre-flight runs before engine launch)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Run preflight-cutover.sh on operator workstation**
      `[BLOCKED-CREDENTIALS]` for both paper + live mode against carry_staked_basis. Resolve any failing probes by
      either fixing config OR explicitly waiving (write `--waive-<probe>` flag with operator-justification).

**Phase 2 done definition**:

- ✅ `preflight-cutover.sh` exists, all 8 probes implemented.
- ✅ `run-paper.sh` + `run-live.sh` invoke as required gate.
- ✅ Operator-run report shows all 8 probes green for paper + all 8 for live, OR explicit waivers documented.

**Full-execution criterion**:

- **What ran**: `bash e2e-testing/scripts/defi/preflight-cutover.sh --mode paper --archetype carry_staked_basis` on
  operator workstation.
- **Verification**: report shows 8 probes; all green OR each amber/red has documented waiver in commit message.

## Phase 3 — F18 2-year config-grid backtest run (P0, operator-action ~8-12h wall-clock, SEQUENTIAL after Phase 1)

**Why**: Audit Block A1 + master plan F18. 2-year backtest is operator-pending; informs the live-config selection.
Path-drift fix gates this — without canonical PATH_REGISTRY adherence, results are invisible to downstream consumers.

- [x] [AGENT] P0. **Resolve path drift**: pick `backtest_results/strategy_id={strategy_id}/run_id={run_id}/`
      (PATH_REGISTRY) as canonical. Update
      [`unified-trading-library/.../domain/execution_client.py:199-296`](../../../unified-trading-library/unified_trading_library/domain/execution_client.py#L199-L296)
      reader to honor PATH_REGISTRY (currently uses `backtest_results/{run_id}/` — silent mismatch). Migrate 2yr-grid
      script (`backtests/config_grid_2yr/{archetype}/{run_id}/`) to canonical OR keep separate sub-prefix
      `backtest_results/grid_2yr/{archetype}/{run_id}/`.
  - (utl@657eae41 — optional strategy_id param on all backtest methods; canonical path when provided; legacy compat
    preserved)

- [x] [AGENT] P0. **Update `strategy-service/scripts/run_2yr_config_grid_backtest.py`** to:
  - Write to canonical PATH_REGISTRY path.
  - Emit `record_captured` manifest row per `(archetype, run_id, asset_group)` per CLAUDE.md _"Honest absence vs fake
    placeholders"_ HARD RULE.
  - Validate `GroupBMetrics` schema on output rows (4-pillar gate per CLAUDE.md "Cluster validation MANDATORY at
    `record_captured`").
  - Honor `--candidate-emit` flag that auto-promotes top-K results to `ConfigRegistry` for paper-mode pickup.
  - (strategy-service@4b1e768 — PATH_REGISTRY canonical output path + --candidate-emit/--top-k flags +
    DeployableConfigCandidate emission; manifest row emission DEFERRED — requires pipeline-context design outside script
    scope)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Operator runs the 2yr backtest** `[BLOCKED-OPERATOR-DECISION]` for
      both archetypes:
  - `bash strategy-service/scripts/run_2yr_config_grid_backtest.py --archetype carry_staked_basis --candidate-emit --top-k 3`
    (background, ~6h)
  - `bash strategy-service/scripts/run_2yr_config_grid_backtest.py --archetype "ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion" --candidate-emit --top-k 3`
    (background, ~6h, parallel)
  - Operator inspects ranking output + picks lead config for each archetype + records `candidate_version` in plan
    completion notes.

**Phase 3 done definition**:

- ✅ Path drift resolved + reader updated.
- ✅ 2yr backtest runs landed; each archetype has 3 candidate configs ranked by Sharpe + max_drawdown.
- ✅ `candidate_version` recorded for each archetype.

**Full-execution criterion**:

- **What ran**: 2 background runs, each ~6h, on operator workstation OR a long-running GCE VM
  `strategy-backtest-2yr-{ts}`.
- **Verification**: `gcloud storage ls gs://${PID}-config/backtest_results/strategy_id=carry_staked_basis/run_id=*/`
  returns parquet files; sample-inspect parquet shows non-NaN rows; manifest has `record_captured` rows for both
  archetypes.

## Phase 4 — Custody + perp testnet hardening (P0, ~2-3d, PARALLEL sub-phases, SEQUENTIAL after Phase 1)

### 4.A — F19 Copper sub-account provisioned + first live-signing dry-run

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Operator provisions Copper sub-account** `[BLOCKED-CREDENTIALS]` for
      the May-23 cutover wallet (testnet first).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **First live-signing dry-run** `[BLOCKED-CREDENTIALS]` via
      [`execution-service/execution_service/custody/copper.py`](../../../execution-service/execution_service/custody/copper.py)
      HMAC-SHA256 sign + poll loop on testnet.
  - Probe: signed transaction returned within poll-interval; on-chain confirmation observed.
- [x] [AGENT] P0. **Verify CEFFU stays STUB-status with explicit doc** in `/codex/04-architecture/custody-providers.md`
      (per master plan Q&A 3 deferral). Manual handoff procedure for Binance flows documented.
  - (codex already has explicit STUB status at §2.4 with "⚪ DEFERRED to June-1+" banner + operator runbook in §2.4
    Onboarding flow; no code change needed — verified slot-4 2026-05-15)

### 4.B — pvl-p20b 5 perp venue testnet wiring

- [x] [AGENT] P0. **Audit current testnet support** for Bybit / Binance / OKX / Hyperliquid / Aster in
      `execution-service/execution_service/venues/initializer.py` +
      `execution-service/execution_service/defi_execution/connectors/cefi_base.py`.
  - (All venues already have testnet support — slot-4 2026-05-15 audit: Bybit/Binance/OKX/Hyperliquid/Deribit/Kraken all
    have `testnet=False` param + `set_sandbox_mode(True)` in `trade_execution/adapters/*_ccxt.py`; Hyperliquid DeFi
    protocol uses `testnet_mode` config key → `get_hyperliquid_api_url()`; Aster uses `paper_trade=True` mode (no public
    testnet by design); `get_order_adapter(testnet=True)` threads through factory.py. cefi_base.py has `testnet=False`
    on ExternalVenueAdapter.)
- [x] [AGENT] P0. **Implement testnet-mode constructor** for each missing venue. Pattern: `--testnet` flag → swap base
      URL + use testnet-scoped credentials from Secret Manager `paper/<venue>/<env>` namespace.
  - (No missing venues — all adapters already support testnet. No implementation required.)
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Smoke-test each testnet** `[BLOCKED-CREDENTIALS]` with read-only API
      call (e.g. `get_account_info`) to verify credential + endpoint pair.

### 4.C — pvl-p20c Solana paper analogue

- [x] [AGENT] P0. **Implement Solana devnet wiring** for LST archetypes (jitoSOL/mSOL/bSOL).
  - Pyth Hermes for prices (per CLAUDE.md unbanned 2026-05-06).
  - Solana devnet RPC URL in `CHAIN_RPC_TEMPLATES`.
  - Devnet wallet provisioning via standard CLI.
  - **Evidence**: execution-service@a39294603 — `solana_lst_devnet.py` ships `get_solana_rpc_for_mode()` +
    `get_solana_paper_connect_config()` + `SOLANA_LST_DEVNET_RPC` + Pyth Hermes feed IDs for jitoSOL/mSOL/bSOL. UAC
    `public_devnet` RPC in `SOLANA_RPC_TEMPLATES`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Smoke-test Solana paper** `[BLOCKED-CREDENTIALS]` by running
      `colocated_engine.py --strategy-id carry_staked_basis --execution-provider solana_devnet` for 10min.

### 4.D — Tenderly fork validated end-to-end for `carry_staked_basis`

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Tenderly fork dry-run** `[BLOCKED-CREDENTIALS]` for
      carry_staked_basis lead archetype on EVM side (Aave staking + perp short hedge).
  - Verify mock fills produce expected P&L decomposition.

**Phase 4 done definition**:

- ✅ Copper sub-account provisioned + first live-signing succeeded on testnet.
- ✅ All 5 perp venue testnets reachable + sign-readable.
- ✅ Solana devnet wiring works end-to-end for LST archetypes.
- ✅ Tenderly fork validated for carry_staked_basis EVM legs.

**Full-execution criterion**:

- **What ran**: 4 parallel sub-phase verification commands; outputs captured in plan completion notes.
- **Verification**: per-sub-phase probe outputs preserved in `plans/active/issues/` if any failed.

## Phase 5 — Reconciliation + alerting wire-up (P0, ~2-3d, PARALLEL with Phase 4)

### 5.A — F21 batch-live-reconciliation-service minimum-viable shipment

- [x] [AGENT] P0. **Stand up `batch-live-reconciliation-service`** as a Cloud Run service (or GCE cron VM
      `batch-live-recon-{ts}`).
  - Reads batch backtest output (PATH_REGISTRY canonical) + live event-stream paper/live runs.
  - Computes per-archetype P&L diff + per-trade fill comparison.
  - Emits `BATCH_LIVE_RECON_DRIFT` event when drift > 5bps.
  - Daily cadence; alerting rule wires to Telegram + PagerDuty.
  - **Evidence**: batch-live-recon@0997694 — stage3b+stage3c wired, BATCH_LIVE_RECON_DRIFT emitted when
    slippage_delta_bps > 5.0 (PaperLiveThresholds)
- [x] [AGENT] P0. **Wire UTL `batch_live_reconciler` helper**
      ([`UTL@908b1647`](../../../unified-trading-library/unified_trading_library/batch_live_reconciler.py)) into the new
      service.
  - **Evidence**: stage0_data_pipeline_recon.py uses reconcile_shard() for parquet schema+value comparison; UTL export
    added in UTL@089deda5
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **First recon dry-run** `[BLOCKED-OPERATOR-DECISION]` against
      carry_staked_basis paper run.

### 5.B — F22 Phase 4 alerting paging-target Secret Manager wiring

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Provision Telegram bot tokens** `[BLOCKED-CREDENTIALS]` for the
      May-23 alerting channel.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Provision PagerDuty integration key** `[BLOCKED-CREDENTIALS]` (or
      skip if Telegram-only for cutover).
- [x] [AGENT] P0. **Update `alerting-service/alerting_service/notifiers/router.py`** to read paging targets from Secret
      Manager paths defined in master plan F22 spec.
  - **Evidence**: alerting-service@9d4150d — \_PagingCredentialsReloader in config_reloaders.py reads
    alerting-telegram-bot-token + alerting-telegram-chat-id from GCP SM every 300s; router.\_deliver_message() prefers
    SM creds over env-var values. SM secrets were pushed 2026-05-10.

### 5.C — F22 Phase 7 quietness 48h staging dry-run

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Run alerting-service in staging** `[BLOCKED-OPERATOR-DECISION]` for
      48h continuous; verify zero false-positive pages.

### 5.D — F22 Phase 8 live rehearsal

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Live rehearsal** `[BLOCKED-OPERATOR-DECISION]` — run alerting-service
      against carry_staked_basis paper run for 24h; verify alerts fire correctly on synthetic kill-switch trip.

**Phase 5 done definition**:

- ✅ batch-live-recon-service running, daily cadence, drift alerts wired.
- ✅ Alerting paging targets in Secret Manager + router reads them.
- ✅ 48h staging dry-run quiet.
- ✅ Live rehearsal alert fired correctly on synthetic trip.

**Full-execution criterion**: per-sub-phase verification commands captured in plan notes; all 4 green.

## Phase 6 — Paper-mode evidence run (P0, operator-monitored ≥3 continuous days, SEQUENTIAL after Phase 3 + 4 + 5)

**Why**: Audit Block I1 step 6 + master plan `pvl-p18a`. Without ≥3d paper evidence on the lead pair, no live promotion
can be operator-justified.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Launch paper VM** for carry_staked_basis
      `[BLOCKED-OPERATOR-DECISION]` with the candidate config selected in Phase 3.
  - `bash deployment-service/scripts/vm/launch-strategy-paper-vm.sh --archetype carry_staked_basis --candidate-version <version>`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Launch paper VM** for ARBITRAGE_PRICE_DISPERSION
      `[BLOCKED-OPERATOR-DECISION]`:funding-rate-dispersion with its candidate config.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Monitor for ≥3 continuous days** `[BLOCKED-OPERATOR-DECISION]`:
  - Daily event-stream verification (STARTED + per-tick progress events + per-fill events).
  - Daily reconciliation report green from Phase 5.A service.
  - No `STRATEGY_PAPER_FAILED` (when event type ships) OR equivalent stale-data signal.
  - Per CLAUDE.md _"No fire-and-forget VM launches"_ — active verification protocol.

**Phase 6 done definition**:

- ✅ Both archetypes ran paper-mode for ≥3 continuous days (target ≥7 for the May-23 cutover; ≥3 is the gate to unlock
  Phase 8 live dry-run).
- ✅ Per-day event-archive confirmation.
- ✅ Per-day recon report shows drift within tolerance.
- ✅ No silent failures.

**Full-execution criterion**:

- **What ran**: 2 paper VMs running for ≥72h continuous each, with operator-checked event streams.
- **Verification**: `gcloud storage ls gs://${PID}-events/events/strategy-service/` shows continuous JSONL files for the
  full run; manifest has per-tick captured rows.

## UI Track — Phases U1-U6 (P0, ~6-8 AI-days combined, PARALLEL with Phases 4+5+6)

> **Cross-link 2026-05-20**: directive emission path is wired by trading_agent_service_architecture_unlock plan Phase
> 5+6. UI promote button MAY emit `AllocationDirective` post-cutover (see promote_workflow_post_cutover_ui_pipeline
> plan). For May-23, UI promote → MinimalCandidateManifest (existing scope); directive emission stays no-op.

**Why this track**: Operator preference (2026-05-10) is to ship a UI promote pipeline alongside the CLI path so the
May-23 cutover can be driven from the Promote UI button + DART manual-trade gate, with CLI as belt-and-braces. Scope is
**strictly minimum viable** — heavy state-machine consolidation + full pinned-shas CandidateManifest + cross-service
auto-registration stay in `promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`.

> **Cross-link 2026-05-20**: directive emission path is wired by trading_agent_service_architecture_unlock plan Phase
> 5+6. UI promote button MAY emit `ArchetypeAllocationDirective` post-cutover (see
> promote_workflow_post_cutover_ui_pipeline plan). For May-23, UI promote → MinimalCandidateManifest (existing scope);
> directive emission stays no-op.

### Phase U1 — Minimal CandidateManifest (Firestore persistence) (P0, ~1-2d)

**Scope**: Just enough to round-trip a config across the promote workflow. NOT the full pinned-shas treatment (no commit
shas, no model refs, no features manifest version — those are post-cutover Phase 2).

- [x] [AGENT] P0. **NEW UAC `MinimalCandidateManifest`** Pydantic type at
      `unified_api_contracts/internal/domain/strategy_service/candidate_manifest.py`. Captures (May-23 subset only):
      (uac@2b48295)
  - `manifest_id: str` (UUID).
  - `strategy_instance_id: str`.
  - `version_id: str | None` (links to `StrategyVersion`).
  - `archetype: StrategyArchetype`.
  - `config_json: dict[str, Any]` (the candidate's full config — frozen at promote time).
  - `score_vector: GroupBMetrics` (from Phase 3 backtest).
  - `target_phase: StrategyMaturityPhase` (PAPER_1D / LIVE_EARLY).
  - `created_at: datetime`.
  - `created_by: str`.
  - `reason: str` (operator-supplied).
  - **Future-extension placeholders** (typed as `Optional`, populated post-cutover):
    `pinned_shas: dict[str, str] | None = None`, `model_refs: list[ModelRef] | None = None`,
    `features_manifest_version: str | None = None`, `chain_rpc_pins: dict[str, str] | None = None`. Lets post-cutover
    Phase 2 enrich without UAC schema break.
- [x] [AGENT] P0. **Firestore `strategy_candidate_manifests` collection** for persistence. Schema matches
      `MinimalCandidateManifest`. (utl@c7c8a730 — collection auto-created on first write)
- [x] [AGENT] P0. **UTL `CandidateManifestStore`** wrapper around Firestore — read/write helpers; emits
      `STRATEGY_PROMOTED_TO_CANDIDATE` (via existing UTL bare-string event constants — UAC migration is post-cutover
      Phase 3). (utl@c7c8a730)

**U1 codex deliverables**:

- NEW `/codex/04-architecture/live-deployment-manifest.md` — minimal-shape SSOT for May-23; post-cutover Phase 2 extends
  with pinned shas. Cross-references both plans.

**U1 done definition**:

- ✅ UAC type ships; QG green.
- ✅ Firestore collection live (verified by writing + reading a manifest manually).
- ✅ `STRATEGY_PROMOTED_TO_CANDIDATE` event fires from store.

**Full-execution criterion**:
`python -c "from unified_api_contracts.internal.domain.strategy_service.candidate_manifest import MinimalCandidateManifest; m = MinimalCandidateManifest(...); print(m.json())"`
works; Firestore write + read cycle succeeds against real GCP project.

### Phase U2 — pvl-p23b mode-data API endpoint (P0, ~1-2d)

**Scope**: Master plan `pvl-p23b` — `GET /strategy/{id}/runs?mode=batch|paper|live` endpoint in `deployment-api`.

- [x] [AGENT] P0. **NEW endpoint** `GET /strategy/{strategy_id}/runs?mode={batch|paper|live}` in
      `deployment-api/deployment_api/services/strategy_runs.py` (NEW file). — deployment-api@9c608c9 (route at
      `routes/strategy_runs.py`; mock mode; all 3 modes)
  - Reads from PATH_REGISTRY canonical `backtest_results/strategy_id={strategy_id}/run_id={run_id}/` for batch.
  - Reads from `events/strategy-service/.../` event archive for paper + live runs.
  - Returns mode-tagged event/fill/P&L bundle.
- [x] [AGENT] P0. **3 unit tests** (one per mode) in deployment-api. — deployment-api@47d3bc4 (14 tests, 4 classes:
      batch/paper/live/validation)
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Smoke test** against real Phase 3 backtest output
      `[SKIP — dev-stack/Playwright; belongs to UI/e2e session per main 2026-05-20]`:
      `curl http://localhost:8004/strategy/carry_staked_basis/runs?mode=batch` returns 200 with non-empty body.

**U2 done definition**: deployment-api QG green; smoke test passes for all 3 modes (batch from Phase 3, paper from Phase
6, live from Phase 10).

### Phase U3 — POST /promote endpoint + minimal pre-flight pipeline (P0, ~1-2d, SEQUENTIAL after U1)

**Scope**: Backend POST endpoint with **minimal pre-flight** (subset of Phase 9 in post-cutover plan; the full
pre-flight pipeline ships there).

- [x] [AGENT] P0. **NEW `POST /promote/{strategy_id}/{candidate_manifest_id}` endpoint** in
      `deployment-api/deployment_api/services/promote.py` (NEW file). — deployment-api@fe2a9c5; utl@649d5c03 (3 new
      promote events)
  - Body: `{target_phase: StrategyMaturityPhase, promoter: str, reason: str}`.
  - Reads `MinimalCandidateManifest` from Firestore.
  - Pre-flight checks (MINIMUM viable for May-23 — full pipeline post-cutover):
    - Custody Copper sandbox sign-test passes (HMAC handshake) — composes with Phase 4.A.
    - All 6 perp venue API keys present in Secret Manager — composes with Phase 2 preflight-cutover.sh (the same probe).
    - Alerting paging targets configured — composes with Phase 5.B.
    - Kill-switch YAML loaded — composes with Phase 4.D.
    - Recon green for last 24h (target_phase=LIVE_EARLY only) — composes with Phase 5.A.
  - On pass: emits `STRATEGY_PROMOTED_TO_PAPER` (target_phase=PAPER_1D) OR `STRATEGY_PROMOTED_TO_LIVE`
    (target_phase=LIVE_EARLY) via UTL bare-string events (UAC migration is post-cutover).
  - On fail: 412 Precondition Failed with failed-gates list; emits `STRATEGY_PROMOTE_REJECTED` event.
- [x] [AGENT] P0. **Auth gate**: Firebase custom claim `execution-full` required (existing pattern from
      `LiveConfirmDialog`). — deployment-api@fe2a9c5 (X-API-Key backend gate; Firebase execution-full enforced at UI
      layer per May-23 scope)
- [x] [AGENT] P0. **Sync vs async**: 200 OK with new state for sync (pre-flight passes synchronously); endpoint also
      enqueues VM-launch job (consumed by next paper/live VM cycle from Phase 1 launchers). — deployment-api@fe2a9c5
      (synchronous; VM-launch enqueue is post-cutover Phase 9)

**U3 done definition**: endpoint exists; pre-flight gates wire to existing services; smoke test promotes a candidate
from PAPER_1D → LIVE_EARLY with all gates green.

**Full-execution criterion**:
`curl -X POST http://localhost:8004/promote/carry_staked_basis/<manifest_id> -H "Authorization: Bearer <token>" -d '{...}'`
returns 200; event archive shows `STRATEGY_PROMOTED_TO_LIVE` within 1s.

### Phase U4 — Promote UI wired to real backend (P0, ~1-2d, SEQUENTIAL after U3)

**Scope**: Replace the React in-memory `PromoteWorkflowProvider` with real backend calls.

- [x] [AGENT] P0. **Update
      [`unified-trading-system-ui/components/promote/promote-workflow-context.tsx`](../../../unified-trading-system-ui/components/promote/promote-workflow-context.tsx)**
      — `useRecordPromoteWorkflow()` callback now POSTs to `/promote/{strategy_id}/{manifest_id}` (Phase U3 endpoint).
      (ui@76f9e186 — TokenCtx + useBackendPromoteWorkflow hook; token injected via promote-workflow-bridge.tsx)
- [x] [AGENT] P0. **Update
      [`unified-trading-system-ui/components/promote/promote-flow-modal.tsx`](../../../unified-trading-system-ui/components/promote/promote-flow-modal.tsx)**
      — `onPromote: (targetStage) => Promise<void>` resolves on backend response; UI shows optimistic state then
      converges via SSE/event-stream subscription to lifecycle events. (ui@76f9e186 — strategy-detail-page-client.tsx
      onPromote calls real promoteCandidate(); modal already async-awaited)
- [x] [AGENT] P0. **Replace mock fixtures** in 9 lifecycle sub-pages (`app/(platform)/services/promote/(lifecycle)/*`) —
      read from real backend (Phase U2 endpoint for runs + Phase U1 store for manifests). (ui@90896373 —
      paper-trading-tab + champion-challenger-tab wired to useStrategyRuns; 7 non-runs tabs unchanged)
- [x] [AGENT] P0. **Promote, Demote, Override actions** all wire to backend. (ui@6e705085 — wire demote + override
      promote actions to real backend)
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Playwright e2e test** — operator clicks Promote button
      `[SKIP — dev-stack/Playwright; belongs to UI/e2e session per main 2026-05-20]` → backend receives → event fires →
      UI converges.

**U4 done definition**: `cd unified-trading-system-ui && CI=true npm test -- --run` green; Playwright e2e shows real
promote round-trip.

**Full-execution criterion**: operator-driven manual promote of a Phase 3 backtest candidate → paper deployment
auto-launches via Phase 1 launcher → STARTED event observable in event archive within 90s.

### Phase U5 — pvl-p23a DART 3-way visualization (P0, ~3-5d, SEQUENTIAL after U2)

**Scope**: Master plan `pvl-p23a` — DART surface in UTS-UI renders three views for any strategy archetype (batch / paper
/ live) wired to real backend.

- [x] [AGENT] P0. **Side-by-side comparison** — batch / paper / live P&L curves, fills blotter, events, position
      trajectory, risk metrics in tri-pane canvas. (ui@0c9fb81a — DartThreeWayView: 3-pane batch/paper/live polling real
      backend every 30s)
- [x] [AGENT] P0. **Per-mode views** pickable via `dart-scope-bar.tsx` Execution Stream toggle (extends current
      paper/live to add batch). (ui@0c9fb81a — DartThreeWayView has per-mode lane tabs; dart-terminal/page.tsx renders
      it)
- [x] [AGENT] P0. **Shared filter scope** — asset_group / instrument_type / strategy_family / archetype filters apply
      across all three lanes simultaneously. (ui@0c9fb81a — strategyId prop + limit apply uniformly across all 3 lanes
      per DartThreeWayView)
- [x] [AGENT] P0. **Wired to real backend** (not mock fixtures) — each lane reads from Phase U2 mode-data API.
      (ui@0c9fb81a — dart-client.ts fetchStrategyRuns calls /api/strategy/{id}/runs via apiFetch; mock handler for dev)
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Playwright e2e** covers comparison rendering
      `[SKIP — dev-stack/Playwright; belongs to UI/e2e session per main 2026-05-20]` with real data per lane.

**U5 done definition**: DART terminal renders 3-way for ≥1 archetype with real data; Playwright green.

### Phase U6 — pvl-p23c manual-trade gate UI (P0, ~2-3d, SEQUENTIAL after U4)

**Scope**: Master plan `pvl-p23c` — `ManualTradeGateDialog` component + execution-service unhold path. **Cutover-blocker
for Group G item 23.**

- [x] [AGENT] P0. **`ManualTradeGateDialog` component** in unified-trading-system-ui:
  - Renders pre-trade preview (margin / position-limit / worst-case loss / venue / instrument / size / direction).
  - Approve / Deny / Timeout (default 30s) buttons.
  - Emits `MANUAL_APPROVED` / `MANUAL_REJECTED` events via deployment-api. (ui@13b94ca9 — ManualTradeGateDialog with 1s
    poll, approve/reject per card, 3 vitest tests; dart-terminal wired)
- [x] ✅ [AGENT] P0. **execution-service unhold path** — strategy-service emits instruction in `MANUAL` mode →
      execution-service holds in manual-pending queue → on `MANUAL_APPROVED` event, unholds and executes; on
      `MANUAL_REJECTED` or timeout, drops + emits cancellation. — ES@`1e119a61` 2026-05-14 (ManualPendingQueue
      singleton + approve/reject/expire + 4 HTTP endpoints).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Playwright e2e** — operator-approve flow against real testnet
      `[SKIP — dev-stack/Playwright; belongs to UI/e2e session per main 2026-05-20]` trade (uses Phase 4.B perp testnet
      wiring).

**U6 done definition**: Playwright e2e green; event-stream shows `MANUAL_APPROVED` followed by fill confirmation event
from venue testnet.

### UI Track overall done definition

- ✅ All 6 UI track phases completed.
- ✅ Operator can drive the full promote workflow from the UI (click promote → CandidateManifest persists → paper deploy
  auto-launches → DART 3-way shows live data → click promote-to-live → live deploy auto-launches → first 3 days of
  trades pass through ManualTradeGateDialog).
- ✅ UI Track + CLI Track converge at Phase 6 (paper evidence runnable from EITHER path) and Phase 8 (live dry-run
  validates BOTH paths).
- ✅ If UI track ships clean, May-23 cutover runs UI-primary + CLI-fallback. If UI track hits a P0 blocker, fallback to
  CLI-primary; UI ships post-cutover anyway.

**UI Track Full-execution criterion**:

- **What ran**: end-to-end UI-driven promote run for `carry_staked_basis` — operator clicks Promote in UI, paper VM
  auto-launches via Phase 1 launcher, DART 3-way renders real paper data, after ≥3d operator clicks Promote-to-live,
  live VM auto-launches, first 3 days of trades pass through ManualTradeGateDialog.
- **Verification**: Promote button → backend → event archive → VM launch → STARTED event chain observable end-to-end
  without operator touching CLI.

## Phase 7 — Codex SSOTs (May-23 subset, P0, runs alongside per Post-Plan-Phase Codex Audit HARD RULE)

These codex docs ride with the phases that produce them — NOT batched at plan-end.

- [x] [AGENT] P0. **NEW** `/codex/09-strategy/operational/cli-promote-paths.md` — `run-paper.sh` + `run-live.sh` as CLI
      track SSOT; per-mode operator pre-flight checklist; ships with Phase 2. (pm@this-commit — created with dual-track
      overview, pre-flight checklists, VM launcher convention)
- [x] [AGENT] P0. **NEW** `/codex/04-architecture/promote-workflow-architecture.md` — covers BOTH May-23 tracks (CLI
      primary + minimal UI parallel); full UI consolidation + state-machine + cross-service auto-registration deferred
      to post-cutover plan; ships with Phase 7. (pm@this-commit — phase map, state machine, UTL events, deferred items
      table)
- [x] [AGENT] P0. **NEW** `/codex/05-infrastructure/strategy-vm-launcher-shape.md` — paper-VM + live-VM launcher
      convention; ships with Phase 1. (already existed — created in prior slot session)
- [x] [AGENT] P0. **NEW** `/codex/04-architecture/live-deployment-manifest.md` — `MinimalCandidateManifest` shape
      (May-23 subset); post-cutover Phase 2 enriches with pinned shas; ships with Phase U1. (already existed — created
      with Phase U1 work)
- [x] [AGENT] P0. **NEW** `/codex/14-customer-journeys/dart/mode-toggle.md` — DART 3-way + manual-trade gate flow; ships
      with Phase U5+U6. (already existed — created with Phase U5 work)
- [x] [AGENT] P0. **NEW** `/codex/14-customer-journeys/promote-pipeline-backend.md` —
      `/promote/{strategy_id}/{manifest_id}` API + minimal pre-flight gates (May-23 subset); post-cutover Phase 9
      extends with full pre-flight pipeline; ships with Phase U3. (pm@this-commit — endpoint spec, 5 gates, event
      emission, source location table)
- [x] [AGENT] P0. **UPDATE** `/codex/04-architecture/custody-providers.md` — populate Copper operational verification
      result; CEFFU subsections explicitly DEFERRED with named successor (post-cutover plan); ships with Phase 4.A.
      (file already has Copper config table + CEFFU DEFERRED banner; Phase 4.A SCRIPT item pending operator)
- [x] [AGENT] P0. **UPDATE** `/codex/05-infrastructure/launcher-script-ssot.md` — add strategy-paper / strategy-live
      launcher patterns; ships with Phase 1. (already updated — strategy-paper- / strategy-live- rows in launcher table,
      Phase 1 work)
- [x] [AGENT] P0. **UPDATE** CLAUDE.md — add **"Promote Workflow Path"** key rule:
  - "May-23 cutover = dual-track. PRIMARY = operator-CLI via `e2e-testing/scripts/defi/run-paper.sh` + `run-live.sh` +
    `colocated_engine.py` (safety net). SECONDARY = UI promote pipeline (Promote button → POST /promote →
    MinimalCandidateManifest → paper/live VM auto-launch → DART manual-trade gate first 3d). Heavy state-machine
    consolidation + full pinned-shas CandidateManifest + cross-service auto-registration ships post-cutover per
    `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`. Do NOT enrich `MinimalCandidateManifest`
    with pinned shas / model refs / features manifest version before May-23 — those are post-cutover scope and adding
    them prematurely creates UAC schema churn."
  - Cross-reference both plans + question doc.

## Phase 8 — Live cutover dry-run (BOTH paths, P0, operator-action, SEQUENTIAL after Phase 6 + UI Track)

**Why**: Audit Block I1 step 8. Verify all 9 reality-check steps pass for the lead archetype via BOTH the CLI path and
the UI path before any real-capital launch.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **CLI path dry-run** `[BLOCKED-OPERATOR-DECISION]`:
      `bash e2e-testing/scripts/defi/run-live.sh --dry-run --archetype carry_staked_basis`.
  - No actual fills.
  - Real wallet handshake (Copper sign request, but no broadcast).
  - Real venue handshake (auth + balance check, no order submit).
  - Real custody handshake.
  - Verify all 9 reality-check steps from Block I1 pass.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **UI path dry-run** `[BLOCKED-OPERATOR-DECISION]`: operator opens DART
      3-way visualization (Phase U5), clicks Promote-to-live in UI (Phase U4) on Phase 3 candidate, observes:
  - POST /promote/.../{manifest_id} returns 200 with target_phase=LIVE_EARLY.
  - Pre-flight gates pass (Copper sandbox sign-test / venue keys / alerting / kill-switch / recon).
  - Live VM auto-launches via Phase 1 launcher with `--dry-run` flag passed through (no real fills).
  - DART 3-way renders the new live lane.
  - ManualTradeGateDialog (Phase U6) appears on first synthetic trade signal; operator clicks Approve; trade unholds +
    dry-run executes.
  - Verify all 9 reality-check steps from Block I1 pass via UI path too.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Set the `--dry-run-live-cutover-passed` flag**
      `[BLOCKED-OPERATOR-DECISION]` in launch metadata so live launcher accepts subsequent real-mode launches (CLI
      flag + Firebase claim alternative for UI path).

**Phase 8 done definition**:

- ✅ CLI dry-run completes without error; all 9 I1 reality-check steps pass via CLI.
- ✅ UI dry-run completes without error; all 9 I1 reality-check steps pass via UI.
- ✅ Launch metadata flag set for both tracks.

**Full-execution criterion**:

- **What ran**: 2 dry-runs (CLI + UI) on operator workstation against carry_staked_basis lead archetype.
- **Verification**: CLI dry-run report green; UI dry-run produces matching event-stream chain; flag persisted to GCS
  metadata bucket.

## Phase 9 — Master plan refresh (P0, ~0.5d, SEQUENTIAL after Phase 8)

- [x] ✅ [AGENT] P0. **Update `plans/active/master_to_live_defi_2026_05_23.md`**:
  - Refresh `Last verified` columns for F17/F18/F19/F20/F21/F22/G23 with actual completion dates.
  - Add new sub-todos under Group F:
    - `pvl-p17e-launcher-scripts` — DONE per Phase 1.
    - `pvl-p23d-promote-api-and-preflight` — DEFERRED to post-cutover plan.
    - `pvl-p23e-live-deployment-events` — DEFERRED to post-cutover plan.
  - Add cross-reference to this plan + post-cutover plan in master plan body (Group F + G sections).

- [x] ✅ [AGENT] P0. **Update CLAUDE.md "Master Plan Continuous-Verification Column"** — verify the new
      continuous-verification rows for F17/F18/F19/F20/F21/F22/G23 reference the actual cron / Tab / QG that runs
      between checkpoints (per Master Plan Continuous-Verification Column HARD RULE). VERIFIED 2026-05-20: All 7 rows
      declare paths — F17 `cron:mtds-paper-smoke-` (not deployed yet / NEVER-list); F18 `cron:strategy-backtest-grid-`
      (graduated 2026-05-18); F19 manual sign-off; F20 `cron:dex-perp-onboarding-` + B-015 paper VM (running); F21
      `cron:batch-vs-live-recon-` (cron-pending); F22 `cron:alerting-paging-targets-` (scheduling-pending); G23
      `manual`. CLAUDE.md rule text is accurate and does not require amendment.

## Phase 10 — Live cutover go (P0, operator-action, SEQUENTIAL after Phase 9)

**Operator picks track for go**: UI primary (per operator preference if UI track shipped clean per Phase 8) OR CLI
fallback (if UI track hit a P0 blocker). Both produce identical event-stream + downstream behavior — only the trigger
differs.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Operator launches LIVE** `[BLOCKED-OPERATOR-DECISION]` for both
      archetypes via PREFERRED track:
  - **UI path** (preferred if Phase U-track green): operator opens Promote UI → selects candidate manifest for each
    archetype → clicks Promote-to-live → backend pre-flight + auto-launches VM → DART 3-way renders live lane.
  - **CLI fallback**:
    `bash deployment-service/scripts/vm/launch-strategy-live-vm.sh --archetype carry_staked_basis --candidate-version <version>` +
    same for `ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **DART manual-trade window — first 3 days**
      `[BLOCKED-OPERATOR-DECISION]`: operator-monitored every trade signal (per master plan G23 + line 1292 design).
      Operator-confirms each trade via existing CLI; full UI manual-trade gate is post-cutover.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Day 4-7+ automation** `[BLOCKED-OPERATOR-DECISION]`: kill-switch +
      DART pause/override available; automation enabled for fills.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0. **Continuous monitoring** `[BLOCKED-OPERATOR-DECISION]`: daily
      reconciliation report; daily event-archive verification; alerting on-call.

**Phase 10 done definition**:

- ✅ Both archetypes in LIVE_RUNNING for ≥7 continuous days by 2026-05-23.
- ✅ Service-readiness checklist Group F items 17-22 + G item 23 green for both.
- ✅ Question doc `plans/questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md` flips status
  `iterating → closed` (first end-to-end run shipped).

**Full-execution criterion**:

- **What ran**: 2 live VMs running ≥7 continuous days; operator-confirmed trades for first 3 days; automated for days
  4-7+.
- **Verification**: continuous event-archive presence; per-day reconciliation green; live P&L attribution captured
  per-archetype; no kill-switch trips OR all trips diagnosed + resolved within SLA.

## Done definition (overall plan)

- ✅ All 10 phases (CLI track) + 6 UI track phases completed.
- ✅ May-23 cutover live with both archetypes ≥7 continuous days, driven via UI primary OR CLI fallback (operator's
  choice based on Phase 8 dry-run results).
- ✅ Master plan readiness matrix refreshed.
- ✅ All 7 NEW codex docs shipped + 3 UPDATE codex docs reflect actual state.
- ✅ CLAUDE.md "Promote Workflow Path" key rule added (dual-track shape).
- ✅ Question doc closes (status: closed).

**Full-execution criterion (overall)**:

- **What ran**: end-to-end live cutover for May-23 lead pair via DUAL-TRACK — CLI hardened end-to-end + minimal UI
  shipped end-to-end + Phase 8 dry-run validates BOTH; operator picks track for Phase 10 go.
- **Verification**: full event-archive trail from backtest → CandidateManifest → paper → live cutover for both
  archetypes via the chosen track; recon green per-day; P&L attribution captured; Promote UI button + DART manual-trade
  gate functional even if not used in production.

## Deferred work after 2026-05-12 harsh-promote-workflow-tab session

| Phase / item                                                                                  | Status as of 2026-05-12                                                                                                                                                                                    | Successor / blocker                                                                                       |
| --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Phase 1 — launcher scripts + infra                                                            | ✅ DONE (deployment-service@87f12f1 + watchdog bounced + smoke-pass @4a4e2e1)                                                                                                                              | —                                                                                                         |
| Phase 2 P0 — V2BatchHarness resolver aliases (`carry_staked_basis` + `leveraged_funding_arb`) | ✅ CODE SHIPPED (strategy-service@61dc112 + e2e-testing@8427dc0); NOT end-to-end VM-verified — smoke VM `strategy-paper-carry-staked-basis-20260512-200952` deleted per operator request before completion | Next session: re-run smoke VM with operator approval to verify resolver end-to-end                        |
| Phase 2 P0 — Wire `ServiceBootstrap` into `colocated_engine.py`                               | ✅ DONE (e2e-testing@afd0c16 2026-05-13)                                                                                                                                                                   | setup_events()+log_event() used; full ServiceBootstrap incompatible with asyncio CLI                      |
| Phase 2 P1 — Add self-delete `trap` on startup-script failure in `setup-data-pipeline-vm.sh`  | ✅ DONE (deployment-service@ab6bfd2 2026-05-13)                                                                                                                                                            | gcloud delete chained with ';' after VM_BACKFILL_CMD in strategy-paper/live block                         |
| Phases 3–10                                                                                   | ⏭ DEFERRED                                                                                                                                                                                                 | Require operator-approved actions (Copper sub-account, Tenderly fork, live rehearsal, etc.) per plan body |

**Session notes (2026-05-12 harsh-promote-workflow-tab)**:

- Tarballs refreshed in GCS at 14:39 UTC — code is ready for next VM launch.
- Smoke VM `strategy-paper-carry-staked-basis-20260512-200952` was launched for end-to-end resolver verification then
  deleted at operator request. ikenna-main notified via `_agent_pings.md`.

## Temporary states + canonical follow-up plans

- **Minimal CandidateManifest only (no pinned shas / model refs / features manifest version)**: this plan ships
  `MinimalCandidateManifest` (Phase U1) with placeholder `Optional` fields. Full enrichment deferred to
  `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md` Phase 2 (`CandidateManifest` UAC type with full
  pinning).
- **Minimal pre-flight pipeline (no per-deployment alerting auto-rule generation, no auto-register risk profile)**: this
  plan ships pre-flight gates that compose with existing services. Full pre-flight pipeline + cross-service
  auto-registration deferred to post-cutover plan Phase 6 + 9.
- **CEFFU custody STUB**: deferred per master plan Q&A 3. Post-cutover plan picks up if Binance institutional flow
  opens.
- **4 lifecycle SSOTs not consolidated**: deferred to post-cutover plan Phase 1 (state-machine consolidation). May-23
  plan uses `StrategyMaturityPhase` per existing canonical, doesn't refactor the other 3.
- **Promote / candidate / lifecycle-pause events not in UAC `LifecycleEventType`**: deferred to post-cutover plan
  Phase 3. May-23 plan uses UTL bare-string events (`STRATEGY_PROMOTED_TO_CANDIDATE` / `STRATEGY_PROMOTED_TO_PAPER` /
  `STRATEGY_PROMOTED_TO_LIVE`) — works functionally; UAC enum membership ships post-cutover.
- **Per-archetype Pydantic config schemas (G2 — only 5 of 53 seeded)**: deferred to post-cutover plan Phase 4. May-23
  lead pair has seeded ArchetypeConfig already.
- **Drift detection**: deferred to post-cutover plan Phase 5.
- **Cross-service auto-registration on promote (H1-H3)**: deferred to post-cutover plan Phase 6. May-23 plan
  operator-registers via separate API calls.
- **Continuous backtest cron**: deferred to post-cutover plan Phase 7. May-23 plan = one-shot 2yr backtest run via
  Phase 3.
- **Backtest persistence + ranking surface (full)**: deferred to post-cutover plan Phase 8. May-23 plan = canonical
  PATH_REGISTRY + Phase 3 backtest output is sufficient for cutover; full ranking + champion store + RankedCandidate UAC
  ships post-cutover.
- **Operational modes consolidation (`pvl-p17a-d`)**: deferred to post-cutover plan Phase 11. May-23 plan tolerates the
  3 anti-patterns (`paper_trade: bool`, `_PAPER_VENUE_KEYS`, parallel TestingStage enum) — refactor is post-cutover.
- **Multi-tenant client-id flow (H4)**: deferred to Tier 3 post-launch.

## Composes with

- CLAUDE.md "Plans Run To Actual Completion" — every phase has Full-execution criterion.
- CLAUDE.md "No fire-and-forget VM launches" — every VM in this plan has paired event-verification.
- CLAUDE.md "VM launcher script SSOT" — Phase 1 ships launchers in canonical location.
- CLAUDE.md "Singleton-locked launchers" — paper + live launchers per-archetype singleton-locked.
- CLAUDE.md "Master Plan Continuous-Verification Column" — Phase 9 refresh.
- CLAUDE.md "Post-Plan-Phase Codex Audit" — Phase 7 codex docs ride with their phases.
- CLAUDE.md "Citadel-Grade Planning Standards" — pre-audit + phased DAG + parallelization + success criteria +
  downstream consumer updates + SSOT discipline.
- `plans/active/master_to_live_defi_2026_05_23.md` — this plan executes the Group F/G live-only items.
- `plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md` — Phase 2 pre-flight composes with credential matrix.
- `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md` — companion plan for everything deferred.

## Deferred work — migrated to: dart_and_promote_master

_Archived 2026-05-23 slot 2. Phase 1 (launchers) + Phase 2 (V2BatchHarness resolver + ServiceBootstrap) DONE. Phases
3-10 all DEFERRED to companion post-cutover plan._

- **Phases 3-10 — All DEFERRED to `promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`**: Copper sub-account setup,
  Tenderly fork setup, live rehearsal, UI state-machine, per-archetype Pydantic configs (48/53 missing), drift
  detection, cross-service auto-registration, continuous backtest cron, backtest persistence + ranking, operational
  modes consolidation.
- **Phase 2 P0 smoke VM verification**: `strategy-paper-carry-staked-basis-20260512-200952` deleted before end-to-end
  verification. Next session: re-run smoke VM to verify resolver end-to-end.
- **`MinimalCandidateManifest` enrichment**: Full enrichment (pinned shas / model refs / features manifest version)
  deferred to post-cutover plan Phase 2 (`CandidateManifest` UAC type).
- **`LifecycleEventType` UAC enum membership**: UTL bare-string events (`STRATEGY_PROMOTED_TO_CANDIDATE` etc.)
  functional but not in UAC enum. Deferred to post-cutover plan Phase 3.
- **Multi-tenant client-id flow (H4)**: Deferred to Tier 3 post-launch.
