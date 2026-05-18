---
title: Harsh's daily work-split — 2026-05-18 (Cycle 2 Day-3; mechanical-only — heavy decisions on Ikenna side)
type: coordination-doc
status: active
created: 2026-05-18
deadline: 2026-05-19
horizon: 1 calendar day (Cycle 2 Day-3 of cutover window per post_freeze_roadmap_2026_05_16_to_05_23.md)
companion_to: null
locked_by: live-defi-rollout
locked_since: 2026-05-18
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
effective_concurrent_slots: 8
estimate_calibration_note: |
  Work-split itself (design class). Scope it schedules = ~16-20 cal AI-days across 8 slots
  on 1 calendar day — pure mechanical pickup from cycle-close deferrals + master-plan
  inventory residuals. Heavy/decision work (Cycle 2 cutover bucket migration + delegate-flip,
  AWS migration, custody Phase 4-5, api_keys credentials, code_freeze sequencing) routed
  to Ikenna side per operator direction 2026-05-18 06:15 UTC.
---

# Harsh's daily work-split — 2026-05-18 (mechanical-only)

> **Scope discipline**: this split is **mechanical work only** — lint sweeps, test coverage extensions, codex drift
> fixes, ruff cleanup, unused-import audits, deferred-cycle-close pickup. Per operator direction 2026-05-18 06:15 UTC,
> the heavy decision-bearing items for today (Cycle 2 Day-3 cutover: write-pause + 36-consumer delegate-flip; AWS
> migration; custody Phase 4-5; api_keys credentials Phase 4-5; code_freeze Phase 2 cutover-runbook execution) are on
> the **Ikenna side** today. Harsh slots stay in mechanical-throughput mode and stay out of cross-side cutover
> coordination unless Ikenna pings.
>
> **Calendar context**: today is **Cycle 2 Day-3** per
> [`post_freeze_roadmap_2026_05_16_to_05_23.md`](post_freeze_roadmap_2026_05_16_to_05_23.md). May-23 cutover = 5 days
> from today. **pvl-p18a paper-runnable target = 2026-05-21 05:31 UTC** (B-015 paper VM running on harsh side since
> 2026-05-18 05:31:38Z; VM monitoring handed to dedicated agent — main does NOT poll the VM).
>
> **🟢 ESTIMATE CALIBRATION** — applies workspace-wide per
> [`codex/08-workflows/estimation-calibration.md`](../../codex/08-workflows/estimation-calibration.md). All slot AI-day
> budgets below are CALIBRATED.

## Why this split

**Backlog observation**: 2026-05-15 EOD cycle-close left ~30 deferred items across 6 slots (slot 4 items 12-15; slot 6
items 2-9; slot 8 items 15-20) plus master-plan inventory residuals on near-done plans (`defi_basedpyright_features_service`
51/54, `defi_simulation_realism` 46/47, `bucket_name_ssot_canonicalisation` 16/22, `alerting_service_live_rules` 50/65,
`ruff_workspace_cleanup` 17/31, `expected_unattempted_propagation_chain` 34/44, `mock_data_pipeline_benchmarking` 29/31).

3 days of cycle break (weekend + B-015 VM crisis 2026-05-17 → 2026-05-18 morning) blocked normal cycle dispatch. Today is
the resume — clear the deferred backlog + push near-done plans over the line before Cycle 3 (2026-05-20) paper-trade
smoke begins.

**Critical-path constraints**:

1. 🟢 **B-015 paper VM stability** — VM `strategy-paper-carry-staked-basis-20260518-105854` running since 05:31:38Z.
   Dedicated agent monitors. Main does NOT poll. If VM dies → cross-side ping to Ikenna-main + dedicated agent.
2. 🟡 **pvl-p18a 3-day clock** — paper-runnable threshold 2026-05-21 05:31 UTC. Margin to cutover = ~50h. Every
   VM-fail-retry cycle eats margin → slot bandwidth pivots to VM-fix if VM falls.
3. 🟢 **No cross-side handshakes from Harsh today** — Ikenna owns Cycle 2 Day-3 cutover execution + write-pause
   coordination + 36-consumer delegate-flip. Harsh stays out.

## Hard rules baked into this split

- **Conflict rules (carry over from 2026-05-15)**: deployment-api + deployment-ui = slot 7 OWNS; features-service =
  slot 4/9 (slot 4 priority on tests, slot 9 on MTDS adapters); MTDS + PBM = slot 9; execution-service = slot 5 (Phase
  9 cost models / risk / fork tests) + slot 2 (complexity lint sweep — separate surface); risk-and-exposure-service =
  slot 5; pnl-attribution-service = slot 5; UAC = surgical only (Ikenna primary, Harsh slots take 1 file at a time max
  per item, no architectural changes); features-service Phase B coverage waves = slot 4 or carry-over polling worker.
- **Compose with workspace rules**: Commit + Push + Flip Plan Checkboxes (in the SAME agent turn); Capture Discoveries
  As Plan Todos Immediately; Grep-Then-Read (not Grep-Then-Conclude); Findings Triage; External Data Is Always Available;
  Plans Run To Actual Completion. SUB_AGENT_MANDATORY_RULES.md paste at top of every Task spawn.
- **No fire-and-forget**: every commit lands on `live-defi-rollout` via `quickmerge.sh "msg" --agent` (Pass-1 QG already
  green from local) or directly via `git push origin HEAD:live-defi-rollout` after Pass-1 QG green.
- **No cross-side dispatch from Harsh-main today**: if a finding looks cross-side, file in `_agent_pings.md` and stop.
- **VM verify at T+10min rule** (codified 2026-05-18 05:15 UTC): any VM launch by any slot MUST verify
  DEPLOYMENT_STARTED + first progress event within 10 min of launch, not "pushed = launched". Captured as plan-todo
  for codex/05-infrastructure update on slot 6 buffer.

## Slot stack — ~18-20 cal AI-days across 8 implementer slots

### Slot 1 main — orchestration (continuous, uncounted)

- Polling loop (~5-10 min cadence) once user starts slots.
- Ping triage (cross-side + intra-side).
- Commit + Push + Flip plan checkboxes for shipped slot work.
- Master plan inventory regenerator at morning + EOD:
  `python3 unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py`.
- B-015 VM watch is **NOT** main's job today (dedicated agent owns). Main forwards any VM ping to that agent.
- Cycle 2 Day-3 cutover work is **NOT** main's job today (Ikenna side). Main forwards any cutover ping to Ikenna-main.

### Slot 2 — execution-service complexity / lint sweep continuation — ~3 cal AI-days

> **Carry-over from autonomous polling loop 2026-05-17**: execution-service Phase B C901/complexity sweep was at
> batch 97 cumulative ~157 files cleared (last @ab2fbe80b). More violations remain.

#### Mechanical queue

- [x] ✅ **1. execution-service Phase B C901/complexity sweep batches 98-105 (continuation)** — C901 was fully cleared by batch 97. Batches 98-104 cleared all remaining 31 E501+I001 violations (31→0). Lint fully clean. execution-service@0d32d9c4. Pre-existing test failures noted (30 unit tests failing before batch 98 @ab2fbe80 — test harness missing `_read_book_metrics`/`_parse_candle_horizon_secs` methods; slot 5 test surface); filed finding in issues/.
- [ ] **2. ruff_workspace_cleanup_2026_05_12 residual items** — 14 items remaining (17/31 = 55%). Pick the 3-4
      smallest mechanical items (likely ruff-flag adoptions or single-file refactors). Plan path:
      [`ruff_workspace_cleanup_2026_05_12.md`](ruff_workspace_cleanup_2026_05_12.md).
- [ ] **3. workspace-wide unused-import audit (slot 4 deferred item 15)** — scan repos for unused imports surviving
      ruff sweep. File issue doc per repo + fix mechanical ones. Done-def: cleanup report + 5+ fixes. **DEFER if
      slot 4 picks up first** — coordinate via slot_2 ping if Q.

#### Reserve queue (pick if primary done early)

- [ ] **4. uac_qg_preexisting_size_violations — Harsh-side surgical 1 file** (P2) — slot 6 buffer item 8. UAC has
      5 pre-existing size violations. Take **the SMALLEST/clearest-cut one** only; refactor only that one; leave
      others for Ikenna. Done-def: 1 file under 900 lines + UAC QG green.

#### Coordination

- **Owned repos**: execution-service (lint surface) + workspace-wide audit scripts.
- **No cross-side handshakes**.
- **Conflict-risk**: execution-service Phase 9 tests = slot 5 surface; lint = slot 2 surface. Run `git fetch` before
  each batch + check for slot-5 commits on execution-service.

### Slot 3 — defi_simulation_realism final + B-016 paper VM monitor — ~2 cal AI-days

> **B-016 APD paper VM** launched 2026-05-15 Phase 2; 30-day autonomous monitor running. Verify still healthy +
> generating events. **B-015 monitoring is NOT on this slot** — dedicated agent owns B-015.

#### Mechanical queue

- [x] ✅ **1. B-016 APD paper VM health check — N/A** — slot-3 polling 2026-05-18 06:57 UTC surfaced that B-016 was
      DEFERRED 2026-05-15 (MTDS CeFi tick coverage insufficient for any 7-day window — see slot_3 ping Q1 from
      2026-05-15 05:18 UTC). No VM exists to check. Item dropped; proceed to item 2.
- [x] ✅ **2. defi_simulation_realism_2026_05_10 final item (98%, 46/47)** — closed by slot-1 main 2026-05-18
      @PM@538aa2fd. Phase 9E = master plan refresh (slot-1-owned per CLAUDE.md G-14). Group F items 17+18 Continuous
      Verification rows extended with defi_simulation_realism Phase 2 design + Phase 8C Tenderly-fork reconciliation
      references; Last verified flipped to 2026-05-18. Plan closes 47/47.
- [x] ✅ **3. strategy_service_phase10_codex_drift — Drift 2 only** — PM@5520e125. 2 codex pointer lines added:
      `market-making.md` (defi_lp/ → MARKET_MAKING) + `arbitrage-structural.md` (mev/ → ARBITRAGE_STRUCTURAL), both
      citing enforcement test `strategy-service@f01d12d`. Drift 2 closed.

#### Reserve queue

- [x] ✅ **4. archetype_paper_runnable_matrix follow-ups** — verified 5/5 complete. No new items from pvl-p18b:
      carry_staked_basis state update to `paper-runnable` gated on ≥3-day soak (B-015 VM running since 05:31:38Z;
      clock expires ~2026-05-21). APD still `backtest-only` pending APD orchestrator. No action needed.
- [ ] **5. REFILL — defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07 residuals (65%, 26/40)** —
      added 2026-05-18 by slot-1 main after slot-3 reached QUEUE EXHAUSTED at 07:08 UTC. 14 items remaining. Strategy
      + codex territory matches slot-3 ownership. Pick 2-3 mechanical items (codex docstring drift, archetype enum
      cross-refs, per-archetype venue subset annotations). Plan path:
      [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md).
      Avoid items that change UAC schemas (Ikenna primary).

#### Coordination

- **Owned repos**: strategy-service + codex.
- **No cross-side handshakes** on B-016 (Ikenna already ACKed Phase 2 2026-05-15).
- **B-015 ping forwarding**: if dedicated agent forwards a strategy-service-side bug, slot 3 picks up. Otherwise no
  touch.

### Slot 4 — deferred items 12-15 (sit / alerting / batch-live / unused-imports) — ~4 cal AI-days

> **Carry-over from 2026-05-15 slot-4 queue**: items 12-15 deferred (cycle-close).

#### Mechanical queue

- [x] ✅ **1. system-integration-tests Phase 8 honest-coverage scenarios (slot 4 item 12)** — sit/ tests for
      honest-coverage emission flow (VM emits → manifest writer → coverage.json → API endpoint). **Check overlap
      with slot 4's prior sit DeFi paper flows shipped @sit@fba72b7 before duplicating.** Done-def: 2+ scenarios +
      sit QG green. — sit@47a1e04: 11 tests / 4 scenario classes (captured/empty_confirmed/attempted_failed/mixed); QG ✅ 56s
- [ ] **2. alerting-service alert routing tests (slot 4 item 13)** — routing by severity (P0 → pager, P1 → email,
      P2 → slack mock). Done-def: routing parity + alerting-service QG green.
- [ ] **3. batch-live-reconciliation reconcile_shard edge cases (slot 4 item 14)** — empty shard, single-row,
      schema-drift, very-large (memory pressure). Done-def: 4+ edge-case tests + batch-live-reconciliation QG green.
- [ ] **4. workspace-wide unused-import audit (slot 4 item 15)** — scan repos for unused imports surviving ruff
      sweep. Issue doc per repo + fix mechanical ones. Done-def: cleanup report + 5+ fixes. **COORDINATE with slot 2
      item 3 — whichever slot starts first owns it; the other slot skips and picks reserve.**

#### Reserve queue

- [ ] **5. features-service Phase B coverage waves continuation (Wave 59+)** — last shipped Wave 58
      (halftime_columns + odds_columns @100%). Pick next wave from features-service test/coverage gap list.
      Done-def: 1 wave shipped (2+ feature groups to 100% coverage).
- [ ] **6. defi_basedpyright_features_service_2026_05_15 final items (94%, 51/54)** — 3 checkboxes left. Plan path:
      [`defi_basedpyright_features_service_2026_05_15.md`](defi_basedpyright_features_service_2026_05_15.md).
      Mechanical basedpyright cleanup.

#### Coordination

- **Owned repos**: features-service (test surface) + system-integration-tests + alerting-service + batch-live-reconciliation-service.
- **No cross-side handshakes**.
- **Conflict-risk**: features-service MTDS-adapter side = slot 9 (separate surface).

### Slot 5 — execution-service / risk / pnl test extension reserve — ~2 cal AI-days

> **2026-05-15 cycle-close**: 19-item extended queue ALL DONE. No carry-over. Pick from master-plan inventory
> residuals.

#### Mechanical queue

- [x] **1. writegate_honest_coverage_endtoend_2026_05_06 residual items** — 48% done (118/246). Many items still
      open. Plan path:
      [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md).
      **Pick 2-3 mechanical items only** — avoid items requiring architectural decisions or cross-service emission
      contract changes (those = Ikenna primary).
      ✅ Phase 2.E.4 DOCS (3 checkboxes): CLAUDE.md "Manifest + honest absence" SSOT line now cross-links § "Reason taxonomy" + § "Per-service consumer-class audit" — pm@30ccfd3c
- [ ] **2. expected_unattempted_propagation_chain_2026_05_12 residuals (77%, 34/44)** — 10 items left. Plan path:
      [`expected_unattempted_propagation_chain_2026_05_12.md`](expected_unattempted_propagation_chain_2026_05_12.md).
      Pick 2-3 mechanical service-side wiring items only (avoid UAC schema changes).
      🔴 AUDITED: all 10 remaining items BLOCKED — Pass 3/4 apply-flips DEFERRED (need MDPS/features infra semantics);
      Phase 6 VALIDATE items need VM/GCP manifest access; P2 DeFi classifier crossref DEFERRED post-live-cutover;
      P2 sports classifier extension DEFERRED. No mechanical slot-5 items available.

#### Reserve queue

- [ ] **3. mock_data_pipeline_benchmarking_2026_05_10 final items (94%, 29/31)** — 2 checkboxes left. Plan path:
      [`mock_data_pipeline_benchmarking_2026_05_10.md`](mock_data_pipeline_benchmarking_2026_05_10.md). Close out.
      🔴 AUDITED: 3.C-followup DEFERRED ("Do NOT add until Phase 3.D confirms"); 3.D PARTIAL/DEFERRED (needs VM subprocess mode + operator sign-off).
- [ ] **4. data_status_drilldown_shard_atom_alignment_2026_05_07 final items (83%, 34/41)** — 7 checkboxes left.
      Plan path: [`data_status_drilldown_shard_atom_alignment_2026_05_07.md`](data_status_drilldown_shard_atom_alignment_2026_05_07.md).
      Pick mechanical items only.
      🔴 AUDITED: 4 items deployment-api/ui (slot 7 conflict rule); 2 items DEFERRED (UAC+UTL+predictions); 1 item infrastructure_master owner. No slot-5 surface available.
- [ ] **5. REFILL — test-coverage extension reserve on slot-5 owned surfaces** — added 2026-05-18 by slot-1 main
      after slot-5 QUEUE EXHAUSTED at 08:00 UTC (items 2/3/4 all BLOCKED). Slot-5 has consistently shipped 4-6
      tests/item across 19 items 2026-05-15. Identify 3-4 uncovered surface areas across
      `execution-service` (Phase 9 / fork / risk / adapter error paths), `risk-and-exposure-service`
      (rule firing edge cases, recovery semantics), `pnl-attribution-service` (cost attribution edge cases).
      Done-def: 12+ new tests across 3+ files + per-repo QG green. Conflict rule: execution-service Phase 9 =
      slot-5 (you), execution-service lint = slot 2 (separate surface).
- [ ] **6. REFILL — bucket_name_ssot_canonicalisation_2026_05_10 residuals (73%, 16/22)** — added 2026-05-18 by
      slot-1 main. 6 items remaining. Workspace-wide SSOT refactor — likely additional `gs://` f-string sweep across
      service-side scripts that bypass `resolve_bucket_name(...)`. Plan path:
      [`bucket_name_ssot_canonicalisation_2026_05_10.md`](bucket_name_ssot_canonicalisation_2026_05_10.md).
      Avoid items that change UAC schemas (Ikenna primary). Pick if item 5 has any blockers.

#### Coordination

- **Owned repos**: execution-service (Phase 9 / fork / risk) + risk-and-exposure-service + pnl-attribution-service.
- **No cross-side handshakes**.
- **Conflict-risk**: execution-service complexity lint = slot 2 surface (separate). Pull origin/LDR before each
  Phase 9 commit.

### Slot 6 — deferred items 2-9 (codex drift + sit + expected_unattempted + buffer) — ~4 cal AI-days

> **Carry-over from 2026-05-15 slot-6 queue**: item 1 (UTL QG sweep) DONE; items 2-9 deferred (cycle-close).
> **Slot 6 owns the slot-6 buffer items as-is** — no re-routing.

#### Mechanical queue

- [x] ✅ **1. strategy_service_phase8_codex_drift (slot 6 item 2)** —
      [`plans/active/issues/strategy_service_phase8_codex_drift_2026_05_15.md`](issues/strategy_service_phase8_codex_drift_2026_05_15.md).
      5 codex docstring/line-ref drifts in `codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md` +
      `arbitrage-price-dispersion.md`. Done-def: 5 drifts patched + codex matches shipped code.
      — PM@54b06a2c (slot 6, 2026-05-15). Issue RESOLVED 2026-05-17. Checkbox backfill by slot-6 2026-05-18.
- [x] ✅ **2. sit_may23_critical_path_coverage_gaps (slot 6 item 4)** —
      [`plans/active/issues/sit_may23_critical_path_coverage_gaps_2026_05_15.md`](issues/sit_may23_critical_path_coverage_gaps_2026_05_15.md).
      SIT scenarios for: (a) DeFi paper carry, (b) DeFi paper APD, (c) mode-switch live/batch gate, (d) batch-live
      DeFi parity smoke. **Check slot 4 item 1 overlap before duplicating.** Done-def: gaps not already filled by
      slot 4 + sit QG green.
      — system-integration-tests@3872ce2 (slot 7 Ikenna, 2026-05-16). Issue RESOLVED 2026-05-16. Checkbox backfill by slot-6 2026-05-18.
- [x] ✅ **3. expected_unattempted_propagation_gap (slot 6 item 5)** —
      [`plans/active/issues/expected_unattempted_propagation_gap_2026_05_12.md`](issues/expected_unattempted_propagation_gap_2026_05_12.md).
      Wire `record_expected_unattempted()` into MTDS/MDPS/features/ML skip paths through the UTL emission_publisher
      chain. Done-def: 4 services emit `expected_unattempted` events + tests. **Conflict-risk**: MTDS = slot 9
      surface, coordinate.
      — uac@0457b0e + mdps@3f70cf6 + features-service@a58480fb (Gate 1 FIRED 2026-05-13). Issue RESOLVED 2026-05-17. Checkbox backfill by slot-6 2026-05-18.
- [x] ✅ **4. codex_04_architecture_drift_audit cleanup (slot 6 item 6)** —
      [`plans/active/issues/codex_04_architecture_drift_audit_2026_05_15.md`](issues/codex_04_architecture_drift_audit_2026_05_15.md).
      4 docs with `unified_trading_services` → `unified_trading_library` rename leftovers + 4 docs with `pyright` →
      `basedpyright` references. Mechanical fixes ~30 min. Done-def: 8 docs updated + grep confirms 0 stale refs.
      — PM@bdbd899f (2 files, slot-3 2026-05-17) + PM@564766e3 (README.md + tier-and-import-architecture.md, slot-6 2026-05-18). Category B clean. Done.

#### Reserve queue

- [x] ✅ **5. UTL bash smoke tests for QG_MEM_CAP (slot 6 item 7)** — Add UTL-side bash smoke tests verifying:
      (a) Linux path builds MEM_WRAP correctly; (b) macOS-simulated path emits warning + empty MEM_WRAP;
      (c) `QG_MEM_CAP=0` silences warning. Done-def: 3+ bash smoke tests + UTL QG green.
      — PM@263e25b6 (5/5 assertions pass; test-qg-mem-cap.sh added to quality-gates-base/tests/).
- [x] ✅ **6. codex/06-coding-standards/quality-gates.md SSOT cross-link refresh (slot 6 item 9)** — verify
      `quality-gates.md` cross-links to the new `quality-gates-memory-governance.md`. Sweep for stale references to
      the OLD `cpu_count // 4` default. Done-def: cross-link added + 0 stale references.
      — PM@782f5acc (Memory Governance subsection added; 0 stale cpu_count // 4 refs confirmed in quality-gates.md).
- [ ] **7. codify "VM verify at T+10min" rule** — drop new section in
      `codex/05-infrastructure/vm-tarball-deployment.md` capturing the rule shipped via 2026-05-18 05:15 UTC ping
      (post-launch verification at T+10min before claiming VM "launched"). Done-def: codex section landed + cross-link
      from CLAUDE.md "no fire-and-forget VM launches" line.

#### Coordination

- **Owned repos**: strategy-service codex + sit + UTL bash + codex/06.
- **No cross-side handshakes**.
- **Conflict-risk**: MTDS = slot 9 surface (item 3 above touches MTDS — coordinate); features-service = slot 4 surface.

### Slot 7 — deployment-api / deployment-ui maintenance — ~2 cal AI-days

> **2026-05-15 cycle-close**: 7-item queue (items 14-20) ALL DONE. No carry-over. Pick from master-plan inventory
> residuals on deployment-api + deployment-ui owned surfaces.

#### Mechanical queue

- [ ] **1. deployment-ui + deployment-api Phase 2F final items (data_status_ui_phase_2f 80%, 4/5)** — 1 item left.
      Plan path: [`data_status_ui_phase_2f.md`](data_status_ui_phase_2f.md). Close out.
- [ ] **2. deploy_missing_auto_launch_2026_05_07 final item (93%, 13/14)** — 1 item left. Plan path:
      [`deploy_missing_auto_launch_2026_05_07.md`](deploy_missing_auto_launch_2026_05_07.md). Close out.
- [ ] **3. deployment-api / deployment-ui Phase 4 cron infra status check** — verify
      `gs://central-element-323112-deployment-events/quality_gates_snapshot/` is still being updated daily by the
      cron VM (B-018 shipped 2026-05-14). Spot-check today's snapshot. File finding if stale.

#### Reserve queue

- [ ] **4. deployment-api + deployment-ui ImportError fallback sweep (deployment-api×3 from slot 2 carry-over)** —
      slot 2's deferred item 6 had deployment-api×3 violations. Slot 7 owns deployment-api → take this. Done-def:
      3 violations cleared + deployment-api QG green.

#### Coordination

- **Owned repos**: deployment-api + deployment-ui (SOLE owner).
- **No cross-side handshakes**.

### Slot 8 — deferred items 15-20 (pre-commit / issue-doc / UTL HMAC / cassette / constraints / codex cross-links) — ~3 cal AI-days

> **Carry-over from 2026-05-15 slot-8 queue**: items 15-20 deferred (cycle-close).

#### Mechanical queue

- [x] ✅ **1. pre-commit hook standardization (slot 8 item 15)** — audit `.pre-commit-config.yaml` across
      26+ active repos; align to canonical PM template + propagate. Done-def: 0 drift across active repos.
      — 24/26 repos updated (added gitleaks hook + multi-line entry: format). deployment-api + deployment-ui skipped (slot 7 SOLE owner — slot 7 to run rollout-pre-commit-configs.sh). SHAs: alerting-service@41112b7, execution-service@803d7e3a, unified-trading-pm@fae60a76 + 21 others on LDR.
- [x] ✅ **2. issue-doc triage sweep (slot 8 item 16)** — `plans/active/issues/` accumulated ~40+ issue docs. Triage:
      (a) close docs whose finding is shipped, (b) merge duplicates, (c) flag stale (≥7 days no activity). Done-def:
      triage scoreboard added to each doc + 10+ closed/merged.
      — 68 docs triaged: 53 CLOSED-SHIPPED, 15 OPEN/BLOCKED. Triage scoreboard section added to all 68. PM@(flip commit).
- [x] ✅ **3. workspace-constraints.toml audit (slot 8 item 19)** — verify all repos honor workspace-constraints.toml
      pin versions. Done-def: 0 drift report.
      — PASS: check-dependency-alignment.py --json → aligned=True, 0 issues. 5 internal version constraint pre-existing issues (UTL 0.3.167 vs repos requiring ≥0.4.0) are semver-agent lag, not workspace-constraints.toml violations — tracked by version-alignment-gate separately.
- [ ] **4. codex/06 cross-link sweep (slot 8 item 20)** — sweep codex/06-coding-standards/ for stale cross-links
      (post-recent renames). Done-def: 0 broken anchors.

#### Reserve queue

- [ ] **5. UTL HMAC signing coverage extension (slot 8 item 17)** — DEFERRED because UTL QG had xdist isolation
      issue. Slot 6 shipped UTL@d3488b7 + UTL@30db050 to fix xdist; UTL QG now green. Slot 8 can now pick this up.
      Done-def: HMAC coverage extension shipped + UTL QG green.
- [ ] **6. workspace-wide cassette parity refresh (slot 8 item 18)** — run cassette schema parity tests across UAC
      external dirs. Done-def: parity green + any drift fixed.

#### Coordination

- **Owned repos**: cross-repo audit work + UTL HMAC.
- **No cross-side handshakes**.
- **Conflict-risk**: UTL = high cross-slot traffic (slot 6 + slot 8 both touch). Always `git fetch` + pull
  origin/LDR before commit.

### Slot 9 — MTDS / PBM coverage extension — ~2 cal AI-days

> **2026-05-15 cycle-close**: 9-item queue ALL DONE. No carry-over. Pick MTDS-handler coverage gaps + PBM-canonical-writer
> extensions.

#### Mechanical queue

- [ ] **1. MTDS handler coverage extensions — 3 handlers pickup** — pick 3 MTDS handlers below current coverage
      target (90%); add 4-6 tests per handler matching the shape of jitoSOL / bSOL / sanctumSOL Tier-1 pattern slot 9
      shipped 2026-05-15. Done-def: 3 handlers above 90% + MTDS QG green.
- [ ] **2. PBM canonical_writer extension — MDPS-side parametrized archetype dispatch hardening** — slot 9 shipped
      `mdps@4ad6060` (25 tests, 3 classes) on 2026-05-15. Identify 1-2 gaps surfaced during that work (any "fall-through
      contract" residuals); add 3-5 tests. Done-def: gap closed + PBM QG green.
- [x] ✅ **3. solana_lst_native_staking_adapters_2026_05_14 final item (95%, 21/22)** — 1 checkbox left. Plan path:
      [`solana_lst_native_staking_adapters_2026_05_14.md`](solana_lst_native_staking_adapters_2026_05_14.md). Close
      out. (deployment-service@ea1356b — launchers + watchdog prefixes; plan now 22/22 100%)

#### Reserve queue

- [ ] **4. solana_restaking_rewards_coverage_2026_05_13 final items (89%, 16/18)** — 2 checkboxes left. Plan path:
      [`solana_restaking_rewards_coverage_2026_05_13.md`](solana_restaking_rewards_coverage_2026_05_13.md). Close out.
- [ ] **5. MTDS lst_rates handler — ezETH/RENZO multi-call architecture gap** — slot 9 noted on 2026-05-15: ezETH
      requires 2-contract call (RestakeManager.calculateTVLs); single-call `_query_rate` does not support. Either
      (a) implement multi-call support, OR (b) file deferral with `EXPECTED_VENDOR_SOURCE_LIMITATION` reason. P3 —
      pick if reserve time.

#### Coordination

- **Owned repos**: MTDS + PBM + MDPS (canonical writer).
- **No cross-side handshakes**.
- **Conflict-risk**: MTDS = slot 6 item 3 (expected_unattempted wiring). Coordinate via ping.

---

## Top-priority items for 2026-05-18 (cross-slot)

| # | Item                                                              | Slot(s)              | Why                                                                                |
| - | ----------------------------------------------------------------- | -------------------- | ---------------------------------------------------------------------------------- |
| 1 | execution-service Phase B batches 98-105 continuation             | slot 2               | Highest-throughput mechanical sweep; clears May-23 lint gate                       |
| 2 | Cycle-close deferrals items 12-15 (slot 4) + items 2-9 (slot 6)   | slot 4 + slot 6      | Backlog from 2026-05-15; routes to ZERO if not picked up today                     |
| 3 | features-service Wave 59+ coverage continuation                   | slot 4 reserve       | Pre-Cycle-3 paper-trade smoke prep                                                 |
| 4 | Near-done plan close-outs (defi_simulation_realism 98%, etc.)     | slots 3, 5, 7, 9     | Master plan % done lift                                                            |
| 5 | Deployment-api/UI Phase 2F + auto-launch final items              | slot 7               | Closes 2 plans from 80-93% to 100%                                                 |
| 6 | MTDS + PBM coverage extension                                     | slot 9               | Continues 2026-05-15 momentum                                                      |

## Operator-action items pending (NOT on Harsh slots — for awareness only)

- 🔴 **Cycle 2 Day-3 cutover execution** — write-pause + 36-consumer delegate-flip (Ikenna slot 1 + slot 3 OWN today)
- 🔴 **B-015 paper VM monitoring** — dedicated agent owns
- 🟡 **AWS migration Phase 4-5** — Ikenna side
- 🟡 **Custody Phase 4-5** (Copper KYB closure + Fireblocks integration) — Ikenna side, depends on operator R9 gate
- 🟡 **Code-freeze Phase 2 cutover-runbook** — Ikenna side
- 🟡 **api_keys_wallets Phase 4-5** — Ikenna side, depends on operator credential asks

## Spawn prompt — paste into each tab (slot N)

```
You are slot N of harsh-side parallel agents for 2026-05-18.

READ FIRST (in order):
1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md
2. unified-trading-pm/plans/active/work_split_2026_05_18_harsh.md § "Slot N"
3. unified-trading-pm/cursor-configs/CLAUDE.md § "Daily Work-Split Process"

YOUR THEME: <as listed in work_split_2026_05_18_harsh.md § Slot N>

WORKFLOW:
- Each item: ship + commit + push + flip plan checkbox in SAME agent turn.
- Format flip commit: `docs(plans): flip slot-N item-X — <repo>@<sha> + <evidence>`
- Ping STARTED + per-item DONE in harsh_orchestrator/pings/slot_N.md
- Conflict rules at top of work_split — verify ownership before touching cross-slot surfaces.

NOT YOUR JOB TODAY:
- Cycle 2 Day-3 cutover (Ikenna side).
- B-015 VM monitoring (dedicated agent).
- AWS migration / custody / api_keys / code-freeze sequencing (Ikenna side).
- Cross-side coordination — file ping in plans/active/_agent_pings.md if a finding is cross-side.

When primary queue done, work reserve queue. When reserve done, ping `[slot-N → main] — QUEUE EXHAUSTED`.
```

## Done-definition (2026-05-18 EOD)

- All slot 2 batches green + cumulative count updated in slot_2.md.
- Slot 4 items 1-4 closed OR explicitly DEFERRED with successor.
- Slot 6 items 1-4 closed OR explicitly DEFERRED with successor.
- Slot 8 items 1-4 closed OR explicitly DEFERRED with successor.
- 4+ master-plan-inventory near-done plans flipped to 100% (defi_simulation_realism, deploy_missing_auto_launch,
  data_status_ui_phase_2f, mock_data_pipeline_benchmarking, solana_lst_native_staking_adapters, defi_basedpyright_features_service).
- 0 cross-side coordination from Harsh-main today (Ikenna side owns Cycle 2 Day-3).
- Master plan inventory regenerated EOD.
- Deferred-work scoreboard at session end (per CLAUDE.md Half-3 rule).

## Composes with

- [`post_freeze_roadmap_2026_05_16_to_05_23.md`](post_freeze_roadmap_2026_05_16_to_05_23.md) — Cycle 2 Day-3 anchor.
- [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) — readiness rollup.
- [`continuation_prompts_harsh_2026_05_15.md`](continuation_prompts_harsh_2026_05_15.md) — source of deferred items.
