#!/usr/bin/env python3
"""Build the codex scope manifest (rule 11).

Walks every `codex/**/*.md` under the PM repo, parses the YAML frontmatter,
validates the `scope:` field against the enum, and emits
`codex/14-playbooks/_generated/scope-manifest.json` mapping each audience to
the list of codex paths visible to it.

Rule 11 SSOT: `codex/14-playbooks/_ssot-rules/11-codex-scope-registry.md`.

Contract
--------
- Scope enum: {sales, engineer, admin, prospect, investor}.
- Frontmatter must be a YAML block delimited by two `---` lines at the top of
  the file. `scope:` is an array subset of the enum; may be absent (defaults
  apply) or `[]` (no audience).
- Default when no `scope:` is declared: `[engineer, admin]`.
- Fails loud (non-zero exit) on: malformed YAML, unknown scope values,
  non-array scope values, or non-list item types.

Usage
-----
    python3 codex/14-playbooks/_tools/build_scope_manifest.py
        [--check-only]                  # do not write output; exit non-zero on errors
        [--root <repo_root>]            # default: autodetect PM repo root
        [--output <path>]               # default: codex/14-playbooks/_generated/scope-manifest.json
        [--verbose]                     # per-file trace

The shell wrapper `build-scope-manifest.sh` invokes this script with defaults.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Final

SCOPE_ENUM: Final[frozenset[str]] = frozenset(
    {"sales", "engineer", "admin", "prospect", "investor"}
)
DEFAULT_SCOPE: Final[tuple[str, ...]] = ("engineer", "admin")
FRONTMATTER_DELIM: Final[str] = "---"


class ScopeParseError(Exception):
    """Raised when a codex doc has invalid scope frontmatter."""


def find_pm_root(start: Path) -> Path:
    """Walk up from `start` until we find the PM repo root (contains codex/)."""
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "codex" / "00-SSOT-INDEX.md").is_file():
            return candidate
    raise SystemExit(
        f"could not locate PM repo root starting from {start} — expected to find codex/00-SSOT-INDEX.md"
    )


def iter_codex_docs(pm_root: Path) -> list[Path]:
    """Return every codex `*.md` that is not under `_archived_pre_v2/`."""
    codex_dir = pm_root / "codex"
    docs: list[Path] = []
    for path in codex_dir.rglob("*.md"):
        if "_archived_pre_v2" in path.parts:
            continue
        docs.append(path)
    return sorted(docs)


def extract_frontmatter(text: str) -> str | None:
    """Return the YAML block between two `---` lines at the very top, or None."""
    if not text.startswith(FRONTMATTER_DELIM + "\n") and not text.startswith(
        FRONTMATTER_DELIM + "\r\n"
    ):
        return None
    # Split on newlines, consume the opening ---
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIM:
        return None
    block_lines: list[str] = []
    for line in lines[1:]:
        if line.strip() == FRONTMATTER_DELIM:
            return "\n".join(block_lines)
        block_lines.append(line)
    # No closing --- found
    return None


_SCOPE_INLINE_RE = re.compile(
    r"^scope:\s*\[\s*(?P<items>[^\]]*)\s*\]\s*$", re.MULTILINE
)
_SCOPE_BLOCK_HEADER_RE = re.compile(r"^scope:\s*$", re.MULTILINE)
_YAML_LIST_ITEM_RE = re.compile(r"^\s+-\s+(?P<item>\S+)\s*$")


def parse_scope_field(frontmatter: str, path: Path) -> list[str] | None:
    """Extract `scope: [...]` or block-list form. Return list or None if absent."""
    # Inline form: scope: [a, b, c]
    inline_match = _SCOPE_INLINE_RE.search(frontmatter)
    if inline_match is not None:
        raw_items = inline_match.group("items").strip()
        if not raw_items:
            return []
        items = [item.strip().strip("'\"") for item in raw_items.split(",")]
        return [item for item in items if item]

    # Block form: scope:\n  - a\n  - b
    block_header = _SCOPE_BLOCK_HEADER_RE.search(frontmatter)
    if block_header is None:
        return None

    # Consume following indented list items
    tail = frontmatter[block_header.end():]
    items: list[str] = []
    for line in tail.splitlines():
        if not line.strip():
            break
        if not line.startswith((" ", "\t")):
            break
        item_match = _YAML_LIST_ITEM_RE.match(line)
        if item_match is None:
            # Non-list content under scope: — malformed
            raise ScopeParseError(
                f"{path}: malformed block-list under `scope:` (line: {line!r})"
            )
        items.append(item_match.group("item").strip().strip("'\""))

    # Also reject scalar form (scope: engineer on one line)
    scalar_match = re.search(r"^scope:\s*(?P<val>\S[^\[\n]*)$", frontmatter, re.MULTILINE)
    if scalar_match is not None and not scalar_match.group("val").startswith("["):
        # Only raise if we did NOT also match a block header — block header
        # matches `scope:` with nothing after, scalar would have content.
        raise ScopeParseError(
            f"{path}: `scope:` must be an array (got scalar: {scalar_match.group('val')!r})"
        )

    return items


def validate_scopes(scopes: list[str], path: Path) -> None:
    unknown = [s for s in scopes if s not in SCOPE_ENUM]
    if unknown:
        raise ScopeParseError(
            f"{path}: unknown scope value(s) {unknown!r} — "
            f"must be subset of {sorted(SCOPE_ENUM)}"
        )


def classify_doc(path: Path, pm_root: Path, verbose: bool) -> tuple[list[str], bool]:
    """Return (scopes, used_default).

    `used_default` is True when the doc lacked a `scope:` field and defaults
    were applied. Emits a warning to stderr in that case (coverage checker
    treats it as an error; manifest builder treats it as a soft fallback).
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as err:
        raise ScopeParseError(f"{path}: could not read — {err}") from err

    frontmatter = extract_frontmatter(text)
    if frontmatter is None:
        if verbose:
            print(
                f"[default] {path.relative_to(pm_root)} — no frontmatter, applied default {list(DEFAULT_SCOPE)}",
                file=sys.stderr,
            )
        return list(DEFAULT_SCOPE), True

    scopes = parse_scope_field(frontmatter, path)
    if scopes is None:
        if verbose:
            print(
                f"[default] {path.relative_to(pm_root)} — frontmatter has no `scope:`, applied default {list(DEFAULT_SCOPE)}",
                file=sys.stderr,
            )
        return list(DEFAULT_SCOPE), True

    validate_scopes(scopes, path)
    return scopes, False


def build_manifest(
    pm_root: Path, verbose: bool, fail_on_default: bool
) -> tuple[dict[str, list[str]], list[Path]]:
    """Walk codex, build the per-audience manifest, return also the list of
    docs that lacked explicit scope (for the coverage checker)."""
    manifest: dict[str, list[str]] = {audience: [] for audience in sorted(SCOPE_ENUM)}
    uncovered: list[Path] = []
    errors: list[str] = []

    for doc in iter_codex_docs(pm_root):
        try:
            scopes, used_default = classify_doc(doc, pm_root, verbose)
        except ScopeParseError as err:
            errors.append(str(err))
            continue
        if used_default:
            uncovered.append(doc)
        rel = doc.relative_to(pm_root).as_posix()
        for audience in scopes:
            manifest[audience].append(rel)

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        raise SystemExit(1)

    # Stable ordering per audience
    for audience in manifest:
        manifest[audience].sort()

    if fail_on_default and uncovered:
        print(
            f"ERROR: {len(uncovered)} codex doc(s) lack explicit `scope:` frontmatter:",
            file=sys.stderr,
        )
        for doc in uncovered[:50]:
            print(f"  - {doc.relative_to(pm_root)}", file=sys.stderr)
        if len(uncovered) > 50:
            print(f"  ... and {len(uncovered) - 50} more", file=sys.stderr)
        raise SystemExit(1)

    return manifest, uncovered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__ or "", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Do not write manifest; fail non-zero on any missing `scope:` frontmatter or invalid value.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="PM repo root (autodetected if omitted).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Manifest output path (default: codex/14-playbooks/_generated/scope-manifest.json).",
    )
    parser.add_argument("--verbose", action="store_true", help="Per-file trace to stderr.")
    args = parser.parse_args(argv)

    here = Path(__file__).resolve().parent
    pm_root = args.root.resolve() if args.root is not None else find_pm_root(here)
    output = (
        args.output
        if args.output is not None
        else pm_root / "codex/14-playbooks/_generated/scope-manifest.json"
    )

    manifest, uncovered = build_manifest(
        pm_root, verbose=args.verbose, fail_on_default=args.check_only
    )

    if args.check_only:
        # build_manifest already exited on errors; if we got here, all covered.
        print(
            f"OK: all {sum(len(v) for v in manifest.values())} scope assignments across "
            f"{len({p for paths in manifest.values() for p in paths})} codex docs have explicit `scope:` frontmatter.",
        )
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    total_assignments = sum(len(v) for v in manifest.values())
    unique_docs = len({p for paths in manifest.values() for p in paths})
    print(
        f"wrote {output.relative_to(pm_root)}: "
        f"{unique_docs} docs, {total_assignments} audience-assignments, "
        f"{len(uncovered)} defaulted-to-[engineer,admin]"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
