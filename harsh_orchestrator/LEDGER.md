---
title: Main Agent Ledger — Harsh side
type: orchestration-ledger
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Main Agent Ledger (Harsh side)

> Tracks today's slot assignments and live state. Universal mechanics and reading order → [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md). Full task briefs → today's work-split. History → `git log`.

---

## Current shift: 2026-05-13 Wave 2 (Day-4 PM, Harsh-side ONLY)

**Work-split**: [`plans/active/work_split_2026_05_13_harsh.md`](../plans/active/work_split_2026_05_13_harsh.md) § "Wave 2"
**Model**: Sonnet 4.6 / thinking: high (all slots). Wave 1 closed; reset done on 6 of 8 slots; 6 implementor slots active (2, 3, 4, 6, 7, 9); 3 held for cleanup (5, 8, 10).

| Slot | Theme | State | Plan-of-record | Branch |
|------|-------|-------|----------------|--------|
| 1 | Main orchestrator + on-call + LEDGER + ping triage | 🟢 ONLINE | (this LEDGER + work-split) | `tab/hk/1` |
| 2 | Wave 3 ✅ DONE (launcher_scripts 15/15 — deployment-api@538e11b + PM@724a2029); 🆕 Wave 4: `data_status_drilldown_shard_atom_alignment_2026_05_07.md` finalisation (61% → 100%, 16 open items) | 🟡 NEW (Wave 4) — see § "Wave 4 task briefs — Slot 2" below | `data_status_drilldown_shard_atom_alignment_2026_05_07.md` | `tab/hk/2` |
| 3 | Wave 3 ✅ DONE (C901 cleanup 11→2 + 12→8 — execution-service@2dee623f); 🆕 Wave 4: PoolStateResult ImportError P1 fix (slot 3's own finding in execution-service/defi_execution/protocols/__init__.py:78) | 🟡 NEW (Wave 4) — see § "Wave 4 task briefs — Slot 3" below | `issues/pool_state_result_import_error_2026_05_13.md` | `tab/hk/3` |
| 4 | **Resume agenda (held pending 17-test-failures question)**: (1) explain the 17 pre-existing test failures slot 4 saw — what command, what's the test list. (2) Pop stash@{0} `slot4-preserved-foreign-wip-service_entry` in `.tabs/4/strategy-service` — commit `service_entry.py --synthetic-input-uri` arg (Phase 3.D/4.A-tail of mock_data). (3) `bash deployment-service/scripts/vm/create-code-tarballs.sh --all` to refresh VM tarballs (normal ops, not gated on operator). (4) Launch Script 3 DRY-RUN VM for defi/sports/prediction (read-only — emits triage.jsonl, doesn't mutate manifest); capture upgrade counts; update issue doc `classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` + plan body with findings. NO apply-flips. | 🟪 ON HOLD per operator (resume to ship the agenda above) | `issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` + mock_data Phase 3.D/4.A-tail | `tab/hk/4` |
| 5 | (cleanup done 2026-05-13 — local tab/hk/5 hard-reset to LDR; cc62f02 preserved on origin/tab/hk/5 as historical record) | 🟪 RESERVE (ready) | — | `tab/hk/5` |
| 6 | 🆕 Wave 3: per_agent_worktrees finalisation + api_football flattening finalisation | 🟡 NEW (Wave 3) — see § "Wave 3 task briefs — Slot 6" below | `per_agent_worktrees_2026_05_10.md` + `api_football_minimal_flattening_removal_2026_05_07.md` | `tab/hk/6` |
| 7 | 🆕 Wave 3: cross_asset Phase 6 validation suite (1G + 6A/6B/6C/6D) — **Opus 4.7** | 🟡 NEW (Wave 3) — see § "Wave 3 task briefs — Slot 7" below | `cross_asset_group_catalogue_audit_2026_05_10.md` Phase 6 | `tab/hk/7` |
| 8 | (cleanup done 2026-05-13 — local tab/hk/8 hard-reset to LDR; 949185c preserved on origin/tab/hk/8 as historical record) | 🟪 RESERVE (ready) | — | `tab/hk/8` |
| 9 | 🆕 Wave 3: Sports classifier extension P1 (Wave 1 audit re-open — slot 9's own grep-miss) | 🟡 NEW (Wave 3) — see § "Wave 3 task briefs — Slot 9" below | `issues/sports_classifier_extension_followup_2026_05_13.md` | `tab/hk/9` |
| 10 | dex_perp Phase 2A/2D/2E + 2F P2 + EigenLayer Phase 3A/3B + Phase 4A/4B + codex 5.1/5.2 | ✅ DONE 2026-05-13 — all in-scope shipped (MDPS@c30d8e0 cherry-picked by main to rescue foot-gun #5: MDPS 19-test fix had been left on tab/hk/10 only); worktree reset complete; 4 items DEFERRED with successor refs in plan body | `dex_perp_and_venue_data_expansion_2026_05_12.md` | `tab/hk/10` |

**Wave 1 closeout** (commits on LDR for the record):
- Slot 2 ✅ DONE (PM@3b317e65) — propagation chain Gate 1 fired
- Slot 3 ✅ DONE (PM@3a16656d) — GCP 3 buckets shipped, AWS deferred Phase 2.6
- Slot 4 ✅ DONE (PM@42755747) — Phase 8A-D rescued via cherry-pick (execution-service@38b3e8a5, foot-gun #5 intercept)
- Slots 5-9 ✅ DONE (PM@3d3d5c14) — batch closure; full per-slot detail in pings/slot_N.md
- Slot 10 ✅ DONE — all in-scope tasks shipped to LDR; 4 items DEFERRED with successor annotations in `dex_perp_and_venue_data_expansion_2026_05_12.md` scoreboard PM@6090e183

**Wave 2 reset status (2026-05-13 09:35-09:40 UTC, PM@7ca204a6)**:
- Slots 2, 3, 4, 6, 7, 9 — reset clean to origin/live-defi-rollout ✅
- Slot 5 — rebase failed (collision casualty cc62f02 in MTDS); deferred to manual cleanup
- Slot 8 — UAC rebase failed (collision casualty 949185c); deferred to manual cleanup
- Slot 10 — skipped per operator (still working at reset time); finished after reset

**Cleanup queue (DONE 2026-05-13 ~11:55 UTC)**:
- ✅ Slot 5 reset: local tab/hk/5 hard-reset to LDR; cc62f02 preserved on origin/tab/hk/5
- ✅ Slot 8 reset: local tab/hk/8 hard-reset to LDR; 949185c preserved on origin/tab/hk/8
- ✅ Slot 10 foot-gun #5 intercept: MDPS@0c92b91 (19-test fix) was NOT on LDR despite slot 10's "all work synced" claim. Main cherry-picked to LDR as MDPS@c30d8e0; slot 10 worktree reset clean.

All 10 slots are now in clean known state on LDR (or as ✅ DONE for slot 10).

**Critical-path sequencing (slot 1 monitors during Wave 2)**:
1. Slot 4 ships Script 3 classifier fix → unblocks defi/sports/prediction legacy-blank reclassification (deferred apply-flips still pending post-cutover)
2. Slot 9 ships mock_data Phase 3.D → benchmark report has real 6-stage timings (not extrapolated)
3. Slots 2/3/6/7 fully independent — run in parallel
4. New HARD RULE: LDR-alignment cadence (codified 2026-05-13 PM@f49d5f7d). Slots that boot must rebase ALL owned repos; FF-push per shippable unit, not end-of-session

**Wave 1 audit retrospective**: 3 critical follow-ups pushed PM@7ca204a6 — see `plans/active/issues/audit_wave1_quality_2026_05_13.md` for synthesis. Two impact Wave 2 spawn:
1. Slot 9 Task 3 strategy-paper VM was never actually launched in Wave 1 — re-opened in `promote_workflow_may23_cli_path_2026_05_10.md` Phase 1 as P0. Available for any slot that finishes early to absorb.
2. Sports classifier extension never shipped (slot 9 Wave 1 grep-then-conclude miss) — re-filed as `plans/active/issues/sports_classifier_extension_followup_2026_05_13.md` P1. Available for reserve pickup.

**Operator-pending**: None blocking Wave 2 spawn. Carry-forward (post-cycle operator decisions): slot 8's A/B/C UAC architecture triage (deferred; lives in cross-side `_agent_pings.md`); Telegram OPS chat_id (operator action); AWS bucket creation (Phase 2.6 window, needs GCE VM with aws CLI).

---

## Wave 2 task briefs (slot N agents — read your row)

Each row is a full task brief. After `--reset-slot N` (done 2026-05-13 09:35 UTC), your worktree at `.tabs/N/` is clean on `tab/hk/N` matching `origin/live-defi-rollout`. Just boot + read your row + start.

### Slot 2 — risk_simulations finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `risk-and-exposure-service` + `unified-api-contracts` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/risk_simulations_limits_alerting_2026_05_10.md`](../plans/active/risk_simulations_limits_alerting_2026_05_10.md) (currently 33/40 P0 = 82%)
- **Task**: Ship the 7 open P0 items:
  1. Phase 4.A — risk-and-exposure-service rule migration to UAC registry; rule_evaluator wired
  2. Phase 8.A — Per-rule synthetic-fire test (uses `simulation_scenarios_topology_price_shocks_2026_05_09`)
  3. Phase 8.B — Per-archetype suite: ≥10 rules per archetype fire on schedule + alert routes per archetype
  4. Phase 8.C — Evidence capture
  5. Phase 9.A — Master plan Group F item 20 row gains "risk rule taxonomy + pre-flight + alerting wire"
  6. Phase 9.B — Banners removed
  7. (4 P1 stablecoin items D.2/D.5/D.6/D.7 — only if time after P0s done)
- **Done-def**: 33/40 → 40/40 P0; rule_evaluator wired; per-archetype suite green; Group F item 20 flipped.
- **No big decisions needed.**

### Slot 3 — DR finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `deployment-service` + `unified-trading-library` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/disaster_recovery_circuit_breakers_2026_05_10.md`](../plans/active/disaster_recovery_circuit_breakers_2026_05_10.md) (currently 28/42 = 67%)
- **Task**: Write scripts + master-plan rows. **DO NOT LAUNCH ANY VMs** — Ikenna's hold direction on backfill/recon VMs is conservative; treat DR-drill VM launches the same and gate execution on operator OK.
  1. Phase 6.A — Cron VM `disaster-drill-cron-` launcher SCRIPT (writes only; no launch)
  2. Phase 6.B — Drill-report tooling (pass/fail per scenario; alerting rule on red >24h)
  3. Phase 9.A — Per-archetype `dr-drill-cutover-` launcher SCRIPT (arm `KILL_PER_ARCHETYPE`, etc.)
  4. Phase 9.B — Evidence-capture format
  5. Phase 10.A — Master plan rows Group F item 20 + 21 green
  6. Phase 10.B — Banners removed
- **Done-def**: 28/42 → ~38/42; SCRIPT artifacts written + linted + dry-run validated locally; ping `pings/slot_3.md` when scripts ready for operator OK to launch VMs.
- **No big decisions needed.**

### Slot 4 — 🐛 Script 3 classifier P1 + arbitrage final (Sonnet 4.6 / thinking: high)

- **Owned repos**: `instruments-service` + `unified-trading-library` + `strategy-service` + `unified-trading-pm`
- **Plans-of-record**:
  - [`plans/active/issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md`](../plans/active/issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md) (P1 bug, slot 6 Wave-1 filed)
  - [`plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md`](../plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md) (18/20 = 90%, 2 P1 items left)
- **Task**:
  1. **Fix `classify_blank_reason_row()` `fixture_manifest` kwarg mismatch**: Read UTL `unified_trading_library.manifest.classify_blank_reason_row` signature; read `instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py` call-site; align (add `fixture_manifest` handling to reconciler OR drop from UTL — pick per which is canonical intent). FF-push.
  2. **Re-run Script 3 DRY-RUN** for defi/sports/prediction (NO `--apply-flips` — Ikenna's hold direction on manifest reconciliation VMs still applies). Update the issue doc with dry-run upgrade counts. FF-push.
  3. **Arbitrage final 2 items**: canonical BTC/USDT slot entry in strategy-service + tests (per plan-of-record line `^- \[ \]`). FF-push.
- **Done-def**: Script 3 classifier signature aligned + dry-run shows non-zero upgrades for defi/sports/prediction; arbitrage_price_dispersion 18/20 → 20/20.
- **No big decisions needed.**

### Slot 6 — wave3x_residual_ssots finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `unified-api-contracts` + `unified-trading-library` + per-asset_group services (as items dictate) + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/wave3x_residual_ssots_2026_05_08.md`](../plans/active/wave3x_residual_ssots_2026_05_08.md) (currently 16/22 = 73%, 6 items left across Tracks B/C/D/E)
- **Task**: Read the plan. Scan open `- [ ]` todos under Tracks B (sports per-source SSOTs) / C (reconcilers) / D (zero-activity-bar audit) / E (sports availability stamping cascade). Ship in plan order. FF-push per shippable unit.
- **Done-def**: 16/22 → 22/22; all Wave 3.X dimensions covered.
- **No big decisions needed.**

### Slot 7 — cross_asset Phase 5 TradFi consolidation (**Opus 4.7 / thinking: high** ⬆ — multi-callsite refactor)

- **Owned repos**: `unified-api-contracts` + `instruments-service` + `market-tick-data-service` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/cross_asset_group_catalogue_audit_2026_05_10.md`](../plans/active/cross_asset_group_catalogue_audit_2026_05_10.md) § Phase 5 + reference [`plans/archive/issues/catalogue_audit_tradfi_2026_05_12.md`](../plans/archive/issues/catalogue_audit_tradfi_2026_05_12.md) for TF-1..TF-10 detail
- **Task**:
  1. **Phase 5A — `tradfi_etfs.py`**: Diff-merge 4 ETF universes → single SSOT at `unified_api_contracts/canonical/domain/derivatives/tradfi_etfs.py`. Sources: `tradfi_symbology.py:459` `KNOWN_ETFS` + `tradfi_ticker_universe.py:295` `ETF_TICKERS` + `tradfi_instrument_universe.py:151` `_BTC_SPOT_ETFS`+`_ETH_SPOT_ETFS` + `TRADFI_TICKER_COVERAGE_START` ETF subset. **READ each source file body** — do not grep-then-conclude on membership equivalence. Escalate membership conflicts to operator via `pings/slot_7.md`.
  2. **Phase 5B — `tradfi_roots.py`**: Diff-merge 3 futures-roots universes (`TRADFI_INSTRUMENTS` + `TRADFI_DATABENTO_INSTRUMENTS` + `databento_cme_converter.py:57` `SUPPORTED_UNDERLYINGS`) → single SSOT.
  3. **Phase 5C — `asset_group_registry.py`**: TradFi entries point at new SSOTs.
  4. **Phase 7 (small) — VIX-15m doc-pointer fix (TF-7)**: VIX-15m constants live in `registry/data_source_continuity.py` NOT `canonical/crosscutting/honest_coverage.py` as CLAUDE.md L535 claims. Fix the doc reference in CLAUDE.md + any codex doc that mirrors the wrong pointer.
- **Done-def**: 4 ETF universes → 1 SSOT (membership diff documented in plan body); 3 futures-roots → 1 SSOT; cross_asset audit Phase 5 checkboxes flipped with evidence; VIX-15m doc-pointer corrected.
- **GREP-THEN-READ warning**: This is multi-callsite refactor. Wave 1 audit found Sonnet had grep-then-conclude failures on this exact shape (3 of 3 slots). Read each source file's actual dict/tuple contents — don't trust the variable name to imply the contents.
- **Escalated to Opus 4.7** per Wave 1 audit recommendation.

### Slot 9 — mock_data Phase 3.D per-reader threading (**Opus 4.7 / thinking: high** ⬆ — 3-reader bespoke wire-in)

- **Owned repos**: `market-tick-data-service` + `ml-inference-service` + `strategy-service` + `unified-trading-library` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/mock_data_pipeline_benchmarking_2026_05_10.md`](../plans/active/mock_data_pipeline_benchmarking_2026_05_10.md) § Phase 3.D (currently 19/29 = 66%)
- **Task**: Wire `default_subprocess_pipeline()` benchmark harness into 3 readers that bypass `resolve_bucket_uri`. For EACH reader, OPEN the function body before deciding the wire-in shape:
  1. **MTDS Tardis/Databento fetch**: External-API non-GCS readers. Needs benchmark-specific instrumentation hook (NOT standard `resolve_bucket_uri` override since these don't go through GCS).
  2. **ml-inference direct feature-vector loader**: Add bespoke `_STAGE_COMMAND_TEMPLATES` entry.
  3. **strategy direct signal+features loader**: Same pattern as (b).
  Then verify with subprocess-pipeline benchmark on 1-day batch.
- **Done-def**: mock_data 19/29 → ~25/29; Phase 3.D `[x]` flipped with shipped SHAs; benchmark report includes all 6 pipeline stages with REAL timings (currently extrapolated for these 3).
- **GREP-THEN-READ warning**: Slot 9 in Wave 1 had a grep-then-conclude failure on sports classifier. Don't repeat — open each reader's function body before declaring shape.
- **Escalated to Opus 4.7** per Wave 1 audit recommendation.

---

## Wave 3 task briefs (post Wave 2 finalisation — 2026-05-13 PM)

5 slots reassigned (2, 3, 6, 7, 9). Slot 4 deliberately UNASSIGNED — operator holding for the "17 pre-existing test failures" question. Slot 1 = main. Slots 5, 8 = RESERVE. Slot 10 = ✅ DONE.

### Slot 2 — launcher_scripts_consolidation finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `deployment-service` + `deployment-api` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`](../plans/active/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md) (currently 11/15 = 73%)
- **Task**: Ship the 4 open `- [ ]` items. Read the plan, scan open todos, ship in order. Likely Phase 2 (deployment-api `_SERVICE_LAUNCHER_SCRIPTS` registry extension — register strategy-paper + strategy-live launchers so Deploy-Missing UI button surfaces them).
- **Done-def**: 11/15 → 15/15; all launchers registered in deployment-api; Deploy-Missing UI surfaces strategy launchers.
- **Why this**: Closes out an in-flight consolidation; unblocks the `1.Y DEFERRED-AFTER-CONSOLIDATION-PHASE2` carry-forward in promote_workflow plan (operators can deploy via UI instead of manually).

### Slot 3 — execution-service C901 cleanup + deployment-service pytest-timeout fix (Sonnet 4.6 / thinking: high)

- **Owned repos**: `execution-service` + `deployment-service` + `unified-trading-pm`
- **Plans-of-record**:
  - [`plans/active/issues/strategy_service_ruf002_sigma_lint_failures_2026_05_13.md`](../plans/active/issues/) (RESOLVED — sigma done by slot 4)
  - Pre-existing QG blockers flagged by slot 4 + slot 5 today: `execution-service/execution_service/providers/rpc_fallback.py:69` (`__init__` complexity 11) + `execution-service/execution_service/api/manual_instruction_api.py:190` (`submit_manual_instruction` complexity 12)
  - `deployment-service` `.venv` missing `pytest-timeout` (slot 5 flagged today)
- **Task**:
  1. **C901 cleanup**: refactor each function below complexity 10. `rpc_fallback.py:69` — extract config/state-setup helper. `manual_instruction_api.py:190` — extract validation + persistence helpers. Tests + basedpyright + ruff green. FF-push.
  2. **pytest-timeout**: add `pytest-timeout = "*"` to `deployment-service/pyproject.toml` `[project.dependencies]` (or appropriate group); `uv pip install -e .[dev]`; verify QG Pass 1 green. FF-push.
  3. File a P3 ack ping with the SHAs.
- **Done-def**: 2 C901 violations cleared (complexity < 10); pytest-timeout installed + QG green in deployment-service. Both slot 4 + slot 5 blockers unblocked.
- **Why this**: Pre-existing QG blockers that block ANY service-touch in those files. Small mechanical refactors (~1-2h total).

### Slot 6 — per_agent_worktrees + api_football finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `unified-trading-pm` + `instruments-service` + per relevant repos
- **Plans-of-record** (2 quick-finishes):
  - [`plans/active/per_agent_worktrees_2026_05_10.md`](../plans/active/per_agent_worktrees_2026_05_10.md) (27/30 = 90%, 3 open)
  - [`plans/active/api_football_minimal_flattening_removal_2026_05_07.md`](../plans/active/api_football_minimal_flattening_removal_2026_05_07.md) (11/16 = 69%, 5 open)
- **Task**: Ship remaining open items in each plan (do per_agent_worktrees first — codex/docs cleanup of the worktrees system; then api_football — sports adapter flattening removal).
- **Done-def**: per_agent_worktrees 30/30; api_football 16/16.
- **Why this**: Two near-done plans; closing them removes residual tracking load. Slot 6's Track D work already adjacent to these (codex + docs).

### Slot 7 — cross_asset Phase 6 validation suite (**Opus 4.7 / thinking: high** ⬆)

- **Owned repos**: `unified-api-contracts` + `instruments-service` + `market-tick-data-service` + `features-service` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/cross_asset_group_catalogue_audit_2026_05_10.md`](../plans/active/cross_asset_group_catalogue_audit_2026_05_10.md) Phase 6 (5 open P0 items)
- **Task**: Natural continuation of slot 7's Phase 5 Wave 2 work. Ship Phase 6 validation suite:
  1. **1G — UAC QG green** post-Phase-1.
  2. **6A — workspace-grep audit** for every deletion / rename / dual-source consolidation Phase 5 made; verify NO downstream consumer reads from old name.
  3. **6B — Per-asset-group coverage % validation** post-Phase-2: probe canonical manifest manually for 5 asset_groups.
  4. **6C — End-to-end smoke** running `measure_honest_coverage.py` against production manifest.
  5. **6D — All Phase 1-5 QGs green** across UAC + instruments-service + MTDS + features.
- **Done-def**: 5 P0 items shipped with evidence; QGs green across 4 repos; coverage % numbers documented in plan body.
- **Why Opus**: Multi-callsite workspace-grep audit + cross-repo QG. Audit recommended Opus for this shape.

### Slot 9 — Sports classifier extension P1 (Wave 1 audit re-open) (Sonnet 4.6 / thinking: high)

- **Owned repos**: `unified-trading-library` + `instruments-service` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/issues/sports_classifier_extension_followup_2026_05_13.md`](../plans/active/issues/sports_classifier_extension_followup_2026_05_13.md) — Wave 1 audit re-open (slot 9's own grep-miss); P1
- **Task**:
  1. **Sports classifier extension** per issue doc § "What needs to happen": **READ `_classify_sports:191` function body BEFORE concluding** (GREP-THEN-READ HARD RULE — slot 9's Wave 1 failure was exactly this anti-pattern). Implement 4 sports rules (EXPECTED_PAUSED_LEAGUE / EXPECTED_PRE_SEASON / EXPECTED_POST_SEASON / EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE) in priority order; query instruments-service sports SSOT for league calendars + source-coverage windows; ≥4 unit tests per rule (16 total).
  2. Re-run Script 3 DRY-RUN for sports after classifier extension (verify non-zero upgrades). NO apply-flips (Ikenna's hold).
- **Done-def**: 4 sports rules shipped in UTL with 16 tests green; Script 3 dry-run shows non-zero upgrades for sports.
- **NOT slot 9's scope**: slot 4's stash@{0} in `.tabs/4/strategy-service` (`service_entry.py --synthetic-input-uri`) — that's **slot 4's own worktree cleanup**, handled by slot 4 when they resume (alongside the 17-test-failures question). Even though the content lands in slot 9's mock_data plan scope, the stash cleanup ownership = the worktree owner = slot 4.

### Slots 5, 8 — RESERVE (no assignment)
Both cleaned + ready. Available for spillover absorption if any Wave 3 slot finishes early or operator picks a reserve-list item to assign.

---

## Wave 4 task briefs (post Wave 3 close-out — 2026-05-13 PM)

Slots 2 and 3 both finished Wave 3 cleanly. Reassigning for Wave 4. Slot 4 stays ON HOLD (17-test-failures + bundled agenda). Slots 6/7/9 still IN-FLIGHT on their Wave 3 work (check their pings before assuming free).

### Slot 2 — data_status_drilldown finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `deployment-api` + `unified-trading-system-ui` (deployment-ui) + per-asset_group services + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.md`](../plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.md) (currently 25/41 = 61%, 16 open)
- **Task**: Ship the 16 open `- [ ]` items. Read the plan first, scan open todos, ship in plan order. Likely a mix of: shard-atom alignment verification across `(asset_group, venue, data_type, instrument_id, day)` for the 5 asset_groups, deployment-api `/api/manifest/drilldown` endpoint refinements, deployment-ui DataStatusPanel drilldown surface. Cross-cutting infra cleanup.
- **Done-def**: 25/41 → 41/41; data-status drilldown surfaces per-shard-atom granularity correctly across all 5 asset_groups.
- **Why this**: Cross-cutting umbrella; closes out a 61%-done plan that's been sitting; aligns with slot 2's deployment/ops context from Wave 3 work.

### Slot 3 — PoolStateResult ImportError P1 fix (Sonnet 4.6 / thinking: high)

- **Owned repos**: `execution-service` (+ possibly UAC if the symbol moved there) + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/issues/pool_state_result_import_error_2026_05_13.md`](../plans/active/issues/pool_state_result_import_error_2026_05_13.md) (P1, slot 3's own Wave 3 finding)
- **Task**:
  1. **Diagnose**: Read `execution_service/defi_execution/protocols/__init__.py:78` (import site) + `execution_service/defi_execution/protocols/base.py` (claimed source). Has `PoolStateResult` been renamed? Removed? Moved to UAC? `git log -p` on `base.py` to find when the export disappeared. Likely root cause: foreign UAC refactor (`DeFiPoolStateResult as PoolStateResult` re-export was removed; multiple slots saw this dirty earlier today as "ruff drift" but it may have been intentional UAC consolidation).
  2. **Fix**: Either restore the re-export at `base.py` (if `PoolStateResult` still exists upstream) OR update `__init__.py:78` to import from the new canonical path (probably `unified_api_contracts.internal.DeFiPoolStateResult`). Pick the canonical path per current UAC SSOT — read UAC `internal/__init__.py` `__all__` to verify.
  3. **Verify**: `bash scripts/quality-gates.sh` in execution-service goes green; tests pass; downstream consumers (any code that imports `PoolStateResult` from `execution_service.defi_execution.protocols`) still work.
  4. **Update issue doc**: mark RESOLVED with fix SHA + root cause documented.
- **Done-def**: ImportError gone; execution-service QG green; downstream consumers verified; issue doc closed.
- **Why this**: Slot 3's own finding from Wave 3 work; their context is fresh on execution-service; small targeted fix (~30-60 min). After this they stand by for the next assignment.
- **GREP-THEN-READ**: read the actual `base.py` file contents + `__init__.py:78` line + UAC `internal/__init__.py` BEFORE deciding the fix path. Don't grep-then-conclude on naming.

---

## Spawned tab — boot

You are slot N. Do this in order, nothing else until done:

1. Read [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) — git discipline, LDR-alignment HARD RULE, workspace-drift recognition, communication bus, pre-commit check, sub-agent rules.
2. Find your **Slot N task brief** in this LEDGER § "Wave 2 task briefs" above → that's your full assignment (owned repos + scope items + done-def + model tier).
3. Read your **plan-of-record** (named in your brief) — scan open `- [ ]` todos for your phase.
4. Append boot ack to [`pings/slot_N.md`](pings/) using `date -u` for timestamp, then start work.

**COMPACT-CYCLE GUARD**: Do NOT read repo-level `.claude/CLAUDE.md` files from repos you're working in — the workspace CLAUDE.md (auto-loaded in system context) covers all critical cross-cutting rules. Only read a repo's CLAUDE.md if it's explicitly named in your task brief.

---

## Default agent-spawn workflow (HARD RULE — codified 2026-05-13)

**This is the default for every wave / morning / mid-day relaunch.** Operator should NEVER receive a verbose paste-ready spawn prompt from main unless they explicitly ask for one. Task briefs live in this LEDGER § "Wave N task briefs" — agents read them from there.

**Step 1 (slot 1 main runs, background, parallel)** — reset all 6 slots in one shot:

```bash
cd /home/hk/unified-trading-system-repos
for n in 2 3 4 6 7 9; do
  (
    find ".tabs/$n" -maxdepth 2 -name ".git" 2>/dev/null | while read g; do
      git -C "$(dirname $g)" checkout -- . 2>/dev/null
    done
    bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot $n 2>&1 | grep -E "Resetting|complete|ERROR" | sed "s/^/[slot $n] /"
  ) &
done
wait
```

Swap the slot list `2 3 4 6 7 9` for whichever slots the operator wants to spawn this wave. The `git checkout -- .` step silently discards any leftover uncommitted state from the prior agent (usually a STARTED ack — no real work lost). Reset then rebases `tab/hk/N` cleanly onto `origin/live-defi-rollout`.

**Step 2 (operator opens N terminals)** — paste this lean prompt (swap `N`):

```
You are Harsh-side slot N. Pull origin/live-defi-rollout in unified-trading-pm, read harsh_orchestrator/LEDGER.md to find your Slot N task brief, then start working on it. If any owned repo in your worktree at /home/hk/unified-trading-system-repos/.tabs/N/ is behind LDR, fetch + rebase first. Follow harsh_orchestrator/AGENT_ONBOARDING.md for git discipline + ping mechanics + LDR-alignment HARD RULE.
```

That's it. No COMPACT-CYCLE GUARD lectures, no LDR-alignment explanations, no GREP-THEN-READ warnings inline — all that lives in `AGENT_ONBOARDING.md` (universal mechanics) and the LEDGER task brief (per-slot specifics including model tier + grep-then-read warnings on multi-callsite scopes).

**Step 3 (main monitors)** — agent reads LEDGER + plan-of-record + boots. If agent asks clarifying questions, the answer is "the LEDGER brief is the SSOT — re-read it; if still unclear, ping `pings/slot_N.md`". Don't expand the prompt; expand the LEDGER brief.

**Deviation only when operator explicitly says**: "give me a direct prompt for slot N" or "use a custom prompt for X reason". Otherwise: default workflow.

---

## Main orchestrator — fresh boot (slot 1)

**HARD RULE: fetch-first** (codified 2026-05-13). Before reading any plan/ping/LEDGER state to make a claim or write back, `git fetch origin --quiet` in the SAME bash call as the read. Default assumption: **agents are working** — burden of proof = "I just fetched and origin shows stalled state". See `AGENT_ONBOARDING.md § "Fetch-first discipline"` for why + always-fetch operations list.

Fresh main-agent chat (context window died, new session):

1. `git -C /home/hk/unified-trading-system-repos/unified-trading-pm fetch origin --quiet && git -C /home/hk/unified-trading-system-repos/unified-trading-pm log --oneline -10 origin/live-defi-rollout` — see recent origin activity.
2. `git -C /home/hk/unified-trading-system-repos/unified-trading-pm fetch origin --quiet && cat harsh_orchestrator/pings/slot_{2..10}.md 2>/dev/null` — intra-side pings (fetch-first).
3. `cat plans/active/_agent_pings.md` — cross-side pings.
4. Read this LEDGER § "Current shift" table — note each slot's state; update any SPAWN PENDING → IN FLIGHT based on ping acks.
5. Ack to operator: "Main online. Slots in flight: N. Pings: M intra / K cross. Standing by."
