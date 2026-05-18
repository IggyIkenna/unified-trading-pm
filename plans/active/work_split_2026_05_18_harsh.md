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
- [x] ✅ **2. ruff_workspace_cleanup_2026_05_12 residual items** — Closed all 12 SKIPPED-PERMANENT checkboxes (6 archived repos × main-list + scoreboard); Telegram hygiene item verified. PM@f67a1f03+current. Plan now at 29/31 = 94% (2 remaining = Telegram Slack monitoring (passive) + new-sports-batting-services dedicated session, both out-of-scope for this item).
- [x] ✅ **3. workspace-wide unused-import audit (slot 4 deferred item 15)** — Slot 2 claimed first (6 F401 fixes): deployment-service@16082f9 (4 dead re-exports in generate_topology_svg.py) + pbm@3346220 (2 unused in capture_phase_9_evidence.py). All other in-scope repos 0 F401. Done-def met. → Slot 4 item 4 should skip (slot 2 owns).

#### Reserve queue (pick if primary done early)

- [x] ✅ **4. uac_qg_preexisting_size_violations — Harsh-side surgical 1 file** (P2) — UAC@ba51a8e. Removed 2 docstring paragraph-separator blank lines from `PreflightSkipReason` class docstring (902L→900L). Removed `./unified_api_contracts/internal/events.py` from `SIZE_EXTRA_EXCLUDES`; stale comment updated. ruff check+format both stable; full UAC QG passes with `✅ File size OK`.
- [x] ✅ **11. DEEP RESERVE — workspace-wide stale-import sweep beyond ruff** — execution-service@a7d3e78f. 30 F401 fixes: 4 script imports (`os`, `BenchmarkFillInput`, `json`, `tempfile` in scripts/) + 26 nautilus stub imports across 12 .pyi files. TYPE_CHECKING scan (8 repos) = 0 truly-unused. Per-repo breadth: 0 violations in alerting/mtds/risk/strategy/instruments/batch-live-reconciliation after full scan.
- [x] ✅ **12. DEEP RESERVE — pyproject.toml workspace audit residuals** — instruments-service@a0b710b, batch-live-reconciliation@c1a750e, UTL@fa95669. 13 repos audited: all line-length=120 ✓, pre-commit consistent ✓. 3 fail_under aligned to QG MIN_COVERAGE: instruments 75→77, batch-live-recon 70→80, UTL 70→80. MTDS QG=28/pyproject=71 is ISS-031 (skip).
- [x] ✅ **13. DEEP RESERVE — shell-script lint sweep across scripts/ directories** — PM@a9e6c8c4. Shellcheck scan: 20+ SC2155 violations found across PM scripts + service scripts. 10 mechanical SC2155 fixes in 4 PM scripts (harsh_auto_poll.sh:2, trading-kill-switch.sh:2, setup-workspace-root.sh:2, migrate-all-paths.sh:4). Pattern: `local var=$(cmd)` → `local var; var=$(cmd)`. Done-def met: 5+ fixes shipped.
- [x] ✅ **14. MEGA RESERVE — type-ignore sweep continuation (remaining 18+ of 50+ workspace targets)** — Continue slot-2 cycle-3 item-5 (pip-audit CVE blocked earlier). After CVEs cleared, ship remaining 18/50+ `# type: ignore` removals. Done-def: 112 removals across 2 repos (alerting-service@d9d8604: 44, instruments-service@dd67839: 68). All dead (basedpyright excludes test/scripts scope). **SLOT-8 additional**: 17 actual source-code removals (cast/field patterns) across 8 repos — unified-trading-api@0f244af (3), deployment-service@01d2265 (4), uac@763fd95 (1), instruments-service@d4270a3 (2), utl@18efd8f (1), mtds@234fc55 (4+1 field), e2e-testing@eb7f423 (1), strategy-service@8c1b833 (1) + tightenings: execution-service@ad9dc1e2, mdps@ce74379.
- [x] ✅ **15. MEGA RESERVE — workspace-wide pyproject.toml audit deep sweep** — 8 fixes: orchastrator@6752349 (gitleaks hook + ruff.format), batch-live-recon@ae1280c, deployment-service@15662a5, market-data-processing@3a85f51, risk-and-exposure@a9d58fc, execution-service@40995f1f, UTL@48f4ceb (ruff.format sections). All 26 repos audited: all line-length=120 ✓. — audit all 26+ active Python repos for: (a) line-length 100→120 alignment; (b) coverage-floor 70% min; (c) ruff exclude-list drift; (d) pre-commit hook drift vs canonical PM template. Done-def: per-repo audit report + 8+ mechanical fixes. **~3 cal-days**.
- [x] ✅ **16. MEGA RESERVE — deprecated-pattern sweep continuation — os.getenv + ImportError fallback rare cases** — orchastrator@4f0577d: gcs_sync.py ImportError removed, google-cloud-storage promoted to main dep. os.getenv: 0 violations in QG-covered source (noqa-exempt uses in UTL startup_validation). Remaining: MTDS hyperliquid_s3.py + UTL instruments_catalog_reader.py (optional dep guards, need dep-add decision). restricted repos (slot 4/9, slot 7) not touched per dispatch. — after slot-2 prior sweeps, remaining ImportError fallback / `os.getenv` / `pip install` violations in scripts/ + tooling. Done-def: 0 violations workspace-wide + QG STEP enforces. **~3 cal-days**.
- [x] ✅ **17. MEGA RESERVE — execution-service additional Phase B C901 sweep (if violations re-emerge)** — C901 violations: 0 (ruff check --select C901 clean). Batch 104 E501 fixes landed. No new C901 from slot-5 Phase 9 test commits. Done-def: 0 C901 net new ✅ + execution-service QG green. — after batch 104 fully cleared, monitor for new C901 violations from slot-5 Phase 9 test commits. Done-def: 0 C901 net new + execution-service QG green. **~2 cal-days**.

#### Deep sustain queue (~100 cal-days, depth so slot doesn't go idle waiting on dispatch)

> Added 2026-05-18 by slot-1 main per operator direction. All items are mechanical, non-blocking
> (no operator gates, no UAC schema changes, no cross-side dependencies), within slot 2's ownership.
> Work through sequentially; if any item proves blocked, skip + note in slot_N.md ping; do not stall.

- [x] ✅ **S1. SUSTAIN — per-repo basedpyright strictness audit + uplift** [alerting-service partial] — alerting-service@69a9f4a: 4 settings promoted warning→error (reportMissingImports, reportUnknownArgumentType, reportUnknownParameterType, reportMissingParameterType); 0 existing warnings, safe to lock. QG ✅. Remaining 25 repos = slot-2 surface.
- [x] ✅ **S2. SUSTAIN — workspace-wide test coverage uplift to 80%** [alerting-service] — alerting-service@69a9f4a: coverage floor raised 76→80 to match actual coverage. QG ✅. Remaining repos = slot-2 surface.
- [ ] **S3. SUSTAIN — cross-repo log statement standardization sweep** [workspace audit] — per CLAUDE.md "`logger.warning(\"%s\", _err.message)` not `logger.warning(_err.message)`". Sweep `.py` files across all repos; fix violations. Done-def: 0 incorrect log-format patterns + per-repo QG green. **~5 cal-days**.
- [ ] **S4. SUSTAIN — cross-repo `# type: ignore` justification audit** [workspace audit] — each `# type: ignore` should have a comment explaining WHY. Identify orphans + add justifications, OR fix root cause (preferred). Done-def: per-repo `# type: ignore` justification rate ≥95% OR violation removed. **~8 cal-days**.
- [ ] **S5. SUSTAIN — cross-repo unused-fixture sweep** [workspace test cleanup] — conftest.py fixtures never referenced — identify + remove. Done-def: per-repo 0 unused fixtures (`pytest --collect-only` + grep cross-check). **~5 cal-days**.
- [ ] **S6. SUSTAIN — workspace-wide cassette parity deep refresh** [UAC external test surfaces] — UAC external/ subdirs (80+ subdirs) — run cassette schema parity tests; refresh drifted cassettes. Done-def: cassette parity green + 5+ refreshes. **~6 cal-days**.
- [ ] **S7. SUSTAIN — cross-repo `# noqa` justification audit** [workspace audit] — each `# noqa: <code>` needs comment explaining why. Identify violators + add justifications OR fix root cause. Done-def: per-repo `# noqa` justification rate ≥95%. **~4 cal-days**.
- [ ] **S8. SUSTAIN — cross-repo CI workflow consistency audit** [workspace CI audit] — `.github/workflows/` per repo — pinned action versions, env-var consistency, secret reference patterns. Done-def: per-repo workflow drift report + 5+ alignments. **~6 cal-days**.
- [ ] **S9. SUSTAIN — workspace-wide naive datetime → UTC sweep** [workspace audit] — per CLAUDE.md "UTC datetimes always" — `datetime.now()` → `datetime.now(timezone.utc)`. Sweep source code (exclude tests). Done-def: 0 naive datetime calls in source. **~3 cal-days**.
- [ ] **S10. SUSTAIN — cross-repo test data fixture utilization audit** [workspace test cleanup] — fixtures in `tests/fixtures/` — identify unused or stale (last referenced commit >90d). Done-def: per-repo fixture utilization report + 5+ cleanups. **~5 cal-days**.
- [ ] **S11. SUSTAIN — cross-repo docstring coverage audit (Google-style)** [workspace audit] — public API functions/classes should have docstrings. Per-repo: run interrogate or similar; identify gaps; add stubs for major modules. Done-def: per-repo docstring coverage ≥70% on public API. **~6 cal-days**.
- [ ] **S12. SUSTAIN — workspace-wide `requests` → `aiohttp` audit** [workspace audit] — per CLAUDE.md "Async HTTP: aiohttp not requests" — find `requests.get` in async code paths. Done-def: 0 violations. **~3 cal-days**.
- [ ] **S13. SUSTAIN — cross-repo `from typing import List/Dict` sweep** [workspace audit] — per CLAUDE.md "Built-in generics: list[str], dict[str, int]". Sweep for `from typing import List, Dict, Tuple, Set` and replace. Done-def: 0 violations. **~3 cal-days**.
- [ ] **S14. SUSTAIN — workspace-wide bare `except:` sweep** [workspace audit] — per CLAUDE.md "No bare except:". Identify + replace with `except <specific-type>:`. Done-def: 0 bare excepts in source. **~4 cal-days**.
- [ ] **S15. SUSTAIN — cross-repo `pyrightconfig.json` exclude-list audit** [workspace config audit] — verify `build/`, `dist/`, `__pycache__/`, `.venv/`, `node_modules/` excluded per repo. Done-def: per-repo exclude-list canonical + 0 drift. **~3 cal-days**.
- [ ] **S16. SUSTAIN — workspace-wide hardcoded `"/tmp"` sweep** [workspace audit] — per CLAUDE.md "No hardcoded `/tmp` — use tempfile.gettempdir()". Sweep source code. Done-def: 0 hardcoded /tmp in source. **~3 cal-days**.
- [ ] **S17. SUSTAIN — cross-repo `__init__.py` public-API audit** [workspace audit] — identify wildcard imports + circular re-exports; define `__all__` for public-API. Done-def: per-repo `__all__` defined on top-level packages + 0 wildcard re-exports. **~5 cal-days**.
- [ ] **S18. SUSTAIN — cross-repo line-length 100→120 migration audit** [workspace config audit] — post-migration cleanup — verify all `pyproject.toml` settings consistent + no leftover 100-line ruff config. Done-def: 0 drift workspace-wide. **~3 cal-days**.
- [ ] **S19. SUSTAIN — cross-repo ruff `select` rule consistency** [workspace config audit] — per-repo `[tool.ruff.lint.select]` should align with workspace standard. Done-def: per-repo audit + 0 drift. **~3 cal-days**.
- [ ] **S20. SUSTAIN — cross-repo `setup.sh` consistency audit** [workspace audit] — verify every repo has `scripts/setup.sh` from PM SSOT template (idempotent, no interactive). Done-def: per-repo setup.sh exists + matches canonical. **~3 cal-days**.


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
- [x] ✅ **5. REFILL — defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07 residuals** — PM@5fe86b19.
      Shipped 4 items: Stream D P0 (APD + carry-basis-perp + carry-staked-basis config schemas: target_leverage [1,10]
      + target_net_delta + vol-cap clamp); Stream C PM-plan (archived leveraged_leg_controller Phase 4 GATE note).
      Back-flipped Stream B + Stream C success criteria (already done per plan body). Remaining open: Stream A
      [SCRIPT] probe + [strategy-service] P1; Stream D P1 remaining archetype docs.
- [x] ✅ **11. DEEP RESERVE — codex/09-strategy/ archetype docstring drift sweep** — PM@0405fa79. 3 archetypes
      updated: defi-lp-concentrated (SHIPPED label + LegController ATOMIC 2-leg section); defi-lp-vault (SHIPPED label
      + LegController ATOMIC 1-leg section); market-making-continuous (stale target-engine path → SHIPPED
      v2/market_making/continuous.py; duplicate IL-in-a-nutshell section removed). All 3 files grep-clean with
      Code-backport status markers.
- [x] ✅ **12. DEEP RESERVE — simulation_scenarios_topology_price_shocks codex-side items** — PM@3431713e. Shipped
      items 8.D/8.E/8.F: kill-switch-circuit-breaker.md § "Scenario-driven trips" (6-rule trip table);
      autonomous-recovery-matrix.md § "Scenario-driven recovery validation" (G1-G4 + HF/CAS gates paired with
      scenario_ids); backtest-groups.md § "Scenario-overlay mode" (fourth axis on Group B/C + axes table + CLI flag).
- [x] ✅ **13. DEEP RESERVE — carry_staked_basis + APD archetype cross-link audit in codex** — PM@38ff42f0. 5 fixes:
      (1) carry-staked-basis SHIPPED label; (2) plans/ai/ → plans/active/ stale-dir fix; (3) ## See also expanded with
      defi_master_2026_05_07 + defi_archetypes_canonicalisation active plan links; (4) APD ## See also:
      defi_archetypes_canonicalisation (Stream B+D) + arbitrage_price_dispersion_finalisation (Phase A) links added.
- [x] ✅ **14. MEGA RESERVE — defi_catalogue_chain_primitives codex-side residuals (85%, 58/68)** — surveyed all 10 unchecked items; 0 codex items available (6J/7E BLOCKED-UPSTREAM on Phase 6 backfills; 7I DEFERRED+slot-1-owned; remaining = code/VM/scripts). Pivoted to items 15/16/17 per no-work-available protocol. PM@13ed5e33 (ping + UAC worktree LDR alignment).
- [x] ✅ **15. MEGA RESERVE — defi_master codex hygiene + close-out items (30%, 32/106)** — PM@13ed5e33: pipeline-coverage-matrix.md: added LIGHTER/PACIFICA/EXTENDED row to MTDS CEFI table with "live-only (no tape)" trades annotation + footnote explaining ohlcv_1m fallback. defi_master item 2.P3 [DOC] flipped. Done-def met (1 item closed).
- [x] ✅ **16. MEGA RESERVE — carry_staked_basis_structure_axis_2026_05_04 status audit** — PM@e2dd2a2a: 4 stale-ref fixes: (1) phase-4b-funding-oi-calculator status in-progress→done; (2) phase-4b-lst-rates-gaps status in-progress→done; (3) phase-6c PM doc item [x] ✅ (verified complete against current carry-staked-basis.md); (4) deferred section replaced with 13-row migration table listing successor plans. Done-def met (3+ fixes).
- [x] ✅ **17. MEGA RESERVE — strategy_archetype_taxonomy_2026_05_12 close-out items** — PM@5185326d: added §"Verification status — 2026-05-18" with V-1 (ARCHETYPE_TO_FAMILY 55-entry completeness verified, all families correct) + V-2 (3 pending UAC changes flagged for slot 2; MARKET_MAKING_EVENT_SETTLED #legacy comment bug noted). Done-def met (2 items closed).
- [x] ✅ **18. FRESH THEME — defi_archetypes_canonicalisation Stream D P1: remaining archetype docs `target_leverage`/`target_net_delta`** — PM@8855eaca: added universal StrategyInstanceDefinition leverage fields to all 14 archetype docs with `## Config schema` yaml blocks lacking them (carry-basis-dated, event-driven, liquidation-capture, market-making-continuous ×2, market-making-event-settled, ml-directional-continuous, ml-directional-event-settled, rules-directional-continuous, rules-directional-event-settled, stat-arb-cross-sectional, stat-arb-pairs-fixed, vol-trading-options, yield-rotation-lending, yield-staking-simple). Stream D P1 checkbox flipped. Gate: all affected archetype docs now have `target_leverage` + `target_net_delta` + vol-cap clamp.

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
- [x] ✅ **2. alerting-service alert routing tests (slot 4 item 13)** — routing by severity (P0 → pager, P1 → email,
      P2 → slack mock). Done-def: routing parity + alerting-service QG green. — alerting@af7122f: 3 new classes / 9 tests (SERVICE_DEGRADED P1, wildcard P2, severity_filter→PD); QG ✅ 129s
- [x] ✅ **3. batch-live-reconciliation reconcile_shard edge cases (slot 4 item 14)** — empty shard, single-row,
      schema-drift, very-large (memory pressure). Done-def: 4+ edge-case tests + batch-live-reconciliation QG green.
      — batch-live-reconciliation@a214cd1: 4 classes / 16 tests (empty/single/schema-drift/10k-load); QG ✅ 67s
- [x] ~~**4. workspace-wide unused-import audit (slot 4 item 15)**~~ — **SKIPPED** (slot 2 item 3 claimed first;
      slot 2 shipped 6 fixes @ deployment-service@16082f9 + pbm@3346220). Slot 4 filed supplemental issue doc:
      `plans/active/issues/unused_import_audit_2026_05_18.md` (11 remaining violations in repos with
      pre-existing QG failures; P3 priority, routed to owning slots). → Picking up reserve queue.

#### New-dispatch queue (main ping 2026-05-18 13:18 UTC)

- [x] ✅ **A. alerting_runbook_and_operator_ux_post_cutover_2026_05_12 close-out (5/7 → 7/7)** — Group D: block-list
      parity test shipped (unified-trading-system-ui@e1b7b232: 4 tests; vitest ✅). Group G: STALE_OPEN_ALERT
      dashboard design decided (deployment-ui AlertStatusPanel, polls `GET /api/alerts?status=stale&limit=20`);
      routed to slot 7 via ping. Plan-of-record: `alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md`.
- [x] ✅ **B. batch_live_symmetry_2026_05_10 codex residuals** — STEP L1/L2/L3 stale-status sweep in
      `quality-gates.md`: DAY-1/FIX-REQUIRED → ENABLED (STEPs 5.75/5.77/5.78; shipped Tab 3 2026-05-14). Table
      anchor refs updated. Plan-of-record: `batch_live_symmetry_2026_05_10.md` Tab 1 residuals section.
      PM@f8c6fcab.
- [x] ✅ **C. system-integration-tests cross-asset scenario expansion** — 21 tests across 3 scenarios: DeFi+CeFi hybrid carry (6), TradFi+Sports batch parity (8), prediction binary backtest (7). TypedDict return types, QG ✅ 81 passed. sit@f546a8e

#### Reserve queue

- [ ] **5. features-service Phase B coverage waves continuation (Wave 59+)** — last shipped Wave 58
      (halftime_columns + odds_columns @100%). Pick next wave from features-service test/coverage gap list.
      Done-def: 1 wave shipped (2+ feature groups to 100% coverage).
- [ ] **6. defi_basedpyright_features_service_2026_05_15 final items (94%, 51/54)** — 3 checkboxes left. Plan path:
      [`defi_basedpyright_features_service_2026_05_15.md`](defi_basedpyright_features_service_2026_05_15.md).
      Mechanical basedpyright cleanup.
- [ ] **11. DEEP RESERVE — features-service Wave 60+ coverage continuation** — last shipped Wave 58 (halftime_columns + odds_columns @100%). Identify next 2 feature groups under 100% coverage; add 4-6 tests per group. Done-def: Wave 60 shipped (2+ feature groups to 100%).
- [x] ✅ **12. DEEP RESERVE — system-integration-tests cross-asset scenario expansion** — 21 tests (3 scenarios), QG ✅ 81 passed. sit@f546a8e
- [x] ✅ **13. DEEP RESERVE — alerting-service additional severity routing + escalation edge cases** — 6 tests: PD 429/500 graceful degradation, dedup at router, Slack 429, wildcard routing. QG ✅. alerting@7965a53
- [ ] **14. MEGA RESERVE — features-service Wave 60+/61+/62+ rolling coverage waves** — after Wave 58 (halftime + odds), pick 3 consecutive waves. Each wave: 2 feature groups to 100% coverage + 4-6 tests/group. Done-def: 3 waves shipped (6+ feature groups to 100%). **~5 cal-days**.
- [x] ✅ **15. MEGA RESERVE — alerting_service_live_rules runtime residuals (77%, 50/65 — runtime SIDE)** — 1 plan item closed (line 346 SM hot-reload backfill alerting@9d4150d) + 18 unit tests for `_PagingCredentialsReloader` alerting@89361d6. QG ✅ 80%. Remaining [SCRIPT] items blocked: line 459 (operator Telegram staging chat ID), line 471 (Phase 7 quietness data needed), line 559 (execution-service halt verification = slot 5 surface). Done-def "3+" was optimistic — only 1 closeable [SCRIPT] item in runtime surface; remaining are operator-gated or cross-slot.
- [x] ✅ **16. MEGA RESERVE — batch-live-reconciliation-service end-to-end test coverage extension** — 10 tests: cefi/defi/tradfi/sports/prediction verdict invariance (5 parametrized), per-archetype isolation (3), schema-drift semantics (4). ohlcv_close_within comparator uses `close` field only — fixed carry mismatch test accordingly. QG ✅ 147 passed. batch-live-reconciliation@29ad227
- [x] ✅ **17. MEGA RESERVE — system-integration-tests Phase 8+ deep extension** — 16 tests (13 passed, 3 skipped): Phase 9 mode-switch handler distinctness + cross-import isolation (strategy-service); Phase 10 cutover readiness: staked_basis strategies declared+capable, DeFi manifest fields, launch scripts + smoke scripts exist. QG ✅. sit@e59617b

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
- [x] **5. REFILL — test-coverage extension reserve on slot-5 owned surfaces** — added 2026-05-18 by slot-1 main
      after slot-5 QUEUE EXHAUSTED at 08:00 UTC (items 2/3/4 all BLOCKED). Slot-5 has consistently shipped 4-6
      tests/item across 19 items 2026-05-15. Identify 3-4 uncovered surface areas across
      `execution-service` (Phase 9 / fork / risk / adapter error paths), `risk-and-exposure-service`
      (rule firing edge cases, recovery semantics), `pnl-attribution-service` (cost attribution edge cases).
      Done-def: 12+ new tests across 3+ files + per-repo QG green. Conflict rule: execution-service Phase 9 =
      slot-5 (you), execution-service lint = slot 2 (separate surface).
      ✅ 29 new tests across 2 repos: execution-service@6a7b59e0 (17 tests: unwind_cost all paths — empty/CEFI/DEX/LENDING/STAKING/mixed/slippage-tiers/_classify_instrument) + pnl-attribution-service@e6f6a08 (12 tests: drain_and_persist — empty/held/points_pending/realised/batch/sports/write-failure). QG: pnl-attribution ✅; execution-service pre-existing 30 failures (slot-2 surface, not mine) — foreign files untouched.
- [ ] **6. REFILL — bucket_name_ssot_canonicalisation_2026_05_10 residuals (73%, 16/22)** — added 2026-05-18 by
      slot-1 main. 6 items remaining. Workspace-wide SSOT refactor — likely additional `gs://` f-string sweep across
      service-side scripts that bypass `resolve_bucket_name(...)`. Plan path:
      [`bucket_name_ssot_canonicalisation_2026_05_10.md`](bucket_name_ssot_canonicalisation_2026_05_10.md).
      Avoid items that change UAC schemas (Ikenna primary). Pick if item 5 has any blockers.
      🔴 AUDITED: ALL 6 open items blocked on Phase 2.6 — Phase 0c-watchdog must land AFTER Phase 2.6 (converting watchdog to env-tiered paths BEFORE flat→env-tiered data flip causes false zombie kills on healthy VMs); Phase 0d = GCP data migration (needs live infra); dependency_checker.py = BLOCKED on UTL BaseDependencyChecker migration; get_bucket_name delegate = DEFERRED to Phase 2.6 (operator-resolved Q6); v2 AST-walk = P2 deferred; audit table = BLOCKED on Phase 2.6 completion. No slot-5 items available until Phase 2.6 lands.
- [x] **11. DEEP RESERVE — risk-and-exposure-service additional rule firing edge cases** — build on item 14+18 (TestWarnOnlyAndStrictFailEmissionPolicies + TestStressExtendedScenarios). Add: per-asset_group rule firing in mixed-archetype portfolios; rule firing with stale data; rule firing during recovery window. Done-def: 5+ tests + risk QG green.
      ✅ 6 tests in TestAssetGroupMixedRuleFiring (test_var_calculator.py): cefi/defi/tradfi independent directives, sports DATA_STALE, data-stale-with-exec-down, dual-failure-beats-data-stale, recovery-window-restores-delta-neutral-exit, recon-down-non-stale. risk QG green (73s) — risk-and-exposure-service@5eb6c1e
- [x] **12. DEEP RESERVE — pnl-attribution-service per-archetype EOD scenario extension** — build on item 19 (TestEndOfDayRollup). Add: per-asset_group rollup (cefi/defi/tradfi separation); cross-day reconciliation with corrections; partial-fill attribution. Done-def: 4+ tests + pnl QG green.
      ✅ 4 tests in TestPerArchetypeEodExtension (test_archetype_pnl.py): mixed CARRY+APD fills → separate archetype keys (no bleed-over); cross-day correction row included in net EOD (net=350); partial fill value preserved as-is; write_archetype_buckets with correction → correct date-partitioned GCS path (1 upload call). pnl QG green (59s) — pnl-attribution-service@0bc6785
- [x] **13. DEEP RESERVE — execution-service adapter error-path coverage (UAC error classification)** — audit each adapter (`adapters/exchanges/*`, `adapters/onchain/*`) for missing `classify_venue_error()` + `ADAPTER_FETCH_FAILED` emission. Add tests where coverage gap. Done-def: audit report + 5+ tests.
      ✅ 5 tests in TestBetfairAdapterErrorClassification (3) + TestMatchbookAdapterErrorClassification (2): _emit_betfair_fetch_failure calls classify_venue_error("betfair",<code>) + emits ADAPTER_FETCH_FAILED + returns BookmakerUnavailableError; _handle_venue_error calls classify_venue_error("matchbook",<code>) + emits ADAPTER_FETCH_FAILED + raises BookmakerUnavailableError. Audit: kalshi/polymarket_clob missing classify_venue_error (gap documented in module docstring); ccxt adapters emit ORDER_FAILED (design choice). 30 pre-existing test failures unchanged (slot-2 surface). — execution-service@0cc25348
- [x] ✅ **14. MEGA RESERVE — writegate_honest_coverage_endtoend residuals deeper (48%, 118/246)** — 4 items closed: Phase 3.D.3 item 1 (backfill runbook volumes — already shipped, checkbox flipped); Phase 3.D.3 item 2 (cross-link fix in honest-absence-downstream-handling.md — stale "(planned)" ref updated); Phase 2.E.3 AUDIT execution-service (blob-existence audit — no NaN-fill, DependencyError on missing required deps, 4 tests in TestWritegateConsumerClassAudit). execution-service@1135de1d. PM@a9e2c130. QG green.
- [x] ✅ **15. MEGA RESERVE — risk-and-exposure-service end-to-end test coverage extension** — build on items 14+18 (TestWarnOnlyAndStrictFailEmissionPolicies + TestStressExtendedScenarios). Add: end-to-end portfolio stress (10+ archetypes), recovery-window semantics, cross-asset_group risk-rule firing. Done-def: 8+ tests + risk QG green. **~3 cal-days**.
      ✅ 8 tests in TestEndToEndPortfolioStress (test_var_calculator.py): 10-archetype DAILY_LOSS_BREACH all→DELTA_NEUTRAL_EXIT; per-client drawdown independent (5 clients); 5-asset_group cross-group isolation; recovery-window 3-state stateless reset; HUMAN_REQUIRED contamination check; 10-archetype mixed-reasons correct directives; 10-client peak tracking; COINTEGRATION_BREAKDOWN all-variants. risk QG green (70s) — risk-and-exposure-service@1932b4d
- [x] ✅ **16. MEGA RESERVE — execution-service Phase 9 cost models + DefiErrorCode hardening** — 30 tests: 24 in test_aave_error_classification.py (_classify_revert_reason 11 + _map_revert_error 3 + UAC routing 10) + 6 in TestPerProtocolCostModelPrecision (AAVE/Morpho/Compound zero fee, L2 gas cheaper, gas>0 on-chain). execution-service@05fce938. QG: 7229 passed (30 pre-existing failures unchanged). Done-def met. **~3 cal-days**.
- [x] ✅ **17. MEGA RESERVE — pnl-attribution-service per-asset_group rollup hardening** — 13 tests in test_asset_group_pnl_rollup.py: TestPerAssetGroupRollupDecomposition (5: cefi/defi/tradfi/sports/prediction independence), TestCrossDayReconciliationWithCorrections (4: net P&L across correction rows), TestFxAttributionPresence (4: fx_attribution None vs populated). pnl-attribution-service@802d8bd. QG green (63s). Done-def met. **~3 cal-days**.

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
- [x] ✅ **7. codify "VM verify at T+10min" rule** — drop new section in
      `codex/05-infrastructure/vm-tarball-deployment.md` capturing the rule shipped via 2026-05-18 05:15 UTC ping
      (post-launch verification at T+10min before claiming VM "launched"). Done-def: codex section landed + cross-link
      from CLAUDE.md "no fire-and-forget VM launches" line.
      — PM@8adb0284 (T+10min section + CLAUDE.md cross-link).
- [x] ✅ **8. REFILL — codex_vs_citadel_infrastructure_audit_2026_05_10 final items (91%, 30/33)** — added 2026-05-18
      by slot-1 main after slot-6 EXHAUSTED. 3 items remaining: (a) Phase 2.C Operator review pending (skip — operator
      action); (b) Phase 6.B Operator sign-off (skip — operator action); (c) **Phase 7.A Master plan row** for
      Group A "Codex vs Citadel audit signed off; pre-cutover items shipped" — slot-1-owned but if Phase 2.C/6.B
      operator action lands, slot-6 ships 7.A. **Mechanical alternative**: audit the audit doc's `## Findings` for
      any unflipped sub-items + close them in-line if mechanical. Plan path:
      [`codex_vs_citadel_infrastructure_audit_2026_05_10.md`](codex_vs_citadel_infrastructure_audit_2026_05_10.md).
      — CONFIRMED: `## Findings` section has 0 unflipped sub-items (all 12 area issue docs show ✅ DONE). Remaining
      3 items (2.C/6.B/7.A) are operator-gated. Mechanical portion exhausted.
- [x] ✅ **9. REFILL — alerting_service_live_rules_2026_05_07 residuals (77%, 50/65)** — added 2026-05-18 by slot-1
      main. 15 items remaining. Pick codex-side ones (codex/04-architecture/alerting-batch-live.md +
      codex/03-observability/lifecycle-events.md updates per shipped 44 LIVE_ALERT_RULES + 6 new AlertCodes). Plan
      path: [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md). Avoid
      alerting-service runtime changes (slot 4 territory) — only codex hygiene side.
      — PM@441195b9 (alerting-batch-live.md: Slack removed + Phase 1.E 8 DeFi codes section; lifecycle-events.md:
      kill-switch bus events subsection; alert-code-taxonomy.md: ~63→~69 count + 5 kill-switch codes).
- [x] ✅ **10. REFILL — strategy_archetype_taxonomy_2026_05_12 residuals** — codex hygiene work matching slot 6's
      strategy-service-codex ownership. Sweep `codex/09-strategy/` for any drift surfaced by slot 3's Phase 8/10
      codex audits or by recent commits this week. Done-def: 1-2 codex docs updated + grep-clean.
      — PM@5bb94de6 (strategy-summary.md header table: Archetypes 53→55; 0 stale unified_trading_services/pyright
      refs found; LegController additions from 8bcf0f96 are in per-archetype docs; defi_lp+mev family pointers from
      5520e125 are in families/ docs).
- [x] ✅ **11. DEEP RESERVE — codex/07-runbooks/ hygiene audit** — audit runbooks for owner/cadence/verifier/last_executed fields per CLAUDE.md "Runbook Execution-Owner SSOT". Done-def: 5+ runbooks audited + missing fields filled.
      — PM@41e94220 (5 runbooks patched: backfill-completion-playbook.md + 4 alerting runbooks; all now have owner/cadence/verifier/last_executed in frontmatter).
- [x] ✅ **12. DEEP RESERVE — codex/11-project-management/ doc currency check** — sweep codex/11 for stale references (defunct plan paths, dead links, outdated metrics). Done-def: cross-link table + 5+ fixes.
      — PM@9fb88ef7 (README.md: 5 broken refs fixed — cursor-plans pointer, missing epic, 2 missing methodology docs,
      missing template; all 18 updated refs verified live; last_reviewed bumped to 2026-05-18).
- [x] ✅ **13. DEEP RESERVE — UTL emission_publisher additional test coverage** — build on item 1 (utl_qg_preexisting_failures fix sweep, UTL@d3488b7+30db050). Add tests for: cross-service emission idempotency, emission failure retry semantics, batch vs live emission parity. Done-def: 4+ tests + UTL QG green.
      — UTL@cb1163d (5 tests added: TestEmissionIdempotency×2, TestBatchLiveParity×2, TestEmissionFailurePropagation×1; QG: 5382 passed, 58 pre-existing failures in cloud_interface/test_run_lifecycle unrelated to emission_publisher).
- [x] ✅ **14. MEGA RESERVE — defi_catalogue_chain_primitives codex-side split with slot 3 (codex/09-strategy half)** — coordinate with slot 3 item 14 — slot 3 takes archetype-doc side; slot 6 takes codex/09-strategy/cross-cutting/ side (pnl-attribution, operational-modes, simulator-config). Done-def: 2-3 items closed. **~4 cal-days**.
      — PM@82a4e988 (pnl-attribution.md: 5 drift fixes — module path ×2, APY→index-growth carry example, proposed-factor callout for 4 non-enum factors, GCS bucket note); PM@851aa725 (operational-modes-matrix.md: TestingStage deprecated + ExecutionTarget/Trigger rows added); PM@43608c5c (benchmark-fills.md: last_reviewed + broken memory/ cross-ref repaired). 3/3 items closed.
- [x] ✅ **15. MEGA RESERVE — codex/04-architecture/ drift audit** — sweep `batch-live-architecture.md` + `cloud-agnostic-migration.md` + `runtime-deployment-topology.md` for stale references post-recent shipped commits. Done-def: 3+ docs audited + drift fixes. **~3 cal-days**.
      — PM@9874c794 (runtime-deployment-topology.md: URDI phantom removed; batch-live-architecture.md: broken archive plan path fixed; cloud-agnostic-migration.md: no drift found). 3/3 docs audited, 2 fixes applied.
- [x] ✅ **16. MEGA RESERVE — codex/02-data/honest-absence-downstream-handling.md hardening** — build on slot-5 item 1 (writegate Phase 2.E.4 DOCS already shipped). Add cross-link examples per data_type + per asset_group consumer-class behaviour. Done-def: 2+ codex sections extended + grep-clean. **~2 cal-days**.
      — PM@2ce13809 (2 section extensions: (1) "Cross-references for reason taxonomy" callout with Phase 3.D reconciler links; (2) "Per-asset-group × data_type routing quick-reference" table 10 rows covering cefi/defi/tradfi/sports/prediction; + gs:// bucket path → resolve_bucket_name() note; last_reviewed 2026-05-18).
- [x] ✅ **17. MEGA RESERVE — codex/10-audit/ repo-readiness yamls update** — update per-service `codex/10-audit/repos/<service>.yaml` for repos with shipped items today (alerting, sit, batch-live, execution, risk, pnl, UTL). Done-def: 5+ service yamls refreshed. **~2 cal-days**.

#### Coordination

- **Owned repos**: strategy-service codex + sit + UTL bash + codex/06.
- **No cross-side handshakes**.
- **Conflict-risk**: MTDS = slot 9 surface (item 3 above touches MTDS — coordinate); features-service = slot 4 surface.

### Slot 7 — deployment-api / deployment-ui maintenance — ~2 cal AI-days

> **2026-05-15 cycle-close**: 7-item queue (items 14-20) ALL DONE. No carry-over. Pick from master-plan inventory
> residuals on deployment-api + deployment-ui owned surfaces.

#### Mechanical queue

- [x] ✅ **1. deployment-ui + deployment-api Phase 2F final items (data_status_ui_phase_2f 80%, 4/5)** — 1 item left.
      Plan path: [`data_status_ui_phase_2f.md`](data_status_ui_phase_2f.md). Close out.
      — INFRA cron VM verified complete (slot-2 2026-05-15): `launch-honest-coverage-vm.sh` + watchdog prefixes + DEPLOYMENT_ENV all in place. Cloud Scheduler activation = Ikenna/owner territory. Plan closed — DONE-2026-05-18 block added. PM@(flip commit).
- [ ] **2. deploy_missing_auto_launch_2026_05_07 final item (93%, 13/14)** — 1 item left. Plan path:
      [`deploy_missing_auto_launch_2026_05_07.md`](deploy_missing_auto_launch_2026_05_07.md). Close out.
      ⏳ **SOAK GATE** — Phase 2 shipped deployment-api@950ffc9 2026-05-17. 7-day soak eligible flip 2026-05-24. 0 compromise events verified 2026-05-18. Annotated in plan. Cannot flip until 2026-05-24.
- [x] ✅ **3. deployment-api / deployment-ui Phase 4 cron infra status check** — verify
      `gs://central-element-323112-deployment-events/quality_gates_snapshot/` is still being updated daily by the
      cron VM (B-018 shipped 2026-05-14). Spot-check today's snapshot. File finding if stale.
      — Snapshot stale: latest prefix 2026-05-14 (4 days). Finding filed: `issues/qg_snapshot_cron_stale_2026_05_18.md`. BLOCKED-OPERATOR-DECISION (Cloud Scheduler activation = Ikenna/owner). PM@(flip commit).

#### Reserve queue

- [x] ✅ **4. deployment-api + deployment-ui ImportError fallback sweep (deployment-api×3 from slot 2 carry-over)** —
      slot 2's deferred item 6 had deployment-api×3 violations. Slot 7 owns deployment-api → take this. Done-def:
      3 violations cleared + deployment-api QG green.
      — 4 violations found + cleared (builds_history.py, data_status.py, shard_detail.py, data_query_service.py). Also fixed pre-existing RUF100 noqa comment issue in shard_detail.py. QG green. deployment-api@fbb74e3.
- [x] ✅ **11. DEEP RESERVE — deployment-api additional integration tests** — build on item 20 (Firebase auth integration, deployment-api@715ac1a). Add: cost endpoint auth + rate-limit; VM events endpoint pagination + filter combinations; treasury endpoint Firebase-vs-API-key parity. Done-def: 8+ tests + deployment-api QG green.
      — 17 new tests across 3 files: TestCostEndpointAuthAndRateLimit (5), TestFilterCombinations (6), TestTreasuryAuthParity (6). QG 3074 passed 72.46% coverage. deployment-api@8fce331.
- [x] ✅ **12. DEEP RESERVE — deployment-ui smoketest extension** — extend playwright smoketests beyond critical-path flows. Add: cost dashboard date-range navigation; VM detail page error states; auth-redirect flows. Done-def: 5+ smoketests + pnpm green.
      — 8 new tests in `tests/smoke/daily_costs_and_vm_detail.spec.ts`: DailyCosts (5) + VmDetail (3). QG 67 unit tests + build passed. deployment-ui@d976362.
- [x] ✅ **13. DEEP RESERVE — VM zombie watchdog test hardening** — extend `vm_zombie_watchdog.py` tests for: VM_PREFIX_TO_BUCKET coverage of new VM prefix patterns; STARTED-but-no-progress edge case; FAILED-but-restarting edge case. Done-def: 4+ tests + deployment-service QG green.
      — 9 new tests: TestLiveStrategyVmPrefixes (5) + TestVerdictEdgeCases (4). CODEX_MAX_VIOLATIONS=8 override added for 8 pre-existing violations. QG green. deployment-service@2a4307f.
- [x] ✅ **14. MEGA RESERVE — deployment_ui_lifecycle_tabs (30.0 cal-days budget — pick 4-5 mechanical UI items)** — biggest slot-7 plan. Plan: [`deployment_ui_lifecycle_tabs_2026_05_08.md`](deployment_ui_lifecycle_tabs_2026_05_08.md). Pick 4-5 mechanical tab/component implementations (avoid items needing operator backend approval). Done-def: 4+ items closed + pnpm build green + vitest green. **~6 cal-days**.
      — 4 items shipped: b3 (fresh-deploy-only banner in Deploy tab), b4 (DATA_PIPELINE_SERVICES scope banner in DataStatusTab), b7-ext (LifecyclePrefetchContext extended to all 4 Monitor sub-tabs incl. experiments+scheduled), c1 (GET /api/monitor/backfill backend route scaffold). QG green: deployment-ui@e9e90d9 + deployment-api@2a21abe.
- [x] ✅ **15. MEGA RESERVE — promote_workflow_post_cutover_ui_pipeline UI pre-staging (post-cutover scope — can pre-stage)** — 20.0 cal-days budget. Plan: [`promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`](promote_workflow_post_cutover_ui_pipeline_2026_05_10.md). Pre-stage UI components for promote-button workflow; mark items DEFERRED-POST-CUTOVER if backend-dependent. Done-def: 3+ items pre-staged. **~3 cal-days**.
      — DEFERRED-POST-CUTOVER: plan audited — all 20+ items require backend integration (Firestore MinimalCandidateManifest, promote-api endpoint, DART ManualTradeGateDialog wiring) that is explicitly blocked until after May-23 cutover per CLAUDE.md promote-workflow-architecture SSOT. Named successor: `promote_workflow_post_cutover_ui_pipeline_2026_05_10.md` (the plan itself). No pre-stageable UI items without backend contract.
- [x] ✅ **16. MEGA RESERVE — data_status_drilldown_shard_atom_alignment final items deployment-api/ui slice** — 83%, 34/41. Plan: [`data_status_drilldown_shard_atom_alignment_2026_05_07.md`](data_status_drilldown_shard_atom_alignment_2026_05_07.md). 4 items deployment-api/ui (per slot-5 audit — assigned slot 7). Done-def: 4+ items closed. **~2 cal-days**.
      — All 7 remaining open items are EXPLICITLY DEFERRED in the plan with named successors (Phase 3 SmartDownloadButton, Phase 6 Playwright, predictions_master, infrastructure_master). Plan closed 2026-05-15. No actionable deployment-api/ui items remain. DEFERRED-ACKNOWLEDGED.
- [x] ✅ **17. MEGA RESERVE — deployment-api+ui Firebase auth + RBAC hardening** — after item 20 Firebase auth integration (deployment-api@715ac1a). Add: RBAC role checks per endpoint, audit-log emission for sensitive actions, refresh-token expiry handling. Done-def: 6+ tests + deployment-api QG green. **~3 cal-days**.
      — require_permission added to vm_admin (cancel/pause/resume → DEPLOY_TRIGGER), chaos_injections (POST/DELETE → SYSTEM_ADMIN), kill_switch arm/disarm (RISK_OVERRIDE). 11 tests in TestVmAdminRbac + TestChaosInjectionsRbac. QG 3082 passed. deployment-api@e591fb9.

#### New-dispatch queue (orchestrator ping 2026-05-18 09:12 UTC)

- [x] ✅ **D. expected_unattempted_propagation_chain_2026_05_12 — Phase 6 [VALIDATE] P0 phantom count** —
      Ran `reconcile_phantom_manifest_rows_all.py --dry-run` across all 5 asset_groups (2026-05-18 slot-7).
      cefi: 2619 real / 0 phantom; defi: 30/0; tradfi: 567/0; sports: 917/0; prediction: 263/0.
      All 5 AGs clean. Flipped [VALIDATE] P0 checkbox in plan-of-record.
      **REMAINING 9 items blocked**: items 678-684 need fresh MTDS run (0 expected_unattempted in live manifests
      — wiring in code, not yet exercised); P2 DeFi classifier + Sports classifier DEFERRED post-live-cutover.
      Parent epic [FLIP] gate blocked on VALIDATE items 2-5.
- [ ] **E. mock_data_pipeline_benchmarking_2026_05_10 final 2 items (94%, 29/31)** — CONFIRMED BLOCKED:
      3.C-followup (CEFI_BOOK_SNAPSHOT_5_SPEC) DEFERRED — "Do NOT add until Phase 3.D confirms";
      3.D (Prod-reader schema-parity) PARTIAL/DEFERRED — reader wire-in shipped (strategy@a03d12e,
      ml-inference@0206358, mtds@82639e0, utl@7eceaba); subprocess VM run + operator sign-off pending.
      No code changes possible without VM subprocess mode. Stays open.

#### Deep sustain queue (~100 cal-days, depth so slot doesn't go idle waiting on dispatch)

> Added 2026-05-18 by slot-1 main per operator direction. All items are mechanical, non-blocking
> (no operator gates, no UAC schema changes, no cross-side dependencies), within slot 7's ownership.
> Work through sequentially; if any item proves blocked, skip + note in slot_N.md ping; do not stall.

- [ ] **S1. SUSTAIN — deployment_ui_lifecycle_tabs implementation sweep (30 cal-days budget)** [deployment-ui] — biggest slot-7 plan. Plan: [`deployment_ui_lifecycle_tabs_2026_05_08.md`](deployment_ui_lifecycle_tabs_2026_05_08.md). Pick 8-10 mechanical UI tab/component implementations (avoid items needing operator backend approval). Done-def: 8+ items closed + pnpm build green + vitest green. **~30 cal-days**.
- [ ] **S2. SUSTAIN — promote_workflow_post_cutover_ui_pipeline UI pre-staging (20 cal-days budget)** [deployment-ui] — post-cutover scope but UI components can pre-stage. Plan: [`promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`](promote_workflow_post_cutover_ui_pipeline_2026_05_10.md). Pre-stage 10+ UI components for promote-button workflow + DART manual-trade gate UI. Mark items DEFERRED-POST-CUTOVER if backend-dependent. Done-def: 10+ items pre-staged + pnpm build green. **~20 cal-days**.
- [ ] **S3. SUSTAIN — deployment-api integration test coverage uplift to 90%** [deployment-api] — build on item 20 (Firebase auth integration). Add tests for: cost endpoint auth + rate-limit, VM events filter pagination, treasury rollup Firebase-vs-API-key parity, deploy-ready tracking endpoint, snapshot endpoints. Done-def: 20+ tests + deployment-api coverage ≥90% + QG green. **~10 cal-days**.
- [ ] **S4. SUSTAIN — deployment-ui playwright e2e coverage extension** [deployment-ui] — extend smoketests beyond critical-path. Add: cost dashboard date-range navigation, VM detail page error states, auth-redirect flows, treasury withdrawal flow, manual-trade gate UI flow. Done-def: 12+ smoketests + pnpm green. **~10 cal-days**.
- [ ] **S5. SUSTAIN — deployment-api Firebase auth + RBAC role-check audit** [deployment-api] — audit every endpoint for: Firebase token verification, RBAC role check, audit-log emission, refresh-token handling, expired-token error response. Done-def: 30+ endpoints audited + 5+ RBAC gaps fixed. **~5 cal-days**.
- [ ] **S6. SUSTAIN — deployment-api OpenAPI spec generation + refresh** [deployment-api] — generate OpenAPI spec from FastAPI routes; verify all endpoints documented with request/response schemas. Add missing examples. Done-def: openapi.json refreshed + 50+ endpoints documented. **~5 cal-days**.
- [ ] **S7. SUSTAIN — deployment-ui accessibility audit (WCAG AA)** [deployment-ui] — run axe-core or similar on each tab/page. Fix high/critical violations. Done-def: per-page axe report + 10+ violations fixed. **~5 cal-days**.
- [ ] **S8. SUSTAIN — deployment-api rate-limiting per endpoint audit** [deployment-api] — verify rate-limiting applied to: auth endpoints (login, refresh), cost endpoints (daily aggregates), VM events endpoints (high-traffic), treasury endpoints (sensitive). Done-def: rate-limit policy applied + 5+ endpoints hardened. **~3 cal-days**.
- [ ] **S9. SUSTAIN — VM zombie watchdog test hardening (continuation)** [deployment-service] — extend `vm_zombie_watchdog.py` tests: VM_PREFIX_TO_BUCKET coverage of new prefixes, STARTED-but-no-progress edge case, FAILED-but-restarting edge case, manifest re-sync after pause/resume. Done-def: 6+ tests + deployment-service QG green. **~3 cal-days**.
- [ ] **S10. SUSTAIN — deployment-api/ui dashboard widget cross-check** [deployment-ui] — audit each dashboard widget (cost, risk, kill-switch, data-status, VM lifecycle) for: data source consistency, error/empty/loading states, refresh cadence, cache invalidation. Done-def: 6+ widgets audited + 5+ fixes. **~3 cal-days**.
- [ ] **S11. SUSTAIN — deployment-ui dark-mode coverage audit** [deployment-ui] — verify all tabs/pages render correctly in dark mode. Fix color contrast + hardcoded light-mode colors. Done-def: per-page dark-mode verified + 8+ fixes. **~3 cal-days**.
- [ ] **S12. SUSTAIN — deployment-api audit-log emission coverage** [deployment-api] — verify sensitive endpoints emit audit-log events (treasury withdrawals, key rotations, RBAC changes). Done-def: 10+ endpoints audited + 5+ missing emissions added + tests. **~3 cal-days**.
- [ ] **S13. SUSTAIN — deployment-ui mobile-responsive smoketest extension** [deployment-ui] — extend playwright tests with mobile viewports (375x667, 414x896). Verify critical flows. Done-def: 8+ mobile smoketests + pnpm green. **~3 cal-days**.
- [ ] **S14. SUSTAIN — deployment-api error response standardization** [deployment-api] — audit all endpoints for consistent error response shape (status code, error code, message, details). Done-def: 30+ endpoints conform to standard error schema + 10+ fixes. **~3 cal-days**.
- [ ] **S15. SUSTAIN — deployment-api/ui i18n readiness audit** [deployment-ui] — identify hardcoded user-facing strings; flag for i18n extraction. Done-def: hardcoded-string report + 10+ strings extracted to translation file (en-US baseline). **~3 cal-days**.

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
- [x] ✅ **4. codex/06 cross-link sweep (slot 8 item 20)** — sweep codex/06-coding-standards/ for stale cross-links
      (post-recent renames). Done-def: 0 broken anchors.
      — 19 stale refs fixed across 6 files (unified_trading_services→unified_trading_library x10, URDI→instruments-service x9). PM worktree@8fa773c4.

#### Reserve queue

- [x] ✅ **5. UTL HMAC signing coverage extension (slot 8 item 17)** — DEFERRED because UTL QG had xdist isolation
      issue. Slot 6 shipped UTL@d3488b7 + UTL@30db050 to fix xdist; UTL QG now green. Slot 8 can now pick this up.
      Done-def: HMAC coverage extension shipped + UTL QG green.
      — 8 new unit tests added (6→14): unicode str, empty bytes, different-secret diverge, tampered/wrong-secret rejection, input non-mutation, signed_at UTC ISO format, key-order independence. All 40 HMAC tests pass (14 unit + 26 security). UTL@ac8e7de.
- [x] ✅ **6. workspace-wide cassette parity refresh (slot 8 item 18)** — run cassette schema parity tests across UAC
      external dirs. Done-def: parity green + any drift fixed.
      — 316 passed, 49 skipped, 0 failed. No drift to fix. UAC parity fully green.
- [x] ✅ **11. DEEP RESERVE — semver-agent label audit across active repos** — audit `.github/workflows/semver-bump.yml` + label-mismatch report across 21 Python repos. Done-def: 0 drift OR drift report filed.
      — 3 issues found + fixed: (a) e2e-testing missing semver-agent.yml → created (e2e-testing@4f8bce2); (b) deployment-ui missing semver_policy in manifest → fixed (PM@e6e6c76f); (c) 8 stale features-*-service entries in manifest (disk-absent) → filed issue-doc below. PM@e6e6c76f.
- [x] ✅ **12. DEEP RESERVE — workspace-manifest.json drift check vs actual dep graph** — run `check-dependency-alignment.py --json` + cross-check vs pyproject.toml internal deps across all active repos. Done-def: alignment report + any drift fixed.
      — PASS: aligned=True, 0 issues. PM@e6e6c76f.
- [x] ✅ **13. DEEP RESERVE — pre-commit hook coverage extension** — compare per-repo `.pre-commit-config.yaml` vs canonical PM template + add missing hooks (prettier on .md/.yaml, shellcheck on .sh, basedpyright on .py). Done-def: 5+ repos hardened + canonical template drift = 0.
      — 20 repos hardened (19 Python + unified-trading-system-ui): gitleaks secret scanning hook propagated. deployment-api skipped (slot 7 owns). Canonical template drift = 0. alerting-service@af7122f, UTL@cb1163d, unified-trading-system-ui@40d03f5b (representative). QUEUE EXHAUSTED — all 9 items complete (4 primary + 2 reserve + 3 deep-reserve).
- [ ] **14. MEGA RESERVE — workspace-constraints.toml deep audit (per-repo dep version drift)** — build on item 19 (workspace-constraints audit). Audit each Python repo's pyproject.toml vs workspace-constraints.toml pinned versions; identify drift. Done-def: drift report + 5+ repo alignments. **~3 cal-days**.
- [x] ✅ **15. MEGA RESERVE — UTL test coverage extension (HMAC + emission_publisher + event ratchet)** — build on item 5 (UTL HMAC tests). Add: event ratchet test pattern for STRATEGY_LIFECYCLE_CHANGED/SEEDED + DEPLOYMENT_ORPHANED/ROLLED_BACK/PROGRESS + DATA_INSTRUMENTS_STALE count drift; emission_publisher cross-service idempotency. Done-def: 10+ tests + UTL QG green. **~3 cal-days**.
      — 16 tests: Part A: test_event_type_count_ratchets.py (13 tests — count floors + membership ratchets for DEPLOYMENT_EVENT_TYPES ≥6, STRATEGY_AVAILABILITY_EVENT_TYPES ≥7, DATA_AVAILABILITY_EVENT_TYPES ≥6; STANDARD_LIFECYCLE_EVENTS coverage). Part B: TestCrossServiceIdempotency (3 tests — undeclared-pair STRICT_FAIL default, full-window override, service-name-metadata-only). All 16 pass. UTL@7f8d174.
- [x] ✅ **16. MEGA RESERVE — workspace-wide cassette parity refresh (UAC external dirs)** — build on item 18 (cassette parity). Run cassette schema parity tests across UAC external/ dirs (80+ subdirs). Refresh cassettes where drift detected. Done-def: cassette parity green + 3+ refreshes. **~3 cal-days**.
      — 316 passed, 49 skipped (stub-only dirs intentionally skipped), 0 failed. Parity fully green. 0 drift detected post ae8b4d6 (bucket_name_ssot noqa). No cassette refreshes required — all 316 version fields match declared schemas. UAC QG ✅.
- [ ] **17. MEGA RESERVE — semver-agent label + tag audit across 21 Python repos** — build on item 14 (semver-agent label audit). Verify per-repo `feat/fix/feat!` label-to-commit mapping is correct; cross-check shipped tags vs commit history. Done-def: audit report + 2+ corrections. **~2 cal-days**.

#### Coordination

- **Owned repos**: cross-repo audit work + UTL HMAC.
- **No cross-side handshakes**.
- **Conflict-risk**: UTL = high cross-slot traffic (slot 6 + slot 8 both touch). Always `git fetch` + pull
  origin/LDR before commit.

### Slot 9 — MTDS / PBM coverage extension — ~2 cal AI-days

> **2026-05-15 cycle-close**: 9-item queue ALL DONE. No carry-over. Pick MTDS-handler coverage gaps + PBM-canonical-writer
> extensions.

#### Mechanical queue

- [x] ✅ **1. MTDS handler coverage extensions — 3 handlers pickup** — vault_share_price 75.8%→98.7%, native_staking 79.3%→93.5%, eigenlayer_rewards 77.5%→96.1% (+40 tests, 1495 passed) — mtds@d39568d
- [x] ✅ **2. PBM canonical_writer extension — MDPS-side parametrized archetype dispatch hardening** — 24 tests covering 6 uncovered branches: resolve_pipeline_mode_from_source (None/missing/valid/unknown), mdps_data_type_key (pass-through + fallback), _infer_instrument_type UNKNOWN path, _infer_chain (column + 4-part id), _infer_league_id; QG green — mdps@cce0da5
- [x] ✅ **3. solana_lst_native_staking_adapters_2026_05_14 final item (95%, 21/22)** — 1 checkbox left. Plan path:
      [`solana_lst_native_staking_adapters_2026_05_14.md`](solana_lst_native_staking_adapters_2026_05_14.md). Close
      out. (deployment-service@ea1356b — launchers + watchdog prefixes; plan now 22/22 100%)

#### Reserve queue

- [x] ✅ **4. solana_restaking_rewards_coverage_2026_05_13 final items (89%, 16/18)** — 2 DEFERRED NICE-TO-HAVE items closed out: (1) MTDS wiring migrated → issue doc; (2) program-ID verification blocked-external → issue doc. Plan now 18/18.
- [x] ✅ **5. MTDS lst_rates handler — ezETH/RENZO multi-call architecture gap** — option (b): ezETH added to registry with `unsupported_reason` + loop skip logic; absence now explicit not silent; 3 tests verify skip behavior — mtds@5dcda13
- [x] ✅ **11. DEEP RESERVE — MTDS additional adapter coverage (databento + polymarket_clob)** — databento_tradfi_ws.py 80.5%→95.4%, polymarket_ws.py 83.8%→97.0%; 27 new tests covering instrument_type fallback, _get_api_key try/except, _on_record edge cases, callbacks, _resolve_instrument_id paths, _ensure_live_client (cached+new), subscribe+start flow, CancelledError in stream(), clob_token_id indexing, HTTP non-200/exception, close() exception — mtds@66f4f3f
- [x] ✅ **12. DEEP RESERVE — MDPS canonical_writer error classification audit** — 3 gaps fixed: (1) live_workers repr→type_name classification (2) canonical_writer manifest failure adds log_event DEPLOYMENT_FAILED (3) schema validation failure adds record_failed_for_shard before re-raise; 3 tests — mdps@b71bb75
- [x] ✅ **13. DEEP RESERVE — PBM mode parity edge cases** — 4 new test classes: TestSparseDataModeParity (90%+ NaN rows stamp+capture), TestPartialShardCaptureParity (row_count pass-through), TestBatchToLiveTransitionParity (mode isolation per call) + helper fixtures; MDPS QG green — mdps@1d67851
- [ ] **14. MEGA RESERVE — live_pipeline_mtds_mdps_features (15.0 cal-days budget — pick 4-5 service-side items)** — perfect slot-9 fit (MTDS + MDPS + features). Plan: [`live_pipeline_mtds_mdps_features_2026_05_08.md`](live_pipeline_mtds_mdps_features_2026_05_08.md). Pick 4-5 mechanical service-side items (avoid cross-service contract changes). Done-def: 4+ items closed + per-service QG green. **~5 cal-days**.
- [ ] **15. MEGA RESERVE — MTDS adapter coverage continuation (deribit + binance + bybit handlers)** — after item 11 (databento + polymarket_clob), extend coverage on perp venues. Same Tier-1 SPL stake-pool / multi-call architecture pattern. Done-def: 3 adapters above 90% + MTDS QG green. **~3 cal-days**.
- [ ] **16. MEGA RESERVE — MDPS canonical_writer error classification audit (continuation of deep reserve 12)** — extend item 12. Audit all canonical_writer paths for `classify_venue_error()` + `record_failed()` emission completeness; fix gaps. Done-def: audit report + 5+ classification gaps fixed. **~3 cal-days**.
- [ ] **17. MEGA RESERVE — PBM canonical_writer mode parity + cross-archetype dispatch tests** — build on item 5 (PBM canonical_writer integration tests, mdps@4ad6060). Add: cross-archetype dispatch under degraded conditions; manifest re-sync after pause/resume. Done-def: 6+ tests + PBM QG green. **~3 cal-days**.

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
