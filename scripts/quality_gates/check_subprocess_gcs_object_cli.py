#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""QG STEP 5.105 — subprocess/os.system GCS/S3 OBJECT-CLI ratchet.

Enforces CLAUDE.md "Writing STORAGE code?": GCS/S3 OBJECT operations (list, describe,
copy, move, delete) go through UTL's `gcs_copy_object`/`gcs_delete_object`/
`gcs_describe_object`/`list_blobs` (`unified_trading_library.cloud_interface`) — never
a subprocess/`os.system` call shelling out to `gcloud storage`/`gsutil`/`aws s3`/
`aws s3api`. This is a DIFFERENT, narrower concern than STEP 5.69 (inline `gs://`/`s3://`
URI f-string construction) and catches a gap that check found nothing about: STEP 5.69
excludes `scripts/` entirely, and neither check inspects subprocess ARGUMENTS at all.

Found 2026-07-27 via behavioral testing of the delete-reversibility governance work: a
workspace-wide grep turned up real, live violations — including `deployment_service/
cli/handlers/maintenance_handler.py` (production service code, not a dead script)
running `gsutil rm` in a loop to delete GCS objects.

Scope is deliberately OBJECT-level only — never flags BUCKET-level admin operations
(`gcloud storage buckets ...`, `gsutil mb/rb/versioning/lifecycle/iam/label/...`,
`aws s3 rb`, `aws s3api {create,delete,get,put,list}-bucket*`), since those have no
UTL equivalent and are legitimate infra/ops CLI usage (bucket creation, soft-delete
policy, IAM — the same class of command this session's own IAM-self-service and
delete-safety work already treats as fine for an agent to run directly).

Shape — **baseline ratchet** (NOT zero-tolerance from day 1), mirroring STEP 5.69 /
5.70 / 5.103's shape exactly:

  1. Load `subprocess_gcs_object_cli_baseline.yaml` — a per-repo count of the
     CURRENTLY-KNOWN subprocess/os.system GCS/S3 object-CLI call sites (excluding
     lines carrying `# noqa: gcs-cli` — the grandfathered, intentional exemption).
  2. AST-walk every `.py` file under the given source dir(s) (scripts/ + tests/ ARE
     scanned here, unlike STEP 5.69 — this check's whole point is the scripts/ gap),
     looking for `subprocess.{run,call,check_call,check_output,Popen}(...)` /
     `os.system(...)` calls whose command argument (a list literal, or a string for
     shell=True) contains an object-level CLI+verb combination.
  3. If a repo's count is `<=` its baseline → OK. `<` baseline → WARNING (ratchet
     down). `>` baseline → ERROR (exit 1) — a NEW site landed; migrate to the UTL
     wrapper or add `# noqa: gcs-cli` with a one-line reason.

The baseline ONLY shrinks. Repos not listed default to count=0 (zero tolerance).

Usage::

    # per-repo (run by base-service.sh STEP 5.105):
    python check_subprocess_gcs_object_cli.py --workspace-root <ws> --scope <repo-dir> --source-dir <pkg>

    # workspace-wide sweep:
    python check_subprocess_gcs_object_cli.py --workspace-root <ws>

    # ratchet the baseline DOWN after a migration:
    python check_subprocess_gcs_object_cli.py --workspace-root <ws> --update-baseline
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

NOQA_MARKER: Final[str] = "noqa: gcs-cli"

#: Object-level verbs per CLI. Deliberately excludes bucket-admin subcommands
#: (buckets/mb/rb/versioning/lifecycle/iam/label/acl/cors/logging/notification/
#: retention/rpo/ubla/web) — those have no UTL equivalent and are legitimate.
_GCLOUD_STORAGE_OBJECT_VERBS: Final[frozenset[str]] = frozenset({"cp", "mv", "rm", "rsync", "ls", "cat"})
_GSUTIL_OBJECT_VERBS: Final[frozenset[str]] = frozenset({"cp", "mv", "rm", "rsync", "ls", "cat"})
_AWS_S3_OBJECT_VERBS: Final[frozenset[str]] = frozenset({"cp", "mv", "rm", "sync", "ls"})
_AWS_S3API_OBJECT_OPS: Final[frozenset[str]] = frozenset(
    {"get-object", "put-object", "delete-object", "copy-object", "head-object"}
)

_SUBPROCESS_FUNCS: Final[frozenset[str]] = frozenset({"run", "call", "check_call", "check_output", "Popen"})

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
        # NOTE: unlike check_inline_bucket_uri.py, scripts/ and tests/ are NOT
        # excluded here — the whole point of this check is the scripts/ gap.
    }
)

EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
    "/.tabs/",
    "/.claude/worktrees/",
)


# ── Command-string classification ───────────────────────────────────────────


def _tokens_from_string(s: str) -> list[str]:
    """Best-effort tokenize a shell=True command string (no quoting handled beyond
    plain whitespace-split — good enough for the CLI-tool + verb prefix we check)."""
    return s.split()


def _classify_tokens(tokens: list[str]) -> str | None:
    """Return a human-readable reason if ``tokens`` (a subprocess argv-shaped list)
    invokes an OBJECT-level GCS/S3 CLI operation, else ``None``."""
    if not tokens:
        return None
    head = tokens[0]

    if head == "gcloud" and len(tokens) >= 3 and tokens[1] == "storage":
        verb = tokens[2]
        if verb in _GCLOUD_STORAGE_OBJECT_VERBS:
            return f"gcloud storage {verb} (GCS object op)"
        return None  # buckets / other subcommands — bucket-admin, not flagged

    if head == "gsutil" and len(tokens) >= 2:
        verb = tokens[1]
        if verb in _GSUTIL_OBJECT_VERBS:
            return f"gsutil {verb} (GCS object op)"
        return None  # mb/rb/versioning/lifecycle/iam/etc — bucket-admin, not flagged

    if head == "aws" and len(tokens) >= 3 and tokens[1] == "s3":
        verb = tokens[2]
        if verb in _AWS_S3_OBJECT_VERBS:
            return f"aws s3 {verb} (S3 object op)"
        return None  # rb — bucket-admin, not flagged

    if head == "aws" and len(tokens) >= 3 and tokens[1] == "s3api":
        op = tokens[2]
        if op in _AWS_S3API_OBJECT_OPS:
            return f"aws s3api {op} (S3 object op)"
        return None  # create/delete/get/put/list-bucket* — bucket-admin, not flagged

    return None


#: sentinel standing in for a non-literal list element (an f-string, a
#: variable, a call result, ...) so token POSITIONS are preserved even though
#: that one token's real value is unknown. Classification only ever inspects
#: tokens[0..2] (tool + verb), which in every real call site observed in this
#: codebase are literal strings — only trailing path/arg elements are dynamic.
_DYNAMIC_TOKEN: Final[str] = "\x00<dynamic>\x00"


def _literal_tokens_from_value(value: ast.expr) -> list[str] | None:
    """Extract tokens from a List/Tuple-of-strings or a literal string AST node.
    Returns ``None`` if ``value`` isn't one of those shapes at all (e.g. it's a
    bare variable reference or a function call — handled by the caller, which
    tries to resolve a Name via its nearest preceding assignment first)."""
    if isinstance(value, (ast.List, ast.Tuple)):
        if not value.elts:
            return None
        return [
            elt.value if isinstance(elt, ast.Constant) and isinstance(elt.value, str) else _DYNAMIC_TOKEN
            for elt in value.elts
        ]
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return _tokens_from_string(value.value)
    return None


def _collect_name_assignments(tree: ast.AST) -> list[tuple[int, str, ast.expr]]:
    """All ``name = <expr>`` assignments in the file, as (lineno, name, value).
    Deliberately NOT scoped per-function — see ``_resolve_command_tokens`` for
    why a whole-file nearest-preceding-line lookup is good enough here."""
    out: list[tuple[int, str, ast.expr]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            out.append((node.lineno, node.targets[0].id, node.value))
    out.sort(key=lambda t: t[0])
    return out


def _resolve_command_tokens(call: ast.Call, assignments: list[tuple[int, str, ast.expr]]) -> list[str] | None:
    """Extract the command tokens for a ``subprocess.run(...)``/``os.system(...)``
    call. Handles both the literal-inline form AND the (dominant, in this
    codebase) two-step idiom ``cmd = ["gsutil", "rm", path]; subprocess.run(cmd, ...)``
    — resolved via the nearest PRECEDING assignment (by line number) to that
    name anywhere in the file. Not real scope/data-flow analysis (a linter, not
    a compiler): this is a heuristic that holds as long as the variable is
    assigned earlier in the same function right before the call, which is the
    only pattern observed in every real call site checked this session. A
    genuinely dynamic command (built across branches, reassigned from an
    unrelated function scope) is a false-negative, not a false-positive — same
    trade-off STEP 5.69 makes for non-f-string URI builds."""
    if not call.args:
        return None
    first = call.args[0]
    direct = _literal_tokens_from_value(first)
    if direct is not None:
        return direct
    if isinstance(first, ast.Name):
        call_lineno = getattr(call, "lineno", None)
        if call_lineno is None:
            return None
        best: ast.expr | None = None
        best_lineno = -1
        for lineno, name, value in assignments:
            if name == first.id and best_lineno < lineno <= call_lineno:
                best, best_lineno = value, lineno
        if best is not None:
            return _literal_tokens_from_value(best)
    return None


def _is_subprocess_or_system_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name) and func.value.id == "subprocess" and func.attr in _SUBPROCESS_FUNCS:
            return True
        if isinstance(func.value, ast.Name) and func.value.id == "os" and func.attr == "system":
            return True
    elif isinstance(func, ast.Name):
        # `from subprocess import run` style — bare name match on the common ones.
        if func.id in _SUBPROCESS_FUNCS:
            return True
    return False


# ── Scanning ─────────────────────────────────────────────────────────────────


def _is_excluded_path(path: Path, *, scoped: bool = False) -> bool:
    """Return True if ``path`` should not be scanned.

    ``scoped`` is True for an explicitly-named repo (``--scope``). The scoped
    repo's OWN checkout path must never be excluded merely because it lives
    under a workspace ``.tabs/`` dir (a per-slot worktree) — that would silently
    blind STEP 5.105 in every slot-local QG run (class-(f) gap, surfaced
    2026-08-10: the restamp_tradfi_cme_future_blank_instrument_id script shipped
    because the ``/.tabs/`` fragment made the check a no-op locally, so only CI
    caught it on an unrelated SHA). The ``/.tabs/`` fragment remains in effect
    for unscoped workspace-wide sweeps, where it deliberately avoids re-scanning
    sibling slot checkouts.
    """
    if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
        return True
    posix = path.as_posix()
    fragments = EXCLUDE_PATH_FRAGMENTS
    if scoped:
        fragments = tuple(f for f in fragments if f != "/.tabs/")
    return any(frag in posix for frag in fragments)


def _iter_py_files(root: Path, *, scoped: bool = False) -> Iterator[Path]:
    if root.is_file() and root.suffix == ".py" and not _is_excluded_path(root, scoped=scoped):
        yield root
        return
    for path in root.rglob("*.py"):
        if _is_excluded_path(path, scoped=scoped):
            continue
        yield path


def count_hits_in_file(path: Path) -> list[tuple[int, str]]:
    """Return [(lineno, reason), ...] for object-level GCS/S3 CLI subprocess call
    sites in ``path`` not carrying a ``# noqa: gcs-cli`` marker."""
    hits: list[tuple[int, str]] = []
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return hits
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return hits  # unlike STEP 5.69 there is no regex fallback — AST-only, skip unparseable files

    source_lines = source.splitlines()
    assignments = _collect_name_assignments(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_subprocess_or_system_call(node):
            continue
        tokens = _resolve_command_tokens(node, assignments)
        if not tokens:
            continue
        reason = _classify_tokens(tokens)
        if reason is None:
            continue
        lineno = getattr(node, "lineno", None)
        if lineno is None:
            continue
        source_line = source_lines[lineno - 1] if 0 < lineno <= len(source_lines) else ""
        if NOQA_MARKER in source_line:
            continue
        hits.append((lineno, reason))
    return sorted(hits)


@dataclass(frozen=True)
class RepoScan:
    repo: str
    count: int
    sites: list[tuple[str, int, str]]  # (repo-relative-file, line, reason)


def scan_repo(repo_root: Path, repo_name: str, *, scoped: bool = False) -> RepoScan:
    sites: list[tuple[str, int, str]] = []
    for py in _iter_py_files(repo_root, scoped=scoped):
        for lineno, reason in count_hits_in_file(py):
            rel = py.relative_to(repo_root).as_posix() if py.is_relative_to(repo_root) else py.as_posix()
            sites.append((rel, lineno, reason))
    return RepoScan(repo=repo_name, count=len(sites), sites=sorted(sites))


# ── Baseline ─────────────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "subprocess_gcs_object_cli_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    counts: dict[str, int] = field(default_factory=dict)
    note: str = ""

    def allowed(self, repo: str) -> int:
        return int(self.counts.get(repo, 0))


def load_baseline() -> Baseline:
    path = _baseline_path()
    if not path.exists():
        return Baseline()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    repos_raw = raw.get("repos") or {}
    counts: dict[str, int] = {}
    for repo, val in repos_raw.items():
        counts[str(repo)] = int(val.get("count", 0)) if isinstance(val, dict) else int(val)
    return Baseline(counts=counts, note=str(raw.get("note") or ""))


def write_baseline(counts: dict[str, int], existing: Baseline) -> None:
    path = _baseline_path()
    merged: dict[str, dict[str, int]] = {}
    for repo in sorted(set(counts) | set(existing.counts)):
        observed = int(counts.get(repo, 0))
        prior = existing.allowed(repo)
        merged[repo] = {"count": min(observed, prior) if repo in existing.counts else observed}
    header = (
        "# Baseline for QG STEP 5.105 — subprocess/os.system GCS/S3 object-CLI ratchet.\n"
        "#\n"
        "# SHRINKING ratchet. `repos[<repo>].count` is the number of subprocess/os.system\n"
        "# call sites invoking an OBJECT-level gcloud storage/gsutil/aws s3/s3api operation\n"
        "# (WITHOUT a `# noqa: gcs-cli` marker) this gate tolerates in that repo. A repo\n"
        "# whose live count EXCEEDS its baseline fails CI -- migrate to UTL's\n"
        "# gcs_copy_object/gcs_delete_object/gcs_describe_object/list_blobs\n"
        "# (unified_trading_library.cloud_interface), or add `# noqa: gcs-cli` with a\n"
        "# one-line reason. NEVER raise a count.\n"
        "#\n"
        "# Repos not listed default to count=0 (zero tolerance -- any new site fails).\n"
        "#\n"
        '# SSOT: CLAUDE.md "Writing STORAGE code?" + /codex/05-infrastructure/gcs-object-operations.md\n'
        "# + plans/active/issues/destructive_command_hook_blind_to_sdk_delete_path_2026_07_27.md (provenance).\n"
    )
    body = yaml.safe_dump(
        {"note": existing.note or "Seeded 2026-07-27 (behavioral-testing follow-up).", "repos": merged},
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
    )
    _ = path.write_text(header + body, encoding="utf-8")


# ── Scope resolution ─────────────────────────────────────────────────────────


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(
                f"[check_subprocess_gcs_object_cli] --scope {scope!r} not a dir under {workspace_root}",
                file=sys.stderr,
            )
            return []
        scan_root = repo_root / source_dir if source_dir else repo_root
        if not scan_root.exists():
            scan_root = repo_root
        return [(scope, scan_root)]
    out: list[tuple[str, Path]] = []
    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir() or child.name in EXCLUDE_DIR_NAMES or child.name.startswith("."):
            continue
        if (child / ".git").exists():
            out.append((child.name, child))
    return out


# ── main ─────────────────────────────────────────────────────────────────────


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="subprocess/os.system GCS/S3 object-CLI ratchet (QG STEP 5.105).")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None)
    parser.add_argument("--source-dir", default=None)
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    baseline = load_baseline()
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print("[check_subprocess_gcs_object_cli] no repos in scope.", file=sys.stderr)
        return 0

    scoped = args.scope is not None
    observed: dict[str, int] = {}
    failures: list[str] = []
    warnings: list[str] = []
    for repo_name, scan_root in scopes:
        scan = scan_repo(scan_root, repo_name, scoped=scoped)
        observed[repo_name] = scan.count
        allowed = baseline.allowed(repo_name)
        if scan.count > allowed:
            new_sites = scan.sites[allowed:] if allowed < len(scan.sites) else scan.sites
            sites_str = "; ".join(f"{f}:{ln} ({why})" for f, ln, why in new_sites[:20])
            failures.append(
                f"[FAIL] {repo_name}: {scan.count} subprocess GCS/S3 object-CLI call(s) > baseline {allowed}. "
                f"New/over-baseline site(s): {sites_str}" + (" ..." if len(new_sites) > 20 else "")
            )
        elif scan.count < allowed:
            warnings.append(
                f"[WARN] {repo_name}: {scan.count} < baseline {allowed} — ratchet DOWN (--update-baseline)."
            )
        else:
            warnings.append(f"[OK]   {repo_name}: {scan.count} (== baseline)")

    if args.update_baseline:
        write_baseline(observed, baseline)
        print(f"[check_subprocess_gcs_object_cli] baseline updated at {_baseline_path()}")
        for line in sorted(f"  {r}: {c}" for r, c in observed.items()):
            print(line)
        return 0

    for w in warnings:
        print(w)
    for f in failures:
        print(f, file=sys.stderr)
    if failures:
        print(
            "\n→ Route the new call through unified_trading_library.cloud_interface's "
            "gcs_copy_object()/gcs_delete_object()/gcs_describe_object()/list_blobs(), OR add "
            "'# noqa: gcs-cli' with a one-line reason if it's a deliberate, audited exception "
            "(e.g. a documented credential-refresh constraint). SSOT: CLAUDE.md 'Writing STORAGE "
            "code?' + codex/05-infrastructure/gcs-object-operations.md. Baseline: "
            "unified-trading-pm/scripts/quality_gates/subprocess_gcs_object_cli_baseline.yaml "
            "(NEVER raise a count).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
