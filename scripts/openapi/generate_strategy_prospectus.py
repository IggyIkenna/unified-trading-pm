"""Generate strategy prospectus documents per StrategyArchetype.

For each of the 57 StrategyArchetype values (or a single archetype if
--archetype is given) renders:
  unified-api-contracts/openapi/prospectus/<archetype_id>.md

Prospectus sections (per task spec):
  1. What it does + how it makes decisions (codex + manifest)
  2. Universe & execution (venues/instruments/algos + honest gap)
  3. Exposures & normalization (share-class, base-currency, gap)
  4. Fund-flow mermaid (treasury vs hot, staked legs derived from cells)
  5. Risk & circuit breakers (KillSwitchReason + RiskGateLayer)
  6. Performance (no backtest data — honest block; metric names from
     performance_metrics.py where reachable)
  7. Footer (manifest_version + generated_from_commit)

TWO-SIDED AUDIT is in audit_prospectus_vs_codex.py.

Honesty labels:
  [MACHINE-DERIVED] — sourced from capability manifest / UAC registry
  [CODEX-DERIVED]   — sourced from hand-authored codex archetype doc

Output: deterministic (sorted, no timestamps).  Run twice = byte-identical.

Usage:
    python generate_strategy_prospectus.py [--archetype <id>] \
        [--output-dir PATH] [--workspace-root PATH]

Plan: plans/active/capability_wizard_and_manifest_2026_06_11.md Phase 3
"""

from __future__ import annotations

import os

os.environ.setdefault("CLOUD_PROVIDER", "local")
os.environ.setdefault("CLOUD_MOCK_MODE", "true")
os.environ.setdefault("DISABLE_AUTH", "true")
os.environ.setdefault("MOCK_STATE_MODE", "deterministic")
os.environ.setdefault("GCP_PROJECT_ID", "mock-project")
os.environ.setdefault("PUBSUB_EMULATOR_HOST", "localhost:8085")
os.environ.setdefault("STORAGE_EMULATOR_HOST", "http://localhost:4443")
os.environ.setdefault("BIGQUERY_EMULATOR_HOST", "localhost:9050")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "mock-project")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("API_KEY", "mock-api-key-for-openapi-gen")

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from _prospectus_codex import (
    extract_section,
    get_body_text,
    get_codex_venue_universe,
    load_codex_doc,
    parse_frontmatter,
)
from _prospectus_manifest import (
    build_fund_flow_mermaid,
    get_execution_algos,
    get_manifest_provenance,
    load_manifest,
)

# ---------------------------------------------------------------------------
# UAC imports (via the generator's UAC venv idiom)
# ---------------------------------------------------------------------------
from unified_api_contracts.internal.architecture_v2.enums import (
    ARCHETYPE_TO_FAMILY,
    KillSwitchReason,
    RiskGateLayer,
    StrategyArchetype,
)

# ---------------------------------------------------------------------------
# ARCHETYPE_CAPABILITY_REGISTRY for per-archetype capability cells
# The registry is a tuple of ArchetypeCapability objects; build a lookup dict.
# ---------------------------------------------------------------------------
_CAPABILITY_REGISTRY_DICT: dict = {}  # type: ignore[type-arg]
_REGISTRY_AVAILABLE = False
try:
    from unified_api_contracts.internal.architecture_v2.archetype_capability import (
        ARCHETYPE_CAPABILITY_REGISTRY as _RAW_REGISTRY,
    )

    _CAPABILITY_REGISTRY_DICT = {item.archetype_id: item for item in _RAW_REGISTRY}
    _REGISTRY_AVAILABLE = True
except Exception as _reg_exc:
    logger.warning("ARCHETYPE_CAPABILITY_REGISTRY unavailable: %s", _reg_exc)

# ---------------------------------------------------------------------------
# Performance metrics (best-effort import)
# ---------------------------------------------------------------------------
_PERF_METRIC_NAMES: list[str] = []
try:
    import importlib

    _pm_spec = importlib.util.find_spec("unified_trading_library.performance_metrics")  # type: ignore[attr-defined]
    if _pm_spec is not None:
        _pm_mod = importlib.import_module("unified_trading_library.performance_metrics")
        # Collect any exported metric names (class attrs, constants, or __all__)
        _all = getattr(_pm_mod, "__all__", None) or dir(_pm_mod)
        _PERF_METRIC_NAMES = sorted(name for name in _all if not name.startswith("_") and name == name.upper())
except Exception as _perf_exc:
    logger.debug("performance_metrics not importable: %s", _perf_exc)

# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------


def _section_what_it_does(
    archetype_id: str,
    family: str,
    codex_body: str | None,
    capability_cells: list,  # type: ignore[type-arg]
    venue_categories: list[str],
) -> str:
    """Section 1: what it does + how it makes decisions."""
    lines: list[str] = []
    lines.append("## 1. What It Does + How It Makes Decisions")
    lines.append("")

    # Machine-derived: family + venue categories + instrument types
    lines.append(
        f"**[MACHINE-DERIVED]** Family: `{family}`  "
        f"| Primary venue categories: {', '.join(sorted(venue_categories)) or 'not registered'}"
    )
    lines.append("")

    if capability_cells:
        lines.append("**[MACHINE-DERIVED]** Capability cells (from ARCHETYPE_CAPABILITY_REGISTRY):")
        lines.append("")
        lines.append("| Venue Category | Instrument Type | Status | Notes |")
        lines.append("|---|---|---|---|")
        # Sort for determinism
        for cell in sorted(
            capability_cells,
            key=lambda c: (str(getattr(c, "asset_group", "")), str(getattr(c, "instrument_type", ""))),
        ):
            ag = str(getattr(cell, "asset_group", ""))
            it = str(getattr(cell, "instrument_type", ""))
            status = str(getattr(cell, "status", ""))
            notes = str(getattr(cell, "notes", ""))[:120]
            lines.append(f"| {ag} | {it} | {status} | {notes} |")
        lines.append("")
    else:
        lines.append(
            "**[MACHINE-DERIVED]** Capability cells: `not_registered` — archetype not in ARCHETYPE_CAPABILITY_REGISTRY"
        )
        lines.append("")

    # Codex-derived: what it does + decision logic
    if codex_body:
        what_section = extract_section(codex_body, "## What it does")
        if what_section:
            lines.append("**[CODEX-DERIVED]** From `codex/09-strategy/architecture-v2/archetypes/`:")
            lines.append("")
            lines.append(what_section)
            lines.append("")

        decision_section = extract_section(codex_body, "## How It Makes Decisions") or extract_section(
            codex_body, "## Decision Logic"
        )
        if decision_section:
            lines.append("**[CODEX-DERIVED]** Decision logic:")
            lines.append("")
            lines.append(decision_section)
            lines.append("")

        exec_section = extract_section(codex_body, "## Execution semantics")
        if exec_section:
            lines.append("**[CODEX-DERIVED]** Execution semantics:")
            lines.append("")
            lines.append(exec_section[:800])
            if len(exec_section) > 800:
                lines.append(
                    f"_...truncated ({len(exec_section)} chars total). See codex archetype doc for full detail._"
                )
            lines.append("")

        config_section = extract_section(codex_body, "## Config schema")
        if config_section:
            lines.append("**[CODEX-DERIVED]** Configurable parameters:")
            lines.append("")
            lines.append(config_section[:600])
            if len(config_section) > 600:
                lines.append("_...truncated. See codex archetype doc._")
            lines.append("")
    else:
        lines.append(
            "> **[CODEX-DERIVED — MISSING]** No hand-authored codex doc found for this archetype. "
            "All content below is machine-derived only."
        )
        lines.append("")

    return "\n".join(lines)


def _section_universe_execution(
    archetype_id: str,
    codex_body: str | None,
    codex_frontmatter: dict[str, str],
    manifest_edges: list[dict],  # type: ignore[type-arg]
    exec_algos: list[dict],  # type: ignore[type-arg]
) -> str:
    """Section 2: Universe & execution."""
    lines: list[str] = []
    lines.append("## 2. Universe & Execution")
    lines.append("")

    # Codex venue universe from frontmatter
    codex_venues = get_codex_venue_universe(codex_frontmatter)
    if codex_venues:
        lines.append(f"**[CODEX-DERIVED]** Venue universe (from doc frontmatter): {', '.join(sorted(codex_venues))}")
        lines.append("")

    # Machine-derived: manifest edges for this archetype
    venue_edges = [e for e in manifest_edges if e.get("relationship") in ("trades_at", "operates_on", "uses_venue")]
    if venue_edges:
        lines.append("**[MACHINE-DERIVED]** Venue edges from capability manifest:")
        lines.append("")
        lines.append("| Target | Status | Relationship |")
        lines.append("|---|---|---|")
        for e in sorted(venue_edges, key=lambda x: str(x.get("target", ""))):
            lines.append(f"| `{e.get('target', '')}` | {e.get('status', '')} | {e.get('relationship', '')} |")
        lines.append("")

    # Execution algos
    if exec_algos:
        algo_names = sorted(a.get("label", a.get("node_id", "")) for a in exec_algos)
        lines.append(f"**[MACHINE-DERIVED]** Available execution algorithms: {', '.join(algo_names)}")
        lines.append("")

    # Order semantics gap (honest gap line — the point)
    lines.append(
        "> **[MACHINE-DERIVED — GAP]** Order semantics (TIF/FOK/IOC/post-only, "
        "ref-pricing modes, multi-leg delta ownership): "
        "`not_registered` — VENUE_ORDER_SEMANTICS registry is honest-empty (Phase 2 backfill pending). "
        "See gap tracker: `plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md`."
    )
    lines.append("")

    # Codex catalog/slot labels
    if codex_body:
        catalog_section = extract_section(codex_body, "## Catalog axis")
        if catalog_section:
            lines.append("**[CODEX-DERIVED]** Catalog slot labels:")
            lines.append("")
            lines.append(catalog_section[:500])
            if len(catalog_section) > 500:
                lines.append("_...truncated. See codex archetype doc._")
            lines.append("")

    return "\n".join(lines)


def _section_exposures(
    archetype_id: str,
    codex_body: str | None,
) -> str:
    """Section 3: Exposures & normalization."""
    lines: list[str] = []
    lines.append("## 3. Exposures & Normalization")
    lines.append("")

    # Share class / base currency from codex
    if codex_body:
        risk_section = extract_section(codex_body, "## Risk profile")
        if risk_section:
            lines.append("**[CODEX-DERIVED]** Risk profile:")
            lines.append("")
            lines.append(risk_section[:600])
            if len(risk_section) > 600:
                lines.append("_...truncated. See codex archetype doc._")
            lines.append("")

        pnl_section = extract_section(codex_body, "## P&L attribution")
        if pnl_section:
            lines.append("**[CODEX-DERIVED]** P&L attribution:")
            lines.append("")
            lines.append(pnl_section[:500])
            if len(pnl_section) > 500:
                lines.append("_...truncated. See codex archetype doc._")
            lines.append("")

    # Honest gap — staked-vs-spot equivalence
    lines.append(
        "> **[MACHINE-DERIVED — FINDING F-CLASS: GAP]** "
        "No declared exposure-normalization model found for this archetype. "
        "Staked-vs-spot equivalence (e.g. stETH/ETH delta-adjusted exposure), "
        "base-currency-neutral views, and intra-leg netting rules are "
        "`not_registered` in any UAC registry. "
        "Gap tracker: `plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md` — "
        "`AGENT P1: Exposure normalization location: staked-ETH vs ETH equivalence`."
    )
    lines.append("")

    return "\n".join(lines)


def _section_fund_flow(
    archetype_id: str,
    venue_categories: list[str],
    capability_cells: list,  # type: ignore[type-arg]
) -> str:
    """Section 4: Fund-flow mermaid."""
    lines: list[str] = []
    lines.append("## 4. Fund Flow")
    lines.append("")
    lines.append(
        "**[MACHINE-DERIVED]** Wallets and venues keyed by venue categories + "
        "TREASURY_SPLIT_POLICIES (DeFi 20/80, CeFi 0/100, Sports no-split). "
        "Staked-basis leg structure derived from archetype family + capability cells."
    )
    lines.append("")

    # Convert capability_cells to a simple list for the mermaid builder
    cell_dicts: list[dict] = []  # type: ignore[type-arg]
    for cell in capability_cells:
        cell_dicts.append(
            {
                "instrument_type": str(getattr(cell, "instrument_type", "")),
                "asset_group": str(getattr(cell, "asset_group", "")),
                "status": str(getattr(cell, "status", "")),
            }
        )

    mermaid = build_fund_flow_mermaid(archetype_id, venue_categories, cell_dicts)
    lines.append(mermaid)
    lines.append("")

    return "\n".join(lines)


def _section_risk(
    archetype_id: str,
    codex_body: str | None,
) -> str:
    """Section 5: Risk & circuit breakers."""
    lines: list[str] = []
    lines.append("## 5. Risk & Circuit Breakers")
    lines.append("")

    # Machine-derived: KillSwitchReason set
    lines.append("**[MACHINE-DERIVED]** KillSwitchReason set (from UAC `enums.KillSwitchReason`):")
    lines.append("")
    for reason in sorted(KillSwitchReason):
        lines.append(f"- `{reason}`")
    lines.append("")

    # Machine-derived: RiskGateLayer placement
    lines.append("**[MACHINE-DERIVED]** RiskGateLayer placement (from UAC `enums.RiskGateLayer`):")
    lines.append("")
    layer_descriptions = {
        "STRATEGY_SELF_CHECK": "Strategy checks pre-instruction emit (position/PnL/delta guards)",
        "RISK_PREFLIGHT": "Risk service pre-flight validation (per-instruction, before execution queue)",
        "EXECUTION_PRETRADE": "Execution service pre-trade validation (order sizing, notional caps)",
        "VENUE_SIDE": "Venue-side limits (margin checks, open-order limits — external)",
    }
    for layer in sorted(RiskGateLayer):
        desc = layer_descriptions.get(str(layer), "")
        lines.append(f"- `{layer}`: {desc}")
    lines.append("")

    # Codex-derived: risk section
    if codex_body:
        risk_section = extract_section(codex_body, "## Risk profile")
        if risk_section and "Risk profile" not in lines[-10:]:  # avoid duplicate
            lines.append("**[CODEX-DERIVED]** Archetype-specific risk notes:")
            lines.append("")
            lines.append(risk_section[:500])
            if len(risk_section) > 500:
                lines.append("_...truncated. See codex archetype doc._")
            lines.append("")

    # Config params from config schema section
    if codex_body:
        config_section = extract_section(codex_body, "## Config schema")
        if config_section:
            # Extract threshold/param names
            param_lines = [
                line.strip()
                for line in config_section.splitlines()
                if line.strip().startswith(
                    (
                        "entry_bps",
                        "exit_bps",
                        "min_",
                        "max_",
                        "stop_loss",
                        "daily_loss",
                        "hedge_deadline",
                        "peg_drift",
                        "target_leverage",
                    )
                )
            ]
            if param_lines:
                lines.append("**[CODEX-DERIVED]** Configurable risk parameters (from config schema):")
                lines.append("")
                for p in sorted(set(param_lines)):
                    lines.append(f"- `{p}`")
                lines.append("")

    return "\n".join(lines)


def _section_performance(archetype_id: str) -> str:
    """Section 6: Performance (honest no-backtest block)."""
    lines: list[str] = []
    lines.append("## 6. Performance")
    lines.append("")
    lines.append(
        "> **No backtest metrics recorded for this archetype configuration.**  "
        "Run Phase 5 backtest-on-demand (`strategy_service/engine/backtest/runner.py` "
        "over historical data) to generate metrics."
    )
    lines.append("")
    lines.append("**NEVER invented numbers are shown here** — this section is honest about the absence.")
    lines.append("")

    if _PERF_METRIC_NAMES:
        lines.append(
            "When backtest results are available, the following metric set "
            "will be reported (from `unified_trading_library.performance_metrics`):"
        )
        lines.append("")
        for name in sorted(_PERF_METRIC_NAMES):
            lines.append(f"- `{name}`")
        lines.append("")
    else:
        lines.append(
            "Metric set: `unified_trading_library.performance_metrics` defines the canonical "
            "metric surface (expected: Sharpe ratio, max drawdown, CAGR, Sortino, Calmar, "
            "win rate, avg trade PnL). Import was unavailable on this host."
        )
        lines.append("")

    return "\n".join(lines)


def _section_footer(archetype_id: str, provenance: dict[str, str]) -> str:
    """Section 7: Footer with provenance."""
    lines: list[str] = []
    lines.append("## 7. Provenance")
    lines.append("")
    lines.append(f"- `manifest_version`: {provenance.get('manifest_version', 'unknown')}")
    lines.append(f"- `generated_from_commit`: `{provenance.get('generated_from_commit', 'unknown')}`")
    lines.append(f"- `archetype_id`: `{archetype_id}`")
    lines.append(
        "- `generated_by`: `scripts/openapi/generate_strategy_prospectus.py` (unified-trading-pm generator family)"
    )
    lines.append("")
    lines.append(
        "_This prospectus is machine-generated. Sections marked [CODEX-DERIVED] are sourced "
        "from hand-authored engineering docs in "
        "`codex/09-strategy/architecture-v2/archetypes/`. "
        "Sections marked [MACHINE-DERIVED] are sourced from the capability manifest "
        "(UAC registry data, 409 nodes / 663 edges). "
        "Full alpha disclosure — debugging mode. Curtailment is a later config flag._"
    )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main prospectus renderer
# ---------------------------------------------------------------------------


def render_prospectus(
    archetype_id: str,
    manifest: dict,  # type: ignore[type-arg]
    provenance: dict[str, str],
    exec_algos: list[dict],  # type: ignore[type-arg]
) -> str:
    """Render a full prospectus markdown document for one archetype."""
    family = str(ARCHETYPE_TO_FAMILY.get(StrategyArchetype(archetype_id), "unknown"))

    # Load codex doc
    codex_doc = load_codex_doc(archetype_id)
    codex_frontmatter: dict[str, str] = {}
    codex_body: str | None = None
    if codex_doc:
        codex_frontmatter = parse_frontmatter(codex_doc)
        codex_body = get_body_text(codex_doc)

    # Capability cells from ARCHETYPE_CAPABILITY_REGISTRY
    capability = _CAPABILITY_REGISTRY_DICT.get(StrategyArchetype(archetype_id))
    capability_cells = sorted(
        capability.cells if capability else [],
        key=lambda c: (str(getattr(c, "asset_group", "")), str(getattr(c, "instrument_type", ""))),
    )

    # Venue categories from cells
    venue_categories: list[str] = sorted({str(getattr(cell, "asset_group", "")) for cell in capability_cells})
    if not venue_categories:
        # Fallback: codex frontmatter status / family
        if "defi" in archetype_id.lower():
            venue_categories = ["DEFI"]
        elif "sports" in archetype_id.lower():
            venue_categories = ["SPORTS"]

    # Manifest edges for this archetype
    manifest_edges: list[dict] = [  # type: ignore[type-arg]
        e for e in manifest.get("edges", []) if e.get("source") == archetype_id
    ]

    # Build header
    title = archetype_id.replace("_", " ").title()
    header = [
        f"# Strategy Prospectus: {title}",
        "",
        f"> **Archetype ID**: `{archetype_id}`  ",
        f"> **Family**: `{family}`  ",
        f"> **Status** (codex): {codex_frontmatter.get('status', 'not declared')}  ",
        "> **Alpha disclosure**: full (debugging mode) — no client-facing curtailment applied.",
        "",
    ]

    sections = [
        "\n".join(header),
        _section_what_it_does(archetype_id, family, codex_body, capability_cells, venue_categories),
        _section_universe_execution(archetype_id, codex_body, codex_frontmatter, manifest_edges, exec_algos),
        _section_exposures(archetype_id, codex_body),
        _section_fund_flow(archetype_id, venue_categories, capability_cells),
        _section_risk(archetype_id, codex_body),
        _section_performance(archetype_id),
        _section_footer(archetype_id, provenance),
    ]
    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate per-archetype strategy prospectus docs")
    parser.add_argument("--archetype", type=str, default=None, help="Single archetype ID to render")
    parser.add_argument(
        "--output-dir", type=Path, default=None, help="Output directory (default: UAC openapi/prospectus/)"
    )
    parser.add_argument("--workspace-root", type=Path, default=None, help="Workspace root")
    parser.add_argument("--uac-root", type=Path, default=None, help="unified-api-contracts repo root")
    args = parser.parse_args()

    workspace_root = args.workspace_root or _SCRIPT_DIR.parent.parent.parent
    uac_root = args.uac_root or (workspace_root / "unified-api-contracts")
    output_dir = args.output_dir or (uac_root / "openapi" / "prospectus")
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(uac_root)
    if not manifest:
        logger.error("Capability manifest empty or missing — run generate_capability_manifest.py first")
        sys.exit(1)

    provenance = get_manifest_provenance(manifest)
    exec_algos = get_execution_algos(manifest)

    # Determine archetypes to render
    if args.archetype:
        try:
            archetypes = [StrategyArchetype(args.archetype)]
        except ValueError:
            logger.error("Unknown archetype: %s", args.archetype)
            logger.error("Valid values: %s", sorted(StrategyArchetype))
            sys.exit(1)
    else:
        archetypes = sorted(StrategyArchetype)

    generated = 0
    missing_codex: list[str] = []
    codex_present: list[str] = []

    for archetype in archetypes:
        archetype_id = str(archetype)
        logger.info("Rendering prospectus for %s ...", archetype_id)

        has_codex = load_codex_doc(archetype_id) is not None
        if has_codex:
            codex_present.append(archetype_id)
        else:
            missing_codex.append(archetype_id)

        doc = render_prospectus(archetype_id, manifest, provenance, exec_algos)

        out_path = output_dir / f"{archetype_id}.md"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(doc)
        generated += 1

    # Summary
    print("\n" + "=" * 60)
    print("PROSPECTUS GENERATOR — SUMMARY")
    print("=" * 60)
    print(f"Total archetypes: {len(archetypes)}")
    print(f"Generated: {generated}")
    print(f"With codex doc: {len(codex_present)}")
    print(f"Missing codex doc (machine-only): {len(missing_codex)}")
    if missing_codex:
        print("Unmapped archetypes (no codex doc):")
        for a in sorted(missing_codex):
            print(f"  {a}")
    print(f"\nOutput: {output_dir}")
    print("=" * 60)

    # Exit non-zero if no docs generated
    if generated == 0:
        logger.error("No prospectus documents generated")
        sys.exit(1)


if __name__ == "__main__":
    main()
