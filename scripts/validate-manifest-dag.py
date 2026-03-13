#!/usr/bin/env python3
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


def load_manifest(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_adj(manifest: dict) -> dict[str, list[str]]:
    """Build adjacency list: repo -> list of direct dependents."""
    adj: dict[str, list[str]] = {}
    repos = manifest.get("repositories", {})
    for repo_name in repos:
        adj[repo_name] = []

    for repo_name, data in repos.items():
        for dep in data.get("dependencies", []):
            dep_name = dep.get("name") if isinstance(dep, dict) else dep
            if dep_name and dep_name in adj:
                # dep_name → repo_name (repo_name depends ON dep_name)
                # Forward edge: dep_name is a dependency of repo_name
                # For cycle detection we walk: if A depends on B depends on A => cycle
                # Build: dep_name -> repo_name (dep_name is needed by repo_name)
                adj[dep_name].append(repo_name)

    return adj


def find_cycles(adj: dict[str, list[str]], start_nodes: list[str] | None = None) -> list[list[str]]:
    """DFS cycle detection. Returns list of cycles found (each cycle is a list of node names)."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {node: WHITE for node in adj}
    path: list[str] = []
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        color[node] = GRAY
        path.append(node)
        for neighbor in adj.get(node, []):
            if color[neighbor] == GRAY:
                # Found a cycle — extract it from the path
                idx = path.index(neighbor)
                cycle = path[idx:] + [neighbor]
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
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
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
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass  # TG failure must never block the script


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate manifest DAG for cycles")
    parser.add_argument("--manifest", default="workspace-manifest.json")
    parser.add_argument("--triggering-repo", default=None, help="Only validate subgraph reachable from this repo")
    args = parser.parse_args()

    if not os.path.exists(args.manifest):
        print(f"ERROR: Manifest not found: {args.manifest}", file=sys.stderr)
        return 2

    try:
        manifest = load_manifest(args.manifest)
    except json.JSONDecodeError as e:
        print(f"ERROR: Manifest JSON parse error: {e}", file=sys.stderr)
        return 2

    adj = build_adj(manifest)
    print(f"DAG: {len(adj)} repos loaded", file=sys.stderr)

    start_nodes: list[str] | None = None
    if args.triggering_repo:
        if args.triggering_repo not in adj:
            print(f"WARNING: {args.triggering_repo} not in manifest — skipping cycle check", file=sys.stderr)
            return 0
        # Check subgraph: the triggering repo and everything downstream
        start_nodes = [args.triggering_repo]

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
    if args.triggering_repo:
        tg_msg = f"Triggering repo: `{args.triggering_repo}`\n" + tg_msg

    send_telegram_alert(tg_msg)
    return 1


if __name__ == "__main__":
    sys.exit(main())
