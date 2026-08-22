#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""One-off helper: align workspace-manifest.json with dirs present at workspace root.

Run from anywhere:
  python3 unified-trading-pm/scripts/manifest/_align_workspace_manifest.py

Edits unified-trading-pm/workspace-manifest.json in place (backup recommended).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

PM_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"

# Repos that exist under WORKSPACE_ROOT (parent of unified-trading-pm) — 2026-04-20
PRESENT: frozenset[str] = frozenset(
    {
        "alerting-service",
        "batch-live-reconciliation-service",
        "client-reporting-api",
        "deployment-api",
        "deployment-service",
        "deployment-ui",
        "execution-service",
        "features-calendar-service",
        "features-commodity-service",
        "features-cross-instrument-service",
        "features-delta-one-service",
        "features-multi-timeframe-service",
        "features-onchain-service",
        "features-sports-service",
        "features-volatility-service",
        "fund-administration-service",
        "ibkr-gateway-infra",
        "instruments-service",
        "market-data-processing-service",
        "market-tick-data-service",
        "ml-inference-service",
        "ml-training-service",
        "pnl-attribution-service",
        "position-balance-monitor-service",
        "risk-and-exposure-service",
        "strategy-service",
        "system-integration-tests",
        "trading-agent-service",
        "unified-api-contracts",
        "unified-trading-api",
        "unified-trading-library",
        "unified-trading-pm",
        "unified-trading-system-ui",
        "user-management-ui",
    }
)

SKIP_ARCHIVE_STATUSES = frozenset({"deprecated", "deleted"})

NEW_TOPO_LEVELS: list[dict[str, object]] = [
    {
        "level": 0,
        "description": "Project management — manifest, templates, scripts, cursor rules.",
        "repos": ["unified-trading-pm"],
    },
    {
        "level": 1,
        "description": "Foundation contracts (Tier 0) — present clone set.",
        "repos": ["unified-api-contracts"],
    },
    {
        "level": 2,
        "description": "Trading library (Tier 1) — depends on UAC.",
        "repos": ["unified-trading-library"],
    },
    {
        "level": 3,
        "description": "Instrument registry — depends on UAC + UTL.",
        "repos": ["instruments-service"],
    },
    {
        "level": 4,
        "description": "Core services (batch + live) — parallel within tier.",
        "repos": sorted(
            [
                "alerting-service",
                "execution-service",
                "features-calendar-service",
                "features-commodity-service",
                "features-cross-instrument-service",
                "features-delta-one-service",
                "features-multi-timeframe-service",
                "features-onchain-service",
                "features-sports-service",
                "features-volatility-service",
                "fund-administration-service",
                "market-data-processing-service",
                "market-tick-data-service",
                "ml-inference-service",
                "ml-training-service",
                "pnl-attribution-service",
                "strategy-service",
                "trading-agent-service",
            ]
        ),
    },
    {
        "level": 5,
        "description": "Client-facing APIs and operational services.",
        "repos": sorted(
            [
                "client-reporting-api",
                "position-balance-monitor-service",
                "risk-and-exposure-service",
                "unified-trading-api",
            ]
        ),
    },
    {
        "level": 6,
        "description": "Deployment + batch reconciliation (orchestration).",
        "repos": sorted(
            [
                "batch-live-reconciliation-service",
                "deployment-api",
                "deployment-service",
            ]
        ),
    },
    {
        "level": 7,
        "description": "UI applications (TypeScript).",
        "repos": sorted(
            [
                "deployment-ui",
                "unified-trading-system-ui",
                "user-management-ui",
            ]
        ),
    },
    {
        "level": 8,
        "description": "IaC + post-deploy validation (last).",
        "repos": sorted(["ibkr-gateway-infra", "system-integration-tests"]),
    },
]

USER_MANAGEMENT_UI: dict[str, object] = {
    "type": "ui",
    "arch_tier": "ui",
    "doc_standard": "ui-canonical",
    "codex_sections": ["06-coding-standards"],
    "version": "0.2.0",
    "version_source": "package.json",
    "dependencies": [],
    # ci_status intentionally NOT seeded (WS-A Phase-3): Firestore is the SSOT and the hourly
    # ci-status-consolidator owns the manifest projection. A repo gets ci_status from its first
    # quality-gates-v2 run (absent == "unset" until then), never a static _align default.
    "coverage_pct": "N/A",
    "bypass_audit_path": "QUALITY_GATE_BYPASS_AUDIT.md",
    "testing_level": "unit",
    "skipped_gates": [],
    "status": "active",
    "github_url": "https://github.com/IggyIkenna/user-management-ui",
    "completion_path": "cefi",
    "semver_rules_ref": "ui",
    "sit_level": "standard",
    "semver_policy": "agent",
    "tier": 3,
    "role": "ui",
    "notes": "User lifecycle management UI (Next.js; Firebase hosting). Added to manifest 2026-04-20.",
    "tags": ["cross-domain", "im", "admin", "ui"],
}


def main() -> None:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    repos = data.get("repositories")
    if not isinstance(repos, dict):
        raise SystemExit("repositories missing or not an object")

    archived: list[str] = []
    for name, info in repos.items():
        if not isinstance(info, dict):
            continue
        if name in PRESENT:
            continue
        st = str(info.get("status", "active"))
        if st in SKIP_ARCHIVE_STATUSES:
            continue
        if st != "archived":
            info["status"] = "archived"
            archived.append(name)

    if "user-management-ui" not in repos:
        repos["user-management-ui"] = dict(USER_MANAGEMENT_UI)

    versions = data.get("versions")
    if isinstance(versions, dict) and "user-management-ui" not in versions:
        versions["user-management-ui"] = "0.2.0"

    topo = data.get("topologicalOrder")
    if isinstance(topo, dict):
        topo["description"] = (
            "Order for cascading quickmerge / run-all-setup.sh. Only repos present in the "
            "active workspace clone set (see repository status=active). Archived libraries "
            "not checked out locally are omitted from levels."
        )
        topo["levels"] = NEW_TOPO_LEVELS

    ws_infra = data.get("workspace_infrastructure")
    if isinstance(ws_infra, dict):
        ws_infra["setup_repos"] = ["unified-trading-pm"]

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    data["lastUpdated"] = now
    prev_notes = str(data.get("notes", ""))
    data["notes"] = (
        "Updated 2026-04-20: Workspace clone alignment — repositories not present under "
        "workspace root marked status=archived (rollout/run-all-setup no longer warn on "
        "missing dirs). topologicalOrder rebuilt for active repos only; added "
        "fund-administration-service + unified-trading-api + user-management-ui to "
        "topo levels; workspace_infrastructure.setup_repos=[unified-trading-pm] (codex "
        "optional clone). | " + prev_notes
    )

    MANIFEST_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH}")
    print(f"Archived (not in workspace): {len(archived)} repos")
    for n in sorted(archived)[:30]:
        print(f"  - {n}")
    if len(archived) > 30:
        print(f"  ... and {len(archived) - 30} more")


if __name__ == "__main__":
    main()
