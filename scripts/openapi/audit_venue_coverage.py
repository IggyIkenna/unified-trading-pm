"""Venue coverage audit (F39) — per-venue verdict against adapter inventory.

Cross-references every venue in the capability manifest against four axes:
  1. instruments snapshot (VENUE_CATEGORY_MAP + INSTRUMENT_TYPES_BY_VENUE)
  2. ENDPOINT_REGISTRY (API credential / access endpoints)
  3. execution-service real adapter inventory (trade_execution/adapters/*.py)
  4. archetype/leg eligibility (ARCHETYPE_LEG_STRUCTURES eligible_venue_ids)

Per-venue verdict:
  wired                  — adapter exists + eligible in >= 1 archetype leg
  adapter-no-eligibility — adapter exists but NOT in any leg eligible_venue_ids
  registered-no-adapter  — in ENDPOINT_REGISTRY but no execution adapter
  orphan                 — in manifest/registry but no adapter and not in ENDPOINT_REGISTRY

Deterministic: sorted, no timestamps, two-run byte-identical.

Output: unified-api-contracts/openapi/venue-coverage-report.md

Usage:
    python audit_venue_coverage.py [--output-dir PATH] [--workspace-root PATH]

Plan: plans/active/capability_wizard_and_manifest_2026_06_11.md Phase 6A (F39)
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
_WORKSPACE_ROOT_DEFAULT = _SCRIPT_DIR / ".." / ".." / ".."

# ---------------------------------------------------------------------------
# Adapter inventory (execution-service/execution_service/trade_execution/adapters)
# Manually maintained mapping: adapter file (relative to adapters/ dir) → venue IDs.
# Venue IDs match the uppercase canonical form used by VENUE_CATEGORY_MAP.
# When an adapter serves multiple venues (e.g. BINANCE-FUTURES + BINANCE-SPOT),
# all venues are listed.  IBKR is a BROKER (not a venue) — excluded here.
# The *_native.py and *_ccxt.py variants map to the same venues as their peers;
# we cite all files so the audit path is traceable.
# ---------------------------------------------------------------------------

# Maps uppercase canonical venue_id → list of adapter file paths (relative to
# execution_service/trade_execution/adapters/).
_ADAPTER_INVENTORY: dict[str, list[str]] = {
    "BETFAIR": ["sports_adapter.py"],
    "BINANCE-FUTURES": ["binance_ccxt.py", "binance_native.py"],
    "BINANCE-SPOT": ["binance_ccxt.py", "binance_native.py"],
    "BITFINEX-SPOT": ["bitfinex_native.py"],
    "BITGET-FUTURES": ["bitget_native.py"],
    "BITGET-SPOT": ["bitget_native.py"],
    "BYBIT-FUTURES": ["bybit_ccxt.py", "bybit_native.py"],
    "BYBIT-SPOT": ["bybit_ccxt.py", "bybit_native.py"],
    "CBOE": ["cboe_adapter.py"],
    "CME": ["cme_adapter.py"],
    "COINBASE-SPOT": ["coinbase_ccxt.py"],
    "DERIBIT": ["deribit_ccxt.py"],
    "FX": ["fx_adapter.py"],
    "HYPERLIQUID": ["hyperliquid_ccxt.py"],
    "ICE": ["ice_adapter.py"],
    "KRAKEN-FUTURES": ["kraken_rest_adapter.py"],
    "KRAKEN-SPOT": ["kraken_rest_adapter.py"],
    "NASDAQ": ["nasdaq_adapter.py"],
    "NYSE": ["nyse_adapter.py"],
    "OKX-FUTURES": ["okx_ccxt.py", "okx_native.py"],
    "OKX-SPOT": ["okx_ccxt.py", "okx_native.py"],
    "POLYMARKET": ["polymarket_adapter.py"],
    "UPBIT": ["upbit_ccxt.py"],
}

# Lowercase normalised form → uppercase canonical venue_id (for leg eligibility lookup)
# leg seeds use lowercase without the -SPOT/-FUTURES suffix for generic references
_LOWERCASE_TO_CANONICAL: dict[str, list[str]] = {}
for _canon in _ADAPTER_INVENTORY:
    _lc = _canon.lower()
    _LOWERCASE_TO_CANONICAL.setdefault(_lc, []).append(_canon)
    # Also add base form: "binance-futures" → "binance"
    _base = _lc.split("-")[0]
    if _base != _lc:
        _LOWERCASE_TO_CANONICAL.setdefault(_base, []).append(_canon)


# ---------------------------------------------------------------------------
# Registry loading helpers
# ---------------------------------------------------------------------------


def _load_venue_category_map(uac_root: Path) -> dict[str, str]:
    """Load VENUE_CATEGORY_MAP from unified-api-contracts."""
    sys.path.insert(0, str(uac_root))
    try:
        from unified_api_contracts.registry import VENUE_CATEGORY_MAP  # noqa: qg-deep-import

        return {str(k): str(v) for k, v in VENUE_CATEGORY_MAP.items()}
    except Exception as exc:
        logger.warning("VENUE_CATEGORY_MAP unavailable: %s", exc)
        return {}


def _load_endpoint_registry_venues(uac_root: Path) -> set[str]:
    """Return set of uppercase venue IDs that appear in ENDPOINT_REGISTRY."""
    sys.path.insert(0, str(uac_root))
    try:
        from unified_api_contracts.registry import ENDPOINT_REGISTRY  # noqa: qg-deep-import

        return {str(spec.venue).upper().strip() for spec in ENDPOINT_REGISTRY if spec.venue}
    except Exception as exc:
        logger.warning("ENDPOINT_REGISTRY unavailable: %s", exc)
        return set()


def _load_leg_eligible_venues(uac_root: Path) -> set[str]:
    """Return set of lowercase venue IDs that appear in any archetype leg eligible_venue_ids."""
    sys.path.insert(0, str(uac_root))
    try:
        from unified_api_contracts.internal.architecture_v2.archetype_leg_spec import (  # noqa: qg-deep-import
            ARCHETYPE_LEG_STRUCTURES,
        )

        result: set[str] = set()
        for structure in ARCHETYPE_LEG_STRUCTURES.values():
            for leg in structure.legs:
                result.update(str(v).lower() for v in leg.eligible_venue_ids)
        return result
    except Exception as exc:
        logger.warning("ARCHETYPE_LEG_STRUCTURES unavailable: %s", exc)
        return set()


# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------

Verdict = str  # "wired" | "adapter-no-eligibility" | "registered-no-adapter" | "orphan"


def _get_verdict(
    venue_id: str,
    has_adapter: bool,
    in_endpoint_registry: bool,
    in_leg_eligibility: bool,
) -> Verdict:
    """Compute per-venue verdict from the four axes."""
    if has_adapter and in_leg_eligibility:
        return "wired"
    if has_adapter and not in_leg_eligibility:
        return "adapter-no-eligibility"
    if not has_adapter and in_endpoint_registry:
        return "registered-no-adapter"
    # No adapter, not in ENDPOINT_REGISTRY — orphan in manifest/registry
    return "orphan"


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

_VERDICT_ORDER = ["wired", "adapter-no-eligibility", "registered-no-adapter", "orphan"]

_VERDICT_DESCRIPTION = {
    "wired": "execution adapter exists + venue appears in >= 1 archetype leg eligible_venue_ids",
    "adapter-no-eligibility": "execution adapter exists but venue NOT in any archetype leg eligible_venue_ids",
    "registered-no-adapter": "venue in ENDPOINT_REGISTRY (data/API access) but NO execution adapter",
    "orphan": "venue in manifest/registry but NO execution adapter AND not in ENDPOINT_REGISTRY",
}


def render_report(
    rows: list[dict[str, object]],
) -> str:
    """Render the venue coverage report (deterministic — sorted inputs, no timestamps)."""
    by_verdict: dict[str, list[dict[str, object]]] = {v: [] for v in _VERDICT_ORDER}
    for row in rows:
        verdict = str(row["verdict"])
        by_verdict.setdefault(verdict, []).append(row)

    lines: list[str] = [
        "# Venue Coverage Report (F39)",
        "#",
        "# Cross-reference: VENUE_CATEGORY_MAP + INSTRUMENT_TYPES_BY_VENUE",
        "#   x ENDPOINT_REGISTRY x execution-service adapter inventory",
        "#   x ARCHETYPE_LEG_STRUCTURES eligible_venue_ids",
        "#",
        "# Verdict definitions:",
    ]
    for v, desc in _VERDICT_DESCRIPTION.items():
        lines.append(f"#   {v}: {desc}")
    lines.append("#")
    lines.append(f"# Total venues: {len(rows)}")
    for v in _VERDICT_ORDER:
        count = len(by_verdict[v])
        lines.append(f"#   {v}: {count}")
    lines.append("")

    for verdict in _VERDICT_ORDER:
        group = sorted(by_verdict[verdict], key=lambda r: str(r["venue_id"]))
        lines.append(f"## {verdict.upper()} ({len(group)})")
        lines.append(f"# {_VERDICT_DESCRIPTION[verdict]}")
        lines.append("")
        if not group:
            lines.append("(none)")
            lines.append("")
            continue
        for row in group:
            venue_id = str(row["venue_id"])
            category = str(row.get("category", ""))
            adapters = row.get("adapters", [])
            adapters_str = ", ".join(sorted(str(a) for a in adapters)) if adapters else "(none)"
            in_er = bool(row.get("in_endpoint_registry", False))
            in_leg = bool(row.get("in_leg_eligibility", False))
            line_parts = [f"  {venue_id}"]
            line_parts.append(f"category={category or '(unknown)'}")
            line_parts.append(f"adapter={adapters_str}")
            line_parts.append(f"endpoint_registry={'yes' if in_er else 'no'}")
            line_parts.append(f"leg_eligible={'yes' if in_leg else 'no'}")
            lines.append("  ".join(line_parts))
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main audit logic
# ---------------------------------------------------------------------------


def build_venue_rows(
    venue_category_map: dict[str, str],
    endpoint_registry_venues: set[str],
    leg_eligible_venues: set[str],
) -> list[dict[str, object]]:
    """Build per-venue rows with all four axes populated."""
    rows: list[dict[str, object]] = []

    # All venues = union of VENUE_CATEGORY_MAP keys + ENDPOINT_REGISTRY venues +
    # adapter inventory canonical IDs.  Some adapters serve venues not yet in the
    # registry (e.g. FX, BITFINEX-SPOT, KRAKEN-*) — include them so the audit
    # captures every adapter-backed venue regardless of registry coverage.
    all_venue_ids: set[str] = (
        set(venue_category_map.keys())
        | endpoint_registry_venues
        | set(_ADAPTER_INVENTORY.keys())
    )

    for venue_id in sorted(all_venue_ids):
        uid = venue_id.upper()

        # Adapter lookup: exact match (uppercase) or base-form (strip -SPOT/-FUTURES)
        adapter_files: list[str] = list(_ADAPTER_INVENTORY.get(uid, []))
        if not adapter_files:
            # Try base form (e.g. "BINANCE" matches "BINANCE-SPOT" adapters)
            base = uid.split("-")[0]
            for canon, files in _ADAPTER_INVENTORY.items():
                if canon.split("-")[0] == base:
                    adapter_files.extend(files)
            adapter_files = sorted(set(adapter_files))

        has_adapter = len(adapter_files) > 0

        # ENDPOINT_REGISTRY: case-insensitive match
        in_er = uid in endpoint_registry_venues or venue_id.lower() in {
            v.lower() for v in endpoint_registry_venues
        }

        # Leg eligibility: lowercase/base match
        lc = venue_id.lower()
        base_lc = lc.split("-")[0]
        in_leg = lc in leg_eligible_venues or base_lc in leg_eligible_venues

        verdict = _get_verdict(venue_id, has_adapter, in_er, in_leg)
        category = venue_category_map.get(venue_id, "")

        rows.append(
            {
                "venue_id": venue_id,
                "category": category,
                "has_adapter": has_adapter,
                "adapters": adapter_files,
                "in_endpoint_registry": in_er,
                "in_leg_eligibility": in_leg,
                "verdict": verdict,
            }
        )

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: UAC openapi/)",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Workspace root (default: three levels above this script)",
    )
    args = parser.parse_args()

    workspace_root = (args.workspace_root or _WORKSPACE_ROOT_DEFAULT).resolve()
    uac_root = workspace_root / "unified-api-contracts"
    output_dir = (args.output_dir or uac_root / "openapi").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Add uac_root to sys.path for imports
    if str(uac_root) not in sys.path:
        sys.path.insert(0, str(uac_root))

    logger.info("Loading registries from %s", uac_root)
    venue_category_map = _load_venue_category_map(uac_root)
    endpoint_registry_venues = _load_endpoint_registry_venues(uac_root)
    leg_eligible_venues = _load_leg_eligible_venues(uac_root)

    logger.info(
        "  VENUE_CATEGORY_MAP: %d venues, ENDPOINT_REGISTRY: %d venues, leg eligible: %d venues",
        len(venue_category_map),
        len(endpoint_registry_venues),
        len(leg_eligible_venues),
    )

    rows = build_venue_rows(venue_category_map, endpoint_registry_venues, leg_eligible_venues)
    report = render_report(rows)

    output_path = output_dir / "venue-coverage-report.md"
    with open(output_path, "w") as f:
        f.write(report)

    logger.info("Written → %s (%d venues)", output_path, len(rows))

    # Summary to stdout
    by_verdict: dict[str, int] = {}
    for row in rows:
        v = str(row["verdict"])
        by_verdict[v] = by_verdict.get(v, 0) + 1
    for verdict in _VERDICT_ORDER:
        logger.info("  %s: %d", verdict, by_verdict.get(verdict, 0))


if __name__ == "__main__":
    main()
