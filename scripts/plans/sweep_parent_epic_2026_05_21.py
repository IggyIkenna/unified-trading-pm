#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: oneoff
# Delete-when: after prod-run + orphan-sweep=0
"""
Orphan parent_epic sweep — 2026-05-21.

For every active plan in plans/active/*.md that is either:
  (a) ORPHAN (no parent_epic: frontmatter), OR
  (b) MISROUTED (parent_epic: points at a SUPERSEDED archaeology slug from the 2026-05-21 epic reorg)
scans the first 250 lines (frontmatter + body) + scores against each of the 19 active epic slugs based on
keyword matches + proposes a parent_epic.

Score = (filename match * 10) + (frontmatter match * 5) + (body match * 1). Highest-scoring epic wins.
Ties + low-confidence cases flagged for operator review (no auto-patch).

Special handling:
  - The cutover master (master_to_live_defi_2026_05_23.md) is NOT an epic — skipped.
  - Index files (INDEX.md, _agent_pings.md, _operator_broadcast_*.md, AUDIT_* without parent) are SKIPPED
    by default (use --include-index to include them).
  - Continuation-prompt files (continuation_prompts_*.md) are SKIPPED — they're ephemeral session artifacts.
  - Plans pointing at a SUPERSEDED slug get re-routed:
       strategy_and_dart_master_SUPERSEDED_2026_05_21 → strategy_master OR dart_and_promote_master (content-decided)
       manifest_evolution_SUPERSEDED_2026_05_21        → manifest_master
       manifest_migration_SUPERSEDED_2026_05_21        → manifest_master
       cross_cutting_may_23_SUPERSEDED_2026_05_21      → client_isolation_and_governance_master

Usage:
    python3 unified-trading-pm/scripts/plans/sweep_parent_epic_2026_05_21.py --dry-run
    python3 unified-trading-pm/scripts/plans/sweep_parent_epic_2026_05_21.py --apply
    python3 unified-trading-pm/scripts/plans/sweep_parent_epic_2026_05_21.py --apply --include-index

Exit codes:
    0 = clean (orphan count after = 0 OR all remaining flagged for operator review)
    1 = unexpected (file unreadable, frontmatter malformed)
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

WORKSPACE = Path("/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1")
PM = WORKSPACE / "unified-trading-pm"
ACTIVE = PM / "plans" / "active"

SCAN_LINES = 250

# ---------- Active epic slugs (19) + skip list ----------

ACTIVE_EPICS = [
    # L0 — Asset-group ops
    "defi_master",
    "cefi_master",
    "tradfi_master",
    "sports_master",
    "predictions_master",
    # L1 — Data pipeline
    "instruments_master",
    "mtds_mdps_master",
    "features_and_ml_master",
    "manifest_master",
    # L2 — Trading core
    "strategy_master",
    "execution_master",
    "trading_agent_master",
    # L3 — Operator surfaces
    "dart_and_promote_master",
    "deployment_and_user_management_master",
    # L4 — Cross-cutting
    "infrastructure_master",
    "observability_master",
    "batch_live_symmetry_master",
    "client_isolation_and_governance_master",
    # L5 — Meta
    "orchestrator_master",
]

SUPERSEDED_SLUGS = {
    "strategy_and_dart_master_SUPERSEDED_2026_05_21",  # split target depends on content
    "manifest_evolution_SUPERSEDED_2026_05_21",
    "manifest_migration_SUPERSEDED_2026_05_21",
    "cross_cutting_may_23_SUPERSEDED_2026_05_21",
}

# Default re-routes for SUPERSEDED parent_epic values (overridable via content score)
SUPERSEDED_DEFAULTS = {
    "manifest_evolution_SUPERSEDED_2026_05_21": "manifest_master",
    "manifest_migration_SUPERSEDED_2026_05_21": "manifest_master",
    "cross_cutting_may_23_SUPERSEDED_2026_05_21": "client_isolation_and_governance_master",
    # strategy_and_dart split is content-decided between strategy_master + dart_and_promote_master
}

# Files we never auto-patch (ephemeral / coordination / non-plan)
SKIP_FILENAMES_DEFAULT = {
    "INDEX.md",
    "_agent_pings.md",
    "master_to_live_defi_2026_05_23.md",  # cutover master — NOT an epic
}

SKIP_GLOBS_DEFAULT = [
    "continuation_prompts_*.md",  # session artifacts
    "_operator_broadcast_*.md",  # broadcast notes
    "_AUDIT_*.md",  # legacy audit snapshots (start with _)
    "AUDIT_*.md",  # legacy audit snapshots
    "work_split_*.md",  # daily orchestration coordination, not domain plans
    "human_work_backlog_*.md",  # orchestration coordination
    "pm_coordination_ledger_*.md",  # orchestration coordination
    "_*.md",  # leading-underscore files = coordination/meta
]

# Filename prefix → epic (strong signal; overrides keyword scoring when confident)
FILENAME_PREFIX_RULES: list[tuple[str, str]] = [
    # Orchestrator-related (high confidence)
    ("agent_orchestrator_", "orchestrator_master"),
    ("orchestrator_", "orchestrator_master"),
    ("agent_reliability_", "orchestrator_master"),
    # Manifest-related
    ("manifest_", "manifest_master"),
    ("d3_manifest_", "manifest_master"),
    ("honest_coverage_", "manifest_master"),
    ("expected_unattempted_", "manifest_master"),
    ("gate_3_phantom_", "manifest_master"),
    # MTDS / MDPS / data pipeline
    ("mtds_", "mtds_mdps_master"),
    ("mdps_", "mtds_mdps_master"),
    ("dex_perp_", "mtds_mdps_master"),
    ("live_pipeline_mtds_", "mtds_mdps_master"),
    ("d4_mtds_", "mtds_mdps_master"),
    # Features / ML
    ("ml_repo_", "features_and_ml_master"),
    ("features_repo_", "features_and_ml_master"),
    ("features_service_", "features_and_ml_master"),
    ("phase5_features_", "features_and_ml_master"),
    # Strategy + archetypes
    ("strategy_archetype_", "strategy_master"),
    ("strategy_execution_contract_", "strategy_master"),
    ("config_grid_archetype_", "strategy_master"),
    ("defi_archetypes_", "strategy_master"),
    ("defi_recursive_borrow_", "strategy_master"),
    # Execution
    ("execution_service_", "execution_master"),
    # Trading agent
    ("trading_agent_", "trading_agent_master"),
    # DART + promote
    ("dart_", "dart_and_promote_master"),
    ("promote_workflow_", "dart_and_promote_master"),
    # Observability
    ("alerting_", "observability_master"),
    # Client isolation + governance
    ("per_client_isolation_", "client_isolation_and_governance_master"),
    ("cross_client_funds_", "client_isolation_and_governance_master"),
    # Batch / live symmetry
    ("batch_live_symmetry_", "batch_live_symmetry_master"),
    ("available_at_schema_lift_", "batch_live_symmetry_master"),
    # Infrastructure
    ("aws_migration_", "infrastructure_master"),
    ("deployment_ui_", "deployment_and_user_management_master"),
    ("d0_orchestrator_", "orchestrator_master"),
    ("d1_is_", "instruments_master"),
    # Defi-specific (only after specific prefixes above)
    ("api_keys_wallets_", "defi_master"),
    ("defi_protocol_", "defi_master"),
    ("defi_catalogue_", "defi_master"),
    # Bucket / SSOT (manifest territory)
    ("bucket_name_ssot_", "manifest_master"),
    # Universe / expected universe
    ("expected_universe_", "instruments_master"),
]


def filename_prefix_match(plan_path: Path) -> str | None:
    """Return the epic slug matching a filename prefix rule, or None."""
    fn = plan_path.name
    for prefix, epic in FILENAME_PREFIX_RULES:
        if fn.startswith(prefix):
            return epic
    return None


# ---------- Keyword tables per epic ----------
# Order matters — earlier keywords are stronger (each keyword contributes equally within a list,
# but matching multiple keywords from the same list = additive score).

EPIC_KEYWORDS: dict[str, list[str]] = {
    # L0
    "defi_master": [
        "defi",
        "DeFi",
        "DEFI",
        "aave",
        "compound",
        "lido",
        "stETH",
        "lst",
        "morpho",
        "uniswap",
        "curve",
        "balancer",
        "jito",
        "marinade",
        "copper",
        "on-chain",
        "on_chain",
        "ethereum",
        "arbitrum",
        "base",
        "optimism",
        "polygon",
        "wallet_provisioning",
        "carry_staked_basis",
        "carry_recursive",
        "arbitrage_price_dispersion",  # also overlap with strategy
    ],
    "cefi_master": [
        "cefi",
        "CeFi",
        "CEFI",
        "binance",
        "bybit",
        "okx",
        "deribit",
        "hyperliquid",
        "kraken",
        "aster",
        "ccxt",
        "CEFFU",
        "perp_funding",
        "perp hedge",
        "spot",
        "perpetual_swap",
        "futures_chain",
    ],
    "tradfi_master": [
        "tradfi",
        "TradFi",
        "TRADFI",
        "databento",
        "opra",
        "cme",
        "cboe",
        "ibkr",
        "yahoo",
        "fred",
        "ecb",
        "vix",
        "es_micro",
        "nq_micro",
        "ETF",
        "dated_future",
    ],
    "sports_master": [
        "sports",
        "Sports",
        "SPORTS",
        "sportradar",
        "betfair",
        "smarkets",
        "matchbook",
        "odds_api",
        "footystats",
        "fixture",
        "league",
        "gbp_sports",
        "epl",
        "nba",
        "premier_league",
    ],
    "predictions_master": [
        "prediction",
        "Prediction",
        "PREDICTION",
        "polymarket",
        "kalshi",
        "binary_outcome",
        "prediction_market",
        "MARKET_LIFECYCLE",
    ],
    # L1
    "instruments_master": [
        "instruments-service",
        "instruments_service",
        "InstrumentRecord",
        "universe",
        "reference_data",
        "venue_universe",
        "instrument_universe",
    ],
    "mtds_mdps_master": [
        "mtds",
        "MTDS",
        "market-tick-data",
        "market_tick_data",
        "mdps",
        "MDPS",
        "market-data-processing",
        "market_data_processing",
        "data_pipeline",
        "data-pipeline",
        "writegate",
        "tick_timestamp",
        "raw_tick_data",
        "ohlcv",
        "candle",
        "raw market data",
    ],
    "features_and_ml_master": [
        "features-service",
        "features_service",
        "feature_group",
        "ml-service",
        "ml_service",
        "ml-inference",
        "ml_inference",
        "ml-training",
        "ml_training",
        "MLPrediction",
        "cascade_prediction",
        "model_promotion",
        "ml_repo_consolidation",
        "features_streaming",
    ],
    "manifest_master": [
        "manifest",
        "Manifest",
        "ManifestWriter",
        "schema_version",
        "v8",
        "honest_absence",
        "honest_coverage",
        "empty_confirmed",
        "expected_unattempted",
        "attempted_failed",
        "manifest_consolidator",
        "phantom_manifest",
        "EMPTY_CONFIRMED_REASONS",
    ],
    # L2
    "strategy_master": [
        "strategy-service",
        "strategy_service",
        "strategy_archetype",
        "archetype",
        "carry_staked_basis",
        "arbitrage_price_dispersion",
        "portfolio_allocator",
        "AllocationSizer",
        "AllocationEngine",
        "share_class",
        "ShareClass",
        "BaseArchetypeEngineV2",
        "V2EngineOrchestrator",
        "kelly",
        "Kelly",
        "pnl_attribution",
        "risk_rules",
        "ARCHETYPE_RULES",
        "position_balance",
        "TreasuryMonitor",
        "MarkPriceAggregator",
    ],
    "execution_master": [
        "execution-service",
        "execution_service",
        "TransferHandler",
        "TransferCoordinator",
        "OrderRouter",
        "fill_engine",
        "matching_engine",
        "DefiCostAggregator",
        "execution_handler",
        "perp_hedge_sizer",
        "DeleverageExecutor",
        "FlashLoanReceiver",
        "execution_provider",
        "OperationType",
        "TRADE_INSTRUCTION",
    ],
    "trading_agent_master": [
        "trading-agent-service",
        "trading_agent_service",
        "AllocationDirective",
        "StrategyPnlStreamEvent",
        "closed_loop_allocator",
        "directive_pipeline",
        "ArchetypeAllocationDirective",
        "StrategyDirectiveReloader",
    ],
    # L3
    "dart_and_promote_master": [
        "DART",
        "dart_",
        "ManualTradeGateDialog",
        "promote_workflow",
        "promote-workflow",
        "promote button",
        "MinimalCandidateManifest",
        "candidate_manifest",
        "StrategyMaturityPhase",
        "paper_1d",
        "live_early",
        "state_machine",
        "dart_three_way",
        "DartThreeWayView",
    ],
    "deployment_and_user_management_master": [
        "deployment-api",
        "deployment_api",
        "deployment-ui",
        "deployment_ui",
        "user-management-service",
        "user_management_service",
        "user-management-ui",
        "user_management_ui",
        "deployment-stack",
        "deployment_stack",
    ],
    # L4
    "infrastructure_master": [
        "infrastructure",
        "infra",
        "vm-tarball",
        "tarball-deployment",
        "per-tab-worktree",
        "per_tab_worktrees",
        "vm_zombie_watchdog",
        "launch-strategy",
        "launch-mtds",
        "launch-features",
        "VM_PREFIX_TO_BUCKET",
        "EPHEMERAL_BATCH",
        "LifecycleClass",
        "cloud-build",
        "terraform",
    ],
    "observability_master": [
        "alerting-service",
        "alerting_service",
        "alerting_rules",
        "telegram_alert",
        "telegram-alert",
        "monitor",
        "telemetry",
        "auto_recovery",
        "auto-recovery",
        "3am",
        "stuck-agent",
        "stuck_detection",
    ],
    "batch_live_symmetry_master": [
        "batch_live",
        "batch=live",
        "batch-live",
        "batch vs live",
        "live=batch",
        "reconciliation",
        "writegate_honest_coverage",
        "available_at",
        "batch-live-reconciliation",
    ],
    "client_isolation_and_governance_master": [
        "client_isolation",
        "client-isolation",
        "per_client_isolation",
        "ClientWorker",
        "ClientAdmissionController",
        "ShardCapacitySensor",
        "cross_client",
        "CrossClientTransferForbidden",
        "jurisdiction",
        "share_class_collision",
        "uac_schema",
        "UAC schema",
        "share_class_registry",
        "client_funds_isolation",
        "intra_client",
        "IntraClientRebalanceCoordinator",
    ],
    # L5
    "orchestrator_master": [
        "orchestrator",
        "agent-orchestrator",
        "agent_orchestrator",
        "multi_vm",
        "multi-vm",
        "vm_registry",
        "planning_vm",
        "planning-vm",
        "epic_vm",
        "epic-vm",
        "main_agent",
        "review_agent",
        "worker_agent",
        "vm_topology",
    ],
}


# ---------- Dataclasses ----------


@dataclass
class Proposal:
    plan_path: Path
    current_parent: str  # "" if orphan; SUPERSEDED slug if misrouted
    proposed_parent: str  # one of ACTIVE_EPICS
    confidence: str  # "high" | "medium" | "low" | "uncertain"
    score: int
    scores: dict[str, int]  # full score table per epic
    reasoning: str  # 1-line summary

    @property
    def kind(self) -> str:
        if self.current_parent == "":
            return "ORPHAN"
        return f"MISROUTED ({self.current_parent.split('_SUPERSEDED')[0]})"


# ---------- Helpers ----------


def read_head(path: Path, n_lines: int = SCAN_LINES) -> str:
    """Read first n_lines of a file."""
    try:
        with path.open(encoding="utf-8") as fp:
            return "".join(line for _, line in zip(range(n_lines), fp, strict=False))
    except (UnicodeDecodeError, FileNotFoundError):
        return ""


def extract_parent_epic(text: str) -> str:
    """Return the parent_epic value from the frontmatter, or '' if absent."""
    # Look in frontmatter only (first --- ... --- block)
    if not text.startswith("---"):
        return ""
    end = text.find("---", 4)
    if end == -1:
        return ""
    frontmatter = text[4:end]
    m = re.search(r"^parent_epic\s*:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
    if not m:
        return ""
    val = m.group(1).strip()
    # Strip .md suffix + any path prefix + quotes
    val = val.strip("\"'")
    val = val.split("/")[-1]
    if val.endswith(".md"):
        val = val[:-3]
    return val


def score_epic(text: str, filename: str, keywords: list[str]) -> int:
    """Score an epic against the plan content."""
    score = 0
    fn_lower = filename.lower()
    for kw in keywords:
        kw_lower = kw.lower()
        # Filename match (strongest signal)
        if kw_lower in fn_lower:
            score += 10
        # Body matches (weaker per occurrence; cap to avoid keyword stuffing)
        count = text.lower().count(kw_lower)
        if count > 0:
            score += min(count, 20)  # cap to 20 hits per keyword
    return score


def propose_parent_epic(plan_path: Path) -> Proposal:
    text = read_head(plan_path)
    current = extract_parent_epic(text)
    filename = plan_path.name

    # Score all 19 epics
    scores: dict[str, int] = {}
    for epic_slug, keywords in EPIC_KEYWORDS.items():
        scores[epic_slug] = score_epic(text, filename, keywords)

    # Filename prefix override (strong signal; HIGH confidence)
    prefix_epic = filename_prefix_match(plan_path)
    if prefix_epic is not None:
        return Proposal(
            plan_path=plan_path,
            current_parent=current,
            proposed_parent=prefix_epic,
            confidence="high",
            score=scores.get(prefix_epic, 0),
            scores=scores,
            reasoning=f"filename-prefix override → {prefix_epic} (content score: {scores.get(prefix_epic, 0)})",
        )

    # Sort epics by score descending
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_slug, top_score = ranked[0]
    runner_slug, runner_score = ranked[1]

    # Special-case SUPERSEDED routing
    if current in SUPERSEDED_DEFAULTS:
        default_target = SUPERSEDED_DEFAULTS[current]
        # Use the default unless the content score strongly indicates otherwise
        if scores.get(default_target, 0) >= top_score * 0.5:
            proposed = default_target
            reasoning = f"SUPERSEDED reroute: {current.split('_SUPERSEDED')[0]} → {default_target} (default)"
            confidence = "high"
        else:
            proposed = top_slug
            reasoning = (
                f"SUPERSEDED reroute overridden by content: top_score={top_score},"
                f" default={default_target}({scores.get(default_target, 0)})"
            )
            confidence = "medium"
    elif current == "strategy_and_dart_master_SUPERSEDED_2026_05_21":
        # Strategy vs DART split — pick whichever scored higher
        strat_score = scores.get("strategy_master", 0)
        dart_score = scores.get("dart_and_promote_master", 0)
        if strat_score > dart_score:
            proposed = "strategy_master"
        elif dart_score > strat_score:
            proposed = "dart_and_promote_master"
        else:
            proposed = "strategy_master"  # default to strategy if tied
        reasoning = f"strategy_and_dart split: strategy({strat_score}) vs dart({dart_score}) → {proposed}"
        confidence = "high" if abs(strat_score - dart_score) > 5 else "medium"
    else:
        proposed = top_slug
        # Confidence based on score + gap to runner-up
        if top_score >= 20 and (runner_score == 0 or top_score / max(runner_score, 1) >= 2):
            confidence = "high"
        elif top_score >= 10:
            confidence = "medium"
        elif top_score >= 3:
            confidence = "low"
        else:
            confidence = "uncertain"
        reasoning = f"top: {top_slug}({top_score}) vs runner: {runner_slug}({runner_score})"

    return Proposal(
        plan_path=plan_path,
        current_parent=current,
        proposed_parent=proposed,
        confidence=confidence,
        score=scores[proposed],
        scores=scores,
        reasoning=reasoning,
    )


def should_skip(plan_path: Path, include_index: bool) -> bool:
    fn = plan_path.name
    if include_index:
        return False
    if fn in SKIP_FILENAMES_DEFAULT:
        return True
    return any(plan_path.match(glob) for glob in SKIP_GLOBS_DEFAULT)


def list_candidates(include_index: bool) -> list[Path]:
    """List plan files that need parent_epic patching."""
    candidates: list[Path] = []
    for path in sorted(ACTIVE.glob("*.md")):
        if should_skip(path, include_index):
            continue
        text = read_head(path, 50)  # only need frontmatter for orphan check
        current = extract_parent_epic(text)
        if current == "" or current in SUPERSEDED_SLUGS:
            candidates.append(path)
    return candidates


def patch_parent_epic(plan_path: Path, new_parent: str, apply: bool) -> bool:
    """Add or update parent_epic: in frontmatter. Returns True if changed."""
    try:
        text = plan_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        return False
    if not text.startswith("---"):
        # No frontmatter — would need to add one. Skip + flag.
        return False
    end = text.find("---", 4)
    if end == -1:
        return False
    frontmatter = text[4:end]
    body = text[end:]

    # Check if parent_epic line already exists
    has_existing = bool(re.search(r"^parent_epic\s*:", frontmatter, re.MULTILINE))
    if has_existing:
        # Replace existing value
        new_frontmatter = re.sub(
            r"^parent_epic\s*:\s*.+?$",
            f"parent_epic: {new_parent}",
            frontmatter,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        # Add new line at end of frontmatter (before closing ---)
        new_frontmatter = frontmatter.rstrip() + f"\nparent_epic: {new_parent}\n"

    if new_frontmatter == frontmatter:
        return False

    new_text = "---" + new_frontmatter + body
    if apply:
        plan_path.write_text(new_text, encoding="utf-8")
    return True


# ---------- Main ----------


def main() -> int:
    parser = argparse.ArgumentParser(description="Orphan parent_epic sweep 2026-05-21")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--include-index", action="store_true", help="Don't skip INDEX.md / coordination files")
    parser.add_argument(
        "--min-confidence",
        choices=["uncertain", "low", "medium", "high"],
        default="low",
        help="Only auto-patch proposals at or above this confidence (default: low)",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("ERROR: must pass --dry-run or --apply", file=sys.stderr)
        return 1
    if args.dry_run and args.apply:
        print("ERROR: --dry-run and --apply are mutually exclusive", file=sys.stderr)
        return 1

    apply = args.apply

    candidates = list_candidates(include_index=args.include_index)
    print("=" * 80)
    print("ORPHAN parent_epic SWEEP — 2026-05-21")
    print("=" * 80)
    print(f"\nWorkspace: {WORKSPACE}")
    print(f"Active plan dir: {ACTIVE.relative_to(WORKSPACE)}")
    print(f"Candidates (orphan or misrouted): {len(candidates)}")
    print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
    print(f"Min confidence to patch: {args.min_confidence}")
    print(f"Scan depth: first {SCAN_LINES} lines per plan")
    print(
        f"Skip: {len(SKIP_FILENAMES_DEFAULT)} named + {len(SKIP_GLOBS_DEFAULT)} globs (use --include-index to disable)"
    )
    print()

    proposals: list[Proposal] = []
    for path in candidates:
        proposals.append(propose_parent_epic(path))

    # Confidence ordering
    conf_order = ["high", "medium", "low", "uncertain"]
    conf_min_idx = conf_order.index(args.min_confidence)

    # Group by confidence
    by_conf = {"high": [], "medium": [], "low": [], "uncertain": []}
    for p in proposals:
        by_conf[p.confidence].append(p)

    # Group by proposed epic
    by_epic = Counter(p.proposed_parent for p in proposals)

    print("=== Distribution by proposed parent_epic ===\n")
    for slug, count in by_epic.most_common():
        print(f"  {slug:50s} {count:3d}")
    print()

    print("=== Distribution by confidence ===\n")
    for conf in conf_order:
        print(f"  {conf:12s} {len(by_conf[conf]):3d}")
    print()

    patched = 0
    skipped_low_conf = 0

    for conf in conf_order:
        if not by_conf[conf]:
            continue
        print(f"\n--- {conf.upper()} confidence ({len(by_conf[conf])}) ---\n")
        for p in by_conf[conf]:
            print(f"  [{p.kind:30s}] {p.plan_path.name}")
            print(f"     → {p.proposed_parent}  (score={p.score}, {p.reasoning})")
            # Apply if confidence sufficient
            if conf_order.index(p.confidence) <= conf_min_idx:
                if patch_parent_epic(p.plan_path, p.proposed_parent, apply):
                    patched += 1
                    print(f"     {'APPLIED' if apply else 'WOULD patch'}")
                else:
                    print("     SKIPPED — no frontmatter or no change needed")
            else:
                skipped_low_conf += 1
                print("     SKIPPED — confidence below threshold")

    print("\n" + "=" * 80)
    print(f"SWEEP {'COMPLETE' if apply else 'DRY-RUN COMPLETE'}")
    print("=" * 80)
    print(f"\nTotal candidates: {len(proposals)}")
    print(f"{'Patched' if apply else 'Would patch'}: {patched}")
    print(f"Skipped (confidence < {args.min_confidence}): {skipped_low_conf}")
    print()
    if skipped_low_conf > 0:
        print(f"** {skipped_low_conf} proposals skipped due to low confidence — operator review required **")
        print("To inspect them: rerun with --min-confidence uncertain")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
