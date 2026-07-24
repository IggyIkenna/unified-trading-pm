---
doc_type: plan
title: Ikenna's daily work-split — 2026-05-08 (15 days to live-DeFi)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, deployment-ui, execution-service, features-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
type: coordination-doc
deadline: 2026-05-23 (live DeFi)
horizon: 1-day cycle (rolls forward EOD)
companion_to: plans/active/work_split_2026_05_08_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

## Deferred work — migrated to:

**None** — successor: not applicable. Verified 2026-07-21 (batch-5 archived-plan discipline triage): mirror of the
companion Harsh 05-08 tracker, same disposable daily-snapshot pattern. This file additionally already contains its own
"## Deferred work after 2026-05-10 audit session" reconciliation table naming successors/blockers per residual item
(cefi_master, predictions_master, launcher_scripts_consolidation, alerting Phase 4-9, etc.) — that section IS the
deferred-work-to-successor mapping this banner requires, just under a heading the checker's regex doesn't match exactly.
All items in it are since resolved (in-flight items were carried by a same-cycle tab; operator-needs-decision items were
resolved via `operator_decisions_2026_05_08.md`).

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
  [`master_to_live_defi_2026_05_23`](master_to_live_defi_2026_05_23.md) Group F (live-only prerequisites) + Group G
  (operator UX) are now the gating ladder. DeFi launches that started 2026-05-07 hit silent-zero regressions (Bug 1 AAVE
  V3 ETHEREUM root-caused as UAC SSOT drift; Tab 14 audit found 13 of 17 probed `(chain, protocol)` pairs have similar
  drift).
- **Yesterday's Ikenna 5-tab layout finished** with Tabs 1-5 done-definitions met (alerting Phase 1, writegate Phase 4.A
  typed-error rendering, expected-universe enumerator `--apply-write` 1.4M rows, defi_archetypes_canonicalisation
  triage, master plan refresh). Carryover into today: alerting Phase 2-9, writegate Phase 2.A residual + Phase 5
  ratchet, defi_master Fork 1 deferred items + Tab 14 4 fix sub-tabs A/B/C/D, paper-trade smoke completion.
- **New incoming overnight**: 4 plans landed 2026-05-07 → 2026-05-08 from cross-cutting scope:
  [`live_pipeline_mtds_mdps_features_2026_05_08`](live_pipeline_mtds_mdps_features_2026_05_08.md) (14 phases),
  [`gcs_migration_bundle_pipeline_mode_2026_05_08`](gcs_migration_bundle_pipeline_mode_2026_05_08.md) (overnight
  migration of millions of parquets),
  [`features_repo_consolidation_2026_05_08`](features_repo_consolidation_2026_05_08.md) (8 repos → 1, deadline
  2026-05-13), [`hard_schema_enforcement_2026_05_08`](hard_schema_enforcement_2026_05_08.md) (under
  infrastructure_master). Live-pipeline + gcs-migration are cross-cutting / migration / governance = Ikenna-side;
  features-repo-consolidation + hard-schema are mechanical = Harsh-side per split principle.
- **Ping ledger (overnight)**: 1 entry — `ml-features-phase2a-tab` Q1 🟡 BLOCKED [ESCALATED-TO-OPERATOR] strategic scope
  ambiguity. That's a Harsh-side ping; Ikenna doesn't pick up.

## May-23 epic context (read first)

The 2026-05-08 plans-restructure landed the **epic layer** at [`plans/epics/`](../epics/) above the granular masters
(per [`plans_workspace_organization_2026_05_08.md`](plans_workspace_organization_2026_05_08.md) +
[`plans/epics/README.md`](../epics/README.md)). 7 epics own the May-23 cutover targets:

| Epic                                                                                  | May-23 scope                              | Side ownership                           |
| ------------------------------------------------------------------------------------- | ----------------------------------------- | ---------------------------------------- |
| [`live_defi_rollout_may_23_2026`](../archive/live_defi_rollout_may_23_2026.epic.md)   | LIVE on real wallet — 3 carry archetypes  | **Ikenna lead** (Tab 1 + Tab 5)          |
| [`cefi_ml_may_23_2026`](../archive/cefi_ml_may_23_2026.epic.md)                       | LIVE on real capital — continuous ML CeFi | **Joint** (Ikenna Tab 2/5 + Harsh Tab 2) |
| [`sp_prediction_may_23_2026`](../archive/sp_prediction_may_23_2026.epic.md)           | BATCH ML only                             | Harsh Tab 2 + 5                          |
| [`price_arbitrage_may_23_2026`](../archive/price_arbitrage_may_23_2026.epic.md)       | BACKTEST only                             | Harsh Tab 5                              |
| [`sports_ml_may_23_2026`](../archive/sports_ml_may_23_2026.epic.md)                   | BACKTEST only                             | Harsh Tab 1 + 5                          |
| [`prediction_markets_may_23_2026`](../archive/prediction_markets_may_23_2026.epic.md) | BACKTEST only                             | Harsh Tab 1 + 5                          |
| [`cross_cutting_may_23_2026`](../epics/cross_cutting_may_23_2026.epic.md)             | Workspace-wide                            | **Both sides every tab**                 |

Ikenna-side covers the 2 LIVE epics (`live_defi_rollout` + `cefi_ml`) plus all `cross_cutting` infra (live-pipeline,
writegate Phase 5, GCS migration, AWS, alerting, master plan refresh). Harsh-side covers the 4 BATCH/BACKTEST epics
(`sp_prediction` + `price_arbitrage` + `sports_ml` + `prediction_markets`) plus implementation-from-spec for both LIVE
epics. Per [`plans/epics/README.md`](../epics/README.md): epics are **read-mostly** + don't duplicate sub-plans; this
split assigns sub-plan tactical work, not epic-level deliverables (the master plan tracks epic completion).

## Working model

**Model A — fixed thematic 6-tab clustering.** The day's work clusters cleanly into 6 themes (DeFi launch + Fork 1
completion, live-pipeline + writegate Phase 5, GCS migration + manifest cluster, AWS migration + cloud-agnostic
governance, alerting + master refresh + governance, cross-cutting design) so 6 fixed tabs absorb the load. Each tab runs
Opus at full window with sub-agent fan-out for mechanical multi-file work. Tabs run to their done-definition, not a
calendar end-of-day — agents finish faster than humans.

> **CI gate reminder (workspace-wide).** Per CLAUDE.md § "CI Verification After Every Push": pushes to
> `live-defi-rollout` do **NOT** trigger remote CI. With ~6 parallel tab agents + many sub-agents pushing all day, the
> ONLY quality gate is each shippable unit's local `bash scripts/quality-gates.sh` (Pass 1) before push. There is no
> remote safety net catching platform-specific failures on this branch. Confirm push landed on origin
> (`git rev-list --left-right --count HEAD...origin/live-defi-rollout` returns `0 0`) per shippable unit.

## Coverage guarantee — 6 tabs absorb today's Ikenna-side scope

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
| `aws_migration_defi_first_2026_05_07`                 | `/codex/05-infrastructure/cloud-agnostic-script-pattern.md` SSOT population                                                         | 4   |
| `aws_migration_defi_first_2026_05_07`                 | Phase 3 cross-cloud parity smoke (CLOUD_PROVIDER=aws read-path on DeFi shards)                                                      | 4   |
| `alerting_service_live_rules_2026_05_07`              | Phase 2 KillSwitchBus rule wiring + `CROSS_CLOUD_EGRESS_DETECTED` rule + AAVE utilization-spike threshold                           | 5   |
| `alerting_service_live_rules_2026_05_07`              | Phase 3-9 paging targets + DART terminal wiring + rehearsal procedure                                                               | 5   |
| `master_to_live_defi_2026_05_23`                      | Group F items 17-22 refresh (operational-validation; 2-year batch run; Copper + CEFFU treasury; live testnet replicating prod)      | 5   |
| `master_to_live_defi_2026_05_23`                      | Group G item 23 (DART manual-trade gate; 6-persona Playwright matrix gate)                                                          | 5   |
| `deploy_missing_auto_launch_2026_05_07`               | Phase 0 IAM scope + audit-log + rate-limit operator decisions (review draft → sign-off → propagate)                                 | 5   |
| `cross_cutting_may_23_deliverables_2026_05_08`        | Strategy catalogue UAC schema + archetype × venue × instrument-type matrix design                                                   | 6   |
| `cross_cutting_may_23_deliverables_2026_05_08`        | Strategy ID UAC schema + canonical naming + versioning rule                                                                         | 6   |
| `cross_cutting_may_23_deliverables_2026_05_08`        | Client model UAC + capital allocation matrix per (client, archetype, venue)                                                         | 6   |
| `cross_cutting_may_23_deliverables_2026_05_08`        | DART manual-trade lane scope decision (per-archetype operator-replicable surfaces)                                                  | 6   |
| `cross_cutting_may_23_deliverables_2026_05_08`        | Strategy catalogue UI scope decision (filter axes for asset_group / archetype / venue / live-vs-backtest)                           | 6   |

**26 items / 6 tabs / 0 dropped.**

## AI-day estimate (per tab, summed across the cycle)

| Tab                         | Theme                                                         | Items                                                                                                                        | AI-days |
| --------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------- |
| 1                           | DeFi launch (Fork 1 + UAC drift fixes)                        | Paper-trade smoke + lending-indices relaunch + 4 UAC drift sub-tabs + Stream A LST collateral + Pyth Hermes archive backfill | ~12     |
| 2                           | Live pipeline + writegate Phase 5                             | 14-phase live_pipeline plan (cross-cutting MTDS + MDPS + features) + ratchet + Redis Stream cascade                          | ~12     |
| 3                           | GCS migration + manifest cluster                              | Overnight bundle migration + Stage 4 rescan + expected_universe v2 + v6→v7 schema design                                     | ~10     |
| 4                           | AWS migration + cloud-agnostic                                | Phase 2 dual-bucket + Phase 3 parity smoke + UCI SSOT + codex page                                                           | ~6      |
| 5                           | Alerting + master refresh + governance                        | Alerting Phase 2-9 + master Group F+G refresh + deploy_missing Phase 0 IAM/audit-log/rate-limit                              | ~10     |
| 6                           | Cross-cutting design (catalogue + IDs + clients + DART scope) | Strategy catalogue UAC + ID schema + client model + capital allocation matrix + DART scope spec                              | ~10     |
| **Total Ikenna-side cycle** |                                                               | **~60**                                                                                                                      |

6 parallel agents × ~10 days solo = ~60 ai-days. Above the CLAUDE.md "25-50 AI-days per side" target but within "err on
beefier scope" guidance — Tab 6 was added 2026-05-08 mid-cycle to close the cross_cutting epic gap (deliverables #1-#4
not assigned to Tabs 1-5 per the audit). **Err on the side of beefier scope**; we can do less of a beefy plan over time,
can't add scope retroactively to a thin one.

---

## TAB 1 — DeFi launch + Fork 1 completion

**Identity**: you own the May-23 DeFi critical path end-to-end. Trading-judgment thread runs through every item: launch
decisions, drift-fix sequencing, paper-trade interpretation, custody integration. Highest collision risk with Harsh's
per-asset_group VM ops cluster (Tab 4 there) — coordinate via the cross-side handshake "DeFi VM relaunches".

**Plan-of-record**: [`defi_master_2026_05_07.md`](defi_master_2026_05_07.md) (Fork 1 + Bug fixes + Stream A + Pyth
Hermes) +
[`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
(Stream A LST collateral) + [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) Group F.

**Scope (6 items, P0-P1)**: Items 3, 5, 6 already shipped (`- [x]`). Remaining 3 items (1, 2, 4) are **all
PARALLEL-SAFE** — disjoint files (Item 1 paper-trade smoke = execution-service + strategy-service + PBM round-trip; Item
2 lending-indices VM relaunch = MTDS `lending_indices_handler.py` + relaunch script; Item 4 Stream A = UAC
`venue_collateral.py` + new codex doc). Send all 3 sub-agent fan-outs in ONE message at boot. Item 1 has internal
pre-reqs (MTDS VM drain + features-onchain Docker rebuild + 4-service QG passes) — those are verification gates inside
Item 1, not parallelization blockers between items.

- [ ] [TRADING+INTEGRATION] P0. **[PARALLEL]** **Paper-trade smoke completion (carry_staked_basis Solana hedge)** —
      execution-service + strategy-service + position-balance-monitor-service end-to-end round-trip. Pre-flight checks
      shipped 2026-05-08 (Pyth Hermes endpoint reachable HTTP 200 in 2.3s); blocked yesterday on (a) MTDS@d19d76c VMs
      drain + (b) features-onchain Docker rebuild + (c) 4-service QG passes. Today: verify drain status of
      `mtds-{vault-share-price,lst-rates,gas-fees}-20260508-010{050,105,121}` VMs first; if drained green, proceed with
      smoke. **Done**: paper fill lands in execution-service, position-balance-monitor reflects open position,
      strategy-service P&L attribution computed (no execution-alpha conflation per CLAUDE.md "Batch = Live"). ~3
      AI-days.
- [ ] [TRADING] P0. **[PARALLEL]** **Lending-indices VM relaunch (Bug 2 + Bug 3)** — Tab 9 yesterday verified Bug 1 (UAC
      SSOT fix end-to-end at AAVE_V3 ETHEREUM 2023-01-27 captured rows). Bugs 2 (Compound V3 schema drift) + 3
      (instruments-store-defi 2022 metadata floor) per
      [`../archive/issues/lending_indices_handler_bugs_2026_05_07.md`](../archive/issues/lending_indices_handler_bugs_2026_05_07.md)
      still pending. Today: **fix both bugs end-to-end + relaunch + 90s STARTED + 10-15min progress + T+30min per-VM
      manifest spot-check**. Per CLAUDE.md "No fire-and-forget VM launches". ~2 AI-days.
- [x] [DESIGN+UAC] P0. **4 UAC `PROTOCOL_LAUNCH_DATES` drift fix sub-tabs A/B/C/D** — **SHIPPED** UAC@6c873e4 (Batches
      A/B/C/D bundled in one commit per single-file no-collision-window opportunity; 13 drift pairs flipped;
      SPARK/ETHEREUM added at 2023-03-07 + removed from PENDING; POLYGON/COMPOUND_V3 removed and moved to PENDING since
      `SUBGRAPH_IDS["compound_v3"]` has no POLYGON entry; 4-pair `_PRE_GENESIS_SUBGRAPH_INDEXED_ALLOWLIST` extended to
      permit launch < chain_genesis for UNISWAP_V3 ARB/OPT/BASE + COMPOUND_V3 BASE; 19/19 tests pass). Tab 14 yesterday
      found 13 of 17 pairs drift (same shape as Tab 9's AAVE_V3-ETHEREUM finding); audit's bundled drift table was
      shipped as one atomic commit per Tab 14's audit caveat that batches all touch the same UAC file (sequential
      merging required). **Manifest re-scan needed** post-this commit per writegate Phase 2.E reason taxonomy — moved
      dates reclassify EXPECTED_PRE_GENESIS_CHAIN ↔ SOURCE_RETURNED_ZERO rows automatically once VMs re-write per-row
      keys. ~3 AI-days.
- [ ] [DESIGN+UAC+CODEX] P0. **[PARALLEL]** **Stream A — DERIBIT/BYBIT/OKX ETH-LST collateral acceptance flips** — per
      [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
      Stream A. Live-API probe to confirm exact 2026-05-07 collateral value ratios for Deribit stETH, Bybit
      stETH/wstETH/USDe/sUSDe, OKX wstETH/stETH. Document evidence in
      `unified-trading-pm/codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md` (new doc). Update
      `unified-api-contracts/unified_api_contracts/registry/venue_collateral.py` matrix entries (5+ flipped rows; see
      plan body for full list). Add unit tests covering the flips. Update
      [`carry-staked-basis.md`](/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md) "Today's
      venue-collateral" section. ~2 AI-days.
- [ ] [TRADING+INFRA] P1. **Pyth Hermes archive backfill — jitoSOL 2022-11 → 2023-10 11-month gap** — Tab 14 audit found
      Pyth Hermes archive doesn't cover the early jitoSOL period needed for `carry_staked_basis` Solana leg historical
      training data + paper-trade smoke realism. Today: probe Hermes archive endpoint, identify the gap bound, design
      the backfill (archive paid plan? Pythnet RPC + index-into-historical? alternative source like Birdeye archive?),
      ship the backfill VM under `deployment-service/scripts/vm/launch-mtds-pyth-hermes-archive-backfill-vm.sh` with
      VM_PREFIX_TO_BUCKET registration + watchdog relaunch. ~2 AI-days.
- [x] [TRADING] P1. **bSOL coverage gap fix in UAC `LST_TOKEN_GENESIS`** — **SHIPPED** UAC@6c873e4 (added bSOL at
      conservative 2022-11-24 floor in `LST_TOKEN_GENESIS` + `BLAZESTAKE → (bSOL,)` in `LST_VENUE_TO_TOKENS`; bundled
      with Item 3 Batch D since both edit `_defi_lst.py` and Tab 14 grouped them; exact mint date for bSO13r4...HP3piy1
      via Solana RPC `getSignaturesForAddress` deferred to follow-up — over-clipping toward 2022-11-24 is the safe
      direction per CLAUDE.md "Honest absence" rule). ~0.5 AI-days.

**Repos owned (collision boundary)**: MTDS (DeFi adapters + lending-indices handler — collides with Harsh Tab 4 only on
lending_indices_handler.py if Bug fixes overlap; coordinate timing), execution-service + strategy-service +
position-balance-monitor-service (paper-trade smoke), deployment-service `scripts/vm/launch-defi-*`

- `launch-mtds-pyth-hermes-archive-backfill-vm.sh` (new), UAC `chain_env.py:PROTOCOL_LAUNCH_DATES` +
  `venue_collateral.py` + `LST_TOKEN_GENESIS`, codex (`16-strategy-playbooks/defi/venue-collateral-2026-05-07.md`,
  `09-strategy/architecture-v2/archetypes/carry-staked-basis.md`).

**Read-first**:

- CLAUDE.md sections: "DeFi Execution Architecture", "Pyth — UNBANNED 2026-05-06", "Cross-Plan Coordination Banners",
  "VM tarball deployment", "VM Naming Convention", "No fire-and-forget VM launches"
- [`plans/active/defi_master_2026_05_07.md`](defi_master_2026_05_07.md) (full body — long)
- [`plans/archive/issues/lending_indices_handler_bugs_2026_05_07.md`](../archive/issues/lending_indices_handler_bugs_2026_05_07.md)
- [`plans/archive/issues/defi_988_missing_dates_audit_2026_05_08.md`](../archive/issues/defi_988_missing_dates_audit_2026_05_08.md)
- [`plans/archive/issues/defi_fork1_prep_audit_2026_05_08.md`](../archive/issues/defi_fork1_prep_audit_2026_05_08.md)
  (Tab 14 output: 13 of 17 pairs drift)
- [`plans/active/master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) Group F+G

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

**Sub-agent isolation table** (paste rows verbatim into each Task prompt's "files OFF-LIMITS" section):

| Sub-agent ID         | Files owned (only edit these)                                                                                                                | Files OFF-LIMITS                                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| sa1.PaperSmoke-exec  | `execution-service/**/pyth_oracle_read.py` + Solana RPC reachability test                                                                    | strategy-service config, PBM wallet/custody, MTDS shard inspection                                                |
| sa1.PaperSmoke-strat | `strategy-service/**/carry_staked_basis_archetype_config.py` validation                                                                      | execution-service Pyth read, PBM wallet/custody, MTDS shard inspection                                            |
| sa1.PaperSmoke-pbm   | `position-balance-monitor-service/**/wallet_adapter.py` + custody adapter health probe                                                       | execution-service, strategy-service, MTDS                                                                         |
| sa1.PaperSmoke-mtds  | MTDS shard read-side inspection (read-only — no writes; reports findings to master)                                                          | All write-side surfaces                                                                                           |
| sa1.LendingIdx-bug2  | MTDS `lending_indices_handler.py` Compound V3 schema-drift fix + tests                                                                       | Bug 3 metadata floor (sa1.LendingIdx-bug3 owns); UAC `chain_env.py`                                               |
| sa1.LendingIdx-bug3  | `instruments-store-defi/...` 2022 metadata floor (depends on Harsh T1 catalog-aware writer-guard SHIPPED first per cross-side handshake)     | MTDS handler (sa1.LendingIdx-bug2 owns); UAC `chain_env.py`                                                       |
| sa1.LendingIdx-relch | `deployment-service/scripts/vm/launch-mtds-lending-indices-vm.sh` relaunch invocation + 90s STARTED + 10-15min progress + T+30min spot-check | Adapter source files (sa1.LendingIdx-bug2/3 own them)                                                             |
| sa1.StreamA-deribit  | Live-API probe Deribit + Bybit collateral ratios (read-only probe, output to evidence doc)                                                   | OKX probe (sa1.StreamA-okx owns); USDe metadata research (sa1.StreamA-usde owns); UAC matrix update (master only) |
| sa1.StreamA-okx      | Live-API probe OKX wstETH/stETH collateral ratios                                                                                            | Deribit/Bybit probe; USDe metadata research; UAC matrix update                                                    |
| sa1.StreamA-usde     | USDe / sUSDe metadata research (Bybit context); output to evidence doc                                                                       | Live-API probes; UAC matrix update                                                                                |

Master sa1 (Tab 1 orchestrator) owns: UAC `registry/venue_collateral.py` matrix flips (after sa1.StreamA-_ probes
complete) + new codex doc `unified-trading-pm/codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md` +
carry-staked-basis codex update + integrated paper-trade smoke round-trip after all sa1.PaperSmoke-_ sub-agents green.

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

**Full-execution criterion** (per PLAN_FORMAT.md § 8 + "Plans Run To Actual Completion" HARD RULE):

- ✅ **Paper-trade smoke ran end-to-end on real infra (testnet wallet + real adapter codepath)**.
  - **What ran**:
    `python -m strategy_service.cli batch --archetype carry_staked_basis --asset-group defi --venue jitoSOL --duration 1h --paper`;
    matching engine returns simulated fill; downstream events flow.
  - **Verification**: `gcloud storage ls gs://${PID}-events/events/strategy/$(date +%Y-%m-%d)/paper-smoke-*/` shows
    STARTED + TRADE_REQUESTED + FILL_RECEIVED + POSITION_UPDATED + PNL_COMPUTED events. Sample one of each event, assert
    non-empty payload + correct strategy_id + position-balance-monitor row in expected
    `gs://${PID}-position-balance/...` shard.
- ✅ **Lending-indices VM ran-to-completion on real infra**.
  - **What ran**: `bash deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh` (or equivalent),
    monitored until STOPPED with `rows_captured > 0`.
  - **Verification**: post-VM `gcloud storage ls gs://${PID}-events/events/mtds/$(date +%Y-%m-%d)/mtds-lending-*/` shows
    STARTED + per-instrument INSTRUMENT_PROCESSED events + STOPPED. Sample 3 random instruments' parquets, assert
    `rows_captured > 0` AND `available_at` column present AND non-NaN.
- ✅ **Pyth Hermes archive backfill VM ran-to-completion on real infra (Solana-only scope)**.
  - **What ran**: `bash deployment-service/scripts/vm/launch-mtds-pyth-hermes-vm.sh`, monitored until STOPPED.
  - **Verification**: pre-2023 jitoSOL parquet exists in `gs://${PID}-mtds/raw_tick_data/...`; sample probe confirms
    non-empty rows + Pyth-specific schema columns; manifest row at
    `(asset_group=defi, chain=solana, source=pyth, data_type=*)` shows captured.
- ✅ **All 13 UAC drift pairs ran QG green on the actual UAC repo**.
  - **What ran**: per-pair commit + `cd unified-api-contracts && bash scripts/quality-gates.sh`.
  - **Verification**: 13 commits in UAC origin/live-defi-rollout each green; basedpyright + ruff + tests all pass;
    workspace consumer audit finds zero stale references to flipped pairs.

**Handoff exception(s)**:

- ~~bSOL `LST_TOKEN_GENESIS` date verification can defer to Stream A successor agent~~ ✓ **CLOSED 2026-05-09**: audit
  confirmed bSOL is already in
  `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_lst.py:47` with date
  `"2022-11-24"` (BlazeStake / SolBlaze conservative floor). No further action.

---

## TAB 2 — Live pipeline + writegate Phase 5 ratchet

**Identity**: you own the cross-cutting batch=live unification thread. Live-pipeline plan is 14 phases spanning MTDS +
MDPS + features-\* — the May-23 cutover model in code form. Writegate Phase 5 ratchet is the workspace QG gate that
prevents honest-coverage % regressions post-cutover. Both are governance-grade work.

**Plan-of-record**: [`live_pipeline_mtds_mdps_features_2026_05_08.md`](live_pipeline_mtds_mdps_features_2026_05_08.md)

- [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md) Phase 5.
- [`available_at_lookahead_bias_completion_2026_05_08.md`](available_at_lookahead_bias_completion_2026_05_08.md)
  (Ikenna-owned 11-link chain meta-plan for available_at + lookahead-bias contract — links 0/3/4/5/7/8 land here).
- [`cefi_ml_may_23_2026.epic.md`](../archive/cefi_ml_may_23_2026.epic.md) (live-ML path activation for the May-23 CeFi
  ML LIVE archetype — extends live_pipeline Phase 5-7 with model serving infra).

**Scope (8 items, P0)**:

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
      [`/codex/02-data/honest_coverage_baseline_2026_05.md`](/codex/02-data/honest_coverage_baseline_2026_05.md)
      (currently a stub, needs population). Writes: UTL helper that computes honest-coverage % per shard-key from the
      manifest; base-service.sh QG STEP that fails CI if a service's coverage drops > 0.5pp from baseline; ratchet
      schedule (monthly cadence, 99% floor) per CLAUDE.md "honest absence" methodology. ~1 AI-day.
- [ ] [DESIGN+CROSS-CUTTING] P0. **`available_at` + lookahead-bias completion (11-link chain)** — Ikenna-owned meta-plan
      at [`available_at_lookahead_bias_completion_2026_05_08.md`](available_at_lookahead_bias_completion_2026_05_08.md).
      Audit 2026-05-08 found ~60% chain coverage; gaps were implicit. Tab 2 lands the cross-cutting links most tightly
      coupled to live-pipeline: link 0 (MDPS bar timestamp + available_at semantics), 3 (reader propagation), 4 (UAC
      `FEATURE_REQUIRED_INPUTS` expansion), 5 (UAC `AVAILABILITY_AT_SEMANTICS` coverage audit), 7
      (`ManifestWriter assert_available_at_present` guard), 8 (QG static check). Links 1/2/6/9/10 distributed across Tab
      1 (per-asset-group adapter stamping) + Harsh Tab 2 (calculator/writer-boundary enforcement) + cross-tab handshake.
      ~3 AI-days for Ikenna Tab 2 share; ~5 AI-days plan-total.
- [ ] [LIVE-ML+DESIGN] P0. **CeFi ML live-serving path activation** — per
      [`cefi_ml_may_23_2026.epic.md`](../archive/cefi_ml_may_23_2026.epic.md). Extends live_pipeline Phase 5-7 with: (a)
      live model artefact registry (UTL `model_registry.py` reads / GCS path SSOT); (b) hot-reload of model artefacts
      without service restart (mirror `InstrumentCacheDeltaReloader` pattern from Phase 10); (c) model-version
      traceability per trade (every `FEATURE_COMPUTED` event + every strategy decision tag includes model_version +
      model_artefact_uri); (d) live ML inference service handler in features-service compute path consuming the
      registry. **Joint with Harsh Tab 2** which wires the ML pipeline + integration test on the Harsh side. ~3 AI-days
      for Ikenna design + Harsh wiring share.
- [ ] [DESIGN] P0. **CeFi ML model-drift alerting + ML signal lifecycle alerting** — per
      [`cefi_ml_may_23_2026.epic.md`](../archive/cefi_ml_may_23_2026.epic.md) success criterion "model-drift alerting
      wired through alerting-service". Extends Tab 5 alerting Phase 2-9 with ML-specific rules (signal-staleness
      threshold, model-drift detection, P&L deviation, ML inference latency SLO). Also wires DART manual-override of ML
      trades per epic success criterion. ~2 AI-days for Tab 2 (rule design); the wiring lands in Tab 5.

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
- [`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md`](live_pipeline_mtds_mdps_features_2026_05_08.md)
- [`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`](gcs_migration_bundle_pipeline_mode_2026_05_08.md)
  (cross-cutting; pipeline_mode hive partition migration is the parallel half)
- [`/codex/05-infrastructure/live-pipeline-architecture.md`](/codex/05-infrastructure/live-pipeline-architecture.md)
- [`/codex/05-infrastructure/replay-subsystem.md`](/codex/05-infrastructure/replay-subsystem.md)
- [`/codex/02-data/pipeline-mode-partition.md`](/codex/02-data/pipeline-mode-partition.md)
- [`/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`](/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md)

**Sub-agent fan-out**:

- Phases 0-3: 4 parallel sub-agents — (a) Phase 0 audit doc; (b) Phase 1 per-venue VM topology; (c) Phase 2
  connection-pool design; (d) Phase 3 sharding-orthogonal verification across MTDS adapters.
- Phases 4-7: 5 parallel sub-agents per asset_group (cefi / defi / tradfi / sports / prediction MDPS+features colocated
  wiring) + 1 features-cross-cutting flavor. Master integrates.
- Phases 8-11: 4 parallel sub-agents — (a) replay subsystem; (b) Redis Stream cascade; (c) instrument lifecycle
  hot-reload (use existing ApiKeyReloader pattern); (d) ServiceEmissionPolicy consumer migration.
- Phase 5 ratchet: 1 general-purpose sub-agent to walk current manifest, compute per-(asset_group, data_type)
  honest-coverage %, populate baseline doc. Master writes the QG STEP + ratchet schedule.

**Phase ordering (HARD SEQUENCE — fanned-out batches gate on prior batch completion)**:

```
Phase 0 audit (read-only)
   │
   ▼
Phases 1-3 MTDS standalone cluster (per-venue VM topology + connection pool + sharding-orthogonal verification)
   │     ↳ ships MTDS topology contract that Phases 4-7 + 12-14 read
   ▼
Phases 4-7 MDPS+features-asset-scoped colocated (5 asset_groups in PARALLEL + features-cross-cutting flavor)
   │     ↳ pre-req: Phase 1-3 contract; ALSO pre-req: Harsh T2 features_repo_consolidation Phase 1-4 SHIPPED first
   │       (cross-side handshake — wait for RESOLVED in features_repo_consolidation_2026_05_08.md)
   ▼
Phases 8-11 (PARALLEL within batch): replay subsystem + Redis Stream cascade + instrument-lifecycle hot-reload +
            ServiceEmissionPolicy slice b/c consumer wiring
   │     ↳ pre-req: Phase 4-7 contracts. Phase 11 slice b couples to manifest-read — Tab 3 v7 schema must be designed
   │       in parallel + RESOLVED before Phase 11 ships
   ▼
Phases 12-14: alerting tier-up + 4-category gap tree + codex SSOT updates (PARALLEL within batch)
```

Writegate Phase 5 ratchet runs INDEPENDENTLY of live-pipeline phases (no contract coupling) — sub-agent spawns from
day-1. `available_at` 11-link chain (Ikenna's share = links 0/3/4/5/7/8) runs INDEPENDENTLY of live-pipeline phases but
couples to UAC `FEATURE_REQUIRED_INPUTS` + `AVAILABILITY_AT_SEMANTICS` SSOTs — those land before any consumer wiring
(Phase 4-7 + 8-11). CeFi ML serving path (item 7) consumes Phase 5-7 + Phase 10 instrument-lifecycle hot-reload —
sequence after Phase 8-11 ship. ML alerting design (item 8) is design-only Tab 2 work; rule wiring lands in Tab 5.

**Sub-agent isolation table** (paste rows verbatim into each Task prompt's "files OFF-LIMITS" section):

| Sub-agent ID          | Files owned (only edit these)                                                                                                                                                                       | Files OFF-LIMITS                                                                                                                                                                                                                                     |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| sa2.P0-audit          | `plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 0 audit body only (read-only on code)                                                                                           | All code surfaces                                                                                                                                                                                                                                    |
| sa2.P1-topology       | `deployment-service/scripts/vm/launch-mtds-live-{venue}-vm.sh` per-venue VM topology design + launcher template                                                                                     | MTDS adapter source files (Phase 4-7 owns); MDPS / features-\*                                                                                                                                                                                       |
| sa2.P2-connpool       | MTDS connection-pool config + tests                                                                                                                                                                 | Adapter business logic; MDPS                                                                                                                                                                                                                         |
| sa2.P3-shard-verify   | MTDS adapters' sharding-orthogonal verification (read-only audit + write tests)                                                                                                                     | MDPS; features-\*; UAC                                                                                                                                                                                                                               |
| sa2.P4-cefi           | `market-data-processing-service/...` + `features-service/cefi/...` colocated MDPS+features wiring for cefi flavor                                                                                   | Other 4 asset_group flavors; features-cross-cutting flavor; MDPS `base_adapter.py` (HARD SEQUENCE — see cross-side handshake; wait for Harsh T2 features-consolidation rewrite + then ship live-pipeline wiring; Harsh T2 lookahead-bias wires LAST) |
| sa2.P4-defi           | MDPS+features-defi colocated wiring                                                                                                                                                                 | Other 4 asset_group flavors; features-cross-cutting flavor                                                                                                                                                                                           |
| sa2.P4-tradfi         | MDPS+features-tradfi colocated wiring                                                                                                                                                               | Other 4 asset_group flavors; features-cross-cutting flavor                                                                                                                                                                                           |
| sa2.P4-sports         | MDPS+features-sports colocated wiring                                                                                                                                                               | Other 4 asset_group flavors; features-cross-cutting flavor                                                                                                                                                                                           |
| sa2.P4-pred           | MDPS+features-prediction colocated wiring                                                                                                                                                           | Other 4 asset_group flavors; features-cross-cutting flavor                                                                                                                                                                                           |
| sa2.P7-crosscut       | features-cross-cutting separate flavor (calendar / volatility / multi-timeframe / cross-instrument)                                                                                                 | Per-asset_group flavors (sa2.P4-\* own them)                                                                                                                                                                                                         |
| sa2.P8-replay         | NEW `unified_trading_library/replay_subsystem.py` + smooth-handoff-to-live shim + tests                                                                                                             | Redis Stream code (sa2.P9 owns); instrument-lifecycle hot-reload (sa2.P10); ServiceEmissionPolicy consumer wiring (sa2.P11)                                                                                                                          |
| sa2.P9-redis          | NEW Redis Stream cascade module: `CANDLE_BOUNDARY_CROSSED` + `CANDLE_COMPUTED` event types + tests                                                                                                  | Replay subsystem; instrument-lifecycle; ServiceEmissionPolicy                                                                                                                                                                                        |
| sa2.P10-instr-hot     | NEW `unified_trading_library/instrument_lifecycle_cache_delta_reloader.py` (mirror ApiKeyReloader pattern) + tests                                                                                  | Replay; Redis; ServiceEmissionPolicy                                                                                                                                                                                                                 |
| sa2.P11-emission      | ServiceEmissionPolicy slice b/c consumer migration: `manifest-read coupling` per-service helper + per-service emission policy declarations (after slice a UAC@58c3b61)                              | UAC `service_emission_policy.py` schema (slice a — already shipped); UTL `emission_publisher.py` (slice a — already shipped); Tab 3 manifest v7 schema design (sa2.P11 reads it)                                                                     |
| sa2.P12-alerting      | Live-pipeline alerting tier-up wiring — connect circuit-breaker rules into alerting-service                                                                                                         | alerting-service rule structure (Ikenna T5 owns); KillSwitchBus (Ikenna T5 owns)                                                                                                                                                                     |
| sa2.P13-gaptree       | 4-category gap tree applied to live + stale-not-missing rule via ServiceEmissionPolicy.PUBLISHED_DEGRADED                                                                                           | Replay; ServiceEmissionPolicy schema; alerting rules                                                                                                                                                                                                 |
| sa2.P14-codex         | Update 8 codex docs per Post-Plan-Phase Audit (`live-pipeline-architecture.md`, `replay-subsystem.md`, `pipeline-mode-partition.md`, `instrument-lifecycle-cache-delta-hot-reload.md` + 4 existing) | Plan body; code surfaces                                                                                                                                                                                                                             |
| sa2.WG5-ratchet       | NEW `unified_trading_library/honest_coverage_ratchet.py` + base-service.sh QG STEP + populate `/codex/02-data/honest_coverage_baseline_2026_05.md`                                                  | live-pipeline source; UAC; per-service emission consumers                                                                                                                                                                                            |
| sa2.AvailAt-MDPS      | `available_at` chain link 0 (MDPS bar timestamp) + link 3 (reader propagation)                                                                                                                      | UAC `FEATURE_REQUIRED_INPUTS` (sa2.AvailAt-UAC owns); UTL `assert_available_at_present` (sa2.AvailAt-UTL owns)                                                                                                                                       |
| sa2.AvailAt-UAC       | UAC `FEATURE_REQUIRED_INPUTS` expansion (link 4) + `AVAILABILITY_AT_SEMANTICS` coverage audit (link 5)                                                                                              | MDPS bar timestamps; UTL guard; QG static check                                                                                                                                                                                                      |
| sa2.AvailAt-UTL       | UTL `ManifestWriter.assert_available_at_present` guard (link 7)                                                                                                                                     | UAC; MDPS; QG                                                                                                                                                                                                                                        |
| sa2.AvailAt-QG        | base-service.sh QG static check (link 8) — fail CI on missing/null available_at                                                                                                                     | UAC; UTL; MDPS                                                                                                                                                                                                                                       |
| sa2.MLLive-design     | Design doc + UAC `model_registry.py` GCS path SSOT (consumed by Harsh T2 sa2.MLLive)                                                                                                                | Harsh T2's wiring side; alerting (Ikenna T5 owns)                                                                                                                                                                                                    |
| sa2.MLAlerting-design | Design doc for ML-specific alerting rules (signal-staleness threshold, model-drift detection, P&L deviation, ML inference latency SLO) — DESIGN ONLY; wiring by Ikenna T5                           | alerting-service code (Ikenna T5 owns); execution-service kill-switch consumers                                                                                                                                                                      |

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
[`gcs_migration_bundle_pipeline_mode_2026_05_08.md`](gcs_migration_bundle_pipeline_mode_2026_05_08.md)

- [`manifest_migration_master_2026_05_07.md`](../epics/manifest_migration_master_2026_05_07.md)
- [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md) Phase 3.D.4
  v2 + [`infrastructure_master_2026_05_07.md`](../epics/infrastructure_master_2026_05_07.md) v6→v7 schema.

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
- [ ] [INFRA+COORDINATION] P1. **Manifest cross-asset rescan post-CeFi VM drain** — Ownership clarified: **Ikenna T3
      writes the rescan launcher script** (in `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` or
      `deployment-service/scripts/vm/launch-manifest-rescan-vm.sh`) + designs the schema flip (which fields change,
      which stay) + handles operator-approval edge cases (any rows where rescan finds disagreement with manifest go to a
      triage file). **Harsh T4 operates the launcher** on a same-region GCE VM. Sequence: Ikenna T3 ships design +
      launcher + announces RESOLVED in
      [`manifest_migration_master_2026_05_07.md`](../epics/manifest_migration_master_2026_05_07.md) `## Open questions`
      → Harsh T4 runs `--dry-run` per asset_group → operator reviews CSV → Harsh T4 runs `--apply-write` → Ikenna T3
      handles edge-case triage. ~1 AI-day.

**Repos owned (collision boundary)**: instruments-service `scripts/enumerate_expected_universe.py` + per-VM launcher,
MTDS writers (pipeline_mode dual-write), all 5 features-\* readers, deployment-api manifest readers, data-status
readers, UTL `manifest_v7.py` (new module), all consumer services for the Phase 4 reader migration. Hands off the actual
rescan VM operation to Harsh Tab 4.

**Read-first**:

- CLAUDE.md sections: "Manifest migration, NOT fallback" rule, "Honest absence vs fake placeholders", "Per-VM shard
  isolation for concurrent backfills", "Manifest concurrency principle", "Manifest phantom audit"
- [`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`](gcs_migration_bundle_pipeline_mode_2026_05_08.md)
- [`plans/epics/manifest_migration_master_2026_05_07.md`](../epics/manifest_migration_master_2026_05_07.md)
- [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)
- [`/codex/02-data/pipeline-mode-partition.md`](/codex/02-data/pipeline-mode-partition.md)
- [`/codex/02-data/chunk-safe-manifest-migrations.md`](/codex/02-data/chunk-safe-manifest-migrations.md)

**Sub-agent fan-out**:

- GCS migration Phases 0-3: 4 parallel sub-agents — (a) Phase 0 audit; (b) writer dual-write per asset_group; (c) Phase
  2 backfill replay; (d) Phase 3 reader fallback. Master coordinates handoff between phases.
- Phases 4-7: 5 parallel sub-agents per asset_group consumer cutover + 1 codex SSOT updater. Master removes the fallback
  in a final commit after all 5 cutovers verify.
- Manifest v7 design: 1 architecture sub-agent drafts the schema + migration script. Master reviews + ships.
- Expected_universe v2: 1 sub-agent extends the v1 enumerator with catalog-join. Master operates the launches.

**Phase ordering (HARD SEQUENCE)**: GCS Phase 0 audit → Phase 1 dual-write enable on writers → Phase 2 backfill replay
tagging → Phase 3 reader fallback shim → Phase 4 per-service consumer cutover → Phase 5 fallback removal → Phase 6
reconciler verification → Phase 7 codex SSOT updates. Phase 5 ONLY ships after ALL Phase 4 cutovers verify (otherwise
consumers break). Manifest v7 design + expected_universe v2 enumerator + cross-asset rescan launcher ship in PARALLEL
with GCS Phase 0-3 (independent contracts). v7 design must be RESOLVED before Ikenna T2 Phase 11 slice b consumes the
per-(shard_key, day) ServiceEmissionPolicy state column.

**Sub-agent isolation table** (paste rows verbatim into each Task prompt's "files OFF-LIMITS" section):

| Sub-agent ID        | Files owned (only edit these)                                                                                                                                              | Files OFF-LIMITS                                                                                                                                           |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| sa3.GCS-P0-audit    | `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 0 audit body only (read-only on code)                                                                | All code surfaces                                                                                                                                          |
| sa3.GCS-P1-cefi     | MTDS writer dual-write for cefi asset_group (`pipeline_mode=batch` hive partition tag-on-write)                                                                            | Other 4 asset_group writers                                                                                                                                |
| sa3.GCS-P1-defi     | MTDS writer dual-write for defi                                                                                                                                            | Other 4 asset_group writers                                                                                                                                |
| sa3.GCS-P1-tradfi   | MTDS writer dual-write for tradfi                                                                                                                                          | Other 4 asset_group writers                                                                                                                                |
| sa3.GCS-P1-sports   | MTDS writer dual-write for sports                                                                                                                                          | Other 4 asset_group writers                                                                                                                                |
| sa3.GCS-P1-pred     | MTDS writer dual-write for prediction                                                                                                                                      | Other 4 asset_group writers                                                                                                                                |
| sa3.GCS-P2-replay   | Backfill replay tagger script (read existing parquets + tag with `pipeline_mode=batch` hive partition); idempotent + resumable + per-shard checkpointed                    | Reader fallback (sa3.GCS-P3 owns); consumer cutover (sa3.GCS-P4-\* own them)                                                                               |
| sa3.GCS-P3-fallback | NEW reader-fallback shim in MDPS / features-\* / deployment-api consumer paths (read both partitions during cutover)                                                       | Writers (sa3.GCS-P1-\* own them); replay tagger                                                                                                            |
| sa3.GCS-P4-cefi     | cefi consumer cutover (per-service: features-cefi reader + deployment-api cefi data-status reader + reconciler)                                                            | Other 4 asset_group consumer cutovers; writers; reader fallback shim                                                                                       |
| sa3.GCS-P4-defi     | defi consumer cutover                                                                                                                                                      | Other 4 asset_group consumer cutovers                                                                                                                      |
| sa3.GCS-P4-tradfi   | tradfi consumer cutover                                                                                                                                                    | Other 4 asset_group consumer cutovers                                                                                                                      |
| sa3.GCS-P4-sports   | sports consumer cutover                                                                                                                                                    | Other 4 asset_group consumer cutovers                                                                                                                      |
| sa3.GCS-P4-pred     | prediction consumer cutover                                                                                                                                                | Other 4 asset_group consumer cutovers                                                                                                                      |
| sa3.GCS-P5-fb-rm    | Reader-fallback removal (final commit after ALL Phase 4 cutovers verify)                                                                                                   | Anything else — this is a single mechanical removal commit                                                                                                 |
| sa3.GCS-P6-recon    | Reconciler walks manifest + cross-checks bucket layout per asset_group                                                                                                     | Source code edits                                                                                                                                          |
| sa3.GCS-P7-codex    | Update 6 codex docs per Post-Plan-Phase Audit (1 NEW `/codex/02-data/pipeline-mode-partition.md` + 5 UPDATE existing)                                                      | Plan body; code surfaces                                                                                                                                   |
| sa3.V7-design       | NEW `unified_trading_library/manifest_v7.py` (formalise per-(shard_key, day) ServiceEmissionPolicy state column) + 1-time migration script + reader-removal of v6 fallback | UAC manifest schema (Wave 4 slice a — already shipped); Tab 2 sa2.P11 ServiceEmissionPolicy consumer wiring (sa3.V7-design ships SCHEMA, sa2.P11 reads it) |
| sa3.ExpUniv-v2      | `instruments-service/scripts/enumerate_expected_universe.py` v2 (cross-bucket join with catalog) + per-VM launcher                                                         | v1 enumerator (already shipped); manifest v7 schema (sa3.V7-design owns)                                                                                   |
| sa3.Rescan-launcher | NEW `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` rescan launcher script + design doc; triage file generator for Harsh T4 to consume                | Harsh T4 operational invocation surface (Harsh runs the launcher); v6→v7 migration script (sa3.V7-design)                                                  |

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

**Plan-of-record**: [`aws_migration_defi_first_2026_05_07.md`](aws_migration_defi_first_2026_05_07.md) +
cross-references to [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) Group F.

**Scope (4 items, P0-P1)**:

- [ ] [INFRA+TESTING] P0. **AWS Phase 3 cross-cloud parity smoke** — `CLOUD_PROVIDER=aws` read-path on DeFi shards (the
      5 buckets created Phase 2 at deployment-service@7da2f3d). Health-check passes against AWS-resident DeFi manifest +
      sample parquet read returns expected rows. Per CLAUDE.md "Force-Sync Warning" + "AWS Migration" framework. ~2
      AI-days.
- [ ] [INFRA+CODEX] P0. **`/codex/05-infrastructure/cloud-agnostic-script-pattern.md` SSOT population** — currently a
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
- [`plans/active/aws_migration_defi_first_2026_05_07.md`](aws_migration_defi_first_2026_05_07.md) full body
- [`/codex/05-infrastructure/cloud-agnostic-migration.md`](/codex/04-architecture/cloud-agnostic-migration.md) (existing
  — read for the migration framework)
- [`/codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md`](/codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md)
  (per-resource cost snapshot extracted from the archived analysis; operator credit + steady-state cost decision)

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

**Plan-of-record**: [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md)

- [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) Group F+G +
  [`deploy_missing_auto_launch_2026_05_07.md`](deploy_missing_auto_launch_2026_05_07.md) Phase 0.

**Scope (5 items, P0)**:

- [ ] [ARCHITECTURE+DESIGN] P0. **Alerting Phase 2 KillSwitchBus rule wiring** — declarative half shipped 2026-05-07 at
      alerting-service@b025e83 (37 unit tests, `triggers_kill_switch=True` flag set on `KILL_SWITCH_*` rules).
      **Publish-side hook + integration test pending** per
      [`../archive/issues/alerting_kill_switch_publish_hook_2026_05_08.md`](../archive/issues/alerting_kill_switch_publish_hook_2026_05_08.md):
      when an alert with `triggers_kill_switch=True` fires through `route_event`, it must publish a `KillSwitchEvent` to
      the UTL bus so execution-service halt subscribers consume it. **Done**: hook wired + integration test +
      execution-service halt-on-event behaviour verified. ~1.5 AI-days.
- [ ] [ARCHITECTURE+DESIGN] P0. **Alerting Phase 2 — `CROSS_CLOUD_EGRESS_DETECTED` rule + AAVE utilization-spike
      threshold value** — audit §3 #5 flagged AAVE threshold ambiguous; resolve via DeFi-team judgment call
      (per-archetype: `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`; renamed from legacy
      `leveraged_funding_arb` per Stream B canonicalisation 2026-05-07) 9000 bps_of_one (90%) vs default 9500 (95%) per
      UAC@d00326d) + lock as documented decision. ~1 AI-day.
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
- [ ] [LIVE-ML+ARCHITECTURE] P0. **CeFi ML alerting wiring + kill-switches + DART manual-override** — per
      [`cefi_ml_may_23_2026.epic.md`](../archive/cefi_ml_may_23_2026.epic.md) success criteria "Live alerting active" +
      "Kill switches + circuit breakers wired per archetype" + "DART manual override". Wires Tab 2's design (this same
      plan §"Tab 2 item 8") through alerting-service routing rules + execution-service kill-switch consumers + DART
      pause/override/replicate UI via strategy_and_dart_master Phase 2.2. Without this, the May-23 LIVE cefi_ml epic
      ships unprotected (operator pages would be the only kill-switch — unacceptable institutional shape per CLAUDE.md
      "DeFi Execution Architecture"). ~3 AI-days.

**Repos owned (collision boundary)**: alerting-service (full ownership), UAC `alerting.py` / `crosscutting/alerting.py`
(Phase 1 shipped, additions only), deployment-api routing (auth_middleware.py for audit-log integration; collides with
**Harsh Tab 3 deployment-ui-lifecycle-tabs** if Harsh edits same routes — see cross-side handshake), PM master plan
(Group F+G refresh — Tab 5 only writes; other tabs don't touch master plan during this cycle).

**Read-first**:

- CLAUDE.md sections: "Master Plan — Live DeFi Trading by 2026-05-23" intro, "Service Infrastructure Requirements",
  "DeFi Execution Architecture" (kill-switch context), "Force-Sync Warning"
- [`plans/active/alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md)
- [`plans/active/master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) Group F + G full
- [`plans/active/deploy_missing_auto_launch_2026_05_07.md`](deploy_missing_auto_launch_2026_05_07.md) Phase 0 + the 3
  STATUS DRAFT proposals
- [`/codex/15-runbooks/alerting/alert-code-taxonomy.md`](/codex/15-runbooks/alerting/alert-code-taxonomy.md)
- [`/codex/15-runbooks/alerting/threshold-tuning.md`](/codex/15-runbooks/alerting/threshold-tuning.md)

**Sub-agent fan-out**:

- Alerting Phase 2 hook: 1 architecture sub-agent designs the route_event → KillSwitchBus hook + integration test
  fixture. Master ships + verifies execution-service halt subscriber.
- Alerting Phase 3-9: 7 parallel sub-agents (one per phase). Each produces a self-contained deliverable. Master
  integrates + ships each as separate commits.
- Master refresh: 7 parallel sub-agents (one per master plan workstream A-G). Each reports what shipped this cycle vs
  what remains. Master writes the refreshed critical-path section + flips Group F/G checkboxes.
- Deploy_missing Phase 0: operator-driven; you facilitate the 3 decisions then sub-agents propagate.

**Collision risk**:

- Master plan: Tab 5 ONLY tab that writes to master_to_live_defi_2026_05_23.md this cycle. Other tabs MUST NOT touch
  (per CLAUDE.md "Two teammates × multiple parallel agents — don't edit unfamiliar files").
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

## TAB 6 — Cross-cutting design (catalogue + IDs + clients + DART scope)

**Identity**: you own the cross_cutting epic's deliverables #1-#4 (strategy catalogue, strategy IDs, clients + accounts,
DART manual-trade lane scope). Audit 2026-05-08 found these were unassigned across Tabs 1-5; this tab is the operator's
mid-cycle add to close the gap before May-23. Pure design / UAC SSOT work — Harsh Tab 6 implements once you ship.

**Plan-of-record**: [`cross_cutting_may_23_deliverables_2026_05_08.md`](cross_cutting_may_23_deliverables_2026_05_08.md)
(shared with Harsh Tab 6) +
[`plans/epics/cross_cutting_may_23_2026.epic.md`](../epics/cross_cutting_may_23_2026.epic.md) (parent epic) +
[`/codex/09-strategy/strategy-summary.md`](/codex/09-strategy/strategy-summary.md) (existing 8-family / 18-archetype
catalogue baseline).

**Scope (5 items, P0-P1)**:

- [ ] [DESIGN+UAC] P0. **Strategy catalogue UAC schema** — declare in
      `unified_api_contracts/canonical/strategy/catalogue.py`: `StrategyArchetype` enum (carry / price-arb /
      ml-prediction / prediction-markets / others); `CatalogueRow` dataclass with
      `(archetype, venue, instrument_type,     asset_group, live_vs_backtest, config)`; `ArchetypeConfig` per-family
      (collateral_currency, hedge_ratio, position_cap_usd, kill_switch_drawdown_pct, kill_switch_position_breach_pct).
      Resolve open question "bar for complete" — default = full enumeration including not-launching-this-cycle
      archetypes per cross_cutting epic deliverable #1 framing. **Done**: UAC schema ships, unit tests covering 3+
      archetype families. ~3 AI-days.
- [ ] [DESIGN+UAC] P0. **Strategy ID UAC schema** — declare canonical naming + versioning rule in
      `unified_api_contracts/canonical/strategy/ids.py`. Default proposal: `<archetype>.<venue>.<instrument_type>.v<N>`
      (e.g. `carry_staked_basis.bybit.perp.v1`); N increments on material config change (collateral / hedge ratio /
      position cap shifts). Provide `derive_strategy_id(catalogue_row) → StrategyId` function. **Done**: UAC schema
      ships, unit tests covering ID derivation + versioning. ~2 AI-days.
- [ ] [DESIGN+UAC] P0. **Client model UAC + capital allocation matrix** — extend
      `unified_api_contracts/canonical/client/model.py` with `Client` (id, accounts: list[(venue, account_id)]) +
      `CapitalAllocation` per (client, archetype, venue) declaring
      `(initial_capital_usd, max_position_pct,     max_drawdown_pct)`. Allocation respected at execution-service entry —
      execution rejects if computed position would breach allocation. **Done**: schema ships, unit tests covering
      allocation respect + tagging propagation shape. ~2 AI-days.
- [ ] [DESIGN] P0. **DART manual-trade lane scope spec** — write
      `/codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md` (or extend existing
      `operational-modes-matrix.md`) with per-archetype list of operator-replicable manual surfaces. Required surfaces:
      (a) DeFi swap / lend / borrow / stake actions per chain × protocol for `carry_staked_basis`; (b) CeFi order
      placement (limit / market / stop) across Bybit / Deribit / Binance / OKX; (c) ML training trigger (pause / resume
      / retrain) per ML archetype; (d) sports bet placement for backtest exec validation; (e) prediction-market trade
      for backtest. Resolve open question "operator-only or external broker-style" — default = operator-only this cycle.
      **Done**: codex doc ships + Harsh T6 has executable spec. ~2 AI-days.
- [ ] [DESIGN] P1. **Strategy catalogue UI scope decision** — filter axes (asset_group / archetype / venue /
      live-vs-backtest) confirmed; UI route in deployment-UI declared; Harsh T6 implements UI per spec. **Done**:
      operator-confirmed UI scope + route assignment in `deployment_ui_lifecycle_tabs_2026_05_08`. ~1 AI-day.

**Read first**:

- [`plans/epics/cross_cutting_may_23_2026.epic.md`](../epics/cross_cutting_may_23_2026.epic.md) — 5-deliverable scope
- [`cross_cutting_may_23_deliverables_2026_05_08.md`](cross_cutting_may_23_deliverables_2026_05_08.md) — shared
  plan-of-record (you write to its `## Open questions` for blockers; Harsh T6 reads it)
- [`/codex/09-strategy/strategy-summary.md`](/codex/09-strategy/strategy-summary.md) — existing catalogue baseline
- [`/codex/09-strategy/operational/onboarding-checklist.md`](/codex/09-strategy/operational/onboarding-checklist.md) —
  strategy onboarding flow (your schemas wire into this)
- [`/codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md`](/codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md)
  — DART manual-trade lane SSOT (extend or peer doc)

**Sub-agent fan-out**:

- 1 main agent: design judgment + UAC schema authoring
- 2 sub-agents (parallel): (a) strategy catalogue row enumeration from existing codex (which archetypes × venues exist,
  even if not in scope today) — output to Harsh T6 as input; (b) DART scope research across deployment-ui /
  unified-trading-system-ui to identify existing manual-action surfaces to extend vs add.

**Sub-agent isolation table** (paste rows verbatim into each Task prompt's "files OFF-LIMITS" section):

| Sub-agent ID         | Files owned (only edit these)                                                                                                                                                        | Files OFF-LIMITS                                                                                                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| sa6.UAC-catalogue    | NEW `unified_api_contracts/canonical/strategy/catalogue.py` schema (StrategyArchetype enum + CatalogueRow dataclass + ArchetypeConfig per-family) + tests                            | `canonical/strategy/ids.py` (sa6.UAC-ids owns); `canonical/strategy/cme_polymarket_arb_archetype.py` (Harsh T5 sa5.CMEPolyArb owns — same DIR but DIFFERENT file; sa6 ships catalogue first) |
| sa6.UAC-ids          | NEW `unified_api_contracts/canonical/strategy/ids.py` (canonical naming + versioning rule + `derive_strategy_id`) + tests                                                            | `canonical/strategy/catalogue.py` (sa6.UAC-catalogue owns); `canonical/client/`                                                                                                              |
| sa6.UAC-client       | NEW `unified_api_contracts/canonical/client/model.py` (Client + accounts list + CapitalAllocation per (client, archetype, venue)) + tests                                            | `canonical/strategy/`; UAC `chain_env.py` (Ikenna T1 owns)                                                                                                                                   |
| sa6.DART-spec        | NEW `/codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md` (5 surfaces: DeFi swap/lend/stake, CeFi orders, ML training trigger, sports bet, prediction-market) | UAC; existing codex `operational-modes-matrix.md` (read-only reference)                                                                                                                      |
| sa6.CatalogueRowEnum | Read-only enumeration of `(archetype, venue, instrument_type)` combos from existing codex `strategy-summary.md` 8-family / 18-archetype baseline → output spec doc                   | All UAC; codex (read-only)                                                                                                                                                                   |
| sa6.DART-research    | Read-only research across deployment-ui / unified-trading-system-ui to identify existing manual-action surfaces (extend vs add for each of 5 DART surfaces)                          | All UI source; UAC                                                                                                                                                                           |

Master sa6 (Tab 6 orchestrator) owns: orchestration + integration + design judgment + per-deliverable RESOLVED block in
`cross_cutting_may_23_deliverables_2026_05_08.md` `## Open questions` so Harsh T6 can consume. UAC editor priority queue
(per cross-side handshakes): sa6 ships NEW dirs (`canonical/strategy/`, `canonical/client/`) FIRST since they have zero
overlap risk; subsequent UAC editors (Harsh T2 `feature_family`, Harsh T5 mechanical adds) wait per the queue.

**Done-definition**:

- [ ] All 4 UAC schemas merged: catalogue, IDs, client model, capital allocation
- [ ] DART scope codex doc shipped (operator-confirmed) + Harsh T6 has executable spec
- [ ] Strategy catalogue UI scope assigned (deployment-UI route declared)
- [ ] Plan-of-record `## Open questions` resolved or escalated
- [ ] DONE block appended to plan-of-record citing every UAC + codex commit sha

**Collision risk**: Tab 6 modifies UAC `canonical/strategy/` + `canonical/client/`. Tab 1 modifies UAC
`canonical/ crosscutting/chain_env.py` (different files). Harsh T5 might add UAC enums for hard_schema (different
module). Use `git add -p` if you both edit UAC in the same window. PM master plan is read-only for this tab (Tab 5
owns).

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
- [ ] **Tab 6 (strategy ID UAC schema) → Tab 1 (DeFi paper-trade smoke) + Tab 5 (alerting + master Group F refresh)**:
      paper-trade smoke fills + alerting rules + Group F items (PBM / R&E / pnl-attribution / batch-live-recon) all gate
      on strategy ID attribution. **Mitigation**: Tab 6 ships ID schema early (Day 1 of cycle); Tab 1 paper-trade tags
      fills with derived strategy IDs once schema lands; Tab 5's alerting rules emit strategy ID per fired alert.

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
- [ ] **MDPS `base_adapter.py` 3-way collision — HARD SEQUENCE (codified 2026-05-08 audit)**: three sub-agents touch
      this file across two operators. To prevent the documented foot-gun pattern (PM@961980db / @611b9501 / @34075d84)
      where parallel `git add` / reset wipes staged hunks, enforce: 1. **Harsh T2 features-consolidation Phase 1-4 ships
      FIRST** — extracts features-cefi/tradfi compute paths into `features-service/`, replacing existing MDPS
      `base_adapter.py` calls. 2. **Ikenna T2 sa2.P4-cefi (live-pipeline) wires SECOND** — adds pipeline_mode
      partition + replay subsystem hooks to MDPS `base_adapter.py` AFTER Harsh T2 has finished its rewrite sweep +
      pushed. 3. **Harsh T2 sa2.PhaseAB×8 (lookahead-bias) wires THIRD** — adds `assert_no_lookahead_for_feature_group`
      calls at compute entry, on top of the live-pipeline-wired version. Each step waits for the previous step's
      RESOLVED block in [`features_repo_consolidation_2026_05_08.md`](features_repo_consolidation_2026_05_08.md) /
      [`live_pipeline_mtds_mdps_features_2026_05_08.md`](live_pipeline_mtds_mdps_features_2026_05_08.md)
      `## Open     questions`. **No surgical `git add -p` in parallel** — sequence enforced via plan-of-record
      signaling.
- [ ] **Harsh Tab 3 (deployment-ui-lifecycle-tabs auth re-shape) → Ikenna Tab 5 (deploy_missing audit-log
      integration)**: audit-log integration wraps the auth re-shape. Hard ordering: Harsh ships auth re-shape Phase 1;
      Ikenna ships audit-log on top.
- [ ] **Harsh Tab 4 (per-asset_group VM ops + reconcilers) → Ikenna Tab 3 (cross-asset rescan design + LAUNCHER)**:
      Ownership clarified — **Ikenna T3 sa3.Rescan-launcher writes the rescan launcher script** (in
      `instruments-service/scripts/` or `deployment-service/scripts/vm/`); **Harsh T4 operates it** on a same-region GCE
      VM. Sequence: Ikenna T3 ships design + launcher + announces RESOLVED in
      [`manifest_migration_master_2026_05_07.md`](../epics/manifest_migration_master_2026_05_07.md) `## Open questions`
      → Harsh T4 runs `--dry-run` per asset_group → operator reviews CSV → Harsh T4 runs `--apply-write` → Ikenna T3
      handles edge-case triage file.
- [ ] **UAC editor priority queue (codified 2026-05-08 audit)**: Up to 4+ sub-agents could touch UAC simultaneously
      across both sides. The conditional-push rule catches collisions at push time but earlier serialization is cheaper.
      **Priority queue (top → bottom; each waits for previous to RESOLVED in
      `cross_cutting_may_23_deliverables_2026_05_08.md` `## Open questions`)**: 1. Ikenna T6 NEW dirs
      (`canonical/strategy/catalogue.py`, `ids.py`, `canonical/client/model.py`) — brand-new files, zero overlap risk;
      ships first. 2. Ikenna T1 `chain_env.py` flips — already shipped UAC@6c873e4; remaining drift fixes in same
      window. 3. Harsh T2 sa2.P5-uac-col `feature_family` column in `canonical/feature/family.py` (NEW dir). 4. Harsh T5
      sa5.HardSchema `canonical/manifest/schema_v6.py` column adds. 5. Harsh T5 sa5.APIFootball
      `external/api_football/normalize.py:377-381`. 6. Harsh T5 sa5.CMEPolyArb
      `canonical/strategy/cme_polymarket_arb_archetype.py` — same DIR as Ikenna T6 (#1) but DIFFERENT FILE; serialize
      after Ikenna T6 ships catalogue + ids files so the dir state is stable. Each editor pre-commit-checks
      `git diff --cached --name-only` matches their assigned file subset exactly.
- [ ] **Ikenna Tab 6 (UAC strategy SSOTs + DART scope) → Harsh Tab 6 (consumer wiring + DART UI)**: cross_cutting epic
      deliverables #1-#4. **Hard ordering**: Ikenna T6 ships UAC catalogue + ID + client schemas + DART codex spec
      first; Harsh T6 consumes after. **Mitigation**: Harsh T6 can scaffold the strategy ID refactor sweep (identify
      every callsite that needs an ID without modifying yet) in parallel with Ikenna T6 schema design. Ikenna T6
      announces `## Open questions` resolved per-deliverable; Harsh T6 reads then ships.

## Collision-risk callouts (file-level)

- **MDPS `base_adapter.py` / `BaseCandleAdapter`** (3-way collision — see HARD SEQUENCE in Cross-side handshakes above):
  Harsh T2 features-consolidation rewrite FIRST → Ikenna T2 sa2.P4-cefi live-pipeline wiring SECOND → Harsh T2
  sa2.PhaseAB×8 lookahead-bias wires THIRD. Sequence enforced via plan-of-record signaling, NOT parallel `git add -p`.
- **UAC** (4+ editor priority queue — see HARD QUEUE in Cross-side handshakes above): Ikenna T6 NEW dirs first → Ikenna
  T1 drift fixes → Harsh T2 `feature_family` column → Harsh T5 schema/normalize/archetype adds in order. Each editor
  pre-commit-checks `git diff --cached --name-only` matches assigned subset.
- **PM master plan**: Ikenna Tab 5 ONLY writes to it; all other tabs read-only.
- **deployment-api `auth_middleware.py`**: Harsh Tab 3 (auth re-shape) THEN Ikenna Tab 5 (audit-log). Sequence enforced.
- **`live-defi-rollout` push race**: per CLAUDE.md conditional push rule. Pre-commit `git status` +
  `git diff --cached --stat` (no path arg) MANDATORY before EVERY commit. Use `git add -p` / `git add <specific-file>`
  only. Branch does NOT trigger remote CI — every shippable unit's local `bash scripts/quality-gates.sh` Pass 1 is the
  ONLY quality gate (per top-of-file CI gate reminder).
- **Pre-commit hook prettier reformat**: any markdown edit triggers prettier. Files you didn't author may get
  reformatted as a side-effect; this is acceptable if content is unchanged. Reference: PM@8b3f949d this morning bundled
  prettier reformats of 6 plans + 2 archive copies for this same reason.

## Daily sync points

- **EOD T+0** (today, midnight UTC): Tabs 1-6 each report done-definition status to operator via plan-of-record
  `## Open questions` resolved + DONE block. Operator runs `git log --oneline -25 origin/live-defi-rollout` to see the
  day's shipments.
- **Tomorrow's daily reset**: 1 main-orchestrator-or-operator runs the daily reset per CLAUDE.md (fetch summary + Q&A
  sweep + draft tomorrow's split). Carryover items roll forward; shipped items reflect in master plan flip.
- **2026-05-15 GCS migration deadline**: Tab 3's GCS bundle migration MUST land by then per the plan frontmatter.
  Earlier is better; latest is acceptable.
- **2026-05-23 live-DeFi cutover**: master plan Group F+G must all be ✅. Tab 5's master refresh tracks the gap.

## Deferred work after 2026-05-10 audit session

The 2026-05-10 PM governance hygiene sweep (this audit session, agent-tag `pm-governance-hygiene-tab`) shipped 13
PM-only governance ships: archive of operator_decisions (lifecycle deadline passed) + 7 resolved issue docs + alerting
Q1 back-flip + manifest_v7 SUPERSEDED banner + launcher_scripts plan-flip + arbitrage Q11 verification + this
scoreboard. Items still open from prior cycles + cross-tab dependencies are tracked here so the next agent picks up
cleanly without re-reading session notes.

| Phase / item                                                        | Status as of 2026-05-10                                 | Successor / blocker                                                                                                                                           |
| ------------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| cefi_master Q1 — helper-shipped pending owner flip                  | `helper-shipped`                                        | Owner picks up + flips checkbox to `[x]` once consumer wire-in audit completes                                                                                |
| predictions_master Q2 — design-shipped                              | `design-shipped`                                        | Pickup agent wires consumer per design contract; flip on wire-in landing                                                                                      |
| `available_at_lookahead_bias_completion_2026_05_08.md` Phase 1      | `design-ready`                                          | Owner agent implements per design; ratchets writegate Phase 5                                                                                                 |
| `simulation_scenarios_topology_price_shocks_2026_05_09.md`          | `operator-needs-decision`                               | Operator triages topology choice; agent picks up post-decision                                                                                                |
| Master plan Continuous Verification matrix per HARD RULE 2026-05-08 | `in-flight (main agent shipping bbc35344 this session)` | Main agent finishes the per-row Continuous Verification column; reviewers gate refresh PRs on it (see CLAUDE.md "Master Plan Continuous-Verification Column") |
| F6 deeper-df-flow refactor                                          | `operator-needs-decision`                               | See `../archive/issues/f6_df_flow_refactor_blocked_by_available_at_2026_05_08.md` + `f6_record_captured_requires_df_features_consolidation_2026_05_08.md`     |
| defi_master Q1                                                      | `operator-needs-decision`                               | Operator triage; defi_master_2026_05_07.md Q&A surface                                                                                                        |
| alerting Phase 4-9                                                  | `operator-needs-scheduling`                             | PagerDuty + Telegram chat structure operator decisions ratified per `operator_decisions_2026_05_08.md`; Phase 4-9 implementation pending operator scheduling  |
| F2-v2 item 2 — in-flight Tab G                                      | `in-flight`                                             | Tab G's session in flight; carryover via Tab G's DONE block                                                                                                   |
| Wave-2 Phase 1+3 — in-flight Tab G                                  | `in-flight`                                             | Same — carryover via Tab G                                                                                                                                    |
| writegate Phase 4.A — in-flight Tab H                               | `in-flight`                                             | Tab H's session in flight                                                                                                                                     |
| `wave3x_residual_ssots_2026_05_08.md` Track A — in-flight Tab H     | `in-flight`                                             | Same — carryover via Tab H                                                                                                                                    |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **Phase 2 (deployment-api launcher registry)** + **Phase 3 (UI cloud-toggle audit)** of
  `launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`: DEFERRED-PER-AUDIT /
  DEFERRED-AFTER-AWS-PHASE-1 annotations added this session; pending Tab 5 governance
  - `aws_migration_defi_first_2026_05_07.md` Phase N execution.

## Defer post-cutover (BOTH must NOT touch)

- DART v2 archetype roadmap (HUMAN-P1 in `strategy_and_dart_master`)
- Marketing copy reconciliation (master §25.A.1-A.3)
- `ml_and_features_master` Phase 4 (Bayesian / calibration / advanced caching)
- `mtds_per_instrument_download_api` Phase 2 + Phase 3 (Phase 1.5 chain axis IS in scope per Harsh Tab 5)
- AWS Phase 5-9 (beyond CeFi-instruments + DeFi)
- `strategy_and_dart_master` Phase 1 service-split full refactor + Phase 5 Unity UAT (operator-only $550 + Java binary)
- `predictions_master` non-Phase-1 work (P1; in Harsh Tab 1 scope only if Phase 1 lands cleanly mid-cycle)
- `consolidated_strategy_and_ui` Phase 3 deep work (now under `strategy_and_dart_master`)
- [`fund_administration_service_and_pooled_subscription_redemption_2026_04_20`](fund_administration_service_and_pooled_subscription_redemption_2026_04_20.md)
  (post-2026-05-23 P2 per cross-plan position banner)
- [`ml_pipeline_ui_integration_2026_04_16`](ml_pipeline_ui_integration_2026_04_16.md) (deferred unless last 2 todos
  verifiable today)
  <!-- CORRECTION 2026-05-08 audit: removed cross-side scope contradictions per audit cluster 7.
       api_football_minimal_flattening_removal + data_status_comprehensive_test_coverage are P0 in-scope
       for Harsh Tab 5 ("the dragon" mechanical refactor) — not deferred this cycle. Both plans must agree;
       Harsh's side wins because it has the implementation tab assignment. -->
  <!-- moved: api_football_minimal_flattening_removal_2026_05_07.md → owned by Harsh Tab 5 sa5.APIFootball -->
  <!-- moved: data_status_comprehensive_test_coverage_2026_05_07.md → owned by Harsh Tab 5 (item #2) -->

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
  4. plans/active/defi_master_2026_05_07.md (full body — your primary plan-of-record).

Your agent-tag for ping-ledger entries: defi-fork1-completion-tab.
Your tab number: 1.

ORCHESTRATION RULES (per CLAUDE.md § "Daily Work-Split Process" universal mechanics):
  1. Shared working tree — no `git pull` needed between tabs; pre-commit check
     (git status + git diff --cached --stat NO PATH ARG) mandatory before EVERY commit.
     Use `git add -p` for shared files; never `git add -A` / `git add <whole-shared-file>`.
  2. Plan-doc Q&A flow — write blockers into defi_master_2026_05_07.md `## Open questions`
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
Final: append a "DONE-2026-05-08" block at the bottom of defi_master_2026_05_07.md
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
  3. plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md (your primary
     plan-of-record).
  4. plans/active/writegate_honest_coverage_endtoend_2026_05_06.md Phase 5 (your
     secondary plan-of-record).
  5. /codex/05-infrastructure/live-pipeline-architecture.md + replay-subsystem.md +
     /codex/02-data/pipeline-mode-partition.md +
     /codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md.

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
  3. plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md (primary).
  4. plans/epics/manifest_migration_master_2026_05_07.md.
  5. plans/active/writegate_honest_coverage_endtoend_2026_05_06.md § Phase 3.D.4 v2.

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
  3. plans/active/aws_migration_defi_first_2026_05_07.md (primary).
  4. /codex/05-infrastructure/cloud-agnostic-script-pattern.md (currently a stub — you populate it).

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
  3. plans/active/alerting_service_live_rules_2026_05_07.md (primary).
  4. plans/active/master_to_live_defi_2026_05_23.md Group F+G full bodies.
  5. plans/active/deploy_missing_auto_launch_2026_05_07.md Phase 0.
  6. /codex/15-runbooks/alerting/alert-code-taxonomy.md + threshold-tuning.md.

Your agent-tag: alerting-master-governance-tab. Your tab number: 5.

YOUR TASK: ship Alerting Phase 2 KillSwitchBus hook + Phase 3-9 alerting wiring + master
plan Group F+G refresh + deploy_missing Phase 0 IAM/audit-log/rate-limit decisions LOCKED.
See work_split_2026_05_08_ikenna.md § "TAB 5".

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE block at bottom of each plan-of-record.
This tab runs LAST (it consumes the cycle's shipments via master refresh).
```

### Tab 6 spawn prompt

```text
You are Tab 6 — a sub-agent spawned by Ikenna's main orchestrator agent (a separate Claude
Code session on the SAME PC, sharing the SAME .git/ + working tree as you).

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — full body (workspace standards). Esp.
     § "Daily Work-Split Process" + § "Two teammates × multiple parallel agents — don't
     edit unfamiliar files" + § "Sub-Agents & Autonomous Agents: Full Rules Required" +
     § "UAC Citadel Architecture".
  2. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (symlink to CLAUDE.md;
     same content — sub-agent framing applies to you).
  3. plans/active/work_split_2026_05_08_ikenna.md § "TAB 6 — Cross-cutting design
     (catalogue + IDs + clients + DART scope)" including the Sub-agent isolation table
     (paste rows verbatim into each Task prompt).
  4. plans/active/cross_cutting_may_23_deliverables_2026_05_08.md (shared plan-of-record
     with Harsh Tab 6 — you write per-deliverable RESOLVED blocks; Harsh T6 reads them).
  5. plans/epics/cross_cutting_may_23_2026.epic.md — 5-deliverable scope (parent epic).
  6. /codex/09-strategy/strategy-summary.md — existing 8-family / 18-archetype catalogue
     baseline (your enumeration source).
  7. /codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md — DART manual-trade lane
     existing SSOT (extend or peer with new dart-manual-trade-spec.md).

Your agent-tag: cross-cutting-design-tab. Your tab number: 6.

ORCHESTRATION RULES (per CLAUDE.md § "Daily Work-Split Process" universal mechanics):
  1. Shared working tree — no `git pull` needed between tabs; pre-commit check
     (git status + git diff --cached --stat NO PATH ARG) mandatory before EVERY commit.
     Use `git add -p` for shared files; never `git add -A` / `git add <whole-shared-file>`.
  2. Plan-doc Q&A flow — write blockers into cross_cutting_may_23_deliverables_2026_05_08.md
     `## Open questions` (status 🟡 BLOCKED), append ping in plans/active/_agent_pings.md,
     continue with what you CAN do.
  3. Conditional push — per shippable unit: commit locally, fetch + check incoming, zero
     incoming → push, any incoming → flag + escalate.
  4. Plan-flip in same logical unit as code — checkbox flip + <repo>@<sha> evidence stamped
     in body, NOT batched at session end.
  5. Findings Triage Discipline (HARD RULE) — case-1-to-5 routing per CLAUDE.md.

CRITICAL HANDSHAKES (HARD ORDERING — Tab 6 IS THE FIRST UAC EDITOR THIS CYCLE):
  • UAC editor priority queue (cross-side handshakes): Tab 6 ships NEW dirs
    (`canonical/strategy/catalogue.py`, `canonical/strategy/ids.py`,
    `canonical/client/model.py`) FIRST since they have zero overlap risk. Other UAC
    editors (Ikenna T1 drift fixes, Harsh T2 `feature_family` column, Harsh T5 mechanical
    adds) wait per the queue. Announce each NEW file as RESOLVED in plan-of-record
    `## Open questions` so Harsh T6 + downstream UAC editors can proceed.
  • Cross-side: Harsh T6 consumes your UAC schemas + DART codex spec for the implementation
    side (refactor sweep + catalogue rows + client tagging + 5 DART manual-trade UIs +
    catalogue UI). Per-deliverable RESOLVED gating: ship deliverable #1 (catalogue
    schema) → Harsh T6 reads + populates rows → ship deliverable #2 (ID schema) → Harsh
    T6 starts ID refactor sweep → ship deliverable #3 (client model) → Harsh T6 wires
    client tagging → ship deliverable #4 (DART spec) → Harsh T6 ships 5 DART surfaces.
  • Cross-tab within Ikenna: Tab 1 paper-trade smoke fills + Tab 5 alerting rules + Tab 5
    master Group F refresh ALL gate on Tab 6 strategy-ID schema (Tab 6 ships first;
    others consume).

YOUR TASK: ship the 5 items in TAB 6 (strategy catalogue UAC schema + strategy ID UAC
schema + client model UAC + DART manual-trade lane scope spec + strategy catalogue UI
scope decision). Fan out per the Sub-agent isolation table. See
work_split_2026_05_08_ikenna.md § "TAB 6" for full done-definition + file-ownership
table.

REPORT-BACK: per shippable unit, code commit + plan-flip commit, conditional push.
Final: append a "DONE-2026-05-08" block at the bottom of
cross_cutting_may_23_deliverables_2026_05_08.md body listing every UAC + codex commit
sha. Then go quiet — don't pick up new work autonomously.
```

## Spawn prompts — fresh fan-out: instruments-service + MTDS (PM 2026-05-08)

> Fresh batch of 4 mechanical/scoped items spawned mid-cycle (Model B sub-agents on top of the existing Model A 6-tab
> clustering). Each touches instruments-service or MTDS only, file-disjoint from Tabs 1-6 in flight.
>
> **Master gate first.** Before spawning F2 or F3, the master agent (you) MUST ship A.9 + A.10 from
> [`instruments_live_master_2026_05_08.md`](../epics/instruments_live_master_2026_05_08.md) lines 204-221 — preflight
> DAG SSOT (UAC) + UTL helper. F2 + F3 consume the helper. F1 + F4 + F5 can spawn immediately.
>
> **Collision audit (vs Tabs 1-6 already in flight):**
>
> - **Item dropped**: MTDS Phase 3 websocket `--mode live` — owned by Tab 2 already, not re-spawned.
> - F1 (instruments-service `cli/`) vs F4 (instruments-service `triggers/`) — different sub-packages, surgical
>   `git add -p` per pre-commit check rule.
> - F2 + F5 in MTDS — file-disjoint: F2 lives in `market_tick_data_service/adapters/{venue}.py` (10 cefi venues), F5 in
>   `orchestrator/` + `adapters/polymarket.py` + `adapters/kalshi.py`. No overlap.
> - F2 vs Tab 2 — Tab 2 owns CLI + scheduler, F2 owns per-venue adapter `available_at` stamping. File-disjoint.

### Tab F1 spawn prompt — instruments-service CLI `--trigger` axis (A.7)

```text
You are Tab F1 — a sub-agent spawned by Ikenna's main orchestrator agent (a separate Claude
Code session on the SAME PC, sharing the SAME .git/ + working tree as you).

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — workspace rules + § "Daily Work-Split Process".
  2. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — sub-agent inheritance.
  3. plans/active/work_split_2026_05_08_ikenna.md § "Spawn prompts — fresh fan-out" — collision map + master gate.
  4. plans/epics/instruments_live_master_2026_05_08.md § "A.7 — CLI `--trigger` axis" lines 182-189
     (your primary plan-of-record).
  5. /codex/06-coding-standards/cli-convention.md — service CLI axes (`--operation`, `--mode`, `--asset-group`).

Your agent-tag for ping-ledger entries: instruments-cli-trigger-tab. Your tab number: F1.

ORCHESTRATION RULES (per CLAUDE.md § "Daily Work-Split Process"):
  1. Shared working tree — pre-commit check (git status + git diff --cached --stat NO PATH ARG) before
     EVERY commit. Use `git add -p` / `git add <specific-file>`. Never `git add -A`.
  2. Plan-doc Q&A flow — write blockers into instruments_live_master_2026_05_08.md `## Open questions`
     (status 🟡 BLOCKED), append ping in plans/active/_agent_pings.md.
  3. Conditional push — per shippable unit: commit locally, `git fetch`, zero incoming → push,
     any incoming → flag + escalate.
  4. Plan-flip in same logical unit as code — `- [ ]` → `- [x]` with `<repo>@<sha>` evidence.
  5. Findings Triage Discipline (HARD RULE) — case-1-to-5 routing per CLAUDE.md.

YOUR TASK: extend instruments-service CLI with `--mode live --trigger <name>` flag axis. Additive only —
don't break existing batch CLI. Per CLAUDE.md § "Service CLIs follow standardised axes":
  - Add `--trigger` argparse arg accepting trigger names (e.g. `cefi.instruments.daily_refresh`,
    `defi.token_lists.refresh`, `sports.fixtures.daily_repoll`).
  - Wire trigger-name → handler dispatch via existing pattern in instruments-service CLI.
  - Add unit tests asserting flag parses + dispatches to handler. Use existing test fixtures.
  - Do NOT implement the actual triggers — that's downstream phases (B.1 / C / D).

REPOS OWNED: instruments-service only.
COLLISION BOUNDARY: instruments-service `cli/` only — F4 owns `triggers/`. Don't touch trigger handler files.

DONE DEFINITION:
  ✅ `instruments-service --mode live --trigger <name>` parses without error for ≥3 trigger names.
  ✅ Unit tests cover argparse + dispatch (real, not mocked — actual CLI invocation in a subprocess
     OR direct argparse-call assertion).
  ✅ `cd instruments-service && bash scripts/quality-gates.sh` Pass 1 GREEN.
  ✅ Commit + push to live-defi-rollout per shippable-unit cadence.
  ✅ Plan-flip in plans/epics/instruments_live_master_2026_05_08.md A.7 → `- [x]` with sha.

REPORT-BACK: per shippable unit (commit + plan-flip + push). Final: DONE-2026-05-08 block at the
bottom of instruments_live_master_2026_05_08.md listing every commit sha. Then go quiet.
```

### Tab F2 spawn prompt — CeFi adapter `available_at` stamping (10 venues × 5 data_types)

```text
You are Tab F2 — a sub-agent spawned by Ikenna's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "`available_at` is per-row, write-time, equal
     to live-pipeline-arrival" + § "Live = batch — same data, same fields, same timing semantics".
  2. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md.
  3. plans/active/work_split_2026_05_08_ikenna.md § "Spawn prompts — fresh fan-out" — master gate +
     collision map.
  4. plans/epics/cefi_master_2026_05_07.md § "Per-adapter `available_at` stamping" lines 387-396.
  5. plans/active/available_at_lookahead_bias_completion_2026_05_08.md (related sweep).
  6. unified_api_contracts.canonical.crosscutting.source_priority.SOURCE_PRIORITY (top entries are
     live-emission timing source; SSOT for stamping latency).

Your agent-tag: cefi-available-at-stamping-tab. Your tab number: F2.

ORCHESTRATION RULES: same 5 rules as Tab F1 above.

PRE-REQ GATE: master agent ships A.9 + A.10 (preflight DAG SSOT + UTL helper) FIRST. If you boot
and `unified_trading_library.preflight_dag` (or equivalent UTL helper from A.10) doesn't exist yet,
write a 🟡 BLOCKED entry on cefi_master_2026_05_07.md `## Open questions` and wait. Don't fork ahead.

YOUR TASK: stamp per-row `available_at` on every CeFi MTDS adapter before `record_captured`. Mirror
the existing sports `_enforce_pit_sports` pattern. Per UAC SOURCE_PRIORITY top entry per
(asset_group, data_type), `available_at = tick_ts + emission_latency_ms`.

VENUES (10 total): bybit, binance, okx, deribit, kraken, bitfinex, bitget, coinbase, gate, kucoin.
DATA_TYPES per venue: trades, ohlcv_1m, ohlcv_15m, funding, open_interest (cefi-relevant subset only —
skip data_types the venue doesn't emit; check existing adapter source-of-truth for the venue's actual
supported data_types list, don't invent).

For each adapter file `market_tick_data_service/adapters/{venue}.py`:
  - Find `record_captured(...)` callsite + the rows-being-written DataFrame.
  - Add `df["available_at"] = stamp_available_at_cefi_tick(df["timestamp"], venue, data_type)` (use
    UTL helper from `unified_trading_library.availability_stamping` — confirm signature first;
    helper exists per CLAUDE.md § "available_at is per-row, write-time").
  - Write unit test under `market-tick-data-service/tests/adapters/test_{venue}_available_at.py`
    asserting stamped column exists + values are in [tick_ts, tick_ts + 60s].
  - Verify `LookaheadBiasError` doesn't fire in batch + live modes via the existing UTL guard.

REPOS OWNED: market-tick-data-service only.
COLLISION BOUNDARY: only `market_tick_data_service/adapters/{venue}.py` files. Do NOT touch
`market_tick_data_service/cli/` (Tab 2 owns), `orchestrator/` (F5 owns), `streaming/` (Tab 2 owns).

DONE DEFINITION:
  ✅ All 10 cefi venue adapters stamp `available_at` per-row before record_captured.
  ✅ Per-venue unit tests pass (10 new test files, 1 per venue).
  ✅ `cd market-tick-data-service && bash scripts/quality-gates.sh` Pass 1 GREEN.
  ✅ FULL-EXECUTION CRITERION (per CLAUDE.md HARD RULE): pick 1 venue (bybit recommended — already
     has live data on disk) and read 1 sample parquet via `pandas.read_parquet()` AFTER landing your
     edits. Assert `available_at` column exists + values match the stamping formula. Cite the
     parquet path + sample row in the DONE block. Smoke-test alone is insufficient.
  ✅ Commit + push per shippable-unit (recommend 1 commit per venue = 10 commits, not bundled).
  ✅ Plan-flip cefi_master_2026_05_07.md per-venue checkbox → `- [x]` with sha.

REPORT-BACK: per-venue commit + per-venue plan-flip. Final: DONE-2026-05-08 block at the bottom
of cefi_master_2026_05_07.md. Then go quiet.
```

### Tab F4 spawn prompt — sports daily fixture re-poll (B.1) + UTL `available_at` test (A.8)

```text
You are Tab F4 — a sub-agent spawned by Ikenna's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "Sports source coverage windows" +
     § "available_at is per-row, write-time".
  2. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md.
  3. plans/active/work_split_2026_05_08_ikenna.md § "Spawn prompts — fresh fan-out".
  4. plans/epics/instruments_live_master_2026_05_08.md § "A.8 — UTL ManifestWriter `available_at`
     confirmation" lines 194-200 + § "B.1 — Sports daily fixture re-poll" lines 285-294.
  5. instruments-service existing api_football fixtures handler (your reference implementation).

Your agent-tag: sports-fixtures-repoll-tab. Your tab number: F4.

ORCHESTRATION RULES: same 5 rules as Tab F1 above.

YOUR TASK: TWO scoped items, ship in order.

ITEM 1 (A.8 — quickest, ship first): Add unit test confirming UTL `ManifestWriter.record_captured`
already handles per-row `available_at` correctly. The behaviour is expected to exist already — this
is a verification test, not new functionality. Test must:
  - Construct a DataFrame with `available_at` column (UTC timestamps).
  - Call `ManifestWriter.record_captured(...)` with the DataFrame.
  - Assert no `LookaheadBiasError` raised + manifest row written with correct shape.
If the behaviour does NOT exist, write 🟡 BLOCKED on instruments_live_master_2026_05_08.md `## Open
questions` and STOP — escalate to master agent.

ITEM 2 (B.1 — main work): Implement sports daily fixture re-poll trigger.
  - Add trigger handler `instruments_service/triggers/sports_fixtures_daily_repoll.py`.
  - Trigger name: `sports.fixtures.daily_repoll`.
  - Behaviour: pull fixtures from api_football for window [today, today + 8d]; upsert to the same
    GCS path as batch fixtures (per UAC `candidate_parquet_paths(SPORTS_FIXTURES, day, league_id)`).
  - Idempotent — re-running same day + same league = no duplicate rows.
  - Stamp `available_at = announced_at` (per CLAUDE.md "fixtures → announced_at").
  - Add integration test asserting trigger writes parquet + manifest row at expected GCS path.

REPOS OWNED: instruments-service only (item 2) + unified-trading-library only (item 1).
COLLISION BOUNDARY: F1 owns instruments-service `cli/`; you own `triggers/` + UTL test only.
Don't touch CLI argparse — F1's job. Wire your trigger name into the existing dispatcher F1 builds
ONCE F1 has shipped — coordinate via plan-of-record Q&A bus if F1 hasn't shipped yet.

DONE DEFINITION:
  ✅ Item 1: UTL `available_at` test green; commit + plan-flip A.8 → `- [x]`.
  ✅ Item 2: trigger handler + integration test green; commit + plan-flip B.1 → `- [x]`.
  ✅ Both repos' `bash scripts/quality-gates.sh` Pass 1 GREEN.
  ✅ FULL-EXECUTION CRITERION: actually invoke the trigger end-to-end against api_football
     (real API, real ADC, real GCS write) for 1 league (premier-league recommended — full
     fixture coverage). Verify `gcloud storage ls gs://...sports-data-prod/by_date/day=<today>/
     entity=fixtures/league=39/` returns the new parquet. Read sample to confirm
     `available_at` populated. Cite GCS URI + sample row in DONE block. Mocked test alone
     insufficient.
  ✅ Push per shippable unit.

REPORT-BACK: per shippable unit. Final: DONE-2026-05-08 block at the bottom of
instruments_live_master_2026_05_08.md listing both A.8 + B.1 commit shas. Then go quiet.
```

### Tab F5 spawn prompt — Polymarket / Kalshi manifest re-bundling Phase 2

```text
You are Tab F5 — a sub-agent spawned by Ikenna's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "Prediction market lifecycle timing"
     + § "Cluster validation MANDATORY at `record_captured` for bundled shards" + § "Shard-
     granularity SSOT".
  2. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md.
  3. plans/active/work_split_2026_05_08_ikenna.md § "Spawn prompts — fresh fan-out".
  4. plans/epics/predictions_master_2026_05_07.md § "Q1 + A1 — Manifest re-bundling for
     Polymarket/Kalshi" lines 108-160 (your primary plan-of-record).
  5. instruments-service@b904785 commit (Phase 1 reference impl: lifecycle timestamps +
     canonical_question_group on instrument definitions — already shipped).
  6. instruments-service@98bb167 commit (Phase 1 supporting work).
  7. UAC `BUNDLED_DATA_TYPES` registry + `prediction_canonical_question_group` data_type
     (search `unified-api-contracts/unified_api_contracts/canonical/crosscutting/honest_coverage.py`).

Your agent-tag: polymarket-rebundling-tab. Your tab number: F5.

ORCHESTRATION RULES: same 5 rules as Tab F1 above.

PRE-REQ GATE: confirm UAC `BUNDLED_DATA_TYPES` includes `prediction_canonical_question_group`
+ helper signature for cluster validation is locked. If unclear, write 🟡 BLOCKED on
predictions_master_2026_05_07.md `## Open questions` for master agent to resolve.

YOUR TASK: implement MTDS orchestrator-side re-bundling for Polymarket + Kalshi ticks. Per option
(a) chosen in predictions_master_2026_05_07.md A1: bundle by `canonical_question_group` at the
manifest layer.

Concrete shape:
  - Read instrument definitions from instruments-service catalog (UAC contract for prediction
    instruments — confirm reader path).
  - For each tick batch, group by `instrument_def.canonical_question_group` (e.g.
    `BTC_UP_DOWN_HOURLY` aggregates 24 market_ids/day).
  - Write bundled parquet per `(canonical_question_group, day)`.
  - Call `ManifestWriter.record_captured(..., expected_root_clusters={...},
    cluster_extractor=lambda row_key: row_key.market_id)` per CLAUDE.md § "Cluster validation
    MANDATORY". Cluster count = HOURLY → 24, DAILY → 1, ELECTION → 1.
  - Respect lifecycle bounds: skip ticks before `market_created_at`, after `settlement_time`.

REPOS OWNED: market-tick-data-service only.
COLLISION BOUNDARY: `market_tick_data_service/orchestrator/` + `market_tick_data_service/adapters/
polymarket.py` + `market_tick_data_service/adapters/kalshi.py`. Do NOT touch other adapters
(F2 owns cefi adapters), do NOT touch `cli/` or `streaming/` (Tab 2 owns).

DONE DEFINITION:
  ✅ Polymarket adapter writes bundled parquet per `(canonical_question_group, day)`.
  ✅ Kalshi adapter writes bundled parquet per `(canonical_question_group, day)`.
  ✅ Cluster validation fires `record_failed(ClusterCoverageError(...))` when expected market_ids
     are missing — verify with a deliberate failing test (drop 1 market_id, assert error).
  ✅ `cd market-tick-data-service && bash scripts/quality-gates.sh` Pass 1 GREEN.
  ✅ FULL-EXECUTION CRITERION: launch a small backfill VM (or local 1-day run with real ADC) for
     1 canonical group (`BTC_UP_DOWN_HOURLY`, 1 day). Verify manifest has `record_captured` row
     with cluster_count=24 (or actual count for that day if some markets weren't created yet).
     Read sample bundled parquet, assert all expected market_ids present. Cite GCS URI in DONE.
  ✅ Commit + push per shippable unit.

REPORT-BACK: per shippable unit. Final: DONE-2026-05-08 block at the bottom of
predictions_master_2026_05_07.md Q1/A1 section listing every commit sha. Then go quiet.
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

When all 6 tabs hit their per-tab done-definition, today's Ikenna split is complete. Tab 5 then runs the master refresh
capturing the cycle's shipped work. EOD: archive this plan to `plans/archive/work_split_2026_05_08_ikenna.md`

- draft tomorrow's `work_split_2026_05_09_ikenna.md` per the daily reset protocol.

## Cross-references

- Companion: [`work_split_2026_05_08_harsh.md`](work_split_2026_05_08_harsh.md) — Harsh's mirror plan.
- Methodology spec: [`cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) §"Daily Work-Split Process".
- Yesterday's archived split:
  [`plans/archive/work_split_2026_05_07_ikenna_5tab_layout.md`](../archive/work_split_2026_05_07_ikenna_5tab_layout.md).
- Master plan: [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) — the durable readiness model.

## VM Status — Tab 1 main launches (2026-05-08 14:11 UTC)

Two VMs launched after operator green-lit "do everything" per session direction:

- **mtds-lending-indices-20260508-141147** RUNNING — relaunch of lending-indices full backfill (2022-01-01 → 2026-05-07)
  with refreshed DEFI tarball post-UAC@6c873e4. Predecessor `mtds-lending-indices-20260508-114519` (Tab 9, 7h running)
  was deleted before relaunch — its progress was ~60% through but using OLD COMPOUND V3 dates that would have required
  rescan. Manifest concurrency principle ensures already-captured rows skip; only empty/failed boundary days re-process
  with corrected UAC dates.
- **mtds-pyth-archive-20260508-141204** RUNNING — first launch of new Pyth Hermes archive backfill VM, default window
  2022-11-01 → 2023-09-30 (jitoSOL genesis → ORACLE_COVERAGE_START boundary). Cascades Pyth Hermes (post-2023-10-01) →
  Pythnet RPC (pre-2023-10-01) → CoinGecko fallback per oracle_prices_handler routing.

**Pre-flight checks (all green 2026-05-08 14:12 UTC)**:

- Pyth Hermes endpoint: HTTP 200 in 158ms.
- Solana RPC `api.mainnet-beta.solana.com`: `getHealth` returns `ok`.
- UAC `venue_accepts_collateral('DRIFT', 'JitoSOL')` = True; `('DRIFT', 'mSOL')` = True.

**Verification cadence**: 90s STARTED + 10-15min progress events per VM (per CLAUDE.md "No fire-and-forget VM launches"
rule). Schedule wakeup set for 14:15 UTC.

**Commits this hour**:

- deployment-service@0722ac4 — Pyth-archive launcher + watchdog dict prefix.
- DEFI tarball refreshed twice (post-UAC@6c873e4 + post-deployment-service@0722ac4) — bundles VMs pull at boot.
