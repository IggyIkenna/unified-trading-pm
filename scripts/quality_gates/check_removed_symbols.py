"""AST-walk QG STEP — workspace-wide removed-symbol detection.

Enforces CLAUDE.md "Citadel-Grade Planning Standards § 6 Downstream Consumer
Updates (extended 2026-05-08 to cover non-library refactors)":

    > grep across the workspace for the removed/renamed symbol is mandatory;
    > the AST-walk pattern from QG STEP 5.64 (workspace-wide callsite
    > enumeration) is the canonical implementation shape.

How it works
------------
1. Loads `removed_symbols_manifest.yaml` (the workspace SSOT for symbols
   that have been removed or renamed by a refactor).
2. AST-walks every `.py` file in the workspace (excluding venvs, build
   artefacts, archived dirs).
3. For each file, parses imports + attribute accesses; matches them
   against the manifest.
4. On match: emits an actionable error with `file:line` + the documented
   `successor:`. Exit 1 on any `removed` finding (errors); `pending_removal`
   entries surface as warnings (informational, exit-clean).

Reference incident
------------------
2026-05-01 → 2026-05-08 silent rot of e2e-testing/scripts/defi/colocated_engine.py:
strategy-service V1-RETIRE Phase 2 removed `get_strategy_factories`; the
import broke for 7 days because the script was outside any service's QG.
This step would have caught it in <1 minute on the next PR.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

#: Top-level directories to skip when walking the workspace.
EXCLUDE_DIR_NAMES: Final[frozenset[str]] = frozenset(
    {
        ".venv",
        ".venv-workspace",
        "venv",
        "node_modules",
        "build",
        "dist",
        "__pycache__",
        ".git",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "htmlcov",
        ".tox",
        ".tabs",  # per-slot reference clones — duplicates of the repos; never scan them
        "site-packages",
    }
)

#: Path-fragment patterns that indicate archived / generated trees.
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
)

#: Allowed `status:` values per manifest entry.
VALID_STATUS: Final[frozenset[str]] = frozenset({"removed", "pending_removal", "renamed"})

#: Required keys per manifest entry.
REQUIRED_KEYS: Final[tuple[str, ...]] = (
    "symbol",
    "removed_at",
    "removed_by_commit",
    "successor",
    "reason",
    "status",
)


# ── Data shapes ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RemovedSymbol:
    """A single manifest entry."""

    symbol: str
    removed_at: _date
    removed_by_commit: str
    successor: str
    reason: str
    status: str  # "removed" | "pending_removal" | "renamed"

    @property
    def module_path(self) -> str:
        """Top-level dotted path up to the last component (the symbol name)."""
        return ".".join(self.symbol.split(".")[:-1])

    @property
    def name(self) -> str:
        """Final component of the dotted path (function/class/attr name)."""
        return self.symbol.split(".")[-1]


@dataclass(frozen=True)
class Finding:
    """A single match between a source file and a removed symbol."""

    file_path: Path
    line: int
    matched_symbol: RemovedSymbol
    snippet: str  # 1-line context for the operator


# ── Manifest loading + validation ────────────────────────────────────────────


def load_manifest(manifest_path: Path) -> list[RemovedSymbol]:
    """Parse + validate the YAML manifest. Raises on schema violations."""
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Removed-symbols manifest not found: {manifest_path}")

    raw_text = manifest_path.read_text(encoding="utf-8")
    raw_yaml = yaml.safe_load(raw_text)

    if not isinstance(raw_yaml, dict) or "removed_symbols" not in raw_yaml:
        raise ValueError(f"Manifest {manifest_path} must be a YAML mapping with key 'removed_symbols'.")

    entries_raw = raw_yaml["removed_symbols"]
    if not isinstance(entries_raw, list):
        raise ValueError(f"Manifest 'removed_symbols' must be a list, got {type(entries_raw)!r}.")

    out: list[RemovedSymbol] = []
    for idx, entry in enumerate(entries_raw):
        if not isinstance(entry, dict):
            raise ValueError(f"Manifest entry #{idx} must be a mapping, got {type(entry)!r}.")
        for key in REQUIRED_KEYS:
            if key not in entry:
                raise ValueError(f"Manifest entry #{idx} missing required key {key!r}: {entry!r}")
        status = entry["status"]
        if status not in VALID_STATUS:
            raise ValueError(
                f"Manifest entry #{idx} has invalid status {status!r}; must be one of {sorted(VALID_STATUS)}."
            )
        removed_at = entry["removed_at"]
        if not isinstance(removed_at, _date):
            raise ValueError(
                f"Manifest entry #{idx} 'removed_at' must be a YAML date (YYYY-MM-DD), "
                f"got {type(removed_at)!r}: {removed_at!r}"
            )
        symbol = entry["symbol"]
        if not isinstance(symbol, str) or "." not in symbol:
            raise ValueError(f"Manifest entry #{idx} 'symbol' must be a dotted path, got {symbol!r}.")
        out.append(
            RemovedSymbol(
                symbol=symbol,
                removed_at=removed_at,
                removed_by_commit=str(entry["removed_by_commit"]),
                successor=str(entry["successor"]),
                reason=str(entry["reason"]),
                status=status,
            )
        )
    return out


# ── File walker ──────────────────────────────────────────────────────────────


def _is_excluded(path: Path, workspace_root: Path) -> bool:
    """Return True if the path lives under an excluded directory or fragment."""
    try:
        rel = path.relative_to(workspace_root)
    except ValueError:
        # Outside workspace root — exclude defensively.
        return True
    parts = rel.parts
    for part in parts:
        if part in EXCLUDE_DIR_NAMES:
            return True
        # Also catch ".venv*" siblings (e.g. ".venv-py313").
        if part.startswith(".venv"):
            return True
    rel_str = str(rel).replace("\\", "/")
    return any(fragment in f"/{rel_str}/" for fragment in EXCLUDE_PATH_FRAGMENTS)


def iter_python_files(workspace_root: Path) -> Iterable[Path]:
    """Yield every non-excluded .py file under the workspace."""
    for path in workspace_root.rglob("*.py"):
        if path.is_file() and not _is_excluded(path, workspace_root):
            yield path


# ── AST scan ─────────────────────────────────────────────────────────────────


def _scan_file_for_symbols(file_path: Path, manifest: list[RemovedSymbol], source_text: str) -> list[Finding]:
    """Return findings for ONE file (pure function — process-pool safe)."""
    try:
        tree = ast.parse(source_text, filename=str(file_path))
    except (SyntaxError, ValueError):
        # Syntax errors are someone else's problem — basedpyright/ruff
        # will catch them. We just skip unparseable files.
        return []

    # Index manifest entries by their last component for O(1) lookup
    # during AST walk; a name-match still needs full-path verification.
    by_name: dict[str, list[RemovedSymbol]] = {}
    by_module_path: dict[str, list[RemovedSymbol]] = {}
    for sym in manifest:
        by_name.setdefault(sym.name, []).append(sym)
        by_module_path.setdefault(sym.module_path, []).append(sym)
        # Also index the full symbol path in case the symbol IS a module.
        by_module_path.setdefault(sym.symbol, []).append(sym)

    source_lines = source_text.splitlines()

    def _snippet(lineno: int) -> str:
        if 1 <= lineno <= len(source_lines):
            return source_lines[lineno - 1].strip()[:180]
        return ""

    findings: list[Finding] = []
    # Dedup at (lineno, symbol) granularity so a single import-line can't
    # produce two findings for the same removed symbol from overlapping
    # match patterns (by_name + by_module_path both hit the same site).
    seen: set[tuple[int, str]] = set()

    def _add(node_lineno: int, sym: RemovedSymbol) -> None:
        key = (node_lineno, sym.symbol)
        if key in seen:
            return
        seen.add(key)
        findings.append(
            Finding(
                file_path=file_path,
                line=node_lineno,
                matched_symbol=sym,
                snippet=_snippet(node_lineno),
            )
        )

    for node in ast.walk(tree):
        # Pattern 1: `from <module> import <name>`
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            module = node.module
            for alias in node.names:
                imported_name = alias.name
                # Match `from manifest.module_path import name_of_symbol`.
                candidates = by_name.get(imported_name, [])
                for sym in candidates:
                    if sym.module_path == module or module.startswith(sym.module_path + "."):
                        _add(node.lineno, sym)
                # Match `from parent_pkg import <removed_module>` where
                # `<parent_pkg>.<removed_module>` is the manifest entry
                # (whole-module removal).
                full_path = f"{module}.{imported_name}"
                module_candidates = by_module_path.get(full_path, [])
                for sym in module_candidates:
                    if sym.symbol == full_path:
                        _add(node.lineno, sym)
        # Pattern 2: `import <module>` (top-level or dotted).
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_module = alias.name
                # Match an exact module path that's been removed.
                module_candidates = by_module_path.get(imported_module, [])
                for sym in module_candidates:
                    if sym.symbol == imported_module:
                        _add(node.lineno, sym)
        # Pattern 3: attribute access `<Receiver>.removed_method(...)`.
        #
        # Fires ONLY when:
        #   - the attr name matches a manifest entry's last component
        #   - the entry has at least 3 dotted components (i.e. a class
        #     method or class attribute, not a module-level symbol)
        #   - the immediate `value` of the Attribute node is a Name
        #     whose id equals the SECOND-TO-LAST component of the
        #     symbol (the class name)
        #
        # Why so strict: `args.client`, `set.add()`, `list.append()`
        # would otherwise produce thousands of false positives. We
        # only flag callsites where the receiver is named the same as
        # the class in the manifest entry — e.g. for
        # `unified_trading_library.manifest.ManifestWriter.add`, only
        # `ManifestWriter.add(` syntactic sites fire (or
        # `<var named manifest_writer>.add(` if the var name happens
        # to match — which we accept because it's still a strong
        # textual signal). For looser detection of method renames
        # against arbitrary receiver names, ship a per-service
        # basedpyright type-check instead — this AST pass is the
        # workspace-wide first-pass net.
        elif isinstance(node, ast.Attribute):
            attr_candidates = by_name.get(node.attr, [])
            if not attr_candidates:
                continue
            # The Attribute node's value is the receiver expression.
            value = node.value
            if isinstance(value, ast.Name):
                receiver_name = value.id
            elif isinstance(value, ast.Attribute):
                # `pkg.ManifestWriter.add` — flatten to the trailing
                # attr name.
                receiver_name = value.attr
            else:
                continue
            for sym in attr_candidates:
                if sym.symbol.count(".") < 2:
                    continue
                # Compare to the second-to-last component (the class
                # name in `module.Class.method`).
                expected_receiver = sym.symbol.split(".")[-2]
                # Tolerate snake_case variable names that match the
                # class case-insensitively (e.g. `manifest_writer.add`
                # for `ManifestWriter.add`).
                if (
                    receiver_name == expected_receiver
                    or receiver_name.lower() == expected_receiver.lower()
                    or receiver_name.replace("_", "").lower() == expected_receiver.lower()
                ):
                    _add(node.lineno, sym)

    return findings


def _scan_one_file_worker(args: tuple[Path, list[RemovedSymbol]]) -> list[Finding]:
    """Process-pool-safe wrapper that reads the source itself."""
    file_path, manifest = args
    try:
        source_text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return _scan_file_for_symbols(file_path, manifest, source_text)


def scan_workspace(
    workspace_root: Path,
    manifest: list[RemovedSymbol],
    *,
    max_workers: int | None = None,
) -> list[Finding]:
    """AST-walk every Python file in the workspace; return all findings."""
    files = list(iter_python_files(workspace_root))
    findings: list[Finding] = []

    if not files:
        return findings

    # Skip the parallelism overhead if the tree is small.
    if len(files) < 200 or max_workers == 1:
        for fpath in files:
            findings.extend(_scan_one_file_worker((fpath, manifest)))
        return findings

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_scan_one_file_worker, (fp, manifest)): fp for fp in files}
        for future in as_completed(futures):
            findings.extend(future.result())
    return findings


# ── Reporting ────────────────────────────────────────────────────────────────


def format_finding(finding: Finding, workspace_root: Path) -> str:
    """Render a single finding as an actionable QG error line."""
    try:
        rel = finding.file_path.relative_to(workspace_root)
    except ValueError:
        rel = finding.file_path
    sym = finding.matched_symbol
    severity = "ERROR" if sym.status == "removed" else "WARN"
    return (
        f"  [{severity}] {rel}:{finding.line}\n"
        f"      Removed symbol: {sym.symbol}\n"
        f"      Status:         {sym.status}\n"
        f"      Reason:         {sym.reason}\n"
        f"      Successor:      {sym.successor}\n"
        f"      Source line:    {finding.snippet}\n"
    )


# ── CLI entrypoint ───────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "AST-walk QG STEP 5.66 — detect imports/uses of symbols listed "
            "in removed_symbols_manifest.yaml across the workspace."
        )
    )
    _ = parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help=(
            "Workspace root (default: ascend from this script until a sibling repo is found, "
            "or use $UNIFIED_TRADING_WORKSPACE_ROOT)."
        ),
    )
    _ = parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help=("Path to removed_symbols_manifest.yaml (default: alongside this script)."),
    )
    _ = parser.add_argument(
        "--validate-manifest",
        action="store_true",
        help="Parse + validate the manifest only; exit without scanning.",
    )
    _ = parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Process-pool size (default: os.cpu_count()).",
    )
    _ = parser.add_argument(
        "--scope",
        type=Path,
        default=None,
        help=(
            "Scope the scan to a single sub-directory (relative to workspace root). "
            "Used by per-repo QG to scan only the calling repo."
        ),
    )
    args = parser.parse_args(argv)

    # Resolve manifest path.
    script_dir = Path(__file__).resolve().parent
    manifest_path = args.manifest if args.manifest is not None else (script_dir / "removed_symbols_manifest.yaml")

    try:
        manifest = load_manifest(manifest_path)
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        print(f"FAIL — manifest invalid: {exc}", file=sys.stderr)
        return 2

    print(f"Loaded {len(manifest)} entries from {manifest_path}.", file=sys.stderr)

    if args.validate_manifest:
        print("Manifest validation: OK.", file=sys.stderr)
        return 0

    # Resolve workspace root.
    if args.workspace_root is not None:
        workspace_root = args.workspace_root.resolve()
    else:
        # Heuristic: ascend from script_dir until we find the workspace
        # (parent of unified-trading-pm).
        workspace_root = script_dir
        while workspace_root != workspace_root.parent:
            if (workspace_root / "unified-trading-pm").is_dir():
                break
            workspace_root = workspace_root.parent
        else:  # pragma: no cover — defensive fallback
            workspace_root = script_dir

    # Honour --scope (per-repo invocation from base-service.sh).
    scan_root = workspace_root
    if args.scope is not None:
        scoped = (workspace_root / args.scope).resolve()
        if scoped.is_dir():
            scan_root = scoped
        else:
            print(
                f"WARN — --scope path not found: {scoped}; falling back to workspace.",
                file=sys.stderr,
            )

    print(f"Scanning {scan_root} ...", file=sys.stderr)
    findings = scan_workspace(scan_root, manifest, max_workers=args.workers)

    errors = [f for f in findings if f.matched_symbol.status == "removed"]
    warnings = [f for f in findings if f.matched_symbol.status == "pending_removal"]

    if findings:
        print("", file=sys.stderr)
        print(
            f"Removed-symbol findings: {len(errors)} ERROR, {len(warnings)} WARN.",
            file=sys.stderr,
        )
        print("", file=sys.stderr)
        for f in findings:
            print(format_finding(f, workspace_root), file=sys.stderr)

    if errors:
        print(
            "FAIL — workspace contains references to symbols marked `removed` "
            "in removed_symbols_manifest.yaml. Update the consumers per the "
            "documented `successor:` for each entry, or — if the symbol was "
            "incorrectly added to the manifest — remove the entry and re-run.",
            file=sys.stderr,
        )
        return 1

    if not findings:
        print("OK — no removed-symbol references in workspace.", file=sys.stderr)
    else:
        print(
            "OK — only `pending_removal` findings (warnings, non-blocking). Migrate before status flips to `removed`.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
