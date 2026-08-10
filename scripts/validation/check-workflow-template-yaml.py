#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Pre-flight: verify every workflow template still parses as valid YAML after prettier would
reformat it -- so a future prettier-mangled placeholder (the `{{RUNS_ON}}` -> `{ { RUNS_ON } }`
class, cicd escalation agt-62ba62, 2026-08-07 --
`plans/active/issues/workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md`)
is caught at ROLLOUT time here, not after it has already propagated to every consuming repo and
surfaced only later as a red `quality-gates-v2`.

Two template shapes live in `scripts/workflow-templates/`:
  - `*.yml`       flat-copy templates -- byte-identical content (only a `__RUNS_ON__`
    substitution) lands in every consuming repo's `.github/workflows/`. These go through THIS
    repo's own `prettier-autostage` pre-commit hook on every commit here (`types_or: [yaml]`
    matches `.yml`), so they are exactly the files a future bare `{{PLACEHOLDER}}` token could
    silently mangle the same way `{{RUNS_ON}}` did. Checked by reformatting via
    `prettier --stdin-filepath <name>` (same pinned min-version convention as
    `scripts/hooks/prettier-autostage.sh`) and `yaml.safe_load()`-ing the result.
  - `*.yml.tmpl`  sed-substituted templates (`{{DEP_REPOS}}`, `{{CI_TRIGGER_BRANCH}}`, etc,
    substituted by `rollout-workflow-templates.sh` itself) -- these are NOT valid standalone
    YAML pre-substitution by design, and are NOT touched by the prettier hook (its extension
    filter excludes `.tmpl`), so they can't suffer the exact same commit-time mangling. Checked
    by first substituting every `{{TOKEN}}` / `__TOKEN__` placeholder with a generic safe scalar
    (mirroring what the rollout script's own sed passes do), THEN running the same
    prettier-reformat + `yaml.safe_load()` pass on the rendered result -- this is what actually
    lands as a real `.yml` file in a consuming repo, so it deserves the same check.

Tool-graceful: if no prettier binary meeting the minimum version can be resolved (mirrors
`prettier-autostage.sh`'s own fallback chain: repo-local -> system -> pinned `npx` fetch), the
prettier-reformat step is SKIPPED with a warning and the gate falls back to a raw
`yaml.safe_load()` of the (rendered, for `.tmpl`) content -- a weaker check that still catches
content that is already broken, just not a hypothetical future prettier-only mangling.

Usage:
    python3 check-workflow-template-yaml.py                 # scan scripts/workflow-templates/
    python3 check-workflow-template-yaml.py --dir PATH       # scan an explicit dir
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

import yaml

PRETTIER_MIN_VERSION = "3.9.5"

# The KNOWN, sanctioned .tmpl placeholder tokens rollout-workflow-templates.sh's own sed passes
# substitute, mapped to an arbitrary safe dummy scalar -- mirrors those sed passes just enough to
# make a .tmpl file's OWN placeholders (which are never valid standalone YAML by design) parse.
# Deliberately NOT a blanket "any {{...}}/__..__ token" regex: a blanket substitution would
# neutralize a reintroduced BAD token (e.g. a future placeholder mistakenly written as
# `{{RUNS_ON}}` instead of `__RUNS_ON__`) before prettier ever sees it, defeating the whole point
# of this check. Only KNOWN tokens get substituted; anything else is left raw so a rogue
# curly-brace placeholder still hits the prettier-mangling class this check exists to catch.
_KNOWN_TMPL_TOKENS: dict[str, str] = {
    "{{DEP_REPOS}}": "example-repo",
    "{{CI_TRIGGER_BRANCH}}": "main",
    "{{QG_RUNNER_LABELS}}": "",
    "__REPO_NAME__": "example-repo",
    "__SOURCE_DIR__": "example_repo",
    "__VERSION_SOURCE__": "pyproject.toml",
    "__RUNS_ON__": "ubuntu-latest",
}


def _version_ok(version: str) -> bool:
    parts_min = [int(p) for p in PRETTIER_MIN_VERSION.split(".")]
    try:
        parts_got = [int(p) for p in version.strip().split(".")]
    except ValueError:
        return False
    return parts_got >= parts_min


def resolve_prettier(repo_root: Path) -> list[str] | None:
    """Return the argv prefix for a prettier invocation meeting PRETTIER_MIN_VERSION, or None."""
    local = repo_root / "node_modules" / ".bin" / "prettier"
    candidates: list[list[str]] = []
    if local.is_file():
        candidates.append([str(local)])
    if shutil.which("prettier"):
        candidates.append(["prettier"])
    for argv in candidates:
        try:
            r = subprocess.run([*argv, "--version"], capture_output=True, text=True, timeout=20, check=False)
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode == 0 and _version_ok(r.stdout):
            return argv
    if shutil.which("npx"):
        # Pinned fetch, mirrors prettier-autostage.sh -- npm caches after the first run.
        return ["npx", "-y", f"prettier@{PRETTIER_MIN_VERSION}"]
    return None


def prettier_reformat(prettier_argv: list[str], filename: str, content: str) -> tuple[bool, str]:
    """Run `content` through prettier as if it were `filename`. Returns (ok, reformatted_or_stderr)."""
    try:
        r = subprocess.run(
            [*prettier_argv, "--stdin-filepath", filename, "--parser", "yaml"],
            input=content,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    if r.returncode != 0:
        return False, r.stderr.strip()
    return True, r.stdout


def render_tmpl_placeholders(content: str) -> str:
    """Substitute only the KNOWN sanctioned .tmpl tokens (see _KNOWN_TMPL_TOKENS) with a dummy
    safe scalar -- everything else (including a rogue/reintroduced placeholder) is left raw.
    """
    for token, dummy in _KNOWN_TMPL_TOKENS.items():
        content = content.replace(token, dummy)
    return content


def check_template(path: Path, prettier_argv: list[str] | None) -> str | None:
    """Return an error message if `path` fails to parse as YAML, else None."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return f"could not read file: {exc}"

    is_tmpl = path.name.endswith(".yml.tmpl")
    if is_tmpl:
        content = render_tmpl_placeholders(content)

    if prettier_argv is not None:
        ok, result = prettier_reformat(prettier_argv, path.name.removesuffix(".tmpl"), content)
        if not ok:
            return f"prettier itself failed to parse this as YAML: {result}"
        content = result

    try:
        yaml.safe_load(content)
    except yaml.YAMLError as exc:
        return f"invalid YAML{' after prettier reformat' if prettier_argv else ''}: {exc}"
    return None


def check_dir(scan_dir: Path, prettier_argv: list[str] | None) -> list[tuple[Path, str]]:
    if not scan_dir.is_dir():
        return []
    failures: list[tuple[Path, str]] = []
    files = sorted({*scan_dir.glob("*.yml"), *scan_dir.glob("*.yml.tmpl")})
    for f in files:
        err = check_template(f, prettier_argv)
        if err:
            failures.append((f, err))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--dir",
        default=None,
        help="Template directory to check (default: scripts/workflow-templates/ next to this script)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parents[1]
    scan_dir = Path(cast(str, args.dir)) if args.dir else repo_root / "scripts" / "workflow-templates"

    if not scan_dir.is_dir():
        print(f"check-workflow-template-yaml: no such dir {scan_dir} — nothing to check.")
        return 0

    prettier_argv = resolve_prettier(repo_root)
    if prettier_argv is None:
        print(
            f"⚠ check-workflow-template-yaml: no prettier >={PRETTIER_MIN_VERSION} resolvable (no local install, "
            "no system prettier, no npx) — falling back to a raw yaml.safe_load() check (will not catch a "
            "hypothetical future prettier-only mangling, only content that is already broken)."
        )

    failures = check_dir(scan_dir, prettier_argv)
    if failures:
        print(f"\n❌ {len(failures)} workflow template(s) fail to parse as YAML:")
        for path, err in failures:
            print(f"  {path.relative_to(scan_dir.parent) if scan_dir.parent in path.parents else path}: {err}")
        return 1

    checked = len(list(scan_dir.glob("*.yml"))) + len(list(scan_dir.glob("*.yml.tmpl")))
    suffix = " (prettier-verified)" if prettier_argv else " (raw yaml.safe_load only — prettier unavailable)"
    print(f"✅ check-workflow-template-yaml: all {checked} template(s) in {scan_dir.name}/ parse cleanly{suffix}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
