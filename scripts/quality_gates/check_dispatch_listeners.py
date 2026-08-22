#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Static dispatch-delivery checker.

A GitHub `repository_dispatch` POST returns 204 whether or not any workflow is
actually subscribed to the dispatched `event_type` — "delivered" and "nobody
subscribed" are indistinguishable at runtime, so this can only be caught
statically (per `issues/post_cutover_silent_assumption_sweep_2026_07_23.md`
F1 + F3). This script walks every repo in the workspace for:

  - DISPATCH SITES: a call to `repos/{owner}/{repo}/dispatches` with an
    `event_type`, in `.github/workflows/*.yml`, `cloudbuild*.yaml`,
    `buildspec*.yaml`, or `scripts/**/*.sh`.
  - LISTENER SITES: `on: repository_dispatch: types: [...]` in each repo's
    own workflows (a block with no `types:` key listens for ALL event types).

... and reports every dispatched `(target_repo, event_type)` pair with no
matching listener.

Target/event_type resolution:
  - LITERAL tokens (no `$`/`{`/`}`) resolve directly.
  - Known owner aliases (`GITHUB_REPOSITORY_OWNER`/`OWNER`/`ORG`/`GH_ORG`/
    `REPO_OWNER`, or the literal `IggyIkenna`) resolve to the fleet's single
    owner — this is a single-GitHub-org workspace.
  - A file-scope shell assignment (`VAR="literal"` or `VAR="${N:-literal}"`)
    resolves `${VAR}`/`$VAR` references to that literal within the same file.
  - A shell function whose body dispatches with `event_type` bound to its
    first positional arg (`local event_type="$1"`, mirroring
    `scripts/deploy/trading-kill-switch.sh`'s `dispatch_event()`) resolves
    each LITERAL-argument call site of that function to its own DispatchSite.
  - Anything else (a loop variable, a computed value) is UNRESOLVED for that
    axis. An unresolved REPO with a literal event_type is checked fleet-wide:
    if literally NO repo anywhere listens for that event_type, it is still a
    provable orphan regardless of which repo the loop picks at runtime (this
    is exactly `cascade-qg-ordering.yml`'s "each dependent repo" fan-out for
    `quality-gate-run`, F3). An unresolved EVENT_TYPE is never counted (never
    silently dropped either — it prints under `--show`).

Baseline-ratchet semantics (mirrors check_credential_ask_orphans.py): a single
`orphan_count` in `check_dispatch_listeners_baseline.yaml`. Default mode fails
if the current count exceeds baseline; `--baseline-write` resets it after
intentionally fixing (shrinking) or knowingly accepting (never growing) the
set.

**NOT wired into `scripts/quality-gates.sh`** — the registration is a separate
finalize-plan todo (`ci_satellite_ao_dispatch_batch1_2026_07_26.md` § "Same-file
contention": `scripts/quality-gates.sh` is claimed by 3 new checkers from this
batch; only one registration commit lands them all).

Usage::

    python scripts/quality_gates/check_dispatch_listeners.py [--workspace-root PATH] [--show] [--baseline-write]

Exit codes:
  0 — at-or-below baseline (clean)
  1 — regression (more orphans than baseline)
  2 — argument / IO error

SSOT: issues/post_cutover_silent_assumption_sweep_2026_07_23.md (F1, F3, Resolution
checklist "Make dispatch delivery observable").
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

SCRIPT_DIR: Final[Path] = Path(__file__).resolve().parent
PM_ROOT: Final[Path] = SCRIPT_DIR.parent.parent
DEFAULT_WORKSPACE_ROOT: Final[Path] = PM_ROOT.parent
DEFAULT_BASELINE_PATH: Final[Path] = SCRIPT_DIR / "check_dispatch_listeners_baseline.yaml"

# Single-owner fleet (github.com/IggyIkenna/*) — every alias workflows/scripts use
# to spell the owner resolves to this literal.
KNOWN_OWNER: Final[str] = "IggyIkenna"
_OWNER_ALIASES: Final[frozenset[str]] = frozenset({"GITHUB_REPOSITORY_OWNER", "OWNER", "ORG", "GH_ORG", "REPO_OWNER"})

_LITERAL_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9_.-]+$")
_VAR_REF_RE: Final[re.Pattern[str]] = re.compile(r"^\$?\{?\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}?$")

# Captures owner/repo as either a literal token (no slashes/quotes/whitespace) or a
# GHA `${{ <expression> }}` block (which may contain whitespace, e.g.
# `${{ github.repository_owner }}`).  Without the GHA branch these dispatch sites are
# silently excluded from the scan — the `${{ }}` contains spaces that `\s` rejects.
_GHA_EXPR_PAT: Final[str] = r"\$\{\{[^}]+\}\}"
_DISPATCH_URL_RE: Final[re.Pattern[str]] = re.compile(
    rf"repos/((?:{_GHA_EXPR_PAT}|[^/\s\"'])+)/((?:{_GHA_EXPR_PAT}|[^/\s\"'])+)/dispatches"
)
_GHA_EXPR_RE: Final[re.Pattern[str]] = re.compile(rf"^{_GHA_EXPR_PAT}$")
# `\\?` tolerates a JSON payload embedded in a shell string with escaped quotes
# (`-d "{\"event_type\":\"service-deployed\", ...}"`), which cloudbuild.yaml /
# buildspec.aws.yaml both use — a plain `["']?` would silently miss every hit there.
_EVENT_TYPE_RE: Final[re.Pattern[str]] = re.compile(
    r"event_type\\?[\"']?\s*[:=]\s*\\?[\"']?([A-Za-z0-9_.${}-]+)\\?[\"']?"
)
# File-scope simple shell assignment: VAR="literal" or VAR="${N:-literal}" (positional-with-default).
_ASSIGN_LITERAL_RE: Final[re.Pattern[str]] = re.compile(r'^\s*([A-Z_][A-Z0-9_]*)="([^"$]+)"\s*$')
_ASSIGN_DEFAULT_RE: Final[re.Pattern[str]] = re.compile(r'^\s*([A-Z_][A-Z0-9_]*)="\$\{\d+:-([^"}]+)\}"\s*$')

# Matches a bash function definition line: `name() {` (the shell-wrapper-dispatch pattern).
_FUNC_DEF_RE: Final[re.Pattern[str]] = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{\s*$")
_FUNC_END_RE: Final[re.Pattern[str]] = re.compile(r"^\}\s*$")
# `local event_type="$1"` (or `${1}`) — the wrapper's first-arg-is-event-type binding.
_LOCAL_FIRST_ARG_RE: Final[re.Pattern[str]] = re.compile(r'^\s*local\s+(\w+)="\$\{?1\}?"\s*$')

WORKFLOW_GLOBS: Final[tuple[str, ...]] = (".github/workflows/*.yml", ".github/workflows/*.yaml")
ROOT_FILE_GLOBS: Final[tuple[str, ...]] = ("cloudbuild*.yaml", "buildspec*.yaml")
SCRIPT_GLOB: Final[str] = "scripts/**/*.sh"

WINDOW_LINES: Final[int] = 6  # how far past a `/dispatches` line to look for event_type


@dataclass(frozen=True)
class DispatchSite:
    file: str
    line: int
    owner: str | None
    repo: str | None  # None == unresolved/dynamic target
    event_type: str | None  # None == unresolved


@dataclass(frozen=True)
class Orphan:
    site: DispatchSite
    reason: str  # "no listener in <repo>" | "no listener anywhere (dynamic target)"


def _resolve_token(token: str, var_map: dict[str, str]) -> str | None:
    """Resolve a URL path token to a literal string, or None if unresolved.

    GHA ``${{ }}`` expressions (e.g. ``${{ github.repository_owner }}``) are
    returned as-is so the dispatch site is tracked (as unresolved) rather than
    silently excluded from the scan.
    """
    if _LITERAL_RE.match(token):
        return token
    if _GHA_EXPR_RE.match(token):
        # GHA expression — cannot resolve to a literal, but surface it so the
        # dispatch site is counted as unresolved rather than silently dropped.
        return token
    m = _VAR_REF_RE.match(token)
    if not m:
        return None
    name = m.group(1)
    if name in var_map:
        return var_map[name]
    if name in _OWNER_ALIASES:
        return KNOWN_OWNER
    return None


def _build_var_map(lines: list[str]) -> dict[str, str]:
    """File-scope simple shell assignments: VAR="literal" / VAR="${N:-literal}"."""
    var_map: dict[str, str] = {}
    for line in lines:
        m = _ASSIGN_LITERAL_RE.match(line)
        if m:
            var_map[m.group(1)] = m.group(2)
            continue
        m = _ASSIGN_DEFAULT_RE.match(line)
        if m:
            var_map[m.group(1)] = m.group(2)
    return var_map


def _extract_event_type(window_text: str, var_map: dict[str, str]) -> str | None:
    m = _EVENT_TYPE_RE.search(window_text)
    if not m:
        return None
    value = m.group(1)
    if _LITERAL_RE.match(value):
        return value
    resolved = _resolve_token(value, var_map)
    return resolved


def _scan_direct_dispatches(rel_file: str, lines: list[str], var_map: dict[str, str]) -> list[DispatchSite]:
    """Primary extractor: a `/dispatches` URL/path with `event_type` in a nearby window.

    Covers every GHA-workflow / Cloud Build / buildspec dispatch in the fleet (all of
    F3's citations) — the `gh api repos/{o}/{r}/dispatches -f event_type=...` and
    `curl .../repos/{o}/{r}/dispatches -d '{"event_type": "...", ...}'` shapes.
    """
    sites: list[DispatchSite] = []
    for i, line in enumerate(lines):
        m = _DISPATCH_URL_RE.search(line)
        if not m:
            continue
        owner_raw, repo_raw = m.group(1), m.group(2)
        owner = _resolve_token(owner_raw, var_map)
        repo = _resolve_token(repo_raw, var_map)
        window = "\n".join(lines[i : min(len(lines), i + WINDOW_LINES + 1)])
        event_type = _extract_event_type(window, var_map)
        sites.append(DispatchSite(file=rel_file, line=i + 1, owner=owner, repo=repo, event_type=event_type))
    return sites


def _scan_shell_wrapper_dispatches(rel_file: str, lines: list[str], var_map: dict[str, str]) -> list[DispatchSite]:
    """Secondary extractor (`.sh` files only): a function that dispatches with
    `event_type` bound to its OWN first positional arg (mirrors
    `trading-kill-switch.sh`'s `dispatch_event()`) — the direct extractor alone
    would only see the function's literal `${event_type}` placeholder, not the
    real per-call-site event_type. Resolve each LITERAL-argument call site.
    """
    # Find function bodies that contain a `/dispatches` URL AND a
    # `local <var>="$1"` binding for the same var used as event_type.
    wrapper_funcs: dict[str, tuple[str | None, str | None]] = {}  # func_name -> (owner, repo)
    i = 0
    while i < len(lines):
        fm = _FUNC_DEF_RE.match(lines[i])
        if not fm:
            i += 1
            continue
        func_name = fm.group(1)
        start = i
        end = start + 1
        while end < len(lines) and not _FUNC_END_RE.match(lines[end]):
            end += 1
        body = lines[start:end]
        body_text = "\n".join(body)
        url_m = _DISPATCH_URL_RE.search(body_text)
        if url_m:
            first_arg_var = next(
                (lm.group(1) for bl in body if (lm := _LOCAL_FIRST_ARG_RE.match(bl))),
                None,
            )
            event_type_ref_m = re.search(r'\\?"event_type\\?"\s*:\s*\\?"\$\{?(\w+)\}?\\?"', body_text)
            if first_arg_var and event_type_ref_m and event_type_ref_m.group(1) == first_arg_var:
                owner = _resolve_token(url_m.group(1), var_map)
                repo = _resolve_token(url_m.group(2), var_map)
                wrapper_funcs[func_name] = (owner, repo)
        i = end + 1

    if not wrapper_funcs:
        return []

    sites: list[DispatchSite] = []
    for func_name, (owner, repo) in wrapper_funcs.items():
        call_re = re.compile(rf'\b{re.escape(func_name)}\s+"([^"$]+)"')
        for i, line in enumerate(lines):
            cm = call_re.search(line)
            if not cm:
                continue
            # Skip the function's own `local event_type=...`/definition line.
            if _FUNC_DEF_RE.match(line):
                continue
            sites.append(DispatchSite(file=rel_file, line=i + 1, owner=owner, repo=repo, event_type=cm.group(1)))
    return sites


def _candidate_files(repo_dir: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in WORKFLOW_GLOBS:
        files.extend(repo_dir.glob(pattern))
    for pattern in ROOT_FILE_GLOBS:
        files.extend(repo_dir.glob(pattern))
    files.extend(repo_dir.glob(SCRIPT_GLOB))
    return sorted(set(files))


def scan_dispatch_sites(workspace_root: Path) -> list[DispatchSite]:
    """Return every dispatch site found across every repo dir in the workspace."""
    sites: list[DispatchSite] = []
    for repo_dir in sorted(workspace_root.iterdir()):
        if not repo_dir.is_dir() or repo_dir.name.startswith("."):
            continue
        for f in _candidate_files(repo_dir):
            try:
                text = f.read_text(encoding="utf-8")
            except OSError:
                continue
            lines = text.splitlines()
            var_map = _build_var_map(lines)
            rel_file = str(f.relative_to(workspace_root))
            sites.extend(_scan_direct_dispatches(rel_file, lines, var_map))
            if f.suffix == ".sh":
                sites.extend(_scan_shell_wrapper_dispatches(rel_file, lines, var_map))
    return sites


def _dispatch_types(on_block: object) -> set[str] | None:
    """Return the `repository_dispatch` `types` set for one workflow's `on:` block,
    or None if this workflow has no `repository_dispatch` trigger at all.
    A `repository_dispatch` present with no `types:` key listens for EVERY type
    (represented as the sentinel {"*"})."""
    if isinstance(on_block, list):
        return {"*"} if "repository_dispatch" in on_block else None
    if not isinstance(on_block, dict):
        return None
    rd = on_block.get("repository_dispatch")
    if rd is None:
        return None
    if not isinstance(rd, dict):
        return {"*"}
    types = rd.get("types")
    if not types:
        return {"*"}
    return {str(t) for t in types}


def scan_listeners(workspace_root: Path) -> dict[str, set[str]]:
    """Return {repo_name: {event_type, ...}} for every repo's active repository_dispatch
    listeners (union across all its workflow files). "*" means listens for ALL types."""
    listeners: dict[str, set[str]] = {}
    for repo_dir in sorted(workspace_root.iterdir()):
        if not repo_dir.is_dir() or repo_dir.name.startswith("."):
            continue
        wf_dir = repo_dir / ".github" / "workflows"
        if not wf_dir.is_dir():
            continue
        repo_types: set[str] = set()
        for wf in sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml")):
            try:
                data = yaml.safe_load(wf.read_text(encoding="utf-8"))
            except (yaml.YAMLError, OSError):
                continue
            if not isinstance(data, dict):
                continue
            # PyYAML parses the bare scalar key `on` as the boolean True.
            on_block = data.get("on", data.get(True))
            types = _dispatch_types(on_block)
            if types:
                repo_types |= types
        if repo_types:
            listeners[repo_dir.name] = repo_types
    return listeners


def find_orphans(sites: list[DispatchSite], listeners: dict[str, set[str]]) -> tuple[list[Orphan], list[DispatchSite]]:
    """Split dispatch sites into (orphans, unresolved) — resolved-and-covered sites
    are dropped silently (they are the healthy case)."""
    orphans: list[Orphan] = []
    unresolved: list[DispatchSite] = []
    all_listened_types: set[str] = set()
    for types in listeners.values():
        all_listened_types |= types

    for site in sites:
        if site.owner != KNOWN_OWNER or site.event_type is None:
            unresolved.append(site)
            continue
        if site.repo is not None:
            repo_types = listeners.get(site.repo, set())
            if site.event_type in repo_types or "*" in repo_types:
                continue
            orphans.append(Orphan(site=site, reason=f"no listener in {site.repo}"))
            continue
        # Dynamic/unresolved target repo: provably orphan only if NO repo anywhere
        # listens for this event_type (cascade-qg-ordering.yml's "each dependent
        # repo" fan-out class). If SOME but not all repos listen, we cannot prove
        # either way from statics alone — report as unresolved, not orphan.
        if site.event_type not in all_listened_types:
            orphans.append(Orphan(site=site, reason="no listener anywhere (dynamic target)"))
        else:
            unresolved.append(site)
    return orphans, unresolved


def _load_baseline(path: Path) -> int:
    if not path.is_file():
        return 0
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return int(data.get("orphan_count", 0))


def _write_baseline(path: Path, count: int) -> None:
    path.write_text(
        yaml.dump({"orphan_count": count}, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help="Directory containing every repo clone as a sibling dir (default: parent of this PM checkout)",
    )
    parser.add_argument(
        "--baseline-path",
        type=Path,
        default=DEFAULT_BASELINE_PATH,
        help="Path to baseline YAML (default: scripts/quality_gates/check_dispatch_listeners_baseline.yaml)",
    )
    parser.add_argument(
        "--baseline-write",
        action="store_true",
        help="Write current orphan count to baseline path (use after intentional debt or a real fix)",
    )
    parser.add_argument("--show", action="store_true", help="Print every orphan + unresolved site")
    args = parser.parse_args()

    workspace_root: Path = args.workspace_root.resolve()
    if not workspace_root.is_dir():
        print(f"ERROR: workspace root not found: {workspace_root}", file=sys.stderr)
        return 2

    sites = scan_dispatch_sites(workspace_root)
    listeners = scan_listeners(workspace_root)
    orphans, unresolved = find_orphans(sites, listeners)

    if args.baseline_write:
        _write_baseline(args.baseline_path, len(orphans))
        print(f"Wrote baseline: {len(orphans)} orphan dispatch(es) across {len(sites)} dispatch site(s) scanned")
        return 0

    baseline = _load_baseline(args.baseline_path)

    if args.show or len(orphans) > baseline:
        for o in orphans:
            target = o.site.repo or "DYNAMIC"
            print(
                f"  ORPHAN {o.site.file}:{o.site.line}  event_type={o.site.event_type!r}  target={target}  ({o.reason})"
            )
    if args.show:
        for u in unresolved:
            print(f"  unresolved {u.file}:{u.line}  owner={u.owner!r} repo={u.repo!r} event_type={u.event_type!r}")

    if len(orphans) > baseline:
        print(
            f"\nERROR: {len(orphans)} orphan repository_dispatch(es) (baseline {baseline}). "
            "Each dispatched event_type has no listener in its resolved target repo — "
            "a 204 that nobody will ever act on.",
            file=sys.stderr,
        )
        print(
            "  Either: (a) add the missing listener, or delete the dead dispatch call, or "
            "(b) if intentional/tracked debt, re-baseline with --baseline-write.",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK — {len(orphans)} orphan repository_dispatch(es) (at-or-below baseline {baseline}); "
        f"{len(sites)} dispatch site(s) scanned, {len(unresolved)} unresolved (see --show)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
