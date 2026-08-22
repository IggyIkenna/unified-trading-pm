#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Aggregate all repo dependencies into .venv-workspace.

Walks every pyproject.toml in the workspace, classifies deps as internal
(workspace path deps) or external, then installs everything into the
workspace venv.

Internal deps: installed as editable (uv pip install -e ../repo-name)
External deps: installed with version constraints from pyproject.toml files

After installation, freezes exact versions to .venv-workspace/requirements.lock
for reproducible installs on subsequent runs.

Usage:
    python aggregate-workspace-deps.py                  # install from lock if exists, else resolve
    python aggregate-workspace-deps.py --resolve        # re-resolve all deps (ignore lock)
    python aggregate-workspace-deps.py --dry-run        # show what would be installed
    python aggregate-workspace-deps.py --lock-only      # just generate the lock file
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import cast

# Type aliases
type DepSpec = str  # e.g. "pydantic>=2.12.5,<3.0.0"
type TomlDict = dict[str, object]

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PM_ROOT = WORKSPACE_ROOT / "unified-trading-pm"
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"
CONSTRAINTS_PATH = PM_ROOT / "workspace-constraints.toml"
VENV_DIR = WORKSPACE_ROOT / ".venv-workspace"
LOCK_FILE = VENV_DIR / "requirements.lock"
WORKSPACE_TOOLS = ["ruff==0.15.0", "basedpyright>=1.18.0,<2.0.0", "pytest>=8.0.0"]


def load_manifest() -> TomlDict:
    """Load workspace manifest and return parsed JSON."""
    with open(MANIFEST_PATH) as f:
        return cast(TomlDict, json.load(f))


def load_workspace_constraints() -> dict[str, str]:
    """Load [dependencies] from workspace-constraints.toml if present. Keys normalized."""
    if not CONSTRAINTS_PATH.is_file():
        return {}
    with open(CONSTRAINTS_PATH, "rb") as f:
        data = cast(TomlDict, tomllib.load(f))
    deps = data.get("dependencies")
    if not isinstance(deps, dict):
        return {}
    return {normalize_pkg_name(k): str(v) for k, v in deps.items()}


def _level_sort_key(lvl: TomlDict) -> int:
    """Sort key for topological levels."""
    raw = lvl.get("level")
    return int(cast(int, raw)) if isinstance(raw, int) else 999


def get_repo_folder_path(manifest: TomlDict, repo_name: str) -> Path:
    """Resolve repo name to workspace folder path (uses folder_name from manifest when present)."""
    repos_raw = manifest.get("repositories")
    if isinstance(repos_raw, dict):
        entry = repos_raw.get(repo_name)
        if isinstance(entry, dict):
            folder = entry.get("folder_name")
            if isinstance(folder, str):
                return WORKSPACE_ROOT / folder
    return WORKSPACE_ROOT / repo_name


def get_topological_order(manifest: TomlDict) -> list[str]:
    """Extract repos in topological order (T0 first)."""
    topo_raw = manifest.get("topologicalOrder")
    if not isinstance(topo_raw, dict):
        return []
    topo: TomlDict = cast(TomlDict, topo_raw)

    levels_raw = topo.get("levels")
    if not isinstance(levels_raw, list):
        return []
    levels_list: list[object] = cast(list[object], levels_raw)

    levels: list[TomlDict] = [cast(TomlDict, lvl) for lvl in levels_list if isinstance(lvl, dict)]

    ordered: list[str] = []
    for level in sorted(levels, key=_level_sort_key):
        repos_raw = level.get("repos")
        if not isinstance(repos_raw, list):
            continue
        repos_list: list[object] = cast(list[object], repos_raw)
        for repo in repos_list:
            if isinstance(repo, str):
                ordered.append(repo)
    return ordered


def parse_pyproject(repo_path: Path) -> tuple[list[DepSpec], dict[str, str]]:
    """Parse a repo's pyproject.toml. Returns (dependencies, uv_sources).

    uv_sources maps dep-name -> relative path (workspace path deps).
    """
    pyproject_path = repo_path / "pyproject.toml"
    if not pyproject_path.is_file():
        return [], {}

    with open(pyproject_path, "rb") as f:
        data: TomlDict = cast(TomlDict, tomllib.load(f))

    project_raw = data.get("project")
    project: TomlDict = cast(TomlDict, project_raw) if isinstance(project_raw, dict) else {}

    # Main dependencies
    deps: list[DepSpec] = []
    raw_deps = project.get("dependencies")
    if isinstance(raw_deps, list):
        deps_list: list[object] = cast(list[object], raw_deps)
        deps = [str(d) for d in deps_list]

    # Optional dev deps
    optional_raw = project.get("optional-dependencies")
    if isinstance(optional_raw, dict):
        optional: TomlDict = cast(TomlDict, optional_raw)
        dev_deps_raw = optional.get("dev")
        if isinstance(dev_deps_raw, list):
            dev_list: list[object] = cast(list[object], dev_deps_raw)
            deps.extend(str(d) for d in dev_list)

    # Parse [tool.uv.sources] for path dependencies
    uv_sources: dict[str, str] = {}
    tool_raw = data.get("tool")
    if isinstance(tool_raw, dict):
        tool: TomlDict = cast(TomlDict, tool_raw)
        uv_raw = tool.get("uv")
        if isinstance(uv_raw, dict):
            uv: TomlDict = cast(TomlDict, uv_raw)
            sources_raw = uv.get("sources")
            if isinstance(sources_raw, dict):
                sources: TomlDict = cast(TomlDict, sources_raw)
                for dep_name_str, source_info_raw in sources.items():
                    if isinstance(source_info_raw, dict):
                        source_info: TomlDict = cast(TomlDict, source_info_raw)
                        path_val = source_info.get("path")
                        if isinstance(path_val, str):
                            uv_sources[dep_name_str] = path_val

    return deps, uv_sources


def normalize_pkg_name(name: str) -> str:
    """Normalize a package name for comparison (PEP 503)."""
    return name.lower().replace("-", "_").replace(".", "_")


def extract_pkg_name(dep_spec: DepSpec) -> str:
    """Extract package name from a dependency spec like 'pydantic>=2.0' or 'pkg @ file://...'."""
    # PEP 508: "name @ url" -> name only
    if " @ " in dep_spec:
        return dep_spec.split(" @ ", 1)[0].strip()
    for sep in [">=", "<=", "!=", "==", ">", "<", "~=", "[", ";"]:
        idx = dep_spec.find(sep)
        if idx > 0:
            return dep_spec[:idx].strip()
    return dep_spec.strip()


def collect_all_deps(
    repos: list[str],
    manifest: TomlDict,
) -> tuple[dict[str, list[DepSpec]], set[str], dict[str, str]]:
    """Walk all repos, collect and classify dependencies.

    Returns:
        external_deps: normalized_name -> list of version specs from different repos
        internal_names: set of normalized package names that are workspace deps
        internal_paths: normalized_name -> relative path to repo
    """
    internal_names: set[str] = set()
    internal_paths: dict[str, str] = {}

    # Pass 1: collect all workspace (path) deps from every repo so we never treat them as external
    for repo_name in repos:
        repo_path = get_repo_folder_path(manifest, repo_name)
        if not repo_path.is_dir():
            continue
        _deps, uv_sources = parse_pyproject(repo_path)
        for dep_name, rel_path in uv_sources.items():
            norm = normalize_pkg_name(dep_name)
            internal_names.add(norm)
            abs_path = (repo_path / rel_path).resolve()
            if abs_path.is_dir():
                internal_paths[norm] = str(abs_path.relative_to(WORKSPACE_ROOT))

    # Pass 2: collect external deps only (skip anything in internal_names)
    external_deps: dict[str, list[DepSpec]] = {}
    for repo_name in repos:
        repo_path = get_repo_folder_path(manifest, repo_name)
        if not repo_path.is_dir():
            continue
        deps, uv_sources = parse_pyproject(repo_path)
        workspace_dep_names = {normalize_pkg_name(d) for d in uv_sources}
        for dep_spec in deps:
            pkg_name = extract_pkg_name(dep_spec)
            norm = normalize_pkg_name(pkg_name)
            if norm in workspace_dep_names or norm in internal_names:
                continue
            if norm not in external_deps:
                external_deps[norm] = []
            external_deps[norm].append(dep_spec)

    # Ensure no internal package leaked into external (e.g. repo order)
    for norm in internal_names:
        external_deps.pop(norm, None)

    return external_deps, internal_names, internal_paths


def _dedupe_spec_name(spec: DepSpec) -> DepSpec:
    """Fix propagate-induced duplicated package names (e.g. aiobotocoreaiobotocore>=2.11.0 -> aiobotocore>=2.11.0)."""
    for sep in [">=", "<=", "!=", "==", ">", "<", "~="]:
        idx = spec.find(sep)
        if idx > 0:
            name, rest = spec[:idx].strip(), spec[idx:]
            # If name is exactly two copies of the same string (e.g. ruffruff), use one
            if len(name) % 2 == 0:
                half = len(name) // 2
                if name[:half] == name[half:]:
                    return name[:half] + rest
            return spec
    return spec


def pick_tightest_constraint(specs: list[DepSpec]) -> DepSpec:
    """Given multiple version specs for the same package, pick the tightest.

    Strategy: pick the spec with the highest minimum version requirement.
    If multiple have the same minimum, prefer ones with upper bounds.
    """
    if len(specs) == 1:
        return specs[0]

    unique = list(set(specs))
    if len(unique) == 1:
        return unique[0]

    # Heuristic: longer = more constrained, higher version = tighter
    return sorted(unique, key=lambda s: (len(s), s), reverse=True)[0]


def generate_requirements(
    external_deps: dict[str, list[DepSpec]],
    internal_paths: dict[str, str],
    topo_order: list[str],
    constraints: dict[str, str] | None = None,
) -> tuple[list[str], list[str]]:
    """Generate two lists: internal editable installs and external deps."""
    # Internal: editable installs in topological order
    # Deduplicate by target path (aliases like unified-cloud-services -> unified-trading-services)
    internal_lines: list[str] = []
    installed_paths: set[str] = set()

    for repo_name in topo_order:
        norm = normalize_pkg_name(repo_name)
        if norm in internal_paths:
            rel_path = internal_paths[norm]
            if rel_path not in installed_paths:
                internal_lines.append(f"-e {rel_path}")
                installed_paths.add(rel_path)

    # Also add any internal deps not in topo order (fallback)
    for _norm, rel_path in sorted(internal_paths.items()):
        if rel_path not in installed_paths:
            internal_lines.append(f"-e {rel_path}")
            installed_paths.add(rel_path)

    # External: use workspace-constraints.toml when present, else tightest from repos (dedupe name duplication)
    constraints = constraints or {}
    external_lines: list[str] = []
    for norm_name in sorted(external_deps):
        if norm_name in constraints:
            spec = constraints[norm_name]
        else:
            spec = pick_tightest_constraint(external_deps[norm_name])
        external_lines.append(_dedupe_spec_name(spec))

    # Ensure constraint overrides apply (e.g. aiofiles 24.x for tardis-client compatibility)
    for i, line in enumerate(external_lines):
        pkg = line.split(">=")[0].split("==")[0].split("<")[0].strip()
        if normalize_pkg_name(pkg) in constraints:
            external_lines[i] = constraints[normalize_pkg_name(pkg)]

    return internal_lines, external_lines


def write_requirements_file(
    internal_lines: list[str],
    external_lines: list[str],
    output_path: Path,
) -> None:
    """Write a combined requirements file."""
    lines = [
        "# Auto-generated by aggregate-workspace-deps.py",
        "# Do not edit manually — re-run the script to update.",
        "",
        "# === Workspace tools ===",
    ]
    for tool in WORKSPACE_TOOLS:
        lines.append(tool)
    lines.append("")
    lines.append("# === Internal workspace deps (editable) ===")
    lines.extend(internal_lines)
    lines.append("")
    lines.append("# === External deps (from all repos' pyproject.toml) ===")
    lines.extend(external_lines)
    lines.append("")

    output_path.write_text("\n".join(lines))


def _get_uv_cmd(venv_python: Path) -> tuple[list[str], bool] | None:
    """Return (uv_prefix, use_system_uv). uv_prefix is the command to run before 'pip install'.
    use_system_uv=True means we must pass --python to target the venv."""
    # Prefer system uv (bootstrap Phase 1 installs it)
    uv_check = subprocess.run(
        ["uv", "--version"],
        capture_output=True,
        text=True,
    )
    if uv_check.returncode == 0:
        return (["uv"], True)
    # Fallback: uv in workspace venv
    if venv_python.is_file():
        uv_in_venv = subprocess.run(
            [str(venv_python), "-m", "uv", "--version"],
            capture_output=True,
            text=True,
        )
        if uv_in_venv.returncode == 0:
            return ([str(venv_python), "-m", "uv"], False)
    return None


def run_uv_install(
    requirements_file: Path,
    *,
    dry_run: bool = False,
    no_deps: bool = False,
) -> bool:
    """Run uv pip install from the requirements file into .venv-workspace."""
    venv_python = VENV_DIR / "bin" / "python"
    if not venv_python.is_file():
        print(f"ERROR: Workspace venv not found at {VENV_DIR}")
        print("  Run workspace-bootstrap.sh first to create it.")
        return False

    uv_result = _get_uv_cmd(venv_python)
    if uv_result is None:
        print("ERROR: uv not found. Install it first:")
        print("  pip install uv   # or: brew install uv / apt install uv")
        print("  Then re-run workspace-bootstrap.sh")
        return False

    uv_prefix, use_system_uv = uv_result
    cmd = [*uv_prefix, "pip", "install"]
    if use_system_uv:
        cmd.extend(["--python", str(venv_python)])
    if no_deps:
        cmd.append("--no-deps")
    cmd.extend(["-r", str(requirements_file)])

    if dry_run:
        print(f"\n[DRY RUN] Would run: {' '.join(cmd)}")
        return True

    print(f"\nInstalling dependencies into {VENV_DIR}...")
    print(f"  Requirements file: {requirements_file}")

    result = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT))
    return result.returncode == 0


def freeze_lockfile() -> bool:
    """Freeze current venv state to requirements.lock."""
    venv_python = VENV_DIR / "bin" / "python"
    if not venv_python.is_file():
        return False

    result = subprocess.run(
        [str(venv_python), "-m", "uv", "pip", "freeze"],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_ROOT),
    )
    if result.returncode != 0:
        print(f"WARNING: Failed to freeze: {result.stderr}")
        return False

    header = "# Auto-generated lock file — exact versions for reproducible installs\n"
    header += "# Re-generate with: python aggregate-workspace-deps.py --resolve\n\n"
    LOCK_FILE.write_text(header + result.stdout)
    print(f"  Lockfile written: {LOCK_FILE}")
    return True


def main() -> None:
    """Aggregate workspace deps and install into .venv-workspace."""
    parser = argparse.ArgumentParser(description="Aggregate workspace dependencies")
    parser.add_argument("--resolve", action="store_true", help="Re-resolve all deps (ignore lockfile)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be installed")
    parser.add_argument("--lock-only", action="store_true", help="Only generate lock file from current state")
    parsed = parser.parse_args()
    do_resolve: bool = bool(cast(object, parsed.resolve))
    do_dry_run: bool = bool(cast(object, parsed.dry_run))
    do_lock_only: bool = bool(cast(object, parsed.lock_only))

    if do_lock_only:
        print("Generating lockfile from current .venv-workspace state...")
        if freeze_lockfile():
            print("Done.")
        else:
            print("Failed.", file=sys.stderr)
            sys.exit(1)
        return

    # If lockfile exists and not --resolve, use it directly
    if LOCK_FILE.is_file() and not do_resolve and not do_dry_run:
        print(f"Using existing lockfile: {LOCK_FILE}")
        print("  (pass --resolve to re-resolve from pyproject.toml files)")
        success = run_uv_install(LOCK_FILE)
        sys.exit(0 if success else 1)

    print("Aggregating dependencies from all workspace repos...\n")

    # Load manifest
    if not MANIFEST_PATH.is_file():
        print(f"ERROR: Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest()
    topo_order = get_topological_order(manifest)

    # Use only repos in topologicalOrder.levels (canonical workflow list); excludes archived repos not in levels.
    repo_names = topo_order

    print(f"  Topological order: {len(topo_order)} repos")

    # Collect deps from all repos in topological order
    external_deps, internal_names, internal_paths = collect_all_deps(repo_names, manifest)

    print(f"  Internal workspace deps: {len(internal_names)}")
    print(f"  External packages: {len(external_deps)}")

    # Generate requirements (prefer workspace-constraints.toml when present for consistent resolution)
    constraints = load_workspace_constraints()
    internal_lines, external_lines = generate_requirements(
        external_deps, internal_paths, topo_order, constraints=constraints
    )

    # Write requirements file (full) and split files for two-phase install
    req_file = VENV_DIR / "requirements.txt"
    write_requirements_file(internal_lines, external_lines, req_file)
    req_internal = VENV_DIR / "requirements-internal.txt"
    req_external = VENV_DIR / "requirements-external.txt"
    req_internal.write_text(
        "# Internal editable only — install with --no-deps to avoid path/editable URL conflict\n"
        + "\n".join(internal_lines)
        + "\n"
    )
    external_only_lines = [
        "# Workspace tools + external only",
        *WORKSPACE_TOOLS,
        "",
        *external_lines,
    ]
    req_external.write_text("\n".join(external_only_lines) + "\n")
    print(f"\n  Requirements file: {req_file}")
    print(f"    Internal (editable): {len(internal_lines)} packages")
    print(f"    External: {len(external_lines)} packages")
    print(f"    Workspace tools: {len(WORKSPACE_TOOLS)} packages")

    if do_dry_run:
        print("\n--- Internal (editable) ---")
        for line in internal_lines:
            print(f"  {line}")
        print(f"\n--- External ({len(external_lines)} packages) ---")
        for line in external_lines[:20]:
            print(f"  {line}")
        if len(external_lines) > 20:
            print(f"  ... and {len(external_lines) - 20} more")
        return

    # Two-phase install: internal with --no-deps first (avoids uv seeing same path as
    # editable and as path dep), then external
    print("\n  Phase 1: internal editable installs (--no-deps)")
    if not run_uv_install(req_internal, no_deps=True):
        print("\nInstallation failed (phase 1).", file=sys.stderr)
        sys.exit(1)
    print("  Phase 2: tools + external deps")
    if not run_uv_install(req_external):
        print("\nInstallation failed (phase 2).", file=sys.stderr)
        sys.exit(1)

    # Freeze lockfile
    print("\nFreezing exact versions to lockfile...")
    freeze_lockfile()

    print("\nDone. Workspace venv has all dependencies installed.")
    print(f"  Venv: {VENV_DIR}")
    print(f"  Lock: {LOCK_FILE}")


if __name__ == "__main__":
    main()
