#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Readiness state dump -- Tuesday deliverable 1
(/plans/active/data_pipeline_completion_2026_08_21.md § "Tuesday dumps",
/plans/epics/system_readiness_master.md § W1).

Derives, per (venue x mode), a readiness verdict across instruments-service
-> MTDS -> MDPS -> features -> strategy -> execution. Readiness is DERIVED,
never declared (operator ruling 2026-08-16): a leg with no real machine
check prints "unverified", never a silent pass. See checks.py's module
docstring for the exact proxy-vs-fact policy this dump follows.

Strategy leg, stated precisely (per the task): a position adapter must exist
for this venue in this mode, AND at least one archetype must be registered
for this venue in this mode -- both, not either (checks.strategy_leg).

The six-surface table (system_readiness_master.md W1, 2026-08-19 ruling):
market data (MTDS) / position (strategy-service) / orders, fills, trades,
account balance (execution-service). Market data is answered by TWO checks,
not three: BATCH (coverage.json-observed) and LIVE (MTDS's own
WS_FEED_CONNECTOR_FACTORIES registry) -- PAPER reuses the LIVE verdict,
since paper always consumes the live market-data feed
(/codex/09-strategy/operational/paper-batch-live-reconciliation.md § 0), never
a separate paper feed. Orders/fills/trades/account_balance are answered by
execution-service's own order-adapter registry (see
_execution_order_capability_probe.py).

Shares its shard enumeration with the honest-coverage-dump skill --
../../honest-coverage-dump/scripts/shard_universe.py is the single source for
reading coverage.json and picking the current grain. This dump does not
re-read GCS objects or re-derive the expected universe itself.

REQUIRES a Python with both unified_api_contracts AND unified_trading_library
importable (the latter via shard_universe.py's GCS read -- cloud_interface
only, never a subprocess gcloud/gsutil call, see that module's docstring).
unified-api-contracts is T0 and does not depend on unified-trading-library,
so this does NOT run under UAC's own venv -- run it under
instruments-service's venv instead, which carries both (it owns
measure_honest_coverage.py, the script that writes the coverage.json this
dump reads):

    cd instruments-service && .venv/bin/python3 \\
        ../unified-trading-pm/cursor-configs/skills/readiness-state-dump/scripts/derive_readiness.py

The strategy position-adapter leg additionally shells out to
strategy-service/.venv (a separate subprocess, never an import -- see
_strategy_position_probe.py) because that registry lives in strategy-service,
not UAC. The execution-service order/fills/trades/balance legs shell out to
execution-service/.venv (_execution_order_capability_probe.py) for the same
reason, and the market_tick_data LIVE leg shells out to
market-tick-data-service/.venv (_mtds_live_feed_probe.py). If a venv is
absent, the corresponding leg(s) report "unverified" honestly rather than
being skipped silently.

Usage:
    python derive_readiness.py                              # full dump, summary view
    python derive_readiness.py --verbose --limit 20
    python derive_readiness.py --venue OKX-FUTURES --mode LIVE
    python derive_readiness.py --asset-group cefi --json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

_HERE = Path(__file__).resolve()
_SKILLS_DIR = _HERE.parents[2]  # .../cursor-configs/skills
_WORKSPACE_ROOT_DEFAULT = _HERE.parents[5]  # the multi-repo checkout root (siblings: uac, strategy-service, ...)

sys.path.insert(0, str(_SKILLS_DIR / "honest-coverage-dump" / "scripts"))

import checks
import instruction_actions
from shard_universe import (
    DEFAULT_PROJECT_ID,
    CoverageReadError,
    detect_grain,
    iter_shard_cells,
    load_coverage,
    venue_asset_group_map,
)
from unified_api_contracts.internal.architecture_v2.venue_strategy_consumability import (
    contract_step_17_check,
)
from unified_api_contracts.internal.domain.execution_service.transfer_types import (
    VENUE_WALLET_CAPABILITIES,
)
from unified_api_contracts.registry.market_data_categories import (
    VENUE_DATA_TYPE_CAPABILITIES,
    VENUES_BY_ASSET_GROUP,
)
from unified_api_contracts.registry.processed_data_dependencies import MDPS_DERIVABLE_DATA_TYPES

# MANUAL added 2026-08-20 (W1 addition, code_readiness_t5_...) -- first-class alongside automated per
# unified_api_contracts.internal.modes.OperationalMode { LIVE, MANUAL, BACKTEST, PAPER } (codex/04-architecture/
# operational-modes.md's SSOT): "Real trades + real endpoints; only the trigger differs (operator-driven)" --
# MANUAL shares LIVE's mainnet endpoint config, so every existing check's mode->env mapping (mode == "PAPER" ->
# testnet, else mainnet) already resolves MANUAL correctly without a per-check special case. No probe currently
# distinguishes manual-vs-automated triggering, so MANUAL rows report `unverified` honestly wherever a check
# does not exist -- exactly this dump's own standing discipline, not a new pattern.
MODES: tuple[str, ...] = ("BATCH", "PAPER", "LIVE", "MANUAL")


def _uac_venue_asset_group_map() -> dict[str, str]:
    out: dict[str, str] = {}
    for ag, venues in VENUES_BY_ASSET_GROUP.items():
        for v in venues:
            out.setdefault(v, ag)
    return out


def _venue_data_types(venue: str) -> frozenset[str]:
    record = VENUE_DATA_TYPE_CAPABILITIES.get(venue)
    if record is None:
        return frozenset()
    return frozenset(record.data_types.keys())


def _query_strategy_position_availability(
    venues: list[str], workspace_root: Path, skip: bool
) -> tuple[dict[str, dict[str, str]], str]:
    """Returns ({venue: {"batch":..,"live":..,"paper":..}}, note)."""
    if skip:
        return {}, "skipped via --skip-strategy-probe"
    strategy_python = workspace_root / "strategy-service" / ".venv" / "bin" / "python3"
    if not strategy_python.exists():
        return {}, f"{strategy_python} not found -- strategy-service venv unavailable in this environment"
    probe_script = _HERE.parent / "_strategy_position_probe.py"
    proc = subprocess.run(
        [str(strategy_python), str(probe_script)],
        input=json.dumps(venues),
        capture_output=True,
        text=True,
        check=False,
        cwd=str(workspace_root / "strategy-service"),
    )
    if proc.returncode != 0:
        return {}, f"strategy-service probe subprocess failed (exit {proc.returncode}): {proc.stderr.strip()[:300]}"
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {}, f"strategy-service probe returned non-JSON output: {exc}"
    return result, f"queried {len(result)} venues via strategy-service/.venv"


def _query_execution_order_capability(
    venues: list[str], workspace_root: Path, skip: bool
) -> tuple[dict[str, dict], str]:
    """Returns ({venue: {"adapter_present":.., "place_order": {"mainnet":.., "testnet":..}}}, note)."""
    if skip:
        return {}, "skipped via --skip-execution-probe"
    execution_python = workspace_root / "execution-service" / ".venv" / "bin" / "python3"
    if not execution_python.exists():
        return {}, f"{execution_python} not found -- execution-service venv unavailable in this environment"
    probe_script = _HERE.parent / "_execution_order_capability_probe.py"
    proc = subprocess.run(
        [str(execution_python), str(probe_script)],
        input=json.dumps(venues),
        capture_output=True,
        text=True,
        check=False,
        cwd=str(workspace_root / "execution-service"),
    )
    if proc.returncode != 0:
        return {}, f"execution-service probe subprocess failed (exit {proc.returncode}): {proc.stderr.strip()[:300]}"
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {}, f"execution-service probe returned non-JSON output: {exc}"
    return result, f"queried {len(result)} venues via execution-service/.venv"


def _query_execution_instruction_path(
    venues: list[str], workspace_root: Path, skip: bool
) -> tuple[dict[str, dict], str]:
    """Returns ({venue: asdict(InstructionPathAvailability)}, note) -- the real
    per-venue-per-mode execution_instruction leg (execution_service.readiness.
    instruction_path, wired 2026-08-20; see checks.py's execution_instruction
    module comment for why this replaces the old venue-independent check)."""
    if skip:
        return {}, "skipped via --skip-instruction-path-probe"
    execution_python = workspace_root / "execution-service" / ".venv" / "bin" / "python3"
    if not execution_python.exists():
        return {}, f"{execution_python} not found -- execution-service venv unavailable in this environment"
    probe_script = _HERE.parent / "_execution_instruction_path_probe.py"
    proc = subprocess.run(
        [str(execution_python), str(probe_script)],
        input=json.dumps(venues),
        capture_output=True,
        text=True,
        check=False,
        cwd=str(workspace_root / "execution-service"),
    )
    if proc.returncode != 0:
        return {}, f"instruction-path probe subprocess failed (exit {proc.returncode}): {proc.stderr.strip()[:300]}"
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {}, f"instruction-path probe returned non-JSON output: {exc}"
    return result, f"queried {len(result)} venues via execution-service/.venv"


def _capability_facts_by_venue(venues: list[str]) -> tuple[dict[str, dict], str]:
    """Flatten UAC SourceCapability auth facts per venue, for the `credentials` leg.

    Venue -> capability-source resolution is a genuine ambiguity: capability keys are
    source-style ("hyperliquid"), venues are canonical dash-form ("OKX-FUTURES").
    execution-service owns the authoritative `_resolve_venue_str`, but importing a T4
    service here would violate the tier rule, so this tries an ordered list of candidate
    keys and reports NOTHING (leg -> unverified) when none resolve. It never guesses a
    match, and an unresolved venue is reported as undeclared, never as "no credential
    needed" -- that distinction is the whole point of the leg.
    """
    from unified_api_contracts.registry.capability import CapabilityResolutionError, resolve_capability
    from unified_api_contracts.registry.capability_data import bootstrap_capabilities

    bootstrap_capabilities()

    out: dict[str, dict] = {}
    unresolved = 0
    for venue in venues:
        cap = None
        for candidate in (venue.lower(), venue.split("-")[0].lower(), venue.replace("-", "_").lower()):
            try:
                cap = resolve_capability(candidate)
                break
            except CapabilityResolutionError:
                continue
        if cap is None:
            unresolved += 1
            continue
        required: set[str] = set()
        for detail in (cap.operation_details or {}).values():
            for env_detail in (detail.environments or {}).values():
                if env_detail.required_credential:
                    required.add(env_detail.required_credential)
        out[venue] = {
            "auth_scope": list(cap.auth_scope or []),
            "auth_environments": dict(cap.auth_environments or {}),
            "supports_testnet": bool(cap.supports_testnet),
            "supports_mainnet": bool(cap.supports_mainnet),
            "required_credentials": sorted(required),
        }
    note = f"resolved UAC capability for {len(out)}/{len(venues)} venues ({unresolved} unresolved -> unverified)"
    return out, note


def _query_archetype_completeness(workspace_root: Path, skip: bool) -> tuple[dict[str, dict[str, str]] | None, str]:
    """Returns ({MODE: {archetype: state}}, note) from the archetype-code-completeness skill.

    CONSUMES that skill's own JSON output rather than re-deriving the hooks here (W1's
    explicit instruction), so the readiness dump and the archetype dump can never disagree
    about whether an archetype is code-complete. Runs under strategy-service's venv, where
    the engine factory / param-schema / allocator registries actually import.
    """
    if skip:
        return None, "skipped via --skip-archetype-probe"
    strategy_python = workspace_root / "strategy-service" / ".venv" / "bin" / "python3"
    if not strategy_python.exists():
        return None, f"{strategy_python} not found -- strategy-service venv unavailable in this environment"
    script = _SKILLS_DIR / "archetype-code-completeness" / "scripts" / "derive_archetype_completeness.py"
    if not script.exists():
        return None, f"{script} not found -- archetype-code-completeness skill absent"
    proc = subprocess.run(
        [str(strategy_python), str(script), "--json"],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(workspace_root / "strategy-service"),
    )
    if proc.returncode != 0:
        return None, f"archetype probe subprocess failed (exit {proc.returncode}): {proc.stderr.strip()[-300:]}"
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return None, f"archetype probe returned non-JSON output: {exc}"

    by_mode: dict[str, dict[str, str]] = defaultdict(dict)
    for row in payload.get("rows") or []:
        # No empty-string defaults: a row missing any of these is skipped, not coerced
        # into a blank key that would silently read as "archetype absent" downstream.
        mode = row.get("mode")
        name = row.get("archetype")
        state = (row.get("overall") or {}).get("state")
        if isinstance(mode, str) and isinstance(name, str) and isinstance(state, str) and mode and name and state:
            by_mode[mode][name] = state
    if not by_mode:
        return None, "archetype probe returned no usable rows"
    counts = {m: sum(1 for s in d.values() if s == "ready") for m, d in sorted(by_mode.items())}
    return dict(by_mode), f"archetype code-completeness read for {len(by_mode)} modes; code-complete per mode: {counts}"


def _query_mtds_live_feed(workspace_root: Path, skip: bool) -> tuple[frozenset[str], str]:
    """Returns (frozenset of venues with a registered live WSFeedConnector, note)."""
    if skip:
        return frozenset(), "skipped via --skip-mtds-probe"
    mtds_python = workspace_root / "market-tick-data-service" / ".venv" / "bin" / "python3"
    if not mtds_python.exists():
        return frozenset(), f"{mtds_python} not found -- market-tick-data-service venv unavailable in this environment"
    probe_script = _HERE.parent / "_mtds_live_feed_probe.py"
    proc = subprocess.run(
        [str(mtds_python), str(probe_script)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(workspace_root / "market-tick-data-service"),
    )
    if proc.returncode != 0:
        return (
            frozenset(),
            f"MTDS live-feed probe subprocess failed (exit {proc.returncode}): {proc.stderr.strip()[:300]}",
        )
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return frozenset(), f"MTDS live-feed probe returned non-JSON output: {exc}"
    return frozenset(result), f"{len(result)} venues registered in MTDS WS_FEED_CONNECTOR_FACTORIES"


def build_dump(
    venues: list[str],
    modes: list[str],
    coverage_payload: dict | None,
    position_avail: dict[str, dict[str, str]],
    execution_probe: dict[str, dict],
    mtds_live_registered: frozenset[str],
    workspace_root: Path | None = None,
    archetype_states: dict[str, dict[str, str]] | None = None,
    instruction_path_probe: dict[str, dict] | None = None,
) -> tuple[list[dict], dict]:
    # grain (FROM-T2 P1, 2026-08-20): detect_grain() reads the grain of the COVERAGE SOURCE, not
    # of the readiness ROWS this function builds (which are always venue x asset_group x mode,
    # unconditionally -- see the `rows.append` below). The old code reported coverage_grain under
    # a bare "grain" key, so a reader saw e.g. "instrument_type" and reasonably assumed the ROWS
    # carried that finer breakdown -- they never did (measured: all 864 rows carry only
    # venue/asset_group/mode/pipeline_stage/leg_states, no instrument_type key on any row). Two
    # keys now, neither silently claiming the other.
    coverage_source_grain = detect_grain(coverage_payload) if coverage_payload else "unmeasured"
    row_grain = "venue_asset_group_mode"
    # Measured once for the whole dump -- InstructionActionV2 handler coverage is
    # venue-independent, so re-deriving it per row would be waste AND would imply a
    # per-venue signal that does not exist. See instruction_actions.py.
    action_coverage = instruction_actions.measure(workspace_root or _WORKSPACE_ROOT_DEFAULT)
    cov_venue_ag = venue_asset_group_map(coverage_payload) if coverage_payload else {}
    uac_venue_ag = _uac_venue_asset_group_map()
    declared_venues = frozenset(VENUE_DATA_TYPE_CAPABILITIES.keys())

    cells_by_venue: dict[str, list] = defaultdict(list)
    if coverage_payload:
        for cell in iter_shard_cells(
            coverage_payload, coverage_source_grain if coverage_source_grain != "unmeasured" else None
        ):
            cells_by_venue[cell.venue].append(cell)

    layer1_by_venue: dict[str, dict] = {}
    if coverage_payload:
        layer1 = (coverage_payload.get("layer_1") or {}).get("by_asset_group") or {}
        for ag_block in layer1.values():
            for venue, block in (ag_block.get("by_venue") or {}).items():
                layer1_by_venue[venue] = block

    wallet_capability_venues = frozenset(VENUE_WALLET_CAPABILITIES.keys())
    capability_facts, capability_note = _capability_facts_by_venue(venues)
    print(f"Credential-requirement facts: {capability_note}")

    rows: list[dict] = []
    leg_state_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    rollup_state_counts: dict[str, int] = defaultdict(int)

    for venue in venues:
        asset_group = cov_venue_ag.get(venue) or uac_venue_ag.get(venue) or "UNKNOWN"
        venue_dts = _venue_data_types(venue)
        step17 = contract_step_17_check(venue, venue_dts)
        satisfying = frozenset(a.value if hasattr(a, "value") else str(a) for a in step17.satisfying_archetypes)

        vd_declared = checks.declared(venue, declared_venues)
        vd_is = checks.instruments_service_refdata(layer1_by_venue.get(venue))

        venue_cells = cells_by_venue.get(venue, [])
        mtds_cells = [(c.data_type, c.count("captured"), c.reachable_total()) for c in venue_cells]
        vd_mtds_batch = checks.mtds_captured(mtds_cells)
        vd_mtds_live = checks.mtds_live_feed(venue, mtds_live_registered)

        vd_mdps = checks.mdps_consumed(venue_dts, MDPS_DERIVABLE_DATA_TYPES)
        vd_features = checks.features_consumed(venue_dts, step17.orphaned_data_types)
        vd_archetype = checks.strategy_archetype_registered(satisfying)
        vd_transfers = checks.execution_transfers(venue, wallet_capability_venues)

        # Mode-invariant execution-service legs -- adapter presence doesn't vary
        # by mode (see checks.py's module comment on the execution surfaces).
        vd_fills = checks.execution_fills(venue, execution_probe)
        vd_trades = checks.execution_trades(venue, execution_probe)
        vd_balance = checks.execution_account_balance(venue, execution_probe)

        mode_avail = position_avail.get(venue)

        for mode in modes:
            mode_status = mode_avail.get(mode.lower()) if mode_avail else None
            vd_adapter = checks.strategy_position_adapter(venue, mode, mode_status)
            vd_strategy = checks.strategy_leg(vd_archetype, vd_adapter)
            vd_orders = checks.execution_orders(venue, mode, execution_probe)
            vd_instruction = checks.execution_instruction(venue, mode, instruction_path_probe)

            # instruments-service / declared / features-consumability / MDPS-capability are
            # structural (mode-invariant) facts; MTDS capture is a TWO-feed question (see
            # SKILL.md "What's real vs unverified, and why"): BATCH is coverage.json-observed,
            # PAPER and LIVE both reuse the SAME live-feed verdict, since paper always consumes
            # the live market-data feed (never a separate paper feed, operator ruling 2026-08-19).
            vd_mtds = vd_mtds_batch if mode == "BATCH" else vd_mtds_live

            legs = {
                "declared": vd_declared,
                "credentials": checks.credentials(venue, mode, capability_facts.get(venue)),
                "instruments_service": vd_is,
                "market_tick_data": vd_mtds,
                "market_data_processing": vd_mdps,
                "features": vd_features,
                "strategy": vd_strategy,
                "strategy_archetype_code": checks.strategy_archetype_code_complete(satisfying, mode, archetype_states),
                "execution_orders": vd_orders,
                "execution_fills": vd_fills,
                "execution_trades": vd_trades,
                "execution_account_balance": vd_balance,
                "execution_transfers": vd_transfers,
                "execution_instruction": vd_instruction,
            }
            overall = checks.rollup(legs)

            for leg_name, verdict in legs.items():
                leg_state_counts[leg_name][verdict.state] += 1
            rollup_state_counts[overall.state] += 1

            rows.append(
                {
                    "venue": venue,
                    "asset_group": asset_group,
                    "mode": mode,
                    "legs": {k: asdict(v) for k, v in legs.items()},
                    "overall": asdict(overall),
                }
            )

    summary = {
        "row_grain": row_grain,
        "coverage_source_grain": coverage_source_grain,
        "venue_count": len(venues),
        "mode_count": len(modes),
        "row_count": len(rows),
        "leg_state_counts": {k: dict(v) for k, v in leg_state_counts.items()},
        "overall_state_counts": dict(rollup_state_counts),
        # A dump-level finding, deliberately NOT folded into the per-row legs: the
        # handler gap is global and backtest-scoped, so attributing it to any single
        # venue-mode would claim more than was measured.
        "instruction_action_coverage": {
            "resolved": action_coverage.resolved,
            "denominator": action_coverage.denominator,
            "handled": list(action_coverage.handled),
            "control_plane": list(action_coverage.control_plane),
            "unhandled": list(action_coverage.unhandled),
            "sources": list(action_coverage.sources),
            "summary": action_coverage.summary(),
        },
    }
    return rows, summary


def _print_human(rows: list[dict], summary: dict, verbose: bool, limit: int) -> None:
    print(f"Readiness state dump -- rows: {summary['row_grain']}, coverage source: {summary['coverage_source_grain']}")
    print(f"Venues: {summary['venue_count']}, modes: {summary['mode_count']}, rows: {summary['row_count']}")
    print()
    print("=== Per-leg verdict counts (across all venues x modes in scope) ===")
    for leg in checks.LEG_ORDER:
        counts = summary["leg_state_counts"].get(leg, {})
        ready = counts.get("ready", 0)
        not_ready = counts.get("not_ready", 0)
        unverified = counts.get("unverified", 0)
        print(f"  {leg:<24} ready={ready:<6} not_ready={not_ready:<6} unverified={unverified:<6}")
    print()
    print("=== Overall (rollup) verdict counts ===")
    for state in ("ready", "not_ready", "unverified"):
        print(f"  {state:<12} {summary['overall_state_counts'].get(state, 0)}")
    print()

    cov = summary.get("instruction_action_coverage") or {}
    if cov:
        # Indexed, not .get(...)-with-a-default: build_dump always populates these keys, so a
        # missing one is a real defect that should fail loudly rather than print a blank line.
        print("=== Instruction-action handler coverage (GLOBAL finding, not per-venue) ===")
        print(f"  {cov['summary']}")
        if cov["unhandled"]:
            print(
                "  These actions have no settlement handler and raise UnhandledActionError. "
                "This is a real gap, but it is venue-independent and backtest-scoped, so it is "
                "reported here rather than failing every venue-mode row."
            )
        print(f"  sources: {cov['sources']}")
        print()

    if not verbose:
        print("(pass --verbose for the per-venue-per-mode table, --limit N to cap rows shown)")
        return

    print(f"=== Per-venue-per-mode rows (showing up to {limit}) ===")
    for row in rows[:limit]:
        overall = row["overall"]
        print(f"  {row['asset_group']}/{row['venue']} [{row['mode']}] -> {overall['state']}  ({overall['evidence']})")
        for leg in checks.LEG_ORDER:
            v = row["legs"][leg]
            print(f"      {leg:<24} {v['state']:<12} {v['evidence']}")
    if len(rows) > limit:
        print(f"  ... {len(rows) - limit} more rows omitted (raise --limit or use --json for the full dump)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--venue", action="append", default=None, help="Filter to one or more venues (repeatable)")
    parser.add_argument("--asset-group", action="append", default=None, help="Filter to one or more asset_groups")
    parser.add_argument("--mode", action="append", choices=list(MODES), default=None, help="Filter to a mode")
    parser.add_argument("--project", default=DEFAULT_PROJECT_ID, help="GCP project hosting the honest-coverage bucket")
    parser.add_argument("--date", default=None, help="coverage.json date (YYYY-MM-DD); defaults to latest")
    parser.add_argument("--workspace-root", default=None, help="Override the multi-repo checkout root")
    parser.add_argument("--skip-strategy-probe", action="store_true", help="Skip the strategy-service subprocess")
    parser.add_argument("--skip-execution-probe", action="store_true", help="Skip the execution-service subprocess")
    parser.add_argument(
        "--skip-instruction-path-probe",
        action="store_true",
        help="Skip the execution-service instruction-path subprocess (execution_instruction leg reports unverified)",
    )
    parser.add_argument("--skip-mtds-probe", action="store_true", help="Skip the market-tick-data-service subprocess")
    parser.add_argument(
        "--skip-archetype-probe",
        action="store_true",
        help="Skip the archetype-code-completeness subprocess (the strategy_archetype_code leg reports unverified)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of the human report")
    parser.add_argument("--verbose", action="store_true", help="Print the full per-venue-per-mode table")
    parser.add_argument("--limit", type=int, default=40, help="Max rows to print in --verbose mode (default 40)")
    args = parser.parse_args()

    workspace_root = Path(args.workspace_root) if args.workspace_root else _WORKSPACE_ROOT_DEFAULT

    coverage_payload = None
    coverage_note = "not loaded"
    try:
        coverage_payload, resolved_date, gcs_path = load_coverage(args.project, args.date)
        coverage_note = f"{gcs_path} (date={resolved_date})"
    except CoverageReadError as exc:
        print(
            f"WARNING: could not read coverage.json ({exc}) -- instruments_service/market_tick_data legs "
            "report unverified for every row",
            file=sys.stderr,
        )

    declared_venues = sorted(VENUE_DATA_TYPE_CAPABILITIES.keys())
    observed_venues = sorted(venue_asset_group_map(coverage_payload).keys()) if coverage_payload else []
    all_venues = sorted(set(declared_venues) | set(observed_venues))

    venue_filter = set(args.venue) if args.venue else None
    ag_filter = set(args.asset_group) if args.asset_group else None
    uac_venue_ag = _uac_venue_asset_group_map()
    cov_venue_ag = venue_asset_group_map(coverage_payload) if coverage_payload else {}

    venues = []
    for v in all_venues:
        if venue_filter and v not in venue_filter:
            continue
        ag = cov_venue_ag.get(v) or uac_venue_ag.get(v) or "UNKNOWN"
        if ag_filter and ag not in ag_filter:
            continue
        venues.append(v)

    modes = list(args.mode) if args.mode else list(MODES)

    position_avail, probe_note = _query_strategy_position_availability(venues, workspace_root, args.skip_strategy_probe)
    execution_probe, execution_probe_note = _query_execution_order_capability(
        venues, workspace_root, args.skip_execution_probe
    )
    instruction_path_probe, instruction_path_note = _query_execution_instruction_path(
        venues, workspace_root, args.skip_instruction_path_probe
    )
    mtds_live_registered, mtds_probe_note = _query_mtds_live_feed(workspace_root, args.skip_mtds_probe)
    archetype_states, archetype_note = _query_archetype_completeness(workspace_root, args.skip_archetype_probe)
    print(f"Archetype code-completeness probe: {archetype_note}")

    rows, summary = build_dump(
        venues,
        modes,
        coverage_payload,
        position_avail,
        execution_probe,
        mtds_live_registered,
        archetype_states=archetype_states,
        instruction_path_probe=instruction_path_probe,
    )
    summary["coverage_source"] = coverage_note
    summary["strategy_probe"] = probe_note
    summary["execution_probe"] = execution_probe_note
    summary["instruction_path_probe"] = instruction_path_note
    summary["mtds_live_probe"] = mtds_probe_note

    if args.json:
        json.dump({"summary": summary, "rows": rows}, sys.stdout, indent=2)
        print()
    else:
        print(f"Coverage source: {coverage_note}")
        print(f"Strategy position-adapter probe: {probe_note}")
        print(f"Execution order-capability probe: {execution_probe_note}")
        print(f"MTDS live-feed probe: {mtds_probe_note}")
        print()
        _print_human(rows, summary, args.verbose, args.limit)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
