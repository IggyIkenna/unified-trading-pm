
## 2026-06-24 — Phase 5 Snapshot governance DONE + next task BLOCKED

**Phase 5 Snapshot governance (defi_governance_params_refresh-001):** ✅ SHIPPED
- UAC: `GOVERNANCE_PROPOSAL_LIVE` AlertCode + AlertRule (HIGH/PAGERDUTY/TELEGRAM) + typed event model — uac@e8c69d6d
- MTDS: `snapshot_space_monitor.py` adapter + `SnapshotGovernanceMonitorHandler` + CLI `monitor-snapshot-governance` + 12 unit tests — mtds@c17deb33
- Deployment-service: `governance_snapshot_monitor_scheduler.tf` (0 */6 * * * UTC cron, aavedao/comp-vote/morpho) + registry — ds@c91b1d9d
- Plan flip: pm@37ad8d1d

**Next task (defi_mtds_subgraph_and_adapter_fixes-002): BLOCKED-OPERATOR-DECISION**
Extended-Starknet Phase 5 is gated on asset_group classification for CLOB-on-chain venues (Lighter/Pacifica/Extended):
- Option (a): extend DeFi asset_group to include them (default, minor mental tension)
- Option (b): new `clob_dex` asset_group (clean but workspace-wide vocab churn)
- Note: STARKNET_RPC_TEMPLATES already in UAC + `_umi_extended.py` candle adapter already exists — only the classification + final wiring remains.
- Blocked as BLK-f731f51a in orchestrator.

Plan ref: `plans/active/defi_mtds_subgraph_and_adapter_fixes_2026_06_20.md` line 81
