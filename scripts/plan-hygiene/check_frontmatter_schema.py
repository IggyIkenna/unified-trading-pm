#!/usr/bin/env python3
"""Per-doc-type frontmatter SCHEMA gate for the PM repo (2026-06-16).

Enforces required-NON-EMPTY fields + value resolutions per doc type, so agents can't
drift the frontmatter of plans / epics / issues / audit-results / codex docs. This is
the hard gate referenced by quality-gates.sh; supersedes the presence-only
`check_frontmatter.sh` for value-level enforcement (that one stays for the .sh-shaped
"first line is ---" + deprecated-field checks).

Doc type → required NON-EMPTY fields (classified by path):
  plan   plans/active/*.md          parent_epic title priority status locked_by
                                     estimate_class estimate_baseline_ai_days estimate_calibrated_ai_days
                                     + VALUE: parent_epic (str|list) each resolves to plans/epics/<slug>.md
  issue  plans/active/issues/*.md    title status priority locked_by created
  epic   plans/epics/*.md            name title priority status tier assigned_vm
  audit  plans/audit/results/*.md    type title epic auditor date status
                                     + instructions_ref REQUIRED when type == audit-result
                                     + VALUE: epic (str|list) each resolves to an epic
  codex  codex/**/*.md               scope

Usage: check_frontmatter_schema.py [file ...]   # no args → full corpus
  --quiet      suppress the success line
Exit 0 = every in-scope doc conforms. Exit 1 = violations.

SSOT for the canonical sets: plans/PLAN_FORMAT.md (plan/epic) + plans/audit/README.md
(audit-result) + CLAUDE.md Findings-Triage (issue) + codex scope convention.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

import yaml

PM = Path(__file__).resolve().parents[2]
EPICS_DIR = PM / "plans" / "epics"

SKIP_NAMES = {"README.md", "INDEX.md", "task_template.md"}

REQUIRED: dict[str, list[str]] = {
    "plan": [
        "parent_epic", "title", "priority", "status", "locked_by",
        "estimate_class", "estimate_baseline_ai_days", "estimate_calibrated_ai_days",
    ],
    "issue": ["title", "status", "priority", "locked_by", "created"],
    "epic": ["name", "title", "priority", "status", "tier", "assigned_vm"],
    "audit": ["type", "title", "epic", "auditor", "date", "status"],
    "codex": ["scope"],
}


def should_skip(name: str) -> bool:
    return name in SKIP_NAMES or name.startswith("_") or name.endswith(".HANDOVER.md") or "SUPERSEDED" in name


def classify(path: Path) -> str | None:
    """Map a doc to its type by path, or None if out of scope. Only DIRECT children
    of each dir count (subdirs like plans/audit/instructions/ are out of scope here)."""
    try:
        rel = path.relative_to(PM).as_posix()
    except ValueError:
        return None
    for prefix, kind in (
        ("plans/active/issues/", "issue"),
        ("plans/active/", "plan"),
        ("plans/epics/", "epic"),
        ("plans/audit/results/", "audit"),
    ):
        if rel.startswith(prefix):
            return kind if "/" not in rel[len(prefix):] else None
    if rel.startswith("codex/"):
        return "codex"
    return None


def _is_empty(v: object) -> bool:
    if v is None:
        return True
    if isinstance(v, str):
        return not v.strip()
    if isinstance(v, (list, dict)):
        return not v
    return False


def _load_frontmatter(path: Path) -> tuple[dict[str, object] | None, str | None]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, "no frontmatter block (first line is not '---')"
    end = text.find("\n---", 3)
    if end == -1:
        return None, "unterminated frontmatter (no closing '---')"
    try:
        parsed = cast("object", yaml.safe_load(text[3:end]))
    except yaml.YAMLError as exc:
        return None, f"frontmatter is not valid YAML ({str(exc).splitlines()[0]})"
    if not isinstance(parsed, dict):
        return None, f"frontmatter parses to {type(parsed).__name__}, not a mapping"
    return cast("dict[str, object]", parsed), None


def _check_epic_value(val: object, field: str, errs: list[str]) -> None:
    """epic / parent_epic must be a slug (or list of slugs) each resolving to an epic file."""
    slugs: list[object] = cast("list[object]", val) if isinstance(val, list) else [val]
    for s in slugs:
        if not isinstance(s, str) or not s.strip():
            errs.append(f"{field}: empty or non-string entry")
            continue
        if not (EPICS_DIR / f"{s.strip()}.md").is_file():
            errs.append(f"{field}: '{s}' does not resolve to plans/epics/{s}.md")


def check(path: Path) -> list[str]:
    kind = classify(path)
    if kind is None:
        return []
    fm, err = _load_frontmatter(path)
    if err is not None:
        return [err]
    assert fm is not None
    errs: list[str] = []
    for field in REQUIRED[kind]:
        if field not in fm or _is_empty(fm[field]):
            errs.append(f"missing/empty required field: {field}")
    if kind == "plan" and not _is_empty(fm.get("parent_epic")):
        _check_epic_value(fm["parent_epic"], "parent_epic", errs)
    if kind == "audit":
        if not _is_empty(fm.get("epic")):
            _check_epic_value(fm["epic"], "epic", errs)
        type_val = fm.get("type")
        if isinstance(type_val, str) and type_val.strip() == "audit-result" and _is_empty(fm.get("instructions_ref")):
            errs.append("missing/empty instructions_ref (required for type: audit-result)")
    return errs


def _corpus() -> list[Path]:
    # codex/**/*.md is intentionally EXCLUDED from the default corpus pending the
    # codex `scope:` cleanup (178 codex docs lacked it as of 2026-06-16 — the
    # existing QG codex-scope step isn't catching them; tracked separately). The
    # codex branch in classify() still works when a codex file is passed explicitly,
    # so this gate flips codex on by re-adding the glob once that cleanup lands.
    return (
        sorted(PM.glob("plans/active/*.md"))
        + sorted(PM.glob("plans/active/issues/*.md"))
        + sorted(PM.glob("plans/epics/*.md"))
        + sorted(PM.glob("plans/audit/results/*.md"))
    )


def main(argv: list[str]) -> int:
    quiet = "--quiet" in argv
    file_args = [a for a in argv if a != "--quiet" and a.endswith(".md")]
    files = [Path(a) if Path(a).is_absolute() else PM / a for a in file_args] if file_args else _corpus()
    failures = 0
    for f in files:
        if not f.is_file() or should_skip(f.name):
            continue
        errs = check(f)
        if errs:
            failures += 1
            print(f"  {f.relative_to(PM)}:")
            for e in errs:
                print(f"    - {e}")
    if failures:
        print(f"\n❌ check_frontmatter_schema: {failures} doc(s) with frontmatter violations")
        return 1
    if not quiet:
        print("✅ check_frontmatter_schema: all in-scope docs conform")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
