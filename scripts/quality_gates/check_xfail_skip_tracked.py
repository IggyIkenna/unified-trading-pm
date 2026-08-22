#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""AST-walk QG STEP — every ``pytest.xfail`` / unconditional ``@pytest.mark.skip`` must cite a tracked plan/issue slug.

Enforces the standing rule that an ``xfail``/``skip`` needs a tracked todo
(operator finding 2026-08-08, fleet-wide "tests weakened rather than fixed"
sweep): an xfail with a good reason and no remediation todo is
indistinguishable, six months later, from coverage that was never written.
This check closes the gap left by the older inline grep rule in
``base-service.sh`` (which only required a ``# reason:`` comment — any reason,
not a *tracked* one) by requiring the reason to cite a plan/issue slug.

What is flagged (ERROR unless baselined in ``xfail_skip_tracked_baseline.yaml``)
--------------------------------------------------------------------------------
* ``@pytest.mark.xfail(...)`` / ``pytest.xfail(...)``  — reason must cite a
  tracked slug. xfail is the "this test is disabled because it fails" marker —
  the weakened-coverage class by definition.
* ``@pytest.mark.skip(...)`` (UNCONDITIONAL decorator, no ``if=``/condition) —
  reason must cite a tracked slug. Unconditional skip = coverage disabled with
  no runtime gate.

What is deliberately EXEMPT (recorded in the check so the boundary stays
greppable) — ``codex/06-coding-standards/quality-gates.md`` "xfail/skip must be
tracked":
* ``@pytest.mark.skipif(condition, ...)`` — has a real runtime condition
  (environment-gated). Documented-reason skipif is legitimate gating, not
  weakened coverage (matches the existing "No pytest.skip() without documented
  reason in skipif condition" rule in ``codex/06-coding-standards/README.md``).
* ``pytest.skip("<reason>")`` call-form with a non-empty reason — pervasively
  used for environment gating (VCR-cassette presence, live-API-key absence,
  CI smoke-test tiers). Requiring a slug on all ~700 of these would be noise;
  the call-form is only flagged when it carries NO reason at all (a skip with
  zero justification IS indistinguishable from coverage never written).

"cites a tracked slug" predicate — the reason string contains one of:
  * a ``plans/`` / ``issues/`` / ``codex/`` path reference
  * a dated stamp ``20YY_MM_DD`` / ``20YY-MM-DD`` (the workspace's universal
    plan/issue slug suffix), e.g. ``defi_..._wireup_2026_08_07``
  * an explicit ``<something>.md`` doc/plan filename reference

Mechanics (shrinking ratchet, mirrors ``check_banned_placeholder_methods.py``)
-------------------------------------------------------------------------------
* Occurences listed in ``xfail_skip_tracked_baseline.yaml`` (status:
  ``pending_removal``) surface as WARNINGS (exit-clean); any NEW occurrence not
  in the baseline fails CI with ``file:line`` + the ``successor:`` from the
  baseline header. Remove a baseline entry the moment its xfail/skip cites a
  real slug (or the test is fixed so it runs) — never ADD a new one. To refresh
  the baseline after an intentional sweep of the existing debt, re-run with
  ``--baseline-write``.

Usage::

    # per-repo (run by base-service.sh STEP 5.107 / base-library.sh STEP 5.102):
    python check_xfail_skip_tracked.py --workspace-root <ws> --scope <repo>

    # workspace-wide sweep (all repos under <ws>):
    python check_xfail_skip_tracked.py --workspace-root <ws>
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

#: A reason string "cites a tracked slug" when it references a plan/issue/codex
#: path, a dated stamp (the workspace's universal slug suffix), or a doc
#: filename. This is deliberately permissive: any one of these is strong
#: evidence the disabling is tied to tracked remediation work (greppable +
#: auditably assigned), which is exactly what a bare prose reason is not.
_TRACKED_SLUG_RE: Final[re.Pattern[str]] = re.compile(
    r"(plans/|issues/|codex/|(?<!\d)\d{4}[_-]\d{2}[_-]\d{2}(?!\d)|\b[\w.\-]+\.md\b)",
    re.IGNORECASE,
)

#: Decorator forms the check understands: ``@pytest.mark.<k>`` or ``@mark.<k>``.
_MARK_DECORATOR_RE: Final[re.Pattern[str]] = re.compile(r"(?:pytest\.)?mark\.(xfail|skip|skipif)$")

#: Top-level dir names to skip when walking.
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
        # Nested per-agent git worktrees (.claude/worktrees/<id>/) can carry an
        # older/different snapshot of the same repo's source — scanning one
        # produces false violations for code that doesn't exist in the actual
        # checked-out tree (found live 2026-08-06, same class as the
        # check_manifest_import_alignment.py / test_event_logging.py fixes).
        ".claude",
        "scripts",  # per "Schema provenance" rule — scripts/ is excluded from strict checks
    }
)

#: Path-fragment patterns that indicate archived / generated / stale-clone trees.
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
    "stale-pre-history-rewrite",
)

#: Required keys per baseline entry.
REQUIRED_KEYS: Final[tuple[str, ...]] = ("repo", "file", "kind", "line", "status", "successor")

#: Allowed ``status:`` values per baseline entry.
VALID_STATUS: Final[frozenset[str]] = frozenset({"pending_removal"})


# ── Data shapes ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Finding:
    """A flagged occurrence (a marker that violates the tracked-slug rule)."""

    repo: str
    file: str  # repo-relative path
    line: int
    kind: str
    snippet: str

    @property
    def baseline_key(self) -> tuple[str, str, str, int]:
        return (self.repo, self.file, self.kind, self.line)


@dataclass(frozen=True)
class BaselineEntry:
    """One currently-known violating occurrence the baseline tolerates as a warning."""

    repo: str
    file: str
    kind: str
    line: int
    status: str  # "pending_removal"
    successor: str


# ── Baseline loading ─────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "xfail_skip_tracked_baseline.yaml"


def load_baseline() -> tuple[dict[tuple[str, str, str, int], BaselineEntry], str]:
    """Return ``({(repo, file, kind, line): BaselineEntry}, default_successor)``."""

    path = _baseline_path()
    if not path.exists():
        return {}, "cite a tracked plan/issue slug in the xfail/skip reason, or fix the test so it runs"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    default_successor = str(doc.get("default_successor", "")) or (  # noqa: qg-empty-fallback — absent key immediately coalesced to a real default on the next line
        "cite a tracked plan/issue slug in the xfail/skip reason, or fix the test so it runs"
    )
    entries: dict[tuple[str, str, str, int], BaselineEntry] = {}
    for raw in doc.get("entries", []) or []:  # noqa: qg-empty-fallback — absent "entries" = empty baseline
        missing = [k for k in REQUIRED_KEYS if k not in raw]
        if missing:
            raise ValueError(f"baseline entry missing keys {missing}: {raw!r}")
        if raw["status"] not in VALID_STATUS:
            raise ValueError(f"baseline entry has invalid status {raw['status']!r}: {raw!r}")
        ent = BaselineEntry(
            repo=str(raw["repo"]),
            file=str(raw["file"]),
            kind=str(raw["kind"]),
            line=int(raw["line"]),
            status=str(raw["status"]),
            successor=str(raw.get("successor", default_successor)),
        )
        entries[(ent.repo, ent.file, ent.kind, ent.line)] = ent
    return entries, default_successor


def write_baseline(entries: list[Finding], default_successor: str) -> None:
    """Write the baseline file from the given findings (all ``pending_removal``)."""

    payload = {
        "doc": "Known xfail/skip markers whose reason does NOT cite a tracked plan/issue slug.",
        "why": (
            "Every pytest.xfail / unconditional @pytest.mark.skip must cite a tracked plan/issue "
            "slug in its reason — an xfail with a good reason and no remediation todo is "
            "indistinguishable, six months later, from coverage that was never written. These are "
            "the CURRENT violations, tolerated as WARNINGS; they must shrink to zero (each entry is "
            "removed the moment its marker cites a real slug or the test is fixed to run). Never ADD "
            "a new entry."
        ),
        "status_explanation": "pending_removal = known violation, must be fixed, tolerated as a warning.",
        "default_successor": default_successor,
        "entries": [
            {
                "repo": e.repo,
                "file": e.file,
                "kind": e.kind,
                "line": e.line,
                "status": "pending_removal",
                "successor": default_successor,
                "snippet": e.snippet[:160],
            }
            for e in sorted(entries, key=lambda e: (e.repo, e.file, e.line))
        ],
    }
    _baseline_path().write_text(
        yaml.safe_dump(payload, sort_keys=False, width=100, allow_unicode=True),
        encoding="utf-8",
    )


# ── AST helpers ──────────────────────────────────────────────────────────────


def _dotted_name(node: ast.expr) -> str:
    """Flatten ``pytest.mark.xfail`` → ``"pytest.mark.xfail"``."""

    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))


def _const_str(value: ast.expr, module_consts: dict[str, str]) -> str | None:
    """Best-effort extraction of a literal string from an AST expression node."""

    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    if isinstance(value, ast.JoinedStr):
        # JoinedStr is an f-string; fold only the constant parts (dynamic parts
        # become a placeholder so a slug in the static part still matches).
        parts: list[str] = []
        for v in value.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                parts.append(v.value)
            else:
                parts.append("{?}")
        return "".join(parts)
    if isinstance(value, ast.Name):
        return module_consts.get(value.id)
    if isinstance(value, ast.BinOp):
        left = _const_str(value.left, module_consts)
        right = _const_str(value.right, module_consts)
        if left is not None and right is not None:
            return left + right
    if isinstance(value, ast.IfExp):
        # ``pytest.skip("a" if cond else "b")`` — a conditional justification is
        # still a justification; fold both branches so the call reads as
        # reason-bearing (never flagged as a zero-justification skip).
        then_val = _const_str(value.body, module_consts)
        else_val = _const_str(value.orelse, module_consts)
        parts = [p for p in (then_val, else_val) if p]
        return parts[0] if parts else None
    return None


def _module_consts(tree: ast.Module) -> dict[str, str]:
    """Resolve top-level ``NAME = "..."`` string constants (skip-reason consts)."""

    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                val = _const_str(node.value, out)
                if val is not None:
                    out[target.id] = val
    return out


def _cites_tracking(reason: str | None) -> bool:
    """True when the reason string carries a plan/issue slug or doc reference."""

    if not reason:
        return False
    return bool(_TRACKED_SLUG_RE.search(reason))


def _comment_reason(lines: list[str], lineno: int) -> str | None:
    """Read a ``# reason: ...`` comment on the marker's own or preceding line."""

    idx = lineno - 1
    for li in (idx, idx - 1):
        if 0 <= li < len(lines):
            m = re.search(r"#\s*reason:\s*(.*)", lines[li])
            if m and m.group(1).strip():
                return m.group(1).strip()
    return None


def _call_reason(call: ast.Call, module_consts: dict[str, str]) -> str | None:
    """Extract the reason from a ``mark.xfail(...)`` / ``mark.skip(...)`` call."""

    for kw in call.keywords:
        if kw.arg in ("reason", "msg") and kw.value is not None:
            val = _const_str(kw.value, module_consts)
            if val is not None:
                return val
    return None


def _classify_decorator(dec: ast.expr) -> tuple[str, ast.Call | None] | None:
    """Return ``(kind, call_node_or_None)`` for a pytest marker decorator, else None."""

    if isinstance(dec, ast.Call):
        target: ast.expr = dec.func
        call = dec
    else:
        target = dec
        call = None
    m = _MARK_DECORATOR_RE.match(_dotted_name(target))
    if not m:
        return None
    return m.group(1), call


def _classify_call(call: ast.Call) -> str | None:
    """Return the marker kind for a ``pytest.xfail(...)`` / ``pytest.skip(...)`` call."""

    name = _dotted_name(call.func)
    if name == "pytest.xfail":
        return "xfail"
    if name == "pytest.skip":
        return "skip_call"
    return None


def _scan_file(path: Path, module_consts: dict[str, str] | None = None) -> list[Finding]:
    """Scan one test file for disabling markers that lack a tracked slug."""

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return []
    if module_consts is None:
        module_consts = _module_consts(tree)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []

    findings: list[Finding] = []

    def _flag(kind: str, node: ast.expr, reasons: list[str | None]) -> None:
        if kind == "skipif":
            return  # conditional — environment-gated, exempt by design
        if kind == "skip_call":
            # call-form skip is exempt when it carries a reason (environmental
            # gating); only a zero-justification skip() is a violation.
            if any(reasons):
                return
        elif any(_cites_tracking(r) for r in reasons if r):
            return
        snippet = next((r for r in reasons if r), "").strip().replace("\n", " ")[:160]
        findings.append(
            Finding(
                repo="",  # filled by the walker
                file=str(path),
                line=node.lineno,
                kind=kind,
                snippet=f"{kind} — reason does not cite a tracked plan/issue slug: {snippet!r}",
            )
        )

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for dec in node.decorator_list:
                classified = _classify_decorator(dec)
                if not classified:
                    continue
                kind, call = classified
                reasons: list[str | None] = []
                if call is not None:
                    reasons.append(_call_reason(call, module_consts))
                # The ``# reason:`` comment lives on the DECORATOR's own line
                # (or the one above it), not the ``def`` line — use the
                # decorator's lineno. A slug in EITHER the ``reason=`` kwarg or
                # the comment satisfies the tracked-slug rule.
                if kind in ("skip", "xfail"):
                    reasons.append(_comment_reason(lines, dec.lineno))
                _flag(kind, dec, reasons)
        elif isinstance(node, ast.Call):
            kind = _classify_call(node)
            if kind is None:
                continue
            reasons = [_call_reason(node, module_consts)]
            # ``pytest.skip("msg")`` — reason in the first positional arg.
            if node.args:
                reasons.append(_const_str(node.args[0], module_consts))
            if kind == "skip_call":
                reasons.append(_comment_reason(lines, node.lineno))
            _flag(kind, node, reasons)
    return findings


# ── File walking ─────────────────────────────────────────────────────────────


def _is_test_file(rel: Path) -> bool:
    if rel.suffix != ".py":
        return False
    parts = set(rel.parts)
    if "tests" in parts or "test" in parts:
        return True
    return rel.name.startswith("test_") or rel.name.endswith("_test.py") or rel.name == "conftest.py"


def _iter_repo_test_files(repo_dir: Path) -> Iterator[Path]:
    """Yield test files under one repo dir (venvs / scripts / archives excluded)."""

    if not repo_dir.is_dir():
        return
    for path in repo_dir.rglob("*.py"):
        rel = path.relative_to(repo_dir)
        if any(seg in EXCLUDE_DIR_NAMES for seg in rel.parts):
            continue
        if any(frag in str(rel) for frag in EXCLUDE_PATH_FRAGMENTS):
            continue
        if _is_test_file(rel):
            yield path


def _resolve_scopes(workspace_root: Path, scope: str | None) -> list[Path]:
    """Return the repo dirs to scan: ``--scope`` given → just it; else every repo."""

    if scope:
        scope_dir = workspace_root / scope
        return [scope_dir] if scope_dir.is_dir() else []
    return [
        d
        for d in sorted(workspace_root.iterdir())
        if d.is_dir()
        and not d.name.startswith(".")
        and d.name != "node_modules"
        and "stale-pre-history-rewrite" not in d.name
    ]


def _scan_repo(repo_dir: Path) -> list[Finding]:
    repo_name = repo_dir.name
    findings: list[Finding] = []
    for path in _iter_repo_test_files(repo_dir):
        try:
            module_consts = _module_consts(ast.parse(path.read_text(encoding="utf-8")))
        except (OSError, SyntaxError):
            continue
        for f in _scan_file(path, module_consts):
            f = Finding(
                repo=repo_name,
                file=str(path.relative_to(repo_dir)),
                line=f.line,
                kind=f.kind,
                snippet=f.snippet,
            )
            findings.append(f)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="single repo dir name to scan")
    parser.add_argument("--baseline-write", action="store_true", help="rewrite the baseline from current findings")
    args = parser.parse_args(argv)

    baseline, default_successor = load_baseline()
    scopes = _resolve_scopes(args.workspace_root, args.scope)
    findings: list[Finding] = []
    for repo_dir in scopes:
        findings.extend(_scan_repo(repo_dir))

    if args.baseline_write:
        write_baseline(findings, default_successor)
        print(f"[OK] xfail_skip_tracked_baseline.yaml rewritten with {len(findings)} current violations")
        return 0

    new_findings = [f for f in findings if f.baseline_key not in baseline]
    baselined = [f for f in findings if f.baseline_key in baseline]

    for f in sorted(baselined, key=lambda e: (e.repo, e.file, e.line)):
        print(f"[WARN] {f.repo} {f.file}:{f.line} — {f.snippet}")
    for f in sorted(new_findings, key=lambda e: (e.repo, e.file, e.line)):
        print(f"[ERROR] {f.repo} {f.file}:{f.line} — {f.snippet}")

    if new_findings:
        print(
            f"[FAIL] {len(new_findings)} new untracked xfail/skip (baseline holds {len(baselined)}). "
            f"Every pytest.xfail / unconditional @pytest.mark.skip must cite a tracked plan/issue slug "
            f"(plans/active/issues/<slug>_<date>.md or a dated slug) in its reason.",
            file=sys.stderr,
        )
        print(
            f"        Fix: add the tracking citation to the reason, or -- if this is genuinely "
            f"pre-existing debt -- re-baseline with --baseline-write (default_successor: {default_successor!r}).",
            file=sys.stderr,
        )
        return 1

    if baselined:
        print(
            f"[OK] {len(baselined)} baselined xfail/skip violation(s) (pending_removal — must cite a "
            f"tracked slug or be fixed); 0 new"
        )
    else:
        print("[OK] no untracked xfail/skip markers (every xfail/skip cites a tracked plan/issue slug)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
