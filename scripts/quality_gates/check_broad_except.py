#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""QG STEP 5.5 — broad ``except Exception`` / ``except Exception as X:`` ratchet.

Replaces the old literal-substring regex check (``codex_rg "except Exception:"``)
which was blind to the ``except Exception as X:`` binding form — a Python
``except`` clause followed by ``as <name>:`` puts text between ``Exception`` and
the trailing colon, so the old regex never matched it at all (not excluded, not
tracked — genuinely invisible). AST-based (mirrors
``check_no_fallback_imports.py``) so both forms — ``except Exception:`` and
``except Exception as exc:`` — are caught identically, immune to string-literal
false positives, and comments/docstrings never trigger it.

Per-repo SHRINKING count ratchet: ``broad_except_baseline.yaml`` grandfathers the
audited pre-existing set (2026-08-09 seed for unified-trading-pm: 77
``except Exception as X:`` sites the old regex never saw, plus whatever
``except Exception:`` sites remained after
``pm_qg_broad_except_ratchet_red_finops_regression_2026_08_09.md`` narrowed the
literal-colon inventory). A NEW broad-except site above the baseline fails.
Narrow a try-block's exception type(s) and the baseline ratchets DOWN via
``--update-baseline``.

Usage::

    # per-repo (run by base-service.sh / base-library.sh STEP 5.5):
    python check_broad_except.py --workspace-root <ws> --scope <repo-dir> [--source-dir <pkg>]

    # workspace-wide sweep:
    python check_broad_except.py --workspace-root <ws>

    # ratchet the baseline DOWN after narrowing except clauses:
    python check_broad_except.py --workspace-root <ws> --update-baseline

Exit codes: 0 = clean / at-or-below baseline; 1 = over baseline; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

#: The "grandfathered, intentional" per-line exemption marker (on the ``except`` line).
NOQA_MARKER: Final[str] = "noqa: broad-except"

#: Broad exception names this gate targets — a bare ``except`` (no type) is caught separately.
BROAD_ERROR_NAMES: Final[frozenset[str]] = frozenset({"Exception", "BaseException"})

#: Top-level dir names to skip when walking. scripts/ stays IN scope (mirrors
#: check_no_fallback_imports.py — that's exactly where this issue's 77-site
#: sweep found the binding-form blind spot).
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
        "site-packages",
        "tests",
        ".claude",
        ".cursor",
    }
)

#: Path-fragment patterns that indicate archived / generated trees.
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
)

#: Test-file basename patterns (skipped).
TEST_FILE_PREFIXES: Final[tuple[str, ...]] = ("test_",)
TEST_FILE_SUFFIXES: Final[tuple[str, ...]] = ("_test.py",)


# ── Baseline ─────────────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "broad_except_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    """Per-repo allowed counts of broad-except sites."""

    counts: dict[str, int] = field(default_factory=dict)
    note: str = ""

    def allowed(self, repo: str) -> int:
        return int(self.counts.get(repo, 0))


def load_baseline(path: Path | None = None) -> Baseline:
    baseline_file = path if path is not None else _baseline_path()
    if not baseline_file.exists():
        return Baseline()
    raw = yaml.safe_load(baseline_file.read_text(encoding="utf-8")) or {}
    repos_raw = raw.get("repos") or {}
    counts: dict[str, int] = {}
    for repo, val in repos_raw.items():
        if isinstance(val, dict):
            counts[str(repo)] = int(val.get("count", 0))
        else:
            counts[str(repo)] = int(val)
    return Baseline(counts=counts, note=str(raw.get("note") or ""))


def write_baseline(counts: dict[str, int], existing: Baseline, path: Path | None = None) -> None:
    """Persist a new baseline. Counts are clamped DOWN — never raised above the
    existing baseline (a higher count means a new broad-except site landed;
    narrow it, don't bake it in)."""
    baseline_file = path if path is not None else _baseline_path()
    merged: dict[str, dict[str, int]] = {}
    all_repos = set(counts) | set(existing.counts)
    for repo in sorted(all_repos):
        if repo not in counts:
            # Not scanned this run (scoped --update-baseline) — carry the existing
            # row forward verbatim (same defect class as check_ruff_rule_ratchet,
            # incident 2026-06-10 — treating unobserved as 0 would zero the fleet).
            merged[repo] = {"count": existing.allowed(repo)}
            continue
        observed = int(counts[repo])
        prior = existing.allowed(repo)
        merged[repo] = {"count": min(observed, prior) if repo in existing.counts else observed}
    header = (
        "# Baseline for QG STEP 5.5 — broad `except Exception[ as X]:` ratchet.\n"
        "#\n"
        "# This is a SHRINKING ratchet. `repos[<repo>].count` is the number of\n"
        "# `except Exception:` / `except Exception as X:` sites (WITHOUT a\n"
        "# `# noqa: broad-except` marker) the gate tolerates in that repo (tests/\n"
        "# excluded; scripts/ INCLUDED). A repo whose live count EXCEEDS its\n"
        "# baseline fails CI — a NEW broad-except site landed; narrow to the\n"
        "# specific exception type(s) the block actually expects, or add\n"
        "# `# noqa: broad-except` on the `except` line with a one-line reason.\n"
        "#\n"
        "# LOWER a count (re-run `--update-baseline`) the moment sites are narrowed.\n"
        "# NEVER raise a count. Repos not listed default to count=0.\n"
        "#\n"
        "# SSOT: plans/active/issues/broad_except_as_binding_form_blind_spot_2026_08_09.md,\n"
        "# plans/active/issues/pm_qg_broad_except_ratchet_red_finops_regression_2026_08_09.md.\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note or "Seeded 2026-08-09 — broad_except_as_binding_form_blind_spot (QG STEP 5.5).",
            "repos": merged,
        },
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
    )
    _ = baseline_file.write_text(header + body, encoding="utf-8")


# ── Scanning ─────────────────────────────────────────────────────────────────


def _is_excluded_path(path: Path) -> bool:
    if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
        return True
    posix = path.as_posix()
    if any(frag in posix for frag in EXCLUDE_PATH_FRAGMENTS):
        return True
    name = path.name
    if any(name.startswith(p) for p in TEST_FILE_PREFIXES):
        return True
    return bool(any(name.endswith(s) for s in TEST_FILE_SUFFIXES))


def _iter_py_files(root: Path) -> Iterator[Path]:
    if root.is_file() and root.suffix == ".py" and not _is_excluded_path(root):
        yield root
        return
    for path in root.rglob("*.py"):
        if _is_excluded_path(path):
            continue
        yield path


def _handler_catches_broad(handler: ast.ExceptHandler) -> bool:
    """True for a bare ``except`` (no type) or ``except Exception[ as X]:`` /
    ``except BaseException[ as X]:`` (alone or in a tuple, incl. dotted forms
    like ``except builtins.Exception:``). The ``as X`` binding, if present, is
    irrelevant to the AST shape — ``ast.ExceptHandler.type`` already excludes it,
    which is exactly why the old regex (matching raw source text) missed this form."""
    spec = handler.type
    if spec is None:
        return True  # bare except
    candidates: list[ast.expr] = list(spec.elts) if isinstance(spec, ast.Tuple) else [spec]
    for cand in candidates:
        if isinstance(cand, ast.Name) and cand.id in BROAD_ERROR_NAMES:
            return True
        if isinstance(cand, ast.Attribute) and cand.attr in BROAD_ERROR_NAMES:
            return True
    return False


def _line_has_noqa(file_lines: list[str], lineno: int) -> bool:
    if lineno < 1 or lineno > len(file_lines):
        return False
    return NOQA_MARKER in file_lines[lineno - 1].lower()


def find_broad_excepts(source_path: Path) -> list[tuple[int, str]]:
    """Return [(lineno, description)] of broad-except sites in a file."""
    try:
        source = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError:
        return []

    file_lines = source.splitlines()
    violations: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if not _handler_catches_broad(node):
            continue
        if _line_has_noqa(file_lines, node.lineno):
            continue
        binds = f" as {node.name}" if node.name else ""
        desc = "bare except" if node.type is None else f"except Exception{binds}"
        violations.append((node.lineno, desc))

    return sorted(violations)


@dataclass(frozen=True)
class RepoScan:
    repo: str
    count: int
    sites: list[tuple[str, int, str]]  # (repo-relative-file, line, description)


def scan_repo(scan_root: Path, repo_name: str, repo_root: Path | None = None) -> RepoScan:
    rel_base = repo_root if repo_root is not None else scan_root
    sites: list[tuple[str, int, str]] = []
    for py in _iter_py_files(scan_root):
        for lineno, desc in find_broad_excepts(py):
            rel = py.relative_to(rel_base).as_posix() if py.is_relative_to(rel_base) else py.as_posix()
            sites.append((rel, lineno, desc))
    return RepoScan(repo=repo_name, count=len(sites), sites=sorted(sites))


# ── Scope resolution ─────────────────────────────────────────────────────────


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    """Return [(repo_name, scan_root)]. --scope → that repo only (optionally
    narrowed to --source-dir under it). Else every immediate git-repo sub-dir."""
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_broad_except] --scope {scope!r} not a dir under {workspace_root}", file=sys.stderr)
            return []
        scan_root = repo_root / source_dir if source_dir else repo_root
        if not scan_root.exists():
            scan_root = repo_root
        return [(scope, scan_root)]
    out: list[tuple[str, Path]] = []
    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name in EXCLUDE_DIR_NAMES or child.name.startswith("."):
            continue
        if (child / ".git").exists():
            out.append((child.name, child))
    return out


# ── main ─────────────────────────────────────────────────────────────────────


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="broad `except Exception[ as X]:` ratchet (QG STEP 5.5).")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name (per-repo QG mode).")
    parser.add_argument(
        "--source-dir", default=None, help="Sub-dir under --scope to narrow the scan to (e.g. the package dir)."
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Rewrite the baseline with the observed counts (clamped DOWN — never raised).",
    )
    parser.add_argument(
        "--baseline-file",
        type=Path,
        default=None,
        help="Override the baseline yaml path (unit tests only).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    baseline_file: Path | None = args.baseline_file
    baseline = load_baseline(baseline_file)
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print("[check_broad_except] no repos in scope.", file=sys.stderr)
        return 0  # nothing to check — not a failure

    observed: dict[str, int] = {}
    failures: list[str] = []
    info_lines: list[str] = []
    for repo_name, scan_root in scopes:
        repo_root = workspace_root / repo_name if (workspace_root / repo_name).is_dir() else scan_root
        scan = scan_repo(scan_root, repo_name, repo_root=repo_root)
        observed[repo_name] = scan.count
        allowed = baseline.allowed(repo_name)
        if scan.count > allowed:
            over = scan.sites[allowed:] if allowed < len(scan.sites) else scan.sites
            sites_str = "; ".join(f"{f}:{ln}" for f, ln, _desc in over[:20])
            failures.append(
                f"[FAIL] {repo_name}: {scan.count} broad-except site(s) > baseline {allowed}. "
                f"New/over-baseline site(s): {sites_str}" + (" ..." if len(over) > 20 else "")
            )
        elif scan.count < allowed:
            info_lines.append(
                f"[WARN] {repo_name}: {scan.count} < baseline {allowed} — ratchet the baseline DOWN "
                f"(re-run `--update-baseline`)."
            )
        else:
            info_lines.append(f"[OK]   {repo_name}: {scan.count} (== baseline)")

    if args.update_baseline:
        write_baseline(observed, baseline, baseline_file)
        print(f"[check_broad_except] baseline updated at {baseline_file or _baseline_path()}")
        for line in sorted(f"  {r}: {c}" for r, c in observed.items()):
            print(line)
        return 0

    for line in info_lines:
        print(line)
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(
            "\n→ Narrow the except clause to the specific exception type(s) the block actually expects "
            "(e.g. `except (ImportError, GoogleAPICallError) as exc:`), never a bare/broad "
            "`except Exception[ as X]:`. For a genuinely-intentional broad catch (e.g. a top-level "
            "best-effort handler) add `# noqa: broad-except` on the `except` line with a one-line reason. "
            "SSOT: unified-trading-pm/scripts/quality_gates/broad_except_baseline.yaml (NEVER raise a count).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
