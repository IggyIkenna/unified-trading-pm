#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""validate-manifest-dag.py — Detect dependency cycles in workspace-manifest.json.

Usage:
    python3 scripts/validate-manifest-dag.py [--manifest PATH] [--triggering-repo REPO]

Exit codes:
    0  — No cycles detected (safe to dispatch)
    1  — Cycle(s) detected (ABORT cascade, alert sent)
    2  — Manifest not found or parse error

Reads workspace-manifest.json from the current directory (or --manifest path).
If --triggering-repo is provided, only checks the subgraph reachable from that repo.
Otherwise checks the full DAG.

Telegram alert:
    If TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set, sends an alert on cycle detection.
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from typing import cast


def load_manifest(path: str) -> dict[str, object]:
    with open(path, encoding="utf-8") as f:
        return cast(dict[str, object], json.load(f))


def _get_dep_name(dep: object) -> str | None:
    """Extract dependency name from dep (dict with 'name' key or plain str)."""
    if isinstance(dep, dict):
        name = dep.get("name")
        return str(name) if name is not None else None
    if isinstance(dep, str):
        return dep
    return None


def build_adj(manifest: dict[str, object]) -> dict[str, list[str]]:
    """Build adjacency list: repo -> list of direct dependents."""
    adj: dict[str, list[str]] = {}
    raw_repos = manifest.get("repositories")
    repos = cast(dict[str, object], raw_repos) if isinstance(raw_repos, dict) else {}
    for repo_name in repos:
        adj[repo_name] = []

    for repo_name, data in repos.items():
        repo_data = cast(dict[str, object], data)
        raw_deps = repo_data.get("dependencies")
        deps = cast(list[object], raw_deps) if isinstance(raw_deps, list) else []
        for dep in deps:
            dep_name = _get_dep_name(dep)
            if dep_name and dep_name in adj:
                # dep_name → repo_name (repo_name depends ON dep_name)
                # Forward edge: dep_name is a dependency of repo_name
                # For cycle detection we walk: if A depends on B depends on A => cycle
                # Build: dep_name -> repo_name (dep_name is needed by repo_name)
                adj[dep_name].append(repo_name)

    return adj


def find_cycles(adj: dict[str, list[str]], start_nodes: list[str] | None = None) -> list[list[str]]:
    """DFS cycle detection. Returns list of cycles found (each cycle is a list of node names)."""
    WHITE, GRAY, BLACK = 0, 1, 2  # noqa: N806
    color: dict[str, int] = dict.fromkeys(adj, WHITE)
    path: list[str] = []
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        color[node] = GRAY
        path.append(node)
        for neighbor in adj.get(node, []):
            if color[neighbor] == GRAY:
                # Found a cycle — extract it from the path
                idx = path.index(neighbor)
                cycle = [*path[idx:], neighbor]
                cycles.append(cycle)
            elif color[neighbor] == WHITE:
                dfs(neighbor)
        path.pop()
        color[node] = BLACK

    nodes_to_check = start_nodes if start_nodes else list(adj.keys())
    for node in nodes_to_check:
        if color.get(node, WHITE) == WHITE:
            dfs(node)

    return cycles


def send_telegram_alert(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    try:
        data = urllib.parse.urlencode(
            {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
            }
        ).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data,
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)  # nosec B310 — intentional: Telegram API over HTTPS
    except (OSError, ValueError):
        pass  # TG failure must never block; documented in QUALITY_GATE_BYPASS_AUDIT §2.9


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate manifest DAG for cycles")
    parser.add_argument("--manifest", default="workspace-manifest.json", type=str)
    parser.add_argument(
        "--triggering-repo", default=None, type=str, help="Only validate subgraph reachable from this repo"
    )
    args = parser.parse_args()

    manifest_path: str = cast(str, args.manifest)
    triggering_repo: str | None = cast(str | None, args.triggering_repo)

    if not os.path.exists(manifest_path):
        print(f"ERROR: Manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    try:
        manifest = load_manifest(manifest_path)
    except json.JSONDecodeError as e:
        print(f"ERROR: Manifest JSON parse error: {e}", file=sys.stderr)
        return 2

    adj = build_adj(manifest)
    print(f"DAG: {len(adj)} repos loaded", file=sys.stderr)

    start_nodes: list[str] | None = None
    if triggering_repo:
        if triggering_repo not in adj:
            print(f"WARNING: {triggering_repo} not in manifest — skipping cycle check", file=sys.stderr)
            return 0
        # Check subgraph: the triggering repo and everything downstream
        start_nodes = [triggering_repo]

    cycles = find_cycles(adj, start_nodes)

    if not cycles:
        print("✅ No dependency cycles detected. Cascade safe to proceed.", file=sys.stderr)
        return 0

    # Format cycle report
    cycle_strs = [" → ".join(c) for c in cycles]
    report = "\n".join(f"  • {c}" for c in cycle_strs)

    print(f"❌ DEPENDENCY CYCLE(S) DETECTED — cascade aborted!\n{report}", file=sys.stderr)

    tg_msg = (
        "⚠️ *Dependency Cycle Detected*\n"
        "Cascade aborted. Check `workspace-manifest.json`.\n"
        "Cycles found:\n" + "\n".join(f"• `{c}`" for c in cycle_strs)
    )
    if triggering_repo:
        tg_msg = f"Triggering repo: `{triggering_repo}`\n" + tg_msg

    send_telegram_alert(tg_msg)
    return 1


if __name__ == "__main__":
    sys.exit(main())
