# Epic: uac_master
# Lifecycle: permanent
# Delete-when: NA
"""Dead code audit for service repos.

Finds Python modules/files in service repos that exist but are never imported
or called by any code path reachable from the service's CLI or API entry points.

Uses subprocess `rg` (ripgrep) for all searching -- never Python `re` on file
contents -- to avoid catastrophic backtracking on large files.

Usage:
    python audit_dead_code.py --workspace-root PATH --output-dir PATH [--verbose]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Repos to SKIP -- libraries, PM, non-service repos.
SKIP_REPO_NAMES: set[str] = {
    "archive",
    "_archived-ui-reference",
    "unified-api-contracts",
    "unified-trading-library",
    "unified-market-interface",
    "unified-reference-data-interface",
    "unified-trading-pm",
    "system-integration-tests",
    "e2e-testing",
    "sports_playground",
}

# Prefixes / suffixes that indicate a non-service repo.
SKIP_PREFIXES: tuple[str, ...] = (".", "_")

# Sub-directories inside the package to exclude from the module list.
SKIP_SUBDIRS: set[str] = {
    "tests",
    "test",
    "scripts",
    "__pycache__",
    ".venv",
    "node_modules",
    "archive",
}

# rg glob excludes applied to every search.
RG_GLOB_EXCLUDES: list[str] = [
    "--glob",
    "!.venv*",
    "--glob",
    "!**/.venv*/**",
    "--glob",
    "!**/node_modules/**",
    "--glob",
    "!**/build/**",
    "--glob",
    "!**/dist/**",
    "--glob",
    "!**/__pycache__/**",
    "--glob",
    "!**/archive/**",
    "--glob",
    "!**/*.egg-info/**",
    "--glob",
    "!**/tests/**",
    "--glob",
    "!**/test/**",
    "--glob",
    "!**/scripts/**",
]

RG_TIMEOUT_SECONDS = 5

# Entry point files in priority order (relative to the package dir).
ENTRY_POINT_CANDIDATES: list[str] = [
    "cli/main.py",
    "__main__.py",
    "api/main.py",
    "api/app.py",
    "config.py",
    "__init__.py",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ModuleInfo:
    """Metadata for a single Python module file within a service."""

    file_path: Path  # Absolute path to .py file
    rel_path: str  # Relative to repo root (e.g. "execution_service/engine/core.py")
    dotted_module: str  # e.g. "execution_service.engine.core"
    short_name: str  # e.g. "core" (leaf module name)
    parent_dotted: str  # e.g. "execution_service.engine"
    is_init: bool  # True if __init__.py
    classification: str = "UNKNOWN"  # REACHABLE / ORPHAN_MODULE / DEAD_BRANCH


@dataclass
class ServiceAudit:
    """Audit results for a single service repo."""

    repo_name: str
    package_name: str
    total_modules: int = 0
    reachable: int = 0
    orphan_modules: list[str] = field(default_factory=list)
    dead_branch_modules: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Discover service repos
# ---------------------------------------------------------------------------


def _discover_service_repos(workspace_root: Path) -> list[tuple[str, str, Path]]:
    """Return (repo_name, package_name, repo_path) for each service/api repo."""
    repos: list[tuple[str, str, Path]] = []
    for entry in sorted(workspace_root.iterdir()):
        if not entry.is_dir():
            continue
        repo_name = entry.name
        if repo_name in SKIP_REPO_NAMES:
            continue
        if any(repo_name.startswith(p) for p in SKIP_PREFIXES):
            continue
        # Must have pyproject.toml (Python repo).
        if not (entry / "pyproject.toml").exists():
            continue
        # Must be a *-service or *-api repo.
        if not (repo_name.endswith("-service") or repo_name.endswith("-api")):
            continue
        # Must have a matching Python package directory.
        package_name = repo_name.replace("-", "_")
        if not (entry / package_name).is_dir():
            continue
        repos.append((repo_name, package_name, entry))
    return repos


# ---------------------------------------------------------------------------
# Discover modules within a service package
# ---------------------------------------------------------------------------


def _discover_modules(repo_path: Path, package_name: str) -> list[ModuleInfo]:
    """Find all .py files in the service package, excluding tests/scripts/__pycache__."""
    package_dir = repo_path / package_name
    modules: list[ModuleInfo] = []

    for py_file in sorted(package_dir.rglob("*.py")):
        # Skip excluded subdirectories.
        rel_to_pkg = py_file.relative_to(package_dir)
        parts = rel_to_pkg.parts
        if any(part in SKIP_SUBDIRS for part in parts):
            continue

        rel_path = str(py_file.relative_to(repo_path))
        # Build dotted module path.
        # e.g. execution_service/engine/core.py -> execution_service.engine.core
        #      execution_service/engine/__init__.py -> execution_service.engine
        is_init = py_file.name == "__init__.py"
        if is_init:
            dotted = ".".join([package_name, *parts[:-1]]) if len(parts) > 1 else package_name
        else:
            stem = py_file.stem
            dotted = ".".join([package_name, *parts[:-1], stem])

        # Parent dotted: the package containing this module.
        dotted_parts = dotted.split(".")
        parent_dotted = ".".join(dotted_parts[:-1]) if len(dotted_parts) > 1 else ""
        short_name = dotted_parts[-1] if not is_init else (dotted_parts[-1] if len(dotted_parts) > 1 else package_name)

        modules.append(
            ModuleInfo(
                file_path=py_file,
                rel_path=rel_path,
                dotted_module=dotted,
                short_name=short_name,
                parent_dotted=parent_dotted,
                is_init=is_init,
            )
        )

    return modules


# ---------------------------------------------------------------------------
# Identify entry points
# ---------------------------------------------------------------------------


def _find_entry_points(
    repo_path: Path,
    package_name: str,
    all_modules: list[ModuleInfo],
) -> list[ModuleInfo]:
    """Return the subset of modules that are entry points."""
    entry_points: list[ModuleInfo] = []
    module_by_rel: dict[str, ModuleInfo] = {m.rel_path: m for m in all_modules}

    for candidate in ENTRY_POINT_CANDIDATES:
        rel = f"{package_name}/{candidate}"
        if rel in module_by_rel:
            entry_points.append(module_by_rel[rel])

    return entry_points


# ---------------------------------------------------------------------------
# Import graph construction via ripgrep
# ---------------------------------------------------------------------------


def _run_rg(
    pattern: str,
    search_path: Path,
    extra_args: list[str] | None = None,
) -> str:
    """Run ripgrep with the given pattern in search_path. Return raw stdout."""
    cmd: list[str] = [
        "rg",
        "--type",
        "py",
        "--no-messages",
        "--no-heading",
        "--with-filename",
    ]
    cmd.extend(RG_GLOB_EXCLUDES)
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(pattern)
    cmd.append(str(search_path))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=RG_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        logger.warning("rg timed out for pattern (first 80 chars): %s", pattern[:80])
        return ""
    except FileNotFoundError:
        logger.error("ripgrep (rg) not found -- please install it")
        sys.exit(1)

    if result.returncode not in (0, 1):  # 1 = no matches
        logger.debug("rg returned %d for pattern: %s", result.returncode, pattern[:80])
    return result.stdout


def _run_rg_files_only(
    pattern: str,
    search_path: Path,
    extra_args: list[str] | None = None,
) -> list[str]:
    """Run ripgrep returning only matching file paths."""
    cmd: list[str] = [
        "rg",
        "--type",
        "py",
        "-l",
        "--no-messages",
    ]
    cmd.extend(RG_GLOB_EXCLUDES)
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(pattern)
    cmd.append(str(search_path))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=RG_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        logger.warning("rg timed out for pattern (first 80 chars): %s", pattern[:80])
        return []
    except FileNotFoundError:
        logger.error("ripgrep (rg) not found -- please install it")
        sys.exit(1)

    if result.returncode not in (0, 1):
        logger.debug("rg returned %d for pattern: %s", result.returncode, pattern[:80])
    return [line for line in result.stdout.strip().split("\n") if line]


def _build_import_edges(  # noqa: C901
    repo_path: Path,
    package_name: str,
    all_modules: list[ModuleInfo],
) -> dict[str, set[str]]:
    """Build a mapping: module_dotted -> set of module_dotted it imports.

    Uses batched rg calls to find all intra-package imports.
    Returns forward edges (importer -> imported).
    """
    package_dir = repo_path / package_name

    # Step 1: Find all import statements referencing the package, in one rg call.
    # Patterns:
    #   from package_name.X.Y import Z
    #   import package_name.X.Y
    #   from .X import Y  (relative imports)
    #   from ..X import Y (relative imports)
    absolute_pattern = f"^(from|import)\\s+{package_name}[.\\s]"
    relative_pattern = "^from\\s+\\.+"

    abs_output = _run_rg(absolute_pattern, package_dir)
    rel_output = _run_rg(relative_pattern, package_dir)

    # Step 2: Parse results into edges.
    # We need: which file (importer) references which module (imported).
    module_by_dotted: dict[str, ModuleInfo] = {m.dotted_module: m for m in all_modules}
    module_by_file: dict[str, ModuleInfo] = {str(m.file_path): m for m in all_modules}

    # Also build a mapping from dotted path to the __init__.py module for packages.
    # e.g. if we have execution_service.engine (an __init__.py), then importing
    # "from execution_service.engine import X" references that __init__.
    package_modules: dict[str, ModuleInfo] = {}
    for m in all_modules:
        if m.is_init:
            package_modules[m.dotted_module] = m

    edges: dict[str, set[str]] = {m.dotted_module: set() for m in all_modules}

    def _resolve_dotted(dotted: str) -> str | None:
        """Resolve a dotted import path to a known module dotted name."""
        # Direct match.
        if dotted in module_by_dotted:
            return dotted
        # Maybe it's a package (the __init__.py).
        if dotted in package_modules:
            return dotted
        # Maybe it's an attribute import: "from pkg.mod import func" where
        # pkg.mod is the module. Try stripping the last component.
        parent = ".".join(dotted.split(".")[:-1])
        if parent and parent in module_by_dotted:
            return parent
        if parent and parent in package_modules:
            return parent
        return None

    def _resolve_relative(
        importing_file: Path,
        dotted_suffix: str,
        dot_count: int,
    ) -> str | None:
        """Resolve a relative import to an absolute dotted module path."""
        # The importing file's package.
        importer_module = module_by_file.get(str(importing_file))
        if importer_module is None:
            return None

        # Start from the importer's package.
        base_parts = importer_module.dotted_module.split(".")
        # For a file (not __init__), the package is everything except the last part.
        # For __init__.py, the package IS the dotted_module.
        if not importer_module.is_init:
            base_parts = base_parts[:-1]

        # Each dot beyond the first goes up one level.
        levels_up = dot_count - 1
        if levels_up > 0:
            if levels_up >= len(base_parts):
                return None
            base_parts = base_parts[:-levels_up]

        target = ".".join(base_parts) + "." + dotted_suffix if dotted_suffix else ".".join(base_parts)

        return _resolve_dotted(target)

    def _process_output(output: str, is_relative: bool) -> None:
        """Parse rg output lines and populate edges."""
        for line in output.strip().split("\n"):
            if not line:
                continue
            # Format: filepath:content  (or filepath:lineno:content with -n)
            colon_idx = line.find(":")
            if colon_idx <= 0:
                continue
            file_path_str = line[:colon_idx]
            content = line[colon_idx + 1 :].strip()

            # Find the importer module.
            importer = module_by_file.get(file_path_str)
            if importer is None:
                # Try resolving relative to repo_path.
                try:
                    abs_path = str((repo_path / file_path_str).resolve())
                    importer = module_by_file.get(abs_path)
                except (OSError, ValueError):
                    pass
                if importer is None:
                    continue

            if is_relative:
                _process_relative_import(importer, content, Path(file_path_str))
            else:
                _process_absolute_import(importer, content)

    def _process_absolute_import(importer: ModuleInfo, content: str) -> None:
        """Parse an absolute import line and add edges."""
        # "from package_name.X.Y import Z, W"
        # "import package_name.X.Y"
        content = content.strip()
        if content.startswith("from "):
            # Extract the module path between "from" and "import".
            rest = content[5:]
            import_idx = rest.find(" import ")
            if import_idx < 0:
                return
            module_path = rest[:import_idx].strip()
            # The imported names (after "import").
            imported_names = rest[import_idx + 8 :].strip()

            # Try resolving the full dotted path first.
            resolved = _resolve_dotted(module_path)
            if resolved:
                edges[importer.dotted_module].add(resolved)

            # Also try: module_path.imported_name for each imported name.
            for name in imported_names.split(","):
                name = name.strip().split(" as ")[0].strip()  # handle "X as Y"
                if name and name != "*":
                    full = f"{module_path}.{name}"
                    resolved_name = _resolve_dotted(full)
                    if resolved_name:
                        edges[importer.dotted_module].add(resolved_name)
        elif content.startswith("import "):
            rest = content[7:].strip()
            for part in rest.split(","):
                mod = part.strip().split(" as ")[0].strip()
                resolved = _resolve_dotted(mod)
                if resolved:
                    edges[importer.dotted_module].add(resolved)

    def _process_relative_import(
        importer: ModuleInfo,
        content: str,
        file_path: Path,
    ) -> None:
        """Parse a relative import line and add edges."""
        content = content.strip()
        if not content.startswith("from "):
            return
        rest = content[5:]
        import_idx = rest.find(" import ")
        if import_idx < 0:
            return
        dot_part = rest[:import_idx].strip()
        imported_names = rest[import_idx + 8 :].strip()

        # Count leading dots.
        dot_count = 0
        for ch in dot_part:
            if ch == ".":
                dot_count += 1
            else:
                break
        suffix = dot_part[dot_count:]

        # Resolve the "from" part.
        resolved_base = _resolve_relative(importer.file_path, suffix, dot_count)
        if resolved_base:
            edges[importer.dotted_module].add(resolved_base)

        # Also try resolving each imported name as a submodule.
        for name in imported_names.split(","):
            name = name.strip().split(" as ")[0].strip()
            if name and name != "*":
                full_suffix = f"{suffix}.{name}" if suffix else name
                resolved_name = _resolve_relative(importer.file_path, full_suffix, dot_count)
                if resolved_name:
                    edges[importer.dotted_module].add(resolved_name)

    _process_output(abs_output, is_relative=False)
    _process_output(rel_output, is_relative=True)

    return edges


# ---------------------------------------------------------------------------
# Reachability analysis (BFS from entry points)
# ---------------------------------------------------------------------------


def _compute_reachable(
    entry_points: list[ModuleInfo],
    forward_edges: dict[str, set[str]],
) -> set[str]:
    """BFS from entry points through forward_edges. Return set of reachable dotted modules."""
    reachable: set[str] = set()
    queue: deque[str] = deque()

    for ep in entry_points:
        queue.append(ep.dotted_module)
        reachable.add(ep.dotted_module)

    while queue:
        current = queue.popleft()
        for neighbour in forward_edges.get(current, set()):
            if neighbour not in reachable:
                reachable.add(neighbour)
                queue.append(neighbour)

    return reachable


# ---------------------------------------------------------------------------
# Dead branch detection
# ---------------------------------------------------------------------------


def _classify_modules(
    all_modules: list[ModuleInfo],
    reachable: set[str],
    forward_edges: dict[str, set[str]],
) -> None:
    """Classify each module as REACHABLE, ORPHAN_MODULE, or DEAD_BRANCH.

    - REACHABLE: in the reachable set.
    - ORPHAN_MODULE: not reachable AND no other module in the repo imports it.
    - DEAD_BRANCH: not reachable BUT at least one other module imports it
      (that importer is itself unreachable -- transitively dead).
    """
    # Build reverse edges: who imports this module?
    reverse_edges: dict[str, set[str]] = {m.dotted_module: set() for m in all_modules}
    for source, targets in forward_edges.items():
        for target in targets:
            if target in reverse_edges:
                reverse_edges[target].add(source)

    for module in all_modules:
        dotted = module.dotted_module
        if dotted in reachable:
            module.classification = "REACHABLE"
        else:
            # Check if ANY module in the repo imports this one.
            importers = reverse_edges.get(dotted, set())
            if importers:
                module.classification = "DEAD_BRANCH"
            else:
                module.classification = "ORPHAN_MODULE"


# ---------------------------------------------------------------------------
# Fallback: string-based import search for modules with zero edges
# ---------------------------------------------------------------------------


def _fallback_string_search(
    repo_path: Path,
    package_name: str,
    module: ModuleInfo,
) -> bool:
    """Use rg to check if ANY file in the repo references this module.

    Catches cases the AST-style parser missed (dynamic imports, string refs, etc.).
    Returns True if the module is referenced by at least one other file.
    """
    package_dir = repo_path / package_name

    # Build search patterns for this module.
    # 1. Absolute dotted: "execution_service.engine.core"
    # 2. "from execution_service.engine import core"
    # 3. Relative: "from .engine import core" or "from . import core"
    patterns: list[str] = []

    if not module.is_init:
        # Pattern: the full dotted module name (escaped dots).
        escaped_dotted = module.dotted_module.replace(".", "\\.")
        patterns.append(escaped_dotted)

        # Pattern: "from <parent> import <short_name>"
        if module.parent_dotted:
            escaped_parent = module.parent_dotted.replace(".", "\\.")
            patterns.append(f"from\\s+{escaped_parent}\\s+import\\s+[^\\n]*\\b{module.short_name}\\b")

        # Relative import: "from .<something> import <short_name>" or "import <short_name>"
        # This is a loose match, but we filter out self-references below.
        patterns.append(f"\\bimport\\s+[^\\n]*\\b{module.short_name}\\b")
    else:
        # For __init__.py, the module IS the package.
        # Check if someone imports from this package.
        escaped_dotted = module.dotted_module.replace(".", "\\.")
        patterns.append(f"from\\s+{escaped_dotted}\\s+import")
        patterns.append(f"import\\s+{escaped_dotted}\\b")

    module_file_str = str(module.file_path)
    for pattern in patterns:
        matching_files = _run_rg_files_only(pattern, package_dir)
        # Exclude self-references.
        other_files = [f for f in matching_files if f != module_file_str]
        if other_files:
            return True

    return False


# ---------------------------------------------------------------------------
# Import-based verification (catches what ripgrep misses)
# ---------------------------------------------------------------------------


def _verify_reachability_via_import(
    repo_path: Path,
    package_name: str,
    entry_points: list[ModuleInfo],
    all_modules: list[ModuleInfo],
    reachable: set[str],
) -> None:
    """Use importlib to verify dead-classified modules are truly unreachable.

    Ripgrep-based graph construction misses transitive import chains, deferred
    imports inside functions, and conditional imports.  This step loads each
    entry point via importlib and checks which modules Python actually pulled
    in via sys.modules, promoting false-positive "dead" modules to REACHABLE.

    Runs in a subprocess to avoid polluting the parent process's sys.modules.
    Tolerates import failures (missing optional deps, etc.) gracefully.
    """
    # Build the set of dotted module names currently classified as dead.
    dead_dotted = {m.dotted_module for m in all_modules if m.classification in ("ORPHAN_MODULE", "DEAD_BRANCH")}
    if not dead_dotted:
        return

    # Build a small Python script that imports the entry points and reports
    # which of the "dead" modules ended up in sys.modules.
    entry_imports = [ep.dotted_module for ep in entry_points]
    script = (
        "import sys, json\n"
        "dead = set(json.loads(sys.argv[1]))\n"
        "entries = json.loads(sys.argv[2])\n"
        "for e in entries:\n"
        "    try:\n"
        "        __import__(e)\n"
        "    except Exception:\n"
        "        pass\n"
        "found = [m for m in dead if m in sys.modules]\n"
        "print(json.dumps(found))\n"
    )

    import json

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                json.dumps(sorted(dead_dotted)),
                json.dumps(entry_imports),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(repo_path),
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except subprocess.TimeoutExpired:
        logger.debug("  import verification timed out for %s", package_name)
        return

    if result.returncode != 0:
        logger.debug(
            "  import verification failed for %s (exit %d)",
            package_name,
            result.returncode,
        )
        return

    stdout = result.stdout.strip()
    if not stdout:
        return

    try:
        promoted: list[str] = json.loads(stdout)
    except json.JSONDecodeError:
        logger.debug("  import verification returned non-JSON for %s", package_name)
        return

    if promoted:
        promoted_set = set(promoted)
        reachable.update(promoted_set)
        for m in all_modules:
            if m.dotted_module in promoted_set and m.classification != "REACHABLE":
                logger.debug("  promoted %s → REACHABLE (import verification)", m.dotted_module)
                m.classification = "REACHABLE"


# ---------------------------------------------------------------------------
# Audit a single service
# ---------------------------------------------------------------------------


def _audit_service(
    repo_name: str,
    package_name: str,
    repo_path: Path,
    verbose: bool,
) -> ServiceAudit:
    """Run the dead code audit for a single service repo."""
    audit = ServiceAudit(repo_name=repo_name, package_name=package_name)

    # 1. Discover all modules.
    all_modules = _discover_modules(repo_path, package_name)
    audit.total_modules = len(all_modules)
    if not all_modules:
        logger.debug("  No modules found in %s", repo_name)
        return audit

    # 2. Identify entry points.
    entry_points = _find_entry_points(repo_path, package_name, all_modules)
    audit.entry_points = [ep.rel_path for ep in entry_points]
    if not entry_points:
        logger.warning("  No entry points found in %s -- marking all as ORPHAN", repo_name)
        for m in all_modules:
            m.classification = "ORPHAN_MODULE"
            audit.orphan_modules.append(m.rel_path)
        return audit

    # 3. Build import graph.
    forward_edges = _build_import_edges(repo_path, package_name, all_modules)

    if verbose:
        edge_count = sum(len(v) for v in forward_edges.values())
        logger.debug("  %s: %d modules, %d edges", repo_name, len(all_modules), edge_count)

    # 4. Compute reachability from entry points.
    reachable = _compute_reachable(entry_points, forward_edges)

    # 5. Classify modules.
    _classify_modules(all_modules, reachable, forward_edges)

    # 6. For ORPHAN_MODULE candidates, do a fallback string search.
    #    If the fallback finds references, promote to DEAD_BRANCH (imported
    #    but still not reachable from entry points).
    for module in all_modules:
        if (
            module.classification == "ORPHAN_MODULE"
            and not module.is_init
            and _fallback_string_search(repo_path, package_name, module)
        ):
            module.classification = "DEAD_BRANCH"

    # 6b. Import-based verification: attempt to load entry points and check
    #     which modules Python actually imports (catches transitive chains,
    #     deferred imports, and dynamic references that ripgrep misses).
    _verify_reachability_via_import(repo_path, package_name, entry_points, all_modules, reachable)

    # 7. Collect results.
    for module in all_modules:
        if module.classification == "REACHABLE":
            audit.reachable += 1
        elif module.classification == "ORPHAN_MODULE":
            audit.orphan_modules.append(module.rel_path)
        elif module.classification == "DEAD_BRANCH":
            audit.dead_branch_modules.append(module.rel_path)

    audit.orphan_modules.sort()
    audit.dead_branch_modules.sort()

    return audit


# ---------------------------------------------------------------------------
# Main audit orchestration
# ---------------------------------------------------------------------------


def run_audit(
    workspace_root: Path,
    output_dir: Path,
    verbose: bool = False,
) -> None:
    """Run the dead code audit across all service/api repos."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    start_time = time.time()

    # 1. Discover service repos.
    repos = _discover_service_repos(workspace_root)
    logger.info("Found %d service/api repos to audit", len(repos))

    # 2. Audit each repo.
    audits: dict[str, ServiceAudit] = {}
    for repo_name, package_name, repo_path in repos:
        logger.info("Auditing %s ...", repo_name)
        audit = _audit_service(repo_name, package_name, repo_path, verbose)
        audits[repo_name] = audit

        orphan_count = len(audit.orphan_modules)
        dead_count = len(audit.dead_branch_modules)
        if orphan_count > 0 or dead_count > 0:
            logger.info(
                "  %s: %d modules, %d reachable, %d orphan, %d dead-branch",
                repo_name,
                audit.total_modules,
                audit.reachable,
                orphan_count,
                dead_count,
            )
        else:
            logger.info(
                "  %s: %d modules, all reachable",
                repo_name,
                audit.total_modules,
            )

    elapsed = time.time() - start_time

    # 3. Compute summary.
    total_modules = sum(a.total_modules for a in audits.values())
    total_reachable = sum(a.reachable for a in audits.values())
    total_orphan = sum(len(a.orphan_modules) for a in audits.values())
    total_dead_branch = sum(len(a.dead_branch_modules) for a in audits.values())

    summary = {
        "total_modules": total_modules,
        "reachable": total_reachable,
        "orphan": total_orphan,
        "dead_branch": total_dead_branch,
        "services_audited": len(audits),
        "elapsed_seconds": round(elapsed, 1),
    }

    # 4. Build JSON report.
    services_json: dict[str, dict[str, int | list[str]]] = {}
    for repo_name, audit in sorted(audits.items()):
        entry: dict[str, int | list[str]] = {
            "total": audit.total_modules,
            "reachable": audit.reachable,
        }
        if audit.orphan_modules:
            entry["orphan_modules"] = audit.orphan_modules
        if audit.dead_branch_modules:
            entry["dead_branch_modules"] = audit.dead_branch_modules
        if audit.entry_points:
            entry["entry_points"] = audit.entry_points
        services_json[repo_name] = entry

    json_report = {
        "summary": summary,
        "services": services_json,
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "dead_code_audit.json"
    with open(json_path, "w") as f:
        json.dump(json_report, f, indent=2)
    logger.info("JSON report: %s", json_path)

    # 5. Build human-readable text report.
    text_lines: list[str] = []
    text_lines.append("=" * 72)
    text_lines.append("Dead Code Audit Report")
    text_lines.append("=" * 72)
    text_lines.append("")
    text_lines.append(f"Workspace: {workspace_root}")
    text_lines.append(f"Elapsed:   {elapsed:.1f}s")
    text_lines.append("")
    text_lines.append("SUMMARY")
    text_lines.append("-" * 40)
    text_lines.append(f"  Services audited:  {summary['services_audited']:>5}")
    text_lines.append(f"  Total modules:     {summary['total_modules']:>5}")
    text_lines.append(f"  Reachable:         {summary['reachable']:>5}")
    text_lines.append(f"  Orphan modules:    {summary['orphan']:>5}")
    text_lines.append(f"  Dead branches:     {summary['dead_branch']:>5}")
    text_lines.append("")

    # Services with issues.
    services_with_issues = [
        (name, audit) for name, audit in sorted(audits.items()) if audit.orphan_modules or audit.dead_branch_modules
    ]

    if services_with_issues:
        text_lines.append("SERVICES WITH DEAD CODE")
        text_lines.append("-" * 40)
        for repo_name, audit in services_with_issues:
            text_lines.append("")
            text_lines.append(f"  {repo_name} ({audit.total_modules} modules, {audit.reachable} reachable)")
            if audit.entry_points:
                text_lines.append(f"    Entry points: {', '.join(audit.entry_points)}")
            if audit.orphan_modules:
                text_lines.append(f"    ORPHAN_MODULE ({len(audit.orphan_modules)}):")
                for mod in audit.orphan_modules:
                    text_lines.append(f"      - {mod}")
            if audit.dead_branch_modules:
                text_lines.append(f"    DEAD_BRANCH ({len(audit.dead_branch_modules)}):")
                for mod in audit.dead_branch_modules:
                    text_lines.append(f"      - {mod}")
        text_lines.append("")

    # Clean services.
    clean_services = [
        (name, audit)
        for name, audit in sorted(audits.items())
        if not audit.orphan_modules and not audit.dead_branch_modules
    ]
    if clean_services:
        text_lines.append("CLEAN SERVICES (no dead code)")
        text_lines.append("-" * 40)
        for repo_name, audit in clean_services:
            text_lines.append(f"  {repo_name}: {audit.total_modules} modules, all reachable")
        text_lines.append("")

    text_lines.append("=" * 72)
    text_lines.append("END OF REPORT")
    text_lines.append("=" * 72)

    text_path = output_dir / "dead_code_audit.txt"
    with open(text_path, "w") as f:
        f.write("\n".join(text_lines) + "\n")
    logger.info("Text report: %s", text_path)

    # 6. Print summary to stdout.
    print()
    print(f"Dead code audit complete in {elapsed:.1f}s")
    print(f"  Services audited:  {summary['services_audited']}")
    print(f"  Total modules:     {summary['total_modules']}")
    print(f"  Reachable:         {summary['reachable']}")
    print(f"  Orphan modules:    {summary['orphan']}")
    print(f"  Dead branches:     {summary['dead_branch']}")
    print(f"\nReports written to: {output_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dead code audit: find unreachable Python modules in service repos.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        required=True,
        help="Path to the multi-repo workspace root.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to write JSON and text reports.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    args = parser.parse_args()

    workspace_root: Path = args.workspace_root.resolve()
    output_dir: Path = args.output_dir.resolve()

    if not workspace_root.is_dir():
        logger.error("Workspace root does not exist: %s", workspace_root)
        sys.exit(1)

    # Verify rg is available.
    try:
        subprocess.run(["rg", "--version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        logger.error("ripgrep (rg) is not installed -- please install it first")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        pass  # rg exists but was slow -- fine

    run_audit(workspace_root, output_dir, verbose=args.verbose)


if __name__ == "__main__":
    main()
