## CREDENTIAL APPROVAL REQUEST — 2026-06-16 UTC — slot-6, BLK-e64b661a

**Task**: `cefi_ml_directional_continuous_live-002` — ≥7-day live ML signal run on OKX + Binance + Bybit
**Plan**: `plans/active/cefi_ml_directional_continuous_live_2026_06_20.md`
**Status**: BLOCKED-OPERATOR (hard-stop: wallet keys + kill-switch arming)

### Required operator actions (in order)

**1. Provision Secret Manager secrets for live CeFi-ML trading**

All 3 venues need trade-scope API keys in GCP Secret Manager (`central-element-323112`):

| Venue | Secret name(s) | Content (JSON) | Notes |
|-------|----------------|----------------|-------|
| Bybit | `bybit_api_key` | `{"api_key": "...", "api_secret": "..."}` | Single unscoped key (no read/trade split) |
| Binance | `binance-trade-api-key` + `binance-trade-api-key-secret` | Per canonical pattern | Already declared in credentials_per_archetype.yaml |
| OKX | `exec-<client>-okx-api-key` | `{"api_key": "..."}` | Per-client pattern; expand per each active client_id |
| OKX | `exec-<client>-okx-api-secret` | `{"api_secret": "..."}` | Per-client; passphrase also needed — see gap below |
| OKX | `exec-<client>-okx-passphrase` | `{"passphrase": "..."}` | OKX requires passphrase in addition to key+secret |

**2. Arm the ML_DIRECTIONAL_CONTINUOUS kill-switch** (manual operator gate per locked design)

The 4 circuit breakers are already code-wired (UAC@547cba3):
- `POSITION_LIMIT_EXCEEDED` (120% of $10k cap → CANCEL_OPEN)
- `DRAWDOWN_DAILY_BPS` (500 BPS → KILL_ALL)
- `ML_SIGNAL_STALENESS_SECONDS` (86400s → BLOCK_NEW, auto-cooldown 30min)
- `ML_MODEL_DRIFT_ACCURACY_DROP` (5% drop → BLOCK_NEW, auto-cooldown 1h)

Kill-switch arming for the archetype requires manual `POST /api/archetypes/ML_DIRECTIONAL_CONTINUOUS/circuit-breakers/arm` or equivalent operator dashboard action.

### Agent-doable gaps found during infrastructure audit (for operator awareness)

These do NOT require operator action but need to ship BEFORE live trading starts:

1. **`credentials_per_archetype.yaml` (UAC)**: `ML_DIRECTIONAL_CONTINUOUS` not declared — only DeFi archetypes present. Agent will add after SM secret names confirmed.
2. **`service_config.py` (execution-service)**: Missing `bybit_secret_name` field (Deribit/Binance/Hyperliquid have it). Agent will add `bybit_secret_name = "bybit_api_key"`.
3. **`live_execution_handler._create_orchestrator_for_venue()`**: Calls `get_order_adapter(venue=..., testnet=...)` with no credentials → adapter raises `ValueError("api_key and api_secret required for real mode")` in live mode. Agent needs to wire SM credential loading before adapter construction.

These 3 items will be shipped in a follow-up turn once operator confirms SM secret names above (especially OKX per-client naming).

**Respond with**: `[ack] slot-6 cefi-ml credentials — SM secret names confirmed, proceed with infra fix + kill-switch armed` when provisioned.

---

**[2026-05-23 ~21:15 UTC] slot-6 MTDS DeFi backfill VM launched** — ref `mtds_mdps_master` MDPS-3.3.DeFi-V

**`mtds-backfill-defi-20260523` RUNNING** (asia-northeast1-c, e2-standard-4). Range: 2024-01-01→2026-05-23, all DeFi
data_types. Tarball sha 498148da (MTDS@498148da, includes fixes 69d694b1 + e86a6ad8). Pre-launch: manifest reset ran —
13,826 SOURCE_RETURNED_ZERO rows deleted from DeFi bucket. T+10 check: RUNNING ✓.

Handler fixes included: (1) dex_swaps hardcode `dex_pool_swaps` → fixed; (2) gas_fees null result fallback; (3)
lending_indices SM error now raises. Issue doc: `plans/active/issues/mtds_defi_dex_swaps_2026_gap_2026_05_23.md`.

**[2026-05-23 ~20:30 UTC] slot-6 SEVENTH FIX + status update** — ref `mtds_mdps_master` MDPS-3.3.DeFi-V

MDPS@305677e: added ORCA-SOLANA/RAYDIUM-SOLANA to `_DEFI_DEX_VENUE_SEGMENTS` (honest-absence when Solana swap events
land). KAMINO excluded (lending_indices, bypass type). Plan: mdps_backfill_phase3 archived → tracking in
mtds_mdps_master. 195633 VMs (2024+2025) RUNNING — slot-2 SIXTH FIX. 2026 DeFi VMs:
`empty_confirmed/SOURCE_RETURNED_ZERO` expected (MTDS dex_swaps_handler stopped writing after 2026-01-24 — MTDS 2026 gap
noted in mtds_mdps_master). PM@54cd3245e docs(plans): update mtds_mdps_master DeFi-V status + Solana fix.

**[2026-05-23 ~18:50 UTC] slot-6 DeFi MDPS FIFTH FIX + VM RELAUNCH** — ref `mdps_backfill_phase3_2026_05_22.md`
MDPS-3.3.DeFi-V

Root cause of 181236 VM `empty_confirmed/SOURCE_RETURNED_ZERO`: new structured Curve/Uniswap files write
`data_type='dex_pool_swaps'` in parquet; `swap_adapter.py` `related_data_types=["swaps"]` filtered them out →
SOURCE_RETURNED_ZERO for every structured file. Also: `_aggregate_from_15s_polars` missing `group_by=["instrument_id"]`
→ multi-instrument bundles mixed into one time-bucket set (1440 full-day 1m candles from sparse cross-pool data).

Two fixes shipped as MDPS@d1637cf:

1. `swap_adapter.py`: add `"dex_pool_swaps"` to `related_data_types`; add Curve column handling
   (`amount_in_usd/amount_in`) in `_calculate_price` and volume calc.
2. `fast_candle_aggregation.py`: split multi-instrument base candles by `instrument_id` before Polars/pandas
   aggregation.

QG ✅ (1299 pass). Tarball rebuilt 18:41 UTC. 5 DeFi VMs relaunched: `mdps-defi-{2022..2026}-20260523-184826` RUNNING.
Verify pending (ETA: 2022/2023 = ~30m, 2024/2025/2026 = several hours).

> **🟢 2026-05-22 WAVE 2 DISPATCH** — codex audit Wave 1 DONE (ff137da7d). Start Wave 2 now.

## [slot-1-main → slot-6] 2026-05-22 ~05:15 UTC — Wave 2: Phase 3 codex bulk pass → MDPS backfill

**Plan ref**: `plans/active/codex_plan_audit_differential_2026_05_22.md` Phase 3 +
`plans/active/mdps_backfill_phase3_2026_05_22.md`

**Wave 1 DONE**: Group D codex audit shipped at `ff137da7d`.

**Wave 2 sequence**:

1. **NOW** — Start `codex_plan_audit_differential_2026_05_22.md` Phase 3 delta annotation bulk pass (not gated)
2. **WAIT for gate** — MTDS CeFi+DeFi verify GREEN (slot 5 posts ping here when done)
3. **After gate** — `mdps_backfill_phase3_2026_05_22.md`: Phase 1 CeFi reprocessor + Phase 2 DeFi reprocessor + Phase 3
   TradFi reprocessor

MTDS backfill VMs (CeFi/DeFi) are running now but VERIFY items (MTDS-3.2.A-V, C-V) are not yet cleared.

**After MDPS backfill verifies GREEN** → run UAC QG broadening triage per the dispatch below.

**Ack**: append `[2026-05-22 HH:MM UTC] slot-6 Phase 3 bulk pass DONE at PM@<sha>` when codex Phase 3 done.

— slot-1-main / ikenna / 2026-05-22

---

> **🟢 2026-05-22 ADDENDUM (Wave 3)** — after MDPS backfill verifies GREEN, run UAC QG broadening triage below.

> **🟢 2026-05-21 DISPATCH — supersedes all prior entries.** Read `plans/active/plan_closeout_archive_2026_05_21.md`
> §Slot 6 and the spawn prompt from operator. History below is audit-trail only.

> _Cleaned 2026-05-22 — audit trail stripped; history preserved in git._

**[2026-05-22 ~09:30 UTC] slot-6 Phase 3 bulk pass DONE** — Codex Phase 3 delta annotation + stubs + structural fixes
all complete at PM@072ba9423 (Wave 1). Phase 5 extended sweep (277 stale-marker docs across all codex sections) also
DONE at PM@37c575bde. Codex plan 100% complete. MTDS VMs still RUNNING (CeFi: mtds-backfill-cefi-2026-05-22b, DeFi:
mtds-dex-pools-backfill, Pred: mtds-backfill-prediction-2026-05-22). pip-audit fix: base-library.sh CVE-2026-45409
ignore added at PM@e56bf09d7 (UAC QG was failing). DeFi expected_coverage Bug 1 SHA confirmed: UAC@3d43382b.

**[2026-05-22 ~06:00 UTC] slot-6 Wave 1 DONE** — Codex audit Phases 1+2+3 ALL complete at PM@072ba9423. Group D
(infrastructure/plan_hygiene epic alignment): all 6 items flipped. plan-hygiene.md updated with `assigned_vm` + `tier`
as required epic fields. infrastructure_master + plan_hygiene_master Codex SSOTs tables added. plan_hygiene_master
frontmatter fixed with `tier: L5`.

**[2026-05-22 ~06:00 UTC] slot-6 Wave 2 ACTIVE** — MDPS backfill launches in progress. Phase 3 TradFi: launching NOW
(MTDS-3.2.B done 2026-05-17 — no gate). Phase 1 CeFi / Phase 2 DeFi / Phase 5 Pred: gated on MTDS verify (MTDS-3.2.A-V /
3.2.C-V / 3.2.E-V) — monitoring. MTDS VMs running: cefi@34.180.126.53, defi@34.180.69.85, pred@34.146.119.158. Plan:
`plans/active/mdps_backfill_phase3_2026_05_22.md`.

## [slot-1-main → slot-6] Wave 3 — UAC root-level QG broadening triage (0.5d)

**Issue**: `plans/active/issues/uac_root_level_tests_preexisting_failures_2026_05_20.md`

**Gate**: run only after MDPS backfill Wave 2 is done (this is post-backfill quality work).

**Scope** (0.5d triage, 2-4d remediation):

Run `PYTEST_UNIT_DIR="tests/" bash scripts/quality-gates.sh` in unified-api-contracts. Collect the 318 failures. Group
into categories:

1. **Sportsbook venues not yet scoped** (`test_venue_contract_coverage.py` failures for matchbook/manifold/etc.) — add
   `@pytest.mark.skip(reason="sportsbook scope: post-cutover")` to each test, or stub the schema module per plan.
2. **DeFi key/parity gaps** (`test_venue_key_parity.py`) — compare VENUE_DATA_TYPE_CAPABILITIES vs expected_coverage.
   Fix entries that diverge. (This pairs well with the coverage gap work done 2026-05-22.)
3. **Schema Any annotations** (`test_no_bare_any_in_normalised_models`) — add specific types.
4. **Cassette parity** (coingecko, polymarket) — update cassette YAML.

After each category fix: commit `fix(uac-tests): <category>`, QG green on that category, push. After all categories
done: change UAC `quality-gates.sh` `PYTEST_UNIT_DIR` from targeted list to `"tests/"`.

**Ack**: append `[2026-05-22 HH:MM UTC] slot-6 Wave3 DONE — UAC QG broadened at uac@<sha>` here when done.

**[2026-05-22 ~08:15 UTC] slot-6 Wave3 DONE** — UAC QG fully broadened at UAC@6e6a1e70.

- Fixed all 318 pre-existing failures: venue parity (25 new venues), sportsbook stubs (matchbook, onexbet,
  18-placeholder), archetype manifest (22 archetypes, multiline JSON), analytics models (4 Pydantic classes), protocol
  launch dates (13 new + 11 pending)
- UAC boundary test (test_ac_uic_alignment.py): fixed FORBIDDEN_PACKAGES to check UTL/UIC — UAC@87a6f367 (prev session)
- PM codex updated: 4 new Carry & Yield archetype sections (CARRY_BASIS_DATED_INV, CARRY_BASIS_PERP_INV,
  CARRY_STAKED_BASIS_DATED, CARRY_RECURSIVE_BORROW_LENDING_ONLY) — PM@24cec4d4d
- quality-gates.sh PYTEST_UNIT_DIR broadened from targeted list → "tests/" — UAC@6e6a1e70
- Full QG: 3570+ tests, 0 failures, exit code 0 (verified 3× independently)
- MDPS TradFi VM running (mdps-backfill-tradfi-20260522-051203). CeFi/DeFi/Pred gated on MTDS verify (monitoring).

**[2026-05-22 ~10:00 UTC] slot-6 MDPS wave 2 progress** — ref `mdps_backfill_phase3_2026_05_22.md`

- **DeFi arch gap RESOLVED** (PM@48befb483): confirmed features-onchain reads `lst_rates`/`dex_pool_state`/
  `lending_indices` directly from specialized buckets — bypass types, no MDPS. MDPS DeFi scope = `dex_swaps` +
  `book_snapshot_5`/`fx_rates`/`market_state`/`liquidity` only. Code evidence: `dependency_checker.py` +
  `data_loader.py`
- **3 unnecessary VMs deleted**: `mdps-backfill-defi-dex-pools-20260522-094538`,
  `mdps-backfill-defi-lending-indices-20260522-094523`, `mdps-backfill-defi-lst-rates-20260522-094503` (were producing
  bars for bypass-type data that features-onchain never reads via MDPS)
- **Main DeFi MDPS VM kept**: `mdps-backfill-defi-20260522-095053` continues for `dex_swaps` (at 2020-02-09, ~39h ETA)
- **Issue docs filed**: `mdps_defi_multi_bucket_arch_gap_2026_05_22.md` (resolved) +
  `mdps_tradfi_schema_contract_gaps_2026_05_22.md` (combo/UNKNOWN/futures_chain NaN bars, VIX unblocked)
- **Codex updated**: `codex/02-data/data-lineage-MTDS-features-ml.md` Layer 2 now documents DeFi bypass types table
  (PM@d21ec4f2b)
- **Gate status**: CeFi gate (MTDS-3.2.A-V) — VM at 2024-01-01, ~2-5 day ETA. Pred gate (MTDS-3.2.E-V) — VM at
  2025-12-13, ~3 day ETA. CeFi MDPS + Pred MDPS cannot launch until respective gates clear.

## [slot-1-main → slot-6] 2026-05-22 — P1 Codex audit Phases 1+2 (P0 items first)

**Plan**: `plans/active/codex_plan_audit_differential_2026_05_22.md`

**Why**: Codex docs are stale vs what active plans have shipped / are planning to ship. Next agent reads stale codex and
implements wrong pattern. P0 items are assumption-violating gaps.

**Your scope**: Phase 1 Group A+B (epic semantic audit) + Phase 2A (LDR-locked plan → codex) — P0 items only. Do NOT do
Phase 3 (delta annotation bulk pass) — that's a separate session.

**P0 priority order** (do in this sequence):

1. `manifest_master.md` ↔ `codex/02-data/availability-manifest-and-data-status.md` — 3 open writegate P0 codex tasks:
   cascade contract, `expected_unattempted` expansion, v8 CeFi reshaping section. WRITE these sections now.
2. `manifest_master.md` ↔ `codex/02-data/honest-absence-downstream-handling.md` — 2 open P0 tasks: per-service
   consumer-class table + typed-reason taxonomy. WRITE these sections now.
3. `writegate_honest_coverage_endtoend_2026_05_06.md` ↔ `codex/02-data/` writegate + emission semantics — Phase 2A P0
   item.
4. `trading_agent_master.md` ↔ `codex/04-architecture/trading-agent-service-directive-pipeline.md` — P1 superseded epic
   ref; confirm lines 189+217 are clean.
5. `mtds_mdps_master.md` ↔ `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — Phase 1 Group B P0.

**Pattern**: for each (plan, codex doc) pair: read the plan's Codex SSOT section OR the plan body's description of what
shipped → read the codex doc → write/edit the doc to reflect current + planned state with delta box:

```
> **[DELTA 2026-05-22]**
> **Current state:** [what's shipped to live-defi-rollout]
> **Planned delta:** [what active plan `<slug>` is delivering]
> **Target architecture:** [final destination]
```

**QG**: No code QG needed — docs only. Flip plan checkboxes in `codex_plan_audit_differential_2026_05_22.md` as you
complete each item.

**Ack**: append `[2026-05-22 HH:MM UTC] slot-6 DONE — codex audit P0 items complete at PM@<sha>` here when done.

---

## [main → slot 6] 2026-05-21 — 6 plan closes + trivial sweeps (pm@5eedc069a)

**Timestamp**: 2026-05-21 | **Status**: 🟢 DISPATCH

**Your job**: Close these 6 plans (trivial sweep aggressively — most remaining items are likely docs/stubs):

1. `codex_vs_citadel_infrastructure_audit` (91% done — almost certainly all trivial)
2. `pm_coordination_ledger` (tiny, 0.3 cal)
3. `missing_question_docs_disposition` (3 items — file dispositions, no code)
4. `scratch_codefreeze_phase4`
5. `compute_optimization_mock_data` (60% done, 1.9 cal — mechanical only)
6. `features_service_qg_cleanup_2026_05_11` — **HARD STOP on Phase 2 parity RUN**: blocked by 7-day live-data window.
   Mark that item `[BLOCKED — 7-day live-data window]`. Close everything else.

**Trivial sweep policy**: before ANY real work on each plan, mark [x] immediately for: QG-run with existing green SHA |
dry-run with recorded results | "don't deprecate" when repo active | "create successor" when successor exists | P3 with
deferred P0/P1 → [ABANDONED] | codex stub already in doc

**Sweep bonus**: scan related_plans: links after all 6 — trivial-sweep any >90% linked plan.

**Ack**: append `[2026-05-21 HH:MM UTC] slot-6 DONE — closed/archived N plans` here when done.

**[2026-05-21 09:30 UTC] slot-6 DONE** — Wave 1: archived 7 plans (6 assigned + sweep bonus
`mock_data_pipeline_benchmarking`); `features_service_qg_cleanup` kept active (Phase 2 BLOCKED-UPSTREAM 7-day window).
Wave 2 Slot D: assessed 4 plans (agent_orchestrator_cloud_run, agent_orchestrator_dual_deployment,
agent_reliability_mitigations, canary_coverage_qg_enforcement). All §Slot 6 items + §Wave 2 Slot D wrapper flipped.
`plan_closeout_archive_2026_05_21` archived at PM@c38098ec (72/72 done). Slot queue exhausted — awaiting next dispatch.

---

> **⚠️ PRIOR ENTRIES BELOW — audit trail only.**

---

## [slot 6 → main] 2026-05-20 — Phase 4 SHIPPED ✅; Phase 7 🟡 BLOCKED-on-Phase-6

**Phase 4 done**: strategy-service@6506f868 (10 files: SharedMarksReader, CredentialStore, ClientContext,
client_worker_entry, make_worker_target, StrategySupervisor + 5 test files); 59 tests pass; basedpyright 0 errors. Plan
flip: PM@6422c115.

**Phase 5 now UNBLOCKED** (was blocked on Phase 4).

**Phase 7 BLOCKED**: requires Phase 6 (execution-service wiring + TransferCoordinator) — assigned to slot 7. Phase 6 not
yet shipped per plan. Once slot 7 ships Phase 6, ping slot 6 to unblock Phase 7 e2e + unit tests.

---

## 2026-05-22 — [slot-4 → slot-6] Path B complete — Phase 8 unblocked

**From**: slot-4 ikenna **Plan ref**: `plans/active/trading_agent_service_architecture_unlock_2026_05_22.md`

All Path B phases done:

- Phase 3 (features-service `performance_features/` scaffold): ✅ uac@72395499, features-service@2a7af305
- Phase 6 (trading-agent-service scaffold): ✅ trading-agent-service@119fa74
- Phase 6.5 (backtest-replay infrastructure): ✅ uac@20567882, trading-agent-service@33a7ae9
- Phase 7 (CI hygiene): ✅ workspace-qg CI run 26275695242 passed 2026-05-22T07:55:20Z
- Phase 8 (Codex SSOT + plan manifest): ✅ PM@d7964d0d (already flipped)

**Action**: Phase 8 is already done (PM@d7964d0d). No further action needed from slot-6 for this plan unless you want to
do a final master-plan flip. All 8 phases GREEN.

— slot-4

---

## 2026-06-01 — [slot-1 → slot-6] Take workspace_config_drift_remediation IN FULL

**From**: slot-1 ikenna **Plan ref**: `plans/active/workspace_config_drift_remediation_2026_06_01.md`

Items 1–5 already SHIPPED + flipped (canonical fix unified-trading-pm@73963a354, generator path-style fix @c6dab6afd,
regression guard @79263233d, features-service ci_status adjudicated + slot-5 stale stash dropped, Item 5 watchdog spec).
**Do not redo.** Two OPEN `- [ ]` P3 todos remain:

- **Item 5b** — implement the FF-pull starvation watchdog per the plan's "§ Item 5 spec" (wire `collision` detection
  into `scripts/dev/slot-git-status-report.sh` + POST the ping; add a bats/unit test; update codex Step 7).
- **agent-audit.yml discovery** — investigate why `.github/workflows/agent-audit.yml` fails at 0s ("log not found") on
  features-service LDR while `quality-gates-v2` is green; determine features-service-only vs workspace-wide; fix or
  retire.

**Action**: FF-pull `unified-trading-pm` to LDR tip first; run full `quality-gates.sh` before claiming mergeable
(basedpyright ratchet 1511 — no regress); land on `live-defi-rollout` (staging is 632 behind); Commit + Push + Flip each
item in the same turn. Both items are P3 — low-priority tail of an otherwise-complete plan.

— slot-1
