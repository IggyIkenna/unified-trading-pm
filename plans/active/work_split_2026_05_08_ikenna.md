---
title: Ikenna's daily work-split — 2026-05-08 (15 days to live-DeFi)
type: coordination-doc
status: active
created: 2026-05-08
deadline: 2026-05-23 (live DeFi)
horizon: 1-day cycle (rolls forward EOD)
companion_to: plans/active/work_split_2026_05_08_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Ikenna's daily work-split — 2026-05-08

> **Companion**: [`work_split_2026_05_08_harsh.md`](work_split_2026_05_08_harsh.md). Cross-side handshakes appear in
> both plans (mirror-image entries). The other side's plan is read-only for you.
>
> **Methodology**: see [`cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) §"Daily Work-Split Process" for the
> full spec — split principle, working models, universal mechanics (shared working tree, conditional push,
> plan-of-record Q&A bus, ping ledger, sub-agent fan-out, daily reset). This doc is today's specific load-balancing
> decision; the spec is the durable rules.

## Why this split exists today

- **15 days to live-DeFi cutover** (2026-05-23). Master plan
  [`master_to_live_defi_2026_05_23`](master_to_live_defi_2026_05_23.plan.md) Group F (live-only prerequisites) + Group G
  (operator UX) are now the gating ladder. DeFi launches that started 2026-05-07 hit silent-zero regressions (Bug 1 AAVE
  V3 ETHEREUM root-caused as UAC SSOT drift; Tab 14 audit found 13 of 17 probed `(chain, protocol)` pairs have similar
  drift).
- **Yesterday's Ikenna 5-tab layout finished** with Tabs 1-5 done-definitions met (alerting Phase 1, writegate Phase 4.A
  typed-error rendering, expected-universe enumerator `--apply-write` 1.4M rows, defi_archetypes_canonicalisation
  triage, master plan refresh). Carryover into today: alerting Phase 2-9, writegate Phase 2.A residual + Phase 5
  ratchet, defi_master Fork 1 deferred items + Tab 14 4 fix sub-tabs A/B/C/D, paper-trade smoke completion.
- **New incoming overnight**: 4 plans landed 2026-05-07 → 2026-05-08 from cross-cutting scope:
  [`live_pipeline_mtds_mdps_features_2026_05_08`](live_pipeline_mtds_mdps_features_2026_05_08.plan.md) (14 phases),
  [`gcs_migration_bundle_pipeline_mode_2026_05_08`](gcs_migration_bundle_pipeline_mode_2026_05_08.plan.md) (overnight
  migration of millions of parquets),
  [`features_repo_consolidation_2026_05_08`](features_repo_consolidation_2026_05_08.plan.md) (8 repos → 1, deadline
  2026-05-13), [`hard_schema_enforcement_2026_05_08`](hard_schema_enforcement_2026_05_08.plan.md) (under
  infrastructure_master). Live-pipeline + gcs-migration are cross-cutting / migration / governance = Ikenna-side;
  features-repo-consolidation + hard-schema are mechanical = Harsh-side per split principle.
- **Ping ledger (overnight)**: 1 entry — `ml-features-phase2a-tab` Q1 🟡 BLOCKED [ESCALATED-TO-OPERATOR] strategic scope
  ambiguity. That's a Harsh-side ping; Ikenna doesn't pick up.

## Working model

**Model A — fixed thematic 5-tab clustering.** The day's work clusters cleanly into 5 themes (DeFi launch,
live-pipeline, GCS migration, AWS migration + governance, master refresh + alerting) so 5 fixed tabs absorb the load.
Each tab runs Opus at full window with sub-agent fan-out for mechanical multi-file work. Tabs run to their
done-definition, not a calendar end-of-day — agents finish faster than humans.

## Coverage guarantee — 5 tabs absorb today's Ikenna-side scope

| Source                                                | Item                                                                                                                                | Tab |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | --- |
| `defi_master_2026_05_07`                              | Fork 1 paper-trade smoke completion (carry_staked_basis Solana hedge end-to-end)                                                    | 1   |
| `defi_master_2026_05_07`                              | Lending-indices VM relaunch (post-Tab 5 + Tab 9 fixes; Bugs 2 + 3 still pending)                                                    | 1   |
| `defi_master_2026_05_07` + Tab 14 audit               | UAC `PROTOCOL_LAUNCH_DATES` drift fix sub-tabs A/B/C/D (13 of 17 (chain, protocol) pairs flagged 2026-05-07)                        | 1   |
| `defi_master_2026_05_07` Stream A                     | DERIBIT/BYBIT/OKX ETH-LST collateral acceptance flips (live-API probe + UAC venue_collateral.py + codex doc)                        | 1   |
| Pyth Hermes archive backfill                          | jitoSOL 2022-11 → 2023-10 11-month coverage gap (carry_staked_basis Solana leg historical)                                          | 1   |
| `live_pipeline_mtds_mdps_features_2026_05_08`         | Phase 0 audit + Phase 1-3 MTDS standalone cluster + Phase 4-6 MDPS+features-asset-scoped colocated + Phase 7 features-cross-cutting | 2   |
| `live_pipeline_mtds_mdps_features_2026_05_08`         | Phase 8 replay subsystem + Phase 9 CANDLE_BOUNDARY_CROSSED Redis Stream cascade + Phase 10 instrument lifecycle                     | 2   |
| `live_pipeline_mtds_mdps_features_2026_05_08`         | Phase 11 ServiceEmissionPolicy consumer wiring (slice b/c following 2026-05-08 morning slice a)                                     | 2   |
| `writegate_honest_coverage_endtoend_2026_05_06`       | Phase 5 workspace QG honest-coverage % gate + per-(asset_group, data_type) ratchet schedule                                         | 2   |
| `gcs_migration_bundle_pipeline_mode_2026_05_08`       | Phase 0-7 overnight migration of millions of parquets (deadline 2026-05-15)                                                         | 3   |
| `manifest_migration_master_2026_05_07`                | Stage 4 cross-asset rescan post-CeFi VM drain (Harsh-side runs the rescan; Ikenna designs the schema flip)                          | 3   |
| `expected_universe` v2 enumerator                     | Cross-bucket join with instruments-service catalog (Phase 3.D.4 v2 deferred from 2026-05-07)                                        | 3   |
| `manifest_migration_master_2026_05_07` + infra_master | v6 → v7 manifest schema migration design (post-writegate Phase 5 ratchet)                                                           | 3   |
| `aws_migration_defi_first_2026_05_07`                 | Phase 2 dual-bucket setup + Storage Transfer Service config + UCI bucket-naming SSOT discipline                                     | 4   |
| `aws_migration_defi_first_2026_05_07`                 | `codex/05-infrastructure/cloud-agnostic-script-pattern.md` SSOT population                                                          | 4   |
| `aws_migration_defi_first_2026_05_07`                 | Phase 3 cross-cloud parity smoke (CLOUD_PROVIDER=aws read-path on DeFi shards)                                                      | 4   |
| `alerting_service_live_rules_2026_05_07`              | Phase 2 KillSwitchBus rule wiring + `CROSS_CLOUD_EGRESS_DETECTED` rule + AAVE utilization-spike threshold                           | 5   |
| `alerting_service_live_rules_2026_05_07`              | Phase 3-9 paging targets + DART terminal wiring + rehearsal procedure                                                               | 5   |
| `master_to_live_defi_2026_05_23`                      | Group F items 17-22 refresh (operational-validation; 2-year batch run; Copper + CEFFU treasury; live testnet replicating prod)      | 5   |
| `master_to_live_defi_2026_05_23`                      | Group G item 23 (DART manual-trade gate; 6-persona Playwright matrix gate)                                                          | 5   |
| `deploy_missing_auto_launch_2026_05_07`               | Phase 0 IAM scope + audit-log + rate-limit operator decisions (review draft → sign-off → propagate)                                 | 5   |

**21 items / 5 tabs / 0 dropped.**

## AI-day estimate (per tab, summed across the cycle)

| Tab                         | Theme                                  | Items                                                                                                                        | AI-days |
| --------------------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------- |
| 1                           | DeFi launch (Fork 1 + UAC drift fixes) | Paper-trade smoke + lending-indices relaunch + 4 UAC drift sub-tabs + Stream A LST collateral + Pyth Hermes archive backfill | ~12     |
| 2                           | Live pipeline + writegate Phase 5      | 14-phase live_pipeline plan (cross-cutting MTDS + MDPS + features) + ratchet + Redis Stream cascade                          | ~12     |
| 3                           | GCS migration + manifest cluster       | Overnight bundle migration + Stage 4 rescan + expected_universe v2 + v6→v7 schema design                                     | ~10     |
| 4                           | AWS migration + cloud-agnostic         | Phase 2 dual-bucket + Phase 3 parity smoke + UCI SSOT + codex page                                                           | ~6      |
| 5                           | Alerting + master refresh + governance | Alerting Phase 2-9 + master Group F+G refresh + deploy_missing Phase 0 IAM/audit-log/rate-limit                              | ~10     |
| **Total Ikenna-side cycle** |                                        | **~50**                                                                                                                      |

5 parallel agents × ~10 days solo = ~50 ai-days, fitting the CLAUDE.md "size to 25-50 AI-days per side per cycle"
target. **Err on the side of beefier scope**; we can do less of a beefy plan over time, can't add scope retroactively to
a thin one.

---

## TAB 1 — DeFi launch + Fork 1 completion

**Identity**: you own the May-23 DeFi critical path end-to-end. Trading-judgment thread runs through every item: launch
decisions, drift-fix sequencing, paper-trade interpretation, custody integration. Highest collision risk with Harsh's
per-asset_group VM ops cluster (Tab 4 there) — coordinate via the cross-side handshake "DeFi VM relaunches".

**Plan-of-record**: [`defi_master_2026_05_07.plan.md`](defi_master_2026_05_07.plan.md) (Fork 1 + Bug fixes + Stream A +
Pyth Hermes) +
[`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.plan.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.plan.md)
(Stream A LST collateral) + [`master_to_live_defi_2026_05_23.plan.md`](master_to_live_defi_2026_05_23.plan.md) Group F.

**Scope (6 items, P0-P1)**:

- [ ] [TRADING+INTEGRATION] P0. **Paper-trade smoke completion (carry_staked_basis Solana hedge)** — execution-service +
      strategy-service + position-balance-monitor-service end-to-end round-trip. Pre-flight checks shipped 2026-05-08
      (Pyth Hermes endpoint reachable HTTP 200 in 2.3s); blocked yesterday on (a) MTDS@d19d76c VMs drain + (b)
      features-onchain Docker rebuild + (c) 4-service QG passes. Today: verify drain status of
      `mtds-{vault-share-price,lst-rates,gas-fees}-20260508-010{050,105,121}` VMs first; if drained green, proceed with
      smoke. **Done**: paper fill lands in execution-service, position-balance-monitor reflects open position,
      strategy-service P&L attribution computed (no execution-alpha conflation per CLAUDE.md "Batch = Live"). ~3
      AI-days.
- [ ] [TRADING] P0. **Lending-indices VM relaunch (Bug 2 + Bug 3)** — Tab 9 yesterday verified Bug 1 (UAC SSOT fix
      end-to-end at AAVEV3 ETHEREUM 2023-01-27 captured rows). Bugs 2 (Compound V3 schema drift) + 3
      (instruments-store-defi 2022 metadata floor) per
      [`issues/lending_indices_handler_bugs_2026_05_07.md`](issues/lending_indices_handler_bugs_2026_05_07.md) still
      pending. Today: **fix both bugs end-to-end + relaunch + 90s STARTED + 10-15min progress + T+30min per-VM manifest
      spot-check**. Per CLAUDE.md "No fire-and-forget VM launches". ~2 AI-days.
- [ ] [DESIGN+UAC] P0. **4 UAC `PROTOCOL_LAUNCH_DATES` drift fix sub-tabs A/B/C/D** — Tab 14 yesterday found 13 of 17
      probed `(chain, protocol)` pairs have UAC SSOT drift (same shape as Tab 9's AAVEV3-ETHEREUM finding). Each sub-tab
      handles a cluster: **A** = Aave V3 multi-chain (BASE / LINEA / BSC / METIS / GNOSIS beyond ETHEREUM); **B** =
      Compound V3 multi-chain (ETHEREUM / ARBITRUM / BASE / OPTIMISM); **C** = Spark / Maker-spinoff lending; **D** =
      remaining suspects (any (chain, protocol) where UAC date pre-dates protocol's general-multi-chain rollout). For
      each: probe-verify the subgraph for earliest `*HistoryItems` event, flip
      `unified_api_contracts/canonical/crosscutting/chain_env.py:PROTOCOL_LAUNCH_DATES` to the correct value, add unit
      test, drop a top-of-file `🟡 IN-FLIGHT REFACTOR` banner per CLAUDE.md "Cross-Plan Coordination Banners" rule while
      landing. **Done**: all 13 pairs corrected + tested + Tab 14 audit doc updated to RESOLVED. ~3 AI-days.
- [ ] [DESIGN+UAC+CODEX] P0. **Stream A — DERIBIT/BYBIT/OKX ETH-LST collateral acceptance flips** — per
      [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.plan.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.plan.md)
      Stream A. Live-API probe to confirm exact 2026-05-07 collateral value ratios for Deribit stETH, Bybit
      stETH/wstETH/USDe/sUSDe, OKX wstETH/stETH. Document evidence in
      `unified-trading-pm/codex/14-playbooks/defi/venue-collateral-2026-05-07.md` (new doc). Update
      `unified-api-contracts/unified_api_contracts/registry/venue_collateral.py` matrix entries (5+ flipped rows; see
      plan body for full list). Add unit tests covering the flips. Update
      [`carry-staked-basis.md`](../../codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md) "Today's
      venue-collateral" section. ~2 AI-days.
- [ ] [TRADING+INFRA] P1. **Pyth Hermes archive backfill — jitoSOL 2022-11 → 2023-10 11-month gap** — Tab 14 audit found
      Pyth Hermes archive doesn't cover the early jitoSOL period needed for `carry_staked_basis` Solana leg historical
      training data + paper-trade smoke realism. Today: probe Hermes archive endpoint, identify the gap bound, design
      the backfill (archive paid plan? Pythnet RPC + index-into-historical? alternative source like Birdeye archive?),
      ship the backfill VM under `deployment-service/scripts/vm/launch-mtds-pyth-hermes-archive-backfill-vm.sh` with
      VM_PREFIX_TO_BUCKET registration + watchdog relaunch. ~2 AI-days.
- [ ] [TRADING] P1. **bSOL coverage gap fix in UAC `LST_TOKEN_GENESIS`** — Tab 14 audit found bSOL is in Fork 1 brief
      but NOT in UAC `LST_TOKEN_GENESIS`. Add it to the SSOT with verified genesis date (probe via Solana RPC). ~0.5
      AI-days.

**Repos owned (collision boundary)**: MTDS (DeFi adapters + lending-indices handler — collides with Harsh Tab 4 only on
lending_indices_handler.py if Bug fixes overlap; coordinate timing), execution-service + strategy-service +
position-balance-monitor-service (paper-trade smoke), deployment-service `scripts/vm/launch-defi-*`

- `launch-mtds-pyth-hermes-archive-backfill-vm.sh` (new), UAC `chain_env.py:PROTOCOL_LAUNCH_DATES` +
  `venue_collateral.py` + `LST_TOKEN_GENESIS`, codex (`14-playbooks/defi/venue-collateral-2026-05-07.md`,
  `09-strategy/architecture-v2/archetypes/carry-staked-basis.md`).

**Read-first**:

- CLAUDE.md sections: "DeFi Execution Architecture", "Pyth — UNBANNED 2026-05-06", "Cross-Plan Coordination Banners",
  "VM tarball deployment", "VM Naming Convention", "No fire-and-forget VM launches"
- [`plans/active/defi_master_2026_05_07.plan.md`](defi_master_2026_05_07.plan.md) (full body — long)
- [`plans/active/issues/lending_indices_handler_bugs_2026_05_07.md`](issues/lending_indices_handler_bugs_2026_05_07.md)
- [`plans/active/issues/defi_988_missing_dates_audit_2026_05_08.md`](issues/defi_988_missing_dates_audit_2026_05_08.md)
- [`plans/active/issues/defi_fork1_prep_audit_2026_05_08.md`](issues/defi_fork1_prep_audit_2026_05_08.md) (Tab 14
  output: 13 of 17 pairs drift)
- [`plans/active/master_to_live_defi_2026_05_23.plan.md`](master_to_live_defi_2026_05_23.plan.md) Group F+G

**Sub-agent fan-out**:

- Item 1 (paper-trade smoke): 4 parallel sub-agents — (a) execution-service Pyth oracle read + Solana RPC reachability,
  (b) strategy-service archetype config validation, (c) position-balance-monitor wallet + custody adapter health, (d)
  MTDS post-drain shard inspection. Master runs the integrated round-trip after all 4 green.
- Item 3 (4 UAC drift fix sub-tabs): 4 parallel sub-agents in ONE message — one per cluster A/B/C/D. Each probes its
  cluster's subgraphs, flips dates, ships test + banner. Master merges.
- Item 4 (Stream A): 3 parallel sub-agents — (a) Deribit + Bybit live-API probe, (b) OKX live-API probe, (c) USDe/sUSDe
  metadata research. Master writes the codex evidence doc + UAC flip + tests.
- Item 5 (Pyth archive): one Explore sub-agent to scope alternatives (Pythnet RPC + index, Birdeye archive paid, manual
  Solana RPC walk). Master picks + ships.

**Collision risk**:

- MTDS `lending_indices_handler.py`: Harsh Tab 4 (per-asset_group VM ops) does NOT touch this file (just runs
  reconcilers). Zero overlap.
- UAC `chain_env.py`: Harsh Tab 5 (mechanical refactors) might touch UAC for `hard_schema_enforcement` or
  `cme_polymarket_arb` UAC additions but NOT `PROTOCOL_LAUNCH_DATES`. Zero overlap if scoped correctly; verify
  pre-commit `git diff --cached --name-only` shows only `chain_env.py` if you're flipping dates.
- `venue_collateral.py`: Stream A only. No collision.
- `carry-staked-basis.md` codex doc: Tab 5 (master refresh) might touch it via Group F refresh; coordinate timing — Tab
  1 ships its update first, Tab 5 pulls before its edit.

**Done definition**:

1. ✅ Paper-trade smoke green: end-to-end carry_staked_basis Solana trade lands a paper fill in execution-service,
   position-balance-monitor reflects open position + strategy P&L computed without execution-alpha conflation.
2. ✅ Lending-indices VM relaunched + STARTED + per-instrument INSTRUMENT_PROCESSED events with `rows_captured > 0` for
   AAVE V3 ETH (Bug 1 already fixed), Compound V3 (Bug 2 fixed), pre-launch dates correctly classified (Bug 3 fixed).
   T+30min per-VM shard spot-check ≥ 90% captured (not 100% empty_confirmed).
3. ✅ All 13 UAC drift pairs flipped with unit tests + IN-FLIGHT banners on flight, banners removed on land.
4. ✅ Stream A: 5+ venue_collateral.py rows flipped + tests green + codex evidence doc + carry-staked-basis.md updated.
5. ✅ Pyth Hermes archive backfill VM running + emitting events + sample shows captured rows for jitoSOL pre-2023.
6. ✅ bSOL added to UAC `LST_TOKEN_GENESIS` with verified date + test.
7. ✅ Plan checkboxes flipped per shippable unit across defi_master, defi_archetypes_canonicalisation, master plan Group
   F.

---

## TAB 2 — Live pipeline + writegate Phase 5 ratchet

**Identity**: you own the cross-cutting batch=live unification thread. Live-pipeline plan is 14 phases spanning MTDS +
MDPS + features-\* — the May-23 cutover model in code form. Writegate Phase 5 ratchet is the workspace QG gate that
prevents honest-coverage % regressions post-cutover. Both are governance-grade work.

**Plan-of-record**:
[`live_pipeline_mtds_mdps_features_2026_05_08.plan.md`](live_pipeline_mtds_mdps_features_2026_05_08.plan.md)

- [`writegate_honest_coverage_endtoend_2026_05_06.plan.md`](writegate_honest_coverage_endtoend_2026_05_06.plan.md)
  Phase 5.

**Scope (5 items, P0)**:

- [ ] [INFRA+DESIGN] P0. **Live pipeline Phases 0-3** — Phase 0 audit pass (pre-flight gap doc); Phase 1-3 MTDS
      standalone cluster (per-venue VM topology + connection pool + sharding-orthogonal). Per CLAUDE.md "ARCHITECTURE
      2026-05-08 — Live pipeline" auto-memory: MTDS standalone cluster + MDPS+features-asset-scoped colocated per
      asset_group + features-cross-cutting separate flavor. ~3 AI-days.
- [ ] [INFRA+DESIGN] P0. **Live pipeline Phases 4-7** — Phase 4-6 MDPS+features-asset-scoped colocated cluster (5
      asset_group flavors) + Phase 7 features-cross-cutting separate flavor. Pipeline_mode hive partition reading. Same
      parquet schema across batch + live. UAC SOURCE_PRIORITY fan-in. UTC midnight alignment. Service-start-order
      independence. ~3 AI-days.
- [ ] [INFRA+DESIGN] P0. **Live pipeline Phases 8-11** — Phase 8 replay subsystem (smooth handoff to live). Phase 9
      CANDLE_BOUNDARY_CROSSED + CANDLE_COMPUTED Redis Stream cascade. Phase 10 instrument lifecycle (event-publish +
      downstream cache-delta hot-reload, NOT a new stream). Phase 11 ServiceEmissionPolicy consumer wiring (slice b:
      manifest-read coupling; slice c: per-service emission policy migration — slice a shipped 2026-05-08 morning at
      UAC@58c3b61 + UTL@1a7e1d4b). ~3 AI-days.
- [ ] [INFRA+DESIGN] P1. **Live pipeline Phases 12-14** — Phase 12 alerting tier-up wiring circuit breakers. Phase 13
      4-category gap tree applied to live (stale-not-missing rule via ServiceEmissionPolicy.PUBLISHED_DEGRADED). Phase
      14 codex SSOT updates per the post-plan-phase codex audit HARD RULE. ~2 AI-days.
- [ ] [GOVERNANCE+DESIGN] P0. **Writegate Phase 5 — workspace QG honest-coverage % gate + per-(asset_group, data_type)
      ratchet schedule**. Per
      [`codex/02-data/honest_coverage_baseline_2026_05.md`](../../codex/02-data/honest_coverage_baseline_2026_05.md)
      (currently a stub, needs population). Writes: UTL helper that computes honest-coverage % per shard-key from the
      manifest; base-service.sh QG STEP that fails CI if a service's coverage drops > 0.5pp from baseline; ratchet
      schedule (monthly cadence, 99% floor) per CLAUDE.md "honest absence" methodology. ~1 AI-day.

**Repos owned (collision boundary)**: MTDS (live-mode wiring; collides with Tab 1 only on lending-indices — different
file paths), MDPS (`base_adapter.py` + `BaseCandleAdapter` + batch_workers — collides with **Harsh Tab 2 features + ML
wiring** if features-cefi/features-tradfi live in MDPS; coordinate via the cross-side handshake "MDPS files split
between Tab 2 [Ikenna live-pipeline] and Tab 2 [Harsh ml-features-phase2a]"), UTL (writegate ratchet helper +
ManifestFreshnessCache), base-service.sh (Phase 5 gate STEP), UAC `crosscutting/` for `SOURCE_PRIORITY` fan-in if
extending, all 5 features-\* repos (live-pipeline wiring; collides with **Harsh Tab 2 features_repo_consolidation** if
not coordinated — see cross-side).

**Read-first**:

- CLAUDE.md sections: "ARCHITECTURE 2026-05-08 — Live pipeline" (the architecture decision that drives this work),
  "Plans must capture full codebase impact upfront", "Post-Plan-Phase Codex Audit HARD RULE", "Service emission policy"
  (in Wave 4 slice a context), "Batch = Live: Unified Pipeline Architecture"
- [`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.plan.md`](live_pipeline_mtds_mdps_features_2026_05_08.plan.md)
- [`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.plan.md`](gcs_migration_bundle_pipeline_mode_2026_05_08.plan.md)
  (cross-cutting; pipeline_mode hive partition migration is the parallel half)
- [`codex/05-infrastructure/live-pipeline-architecture.md`](../../codex/05-infrastructure/live-pipeline-architecture.md)
- [`codex/05-infrastructure/replay-subsystem.md`](../../codex/05-infrastructure/replay-subsystem.md)
- [`codex/02-data/pipeline-mode-partition.md`](../../codex/02-data/pipeline-mode-partition.md)
- [`codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`](../../codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md)

**Sub-agent fan-out**:

- Phases 0-3: 4 parallel sub-agents — (a) Phase 0 audit doc; (b) Phase 1 per-venue VM topology; (c) Phase 2
  connection-pool design; (d) Phase 3 sharding-orthogonal verification across MTDS adapters.
- Phases 4-7: 5 parallel sub-agents per asset_group (cefi / defi / tradfi / sports / prediction MDPS+features colocated
  wiring) + 1 features-cross-cutting flavor. Master integrates.
- Phases 8-11: 4 parallel sub-agents — (a) replay subsystem; (b) Redis Stream cascade; (c) instrument lifecycle
  hot-reload (use existing ApiKeyReloader pattern); (d) ServiceEmissionPolicy consumer migration.
- Phase 5 ratchet: 1 general-purpose sub-agent to walk current manifest, compute per-(asset_group, data_type)
  honest-coverage %, populate baseline doc. Master writes the QG STEP + ratchet schedule.

**Collision risk**:

- **MDPS `base_adapter.py` / `BaseCandleAdapter`**: Tab 1 doesn't touch (DeFi adapters are different files). Harsh Tab 2
  (ml-features-phase2a) wires `assert_no_lookahead_for_feature_group` into compute calls — different layer, different
  files. **File-level overlap expected to be zero**. Per-commit pre-commit check (`git status` +
  `git diff --cached --stat` no path arg + `git add -p` for any shared file) is critical.
- **Features-\* 5+1 repos**: Harsh Tab 2 ships features_repo_consolidation (8 repos → 1). Live-pipeline Phase 4-7 wires
  the consolidated repo. **Hard sync gate**: features_repo_consolidation Phase 1-4 must land BEFORE live-pipeline Phase
  4-7. See cross-side handshake.
- **UTL `legacy_reason_classifier.py` + `ManifestFreshnessCache`**: shipped 2026-05-07; you wire consumers. No collision
  unless other agents add new helpers in the same module.

**Done definition**:

1. ✅ Phases 0-14 of live_pipeline plan flipped or with explicit "DEFERRED — see plan body" markers explaining why (per
   user direction "no deferreds" — actually ship every phase).
2. ✅ Writegate Phase 5 QG STEP active in base-service.sh; baseline doc populated with per-(asset_group, data_type)
   honest-coverage % numbers; ratchet schedule committed.
3. ✅ Plan flips per shippable unit + codex SSOTs updated per Post-Plan-Phase Codex Audit HARD RULE for every phase that
   lands a contract / pattern / SSOT change.

---

## TAB 3 — GCS migration + manifest cluster

**Identity**: you own the on-disk shape migration end-to-end. Pipeline_mode hive partition is the cross-cutting shape
decision (millions of parquets re-keyed). Manifest v6 → v7 is the schema evolution. Expected_universe v2 closes the
rollup-vs-drilldown denominator-divergence (codex SSOT codified 2026-05-07).

**Plan-of-record**:
[`gcs_migration_bundle_pipeline_mode_2026_05_08.plan.md`](gcs_migration_bundle_pipeline_mode_2026_05_08.plan.md)

- [`manifest_migration_master_2026_05_07.plan.md`](../epics/manifest_migration_master_2026_05_07.plan.md)
- [`writegate_honest_coverage_endtoend_2026_05_06.plan.md`](writegate_honest_coverage_endtoend_2026_05_06.plan.md) Phase
  3.D.4 v2 + [`infrastructure_master_2026_05_07.plan.md`](../epics/infrastructure_master_2026_05_07.plan.md) v6→v7
  schema.

**Scope (5 items, P0)**:

- [ ] [INFRA+MIGRATION] P0. **GCS migration Phase 0-3** — Phase 0 audit + Phase 1 dual-write enable on writers + Phase 2
      backfill replay tagging existing parquets with `pipeline_mode=batch` hive partition + Phase 3 consumer-read
      fallback shim deployment. Migration of millions of parquets is overnight; idempotent + resumable + per-shard
      checkpointed. ~3 AI-days.
- [ ] [INFRA+MIGRATION] P0. **GCS migration Phase 4-7** — Phase 4 reader migration (per-service consumer cutover) +
      Phase 5 fallback removal + Phase 6 reconciler verification + Phase 7 codex SSOT updates. **Done**: every consumer
      reads `pipeline_mode=batch|live` partition; no fallback paths; reconciler walks manifest + cross-checks bucket
      layout. Deadline 2026-05-15 per plan frontmatter. ~3 AI-days.
- [ ] [INFRA+MIGRATION] P0. **Manifest v6 → v7 schema migration design** — v6 added `pipeline_mode` column (overlap with
      GCS hive partition). v7 needs to formalise per-(shard_key, day) ServiceEmissionPolicy state column (ties to
      writegate Phase 4 typed-error rendering). Design doc + migration script + reader fallback strategy + codex SSOT
      update. **Done**: v7 schema + 1-time migration script (precedent
      `instruments-service/scripts/migrate_local_sfi_to_canonical.py`) + reader removal of v6 fallback per CLAUDE.md
      "Manifest migration, NOT fallback". ~2 AI-days.
- [ ] [INFRA] P0. **Expected_universe v2 enumerator** — v1 shipped 2026-05-07 (1.4M rows; CeFi + Prediction stubs now
      real impl per UAC@`ac218dc`). v2 = cross-bucket join with instruments-service catalog (catalog-aware expected
      universe; instrument lifecycle bounds applied at expected-row generation, not just write-side). Per writegate
      Phase 3.D.4 v2 deferred 2026-05-07. **Done**: v2 enumerator launches + writes per-VM shard + consolidator merges +
      every (catalog-alive instrument × applicable date × data_type) has a manifest row. ~1 AI-day.
- [ ] [INFRA+COORDINATION] P1. **Manifest cross-asset rescan post-CeFi VM drain** — Harsh Tab 4 runs the rescan itself
      (mechanical); Ikenna designs the rescan flip schema (which fields change, which fields stay) + handles
      operator-approval edge cases (any rows where rescan finds disagreement with manifest go to a triage file). ~1
      AI-day.

**Repos owned (collision boundary)**: instruments-service `scripts/enumerate_expected_universe.py` + per-VM launcher,
MTDS writers (pipeline_mode dual-write), all 5 features-\* readers, deployment-api manifest readers, data-status
readers, UTL `manifest_v7.py` (new module), all consumer services for the Phase 4 reader migration. Hands off the actual
rescan VM operation to Harsh Tab 4.

**Read-first**:

- CLAUDE.md sections: "Manifest migration, NOT fallback" rule, "Honest absence vs fake placeholders", "Per-VM shard
  isolation for concurrent backfills", "Manifest concurrency principle", "Manifest phantom audit"
- [`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.plan.md`](gcs_migration_bundle_pipeline_mode_2026_05_08.plan.md)
- [`plans/epics/manifest_migration_master_2026_05_07.plan.md`](../epics/manifest_migration_master_2026_05_07.plan.md)
- [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
- [`codex/02-data/pipeline-mode-partition.md`](../../codex/02-data/pipeline-mode-partition.md)
- [`codex/02-data/chunk-safe-manifest-migrations.md`](../../codex/02-data/chunk-safe-manifest-migrations.md)

**Sub-agent fan-out**:

- GCS migration Phases 0-3: 4 parallel sub-agents — (a) Phase 0 audit; (b) writer dual-write per asset_group; (c) Phase
  2 backfill replay; (d) Phase 3 reader fallback. Master coordinates handoff between phases.
- Phases 4-7: 5 parallel sub-agents per asset_group consumer cutover + 1 codex SSOT updater. Master removes the fallback
  in a final commit after all 5 cutovers verify.
- Manifest v7 design: 1 architecture sub-agent drafts the schema + migration script. Master reviews + ships.
- Expected_universe v2: 1 sub-agent extends the v1 enumerator with catalog-join. Master operates the launches.

**Collision risk**:

- **Per-VM shard isolation rule**: every multi-worker run MUST set `VM_NAME=<unique-tag>` +
  `MANIFEST_PER_VM_SHARDS=true` per CLAUDE.md "Per-VM shard isolation". Already-shipped guard fires
  `MultiWorkerWithoutShardIsolationError` if missed.
- **Manifest concurrency principle**: every consumer of the manifest MUST follow read-once + per-date freshness check +
  write-time CAS. The rescan + v6→v7 migration + dual-write all touch the manifest.
- **Manifest phantom audit**: phantom rows can mask migration mid-state. Run the phantom audit (Harsh Tab 4 actually)
  before + after migration; flag any drift.

**Done definition**:

1. ✅ GCS bundle migration Phase 0-7 complete; every consumer reads pipeline_mode partition; reconciler verified.
2. ✅ Manifest v6 → v7 migration shipped; reader removed v6 fallback; codex updated.
3. ✅ Expected_universe v2 enumerator running; catalog-aware rows in manifest.
4. ✅ Cross-asset rescan design + Harsh Tab 4 ran rescan + triage file populated for any disagreements.

---

## TAB 4 — AWS migration + cloud-agnostic governance

**Identity**: you own the cross-cloud parity thread. May-23 master plan requires AWS↔GCP cloud parity (Group F item in
master). Phase 0 (operator credit confirmed ≥$40k) + Phase 1 smoke shipped 2026-05-07; Phase 2 dual-bucket setup shipped
2026-05-07. Today picks up Phase 3 + cross-cutting governance (cloud-agnostic-script-pattern.md SSOT).

**Plan-of-record**: [`aws_migration_defi_first_2026_05_07.plan.md`](aws_migration_defi_first_2026_05_07.plan.md) +
cross-references to [`master_to_live_defi_2026_05_23.plan.md`](master_to_live_defi_2026_05_23.plan.md) Group F.

**Scope (4 items, P0-P1)**:

- [ ] [INFRA+TESTING] P0. **AWS Phase 3 cross-cloud parity smoke** — `CLOUD_PROVIDER=aws` read-path on DeFi shards (the
      5 buckets created Phase 2 at deployment-service@7da2f3d). Health-check passes against AWS-resident DeFi manifest +
      sample parquet read returns expected rows. Per CLAUDE.md "Force-Sync Warning" + "AWS Migration" framework. ~2
      AI-days.
- [ ] [INFRA+CODEX] P0. **`codex/05-infrastructure/cloud-agnostic-script-pattern.md` SSOT population** — currently a
      stub. Populate with the 4-cloud-tier discipline + bucket-naming SSOT + dual-bucket dual-write rule + Storage
      Transfer Service config pattern + UCI bucket-naming module reference + per-asset_group migration sequencing. ~1
      AI-day.
- [ ] [INFRA+UAC+UCI] P0. **UCI bucket-naming SSOT discipline** — extend `unified-cloud-interface/cloud_providers.yaml`
      with the full per-asset-group AWS bucket dictionary; add a UCI module `unified_cloud_interface.bucket_naming`
      exposing `get_bucket_name(cloud, asset_group, kind)` so all consumers stop hardcoding bucket names. Update UAC if
      bucket names cross-reference UAC enums. **Done**: every hardcoded bucket name in MTDS / MDPS / instruments-service
      / features-\* migrated to UCI lookups. ~2 AI-days.
- [ ] [INFRA] P1. **AWS Phase 4 prep — CeFi instruments + read-path** — extend Phase 3 read-path smoke to CeFi
      asset_group; provision dual-bucket for CeFi instruments (`instruments-store-cefi` AWS counterpart). Per master
      plan Group F "AWS↔GCP cloud parity" requires CeFi + DeFi as the May-23 baseline; rest defer post-cutover. ~1
      AI-day.

**Repos owned (collision boundary)**: deployment-service `scripts/aws/` + `cloud-build/`, unified-cloud-interface
(bucket-naming SSOT module), all consumer services for the bucket-naming refactor. **Hands off** alerting Phase 2-9 to
Tab 5 (single owner of alerting); hands off live-pipeline cross-cloud verification to Tab 2.

**Read-first**:

- CLAUDE.md sections: "Force-Sync Warning (CRITICAL)", "Workspace Configs (Canonical in PM)", "Workflow Templates"
- [`plans/active/aws_migration_defi_first_2026_05_07.plan.md`](aws_migration_defi_first_2026_05_07.plan.md) full body
- [`codex/05-infrastructure/cloud-agnostic-migration.md`](../../codex/04-architecture/cloud-agnostic-migration.md)
  (existing — read for the migration framework)
- [`codex/05-infrastructure/aws_migration_cost_analysis_2026_05_07.md`](../../codex/05-infrastructure/aws_migration_cost_analysis_2026_05_07.md)
  (operator credit + steady-state cost decision)

**Sub-agent fan-out**:

- Phase 3 smoke: 2 parallel sub-agents — (a) instruments-service CLOUD_PROVIDER=aws health-check; (b) MTDS
  CLOUD_PROVIDER=aws read on a DeFi shard.
- Codex SSOT: 1 sub-agent walks current bucket-name hardcoding instances + drafts the doc body. Master writes the
  authoritative version.
- UCI module: 2 parallel sub-agents — (a) write the module + tests; (b) sweep consumer migrations across MTDS + MDPS +
  instruments-service + features-_ (5 sub-sub-agents inside this one) — but verify zero collision with Tab 2 features-_
  live-pipeline wiring before sweeping.

**Collision risk**:

- **deployment-service `scripts/`**: Tab 1 (DeFi launchers) and Tab 4 (AWS scripts) both touch `scripts/`. Different
  subdirs (`vm/` vs `aws/`); zero overlap.
- **UCI sweep across consumers**: Tab 2 (live-pipeline) is also wiring consumers; if Tab 2 hits the same consumer in the
  same edit window, conflict. Coordinate via cross-tab handshake "UCI bucket-naming sweep timing" — Tab 4 ships UCI
  module first (no consumer edit), then announces in plan-of-record `## Open questions` that the sweep starts; Tab 2
  confirms its own edits are not in flight on the same files.

**Done definition**:

1. ✅ Phase 3 smoke green for DeFi (instruments + MTDS); Phase 4 smoke green for CeFi.
2. ✅ Codex `cloud-agnostic-script-pattern.md` populated; ratified.
3. ✅ UCI bucket-naming module shipped + every consumer migrated.
4. ✅ Plan flips per shippable unit + codex updated per Post-Plan-Phase Codex Audit HARD RULE.

---

## TAB 5 — Alerting + master refresh + governance

**Identity**: you own the operational + governance + master refresh thread. Highest-leverage tab for "is the workspace
ready to ship live trading by May 23?" Reads everything (live-pipeline + DeFi + GCS migration + AWS) and writes the
readiness narrative + alert wiring + IAM/audit-log/rate-limit operator decisions.

**Plan-of-record**: [`alerting_service_live_rules_2026_05_07.plan.md`](alerting_service_live_rules_2026_05_07.plan.md)

- [`master_to_live_defi_2026_05_23.plan.md`](master_to_live_defi_2026_05_23.plan.md) Group F+G +
  [`deploy_missing_auto_launch_2026_05_07.plan.md`](deploy_missing_auto_launch_2026_05_07.plan.md) Phase 0.

**Scope (5 items, P0)**:

- [ ] [ARCHITECTURE+DESIGN] P0. **Alerting Phase 2 KillSwitchBus rule wiring** — declarative half shipped 2026-05-07 at
      alerting-service@b025e83 (37 unit tests, `triggers_kill_switch=True` flag set on `KILL_SWITCH_*` rules).
      **Publish-side hook + integration test pending** per
      [`issues/alerting_kill_switch_publish_hook_2026_05_08.md`](issues/alerting_kill_switch_publish_hook_2026_05_08.md):
      when an alert with `triggers_kill_switch=True` fires through `route_event`, it must publish a `KillSwitchEvent` to
      the UTL bus so execution-service halt subscribers consume it. **Done**: hook wired + integration test +
      execution-service halt-on-event behaviour verified. ~1.5 AI-days.
- [ ] [ARCHITECTURE+DESIGN] P0. **Alerting Phase 2 — `CROSS_CLOUD_EGRESS_DETECTED` rule + AAVE utilization-spike
      threshold value** — audit §3 #5 flagged AAVE threshold ambiguous; resolve via DeFi-team judgment call
      (per-archetype: `leveraged_funding_arb` 9000 bps_of_one (90%) vs default 9500 (95%) per UAC@d00326d) + lock as
      documented decision. ~1 AI-day.
- [ ] [ARCHITECTURE] P0. **Alerting Phase 3-9** — per the audit, only 14/53 = 26% of alerting plan complete. Phase 3
      paging-target Secret Manager rotation. Phase 4 DART terminal wiring. Phase 5 dashboards. Phase 6 drill cadence.
      Phase 7 quietness baseline runtime SLO. Phase 8 rehearsal procedure. Phase 9 post-rehearsal iteration. ~3 AI-days.
- [ ] [GOVERNANCE+JUDGMENT] P0. **Master plan Group F+G refresh** — Group F items 17-22 (live-only prerequisites:
      backtest fidelity / 2-year batch run / Copper + CEFFU treasury / live testnet replicating prod / batch-vs-live
      reconciliation / circuit breakers + kill switches + alerting + auto-recovery) + Group G item 23 (DART manual-trade
      gate). Each item reads the relevant cross-plan status, flips master plan checkboxes, refreshes critical-path
      narrative for the 15-day cycle. ~2 AI-days.
- [ ] [GOVERNANCE+HUMAN-APPROVAL] P0. **Deploy_missing Phase 0 IAM scope + audit-log + rate-limit operator decisions** —
      Tab 13 yesterday drafted 3 proposals (PM@`6d44c73` + `fdc0bb9`). Today: review with operator, lock decisions,
      propagate through deploy_missing Phase 1+ and onto every Cloud Run service that uses the deployment-api launch
      path. **Done**: 3 STATUS DRAFT proposals → STATUS DECIDED with operator sign-off recorded; Phase 1+ work
      unblocked; IAM/audit-log/rate-limit propagated. ~2 AI-days.

**Repos owned (collision boundary)**: alerting-service (full ownership), UAC `alerting.py` / `crosscutting/alerting.py`
(Phase 1 shipped, additions only), deployment-api routing (auth_middleware.py for audit-log integration; collides with
**Harsh Tab 3 deployment-ui-lifecycle-tabs** if Harsh edits same routes — see cross-side handshake), PM master plan
(Group F+G refresh — Tab 5 only writes; other tabs don't touch master plan during this cycle).

**Read-first**:

- CLAUDE.md sections: "Master Plan — Live DeFi Trading by 2026-05-23" intro, "Service Infrastructure Requirements",
  "DeFi Execution Architecture" (kill-switch context), "Force-Sync Warning"
- [`plans/active/alerting_service_live_rules_2026_05_07.plan.md`](alerting_service_live_rules_2026_05_07.plan.md)
- [`plans/active/master_to_live_defi_2026_05_23.plan.md`](master_to_live_defi_2026_05_23.plan.md) Group F + G full
- [`plans/active/deploy_missing_auto_launch_2026_05_07.plan.md`](deploy_missing_auto_launch_2026_05_07.plan.md) Phase
  0 + the 3 STATUS DRAFT proposals
- [`codex/14-playbooks/alerting/alert-code-taxonomy.md`](../../codex/14-playbooks/alerting/alert-code-taxonomy.md)
- [`codex/14-playbooks/alerting/threshold-tuning.md`](../../codex/14-playbooks/alerting/threshold-tuning.md)

**Sub-agent fan-out**:

- Alerting Phase 2 hook: 1 architecture sub-agent designs the route_event → KillSwitchBus hook + integration test
  fixture. Master ships + verifies execution-service halt subscriber.
- Alerting Phase 3-9: 7 parallel sub-agents (one per phase). Each produces a self-contained deliverable. Master
  integrates + ships each as separate commits.
- Master refresh: 7 parallel sub-agents (one per master plan workstream A-G). Each reports what shipped this cycle vs
  what remains. Master writes the refreshed critical-path section + flips Group F/G checkboxes.
- Deploy_missing Phase 0: operator-driven; you facilitate the 3 decisions then sub-agents propagate.

**Collision risk**:

- Master plan: Tab 5 ONLY tab that writes to master_to_live_defi_2026_05_23.plan.md this cycle. Other tabs MUST NOT
  touch (per CLAUDE.md "Two teammates × multiple parallel agents — don't edit unfamiliar files").
- alerting-service: Tab 5 ONLY. No collision.
- deployment-api `auth_middleware.py`: Harsh Tab 3 (deployment-ui-lifecycle-tabs) writes auth-flow re-shape. Tab 5
  (audit-log integration for deploy_missing) might touch the same file. **Hard sync gate**: Tab 5 ships auth audit-log
  AFTER Harsh Tab 3 ships the auth re-shape (Tab 3 shape is foundational; audit-log wraps it).

**Done definition**:

1. ✅ Alerting Phase 2 KillSwitchBus hook + integration test + execution-service halt-on-event verified.
2. ✅ Alerting Phase 3-9 shipped (paging targets, DART wiring, dashboards, drill cadence, quietness baseline, rehearsal
   procedure executed).
3. ✅ Master plan Group F+G refresh committed — every item 17-23 has current-status note pointing at owner plan +
   commit-sha evidence.
4. ✅ Deploy_missing Phase 0 IAM/audit-log/rate-limit decisions LOCKED with operator sign-off recorded.

---

## Cross-tab handshakes (within Ikenna side)

Hard sync gates between tabs. Operate independently otherwise.

- [ ] **Tab 1 (UAC drift fixes) → Tab 5 (master refresh)**: Tab 1 ships drift fixes throughout the day; Tab 5's master
      refresh runs LAST and reflects them in Group F status. Tab 5 delays its master commit until Tab 1 reports DONE.
- [ ] **Tab 1 (paper-trade smoke) → Tab 5 (Group G refresh)**: Tab 1 paper-trade smoke green is the master plan Group G
      item 23 success criterion. Tab 5 reads Tab 1's status before the Group G flip.
- [ ] **Tab 2 (live-pipeline Phase 11 ServiceEmissionPolicy slice b/c) → Tab 3 (manifest v7 design)**: Phase 11 slice b
      couples to manifest-read; Tab 3's v7 schema MUST include the per-(shard_key, day) ServiceEmissionPolicy state
      column. Tab 3 waits for Tab 2's slice b spec before committing the v7 design.
- [ ] **Tab 3 (manifest v7 migration script) → Tab 1 (lending-indices VM relaunch)**: V7 migration script must preserve
      all existing manifest rows; Tab 1's VM relaunch reads manifest mid-migration. **Mitigation**: Tab 3 ships v7
      migration script with a feature-flag gate (default OFF); Tab 1 VM relaunch reads via existing v6 reader; cutover
      after Tab 3's migration completes + Tab 5's Group F refresh notes "manifest v7 active."
- [ ] **Tab 4 (UCI bucket-naming sweep) → Tab 2 (live-pipeline consumer wiring)**: UCI sweep replaces hardcoded bucket
      names; live-pipeline Phase 4-7 wires consumers. Hard ordering: UCI module ships, sweep across consumers runs, THEN
      live-pipeline Phase 4-7 consumes UCI lookups (not new hardcoding).
- [ ] **Tab 4 (AWS Phase 3 smoke) → Tab 5 (Group F refresh)**: Phase 3 green = Group F "AWS↔GCP cloud parity" checkbox
      flip. Tab 4 announces in plan-of-record `## Open questions` when smoke green; Tab 5 reads + flips.
- [ ] **Tab 5 (operator IAM decision) → Tab 4 (AWS infrastructure provisioning)**: deploy_missing Phase 0 IAM decision
      shapes how Cloud Run services authenticate against AWS for Phase 3 smoke. If operator picks restrictive IAM, Tab 4
      has more work; if blanket, Tab 4 ships faster. Coordinate at Tab 5's first decision-checkpoint.

## Cross-side handshakes (Ikenna ↔ Harsh)

These handshakes appear in BOTH plans (mirror-image). When a hard-gate item ships, the producing side pushes
immediately + announces in plan-of-record; consuming side `git pull`s before its next dependent edit.

- [ ] **Harsh Tab 1 (instruments-live + lifecycle ingestion) → Ikenna Tab 1 (lending-indices Bug 3 fix)**: Bug 3 =
      instruments-store-defi 2022 metadata floor. Harsh's instruments-live Phase D (defi instrument lifecycle
      activation) lands the catalog-aware floor. Ikenna's Bug 3 fix reads the new catalog. Hard sync: Harsh Phase D
      ships first.
- [ ] **Harsh Tab 2 (features_repo_consolidation Phase 1-4) → Ikenna Tab 2 (live-pipeline Phase 4-7)**: Live-pipeline
      Phase 4-7 wires the consolidated features repo. **Hard ordering**: features_repo_consolidation Phase 1-4 must land
      before live-pipeline Phase 4-7. Harsh announces feat repo consolidation Phase 4 ship; Ikenna pulls + starts Phase
      4-7 wiring.
- [ ] **Harsh Tab 2 (ml-features-phase2a wires) → Ikenna Tab 2 (live-pipeline Phase 11 ServiceEmissionPolicy slice b)**:
      Slice b couples to assert_no_lookahead_for_feature_group; ml-features-phase2a wires it into 8 services.
      Coordinate: Harsh ships per-service wires; Ikenna reads the wires + extends ServiceEmissionPolicy state to reflect
      lookahead-bias-checked status.
- [ ] **Harsh Tab 3 (deployment-ui-lifecycle-tabs auth re-shape) → Ikenna Tab 5 (deploy_missing audit-log
      integration)**: audit-log integration wraps the auth re-shape. Hard ordering: Harsh ships auth re-shape Phase 1;
      Ikenna ships audit-log on top.
- [ ] **Harsh Tab 4 (per-asset_group VM ops + reconcilers) → Ikenna Tab 3 (cross-asset rescan design)**: Harsh runs the
      rescan; Ikenna designs the schema flip. Coordinate: Ikenna ships design + ships rescan launcher script; Harsh runs
      the launcher + reports findings; Ikenna handles edge cases.
- [ ] **Harsh Tab 5 (mechanical refactors) → Ikenna Tab 1 (UAC drift fixes)**: Harsh's mechanical refactors might touch
      UAC `chain_env.py` for unrelated reasons (e.g. hard_schema_enforcement column adds). If yes, surgical `git add -p`
      to keep edits separate; Ikenna's `PROTOCOL_LAUNCH_DATES` flips never overlap with Harsh's mechanical UAC adds.

## Collision-risk callouts (file-level)

- **MDPS `base_adapter.py` / `BaseCandleAdapter`**: Ikenna Tab 2 wires live-pipeline; Harsh Tab 2 wires
  ml-features-phase2a. Different layers, different methods. Pre-commit `git diff --cached --name-only` MUST show only
  your files.
- **UAC `chain_env.py`**: Ikenna Tab 1 (`PROTOCOL_LAUNCH_DATES`); Harsh Tab 5 might add columns for hard_schema. Use
  `git add -p` if you both edit in the same window.
- **PM master plan**: Ikenna Tab 5 ONLY writes to it; all other tabs read-only.
- **deployment-api `auth_middleware.py`**: Harsh Tab 3 (auth re-shape) THEN Ikenna Tab 5 (audit-log). Sequence enforced.
- **`live-defi-rollout` push race**: per CLAUDE.md conditional push rule. Pre-commit `git status` +
  `git diff --cached --stat` (no path arg) MANDATORY before EVERY commit. Use `git add -p` / `git add <specific-file>`
  only.
- **Pre-commit hook prettier reformat**: any markdown edit triggers prettier. Files you didn't author may get
  reformatted as a side-effect; this is acceptable if content is unchanged. Reference: PM@8b3f949d this morning bundled
  prettier reformats of 6 plans + 2 archive copies for this same reason.

## Daily sync points

- **EOD T+0** (today, midnight UTC): Tabs 1-5 each report done-definition status to operator via plan-of-record
  `## Open questions` resolved + DONE block. Operator runs `git log --oneline -25 origin/live-defi-rollout` to see the
  day's shipments.
- **Tomorrow's daily reset**: 1 main-orchestrator-or-operator runs the daily reset per CLAUDE.md (fetch summary + Q&A
  sweep + draft tomorrow's split). Carryover items roll forward; shipped items reflect in master plan flip.
- **2026-05-15 GCS migration deadline**: Tab 3's GCS bundle migration MUST land by then per the plan frontmatter.
  Earlier is better; latest is acceptable.
- **2026-05-23 live-DeFi cutover**: master plan Group F+G must all be ✅. Tab 5's master refresh tracks the gap.

## Defer post-cutover (BOTH must NOT touch)

- DART v2 archetype roadmap (HUMAN-P1 in `strategy_and_dart_master`)
- Marketing copy reconciliation (master §25.A.1-A.3)
- `ml_and_features_master` Phase 4 (Bayesian / calibration / advanced caching)
- `mtds_per_instrument_download_api` Phase 2 + Phase 3 (Phase 1.5 chain axis IS in scope per Harsh Tab 5)
- AWS Phase 5-9 (beyond CeFi-instruments + DeFi)
- `strategy_and_dart_master` Phase 1 service-split full refactor + Phase 5 Unity UAT (operator-only $550 + Java binary)
- `predictions_master` non-Phase-1 work (P1; in Harsh Tab 1 scope only if Phase 1 lands cleanly mid-cycle)
- `consolidated_strategy_and_ui` Phase 3 deep work (now under `strategy_and_dart_master`)
- [`fund_administration_service_and_pooled_subscription_redemption_2026_04_20`](fund_administration_service_and_pooled_subscription_redemption_2026_04_20.plan.md)
  (post-2026-05-23 P2 per cross-plan position banner)
- [`ml_pipeline_ui_integration_2026_04_16`](ml_pipeline_ui_integration_2026_04_16.plan.md) (deferred unless last 2 todos
  verifiable today)
- [`api_football_minimal_flattening_removal_2026_05_07`](api_football_minimal_flattening_removal_2026_05_07.plan.md)
  (sports-pipeline plumbing — picks up post-May-23)
- [`data_status_comprehensive_test_coverage_2026_05_07`](data_status_comprehensive_test_coverage_2026_05_07.plan.md)
  (regression-test net — post-May-23)

## Spawn prompts (paste-ready per tab)

> Use these when opening a fresh Claude Code tab + telling it _"work on Tab N"_. Each prompt is fully self-contained per
> the CLAUDE.md spawn-prompt template.

### Tab 1 spawn prompt

```text
You are Tab 1 — a sub-agent spawned by Ikenna's main orchestrator agent (a separate Claude
Code session on the SAME PC, sharing the SAME .git/ + working tree as you).

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — workspace rules + § "Daily Work-Split Process".
  2. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — sub-agent inheritance.
  3. plans/active/work_split_2026_05_08_ikenna.md § "TAB 1 — DeFi launch + Fork 1 completion" —
     your scope, repos owned, read-first list, sub-agent fan-out plan, collision risk, done definition.
  4. plans/active/defi_master_2026_05_07.plan.md (full body — your primary plan-of-record).

Your agent-tag for ping-ledger entries: defi-fork1-completion-tab.
Your tab number: 1.

ORCHESTRATION RULES (per CLAUDE.md § "Daily Work-Split Process" universal mechanics):
  1. Shared working tree — no `git pull` needed between tabs; pre-commit check
     (git status + git diff --cached --stat NO PATH ARG) mandatory before EVERY commit.
     Use `git add -p` for shared files; never `git add -A` / `git add <whole-shared-file>`.
  2. Plan-doc Q&A flow — write blockers into defi_master_2026_05_07.plan.md `## Open questions`
     (status 🟡 BLOCKED), append ping in plans/active/_agent_pings.md, continue with what you CAN do.
  3. Conditional push — per shippable unit: commit locally, fetch + check incoming, zero
     incoming → push, any incoming → flag + escalate.
  4. Plan-flip in same logical unit as code — checkbox flip + <repo>@<sha> evidence stamped
     in body, NOT batched at session end.
  5. Findings Triage Discipline (HARD RULE) — case-1-to-5 routing per CLAUDE.md.

YOUR TASK: ship the 6 items in TAB 1 (paper-trade smoke completion + lending-indices
relaunch + 4 UAC drift sub-tabs + Stream A LST collateral + Pyth Hermes archive backfill +
bSOL coverage gap). See work_split_2026_05_08_ikenna.md § "TAB 1" for full done-definition.

REPORT-BACK: per shippable unit, code commit + plan-flip commit, conditional push.
Final: append a "DONE-2026-05-08" block at the bottom of defi_master_2026_05_07.plan.md
body listing every code + plan-flip commit sha. Then go quiet — don't pick up new work
autonomously.
```

### Tab 2 spawn prompt

```text
You are Tab 2 — a sub-agent spawned by Ikenna's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "Daily Work-Split Process",
     § "ARCHITECTURE 2026-05-08 — Live pipeline" (in auto-memory; cite from CLAUDE.md
     "Plans must capture full codebase impact upfront" rule).
  2. plans/active/work_split_2026_05_08_ikenna.md § "TAB 2 — Live pipeline + writegate
     Phase 5 ratchet" — your scope.
  3. plans/active/live_pipeline_mtds_mdps_features_2026_05_08.plan.md (your primary
     plan-of-record).
  4. plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md Phase 5 (your
     secondary plan-of-record).
  5. codex/05-infrastructure/live-pipeline-architecture.md + replay-subsystem.md +
     codex/02-data/pipeline-mode-partition.md +
     codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md.

Your agent-tag: live-pipeline-tab. Your tab number: 2.

ORCHESTRATION RULES: per CLAUDE.md § "Daily Work-Split Process" + Tab 1 spawn prompt.

YOUR TASK: ship live-pipeline Phases 0-14 + writegate Phase 5 ratchet. See
work_split_2026_05_08_ikenna.md § "TAB 2" for full done-definition.

REPORT-BACK: per CLAUDE.md HARD RULE cadence (5-15+ small commits across 14 phases).
Final: DONE-2026-05-08 blocks at the bottom of both plan-of-records.
```

### Tab 3 spawn prompt

```text
You are Tab 3 — a sub-agent spawned by Ikenna's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "Manifest migration, NOT fallback",
     § "Honest absence vs fake placeholders", § "Per-VM shard isolation for concurrent backfills",
     § "Manifest concurrency principle", § "Manifest phantom audit".
  2. plans/active/work_split_2026_05_08_ikenna.md § "TAB 3 — GCS migration + manifest cluster".
  3. plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.plan.md (primary).
  4. plans/epics/manifest_migration_master_2026_05_07.plan.md.
  5. plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md § Phase 3.D.4 v2.

Your agent-tag: gcs-manifest-migration-tab. Your tab number: 3.

YOUR TASK: ship GCS migration Phase 0-7 + manifest v6→v7 migration design + expected_universe
v2 enumerator + cross-asset rescan design. See work_split_2026_05_08_ikenna.md § "TAB 3".

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE block at bottom of each plan-of-record.
```

### Tab 4 spawn prompt

```text
You are Tab 4 — a sub-agent spawned by Ikenna's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "Force-Sync Warning (CRITICAL)",
     § "Workspace Configs (Canonical in PM)".
  2. plans/active/work_split_2026_05_08_ikenna.md § "TAB 4 — AWS migration + cloud-agnostic governance".
  3. plans/active/aws_migration_defi_first_2026_05_07.plan.md (primary).
  4. codex/05-infrastructure/cloud-agnostic-script-pattern.md (currently a stub — you populate it).

Your agent-tag: aws-cloud-agnostic-tab. Your tab number: 4.

YOUR TASK: ship AWS Phase 3 cross-cloud parity smoke + codex SSOT population +
UCI bucket-naming module + AWS Phase 4 prep. See work_split_2026_05_08_ikenna.md § "TAB 4".

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE block at bottom of plan-of-record.
```

### Tab 5 spawn prompt

```text
You are Tab 5 — a sub-agent spawned by Ikenna's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "Master Plan — Live DeFi Trading by 2026-05-23",
     § "DeFi Execution Architecture" (kill-switch context), § "Service Infrastructure Requirements".
  2. plans/active/work_split_2026_05_08_ikenna.md § "TAB 5 — Alerting + master refresh + governance".
  3. plans/active/alerting_service_live_rules_2026_05_07.plan.md (primary).
  4. plans/active/master_to_live_defi_2026_05_23.plan.md Group F+G full bodies.
  5. plans/active/deploy_missing_auto_launch_2026_05_07.plan.md Phase 0.
  6. codex/14-playbooks/alerting/alert-code-taxonomy.md + threshold-tuning.md.

Your agent-tag: alerting-master-governance-tab. Your tab number: 5.

YOUR TASK: ship Alerting Phase 2 KillSwitchBus hook + Phase 3-9 alerting wiring + master
plan Group F+G refresh + deploy_missing Phase 0 IAM/audit-log/rate-limit decisions LOCKED.
See work_split_2026_05_08_ikenna.md § "TAB 5".

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE block at bottom of each plan-of-record.
This tab runs LAST (it consumes the cycle's shipments via master refresh).
```

## Discipline reminders (every tab, every commit)

Per CLAUDE.md § "Daily Work-Split Process — Universal mechanics":

- **Pre-commit check is mandatory before EVERY commit**: `git status` then `git diff --cached --stat` (NO path
  argument). Surgically un-stage anything you don't recognise. Use `git add -p` / `git add <specific-file>` only.
- **Per shippable unit**: commit locally + flip checkbox + push (conditional rule: fetch + zero incoming → push; any
  incoming → flag + escalate). Don't batch.
- **Plan flip in same logical unit as code**: ship code → flip checkbox → commit plan flip → push. Never end-of-session.
- **Sub-agent rules injection**: paste
  [`cursor-configs/SUB_AGENT_MANDATORY_RULES.md`](../../cursor-configs/SUB_AGENT_MANDATORY_RULES.md) at top of every
  Task prompt. Sub-agents in `--print` mode CANNOT read files from disk.
- **Discoveries as plan todos**: any side-discovery → plan todo at the moment it surfaces (P0-P3 + body prefix +
  provenance citation).
- **Findings Triage Discipline (HARD RULE)**: case-1-to-5 routing per CLAUDE.md. Big findings (case 5) → file an issue
  doc + notify operator immediately.
- **CI Verification After Every Push (HARD RULE)**: every push to a CI-triggering branch needs a watcher (sub-agent or
  `ScheduleWakeup`). For `live-defi-rollout` pushes, CI does NOT run remotely; just confirm push landed.
- **Cross-plan coordination banners**: when launching VMs or starting in-flight refactors, banner every other active
  plan whose work is influenced. Banner-add is part of the launch logical unit.
- **Post-Plan-Phase Codex Audit (HARD RULE)**: at every major phase boundary, audit + update codex docs the phase
  touched or should have touched.

## Done definition (whole layout)

When all 5 tabs hit their per-tab done-definition, today's Ikenna split is complete. Tab 5 then runs the master refresh
capturing the cycle's shipped work. EOD: archive this plan to `plans/archive/work_split_2026_05_08_ikenna.md`

- draft tomorrow's `work_split_2026_05_09_ikenna.md` per the daily reset protocol.

## Cross-references

- Companion: [`work_split_2026_05_08_harsh.md`](work_split_2026_05_08_harsh.md) — Harsh's mirror plan.
- Methodology spec: [`cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) §"Daily Work-Split Process".
- Yesterday's archived split:
  [`plans/archive/work_split_2026_05_07_ikenna_5tab_layout.md`](../archive/work_split_2026_05_07_ikenna_5tab_layout.md).
- Master plan: [`master_to_live_defi_2026_05_23.plan.md`](master_to_live_defi_2026_05_23.plan.md) — the durable
  readiness model.
