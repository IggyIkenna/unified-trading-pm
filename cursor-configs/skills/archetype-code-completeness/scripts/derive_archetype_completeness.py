#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Archetype code-completeness dump -- /plans/epics/system_readiness_master.md § W1.

"Archetype readiness is CODE completeness, not data availability. The
existing `strategy — archetype half` leg [in readiness-state-dump] uses
`satisfying_archetypes()`, which answers 'which archetypes can this venue's
DATA satisfy' — a different question from 'are this archetype's code paths
and hooks complete for batch / paper / live'. Nothing answers the latter."

This script answers the latter, per StrategyArchetype member (60 as of
2026-08-19 -- NOT venue-scoped, unlike readiness-state-dump). See checks.py's
module docstring for the full per-hook policy (what each leg checks, why
absence means what it means, and which legs are DATED AGENT AUDIT notes
rather than clean registry lookups).

REQUIRES running under strategy-service's OWN venv -- every hook this script
checks (ARCHETYPE_ENGINE_REGISTRY, PARAM_SCHEMA_REGISTRY,
ALLOCATOR_ARCHETYPE_REGISTRY, STRATEGY_TYPE_TO_SLOT, the paper_run_handler.py
tick-loader frozensets, topology_enforcement) lives inside strategy-service
itself, so -- unlike readiness-state-dump, which runs under
instruments-service's venv and shells out once for the position-adapter half
-- this script needs no cross-venv subprocess at all:

    cd strategy-service && .venv/bin/python3 \\
        ../unified-trading-pm/cursor-configs/skills/archetype-code-completeness/scripts/derive_archetype_completeness.py

Usage:
    python derive_archetype_completeness.py                       # full dump, summary view
    python derive_archetype_completeness.py --verbose --limit 20
    python derive_archetype_completeness.py --archetype CARRY_STAKED_BASIS --mode LIVE
    python derive_archetype_completeness.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

_HERE = Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parent))

import checks
from strategy_service.cli.handlers import paper_run_handler
from strategy_service.engine.strategies.v2.archetype_slot_resolver import STRATEGY_TYPE_TO_SLOT
from strategy_service.engine.strategies.v2.factory import (
    ARCHETYPE_ENGINE_REGISTRY,
    get_archetype_engine_class,
)
from strategy_service.engine.strategies.v2.param_schema import (
    PARAM_SCHEMA_REGISTRY,
    check_archetype_schema_coverage,
)
from strategy_service.engine.strategies.v2.target_universe.catalog import specs_for_archetype
from strategy_service.portfolio_allocator.archetypes import ALLOCATOR_ARCHETYPE_REGISTRY
from strategy_service.topology_enforcement import load_topology_requirements
from unified_api_contracts.internal import StrategyArchetype

MODES: tuple[str, ...] = ("BATCH", "PAPER", "LIVE")

# The 9 named tick-loader dispatch frozensets in paper_run_handler.py (checks.py's
# paper_dispatch docstring) -- imported live via getattr, never hardcoded, so this
# dump never drifts from the real dispatch clauses as they're added to/renamed.
_PAPER_FROZENSET_NAMES: tuple[str, ...] = (
    "_FUNDING_ARCHETYPES",
    "_RECURSIVE_STAKED_ARCHETYPES",
    "_STAKED_BASIS_DATED_ARCHETYPES",
    "_YIELD_STAKING_SIMPLE_ARCHETYPES",
    "_YIELD_ROTATION_LENDING_ARCHETYPES",
    "_BASIS_DATED_ARCHETYPES",
    "_DEX_DISPERSION_ARCHETYPES",
    "_DEX_LP_ARCHETYPES",
    "_VAULT_ARCHETYPES",
)


def _load_paper_frozensets() -> dict[str, frozenset[StrategyArchetype]]:
    out: dict[str, frozenset[StrategyArchetype]] = {}
    for name in _PAPER_FROZENSET_NAMES:
        value = getattr(paper_run_handler, name, None)
        if isinstance(value, frozenset):
            out[name] = value
    return out


def _allocator_rank_values() -> frozenset[str]:
    return frozenset(a.value for a in ALLOCATOR_ARCHETYPE_REGISTRY)


def _engine_factory_verdict(archetype: StrategyArchetype) -> checks.Verdict:
    in_registry = archetype in ARCHETYPE_ENGINE_REGISTRY
    if not in_registry:
        return checks.engine_factory(archetype.value, in_registry=False, resolves=False, resolve_error=None)
    try:
        get_archetype_engine_class(archetype)
    except (ImportError, AttributeError, KeyError) as exc:
        return checks.engine_factory(archetype.value, in_registry=True, resolves=False, resolve_error=str(exc))
    return checks.engine_factory(archetype.value, in_registry=True, resolves=True, resolve_error=None)


def _param_schema_verdict(archetype: StrategyArchetype, coverage: object) -> checks.Verdict:
    has_schema = archetype.value in PARAM_SCHEMA_REGISTRY
    missing_schema = coverage.missing_schema  # type: ignore[attr-defined]
    new_missing_schema = coverage.new_missing_schema  # type: ignore[attr-defined]
    is_baselined_gap = archetype.value in missing_schema and archetype.value not in new_missing_schema
    return checks.param_schema(archetype.value, has_schema=has_schema, is_baselined_gap=is_baselined_gap)


def _target_universe_verdict(archetype: StrategyArchetype) -> checks.Verdict:
    try:
        specs = specs_for_archetype(archetype)
    except KeyError:
        specs = ()
    return checks.target_universe_catalog(archetype.value, spec_count=len(specs))


def _allocator_rank_verdict(archetype: StrategyArchetype, rank_values: frozenset[str]) -> checks.Verdict:
    candidate = f"{archetype.value}_RANK"
    dedicated = candidate if candidate in rank_values else None
    return checks.allocator_rank(archetype.value, dedicated_rank_member=dedicated)


def _batch_dispatch_verdict(
    archetype: StrategyArchetype, slot_archetypes: frozenset[StrategyArchetype]
) -> checks.Verdict:
    return checks.batch_dispatch(archetype.value, in_slot_resolver=archetype in slot_archetypes)


def _paper_dispatch_verdict(
    archetype: StrategyArchetype, paper_frozensets: dict[str, frozenset[StrategyArchetype]]
) -> checks.Verdict:
    for name, members in paper_frozensets.items():
        if archetype in members:
            return checks.paper_dispatch(archetype.value, in_named_frozenset=True, frozenset_name=name)
    return checks.paper_dispatch(archetype.value, in_named_frozenset=False, frozenset_name=None)


def _live_topology_verdict(archetype: StrategyArchetype) -> checks.Verdict:
    try:
        load_topology_requirements(archetype.value)
    except (FileNotFoundError, ValueError) as exc:
        return checks.live_topology_gate(archetype.value, resolves=False, error=str(exc))
    return checks.live_topology_gate(archetype.value, resolves=True, error=None)


def build_dump(archetypes: list[StrategyArchetype], modes: list[str]) -> tuple[list[dict], dict]:
    coverage = check_archetype_schema_coverage()
    rank_values = _allocator_rank_values()
    slot_archetypes = frozenset(m.archetype for m in STRATEGY_TYPE_TO_SLOT.values())
    paper_frozensets = _load_paper_frozensets()

    rows: list[dict] = []
    leg_state_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    rollup_state_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for archetype in archetypes:
        mode_invariant_legs = {
            "engine_factory": _engine_factory_verdict(archetype),
            "param_schema": _param_schema_verdict(archetype, coverage),
            "target_universe_catalog": _target_universe_verdict(archetype),
            "allocator_rank": _allocator_rank_verdict(archetype, rank_values),
        }

        for mode in modes:
            if mode == "BATCH":
                mode_leg = _batch_dispatch_verdict(archetype, slot_archetypes)
            elif mode == "PAPER":
                mode_leg = _paper_dispatch_verdict(archetype, paper_frozensets)
            else:
                mode_leg = _live_topology_verdict(archetype)

            legs = {**mode_invariant_legs, checks.MODE_SPECIFIC_LEG[mode]: mode_leg}
            if archetype.value in checks.POLICY_EXCLUDED_ARCHETYPES:
                # Every leg of a policy-excluded archetype reports the exclusion.
                # Its missing schema / catalog rows are CONSEQUENCES of the decision
                # not to build it, not independent findings, and listing them as
                # not_ready would inflate the gap count with work nobody will do.
                legs = {
                    name: checks.Verdict("excluded_by_policy", checks.POLICY_EXCLUDED_ARCHETYPES[archetype.value])
                    for name in legs
                }
            overall = checks.rollup(legs)

            for leg_name, verdict in legs.items():
                leg_state_counts[leg_name][verdict.state] += 1
            rollup_state_counts[mode][overall.state] += 1

            rows.append(
                {
                    "archetype": archetype.value,
                    "mode": mode,
                    "legs": {k: asdict(v) for k, v in legs.items()},
                    "overall": asdict(overall),
                }
            )

    all_legs = (*checks.LEG_ORDER_MODE_INVARIANT, *checks.MODE_SPECIFIC_LEG.values())
    summary = {
        "archetype_count": len(archetypes),
        "mode_count": len(modes),
        "row_count": len(rows),
        "leg_state_counts": {leg: dict(leg_state_counts.get(leg, {})) for leg in all_legs},
        "overall_state_counts_by_mode": {mode: dict(rollup_state_counts.get(mode, {})) for mode in modes},
        "param_schema_new_regressions": sorted(coverage.new_missing_schema),  # type: ignore[attr-defined]
    }
    return rows, summary


def _print_human(rows: list[dict], summary: dict, verbose: bool, limit: int) -> None:
    print(
        f"Archetype code-completeness dump -- {summary['archetype_count']} archetypes x {summary['mode_count']} modes"
    )
    print()
    print("=== Per-leg verdict counts (across all archetypes x modes in scope) ===")
    for leg, counts in summary["leg_state_counts"].items():
        ready = counts.get("ready", 0)
        not_ready = counts.get("not_ready", 0)
        excluded = counts.get("excluded_by_policy", 0)
        unverified = counts.get("unverified", 0)
        print(
            f"  {leg:<28} ready={ready:<6} not_ready={not_ready:<6} unverified={unverified:<6} excluded={excluded:<6}"
        )
    print()
    print("=== Overall (rollup) verdict counts, per mode ===")
    for mode, counts in summary["overall_state_counts_by_mode"].items():
        print(
            f"  {mode:<8} ready={counts.get('ready', 0):<6} not_ready={counts.get('not_ready', 0):<6} "
            f"excluded={counts.get('excluded_by_policy', 0):<6} "
            f"unverified={counts.get('unverified', 0):<6}"
        )
    print()
    if summary["param_schema_new_regressions"]:
        regressions = summary["param_schema_new_regressions"]
        print(f"!!! param_schema NEW regressions (not in the baselined gap set): {regressions}")
        print()

    if not verbose:
        print("(pass --verbose for the per-archetype-per-mode table, --limit N to cap rows shown)")
        return

    print(f"=== Per-archetype-per-mode rows (showing up to {limit}) ===")
    for row in rows[:limit]:
        overall = row["overall"]
        print(f"  {row['archetype']} [{row['mode']}] -> {overall['state']}  ({overall['evidence']})")
        for leg_name, v in row["legs"].items():
            print(f"      {leg_name:<28} {v['state']:<12} {v['evidence']}")
    if len(rows) > limit:
        print(f"  ... {len(rows) - limit} more rows omitted (raise --limit or use --json for the full dump)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--archetype", action="append", default=None, help="Filter to one or more archetype values (repeatable)"
    )
    parser.add_argument("--mode", action="append", choices=list(MODES), default=None, help="Filter to a mode")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of the human report")
    parser.add_argument("--verbose", action="store_true", help="Print the full per-archetype-per-mode table")
    parser.add_argument("--limit", type=int, default=60, help="Max rows to print in --verbose mode (default 60)")
    args = parser.parse_args()

    all_archetypes = sorted(StrategyArchetype, key=lambda a: a.value)
    archetype_filter = set(args.archetype) if args.archetype else None
    archetypes = [a for a in all_archetypes if archetype_filter is None or a.value in archetype_filter]
    modes = list(args.mode) if args.mode else list(MODES)

    rows, summary = build_dump(archetypes, modes)

    if args.json:
        json.dump({"summary": summary, "rows": rows}, sys.stdout, indent=2)
        print()
    else:
        _print_human(rows, summary, args.verbose, args.limit)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
