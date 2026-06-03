#!/usr/bin/env python3
"""Auto-populate usage tags on workspace-manifest.json repos.

Infers tags from existing fields (type, arch_tier, tier, completion_path,
cluster, name patterns) without manual curation.

Tag categories:
  - capability: data-ingestion, execution, feature-computation, ml-training,
                ml-inference, risk, pnl, monitoring, alerting, onboarding,
                analytics, config, events, contracts
  - domain:     cefi, tradfi, defi, sports, prediction, cross-domain
  - criticality: critical (T0-T1), important (T2), standard (T3+)

Usage:
    python auto-populate-tags.py                   # dry-run (prints diff)
    python auto-populate-tags.py --write           # writes manifest in-place
    python auto-populate-tags.py --write --verify   # writes + prints summary
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PM_ROOT = SCRIPT_DIR.parent.parent
MANIFEST = PM_ROOT / "workspace-manifest.json"


# ---------------------------------------------------------------------------
# Tag inference rules
# ---------------------------------------------------------------------------


def infer_tags(name: str, info: dict[str, object]) -> list[str]:  # noqa: C901
    """Infer tags for a repo based on its manifest fields and name."""
    tags: set[str] = set()

    repo_type = str(info.get("type", ""))
    tier = info.get("tier")
    completion_path = str(info.get("completion_path", ""))
    _cluster = str(info.get("cluster", ""))
    name_lower = name.lower()

    # --- Criticality ---
    if isinstance(tier, int):
        if tier <= 1:
            tags.add("critical")
        elif tier == 2:
            tags.add("important")
        else:
            tags.add("standard")
    elif repo_type in ("devops", "infrastructure", "test-harness"):
        tags.add("standard")
    else:
        tags.add("standard")

    # --- Domain ---
    domain_map: dict[str, str] = {
        "cefi": "cefi",
        "tradfi": "tradfi",
        "defi": "defi",
        "sports": "sports",
        "ml": "cross-domain",
        "core": "cross-domain",
        "infrastructure": "cross-domain",
        "all": "cross-domain",
    }
    mapped_domain = domain_map.get(completion_path, "")
    if mapped_domain:
        tags.add(mapped_domain)

    # Name-based domain overrides / additions
    if "defi" in name_lower:
        tags.discard("cefi")
        tags.add("defi")
    if "sports" in name_lower:
        tags.discard("cefi")
        tags.add("sports")
    if "tradfi" in name_lower or "ibkr" in name_lower:
        tags.discard("cefi")
        tags.add("tradfi")
    if "onchain" in name_lower:
        tags.add("defi")

    # --- Capability ---

    # Contracts / schemas
    if "contracts" in name_lower or "internal-contracts" in name_lower:
        tags.add("contracts")

    # Events
    if "events" in name_lower:
        tags.add("events")

    # Config
    if "config" in name_lower:
        tags.add("config")

    # Cloud / infrastructure
    if "cloud" in name_lower:
        tags.add("config")

    # Execution
    if "execution" in name_lower or "trade-execution" in name_lower:
        tags.add("execution")
    if "matching-engine" in name_lower or "algo" in name_lower:
        tags.add("execution")

    # Feature computation
    if "feature" in name_lower:
        tags.add("feature-computation")

    # ML
    if "ml" in name_lower and "training" in name_lower:
        tags.add("ml-training")
    if "ml" in name_lower and "inference" in name_lower:
        tags.add("ml-inference")
    if "ml-interface" in name_lower:
        tags.add("ml-training")
        tags.add("ml-inference")

    # Market data / data ingestion
    if "market" in name_lower and ("data" in name_lower or "tick" in name_lower):
        tags.add("data-ingestion")
    if "instruments" in name_lower:
        tags.add("data-ingestion")
    if "reference-data" in name_lower:
        tags.add("data-ingestion")

    # Risk
    if "risk" in name_lower or "exposure" in name_lower:
        tags.add("risk")

    # PnL
    if "pnl" in name_lower or "attribution" in name_lower:
        tags.add("pnl")

    # Position
    if "position" in name_lower or "balance" in name_lower:
        tags.add("risk")

    # Monitoring / alerting
    if "alerting" in name_lower:
        tags.add("alerting")
    if "monitor" in name_lower or "health" in name_lower:
        tags.add("monitoring")

    # Analytics
    if "analytics" in name_lower:
        tags.add("analytics")

    # Onboarding
    if "onboarding" in name_lower:
        tags.add("onboarding")

    # Deployment
    if "deployment" in name_lower:
        tags.add("deployment")

    # Strategy
    if "strategy" in name_lower:
        tags.add("execution")

    # Reporting
    if "reporting" in name_lower or "client-reporting" in name_lower:
        tags.add("analytics")

    # Settlement
    if "settlement" in name_lower:
        tags.add("execution")

    # Reconciliation
    if "reconciliation" in name_lower:
        tags.add("analytics")

    # Batch / audit
    if "audit" in name_lower:
        tags.add("monitoring")
    if "batch" in name_lower:
        tags.add("analytics")

    # Trading agent
    if "trading-agent" in name_lower:
        tags.add("execution")

    # Logs
    if "logs" in name_lower or "dashboard" in name_lower:
        tags.add("monitoring")

    # Domain client
    if "domain-client" in name_lower:
        tags.add("config")

    # UI kit / auth
    if "ui-kit" in name_lower or "ui-auth" in name_lower:
        tags.add("onboarding")

    # Admin UI
    if "admin" in name_lower:
        tags.add("config")

    # PM (devops/docs). unified-trading-codex is ARCHIVED (folded into PM at codex/) — not a live repo.
    if name_lower == "unified-trading-pm":
        tags.add("config")

    # System integration tests
    if "system-integration" in name_lower or "test-harness" in repo_type:
        tags.add("monitoring")

    # Trading library (foundation)
    if name_lower == "unified-trading-library":
        tags.add("contracts")

    return sorted(tags)


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------


def populate_tags(
    manifest_path: Path | None = None,
    write: bool = False,
) -> dict[str, list[str]]:
    """Compute tags for all repos. Optionally write to manifest.

    Returns:
        Dict of repo name -> tags list.
    """
    src = manifest_path or MANIFEST

    with open(src) as f:
        data = json.load(f)

    repos: dict[str, object] = data.get("repositories", {})  # noqa: qg-empty-fallback
    all_tags: dict[str, list[str]] = {}
    changed = 0

    for name in sorted(repos.keys()):
        info = repos[name]
        if not isinstance(info, dict):
            continue

        tags = infer_tags(name, info)
        all_tags[name] = tags

        existing = info.get("tags", [])  # noqa: qg-empty-fallback
        if not isinstance(existing, list):
            existing = []

        if sorted(existing) != tags:
            changed += 1
            info["tags"] = tags

    if write:
        # Write with same formatting (2-space indent, sorted keys at top level)
        with open(src, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Written: {src}")
        print(f"  Repos updated: {changed}/{len(all_tags)}")
    else:
        print(f"Dry run — {changed}/{len(all_tags)} repos would be updated.")
        print(f"  Run with --write to apply changes to {src}")

    return all_tags


def print_summary(all_tags: dict[str, list[str]]) -> None:
    """Print tag distribution summary."""
    tag_counts: dict[str, int] = {}
    for tags in all_tags.values():
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    print("\nTag distribution:")
    print(f"  {'Tag':<24} {'Count':>5}")
    print(f"  {'-' * 24} {'-' * 5}")
    for tag, count in sorted(tag_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {tag:<24} {count:>5}")

    print(f"\n  Total repos: {len(all_tags)}")
    print(f"  Total unique tags: {len(tag_counts)}")

    # Show per-category breakdown
    criticality_tags = {"critical", "important", "standard"}
    domain_tags = {"cefi", "tradfi", "defi", "sports", "cross-domain"}

    crit_counts = {t: tag_counts.get(t, 0) for t in sorted(criticality_tags)}
    domain_counts = {t: tag_counts.get(t, 0) for t in sorted(domain_tags)}

    print(f"\n  Criticality: {crit_counts}")
    print(f"  Domain: {domain_counts}")


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Auto-populate tags on workspace-manifest.json repos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write tags to manifest (default: dry-run)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Print tag distribution summary",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help=f"Path to workspace-manifest.json (default: {MANIFEST})",
    )

    args = parser.parse_args()
    all_tags = populate_tags(args.manifest, write=args.write)

    if args.verify or not args.write:
        print_summary(all_tags)


if __name__ == "__main__":
    main()
