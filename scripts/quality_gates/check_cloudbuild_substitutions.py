#!/usr/bin/env python3
"""QG STEP 5.19 — cloudbuild.yaml unescaped-substitution validator.

Cloud Build parses EVERY step string (``args`` / ``script`` / ``env``) for
``$WORD`` / ``${WORD}`` substitution references — including bash COMMENT lines
inside ``args: - |`` blocks. A reference that is neither a Cloud Build builtin
(``$PROJECT_ID``, ``$SHORT_SHA``, …) nor a ``_``-prefixed user substitution
makes Cloud Build REJECT the whole config — and the rejection is SILENT (no
build record / a FAILURE record with empty substitutions; no GitHub check, no
Slack). Shell variables and command substitutions inside cloudbuild bash
blocks must be ``$$``-escaped (``$$VAR``, ``$$(cmd)``).

Incident: plans/active/issues/
cloudbuild_silent_failures_no_alerting_no_validation_2026_06_10.md (Gap 3) —
two config pushes fired ZERO builds with no signal; the second rejection was a
bash comment that mentioned shell vars with single dollars.

What is flagged (scan is over the YAML-PARSED step strings, so YAML ``#``
comments are naturally exempt — exactly mirroring what Cloud Build sees):

1. ``$WORD`` / ``${WORD}`` where WORD is NOT a Cloud Build builtin and NOT
   ``_``-prefixed. ``$$`` is honored as the escape (consumed first by the scan
   regex, so ``$$VAR`` / ``$$$PROJECT_ID`` resolve correctly).
2. Bare ``$(`` (un-escaped command substitution) — must be ``$$(``.

Usage::

    # explicit file(s) (run by base-service.sh STEP 5.19 from the repo root):
    python check_cloudbuild_substitutions.py cloudbuild.yaml

    # one manifest repo (resolves <workspace>/<repo>/cloudbuild.yaml):
    python check_cloudbuild_substitutions.py --repo execution-service

    # every workspace-manifest.json repo that has a cloudbuild.yaml:
    python check_cloudbuild_substitutions.py --all

Exit codes: 0 = clean; 1 = violations; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

import yaml

SCRIPT_DIR: Final[Path] = Path(__file__).resolve().parent
PM_ROOT: Final[Path] = SCRIPT_DIR.parent.parent
DEFAULT_WORKSPACE_ROOT: Final[Path] = PM_ROOT.parent

#: Cloud Build builtin substitutions — always legal as bare ``$WORD``/``${WORD}``.
CLOUD_BUILD_BUILTINS: Final[frozenset[str]] = frozenset(
    {
        "PROJECT_ID",
        "PROJECT_NUMBER",
        "BUILD_ID",
        "COMMIT_SHA",
        "SHORT_SHA",
        "REVISION_ID",
        "REPO_NAME",
        "REPO_FULL_NAME",
        "BRANCH_NAME",
        "TAG_NAME",
        "REF_NAME",
        "TRIGGER_NAME",
        "TRIGGER_BUILD_CONFIG_PATH",
        "LOCATION",
        "SERVICE_ACCOUNT_EMAIL",
        "SERVICE_ACCOUNT",
    }
)

#: Step keys whose string values Cloud Build substitution-scans (our scope).
SCANNED_STEP_KEYS: Final[tuple[str, ...]] = ("args", "script", "env")

#: The remedy line printed on violations (also imported by rollout-cloudbuild.py).
REMEDY: Final[str] = "shell vars in cloudbuild bash blocks need $$; even COMMENT lines are scanned by the validator"

#: Token scan. Alternation order is the escape semantics: ``$$`` is consumed
#: FIRST (non-overlapping finditer), so ``$$VAR`` / ``$$(`` never reach the
#: substitution branches and ``$$$PROJECT_ID`` resolves as escape + builtin.
#: (Equivalent to a negative-lookbehind-for-$ scan, but also correct for runs
#: of dollars, where a plain lookbehind mis-rejects the post-escape token.)
# NOTE: bare ``$(`` is deliberately NOT a token — Cloud Build only substitutes word-keys
# (``$WORD`` / ``${WORD}``); ``$(`` never parses as a substitution and passes through to bash
# as a literal command substitution (verified against live GCB 2026-06-10: 17 fleet configs
# carry bare ``$(cmd)`` in bash blocks and build fine). Flagging it would red 17 repos on a
# non-issue. Only word-key tokens (and the ``$$`` escape) are scanned.
_TOKEN_RE: Final[re.Pattern[str]] = re.compile(r"\$\$|\$\{(\w+)\}|\$(\w+)")


@dataclass(frozen=True)
class Violation:
    """One unescaped-substitution occurrence inside a cloudbuild step string."""

    file: str
    step_id: str
    varname: str

    def render(self) -> str:
        return f"{self.file}:{self.step_id}:{self.varname}"


def find_unescaped_substitutions(text: str) -> list[str]:
    """Return the flagged tokens (unescaped non-builtin var names) in one step string."""
    flagged: list[str] = []
    for match in _TOKEN_RE.finditer(text):
        if match.group(0) == "$$":
            continue  # escape — also neutralises $$VAR / $${VAR}
        word = match.group(1) if match.group(1) is not None else match.group(2)
        if word is None:  # pragma: no cover — regex guarantees a group
            continue
        if word.startswith("_") or word in CLOUD_BUILD_BUILTINS:
            continue
        flagged.append(word)
    return flagged


def _iter_strings(value: object) -> Iterator[str]:
    """Yield every string in a scalar-or-list step field value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in cast("list[object]", value):
            if isinstance(item, str):
                yield item


def scan_cloudbuild_text(text: str, label: str) -> list[Violation]:
    """Scan a cloudbuild yaml document (as text) for unescaped substitutions."""
    try:
        loaded = cast("object", yaml.safe_load(text))
    except yaml.YAMLError as exc:
        # An unparseable config is its own (loud) violation class.
        return [Violation(file=label, step_id="<yaml-parse>", varname=f"YAML error: {exc}")]
    if not isinstance(loaded, dict):
        return []
    doc = cast("dict[str, object]", loaded)
    steps_obj = doc.get("steps")
    if not isinstance(steps_obj, list):
        return []
    violations: list[Violation] = []
    seen: set[tuple[str, str]] = set()
    for idx, step_obj in enumerate(cast("list[object]", steps_obj)):
        if not isinstance(step_obj, dict):
            continue
        step = cast("dict[str, object]", step_obj)
        raw_id = step.get("id")
        step_id = str(raw_id) if raw_id is not None else f"step[{idx}]"
        for key in SCANNED_STEP_KEYS:
            for chunk in _iter_strings(step.get(key)):
                for token in find_unescaped_substitutions(chunk):
                    dedupe_key = (step_id, token)
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    violations.append(Violation(file=label, step_id=step_id, varname=token))
    return violations


def scan_cloudbuild(path: Path) -> list[Violation]:
    """Scan a cloudbuild yaml file for unescaped substitutions."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [Violation(file=str(path), step_id="<io>", varname=f"read error: {exc}")]
    return scan_cloudbuild_text(text, label=str(path))


# ── Target resolution ────────────────────────────────────────────────────────


def _manifest_repos(workspace_root: Path) -> list[str]:
    manifest_path = workspace_root / "unified-trading-pm" / "workspace-manifest.json"
    if not manifest_path.exists():
        manifest_path = PM_ROOT / "workspace-manifest.json"
    with manifest_path.open(encoding="utf-8") as f:
        manifest = cast("object", json.load(f))
    if not isinstance(manifest, dict):
        return []
    manifest_doc = cast("dict[str, object]", manifest)
    repos_obj: object = manifest_doc.get("repositories") or manifest_doc.get("repos")
    if not isinstance(repos_obj, dict):
        return []
    return sorted(str(name) for name in cast("dict[object, object]", repos_obj))


def _resolve_targets(
    paths: list[Path], repo: str | None, all_repos: bool, workspace_root: Path
) -> tuple[list[Path], list[str]]:
    """Return (files-to-scan, errors). Exactly one selection mode applies."""
    errors: list[str] = []
    if paths:
        files: list[Path] = []
        for p in paths:
            if p.is_file():
                files.append(p)
            else:
                errors.append(f"not a file: {p}")
        return files, errors
    if repo is not None:
        candidate = workspace_root / repo / "cloudbuild.yaml"
        if not candidate.is_file():
            errors.append(f"--repo {repo}: no cloudbuild.yaml at {candidate}")
            return [], errors
        return [candidate], errors
    if all_repos:
        files = []
        for name in _manifest_repos(workspace_root):
            candidate = workspace_root / name / "cloudbuild.yaml"
            if candidate.is_file():
                files.append(candidate)
        return files, errors
    errors.append("nothing to scan — pass cloudbuild.yaml path(s), --repo <name>, or --all")
    return [], errors


# ── main ─────────────────────────────────────────────────────────────────────


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="cloudbuild.yaml unescaped-substitution validator (QG STEP 5.19).")
    _ = parser.add_argument("paths", nargs="*", type=Path, help="cloudbuild yaml file path(s).")
    _ = parser.add_argument(
        "--repo", default=None, help="Manifest repo name — scans <workspace>/<repo>/cloudbuild.yaml."
    )
    _ = parser.add_argument(
        "--all", action="store_true", dest="all_repos", help="Scan every manifest repo that has a cloudbuild.yaml."
    )
    _ = parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help="Workspace root for --repo / --all resolution (default: the PM checkout's parent).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    paths = cast("list[Path]", args.paths)
    repo = cast("str | None", args.repo)
    all_repos = cast("bool", args.all_repos)
    workspace_root = cast("Path", args.workspace_root).resolve()

    files, errors = _resolve_targets(paths, repo, all_repos, workspace_root)
    if errors:
        for err in errors:
            print(f"[check_cloudbuild_substitutions] {err}", file=sys.stderr)
        return 2
    if not files:
        print("[check_cloudbuild_substitutions] no cloudbuild.yaml files in scope — nothing to check.")
        return 0

    all_violations: list[Violation] = []
    for path in files:
        all_violations.extend(scan_cloudbuild(path))

    if not all_violations:
        print(f"[check_cloudbuild_substitutions] OK — {len(files)} file(s) clean (no unescaped substitutions).")
        return 0

    for violation in all_violations:
        print(violation.render(), file=sys.stderr)
    print(
        f"\n[check_cloudbuild_substitutions] {len(all_violations)} unescaped substitution(s) across "
        f"{len({v.file for v in all_violations})} file(s). Cloud Build SILENTLY rejects such configs "
        f"(no build record, no GitHub check). Remedy: {REMEDY}.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
