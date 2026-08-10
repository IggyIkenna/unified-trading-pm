#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Pre-rollout lint: verify each workflow template parses as YAML after prettier.

Motivation (workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md):
`prettier --write` deterministically reformats a bare `{{PLACEHOLDER}}` YAML
flow-mapping-shaped token into `{ { PLACEHOLDER } }` — invalid YAML (a nested
flow mapping used as an unhashable key) that GitHub silently refuses to schedule.
That class shipped a broken `runs-on:` to 7 fleet repos on 2026-08-05 and only
surfaced later as a red `quality-gates-v2`. This gate simulates the prettier pass
the committed template experiences (via the pre-commit hook's prettier-autostage),
then `yaml.safe_load`s the result — so a future prettier-mangled placeholder
fails the ROLLOUT script's own pre-flight at rollout time, not after propagating
to every consuming repo.

`.tmpl` templates (e.g. quality-gates-v2.yml.tmpl) legitimately carry `{{...}}`
substitution tokens that only make sense after the rollout script's sed pass. For
those, the known tokens are replaced with representative dummy values (mirroring
rollout-workflow-templates.sh's own substitution) BEFORE the prettier+parse
simulation — an UNKNOWN `{{FOO}}` token survives substitution and is caught
exactly like a flat-copy placeholder.

Prettier-unavailable fallback: mirrors check-action-pins.py's network-graceful
convention. If no prettier >= 3.9.5 resolves (repo-local node_modules, PATH, or a
pinned `npx -y prettier@3.9.5` fetch), the lint falls back to parsing WITHOUT the
prettier simulation — still catching an already-mangled committed template (the
primary failure mode at rollout time), at the cost of missing a token prettier
WOULD mangle but has not yet. Pass `--no-prettier` to force this mode (CI under
`--block-network`).

Usage:
    python3 check-template-yaml.py                # scan scripts/workflow-templates/
    python3 check-template-yaml.py --dir PATH     # scan an explicit dir
    python3 check-template-yaml.py --no-prettier  # parse-only (no prettier simulation)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml  # PyYAML — PM scripts are ruff-gated (not basedpyright-gated); pyyaml is a venv dep.

# Any prettier OLDER than this is never used (2026-07-14: <3.9.5 deterministically
# corrupts markdown — same minimum-version guard as scripts/hooks/prettier-autostage.sh).
PRETTIER_MIN_VERSION = "3.9.5"

# Known `.tmpl` substitution tokens + representative dummy values, mirroring the
# rollout script's own sed pass (rollout-workflow-templates.sh). A token added
# there MUST be mirrored here or a legit template would false-positive. Values are
# shaped to match the real rollout output (e.g. `{{QG_RUNNER_LABELS}}` renders as
# a JSON array string, `{{DEP_REPOS}}` as a space-separated list).
TMPL_SUBSTITUTIONS: tuple[tuple[str, str], ...] = (
    ("{{DEP_REPOS}}", "dep1 dep2"),
    ("__REPO_NAME__", "test-repo"),
    ("__SOURCE_DIR__", "test_repo"),
    ("__VERSION_SOURCE__", "pyproject.toml"),
    ("{{CI_TRIGGER_BRANCH}}", "main"),
    ("{{QG_RUNNER_LABELS}}", '["ubuntu-latest"]'),
    ("__RUNS_ON__", "ubuntu-latest"),
)


def substitute_tmpl(text: str) -> str:
    """Replace known `.tmpl` substitution tokens with representative values.

    A `.tmpl` file is not parseable as YAML until the rollout script's sed pass
    runs — substituting known tokens with values in the same shape the rollout
    produces makes the template lintable, while leaving any UNKNOWN `{{...}}`
    token in place so it is caught as the bug class it is.
    """
    out = text
    for token, value in TMPL_SUBSTITUTIONS:
        out = out.replace(token, value)
    return out


def lint_yaml(text: str) -> list[str]:
    """Return YAML parse errors for `text` (empty list = parses cleanly)."""
    try:
        yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [str(exc)]
    return []


def _version_ok(version: str) -> bool:
    """True iff `version` >= PRETTIER_MIN_VERSION (numeric, part-wise compare)."""
    try:
        want = [int(x) for x in PRETTIER_MIN_VERSION.split(".")]
        got = [int(x) for x in version.split(".")]
    except ValueError:
        return False
    return got >= want


def _prettier_version(cmd: list[str]) -> str | None:
    try:
        r = subprocess.run([*cmd, "--version"], capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() or None


def resolve_prettier() -> str | None:
    """Return a prettier invocation (>= PRETTIER_MIN_VERSION), or None.

    Precedence mirrors scripts/hooks/prettier-autostage.sh: repo-local
    node_modules/.bin/prettier, then a PATH prettier, then a pinned
    `npx -y prettier@<min>` fetch (npm-cached after first use). A resolved binary
    older than the min version is NEVER used — same corruption guard as the hook.
    """
    repo_root = Path(__file__).resolve().parents[2]
    local = repo_root / "node_modules" / ".bin" / "prettier"
    if local.is_file():
        v = _prettier_version([str(local)])
        if v is not None and _version_ok(v):
            return str(local)
    if shutil.which("prettier"):
        v = _prettier_version(["prettier"])
        if v is not None and _version_ok(v):
            return "prettier"
    if shutil.which("npx"):
        return f"npx -y prettier@{PRETTIER_MIN_VERSION}"
    return None


def lint_template_file(path: Path, prettier: str | None) -> list[str]:
    """Lint one template: substitute (.tmpl), prettier-simulate, then parse.

    Returns a list of human-readable problems (empty = safe to roll out). With
    `prettier` set, the content is written to a scratch copy and prettier
    `--parser yaml` runs on it first — the exact pass the pre-commit hook would
    apply — then the reformatted result is parsed. Without it, the content is
    parsed as-is (parse-only fallback).
    """
    name = path.name
    text = path.read_text(encoding="utf-8")
    if name.endswith(".tmpl"):
        text = substitute_tmpl(text)
    mode = "direct"
    if prettier is not None:
        mode = "prettier"
        with tempfile.TemporaryDirectory(prefix="tmpl-yaml-lint-") as td:
            scratch = Path(td) / "tpl.yml"
            scratch.write_text(text, encoding="utf-8")
            try:
                r = subprocess.run(
                    [*prettier.split(), "--parser", "yaml", "--write", str(scratch)],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                return [f"{name}: prettier invocation failed: {exc}"]
            if r.returncode != 0:
                # prettier refusing to format IS a caught break (same bug class).
                detail = (r.stderr.strip() or r.stdout.strip())[:400]
                return [f"{name}: prettier failed to format (likely invalid YAML): {detail}"]
            text = scratch.read_text(encoding="utf-8")
    errors = lint_yaml(text)
    return [f"{name}: not valid YAML ({mode} lint): {err}" for err in errors]


def _scan_dir(args: argparse.Namespace) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    if args.templates:
        return repo_root / "scripts" / "workflow-templates"
    return Path(args.dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint workflow templates as YAML after prettier.")
    parser.add_argument(
        "--dir", default=".github/workflows", help="Templates dir to scan (default: .github/workflows)."
    )
    parser.add_argument("--templates", action="store_true", help="Scan scripts/workflow-templates/ (pre-rollout gate).")
    parser.add_argument("--no-prettier", action="store_true", help="Skip the prettier simulation; parse-only.")
    args = parser.parse_args()

    scan_dir = _scan_dir(args)
    if not scan_dir.is_dir():
        print(f"check-template-yaml: no such dir {scan_dir} — nothing to check.")
        return 0

    prettier: str | None = None if args.no_prettier else resolve_prettier()
    if args.no_prettier:
        print("check-template-yaml: --no-prettier — parse-only mode (no prettier simulation).")
    elif prettier is None:
        print(
            "⚠ check-template-yaml: no prettier >= 3.9.5 available — parse-only fallback "
            "(an already-mangled committed template is still caught)."
        )

    files = sorted({p for pat in ("*.yml", "*.yaml", "*.yml.tmpl", "*.tmpl") for p in scan_dir.glob(pat)})
    if not files:
        print(f"check-template-yaml: no template files in {scan_dir}.")
        return 0

    failures: list[str] = []
    for f in files:
        problems = lint_template_file(f, prettier)
        if problems:
            failures.extend(problems)
        else:
            print(f"✅ {f.relative_to(scan_dir)}: parses as YAML after {prettier or 'direct'} lint.")

    if failures:
        print("\n❌ template-content lint FAILED:")
        for problem in failures:
            print(f"  {problem}")
        print(
            "\n  A template that does not survive prettier's format pass will ship broken to every consuming repo"
            "\n  (2026-08-05 runs-on incident). Fix the template before rollout — if you just added a `{{PLACEHOLDER}}`"
            "\n  token, use the double-underscore convention (e.g. __RUNS_ON__) instead."
        )
        return 1

    print(f"✅ check-template-yaml: all {len(files)} template file(s) in {scan_dir.name}/ parse as YAML.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
