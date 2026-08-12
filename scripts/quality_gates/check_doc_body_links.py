#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Inline markdown body-link existence check — complements docspec.validate_doc_references().

validate_doc_references() (scripts/docs/docspec.py, wired into check_frontmatter_schema.py) already
gates FRONTMATTER path-shaped free_list fields (related/codex_ssots/supersedes/superseded_by/
depends_on/related_plans/referenced_by/doc_versions_checked) for existence. It never looks at a doc's
BODY — an inline markdown link like `[the SSOT](../foo.md)` is invisible to it. This check covers
that gap: it walks the same live doc trees check_frontmatter_schema.py uses (imported directly, not
duplicated, to avoid the exact hand-maintained-list drift docs-reconcile itself exists to catch),
extracts `[text](target)` links from each doc's BODY (frontmatter block + fenced code blocks
excluded — a code fence showing markdown link syntax as an example is not a real reference), and
checks existence for any target that is a relative path ending in `.md`/`.mdc`. Any URI-scheme target
(http(s)://, mailto:, vscode-webview://, ...) and anchor-only (`#foo`) targets are skipped — not
corpus-relative doc links.

Also extracts the corpus's other dominant citation convention: a bare backtick-quoted path starting
with `codex/` or `/codex/`, e.g. "SSOT: `codex/foo/bar.md`" — narrower first cut of the P1 broken-link
gap filed in doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md (the codex/-prefixed
subset only; other backtick-cited trees like plans/ are left for a later pass). Reuses `_resolve()`
unchanged.

Resolution mirrors validate_doc_references()'s three tiers: relative to the referencing doc's own
directory, relative to the PM root, then a plans/archive/** basename fallback (a doc that graduated
to archive is a normal lifecycle event, not breakage). A fourth, final tier: a relative link that
climbs out of the PM repo into a SIBLING repo directory not present in the current checkout (CI's
narrow `dep_repos` fetch clones only unified-trading-library/unified-api-contracts alongside
unified-trading-pm, never the full 25-repo fleet) is unverifiable, not broken — soft-skipped rather
than flagged.

Ratcheted against doc_body_link_baseline.yaml (same convention as doc_reference_baseline.yaml) so
pre-existing rot found at seed time doesn't fail every run — only a NEW broken link (not already in
the baseline) fails the gate.

Usage: check_doc_body_links.py [file ...]   # no args -> full live corpus
  --quiet             suppress the success line
  --update-baseline   regenerate doc_body_link_baseline.yaml from the CURRENT full-corpus scan (run
                       after a cleanup pass; NEVER to launder a check you just introduced — see the
                       baseline file's own header)
Exit 0 = zero NEW broken links. Exit 1 = new breakage (each printed with its remedy).
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]
LINK_BASELINE = Path(__file__).resolve().parent / "doc_body_link_baseline.yaml"

_LINK_RE = re.compile(r'\[[^\]\n]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
_BACKTICK_CODEX_RE = re.compile(r"`(/?codex/[^`\s*]+\.(?:md|mdc))`")
_FENCE_RE = re.compile(r"^\s*```")
_URI_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://")


def _load_frontmatter_schema_module():
    spec = importlib.util.spec_from_file_location(
        "check_frontmatter_schema", PM / "scripts" / "plan-hygiene" / "check_frontmatter_schema.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/plan-hygiene/check_frontmatter_schema.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_frontmatter_schema"] = mod
    spec.loader.exec_module(mod)
    return mod


def _strip_frontmatter(text: str) -> str:
    """Blank out the frontmatter block rather than slicing it off, so every line number reported
    downstream still matches the ORIGINAL file (an editor jump-to-line target), not a post-strip
    offset that only makes sense internally."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            newline_count = text[: end + 5].count("\n")
            return ("\n" * newline_count) + text[end + 5 :]
    return text


def _body_without_fences(text: str) -> str:
    """Blank fenced-code-block lines (never drop them) — same line-alignment reasoning as above: a
    real link after a code fence must keep its true line number, not shift up by the fence's length."""
    out_lines: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            out_lines.append("")
            continue
        out_lines.append("" if in_fence else line)
    return "\n".join(out_lines)


def _extract_links(text: str) -> list[tuple[int, str]]:
    """Return (1-based line number, target) for every markdown link target in text — real
    `[text](target)` links plus backtick-quoted `codex/`/`/codex/` path citations (the corpus's
    other dominant cross-reference convention)."""
    out: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for m in _LINK_RE.finditer(line):
            out.append((lineno, m.group(1)))
        for m in _BACKTICK_CODEX_RE.finditer(line):
            # A backtick path containing a literal "..." is a PLACEHOLDER, never a citation —
            # no real file has an "..." segment, so resolving it can only ever report a false
            # broken link. Measured 2026-08-12: `codex/NN-name/...md`, written in PROSE inside
            # elysium-presentation-authoring-notes.md precisely to describe this class of
            # false positive, failed check_doc_body_links for the whole fleet and blocked every
            # unified-trading-pm quickmerge. Fences were already excluded (_body_without_fences);
            # this is the prose case that exclusion cannot reach.
            if "..." in m.group(1):
                continue
            out.append((lineno, m.group(1)))
    return out


def _is_checkable(target: str) -> str | None:
    """Clean + classify a link target; return the corpus-relative path if worth checking, else None."""
    t = target.strip().strip("<>")
    if not t or t.startswith(("mailto:", "#")):
        return None
    if _URI_SCHEME_RE.match(t):
        return None  # any URI scheme (http(s)://, vscode-webview://, ftp://, ...) — not a corpus-relative link
    t = t.split("#", 1)[0]  # strip in-doc fragment
    if not t or not t.endswith((".md", ".mdc")):
        return None
    return t


def _crosses_into_absent_sibling_repo(doc_dir: Path, pm_root: Path, target: str) -> bool:
    """A relative link that climbs out of the PM repo into a sibling repo dir (e.g.
    `../../../deployment-service/docs/X.md`) is genuinely unverifiable — not broken — when that
    sibling repo simply isn't present in the current checkout. Full local dev clones every sibling
    repo, so this never fires there; CI's narrow `dep_repos` fetch (only unified-trading-library /
    unified-api-contracts get cloned alongside unified-trading-pm) is exactly the case this exists
    for — same soft-skip philosophy as an absent sibling clone in check_plan_commit_sha_evidence.py."""
    try:
        resolved = (doc_dir / target).resolve()
    except (OSError, ValueError):
        return False
    workspace_root = pm_root.parent
    try:
        rel_to_workspace = resolved.relative_to(workspace_root)
    except ValueError:
        return False  # not even under the workspace root — a genuinely broken link
    if not rel_to_workspace.parts:
        return False
    sibling_repo = rel_to_workspace.parts[0]
    if sibling_repo == pm_root.name:
        return False  # stayed inside PM — a real broken link, not a cross-repo case
    return not (workspace_root / sibling_repo).is_dir()


def _resolve(doc_dir: Path, pm_root: Path, target: str) -> bool:
    if target.startswith("/"):
        # Repo-root-relative convention used throughout this corpus (e.g. "/codex/foo.md" meaning
        # "<PM root>/codex/foo.md") — NOT a filesystem-absolute path. `Path.__truediv__` treats a
        # leading-"/" right operand as absolute and silently discards the left side, so this must be
        # resolved against pm_root explicitly rather than via the doc_dir/pm_root `/` joins below.
        stripped = target.lstrip("/")
        if (pm_root / stripped).is_file():
            return True
        return any((pm_root / "plans" / "archive").glob(f"**/{Path(stripped).name}"))
    if (doc_dir / target).is_file():
        return True
    if (pm_root / target).is_file():
        return True
    if any((pm_root / "plans" / "archive").glob(f"**/{Path(target).name}")):
        return True
    return _crosses_into_absent_sibling_repo(doc_dir, pm_root, target)


def _load_baseline() -> set[str]:
    if not LINK_BASELINE.is_file():
        return set()
    data = yaml.safe_load(LINK_BASELINE.read_text()) or {}
    return set(data.get("known_broken") or [])


def find_broken_links(paths: list[Path], pm_root: Path) -> dict[str, list[tuple[int, str]]]:
    """Pure scan: {doc-rel-path: [(lineno, unresolved target), ...]} for every path given.

    No baseline/CLI concerns here — just "which links in these docs fail to resolve", so this is
    directly unit-testable against a synthetic doc tree (see test_check_doc_body_links.py).
    """
    out: dict[str, list[tuple[int, str]]] = {}
    for path in paths:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        body = _body_without_fences(_strip_frontmatter(text))
        doc_dir = path.resolve().parent
        rel = path.resolve().relative_to(pm_root).as_posix()
        seen_targets: set[str] = set()
        broken: list[tuple[int, str]] = []
        for lineno, raw_target in _extract_links(body):
            target = _is_checkable(raw_target)
            if target is None or target in seen_targets:
                continue
            if _resolve(doc_dir, pm_root, target):
                continue
            seen_targets.add(target)
            broken.append((lineno, target))
        if broken:
            out[rel] = broken
    return out


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    quiet = "--quiet" in args
    update_baseline = "--update-baseline" in args
    files = [Path(a) for a in args if not a.startswith("--")]

    fm_mod = _load_frontmatter_schema_module()
    # --update-baseline always scans the FULL corpus — the baseline represents total corpus state,
    # not whatever subset happened to be passed as file args.
    paths = fm_mod._iter_docs() if (update_baseline or not files) else files
    baseline = _load_baseline()

    checked = len(paths)
    scanned = find_broken_links(paths, PM)

    bad: list[tuple[str, list[str]]] = []
    new_keys: set[str] = set()
    for rel, broken in scanned.items():
        problems: list[str] = []
        for lineno, target in broken:
            key = f"{rel}::{target}"
            if update_baseline:
                new_keys.add(key)
            elif key not in baseline:
                problems.append(f"line {lineno}: broken link -> '{target}' (NEW — not in doc_body_link_baseline.yaml)")
        if problems:
            bad.append((rel, problems))

    if update_baseline:
        LINK_BASELINE.write_text(
            "# Baseline for the inline markdown body-link existence check (check_doc_body_links.py).\n"
            "#\n"
            "# This is a SHRINKING ratchet, same convention as doc_reference_baseline.yaml. `known_broken`\n"
            '# is the exact set of "<doc>::<target>" keys this checker tolerates today. A key NOT in this\n'
            "# set (a NEW broken body link) fails the gate. A key IN this set that no longer reproduces\n"
            "# (the link got fixed) is harmless dead weight, not an error — but should be removed by\n"
            "# re-running --update-baseline after a cleanup pass.\n"
            "#\n"
            "# NEVER add an entry here to silence a check you introduced yourself — this baseline is for\n"
            "# PRE-EXISTING debt found at seed time, not a way to launder new breakage.\n"
            "known_broken:\n"
            # width=float("inf") disables PyYAML's default 80-col auto-wrap: a sufficiently long key
            # (a real one exists — an ellipsis-placeholder path in strategy-catalogue-3tier.md) would
            # otherwise get split across two physical lines via YAML's backslash-continuation syntax,
            # which downstream tools (prettier) then choke on when the manual "  - " prefix + single
            # trailing "\n" this loop adds don't account for the embedded line break.
            + "".join(
                f"  - {yaml.safe_dump(k, default_style=chr(34), width=float('inf')).strip()}\n"
                for k in sorted(new_keys)
            )
        )
        print(f"doc_body_link_baseline.yaml regenerated: {len(new_keys)} known_broken entries.")
        return 0

    if bad:
        print(f"❌ check_doc_body_links: {len(bad)} doc(s) with NEW broken inline links:", file=sys.stderr)
        for rel, problems in bad:
            print(f"  {rel}:", file=sys.stderr)
            for pr in problems:
                print(f"    - {pr}", file=sys.stderr)
        print(
            "  Remedy: fix the link target, or if it points to a doc that legitimately moved, repoint it.\n"
            "  If this is pre-existing debt you're not touching:"
            " python3 scripts/quality_gates/check_doc_body_links.py --update-baseline",
            file=sys.stderr,
        )
        return 1
    if not quiet:
        print(f"✅ check_doc_body_links: {checked} docs scanned, zero NEW broken inline links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
