#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Remove repository entries that are no longer part of the workspace (libraries retired).

Run from workspace root:
  python3 unified-trading-pm/scripts/manifest/prune_removed_repositories.py

Deletes keys from ``repositories`` and ``versions``, strips references from
``dependencies``, ``internal_dependencies``, ``runtime_clients``, and
``serves_ui`` / cross-refs where applicable. Re-run ``generate_workspace_dag.py`` after.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

PM_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"

# Retired / not cloned — removed from active manifest (2026-04-20)
REMOVED: frozenset[str] = frozenset(
    {
        "execution-algo-library",
        "matching-engine-library",
        "unified-cloud-interface",
        "unified-config-interface",
        "unified-defi-execution-interface",
        "unified-domain-client",
        "unified-feature-calculator-library",
        "unified-feature-orchestration-library",
        "unified-features-interface",
        "unified-internal-contracts",
        "unified-market-interface",
        "unified-ml-interface",
        "unified-position-interface",
        "unified-reference-data-interface",
        "unified-sports-execution-interface",
        "unified-sports-reference-interface",
        "unified-trade-execution-interface",
        "unified-trading-codex",
        # Added 2026-06-19: orphans found as live Cloud Build triggers/links but absent from BOTH the
        # live 25-repo set AND this list (pre-25-era debris; their zombie triggers + links were deleted).
        "unified-cloud-services",
        "unified-domain-services",
        "unified-events-interface",
        "unified-order-interface",
        "ml-training-ui",
        "market-tick-data-handler",
        "live-health-monitor-ui",
        "execution-results-api",
        "market-data-api",
    }
)


def _filter_dep_list(deps: object) -> list[dict[str, object]] | None:
    if not isinstance(deps, list):
        return None
    out: list[dict[str, object]] = []
    for d in deps:
        if not isinstance(d, dict):
            continue
        name = d.get("name")
        if isinstance(name, str) and name in REMOVED:
            continue
        out.append(d)
    return out


def _filter_str_list(val: object) -> list[str] | None:
    if not isinstance(val, list):
        return None
    out = [x for x in val if isinstance(x, str) and x not in REMOVED]
    return out


def _first_token_pkg(line: str) -> str:
    return line.split()[0].split("(")[0].rstrip(",")


def scrub_publishing_order(data: dict[str, object]) -> None:
    po = data.get("publishingOrder")
    if not isinstance(po, dict):
        return
    steps = po.get("steps")
    if not isinstance(steps, list):
        return
    new_steps: list[dict[str, object]] = []
    for st in steps:
        if not isinstance(st, dict):
            continue
        pkgs = st.get("packages")
        if not isinstance(pkgs, list):
            new_steps.append(st)
            continue
        filtered: list[str] = []
        for p in pkgs:
            if p == "All services" or (isinstance(p, str) and p not in REMOVED):
                filtered.append(p)
        if not filtered:
            continue
        out = dict(st)
        out["packages"] = filtered
        new_steps.append(out)
    po["steps"] = new_steps


def scrub_completion_paths(data: dict[str, object]) -> None:
    cp = data.get("completion_paths")
    if not isinstance(cp, dict):
        return
    for _key, block in cp.items():
        if _key.startswith("_") or not isinstance(block, dict):
            continue
        for field in ("required_libraries", "additional_libraries"):
            lst = block.get(field)
            if not isinstance(lst, list):
                continue
            new_lst: list[str] = []
            for line in lst:
                if not isinstance(line, str):
                    new_lst.append(line)
                    continue
                pkg = _first_token_pkg(line)
                if pkg in REMOVED:
                    continue
                new_lst.append(line)
            block[field] = new_lst


def scrub_tier_rules(data: dict[str, object]) -> None:
    tr = data.get("tier_rules")
    if not isinstance(tr, dict):
        return
    updates: dict[str, str] = {
        "0": "Pure leaf — contract packages (e.g. UAC). No inter-library deps.",
        "1": "Trading library tier (UTL) — imports Tier 0 contracts only.",
        "2": "Reserved — legacy split interface repos removed; consume cloud/config via UTL.",
        "3": "Reserved — legacy domain-client split removed; use UTL storage helpers.",
        "infrastructure": "Infrastructure repos — IaC (Terraform), scripts. Python repos use minimal deps.",
        "devops": "DevOps/deployment — deployment-service, deployment-api. Imports UTL + UAC.",
        "api": "API gateway services (FastAPI) — HTTP boundary; deps: UTL + UAC.",
    }
    for k, desc in updates.items():
        block = tr.get(k)
        if isinstance(block, dict):
            block["description"] = desc


def main() -> None:
    data: dict[str, object] = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    repos = data.get("repositories")
    if not isinstance(repos, dict):
        raise SystemExit("repositories missing")

    for key in REMOVED:
        repos.pop(key, None)

    versions = data.get("versions")
    if isinstance(versions, dict):
        for key in REMOVED:
            versions.pop(key, None)

    for info in list(repos.values()):
        if not isinstance(info, dict):
            continue
        fd = _filter_dep_list(info.get("dependencies"))
        if fd is not None:
            info["dependencies"] = fd
        il = _filter_str_list(info.get("internal_dependencies"))
        if il is not None:
            info["internal_dependencies"] = il
        rl = _filter_str_list(info.get("runtime_clients"))
        if rl is not None:
            info["runtime_clients"] = rl
        su = _filter_str_list(info.get("serves_ui"))
        if su is not None:
            info["serves_ui"] = su
        ps = info.get("proxies_service")
        if isinstance(ps, str) and ps in REMOVED:
            del info["proxies_service"]
        if info.get("internal_dependencies") == []:
            del info["internal_dependencies"]
        if info.get("runtime_clients") == []:
            del info["runtime_clients"]

    scrub_publishing_order(data)
    scrub_completion_paths(data)
    scrub_tier_rules(data)

    data["lastUpdated"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    note = (
        "Updated 2026-04-20: Pruned retired library repos from manifest (no longer cloned); "
        "stripped dependency pointers; execution-service uses UTL cloud facades only. | "
    )
    prev = str(data.get("notes", ""))
    data["notes"] = note + prev

    MANIFEST_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH}")
    print(f"Removed {len(REMOVED)} repository keys (if present) and scrubbed references.")


if __name__ == "__main__":
    main()
