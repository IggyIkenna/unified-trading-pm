---
doc_type: plan
title:
  Post-freeze roadmap — 2026-05-16 → 2026-06-04 (cutover + paper-trade + live + 7-day monitor + post-cutover kickoff)
summary:
status: complete
nature: record
asset_group: [defi]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-12
locked_by: live-defi-rollout
locked_since: 2026-05-12
estimate_class: design
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 2.4
effective_concurrent_slots: 1
parent_epic: defi_master
assigned_vm: vm-defi
priority: P2
---

# Post-freeze roadmap — 2026-05-16 → 2026-06-04

> **Why this exists**: gap-filler between high-level master plan
> ([`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) — what + why) and day-of work-splits
> (`work_split_<YYYY_MM_DD>_<side>.md` — slot × theme). This roadmap = per-cycle skeleton mapping 8 slots × 2 sides
> across 3 cycles to canonical phase plans. **Paste-ready prompts get drafted day-of** when actual state is known
> (current cycle's shipments shape what each post-freeze slot owns).
>
> **Cycle structure** (post 2026-05-15 Phase 1 freeze gate):
>
> - **Cycle 2 (2026-05-16 → 2026-05-19, 4 days)** — bucket migration + cutover execution per `code_freeze` Phase 2.6
>   5-step sub-sequence
> - **Cycle 3 (2026-05-20 → 2026-05-22, 3 days)** — paper-trade smoke + batch-vs-live recon + ratchet lock-in per
>   `manifest_schema_final_gate` Phase 12
> - **Cycle 4 (2026-05-23, 1 day)** — operator-triggered live wallet enable + 7-day-monitor START per
>   `manifest_schema_final_gate` Phase 13 + master plan G23
> - **Cycle 5 (2026-05-24 → 2026-05-30, 7 days)** — live monitor + 7-day continuous-run gate (Phase 13.B done-def).
>   Bug-fix-only mode; no new feature work. Plan archives to `complete` if 7-day clean.
> - **Cycle 6 (2026-05-31 → 2026-06-04, 4 days)** — post-cutover backlog kickoff. Return-to-normal cycle cadence;
>   deferred plans unblock. Beyond Cycle 6 = steady state daily work-splits (no more roadmap-level planning needed).

## Cycle 2 — bucket migration + cutover execution (2026-05-16 → 2026-05-19)

**Theme**: Phase 2.6 cutover window per `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2 + slot 3's
2026-05-12 dry-run runbook. 5-step sequence: **provision → rsync → write-pause → delegate-flip → archive**. Per-day:

| Day | Date       | Phase             | Critical-path action                                                                                                                                                                                                       |
| --- | ---------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 2026-05-16 | **Provision**     | ~300-400 buckets across both clouds × 3 envs (prod / staging / dev). GCP `asia-northeast1` + AWS `ap-northeast-1`. Idempotent. Operator authorizes via slot 1 (ADC admin perms; bucket creation is not on hard-stop list). |
| 2   | 2026-05-17 | **Rsync**         | Storage Transfer Service (GCP) + AWS DataSync (AWS). Drift verification ≤0.01%. Same-region $0 egress. Sample-read each layout.                                                                                            |
| 3   | 2026-05-18 | **Write-pause**   | All Group-A continuously-running services (MTDS + instruments-service) paused. Operator-triggered. ~30 min window.                                                                                                         |
| 3   | 2026-05-18 | **Delegate-flip** | 36 consumers of `get_bucket_name`-style legacy delegate flip to `resolve_bucket_name` (Done-def #3 deferred from Phase 1 freeze gate per bucket_name_ssot § A6). All within the write-pause window.                        |
| 4   | 2026-05-19 | **Archive**       | Old flat buckets archived (not deleted — preserved for 30d). Manifest re-sync post-data-sync via Phase 0h script. Write-resume.                                                                                            |

**Per-slot allocation (both sides, 7 implementer slots × 2 sides = 14 slots)**:

| Slot | Ikenna theme                                                                                                              | Harsh theme                                                                                                               |
| ---- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| 1    | Main orchestrator + cutover-runbook execution governance                                                                  | Main orchestrator + per-service write-pause coordination                                                                  |
| 2    | Phase 2.6 day-1 provisioning runs (`gcloud storage buckets create` + AWS equivalent)                                      | Phase 2.6 day-2 rsync runs (Storage Transfer Service + DataSync)                                                          |
| 3    | code_freeze Phase 2 cutover-runbook live (run + verify each step)                                                         | Phase 2.6 day-3 write-pause + delegate-flip orchestration                                                                 |
| 4    | api_keys_wallets Phase 4-5 (Copper KYB closure + Fireblocks integration — depends on R9 operator gate from Cycle 1)       | defi_simulation_realism Phase 7 (matching-engine integration) + per-AMM connector backfills                               |
| 5    | defi_recursive_borrow Phase 3-4 (sim contract integration + per-family backtest scenarios)                                | risk + DR Phase 8-9 (real-VM rule-fire suite + cutover gate)                                                              |
| 6    | defi_simulation_realism Phase 4-5 (matching-engine integration + multi-hop routing)                                       | cross_cutting Phase 5-6 (post-cutover deliverables + UI polish) + manifest Phase 4-5 (post-cutover consumer verification) |
| 7    | simulation_scenarios Phase 3-4 (scenario-runner + per-scenario test fixtures)                                             | mock_data_pipeline_benchmarking Phase 2-3 (post-cutover benchmark harness validation)                                     |
| 8    | cross_cutting Phase 7 (DART manual surfaces post-cutover validation) + master plan Group F/G refresh per cutover progress | cross_asset_group_catalogue_audit follow-ups + per-asset_group catalog post-migration verification                        |

**Key milestones**:

- **2026-05-16 EOD**: all buckets provisioned (Ikenna-2 + Harsh-2 sign off). Slot 1 verifies via `gcloud storage ls` +
  `aws s3 ls`.
- **2026-05-17 EOD**: rsync ≤0.01% drift verified per layout (Harsh-2 + Ikenna-3). Master plan Group D #13
  `Last verified` flips to 2026-05-17.
- **2026-05-18 EOD**: write-pause window closed clean. Delegate-flip lands across 36 consumers in one bundled push
  (Harsh-3 + Ikenna-3 cross-coordinate).
- **2026-05-19 EOD**: archive complete. Manifest re-sync executed. Write-resume verified across 21+ services. Cycle 2 ✅
  DONE.

**Cross-side handshakes**:

- **Day 1**: Ikenna-2 provisions → Harsh-2 rsyncs. Provisioning artefact (per-bucket creation log) handed off EOD.
- **Day 3**: write-pause coordination is full-workspace — 5-min p99 latency on operator-triggered pause across 7
  services. Slot 1 + Harsh-1 jointly own.
- **Day 4**: archive + manifest re-sync — Ikenna-3 owns the run, Harsh-3 verifies cross-cloud parity.

**Day-of prompt drafting**: 2026-05-15 EOD (end of current cycle), main orchestrators (Ikenna slot 1 + Harsh slot 1)
draft paste-ready continuation prompts based on actual end-of-cycle-1 state. Format: same as
`continuation_prompts_2026_05_12.md` / `_harsh.md`.

## Cycle 3 — paper-trade smoke + batch-vs-live recon + ratchet lock-in (2026-05-20 → 2026-05-22)

**Theme**: `manifest_schema_final_gate_2026_05_09.md` Phase 12.A + 12.B + 12.C — parallel.

| Day | Date       | Phase                                | Critical-path action                                                                                                                                                                                                               |
| --- | ---------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 2026-05-20 | **12.A — Paper-trade smoke kickoff** | `carry_staked_basis` + `leveraged_funding_arb` archetypes run on testnet against post-Phase-11 features. Strategy / risk / position / alerting / reconciliation wired identically to live shape. STARTED + ≥1 progress event/hour. |
| 2   | 2026-05-21 | **12.B — Batch-vs-live recon**       | Run `batch_live_reconciler` (UTL@908b1647 helper, shipped Cycle 1). Compare batch P&L vs live P&L over the paper-trade window. **Delta < 5bps tolerance** (master plan F21).                                                       |
| 3   | 2026-05-22 | **12.C — Ratchet lock-in**           | `measure-honest-coverage.py` re-runs against post-backfill manifest. Lock ratchet in `/codex/02-data/honest_coverage_baseline_2026_05.md` with ±0.5pp tolerance + monthly cadence + 99% floor.                                     |

**Per-slot allocation**:

| Slot | Ikenna theme                                                                                        | Harsh theme                                                                             |
| ---- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| 1    | Main orchestrator + paper-trade event-stream monitoring + recon dashboard ownership                 | Main orchestrator + per-service paper-trade adapter health + alert response             |
| 2    | Paper-trade smoke harness kickoff (carry_staked_basis variant)                                      | Paper-trade smoke harness kickoff (leveraged_funding_arb variant)                       |
| 3    | Batch-vs-live reconciler runs + delta tracking                                                      | Per-asset_group recon decomposition (cefi / defi / tradfi / sports / prediction parity) |
| 4    | Ratchet lock-in measurement + codex baseline doc                                                    | Per-service ratchet floor verification (21+ services × 99% floor check)                 |
| 5    | Anomaly triage (any divergence > 5bps surfaces here)                                                | Anomaly fix-cycle (re-run after fix; <5bps gate verified)                               |
| 6    | DART manual-trade gate visualization smoke (master plan G23)                                        | UI surface smoke (deployment-UI live-data-status / risk / kill-switch tabs)             |
| 7    | Alerting rule firing verification (44 LIVE_ALERT_RULES + 6 new AlertCodes from slot-7 Cycle-0 ship) | Circuit-breaker arming smoke (20 BreakerConfig × 2 archetypes + 11 KillSwitchIds)       |
| 8    | Master plan Group F/G `Last verified` refresh per item per day                                      | Cross_asset_group catalogue final pre-cutover audit + signoff                           |

**Key milestones**:

- **2026-05-20 EOD**: paper-trade smoke ✅ STARTED. Event-stream landing per archetype. No 🟡 BLOCKED on adapter health.
- **2026-05-21 EOD**: recon delta < 5bps green. If not green → operator decision: fix-cycle (extend to 2026-05-22 PM) OR
  scope-cut.
- **2026-05-22 EOD**: ratchet locked. All master plan Group F items with `Last verified` flipped to 2026-05-22. Cycle 3
  ✅ DONE. Live-readiness pre-flight green per master plan G23 DART manual-trade gate.

**Cross-side handshakes**:

- **Day 1**: archetype kickoff is independent per side; cross-side parity check Day 1 EOD.
- **Day 2**: recon Δ — joint owner. If Δ > 5bps either side, both main orchestrators escalate.
- **Day 3**: ratchet codex doc — Ikenna-side ships canonical; Harsh-side verifies per-service.

**Day-of prompt drafting**: 2026-05-19 EOD, main orchestrators draft paste-ready continuation prompts based on actual
Cycle 2 cutover-completion state.

## Cycle 4 — live cutover (2026-05-23, single day)

**Theme**: `manifest_schema_final_gate_2026_05_09.md` Phase 13 + master plan G23.

| Time    | Phase                                           | Critical-path action                                                                                                                                                                 |
| ------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| AM      | **13.A — Operator triggers live wallet enable** | `carry_staked_basis` + `leveraged_funding_arb` arming on real wallet. ≥7 continuous days monitor START. Hard-stop list item: operator-only action; no agent runs this.               |
| PM      | **13.B — Banner removal + status flip**         | Banner removal across all `plans/active/*.md` Phase-0 bannered plans. Status flip on manifest_schema_final_gate plan from `active` → `complete` once 7-day continuous run validates. |
| All day | **Monitor**                                     | Slot 1 (both sides) full-attention monitoring. Event streams, P&L, alerts, kill-switch readiness. No new feature work; bug fixes only.                                               |

**Per-slot allocation** (Day-1 of live; Cycle 4 day):

| Slot | Both sides                                                                        |
| ---- | --------------------------------------------------------------------------------- |
| 1    | Main orchestrator + on-call governance + live-status dashboard ownership          |
| 2-3  | Anomaly response + same-day bug-fix cycle                                         |
| 4-5  | Per-archetype live-monitor (real wallet P&L, position drift, recon-vs-batch live) |
| 6-7  | Per-venue health monitoring (Aave + Hyperliquid + cefi perp venues)               |
| 8    | Operator-UX support + DART manual-trade gate live UI verification                 |

**Key milestones**:

- **AM**: live wallet armed. STARTED event emitted. Master plan G23 manual-trade gate ✅.
- **EOD 1**: ≥4-hour clean run. No 🟡 BLOCKED. ≤1 amber. 7-day monitor counter starts.
- **EOD +7d** (2026-05-30): if 7-day continuous run validates → manifest_schema_final_gate plan flips to `complete`.
  Live trading is the new steady state.

**Day-of prompt drafting**: 2026-05-22 EOD, both sides draft single-day Cycle 4 prompt — much shorter than typical (live
monitor, not feature work).

## Cycle 5 — live monitor + 7-day continuous-run gate (2026-05-24 → 2026-05-30)

**Theme**: `manifest_schema_final_gate_2026_05_09.md` Phase 13.B done-def — "≥7 continuous days" gate. Plan archives to
`complete` once this gate closes clean. **No new feature work; bug fixes + incident response only**. Master plan G23
DART manual-trade gate stays armed for operator review.

| Day | Date                    | Mode                                                                                                                                                                                |
| --- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 2026-05-24              | Day-1 of 7-day monitor. Full-attention slot 1 ownership both sides. Anomaly response cycle stays hot.                                                                               |
| 2-6 | 2026-05-25 → 2026-05-29 | Monitor + bug-fix-only. P&L reconcile daily. No new features. Reserve list pickup if slots idle, but bug-fix has priority.                                                          |
| 7   | 2026-05-30              | Gate evaluation: if 7-day clean → `manifest_schema_final_gate` plan flips `active` → `complete`; live trading is the new steady state. If anomalies → extend monitor + re-evaluate. |

**Per-slot allocation (both sides)** — same shape as Cycle 4 (live cutover day):

| Slot | Both sides                                                              |
| ---- | ----------------------------------------------------------------------- |
| 1    | Main orchestrator + live-status dashboard + incident triage             |
| 2-3  | On-call bug-fix cycle + reconciliation anomaly response                 |
| 4-5  | Per-archetype live-monitor (real wallet P&L drift, recon-vs-batch live) |
| 6-7  | Per-venue health monitoring + connector failure response                |
| 8    | Operator-UX support + DART manual-trade gate live UI maintenance        |

**Done-def**: 7-day continuous run validates → `manifest_schema_final_gate_2026_05_09.md` → `complete`. Live trading is
steady-state.

**Hard-stops**: anything affecting live wallet keys, custody endpoint config, or kill-switch arming = operator-only.

**Day-of prompt drafting**: 2026-05-23 EOD (end of Cycle 4 cutover day), both sides draft Cycle 5 monitor cadence — much
shorter prompts than feature cycles (just "monitor + respond + log").

## Cycle 6 — post-cutover backlog kickoff (2026-05-31 → 2026-06-04, first 4-day cycle of steady state)

**Theme**: return to normal cycle cadence with **post-cutover backlog**. Plans deferred during freeze + cutover unblock.
Live trading runs in parallel; this cycle covers feature work that wasn't critical-path to May-23.

**Eligible plans** (frontmatter `deadline:` ≥ 2026-05-24 OR explicitly deferred to post-cutover):

- `wave2_polymarket_record_captured_from_counts_2026_05_09` (deadline 2026-06-15)
- `simulation_scenarios_post_cutover_2026_06_01` (deadline 2026-07-15)
- `promote_workflow_post_cutover_ui_pipeline_2026_05_10` (post-cutover deliverable)
- `expected_universe_v2_design_2026_05_08` enumerator implementation (was BLOCKED on v8 schema; v8 lands Cycle 1)
- `client_reporting_pnl_attribution_mvp_2026_05_10` (Group F item 22; if not pulled forward by Cycle 1-3 reserve)
- `wallet_treasury_client_flow_2026_05_10` (Group F item 19; same)
- `mock_data_pipeline_benchmarking_2026_05_10` (backtest data prereq; same)
- `cross_asset_group_catalogue_audit_2026_05_10` (per-asset_group; ~31 calibrated; if not pulled forward)
- `codex_vs_citadel_infrastructure_audit_2026_05_10` (~15.6 calibrated; hygiene)
- DeFi Family 3+ archetypes (post-Family 1+2 cutover stability)
- per_agent_worktrees Phase 4.5 P1 (R1/R2/R3 ping-doc reset + Ikenna migration to per-slot files; if not picked up
  earlier)
- DefiManifestRecorder ManifestFreshnessCache wire-in (if not picked up earlier as scope-extension)

**Per-slot allocation**: 7 implementer slots × 2 sides assigned to eligible plans per pickup precedence in current
work-split. Same density-push principle (3.5-4 AI-days/slot/day) since pace is now well-validated.

**Cross-cycle dependencies**:

- Live trading takes operator priority — if Cycle 5 7-day monitor reveals issues, Cycle 6 themes may shift to
  remediation before backlog pickup.
- Cycle 6 is the **first cycle where "feature freeze" no longer applies** — new schema additions / refactors are fair
  game post-`manifest_schema_final_gate` archival.

**Beyond Cycle 6**: workspace returns to "steady state" cadence — daily work-splits per CLAUDE.md "Daily Work-Split
Process" without freeze-gate / cutover constraints. Per-plan deadlines (e.g. 2026-06-15 wave2, 2026-07-15 simulation
post-cutover) drive scheduling. Roadmap-level planning at this granularity ends Cycle 6; subsequent cycles are per-day
work-split-driven.

**Day-of prompt drafting**: 2026-05-30 EOD (end of Cycle 5 live-monitor 7-day gate), both sides draft Cycle 6 themes
based on (a) post-cutover priority backlog (with operator input on which deferred plans go first) and (b) whatever
remediation Cycle 5 surfaced.

## Day-of prompt drafting cadence (post-2026-05-15)

| Cycle | Drafted on     | By                                   | Output                                                                                                                    |
| ----- | -------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| 2     | 2026-05-15 EOD | Ikenna slot 1 + Harsh slot 1 (joint) | `work_split_2026_05_16_*.md` + `continuation_prompts_2026_05_16_*.md`                                                     |
| 3     | 2026-05-19 EOD | Same                                 | `work_split_2026_05_20_*.md` + `continuation_prompts_2026_05_20_*.md`                                                     |
| 4     | 2026-05-22 EOD | Same                                 | `work_split_2026_05_23_*.md` + `continuation_prompts_2026_05_23_*.md`                                                     |
| 5     | 2026-05-23 EOD | Same                                 | `work_split_2026_05_24_*.md` + `continuation_prompts_2026_05_24_*.md` (monitor-only; shorter prompts than feature cycles) |
| 6     | 2026-05-30 EOD | Same                                 | `work_split_2026_05_31_*.md` + `continuation_prompts_2026_05_31_*.md` (post-cutover backlog return-to-normal cadence)     |

**Why deferred drafting**: each cycle's actual shipments shape what the next cycle's slots own. Drafting at cycle-end
captures the actual state (✅ DONE / ⚪ PARTIAL / 🟡 BLOCKED scoreboard) into the next cycle's carry-forward.

## Reserve plans (Cycle 2-4 pickup precedence if a slot closes early)

Same precedence as `work_split_2026_05_12_ikenna.md` § Reserve list:

1. `client_reporting_pnl_attribution_mvp_2026_05_10` (~6.5 calibrated)
2. `wallet_treasury_client_flow_2026_05_10` (~8.8 calibrated)
3. `mock_data_pipeline_benchmarking_2026_05_10` (~7.0 calibrated)
4. `cross_asset_group_catalogue_audit_2026_05_10` (~31.2 calibrated; can fan out)
5. `codex_vs_citadel_infrastructure_audit_2026_05_10` (~15.6 calibrated; hygiene)
6. expected_universe_v2 enumerator implementation (post 2026-05-15 freeze)

## Hard-stops (operator-only actions through Cycle 4)

Per CLAUDE.md "Plans Run To Actual Completion" § Operator authority + ADC. Operator (NOT agents) does:

- Live wallet enable (Cycle 4 13.A)
- Custody endpoint approvals (Copper / CEFFU / Fireblocks; Cycle 2 day-1)
- Force-push to main / 1.0.0 version graduation (none scheduled, but if needed)
- Live-trading kill-switch arming
- Wallet private keys

Everything else (bucket provisioning, VM launches, data migration, manifest re-sync, paper-trade adapter wiring, recon-Δ
measurement) is agent-runnable with ADC admin perms.

## Composes with

- [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) — the umbrella; this roadmap is the per-cycle
  skeleton beneath it.
- [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md) §
  Phase 2.6 cutover sub-sequence — Cycle 2 SSOT.
- [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) § Phase 12 + Phase 13 — Cycle
  3 + Cycle 4 SSOT.
- [`bucket_name_ssot_canonicalisation_2026_05_10.md`](bucket_name_ssot_canonicalisation_2026_05_10.md) § A5 + A6 —
  bucket aliases + Done-def #3 cutover-deferral context.
- [`work_split_2026_05_12_ikenna.md`](../archive/2026_05/work_split_2026_05_12_ikenna.md) +
  [`work_split_2026_05_12_harsh.md`](../archive/2026_05/work_split_2026_05_12_harsh.md) — Cycle 1 (current); the
  predecessor this roadmap continues from.
- CLAUDE.md § "Daily Work-Split Process" + § "Per-Tab Worktrees" + § "Plans Run To Actual Completion" — workflow rules
  this roadmap operates under.

## Deferred work — migrated to:

All roadmap phases completed or superseded by day-of work-splits. No deferred items — all execution milestones are
tracked in their respective epic plans and active plans. Archiving 2026-05-23.
