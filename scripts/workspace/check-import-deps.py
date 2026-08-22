#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Check that Python imports match declared dependencies in pyproject.toml.

The workspace venv installs all repos, so imports from undeclared packages
silently succeed. This script catches those violations by:

1. For each repo in workspace-manifest.json:
   - Parsing pyproject.toml [project.dependencies] for declared packages
   - Using workspace-manifest.json to identify internal workspace packages
   - Scanning all .py source files for import statements via ast.parse
   - Mapping import module names to package names (e.g. unified_domain_client
     -> unified-domain-client)
   - Flagging any import from an internal workspace package NOT listed in
     that repo's pyproject.toml dependencies
   - Flagging any import from an external package NOT in the repo's deps
     AND not in workspace-constraints.toml
   - Excluding stdlib modules and the repo's own package

2. Outputting a per-repo violation report

3. Exiting non-zero if any violations found

Usage:
    python check-import-deps.py                # check all repos
    python check-import-deps.py --repo NAME    # check a single repo
    python check-import-deps.py --verbose      # show all imports, not just violations
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
import sysconfig
import tomllib
from pathlib import Path
from typing import cast

type TomlDict = dict[str, object]

# Resolve workspace paths relative to this script
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PM_ROOT = WORKSPACE_ROOT / "unified-trading-pm"
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"
CONSTRAINTS_PATH = PM_ROOT / "workspace-constraints.toml"

# Directories to exclude when scanning source files
EXCLUDE_DIRS = {
    ".venv",
    "venv",
    ".venv-workspace",
    "__pycache__",
    ".git",
    ".github",
    "node_modules",
    "build",
    "dist",
    ".egg-info",
    ".eggs",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "tests",
    "examples",
    "docs",
    "scripts",
    # Nested per-agent git worktrees (.claude/worktrees/<id>/) can carry an
    # older/different snapshot of the same repo's source — scanning one produces
    # false violations for code that doesn't exist in the actual checked-out
    # tree (found live 2026-08-06, same class as the check_manifest_import_
    # alignment.py / test_event_logging.py fixes).
    ".claude",
}


def get_stdlib_modules() -> set[str]:
    """Return set of standard library top-level module names."""
    stdlib_path = sysconfig.get_paths()["stdlib"]
    stdlib = set()
    stdlib_dir = Path(stdlib_path)
    if stdlib_dir.exists():
        for item in stdlib_dir.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                stdlib.append(item.name) if False else stdlib.add(item.name)
            elif item.suffix == ".py" and item.name != "__init__.py":
                stdlib.add(item.stem)

    # Also add well-known stdlib modules that may not be on disk
    known_stdlib = {
        "abc",
        "argparse",
        "ast",
        "asyncio",
        "atexit",
        "base64",
        "binascii",
        "bisect",
        "builtins",
        "calendar",
        "cgi",
        "cgitb",
        "codecs",
        "collections",
        "colorsys",
        "compileall",
        "concurrent",
        "configparser",
        "contextlib",
        "contextvars",
        "copy",
        "copyreg",
        "cProfile",
        "csv",
        "ctypes",
        "dataclasses",
        "datetime",
        "dbm",
        "decimal",
        "difflib",
        "dis",
        "distutils",
        "doctest",
        "email",
        "encodings",
        "enum",
        "errno",
        "faulthandler",
        "fcntl",
        "filecmp",
        "fileinput",
        "fnmatch",
        "fractions",
        "ftplib",
        "functools",
        "gc",
        "getopt",
        "getpass",
        "gettext",
        "glob",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "idlelib",
        "imaplib",
        "importlib",
        "inspect",
        "io",
        "ipaddress",
        "itertools",
        "json",
        "keyword",
        "lib2to3",
        "linecache",
        "locale",
        "logging",
        "lzma",
        "mailbox",
        "mailcap",
        "marshal",
        "math",
        "mimetypes",
        "mmap",
        "modulefinder",
        "multiprocessing",
        "netrc",
        "numbers",
        "operator",
        "optparse",
        "os",
        "pathlib",
        "pdb",
        "pickle",
        "pickletools",
        "pkgutil",
        "platform",
        "plistlib",
        "poplib",
        "posixpath",
        "pprint",
        "profile",
        "pstats",
        "pty",
        "py_compile",
        "pyclbr",
        "pydoc",
        "queue",
        "quopri",
        "random",
        "re",
        "readline",
        "reprlib",
        "resource",
        "rlcompleter",
        "runpy",
        "sched",
        "secrets",
        "select",
        "selectors",
        "shelve",
        "shlex",
        "shutil",
        "signal",
        "site",
        "smtpd",
        "smtplib",
        "sndhdr",
        "socket",
        "socketserver",
        "sqlite3",
        "sre_compile",
        "sre_constants",
        "sre_parse",
        "ssl",
        "stat",
        "statistics",
        "string",
        "stringprep",
        "struct",
        "subprocess",
        "sunau",
        "symtable",
        "sys",
        "sysconfig",
        "syslog",
        "tabnanny",
        "tarfile",
        "telnetlib",
        "tempfile",
        "termios",
        "test",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "tkinter",
        "token",
        "tokenize",
        "tomllib",
        "trace",
        "traceback",
        "tracemalloc",
        "tty",
        "turtle",
        "turtledemo",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uuid",
        "venv",
        "warnings",
        "wave",
        "weakref",
        "webbrowser",
        "wsgiref",
        "xdrlib",
        "xml",
        "xmlrpc",
        "zipapp",
        "zipfile",
        "zipimport",
        "zlib",
        "zoneinfo",
        # C-level modules
        "_thread",
        "_io",
        "_signal",
        "_weakref",
        "_abc",
        "_collections",
        "_functools",
        "_operator",
        "_stat",
        "_string",
        "_struct",
        # Common typing extensions
        "typing_extensions",
    }
    stdlib.update(known_stdlib)
    return stdlib


def pkg_name_to_import_name(pkg_name: str) -> str:
    """Convert a PyPI package name to its likely Python import name.

    Examples:
        unified-domain-client -> unified_domain_client
        google-cloud-storage -> google (top-level)
        pydantic -> pydantic
    """
    return pkg_name.replace("-", "_")


def extract_package_name_from_dep(dep_spec: str) -> str:
    """Extract the package name from a dependency specification.

    Examples:
        'pydantic>=2.0,<3.0' -> 'pydantic'
        'unified-domain-client>=0.1.0' -> 'unified-domain-client'
        'boto3-stubs[s3]>=1.0' -> 'boto3-stubs'
    """
    # Remove extras
    name = dep_spec.split("[")[0]
    # Remove version specifiers
    for sep in (">=", "<=", "==", "!=", ">", "<", "~=", ";"):
        name = name.split(sep)[0]
    return name.strip()


def load_manifest() -> dict[str, object]:
    """Load workspace-manifest.json."""
    with open(MANIFEST_PATH) as f:
        return cast(dict[str, object], json.load(f))


def get_internal_package_names(manifest: dict[str, object]) -> dict[str, str]:
    """Get mapping of import_name -> repo_name for all internal packages."""
    if "repositories" not in manifest:
        raise KeyError("repositories required in workspace-manifest.json")
    repos = cast(dict[str, object], manifest["repositories"])
    result: dict[str, str] = {}
    for repo_name in repos:
        import_name = pkg_name_to_import_name(repo_name)
        result[import_name] = repo_name
    return result


def load_constraints() -> set[str]:
    """Load external package names from workspace-constraints.toml."""
    if not CONSTRAINTS_PATH.exists():
        return set()
    with open(CONSTRAINTS_PATH, "rb") as f:
        data = cast(TomlDict, tomllib.load(f))
    if "dependencies" not in data:
        raise KeyError("[dependencies] required in workspace-constraints.toml")
    deps_section = cast(dict[str, object], data["dependencies"])
    return set(deps_section.keys())


def parse_repo_deps(repo_dir: Path) -> set[str]:
    """Parse declared dependencies from a repo's pyproject.toml.

    Returns set of package names (not import names).
    """
    pyproject = repo_dir / "pyproject.toml"
    if not pyproject.exists():
        return set()
    with open(pyproject, "rb") as f:
        data = cast(TomlDict, tomllib.load(f))
    if "project" not in data:
        raise KeyError("[project] required in pyproject.toml")
    project = cast(dict[str, object], data["project"])
    deps_raw = cast(list[object], (project.get("dependencies") or []))  # PEP 621: optional
    result: set[str] = set()
    for dep in deps_raw:
        if isinstance(dep, str):
            pkg_name = extract_package_name_from_dep(dep)
            result.add(pkg_name)
    return result


def extract_imports_from_file(filepath: Path) -> set[str]:
    """Extract top-level import module names from a Python file using ast."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return set()

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Get top-level module: "foo.bar.baz" -> "foo"
                top = alias.name.split(".")[0]
                imports.add(top)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:  # Skip relative imports
            top = node.module.split(".")[0]
            imports.add(top)
    return imports


def scan_repo_imports(repo_dir: Path, own_package: str) -> set[str]:
    """Scan all Python source files in a repo for third-party imports.

    Excludes stdlib, own package, and files in EXCLUDE_DIRS.
    """
    all_imports: set[str] = set()
    for py_file in repo_dir.rglob("*.py"):
        # Skip excluded directories
        parts = py_file.relative_to(repo_dir).parts
        if any(p in EXCLUDE_DIRS or p.startswith(".venv") for p in parts):
            continue
        all_imports.update(extract_imports_from_file(py_file))

    # Remove own package
    all_imports.discard(own_package)
    return all_imports


def check_repo(
    repo_name: str,
    repo_dir: Path,
    internal_packages: dict[str, str],
    constraints_packages: set[str],
    stdlib_modules: set[str],
    verbose: bool = False,
) -> list[str]:
    """Check a single repo for import-dependency violations.

    Returns list of violation messages.
    """
    own_import_name = pkg_name_to_import_name(repo_name)

    # Get declared deps
    declared_deps = parse_repo_deps(repo_dir)
    declared_import_names = {pkg_name_to_import_name(d) for d in declared_deps}

    # Also map declared dep package names for lookup
    declared_pkg_names = declared_deps

    # Get all imports from source
    all_imports = scan_repo_imports(repo_dir, own_import_name)

    violations: list[str] = []

    for import_name in sorted(all_imports):
        # Skip stdlib
        if import_name in stdlib_modules:
            continue

        # Skip own package
        if import_name == own_import_name:
            continue

        # Check if it's an internal workspace package
        if import_name in internal_packages:
            internal_repo = internal_packages[import_name]
            # Check if declared in pyproject.toml
            if internal_repo not in declared_pkg_names and import_name not in declared_import_names:
                violations.append(
                    f"  INTERNAL: imports '{import_name}' (repo: {internal_repo}) but not declared in pyproject.toml"
                )
            elif verbose:
                print(f"  OK internal: {import_name} -> {internal_repo}")
            continue

        # External package — check if in declared deps or constraints
        # Map import name back to possible package names
        possible_pkg = import_name.replace("_", "-")

        if possible_pkg in declared_pkg_names or import_name in declared_import_names:
            if verbose:
                print(f"  OK external: {import_name}")
            continue

        # Check constraints
        if import_name in constraints_packages or possible_pkg in constraints_packages:
            # Package is in workspace constraints but not in this repo's deps
            violations.append(
                f"  EXTERNAL: imports '{import_name}' (pkg: {possible_pkg}) "
                f"- in workspace constraints but not in this repo's pyproject.toml"
            )
            continue

        # Might be a sub-package of a declared dep (e.g., google.cloud.storage
        # -> google-cloud-storage). Skip common prefixes.
        known_namespace_packages = {
            "google": {
                "google-cloud-storage",
                "google-cloud-pubsub",
                "google-auth",
                "google-api-python-client",
                "google-cloud-build",
                "google-cloud-compute",
                "google-cloud-bigquery",
                "google-cloud-secret-manager",
                "google-cloud-logging",
                "google-cloud-monitoring",
                "gcloud-aio-storage",
                "google-cloud-run",
            },
            "grpc": {"grpcio"},
            "attr": {"attrs"},
            "yaml": {"pyyaml"},
            "PIL": {"pillow"},
            "sklearn": {"scikit-learn"},
            "cv2": {"opencv-python"},
            "bs4": {"beautifulsoup4"},
            "dateutil": {"python-dateutil"},
            "dotenv": {"python-dotenv"},
            "jwt": {"pyjwt"},
            "nacl": {"pynacl"},
            "web3": {"web3"},
            "eth_abi": {"eth-abi"},
            "eth_typing": {"eth-typing"},
            "eth_utils": {"eth-utils"},
            "pkg_resources": {"setuptools"},
            "setuptools": {"setuptools"},
            "werkzeug": {"werkzeug", "flask"},
            "starlette": {"starlette", "fastapi"},
            "uvicorn": {"uvicorn"},
            "httpx": {"httpx"},
        }

        if import_name in known_namespace_packages:
            possible_pkgs = known_namespace_packages[import_name]
            if any(p in declared_pkg_names for p in possible_pkgs):
                if verbose:
                    print(f"  OK namespace: {import_name} -> {possible_pkgs & declared_pkg_names}")
                continue

        # Unknown import not in stdlib, not in deps, not in constraints
        # Only flag if it looks like a real package (not a local module)
        violations.append(
            f"  UNDECLARED: imports '{import_name}' - not in pyproject.toml, not in workspace constraints, not stdlib"
        )

    return violations


def main() -> int:
    """Run the import dependency checker."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="Check only this repo")
    parser.add_argument("--verbose", action="store_true", help="Show all imports")

    class Args(argparse.Namespace):
        repo: str | None = None
        verbose: bool = False

    args = parser.parse_args(namespace=Args())
    repo_name_filter: str | None = args.repo
    verbose: bool = args.verbose

    manifest = load_manifest()
    if "repositories" not in manifest:
        raise KeyError("repositories required in workspace-manifest.json")
    repos = cast(dict[str, object], manifest["repositories"])
    internal_packages = get_internal_package_names(manifest)
    constraints_packages = load_constraints()
    stdlib_modules = get_stdlib_modules()

    total_violations = 0
    repos_checked = 0
    repos_with_violations = 0

    for repo_name in sorted(repos.keys()):
        if repo_name_filter and repo_name != repo_name_filter:
            continue

        repo_dir = WORKSPACE_ROOT / repo_name
        if not repo_dir.exists():
            continue

        pyproject = repo_dir / "pyproject.toml"
        if not pyproject.exists():
            continue

        violations = check_repo(
            repo_name,
            repo_dir,
            internal_packages,
            constraints_packages,
            stdlib_modules,
            verbose,
        )
        repos_checked += 1

        if violations:
            repos_with_violations += 1
            total_violations += len(violations)
            print(f"\n{'=' * 60}")
            print(f"VIOLATIONS in {repo_name} ({len(violations)}):")
            print(f"{'=' * 60}")
            for v in violations:
                print(v)

    # Summary
    print(f"\n{'=' * 60}")
    print("IMPORT DEPENDENCY CHECK SUMMARY")
    print(f"{'=' * 60}")
    print(f"Repos checked: {repos_checked}")
    print(f"Repos with violations: {repos_with_violations}")
    print(f"Total violations: {total_violations}")

    if total_violations > 0:
        print(f"\nFAILED: {total_violations} undeclared import(s) found.")
        print("Fix by adding the missing packages to pyproject.toml [project.dependencies].")
        return 1

    print("\nPASSED: All imports match declared dependencies.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
