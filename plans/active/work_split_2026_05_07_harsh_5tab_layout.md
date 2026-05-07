---
title: Harsh 5-tab agent layout — coherent context bundles for parallel Opus 4.7 sessions (2026-05-07)
type: coordination-doc
status: active
created: 2026-05-07
deadline: 2026-05-23 (live DeFi)
horizon: scope-bounded (each tab runs to its done-definition, ignore the parent's D1-D5 calendar)
companion_to: plans/active/work_split_2026_05_07.md
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

# Harsh 5-tab agent layout — coherent context bundles for parallel Opus 4.7 sessions

> **Companion to**: [`work_split_2026_05_07.md`](work_split_2026_05_07.md) (Ikenna ↔ Harsh per-day split),
> [`work_split_2026_05_07_ikenna_5tab_layout.md`](work_split_2026_05_07_ikenna_5tab_layout.md) (Ikenna's mirror layout),
> and [`_AUDIT_2026_05_07_dependency_graph.md`](_AUDIT_2026_05_07_dependency_graph.md) (per-plan status + critical path).
> This doc takes the 11 Harsh-owned items and groups them into **5 coherent context bundles**, one per Claude Code tab.
> Each tab runs Opus 4.7 as the master agent with full window on its bundle, and fans out to sub-agents (Task tool /
> general-purpose / Explore) for mechanical multi-file work the master can spec cleanly. The 5-day calendar in the
> parent doc is descriptive, not prescriptive — agents finish faster, so each tab runs to its done-definition, not a
> calendar date.

## Coverage guarantee

D1 (2026-05-07) items are both DONE — cefi VM babysit is offloaded to a parallel monitoring agent (37 VMs running),
and UAC backfill types shipped early via Ikenna `UAC@a70b3f6`. Plan checkboxes flipped in `PM@fb7aefa`. The remaining
11 items spanning D2-D5 are assigned to exactly one tab:

| Parent day | Item                                                            | Tab     |
| ---------- | --------------------------------------------------------------- | ------- |
| D2         | UAC `feature_group → required_inputs` SSOT (verify + flip only) | Tab 2   |
| D2         | Hook `features_sports_reconcile_available_at.py` into VM exit   | Tab 5   |
| D3         | `POST /api/backfill/launch` + `GET /api/vm/events` handlers     | Tab 1   |
| D3         | UAC canonical_question_group SSOT (Polymarket+Kalshi)           | Tab 2   |
| D4         | Cross-asset manifest rescan (post-cefi-drain)                   | Tab 3   |
| D4         | TradFi MDPS post-drain ES.OPT 11-cluster validation rerun       | Tab 3   |
| D4         | Migrate 10 of 30 ad-hoc VM launchers into deployment-service    | Tab 4   |
| D5         | aws_migration Phase 0/1 smoke                                   | Tab 4   |
| D5         | DART 6-persona Playwright matrix verification                   | Tab 5   |
| D5         | ml/features Phase 3 Parquet column-pruning quick-win            | Tab 5   |
| D5         | `deploy_missing_auto_launch` Phase 1 successor                  | Tab 1   |

11 items / 11 assigned / 0 dropped.

## Layered parallelism model

- **Layer 1 (5 tabs, this doc)**: split by **coherent context cluster** so each master agent's window stays warm on
  related files / plans / judgment threads. File collisions across tabs are mitigated below per-tab + against Ikenna's
  parallel 5-tab layout.
- **Layer 2 (sub-agents within each tab)**: master fans out via Task tool when work is multi-file mechanical (per-repo
  edit, per-launcher migration, per-asset_group reconcile pass) and the master can spec it cleanly. Sub-agents inherit
  [`cursor-configs/SUB_AGENT_MANDATORY_RULES.md`](../../cursor-configs/SUB_AGENT_MANDATORY_RULES.md) — paste at top of
  every Task prompt or use [`scripts/agents/inject-mandatory-rules.sh`](../../scripts/agents/inject-mandatory-rules.sh).
- **Sub-agent batching rule**: if N independent sub-agents fan out, send them in a SINGLE message with N Task blocks so
  they run concurrently. Sequential sub-agent calls are wasted parallelism.

## Universal boot protocol (every tab reads first)

Before touching any file in your scope:

1. [`/home/hk/unified-trading-system-repos/.claude/CLAUDE.md`](../../../.claude/CLAUDE.md) — workspace rules (commit +
   push per shippable unit, plan-checkbox flip in same logical unit, mandatory pre-commit `git status` +
   `git diff --cached --stat` no-path-arg discipline, dirty-deps direct-push not quickmerge, **Findings Triage
   Discipline (HARD RULE)** — case-1-to-5 decision tree for any issue surfaced mid-task).
2. [`work_split_2026_05_07.md`](work_split_2026_05_07.md) § "Collision-risk callouts" — read every callout that names a
   file your tab touches.
3. [`work_split_2026_05_07_ikenna_5tab_layout.md`](work_split_2026_05_07_ikenna_5tab_layout.md) — Ikenna's tab
   ownership boundaries; cross-tab collision avoidance section below.
4. Your tab section in this doc — items, repos, read-first list, done definition.
5. Each plan you'll edit — frontmatter + top-of-file banners (cross-plan coordination signal).
6. Cross-tab handshake: at boot, run
   `git fetch origin live-defi-rollout && git log --oneline -20 origin/live-defi-rollout` to see what other tabs (mine
   AND Ikenna's) shipped since your last context. Pull before the first edit.

---

## TAB 1 — Backfill control plane (deployment-api work-stream-A + auto-launch)

**Identity**: You own the programmatic VM-launch + event-tail surface end-to-end. This is the **highest-leverage tab**
for the May-23 deadline because it unblocks Ikenna's Agent 4 D4 work (Ikenna can launch DeFi backfill VMs through your
endpoint instead of bash-shelling). UAC Phase 1 types already shipped (`UAC@a70b3f6`); you wire the routes.

**Scope (2 items — Phase 2 routes + Phase 1 successor)**:

- [ ] [SCRIPT] P0. deployment-api Phase 2 — `POST /api/backfill/launch` + `GET /api/vm/events` handlers against the
      already-shipped UAC types (`BackfillLaunchRequest` / `BackfillLaunchResult` / `VMLifecycleEvent` /
      `VMEventListResult` / `BackfillLaunchTaskKind`). Plan:
      [`deployment_api_work_stream_a_2026_05_07`](deployment_api_work_stream_a_2026_05_07.plan.md) Phase 2.A + 2.B.
      Repos: deployment-api. Net-new files: `deployment_api/routes/backfill_launch.py` +
      `deployment_api/routes/vm_events.py`.
- [ ] [SCRIPT] P1. `deploy_missing_auto_launch` Phase 1 — preview → auto-launch successor (only after Phase 2 routes
      land). Plan: [`deploy_missing_auto_launch_2026_05_07`](deploy_missing_auto_launch_2026_05_07.plan.md). Repo:
      deployment-api. Wires the existing data-status `Deploy-Missing` button through the new `/api/backfill/launch`
      endpoint with operator-confirm preview.

**Repos owned (collision boundary)**: deployment-api **new endpoint files only** (`routes/backfill_launch.py`,
`routes/vm_events.py`, related tests under `tests/integration/`). Hands off the `error_reason` rendering pipeline
in deployment-api to Ikenna Agent 2 (writegate Phase 4.A — different files entirely).

**Read-first**:

- [`plans/active/deployment_api_work_stream_a_2026_05_07.plan.md`](deployment_api_work_stream_a_2026_05_07.plan.md)
  Phase 2 — full spec (subprocess wrapping, `_TASK_TO_LAUNCHER` mapping, `_PREFIX_TO_SERVICE` resolver, dry-run /
  mock-mode guard, integration tests with `monkeypatch.setattr("subprocess.run", _fake_run)`)
- [`plans/active/deploy_missing_auto_launch_2026_05_07.plan.md`](deploy_missing_auto_launch_2026_05_07.plan.md) — full
  plan
- [`unified-api-contracts/unified_api_contracts/internal/deployment.py`](../../../unified-api-contracts/unified_api_contracts/internal/deployment.py)
  lines 189-397 — UAC types you call against (`UAC@a70b3f6`)
- [`deployment-service/scripts/vm/vm_zombie_watchdog.py`](../../../deployment-service/scripts/vm/vm_zombie_watchdog.py)
  `VM_PREFIX_TO_BUCKET` — read-only validation surface for `vm_name_prefix` checks
- Existing route patterns: `deployment-api/deployment_api/routes/data_status.py` /
  `deployment_api/routes/deploy_events_sse.py` for shape consistency
- CLAUDE.md sections: "No fire-and-forget VM launches", "VM Naming Convention", "Singleton-locked launchers",
  "Manifest concurrency principle"
- [`codex/03-observability/lifecycle-events.md`](../../codex/03-observability/lifecycle-events.md) — event schema you
  parse against in `/api/vm/events`

**Sub-agent fan-out**:

- Phase 2.A + 2.B in parallel (per the plan's `PARALLEL within phase` marker) — two Task blocks in one message:
  (a) `backfill_launch.py` route + integration tests, (b) `vm_events.py` route + integration tests with mocked GCS
  client. Master integrates + wires `main.py` `_authenticated_router.include_router(...)` calls in a separate commit.
- One Explore sub-agent to verify the launcher set in `_TASK_TO_LAUNCHER` matches actual `deployment-service/scripts/vm/launch-*.sh`
  filenames — closed-set validation.
- `deploy_missing_auto_launch` Phase 1: one Task block once Phase 2 routes are merged — wiring + UI preview integration.

**Collision risk**:

- **Ikenna Agent 2 (writegate Phase 4.A)** — Agent 2 touches deployment-api `error_reason` rendering pipeline
  (response-shape extension to existing routes). You touch new route files. Pre-commit `git diff --cached --name-only`
  before every commit; verify only `routes/backfill_launch.py` / `routes/vm_events.py` / `main.py` (your include_router
  lines) / `tests/integration/test_backfill_launch.py` / `tests/integration/test_vm_events.py` are staged.
- **`main.py` includes** — both you and Agent 2 may add `include_router(...)` lines. Surgical `git add -p` on `main.py`;
  push immediately after each commit so Agent 2 pulls fresh.

**Done definition**:

1. Phase 2.A + 2.B routes shipped + 13 integration tests pass (7 for backfill_launch + 6 for vm_events per plan spec).
2. `from unified_api_contracts.internal import BackfillLaunchRequest, BackfillLaunchResult, VMLifecycleEvent, VMEventListResult, BackfillLaunchTaskKind`
   resolves in deployment-api source.
3. Mock-mode + dry-run path NEVER calls subprocess (verified via test).
4. `deploy_missing_auto_launch` Phase 1 successor wired against Phase 2 routes.
5. Plan checkboxes flipped in
   [`deployment_api_work_stream_a_2026_05_07.plan.md`](deployment_api_work_stream_a_2026_05_07.plan.md) +
   [`deploy_missing_auto_launch_2026_05_07.plan.md`](deploy_missing_auto_launch_2026_05_07.plan.md) per shippable unit.

---

## TAB 2 — UAC schema SSOTs (pure-spec mechanical work)

**Identity**: You ship UAC schema additions from clear plan specs. Two items, both Pydantic + StrEnum work, both
gating downstream consumers.

**Scope (2 items)**:

- [ ] [SCRIPT] P0. **Verify + flip** UAC `feature_group → required_inputs` SSOT (Phase 1A). The work was already shipped
      in this session — `unified_api_contracts/canonical/domain/features/required_inputs.py` (428 LOC, `InputReq`
      dataclass + `FEATURE_REQUIRED_INPUTS` dict for 32 feature_groups) +
      `unified_api_contracts/canonical/domain/features/registry.py` (249 LOC, `EXPECTED_FEATURE_GROUPS_BY_SERVICE` +
      `FEATURE_COVERAGE_START`) + tests at `tests/test_feature_dag_ssot.py`. Run `bash scripts/quality-gates.sh
      tests/test_feature_dag_ssot.py` to verify green; flip the matching checkboxes in
      [`ml_and_features_master_2026_05_07`](ml_and_features_master_2026_05_07.plan.md) Phase 1A. Repo: UAC + PM.
- [ ] [SCRIPT] P1. UAC `canonical_question_group` SSOT (Polymarket HOURLY/DAILY + Kalshi groupings + ELECTION).
      Plan: [`predictions_master_2026_05_07`](predictions_master_2026_05_07.plan.md) Phase 1. Repo: UAC. New module:
      `unified_api_contracts/canonical/domain/predictions/canonical_question_group.py` (or facade equivalent — check
      current predictions layout first). The `BTC_UP_DOWN_HOURLY` / `BTC_UP_DOWN_DAILY` / `SPX_UP_DOWN_DAILY` /
      `ELECTION_PRESIDENT_2028` taxonomy + per-group market_id classification rules + cluster-validation expected
      counts (HOURLY=24, DAILY=1, ELECTION=1).

**Repos owned (collision boundary)**: UAC `canonical/domain/features/` (already shipped) + UAC
`canonical/domain/predictions/` (greenfield for canonical_question_group). Hands off UAC `alerting.py` (Ikenna Agent 1)
and UAC `internal/deployment.py` (Ikenna `a70b3f6`, already shipped).

**Read-first**:

- [`plans/active/ml_and_features_master_2026_05_07.plan.md`](ml_and_features_master_2026_05_07.plan.md) Phase 1A
- [`plans/active/predictions_master_2026_05_07.plan.md`](predictions_master_2026_05_07.plan.md) Phase 1
- Existing UAC `canonical_question_group` references — search via Explore sub-agent (CLAUDE.md mentions the registry
  is "currently no SSOT exists" — greenfield scope)
- Existing UAC StrEnum patterns (e.g. `BackfillLaunchTaskKind`, `LifecycleEventType`, `EMPTY_CONFIRMED_REASONS`) for
  shape consistency
- CLAUDE.md sections: "Prediction market lifecycle timing", "Shard-granularity SSOT" (per-asset-group shard-key matrix
  for prediction = `(asset_group=prediction, venue, data_type, canonical_question_group, day)`), "Cluster validation
  MANDATORY" (prediction is a bundled data_type)
- [`unified-api-contracts/unified_api_contracts/canonical/domain/features/`](../../../unified-api-contracts/unified_api_contracts/canonical/domain/features/)
  for the layout precedent

**Sub-agent fan-out**:

- One Task to scan workspace for existing market_id → canonical_question_group references (consumer audit) — informs
  the closed-set design.
- One Task to verify `feature_dag` SSOT tests are green via `cd unified-api-contracts && bash scripts/quality-gates.sh
  tests/test_feature_dag_ssot.py` (parallel with the consumer scan above).
- For canonical_question_group: one general-purpose sub-agent to extract the existing market_id naming patterns from
  Polymarket + Kalshi instrument adapters in MTDS / instruments-service — informs the regex / slug-prefix mapping.

**Collision risk**:

- **Ikenna Agent 1 (UAC alerting)** — Agent 1 touches UAC `alerting.py` (or new alerting facade). You touch
  `canonical/domain/features/` + `canonical/domain/predictions/`. Different sub-modules. Risk only on `__init__.py`
  re-exports (`unified_api_contracts/__init__.py` if that's where new symbols re-export). Push immediately after each
  commit so other tabs `git pull --rebase` cleanly.
- **Ikenna `a70b3f6`** — already shipped, no live collision.

**Done definition**:

1. Phase 1A `feature_dag` tests verified green via `quality-gates.sh tests/test_feature_dag_ssot.py`; checkboxes
   flipped in `ml_and_features_master_2026_05_07.plan.md` with `UAC@<sha>` evidence stamps.
2. `canonical_question_group` SSOT shipped: closed-set StrEnum, market_id classification helper(s), expected per-group
   cluster counts, round-trip JSON tests, consumer-import smoke test (`from unified_api_contracts.predictions import
   canonical_question_group_for_market_id` works).
3. Plan checkboxes flipped in `predictions_master_2026_05_07.plan.md` Phase 1 per shippable unit.

---

## TAB 3 — Manifest correctness (post-cefi-drain) — IDLE until prerequisite met

**Identity**: You own manifest-hygiene work that's **gated on cefi VM drain** (the 37-VM bitfinex/bitget/kraken
backfill currently in-flight). You start IDLE — boot only when cefi VMs drain (operator signals + watchdog confirms
zero `cefi-*` instances RUNNING in `asia-northeast1-c`). Once unblocked, two coordinated rescan + validation passes.

**Scope (2 items, hard prerequisite)**:

- [ ] [SCRIPT] P0. Cross-asset manifest rescan — run
      [`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`](../../../instruments-service/scripts/reconcile_phantom_manifest_rows_all.py)
      `--asset-group {cefi|defi|tradfi|prediction|sports} --dry-run` per asset_group; review residuals; run `--apply`
      where dry-run residuals look real. Merge per-VM shards into canonical via the consolidator daemon (already
      running). Plan:
      [`manifest_migration_master_2026_05_07`](manifest_migration_master_2026_05_07.plan.md) Stage 4. Repo:
      instruments-service scripts. **Hard prerequisite**: cefi VMs drained.
- [ ] [SCRIPT] P1. TradFi MDPS post-drain ES.OPT 11-cluster validation rerun — if cluster-coverage gate flagged any
      partial bundles during the pre-drain run, re-fetch + re-validate. Plan:
      [`tradfi_master_2026_05_07`](tradfi_master_2026_05_07.plan.md). Repo: MDPS. Use the writegate Phase 1A
      cluster-coverage helper (`UAC.BUNDLED_DATA_TYPES` + `ManifestWriter.record_captured(expected_root_clusters=...)`)
      to gate the new captures.

**Repos owned (collision boundary)**: instruments-service `scripts/` (specifically `reconcile_phantom_manifest_rows_all.py`
operations only — read-only on Ikenna Agent 3's `enumerate_expected_universe.py`), MDPS post-drain re-fetch paths.
Hands off MDPS `base_adapter.py` / `BaseCandleAdapter` to Ikenna Agent 2 (writegate Phase 2.A residual — same plan,
different files).

**Read-first**:

- [`plans/active/manifest_migration_master_2026_05_07.plan.md`](manifest_migration_master_2026_05_07.plan.md) Stage 4
- [`plans/active/tradfi_master_2026_05_07.plan.md`](tradfi_master_2026_05_07.plan.md) ES.OPT 11-cluster section
- [`plans/active/cefi_master_2026_05_07.plan.md`](cefi_master_2026_05_07.plan.md) § "Tardis-venues backfill IN-FLIGHT"
  (`PM@9b1f1d5`) — context for what's draining + 3 findings (bundle shape / missing rows_captured / CPU saturation)
- [`plans/active/issues/cefi_tardis_writegate_findings_2026_05_07.md`](issues/cefi_tardis_writegate_findings_2026_05_07.md)
  — finding #1 directly impacts the rescan: the bundle-shaped captured rows (empty `instrument_id`) may need a
  shape-aware reconcile pass after Ikenna Agent 2's Phase 2.A lands. Coordinate timing.
- [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
  § "Phantom audit — re-runnable recipe"
- CLAUDE.md sections: "Manifest phantom audit", "Manifest concurrency principle", "Per-VM shard isolation for
  concurrent backfills", "Cluster validation MANDATORY at record_captured for bundled shards"

**Sub-agent fan-out**:

- 5 parallel sub-agents in one message — one per asset_group running
  `reconcile_phantom_manifest_rows_all.py --asset-group {cefi|defi|tradfi|prediction|sports} --dry-run` on a same-region
  GCE VM (cross-region listing is 18× slower per CLAUDE.md). Each reports residuals + suggested action. Master reviews
  + decides per-asset_group whether to `--apply`.
- ES.OPT cluster-validation: one Task to read pre-drain `tradfi_master` results + identify partial-bundle dates;
  one Task to re-fetch those dates with the cluster-coverage gate active. Sequential within tab, parallel with the
  manifest rescan above.

**Collision risk**:

- **Ikenna Agent 3 (expected-universe enumerator)** — Agent 3 also touches `instruments-service/scripts/` (the
  enumerator) and runs VMs in the same zone. Different scripts (reconcile vs enumerate), different VM prefixes
  (`*-rescan-` vs `expected-universe-enum-*`). Sequence: Agent 3 runs enumerator FIRST (operator-review CSV +
  `--apply-write`), THEN you run the reconciler (which trusts the now-honest expected universe). Coordinate via PM
  banner-add when each VM run starts.
- **Ikenna Agent 2 (writegate Phase 2.A residual)** — Agent 2's `_create_empty_output()` deletion + path-B/C migration
  changes the shape of newly-written captured rows. You run the reconciler AFTER Agent 2's Phase 2.A ships; otherwise
  the reconciler will see two row shapes (pre-fix bundle + post-fix per-instrument) and may flag false phantoms.

**Done definition**:

1. Cefi VMs drained (verified: zero `cefi-*` instances in `asia-northeast1-c`).
2. Cross-asset rescan complete: 5 dry-run reports + per-asset_group `--apply` decisions documented + applied.
3. Per-VM shards merged into canonical by consolidator (verify
   `gs://market-data-tick-cefi-{pid}/_index/per_vm/` is empty after merge).
4. ES.OPT 11-cluster validation: any partial bundles re-captured + cluster-coverage gate green.
5. Plan checkboxes flipped in `manifest_migration_master_2026_05_07.plan.md` Stage 4 +
   `tradfi_master_2026_05_07.plan.md` per shippable unit.

---

## TAB 4 — Cloud-agnostic infra (AWS migration smoke + launcher consolidation)

**Identity**: You own the **DeFi-first AWS migration smoke** + the launcher SSOT cleanup. Both are infra-hardening,
both touch `deployment-service/scripts/vm/`, both are about cloud-agnostic discipline. The aws_migration plan is
shared with Ikenna Agent 4 (Phase 2 dual-bucket) — your scope is Phase 0/1 ONLY (early in the plan body, surgical
`git add -p`).

**Scope (2 items)**:

- [ ] [SCRIPT] P2. Migrate first batch of 10 ad-hoc VM launchers from `e2e-testing/scripts/` /
      `features-*-service/scripts/` / intra-repo into the canonical
      `deployment-service/scripts/vm/launch-{asset_group}-{flavor}-vm.sh` location. Plan:
      [`launcher_scripts_consolidation_into_deployment_service_2026_05_07`](launcher_scripts_consolidation_into_deployment_service_2026_05_07.plan.md).
      Repo: deployment-service. Per-launcher checklist: file move, `VM_PREFIX_TO_BUCKET` registry update in
      `vm_zombie_watchdog.py`, `_SERVICE_LAUNCHER_SCRIPTS` registry update in
      `deployment-api/deployment_api/services/deploy_missing.py`, watchdog VM relaunch, downstream consumer-script
      reference updates. Target: 10 of 30 in this cycle; rest carry over post-May-23.
- [ ] [SCRIPT] P0. aws_migration Phase 0/1 smoke — `CLOUD_PROVIDER=aws instruments-service --health-check` +
      `setup-defi-buckets.sh --dry-run`. Plan:
      [`aws_migration_defi_first_2026_05_07`](aws_migration_defi_first_2026_05_07.plan.md) Phase 0-1 (early-in-plan
      section ONLY — Ikenna Agent 4 owns Phase 2). Repos: deployment-service + instruments-service.

**Repos owned (collision boundary)**: deployment-service `scripts/vm/` (launcher migrations + watchdog dict) +
instruments-service health-check + UCI bucket-naming smoke. Hands off `setup-defi-buckets.sh` Phase 2 (real bucket
creation + Storage Transfer config) to Ikenna Agent 4. Hands off `launch-defi-*` launchers to Ikenna Agent 4.

**Read-first**:

- [`plans/active/launcher_scripts_consolidation_into_deployment_service_2026_05_07.plan.md`](launcher_scripts_consolidation_into_deployment_service_2026_05_07.plan.md)
  — full plan + per-launcher migration checklist
- [`plans/active/aws_migration_defi_first_2026_05_07.plan.md`](aws_migration_defi_first_2026_05_07.plan.md) Phase 0-1
  ONLY (skip Phase 2 — Ikenna's scope)
- [`codex/05-infrastructure/launcher-script-ssot.md`](../../codex/05-infrastructure/launcher-script-ssot.md) — workspace
  rule that all launchers live under `deployment-service/scripts/vm/`
- [`codex/05-infrastructure/vm-tarball-deployment.md`](../../codex/05-infrastructure/vm-tarball-deployment.md) — tarball
  deploy modes affected by launcher moves
- [`codex/05-infrastructure/cloud-agnostic-script-pattern.md`](../../codex/05-infrastructure/cloud-agnostic-script-pattern.md)
  — Ikenna Agent 4 will populate this for Phase 2; you may use it for Phase 0/1 verification
- CLAUDE.md sections: "VM launcher script SSOT (codified 2026-05-07)", "VM Naming Convention", "VM tarball deployment",
  "Singleton-locked launchers"

**Sub-agent fan-out**:

- Launcher migration: 10 parallel Tasks in one message (one per launcher) — each Task does the full per-launcher
  checklist (move file, update both registries, update consumer references). Master reviews + commits in 10 separate
  commits + push (per-launcher shippable unit). After all 10 land, ONE watchdog VM relaunch.
- AWS Phase 0/1: two parallel sub-agents — (a) instruments-service `--health-check` against `CLOUD_PROVIDER=aws`
  emulator (moto / @mock_aws) + report; (b) `setup-defi-buckets.sh --dry-run` walk-through + verify bucket-naming
  matches the SSOT Ikenna Agent 4 will populate. Master integrates outputs + commits.

**Collision risk**:

- **Ikenna Agent 4 (DeFi launch + AWS Phase 2)** — same `aws_migration_defi_first_2026_05_07.plan.md` body. Parent
  doc D4 collision callout: "Harsh edits only Phase 0/1 section (early in plan) with surgical `git add -p`; Ikenna
  edits only Phase 2; sync at EOD D4." Strict surgical staging. Pre-commit `git diff --cached` before every commit;
  verify only Phase 0/1 hunks staged.
- **Ikenna Agent 3 (enumerator)** — Agent 3 owns `launch-expected-universe-enumerator-vm.sh` + watchdog dict updates.
  You own non-DeFi-non-enumerator ad-hoc launchers. Different files. Coordinate watchdog relaunch timing — only ONE
  watchdog relaunch per cycle (Agent 3 does theirs after dict update, you do yours after the 10-launcher batch).
  Whoever ships first owns the relaunch; the second tab's dict update lands without re-relaunch.
- **Ikenna Agent 4** — also touches `deployment-service/scripts/vm/`. Different launcher files (DeFi vs your migrated
  ad-hoc set). Pre-commit name-only check.

**Done definition**:

1. 10 launchers migrated + 10 commits + 10 plan-flips + watchdog VM relaunched + verified by
   `gcloud compute instances list --filter="name~vm-zombie-watchdog"`.
2. AWS Phase 0/1 smoke green: instruments-service health-check passes under `CLOUD_PROVIDER=aws` mock; `setup-defi-buckets.sh
   --dry-run` exits 0 with bucket-naming matching SSOT.
3. Plan checkboxes flipped in `launcher_scripts_consolidation_into_deployment_service_2026_05_07.plan.md` (10 of 30) +
   `aws_migration_defi_first_2026_05_07.plan.md` Phase 0/1 section per shippable unit.

---

## TAB 5 — UI testing + features plumbing + ml quick-win

**Identity**: You own the UI/test surface + non-critical-path feature plumbing. **Lightest tab by priority** but
heaviest by repo diversity (4 repos). All 3 items are independent — order doesn't matter. Run them in parallel as
sub-agents if you have the context budget.

**Scope (3 items)**:

- [ ] [SCRIPT] P1. Hook
      [`features-sports-service/scripts/features_sports_reconcile_available_at.py`](../../../features-sports-service/scripts/features_sports_reconcile_available_at.py)
      (already shipped per `features-sports-service@f123069`) into per-source backfill VM exit-step. Plan:
      [`sports_master_2026_05_07`](sports_master_2026_05_07.plan.md). Repos: features-sports-service +
      deployment-service. Per-source launcher (`launch-af-backfill.sh`, `launch-fs-backfill.sh`, etc.) gains a final
      step that runs the reconciler before VM auto-shutdown.
- [ ] [TEST] P0. DART 6-persona Playwright matrix verification on manual-trade flow. Plan:
      [`strategy_and_dart_master_2026_05_07`](strategy_and_dart_master_2026_05_07.plan.md) Phase 2.2. Repo:
      unified-trading-system-ui. 6 personas × manual-trade golden path; record any new regressions as case-3 findings
      per [Findings Triage Discipline](../../cursor-configs/CLAUDE.md) (annotate the right plan, don't fix unfamiliar
      UI files yourself).
- [ ] [SCRIPT] P1. ml/features Phase 3 — Parquet column-pruning quick-win (1-3 day pure-win, self-contained). Plan:
      [`ml_and_features_master_2026_05_07`](ml_and_features_master_2026_05_07.plan.md) Phase 3. Repo:
      ml-training-service. Document benchmark before/after in plan body.

**Repos owned (collision boundary)**: features-sports-service `scripts/` + deployment-service per-source sports
launchers (`launch-af-backfill.sh` etc.) + unified-trading-system-ui `tests/playwright/` + ml-training-service training
loop / parquet read paths. Hands off DART backend (`unified-trading-services` strategy-service) to Ikenna Agent 4 if
Playwright surfaces a backend regression.

**Read-first**:

- [`plans/active/sports_master_2026_05_07.plan.md`](sports_master_2026_05_07.plan.md) (sports reconciler hookup
  todo)
- [`plans/active/strategy_and_dart_master_2026_05_07.plan.md`](strategy_and_dart_master_2026_05_07.plan.md) Phase
  2.2 — DART matrix spec
- [`plans/active/ml_and_features_master_2026_05_07.plan.md`](ml_and_features_master_2026_05_07.plan.md) Phase 3
  — column-pruning spec
- [`features-sports-service/scripts/features_sports_reconcile_available_at.py`](../../../features-sports-service/scripts/features_sports_reconcile_available_at.py)
  — already-shipped reconciler (your job is to wire its entry-point into the launcher exit-step)
- Existing per-source sports launchers: `launch-af-backfill.sh` / `launch-fs-backfill.sh` /
  `launch-sfi-backfill.sh` / `launch-understat-backfill.sh` / `launch-transfermarkt-backfill.sh` /
  `launch-openmeteo-backfill.sh`
- CLAUDE.md sections: "available_at is per-row, write-time, equal to live-pipeline-arrival", "Sports source coverage
  windows", "Two teammates × multiple parallel agents — don't edit unfamiliar files" (mandatory for the UI test work
  — DART code is shared with Ikenna's strategy-service work)

**Sub-agent fan-out**:

- All 3 items are independent — fan out as 3 Tasks in ONE message at boot:
  - Task A: Sports reconciler hookup — wire `features_sports_reconcile_available_at.py` into the 6 per-source
    launcher exit-steps.
  - Task B: DART Playwright matrix — run the 6-persona spec headless, collect regression report.
  - Task C: Parquet column-pruning — implement + benchmark (read-row-count baseline → pruned baseline → diff).
- Master reviews each output + commits per shippable unit.

**Collision risk**:

- **Ikenna Agent 4 (paper-trade smoke)** — Agent 4 touches execution-service + strategy-service +
  position-balance-monitor-service. Your DART Playwright runs against the same backend stack but does not edit it
  (read-only / black-box test). If Playwright surfaces a regression, file it as a case-3 issue annotation in
  `strategy_and_dart_master_2026_05_07.plan.md` (or escalate to case-5 if it breaks paper-trade smoke); do NOT fix
  Ikenna's backend code yourself.
- **Ikenna Agent 5 (PM governance)** — Agent 5 may flip checkboxes in `ml_and_features_master_2026_05_07.plan.md` /
  `strategy_and_dart_master_2026_05_07.plan.md` for the master refresh. Flip your own checkboxes per shippable unit;
  Agent 5 audits flip hygiene, doesn't pre-emptively flip yours.
- **deployment-service per-source launchers** — Tab 4 owns ad-hoc launcher migration; you own per-source sports
  launcher exit-step additions. Different files (you edit existing `launch-{source}-backfill.sh` content; Tab 4
  moves NEW launchers in). Pre-commit name-only check.

**Done definition**:

1. All 6 per-source sports launchers have a final reconcile step + reconciler entry-point invoked correctly + verified
   by a smoke launch (1 source, dry-run).
2. DART 6-persona Playwright matrix executes green; any regressions annotated in
   `strategy_and_dart_master_2026_05_07.plan.md` per case-3 / case-5 of Findings Triage Discipline.
3. Parquet column-pruning shipped + benchmark documented (e.g. `read time 8.2s → 3.1s, 62% reduction`); plan body
   updated with numbers.
4. Plan checkboxes flipped in `sports_master_2026_05_07.plan.md` + `strategy_and_dart_master_2026_05_07.plan.md` Phase
   2.2 + `ml_and_features_master_2026_05_07.plan.md` Phase 3 per shippable unit.

---

## Cross-tab handshakes (within Harsh's 5 tabs + against Ikenna's 5 tabs)

These are the ONLY hard sync gates. Operate independently otherwise.

### Within Harsh's tabs

- [ ] **Tab 1 routes shipped → Tab 1 deploy_missing_auto_launch successor**: Phase 1 of `deploy_missing_auto_launch`
      depends on Phase 2 routes. Tab 1 enforces internally — sequential within the tab.
- [ ] **Cefi VMs drained → Tab 3 boot**: Tab 3 idle until verified zero `cefi-*` instances RUNNING. Operator or Tab 4
      (during launcher migration) signals when drain complete. Tab 3 self-checks via
      `gcloud compute instances list --filter="name~'^cefi-'" --format='value(name)' | wc -l`.
- [ ] **Tab 4 watchdog relaunch ↔ Tab 4 + Ikenna Agent 3 watchdog relaunch**: ONE relaunch per cycle. Whoever ships
      first owns the relaunch + posts to chat; the other waits for confirmation before completing their dict update.

### Against Ikenna's 5 tabs

- [ ] **Ikenna Agent 1 (UAC alerting) → Tab 2 (UAC SSOTs)**: when Ikenna Agent 1 pushes UAC `AlertCode` StrEnum, Tab 2
      `git pull` in UAC checkout before next UAC edit. Risk surface: `__init__.py` re-exports.
- [ ] **Ikenna Agent 2 (writegate Phase 2.A residual) → Tab 3 (manifest rescan)**: Tab 3 runs reconciler AFTER Phase
      2.A ships, OR uses dual-shape recognition (per-VM bundles AND per-instrument rows). Whichever Ikenna Agent 2
      lands first sets the timing.
- [ ] **Ikenna Agent 2 (writegate Phase 4.A) ↔ Tab 1 (deployment-api routes)**: separation enforced via pre-commit
      `git diff --cached --name-only`. Agent 2 owns `error_reason` rendering response-shape on existing routes; Tab 1
      owns `routes/backfill_launch.py` + `routes/vm_events.py`. Both add `include_router(...)` lines to `main.py`;
      surgical `git add -p` on `main.py`; push immediately so the other tab pulls fresh.
- [ ] **Ikenna Agent 3 (enumerator VMs) → Tab 3 (manifest rescan)**: Agent 3 enumerator runs FIRST (operator-review
      CSV + `--apply-write`); THEN Tab 3 reconciler runs against the now-honest expected universe. Sequence enforced
      by Tab 3 boot-check.
- [ ] **Ikenna Agent 3 (deployment-service watchdog dict) ↔ Tab 4 (launcher migration watchdog dict)**: see "Within
      Harsh's tabs" above — one relaunch per cycle.
- [ ] **Ikenna Agent 4 (aws_migration Phase 2) ↔ Tab 4 (aws_migration Phase 0/1)**: same plan body. Surgical `git add
      -p` per parent doc D4 collision callout; sync at EOD D4 with cross-section consistency check (Phase 0 + 1 + 2
      read as one continuous plan).
- [ ] **Ikenna Agent 4 (DeFi launchers) ↔ Tab 4 (ad-hoc launcher migration)**: different launcher files. Pre-commit
      name-only check.
- [ ] **Ikenna Agent 4 (paper-trade smoke regression) ↔ Tab 5 (DART Playwright)**: if Tab 5 Playwright surfaces a
      regression that affects paper-trade smoke, escalate as case-5 finding (operator notify + issues doc) per
      Findings Triage Discipline. Don't fix Ikenna's backend code.
- [ ] **Ikenna Agent 5 (PM governance master refresh) ← all Harsh tabs**: Tab 1-5 ping Agent 5 via PM commit when their
      done-definition is met so Agent 5 captures shipped work in the master refresh.

## Discipline reminders (every tab, every commit)

Same as Ikenna's mirror layout — repeated here for tab-boot completeness:

- **Pre-commit (mandatory)**: `git status` then `git diff --cached --stat` (NO path argument). If anything you don't
  recognise is staged, surgically `git restore --staged <file>` or `git stash --keep-index` it. See CLAUDE.md
  "mandatory pre-commit check" — incidents PM@961980db / PM@611b9501 / PM@7de75819 are documented foot-guns.
- **Per shippable unit**: commit + push immediately. Local-only commits are invisible to other tabs + CI + VMs pulling
  from `live-defi-rollout`. No "I'll commit at the end."
- **Plan flip in same logical unit as code**: ship code → flip checkbox → commit plan flip → push. Don't batch.
- **Findings Triage Discipline (HARD RULE)**: any side-discovery during execution → classify case-1-to-5 per
  CLAUDE.md § "Findings Triage Discipline"; **big findings (case 5) trigger immediate operator notify in chat AND
  issue doc in [`plans/active/issues/`](issues/)** — do both, not one or the other.
- **Sub-agent rules injection**: paste
  [`cursor-configs/SUB_AGENT_MANDATORY_RULES.md`](../../cursor-configs/SUB_AGENT_MANDATORY_RULES.md) at top of every
  Task prompt. Sub-agents in `--print` mode CANNOT read files from disk.
- **Dirty deps → direct push not quickmerge**: parent CLAUDE.md rule. Default flow:
  `git add <files> && git commit && git push origin live-defi-rollout`.
- **Cross-plan coordination banners**: when launching VMs or starting in-flight refactors, banner every other active
  plan whose work is influenced. Banner-add is part of the launch logical unit. Banner-remove on completion (Ikenna
  Agent 5 sweeps strays).

## Done definition (whole layout)

When all 5 Harsh tabs hit their per-tab done-definition, the 11-item Harsh split is complete. Ikenna Agent 5 then
captures Harsh's shipped work in the master refresh, and the parent
[`work_split_2026_05_07.md`](work_split_2026_05_07.md) checkboxes are flipped in bulk reflecting reality.
