#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Generate the v2-sourced strategy mock fixture files for unified-trading-system-ui.

Reads UAC STRATEGY_REGISTRY (99 slot-label entries derived from
ARCHETYPE_CAPABILITY_REGISTRY) and emits two TypeScript files:

 1. ``lib/mocks/fixtures/strategy-catalog-data.ts`` — the lean catalog view
    (StrategyCatalogEntry) used by the research / family dashboards.
 2. ``lib/mocks/fixtures/strategy-instances.ts`` — the rich StrategyInstance
    view used by the strategy-detail pages + order entry + book widgets.

Usage::

    python unified-trading-pm/scripts/propagation/generate-strategy-instances-fixture.py \\
        --workspace "$UNIFIED_TRADING_WORKSPACE_ROOT"

Writes deterministic output. Re-run after any change to UAC's
``ARCHETYPE_CAPABILITY_REGISTRY`` or representative-slot labels.
"""

# ruff: noqa: E501
# Long lines here are emitted TypeScript string literals (formatted source).
# Breaking them up would require elaborate line-continuation that hurts readability.

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

_ARCHETYPE_TO_FAMILY_V1_NAME: dict[str, str] = {
    "ML_DIRECTIONAL_CONTINUOUS": "ML Directional (Continuous)",
    "ML_DIRECTIONAL_EVENT_SETTLED": "ML Directional (Event Settled)",
    "RULES_DIRECTIONAL_CONTINUOUS": "Rules Directional (Continuous)",
    "RULES_DIRECTIONAL_EVENT_SETTLED": "Rules Directional (Event Settled)",
    "CARRY_BASIS_DATED": "Basis Trade (Dated)",
    "CARRY_BASIS_PERP": "Basis Trade (Perp)",
    "CARRY_STAKED_BASIS": "Staked Basis",
    "CARRY_RECURSIVE_STAKED": "Recursive Staked Basis",
    "YIELD_ROTATION_LENDING": "Lending Rotation",
    "YIELD_STAKING_SIMPLE": "Simple Staking",
    "ARBITRAGE_PRICE_DISPERSION": "Price Dispersion Arbitrage",
    "LIQUIDATION_CAPTURE": "Liquidation Capture",
    "MARKET_MAKING_CONTINUOUS": "Market Making (Continuous)",
    "MARKET_MAKING_EVENT_SETTLED": "Market Making (Event Settled)",
    "EVENT_DRIVEN": "Event Driven",
    "VOL_TRADING_OPTIONS": "Vol Trading (Options)",
    "STAT_ARB_PAIRS_FIXED": "Stat Arb (Pairs Fixed)",
    "STAT_ARB_CROSS_SECTIONAL": "Stat Arb (Cross Sectional)",
}


# Map archetype -> execution mode (HUF / SCE / EVT). Mirrors strategy-service.
_ARCHETYPE_EXEC_MODE: dict[str, str] = {
    "ML_DIRECTIONAL_CONTINUOUS": "SCE",
    "ML_DIRECTIONAL_EVENT_SETTLED": "EVT",
    "RULES_DIRECTIONAL_CONTINUOUS": "HUF",
    "RULES_DIRECTIONAL_EVENT_SETTLED": "EVT",
    "CARRY_BASIS_DATED": "HUF",
    "CARRY_BASIS_PERP": "HUF",
    "CARRY_STAKED_BASIS": "HUF",
    "CARRY_RECURSIVE_STAKED": "EVT",
    "YIELD_ROTATION_LENDING": "HUF",
    "YIELD_STAKING_SIMPLE": "HUF",
    "ARBITRAGE_PRICE_DISPERSION": "EVT",
    "LIQUIDATION_CAPTURE": "EVT",
    "MARKET_MAKING_CONTINUOUS": "EVT",
    "MARKET_MAKING_EVENT_SETTLED": "EVT",
    "EVENT_DRIVEN": "EVT",
    "VOL_TRADING_OPTIONS": "EVT",
    "STAT_ARB_PAIRS_FIXED": "HUF",
    "STAT_ARB_CROSS_SECTIONAL": "HUF",
}


_CATEGORY_TO_asset_group: dict[str, str] = {
    "CEFI": "CeFi",
    "DEFI": "DeFi",
    "TRADFI": "TradFi",
    "SPORTS": "Sports",
    "PREDICTION": "Prediction",
}


_CATEGORY_DEFAULT_CLIENT: dict[str, str] = {
    "CEFI": "quant-fund",
    "DEFI": "defi-desk",
    "TRADFI": "alpha-main",
    "SPORTS": "sports-desk",
    "PREDICTION": "quant-fund",
}


_FAMILY_TIMEFRAME: dict[str, str] = {
    "CARRY_AND_YIELD": "1H",
    "ML_DIRECTIONAL": "5m",
    "RULES_DIRECTIONAL": "15m",
    "ARBITRAGE_STRUCTURAL": "Real-time",
    "MARKET_MAKING": "Real-time",
    "EVENT_DRIVEN": "Event",
    "VOL_TRADING": "Daily",
    "STAT_ARB_PAIRS": "1H",
}


# Seeded deterministic pseudo-random derived only from (slot_label, idx). Used
# to populate the Strategy mock fields with stable per-slot values.
def _hash_int(seed: str) -> int:
    h = 1469598103934665603  # FNV-1a 64-bit offset
    for ch in seed:
        h ^= ord(ch)
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


def _rand_float(seed: str, lo: float, hi: float) -> float:
    h = _hash_int(seed)
    return lo + ((h % 1_000_000) / 1_000_000.0) * (hi - lo)


def _rand_int(seed: str, lo: int, hi: int) -> int:
    return int(_rand_float(seed, float(lo), float(hi)))


@dataclass
class StrategyEntry:
    slot: str
    name: str
    family_v2: str
    asset_group: str
    archetype_v2: str
    coverage_status: str


def _load_registry(workspace: Path) -> list[StrategyEntry]:
    uac = workspace / "unified-api-contracts"
    sys.path.insert(0, str(uac))
    from unified_api_contracts.internal.domain.strategy_service import STRATEGY_REGISTRY

    out: list[StrategyEntry] = []
    for s in STRATEGY_REGISTRY.all():
        out.append(
            StrategyEntry(
                slot=s.strategy_id,
                name=s.name,
                family_v2=s.family.value,
                asset_group=s.asset_group.value,
                archetype_v2=s.archetype.value,
                coverage_status=s.coverage_status.value,
            )
        )
    return out


def _ts_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _parse_slot(slot: str) -> tuple[str, str]:
    """Return (archetype_prefix, body) for ``ARCHETYPE@body``."""
    if "@" in slot:
        a, b = slot.split("@", 1)
        return a, b
    return slot, ""


def _derive_venues(body: str, category: str) -> list[str]:
    parts = body.split("-")
    venue_token = parts[0] if parts else ""
    venue_map = {
        "binance": "BINANCE",
        "bybit": "BYBIT",
        "hyperliquid": "HYPERLIQUID",
        "deribit": "DERIBIT",
        "okx": "OKX",
        "gmx": "GMX",
        "uniswap": "UNISWAP",
        "curve": "CURVE",
        "aave": "AAVE",
        "lido": "LIDO",
        "jito": "JITO",
        "kamino": "KAMINO",
        "drift": "DRIFT",
        "morpho": "MORPHO",
        "compound": "COMPOUND",
        "ice": "ICE",
        "cme": "CME",
        "cboe": "CBOE",
        "ibkr": "IBKR",
        "betfair": "BETFAIR",
        "smarkets": "SMARKETS",
        "polymarket": "POLYMARKET",
        "unity": "UNITY",
        "multi": "MULTI-VENUE",
    }
    venues: list[str] = []
    for tok in parts:
        mapped = venue_map.get(tok)
        if mapped and mapped not in venues:
            venues.append(mapped)
    if not venues:
        venues.append(venue_token.upper() if venue_token else category)
    return venues


def _derive_underlying(body: str) -> str:
    tokens = body.split("-")
    for tok in tokens:
        if tok.lower() in {"btc", "eth", "sol", "weth", "wbtc", "usdc", "usdt"}:
            return tok.upper()
        if len(tok) == 3 and tok.isupper() and tok not in {"USD", "GBP", "EUR"}:
            return tok
    return tokens[1].upper() if len(tokens) > 1 else ""


def _readiness_for(coverage: str) -> tuple[str, str]:
    """(readinessStatus, strategyStatus) per UAC coverage_status."""
    if coverage == "SUPPORTED":
        return ("LIVE", "live")
    if coverage == "PARTIAL":
        return ("PAPER", "paper")
    return ("RESEARCH", "development")


def _generate_catalog(entries: list[StrategyEntry]) -> str:
    lines: list[str] = []
    lines.append("// AUTO-GENERATED by unified-trading-pm/scripts/propagation/generate-strategy-instances-fixture.py.")
    lines.append("// SSOT: unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/registry.py")
    lines.append("// Do NOT edit by hand. 99 entries derived from the v2 ARCHETYPE_CAPABILITY_REGISTRY.")
    lines.append("")
    lines.append('export type StrategyVenueAssetGroup = "DEFI" | "CEFI" | "TRADFI" | "SPORTS" | "PREDICTION";')
    lines.append('export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "VERY_HIGH";')
    lines.append('export type ReadinessStatus = "RESEARCH" | "BACKTEST" | "PAPER" | "STAGING" | "LIVE" | "SUSPENDED";')
    lines.append("")
    # Color maps preserved from the previous fixture
    lines.append("export const ASSET_GROUP_COLORS: Record<StrategyVenueAssetGroup, string> = {")
    lines.append('  DEFI: "bg-purple-500/15 text-purple-400 border-purple-500/30",')
    lines.append('  CEFI: "bg-blue-500/15 text-blue-400 border-blue-500/30",')
    lines.append('  TRADFI: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",')
    lines.append('  SPORTS: "bg-orange-500/15 text-orange-400 border-orange-500/30",')
    lines.append('  PREDICTION: "bg-pink-500/15 text-pink-400 border-pink-500/30",')
    lines.append("};")
    lines.append("")
    lines.append("export const RISK_COLORS: Record<RiskLevel, string> = {")
    lines.append('  LOW: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",')
    lines.append('  MEDIUM: "bg-amber-500/15 text-amber-400 border-amber-500/30",')
    lines.append('  HIGH: "bg-orange-500/15 text-orange-400 border-orange-500/30",')
    lines.append('  VERY_HIGH: "bg-red-500/15 text-red-400 border-red-500/30",')
    lines.append("};")
    lines.append("")
    lines.append("export const STATUS_COLORS: Record<ReadinessStatus, string> = {")
    lines.append('  LIVE: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",')
    lines.append('  STAGING: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",')
    lines.append('  PAPER: "bg-blue-500/15 text-blue-400 border-blue-500/30",')
    lines.append('  BACKTEST: "bg-amber-500/15 text-amber-400 border-amber-500/30",')
    lines.append('  RESEARCH: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",')
    lines.append('  SUSPENDED: "bg-red-500/15 text-red-400 border-red-500/30",')
    lines.append("};")
    lines.append("")
    # Lean interface — v2-canonical family + venue asset group, the rest for dashboard UI
    lines.append("export interface StrategyCatalogEntry {")
    lines.append("  strategy_id: string;")
    lines.append("  name: string;")
    lines.append("  assetGroup: StrategyVenueAssetGroup;")
    lines.append("  family: string; // v2 StrategyFamily value")
    lines.append("  archetype: string; // v2 StrategyArchetype value")
    lines.append("  subcategory: string;")
    lines.append("  description: string;")
    lines.append("  how_it_works: string;")
    lines.append("  performance: {")
    lines.append("    target_apy_range: [number, number];")
    lines.append("    expected_sharpe: number;")
    lines.append("    max_drawdown_pct: number;")
    lines.append("    calmar_ratio: number;")
    lines.append("    win_rate_pct: number;")
    lines.append("    avg_trade_duration: string;")
    lines.append("    backtest_period: string;")
    lines.append("    monthly_returns: number[];")
    lines.append("    benchmark: string;")
    lines.append("  };")
    lines.append("  risk: {")
    lines.append("    risk_level: RiskLevel;")
    lines.append("    max_position_usd: number;")
    lines.append("    max_leverage: number;")
    lines.append("    stop_loss_pct: number | null;")
    lines.append("    circuit_breakers: string[];")
    lines.append("    liquidation_protection: string | null;")
    lines.append("    correlation_to_btc: number;")
    lines.append("    tail_risk: string;")
    lines.append("  };")
    lines.append("  money_ops: {")
    lines.append("    min_deposit_usd: number;")
    lines.append("    recommended_deposit_usd: number;")
    lines.append("    deposit_currency: string[];")
    lines.append("    treasury_wallet: string;")
    lines.append("    trading_wallet: string;")
    lines.append("    auto_rebalance: boolean;")
    lines.append("    rebalance_frequency: string;")
    lines.append("    rebalance_buffer_pct: number;")
    lines.append("    withdrawal_notice: string;")
    lines.append("    fee_structure: string;")
    lines.append("    gas_budget_pct: number;")
    lines.append("  };")
    lines.append("  config: {")
    lines.append("    timeframe: string;")
    lines.append("    venues: string[];")
    lines.append("    chains: string[];")
    lines.append("    instruments: string[];")
    lines.append('    execution_mode: "BATCH" | "LIVE" | "BOTH";')
    lines.append("    deployment_type: string;")
    lines.append("    scaling: string;")
    lines.append("    config_hot_reload: boolean;")
    lines.append("    schema_version: string;")
    lines.append("  };")
    lines.append("  readiness: {")
    lines.append('    code: "C0" | "C1" | "C2" | "C3" | "C4" | "C5";')
    lines.append('    deployment: "D0" | "D1" | "D2" | "D3" | "D4" | "D5" | "none";')
    lines.append('    business: "B0" | "B1" | "B2" | "B3" | "B4" | "B5" | "B6" | "none";')
    lines.append("    status: ReadinessStatus;")
    lines.append("    estimated_launch: string | null;")
    lines.append("    blockers: string[];")
    lines.append("  };")
    lines.append("  security: {")
    lines.append("    custody: string;")
    lines.append("    key_management: string;")
    lines.append("    audit_trail: boolean;")
    lines.append("    disaster_recovery: string;")
    lines.append("    insurance: string | null;")
    lines.append("  };")
    lines.append("  venue_coverage: {")
    lines.append("    primary_venues: string[];")
    lines.append("    backup_venues: string[];")
    lines.append("    data_sources: string[];")
    lines.append("  };")
    lines.append("}")
    lines.append("")
    lines.append("// Backwards-compatible type alias (older consumers)")
    lines.append("export type CatalogStrategy = StrategyCatalogEntry;")
    lines.append("")
    lines.append("export const STRATEGY_CATALOG: StrategyCatalogEntry[] = [")
    for e in entries:
        readiness_status, _ = _readiness_for(e.coverage_status)
        _arch_prefix, body = _parse_slot(e.slot)
        venues = _derive_venues(body, e.asset_group)
        underlying = _derive_underlying(body)
        timeframe = _FAMILY_TIMEFRAME.get(e.family_v2, "1H")
        apy_lo = round(_rand_float(e.slot + "apy_lo", 4.0, 12.0), 1)
        apy_hi = round(apy_lo + _rand_float(e.slot + "apy_sp", 4.0, 16.0), 1)
        sharpe = round(_rand_float(e.slot + "sharpe", 1.2, 2.6), 2)
        max_dd = round(_rand_float(e.slot + "dd", 2.0, 12.0), 1)
        win_rate = round(_rand_float(e.slot + "win", 55.0, 74.0), 0)
        risk_level = (
            "LOW"
            if e.family_v2 == "CARRY_AND_YIELD" or e.family_v2 == "ARBITRAGE_STRUCTURAL"
            else ("MEDIUM" if e.family_v2 != "ML_DIRECTIONAL" else "HIGH")
        )
        deposit = _rand_int(e.slot + "dep", 25000, 200000)
        rec_dep = deposit * _rand_int(e.slot + "recdep", 3, 6)
        max_pos = rec_dep * _rand_int(e.slot + "maxpos", 4, 8)
        code = "C5" if readiness_status == "LIVE" else ("C4" if readiness_status == "PAPER" else "C3")
        dep_gate = "D5" if readiness_status == "LIVE" else ("D3" if readiness_status == "PAPER" else "D1")
        biz_gate = "B5" if readiness_status == "LIVE" else ("B3" if readiness_status == "PAPER" else "B1")
        exec_mode = "LIVE" if readiness_status == "LIVE" else "BOTH"
        desc = (
            f"{_ARCHETYPE_TO_FAMILY_V1_NAME[e.archetype_v2]} strategy on "
            f"{_CATEGORY_TO_asset_group[e.asset_group]} "
            f"venue{'s' if len(venues) > 1 else ''} {', '.join(venues)}."
            + (f" Underlying: {underlying}." if underlying else "")
        )
        how = (
            f"Derived from UAC slot label {e.slot}. "
            f"{'Fully productionised' if readiness_status == 'LIVE' else 'Partially-coverage / research'} "
            f"cell ({e.coverage_status}). "
            f"Family: {e.family_v2}. Archetype: {e.archetype_v2}."
        )
        chain = (
            "ETHEREUM"
            if "ethereum" in body
            else ("ARBITRUM" if "arbitrum" in body else ("SOLANA" if "solana" in body else ""))
        )
        chains = [chain] if chain else []
        subcategory = underlying or e.asset_group
        lines.append("  {")
        lines.append(f'    strategy_id: "{_ts_escape(e.slot)}",')
        lines.append(f'    name: "{_ts_escape(e.name)}",')
        lines.append(f'    assetGroup: "{e.asset_group}",')
        lines.append(f'    family: "{e.family_v2}",')
        lines.append(f'    archetype: "{e.archetype_v2}",')
        lines.append(f'    subcategory: "{_ts_escape(subcategory)}",')
        lines.append(f'    description: "{_ts_escape(desc)}",')
        lines.append(f'    how_it_works: "{_ts_escape(how)}",')
        lines.append("    performance: {")
        lines.append(f"      target_apy_range: [{apy_lo}, {apy_hi}],")
        lines.append(f"      expected_sharpe: {sharpe},")
        lines.append(f"      max_drawdown_pct: {max_dd},")
        lines.append(f"      calmar_ratio: {round((apy_lo + apy_hi) / 2 / max(max_dd, 1.0), 2)},")
        lines.append(f"      win_rate_pct: {int(win_rate)},")
        lines.append('      avg_trade_duration: "4-24 hours",')
        lines.append('      backtest_period: "2024-07-01 to 2026-04-01",')
        lines.append(
            "      monthly_returns: ["
            + ", ".join(str(round(_rand_float(e.slot + f"mret{i}", -3.0, 5.0), 1)) for i in range(12))
            + "],"
        )
        lines.append('      benchmark: "Risk-free rate (SOFR)",')
        lines.append("    },")
        lines.append("    risk: {")
        lines.append(f'      risk_level: "{risk_level}",')
        lines.append(f"      max_position_usd: {max_pos},")
        lines.append(f"      max_leverage: {_rand_float(e.slot + 'lev', 1.0, 5.0):.1f},")
        lines.append(f"      stop_loss_pct: {max_dd + 1.0:.1f},")
        lines.append(
            '      circuit_breakers: ["Max drawdown breach", "Liquidity collapse", "Model calibration drift"],'
        )
        lines.append('      liquidation_protection: "Defensive exit at configured HF threshold",')
        lines.append(f"      correlation_to_btc: {round(_rand_float(e.slot + 'btc', -0.1, 0.6), 2)},")
        lines.append('      tail_risk: "Venue failure, model drift, or correlated factor shock.",')
        lines.append("    },")
        lines.append("    money_ops: {")
        lines.append(f"      min_deposit_usd: {deposit},")
        lines.append(f"      recommended_deposit_usd: {rec_dep},")
        lines.append('      deposit_currency: ["USDC", "USDT"],')
        lines.append('      treasury_wallet: "Copper MPC Custody",')
        lines.append('      trading_wallet: "Venue-managed",')
        lines.append("      auto_rebalance: true,")
        lines.append(f'      rebalance_frequency: "{timeframe}",')
        lines.append(f"      rebalance_buffer_pct: {_rand_int(e.slot + 'rb', 5, 30)},")
        lines.append('      withdrawal_notice: "T+0 to T+3",')
        lines.append('      fee_structure: "2/20 above HWM",')
        lines.append(f"      gas_budget_pct: {round(_rand_float(e.slot + 'gas', 0.1, 1.2), 2)},")
        lines.append("    },")
        lines.append("    config: {")
        lines.append(f'      timeframe: "{timeframe}",')
        lines.append("      venues: [" + ", ".join(f'"{v}"' for v in venues) + "],")
        lines.append("      chains: [" + ", ".join(f'"{c}"' for c in chains) + "],")
        lines.append(f'      instruments: ["{e.slot}"],')
        lines.append(f'      execution_mode: "{exec_mode}",')
        lines.append('      deployment_type: "GCE VM (tarball)",')
        lines.append('      scaling: "Single instance per venue",')
        lines.append("      config_hot_reload: true,")
        lines.append('      schema_version: "5.0.0",')
        lines.append("    },")
        lines.append("    readiness: {")
        lines.append(f'      code: "{code}",')
        lines.append(f'      deployment: "{dep_gate}",')
        lines.append(f'      business: "{biz_gate}",')
        lines.append(f'      status: "{readiness_status}",')
        lines.append(
            "      estimated_launch: null," if readiness_status == "LIVE" else '      estimated_launch: "Q3 2026",'
        )
        lines.append("      blockers: [],")
        lines.append("    },")
        lines.append("    security: {")
        lines.append('      custody: "Copper MPC + self-custody",')
        lines.append('      key_management: "Secret Manager + runtime injection",')
        lines.append("      audit_trail: true,")
        lines.append('      disaster_recovery: "Position state in GCS, auto-resume on restart",')
        lines.append("      insurance: null,")
        lines.append("    },")
        lines.append("    venue_coverage: {")
        lines.append("      primary_venues: [" + ", ".join(f'"{v}"' for v in venues[:2]) + "],")
        backup = venues[2:5] if len(venues) > 2 else []
        lines.append("      backup_venues: [" + ", ".join(f'"{v}"' for v in backup) + "],")
        lines.append('      data_sources: ["MTDS", "UAC capability manifest"],')
        lines.append("    },")
        lines.append("  },")
    lines.append("];")
    lines.append("")
    lines.append("// ---------------------------------------------------------------------------")
    lines.append("// Helper functions (same signatures as the pre-v2 fixture)")
    lines.append("// ---------------------------------------------------------------------------")
    lines.append("")
    lines.append(
        "export function getStrategiesByAssetGroup(assetGroup: StrategyVenueAssetGroup): StrategyCatalogEntry[] {"
    )
    lines.append("  return STRATEGY_CATALOG.filter((s) => s.assetGroup === assetGroup);")
    lines.append("}")
    lines.append("")
    lines.append("export function getStrategiesByFamily(family: string): StrategyCatalogEntry[] {")
    lines.append("  return STRATEGY_CATALOG.filter((s) => s.family === family);")
    lines.append("}")
    lines.append("")
    lines.append("export function getStrategiesByStatus(status: ReadinessStatus): StrategyCatalogEntry[] {")
    lines.append("  return STRATEGY_CATALOG.filter((s) => s.readiness.status === status);")
    lines.append("}")
    lines.append("")
    lines.append("export function getStrategiesByRiskLevel(riskLevel: RiskLevel): StrategyCatalogEntry[] {")
    lines.append("  return STRATEGY_CATALOG.filter((s) => s.risk.risk_level === riskLevel);")
    lines.append("}")
    lines.append("")
    lines.append("export function getStrategyById(strategyId: string): StrategyCatalogEntry | undefined {")
    lines.append("  return STRATEGY_CATALOG.find((s) => s.strategy_id === strategyId);")
    lines.append("}")
    lines.append("")
    lines.append("export function getCatalogSummary(): {")
    lines.append("  total: number;")
    lines.append("  byAssetGroup: Record<string, number>;")
    lines.append("  byStatus: Record<string, number>;")
    lines.append("  byRiskLevel: Record<string, number>;")
    lines.append("  liveCount: number;")
    lines.append("  totalTargetCapital: number;")
    lines.append("} {")
    lines.append("  const byAssetGroup: Record<string, number> = {};")
    lines.append("  const byStatus: Record<string, number> = {};")
    lines.append("  const byRiskLevel: Record<string, number> = {};")
    lines.append("  let liveCount = 0;")
    lines.append("  let totalTargetCapital = 0;")
    lines.append("  for (const s of STRATEGY_CATALOG) {")
    lines.append("    byAssetGroup[s.assetGroup] = (byAssetGroup[s.assetGroup] || 0) + 1;")
    lines.append("    byStatus[s.readiness.status] = (byStatus[s.readiness.status] || 0) + 1;")
    lines.append("    byRiskLevel[s.risk.risk_level] = (byRiskLevel[s.risk.risk_level] || 0) + 1;")
    lines.append('    if (s.readiness.status === "LIVE") liveCount++;')
    lines.append("    totalTargetCapital += s.money_ops.recommended_deposit_usd;")
    lines.append("  }")
    lines.append("  return {")
    lines.append("    total: STRATEGY_CATALOG.length,")
    lines.append("    byAssetGroup,")
    lines.append("    byStatus,")
    lines.append("    byRiskLevel,")
    lines.append("    liveCount,")
    lines.append("    totalTargetCapital,")
    lines.append("  };")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _generate_instances(entries: list[StrategyEntry]) -> str:
    lines: list[str] = []
    lines.append("// AUTO-GENERATED by unified-trading-pm/scripts/propagation/generate-strategy-instances-fixture.py.")
    lines.append("// SSOT: unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/registry.py")
    lines.append("// StrategyInstance is the RICH per-slot mock used by the trading detail pages,")
    lines.append("// the order-entry widget, and the book / terminal data contexts. Slot labels are")
    lines.append("// v2-canonical (ARCHETYPE@venue-asset-instrument-period-quote-env).")
    lines.append("")
    lines.append('import type { AssetClass, StrategyExecutionMode, SystemMode, TestingStage } from "@/lib/taxonomy";')
    lines.append('import { TESTING_STAGES, TESTING_STAGE_CONFIG, SYSTEM_MODE_CONFIG } from "@/lib/taxonomy";')
    lines.append(
        'import type { StrategyArchetype as StrategyArchetypeV2, StrategyFamily } from "@/lib/architecture-v2";'
    )
    lines.append("")
    lines.append("export type { AssetClass, SystemMode };")
    lines.append("export { TESTING_STAGES, TESTING_STAGE_CONFIG, SYSTEM_MODE_CONFIG };")
    lines.append("")
    lines.append("/** Legacy alias — execution-mode-context owns its own mode axis now. Kept for backwards")
    lines.append("    compatibility with the previous strategy-registry export. */")
    lines.append("export type ExecutionMode = SystemMode;")
    lines.append("")
    lines.append("export interface ExecutionModeConfig {")
    lines.append("  mode: ExecutionMode;")
    lines.append('  dataSource: "pubsub" | "gcs";')
    lines.append("  latency: string;")
    lines.append("  description: string;")
    lines.append("}")
    lines.append("")
    lines.append("export const EXECUTION_MODES: Record<ExecutionMode, ExecutionModeConfig> = {")
    lines.append(
        '  live: { mode: "live", dataSource: "pubsub", latency: "Real-time", description: "Live feed via Pub/Sub" },'
    )
    lines.append(
        '  paper: { mode: "paper", dataSource: "pubsub", latency: "Real-time", description: "Live feed, simulated fills" },'
    )
    lines.append(
        '  batch: { mode: "batch", dataSource: "gcs", latency: "Historical", description: "Historical replay from GCS" },'
    )
    lines.append("};")
    lines.append("")
    lines.append("export interface Instrument {")
    lines.append("  key: string;")
    lines.append("  venue: string;")
    lines.append("  type: string;")
    lines.append("  role: string;")
    lines.append("}")
    lines.append("")
    lines.append("export interface RiskProfile {")
    lines.append("  targetReturn: string;")
    lines.append("  targetSharpe: string;")
    lines.append("  maxDrawdown: string;")
    lines.append("  maxLeverage: string;")
    lines.append("  capitalScalability: string;")
    lines.append("}")
    lines.append("")
    lines.append("export interface LatencyProfile {")
    lines.append("  dataToSignal: string;")
    lines.append("  signalToInstruction: string;")
    lines.append("  instructionToFill: string;")
    lines.append("  endToEnd: string;")
    lines.append("  coLocationNeeded: boolean;")
    lines.append("}")
    lines.append("")
    lines.append("export interface PnLComponent {")
    lines.append("  id: string;")
    lines.append("  label: string;")
    lines.append("  settlementType: string;")
    lines.append("  description: string;")
    lines.append("  color: string;")
    lines.append("}")
    lines.append("")
    lines.append("export interface PnLBreakdown {")
    lines.append("  components: PnLComponent[];")
    lines.append("  formula?: string;")
    lines.append("}")
    lines.append("")
    lines.append("export interface FeatureConsumed {")
    lines.append("  name: string;")
    lines.append("  source: string;")
    lines.append("  sla: string;")
    lines.append("  usedFor: string;")
    lines.append("}")
    lines.append("")
    lines.append("export interface RiskSubscription {")
    lines.append("  riskType: string;")
    lines.append("  subscribed: boolean;")
    lines.append("  threshold?: string;")
    lines.append("  action?: string;")
    lines.append("}")
    lines.append("")
    lines.append("export interface TestingStageStatus {")
    lines.append("  stage: TestingStage;")
    lines.append('  status: "done" | "pending" | "blocked" | "in_progress";')
    lines.append("  notes?: string;")
    lines.append("}")
    lines.append("")
    lines.append("export interface StrategyConfig {")
    lines.append("  key: string;")
    lines.append("  value: string;")
    lines.append("  description: string;")
    lines.append("}")
    lines.append("")
    lines.append("/** Rich per-slot mock strategy shape. v2-canonical: `archetype` + `family` are the v2 enum values;")
    lines.append(
        " *  `id` = slot label; `strategyIdPattern` is retained as an alias for backwards compat (equals `id`). */"
    )
    lines.append("export interface StrategyInstance {")
    lines.append("  id: string;")
    lines.append("  name: string;")
    lines.append("  description: string;")
    lines.append("  strategyIdPattern: string;")
    lines.append("  clientId: string;")
    lines.append("  assetClass: AssetClass;")
    lines.append("  strategyType: string;")
    lines.append("  family: StrategyFamily;")
    lines.append("  archetype: StrategyArchetypeV2;")
    lines.append("  executionMode: StrategyExecutionMode;")
    lines.append('  status: "live" | "paused" | "warning" | "development" | "staging" | "paper";')
    lines.append("  version: string;")
    lines.append("  deployedAt?: string;")
    lines.append("  instruments: Instrument[];")
    lines.append("  featuresConsumed: FeatureConsumed[];")
    lines.append("  dataArchitecture: {")
    lines.append("    rawDataSource: string;")
    lines.append("    processedData: string[];")
    lines.append("    interval: string;")
    lines.append("    lowestGranularity: string;")
    lines.append("    executionMode: string;")
    lines.append("  };")
    lines.append("  sorEnabled: boolean;")
    lines.append("  sorConfig?: {")
    lines.append("    legs: { name: string; sorEnabled: boolean; allowedVenues?: string[] }[];")
    lines.append("  };")
    lines.append("  pnlAttribution: PnLBreakdown;")
    lines.append("  riskProfile: RiskProfile;")
    lines.append("  latencyProfile: LatencyProfile;")
    lines.append("  riskSubscriptions: RiskSubscription[];")
    lines.append("  testingStatus: TestingStageStatus[];")
    lines.append("  configParams: StrategyConfig[];")
    lines.append("  crossAssetLink?: { from: string; to: string; instruments: string[] };")
    lines.append("  venues: string[];")
    lines.append("  performance: {")
    lines.append("    pnlTotal: number;")
    lines.append("    pnlMTD: number;")
    lines.append("    sharpe: number;")
    lines.append("    maxDrawdown: number;")
    lines.append("    returnPct: number;")
    lines.append("    positions: number;")
    lines.append("    netExposure: number;")
    lines.append("  };")
    lines.append("  sparklineData: number[];")
    lines.append("  references?: {")
    lines.append("    implementation?: string;")
    lines.append("    configSchema?: string;")
    lines.append("    executionAdapter?: string;")
    lines.append("  };")
    lines.append("  instructionTypes: string[];")
    lines.append("  kellySizing?: {")
    lines.append("    fraction: number;")
    lines.append("    maxStakePct: number;")
    lines.append("    edgeThreshold: number;")
    lines.append("    bankrollDrawdownLimit: number;")
    lines.append("  };")
    lines.append("}")
    lines.append("")
    lines.append("/** Back-compat alias. */")
    lines.append("export type Strategy = StrategyInstance;")
    lines.append("")
    lines.append("export const STRATEGY_INSTANCES: StrategyInstance[] = [")
    for e in entries:
        readiness_status, status = _readiness_for(e.coverage_status)
        _arch_prefix, body = _parse_slot(e.slot)
        venues = _derive_venues(body, e.asset_group)
        underlying = _derive_underlying(body)
        exec_mode = _ARCHETYPE_EXEC_MODE[e.archetype_v2]
        asset_group = _CATEGORY_TO_asset_group[e.asset_group]
        client = _CATEGORY_DEFAULT_CLIENT[e.asset_group]
        net_exposure = _rand_int(e.slot + "netexp", 500_000, 15_000_000)
        sharpe = round(_rand_float(e.slot + "sharpe", 1.2, 2.6), 2)
        max_dd = round(_rand_float(e.slot + "dd", 2.0, 12.0), 1)
        ret_pct = round(_rand_float(e.slot + "ret", -5.0, 18.0), 1)
        pnl_total = int(net_exposure * (ret_pct / 100.0))
        pnl_mtd = int(pnl_total * _rand_float(e.slot + "mtd_pct", 0.05, 0.3))
        positions = _rand_int(e.slot + "pos", 1, 6)
        spark = [int(_rand_float(e.slot + f"sp{i}", 8.0, 28.0)) for i in range(12)]
        strategy_type = _ARCHETYPE_TO_FAMILY_V1_NAME[e.archetype_v2]
        lines.append("  {")
        lines.append(f'    id: "{_ts_escape(e.slot)}",')
        lines.append(f'    name: "{_ts_escape(e.name)}",')
        lines.append(
            f'    description: "Auto-generated mock for UAC slot {_ts_escape(e.slot)} ({e.coverage_status}).",'
        )
        lines.append(f'    strategyIdPattern: "{_ts_escape(e.slot)}",')
        lines.append(f'    clientId: "{client}",')
        lines.append(f'    assetClass: "{asset_group}",')
        lines.append(f'    strategyType: "{_ts_escape(strategy_type)}",')
        lines.append(f'    family: "{e.family_v2}",')
        lines.append(f'    archetype: "{e.archetype_v2}",')
        lines.append(f'    executionMode: "{exec_mode}",')
        lines.append(f'    status: "{status}",')
        lines.append(
            f'    version: "{_rand_int(e.slot + "ver", 1, 3)}.{_rand_int(e.slot + "min", 0, 9)}.{_rand_int(e.slot + "pat", 0, 9)}",'
        )
        lines.append('    deployedAt: "2026-03-15 09:00:00",')
        primary_venue = venues[0] if venues else "UNKNOWN"
        lines.append("    instruments: [")
        lines.append(
            f'      {{ key: "{primary_venue}:SPOT:{underlying or "ASSET"}", venue: "{primary_venue}", type: "SPOT_ASSET", role: "Primary leg" }},'
        )
        if len(venues) > 1:
            lines.append(
                f'      {{ key: "{venues[1]}:HEDGE:{underlying or "ASSET"}", venue: "{venues[1]}", type: "Perp", role: "Hedge leg" }},'
            )
        lines.append("    ],")
        lines.append("    featuresConsumed: [")
        lines.append('      { name: "price", source: "market-tick-data", sla: "1s", usedFor: "Signal generation" },')
        lines.append("    ],")
        lines.append("    dataArchitecture: {")
        lines.append('      rawDataSource: "CloudDataProvider (live) / CSVDataProvider (backtest)",')
        lines.append('      processedData: ["price"],')
        lines.append(f'      interval: "{_FAMILY_TIMEFRAME.get(e.family_v2, "1H")}",')
        lines.append(f'      lowestGranularity: "{_FAMILY_TIMEFRAME.get(e.family_v2, "1H")}",')
        lines.append(
            f'      executionMode: "{("same_candle_exit" if exec_mode == "SCE" else ("hold_until_flip" if exec_mode == "HUF" else "event_driven"))}",'
        )
        lines.append("    },")
        lines.append("    sorEnabled: true,")
        lines.append("    pnlAttribution: {")
        lines.append("      components: [")
        lines.append(
            '        { id: "trading_pnl", label: "Trading P&L", settlementType: "REALIZED", description: "Entry/exit fills", color: "#a78bfa" },'
        )
        lines.append(
            '        { id: "mark_to_market", label: "Mark-to-Market", settlementType: "MARK_TO_MARKET", description: "Open position valuation", color: "#60a5fa" },'
        )
        lines.append(
            '        { id: "transaction_costs", label: "Transaction Costs", settlementType: "PER_FILL", description: "Fees, slippage, gas", color: "#ef4444" },'
        )
        lines.append("      ],")
        lines.append('      formula: "total_pnl = equity_current - equity_initial",')
        lines.append("    },")
        lines.append("    riskProfile: {")
        lo = round(_rand_float(e.slot + "rlo", 4.0, 10.0), 1)
        hi = round(lo + _rand_float(e.slot + "rhi", 3.0, 10.0), 1)
        lines.append(f'      targetReturn: "{lo}-{hi}%",')
        lines.append(f'      targetSharpe: "{sharpe}+",')
        lines.append(f'      maxDrawdown: "{max_dd}%",')
        lev = round(_rand_float(e.slot + "lev", 1.0, 5.0), 1)
        lines.append(f'      maxLeverage: "{lev}x",')
        lines.append(f'      capitalScalability: "${_rand_int(e.slot + "cs", 1, 50)}M",')
        lines.append("    },")
        lines.append("    latencyProfile: {")
        lines.append('      dataToSignal: "50ms p50 / 200ms p99",')
        lines.append('      signalToInstruction: "5ms p50 / 20ms p99",')
        lines.append('      instructionToFill: "2s p50 / 15s p99",')
        lines.append('      endToEnd: "~3s p50 / ~16s p99",')
        lines.append("      coLocationNeeded: false,")
        lines.append("    },")
        lines.append("    riskSubscriptions: [")
        lines.append('      { riskType: "delta", subscribed: true, threshold: "2% drift", action: "Rebalance" },')
        lines.append("    ],")
        lines.append(
            "    testingStatus: ["
            + ", ".join(
                f'{{ stage: "{stg}", status: "{("done" if readiness_status == "LIVE" else ("pending" if readiness_status != "RESEARCH" else "blocked"))}" }}'
                for stg in (
                    "MOCK",
                    "HISTORICAL",
                    "LIVE_MOCK",
                    "LIVE_TESTNET",
                    "STAGING",
                    "LIVE_REAL",
                )
            )
            + "],"
        )
        lines.append("    configParams: [")
        lines.append('      { key: "initial_capital", value: "1000000", description: "Starting capital" },')
        lines.append("    ],")
        lines.append("    venues: [" + ", ".join(f'"{v}"' for v in venues) + "],")
        lines.append("    performance: {")
        lines.append(f"      pnlTotal: {pnl_total},")
        lines.append(f"      pnlMTD: {pnl_mtd},")
        lines.append(f"      sharpe: {sharpe},")
        lines.append(f"      maxDrawdown: {max_dd},")
        lines.append(f"      returnPct: {ret_pct},")
        lines.append(f"      positions: {positions},")
        lines.append(f"      netExposure: {net_exposure},")
        lines.append("    },")
        lines.append("    sparklineData: [" + ", ".join(str(x) for x in spark) + "],")
        lines.append("    references: {")
        lines.append(f'      implementation: "strategy-service/engine/strategies/{e.archetype_v2.lower()}.py",')
        lines.append(
            '      configSchema: "unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json",'
        )
        lines.append('      executionAdapter: "execution-service/connectors/*",')
        lines.append("    },")
        lines.append('    instructionTypes: ["TRADE", "SWAP"],')
        lines.append("  },")
    lines.append("];")
    lines.append("")
    lines.append("/** Legacy alias — same list as STRATEGY_INSTANCES. */")
    lines.append("export const STRATEGIES: StrategyInstance[] = STRATEGY_INSTANCES;")
    lines.append("")
    lines.append("// ---------------------------------------------------------------------------")
    lines.append("// Helper functions (identical signatures to the pre-v2 registry)")
    lines.append("// ---------------------------------------------------------------------------")
    lines.append("")
    lines.append("export function getStrategyById(id: string): StrategyInstance | undefined {")
    lines.append("  return STRATEGY_INSTANCES.find((s) => s.id === id);")
    lines.append("}")
    lines.append("")
    lines.append(
        'export function getStrategiesByAssetClass(assetClass: StrategyInstance["assetClass"]): StrategyInstance[] {'
    )
    lines.append("  return STRATEGY_INSTANCES.filter((s) => s.assetClass === assetClass);")
    lines.append("}")
    lines.append("")
    lines.append("export function getStrategiesByArchetype(archetype: StrategyArchetypeV2): StrategyInstance[] {")
    lines.append("  return STRATEGY_INSTANCES.filter((s) => s.archetype === archetype);")
    lines.append("}")
    lines.append("")
    lines.append('export function getStrategiesByStatus(status: StrategyInstance["status"]): StrategyInstance[] {')
    lines.append("  return STRATEGY_INSTANCES.filter((s) => s.status === status);")
    lines.append("}")
    lines.append("")
    lines.append("export function getStrategiesByVenue(venue: string): StrategyInstance[] {")
    lines.append("  return STRATEGY_INSTANCES.filter((s) => s.venues.includes(venue));")
    lines.append("}")
    lines.append("")
    lines.append("export function getStrategiesByClientId(clientId: string): StrategyInstance[] {")
    lines.append("  return STRATEGY_INSTANCES.filter((s) => s.clientId === clientId);")
    lines.append("}")
    lines.append("")
    lines.append(
        'export function getStrategiesByExecutionMode(mode: StrategyInstance["executionMode"]): StrategyInstance[] {'
    )
    lines.append("  return STRATEGY_INSTANCES.filter((s) => s.executionMode === mode);")
    lines.append("}")
    lines.append("")
    lines.append("export function getTotalAUM(strategies: StrategyInstance[] = STRATEGY_INSTANCES): number {")
    lines.append("  return strategies.reduce((sum, s) => sum + Math.abs(s.performance.netExposure), 0);")
    lines.append("}")
    lines.append("")
    lines.append("export function getTotalPnL(strategies: StrategyInstance[] = STRATEGY_INSTANCES): number {")
    lines.append("  return strategies.reduce((sum, s) => sum + s.performance.pnlTotal, 0);")
    lines.append("}")
    lines.append("")
    lines.append("export function getTotalMTDPnL(strategies: StrategyInstance[] = STRATEGY_INSTANCES): number {")
    lines.append("  return strategies.reduce((sum, s) => sum + s.performance.pnlMTD, 0);")
    lines.append("}")
    lines.append("")
    lines.append("// ---------------------------------------------------------------------------")
    lines.append("// Derived mock Position / PnLBreakdownData helpers (used by detail pages)")
    lines.append("// ---------------------------------------------------------------------------")
    lines.append("")
    lines.append("export interface Position {")
    lines.append("  id: string;")
    lines.append("  strategyId: string;")
    lines.append("  strategyName: string;")
    lines.append("  client: string;")
    lines.append("  underlying: string;")
    lines.append("  venue: string;")
    lines.append("  instrument: string;")
    lines.append('  side: "LONG" | "SHORT";')
    lines.append("  size: number;")
    lines.append("  entryPrice: number;")
    lines.append("  currentPrice: number;")
    lines.append("  notional: number;")
    lines.append("  unrealizedPnL: number;")
    lines.append("  unrealizedPnLPct: number;")
    lines.append("  margin: number;")
    lines.append("  leverage: number;")
    lines.append("  liquidationPrice?: number;")
    lines.append("  healthFactor?: number;")
    lines.append("  ltv?: number;")
    lines.append("  lastUpdated: string;")
    lines.append("}")
    lines.append("")
    lines.append("export function generatePositionsForStrategy(strategy: StrategyInstance): Position[] {")
    lines.append("  const positions: Position[] = [];")
    lines.append("  strategy.instruments.forEach((inst, idx) => {")
    lines.append(
        '    const isShort = inst.role.toLowerCase().includes("short") || inst.role.toLowerCase().includes("hedge");'
    )
    lines.append(
        "    const baseSize = strategy.performance.netExposure / (strategy.instruments.length * (isShort ? -1 : 1));"
    )
    lines.append("    const entryPrice = 100;")
    lines.append("    const currentPrice = 101;")
    lines.append("    const size = Math.abs(baseSize / entryPrice);")
    lines.append("    const notional = size * currentPrice;")
    lines.append(
        "    const unrealizedPnL = isShort ? (entryPrice - currentPrice) * size : (currentPrice - entryPrice) * size;"
    )
    lines.append("    positions.push({")
    lines.append("      id: `pos-${strategy.id}-${idx}`,")
    lines.append("      strategyId: strategy.id,")
    lines.append("      strategyName: strategy.name,")
    lines.append('      client: "Internal",')
    lines.append('      underlying: inst.key.split(":").pop() ?? "",')
    lines.append("      venue: inst.venue,")
    lines.append("      instrument: inst.key,")
    lines.append('      side: isShort ? "SHORT" : "LONG",')
    lines.append("      size: Math.round(size * 1000) / 1000,")
    lines.append("      entryPrice,")
    lines.append("      currentPrice,")
    lines.append("      notional: Math.abs(notional),")
    lines.append("      unrealizedPnL: Math.round(unrealizedPnL),")
    lines.append("      unrealizedPnLPct: Math.round((unrealizedPnL / Math.abs(baseSize)) * 10000) / 100,")
    lines.append('      margin: Math.abs(notional) * (inst.type === "Perp" ? 0.1 : 1),')
    lines.append('      leverage: inst.type === "Perp" ? 10 : 1,')
    lines.append("      liquidationPrice: isShort ? Math.round(entryPrice * 1.15) : Math.round(entryPrice * 0.85),")
    lines.append('      lastUpdated: "1s ago",')
    lines.append("    });")
    lines.append("  });")
    lines.append("  return positions;")
    lines.append("}")
    lines.append("")
    lines.append(
        "export function getAllPositions(): Position[] { return STRATEGY_INSTANCES.flatMap(generatePositionsForStrategy); }"
    )
    lines.append("")
    lines.append("export interface PnLBreakdownData {")
    lines.append("  strategyId: string;")
    lines.append("  components: {")
    lines.append("    componentId: string;")
    lines.append("    label: string;")
    lines.append("    value: number;")
    lines.append("    pct: number;")
    lines.append("    color: string;")
    lines.append('    settlementCategory: "REALIZED" | "UNREALIZED" | "RESIDUAL";')
    lines.append("  }[];")
    lines.append("  total: number;")
    lines.append("  realized: number;")
    lines.append("  unrealized: number;")
    lines.append("  residual: number;")
    lines.append("}")
    lines.append("")
    lines.append('function getSettlementCategory(settlementType: string): "REALIZED" | "UNREALIZED" | "RESIDUAL" {')
    lines.append(
        '  if (["PER_FILL", "PER_TRADE", "FUNDING_8H", "REALIZED"].some((t) => settlementType.includes(t))) return "REALIZED";'
    )
    lines.append('  if (settlementType.includes("MARK_TO_MARKET")) return "UNREALIZED";')
    lines.append('  return "RESIDUAL";')
    lines.append("}")
    lines.append("")
    lines.append("export function generatePnLBreakdown(strategy: StrategyInstance): PnLBreakdownData {")
    lines.append("  const total = strategy.performance.pnlMTD;")
    lines.append("  const components = strategy.pnlAttribution.components.map((comp, i) => {")
    lines.append('    const pct = comp.id.includes("cost") ? -10 - i * 3 : 40 - i * 15;')
    lines.append("    return {")
    lines.append("      componentId: comp.id,")
    lines.append("      label: comp.label,")
    lines.append("      value: Math.round(total * (pct / 100)),")
    lines.append("      pct,")
    lines.append("      color: comp.color,")
    lines.append("      settlementCategory: getSettlementCategory(comp.settlementType),")
    lines.append("    };")
    lines.append("  });")
    lines.append(
        '  const realized = components.filter((c) => c.settlementCategory === "REALIZED").reduce((sum, c) => sum + c.value, 0);'
    )
    lines.append(
        '  const unrealized = components.filter((c) => c.settlementCategory === "UNREALIZED").reduce((sum, c) => sum + c.value, 0);'
    )
    lines.append("  const residual = total - components.reduce((sum, c) => sum + c.value, 0);")
    lines.append("  return { strategyId: strategy.id, components, total, realized, unrealized, residual };")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args()
    workspace: Path = args.workspace.resolve()
    entries = _load_registry(workspace)
    if len(entries) != 99:
        print(
            f"WARN: expected 99 STRATEGY_REGISTRY entries, got {len(entries)}",
            file=sys.stderr,
        )
    ui = workspace / "unified-trading-system-ui"
    catalog_path = ui / "lib/mocks/fixtures/strategy-catalog-data.ts"
    instances_path = ui / "lib/mocks/fixtures/strategy-instances.ts"
    catalog_path.write_text(_generate_catalog(entries))
    instances_path.write_text(_generate_instances(entries))
    print(f"Wrote {catalog_path} ({len(entries)} entries)")
    print(f"Wrote {instances_path} ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
