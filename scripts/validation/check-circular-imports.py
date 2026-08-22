#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
check-circular-imports.py

Detects circular imports in a Python package using AST analysis.
Does NOT execute code — pure static analysis.

Usage:
    python3 check-circular-imports.py <source_dir>
    python3 check-circular-imports.py instruments_service/

Exit code: 0 = clean, 1 = circular imports found.
"""

import ast
import logging
import sys
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


def get_package_imports(source_dir: Path) -> dict[str, set[str]]:
    """Build import graph: module -> set of internal modules it imports."""
    package = source_dir.name
    graph: dict[str, set[str]] = defaultdict(set)

    for py_file in source_dir.rglob("*.py"):
        # Derive module name from path (e.g. instruments_service.config.base)
        rel = py_file.relative_to(source_dir.parent)
        module = str(rel).replace("/", ".").removesuffix(".py")

        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError as e:
            logger.debug("Skipping item due to %s: %s", type(e).__name__, e)
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(package):
                        graph[module].add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith(package):
                    graph[module].add(node.module)
                elif node.level and node.level > 0:
                    # Relative import — resolve to absolute
                    parts = module.split(".")
                    base = ".".join(parts[: len(parts) - node.level])
                    target = f"{base}.{node.module}" if node.module else base
                    if target.startswith(package):
                        graph[module].add(target)

    return dict(graph)


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Find all strongly connected components with >1 node (= cycles) via DFS."""
    cycles: list[list[str]] = []
    visited: set[str] = set()
    rec_stack: list[str] = []
    path_set: set[str] = set()

    def dfs(node: str) -> bool:
        visited.add(node)
        rec_stack.append(node)
        path_set.add(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in path_set:
                # Found cycle — extract it
                cycle_start = rec_stack.index(neighbor)
                cycle = rec_stack[cycle_start:]
                # Deduplicate cycles (normalize by rotating to smallest element)
                normalized = tuple(sorted(range(len(cycle)), key=lambda i: cycle[i]))
                rotated = cycle[normalized[0] :] + cycle[: normalized[0]]
                if rotated not in [list(c) for c in cycles]:
                    cycles.append([*rotated, rotated[0]])  # show full loop
                return False

        rec_stack.pop()
        path_set.discard(node)
        return False

    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: check-circular-imports.py <source_dir>", file=sys.stderr)
        return 1

    source_dir = Path(sys.argv[1]).resolve()
    if not source_dir.is_dir():
        print(f"Error: {source_dir} is not a directory", file=sys.stderr)
        return 1

    graph = get_package_imports(source_dir)
    cycles = find_cycles(graph)

    if not cycles:
        print(f"✓ No circular imports in {source_dir.name}/")
        return 0

    print(f"✗ Circular imports found in {source_dir.name}/:")
    for cycle in cycles[:10]:  # Cap output at 10 cycles
        print("  " + " → ".join(cycle))
    if len(cycles) > 10:
        print(f"  ... and {len(cycles) - 10} more cycles")
    return 1


if __name__ == "__main__":
    sys.exit(main())
