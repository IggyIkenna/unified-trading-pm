---
doc_type: plan
title: Ikenna 5-tab agent layout — coherent context bundles for parallel Opus 4.7 sessions (2026-05-07)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, deployment-ui, execution-service, features-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-07
type: coordination-doc
deadline: 2026-05-23 (live DeFi)
horizon: scope-bounded (each tab runs to its done-definition, ignore the parent's D1-D5 calendar)
companion_to: plans/active/work_split_2026_05_07.md
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

# Ikenna 5-tab agent layout — coherent context bundles for parallel Opus 4.7 sessions

> **Companion to**: [`work_split_2026_05_07.md`](work_split_2026_05_07.md) (Ikenna ↔ Harsh per-day split) and
> [`_AUDIT_2026_05_07_dependency_graph.md`](_AUDIT_2026_05_07_dependency_graph.md) (per-plan status + critical path).
> This doc takes the 13 Ikenna-owned items and groups them into **5 coherent context bundles**, one per Claude Code tab.
> Each tab runs Opus 4.7 as the master agent with full window on its bundle, and fans out to sub-agents (Task tool /
> general-purpose / Explore) for mechanical multi-file work the master can spec cleanly. The 5-day calendar in the
> parent doc is descriptive, not prescriptive — agents finish faster, so each tab runs to its done-definition, not a
> calendar date.

## Coverage guarantee

All 13 Ikenna items from [`work_split_2026_05_07.md`](work_split_2026_05_07.md) are assigned to exactly one tab:

| Parent day | Item                                                   | Tab     |
| ---------- | ------------------------------------------------------ | ------- |
| D1         | UAC `AlertCode` taxonomy                               | Agent 1 |
| D1         | writegate Phase 4.A typed-error rendering              | Agent 2 |
| D2         | Expected-universe enumerator Phase 3.D.4               | Agent 3 |
| D2         | writegate Phase 2.A residual (MDPS + UTL)              | Agent 2 |
| D2         | Audit 2 new umbrellas + master Group F+G fold-in       | Agent 5 |
| D3         | alerting Phase 2 (KillSwitchBus + rules + thresholds)  | Agent 1 |
| D3         | writegate Phase 5 (workspace QG ratchet)               | Agent 2 |
| D4         | DeFi backfill VMs launch                               | Agent 4 |
| D4         | aws_migration Phase 2 (dual-bucket)                    | Agent 4 |
| D4         | Triage `defi_archetypes_canonicalisation`              | Agent 4 |
| D4         | Triage `session_2026_05_07_data_status_audit_findings` | Agent 5 |
| D5         | carry_staked_basis paper-trade smoke                   | Agent 4 |
| D5         | Master plan refresh                                    | Agent 5 |

13 items / 13 assigned / 0 dropped.

## Layered parallelism model

- **Layer 1 (5 tabs, this doc)**: split by **coherent context cluster** so each master agent's window stays warm on
  related files / plans / judgment threads. File collisions across tabs are mitigated below per-tab.
- **Layer 2 (sub-agents within each tab)**: master fans out via Task tool when work is multi-file mechanical (per-repo
  edit, per-plan banner add, per-chain VM monitoring) and the master can spec it cleanly. Sub-agents inherit
  [`cursor-configs/SUB_AGENT_MANDATORY_RULES.md`](../../cursor-configs/SUB_AGENT_MANDATORY_RULES.md) — paste at top of
  every Task prompt or use [`scripts/agents/inject-mandatory-rules.sh`](../../scripts/agents/inject-mandatory-rules.sh).
- **Sub-agent batching rule**: if N independent sub-agents fan out, send them in a SINGLE message with N Task blocks so
  they run concurrently. Sequential sub-agent calls are wasted parallelism.

## Universal boot protocol (every agent reads first)

Before touching any file in your scope:

1. [`/Users/ikennaigboaka/Code/unified-trading-system-repos/.claude/CLAUDE.md`](../../../.claude/CLAUDE.md) — workspace
   rules (commit + push per shippable unit, plan-checkbox flip in same logical unit, mandatory pre-commit `git status` +
   `git diff --cached --stat` no-path-arg discipline, dirty-deps direct-push not quickmerge).
2. [`work_split_2026_05_07.md`](work_split_2026_05_07.md) § "Collision-risk callouts" — read every callout that names a
   file your tab touches.
3. Your tab section below — items, repos, read-first list, done definition.
4. Each plan you'll edit — frontmatter + top-of-file banners (cross-plan coordination signal).
5. Cross-tab handshake: at boot, run
   `git fetch origin live-defi-rollout && git log --oneline -20 origin/live-defi-rollout` to see what other tabs shipped
   since your last context. Pull before the first edit.

---

## AGENT 1 — Alerting

**Identity**: You own the alerting workspace surface end-to-end. Ikenna items D1 (alerting taxonomy) + D3 (rules +
thresholds).

**Scope (2 items)**:

- [x] [DESIGN] P0. UAC `AlertCode` StrEnum + threshold dataclass + severity-vs-alert-code separation. Plan:
      [`alerting_service_live_rules_2026_05_07`](alerting_service_live_rules_2026_05_07.plan.md) Phase 1. Repo: UAC
      (`unified_api_contracts/canonical/crosscutting/alerting.py` or facade equivalent — check current layout first).
      **DONE 2026-05-07** — UAC@`d00326d` shipped + alerting plan Phase 1 checkbox flips per PM@`7624ab21`.
- [ ] [ARCHITECTURE] P0. alerting Phase 2 — `KillSwitchBus` rule wiring + `CROSS_CLOUD_EGRESS_DETECTED` rule + AAVE
      utilization-spike threshold value (audit §3 #5 flagged the bps as ambiguous; resolve via either DeFi-team judgment
      call or threshold-research sub-agent). Plan: alerting Phase 2. Repo: alerting-service. **PENDING** —
      `grep     AlertCode alerting-service/` returns 0 hits as of 2026-05-07 evening; Phase 2 consumer wiring is the
      gate.

**Repos owned (collision boundary)**: UAC `alerting.py` (and/or new alerting facade) + alerting-service. Hands off
deployment-api / UTL / MDPS to other agents.

**Read-first**:

- [`plans/active/alerting_service_live_rules_2026_05_07.plan.md`](alerting_service_live_rules_2026_05_07.plan.md)
- [`/codex/14-playbooks/alerting/alert-code-taxonomy.md`](/codex/14-playbooks/alerting/alert-code-taxonomy.md) (codex
  SSOT expects the StrEnum to land at the spec'd location)
- Audit §3 #5 in [`_AUDIT_2026_05_07_dependency_graph.md`](_AUDIT_2026_05_07_dependency_graph.md) (AAVE bps ambiguity)
- Existing UAC StrEnum patterns (e.g. `LifecycleEventType`, `PreflightSkipReason`) for shape consistency

**Sub-agent fan-out**:

- Phase 1 (taxonomy): one general-purpose agent to scan workspace for existing `Alert` / `Severity` / `AlertCode`
  references that the new StrEnum must subsume; you author the closed-set in the master tab once you have the scan.
- Phase 2 (rules): three parallel sub-agents in one message — (a) `KillSwitchBus` rule wiring, (b)
  `CROSS_CLOUD_EGRESS_DETECTED` rule scaffold + tests, (c) AAVE utilization-spike threshold research (read DeFi carry
  plans + Aave docs, propose value with citation). Master integrates outputs.

**Collision risk**: only tab touching UAC `alerting.py` and alerting-service source. Risk is `pyproject.toml` /
`__init__.py` re-exports if Harsh's parallel UAC work (control-plane / feature_dag / predictions) re-exports through the
same `__init__.py`. Push immediately after each commit so other tabs `git pull --rebase` cleanly.

**Done definition**:

1. ✅ UAC `AlertCode` StrEnum + threshold dataclass merged + tests green via repo `bash scripts/quality-gates.sh`.
   **Shipped 2026-05-07 at UAC@d00326d** — 39-code closed set, `AlertSeverity` (CRITICAL/HIGH/WARN/INFO),
   `AlertChannel`, `AlertRule` Pydantic with construction-time validators, `LIVE_ALERT_RULES` (37), `ALERT_THRESHOLDS`
   (10 with explicit `ThresholdUnit`), 31 unit tests green, all 6/6 QG gates green.
2. ⚠️ alerting-service Phase 2 rules wired + KillSwitchBus integration test passes. **PARTIAL** — declarative half
   shipped 2026-05-07 at alerting-service@b025e83 (`_default_routing_rules` consumes UAC `LIVE_ALERT_RULES`, AAVE
   threshold migrated to UAC, 37 unit tests green, `triggers_kill_switch=True` flag set on `KILL_SWITCH_*` rules with
   construction-time validator). **Publish-side hook + integration test DEFERRED** to a future session / Harsh
   pair-review per
   [`issues/alerting_kill_switch_publish_hook_2026_05_08.md`](issues/alerting_kill_switch_publish_hook_2026_05_08.md):
   when an alert with `triggers_kill_switch=True` fires through `route_event`, it must publish a `KillSwitchEvent` to
   the UTL bus so execution-service halt subscribers consume it. Without this hook, paged operators must manually
   trigger the kill switch via DART — acceptable for the 7-day live-soak with humans watching, NOT acceptable as
   institutional steady state. Gates `master_to_live_defi_2026_05_23` Group F (kill-switch verification) + alerting plan
   Phase 8 rehearsal.
3. ✅ AAVE bps threshold has a documented value with a citation comment pointing at source. **Shipped 2026-05-07 at
   UAC@d00326d** — `ALERT_THRESHOLDS["defi_aave_utilization_spike_bps"]` carries explicit `ThresholdUnit.BPS_OF_ONE`
   - citation to Aave V3 InterestRateStrategy `optimalUsageRatio=0.95 RAY` for WETH/USDC/USDT/DAI. Per-archetype
     override: `leveraged_funding_arb` fires at 9000 bps_of_one (90 %) vs default 9500 (95 %).
4. ✅ Plan checkboxes flipped in
   [`alerting_service_live_rules_2026_05_07.plan.md`](alerting_service_live_rules_2026_05_07.plan.md) in the same
   logical unit as each code commit. **Phase 1 flipped at PM@7624ab21; Phase 2 + codex SSOTs (alert-code-taxonomy.md +
   threshold-tuning.md) activated at PM@48ed2e4f.**

**Status (2026-05-08)**: COMPLETE except item 2 publish-side hook (deferred + tracked in `issues/`). Agent 1 stops here;
the deferred hook is a small follow-up (~30-45 min) that either Harsh picks up via the issue doc OR a future Ikenna
session lands once Harsh has pair-reviewed the architectural seam between `route_event` and the `KillSwitchBus`
publisher.

---

## AGENT 2 — Writegate (heaviest tab)

**Identity**: You own the writegate honest-coverage thread end-to-end. Three Ikenna items spanning UTL +
deployment-api + deployment-ui + MDPS + base-service.sh — all ONE plan, builds on itself.

**Scope (3 items)**:

- [x] [DESIGN] P0. writegate Phase 4.A — UTL classifier → deployment-api `error_reason` API field → deployment-ui typed
      badge. Plan:
      [`writegate_honest_coverage_endtoend_2026_05_06`](writegate_honest_coverage_endtoend_2026_05_06.plan.md) Phase
      4.A. Repos: UTL + deployment-api + deployment-ui. Per-asset-group consumer-class judgment lives in
      [`/codex/02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md).
      **DONE 2026-05-07** — deployment-ui@`a7384a0` (TypedReasonBadges + FailurePillarStack components + 24 unit tests +
      client.ts TurboSubDimension extension) + deployment-ui@`621f0b3` (DataStatusTab venue summary line wiring) + Phase
      4.A.3 leaf-stats endpoint (PM@`fa9b5f43`) + Phase 4.B.1 + 4.B.2 flips (PM@`0c2a0cca` / `21f8a277`). Closed-set
      drift guard test fails CI on `_FAILURE_PILLAR_KEYS` / `_EMPTY_REASON_KEYS` drift.
- [ ] [DEEP] P0. writegate Phase 2.A residual — `batch_workers` path-B/C migration + MDPS cluster-coverage wiring
  - delete `_write_manifest_records`. Plan: writegate Phase 2.A. Repos: MDPS + UTL. Three-category empty-vs-failed
    judgment per CLAUDE.md "Three-category empty-output decision" rule; partial-bundle cluster-validation correctness
    for the 11-cluster ES.OPT surface.
- [ ] [GOVERNANCE] P0. writegate Phase 5 — workspace QG honest-coverage % gate + per-(asset_group, data_type) ratchet
      schedule. Plan: writegate Phase 5. Repos: UTL + base-service.sh. Codex SSOT to populate:
      [`/codex/02-data/honest_coverage_baseline_2026_05.md`](/codex/02-data/honest_coverage_baseline_2026_05.md)
      (currently a stub).

**Repos owned (collision boundary)**: UTL (writegate paths only — `legacy_reason_classifier.py`, write-gate helper,
ratchet helpers), MDPS (`base_adapter.py` / `BaseCandleAdapter` / batch_workers), deployment-api (ONLY the
`error_reason` rendering pipeline — Harsh owns new launch + vm-events endpoint files), deployment-ui (typed badge
component), base-service.sh (Phase 5 gate). Hands off UAC alerting / instruments-service / aws-migration to other
agents.

**Read-first**:

- [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md`](writegate_honest_coverage_endtoend_2026_05_06.plan.md)
  — entire plan
- [`/codex/02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md)
- [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)
- CLAUDE.md sections: "Three-category empty-output decision", "Honest absence vs fake placeholders", "Cluster validation
  MANDATORY", "Manifest migration, NOT fallback"
- Existing UTL `legacy_reason_classifier.py` (Tier 3D.2 shipped 2026-05-07, your Phase 4.A wires it through)
- Auto-memory: "HANDOFF — Tier 3D.2 reader-side classify_legacy_empty_row UTL helper"

**Sub-agent fan-out**:

- Phase 4.A: three parallel sub-agents in one message — (a) UTL classifier wiring + tests, (b) deployment-api
  `error_reason` API response shape + endpoint integration, (c) deployment-ui typed badge component + Playwright smoke.
  Master integrates + commits per shippable unit.
- Phase 2.A: two parallel sub-agents — (a) `batch_workers` path-B + path-C migration off `_create_empty_output()` with
  three-category decision, (b) MDPS cluster-coverage wiring per adapter family (ES.OPT 11-cluster being the flagship).
  Master reviews before the `_write_manifest_records` deletion (irreversible — verify all consumers migrated first).
- Phase 5: one general-purpose sub-agent to populate
  [`/codex/02-data/honest_coverage_baseline_2026_05.md`](/codex/02-data/honest_coverage_baseline_2026_05.md) by walking
  the current manifest + computing per-(asset_group, data_type) honest-coverage %; master designs the ratchet schedule +
  writes the QG step.

**Collision risk**:

- deployment-api: Harsh owns new endpoint files (D1+D3); you own `error_reason` rendering pipeline only — touch ONLY the
  response-shape + classifier-call code path. Run `git diff --cached --name-only` before every commit and verify no new
  endpoint files are staged.
- MDPS `base_adapter.py` / `BaseCandleAdapter`: ship the Phase 2.A commit early so Harsh's any sports-features-service
  follow-on isn't blocked. Per parent doc D2 sync point.
- UTL: Tier 3D.2 helper already shipped — you're wiring consumers. No collision unless other agents add new helpers in
  the same module.
- This is the heaviest tab. If context pressure hits mid-Phase-2.A, hand the cluster-coverage wiring to Agent 3 AFTER
  the enumerator VMs are running (Agent 3 idle while VMs process).

**Done definition**:

1. Phase 4.A: typed `error_reason` flows UTL → API → UI, Playwright smoke shows typed badge in data-status drilldown.
2. Phase 2.A: zero `_create_empty_output()` callsites in MDPS, `_write_manifest_records` deleted, partial-bundle
   cluster-coverage gate fires on ES.OPT regression test.
3. Phase 5: workspace QG honest-coverage gate active in `base-service.sh`, baseline doc populated, ratchet schedule
   committed.
4. Plan checkboxes flipped per shippable unit in
   [`writegate_honest_coverage_endtoend_2026_05_06.plan.md`](writegate_honest_coverage_endtoend_2026_05_06.plan.md).

---

## AGENT 3 — Expected-universe enumerator (ops-heavy single workflow)

**Identity**: You execute the Phase 3.D.4 carry-over from the 2026-05-07 PM Claude session. Single multi-step ops
workflow; reading the handoff doc saturates the context.

**Scope (1 item, 4 sub-phases + cross-plan banner sweep)**:

- [x] [INFRA+COORDINATION] P0. Expected-universe enumerator Phase 3.D.4. Plan: documented in
      [`_HANDOFF_expected_universe_enumerator_2026_05_07.md`](_HANDOFF_expected_universe_enumerator_2026_05_07.md).
      Repos: deployment-service + instruments-service + PM (banners across 6+ plans). **DONE 2026-05-07 (Agent 3)** —
      `--apply-write` complete across all 5 asset_groups: 1,455,901 rows in per-VM manifest shards (tradfi 35,033 +
      sports 13,176 + cefi 119,152 + prediction 2,280 + defi 1,286,260) per PM@`79e47874`. Consolidator P0
      ArrowTypeError RESOLVED via instruments-service@`a936a28` per PM@`341bb285`. Banners on 6+ active plans added then
      removed per PM@`dae6d40d` + `5ae70bf1`. 4 sub-phases:
  1. Build
     [`deployment-service/scripts/vm/launch-expected-universe-enumerator-vm.sh`](../../../deployment-service/scripts/vm/launch-expected-universe-enumerator-vm.sh)
     mirroring
     [`launch-defi-phantom-recon-vm.sh`](../../../deployment-service/scripts/vm/launch-defi-phantom-recon-vm.sh).
  2. Update [`vm_zombie_watchdog.py`](../../../deployment-service/scripts/vm/vm_zombie_watchdog.py)
     `VM_PREFIX_TO_BUCKET` (add `expected-universe-enum-`) + relaunch watchdog.
  3. Refresh tarballs: `bash deployment-service/scripts/vm/create-code-tarballs.sh --all`.
  4. Sequential VM launches (TradFi → DeFi → Sports → CeFi stub → Prediction stub) with no-fire-and-forget event
     verification (90s STARTED + 10-15min progress + ENUMERATOR_COMPLETED). Scan-only first, operator-review CSV, then
     `--apply-write`. Banner-add to 6+ active plans on launch, banner-remove on auto-shutdown.

**Repos owned (collision boundary)**: deployment-service `scripts/vm/` (launcher + watchdog + tarball script — all your
files), instruments-service `scripts/enumerate_expected_universe.py` (already shipped, you OPERATE it), PM banner
adds/removes across 6+ plans (writegate / drilldown / master-defi / defi_master / 2 issue files / canonicalisation).
Hands off other deployment-service launchers to Agent 4 (DeFi launch).

**Read-first**:

- [`plans/active/_HANDOFF_expected_universe_enumerator_2026_05_07.md`](_HANDOFF_expected_universe_enumerator_2026_05_07.md)
  — entire doc
- [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) §
  "Rollup-vs-drilldown denominator divergence (codified 2026-05-07)"
- Existing [`launch-defi-phantom-recon-vm.sh`](../../../deployment-service/scripts/vm/launch-defi-phantom-recon-vm.sh)
  as launcher template
- CLAUDE.md sections: "VM launcher script SSOT", "VM Naming Convention", "No fire-and-forget VM launches", "Cross-Plan
  Coordination Banners"
- Auto-memory: "DEX perp onboarding 2026-05-07" (Lighter/Pacifica VM precedent for event verification)

**Sub-agent fan-out**:

- Sub-phases 1-3 in parallel (3 different files): one Task each for launcher script | watchdog dict update | tarball
  refresh. Send in ONE message.
- Cross-plan banner adds: one Task per plan family (writegate / drilldown / defi-master / canonicalisation /
  issue-file-1 / issue-file-2). Banner content is templated in CLAUDE.md, sub-agents copy-paste with the right vm-name +
  ETA. Send all 6 in one message.
- Per-asset-group VM verification: while VMs run, fan out one monitoring sub-agent per asset_group to tail events
  bucket + flag stalls. Master keeps the launch sequence sequential but verification is parallel.

**Collision risk**:

- deployment-service `scripts/vm/`: Agent 4 also touches this dir (DeFi launch + AWS bucket scripts) — different
  launcher files, no overlap. Verify with `git diff --cached --name-only` pre-commit.
- PM banner adds touch many plan files — surgical `git add -p` discipline + push-after-each-plan-file mitigates
  cross-tab conflicts. Mandatory pre-commit `git status` + `git diff --cached --stat` (no path arg) discipline.
- Watchdog relaunch: if you delete the running watchdog VM mid-relaunch, other tabs lose zombie protection for ~2min.
  Coordinate timing — relaunch when no other tab has just launched a VM.

**Done definition**:

1. Launcher script committed + pushed; watchdog dict updated + watchdog VM relaunched + verified by
   `gcloud compute instances list --filter="name~vm-zombie-watchdog"`.
2. Tarballs refreshed with `--all` (verify with `gcloud storage ls gs://deployment-scripts-${PID}/code/`).
3. All 5 enumerator VMs run scan-only → operator review → `--apply-write` → ENUMERATOR_COMPLETED event observed.
4. All 6+ plan banners added on launch + removed on completion (single sweep).
5. Manifest reflects expected-universe rows (verify by spot-checking a TradFi non-trading day + DeFi pre-genesis date
   show as `expected_empty` with reason).

---

## AGENT 4 — DeFi launch + AWS migration + paper-trade smoke

**Identity**: You own the May-23 DeFi critical path. Trading-judgment thread runs through all 4 items: triage informs
launch, launch informs AWS bucket-naming, all three feed paper-trade smoke.

**Scope (4 items, must be executed in this order)**:

- [x] [COORDINATION] P1. **Triage first** —
      [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.plan.md).
      Decide venue-collateral matrix BEFORE the launch picks chains/protocols. Repo: PM. Output: a documented decision
      pinned at the top of the canonicalisation plan + the defi_master Fork 1 plan. **SHIPPED 2026-05-07** by Agent 4
      (PM@6742d8fd, picked up by parallel-agent commit). DRIFT-Solana mSOL/JitoSOL accepted=True at 10% haircut so
      `carry_staked_basis` Solana hedge leg is unblocked at the matrix level; DERIBIT/BYBIT/OKX ETH-LST flips deferred
      to a separate agent (Agent 1 UAC context or independent). Stream B `leveraged_funding_arb` →
      `ARBITRAGE_PRICE_DISPERSION` config variant decision propagated.
- [x] [TRADING] P0. Launch first DeFi backfill VMs (Aave / Uniswap / LST yields / Pyth + Chainlink). Plan:
      [`defi_master_2026_05_07`](defi_master_2026_05_07.plan.md) Fork 1. Repos: MTDS + deployment-service. First run
      with the just-shipped Pyth Hermes + Chainlink multi-chain paths. Per-chain VM event verification mandatory.
      **SHIPPED 2026-05-08** by Agent 4: launched 3 VMs (vault-share-price + lst-rates + gas-fees, 2020-01-01..today),
      caught DefiManifestRecorder blank-reason regression (writegate Phase 3.D.5 Wave 2.M missed DEFI side), shipped
      MTDS@d19d76c fix (DefiManifestRecorder.record_empty(reason=) required + 28-callsite migration across 20 handlers +
      7 unit tests) per `plans/active/issues/defi_manifest_recorder_blank_reason_2026_05_07.md`, refreshed tarballs,
      relaunched: mtds-{vault-share-price,lst-rates,gas-fees}-20260508-010{050,105,121}. Lending-indices VM remains
      DEFERRED (Bug 1 AAVE V3 ETHEREUM silent-zero + Bug 2 COMPOUND V3 subgraph schema + Bug 3 instruments-store-defi
      2022 metadata floor) per `plans/active/issues/lending_indices_handler_bugs_2026_05_07.md`. **Bug 1 root cause
      diagnosed + UAC SSOT fix shipped 2026-05-08 by Harsh Tab 9 at UAC@`6a64a56`** (corrected
      `PROTOCOL_LAUNCH_DATES[("ETHEREUM","AAVE_V3")]` from `2022-03-14` → `2023-01-27`); when Agent 4 picks the relaunch
      back up, **`git pull` UAC first** so the corrected date is in place — relaunching against a stale UAC checkout
      would reproduce Bug 1's silent-zero AAVE V3 ETHEREUM rows. Bugs 2 + 3 still pending fixes.
- [x] [INFRA-DESIGN] P1. aws_migration Phase 2 — dual-bucket setup + Storage Transfer Service config + bucket-naming
      SSOT discipline. Plan: [`aws_migration_defi_first_2026_05_07`](aws_migration_defi_first_2026_05_07.plan.md)
      Phase 2. Repos: deployment-service + UCI. Codex SSOT to populate:
      [`/codex/05-infrastructure/cloud-agnostic-script-pattern.md`](/codex/05-infrastructure/cloud-agnostic-script-pattern.md).
      **SHIPPED 2026-05-07** by Agent 4: deployment-service@7da2f3d (cloud-providers.yaml +10 keys both gcp.storage +
      aws.storage; `scripts/aws/setup-defi-buckets.sh` idempotent provisioning), PM@bd8d272b (codex SSOT 7 sections
      populated). Operator next step: `bash scripts/aws/setup-defi-buckets.sh --apply` from authenticated AWS session.
- [-] [TRADING+INTEGRATION] P0. carry_staked_basis paper-trade smoke (Solana Pyth + jitoSOL/mSOL hedging) — verify
  execution-service + strategy-service + position-balance-monitor-service interactions. Plan: defi_master. Repos:
  execution-service + strategy-service + position-balance-monitor-service. **PARTIAL 2026-05-08** by Agent 4 —
  pre-flight Pyth Hermes endpoint reachable (HTTP 200, 2.3s); full smoke BLOCKED on (a) MTDS@d19d76c VMs draining
  successfully to verify lst-rates Solana coverage post-fix, (b) features-onchain Docker rebuild (defi_master gate), (c)
  4-service QG passes (defi_master gate). Successor: pick up after VM drain confirms manifest captures empty-vs-captured
  rows correctly + features-onchain rebuild lands.

**Repos owned (collision boundary)**: MTDS (DeFi adapters + backfill paths only — Agent 2 owns MDPS, no overlap),
deployment-service `scripts/vm/launch-defi-*` + `setup-defi-buckets.sh` (Agent 3 owns the enumerator launcher, no
overlap), UCI (bucket-naming SSOT), execution-service + strategy-service + position-balance-monitor-service (paper-trade
smoke). Hands off PM master plan refresh to Agent 5.

**Read-first**:

- [`plans/active/defi_master_2026_05_07.plan.md`](defi_master_2026_05_07.plan.md)
- [`plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.plan.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.plan.md)
- [`plans/active/aws_migration_defi_first_2026_05_07.plan.md`](aws_migration_defi_first_2026_05_07.plan.md)
- [`plans/active/master_to_live_defi_2026_05_23.plan.md`](master_to_live_defi_2026_05_23.plan.md) Group F+G (paper-trade
  - custody preconditions)
- CLAUDE.md sections: "DeFi Execution Architecture", "Pyth — UNBANNED 2026-05-06", "VM tarball deployment", "VM Naming
  Convention", "Singleton-locked launchers", "No fire-and-forget VM launches"
- Auto-memory: "MTDS parallelization fix shipped 2026-05-07", "DEX perp onboarding 2026-05-07"

**Sub-agent fan-out**:

- Triage: one general-purpose sub-agent to scan the canonicalisation plan + cross-reference defi_master Fork 1 picks;
  report contradictions. Master makes the call, writes the decision doc.
- DeFi launch: per-chain monitoring sub-agents (Aave / Uniswap / LST / Pyth-Solana / Chainlink-EVM) — fan out 5 in one
  message, each tails its chain's events bucket + flags stalls. Master sequential on launches, parallel on monitoring.
- AWS Phase 2: two parallel sub-agents — (a) dual-bucket setup script + Storage Transfer config, (b) UCI bucket-naming
  SSOT module + tests. Master writes the codex SSOT page integrating both outputs.
- Paper-trade smoke: three parallel sub-agents for pre-flight checks — (a) execution-service Pyth oracle read + Solana
  RPC reachability, (b) strategy-service archetype config validation, (c) position-balance-monitor wallet
  - custody adapter health. Master runs the integrated round-trip after all three green.

**Collision risk**:

- deployment-service `scripts/vm/`: Agent 3 owns enumerator launcher; you own DeFi launch + AWS bucket scripts.
  Different files. Pre-commit `git diff --cached --name-only` discipline.
- PM `defi_master_2026_05_07.plan.md`: Agent 5 may also touch this for master refresh — coordinate via EOD push; if you
  ship a flip, push immediately so Agent 5 pulls fresh.
- aws_migration plan body: parent doc flags Ikenna D4 Phase 2 + Harsh D5 Phase 0/1 collision; Harsh restricted to Phase
  0/1 section. You restricted to Phase 2 section. Surgical `git add -p` if both sections evolve in parallel.
- VM launcher singleton-lock: per CLAUDE.md, rate-limited adapters use singleton-lock. If launching multiple same-prefix
  DeFi VMs, verify the lock pattern is in place.

**Done definition**:

1. Canonicalisation triage decision committed + pinned at top of both plans.
2. All DeFi backfill VMs launched + STARTED + per-chain progress events flowing + first batch completed without
   silent-empty regressions (cluster-coverage gate would catch — but spot-verify a sample parquet).
3. AWS dual-bucket created + Storage Transfer config validated + UCI bucket-naming SSOT shipped + codex page populated.
4. Paper-trade smoke: end-to-end carry_staked_basis trade lands a paper fill in execution-service +
   position-balance-monitor reflects the open position + strategy-service P&L attribution computed (no execution-alpha
   conflation).
5. Plan checkboxes flipped per shippable unit across defi_master + aws_migration + canonicalisation plans.

---

## AGENT 5 — PM governance + coordination + on-call unblocker

**Identity**: You own all PM-only judgment work + serve as the cross-tab on-call unblocker. Lightest tab by
implementation volume but highest by coordination judgment.

**Scope (3 items + on-call)**:

- [x] [COORDINATION] P1. Audit the 2 new umbrellas + master Group F+G fold-in: phase ordering reads as one plan, not 4
      stitched-together plans. Plans: [`ml_and_features_master_2026_05_07`](ml_and_features_master_2026_05_07.plan.md) +
      [`strategy_and_dart_master_2026_05_07`](strategy_and_dart_master_2026_05_07.plan.md) +
      [`master_to_live_defi_2026_05_23`](master_to_live_defi_2026_05_23.plan.md) Group F. Repo: PM. **DONE 2026-05-07
      (Agent 5)** — surface audit + 3-agent deep audit (PM@`21f8a277` + `f3bcbbf8` foot-gun-absorbed). 14 substantive
      deep-audit findings integrated as targeted edits across the 3 plans.
- [x] [COORDINATION] P2. Triage
      [`session_2026_05_07_data_status_audit_findings`](session_2026_05_07_data_status_audit_findings.plan.md) — folds
      into infra_master or stays standalone? Decision-only, ~30 min. Repo: PM. **DONE 2026-05-07 (Agent 5)** —
      STANDALONE (PM@`2bd62a90`). Cross-master rollup spans 5 owner plans; lifecycle-bounded.
- [x] [COORDINATION] P0. Master plan refresh: reflect all other tabs' progress in critical-path § + flip Group F/G
      checkboxes for what shipped this cycle. Plan: master. Repo: PM. **Run last** — needs other tabs' commits landed.
      **DONE 2026-05-07 (Agent 5)** — service-readiness matrix refreshed (PM@`fa9b5f43` foot-gun-absorbed) + 6-agent
      fan-out for substantive critical-path § Week 1/2/3 refresh + new "Top 3 risks for May-23 cutover" subsection
      (PM@`df5b9b78`) + CEFFU codex doc stub + 5 P0 follow-up todos in work-stream F (PM@`3fad0d61`).
- [x] [ON-CALL] P1. Cross-tab unblocker:
  - Sweep stale cross-plan banners (verify VMs no longer RUNNING via gcloud, refactors landed via plan-checkbox check).
  - Audit other tabs' plan-flip hygiene (`git log --oneline live-defi-rollout` then verify each code commit has a
    same-day plan flip).
  - Resolve `live-defi-rollout` push races for other tabs if they ping you (`git pull --rebase` + push).
  - Pre-commit discipline check on accidental bundling — if any tab reports the foot-gun (incidents PM@961980db /
    PM@611b9501 / PM@7de75819), help recover surgically.

  **DONE 2026-05-07 (Agent 5)** — read-only sweep verified zero stale banners, healthy plan-flip hygiene across recent
  commits, no foot-gun rescue requests received. Foot-gun #1 hit Agent 5's own commits 3× this session (PM@`21f8a277` /
  `fa9b5f43` / `f3bcbbf8` absorbed by parallel-agent semver-rollout-bot's `git add` cycles); content correct,
  attribution muddled — documented in auto-memory `handoff_agent5_5tab_layout_2026_05_07.md`.

**Repos owned (collision boundary)**: PM only — but multiple plan files. Mandatory surgical `git add -p` discipline

- push-after-each-plan-file. Risk on `master_to_live_defi_2026_05_23.plan.md` body (Agent 4 may touch via defi-master
  cross-references; coordinate timing).

**Read-first**:

- [`plans/active/_AUDIT_2026_05_07_dependency_graph.md`](_AUDIT_2026_05_07_dependency_graph.md) — the audit that drove
  all umbrella consolidations
- [`plans/active/master_to_live_defi_2026_05_23.plan.md`](master_to_live_defi_2026_05_23.plan.md) — entire Group F + G
- [`plans/active/ml_and_features_master_2026_05_07.plan.md`](ml_and_features_master_2026_05_07.plan.md)
- [`plans/active/strategy_and_dart_master_2026_05_07.plan.md`](strategy_and_dart_master_2026_05_07.plan.md)
- [`plans/active/session_2026_05_07_data_status_audit_findings.plan.md`](session_2026_05_07_data_status_audit_findings.plan.md)
- CLAUDE.md sections: "Cross-Plan Coordination Banners", "Plan Locking", "Capture Discoveries As Plan Todos
  Immediately", "Commit + Push + Flip Plan Checkboxes"
- Auto-memory: "Master plan audit continuation 2026-05-07"

**Sub-agent fan-out**:

- Umbrella audit: 3 parallel sub-agents in one message, one per umbrella (ml_and_features / strategy_and_dart / master
  Group F+G). Each sub-agent reports phase-ordering smell + critical-path callout gaps. Master integrates + edits.
- Master refresh: parallel sub-agents per asset_group umbrella (cefi / defi / tradfi / sports / prediction +
  infrastructure). Each reads its umbrella + reports what shipped this cycle vs what remains. Master writes the
  refreshed critical-path section.
- Triage: lightweight, no sub-agents needed.
- On-call: reactive, fan out only when an unblock request arrives.

**Collision risk**:

- `master_to_live_defi_2026_05_23.plan.md`: parent doc flags Ikenna-only (D5 refresh). Other tabs stay out, but watch
  for accidental edits. If Agent 4 needs to touch master for a defi cross-reference, coordinate timing.
- Other plan files: every other tab flips its own plan checkboxes. Your role is to AUDIT flip hygiene, not to flip for
  them. Don't pre-emptively flip another tab's checkboxes.

**Done definition**:

1. 2 umbrella audits completed with concrete phase-ordering edits committed (or "no edits needed" finding documented).
2. data_status_audit_findings triage decision committed (folded into infra_master or marked standalone with reason).
3. Master plan refresh committed AFTER all other tabs report done — captures their shipped work in critical-path §.
4. On-call: zero stale banners at end of cycle, zero plan-flip-hygiene violations across other tabs (or all surfaced +
   resolved).

---

## Cross-tab handshakes

These are the ONLY hard sync gates. Operate independently otherwise.

- [ ] **UAC alerting (Agent 1) → other tabs**: when Agent 1 pushes the `AlertCode` StrEnum, all other tabs `git pull` in
      their UAC checkout before next UAC edit. Risk surface: `__init__.py` re-exports.
- [ ] **MDPS Phase 2.A residual (Agent 2) shipped early**: parent doc D2 sync requires this committed before lunch so
      Harsh's any sports-features-service follow-on isn't blocked. Agent 2 self-imposes this gate.
- [ ] **Enumerator VMs (Agent 3) running → Agent 5 banner-sweep**: Agent 3 adds banners on launch; Agent 5 sweeps stale
      ones on completion. Coordinate via the banner content's ETA field.
- [ ] **Canonicalisation triage (Agent 4) → DeFi launch (Agent 4)**: same tab, sequential. Agent 4 enforces internally.
- [ ] **All other tabs report done → master plan refresh (Agent 5)**: Agent 5 runs last. Other tabs ping Agent 5 when
      their done-definition is met.
- [ ] **deployment-api (Agent 2 + Harsh)**: Agent 2 touches ONLY `error_reason` rendering pipeline. Harsh touches ONLY
      new launch + vm-events endpoint files. Pre-commit `git diff --cached --name-only` verifies separation.
- [ ] **deployment-service `scripts/vm/` (Agent 3 + Agent 4)**: Agent 3 owns enumerator launcher + watchdog + tarball
      script. Agent 4 owns DeFi launch + AWS bucket scripts. Different files. Pre-commit name-only verifies.
- [x] **UAC `chain_env.py` `PROTOCOL_LAUNCH_DATES` (Harsh Tab 9 → Agent 4 D4) — SHIPPED 2026-05-08 at UAC@6a64a56**.
      Harsh's Tab 9 (lending-indices-relaunch-tab) diagnosed AAVE V3 ETHEREUM launch date wrong via the Bug 1 reproducer
      (per [`issues/lending_indices_handler_bugs_2026_05_07.md`](issues/lending_indices_handler_bugs_2026_05_07.md) Q1)
      and shipped UAC@`6a64a56` flipping `("ETHEREUM", "AAVE_V3"): "2022-03-14" → "2023-01-27"`. **Coordination pattern
      for future similar UAC SSOT fixes (any `*_LAUNCH_DATES` / `*_GENESIS_DATES` / `SOURCE_COVERAGE_START` /
      `venue_trading_calendar`)**: any agent in flight on `chain_env.py` (or sibling SSOTs) when a downstream Tab is
      about to consume `PROTOCOL_LAUNCH_DATES` for VM launches MUST coordinate via a top-of-file
      `🟡 IN-FLIGHT     REFACTOR` banner per CLAUDE.md "Cross-Plan Coordination Banners" rule. Agent 4's deferred
      lending-indices relaunch + any future Agent 3 expected-universe enumerator re-runs that consume
      `PROTOCOL_LAUNCH_DATES` are now safe (the corrected date is on `origin/live-defi-rollout`); pull UAC before
      relaunching.

## Discipline reminders (every tab, every commit)

- **Pre-commit (mandatory)**: `git status` then `git diff --cached --stat` (NO path argument). If anything you don't
  recognise is staged, surgically `git restore --staged <file>` or `git stash --keep-index` it. See CLAUDE.md "mandatory
  pre-commit check" — incidents PM@961980db / PM@611b9501 / PM@7de75819 are documented foot-guns.
- **Per shippable unit**: commit + push immediately. Local-only commits are invisible to other tabs + CI + VMs pulling
  from `live-defi-rollout`. No "I'll commit at the end."
- **Plan flip in same logical unit as code**: ship code → flip checkbox → commit plan flip → push. Don't batch.
- **Sub-agent rules injection**: paste
  [`cursor-configs/SUB_AGENT_MANDATORY_RULES.md`](../../cursor-configs/SUB_AGENT_MANDATORY_RULES.md) at top of every
  Task prompt. Sub-agents in `--print` mode CANNOT read files from disk.
- **Discoveries as plan todos**: any side-discovery during execution → plan todo at the moment it surfaces (P0-P3 +
  `**DEFERRED**` / `**NICE-TO-HAVE**` body prefix + provenance citation). Same logical unit as discovery.
- **Dirty deps → direct push not quickmerge**: parent CLAUDE.md rule. Default flow:
  `git add <files> && git commit && git push origin live-defi-rollout`.
- **Cross-plan coordination banners**: when launching VMs or starting in-flight refactors, banner every other active
  plan whose work is influenced. Banner-add is part of the launch logical unit. Banner-remove on completion (Agent 5
  sweeps strays).

## Done definition (whole layout)

When all 5 tabs hit their per-tab done-definition, the 13-item Ikenna split is complete. Agent 5 then runs the master
refresh capturing the cycle's shipped work, and the parent [`work_split_2026_05_07.md`](work_split_2026_05_07.md)
checkboxes are flipped in bulk reflecting reality.
