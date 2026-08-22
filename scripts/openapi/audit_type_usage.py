# Epic: uac_master
# Lifecycle: permanent
# Delete-when: NA
"""Deep usage audit of UAC/UIC types across the workspace.

Scans all service repos for actual usage of types exported from
unified-api-contracts (UAC top-level) and unified-api-contracts.internal (UIC).

Classifies each type as ALIVE, TEST_ONLY, IMPORT_CHAIN_ONLY, or DEAD.

Uses subprocess `rg` (ripgrep) for all searching — never Python `re` on file
contents — to avoid catastrophic backtracking on large files.

Usage:
    python audit_type_usage.py --workspace-root PATH --output-dir PATH [--verbose]
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Directories at the workspace root to skip when searching for consumers.
SKIP_DIRS: set[str] = {
    "archive",
    ".venv-workspace",
    ".venv",
    ".cursor",
    ".claude",
    "e2e-testing",
    "sports_playground",
    "node_modules",
    "unified-api-contracts",  # UAC itself — we want *external* consumers only
}

# Common rg glob excludes applied to every search.
RG_GLOB_EXCLUDES: list[str] = [
    "--glob",
    "!.venv*",
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
]

BATCH_SIZE = 50
RG_TIMEOUT_SECONDS = 10


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class TypeUsage:
    name: str
    source: str  # "UAC" or "UIC"
    instantiation_files: list[str] = field(default_factory=list)
    type_annotation_files: list[str] = field(default_factory=list)
    isinstance_files: list[str] = field(default_factory=list)
    re_export_files: list[str] = field(default_factory=list)
    import_only_files: list[str] = field(default_factory=list)

    @property
    def classification(self) -> str:
        non_test_instantiation = [f for f in self.instantiation_files if not _is_test_file(f)]
        non_test_annotation = [f for f in self.type_annotation_files if not _is_test_file(f)]
        non_test_isinstance = [f for f in self.isinstance_files if not _is_test_file(f)]

        non_init_instantiation = [f for f in non_test_instantiation if not _is_init_file(f)]
        non_init_annotation = [f for f in non_test_annotation if not _is_init_file(f)]
        non_init_isinstance = [f for f in non_test_isinstance if not _is_init_file(f)]

        if non_init_instantiation or non_init_annotation or non_init_isinstance:
            return "ALIVE"

        all_test_files = self.instantiation_files + self.type_annotation_files + self.isinstance_files
        if any(_is_test_file(f) for f in all_test_files):
            return "TEST_ONLY"

        all_init_files = self.re_export_files + [
            f for f in (self.instantiation_files + self.type_annotation_files) if _is_init_file(f)
        ]
        if all_init_files:
            return "IMPORT_CHAIN_ONLY"

        return "DEAD"


def _is_test_file(path: str) -> bool:
    return "/tests/" in path or "/test_" in path or path.endswith("_test.py")


def _is_init_file(path: str) -> bool:
    return path.endswith("__init__.py")


# ---------------------------------------------------------------------------
# Extract __all__ from an __init__.py via AST
# ---------------------------------------------------------------------------


def extract_all_names(init_path: Path) -> list[str]:
    """Parse __all__ from an __init__.py using the AST — no imports needed."""
    if not init_path.exists():
        logger.error("File not found: %s", init_path)
        return []

    source = init_path.read_text()
    tree = ast.parse(source, filename=str(init_path))

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__" and isinstance(node.value, ast.List):
                    names: list[str] = []
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            names.append(elt.value)
                    return names
    logger.warning("Could not find __all__ in %s", init_path)
    return []


# ---------------------------------------------------------------------------
# Batched ripgrep searches
# ---------------------------------------------------------------------------


def _build_search_dirs(workspace_root: Path) -> list[Path]:
    """Return list of repo directories to search (excluding SKIP_DIRS)."""
    dirs: list[str] = []
    for entry in sorted(workspace_root.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue
        if entry.name in SKIP_DIRS:
            continue
        dirs.append(str(entry))
    return [Path(d) for d in dirs]


def _run_rg(
    pattern: str,
    search_paths: list[Path],
    extra_args: list[str] | None = None,
) -> list[str]:
    """Run ripgrep with the given pattern across search_paths. Return matching file paths."""
    cmd = [
        "rg",
        "--type",
        "py",
        "-l",  # files-with-matches only
        "--no-messages",
    ]
    cmd.extend(RG_GLOB_EXCLUDES)
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(pattern)
    cmd.extend(str(p) for p in search_paths)

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
        logger.error("ripgrep (rg) not found — please install it")
        sys.exit(1)

    if result.returncode not in (0, 1):  # 1 = no matches
        logger.debug("rg returned %d for pattern: %s", result.returncode, pattern[:80])
    return [line for line in result.stdout.strip().split("\n") if line]


def _run_rg_with_content(
    pattern: str,
    search_paths: list[Path],
    extra_args: list[str] | None = None,
) -> list[tuple[str, str]]:
    """Run rg returning (file_path, matched_line) pairs."""
    cmd = [
        "rg",
        "--type",
        "py",
        "--no-filename",
        "--with-filename",
        "--no-heading",
        "--no-messages",
    ]
    cmd.extend(RG_GLOB_EXCLUDES)
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(pattern)
    cmd.extend(str(p) for p in search_paths)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=RG_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        logger.warning("rg timed out for content pattern (first 80 chars): %s", pattern[:80])
        return []
    except FileNotFoundError:
        logger.error("ripgrep (rg) not found — please install it")
        sys.exit(1)

    pairs: list[tuple[str, str]] = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        # Format: filepath:matched_content
        colon_idx = line.find(":")
        if colon_idx > 0:
            pairs.append((line[:colon_idx], line[colon_idx + 1 :]))
    return pairs


def _batch_search_instantiation(
    type_names: list[str],
    search_paths: list[Path],
) -> dict[str, list[str]]:
    """Search for TypeName( patterns — instantiation signal."""
    results: dict[str, list[str]] = {name: [] for name in type_names}
    # Build alternation pattern: (TypeName1|TypeName2|...)\(
    # We search with content to attribute hits to specific types.
    alternation = "|".join(type_names)
    pattern = f"({alternation})\\("

    pairs = _run_rg_with_content(pattern, search_paths)
    for file_path, matched_line in pairs:
        for name in type_names:
            if f"{name}(" in matched_line and file_path not in results[name]:
                results[name].append(file_path)
    return results


def _batch_search_type_annotation(
    type_names: list[str],
    search_paths: list[Path],
) -> dict[str, list[str]]:
    """Search for : TypeName, -> TypeName, [TypeName], dict[str, TypeName]."""
    results: dict[str, list[str]] = {name: [] for name in type_names}
    alternation = "|".join(type_names)
    # Match ": TypeName" or "-> TypeName" or "[TypeName]" or "[TypeName," etc.
    pattern = f"(: |-> |\\[)({alternation})(\\]|,|\\)|\\s|$)"

    pairs = _run_rg_with_content(pattern, search_paths)
    for file_path, matched_line in pairs:
        for name in type_names:
            # Check for annotation context
            if (
                f": {name}" in matched_line
                or f"-> {name}" in matched_line
                or f"[{name}]" in matched_line
                or f"[{name}," in matched_line
                or f", {name}]" in matched_line
                or f"[{name}]" in matched_line
            ) and file_path not in results[name]:
                results[name].append(file_path)
    return results


def _batch_search_isinstance(
    type_names: list[str],
    search_paths: list[Path],
) -> dict[str, list[str]]:
    """Search for isinstance(x, TypeName) patterns."""
    results: dict[str, list[str]] = {name: [] for name in type_names}
    alternation = "|".join(type_names)
    pattern = f"isinstance\\(.*, ({alternation})"

    pairs = _run_rg_with_content(pattern, search_paths)
    for file_path, matched_line in pairs:
        for name in type_names:
            if "isinstance(" in matched_line and name in matched_line and file_path not in results[name]:
                results[name].append(file_path)
    return results


def _batch_search_re_export(
    type_names: list[str],
    search_paths: list[Path],
) -> dict[str, list[str]]:
    """Search for re-export patterns in __init__.py files."""
    results: dict[str, list[str]] = {name: [] for name in type_names}
    alternation = "|".join(type_names)
    # "import TypeName as TypeName" or "TypeName as TypeName" in __init__.py
    pattern = f"({alternation}) as ({alternation})"

    pairs = _run_rg_with_content(pattern, search_paths, extra_args=["--glob", "*__init__.py"])
    for file_path, matched_line in pairs:
        for name in type_names:
            if f"{name} as {name}" in matched_line and file_path not in results[name]:
                results[name].append(file_path)
    return results


def _batch_search_import_only(
    type_names: list[str],
    search_paths: list[Path],
) -> dict[str, list[str]]:
    """Search for files that import a type but only have it on import lines.

    Strategy: find all files that mention the type name, then for each file
    check if the name appears outside of import statements.

    We use rg to find files, then for each file check if the type appears
    in non-import lines.
    """
    results: dict[str, list[str]] = {name: [] for name in type_names}
    alternation = "|".join(type_names)
    # Find all files mentioning any of these names in import statements
    import_pattern = f"(from .+ import .+({alternation})|import .+({alternation}))"
    import_files = _run_rg(import_pattern, search_paths)

    if not import_files:
        return results

    # For files that import a type, check if the type appears in non-import lines
    # We do this per-batch: find all mentions, subtract import-only mentions
    all_mention_pattern = f"\\b({alternation})\\b"
    import_file_paths = [Path(f) for f in import_files if Path(f).exists()]

    if not import_file_paths:
        return results

    # Get all mentions with content
    all_pairs = _run_rg_with_content(all_mention_pattern, import_file_paths)

    # Group by file
    file_mentions: dict[str, list[str]] = {}
    for file_path, matched_line in all_pairs:
        file_mentions.setdefault(file_path, []).append(matched_line)

    for file_path, lines in file_mentions.items():
        for name in type_names:
            import_count = 0
            total_count = 0
            for line in lines:
                if name not in line:
                    continue
                total_count += 1
                stripped = line.strip()
                if stripped.startswith(("from ", "import ")) or stripped.startswith('"'):
                    import_count += 1
                elif stripped.startswith("'") and stripped.endswith("'"):
                    # __all__ entry
                    import_count += 1

            if total_count > 0 and total_count == import_count and file_path not in results[name]:
                results[name].append(file_path)

    return results


# ---------------------------------------------------------------------------
# Main audit logic
# ---------------------------------------------------------------------------


def run_audit(
    workspace_root: Path,
    output_dir: Path,
    verbose: bool = False,
) -> None:
    """Run the full type usage audit."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    start_time = time.time()

    # 1. Collect type names from __all__
    uac_init = workspace_root / "unified-api-contracts/unified_api_contracts/__init__.py"
    uic_init = workspace_root / "unified-api-contracts/unified_api_contracts/internal/__init__.py"

    logger.info("Extracting __all__ from UAC...")
    uac_names = extract_all_names(uac_init)
    logger.info("  Found %d UAC exports", len(uac_names))

    logger.info("Extracting __all__ from UIC...")
    uic_names = extract_all_names(uic_init)
    logger.info("  Found %d UIC exports", len(uic_names))

    # Filter to class/type-like names (PascalCase or UPPER_CASE — skip functions
    # like get_data_sources_for_venue, american_to_decimal, etc.)
    all_type_names: list[tuple[str, str]] = []  # (name, source)
    for name in uac_names:
        all_type_names.append((name, "UAC"))
    for name in uic_names:
        # Avoid duplicates where UIC re-exports UAC types
        if not any(n == name for n, s in all_type_names):
            all_type_names.append((name, "UIC"))

    logger.info("Total unique type names to audit: %d", len(all_type_names))

    # 2. Build search directories
    search_dirs = _build_search_dirs(workspace_root)
    logger.info("Searching across %d repo directories", len(search_dirs))

    # 3. Process in batches
    usages: dict[str, TypeUsage] = {}
    for name, source in all_type_names:
        usages[name] = TypeUsage(name=name, source=source)

    type_name_list = [name for name, _ in all_type_names]
    total_batches = (len(type_name_list) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(total_batches):
        batch_start = batch_idx * BATCH_SIZE
        batch_end = min(batch_start + BATCH_SIZE, len(type_name_list))
        batch = type_name_list[batch_start:batch_end]
        logger.info(
            "Checking batch %d/%d (%d types: %s ... %s)",
            batch_idx + 1,
            total_batches,
            len(batch),
            batch[0],
            batch[-1],
        )

        # Run all search categories for this batch
        instantiation = _batch_search_instantiation(batch, search_dirs)
        annotation = _batch_search_type_annotation(batch, search_dirs)
        isinstance_hits = _batch_search_isinstance(batch, search_dirs)
        re_exports = _batch_search_re_export(batch, search_dirs)

        for name in batch:
            usages[name].instantiation_files.extend(instantiation.get(name, []))
            usages[name].type_annotation_files.extend(annotation.get(name, []))
            usages[name].isinstance_files.extend(isinstance_hits.get(name, []))
            usages[name].re_export_files.extend(re_exports.get(name, []))

    # 4. Classify
    alive: list[TypeUsage] = []
    test_only: list[TypeUsage] = []
    import_chain_only: list[TypeUsage] = []
    dead: list[TypeUsage] = []

    for usage in usages.values():
        classification = usage.classification
        if classification == "ALIVE":
            alive.append(usage)
        elif classification == "TEST_ONLY":
            test_only.append(usage)
        elif classification == "IMPORT_CHAIN_ONLY":
            import_chain_only.append(usage)
        else:
            dead.append(usage)

    elapsed = time.time() - start_time

    # 5. Write reports
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "alive": len(alive),
        "test_only": len(test_only),
        "import_chain_only": len(import_chain_only),
        "dead": len(dead),
        "total": len(usages),
    }

    json_report = {
        "summary": summary,
        "dead_types": sorted(
            [
                {
                    "name": u.name,
                    "source": u.source,
                }
                for u in dead
            ],
            key=lambda x: str(x["name"]),
        ),
        "import_chain_only": sorted(
            [
                {
                    "name": u.name,
                    "source": u.source,
                    "chain": sorted(u.re_export_files),
                }
                for u in import_chain_only
            ],
            key=lambda x: str(x["name"]),
        ),
        "test_only": sorted(
            [
                {
                    "name": u.name,
                    "source": u.source,
                    "test_files": sorted(set(u.instantiation_files + u.type_annotation_files + u.isinstance_files)),
                }
                for u in test_only
            ],
            key=lambda x: str(x["name"]),
        ),
        "alive_types": sorted(
            [
                {
                    "name": u.name,
                    "source": u.source,
                    "instantiation_count": len(
                        [f for f in u.instantiation_files if not _is_test_file(f) and not _is_init_file(f)]
                    ),
                    "annotation_count": len(
                        [f for f in u.type_annotation_files if not _is_test_file(f) and not _is_init_file(f)]
                    ),
                    "isinstance_count": len(
                        [f for f in u.isinstance_files if not _is_test_file(f) and not _is_init_file(f)]
                    ),
                }
                for u in alive
            ],
            key=lambda x: str(x["name"]),
        ),
    }

    json_path = output_dir / "type_usage_audit.json"
    with open(json_path, "w") as f:
        json.dump(json_report, f, indent=2)
    logger.info("JSON report: %s", json_path)

    # Human-readable text report
    text_lines: list[str] = []
    text_lines.append("=" * 72)
    text_lines.append("UAC / UIC Type Usage Audit Report")
    text_lines.append("=" * 72)
    text_lines.append("")
    text_lines.append(f"Workspace: {workspace_root}")
    text_lines.append(f"Elapsed:   {elapsed:.1f}s")
    text_lines.append("")
    text_lines.append("SUMMARY")
    text_lines.append("-" * 40)
    text_lines.append(f"  ALIVE:             {summary['alive']:>4}")
    text_lines.append(f"  TEST_ONLY:         {summary['test_only']:>4}")
    text_lines.append(f"  IMPORT_CHAIN_ONLY: {summary['import_chain_only']:>4}")
    text_lines.append(f"  DEAD:              {summary['dead']:>4}")
    text_lines.append(f"  TOTAL:             {summary['total']:>4}")
    text_lines.append("")

    if dead:
        text_lines.append("")
        text_lines.append("DEAD TYPES (no external usage)")
        text_lines.append("-" * 40)
        for u in sorted(dead, key=lambda x: x.name):
            text_lines.append(f"  [{u.source}] {u.name}")

    if test_only:
        text_lines.append("")
        text_lines.append("TEST-ONLY TYPES (used only in test files)")
        text_lines.append("-" * 40)
        for u in sorted(test_only, key=lambda x: x.name):
            files_str = ", ".join(
                _shorten_path(f, workspace_root)
                for f in sorted(set(u.instantiation_files + u.type_annotation_files + u.isinstance_files))[:5]
            )
            text_lines.append(f"  [{u.source}] {u.name}")
            text_lines.append(f"           files: {files_str}")

    if import_chain_only:
        text_lines.append("")
        text_lines.append("IMPORT-CHAIN-ONLY TYPES (only in __init__.py re-exports)")
        text_lines.append("-" * 40)
        for u in sorted(import_chain_only, key=lambda x: x.name):
            chain_str = ", ".join(_shorten_path(f, workspace_root) for f in sorted(u.re_export_files)[:5])
            text_lines.append(f"  [{u.source}] {u.name}")
            if chain_str:
                text_lines.append(f"           chain: {chain_str}")

    if alive:
        text_lines.append("")
        text_lines.append("ALIVE TYPES (top 20 by instantiation count)")
        text_lines.append("-" * 40)
        top_alive = sorted(
            alive,
            key=lambda u: len([f for f in u.instantiation_files if not _is_test_file(f) and not _is_init_file(f)]),
            reverse=True,
        )[:20]
        for u in top_alive:
            non_test_inst = len([f for f in u.instantiation_files if not _is_test_file(f) and not _is_init_file(f)])
            non_test_annot = len([f for f in u.type_annotation_files if not _is_test_file(f) and not _is_init_file(f)])
            text_lines.append(f"  [{u.source}] {u.name:<50} inst={non_test_inst:<3} annot={non_test_annot}")

    text_lines.append("")
    text_lines.append("=" * 72)
    text_lines.append("END OF REPORT")
    text_lines.append("=" * 72)

    text_path = output_dir / "type_usage_audit.txt"
    with open(text_path, "w") as f:
        f.write("\n".join(text_lines) + "\n")
    logger.info("Text report: %s", text_path)

    # Print summary to stdout
    print()
    print(f"Audit complete in {elapsed:.1f}s")
    print(f"  ALIVE:             {summary['alive']}")
    print(f"  TEST_ONLY:         {summary['test_only']}")
    print(f"  IMPORT_CHAIN_ONLY: {summary['import_chain_only']}")
    print(f"  DEAD:              {summary['dead']}")
    print(f"  TOTAL:             {summary['total']}")
    print(f"\nReports written to: {output_dir}")


def _shorten_path(path: str, workspace_root: Path) -> str:
    """Shorten an absolute path relative to the workspace root."""
    try:
        return str(Path(path).relative_to(workspace_root))
    except ValueError:
        return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deep usage audit of UAC/UIC types across the workspace.",
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

    uac_dir = workspace_root / "unified-api-contracts"
    if not uac_dir.is_dir():
        logger.error("UAC repo not found at: %s", uac_dir)
        sys.exit(1)

    # Verify rg is available
    try:
        subprocess.run(["rg", "--version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        logger.error("ripgrep (rg) is not installed — please install it first")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        pass  # rg exists but was slow — fine

    run_audit(workspace_root, output_dir, verbose=args.verbose)


if __name__ == "__main__":
    main()
