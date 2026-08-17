#!/usr/bin/env python3
"""Flag docs where the Progress Log says "extracted to X" but no checkbox in Todos cites X.

Why this exists: plans/active/issues/na_audit_progress_log_extracted_checkbox_never_flipped_pattern_2026_08_16.md
found the SAME defect shape 4 times in one tradfi-tranche /na-eligibility-audit run: a doc's Progress
Log records "ruled ... extracted to <new AO-dispatch doc>", but the corresponding `- [ ]` checkbox was
never flipped to `[x]` citing that extraction -- so the doc still LOOKS like it has open, undispatched
work even though the real work already moved to a live, dispatchable plan elsewhere. This script does
the mechanical cross-check (Progress Log "extracted to" claims vs. Todos-section citations) that would
have caught all 4 instances without a full agentic re-read.

Citation scope is the WHOLE Todos section (open + closed checkboxes), not just open ones: the corpus's
own fix pattern for this defect is to flip the checkbox to `[x]` AND add the citation in the SAME edit
(see the real fixed instances this script's own smoke test reproduces) -- so a correctly-fixed doc has
the citation on a now-CLOSED checkbox, and a doc with one closed+cited extraction todo plus OTHER,
unrelated open todos is NOT a defect. The actual bug shape is: X is named in the Progress Log but never
appears ANYWHERE in the Todos section at all.

Scope matches the source issue doc's "Recommended decision": every `assigned_vm: NA` doc with status
active/open that has at least one open checkbox.

# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: never (this class of gap -- a narrative Progress Log note landing without its mechanical
# checkbox-flip counterpart -- is a standing corpus-hygiene risk, not a one-off cleanup)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]

DOC_TREES = ["plans/active/*.md", "plans/active/issues/*.md"]

# Top-level checkbox bullet: "- [ ]" (open) / "- [x]"/"- [X]" (closed); "*" bullet variant confirmed
# live elsewhere in this corpus (see generate_na_doc_tranche_inventory.py's own CHECKBOX_RE comment).
_OPEN_CHECKBOX_RE = re.compile(r"^\s*[-*]\s*\[ \]", re.MULTILINE)

# "extracted ... to ... <path>.md" -- bounded, non-greedy windows so it doesn't run away across an
# entire Progress Log entry. DOTALL so a wrapped/multi-line note still matches.
_EXTRACTED_TO_RE = re.compile(
    r"extracted\b.{0,150}?\bto\b.{0,80}?([A-Za-z0-9][A-Za-z0-9_\-]*\.md)",
    re.IGNORECASE | re.DOTALL,
)


def _load_docspec():
    spec = importlib.util.spec_from_file_location("docspec", PM / "scripts" / "docs" / "docspec.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/docs/docspec.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["docspec"] = mod
    spec.loader.exec_module(mod)
    return mod


ds = _load_docspec()


def _section(text: str, header: str) -> str:
    """Text from '## <header>' to the next top-level '## ' header (or EOF)."""
    m = re.search(rf"^## {re.escape(header)}\s*$", text, re.MULTILINE)
    if m is None:
        return ""
    rest = text[m.end() :]
    nxt = re.search(r"^## ", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


def extracted_targets(progress_log_text: str) -> list[str]:
    """Basenames named via 'extracted ... to <path>.md' phrasing in the Progress Log.

    Excludes `*_progress_log_history_*.md` targets -- a SEPARATE, well-established convention
    (25 archived instances corpus-wide) for line-cap remediation: verbatim-splitting a doc's own OLD
    Progress Log prose into an archive doc to shrink it back under the 1000-line hard cap. That kind of
    "extraction" moves narrative history, not dispatchable work, so no checkbox is ever expected to cite
    it -- flagging it would be a structural false positive on a distinct, already-understood pattern,
    not an instance of the checkbox-never-flipped defect this checker targets.
    """
    return sorted(
        {
            os.path.basename(m.group(1))
            for m in _EXTRACTED_TO_RE.finditer(progress_log_text)
            if "_progress_log_history_" not in m.group(1)
        }
    )


def has_open_checkbox(todos_text: str) -> bool:
    return _OPEN_CHECKBOX_RE.search(todos_text) is not None


def find_uncited_extractions(text: str) -> list[dict[str, object]]:
    """Return one finding per Progress-Log 'extracted to X' claim never cited anywhere in Todos.

    Only scans docs with at least one open checkbox (the scope this defect matters for -- a doc with
    zero open todos is either already archived or otherwise not this check's concern).
    """
    todos_text = _section(text, "Todos")
    progress_text = _section(text, "Progress Log")
    if not todos_text or not progress_text or not has_open_checkbox(todos_text):
        return []
    findings: list[dict[str, object]] = []
    for target in extracted_targets(progress_text):
        if target not in todos_text:
            findings.append({"target": target})
    return findings


def _iter_docs() -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for pat in DOC_TREES:
        for p in PM.glob(pat):
            rel = p.relative_to(PM).as_posix()
            if p.is_file() and p not in seen and not rel.startswith(".claude/"):
                seen.add(p)
                out.append(p)
    return sorted(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a summary")
    args = parser.parse_args(argv)

    results: list[dict[str, object]] = []
    for path in _iter_docs():
        rel = path.relative_to(PM).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            fm, _ = ds.parse_frontmatter(text)
        except yaml.YAMLError:
            continue
        if fm is None:
            continue
        assigned_vm = fm.get("assigned_vm")
        status = fm.get("status")
        if not (isinstance(assigned_vm, str) and assigned_vm.strip().upper() == "NA"):
            continue
        if status not in ("active", "open"):
            continue

        findings = find_uncited_extractions(text)
        if findings:
            results.append({"path": rel, "findings": findings})

    if args.json:
        print(json.dumps(results, indent=1))
        return 0

    if not results:
        print("No uncited 'extracted to' claims found.")
        return 0
    print(f"{len(results)} doc(s) with an uncited 'extracted to' claim:")
    for r in results:
        print(f"  {r['path']}")
        for f in r["findings"]:
            print(f"    -> extracted to {f['target']!r} but never cited in the Todos section")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
