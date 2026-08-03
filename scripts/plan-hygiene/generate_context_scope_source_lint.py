#!/usr/bin/env python3
"""Post-hoc deterministic lint for /context-scout Phase 3: flag docs whose `context_scope` has
ZERO source-path entries even though the doc body names a plausible source-code token.

Why this exists: Phase 1's source-path hunting is pure agent judgment with no other check that it
actually ran as specified -- confirmed miss on a live repro:
plans/active/issues/context_scout_source_hunting_gap_2026_08_03.md. This script is a cheap,
deterministic, regex-only second pass -- NOT a replacement for Phase 1's judgment, and NOT a
blocking gate (no baseline, not wired into run_hygiene_sweep.sh) -- it only surfaces candidates for
a human to spot-check in the Phase 3 report. A body mentioning a `*_service` token or a `.py`
filename doesn't guarantee that path is the right thing to cite (could be a false positive: a
generic phrase, a renamed/deleted file, a doc discussing a service in the abstract) -- advisory
only, matching the SKILL.md Phase 3 contract ("report these -- a doc with genuinely no
reading-list is fine, but worth surfacing").

A `context_scope` entry counts as a SOURCE-PATH entry if it does not start with `/codex/` or
`/plans/` -- those two prefixes are reserved for codex/plan-doc citations per this workspace's
leading-slash cross-reference convention (/codex/11-project-management/
cross-reference-path-convention.md). Anything else (a bare repo-relative path, e.g.
`market-data-processing-service/market_data_processing_service/app/core/dependency_checker.py`) is
a source path.

# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: never (standing Phase-3 lint for the /context-scout skill)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]

DOC_TREES = ["plans/active/*.md", "plans/active/issues/*.md"]
IN_SCOPE_STATUS = {
    "plan": {"active", "blocked", "paused"},
    "issue": {"open", "blocked"},
}

_SERVICE_TOKEN_RE = re.compile(r"\b\w+_service\b")
_PY_FILE_RE = re.compile(r"\b[\w./-]+\.py\b")
_MAX_FLAGGED_TOKENS_PER_DOC = 5

# SKILL.md Phase 1 step 4's own stated exemption: these doc shapes are legitimately code-free
# (a dispatch-batch coordinator, a *_finalize gate) -- a codex/plan-only context_scope on one of
# these is the CORRECT complete answer, not a scouting miss, so this lint must not cry wolf on them.
_EXEMPT_FILENAME_RE = re.compile(r"satellite_ao_dispatch_batch\d+|_finalize_\d{4}_\d{2}_\d{2}\.md$")


def _load_docspec():
    spec = importlib.util.spec_from_file_location("docspec", PM / "scripts" / "docs" / "docspec.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/docs/docspec.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["docspec"] = mod
    spec.loader.exec_module(mod)
    return mod


ds = _load_docspec()


def _iter_docs() -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for pat in DOC_TREES:
        for p in PM.glob(pat):
            if p.is_file() and p not in seen:
                seen.add(p)
                out.append(p)
    return sorted(out)


def _normalize_context_scope(raw: object) -> list[str]:
    """Coerce a `context_scope` field to a flat list of strings, tolerating malformed frontmatter
    (a stray nested list or dict) rather than crashing -- this lint is advisory, not a schema
    validator; a doc with malformed `context_scope` YAML is a separate finding, not this script's
    job to fix."""
    if isinstance(raw, str):
        return [raw]
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, list):
            out.extend(_normalize_context_scope(item))
        # dicts and other shapes are dropped -- not a citable path
    return out


def _is_source_path(entry: str) -> bool:
    return not (entry.startswith("/codex/") or entry.startswith("/plans/"))


def _repo_path_patterns(repos: list[str]) -> list[re.Pattern[str]]:
    """A `repos:` frontmatter name (either hyphen or underscore form) followed by a path-like
    token, e.g. `market-tick-data-service/scripts/foo.py` or
    `market_tick_data_service.engine.orchestrator`."""
    patterns = []
    for repo in repos:
        if not isinstance(repo, str) or not repo:
            continue
        for variant in {repo, repo.replace("-", "_")}:
            patterns.append(re.compile(re.escape(variant) + r"[/.][\w./-]+"))
    return patterns


def _candidate_tokens(body: str, repos: list[str]) -> list[str]:
    found: list[str] = []
    for m in _SERVICE_TOKEN_RE.finditer(body):
        found.append(m.group(0))
    for m in _PY_FILE_RE.finditer(body):
        found.append(m.group(0))
    for pattern in _repo_path_patterns(repos):
        for m in pattern.finditer(body):
            found.append(m.group(0))
    seen: set[str] = set()
    out: list[str] = []
    for tok in found:
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out


def _uncovered(tokens: list[str], context_scope: list[str]) -> list[str]:
    scope_blob = " ".join(context_scope).lower()
    return [t for t in tokens if t.lower() not in scope_blob][:_MAX_FLAGGED_TOKENS_PER_DOC]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a summary table")
    args = parser.parse_args(argv)

    flagged = []
    scanned = 0
    for path in _iter_docs():
        rel = path.relative_to(PM).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            fm, body = ds.parse_frontmatter(text)
        except yaml.YAMLError:
            continue
        if fm is None:
            continue
        doc_type = fm.get("doc_type")
        if doc_type not in IN_SCOPE_STATUS:
            continue
        status = fm.get("status")
        if status not in IN_SCOPE_STATUS[doc_type]:
            continue
        if _EXEMPT_FILENAME_RE.search(path.name):
            continue

        context_scope = _normalize_context_scope(fm.get("context_scope"))
        if not context_scope:
            continue  # never-scouted -- Phase 0's own verdict already covers this doc

        if any(_is_source_path(e) for e in context_scope):
            continue  # already has >=1 source-path entry -- nothing to flag

        scanned += 1
        repos = fm.get("repos") or []
        if isinstance(repos, str):
            repos = [repos]
        tokens = _candidate_tokens(body, repos)
        uncovered = _uncovered(tokens, context_scope)
        if uncovered:
            flagged.append({"path": rel, "candidate_tokens": uncovered})

    if args.json:
        print(json.dumps({"scanned": scanned, "flagged": flagged}, indent=1))
        return 0

    print(f"Docs with zero source-path context_scope entries scanned: {scanned}")
    print(f"Flagged for human spot-check: {len(flagged)}")
    for f in flagged:
        print(f"  {f['path']}")
        for tok in f["candidate_tokens"]:
            print(f"      - {tok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
